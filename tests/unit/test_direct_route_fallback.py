"""The run's decision where the certified evaluation falls back or withdraws.

``meat-core/frank-wolfe/req:bracket-on-reference`` (iv), (v) and
``req:certified-evaluation`` (i), (ix) with ``foundations/req:snap-reference``
(iii)(b); the run tier's half is :mod:`certiqs_key.runs.direct_route`. CONTRACT
TESTS on the ideal optical device at angle 1/7 (``N = 2``), whose preparation
(no solve, well under a second) hands an enclosed reference on its two moved
blocks and compiles a companion carrying it:

* the companion's bound counts and the key length is formed from a number
  certified on it: both blocks are evaluated off their snap, nothing rests;
* THE FALLBACK -- it counts, but the key length is formed from a number
  certified on the searched declaration: both rest on A-SNAP in the group
  reference bracket withdrawn, cause ``companion_not_certified``, and neither
  is counted as evaluated off its snap;
* the bracket withdrawn on ``factor_enclosure_inconsistent``: both rest with
  that cause, whose fix reads as an engine defect;
* the certified record's ``premises`` and ``resting_blocks`` follow the
  declaration the certified number is formed on, also where the key length
  is not formed from it;
* a station the companion does not replace (no companion formed for it)
  rests as without one, reference bracket not evaluated, whatever became
  of the replaced station's bracket.
"""

from __future__ import annotations

from fractions import Fraction as F
from functools import cache
from types import SimpleNamespace
from typing import Any

import pytest

from certiqs_key.foundations.resting import RestingCause, RestingGroup
from certiqs_key.runs.direct_route import (
    INSTANCE_SNAP,
    certified_premises,
    direct_route,
)

pytestmark = pytest.mark.contract

MOVED = ("m=1, t=off", "m=2, t=off")


@cache
def _preparation() -> Any:
    from instances.optical_bb84.surface import default_config, preparation

    from certiqs_key.runs.config import SolverSettings
    from certiqs_key.runs.pipeline import Preparation

    base = default_config(solver=SolverSettings(method="fw", max_iterations=3))
    config = base.with_(
        device={
            **base.device,
            "photon_cutoff": F(2),
            "exact_window": F(3),
            "half_wave_angle": F(1, 7),
        }
    )
    outcome = preparation(config)
    assert isinstance(outcome, Preparation)
    return outcome


def _result(
    status: str, *, cause: str | None = None, certified: dict[str, Any] | None = None
) -> Any:
    p = _preparation()
    bracket = {
        "status": status,
        "reason": None if status == "counted" else "reference_bracket_withdrawn",
        "cause": cause,
    }
    return SimpleNamespace(
        device_artifacts=(),
        reduction_artifact=p.reduction_artifact,
        rows_adaptation=p.rows_adaptation,
        reference_companion=p.reference_companion,
        declaration=p.declaration,
        key_rate=SimpleNamespace(reference_bracket=bracket, certified=certified),
    )


def _causes(result: Any) -> dict[str, str | None]:
    station = direct_route(result).station(None)
    assert station is not None
    return {block.block: block.cause for block in station.named}


def test_the_case_hands_and_moves_two_blocks() -> None:
    p = _preparation()
    blocks = {
        block["block"]: block["status"]
        for snap in p.rows_adaptation["measurement_snaps"]
        for block in snap["blocks"]
    }
    assert blocks == {"m=0": "kept", "m=1": "moved", "m=2": "moved"}


def test_certified_on_the_companion_evaluates_both_off_their_snap() -> None:
    result = _result(
        "counted",
        certified={"status": "certified", "declaration": "reference_companion"},
    )
    decision = direct_route(result)
    assert decision.counted and not decision.fallback
    assert decision.evaluated_off_snap_count == 2 and not decision.rests_on_a_snap
    assert certified_premises(result) == {"premises": [], "resting_blocks": []}


def test_in_the_fallback_the_carried_blocks_rest_on_a_snap() -> None:
    result = _result(
        "counted", certified={"status": "certified", "declaration": "searched"}
    )
    decision = direct_route(result)
    assert decision.counted and decision.fallback
    assert decision.evaluated_off_snap_count == 0
    assert _causes(result) == dict.fromkeys(
        MOVED, str(RestingCause.COMPANION_NOT_CERTIFIED)
    )
    record = decision.as_record()
    assert record["fallback"] is True
    assert {b["group"] for b in record["resting_blocks"]} == {
        str(RestingGroup.REFERENCE_BRACKET_WITHDRAWN)
    }
    premises = certified_premises(result)
    assert premises is not None and premises["premises"] == ["A-SNAP"]
    assert [b["block"] for b in premises["resting_blocks"]] == list(MOVED)


@pytest.mark.parametrize("status", ["not_certified", "withheld"])
def test_a_fallback_that_certifies_nothing_leaves_the_key_on_the_companion(
    status: str,
) -> None:
    """The key length is the companion's first-order one: the blocks are off snap.

    The certified record's own premises and resting blocks describe the
    declaration it names, whatever the status (``req:certified-evaluation``
    (ix)): in a fallback not reported at the certified tier they name A-SNAP
    and the blocks with ``companion_not_certified``.
    """
    result = _result("counted", certified={"status": status, "declaration": "searched"})
    assert direct_route(result).evaluated_off_snap_count == 2
    premises = certified_premises(result)
    assert premises is not None and premises["premises"] == ["A-SNAP"]
    assert {b["cause"] for b in premises["resting_blocks"]} == {
        str(RestingCause.COMPANION_NOT_CERTIFIED)
    }


