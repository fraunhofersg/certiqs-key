#!/usr/bin/env python3
r"""Motivation: a symbol that compiles and was never catalogued.

`spec/macros.tex` is the executable form of `spec/notation.md`, and the
assembler's `latexmk` run is the only machine that reads a claim body today.
A compile answers one question -- does every control sequence have a
definition -- and it answers it against the *union* of the macro file, so it is
silent about the two ways a symbol goes wrong here:

* a claim writes a symbol the notation reference never defines. The
  error class is a bare `Q` written where the declared measured system is
  `\Qsys`. A bare `Q`
  compiles, renders identically today, and stops being the declared system the
  moment the catalogue's `\Qsys` row moves. The mirror case is a genuinely new
  macro used before it is added to `spec/macros.tex`: that one the compile does
  catch, but only once someone runs it, and only as a TeX error rather than as
  a located finding;
* a macro exists but its *meaning* was never recorded, or drifted from what was
  recorded. `spec/notation.md` §1 fixes part A of `spec/macros.tex` as a
  verbatim copy of the catalogue and makes any change to a part-A name,
  expansion or Meaning a notation change with a version bump. Nothing enforced
  that: the two files can disagree and every contract still compiles, because
  TeX reads only one of them.

So this tool reports, per claim file, a macro used and defined nowhere, and,
per part-A macro, an expansion the catalogue does not record. It checks form
only and **it never refuses anything** (`PRINCIPLES.md` §5): whether a symbol is
the *right* one for the mathematics is the verifier's and the human's.
`PRINCIPLES.md` §3 names "symbols are declared" among the machine checks of
form.

WHAT IT DOES NOT DECIDE, on purpose. It decides the macro layer only. A symbol
written as raw LaTeX -- `$\mathcal{H}(A)$` instead of `\Hs{A}`, or the bare `Q`
above -- carries no control sequence and is invisible to check (a);
only a reader catches that. It does not compare a macro's *Meaning* column
against the mathematics, and it does not decide whether a `\ref`, a citation or
an edge is right -- those are `check_claims`' and the verifier's.

(a) UNDEFINED MACROS. Every control sequence in a claim body (the text after
the `% ---` header; LaTeX comments blanked by `check_claims.strip_comments`, so
a macro named only in a comment is not a use) that is not

  * defined in `spec/macros.tex` (part A or part B), nor
  * defined in the claim file itself (`\newcommand`, `\renewcommand`,
    `\providecommand`, `\DeclareMathOperator`, `\def`, `\let`, `\newlength`),
    which no claim file does today but which the check must not punish, nor
  * in `ALLOWED` below.

`ALLOWED` is the LaTeX2e kernel plus exactly the packages the contract
preamble (`harness/contract_render.py`) loads for claim bodies -- amsmath,
amssymb, amsfonts, amsthm, mathtools, dsfont, braket, physics, xcolor, array,
enumitem, hyperref, bookmark, graphicx, longtable, xurl, needspace -- the
commands its ten theorem environments bring, and the five commands the
preamble defines for claim bodies (`\xref`, `\term`, `\tref`, `\iface`, `\repodoc`;
`_CLAIM_BODY` below). The packages the preamble loads for its own front and
back matter, meta lines and main-result frames (booktabs, xltabular,
imakeidx, tcolorbox, refcount) are left
out on purpose, as are the assembler's own macros (`\claimmeta`, `\mref` and
the like): none of them belongs in a claim file. cleveref is not loaded, so
`\cref` and its family are not in the list and `check_claims` refuses them.
It is written out by hand rather
than derived, because deriving it would mean parsing the packages: the list is
the tool's declared boundary and a reader can audit it. **A genuine standard
command missing from it shows up as an undefined-macro finding, and the fix is
to add it here, never to change a claim.**

(b) EXPANSION AGAINST THE CATALOGUE. For every macro defined in part A of
`spec/macros.tex` (the region between the `PART A` and `PART B` banner
comments), the expansion `spec/notation.md` records for it must be the same
LaTeX. Exactly which columns are read, and how a row is matched to a macro:

  * The symbol tables of §3. A table is read when its header row's first two
    cells are `Macro` and `Rendered`; **only those two columns are read** --
    Meaning and Notes are prose for the human and this tool does not parse
    them. In a data row, the Macro cell's backtick spans that begin with a
    backslash are the macros, in order, each parsed as a name plus its
    brace-delimited representative arguments (`` `\Hs{A}` `` is the macro `Hs`
    with the one argument `A`); the Rendered cell's `$...$` spans are the
    renderings, in order. A row is matched to a macro **positionally**: the
    k-th macro of the Macro cell against the k-th `$...$` span of the Rendered
    cell. A row whose two counts differ records nothing and is counted as
    unmatched in the summary (`\simpl`, whose rendering is the prose
    *(empty)*, is the standing case). Cells are split on unescaped `|`, and
    `\|` inside a cell is the Markdown escape for a literal `|` that §1
    documents.
  * §3.9 (Reserved, Superseded), whose entries are prose and a two-column
    Old/Superseded-by table rather than a symbol table, is read by one inline
    rule instead: a backtick span `` `\name` `` immediately followed by
    `($...$)` records that rendering for that macro. The rule is applied to
    §3.9 alone, so that a §3 Notes column mentioning a macro cannot be read as
    a second record of it, and it is applied to the section as one block rather
    than line by line, because its Reserved paragraph wraps between a macro and
    its rendering (`\kout` and `$k_{\mathrm{out}}$` sit on two lines).

Comparison. Both sides -- the macro's body with the catalogue's representative
arguments substituted for `#1`, `#2`, ..., and the catalogue's rendering -- are
expanded to a fixed point against the whole of `spec/macros.tex` (so
`\blk{M}{\leqN}` reaches `M^{(\leq N)}`), then tokenised into control words and single
characters, and whitespace is dropped. **A difference only in grouping braces
is not reported**: `\Wflag` expands through `\Flag`'s own braces to
`W_{{\mathrm{Flg}}}` while the catalogue writes `W_{\mathrm{Flg}}`, and the two
are the same expansion. An arity disagreement -- the catalogue writing an
argument count the definition does not take -- is reported, because it means
the row and the definition are not describing the same macro. A part-A macro
the catalogue records nowhere is a note, not a finding: it says the catalogue
is incomplete, which is a notation change for a human, not a defect in a claim.

(c) `--unused`, informational and never an error: macros `spec/macros.tex`
defines that no claim file uses. A part-A macro is catalogued notation and may
legitimately sit unused; a part-B macro that no claim uses is a candidate for
deletion at the next notation pass. It is a listing, not a finding, so it does
not touch the exit code.

(d) PLAIN MEANING CELLS. The contract's notation table renders the Meaning
cell of every symbol-table row (`contract_frontmatter.meaning_tex`), so the
cell is checked as the plain text it becomes there: no Markdown strong
emphasis (`**` or `__`, which would print as bold: "**The** test-statistics
map"), no section pointer (a "§3.11 b" names a
section of `spec/notation.md`, which the PDF does not hold), and no label in
a code span that is not a claim name the table links (`MEANING_CLAIM_RE`:
`eq:feas` and a bare `foundations/req:declared-tolerance` printed as
typewriter text). Mathematics and code spans are exempt from the first two
rules.
The Notes column is not
rendered and is not read.

Exit 1 when (a), (b) or (d) is non-empty, 0 otherwise. Findings print as
`path:line: message`, as `check_claims` does.

Usage:
    python -m harness.check_symbols [--repo .] [--module <id>] [--unused]
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from harness.check_claims import (
    ClaimFormatError,
    Error,
    Repo,
    discover_modules,
    in_scope,
    rel_path,
    split_header,
    strip_comments,
)

# --- The standard-command allow-list -----------------------------------------
#
# See the module docstring: the LaTeX2e kernel plus the packages the assembler's
# preamble loads. Add a genuine standard command here; never change a claim to
# satisfy this list.

_KERNEL = """
newcommand renewcommand providecommand DeclareMathOperator def let
newenvironment renewenvironment newtheorem theoremstyle newlength setlength
addtolength setcounter addtocounter newcounter stepcounter refstepcounter
value the arabic roman Roman alph Alph fnsymbol numberwithin begin end
label ref pageref eqref autoref nameref cite nocite item setlist
footnote footnotemark footnotetext marginpar caption centering raggedright
raggedleft newpage clearpage pagebreak linebreak nolinebreak newline noindent
indent par relax protect ensuremath expandafter csname endcsname makeatletter
makeatother verb char today allowbreak allowdisplaybreaks sloppy fussy
hspace vspace hfill vfill hphantom vphantom phantom smash rlap llap makebox
mbox framebox fbox parbox raisebox rule quad qquad enspace thinspace
negthinspace medskip smallskip bigskip noalign dotfill hrulefill
multicolumn multirow cline hline arraystretch tabcolsep arraybackslash
textwidth textheight linewidth columnwidth paperwidth parindent parskip
baselineskip
"""

_TEXT = """
emph textbf textit texttt textrm textsf textsc textsl textup textmd
textnormal textbackslash textasciitilde textunderscore bfseries itshape
ttfamily rmfamily sffamily scshape slshape upshape mdseries normalfont em it
bf sc sl tt rm sf tiny scriptsize footnotesize small normalsize large Large
LARGE huge Huge underline sout newblock
"""

# amsmath, amsthm, mathtools, array/longtable/enumitem/needspace, hyperref,
# graphicx, xcolor -- the packages the assembler loads (cleveref is not one).
_PACKAGES = """
text intertext shortintertext tag notag nonumber substack sideset
operatorname operatornamewithlimits qed qedhere proofname
mathtoolsset prescript coloneqq eqqcolon vcentcolon adjustlimits
Needspace needspace endhead endfoot endfirsthead endlastfoot
href url hypersetup phantomsection texorpdfstring hyperref
includegraphics graphicspath rotatebox scalebox resizebox
definecolor color textcolor colorbox fcolorbox pagecolor
toprule midrule bottomrule
"""

_MATH = """
frac dfrac tfrac cfrac binom dbinom tbinom sqrt overline widehat widetilde
hat tilde bar vec dot ddot check breve acute grave mathring overbrace
underbrace overset underset stackrel overrightarrow overleftarrow
overleftrightarrow xrightarrow xleftarrow mathrm mathbf mathit mathsf mathtt
mathcal mathbb mathfrak mathds mathnormal boldsymbol pmb textstyle
displaystyle scriptstyle scriptscriptstyle limits nolimits left right middle
big Big bigg Bigg bigl bigr Bigl Bigr biggl biggr Biggl Biggr langle rangle
lvert rvert lVert rVert lceil rceil lfloor rfloor lbrace rbrace lbrack
rbrack vert Vert mid nmid parallel colon mathrel mathbin mathop
mathord mathpunct mathopen mathclose mspace mkern negmedspace negthickspace
"""

_SYMBOLS = """
alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa
varkappa lambda mu nu xi pi varpi rho varrho sigma varsigma tau upsilon phi
varphi chi psi omega digamma Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi
Psi Omega aleph beth hbar imath jmath ell wp Re Im partial infty emptyset
varnothing nabla surd top bot angle triangle forall exists nexists neg lnot
flat natural sharp clubsuit diamondsuit heartsuit spadesuit prime backslash
cdot cdots ldots vdots ddots dots dotsc dotsb dotsm dotsi dotso star ast circ
bullet div times cap cup uplus sqcap sqcup vee wedge land lor setminus wr
diamond bigtriangleup bigtriangledown triangleleft triangleright oplus ominus
otimes oslash odot bigcirc dagger ddagger amalg leq le geq ge equiv models
prec succ sim perp preceq succeq simeq ll gg asymp subset supset approx
bowtie subseteq supseteq cong Join sqsubset sqsupset neq ne sqsubseteq
sqsupseteq doteq frown in ni propto notin vdash dashv smile leqslant geqslant
nleq ngeq nless ngtr nsubseteq nsupseteq subsetneq supsetneq varsubsetneq
lesssim gtrsim leftarrow rightarrow to gets uparrow downarrow updownarrow
Leftarrow Rightarrow Uparrow Downarrow Updownarrow leftrightarrow
Leftrightarrow longleftarrow longrightarrow longleftrightarrow Longleftarrow
Longrightarrow Longleftrightarrow mapsto longmapsto hookleftarrow
hookrightarrow leftharpoonup rightharpoonup leftharpoondown rightharpoondown
rightleftharpoons leadsto nearrow searrow swarrow nwarrow iff implies
impliedby nrightarrow twoheadrightarrow sum prod coprod int oint iint iiint
bigcap bigcup bigsqcup bigvee bigwedge bigodot bigotimes bigoplus biguplus
lim limsup liminf max min sup inf arg deg det dim exp gcd hom ker lg ln log
Pr sin cos tan cot sec csc sinh cosh tanh coth arcsin arccos arctan injlim
projlim varinjlim varprojlim varlimsup varliminf boxed blacksquare square
Diamond checkmark dag S P copyright pounds pm mp not nparallel nsim ncong
nvdash succnsim precnsim lneq gneq lessgtr gtrless thickapprox thicksim
backsim eqsim between pitchfork therefore because circledast circleddash
boxplus boxminus boxtimes boxdot ltimes rtimes leftthreetimes rightthreetimes
curlyvee curlywedge veebar barwedge doublebarwedge intercal divideontimes
centerdot dotplus smallsetminus upharpoonright upharpoonleft downharpoonright
downharpoonleft multimap rightsquigarrow leftrightsquigarrow looparrowleft
looparrowright circlearrowleft circlearrowright rightleftarrows leftrightarrows
upuparrows downdownarrows Lleftarrow Rrightarrow twoheadleftarrow
rightarrowtail leftarrowtail nleftarrow nLeftarrow nRightarrow
nleftrightarrow nLeftrightarrow complement mho Bbbk Finv Game eth hslash
backepsilon subsetneqq supsetneqq varsubsetneqq varsupsetneqq nsubseteqq
nsupseteqq trianglelefteq trianglerighteq ntriangleleft ntriangleright unlhd
unrhd vartriangle vartriangleleft vartriangleright blacktriangle
blacktriangledown blacktriangleleft blacktriangleright triangledown triangleq
bigstar lozenge blacklozenge measuredangle sphericalangle
"""

# braket + physics (physics wins for the shared names; see spec/notation.md §1)
_QUANTUM = """
ket bra braket ketbra dyad expval ev tr Tr trace pdv dv grad div curl
laplacian abs norm order comm acomm poissonbracket qty pqty bqty vqty
absolutevalue evaluated eval dmat mqty smatrixquantity matrixquantity
Set set rank anticommutator commutator Bra Ket Braket flatfrac
"""

# The claim-body commands the assembler's preamble defines (spec/claim-format.md
# section 4): \xref{<full id>} a claim of another contract, \term[gloss]{...} a
# phrase a definition defines, \tref[phrase]{...} a use of a defined term, linked
# to its definition, \iface{...} an interface key or refusal string a requirement
# binds, \repodoc{path#anchor} a repository file. `requirement` is the claim
# environment of the `req` kind; amsthm's \newtheorem defines \requirement and
# \endrequirement for it, as it does for the other nine kinds. Where each command
# may stand is check_claims' and check_presentation's question, not this list's.
# The assembler's own macros (\DeclareXref, \claimid and the like) never belong
# in a claim file and are deliberately absent.
_CLAIM_BODY = """
xref term tref iface repodoc requirement
"""

ALLOWED: frozenset[str] = frozenset(
    name
    for block in (_KERNEL, _TEXT, _PACKAGES, _MATH, _SYMBOLS, _QUANTUM, _CLAIM_BODY)
    for name in block.split()
)

#: Every control sequence. The symbol form is matched and discarded so that a
#: row break followed by a letter is not read as a macro.
TOKEN_RE = re.compile(r"\\(?:([A-Za-z@]+)|.)")

#: The six ways a claim file or the macro file may define a macro.
DEFINITION_RE = re.compile(
    r"\\(?:re|provide)?newcommand\*?\s*\{?\s*\\([A-Za-z@]+)\s*\}?"
    r"(?:\s*\[\s*(\d+)\s*\])?"
    r"|\\DeclareMathOperator\*?\s*\{\s*\\([A-Za-z@]+)\s*\}"
    r"|\\def\s*\\([A-Za-z@]+)"
    r"|\\let\s*\\([A-Za-z@]+)"
    r"|\\newlength\s*\{?\s*\\([A-Za-z@]+)\s*\}?"
)

PART_BANNER_RE = re.compile(r"^%\s*PART\s+([AB])\b")
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
BACKTICK_RE = re.compile(r"`([^`]*)`")
MATH_RE = re.compile(r"\$([^$]+)\$")
INLINE_RECORD_RE = re.compile(r"(`\\[A-Za-z@]+(?:\{[^{}]*\})*`)\s*\(\$([^$]+)\$\)")
SECTION_39_RE = re.compile(r"^###\s+3\.9\b")
SECTION_END_RE = re.compile(r"^(?:##\s|###\s)")
LATEX_TOKEN_RE = re.compile(r"\\[A-Za-z@]+|\\.|\S")
#: A claim a Meaning cell names: a module id (possibly in a code span), an
#: optional kind abbreviation, then the claim label in a code span --
#: "meat-core Def. `def:declaration`", "`reductions` `def:joint-family`". The
#: contract's notation table renders such a name as a link.
MEANING_CLAIM_RE = re.compile(
    r"`?(?P<module>[a-z][a-z0-9-]*(?:/[a-z0-9-]+)?)`?\s+"
    r"(?:(?:Def|Thm|Lem|Rem|Prop|Cor|Req|Ex|Ass)\.\s+)?"
    r"`(?P<label>[a-z]+:[A-Za-z0-9-]+)`"
)
#: A code span of a Meaning cell that reads as a label: ``kind:slug``, with an
#: optional module path, or an equation label.
MEANING_LABEL_SPAN_RE = re.compile(
    r"`((?:[a-z0-9-]+/){0,2}(?:thm|lem|prop|cor|def|ass|rem|ex|fact|req|eq)"
    r":[A-Za-z0-9-]+)`")
#: Markdown strong emphasis, which the contract's notation table set as bold.
MEANING_STRONG_RE = re.compile(r"\*\*|__")


@dataclass(frozen=True)
class Macro:
    """One macro definition of ``spec/macros.tex``."""

    name: str
    nargs: int
    body: str
    part: str          # "A", "B" or "" (before either banner)
    line: int


@dataclass(frozen=True)
class Record:
    """One rendering the catalogue records for a macro, with its row."""

    name: str
    args: tuple[str, ...]
    rendering: str
    line: int


@dataclass
class Findings:
    """What one run found, split by what it means for the exit code."""

    errors: list[Error] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ClaimBody:
    """One claim file's body, with what it needs to be scanned."""

    rel: str
    module_id: str
    text: str
    first_line: int


