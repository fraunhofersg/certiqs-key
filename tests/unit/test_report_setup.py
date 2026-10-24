"""The report's "Your QKD setup" (report 0.8.0; design section 2 of report v2).

Each receiver route is read on a real committed record where one exists
(``runs/report_examples/``: element graph per station in ``bbm92``, a single
element graph in ``optical_bb84``, a declared finite POVM in ``bb84``, port
Grams in ``document-optical_bb84_port_grams``); no committed record takes the
instrument-matrix route, so that one is a SYNTHETIC record derived from the
port-Gram one, with the expectation written by hand. The basis labels are
pinned against facts independent of the labelling code: the receiver's
occupation-vector order (:func:`certiqs_key.receiver.fock.occupation_vectors`)
and the port map, which says which channel mode each detector collects.
"""

from __future__ import annotations

import copy
import gzip
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from tests.support.report_records import completed_record, refused_record

from certiqs_key.receiver.fock import occupation_vectors
from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_markdown,
    report_schema,
)
from certiqs_key.runs.report.model import OperatorFamily, SetupStation
from certiqs_key.runs.report.setup import build_setup, occupation_label

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "runs" / "report_examples"


def example(name: str) -> dict[str, Any]:
    folder = EXAMPLES / name
    gz = folder / "record.json.gz"
    if gz.is_file():
        with gzip.open(gz, "rt", encoding="utf-8") as handle:
            data: dict[str, Any] = json.load(handle)
            return data
    loaded: dict[str, Any] = json.loads(
        (folder / "record.json").read_text(encoding="utf-8")
    )
    return loaded


def family(station: SetupStation, kind: str) -> OperatorFamily:
    (found,) = [item for item in station["families"] if item["kind"] == kind]
    return found


def real(entry: list[Any]) -> float:
    return float(Fraction(entry[0])) if isinstance(entry[0], str) else entry[0]


# --------------------------------------------------------------------------
# The basis of a photon-number block
# --------------------------------------------------------------------------


def test_the_one_photon_basis_is_z_v_then_z_h_as_the_receiver_orders_it() -> None:
    # The receiver's order, ascending lexicographic occupation vectors.
    assert occupation_vectors(2, 1) == ((0, 1), (1, 0))
    modes = ("Z_H", "Z_V")
    assert [occupation_label(vector, modes) for vector in occupation_vectors(2, 1)] == [
        "one photon in mode Z_V", "one photon in mode Z_H",
    ]
    assert occupation_label((0, 0), modes) == "vacuum"
    assert occupation_label((2, 0), modes) == "two photons in mode Z_H"
    assert occupation_label((1, 1), modes) == "one in mode Z_H, one in mode Z_V"


def test_bob_s_one_photon_v_element_sits_on_the_z_v_basis_state() -> None:
    """Pinned against the port map: detector V collects Z_V (via the Z-arm PBS).

    Bob's V detector clicks only on a photon in Z_V and his H detector only
    on a photon in Z_H, so on the labelled basis V must be non-zero exactly
    at "one photon in mode Z_V" and H exactly at "one photon in mode Z_H".
    """
    setup = build_setup(example("bbm92"))
    bob = next(station for station in setup["stations"] if station["party"] == "B")
    assert bob["channel_modes"] == ["Z_H", "Z_V"]
    blocks = family(bob, "photon-blocks")["blocks"]
    one = next(block for block in blocks if block["title"].endswith("1 photon"))
    assert one["basis"] == ["one photon in mode Z_V", "one photon in mode Z_H"]
    elements = {element["outcome"]: element["matrix"] for element in one["elements"]}
    v, h = elements["V"], elements["H"]
    assert real(v[0][0]) > 0.1 and abs(real(v[1][1])) < 1e-12
    assert real(h[1][1]) > 0.1 and abs(real(h[0][0])) < 1e-12
    assert real(v[0][0]) == pytest.approx(real(h[1][1]))
    # The target POVM's one-photon sector carries the same labels.
    target = family(bob, "target-povm")
    sector = next(block for block in target["blocks"] if block["title"] == "1 photon")
    assert sector["basis"] == one["basis"]
    assert target["claims"]


