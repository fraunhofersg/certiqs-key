"""Protocol documents for the optical, decoy and multi-station tests.

WHY A SUPPORT MODULE. The lowering tests cover three whole documents
-- the packaged templates
``instances/{optical_bb84,decoy_bb84,bbm92}/protocol.yaml``, which are the
instances -- and a set of COVERAGE documents, each exercising one lowering no
instance uses: the port-Gram and instrument-matrix routes, the catalogue's
C3-C10 entries, a declared dark-count matrix, a probe, a three-message
transcript, three stations, a two-station Band A. The templates are read as
packaged, from their place; each coverage document is a CUSTOM document, one
edit away from a template.

The coverage documents assert nothing about the protocol: whether the engine
accepts each one is the engine's decision, and the test checks only that a
module takes it.
"""

from __future__ import annotations

import copy
import itertools
from collections.abc import Callable
from pathlib import Path
from typing import Any

from instances.declared import DocumentSurface, load, load_packaged
from instances.declared.reader import parse_text
from probe_presence import PROBE_PRESENT
from tests.support.declared_documents import bb84_tree

ROOT = Path(__file__).resolve().parents[2]

__all__ = [
    "COVERAGE",
    "coverage_surface",
    "custom_from",
    "template_path",
    "template_surface",
    "template_tree",
]

HALF = "1/2"
QUARTER = "1/4"


def template_path(name: str) -> Path:
    """Return a packaged instance's template, ``instances/<name>/protocol.yaml``."""
    return ROOT / "instances" / name / "protocol.yaml"


def template_tree(name: str) -> dict[str, Any]:
    """Return one packaged template's parsed tree (a fresh copy)."""
    tree: dict[str, Any] = parse_text(
        template_path(name).read_text(encoding="utf-8"), syntax="yaml"
    )
    return tree


def template_surface(name: str) -> DocumentSurface:
    """Return a template as the packaged instance it reproduces, from its place."""
    return load_packaged(template_path(name))


def _custom(tree: dict[str, Any], name: str) -> dict[str, Any]:
    """Make a template's tree a custom document: its own id, no packaged strings."""
    tree["identity"] = {
        "id": name,
        "title": f"Coverage document {name}",
        "summary": "A variation of an optical instance for the lowering's coverage.",
    }
    for station in tree["stations"]:
        station.pop("declared_by", None)
    source = tree["source"]
    for key in ("record_label", "record_site", "retention_attestation"):
        source.pop(key, None)
    return tree


def custom_from(
    template: str, edit: Callable[[dict[str, Any]], None], name: str
) -> DocumentSurface:
    """Return a custom document: a template made custom, then ``edit``."""
    tree = _custom(template_tree(template), name)
    edit(tree)
    return load(tree)


def _uniform_table(tree: dict[str, Any], labels: list[str]) -> None:
    tree["honest"] = {
        "acceptance_table": dict.fromkeys(labels, f"1/{len(labels)}"),
        "source": "a uniform table, for the coverage test only",
    }


def _bob(tree: dict[str, Any]) -> dict[str, Any]:
    measurement: dict[str, Any] = tree["stations"][0]["measurement"]
    return measurement


# ---------------------------------------------------------------------------
#  The coverage documents
# ---------------------------------------------------------------------------


def port_grams(tree: dict[str, Any]) -> None:
    """Optical BB84's receiver declared by its four ideal port Grams (route i)."""
    bob = _bob(tree)
    bob["route"] = "port_grams"
    bob["elements"] = []
    bob["edges"] = []
    bob["port_grams"] = {
        "H": {"matrix": [[HALF, 0], [0, 0]]},
        "V": {"matrix": [[0, 0], [0, HALF]]},
        "D": {"matrix": [[QUARTER, QUARTER], [QUARTER, QUARTER]]},
        "A": {"matrix": [[QUARTER, "-1/4"], ["-1/4", QUARTER]]},
    }


def instrument_matrix(tree: dict[str, Any]) -> None:
    """Optical BB84's receiver declared by its instrument matrix (route ii).

    The entries are the binary64 values the ideal graph compiles to, written
    as their shortest decimals: ``1/sqrt 2`` is no exact rational, so each such
    entry reaches the receiver through a recorded conversion.
    """
    from instances.common.optics import ReceiverParameters, element_graph

    from certiqs_key.receiver.graph import compile_element_graph

    gamma = compile_element_graph(element_graph(ReceiverParameters()), 8)
    bob = _bob(tree)
    bob["route"] = "instrument_matrix"
    bob["elements"] = []
    bob["edges"] = []
    bob["instrument_matrix"] = {
        "matrix": [
            [[repr(float(z.real)), repr(float(z.imag))] for z in row] for row in gamma
        ]
    }


