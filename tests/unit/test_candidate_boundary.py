"""One candidate gate, independent of search and its convergence status."""

from dataclasses import replace
from fractions import Fraction
from typing import Any

import numpy as np
import pytest
from tests.support.general_toys import decoy_like_general, honest_q, maps_of
from tests.unit.test_meat_joint_driver import _EchoOracle

from certiqs_key.meat_core.errors import SupportError
from certiqs_key.meat_core.reasons import AssuranceReason
from certiqs_key.solvers.assessment import assess_candidate
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    joint_initial_point,
    run_joint_frank_wolfe,
)
from certiqs_key.solvers.oracles.acceptance import SingletonAcceptanceOracle
from certiqs_key.solvers.problem import prepared_from_maps
from certiqs_key.solvers.solve import solve_prepared
from certiqs_key.solvers.types import SearchRequest, SearchResult


def _problem(options: FrankWolfeOptions | None = None, dropped: Any = None) -> Any:
    maps = maps_of(decoy_like_general())
    point = joint_initial_point(maps.parametrization)
    return prepared_from_maps(
        maps,
        _EchoOracle(point, trusted=True),
        SingletonAcceptanceOracle(honest_q(maps, point)),
        1.5,
        options or FrankWolfeOptions(max_iterations=1),
        dropped=dropped,
    )


@pytest.mark.parametrize("dropped", [None, [("match", ("one", "q"))]])
def test_one_point_assessment_matches_explicit_fw_gate(dropped: Any) -> None:
    problem = _problem(dropped=dropped)
    assessed = assess_candidate(problem, problem.initial)
    fw = run_joint_frank_wolfe(
        problem.maps,
        problem.oracle,
        problem.acceptance,
        problem.initial,
        problem.alpha,
        problem.settings,
        dropped=problem.dropped,
    )
    assert assessed.gate == fw.gates[0]
    assert assessed.gap == fw.gap
    assert assessed.bracket == (fw.h_lb_dropped if dropped else fw.h_lb)
    assert assessed.q_iterate.view == fw.q


@pytest.mark.parametrize("invalid", ["outside", "missing", "float"])
def test_external_q_cannot_vouch_for_its_own_membership(invalid: str) -> None:
    problem = _problem()
    exact = {key: Fraction(value) for key, value in problem.acceptance.start().items()}
    first = next(iter(exact))
    if invalid == "outside":
        exact[first] += Fraction(1, 100)
    elif invalid == "missing":
        exact.pop(first)
    else:
        exact[first] = float(exact[first])  # type: ignore[assignment]
    result = assess_candidate(problem, problem.initial, exact)
    assert result.bracket is None
    assert result.gate.withdrawal == str(AssuranceReason.ITERATE_NOT_FEASIBLE)
    assert result.gate.oracle_status == "not-called"


def test_perturbed_gradient_stays_withdrawn_in_shared_assessor() -> None:
    problem = _problem(FrankWolfeOptions(gradient_perturbation=1e-8))
    result = assess_candidate(problem, problem.initial)
    assert not result.contributes
    assert result.gate.withdrawal == str(AssuranceReason.GRADIENT_PERTURBATION_APPLIED)


def test_coupling_residual_withdraws_instead_of_becoming_a_search_tolerance() -> None:
    problem = _problem()
    point = {pair: block * 1.001 for pair, block in problem.initial.items()}
    result = assess_candidate(problem, point)
    assert not result.contributes
    assert result.gate.withdrawal == str(AssuranceReason.ITERATE_NOT_FEASIBLE)


def test_invalid_psd_and_nonhermitian_candidates_are_refused() -> None:
    problem = _problem()
    point = {pair: block.copy() for pair, block in problem.initial.items()}
    point[next(iter(point))][0, 0] = -1
    with pytest.raises(SupportError):
        assess_candidate(problem, point)
    point = {pair: block.copy() for pair, block in problem.initial.items()}
    point[next(iter(point))][0, 1] = 0.1j
    with pytest.raises(SupportError):
        assess_candidate(problem, point)