# --- Small LaTeX helpers ------------------------------------------------------


def read_group(text: str, index: int) -> tuple[str, int] | None:
    """Read a brace group at or after ``index``; None if there is none there."""
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text) or text[index] != "{":
        return None
    depth = 0
    for position in range(index, len(text)):
        if text[position] == "{":
            depth += 1
        elif text[position] == "}":
            depth -= 1
            if depth == 0:
                return text[index + 1 : position], position + 1
    return None


def substitute(body: str, args: tuple[str, ...]) -> str:
    """Replace ``#1``..``#9`` in a macro body with the given arguments."""
    def one(match: re.Match[str]) -> str:
        position = int(match.group(1)) - 1
        return args[position] if 0 <= position < len(args) else match.group(0)

    return re.sub(r"#(\d)", one, body)


def expand(text: str, macros: dict[str, Macro], rounds: int = 12) -> str:
    """Expand every known macro in ``text`` to a fixed point (bounded)."""
    for _round in range(rounds):
        out: list[str] = []
        index = 0
        changed = False
        while index < len(text):
            match = TOKEN_RE.match(text, index)
            if match is None or match.group(1) is None:
                out.append(text[index])
                index += 1
                continue
            macro = macros.get(match.group(1))
            if macro is None:
                out.append(match.group(0))
                index = match.end()
                continue
            cursor = match.end()
            args: list[str] = []
            for _argument in range(macro.nargs):
                group = read_group(text, cursor)
                if group is None:
                    break
                args.append(group[0])
                cursor = group[1]
            if len(args) != macro.nargs:
                out.append(match.group(0))
                index = match.end()
                continue
            out.append(substitute(macro.body, tuple(args)))
            index = cursor
            changed = True
        text = "".join(out)
        if not changed:
            break
    return text


