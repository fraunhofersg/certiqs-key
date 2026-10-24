"""The Bernstein rule's evaluation is the one prop:rule-bernstein (ii) proves monotone.

``binomial-box/prop:rule-bernstein``
defines ``L`` as ``m (u - 1)`` with ``u`` the upper root enclosure of
Eq. ``eq:isqrt-bounds`` iterated ``j`` times from ``1/eps``, and its (ii)
proves monotonicity for one evaluation: before every square root the argument
is rounded up onto ``2^-s Z`` and ``u`` is the upper bound of
Eq. ``eq:isqrt-bounds`` at that grid point with ``d = 2^s`` fixed; ``L`` and
``t`` are the least multiples of ``2^-s`` at or above the values so obtained.

The small cases below are worked by hand from that text, at parameters small
enough to follow (``j = 1``, ``s`` of 0 or 1):

* ``j = 1, s = 0, eps = 1/2``: ``y = 2``, ``c = ceil(2) = 2``, ``d = 1``,
  ``u = (isqrt(2) + 1)/1 = 2``, ``L = ceil(2 (2 - 1)) = 2``.
* ``j = 1, s = 0, eps = 4/9``: ``y = 9/4``, ``c = ceil(9/4) = 3``,
  ``u = (isqrt(3) + 1)/1 = 2``, ``L = 2``. The bare Eq. ``eq:isqrt-bounds`` on
  ``9/4`` would give ``L = 3/2`` and invert the order; on the grid the two
  budgets give the same ``L`` and nothing inverts.
* ``j = 1, s = 1, eps = 1/2``: ``c = ceil(2 * 2) = 4``, ``d = 2``,
  ``u = (isqrt(4 * 2 * 4) + 1)/(2 * 2) = (5 + 1)/4 = 3/2``,
  ``L = ceil(2 (3/2 - 1) * 2)/2 = 1``, and ``1 >= ln 2``.
* ``t`` at ``s = 1``, ``v = 1``, ``L = 1``: ``L/3 = 1/3``, radicand
  ``1/9 + 2 = 19/9``, ``c = ceil(38/9) = 5``,
  ``u = (isqrt(5 * 2 * 4) + 1)/4 = (6 + 1)/4 = 7/4``,
  ``t = ceil((1/3 + 7/4) * 2)/2 = ceil(25/6)/2 = 5/2``, above
  ``t(1) = 1/3 + sqrt(19/9) = 1.786...``.

The frozen R-A endpoints (tests/oracles/registry_statistics_rules.py) are
reproduced unchanged by tests/golden/test_statistics_rules_against_registry.py.
"""

from __future__ import annotations

import math
from fractions import Fraction
from itertools import pairwise

from certiqs_key.statistics.bernstein import (
    DEFAULT_BERNSTEIN_PARAMETERS,
    BernsteinParameters,
    bernstein_deviation,
    budget_term,
    grid_root_up,
)
from certiqs_key.statistics.logs import log_bounds


def test_the_hand_worked_budget_terms() -> None:
    coarse = BernsteinParameters(root_exponent=1, root_precision=0)
    assert budget_term(Fraction(1, 2), coarse) == 2
    assert budget_term(Fraction(4, 9), coarse) == 2
    finer = BernsteinParameters(root_exponent=1, root_precision=1)
    assert budget_term(Fraction(1, 2), finer) == 1
    assert budget_term(Fraction(1, 2), finer) >= math.log(2)


def test_the_hand_worked_root_and_deviation() -> None:
    assert grid_root_up(Fraction(2), 0) == 2
    assert grid_root_up(Fraction(9, 4), 0) == 2
    assert grid_root_up(Fraction(2), 1) == Fraction(3, 2)
    assert grid_root_up(Fraction(19, 9), 1) == Fraction(7, 4)
    finer = BernsteinParameters(root_exponent=1, root_precision=1)
    deviation = bernstein_deviation(Fraction(1), Fraction(1), finer)
    assert deviation == Fraction(5, 2)
    assert deviation >= Fraction(1, 3) + math.sqrt(19 / 9)


def test_the_root_bound_is_an_upper_bound_and_monotone_in_its_argument() -> None:
    values = sorted(
        {
            Fraction(numerator, denominator)
            for numerator in range(1, 60)
            for denominator in (1, 3, 7, 16)
        }
    )
    for precision in (0, 1, 8):
        previous = Fraction(0)
        for value in values:
            root = grid_root_up(value, precision)
            assert root * root > value
            assert root >= previous
            previous = root


def test_the_budget_term_is_monotone_across_binary_boundaries() -> None:
    """(ii) at the default parameters, where the split changes its exponent.

    The budgets straddle ``2^-k`` closely on both sides for k = 1..30, and a
    smaller budget never gives a smaller ``L``; every ``L`` is at or above the
    rigorous lower enclosure of ``ln(1/eps)``.
    """
    budgets = sorted(
        {
            Fraction(1, 2**k) * factor
            for k in range(1, 31)
            for factor in (
                Fraction(2**20 - 1, 2**20),
                Fraction(1),
                Fraction(2**20 + 1, 2**20),
            )
        }
    )
    terms = [budget_term(budget, DEFAULT_BERNSTEIN_PARAMETERS) for budget in budgets]
    for smaller, larger in pairwise(terms):
        assert smaller >= larger
    for budget, term in zip(budgets, terms, strict=True):
        lower = log_bounds(1 / budget, 32, 64).lower
        assert term >= lower
