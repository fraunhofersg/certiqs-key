"""Keep or move, end to end: the instance snap through record and report.

The measurement snap (``foundations/req:snap-reference``): a block the model gives
exactly on the lattice is KEPT, every other block is MOVED by the one fidelity-first
procedure, the reference is handed beside the snap, and the run decides after its search
which moved blocks it evaluates off their snap (``foundations/def:evaluated-off-snap``);
the rest rest on A-SNAP in one of four groups. Every case runs the optical BB84 instance
through its own runner (or its preparation, the runner's prologue), records the run and
builds its report. The cases that assert a key run at :data:`KEY_ITERATIONS`, where each
was measured (at three iterations several give 0, which says nothing about the snap).

* the shipped default: every block kept, A-SNAP in the closure and not
  engaged, key 1809 at the measured budget;
* a noisy two-photon device (eta = 0.9, dark counts on every port): every
  block moved and handed, every one evaluated off its snap, no A-SNAP, key
  1482; the same on the licensed route;
* the same device with ``reference_enclosure`` off: the enclosed block is not
  handed and rests on A-SNAP in the group "no usable reference", the run
  completes, A-SNAP engaged among the user's premises; with the strict option
  as well, the run is refused at the receiver's docking;
* eta = 0.9 at N = 2 without dark counts: m = 0 kept, m = 1 and m = 2 moved
  and handed, both evaluated off their snap;
* an ideal two-photon device with a rotated basis: the blocks above zero
  photons moved and handed their enclosure, nothing flagged; the run
  completes with a positive key, and the strict option passes, nothing
  resting.
"""

from __future__ import annotations

import json
import tempfile
from fractions import Fraction as F
from pathlib import Path
from typing import Any

import pytest

import certiqs_key.runs as runs_package
from certiqs_key.runs.config import RunConfig, SolverSettings
from certiqs_key.runs.record import record_run
from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_markdown,
)

pytestmark = pytest.mark.requires_qics
pytest.importorskip("qics")

PORTS = ("H", "V", "D", "A")

#: The Frank-Wolfe budget of the cases that assert a key. Measured at 20
#: iterations: default 1809, rotated ideal N = 2 1322, noisy N = 2 encoded and
#: licensed 1482.
KEY_ITERATIONS = 20


def _config(iterations: int = 3, **device: Any) -> RunConfig:
    """Return the optical default at ``iterations`` with ``device`` laid over it."""
    from instances.optical_bb84.surface import default_config

    base: RunConfig = default_config(
        solver=SolverSettings(method="fw", max_iterations=iterations)
    )
    if not device:
        return base
    return base.with_(device={**base.device, **device})


def _key(record: dict[str, Any]) -> int | None:
    key: int | None = record["payload"]["stages"]["key_rate"]["key_length"]
    return key


def _two_photons(**device: Any) -> dict[str, Any]:
    return {"photon_cutoff": F(2), "exact_window": F(3), **device}


def _run(config: RunConfig) -> dict[str, Any]:
    """Run the optical instance's own runner and return the record as JSON."""
    from instances.optical_bb84.surface import runner

    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    with tempfile.TemporaryDirectory() as tmp:
        outcome = runner(QicsSectorChoiOracle(), Path(tmp), created_by="t")(config, 0)
        record: dict[str, Any] = record_run(outcome, config, created_by="t").as_dict()
    return json.loads(json.dumps(record))


