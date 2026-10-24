"""Motivation: navigation links must survive renumbering and escape plain text.

The assembler and graph index share stable PDF destinations. Metadata is
escaped as text so a title's ampersand cannot break the generated claim index.
Group validation lives with the other module checks in check_claims.py.

Plain-text fields (claim summaries, module and reading-group abstracts) are
rendered twice, into the contract's TeX and into the graph index's Markdown,
and read once more by the checker. Four things they share live here so that
the readers cannot disagree: the mapped Unicode set (a character outside
it would stop pdflatex or render differently in the two views), the
``[[label]]`` link syntax, the word each claim kind is printed with, and how
a plain text splits into sentences (the summary's sentence limit and the
role-word rule of check_claims both count them).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

#: The word a claim of each kind is printed with (theorem heading, link text).
KIND_WORD: dict[str, str] = {
    "thm": "Theorem",
    "lem": "Lemma",
    "prop": "Proposition",
    "cor": "Corollary",
    "def": "Definition",
    "ass": "Assumption",
    "rem": "Remark",
    "ex": "Example",
    "fact": "Fact",
    "req": "Requirement",
}

#: The abbreviation a claim of each kind is cited with in a meta line ("Def. 2.1").
KIND_ABBREV: dict[str, str] = {
    "thm": "Thm.",
    "lem": "Lem.",
    "prop": "Prop.",
    "cor": "Cor.",
    "def": "Def.",
    "ass": "Ass.",
    "rem": "Rem.",
    "ex": "Ex.",
    "fact": "Fact",
    "req": "Req.",
}


def _math(tex: str) -> str:
    return r"\ensuremath{" + tex + "}"


#: The non-ASCII characters a plain-text field may carry, each with the TeX
#: that renders it under pdflatex with the assembler's OT1 preamble. The
#: renderer substitutes them (``tex_mapped``); the Markdown view keeps the
#: character itself. A character not listed here is refused by the
#: presentation checks: add it here, with its TeX, rather than work around it.
UNICODE_TEX: dict[str, str] = {
    # Greek, lower case (epsilon and phi in their text-book variants)
    "\N{GREEK SMALL LETTER ALPHA}": _math(r"\alpha"),
    "\N{GREEK SMALL LETTER BETA}": _math(r"\beta"),
    "\N{GREEK SMALL LETTER GAMMA}": _math(r"\gamma"),
    "\N{GREEK SMALL LETTER DELTA}": _math(r"\delta"),
    "\N{GREEK SMALL LETTER EPSILON}": _math(r"\varepsilon"),
    "\N{GREEK LUNATE EPSILON SYMBOL}": _math(r"\epsilon"),
    "\N{GREEK SMALL LETTER ZETA}": _math(r"\zeta"),
    "\N{GREEK SMALL LETTER ETA}": _math(r"\eta"),
    "\N{GREEK SMALL LETTER THETA}": _math(r"\theta"),
    "\N{GREEK THETA SYMBOL}": _math(r"\vartheta"),
    "\N{GREEK SMALL LETTER IOTA}": _math(r"\iota"),
    "\N{GREEK SMALL LETTER KAPPA}": _math(r"\kappa"),
    "\N{GREEK SMALL LETTER LAMDA}": _math(r"\lambda"),
    "\N{GREEK SMALL LETTER MU}": _math(r"\mu"),
    "\N{GREEK SMALL LETTER NU}": _math(r"\nu"),
    "\N{GREEK SMALL LETTER XI}": _math(r"\xi"),
    "\N{GREEK SMALL LETTER PI}": _math(r"\pi"),
    "\N{GREEK SMALL LETTER RHO}": _math(r"\rho"),
    "\N{GREEK RHO SYMBOL}": _math(r"\varrho"),
    "\N{GREEK SMALL LETTER SIGMA}": _math(r"\sigma"),
    "\N{GREEK SMALL LETTER FINAL SIGMA}": _math(r"\varsigma"),
    "\N{GREEK SMALL LETTER TAU}": _math(r"\tau"),
    "\N{GREEK SMALL LETTER UPSILON}": _math(r"\upsilon"),
    "\N{GREEK SMALL LETTER PHI}": _math(r"\varphi"),
    "\N{GREEK PHI SYMBOL}": _math(r"\phi"),
    "\N{GREEK SMALL LETTER CHI}": _math(r"\chi"),
    "\N{GREEK SMALL LETTER PSI}": _math(r"\psi"),
    "\N{GREEK SMALL LETTER OMEGA}": _math(r"\omega"),
    # Greek, upper case (those that differ from Latin letters)
    "\N{GREEK CAPITAL LETTER GAMMA}": _math(r"\Gamma"),
    "\N{GREEK CAPITAL LETTER DELTA}": _math(r"\Delta"),
    "\N{GREEK CAPITAL LETTER THETA}": _math(r"\Theta"),
    "\N{GREEK CAPITAL LETTER LAMDA}": _math(r"\Lambda"),
    "\N{GREEK CAPITAL LETTER XI}": _math(r"\Xi"),
    "\N{GREEK CAPITAL LETTER PI}": _math(r"\Pi"),
    "\N{GREEK CAPITAL LETTER SIGMA}": _math(r"\Sigma"),
    "\N{GREEK CAPITAL LETTER UPSILON}": _math(r"\Upsilon"),
    "\N{GREEK CAPITAL LETTER PHI}": _math(r"\Phi"),
    "\N{GREEK CAPITAL LETTER PSI}": _math(r"\Psi"),
    "\N{GREEK CAPITAL LETTER OMEGA}": _math(r"\Omega"),
    # Latin letters with diacritics (names in citations)
    "\N{LATIN SMALL LETTER A WITH ACUTE}": r"\'a",
    "\N{LATIN SMALL LETTER A WITH GRAVE}": r"\`a",
    "\N{LATIN SMALL LETTER A WITH CIRCUMFLEX}": r"\^a",
    "\N{LATIN SMALL LETTER A WITH DIAERESIS}": r'\"a',
    "\N{LATIN SMALL LETTER A WITH RING ABOVE}": r"\aa{}",
    "\N{LATIN SMALL LETTER E WITH ACUTE}": r"\'e",
    "\N{LATIN SMALL LETTER E WITH GRAVE}": r"\`e",
    "\N{LATIN SMALL LETTER E WITH CIRCUMFLEX}": r"\^e",
    "\N{LATIN SMALL LETTER E WITH DIAERESIS}": r'\"e',
    "\N{LATIN SMALL LETTER I WITH ACUTE}": r"\'{\i}",
    "\N{LATIN SMALL LETTER I WITH DIAERESIS}": r'\"{\i}',
    "\N{LATIN SMALL LETTER O WITH ACUTE}": r"\'o",
    "\N{LATIN SMALL LETTER O WITH GRAVE}": r"\`o",
    "\N{LATIN SMALL LETTER O WITH CIRCUMFLEX}": r"\^o",
    "\N{LATIN SMALL LETTER O WITH DIAERESIS}": r'\"o',
    "\N{LATIN SMALL LETTER O WITH STROKE}": r"\o{}",
    "\N{LATIN SMALL LETTER U WITH ACUTE}": r"\'u",
    "\N{LATIN SMALL LETTER U WITH GRAVE}": r"\`u",
    "\N{LATIN SMALL LETTER U WITH CIRCUMFLEX}": r"\^u",
    "\N{LATIN SMALL LETTER U WITH DIAERESIS}": r'\"u',
    "\N{LATIN SMALL LETTER N WITH TILDE}": r"\~n",
    "\N{LATIN SMALL LETTER C WITH CEDILLA}": r"\c{c}",
    "\N{LATIN SMALL LETTER SHARP S}": r"\ss{}",
    "\N{LATIN CAPITAL LETTER A WITH DIAERESIS}": r'\"A',
    "\N{LATIN CAPITAL LETTER A WITH RING ABOVE}": r"\AA{}",
    "\N{LATIN CAPITAL LETTER E WITH ACUTE}": r"\'E",
    "\N{LATIN CAPITAL LETTER O WITH DIAERESIS}": r'\"O',
    "\N{LATIN CAPITAL LETTER U WITH DIAERESIS}": r'\"U',
    # typography
    "\N{EN DASH}": r"\textendash{}",
    "\N{EM DASH}": r"\textemdash{}",
    "\N{LEFT SINGLE QUOTATION MARK}": "`",
    "\N{RIGHT SINGLE QUOTATION MARK}": "'",
    "\N{LEFT DOUBLE QUOTATION MARK}": "``",
    "\N{RIGHT DOUBLE QUOTATION MARK}": "''",
    "\N{HORIZONTAL ELLIPSIS}": r"\ldots{}",
    "\N{NO-BREAK SPACE}": "~",
    "\N{SECTION SIGN}": r"\S{}",
    # mathematics
    "\N{LESS-THAN OR EQUAL TO}": _math(r"\le"),
    "\N{GREATER-THAN OR EQUAL TO}": _math(r"\ge"),
    "\N{NOT EQUAL TO}": _math(r"\neq"),
    "\N{ALMOST EQUAL TO}": _math(r"\approx"),
    "\N{IDENTICAL TO}": _math(r"\equiv"),
    "\N{TILDE OPERATOR}": _math(r"\sim"),
    "\N{ASYMPTOTICALLY EQUAL TO}": _math(r"\simeq"),
    "\N{APPROXIMATELY EQUAL TO}": _math(r"\cong"),
    "\N{PROPORTIONAL TO}": _math(r"\propto"),
    "\N{MUCH LESS-THAN}": _math(r"\ll"),
    "\N{MUCH GREATER-THAN}": _math(r"\gg"),
    "\N{RIGHTWARDS ARROW}": _math(r"\to"),
    "\N{LEFTWARDS ARROW}": _math(r"\leftarrow"),
    "\N{LEFT RIGHT ARROW}": _math(r"\leftrightarrow"),
    "\N{RIGHTWARDS DOUBLE ARROW}": _math(r"\Rightarrow"),
    "\N{LEFTWARDS DOUBLE ARROW}": _math(r"\Leftarrow"),
    "\N{LEFT RIGHT DOUBLE ARROW}": _math(r"\Leftrightarrow"),
    "\N{RIGHTWARDS ARROW FROM BAR}": _math(r"\mapsto"),
    "\N{ELEMENT OF}": _math(r"\in"),
    "\N{NOT AN ELEMENT OF}": _math(r"\notin"),
    "\N{SUBSET OF OR EQUAL TO}": _math(r"\subseteq"),
    "\N{SUBSET OF}": _math(r"\subset"),
    "\N{SUPERSET OF OR EQUAL TO}": _math(r"\supseteq"),
    "\N{SUPERSET OF}": _math(r"\supset"),
    "\N{INTERSECTION}": _math(r"\cap"),
    "\N{UNION}": _math(r"\cup"),
    "\N{SET MINUS}": _math(r"\setminus"),
    "\N{EMPTY SET}": _math(r"\emptyset"),
    "\N{FOR ALL}": _math(r"\forall"),
    "\N{THERE EXISTS}": _math(r"\exists"),
    "\N{DOUBLE-STRUCK CAPITAL N}": _math(r"\mathbb{N}"),
    "\N{DOUBLE-STRUCK CAPITAL Z}": _math(r"\mathbb{Z}"),
    "\N{DOUBLE-STRUCK CAPITAL Q}": _math(r"\mathbb{Q}"),
    "\N{DOUBLE-STRUCK CAPITAL R}": _math(r"\mathbb{R}"),
    "\N{DOUBLE-STRUCK CAPITAL C}": _math(r"\mathbb{C}"),
    "\N{MIDDLE DOT}": _math(r"\cdot"),
    "\N{MULTIPLICATION SIGN}": _math(r"\times"),
    "\N{MINUS SIGN}": _math("-"),
    "\N{PLUS-MINUS SIGN}": _math(r"\pm"),
    "\N{MINUS-OR-PLUS SIGN}": _math(r"\mp"),
    "\N{SQUARE ROOT}": _math(r"\surd"),
    "\N{N-ARY SUMMATION}": _math(r"\sum"),
    "\N{N-ARY PRODUCT}": _math(r"\prod"),
    "\N{INTEGRAL}": _math(r"\int"),
    "\N{INFINITY}": _math(r"\infty"),
    "\N{PARTIAL DIFFERENTIAL}": _math(r"\partial"),
    "\N{NABLA}": _math(r"\nabla"),
    "\N{CIRCLED TIMES}": _math(r"\otimes"),
    "\N{CIRCLED PLUS}": _math(r"\oplus"),
    "\N{RING OPERATOR}": _math(r"\circ"),
    "\N{LEFT CEILING}": _math(r"\lceil"),
    "\N{RIGHT CEILING}": _math(r"\rceil"),
    "\N{LEFT FLOOR}": _math(r"\lfloor"),
    "\N{RIGHT FLOOR}": _math(r"\rfloor"),
    "\N{MATHEMATICAL LEFT ANGLE BRACKET}": _math(r"\langle"),
    "\N{MATHEMATICAL RIGHT ANGLE BRACKET}": _math(r"\rangle"),
    "\N{DOUBLE VERTICAL LINE}": _math(r"\|"),
    "\N{SCRIPT SMALL L}": _math(r"\ell"),
    "\N{DEGREE SIGN}": _math(r"^{\circ}"),
    "\N{SUPERSCRIPT TWO}": _math("^{2}"),
    "\N{SUPERSCRIPT THREE}": _math("^{3}"),
    "\N{SUPERSCRIPT ONE}": _math("^{1}"),
    "\N{SUBSCRIPT ZERO}": _math("_{0}"),
    "\N{SUBSCRIPT ONE}": _math("_{1}"),
    "\N{SUBSCRIPT TWO}": _math("_{2}"),
    "\N{SUPERSCRIPT LATIN SMALL LETTER N}": _math("^{n}"),
    "\N{LATIN SUBSCRIPT SMALL LETTER K}": _math("_{k}"),
}

#: ``[[label]]``, ``[[module/label]]`` (a full claim id) or ``[[A-XXX]]``.
LINK_RE = re.compile(r"\[\[([^\[\]]*)\]\]")
SHORT_ID_LINK_RE = re.compile(r"^A-[A-Z0-9][A-Z0-9-]*$")


def unmapped_characters(text: str) -> list[str]:
    """Return the non-ASCII characters of ``text`` outside the mapped set."""
    return sorted({char for char in text
                   if ord(char) > 127 and char not in UNICODE_TEX})


OPENING_QUOTES = "\N{LEFT SINGLE QUOTATION MARK}\N{LEFT DOUBLE QUOTATION MARK}"
CLOSING_QUOTES = "\N{RIGHT SINGLE QUOTATION MARK}\N{RIGHT DOUBLE QUOTATION MARK}"
#: Words before a full stop that end no sentence ("Eq. 3", "e.g. a").
ABBREVIATIONS = frozenset({
    "e.g", "i.e", "cf", "etc", "vs", "resp", "approx", "viz", "al", "no", "nos",
    "eq", "eqs", "thm", "thms", "def", "defs", "lem", "prop", "cor", "sec", "secs",
    "fig", "figs", "ref", "refs", "ch", "app", "ex", "rem", "p", "pp", "vol",
    "ass", "st", "dr", "mr", "ms", "prof",
})
SENTENCE_END_RE = re.compile(r"[.!?]+[\"')\]" + CLOSING_QUOTES + r"]*(?=\s|$)")


def plain_sentences(text: str) -> list[str]:
    """Split plain text into sentences: abbreviations and numbers end none.

    A sentence ends at ``.``, ``!`` or ``?`` (with any closing quote or
    bracket) followed by the end of the text or by a space and a capital,
    digit or opening quote, unless the word before a full stop is an
    abbreviation or a single letter (an initial). Text after the last end is
    one more sentence. The summary's sentence limit (check_presentation) and
    the role-word rule of check_claims both read this split, so the two
    cannot count sentences differently.
    """
    text = " ".join(text.split())
    sentences: list[str] = []
    last_end = 0
    for match in SENTENCE_END_RE.finditer(text):
        after = text[match.end():].lstrip()
        if after and not (after[0].isupper() or after[0].isdigit()
                          or after[0] in "\"'([" + OPENING_QUOTES):
            continue
        if match.group().startswith(".") and not match.group().startswith(".."):
            word = text[:match.start()].rsplit(" ", 1)[-1]
            word = word.lstrip("(\"'[" + OPENING_QUOTES).lower()
            if word in ABBREVIATIONS or re.fullmatch(r"[a-z]", word):
                continue
        sentences.append(text[last_end:match.end()].strip())
        last_end = match.end()
    if text[last_end:].strip():
        sentences.append(text[last_end:].strip())
    return sentences


def link_key(target: str, module_id: str) -> str:
    """Return what a ``[[...]]`` target names: a short id, or a full claim id.

    A bare label is first read in the module (core or submodule) whose field
    holds the link; ``check_claims.link_target`` then looks for it in the rest
    of that module's contract.
    """
    target = target.strip()
    if SHORT_ID_LINK_RE.match(target) or "/" in target:
        return target
    return f"{module_id}/{target}"


@dataclass(frozen=True)
class LinkTarget:
    """A claim a plain-text link resolves to, with what its rendering needs."""

    claim_id: str
    kind: str          # the kind code, e.g. "prop"
    label: str         # the claim's label, e.g. "prop:tagging"
    title: str         # the authored (TeX) header title
    short_id: str = ""  # set when the link was written as a short id

    @property
    def core(self) -> str:
        """The core module whose contract PDF holds the claim."""
        return self.claim_id.split("/", 1)[0]


Resolver = Callable[[str], LinkTarget | None]


def _plain_math_symbols() -> dict[str, str]:
    r"""Map each mapped character's math macro back to the character (``\le`` to ≤)."""
    found: dict[str, str] = {}
    for char, tex in UNICODE_TEX.items():
        match = re.fullmatch(r"\\ensuremath\{\\([A-Za-z]+)\}", tex)
        if match:
            found.setdefault(match.group(1), char)
    return found


