"""The alpha search sets aside an evaluation whose bracket stayed wide.

At cutoff 3 of the BBM92 study the golden-section step would take two solves
that had stopped with a bracket 2-3 times their value as real values and move
away from the good alpha. Held here (certiqs_key.runs.alpha_search, "AN
EVALUATION WHOSE BRACKET STAYED WIDE"):

* an evaluation whose relative gap exceeds both a floor (1e-3, or the run's
  gap target over its h_low where larger) and ten times the median of the
  other evaluations' is set aside, and the record says so -- also through
  the record's attached copy of the search;
* its certified score is a lower bound, so it is read as one:
  it centres the refinement where it is the best coarse score, takes part
  in a golden-section comparison it wins, and a comparison it would lose
  stops the refinement (recorded);
* where every evaluation is equally open, or a gap is below the floor,
  nothing is set aside and the search runs as before;
* a set-aside evaluation's key length, certified, stays eligible for the
  choice.

Synthetic evaluators, as in tests/unit/test_runs_alpha_search.py.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

import certiqs_key.runs as runs_package
from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.alpha_search import (
    SET_ASIDE_RULE,
    WIDE_FACTOR,
    WIDE_RELATIVE_GAP,
    AlphaPoint,
    AlphaSearchResult,
    AlphaSearchSettings,
    _without_runs,
    search_alpha,
)
from certiqs_key.runs.config import RunConfig

H = 0.024


def _evaluator(
    calls: list[float],
    *,
    wide: Callable[[float], bool] = lambda alpha: False,
    gap: float = 1e-4,
    peak: float = 7e-3,
    wide_score: float = -8e5,
) -> Callable[[float], AlphaPoint]:
    """Return a key peaked at ``alpha - 1 = peak``; ``wide`` alphas lose h_lb.

    A wide evaluation's h_lb drops by three times its value, as at cutoff 3
    (h_lb -0.051 against h_low 0.024); its certified score is ``wide_score``,
    by default far below its neighbours'.
    """

    def evaluate(alpha: float) -> AlphaPoint:
        calls.append(alpha)
        t = math.log(alpha - 1.0) - math.log(peak)
        key = 3.4e5 - 1e4 * t * t
        h_low = H
        if wide(alpha):
            h_lb = H - 3 * H
            return AlphaPoint(
                score=wide_score,
                key_length=max(0, int(wide_score)),
                h_lb=h_lb,
                h_low=h_low,
                reason="ok",
            )
        return AlphaPoint(
            score=key,
            key_length=int(key),
            h_lb=h_low * (1 - gap),
            h_low=h_low,
            reason="ok",
        )

    return evaluate


def _near(alpha: float, target: float) -> bool:
    return abs(alpha - target) <= 1e-9 * target


def _refinement_points(settings: AlphaSearchSettings) -> list[float]:
    """Return the alphas the refinement evaluates with no evaluation wide."""
    calls: list[float] = []
    search_alpha(_evaluator(calls), settings)
    return calls[settings.coarse_points :]


def test_a_wide_evaluation_that_would_lose_stops_the_refinement() -> None:
    """The first golden point is wide and loses to the second: stop there."""
    settings = AlphaSearchSettings()
    grid = settings.coarse_grid()
    c = _refinement_points(settings)[0]
    calls: list[float] = []
    result = search_alpha(_evaluator(calls, wide=lambda a: _near(a, c)), settings)
    # Both golden points are evaluated; the comparison is not made.
    assert len(calls) == len(grid) + 2
    wide = result.evaluations[len(grid)]
    assert wide.phase == "refine" and _near(wide.alpha, c)
    assert wide.point.set_aside is not None
    assert wide.point.set_aside.startswith("wide_bracket: relative gap 3")
    assert result.refinement_stopped is not None
    assert repr(wide.alpha) in result.refinement_stopped
    assert [e.point.set_aside is None for e in result.evaluations] == [
        True
    ] * len(grid) + [False, True]
    assert result.chosen is not None and result.chosen is not wide


def test_a_wide_second_golden_point_that_would_lose_stops_the_refinement() -> None:
    settings = AlphaSearchSettings()
    grid = settings.coarse_grid()
    d = _refinement_points(settings)[1]
    calls: list[float] = []
    result = search_alpha(_evaluator(calls, wide=lambda a: _near(a, d)), settings)
    assert len(calls) == len(grid) + 2
    assert result.evaluations[-1].point.set_aside is not None
    assert result.refinement_stopped is not None
    assert repr(result.evaluations[-1].alpha) in result.refinement_stopped


def test_a_wide_golden_point_that_wins_takes_part() -> None:
    """Its score is a lower bound: winning on it is valid evidence."""
    settings = AlphaSearchSettings()
    grid = settings.coarse_grid()
    plain = _refinement_points(settings)
    c = plain[0]
    calls: list[float] = []
    result = search_alpha(
        _evaluator(calls, wide=lambda a: _near(a, c), wide_score=4e5), settings
    )
    assert len(calls) == len(grid) + settings.refine_steps
    assert result.evaluations[len(grid)].point.set_aside is not None
    assert result.refinement_stopped is None
    # It won against the second golden point, so the next point lies on its
    # side of the bracket, below c (the plain search goes the other way).
    assert calls[len(grid) + 2] < c
    assert plain[2] > c
    assert result.chosen is not None and _near(result.chosen.alpha, c)


def _coarse_search(top_score: float) -> tuple[list[float], AlphaSearchResult]:
    """Return a search whose grid point 2 is wide, with ``top_score``."""
    settings = AlphaSearchSettings()
    grid = settings.coarse_grid()
    wide = grid[2]

    def evaluate(alpha: float) -> AlphaPoint:
        t = math.log(alpha - 1.0) - math.log(grid[4] - 1.0)
        key = 3.4e5 - 1e4 * t * t
        if _near(alpha, wide):
            return AlphaPoint(
                score=top_score,
                key_length=max(0, int(top_score)),
                h_lb=0.5 * H,
                h_low=H,
                reason="ok",
            )
        return AlphaPoint(
            score=key, key_length=int(key), h_lb=H * (1 - 1e-5), h_low=H, reason="ok"
        )

    return grid, search_alpha(evaluate, settings)


def test_a_wide_coarse_point_that_wins_centres_the_refinement() -> None:
    grid, result = _coarse_search(4e5)
    coarse = result.evaluations[: len(grid)]
    assert [e.point.set_aside is not None for e in coarse] == [
        False, False, True, False, False, False,
    ]
    refine = result.evaluations[len(grid) :]
    assert refine
    lo, hi = grid[1] - 1.0, grid[3] - 1.0
    assert all(lo <= e.alpha - 1.0 <= hi for e in refine)
    assert result.chosen is not None and _near(result.chosen.alpha, grid[2])


def test_a_wide_coarse_point_that_loses_does_not_centre_the_refinement() -> None:
    grid, result = _coarse_search(-8e5)
    coarse = result.evaluations[: len(grid)]
    assert coarse[2].point.set_aside is not None
    refine = result.evaluations[len(grid) :]
    assert len(refine) == AlphaSearchSettings().refine_steps
    lo, hi = grid[3] - 1.0, grid[5] - 1.0
    assert all(lo <= e.alpha - 1.0 <= hi for e in refine)
    assert result.refinement_stopped is None


def test_the_gap_target_raises_the_floor() -> None:
    """A solve asked only to close to its gap target is not wide for that."""
    settings = AlphaSearchSettings()
    special = settings.coarse_grid()[0]

    def evaluate_with(target: float | None) -> Callable[[float], AlphaPoint]:
        def evaluate(alpha: float) -> AlphaPoint:
            point = _evaluator([])(alpha)
            gap = 0.02 if _near(alpha, special) else 1e-4
            return AlphaPoint(
                score=point.score,
                key_length=point.key_length,
                h_lb=H * (1 - gap),
                h_low=H,
                reason="ok",
                gap_target=target,
            )

        return evaluate

    without = search_alpha(evaluate_with(None), settings)
    assert without.evaluations[0].point.set_aside is not None
    # 1e-3 / 0.024 = 0.042, above the 0.02 relative gap.
    loose = search_alpha(evaluate_with(1e-3), settings)
    assert loose.evaluations[0].point.set_aside is None
    tight = search_alpha(evaluate_with(1e-6), settings)
    assert tight.evaluations[0].point.set_aside is not None


def test_the_attached_search_keeps_why_the_refinement_stopped() -> None:
    """The record's copy of the search keeps refinement_stopped."""
    settings = AlphaSearchSettings()
    c = _refinement_points(settings)[0]
    result = search_alpha(_evaluator([], wide=lambda a: _near(a, c)), settings)
    assert result.refinement_stopped is not None
    stripped = _without_runs(result)
    assert stripped.refinement_stopped == result.refinement_stopped
    payload = stripped.as_payload()
    assert payload["refinement_stopped"] == result.refinement_stopped
    assert payload == result.as_payload()


