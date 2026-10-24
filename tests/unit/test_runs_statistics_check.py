"""The run tier's part of the check of the acceptance set against the statistics.

WHY THIS EXISTS. ``meat-core/req:unreachable-acceptance-set`` asks for one
solve per run, before any order is evaluated, and one decision on the cap
``2^(-x)`` with it: a run whose cap is at most ``tau`` is refused as a whole
and evaluated at no order (item (iv)); every order a run evaluates records its
diagnostic ``n f`` (item (v)). A search whose evaluations each solved again,
that went on evaluating after the cap refused the run, or whose refusal read
anything but the cap would each break the requirement. What is held here,
without a solver:

* the run's check solves once and refuses to reuse its bound for another
  declaration or acceptance set, and keeps a bound not formed too;
* the outer search on a fake run that refuses as
  :func:`~certiqs_key.runs.pipeline.run_slice` does: refused at the evaluation
  that formed the bound, the search stopping there, or completed with every
  evaluated order noted;
* which rule of item (i) fixed ``alpha_0``.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.meat_core.finitekey.consistency import (
    Alpha0Rule,
    DivergenceBound,
    NoBoundReason,
)
from certiqs_key.runs.alpha_search import UNREACHABLE_EVALUATION_REASON, run_searched
from certiqs_key.runs.config import AlphaSearchSettings, RunConfig
from certiqs_key.runs.pipeline import SliceRefusal, SliceResult, SliceStage
from certiqs_key.runs.statistics_check import (
    UNREACHABLE_REASON,
    RunCheck,
    honest_supplied_from_note,
    refusal_detail,
    run_check,
)

#: Every evaluation's key length (bits), and the run's n and tau.
KEY, N, TAU = 1_000_000, 1000, F(1, 2)
#: alpha_0 of the search below: 1 + lower, lower = 1e-5 (the default domain).
ALPHA_0 = 1.0 + 1e-5


def test_a_supplied_law_is_read_off_the_note_where_the_caller_does_not_say() -> None:
    assert honest_supplied_from_note({"overridden": True})
    assert honest_supplied_from_note({"supplied": True})
    assert not honest_supplied_from_note({"overridden": False})
    assert not honest_supplied_from_note(None)


# ===========================================================================
#  Items (i), (ii), (iv): one solve and one decision per run
# ===========================================================================


def _solved(b: F, calls: list[float]) -> Any:
    def solve(alpha_0: float) -> DivergenceBound:
        calls.append(alpha_0)
        return DivergenceBound(alpha_0=alpha_0, bound=b, tier="certified", estimate=1.0)

    return solve


def _begin(check: RunCheck, alpha: float, tau: F = TAU, rounds: int = 10) -> None:
    check.begin(
        honest_supplied=True, caller_constraint_entries=0, option="on",
        tau=tau, rounds=rounds, alpha=alpha,
    )


def test_the_bound_is_formed_once_and_only_for_its_declaration() -> None:
    check = RunCheck()
    _begin(check, 1.5)
    calls: list[float] = []
    first = check.ensure_bound(("decl", "acc"), _solved(F(1), calls))
    again = check.ensure_bound(("decl", "acc"), _solved(F(2), calls))
    assert first is again and calls == [1.5]
    with pytest.raises(RuntimeError, match="another declaration"):
        check.ensure_bound(("other", "acc"), _solved(F(1), calls))


def test_the_cap_is_decided_with_the_bound() -> None:
    """With n = 10, alpha_0 = 3/2, b = 3/10: x = 10 * (1/3) * (3/10) = 1 >= 1, refused.

    With b = 3/20 instead, x = 1/2 < 1 and nothing is refused.
    """
    check = RunCheck()
    _begin(check, 1.5)
    check.ensure_bound(("decl", "acc"), _solved(F(3, 10), []))
    assert check.cap is not None and check.cap.exponent == 1 and check.refused
    record = check.record()
    assert record is not None and record.refused
    detail = refusal_detail(check.cap, check.bound)  # type: ignore[arg-type]
    assert "min_model_pass_probability = 1/2" in detail
    assert "evaluated at no order" in detail
    kept = RunCheck()
    _begin(kept, 1.5)
    kept.ensure_bound(("decl", "acc"), _solved(F(3, 20), []))
    assert kept.cap is not None and kept.cap.exponent == F(1, 2)
    assert not kept.refused


def test_a_bound_not_formed_is_kept_too_and_not_solved_again() -> None:
    """Item (ii): the reason no bound was formed is the run's outcome, once.

    A search reads it at every order; solving again at each would repeat a
    solve whose outcome is already recorded. There is no cap, and nothing is
    refused.
    """
    check = RunCheck(alpha_0=ALPHA_0, searched=True)
    calls: list[float] = []

    def not_formed(alpha_0: float) -> DivergenceBound:
        calls.append(alpha_0)
        return DivergenceBound(
            alpha_0=alpha_0,
            bound=None,
            tier=None,
            no_bound_reason=NoBoundReason.SOLVE_NOT_COMPLETED,
            estimate=-1e-15,
        )

    for alpha in (1.001, 1.1, 1.5):
        _begin(check, alpha)
        outcome = check.ensure_bound(("decl", "acc"), not_formed)
        assert outcome.no_bound_reason is NoBoundReason.SOLVE_NOT_COMPLETED
        assert check.cap is None and not check.refused
        check.note_order(alpha)
    assert calls == [ALPHA_0]
    record = check.record()
    assert record is not None
    assert [o.proven_part for o in record.orders] == [None, None, None]


def test_one_runs_evaluations_must_agree_on_the_scope() -> None:
    check = RunCheck(alpha_0=1.0001, searched=True)
    _begin(check, 1.2)
    assert check.alpha_0 == 1.0001  # the search's, not the evaluation's
    with pytest.raises(RuntimeError, match="differ"):
        _begin(check, 1.3, tau=F(1, 3))


# ===========================================================================
#  The outer search
# ===========================================================================


def _config() -> RunConfig:
    return RunConfig(
        rounds=N,
        completeness_budget=F(1, 10**6),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        declared_tolerance=0.0,
        alpha_search=AlphaSearchSettings(coarse_points=3, refine_steps=0),
    )


def _result(alpha: float) -> SliceResult:
    rate = SimpleNamespace(
        key_length=KEY, h_lb=1.0, h_low=1.0, reference_bracket=None,
        rounds=N, alpha=alpha, key_length_reason_code="first_order_reported",
    )
    return SliceResult(
        compilation=None,  # type: ignore[arg-type]
        declaration=None,  # type: ignore[arg-type]
        honest_distribution={},
        acceptance=None,  # type: ignore[arg-type]
        docked=None,  # type: ignore[arg-type]
        bundle_directory=Path("."),
        bundle=None,  # type: ignore[arg-type]
        reread=None,  # type: ignore[arg-type]
        labels=None,  # type: ignore[arg-type]
        key_rate=rate,  # type: ignore[arg-type]
        declared_tolerance=0.0,
    )


def _fake_run(
    b: F, solves: list[float], checks: list[RunCheck], *, before_solve: int = 0
) -> Any:
    """Return a run at one alpha that refuses as run_slice does.

    The first ``before_solve`` evaluations are refused before the check's
    solve (a compilation refusal), so the bound is formed at a later one.
    """

    def run_one(config: RunConfig, index: int) -> Any:
        alpha = config.alpha
        assert alpha is not None
        check = run_check()
        checks.append(check)
        check.begin(
            honest_supplied=True, caller_constraint_entries=0, option="on",
            tau=TAU, rounds=N, alpha=alpha,
        )
        if index < before_solve:
            return SliceRefusal(
                stage=SliceStage.COMPILATION, reason="compiled_badly", detail="x"
            )
        check.ensure_bound(("decl", "acc"), _solved(b, solves))
        if check.refused:
            return SliceRefusal(
                stage=SliceStage.SOLVE, reason=UNREACHABLE_REASON, detail="refused"
            )
        check.note_order(alpha)
        return _result(alpha)

    return run_one


def test_a_search_whose_cap_is_above_tau_evaluates_every_order() -> None:
    """With b = 1, x = 1000 (alpha_0-1)/alpha_0 = 1000 * 1e-5/(1 + 1e-5), about 0.01.

    2^-0.01 is about 0.993 > 1/2: nothing is refused, the search solves once,
    and every order it evaluates records its diagnostic.
    """
    solves: list[float] = []
    checks: list[RunCheck] = []
    outcome = run_searched(_config(), _fake_run(F(1), solves, checks))
    assert solves == [ALPHA_0]
    assert len({id(check) for check in checks}) == 1
    assert isinstance(outcome, SliceResult)
    record = outcome.statistics_consistency
    assert record is not None and not record.refused
    assert record.cap is not None and record.cap.exponent < F(1, 50)
    assert len(record.orders) == 3
    search = outcome.alpha_search
    assert search is not None and search.chosen is not None


def test_a_search_whose_cap_is_at_most_tau_stops_at_once_and_is_refused() -> None:
    """With b = 1000, x is about 1000 * 1e-5 * 1000 = 10 >= 1, so 2^-x <= 1/2.

    The run is refused as a whole at its first evaluation, before that
    evaluation's own solve: the search stops, chooses nothing, and no order
    is evaluated.
    """
    solves: list[float] = []
    outcome = run_searched(_config(), _fake_run(F(1000), solves, []))
    assert solves == [ALPHA_0]
    assert isinstance(outcome, SliceRefusal)
    assert outcome.reason == UNREACHABLE_REASON
    assert "no alpha is chosen" in outcome.detail
    search = outcome.alpha_search
    assert search is not None and search.chosen is None
    assert len(search.evaluations) == 1
    assert search.evaluations[0].point.reason == UNREACHABLE_EVALUATION_REASON
    record = outcome.statistics_consistency
    assert record is not None and record.refused and record.orders == ()


def test_a_bound_formed_at_a_later_evaluation_refuses_there() -> None:
    """The first evaluation is refused before the solve; the second forms b."""
    solves: list[float] = []
    outcome = run_searched(
        _config(), _fake_run(F(1000), solves, [], before_solve=1)
    )
    assert isinstance(outcome, SliceRefusal) and outcome.reason == UNREACHABLE_REASON
    search = outcome.alpha_search
    assert search is not None and len(search.evaluations) == 2
    assert solves == [ALPHA_0]


def test_a_check_outside_a_search_is_the_runs_own() -> None:
    assert run_check() is not run_check()


def test_no_evaluated_order_lies_below_alpha_0() -> None:
    """The review's F-3: alpha_0 is at most the first order the search evaluates.

    1 + lower = 1.0000063803106163; the search evaluates its first grid point
    at 12 significant digits, 1.00000638031 (item (i): every order the search
    evaluates is at least alpha_0).
    """
    config = replace(
        _config(),
        alpha_search=AlphaSearchSettings(
            lower=6.380310616175632e-06, coarse_points=3, refine_steps=0
        ),
    )
    solves: list[float] = []
    outcome = run_searched(config, _fake_run(F(1, 10**6), solves, []))
    record = outcome.statistics_consistency
    assert record is not None and len(record.orders) == 3
    assert all(order.alpha >= solves[0] for order in record.orders)


def test_the_rule_that_fixed_alpha_0_is_recorded() -> None:
    """Item (i), (v): a search's lowest evaluated order; a run's fixed order."""
    outcome = run_searched(_config(), _fake_run(F(1, 10**9), [], []))
    record = outcome.statistics_consistency
    assert record is not None
    assert record.alpha_0_rule is Alpha0Rule.LOWEST_EVALUATED_ORDER
    assert record.as_record()["alpha_0_rule"] == "lowest_evaluated_order"
    alone = RunCheck()
    _begin(alone, 1.5)
    assert alone.alpha_0 == 1.5 and alone.alpha_0_rule is Alpha0Rule.FIXED_ORDER


def test_an_undecided_refusal_does_not_say_the_cap_is_at_most_tau(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With the integer enclosure [1, 2] of log2 3, x = 3/2 is undecided.

    n = 10, alpha_0 = 3/2, b = 9/20: x = 10 * (1/3) * (9/20) = 3/2. The run is
    refused, and its detail says the cap is not shown to exceed tau.
    """
    from certiqs_key.foundations import balls

    monkeypatch.setattr(balls, "AVAILABLE", False)
    check = RunCheck()
    _begin(check, 1.5, tau=F(1, 3))
    check.ensure_bound(("decl", "acc"), _solved(F(9, 20), []))
    assert check.cap is not None and check.cap.exponent == F(3, 2)
    assert check.refused
    detail = refusal_detail(check.cap, check.bound)  # type: ignore[arg-type]
    assert "which is not shown to exceed min_model_pass_probability = 1/3" in detail
    assert "is at most" not in detail
