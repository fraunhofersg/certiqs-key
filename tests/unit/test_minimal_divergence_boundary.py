"""The statistics check's solve: what it records and what it raises.

WHY THIS EXISTS. ``meat-core/req:unreachable-acceptance-set`` (ii): the
check's solve "is not refused on the sign of its estimate O_0 ...: b is formed
from the solve's points whatever that sign, and a negative O_0 is recorded as
a diagnostic and refuses nothing"; where no bound is formed (the first-order
number withdrawn, the solve not completed, or an order outside
``(1, infinity)``) the run proceeds with the reason recorded. On a table some
feasible state reaches, the penalty-only program's value is exactly 0, so the
sign of a computed objective is a matter of the last bit times
``alpha_0 / (alpha_0 - 1)``. In the key-rate solve the portfolio methods
refuse at the first negative point they assess
(``frank-wolfe/req:negative-estimate-refused``, which binds the run's own
search alone); in the check such a refusal would escape and refuse the run.
Method ``fw`` never refuses at a point, so a test on it alone cannot see this:
every method is tested.

What is held here, on the qubit BB84 toy with the QICS oracle:

* THE ULP CASE UNDER EVERY METHOD. The objective is replaced by the value of
  a one-ulp mismatch, ``-(alpha/(alpha-1)) ulp(1/2) / ln 2`` (a distribution
  entry of 1/2 one ulp high, as in the investigation of the defect), at every
  point. The check returns, with no exception, a bound ``b`` formed from the
  solve's points, not positive on this reachable table, with that estimate
  recorded as negative; the key-rate solve of the same declaration still
  refuses with ``NegativeObjectiveError``.
* THE BUDGET SHARE: the solve's request carries a quarter of the run's wall
  budget (``STATISTICS_CHECK_BUDGET_SHARE``), the record says so, and an
  evaluation with no wall budget gives the solve none.
* ITS OWN EXCEPTION BOUNDARY. An oracle failure without a status and a
  numerical failure (``SupportError``, ``LinAlgError``, ``ValueError``) where
  the search assesses or checks a point, under any method, are recorded as
  ``solve_not_completed``; an infeasibility verdict, a programming error and
  a numerical failure of the preparation are raised, and the key-rate solve
  raises what it always raised, its cause chain intact.
* EVERY OTHER NO-BOUND BRANCH: a withdrawn first-order number, and an order
  outside ``(1, infinity)``, at which no solve runs.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
from tests.support.general_toys import qubit_bb84_general

from certiqs_key.meat_core.errors import SupportError
from certiqs_key.meat_core.finitekey.consistency import (
    STATISTICS_CHECK_BUDGET_SHARE,
    NoBoundReason,
)
from certiqs_key.solvers import solve as solve_module
from certiqs_key.solvers.frank_wolfe import joint_driver
from certiqs_key.solvers.frank_wolfe.general_keyrate import (
    NegativeObjectiveError,
    solve_general,
)
from certiqs_key.solvers.frank_wolfe.minimal_divergence import (
    bound_minimal_divergence,
)
from certiqs_key.solvers.oracles.protocol import OracleFailure
from certiqs_key.solvers.types import SEARCH_METHODS, SearchRequest

pytestmark = pytest.mark.requires_qics

ALPHA = 1.5
#: D(q || P) with one entry 1/2 of P one ulp above q's: -ulp(1/2)/ln 2 to
#: first order, times alpha/(alpha-1) = 3 in the objective.
ULP_CASE = -(ALPHA / (ALPHA - 1)) * math.ulp(0.5) / math.log(2)


def _oracle() -> Any:
    pytest.importorskip("qics")
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    return QicsSectorChoiOracle()


def _request(method: str) -> SearchRequest:
    return SearchRequest(method=method, budget_seconds=2.0, max_iterations=20)


@pytest.fixture
def ulp_objective(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every objective value the driver and the assessor form is the ulp case."""
    original = joint_driver.joint_objective_value

    def shifted(*args: Any, **kwargs: Any) -> float:
        original(*args, **kwargs)
        return ULP_CASE

    monkeypatch.setattr(joint_driver, "joint_objective_value", shifted)


