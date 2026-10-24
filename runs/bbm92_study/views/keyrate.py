r"""The study's key-rate figures in native PGFPlots, from the sweeps' ``summary.csv``.

``runs/bbm92_study/plot.py`` draws the same sweeps with matplotlib as quick
looks. For the whitepaper they are redrawn here as PGFPlots, so they share the
other figures' fonts and palette and stay vector. Each figure reads
``<data>/<sweep>/summary.csv`` as ``runs/bbm92_study/summarize.py`` writes it:

======  ==========  ================================================================
figure  sweep       what it draws
======  ==========  ================================================================
F1      ``loss``    key rate per round against ``loss_db``, a line per block of
                    expected ``coincidences``; below it, the same rate as a
                    fraction of the perfect devices' asymptotic rate
F2      ``qber``    key rate per round against ``100 * qber``, a line per
                    ``loss_db``
F3      ``rounds``  key rate per round against ``rounds``, a line per ``loss_db``,
                    all losses in one plot
F3b     ``rounds``  key bits per expected coincidence against
                    ``expected_coincidences``, a line per ``loss_db``
F4      ``solvers`` key rate per round against ``alpha - 1`` (log), a line per
                    ``method``; beside it, each method's solve times
F5      ``routes``  key rate per round against the photon cutoff, encoded
                    (WPFSS) and licensed (FSS), a panel per ``devices``; F5t
                    tabulates the key length in bits with the snapped run's own
                    bound beside each reported one
F6      ``ladder``  key rate per rung as grouped horizontal bars, one per block of
                    ``coincidences`` and a grey reference block (by ``rounds``),
                    over a table of each row's value, source and change
F7      ``alpha``   ``key_length`` over its maximum for the same block, against
                    ``alpha - 1`` (log), a line per block, the maximum starred
======  ==========  ================================================================

THE RULES THE LINE FIGURES FOLLOW
==========================
* REALISTIC DEVICES ARE DRAWN, PERFECT ONES ARE THE REFERENCE: the realistic
  set has every source and receiver imperfection of the parameter table. Where
  a sweep has a ``devices`` column, the ``realistic`` rows are the solid lines
  with marks and the ``perfect`` rows the same colour, thin and dashed,
  without marks; both at the same channel.
* THE ASYMPTOTE IS THE PERFECT CURVES' ONLY. The closed form of
  :mod:`runs.bbm92_study.asymptote` is drawn dotted as ``n -> infinity``,
  on the perfect references only ("Analytic only").
* A POINT WITHOUT A POSITIVE KEY IS SHOWN, as an open downward triangle on
  the bottom axis at its x, in its series' colour; a point not yet run is
  left out and counted in the caption.
* Series take the series palette (``tex.SERIES``: navy, vermilion, sky, ink),
  apart in greyscale as well as hue, and differ in marker as well. Where lines
  overlap (F3b) the marks are open and shrink from series to series, so every
  one stays visible.
* SERIES ARE NAMED AT THEIR ENDS, NOT IN A LEGEND:
  a column of labels right of the axis, in each series' colour, each joined to
  its line's last point by a thin leader, pushed apart where they would
  collide, under a muted heading naming the quantity. What is left of a legend
  above the plot keys only the line styles (perfect dashed, the asymptote
  dotted, the open triangle). The two-panel figures whose right side is taken
  (F4's solve times, F5's second device set) keep their key above.
* Every figure shows rate per round where it shows a key at all, so the
  figures read on one scale; F3b's key per coincidence and F7's key length
  relative to its maximum are the two deliberate exceptions.
* Labels, legends and direct labels are ``\figmain`` (7.5 pt), ticks
  ``\figsmall`` (6.25 pt), on a light grid (the preamble's ``fig axis``); the
  legend sits above the plot unless a figure says otherwise, so it covers no
  line.
* The data is inline (``\addplot table``), so each ``.tex`` is self-contained.
* A sweep with no file or no drawable point gives no figure; the command line
  says so.

The captions are written from the same rows: the fixed parameters are the
label columns with a single value across the sweep. Device values cite their
registered sources (``\cite`` keys are refs/index.json ids, which the
whitepaper's bibliography carries).
"""

from __future__ import annotations

import csv
import io
import math as _math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise

from runs.bbm92_study.asymptote import (
    TEST_FRACTION,
    binary_entropy,
    ideal_rate,
    ideal_rate_per_coincidence,
)
from runs.bbm92_study.sweeps import LADDER_REFERENCE_ROUNDS, REALISTIC, mean_efficiency
from runs.bbm92_study.views.tex import (
    MAIN,
    PLOT,
    PLOT_LABEL,
    SMALL,
    Rendered,
    escape,
    numeral,
    series,
)

__all__ = ["FIGURES", "KeyRateFigure", "parse_summary", "render_keyrate"]

Row = dict[str, str]

MARKS: tuple[str, ...] = ("*", "square*", "triangle*", "diamond*", "pentagon*")
OPEN_MARKS: tuple[str, ...] = ("o", "square", "triangle", "diamond", "pentagon")
#: F3b's open marks shrink from series to series, so concentric ones all show.
OPEN_SIZES: tuple[float, ...] = (4.0, 3.0, 2.2, 1.5, 1.0)
#: A plot's axis box in cm; the whitepaper's text block is about 12.7 cm wide.
WIDTH = 9.0
HEIGHT = 5.4
#: The preamble's ``fig axis``: light grid, muted ticks in ``\figsmall``,
#: labels in ``\figmain``, tick numbers in the figure font.
AXIS = "scale only axis, fig axis, clip=false"
LEGEND = "legend cell align=left"
#: A series line: realistic devices, with marks.
LINE = "line width=1.0pt"
MARK_SIZE = "1.8pt"
PERFECT = "densely dashed, line width=0.7pt"
ASYMPTOTE = "dotted, line width=1.0pt"
#: The direct labels' column: its offset right of the axis and the height one
#: label needs, both in cm.
LABEL_OFFSET = 0.16
LABEL_HEIGHT = 0.34
ZERO = (
    "only marks, mark=triangle, mark size=3pt, "
    "mark options={rotate=180, solid, fill=white, line width=0.7pt}"
)


#: Plain decimal y ticks, without pgfplots' common factor: that factor's
#: label sits at the axis's top left, on a legend or a title.
_PLAIN_Y = (
    "scaled y ticks=false, y tick label style={{/pgf/number format/fixed, "
    "/pgf/number format/precision={precision}}}"
)


def _above(columns: int) -> str:
    """Return the options that put the legend in a row above the axis."""
    return (
        f"legend columns={columns}, legend style={{at={{(0.5,1.03)}}, "
        "anchor=south, /tikz/every even column/.append style={column sep=7pt}}"
    )

#: The device sets' values are the parameter table's, which every caption
#: points to rather than repeating them.
_DEVICES = (
    "The realistic and perfect devices are those of the parameter table; a "
    "round is one emitted pair."
)
_LADDER = (
    "Each value is taken from the source in its row; the misalignment is the "
    "laboratory bound on the polarization error, as a rotation of Bob's "
    "analyser."
)


@dataclass(frozen=True)
class KeyRateFigure:
    """One key-rate figure: its id, file name, sweep, drawing and caption note.

    ``draw`` names the drawing in ``_RENDER``; it defaults to ``figure``.
    ``note`` is a sentence the caption ends with. ``kind`` is ``"table"`` for a
    body that goes in a table float (F5t).
    """

    figure: str
    name: str
    sweep: str
    draw: str = ""
    note: str = ""
    kind: str = "figure"


FIGURES: tuple[KeyRateFigure, ...] = (
    KeyRateFigure("F1", "keyrate-loss", "loss", note=_DEVICES),
    KeyRateFigure("F2", "keyrate-qber", "qber", note=_DEVICES),
    KeyRateFigure("F3", "keyrate-rounds", "rounds", note=_DEVICES),
    KeyRateFigure("F3b", "keyrate-coincidences", "rounds", note=_DEVICES),
    KeyRateFigure("F4", "keyrate-solvers", "solvers", note=_DEVICES),
    KeyRateFigure("F5", "keyrate-routes", "routes", note=_DEVICES),
    KeyRateFigure("F5t", "keyrate-routes-table", "routes", note=_DEVICES, kind="table"),
    KeyRateFigure("F6", "keyrate-ladder", "ladder", note=_LADDER),
    KeyRateFigure("F7", "keyrate-alpha", "alpha", note=_DEVICES),
)


def parse_summary(text: str) -> list[Row]:
    """Parse a ``summary.csv`` into rows of strings."""
    return list(csv.DictReader(io.StringIO(text)))


# --------------------------------------------------------------------------
# Reading rows
# --------------------------------------------------------------------------


def _float(row: Row, key: str) -> float | None:
    value = row.get(key, "")
    try:
        return float(value) if value not in ("", None) else None
    except ValueError:
        return None


def _ok(row: Row) -> bool:
    return row.get("status") == "ok"


def _positive(row: Row) -> bool:
    length = _float(row, "key_length")
    return _ok(row) and length is not None and length > 0


def _zero(row: Row) -> bool:
    return _ok(row) and not _positive(row)


def _devices(row: Row) -> str:
    return row.get("devices") or "realistic"


def _rate(r: Row) -> float | None:
    length, rounds = _float(r, "key_length"), _float(r, "rounds")
    return length / rounds if length is not None and rounds else None


def _per_coincidence(r: Row) -> float | None:
    length, c = _float(r, "key_length"), _float(r, "expected_coincidences")
    return length / c if length is not None and c else None


def _single_value(rows: Sequence[Row], key: str) -> float | None:
    values = {v for r in rows if _ok(r) and (v := _float(r, key)) is not None}
    return values.pop() if len(values) == 1 else None


def _label_columns(rows: Sequence[Row]) -> list[str]:
    """Return the sweep's label columns: those between ``point`` and ``status``."""
    if not rows:
        return []
    keys = list(rows[0])
    return keys[keys.index("point") + 1 : keys.index("status")]


# --------------------------------------------------------------------------
# Words
# --------------------------------------------------------------------------


def _power(value: float) -> str:
    exponent = _math.log10(value) if value > 0 else 0.0
    if value > 0 and abs(exponent - round(exponent)) < 1e-9:
        return f"10^{{{round(exponent)}}}"
    mantissa = value / 10 ** _math.floor(exponent)
    if abs(mantissa - round(mantissa)) < 1e-9:
        return rf"{round(mantissa)} \times 10^{{{_math.floor(exponent)}}}"
    return numeral(value, 3)


def _describe(column: str, value: float | str) -> str:
    """Word one label value for a series label or a caption."""
    if column == "rounds":
        return f"$n = {_power(float(value))}$"
    if column == "coincidences":
        return f"${_power(float(value))}$ coincidences"
    if column == "loss_db":
        return f"${numeral(float(value), 3)}$\\,dB"
    if column == "qber":
        return f"QBER ${numeral(100 * float(value), 3)}\\,\\%$"
    if column == "alpha":
        return rf"$\alpha = {numeral(float(value), 6)}$"
    if column == "devices":
        return "realistic devices" if value == "realistic" else "perfect devices"
    return escape(value)