def test_a_nonoptimal_oracle_status_changes_no_bound() -> None:
    """``req:first-order-withdrawal``: no status of the oracle withdraws an iterate.

    The feasible side of the bracket is verified without the return or its
    status (``req:verified-feasible-side``), so a near-optimal status withdraws
    nothing.
    """
    problem = _problem()
    control = assess_candidate(problem, problem.initial)
    original = problem.oracle.minimize

    def not_optimal(program: Any) -> Any:
        return replace(original(program), diagnostics={"sol_status": "near_optimal"})

    problem.oracle.minimize = not_optimal
    result = assess_candidate(problem, problem.initial)
    assert result.contributes
    assert result.gate.withdrawal is None
    assert result.bracket == control.bracket
    assert result.gate.oracle_status == "near_optimal"


def test_explicit_request_returns_generic_result_and_contributing_point() -> None:
    problem = _problem()
    result = solve_prepared(problem, SearchRequest(max_iterations=1))
    assert isinstance(result, SearchResult)
    assert result.best_assessment is not None
    assert result.best_assessment.bracket == result.h_lb
    assert result.search_report["method"] == "fw"
    assert result.search_report["best_contributing_candidate"]["q"] == result.q


def test_deadline_keeps_last_qualifying_bound() -> None:
    problem = _problem(FrankWolfeOptions(max_iterations=5, gap_tolerance=-1))
    result = run_joint_frank_wolfe(
        problem.maps,
        problem.oracle,
        problem.acceptance,
        problem.initial,
        problem.alpha,
        problem.settings,
        deadline=0.0,
    )
    assert result.status == "budget_exhausted"
    assert len(result.gates) == 1
    assert result.h_lb == result.gates[0].linearization
    assert all(
        np.array_equal(result.choi[key], value)
        for key, value in problem.initial.items()
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"budget_seconds": 0},
        {"gap_target": float("inf")},
        {"max_iterations": 0},
        {"method": "made-up"},
    ],
)
def test_request_validates_effort_only(kwargs: Any) -> None:
    with pytest.raises(ValueError):
        SearchRequest(**kwargs)


@pytest.mark.parametrize(
    "change",
    [
        {"method": "pairwise"},
        {"oracle": "spectral"},
        {"max_iterations": 2},
        {"gap_target": 0.001},
    ],
)
def test_prepared_request_mismatch_is_explicit(change: Any) -> None:
    problem = _problem()
    request = replace(SearchRequest(max_iterations=1), **change)
    with pytest.raises(ValueError, match="prepared settings differ"):
        solve_prepared(problem, request)


def test_later_lower_objective_keeps_earlier_stronger_bound(monkeypatch: Any) -> None:
    import certiqs_key.solvers.search.factor as factor
    import certiqs_key.solvers.solve as coordinator
    from certiqs_key.solvers.search.common import SearchOutcome

    problem = _problem()
    base = assess_candidate(problem, problem.initial)
    first = replace(
        base, gate=replace(base.gate, objective=2.0, linearization=1.5), gap=0.5
    )
    later = replace(
        base, gate=replace(base.gate, objective=1.0, linearization=0.9), gap=0.1
    )
    assessments = iter((first, later))
    monkeypatch.setattr(
        coordinator, "assess_candidate", lambda *a, **k: next(assessments)
    )
    monkeypatch.setattr(
        factor,
        "search_factor",
        lambda *a, **k: SearchOutcome(
            problem.initial, {}, 1.0, "numerical_failure", iterations=999
        ),
    )
    result = solve_prepared(problem, SearchRequest(method="factor", max_iterations=1))
    assert result.h_lb == 1.5
    assert result.objective == 1.0
    assert result.best_assessment == first
    assert result.status == "numerical_failure"
    assert result.iterations == result.search_report["assessment_count"] == 2
    assert result.search_report["attempts"][0]["iterations"] == 999
    assert result.search_report["last_candidate"]["gate"]["linearization"] == 0.9


