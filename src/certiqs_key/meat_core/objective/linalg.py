"""Support-aware linear algebra for the contracted objective.

Everything here serves one expression, contract.tex Eq. ``eq:fK``::

    T_chat(omega) = tr[ ( Z( G_chat(omega)^{1/alpha} ) )^alpha ] .

Three conventions of the contract are realised here and nowhere else.

**The kernel convention.** foundations/def:pinching: "the power ``X^p`` is
defined by functional calculus on the support of ``X`` and by ``0^p = 0`` on its
kernel". For ``p = 1/alpha < 1`` the map ``t -> t^p`` has infinite slope at
``0``, so an eigenvalue that floating point reports as ``1e-17`` instead of
``0`` becomes ``1e-9`` after the power and pollutes ``T`` at the ninth digit.
Every power below therefore applies an explicit support cutoff.

**The cutoff is relative, not absolute.** ``T`` is positively homogeneous of
degree one, ``T(cX) = c T(X)`` (contract.tex proof of Theorem ``thm:gradient``
(ii)), so which directions count as support must not depend on the scale of
``X``. A cutoff with an absolute floor would make ``supp X`` shrink as
``tr X -> 0`` and would silently delete the support of a branch operator on a
lightly weighted sector. The cutoff is therefore a fixed fraction of the
spectral radius.

**Pinching is a row-label operation.** The key pinching of Definition
``def:maps`` is ``Z(tau) = sum_j Z_j tau Z_j`` with ``Z_j = |j><j|_R`` tensored
with the identity on every other register, so it keeps exactly those matrix
entries whose two basis indices carry the same raw-key value and zeroes the
rest.
"""

from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt

from certiqs_key.meat_core import thresholds
from certiqs_key.meat_core.errors import HypothesisError

#: Hermitian matrices are held in ``complex128`` throughout: the contract's
#: operators are Hermitian, not real symmetric, and the oracle capability the
#: architecture requires is the complex Hermitian PSD cone
#: (spec/architecture.md 7.4).
Matrix = npt.NDArray[np.complex128]

#: Real vectors and spectra.
Vector = npt.NDArray[np.float64]

#: Eigenvalues below this fraction of the spectral radius are kernel
#: directions. See the module docstring for why it is relative.
SUPPORT_CUTOFF = thresholds.declared(thresholds.SUPPORT_CUTOFF)

#: THE SAME RULER, READ ON A FACTOR. A singular value ``sigma`` of a matrix
#: ``A`` is the square root of an eigenvalue of ``A A^dagger``, so counting the
#: singular values above ``sqrt(SUPPORT_CUTOFF)`` relative to the largest one
#: is counting the eigenvalues of ``A A^dagger`` above ``SUPPORT_CUTOFF``
#: relative to its spectral radius -- :func:`support_rank`'s rule, applied to
#: the operator the factor generates. DERIVED FROM THE ``support_cutoff`` ROW,
#: NOT A DECLARED NUMBER OF ITS OWN: ``frank-wolfe/rem:fo-one-ruler``
#: reads ``dim W_{chat,s}`` this way so that both sides of Eq.
#: ``eq:hsupp-check`` are measured in the units of ``X``, whose directions
#: carry ``sigma^2``. See :func:`factor_support`.
FACTOR_SUPPORT_CUTOFF = math.sqrt(SUPPORT_CUTOFF)

#: Tolerance for the Hermiticity check at the boundary of this module.
HERMITICITY_TOLERANCE = thresholds.declared(thresholds.INTERNAL_HERMITICITY)

#: Relative separation below which two eigenvalues are treated as degenerate
#: in the divided-difference kernel of Eq. eq:dk. See :func:`divided_difference`.
DEGENERACY_TOLERANCE = thresholds.declared(thresholds.DEGENERACY_WINDOW)


def as_matrix(values: npt.ArrayLike) -> Matrix:
    """Return ``values`` as a contiguous complex matrix."""
    array = np.ascontiguousarray(np.asarray(values, dtype=np.complex128))
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError(f"expected a square matrix, got shape {array.shape}")
    return array