def test_the_element_list_reads_as_the_bbm92_receiver() -> None:
    setup = build_setup(example("bbm92"))
    bob = next(station for station in setup["stations"] if station["party"] == "B")
    words = {element["name"]: element["description"] for element in bob["elements"]}
    assert "beamsplitter" in words["bs"] and "(50:50)" in words["bs"]
    assert words["hwp"].startswith("half-wave plate at angle π/8 = 22.5°")
    assert "in the X arm" in words["hwp"]
    assert "transmits H and reflects V" in words["pbs_z"]
    assert "transmits H and reflects V" in words["pbs_x"]
    assert [detector["port"] for detector in bob["detectors"]] == ["H", "V", "D", "A"]
    assert {detector["port"]: detector["modes"] for detector in bob["detectors"]} == {
        "H": ["Z_H", "Z_V"], "V": ["Zr_H", "Zr_V"],
        "D": ["X_H", "X_V"], "A": ["Xr_H", "Xr_V"],
    }
    meanings = {letter["letter"]: letter["meaning"] for letter in bob["outcomes"]}
    assert meanings["nc"] == "no detector clicked"
    assert meanings["H"].startswith("only detector H clicked")
    assert meanings["mc"].startswith("more than one detector clicked")
    assert bob["photon_cutoff"] == 1


# --------------------------------------------------------------------------
# Every receiver route
# --------------------------------------------------------------------------


def test_element_graph_per_station() -> None:
    setup = build_setup(example("bbm92"))
    assert [station["party"] for station in setup["stations"]] == ["A", "B"]
    for station in setup["stations"]:
        assert station["route"] == "element-graph"
        kinds = [item["kind"] for item in station["families"]]
        assert kinds == ["photon-blocks", "dark-composed", "target-povm"]


def test_a_single_element_graph_receiver_says_what_the_record_lacks() -> None:
    setup = build_setup(example("optical_bb84"))
    (station,) = setup["stations"]
    assert station["route"] == "element-graph"
    assert [element["name"] for element in station["elements"]] == [
        "bs", "hwp", "pbs_z", "pbs_x",
    ]
    assert station["families"] == []
    assert any("not its POVM operators" in note for note in station["notes"])
    assert [letter["letter"] for letter in station["outcomes"]] == [
        "nc", "H", "V", "D", "A", "mc",
    ]


def test_the_declared_finite_povm_is_the_povm() -> None:
    setup = build_setup(example("bb84"))
    (station,) = setup["stations"]
    assert station["route"] == "declared-finite-povm"
    declared = family(station, "declared-povm")
    (block,) = declared["blocks"]
    elements = {element["outcome"]: element["matrix"] for element in block["elements"]}
    assert set(elements) == {"(Z,0)", "(Z,1)", "(X,0)", "(X,1)"}
    assert real(elements["(Z,0)"][0][0]) == pytest.approx(0.5)
    assert declared["claims"] == ["protocol-compiler/thm:band-a"]


def test_declared_port_grams_are_shown_on_the_channel_modes() -> None:
    setup = build_setup(example("document-optical_bb84_port_grams"))
    (station,) = setup["stations"]
    assert station["route"] == "port-grams"
    grams = family(station, "port-grams")
    (block,) = grams["blocks"]
    assert block["basis"] == ["Z_H", "Z_V"]
    elements = {element["outcome"]: element["matrix"] for element in block["elements"]}
    assert elements["H"] == [[["1/2", "0"], ["0", "0"]], [["0", "0"], ["0", "0"]]]
    assert block["exact"]


