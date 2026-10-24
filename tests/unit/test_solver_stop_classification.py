"""The stop cause a candidate search records, read against its value.

``solvers/solve.py`` (``classify_termination``, ``CONVERGED_RELATIVE_GAP``):
a search whose last stage stopped on its own no-progress rule reads
``relative_gap_met`` instead of ``stagnated`` where its bracket closed to
1e-3 of ``h_low``. A label only; the absolute gap target still decides when
the search stops. The numbers are hand-written: bbm92 at a key-round mass
of about 1.8e-6 per round has h_low = 1.082e-6,
where the absolute target 1e-10 is about 1e-4 of the value.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from tests.unit.test_candidate_boundary import _mock_portfolio

from certiqs_key.runs.report.explain import solve_stop
from certiqs_key.solvers.assessment import assess_candidate
from certiqs_key.solvers.search.common import SearchOutcome
from certiqs_key.solvers.solve import (
    CONVERGED_RELATIVE_GAP,
    _open_relative,
    classify_termination,
    solve_prepared,
)


def _bracket(h_low: float, h_lb: float) -> float | None:
    """Return the solve's relative bracket for an estimate and a bound."""
    estimate = SimpleNamespace(objective=h_low)
    best = SimpleNamespace(gate=SimpleNamespace(linearization=h_lb))
    return _open_relative(best, estimate)  # type: ignore[arg-type]


def test_the_level_is_a_tenth_of_a_percent() -> None:
    assert CONVERGED_RELATIVE_GAP == 1e-3


def test_a_small_value_whose_bracket_closed_reads_converged() -> None:
    # h_low - h_lb = 8e-10, above the absolute target 1e-10, but
    # 8e-10 / 1.082e-6 = 7.39e-4 of the value.
    relative = _bracket(1.082e-6, 1.0812e-6)
    assert relative == pytest.approx(7.3937e-4, rel=1e-4)
    assert classify_termination("stagnated", relative) == "relative_gap_met"


def test_a_small_value_whose_bracket_stayed_open_reads_stagnated() -> None:
    # 1.082e-6 against 1.0766e-6 (probe P1's bound on the searched
    # declaration): 5.4e-9 / 1.082e-6 = 4.99e-3, above 1e-3.
    relative = _bracket(1.082e-6, 1.0766e-6)
    assert relative == pytest.approx(4.9908e-3, rel=1e-4)
    assert classify_termination("stagnated", relative) == "stagnated"


def test_an_ordinary_value_reads_as_before() -> None:
    # h_low 0.25 against h_lb 0.249: 4e-3 of the value, stagnated as before.
    assert classify_termination("stagnated", _bracket(0.25, 0.249)) == "stagnated"
    # Every other stop cause is kept, however closed the bracket.
    closed = _bracket(0.25, 0.25 - 1e-11)
    for termination in (
        "target_met",
        "budget_exhausted",
        "numerical_failure",
        "oracle_failure",
        "unsupported",
    ):
        assert classify_termination(termination, closed) == termination
    # No bracket formed: nothing to read.
    assert classify_termination("stagnated", None) == "stagnated"
    assert _bracket(0.0, -1e-3) is None
    # An infinite estimate has no relative bracket (JSON has no NaN).
    assert _bracket(float("inf"), 0.1) is None


def test_the_level_itself_counts_as_converged() -> None:
    assert classify_termination("stagnated", 1e-3) == "relative_gap_met"
    assert classify_termination("stagnated", 1.0000001e-3) == "stagnated"


def test_the_report_says_the_search_converged_relative_to_its_value() -> None:
    report = {
        "termination": "relative_gap_met",
        "gap_target": 1e-10,
        "converged_relative_gap": 1e-3,
        "attempts": [],
    }
    # The search's own bracket (on the searched declaration) is 7.39e-4; the
    # reported h_lb is the reference companion's, -2.61e-6 (probe P1), so the
    # reported bracket is (1.082e-6 + 2.61e-6) / 1.082e-6 = 3.41.
    report["relative_gap"] = 7.3937e-4
    text = solve_stop(report, {"h_low": 1.082e-6, "h_lb": -2.61e-6})
    assert text is not None
    assert "The search did not meet its gap target (1e-10)." in text
    assert (
        "It converged all the same: its last stage stopped making progress with "
        "the search's own bracket, on the declaration it searched, closed to a "
        "relative gap of 0.000739, within 0.001 of the value it brackets"
    ) in text
    assert (
        "The reported bracket (h_low against the h_lb the run reports) closed "
        "to a relative gap of 3.41 ((h_low - h_lb) / |h_low|)."
    ) in text
    assert "The record's termination field reads relative_gap_met." in text
    # Any other termination keeps the plain wording.
    plain = solve_stop(
        {**report, "termination": "stagnated"}, {"h_low": 0.5, "h_lb": 0.4}
    )
    assert plain is not None
    assert "Its bracket closed to a relative gap of 0.2" in plain
    assert "reported bracket" not in plain and "converged" not in plain


def test_the_portfolio_records_relative_gap_met(monkeypatch: Any) -> None:
    """solve_prepared relabels a final stagnated, and records why.

    Every stage is stubbed to end stagnated, and every assessment has the
    estimate 1.082e-6 and the bracket 1.0812e-6: the gap 8e-10 misses the
    absolute target 1e-10, the relative bracket 8e-10 / 1.082e-6 = 7.39e-4
    is within 1e-3.
    """
    result = _stagnating_portfolio(monkeypatch, bracket=1.0812e-6)
    report = result.search_report
    assert result.status == report["termination"] == "relative_gap_met"
    assert report["relative_gap"] == pytest.approx(7.3937e-4, rel=1e-4)
    assert report["converged_relative_gap"] == CONVERGED_RELATIVE_GAP
    # Every stage's own termination is untouched.
    assert {a["termination"] for a in report["attempts"] if "settings" in a} == {
        "stagnated"
    }


def test_the_portfolio_keeps_stagnated_where_the_bracket_stayed_open(
    monkeypatch: Any,
) -> None:
    # 1.0766e-6 (probe P1's bound on the searched declaration): 4.99e-3.
    result = _stagnating_portfolio(monkeypatch, bracket=1.0766e-6)
    report = result.search_report
    assert result.status == report["termination"] == "stagnated"
    assert report["relative_gap"] == pytest.approx(4.9908e-3, rel=1e-4)


def _stagnating_portfolio(monkeypatch: Any, *, bracket: float) -> Any:
    import certiqs_key.solvers.search.corrective as corrective
    import certiqs_key.solvers.search.entropy as entropy
    import certiqs_key.solvers.search.factor as factor
    import certiqs_key.solvers.solve as coordinator

    problem, request, clock, _ = _mock_portfolio(monkeypatch)
    template = assess_candidate(problem, problem.initial)
    h_low = 1.082e-6

    def assess(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 1.0
        return replace(
            template,
            gate=replace(template.gate, objective=h_low, linearization=bracket),
            gap=h_low - bracket,
        )

    def search(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 1.0
        return SearchOutcome(problem.initial, {}, h_low, "stagnated")

    monkeypatch.setattr(coordinator, "assess_candidate", assess)
    for module, name in (
        (factor, "search_factor"),
        (entropy, "search_entropy"),
        (corrective, "search_corrective"),
    ):
        monkeypatch.setattr(module, name, search)
    assert request.gap_target == 1e-10
    return solve_prepared(problem, request)
