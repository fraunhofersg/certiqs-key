r"""The receiver as a compact beam diagram labelled by symbols, from ``optics.json``.

The detailed figure (``optics.py``) draws a receiver as a mode circuit, one
rail per mode, with every parameter's value. This one is its companion beside
the parameter table (``devices.py``): the same receiver as an optical bench,
one line per beam path, each element labelled by the symbol of its parameter
in the table and no value, so that the two read as one figure and table. It
is about half a text width wide.

LAYOUT: BEAMS, NOT MODES
========================
A structured mode is a path with a polarisation; the drawing has one beam per
path. The channel's path enters from the left. The elements are taken in the
order of their ``column`` (the element DAG's topological order), each placed
one step further along the beam it acts on; an element whose support reaches
a path no beam has reached yet (a beamsplitter's reflected arm, a polarising
splitter's reflected output) starts that path's beam there, at a right angle:
counter-clockwise unless that ray would run into something already drawn,
then clockwise. A detector ends the beam of the path its port reads (one or
both of its polarisations); a path no port reads ends in a short dashed stub
(its light is lost). Each label goes
to the side of its element with more room. The layout handles a tree of
beams, which is what a passive receiver of splitters and plates is; an
element joining two beams, or a port reading two paths, is refused rather
than drawn wrong.

SYMBOLS
=======
By catalogue id, as the detailed figure picks its glyphs, never by instance
name: the passive basis choice (the C1 beamsplitter the channel enters
first) is labelled by the transmittance ``T``, a polarising splitter (C2) by
its two leaks (the share of V it transmits and of H it reflects), a
retarder (C3) by its angle as a multiple of pi, a detector by the efficiency
of its port; the dark-click probability is one line for all detectors. The
caption says where the leaked light goes, read off the ports: to the other
detector of the pair where every port reads both polarisations of its path,
to no detector otherwise. Each symbol sits in a tint tag touching its
element (``fig chip``: elements and detectors drawn larger, every label
attached to what it names, nothing floating). The
symbols are
:data:`~runs.bbm92_study.views.devices.SYMBOLS`. Where the stations' plates
stand at different angles, the plate is labelled by the angle of the station
at the simplest multiple of pi plus half the analyser rotation (a plate turned
by ``t`` rotates the polarisation by ``2t``), and the caption names the station
at which the rotation is zero.
"""

from __future__ import annotations

import math as _math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from runs.bbm92_study.views.devices import SYMBOLS, efficiency_symbol
from runs.bbm92_study.views.optics import _station, pi_multiple, radians
from runs.bbm92_study.views.tex import (
    MAIN,
    SMALL,
    Rendered,
    at,
    draw,
    escape,
    node,
    numeral,
)

__all__ = ["render_optics_compact"]

STEP = 1.3
"""Distance between consecutive elements along a beam (cm)."""
INPUT = 0.75
DETECTOR_GAP = 0.75
STUB = 0.45
CUBE = 0.46
"""A splitter's side (cm): 4.6 mm, the detectors' radius 2.6 mm."""
PLATE_ALONG = 0.09
PLATE_ACROSS = 0.56
D_RADIUS = 0.26
D_FLAT = 0.09
DASH = "dash pattern=on 1.6pt off 1.2pt"
LABEL_GAP = CUBE / 2 + 0.05
"""From an element's centre to its tag: the tag touches the element's edge."""
CLEAR = 0.55
BEAM = "cqOptical, line width=0.8pt"
LINE = "cqInk, line width=0.6pt"
TAG = r"fig chip, font=\sffamily\figsmall"
"""A symbol's tag: the preamble's ``fig chip`` (a tint chip), small type."""
CHAR = 0.12
"""Rough width of one character of a tag (cm), for label room."""

Vec = tuple[float, float]


def _add(p: Vec, d: Vec, s: float = 1.0) -> Vec:
    return (p[0] + s * d[0], p[1] + s * d[1])


def _ccw(d: Vec) -> Vec:
    return (-d[1], d[0])


def _cw(d: Vec) -> Vec:
    return (d[1], -d[0])


def _point_segment(p: Vec, a: Vec, b: Vec) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    t = (
        0.0
        if length == 0
        else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length))
    )
    return _math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


