"""A proved contradiction refuses a searched run as a whole, and stops the search.

Where every alpha with ``alpha - 1`` from 1e-5 to 0.115 is refused with
``entropy_bound_above_key_ceiling``, the search must not score those ``-inf``,
choose the one alpha that slipped through, and end ``done`` with a key six
times too large. Such a refusal proves ``D_min > 0``, which does not depend
on alpha (certiqs_key.runs.plausibility, "A BOUND ABOVE THE CEILING PROVES A
CONTRADICTION"). Held here (certiqs_key.runs.alpha_search, "A PROVED
CONTRADICTION REFUSES THE RUN"):

* the search stops at the first such evaluation, on the grid or in the
  refinement, chooses nothing, and keeps every evaluation made up to it;
* the proof wins over a set-aside and over passing evaluations with keys;
* every other refusal still scores ``-inf`` and the search goes on;
* the runner returns the proving evaluation's own refusal, its detail saying
  the run was refused as a whole at that alpha, the ``alpha`` child's status
  ``contradiction``, and the record validates against its schema.

Synthetic evaluators and stand-in outcomes, as in
tests/unit/test_runs_alpha_search.py and test_runs_alpha_search_wiring.py.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.alpha_search import (
    CONTRADICTION_REASON,
    CONTRADICTION_RULE,
    AlphaPoint,
    AlphaSearchResult,
    AlphaSearchSettings,
    search_alpha,
    searching_runner,
)
from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.errors import RunRefusalReason
from certiqs_key.runs.flow import StageChild, StageRecord, StageStatus
from certiqs_key.runs.pipeline import SliceRefusal
from certiqs_key.runs.record import record_run
from certiqs_key.runs.stages import SliceStage

jsonschema = pytest.importorskip("jsonschema")

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = AlphaSearchSettings()
SMALL = AlphaSearchSettings(lower=1e-4, upper=0.1, coarse_points=3, refine_steps=2)


def _near(alpha: float, target: float) -> bool:
    return abs(alpha - target) <= 1e-9 * target


def _proved() -> AlphaPoint:
    return AlphaPoint(score=-math.inf, key_length=None, reason=CONTRADICTION_REASON)


def _evaluator(
    calls: list[float],
    *,
    proves: Callable[[float], bool] = lambda alpha: False,
    refuses: Callable[[float], bool] = lambda alpha: False,
) -> Callable[[float], AlphaPoint]:
    """Return a key peaked at ``alpha - 1 = 7e-3``; ``proves`` alphas prove one."""

    def evaluate(alpha: float) -> AlphaPoint:
        calls.append(alpha)
        if proves(alpha):
            return _proved()
        if refuses(alpha):
            return AlphaPoint(
                score=-math.inf, key_length=None, reason="solve: negative_objective"
            )
        t = math.log(alpha - 1.0) - math.log(7e-3)
        key = 3.4e5 - 1e4 * t * t
        return AlphaPoint(
            score=key, key_length=int(key), h_lb=0.024, h_low=0.024, reason="ok"
        )

    return evaluate


def test_the_reason_is_the_run_tier_refusal_as_an_evaluation_records_it() -> None:
    assert CONTRADICTION_REASON == "solve: entropy_bound_above_key_ceiling"
    assert CONTRADICTION_REASON.endswith(
        str(RunRefusalReason.ENTROPY_BOUND_ABOVE_KEY_CEILING)
    )
    assert _proved().proves_contradiction
    other = AlphaPoint(score=-math.inf, key_length=None, reason="solve: x")
    assert not other.proves_contradiction


@pytest.mark.parametrize("index", [0, 2, 5])
def test_a_proof_on_the_grid_stops_the_search_there(index: int) -> None:
    grid = [float(f"{a:.12g}") for a in SETTINGS.coarse_grid()]
    calls: list[float] = []
    result = search_alpha(
        _evaluator(calls, proves=lambda a: _near(a, grid[index])), SETTINGS
    )
    # Nothing after the proof was evaluated, and nothing was chosen.
    assert calls == grid[: index + 1]
    assert [e.alpha for e in result.evaluations] == grid[: index + 1]
    assert result.chosen is None and result.alpha is None
    assert result.contradiction is not None
    assert result.contradiction.alpha == grid[index]
    assert result.contradiction is result.evaluations[-1]
    payload = result.as_payload()
    json.dumps(payload)
    assert payload["chosen_alpha"] is None
    assert payload["contradiction_alpha"] == grid[index]
    assert payload["contradiction_rule"] == CONTRADICTION_RULE
    assert payload["evaluations"][-1]["reason"] == CONTRADICTION_REASON
    # The evaluations before it had keys, and none was chosen.
    assert all(e["key_length"] for e in payload["evaluations"][:-1])


def test_a_proof_in_the_refinement_stops_it_and_wins_over_every_key() -> None:
    unproved: list[float] = []
    search_alpha(_evaluator(unproved), SETTINGS)
    second = unproved[SETTINGS.coarse_points + 1]
    calls: list[float] = []
    result = search_alpha(
        _evaluator(calls, proves=lambda a: _near(a, second)), SETTINGS
    )
    # The same search up to the proof, and not one evaluation after it.
    assert calls == unproved[: SETTINGS.coarse_points + 2]
    assert len(result.evaluations) == SETTINGS.coarse_points + 2
    assert result.chosen is None
    assert result.contradiction is not None and _near(
        result.contradiction.alpha, second
    )
    assert result.contradiction.phase == "refine"


def test_the_proof_wins_over_a_set_aside_evaluation() -> None:
    """A set-aside reads a wide bracket; the proof a bound above the ceiling."""
    grid = [float(f"{a:.12g}") for a in SETTINGS.coarse_grid()]

    def evaluator(calls: list[float], proves: float | None) -> Any:
        def evaluate(alpha: float) -> AlphaPoint:
            calls.append(alpha)
            if proves is not None and _near(alpha, proves):
                return _proved()
            wide = _near(alpha, grid[1])
            return AlphaPoint(
                score=1e5 + alpha,
                key_length=100_000,
                h_lb=0.024 - (0.072 if wide else 1e-6),
                h_low=0.024,
                reason="ok",
            )

        return evaluate

    unproved: list[float] = []
    before = search_alpha(evaluator(unproved, None), SETTINGS)
    assert before.evaluations[1].point.set_aside is not None
    first_refine = unproved[SETTINGS.coarse_points]
    result = search_alpha(evaluator([], first_refine), SETTINGS)
    # The set-aside stays recorded, and the proof decides the run.
    assert result.evaluations[1].point.set_aside is not None
    assert result.chosen is None and result.contradiction is not None
    assert _near(result.contradiction.alpha, first_refine)


def test_every_other_refusal_still_lets_the_search_go_on() -> None:
    grid = [float(f"{a:.12g}") for a in SETTINGS.coarse_grid()]
    calls: list[float] = []
    result = search_alpha(
        _evaluator(calls, refuses=lambda a: _near(a, grid[0])), SETTINGS
    )
    assert result.contradiction is None and result.chosen is not None
    assert len(calls) == SETTINGS.coarse_points + SETTINGS.refine_steps
    assert result.as_payload()["contradiction_alpha"] is None


def test_a_result_with_a_proof_chooses_nothing() -> None:
    evaluation = search_alpha(_evaluator([]), SMALL).evaluations[0]
    with pytest.raises(ValueError, match="chooses no alpha"):
        AlphaSearchResult(
            settings=SMALL,
            evaluations=(evaluation,),
            chosen=evaluation,
            contradiction=evaluation,
        )


# ===========================================================================
#  The runner and the record
# ===========================================================================


@dataclass(frozen=True)
class _Ran:
    """A stand-in completed outcome: what the search reads and attaches to."""

    key_rate: Any
    bundle: Path
    stages: tuple[StageRecord, ...] = ()
    alpha_search: Any = None


def _config(**changes: object) -> RunConfig:
    base = {
        "rounds": 10_000,
        "completeness_budget": F(1, 1_000_000),
        "parameters": KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=7
        ),
        "declared_tolerance": 1e-12,
        "model": {"qber": F(1, 50)},
    }
    return RunConfig(**{**base, **changes})  # type: ignore[arg-type]


def _one_alpha(
    calls: list[float], proves: Callable[[float], bool]
) -> Callable[[RunConfig, Path], Any]:
    """Return a one-alpha run: a key peaked in alpha, or the plausibility refusal."""

    def run_at(point: RunConfig, bundle: Path) -> Any:
        assert point.alpha is not None
        calls.append(point.alpha)
        if proves(point.alpha):
            detail = f"the accepted statistics contradict ... (at {point.alpha})"
            solve = StageRecord(
                stage=SliceStage.SOLVE,
                module="meat-core",
                status=StageStatus.REFUSED,
                reason=str(RunRefusalReason.ENTROPY_BOUND_ABOVE_KEY_CEILING),
                refusal_detail=detail,
                detail={"refused_by": "runs", "plausibility": {"exceeded": True}},
            )
            return SliceRefusal(
                stage=SliceStage.SOLVE,
                reason=str(RunRefusalReason.ENTROPY_BOUND_ABOVE_KEY_CEILING),
                detail=detail,
                stages=(solve,),
                plausibility={"exceeded": True, "alpha": point.alpha},
            )
        t = math.log(point.alpha - 1.0) - math.log(3e-3)
        key_length = int(1e6 - 1e5 * t * t)
        rate = SimpleNamespace(
            key_length=key_length, h_lb=0.4, h_low=0.4, reference_bracket=None,
            rounds=point.rounds, alpha=point.alpha,
            key_length_reason_code="first_order_reported",
        )
        child = StageChild(
            name="alpha", status="chosen",
            detail={"alpha": point.alpha, "key_length": key_length, "searched": False},
        )
        solve = StageRecord(
            stage=SliceStage.SOLVE, module="meat-core",
            status=StageStatus.EXECUTED, children=(child,),
        )
        return _Ran(key_rate=rate, bundle=bundle, stages=(solve,))

    return run_at


def test_the_runner_returns_the_proving_refusal_with_the_whole_run_sentence(
    tmp_path: Path,
) -> None:
    grid = [float(f"{a:.12g}") for a in SMALL.coarse_grid()]
    calls: list[float] = []
    run = searching_runner(_one_alpha(calls, lambda a: _near(a, grid[1])), tmp_path)
    outcome = run(_config(alpha_search=SMALL), 0)
    assert calls == grid[:2]
    assert isinstance(outcome, SliceRefusal)
    assert outcome.reason == "entropy_bound_above_key_ceiling"
    # The proving evaluation's own refusal, not the first evaluation's run.
    assert outcome.plausibility == {"exceeded": True, "alpha": grid[1]}
    assert outcome.detail.startswith("the accepted statistics contradict")
    assert f"stopped at alpha = {grid[1]!r}" in outcome.detail
    assert "refused as a whole" in outcome.detail
    search = outcome.alpha_search
    assert search is not None and search.chosen is None
    assert search.contradiction is not None and search.contradiction.alpha == grid[1]
    (solve,) = outcome.stages
    assert solve.refusal_detail == outcome.detail
    (child,) = solve.children
    assert child.name == "alpha" and child.status == "contradiction"
    assert child.detail["contradiction_alpha"] == grid[1]
    assert child.detail["chosen_alpha"] is None
    assert [e["alpha"] for e in child.detail["evaluations"]] == grid[:2]


def test_a_searched_run_refused_as_a_whole_records_and_validates(
    tmp_path: Path,
) -> None:
    grid = [float(f"{a:.12g}") for a in SMALL.coarse_grid()]
    searched = _config(alpha_search=SMALL)
    run = searching_runner(_one_alpha([], lambda a: _near(a, grid[0])), tmp_path)
    outcome = run(searched, 0)
    record = record_run(outcome, searched, created_by="test").as_dict()
    schema = json.loads(
        (ROOT / "src" / "certiqs_key" / "runs" / "record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    # The stand-in's plausibility block is not the check's own; the record's
    # shape around it is what is held here.
    del record["payload"]["stages"]["solve"]["plausibility"]
    jsonschema.validate(record, schema)
    payload = record["payload"]
    assert payload["refused"] is True
    stage = payload["stages"]["solve"]
    assert stage["reason"] == "entropy_bound_above_key_ceiling"
    assert "refused as a whole" in stage["detail"]
    (solve,) = payload["composition_flow"]["stages"]
    (child,) = solve["children"]
    assert child["status"] == "contradiction"
    assert child["detail"]["contradiction_alpha"] == grid[0]
    assert len(child["detail"]["evaluations"]) == 1