def catalogue(tree: dict[str, Any]) -> None:
    """Put a quarter-wave plate and catalogue entries C4 to C10 in line.

    Before the basis beamsplitter the channel path passes a quarter-wave plate
    (C3), a rotator (C4), a mirror (C5), a phase shifter (C6), a loss (C7), a
    polarizer (C8), a mode routing (C9) and a generic 2 x 2 block (C10), each
    at a parameter where it is the identity or close to it.
    """
    bob = _bob(tree)
    on_z = ["Z_H", "Z_V"]
    chain = [
        {
            "name": "qwp",
            "component": "quarter_wave",
            "params": {"angle_pi": 0, "loss": 0},
        },
        {"name": "rot", "component": "rotator", "params": {"rotation_angle_pi": 0}},
        {
            "name": "mirror",
            "component": "mirror",
            "params": {
                "reflectivity_h": 1,
                "reflectivity_v": 1,
                "phase_h_pi": 0,
                "phase_v_pi": 0,
                "handedness_flip": False,
            },
        },
        {
            "name": "phase",
            "component": "phase_shifter",
            "params": {"phases_pi": [0, "1/2"]},
        },
        {
            "name": "loss",
            "component": "loss",
            "params": {"efficiencies": ["99/100", "99/100"]},
        },
        {
            "name": "polarizer",
            "component": "polarizer",
            "params": {"angle_pi": 0, "pass_transmittance": 1, "leak_transmittance": 1},
        },
        {
            "name": "routing",
            "component": "mode_routing",
            "params": {"permutation": [0, 1]},
        },
        {
            "name": "block",
            "component": "generic_block",
            "params": {"block": {"matrix": [["0.6", 0], [0, "0.6"]]}},
        },
    ]
    for element in chain:
        element["support"] = on_z
    names = [element["name"] for element in chain]
    bob["elements"] = [*chain, *bob["elements"]]
    bob["edges"] = [
        *([a, b] for a, b in itertools.pairwise(names)),
        [names[-1], "bs"],
        *bob["edges"],
    ]


def dark_count_matrix(tree: dict[str, Any]) -> None:
    """Declare a dark-count channel ``R`` (DECLARED_MATRIX) on the 16 patterns.

    The identity channel except that the empty pattern turns into the single
    click on ``H`` with probability 1/1000: column-stochastic, and every
    multi-click column maps into the multi-clicks.
    """
    size = 16
    rows: list[list[Any]] = [[0] * size for _ in range(size)]
    for index in range(size):
        rows[index][index] = 1
    rows[0][0] = "999/1000"
    rows[1][0] = "1/1000"
    _bob(tree)["dark_count_channel"] = {"matrix": rows}


def tau_modes(tree: dict[str, Any]) -> None:
    """Every mode declared at the time-bin ``tau = 1`` (the single-value rule holds)."""
    for mode in _bob(tree)["modes"]:
        mode["tau"] = 1


def explicit_carried_operator(tree: dict[str, Any]) -> None:
    """On the licensed route, an explicit carried operator beside the library's.

    The operator is ``0 >= 0`` on the target, certified by positivity -- a
    request the reductions certify against the first pass's own channel.
    """
    reduction = tree["stations"][0]["reduction"]
    zero = {"scale": {"factor": 0, "of": {"identity": 9}}}
    reduction["cases"]["licensed"]["carried_operators"] = [
        {
            "label": "zero",
            "operator": zero,
            "relation": "ge",
            "constant": 0,
            "certificate_kind": "positivity",
        },
    ]


def generic_probe(tree: dict[str, Any]) -> None:
    """Declare a probe on the beamsplitter's free input: thermal light at ``on``."""
    bob = _bob(tree)
    bob["source_modes"] = ["X_H", "X_V"]
    bob["probe"] = {
        "settings": [
            {"label": "off", "mean_photons": [0, 0], "class_weight": "3/4"},
            {"label": "on", "mean_photons": [1, 1], "class_weight": "1/4"},
        ],
        "exact_window": {"on": 2},
        "tail_window": {"on": 2},
    }
    tree["honest"] = {
        "envelope": {
            "lower": dict.fromkeys(("gen", "ok", "err", "mis", "nc", "mc"), 0),
            "upper": dict.fromkeys(("gen", "ok", "err", "mis", "nc", "mc"), 1),
        },
        "source": "a vacuous envelope, for the coverage test only",
    }


