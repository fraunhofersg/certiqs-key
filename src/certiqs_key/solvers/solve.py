"""Bounded candidate coordination with one original first-order assessor.

Policy candidate-portfolio-v5 allocates one global wall budget, keeps a cold
anchor independent of a warm seed, and retains the maximum qualifying bracket.
An entropy stage its own allocation guard would refuse is skipped before any
share is allocated (``_entropy_resource_skip``).
Search termination is diagnostic; only the original gate grants a bracket.
Under it ``max_iterations`` caps the Frank-Wolfe stages only; the factor,
entropy-polish and corrective stages run to their own convergence or their
deadline share, a corrective stage probes again while the assessed
bracket improves, and time the schedule leaves goes back to a search its own
deadline cut while it progressed.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping
from dataclasses import asdict, replace
from fractions import Fraction
from typing import Any

import numpy as np

from certiqs_key.meat_core.errors import SupportError
from certiqs_key.meat_core.objective.joint import JointSector
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.solvers.assessment import CandidateAssessment, assess_candidate
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    IterateObserver,
    JointFrankWolfeResult,
    StageTimings,
    _check_point,
    joint_run_metadata,
    run_joint_frank_wolfe,
)
from certiqs_key.solvers.frank_wolfe.reference import ReferenceCandidates
from certiqs_key.solvers.oracles.protocol import OracleFailure
from certiqs_key.solvers.problem import PreparedProblem
from certiqs_key.solvers.types import SearchRequest

POLICY_ID = "candidate-portfolio-v5"
DEFAULT_PORTFOLIO_SECONDS = 120.0
#: Under auto, the largest share of a corrective stage one probe may take.
#: A quarter leaves room for three more probes after one that runs to its
#: slice, while each slice is long enough for many corrective iterations
#: (the stage itself is 15 or 10 % of the solve's budget, renormalised
#: over the supported stages).
CORRECTIVE_PROBE_SLICE = 0.25
#: Under auto, the progress that earns a corrective series another probe:
#: the probe raised the series' own best assessed bracket by MORE than this
#: fraction of the bracket left open before it (the best estimate minus that
#: series best). Probes that close less than a hundredth of the open bracket
#: would need hundreds more to matter; the time goes to the next stage
#: instead.
CORRECTIVE_PROGRESS_FRACTION = 0.01
#: Under auto, the global relative bracket ``(h_low - h_lb) / |h_low|`` (the
#: best estimate against the best bracket) at or below which no cold
#: corrective series is started: the warm work has already closed the bracket
#: that far, and a cold series could only add what it cannot improve on.
#: A skipped cold stage is recorded with this value and the bracket it read.
CORRECTIVE_COLD_TAU = 5e-4
#: Under auto, the least time, as a fraction of the solve's budget, worth
#: resuming a stage for (_resumptions): below it a resumed stage would do
#: little more than its first assessment.
RESUME_MIN_FRACTION = 0.05
#: The relative bracket ``(h_low - h_lb) / |h_low|`` (:func:`_open_relative`,
#: the solve's own best estimate against its own best bound) at or below which
#: a search whose last stage stopped on its own no-progress rule is said to
#: have CONVERGED: its termination reads ``relative_gap_met`` instead of
#: ``stagnated``. A LABEL ONLY. The gap target (``gap_target``, the absolute
#: ``meat_core.thresholds.OPTIMIZER_GAP``) still decides when the search
#: stops, and the classification is made after the last stage, so no search
#: stops earlier or runs a different schedule and no bound moves. Why: the
#: absolute target 1e-10 is about 1e-9 of an entropy near 0.1 but 1e-4 of
#: one near 1e-6, where a key round has probability of order 1e-6 per round;
#: there, searches that had closed their bracket to 1e-4 of h_low read
#: stagnated, as if they had failed to converge (BBM92 with an SPDC source at
#: 0.05 pairs per round and dark counts of 1e-6, at cutoff 1). The
#: value is the alpha search's floor below which no bracket is too wide to
#: rank by (``certiqs_key.runs.alpha_search.WIDE_RELATIVE_GAP``): a bracket
#: that closed can hide at most about 0.1 % of ``n h``.
CONVERGED_RELATIVE_GAP = 1e-3
RESUME_RULE = (
    "once the schedule is done, time left (at least "
    f"{RESUME_MIN_FRACTION:g} of the budget) goes to one more run, from the "
    "best assessed point, of each search its own deadline cut while it was "
    "raising the assessed bracket: the factor search (also for the entropy "
    "stage's polish) and a corrective series whose last probe progressed and "
    "stopped at its stage deadline, by their schedule shares; a Frank-Wolfe "
    "stage is never "
    "resumed, its work being capped by max_iterations"
)


def evaluation_wall_budget(request: SearchRequest) -> float | None:
    """Return the wall budget of one evaluation of the run under ``request``.

    The request's ``budget_seconds`` where it sets one; otherwise, under every
    method the portfolio coordinates (all but the explicit ``fw`` and
    ``pairwise``), the budget it then spends, :data:`DEFAULT_PORTFOLIO_SECONDS`;
    ``None`` for an explicit ``fw`` or ``pairwise`` search with no budget,
    which its iteration cap alone bounds. The shares of
    ``frank-wolfe/req:bracket-on-reference`` (i) (the polish) and
    ``meat-core/req:unreachable-acceptance-set`` (i) (the statistics check's
    solve) are taken of it.
    """
    if request.budget_seconds is not None:
        return request.budget_seconds
    if request.method in ("fw", "pairwise"):
        return None
    return DEFAULT_PORTFOLIO_SECONDS


def _entropy_resource_skip(problem: PreparedProblem) -> dict[str, Any] | None:
    """Return the skip record of an entropy stage its own guard would refuse.

    RESOURCE INFEASIBILITY IS LEARNED BEFORE STAGE TIME IS ALLOCATED. The
    entropy initializer refuses, before it builds anything, a cone whose
    allocation plan exceeds its assembly budget (``search.entropy``,
    ``_preflight_memory``); under auto that refusal used to come only after
    the factor stage had been cut to its 25 % share, half the budget
    reserved for a stage certain to fail. The same plan is now read first,
    and a refused stage is skipped so that the existing renormalisation
    hands its share to the stages that can run. The plan reads block
    dimensions only (a resource predicate, never a protocol name), its
    time is spent inside the solve's budget, and a stage the plan admits
    runs exactly as before. Effort only: every candidate is still judged
    by the one assessor.
    """
    from certiqs_key.solvers.search.common import EntropySettings
    from certiqs_key.solvers.search.entropy import (
        INITIALIZER_FAILURES,
        entropy_preflight,
    )

    settings = EntropySettings()
    started = time.perf_counter()
    try:
        entropy_preflight(problem, settings)
    except MemoryError as refusal:
        return {
            "reason": "resource_infeasible",
            "detail": str(refusal),
            "assembly_limit_bytes": settings.max_assembly_bytes,
            "preflight_seconds": time.perf_counter() - started,
        }
    except INITIALIZER_FAILURES:
        # Any other refusal is the stage's to meet: it runs, and ends as the
        # numerical failure it always was, instead of ending the solve here.
        return None
    return None


def _same_start(
    first: Mapping[JointSector, Matrix], second: Mapping[JointSector, Matrix]
) -> bool:
    """Return whether two search starts are the same point, block for block.

    A corrective series is deterministic in its start, so a cold series that
    starts where the warm one did repeats it bit for bit (on a
    declaration with rows, factor and entropy being unsupported, the warm
    series starts at the anchor, and the licensed route at cutoff 1 ran the
    same probes twice).
    """
    return first.keys() == second.keys() and all(
        np.array_equal(first[pair], second[pair]) for pair in first
    )


def _open_relative(
    best: CandidateAssessment | None, estimate: CandidateAssessment | None
) -> float | None:
    """Return the solve's relative bracket, best estimate against best bound.

    Both are this solve's own assessments, on the declaration it searches;
    the reference companion's bound, formed after the search, is not read,
    so no snap offset enters CORRECTIVE_COLD_TAU's test.
    """
    if best is None or estimate is None or estimate.objective == 0:
        return None
    relative = max(0.0, estimate.objective - best.gate.linearization) / abs(
        estimate.objective
    )
    # An infinite estimate gives NaN: no relative bracket, recorded as null
    # (JSON has no NaN). Every caller reads None as it read NaN, as unmet.
    return relative if math.isfinite(relative) else None


def classify_termination(termination: str, relative_gap: float | None) -> str:
    """Return the termination a search records, its relative bracket read.

    ``stagnated`` (the last stage stopped on its own no-progress rule) becomes
    ``relative_gap_met`` where ``relative_gap``, :func:`_open_relative`'s
    ``(h_low - h_lb) / |h_low|``, is at most :data:`CONVERGED_RELATIVE_GAP`;
    every other termination, and a stagnated search with no bracket or a
    wider one, is returned as it is. A label: it is read after the search
    and decides nothing.
    """
    if (
        termination == "stagnated"
        and relative_gap is not None
        and relative_gap <= CONVERGED_RELATIVE_GAP
    ):
        return "relative_gap_met"
    return termination


def _resumptions(
    attempts: list[dict[str, Any]], total: float, left: float
) -> list[tuple[str, str, float]]:
    """Return the stages to run again with the time the schedule left.

    RESUMING A CUT STAGE (the same decision as the caps: under auto the
    factor, entropy-polish and corrective searches run to their own
    convergence or their deadline). A stage's share is fixed when it starts,
    before the later stages show whether they will use theirs: on the BBM92
    encoded route at cutoff 4 the factor search was still raising the
    bracket when its 150 s share ended (h_lb 0.0143 against h_low 0.0242),
    the entropy initializer failed in 0.6 s and both corrective stages
    stopped within seconds, so the solve ended after 174 of its 600 s. So,
    once the schedule is done and at least RESUME_MIN_FRACTION of the budget
    is left, each search its own deadline cut while it progressed runs once
    more from the best assessed point: the factor search where the factor
    stage, or the entropy stage's polish (a factor search), ended at its
    deadline with a higher bracket than it started with, and the corrective
    search where a corrective series stopped at its stage deadline in a probe
    that was still progressing (``progressed`` on that probe's attempt; a
    series whose last probes were flat when the time ran out is not cut but
    done). They
    share the time by their schedule shares (the larger where both factor
    and entropy were cut). A Frank-Wolfe stage is never resumed: under auto
    its work is what max_iterations caps.
    """
    if left < RESUME_MIN_FRACTION * total:
        return []
    shares: dict[str, float] = {}
    for attempt in attempts:
        method, share = attempt.get("method"), attempt.get("budget_share")
        if share is None or attempt.get("resumed"):
            continue
        if method in ("factor", "entropy"):
            before = attempt.get("assessed_bound_before")
            after = attempt.get("assessed_bound_after")
            if attempt.get("termination") == "budget_exhausted" and (
                after is not None and (before is None or after > before)
            ):
                shares["factor"] = max(shares.get("factor", 0.0), share)
        elif (
            method == "corrective"
            and attempt.get("stop_reason") == "stage_deadline"
            and attempt.get("progressed") is True
        ):
            shares["corrective"] = max(shares.get("corrective", 0.0), share)
    return [
        (method, "best", shares[method])
        for method in ("factor", "corrective")
        if method in shares
    ]


class _AssessmentFailure(Exception):
    """Keep mandatory assessor refusals outside a method's numerical catch."""

    def __init__(self, failure: Exception) -> None:
        self.failure = failure


