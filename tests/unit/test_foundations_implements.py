"""The clauses of the foundations claims whose ``implements`` links are set.

``foundations/def:binary64`` (i) -> ``certiqs_key.foundations.exact:scalar_is_binary64``
and ``foundations/def:tiers`` -> ``certiqs_key.foundations.assurance:Assurance``.
``tests/unit/test_binary64_range.py`` already pins the real predicate
``is_binary64`` at the range boundaries; what is added here is the complex
clause of def:binary64 (i), that ``B_C`` asks each part separately, and the
three clauses of def:tiers. Every expected value is derived by hand in the
comment beside it from Definition def:binary64 (i): ``B`` is the set of
``m 2^q`` with ``|m| < 2^53`` and ``-1074 <= q <= 971``.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.foundations.exact import Cx, scalar_is_binary64

_MAX = F(((1 << 53) - 1) << 971)  # m = 2^53 - 1, q = 971: the largest element of B
_TINY = F(1, 1 << 1074)  # m = 1, q = -1074: the smallest positive element of B


@pytest.mark.parametrize(
    ("value", "in_b_c"),
    [
        # Both parts in B: 1 = 1 * 2^0, 2^-1074 = 1 * 2^-1074.
        (Cx(F(1), _TINY), True),
        # Both parts at the extremes of B, of opposite signs.
        (Cx(_MAX, -_MAX), True),
        # Real part in B, imaginary part 2^-1075 not: any m 2^q = 2^-1075 with
        # q >= -1074 needs m = 2^(-1075-q), not an integer.
        (Cx(F(1), F(1, 1 << 1075)), False),
        # The same with the parts swapped: the real part is asked too.
        (Cx(F(1, 1 << 1075), F(1)), False),
        # Imaginary part 1 + 2^-53 = (2^53 + 1) 2^-53; its odd significand
        # 2^53 + 1 does not fit |m| < 2^53 at any q, so it is not in B.
        (Cx(F(1), 1 + F(1, 1 << 53)), False),
        # Imaginary part 2^1024 = m 2^q needs q <= 971 hence m >= 2^53.
        (Cx(F(0), F(1 << 1024)), False),
        # 1/3 is not a dyadic rational, so it is in no m 2^q.
        (Cx(F(1, 3), F(0)), False),
        # The real axis: B embeds in B_C with imaginary part 0 = 0 * 2^0.
        (Cx(F(3, 4), F(0)), True),
    ],
)
def test_scalar_is_binary64_decides_b_c_part_by_part(value: Cx, in_b_c: bool) -> None:
    """def:binary64 (i): ``x + iy`` is in ``B_C`` iff ``x`` and ``y`` are in ``B``."""
    assert scalar_is_binary64(value) is in_b_c
    assert scalar_is_binary64(Cx(-value.re, -value.im)) is in_b_c


def test_the_tiers_are_exactly_three_labels() -> None:
    """def:tiers: a tier is one of three labels, and there is no other tier."""
    labels = {"estimate", "first-order", "certified"}
    assert {tier.value for tier in Assurance} == labels
    assert len(Assurance) == 3


def test_the_tiers_are_listed_weakest_first() -> None:
    """def:tiers: estimate below first-order below certified."""
    assert list(Assurance) == [
        Assurance.ESTIMATE, Assurance.FIRST_ORDER, Assurance.CERTIFIED
    ]


@pytest.mark.parametrize("label", ["Certified", "Estimate", "first_order", ""])
def test_no_other_label_is_a_tier(label: str) -> None:
    """def:tiers: "There is no other tier"."""
    with pytest.raises(ValueError):
        Assurance(label)