def tokens(text: str) -> list[str]:
    """Tokenise LaTeX into control words and single non-space characters."""
    return LATEX_TOKEN_RE.findall(text)


def same_expansion(left: str, right: str) -> bool:
    """Whether two expansions agree, ignoring whitespace and grouping braces."""
    if tokens(left) == tokens(right):
        return True
    bare_left = [token for token in tokens(left) if token not in ("{", "}")]
    bare_right = [token for token in tokens(right) if token not in ("{", "}")]
    return bare_left == bare_right


def definition_name(match: re.Match[str]) -> str | None:
    """Return the macro name a ``DEFINITION_RE`` match defines."""
    return next((group for group in (match.group(1), match.group(3),
                                     match.group(4), match.group(5),
                                     match.group(6)) if group), None)


# --- Reading the two spec files ----------------------------------------------


def read_macros(path: Path) -> dict[str, Macro]:
    r"""Read ``spec/macros.tex``: name -> definition, tagged part A or part B.

    The part is decided by the ``% PART A``/``% PART B`` banner comments the
    file carries; a macro defined before either banner is tagged "".
    """
    macros: dict[str, Macro] = {}
    part = ""
    text = path.read_text(encoding="utf-8")
    for number, raw in enumerate(text.split("\n"), start=1):
        banner = PART_BANNER_RE.match(raw)
        if banner:
            part = banner.group(1)
            continue
        line = strip_comments(raw)
        match = DEFINITION_RE.search(line)
        if match is None:
            continue
        name = definition_name(match)
        if name is None:
            continue
        nargs = int(match.group(2)) if match.group(2) else 0
        group = read_group(line, match.end())
        macros[name] = Macro(name, nargs, group[0] if group else "", part, number)
    return macros


