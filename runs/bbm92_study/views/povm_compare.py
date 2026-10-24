r"""One station's POVM for two device sets side by side.

The figure reads each set's ``povm-dark-composed.json``.

The single-set figure (``povm.py``) puts the outcomes across and the
photon-number blocks down. Two sets that way would be twelve outcome columns,
too wide for a text width, so this figure turns the grid: one row per outcome,
the letter and its click patterns at the left, and to the right one column
group per device set, each with its photon-number blocks side by side (n = 0,
then n = 1), the basis kets over the columns. Cells are wider than tall, so
an entry such as ``1.3e-7`` prints in full.

* Both sets are drawn from the dark-composed family (the photon-number blocks
  composed with the detectors' dark-count channel), so the dark counts show:
  without dark counts the two families agree.
* A block's shading scale is shared by the two sets: the largest magnitude of
  that photon number in either, so a cell compares across sets as well as
  across outcomes.
* The blocks are the NORMALIZED station's where the preparation factored a
  common loss out of the detectors (the receiver's efficiency normalization):
  the caption states the factor and each declared efficiency beside the one
  the blocks use, from the preparation extract.

A complex block is refused: this figure prints one number per entry, and the
single-set figure draws real and imaginary parts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any

from certiqs_key.receiver.efficiency import DEFAULT_MARGIN
from runs.bbm92_study.views.povm import _fibre_text, _group, _is_complex, _ket, _scale
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

__all__ = ["render_povm_compare"]

CELL_W = 1.5
CELL_H = 0.42
BLOCK_GAP = 0.16
SET_GAP = 0.5
ROW_GAP = 0.16
LABEL_X = -0.12
MARGIN = numeral(float(DEFAULT_MARGIN))
"""The receiver's normalization margin, ``0.99``: the default factored loss is
the largest declared efficiency over it."""


def _blocks(group: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    blocks = list(group["blocks"])
    for b in blocks:
        if _is_complex(b):
            raise ValueError(
                f"block {b['key']!r} is complex: use the single-set figure"
            )
    return blocks


def _tight(math: str) -> str:
    """Set a times sign without its binary-operator space, so an entry fits its cell."""
    return math.replace(r"\times", r"{\times}")


def _cell(x: float, y: float, value: float, scale: float) -> list[str]:
    share = min(1.0, abs(value) / scale) if scale > 0 else 0.0
    tint = "cqNegative" if value < -ZERO_DISPLAY else "cqData"
    square = f"{at(x, y)} rectangle ++{at(CELL_W, -CELL_H)}"
    ink = "white" if share > 0.55 else "cqInk"
    return [
        rf"\fill[{tint}!{round(100 * share)}] {square};",
        rf"\draw[cqCellRule, line width=0.4pt] {square};",
        node(
            f"inner sep=0pt, font={SMALL}, text={ink}",
            x + CELL_W / 2,
            y - CELL_H / 2,
            f"${_tight(numeral(value, 2))}$",
        ),
    ]


def render_povm_compare(
    povms: Mapping[str, Mapping[str, Any]],
    normalization: Mapping[str, Any] | None = None,
    station: int = 0,
    party_names: Mapping[str, str] | None = None,
) -> Rendered:
    """Return the station's POVM of each set in ``povms`` side by side, and a caption.

    ``povms`` maps a set name (the column title) to its parsed
    ``povm-dark-composed.json``, in drawing order; ``normalization`` is the
    station's entry of the last set's preparation extract (``normalization[]``),
    for the caption.
    """
    groups = {name: _group(p, station) for name, p in povms.items()}
    blocks = {name: _blocks(g) for name, g in groups.items()}
    names = list(groups)
    reference = blocks[names[0]]
    letters = [e["letter"] for e in reference[0]["elements"]]
    keys = [b["key"] for b in reference]
    for name in names:
        if [b["key"] for b in blocks[name]] != keys or any(
            [e["letter"] for e in b["elements"]] != letters for b in blocks[name]
        ):
            raise ValueError(f"set {name!r} lists other blocks or outcomes")
    dims = [int(b["dimension"]) for b in reference]
    scales = [max(_scale(blocks[n][k]) for n in names) for k in range(len(keys))]
    fibres = {o["letter"]: o.get("fibre") for o in groups[names[0]].get("outcomes", [])}

    block_x: list[float] = []
    x = 0.0
    for d in dims:
        block_x.append(x)
        x += d * CELL_W + BLOCK_GAP
    set_width = x - BLOCK_GAP

    def set_x(i: int) -> float:
        return i * (set_width + SET_GAP)

    out: list[str] = [rf"\begin{{tikzpicture}}[font={MAIN}]"]
    muted = f"inner sep=1pt, font={SMALL}, text=cqMuted"
    for i, name in enumerate(names):
        x0 = set_x(i)
        out.append(
            node(
                rf"anchor=south, inner sep=1pt, font={MAIN}\bfseries",
                x0 + set_width / 2,
                0.62,
                escape(name),
            )
        )
        for k, b in enumerate(reference):
            bx = x0 + block_x[k]
            out.append(
                node(
                    f"anchor=south, {muted}",
                    bx + dims[k] * CELL_W / 2,
                    0.32,
                    escape(b.get("label", b["key"])),
                )
            )
            for j, ket in enumerate(b.get("basis", [])):
                out.append(
                    node(
                        f"anchor=south, {muted}",
                        bx + (j + 0.5) * CELL_W,
                        0.02,
                        _ket(str(ket)),
                    )
                )
    top = 0.0
    row_height = max(dims) * CELL_H
    for r, letter in enumerate(letters):
        mid = top - row_height / 2
        out.append(
            node(
                rf"anchor=south east, inner sep=1pt, font={MAIN}\bfseries",
                LABEL_X,
                mid,
                escape(letter),
            )
        )
        fibre = _fibre_text(fibres.get(letter))
        if fibre:
            out.append(
                node(
                    f"anchor=north east, align=right, {muted}",
                    LABEL_X,
                    mid,
                    fibre,
                )
            )
        for i, name in enumerate(names):
            for k, d in enumerate(dims):
                element = blocks[name][k]["elements"][r]
                bx = set_x(i) + block_x[k]
                by = top - (row_height - d * CELL_H) / 2
                for a in range(d):
                    for c in range(d):
                        out += _cell(
                            bx + c * CELL_W,
                            by - a * CELL_H,
                            float(element["re"][a][c]),
                            scales[k],
                        )
        top -= row_height + ROW_GAP
    out.append(r"\end{tikzpicture}")
    caption = _caption(
        names, groups, reference, normalization, station, party_names or {}
    )
    return Rendered("\n".join(out) + "\n", caption)


def _decimal(value: Fraction, digits: int = 4) -> str:
    return numeral(float(value), digits)


def _caption(
    names: Sequence[str],
    groups: Mapping[str, Mapping[str, Any]],
    reference: Sequence[Mapping[str, Any]],
    normalization: Mapping[str, Any] | None,
    station: int,
    party_names: Mapping[str, str],
) -> str:
    """Write the caption: the layout, the normalized efficiencies, the dark counts."""
    party = (normalization or {}).get("party")
    who = (
        escape(party_names[str(party)]) + "'s"
        if party in party_names
        else (f"Station {station}'s")
    )
    sides = " and ".join(
        f"{escape(n)} ({'left' if i == 0 else 'right'})" for i, n in enumerate(names)
    )
    blocks = " and ".join(escape(b.get("label", b["key"])) for b in reference)
    parts = [
        f"{who} measurement with {sides} devices: each outcome's operator on "
        f"{blocks} photons, shaded on one scale per photon number."
    ]
    if normalization and Fraction(normalization["factored_loss"]) < 1:
        t = Fraction(normalization["factored_loss"])
        # The default factor is the largest declared efficiency over the
        # receiver's margin (req:efficiency-normalization); a declared one is
        # stated as it is.
        rule = (
            ""
            if normalization.get("factor_declared")
            else rf"\eta_{{\max}}/{MARGIN} = "
        )
        pairs: dict[str, str] = {}
        for p in normalization["ports"]:
            pairs.setdefault(
                _decimal(Fraction(p["declared"])), _decimal(Fraction(p["compiled"]))
            )
        declared = " and ".join(f"${d}$" for d in pairs)
        compiled = " and ".join(f"${c}$" for c in pairs.values())
        parts.append(
            f"The {escape(names[-1])} entries use normalized efficiencies: the "
            f"engine moves the common loss ${rule}{t.numerator}/{t.denominator}$ "
            rf"into the channel, so the declared $\eta$ of {declared} enter as "
            f"{compiled}."
        )
    last = groups[names[-1]]
    no_click = {o["letter"] for o in last.get("outcomes", []) if o.get("fibre") == [[]]}
    zero = next((b for b in last["blocks"] if int(b["dimension"]) == 1), None)
    if zero is not None:
        clicks = [
            float(e["re"][0][0])
            for e in zero["elements"]
            if e["letter"] not in no_click and abs(float(e["re"][0][0])) > ZERO_DISPLAY
        ]
        if clicks:
            parts.append(
                f"Dark counts give the {escape(zero.get('label', zero['key']))} "
                f"click entries (${numeral(max(clicks), 2)}$)."
            )
    return " ".join(parts)