def _missing(rows: Sequence[Row]) -> str:
    """Return the caption sentence on the points not yet run."""
    missing = sum(1 for r in rows if not _ok(r))
    if not missing:
        return ""
    return (
        f"{missing} point{'s' if missing != 1 else ''} of the sweep "
        f"{'have' if missing != 1 else 'has'} not been run yet."
    )


def _zero_sentence(rows: Sequence[Row], where: str = "bottom axis") -> str:
    if not any(_zero(r) for r in rows):
        return ""
    return (
        f"An open downward triangle on the {where} marks a point without a "
        "positive key length."
    )


def _fixed(rows: Sequence[Row], skip: Sequence[str]) -> str:
    """Return the caption clause naming the label columns with a single value."""
    fixed = []
    for column in _label_columns(rows):
        if column in skip:
            continue
        values = {r[column] for r in rows if r.get(column) not in ("", None)}
        if len(values) == 1:
            fixed.append(_describe(column, values.pop()))
    return ", ".join(fixed)


def _method(rows: Sequence[Row]) -> str:
    """Return the caption sentence on how alpha and error correction were set."""
    parts = []
    searched = {r.get("alpha_searched") for r in rows if _ok(r)}
    if searched == {"True"}:
        parts.append(
            r"the R\'enyi order $\alpha$, a free parameter of the entropy bound, is "
            "chosen per point to maximise the key"
        )
    f_ec = _single_value(rows, "f_ec")
    if f_ec is not None:
        parts.append(
            f"error correction is charged at ${numeral(f_ec, 3)}$ times the "
            "entropy of Alice's raw key given Bob's data under the honest model"
        )
    if not parts:
        return ""
    sentence = "; ".join(parts)
    return sentence[0].upper() + sentence[1:] + "."


def _oracle_note(rows: Sequence[Row]) -> str:
    """Return the caption sentence on points that ran with another oracle."""
    other = sum(1 for r in rows if _ok(r) and r.get("oracle") == "spectral")
    if not other:
        return ""
    where = "; ".join(
        _where(r, rows) for r in rows if _ok(r) and r.get("oracle") == "spectral"
    )
    return (
        f"{other} point{'s' if other != 1 else ''} ({where}) ran with the spectral "
        "linear oracle, an exact closed-form minimiser, in place of QICS, the "
        "conic solver every other point uses (the study declares it for "
        f"{'these points' if other != 1 else 'this point'}, where QICS once "
        "stalled)."
    )


def _where(row: Row, rows: Sequence[Row]) -> str:
    """Name a row by the label columns that vary across the sweep."""
    words = []
    for column in _label_columns(rows):
        if column == "rounds":  # follows from the others
            continue
        values = {r.get(column) for r in rows if r.get(column) not in ("", None)}
        if len(values) > 1 and row.get(column) not in ("", None):
            words.append(_describe(column, row[column]))
    return ", ".join(words)


def _perfect_note(rows: Sequence[Row]) -> str:
    """Return the sentence defining perfect devices, if the sweep has them."""
    if not any(_devices(r) == "perfect" for r in rows):
        return ""
    return (
        "Perfect devices: a source of visibility 1, and receivers with "
        "efficiency 1, no dark counts, a balanced basis split, ideal polarizing "
        "beam splitters and no misalignment."
    )


def _asymptote_note(qber: float, f_ec: float) -> str:
    """Return the sentence giving the asymptote in closed form."""
    keep = 1 - TEST_FRACTION
    return (
        r"The asymptote is $\tfrac{"
        + str(keep.numerator)
        + "}{"
        + str(keep.denominator)
        + r"} \cdot \tfrac12 \cdot \bigl(1 - h(Q) - f\,h(Q)\bigr) = "
        + numeral(ideal_rate_per_coincidence(qber, f_ec), 3)
        + "$ bits per coincidence: "
        + f"{TEST_FRACTION.numerator}/{TEST_FRACTION.denominator}"
        + " of the rounds are test rounds and give no key, and half of the other "
        "coincidences survive sifting; $h$ is the binary entropy, $f$ the "
        "error-correction factor."
    )


def _rounds_rule(rows: Sequence[Row]) -> str:
    """Return the caption sentence on how n was set, if a sweep sets it so."""
    if not any(r.get("coincidences") for r in rows):
        return ""
    return (
        "The number of rounds $n$ (emitted pairs) of each point is set, to two "
        "significant digits, so that about the stated number of coincidences is "
        "expected."
    )


def _gap(r: Row) -> float | None:
    """Return a point's convergence gap, the summary's ``gap`` column, at least 0.

    The record's Frank--Wolfe gap of the candidate the bound comes from: the
    bound is that candidate's objective minus this gap, and the minimum lies
    between the two, so closing the gap could raise the bound by at most this
    much, which is what a figure shows where it shows the convergence gap.
    Not ``h_low - h_lb``: h_low is the solver's own point on
    the rounded copy of the receiver model, while h_lb is evaluated on the
    declared one, so their difference mixes the convergence gap with the
    rounding (README, "Termination").
    """
    gap = _float(r, "gap")
    return max(gap, 0.0) if gap is not None else None


def _relative_gap(r: Row) -> float | None:
    """Return the convergence gap over the candidate's objective, h_lb + gap."""
    gap, lb = _gap(r), _float(r, "h_lb")
    if gap is None or lb is None or lb + gap == 0:
        return None
    return gap / abs(lb + gap)


def _gap_sentence(rows: Sequence[Row]) -> str:
    """Return the caption sentence giving the largest convergence gap shown."""
    gaps = [
        (g, r) for r in rows if _positive(r) and (g := _relative_gap(r)) is not None
    ]
    if not gaps:
        return ""
    worst, row = max(gaps, key=lambda item: item[0])
    where = _where(row, rows)
    return (
        "Every rate is the certified bound; the largest convergence gap among "
        "the points shown (how far the bound lies below the objective of the "
        "solver's point it comes from, relative to that objective; closing it "
        f"could raise the bound by at most this much) is "
        f"${_percent(100 * worst)}\\,\\%$" + (f", at {where}." if where else ".")
    )


def _join(*sentences: str) -> str:
    return " ".join(s for s in sentences if s)


# --------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------


def _table(points: Sequence[tuple[float, float]]) -> str:
    lines = "\n".join(f"{x!r} {y!r}" for x, y in points)
    return f"table[row sep=newline] {{\nx y\n{lines}\n}}"


def _solid(k: int, colour: str) -> str:
    return (
        f"{colour}, solid, {LINE}, mark={MARKS[k % len(MARKS)]}, "
        f"mark size={MARK_SIZE}, mark options={{solid}}"
    )


def _power_text(value: float) -> str:
    r"""Return :func:`_power` in text mode: a label's digits in the figure font."""
    exponent = _math.floor(_math.log10(value)) if value > 0 else 0
    mantissa = value / 10**exponent if value > 0 else 0.0
    sign = "\\textendash{}" if exponent < 0 else ""
    if value > 0 and abs(mantissa - 1) < 1e-9:
        return f"10\\textsuperscript{{{sign}{abs(exponent)}}}"
    if value > 0 and abs(mantissa - round(mantissa)) < 1e-9:
        return (
            f"{round(mantissa)}\\,\\texttimes\\,10\\textsuperscript{{{sign}{abs(exponent)}}}"
        )
    return f"${numeral(value, 3)}$"


def _short(column: str, value: float | str) -> str:
    """Word a series value for a direct label, its quantity named in the heading."""
    if column in ("coincidences", "rounds"):
        return _power_text(float(value))
    if column == "loss_db":
        text = numeral(float(value), 3)
        return f"{text}\\,dB" if "\\" not in text else f"${text}$\\,dB"
    return _describe(column, value)


_HEADINGS: Mapping[str, str] = {
    "coincidences": "coincidences",
    "rounds": "rounds $n$",
    "loss_db": "channel loss",
}


def _end_labels(
    ends: Sequence[tuple[str, str, float, float]],
    *,
    xmax: float,
    ymin: float,
    ymax: float,
    height: float,
    log: bool = False,
    heading: str = "",
) -> list[str]:
    """Return the direct labels of a panel's series, right of its axis.

    ``ends`` holds each series' colour, label and last point. The labels sit
    in one column at ``xmax``, each at its line's last y, pushed apart (in the
    axis's own scale) where they would collide, and are joined to the last
    point by a thin leader in the series' colour; ``heading`` names the
    quantity above the column. ``height`` is the axis height in cm.
    """
    if not ends:
        return []

    def scale(y: float) -> float:
        return _math.log10(y) if log else y

    def unscale(v: float) -> float:
        return 10**v if log else v

    lo, hi = scale(ymin), scale(ymax)
    gap = (hi - lo) * LABEL_HEIGHT / height
    order = sorted(ends, key=lambda e: scale(e[3]))
    spots = [scale(e[3]) for e in order]
    for i in range(1, len(spots)):
        spots[i] = max(spots[i], spots[i - 1] + gap)
    over = spots[-1] - (hi - gap / 2)
    if over > 0:
        spots = [v - over for v in spots]
        for i in range(len(spots) - 2, -1, -1):
            spots[i] = min(spots[i], spots[i + 1] - gap)
    out = []
    for (colour, label, x, y), v in zip(order, spots, strict=True):
        at = unscale(v)
        out.append(
            rf"\draw[{colour}, line width=0.5pt] (axis cs:{x!r},{y!r}) -- "
            rf"(axis cs:{xmax!r},{at!r}) -- ++({LABEL_OFFSET / 2}cm,0pt);"
        )
        out.append(
            rf"\node[anchor=west, inner sep=1pt, font={PLOT}\bfseries, "
            rf"text={colour}] at ([xshift={LABEL_OFFSET}cm]axis cs:{xmax!r},{at!r}) "
            f"{{{label}}};"
        )
    if heading:
        out.append(
            rf"\node[anchor=south west, inner sep=1pt, font={SMALL}, text=cqMuted] "
            rf"at ([xshift={LABEL_OFFSET}cm, yshift={LABEL_HEIGHT / 2}cm]axis cs:"
            f"{xmax!r},{unscale(spots[-1])!r}) {{{heading}}};"
        )
    return out


def _ends(series: Series, colours: Mapping[float, str], column: str) -> list[
    tuple[str, str, float, float]
]:
    """Return each series' colour, short label and last point (:func:`_end_labels`)."""
    return [
        (colours[k], _short(column, k), *max(points)) for k, points in series if points
    ]


Series = list[tuple[float, list[tuple[float, float]]]]