def three_stations(tree: dict[str, Any]) -> None:
    """bbm92 with a third station of Bob's, under the run tier's restrictions.

    The partition is written as rules (Bob reads his two stations' letters
    jointly), the witness is ``none``, the channel interface ``none``, and the
    honest model a table; the stations dock as three factors.
    """
    third = copy.deepcopy(tree["stations"][1])
    third["id"] = "carol_station"
    tree["stations"].append(third)
    letters = ["nc", "H", "V", "D", "A", "mc"]
    tree["alphabets"]["bob_pair"] = {
        "product": {"dims": {"b": letters, "c": letters}, "label": "{b}+{c}"}
    }
    tree["alphabets"]["alice_letters"] = {
        "product": {
            "dims": {"letter": letters, "choice": ["gen", "test"]},
            "label": "({letter},{choice})",
        }
    }
    tree["public"]["partition"] = {
        "alice_readout": {
            "alphabet": "alice_letters",
            "map": [{"value": "{v.alice_station}"}],
        },
        "bob_readout": {
            "alphabet": "bob_pair",
            "map": [{"value": "{v.bob_station}+{v.carol_station}"}],
        },
        "sector_factor_parties": {
            "alice_station": "A",
            "bob_station": "B",
            "carol_station": "B",
        },
    }
    transcript = tree["public"]["transcript"]["messages"]
    transcript[0]["table"] = [{"value": "all"}]
    transcript[0]["alphabet"] = "derived"
    transcript[1]["table"] = [{"value": "all"}]
    transcript[1]["alphabet"] = "derived"
    tree["public"]["sifting"] = [{"value": "fail"}]
    tree["public"]["key"] = {"holder": "A", "alphabet": [0, 1], "rule": [{"value": 0}]}
    tree["public"]["acceptance"] = {"map": [{"value": "all"}]}
    tree["constraints"] = {"feasibility_witness": "none"}
    tree["channel_interface"] = {"variant": "none"}
    _uniform_table(tree, ["all"])


def wcp_two_intensities(tree: dict[str, Any]) -> None:
    """Declare a WCP source of two intensities, generating in the X basis."""
    source = tree["source"]
    source["intensities"] = source["intensities"][:2]
    source["generation"] = {"intensity": "signal", "polarisations": ["plus", "minus"]}
    source["test"]["intensity_probabilities"] = {
        "signal": {"param": "test_signal"},
        "weak": {"expr": "test_weak + test_vacuum"},
    }
    source["lattice_exponent"] = 20


# ---------------------------------------------------------------------------
#  Band-A coverage: the bb84 template's tree
# ---------------------------------------------------------------------------


def _band_a_custom(tree: dict[str, Any], name: str) -> dict[str, Any]:
    tree["identity"] = {
        "id": name,
        "title": f"Coverage document {name}",
        "summary": "A variation of qubit BB84 for the lowering's coverage tests.",
    }
    return tree


def three_message_transcript(tree: dict[str, Any]) -> None:
    """BB84 announced as a transcript of three messages.

    Alice announces her basis, Bob his basis (or his bit in X), and Alice
    then confirms whether the round is kept: the third message reads both
    earlier ones.
    """
    public = tree["public"]
    public.pop("announcements")
    tree["alphabets"]["confirm"] = {"enum": ["keep", "drop"]}
    public["transcript"] = {
        "messages": [
            {
                "id": "m1",
                "sender": "A",
                "alphabet": "ann",
                "table": [
                    {"when": {"r.basis": "Z"}, "value": "Z"},
                    {"value": "(X,{r.bit})"},
                ],
            },
            {
                "id": "m2",
                "sender": "B",
                "alphabet": "ann",
                "table": [
                    {"when": {"r.choice": "Z"}, "value": "Z"},
                    {"value": "(X,{r.outcome})"},
                ],
            },
            {
                "id": "m3",
                "sender": "A",
                "alphabet": "confirm",
                "table": [
                    {"when": {"m1": "Z", "m2": "Z"}, "value": "keep"},
                    {"value": "drop"},
                ],
            },
        ]
    }
    public["sifting"] = [{"when": {"m3": "keep"}, "value": "pass"}, {"value": "fail"}]
    public["acceptance"] = {
        "alphabet": ["gen", "ok", "err", "disc"],
        "map": [
            {"when": {"m3": "keep"}, "value": "gen"},
            {
                "when": {"m1.basis": "X", "m2.basis": "X", "m1.bit": {"eq": "m2.bit"}},
                "value": "ok",
            },
            {"when": {"m1.basis": "X", "m2.basis": "X"}, "value": "err"},
            {"value": "disc"},
        ],
    }


