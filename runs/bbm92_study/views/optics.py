"""The receiver mode circuit of one station, from ``optics.json``.

This is the "Mode transformation" view as a TikZ picture, the same content
laid out by the same rules and drawn for paper:

* one horizontal rail per declared mode, in the view model's ``rails`` order
  (grouped by path, polarisation order inside a group), with a gap between
  groups, and each mode's input role at its left: channel, probe, or vacuum
  where the station's ``undeclared_inputs_vacuum`` assumption names it;
* each element of ``elements`` a glyph spanning its ``support`` rails, in the
  order of its ``column`` (the element DAG's topological order). Elements
  sharing a column stand side by side in it, top rail first, so every element
  has its own label slot; where the support is not contiguous in rail order
  the glyph is one box per contiguous run, joined by a connector, so a rail the
  element does not act on visibly passes it by;
* the labels in a strip above the rails (class and element name; the
  catalogue ids stay out, since two different splitters share one) and the
  parameters in a strip below, so no label sits between two rails;
* one detector per entry of ``ports`` at the right, spanning the rails of its
  modes (both polarisations of its path, where it clicks on either), with its
  efficiency and dark-count probability, stated once for all when they agree;
  a rail no port reads ends dashed and "unmonitored (loss)" (the receiver
  contract's rem:unmonitored: the amplitude reaching it is loss).

What explains the figure goes into the caption :func:`_caption` writes from the
same data: the encoding, the passive basis choice in words,
where the detector values come from.

Nothing is placed by an instance name. The glyph is chosen by catalogue id
(C1 beamsplitter, C2 polarising beamsplitter, C3 retarder; anything else a
dashed labelled box); the passive basis choice is the
C1 element the channel modes enter first, found from ``modes[].channel`` and
the columns. A retarder's angle and retardance are read in either form the
receiver writes (:func:`radians`, :func:`pi_multiple`).

WHERE A DETECTOR'S DARK COUNT COMES FROM
=======================================
The view model attaches per-port detector parameters through
``ports[].detector.parameters``. For a two-station protocol it does not (its
``engine_gaps`` says why), so the figure falls back to the declared device of
the same preparation, copied into the snapshot as the device set's
``preparation-extract.json`` (``device[<party>]``); the caption says so. A
value in neither place prints as "n/a" rather than as a guess.
"""

from __future__ import annotations

import math as _math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from runs.bbm92_study.views.tex import (
    MAIN,
    SMALL,
    Rendered,
    at,
    draw,
    escape,
    node,
    numeral,
    rational,
    words,
)

__all__ = ["pi_multiple", "radians", "render_optics"]

RAIL_GAP = 0.40
GROUP_GAP = 0.24
LABEL_X = 1.75
RAIL_START = 1.9
FIRST_SLOT = 2.75
SLOT_WIDTH = 1.2
COLUMN_GAP = 0.2
GLYPH_WIDTH = 0.46
PLATE_WIDTH = 0.16
GLYPH_PAD = 0.13
STRIP = 0.3
DETECTOR_GAP = 0.6
DETECTOR_WIDTH = 0.32
ARROW = "-{Stealth[length=3.5pt]}"
DOTTED = "cqRule, line width=0.4pt, densely dotted"


@dataclass(frozen=True)
class _Glyph:
    element: Mapping[str, Any]
    x: float
    runs: tuple[tuple[float, float], ...]
    support_ys: tuple[float, ...]


def _rail_positions(
    rails: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, float], list[str]]:
    """Return each mode's rail ``y`` (top rail at 0, downwards) and the rail order."""
    ys: dict[str, float] = {}
    order: list[str] = []
    y = 0.0
    for g, group in enumerate(rails):
        if g:
            y -= GROUP_GAP
        for label in group["modes"]:
            ys[label] = y
            order.append(label)
            y -= RAIL_GAP
    return ys, order


def _contiguous_runs(support: Sequence[str], order: Sequence[str]) -> list[list[str]]:
    """Split ``support`` into runs of consecutive rails in ``order``."""
    index = sorted(order.index(m) for m in support if m in order)
    runs: list[list[str]] = []
    for i in index:
        if runs and order.index(runs[-1][-1]) == i - 1:
            runs[-1].append(order[i])
        else:
            runs.append([order[i]])
    return runs


