"""The matrix-function enclosures over a WIDE ball, where their widening decides.

``foundations/lem:matrix-function-perturbation`` (i), (ii), (iii)(b): the
Lipschitz widening ``L e`` of a power, the ``sqrt(n) L e`` of its trace, and
the ``p (1-p) a^(p-2) e ||H||`` of the derivative, with ``L`` read at the end
of ``[lo, hi]`` where ``|f'|`` is largest and ``a`` at the lower end;
``foundations/cor:least-eigenvalue-over-enclosure`` (ii) on a ball (both parts
of every radius count); and the grid rounding of
``foundations/dyadic.enclosure_eigenvalue_bounds`` charged to the radius
(``lem:recentred-enclosure`` (iv)).

``tests/unit/test_certified_arithmetic.py`` builds ``Ball.of`` exact matrices,
whose spectral residual ``e`` is about ``1e-38``, so the perturbation terms
never decide containment and deleting any of them would survive that file.
Here the input is a ball of radius ``1e-6``, and the exact values at members on
its boundary (60-digit ``mpmath``) must lie in every enclosure.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

mpmath = pytest.importorskip("mpmath")
pytest.importorskip("flint")
from certiqs_key.foundations import balls  # noqa: E402
from certiqs_key.foundations.exact import Cx  # noqa: E402

pytestmark = pytest.mark.contract

RADIUS = Fraction(1, 10**6)


def _cx(z: complex) -> Cx:
    return Cx(Fraction(z.real), Fraction(z.imag))


def _mp(array: np.ndarray) -> object:
    mpmath.mp.dps = 60
    out = mpmath.matrix(*array.shape)
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            z = complex(array[i, j])
            re, im = Fraction(z.real), Fraction(z.imag)
            out[i, j] = mpmath.mpc(
                mpmath.mpf(re.numerator) / re.denominator,
                mpmath.mpf(im.numerator) / im.denominator,
            )
    return out


def _inside(part: object, value: object) -> bool:
    lo, hi = -balls.upper(-part), balls.upper(part)
    v = mpmath.mpf(value)
    return bool(
        mpmath.mpf(lo.numerator) / lo.denominator
        <= v
        <= mpmath.mpf(hi.numerator) / hi.denominator
    )


def _members(centre: np.ndarray, rng: np.random.Generator) -> list[np.ndarray]:
    n = centre.shape[0]
    r = float(RADIUS) * (1 - 2.0**-20)  # strictly inside the box after rounding
    out = [
        centre + r * np.ones((n, n)),
        centre - r * np.ones((n, n)),
        centre + r * np.eye(n),
        centre - r * np.eye(n),
    ]
    for _ in range(3):
        a = rng.uniform(-1, 1, (n, n)) + 1j * rng.uniform(-1, 1, (n, n))
        h = (a + a.conj().T) / 2
        out.append(centre + r * h / np.max(np.abs(h)))
    return out


@pytest.mark.parametrize("seed", [1, 2, 3])
@pytest.mark.parametrize("exponent", [Fraction(2, 3), Fraction(3, 2)])
def test_powers_traces_and_derivatives_hold_every_member(
    seed: int, exponent: Fraction
) -> None:
    rng = np.random.default_rng(seed)
    n = 3
    q, _ = np.linalg.qr(rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n)))
    centre = np.asarray(q @ np.diag([1.0, 1.5, 3.0]) @ q.conj().T, dtype=np.complex128)
    centre = (centre + centre.conj().T) / 2
    direction = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    direction = np.asarray((direction + direction.conj().T) / 2, dtype=np.complex128)
    rows = tuple(tuple(_cx(complex(z)) for z in row) for row in centre)
    with balls.precision(128):
        ball = balls.Ball.enclosure(rows, [[RADIUS] * n for _ in range(n)])
        sp = balls.spectral(ball)
        s = balls.real(exponent)
        powered = balls.power(sp, s, "A")
        traced = balls.trace_power(sp, s, "A")
        p = balls.real(Fraction(2, 3))
        dpow = balls.deriv_power(
            sp,
            p,
            balls.Ball.of([[_cx(complex(z)) for z in row] for row in direction]),
            "A",
        )
    mpmath.mp.dps = 60
    se = mpmath.mpf(exponent.numerator) / exponent.denominator
    pm = mpmath.mpf(2) / 3
    for member in _members(centre, rng):
        values, vectors = mpmath.eighe(_mp(member))
        root = vectors * mpmath.diag([x**se for x in values]) * vectors.H
        h = vectors.H * _mp(direction) * vectors
        kernel = mpmath.matrix(n, n)
        for i in range(n):
            for j in range(n):
                x, y = values[i], values[j]
                dd = (
                    pm * x ** (pm - 1)
                    if abs(x - y) < mpmath.mpf(10) ** -40
                    else (x**pm - y**pm) / (x - y)
                )
                kernel[i, j] = dd * h[i, j]
        derivative = vectors * kernel * vectors.H
        for i in range(n):
            for j in range(n):
                assert _inside(powered.m[i, j].real, root[i, j].real)
                assert _inside(powered.m[i, j].imag, root[i, j].imag)
                assert _inside(dpow.m[i, j].real, derivative[i, j].real)
                assert _inside(dpow.m[i, j].imag, derivative[i, j].imag)
        assert _inside(traced, sum(x**se for x in values))


@pytest.mark.parametrize(
    ("s", "lo", "hi", "bound"),
    [
        # s > 1: |f'| is largest at the upper end, s hi^(s-1) = 3/2 * 2 = 3.
        (Fraction(3, 2), Fraction(1), Fraction(4), Fraction(3)),
        # s < 1: at the lower end, s lo^(s-1) = 1/2 * 2 = 1.
        (Fraction(1, 2), Fraction(1, 4), Fraction(4), Fraction(1)),
    ],
)
def test_the_lipschitz_constant_bounds_the_derivative_on_the_whole_interval(
    s: Fraction, lo: Fraction, hi: Fraction, bound: Fraction
) -> None:
    """lem:matrix-function-perturbation (i): the Lipschitz constant ``L``.

    ``L = s a^(s-1)`` if ``s <= 1``, ``s b^(s-1)`` if ``s >= 1``.
    """
    with balls.precision(128):
        constant = balls._lipschitz(balls.real(s), balls.real(lo), balls.real(hi))
    assert balls.upper(constant) >= bound


@pytest.mark.parametrize("exponent", [Fraction(2, 3), Fraction(3, 2)])
def test_a_spread_spectrum_with_radii_on_the_diagonal_only(exponent: Fraction) -> None:
    """A spread spectrum, the radii on the diagonal only.

    Radii on the diagonal alone (so ``e`` must read the diagonal residual) and
    a spectrum from 1/100 to 100 (so the constant ``a^(p-2)`` of (iii)(b) must be
    taken at the LOWER end): the exact values at the box's corners lie inside.
    """
    n = 3
    diagonal = [0.01, 1.0, 100.0]
    centre = np.diag(diagonal).astype(np.complex128)
    rng = np.random.default_rng(7)
    direction = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    direction = np.asarray((direction + direction.conj().T) / 2, dtype=np.complex128)
    rows = tuple(tuple(_cx(complex(z)) for z in row) for row in centre)
    radii = [[RADIUS if i == j else Fraction(0) for j in range(n)] for i in range(n)]
    with balls.precision(128):
        ball = balls.Ball.enclosure(rows, radii)
        sp = balls.spectral(ball)
        powered = balls.power(sp, balls.real(exponent), "A")
        dpow = balls.deriv_power(
            sp,
            balls.real(Fraction(2, 3)),
            balls.Ball.of([[_cx(complex(z)) for z in row] for row in direction]),
            "A",
        )
    r = float(RADIUS) * (1 - 2.0**-20)
    mpmath.mp.dps = 60
    se = mpmath.mpf(exponent.numerator) / exponent.denominator
    pm = mpmath.mpf(2) / 3
    for signs in ((1, 1, 1), (-1, -1, -1), (-1, 1, -1), (1, -1, 1)):
        member = centre + r * np.diag(signs)
        values = [
            mpmath.mpf(Fraction(member[i, i].real).numerator)
            / Fraction(member[i, i].real).denominator
            for i in range(n)
        ]
        for i in range(n):
            assert _inside(powered.m[i, i].real, values[i] ** se)
            for j in range(n):
                x, y = values[i], values[j]
                dd = pm * x ** (pm - 1) if i == j else (x**pm - y**pm) / (x - y)
                h = _mp(direction)[i, j]
                assert _inside(dpow.m[i, j].real, (dd * h).real)
                assert _inside(dpow.m[i, j].imag, (dd * h).imag)


def test_the_least_eigenvalue_over_a_ball_reads_both_parts_of_each_radius() -> None:
    """cor:least-eigenvalue-over-enclosure (ii) on a ball: |Re| and |Im| both count.

    The member ``[[1 - r, r(1+i)], [r(1-i), 1 - r]]`` lies in the ball of the
    identity with halo ``r`` on every real and imaginary part, and its least
    eigenvalue is ``1 - (1 + sqrt 2) r``; ``least_eigenvalue`` must lie below it.
    """
    r = RADIUS
    one, zero = _cx(1 + 0j), _cx(0j)
    with balls.precision(128):
        ball = balls.Ball.enclosure(((one, zero), (zero, one)), [[r, r], [r, r]])
        low = balls.least_eigenvalue(ball)
    # 2.41421357 > 1 + sqrt 2, so this right-hand side lies below the member's.
    assert low <= 1 - Fraction(241421357, 10**8) * r


def test_the_grid_rounding_of_the_centre_is_charged_to_the_radius() -> None:
    """The grid rounding of the centre enters rho.

    lem:recentred-enclosure / dyadic.enclosure_eigenvalue_bounds: an entry below
    the 160-bit grid is rounded away, and its rounding must enter rho.
    """
    from certiqs_key.foundations.dyadic import enclosure_eigenvalue_bounds

    tiny = Fraction(1, 2**200)
    centre = ((_cx(1 + 0j), _cx(0j)), (_cx(0j), Cx(-tiny, Fraction(0))))
    low, high = enclosure_eigenvalue_bounds(centre, [[Fraction(0)] * 2] * 2)
    assert low <= -tiny and high >= 1