#: What a macro inside a title's ``$...$`` flattens to in a plain title (PDF
#: bookmarks, graph labels, ``graphs/README.md``): the mapped character of
#: ``UNICODE_TEX`` whose TeX it is (``\varepsilon`` to ε, ``\ge`` to ≥), a few
#: aliases, and the operator words. A title may use exactly these macros in
#: its mathematics (``check_presentation``'s rule ``title-plain``); a symbol
#: missing here is added here, with a plain rendering from the mapped set or
#: ASCII, rather than spelled out in the title.
PLAIN_TITLE_MACROS: dict[str, str] = {
    **_plain_math_symbols(),
    "leq": "\N{LESS-THAN OR EQUAL TO}", "geq": "\N{GREATER-THAN OR EQUAL TO}",
    "ne": "\N{NOT EQUAL TO}", "star": "*", "ast": "*",
    "ldots": "\N{HORIZONTAL ELLIPSIS}", "dots": "\N{HORIZONTAL ELLIPSIS}",
    "cdots": "\N{HORIZONTAL ELLIPSIS}",
    **{word: word for word in ("min", "max", "inf", "sup", "lim", "log", "ln",
                               "exp", "det", "dim", "ker", "tr", "Tr")},
}
#: Macros of a title's mathematics whose argument is kept and whose name goes.
PLAIN_TITLE_WRAPPERS = ("mathrm", "mathsf", "mathbf", "mathit", "text",
                        "textrm", "operatorname")