def _series(
    rows: Sequence[Row],
    by: str,
    x: Callable[[Row], float | None],
    y: Callable[[Row], float | None],
    devices: str | None = None,
) -> Series:
    """Group the positive points by ``by``, each series sorted by ``x``."""
    groups: dict[float, list[tuple[float, float]]] = {}
    for r in rows:
        key = _float(r, by)
        if key is None or not _positive(r):
            continue
        if devices is not None and _devices(r) != devices:
            continue
        xv, yv = x(r), y(r)
        if xv is None or yv is None or yv <= 0:
            continue
        groups.setdefault(key, []).append((xv, yv))
    return [(k, sorted(v)) for k, v in sorted(groups.items()) if v]


def _zeros(
    rows: Sequence[Row],
    by: str,
    x: Callable[[Row], float | None],
    devices: str = "realistic",
) -> dict[float, list[float]]:
    """Return the x of each zero-key point, grouped by ``by``."""
    out: dict[float, list[float]] = {}
    for r in rows:
        key, xv = _float(r, by), x(r)
        if key is None or xv is None or not _zero(r) or _devices(r) != devices:
            continue
        out.setdefault(key, []).append(xv)
    return out


def _keys(rows: Sequence[Row], by: str) -> list[float]:
    """Return every value of ``by`` among the run points, sorted."""
    return sorted({k for r in rows if _ok(r) and (k := _float(r, by)) is not None})


def _colours(keys: Sequence[float]) -> dict[float, str]:
    return dict(zip(keys, series(len(keys)), strict=True))


def _perfect_lines(series: Series, colours: Mapping[float, str]) -> list[str]:
    return [
        rf"\addplot[{colours[k]}, {PERFECT}, forget plot] {_table(points)};"
        for k, points in series
    ]


def _zero_marks(
    zeros: Mapping[float, Sequence[float]],
    colours: Mapping[float, str],
    y: float,
    stagger: float = 1.0,
) -> list[str]:
    """Return the zero-key marks; on a log axis ``stagger`` lifts each series.

    Series whose zero-key points share an x would otherwise draw their marks
    on top of each other (the readers' F2: "the triangles overlap"); the
    ``i``-th series sits at ``y * stagger**i``.
    """
    out = []
    for i, (k, xs) in enumerate(sorted(zeros.items())):
        at = y * stagger**i
        coords = " ".join(f"({x!r},{at!r})" for x in sorted(xs))
        out.append(rf"\addplot[{colours.get(k, 'cqMuted')}, {ZERO}, forget plot] "
                   rf"coordinates {{{coords}}};")
    return out


def _reference_legend(perf: bool, asymptote: bool, zeros: bool) -> list[str]:
    """Return legend entries for the reference styles, after the series' own."""
    out = []
    if perf:
        out += [
            rf"\addlegendimage{{cqMuted, {PERFECT}}}",
            r"\addlegendentry{perfect devices (same colours)}",
        ]
    if asymptote:
        out += [
            rf"\addlegendimage{{cqInk, {ASYMPTOTE}}}",
            # No bare comma (pgfplots splits legend entries on commas), and
            # \rightarrow, not \to, which breaks a pgfplots legend entry.
            r"\addlegendentry{perfect{,} $n \rightarrow \infty$}",
        ]
    if zeros:
        out += [
            rf"\addlegendimage{{cqMuted, {ZERO}}}",
            r"\addlegendentry{no positive key}",
        ]
    return out


#: The factor between staggered zero-key marks on a log axis.
STAGGER = 1.5


def _log_floor(*series: Series) -> float:
    """Return a log axis's bottom, below every drawn value, for the zero marks.

    Four staggered marks reach ``floor * STAGGER**3``, still below the data.
    """
    ys = [y for s in series for _k, points in s for _x, y in points]
    return min(ys) / 4.0 if ys else 1e-6


def _single(xlabel: str, ylabel: str, options: str, body: Sequence[str]) -> str:
    return _panels(
        [Panel(xlabel, ylabel, f"width={WIDTH}cm, height={HEIGHT}cm, {options}", body)]
    )


@dataclass(frozen=True)
class Panel:
    """One axis of a figure: its labels, its options and what it draws.

    ``place`` positions it against the panel before (``below`` or ``right``);
    the first panel ignores it.
    """

    xlabel: str
    ylabel: str
    options: str
    body: Sequence[str]
    place: str = "below"


#: The gap between panels, in cm: below leaves room for the upper panel's
#: x ticks when it has no label; right for the right panel's y ticks.
_GAP = {"below": 0.35, "right": 1.6}


def _panels(panels: Sequence[Panel]) -> str:
    """Return one tikzpicture holding the panels, each placed by the one before."""
    lines = [rf"\begin{{tikzpicture}}[font={PLOT}]"]
    for k, panel in enumerate(panels):
        where = ""
        if k:
            if panel.place == "right":
                where = (
                    f"at={{(p{k - 1}.south east)}}, anchor=south west, "
                    f"xshift={_GAP['right']}cm, "
                )
            else:
                where = (
                    f"at={{(p{k - 1}.south west)}}, anchor=north west, "
                    f"yshift=-{_GAP['below']}cm, "
                )
        logs = ("fig log x, " if "xmode=log" in panel.options else "") + (
            "fig log y, " if "ymode=log" in panel.options else ""
        )
        lines += [
            rf"\begin{{axis}}[name=p{k}, {where}{AXIS}, {logs}"
            f"xlabel={{{panel.xlabel}}}, ylabel={{{panel.ylabel}}}, {panel.options}]",
            *panel.body,
            r"\end{axis}",
        ]
    lines += [r"\end{tikzpicture}", ""]
    return "\n".join(lines)


def _qber_and_fec(rows: Sequence[Row]) -> tuple[float, float] | None:
    """Return the perfect rows' (QBER, f_EC), the asymptote's arguments."""
    perf = [r for r in rows if _devices(r) == "perfect"]
    q, f = _single_value(perf, "qber"), _single_value(perf, "f_ec")
    return (q, f) if q is not None and f is not None else None


# --------------------------------------------------------------------------
# F1: loss
# --------------------------------------------------------------------------


def _f1(rows: Sequence[Row]) -> Rendered | None:
    """Rate against loss, and below it the rate over the perfect asymptote.

    The rate panel alone is a straight line per block on a log axis: with the
    coincidences fixed, the loss only sets n, so the lines are hard to tell
    apart. The lower panel divides each rate by
    the perfect devices' asymptotic rate at the same loss, on a linear axis,
    where the blocks and the device sets separate.
    """

    def x(r: Row) -> float | None:
        return _float(r, "loss_db")

    real = _series(rows, "coincidences", x, _rate, "realistic")
    perf = _series(rows, "coincidences", x, _rate, "perfect")
    if not real and not perf:
        return None
    keys = _keys(rows, "coincidences")
    colours = _colours(keys)
    zeros = _zeros(rows, "coincidences", x)
    fixed = _qber_and_fec(rows)
    losses = _keys(rows, "loss_db")
    curve: list[tuple[float, float]] = []
    if fixed and perf and losses:
        q, f = fixed
        curve = [(L, ideal_rate(L, q, f)) for L in _grid(losses[0], losses[-1], 33)]
    floor = _log_floor(real, perf, [(0.0, curve)] if curve else [])
    xrange = f"xmin={losses[0] - 1!r}, xmax={losses[-1] + 1!r}, "
    top: list[str] = []
    for k, (c, points) in enumerate(real):
        top.append(rf"\addplot[{_solid(k, colours[c])}, forget plot] {_table(points)};")
    top += _perfect_lines(perf, colours)
    if curve:
        top.append(rf"\addplot[cqInk, {ASYMPTOTE}, forget plot] {_table(curve)};")
    top += _zero_marks(zeros, colours, floor, STAGGER)
    references = _reference_legend(bool(perf), bool(curve), bool(zeros))
    top += references
    if not fixed:
        ys = [y for s in (real, perf) for _k, pts in s for _x, y in pts]
        top += _end_labels(
            _ends(real, colours, "coincidences"),
            xmax=losses[-1] + 1,
            ymin=floor / 1.2,
            ymax=max(ys),
            height=HEIGHT * 0.6,
            log=True,
            heading=_HEADINGS["coincidences"],
        )
    panels = [
        Panel(
            "" if fixed else "total channel loss (dB)",
            "key rate per round",
            f"width={WIDTH}cm, height={HEIGHT * 0.6}cm, {xrange}"
            f"ymode=log, ymin={floor / 1.2!r}, ymajorgrids, xmajorgrids, "
            + ("xticklabels={}, " if fixed else "")
            + f"{_above(max(len(references) // 2, 1))}, {LEGEND}",
            top,
        )
    ]
    ratios: list[str] = []
    spread, worst = 0.0, 0.0
    if fixed:
        q, f = fixed

        def fraction(r: Row) -> float | None:
            rate, loss = _rate(r), _float(r, "loss_db")
            return rate / ideal_rate(loss, q, f) if rate and loss is not None else None

        realistic_fractions: Series = []
        for kind, style in (("perfect", PERFECT), ("realistic", "")):
            for c, points in _series(rows, "coincidences", x, fraction, kind):
                if not style:
                    realistic_fractions.append((c, points))
                mean = sum(y for _x, y in points) / len(points)
                for lx, y in points:
                    if abs(y - mean) / mean > spread:
                        spread, worst = abs(y - mean) / mean, lx
                line = (
                    f"{colours[c]}, {style}"
                    if style
                    else _solid(keys.index(c), colours[c])
                )
                ratios.append(rf"\addplot[{line}, forget plot] {_table(points)};")
        ratios.append(
            rf"\addplot[cqInk, {ASYMPTOTE}, forget plot] "
            f"coordinates {{({losses[0] - 1!r},1) ({losses[-1] + 1!r},1)}};"
        )
        ratios += _end_labels(
            _ends(realistic_fractions, colours, "coincidences"),
            xmax=losses[-1] + 1,
            ymin=0.0,
            ymax=1.05,
            height=HEIGHT * 0.7,
            heading=_HEADINGS["coincidences"],
        )
        panels.append(
            Panel(
                "total channel loss (dB)",
                r"rate $/$ perfect $n \rightarrow \infty$",
                f"width={WIDTH}cm, height={HEIGHT * 0.7}cm, {xrange}"
                "ymin=0, ymax=1.05, ytick={0,0.2,0.4,0.6,0.8,1}, ymajorgrids, "
                "xmajorgrids",
                ratios,
            )
        )
    tex = _panels(panels)
    blocks = [_describe("coincidences", c) for c in keys]
    caption = _join(
        "Secret key rate per round against the total channel loss, split equally "
        "between the two arms, one colour per block of expected coincidences, "
        f"from {blocks[0]} to {blocks[-1]}, named at the lines' ends. Solid "
        "lines are the realistic "
        "devices, dashed lines of the same colour the perfect ones, at the same "
        r"channel; the dotted line is the perfect devices' rate as $n \to \infty$ "
        "(closed form; see the figure against coincidences).",
        "Top: the rate itself, which falls with the transmission. Bottom: each "
        "rate divided by the asymptotic rate at the same loss. Every line stays "
        f"within ${_percent(100 * spread)}\\,\\%$ of its own mean, so the loss "
        "changes the key almost only through the coincidences it leaves; the "
        f"largest departure is at {_describe('loss_db', worst)}, where the same "
        "coincidences take the fewest rounds and the rate is a little higher "
        "(the QBER figure shows the same at its threshold). The gap below 1 is "
        "the cost of the finite block "
        "(more coincidences, less gap) and, for the realistic devices, of their "
        "efficiency and their errors: for the same coincidences they need "
        rf"$1/{numeral(mean_efficiency('realistic'), 3)}^2$ times the rounds (the "
        "mean port efficiency, squared), and their errors cost key per "
        "coincidence besides."
        if fixed
        else "",
        _rounds_rule(rows),
        _fixed_sentence(rows, ["loss_db", "coincidences", "rounds", "devices"]),
        _gap_sentence(rows),
        _method(rows),
        _zero_sentence(rows),
        _missing(rows),
    )
    return Rendered(tex, caption)


