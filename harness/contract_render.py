r"""Motivation: a contract page a newcomer can read, generated from the claim files.

A contract that is one long run of claims, each preceded by a boxed
"Non-normative summary" and followed by nothing that says what it rests on,
what rests on it or where its code is, is hard to read. This module writes the
body of the page `spec/style.md` sections 3 to 6 describe:

- the preamble: the mathematics packages in the order the macro set needs, one
  shared theorem counter per section (`\newtheorem{theorem}{Theorem}[section]`,
  every other kind on it), upright statements, the prominence wrappers
  (`mainclaim`, a breakable tcolorbox with a rule in the margin, and
  `technicalclaim`), the non-normative styles, the meta-line commands, the
  mapped Unicode set of `contract_navigation.UNICODE_TEX`, and the claim-body
  commands (`\xref`, `\term`, `\iface`) a claim file cannot define itself;
- the parts and sections of `contract_structure.contract_sections()`, each
  section opening with its introduction and the claims of other contracts its
  claims use;
- each claim: its summary (grey italic, holding the stable named destination
  `claim-<full id>` that other PDFs, the graphs and the frontend link to), a
  numbered bookmark, the lead-in, the statement with its header title, the
  generated meta line, the proof. Text a claim file still carries after its
  statement or proof is printed where it stands, never dropped
  (`check_claims` reports it).

The meta line says what a reader otherwise had to ask a tool: what the claim
uses (for a requirement, what motivates it) and assumes, who assumes an
assumption and under which machine key the run ledger records it, what uses
the claim, its provenance and status (with the effective status when lower),
its code and the oracle registries pinning it. Every internal reference is a
link whose whole text ("Def. 2.1") is clickable; every foreign one prints the
target's full id, linked into the other contract's PDF at its named
destination (a relative URI, `<file>#nameddest=<destination>`, since browser
PDF viewers such as Edge's ignore hyperref's default GoToR action).

An assumption's meta line also prints its `category`, `affects` and `refines`
header fields when present. Whether the
engine verifies an assumption is not a hand-written sentence in its body (a
hand-kept copy of the `verification` field could disagree with it); every
assumption gets that sentence generated from the field
(`VERIFICATION_SENTENCES`), in the meta line's grey, followed by its
`user_statement` as a grey "Reading:" paragraph. Any other claim that carries a
`user_statement` (optional on every kind but a definition) gets the same "Reading:"
paragraph after its
statement, so the plain reading the key-rate report shows a user is printed
beside the statement it reads.

The front and back matter are `harness/contract_frontmatter.py`; the command
line and the build are `harness/assemble_contract.py`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import yaml

from harness.check_claims import (
    ENV_BEGIN_RE,
    REPODOC_RE,
    TERM_GLOSS_RE,
    TREF_RE,
    XREF_RE,
    Claim,
    DefinedTerm,
    Repo,
    contract_of,
    defined_terms,
    effective_status,
    environment_span,
    link_resolver,
    link_target,
    plain_text_fields,
    resolve_term,
    status_rank,
    strip_comments,
)
from harness.contract_navigation import (
    KIND_ABBREV,
    KIND_WORD,
    LINK_RE,
    contract_pdf,
    plain_title,
    tex_mapped,
    tex_plain,
    tex_safe,
    tex_text,
    unicode_declarations,
    xref_title,
)
from harness.contract_structure import ContractSections, Section, contract_sections
from harness.oracle_pins import OraclePin, oracle_pins

#: From a contract (spec/modules/<core>/contract.tex) to the repository root.
TO_ROOT = "../../../"
#: Where a code or registry link points by default: the hosted repository's
#: main branch. A contract rendered for another host (a public copy of the
#: tree) passes its own base as ``Contract(code_url=...)``, from the
#: assembler's ``--code-url``.
GITHUB = "https://github.com/fraunhofersg/certiqs-key/blob/v0.1.0/"
#: Numbered display environments a restated statement must re-tag.
NUMBERED_DISPLAYS = ("equation", "align", "gather", "multline", "flalign", "alignat")
DISPLAY_RE = re.compile(r"\\begin\{(" + "|".join(NUMBERED_DISPLAYS) + r")\}")
#: Displays whose every line carries a number of its own.
MULTILINE_DISPLAYS = ("align", "gather", "flalign", "alignat")
NUMBER_MARK_RE = re.compile(r"\\(?:label|tag|notag|nonumber)(?![A-Za-z])")
PROOF_BEGIN_RE = re.compile(r"\\begin\{proof\}")
#: An interface key or machine key: what ``\iface`` can print verbatim.
KEY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
#: The sentence printed after every assumption, from its ``verification`` field
#: (spec/claim-format.md sections 3.2 and 7): the field is the one source, so
#: the body does not say it by hand. ``decided`` and ``discharged`` are refused
#: on an assumption, so no sentence exists for them.
VERIFICATION_SENTENCES: dict[str, str] = {
    "never": "The engine does not verify this assumption; a run that rests on it "
             "records it as unverified.",
    "partly": "The engine decides part of this assumption; the rest is attested.",
}


def category_words(category: str) -> str:
    """Print a ``category`` value as words: "channel-and-adversary" as three."""
    return category.replace("-", " ")


class AssemblyError(Exception):
    """The module cannot be assembled; the message says why."""


PREAMBLE_HEAD = r"""% GENERATED FILE -- DO NOT EDIT.
%
% Produced by harness/assemble_contract.py from module.yaml and claims/*.tex.
% Edit the claim files and regenerate; `--check` fails if this file is stale.
\documentclass[11pt,a4paper]{article}
%% --- 1. Mathematics (order matters: physics after braket wins \ket, \tr) ---
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}
\usepackage{amsthm}
\usepackage{mathtools}
\usepackage{dsfont}
\usepackage{braket}
\usepackage{physics}
%% --- 2. Page furniture ------------------------------------------------------
\usepackage{xcolor}
\usepackage{array}    % >{...} column prefixes in the wide tables of some claims
\usepackage{enumitem}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{xltabular}              % front- and back-matter tables across pages
\usepackage{needspace}
\usepackage{xurl}
\usepackage[noautomatic]{imakeidx}  % defined-terms index; latexmk runs makeindex
\makeindex[title=Index of defined terms,intoc]
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable}
%% --- 3. Links and navigation (hyperref late; bookmark, refcount after it) ---
\usepackage{hyperref}
\usepackage{bookmark}
\usepackage{refcount}
%% --- 4. Colours: every distinction also has a shape (rule, caps, size, weight)
\definecolor{nnGrey}{gray}{0.40}      % non-normative text
\definecolor{metaGrey}{gray}{0.30}    % the generated meta line
\definecolor{techGrey}{gray}{0.45}    % heading of a technical claim
\definecolor{mainRule}{RGB}{0,110,140}
\definecolor{reqAccent}{RGB}{165,70,0}
\definecolor{linkBlue}{RGB}{0,62,150}
\definecolor{extLink}{RGB}{120,40,140}  % links into another PDF
\hypersetup{colorlinks=true, linkcolor=linkBlue, citecolor=linkBlue,
  urlcolor=linkBlue, filecolor=extLink, bookmarksnumbered=true,
  bookmarksopen=true, bookmarksopenlevel=1, pdfdisplaydoctitle=true}
% A link into another PDF (\href to a .pdf, \hyperref{file}..., xr-hyper) is a
% relative URI, <file>#nameddest=<destination>, in the file-link colour:
% browser viewers (Edge, Chrome) ignore hyperref's default GoToR action.
\makeatletter
\renewcommand*{\hyper@linkfile}[3]{% anchor text, file name, destination
  \begingroup
    \ifx\\#3\\\def\CQ@target{#2}\else\def\CQ@target{#2\hyper@hash nameddest=#3}\fi
    \let\@urlcolor\@filecolor
    \hyper@linkurl{#1}{\CQ@target}%
  \endgroup}
\makeatother
%% --- 5. The mapped Unicode set (harness/contract_navigation.py, UNICODE_TEX)
"""

PREAMBLE_TAIL = r"""%% --- 6. Numbering: one counter per section -----------------------
\numberwithin{equation}{section}
\setcounter{tocdepth}{1}
%% --- 7. The project macro set, then the claim environments -----------------
% spec/macros.tex, read relative to this module's directory (latexmk -cd).
\input{../../macros}
\makeatletter
\newcommand*{\ClaimHeadFont}{\bfseries}   % switched by prominence
\newcommand*{\ClaimNoteFont}{\mdseries}
\newcommand*{\ClaimShortId}{}
\newcommand*{\SetShortId}[1]{\renewcommand*{\ClaimShortId}{#1}}
\newcommand*{\RestatedName}{}
% Upright bodies throughout: italic is reserved for non-normative text.
% \@endparpenalty\@M keeps the meta line on the statement's page.
\newtheoremstyle{claim}{\topsep}{\topsep}{\normalfont\@endparpenalty\@M}{}%
  {\ClaimHeadFont}{.}{.5em}{\thmname{#1}\thmnumber{ #2}\thmnote{ {\ClaimNoteFont(#3)}}}
\newtheoremstyle{claimass}{\topsep}{\topsep}{\normalfont\@endparpenalty\@M}{}%
  {\ClaimHeadFont}{.}{.5em}{\thmname{#1}\thmnumber{ #2}%
  \ifx\ClaimShortId\@empty\else\ [\textsf{\ClaimShortId}]\fi%
  \thmnote{ {\ClaimNoteFont(#3)}}}
\newtheoremstyle{claimremark}{.5\topsep}{.5\topsep}{\small\@endparpenalty\@M}{}%
  {\itshape}{.}{.5em}{\thmname{#1}\thmnumber{ #2}\thmnote{ {\upshape(#3)}}}
\newtheoremstyle{claimreq}{\topsep}{\topsep}{\normalfont\@endparpenalty\@M}{}%
  {\color{reqAccent}\scshape}{.}{.5em}%
  {\thmname{#1}\thmnumber{ #2}\thmnote{ {\upshape(#3)}}}
\makeatother
\theoremstyle{claim}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{fact}[theorem]{Fact}
\newtheorem{definition}[theorem]{Definition}
\newtheorem*{restatedclaim}{\RestatedName}
\theoremstyle{claimass}
\newtheorem{assumption}[theorem]{Assumption}
\newtheorem*{restatedassumption}{\RestatedName}
\theoremstyle{claimremark}
\newtheorem{remark}[theorem]{Remark}
\newtheorem{example}[theorem]{Example}
\theoremstyle{claimreq}
\newtheorem{requirement}[theorem]{Requirement}
\newtheorem*{restatedrequirement}{\RestatedName}
%% --- 8. Prominence: main results a margin rule and a bold heading ----------
\newtcolorbox{mainclaim}{enhanced jigsaw, breakable, blanker,
  borderline west={1.5pt}{-8pt}{mainRule}, left=0pt, right=0pt, top=0pt, bottom=0pt,
  boxsep=0pt, before skip=\topsep, after skip=\topsep, parbox=false,
  before upper={\renewcommand*{\ClaimNoteFont}{\bfseries}}}
\newenvironment{technicalclaim}{\renewcommand*{\ClaimHeadFont}{\mdseries\color{techGrey}}%
  \renewcommand*{\ClaimNoteFont}{}}{}
%% --- 9. Non-normative text, the meta line, navigation ------------------------
\makeatletter
% Tie what follows to this paragraph: no page break, no list penalty before
% the next theorem head (the \@nobreak route a section heading uses).
\newcommand{\keepwithnext}{\par\nobreak\vspace{3pt}\@nobreaktrue
  \everypar{\if@nobreak\@nobreakfalse\clubpenalty\@M\else\clubpenalty\@clubpenalty\everypar{}\fi}}
\newcommand{\claimsummary}[2]{% #1 claim id (named destination), #2 summary
  \par\addvspace{\bigskipamount}\Needspace{6\baselineskip}%
  {\small\itshape\color{nnGrey}\noindent\hypertarget{claim-#1}{}#2\par}\keepwithnext}
\newcommand{\claimanchor}[1]{% a claim without a summary: the destination alone
  \par\addvspace{\bigskipamount}\Needspace{6\baselineskip}%
  \phantomsection\hypertarget{claim-#1}{}\keepwithnext}
\newcommand{\claimleadin}[1]{{\color{nnGrey}\noindent#1\par}\keepwithnext}
\newcommand{\claimmeta}[1]{\par\nobreak\vspace{2pt}%
  {\footnotesize\color{metaGrey}\raggedright\interlinepenalty\@M\noindent#1\par}%
  \addvspace{\medskipamount}}
% After an assumption: the sentence generated from its verification field; after
% any claim with one: its plain-text reading (user_statement). Both
% non-normative, both grey.
\newcommand{\claimverification}[1]{\par\nobreak\vspace{2pt}%
  {\footnotesize\color{metaGrey}\noindent#1\par}\nobreak}
\newcommand{\claimreading}[1]{\par\nobreak\vspace{2pt}%
  {\footnotesize\color{nnGrey}\noindent\emph{Reading:}\enspace#1\par}\nobreak}
\makeatother
\newcommand{\claimbookmark}[4]{% #1 id, #2 kind word, #3 label, #4 plain title
  \bookmark[dest=claim-#1,level=2]{#2 \getrefnumber{#3} #4}}
\newcommand{\metasep}{\unskip\enspace\textperiodcentered\enspace\ignorespaces}
\newcommand{\metalabel}[1]{\emph{#1}\enspace}
\newcommand{\sectionintro}[1]{{\color{nnGrey}\noindent#1\par}\smallskip}
\newcommand{\sectionimports}[1]{{\footnotesize\color{metaGrey}\raggedright\noindent\metalabel{Imports}#1\par}\smallskip}
\newenvironment{overview}{\par\color{nnGrey}\itshape\noindent\ignorespaces}{\par}
% References: the whole "Def. 2.1" is the link; ids are the fallback text of
% every link into another PDF (a relative URI to a named destination).
\newcommand{\mref}[2]{\hyperref[#2]{#1~\ref*{#2}}}
\newcommand{\aref}[2]{\hyperref[#2]{\textsf{#1}}}
\DeclareUrlCommand{\claimid}{\urlstyle{sf}\def\UrlBreaks{\do\/\do\:\do\-\do\.\do\_}%
  \def\UrlBigBreaks{}\def\UrlNoBreaks{}}
\newcommand{\extref}[2]{\hyperref{#1}{}{claim-#2}{\claimid{#2}}}
\newcommand{\extaref}[3]{\hyperref{#1}{}{claim-#2}{\textsf{#3}}}
\newcommand{\coderef}[2]{\href{#1}{\claimid{#2}}}
% Claim-body commands (spec/claim-format.md section 4): \xref{<full id>} prints
% the kind, title and id of a claim of another contract, linked to its stable
% destination in that contract's PDF (one \DeclareXref per cited claim below);
% \term[gloss]{phrase} marks a defined phrase for the index (the gloss feeds
% the Terms table); \tref[phrase]{text} is a use of a defined term. The
% assembler rewrites both in the body into \termdef (the definition's named
% destination term-<slug>) and \termref / \exttermref (a link to it, in this
% or another contract's PDF); the fallbacks below serve text it copies
% elsewhere, such as the digest. \iface is an interface key.
\makeatletter
\newcommand{\DeclareXref}[4]{% id, kind word, title, contract PDF
  \@namedef{xref@#1}{\hyperref{#4}{}{claim-#1}{#2 ``#3'' ({\small\claimid{#1}})}}}
\newcommand{\xref}[1]{\@ifundefined{xref@#1}%
  {\textbf{[unresolved \nolinkurl{#1}]}\@latex@warning{Unresolved xref #1}}%
  {\@nameuse{xref@#1}}}
\makeatother
\DeclareUrlCommand{\iface}{\urlstyle{tt}}
\newcommand{\term}[2][]{\emph{#2}\index{#2}}
\newcommand{\tref}[2][]{#2}
\newcommand{\termdef}[2]{\hypertarget{#1}{}\emph{#2}\index{#2}}
\newcommand{\termref}[2]{\hyperlink{#1}{#2}}
\newcommand{\exttermref}[3]{\hyperref{#1}{}{#2}{#3}}
"""


INDEX_LINES = ("\\usepackage[noautomatic]{imakeidx}  % defined-terms index; latexmk "
               "runs makeindex\n\\makeindex[title=Index of defined terms,intoc]\n")
HYPERREF_LINE = "\\usepackage{hyperref}\n"
MACROS_LINE = "\\input{../../macros}\n"


def preamble(pdftitle: str, *, macros: str = "../../macros", index: bool = True,
             xr: bool = False) -> str:
    """Return the preamble of a contract, or of the digest or overview built with it.

    ``pdftitle`` is plain text for the PDF's metadata. ``macros`` is the path
    of ``spec/macros`` from the document's directory; ``index`` loads the
    defined-terms index (a contract's); ``xr`` loads xr-hyper before hyperref,
    as a document that reads another's labels must (the digest).
    """
    head, tail = PREAMBLE_HEAD, PREAMBLE_TAIL
    if not index:
        head = head.replace(INDEX_LINES, "")
    if xr:
        head = head.replace(HYPERREF_LINE, "\\usepackage{xr-hyper}   % before "
                            "hyperref: the contract's labels\n" + HYPERREF_LINE)
    tail = tail.replace(MACROS_LINE, f"\\input{{{macros}}}\n")
    return (head + unicode_declarations() + tail
            + f"\\hypersetup{{pdftitle={{{tex_text(pdftitle)}}}}}\n")


#: The kinds a statements-only digest holds (technical claims are left out too).
DIGEST_KINDS = frozenset({"def", "fact", "ass", "thm", "lem", "prop", "cor", "req"})


def in_digest(claim: Claim) -> bool:
    """Whether a claim's statement belongs in the module's statements digest."""
    return (claim.kind in DIGEST_KINDS
            and claim.header.get("prominence") != "technical")


def repodoc_link(match: re.Match[str]) -> str:
    r"""Rewrite ``\repodoc{path#anchor}`` into a relative link showing the path.

    ``#`` inside a macro argument must reach ``\href`` as ``\#``; the checker
    restricts paths and anchors to letters, digits and ``._-/``.
    """
    path, _, anchor = match.group(1).strip().partition("#")
    target = TO_ROOT + path + (r"\#" + anchor if anchor else "")
    shown = r"\nolinkurl{" + path + "}" + (r"\texttt{\#" + tex_text(anchor) + "}"
                                           if anchor else "")
    return r"\href{" + target + "}{" + shown + "}"


def inject_title(statement: str, title: str) -> str:
    """Give the claim environment its title (the file carries none, check 2)."""
    match = ENV_BEGIN_RE.search(statement)
    if match is None:
        return statement
    return statement[: match.end()] + f"[{title}]" + statement[match.end():]


@dataclass(frozen=True)
class ClaimParts:
    """A claim body cut at its environment and proof, in reading order."""

    lead: str          # before the environment
    statement: str     # \begin{env} ... \end{env}
    between: str       # between the environment and the proof
    proof: str         # \begin{proof} ... \end{proof}
    trailing: str      # after the proof (or the environment)


def split_body(body: str) -> ClaimParts:
    """Cut a claim body; offsets come from the comment-blanked text.

    ``check_claims.strip_comments`` keeps every offset, so the pieces are cut
    from the body as written, comments included. A body without a claim
    environment is all statement (the checker reports it).
    """
    blank = strip_comments(body)
    span = environment_span(blank)
    if span is None:
        return ClaimParts("", body.strip(), "", "", "")
    rest = span.end
    between = proof = ""
    opening = PROOF_BEGIN_RE.search(blank, span.end)
    if opening is not None:
        close = blank.find("\\end{proof}", opening.end())
        end = len(body) if close == -1 else close + len("\\end{proof}")
        between = body[span.end:opening.start()]
        proof, rest = body[opening.start():end], end
    return ClaimParts(body[:span.begin], body[span.begin:span.end], between, proof,
                      body[rest:])


def has_text(tex: str) -> bool:
    """Whether a piece of TeX holds anything but whitespace and comments."""
    return bool(strip_comments(tex).strip())


def line_ends(content: str) -> list[int]:
    r"""Return the offsets of the top-level ``\\`` row ends of a display body."""
    blank = strip_comments(content)
    ends: list[int] = []
    braces = environments = 0
    index = 0
    while index < len(blank):
        if blank.startswith("\\begin{", index):
            environments += 1
        elif blank.startswith("\\end{", index):
            environments -= 1
        if blank.startswith("\\\\", index):
            if braces == 0 and environments == 0:
                ends.append(index)
            index += 2
            continue
        char = blank[index]
        if char == "\\":
            index += 2
            continue
        if char == "{":
            braces += 1
        elif char == "}":
            braces -= 1
        index += 1
    return ends


def number_displays(statement: str, stem: str) -> str:
    r"""Label every numbered display row of a statement that carries no label.

    A main result is restated in the front matter with its displays tagged by
    their numbers (``\tag{\ref*{<label>}}``, SPIKE.md 2.9), which needs a label
    on every numbered row; an unlabelled row gets ``eq:auto-<stem>-<n>``. A
    row with ``\tag``, ``\notag`` or ``\nonumber`` is left alone.
    """
    out: list[str] = []
    position = count = 0
    for match in DISPLAY_RE.finditer(statement):
        env = match.group(1)
        head = match.end()
        if env == "alignat":
            argument = re.match(r"\s*\{[^{}]*\}", statement[head:])
            head += argument.end() if argument else 0
        close = statement.find(f"\\end{{{env}}}", head)
        if close == -1 or match.start() < position:
            continue
        content = statement[head:close]
        rows: list[tuple[int, int]] = []
        start = 0
        if env in MULTILINE_DISPLAYS:
            for end in line_ends(content):
                rows.append((start, end))
                start = end + 2
        rows.append((start, len(content)))
        pieces: list[str] = []
        cursor = 0
        for index, (start, stop) in enumerate(rows):
            pieces.append(content[cursor:start])
            row = content[start:stop]
            blank = strip_comments(row)
            empty_last = index and index == len(rows) - 1 and not blank.strip()
            if NUMBER_MARK_RE.search(blank) is None and not empty_last:
                count += 1
                cut = len(blank.rstrip())
                row = row[:cut] + f"\\label{{eq:auto-{stem}-{count}}}" + row[cut:]
            pieces.append(row)
            cursor = stop
        out.append(statement[position:head] + "".join(pieces))
        position = close
    out.append(statement[position:])
    return "".join(out)


def ledger_machine_key(interface: Any, short_id: str) -> str | None:
    """Return the ``machine_key`` of the ``interface`` row whose ``id`` is ``short_id``.

    The owner's interface.yaml is the one place a run ledger's key is written
    (spec/claim-format.md section 5); the walk is breadth-first, so a row
    nearer the top wins. None when no such row carries a key.
    """
    stack = [interface]
    while stack:
        node = stack.pop(0)
        if isinstance(node, dict):
            if node.get("id") == short_id and node.get("machine_key"):
                return str(node["machine_key"])
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return None


class Contract:
    """One contract being rendered: the repository, its structure and lookups."""

    def __init__(self, root: Path, repo: Repo, core: str, *,
                 code_url: str = GITHUB) -> None:
        """Read the structure and every table the meta lines need.

        ``code_url`` is the base every code and registry link is written under.
        """
        self.root = root
        self.code_url = code_url
        self.repo = repo
        self.core = core
        if core not in repo.modules:
            raise AssemblyError(f"spec/modules/{core}/module.yaml: no module.yaml")
        try:
            self.structure: ContractSections = contract_sections(repo, core)
        except ValueError as exc:
            raise AssemblyError(f"{core}: {exc}") from exc
        self.order = self.structure.claims()
        self.position = {cid: index for index, cid in enumerate(self.order)}
        self.used_by: dict[str, list[str]] = {}
        self.assumed_by: dict[str, list[str]] = {}
        for other in repo.claims.values():
            for target in dict.fromkeys(other.resolved_uses):
                self.used_by.setdefault(target, []).append(other.claim_id)
            for short_id in dict.fromkeys(other.assumes):
                self.assumed_by.setdefault(short_id, []).append(other.claim_id)
        self.pins: dict[str, tuple[OraclePin, ...]] = oracle_pins(root)
        self._interfaces: dict[str, Any] = {}

    # --- lookups ---------------------------------------------------------------

    def claim(self, claim_id: str) -> Claim:
        """Return a claim of this contract, or raise ``AssemblyError`` saying why."""
        claim = self.repo.claims.get(claim_id)
        if claim is not None:
            return claim
        module_id, _, label = claim_id.rpartition("/")
        path = (self.root / "spec" / "modules" / module_id / "claims"
                / (label.replace(":", "-", 1) + ".tex"))
        if not path.is_file():
            raise AssemblyError(f"{path.as_posix()}: claim file not found")
        found = [error.render() for error in self.repo.errors
                 if error.path.endswith(path.name) and module_id in error.path]
        raise AssemblyError(found[0] if found else
                            f"{path.as_posix()}: claim file could not be read")

    def local(self, claim_id: str) -> bool:
        """Whether a claim belongs to this contract (the core or a submodule)."""
        return contract_of(claim_id) == self.core

    def sorted_ids(self, ids: list[str]) -> list[str]:
        """Order claim ids: this contract's in document order, then others by id."""
        unique = list(dict.fromkeys(ids))
        return sorted(unique, key=lambda cid: (0, self.position[cid], cid)
                      if cid in self.position else (1, 0, cid))

    def ref(self, claim_id: str) -> str:
        """Refer to a claim: "Def. 2.1" inside, the full id into another PDF."""
        claim = self.repo.claims.get(claim_id)
        if claim is None:
            return r"\claimid{" + claim_id + "}"
        if self.local(claim_id):
            return f"\\mref{{{KIND_ABBREV.get(claim.kind, 'Claim')}}}{{{claim.label}}}"
        return f"\\extref{{{contract_pdf(contract_of(claim_id), 'contract')}}}" \
               f"{{{claim_id}}}"

    def word_ref(self, claim_id: str) -> str:
        """Refer to a claim of this contract, kind written out ("Proposition 7.3")."""
        claim = self.repo.claims[claim_id]
        return f"\\mref{{{KIND_WORD.get(claim.kind, 'Claim')}}}{{{claim.label}}}"

    def short_ref(self, short_id: str) -> str:
        """Print an assumption's short id, linked to where it is stated."""
        owner = self.repo.assumptions.get(short_id)
        if owner is None:
            return r"\textsf{" + tex_text(short_id) + "}"
        if self.local(owner.claim_id):
            return f"\\aref{{{short_id}}}{{{owner.label}}}"
        return (f"\\extaref{{{contract_pdf(contract_of(owner.claim_id), 'contract')}}}"
                f"{{{owner.claim_id}}}{{{short_id}}}")

    def interface(self, module_id: str) -> Any:
        """Return a module's parsed ``interface.yaml`` (None when it has none)."""
        if module_id not in self._interfaces:
            path = self.root / "spec" / "modules" / module_id / "interface.yaml"
            loaded: Any = None
            if path.is_file():
                try:
                    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
                except yaml.YAMLError as exc:
                    raise AssemblyError(f"{path.as_posix()}: not valid YAML: "
                                        f"{exc}") from exc
            self._interfaces[module_id] = loaded
        return self._interfaces[module_id]

    def machine_key(self, short_id: str) -> str | None:
        """Return the run ledger's key for an assumption, if its owner records one.

        The owner is the module holding the assumption claim; its key is the
        ``machine_key`` of the mapping in that file whose ``id`` is the short
        id. None when there is no such row.
        """
        owner = self.repo.assumptions.get(short_id)
        if owner is None:
            return None
        return ledger_machine_key(self.interface(owner.module_id), short_id)

    @cached_property
    def bibtex_keys(self) -> dict[str, str]:
        """Map each registered ref-id to its BibTeX key (``refs/index.json``)."""
        path = self.root / "refs" / "index.json"
        if not path.is_file():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("entries", []) if isinstance(data, dict) else []
        return {str(entry["ref_id"]): str(entry.get("bibtex_key") or entry["ref_id"])
                for entry in entries if isinstance(entry, dict) and entry.get("ref_id")}

    def plain(self, text: str, module_id: str) -> str:
        """Render a plain-text field of ``module_id`` with its ``[[...]]`` links."""
        return tex_plain(text, link_resolver(self.repo, module_id), self.core)

    # --- defined terms -----------------------------------------------------------

    @cached_property
    def terms(self) -> list[DefinedTerm]:
        r"""The terms this contract's definitions mark with ``\term``."""
        return [term for (owner, _key), term in defined_terms(self.repo).items()
                if owner == self.core]

    def term_link(self, term: DefinedTerm, text: str) -> str:
        """Link ``text`` (TeX) to a term's definition, here or in its own PDF."""
        if term.contract == self.core:
            return f"\\termref{{{term.anchor}}}{{{text}}}"
        return (f"\\exttermref{{{contract_pdf(term.contract, 'contract')}}}"
                f"{{{term.anchor}}}{{{text}}}")

    def body_terms(self, text: str) -> str:
        r"""Give each ``\term`` its destination and link each ``\tref`` use.

        An unresolved ``\tref`` keeps its text (the checker reports it).
        """
        def define(match: re.Match[str]) -> str:
            phrase = " ".join(match.group(2).split())
            found = resolve_term(self.repo, self.core, phrase)
            anchor = found.anchor if isinstance(found, DefinedTerm) else "term-x"
            return f"\\termdef{{{anchor}}}{{{match.group(2)}}}"

        def use(match: re.Match[str]) -> str:
            found = resolve_term(self.repo, self.core, match.group(1) or match.group(2))
            if isinstance(found, str):
                return match.group(2)
            return self.term_link(found, match.group(2))

        return TREF_RE.sub(use, TERM_GLOSS_RE.sub(define, text))

    def plain_linked(self, text: str, module_id: str) -> str:
        """Render a plain-text field, linking the first use of each defined term.

        The overview and the section introductions use the contract's jargon
        before its definitions; the first use of each multi-word term this
        contract defines links to the definition. Text inside a ``[[...]]``
        link is left alone.
        """
        flat = " ".join(text.split())
        links = [match.span() for match in LINK_RE.finditer(flat)]
        found: list[tuple[int, int, DefinedTerm]] = []
        longest_first = sorted(self.terms,
                               key=lambda t: (-len(t.phrase.split()), t.phrase))
        for term in longest_first:
            if len(term.phrase.split()) < 2 or re.search(r"[\\$]", term.phrase):
                continue
            words = [re.escape(word) for word in term.phrase.split()]
            pattern = re.compile(r"(?<![A-Za-z-])" + r"\s+".join(words)
                                 + r"(?:s|es)?(?![A-Za-z-])", re.I)
            for match in pattern.finditer(flat):
                start, end = match.span()
                if any(s < end and start < e for s, e in links) or any(
                        s < end and start < e for s, e, _t in found):
                    continue
                found.append((start, end, term))
                break
        pieces: list[str] = []
        position = 0
        marks: dict[str, str] = {}
        for number, (start, end, term) in enumerate(sorted(found, key=lambda f: f[0])):
            mark = f"\x00{number}\x00"
            marks[mark] = self.term_link(term, tex_mapped(flat[start:end]))
            pieces += [flat[position:start], mark]
            position = end
        pieces.append(flat[position:])
        rendered = self.plain("".join(pieces), module_id)
        for mark, link in marks.items():
            rendered = rendered.replace(mark, link)
        return rendered


# --- the claim-body cross references -------------------------------------------


def foreign_citations(repo: Repo, core: str) -> list[str]:
    r"""Return the claims of other contracts this contract cites, sorted.

    They are the ``\xref`` targets of its claim bodies and the claim targets
    of the ``[[...]]`` links of its summaries and abstracts; each needs one
    ``\DeclareXref`` line. A target that is no claim is left out: the checker
    reports it, and ``\xref`` prints it as unresolved.
    """
    cited: set[str] = set()
    for claim in repo.claims.values():
        if contract_of(claim.claim_id) != core:
            continue
        for match in XREF_RE.finditer(strip_comments(claim.body)):
            cited.add(match.group(1).strip())
    for item in plain_text_fields(repo):
        if contract_of(item.module_id) != core:
            continue
        for match in LINK_RE.finditer(item.text):
            target = link_target(repo, item.module_id, match.group(1))
            if target is not None and not target.short_id:
                cited.add(target.claim_id)
    return sorted(cid for cid in cited
                  if cid in repo.claims and contract_of(cid) != core)


def declare_xrefs(repo: Repo, core: str) -> str:
    r"""Return the ``\DeclareXref`` lines of one contract (empty when it cites none)."""
    lines = []
    for cid in foreign_citations(repo, core):
        claim = repo.claims[cid]
        title = xref_title(str(claim.header.get("title", claim.label)))
        lines.append(f"\\DeclareXref{{{cid}}}{{{KIND_WORD.get(claim.kind, 'Claim')}}}"
                     f"{{{title}}}{{{contract_pdf(contract_of(cid), 'contract')}}}\n")
    if not lines:
        return ""
    return ("\n% Claims of other contracts cited here (\\xref, [[...]]).\n"
            + "".join(lines))


# --- the meta line --------------------------------------------------------------


def code_link(root: Path, dotted: str, base: str = GITHUB) -> str:
    """Link an ``implements`` entry to its file under ``base``, the hosted tree."""
    module, _, _ = dotted.strip().partition(":")
    path = "src/" + module.replace(".", "/") + ".py"
    if not (root / path).is_file() and (root / path[:-3] / "__init__.py").is_file():
        path = path[:-3] + "/__init__.py"
    return f"\\coderef{{{base}{path}}}{{{dotted.strip()}}}"


def citation(contract: Contract, entry: str) -> str:
    r"""Render one ``refs`` entry ("ref-id, locator") as ``\cite[locator]{key}``."""
    ref_id, _, locator = entry.partition(",")
    key = contract.bibtex_keys.get(ref_id.strip(), ref_id.strip())
    locator = locator.strip()
    return (f"\\cite[{{{tex_mapped(locator)}}}]{{{key}}}" if locator
            else f"\\cite{{{key}}}")


def implements_of(claim: Claim) -> list[str]:
    """Return a claim's ``implements`` entries (a string or a list of them)."""
    value = claim.header.get("implements")
    if not value:
        return []
    entries = value if isinstance(value, list) else [value]
    return [str(entry) for entry in entries if str(entry).strip()]


def assumption_items(contract: Contract, claim: Claim) -> list[str]:
    """Return an assumption's Category, Affects and Refines meta items, when present."""
    items: list[str] = []
    category = claim.header.get("category")
    if isinstance(category, str) and category:
        items.append(r"\metalabel{Category}" + tex_text(category_words(category)))
    affects = claim.header.get("affects")
    if isinstance(affects, list) and affects:
        items.append(r"\metalabel{Affects}"
                     + ", ".join(tex_text(str(item)) for item in affects))
    refines = claim.header.get("refines")
    if isinstance(refines, str) and refines:
        items.append(r"\metalabel{Refines}" + contract.short_ref(refines))
    return items


def claim_notes(contract: Contract, claim: Claim) -> str:
    r"""Return the grey lines after a statement: verification sentence, reading.

    For an assumption the verification sentence (``VERIFICATION_SENTENCES``)
    comes first; the ``user_statement`` of any claim that carries one follows
    as a "Reading:" paragraph, its links rendered as in a summary.
    """
    out = ""
    verification = str(claim.header.get("verification") or "")
    if claim.kind == "ass" and verification in VERIFICATION_SENTENCES:
        out += f"\\claimverification{{{VERIFICATION_SENTENCES[verification]}}}\n"
    reading = claim.header.get("user_statement")
    if isinstance(reading, str) and reading.strip():
        out += ("\\claimreading{" + contract.plain(reading.strip(), claim.module_id)
                + "}\n")
    return out


def meta_line(contract: Contract, claim: Claim) -> str:
    r"""Return the claim's ``\claimmeta{...}`` line (spec/style.md section 3)."""
    items: list[str] = []
    targets = list(claim.resolved_uses)
    if claim.kind == "req":
        targets += claim.resolved_mentions
    if targets:
        word = "Motivated by" if claim.kind == "req" else "Uses"
        items.append(f"\\metalabel{{{word}}}"
                     + ", ".join(contract.ref(t) for t in contract.sorted_ids(targets)))
    if claim.assumes:
        items.append(r"\metalabel{Assumes}" + ", ".join(
            contract.short_ref(s) for s in dict.fromkeys(claim.assumes)))
    short_id = str(claim.header.get("short_id") or "")
    if claim.kind == "ass":
        items += assumption_items(contract, claim)
    if claim.kind == "ass" and short_id:
        assumers = contract.assumed_by.get(short_id, [])
        if assumers:
            items.append(r"\metalabel{Assumed by}" + ", ".join(
                contract.ref(t) for t in contract.sorted_ids(assumers)))
        key = contract.machine_key(short_id)
        if key:
            # a key is an identifier; a ledger row written as prose keeps its spaces
            shown = (r"\iface{" + key + "}" if KEY_RE.match(key)
                     else r"\texttt{" + tex_safe(key) + "}")
            items.append(r"\metalabel{Machine key}" + shown)
    users = contract.used_by.get(claim.claim_id, [])
    if users:
        items.append(r"\metalabel{Used by}" + ", ".join(
            contract.ref(t) for t in contract.sorted_ids(users)))
    if claim.kind != "req":
        refs = [str(entry) for entry in claim.header.get("refs") or []]
        if claim.header.get("provenance") == "published":
            items.append("published" + (" in " if refs else "") + "; ".join(
                citation(contract, entry) for entry in refs))
        else:
            items.append("newly derived")
    effective = effective_status(contract.repo, claim.claim_id)[0]
    status = claim.status
    if status_rank(effective) < status_rank(status):
        status += f" (effective: {effective})"
    items.append(status)
    code = implements_of(claim)
    if code:
        items.append(r"\metalabel{Code}" + ", ".join(
            code_link(contract.root, entry, contract.code_url) for entry in code))
    pins = contract.pins.get(claim.claim_id, ())
    if pins:
        # The registry files only: the oracle codes they pin by are the
        # registries' vocabulary, not the contract's (spec/style.md section 7).
        registries = sorted({path for pin in pins for path in pin.registries})
        items.append(r"\metalabel{Oracles}" + ", ".join(
            f"\\coderef{{{contract.code_url}{path}}}{{{path.rsplit('/', 1)[-1]}}}"
            for path in registries))
    return "\\claimmeta{" + "\n\\metasep ".join(items) + "}"


# --- claims, sections, parts ------------------------------------------------------


def statement_of(contract: Contract, claim: Claim) -> ClaimParts:
    """Return a claim's pieces as emitted: title injected, links rendered.

    The unlabelled numbered displays of a statement that is copied elsewhere
    (a main result into the front matter, every digest claim into the digest)
    get labels here, so that the copy can carry their numbers.
    """
    body = REPODOC_RE.sub(repodoc_link, claim.body)
    parts = split_body(body)
    title = str(claim.header.get("title", claim.label))
    statement = inject_title(parts.statement, title)
    if in_digest(claim):          # every main result is a digest claim
        statement = number_displays(statement, claim.label.replace(":", "-"))
    return ClaimParts(parts.lead, statement, parts.between, parts.proof, parts.trailing)


def claim_tex(contract: Contract, claim_id: str) -> str:
    """Render one claim: summary, bookmark, lead-in, statement, meta line, proof."""
    claim = contract.claim(claim_id)
    parts = statement_of(contract, claim)
    title = str(claim.header.get("title", claim.label))
    summary = str(claim.header.get("summary") or "").strip()
    prominence = str(claim.header.get("prominence") or "standard")
    rendered = contract.plain(summary, claim.module_id)
    out = [f"\n% claim {claim_id}\n",
           (f"\\claimsummary{{{claim_id}}}{{{rendered}}}\n"
            if summary else f"\\claimanchor{{{claim_id}}}\n"),
           f"\\claimbookmark{{{claim_id}}}{{{KIND_WORD.get(claim.kind, 'Claim')}}}"
           f"{{{claim.label}}}{{{tex_text(plain_title(title))}}}\n"]
    lead = contract.body_terms(parts.lead)
    if has_text(lead):
        out.append("\\claimleadin{%\n" + lead.strip() + "\n}\n")
    elif lead.strip():
        out.append(lead.strip() + "\n")
    if claim.kind == "ass":
        short_id = tex_text(str(claim.header.get("short_id") or ""))
        out.append(f"\\SetShortId{{{short_id}}}\n")
    wrapper = {"main": "mainclaim", "technical": "technicalclaim"}.get(prominence)
    if wrapper:
        out.append(f"\\begin{{{wrapper}}}\n")
    out.append(contract.body_terms(parts.statement).strip() + "\n")
    if wrapper:
        out.append(f"\\end{{{wrapper}}}\n")
    out.append(claim_notes(contract, claim))
    out.append(meta_line(contract, claim) + "\n")
    for piece in (parts.between, parts.proof, parts.trailing):
        if piece.strip():
            out.append("\n" + contract.body_terms(piece).strip() + "\n")
    return "".join(out)


def section_imports(contract: Contract, section: Section) -> str:
    """List the claims of other contracts a section's claims use, once each."""
    foreign = [target for cid in section.claims
               for target in contract.claim(cid).resolved_uses
               if not contract.local(target)]
    if not foreign:
        return ""
    return ("\\sectionimports{" + ", ".join(contract.ref(t) for t in
                                              contract.sorted_ids(foreign)) + "}\n")


def section_tex(contract: Contract, section: Section) -> str:
    """Render one section: heading, introduction, imports, claims."""
    out = [f"\n\\section{{{tex_text(section.title)}}}\\label{{{section.anchor}}}\n"]
    if section.abstract.strip():
        intro = contract.plain_linked(section.abstract, section.module_id)
        out.append("\\sectionintro{" + intro + "}\n")
    out.append(section_imports(contract, section))
    out += [claim_tex(contract, cid) for cid in section.claims]
    return "".join(out)


def body_tex(contract: Contract) -> str:
    """Render every part of the contract, in order."""
    out: list[str] = []
    for part in contract.structure.parts:
        out.append(f"\n\\clearpage\n\\part{{{tex_text(part.title)}}}\n")
        if part.intro.strip():
            out.append("\\sectionintro{" + contract.plain(part.intro, part.module_id)
                       + "}\n")
        out += [section_tex(contract, section) for section in part.sections]
    return "".join(out)
