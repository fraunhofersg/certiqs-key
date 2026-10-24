"""A deliberately naive reference evaluator for the oracle registry.

WHAT THIS IS, AND WHAT IT IS NOT
================================
It is the *reproduction path* for the registry's golden values: dense, tiny,
eigendecomposition-based, and written straight off the displayed equations of
``contract.tex`` 0.4.0. It exists so that every number in ``registry.py`` can
be recomputed from a clean checkout with nothing but NumPy.

It is **not** an implementation of ``meat-core``, and nothing here may be
promoted into ``src/``. Specifically it contains

* no generation of protocol maps from a declaration (claims C1, C2 -- the toy
  Kraus operators are hand-written in ``toy_declarations.py`` instead);
* no Choi parametrization (C11) and no gradients (C12);
* no feasible-set construction and **no optimizer of any kind**. Every
  ``h_low`` in this registry is a hand-derived closed form; where the argmin
  claim is checked, it is checked by evaluating the objective on a grid of a
  one-parameter family, which is a check and not a solver.

THE AUTHORITY ORDER MATTERS
===========================
The hand derivation recorded with each registry entry is authoritative. This
module is a witness to it. When the two disagree the finding is reported and
resolved deliberately, with its derivation -- never by editing a golden value
to match what code produced (the oracle-freeze rule).

ADR-0003: no value here comes from MATLAB, OpenQKDSecurity, CVX, MOSEK or
Julia. Nothing is vendored; everything is recomputed.

Numerical note on ``X^{1/alpha}``
---------------------------------
``contract.tex`` Section 4.1 defines ``X^p`` by functional calculus on the
support of ``X`` and by ``0^p = 0`` on its kernel. That distinction is
load-bearing here: for ``p = 1/alpha < 1`` the map ``t -> t^p`` has infinite
slope at ``0``, so an eigenvalue that is numerically ``1e-17`` instead of ``0``
becomes ``1e-9`` after the power and pollutes ``T`` at the ninth digit. Every
power below therefore applies an explicit relative support cutoff.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import numpy.typing as npt

Matrix = npt.NDArray[np.float64]

#: Relative eigenvalue cutoff used to realise the contract's ``0^p = 0``
#: convention in floating point. Eigenvalues below ``SUPPORT_CUTOFF`` times the
#: spectral radius are treated as exactly zero, i.e. as kernel directions.
SUPPORT_CUTOFF = 1e-12


def _spectral(matrix: Matrix) -> tuple[npt.NDArray[np.float64], Matrix]:
    """Return the eigenvalues (kernel directions zeroed) and eigenvectors."""
    values, vectors = np.linalg.eigh(matrix)
    radius = float(np.max(np.abs(values))) if values.size else 0.0
    floor = SUPPORT_CUTOFF * max(radius, 1.0)
    return np.where(values > floor, values, 0.0), vectors


def psd_power(matrix: Matrix, exponent: float) -> Matrix:
    """Return ``matrix ** exponent`` by functional calculus, with ``0**p = 0``.

    contract.tex Section 4.1: "the power ``X^p`` is defined by functional
    calculus on the support of ``X`` and by ``0^p = 0`` on its kernel".
    """
    values, vectors = _spectral(matrix)
    powered = np.where(values > 0.0, values**exponent, 0.0)
    return np.asarray((vectors * powered) @ vectors.conj().T, dtype=np.float64)


def psd_trace_power(matrix: Matrix, exponent: float) -> float:
    """Return ``tr[matrix ** exponent]`` with the same kernel convention."""
    values, _ = _spectral(matrix)
    return float(np.sum(np.where(values > 0.0, values**exponent, 0.0)))


def key_pinch(matrix: Matrix, row_key_values: Sequence[int]) -> Matrix:
    """Apply the key pinching ``Z(tau) = sum_j Z_j tau Z_j`` (contract Def. def:maps).

    ``Z_j = |j><j|_R`` tensored with the identity on every other register, so
    ``Z`` keeps exactly those matrix entries whose two rows carry the same raw
    key value and zeroes the rest.
    """
    labels = np.asarray(row_key_values)
    keep = labels[:, None] == labels[None, :]
    return np.asarray(matrix * keep, dtype=np.float64)


def branch_operator(kraus: Sequence[Matrix], omega: Matrix) -> Matrix:
    """Return ``G(omega) = sum_kappa K_kappa omega K_kappa^dagger`` (Eq. eq:GTheta)."""
    if not kraus:
        return np.zeros((0, 0), dtype=np.float64)
    return np.asarray(
        sum(k @ omega @ k.conj().T for k in kraus),
        dtype=np.float64,
    )


def trace_power_pinched(
    branch: Matrix, alpha: float, row_key_values: Sequence[int]
) -> float:
    """Return ``T = tr[(Z(G^{1/alpha}))^alpha]`` (contract Eq. eq:fK).

    This is the single nonlinear ingredient of the contracted objective.
    """
    if branch.size == 0:
        return 0.0
    pinched = key_pinch(psd_power(branch, 1.0 / alpha), row_key_values)
    return psd_trace_power(pinched, alpha)


def sector_deficit(
    branch: Matrix, alpha: float, row_key_values: Sequence[int]
) -> float:
    """Return ``f_{chat,s} = T_{chat,s} - tr G_{chat,s}`` (contract Eq. eq:f-def).

    Corollary ``cor:f-nonpos``: this is ``<= 0`` always, and ``== 0`` exactly
    when ``G_{chat,s}`` is already block-diagonal for the key pinching.
    """
    if branch.size == 0:
        return 0.0
    return trace_power_pinched(branch, alpha, row_key_values) - float(np.trace(branch))


def k_from_identity(t_value: float, p_value: float, trace_g: float) -> float:
    """Return ``K = T + P - tr G`` (contract Eq. eq:fK)."""
    return t_value + p_value - trace_g


def relative_entropy_to_pinching(
    branch: Matrix, row_key_values: Sequence[int]
) -> float:
    """Return ``D(G || Z(G))`` in bits -- the summand of the C16 limit Eq. eq:oracle.

    contract.tex Section 4.18 records that this is always finite:
    ``supp G`` is contained in ``supp Z(G)``.
    """
    if branch.size == 0:
        return 0.0
    pinched = key_pinch(branch, row_key_values)

    def _plog(matrix: Matrix) -> Matrix:
        values, vectors = _spectral(matrix)
        logs = np.where(values > 0.0, np.log2(np.where(values > 0.0, values, 1.0)), 0.0)
        return np.asarray((vectors * logs) @ vectors.conj().T, dtype=np.float64)

    return float(np.real(np.trace(branch @ (_plog(branch) - _plog(pinched)))))


def divergence_kernel(u: float, v: float) -> float:
    """Return the extended kernel ``d(u, v) = u log2(u / v)`` of foundations/lem:kernel.

    Conventions of contract.tex Definition ``foundations/def:kl`` and Lemma
    ``foundations/lem:kernel``: ``d(0, v) = 0`` for every ``v >= 0`` (including
    ``v = 0``), and ``d(u, 0) = +inf`` for ``u > 0``. The kernel is jointly convex,
    lower semicontinuous, and non-increasing in ``v``.
    """
    if u < 0.0 or v < 0.0:
        raise ValueError(
            "the divergence kernel is defined on the non-negative quadrant"
        )
    if u == 0.0:
        return 0.0
    if v == 0.0:
        return math.inf
    return u * math.log2(u / v)


def objective(
    *,
    alpha: float,
    q: Mapping[str, float],
    p_chat: Mapping[str, float],
    k_chat: Mapping[str, float],
    chat_key: Sequence[str],
) -> float:
    """Return ``O_alpha(q, omega)`` of contract Eq. eq:objective.

    ``p_chat`` and ``k_chat`` carry ``P_chat(omega)`` and ``K_chat(omega)``;
    ``k_chat`` is read only for ``chat in chat_key``.
    """
    live = set(chat_key)
    total = 0.0
    for chat, weight in q.items():
        p_value = p_chat[chat]
        if chat not in live:
            total += (alpha / (alpha - 1.0)) * divergence_kernel(weight, p_value)
        else:
            total += divergence_kernel(weight, p_value)
            total += divergence_kernel(weight, k_chat[chat]) / (alpha - 1.0)
        if math.isinf(total):
            return math.inf
    return total


def branch_entropy(k_value: float, p_value: float, alpha: float) -> float:
    """Return ``H~down(Z | I Etilde)_{nu|chat} = (1/(1-alpha)) log2(K / P)``.

    contract.tex Theorem ``thm:branch-formula``, Eq. ``eq:c5``, valid for ``P_chat > 0``.
    """
    if p_value <= 0.0:
        raise ValueError("the branch formula of C5 requires P_chat > 0")
    if k_value <= 0.0:
        return math.inf
    return math.log2(k_value / p_value) / (1.0 - alpha)


def key_length(
    *,
    rounds: int,
    h_low: float,
    lambda_ec: int,
    eps_ev: float,
    eps_pa: float,
    alpha: float,
    ideal_hash: bool = True,
) -> int:
    """Return ``l_max`` of contract Remark rem:plus2 (the reported key length).

    ``l_max = max{0, floor(n h_low - lambda_EC - ceil(log2(1/eps_ev))
    - (alpha/(alpha-1)) log2(1/eps_pa) + 1)}``, where the floor and the clamp at
    zero are the platform's conservative integer-output rule, both in the safe
    direction.

    ``ideal_hash=False`` applies the one-bit penalty that Assumption ``A-HASH``
    records for a merely two-universal privacy-amplification family.

    Raises when ``h_low`` is ``+inf``: Remark ``rem:hlow-range`` requires the
    fail-closed branch there -- emit no key-length claim at all.
    """
    if not 1.0 < alpha < 2.0:
        raise ValueError(
            "req:key-length-alpha-domain: every key-length statement requires "
            "alpha in (1, 2)"
        )
    if not 0.0 < eps_pa <= 1.0 or not 0.0 < eps_ev <= 1.0:
        raise ValueError("eps_pa and eps_ev lie in (0, 1]")
    if lambda_ec < 0:
        raise ValueError("lambda_ec is a non-negative integer")
    if rounds < 1:
        raise ValueError("rounds >= 1")
    if math.isinf(h_low):
        raise ValueError(
            "h_low = +inf: no key-length claim may be emitted "
            "(contract.tex Remark rem:hlow-range, fail-closed branch)"
        )
    # log2(1/eps) is written -log2(eps): the same real number, and it does not
    # overflow for an eps below 2^-1024, where the literal 1.0/eps would become
    # inf and turn a finite deduction into a crash.
    bound = (
        rounds * h_low
        - lambda_ec
        - math.ceil(-math.log2(eps_ev))
        - (alpha / (alpha - 1.0)) * (-math.log2(eps_pa))
        + 1.0
    )
    if not ideal_hash:
        bound -= 1.0
    return max(0, math.floor(bound))


# ---------------------------------------------------------------------------
#  Eq. eq:defects -- the three operator-tolerance defects (C21, new at 0.5.0)
# ---------------------------------------------------------------------------
#
#  These reproduce contract.tex Definition ``def:optol``, Eq. ``eq:defects``,
#  and nothing else. They are here for the same reason ``psd_trace_power`` is:
#  every number the registry freezes must be recomputable from a clean checkout
#  with nothing but NumPy, and the HAND DERIVATION recorded with each frozen
#  case stays authoritative when the two disagree.
#
#  They are NOT an admission rule. Deciding ``Delta <= eps_dec``, ordering the
#  three refusals, and choosing the arithmetic those comparisons are made in
#  are the implementation's (``interface.yaml`` open choices OC-4 and OC-5),
#  and nothing here decides any of them.


ComplexMatrix = npt.NDArray[np.complex128]


def _complex(matrix: npt.ArrayLike) -> ComplexMatrix:
    """Return ``matrix`` as a complex square array.

    The families of contract Section 4.23 are not all real: a Hermiticity
    defect on a one-dimensional sector block is an imaginary part, so the
    defect evaluators cannot use this module's real ``Matrix`` alias.
    """
    array = np.asarray(matrix, dtype=np.complex128)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("a declared POVM element is a square matrix")
    return array


def operator_norm(matrix: npt.ArrayLike) -> float:
    """Return ``||matrix||``, the operator norm (largest singular value).

    contract.tex Section 3 fixes the unsubscripted ``||.||`` as exactly this;
    the trace and Frobenius norms are always subscripted there.
    """
    return float(np.linalg.norm(_complex(matrix), 2))


def hermitian_part(matrix: npt.ArrayLike) -> ComplexMatrix:
    """Return ``(F + F^dagger) / 2``, the Hermitian part of ``matrix``."""
    array = _complex(matrix)
    return np.asarray(0.5 * (array + array.conj().T), dtype=np.complex128)


def hermiticity_defects(family: Sequence[npt.ArrayLike]) -> tuple[float, ...]:
    """Return ``||F_v - F_v^dagger||`` for each ``v``, in the given order.

    The PER-OUTCOME vector that ``operator_tolerance_report`` carries and whose
    maximum is ``Delta_herm`` (contract Section 2.2; Eq. eq:defects).
    """
    return tuple(
        operator_norm(_complex(element) - _complex(element).conj().T)
        for element in family
    )


def negative_parts(family: Sequence[npt.ArrayLike]) -> tuple[float, ...]:
    """Return ``max{0, -lambda_min((F_v + F_v^dagger)/2)}`` for each ``v``.

    The second PER-OUTCOME vector of ``operator_tolerance_report``, whose
    maximum is ``Delta_pos``. The minimum is taken of the HERMITIAN PART, which
    is what makes the quantity real for a family that is not Hermitian.
    """
    values: list[float] = []
    for element in family:
        spectrum = np.linalg.eigvalsh(hermitian_part(element))
        values.append(max(0.0, -float(np.min(spectrum))))
    return tuple(values)


def completeness_defect(family: Sequence[npt.ArrayLike]) -> float:
    """Return ``||sum_v F_v - 1_Q||``, the completeness defect ``Delta_cpl``."""
    total = sum(_complex(element) for element in family)
    if not isinstance(total, np.ndarray):
        raise ValueError("the declared POVM is empty")
    return operator_norm(total - np.eye(total.shape[0], dtype=np.complex128))


def defects(family: Sequence[npt.ArrayLike]) -> tuple[float, float, float]:
    """Return ``(Delta_herm, Delta_pos, Delta_cpl)`` of Eq. ``eq:defects``.

    All three are non-negative by construction, and all three vanish exactly
    when the family is a block-diagonal POVM (contract Lemma ``lem:optol-zero``
    -- the block-diagonality half is condition (T), decided elsewhere and never
    within a tolerance).
    """
    return (
        max(hermiticity_defects(family)),
        max(negative_parts(family)),
        completeness_defect(family),
    )


def block_diagonality_defect(
    matrix: npt.ArrayLike, sector_dims: Sequence[int]
) -> float:
    """Return ``||F - Pin_S(F)||`` for the declared sector decomposition.

    A DIAGNOSTIC ONLY, and the contract says so in as many words: condition (T)
    of Definition ``def:optol`` is "decided EXACTLY and never within a
    tolerance", and Remark ``rem:optol-reach`` (a) records that this defect
    "can of course be written down" while what cannot be written down is what
    the statements consuming the decomposition would say about an operator that
    is only nearly block-diagonal. It exists so that a frozen (T)-violating
    family can record HOW FAR from block-diagonal it is without any suggestion
    that the number is compared against ``eps_dec``.
    """
    array = _complex(matrix)
    projected = np.zeros_like(array)
    offset = 0
    for dimension in sector_dims:
        stop = offset + dimension
        projected[offset:stop, offset:stop] = array[offset:stop, offset:stop]
        offset = stop
    if offset != array.shape[0]:
        raise ValueError("the sector dimensions do not sum to the matrix dimension")
    return operator_norm(array - projected)