#: Control symbols of a title's mathematics that flatten to a space.
PLAIN_TITLE_SPACES = (",", ";", ":", "!", " ")
TITLE_MATH_RE = re.compile(r"\$([^$]*)\$")
TITLE_WRAPPER_RE = re.compile(r"\\(?:" + "|".join(PLAIN_TITLE_WRAPPERS)
                              + r")\{([^{}]*)\}")


def _plain_math(math: str) -> str:
    """Flatten the mathematics of a title through ``PLAIN_TITLE_MACROS``."""
    math = TITLE_WRAPPER_RE.sub(r"\1", math)

    def symbol(match: re.Match[str]) -> str:
        name = match.group(1)
        if name is None:
            return " " if match.group(2) in PLAIN_TITLE_SPACES else match.group(0)
        shown = PLAIN_TITLE_MACROS.get(name)
        if shown is None:
            return name + " "
        following = match.string[match.end():match.end() + 1]
        return shown + (" " if shown.isalpha() and following.isalpha() else "")

    return re.sub(r"\\(?:([A-Za-z]+)|(.))\s*", symbol, math)


def unrenderable_title_tex(title: str) -> list[str]:
    r"""Return the TeX of a title that ``plain_title`` cannot render cleanly.

    Outside ``$...$`` every backslash is such TeX (an accent such as
    ``R\'enyi`` printed as ``R\textbackslash{}'enyi`` in a bookmark; a title
    writes the accented letter itself, from the mapped set); inside it, a
    control sequence that is neither in ``PLAIN_TITLE_MACROS``, nor a wrapper
    of ``PLAIN_TITLE_WRAPPERS``, nor a spacing symbol. Each is returned once, as
    written.
    """
    found: list[str] = []
    position = 0
    for match in TITLE_MATH_RE.finditer(title):
        found += re.findall(r"\\(?:[A-Za-z]+|.)", title[position:match.start()])
        for command in re.findall(r"\\(?:[A-Za-z]+|.)", match.group(1)):
            name = command[1:]
            if (name in PLAIN_TITLE_MACROS or name in PLAIN_TITLE_WRAPPERS
                    or name in PLAIN_TITLE_SPACES):
                continue
            found.append(command)
        position = match.end()
    found += re.findall(r"\\(?:[A-Za-z]+|.)", title[position:])
    return list(dict.fromkeys(found))


