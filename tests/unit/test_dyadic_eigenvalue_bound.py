"""``foundations/lem:least-eigenvalue-bound``: sound always, tight when refined.

CONTRACT TESTS. The lemma says that, for ANY real ``V`` whose Gram defect is
below one, the Gershgorin bound of the conjugated real embedding divided by
``1 +- theta`` is at most ``lambda_min``. So the bound must never exceed the
least eigenvalue, whatever basis the implementation proposes -- the first
test would fail if it did -- and the refinement (a
complex-pair basis and one Ogita-Aishima step) decides how close it lies.

THE REFERENCE is ``mpmath`` at 60 significant digits on the EXACT dyadic
matrix the bound saw (every binary64 entry read as the rational it is), so the
comparison is against the true ``lambda_min`` to about ``1e-55``, far below
the bound's own gap. Matrices: random Hermitian of sizes 1 to 12, repeated
eigenvalues, a cluster of spread ``1e-9``, rank-deficient, and an exact
tensor degeneracy (``A (x) 1``), the cases where a float eigensolver returns
an arbitrary basis of an eigenspace.
"""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
import pytest

from certiqs_key.foundations.dyadic import (
    DyadicMatrix,
    dyadic_upper,
    float_down,
    largest_eigenvalue_bound,
    least_eigenvalue_bound,
)

mpmath = pytest.importorskip("mpmath")

pytestmark = pytest.mark.contract


def _exact_spectrum(matrix: DyadicMatrix) -> list[object]:
    """Return the eigenvalues of the exact matrix at 60 digits."""
    mpmath.mp.dps = 60
    size = matrix.shape[0]
    reference = mpmath.matrix(size, size)
    for i in range(size):
        for j in range(size):
            real, imag = matrix.entry(i, j)
            reference[i, j] = mpmath.mpc(
                mpmath.mpf(real.numerator) / real.denominator,
                mpmath.mpf(imag.numerator) / imag.denominator,
            )
    return sorted(mpmath.eighe(reference, eigvals_only=True))


def _as_mp(value: Fraction) -> object:
    return mpmath.mpf(value.numerator) / value.denominator


def _cases() -> list[tuple[str, np.ndarray]]:
    rng = np.random.default_rng(20261008)
    cases: list[tuple[str, np.ndarray]] = []
    for size in (1, 2, 3, 4, 6, 9, 12):
        raw = rng.normal(size=(size, size)) + 1j * rng.normal(size=(size, size))
        cases.append((f"random-{size}", (raw + raw.conj().T) / 2))
        unitary, _ = np.linalg.qr(raw)
        repeated = np.array([1.0] * (size // 2) + [2.0] * (size - size // 2))
        cases.append((f"repeated-{size}", (unitary * repeated) @ unitary.conj().T))
        cluster = np.array([1.0 + 1e-9 * k for k in range(size)])
        cases.append((f"cluster-{size}", (unitary * cluster) @ unitary.conj().T))
        deficient = np.array([0.0] * (size - size // 2) + [3.0] * (size // 2))
        cases.append(
            (f"rank-deficient-{size}", (unitary * deficient) @ unitary.conj().T)
        )
    base = rng.normal(size=(3, 3)) + 1j * rng.normal(size=(3, 3))
    cases.append(("tensor-degenerate", np.kron((base + base.conj().T) / 2, np.eye(3))))
    return cases


CASES = _cases()


@pytest.mark.parametrize(("name", "values"), CASES, ids=[name for name, _ in CASES])
@pytest.mark.parametrize("basis", ["refined", "eigen", "identity"])
def test_the_bound_never_exceeds_the_least_eigenvalue(
    name: str, values: np.ndarray, basis: str
) -> None:
    """Lemma (ii): sound at every basis the lemma admits, refined or not."""
    matrix = DyadicMatrix.from_array(values).hermitian_part()
    spectrum = _exact_spectrum(matrix)
    low = least_eigenvalue_bound(matrix, basis=basis)  # type: ignore[arg-type]
    assert _as_mp(low) <= spectrum[0], name
    # (iv): the same lemma applied to -R bounds the largest eigenvalue.
    high = largest_eigenvalue_bound(matrix, basis=basis)  # type: ignore[arg-type]
    assert _as_mp(high) >= spectrum[-1], name


@pytest.mark.parametrize(("name", "values"), CASES, ids=[name for name, _ in CASES])
def test_the_refined_bound_is_tight(name: str, values: np.ndarray) -> None:
    """Tightness, which the basis decides: within ``1e-20 ||R||`` when refined.

    Measured at most ``4.3e-24 ||R||`` (a cluster of spread ``1e-6``); the
    unrefined eigenbasis loses about ``2 n eps ||R||``, which is what makes the
    refinement necessary for a ``1e-12`` slack.
    """
    matrix = DyadicMatrix.from_array(values).hermitian_part()
    spectrum = _exact_spectrum(matrix)
    scale = max(1.0, float(np.linalg.norm(values, 2)))
    gap = spectrum[0] - _as_mp(least_eigenvalue_bound(matrix))
    assert 0 <= gap <= 1e-20 * scale, (name, gap)


def test_a_diagonal_matrix_gives_its_least_entry_exactly() -> None:
    """At ``V = 1`` a diagonal matrix has no Gershgorin radius: the bound is exact."""
    matrix = DyadicMatrix.from_array(np.diag([0.75, -0.125, 3.0]))
    assert least_eigenvalue_bound(matrix) == Fraction(-1, 8)


def test_a_matrix_that_is_not_hermitian_is_refused() -> None:
    with pytest.raises(ValueError, match="Hermitian"):
        least_eigenvalue_bound(
            DyadicMatrix.from_array(np.array([[0.0, 1.0], [0.0, 0.0]]))
        )


def test_the_exact_arithmetic_reads_every_binary64_number_as_its_dyadic() -> None:
    """``1 + 1e-17`` is 1 in binary64; the exact sum keeps the difference."""
    one = DyadicMatrix.identity(1)
    tiny = DyadicMatrix.from_array(np.array([[1e-17]]))
    total = one + tiny
    assert total.entry(0, 0)[0] == 1 + Fraction(1e-17)
    assert total.trace() > 1


def test_rounding_toward_minus_infinity_and_dyadic_rounding_up() -> None:
    """``float_down`` never exceeds its argument; ``dyadic_upper`` never falls below."""
    rng = np.random.default_rng(7)
    for _ in range(200):
        value = Fraction(
            int(rng.integers(-(10**18), 10**18)), int(rng.integers(1, 10**18))
        )
        down = float_down(value)
        assert Fraction(down) <= value
        assert Fraction(math.nextafter(down, math.inf)) > value
        up = dyadic_upper(value)
        assert up >= value
        assert up.denominator & (up.denominator - 1) == 0
        assert abs(up - value) <= abs(value) * Fraction(1, 2**60) + Fraction(1, 2**200)