def two_station_band_a(tree: dict[str, Any]) -> None:
    """BBM92 as Band A: an untrusted pair source, two declared qubit stations.

    Alice's station is the bb84 template's Bob with Alice's party; the
    partition is the factor projection (each party reads its own station),
    and the two messages are the accepted format's announcements. The
    compiler decides whether its general format takes two Band-A factors;
    the test records which.
    """
    alice = copy.deepcopy(tree["stations"][0])
    alice["id"] = "alice_station"
    alice["party"] = "A"
    alice["measurement"]["choice_family"]["weights"] = {
        "Z": {"param": "alice_z"},
        "X": {"param": "alice_x"},
    }
    tree["stations"][0]["id"] = "bob_station"
    tree["stations"] = [alice, tree["stations"][0]]
    tree["source"] = {
        "kind": "untrusted",
        "alphabet": {"enum": ["x0"]},
        "transmitted_dim": 1,
        "weights": {"x0": 1},
        "states": {"x0": {"identity": 1}},
        "alice_dim": 1,
        "alice_povm": {"x0": {"identity": 1}},
    }
    public = tree["public"]
    public["partition"] = "factor_projection"
    public["announcements"]["alice"]["map"] = [
        {"when": {"x.choice": "Z"}, "value": "Z"},
        {"value": "(X,{x.outcome})"},
    ]
    public["key"]["rule"] = [{"value": {"int": "o.outcome"}}]
    tree["channel_interface"] = {"variant": "none"}
    _uniform_table(tree, ["gen", "ok", "err", "disc"])


def band_a_choice_weighting(tree: dict[str, Any]) -> None:
    """Weight Bob's declared measurement by a public coin of his own.

    The weighted labels keep the basis as ``choice`` and carry the coin's
    value as ``weighted_choice``, so the template's rules read as before.
    """
    tree["stations"][0]["choice_weighting"] = {
        "choices": ["gen", "test"],
        "settings": ["s"],
        "setting_of": [{"value": "s"}],
        "matrix": {"s|gen": "7/8", "s|test": "1/8"},
    }


#: The coverage documents: (the template, the edit).
COVERAGE: dict[str, tuple[str, Callable[[dict[str, Any]], None]]] = {
    "port_grams": ("optical_bb84", port_grams),
    "instrument_matrix": ("optical_bb84", instrument_matrix),
    "catalogue_c3_to_c10": ("optical_bb84", catalogue),
    "dark_count_matrix": ("optical_bb84", dark_count_matrix),
    "tau_modes": ("optical_bb84", tau_modes),
    "explicit_carried_operator": ("optical_bb84", explicit_carried_operator),
    "three_stations": ("bbm92", three_stations),
    "wcp_two_intensities": ("decoy_bb84", wcp_two_intensities),
    "three_message_transcript": ("bb84", three_message_transcript),
    "two_station_band_a": ("bb84", two_station_band_a),
    "band_a_choice_weighting": ("bb84", band_a_choice_weighting),
    # A document declaring a probe, where the probe-conditioning submodule is.
    **({"generic_probe": ("optical_bb84", generic_probe)} if PROBE_PRESENT else {}),
}

#: The configuration overrides a coverage document runs at, where not the defaults.
COVERAGE_CONFIG: dict[str, dict[str, Any]] = {
    "explicit_carried_operator": {"device": {"route": "licensed"}},
}


def coverage_surface(name: str) -> DocumentSurface:
    """Return one coverage document's surface."""
    base, edit = COVERAGE[name]
    if base == "bb84":
        tree = _band_a_custom(bb84_tree(), f"coverage_{name}")
        edit(tree)
        return load(tree)
    return custom_from(base, edit, f"coverage_{name}")