def plain_title(title: str) -> str:
    r"""Project authored TeX titles to text for graph labels and PDF bookmarks.

    The mathematics of a title flattens through ``PLAIN_TITLE_MACROS`` (``$d_A
    \ge 2$`` reads d_A≥2); formatting wrappers disappear; references retain
    stable labels, and a macro the map does not know keeps its name, which the
    presentation rule ``title-plain`` refuses in a claim title. The PDF
    heading and the claim index retain the authored mathematical notation.
    """
    title = TITLE_MATH_RE.sub(lambda math: "$" + _plain_math(math.group(1)) + "$",
                              title)
    title = re.sub(r"\\(?:emph|texttt|textbf|textrm)\{([^{}]*)\}", r"\1", title)
    title = re.sub(r"\\(?:ref|eqref|cref)\{([^{}]*)\}", r"\1", title)
    title = re.sub(r"\\([A-Za-z]+)", r"\1 ", title)
    title = re.sub(r"\\([&%_#$])", r"\1", title)
    return " ".join(title.replace("$", "").replace("{", "").replace("}", "")
                    .replace("~", " ").split())


def tex_title(title: str) -> str:
    """Keep existing authored TeX titles; escape titles that are plain text."""
    return title if "\\" in title or "$" in title else tex_text(title)


