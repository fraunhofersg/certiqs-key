"""The once-per-run solve of the penalty-only program, with every pair dropped.

``meat-core/req:unreachable-acceptance-set`` (i) and (ii), the solver's part:
on the declaration the run searches and with the run's acceptance set, the
first-order search of the dropped program for the dropped set of every pair
(``meat-core/prop:minimal-divergence``) at the order ``alpha_0``, with the
method, iteration cap and gap target of one of the run's own evaluations and
the share ``STATISTICS_CHECK_BUDGET_SHARE`` of its wall budget; then the
first-order number
of that program (``frank-wolfe/cor:fo-dropped``) and, unless the run sets
``certified_evaluation`` to ``off``, its certified evaluation on the same
declaration at the solve's points (``frank-wolfe/req:certified-evaluation``
(ii)-(v), ``frank-wolfe/lem:certified-bracket`` (iv)). No other solver is
needed: with every pair dropped the objective is the scaled divergence
(``prop:minimal-divergence`` (i)).

WHAT DIFFERS FROM A RUN'S OWN SOLVE, AND WHY.

* No refusal. A withdrawn first-order number, a solve that did not complete,
  or an order outside ``(1, infinity)`` forms no bound and refuses nothing:
  the run proceeds with the reason recorded (item (ii)). ``strict``
  certification does not refuse here either: the check is a diagnostic of
  the model, and ``strict`` concerns the arithmetic of a reported key length.
* The sign of the estimate decides nothing. ``O_0`` is no estimate of the
  run (``frank-wolfe/req:negative-estimate-refused`` reads the run's own
  search alone), and the first-order bound holds at points of the relaxed
  set, where the objective may fall below zero
  (``frank-wolfe/rem:fo-negative-values``): on a table some feasible state
  reaches, the program's value is exactly 0 and the sign of an assessed
  objective is set by rounding and by the relaxation window. So the search
  runs with the portfolio's per-point refusal of a negative objective off
  (``refuse_negative`` of :func:`~certiqs_key.solvers.solve.solve_prepared`),
  every method runs to its own stop, ``b`` is formed from the solve's points
  whatever the sign of the estimate it returns, and a negative estimate is
  recorded as a diagnostic (``estimate_negative``).
* Its own exception boundary. What does not complete the solve is recorded,
  not raised: an oracle failure that leaves a step unsolved or carries no
  status (a backend exception, a malformed return), and a numerical failure
  (``SupportError``, ``LinAlgError``, ``ValueError``) raised by the search
  under any method: where it assesses or checks a point, or anywhere in the
  explicit Frank-Wolfe driver
  (:func:`~certiqs_key.solvers.solve.raised_assessing_a_point`); the dropped
  program is not the run's program, so its search can fail where the run's
  does not. What concerns the run is raised: the preparation's errors, which
  the run's own solve raises the same, and an infeasibility verdict, which
  says the run's feasible set is empty.
* No warm start. The run's seed is a point of its own program; the request is
  otherwise the run's (method, iteration cap, gap target).
* A share of the budget. Its wall budget is ``STATISTICS_CHECK_BUDGET_SHARE``
  (1/4) of the wall budget of one evaluation of the run
  (:func:`~certiqs_key.solvers.solve.evaluation_wall_budget`), where it has
  one: ``b`` is a lower bound at any effort, so a shorter solve can leave a
  mismatch unproven or the ceiling looser, and makes no bound unsound.
* No reference companion. The bound is formed on the searched declaration
  (item (ii): "whatever declaration the run's key length is formed on").
* Item (vii) of the certified evaluation does not apply: the parts are
  (ii)-(v), so a certified point gives the certified number whatever
  upstream reason would withhold a run's certified tier.
"""

from __future__ import annotations

import math
import time
from dataclasses import replace
from fractions import Fraction

from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.finitekey.consistency import (
    STATISTICS_CHECK_BUDGET_SHARE,
    DivergenceBound,
    NoBoundReason,
    StopCause,
)
from certiqs_key.meat_core.objective.joint import JointMaps, JointSector
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_driver import JointFrankWolfeResult
from certiqs_key.solvers.oracles.protocol import LinearOracle, OracleFailure
from certiqs_key.solvers.types import SearchRequest

