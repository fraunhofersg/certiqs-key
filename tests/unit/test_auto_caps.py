"""What max_iterations caps under method auto: the Frank-Wolfe stages only.

Under method auto, max_iterations caps the Frank-Wolfe stages only. On the
BBM92 encoded route at cutoff 3 a factor stage capped at max_iterations = 200
stops after 14.5 s of its 150 s share with h_lb -0.0507; uncapped it converges
by its own L-BFGS tolerance. Held here:

* under auto, the factor search, the entropy stage's polish and the
  corrective search get no iteration cap (``max_iterations=None``), and the
  entropy cone keeps its own default;
* an explicit factor, entropy or corrective request keeps max_iterations as
  its cap, and auto's Frank-Wolfe stage keeps it too;
* an uncapped search runs to its own convergence and refuses to run without
  a deadline.

The corrective probe rule is held in tests/unit/test_candidate_boundary.py
beside the portfolio's other allocation tests. These are search-effort
tests: every candidate is still certified by solvers/assessment.py, so no
claim rests on them.
"""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Any

import pytest
from tests.unit.test_candidate_boundary import _mock_portfolio, _problem

from certiqs_key.solvers.assessment import assess_candidate
from certiqs_key.solvers.search.common import (
    CorrectiveSettings,
    EntropySettings,
    FactorSettings,
    SearchOutcome,
)
from certiqs_key.solvers.solve import (
    CORRECTIVE_COLD_TAU,
    solve_prepared,
)
from certiqs_key.solvers.solve import _same_start as real_same_start
from certiqs_key.solvers.types import SearchResult


def _capture(monkeypatch: Any, problem: Any, clock: list[float]) -> list[Any]:
    import certiqs_key.solvers.search.corrective as corrective
    import certiqs_key.solvers.search.entropy as entropy
    import certiqs_key.solvers.search.factor as factor

    seen: list[Any] = []

    def search(*args: Any, **kwargs: Any) -> Any:
        seen.append(kwargs["settings"])
        clock[0] += 1.0
        return SearchOutcome(problem.initial, {}, 10.0, "stagnated")

    for module, name in (
        (factor, "search_factor"),
        (entropy, "search_entropy"),
        (corrective, "search_corrective"),
    ):
        monkeypatch.setattr(module, name, search)
    return seen


def test_auto_runs_factor_entropy_and_corrective_uncapped(monkeypatch: Any) -> None:
    problem, request, clock, _ = _mock_portfolio(monkeypatch, max_iterations=7)
    seen = _capture(monkeypatch, problem, clock)
    result = solve_prepared(problem, request)
    factor, entropy, *correctives = seen
    assert len(correctives) >= 2
    assert isinstance(factor, FactorSettings) and factor.max_iterations is None
    assert isinstance(entropy, EntropySettings)
    assert entropy.polish.max_iterations is None
    # The cone keeps its own iteration default, not min(100, max_iterations).
    assert entropy.max_iterations == EntropySettings().max_iterations == 100
    for settings in correctives:
        assert isinstance(settings, CorrectiveSettings)
        assert settings.max_iterations is None
    report = result.search_report
    assert report["max_iterations_caps"] == ["fw"]
    assert report["max_iterations"] == 7
    assert report["corrective_probes"]["slice_of_stage"] == 0.25
    stages = [a for a in report["attempts"] if "settings" in a]
    assert len(stages) == len(seen)
    for attempt in stages:
        native = attempt["settings"]
        if attempt["method"] == "entropy":
            assert native["max_iterations"] == 100  # the cone's own
            native = native["polish"]
        assert native["max_iterations"] is None, attempt["method"]


@pytest.mark.parametrize("method", ["factor", "entropy", "corrective"])
def test_an_explicit_method_keeps_max_iterations_as_its_cap(
    monkeypatch: Any, method: str
) -> None:
    problem, request, clock, _ = _mock_portfolio(monkeypatch, max_iterations=7)
    request = replace(request, method=method)
    seen = _capture(monkeypatch, problem, clock)
    result = solve_prepared(problem, request)
    (settings,) = seen
    if isinstance(settings, EntropySettings):
        assert settings.max_iterations == 7
        assert settings.polish.max_iterations == 7
    else:
        assert settings.max_iterations == 7
    assert result.search_report["max_iterations_caps"] == [method]
    assert result.search_report["corrective_probes"] is None