def _grid(lo: float, hi: float, count: int) -> list[float]:
    return [lo + (hi - lo) * i / (count - 1) for i in range(count)]


def _fixed_sentence(rows: Sequence[Row], skip: Sequence[str]) -> str:
    fixed = _fixed(rows, skip)
    return f"Fixed: {fixed}." if fixed else ""


# --------------------------------------------------------------------------
# F2: QBER
# --------------------------------------------------------------------------


def _qber_threshold(f_ec: float) -> float:
    """Return the QBER at which the perfect asymptotic rate reaches zero."""
    lo, hi = 0.0, 0.5
    for _ in range(60):
        mid = (lo + hi) / 2
        if 1.0 - (1.0 + f_ec) * binary_entropy(mid) > 0:
            lo = mid
        else:
            hi = mid
    return lo


def _f2(rows: Sequence[Row]) -> Rendered | None:
    def x(r: Row) -> float | None:
        q = _float(r, "qber")
        return 100 * q if q is not None else None

    real = _series(rows, "loss_db", x, _rate, "realistic")
    perf = _series(rows, "loss_db", x, _rate, "perfect")
    if not real and not perf:
        return None
    keys = _keys(rows, "loss_db")
    colours = _colours(keys)
    zeros = _zeros(rows, "loss_db", x)
    f_ec = _single_value(rows, "f_ec")
    curves: list[tuple[float, list[tuple[float, float]]]] = []
    if f_ec is not None and perf:
        top = _qber_threshold(f_ec) * 0.999
        for loss in keys:
            curves.append(
                (
                    loss,
                    [
                        (100 * q, ideal_rate(loss, q, f_ec))
                        for q in _grid(0.0, top, 40)
                    ],
                )
            )
    floor = _log_floor(real, perf)
    body: list[str] = []
    for k, (loss, points) in enumerate(real):
        body.append(
            rf"\addplot[{_solid(k, colours[loss])}, forget plot] {_table(points)};"
        )
    body += _perfect_lines(perf, colours)
    for loss, curve in curves:
        kept = [(qx, y) for qx, y in curve if y >= floor]
        body.append(
            rf"\addplot[{colours[loss]}, {ASYMPTOTE}, forget plot] {_table(kept)};"
        )
    body += _zero_marks(zeros, colours, floor, STAGGER)
    body += _reference_legend(bool(perf), bool(curves), bool(zeros))
    qs = [px for s in (real, perf) for _k, pts in s for px, _y in pts]
    qs += [z for zs in zeros.values() for z in zs]
    ys = [y for s in (real, perf) for _k, pts in s for _x, y in pts]
    qmax = max(qs) + 0.5 if qs else 1.0
    body += _end_labels(
        _ends(real, colours, "loss_db"),
        xmax=qmax,
        ymin=floor / 1.3,
        ymax=max(ys) if ys else 1.0,
        height=HEIGHT,
        log=True,
        heading=_HEADINGS["loss_db"],
    )
    tex = _single(
        r"QBER (\%)",
        "key rate per round",
        f"xmax={qmax!r}, ymode=log, ymin={floor / 1.3!r}, ymajorgrids, xmajorgrids, "
        f"{_above(3)}, {LEGEND}",
        body,
    )
    caption = _join(
        "Secret key rate per round against the quantum bit error rate of the "
        "source (set through its visibility, for both device sets; the realistic "
        "receivers add their own errors on top), one colour per total channel "
        "loss, named at the lines' ends. Solid lines are the realistic devices; "
        "dashed lines of the same "
        "colour are the perfect ones, and dotted lines their asymptotic rate as "
        "$n \\to \\infty$, "
        "which reaches zero at "
        f"QBER ${numeral(100 * _qber_threshold(f_ec), 3)}\\,\\%$."
        if f_ec is not None
        else "",
        _rounds_rule(rows),
        _qber_reach(rows),
        _fixed_sentence(rows, ["qber", "loss_db", "rounds", "devices"]),
        _gap_sentence(rows),
        _method(rows),
        "An open downward triangle marks a realistic point without a positive "
        "key length; a perfect line ends at its last positive point."
        if any(_zero(r) for r in rows)
        else "",
        _missing(rows),
    )
    return Rendered(tex, caption)


def _qber_reach(rows: Sequence[Row]) -> str:
    """Return the sentence on the largest QBER with a key, per loss (realistic)."""
    reach: dict[float, float] = {}
    for r in rows:
        loss, q = _float(r, "loss_db"), _float(r, "qber")
        if loss is not None and q is not None and _devices(r) == "realistic" and (
            _positive(r)
        ):
            reach[loss] = max(reach.get(loss, 0.0), q)
    if not reach:
        return ""
    groups: dict[float, list[float]] = {}
    for loss, q in sorted(reach.items()):
        groups.setdefault(q, []).append(loss)
    parts = [
        f"QBER ${numeral(100 * q, 3)}\\,\\%$ at "
        + " and ".join(_describe("loss_db", loss) for loss in losses)
        for q, losses in sorted(groups.items(), reverse=True)
    ]
    return (
        "With the realistic devices the last source QBER with a positive key is "
        f"{'; '.join(parts)}: near the threshold the loss matters beyond the "
        "coincidences."
        if len(groups) > 1
        else "With the realistic devices the last source QBER with a positive key "
        f"is {parts[0]}."
    )


# --------------------------------------------------------------------------
# F3 and F3b: rounds and coincidences
# --------------------------------------------------------------------------


def _f3(rows: Sequence[Row]) -> Rendered | None:
    """Key rate against n, every loss in one plot."""

    def x(r: Row) -> float | None:
        return _float(r, "rounds")

    real = _series(rows, "loss_db", x, _rate, "realistic")
    perf = _series(rows, "loss_db", x, _rate, "perfect")
    if not real and not perf:
        return None
    keys = _keys(rows, "loss_db")
    colours = _colours(keys)
    zeros = _zeros(rows, "loss_db", x)
    floor = _log_floor(real, perf)
    xs = [px for s in (real, perf) for _k, pts in s for px, _y in pts]
    xs += [z for zs in zeros.values() for z in zs]
    body: list[str] = []
    for k, (loss, points) in enumerate(real):
        body.append(
            rf"\addplot[{_solid(k, colours[loss])}, forget plot] {_table(points)};"
        )
    body += _perfect_lines(perf, colours)
    fixed = _qber_and_fec(rows)
    if fixed and perf and xs:
        q, f = fixed
        for loss in keys:
            level = ideal_rate(loss, q, f)
            body.append(
                rf"\addplot[{colours[loss]}, {ASYMPTOTE}, forget plot] "
                f"{_table([(min(xs), level), (max(xs), level)])};"
            )
    body += _zero_marks(zeros, colours, floor, STAGGER)
    body += _reference_legend(bool(perf), bool(fixed and perf), bool(zeros))
    ys = [y for s in (real, perf) for _k, pts in s for _x, y in pts]
    nmax = max(xs) * 1.4 if xs else 1.0
    body += _end_labels(
        _ends(real, colours, "loss_db"),
        xmax=nmax,
        ymin=floor / 1.3,
        ymax=max(ys) if ys else 1.0,
        height=HEIGHT,
        log=True,
        heading=_HEADINGS["loss_db"],
    )
    tex = _single(
        "rounds $n$",
        "key rate per round",
        f"xmode=log, xmax={nmax!r}, ymode=log, ymin={floor / 1.3!r}, xmajorgrids, "
        f"ymajorgrids, {_above(4)}, {LEGEND}",
        body,
    )
    caption = _join(
        "Secret key rate per round against the number of rounds $n$, one line per "
        "total channel loss, one colour each, named at the lines' ends. Solid "
        "lines are the realistic "
        "devices; dashed lines of the same colour are the perfect ones, and the "
        "dotted level lines their asymptotic rate as $n \\to \\infty$. Every "
        "line covers the same range of expected coincidences, so a line at more "
        "loss sits at larger $n$, and a realistic line starts at larger $n$ than "
        "its perfect one, which needs fewer rounds for the same coincidences. The "
        "realistic lines level off below the dotted lines: their detectors "
        f"register a share ${numeral(mean_efficiency('realistic') ** 2, 3)}$ of "
        "the pairs, and their errors cost key per coincidence besides.",
        _perfect_note(rows),
        _fixed_sentence(rows, ["rounds", "loss_db", "coincidences", "devices"]),
        _gap_sentence(rows),
        _method(rows),
        _zero_sentence(rows),
        _missing(rows),
    )
    return Rendered(tex, caption)


