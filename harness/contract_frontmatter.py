r"""Motivation: a contract a reader can enter without reading it front to back.

A reader of a contract wants, before any section, what the module
establishes, which results are its main ones and what they assume, what its
symbols and its jargon mean; after it, how to find a claim by number or
identifier, where a defined term is defined and what the module's interface
is. Without them the main results are nowhere marked, the assumptions are
scattered through the claims, and the notation lives only in
`spec/notation.md`. The skeleton (main results, assumptions at a glance,
notation table per contract, defined-terms index, interface appendix) is
written here, around the body of `harness/contract_render.py`. The main
results are listed and linked rather than restated (restating them in full
would cost several pages before the first section; the digest keeps the full
statements), and the Terms table and the links serve the glossary:

- front: title and version, the module overview (the first use of each
  multi-word term the contract defines linked to its definition), the
  one-line legend for the non-normative styles, links to the design notes,
  the graphs and the viewing instructions, the contents; then every
  `prominence: main` claim listed by number, title and summary, linked to its
  statement, with its transitive assumption closure
  (`check_claims.assumption_closure`); a table of every assumption the
  contract's claims assume, its own and other contracts', with its `category`
  (grouped by category once any assumption listed carries one); the rows of
  `spec/notation.md` whose macros the contract's claim bodies use; the Terms
  table: every phrase the contract defines with `\term` and every term of
  another contract it links with `\tref`, each with its one-line gloss and a
  link to its definition;
- back: the whitelisted fields of the declared inputs and outputs of each
  `interface.yaml` (name, symbol, presence and the claims its `fixed_by` or
  `locator` names; free text stays out), the claim
  index with each claim's number, the index of defined terms (`\term`,
  imakeidx; latexmk runs makeindex), the bibliography.

Everything here is generated from the claim files, `module.yaml`,
`interface.yaml` and `spec/notation.md`, so `assemble_contract --check` sees a
stale page as it sees a stale claim.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from harness.check_claims import (
    ASSUMPTION_CATEGORIES,
    LABEL_RE,
    TERM_RE,
    TREF_RE,
    DefinedTerm,
    assumption_closure,
    contract_of,
    resolve_term,
    strip_comments,
)
from harness.check_symbols import MEANING_CLAIM_RE, TOKEN_RE, catalogue_rows
from harness.contract_navigation import (
    KIND_WORD,
    contract_pdf,
    markdown_tex,
    tex_safe,
    tex_text,
    tex_title,
    xref_title,
)
from harness.contract_render import (
    KEY_RE,
    MULTILINE_DISPLAYS,
    NUMBERED_DISPLAYS,
    Contract,
    category_words,
    line_ends,
)

#: The legend of the non-normative styles, printed once (SPIKE.md 2.7).
LEGEND = ("here and throughout, is non-normative: it explains, and nothing in "
          "it is assumed or proved.")
TAG_RE = re.compile(r"\\tag\*?(?![A-Za-z])")
STARRED_RE = re.compile(r"\\begin\{(" + "|".join(NUMBERED_DISPLAYS)
                        + r")\}(.*?)\\end\{\1\}", re.S)
CLAIM_TOKEN_RE = re.compile(
    r"(?<![\w/:-])((?:[a-z0-9-]+/){0,2}(?:thm|lem|prop|cor|def|ass|rem|ex|fact|req)"
    r":[a-z0-9][a-z0-9-]*)")
COLUMN = r">{\raggedright\arraybackslash}"


def unnumbered(title: str, back: bool = False) -> str:
    """Open an unnumbered section listed in the contents and the bookmarks.

    A back-matter section is a top-level bookmark, not one nested in the
    last part.
    """
    return (("\\clearpage\n\\bookmarksetupnext{level=part}\n" if back else "\n")
            + f"\\section*{{{title}}}\\addcontentsline{{toc}}{{section}}{{{title}}}\n")


# --- the title page -------------------------------------------------------------


def title_tex(contract: Contract) -> str:
    """Title and version, overview, legend, links and contents."""
    meta = contract.repo.modules[contract.core].meta
    title = tex_text(str(meta.get("title", contract.core)))
    version = tex_text(str(meta.get("version", "0.0.0")))
    out = ["\n\\begin{document}\n\\begin{center}\n",
           f"{{\\LARGE\\bfseries {title}}}\\\\[4pt]\n",
           f"{{\\large Contract, version {version}}}\n\\end{{center}}\n"]
    abstract = str(meta.get("abstract", "") or "")
    if abstract.strip():
        overview = contract.plain_linked(abstract, contract.core)
        out.append("\\begin{overview}\n" + overview + "\n\\end{overview}\n")
    out.append("\\medskip\n\\noindent{\\small\\textcolor{nnGrey}{\\itshape Grey text}, "
               + LEGEND + "}\n\n")
    # Markdown pages are linked on the repository host, which renders them; the
    # Pages site serves the PDFs and the graphs beside the contract but no Markdown.
    module = f"{contract.code_url}spec/modules/{contract.core}/"
    links = []
    if (contract.root / "spec" / "modules" / contract.core / "design.md").is_file():
        links.append(rf"The \href{{{module}design.md}}{{design notes}} (non-normative) "
                     r"explain why the module is built as it is and draw its "
                     r"processing flowchart.")
    links.append(r"The dependencies between the sections are drawn in "
                 r"\href{graphs/overview.svg}{the section dependency matrix}, and "
                 rf"\href{{{module}graphs/README.md}}{{the graph index}} opens every "
                 r"section's dependency graph.")
    links.append(r"The \href{digest.pdf}{statements digest} holds every "
                 r"definition, assumption, result and requirement without the proofs.")
    reading = f"{contract.code_url}harness/contract-reading.md"
    links.append(rf"\href{{{reading}}}{{How to read a contract}} explains this "
                 r"layout and its links.")
    out.append("\\smallskip\n\\noindent{\\small " + " ".join(links) + "}\n\n")
    out.append("{\\small\\tableofcontents}\n")
    return "".join(out)


# --- main results ------------------------------------------------------------------


def contract_tag(label: str) -> str:
    r"""Tag a restated display row with the original's number, inside the contract."""
    return r"\tag{\ref*{" + label + "}}"