def hermitian_part(matrix: Matrix) -> Matrix:
    """Return ``(X + X^dagger) / 2``.

    NOT A REPAIR AND NOT A DECISION. It is applied only where
    :func:`check_internal_hermiticity` has already decided the operator
    Hermitian within :data:`HERMITICITY_TOLERANCE`, so what it removes is
    representation noise BOUNDED BY THAT WINDOW and never a genuine
    anti-Hermitian part. On an operator no caller decided, it would discard
    whatever it was given in silence, which is what the guard exists to
    prevent.

    ON AN EXACTLY HERMITIAN ARGUMENT IT IS THE IDENTITY, entry for entry and
    not merely to within the window: ``X[i][j]`` and ``conj(X[j][i])`` are then
    the same machine number, their sum is exact in binary64, and halving a
    binary64 number is exact. So where this is reached with a DECLARED operator
    -- which happens, and only after that operator has been decided exactly
    (see :func:`check_internal_hermiticity`) -- it returns what it was handed
    and discards nothing at all.
    """
    return np.asarray(0.5 * (matrix + matrix.conj().T), dtype=np.complex128)


def is_hermitian(matrix: Matrix, tolerance: float = HERMITICITY_TOLERANCE) -> bool:
    """Return whether ``matrix`` is Hermitian to within ``tolerance``.

    THE WINDOW IS NEVER THE DECISION ON A DECLARED OPERATOR, and that is a
    statement about ORDER rather than about the arguments this function sees.
    Declared data is decided EXACTLY, by
    :func:`certiqs_key.foundations.exact_admission.is_hermitian_exact`, at
    ``validate_declaration`` -- which every entry point runs before any
    numerical work: ``declaration_from_bundle`` on the bundle path, and
    ``solve`` and ``solve_declaration`` on the in-memory path. A declared
    operator therefore reaches this function only AFTER its predicate was
    decided without a window, where the test below can only pass and
    :func:`hermitian_part` can only be the identity. What
    this window decides is what it says it decides: an operator this module
    FORMED, whose Hermiticity no exact rule has established.

    :func:`check_internal_hermiticity` is the one caller and the
    `internal_hermiticity` threshold row names it.
    """
    scale = max(float(np.max(np.abs(matrix))) if matrix.size else 0.0, 1.0)
    return bool(np.allclose(matrix, matrix.conj().T, atol=tolerance * scale, rtol=0.0))