def _f3b(rows: Sequence[Row]) -> Rendered | None:
    """Key bits per coincidence against coincidences.

    Per coincidence rather than the key length itself: the key length spans
    ten decades, on which the losses' lines are one line; per coincidence they
    sit on a linear axis where a difference between losses is visible. The
    marks are open and shrink from series to series so that coinciding points
    all show.
    """

    def x(r: Row) -> float | None:
        return _float(r, "expected_coincidences")

    real = _series(rows, "loss_db", x, _per_coincidence, "realistic")
    perf = _series(rows, "loss_db", x, _per_coincidence, "perfect")
    if not real and not perf:
        return None
    keys = _keys(rows, "loss_db")
    colours = _colours(keys)
    zeros = _zeros(rows, "loss_db", x)
    body: list[str] = []
    for k, (loss, points) in enumerate(real):
        size = OPEN_SIZES[k % len(OPEN_SIZES)]
        body.append(
            rf"\addplot[{colours[loss]}, solid, line width=0.7pt, "
            rf"mark={OPEN_MARKS[k % len(OPEN_MARKS)]}, mark size={size}pt, "
            rf"mark options={{solid, line width=0.6pt}}, forget plot] {_table(points)};"
        )
    body += _perfect_lines(perf, colours)
    fixed = _qber_and_fec(rows)
    xs = [px for s in (real, perf) for _k, pts in s for px, _y in pts]
    xs += [z for zs in zeros.values() for z in zs]
    if fixed and perf and xs:
        level = ideal_rate_per_coincidence(*fixed)
        body.append(
            rf"\addplot[cqInk, {ASYMPTOTE}, forget plot] "
            f"{_table([(min(xs), level), (max(xs), level)])};"
        )
    body += _zero_marks(zeros, colours, 0.0)
    body += _reference_legend(bool(perf), bool(fixed and perf), bool(zeros))
    ys = [y for s in (real, perf) for _k, pts in s for _x, y in pts]
    cmax = max(xs) * 1.4 if xs else 1.0
    ytop = max(ys) * 1.05 if ys else 1.0
    body += _end_labels(
        _ends(real, colours, "loss_db"),
        xmax=cmax,
        ymin=0.0,
        ymax=ytop,
        height=HEIGHT,
        heading=_HEADINGS["loss_db"],
    )
    tex = _single(
        "expected coincidences",
        "key bits per coincidence",
        f"xmode=log, xmax={cmax!r}, ymin=0, ymax={ytop!r}, xmajorgrids, ymajorgrids, "
        f"{_above(4)}, {LEGEND}",
        body,
    )
    caption = _join(
        "Key length per expected coincidence (a round in which both stations "
        "register a click) against the expected coincidences, one line per total "
        "channel loss, from the same runs as the figure against $n$. Open marks "
        "shrink from line to line, so coinciding points stay visible; where the "
        "lines coincide, the key depends on the loss only through the "
        "coincidences it leaves. Solid lines with open marks are the realistic "
        "devices, dashed lines the perfect ones, and the dotted level line the "
        "perfect devices' key per coincidence as $n \\to \\infty$, the same at "
        "every loss; the perfect lines coincide as well.",
        _per_coincidence_match(rows),
        _asymptote_note(*fixed) if fixed else "",
        _smallest_block(rows),
        _perfect_note(rows),
        _fixed_sentence(rows, ["rounds", "loss_db", "coincidences", "devices"]),
        _gap_sentence(rows),
        _method(rows),
        _zero_sentence(rows, "zero line"),
        _missing(rows),
    )
    return Rendered(tex, caption)


def _per_coincidence_match(rows: Sequence[Row]) -> str:
    """Return the sentence on how close realistic and perfect are per coincidence."""
    by: dict[tuple[float, float, str], float] = {}
    for r in rows:
        loss, c = _float(r, "loss_db"), _float(r, "coincidences")
        y = _per_coincidence(r) if _positive(r) else None
        if loss is not None and c is not None and y:
            by[(loss, c, _devices(r))] = y
    gaps: dict[float, float] = {}
    for (loss, c, d), y in by.items():
        if d == "realistic" and (loss, c, "perfect") in by:
            perf = by[(loss, c, "perfect")]
            gaps[c] = max(gaps.get(c, 0.0), abs(y - perf) / perf)
    blocks = sorted(gaps)
    # The first block from which every larger block agrees within 5 %.
    close = [c for c in blocks if all(gaps[b] <= 0.05 for b in blocks if b >= c)]
    if not close:
        return ""
    start = close[0]
    above = max(gaps[c] for c in blocks if c >= start)
    below = [gaps[c] for c in blocks if c < start]
    return (
        f"From ${_power(start)}$ coincidences on, realistic and perfect devices give "
        rf"the same key per coincidence within ${_percent(100 * above)}\,\%$, "
        "so the devices cost rounds rather than key per coincidence"
        + (
            f"; below, the realistic key per coincidence is lower, by up to "
            rf"${_percent(100 * max(below))}\,\%$."
            if below
            else "."
        )
    )


def _smallest_block(rows: Sequence[Row]) -> str:
    """Return the sentence naming the smallest block with a key, per loss."""
    smallest: dict[float, float] = {}
    for r in rows:
        loss, c = _float(r, "loss_db"), _float(r, "coincidences")
        if loss is None or c is None or _devices(r) != "realistic" or not _positive(r):
            continue
        smallest[loss] = min(smallest.get(loss, c), c)
    if not smallest:
        return ""
    values = set(smallest.values())
    computed = min(
        (c for r in rows if _ok(r) and (c := _float(r, "coincidences")) is not None),
        default=None,
    )
    if computed is not None and values == {computed}:
        return (
            "With the realistic devices the smallest block computed, "
            f"${_power(computed)}$ expected coincidences, already gives a positive "
            "key at every loss; smaller blocks were not computed."
        )
    if len(values) == 1:
        return (
            "With the realistic devices the smallest block with a positive key is "
            f"${_power(values.pop())}$ expected coincidences at every loss."
        )
    parts = ", ".join(
        f"${_power(c)}$ at {_describe('loss_db', loss)}"
        for loss, c in sorted(smallest.items())
    )
    return (
        f"With the realistic devices the smallest block with a positive key is {parts}."
    )


# --------------------------------------------------------------------------
# F4: solvers
# --------------------------------------------------------------------------


#: F4's solver methods in drawing order: auto last, so that where its rate
#: coincides with pairwise's (the final runs: within 1 %) it stays on top.
SOLVER_ORDER: tuple[str, ...] = ("fw", "pairwise", "auto")
#: F4's line styles, one per method, so coinciding lines stay distinguishable.
SOLVER_STYLES: tuple[str, ...] = ("dotted", "dashed", "solid")


def _solver_seconds(rows: Sequence[Row], methods: Sequence[str]) -> str:
    """Return the caption sentence on each method's solve times."""
    parts = []
    for method in methods:
        seconds = [
            s
            for r in rows
            if r.get("method") == method
            and _ok(r)
            and (s := _float(r, "solver_seconds")) is not None
        ]
        if seconds:
            lo, hi = min(seconds), max(seconds)
            span = f"{lo:.0f}" if round(lo) == round(hi) else f"{lo:.0f} to {hi:.0f}"
            parts.append(f"{escape(method)} {span}\\,s")
    return f"Solve times: {'; '.join(parts)}." if parts else ""


def _solver_brackets(rows: Sequence[Row], methods: Sequence[str]) -> str:
    """Return the caption sentence on how far each method left its bracket open.

    The bracket is the distance from the certified bound ``h_lb`` up to the
    solver's own estimate ``h_low``: what a longer solve could still add.
    """
    parts = []
    for method in methods:
        widths = [
            hi - lo
            for r in rows
            if r.get("method") == method
            and _ok(r)
            and (lo := _float(r, "h_lb")) is not None
            and (hi := _float(r, "h_low")) is not None
        ]
        rate = max(
            (y for r in rows if r.get("method") == method and (y := _rate(r))),
            default=0.0,
        )
        if widths:
            parts.append(
                f"{escape(method)} at most ${_sci(max(widths))}$"
                + (
                    ", more than its rate itself: that solve stopped far from "
                    "converged"
                    if max(widths) > rate
                    else ""
                )
            )
    if not parts:
        return ""
    return (
        "Each solver also reports its own estimate of the minimum; the distance "
        "from the certified bound up to it, which a longer solve could still "
        f"gain, is in bits per round: {'; '.join(parts)}."
    )


def _solver_takeaway(rows: Sequence[Row], methods: Sequence[str]) -> str:
    """Return the sentence naming the method with the largest rate at every order.

    Written from the rows: the best method, if one is best at every order, and
    each other method's largest shortfall from it.
    """
    rates: dict[str, dict[float, float]] = {}
    for r in rows:
        a, y = _float(r, "alpha"), _float(r, "key_length")
        if r.get("method") in methods and _ok(r) and a is not None and y is not None:
            rates.setdefault(r["method"], {})[a] = max(y, 0.0)
    alphas = sorted({a for by in rates.values() for a in by})
    if len(rates) < 2 or not alphas:
        return ""
    best = {a: max(by.get(a, 0.0) for by in rates.values()) for a in alphas}
    leaders = [
        m
        for m in methods
        if m in rates and all(rates[m].get(a) == best[a] for a in alphas)
    ]
    if not leaders:
        return ""
    leader = leaders[0]
    parts = []
    for m in methods:
        if m == leader or m not in rates:
            continue
        short = max(
            (best[a] - rates[m].get(a, 0.0)) / best[a] for a in alphas if best[a] > 0
        )
        parts.append(f"{escape(m)} up to ${_percent(100 * short)}\\,\\%$")
    return (
        f"{escape(leader)} certifies the largest rate at every order. Shortfall "
        "from it: "
        f"{'; '.join(parts)} (100\\,\\% is no key at all)."
        if parts
        else ""
    )


def _percent(value: float) -> str:
    """Return a percentage with two significant digits, never in e-notation."""
    return f"{value:.0f}" if abs(value) >= 10 else numeral(float(f"{value:.2g}"), 6)


def _sci(value: float) -> str:
    """Return ``value`` with two significant digits, as a power of ten if small."""
    if value == 0:
        return "0"
    exponent = _math.floor(_math.log10(abs(value)))
    if -3 <= exponent <= 3:
        return numeral(float(f"{value:.2g}"), 6)
    mantissa = float(f"{value / 10**exponent:.2g}")
    return rf"{numeral(mantissa, 3)} \times 10^{{{exponent}}}"


