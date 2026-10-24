"""The generated JSON Schema is current and agrees with the models; load checks.

``protocol-document.schema.json`` is a VIEW of ``instances/declared/model.py``
(PRINCIPLES.md section 7), so the committed file must be byte-for-byte what
``python -m instances.declared.schema`` writes. The schema and the models must
also agree on a whole document: the hand-written custom BB84 fixture validates
under both, and an unknown key is refused by both. The last tests are the
load-time checks a whole document gets beyond its shape: every reference
resolves, and the station mix, topology and source-and-station pairing are
ones the run tier has a route for.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from instances.declared import DocumentError, DocumentReason, load, load_packaged
from instances.declared.reader import canonicalize, parse_text
from instances.declared.schema import SCHEMA_PATH, main, schema, schema_text

CUSTOM = (
    Path(__file__).resolve().parent / "fixtures" / "declared" / "custom_qubit_bb84.yaml"
)
DOCUMENTS = Path(__file__).resolve().parents[2] / "instances"


def _custom() -> dict[str, Any]:
    tree, _ = canonicalize(parse_text(CUSTOM.read_text(encoding="utf-8")))
    return tree


def test_the_committed_schema_is_current() -> None:
    assert SCHEMA_PATH.read_bytes() == schema_text().encode("utf-8"), (
        "run python -m instances.declared.schema"
    )
    assert main(["--check"]) == 0


def test_the_schema_is_a_valid_draft_2020_12_schema() -> None:
    jsonschema.Draft202012Validator.check_schema(schema())
    assert (
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["additionalProperties"]
        is False
    )


def test_models_and_schema_agree_on_a_whole_document() -> None:
    tree = _custom()
    validator = jsonschema.Draft202012Validator(schema())
    validator.validate(tree)
    assert load(tree).DESCRIPTOR.id == "custom_qubit_bb84"
    for edit in (
        lambda t: t["stations"][0]["reduction"].update(colour="teal"),
        lambda t: t.update(extra={}),
        lambda t: t["public"]["acceptance"]["cases"]["merged"].update(alphabett=[]),
    ):
        broken = copy.deepcopy(tree)
        edit(broken)
        assert not validator.is_valid(broken)
        with pytest.raises(DocumentError) as caught:
            load(broken)
        assert caught.value.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION


def _refused(edit: Any) -> DocumentError:
    tree = _custom()
    edit(tree)
    with pytest.raises(DocumentError) as caught:
        load(tree)
    return caught.value


def test_every_reference_resolves_at_load() -> None:
    error = _refused(
        lambda t: t["source"]["weights"].update({"(Z,0)": {"param": "alice_y"}})
    )
    assert error.reason is DocumentReason.UNKNOWN_PARAMETER_REFERENCE
    assert error.path == "/source/weights/(Z,0)"
    error = _refused(
        lambda t: t["source"]["weights"].update({"(Z,0)": {"expr": "alice_z / qber_"}})
    )
    assert error.reason is DocumentReason.UNKNOWN_PARAMETER_REFERENCE
    error = _refused(lambda t: t["public"]["acceptance"].update(switch="qber"))
    assert error.reason is DocumentReason.VALUE_KIND_MISMATCH
    assert error.path == "/public/acceptance/switch"
    error = _refused(lambda t: t["honest"].update(station="charlie"))
    assert error.reason is DocumentReason.STATION_REFERENCE_UNKNOWN
    error = _refused(lambda t: t["alphabets"]["signal"]["product"].update(label="x"))
    assert error.reason is DocumentReason.ALPHABET_LABELS_NOT_DISTINCT
    error = _refused(
        lambda t: t["parameters"]["table"].append(t["parameters"]["table"][0])
    )
    assert error.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION
    error = _refused(
        lambda t: t["parameters"]["table"][0].update(applies_when={"nothing": ["x"]})
    )
    assert error.reason is DocumentReason.UNKNOWN_PARAMETER_REFERENCE
    error = _refused(
        lambda t: t["parameters"]["table"][0].update(
            applies_when={"acceptance_map": ["x"]}
        )
    )
    assert error.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION
    error = _refused(lambda t: t["snap"]["groups"].append(["qber"]))
    assert error.reason is DocumentReason.UNKNOWN_PARAMETER_REFERENCE
    error = _refused(lambda t: t["run_defaults"].update(rounds="alice_z * 100"))
    assert error.reason is DocumentReason.UNKNOWN_PARAMETER_REFERENCE
    error = _refused(lambda t: t["run_defaults"].update(rounds="10000/3"))
    assert error.reason is DocumentReason.EXPRESSION_NOT_INTEGRAL
    error = _refused(lambda t: t["presets"][0]["device"].update(qber="1/3"))
    assert error.reason is DocumentReason.UNKNOWN_PARAMETER_REFERENCE


def _optical(station: dict[str, Any]) -> dict[str, Any]:
    return {
        **station,
        "measurement": {
            "kind": "optical",
            "modes": [
                {"path": "Z", "polarization": "H"},
                {"path": "Z", "polarization": "V"},
            ],
            "channel_modes": ["Z_H", "Z_V"],
            "route": "element_graph",
            "ports": [
                {"label": "H", "modes": ["Z_H"]},
                {"label": "V", "modes": ["Z_V"]},
            ],
            "detectors": [
                {"port": "H", "efficiency": 1, "dark_count": 0},
                {"port": "V", "efficiency": 1, "dark_count": 0},
            ],
            "coarse_graining": {
                "letters": [
                    {"label": "nc"},
                    {"label": "H"},
                    {"label": "V"},
                    {"label": "mc"},
                ],
                "map": [{"when": {"count": "0"}, "value": "nc"}, {"value": "mc"}],
            },
            "photon_cutoff": 1,
        },
    }


def test_station_mix_and_topology() -> None:
    error = _refused(
        lambda t: t["stations"].append(_optical({**t["stations"][0], "id": "eve"}))
    )
    assert error.reason is DocumentReason.STATION_KINDS_MIXED

    def three(tree: dict[str, Any]) -> None:
        first = tree["stations"][0]
        tree["stations"].extend([{**first, "id": "carol"}, {**first, "id": "dave"}])

    error = _refused(three)
    assert error.reason is DocumentReason.UNSUPPORTED_TOPOLOGY
    assert error.path == "/public/partition"
    error = _refused(
        lambda t: (three(t), t["public"].update(partition="factor_projection"))
    )
    assert error.reason is DocumentReason.UNSUPPORTED_TOPOLOGY
    error = _refused(lambda t: t["stations"].append({**t["stations"][0], "id": "bob"}))
    assert error.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION


def _decoy_band_a(stations: int) -> dict[str, Any]:
    """Return decoy_bb84's ``wcp_decoy`` source beside bb84's declared POVM station(s).

    The rest is cut down to what such a document needs (the decoy parameters,
    a two-message transcript, an acceptance table), so that the pairing is
    the one thing refused: without the load check this document reaches the
    compiler with a chain that carries no source segment.
    """
    tree: dict[str, Any] = parse_text(
        (DOCUMENTS / "decoy_bb84" / "protocol.yaml").read_text(encoding="utf-8"),
        syntax="yaml",
    )
    bb84 = parse_text(
        (DOCUMENTS / "bb84" / "protocol.yaml").read_text(encoding="utf-8"),
        syntax="yaml",
    )
    tree["identity"] = {"id": "decoy_band_a", "title": "t", "summary": "s"}
    for key in ("record_site", "record_label"):
        tree["source"].pop(key)
    tree["source"]["retention_attestation"]["attested_by"] = "test"
    station = copy.deepcopy(bb84["stations"][0])
    station["measurement"]["choice_family"]["weights"] = {"Z": "1/2", "X": "1/2"}
    tree["stations"] = [
        {**copy.deepcopy(station), "id": "bob" if index == 0 else f"bob{index}"}
        for index in range(stations)
    ]
    keep = {
        "gamma",
        "mu_signal",
        "mu_weak",
        "mu_vacuum",
        "test_signal",
        "test_weak",
        "test_vacuum",
        "entropy_cutoff",
        "source_cutoff",
    }
    tree["parameters"]["table"] = [
        row for row in tree["parameters"]["table"] if row["name"] in keep
    ]
    tree.pop("presets", None)
    for key in ("derived", "derived_timing"):
        tree["run_defaults"].pop(key)
    choice = "{r.choice}" if stations == 1 else "{r.bob.choice}"
    tree["public"] = {
        "partition": "default",
        "transcript": {
            "messages": [
                tree["public"]["transcript"]["messages"][0],
                {
                    "id": "m2",
                    "sender": "B",
                    "alphabet": "derived",
                    "table": [{"value": {"label": choice}}],
                },
            ]
        },
        "sifting": [
            {"when": {"m1": "gen-Z", "m2": "Z"}, "value": "pass"},
            {"value": "fail"},
        ],
        "key": {
            "holder": "A",
            "alphabet": [0, 1],
            "rule": [{"when": {"o.polarisation": "V"}, "value": 1}, {"value": 0}],
        },
        "acceptance": {
            "alphabet": ["gen", "disc"],
            "map": [
                {"when": {"m1": "gen-Z", "m2": "Z"}, "value": "gen"},
                {"value": "disc"},
            ],
        },
    }
    tree["honest"] = {
        "acceptance_table": {"gen": "1/2", "disc": "1/2"},
        "source": "test",
    }
    del tree["channel_interface"]
    return tree


@pytest.mark.parametrize("stations", [1, 2], ids=["one-station", "several-stations"])
def test_a_wcp_decoy_source_beside_declared_povm_stations_is_refused_at_load(
    stations: int,
) -> None:
    """The Band-A lowering docks no source segment, so the pairing is refused.

    The refusal is the document's own reason, at load, naming the pairing;
    the document never reaches the compiler, whose source-segment check
    would otherwise report a provenance failure that did not happen.
    """
    with pytest.raises(DocumentError) as caught:
        load(_decoy_band_a(stations))
    error = caught.value
    assert error.reason is DocumentReason.WCP_DECOY_NEEDS_OPTICAL_STATIONS
    assert error.path == "/stations"
    assert "wcp_decoy" in error.detail
    assert "optical stations" in error.detail
    # Controls: the source beside its optical station, and the declared POVM
    # station beside its trusted source, each load as the templates they are.
    for template in ("decoy_bb84", "bb84"):
        path = DOCUMENTS / template / "protocol.yaml"
        assert load_packaged(path).DESCRIPTOR.id == template


def _decoy_two_optical(party: str) -> dict[str, Any]:
    """Return decoy_bb84 with a second optical receiver, otherwise runnable.

    Beside the second station (decoy_bb84's own receiver again, of
    ``party``) the document is cut to what two stations need: Bob's message
    reads the first station's letter, the acceptance is two values with a
    raw honest table, and the channel interface is ``bipartite``. Without
    the load check this document prepares up to the compiler, which refuses
    it with ``source_segment_not_from_admitting_module`` (the several-station
    lowering docks no source segment; probed for
    instances/decoy-source-several-optical-stations).
    """
    tree: dict[str, Any] = parse_text(
        (DOCUMENTS / "decoy_bb84" / "protocol.yaml").read_text(encoding="utf-8"),
        syntax="yaml",
    )
    tree["identity"] = {"id": "decoy_two_stations", "title": "t", "summary": "s"}
    for key in ("record_site", "record_label"):
        tree["source"].pop(key)
    tree["source"]["retention_attestation"]["attested_by"] = "test"
    station = tree["stations"][0]
    del station["declared_by"]
    tree["stations"].append({**copy.deepcopy(station), "id": "bob2", "party": party})
    tree["public"]["transcript"]["messages"][1]["table"] = [
        {
            "when": {"m1.round": "gen", "r.bob.letter": ["H", "V", "D", "A"]},
            "value": "{r.bob.basis}",
        },
        {"value": "{r.bob.letter}"},
    ]
    tree["public"]["acceptance"] = {
        "map": [
            {"when": {"m1": "gen-Z", "m2": "Z"}, "value": "gen"},
            {"value": "disc"},
        ]
    }
    tree["honest"] = {
        "acceptance_table": {"gen": "1/2", "disc": "1/2"},
        "source": "test",
    }
    tree["channel_interface"] = {"variant": "bipartite"}
    return tree


@pytest.mark.parametrize("party", ["B", "A"])
def test_a_wcp_decoy_source_beside_several_optical_stations_is_refused_at_load(
    party: str,
) -> None:
    """Only the one-station optical lowering docks a decoy source's segment.

    The several-station provider builds each station's chain without the
    source segment, so the pairing is refused at load with its own reason,
    naming it; the document never reaches the compiler's provenance check.
    """
    with pytest.raises(DocumentError) as caught:
        load(_decoy_two_optical(party))
    error = caught.value
    assert error.reason is DocumentReason.WCP_DECOY_NEEDS_ONE_OPTICAL_STATION
    assert error.path == "/stations"
    assert "wcp_decoy" in error.detail
    assert "exactly one optical station" in error.detail
    # Control: the same document with its one station is not refused for
    # the pairing (decoy_bb84 itself loads in the test above).
    tree = _decoy_two_optical(party)
    del tree["stations"][1]
    assert load(tree).DESCRIPTOR.id == "decoy_two_stations"


def test_annotations_are_opaque() -> None:
    tree = _custom()
    tree["annotations"] = {"anything": {"param": "not_a_parameter", "x": [1.5, None]}}
    surface = load(tree)
    assert surface.canonical["annotations"]["anything"]["param"] == "not_a_parameter"


def test_a_misspelt_switch_case_is_refused() -> None:
    error = _refused(
        lambda t: t["public"]["acceptance"]["cases"].update(
            merged_test=t["public"]["acceptance"]["cases"]["merged"]
        )
    )
    assert error.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION
    assert error.path == "/public/acceptance/cases/merged_test"


def test_a_static_value_may_be_an_expression_of_no_name() -> None:
    tree = _custom()
    tree["presets"][0]["device"] = {"alice_z": {"expr": "3/4"}, "alice_x": "2^-2"}
    preset = load(tree).PRESETS[0]
    assert preset.as_payload()["device"] == {"alice_z": "3/4", "alice_x": "1/4"}
    error = _refused(
        lambda t: t["presets"][0]["device"].update(alice_z={"expr": "1 - alice_x"})
    )
    assert error.reason is DocumentReason.UNKNOWN_PARAMETER_REFERENCE


def test_the_schema_describes_itself_and_its_subtle_fields() -> None:
    generated = schema()
    assert "do not edit" in generated["description"]
    defs = generated["$defs"]
    for model, field in (
        ("RunDefaults", "derived_timing"),
        ("RunDefaults", "sections"),
        ("Parameters", "check_order"),
        ("ParameterRow", "per_port_of"),
        ("Preparation", "rebind"),
        ("TranscriptMessage", "alphabet"),
        ("BeamsplitterParams", "phase_pi"),
    ):
        assert defs[model]["properties"][field].get("description"), (model, field)
    assert "design" not in json.dumps(
        {name: d.get("description", "") for name, d in defs.items()}
    )