@pytest.mark.parametrize(
    "gap", [0.05, 5e-4], ids=["every-evaluation-equally-open", "below-the-floor"]
)
def test_no_evaluation_is_set_aside_without_an_outlier_above_the_floor(
    gap: float,
) -> None:
    settings = AlphaSearchSettings()
    calls: list[float] = []
    # gap 0.05: all equally open; gap 5e-4 everywhere but one at 9e-4 (ten
    # times, but under the 1e-3 floor).
    special = settings.coarse_grid()[3]

    def evaluate(alpha: float) -> AlphaPoint:
        point = _evaluator(calls, gap=gap)(alpha)
        if gap < WIDE_RELATIVE_GAP and _near(alpha, special):
            return AlphaPoint(
                score=point.score,
                key_length=point.key_length,
                h_lb=H * (1 - 9e-4),
                h_low=H,
                reason="ok",
            )
        return point

    result = search_alpha(evaluate, settings)
    assert all(e.point.set_aside is None for e in result.evaluations)
    assert result.refinement_stopped is None
    assert len(calls) == settings.coarse_points + settings.refine_steps


def test_refused_and_gapless_evaluations_are_never_set_aside() -> None:
    def evaluate(alpha: float) -> AlphaPoint:
        if alpha < 1.0 + 1e-4:
            return AlphaPoint(score=-math.inf, key_length=None, reason="refused")
        if alpha > 1.1:
            return AlphaPoint(
                score=1.0, key_length=1, h_lb=0.0, h_low=math.inf, reason="ok"
            )
        return AlphaPoint(
            score=alpha, key_length=10, h_lb=H * (1 - 1e-5), h_low=H, reason="ok"
        )

    result = search_alpha(evaluate)
    assert all(e.point.set_aside is None for e in result.evaluations)
    payload = result.as_payload()
    json.dumps(payload, allow_nan=False)
    first, last_coarse = payload["evaluations"][0], payload["evaluations"][5]
    assert first["relative_gap"] is None and first["h_low"] is None
    assert last_coarse["h_low"] is None and last_coarse["relative_gap"] is None


