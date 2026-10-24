"""The dark-count slack: ``rbar``, ``delta_dc`` and Eq. ``eq:darkpmcslack``.

Golden replay of ``DARK_SLACK_CASES``, ``D2_SLACK_CASES``,
``DARK_ROUTE_EXCLUSIVITY_CASES`` and ``POVM_DEFECT_UNDER_WIDENED_D1`` (oracle
entry ``O-RP-DARKSLACK``), first frozen at registry 0.2.0 (a registry version
is one of tests/oracles/registry_receiver_povm.py, not of this module).

WHAT THE ARTIFACT EMITS is ``R`` with THREE SCALARS UNDER DISTINCT NAMES --
``r_min`` exactly as Eq. ``eq:rmin`` computes it, ``rbar = min{r_min, 1}``, and
``delta_dc`` by route -- and the inequality a consumer composes with is
Eq. ``eq:darkpmcslack``, NOT Eq. ``eq:darkpmc``.

THE FIVE THINGS THIS FILE EXISTS TO CATCH:

* ``r_min`` IS NEVER MODIFIED. ``DS-DECLARED-WITNESS-K4`` emits
  ``r_min = 1 + eps_4 > 1`` and ``DS-DECLARED-D1-NEGATIVE-ADMIT-K2`` emits
  ``r_min = -eps_4 < 0``; both are the numbers Eq. ``eq:rmin`` computes;
* ``rbar`` IS NOT FLOORED AT ZERO. A negative ``rbar`` is admissible, because
  "no step uses the sign of ``r_min`` or of ``rbar``";
* ``delta_dc`` FOLLOWS THE ROUTE, not the channel. The witness channel uses no
  (D2) slack at all and still carries the ``(K + 1) eps_2`` term;
* (D1) HAS TWO HALVES, at ``eps_4``, and (D2) is decided at ``eps_2`` with a
  STRICT comparison. Four admit/refuse pairs pin all four sides;
* THE COMPOSED VALUE IS NOT CLAMPED UP TO ``p_mc``. Two admitted channels
  compose BELOW the bare bound, and the contract says the two emitted numbers
  should say so.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from receiver_povm_support import TOLERANCE
from registry_receiver_povm import (
    D2_SLACK_CASES,
    DARK_ROUTE_EXCLUSIVITY_CASES,
    DARK_SLACK_CASES,
    POVM_DEFECT_UNDER_WIDENED_D1,
    rp_oracle,
)

from certiqs_key.receiver import (
    DarkCountChannel,
    DarkCountRoute,
    Refusal,
    RefusalReason,
    capped_coefficient,
    check_dark_channel,
    check_dark_count_source,
    composed_slack,
    composition_correction,
    improved_bound,
    improves_on_weight,
    minimum_multiclick_mass,
    multiclick_mass,
    overstatement,
    product_form,
)

_ROUTES = {
    "generated": DarkCountRoute.PER_PORT_PRODUCT_FORM,
    "declared": DarkCountRoute.DECLARED_MATRIX,
}


def _channel(case_id: str) -> DarkCountChannel:
    """Return one frozen dark-slack case as the module's own channel."""
    case = next(c for c in DARK_SLACK_CASES if c.case_id == case_id)
    if case.route == "generated":
        # The two generated cases are the frozen product forms; DS-GENERATED-K3
        # freezes only its multiclick masses, so the generator is the datum.
        probabilities = (
            [F(1, 10), F(1, 5)]
            if case.port_count == 2
            else [F(1, 10)] * case.port_count
        )
        return product_form(probabilities, DarkCountRoute.PER_PORT_PRODUCT_FORM)
    columns = {
        frozenset(column): {frozenset(row): float(value) for row, value in entries}
        for column, entries in case.columns
    }
    return DarkCountChannel(case.port_count, _ROUTES[case.route], columns)


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_channel_is_admitted_or_refused_at_its_declared_tolerance() -> (
    None
):
    """Def. def:tolmap (iii): (D1) at eps_4, (D2) at eps_2, both sides of both."""
    assert rp_oracle("O-RP-DARKSLACK").claims == ("RC11",)
    for case in DARK_SLACK_CASES:
        channel = _channel(case.case_id)
        outcome = check_dark_channel(channel, TOLERANCE)
        assert (outcome is None) is case.admitted, case.case_id
        if not case.admitted:
            assert isinstance(outcome, Refusal), case.case_id
            expected = (
                RefusalReason.DARK_CONDITION_D1_FAILED
                if case.failing_condition == "(D1)"
                else RefusalReason.DARK_CONDITION_D2_FAILED
            )
            assert outcome.reason is expected, case.case_id
            # The contract spells NO reason for a (D1) or (D2) failure, so the
            # frozen case carries the CONDITION and this module's key is its own.
            assert case.r_min is None, case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_the_three_emitted_scalars_are_the_frozen_ones() -> None:
    """The emitted r_min UNMODIFIED, rbar = min{r_min, 1}, and delta_dc by route."""
    for case in DARK_SLACK_CASES:
        if not case.admitted:
            continue
        channel = _channel(case.case_id)
        r_min = minimum_multiclick_mass(channel)
        r_bar = capped_coefficient(r_min)
        delta = composition_correction(channel.route, channel.port_count, TOLERANCE)
        assert r_min == pytest.approx(float(case.r_min or 0), abs=1e-12), case.case_id
        assert r_bar == pytest.approx(float(case.r_bar or 0), abs=1e-12), case.case_id
        assert delta == pytest.approx(float(case.delta_dc or 0), abs=1e-12), (
            case.case_id
        )
        # Eq. eq:rbarcost: 0 <= r_min - rbar <= (K + 2) eps_4.
        cost = r_min - r_bar
        assert cost == pytest.approx(float(case.r_bar_cost or 0), abs=1e-12), (
            case.case_id
        )
        assert cost + 1e-12 >= 0.0
        assert cost <= float(case.r_bar_cost_bound or 0) + 1e-12, case.case_id
        # Eq. eq:rminupper bounds every column's multiclick mass.
        for column, mass in case.mc_mass:
            actual = multiclick_mass(channel, frozenset(column))
            assert actual == pytest.approx(float(mass), abs=1e-12), (
                case.case_id,
                column,
            )
            assert actual <= float(case.r_min_upper_bound or 1) + 1e-12