def pi_multiple(value: Any) -> Fraction | None:
    """Return an angle as an exact multiple of pi, or ``None`` if it is not one.

    The receiver writes a retarder's ``angle`` and ``retardance`` as
    ``{"pi_coefficient": "p/q"}``, the exact rational ``p/q`` times pi. An
    older view model writes radians as a float; one within ``1e-9`` of a
    multiple of pi with a denominator up to 1000 is read as that multiple.
    """
    if isinstance(value, Mapping):
        return rational(value["pi_coefficient"])
    ratio = float(value) / _math.pi
    near = Fraction(ratio).limit_denominator(1000)
    return near if abs(float(near) - ratio) < 1e-9 else None


def radians(value: Any) -> float:
    """Return an angle in radians: a float as it is, a ``pi_coefficient`` times pi."""
    if isinstance(value, Mapping):
        return float(rational(value["pi_coefficient"])) * _math.pi
    return float(value)


def _parameter_lines(element: Mapping[str, Any]) -> str:
    """Return the parameters printed under a glyph, one per line.

    ``{=}`` drops the relation spacing: the labels of neighbouring glyphs share
    one row, and under the plate and the Z-arm PBS they would otherwise touch.
    """
    p = {q["name"]: q["value"] for q in element.get("parameters", [])}
    parts: list[str] = []
    catalogue = element.get("catalogue_id")
    if catalogue == "C1" and "transmittance" in p:
        parts.append(f"$t{{=}}{numeral(float(p['transmittance']))}$")
    elif catalogue == "C2":
        for key, symbol in (("transmittance_h", "t_H"), ("transmittance_v", "t_V")):
            if key in p:
                parts.append(f"${symbol}{{=}}{numeral(float(p[key]))}$")
    elif catalogue == "C3":
        if "retardance" in p:
            named = {Fraction(1): r"\lambda/2", Fraction(1, 2): r"\lambda/4"}
            multiple = pi_multiple(p["retardance"])
            plate = named.get(multiple) if multiple is not None else None
            delta = rf"\delta{{=}}{numeral(radians(p['retardance']))}"
            parts.append(f"${plate or delta}$")
        if "angle" in p:
            degrees = _math.degrees(radians(p["angle"]))
            parts.append(rf"$\theta{{=}}{numeral(degrees)}^\circ$")
    for name, value in p.items():
        if name.startswith("loss") and isinstance(value, int | float) and value:
            parts.append(f"{escape(name)} ${numeral(float(value))}$")
    return r"\\".join(parts)


def _vacuum_inputs(assumptions: Sequence[Mapping[str, Any]]) -> set[str]:
    """Return the modes the station's assumption ledger declares vacuum inputs."""
    vacuum: set[str] = set()
    for a in assumptions:
        constrains = a.get("constrains")
        if a.get("machine_key") == "undeclared_inputs_vacuum" and isinstance(
            constrains, Mapping
        ):
            vacuum.update(str(m) for m in constrains.get("undeclared_input_modes", []))
    return vacuum


def _mode_label(mode: Mapping[str, Any]) -> str:
    """Draw a structured mode as its path with the polarisation as subscript."""
    if mode.get("structured") and mode.get("path") and mode.get("polarization"):
        path = escape(mode["path"])
        pol = escape(mode["polarization"])
        return rf"$\mathrm{{{path}}}_{{\mathrm{{{pol}}}}}$"
    return escape(mode["label"])


def _detector_values(
    port: Mapping[str, Any], fallback: Mapping[str, Any] | None
) -> tuple[str, str, bool]:
    """Return a port's efficiency and dark-count probability as math.

    The third value says whether either came from the record fallback.
    """
    name = str(port["port"])
    detector = port.get("detector") or {}
    eta: str | None = None
    dark: str | None = None
    for q in detector.get("parameters", []):
        if q.get("quantity") == "efficiency" or q.get("name") == "efficiency":
            eta = numeral(float(q["value"]))
        if q.get("name") == "dark_count":
            dark = numeral(float(q["value"]))
    used_fallback = False
    if eta is None and detector.get("eta_record"):
        eta = numeral(float(detector["eta_record"]["value"]))
    if eta is None and fallback and name in fallback.get("efficiency", {}):
        eta = numeral(float(rational(fallback["efficiency"][name])))
        used_fallback = True
    if dark is None and fallback and name in fallback.get("dark_count", {}):
        dark = numeral(float(rational(fallback["dark_count"][name])))
        used_fallback = True
    return eta or r"\mbox{n/a}", dark or r"\mbox{n/a}", used_fallback


def _station(optics: Mapping[str, Any], station: int) -> Mapping[str, Any]:
    stations = optics.get("stations")
    if stations:
        found = [s for s in stations if s["station"]["index"] == station]
        if not found:
            raise ValueError(f"optics view has no station {station}")
        return dict(found[0])
    return optics


