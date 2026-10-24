"""The protocol as a simplified swimlane, from ``protocol_map.json``.

The interactive protocol map shows every operation. This figure keeps its rules
and drops what a column-width figure cannot carry:

* **lanes** are the view model's ``lanes``, ordered by :data:`LANE_ORDER` --
  source on the left, Eve on the right, read as the physical flow -- with any
  lane it does not name after these, in the view model's order. Each lane has
  its colour from the palette (the only figure that uses lane colours); secrecy
  is encoded by lane, and "going public" is a register moving into the Public
  lane;
* **time runs downward**, one row per step whose ``type`` is in
  :data:`STEP_TYPES`, in the view model's order. A step of another type is
  not drawn: if a drawn step follows it, its operations are folded into the
  previous drawn step's box in their own lane (the readout joins the
  measurement), and otherwise it is dropped (the post-processing band);
* **one box per lane per step**, naming its operation and the symbol its
  ``math`` defines, as :func:`~runs.bbm92_study.views.tex.math_head` reads it.
  A box of more than two operations (a measurement built from a receiver
  construction) names the last and its symbol only (the Gamma_G -> POVM chain
  belongs to another figure). Titles that
  differ only in a trailing index merge ("channel, arms 0 and 1"), and a
  title's ", party X" is dropped where the lane already says it;
* **a party's public choice** (``label_legend.choices``: its values and exact
  weights) is one line in that party's measurement box, where the station
  makes it;
* **wires never run behind a box.** A box takes the left
  :data:`BOX_SHARE` of its lane; the rest is a gutter. A register read more
  than one row below the row that writes it keeps a lifeline in its own lane's
  gutter, joined from the writer and tapped by each reader in the gap between
  rows; a register read only in the next row runs straight from the writer's
  bottom edge. Wires into one box nest (nearest source on the upper track,
  entering farthest), so they do not cross each other. A register read in
  the row that writes it is one horizontal arrow. Quantum registers are heavy
  wires with square tags, classical ones thin wires with round tags, and a
  wire takes the colour of the lane that emitted it.

What explains the figure -- the encoding, the choice weights in words, what is
folded or dropped, the pointer to the optics figure -- is in the caption
:func:`protocol_caption` writes from the same data.
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from runs.bbm92_study.views.tex import (
    MAIN,
    SMALL,
    Rendered,
    draw,
    escape,
    lane_colour,
    math,
    math_head,
    node,
    words,
)

__all__ = ["LANE_ORDER", "STEP_TYPES", "render_protocol"]

STEP_TYPES: tuple[str, ...] = (
    "source",
    "transmission",
    "measurement",
    "announcement",
    "sifting",
    "key_rule",
    "acceptance",
)
"""The step types drawn, as the whitepaper's worked example walks through them."""

LANE_ORDER: tuple[str, ...] = ("source", "alice", "public", "bob", "eve")
"""Lane ids left to right; a lane not named here follows, in the JSON's order."""

TOTAL_WIDTH = 12.4
STEP_LABEL_WIDTH = 2.0
LANE_PAD = 0.08
BOX_SHARE = 0.85
LINE_HEIGHT = 0.25
WRAP = 15
HEADER_HEIGHT = 0.62
GAP_BASE = 0.36
TRACK = 0.22
SINK = 0.7
SPREAD = 0.30
TAG_MIN_RUN = 0.75
ARROW = "-{Stealth[length=4.5pt, width=3.8pt]}"

_Key = tuple[int, str]
"""A box: its row and its lane."""


@dataclass
class _Box:
    ops: list[Mapping[str, Any]] = field(default_factory=list)
    folded: list[Mapping[str, Any]] = field(default_factory=list)