#: The exceptions a search raises where the assessment of a point fails
#: numerically: a point off its support face or outside the cone
#: (``SupportError``), a decomposition that did not converge, a non-finite or
#: malformed number. A programming error (``TypeError``, ``KeyError``, ...)
#: is none of them.
NUMERICAL_FAILURES: tuple[type[Exception], ...] = (
    SupportError,
    np.linalg.LinAlgError,
    ValueError,
)
_MARK = "_certiqs_raised_assessing_a_point"


def _mark_numerical(failure: BaseException) -> None:
    """Mark ``failure`` as raised by the search's assessment of a point.

    Only an attribute: the exception keeps its type, its message and its
    cause chain, so a caller that does not ask sees what it always saw.
    """
    if isinstance(failure, NUMERICAL_FAILURES):
        failure.__dict__.setdefault(_MARK, True)


def raised_assessing_a_point(error: BaseException) -> bool:
    """Return whether the search raised ``error`` assessing a point numerically.

    Marked (:data:`NUMERICAL_FAILURES` only) where it comes out of: a
    portfolio checkpoint's assessment of a point; the whole explicit ``fw``
    or ``pairwise`` search, and ``auto``'s Frank-Wolfe stage, whatever step
    of the driver raised it (a point it checks, a decomposition, a backend
    error not converted to an oracle failure); and the check of the
    returned point. A request or preparation error, raised before the
    search, is not marked, and neither is a broken internal invariant of a
    driver, which is no ``NUMERICAL_FAILURES`` (the pairwise rule's exact
    active set raises ``RuntimeError``).
    The statistics check asks, so that a numerical failure of its search is
    recorded as its solve not completed
    (``meat-core/req:unreachable-acceptance-set`` (ii);
    :func:`~certiqs_key.solvers.frank_wolfe.minimal_divergence.bound_minimal_divergence`).
    """
    return bool(getattr(error, _MARK, False))