def test_a_bracket_withdrawn_as_inconsistent_names_the_engine_defect() -> None:
    result = _result(
        "withdrawn",
        cause="factor_enclosure_inconsistent",
        certified={"status": "certified", "declaration": "searched"},
    )
    decision = direct_route(result)
    assert not decision.counted and not decision.fallback
    assert _causes(result) == dict.fromkeys(
        MOVED, str(RestingCause.FACTOR_ENCLOSURE_INCONSISTENT)
    )
    station = decision.station(None)
    assert station is not None
    fixes = {block.fix for block in station.resting}
    assert len(fixes) == 1 and "defect of the engine" in str(next(iter(fixes)))
    premises = certified_premises(result)
    assert premises is not None and premises["premises"] == ["A-SNAP"]


def test_a_bracket_withdrawn_for_no_contributing_point_keeps_its_cause() -> None:
    result = _result(
        "withdrawn", certified={"status": "certified", "declaration": "searched"}
    )
    assert _causes(result) == dict.fromkeys(
        MOVED, str(RestingCause.REFERENCE_BRACKET_WITHDRAWN)
    )


def test_the_three_causes_share_the_withdrawn_group_and_its_fix() -> None:
    """``req:snap-reference`` (iii)(b): three causes, one group, one group fix."""
    causes = (
        RestingCause.REFERENCE_BRACKET_WITHDRAWN,
        RestingCause.FACTOR_ENCLOSURE_INCONSISTENT,
        RestingCause.COMPANION_NOT_CERTIFIED,
    )
    withdrawn = RestingGroup.REFERENCE_BRACKET_WITHDRAWN
    assert {cause.group for cause in causes} == {withdrawn}
    assert "reference companion's evaluated points" in (
        RestingGroup.REFERENCE_BRACKET_WITHDRAWN.fix()
    )
    assert "certified evaluation's reasons" in RestingCause.COMPANION_NOT_CERTIFIED.fix


def _with_moved_sector(result: Any, sector: int = 3) -> Any:
    """Return the run as if its emission normaliser moved a class of ``sector``."""
    artifact = result.reduction_artifact
    result.reduction_artifact = SimpleNamespace(
        reference_companion=artifact.reference_companion,
        emission_record=SimpleNamespace(
            moved_sectors=((sector, ("a class",)),), last_resort_sectors=frozenset()
        ),
    )
    return result


def test_in_the_fallback_a_moved_data_sector_rests_too() -> None:
    """``req:bracket-on-reference`` (v): the sectors whose normalizer it bypasses.

    Counted and formed on the companion, the sector is evaluated off its snap;
    in the fallback it rests with the cause ``companion_not_certified``.
    """
    on_companion = _with_moved_sector(
        _result(
            "counted",
            certified={"status": "certified", "declaration": "reference_companion"},
        )
    )
    station = direct_route(on_companion).station(None)
    assert station is not None and station.emission_sectors == frozenset({3})
    fallback = _with_moved_sector(
        _result("counted", certified={"status": "certified", "declaration": "searched"})
    )
    station = direct_route(fallback).station(None)
    assert station is not None and station.emission_sectors == frozenset()
    assert _causes(fallback)["data sector 3"] == str(
        RestingCause.COMPANION_NOT_CERTIFIED
    )


@pytest.mark.parametrize(
    ("status", "cause", "certified", "replaced_cause"),
    [
        pytest.param(
            "withdrawn", None, None, RestingCause.REFERENCE_BRACKET_WITHDRAWN,
            id="withdrawn",
        ),
        pytest.param(
            "withdrawn",
            "factor_enclosure_inconsistent",
            None,
            RestingCause.FACTOR_ENCLOSURE_INCONSISTENT,
            id="withdrawn-inconsistent",
        ),
        pytest.param(
            "counted",
            None,
            {"status": "certified", "declaration": "reference_companion"},
            None,
            id="counted",
        ),
        pytest.param(
            "counted",
            None,
            {"status": "certified", "declaration": "searched"},
            RestingCause.COMPANION_NOT_CERTIFIED,
            id="fallback",
        ),
    ],
)
def test_a_station_the_companion_does_not_replace_rests_as_without_one(
    status: str,
    cause: str | None,
    certified: dict[str, Any] | None,
    replaced_cause: RestingCause | None,
) -> None:
    """Two stations; the companion replaces the first, none was formed for the second.

    ``req:bracket-on-reference`` (iv) and (v): the first station's handed
    blocks are evaluated off their snap, or rest in the group reference
    bracket withdrawn with the cause; the second's, on which the same
    reference was handed but which no companion carries, rest as without a
    companion, reference bracket not evaluated, whatever became of the first
    station's bracket.
    """
    p = _preparation()
    unformed = SimpleNamespace(
        reference_companion=None, emission_record=p.reduction_artifact.emission_record
    )
    result = _result(status, cause=cause, certified=certified)
    result.device_artifacts = (
        SimpleNamespace(
            reduction=p.reduction_artifact, rows_adaptation=p.rows_adaptation
        ),
        SimpleNamespace(reduction=unformed, rows_adaptation=p.rows_adaptation),
    )
    decision = direct_route(result)

    def causes(index: int) -> dict[str, str | None]:
        station = decision.station(index)
        assert station is not None
        return {b.block: b.cause for b in station.named if b.origin == INSTANCE_SNAP}

    expected = None if replaced_cause is None else str(replaced_cause)
    assert causes(0) == dict.fromkeys(MOVED, expected)
    assert causes(1) == dict.fromkeys(
        MOVED, str(RestingCause.REFERENCE_BRACKET_NOT_EVALUATED)
    )
