r"""The LaTeX side shared by every figure: escaping, numbers, the palette, headers.

Every figure module turns parsed view-model JSON into a LaTeX string and does
nothing else; what they have in common lives here, so that a label is escaped
one way and a colour is named once.

THE PALETTE IS DEFINED ONCE, HERE, AND WRITTEN TO ``views-preamble.tex``
=======================================================================
:data:`PALETTE` is the only place a colour value appears in this package.
:func:`preamble` writes it as named ``xcolor`` colours, with the figure fonts,
the line and plot styles and the TikZ libraries, and every figure refers to
the names only. The values are the whitepaper's figure tokens:

* the diagrams draw in an accent (``blue!55!black``) and greys;
* the key-rate plots' series take :data:`SERIES`: the accent navy, vermilion,
  sky and ink, apart in greyscale (L* 24 / 56 / 74 / 9) and under protan and
  deutan simulation; every pair a reader must tell apart also differs in
  mark or line style. ``cqReference`` is the muted grey of a reference
  series (the ladder's n = 10^10 bar);
* the protocol swimlane's lanes are the whitepaper's lane tokens (Alice the
  accent, Bob teal, Public grey, Eve plum, an unheld source amber);
* the whitepaper's ``vouch`` red is not used: it means "the user must check
  this" there.

THE WHITEPAPER'S TOKENS WIN
===========================
The whitepaper defines the same names in its figure style and reads it
before ``views-preamble.tex``; that style sets ``\figtokensloaded``, and the
generated preamble then skips its own copy, so a token is defined once in a
document. A document without the whitepaper's figure style gets the copy
here. Two sizes for every figure, Fira Sans: ``\figmain`` (7.5 pt) and
``\figsmall`` (6.25 pt) (:data:`MAIN`, :data:`SMALL`); the plots set their
labels, ticks and direct labels in the same two (:data:`PLOT`,
:data:`PLOT_LABEL` are ``\figmain``, ticks ``\figsmall``).

ESCAPING IS FOR TEXT; MATH IS PASSED THROUGH
============================================
:func:`escape` makes a view-model string safe in text mode, including the
handful of non-ASCII symbols the view models carry. A string the view model
labels as math (an operation's or register's ``math`` field, written for
KaTeX) goes through :func:`math` instead, which only rewrites the KaTeX
spellings that plain LaTeX lacks without ``amsmath``. A character outside
both tables is an error rather than a silently missing glyph.
"""

from __future__ import annotations

import math as _math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

__all__ = [
    "LANE_FALLBACK",
    "MAIN",
    "PALETTE",
    "PLOT",
    "PLOT_LABEL",
    "SERIES",
    "SMALL",
    "ZERO_DISPLAY",
    "Rendered",
    "at",
    "draw",
    "escape",
    "header",
    "lane_colour",
    "math",
    "math_head",
    "node",
    "number",
    "numeral",
    "preamble",
    "rational",
    "series",
    "words",
]

ZERO_DISPLAY = 1e-12
"""Entries below this magnitude are printed and shaded as zero.

A display threshold, not a mathematical statement: the POVM view models carry
floating-point residue of order ``1e-16`` where the operator is exactly zero,
and the run records' own declared tolerance is ``1e-12``.
"""

PALETTE: Mapping[str, str] = {
    # The accent (the whitepaper's figAccent, blue!55!black) and its
    # family: every figure but the swimlane draws in these only.
    "cqAccent": "blue!55!black",
    "cqData": "cqAccent",
    "cqOptical": "cqAccent",
    "cqPositive": "cqAccent",
    # The plots' series, in this order (module docstring).
    "cqSeries1": "cqAccent",
    "cqSeries2": "D55E00",
    "cqSeries3": "56A8DC",
    "cqSeries4": "1A1A1A",
    # A reference series: muted grey.
    "cqReference": "black!38",
    # Neutrals.
    "cqInk": "black!85",
    "cqDetector": "cqInk",
    "cqMuted": "black!62",
    "cqNegative": "cqMuted",
    "cqRule": "black!22",
    "cqCellRule": "black!42",
    # Lanes, for the protocol swimlane only.
    "cqLaneAlice": "cqAccent",
    "cqLaneBob": "0E7C86",
    "cqLanePublic": "black!60",
    "cqLaneEve": "7A2E8E",
    "cqLaneSource": "B85C00",
}
"""Colour name to value: six hex digits, or an ``xcolor`` expression.

The same values as the whitepaper's figure style; its ``vouch`` red
is deliberately absent: it means "the user must check this" there.
"""

