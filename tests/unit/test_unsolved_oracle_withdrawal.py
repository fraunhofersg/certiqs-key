"""An unsolved linear oracle ends a search stage; it does not end the point.

A QICS ``unknown`` status (exit ``slow_progress``) at one checkpoint
assessment must not discard a bracket an earlier assessment certified on its
own optimal return, nor stop the alpha search. What is held here:

* a portfolio checkpoint whose oracle raises a status that is neither optimal
  nor an infeasibility verdict, after a bracket is formed, FORMS ITS BRACKET
  with the multipliers the solves left -- zero here, the stub returning no
  dual -- ``req:first-order-withdrawal`` says "neither the point the oracle returned at
  that iterate nor its status removes the iterate", and
  ``req:verified-feasible-side`` (ii) bounds a group "whose solve returned no
  finite dual, whatever its status" with zero multipliers. Its status is
  recorded, its stage ended, and every bracket kept;
* an infeasibility verdict (``pinfeas``, ``def:admissible-declaration`` (vii))
  still stops the solve, and so does an unsolved status met before anything
  was certified, and so does any unsolved status in an explicit FW run, whose
  replay is unchanged;
* the QICS adapter tags its status raise with the status and the verdict;
* the outer alpha search records an evaluation that raised an unsolved failure
  as refused (``solve: oracle_failure``, a declared ``RunRefusalReason``) and
  chooses among the rest; where every evaluation raised, the failure is raised.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from tests.support.general_toys import (
    decoy_like_general,
    honest_q,
    maps_of,
    random_choi_point,
)
from tests.unit.test_meat_joint_driver import _EchoOracle

from certiqs_key.runs.alpha_search import (
    AlphaPoint,
    AlphaSearchSettings,
    search_alpha,
    searching_runner,
)
from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.errors import RunRefusalReason
from certiqs_key.runs.pipeline import SliceRefusal
from certiqs_key.runs.stages import SliceStage
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    joint_initial_point,
    run_joint_frank_wolfe,
)
from certiqs_key.solvers.oracles.acceptance import SingletonAcceptanceOracle
from certiqs_key.solvers.oracles.protocol import (
    OracleFailure,
    OracleSolution,
    SectorChoiProblem,
)
from certiqs_key.solvers.problem import prepared_from_maps
from certiqs_key.solvers.types import SearchRequest

pytestmark = pytest.mark.contract

UNSOLVED = "unknown"
TARGET = 1e-300
REFUSED = f"{SliceStage.SOLVE}: {RunRefusalReason.ORACLE_FAILURE}"


def _unsolved() -> OracleFailure:
    return OracleFailure(
        "the linear oracle returned status 'unknown' (exit 'slow_progress') (test)",
        status=UNSOLVED,
    )


def _infeasible() -> OracleFailure:
    return OracleFailure(
        "the linear oracle returned status 'pinfeas' (test)",
        status="pinfeas",
        infeasible=True,
    )


class _FailingEcho(_EchoOracle):
    """The echo oracle, raising the queued ``failures`` one call at a time.

    While the queue is not empty each call raises its head, after ``skip``
    calls that still answer, so a test decides exactly which oracle call, and
    so which assessment, fails.
    """

    def __init__(self, point: Mapping[Any, Any], *, trusted: bool) -> None:
        super().__init__(point, trusted=trusted)
        self.failures: list[OracleFailure] = []
        self.skip = 0

    def minimize(self, problem: SectorChoiProblem) -> OracleSolution:
        if self.failures:
            if self.skip > 0:
                self.skip -= 1
            else:
                raise self.failures.pop(0)
        return super().minimize(problem)


def _problem(max_iterations: int = 1) -> tuple[Any, _FailingEcho]:
    maps = maps_of(decoy_like_general())
    point = joint_initial_point(maps.parametrization)
    # The echoed vertex is another coupling point, so the gap is not zero, and
    # the target is below it: the initial assessment does not end the solve.
    oracle = _FailingEcho(random_choi_point(maps.parametrization, 1), trusted=True)
    problem = prepared_from_maps(
        maps,
        oracle,
        SingletonAcceptanceOracle(honest_q(maps, point)),
        1.5,
        FrankWolfeOptions(max_iterations=max_iterations, gap_tolerance=TARGET),
    )
    return problem, oracle


def _search_meeting(
    oracle: _FailingEcho, failure: OracleFailure | None, problem: Any
) -> Any:
    """Return a stand-in search: one checkpoint, at which ``failure`` is queued."""
    from certiqs_key.solvers.search.common import SearchOutcome, initial_q

    def search(*args: Any, **kwargs: Any) -> Any:
        exact = initial_q(problem)
        if failure is not None:
            oracle.failures.append(failure)
        kwargs["checkpoint"](problem.initial, exact)
        return SearchOutcome(problem.initial, exact, 0.0, "stagnated")

    return search


# ===========================================================================
#  (a) The portfolio checkpoint bounds and ends its stage instead of aborting
# ===========================================================================


def test_an_unsolved_checkpoint_after_a_certified_one_keeps_its_bracket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test (1): the earlier bracket stands, the unsolved one is formed too."""
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.solve import solve_prepared

    problem, oracle = _problem()
    monkeypatch.setattr(
        factor, "search_factor", _search_meeting(oracle, _unsolved(), problem)
    )
    result = solve_prepared(
        problem, SearchRequest(method="factor", max_iterations=1, gap_target=TARGET)
    )
    first, withdrawn = result.gates[0], result.gates[1]
    # The initial assessment certified a bracket on its own optimal return.
    assert first.contributes and first.oracle_status == "optimal"
    # The unsolved one withdraws nothing: it contributes its bracket,
    # formed with zero multipliers, with the backend's status beside it.
    assert withdrawn.withdrawal is None
    assert withdrawn.oracle_optimal is False
    assert withdrawn.oracle_status == UNSOLVED
    assert withdrawn.feasible_side_multipliers
    assert set(withdrawn.feasible_side_multipliers.values()) <= {"zero"}
    assert math.isfinite(withdrawn.linearization)
    assert math.isfinite(withdrawn.objective)
    # h_lb is the maximum over the brackets that remain: the earlier one.
    assert result.h_lb == first.linearization
    assert result.withdrawal is None
    assert result.best_assessment is not None
    assert result.best_assessment.gate == first
    report = result.search_report
    (attempt,) = report["attempts"]
    assert attempt["termination"] == "oracle_failure"
    assert attempt["oracle_failure"]["oracle_status"] == UNSOLVED
    assert attempt["oracle_failure"]["iteration"] == withdrawn.iteration
    assert "slow_progress" in attempt["oracle_failure"]["message"]
    history = report["assessment_history"]
    assert history[1]["contributes"] is True
    assert history[1]["oracle_status"] == UNSOLVED
    assert "slow_progress" in history[1]["oracle_failure"]
    assert "oracle_failure" not in history[0]
    # The stage ended at the failure: no final checkpoint of the stand-in's
    # outcome was formed after it.
    assert len(result.gates) == 2