def _glyph_style(catalogue: str) -> str:
    """Return the glyph's style: shape and fill, not hue, tell the classes apart."""
    if catalogue == "C3":
        return "draw=cqInk, fill=cqInk!55, line width=0.5pt"
    if catalogue == "C2":
        return "draw=cqInk, fill=cqRule!45, line width=0.6pt"
    if catalogue == "C1":
        return "draw=cqInk, fill=white, line width=0.6pt"
    return "draw=cqInk, fill=white, line width=0.6pt, dashed"


def _role(mode: Mapping[str, Any], vacuum: set[str]) -> str:
    if mode.get("channel"):
        return "channel"
    if mode.get("probe"):
        return "probe"
    return "vacuum" if mode["label"] in vacuum else "other"


def _glyphs(
    model: Mapping[str, Any], ys: Mapping[str, float], order: Sequence[str]
) -> list[_Glyph]:
    """Place the elements: by column, then by top rail, one slot each."""

    def first_rail(e: Mapping[str, Any]) -> int:
        return min((order.index(m) for m in e["support"] if m in order), default=0)

    elements = sorted(
        model["elements"], key=lambda e: (int(e["column"]), first_rail(e))
    )
    glyphs: list[_Glyph] = []
    x = FIRST_SLOT
    for i, e in enumerate(elements):
        if i and int(e["column"]) != int(elements[i - 1]["column"]):
            x += COLUMN_GAP
        runs = tuple(
            (ys[run[0]] + GLYPH_PAD, ys[run[-1]] - GLYPH_PAD)
            for run in _contiguous_runs(e["support"], order)
        )
        support_ys = tuple(ys[m] for m in e["support"] if m in ys)
        glyphs.append(_Glyph(e, x, runs, support_ys))
        x += SLOT_WIDTH
    return glyphs


def _rails(
    model: Mapping[str, Any],
    ys: Mapping[str, float],
    order: Sequence[str],
    glyphs: Sequence[_Glyph],
    detector_x: float,
) -> list[str]:
    """Draw every rail: label and role, input, inside the optics, output."""
    modes = {m["label"]: m for m in model["modes"]}
    vacuum = _vacuum_inputs(model.get("assumptions", []))
    monitored = {m for p in model["ports"] for m in p["modes"]}
    out: list[str] = []
    for label in order:
        y = ys[label]
        mode = modes[label]
        touching = [g.x for g in glyphs if y in g.support_ys]
        first = min(touching) - GLYPH_WIDTH / 2 if touching else RAIL_START + 0.6
        last = max(touching) + GLYPH_WIDTH / 2 if touching else first
        role = _role(mode, vacuum)
        tint = "cqOptical" if role == "channel" else "cqMuted"
        out.append(
            node(
                f"anchor=east, inner sep=1pt, font={MAIN}",
                LABEL_X,
                y,
                _mode_label(mode),
            )
        )
        out.append(
            node(
                rf"anchor=east, inner sep=1pt, font={SMALL}\itshape, text={tint}",
                LABEL_X - 0.62,
                y,
                role,
            )
        )
        if mode.get("channel"):
            style = f"cqOptical, line width=1.1pt, {ARROW}"
        else:
            style = "cqMuted, line width=0.4pt"
        out.append(draw(style, (RAIL_START, y), (first, y)))
        if last > first:
            out.append(draw("cqInk, line width=0.5pt", (first, y), (last, y)))
        if label in monitored:
            out.append(draw("cqDetector, line width=0.8pt", (last, y), (detector_x, y)))
        else:
            end = detector_x - 0.05
            dashed = "cqMuted, line width=0.4pt, dash pattern=on 1.6pt off 1.2pt"
            out.append(draw(dashed, (last, y), (end, y)))
            out.append(
                node(
                    f"anchor=west, inner sep=1pt, font={SMALL}, text=cqMuted",
                    end,
                    y,
                    "unmonitored (loss)",
                )
            )
    return out


def _is_basis_choice(model: Mapping[str, Any], glyphs: Sequence[_Glyph]) -> set[str]:
    """Return the ids of the C1 elements the channel modes enter first."""
    channel = {m["label"] for m in model["modes"] if m.get("channel")}
    first_column = min(
        (
            int(g.element["column"])
            for g in glyphs
            if channel & set(g.element["support"])
        ),
        default=None,
    )
    return {
        str(g.element["id"])
        for g in glyphs
        if g.element.get("catalogue_id") == "C1"
        and channel & set(g.element["support"])
        and int(g.element["column"]) == first_column
    }