def check_internal_hermiticity(matrix: Matrix) -> Matrix:
    """Return the Hermitian part, REFUSING an operator above the window.

    THE `internal_hermiticity` GROUP B ROW, EXECUTED. Its words are: Hermiticity
    of an operator THIS MODULE FORMED -- a branch operator, a pinched power --
    before a spectral decomposition is taken of it; what the run then consumes
    is the HERMITIAN PART, which is Hermitian by construction, the window
    bounding the discarded anti-Hermitian half; ABOVE THE WINDOW THE OPERATOR IS
    REFUSED, NO SPECTRAL DECOMPOSITION BEING TAKEN OF IT.

    THE ROW LIVES HERE. The two DECLARED constraint-operator checks of the
    declaration validator are decided exactly, a declared predicate not being
    decided at a window, so they do not call :func:`is_hermitian`. Without this
    function the row would name a symbol nothing called and a fail-closed rule
    would be decided nowhere, while every formed operator reached
    :func:`hermitian_part` and had its anti-Hermitian half discarded in silence.
    This function is the fail-closed reading of the row.

    WHY THE GUARD IS NOT A REPAIR. The window bounds what is discarded; it does
    not license the discarding. An operator inside it is representation noise
    away from Hermitian and its Hermitian part is the operator the contract
    means; one outside it is a different operator, and no claim of this contract
    is stated about the Hermitian part of a non-Hermitian thing.

    SOME OF WHAT REACHES IT IS DECLARED, AND IT HAS BEEN DECIDED EXACTLY FIRST.
    Five call sites hand a DECLARED operator down to :func:`support_spectrum`:
    ``psd_power`` on a declared ``M_x`` and on a declared ``F_v`` block, and
    ``support_rank`` and ``psd_power`` on the declared ``tau_A`` in the
    one-factor :func:`~certiqs_key.meat_core.objective.choi.choi_parametrization`
    alone. The production frame and root of ``tau_A``
    (:func:`~certiqs_key.meat_core.objective.joint.marginal_frame`) do not come
    here: :data:`SUPPORT_CUTOFF` would drop a positive eigenvalue of
    ``tau_A`` and break ``eq:iota`` and ``eq:WWtau``. The row's
    words are about an operator this module formed, and they stay true because
    the ORDER makes them true: every entry point decides ``alice_povm_exact``,
    ``alice_marginal_exact``, ``bob_povm_admission`` and
    ``constraint_operator_exact`` -- exactly, at no window -- before anything
    is computed, so on those arguments this function's test cannot fail and
    :func:`hermitian_part` cannot discard anything. NO DEFECT IS MEASURED ON
    UNDECIDED DECLARED DATA and no declared predicate is decided here.
    A caller that reaches the objective functions directly, without going
    through an entry point, is inside the module's own API rather than on a
    fail-closed path, and what it meets here is a refusal above the window --
    the conservative direction, and never a silent symmetrization.

    Raises:
        HypothesisError: naming the measured defect, the window and the scale.
    """
    if not is_hermitian(matrix):
        scale = max(float(np.max(np.abs(matrix))) if matrix.size else 0.0, 1.0)
        defect = float(np.max(np.abs(matrix - matrix.conj().T)))
        raise HypothesisError(
            "the `internal_hermiticity` threshold row: an operator this module "
            f"FORMED has Hermiticity defect {defect!r} against a window of "
            f"{HERMITICITY_TOLERANCE!r} relative to its own scale {scale!r}. "
            "ABOVE THE WINDOW THE OPERATOR IS REFUSED, NO SPECTRAL "
            "DECOMPOSITION BEING TAKEN OF IT: what a run consumes below the "
            "window is the Hermitian part, whose discarded half the window "
            "BOUNDS, and above it there is nothing for that bound to say. IF "
            "THE OPERATOR IS ONE YOU DECLARED, THIS IS NOT THE RULE THAT "
            "DECIDED IT: every declared operator is decided EXACTLY and at no "
            "window, by validate_declaration, before any of this is computed "
            "(def:declaration), and a declared operator that failed there was "
            "refused with declaration_not_exactly_admissible naming its Group A "
            "row. What is refused here is an operator FORMED from data already "
            "admitted. It is not a repair either: nothing is symmetrized to "
            "make the check pass"
        )
    return hermitian_part(matrix)


def support_spectrum(matrix: Matrix) -> tuple[Vector, Matrix]:
    """Return the eigenvalues with kernel directions zeroed, and eigenvectors.

    The kernel decision is the contract's ``0^p = 0`` convention made
    executable: an eigenvalue at or below :data:`SUPPORT_CUTOFF` times the
    spectral radius is a kernel direction and is returned as exactly ``0.0``.
    Negative eigenvalues -- representation noise on a PSD input -- are treated
    the same way.

    THE ONE PLACE A SPECTRAL DECOMPOSITION IS TAKEN in this package, which is
    why the `internal_hermiticity` guard is here and nowhere else: every formed
    operator whose spectrum this contract reads --
    :func:`psd_power`, :func:`psd_trace_power`, :func:`support_rank` and
    :func:`is_positive_definite` -- reaches it through this function.
    """
    values, vectors = np.linalg.eigh(check_internal_hermiticity(matrix))
    radius = float(np.max(np.abs(values))) if values.size else 0.0
    floor = SUPPORT_CUTOFF * radius
    kept: Vector = np.where(values > floor, values, 0.0)
    return kept, np.asarray(vectors, dtype=np.complex128)


def psd_power(matrix: Matrix, exponent: float) -> Matrix:
    """Return ``matrix ** exponent`` by functional calculus, with ``0**p = 0``."""
    values, vectors = support_spectrum(matrix)
    powered = np.where(values > 0.0, values ** float(exponent), 0.0)
    return np.asarray((vectors * powered) @ vectors.conj().T, dtype=np.complex128)