def test_the_auto_portfolio_goes_on_with_its_next_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The stage that met the failure ends; the schedule's next stage runs."""
    import certiqs_key.solvers.search.corrective as corrective
    import certiqs_key.solvers.search.entropy as entropy
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.solve import solve_prepared

    problem, oracle = _problem()
    monkeypatch.setattr(
        factor, "search_factor", _search_meeting(oracle, _unsolved(), problem)
    )
    for module, name in (
        (entropy, "search_entropy"),
        (corrective, "search_corrective"),
    ):
        monkeypatch.setattr(module, name, _search_meeting(oracle, None, problem))
    result = solve_prepared(
        problem, SearchRequest(method="auto", max_iterations=1, gap_target=TARGET)
    )
    terminations = [a["termination"] for a in result.search_report["attempts"]]
    assert terminations[0] == "oracle_failure"
    assert len(terminations) > 1
    withdrawn = [g for g in result.gates if g.oracle_status == UNSOLVED]
    assert len(withdrawn) == 1
    assert withdrawn[0].withdrawal is None
    assert result.h_lb == result.gates[0].linearization


def test_an_infeasibility_verdict_still_stops_the_solve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test (2): pinfeas says the declared feasible set is empty; nothing goes on."""
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.solve import solve_prepared

    problem, oracle = _problem()
    monkeypatch.setattr(
        factor, "search_factor", _search_meeting(oracle, _infeasible(), problem)
    )
    with pytest.raises(OracleFailure, match="pinfeas") as caught:
        solve_prepared(
            problem, SearchRequest(method="factor", max_iterations=1, gap_target=TARGET)
        )
    assert caught.value.infeasible and not caught.value.unsolved


def test_an_unsolved_status_before_any_bracket_still_stops_the_solve() -> None:
    """With nothing certified there is nothing to keep, and no bound is reported."""
    from certiqs_key.solvers.solve import solve_prepared

    problem, oracle = _problem()
    oracle.failures.append(_unsolved())
    with pytest.raises(OracleFailure, match="slow_progress"):
        solve_prepared(
            problem, SearchRequest(method="factor", max_iterations=1, gap_target=TARGET)
        )


def test_an_explicit_fw_run_raises_on_an_unsolved_status_as_before() -> None:
    """The FW loop does not opt in: its replay and its stop are unchanged."""
    problem, oracle = _problem()
    oracle.failures.append(_unsolved())
    with pytest.raises(OracleFailure, match="slow_progress"):
        run_joint_frank_wolfe(
            problem.maps,
            oracle,
            problem.acceptance,
            problem.initial,
            problem.alpha,
            problem.settings,
        )


def test_an_unsolved_final_checkpoint_is_bounded_and_the_bracket_kept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The checkpoint after a stage's outcome (not guarded) is bounded the same way."""
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.search.common import SearchOutcome, initial_q
    from certiqs_key.solvers.solve import solve_prepared

    problem, oracle = _problem()

    def search(*args: Any, **kwargs: Any) -> Any:
        # No checkpoint of its own; the failure meets the final one.
        oracle.failures.append(_unsolved())
        exact = initial_q(problem)
        return SearchOutcome(problem.initial, exact, 0.0, "stagnated")

    monkeypatch.setattr(factor, "search_factor", search)
    result = solve_prepared(
        problem, SearchRequest(method="factor", max_iterations=1, gap_target=TARGET)
    )
    first, withdrawn = result.gates
    assert withdrawn.withdrawal is None
    assert withdrawn.oracle_status == UNSOLVED
    assert result.h_lb == first.linearization
    history = result.search_report["assessment_history"]
    assert history[1]["oracle_status"] == UNSOLVED
    assert "slow_progress" in history[1]["oracle_failure"]
    (attempt,) = result.search_report["attempts"]
    assert attempt["termination"] == "stagnated"
    # The bounded assessment is a reference candidate like any other: it
    # contributes, and the companion re-forms its bracket with a fresh solve.
    best = [a for a, roles, _ in result.reference_candidates if "best" in roles]
    assert best and all(a.contributes for a in best)