def parse_macro_cell(cell: str) -> list[tuple[str, tuple[str, ...]]]:
    r"""Return a Macro cell's backtick-quoted macros, with their arguments."""
    found: list[tuple[str, tuple[str, ...]]] = []
    for span in BACKTICK_RE.findall(cell):
        span = span.strip()
        head = re.match(r"\\([A-Za-z@]+)", span)
        if head is None:
            continue
        args: list[str] = []
        cursor = head.end()
        while True:
            group = read_group(span, cursor)
            if group is None:
                break
            args.append(group[0])
            cursor = group[1]
        found.append((head.group(1), tuple(args)))
    return found


@dataclass(frozen=True)
class CatalogueRow:
    r"""One data row of a §3 symbol table that names at least one macro.

    ``meaning`` is the Meaning cell as written (Markdown with ``$...$``
    mathematics), read for the notation table of a contract PDF; this tool's
    own checks never read it.
    """

    macros: tuple[tuple[str, tuple[str, ...]], ...]
    renderings: tuple[str, ...]
    meaning: str
    line: int


def symbol_table_rows(text: str) -> Iterator[tuple[int, list[str]]]:
    r"""Yield (line, cells) for every data row of a Macro/Rendered symbol table.

    Cells are split on unescaped ``|`` and the Markdown escape ``\\|`` is read
    as a literal ``|``, as the module docstring says.
    """
    in_table = False
    for number, raw in enumerate(text.split("\n"), start=1):
        stripped = raw.strip()
        if not stripped.startswith("|"):
            in_table = False
            continue
        cells = [cell.replace(r"\|", "|").strip()
                 for cell in CELL_SPLIT_RE.split(stripped)[1:-1]]
        if len(cells) < 2:
            continue
        if cells[0].lower() == "macro" and cells[1].lower() == "rendered":
            in_table = True
            continue
        if not in_table or set(cells[0]) <= set("- :"):
            continue
        yield number, cells