__all__ = ["bound_minimal_divergence", "every_pair", "stop_cause"]


def every_pair(maps: JointMaps) -> tuple[tuple[str, JointSector], ...]:
    """Return the dropped set of every pair, ``Chat_key x (T x S)``.

    ``meat-core/prop:minimal-divergence``'s ``D_all`` (``def:dropped`` admits
    it): with every pair dropped no key-live term keeps a deficit.
    """
    return tuple((chat, pair) for chat in maps.chat_key for pair in maps.joint_sectors)


def stop_cause(run: JointFrankWolfeResult) -> str:
    """Return item (v)'s stop cause, the cause the solve reports stopping on.

    Item (v) names the gap target, the iteration cap and the budget as
    examples. The explicit search reports ``converged`` (its gap at the
    target), ``iteration-limit`` or ``budget_exhausted``; the portfolio
    reports its ``termination``, ``target_met`` or ``budget_exhausted`` (its
    iteration cap bounds its Frank-Wolfe stages only); these are recorded
    under the three names of :class:`StopCause`. Every other status the
    solver reports (the iterate stagnated, or stagnated with its bracket
    closed relative to its value, ``relative_gap_met``, which is not the gap
    target; a hypothesis failed and withdrew the bracket, the objective was
    infinite at the start, a stage was unsupported, an oracle failure) is
    recorded as the solver states it.
    """
    status = run.status
    if status in ("converged", "target_met"):
        return str(StopCause.GAP_TARGET)
    if status == "iteration-limit":
        return str(StopCause.ITERATION_CAP)
    if status == "budget_exhausted":
        return str(StopCause.BUDGET)
    return str(status)


def _request_of(
    request: SearchRequest | None, options: FrankWolfeOptions | None
) -> SearchRequest:
    """Return the solve's request: the run's, no warm start, a share of its budget.

    The method, iteration cap and gap target are those of one evaluation of
    the run; the wall budget is ``STATISTICS_CHECK_BUDGET_SHARE`` of that
    evaluation's (``req:unreachable-acceptance-set`` (i)), and none where the
    evaluation has none.
    """
    from certiqs_key.solvers.solve import evaluation_wall_budget

    chosen = request if request is not None else SearchRequest.from_options(options)
    wall = evaluation_wall_budget(chosen)
    return replace(
        chosen,
        warm_start=None,
        budget_seconds=(
            None if wall is None else wall * float(STATISTICS_CHECK_BUDGET_SHARE)
        ),
    )