def restate(content: str, tag: Callable[[str], str] = contract_tag,
            tagged: Callable[[str], str] = lambda label: "") -> str:
    r"""Copy a statement's content without duplicating a label or a term.

    Comments go, labels are stripped, a numbered display becomes its starred
    form with each labelled row tagged by ``tag(<label>)`` (in the contract's
    front matter ``\tag{\ref*{<label>}}``, the original's number; the digest
    passes its own); a row that carries its own ``\tag`` keeps it and its
    label becomes ``tagged(<label>)`` (nothing, by default).
    ``subequations`` is unwrapped, and ``\term`` becomes ``\emph`` so the
    index points at the definition only. A label that ``tag`` or ``tagged``
    writes must not be spelled ``\label``, which the last step strips.
    """
    text = strip_comments(content)
    text = re.sub(r"\\begin\{subequations\}\s*(?:\\label\{[^}]*\})?", "", text)
    text = text.replace("\\end{subequations}", "")

    def star(match: re.Match[str]) -> str:
        env, inner = match.group(1), match.group(2)
        argument = ""
        if env == "alignat":
            head = re.match(r"\s*\{[^{}]*\}", inner)
            if head is not None:
                argument, inner = head.group(0), inner[head.end():]
        cuts = line_ends(inner) if env in MULTILINE_DISPLAYS else []
        rows, start = [], 0
        for cut in [*cuts, len(inner)]:
            rows.append(inner[start:cut])
            start = cut
        # A row with its own \tag keeps it: a second one is an amsmath error.
        inner = "".join(
            LABEL_RE.sub(lambda label: tagged(label.group(1)), row)
            if TAG_RE.search(row) else
            LABEL_RE.sub(lambda label: tag(label.group(1)), row) for row in rows)
        inner = re.sub(r"\\(?:notag|nonumber)(?![A-Za-z])", "", inner)
        return f"\\begin{{{env}*}}{argument}{inner}\\end{{{env}*}}"

    text = STARRED_RE.sub(star, text)
    text = LABEL_RE.sub("", text)
    text = TERM_RE.sub(lambda term: r"\emph{" + term.group(1) + "}", text)
    text = TREF_RE.sub(lambda use: use.group(2), text)
    return text.strip()