def catalogue_rows(path: Path) -> list[CatalogueRow]:
    """Return the §3 symbol-table rows that name a macro, in file order."""
    rows: list[CatalogueRow] = []
    for number, cells in symbol_table_rows(path.read_text(encoding="utf-8")):
        used = parse_macro_cell(cells[0])
        if not used:
            continue
        rows.append(CatalogueRow(tuple(used), tuple(MATH_RE.findall(cells[1])),
                                 cells[2] if len(cells) > 2 else "", number))
    return rows


def read_catalogue(path: Path) -> tuple[dict[str, list[Record]], int]:
    r"""Read ``spec/notation.md``'s catalogue: macro -> recorded renderings.

    Two rules, both stated in the module docstring: the positional
    Macro/Rendered pairing of §3's symbol tables, and the inline
    `` `\name` ($rendering$) `` form of §3.9. Returns the records and the number
    of symbol-table rows whose two counts did not match.
    """
    records: dict[str, list[Record]] = {}
    unmatched = 0
    source = path.read_text(encoding="utf-8")
    for number, cells in symbol_table_rows(source):
        used = parse_macro_cell(cells[0])
        rendered = MATH_RE.findall(cells[1])
        if not used:
            continue
        if len(used) != len(rendered):
            unmatched += 1
            continue
        for (name, args), rendering in zip(used, rendered, strict=True):
            records.setdefault(name, []).append(
                Record(name, args, rendering, number))
    in_39 = False
    section_39: list[tuple[int, str]] = []
    for number, raw in enumerate(source.split("\n"), start=1):
        if SECTION_39_RE.match(raw):
            in_39 = True
        elif in_39 and SECTION_END_RE.match(raw):
            in_39 = False
        if in_39:
            section_39.append((number, raw.replace(r"\|", "|")))
    # §3.9 is read as one block, not line by line: its Reserved paragraph wraps
    # between a macro and its rendering (`\kout` and $k_{\mathrm{out}}$ sit on
    # two lines), and a line-by-line rule loses exactly those entries.
    first = section_39[0][0] if section_39 else 1
    block = "\n".join(text for _number, text in section_39)
    for inline in INLINE_RECORD_RE.finditer(block):
        line = first + block.count("\n", 0, inline.start())
        for name, args in parse_macro_cell(inline.group(1)):
            records.setdefault(name, []).append(
                Record(name, args, inline.group(2), line))
    return records, unmatched


