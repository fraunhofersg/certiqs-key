"""The two smallest pieces: the support-aware linear algebra and the kernel.

Neither is a claim of its own; both are how three conventions of the contract
become executable, and each of the three is a place an implementation can be
quietly wrong:

* ``0^p = 0`` on the kernel (contract Section 4.1), realised by a relative
  support cutoff;
* the key pinching ``Z`` of Definition ``def:maps`` as a row-label operation;
* the lower-semicontinuous extension of ``d(u, v)`` (Lemma ``foundations/lem:kernel``),
  whose values ``d(0, 0) = 0`` and ``d(u, 0) = +inf`` carry claim C9b.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from certiqs_key.foundations.kernel import (
    LOG2_E,
    divergence_kernel,
    divergence_kernel_du,
    divergence_kernel_dv,
)
from certiqs_key.meat_core.objective.linalg import (
    SUPPORT_CUTOFF,
    as_matrix,
    divided_difference,
    is_hermitian,
    is_positive_definite,
    pinch,
    psd_power,
    psd_trace_power,
    support_rank,
    support_spectrum,
)


@pytest.mark.contract
def test_the_kernel_convention_is_zero_on_the_kernel() -> None:
    """Contract Section 4.1: ``X^p`` on the support, ``0^p = 0`` off it."""
    operator = np.diag([1.0, 0.0]).astype(np.complex128)
    powered = psd_power(operator, 0.3)
    assert powered[1, 1] == 0.0
    assert powered[0, 0] == pytest.approx(1.0)
    assert psd_trace_power(operator, 0.3) == pytest.approx(1.0)
    assert support_rank(operator) == 1


@pytest.mark.contract
def test_numerical_dust_is_treated_as_kernel() -> None:
    """Without a cutoff, an eigenvalue of 1e-17 becomes 1e-9 after ``t^{1/alpha}``.

    That is the failure the registry names: it would pollute ``T`` at the ninth
    digit. With the cutoff the same input gives exactly the rank-one answer.
    """
    dust = np.diag([1.0, 1e-17]).astype(np.complex128)
    assert psd_trace_power(dust, 1.0 / 1.9) == pytest.approx(1.0, abs=1e-15)
    assert support_rank(dust) == 1
    without_cutoff = 1.0 + (1e-17) ** (1.0 / 1.9)
    assert without_cutoff > 1.0 + 1e-10  # what the cutoff prevents


@pytest.mark.contract
@pytest.mark.parametrize("scale", (1e-18, 1e-6, 1.0, 1e6))
def test_the_cutoff_is_relative_so_the_support_is_scale_invariant(
    scale: float,
) -> None:
    """``T(cX) = c T(X)``, so which directions are support must not depend on ``c``.

    An absolute floor would delete the support of a lightly weighted sector and
    silently turn its branch operator into zero.
    """
    operator = scale * np.diag([1.0, 0.5, 0.0]).astype(np.complex128)
    assert support_rank(operator) == 2
    values, _ = support_spectrum(operator)
    assert sorted(values)[0] == 0.0
    assert psd_trace_power(operator, 0.5) == pytest.approx(
        (scale**0.5) * (1.0 + 0.5**0.5), rel=1e-12
    )
    assert SUPPORT_CUTOFF == 1e-12


@pytest.mark.contract
def test_the_pinching_keeps_entries_that_share_a_raw_key_value() -> None:
    """Definition def:maps: ``Z(tau) = sum_j Z_j tau Z_j`` on the ``R`` register."""
    labels = np.asarray([0, 1, 0], dtype=np.int64)
    matrix = np.arange(9, dtype=np.float64).reshape(3, 3).astype(np.complex128)
    pinched = pinch(matrix, labels)
    assert pinched[0, 2] == matrix[0, 2]  # both labelled 0
    assert pinched[0, 1] == 0.0  # 0 against 1
    assert pinched[1, 1] == matrix[1, 1]
    # Idempotent, and a fixed point is exactly a block-diagonal operator.
    assert np.allclose(pinch(pinched, labels), pinched)


@pytest.mark.contract
def test_the_pinching_is_trace_preserving_and_self_adjoint() -> None:
    """Definition foundations/def:pinching: CPTP, self-adjoint, idempotent, unital."""
    labels = np.asarray([0, 0, 1], dtype=np.int64)
    generator = np.random.default_rng(5)
    raw = generator.normal(size=(3, 3)) + 1j * generator.normal(size=(3, 3))
    matrix = as_matrix(raw @ raw.conj().T)
    other = as_matrix(np.eye(3) * np.array([1.0, 2.0, 3.0]))
    assert np.trace(pinch(matrix, labels)).real == pytest.approx(np.trace(matrix).real)
    assert np.trace(other @ pinch(matrix, labels)).real == pytest.approx(
        np.trace(pinch(other, labels) @ matrix).real
    )
    assert np.allclose(pinch(np.eye(3, dtype=np.complex128), labels), np.eye(3))


@pytest.mark.contract
def test_the_divided_difference_kernel_is_the_contracts() -> None:
    """Eq. eq:dk: the difference quotient off the diagonal, the derivative on it."""
    values = np.asarray([0.25, 1.0], dtype=np.float64)
    kernel = divided_difference(values, 0.5)
    assert kernel[0, 0] == pytest.approx(0.5 * 0.25**-0.5)
    assert kernel[1, 1] == pytest.approx(0.5 * 1.0**-0.5)
    assert kernel[0, 1] == pytest.approx((0.25**0.5 - 1.0) / (0.25 - 1.0))
    assert kernel[0, 1] == kernel[1, 0]  # symmetric and real


@pytest.mark.contract
def test_the_divided_difference_kernel_is_continuous_across_the_diagonal() -> None:
    """Nearly-equal eigenvalues take the derivative value, not a cancelled ratio."""
    for separation in (1e-8, 1e-12, 1e-16, 0.0):
        values = np.asarray([1.0, 1.0 + separation], dtype=np.float64)
        kernel = divided_difference(values, 0.4)
        assert kernel[0, 1] == pytest.approx(0.4 * 1.0**-0.6, rel=1e-6)


@pytest.mark.contract
def test_the_divided_difference_kernel_refuses_a_singular_argument() -> None:
    """Eq. eq:dk is stated at a positive definite argument."""
    with pytest.raises(ValueError, match="eq:dk"):
        divided_difference(np.asarray([1.0, 0.0]), 0.5)


@pytest.mark.contract
def test_hermiticity_and_definiteness_helpers() -> None:
    """The boundary predicates the validation layer relies on."""
    assert is_hermitian(np.array([[1.0, 1j], [-1j, 2.0]], dtype=np.complex128))
    assert not is_hermitian(np.array([[1.0, 1j], [1j, 2.0]], dtype=np.complex128))
    assert is_positive_definite(np.eye(2, dtype=np.complex128))
    assert not is_positive_definite(np.diag([1.0, 0.0]).astype(np.complex128))
    with pytest.raises(ValueError, match="square"):
        as_matrix(np.zeros((2, 3)))


@pytest.mark.contract
def test_o_kernel_conventions_frozen_values() -> None:
    """Lemma foundations/lem:kernel, value by value. The registry pins the same six."""
    assert divergence_kernel(0.0, 0.0) == 0.0
    assert divergence_kernel(0.0, 0.5) == 0.0
    assert divergence_kernel(0.5, 0.0) == math.inf
    assert divergence_kernel(0.5, 0.5) == 0.0
    assert divergence_kernel(0.5, 0.25) == pytest.approx(0.5)
    assert divergence_kernel(0.25, 0.5) == pytest.approx(-0.25)


@pytest.mark.contract
def test_a_single_kernel_term_may_be_negative() -> None:
    """Clamping individual terms at zero computes a larger objective."""
    assert divergence_kernel(0.25, 0.5) < 0.0
    total = divergence_kernel(0.25, 0.5) + divergence_kernel(0.75, 0.5)
    assert total > 0.0  # only the full KL sum is non-negative


@pytest.mark.contract
def test_the_kernel_is_non_increasing_in_its_second_argument() -> None:
    """The property Theorem thm:convexity uses to carry convexity through K."""
    values = [divergence_kernel(0.5, v) for v in (0.1, 0.25, 0.5, 0.9, 1.0)]
    assert values == sorted(values, reverse=True)


@pytest.mark.contract
def test_the_kernel_is_jointly_convex() -> None:
    """foundations/lem:kernel, checked on the midpoint of random feasible pairs."""
    generator = np.random.default_rng(11)
    for _ in range(200):
        u1, v1, u2, v2 = generator.uniform(0.01, 1.0, size=4)
        left = divergence_kernel(0.5 * (u1 + u2), 0.5 * (v1 + v2))
        right = 0.5 * divergence_kernel(u1, v1) + 0.5 * divergence_kernel(u2, v2)
        assert left <= right + 1e-12


@pytest.mark.contract
def test_the_kernel_rejects_negative_arguments() -> None:
    """The kernel is stated on the non-negative quadrant only."""
    for u, v in ((-0.1, 0.5), (0.5, -0.1)):
        with pytest.raises(ValueError, match="non-negative quadrant"):
            divergence_kernel(u, v)


@pytest.mark.contract
def test_the_kernel_derivatives_are_the_ones_in_the_gradient_formulas() -> None:
    """Corollary cor:full-gradient: ``log2(u/v) + log2 e`` and ``-(u/v) log2 e``."""
    assert pytest.approx(1.0 / math.log(2.0)) == LOG2_E
    assert divergence_kernel_du(0.5, 0.25) == pytest.approx(1.0 + LOG2_E)
    assert divergence_kernel_dv(0.5, 0.25) == pytest.approx(-2.0 * LOG2_E)
    step = 1e-7
    numeric = (
        divergence_kernel(0.5 + step, 0.25) - divergence_kernel(0.5 - step, 0.25)
    ) / (2.0 * step)
    assert numeric == pytest.approx(divergence_kernel_du(0.5, 0.25), rel=1e-6)
    numeric = (
        divergence_kernel(0.5, 0.25 + step) - divergence_kernel(0.5, 0.25 - step)
    ) / (2.0 * step)
    assert numeric == pytest.approx(divergence_kernel_dv(0.5, 0.25), rel=1e-6)


@pytest.mark.contract
def test_the_kernel_derivatives_refuse_the_points_the_corollary_excludes() -> None:
    """Corollary cor:full-gradient is stated at q, P, K all strictly positive."""
    for bad in ((0.0, 0.5), (0.5, 0.0)):
        with pytest.raises(ValueError, match="cor:full-gradient"):
            divergence_kernel_du(*bad)
        with pytest.raises(ValueError, match="cor:full-gradient"):
            divergence_kernel_dv(*bad)
