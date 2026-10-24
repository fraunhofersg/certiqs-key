"""The three-term objective ``O_alpha`` and the feasible set ``W``.

contract.tex Definition ``def:feasible``, Eq. ``eq:objective``::

    O_alpha(q, omega) = (alpha/(alpha-1)) sum_{chat not in Chat_key} d(q, P)
                      + sum_{chat in Chat_key} [ d(q, P) + d(q, K)/(alpha-1) ]

with ``d`` the extended kernel of Lemma ``foundations/lem:kernel`` and ``h_low`` the
infimum of ``O_alpha`` over ``AcceptSet x W`` (Eq. ``eq:hlow-def``).

Two properties of this function drive every design choice downstream.

* It is **extended-real**. ``d(u, 0) = +inf`` for ``u > 0``, so an acceptance
  vector that is not absolutely continuous with respect to the reachable
  statistics gives ``+inf`` -- and Remark ``rem:hlow-range`` requires an
  implementation to propagate that value and never clamp it. The output domain
  of ``h_low`` is ``[0, +inf]``.
* It is **jointly convex and lower semicontinuous** (Theorem ``thm:convexity``,
  C9b), because ``d`` is jointly convex, lsc and non-increasing in its second
  argument while ``K_chat`` is concave (C9a). Evaluating it at a feasible point
  bounds ``h_low`` from ABOVE, never from below, so a value computed here is an
  ESTIMATE, and ``lem:estimate`` is the whole of its warrant. A LOWER bound is
  what a SOLVER SUBMODULE supplies, docking at ``lem:estimate`` and
  ``cor:keylength-bound`` with its own bound and its own trust root -- for the
  submodule this repository carries, :mod:`certiqs_key.solvers.frank_wolfe` --
  and never by reading this function's output.

The Renyi order is checked against ``(1, inf)`` here: claims C3-C12, C16 and
C17 hold on that interval and only a KEY-LENGTH statement is confined to
``(1, 2)`` (``req:key-length-alpha-domain``). The narrower guard lives in
:mod:`certiqs_key.meat_core.finitekey.keylength`, where it belongs.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np

from certiqs_key.domain.manifest import ConstraintRelation
from certiqs_key.foundations.kernel import divergence_kernel
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.branch import (
    BranchValues,
    GeneratedMaps,
    evaluate_branches,
)
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix, hermitian_part

#: Absolute tolerance for the feasibility checks of Eq. ``eq:feas``. Applied to
#: quantities of order one (a normalized state and its marginal).
FEASIBILITY_TOLERANCE = 1e-9


def check_alpha_structural(alpha: float) -> None:
    """Raise unless ``alpha`` lies in the structural domain ``(1, inf)``.

    ``req:objective-alpha-domain``. Claims C3-C12, C16 and C17 hold for
    ``alpha in (1, inf)``; the endpoint ``alpha = inf`` is not defined by
    Definition ``foundations/def:renyi`` and no claim uses it.
    """
    if not math.isfinite(alpha) or alpha <= 1.0:
        raise ValueError(
            "Requirement req:objective-alpha-domain: the structural claims of "
            f"this contract hold for alpha in (1, inf); got alpha={alpha!r}"
        )


def objective_from_branches(
    *,
    alpha: float,
    q: Mapping[str, float],
    values: Mapping[str, BranchValues],
    chat_key: tuple[str, ...],
) -> float:
    """Return ``O_alpha(q, omega)`` from precomputed branch values.

    Split out so that the objective can be evaluated from ``P`` and ``K`` alone
    -- which is what makes the state form and the Choi form of C11 comparable
    term by term.
    """
    check_alpha_structural(alpha)
    live = set(chat_key)
    total = 0.0
    for chat, weight in q.items():
        value = values[chat]
        if chat in live:
            total += divergence_kernel(weight, value.p)
            total += divergence_kernel(weight, value.k) / (alpha - 1.0)
        else:
            total += (alpha / (alpha - 1.0)) * divergence_kernel(weight, value.p)
        if math.isinf(total):
            return math.inf
    return total


def objective_value(
    maps: GeneratedMaps,
    q: Mapping[str, float],
    omega: Mapping[str, Matrix],
    alpha: float,
) -> float:
    """Return ``O_alpha(q, omega)`` of Eq. ``eq:objective`` at a feasible point.

    The value is an extended real: ``+inf`` is a legitimate return, never an
    error and never clamped (Remark ``rem:hlow-range``).
    """
    values = evaluate_branches(maps, omega, alpha)
    return objective_from_branches(
        alpha=alpha, q=q, values=values, chat_key=maps.chat_key
    )


def acceptance_vector(declaration: ProtocolDeclaration) -> dict[str, float]:
    """Return the accepted frequency vector ``q`` of a singleton acceptance set."""
    return dict(
        zip(
            declaration.acceptance_values,
            declaration.acceptance_set.frequencies,
            strict=True,
        )
    )


def constraint_value(
    declaration: ProtocolDeclaration, index: int, omega: Mapping[str, Matrix]
) -> Matrix:
    """Return ``tr_Q[(1_A x O_k) omega]`` as an operator on ``A``.

    The TRUSTED-source-mode left-hand side of one entry of the declared list
    ``L`` (Eq. ``eq:feas-modes``, trusted row). ``O_k`` is
    sector-block-diagonal by def:admissible-declaration (iii), so the partial trace is a
    sum over sectors. The untrusted-mode left-hand side is the SCALAR
    :func:`scalar_constraint_value`, not this operator's trace read as an
    operator condition.
    """
    entry = declaration.constraint_list[index]
    d_a = declaration.alice_dim
    out = np.zeros((d_a, d_a), dtype=np.complex128)
    for sector in declaration.sector_index_set:
        width = declaration.sector_dims[sector]
        operator = as_matrix(entry.operator_blocks[sector])
        block = np.asarray(omega[sector], dtype=np.complex128)
        # tr_{Q_s}[(1_A x O^{(s)}) omega_s] with the A factor first.
        reshaped = block.reshape(d_a, width, d_a, width)
        out = out + np.einsum("qp,apbq->ab", operator, reshaped)
    return np.asarray(out, dtype=np.complex128)


def scalar_constraint_value(
    declaration: ProtocolDeclaration, index: int, omega: Mapping[str, Matrix]
) -> float:
    """Return ``tr[(1_A x O_k) omega]``, the UNTRUSTED-mode left-hand side.

    Eq. ``eq:feas-modes``, untrusted row, and Eq. ``eq:choi-feas-un``: a real
    number compared with the declared real ``c_k`` (Definition ``def:homog``
    (b)). This is the FULL trace, over ``A`` as well as ``Q`` -- in
    untrusted-source mode ``A`` is an output of Eve's channel, so Lemma
    ``lem:range`` (i) transports only the trace identity ``eq:transport-un`` and
    there is no operator-valued analogue.
    """
    entry = declaration.constraint_list[index]
    total = 0.0
    for sector in declaration.sector_index_set:
        operator = as_matrix(entry.operator_blocks[sector])
        block = np.asarray(omega[sector], dtype=np.complex128)
        lifted = np.kron(np.eye(declaration.alice_dim, dtype=np.complex128), operator)
        total += float(np.real(np.trace(lifted @ block)))
    return total


def _scalar_relation_holds(
    relation: ConstraintRelation, difference: float, tolerance: float
) -> bool:
    """Return whether a real difference satisfies the declared relation.

    def:admissible-declaration (vi): in untrusted-source mode the same three machine
    keys denote the ORDER OF THE REALS. ``difference`` is ``lhs - c_k``.
    """
    if relation is ConstraintRelation.SUCCEQ:
        return difference >= -tolerance
    if relation is ConstraintRelation.PRECEQ:
        return difference <= tolerance
    return abs(difference) <= tolerance


def _relation_holds(
    relation: ConstraintRelation, difference: Matrix, tolerance: float
) -> bool:
    """Return whether ``difference`` satisfies the declared operator relation.

    ``difference`` is ``lhs - Theta_k``. ``preceq`` asks for it to be negative
    semidefinite, ``succeq`` for positive semidefinite, ``eq`` for zero. The
    raw spectrum is used rather than the support spectrum: a violation is
    exactly what must not be rounded away here.
    """
    raw, _ = np.linalg.eigh(hermitian_part(difference))
    if relation is ConstraintRelation.SUCCEQ:
        return bool(np.all(raw >= -tolerance))
    if relation is ConstraintRelation.PRECEQ:
        return bool(np.all(raw <= tolerance))
    return bool(np.max(np.abs(difference)) <= tolerance) if difference.size else True


def check_feasible(
    declaration: ProtocolDeclaration,
    omega: Mapping[str, Matrix],
    *,
    tolerance: float = FEASIBILITY_TOLERANCE,
) -> None:
    """Raise unless ``omega`` lies in the feasible set of Eq. ``eq:feas``.

    The conditions, in the contract's order: sector-block-diagonality
    (structural here, since the state is *held* as blocks), ``tr omega = 1``,
    the marginal condition, and every entry of the declared constraint list.
    Positivity of each block is checked too -- the feasible set is a subset of
    the PSD cone.

    ``tr omega = 1`` is checked EXPLICITLY and unconditionally, which is
    Eq. ``eq:feas``'s own emphasis: in trusted-source mode it follows from
    ``omega_A = tau_A``, "but that derivation is unavailable in untrusted-source
    mode, where normalization is the ONLY unconditional constraint the feasible
    set carries". Leaving it implied would empty the untrusted-mode program of
    its one defining condition.

    The marginal and constraint rows are then read per mode
    (Eq. ``eq:feas-modes``): ``omega_A = tau_A`` and operator entries in
    trusted-source mode; no marginal condition and SCALAR entries in
    untrusted-source mode.
    """
    d_a = declaration.alice_dim
    marginal = np.zeros((d_a, d_a), dtype=np.complex128)
    for sector in declaration.sector_index_set:
        width = declaration.sector_dims[sector]
        block = np.asarray(omega[sector], dtype=np.complex128)
        expected = (d_a * width, d_a * width)
        if block.shape != expected:
            raise DeclarationError(
                f"sector {sector!r}: state block has shape {block.shape}, "
                f"expected {expected} for A (x) Q_s with the A factor first"
            )
        raw, _ = np.linalg.eigh(hermitian_part(block))
        if bool(np.any(raw < -tolerance)):
            raise DeclarationError(
                f"sector {sector!r}: state block is not positive semidefinite "
                f"(minimum eigenvalue {float(np.min(raw)):.3e})"
            )
        marginal = marginal + np.einsum(
            "aqbq->ab", block.reshape(d_a, width, d_a, width)
        )
    trace = float(np.real(np.trace(marginal)))
    if abs(trace - 1.0) > tolerance:
        raise DeclarationError(
            f"Eq. eq:feas: tr omega = {trace!r}, not 1. The contract writes this "
            "condition explicitly and does not derive it: in untrusted-source "
            "mode it is the only unconditional constraint the feasible set "
            "carries"
        )
    if declaration.is_trusted_source:
        tau = declaration.trusted_marginal
        if not bool(np.allclose(marginal, tau, atol=tolerance, rtol=0.0)):
            raise DeclarationError(
                "Eq. eq:feas-modes (trusted): the A-marginal of omega is not "
                "the trusted marginal tau_A (maximum deviation "
                f"{float(np.max(np.abs(marginal - tau))):.3e})"
            )
    for index, entry in enumerate(declaration.constraint_list):
        if declaration.is_trusted_source:
            difference = constraint_value(declaration, index, omega) - as_matrix(
                entry.operator_bound
            )
            satisfied = _relation_holds(entry.relation, difference, tolerance)
        else:
            residual = (
                scalar_constraint_value(declaration, index, omega) - entry.scalar_bound
            )
            satisfied = _scalar_relation_holds(entry.relation, residual, tolerance)
        if not satisfied:
            raise DeclarationError(
                f"Eq. eq:feas-modes: constraint {index} ({entry.relation.value}) "
                "is violated at this state"
            )
