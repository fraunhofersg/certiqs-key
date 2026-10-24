r"""Motivation: a module's statements, readable in one sitting.

A contract carries every proof, remark and computational step, which is what
a reviewer needs and more than a reader who wants to know what the module
states. A statements-only digest per module gives that: every
definition, fact, assumption, result and requirement, with the contract's
numbers; remarks, examples, technical claims and all proofs are left out.
Written by hand it would be a second copy of every statement and drift; it is
generated here from the same claim files, and `assemble_contract` builds it
right after the contract, so the two cannot disagree.

How it keeps the contract's numbers:

- a heading prints the number `contract_structure` computes, and a LaTeX
  guard (`\digestlabel`) compares it with the contract's own number, read from
  `contract.aux` through xr-hyper, and stops the build on a difference;
- a display keeps its number: the contract labels every numbered display row
  of a digest claim's statement (`contract_render.number_displays`), and the
  digest's starred copy is tagged with that label's number from the aux;
- a reference between two digest items stays in the digest (a local label
  carrying the contract's number); a reference to anything the digest leaves
  out (a remark, a proof's display, an item label) becomes `\ref{C-<label>}`,
  which xr-hyper links into the contract PDF;
- each heading links to the claim's stable named destination `claim-<id>`
  in `contract.pdf` beside it.

The digest therefore needs the contract's `.aux`: it is compiled after the
contract and before the contract's auxiliary files are cleaned.
"""

from __future__ import annotations

import re

from harness.check_claims import LABEL_RE, Claim, environment_span, strip_comments
from harness.contract_frontmatter import STARRED_RE, restate
from harness.contract_navigation import KIND_WORD, plain_title, tex_text
from harness.contract_render import (
    Contract,
    declare_xrefs,
    in_digest,
    preamble,
    statement_of,
)

DIGEST_PREAMBLE = r"""
% The digest: the contract's labels under the prefix C-, its numbers checked.
\externaldocument[C-]{contract}
\theoremstyle{claim}\newtheorem*{digestclaim}{\RestatedName}
\theoremstyle{claimass}\newtheorem*{digestassumption}{\RestatedName}
\theoremstyle{claimreq}\newtheorem*{digestrequirement}{\RestatedName}
\makeatletter
% #1 label, #2 the number the assembler computed: a local label carrying it, so
% that a reference between two digest items stays in the digest; the build
% stops when the contract's own number differs.
\newcommand{\digestlabel}[2]{\phantomsection
  \edef\digest@theirs{\getrefnumber{C-#1}}\def\digest@ours{#2}%
  \ifx\digest@theirs\digest@ours\else
    \PackageError{digest}{#1 is #2 here but \digest@theirs\space in the contract}{}\fi
  \def\@currentlabel{#2}\label{#1}}
\makeatother
% A display's local label (amsmath records the \tag, i.e. the contract's number).
\newcommand{\digesteqlabel}[1]{\label{#1}}
"""
REF_RE = re.compile(r"\\(ref|eqref|pageref)\{([^}]*)\}")


def digest_tag(label: str) -> str:
    r"""Tag a display row with the contract's number and give it a local label."""
    return r"\tag{\getrefnumber{C-" + label + r"}}\digesteqlabel{" + label + "}"


def statement_content(contract: Contract, claim: Claim) -> str:
    """Return a claim's statement as the contract emits it, without its environment."""
    statement = statement_of(contract, claim).statement
    span = environment_span(strip_comments(statement))
    return "" if span is None else statement[span.content:span.close]


def display_labels(content: str) -> set[str]:
    """Return the labels inside a statement's numbered displays."""
    return {label for match in STARRED_RE.finditer(strip_comments(content))
            for label in LABEL_RE.findall(match.group(2))}


