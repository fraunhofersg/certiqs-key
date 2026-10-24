"""The POVM of one station, all photon-number blocks in one figure, from ``povm.json``.

The interactive POVM viewer shows the selected outcome's
operator as a heatmap per photon-number block, with magnitude as lightness and
phase as hue. Phase as hue prints badly and cannot be read in grey, so on paper
the figure is a grid: one column per outcome letter under a shared header, one
row per photon-number block (n = 0 and n = 1 in one figure),
every operator entry a filled cell:

* the cell's shade is the entry's magnitude over the block's largest magnitude
  (one scale per block, so letters compare),
  and the entry's signed value is printed in the cell;
* a complex block (an imaginary part above
  :data:`~runs.bbm92_study.views.tex.ZERO_DISPLAY`) is drawn as two rows, its
  real and its imaginary part, a negative entry shaded grey; a real block is
  one row;
* under each letter its coarse-graining fibre: the click patterns that make it
  (``outcomes[].fibre``), worded as the interactive view words them.

The figure reads the ``photon_blocks`` group of the chosen station. The
declared-sector groups (the compiled declaration's sectors) are a second view
of the same measurement and are not drawn here. The station, the shading
scale and the completeness residual go into the caption.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from runs.bbm92_study.views.tex import (
    MAIN,
    SMALL,
    ZERO_DISPLAY,
    Rendered,
    at,
    escape,
    node,
    numeral,
)

__all__ = ["render_povm"]

CELL = 0.74
PANEL_GAP = 0.3
ROW_GAP = 0.32
_KET = re.compile(r"\|(.*)\N{MATHEMATICAL RIGHT ANGLE BRACKET}")


@dataclass(frozen=True)
class _Row:
    block: Mapping[str, Any]
    kind: str
    """``"real"`` (a real block), ``"re"`` or ``"im"`` (a complex block's parts)."""
    scale: float


def _fibre_text(fibre: Sequence[Sequence[str]] | None) -> str:
    """Word a coarse-graining fibre: its pattern, or its count and click range."""
    if fibre is None:
        return ""
    if len(fibre) == 1:
        # Math braces: not every text font has brace glyphs.
        return r"$\{$" + ", ".join(escape(p) for p in fibre[0]) + r"$\}$"
    sizes = [len(p) for p in fibre]
    lo, hi = min(sizes), max(sizes)
    clicks = f"{lo}" if lo == hi else f"{lo}--{hi}"
    return rf"{len(fibre)} patterns,\\ {clicks} clicks"


def _ket(label: str) -> str:
    """Draw a basis label ``|a,b>`` as a ket; any other label escaped."""
    found = _KET.fullmatch(label)
    if found:
        return rf"$|{escape(found.group(1))}\rangle$"
    return escape(label)


def _group(povm: Mapping[str, Any], station: int) -> Mapping[str, Any]:
    for group in povm["groups"]:
        if group.get("kind") == "photon_blocks" and group.get("station") == station:
            return dict(group)
    raise ValueError(f"povm view has no photon-number blocks for station {station}")


def _is_complex(block: Mapping[str, Any]) -> bool:
    return any(
        abs(v) > ZERO_DISPLAY for e in block["elements"] for row in e["im"] for v in row
    )


def _scale(block: Mapping[str, Any]) -> float:
    return max(
        (
            abs(complex(r, i))
            for e in block["elements"]
            for re_row, im_row in zip(e["re"], e["im"], strict=True)
            for r, i in zip(re_row, im_row, strict=True)
        ),
        default=0.0,
    )


def _cell(x: float, y: float, value: float, scale: float) -> list[str]:
    """Return one filled cell with its printed value."""
    share = min(1.0, abs(value) / scale) if scale > 0 else 0.0
    tint = "cqNegative" if value < -ZERO_DISPLAY else "cqData"
    square = f"{at(x, y)} rectangle ++{at(CELL, -CELL)}"
    ink = "white" if share > 0.55 else "cqInk"
    return [
        rf"\fill[{tint}!{round(100 * share)}] {square};",
        rf"\draw[cqCellRule, line width=0.4pt] {square};",
        node(
            f"inner sep=0pt, font={MAIN}, text={ink}",
            x + CELL / 2,
            y - CELL / 2,
            f"${numeral(value, 2)}$",
        ),
    ]


def render_povm(povm: Mapping[str, Any], station: int = 0) -> Rendered:
    """Return the station's photon-number blocks as one grid, with its caption."""
    group = _group(povm, station)
    blocks = list(group["blocks"])
    letters = [e["letter"] for e in blocks[0]["elements"]]
    for block in blocks:
        if [e["letter"] for e in block["elements"]] != letters:
            raise ValueError("the blocks of one station list different outcomes")
    fibres = {o["letter"]: o.get("fibre") for o in group.get("outcomes", [])}
    rows: list[_Row] = []
    for block in blocks:
        kinds = ["re", "im"] if _is_complex(block) else ["real"]
        rows += [_Row(block, kind, _scale(block)) for kind in kinds]
    width = max(int(b["dimension"]) for b in blocks) * CELL

    def column(k: int) -> float:
        return k * (width + PANEL_GAP)

    out: list[str] = [rf"\begin{{tikzpicture}}[font={MAIN}]"]
    for k, letter in enumerate(letters):
        out.append(
            node(
                rf"anchor=south, inner sep=1pt, font={MAIN}\bfseries",
                column(k) + width / 2,
                0.04,
                escape(letter),
            )
        )
    top = 0.0
    muted = f"anchor=east, inner sep=1pt, font={SMALL}, text=cqMuted"
    for row in rows:
        d = int(row.block["dimension"])
        side = d * CELL
        label = escape(row.block.get("label", row.block["key"]))
        if row.kind != "real":
            label += rf", $\mathrm{{{'Re' if row.kind == 're' else 'Im'}}}$"
        out.append(
            node(
                f"anchor=east, inner sep=1pt, font={MAIN}", -0.78, top - side / 2, label
            )
        )
        for i, b in enumerate(row.block.get("basis", [])):
            out.append(node(muted, -0.04, top - (i + 0.5) * CELL, _ket(str(b))))
        for k, element in enumerate(row.block["elements"]):
            x0 = column(k) + (width - side) / 2
            part = element["im" if row.kind == "im" else "re"]
            for i in range(d):
                for j in range(d):
                    out += _cell(x0 + j * CELL, top - i * CELL, part[i][j], row.scale)
        top -= side + ROW_GAP
    for k, letter in enumerate(letters):
        out.append(
            node(
                f"anchor=north, inner sep=1pt, align=center, font={SMALL}, "
                "text=cqMuted",
                column(k) + width / 2,
                top + ROW_GAP - 0.04,
                _fibre_text(fibres.get(letter)),
            )
        )
    out.append(r"\end{tikzpicture}")
    return Rendered("\n".join(out) + "\n", _caption(group, blocks))


def _caption(group: Mapping[str, Any], blocks: Sequence[Mapping[str, Any]]) -> str:
    """Write the POVM's caption from the same data the figure reads."""
    listed = ", ".join(
        f"{escape(b.get('label', b['key']))} (dimension {int(b['dimension'])})"
        for b in blocks
    )
    scales = ", ".join(f"${numeral(_scale(b), 3)}$" for b in blocks)
    residual = max(
        float((b.get("completeness") or {}).get("max_abs", 0.0)) for b in blocks
    )
    real = not any(_is_complex(b) for b in blocks)
    parts = [
        f"The measurement of station {int(group.get('station', 0))} as a POVM, one "
        f"row per photon-number block: {listed}.",
        "Each small matrix is the operator of one outcome in the Fock basis listed "
        "on the left; the printed numbers are its entries"
        + (", all real" if real else ", split into real and imaginary parts")
        + ", and the shading is their magnitude relative to the largest in the "
        f"block ({scales}).",
        "Under each outcome are the detector click patterns it collects",
    ]
    for o in group.get("outcomes", []):
        fibre = o.get("fibre") or []
        if len(fibre) > 1:
            lo, hi = min(len(p) for p in fibre), max(len(p) for p in fibre)
            clicks = f"{lo}" if lo == hi else f"{lo} to {hi}"
            parts[-1] += (
                f"; {escape(o['letter'])} collects the {len(fibre)} patterns with "
                f"{clicks} clicks"
            )
    parts[-1] += "."
    if residual < ZERO_DISPLAY:
        mantissa, exponent = f"{residual:.1e}".split("e")
        said = (
            f"to floating-point precision (largest deviation "
            f"${mantissa}\\times10^{{{int(exponent)}}}$)"
            if residual > 0
            else "exactly"
        )
    else:
        said = f"up to ${numeral(residual, 2)}$ in every entry"
    parts.append(f"The operators sum to the identity {said}.")
    return " ".join(parts)