@dataclass
class _Register:
    data: Mapping[str, Any]
    producer: _Key
    consumers: list[_Key] = field(default_factory=list)

    @property
    def id(self) -> str:
        return str(self.data["id"])

    @property
    def lane(self) -> str:
        return str(self.data["lane"])

    @property
    def later(self) -> list[_Key]:
        """The readers in a later row (a same-row reader is a direct arrow)."""
        return [c for c in self.consumers if c[0] > self.producer[0]]

    @property
    def direct(self) -> list[_Key]:
        return [c for c in self.consumers if c[0] == self.producer[0]]

    @property
    def gutter(self) -> bool:
        """Whether its lifeline passes a row, and so must run in a gutter."""
        return any(c[0] > self.producer[0] + 1 for c in self.consumers)


@dataclass
class _Layout:
    """The geometry: lane columns, row bands, gutter slots, edge points."""

    lane_index: Mapping[str, int]
    lane_width: float
    slot: dict[str, float] = field(default_factory=dict)
    row_top: list[float] = field(default_factory=list)
    row_height: list[float] = field(default_factory=list)
    used: dict[tuple[_Key, str], list[float]] = field(default_factory=dict)

    @property
    def box_width(self) -> float:
        return self.lane_width * BOX_SHARE

    def left(self, lane: str) -> float:
        return STEP_LABEL_WIDTH + self.lane_index[lane] * self.lane_width

    def box_left(self, lane: str) -> float:
        return self.left(lane) + LANE_PAD

    def box_centre(self, lane: str) -> float:
        return self.box_left(lane) + self.box_width / 2

    def gutter(self, lane: str) -> tuple[float, float]:
        start = self.box_left(lane) + self.box_width
        return start, self.left(lane) + self.lane_width

    def top(self, key: _Key) -> float:
        return self.row_top[key[0]]

    def bottom(self, key: _Key) -> float:
        return self.row_top[key[0]] - self.row_height[key[0]]

    def middle(self, key: _Key) -> float:
        return self.row_top[key[0]] - self.row_height[key[0]] / 2

    def track_y(self, gap: int, index: int) -> float:
        below = self.row_top[gap] - self.row_height[gap]
        return below - GAP_BASE / 2 - TRACK * (index + 0.5) + 0.08

    def edge_point(
        self,
        key: _Key,
        edge: str,
        toward: float,
        far: bool = False,
        prefer: float | None = None,
    ) -> float:
        """Return a free ``x`` on a box's top or bottom edge.

        ``prefer`` is taken when it is on the edge and free (a straight
        in-lane wire); otherwise the point lies on the side of ``toward``, or
        away from it if ``far``.
        """
        left = self.box_left(key[1]) + SPREAD / 2
        right = self.box_left(key[1]) + self.box_width - SPREAD / 2
        grid: list[float] = []
        x = left
        while x <= right + 1e-9:
            grid.append(x)
            x += SPREAD
        taken = self.used.setdefault((key, edge), [])
        free = [g for g in grid if all(abs(g - t) > SPREAD / 2 for t in taken)] or grid
        if (
            prefer is not None
            and left - 1e-9 <= prefer <= right + 1e-9
            and all(abs(prefer - t) > SPREAD / 2 for t in taken)
        ):
            taken.append(prefer)
            return prefer
        right_side = (toward > self.box_centre(key[1])) != far
        chosen = max(free) if right_side else min(free)
        taken.append(chosen)
        return chosen


def _boxes(
    model: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], dict[_Key, _Box], list[str], list[str]]:
    """Return the drawn steps, their boxes, and the folded and dropped steps' titles."""
    steps = list(model["steps"])
    drawn_at = [i for i, s in enumerate(steps) if s.get("type") in STEP_TYPES]
    if not drawn_at:
        raise ValueError("protocol map has none of the drawn step types")
    rows: list[Mapping[str, Any]] = []
    boxes: dict[_Key, _Box] = {}
    folded: list[str] = []
    dropped: list[str] = []
    for i, step in enumerate(steps):
        drawn = step.get("type") in STEP_TYPES
        if drawn:
            rows.append(step)
        elif not rows or i > drawn_at[-1]:
            dropped.append(str(step.get("title", step["id"])))
            continue
        else:
            folded.append(str(step.get("title", step["id"])))
        for op in step["operations"]:
            box = boxes.setdefault((len(rows) - 1, str(op["lane"])), _Box())
            (box.ops if drawn else box.folded).append(op)
    return rows, boxes, folded, dropped