def test_a_failure_without_a_status_at_a_checkpoint_still_stops_the_solve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On the portfolio path a status-less failure is never withdrawn."""
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.solve import solve_prepared

    problem, oracle = _problem()
    failure = OracleFailure("repair window (test)")
    monkeypatch.setattr(
        factor, "search_factor", _search_meeting(oracle, failure, problem)
    )
    with pytest.raises(OracleFailure, match="repair window") as caught:
        solve_prepared(
            problem, SearchRequest(method="factor", max_iterations=1, gap_target=TARGET)
        )
    assert caught.value is failure


def test_the_auto_fw_stage_withdraws_after_a_certified_bracket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The cold FW stage (corrective unsupported) ends on an unsolved status.

    The explicit driver keeps its raise; the portfolio's FW stage catches it
    once a bracket is certified, as a checkpoint withdraws.
    """
    import certiqs_key.solvers.search.common as common
    import certiqs_key.solvers.search.entropy as entropy
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.solve import solve_prepared

    problem, oracle = _problem()
    reason = common.capability_reason
    monkeypatch.setattr(
        common,
        "capability_reason",
        lambda p, method: "test: unsupported"
        if method == "corrective"
        else reason(p, method),
    )
    monkeypatch.setattr(
        factor, "search_factor", _search_meeting(oracle, None, problem)
    )
    monkeypatch.setattr(
        entropy, "search_entropy", _search_meeting(oracle, None, problem)
    )
    original = solve_prepared.__globals__["run_joint_frank_wolfe"]
    started: list[int] = []

    def failing_fw(*args: Any, **kwargs: Any) -> Any:
        started.append(1)
        oracle.failures.append(_unsolved())
        return original(*args, **kwargs)

    monkeypatch.setitem(solve_prepared.__globals__, "run_joint_frank_wolfe", failing_fw)
    result = solve_prepared(
        problem, SearchRequest(method="auto", max_iterations=1, gap_target=TARGET)
    )
    assert started == [1]
    assert result.h_lb == result.gates[0].linearization
    last = result.search_report["attempts"][-1]
    assert last["method"] == "fw"
    assert last["termination"] == "oracle_failure"
    assert last["oracle_failure"]["oracle_status"] == UNSOLVED
    assert "slow_progress" in last["oracle_failure"]["message"]
    assert last["oracle_failure"]["iterates_assessed"] == 0


