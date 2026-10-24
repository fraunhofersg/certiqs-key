"""The honest statistics against the acceptance box, from ``record-extract.json``.

The interactive statistics inspector draws one
row per acceptance outcome on a shared axis: the honest value as a dot, the
emitted box ``[q-, q+]`` as a band. The figure keeps that form and adds one
thing paper needs. At ``n = 1e8`` rounds the box is a few ``1e-4`` wide, which
on a probability axis running to about one half is thinner than a line; a band
no reader can see shows nothing. So there are two panels on the same rows,
each with a short title instead of a shared legend:

* left, "honest p": the probability itself, on a logarithmic axis when the
  plotted values span more than one decade, a linear one otherwise;
* right, "acceptance box around p": ``q - p`` in units of ``1e-4``, where the
  box's width -- the finite-size price of the acceptance test -- is visible and
  comparable across rows.

The honest value is a filled dot, the box a band with end ticks: they differ in
mark as well as colour. A thin rule separates groups of outcomes, a group being
the outcomes whose labels share the text before the first ``:`` (the key-round
outcomes from the test outcomes, here).

WHY THE LOG AXIS COMES SO EARLY
===============================
The interactive inspector switches to a log axis only beyond three decades. On
paper that is too late: at 1.75 decades the test outcomes (around ``1e-2``)
crowd against zero beside the key-generation outcome (``0.44``) and cannot be
told apart. The rule here is: log as soon as the values span more
than one decade (:data:`LOG_DECADES`), where a linear axis starts to crush the
small ones. On a log axis the panel runs from a factor :data:`LOG_MARGIN` below
the smallest plotted value to as far above the largest.

Only outcomes in the support are drawn: an outcome whose honest probability is
zero and whose box is ``[0, 0]`` has nothing to plot. How many there are, and
the run's round count, endpoint rule and completeness budget, are in the caption.
"""

from __future__ import annotations

import math as _math
from collections.abc import Mapping, Sequence
from typing import Any

from runs.bbm92_study.views.tex import MAIN, SMALL, Rendered, escape, numeral, rational

__all__ = ["LOG_DECADES", "render_statistics", "use_log_axis"]

LOG_DECADES = 1.0
"""Log probability axis beyond this many decades."""

ROW_HEIGHT = 0.32
LOG_MARGIN = 1.6
"""On a log axis, the room left and right of the plotted values, as a factor."""
OFFSET_UNIT = 1e-4
LEFT_WIDTH = 4.8
RIGHT_WIDTH = 4.4
BAND = "cqData!40, line width=3.4pt"
TICK = "cqData, line width=0.6pt"
DOT = "only marks, mark=*, mark size=1.4pt, cqInk"


def use_log_axis(values: Sequence[float]) -> bool:
    """Return whether positive ``values`` span more than :data:`LOG_DECADES`."""
    positive = [v for v in values if v > 0]
    if len(positive) < 2:
        return False
    return _math.log10(max(positive) / min(positive)) > LOG_DECADES


def _plot(style: str, points: Sequence[tuple[float, float]]) -> str:
    coordinates = " ".join(f"({x!r},{y!r})" for x, y in points)
    return rf"\addplot[{style}] coordinates {{{coordinates}}};"


def _support(
    extract: Mapping[str, Any],
) -> tuple[list[tuple[str, float, float, float]], int]:
    """Return the rows to draw, ``(label, p, q-, q+)``, and how many are empty."""
    rows: list[tuple[str, float, float, float]] = []
    empty = 0
    for o in extract["outcomes"]:
        p = float(rational(o["honest"]))
        lo, hi = float(o["box_lower"]), float(o["box_upper"])
        if not lo <= hi:
            raise ValueError(f"box of {o['label']!r} is empty: [{lo}, {hi}]")
        if p == 0 and hi == 0:
            empty += 1
            continue
        rows.append((str(o["label"]), p, lo, hi))
    if not rows:
        raise ValueError("no outcome in the support: nothing to plot")
    return rows, empty


def _group_breaks(labels: Sequence[str]) -> list[float]:
    """Return the ``y`` between consecutive rows whose label groups differ."""
    groups = [label.split(":", 1)[0] for label in labels]
    return [i - 0.5 for i in range(1, len(groups)) if groups[i] != groups[i - 1]]


def _rules(breaks: Sequence[float], xref: float) -> list[str]:
    """Rules across the whole axis at the group breaks (``xref``: any valid x)."""
    return [
        rf"\draw[cqMuted, line width=0.5pt] "
        rf"({{rel axis cs:0,0}} |- {{axis cs:{xref!r},{b!r}}}) -- "
        rf"({{rel axis cs:1,0}} |- {{axis cs:{xref!r},{b!r}}});"
        for b in breaks
    ]


