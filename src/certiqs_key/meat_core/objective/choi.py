"""The Choi reformulation of C11 (Theorem ``thm:choi``), in both source modes.

TRUSTED-SOURCE MODE (Theorem ``thm:choi``)
==========================================
contract.tex Eq. ``eq:iota`` fixes an isometry ``iota : A_0 -> A`` onto
``supp tau_A``, Eq. ``eq:Wtau`` sets ``W_tau = tau_A^{1/2} iota``, and Lemma
``lem:choi-marginal`` shows that

    chi(J) = (W_tau x 1) J (W_tau^dagger x 1)

is a bijection from ``{J >= 0 : tr_Q J = 1_{A_0}}`` onto
``{omega >= 0 : tr_Q omega = tau_A}``. Theorem ``thm:choi`` restricts it to
sector-block-diagonal operators and states the resulting program
Eq. ``eq:choi-program`` -- an **exact** reformulation, not a relaxation, jointly
convex with affine or conic constraints.

Ordering, from the ``choi_ordering`` convention of the conventions and Remark
``rem:ordering``: each ``J_s`` lives on ``A_0 (x) Q_s`` with the **input factor
A_0 first**; the coupling constraint is ``sum_s tr_{Q_s} J_s = 1_{A_0}``, so the
branches are generally trace-non-increasing and only their sum is
trace-preserving; every declared sector, one-dimensional flag sectors included,
is treated uniformly as an output sector of the parametrized channel.

A SINGULAR ``tau_A`` IS ADMISSIBLE, AND ITS BASIS IS RECORDED
=============================================================
The `inputs` table admits a singular ``tau_A``; then ``d_{A_0} = rank tau_A < d_A`` and
``iota`` is a genuine choice. The contract "deliberately names none" as
canonical and Remark ``rem:basis-invariance`` proves in four steps that the
choice is immaterial to ``h_low``, ``key_length`` and ``sector_report``, while
the reported ``J_s`` and the channel reading of Remark ``rem:ordering`` are
relative to it. the conventions therefore requires exactly two things of an
implementation, and both are done here:

* it **must not refuse** a singular ``tau_A`` "on the ground that the contract
  names no canonical basis";
* it **must record** the ``iota`` it used, as
  ``optimizer_certificate.choi_input_basis``, whenever ``rank tau_A < d_A``.

:func:`choi_parametrization` accepts an explicit ``iota`` and otherwise fixes a
deterministic one
(:func:`~certiqs_key.meat_core.declaration.declaration.support_isometry`),
validating either against Eq. ``eq:iota``.

UNTRUSTED-SOURCE MODE (Definition ``def:untrusted-choi``)
=========================================================
"In untrusted-source mode there is no marginal to fix, so there is nothing to
reparametrize and the Choi step is the identity. This is the degenerate case of
Theorem ``thm:choi``, not a second program." Accordingly ``chi = id``,
``J = omega``, ``J_s = omega_s``, there is no ``A_0``, no ``iota`` and no
``W_tau``, and the ``choi_input_basis`` field is ABSENT.

The one thing that must not be done is spelled out in the contract and is
enforced by :class:`Coupling` here: the untrusted program is **not** obtained by
substituting ``W_tau = 1_A`` into Eq. ``eq:choi-feas``. That substitution would
give ``sum_s tr_{Q_s} omega_s = 1_A`` -- ``omega_A`` fixed to the *unnormalized*
identity, an infeasible condition and the operator form the licence does not
supply (Remark ``rem:homog`` (a)). The coupling constraint that binds the sector
blocks in untrusted-source mode is the single SCALAR equation
``sum_s tr omega_s = 1`` of Eq. ``eq:choi-feas-un``. The two coupling forms are
therefore separate members of an enum rather than one formula with a
substituted matrix, so the mistake has no expression in this module.

At ``d_A = 1`` the two coincide: ``1_{A_0} = [1]`` and
``sum_s tr_{Q_s} J_s = 1_{A_0}`` *is* ``sum_s tr omega_s = 1`` (Remark
``rem:modes-da1`` (b4)).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from certiqs_key.meat_core import thresholds
from certiqs_key.meat_core.declaration.declaration import (
    ProtocolDeclaration,
    SourceMode,
    support_isometry,
)
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.branch import GeneratedMaps
from certiqs_key.meat_core.objective.linalg import (
    Matrix,
    as_matrix,
    psd_power,
    support_rank,
)
from certiqs_key.meat_core.objective.objective import objective_value
from certiqs_key.meat_core.reasons import RefusalReason

#: How close a supplied ``iota`` must come to Eq. ``eq:iota``. Tight: the two
#: identities are exact statements about an isometry, and a drifting one is a
#: defect in the caller rather than something to absorb.
ISOMETRY_TOLERANCE = thresholds.declared(thresholds.CHOI_ISOMETRY)


class Coupling(StrEnum):
    """Which coupling constraint binds the sector blocks (lem:choi-marginal).

    The two are not two spellings of one condition; see the module docstring.
    """

    #: ``sum_s tr_{Q_s} J_s = 1_{A_0}`` -- Eq. ``eq:choi-feas``, trusted mode.
    INPUT_IDENTITY = "input_identity"
    #: ``sum_s tr omega_s = 1`` -- Eq. ``eq:choi-feas-un``, untrusted mode.
    UNIT_TRACE = "unit_trace"


@dataclass(frozen=True)
class ChoiParametrization:
    """The map ``chi`` of lem:choi-marginal, in whichever mode the declaration is in.

    ``input_dim`` is ``dim A_0 = rank tau_A`` in trusted-source mode and ``d_A``
    in untrusted-source mode, where the "input factor" of a block is the ``A``
    factor of ``omega_s`` itself and ``chi`` is the identity.

    ``iota`` is the declared isometry of Eq. ``eq:iota`` in trusted-source mode
    and ``None`` in untrusted-source mode, where the contract defines none.
    """

    declaration: ProtocolDeclaration
    w_tau: Matrix
    w_pinv: Matrix
    input_dim: int
    coupling: Coupling
    iota: Matrix | None

    @property
    def source_mode(self) -> SourceMode:
        """Return the declared source mode this parametrization was built for."""
        return self.declaration.source_mode

    @property
    def is_identity(self) -> bool:
        """Return whether ``chi`` is the identity.

        Definition ``def:untrusted-choi``.
        """
        return self.coupling is Coupling.UNIT_TRACE

    @property
    def records_input_basis(self) -> bool:
        """Return whether ``choi_input_basis`` must be reported.

        the `outputs` table and the conventions: whenever the declaration is in
        trusted-source mode with ``rank tau_A < d_A``. For a nonsingular
        ``tau_A`` one may take ``iota = 1_A`` and the declared basis of ``A``
        serves; in untrusted-source mode there is no input register at all.
        """
        return self.iota is not None and self.input_dim < self.declaration.alice_dim

    def chi(self, sector: str, choi_block: Matrix) -> Matrix:
        """Return ``omega_s = (W x 1) J_s (W^dagger x 1)`` (Lemma lem:choi-marginal)."""
        width = self.declaration.sector_dims[sector]
        lift = np.kron(self.w_tau, np.eye(width, dtype=np.complex128))
        return np.asarray(lift @ choi_block @ lift.conj().T, dtype=np.complex128)

    def chi_inverse(self, sector: str, state_block: Matrix) -> Matrix:
        """Return ``J_s`` from ``omega_s``, the inverse of :meth:`chi`."""
        width = self.declaration.sector_dims[sector]
        drop = np.kron(self.w_pinv, np.eye(width, dtype=np.complex128))
        return np.asarray(drop @ state_block @ drop.conj().T, dtype=np.complex128)

    def chi_adjoint(self, sector: str, operator: Matrix) -> Matrix:
        """Return ``chi^dagger(A) = (W^dagger x 1) A (W x 1)``.

        The adjoint in the Hilbert-Schmidt inner product, which is what turns a
        state-form gradient into a Choi-form one (Corollary
        ``cor:full-gradient``). In untrusted-source mode ``W_tau`` is the
        identity and this is the identity map, which is exactly what
        Eq. ``eq:grad-pieces-un`` says: the pieces lose their ``W_tau``
        conjugation.
        """
        width = self.declaration.sector_dims[sector]
        lift = np.kron(self.w_tau, np.eye(width, dtype=np.complex128))
        return np.asarray(lift.conj().T @ operator @ lift, dtype=np.complex128)

    def state_from_choi(self, choi: Mapping[str, Matrix]) -> dict[str, Matrix]:
        """Return the block-diagonal state ``omega`` of a Choi point."""
        return {
            sector: self.chi(sector, as_matrix(choi[sector]))
            for sector in self.declaration.sector_index_set
        }

    def choi_from_state(self, omega: Mapping[str, Matrix]) -> dict[str, Matrix]:
        """Return the Choi point of a block-diagonal feasible state."""
        return {
            sector: self.chi_inverse(sector, as_matrix(omega[sector]))
            for sector in self.declaration.sector_index_set
        }


def channel_action(
    parametrization: ChoiParametrization,
    sector: str,
    choi_block: Matrix,
    state: Matrix,
) -> Matrix:
    """Return ``E_s(rho) = tr_{A_0}[(rho^T x 1_{Q_s}) J_s]`` (Remark rem:ordering).

    The interpretive reading of a Choi block, and the only place the transpose
    basis is used. No derivation of the contract uses this map and no quantity
    computed by this package depends on it; it is written out because Remark
    ``rem:ordering`` requires the implementation to fix the transpose basis and
    the factor order exactly as declared, and the honest way to fix them is to
    write down the map they define.

    The transpose is taken in the DECLARED BASIS of ``A_0``: "the columns of the
    declared isometry ``iota`` ... written in the input basis of ``A``". Remark
    ``rem:ordering`` records that the channel is pinned down only up to the
    unitary relabelling of its input that a different ``iota`` induces, which is
    why the declared ``iota`` is recorded beside any reported ``J_s``.
    """
    declaration = parametrization.declaration
    width = declaration.sector_dims[sector]
    input_dim = parametrization.input_dim
    transposed = np.asarray(state, dtype=np.complex128).T
    block = np.asarray(choi_block, dtype=np.complex128).reshape(
        input_dim, width, input_dim, width
    )
    return np.asarray(np.einsum("ba,aqbr->qr", transposed, block), dtype=np.complex128)


class ChoiIsometryError(DeclarationError):
    """A frame this module cannot verify exactly: the ``choi_isometry`` row.

    A subclass of :class:`~certiqs_key.meat_core.errors.DeclarationError` because it IS
    one -- no result is produced -- carrying the machine-readable reason
    the conventions spells so that a caller need not read prose to learn which row
    refused.
    """

    reason = RefusalReason.CHOI_ISOMETRY_INEXACT


def check_declared_isometry(iota: Matrix, tau: Matrix, alice_dim: int) -> None:
    """Raise unless ``iota`` is a TIGHT frame for ``tau``: stricter than ``eq:iota``.

    ``iota^dagger iota = 1_{A_0}`` and ``iota iota^dagger = Pi_{supp tau_A}``:
    an isometry ONTO the support, not merely into it as Eq. ``eq:iota`` asks.
    The tightness is required by the one-factor parametrization's two-sided
    inverse (below); the contract names no frame canonical.

    STRICTER THAN ``eq:iota``, AND WHY. Eq. ``eq:iota``
    asks only that the frame CONTAIN the support; this function also demands a
    TIGHT frame, and to decide it computes ``rank tau_A`` from an
    eigendecomposition (:func:`support_rank`, and the projector compared
    below). The demand serves :class:`ChoiParametrization`, whose
    :meth:`~ChoiParametrization.chi_inverse` is the two-sided inverse
    ``W^+ = (W^dagger W)^{-1} W^dagger`` that ``lem:choi-marginal`` gives only
    on a tight frame; a non-tight frame would make that Gram matrix singular.
    No claim needs the tightness: the lemma, ``thm:choi`` and the one driver's
    frames (:func:`~certiqs_key.meat_core.objective.joint.joint_choi_parametrization`,
    which never calls this function) hold on any containing frame. So this
    function refuses frames the lemma admits, which is the conservative
    direction, and it is reached only by the one-factor parametrization.

    AT EXACTLY 0, AND THAT IS A REAL NARROWING. Contract Section
    2.6's ``choi_isometry`` row declares the window "exactly 0, entrywise, as
    binary64 data; NO DECLARED NUMBER", and says what makes that reachable:
    "BOTH CONSTRUCTIONS OF SECTION 4.13 MEET IT BY {0, 1} ARITHMETIC; anything
    else is refused with ``choi_isometry_inexact``." A frame whose entries are
    not 0 and 1 -- a Hadamard basis, say, whose ``1/sqrt 2`` entries do not
    close in binary64 -- is REFUSED, where a ``1e-10`` window would
    admit it.

    WHAT IS NOT WITHDRAWN. Remark ``rem:basis-invariance`` is untouched:
    ``h_low``, ``key_length`` and ``sector_report`` do not depend on which
    admissible frame is used, and that is a statement about REAL numbers which
    no window of this module can affect. What is withdrawn is this module's
    ability to CONSUME a frame it cannot verify exactly -- and the remedy is
    the same one lem:choi-marginal already gives: use a construction that exhibits
    the frame exactly.

    Raises:
        ChoiIsometryError: carrying ``choi_isometry_inexact``, which is one of
            the seventeen machine-readable strings of the conventions.
    """
    matrix = as_matrix(iota) if iota.shape[0] == iota.shape[1] else np.asarray(iota)
    rank = support_rank(tau)
    if matrix.shape != (alice_dim, rank):
        raise DeclarationError(
            f"Eq. eq:iota: iota has shape {matrix.shape}, expected "
            f"({alice_dim}, {rank}) for a map A_0 -> A with "
            f"d_{{A_0}} = rank tau_A = {rank}"
        )
    identity = matrix.conj().T @ matrix
    if not np.allclose(
        identity, np.eye(rank, dtype=np.complex128), atol=ISOMETRY_TOLERANCE, rtol=0.0
    ):
        raise ChoiIsometryError(
            "contract Eq. eq:iota and `declared_thresholds` "
            "(choi_isometry): "
            "iota^dagger iota - 1_{A_0} is not EXACTLY 0 as binary64 data "
            f"(worst entry {float(np.max(np.abs(identity - np.eye(rank)))):.3e}). "
            "This check requires a TIGHT frame, of dimension rank tau_A, which "
            "is stricter than eq:iota and is required by the one-factor "
            "parametrization's two-sided inverse chi_inverse. "
            "The row declares no number and admits no window: 'both "
            "constructions of lem:choi-marginal meet it by {0, 1} ARITHMETIC, and "
            "anything else is refused'. Remark rem:basis-invariance is "
            "untouched -- h_low does not depend on which admissible frame is "
            "used -- but a frame this module cannot verify exactly is one it "
            "does not consume"
        )
    projector = matrix @ matrix.conj().T
    values, vectors = np.linalg.eigh(np.asarray(tau, dtype=np.complex128))
    # THE marginal_support_floor ROW IS NOT CARRIED (`declared_thresholds`,
    # Group C):
    # "NO RUN NEEDS THE RANK -- Eq. eq:iota asks the Choi input register only
    # to CONTAIN the support, the identity W_tau W_tau^dagger = tau_A then
    # holds for every admissible frame, and Theorem thm:choi maps Feas^J onto
    # Feas in each, so the value is the same and the truncation the row would
    # decide HAS NO SITE." That is true of eq:iota and of the one driver. What
    # is left HERE is the tightness demand of the docstring: the CHECK that a
    # DECLARED iota projects onto the support, at the choi_isometry window --
    # exactly 0 -- against a support read off a computed spectrum
    # (values > 0), as the shape check above reads support_rank. That is a
    # rank decision, and eq:iota alone would need none.
    floor = 0.0
    keep = vectors[:, values > floor]
    expected = keep @ keep.conj().T
    if not np.allclose(projector, expected, atol=ISOMETRY_TOLERANCE, rtol=0.0):
        raise ChoiIsometryError(
            "contract Eq. eq:iota and `declared_thresholds` "
            "(choi_isometry): "
            "iota iota^dagger is not EXACTLY the projector onto supp tau_A as "
            "binary64 data. This check requires a TIGHT frame -- the declared "
            "basis must span the support exactly, any orthonormal basis OF THE "
            "SUPPORT and no other -- which is stricter than eq:iota (a frame "
            "CONTAINING the support) and is required by the one-factor "
            "parametrization's two-sided inverse chi_inverse; the row admits "
            "no window"
        )


def choi_parametrization(
    declaration: ProtocolDeclaration, *, iota: Matrix | None = None
) -> ChoiParametrization:
    """Return the parametrization of lem:choi-marginal for a validated declaration.

    In UNTRUSTED-source mode this is the identity of Definition
    ``def:untrusted-choi``: ``chi = id``, ``J_s = omega_s``, no ``A_0`` and no
    ``iota``, with the scalar coupling :attr:`Coupling.UNIT_TRACE`. Supplying an
    ``iota`` there is an error rather than a no-op, because the contract defines
    no input register to declare a basis of.

    In TRUSTED-source mode ``iota`` defaults to the deterministic support basis
    of :func:`~certiqs_key.meat_core.declaration.declaration.support_isometry`; any
    orthonormal basis of ``supp tau_A`` may be supplied instead and is validated
    against Eq. ``eq:iota``. A singular ``tau_A`` is accepted -- the conventions
    forbids refusing one -- and the ``iota`` used is available for the
    ``choi_input_basis`` record.

    Raises:
        DeclarationError: if an ``iota`` is supplied in untrusted-source mode,
            or if the supplied ``iota`` fails Eq. ``eq:iota``.
    """
    if declaration.alice_marginal is None:
        if iota is not None:
            raise DeclarationError(
                "Definition def:untrusted-choi (a): in untrusted-source mode the "
                "Choi step is the identity -- there is no A_0 and no iota, so "
                "there is no declared basis to supply"
            )
        identity = np.eye(declaration.alice_dim, dtype=np.complex128)
        return ChoiParametrization(
            declaration=declaration,
            w_tau=identity,
            w_pinv=identity,
            input_dim=declaration.alice_dim,
            coupling=Coupling.UNIT_TRACE,
            iota=None,
        )

    tau = declaration.trusted_marginal
    declared = support_isometry(tau) if iota is None else np.asarray(iota)
    check_declared_isometry(declared, tau, declaration.alice_dim)
    root = psd_power(tau, 0.5)
    w_tau = np.asarray(root @ declared, dtype=np.complex128)
    # W^+ = (W^dagger W)^{-1} W^dagger (lem:choi-marginal). W has full
    # COLUMN rank, since tau_A is positive definite on its support and iota maps
    # onto that support, so the inverse exists exactly.
    gram = w_tau.conj().T @ w_tau
    w_pinv = np.asarray(np.linalg.inv(gram) @ w_tau.conj().T, dtype=np.complex128)
    return ChoiParametrization(
        declaration=declaration,
        w_tau=w_tau,
        w_pinv=w_pinv,
        input_dim=int(declared.shape[1]),
        coupling=Coupling.INPUT_IDENTITY,
        iota=np.asarray(declared, dtype=np.complex128),
    )


def choi_objective_value(
    maps: GeneratedMaps,
    parametrization: ChoiParametrization,
    q: Mapping[str, float],
    choi: Mapping[str, Matrix],
    alpha: float,
) -> float:
    """Return the objective of Eq. ``eq:choi-program`` at a Choi point.

    Theorem ``thm:choi`` states the reformulation is EXACT, so this is the
    state-form objective at ``omega = chi(J)`` -- computed that way rather than
    re-derived, so that the exactness claim is a testable identity between two
    call paths rather than a duplicated formula. In untrusted-source mode
    ``chi`` is the identity and Definition ``def:untrusted-choi`` (c) says the value
    is ``h_low`` of Eq. ``eq:hlow-def`` "by definition rather than by a
    theorem"; the same call path computes it.
    """
    return objective_value(maps, q, parametrization.state_from_choi(choi), alpha)


def coupling_residual(
    parametrization: ChoiParametrization, choi: Mapping[str, Matrix]
) -> float:
    """Return how far a point misses its mode's coupling constraint.

    ``|| sum_s tr_{Q_s} J_s - 1_{A_0} ||_max`` for Eq. ``eq:choi-feas``, and
    ``| sum_s tr omega_s - 1 |`` for Eq. ``eq:choi-feas-un``. The second is not
    the first with ``W_tau = 1_A`` substituted; see the module docstring.
    """
    declaration = parametrization.declaration
    if parametrization.coupling is Coupling.UNIT_TRACE:
        total = sum(
            float(np.real(np.trace(np.asarray(choi[sector], dtype=np.complex128))))
            for sector in declaration.sector_index_set
        )
        return abs(total - 1.0)
    input_dim = parametrization.input_dim
    total_operator = np.zeros((input_dim, input_dim), dtype=np.complex128)
    for sector in declaration.sector_index_set:
        width = declaration.sector_dims[sector]
        block = np.asarray(choi[sector], dtype=np.complex128)
        total_operator = total_operator + np.einsum(
            "aqbq->ab", block.reshape(input_dim, width, input_dim, width)
        )
    difference = total_operator - np.eye(input_dim, dtype=np.complex128)
    return float(np.max(np.abs(difference)))