def _auto_with_a_failing_fw_stage(
    monkeypatch: pytest.MonkeyPatch, failure: OracleFailure
) -> tuple[Any, Any, list[Any]]:
    """Return the auto solve and its problem, the FW stage failing at its 2nd iterate.

    Corrective is unsupported, so the schedule's last stage is FW from the
    cold anchor; factor and entropy are stand-ins. In the FW stage the first
    assessment's oracle calls (one per Alice sector) answer and the next call
    raises ``failure``. The third value lists the FW stage's own assessments.
    """
    import certiqs_key.solvers.search.common as common
    import certiqs_key.solvers.search.entropy as entropy
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.solve import solve_prepared

    problem, oracle = _problem(max_iterations=3)
    reason = common.capability_reason
    monkeypatch.setattr(
        common,
        "capability_reason",
        lambda p, method: "test: unsupported"
        if method == "corrective"
        else reason(p, method),
    )
    monkeypatch.setattr(
        factor, "search_factor", _search_meeting(oracle, None, problem)
    )
    monkeypatch.setattr(
        entropy, "search_entropy", _search_meeting(oracle, None, problem)
    )
    original = solve_prepared.__globals__["run_joint_frank_wolfe"]
    seen: list[Any] = []

    def failing_fw(*args: Any, **kwargs: Any) -> Any:
        observer = kwargs["assessment_observer"]

        def observe(assessment: Any) -> None:
            seen.append(assessment)
            observer(assessment)

        oracle.skip = len(problem.maps.declaration.alice_sectors)
        oracle.failures.append(failure)
        return original(*args, **{**kwargs, "assessment_observer": observe})

    monkeypatch.setitem(solve_prepared.__globals__, "run_joint_frank_wolfe", failing_fw)

    def solve() -> Any:
        return solve_prepared(
            problem, SearchRequest(method="auto", max_iterations=3, gap_target=TARGET)
        )

    return solve, problem, seen


def test_a_bracket_certified_inside_the_fw_stage_is_carried_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The FW stage's own bracket, formed before the failure, joins the maximum."""
    solve, _, seen = _auto_with_a_failing_fw_stage(monkeypatch, _unsolved())
    result = solve()
    assert len(seen) == 1 and seen[0].contributes
    # By identity: the stage starts at the anchor, which here equals the
    # initial point, so an equal gate is already there from the initial
    # checkpoint and an `in` check would pass without the carry-out.
    assert any(gate is seen[0].gate for gate in result.gates)
    contributing = [g.linearization for g in result.gates if g.contributes]
    assert result.h_lb == max(contributing)
    last = result.search_report["attempts"][-1]
    assert last["method"] == "fw"
    assert last["termination"] == "oracle_failure"
    assert last["oracle_failure"]["iterates_assessed"] == 1