def _registers(model: Mapping[str, Any], boxes: Mapping[_Key, _Box]) -> list[_Register]:
    """Return the registers a drawn box emits, with the drawn boxes that read them.

    A register emitted and read only inside one box (the measurement's raw
    outcome, read by the folded readout) is internal to it and not drawn.
    """
    producer: dict[str, _Key] = {}
    readers: dict[str, list[_Key]] = {}
    for key, box in sorted(boxes.items()):
        for op in box.ops + box.folded:
            for r in op.get("outputs", []):
                producer.setdefault(str(r), key)
    for key, box in sorted(boxes.items()):
        for op in box.ops + box.folded:
            for r in op.get("inputs", []):
                found = producer.get(str(r))
                if found is not None and found != key:
                    keys = readers.setdefault(str(r), [])
                    if key not in keys:
                        keys.append(key)
    out: list[_Register] = []
    for data in model["registers"]:
        rid = str(data["id"])
        if rid not in producer:
            continue
        home = boxes[producer[rid]]
        internal = rid not in readers and any(
            rid in [str(i) for i in op.get("inputs", [])]
            for op in home.ops + home.folded
        )
        if not internal:
            reg = _Register(data, producer[rid], sorted(readers.get(rid, [])))
            if any(c[0] < reg.producer[0] for c in reg.consumers):
                raise ValueError(f"register {rid} is read before it is written")
            out.append(reg)
    return out


def _merge_titles(titles: Sequence[str]) -> list[str]:
    """Merge titles that differ only in a trailing index.

    "channel, arm 0" and "channel, arm 1" become "channel, arms 0 and 1".
    """
    found = [re.fullmatch(r"(.*\D)(\d+)", t) for t in titles]
    if len(titles) < 2 or not all(found):
        return list(titles)
    prefixes = {m.group(1) for m in found if m}
    if len(prefixes) != 1:
        return list(titles)
    prefix = prefixes.pop().rstrip()
    indices = [m.group(2) for m in found if m]
    listed = ", ".join(indices[:-1]) + " and " + indices[-1]
    return [f"{prefix}s {listed}"]


def _box_text(box: _Box, party: str | None) -> tuple[list[str], str]:
    """Return a box's wrapped title lines and its math."""
    ops = box.ops or box.folded
    titles = [str(op.get("title", op["id"])) for op in ops]
    if party:
        titles = [re.sub(rf",\s*party\s+{re.escape(party)}$", "", t) for t in titles]
    heads = [math(math_head(str(op["math"]))) for op in ops if op.get("math")]
    if len(titles) > 2:
        return textwrap.wrap(titles[-1], WRAP), heads[-1] if heads else ""
    lines = [line for t in _merge_titles(titles) for line in textwrap.wrap(t, WRAP)]
    return lines, r",\ ".join(dict.fromkeys(heads))


def _choices(model: Mapping[str, Any]) -> list[tuple[str, list[tuple[str, str]]]]:
    """Return each party's public choice: its lane and ``(value, weight)`` pairs."""
    lane_of = {lane.get("party"): str(lane["id"]) for lane in model["lanes"]}
    out = []
    for choice in (model.get("label_legend") or {}).get("choices", []):
        lane = lane_of.get(choice.get("party"))
        if lane is not None:
            pairs = [(str(a["value"]), str(a["weight"])) for a in choice["alphabet"]]
            out.append((lane, pairs))
    return out