def _validate(record: dict[str, Any]) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (Path(runs_package.__file__).resolve().parent / "record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(record, schema)


def _snaps(record: dict[str, Any]) -> list[dict[str, Any]]:
    instance = record["payload"]["snaps"]["instance"]
    return list(instance["measurement_snaps"])


def _manifest_ids(record: dict[str, Any]) -> set[str]:
    manifest = record["payload"]["assumption_manifest"]
    return {entry["short_id"] for entry in manifest["assumptions"]}


def _a_snap_not_engaged(record: dict[str, Any]) -> None:
    """A-SNAP is in the closure and, with no block resting, not engaged.

    ``reductions/thm:emit`` (vi) assumes it, so the reductions roots' closure
    holds it; the ledger row's presence rule keeps it out of the engaged list,
    with no discrepancy.
    """
    manifest = record["payload"]["assumption_manifest"]
    assert "A-SNAP" not in _manifest_ids(record)
    assert any(
        "A-SNAP" in closure["assumptions"]
        for closure in manifest["claim_closure"].values()
    )
    listed = [item for item in manifest["not_engaged"] if item["short_id"] == "A-SNAP"]
    assert [item["module"] for item in listed] == ["reductions"]
    assert not [
        item for item in manifest["discrepancies"] if item["short_id"] == "A-SNAP"
    ]


def _statuses(record: dict[str, Any]) -> dict[str, tuple[str, str | None, bool]]:
    """Per block: its status, the kind handed beside it, evaluated off its snap."""
    (snap,) = _snaps(record)
    return {
        block["block"]: (
            block["status"],
            block["handed_reference_kind"],
            block["evaluated_off_snap"],
        )
        for block in snap["blocks"]
    }


def test_the_shipped_default_is_kept() -> None:
    """Unchanged by the retirement: every block kept, 1810 at the measured budget.

    1809 from the search's points alone; the companion polish
    (frank-wolfe/req:bracket-on-reference (i)) continues the 20-iteration
    search on the companion and adds a bit.
    """
    record = _run(_config(KEY_ITERATIONS))
    _validate(record)
    payload = record["payload"]
    assert payload["refused"] is False
    parameters = payload["config"]["parameters"]
    assert parameters["reference_enclosure"] is True
    assert parameters["strict_snaps"] is False
    assert "certify_snaps" not in parameters
    assert "certified_weight_ceiling" not in parameters
    (snap,) = _snaps(record)
    assert snap["run_settings"] == {
        "reference_enclosure": True,
        "strict_snaps": False,
    }
    assert _statuses(record) == {
        "m=0": ("kept", "exact", False),
        "m=1": ("kept", "exact", False),
    }
    assert "domination_record" not in payload["stages"]["reduction"]
    _a_snap_not_engaged(record)
    report = build_report(record)
    section = report["sections"]["protocol"]["measurement_snaps"]
    assert section is not None
    assert section["warnings"] == [] and section["rests_on_a_snap"] is False
    assert section["assumption"] is None
    assert _key(record) == 1810


#: Declared at the factored loss one
#: (receiver/detector-imperfections/req:efficiency-normalization): the device
#: keeps its loss, so that its blocks are the non-dyadic ones these cases are
#: about; at its default the normalized station is lossless.
NOISY = {
    "efficiency": dict.fromkeys(PORTS, F(9, 10)),
    "dark_count": dict.fromkeys(PORTS, F(1, 10**6)),
    "efficiency_normalization": F(1),
}


@pytest.mark.parametrize("route", ["encoded", "licensed"])
def test_a_noisy_device_is_moved_handed_and_evaluated_off(route: str) -> None:
    """Every block moved (none on the lattice), handed, and evaluated off its snap.

    The first-order bound is formed on the reference companion, which carries
    the handed reference on every block, so the run does not rest on A-SNAP.
    The key was 1482 on either route from the search's points alone; the
    companion polish (frank-wolfe/req:bracket-on-reference (i)) continues the
    20-iteration search on the companion and raises it (POLISHED_KEYS).
    """
    record = _run(_config(KEY_ITERATIONS, **_two_photons(route=route, **NOISY)))
    _validate(record)
    payload = record["payload"]
    assert payload["refused"] is False
    assert _statuses(record) == {
        "m=0": ("moved", "exact", True),
        "m=1": ("moved", "exact", True),
        "m=2": ("moved", "enclosed", True),
    }
    for block in _snaps(record)[0]["blocks"]:
        assert block["cause"] is None and block["group"] is None
        assert block["rests_on_assumption"] is False
        assert block["support_not_preserved"] is False
    kinds = {link["kind"] for link in payload["stages"]["reduction"]["chain"]}
    assert "family-dominating" not in kinds
    assert payload["snaps"]["reference_companion"]["rests_on_a_snap"] is False
    _a_snap_not_engaged(record)
    report = build_report(record)
    section = report["sections"]["protocol"]["measurement_snaps"]
    assert section is not None and section["rests_on_a_snap"] is False
    assert {block["group"] for block in section["blocks"]} == {None}
    text = render_markdown(report, contract_link=default_contract_link(""))
    assert "evaluated off their snap" in text
    assert _key(record) == POLISHED_KEYS[route]


#: The noisy two-photon device's key at KEY_ITERATIONS, per route, measured
#: with the companion polish (a snapshot; 1482 on both from the search's points
#: alone).
POLISHED_KEYS = {"encoded": 1491, "licensed": 1490}


def test_the_enclosure_off_leaves_the_enclosed_block_resting() -> None:
    record = _run(_config(**_two_photons(**NOISY)).with_(reference_enclosure=False))
    _validate(record)
    payload = record["payload"]
    assert payload["refused"] is False
    assert payload["config"]["parameters"]["reference_enclosure"] is False
    assert _statuses(record) == {
        "m=0": ("moved", "exact", True),
        "m=1": ("moved", "exact", True),
        "m=2": ("moved", None, False),
    }
    (snap,) = _snaps(record)
    two = next(block for block in snap["blocks"] if block["block"] == "m=2")
    assert two["rests_on_assumption"] is True
    assert two["cause"] == "enclosure_not_used"
    assert two["group"] == "no_usable_reference"
    assert "A-SNAP" in _manifest_ids(record)
    manifest = payload["assumption_manifest"]
    assert not [
        item for item in manifest["discrepancies"] if item["short_id"] == "A-SNAP"
    ]
    snap_entry = next(e for e in manifest["assumptions"] if e["short_id"] == "A-SNAP")
    assert snap_entry["emitted_by"][0]["module"] == "reductions"
    # A premise about the user's device, listed among the premises the user
    # vouches for (category receiver), not among the engine's numerics.
    assert snap_entry["section"] == "assumptions"
    assert snap_entry["category"] == "receiver"
    assert "A-SNAP" not in {item["short_id"] for item in manifest["not_engaged"]}
    report = build_report(record)
    section = report["sections"]["protocol"]["measurement_snaps"]
    assert section is not None and section["rests_on_a_snap"] is True
    assert section["assumption"] == "A-SNAP"
    assert section["settings"]["reference_enclosure"] is False
    assert any("A-SNAP" in warning for warning in section["warnings"])
    text = render_markdown(report, contract_link=default_contract_link(""))
    # An underscore between two letters opens no emphasis, so the carried
    # identifier reads as written.
    assert "Measurement snaps" in text and "enclosure_not_used" in text


def test_the_strict_option_refuses_a_block_with_no_handed_reference() -> None:
    """``foundations/req:snap-reference`` (iv): refused as soon as it is decided.

    With enclosed references not used the declarer hands nothing on m = 2, so
    it refuses at its snap, naming the block, its cause, its group and fix.
    """
    config = _config(**_two_photons(**NOISY)).with_(
        reference_enclosure=False, strict_snaps=True
    )
    record = _run(config)
    _validate(record)
    payload = record["payload"]
    assert payload["refused"] is True
    docking = payload["stages"]["receiver_docking"]
    assert docking["reason"] == "strict_snaps"
    assert "A-SNAP" in docking["detail"] and "m=2" in docking["detail"]


def test_a_non_dyadic_device_keeps_its_vacuum_block_and_moves_the_rest() -> None:
    """Eta = 0.9, N = 2, no dark counts: m = 0 kept, m = 1, 2 moved and handed.

    Both are moved by the one procedure, handed (exact and enclosed), and the
    run evaluates both off their snap.
    """
    record = _run(
        _config(
            **_two_photons(
                efficiency=dict.fromkeys(PORTS, F(9, 10)),
                efficiency_normalization=F(1),
            )
        )
    )
    _validate(record)
    assert record["payload"]["refused"] is False
    assert _statuses(record) == {
        "m=0": ("kept", "exact", False),
        "m=1": ("moved", "exact", True),
        "m=2": ("moved", "enclosed", True),
    }
    decision = record["payload"]["snaps"]["reference_companion"]
    assert decision["status"] == "counted"
    assert [item["block"] for item in decision["kept_blocks"]] == ["m=0, t=off"]
    section = build_report(record)["sections"]["protocol"]["measurement_snaps"]
    assert section is not None and section["rests_on_a_snap"] is False
    assert section["evaluated_off_snap"] == 2


ROTATED = _two_photons(half_wave_angle=F(1, 7))


def test_a_rotated_ideal_device_hands_its_enclosure() -> None:
    """An ideal device at an angle off the pi/8 grid, read off its preparation.

    The blocks above zero photons are irrational: snapped from the receiver's
    floating-point blocks by the support-safe procedure (no last resort, no
    flag) and handed their enclosure, so nothing rests at the snap.
    """
    from instances.optical_bb84.surface import preparation

    outcome = preparation(_config(**ROTATED))
    assert not outcome.refuses
    adaptation = outcome.rows_adaptation
    assert adaptation is not None
    (snap,) = adaptation["measurement_snaps"]
    found = {
        block["block"]: (
            block["status"],
            block["reference_kind"],
            block["handed_reference_kind"],
            block["support_not_preserved"],
            block["rests_on_assumption"],
        )
        for block in snap["blocks"]
    }
    assert found == {
        "m=0": ("kept", "exact", "exact", False, False),
        "m=1": ("moved", "none", "enclosed", False, False),
        "m=2": ("moved", "none", "enclosed", False, False),
    }
    for block in snap["blocks"]:
        assert "round-down" not in block["steps"]
        assert "uniform-lift-last-resort" not in block["steps"]


def test_a_rotated_ideal_device_runs_to_completion_off_its_snap() -> None:
    """The run completes at a positive key (1322 measured) and rests on no snap.

    Certified on the reference companion, whose analyser elements the
    receiver's factor form fixes.
    """
    record = _run(_config(KEY_ITERATIONS, **ROTATED))
    assert record["payload"]["refused"] is False
    key_rate = record["payload"]["stages"]["key_rate"]
    assert key_rate["certified"]["declaration"] == "reference_companion"
    assert "A-SNAP" not in _manifest_ids(record)
    key = _key(record)
    assert key is not None and key > 0, key


def test_the_strict_option_passes_a_run_that_rests_on_nothing() -> None:
    """``req:snap-reference`` (iv): a strict run with no resting block proceeds."""
    record = _run(_config(**ROTATED).with_(strict_snaps=True))
    _validate(record)
    payload = record["payload"]
    assert payload["refused"] is False
    assert payload["snaps"]["reference_companion"]["rests_on_a_snap"] is False
