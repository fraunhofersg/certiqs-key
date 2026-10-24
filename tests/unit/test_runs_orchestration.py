"""The orchestration tier: the composition it owns, the record it writes.

No marker. These are not contract tests and there is nothing here to mark: the
``runs`` tier has no mathematical contract, states no claim, and computes no
number (spec/architecture.md 3.3, PRINCIPLES.md section 4). What is asserted is that it
composes, orders and records faithfully -- and, in two places, that it does NOT
do something: it invents no default and it invents no envelope field.

The ``SliceResult`` branch of :func:`~certiqs_key.runs.record.record_run` is
exercised by ``tests/integration/test_bb84_slice.py``, which has a real solver
run to record. Everything reachable without one is exercised here.
"""

from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

import pytest
from tests.support.lowered_templates import lowered

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs import (
    RunConfig,
    SliceRefusal,
    SliceStage,
    grid,
    record_run,
    sweep,
    write_record,
)

PARAMETERS = KeyLengthParameters(
    alpha=1.1, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
)


def config(**changes: object) -> RunConfig:
    """Return a base run config, optionally modified.

    ``declared_tolerance`` is passed explicitly because there is no default to
    fall back on (spec/architecture.md 2.8, spec/architecture.md 2.8), and ``0.0`` is
    the exact reading -- the value a run declares when it asserts that nothing it
    declares needs repairing.
    """
    base = RunConfig(
        rounds=2_000,
        completeness_budget=F(1, 1_000_000),
        parameters=PARAMETERS,
        declared_tolerance=0.0,
        model={"qber": F(1, 100)},
    )
    return base.with_(**changes) if changes else base


def refusal(reason: str = "unsupported-declaration") -> SliceRefusal:
    """Return a compilation-stage refusal carrying an owning module's reason."""
    return SliceRefusal(
        stage=SliceStage.COMPILATION,
        reason=reason,
        detail="the compiler declined, in its own vocabulary",
    )


# ---------------------------------------------------------------------------
# the composition
# ---------------------------------------------------------------------------


def test_with_returns_a_copy_and_leaves_the_base_alone() -> None:
    """A swept axis must not mutate the config every other point derives from."""
    base = config()
    derived = base.with_(rounds=5_000)
    assert derived.rounds == 5_000
    assert base.rounds == 2_000
    assert derived.parameters is base.parameters


def test_grid_with_no_axes_is_the_base_alone() -> None:
    """A sweep over nothing is one run, not zero."""
    base = config()
    assert grid(base) == (base,)


def test_grid_is_the_cartesian_product_in_a_deterministic_order() -> None:
    """Axis names are SORTED, so ``alpha`` precedes ``rounds`` and rounds vary fastest.

    Sorting rather than keyword order is the stronger guarantee, and it is the one
    that matters: two callers who name the same axes in different orders get the
    same grid, so their record sets stay comparable point for point.
    """
    points = grid(config(), rounds=[2_000, 5_000], alpha=[1.1, 1.5])
    assert [(p.alpha, p.rounds) for p in points] == [
        (1.1, 2_000),
        (1.1, 5_000),
        (1.5, 2_000),
        (1.5, 5_000),
    ]
    assert grid(config(), alpha=[1.1, 1.5], rounds=[2_000, 5_000]) == points


def test_a_model_axis_merges_into_the_opaque_model_mapping() -> None:
    """``model`` is swept by key because the tier cannot reach it by attribute."""
    points = grid(config(), model={"qber": [F(1, 100), F(3, 100)]})
    assert [p.model["qber"] for p in points] == [F(1, 100), F(3, 100)]


def test_a_model_axis_composes_with_a_field_axis() -> None:
    """Field axes run before model axes, and every combination appears once."""
    points = grid(
        config(), rounds=[2_000, 5_000], model={"qber": [F(1, 100), F(1, 50)]}
    )
    assert len(points) == 4
    assert {(p.rounds, p.model["qber"]) for p in points} == {
        (2_000, F(1, 100)),
        (2_000, F(1, 50)),
        (5_000, F(1, 100)),
        (5_000, F(1, 50)),
    }


# ---------------------------------------------------------------------------
# the record
# ---------------------------------------------------------------------------


def test_a_refusal_is_recorded_with_the_owning_modules_own_reason() -> None:
    """A refusal is an outcome. It is recorded, never suppressed and never renamed."""
    record = record_run(refusal(), config(), created_by="test")
    assert record.payload["refused"] is True
    stage = record.payload["stages"]["compilation"]
    assert stage["reason"] == "unsupported-declaration"
    assert stage["refused"] is True