class _UnsolvedAssessment(Exception):
    """End a search stage at a checkpoint whose oracle was left unsolved.

    Not a ``MeatError``, so a search method's numerical catch cannot turn it
    into its own termination; the coordinator catches it, ends the stage and
    keeps every bracket already certified.
    """

    def __init__(self, assessment: CandidateAssessment) -> None:
        self.assessment = assessment


def _assessment_payload(
    assessment: CandidateAssessment | None,
) -> dict[str, Any] | None:
    if assessment is None:
        return None
    return {
        "gate": asdict(assessment.gate),
        "gap": assessment.gap,
        "q": dict(assessment.q_iterate.view),
        "q_exact": None
        if assessment.q_iterate.exact is None
        else {key: str(value) for key, value in assessment.q_iterate.exact.items()},
        "point": [
            {
                "sector": list(pair),
                "real": block.real.tolist(),
                "imag": block.imag.tolist(),
            }
            for pair, block in assessment.point.items()
        ],
    }


def _refuse_negative(assessment: CandidateAssessment) -> None:
    if assessment.objective < 0:
        from certiqs_key.meat_core.reasons import RefusalReason
        from certiqs_key.solvers.frank_wolfe.general_keyrate import (
            NegativeObjectiveError,
        )

        raise NegativeObjectiveError(
            "the original assessed objective is negative; a prior bound does not "
            "override req:negative-estimate-refused",
            reason=RefusalReason.NEGATIVE_OBJECTIVE,
            value=assessment.objective,
            point={
                str(pair): block.tolist() for pair, block in assessment.point.items()
            },
        )