def xref_title(title: str) -> str:
    r"""Return an authored title fit to print in another contract.

    A ``\ref`` in a title names a label of the title's own contract, which the
    citing contract does not have; it is printed as the label instead.
    """
    return re.sub(r"\\(?:ref|eqref|cref)\{([^{}]*)\}", r"\\textsf{\1}",
                  tex_title(title))


TEX_ESCAPES: dict[str, str] = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def tex_text(text: str) -> str:
    """Escape plain metadata without treating it as authored mathematical TeX."""
    return "".join(TEX_ESCAPES.get(char, char) for char in text)


def tex_mapped(text: str) -> str:
    """Escape a plain-text field and set its mapped Unicode characters as TeX.

    Summaries and abstracts may carry the characters of ``UNICODE_TEX``; each
    becomes the TeX that renders it, so the contract does not depend on what
    the TeX installation's UTF-8 support covers. ``<``, ``>`` and ``|`` take
    their text-mode commands (``TEXT_SYMBOLS``): in OT1 they print as ``¡``,
    ``¿`` and a dash.
    """
    return "".join(TEX_ESCAPES.get(char) or TEXT_SYMBOLS.get(char)
                   or UNICODE_TEX.get(char, char) for char in text)


def _unmapped_tex(char: str) -> str:
    return r"\textsf{[U+" + f"{ord(char):04X}" + "]}"


