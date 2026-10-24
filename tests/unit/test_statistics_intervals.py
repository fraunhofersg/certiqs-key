"""The exact rule and the guard, on inputs the registry does not freeze.

The seven frozen ``GUARD_CASES`` pin the values. What is pinned here is the
STRUCTURE ``prop:rule-exact`` and ``lem:guard`` prove, over a sweep: existence and the
ordering chain (i), the budgets met at the EMITTED endpoints (ii), extremality
and the one admissible direction (iii), the degenerate masses (v), and the exact
cost of the guard with its four iff conditions (vi).

ONE TEST HERE CLOSES A LOOP THE IMPLEMENTATION OPENS. The four verdicts
``guard_lo0``..``guard_up1`` are computed from the ENLARGEMENT, which Theorem
``prop:rule-exact`` (vi) proves equivalent to the budget-versus-distribution-function
comparisons the equations are stated as. That equivalence is the contract's, and
:func:`test_the_four_guard_conditions_agree_with_their_own_equations` evaluates
the other side of it directly, so the implementation's shortcut is checked
against the form it took the shortcut from.

THE CLAIMS CITED. There is no assumption A-RATIONAL: the condition is the
definition ``def:conservative-evaluation``, decided by requirements, and its
"Consequently" sentence is ``binomial-box/lem:widening``; this file names
those, so that a test and the line it tests name the same claim. (``receiver/ass:exact``
owns A-EXACT for a different assumption, the exact window; the frozen registry
keeps A-EXACT wherever a derivation names it, and says at its own site why.)

What is the exact rule's is ``binomial-box/prop:rule-exact`` and what holds for
every rule is ``binomial-box/lem:guard``, clause for clause, and this file
cites those. The frozen registry keeps SA3 as a section id.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from certiqs_key.statistics import (
    binomial_cdf,
    binomial_pmf,
    extremal_endpoints,
    guarded_endpoints,
    lower_tail,
    outcome_interval,
    upper_tail,
)

#: A sweep wide enough to reach both regimes of Remark rem:guard: ordinary
#: budgets, a near-unit single-tail budget, a zero budget, and rare outcomes
#: whose expected count over the whole run is below the tail budget.
SWEEP = [
    (rounds, Fraction(numerator, denominator), Fraction(lower), Fraction(upper))
    for rounds in (1, 2, 3, 8, 11)
    for numerator, denominator in ((0, 1), (1, 1), (1, 2), (1, 5), (3, 4), (1, 100))
    for lower in (Fraction(0), Fraction(1, 20), Fraction(1, 4), Fraction(9, 10))
    for upper in (Fraction(0), Fraction(1, 20), Fraction(1, 3))
]


@pytest.mark.contract
def test_the_ordering_chain_holds_on_every_input_of_the_sweep() -> None:
    """Eq. eq:ordering: ``0 <= k^- <= floor(n p) <= ceil(n p) <= k^+ <= n``.

    Lemma ``lem:guard`` (i). The chain is what makes honest containment
    unconditional -- ``q^- <= floor(n p)/n <= p`` and ``p <= ceil(n p)/n <=
    q^+`` -- so it is asserted on every input rather than on the frozen ones.
    """
    for rounds, honest, eps_lower, eps_upper in SWEEP:
        interval = outcome_interval(rounds, honest, eps_lower, eps_upper)
        assert 0 <= interval.k_lower <= interval.floor_np
        assert interval.floor_np <= interval.ceil_np <= interval.k_upper <= rounds
        assert interval.floor_np == math.floor(rounds * honest)
        assert interval.ceil_np == math.ceil(rounds * honest)
        # The consequence the construction map depends on.
        assert interval.box_lower <= honest <= interval.box_upper


@pytest.mark.contract
def test_the_emitted_endpoints_meet_their_budgets() -> None:
    """Eq. eq:budget-met, Lemma lem:guard (ii), at the EMITTED endpoints.

    Not at ``kappa^{+-}``: the guard moves ``k^-`` DOWN and ``k^+`` UP, and
    part (ii) is a consequence of part (iii) and that direction.
    """
    for rounds, honest, eps_lower, eps_upper in SWEEP:
        interval = outcome_interval(rounds, honest, eps_lower, eps_upper)
        assert lower_tail(rounds, honest, interval.k_lower).upper <= eps_lower
        assert upper_tail(rounds, honest, interval.k_upper).upper <= eps_upper


@pytest.mark.contract
def test_the_extremal_endpoints_are_extremal_and_the_relaxation_is_admissible() -> None:
    """Claim prop:rule-exact (iii), in both directions, including the unsound one.

    ``kappa^-`` is the LARGEST admissible count and ``kappa^+`` the SMALLEST, so
    one step INSIDE either breaks its budget -- the direction
    ``binomial-box/lem:widening`` (v) shows unsafe -- while every step outside
    meets it.
    """
    for rounds, honest, eps_lower, eps_upper in SWEEP:
        kappa_lower, kappa_upper, _ = extremal_endpoints(
            rounds, honest, eps_lower, eps_upper
        )
        for relaxed in range(kappa_lower + 1):
            assert lower_tail(rounds, honest, relaxed).upper <= eps_lower
        for relaxed in range(kappa_upper, rounds + 1):
            assert upper_tail(rounds, honest, relaxed).upper <= eps_upper
        if kappa_lower < rounds:
            assert lower_tail(rounds, honest, kappa_lower + 1).upper > eps_lower
        if kappa_upper > 0:
            assert upper_tail(rounds, honest, kappa_upper - 1).upper > eps_upper


@pytest.mark.contract
def test_the_four_guard_conditions_agree_with_their_own_equations() -> None:
    """Claim prop:rule-exact (vi): the enlargement side against the tail side.

    Eqs. ``eq:guard-lo0``, ``eq:guard-lo1``, ``eq:guard-up0`` and
    ``eq:guard-up1`` are stated as comparisons of an allocated budget against a
    value of the count distribution function, and the theorem proves each one
    equivalent to a statement about Eq. ``eq:guard-cost``'s enlargement. The
    module evaluates the enlargement side; this evaluates the tail side, using
    ``Pr[N >= k] = Pr[N > k-1]``, and asserts they agree.
    """
    for rounds, honest, eps_lower, eps_upper in SWEEP:
        interval = outcome_interval(rounds, honest, eps_lower, eps_upper)
        floor_np, ceil_np = interval.floor_np, interval.ceil_np
        lo0 = eps_lower < binomial_cdf(rounds, honest, floor_np).value
        lo1 = eps_lower < binomial_cdf(rounds, honest, floor_np + 1).value
        up0 = eps_upper < upper_tail(rounds, honest, ceil_np - 1).value
        up1 = eps_upper < upper_tail(rounds, honest, ceil_np - 2).value
        assert interval.guard_lo0_holds is lo0
        assert interval.guard_lo1_holds is lo1
        assert interval.guard_up0_holds is up0
        assert interval.guard_up1_holds is up1


@pytest.mark.contract
def test_the_guard_cost_identities_and_the_distance_bound() -> None:
    """Eq. eq:guard-cost and Eq. eq:guard-from-p, on the whole sweep.

    The two measures are different and the contract states both, "because
    reporting only the second one would overstate the guarantee": the
    enlargement against the raw quantile interval is not bounded by one count,
    while the emitted endpoint's DISTANCE from the honest value is at most
    ``1/n`` on whichever side the guard acts.
    """
    for rounds, honest, eps_lower, eps_upper in SWEEP:
        interval = outcome_interval(rounds, honest, eps_lower, eps_upper)
        assert interval.lower_enlargement == max(
            0, interval.kappa_lower - interval.k_lower
        )
        assert interval.upper_enlargement == max(
            0, interval.k_upper - interval.kappa_upper
        )
        assert interval.lower_enlargement == max(
            0, interval.kappa_lower - interval.floor_np
        )
        assert interval.upper_enlargement == max(
            0, interval.ceil_np - interval.kappa_upper
        )
        assert interval.distance_below_p >= 0
        assert interval.distance_above_p >= 0
        if interval.lower_enlargement > 0:
            assert interval.distance_below_p <= Fraction(1, rounds)
        if interval.upper_enlargement > 0:
            assert interval.distance_above_p <= Fraction(1, rounds)


@pytest.mark.contract
def test_the_guard_is_the_two_clamps_and_nothing_else() -> None:
    """Eq. eq:guard, evaluated against the extremal endpoints it clamps."""
    for rounds, honest, eps_lower, eps_upper in SWEEP:
        kappa_lower, kappa_upper, _ = extremal_endpoints(
            rounds, honest, eps_lower, eps_upper
        )
        assert guarded_endpoints(rounds, honest, kappa_lower, kappa_upper) == (
            min(kappa_lower, math.floor(rounds * honest)),
            max(kappa_upper, math.ceil(rounds * honest)),
        )


@pytest.mark.contract
@pytest.mark.parametrize("rounds", [1, 2, 7, 40])
@pytest.mark.parametrize("budget", [Fraction(0), Fraction(1, 8), Fraction(9, 10)])
def test_a_degenerate_honest_mass_gives_a_degenerate_interval(
    rounds: int, budget: Fraction
) -> None:
    """Claim prop:rule-exact (v), for every admissible budget rather than one.

    At ``p = 0`` the interval is ``[0, 0]`` and at ``p = 1`` it is ``[n, n]``,
    "in both cases ``eps^-`` and ``eps^+`` are unspent, both tails being exactly
    zero" -- which is one of the two reasons Remark ``rem:epsstar`` gives for
    ``epsilon_star`` being generally strictly below ``ecomp``.
    """
    empty = outcome_interval(rounds, Fraction(0), budget, budget)
    assert (empty.k_lower, empty.k_upper) == (0, 0)
    full = outcome_interval(rounds, Fraction(1), budget, budget)
    assert (full.k_lower, full.k_upper) == (rounds, rounds)
    for interval, honest in ((empty, Fraction(0)), (full, Fraction(1))):
        assert lower_tail(rounds, honest, interval.k_lower).value == 0
        assert upper_tail(rounds, honest, interval.k_upper).value == 0


@pytest.mark.contract
@pytest.mark.parametrize("honest", [Fraction(1, 3), Fraction(1, 2), Fraction(4, 5)])
def test_a_zero_budget_buys_the_whole_range(honest: Fraction) -> None:
    """The proof of Theorem thm:monotonicity-limits (iii), as it applies to one outcome.

    At ``eps^- = 0`` no ``k >= 1`` is admissible, since
    ``Pr[N < k] >= (1-p)^n > 0``; at ``eps^+ = 0`` no ``k <= n-1`` is, since
    ``Pr[N > k] >= p^n > 0``. So the interval is the whole of ``[0, n]`` and the
    box bounds are ``[0, 1]``: a zero completeness budget buys no constraint.
    """
    interval = outcome_interval(9, honest, Fraction(0), Fraction(0))
    assert (interval.kappa_lower, interval.kappa_upper) == (0, 9)
    assert (interval.k_lower, interval.k_upper) == (0, 9)
    assert (interval.box_lower, interval.box_upper) == (Fraction(0), Fraction(1))


@pytest.mark.contract
def test_the_interval_shrinks_as_the_budget_grows() -> None:
    """Theorem thm:monotonicity-limits (i) at the level of one outcome, which is where it is proved.

    Raising a budget grows the admissible set of Eq. ``eq:kappaminus``, so its
    MAXIMUM does not fall; it grows the set of Eq. ``eq:kappaplus``, so its
    MINIMUM does not rise; and both clamps of Eq. ``eq:guard`` are monotone in
    their first argument.
    """  # noqa: E501
    budgets = [Fraction(index, 20) for index in range(20)]
    previous = outcome_interval(11, Fraction(3, 7), budgets[0], budgets[0])
    for budget in budgets[1:]:
        current = outcome_interval(11, Fraction(3, 7), budget, budget)
        assert previous.k_lower <= current.k_lower
        assert current.k_upper <= previous.k_upper
        previous = current


@pytest.mark.contract
def test_an_undecidable_comparison_moves_both_endpoints_outward() -> None:
    """A conservative evaluation at BOTH comparison sites of the sweep, not just one.

    ``within_budget`` is pinned in isolation elsewhere; this pins the two CALL
    SITES, which is where the direction is actually chosen -- and the second of
    them (``kappa^+``) calls no helper at all. The budgets here are set EXACTLY
    equal to the tail values they are compared against, on a ``p`` whose
    denominator forces the enclosure route, so neither comparison can be
    certified: the true endpoints are ``kappa^- = 3`` and ``kappa^+ = 4``, and a
    conservative decision must return something strictly outside both.
    Deciding either comparison the other way would return the true endpoints and
    would not be a conservative evaluation (``def:conservative-evaluation``).
    """
    rounds = 8
    honest = Fraction(3**400 // 3 + 1, 3**400)
    eps_lower = sum(
        (binomial_pmf(rounds, honest, count) for count in range(3)), Fraction(0)
    )
    eps_upper = sum(
        (binomial_pmf(rounds, honest, count) for count in range(5, rounds + 1)),
        Fraction(0),
    )
    kappa_lower, kappa_upper, exact = extremal_endpoints(
        rounds, honest, eps_lower, eps_upper
    )
    assert exact is False
    assert kappa_lower < 3
    assert kappa_upper > 4
    # The enlarged interval still meets the budgets and still contains the
    # honest value, which is what makes the direction free to take.
    interval = outcome_interval(rounds, honest, eps_lower, eps_upper)
    assert lower_tail(rounds, honest, interval.k_lower).upper <= eps_lower
    assert upper_tail(rounds, honest, interval.k_upper).upper <= eps_upper
    assert interval.box_lower <= honest <= interval.box_upper