@pytest.mark.contract
@pytest.mark.oracle
def test_the_composition_is_eq_darkpmcslack_and_not_eq_darkpmc() -> None:
    """Prop. prop:dark-slack-bound, Rem. rem:d2slack: composed, exact, and gap."""
    for case in DARK_SLACK_CASES:
        if not case.admitted or case.p_mc is None:
            continue
        channel = _channel(case.case_id)
        r_min = minimum_multiclick_mass(channel)
        r_bar = capped_coefficient(r_min)
        delta = composition_correction(channel.route, channel.port_count, TOLERANCE)
        weight = float(case.p_mc)
        slack = composed_slack(weight, r_bar, delta)
        exact_form = improved_bound(r_min, weight)
        assert slack == pytest.approx(float(case.composed_slack), abs=1e-12), (
            case.case_id
        )
        assert exact_form == pytest.approx(
            float(case.composed_exact_form), abs=1e-12
        ), case.case_id
        gap = overstatement(r_min, r_bar, delta, weight)
        assert gap == pytest.approx(float(case.overstatement), abs=1e-12), case.case_id
        # The three agree: eq:darkpmc - eq:darkpmcslack IS eq:darkoverstate.
        assert exact_form - slack == pytest.approx(gap, abs=1e-12), case.case_id
        # And the improvement threshold of rem:d2slack.
        assert improves_on_weight(r_bar, delta, weight) is case.improves_on_p_mc, (
            case.case_id
        )
        if case.improves_on_p_mc:
            assert slack >= weight - 1e-12, case.case_id
        else:
            # NOT CLAMPED UP TO p_mc: the composed value may sit below it.
            assert slack <= weight + 1e-12, case.case_id


@pytest.mark.contract
def test_on_the_generated_route_the_two_inequalities_coincide() -> None:
    """Rem. rem:d2slack: "eq:darkpmcslack IS eq:darkpmc" on that route."""
    for case in DARK_SLACK_CASES:
        if case.route != "generated":
            continue
        channel = _channel(case.case_id)
        r_min = minimum_multiclick_mass(channel)
        correction = composition_correction(
            channel.route, channel.port_count, TOLERANCE
        )
        assert correction == 0.0
        assert r_min <= 1.0
        assert capped_coefficient(r_min) == r_min
        weight = float(case.p_mc or 0)
        assert composed_slack(weight, r_min, 0.0) == pytest.approx(
            improved_bound(r_min, weight), abs=1e-15
        )


@pytest.mark.contract
def test_r_min_may_exceed_one_and_may_be_negative_and_is_never_modified() -> None:
    """`dark_count_channel`: "Neither R nor r_min is modified"; rbar is not floored."""
    witness = _channel("DS-DECLARED-WITNESS-K4")
    assert minimum_multiclick_mass(witness) > 1.0
    assert capped_coefficient(minimum_multiclick_mass(witness)) == 1.0
    negative = _channel("DS-DECLARED-D1-NEGATIVE-ADMIT-K2")
    r_min = minimum_multiclick_mass(negative)
    assert r_min < 0.0
    # NOT FLOORED AT ZERO: rbar = min{r_min, 1} = r_min here.
    assert capped_coefficient(r_min) == r_min
    assert capped_coefficient(r_min) < 0.0
    # 1 - rbar >= 0 in both, which is the whole of the work eq:rbar does.
    for channel in (witness, negative):
        assert 1.0 - capped_coefficient(minimum_multiclick_mass(channel)) >= 0.0


