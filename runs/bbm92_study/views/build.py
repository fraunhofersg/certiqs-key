r"""Every figure of the worked example, from the parsed inputs, as file texts.

:func:`build` is the one entry point the command line calls: it takes the
parsed JSON of a snapshot folder (``snapshot.py`` writes one and
:func:`~runs.bbm92_study.views.snapshot.read_snapshot` reads it) and,
optionally, the parsed key-rate summaries, and returns every figure with its
proposed caption. :func:`files` turns them into the texts to write -- each figure behind
the header that names its source files and pins, each caption in a
``<name>.caption.tex`` beside it -- and :func:`preview` into a document that
shows them as the whitepaper would. Nothing here reads or writes a file, so a
test can run it on the committed snapshot and inspect what came back.

CAPTIONS, NOT ANNOTATIONS
=========================
What explains, qualifies
or gives provenance -- legend sentences, footnotes, counts of what is not
shown, pointers to other figures -- is in each figure's caption, written by
its module from the same data; the drawing keeps axis, lane and step labels,
the names of what is drawn, the values that belong to it, and direct series
labels. A caption is plain caption text for ``\caption{...}``.

WHICH DEVICE SET A FIGURE IS DRAWN FROM
=======================================
The snapshot holds the study's two device sets. A figure of one set is drawn
from the set :data:`FIGURE_SET` names: the realistic one wherever the figure
shows what a run of the study meets (the protocol, the receiver, the
statistics, the key map), the perfect one for the single-set POVM, whose
caption explains an ideal measurement. ``povm-compare`` draws both.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from runs.bbm92_study.views.devices import render_devices
from runs.bbm92_study.views.keymap import render_keymap
from runs.bbm92_study.views.keyrate import FIGURES as KEYRATE_FIGURES
from runs.bbm92_study.views.keyrate import Row, render_keyrate
from runs.bbm92_study.views.optics import render_optics
from runs.bbm92_study.views.optics_compact import render_optics_compact
from runs.bbm92_study.views.povm import render_povm
from runs.bbm92_study.views.povm_compare import render_povm_compare
from runs.bbm92_study.views.protocol import render_protocol
from runs.bbm92_study.views.snapshot import SETS
from runs.bbm92_study.views.statistics import render_statistics
from runs.bbm92_study.views.tex import Rendered, header, preamble

__all__ = [
    "FIGURE_SET",
    "PREAMBLE",
    "Figure",
    "build",
    "files",
    "preview",
    "render_all",
]

FIGURE_SET: Mapping[str, str] = {
    "protocol": "realistic",
    "optics": "realistic",
    "optics-compact": "realistic",
    "povm": "perfect",
    "statistics": "realistic",
    "keymap": "realistic",
}
"""The device set each single-set figure is drawn from."""

PREAMBLE = "views-preamble.tex"


@dataclass(frozen=True)
class Figure:
    """One figure or table: its file name, body, caption and provenance."""

    name: str
    title: str
    rendered: Rendered
    sources: list[str] = field(default_factory=list)
    pins: list[str] = field(default_factory=list)
    kind: str = "figure"
    """``"figure"`` or ``"table"``: the float the body goes into."""


def _pins(
    entry: Mapping[str, Any], record: Mapping[str, Any] | None = None
) -> list[str]:
    engine, frontend = entry["engine_pin"], entry["frontend_commit"]
    pins = [f"engine {engine} (view-model builders {frontend})"]
    if record is not None:
        pins.append(f"run record engine commit {record['engine_commit']}")
    return pins


def build(
    data: Mapping[str, Any],
    station: int = 0,
    sweeps: Mapping[str, Sequence[Row]] | None = None,
) -> tuple[list[Figure], list[str]]:
    """Return every figure, and a message for each figure skipped or qualified.

    ``data`` is :func:`~runs.bbm92_study.views.snapshot.read_snapshot`'s
    return: the snapshot and, per device set, its parsed files. ``station``
    picks the receiver drawn by the optics and POVM figures; ``sweeps`` maps
    a sweep name to its parsed ``summary.csv`` rows.
    """
    entries = data["snapshot"]["sets"]
    sets = data["sets"]
    messages: list[str] = []

    def of(figure: str) -> tuple[str, Mapping[str, Any], Mapping[str, Any]]:
        name = FIGURE_SET[figure]
        return name, sets[name], entries[name]

    _, protocol, protocol_entry = of("protocol")
    party_names = {
        str(lane["party"]): str(lane["title"])
        for lane in protocol["protocol_map"]["lanes"]
        if lane.get("party")
    }
    _, optics, optics_entry = of("optics")
    _, compact, compact_entry = of("optics-compact")
    _, povm, povm_entry = of("povm")
    _, keymap, keymap_entry = of("keymap")
    last = sets[SETS[-1]]
    normalization = next(
        (
            n
            for n in last["preparation"]["normalization"]
            if int(n["station"]) == station
        ),
        None,
    )
    out = [
        Figure(
            "protocol",
            "Protocol swimlane",
            render_protocol(protocol["protocol_map"]),
            [protocol["files"]["protocol_map"]],
            _pins(protocol_entry),
        ),
        Figure(
            "optics",
            f"Receiver mode circuit, station {station}",
            render_optics(
                optics["optics"],
                station=station,
                device=optics["preparation"].get("device"),
                party_names=party_names,
            ),
            [
                optics["files"]["optics"],
                optics["files"]["preparation"] + " (detector values)",
            ],
            _pins(optics_entry),
        ),
        Figure(
            "optics-compact",
            f"Receiver beam diagram labelled by symbols, station {station}",
            render_optics_compact(
                compact["optics"], station=station, party_names=party_names
            ),
            [compact["files"]["optics"], "runs/bbm92_study/views/devices.py (symbols)"],
            _pins(compact_entry),
        ),
        Figure(
            "devices",
            "Device parameters, perfect and realistic (the body of a table float)",
            render_devices(),
            ["runs/bbm92_study/sweeps.py (REALISTIC)"],
            ["engine not involved: the values declared in the sweeps"],
            kind="table",
        ),
        Figure(
            "povm",
            f"POVM, station {station}",
            render_povm(povm["povm"], station=station),
            [povm["files"]["povm"]],
            _pins(povm_entry),
        ),
        Figure(
            "povm-compare",
            f"POVM, station {station}, " + " and ".join(SETS) + " side by side",
            render_povm_compare(
                {name: sets[name]["povm_dark"] for name in SETS},
                normalization=normalization,
                station=station,
                party_names=party_names,
            ),
            [sets[name]["files"]["povm_dark"] for name in SETS]
            + [last["files"]["preparation"] + " (normalization)"],
            _pins(entries[SETS[-1]]),
        ),
    ]
    name, stats, stats_entry = of("statistics")
    record = stats["record_extract"]
    if record is None:
        messages.append(
            f"statistics: skipped, the {name} set names no record extract "
            "(snapshot.json)"
        )
    else:
        if not str(record["engine_commit"]).startswith(stats_entry["engine_pin"]):
            messages.append(
                f"statistics: the {name} set's record extract "
                f"({stats['files']['record_extract']}) is from engine "
                f"{str(record['engine_commit'])[:8]}, not the set's pin "
                f"{stats_entry['engine_pin']}: a placeholder until the set's run"
            )
        out.append(
            Figure(
                "statistics",
                "Honest statistics and the acceptance box",
                render_statistics(record),
                [
                    stats["files"]["record_extract"]
                    + f" (from {record['origin']['record']})"
                ],
                _pins(stats_entry, record),
            )
        )
    out.append(
        Figure(
            "keymap",
            "Sifting and the key map (the body of a table float)",
            render_keymap(keymap["protocol_map"]),
            [keymap["files"]["protocol_map"]],
            _pins(keymap_entry),
            kind="table",
        )
    )
    if sweeps is not None:
        drawn, skipped = render_keyrate(sweeps)
        messages += [f"key rate: {m}" for m in skipped]
        for spec in KEYRATE_FIGURES:
            if spec.name in drawn:
                rendered, pins = drawn[spec.name]
                out.append(
                    Figure(
                        spec.name,
                        f"Key rate, {spec.figure} ({spec.sweep} sweep)",
                        rendered,
                        [f"{spec.sweep}/summary.csv"],
                        pins,
                        kind=spec.kind,
                    )
                )
    return out, messages


def files(figures: Sequence[Figure]) -> dict[str, str]:
    """Return ``{file name: text}``: the preamble, each figure and its caption."""
    out: dict[str, str] = {PREAMBLE: preamble()}
    for f in figures:
        out[f"{f.name}.tex"] = header(f.title, f.sources, f.pins) + f.rendered.body
        out[f"{f.name}.caption.tex"] = f.rendered.caption + "\n"
    return out


def render_all(
    data: Mapping[str, Any],
    station: int = 0,
    sweeps: Mapping[str, Sequence[Row]] | None = None,
) -> dict[str, str]:
    """Return the files of :func:`build`'s figures (see :func:`files`)."""
    return files(build(data, station, sweeps)[0])