def main_result_tex(contract: Contract, claim_id: str) -> str:
    """List one main result: number, title and summary, what it rests on."""
    claim = contract.claim(claim_id)
    title = tex_title(str(claim.header.get("title", claim.label)))
    word = KIND_WORD.get(claim.kind, "Claim")
    summary = str(claim.header.get("summary") or "").strip()
    out = [f"\\par\\noindent\\hyperref[{claim.label}]{{\\textbf{{{word}~"
           f"\\ref*{{{claim.label}}}}}}}\\enspace {title}\\par\\nobreak\n"]
    if summary:
        out.append("{\\small\\itshape\\color{nnGrey}\\noindent "
                   + contract.plain(summary, claim.module_id) + "\\par}\\nobreak\n")
    if claim.kind != "ass":        # an assumption rests on nothing but itself
        closure = assumption_closure(contract.repo, claim_id)
        rests = (", ".join(contract.short_ref(short_id) for short_id in closure)
                 or "no assumption")
        out.append(f"\\claimmeta{{\\metalabel{{Rests on}}{rests}}}\n")
    else:
        out.append("\\medskip\n")
    return "".join(out)


def main_results_tex(contract: Contract) -> str:
    """List every main result with its summary; nothing when there is none."""
    mains = [cid for cid in contract.order
             if contract.claim(cid).header.get("prominence") == "main"]
    if not mains:
        return ""
    return (unnumbered("Main results")
            + "\\sectionintro{The module's most important results, those its "
              "overview names as what it establishes, with every assumption each "
              "rests on, directly or through the claims it uses. Each links to its "
              "statement and proof; the statements digest holds them in full.}\n"
            + "".join(main_result_tex(contract, cid) for cid in mains))


# --- assumptions at a glance ---------------------------------------------------------


def assumptions_tex(contract: Contract) -> str:
    """Tabulate the assumptions the contract states or its claims assume."""
    repo = contract.repo
    own = [cid for cid in contract.order if contract.claim(cid).kind == "ass"]
    own_ids = [str(contract.claim(cid).header.get("short_id") or "") for cid in own]
    assumed: dict[str, list[str]] = {}
    for cid in contract.order:
        for short_id in dict.fromkeys(contract.claim(cid).assumes):
            assumed.setdefault(short_id, []).append(cid)
    foreign = sorted(short_id for short_id in assumed if short_id not in own_ids)
    listed = [*[s for s in own_ids if s], *foreign]

    def category(short_id: str) -> str:
        owner = repo.assumptions.get(short_id)
        value = owner.header.get("category") if owner is not None else None
        return value if isinstance(value, str) else ""

    if any(category(short_id) for short_id in listed):
        # grouped by category in the vocabulary's order, uncategorised last
        rank = {name: index for index, name in enumerate(ASSUMPTION_CATEGORIES)}
        listed.sort(key=lambda s: (rank.get(category(s), len(rank)), s))
    rows: list[str] = []
    for short_id in listed:
        owner = repo.assumptions.get(short_id)
        kind = tex_text(category_words(category(short_id)))
        if owner is None:
            where, title = r"\emph{no such assumption}", ""
        elif contract.local(owner.claim_id):
            where = contract.word_ref(owner.claim_id)
            title = tex_title(str(owner.header.get("title", owner.label)))
        else:
            pdf = contract_pdf(contract_of(owner.claim_id), "contract")
            where = f"\\extref{{{pdf}}}{{{owner.claim_id}}}"
            title = xref_title(str(owner.header.get("title", owner.label)))
        by = ", ".join(contract.ref(cid) for cid in assumed.get(short_id, [])) or "---"
        rows.append(f"{contract.short_ref(short_id)} & {kind} & {title} & {where} & "
                    f"{by}\\\\\n")
    if not rows:
        return ""
    return (unnumbered("Assumptions at a glance")
            + "\\sectionintro{Every assumption this contract states or its claims "
              "assume, with its category and the claims of this contract that "
              "assume it directly. An assumption of another contract links into "
              "that contract's PDF.}\n"
            + "{\\footnotesize\\begin{xltabular}{\\linewidth}{@{}" + COLUMN + "p{1.6cm}"
            + COLUMN + "p{1.9cm}" + COLUMN + "X" + COLUMN + "p{2.3cm}" + COLUMN
            + "p{2.8cm}@{}}\n"
            + "\\toprule\nAssumption & Category & Title & Stated as & "
              "Assumed directly by\\\\\n"
            + "\\midrule\n\\endhead\n" + "\\addlinespace\n".join(rows)
            + "\\bottomrule\n\\end{xltabular}}\n")


