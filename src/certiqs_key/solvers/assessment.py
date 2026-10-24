"""One first-order hypothesis gate for every candidate-search method.

The gate implements meat-core/frank-wolfe/thm:firstorder (with its part (iv)),
req:first-order-withdrawal and req:verified-feasible-side. Search arithmetic
never enters this module. The FW loop reuses the returned original gradient
and the oracle's vertex for its step rather than calling either twice; the
bracket reads the vertex nowhere, its feasible side being the bound verified
from the backends' duals (:mod:`certiqs_key.solvers.frank_wolfe.verified`).
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np

from certiqs_key.foundations.dyadic import float_down
from certiqs_key.meat_core.errors import GradientHypothesisError, SupportError
from certiqs_key.meat_core.objective.joint import DroppedSet, JointMaps, JointSector
from certiqs_key.meat_core.objective.joint_gradient import JointObjectiveGradient
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix
from certiqs_key.meat_core.reasons import AssuranceReason
from certiqs_key.solvers.frank_wolfe.acceptance_iterate import (
    AcceptanceIterate,
    AcceptanceVertex,
    acceptance_vertex,
)
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.verified import (
    FeasibleSideBound,
    GroupSolve,
    verified_feasible_side,
)
from certiqs_key.solvers.oracles.acceptance import (
    AcceptanceOracle,
    ExactAcceptanceOracle,
)
from certiqs_key.solvers.oracles.joint_rows import PrebuiltRows
from certiqs_key.solvers.oracles.protocol import LinearOracle, OracleFailure

if TYPE_CHECKING:
    from certiqs_key.solvers.frank_wolfe.joint_driver import (
        JointIterateGate,
        StageTimings,
    )
    from certiqs_key.solvers.problem import PreparedProblem


@dataclass(frozen=True)
class CandidateAssessment:
    """The consumed point and its original first-order evidence (not success)."""

    point: Mapping[JointSector, Matrix]
    q_iterate: AcceptanceIterate
    gate: JointIterateGate
    gap: float
    gradient: JointObjectiveGradient | None
    vertex: Mapping[JointSector, Matrix] | None
    vertex_q: AcceptanceVertex | None
    oracle_diagnostics: tuple[Mapping[str, Any], ...]
    #: The unsolved oracle failure met at this assessment, where its caller
    #: opted in (``bound_unsolved``); ``None`` on every assessment whose
    #: oracle returned. It withdraws nothing (req:first-order-withdrawal): the
    #: bracket was formed with the multipliers the solves left.
    oracle_failure: OracleFailure | None = field(default=None, compare=False)
    #: ``b^F_t`` exactly, with its record (req:verified-feasible-side), where
    #: a bracket was formed; the gate carries it rounded toward ``-inf``.
    feasible_side: FeasibleSideBound | None = field(default=None, compare=False)
    #: Each group's subproblem and dual, the multipliers the certified
    #: evaluation reads (``req:certified-evaluation`` (v)(c)); ``None`` where
    #: no oracle was called.
    solves: Mapping[str, GroupSolve] | None = field(default=None, compare=False)

    @property
    def contributes(self) -> bool:
        """Whether all original hypotheses held at this point."""
        return self.gate.contributes

    @property
    def objective(self) -> float:
        """The unmodified original objective at the consumed point."""
        return self.gate.objective

    @property
    def bracket(self) -> float | None:
        """The original raw bracket, absent when any hypothesis failed."""
        return self.gate.linearization if self.contributes else None


def assess_first_order(
    maps: JointMaps,
    oracle: LinearOracle,
    acceptance: AcceptanceOracle,
    point: Mapping[JointSector, Matrix],
    q_iterate: AcceptanceIterate,
    alpha: float,
    settings: FrankWolfeOptions,
    chosen: DroppedSet,
    rows: Mapping[str, PrebuiltRows] | None,
    assignment: Mapping[str, str],
    spectral: LinearOracle | None,
    iteration: int,
    timings: StageTimings,
    diagnostics: list[Mapping[str, Any]],
    value: float,
    skip_key_inert: bool = True,
    *,
    bound_unsolved: bool = False,
) -> CandidateAssessment:
    """Apply thm:firstorder at an already formed original-objective point.

    This internal entry consumes FW's cached original value; public assessment
    below always evaluates that value afresh. Retaining FW's evaluation order
    keeps explicit replay identical, including its arithmetic qualifications.

    THE BRACKET (thm:firstorder (iv); req:verified-feasible-side). Where the
    iterate contributes, the bracket is ``value + fl_down(b^F_t) - <G, J_t> +
    <g, v_t - q_t>``: the acceptance side the exact minimisation
    (``acceptance_vertex``), the feasible side the bound of
    ``lem:feasible-side-dual`` verified exactly from the backends' duals and
    rounded toward ``-inf``. The oracle's returned point enters only the
    search's gap and the diagnostics ``oracle_pairing`` and ``dual_gap``; its
    status only the diagnostic ``oracle_status``. Neither withdraws the
    iterate (req:first-order-withdrawal), whose reasons are a failed gradient
    hypothesis, an applied perturbation and a point not established in
    ``AcceptSet x Feas^J(epsilon)``.

    ``bound_unsolved`` (off by default, so the FW loop raises as before; the
    reference companion and a portfolio checkpoint pass it): an
    :class:`OracleFailure` whose backend status is no infeasibility verdict
    (:attr:`OracleFailure.unsolved`) is not raised.
    The bracket is formed with the multipliers the solves left -- each solved
    group's dual, the failing group's where its failure carries one, zero
    elsewhere (req:verified-feasible-side (ii)) -- and the failure is kept on
    the assessment, which the caller reads to end its search there. An
    infeasibility verdict, and every failure without a status, still raises.
    """
    from certiqs_key.solvers.frank_wolfe import joint_driver as driver

    JointIterateGate = driver.JointIterateGate
    joint_gradient = driver.joint_gradient
    _oracle_vertex = driver._oracle_vertex
    _status_of = driver._status_of
    _check_point = driver._check_point
    parametrization = maps.parametrization
    q = q_iterate.view
    calls_start = len(diagnostics)
    started = time.perf_counter()
    try:
        gradient = joint_gradient(
            maps,
            q,
            point,
            alpha,
            dropped=chosen,
            skip_key_inert=skip_key_inert,
            perturbation=settings.gradient_perturbation,
        )
    except GradientHypothesisError as failure:
        timings.record("gradient", time.perf_counter() - started)
        measured = _check_point(
            parametrization,
            point,
            settings,
            f"iteration {iteration}",
            residuals_fatal=False,
        )
        gate = JointIterateGate(
            iteration=iteration,
            objective=value,
            linearization=math.nan,
            oracle_optimal=False,
            min_block_eigenvalue=measured.smallest,
            coupling_residual=measured.worst,
            withdrawal=failure.reason,
            constraint_row_residual=measured.rows,
            acceptance_iterate_exact=q_iterate.on_island,
            min_block_eigenvalue_at=measured.smallest_at,
            coupling_residual_at=measured.worst_at,
        )
        return CandidateAssessment(
            dict(point),
            q_iterate,
            gate,
            math.inf,
            None,
            None,
            None,
            tuple(diagnostics[calls_start:]),
        )
    timings.record("gradient", time.perf_counter() - started)

    started = time.perf_counter()
    calls_before = len(diagnostics)
    solves: dict[str, GroupSolve] = {}
    unsolved: OracleFailure | None = None
    vertex: dict[JointSector, Matrix] | None = None
    optimal = False
    try:
        vertex, optimal = _oracle_vertex(
            maps,
            oracle,
            gradient.blocks,
            diagnostics,
            rows,
            assignment=assignment,
            spectral=spectral,
            iteration=iteration,
            solves=solves,
        )
    except OracleFailure as failure:
        if not (bound_unsolved and failure.unsolved):
            raise
        unsolved = failure
    timings.record("oracle", time.perf_counter() - started)
    oracle_status = (
        str(unsolved.status)
        if unsolved is not None
        else _status_of(diagnostics[calls_before:])
    )
    cost = {
        chat: gradient.q.get(chat, 0.0) for chat in maps.declaration.acceptance_values
    }
    vertex_q = acceptance_vertex(acceptance, cost)
    acceptance_point = vertex_q.view

    # THE SEARCH'S GAP, from the oracle's vertex exactly as before: it decides
    # the loop's stopping rule, and no bracket reads it.
    gap = math.inf
    oracle_pairing: float | None = None
    if vertex is not None:
        direction_value = 0.0
        oracle_pairing = 0.0
        for pair, block in gradient.blocks.items():
            returned = as_matrix(vertex[pair])
            difference = returned - as_matrix(point[pair])
            direction_value += float(np.real(np.trace(block @ difference)))
            oracle_pairing += float(np.real(np.trace(block @ returned)))
        for chat, slope in gradient.q.items():
            shift = acceptance_point[chat] - q[chat]
            if shift != 0.0:
                direction_value += slope * shift
        gap = -direction_value
    consumed = _check_point(
        parametrization,
        point,
        settings,
        f"iteration {iteration}",
        residuals_fatal=False,
    )
    # MEMBERSHIP IN AcceptSet x Feas^J(epsilon), req:iterate-checks: per-
    # block positivity at exactly 0, the coupling at iterate_coupling and
    # the declared rows at constraint_rows on the consumed point, and the
    # acceptance factor on the exact island. NOTHING IS CHECKED ON THE
    # ORACLE'S RETURN, and neither it nor its status withdraws the iterate
    # (req:first-order-withdrawal). A failure withdraws this iterate's
    # bracket; the run goes on.
    feasible = (
        consumed.smallest >= 0.0
        and consumed.relaxed_member(settings)
        and q_iterate.on_island
    )
    withdrawal = (
        str(AssuranceReason.GRADIENT_PERTURBATION_APPLIED)
        if settings.gradient_perturbation != 0.0
        else None
        if feasible
        else str(AssuranceReason.ITERATE_NOT_FEASIBLE)
    )
    linearization = math.nan
    side: FeasibleSideBound | None = None
    record: dict[str, Any] = {}
    if withdrawal is None:
        started = time.perf_counter()
        side = verified_feasible_side(parametrization, gradient.blocks, solves)
        timings.record("feasible_side", time.perf_counter() - started)
        # thm:firstorder (iv): b^F_t in place of <G, S_t>, the pairing with
        # the point kept, rounded toward -inf where it enters the binary64
        # sum (req:verified-feasible-side (v)).
        bound = float_down(side.bound)
        direction = bound
        for pair, block in gradient.blocks.items():
            direction -= float(np.real(np.trace(block @ as_matrix(point[pair]))))
        for chat, slope in gradient.q.items():
            shift = acceptance_point[chat] - q[chat]
            if shift != 0.0:
                direction += slope * shift
        linearization = value + direction
        record = {
            "feasible_side_bound": bound,
            "frame_deduction": float(side.frame_deduction),
            "row_multiplier_norm": float(side.row_multiplier_norm),
            "oracle_pairing": oracle_pairing,
            "dual_gap": (
                None
                if oracle_pairing is None
                else float(Fraction(oracle_pairing) - side.bound)
            ),
            "feasible_side_multipliers": dict(side.multipliers),
        }
    gate = JointIterateGate(
        iteration=iteration,
        objective=value,
        linearization=linearization,
        oracle_optimal=optimal,
        min_block_eigenvalue=consumed.smallest,
        coupling_residual=consumed.worst,
        constraint_row_residual=consumed.rows,
        acceptance_iterate_exact=q_iterate.on_island,
        oracle_status=oracle_status,
        min_block_eigenvalue_at=consumed.smallest_at,
        coupling_residual_at=consumed.worst_at,
        withdrawal=withdrawal,
        **record,
    )
    return CandidateAssessment(
        dict(point),
        q_iterate,
        gate,
        gap,
        gradient,
        vertex,
        vertex_q,
        tuple(diagnostics[calls_start:]),
        oracle_failure=unsolved,
        feasible_side=side,
        solves=solves,
    )


def assess_candidate(
    problem: PreparedProblem,
    point: Mapping[JointSector, Matrix],
    q_exact: Mapping[str, Fraction] | None = None,
    *,
    iteration: int = 1,
    timings: StageTimings | None = None,
    bound_unsolved: bool = False,
) -> CandidateAssessment:
    """Recompute original objective/gradient and every gate at a supplied point.

    Exact external q is admitted by the original geometry, never on a search
    method's assertion. A singleton keeps its declared point even though it
    has no box partial-minimum rule. ``bound_unsolved`` is
    :func:`assess_first_order`'s: an unsolved oracle status is bounded with
    the multipliers the solves left (``oracle_failure`` set) instead of
    raising.
    """
    from certiqs_key.solvers.frank_wolfe import joint_driver as driver
    from certiqs_key.solvers.frank_wolfe.q_rule import q_rule_for

    driver._check_point(
        problem.maps.parametrization,
        point,
        problem.settings,
        "assessment point",
        residuals_fatal=False,
    )
    for pair, block in point.items():
        defect = driver.hermiticity_defect(block)
        if defect is not None:
            raise SupportError(f"assessment point: block {pair} is {defect}")
    q_iterate = AcceptanceIterate.start(problem.acceptance)
    q_rule = q_rule_for(problem.acceptance, problem.maps, problem.alpha)
    if q_exact is not None:
        exact = dict(q_exact)
        valid = set(exact) == set(q_iterate.view) and all(
            isinstance(x, Fraction) for x in exact.values()
        )
        if valid and isinstance(problem.acceptance, ExactAcceptanceOracle):
            valid = problem.acceptance.exact_contains(exact)
        elif valid:
            valid = exact == {
                key: Fraction(value) for key, value in q_iterate.view.items()
            }
        q_iterate = AcceptanceIterate(
            {key: float(value) for key, value in exact.items()}, exact, bool(valid)
        )
        if not valid:
            measured = driver._check_point(
                problem.maps.parametrization,
                point,
                problem.settings,
                "assessment point",
                residuals_fatal=False,
            )
            gate = driver.JointIterateGate(
                iteration=iteration,
                objective=math.nan,
                linearization=math.nan,
                oracle_optimal=False,
                min_block_eigenvalue=measured.smallest,
                coupling_residual=measured.worst,
                withdrawal=str(AssuranceReason.ITERATE_NOT_FEASIBLE),
                constraint_row_residual=measured.rows,
                min_block_eigenvalue_at=measured.smallest_at,
                coupling_residual_at=measured.worst_at,
            )
            return CandidateAssessment(
                dict(point), q_iterate, gate, math.inf, None, None, None, ()
            )
    elif q_rule is not None:
        exact, _ = q_rule.exact_at(
            problem.maps,
            point,
            dropped=problem.dropped,
            skip_key_inert=problem.skip_key_inert,
        )
        q_iterate = q_iterate.at(exact)
    value = driver.joint_objective_value(
        problem.maps,
        q_iterate.view,
        point,
        problem.alpha,
        dropped=problem.dropped,
        skip_key_inert=problem.skip_key_inert,
    )
    return assess_first_order(
        problem.maps,
        problem.oracle,
        problem.acceptance,
        point,
        q_iterate,
        problem.alpha,
        problem.settings,
        problem.dropped,
        problem.rows,
        problem.assignment,
        problem.spectral,
        iteration,
        timings if timings is not None else driver.StageTimings(),
        [],
        value,
        problem.skip_key_inert,
        bound_unsolved=bound_unsolved,
    )