def test_autos_frank_wolfe_stage_keeps_the_cap(monkeypatch: Any) -> None:
    import certiqs_key.solvers.search.common as common
    import certiqs_key.solvers.solve as coordinator

    problem, request, clock, _ = _mock_portfolio(monkeypatch, max_iterations=37)
    monkeypatch.setattr(common, "capability_reason", lambda *args: "geometry")
    base = assess_candidate(problem, problem.initial)
    caps: list[int] = []

    def fw(*args: Any, **kwargs: Any) -> Any:
        caps.append(args[5].max_iterations)
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
    assert caps == [37]
    assert result.search_report["max_iterations_caps"] == ["fw"]


def test_an_uncapped_search_needs_a_deadline() -> None:
    from certiqs_key.solvers.search.corrective import search_corrective
    from certiqs_key.solvers.search.factor import search_factor

    problem = _problem()
    with pytest.raises(ValueError, match="needs a deadline"):
        search_factor(problem, settings=FactorSettings(max_iterations=None))
    with pytest.raises(ValueError, match="needs a deadline"):
        search_corrective(problem, settings=CorrectiveSettings(max_iterations=None))


def test_an_uncapped_factor_search_hands_l_bfgs_no_work_cap(
    monkeypatch: Any,
) -> None:
    """Capped: maxiter is the cap and scipy's own maxfun stays; uncapped: neither."""
    import certiqs_key.solvers.search.factor as factor
    from certiqs_key.solvers.search.common import UNCAPPED_NATIVE_WORK

    problem = _problem()
    seen: list[dict[str, Any]] = []
    minimize = factor.minimize

    def spy(*args: Any, **kwargs: Any) -> Any:
        seen.append(dict(kwargs["options"]))
        return minimize(*args, **kwargs)

    monkeypatch.setattr(factor, "minimize", spy)
    capped = factor.search_factor(problem, settings=FactorSettings(max_iterations=3))
    deadline = time.perf_counter() + 600.0
    free = factor.search_factor(
        problem, settings=FactorSettings(max_iterations=None), deadline=deadline
    )
    assert seen[0]["maxiter"] == 3 and "maxfun" not in seen[0]
    assert seen[1]["maxiter"] == seen[1]["maxfun"] == UNCAPPED_NATIVE_WORK
    # Uncapped, the search ends by its own tolerance, well before the deadline.
    assert free.termination == "stagnated"
    assert time.perf_counter() < deadline
    assert capped.termination in ("stagnated", "budget_exhausted")


def test_an_uncapped_corrective_search_ends_by_stagnation() -> None:
    from certiqs_key.solvers.search.corrective import search_corrective

    problem = _problem()
    deadline = time.perf_counter() + 600.0
    outcome = search_corrective(
        problem, settings=CorrectiveSettings(max_iterations=None), deadline=deadline
    )
    assert outcome.termination in ("stagnated", "numerical_failure")
    assert time.perf_counter() < deadline


