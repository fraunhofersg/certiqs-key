"""The certified key length is exactly ``l_max`` (``req:certified-evaluation`` (vi)).

CONTRACT TESTS of :func:`~certiqs_key.meat_core.finitekey.keylength.
certified_key_length` against ``def:max-key-length`` evaluated independently
at 80 digits (``mpmath``): ``c = n h - lambda_EC - ceil(log2(1/eps_EV)) + 1``
exact, ``tau = (alpha/(alpha-1)) log2(1/eps_PA)``, the key length
``max{0, floor(c - tau)}``.

The cases that decide it are placed by hand: ``h`` is chosen so that
``c - tau`` lies a hair above or below an integer, closer than the
first-order path's rigorous upper bound on ``log2(1/eps_PA)`` (``2^-128``)
and than a binary64 ``tau`` resolves. Rounding ``tau`` to nearest gains a bit
where ``tau`` rounds down (the unsafe direction); stopping at the first
enclosure without refining loses one where the enclosure straddles the
integer. Neither is ``l_max``, and the tests fail for both.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from certiqs_key.meat_core.finitekey.keylength import (
    _ceil_log2,
    certified_key_length,
)

mpmath = pytest.importorskip("mpmath")

pytestmark = pytest.mark.contract

ROUNDS = 10**8
LAMBDA_EC = 12345
ALPHA = 1.05


def _tau(eps_pa: float, alpha: float = ALPHA) -> object:
    mpmath.mp.dps = 80
    a = mpmath.mpf(Fraction(alpha).numerator) / Fraction(alpha).denominator
    eps = mpmath.mpf(Fraction(eps_pa).numerator) / Fraction(eps_pa).denominator
    return a / (a - 1) * mpmath.log(1 / eps, 2)


def _reference(h: Fraction, eps_ev: float, eps_pa: float) -> int:
    mpmath.mp.dps = 80
    ev = mpmath.mpf(Fraction(eps_ev).numerator) / Fraction(eps_ev).denominator
    ceil_ev = int(mpmath.ceil(mpmath.log(1 / ev, 2)))
    c = ROUNDS * max(Fraction(0), h) - LAMBDA_EC - ceil_ev + 1
    value = mpmath.mpf(c.numerator) / c.denominator - _tau(eps_pa)
    return max(0, int(mpmath.floor(value)))


def _h_at(offset: float, eps_ev: float, eps_pa: float, k: int) -> Fraction:
    """``h`` with ``c - tau = k + offset`` to 60 digits."""
    mpmath.mp.dps = 80
    ceil_ev = _ceil_log2(1 / Fraction(eps_ev))
    target = mpmath.mpf(k) + mpmath.mpf(offset) + _tau(eps_pa) + LAMBDA_EC + ceil_ev - 1
    return Fraction(mpmath.nstr(target / ROUNDS, 60))


@pytest.mark.parametrize("eps_pa", [2.0**-30, 1e-10, 3e-11, 0.1])
@pytest.mark.parametrize("h", [Fraction(3, 10), Fraction(1, 10**4), Fraction(-1, 7)])
def test_the_certified_length_is_l_max(eps_pa: float, h: Fraction) -> None:
    length, clamped = certified_key_length(
        rounds=ROUNDS,
        h=h,
        lambda_ec=LAMBDA_EC,
        eps_ev=1e-10,
        eps_pa=eps_pa,
        alpha=ALPHA,
    )
    assert clamped == (h < 0)
    assert length == _reference(h, 1e-10, eps_pa)


@pytest.mark.parametrize("offset", [1e-45, -1e-45, 1e-20, -1e-20])
def test_the_floor_is_decided_however_close_c_minus_tau_lies(offset: float) -> None:
    eps_pa = 1e-10
    k = 2_000_000
    h = _h_at(offset, 1e-10, eps_pa, k)
    length, _ = certified_key_length(
        rounds=ROUNDS,
        h=h,
        lambda_ec=LAMBDA_EC,
        eps_ev=1e-10,
        eps_pa=eps_pa,
        alpha=ALPHA,
    )
    assert length == (k if offset > 0 else k - 1)


def test_a_tau_rounded_to_nearest_is_not_l_max() -> None:
    """The premise: binary64 ``tau`` lies below the true one, so nearest gains a bit."""
    eps_pa = 1e-10
    true_tau = _tau(eps_pa)
    nearest = (ALPHA / (ALPHA - 1)) * -math.log2(eps_pa)
    assert mpmath.mpf(nearest) != true_tau
    gap = abs(true_tau - mpmath.mpf(nearest))
    offset = -float(gap) / 2 if mpmath.mpf(nearest) < true_tau else float(gap) / 2
    k = 3_000_000
    h = _h_at(offset, 1e-10, eps_pa, k)
    exact = k if offset > 0 else k - 1
    length, _ = certified_key_length(
        rounds=ROUNDS,
        h=h,
        lambda_ec=LAMBDA_EC,
        eps_ev=1e-10,
        eps_pa=eps_pa,
        alpha=ALPHA,
    )
    assert length == exact
    ceil_ev = _ceil_log2(Fraction(10**10))
    c = ROUNDS * h - LAMBDA_EC - ceil_ev + 1
    assert math.floor(c - Fraction(nearest)) != exact


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Fraction(1), 0),
        (Fraction(2), 1),
        (Fraction(3), 2),
        (Fraction(1024), 10),
        (Fraction(1025), 11),
        (Fraction(10**10), 34),
        (Fraction(2**40) + Fraction(1, 3), 41),
    ],
)
def test_the_ceiling_of_log2_compares_powers_of_two(
    value: Fraction, expected: int
) -> None:
    assert _ceil_log2(value) == expected
