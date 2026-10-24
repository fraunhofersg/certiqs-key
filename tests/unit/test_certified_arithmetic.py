"""The arithmetic of the certified tier: factor forms, enclosures, matrix functions.

CONTRACT TESTS of the foundations claims the certified evaluation rests on,
each against an independent reference (exact rationals, or ``mpmath`` at 60
digits on the exact matrix), and each failing if its claim were false:

* ``foundations/cor:least-eigenvalue-over-enclosure`` (i), (ii):
  :func:`~certiqs_key.foundations.dyadic.enclosure_eigenvalue_bounds` brackets
  the spectrum of EVERY Hermitian member of an entrywise enclosure, checked at
  the members that move the extreme eigenvalues most (wide radii, so that a
  bound charged on the wrong side fails visibly);
* (iii): :func:`~certiqs_key.foundations.exact.factor_form` reproduces the
  element exactly and refuses one that is not positive semidefinite;
* ``foundations/lem:matrix-function-perturbation`` (i)-(iv): the enclosures of
  ``A^s``, ``tr A^s`` and ``D_A[H]`` (:mod:`certiqs_key.foundations.balls`)
  contain the exact values at repeated, clustered and generic spectra, and a
  matrix whose floor is not certified positive is refused (the floor is what
  proves the compression is the support, ``req:certified-evaluation``
  (iii)(b));
* the enclosures formed at 128 and at 256 bits overlap, entry by entry.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from certiqs_key.foundations.dyadic import enclosure_eigenvalue_bounds
from certiqs_key.foundations.errors import HypothesisError
from certiqs_key.foundations.exact import (
    Cx,
    conjugate_transpose,
    factor_form,
    matmul,
    rank_factorisation,
)

mpmath = pytest.importorskip("mpmath")
balls = pytest.importorskip("certiqs_key.foundations.balls")
pytest.importorskip("flint")

pytestmark = pytest.mark.contract


def _cx(z: complex) -> Cx:
    return Cx(Fraction(z.real), Fraction(z.imag))


def _rows(array: np.ndarray) -> tuple[tuple[Cx, ...], ...]:
    return tuple(tuple(_cx(complex(z)) for z in row) for row in array)


def _mp(array: np.ndarray) -> object:
    mpmath.mp.dps = 60
    out = mpmath.matrix(*array.shape)
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            z = complex(array[i, j])
            out[i, j] = mpmath.mpc(
                mpmath.mpf(Fraction(z.real).numerator) / Fraction(z.real).denominator,
                mpmath.mpf(Fraction(z.imag).numerator) / Fraction(z.imag).denominator,
            )
    return out


def _hermitian(rng: np.random.Generator, size: int) -> np.ndarray:
    a = rng.normal(size=(size, size)) + 1j * rng.normal(size=(size, size))
    return np.asarray((a + a.conj().T) / 2, dtype=np.complex128)


def _cases() -> list[np.ndarray]:
    rng = np.random.default_rng(20261009)
    out = [_hermitian(rng, n) for n in (1, 2, 3, 5)]
    out.append(np.diag([1.0, 1.0, 2.0]).astype(np.complex128))
    q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    out.append(np.asarray(q @ np.diag([1.0, 1.0, 2.0]) @ q.T, dtype=np.complex128))
    out.append(np.diag([1.0, 1.0 + 1e-12, 3.0]).astype(np.complex128))
    return out


@pytest.mark.parametrize("index", range(7))
def test_enclosure_bounds_bracket_every_member(index: int) -> None:
    centre = _cases()[index]
    n = centre.shape[0]
    radius = Fraction(1, 64)
    lower, upper = enclosure_eigenvalue_bounds(
        _rows(centre), [[radius] * n for _ in range(n)]
    )
    # Members that push the spectrum furthest within the box: C -+ r J with J
    # the all-ones matrix (||r J||_2 = n r), and C -+ r 1.
    ones = np.ones((n, n))
    for member in (
        centre - 1 / 64 * ones,
        centre + 1 / 64 * ones,
        centre - np.eye(n) / 64,
        centre + np.eye(n) / 64,
    ):
        spectrum = sorted(mpmath.eighe(_mp(member), eigvals_only=True))
        assert mpmath.mpf(lower.numerator) / lower.denominator <= spectrum[0]
        assert spectrum[-1] <= mpmath.mpf(upper.numerator) / upper.denominator


def test_an_exact_enclosure_is_tight() -> None:
    centre = _cases()[3]
    n = centre.shape[0]
    lower, upper = enclosure_eigenvalue_bounds(
        _rows(centre), [[Fraction(0)] * n for _ in range(n)]
    )
    spectrum = sorted(mpmath.eighe(_mp(centre), eigvals_only=True))
    assert abs(float(lower) - float(spectrum[0])) < 1e-30
    assert abs(float(upper) - float(spectrum[-1])) < 1e-30


def test_factor_form_reproduces_a_rank_deficient_element_exactly() -> None:
    half = Fraction(1, 2)
    v = (Cx(Fraction(1), Fraction(0)), Cx(half, half), Cx(Fraction(0), Fraction(1, 3)))
    element = tuple(tuple(v[i] * v[j].conjugate() for j in range(3)) for i in range(3))
    form = factor_form(element)
    assert form is not None
    e, core = form
    assert len(e) == 1
    assert matmul(matmul(conjugate_transpose(e), core), e) == element
    b, c = rank_factorisation(element)
    assert matmul(b, c) == element and len(c) == 1


def test_factor_form_refuses_a_matrix_that_is_not_psd() -> None:
    one, zero = Cx(Fraction(1), Fraction(0)), Cx(Fraction(0), Fraction(0))
    with pytest.raises(HypothesisError):
        factor_form(((one, one), (one, zero)))


@pytest.mark.parametrize("index", range(1, 7))
def test_matrix_functions_contain_the_exact_values(index: int) -> None:
    case = _cases()[index]
    n = case.shape[0]
    positive = case + (abs(float(np.min(np.linalg.eigvalsh(case)))) + 1) * np.eye(n)
    direction = _hermitian(np.random.default_rng(index), n)
    mpmath.mp.dps = 60
    values, vectors = mpmath.eighe(_mp(positive))
    p = Fraction(2, 3)
    pm = mpmath.mpf(2) / 3

    def f(x: object) -> object:
        return x**pm

    root = vectors * mpmath.diag([f(x) for x in values]) * vectors.H
    h = vectors.H * _mp(direction) * vectors
    kernel = mpmath.matrix(n, n)
    for i in range(n):
        for j in range(n):
            x, y = values[i], values[j]
            dd = (
                pm * x ** (pm - 1)
                if abs(x - y) < mpmath.mpf(10) ** -40
                else ((f(x) - f(y)) / (x - y))
            )
            kernel[i, j] = dd * h[i, j]
    derivative = vectors * kernel * vectors.H
    with balls.precision(128):
        spectral = balls.spectral(balls.Ball.of(_rows(positive)))
        powered = balls.power(spectral, balls.real(p), "A")
        traced = balls.trace_power(spectral, balls.real(p), "A")
        dpow = balls.deriv_power(
            spectral, balls.real(p), balls.Ball.of(_rows(direction)), "A"
        )
    for ball, reference in ((powered, root), (dpow, derivative)):
        for i in range(n):
            for j in range(n):
                for part, value in (
                    (ball.m[i, j].real, reference[i, j].real),
                    (ball.m[i, j].imag, reference[i, j].imag),
                ):
                    lo = -balls.upper(-part)
                    hi = balls.upper(part)
                    exact = mpmath.mpf(value)
                    assert mpmath.mpf(lo.numerator) / lo.denominator <= exact
                    assert exact <= mpmath.mpf(hi.numerator) / hi.denominator
    total = sum(f(x) for x in values)
    lo, hi = -balls.upper(-traced), balls.upper(traced)
    assert mpmath.mpf(lo.numerator) / lo.denominator <= total
    assert total <= mpmath.mpf(hi.numerator) / hi.denominator
    assert powered.radius() < 1e-30 and dpow.radius() < 1e-24


def test_a_floor_not_certified_positive_is_refused() -> None:
    """A singular member in the ball: no power, trace or derivative is formed."""
    singular = balls.Ball.enclosure(
        _rows(np.diag([1.0, 0.0]).astype(np.complex128)),
        [[Fraction(0), Fraction(0)], [Fraction(0), Fraction(1, 10**30)]],
    )
    with balls.precision(128):
        spectral = balls.spectral(singular)
        for call in (
            lambda: balls.power(spectral, balls.real(Fraction(1, 2)), "X"),
            lambda: balls.trace_power(spectral, balls.real(2), "X"),
            lambda: balls.deriv_power(
                spectral, balls.real(Fraction(1, 2)), singular, "X"
            ),
        ):
            with pytest.raises(balls.NotCertified):
                call()


def test_the_cholesky_of_a_gram_not_certified_pd_is_refused() -> None:
    gram = balls.Ball.enclosure(
        _rows(np.array([[1.0, 1.0], [1.0, 1.0]], dtype=np.complex128)),
        [[Fraction(0)] * 2, [Fraction(0), Fraction(1, 10**20)]],
    )
    with balls.precision(128), pytest.raises(balls.NotCertified):
        balls.cholesky_upper(gram, "G")


def test_enclosures_at_128_and_256_bits_overlap() -> None:
    case = _cases()[5] + 2 * np.eye(3)
    direction = _hermitian(np.random.default_rng(5), 3)
    results = []
    for bits in (128, 256):
        with balls.precision(bits):
            spectral = balls.spectral(balls.Ball.of(_rows(case)))
            results.append(
                balls.deriv_power(
                    spectral,
                    balls.real(Fraction(1, 3)),
                    balls.Ball.of(_rows(direction)),
                    "A",
                )
            )
    for i in range(3):
        for j in range(3):
            assert results[0].m[i, j].overlaps(results[1].m[i, j])


def test_the_upper_end_is_above_every_member() -> None:
    with balls.precision(128):
        wide = balls.real(Fraction(1, 3)) + balls.flint.arb(
            0, balls.real(Fraction(1, 7))
        )
        assert balls.upper(wide) >= Fraction(1, 3) + Fraction(1, 7)
        assert -balls.upper(-wide) <= Fraction(1, 3) - Fraction(1, 7)