def _f4(rows: Sequence[Row]) -> Rendered | None:
    """Key rate per method against alpha, and each method's solve time.

    The left panel is what a user gets, the key rate per round each method
    certifies at each order, and the right panel is what it costs, the solve
    time of each point.
    """
    present = {r["method"] for r in rows if r.get("method") and _ok(r)}
    methods = [m for m in SOLVER_ORDER if m in present] + sorted(
        present - set(SOLVER_ORDER)
    )
    if not any(_positive(r) for r in rows if r.get("method") in methods):
        return None
    colours = series(len(methods))
    rate: list[str] = []
    time: list[str] = []
    zeros: dict[float, list[float]] = {}
    for k, method in enumerate(methods):
        mine = [r for r in rows if r.get("method") == method and _ok(r)]
        for r in mine:
            a = _float(r, "alpha")
            if _zero(r) and a is not None:
                zeros.setdefault(float(k), []).append(a - 1)
        points = sorted(
            (a - 1, y)
            for r in mine
            if _positive(r)
            and (a := _float(r, "alpha")) is not None
            and (y := _rate(r)) is not None
        )
        style = _solid(k, colours[k]).replace(
            "solid", SOLVER_STYLES[k % len(SOLVER_STYLES)], 1
        )
        if points:
            rate.append(rf"\addplot[{style}] {_table(points)};")
            rate.append(rf"\addlegendentry{{{escape(method)}}}")
        # One mark per order, each order a little higher, so equal times
        # stay four marks rather than one.
        timed = sorted(
            (a, s)
            for r in mine
            if (a := _float(r, "alpha")) is not None
            and (s := _float(r, "solver_seconds")) is not None
        )
        seconds = " ".join(
            f"({s!r},{k + 0.12 * (j - (len(timed) - 1) / 2):.3f})"
            for j, (_a, s) in enumerate(timed)
        )
        if seconds:
            time.append(
                rf"\addplot[only marks, {colours[k]}, "
                rf"mark={OPEN_MARKS[k % len(OPEN_MARKS)]}, mark size={MARK_SIZE}, "
                rf"mark options={{line width=0.8pt}}] coordinates {{{seconds}}};"
            )
    rate += _zero_marks(zeros, dict(enumerate(colours)), 0.0)
    if zeros:
        rate += _reference_legend(False, False, True)
    ticks = ",".join(str(k) for k in range(len(methods)))
    names = ",".join("{" + escape(m) + "}" for m in methods)
    orders = sorted(
        {a - 1 for r in rows if _ok(r) and (a := _float(r, "alpha")) is not None}
    )
    xticks = (
        f"xtick={{{','.join(repr(o) for o in orders)}}}, "
        f"xticklabels={{{','.join(f'{o:.3g}' for o in orders)}}}, "
        "x tick label style={/pgf/number format/fixed}, "
        if orders
        else ""
    )
    tex = _panels(
        [
            Panel(
                r"R\'enyi order $\alpha - 1$",
                "key rate per round",
                f"width={WIDTH * 0.7}cm, height={HEIGHT}cm, xmode=log, ymin=0, "
                f"{xticks}"
                f"xmajorgrids, ymajorgrids, {_above(len(methods) + bool(zeros))}, "
                f"{_PLAIN_Y.format(precision=3)}, "
                f"{LEGEND}",
                rate,
            ),
            Panel(
                "solve time (s)",
                "",
                f"width={WIDTH * 0.32}cm, height={HEIGHT}cm, xmode=log, "
                f"xmin=3, xmax=3000, ymin=-0.6, ymax={len(methods) - 0.4}, "
                f"ytick={{{ticks}}}, yticklabels={{{names}}}, "
                "ytick style={draw=none}, "
                "xmajorgrids",
                time,
                place="right",
            ),
        ]
    )
    caption = _join(
        r"The solver methods compared at one point, at four fixed R\'enyi orders "
        r"$\alpha$. fw is the Frank--Wolfe method and pairwise its variant with "
        "pairwise steps, both stopped here at their limit of 2000 iterations; auto "
        "is the engine's default, which runs several methods in turn (one of them "
        "with a conic solver) and keeps the best certified bound. Left: the key "
        "rate per round each method certifies, one line per method. Right: how "
        "long each solve took, one open mark per order, stacked from the smallest "
        r"order up.",
        _solver_takeaway(rows, methods),
        _solver_seconds(rows, methods),
        _solver_brackets(rows, methods),
        _fixed_sentence(rows, ["method", "alpha"]),
        _zero_sentence(rows),
        _missing(rows),
    )
    return Rendered(tex, caption)


# --------------------------------------------------------------------------
# F5: encoded (WPFSS) against licensed (FSS)
# --------------------------------------------------------------------------

#: Terminations at which the solver stopped on its budget, not on its gap:
#: the key length is still a certified lower bound, only a looser one.
_STOPPED_ON_BUDGET = frozenset({"budget_exhausted", "max_iterations"})
#: The routes as the literature names them.
ROUTE_WORDS: Mapping[str, str] = {
    "encoded": "encoded (WPFSS)",
    "licensed": "licensed (FSS)",
}
_ROUTE_CITES: Mapping[str, str] = {
    "encoded": (
        r"the weight-preserving flag-state squasher \parencite{tupkary2026decoy}"
    ),
    "licensed": (
        r"the flag-state squasher \parencite{zhang2021security} imposed as a "
        "constraint list"
    ),
}


#: The device sets in panel order: the realistic one first.
DEVICE_ORDER: tuple[str, ...] = ("realistic", "perfect")
_DEVICE_WORDS: Mapping[str, str] = {
    "realistic": "realistic devices",
    "perfect": "perfect devices",
}

Cell = tuple[str, int, str]


def _route_cells(rows: Sequence[Row]) -> dict[Cell, Row]:
    """Return the route rows keyed by device set, cutoff and route."""
    cells: dict[Cell, Row] = {}
    for r in rows:
        cutoff = _float(r, "cutoff")
        if cutoff is not None and r.get("route") in ROUTE_WORDS:
            cells[(_devices(r), int(cutoff), r["route"])] = r
    return cells


def _route_devices(cells: Mapping[Cell, Row]) -> list[str]:
    present = {d for d, _c, _r in cells}
    return [d for d in DEVICE_ORDER if d in present] + sorted(
        present - set(DEVICE_ORDER)
    )


def _f5(rows: Sequence[Row]) -> Rendered | None:
    """Key rate against photon cutoff, per route, a panel per device set.

    Rate per round, as every other figure, and both device sets, a panel
    each, each panel on its own y range: the routes differ by about a percent, which
    one shared axis would flatten. The ranges span the same fraction of each
    panel's rate, so the same relative change looks the same in both panels:
    scaled separately, the ideal-detector panel blew differences of a part in a million
    up to full height (the second preview).
    """
    cells = _route_cells(rows)
    if not any(_positive(r) for r in cells.values()):
        return None
    cutoffs = sorted({c for _d, c, _r in cells})
    colours = dict(zip(ROUTE_WORDS, series(2), strict=True))
    ticks = ",".join(str(c) for c in cutoffs)
    reference = {
        d: max(
            (
                y
                for (dd, _c, route), r in cells.items()
                if dd == d and route == "encoded" and _positive(r) and (y := _rate(r))
            ),
            default=0.0,
        )
        for d in _route_devices(cells)
    }
    # Each mark and the top of its gap bar.
    changes = [
        v
        for (d, _c, _route), r in cells.items()
        if reference.get(d) and _positive(r) and (y := _rate(r))
        for v in (y / reference[d] - 1, (y + _rate_gap(r)) / reference[d] - 1)
    ] or [0.0]
    low, high = min(*changes, 0.0), max(*changes, 0.0)
    pad = 0.15 * (high - low) or 1e-3
    panels: list[Panel] = []
    budget = False
    for d in _route_devices(cells):
        ref = reference[d] or 1.0
        yrange = f"ymin={ref * (1 + low - pad)!r}, ymax={ref * (1 + high + pad)!r}, "
        body: list[str] = []
        for k, route in enumerate(ROUTE_WORDS):
            points = [
                (c, y)
                for c in cutoffs
                if (r := cells.get((d, c, route))) is not None
                and _positive(r)
                and (y := _rate(r)) is not None
            ]
            if not points:
                continue
            style = "solid" if k == 0 else "dashed"
            bars = "\n".join(
                f"{c!r} {y!r} {_rate_gap(cells[(d, c, route)])!r}" for c, y in points
            )
            body.append(
                rf"\addplot[{colours[route]}, {style}, {LINE}, "
                rf"mark={MARKS[k]}, mark size={MARK_SIZE}, mark options={{solid}}, "
                r"error bars/.cd, y dir=plus, y explicit, "
                r"error bar style={line width=0.8pt, solid}, "
                r"error mark options={rotate=90, mark size=2.5pt, line width=0.8pt}] "
                f"table[row sep=newline, y error plus=e] {{\nx y e\n{bars}\n}};"
            )
            if not panels:
                body.append(rf"\addlegendentry{{{ROUTE_WORDS[route]}}}")
            stopped = [
                (c, y)
                for c, y in points
                if cells[(d, c, route)].get("termination") in _STOPPED_ON_BUDGET
            ]
            if stopped:
                budget = True
                coords = " ".join(f"({c!r},{y!r})" for c, y in stopped)
                body.append(
                    rf"\addplot[only marks, mark=o, mark size=4.8pt, "
                    rf"mark options={{line width=0.9pt}}, "
                    rf"{colours[route]}, forget plot] coordinates {{{coords}}};"
                )
        if not panels and budget:
            body += [
                r"\addlegendimage{only marks, mark=o, mark size=4.8pt, "
                r"mark options={line width=0.9pt}, cqMuted}",
                r"\addlegendentry{stopped on its budget}",
            ]
        panels.append(
            Panel(
                "photon cutoff",
                "key rate per round" if not panels else "",
                f"width={WIDTH * 0.48}cm, height={HEIGHT * 0.9}cm, "
                f"title={{{_DEVICE_WORDS.get(d, escape(d))}}}, "
                f"title style={{font={PLOT_LABEL}}}, xtick={{{ticks}}}, "
                f"xmin={cutoffs[0] - 0.3}, xmax={cutoffs[-1] + 0.3}, {yrange}"
                "ymajorgrids, "
                # Rates that differ in the fourth digit: plain decimals, so
                # neighbouring ticks differ.
                + _PLAIN_Y.format(precision=4)
                + (
                    f", legend to name=routeslegend, legend columns=3, {LEGEND}"
                    if not panels
                    else ""
                ),
                body,
                place="right",
            )
        )
    tex = _panels(panels).replace(
        r"\end{tikzpicture}",
        r"\node[anchor=south] at ($(p0.north west)!0.5!(p"
        + str(len(panels) - 1)
        + r".north east)+(0,0.75cm)$) {\pgfplotslegendfromname{routeslegend}};"
        "\n"
        r"\end{tikzpicture}",
    )
    caption = _join(
        "Key rate per round against the photon cutoff of the receiver model "
        "(the largest photon number the receiver is modelled at exactly), on two "
        "routes. On the encoded route the squasher, "
        f"{_ROUTE_CITES['encoded']}, is built into the receiver model; on the "
        f"licensed route, {_ROUTE_CITES['licensed']}, its conditions are imposed "
        "as extra constraints of the optimisation. Both account for photon "
        "numbers above the cutoff, so a larger cutoff models more of the receiver "
        "exactly but is not needed for the bound to hold. "
        + (
            "One panel per device set; both span the same fraction of their rate."
            if len(panels) > 1
            else ""
        ),
        _route_takeaway(cells),
        _cutoff_spread(cells),
        "The bar above each mark spans the convergence gap: closing it could "
        "raise the rate by at most the bar; where no bar shows, the gap is "
        "smaller than the mark.",
        _gap_sentence(list(cells.values())),
        "A ring marks a solve that stopped on its budget rather than its gap: the "
        "rate is still a certified lower bound, only a looser one, so part of the "
        "difference between the routes may be the solver's."
        if budget
        else "",
        "The accompanying table gives the key lengths in bits.",
        _rounds_rule(rows),
        _fixed_sentence(rows, ["cutoff", "route", "devices", "rounds"]),
        _method(rows),
        _missing(rows),
    )
    return Rendered(tex, caption)