def test_negative_later_assessment_is_mandatory_run_refusal(monkeypatch: Any) -> None:
    import certiqs_key.solvers.search.factor as factor
    import certiqs_key.solvers.solve as coordinator
    from certiqs_key.solvers.frank_wolfe.general_keyrate import NegativeObjectiveError
    from certiqs_key.solvers.search.common import SearchOutcome

    problem = _problem()
    base = assess_candidate(problem, problem.initial)
    first = replace(
        base, gate=replace(base.gate, objective=2.0, linearization=1.5), gap=0.5
    )
    negative = replace(
        base, gate=replace(base.gate, objective=-1.0, linearization=-2.0), gap=1.0
    )
    assessments = iter((first, negative))
    monkeypatch.setattr(
        coordinator, "assess_candidate", lambda *a, **k: next(assessments)
    )

    def search(*args: Any, **kwargs: Any) -> Any:
        kwargs["checkpoint"](problem.initial, {})
        return SearchOutcome(problem.initial, {}, 0.0, "stagnated")

    monkeypatch.setattr(factor, "search_factor", search)
    with pytest.raises(NegativeObjectiveError):
        solve_prepared(problem, SearchRequest(method="factor", max_iterations=1))


def test_explicit_unsupported_method_is_reported_even_at_a_good_anchor(
    monkeypatch: Any,
) -> None:
    import certiqs_key.solvers.search.common as common

    problem = _problem()
    monkeypatch.setattr(common, "capability_reason", lambda *a: "unsupported geometry")
    result = solve_prepared(problem, SearchRequest(method="factor", max_iterations=1))
    assert result.status == "unsupported"
    assert result.search_report["attempts"][0]["reason"] == "unsupported geometry"


@pytest.mark.parametrize("method", ["fw", "pairwise", "auto"])
def test_supplied_row_start_only_builds_cold_anchor_when_needed(method: str) -> None:
    from tests.unit.test_joint_solver_options import _trusted_with_a_row

    maps = maps_of(_trusted_with_a_row(bound=1.0))
    point = joint_initial_point(maps.parametrization)
    oracle = _EchoOracle(point, trusted=True)
    request = SearchRequest(method=method)
    prepared = prepared_from_maps(
        maps,
        oracle,
        SingletonAcceptanceOracle(honest_q(maps, point)),
        1.5,
        request.fw_options(),
        start=point,
        search_method=method,
    )
    assert len(oracle.problems) == (
        len(maps.declaration.alice_sectors) if method == "auto" else 0
    )
    assert prepared.search_method == method
    if method == "fw":
        with pytest.raises(ValueError, match="method"):
            solve_prepared(prepared, replace(request, method="auto"))