# --- notation ----------------------------------------------------------------------


def used_macros(contract: Contract) -> set[str]:
    """Return every control word the contract's claim bodies use."""
    used: set[str] = set()
    for cid in contract.order:
        for match in TOKEN_RE.finditer(strip_comments(contract.claim(cid).body)):
            if match.group(1):
                used.add(match.group(1))
    return used


def meaning_tex(contract: Contract, text: str) -> str:
    """Render a Meaning cell, its claim names as links.

    A claim the cell names by module and label becomes a reference: a claim of
    this contract the in-document one (``Def. 2.1``), any other a link into its
    contract's PDF. A name that resolves to no claim (an equation label, a
    typo) stays the code span it was.
    """
    out: list[str] = []
    last = 0
    for match in MEANING_CLAIM_RE.finditer(text):
        cid = f"{match['module']}/{match['label']}"
        if cid not in contract.repo.claims:
            continue
        before = text[last:match.start()]
        out.append(markdown_tex(before) + (" " if before[-1:].isspace() else ""))
        out.append(contract.ref(cid))
        last = match.end()
    rest = text[last:]
    out.append((" " if rest[:1].isspace() and out else "") + markdown_tex(rest))
    return "".join(out)


def notation_tex(contract: Contract) -> str:
    """Render the rows of ``spec/notation.md`` whose macros the contract uses."""
    path = contract.root / "spec" / "notation.md"
    if not path.is_file():
        return ""
    used = used_macros(contract)
    rows = []
    for row in catalogue_rows(path):
        if not any(name in used for name, _ in row.macros):
            continue
        symbols = ", ".join(
            "$\\" + name + "".join("{" + arg + "}" for arg in args) + "$"
            for name, args in row.macros)
        rows.append(f"{symbols} & {meaning_tex(contract, row.meaning)}\\\\\n")
    if not rows:
        return ""
    return (unnumbered("Notation")
            + "\\sectionintro{The symbols of the repository's notation catalogue "
              "(\\href{../../notation.md}{spec/notation.md}) that this contract "
              "uses, in the catalogue's order, with their meaning.}\n"
            + "{\\small\\begin{xltabular}{\\linewidth}{@{}" + COLUMN + "p{3.6cm}"
            + COLUMN + "X@{}}\n\\toprule\nSymbol & Meaning\\\\\n\\midrule\n\\endhead\n"
            + "".join(rows) + "\\bottomrule\n\\end{xltabular}}\n")