def _lane_order(lanes: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Order the lanes by :data:`LANE_ORDER`, unknown lanes after, as given."""
    rank = {lane_id: k for k, lane_id in enumerate(LANE_ORDER)}
    indexed = list(enumerate(lanes))
    indexed.sort(key=lambda t: (rank.get(str(t[1]["id"]), len(rank)), t[0]))
    return [lane for _, lane in indexed]


@dataclass
class _Wire:
    """One register's drawing: its lifeline ``x``, join and tap tracks."""

    reg: _Register
    x: float = 0.0
    exit: float = 0.0
    join: tuple[int, int] | None = None
    taps: list[tuple[_Key, int, int]] = field(default_factory=list)


def _wires(
    registers: Sequence[_Register], layout: _Layout
) -> tuple[list[_Wire], dict[int, int]]:
    """Place every lifeline and give each join and tap its gap and track.

    Joins run in the gap below the writing row and come first in it; taps run
    in the gap above the reading row, nearest source first.
    """
    tracks: dict[int, int] = {}

    def track(gap: int) -> int:
        tracks[gap] = tracks.get(gap, 0) + 1
        return tracks[gap] - 1

    wires = [_Wire(reg) for reg in registers]
    gutters: dict[str, list[_Wire]] = {}
    for w in wires:
        if w.reg.gutter:
            gutters.setdefault(w.reg.lane, []).append(w)
    for lane, ws in gutters.items():
        start, end = layout.gutter(lane)
        for k, w in enumerate(ws):
            w.x = start + (end - start) * (k + 1) / (len(ws) + 1)
    for w in wires:
        target = w.reg.later[0] if w.reg.later else None
        toward = (
            w.x
            if w.reg.gutter
            else (
                layout.box_centre(target[1])
                if target
                else layout.box_centre(w.reg.producer[1]) + 1
            )
        )
        w.exit = layout.edge_point(w.reg.producer, "bottom", toward)
        if w.reg.gutter:
            w.join = (w.reg.producer[0], track(w.reg.producer[0]))
        else:
            w.x = w.exit
    taps = [(w, c) for w in wires for c in w.reg.later]
    taps.sort(key=lambda t: (t[1], abs(t[0].x - layout.box_centre(t[1][1]))))
    for w, c in taps:
        w.taps.append((c, c[0] - 1, track(c[0] - 1)))
    return wires, tracks


def _tag(reg: _Register, x: float, y: float) -> str:
    """Return a register's tag: square for quantum, round for classical."""
    colour = lane_colour(reg.producer[1])
    quantum = reg.data.get("type") == "quantum"
    shape = "rectangle" if quantum else "rectangle, rounded corners=2.5pt"
    width = "0.7pt" if quantum else "0.4pt"
    label = math(str(reg.data.get("math") or reg.data.get("label")))
    options = (
        f"{shape}, draw={colour}, line width={width}, fill=white, "
        f"inner xsep=1.6pt, inner ysep=1.3pt, font={SMALL}"
    )
    return node(options, x, y, rf"$\vphantom{{A'}}{label}$")


def _style(reg: _Register, arrow: bool = False) -> str:
    colour = lane_colour(reg.producer[1])
    width = "0.9pt" if reg.data.get("type") == "quantum" else "0.45pt"
    return f"draw={colour}, line width={width}" + (f", {ARROW}" if arrow else "")


def _draw_wires(wires: Sequence[_Wire], layout: _Layout) -> tuple[list[str], list[str]]:
    """Draw every lifeline with its join and taps; return wires and tags."""
    out: list[str] = []
    tags: list[str] = []
    gutter_rank: dict[str, int] = {}
    for w in wires:
        reg = w.reg
        # (length, x at the tag's place along it, y): the tag goes on the join
        # when it is long enough, else on the first long tap, at a third or two
        # thirds of its length by its track's parity, so tags of neighbouring
        # tracks do not meet.
        runs: list[tuple[float, float, float]] = []
        if w.join is not None:
            ty = layout.track_y(*w.join)
            out.append(
                draw(
                    _style(reg),
                    (w.exit, layout.bottom(reg.producer)),
                    (w.x, ty),
                    via="|-",
                )
            )
            start = ty
            runs.append((abs(w.x - w.exit), (w.x + w.exit) / 2, ty))
        else:
            start = layout.bottom(reg.producer)
        tap_ys = [layout.track_y(g, i) for _c, g, i in w.taps]
        if tap_ys:
            out.append(draw(_style(reg), (w.x, start), (w.x, min(tap_ys))))
        for c, g, i in w.taps:
            ty = layout.track_y(g, i)
            straight = not w.reg.gutter and c[1] == reg.producer[1]
            entry = layout.edge_point(
                c, "top", w.x, far=True, prefer=w.x if straight else None
            )
            if abs(entry - w.x) < 1e-9:
                out.append(
                    draw(_style(reg, arrow=True), (w.x, ty), (w.x, layout.top(c)))
                )
            else:
                out.append(
                    draw(
                        _style(reg, arrow=True),
                        (w.x, ty),
                        (entry, layout.top(c)),
                        via="-|",
                    )
                )
                share = 0.35 if i % 2 else 0.65
                runs.append((abs(entry - w.x), w.x + (entry - w.x) * share, ty))
        if not reg.consumers:
            end = start - SINK + 0.22
            out.append(draw(_style(reg, arrow=True), (w.x, start), (w.x, end)))
            tags.append(_tag(reg, w.x, start - 0.24))
            continue
        if not w.taps:
            continue
        long_runs = [run for run in runs if run[0] >= TAG_MIN_RUN]
        if long_runs:
            tags.append(_tag(reg, long_runs[0][1], long_runs[0][2]))
        elif w.reg.gutter:
            k = gutter_rank[reg.lane] = gutter_rank.get(reg.lane, -1) + 1
            tags.append(_tag(reg, w.x, start - 0.3 - 0.4 * k))
        else:
            tags.append(_tag(reg, w.x, start - 0.24))
    return out, tags


def render_protocol(model: Mapping[str, Any]) -> Rendered:
    """Return the simplified swimlane of ``model`` with its caption."""
    lanes = [dict(lane) for lane in _lane_order(model["lanes"])]
    party_of = {str(lane["id"]): lane.get("party") for lane in lanes}
    layout = _Layout(
        lane_index={str(lane["id"]): k for k, lane in enumerate(lanes)},
        lane_width=(TOTAL_WIDTH - STEP_LABEL_WIDTH) / len(lanes),
    )
    rows, boxes, folded, dropped = _boxes(model)
    registers = _registers(model, boxes)
    wires, tracks = _wires(registers, layout)

    texts = {key: _box_text(box, party_of.get(key[1])) for key, box in boxes.items()}
    notes: dict[_Key, str] = {}
    measurement = next(
        (r for r, s in enumerate(rows) if s.get("type") == "measurement"), None
    )
    if measurement is not None:
        for choice_lane, pairs in _choices(model):
            if (measurement, choice_lane) in texts:
                notes[(measurement, choice_lane)] = r"\,$\cdot$\,".join(
                    rf"{escape(v)}\,{escape(w)}" for v, w in pairs
                )
    y = -HEADER_HEIGHT
    for r in range(len(rows)):
        lines = max(
            len(t[0]) + (1 if t[1] else 0) + (1 if k in notes else 0)
            for k, t in texts.items()
            if k[0] == r
        )
        layout.row_top.append(y)
        layout.row_height.append(lines * LINE_HEIGHT + 0.16)
        y -= layout.row_height[-1] + GAP_BASE + TRACK * tracks.get(r, 0)
    bottom = layout.row_top[-1] - layout.row_height[-1] - SINK

    out: list[str] = [
        rf"\begin{{tikzpicture}}[font={MAIN}, line cap=round, line join=round]"
    ]
    for lane in lanes:
        colour = lane_colour(str(lane["id"]))
        x0 = layout.left(str(lane["id"]))
        band = f"({x0 + 0.03:.3f},{-HEADER_HEIGHT + 0.08:.3f}) rectangle "
        band += f"({x0 + layout.lane_width - 0.03:.3f},{bottom:.3f})"
        out.append(rf"\fill[{colour}!5] {band};")
        heading = (
            f"anchor=south, align=center, text width={layout.lane_width - 0.1:.3f}cm, "
            rf"inner sep=1pt, font={MAIN}\bfseries, text={colour}"
        )
        out.append(
            node(
                heading,
                x0 + layout.lane_width / 2,
                -HEADER_HEIGHT + 0.1,
                words(lane["title"]),
            )
        )
    step_label = (
        f"anchor=east, align=right, text width={STEP_LABEL_WIDTH - 0.12:.3f}cm, "
        f"inner sep=1pt, font={SMALL}"
    )
    for r, step in enumerate(rows):
        title = rf"\textbf{{{r + 1}}}\enspace {words(step['title'])}"
        out.append(
            node(step_label, STEP_LABEL_WIDTH - 0.08, layout.middle((r, "")), title)
        )

    wired, tags = _draw_wires(wires, layout)
    out += wired

    for key, (title_lines, body) in sorted(texts.items()):
        content = r"\\".join(words(t) for t in title_lines)
        if body:
            content += (r"\\" if title_lines else "") + rf"\mbox{{${body}$}}"
        if key in notes:
            content += rf"\\\mbox{{\color{{cqMuted}}{notes[key]}}}"
        options = (
            f"draw={lane_colour(key[1])}, line width=0.6pt, fill=white, "
            "rounded corners=1.5pt, anchor=north, align=center, "
            f"text width={layout.box_width - 0.08:.3f}cm, "
            f"minimum height={layout.row_height[key[0]]:.3f}cm, "
            f"inner sep=1.5pt, font={SMALL}"
        )
        out.append(node(options, layout.box_centre(key[1]), layout.top(key), content))

    for w in wires:
        for c in w.reg.direct:
            y_mid = layout.middle(c)
            rightward = layout.lane_index[c[1]] > layout.lane_index[w.reg.producer[1]]
            x_from = layout.box_left(w.reg.producer[1]) + (
                layout.box_width if rightward else 0
            )
            x_to = layout.box_left(c[1]) + (0 if rightward else layout.box_width)
            out.append(draw(_style(w.reg, arrow=True), (x_from, y_mid), (x_to, y_mid)))
            tags.append(_tag(w.reg, (x_from + x_to) / 2, y_mid))

    out += tags
    out.append(r"\end{tikzpicture}")
    caption = protocol_caption(model, lanes, rows, folded, dropped)
    return Rendered("\n".join(out) + "\n", caption)


def _series(items: Sequence[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def protocol_caption(
    model: Mapping[str, Any],
    lanes: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    folded: Sequence[str],
    dropped: Sequence[str],
) -> str:
    """Write the swimlane's caption from the same data the figure reads."""
    columns = _series([escape(lane["title"]) for lane in lanes])
    first, last = escape(rows[0]["title"]), escape(rows[-1]["title"])
    parts = [
        "The worked example's protocol as the engine compiles it.",
        f"Columns are the parties and the adversary ({columns}); rows are the "
        f"steps, from {first} to {last}, with time running downwards.",
        "A box is an operation, named with the symbol it defines; a wire is a "
        "register, heavy with a square tag for a quantum system and thin with a "
        "round tag for a classical one, coloured by the column that writes it. A "
        "register entering the Public column has been announced.",
    ]
    lane_title = {str(lane["id"]): escape(lane["title"]) for lane in lanes}
    for lane, pairs in _choices(model):
        said = _series(
            [f"{escape(v)} with probability ${escape(w)}$" for v, w in pairs]
        )
        parts.append(f"{lane_title.get(lane, escape(lane))}'s station chooses {said}.")
    if any(
        len(b.get("operations") or []) > 2
        for b in rows
        if b.get("type") == "measurement"
    ):
        parts.append(
            "Each measurement box stands for the receiver drawn in the optics figure "
            "and the POVM it defines."
        )
    if folded:
        parts.append(
            f"The {_series([escape(t).lower() for t in folded])} is part of the "
            "measurement step."
        )
    if dropped:
        parts.append(
            f"The {_series([escape(t).lower() for t in dropped])} is not shown."
        )
    return " ".join(parts)
