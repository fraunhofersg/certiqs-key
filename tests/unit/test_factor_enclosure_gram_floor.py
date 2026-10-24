"""The Gram floor of a factor enclosure is decided EXACTLY.

``foundations/cor:rank-over-factor-enclosure`` (ii), (iii): whether
``l - rho > 0`` is a comparison of rationals, which ``fixes_rank`` makes by
deciding ``G - rho 1`` positive definite through the exact ``LDL^*``. The
cases in ``test_factor_enclosure.py`` are all far from the binary64
resolution, so a binary64 eigenvalue would decide them the same way.

Here ``L_c = [[1, 1], [0, e]]`` with ``e = 2^-30`` and a radius ``tau`` on
entry (2, 2) only. By eq:gram-radius every ``s_ml`` vanishes except
``s_22 = 2 e tau + tau^2``, and ``lambda_min(G) = ((2 + e^2) - sqrt((2 +
e^2)^2 - 4 e^2)) / 2``, about ``e^2 / 2 = 2^-61``. In binary64 both ``G - rho
1`` below round to ``[[1, 1], [1, 1]]``, so a float decision returns the same
answer for both. The exact answers differ: ``tau = 2^-34`` gives ``rho``
about ``2^-63``, and the rank is fixed; ``tau = 2^-31`` gives ``rho`` about
``1.25 * 2^-60``, and it is not.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.foundations.exact import Cx
from certiqs_key.foundations.reference import FactorEnclosure, fixes_rank, gram_radius

pytestmark = pytest.mark.contract

ZERO = F(0)
E = F(1, 2**30)


def _factor(tau: F) -> FactorEnclosure:
    return FactorEnclosure(
        ((Cx(F(1), ZERO), Cx(F(1), ZERO)), (Cx(ZERO, ZERO), Cx(E, ZERO))),
        ((ZERO, ZERO), (ZERO, tau)),
        (F(1), F(1)),
    )


@pytest.mark.parametrize(
    ("tau", "fixed"), [(F(1, 2**34), True), (F(1, 2**31), False)]
)
def test_the_floor_is_decided_below_the_float_resolution(tau: F, fixed: bool) -> None:
    factor = _factor(tau)
    s22 = 2 * E * tau + tau * tau
    rho = gram_radius(factor)
    assert s22 <= rho <= s22 * (1 + F(1, 2**60))
    # lambda_min(G) lies in (e^2/2 - e^4, e^2/2): the exact side of the claim.
    low, high = E * E / 2 - E**4, E * E / 2
    assert (low > rho) is fixed and (high > rho) is fixed
    assert fixes_rank(factor) is fixed