# --- Reading the claim files --------------------------------------------------


def claim_bodies(repo: Repo) -> list[ClaimBody]:
    """Return every claim file's body, comments blanked, in path order.

    A file whose ``% ---`` header does not parse is scanned whole rather than
    skipped: the malformed header is ``check_claims``' finding to report, and
    this check still has something to say about the body.
    """
    bodies: list[ClaimBody] = []
    for module_id in sorted(repo.modules):
        claims_dir = repo.modules[module_id].path / "claims"
        if not claims_dir.is_dir():
            continue
        for path in sorted(claims_dir.glob("*.tex")):
            text = path.read_text(encoding="utf-8")
            try:
                _header, body, body_start = split_header(text)
            except ClaimFormatError:
                body, body_start = text, 1
            bodies.append(ClaimBody(rel_path(repo.root, path), module_id,
                                    strip_comments(body), body_start))
    return bodies


def local_definitions(text: str) -> set[str]:
    """Return the macros a claim file defines for itself."""
    names: set[str] = set()
    for match in DEFINITION_RE.finditer(text):
        name = definition_name(match)
        if name:
            names.add(name)
    return names


def used_macros(body: ClaimBody) -> dict[str, tuple[int, int]]:
    """Return every control word used, mapped to its first line and its count."""
    seen: dict[str, tuple[int, int]] = {}
    for match in TOKEN_RE.finditer(body.text):
        name = match.group(1)
        if name is None:
            continue
        line = body.first_line + body.text.count("\n", 0, match.start())
        first, count = seen.get(name, (line, 0))
        seen[name] = (first, count + 1)
    return seen


