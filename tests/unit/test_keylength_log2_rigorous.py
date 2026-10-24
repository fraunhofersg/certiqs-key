"""``log2(1/eps_PA)`` bounded above rigorously, on integers, trusting no libm.

The key length subtracts ``(alpha / (alpha - 1)) log2(1/eps_PA)``, so its
lower bound needs an UPPER bound on the logarithm. It is an exact rational from
the ``atanh`` series (``meat_core/finitekey/keylength.py``). These tests would
fail if the bound fell below the true value, checked two independent ways:

* with INTEGERS ONLY at a coarse grid: ``x = a / 2^12`` lies above
  ``log2(1/eps) = log2(2^k / p)`` exactly when ``2^a p^4096 >= 2^(4096 k)``,
  a comparison of Python integers, so the least such ``x`` and the one below
  it bracket the true value, and the bound must not fall below the lower
  end;
* at 80 digits (``mpmath``), against the true value itself.

And it must stay within ``1e-12`` of the former binary64 value, so that no key
length moves for a reason other than rigour.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction

import pytest

from certiqs_key.meat_core.finitekey.keylength import _log2_reciprocal_upper

pytestmark = pytest.mark.contract

#: Fractional bits of the integer check: ``p^4096`` has at most 220,000 bits.
GRID_BITS = 12


def _samples(count: int = 120) -> list[float]:
    rng = random.Random(20261008)
    values = [2.0 ** (-rng.uniform(0.0, 60.0)) for _ in range(count)]
    return [*values, 1e-10, 1e-9, 3e-11, 0.1, 0.999, 1.5 * 2.0**-33, 1e-300]


def _integer_bracket(eps: float) -> tuple[Fraction, Fraction]:
    """Return ``(lo, hi)``, consecutive multiples of ``2^-12`` around ``log2(1/eps)``.

    ``eps = p / 2^k``; ``a / 2^12 >= log2(2^k / p)`` iff
    ``2^a p^(2^12) >= 2^(k 2^12)``. ``hi`` is the least such multiple.
    """
    numerator, denominator = eps.as_integer_ratio()
    k = denominator.bit_length() - 1
    scale = 1 << GRID_BITS
    target = 1 << (k * scale)
    power = numerator**scale
    # Start from the float estimate and walk to the exact crossing.
    a = math.floor(-math.log2(eps) * scale) - 2
    while (power << a if a >= 0 else power >> -a) >= target and a > -(10**9):
        a -= 1
    while not ((power << a) if a >= 0 else (power >> -a)) >= target:
        a += 1
    return Fraction(a - 1, scale), Fraction(a, scale)


@pytest.mark.parametrize("eps", _samples()[:40] + _samples()[-7:])
def test_the_bound_lies_in_the_integer_bracket(eps: float) -> None:
    lower, upper = _integer_bracket(eps)
    bound = _log2_reciprocal_upper(eps)
    assert bound >= lower
    assert bound <= upper + Fraction(1, 2**100)


def test_the_bound_is_above_the_true_value_and_within_1e_12_of_the_former_one() -> None:
    mpmath = pytest.importorskip("mpmath")
    mpmath.mp.dps = 80
    for eps in _samples():
        bound = _log2_reciprocal_upper(eps)
        truth = -mpmath.log(mpmath.mpf(eps), 2)
        assert mpmath.mpf(bound.numerator) / bound.denominator >= truth, eps
        former = Fraction(math.nextafter(-math.log2(eps), math.inf))
        if math.frexp(eps)[0] == 0.5:
            former = Fraction(1 - math.frexp(eps)[1])
        assert abs(float(bound - former)) <= 1e-12, eps


@pytest.mark.parametrize("exponent", [0, 1, 7, 33, 1074])
def test_a_power_of_two_is_exact(exponent: int) -> None:
    """``eps = 2^-k`` gives ``k`` exactly: an enclosure there would cost a key bit."""
    assert _log2_reciprocal_upper(math.ldexp(1.0, -exponent)) == exponent