def used_terms(contract: Contract) -> list[DefinedTerm]:
    r"""Return the terms of other contracts this contract links with ``\tref``."""
    found: dict[str, DefinedTerm] = {}
    for cid in contract.order:
        for match in TREF_RE.finditer(strip_comments(contract.claim(cid).body)):
            term = resolve_term(contract.repo, contract.core,
                                match.group(1) or match.group(2))
            if isinstance(term, DefinedTerm) and term.contract != contract.core:
                found.setdefault(term.claim_id + "|" + term.phrase, term)
    return list(found.values())


def terms_tex(contract: Contract) -> str:
    """Tabulate the contract's defined terms and the foreign terms it uses."""
    terms = [*contract.terms, *used_terms(contract)]
    if not terms:
        return ""

    def order(term: DefinedTerm) -> str:
        return re.sub(r"[^a-z0-9 ]", "", term.phrase.lower())

    rows = []
    for term in sorted(terms, key=order):
        claim = contract.repo.claims[term.claim_id]
        meaning = (contract.plain(term.gloss, claim.module_id) if term.gloss
                   else "---")
        where = (contract.word_ref(term.claim_id) if contract.local(term.claim_id)
                 else f"\\extref{{{contract_pdf(term.contract, 'contract')}}}"
                      f"{{{term.claim_id}}}")
        rows.append(f"{contract.term_link(term, term.phrase)} & {meaning} & "
                    f"{where}\\\\\n")
    return (unnumbered("Terms")
            + "\\sectionintro{The phrases this contract defines, and the terms of "
              "other contracts it uses, each with a one-line gloss and the "
              "definition that fixes it. In the text, a linked term opens its "
              "definition.}\n"
            + "{\\small\\begin{xltabular}{\\linewidth}{@{}" + COLUMN + "p{3.6cm}"
            + COLUMN + "X" + COLUMN + "p{2.6cm}@{}}\n\\toprule\nTerm & Meaning & "
            "Defined in\\\\\n\\midrule\n\\endhead\n"
            + "\\addlinespace[2pt]\n".join(rows) + "\\bottomrule\n\\end{xltabular}}\n")


def front_tex(contract: Contract) -> str:
    """Render the front matter: title, main results, assumptions, notation, terms."""
    return (title_tex(contract) + main_results_tex(contract)
            + assumptions_tex(contract) + notation_tex(contract) + terms_tex(contract))


# --- the interface appendix -----------------------------------------------------


def interface_rows(node: Any) -> list[dict[str, Any]]:
    """Return every mapping with a ``name`` under an interface value, in order."""
    found: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if "name" in node:
            return [node]
        for value in node.values():
            found += interface_rows(value)
    elif isinstance(node, list):
        for value in node:
            found += interface_rows(value)
    return found


def named_claims(contract: Contract, module_id: str, text: str) -> list[str]:
    """Return the claims a free-text field of ``module_id`` names by label or id."""
    found: list[str] = []
    for match in CLAIM_TOKEN_RE.finditer(text):
        token = match.group(1)
        candidates = [token, f"{contract.core}/{token}", f"{module_id}/{token}"]
        hit = next((c for c in candidates if c in contract.repo.claims), None)
        if hit is None and "/" not in token:
            same = [cid for cid in contract.order if cid.rsplit("/", 1)[1] == token]
            hit = same[0] if len(same) == 1 else None
        if hit is not None and hit not in found:
            found.append(hit)
    return found


def interface_table(contract: Contract, module_id: str,
                    rows: list[dict[str, Any]]) -> str:
    """Render one table of interface rows: key and symbol, presence, fixing claims."""
    lines = []
    for row in rows:
        fixed = row.get("fixed_by", row.get("locator", ""))
        claims = named_claims(contract, module_id, str(fixed or ""))
        # `symbol: null` is "no symbol", not the string "None".
        raw_symbol = row.get("symbol")
        symbol = "" if raw_symbol is None else tex_safe(str(raw_symbol))
        presence = tex_safe(str(row.get("presence", "")))
        name = str(row["name"])
        key = (f"\\iface{{{name}}}" if KEY_RE.match(name)
               else f"\\texttt{{{tex_safe(name)}}}")
        lines.append(key
                     + (f"\\newline {symbol}" if symbol else "")
                     + f" & {presence} & "
                     + (", ".join(contract.ref(cid) for cid in claims) or "---")
                     + "\\\\\n")
    return ("{\\footnotesize\\begin{xltabular}{\\linewidth}{@{}" + COLUMN + "p{4.4cm}"
            + COLUMN + "X" + COLUMN + "p{2.9cm}@{}}\n\\toprule\n"
            + "Key and symbol & Presence & Fixed by\\\\\n\\midrule\n\\endhead\n"
            + "\\addlinespace\n".join(lines) + "\\bottomrule\n\\end{xltabular}}\n")