def test_good_warm_seed_does_not_skip_independent_cold_assessment(
    monkeypatch: Any,
) -> None:
    from tests.unit.test_joint_solver_options import _seed

    import certiqs_key.solvers.search.factor as factor
    import certiqs_key.solvers.solve as coordinator

    original = _problem()
    seed = _seed(original.maps.declaration)
    request = SearchRequest(method="auto", max_iterations=1, warm_start=seed)
    problem = prepared_from_maps(
        original.maps,
        original.oracle,
        original.acceptance,
        original.alpha,
        request.fw_options(),
        search_method="auto",
    )
    assert any(
        not np.array_equal(problem.initial[pair], block)
        for pair, block in problem.anchor.items()
    )
    base = assess_candidate(original, original.anchor)
    good = replace(
        base,
        point=problem.initial,
        gate=replace(base.gate, objective=2.0, linearization=2.0),
        gap=0.0,
    )
    cold = replace(
        base,
        point=problem.anchor,
        gate=replace(base.gate, objective=3.0, linearization=1.0),
        gap=2.0,
    )
    seen = []

    def assess(problem: Any, point: Any, *args: Any, **kwargs: Any) -> Any:
        seen.append(point)
        return good if len(seen) == 1 else cold

    def search(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("target was met by the warm seed")

    monkeypatch.setattr(coordinator, "assess_candidate", assess)
    monkeypatch.setattr(factor, "search_factor", search)
    result = solve_prepared(problem, request)
    assert len(seen) == 2
    assert seen[0] is problem.initial and seen[1] is problem.anchor
    assert result.h_lb == 2.0
    assert result.status == "target_met"
    assert result.search_report["assessment_count"] == 2
    assert result.iterations == 2
    assert result.search_report["iteration_unit"] == "assessment"
    assert [
        row["raw_bracket"] for row in result.search_report["assessment_history"]
    ] == [2.0, 1.0]


def test_fw_history_observes_each_gate_without_additional_oracle_calls() -> None:
    problem = _problem()
    result = solve_prepared(problem, SearchRequest(max_iterations=1))
    history = result.search_report["assessment_history"]
    assert len(history) == len(result.gates) == 1
    assert len(problem.oracle.problems) == len(problem.maps.declaration.alice_sectors)
    for row, gate in zip(history, result.gates, strict=True):
        assert row["objective"] == gate.objective
        assert row["raw_bracket"] == gate.linearization
        assert row["raw_gap"] == result.gap
        assert row["contributes"] == gate.contributes
        assert row["withdrawal"] == gate.withdrawal
        assert 0 <= row["elapsed_seconds"] <= result.search_report["solver_seconds"]
    assert result.search_report["iteration_unit"] == "fw_iteration"


def _mock_portfolio(monkeypatch: Any, *, max_iterations: int = 100) -> Any:
    import certiqs_key.solvers.search.common as common
    import certiqs_key.solvers.solve as coordinator

    request = SearchRequest(
        method="auto", budget_seconds=100, max_iterations=max_iterations
    )
    problem = _problem(request.fw_options())
    base = assess_candidate(problem, problem.initial)
    clock = [0.0]
    bracket = [1.0]

    def assess(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 1.0
        return replace(
            base,
            gate=replace(base.gate, objective=10.0, linearization=bracket[0]),
            gap=10.0 - bracket[0],
        )

    monkeypatch.setattr(coordinator.time, "perf_counter", lambda: clock[0])
    monkeypatch.setattr(coordinator, "assess_candidate", assess)
    monkeypatch.setattr(common, "capability_reason", lambda *args: None)
    # Every mocked search returns the same point, so the warm and the cold
    # corrective series would start alike and the cold one be skipped;
    # these tests are about the series themselves, so the mock treats
    # the two starts as different. tests/unit/test_auto_caps.py holds the skip.
    monkeypatch.setattr(coordinator, "_same_start", lambda first, second: False)
    return problem, request, clock, bracket


def test_an_entropy_stage_its_allocation_guard_refuses_gets_no_share(
    monkeypatch: Any,
) -> None:
    import certiqs_key.solvers.search.corrective as corrective
    import certiqs_key.solvers.search.entropy as entropy
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.search.common import SearchOutcome

    problem, request, clock, _ = _mock_portfolio(monkeypatch)
    ran: list[str] = []

    def refuse(*args: Any, **kwargs: Any) -> int:
        raise MemoryError("entropy allocation plan exceeds assembly memory budget")

    def search_as(name: str) -> Any:
        def search(*args: Any, **kwargs: Any) -> Any:
            ran.append(name)
            clock[0] += 2.0
            return SearchOutcome(problem.initial, {}, 10.0, "stagnated")

        return search

    monkeypatch.setattr(entropy, "entropy_preflight", refuse)
    for module, name in (
        (factor, "search_factor"),
        (entropy, "search_entropy"),
        (corrective, "search_corrective"),
    ):
        monkeypatch.setattr(module, name, search_as(name))
    report = solve_prepared(problem, request).search_report
    assert "search_entropy" not in ran
    (skip,) = [a for a in report["attempts"] if a["method"] == "entropy"]
    assert skip["termination"] == "skipped"
    assert skip["reason"] == "resource_infeasible"
    allocations = report["resolved_allocations"]
    assert [row["method"] for row in allocations[:3]] == [
        "factor",
        "corrective",
        "corrective",
    ]
    # The refused half of the budget goes to the stages that can run: factor
    # gets 0.25 of the remaining supported 0.50, not 0.25 of 1.0.
    assert allocations[0]["normalized_remaining_share"] == pytest.approx(0.5)


@pytest.mark.parametrize("refusal", [None, ValueError("nonempty Choi blocks")])
def test_an_admitted_or_failing_preflight_leaves_the_entropy_stage_scheduled(
    monkeypatch: Any, refusal: Exception | None
) -> None:
    # The real preflight admits the toy's small cone; a preflight failure that
    # is not the allocation guard's is the stage's to meet, as in v4, and
    # never ends the solve before the stage loop.
    import certiqs_key.solvers.search.corrective as corrective
    import certiqs_key.solvers.search.entropy as entropy
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.search.common import SearchOutcome

    problem, request, clock, _ = _mock_portfolio(monkeypatch)
    if refusal is not None:

        def fail(*args: Any, **kwargs: Any) -> Any:
            raise refusal

        monkeypatch.setattr(entropy, "_cone_plan", fail)

    def search(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 2.0
        return SearchOutcome(problem.initial, {}, 10.0, "stagnated")

    for module, name in (
        (factor, "search_factor"),
        (entropy, "search_entropy"),
        (corrective, "search_corrective"),
    ):
        monkeypatch.setattr(module, name, search)
    report = solve_prepared(problem, request).search_report
    allocations = report["resolved_allocations"]
    assert [row["method"] for row in allocations[:2]] == ["factor", "entropy"]
    assert allocations[0]["normalized_remaining_share"] == pytest.approx(0.25)
    assert not any(a.get("reason") == "resource_infeasible" for a in report["attempts"])


def test_portfolio_reclaims_early_finish_time_without_extending_global_budget(
    monkeypatch: Any,
) -> None:
    import certiqs_key.solvers.search.corrective as corrective
    import certiqs_key.solvers.search.entropy as entropy
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.search.common import SearchOutcome

    problem, request, clock, _ = _mock_portfolio(monkeypatch)
    calls = []

    def search(*args: Any, **kwargs: Any) -> Any:
        calls.append((clock[0], kwargs["deadline"]))
        clock[0] += 2.0
        return SearchOutcome(problem.initial, {}, 10.0, "stagnated")

    for module, name in (
        (factor, "search_factor"),
        (entropy, "search_entropy"),
        (corrective, "search_corrective"),
    ):
        monkeypatch.setattr(module, name, search)
    result = solve_prepared(problem, request)
    report = result.search_report
    assert report["policy"] == "candidate-portfolio-v5"
    allocations = report["resolved_allocations"]
    assert [row["budget_share"] for row in allocations] == [0.25, 0.50, 0.15, 0.10]
    assert allocations[0]["allocated_seconds"] == pytest.approx(98 * 0.25)
    # Early factor exit returns its unused time to the remaining supported stages.
    assert allocations[1]["allocated_seconds"] == pytest.approx(95 * 0.50 / 0.75)
    assert allocations[-1]["normalized_remaining_share"] == 1.0
    assert allocations[-1]["deadline_seconds"] == 99.0
    assert all(start < deadline <= 99 for start, deadline in calls)


def test_all_unsupported_candidates_give_fw_the_full_remaining_budget(
    monkeypatch: Any,
) -> None:
    import certiqs_key.solvers.search.common as common
    import certiqs_key.solvers.solve as coordinator

    problem, request, clock, _ = _mock_portfolio(monkeypatch)
    monkeypatch.setattr(common, "capability_reason", lambda *args: "geometry")
    # Obtain a structurally valid FW result without running a second numerical search.
    base = assess_candidate(problem, problem.initial)
    calls = []

    def fw(*args: Any, **kwargs: Any) -> Any:
        calls.append(kwargs["deadline"])
        kwargs["assessment_observer"](base)
        clock[0] += 2
        return SearchResult(
            objective=base.objective,
            choi=problem.initial,
            q=base.q_iterate.view,
            iterations=1,
            gap=base.gap,
            h_lb=base.bracket,
            h_lb_dropped=None,
            dropped_set=(),
            withdrawal=None,
            status="iteration-limit",
            best_assessment=base,
        )

    monkeypatch.setattr(coordinator, "run_joint_frank_wolfe", fw)
    result = solve_prepared(problem, request)
    assert calls == [99.0]
    allocations = result.search_report["resolved_allocations"]
    assert len(allocations) == 1 and allocations[0]["method"] == "fw"
    assert allocations[0]["normalized_remaining_share"] == 1.0
    assert (
        sum(a["termination"] == "unsupported" for a in result.search_report["attempts"])
        == 3
    )


@pytest.mark.parametrize(
    "step,cap,probes",
    [
        # Progress of at least 1 % of the open bracket earns another probe
        # until the stage's time is spent, whatever max_iterations says.
        (0.1, 100, None),
        (0.1, 1, None),
        # No progress, or less than 1 % of the open bracket (about 9 here):
        # one probe per stage.
        (0.0, 100, 1),
        (1e-6, 100, 1),
    ],
)
def test_corrective_probes_continue_while_the_assessed_bracket_improves(
    monkeypatch: Any,
    step: float,
    cap: int,
    probes: int | None,
) -> None:
    import certiqs_key.solvers.search.common as common
    import certiqs_key.solvers.search.corrective as corrective
    from certiqs_key.solvers.search.common import SearchOutcome

    problem, request, clock, bracket = _mock_portfolio(monkeypatch, max_iterations=cap)
    monkeypatch.setattr(
        common,
        "capability_reason",
        lambda problem, method: None if method == "corrective" else "geometry",
    )
    calls = []

    def search(*args: Any, **kwargs: Any) -> Any:
        calls.append((kwargs["settings"].max_iterations, kwargs["deadline"]))
        clock[0] += 1.0
        bracket[0] += step
        return SearchOutcome(
            problem.initial, {}, 10.0, "budget_exhausted", iterations=20
        )

    monkeypatch.setattr(corrective, "search_corrective", search)
    result = solve_prepared(problem, request)
    report = result.search_report
    assert {count for count, _ in calls} == {None}
    assert report["max_iterations_caps"] == ["fw"]
    attempts = [a for a in report["attempts"] if a["method"] == "corrective"]
    stages = sorted({a["stage"] for a in attempts})
    assert len(stages) == 2
    for stage in stages:
        series = [a for a in attempts if a["stage"] == stage]
        assert [a["probe"] for a in series] == list(range(1, len(series) + 1))
        assert all(a["continued"] for a in series[:-1])
        assert not series[-1]["continued"]
        allocated = series[0]["allocated_seconds"]
        for probe in series:
            assert probe["probe_deadline_seconds"] <= probe["deadline_seconds"]
            # A slice of at most a quarter of the stage, or the stage's rest
            # where less than half a slice would be left after it.
            assert probe["probe_deadline_seconds"] - probe[
                "probe_start_seconds"
            ] <= 0.25 * allocated + 1e-9 or probe["probe_deadline_seconds"] == probe[
                "deadline_seconds"
            ]
        if probes is None:
            assert len(series) > 2
            assert series[-1]["stop_reason"] == "stage_deadline"
        else:
            # A warm series starts at the global best and is judged against
            # it; a cold series has no baseline, so its first bracket is its
            # first progress and earns one more probe.
            cold = series[0]["source"] == "cold"
            assert len(series) == probes + int(cold)
            assert series[-1]["stop_reason"] == "no_bracket_progress"
            assert [a["progressed"] for a in series] == [True] * int(cold) + [
                False
            ] * probes
    assert all(deadline <= 99 for _, deadline in calls)


def test_corrective_does_not_continue_after_its_stage_deadline(
    monkeypatch: Any,
) -> None:
    import certiqs_key.solvers.search.common as common
    import certiqs_key.solvers.search.corrective as corrective
    from certiqs_key.solvers.search.common import SearchOutcome

    problem, request, clock, bracket = _mock_portfolio(monkeypatch)
    monkeypatch.setattr(
        common,
        "capability_reason",
        lambda problem, method: None if method == "corrective" else "geometry",
    )
    deadlines = []

    def search(*args: Any, **kwargs: Any) -> Any:
        # Each probe spends all the time it was given, and progresses.
        deadlines.append(kwargs["deadline"])
        clock[0] = kwargs["deadline"]
        bracket[0] += 0.1
        return SearchOutcome(
            problem.initial, {}, 10.0, "budget_exhausted", iterations=20
        )

    monkeypatch.setattr(corrective, "search_corrective", search)
    result = solve_prepared(problem, request)
    attempts = [
        a for a in result.search_report["attempts"] if a["method"] == "corrective"
    ]
    for stage in {a["stage"] for a in attempts}:
        series = [a for a in attempts if a["stage"] == stage]
        # A probe that spends its slice leaves room for more: about four per
        # stage, the last ending at the stage's deadline.
        assert 2 < len(series) <= 5
        assert series[-1]["stop_reason"] == "stage_deadline"
        assert not series[-1]["continued"]
        assert max(a["probe_deadline_seconds"] for a in series) == pytest.approx(
            series[0]["deadline_seconds"]
        )
    assert result.search_report["solver_seconds"] == pytest.approx(100.0)
    assert max(deadlines) <= 99


def test_a_failing_probe_ends_the_corrective_series(monkeypatch: Any) -> None:
    import certiqs_key.solvers.search.common as common
    import certiqs_key.solvers.search.corrective as corrective
    from certiqs_key.solvers.search.common import SearchOutcome

    problem, request, clock, bracket = _mock_portfolio(monkeypatch)
    monkeypatch.setattr(
        common,
        "capability_reason",
        lambda problem, method: None if method == "corrective" else "geometry",
    )

    def search(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 1.0
        bracket[0] += 0.1
        return SearchOutcome(problem.initial, {}, 10.0, "numerical_failure")

    monkeypatch.setattr(corrective, "search_corrective", search)
    result = solve_prepared(problem, request)
    attempts = [
        a for a in result.search_report["attempts"] if a["method"] == "corrective"
    ]
    assert [a["stop_reason"] for a in attempts] == ["search_numerical_failure"] * 2


def test_a_search_stopped_at_the_deadline_is_not_reported_as_target_met(
    monkeypatch: Any,
) -> None:
    """A checkpoint returns true at the target OR the solve's deadline."""
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.search.common import SearchOutcome

    problem, request, clock, _ = _mock_portfolio(monkeypatch)
    request = replace(request, method="factor")

    def search(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 1.0
        return SearchOutcome(problem.initial, {}, 10.0, "target_met")

    monkeypatch.setattr(factor, "search_factor", search)
    result = solve_prepared(problem, request)
    attempt = result.search_report["attempts"][0]
    assert attempt["termination"] == "budget_exhausted"
    assert "stop_reason" not in attempt


def test_explicit_corrective_honors_requested_native_cap(monkeypatch: Any) -> None:
    import certiqs_key.solvers.search.corrective as corrective
    from certiqs_key.solvers.search.common import SearchOutcome

    problem, request, _, _ = _mock_portfolio(monkeypatch, max_iterations=10000)
    request = replace(request, method="corrective")
    seen = []

    def search(*args: Any, **kwargs: Any) -> Any:
        seen.append(kwargs["settings"].max_iterations)
        return SearchOutcome(problem.initial, {}, 10.0, "stagnated")

    monkeypatch.setattr(corrective, "search_corrective", search)
    result = solve_prepared(problem, request)
    assert seen == [10000]
    assert result.search_report["attempts"][0]["settings"]["max_iterations"] == 10000