def _elements(
    model: Mapping[str, Any], glyphs: Sequence[_Glyph], label_y: float, param_y: float
) -> list[str]:
    """Draw the glyphs, their label strip above and their parameter strip below."""
    choice = _is_basis_choice(model, glyphs)
    out: list[str] = []
    for g in glyphs:
        e = g.element
        catalogue = str(e.get("catalogue_id"))
        half = (PLATE_WIDTH if catalogue == "C3" else GLYPH_WIDTH) / 2
        if len(g.runs) > 1:
            out.append(
                draw(
                    "cqInk, line width=0.5pt", (g.x, g.runs[0][1]), (g.x, g.runs[-1][0])
                )
            )
        for top, bottom in g.runs:
            corners = f"{at(g.x - half, bottom)} rectangle {at(g.x + half, top)}"
            out.append(rf"\filldraw[{_glyph_style(catalogue)}] {corners};")
            if catalogue in ("C1", "C2"):
                out.append(
                    draw(
                        "cqInk, line width=0.5pt",
                        (g.x - half, bottom),
                        (g.x + half, top),
                    )
                )
        for y in g.support_ys:
            out.append(rf"\fill[cqOptical] {at(g.x, y)} circle (0.9pt);")
        if g.runs[0][0] < label_y - STRIP - 0.05:
            out.append(draw(DOTTED, (g.x, label_y), (g.x, g.runs[0][0])))
        if g.runs[-1][1] > param_y + STRIP + 0.05:
            out.append(draw(DOTTED, (g.x, g.runs[-1][1]), (g.x, param_y)))
        title = words(e.get("class_title") or catalogue)
        label = rf"{title}\\{{\itshape {escape(e.get('name', ''))}}}"
        width = f"text width={SLOT_WIDTH - 0.02:.3f}cm"
        out.append(
            node(
                f"anchor=south, inner sep=1pt, align=center, {width}, font={SMALL}",
                g.x,
                label_y,
                label,
            )
        )
        if str(e["id"]) in choice:
            out.append(
                node(
                    rf"anchor=south, inner sep=1pt, font={SMALL}\itshape, "
                    "text=cqOptical",
                    g.x,
                    label_y + 0.62,
                    "passive basis choice",
                )
            )
        params = _parameter_lines(e)
        if params:
            out.append(
                node(
                    f"anchor=north, inner sep=1pt, align=center, font={SMALL}",
                    g.x,
                    param_y,
                    params,
                )
            )
    return out


def _detectors(
    model: Mapping[str, Any],
    ys: Mapping[str, float],
    detector_x: float,
    fallback: Mapping[str, Any] | None,
) -> tuple[list[str], bool]:
    """Draw each port's detector and its values; say whether the fallback was used.

    When every detector has the same efficiency and dark-count probability,
    one line under the column states them once; otherwise each detector has
    its own.
    """
    out: list[str] = []
    values = [_detector_values(port, fallback) for port in model["ports"]]
    shared = len({(eta, dark) for eta, dark, _ in values}) == 1
    lowest = 0.0
    for port, (eta, dark, _used) in zip(model["ports"], values, strict=True):
        port_ys = [ys[m] for m in port["modes"] if m in ys]
        if not port_ys:
            continue
        y_top, y_bottom = max(port_ys) + 0.16, min(port_ys) - 0.16
        lowest = min(lowest, y_bottom)
        radius = (y_top - y_bottom) / 2
        xm = detector_x + DETECTOR_WIDTH / 2
        shape = (
            f"{at(detector_x, y_top)} -- {at(xm, y_top)} "
            f"arc[start angle=90, end angle=-90, radius={radius:.3f}] "
            f"-- {at(detector_x, y_bottom)} -- cycle"
        )
        out.append(
            rf"\filldraw[draw=cqDetector, fill=white, line width=0.8pt] {shape};"
        )
        yc = (y_top + y_bottom) / 2
        out.append(
            node(
                rf"inner sep=0pt, font={SMALL}\bfseries",
                detector_x + 0.17,
                yc,
                escape(port["port"]),
            )
        )
        if not shared:
            out.append(
                node(
                    f"anchor=west, inner sep=1pt, font={SMALL}",
                    detector_x + DETECTOR_WIDTH + 0.2,
                    yc,
                    rf"$\eta={eta}$, $p_{{\mathrm{{dc}}}}={dark}$",
                )
            )
    if shared and values:
        eta, dark, _used = values[0]
        out.append(
            node(
                f"anchor=north west, inner sep=1pt, font={SMALL}",
                detector_x - 0.1,
                lowest - 0.12,
                rf"all detectors: $\eta={eta}$, $p_{{\mathrm{{dc}}}}={dark}$",
            )
        )
    return out, any(used for _e, _d, used in values)


