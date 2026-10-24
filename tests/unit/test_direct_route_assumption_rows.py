"""A-SNAP's ledger row: disengaged only where every named block is evaluated off.

``foundations/def:evaluated-off-snap`` (ii) with
``meat-core/frank-wolfe/req:bracket-on-reference`` (iv), (v); the run tier's
half is ``certiqs_key.runs.assumptions._reductions_rows``. The row is listed as
not engaged, citing that every named block was evaluated off its snap, only
where the run names some block and every named one was; where the record names
none, the row stands as emitted, so the condition is never cited where it does
not hold. The noisy optical device's preparation (no solve, well under a
second) gives an artefact whose ledger carries the A-SNAP row.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.reasons import SNAPPED_MEASUREMENT_ROW
from certiqs_key.runs.assumptions import EmittedRow, _reductions_rows
from certiqs_key.runs.config import SolverSettings
from certiqs_key.runs.direct_route import (
    EVALUATED_OFF_CONDITION,
    RestingBlock,
    StationEvaluation,
)

pytestmark = pytest.mark.contract

PORTS = ("H", "V", "D", "A")


def _artifact() -> ProofReductionArtifact:
    from instances.optical_bb84.surface import default_config, preparation

    from certiqs_key.runs.pipeline import Preparation

    base = default_config(solver=SolverSettings(method="fw", max_iterations=3))
    config = base.with_(
        device={
            **base.device,
            "photon_cutoff": F(2),
            "exact_window": F(3),
            "efficiency": dict.fromkeys(PORTS, F(9, 10)),
            "dark_count": dict.fromkeys(PORTS, F(1, 10**6)),
        }
    )
    outcome = preparation(config)
    assert isinstance(outcome, Preparation)
    artifact = outcome.reduction_artifact
    assert artifact is not None
    assert any(
        entry.assumption_id == SNAPPED_MEASUREMENT_ROW.identifier
        for entry in artifact.assumption_ledger
    ), "the artefact carries no A-SNAP row, so the case shows nothing"
    return artifact


def _a_snap(evaluation: StationEvaluation) -> EmittedRow:
    (row,) = [
        row
        for row in _reductions_rows(_artifact(), None, evaluation)
        if row.short_id == SNAPPED_MEASUREMENT_ROW.identifier
    ]
    return row


def _block(off: bool, name: str = "m=1, t=off") -> RestingBlock:
    if off:
        return RestingBlock("instance_snap", name, None, None, evaluated_off_snap=True)
    return RestingBlock(
        "instance_snap",
        name,
        "reference_bracket_withdrawn",
        "reference_bracket_withdrawn",
        evaluated_off_snap=False,
    )


def test_a_record_naming_no_block_keeps_a_snap_engaged() -> None:
    """No block named: the row stands as emitted, with no condition cited."""
    evaluation = StationEvaluation(
        station=None,
        factor=None,
        instance_blocks=frozenset({"m=1, t=off"}),
        emission_sectors=frozenset(),
        kept_blocks=(),
        named=(),
    )
    row = _a_snap(evaluation)
    assert row.engaged is True and row.condition is None


def test_every_named_block_evaluated_off_disengages_a_snap() -> None:
    evaluation = StationEvaluation(
        station=None,
        factor=None,
        instance_blocks=frozenset({"m=1, t=off"}),
        emission_sectors=frozenset(),
        kept_blocks=(),
        named=(_block(True),),
    )
    row = _a_snap(evaluation)
    assert row.engaged is False and row.condition == EVALUATED_OFF_CONDITION


def test_some_named_block_resting_keeps_a_snap_bound_to_it() -> None:
    evaluation = StationEvaluation(
        station=None,
        factor=None,
        instance_blocks=frozenset({"m=1, t=off"}),
        emission_sectors=frozenset(),
        kept_blocks=(),
        named=(_block(True), _block(False, "m=2, t=off")),
    )
    row = _a_snap(evaluation)
    assert row.engaged is True and row.condition is None
    assert row.bindings == (
        (
            "resting_blocks",
            (
                "instance_snap: m=2, t=off "
                "(reference_bracket_withdrawn: reference_bracket_withdrawn)",
            ),
        ),
    )


def test_the_run_completes_the_receiver_s_fix_of_a_handed_block() -> None:
    """receiver/detector-imperfections/req:snap-fix.

    The receiver states the fix of a handed last-resort block at the snap (its
    noise fix only, the block having no cause there). The run's decision
    completes it: a block evaluated off its snap is named with no fix, and a
    block resting for a cause of the run's (here the bracket withdrawn) names
    that cause's fix beside the receiver's noise fix. A block resting for the
    receiver's own cause keeps the receiver's fix as written.
    """
    from certiqs_key.foundations.resting import RestingCause
    from certiqs_key.runs.direct_route import annotate_snap_records

    noise = "the block was snapped by the last resort: model the noise"
    own = "the receiver offers no reference: declare exact data"
    snap = {
        "setting": "off",
        "blocks": [
            {"block": "m=1", "status": "moved", "receiver_fix": noise},
            {"block": "m=2", "status": "moved", "receiver_fix": noise},
            {"block": "m=3", "status": "moved", "receiver_fix": own},
        ],
        "receiver_fixes": {"m=1": noise, "m=2": noise, "m=3": own},
    }
    withdrawn = RestingBlock(
        "instance_snap",
        "m=2, t=off",
        "last_resort",
        "reference_bracket_withdrawn",
        evaluated_off_snap=False,
        support_not_preserved=True,
    )
    unhanded = RestingBlock(
        "instance_snap",
        "m=3, t=off",
        "no_usable_reference",
        "no_reference",
        evaluated_off_snap=False,
    )
    evaluation = StationEvaluation(
        station=None,
        factor=None,
        instance_blocks=frozenset({"m=1, t=off"}),
        emission_sectors=frozenset(),
        kept_blocks=(),
        named=(_block(True), withdrawn, unhanded),
    )
    annotated = annotate_snap_records({"measurement_snaps": [snap]}, evaluation)
    assert annotated is not None
    (out,) = annotated["measurement_snaps"]
    fixes = {block["block"]: block["receiver_fix"] for block in out["blocks"]}
    assert fixes["m=1"] is None
    assert fixes["m=2"] == (
        f"{RestingCause.REFERENCE_BRACKET_WITHDRAWN.fix}; {noise}"
    )
    assert fixes["m=3"] == own
    assert out["receiver_fixes"] == {"m=2": fixes["m=2"], "m=3": own}