def render_statistics(extract: Mapping[str, Any]) -> Rendered:
    """Return the dot-and-interval chart of the record extract, with its caption."""
    rows, empty = _support(extract)
    n = len(rows)
    ys = list(range(n))
    log = use_log_axis([v for _, p, lo, hi in rows for v in (p, lo, hi)])
    labels = ",".join("{" + escape(label) + "}" for label, *_ in rows)
    xmax = max(hi for *_, hi in rows)
    offsets = [
        ((lo - p) / OFFSET_UNIT, (hi - p) / OFFSET_UNIT) for _, p, lo, hi in rows
    ]
    reach = max(max(abs(a), abs(b)) for a, b in offsets)
    reach = _math.ceil(reach * 1.15 * 2) / 2 if reach > 0 else 1.0
    breaks = _group_breaks([label for label, *_ in rows])

    common = (
        f"height={n * ROW_HEIGHT + 0.4:.3f}cm, scale only axis, y dir=reverse, "
        f"ymin=-0.6, ymax={n - 0.4:.1f}, ytick={{{','.join(map(str, ys))}}}, "
        "tick style={cqRule}, axis line style={cqRule}, "
        f"tick label style={{font={SMALL}}}, label style={{font={MAIN}}}, "
        f"title style={{font={MAIN}, yshift=-2pt}}, "
        "ymajorgrids, grid style={cqRule!40, line width=0.3pt}, clip=false"
    )
    if log:
        smallest = min(v for _, p, lo, hi in rows for v in (p, lo, hi) if v > 0)
        xmin = smallest / LOG_MARGIN
        left_x = f"xmode=log, xmin={xmin!r}, xmax={xmax * LOG_MARGIN!r}, log basis x=10"
    else:
        xmin = 0.0
        left_x = (
            f"xmin=0, xmax={xmax * 1.08!r}, scaled x ticks=false, "
            "xticklabel style={/pgf/number format/fixed}"
        )
    xlabel = "probability" + (" (log scale)" if log else "")

    out: list[str] = [rf"\begin{{tikzpicture}}[font={MAIN}]"]
    out.append(
        rf"\begin{{axis}}[name=prob, width={LEFT_WIDTH}cm, {common}, "
        f"yticklabels={{{labels}}}, {left_x}, xlabel={{{xlabel}}}, "
        "title={honest $p$}]"
    )
    for y, (_, _p, lo, hi) in zip(ys, rows, strict=True):
        out.append(_plot(f"{BAND}, forget plot", [(max(lo, xmin), y), (hi, y)]))
    dots = [
        (p, y) for y, (_, p, _l, _h) in zip(ys, rows, strict=True) if p > 0 or not log
    ]
    out.append(_plot(f"{DOT}, forget plot", dots))
    out += _rules(breaks, xmin if log else 0.0)
    out.append(r"\end{axis}")

    out.append(
        r"\begin{axis}[at={(prob.east)}, anchor=west, xshift=0.45cm, "
        f"width={RIGHT_WIDTH}cm, {common}, yticklabels={{}}, "
        f"xmin={-reach!r}, xmax={reach!r}, "
        "xlabel={$q - p$, in units of $10^{-4}$}, title={acceptance box around $p$}, "
        "extra x ticks={0}, extra x tick labels={}, "
        "extra x tick style={grid=major, grid style={cqMuted, line width=0.4pt}}]"
    )
    for y, (a, b) in zip(ys, offsets, strict=True):
        out.append(_plot(f"{BAND}, forget plot", [(a, y), (b, y)]))
        for end in (a, b):
            out.append(
                rf"\draw[{TICK}] (axis cs:{end!r},{y - 0.28!r}) -- "
                rf"(axis cs:{end!r},{y + 0.28!r});"
            )
    out.append(_plot(f"{DOT}, forget plot", [(0.0, y) for y in ys]))
    out += _rules(breaks, 0.0)
    out.append(r"\end{axis}")
    out.append(r"\end{tikzpicture}")
    return Rendered("\n".join(out) + "\n", _caption(extract, rows, empty, log))


def _caption(
    extract: Mapping[str, Any],
    rows: Sequence[tuple[str, float, float, float]],
    empty: int,
    log: bool,
) -> str:
    """Write the statistics caption from the same data the figure reads."""
    total = len(rows) + empty
    widths = [(hi - lo) / 2 / OFFSET_UNIT for _, _p, lo, hi in rows]
    parts = [
        "The honest statistics against the acceptance test.",
        f"Each row is one of the {len(rows)} acceptance outcomes the honest "
        f"implementation produces with positive probability; the other {empty} of "
        f"the {total} outcomes have probability zero and an acceptance interval "
        "$[0, 0]$, and are not shown."
        if empty
        else f"Each row is one of the {len(rows)} acceptance outcomes.",
        "Left: the honest probability $p$ of each outcome"
        + (" on a logarithmic scale." if log else "."),
        "Right: the acceptance box $[q^-, q^+]$ the protocol accepts around it, as "
        f"$q - p$ in units of $10^{{-4}}$; its half-width runs from "
        f"${numeral(min(widths), 2)}$ to ${numeral(max(widths), 2)}$ in these "
        "units.",
    ]
    if extract.get("rounds"):
        budget = float(rational(extract["completeness_budget"]))
        rule = escape(extract.get("endpoint_rule", ""))
        parts.append(
            f"The box is set for $n = {numeral(float(extract['rounds']), 3)}$ rounds "
            f"with a completeness budget of ${numeral(budget, 3)}$"
            + (f" and {rule.capitalize()} endpoints." if rule else ".")
        )
    return " ".join(parts)
