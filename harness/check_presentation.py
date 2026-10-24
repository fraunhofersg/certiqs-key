#!/usr/bin/env python3
r"""Motivation: contracts a reader new to the repository cannot use.

Contracts are hard to read for the reader `spec/style.md` writes for, and
every defect is of a kind a machine can see: prose outside the claim
environments (text before or after the environment, some of it normative, a
lead-in that labels an equation a proof cites); bold asides, code identifiers
and file names inside statements; cross-contract references written as
`\texttt{module/label}`, unlinked and unchecked, and `\ref`s that LaTeX
silently resolves to a local label of the same name; oracle codes (C5, PC9,
SA5) in titles; a duplicated title in the environment; summaries of any
length, and none on remarks; no way to tell a main result from a minor lemma.
These rules are what keeps contracts readable, since the editor runs only on
demand and the drafter is not asked to follow `spec/style.md` by hand.

Each rule is specified in `spec/claim-format.md`, where it is marked as a
presentation rule; `RULES` below names each one with the property it checks.
They run in every run of `python -m harness.check_claims`, which prints every
finding as `path:line: presentation[<rule>]: message`, then a count per rule,
and exits 1 on any finding.
Three rules are `check_claims`' own checks (0 to 2): the header without
`origin`, the claim environment without a bracketed title and the mapped
Unicode set of summaries and abstracts. Like every check
here they judge form only: whether a lead-in asserts
something a proof needs, or whether a summary says what the claim says, is the
equivalence reviewer's and the human's.

Two rules serve the glossary: repository jargon such as "virtual
ensemble" used pages before its definition leaves nothing to click. Every
`\term` carries a one-line gloss for the contract's generated Terms table
(`term-gloss`), and in every section the first use of a multi-word defined
term is a `\tref` link to its definition (`term-link`). The link rule reads
prose only (math, `\term`, `\tref` and comments removed), counts a plural
as a use, leaves out the section that defines the term, and covers the
contract's own terms and those of the modules it depends on. Single-word
terms ("instance", "sound") are too often plain English to flag by machine;
editors link them where they help.

A title is printed as TeX in its heading and flattened to plain text
(`contract_navigation.plain_title`) for the PDF bookmarks, the graph labels
and `graphs/README.md`. A flattening that kept a macro's name would let a TeX accent
or an uncatalogued macro surface in those views as noise ("R\'enyi" read
"R\textbackslash{}'enyi"). The
flattening maps the common macros to the mapped Unicode set
(`PLAIN_TITLE_MACROS`), and `title-plain` refuses a title with a backslash
outside `$...$` or a macro inside it that the map does not render.

The cost is one more pass over the claim bodies in every run; the rules
reuse `check_claims`' reader and never parse a file of their own.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from harness.check_claims import (
    PROOF_KINDS,
    TERM_GLOSS_RE,
    TERM_RE,
    TREF_RE,
    Claim,
    DefinedTerm,
    Module,
    PlainField,
    Repo,
    contract_of,
    declared_claims,
    defined_terms,
    environment_span,
    field_line,
    in_scope,
    plain_text_fields,
    reading_groups,
    rendered_plain_text,
    resolve_term,
    strip_comments,
    term_key,
)
from harness.check_symbols import read_group
from harness.contract_navigation import (
    KIND_WORD,
    plain_sentences,
    plain_title,
    unrenderable_title_tex,
)

#: Every presentation rule, in report order, with the property it checks.
RULES: dict[str, str] = {
    "prominence-missing": "every claim declares prominence",
    "summary-missing": "every claim has a summary, remarks included",
    "summary-sentences": "a summary has at most two sentences",
    "summary-length": "a summary has at most 300 characters as rendered",
    "title-length": "a title has at most 70 characters as rendered",
    "title-code": "a title carries no claim code (C5, PC9, SA5, ...)",
    "title-short-id": "a title carries no assumption short id",
    "title-plain": "a title has no TeX outside $...$ and only macros the plain-title "
                   "map renders inside it",
    "lead-in": "a lead-in holds no label, numbered display, term or macro definition",
    "after-statement": "only the proof follows the statement, nothing the proof",
    "statement-markup": r"no \textbf \texttt \verb \url \href \repodoc in a statement",
    "statement-code": "no code identifier or repository file name in a statement",
    "texttt-claim-id": r"a claim id is never set in \texttt (\xref or \ref instead)",
    "foreign-ref": r"\ref stays in the contract; another contract's claim is an \xref",
    "iface-outside-req": r"\iface appears only in a requirement",
    "order": "requirements come last; assumptions close the mathematics",
    "term-gloss": r"every \term carries a one-line gloss, \term[gloss]{phrase}",
    "term-link": r"a section's first use of a multi-word defined term is a \tref",
}

SUMMARY_SENTENCES = 2
SUMMARY_CHARACTERS = 300
TITLE_CHARACTERS = 70
#: Oracle claim codes: C5, C12a, PC9, RC8, PR13, SA5, DA1.
ORACLE_CODE_RE = re.compile(r"\b(?:C|PC|RC|PR|SA|DA)\d+[a-z]?\b")
SHORT_ID_TEXT_RE = re.compile(r"\bA-[A-Z0-9][A-Z0-9-]*[A-Z0-9]\b|\bA-[A-Z0-9]\b")
CLAIM_ID_RE = re.compile(r"^(?:[a-z0-9-]+/){0,2}(?:"
                         + "|".join(KIND_WORD) + r"):[a-z0-9][a-z0-9-]*$")
STATEMENT_MARKUP_RE = re.compile(r"\\(textbf|texttt|verb|url|href|repodoc)(?![A-Za-z])")
IFACE_RE = re.compile(r"\\iface(?![A-Za-z])")
CODE_RE = re.compile(r"certiqs_key"
                     r"|\b[A-Za-z0-9_./-]*[A-Za-z0-9_]\.(?:py|yaml|yml|md|json)\b")
NUMBERED_DISPLAY_RE = re.compile(
    r"\\begin\{(?:equation|align|gather|multline|flalign|alignat|eqnarray|subequations)\}"
    r"|\\tag(?![A-Za-z])")
MACRO_DEFINITION_RE = re.compile(
    r"\\(?:(?:re|provide)?newcommand|DeclareMathOperator|(?:re)?newenvironment"
    r"|def|let|newlength)(?![A-Za-z])")
LABEL_IN_TEXT_RE = re.compile(r"\\label\{([^}]*)\}")
@dataclass(frozen=True, order=True)
class Finding:
    """One presentation finding, rendered like a check_claims error."""

    path: str
    line: int
    rule: str
    message: str
    module: str = ""

    def render(self) -> str:
        """Return the one-line rendering used on stdout."""
        return f"{self.path}:{self.line}: presentation[{self.rule}]: {self.message}"


def sentence_count(text: str) -> int:
    """Count sentences, not full stops: abbreviations and numbers end none.

    The split is ``contract_navigation.plain_sentences``, which the role-word
    rule of check_claims reads too.
    """
    return len(plain_sentences(text))


def rendered_plain(repo: Repo, item: PlainField) -> str:
    """Return a plain-text field as the reader sees it: links as "Kind 1.1"."""
    return rendered_plain_text(repo, item.module_id, item.text)


class Collector:
    """Accumulates findings for one repository."""

    def __init__(self, repo: Repo) -> None:
        """Start an empty collection over ``repo``."""
        self.repo = repo
        self.findings: list[Finding] = []

    def add(self, path: str, line: int, rule: str, message: str, module: str) -> None:
        """Record one finding under ``rule`` (a key of ``RULES``)."""
        assert rule in RULES, rule
        self.findings.append(Finding(path, line, rule, message, module))

    def claim(self, claim: Claim, line: int, rule: str, message: str) -> None:
        """Record a finding at a line of a claim file."""
        self.add(claim.rel, line, rule, message, claim.module_id)

    def field(self, claim: Claim, name: str, rule: str, message: str) -> None:
        """Record a finding at a header field of a claim file."""
        self.claim(claim, claim.line_of(name), rule, message)


# --- header and title ----------------------------------------------------------


def check_header(out: Collector, claim: Claim) -> None:
    """Prominence and summary present."""
    header = claim.header
    if "prominence" not in header:
        out.claim(claim, 1, "prominence-missing",
                  "no prominence (main, standard or technical)")
    summary = header.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        out.claim(claim, 1, "summary-missing", "no summary")


def check_title(out: Collector, claim: Claim) -> None:
    """Length as rendered, oracle codes and short ids."""
    title = str(claim.header.get("title", ""))
    shown = plain_title(title)
    if len(shown) > TITLE_CHARACTERS:
        out.field(claim, "title", "title-length",
                  f"title has {len(shown)} characters as rendered "
                  f"(at most {TITLE_CHARACTERS})")
    for match in ORACLE_CODE_RE.finditer(title):
        out.field(claim, "title", "title-code",
                  f"title carries the claim code {match.group()}")
    for match in SHORT_ID_TEXT_RE.finditer(title):
        if match.group() in out.repo.assumptions:
            out.field(claim, "title", "title-short-id",
                      f"title carries the short id {match.group()} "
                      "(the heading of an assumption prints it)")
    unrenderable = unrenderable_title_tex(title)
    if unrenderable:
        out.field(claim, "title", "title-plain",
                  f"title carries {', '.join(unrenderable)}, which the plain title "
                  f"of bookmarks and graphs cannot render (it reads '{shown}'); "
                  "write an accented letter itself, or a symbol of "
                  "contract_navigation.PLAIN_TITLE_MACROS inside $...$")


def check_plain_fields(out: Collector) -> None:
    """Summaries: sentences and length (the Unicode set is check_claims')."""
    for item in plain_text_fields(out.repo):
        if item.claim is None or item.name != "summary":
            continue
        shown = rendered_plain(out.repo, item)
        sentences = sentence_count(shown)
        if sentences > SUMMARY_SENTENCES:
            out.add(item.path, item.line, "summary-sentences",
                    f"summary has {sentences} sentences (at most {SUMMARY_SENTENCES})",
                    item.module_id)
        if len(shown) > SUMMARY_CHARACTERS:
            out.add(item.path, item.line, "summary-length",
                    f"summary has {len(shown)} characters as rendered "
                    f"(at most {SUMMARY_CHARACTERS})", item.module_id)


# --- body shape -----------------------------------------------------------------


def first_text(body: str, start: int, end: int) -> int | None:
    """Return the offset of the first non-space character in a slice, if any."""
    stripped = body[start:end]
    for offset, char in enumerate(stripped):
        if not char.isspace():
            return start + offset
    return None


def check_shape(out: Collector, claim: Claim) -> None:
    """Lead-in content and what follows the statement (a title is check_claims')."""
    body = strip_comments(claim.body)
    span = environment_span(body)
    if span is None:
        return          # check_claims' identity check reports it
    lead = body[:span.begin]
    for regex, what in ((LABEL_IN_TEXT_RE, "a \\label"),
                        (NUMBERED_DISPLAY_RE, "a numbered display"),
                        (TERM_RE, "a \\term"),
                        (MACRO_DEFINITION_RE, "a macro definition")):
        for match in regex.finditer(lead):
            out.claim(claim, claim.line_at(body, match.start()), "lead-in",
                      f"the lead-in holds {what}; it is non-normative and nothing "
                      "may cite it")
    rest = span.end
    if claim.kind in PROOF_KINDS:
        proof = body.find("\\begin{proof}", rest)
        if proof != -1:
            between = first_text(body, rest, proof)
            if between is not None:
                out.claim(claim, claim.line_at(body, between), "after-statement",
                          "text between the statement and its proof")
            close = body.find("\\end{proof}", proof)
            rest = len(body) if close == -1 else close + len("\\end{proof}")
    after = first_text(body, rest, len(body))
    if after is not None:
        where = "the proof" if rest != span.end else "the statement"
        extra = ("a second proof" if body.startswith("\\begin{proof}", after)
                 else "text")
        out.claim(claim, claim.line_at(body, after), "after-statement",
                  f"{extra} after {where}; nothing follows it")


def texttt_argument(body: str, match: re.Match[str]) -> str | None:
    r"""Return the argument of a ``\texttt`` match, normalised, if it has one."""
    group = read_group(body, match.end())
    if group is None:
        return None
    argument = re.sub(r"\\(?:allowbreak|linebreak|-)(?![A-Za-z])\s*", "", group[0])
    return argument.replace("\\_", "_").strip()


def check_statement(out: Collector, claim: Claim) -> None:
    """Markup and code identifiers inside the claim environment."""
    body = strip_comments(claim.body)
    span = environment_span(body)
    if span is None:
        return
    content = body[span.content:span.close]
    for match in STATEMENT_MARKUP_RE.finditer(content):
        if match.group(1) == "texttt":
            argument = texttt_argument(content, match)
            if argument is not None and CLAIM_ID_RE.match(argument):
                continue            # reported as texttt-claim-id
        out.claim(claim, claim.line_at(body, span.content + match.start()),
                  "statement-markup", f"\\{match.group(1)} in the statement")
    # The arguments of \iface and \repodoc are keys and paths by design; \_ is
    # how TeX writes the underscore of certiqs_key. Only newlines are kept from
    # what is removed, so line numbers stay exact.
    text = re.sub(r"\\(?:iface|repodoc)\{[^}]*\}",
                  lambda removed: "\n" * removed.group().count("\n"),
                  content).replace("\\_", "_")
    first = claim.line_at(body, span.content)
    for match in CODE_RE.finditer(text):
        out.claim(claim, first + text.count("\n", 0, match.start()),
                  "statement-code",
                  f"'{match.group()}' in the statement: a code identifier or file "
                  "name belongs in a requirement's \\iface, a lead-in's \\repodoc "
                  "or design.md")


def check_texttt_ids(out: Collector, claim: Claim) -> None:
    r"""``\texttt{<claim id>}`` anywhere in the body."""
    body = strip_comments(claim.body)
    for match in re.finditer(r"\\texttt(?![A-Za-z])", body):
        argument = texttt_argument(body, match)
        if argument is None or not CLAIM_ID_RE.match(argument):
            continue
        label = argument.rsplit("/", 1)[-1]
        foreign = ("/" in argument
                   and contract_of(argument) != contract_of(claim.claim_id))
        suggestion = (f"\\xref{{{argument}}}" if foreign else
                      f"{KIND_WORD.get(label.split(':')[0], 'Claim')}~\\ref{{{label}}}")
        out.claim(claim, claim.line_at(body, match.start()), "texttt-claim-id",
                  f"\\texttt{{{argument}}} names a claim; write {suggestion}")


def check_iface(out: Collector, claim: Claim) -> None:
    r"""``\iface`` only in a requirement."""
    if claim.kind == "req":
        return
    body = strip_comments(claim.body)
    for match in IFACE_RE.finditer(body):
        out.claim(claim, claim.line_at(body, match.start()), "iface-outside-req",
                  "\\iface names an interface key or refusal string, which only a "
                  "requirement binds")


def check_foreign_refs(out: Collector, claim: Claim) -> None:
    r"""Report a ``\ref`` whose declared target lies in another contract."""
    repo = out.repo
    contract = contract_of(claim.claim_id)
    owners: dict[str, set[str]] = {}
    for target_id in declared_claims(repo, claim):
        target = repo.claims[target_id]
        for label in {target.label, *target.own_labels}:
            owners.setdefault(label, set()).add(target_id)
    for label, line in claim.refs_seen:
        if label in claim.own_labels:
            continue
        found = owners.get(label, set())
        foreign = sorted(o for o in found if contract_of(o) != contract)
        if not foreign:
            continue
        local = sorted(o for o in found if contract_of(o) == contract)
        if local:
            message = (f"\\ref{{{label}}} is ambiguous: it resolves to {local[0]} in "
                       f"this contract, while the declared {foreign[0]} of another "
                       f"contract defines the same label; if that one is meant, write "
                       f"\\xref{{{foreign[0]}}}")
        else:
            message = (f"\\ref{{{label}}} names a label of {foreign[0]} in another "
                       f"contract, which this PDF does not hold; write "
                       f"\\xref{{{foreign[0]}}}")
        out.claim(claim, line, "foreign-ref", message)


# --- module order ---------------------------------------------------------------


def order_line(module: Module, label: str) -> int:
    """Return the line of ``- label`` in a module.yaml's order, else of order."""
    pattern = re.compile(r"^\s*-\s*['\"]?" + re.escape(label) + r"['\"]?\s*(#.*)?$")
    for number, text in enumerate(module.lines, start=1):
        if pattern.match(text):
            return number
    return field_line(module.lines, "order")


def check_order(out: Collector, module: Module) -> None:
    """Check that requirements come last and assumptions close the mathematics."""
    order = module.order
    kinds = [label.split(":", 1)[0] for label in order]

    def add(label: str, message: str) -> None:
        out.add(module.rel, order_line(module, label), "order", message,
                module.module_id)

    first_req = kinds.index("req") if "req" in kinds else len(order)
    for label, kind in zip(order[first_req + 1:], kinds[first_req + 1:], strict=True):
        if kind != "req":
            add(label, f"'{label}' follows the first requirement "
                f"'{order[first_req]}'; requirements come after every other claim")
    if "ass" in kinds[:first_req]:
        first_ass = kinds.index("ass")
        for label, kind in zip(order[first_ass + 1:first_req],
                               kinds[first_ass + 1:first_req], strict=True):
            if kind not in ("ass", "rem"):
                add(label, f"'{label}' follows the first assumption "
                    f"'{order[first_ass]}'; between it and the first requirement "
                    "only assumptions and remarks stand")
    groups = module.meta.get("reading_groups")
    if isinstance(groups, list) and groups:
        try:
            starts = {labels[0] for _title, labels in reading_groups(
                {**module.meta, "order": order}) if labels}
        except ValueError:
            return                  # check_claims reports the malformed groups
        for kind in ("ass", "req"):
            if kind in kinds:
                first = order[kinds.index(kind)]
                if first not in starts:
                    word = "assumption" if kind == "ass" else "requirement"
                    add(first, f"the first {word} '{first}' does not start a "
                        "reading group")


# --- defined terms ---------------------------------------------------------------

#: Math, which never counts as a use of a term.
MATH_RE = re.compile(
    r"\$\$.*?\$\$|\$[^$]*\$|\\\[.*?\\\]|\\\(.*?\\\)"
    r"|\\begin\{(equation|align|gather|multline|flalign|alignat|eqnarray|displaymath)"
    r"\*?\}.*?\\end\{\1\*?\}", re.S)


def blank(text: str, start: int, end: int, fill: str = " ") -> str:
    """Replace ``text[start:end]`` by ``fill`` characters, keeping every newline."""
    return text[:start] + "".join(
        "\n" if char == "\n" else fill for char in text[start:end]) + text[end:]


def check_term_glosses(out: Collector, claim: Claim) -> None:
    r"""Every ``\term`` carries its one-line gloss."""
    body = strip_comments(claim.body)
    for match in TERM_GLOSS_RE.finditer(body):
        if not (match.group(1) or "").strip():
            out.claim(claim, claim.line_at(body, match.start()), "term-gloss",
                      f"\\term{{{match.group(2)}}} has no gloss; write "
                      "\\term[<one line saying what it is>]{...} for the Terms table")


def term_pattern(term: DefinedTerm) -> re.Pattern[str]:
    """Match a term's phrase in prose, a plural included, case ignored."""
    words = [re.escape(word) for word in term.phrase.split()]
    return re.compile(r"(?<![A-Za-z-])" + r"\s+".join(words)
                      + r"(?:s|es)?(?![A-Za-z-])", re.I)


def check_term_links(out: Collector, module: Module) -> None:
    """In each section, the first use of a multi-word defined term is linked."""
    repo = out.repo
    contract = contract_of(module.module_id)
    depends = {contract_of(str(dep)) for dep in module.meta.get("depends_on") or []}
    terms = [term for (owner, _key), term in defined_terms(repo).items()
             if (owner == contract or owner in depends)
             and len(term.phrase.split()) > 1 and not re.search(r"[\\$]", term.phrase)]
    if not terms:
        return
    try:
        groups = reading_groups(module.meta)
    except ValueError:
        return                      # check_claims reports the malformed groups
    for title, labels in groups:
        ids = [f"{module.module_id}/{label}" for label in labels]
        claims = [repo.claims[cid] for cid in ids if cid in repo.claims]
        defined_here = {term_key(term.phrase) for term in terms
                        if term.claim_id in ids}
        first_plain: dict[str, tuple[Claim, int]] = {}
        linked: set[str] = set()
        for claim in claims:
            body = strip_comments(claim.body)
            prose = body
            for match in MATH_RE.finditer(body):
                prose = blank(prose, match.start(), match.end())
            events: list[tuple[int, str, bool]] = []
            for match in TREF_RE.finditer(body):
                found = resolve_term(repo, contract, match.group(1) or match.group(2))
                if not isinstance(found, str):
                    events.append((match.start(), term_key(found.phrase), True))
                prose = blank(prose, match.start(), match.end(), "x")
            for match in TERM_RE.finditer(body):
                prose = blank(prose, match.start(), match.end(), "x")
            # Longest phrases first, each blanked once found, so that "virtual
            # transmitted system" is no use of "transmitted system".
            for term in sorted(terms, key=lambda t: (-len(t.phrase.split()), t.phrase)):
                key = term_key(term.phrase)
                hits = list(term_pattern(term).finditer(prose))
                if hits and key not in defined_here:
                    events.append((hits[0].start(), key, False))
                for hit in hits:
                    prose = blank(prose, hit.start(), hit.end(), "x")
            for position, key, is_link in sorted(events):
                if key in linked or key in first_plain:
                    continue
                if is_link:
                    linked.add(key)
                else:
                    first_plain[key] = (claim, position)
        for key, (claim, position) in sorted(first_plain.items()):
            body = strip_comments(claim.body)
            out.claim(claim, claim.line_at(body, position), "term-link",
                      f"the first use of '{key}' in the section '{title}' is not "
                      f"linked; write \\tref{{...}} there")


# --- running ----------------------------------------------------------------------


def presentation_findings(repo: Repo) -> list[Finding]:
    """Run every presentation rule over a loaded repository."""
    out = Collector(repo)
    for claim_id in sorted(repo.claims):
        claim = repo.claims[claim_id]
        check_header(out, claim)
        check_title(out, claim)
        check_shape(out, claim)
        check_statement(out, claim)
        check_texttt_ids(out, claim)
        check_iface(out, claim)
        check_foreign_refs(out, claim)
        check_term_glosses(out, claim)
    check_plain_fields(out)
    for module_id in sorted(repo.modules):
        check_order(out, repo.modules[module_id])
        check_term_links(out, repo.modules[module_id])
    return sorted(out.findings)


def report_presentation(repo: Repo, wanted: str | None, scope: str) -> int:
    """Print the findings in scope and a count per rule; return how many there are."""
    findings = [f for f in presentation_findings(repo) if in_scope(f.module, wanted)]
    for finding in findings:
        print(finding.render())
    if not findings:
        return 0
    counts = dict.fromkeys(RULES, 0)
    files: dict[str, set[str]] = {rule: set() for rule in RULES}
    for finding in findings:
        counts[finding.rule] += 1
        files[finding.rule].add(finding.path)
    width = max(len(rule) for rule in RULES)
    print(f"presentation rules under {scope}: findings, files, rule")
    for rule, description in RULES.items():
        print(f"  {rule.ljust(width)} {counts[rule]:6} {len(files[rule]):6}  "
              f"{description}")
    every = {path for paths in files.values() for path in paths}
    print(f"  {'total'.ljust(width)} {len(findings):6} {len(every):6}")
    return len(findings)