def test_the_record_carries_no_deferred_envelope_field() -> None:
    """The four deferred envelope fields are absent (spec/future-scope.md 1)."""
    record = record_run(refusal(), config(), created_by="test")
    written = record.as_dict()
    for deferred in (
        "artifact_id",
        "content_hash",
        "input_artifact_hashes",
        "provenance",
    ):
        assert deferred not in written


def test_the_record_claims_no_mathematical_spec_version_of_its_own() -> None:
    """No module produced it, so there is no honest value for that field."""
    written = record_run(refusal(), config(), created_by="test").as_dict()
    assert "mathematical_spec_version" not in written
    assert written["kind"] == "run-record"


def test_exact_rationals_survive_the_record_as_exact_strings() -> None:
    """A float here would discard the exactness the emitting module guarantees."""
    written = record_run(refusal(), config(), created_by="test").as_dict()
    recorded = written["payload"]["config"]
    assert recorded["completeness_budget"] == "1/1000000"
    assert F(recorded["model"]["qber"]) == F(1, 100)


def test_a_record_round_trips_through_json(tmp_path: Path) -> None:
    """The record is data. Nothing in it needs a custom decoder to read back."""
    record = record_run(refusal(), config(), created_by="test")
    path = tmp_path / "run-0000.json"
    write_record(path, record)
    assert json.loads(path.read_text(encoding="utf-8")) == record.as_dict()


def test_write_record_never_overwrites(tmp_path: Path) -> None:
    """A log that can silently replace a previous run's record is not a log."""
    record = record_run(refusal(), config(), created_by="test")
    path = tmp_path / "run-0000.json"
    write_record(path, record)
    with pytest.raises(FileExistsError):
        write_record(path, record)


# ---------------------------------------------------------------------------
# the loop
# ---------------------------------------------------------------------------


def test_sweep_runs_every_point_in_order_and_drops_none(tmp_path: Path) -> None:
    """Every point is run and every outcome kept, refusals included."""
    seen: list[tuple[int, int]] = []

    def runner(cfg: RunConfig, index: int) -> SliceRefusal:
        seen.append((index, cfg.rounds))
        return refusal(f"declined-{index}")

    points = grid(config(), rounds=[2_000, 5_000, 20_000])
    swept = sweep(points, runner, created_by="test", record_dir=tmp_path)

    assert seen == [(0, 2_000), (1, 5_000), (2, 20_000)]
    assert [s.index for s in swept] == [0, 1, 2]
    assert [s.record.payload["stages"]["compilation"]["reason"] for s in swept] == [
        "declined-0",
        "declined-1",
        "declined-2",
    ]


def test_sweep_writes_one_record_per_point(tmp_path: Path) -> None:
    """A sweep's output is a directory of records, one per grid point."""
    points = grid(config(), rounds=[2_000, 5_000])
    swept = sweep(
        points,
        lambda _cfg, index: refusal(f"declined-{index}"),
        created_by="test",
        record_dir=tmp_path,
    )
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "run-0000.json",
        "run-0001.json",
    ]
    assert all(s.record_path is not None for s in swept)


def test_sweep_keeps_records_in_memory_when_no_directory_is_given() -> None:
    """``record_dir=None`` is a supported mode, not a degraded one."""
    swept = sweep(
        grid(config(), rounds=[2_000]),
        lambda _cfg, _index: refusal(),
        created_by="test",
    )
    assert swept[0].record_path is None
    assert swept[0].record.payload["refused"] is True


# ---------------------------------------------------------------------------
# the instance bridge
#
# The seam itself, so it is tested where the seam is described rather than split
# across two files: the run tier carries ``model`` uninterpreted, and the
# instance that owns the vocabulary is the one that reads it.
# ---------------------------------------------------------------------------


def provider_from_config(run: RunConfig) -> object:
    """Return the bb84 instance's honest provider for ``run``'s model section.

    The instance's reader is its template's lowering; the
    device section is the instance's own default, because only the model
    section is under test here.
    """
    from instances.bb84.surface import default_config

    return lowered("bb84", default_config(model=dict(run.model)))[1].honest


def test_the_instance_reads_its_own_model_parameters_out_of_the_config() -> None:
    """``model`` is opaque to ``runs`` and legible to the instance that owns it."""
    provider = provider_from_config(config(model={"qber": F(1, 25)}))
    assert callable(provider)