#: Characters that print wrongly in OT1 text mode, beyond ``TEX_ESCAPES``.
TEXT_SYMBOLS: dict[str, str] = {"<": r"\textless{}", ">": r"\textgreater{}",
                                "|": r"\textbar{}"}


def _escape_free(text: str) -> str:
    return "".join(TEX_ESCAPES.get(char) or TEXT_SYMBOLS.get(char)
                   or UNICODE_TEX.get(char)
                   or (_unmapped_tex(char) if ord(char) > 127 else char)
                   for char in text)


def tex_safe(text: str) -> str:
    """Escape free text that no check restricts to the mapped Unicode set.

    Used for text the assembler prints from files the checker does not read
    (``interface.yaml``, ``spec/notation.md``): a character outside the mapped
    set would stop pdflatex, so it prints as its code point instead. Line
    breaks become spaces.
    """
    return _escape_free(" ".join(text.split()))


MARKDOWN_SPAN_RE = re.compile(r"(\$[^$]+\$|`[^`]*`|\*\*[^*]+\*\*|\*[^*\s][^*]*\*)")


def markdown_tex(text: str) -> str:
    r"""Render one Markdown table cell of ``spec/notation.md`` as TeX.

    ``$...$`` is the catalogue's mathematics and is kept as it stands (the
    notation macros are loaded); a code span becomes typewriter text, ``**x**``
    bold and ``*x*`` emphasis; everything else is escaped by ``tex_safe``.
    """
    out: list[str] = []
    for piece in MARKDOWN_SPAN_RE.split(" ".join(text.split())):
        if not piece:
            continue
        if piece.startswith("$"):
            out.append(piece)
        elif piece.startswith("`"):
            out.append(r"\texttt{" + _escape_free(piece[1:-1]) + "}")
        elif piece.startswith("**"):
            out.append(r"\textbf{" + markdown_tex(piece[2:-2]) + "}")
        elif piece.startswith("*") and len(piece) > 1:
            out.append(r"\emph{" + markdown_tex(piece[1:-1]) + "}")
        else:
            out.append(_escape_free(piece))
    return "".join(out)


