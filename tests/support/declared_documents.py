"""Protocol documents for the lowering tests: bb84's, and custom variations of it.

WHY A SUPPORT MODULE. The lowering tests need the bb84 document
(the packaged template ``instances/bb84/protocol.yaml``) read as the packaged
instance it reproduces, and a handful of CUSTOM documents that each exercise
one lowering the qubit instance does not: a Y basis, a three-letter key
alphabet, an ensemble presentation, a block certificate, an explicit
partition, explicit constraint entries with a licence, a three-outcome
declared POVM, an untrusted source. Each custom document is the bb84 tree with
one change, written here once so that the coverage test and the report tests
read the same documents.

The coverage documents assert nothing about the protocol: whether the engine
accepts each one is the engine's decision, and the test checks only that it is
taken by a module.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

from instances.declared import DocumentSurface, load, load_packaged
from instances.declared.reader import parse_text

ROOT = Path(__file__).resolve().parents[2]
BB84_DOCUMENT = ROOT / "instances" / "bb84" / "protocol.yaml"

__all__ = [
    "BB84_DOCUMENT",
    "COVERAGE",
    "bb84_surface",
    "bb84_tree",
    "custom",
    "declaring_everything",
]

HALF = "1/2"
#: The Y-basis projectors of Eq. ``eq:ystates``, ``[re, im]`` entries.
P_Y0 = {"matrix": [[HALF, [0, "-1/2"]], [[0, HALF], HALF]]}
P_Y1 = {"matrix": [[HALF, [0, HALF]], [[0, "-1/2"], HALF]]}
PHI_PLUS = {"outer": {"vector": [1, 0, 0, 1], "squared_norm": 2}}
SIGNALS = ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")


def bb84_tree() -> dict[str, Any]:
    """Return the bb84 document's parsed tree (a fresh copy)."""
    tree: dict[str, Any] = parse_text(
        BB84_DOCUMENT.read_text(encoding="utf-8"), syntax="yaml"
    )
    return tree


def bb84_surface() -> DocumentSurface:
    """Return the bb84 template as the packaged instance it is.

    It carries the packaged id ``bb84`` and the ``record_label`` ``bb84`` (the
    instance string bb84's honest note records), which only a packaged
    document may write, so it is read as one: from its place,
    ``instances/bb84/protocol.yaml``.
    """
    return load_packaged(BB84_DOCUMENT)


def custom(edit: Callable[[dict[str, Any]], None], name: str) -> DocumentSurface:
    """Return a custom document: the bb84 tree as a custom one, then ``edit``."""
    tree = bb84_tree()
    tree["identity"] = {
        "id": name,
        "title": f"Coverage document {name}",
        "summary": "A variation of qubit BB84 for the lowering's coverage tests.",
    }
    edit(tree)
    return load(tree)


def _table_honest(tree: dict[str, Any], labels: list[str]) -> None:
    """Replace the library model by a uniform acceptance table over ``labels``."""
    share = f"1/{len(labels)}"
    tree["honest"] = {
        "acceptance_table": dict.fromkeys(labels, share),
        "source": "a uniform table, for the coverage test only",
    }


def y_basis(tree: dict[str, Any]) -> None:
    """Replace the X basis by the Y basis, whose states are genuinely complex."""
    tree["alphabets"]["signal"]["product"]["dims"]["basis"] = ["Z", "Y"]
    ann = tree["alphabets"]["ann"]["union"][1]
    ann["product"]["label"] = "(Y,{bit})"
    ann["attrs"] = {"basis": "Y"}
    source = tree["source"]
    source["weights"] = {
        "(Z,0)": {"expr": "alice_z / 2"},
        "(Z,1)": {"expr": "alice_z / 2"},
        "(Y,0)": {"expr": "alice_x / 2"},
        "(Y,1)": {"expr": "alice_x / 2"},
    }
    states = source["states"]
    source["states"] = {
        "(Z,0)": states["(Z,0)"],
        "(Z,1)": states["(Z,1)"],
        "(Y,0)": P_Y0,
        "(Y,1)": P_Y1,
    }
    for family in (
        source["alice"]["choice_family"],
        tree["stations"][0]["measurement"]["choice_family"],
    ):
        family["choices"] = ["Z", "Y"]
        family["weights"] = {"Z": family["weights"]["Z"], "Y": family["weights"]["X"]}
        family["conditional_alphabets"] = {"Z": [0, 1], "Y": [0, 1]}
    elements = tree["stations"][0]["measurement"]["choice_family"]
    elements["conditional_elements"] = {
        "Z": elements["conditional_elements"]["Z"],
        "Y": {"0": P_Y0, "1": P_Y1},
    }
    public = tree["public"]
    public["announcements"]["alice"]["map"][1]["value"] = "(Y,{x.bit})"
    public["announcements"]["bob"]["map"][1]["value"] = "(Y,{v.outcome})"
    for rule in public["acceptance"]["map"]:
        for key in ("A.basis", "B.basis"):
            if rule.get("when", {}).get(key) == "X":
                rule["when"][key] = "Y"


def three_letter_key(tree: dict[str, Any]) -> None:
    """Declare the key alphabet ``{0, 1, 2}``; the key map still lands in it."""
    tree["public"]["key"]["alphabet"] = [0, 1, 2]