@pytest.mark.parametrize("method", SEARCH_METHODS)
@pytest.mark.usefixtures("ulp_objective")
def test_a_negative_estimate_forms_a_bound_and_raises_nothing(method: str) -> None:
    """Item (ii): b is formed whatever the sign of O_0; O_0 < 0 is recorded.

    The table is reachable (the toy's honest law), so the value is exactly 0
    and b, a lower bound on it, is not positive: no mismatch is proven.
    """
    bound = bound_minimal_divergence(
        qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=_request(method)
    )
    assert bound.no_bound_reason is None
    assert bound.bound is not None and bound.tier in ("certified", "first-order")
    assert bound.bound <= 0
    assert bound.estimate == ULP_CASE and bound.estimate_negative is True
    record = bound.as_record()
    assert record["estimate_negative"] is True and record["no_bound_reason"] is None


@pytest.mark.parametrize(
    ("request_", "expected"),
    [
        (SearchRequest(method="auto", budget_seconds=8.0), 2.0),
        (SearchRequest(method="auto"), 30.0),  # the portfolio's 120 s default
        (SearchRequest(method="fw", budget_seconds=4.0), 1.0),
        (SearchRequest(method="fw"), None),  # no wall budget: none given
    ],
)
def test_the_check_s_solve_gets_a_quarter_of_the_evaluation_s_budget(
    monkeypatch: pytest.MonkeyPatch, request_: SearchRequest, expected: float | None
) -> None:
    """Item (i): the solve gets statistics_check_budget_share of the wall budget.

    That share of one evaluation's wall budget, recorded with the solve; the
    method, cap and gap target are the run's.
    """
    from certiqs_key.solvers.frank_wolfe import general_keyrate

    seen: list[SearchRequest] = []
    original = general_keyrate._run_general

    def spy(*args: Any, **kwargs: Any) -> Any:
        seen.append(args[8])
        return original(*args, **kwargs)

    monkeypatch.setattr(general_keyrate, "_run_general", spy)
    bound = bound_minimal_divergence(
        qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=request_
    )
    (chosen,) = seen
    assert chosen.budget_seconds == expected
    assert (chosen.method, chosen.max_iterations, chosen.gap_target) == (
        request_.method, request_.max_iterations, request_.gap_target
    )
    assert chosen.warm_start is None
    assert bound.budget_share == STATISTICS_CHECK_BUDGET_SHARE == 1 / 4
    assert bound.budget_seconds == expected
    record = bound.as_record()
    assert record["budget_share"] == "1/4" and record["budget_seconds"] == expected


@pytest.mark.parametrize("method", SEARCH_METHODS)
@pytest.mark.usefixtures("ulp_objective")
def test_the_key_rate_solve_still_refuses_a_negative_estimate(method: str) -> None:
    with pytest.raises(NegativeObjectiveError) as refused:
        solve_general(
            qubit_bb84_general(), _oracle(), alpha=ALPHA, request=_request(method)
        )
    assert str(refused.value.reason) == "negative_objective"
    assert refused.value.value == ULP_CASE


@pytest.mark.usefixtures("ulp_objective")
def test_the_portfolio_goes_on_past_a_negative_point_in_the_check() -> None:
    """With the per-point refusal off, every negative point is assessed and kept.

    A gap target of 0 keeps the search from stopping at its first point, whose
    gap on the toy is already below the default target; every stage then
    stagnates within a fraction of a second, so the budget is only a cap.
    """
    from certiqs_key.solvers.frank_wolfe.general_keyrate import _run_general
    from certiqs_key.solvers.frank_wolfe.minimal_divergence import every_pair
    from certiqs_key.solvers.problem import _prepare_general

    oracle = _oracle()
    maps, acceptance = _prepare_general(qubit_bb84_general(), oracle)
    common: tuple[Any, ...] = (maps, oracle, acceptance, ALPHA, None, every_pair(maps))
    request = SearchRequest(method="auto", budget_seconds=30.0, gap_target=0.0)
    run = _run_general(*common, None, None, request, refuse_negative=False)
    history = run.search_report["assessment_history"]
    assert len(history) >= 2
    assert all(entry["objective"] == ULP_CASE for entry in history)
    assert run.objective == ULP_CASE
    with pytest.raises(NegativeObjectiveError):
        _run_general(*common, None, None, request)