def unicode_declarations() -> str:
    r"""Return one ``\DeclareUnicodeCharacter`` line per character of ``UNICODE_TEX``.

    The contract preamble carries them so that a mapped character written
    directly in TeX (a title, a claim body) renders as the plain-text fields
    render it.
    """
    return "".join(f"\\DeclareUnicodeCharacter{{{ord(char):04X}}}{{{tex}}}\n"
                   for char, tex in UNICODE_TEX.items())


def contract_pdf(core: str, from_dir: str) -> str:
    """Return the path of ``core``'s contract PDF relative to a directory.

    ``from_dir`` is ``"contract"`` for a link inside a contract PDF (which
    lives in ``spec/modules/<core>/``) and ``"graphs"`` for one inside a graph
    index (``spec/modules/<core>/graphs/``).
    """
    return ("../" if from_dir == "graphs" else "") + f"../{core}/contract.pdf"


def tex_link(target: LinkTarget, contract: str) -> str:
    r"""Render one resolved link for the PDF of ``contract``.

    Inside the same contract a claim prints as "Kind 7.3" and a short id as
    itself, both linked to the claim's stable destination; a claim of another
    contract prints as ``\xref`` does, and a short id links into that PDF.
    """
    destination = claim_anchor(target.claim_id)
    if target.core == contract:
        text = (tex_text(target.short_id) if target.short_id else
                f"{KIND_WORD.get(target.kind, 'Claim')}~\\ref*{{{target.label}}}")
        return f"\\hyperlink{{{destination}}}{{{text}}}"
    if target.short_id:
        pdf = contract_pdf(target.core, "contract")
        text = tex_text(target.short_id)
        return f"\\hyperref{{{pdf}}}{{}}{{{destination}}}{{{text}}}"
    return f"\\xref{{{target.claim_id}}}"