def ensemble_presentation(tree: dict[str, Any]) -> None:
    """Declare the source by its ensemble presentation: no ``A``, no ``{M_x}``."""
    source = tree["source"]
    for key in ("alice_dim", "alice", "alice_marginal"):
        del source[key]
    source["certificate"] = {
        "form": "ensemble_presentation",
        "virtual_sectors": {
            "labels": ["t0"],
            "dims": [2],
            "block_kind": "proof_sector",
        },
        "weighted_blocks": {
            label: [
                {"scale": {"factor": {"expr": "1/4"}, "of": source["states"][label]}}
            ]
            for label in SIGNALS
        },
    }
    _table_honest(tree, ["gen", "ok", "err", "disc"])


def block_certificate(tree: dict[str, Any]) -> None:
    """Declare the certificate in block form, one sector on each side."""
    source = tree["source"]
    sectors = {"labels": ["t0"], "dims": [2], "block_kind": "proof_sector"}
    source["certificate"] = {
        "form": "block",
        "alice_sectors": sectors,
        "virtual_sectors": sectors,
        "alice_marginal_blocks": [source["alice_marginal"]],
        "psi_blocks": [PHI_PLUS],
        "virtual_weights": dict.fromkeys(SIGNALS, "1/4"),
        "virtual_blocks": {
            label: [{"scale": {"factor": "1/4", "of": source["states"][label]}}]
            for label in SIGNALS
        },
    }


def explicit_partition(tree: dict[str, Any]) -> None:
    """Write the party partition as rules, with a factor party for ``s0``."""
    tree["alphabets"]["outcome"] = {
        "product": {
            "dims": {"choice": ["Z", "X"], "outcome": [0, 1]},
            "label": "({choice},{outcome})",
        }
    }
    tree["public"]["partition"] = {
        "alice_readout": {"alphabet": "signal", "map": [{"value": "{x}"}]},
        "bob_readout": {"alphabet": "outcome", "map": [{"value": "{v}"}]},
        "sector_factor_parties": {"s0": "B"},
    }


def three_outcome_povm(tree: dict[str, Any]) -> None:
    """Give Bob a direct three-outcome POVM: two Z halves and one unresolved."""
    tree["stations"][0]["measurement"] = {
        "kind": "declared_povm",
        "dimension": 2,
        "povm": {
            "0": {"matrix": [[HALF, 0], [0, 0]]},
            "1": {"matrix": [[0, 0], [0, HALF]]},
            "n": {"matrix": [[HALF, 0], [0, HALF]]},
        },
    }
    tree["alphabets"]["bob_ann"] = {"enum": ["Z", "N"]}
    public = tree["public"]
    public["announcements"]["bob"] = {
        "alphabet": "bob_ann",
        "map": [{"when": {"v": ["0", "1"]}, "value": "Z"}, {"value": "N"}],
    }
    public["acceptance"] = {
        "alphabet": ["gen", "disc"],
        "map": [{"when": {"A": "Z", "B": "Z"}, "value": "gen"}, {"value": "disc"}],
    }


def untrusted_source(tree: dict[str, Any]) -> None:
    """Declare an untrusted source at ``d_A = 1``: one letter, a trivial POVM."""
    tree["alphabets"]["one"] = {"enum": [{"label": "x0", "basis": "Z", "bit": "0"}]}
    tree["source"] = {
        "kind": "untrusted",
        "alphabet": "one",
        "transmitted_dim": 2,
        "weights": {"x0": 1},
        "states": {"x0": {"scale": {"factor": HALF, "of": {"identity": 2}}}},
        "alice_dim": 1,
        "alice_povm": {"x0": {"identity": 1}},
    }
    _table_honest(tree, ["gen", "ok", "err", "disc"])


def declaring_everything(tree: dict[str, Any]) -> None:
    """Every user-declared kind at once.

    A retention attestation, an explicit constraint entry with its licence, an
    explicit feasibility witness, and the declared receiver POVM every Band-A
    document has.
    """
    tree["source"]["retention_attestation"] = {
        "attested_by": "declared.coverage_lab",
        "statement": "Alice's lab keeps the virtual system until the end.",
    }
    tree["constraints"] = {
        "entries": [
            {
                "label": "unit_trace",
                "operator": {"blocks": {"s0": {"identity": 2}}},
                "relation": "eq",
                "rhs": 1,
            }
        ],
        "attack_set_license": {"statement": "Every attack keeps tr rho_Q = 1."},
        "feasibility_witness": {"blocks": [PHI_PLUS]},
    }


#: The coverage documents, by name.
COVERAGE: dict[str, Callable[[dict[str, Any]], None]] = {
    "y_basis": y_basis,
    "three_letter_key": three_letter_key,
    "ensemble_presentation": ensemble_presentation,
    "block_certificate": block_certificate,
    "explicit_partition": explicit_partition,
    "explicit_entries_with_licence": declaring_everything,
    "three_outcome_povm": three_outcome_povm,
    "untrusted_source": untrusted_source,
}


def coverage_surface(name: str) -> DocumentSurface:
    """Return one coverage document's surface."""
    return custom(copy.deepcopy(COVERAGE[name]), f"coverage_{name}")