def psd_trace_power(matrix: Matrix, exponent: float) -> float:
    """Return ``tr[matrix ** exponent]`` with the same kernel convention."""
    values, _ = support_spectrum(matrix)
    return float(np.sum(np.where(values > 0.0, values ** float(exponent), 0.0)))


def support_rank(matrix: Matrix) -> int:
    """Return the number of support directions under the cutoff."""
    values, _ = support_spectrum(matrix)
    return int(np.count_nonzero(values))


def factor_support(singular_values: npt.ArrayLike) -> npt.NDArray[np.bool_]:
    """Return which singular values of a factor ``A`` span its support.

    ``singular_values`` are those of ``A``; the mask keeps each one above
    :data:`FACTOR_SUPPORT_CUTOFF` times the largest. That is the
    ``support_cutoff`` row read on ``A A^dagger``, whose eigenvalues are the
    squares, so the support of a factor and the support of the operator it
    generates are decided by one ruler. An all-zero or empty input keeps
    nothing.
    """
    values = np.asarray(singular_values, dtype=np.float64)
    if values.size == 0:
        return np.zeros(0, dtype=np.bool_)
    largest = float(np.max(values))
    if largest == 0.0:
        return np.zeros(values.shape, dtype=np.bool_)
    return np.asarray(values > FACTOR_SUPPORT_CUTOFF * largest, dtype=np.bool_)


def is_positive_definite(matrix: Matrix) -> bool:
    """Return whether every eigenvalue survives the support cutoff."""
    values, _ = support_spectrum(matrix)
    return bool(values.size) and bool(np.all(values > 0.0))


def pinch(matrix: Matrix, labels: npt.NDArray[np.int64]) -> Matrix:
    """Apply the key pinching ``Z`` of contract Definition ``def:maps``.

    ``labels[i]`` is the raw-key value carried by basis index ``i``. ``Z`` keeps
    the entries whose two indices share a label and zeroes the rest, which is
    exactly ``sum_j Z_j X Z_j`` for ``Z_j`` the projector onto the indices
    labelled ``j``.
    """
    keep = labels[:, None] == labels[None, :]
    return np.asarray(matrix * keep, dtype=np.complex128)


def divided_difference(values: Vector, exponent: float) -> npt.NDArray[np.float64]:
    """Return the kernel ``f^{[1]}`` of contract Eq. ``eq:dk`` for ``f(x)=x^p``.

    ``f^{[1]}(l, m) = (l^p - m^p) / (l - m)`` off the diagonal and ``p l^{p-1}``
    on it. ``values`` must be strictly positive: the kernel is what
    differentiates the matrix power, and Theorem ``thm:gradient`` states it only
    where the argument is positive definite on the working face. Callers pass
    the SUPPORT spectrum, which is where the composite gradient of C12 lives
    (see :mod:`certiqs_key.meat_core.objective.gradient`).
    """
    if values.size and not bool(np.all(values > 0.0)):
        raise ValueError(
            "the divided-difference kernel of Eq. eq:dk is defined on a "
            "positive definite argument; pass the support spectrum"
        )
    powered = values ** float(exponent)
    numerator = powered[:, None] - powered[None, :]
    denominator = values[:, None] - values[None, :]
    diagonal = float(exponent) * values ** (float(exponent) - 1.0)
    # Eigenvalues that coincide, and eigenvalues that ``eigh`` separates only by
    # rounding noise, both take the derivative value: the difference quotient
    # loses every significant digit to cancellation there, and the kernel of
    # Eq. eq:dk is continuous across the diagonal, so this is a numerical
    # stabilization of the same function rather than a different one.
    scale = np.maximum(np.abs(values)[:, None], np.abs(values)[None, :])
    degenerate = np.abs(denominator) <= DEGENERACY_TOLERANCE * scale
    with np.errstate(divide="ignore", invalid="ignore"):
        quotient = np.where(
            degenerate, 0.0, numerator / np.where(degenerate, 1.0, denominator)
        )
    kernel = np.where(
        degenerate, np.broadcast_to(diagonal[:, None], quotient.shape), quotient
    )
    return np.asarray(kernel, dtype=np.float64)