def _rate_gap(r: Row) -> float:
    """Return the convergence gap per round (:func:`_gap`), 0 where unknown.

    The key length is linear in the entropy bound at a fixed alpha, so closing
    the gap could raise the rate per round by at most this much.
    """
    return _gap(r) or 0.0


def _route_takeaway(cells: Mapping[Cell, Row]) -> str:
    """Return the sentence on how far licensed falls below encoded, per device set."""
    parts = []
    for d in _route_devices(cells):
        gaps = [
            100 * (e - lic) / e
            for (dd, c, route), r in cells.items()
            if dd == d
            and route == "encoded"
            and (e := _rate(r) or 0.0) > 0
            and (other := cells.get((d, c, "licensed"))) is not None
            and _ok(other)
            and (lic := _rate(other)) is not None
        ]
        if gaps:
            lo, hi = min(gaps), max(gaps)
            span = (
                f"${numeral(lo, 2)}\\,\\%$"
                if round(lo, 1) == round(hi, 1)
                else f"${numeral(lo, 2)}$ to ${numeral(hi, 2)}\\,\\%$"
            )
            parts.append(f"{span} with {_DEVICE_WORDS.get(d, escape(d))}")
    if not parts:
        return ""
    return f"The licensed route lies below the encoded one by {' and '.join(parts)}."


def _cutoff_spread(cells: Mapping[Cell, Row]) -> str:
    """Return the sentence on how much the encoded route varies with the cutoff."""
    parts = []
    for d in _route_devices(cells):
        ys = [
            y
            for (dd, _c, route), r in sorted(cells.items())
            if dd == d and route == "encoded" and _positive(r) and (y := _rate(r))
        ]
        if len(ys) > 1:
            spread = 100 * (max(ys) - min(ys)) / max(ys)
            parts.append(
                f"${_percent(spread)}\\,\\%$ with {_DEVICE_WORDS.get(d, escape(d))}"
            )
    if not parts:
        return ""
    return (
        "Across the cutoffs the encoded route varies by "
        f"{' and '.join(parts)}, without a trend."
    )


def _route_rounds(cells: Mapping[Cell, Row]) -> str:
    """Return the sentence giving n and the expected coincidences per device set."""
    parts = []
    for d in _route_devices(cells):
        row = next(
            (r for (dd, _c, _r), r in sorted(cells.items()) if dd == d and _ok(r)),
            None,
        )
        n = _float(row, "rounds") if row else None
        c = _float(row, "expected_coincidences") if row else None
        if n and c:
            parts.append(
                f"{_DEVICE_WORDS.get(d, escape(d))} $n = {_power(n)}$ with "
                f"${c / 1e6:.3f} \\times 10^{{6}}$ expected coincidences"
            )
    if len(parts) < 2:
        return ""
    return (
        f"Rounds: {'; '.join(parts)} (n is rounded to two digits). So the "
        "realistic lengths in bits come out above the perfect ones although their rate "
        "per round is lower; compare the routes within a device set."
    )


def _bits(value: float) -> str:
    """Return an integer bit count with thin spaces between thousands."""
    return f"{round(value):,}".replace(",", r"\,")