class _FailingOnce:
    """The QICS oracle, whose first solve raises ``failure``."""

    def __init__(self, failure: OracleFailure) -> None:
        self.inner = _oracle()
        self.failure: OracleFailure | None = failure

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)

    def minimize(self, problem: Any) -> Any:
        if self.failure is not None:
            failure, self.failure = self.failure, None
            raise failure
        return self.inner.minimize(problem)


@pytest.mark.parametrize("method", ["fw", "auto"])
def test_an_oracle_failure_without_a_status_is_a_solve_not_completed(
    method: str,
) -> None:
    oracle = _FailingOnce(OracleFailure("backend exception"))
    bound = bound_minimal_divergence(
        qubit_bb84_general(), oracle, alpha_0=ALPHA, request=_request(method)
    )
    assert bound.no_bound_reason is NoBoundReason.SOLVE_NOT_COMPLETED
    assert bound.stop_cause == "oracle_failure"
    assert bound.detail is not None
    assert "failed without a status" in bound.detail
    assert "backend exception" in bound.detail


@pytest.mark.parametrize("method", ["fw", "auto"])
def test_an_infeasibility_verdict_concerns_the_run_and_is_raised(method: str) -> None:
    verdict = OracleFailure("empty", status="infeasible", infeasible=True)
    with pytest.raises(OracleFailure, match="empty"):
        bound_minimal_divergence(
            qubit_bb84_general(),
            _FailingOnce(verdict),
            alpha_0=ALPHA,
            request=_request(method),
        )


