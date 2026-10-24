"""SA2 -- the tail machinery itself: both routes, both boundaries, both forms.

The frozen registry pins the VALUES of six small tables
(``tests/golden/test_statistics_acceptance_against_registry.py`` reads them).
What it cannot pin is the machinery's behaviour off those tables: the boundary
conventions of Theorem ``thm:binomial-tails``, the monotonicity the proof of
``prop:rule-exact`` (iii) runs on, and -- the load-bearing one -- that the ENCLOSURE
route is a rigorous bracket rather than an approximation, so that the one
decision it feeds is the conservative one ``def:conservative-evaluation``
asks for.

THE CLAIMS CITED. There is no assumption A-RATIONAL: the condition is the
definition ``def:conservative-evaluation``, decided by requirements, and its
"Consequently" sentence is ``binomial-box/lem:widening``; this file names
those, so that a test and the line it tests name the same claim.
(``receiver/ass:exact`` owns A-EXACT for a different assumption, the exact
window; the frozen registry keeps A-EXACT wherever a derivation names it, and
says at its own site why.)

What is the exact rule's is ``binomial-box/prop:rule-exact`` and what holds for
every rule is ``binomial-box/lem:guard``, clause for clause, and this file
cites those. The frozen registry keeps SA3 as a section id.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from certiqs_key.statistics import (
    TailBound,
    binomial_cdf,
    binomial_pmf,
    extremal_endpoints,
    lower_tail,
    regularized_incomplete_beta,
    upper_tail,
    within_budget,
)
from certiqs_key.statistics import tails as tails_module

HALF = Fraction(1, 2)


@pytest.mark.contract
def test_the_boundary_values_are_exact_on_every_route() -> None:
    """Theorem thm:binomial-tails's boundary values, and why they may not be enclosures.

    ``Pr[N < 0] = 0`` is what makes ``k = 0`` admissible in Eq.
    ``eq:kappaminus`` for every budget, and ``Pr[N > n] = 0`` what makes
    ``k = n`` admissible in Eq. ``eq:kappaplus``. Those two facts are the whole
    of ``prop:rule-exact`` (i): the two sets are non-empty, so the extrema
    exist. A bracket that a conservative comparison could reject would break
    that on the enclosure route.
    """
    for rounds, honest in ((4, HALF), (10**6, Fraction(1, 10**9))):
        below = lower_tail(rounds, honest, 0)
        assert below.exact is True
        assert below.value == 0
        above = upper_tail(rounds, honest, rounds)
        assert above.exact is True
        assert above.value == 0
    # The other two boundary values of Theorem thm:binomial-tails.
    assert lower_tail(4, HALF, 5).value == 1
    assert upper_tail(4, HALF, -1).value == 1
    assert binomial_cdf(4, HALF, -1).value == 0
    assert binomial_cdf(4, HALF, 4).value == 1


@pytest.mark.contract
def test_both_tails_are_monotone_in_the_count() -> None:
    """The property the proof of prop:rule-exact (iii) uses, and nothing else.

    ``k -> Pr[N < k]`` is non-decreasing because the events increase with ``k``;
    ``k -> Pr[N > k]`` is non-increasing. Extremality and the admissible
    relaxation of ``prop:rule-exact`` (iii) are that monotonicity and the
    definition of a maximum.
    """
    for honest in (Fraction(1, 5), HALF, Fraction(7, 8)):
        below = [lower_tail(9, honest, k).value for k in range(11)]
        above = [upper_tail(9, honest, k).value for k in range(10)]
        assert below == sorted(below)
        assert above == sorted(above, reverse=True)
        assert below[0] == 0
        assert above[-1] == 0


@pytest.mark.contract
def test_the_upper_tail_is_non_decreasing_in_the_success_probability() -> None:
    """The last sentence of Theorem thm:binomial-tails: ``p -> Pr[N >= k]`` is non-decreasing."""  # noqa: E501
    values = [upper_tail(6, Fraction(index, 12), 2).value for index in range(13)]
    assert values == sorted(values)


@pytest.mark.contract
def test_a_degenerate_honest_mass_spends_no_budget() -> None:
    """Claim prop:rule-exact (v), at the level of the tails themselves."""
    for count in range(5):
        assert upper_tail(4, Fraction(0), count).value == 0
        assert lower_tail(4, Fraction(1), count).value == 0
    assert lower_tail(4, Fraction(0), 1).value == 1
    assert upper_tail(4, Fraction(1), 3).value == 1


@pytest.mark.contract
def test_the_incomplete_beta_form_equals_the_summed_tail() -> None:
    """Eq. eq:uppertail, on a spread of ``(n, p, k)`` the registry does not freeze.

    ``I_p(k, n-k+1) = Pr[N >= k] = Pr[N > k-1]``. The two sides are computed by
    routes sharing no step: a polynomial integral against a sum of mass points.
    """
    for rounds in (1, 2, 5, 7):
        for numerator in range(rounds * 2 + 1):
            honest = Fraction(numerator, rounds * 2)
            for count in range(1, rounds + 1):
                assert (
                    regularized_incomplete_beta(honest, count, rounds - count + 1)
                    == upper_tail(rounds, honest, count - 1).value
                )


@pytest.mark.contract
def test_the_incomplete_beta_refuses_its_own_domain_violations() -> None:
    """Eq. eq:ireg is stated for ``a, b >= 1`` and ``x`` in ``[0, 1]``."""
    with pytest.raises(ValueError, match="a, b >= 1"):
        regularized_incomplete_beta(HALF, 0, 3)
    with pytest.raises(ValueError, match="x in"):
        regularized_incomplete_beta(Fraction(3, 2), 1, 3)


# ---------------------------------------------------------------------------
#  The enclosure route
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_enclosure_route_brackets_the_exact_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bracket, not an approximation -- checked against the exact value.

    The budget is forced to zero so that a case whose exact tails ARE known
    takes the enclosure route; the two are then compared directly. That is the
    only way to check the enclosure at all: where it is taken in earnest, the
    exact value is by construction too large to write down.
    """
    exact = {
        (rounds, count): (
            lower_tail(rounds, honest, count).value,
            upper_tail(rounds, honest, count).value,
        )
        for rounds, honest in ((8, Fraction(3, 4)), (10, HALF))
        for count in range(rounds + 1)
    }
    monkeypatch.setattr(tails_module, "EXACT_TAIL_BIT_BUDGET", 0)
    for (rounds, count), (below, above) in exact.items():
        honest = Fraction(3, 4) if rounds == 8 else HALF
        enclosed_below = lower_tail(rounds, honest, count)
        enclosed_above = upper_tail(rounds, honest, count)
        if count not in (0, rounds):
            assert enclosed_below.exact is False
            assert enclosed_above.exact is False
        assert enclosed_below.lower <= below <= enclosed_below.upper
        assert enclosed_above.lower <= above <= enclosed_above.upper