def _f5t(rows: Sequence[Row]) -> Rendered | None:
    """Tabulate F5 in bits: the reported key length and the snapped bound's.

    Since the direct route the key length is the bound on the receiver's
    reference declaration; the record keeps the snapped run's own bound beside
    it as a diagnostic.
    """
    cells = _route_cells(rows)
    if not any(_positive(r) for r in cells.values()):
        return None
    cutoffs = sorted({c for _d, c, _r in cells})
    devices = _route_devices(cells)
    budget = dash = False
    lines = [
        r"\begin{tabular}{llrrrrrr}",
        r"\toprule",
        r" & & \multicolumn{3}{c}{"
        + ROUTE_WORDS["encoded"]
        + r"} & \multicolumn{3}{c}{"
        + ROUTE_WORDS["licensed"]
        + r"} \\",
        r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
        r"devices & cutoff & reported & snapped & gap & reported & snapped & gap \\",
        r"\midrule",
    ]
    for i, d in enumerate(devices):
        if i:
            lines.append(r"\addlinespace")
        for j, cutoff in enumerate(cutoffs):
            first = _DEVICE_WORDS.get(d, escape(d)) if j == 0 else ""
            entries = [first, f"${cutoff}$"]
            for route in ROUTE_WORDS:
                cell = cells.get((d, cutoff, route))
                if cell is None or not _ok(cell):
                    entries += ["--", "--", "--"]
                    dash = True
                    continue
                length = _float(cell, "key_length")
                mark = ""
                if cell.get("termination") in _STOPPED_ON_BUDGET:
                    mark, budget = r"$^\dagger$", True
                entries.append(f"${_bits(length or 0.0)}${mark}")
                snapped = _float(cell, "snapped_key_length")
                if snapped is None:
                    entries.append("--")
                    dash = True
                else:
                    entries.append(f"${_bits(snapped)}$")
                gap = _relative_gap(cell)
                entries.append(
                    "--" if gap is None else f"${_percent(100 * gap)}\\,\\%$"
                )
            lines.append(" & ".join(entries) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    run = [r for r in cells.values() if _ok(r)]
    counted = sum(1 for r in run if r.get("bracket_status") == "counted")
    resting = sum(1 for r in run if r.get("rests_on_a_snap") == "True")
    caption = _join(
        "Key length in bits per photon cutoff of the receiver model, on the "
        "encoded (WPFSS) and the licensed (FSS) route"
        + (", for each device set. " if len(devices) > 1 else ". ")
        + "The solver works on a copy of the receiver model rounded to exact "
        "numbers (snapped). \\emph{Reported} is the key length of the run, the "
        "bound evaluated again on the receiver model as declared; "
        "\\emph{snapped} is the bound on the rounded copy, kept for comparison; "
        "\\emph{gap} is the convergence gap, how far the bound lies below the "
        "objective of the solver's point it comes from, relative to that "
        "objective: closing it could raise the bound by at most this much.",
        _route_rounds(cells),
        (
            f"In all {len(run)} runs the reported length is the bound on the "
            "declared model, so no length rests on the rounded copy; the two "
            "values differ by a few hundred bits at most."
            if counted == len(run) and not resting
            else f"{counted} of the {len(run)} runs report the bound on the "
            f"declared model; {resting} rest{'s' if resting == 1 else ''} on the "
            "rounded copy."
        )
        if run
        else "",
        r"A dagger marks a solve that stopped on its budget rather than its gap."
        if budget
        else "",
        "A dash marks a value the run does not have." if dash else "",
        _rounds_rule(rows),
        _fixed_sentence(rows, ["cutoff", "route", "devices", "rounds"]),
        _method(rows),
    )
    return Rendered("\n".join(lines), caption)


# --------------------------------------------------------------------------
# F6: the imperfection ladder
# --------------------------------------------------------------------------

#: The ladder's rungs in words, each adding one effect to the rungs above.
RUNG_WORDS: Mapping[str, str] = {
    "perfect": "perfect devices",
    "efficiency": "+ detector efficiency",
    "dark": "+ dark counts",
    "mismatch": "+ efficiency mismatch",
    "basis-split": "+ basis-choice bias",
    "extinction": "+ PBS leaks",
    "misalignment": "+ misaligned analyser (Bob)",
    "visibility": "+ source visibility",
}


#: Each rung's value as typeset; the summary's ``value`` column says the same
#: in plain text, and a rung missing here falls back to it.
RUNG_VALUES: Mapping[str, str] = {
    "efficiency": r"$\eta = 0.8$",
    "dark": r"$p_{\mathrm{dc}} = 1.3\times10^{-7}$",
    "mismatch": r"$\eta_{\mathrm{V,A}} = \tfrac{54}{59}\,\eta_{\mathrm{H,D}}$",
    "basis-split": r"$T:R = 56:44$",
    "extinction": (
        r"$\epsilon_{\mathrm{t}} = 10^{-3}$, $\epsilon_{\mathrm{r}} = 10^{-2}$"
    ),
    "misalignment": r"$\sin^2\theta = 0.004$",
    "visibility": r"$V = 0.98$",
}


def _sifting() -> float:
    """Return the chance that both stations' passive splits pick the same basis."""
    t = float(REALISTIC["basis_split"])
    return t * t + (1 - t) * (1 - t)


def _change(value: float, previous: float) -> str:
    """Return the relative change from ``previous`` as a signed percentage."""
    change = 100 * (value - previous) / previous
    digits = 2 if abs(change) < 1 else 1
    return rf"${change:+.{digits}f}\,\%$"


#: The vertical step between the ladder's block labels (pt).
LADDER_LABEL_STEP = 7.5
#: A ladder block: whether it is the large reference, its value and the
#: column the value is from (``coincidences``, or ``rounds`` for the reference
#: and for a summary written before the blocks were labelled).
Block = tuple[bool, float, str]


def _ladder_block(r: Row) -> Block | None:
    """Return a ladder row's block.

    The sweep labels each block by its realistic expected coincidences and the
    reference by its rounds alone (an empty ``coincidences``); a summary
    without the column (written before the blocks were) is grouped by rounds,
    its ``LADDER_REFERENCE_ROUNDS`` block the reference.
    """
    n = _float(r, "rounds")
    if "coincidences" in r:
        c = _float(r, "coincidences")
        if c is not None:
            return (False, c, "coincidences")
        return (True, n, "rounds") if n is not None else None
    if n is None:
        return None
    return (n >= LADDER_REFERENCE_ROUNDS, n, "rounds")


def _block_words(block: Block, short: bool = False) -> str:
    """Name a ladder block: its coincidences, or its n."""
    _reference, value, column = block
    if short:
        text = _power_text(value)
        return text if column == "coincidences" else rf"\textit{{n}}\,=\,{text}"
    return _describe(column, value)


def _f6(rows: Sequence[Row]) -> Rendered | None:
    """Draw grouped bars per rung, one per block, over a table.

    One bar per block of expected coincidences, in the series colours, and the
    large reference block in muted grey; the blocks are named at the top
    rung's bars. Rungs are cumulative, so the table's change is from the rung
    above, not from the perfect devices.
    """
    by_block: dict[Block, dict[int, float]] = {}
    rung_rows: dict[int, Row] = {}
    for r in rows:
        rung, block = _float(r, "rung"), _ladder_block(r)
        if rung is None or block is None:
            continue
        rung_rows.setdefault(int(rung), r)
        if _positive(r) and (rate := _rate(r)) is not None:
            by_block.setdefault(block, {})[int(rung)] = rate
    if not by_block:
        return None
    blocks = sorted(by_block)
    rungs = sorted(rung_rows)
    colours = iter(series(sum(1 for reference, _v, _c in blocks if not reference)))
    fill = {b: ("cqReference" if b[0] else next(colours)) for b in blocks}
    width, step = 3.2, 3.6
    body: list[str] = []
    for k, block in enumerate(blocks):
        shift = (k - (len(blocks) - 1) / 2) * step
        coords = " ".join(
            f"({rate!r},{-rung})" for rung, rate in sorted(by_block[block].items())
        )
        body.append(
            rf"\addplot[xbar, bar width={width}pt, bar shift={-shift:.2f}pt, "
            rf"fill={fill[block]}, draw=none] coordinates {{{coords}}};"
        )
    # The blocks named at the top rung: a column right of its longest bar,
    # each label joined to its own bar's end, in the bars' order.
    tops = {b: by_block[b][rungs[0]] for b in blocks if rungs[0] in by_block[b]}
    if tops:
        column = max(tops.values())
        for k, block in enumerate(blocks):
            if block not in tops:
                continue
            bar = -(k - (len(blocks) - 1) / 2) * step
            label = ((len(blocks) - 1) / 2 - k) * LADDER_LABEL_STEP
            body.append(
                rf"\draw[{fill[block]}, line width=0.5pt] ([yshift={bar:.2f}pt]axis cs:"
                rf"{tops[block]!r},{-rungs[0]}) -- ([xshift=6pt, yshift={label:.2f}pt]"
                rf"axis cs:{column!r},{-rungs[0]});"
            )
            body.append(
                rf"\node[anchor=west, inner sep=1pt, font={SMALL}\bfseries, "
                rf"text={fill[block]}] at ([xshift=7pt, yshift={label:.2f}pt]axis cs:"
                rf"{column!r},{-rungs[0]}) {{{_block_words(block, short=True)}}};"
            )
    ticks = ",".join(str(-k) for k in rungs)
    words = ",".join(
        "{" + escape(RUNG_WORDS.get(rung_rows[k].get("effect", ""), "")) + "}"
        for k in rungs
    )
    xmax = max(rate for rates in by_block.values() for rate in rates.values()) * 1.25
    plot = _single(
        "key rate per round",
        "",
        f"xmin=0, xmax={xmax!r}, ymin={-rungs[-1] - 0.7}, ymax=0.7, "
        f"ytick={{{ticks}}}, yticklabels={{{words}}}, y tick label style="
        f"{{font={PLOT}, align=right}}, ytick style={{draw=none}}, xmajorgrids, "
        "scaled x ticks=false, x tick label style={/pgf/number format/fixed}",
        body,
    )
    header = " & ".join(
        ["", "value", "source", *(_block_words(b, short=True) for b in blocks)]
    )
    table = [
        r"\par\medskip",
        rf"{{{MAIN}\setlength{{\tabcolsep}}{{4pt}}",
        r"\begin{tabular}{lll" + "r" * len(blocks) + "}",
        r"\toprule",
        r" & & & \multicolumn{"
        + str(len(blocks))
        + r"}{c}{change from the row above} \\",
        r"\cmidrule(lr){4-" + str(3 + len(blocks)) + "}",
        header + r" \\",
        r"\midrule",
    ]
    for k in rungs:
        r = rung_rows[k]
        source = r.get("source") or ""
        cells = [
            escape(RUNG_WORDS.get(r.get("effect", ""), "")),
            RUNG_VALUES.get(r.get("effect", ""), escape(r.get("value") or "")),
            rf"\cite{{{source}}}" if source else "",
        ]
        for block in blocks:
            rate, previous = by_block[block].get(k), by_block[block].get(k - 1)
            if rate is None:
                cells.append("--")
            elif previous is None:
                cells.append("reference" if k == rungs[0] else "--")
            else:
                cells.append(_change(rate, previous))
        table.append(" & ".join(cells) + r" \\")
    table += [r"\bottomrule", r"\end{tabular}}", ""]
    caption = _join(
        "Secret key rate per round as device imperfections are added one at a "
        "time, top to bottom, one bar per block, named at the top row's bars; "
        "each row keeps every imperfection above it. "
        + _ladder_blocks_sentence(blocks)
        + " The table gives each row's value, its "
        "source and its change from the row above; that change depends on the "
        "order of the rows, since each is charged against the key left by the "
        "rows above it. The basis-choice bias gains key because both stations "
        "split at the same ratio: a round survives sifting when both choose the "
        f"same basis, with probability ${numeral(_sifting(), 4)}$ instead of "
        "$0.5$. The misalignment is on Bob's analyser only: the same real "
        r"polarisation rotation at both stations leaves the source state "
        r"$\lvert\Phi^+\rangle$, and so the key, unchanged.",
        "Source visibility comes first, so every later row is added to a "
        "source that already makes errors. Added to error-free devices, an "
        "imperfection that first makes errors possible would also pay the "
        "acceptance test's statistical margin on them, which at small $n$ "
        "outweighs the effect itself."
        if [rung_rows[k].get("effect") for k in rungs[:2]] == ["perfect", "visibility"]
        else "",
        _fixed_sentence(
            rows, ["rung", "effect", "value", "source", "rounds", "coincidences"]
        ),
        _method(rows),
        _zero_sentence(rows),
        _missing(rows),
    )
    return Rendered(plot + "\n".join(table), caption)


def _ladder_blocks_sentence(blocks: Sequence[Block]) -> str:
    """Return the caption sentence naming the ladder's blocks."""
    counted = [(v, c) for reference, v, c in blocks if not reference]
    references = [v for reference, v, _c in blocks if reference]
    parts = []
    if counted and all(c == "coincidences" for _v, c in counted):
        parts.append(
            "The coloured bars are blocks of "
            + ", ".join(f"${_power(v)}$" for v, _c in counted)
            + " expected coincidences with the realistic devices at 0 dB, each "
            "at the same $n$ on every row"
        )
    elif counted:
        parts.append(
            "The coloured bars are blocks of "
            + ", ".join(_describe("rounds", v) for v, _c in counted)
            + " rounds"
        )
    if references:
        parts.append(
            "the grey bar is a large reference block, "
            + ", ".join(_describe("rounds", n) for n in references)
        )
    return ("; ".join(parts) + ".") if parts else ""


# --------------------------------------------------------------------------
# F7: alpha
# --------------------------------------------------------------------------


def _f7(rows: Sequence[Row]) -> Rendered | None:
    by = "coincidences" if any(r.get("coincidences") for r in rows) else "rounds"
    best: dict[float, float] = {}
    for r in rows:
        key, length = _float(r, by), _float(r, "key_length")
        if key is not None and length is not None and _positive(r):
            best[key] = max(best.get(key, 0.0), length)
    lines = _series(
        rows,
        by,
        lambda r: (a - 1) if (a := _float(r, "alpha")) is not None else None,
        lambda r: (
            (length / best[key])
            if (length := _float(r, "key_length")) is not None
            and (key := _float(r, by)) in best
            else None
        ),
    )
    if not lines:
        return None
    colours = series(len(lines))
    body: list[str] = []
    for k, (_value, points) in enumerate(lines):
        body.append(
            rf"\addplot[{_solid(k, colours[k])}, forget plot] {_table(points)};"
        )
    # The maxima after every line, large and on a white disc, so no line or
    # mark hides them (the readers: "only the blue star is visible").
    for k, (_value, points) in enumerate(lines):
        top = max(points, key=lambda p: p[1])
        at = f"({top[0]!r},{top[1]!r})"
        body.append(
            rf"\addplot[only marks, mark=*, mark size=5pt, white, forget plot] "
            f"coordinates {{{at}}};"
        )
        body.append(
            rf"\addplot[only marks, mark=star, mark size=5pt, line width=1.2pt, "
            rf"{colours[k]}, forget plot] coordinates {{{at}}};"
        )
    amax = max(x for _v, points in lines for x, _y in points) * 1.5
    body += _end_labels(
        _ends(lines, {v: colours[k] for k, (v, _p) in enumerate(lines)}, by),
        xmax=amax,
        ymin=0.0,
        ymax=1.08,
        height=HEIGHT,
        heading=_HEADINGS.get(by, ""),
    )
    tex = _single(
        r"$\alpha - 1$",
        "key length relative to its maximum",
        f"xmode=log, xmax={amax!r}, ymin=0, ymax=1.08, xmajorgrids, ymajorgrids",
        body,
    )
    caption = _join(
        r"Key length against the R\'enyi order $\alpha$, relative to the largest "
        "key length of the same block, one line per block, named at its end; "
        "the star marks each line's best computed order.",
        _alpha_takeaway(lines),
        _rounds_rule(rows),
        _fixed_sentence(rows, ["alpha", "rounds", "coincidences"]),
        _method(rows),
        _missing(rows),
    )
    return Rendered(tex, caption)


def _alpha_takeaway(lines: Series) -> str:
    """Return the sentence giving each block's best order of the grid."""
    bests = [(value, max(points, key=lambda p: p[1])[0]) for value, points in lines]
    if not bests:
        return ""
    parts = ", ".join(f"${_sci(a)}$ for ${_power(v)}$" for v, a in bests)
    shrinks = all(a > b for (_v, a), (_w, b) in pairwise(bests))
    lead = (
        r"The best $\alpha - 1$ shrinks as the block grows"
        if shrinks and len(bests) > 1
        else r"The best $\alpha - 1$ is"
    )
    return f"{lead}: {parts}."


_RENDER: Mapping[str, Callable[[Sequence[Row]], Rendered | None]] = {
    "F1": _f1,
    "F2": _f2,
    "F3": _f3,
    "F3b": _f3b,
    "F4": _f4,
    "F5": _f5,
    "F5t": _f5t,
    "F6": _f6,
    "F7": _f7,
}


def render_keyrate(
    sweeps: Mapping[str, Sequence[Row]],
) -> tuple[dict[str, tuple[Rendered, list[str]]], list[str]]:
    """Return the drawable figures and a message for each figure without data.

    The figures are keyed by file name, each with its pins.
    """
    figures: dict[str, tuple[Rendered, list[str]]] = {}
    skipped: list[str] = []
    for figure in FIGURES:
        rows = sweeps.get(figure.sweep)
        rendered = _RENDER[figure.draw or figure.figure](rows) if rows else None
        if rendered is not None and rows and _oracle_note(rows):
            rendered = Rendered(
                rendered.body, f"{rendered.caption} {_oracle_note(rows)}"
            )
        if rendered is None:
            skipped.append(
                f"{figure.figure} ({figure.sweep}): no drawable data, skipped"
            )
            continue
        if figure.note:
            rendered = Rendered(
                rendered.body, f"{rendered.caption} {figure.note}".strip()
            )
        commits = sorted(
            {r.get("git_commit", "") for r in rows or [] if r.get("git_commit")}
        )
        dirty = any(r.get("git_dirty") == "True" for r in rows or [])
        pins = [f"engine {c[:8]}" for c in commits] + (
            ["some points from an uncommitted tree"] if dirty else []
        )
        figures[figure.name] = (rendered, pins)
    return figures, skipped