def test_a_verdict_in_the_fw_stage_is_not_hidden_by_a_negative_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pinfeas is raised as itself, even where the stage's best would be refused.

    The verdict is tested before the stage's best assessment is merged, so the
    negative-objective refusal of that assessment never runs in its place.
    """
    import certiqs_key.solvers.solve as coordinator

    failure = _infeasible()
    solve, _, seen = _auto_with_a_failing_fw_stage(monkeypatch, failure)
    refuse = coordinator._refuse_negative

    def refuse_the_fw_stage(assessment: Any) -> None:
        if any(assessment is mine for mine in seen):
            raise RuntimeError("the FW stage's best is refused as negative (test)")
        refuse(assessment)

    monkeypatch.setattr(coordinator, "_refuse_negative", refuse_the_fw_stage)
    with pytest.raises(OracleFailure, match="pinfeas") as caught:
        solve()
    assert caught.value is failure
    assert len(seen) == 1


def test_a_failure_without_a_status_is_not_unsolved() -> None:
    """A spectral or repair-window failure carries no status and still stops."""
    plain = OracleFailure("spectral backend failed (test)")
    assert plain.status is None and not plain.unsolved and not plain.infeasible
    assert _unsolved().unsolved and not _unsolved().infeasible


@pytest.mark.requires_qics
@pytest.mark.parametrize(
    ("status", "infeasible"),
    [
        ("unknown", False),
        ("illposed", False),
        ("dinfeas", False),
        ("pinfeas", True),
        ("near_pinfeas", True),
    ],
)
def test_the_qics_adapter_tags_its_status_raise(
    monkeypatch: pytest.MonkeyPatch, status: str, infeasible: bool
) -> None:
    """The adapter, which alone knows its status words, names the verdict."""
    import qics

    from certiqs_key.solvers.frank_wolfe.joint_driver import (
        joint_program_for_alice_sector,
    )
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    def solve(self: Any) -> dict[str, Any]:
        return {"sol_status": status, "exit_status": "slow_progress"}

    monkeypatch.setattr(qics.Solver, "solve", solve)
    maps = maps_of(decoy_like_general())
    point = joint_initial_point(maps.parametrization)
    cost = {pair: np.eye(block.shape[0]) for pair, block in point.items()}
    alice = maps.declaration.alice_sectors[0]
    program = joint_program_for_alice_sector(maps.parametrization, alice, cost)
    with pytest.raises(OracleFailure) as caught:
        QicsSectorChoiOracle().minimize(program)
    assert caught.value.status == status
    assert caught.value.infeasible is infeasible
    assert caught.value.unsolved is not infeasible


# ===========================================================================
#  (c) The alpha search records the evaluation as refused and goes on
# ===========================================================================


def _peaked_or_failing(
    calls: list[float], failure: OracleFailure, below: float
) -> Any:
    """Return a score peaked at ``alpha - 1 = 3e-3``, raising below ``below``."""

    def evaluate(alpha: float) -> AlphaPoint:
        calls.append(alpha)
        if alpha < below:
            raise failure
        t = math.log(alpha - 1.0) - math.log(3e-3)
        score = 1e6 - 1e5 * t * t
        return AlphaPoint(score=score, key_length=max(0, int(score)), h_lb=0.4)

    return evaluate


def test_an_alpha_whose_solve_raised_is_refused_and_the_search_goes_on() -> None:
    """Test (3): the failing alpha is a recorded refusal; the rest decide."""
    calls: list[float] = []
    settings = AlphaSearchSettings()
    lowest = 1.0 + settings.lower
    result = search_alpha(
        _peaked_or_failing(calls, _unsolved(), below=lowest * (1 + 1e-12)), settings
    )
    assert calls[0] == pytest.approx(lowest)
    assert len(calls) == settings.coarse_points + settings.refine_steps
    refused = result.evaluations[0]
    assert refused.point.refused
    assert refused.point.reason == REFUSED == "solve: oracle_failure"
    assert refused.point.failure is not None
    assert result.chosen is not None and result.chosen is not refused
    assert abs(math.log((result.chosen.alpha - 1.0) / 3e-3)) < 1.0
    payload = result.as_payload()
    json.dumps(payload)
    assert payload["evaluations"][0] == {
        "alpha": refused.alpha,
        "phase": "coarse",
        "key_length": None,
        "h_lb": None,
        "score": None,
        "reason": "solve: oracle_failure",
        "seconds": refused.seconds,
        "h_low": None,
        "relative_gap": None,
        "set_aside": None,
    }


def test_an_infeasibility_verdict_stops_the_alpha_search() -> None:
    """Empty at one alpha is empty at every alpha: the search does not go on."""
    calls: list[float] = []
    with pytest.raises(OracleFailure, match="pinfeas"):
        search_alpha(_peaked_or_failing(calls, _infeasible(), below=math.inf))
    assert len(calls) == 1


@pytest.mark.parametrize(
    "error",
    [OracleFailure("repair window (test)"), ValueError("not an oracle failure")],
)
def test_the_alpha_search_swallows_nothing_else(error: Exception) -> None:
    """Only an unsolved oracle status is a refused evaluation; the rest propagate."""
    calls: list[float] = []

    def evaluate(alpha: float) -> AlphaPoint:
        calls.append(alpha)
        raise error

    with pytest.raises(type(error)) as caught:
        search_alpha(evaluate)
    assert caught.value is error
    assert len(calls) == 1


def test_only_the_first_raising_evaluation_keeps_its_failure() -> None:
    """A failure holds its whole solve; a search keeps one, not one per alpha."""
    settings = AlphaSearchSettings()
    result = search_alpha(
        _peaked_or_failing([], _unsolved(), below=math.inf), settings
    )
    assert result.chosen is None
    assert len(result.evaluations) == settings.coarse_points
    assert {e.point.reason for e in result.evaluations} == {REFUSED}
    kept = [e for e in result.evaluations if e.point.failure is not None]
    assert kept == [result.evaluations[0]]


SMALL = AlphaSearchSettings(lower=1e-4, upper=0.1, coarse_points=3, refine_steps=1)


def _config() -> RunConfig:
    from fractions import Fraction

    from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters

    return RunConfig(
        rounds=10_000,
        completeness_budget=Fraction(1, 1_000_000),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=7
        ),
        declared_tolerance=1e-12,
        alpha_search=SMALL,
    )


@dataclass(frozen=True)
class _Ran:
    key_rate: Any
    bundle: Path
    stages: tuple[Any, ...] = ()
    alpha_search: Any = None


def test_the_runner_returns_the_chosen_run_when_the_first_alpha_raised(
    tmp_path: Path,
) -> None:
    from types import SimpleNamespace

    lowest = 1.0 + SMALL.lower

    def run_at(point: RunConfig, bundle: Path) -> _Ran:
        assert point.alpha is not None
        if point.alpha <= lowest * (1 + 1e-12):
            raise _unsolved()
        rate = SimpleNamespace(
            key_length=int(1000 * point.alpha),
            h_lb=0.4,
            h_low=0.4,
            reference_bracket=None,
            rounds=point.rounds,
            alpha=point.alpha,
            key_length_reason_code="first_order_reported",
        )
        return _Ran(key_rate=rate, bundle=bundle)

    outcome: Any = searching_runner(run_at, tmp_path)(_config(), 0)
    search = outcome.alpha_search
    assert search is not None and search.chosen is not None
    assert outcome.key_rate.alpha == search.alpha
    assert search.evaluations[0].point.reason == REFUSED
    # The outcome carries no failure (nor any run) of the other evaluations.
    assert all(e.point.failure is None for e in search.evaluations)


def test_the_runner_returns_the_first_refusal_when_the_rest_raised(
    tmp_path: Path,
) -> None:
    lowest = 1.0 + SMALL.lower

    def run_at(point: RunConfig, bundle: Path) -> SliceRefusal:
        assert point.alpha is not None
        if point.alpha <= lowest * (1 + 1e-12):
            raise _unsolved()
        return SliceRefusal(
            stage=SliceStage.SOLVE,
            reason="negative_objective",
            detail=f"at alpha {point.alpha}",
        )

    outcome = searching_runner(run_at, tmp_path)(_config(), 0)
    assert isinstance(outcome, SliceRefusal)
    assert outcome.alpha_search is not None
    assert outcome.alpha_search.chosen is None
    reasons = [e.point.reason for e in outcome.alpha_search.evaluations]
    assert reasons[0] == REFUSED
    assert set(reasons[1:]) == {"solve: negative_objective"}
    # The first evaluation that returned an outcome is the one returned.
    second = outcome.alpha_search.evaluations[1].alpha
    assert outcome.detail == f"at alpha {second}"


def test_the_runner_raises_the_first_failure_when_every_alpha_raised(
    tmp_path: Path,
) -> None:
    failures: list[OracleFailure] = []

    def run_at(point: RunConfig, bundle: Path) -> SliceRefusal:
        failures.append(_unsolved())
        raise failures[-1]

    with pytest.raises(OracleFailure) as caught:
        searching_runner(run_at, tmp_path)(_config(), 0)
    assert len(failures) == SMALL.coarse_points
    assert caught.value is failures[0]