def preview(figures: Sequence[Figure], bibliography: str | None = None) -> str:
    r"""Return a document that shows every figure as the whitepaper would.

    Its preamble mirrors the whitepaper's (T1 fonts, British
    babel, the AMS packages, xcolor and TikZ with ``arrows.meta``) plus the
    two packages the figures add, ``pgfplots`` and ``booktabs``. Each figure
    sits in its float with its proposed caption. ``bibliography`` is the path
    of ``refs/references.bib`` from the output folder; given, the captions'
    ``\cite`` keys resolve as in the whitepaper, which loads the same file
    with the same biblatex options.
    """
    body: list[str] = []
    for f in figures:
        caption = rf"\caption{{{f.rendered.caption}}}"
        if f.kind == "table":
            body += [
                r"\begin{table}[!htbp]",
                r"\centering",
                caption,
                r"\smallskip",
                rf"\input{{{f.name}}}",
                r"\end{table}",
            ]
        else:
            body += [
                r"\begin{figure}[!htbp]",
                r"\centering",
                rf"\input{{{f.name}}}",
                caption,
                r"\end{figure}",
            ]
        body.append(r"\clearpage")
    return "\n".join(
        [
            "% views-preview.tex: generated by runs.bbm92_study.views --preview.",
            "% The preamble mirrors the whitepaper's, plus pgfplots",
            "% and booktabs, which the figures need.",
            r"\documentclass[11pt]{article}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage[british]{babel}",
            r"\usepackage{csquotes}",
            r"\usepackage{amsmath,amssymb}",
            r"\usepackage{graphicx}",
            r"\usepackage{xcolor}",
            r"\usepackage{tikz}",
            r"\usetikzlibrary{arrows.meta}",
            r"\usepackage{pgfplots}",
            r"\usepackage{booktabs}",
            *(
                [
                    r"\usepackage[style=authoryear,backend=biber,maxcitenames=2]"
                    r"{biblatex}",
                    rf"\addbibresource{{{bibliography}}}",
                ]
                if bibliography
                else []
            ),
            rf"\input{{{PREAMBLE}}}",
            r"\begin{document}",
            *body,
            *([r"\printbibliography"] if bibliography else []),
            r"\end{document}",
            "",
        ]
    )
