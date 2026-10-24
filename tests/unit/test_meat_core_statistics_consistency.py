"""The check of the acceptance set against the feasible statistics: the core's part.

WHY THIS EXISTS. ``meat-core/req:unreachable-acceptance-set`` (iv) refuses a
checked run whose cap ``2^(-x)`` on the probability that devices as declared
pass the acceptance test is at most ``tau`` (``min_model_pass_probability``),
``x = n (alpha_0-1)/alpha_0 b``, decided exactly where ``tau`` is a power of
two and otherwise against a rigorous enclosure of ``log2(1/tau)``, an
undecided comparison refusing. A decision that rounded the wrong way would
either let through a run whose own model expects it to abort or withhold a
sound key. What is held here, against values derived by hand:

* which runs are checked, and why not (the requirement's opening paragraph);
* the floor ``f(alpha') = alpha'/(alpha'-1) (alpha_0-1)/alpha_0 b`` of item
  (iii) and its zero at ``b <= 0`` (``prop:minimal-divergence`` (iv));
* the exponent ``x`` (``prop:model-pass-bound`` (ii)), exact;
* item (iv): ``tau = 1/2`` with ``x`` just below, at and above 1; ``tau = 1/3``
  with ``x`` on both sides of ``log2 3``; ``tau = 1``; the undecided band;
  no cap and no refusal where ``b <= 0`` or no bound was formed;
* item (v): the record's entries, ``x`` rounded toward ``-inf`` with the tier
  of ``b``, the decision, ``tau``, the refusal, each order's ``n f``.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

import pytest

from certiqs_key.foundations import balls
from certiqs_key.meat_core.finitekey.consistency import (
    DEFAULT_MIN_MODEL_PASS_PROBABILITY,
    STATISTICS_CHECK_BUDGET_SHARE,
    Alpha0Rule,
    CapDecision,
    DivergenceBound,
    NoBoundReason,
    StatisticsConsistency,
    UncheckedReason,
    check_scope,
    decide_pass_cap,
    dmin_lower_bound,
    model_pass_exponent,
    order_diagnostic,
    proven_floor,
)
from certiqs_key.meat_core.reasons import RefusalReason

pytestmark = pytest.mark.contract

ALPHA_0 = 1.5
#: n of the record tests below.
N = 1000
#: 2^-60, a step far below any rounding of the comparisons below.
TINY = F(1, 2**60)


def _bound(b: F | None, *, estimate: float | None = 0.25) -> DivergenceBound:
    if b is None:
        return DivergenceBound(
            alpha_0=ALPHA_0,
            bound=None,
            tier=None,
            no_bound_reason=NoBoundReason.FIRST_ORDER_WITHDRAWN,
            estimate=estimate,
        )
    return DivergenceBound(
        alpha_0=ALPHA_0, bound=b, tier="certified", estimate=estimate
    )


def _decide(x: F, tau: F, tier: str = "certified"):  # noqa: ANN202
    """Decide item (iv) at the exponent ``x``: n = 3 and alpha_0 = 3/2, so b = x.

    (alpha_0-1)/alpha_0 = 1/3, so x = 3 * (1/3) * b = b.
    """
    return decide_pass_cap(rounds=3, alpha_0=1.5, bound=x, tier=tier, tau=tau)


# ===========================================================================
#  The scope
# ===========================================================================


def test_a_run_is_checked_where_its_statistics_or_a_constraint_are_the_callers():
    supplied = check_scope(
        honest_supplied=True, caller_constraint_entries=0, option="on"
    )
    assert supplied.checked and supplied.unchecked_reason is None
    declared = check_scope(
        honest_supplied=False, caller_constraint_entries=2, option="on"
    )
    assert declared.checked
    model = check_scope(honest_supplied=False, caller_constraint_entries=0, option="on")
    assert not model.checked
    assert model.unchecked_reason is UncheckedReason.OUT_OF_SCOPE
    # An unchecked run names A-REACH as the caller's.
    assert model.as_record()["unchecked_premise"] == "A-REACH"
    assert supplied.as_record()["unchecked_premise"] is None


def test_off_opts_a_run_in_scope_out_and_one_out_of_scope_stays_out_of_scope():
    opted = check_scope(honest_supplied=True, caller_constraint_entries=0, option="off")
    assert not opted.checked and opted.unchecked_reason is UncheckedReason.OPTED_OUT
    out = check_scope(honest_supplied=False, caller_constraint_entries=0, option="off")
    assert out.unchecked_reason is UncheckedReason.OUT_OF_SCOPE
    with pytest.raises(ValueError, match="statistics_check"):
        check_scope(honest_supplied=True, caller_constraint_entries=0, option="maybe")


# ===========================================================================
#  Items (iii) and (v): the floor and the ceiling
# ===========================================================================


def test_the_floor_is_the_bound_carried_to_each_order_exactly() -> None:
    # alpha_0 = 3/2: (alpha_0 - 1)/alpha_0 = 1/3, so D_min >= b/3.
    b = F(3, 10)
    assert dmin_lower_bound(b, ALPHA_0) == F(1, 10)
    # alpha' = 5/4: alpha'/(alpha'-1) = 5, so f = 5 * 1/10 = 1/2.
    assert proven_floor(1.25, ALPHA_0, b) == F(1, 2)
    # At alpha' = alpha_0 the floor is b itself.
    assert proven_floor(ALPHA_0, ALPHA_0, b) == b
    # It grows as alpha' tends to one (alpha'/(alpha'-1) is decreasing).
    assert proven_floor(1.125, ALPHA_0, b) > proven_floor(1.25, ALPHA_0, b)


def test_the_floor_is_zero_where_the_bound_is_not_positive() -> None:
    assert proven_floor(1.25, ALPHA_0, F(0)) == 0
    assert proven_floor(1.25, ALPHA_0, F(-1, 10**15)) == 0


# ===========================================================================
#  Item (iv): the cap and the refusal
# ===========================================================================


def test_the_pass_exponent_against_hand_derived_values() -> None:
    """The exponent x = n (alpha_0-1)/alpha_0 b, derived by hand.

    * n = 1000, alpha_0 = 3/2, b = 3/10: (alpha_0-1)/alpha_0 = (1/2)/(3/2) =
      1/3, so x = 1000 * 1/3 * 3/10 = 100.
    * n = 4 * 10^10, alpha_0 = 5/4, b = 1/1000: (1/4)/(5/4) = 1/5, so
      x = 4 * 10^10 / 5 / 1000 = 8 * 10^6.
    * n = 7, alpha_0 = 3/2, b = 1/10: x = 7 * 1/3 * 1/10 = 7/30, which no
      binary64 number equals.
    """
    assert model_pass_exponent(1000, 1.5, F(3, 10)) == 100
    assert model_pass_exponent(40_000_000_000, 1.25, F(1, 1000)) == 8_000_000
    assert model_pass_exponent(7, 1.5, F(1, 10)) == F(7, 30)
    assert model_pass_exponent(1000, 1.5, F(0)) is None
    assert model_pass_exponent(1000, 1.5, F(-1, 10**15)) is None
    with pytest.raises(ValueError, match="rounds"):
        model_pass_exponent(0, 1.5, F(3, 10))


def test_the_default_threshold_is_one_half() -> None:
    assert F(1, 2) == DEFAULT_MIN_MODEL_PASS_PROBABILITY


def test_tau_one_half_refuses_from_x_equal_to_one_exactly() -> None:
    """With tau = 1/2 = 2^-1, k = 1: refused exactly where x >= 1, i.e. 2^-x <= 1/2."""
    below = _decide(1 - TINY, F(1, 2))
    assert below is not None
    assert below.refused is False and below.decision is CapDecision.EXACT
    at = _decide(F(1), F(1, 2))
    assert at is not None and at.refused is True and at.decision is CapDecision.EXACT
    above = _decide(1 + TINY, F(1, 2))
    assert above is not None and above.refused is True
    assert at.exponent == 1 and at.tau == F(1, 2) and at.tier == "certified"


def test_tau_one_third_is_decided_against_an_enclosure_of_log2_3() -> None:
    """With tau = 1/3, log2(1/tau) = log2 3 = 1.58496250072115618...

    By hand: 2^1.58496 < 3 because 1.58496 < log2 3, and 2^1.58497 > 3. The
    first is not refused (cap above 1/3), the second is; both are decided by
    the enclosure, whose width is far below 10^-5.
    """
    below = _decide(F(158496, 100000), F(1, 3))
    assert below is not None
    assert below.refused is False and below.decision is CapDecision.ENCLOSURE
    above = _decide(F(158497, 100000), F(1, 3))
    assert above is not None
    assert above.refused is True and above.decision is CapDecision.ENCLOSURE


def test_tau_one_refuses_every_positive_exponent() -> None:
    """With tau = 1 = 2^0, k = 0: every x > 0 has x >= 0."""
    cap = _decide(TINY, F(1))
    assert cap is not None and cap.refused is True and cap.decision is CapDecision.EXACT


def test_an_undecided_comparison_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    """With the enclosure [1, 2] of log2 3 (the integer one), x = 3/2 is undecided."""
    monkeypatch.setattr(balls, "AVAILABLE", False)
    assert balls.log2_enclosure(F(3)) == (F(1), F(2))
    cap = _decide(F(3, 2), F(1, 3))
    assert cap is not None
    assert cap.refused is True and cap.decision is CapDecision.UNDECIDED
    # Outside the band the integer enclosure still decides.
    low = _decide(F(1, 2), F(1, 3))
    high = _decide(F(2), F(1, 3))
    assert low is not None and not low.refused
    assert low.decision is CapDecision.ENCLOSURE
    assert high is not None and high.refused
    assert high.decision is CapDecision.ENCLOSURE


def test_the_enclosure_holds_log2_3() -> None:
    """The enclosure of log2 3 = 1.584962500721156181453... meets these digits."""
    lo, hi = balls.log2_enclosure(F(3))
    assert lo <= F(158496250072115619, 10**17)
    assert hi >= F(158496250072115618, 10**17)
    assert hi - lo < F(1, 10**30)


def test_a_non_positive_bound_has_no_cap_and_refuses_nothing() -> None:
    assert _decide(F(0), F(1)) is None
    assert _decide(F(-1, 10**15), F(1)) is None


def test_a_threshold_outside_the_half_open_unit_interval_is_refused() -> None:
    for tau in (F(0), F(-1, 2), F(3, 2)):
        with pytest.raises(ValueError, match="min_model_pass_probability"):
            _decide(F(1), tau)
    with pytest.raises(ValueError, match="min_model_pass_probability"):
        _decide(F(1), 0.5)  # type: ignore[arg-type]


def test_the_decision_carries_the_tier_of_the_bound() -> None:
    cap = _decide(F(2), F(1, 2), tier="first-order")
    assert cap is not None and cap.tier == "first-order" and cap.refused


# ===========================================================================
#  Item (v): the record
# ===========================================================================


def test_a_bound_and_its_reason_are_exclusive() -> None:
    with pytest.raises(ValueError, match="bound is formed"):
        DivergenceBound(alpha_0=ALPHA_0, bound=None, tier=None)
    with pytest.raises(ValueError, match="tier"):
        DivergenceBound(alpha_0=ALPHA_0, bound=F(1), tier=None)


def _consistency(
    bound: DivergenceBound | None, rounds: int, tau: F = F(1, 2), alphas=()  # noqa: ANN001
) -> StatisticsConsistency:
    cap = (
        None
        if bound is None or bound.bound is None or bound.tier is None
        else decide_pass_cap(
            rounds=rounds, alpha_0=bound.alpha_0, bound=bound.bound,
            tier=bound.tier, tau=tau,
        )
    )
    return StatisticsConsistency(
        scope=check_scope(
            honest_supplied=True, caller_constraint_entries=0, option="on"
        ),
        tau=tau,
        rounds=rounds,
        bound=bound,
        cap=cap,
        orders=tuple(
            order_diagnostic(alpha=a, bound=bound, rounds=rounds) for a in alphas
        ),
        alpha_0_rule=Alpha0Rule.FIXED_ORDER,
    )


def test_the_record_carries_the_cap_its_decision_and_the_refusal() -> None:
    """With n = 1000, alpha_0 = 3/2, b = 3/10: x = 100 (hand-derived above), refused.

    At alpha' = 5/4 the diagnostic n f = 1000 * 5 * (1/3) * (3/10) = 500.
    """
    bound = _bound(F(3, 10), estimate=0.31)
    record = _consistency(bound, N, alphas=(1.25,)).as_record()
    assert record["checked"] is True
    assert record["min_model_pass_probability"] == "1/2"
    assert "contradiction_share" not in record and "refused_as_whole" not in record
    assert record["model_pass_exponent_bits"] == 100.0
    assert record["model_pass_exponent_tier"] == "certified"
    assert record["model_pass_decision"] == "exact"
    assert record["refused"] is True and record["no_cap_reason"] is None
    solve = record["solve"]
    assert solve["bound"] == pytest.approx(0.3) and solve["bound"] <= 0.3
    assert solve["dmin_lower_bound"] == pytest.approx(0.1)
    assert record["orders"] == [{"alpha": 1.25, "proven_part_bits": 500.0}]


def test_an_unrefused_cap_is_recorded_with_its_decision() -> None:
    """With n = 3, alpha_0 = 3/2, b = 1/2: x = 1/2, 2^-1/2 > 1/3 = tau: not refused."""
    record = _consistency(_bound(F(1, 2)), 3, tau=F(1, 3)).as_record()
    assert record["model_pass_exponent_bits"] == 0.5
    assert record["model_pass_decision"] == "enclosure"
    assert record["refused"] is False
    assert record["min_model_pass_probability"] == "1/3"


def test_the_recorded_exponent_is_rounded_down() -> None:
    """The exponent 7/30 is no binary64 number: the record holds the one below.

    A recorded x above 7/30 would show a cap 2^(-x) below the proven one.
    """
    recorded = _consistency(_bound(F(1, 10)), 7).as_record()["model_pass_exponent_bits"]
    assert F(recorded) < F(7, 30)
    above = math.nextafter(recorded, math.inf)
    assert F(above) > F(7, 30)


def test_the_record_says_why_there_is_no_cap() -> None:
    for bound, why in (
        (_bound(F(0)), "bound_not_positive"),
        (_bound(F(-1, 10**15)), "bound_not_positive"),
        (_bound(None), "no_bound_formed"),
    ):
        record = _consistency(bound, N, alphas=(1.25,)).as_record()
        assert record["model_pass_exponent_bits"] is None, bound
        assert record["model_pass_exponent_tier"] is None, bound
        assert record["model_pass_decision"] is None, bound
        assert record["no_cap_reason"] == why and record["refused"] is False
    # No bound: n f is not defined at an order; b <= 0: f = 0.
    assert _consistency(_bound(None), N, alphas=(1.25,)).as_record()["orders"] == [
        {"alpha": 1.25, "proven_part_bits": None}
    ]
    assert _consistency(_bound(F(0)), N, alphas=(1.25,)).as_record()["orders"] == [
        {"alpha": 1.25, "proven_part_bits": 0.0}
    ]
    # Before the solve ran, nothing is said.
    assert _consistency(None, N).as_record()["no_cap_reason"] is None


def test_the_record_carries_the_budget_share_the_sign_and_the_alpha_0_rule() -> None:
    """Item (v): the share and wall budget of the solve, whether O_0 < 0, the rule.

    b = 1/10 is formed beside a negative estimate O_0 = -1e-9 (item (ii): the
    sign decides nothing), recorded as a diagnostic.
    """
    assert F(1, 4) == STATISTICS_CHECK_BUDGET_SHARE
    bound = DivergenceBound(
        alpha_0=ALPHA_0,
        bound=F(1, 10),
        tier="first-order",
        estimate=-1e-9,
        budget_share=STATISTICS_CHECK_BUDGET_SHARE,
        budget_seconds=30.0,
    )
    assert bound.formed and bound.estimate_negative is True
    record = _consistency(bound, N).as_record()
    solve = record["solve"]
    assert solve["budget_share"] == "1/4" and solve["budget_seconds"] == 30.0
    assert solve["estimate_negative"] is True and solve["bound"] is not None
    assert record["alpha_0_rule"] == "fixed_order"
    assert record["model_pass_exponent_tier"] == "first-order"
    positive = _bound(F(1, 10), estimate=0.2)
    assert positive.estimate_negative is False
    assert _bound(F(1, 10), estimate=None).estimate_negative is None


def test_the_refusal_string_is_the_cores() -> None:
    assert str(RefusalReason.ACCEPTANCE_SET_UNREACHABLE) == "acceptance_set_unreachable"


@pytest.mark.parametrize(
    ("value", "lo"),
    [
        # By hand: 2^0 = 1 <= 4/3 < 2; 2^2 = 4 <= 4 < 8; 2^-2 = 1/4 <= 1/3 < 1/2;
        # 1 <= 7/4 < 2; 1/2 <= 1023/1024 < 1.
        (F(4, 3), 0),
        (F(4), 2),
        (F(1, 3), -2),
        (F(7, 4), 0),
        (F(1023, 1024), -1),
    ],
)
def test_the_integer_enclosure_without_the_extra(
    monkeypatch: pytest.MonkeyPatch, value: F, lo: int
) -> None:
    """Without python-flint: [k, k + 1] with 2^k <= v < 2^(k+1)."""
    monkeypatch.setattr(balls, "AVAILABLE", False)
    low, high = balls.log2_enclosure(value)
    assert (low, high) == (lo, lo + 1)
    assert F(2) ** int(low) <= value < F(2) ** int(high)