def test_a_factor_stage_cut_by_its_deadline_resumes_with_the_time_left(
    monkeypatch: Any,
) -> None:
    """The cutoff-4 shape: factor cut while improving, the rest over at once."""
    import certiqs_key.solvers.search.corrective as corrective
    import certiqs_key.solvers.search.entropy as entropy
    import certiqs_key.solvers.search.factor as factor

    problem, request, clock, bracket = _mock_portfolio(monkeypatch)
    starts: list[Any] = []

    def factor_search(*args: Any, **kwargs: Any) -> Any:
        starts.append(args[1])
        clock[0] = kwargs["deadline"]
        bracket[0] += 0.1
        return SearchOutcome(problem.initial, {}, 10.0, "budget_exhausted")

    def failing(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 0.5
        return SearchOutcome(problem.initial, {}, 10.0, "numerical_failure")

    def stagnating(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 0.5
        return SearchOutcome(problem.initial, {}, 10.0, "stagnated")

    monkeypatch.setattr(factor, "search_factor", factor_search)
    monkeypatch.setattr(entropy, "search_entropy", failing)
    monkeypatch.setattr(corrective, "search_corrective", stagnating)
    result = solve_prepared(problem, request)
    report = result.search_report
    allocations = report["resolved_allocations"]
    assert [a["method"] for a in allocations] == [
        "factor", "entropy", "corrective", "corrective", "factor",
    ]
    assert [a["resumed"] for a in allocations] == [False] * 4 + [True]
    resumed = allocations[-1]
    assert resumed["source"] == "best"
    # The resumption takes all the time left, up to the reserve.
    assert resumed["deadline_seconds"] == pytest.approx(99.0)
    assert len(starts) == 2 and starts[0] is problem.anchor
    assert starts[1] is not problem.anchor
    assert report["resume_rule"] is not None
    assert result.search_report["solver_seconds"] <= 100.0 + 1e-9


def test_resumption_reads_cut_progressing_stages_only() -> None:
    from certiqs_key.solvers.solve import _resumptions

    def attempt(method: str, termination: str, before: Any, after: Any,
                **extra: Any) -> dict[str, Any]:
        return {"method": method, "termination": termination,
                "budget_share": {"factor": 0.25, "entropy": 0.5}.get(method, 0.15),
                "assessed_bound_before": before, "assessed_bound_after": after,
                "resumed": False, **extra}

    cut = attempt("factor", "budget_exhausted", -1.0, 0.01)
    flat = attempt("factor", "budget_exhausted", 0.01, 0.01)
    converged = attempt("factor", "stagnated", -1.0, 0.01)
    polish = attempt("entropy", "budget_exhausted", None, 0.02)
    series = attempt("corrective", "budget_exhausted", 0.0, 0.01,
                     stop_reason="stage_deadline", progressed=True)
    # Out of time, but its last probe was flat -- done, not cut.
    done = attempt("corrective", "budget_exhausted", 0.01, 0.01,
                   stop_reason="stage_deadline", progressed=False)
    stalled = attempt("corrective", "stagnated", 0.0, 0.0,
                      stop_reason="no_bracket_progress")
    fw = {"method": "fw", "termination": "budget_exhausted", "budget_share": 0.1}
    assert _resumptions([cut], 100.0, 50.0) == [("factor", "best", 0.25)]
    assert _resumptions([cut], 100.0, 4.0) == []  # under 5 % of the budget
    assert _resumptions([flat, converged, stalled, done, fw], 100.0, 50.0) == []
    assert _resumptions([cut, polish, series], 100.0, 50.0) == [
        ("factor", "best", 0.5),
        ("corrective", "best", 0.15),
    ]
    assert _resumptions([{**cut, "resumed": True}], 100.0, 50.0) == []


def _corrective_only(monkeypatch: Any) -> tuple[Any, Any, list[float], list[float]]:
    import certiqs_key.solvers.search.common as common

    problem, request, clock, bracket = _mock_portfolio(monkeypatch)
    monkeypatch.setattr(
        common,
        "capability_reason",
        lambda problem, method: None if method == "corrective" else "geometry",
    )
    return problem, request, clock, bracket


def test_a_series_flat_when_its_time_ran_out_is_not_resumed(
    monkeypatch: Any,
) -> None:
    """Probes 1-3 progress, later ones are flat up to the deadline."""
    import certiqs_key.solvers.search.corrective as corrective

    problem, request, clock, bracket = _corrective_only(monkeypatch)
    calls = [0]

    def search(*args: Any, **kwargs: Any) -> Any:
        calls[0] += 1
        # Every probe spends its whole slice.
        clock[0] = kwargs["deadline"]
        if calls[0] <= 3:
            bracket[0] += 1.0
        return SearchOutcome(problem.initial, {}, 10.0, "budget_exhausted")

    monkeypatch.setattr(corrective, "search_corrective", search)
    result = solve_prepared(problem, request)
    report = result.search_report
    warm = [a for a in report["attempts"] if a.get("stage") == 2]
    assert [a["progressed"] for a in warm] == [True, True, True, False]
    assert warm[-1]["stop_reason"] == "stage_deadline"
    assert not any(a["resumed"] for a in report["resolved_allocations"])


def test_a_cold_series_is_judged_on_its_own_path(monkeypatch: Any) -> None:
    """Below the warm best, yet improving: the cold series goes on."""
    import certiqs_key.solvers.search.corrective as corrective

    problem, request, clock, bracket = _corrective_only(monkeypatch)
    calls = [0]

    def search(*args: Any, **kwargs: Any) -> Any:
        calls[0] += 1
        clock[0] += 1.0
        # The warm series is two probes (a jump, then flat); the rest is cold.
        if calls[0] <= 2:
            # The warm series jumps to 5 and is then flat.
            bracket[0] = 5.0
        else:
            # The cold series climbs from 1 toward 5, never above it.
            bracket[0] = 1.0 if bracket[0] >= 5.0 else min(4.9, bracket[0] + 0.5)
        return SearchOutcome(problem.initial, {}, 10.0, "budget_exhausted")

    monkeypatch.setattr(corrective, "search_corrective", search)
    result = solve_prepared(problem, request)
    report = result.search_report
    cold = [a for a in report["attempts"] if a.get("stage") == 3]
    assert len(cold) > 2
    assert all(a["progressed"] for a in cold[:-1])
    assert all(a["series_bound_after"] < 5.0 for a in cold)
    assert all(a["assessed_bound_after"] == 5.0 for a in cold)
    assert [a["probe_source"] for a in cold[:2]] == ["cold", "series_best"]
    # The global best decides what is reported.
    assert result.h_lb == 5.0


def test_a_cold_series_that_would_repeat_the_warm_one_is_skipped(
    monkeypatch: Any,
) -> None:
    """Both start at the anchor; the warm series gets the time."""
    import certiqs_key.solvers.solve as coordinator

    problem, request, clock, _ = _corrective_only(monkeypatch)
    monkeypatch.setattr(coordinator, "_same_start", real_same_start)
    assert real_same_start(problem.initial, problem.anchor)
    import certiqs_key.solvers.search.corrective as corrective

    def search(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 1.0
        return SearchOutcome(problem.initial, {}, 10.0, "stagnated")

    monkeypatch.setattr(corrective, "search_corrective", search)
    report = solve_prepared(problem, request).search_report
    (skip,) = [a for a in report["attempts"] if a["termination"] == "skipped"]
    assert skip["source"] == "cold"
    assert skip["reason"] == "cold_start_equals_warm_start"
    (warm,) = report["resolved_allocations"]
    assert warm["source"] == "best"
    assert warm["normalized_remaining_share"] == 1.0


def test_no_cold_series_once_the_bracket_is_closed_to_tau(monkeypatch: Any) -> None:
    import certiqs_key.solvers.search.corrective as corrective

    problem, request, clock, bracket = _corrective_only(monkeypatch)

    def search(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 1.0
        # The estimate is 10; this leaves a relative bracket of 1e-4.
        bracket[0] = 10.0 * (1 - 1e-4)
        return SearchOutcome(problem.initial, {}, 10.0, "stagnated")

    monkeypatch.setattr(corrective, "search_corrective", search)
    report = solve_prepared(problem, request).search_report
    (skip,) = [a for a in report["attempts"] if a["termination"] == "skipped"]
    assert skip["reason"] == "bracket_closed_to_cold_tau"
    assert skip["tau"] == CORRECTIVE_COLD_TAU == 5e-4
    assert skip["relative_bracket"] == pytest.approx(1e-4)
    assert report["corrective_probes"]["cold_tau"] == CORRECTIVE_COLD_TAU


def test_a_support_refusal_moves_the_series_to_the_fallback_blend(
    monkeypatch: Any,
) -> None:
    """The refused probe ends alone; the series goes on at 1e-6, once."""
    import certiqs_key.solvers.search.corrective as corrective
    from certiqs_key.solvers.search.common import SUPPORT_FALLBACK_BLEND

    problem, request, clock, _ = _corrective_only(monkeypatch)
    blends: list[float] = []

    def search(*args: Any, **kwargs: Any) -> Any:
        blends.append(kwargs["settings"].blend)
        clock[0] += 1.0
        return SearchOutcome(
            problem.initial,
            {},
            10.0,
            "numerical_failure",
            diagnostics={"support_refusal": True},
        )

    monkeypatch.setattr(corrective, "search_corrective", search)
    report = solve_prepared(problem, request).search_report
    warm = [a for a in report["attempts"] if a.get("stage") == 2]
    assert blends[:2] == [1e-10, SUPPORT_FALLBACK_BLEND]
    assert [a["blend"] for a in warm] == [1e-10, SUPPORT_FALLBACK_BLEND]
    assert warm[0]["support_refusal"] and warm[0]["continued"]
    assert warm[0]["blend_raised_to"] == SUPPORT_FALLBACK_BLEND
    # Refused again at the fallback: the series ends.
    assert warm[1]["stop_reason"] == "search_numerical_failure"
    assert warm[1]["blend_raised_to"] is None
    # The next series starts at the default again.
    cold = [a for a in report["attempts"] if a.get("stage") == 3]
    assert cold[0]["blend"] == 1e-10


def test_the_corrective_search_names_a_support_refusal(monkeypatch: Any) -> None:
    import certiqs_key.solvers.search.corrective as corrective
    from certiqs_key.meat_core.errors import GradientHypothesisError

    problem = _problem()
    for reason, named in (
        ("gradient_hypothesis_support", True),
        ("gradient_hypothesis_positivity", False),
    ):

        def refuse(*args: Any, reason: str = reason, **kwargs: Any) -> Any:
            raise GradientHypothesisError("hypothesis refused", reason=reason)

        monkeypatch.setattr(corrective.stable, "evaluate", refuse)
        outcome = corrective.search_corrective(
            problem, settings=CorrectiveSettings(max_iterations=1)
        )
        assert outcome.termination == "numerical_failure"
        assert outcome.diagnostics["support_refusal"] is named