# --- The two checks -----------------------------------------------------------


def check_undefined(bodies: list[ClaimBody], macros: dict[str, Macro],
                    found: Findings) -> None:
    """Check (a): every macro a claim body uses is defined somewhere."""
    for body in bodies:
        local = local_definitions(body.text)
        for name, (line, count) in sorted(used_macros(body).items()):
            if name in macros or name in local or name in ALLOWED:
                continue
            times = "occurrence" if count == 1 else "occurrences"
            found.errors.append(Error(
                body.rel, line,
                rf"symbols: undefined macro \{name} ({count} {times}): not in "
                "spec/macros.tex, not defined in this file, and not in this "
                "tool's standard-command allow-list", body.module_id))


def check_catalogue(macros: dict[str, Macro], records: dict[str, list[Record]],
                    notation_rel: str, macros_rel: str, found: Findings) -> None:
    """Check (b): a part-A expansion is the one the catalogue records."""
    uncatalogued: list[str] = []
    part_a = sorted((m for m in macros.values() if m.part == "A"),
                    key=lambda macro: macro.line)
    for macro in part_a:
        entries = records.get(macro.name)
        if not entries:
            uncatalogued.append(macro.name)
            continue
        comparable = [e for e in entries if len(e.args) == macro.nargs]
        if not comparable:
            entry = entries[0]
            found.errors.append(Error(
                macros_rel, macro.line,
                rf"catalogue: \{macro.name} takes {macro.nargs} argument(s) "
                f"here, but {notation_rel}:{entry.line} records it with "
                f"{len(entry.args)}"))
            continue
        if any(same_expansion(expand(substitute(macro.body, entry.args), macros),
                              expand(entry.rendering, macros))
               for entry in comparable):
            continue
        entry = comparable[0]
        expansion = expand(substitute(macro.body, entry.args), macros).strip()
        found.errors.append(Error(
            macros_rel, macro.line,
            rf"catalogue: \{macro.name} expands to '{expansion}', but "
            f"{notation_rel}:{entry.line} records '{entry.rendering.strip()}'"))
    if uncatalogued:
        found.notes.append(
            f"{len(uncatalogued)} part-A macro(s) with no catalogue row: "
            + ", ".join("\\" + name for name in sorted(uncatalogued)))


def claim_file_exists(repo: Repo, module_id: str, label: str) -> bool:
    """Whether ``module_id`` (a module or submodule) has a claim file for ``label``."""
    module = repo.modules.get(module_id)
    if module is None or ":" not in label:
        return False
    return (module.path / "claims" / (label.replace(":", "-", 1) + ".tex")).is_file()