def digest_body(content: str, local: set[str]) -> str:
    """Copy a statement for the digest: tagged displays, references resolved."""
    text = restate(content, digest_tag,
                   lambda label: r"\digesteqlabel{" + label + "}")

    def point(match: re.Match[str]) -> str:
        command, label = match.group(1), match.group(2).strip()
        if label in local:
            return match.group(0)
        return f"\\{command}{{C-{label}}}"

    return REF_RE.sub(point, text)


def item_tex(contract: Contract, claim: Claim, number: str, local: set[str]) -> str:
    """Render one digest item: local label, bookmark, heading linked to the contract."""
    word = KIND_WORD.get(claim.kind, "Claim")
    title = str(claim.header.get("title", claim.label))
    env = {"ass": "digestassumption", "req": "digestrequirement"}.get(
        claim.kind, "digestclaim")
    out = [f"\n% claim {claim.claim_id}\n",
           f"\\digestlabel{{{claim.label}}}{{{number}}}"
           f"\\pdfbookmark[2]{{{word} {number} {tex_text(plain_title(title))}}}"
           f"{{digest-{claim.claim_id}}}\n"]
    if claim.kind == "ass":
        short_id = tex_text(str(claim.header.get("short_id") or ""))
        out.append(f"\\SetShortId{{{short_id}}}\n")
    main = claim.header.get("prominence") == "main"
    if main:
        out.append("\\begin{mainclaim}\n")
    out.append(f"\\renewcommand*{{\\RestatedName}}{{\\hyperref{{contract.pdf}}{{}}"
               f"{{claim-{claim.claim_id}}}{{{word}~{number}}}}}%\n"
               f"\\begin{{{env}}}[{title}]\n"
               f"{digest_body(statement_content(contract, claim), local)}\n"
               f"\\end{{{env}}}\n")
    if main:
        out.append("\\end{mainclaim}\n")
    return "".join(out)


def render_digest(contract: Contract) -> str:
    """Render the statements digest of one contract as TeX."""
    repo, core = contract.repo, contract.core
    meta = repo.modules[core].meta
    title = str(meta.get("title", core))
    version = str(meta.get("version", "0.0.0"))
    numbers = contract.structure.numbers()
    included = [cid for cid in contract.order if in_digest(contract.claim(cid))]
    local = {contract.claim(cid).label for cid in included}
    for cid in included:
        local |= display_labels(statement_content(contract, contract.claim(cid)))
    out = [preamble(f"{title} -- statements digest {version}", index=False, xr=True),
           DIGEST_PREAMBLE, declare_xrefs(repo, core),
           "\n\\begin{document}\n\\begin{center}\n",
           f"{{\\LARGE\\bfseries {tex_text(title)}}}\\\\[4pt]\n",
           f"{{\\large Statements digest, version {tex_text(version)}}}\n"
           "\\end{center}\n",
           "\\noindent{\\small Every definition, fact, assumption, result and "
           "requirement of the \\href{contract.pdf}{contract}, with the "
           "contract's numbers; remarks, examples, technical steps and all proofs "
           "are left out. Each heading opens its statement in the contract.}\n"]
    for part in contract.structure.parts:
        sections = [s for s in part.sections
                    if any(cid in included for cid in s.claims)]
        if not sections:
            continue
        part_title = tex_text(part.title)
        out.append(f"\n\\part*{{{part_title}}}"
                   f"\\pdfbookmark[0]{{{part_title}}}{{digest-part-{part.number}}}\n")
        for section in sections:
            heading = f"{section.number}\\quad {tex_text(section.title)}"
            out.append(f"\n\\section*{{{heading}}}"
                       f"\\pdfbookmark[1]{{{section.number} "
                       f"{tex_text(section.title)}}}{{digest-{section.anchor}}}\n")
            out += [item_tex(contract, contract.claim(cid), numbers[cid], local)
                    for cid in section.claims if cid in included]
    out.append("\n\\bibliographystyle{plain}\n"
               "\\bibliography{../../../refs/references}\n\n\\end{document}\n")
    return "".join(out)