SERIES: tuple[str, ...] = ("cqSeries1", "cqSeries2", "cqSeries3", "cqSeries4")
"""The plots' series colours, in order."""

MAIN = r"\sffamily\figmain"
r"""The figures' main font: ``\figmain``, 7.5 pt Fira Sans."""

SMALL = r"\sffamily\figsmall"
r"""The figures' small font: ``\figsmall``, 6.25 pt Fira Sans, the floor."""

PLOT = r"\sffamily\figplot"
r"""The plots' legend and direct-label font, ``\figplot`` (= ``\figmain``)."""

PLOT_LABEL = r"\sffamily\figplotlabel"
r"""The plots' axis-label font, ``\figplotlabel`` (= ``\figmain``)."""


@dataclass(frozen=True)
class Rendered:
    """A figure's or table's body and its proposed caption.

    The body holds what the drawing shows; everything that explains,
    qualifies or gives provenance is in the caption, plain
    caption text written from the same data.
    """

    body: str
    caption: str


def series(count: int) -> list[str]:
    """Return the first ``count`` series colours.

    Past four the palette has no validated colour: a plot with more series
    folds or splits them instead.
    """
    if count > len(SERIES):
        raise ValueError(f"the palette has {len(SERIES)} series colours, not {count}")
    return list(SERIES[:count])


LANE_FALLBACK = "cqInk"
"""The colour of a lane the palette does not name."""

_TEXT_ESCAPES: Mapping[str, str] = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "|": r"\textbar{}",
    "<": r"\textless{}",
    ">": r"\textgreater{}",
    # The non-ASCII symbols the view models carry, by name.
    "\N{UP TACK}": r"$\perp$",
    "\N{MATHEMATICAL RIGHT ANGLE BRACKET}": r"$\rangle$",
    "\N{MATHEMATICAL LEFT ANGLE BRACKET}": r"$\langle$",
    "\N{MIDDLE DOT}": r"$\cdot$",
    "\N{RIGHTWARDS ARROW}": r"$\to$",
    "\N{GREATER-THAN OR EQUAL TO}": r"$\geq$",
    "\N{LESS-THAN OR EQUAL TO}": r"$\leq$",
    "\N{MULTIPLICATION SIGN}": r"$\times$",
    "\N{MINUS SIGN}": r"$-$",
    "\N{EN DASH}": "--",
    "\N{EM DASH}": "---",
    "\N{LEFT DOUBLE QUOTATION MARK}": "``",
    "\N{RIGHT DOUBLE QUOTATION MARK}": "''",
    "\N{RIGHT SINGLE QUOTATION MARK}": "'",
    "\N{HORIZONTAL ELLIPSIS}": r"\dots{}",
    "\N{GREEK SMALL LETTER SIGMA}": r"$\sigma$",
    "\N{GREEK SMALL LETTER FINAL SIGMA}": r"$\varsigma$",
    "\N{GREEK SMALL LETTER ETA}": r"$\eta$",
    "\N{GREEK SMALL LETTER EPSILON}": r"$\varepsilon$",
    "\N{GREEK SMALL LETTER LAMDA}": r"$\lambda$",
    "\N{GREEK SMALL LETTER ALPHA}": r"$\alpha$",
    "\N{GREEK SMALL LETTER THETA}": r"$\theta$",
    "\N{GREEK SMALL LETTER PHI}": r"$\varphi$",
    "\N{GREEK SMALL LETTER TAU}": r"$\tau$",
    "\N{GREEK SMALL LETTER MU}": r"$\mu$",
    "\N{GREEK CAPITAL LETTER GAMMA}": r"$\Gamma$",
    "\N{GREEK CAPITAL LETTER SIGMA}": r"$\Sigma$",
}


def escape(text: object) -> str:
    """Return ``text`` safe in LaTeX text mode.

    ``None`` prints as an em dash and the sifting failure value ``"perp"`` as
    the symbol, as the interactive view draws them.
    """
    if text is None:
        return "---"
    if text == "perp":
        return r"$\perp$"
    out: list[str] = []
    for ch in str(text):
        if ch in _TEXT_ESCAPES:
            out.append(_TEXT_ESCAPES[ch])
        elif ord(ch) < 128:
            out.append(ch)
        else:
            raise ValueError(f"no LaTeX spelling for {ch!r} in {text!r}")
    return "".join(out)