def tex_plain(text: str, resolve: Resolver | None, contract: str) -> str:
    """Escape a plain-text field for TeX, rendering its ``[[...]]`` links.

    A link the resolver does not know stays literal text; the checker has
    already reported it.
    """
    text = " ".join(text.split())
    if resolve is None:
        return tex_mapped(text)
    out: list[str] = []
    position = 0
    for match in LINK_RE.finditer(text):
        out.append(tex_mapped(text[position:match.start()]))
        target = resolve(match.group(1))
        out.append(tex_mapped(match.group(0)) if target is None
                   else tex_link(target, contract))
        position = match.end()
    out.append(tex_mapped(text[position:]))
    return "".join(out)


def _markdown_escape(text: str) -> str:
    return re.sub(r"([\\`*_{}\[\]()<>#+.!|~-])", r"\\\1", text)


def markdown_text(text: str) -> str:
    """Keep plain summaries from becoming Markdown links, HTML or formatting."""
    return _markdown_escape(" ".join(text.split()))


def markdown_plain(text: str, resolve: Resolver | None, contract: str) -> str:
    """Escape a plain-text field for a graph index, rendering its links.

    A link opens the target claim in its contract PDF; its text is the kind
    and title (or the short id it was written as).
    """
    text = " ".join(text.split())
    if resolve is None:
        return markdown_text(text)
    out: list[str] = []
    position = 0
    for match in LINK_RE.finditer(text):
        out.append(_markdown_escape(text[position:match.start()]))
        target = resolve(match.group(1))
        if target is None:
            out.append(_markdown_escape(match.group(0)))
        else:
            quoted = f"\N{LEFT DOUBLE QUOTATION MARK}{plain_title(target.title)}" \
                     "\N{RIGHT DOUBLE QUOTATION MARK}"
            words = (target.short_id if target.short_id else
                     f"{KIND_WORD.get(target.kind, 'Claim')} {quoted}")
            pdf = ("../contract.pdf" if target.core == contract
                   else contract_pdf(target.core, "graphs"))
            out.append(f"[{_markdown_escape(words)}]"
                       f"({pdf}#nameddest={claim_anchor(target.claim_id)})")
        position = match.end()
    out.append(_markdown_escape(text[position:]))
    return "".join(out)


def claim_anchor(claim_id: str) -> str:
    """Return a stable PDF destination, independent of theorem numbering."""
    return "claim-" + claim_id


def group_anchor(first_claim_id: str) -> str:
    """Use the group's existing start anchor, independent of its title/number."""
    return "group-" + first_claim_id


def group_slug(title: str) -> str:
    """Make a descriptive suffix; the numeric prefix guarantees uniqueness."""
    return re.sub(r"[^a-z0-9]+", "-", plain_title(title).lower()).strip("-") or "claims"