def check_meanings(text: str, notation_rel: str, repo: Repo, found: Findings) -> None:
    r"""Check (d): a Meaning cell is plain, and every label it names resolves.

    The contract's notation table renders the Meaning cell of each symbol-table
    row (``contract_frontmatter.meaning_tex``): Markdown strong emphasis became
    bold ("**The** test-statistics map" of ``\Phimap``, set in meat-core's
    contract), a section pointer ("§3.11 b") named a section of a document the
    PDF does not hold, and a label in a code span that is not a claim name of
    ``MEANING_CLAIM_RE`` (``eq:feas``, ``foundations/req:declared-tolerance``)
    printed as typewriter text instead of a link.
    """
    for number, cells in symbol_table_rows(text):
        if len(cells) < 3:
            continue
        meaning = cells[2]
        plain = re.sub(r"`[^`]*`", "", MATH_RE.sub("", meaning))
        if MEANING_STRONG_RE.search(plain):
            found.errors.append(Error(
                notation_rel, number,
                "notation: the Meaning cell carries strong emphasis (** or __), "
                "which the contract's notation table prints as bold; write the "
                "words plainly"))
        if "\N{SECTION SIGN}" in plain:
            found.errors.append(Error(
                notation_rel, number,
                "notation: the Meaning cell carries a section pointer (a section "
                "sign), which names a section the contract does not hold; say it "
                "in words or drop it"))
        names = [(match.span(), f"{match['module']}/{match['label']}")
                 for match in MEANING_CLAIM_RE.finditer(meaning)]
        for span in MEANING_LABEL_SPAN_RE.finditer(meaning):
            covering = [cid for (start, end), cid in names
                        if start <= span.start() and span.end() <= end]
            if any(claim_file_exists(repo, *cid.rsplit("/", 1)) for cid in covering):
                continue
            found.errors.append(Error(
                notation_rel, number,
                f"notation: the Meaning cell names `{span.group(1)}`, which is no "
                "claim name the notation table can link; write it as "
                "'<module> <Kind>. `<label>`' naming an existing claim, or in words"))


def report_unused(bodies: list[ClaimBody], macros: dict[str, Macro]) -> None:
    """Print the macros no claim file uses, part by part (informational)."""
    used: set[str] = set()
    for body in bodies:
        used |= set(used_macros(body))
    for part, title in (("A", "part A (catalogued notation)"),
                        ("B", "part B (module-local)")):
        names = sorted(macro.name for macro in macros.values()
                       if macro.part == part and macro.name not in used)
        print(f"unused in {title}: {len(names)}")
        for name in names:
            print(f"  \\{name}  (spec/macros.tex:{macros[name].line})")


# --- Command line -------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="python -m harness.check_symbols",
        description="Check that every symbol a claim uses is defined, and that "
                    "spec/macros.tex part A matches spec/notation.md's "
                    "catalogue.")
    parser.add_argument("--repo", default=".", help="repository root (default: .)")
    parser.add_argument("--module", default=None,
                        help="report only findings of this module id")
    parser.add_argument("--unused", action="store_true",
                        help="also list macros no claim file uses "
                             "(informational, never an error)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run both checks over a repository and return the exit code."""
    args = build_parser().parse_args(argv)
    root = Path(args.repo)
    if not root.is_dir():
        print(f"error: --repo {args.repo} is not a directory", file=sys.stderr)
        return 1
    macros_path = root / "spec" / "macros.tex"
    notation_path = root / "spec" / "notation.md"
    for path in (macros_path, notation_path):
        if not path.is_file():
            print(f"error: {rel_path(root, path)} not found", file=sys.stderr)
            return 1
    repo = Repo(root=root)
    discover_modules(repo)
    repo.errors.clear()     # a module.yaml finding is check_claims' to report
    if args.module is not None and args.module not in repo.modules:
        print(f"error: --module '{args.module}' is not a module", file=sys.stderr)
        return 1

    macros = read_macros(macros_path)
    records, unmatched = read_catalogue(notation_path)
    every_body = claim_bodies(repo)
    bodies = [b for b in every_body if in_scope(b.module_id, args.module)]

    found = Findings()
    check_undefined(bodies, macros, found)
    check_catalogue(macros, records, rel_path(root, notation_path),
                    rel_path(root, macros_path), found)
    check_meanings(notation_path.read_text(encoding="utf-8"),
                   rel_path(root, notation_path), repo, found)

    for error in sorted(found.errors):
        print(error.render())
    scope = args.module or "spec/modules"
    part_a = sum(1 for macro in macros.values() if macro.part == "A")
    print(f"{len(bodies)} claim file(s) under {scope}; {len(macros)} macro(s) "
          f"in spec/macros.tex ({part_a} in part A); {len(records)} macro(s) "
          f"recorded by spec/notation.md ({unmatched} catalogue row(s) not "
          "comparable)")
    for note in found.notes:
        print(f"note: {note}")
    if args.unused:
        report_unused(every_body, macros)
    if found.errors:
        print(f"{len(found.errors)} finding(s) in {scope}", file=sys.stderr)
        return 1
    print(f"ok: every macro used under {scope} is defined, part A matches the "
          "catalogue, and the Meaning cells are plain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