def words(text: object) -> str:
    """Return ``text`` escaped, each word boxed so a narrow node never hyphenates it.

    A label is read as a name, and a broken name reads worse than a slightly
    wide one.
    """
    return " ".join(rf"\mbox{{{escape(word)}}}" for word in str(text).split())


_KATEX_ONLY: Sequence[tuple[str, str]] = (
    (r"\text{", r"\mbox{"),
    (r"\lvert", "|"),
    (r"\rvert", "|"),
    (r"\operatorname{", r"\mathrm{"),
)

_TEXT_UNDERSCORE = re.compile(r"^\\text\{([A-Za-z]+)\\_([A-Za-z0-9']+)\}$")


def math(source: str) -> str:
    r"""Return a view model's KaTeX math string as plain-LaTeX math (no ``$``).

    A register whose math is a literal ``\text{X\_Y}`` -- the view model's
    spelling of a label it has no math for -- is drawn as ``X_{Y}``, which is
    what the label means; any other math is passed through with only the
    KaTeX-only macros of ``_KATEX_ONLY`` rewritten.
    """
    found = _TEXT_UNDERSCORE.match(source)
    if found:
        return f"{found.group(1)}_{{{found.group(2)}}}"
    out = source
    for old, new in _KATEX_ONLY:
        out = out.replace(old, new)
    if any(ord(ch) >= 128 for ch in out):
        raise ValueError(f"non-ASCII character in math {source!r}")
    return out


def math_head(source: str) -> str:
    r"""Return the symbol a defining math string names.

    That is what precedes its first top-level ``:`` or ``=``:
    ``\varsigma: K=\prod_m C_m\to\dots`` names ``\varsigma`` and
    ``r(x,v)=r^0_h(\dots)`` names ``r(x,v)``; a string with neither is
    returned whole. The swimlane prints the head; the definition is the
    subject of the other figures.
    """
    depth = 0
    for i, ch in enumerate(source):
        if ch in "{(":
            depth += 1
        elif ch in "})":
            depth -= 1
        elif ch in ":=" and depth == 0 and i > 0:
            return source[:i].strip()
    return source.strip()


def number(value: float, digits: int = 4) -> str:
    """Return ``value`` with at most ``digits`` significant digits, in ``$``.

    Magnitudes below :data:`ZERO_DISPLAY` print as ``0``; a negative value
    prints with a true minus sign.
    """
    return f"${numeral(value, digits)}$"


def numeral(value: float, digits: int = 4) -> str:
    """Return :func:`number`'s text without the ``$``, for use inside math."""
    if not _math.isfinite(value):
        raise ValueError(f"not a finite number: {value!r}")
    if abs(value) < ZERO_DISPLAY:
        return "0"
    magnitude = abs(value)
    if magnitude < 1e-3 or magnitude >= 1e5:
        mantissa, exponent = f"{magnitude:.{digits - 1}e}".split("e")
        mantissa = mantissa.rstrip("0").rstrip(".")
        body = rf"{mantissa}\times10^{{{int(exponent)}}}"
    else:
        # Rounded to ``digits`` significant digits but written out in full:
        # ``g`` alone would print 100 at two digits as ``1e+02``.
        body = format(Decimal(f"{magnitude:.{digits}g}"), "f")
    return f"{'-' if value < 0 else ''}{body}"


def rational(value: str | int | float) -> Fraction:
    """Parse an exact ``"p/q"`` string (or a number) as a fraction."""
    if isinstance(value, float):
        return Fraction(value)
    return Fraction(str(value))


def lane_colour(lane_id: str) -> str:
    """Return the palette name of a lane, :data:`LANE_FALLBACK` if unnamed."""
    parts = re.split(r"\W+", lane_id)
    name = "cqLane" + "".join(part.capitalize() for part in parts)
    return name if name in PALETTE else LANE_FALLBACK


def at(x: float, y: float) -> str:
    """Return a TikZ coordinate, in centimetres, to the millimetre's hundredth."""
    return f"({x:.3f},{y:.3f})"


def node(options: str, x: float, y: float, text: str) -> str:
    r"""Return one ``\node`` command."""
    return rf"\node[{options}] at {at(x, y)} {{{text}}};"