@pytest.mark.parametrize(
    "model",
    [{}, {"visibility": F(1, 2)}, {"qber": F(1, 100), "extra": F(0)}],
    ids=["missing", "wrong-name", "extra"],
)
def test_a_model_mapping_the_instance_does_not_recognise_is_an_error(
    model: dict[str, F],
) -> None:
    """No default is substituted for a parameter the instance was not given."""
    with pytest.raises(KeyError):
        provider_from_config(config(model=model))


@pytest.mark.smoke
def test_the_record_is_self_contained_about_what_was_asked() -> None:
    """Reading a record must not require the script that produced it."""
    swept = sweep(
        grid(config(), rounds=[5_000], model={"qber": [F(3, 100)]}),
        lambda _cfg, _index: refusal(),
        created_by="test",
    )
    recorded = swept[0].record.payload["config"]
    assert recorded["rounds"] == 5_000
    assert recorded["model"]["qber"] == "3/100"
    # THERE IS NO REQUESTED TIER TO RECORD, AND THE ABSENCE IS ASSERTED.
    # `meat-core` takes no requested tier, so `RunConfig` has no such field
    # (see `certiqs_key.runs.config`). The record says what was asked for
    # without the script beside it, and what was asked for includes no tier,
    # because the ACHIEVED tier is reported on the result
    # (spec/architecture.md 2.8).
    assert "requested_assurance" not in recorded
    assert recorded["declared_tolerance"] == 0.0


# ---------------------------------------------------------------------------
# a negative objective is a REFUSAL of this tier, not an exception out of it
# ---------------------------------------------------------------------------


def test_a_negative_objective_is_recorded_as_a_refusal_not_raised(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The solver still raises; THIS TIER turns it into data.

    The hard error stays where it is -- the ``h_low`` output row forbids
    clamping and "zero cannot stand in for it", so a solver that returned
    ``0.0`` here would report a plausible number in place of a detected
    inconsistency. A CALLER SWEEPING INTO THE NO-KEY REGION would get a
    traceback with no reason code to file the point under, so a sweep would
    return results and crashes mixed together.

    THE REASON CODE IS THE SOLVER'S OWN and is not invented here, which is what
    :class:`SliceRefusal` requires of every reason it carries.

    The error is INJECTED rather than provoked by a physical point. A real one
    exists -- the optical instance at cutoff 1 with NO exact window, half a
    decibel of loss -- but pinning it would make this test a statement about
    where the no-key region begins, which is a physics question under active
    review and not what this test is about.
    """
    from instances.bb84.surface import default_config, runner

    from certiqs_key.meat_core.reasons import RefusalReason
    from certiqs_key.runs import pipeline as pipeline_module
    from certiqs_key.runs.flow import STAGE_ORDER, SliceStage, StageStatus
    from certiqs_key.solvers.frank_wolfe import NegativeObjectiveError

    def _raise(*_args: object, **_kwargs: object) -> object:
        raise NegativeObjectiveError(
            "injected",
            reason=RefusalReason.NEGATIVE_OBJECTIVE,
            value=-1.0111189167763294e-10,
            point={},
        )

    monkeypatch.setattr(pipeline_module, "solve_bundle", _raise)

    class _UnusedOracle:
        """Never touched: the run refuses inside the call this test replaced."""

    outcome = runner(
        _UnusedOracle(), tmp_path / "bundles", created_by="tests.unit"
    )(default_config(), 0)

    assert isinstance(outcome, SliceRefusal)
    assert outcome.stage is SliceStage.SOLVE
    assert outcome.reason == "negative_objective"
    assert "injected" in outcome.detail
    # The compilation is carried, because a caller diagnosing a near-zero point
    # needs the alphabet and the declaration it was computed on.
    assert outcome.compilation is not None

    # AND THE COMPOSITION FLOW SAYS SO: the solve stage refused and every stage
    # after it did not run. A refusal that left the graph looking like a
    # completed run would be worse than a traceback.
    by_stage = {record.stage: record for record in outcome.stages}
    assert by_stage[SliceStage.SOLVE].status is StageStatus.REFUSED
    assert by_stage[SliceStage.SOLVE].reason == "negative_objective"
    assert all(
        record.status is not StageStatus.EXECUTED
        for stage, record in by_stage.items()
        if STAGE_ORDER.index(stage) > STAGE_ORDER.index(SliceStage.SOLVE)
    )