def bound_minimal_divergence(
    d: GeneralDeclaration,
    oracle: LinearOracle,
    *,
    alpha_0: float,
    request: SearchRequest | None = None,
    options: FrankWolfeOptions | None = None,
    eps_auth: float = 0.0,
) -> DivergenceBound:
    """Run items (i) and (ii) of ``meat-core/req:unreachable-acceptance-set``.

    ``d`` is the declaration the run searches, ``alpha_0`` the order fixed
    before any order is evaluated, ``request``/``options`` the search request
    of one of the run's evaluations (its ``certified_evaluation`` option is
    read; ``strict`` acts as ``on`` here), the solve getting
    ``STATISTICS_CHECK_BUDGET_SHARE`` of its wall budget. Returns ``b`` with
    its tier, or the reason none was formed, and what item (v) records of the
    solve: the share and budget, the estimate and whether it is negative.

    Raises what the run's own preparation raises (an inadmissible
    declaration, a vacuous security statement, a capability the oracle lacks)
    and an :class:`~certiqs_key.solvers.oracles.protocol.OracleFailure` that is
    an infeasibility verdict: those concern the run, not this check. Every
    other oracle failure, and a numerical failure where the search assesses a
    point, is returned as ``solve_not_completed`` with what failed in ``detail``
    (the module docstring's "own exception boundary"). Any other exception is
    raised as the defect it is.
    """
    from certiqs_key.solvers.frank_wolfe.general_keyrate import _certify, _run_general
    from certiqs_key.solvers.problem import _prepare_general
    from certiqs_key.solvers.solve import NUMERICAL_FAILURES, raised_assessing_a_point

    started = time.perf_counter()
    if not (math.isfinite(alpha_0) and alpha_0 > 1.0):
        return DivergenceBound(
            alpha_0=alpha_0,
            bound=None,
            tier=None,
            no_bound_reason=NoBoundReason.ALPHA_OUTSIDE_OBJECTIVE_DOMAIN,
            detail=(
                "meat-core/req:objective-alpha-domain: the program is evaluated "
                f"only at an order in (1, infinity), and alpha_0 = {alpha_0!r}; "
                "the solve is refused and does not run"
            ),
        )
    chosen = _request_of(request, options)
    budget = {
        "budget_share": STATISTICS_CHECK_BUDGET_SHARE,
        "budget_seconds": chosen.budget_seconds,
    }
    preparation_started = time.perf_counter()
    maps, acceptance = _prepare_general(d, oracle, eps_auth=eps_auth)
    preparation_seconds = time.perf_counter() - preparation_started
    dropped = every_pair(maps)
    try:
        run = _run_general(
            maps,
            oracle,
            acceptance,
            alpha_0,
            None,
            dropped,
            None,
            None,
            chosen,
            preparation_seconds,
            refuse_negative=False,
        )
    except OracleFailure as failure:
        if failure.infeasible:
            raise
        return DivergenceBound(
            alpha_0=alpha_0,
            bound=None,
            tier=None,
            no_bound_reason=NoBoundReason.SOLVE_NOT_COMPLETED,
            stop_cause="oracle_failure",
            **budget,  # type: ignore[arg-type]
            detail=(
                f"the linear oracle left a step unsolved (status {failure.status!r}): "
                f"{failure}"
                if failure.unsolved
                else f"the linear oracle failed without a status: {failure}"
            ),
            seconds=time.perf_counter() - started,
        )
    except NUMERICAL_FAILURES as failure:
        if not raised_assessing_a_point(failure):
            raise
        return DivergenceBound(
            alpha_0=alpha_0,
            bound=None,
            tier=None,
            no_bound_reason=NoBoundReason.SOLVE_NOT_COMPLETED,
            stop_cause="numerical_failure",
            **budget,  # type: ignore[arg-type]
            detail=(
                "the search failed numerically "
                f"({type(failure).__name__}): {failure}"
            ),
            seconds=time.perf_counter() - started,
        )
    first_order = run.h_lb_dropped if run.dropped_set else run.h_lb
    common = {
        "alpha_0": alpha_0,
        "stop_cause": stop_cause(run),
        "solver_status": run.status,
        "termination": run.search_report.get("termination"),
        "estimate": run.objective,
        "estimate_relaxed_member": run.estimate_point_relaxed_member,
        "first_order": first_order,
        "withdrawal": run.withdrawal,
        "iterations": run.iterations,
        **budget,
    }
    # THE SIGN OF THE ESTIMATE DECIDES NOTHING (item (ii)): b is formed from
    # the solve's points whatever it is; a negative O_0 is recorded
    # (DivergenceBound.estimate_negative) and refuses nothing.
    if first_order is None or not math.isfinite(first_order):
        return DivergenceBound(
            **common,  # type: ignore[arg-type]
            bound=None,
            tier=None,
            no_bound_reason=NoBoundReason.FIRST_ORDER_WITHDRAWN,
            detail=(
                "the first-order number of the dropped program is withdrawn "
                f"({run.withdrawal}): no iterate contributed a bracket"
                if first_order is None
                else f"the first-order number of the dropped program is "
                f"{first_order!r}, not a finite number"
            ),
            seconds=time.perf_counter() - started,
        )
    option = "off" if chosen.certified_evaluation == "off" else "on"
    certification = _certify(
        maps,
        run,
        None,
        acceptance,
        alpha_0,
        option=option,
        companion=None,
        withheld=(),
    )
    record = certification.as_record(
        first_order=first_order, first_order_key_length=None
    )
    certified = certification.certified_bound
    return DivergenceBound(
        **common,  # type: ignore[arg-type]
        bound=Fraction(first_order) if certified is None else certified,
        tier="first-order" if certified is None else "certified",
        certification=record,
        seconds=time.perf_counter() - started,
    )