def draw(options: str, *points: tuple[float, float], via: str = "--") -> str:
    r"""Return one ``\draw`` command through ``points``, joined by ``via``."""
    path = f" {via} ".join(at(x, y) for x, y in points)
    return rf"\draw[{options}] {path};"


def header(figure: str, sources: Iterable[str], pins: Iterable[str]) -> str:
    """Return the comment block that opens every generated file."""
    lines = [
        f"% {figure}: generated by runs.bbm92_study.views; do not edit by hand.",
        "% Source JSON: " + ", ".join(sources) + ".",
        "% Pins: " + "; ".join(pins) + ".",
        "% Needs views-preamble.tex (palette, fonts, TikZ libraries) loaded first.",
    ]
    return "\n".join(lines) + "\n"


#: The tokens' fonts, line and plot styles, as the whitepaper's
#: figure style sets them; written inside the guard of :func:`preamble`.
TOKEN_STYLES: tuple[str, ...] = (
    r"\def\figfamily{\fontfamily{FiraSans-TLF}}",
    r"\def\figmain{\figfamily\fontsize{7.5}{9.2}\selectfont}",
    r"\def\figsmall{\figfamily\fontsize{6.25}{7.6}\selectfont}",
    r"\let\figplot\figmain",
    r"\let\figplotlabel\figmain",
    r"\def\figradius{3.4pt}",
    r"\tikzset{fig hair/.style={line width=0.4pt}, fig line/.style={line width=0.6pt},",
    r"  fig flow/.style={line width=0.9pt, black!55, -{Stealth[length=5pt]}},",
    r"  fig use/.style={line width=0.6pt, black!55, -{Stealth[length=4pt]}},",
    r"  fig chip/.style={fill=cqAccent!9, text=cqInk, rounded corners=1.5pt,",
    r"    inner xsep=2.2pt, inner ysep=1.2pt}}",
    r"\newcommand{\figtickexp}[1]{\pgfmathtruncatemacro\figexp{round(#1/ln(10))}%",
    r"  \ifnum\figexp<0 \textendash\the\numexpr-\figexp\relax\else\figexp\fi}",
    r"\pgfplotsset{",
    r"  fig numbers/.style={",
    r"    xticklabel={\pgfmathprintnumber[assume math mode=true]{\tick}},",
    r"    yticklabel={\pgfmathprintnumber[assume math mode=true]{\tick}}},",
    r"  fig log y/.style={yticklabel={10\textsuperscript{\figtickexp{\tick}}}},",
    r"  fig log x/.style={xticklabel={10\textsuperscript{\figtickexp{\tick}}}},",
    r"  fig axis/.style={fig numbers, axis line style={cqRule}, tick style={cqRule},",
    r"    grid style={cqRule!60, line width=0.3pt}, major grid style={cqRule!70},",
    r"    tick label style={font=\sffamily\figsmall, text=cqMuted},",
    r"    label style={font=\sffamily\figmain},",
    r"    legend style={font=\sffamily\figmain, draw=none, fill=none}},",
    r"}",
)


def preamble() -> str:
    r"""Return ``views-preamble.tex``: palette, fonts, styles and libraries.

    Loaded once by a document after ``tikz``, ``pgfplots``, ``booktabs`` and
    ``xcolor``. The palette, fonts and styles sit inside a guard: a document
    that read the whitepaper's figure style first (which sets
    ``\figtokensloaded``) keeps its own definitions, so no token is defined
    twice; any other document gets these. The fixed font sizes keep a
    figure's layout independent of the document's base size.
    """
    colours = "\n".join(
        rf"\definecolor{{{name}}}{{HTML}}{{{value}}}"
        if re.fullmatch(r"[0-9A-F]{6}", value)
        else rf"\colorlet{{{name}}}{{{value}}}"
        for name, value in PALETTE.items()
    )
    return "\n".join(
        [
            "% views-preamble.tex: generated by runs.bbm92_study.views; do not edit.",
            "% The palette (tex.PALETTE), the figure fonts and styles, the TikZ",
            "% libraries. The whitepaper defines the same tokens in its figure style",
            "% and reads it first; then the guard skips this copy.",
            "% Needs tikz, pgfplots, booktabs and xcolor loaded before it.",
            r"\usetikzlibrary{arrows.meta,calc}",
            r"\pgfplotsset{compat=1.18}",
            r"\ifdefined\figtokensloaded\else",
            colours,
            *TOKEN_STYLES,
            r"\fi",
            "",
        ]
    )