def solve_prepared(
    problem: PreparedProblem,
    request: SearchRequest,
    *,
    observer: IterateObserver | None = None,
    refuse_negative: bool = True,
) -> JointFrankWolfeResult:
    """Run one explicit search or the bounded structural portfolio.

    Deadline checks are cooperative. A backend call already running cannot be
    interrupted safely in-process; its overrun is recorded. Benchmarks enforce
    their hard process deadline externally. No failed security oracle is rerouted.

    ``refuse_negative`` (default true) is the portfolio's refusal of a
    negative assessed objective at every point it assesses
    (``_refuse_negative``, ``frank-wolfe/req:negative-estimate-refused``),
    which the key-rate solve keeps: its value is bounded away from 0 where a
    key exists, and its estimate is the least objective the checkpoints
    assessed, so a negative point would make it negative. The statistics check
    of ``meat-core/req:unreachable-acceptance-set`` sets it false: its
    program's value is exactly 0 on a reachable table, so the sign of an
    assessed objective is decided by rounding, and item (ii) makes a negative
    estimate a reason no bound was formed that refuses nothing. With it false
    a negative point is assessed and recorded like any other, the search
    goes on to its own stop, and the returned estimate (the least assessed
    objective, negative where any was) is the caller's to decide on. Every
    method then behaves as the explicit ``fw`` and ``pairwise`` searches
    always have, which never refuse here.
    """
    from certiqs_key.solvers.frank_wolfe.joint_options import joint_choices

    oracle_choice, step_rule, warm = joint_choices(problem.settings)
    expected_step = "pairwise" if request.method == "pairwise" else "vanilla"
    mismatches = []
    if problem.search_method is not None and problem.search_method != request.method:
        mismatches.append("method")
    for name, actual, expected in (
        ("oracle", oracle_choice, request.oracle),
        ("step_rule", step_rule, expected_step),
        ("max_iterations", problem.settings.max_iterations, request.max_iterations),
        ("gap_target", problem.settings.gap_tolerance, request.gap_target),
        ("warm_start", warm, request.warm_start),
    ):
        if actual != expected:
            mismatches.append(name)
    if mismatches:
        raise ValueError(
            "prepared settings differ from SearchRequest: "
            + ", ".join(mismatches)
            + "; prepare_problem(request=request) resolves them together"
        )
    started = time.perf_counter()

    def refuse(assessment: CandidateAssessment) -> None:
        if refuse_negative:
            _refuse_negative(assessment)

    assessment_history: list[dict[str, Any]] = []
    # THE POINTS A REFERENCE COMPANION IS EVALUATED AT
    # (frank-wolfe/req:bracket-on-reference (i), its first set): every
    # assessment the search forms passes here, and five are kept with the
    # order the search consumed them in.
    candidates = ReferenceCandidates()

    def record_assessment(assessment: CandidateAssessment) -> None:
        candidates.observe(assessment)
        entry: dict[str, Any] = {
            "elapsed_seconds": time.perf_counter() - started,
            "objective": assessment.objective,
            "raw_bracket": assessment.gate.linearization,
            "raw_gap": assessment.gap,
            "contributes": assessment.contributes,
            "withdrawal": assessment.gate.withdrawal,
        }
        if assessment.oracle_failure is not None:
            # Only a portfolio checkpoint sets it (bound_unsolved below), so
            # an explicit fw/pairwise history is the one it always was.
            entry["oracle_status"] = assessment.gate.oracle_status
            entry["oracle_failure"] = str(assessment.oracle_failure)
        assessment_history.append(entry)

    if request.method in ("fw", "pairwise"):
        deadline = (
            None if request.budget_seconds is None else started + request.budget_seconds
        )
        try:
            run = run_joint_frank_wolfe(
                problem.maps,
                problem.oracle,
                problem.acceptance,
                problem.initial,
                problem.alpha,
                problem.settings,
                dropped=problem.dropped,
                anchor=problem.anchor
                if request.warm_start is not None
                else problem.initial,
                observer=observer,
                deadline=deadline,
                assessment_observer=record_assessment,
            )
        except NUMERICAL_FAILURES as failure:
            _mark_numerical(failure)
            raise
        termination = (
            "target_met"
            if run.status == "converged"
            else "budget_exhausted"
            if run.status in ("iteration-limit", "budget_exhausted")
            else "numerical_failure"
        )
        return replace(
            run,
            reference_candidates=candidates.points(),
            search_report={
                "method": request.method,
                "policy": "explicit-v1",
                "termination": termination,
                "budget_seconds": request.budget_seconds,
                "gap_target": request.gap_target,
                "max_iterations": request.max_iterations,
                "assessment_history": assessment_history,
                "iteration_unit": "fw_iteration",
                "preparation_seconds": problem.preparation_seconds,
                "solver_seconds": time.perf_counter() - started,
                "attempts": [
                    {
                        "method": request.method,
                        "termination": termination,
                        "iterations": run.iterations,
                    }
                ],
                "best_contributing_candidate": _assessment_payload(run.best_assessment),
            },
        )

    # Imports are lazy: an explicit historical FW run does not initialize any
    # candidate-specific backend or arithmetic.
    from certiqs_key.solvers.search.common import (
        SUPPORT_FALLBACK_BLEND,
        CorrectiveSettings,
        EntropySettings,
        FactorSettings,
        capability_reason,
    )
    from certiqs_key.solvers.search.corrective import search_corrective
    from certiqs_key.solvers.search.entropy import search_entropy
    from certiqs_key.solvers.search.factor import search_factor

    total = request.budget_seconds or DEFAULT_PORTFOLIO_SECONDS
    deadline = started + total
    timings = StageTimings()
    assessments: list[CandidateAssessment] = []
    best: CandidateAssessment | None = None
    estimate: CandidateAssessment | None = None
    attempts: list[dict[str, Any]] = []
    termination = "budget_exhausted"

    def checkpoint(
        point: Mapping[JointSector, Matrix],
        exact: Mapping[str, Fraction] | None,
        *,
        final: bool = False,
    ) -> bool:
        nonlocal best, estimate
        if not final and assessments and time.perf_counter() >= deadline:
            return True
        before = time.perf_counter()
        # AN UNSOLVED ORACLE ENDS THE STAGE, ONCE A BRACKET IS FORMED. A
        # backend status that is no infeasibility verdict withdraws nothing
        # (req:first-order-withdrawal): the bracket is formed with the
        # multipliers the solves left (req:verified-feasible-side (ii)), and
        # the failure, kept on the assessment, ends the search stage that met
        # it. Here and not in the QICS adapter: the adapter's raise is what the
        # FW loop and the reference companion rely on, and an explicit
        # fw/pairwise run is unchanged by it. Nothing is re-routed to another
        # backend (spec/architecture.md 7.3). With no bracket formed yet the
        # failure stops the solve; an infeasibility verdict
        # (def:admissible-declaration (vii)) always does.
        try:
            assessment = assess_candidate(
                problem,
                point,
                exact,
                iteration=len(assessments) + 1,
                timings=timings,
                bound_unsolved=best is not None,
            )
        except NUMERICAL_FAILURES as failure:
            _mark_numerical(failure)
            raise
        timings.record("assessment", time.perf_counter() - before)
        refuse(assessment)
        record_assessment(assessment)
        assessments.append(assessment)
        if estimate is None or assessment.objective < estimate.objective:
            estimate = assessment
        if assessment.contributes and (
            best is None or assessment.gate.linearization > best.gate.linearization
        ):
            best = assessment
        if observer is not None:
            observer(len(assessments), assessment.gap)
        return target_met() or time.perf_counter() >= deadline

    def target_met() -> bool:
        return best is not None and abs(best.gap) <= request.gap_target

    # This also reassesses a supplied warm seed at the new target order.
    checkpoint(problem.initial, None, final=True)
    if request.method == "auto" and any(
        not np.array_equal(problem.initial[pair], block)
        for pair, block in problem.anchor.items()
    ):
        # An already-good warm/supplied point must not eliminate the independent
        # cold assessment. Keep both qualifying brackets under the same target.
        checkpoint(problem.anchor, None, final=True)
    auto = request.method == "auto"
    if auto:
        schedule = [
            ("factor", "cold", 0.25),
            ("entropy", "cold", 0.50),
            ("corrective", "best", 0.15),
            ("corrective", "cold", 0.10),
        ]
        if capability_reason(problem, "corrective") is not None:
            schedule[-1] = ("fw", "cold", 0.10)
    else:
        schedule = [(request.method, "initial", 1.0)]

    reasons = {
        method: None if method == "fw" else capability_reason(problem, method)
        for method, _, _ in schedule
    }
    allocations: list[dict[str, Any]] = []
    # Stages skipped before they start, by index, with the record of why.
    skipped: dict[int, dict[str, Any]] = {}
    if auto:
        for index, (method, _, _) in enumerate(schedule):
            if method == "entropy" and reasons[method] is None:
                refusal = _entropy_resource_skip(problem)
                if refusal is not None:
                    skipped[index] = refusal
    # The stages run, in order: the schedule, then under auto at most one
    # resumption of each stage its own deadline cut (_resumptions).
    plan = list(schedule)
    stage = -1
    while True:
        stage += 1
        if stage == len(plan):
            if not auto or len(plan) > len(schedule) or target_met():
                break
            plan.extend(
                _resumptions(attempts, total, deadline - time.perf_counter())
            )
            if stage == len(plan):
                break
        method, source, share = plan[stage]
        resumed = stage >= len(schedule)
        reason = reasons[method]
        if reason is not None:
            attempts.append(
                {"method": method, "termination": "unsupported", "reason": reason}
            )
            termination = "unsupported"
            continue
        if stage in skipped:
            attempts.append(
                {
                    "stage": stage,
                    "method": method,
                    "source": source,
                    "termination": "skipped",
                    **skipped[stage],
                }
            )
            continue
        if target_met():
            termination = "target_met"
            break
        if time.perf_counter() >= deadline:
            termination = "budget_exhausted"
            break
        if auto and method == "corrective" and source == "cold" and not resumed:
            # NO COLD SERIES ONCE THE BRACKET IS CLOSED TO CORRECTIVE_COLD_TAU.
            open_relative = _open_relative(best, estimate)
            if open_relative is not None and open_relative <= CORRECTIVE_COLD_TAU:
                attempts.append(
                    {
                        "stage": stage,
                        "method": method,
                        "source": source,
                        "termination": "skipped",
                        "reason": "bracket_closed_to_cold_tau",
                        "tau": CORRECTIVE_COLD_TAU,
                        "relative_bracket": open_relative,
                    }
                )
                continue
        initial = (
            problem.anchor
            if source == "cold"
            else best.point
            if source == "best" and best is not None
            else problem.initial
        )
        if (
            auto
            and method == "corrective"
            and source == "best"
            and not resumed
            and _same_start(initial, problem.anchor)
        ):
            # THE COLD SERIES WOULD REPEAT THIS ONE: its start is
            # the anchor, and so is this one's. It is skipped now, so that its
            # share goes to this series or to its resumption.
            for later in range(stage + 1, len(schedule)):
                if schedule[later][:2] == ("corrective", "cold"):
                    skipped[later] = {
                        "reason": "cold_start_equals_warm_start",
                        "warm_stage": stage,
                    }
        # Reserve one final original assessment; adapt its allowance to measured
        # cost without moving any hypothesis window.
        reserve = max(
            0.01,
            timings.seconds.get("assessment", 0.0)
            / max(1, timings.calls.get("assessment", 0)),
        )
        attempt_start = time.perf_counter()
        remaining_weight = sum(
            weight
            for index, (name, _, weight) in enumerate(plan)
            if index >= stage and reasons[name] is None and index not in skipped
        )
        remaining_seconds = max(0.0, deadline - reserve - attempt_start)
        normalized_share = share / remaining_weight
        attempt_deadline = attempt_start + remaining_seconds * normalized_share
        allocation = {
            "stage": stage,
            "method": method,
            "source": source,
            "budget_share": share,
            "remaining_supported_share": remaining_weight,
            "normalized_remaining_share": normalized_share,
            "start_seconds": attempt_start - started,
            "deadline_seconds": attempt_deadline - started,
            "remaining_seconds": remaining_seconds,
            "allocated_seconds": attempt_deadline - attempt_start,
            "assessment_reserve_seconds": reserve,
            "resumed": resumed,
        }
        allocations.append(allocation)
        if attempt_deadline <= attempt_start:
            termination = "budget_exhausted"
            break
        if method == "fw":
            # The FW stage's own assessments, the best contributing one kept, so
            # that a stage ended by an unsolved oracle loses none of them, and
            # how many there were.
            stage_best: list[CandidateAssessment] = []
            stage_seen: list[int] = [0]

            def observe_fw(
                assessment: CandidateAssessment,
                kept: list[CandidateAssessment] = stage_best,
                seen: list[int] = stage_seen,
            ) -> None:
                record_assessment(assessment)
                seen[0] += 1
                if assessment.contributes and (
                    not kept
                    or assessment.gate.linearization > kept[0].gate.linearization
                ):
                    kept[:] = [assessment]

            try:
                fw = run_joint_frank_wolfe(
                    problem.maps,
                    problem.oracle,
                    problem.acceptance,
                    initial,
                    problem.alpha,
                    problem.settings,
                    dropped=problem.dropped,
                    anchor=problem.anchor,
                    deadline=attempt_deadline,
                    stagnation_limit=2,
                    assessment_observer=observe_fw,
                )
            except NUMERICAL_FAILURES as failure:
                _mark_numerical(failure)
                raise
            except OracleFailure as failure:
                # THE SAME RULE AS AT A CHECKPOINT (bound_unsolved above),
                # in this portfolio-only stage: the explicit driver keeps its
                # raise, so an explicit fw/pairwise run is unchanged, and the
                # coordinator ends the stage here. The driver's raise comes
                # before the failing iterate's bracket is formed; every
                # bracket formed before it, in this stage or earlier, stands. With
                # none, or on an infeasibility verdict or a failure without a
                # status, the solve stops as before -- and the verdict or the
                # failure is tested FIRST, so that no refusal of the stage's
                # own best assessment (a negative objective) can hide it.
                if not failure.unsolved:
                    raise
                if stage_best:
                    refuse(stage_best[0])
                    assessments.append(stage_best[0])
                    if (
                        best is None
                        or stage_best[0].gate.linearization > best.gate.linearization
                    ):
                        best = stage_best[0]
                if best is None:
                    raise
                termination = "target_met" if target_met() else "oracle_failure"
                attempts.append(
                    {
                        **allocation,
                        "termination": termination,
                        "seconds": time.perf_counter() - attempt_start,
                        # The driver's raise names no iterate; the block
                        # says how many of the stage's iterates were
                        # assessed before it.
                        "oracle_failure": {
                            "iterates_assessed": stage_seen[0],
                            "oracle_status": failure.status,
                            "message": str(failure),
                        },
                    }
                )
                continue
            # FW's qualifying brackets are already the same assessor's output.
            if fw.best_assessment is not None:
                refuse(fw.best_assessment)
                assessments.append(fw.best_assessment)
                if (
                    best is None
                    or fw.best_assessment.gate.linearization > best.gate.linearization
                ):
                    best = fw.best_assessment
            checkpoint(fw.choi, None, final=True)
            termination = (
                "target_met"
                if target_met()
                else "stagnated"
                if fw.status == "stagnated"
                else "budget_exhausted"
            )
            attempts.append(
                {
                    **allocation,
                    "termination": termination,
                    "seconds": time.perf_counter() - attempt_start,
                    "iterations": fw.iterations,
                }
            )
            continue
        # WHAT max_iterations CAPS UNDER auto. A Frank-Wolfe stage (above)
        # keeps the request's cap; the factor search, the entropy stage's
        # polish and the corrective search run to their own convergence or
        # their deadline share. A 200-iteration cap stopped the factor stage
        # after 14.5 s of its 150 s share with h_lb -0.0507 where, uncapped, it
        # converged by its own tolerance at 294 iterations with a gap of
        # 9.3e-5. The entropy cone keeps its own iteration default. Every
        # candidate any of them makes is still certified by the one assessor,
        # so this is effort only. An explicit factor, entropy or corrective
        # request keeps max_iterations as its cap.
        settings: FactorSettings | CorrectiveSettings | EntropySettings
        if method == "factor":
            settings = FactorSettings(
                max_iterations=None if auto else request.max_iterations
            )
        elif method == "entropy":
            settings = (
                EntropySettings(polish=FactorSettings(max_iterations=None))
                if auto
                else EntropySettings(
                    max_iterations=min(100, request.max_iterations),
                    polish=FactorSettings(max_iterations=request.max_iterations),
                )
            )
        else:
            settings = CorrectiveSettings(
                max_iterations=None if auto else request.max_iterations
            )

        def guarded_checkpoint(
            point: Mapping[JointSector, Matrix], exact: Mapping[str, Fraction]
        ) -> bool:
            count = len(assessments)
            try:
                stop = checkpoint(point, exact)
            except Exception as failure:
                raise _AssessmentFailure(failure) from failure
            fresh = assessments[count:]
            if fresh and fresh[-1].oracle_failure is not None:
                # The stage ends here: its search would only go on handing the
                # same backend the same kind of cost.
                raise _UnsolvedAssessment(assessments[-1])
            return stop

        # CORRECTIVE PROBES UNDER auto (the same decision as the caps above):
        # a corrective stage runs a SERIES of probes, each an uncapped
        # corrective search, while the series' own assessed bracket improves
        # and the stage has time left. A probe gets at most a slice of the
        # stage (CORRECTIVE_PROBE_SLICE), so that one probe that stalls cannot
        # take the stage from the probes after it; a slice that would leave
        # less than half a slice goes to the probe whole. Only progress in a
        # qualifying original bracket earns another probe -- more than
        # CORRECTIVE_PROGRESS_FRACTION of the bracket left open before it --
        # never a native optimizer objective.
        # THE SERIES IS JUDGED ON ITS OWN PATH: its progress is
        # its best assessed bracket against its best before the probe, and
        # the next probe starts from the series' own best point. A cold
        # series that improves along its own path but cannot beat the warm
        # series' best within one slice was stopped after one slice (the
        # licensed route at cutoff 1 ended at 224 of 600 s); judged against
        # the global best it never could continue. The global best still
        # decides what is reported. A warm series starts from the global
        # best, so that is its baseline; a cold one starts with none. Each
        # probe's attempt says why the series stopped (stop_reason) and
        # whether it progressed. An explicit request runs one search.
        # THE BLEND: every series starts at the default
        # CorrectiveSettings.blend (1e-10) and moves to SUPPORT_FALLBACK_BLEND
        # (1e-6) for its remaining probes only after a probe ends in the
        # H-SUPP^D rank refusal, which ends that probe alone; every bracket
        # assessed before it stays certified. A fixed 1e-6 cost the licensed
        # route at cutoff 1, where 1e-10 never failed, about 360 bits. The
        # blend is not stepped back down: each step down would have to fail
        # again to learn its margin, which the per-probe support_margin now
        # shows without that.
        # A PROBE CUT BY ITS SLICE RESTARTS FROM THE SERIES' BEST, measured
        # (licensed route, cutoff 1). Continuing the cut search
        # with its active set spent the whole
        # 600 s but raised the snapped bound only from 0.0242054 to 0.0242069;
        # restarting from the best point with a fresh active set reached
        # 0.0242162 in 160 s, its stale and folded atoms gone. In that
        # measured probe the series ended with time left because it had
        # converged on the searched declaration (snapped gap 1.7e-6,
        # relative 7e-5); the key it lacked against other runs is the
        # reference companion's offset (4.6e-5 there against 6.4e-6 on an
        # earlier search), which depends on the points the search hands the
        # companion and not on closing the snapped gap further.
        probing = auto and method == "corrective"
        stage_seconds = attempt_deadline - attempt_start
        series_best: CandidateAssessment | None = best if source == "best" else None
        probe = 0
        while True:
            probe_start = time.perf_counter()
            probe_deadline = attempt_deadline
            if probing:
                slice_seconds = CORRECTIVE_PROBE_SLICE * stage_seconds
                if attempt_deadline - probe_start - slice_seconds >= slice_seconds / 2:
                    probe_deadline = probe_start + slice_seconds
            previous_bound = None if best is None else best.gate.linearization
            series_before = (
                None if series_best is None else series_best.gate.linearization
            )
            open_before = (
                None
                if series_before is None or estimate is None
                else max(0.0, estimate.objective - series_before)
            )
            assessed_before = len(assessments)
            # The exception a checkpoint raised, carried out of the stage
            # (_AssessmentFailure) and raised again after the try statement,
            # outside any handler: inside one, Python would set its
            # __context__ to the carrier.
            raised: Exception | None = None
            try:
                if isinstance(settings, FactorSettings):
                    outcome = search_factor(
                        problem,
                        initial,
                        settings=settings,
                        deadline=attempt_deadline,
                        checkpoint=guarded_checkpoint,
                    )
                elif isinstance(settings, EntropySettings):
                    outcome = search_entropy(
                        problem,
                        initial,
                        settings=settings,
                        deadline=attempt_deadline,
                        checkpoint=guarded_checkpoint,
                    )
                else:
                    outcome = search_corrective(
                        problem,
                        initial,
                        settings=settings,
                        deadline=probe_deadline,
                        checkpoint=guarded_checkpoint,
                    )
            except _AssessmentFailure as failure:
                raised = failure.failure
            except _UnsolvedAssessment as unsolved:
                termination = "target_met" if target_met() else "oracle_failure"
                attempts.append(
                    {
                        **allocation,
                        "probe": probe + 1,
                        "probe_source": source if probe == 0 else "series_best",
                        "termination": termination,
                        "seconds": time.perf_counter() - probe_start,
                        "probe_start_seconds": probe_start - started,
                        "probe_available_seconds": max(
                            0.0, attempt_deadline - probe_start
                        ),
                        "probe_deadline_seconds": probe_deadline - started,
                        "settings": asdict(settings),
                        "oracle_failure": {
                            "iteration": unsolved.assessment.gate.iteration,
                            "oracle_status": unsolved.assessment.gate.oracle_status,
                            "message": str(unsolved.assessment.oracle_failure),
                        },
                        "assessed_bound_before": previous_bound,
                        "assessed_bound_after": None
                        if best is None
                        else best.gate.linearization,
                        "continued": False,
                        **(
                            {"stop_reason": "oracle_failure", "progressed": False}
                            if probing
                            else {}
                        ),
                    }
                )
                break
            if raised is not None:
                # The checkpoint's own exception, its cause, its context and
                # its mark (_mark_numerical) as they were.
                raise raised
            checkpoint(outcome.point, outcome.q_exact, final=True)
            stopped = outcome.termination
            if stopped == "target_met" and not target_met():
                # A search stops at a checkpoint that returns true, which is
                # the gap target met OR the solve's deadline passed; only the
                # first is a met target.
                stopped = "budget_exhausted"
            termination = "target_met" if target_met() else stopped
            current_bound = None if best is None else best.gate.linearization
            for assessment in assessments[assessed_before:]:
                if assessment.contributes and (
                    series_best is None
                    or assessment.gate.linearization > series_best.gate.linearization
                ):
                    series_best = assessment
            series_after = (
                None if series_best is None else series_best.gate.linearization
            )
            progress_floor = (
                None
                if series_before is None or series_after is None
                else 32 * math.ulp(max(1.0, abs(series_before), abs(series_after)))
            )
            progress_threshold = (
                None
                if progress_floor is None or open_before is None
                else max(progress_floor, CORRECTIVE_PROGRESS_FRACTION * open_before)
            )
            progressed = series_after is not None and (
                series_before is None
                or (
                    progress_threshold is not None
                    and series_after - series_before > progress_threshold
                )
            )
            support_refused = (
                probing
                and isinstance(settings, CorrectiveSettings)
                and stopped == "numerical_failure"
                and outcome.diagnostics.get("support_refusal") is True
            )
            raise_blend = (
                support_refused
                and isinstance(settings, CorrectiveSettings)
                and settings.blend < SUPPORT_FALLBACK_BLEND
            )
            out_of_time = time.perf_counter() >= attempt_deadline
            stop_reason = (
                None
                if not probing
                else "target_met"
                if target_met()
                else ("stage_deadline" if out_of_time else None)
                if raise_blend
                else f"search_{stopped}"
                if stopped not in ("budget_exhausted", "stagnated")
                else "stage_deadline"
                if out_of_time
                else "no_bracket_progress"
                if not progressed
                else None
            )
            continue_probe = probing and stop_reason is None
            attempts.append(
                {
                    **allocation,
                    "probe": probe + 1,
                    "probe_source": source if probe == 0 else "series_best",
                    "termination": termination,
                    "seconds": time.perf_counter() - probe_start,
                    "probe_start_seconds": probe_start - started,
                    "probe_available_seconds": max(0.0, attempt_deadline - probe_start),
                    "probe_deadline_seconds": probe_deadline - started,
                    "settings": asdict(settings),
                    "iterations": outcome.iterations,
                    "evaluations": outcome.evaluations,
                    "oracle_calls": outcome.oracle_calls,
                    "diagnostics": outcome.diagnostics,
                    "assessed_bound_before": previous_bound,
                    "assessed_bound_after": current_bound,
                    "series_bound_before": series_before,
                    "series_bound_after": series_after,
                    "progress_roundoff_floor": progress_floor,
                    "progress_threshold": progress_threshold,
                    "continued": continue_probe,
                    **(
                        {
                            "stop_reason": stop_reason,
                            "progressed": progressed,
                            "blend": settings.blend
                            if isinstance(settings, CorrectiveSettings)
                            else None,
                            "support_refusal": support_refused,
                            "blend_raised_to": SUPPORT_FALLBACK_BLEND
                            if raise_blend
                            else None,
                        }
                        if probing
                        else {}
                    ),
                }
            )
            if not continue_probe:
                break
            if raise_blend:
                assert isinstance(settings, CorrectiveSettings)
                settings = replace(settings, blend=SUPPORT_FALLBACK_BLEND)
                if series_best is not None:
                    initial = series_best.point
            else:
                assert series_best is not None
                initial = series_best.point
            probe += 1
    if target_met() and not (request.method != "auto" and termination == "unsupported"):
        termination = "target_met"
    elif time.perf_counter() >= deadline:
        termination = "budget_exhausted"
    # THE STOP CAUSE, READ AGAINST THE VALUE (CONVERGED_RELATIVE_GAP): a
    # relabelling after the search, which stops nothing and moves no bound.
    relative_gap = _open_relative(best, estimate)
    termination = classify_termination(termination, relative_gap)
    assert estimate is not None
    last = assessments[-1]
    point = estimate.point
    try:
        returned = _check_point(
            problem.maps.parametrization,
            point,
            problem.settings,
            "returned point",
            residuals_fatal=False,
        )
    except NUMERICAL_FAILURES as failure:
        _mark_numerical(failure)
        raise
    bracket = None if best is None else best.gate.linearization
    elapsed = time.perf_counter() - started
    report = {
        "method": request.method,
        "policy": POLICY_ID if request.method == "auto" else "explicit-v1",
        "termination": termination,
        "budget_seconds": total,
        "gap_target": request.gap_target,
        # The relative bracket the termination was classified on, and the
        # level at which a stagnated search reads relative_gap_met.
        "relative_gap": relative_gap,
        "converged_relative_gap": CONVERGED_RELATIVE_GAP,
        "max_iterations": request.max_iterations,
        "attempts": attempts,
        "resolved_allocations": allocations,
        "resume_rule": RESUME_RULE if auto else None,
        # What max_iterations capped (the decision above the stage loop).
        "max_iterations_caps": ["fw"] if auto else [request.method],
        "corrective_probes": {
            "slice_of_stage": CORRECTIVE_PROBE_SLICE,
            "progress_fraction": CORRECTIVE_PROGRESS_FRACTION,
            "cold_tau": CORRECTIVE_COLD_TAU,
            "fallback_blend": SUPPORT_FALLBACK_BLEND,
            "rule": (
                "another probe, from the series' own best assessed point, while "
                "the series' best assessed bracket rose by more than "
                "progress_fraction of the bracket left open above it, the stage "
                "has time left and the gap target is unmet"
            ),
        }
        if auto
        else None,
        "resolved_schedule": [
            {
                "method": method,
                "start": source,
                "budget_share": share,
                "unsupported_reason": reasons[method],
            }
            for method, source, share in schedule
        ],
        "preparation_seconds": problem.preparation_seconds,
        "solver_seconds": elapsed,
        "budget_overrun_seconds": max(0.0, elapsed - total),
        "assessment_count": len(assessment_history),
        "iteration_unit": "assessment",
        "assessment_history": assessment_history,
        "capabilities": dict(problem.capabilities),
        "best_contributing_candidate": _assessment_payload(best),
        "last_candidate": _assessment_payload(last),
        "returned_candidate_role": "best_original_objective",
    }
    return JointFrankWolfeResult(
        objective=estimate.objective,
        choi=point,
        q=estimate.q_iterate.view,
        iterations=len(assessment_history),
        gap=math.inf if best is None else best.gap,
        h_lb=bracket if not problem.dropped else None,
        h_lb_dropped=bracket if problem.dropped else None,
        dropped_set=tuple(sorted(problem.dropped)),
        withdrawal=None if best is not None else last.gate.withdrawal,
        status=termination,
        gates=tuple(x.gate for x in assessments),
        oracle_diagnostics=tuple(y for x in assessments for y in x.oracle_diagnostics),
        timings=timings,
        solver_report={
            "oracle": request.oracle,
            "assignment": dict(problem.assignment),
            "search": request.method,
        },
        returned_point=returned,
        estimate_point_relaxed_member=returned.established(problem.settings),
        best_assessment=best,
        search_report=report,
        reference_candidates=candidates.points(),
        **joint_run_metadata(problem.maps, first_order=best is not None),
    )