def interface_tex(contract: Contract) -> str:
    """Render the declared inputs and outputs of each module of the contract."""
    out: list[str] = []
    modules = [contract.core, *[part.module_id for part in contract.structure.parts
                                if part.module_id != contract.core]]
    for module_id in dict.fromkeys(modules):
        document = contract.interface(module_id)
        if not isinstance(document, dict):
            continue
        title = tex_text(str(contract.repo.modules[module_id].meta.get("title",
                                                                          module_id)))
        relative = Path(module_id.removeprefix(contract.core).lstrip("/"),
                        "interface.yaml").as_posix()
        for key, word in (("inputs", "Inputs"), ("outputs", "Outputs")):
            rows = interface_rows(document.get(key))
            if rows:
                out.append(f"\\subsection*{{{word}: {title}}}\n"
                           f"\\noindent{{\\small From \\href{{{relative}}}"
                           f"{{\\nolinkurl{{{relative}}}}}.}}\\par\\smallskip\n"
                           + interface_table(contract, module_id, rows))
    if not out:
        return ""
    return (unnumbered("Interface", back=True)
            + "\\sectionintro{The declared inputs and outputs of the module and its "
              "submodules: each key with its symbol, when it is present and the "
              "claims that fix it. The domains, types and refusal rules are in the "
              "interface files themselves.}\n" + "".join(out))


# --- the indexes and the bibliography -------------------------------------------


def claim_index_tex(contract: Contract) -> str:
    """Render the claim index: number, title, identifier and page of each claim."""
    rows = []
    for cid in contract.order:
        claim = contract.claim(cid)
        title = tex_title(str(claim.header.get("title", claim.label)))
        rows.append(f"{contract.word_ref(cid)} & {title}\\newline"
                    f"{{\\footnotesize\\color{{metaGrey}}\\claimid{{{cid}}}}} & "
                    f"\\pageref{{{claim.label}}}\\\\\n")
    return (unnumbered("Claim index", back=True)
            + "{\\small\\begin{xltabular}{\\linewidth}{@{}" + COLUMN + "p{2.7cm}"
            + COLUMN + "Xr@{}}\n\\toprule\n"
            + "Claim & Title and identifier & Page\\\\\n\\midrule\n\\endhead\n"
            + "\\addlinespace[2pt]\n".join(rows) + "\\bottomrule\n\\end{xltabular}}\n")


def terms_index_tex(contract: Contract) -> str:
    r"""Print the index of defined terms when a claim marks one with ``\term``."""
    if not any(TERM_RE.search(strip_comments(contract.claim(cid).body))
               for cid in contract.order):
        return ""
    return "\n\\clearpage\n\\bookmarksetupnext{level=part}\n\\printindex\n"


BIBLIOGRAPHY = ("\n\\clearpage\\phantomsection\\bookmarksetupnext{level=part}%\n"
                "\\addcontentsline{toc}{section}{References}\n"
                "\\bibliographystyle{plain}\n"
                "\\bibliography{../../../refs/references}\n")


def back_tex(contract: Contract) -> str:
    """Render the back matter: interface, claim index, terms index, bibliography."""
    return (interface_tex(contract) + claim_index_tex(contract)
            + terms_index_tex(contract) + BIBLIOGRAPHY + "\n\\end{document}\n")