def test_the_record_names_the_set_aside_evaluation_and_the_rule() -> None:
    settings = AlphaSearchSettings()
    first: list[float] = []
    search_alpha(_evaluator(first), settings)
    c = first[settings.coarse_points]
    result = search_alpha(_evaluator([], wide=lambda a: _near(a, c)), settings)
    payload = result.as_payload()
    json.dumps(payload, allow_nan=False)
    assert payload["set_aside_rule"] == SET_ASIDE_RULE
    assert f"{WIDE_RELATIVE_GAP:g}" in SET_ASIDE_RULE
    assert f"{WIDE_FACTOR:g} times" in SET_ASIDE_RULE
    assert payload["refinement_stopped"] == result.refinement_stopped
    index = settings.coarse_points
    wide = payload["evaluations"][index]
    assert wide["set_aside"] is not None
    assert wide["relative_gap"] == pytest.approx(3.0)
    assert wide["h_low"] == H
    others = payload["evaluations"][:index] + payload["evaluations"][index + 1 :]
    assert all(e["set_aside"] is None for e in others)
    jsonschema = pytest.importorskip("jsonschema")
    path = Path(runs_package.__file__).resolve().parent / "record.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.validate(
        payload, {"$defs": schema["$defs"], "$ref": "#/$defs/alpha_search"}
    )