@dataclass
class _Box:
    """An axis-aligned rectangle something occupies: a glyph or a label."""

    x0: float
    y0: float
    x1: float
    y1: float

    def overlaps(self, other: _Box, pad: float = 0.04) -> bool:
        return not (
            self.x1 + pad <= other.x0
            or other.x1 + pad <= self.x0
            or self.y1 + pad <= other.y0
            or other.y1 + pad <= self.y0
        )


@dataclass
class _Placed:
    element: Mapping[str, Any]
    at: Vec
    incoming: Vec
    outgoing: list[Vec]


@dataclass
class _Bench:
    """What has been drawn so far: beam segments, element centres, label boxes."""

    segments: list[tuple[Vec, Vec]] = field(default_factory=list)
    centres: list[Vec] = field(default_factory=list)
    boxes: list[_Box] = field(default_factory=list)

    def clear_ray(self, start: Vec, d: Vec, reach: float) -> bool:
        """Whether a ray from ``start`` keeps :data:`CLEAR` from everything drawn."""
        samples = [_add(start, d, reach * k / 8) for k in range(1, 9)]
        for p in samples:
            if any(_math.dist(p, c) < CLEAR for c in self.centres if c != start):
                return False
            for a, b in self.segments:
                if start in (a, b):
                    continue
                if _point_segment(p, a, b) < CLEAR:
                    return False
        return True

    def room(self, box: _Box) -> float:
        """Return how far ``box`` keeps from the beams and boxes (0 if it touches)."""
        if any(box.overlaps(b) for b in self.boxes):
            return 0.0
        corners = [
            (box.x0, box.y0),
            (box.x1, box.y0),
            (box.x0, box.y1),
            (box.x1, box.y1),
            ((box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2),
        ]
        near = min(
            (_point_segment(p, a, b) for p in corners for a, b in self.segments),
            default=10.0,
        )
        inside = any(
            box.x0 - 0.02 <= x <= box.x1 + 0.02 and box.y0 - 0.02 <= y <= box.y1 + 0.02
            for a, b in self.segments
            for x, y in (a, b, _add(a, (b[0] - a[0], b[1] - a[1]), 0.5))
        )
        return 0.0 if inside else near


def _visible_length(text: str) -> int:
    """Count a label's printed characters roughly: a control word is one."""
    out = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            i += 1
            while i < len(text) and text[i].isalpha():
                i += 1
            out += 1
            continue
        if ch not in "{}$_^":
            out += 1
        i += 1
    return out


def _label_box(anchor: Vec, side: Vec, text: str, height: float = 0.36) -> _Box:
    """Return the box a tag set beside ``anchor`` on ``side`` occupies."""
    width = CHAR * _visible_length(text) + 0.12
    x, y = anchor
    if side == (1.0, 0.0):
        return _Box(x, y - height / 2, x + width, y + height / 2)
    if side == (-1.0, 0.0):
        return _Box(x - width, y - height / 2, x, y + height / 2)
    if side == (0.0, 1.0):
        return _Box(x - width / 2, y, x + width / 2, y + height)
    return _Box(x - width / 2, y - height, x + width / 2, y)


_ANCHOR: Mapping[Vec, str] = {
    (1.0, 0.0): "west",
    (-1.0, 0.0): "east",
    (0.0, 1.0): "south",
    (0.0, -1.0): "north",
}


def _paths(model: Mapping[str, Any], modes: Sequence[str]) -> list[str]:
    path = {m["label"]: m.get("path") for m in model["modes"]}
    out: list[str] = []
    for label in modes:
        p = path.get(label)
        if not p:
            raise ValueError(
                f"mode {label!r} has no path: the compact figure needs paths"
            )
        if p not in out:
            out.append(str(p))
    return out


def _ports_read_whole_paths(model: Mapping[str, Any]) -> bool:
    """Whether every port reads every mode of its path (both polarisations).

    Then a detector clicks on either polarisation of its path, and the light a
    polarising splitter leaks the wrong way clicks the other detector of the
    pair instead of being lost.
    """
    by_path: dict[str, set[str]] = {}
    for m in model["modes"]:
        by_path.setdefault(str(m.get("path")), set()).add(str(m["label"]))
    for port in model["ports"]:
        read = {str(label) for label in port["modes"]}
        for path in _paths(model, port["modes"]):
            if not by_path.get(path, set()) <= read:
                return False
    return True


def _pi_text(multiple: Fraction) -> str:
    r"""Return ``multiple`` times pi as math: ``\pi/8``, ``3\pi/8``, ``\pi``."""
    if multiple == 0:
        return "0"
    top = "" if abs(multiple.numerator) == 1 else str(abs(multiple.numerator))
    sign = "-" if multiple < 0 else ""
    bottom = "" if multiple.denominator == 1 else f"/{multiple.denominator}"
    return rf"{sign}{top}\pi{bottom}"


def _plate_angles(optics: Mapping[str, Any], element_id: str) -> dict[int, Any]:
    """Return each station's ``angle`` value of the element ``element_id``."""
    out: dict[int, Any] = {}
    for s in optics.get("stations") or []:
        for e in s["elements"]:
            if e["id"] == element_id:
                p = {q["name"]: q["value"] for q in e.get("parameters", [])}
                if "angle" in p:
                    out[int(s["station"]["index"])] = p["angle"]
    return out


def _plate_label(
    optics: Mapping[str, Any], element: Mapping[str, Any], station: int
) -> tuple[str, list[int]]:
    """Return the plate's label and the stations whose analyser rotation is zero.

    The list is empty where every station's plate stands at the same angle.
    """
    angles = _plate_angles(optics, str(element["id"]))
    own = angles.get(station)
    if own is None:
        return "", []
    multiples = {k: pi_multiple(v) for k, v in angles.items()}
    exact = {k: m for k, m in multiples.items() if m is not None}
    if len({radians(v) for v in angles.values()}) == 1 or not exact:
        m = multiples[station]
        text = (
            _pi_text(m)
            if m is not None
            else rf"{numeral(_math.degrees(radians(own)))}^\circ"
        )
        return text, []
    nominal = min(exact.values(), key=lambda m: (m.denominator, abs(m.numerator)))
    zero = sorted(k for k, m in exact.items() if m == nominal)
    return rf"{_pi_text(nominal)}+{SYMBOLS['rotation']}/2", zero


def _basis_choice(model: Mapping[str, Any]) -> str | None:
    """Return the id of the C1 element the channel modes enter first, if any."""
    channel = {m["label"] for m in model["modes"] if m.get("channel")}
    touching = [e for e in model["elements"] if channel & set(e["support"])]
    if not touching:
        return None
    first = min(int(e["column"]) for e in touching)
    for e in touching:
        if int(e["column"]) == first and e.get("catalogue_id") == "C1":
            return str(e["id"])
    return None


def _layout(
    model: Mapping[str, Any],
) -> tuple[list[_Placed], dict[str, tuple[Vec, Vec]], _Bench]:
    """Place the elements along the beams; return them, the beam ends and the bench.

    The channel's beam starts at the origin heading right; a beam end is its
    last point and its direction.
    """
    channel = _paths(model, [m["label"] for m in model["modes"] if m.get("channel")])
    if len(channel) != 1:
        raise ValueError("the compact figure draws one channel path")
    order = {m["label"]: i for i, m in enumerate(model["modes"])}
    elements = sorted(
        model["elements"],
        key=lambda e: (int(e["column"]), min(order.get(m, 0) for m in e["support"])),
    )
    bench = _Bench()
    heads: dict[str, tuple[Vec, Vec]] = {channel[0]: ((0.0, 0.0), (1.0, 0.0))}
    placed: list[_Placed] = []
    for e in elements:
        paths = _paths(model, e["support"])
        known = [p for p in paths if p in heads]
        new = [p for p in paths if p not in heads]
        if len(known) != 1 or len(new) > 1:
            raise ValueError(
                f"element {e['id']!r} joins beams or splits into several: the "
                "compact figure draws a tree of beams"
            )
        start, d = heads[known[0]]
        here = _add(start, d, STEP)
        bench.segments.append((start, here))
        bench.centres.append(here)
        heads[known[0]] = (here, d)
        outgoing = [d]
        for path in new:
            reach = STEP + DETECTOR_GAP + 2 * D_RADIUS
            turn = _ccw(d) if bench.clear_ray(here, _ccw(d), reach) else _cw(d)
            heads[path] = (here, turn)
            outgoing.append(turn)
        placed.append(_Placed(e, here, d, outgoing))
    return placed, heads, bench


def _glyph(p: _Placed) -> list[str]:
    """Draw one element: a cube with its splitting face, a plate, or a box."""
    catalogue = str(p.element.get("catalogue_id"))
    x, y = p.at
    if catalogue == "C3":
        dx = p.incoming[0]
        hx = PLATE_ALONG / 2 if dx else PLATE_ACROSS / 2
        hy = PLATE_ACROSS / 2 if dx else PLATE_ALONG / 2
        return [
            rf"\filldraw[draw=cqInk, fill=cqInk!55, line width=0.5pt] "
            rf"{at(x - hx, y - hy)} rectangle {at(x + hx, y + hy)};"
        ]
    half = CUBE / 2
    fill = {"C1": "white", "C2": "cqRule!45"}.get(catalogue, "white")
    dashed = "" if catalogue in ("C1", "C2") else ", dashed"
    out = [
        rf"\filldraw[draw=cqInk, fill={fill}, line width=0.6pt{dashed}] "
        rf"{at(x - half, y - half)} rectangle {at(x + half, y + half)};"
    ]
    if catalogue in ("C1", "C2"):
        if len(p.outgoing) > 1:
            # The splitting face is the mirror taking the beam into its branch:
            # its normal is the difference of the two directions.
            nx = p.outgoing[1][0] - p.incoming[0]
            ny = p.outgoing[1][1] - p.incoming[1]
            fx, fy = -ny, nx
        else:
            fx, fy = 1.0, 1.0
        scale = half / max(abs(fx), abs(fy))
        out.append(
            draw(
                LINE, (x - fx * scale, y - fy * scale), (x + fx * scale, y + fy * scale)
            )
        )
    return out


def _glyph_box(p: _Placed) -> _Box:
    x, y = p.at
    if p.element.get("catalogue_id") == "C3":
        horizontal = bool(p.incoming[0])
        hx = PLATE_ALONG / 2 if horizontal else PLATE_ACROSS / 2
        hy = PLATE_ACROSS / 2 if horizontal else PLATE_ALONG / 2
        return _Box(x - hx, y - hy, x + hx, y + hy)
    return _Box(x - CUBE / 2, y - CUBE / 2, x + CUBE / 2, y + CUBE / 2)


def _place_label(
    bench: _Bench, centre: Vec, sides: Sequence[Vec], text: str
) -> tuple[Vec, Vec]:
    """Return the anchor point and side with the most room for ``text``."""
    best: tuple[float, int, Vec, Vec] | None = None
    for rank, side in enumerate(sides):
        anchor = _add(centre, side, LABEL_GAP)
        box = _label_box(anchor, side, text)
        score = bench.room(box)
        if best is None or score > best[0] + 1e-9:
            best = (score, rank, anchor, side)
    assert best is not None
    _score, _rank, anchor, side = best
    bench.boxes.append(_label_box(anchor, side, text))
    return anchor, side


def _ports_by_path(model: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    out: dict[str, Mapping[str, Any]] = {}
    for port in model["ports"]:
        paths = _paths(model, port["modes"])
        if len(paths) != 1 or paths[0] in out:
            raise ValueError(
                f"port {port['port']!r}: the compact figure draws one detector per path"
            )
        out[paths[0]] = port
    return out


def _beams(
    model: Mapping[str, Any],
    heads: Mapping[str, tuple[Vec, Vec]],
    bench: _Bench,
) -> tuple[list[str], list[tuple[Vec, Vec, Mapping[str, Any]]]]:
    """Draw every beam, the channel's input arrow and each lead to a detector.

    Return the drawing and, per detector, its face, direction and port.
    """
    out: list[str] = []
    for a, b in list(bench.segments):
        if a == (0.0, 0.0):
            tip = _add(b, (-1.0, 0.0), CUBE / 2 + 0.03)
            out.append(draw(f"{BEAM}, -{{Stealth[length=3pt]}}", (-INPUT, 0.0), tip))
        else:
            out.append(draw(BEAM, a, b))
    out.append(
        node(
            rf"anchor=east, inner sep=1pt, font={SMALL}\itshape, text=cqMuted",
            -INPUT,
            0.0,
            "channel",
        )
    )
    bench.segments.append(((-INPUT, 0.0), (0.0, 0.0)))
    bench.boxes.append(_label_box((-INPUT, 0.0), (-1.0, 0.0), "channel"))
    ports = _ports_by_path(model)
    detectors: list[tuple[Vec, Vec, Mapping[str, Any]]] = []
    for path, (end, d) in heads.items():
        if path not in ports:
            stub = _add(end, d, STUB)
            out.append(draw(f"cqMuted, line width=0.4pt, {DASH}", end, stub))
            bench.segments.append((end, stub))
            continue
        face = _add(end, d, DETECTOR_GAP)
        out.append(draw(BEAM, end, face))
        bench.segments.append((end, face))
        detectors.append((face, d, ports[path]))
    return out, detectors


def _detectors(
    detectors: Sequence[tuple[Vec, Vec, Mapping[str, Any]]], bench: _Bench
) -> list[str]:
    """Draw each detector, its port letter inside and its efficiency beyond it."""
    out: list[str] = []
    for face, d, port in detectors:
        angle = _math.degrees(_math.atan2(d[1], d[0]))
        out.append(
            rf"\filldraw[draw=cqDetector, fill=white, line width=0.7pt, "
            rf"shift={{{at(*face)}}}, rotate={angle:.0f}] "
            rf"(0,{D_RADIUS}) -- ({D_FLAT},{D_RADIUS}) "
            rf"arc[start angle=90, end angle=-90, radius={D_RADIUS}] "
            rf"-- (0,{-D_RADIUS}) -- cycle;"
        )
        centre = _add(face, d, (D_FLAT + D_RADIUS) / 2 + 0.01)
        out.append(
            node(
                rf"inner sep=0pt, font={SMALL}\bfseries", *centre, escape(port["port"])
            )
        )
        tip = _add(face, d, D_FLAT + D_RADIUS)
        across = (abs(d[1]) * D_RADIUS, abs(d[0]) * D_RADIUS)
        bench.boxes.append(
            _Box(
                min(face[0], tip[0]) - across[0],
                min(face[1], tip[1]) - across[1],
                max(face[0], tip[0]) + across[0],
                max(face[1], tip[1]) + across[1],
            )
        )
        text = f"${efficiency_symbol(str(port['port']))}$"
        anchor = _add(tip, d, 0.02)
        bench.boxes.append(_label_box(anchor, d, text))
        out.append(node(f"anchor={_ANCHOR[d]}, {TAG}", *anchor, text))
    return out


def _element_text(
    optics: Mapping[str, Any], p: _Placed, choice: str | None, station: int
) -> tuple[str, list[int]]:
    """Return an element's symbol label and, for a plate, the zero-rotation stations."""
    e = p.element
    catalogue = e.get("catalogue_id")
    if catalogue == "C1" and str(e["id"]) == choice:
        return f"${SYMBOLS['basis_split']}$", []
    if catalogue == "C2":
        leaks = f"{SYMBOLS['pbs_leak_transmitted']}, {SYMBOLS['pbs_leak_reflected']}"
        return f"${leaks}$", []
    if catalogue == "C3":
        angle, zero_at = _plate_label(optics, e, station)
        return (f"${angle}$" if angle else ""), zero_at
    return escape(e.get("name") or e["id"]), []


def _dark_note(bench: _Bench) -> str:
    """Set the one dark-click line under the drawing, flush with its right edge.

    A legend line in a fixed place reads after the drawing, as a note does;
    one squeezed into whichever corner is free would be read first.
    """
    note = rf"all detectors: ${SYMBOLS['dark_count']}$"
    xs = [x for b in bench.boxes for x in (b.x0, b.x1)]
    ys = [y for b in bench.boxes for y in (b.y0, b.y1)]
    return node(
        f"anchor=north east, {TAG}",
        max(xs),
        min(ys) - 0.1,
        note,
    )


def _same_receiver(optics: Mapping[str, Any], model: Mapping[str, Any]) -> bool:
    """Whether every station has this receiver's elements and ports, values aside."""

    def shape(s: Mapping[str, Any]) -> tuple[Any, ...]:
        elements = sorted(
            (str(e["id"]), str(e.get("catalogue_id")), tuple(e["support"]))
            for e in s["elements"]
        )
        ports = sorted((str(p["port"]), tuple(p["modes"])) for p in s["ports"])
        return (tuple(elements), tuple(ports))

    stations = optics.get("stations") or []
    return len(stations) > 1 and all(shape(s) == shape(model) for s in stations)


def render_optics_compact(
    optics: Mapping[str, Any],
    station: int = 0,
    party_names: Mapping[str, str] | None = None,
) -> Rendered:
    """Return the receiver of ``station`` as a beam diagram labelled by symbols.

    ``party_names`` names the parties in the caption (from the protocol map's
    lanes).
    """
    model = _station(optics, station)
    placed, heads, bench = _layout(model)
    choice = _basis_choice(model)
    for p in placed:
        bench.boxes.append(_glyph_box(p))
    beams, detectors = _beams(model, heads, bench)
    drawn_detectors = _detectors(detectors, bench)

    zero_at: list[int] = []
    labels: list[str] = []
    for p in placed:
        text, zero = _element_text(optics, p, choice, station)
        zero_at += zero
        if not text:
            continue
        across = [_ccw(p.incoming), _cw(p.incoming)]
        # Free sides first, then up before down and left before right.
        sides = sorted(across, key=lambda s: (s in p.outgoing, -s[1], s[0]))
        anchor, side = _place_label(bench, p.at, sides, text)
        labels.append(node(f"anchor={_ANCHOR[side]}, {TAG}", *anchor, text))

    out: list[str] = [rf"\begin{{tikzpicture}}[font={MAIN}, line cap=round]"]
    out += beams
    for p in placed:
        out += _glyph(p)
    out += drawn_detectors
    out += labels
    out.append(_dark_note(bench))
    out.append(r"\end{tikzpicture}")

    names = party_names or {}
    party_of = {
        int(s["station"]["index"]): str(s["station"].get("party"))
        for s in optics.get("stations") or []
    }

    def who(k: int) -> str:
        return escape(names.get(party_of.get(k, ""), f"station {k}"))

    caption = _caption(
        model,
        placed,
        choice,
        [who(k) for k in zero_at],
        None if _same_receiver(optics, model) else who(station),
    )
    return Rendered("\n".join(out) + "\n", caption)


def _caption(
    model: Mapping[str, Any],
    placed: Sequence[_Placed],
    choice: str | None,
    zero_at: Sequence[str],
    only: str | None,
) -> str:
    """Write the caption: a title, what the symbols are, where the values are.

    ``only`` names the station's party where the other stations' receivers
    differ; ``None`` says that every station has this receiver.
    """
    s = {name: f"${symbol}$" for name, symbol in SYMBOLS.items()}
    ports = [str(p["port"]) for p in model["ports"]]
    etas = ", ".join(f"${efficiency_symbol(p)}$" for p in ports)
    whose = f"{only}'s receiver" if only else "Each station's receiver"
    parts = [f"{whose} in symbols; the parameter table gives their values."]
    clauses: list[str] = []
    if choice is not None:
        clauses.append(
            f"a beamsplitter of transmittance {s['basis_split']} chooses the basis"
        )
    plates = [p for p in placed if p.element.get("catalogue_id") == "C3"]
    if plates:
        clauses.append("a half-wave plate rotates the polarization of one arm")
    if any(p.element.get("catalogue_id") == "C2" for p in placed):
        whole = _ports_read_whole_paths(model)
        where = "the other detector" if whole else "no detector"
        clauses.append(
            f"polarizing splitters leak {s['pbs_leak_transmitted']} (V), "
            f"{s['pbs_leak_reflected']} (H) to {where}"
        )
    clauses.append(
        f"the detectors have efficiencies {etas} and dark-click probability "
        f"{s['dark_count']}"
    )
    text = "; ".join(clauses)
    parts.append(text[0].upper() + text[1:] + ".")
    if zero_at:
        parts.append(
            f"The analyser rotation {s['rotation']} is zero at {' and '.join(zero_at)}."
        )
    return " ".join(parts)