def test_an_instrument_matrix_is_shown_from_modes_to_inputs() -> None:
    """SYNTHETIC: no committed record takes the instrument-matrix route."""
    record = copy.deepcopy(example("document-optical_bb84_port_grams"))
    record["payload"]["stages"]["receiver_construction"]["receiver_route"] = (
        "instrument-matrix"
    )
    measurement = record["payload"]["protocol_document"]["canonical"]["stations"][0][
        "measurement"
    ]
    del measurement["port_grams"]
    measurement["route"] = "instrument_matrix"
    rows = len(measurement["modes"])
    measurement["instrument_matrix"] = {
        "matrix": [[1 if row == column else 0 for column in range(2)]
                   for row in range(rows)]
    }
    (station,) = build_setup(record)["stations"]
    assert station["route"] == "instrument-matrix"
    instrument = family(station, "instrument-matrix")
    (block,) = instrument["blocks"]
    assert block["column_basis"] == ["Z_H", "Z_V"]
    assert block["basis"][0] == "Z_H"
    assert len(block["basis"]) == rows
    (element,) = block["elements"]
    assert element["matrix"][0][0] == ["1", "0"]


# --------------------------------------------------------------------------
# Protocol, source, acceptance, expected statistics
# --------------------------------------------------------------------------


def test_protocol_steps_of_bbm92() -> None:
    steps = {step["title"]: step for step in build_setup(example("bbm92"))["protocol"]}
    assert "test with probability 0.125" in steps["Public choice (test coin)"]["text"]
    assert steps["Rounds"]["pointer"] == "/payload/config/rounds"
    assert "Key bases: ZX" in steps["Sifting and key map"]["text"]
    assert steps["Announcements"]["text"].startswith("First Alice announces")


def test_the_source_and_the_acceptance_test() -> None:
    setup = build_setup(example("bbm92"))
    source = setup["source"]
    assert source is not None
    assert source["mode"] == "untrusted" and source["trusted"] is False
    assert "only predicts" in source["text"]
    acceptance = setup["acceptance"]
    assert acceptance is not None
    assert acceptance["rows"] == len(acceptance["outcomes"]) > 0
    assert acceptance["completeness_certified"] is not None


def _qber_record(error: Fraction) -> dict[str, Any]:
    """Return a hand-made honest law: Z rounds only, Bob errs with ``error``."""
    record = completed_record()
    right, wrong = (1 - error) / 2, error / 2
    raw = {"(Z,0)|0": right, "(Z,0)|1": wrong, "(Z,1)|1": right, "(Z,1)|0": wrong}
    pairs = [(("(Z,0)", "0"), 0), (("(Z,0)", "1"), 0),
             (("(Z,1)", "1"), 1), (("(Z,1)", "0"), 1)]
    record["payload"]["compiled"] = {
        "public": {
            "key_holder": "A",
            "key_alphabet": [0, 1],
            "key_map": [[list(pair), bit] for pair, bit in pairs],
            "party_partition": {
                "alice_readout": [[list(pair), pair[0]] for pair, _ in pairs],
                "bob_readout": [[list(pair), pair[1]] for pair, _ in pairs],
            },
            "announce_alice": [["(Z,0)", "Z"], ["(Z,1)", "Z"]],
        },
        "source": {"source_mode": "trusted", "signal_alphabet": ["(Z,0)", "(Z,1)"]},
    }
    record["payload"]["stages"]["acceptance_construction"] = {
        "raw_joint_distribution": {key: str(value) for key, value in raw.items()},
        "outcomes": ["gen"],
    }
    return record


def test_the_expected_qber_and_key_probability_by_hand() -> None:
    expected = {
        item["name"]: item["value"]
        for item in build_setup(_qber_record(Fraction(1, 20)))["expected"]
    }
    assert expected["Probability that a round gives a raw key bit"] == 1.0
    assert expected["Expected QBER, key rounds Alice announces Z"] == pytest.approx(
        0.05, abs=1e-15
    )


def test_the_bbm92_example_s_expected_statistics() -> None:
    record = example("bbm92")
    expected = {item["name"]: item for item in build_setup(record)["expected"]}
    assert set(expected) >= {
        "Probability that a round gives a raw key bit",
        "Expected QBER, key rounds Alice announces gen:Z",
        "Expected QBER, key rounds Alice announces gen:X",
        "Detection probability at Alice's station",
        "Detection probability at Bob's station",
    }
    for item in expected.values():
        assert item["value"] is not None and 0 <= item["value"] <= 1
        assert item["how"]