def test_the_cutoff_three_search_no_longer_moves_on_its_failed_evaluations() -> None:
    """The committed N = 3 search, replayed (routes/encoded-N3/record.json.gz).

    Its evaluations' h_lb and key lengths as recorded, with the converged
    relative gap of its chosen run (6.4e-6 / 0.0244, about 2.6e-4) where the
    record keeps no h_low. Alphas 1.0027 and 1.00702 were the failed solves.
    Without the guard the refinement would go on to 1.0015, 1.0010 and 1.0019
    and keep 1.00435; with it, it stops at the first comparison a failed one
    would lose (1.00702 against 1.0027, both set aside).
    """
    recorded = {
        1.00001: (0.0216126990, 0),
        1.0000757858283: (0.0240996057, 0),
        1.00057434917749: (0.0244671505, 299363),
        1.00435275281648: (0.0243486264, 342807),
        1.03298769776098: (0.0135579963, 176140),
        1.25: (0.0074902268, 79845),
        1.00269771682: (-0.0312018553, 0),
        1.00702112275: (-0.0506620120, 0),
    }
    honest = {1.00001: 0.0245, 1.03298769776098: 0.02245, 1.25: 0.01046}
    calls: list[float] = []

    def evaluate(alpha: float) -> AlphaPoint:
        calls.append(alpha)
        key = min(recorded, key=lambda a: abs(a - alpha))
        assert abs(key - alpha) < 1e-6, alpha
        h_lb, length = recorded[key]
        h_low = honest.get(key, 0.02424 if h_lb < 0 else h_lb * (1 + 2.6e-4))
        score = float(length) if length > 0 else -1e5 - 1e7 * max(0.0, -h_lb)
        return AlphaPoint(
            score=score, key_length=length, h_lb=h_lb, h_low=h_low, reason="ok"
        )

    result = search_alpha(evaluate, AlphaSearchSettings())
    assert len(calls) == 8
    assert result.evaluations[-1].point.set_aside is not None
    assert result.evaluations[-2].point.set_aside is not None
    assert result.refinement_stopped is not None
    assert "1.00702112275" in result.refinement_stopped
    assert result.refinement_stopped is not None
    assert result.chosen is not None
    assert result.chosen.alpha == pytest.approx(1.00435275281648)


def test_the_gap_reads_one_declaration() -> None:
    """The reference companion's h_lb does not enter the convergence gap.

    Licensed route, cutoff 1 (r4 probe): reported h_lb 0.0241700 on the
    reference declaration, snapped bound 0.0242169, h_low 0.0242179 on the
    snapped copy. The mixed pair reads a relative gap of 2e-3, above the
    floor; the searched declaration's own pair reads 4e-5.
    """
    from certiqs_key.runs.alpha_search import _searched_bound

    counted = {"counted": True, "snapped": {"h_lb": 0.0242169, "key_length": 1}}
    assert _searched_bound(counted) == 0.0242169
    assert _searched_bound({**counted, "counted": False}) is None
    assert _searched_bound(None) is None
    mixed = AlphaPoint(
        score=1.0, key_length=1, h_lb=0.0241700, h_low=0.0242179, reason="ok"
    )
    own = replace(mixed, h_lb_searched=_searched_bound(counted))
    assert mixed.relative_gap is not None and mixed.relative_gap > WIDE_RELATIVE_GAP
    assert own.relative_gap == pytest.approx((0.0242179 - 0.0242169) / 0.0242179)
    assert own.relative_gap < WIDE_RELATIVE_GAP


def test_a_counted_reference_without_a_snapped_bound_judges_no_gap() -> None:
    """No bound on the searched declaration: no gap, never the mixed pair."""
    from certiqs_key.runs.alpha_search import _searched_bound

    bound = _searched_bound({"counted": True, "snapped": {"h_lb": None}})
    assert bound is not None and math.isnan(bound)
    point = AlphaPoint(
        score=1.0, key_length=1, h_lb=0.0241700, h_low=0.0242179, reason="ok",
        h_lb_searched=bound,
    )
    assert point.relative_gap is None


def test_a_counted_record_judges_the_snapped_gap_scores_the_reported() -> None:
    """The wiring: _point scores the reported bound and judges the snapped gap."""
    from certiqs_key.runs.alpha_search import _point

    key_rate = {
        "key_length": 0,
        "h_lb": 0.0241700,
        "h_low": 0.0242179,
        "key_length_reason_code": "first_order_reported",
        "reference_bracket": {
            "counted": True,
            "snapped": {"h_lb": 0.0242169, "key_length": 0},
        },
    }
    point_config = RunConfig(
        rounds=10_000,
        completeness_budget=Fraction(1, 1_000_000),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=7
        ),
        declared_tolerance=1e-12,
    )
    point = _point(key_rate, point_config, run=None)
    assert point.h_lb == 0.0241700
    assert point.h_lb_searched == 0.0242169
    assert point.relative_gap is not None
    assert point.relative_gap < WIDE_RELATIVE_GAP
    uncounted = _point(
        {
            **key_rate,
            "reference_bracket": {
                **key_rate["reference_bracket"],
                "counted": False,
            },
        },
        point_config,
        run=None,
    )
    assert uncounted.h_lb_searched is None
    assert point.score == uncounted.score