@pytest.mark.contract
def test_the_enclosure_route_reproduces_the_frozen_endpoints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The conservative decision is not a different decision, where it can decide.

    ``GUARD-lower-two-counts`` is ``n = 10``, ``p = 1/2``, budgets ``9/10`` and
    ``1/20``, and its frozen endpoints are ``kappa^- = 7``, ``kappa^+ = 8``.
    Forced onto the enclosure route the module must return the same integers:
    an enclosure only changes an answer when it cannot decide, and at
    192 significant bits nothing here is that close.
    """
    monkeypatch.setattr(tails_module, "EXACT_TAIL_BIT_BUDGET", 0)
    lower, upper, exact = extremal_endpoints(10, HALF, Fraction(9, 10), Fraction(1, 20))
    assert (lower, upper) == (7, 8)
    assert exact is False


@pytest.mark.contract
def test_the_enclosure_agrees_with_the_contracts_own_bernoulli_bounds() -> None:
    """The instance Remark rem:guard reasons about, at ``n = 10^6``.

    The remark's argument is ``Pr[N > 0] = 1 - (1-p)^n <= n p`` by Bernoulli's
    inequality, with the mirror ``Pr[N < 1] = (1-p)^n >= 1 - n p``. The exact
    tails here have some ten million digits and the frozen registry writes
    neither down; what it freezes is the pair of integers the inequalities
    decide. This asserts the enclosure is consistent with BOTH inequalities, so
    the endpoints are not merely right by accident.
    """
    rounds, honest = 10**6, Fraction(1, 10**9)
    expectation = rounds * honest
    above = upper_tail(rounds, honest, 0)
    assert above.exact is False
    assert above.upper <= expectation
    below = lower_tail(rounds, honest, 1)
    assert below.lower >= 1 - expectation
    assert below.lower <= below.upper <= 1


@pytest.mark.contract
def test_an_undecided_comparison_is_resolved_against_the_budget() -> None:
    """A conservative evaluation: the decision is made against the UPPER bound only.

    A bracket straddling the budget establishes nothing, so the count is treated
    as inadmissible -- which lowers ``kappa^-`` and raises ``kappa^+``, i.e.
    enlarges the emitted interval, which ``prop:rule-exact`` (iii) says "can
    only lower the failure probability".
    """
    budget = Fraction(1, 10)
    straddling = TailBound(Fraction(1, 20), Fraction(1, 5), exact=False)
    assert within_budget(straddling, budget) is False
    assert within_budget(TailBound(Fraction(0), budget, exact=False), budget) is True
    assert within_budget(TailBound(budget, budget, exact=True), budget) is True


@pytest.mark.contract
def test_a_tail_bound_refuses_to_be_an_enclosure_it_is_not() -> None:
    """The invariants of the record, so that an inverted bracket cannot exist."""
    with pytest.raises(ValueError, match="lower <= upper"):
        TailBound(Fraction(1, 2), Fraction(1, 4), exact=False)
    with pytest.raises(ValueError, match="single number"):
        TailBound(Fraction(1, 4), Fraction(1, 2), exact=True)
    with pytest.raises(ValueError, match="enclosure, not exactly"):
        _ = TailBound(Fraction(1, 4), Fraction(1, 2), exact=False).value


@pytest.mark.contract
def test_the_mass_points_sum_to_one_and_vanish_off_the_range() -> None:
    """The elementary fact every table rests on, and the two out-of-range values."""
    for rounds, honest in ((1, Fraction(1, 3)), (6, Fraction(2, 7))):
        total = sum(
            (binomial_pmf(rounds, honest, count) for count in range(rounds + 1)),
            Fraction(0),
        )
        assert total == 1
        assert binomial_pmf(rounds, honest, -1) == 0
        assert binomial_pmf(rounds, honest, rounds + 1) == 0