@pytest.mark.parametrize(
    "error",
    [np.linalg.LinAlgError("eigh did not converge"), ValueError("not finite")],
)
def test_a_numerical_failure_at_a_checkpoint_is_a_solve_not_completed(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    original = solve_module.assess_candidate
    calls = [0]

    def failing_first(*args: Any, **kwargs: Any) -> Any:
        calls[0] += 1
        if calls[0] == 1:
            raise error
        return original(*args, **kwargs)

    monkeypatch.setattr(solve_module, "assess_candidate", failing_first)
    bound = bound_minimal_divergence(
        qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=_request("auto")
    )
    assert bound.no_bound_reason is NoBoundReason.SOLVE_NOT_COMPLETED
    assert bound.stop_cause == "numerical_failure"
    assert bound.detail is not None and str(error) in bound.detail
    # The key-rate solve sees the exception it always saw.
    calls[0] = 0
    with pytest.raises(type(error)):
        solve_general(
            qubit_bb84_general(), _oracle(), alpha=ALPHA, request=_request("auto")
        )


def test_the_key_rate_solve_keeps_the_cause_chain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The mark is an attribute: the exception and its cause are the ones raised."""
    cause = KeyError("the lower-level failure")
    error = ValueError("not finite")
    error.__cause__ = cause

    def failing(*args: Any, **kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(solve_module, "assess_candidate", failing)
    with pytest.raises(ValueError) as raised:
        solve_general(
            qubit_bb84_general(), _oracle(), alpha=ALPHA, request=_request("auto")
        )
    assert raised.value is error and raised.value.__cause__ is cause
    assert solve_module.raised_assessing_a_point(raised.value)


def _stage_raising(monkeypatch: pytest.MonkeyPatch, error: Exception) -> Any:
    """Return a factor stage whose one checkpoint's assessment raises ``error``."""

    def stage(problem: Any, initial: Any, *, checkpoint: Any, **kwargs: Any) -> Any:
        def failing(*args: Any, **kwargs: Any) -> Any:
            raise error

        monkeypatch.setattr(solve_module, "assess_candidate", failing)
        checkpoint(problem.anchor, {})
        raise AssertionError("the checkpoint returned")

    return stage


def test_what_a_search_stage_checkpoint_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Through the stage's own wrap (guarded_checkpoint) and out of the stage.

    A gap target of 0 keeps the solve from stopping at its first point, so the
    factor stage runs. A SupportError is recorded as a numerical failure; a
    TypeError, a programming error, is raised as it is. Raised, the
    checkpoint's exception keeps its own cause and context: the stage's
    carrier (_AssessmentFailure) appears in neither, and the solve raises the
    SupportError the same way, marked. (It is called with the per-point
    refusal off: on this toy the key-rate program's value is 0 too, and an
    ulp-negative first point would refuse before the stage runs.)
    """
    from certiqs_key.solvers.frank_wolfe.general_keyrate import _run_general
    from certiqs_key.solvers.problem import _prepare_general
    from certiqs_key.solvers.search import factor

    request = SearchRequest(method="factor", budget_seconds=30.0, gap_target=0.0)
    monkeypatch.setattr(
        factor,
        "search_factor",
        _stage_raising(monkeypatch, SupportError("left the support face")),
    )
    bound = bound_minimal_divergence(
        qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=request
    )
    assert bound.no_bound_reason is NoBoundReason.SOLVE_NOT_COMPLETED
    assert bound.stop_cause == "numerical_failure"
    assert bound.detail is not None and "left the support face" in bound.detail
    for error in (TypeError("a programming error"), SupportError("left the face")):
        cause, context = KeyError("its cause"), IndexError("its context")
        error.__cause__, error.__context__ = cause, context
        monkeypatch.undo()
        monkeypatch.setattr(
            factor, "search_factor", _stage_raising(monkeypatch, error)
        )
        with pytest.raises(type(error)) as raised:
            if isinstance(error, TypeError):
                bound_minimal_divergence(
                    qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=request
                )
            else:
                oracle = _oracle()
                maps, acceptance = _prepare_general(qubit_bb84_general(), oracle)
                _run_general(
                    maps, oracle, acceptance, ALPHA, None, None, None, None,
                    request, refuse_negative=False,
                )
        assert raised.value is error
        assert raised.value.__cause__ is cause
        assert raised.value.__context__ is context
        assert solve_module.raised_assessing_a_point(raised.value) is isinstance(
            error, SupportError
        )


@pytest.mark.parametrize("method", ["fw", "pairwise"])
def test_a_numerical_failure_in_the_explicit_search_is_a_solve_not_completed(
    monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    def failing(*args: Any, **kwargs: Any) -> Any:
        raise SupportError("an iterate left the cone")

    monkeypatch.setattr(solve_module, "run_joint_frank_wolfe", failing)
    bound = bound_minimal_divergence(
        qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=_request(method)
    )
    assert bound.no_bound_reason is NoBoundReason.SOLVE_NOT_COMPLETED
    assert bound.stop_cause == "numerical_failure"
    assert bound.detail is not None and "left the cone" in bound.detail
    # The key-rate solve raises it as before.
    with pytest.raises(SupportError, match="left the cone"):
        solve_general(
            qubit_bb84_general(), _oracle(), alpha=ALPHA, request=_request(method)
        )


def test_a_programming_error_in_the_explicit_search_is_raised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing(*args: Any, **kwargs: Any) -> Any:
        raise TypeError("a programming error")

    monkeypatch.setattr(solve_module, "run_joint_frank_wolfe", failing)
    with pytest.raises(TypeError, match="a programming error"):
        bound_minimal_divergence(
            qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=_request("fw")
        )


def test_a_numerical_failure_in_autos_frank_wolfe_stage_is_a_solve_not_completed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The FW stage runs last under auto where corrective is unsupported."""
    from certiqs_key.solvers.search import common

    original = common.capability_reason

    def no_corrective(problem: Any, method: str) -> str | None:
        if method == "corrective":
            return "unsupported here (a fake, for this test)"
        return original(problem, method)

    def failing(*args: Any, **kwargs: Any) -> Any:
        raise np.linalg.LinAlgError("eigh did not converge")

    monkeypatch.setattr(common, "capability_reason", no_corrective)
    monkeypatch.setattr(solve_module, "run_joint_frank_wolfe", failing)
    request = SearchRequest(method="auto", budget_seconds=30.0, gap_target=0.0)
    bound = bound_minimal_divergence(
        qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=request
    )
    assert bound.no_bound_reason is NoBoundReason.SOLVE_NOT_COMPLETED
    assert bound.stop_cause == "numerical_failure"
    assert bound.detail is not None and "did not converge" in bound.detail


def test_a_numerical_failure_checking_the_returned_point_is_a_solve_not_completed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing(*args: Any, **kwargs: Any) -> Any:
        raise SupportError("returned point: non-finite block")

    monkeypatch.setattr(solve_module, "_check_point", failing)
    bound = bound_minimal_divergence(
        qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=_request("auto")
    )
    assert bound.no_bound_reason is NoBoundReason.SOLVE_NOT_COMPLETED
    assert bound.stop_cause == "numerical_failure"


def test_a_numerical_failure_of_the_preparation_is_raised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raised before the search: it concerns the run, which prepares the same."""
    from certiqs_key.solvers import problem

    def failing(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("raised preparing the problem")

    monkeypatch.setattr(problem, "prepared_from_maps", failing)
    with pytest.raises(ValueError, match="preparing the problem"):
        bound_minimal_divergence(
            qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=_request("auto")
        )


@pytest.mark.parametrize(
    ("first_order", "said"),
    [(None, "iterate_not_feasible"), (math.inf, "not a finite number")],
)
def test_a_withdrawn_first_order_number_forms_no_bound(
    monkeypatch: pytest.MonkeyPatch, first_order: float | None, said: str
) -> None:
    """The branch where no first-order number is formed.

    The search's own result is replaced by one whose estimate is 0 and whose
    first-order number is withdrawn (the reason the solver states beside it)
    or not finite.
    """
    from dataclasses import replace

    from certiqs_key.solvers.frank_wolfe import general_keyrate

    original = general_keyrate._run_general

    def withdrawn(*args: Any, **kwargs: Any) -> Any:
        run = original(*args, **kwargs)
        return replace(
            run,
            objective=0.0,
            h_lb=first_order,
            h_lb_dropped=first_order,
            withdrawal="iterate_not_feasible",
        )

    monkeypatch.setattr(general_keyrate, "_run_general", withdrawn)
    bound = bound_minimal_divergence(
        qubit_bb84_general(), _oracle(), alpha_0=ALPHA, request=_request("auto")
    )
    assert bound.bound is None
    assert bound.no_bound_reason is NoBoundReason.FIRST_ORDER_WITHDRAWN
    assert bound.withdrawal == "iterate_not_feasible"
    assert bound.estimate == 0.0
    assert bound.detail is not None and said in bound.detail


@pytest.mark.parametrize("alpha_0", [1.0, 0.5, math.inf, math.nan])
def test_an_order_outside_the_objective_domain_runs_no_solve(
    monkeypatch: pytest.MonkeyPatch, alpha_0: float
) -> None:
    from certiqs_key.solvers.frank_wolfe import general_keyrate

    def must_not_run(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("the solve ran")

    monkeypatch.setattr(general_keyrate, "_run_general", must_not_run)
    bound = bound_minimal_divergence(
        qubit_bb84_general(), _oracle(), alpha_0=alpha_0, request=_request("auto")
    )
    assert bound.bound is None and bound.stop_cause is None
    assert bound.no_bound_reason is NoBoundReason.ALPHA_OUTSIDE_OBJECTIVE_DOMAIN