def _stripped(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _stripped(v) for k, v in value.items() if k != "provenance"}
    if isinstance(value, list):
        return [_stripped(v) for v in value]
    return value


def render_optics(
    optics: Mapping[str, Any],
    station: int = 0,
    device: Mapping[str, Any] | None = None,
    party_names: Mapping[str, str] | None = None,
) -> Rendered:
    """Return the mode circuit of ``station`` with its caption.

    ``device`` is the declared device table keyed by party (a preparation
    extract's ``device``); it is read only for a detector value the view
    model does not attach.
    ``party_names`` names the parties in the caption (from the protocol map's
    lanes).
    """
    model = _station(optics, station)
    ys, order = _rail_positions(model["rails"])
    party = (model.get("station") or {}).get("party")
    fallback = device.get(party) if device and party else None
    glyphs = _glyphs(model, ys, order)
    last_slot = glyphs[-1].x if glyphs else FIRST_SLOT
    detector_x = last_slot + SLOT_WIDTH / 2 + DETECTOR_GAP
    label_y = max(ys.values()) + GLYPH_PAD + STRIP
    param_y = min(ys.values()) - GLYPH_PAD - STRIP

    out: list[str] = [rf"\begin{{tikzpicture}}[font={MAIN}, line cap=round]"]
    out += _rails(model, ys, order, glyphs, detector_x)
    out += _elements(model, glyphs, label_y, param_y)
    detectors, used_fallback = _detectors(model, ys, detector_x, fallback)
    out += detectors
    out.append(r"\end{tikzpicture}")
    caption = _caption(optics, model, glyphs, station, used_fallback, party_names or {})
    return Rendered("\n".join(out) + "\n", caption)


def _series(items: Sequence[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _monitoring_sentence(model: Mapping[str, Any]) -> str:
    """Say what the detectors monitor, read off the ports.

    A port reading several modes is a detector clicking on any of them (both
    polarisations of its path, for a polarisation receiver); a mode no port
    reads is loss, and the sentence names that only where one exists.
    """
    monitored = {m for p in model["ports"] for m in p["modes"]}
    single = all(len(p["modes"]) == 1 for p in model["ports"])
    what = (
        "Each detector monitors one output mode"
        if single
        else "Each detector monitors the modes it spans and clicks on light in any "
        "of them"
    )
    if all(m["label"] in monitored for m in model["modes"]):
        return what + "."
    return (
        f"{what}; light in an output no detector monitors is lost (the receiver "
        "contract's remark on unmonitored modes)."
    )


def _caption(
    optics: Mapping[str, Any],
    model: Mapping[str, Any],
    glyphs: Sequence[_Glyph],
    station: int,
    used_fallback: bool,
    party_names: Mapping[str, str],
) -> str:
    """Write the receiver's caption from the same data the figure reads."""
    party = (model.get("station") or {}).get("party")
    who = escape(party_names.get(str(party), f"party {party}")) if party else ""
    parts = [
        f"The receiver of {who}'s station as a mode circuit."
        if who
        else f"The receiver of station {station} as a mode circuit."
    ]
    others = [
        s for s in optics.get("stations") or [] if s["station"]["index"] != station
    ]
    keys = ("modes", "rails", "elements", "edges", "ports")
    if others and all(
        _stripped({k: s.get(k) for k in keys})
        == _stripped({k: model.get(k) for k in keys})
        for s in others
    ):
        names = [
            escape(party_names.get(str(s["station"].get("party")), "the other station"))
            for s in others
        ]
        parts.append(f"{_series(names)}'s receiver is the same.")
    channel = [_mode_label(m) for m in model["modes"] if m.get("channel")]
    parts.append(
        "Each horizontal line is one optical mode, a path with a polarisation; "
        f"the channel delivers {_series(channel)}, and the other modes enter empty "
        "(in the vacuum state)."
    )
    parts.append(
        "The optical elements act on the modes they span (dots), in the order "
        "light meets them, with their parameters below."
    )
    if _is_basis_choice(model, glyphs):
        parts.append(
            "The first beamsplitter sends each photon at random into one of the two "
            "measurement bases: the basis choice is passive."
        )
    parts.append(_monitoring_sentence(model))
    if used_fallback:
        parts.append(
            r"The detector efficiency $\eta$ and dark-count probability "
            r"$p_{\mathrm{dc}}$ are the values the run declares for the device."
        )
    return " ".join(parts)