@pytest.mark.contract
@pytest.mark.oracle
def test_eq_d2slack_holds_on_every_admitted_multiclick_column() -> None:
    """Eq. eq:d2slack: R_{MC|S'} >= 1 - delta_dc for every S' in MC_K."""
    for case_id, column, achieved, bound, exact in D2_SLACK_CASES:
        channel = _channel(case_id)
        delta = composition_correction(channel.route, channel.port_count, TOLERANCE)
        mass = multiclick_mass(channel, frozenset(column))
        assert mass == pytest.approx(float(achieved), abs=1e-12), (case_id, column)
        assert 1.0 - delta == pytest.approx(float(bound), abs=1e-12), case_id
        assert mass >= 1.0 - delta - 1e-12, (case_id, column)
        # Thm. thm:dark-counts (iii)'s EXACT value is 1, and the admitted channel
        # misses it by no more than delta_dc.
        assert float(exact) == 1.0
        assert float(exact) - mass <= delta + 1e-12, (case_id, column)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_dark_count_routes_are_exclusive() -> None:
    """Req. req:dark-route-exclusive: a REFUSAL, with the contract's verbatim reason."""
    declared = _channel("DS-DECLARED-BELOW-THRESHOLD-K2")
    for (
        case_id,
        has_declared,
        has_dark,
        admitted,
        route,
        reason,
    ) in DARK_ROUTE_EXCLUSIVITY_CASES:
        channel = declared if has_declared else None
        probabilities = [F(1, 10), F(0)] if has_dark else [F(0), F(0)]
        outcome = check_dark_count_source(channel, probabilities)
        assert (outcome is None) is admitted, case_id
        if admitted:
            assert reason is None, case_id
            expected = (
                DarkCountRoute.DECLARED_MATRIX
                if route == "declared"
                else DarkCountRoute.PER_PORT_PRODUCT_FORM
            )
            taken = (
                channel.route
                if channel is not None
                else product_form(probabilities).route
            )
            assert taken is expected, case_id
        else:
            assert isinstance(outcome, Refusal), case_id
            assert str(outcome.reason) == reason, case_id


@pytest.mark.contract
def test_route_exclusivity_is_decided_on_the_exact_declared_probability() -> None:
    """Req. req:dark-route-exclusive: some p_dc|k NON-ZERO, decided EXACTLY.

    The two routes are exclusive on an EXACT condition about declared data,
    and Def. def:tolmap -- which fixes every condition this contract decides
    under a threshold, and says each is decided "by no other threshold" --
    names none for it.  Deciding it through `to_float` supplies one anyway:
    the binary64 underflow point, at which an exactly non-zero declared
    probability reads 0.0 and the contract-verbatim refusal fails OPEN.
    """
    declared = _channel("DS-DECLARED-BELOW-THRESHOLD-K2")
    underflowing = F(1, 10**400)
    assert underflowing != 0
    assert float(underflowing) == 0.0
    outcome = check_dark_count_source(declared, [underflowing, F(0)])
    assert isinstance(outcome, Refusal)
    assert outcome.reason is RefusalReason.DARK_COUNT_CHANNEL_DECLARED_TWICE


@pytest.mark.contract
def test_the_composed_family_s_defect_is_reported_not_repaired() -> None:
    """Rem. rem:d2slack: the composed family need not be a POVM, and is not fixed.

    The two defects are bounded by ``eps_4`` and BOTH ARE PROPERTIES OF THE
    DECLARED DATUM. Nothing in this package renormalizes a column, clips an
    entry or projects a composed row: the frozen statement is prose, and what is
    checked here is that the composed family really can miss completeness by
    ``eps_4`` and that the module reports rather than repairs.
    """
    assert len(POVM_DEFECT_UNDER_WIDENED_D1) == 2
    kinds = {row[0] for row in POVM_DEFECT_UNDER_WIDENED_D1}
    assert kinds == {"completeness", "positivity"}
    witness = _channel("DS-DECLARED-WITNESS-K4")
    # Its column sums are 1 +/- eps_4 exactly, so sum_S Mtilde_S is not id.
    sums = {round(sum(entries.values()), 12) for entries in witness.columns.values()}
    assert sums == {
        round(1.0 + TOLERANCE.eps_4, 12),
        round(1.0 - TOLERANCE.eps_4, 12),
    }
    # ADMITTED ANYWAY, and emitted as declared.
    assert check_dark_channel(witness, TOLERANCE) is None
