"""The outer alpha search (certiqs_key.runs.alpha_search) on synthetic evaluators.

The search is pure over its evaluator, so these tests drive it with scores of
known shape. The run-tier adapter is exercised on a real instance by
tests/integration/test_runs_alpha_search_bbm92.py.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable

import pytest

from certiqs_key.runs.alpha_search import (
    AlphaPoint,
    AlphaSearchError,
    AlphaSearchSettings,
    search_alpha,
    unclamped_length,
)

REFUSED = "solve: negative_objective"


def _peaked(
    at: float, calls: list[float], top: float = 1e6
) -> Callable[[float], AlphaPoint]:
    """Return a score concave in log(alpha - 1), maximal at ``alpha - 1 = at``."""

    def evaluate(alpha: float) -> AlphaPoint:
        calls.append(alpha)
        t = math.log(alpha - 1.0) - math.log(at)
        score = top - 1e5 * t * t
        return AlphaPoint(score=score, key_length=max(0, int(score)), h_lb=0.4)

    return evaluate


def test_finds_the_peak_within_the_refinement_resolution() -> None:
    calls: list[float] = []
    result = search_alpha(_peaked(3e-3, calls))
    assert result.alpha is not None
    assert abs(math.log((result.alpha - 1.0) / 3e-3)) < 1.0
    settings = AlphaSearchSettings()
    assert len(calls) == settings.coarse_points + settings.refine_steps


def test_each_alpha_is_evaluated_once() -> None:
    calls: list[float] = []
    search_alpha(_peaked(3e-3, calls), AlphaSearchSettings(refine_steps=8))
    assert len(calls) == len(set(calls))


def test_a_peak_at_the_grid_end_stays_inside_the_interval() -> None:
    calls: list[float] = []
    settings = AlphaSearchSettings()
    # At the lower end, alpha - 1 = 1e-5, (ln 100)^2 = 21.2: the score is
    # 1e7 - 2.12e6 > 0, a positive key length, so an alpha is chosen.
    result = search_alpha(_peaked(1e-7, calls, top=1e7), settings)
    assert result.alpha is not None
    lo, hi = settings.lower * (1 - 1e-9), settings.upper * (1 + 1e-9)
    assert all(lo <= a - 1.0 <= hi for a in calls)
    assert result.alpha == pytest.approx(1.0 + settings.lower, rel=1e-9)


def test_refused_points_never_win_and_all_refused_chooses_none() -> None:
    def refuse_small(alpha: float) -> AlphaPoint:
        if alpha < 1.01:
            return AlphaPoint(score=-math.inf, key_length=None, reason=REFUSED)
        return AlphaPoint(score=-alpha, key_length=0, h_lb=-0.1)

    # Every evaluation that formed a bound has key length 0: no alpha is
    # chosen (test_runs_alpha_search_no_key.py), and with no h_low the run
    # reported is the highest score, -alpha, the smallest alpha not refused.
    result = search_alpha(refuse_small)
    assert result.chosen is None and result.alpha is None
    reported = result.no_positive_key
    assert reported is not None and not reported.point.refused
    assert reported.alpha >= 1.01
    assert reported.alpha == min(
        e.alpha for e in result.evaluations if not e.point.refused
    )

    def refuse_all(alpha: float) -> AlphaPoint:
        return AlphaPoint(score=-math.inf, key_length=None, reason=REFUSED)

    none = search_alpha(refuse_all)
    assert none.chosen is None and none.alpha is None
    assert len(none.evaluations) == AlphaSearchSettings().coarse_points
    payload = none.as_payload()
    json.dumps(payload)
    assert payload["chosen_alpha"] is None
    assert all(e["score"] is None for e in payload["evaluations"])


def test_payload_records_every_evaluation_in_order() -> None:
    calls: list[float] = []
    result = search_alpha(_peaked(3e-3, calls))
    payload = result.as_payload()
    json.dumps(payload)
    assert payload["searched"] is True
    assert [e["alpha"] for e in payload["evaluations"]] == calls
    assert {e["phase"] for e in payload["evaluations"]} == {"coarse", "refine"}


@pytest.mark.parametrize(
    "settings",
    [
        {"lower": 0.0},
        {"lower": 0.1, "upper": 0.05},
        {"upper": 1.0},
        {"coarse_points": 1},
        {"refine_steps": -1},
        {"lower": math.nan},
    ],
)
def test_settings_that_are_not_ones_are_refused(settings: dict[str, float]) -> None:
    with pytest.raises(AlphaSearchError):
        AlphaSearchSettings(**settings)  # type: ignore[arg-type]


def test_unclamped_length_reproduces_a_recorded_key_length() -> None:
    # bbm92 ideal device, n = 1e8, alpha = 1.003, method auto, at a development commit:
    # key_length 43,718,559 from h_lb 0.4372861848869387.
    value = unclamped_length(
        rounds=100_000_000,
        h_lb=0.4372861848869387,
        alpha=1.003,
        eps_pa=2.0**-30,
        eps_ev=2.0**-30,
        lambda_ec=0,
    )
    assert math.floor(value) == 43_718_559