# --------------------------------------------------------------------------
# What the record does not hold
# --------------------------------------------------------------------------


@pytest.mark.parametrize("version", ["0.20.0", "0.21.0", "0.22.0", "0.23.0", "0.24.0"])
def test_older_and_synthetic_records_build_with_notes(version: str) -> None:
    record = completed_record()
    record["schema_version"] = version
    if version == "0.20.0":
        del record["payload"]["protocol_document"]
    setup = build_setup(record)
    assert setup["source_notes"] or setup["station_notes"] or setup["expected_notes"]
    assert setup["stations"] == [] or all(
        station["name"] for station in setup["stations"]
    )


_OFF_LINE = (
    "Efficiency normalization: off (factor 1 declared); the detectors are "
    "analysed at their declared efficiencies."
)


def _at_factor_one(
    version: str, efficiency: str, *, declared: bool, applied: bool, reason: str | None
) -> dict[str, Any]:
    """optical_bb84's record at schema ``version``, its receiver at ``t = 1``."""
    record = copy.deepcopy(example("optical_bb84"))
    record["schema_version"] = version
    record["payload"]["stages"]["receiver_construction"]["efficiency_normalization"] = {
        "factored_loss": "1",
        "factor_declared": declared,
        "applied": applied,
        "reason": reason,
        "ports": [
            {
                "port": port,
                "declared_efficiency": efficiency,
                "compiled_efficiency": efficiency,
            }
            for port in ("H", "V", "D", "A")
        ],
        "measurement": None,
    }
    return record


@pytest.mark.parametrize(
    ("version", "efficiency", "declared", "applied", "reason", "off"),
    [
        # Record 0.39.0: a declared one is declared_one; a default one
        # (eta_max >= 99/100) reads applied at t = 1 with no reason.
        ("0.39.0", "3/5", True, False, "declared_one", True),
        ("0.39.0", "99/100", False, True, None, False),
        # Record 0.40.0: a factor of one is factor_one whoever chose it, and
        # factor_declared says who (receiver/detector-imperfections/
        # req:normalization-record).
        ("0.40.0", "3/5", True, False, "factor_one", True),
        ("0.40.0", "99/100", False, False, "factor_one", False),
        ("0.40.0", "1", True, False, "factor_one", False),
    ],
)
def test_a_factor_of_one_renders_the_off_line_only_where_declared(
    version: str,
    efficiency: str,
    declared: bool,
    applied: bool,
    reason: str | None,
    off: bool,
) -> None:
    """The off line where the factor one was declared and a detector is below one.

    A 0.39.0 record still renders (another reader re-renders study records of
    that schema with this builder), its ``declared_one`` read as a declared
    factor of one; at the default one neither schema prints a line.
    """
    record = _at_factor_one(
        version, efficiency, declared=declared, applied=applied, reason=reason
    )
    report = build_report(record)
    assert report["sections"]["provenance"]["record_schema_version"] == version
    (station,) = report["sections"]["setup"]["stations"]
    normalization = [
        note for note in station["notes"] if note.startswith("Efficiency normalization")
    ]
    assert normalization == ([_OFF_LINE] if off else [])
    markdown = render_markdown(report, contract_link=default_contract_link())
    assert (_OFF_LINE in markdown) is off


def test_a_refused_and_a_malformed_record_never_crash() -> None:
    build_setup(refused_record())
    record = example("bbm92")
    record["payload"]["stages"]["stations"] = [{"receiver": "garbage"}, 7]
    record["payload"]["compiled"]["public"]["key_map"] = "garbage"
    record["payload"]["stages"]["acceptance_construction"][
        "raw_joint_distribution"] = {"x": "not a number"}
    setup = build_setup(record)
    assert setup["stations"][0]["families"] == []
    assert any("not exact" in note for note in setup["expected_notes"])


def test_the_setup_validates_against_the_report_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    for name in ("bbm92", "bb84", "optical_bb84", "document-optical_bb84_port_grams"):
        report = build_report(example(name))
        jsonschema.validate(report, report_schema())
        assert report["sections"]["setup"]["stations"]
