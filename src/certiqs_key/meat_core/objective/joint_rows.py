"""The rows of ``eq:feas-general``, and their conjugated Choi forms.

``def:feasible``'s general format writes the feasible set as five lines --
normalization, the marginal per Alice sector, a lifted-operator entry per Alice
sector, a scalar entry in untrusted-source mode, and a ``party_local`` row per
pair ``(t, s_{f^c})`` -- and ``thm:choi``'s general format says what each is in
Choi coordinates: the lifted-operator row conjugated by ``W_t``, the
``party_local`` row conjugated by ``W_t (x) 1``, and in untrusted-source mode
no conjugation at all.

THE LIFTED OPERATOR IS NEVER FORMED HERE
========================================
``1 (x) O_k (x) 1`` is never formed in this module's reading of a row:
:func:`entry_value_per_alice_sector` contracts the declared block of the scope
against the state with an index arrangement, so the only array multiplied has
the size of the DECLARED block. :func:`lifted_block` forms it, and its one
caller is the ORACLE BOUNDARY one layer up
(:mod:`certiqs_key.solvers.oracles.joint_rows`), where a conic backend consumes
a matrix and nothing exact is decided on it. **That is the same licence the
Kronecker block ``F_v^{(s)}`` has** (``def:declaration`` (DX3): formed in
floating point inside the objective and nowhere as declared data).

THE PARTY-LOCAL ROW IS AN OPERATOR ROW ON MORE THAN ``A``
========================================================
``eq:partylocal-entry`` compares an operator on "the systems of ``omega`` other
than ``Q_{f_k}``" against ``0`` -- ``A`` and the other measured factors -- so
its comparison space is ``A_t (x) Q_{f^c,s_{f^c}}`` and NOT ``A_t``. That is
why the oracle protocol gains a row type whose coefficient is one operator per
Choi block rather than a product ``G (x) H_s``: the party-local row's
coefficient entangles the Choi input register with the other factors' blocks,
and no ``G (x) H_s`` can express it.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from certiqs_key.domain.manifest import ConstraintRelation
from certiqs_key.meat_core.declaration.general import SEPARATOR, GeneralDeclaration
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.joint import (
    JointChoiParametrization,
    JointSector,
)
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix, hermitian_part
from certiqs_key.meat_core.objective.objective import FEASIBILITY_TOLERANCE

#: The feasibility window of the general format's rows. THE SAME NUMBER THE
#: ACCEPTED PATH USES for the same question, and no wider: it decides a
#: residual on a point THIS MODULE COMPUTED (a formed iterate), never a defect
#: of declared data, which is the distinction ``spec/architecture.md`` 2.8
#: draws. It is not a tolerance on a declaration and no declaration is admitted
#: by it.


def split_dims(
    declaration: GeneralDeclaration, scope: str, sector: str
) -> tuple[int, int, int]:
    """Return ``(left, scoped, right)`` dimensions of one ``Q_s`` block.

    The three factors the product sector map of ``eq:productmap`` splits ``Q_s``
    into around the scope of an entry: the factors declared before it, the
    scoped one, and those after. Public because the oracle-row builder one
    layer up needs the same arrangement, and two spellings of it would let the
    engine's reading of a row and the backend's be about different operators.
    """
    return _split_dims(declaration, scope, sector)


def scoped_block(declaration: GeneralDeclaration, index: int, sector: str) -> Matrix:
    """Return ``O_k^{(s_f)}``, the declared block of an entry at its scope."""
    entry = declaration.constraint_list[index]
    position = factor_position(declaration, entry.scope)
    return as_matrix(entry.operator_blocks[declaration.split_sector(sector)[position]])


def lifted_block(
    declaration: GeneralDeclaration, scope: str, sector: str, operator: Matrix
) -> Matrix:
    """Return the ``s``-block of the lifted operator, FOR THE ORACLE BOUNDARY.

    ``1 (x) O_k^{(s_f)} (x) 1`` on ``Q_s`` (``def:declaration`` (DX6)), formed
    in floating point because a conic backend consumes a matrix. No exact
    predicate reads it and it is no part of any declaration; see the module
    docstring for the licence and its limit.
    """
    left, _, right = _split_dims(declaration, scope, sector)
    return np.asarray(
        np.kron(
            np.kron(np.eye(left, dtype=np.complex128), as_matrix(operator)),
            np.eye(right, dtype=np.complex128),
        ),
        dtype=np.complex128,
    )


def factor_position(declaration: GeneralDeclaration, scope: str) -> int:
    """Return the position of a scope in the declared factor order."""
    for position, factor in enumerate(declaration.factors):
        if factor.label == scope:
            return position
    raise DeclarationError(
        f"def:declaration (DX6): the scope {scope!r} is no declared measured "
        f"factor {[f.label for f in declaration.factors]}"
    )


def other_factor_label(declaration: GeneralDeclaration, scope: str, sector: str) -> str:
    """Return the identifier ``s_{f^c}`` of the other factors' blocks.

    The other factors' identifiers joined in the DECLARED factor order, which
    is the order ``eq:feas-general``'s ``Q_{f^c,s_{f^c}}`` is "the product of
    the other factors' blocks" in. With one measured factor it is the empty
    identifier, and the party-local row is then a row on ``A_t`` alone -- the
    one-factor reading ``def:homog`` states.
    """
    position = factor_position(declaration, scope)
    parts = declaration.split_sector(sector)
    return SEPARATOR.join(part for index, part in enumerate(parts) if index != position)


def _split_dims(
    declaration: GeneralDeclaration, scope: str, sector: str
) -> tuple[int, int, int]:
    """Return ``(left, scoped, right)`` dimensions of one ``Q_s`` block."""
    position = factor_position(declaration, scope)
    parts = declaration.split_sector(sector)
    left = 1
    right = 1
    scoped = 1
    factors = zip(declaration.factors, parts, strict=True)
    for index, (factor, part) in enumerate(factors):
        dim = factor.sectors.dims[part]
        if index < position:
            left *= dim
        elif index == position:
            scoped = dim
        else:
            right *= dim
    return left, scoped, right


def entry_value_per_alice_sector(
    declaration: GeneralDeclaration,
    index: int,
    state: Mapping[JointSector, Matrix],
) -> dict[str, Matrix]:
    """Return ``sum_s tr_{Q_s}[(1_{A_t} (x) O_k^{up(s)}) omega^{(t,s)}]`` per ``t``.

    The third line of ``eq:feas-general``. The lifted operator is NOT formed:
    the declared block of the scope is contracted against the state with the
    index arrangement ``(a, left, scoped, right)`` that the product sector map
    of ``eq:productmap`` fixes, so the only array multiplied is the declared
    one.
    """
    entry = declaration.constraint_list[index]
    out: dict[str, Matrix] = {}
    for alice_sector in declaration.alice_sectors:
        width = declaration.alice_dim_of(alice_sector)
        total = np.zeros((width, width), dtype=np.complex128)
        for sector in declaration.sector_index_set:
            left, scoped, right = _split_dims(declaration, entry.scope, sector)
            operator = as_matrix(
                entry.operator_blocks[
                    declaration.split_sector(sector)[
                        factor_position(declaration, entry.scope)
                    ]
                ]
            )
            block = as_matrix(state[(alice_sector, sector)]).reshape(
                width, left, scoped, right, width, left, scoped, right
            )
            total = total + np.einsum("ji,alirbljr->ab", operator, block)
        out[alice_sector] = np.asarray(total, dtype=np.complex128)
    return out


def entry_trace_value(
    declaration: GeneralDeclaration,
    index: int,
    state: Mapping[JointSector, Matrix],
) -> float:
    """Return ``sum_{(t,s)} tr[(1_{A_t} (x) O_k^{up(s)}) omega^{(t,s)}]``.

    The fourth line of ``eq:feas-general``: the UNTRUSTED-source-mode scalar
    entry, a comparison of real numbers. It is the full trace, over ``A`` as
    well, because in that mode ``A`` is an output of Eve's channel and
    ``lem:range`` (i) transports only the trace identity.
    """
    values = entry_value_per_alice_sector(declaration, index, state)
    return float(sum(np.real(np.trace(values[t])) for t in declaration.alice_sectors))


def party_local_value(
    declaration: GeneralDeclaration,
    index: int,
    state: Mapping[JointSector, Matrix],
) -> dict[tuple[str, str], Matrix]:
    """Return the party-local value per ``(t, s_{f^c})``, ``eq:feas-general``.

    ``tr_{Q_{f,s_f}}[(1 (x) (O_k^{(s_f)} - c_k 1)) omega^{(t,(s_{f^c},s_f))}]``
    summed over ``s_f``, an operator on ``A_t (x) Q_{f^c,s_{f^c}}`` with the
    ``A`` index first and the other factors in their declared order. The value
    of ``eq:partylocal-entry``, block by block.
    """
    entry = declaration.constraint_list[index]
    if not entry.is_party_local:
        raise DeclarationError(
            f"entry {index} is tagged {entry.rhs_tag.value!r}; only a "
            "party_local entry has the reading of eq:partylocal-entry"
        )
    constant = entry.scalar_bound
    position = factor_position(declaration, entry.scope)
    out: dict[tuple[str, str], Matrix] = {}
    for alice_sector in declaration.alice_sectors:
        width = declaration.alice_dim_of(alice_sector)
        for sector in declaration.sector_index_set:
            left, scoped, right = _split_dims(declaration, entry.scope, sector)
            scoped_label = declaration.split_sector(sector)[position]
            operator = as_matrix(entry.operator_blocks[scoped_label])
            deviation = operator - constant * np.eye(scoped, dtype=np.complex128)
            block = as_matrix(state[(alice_sector, sector)]).reshape(
                width, left, scoped, right, width, left, scoped, right
            )
            value = np.einsum("ji,alirBLjR->aBlLrR", deviation, block)
            size = width * left * right
            contribution = np.asarray(
                value.transpose(0, 2, 4, 1, 3, 5).reshape(size, size),
                dtype=np.complex128,
            )
            key = (alice_sector, other_factor_label(declaration, entry.scope, sector))
            out[key] = (
                out.get(key, np.zeros((size, size), dtype=np.complex128)) + contribution
            )
    return out


def marginal_per_alice_sector(
    declaration: GeneralDeclaration, state: Mapping[JointSector, Matrix]
) -> dict[str, Matrix]:
    """Return ``sum_s tr_{Q_s} omega^{(t,s)}`` per Alice sector."""
    out: dict[str, Matrix] = {}
    for alice_sector in declaration.alice_sectors:
        width = declaration.alice_dim_of(alice_sector)
        total = np.zeros((width, width), dtype=np.complex128)
        for sector in declaration.sector_index_set:
            dim = declaration.sector_dim(sector)
            block = as_matrix(state[(alice_sector, sector)]).reshape(
                width, dim, width, dim
            )
            total = total + np.einsum("aqbq->ab", block)
        out[alice_sector] = np.asarray(total, dtype=np.complex128)
    return out


def _relation_holds(
    relation: ConstraintRelation, difference: Matrix, tolerance: float
) -> bool:
    """Return whether ``difference`` satisfies the declared operator relation."""
    if difference.size == 0:
        return True
    raw = np.linalg.eigvalsh(hermitian_part(difference))
    if relation is ConstraintRelation.SUCCEQ:
        return bool(np.all(raw >= -tolerance))
    if relation is ConstraintRelation.PRECEQ:
        return bool(np.all(raw <= tolerance))
    return bool(np.max(np.abs(difference)) <= tolerance)


def _scalar_relation_holds(
    relation: ConstraintRelation, difference: float, tolerance: float
) -> bool:
    """Return whether a real difference satisfies the declared relation."""
    if relation is ConstraintRelation.SUCCEQ:
        return difference >= -tolerance
    if relation is ConstraintRelation.PRECEQ:
        return difference <= tolerance
    return abs(difference) <= tolerance


def check_joint_feasible(
    parametrization: JointChoiParametrization,
    state: Mapping[JointSector, Matrix],
    *,
    tolerance: float = FEASIBILITY_TOLERANCE,
) -> None:
    """Raise unless ``omega`` lies in ``Feas`` of ``eq:feas-general``.

    The five lines in the order the equation writes them: normalization --
    written EXPLICITLY, as ``def:feasible`` insists, because in
    untrusted-source mode it is the only unconditional condition -- the
    marginal per Alice sector in trusted-source mode, the lifted-operator entry
    per Alice sector (trusted) or its trace (untrusted), and the party-local row
    per ``(t, s_{f^c})`` IN EITHER MODE.

    Block diagonality along ``T`` and along ``S`` needs no check: the point IS
    a list over the joint sectors, so no off-block entry can be written.
    """
    declaration = parametrization.declaration
    total = 0.0
    for pair in parametrization.joint_sectors:
        block = as_matrix(state[pair])
        alice_sector, sector = pair
        expected = declaration.joint_block_dim(alice_sector, sector)
        if block.shape != (expected, expected):
            raise DeclarationError(
                f"the joint sector {pair}: the block has shape {block.shape}, "
                f"expected ({expected}, {expected}) for A_t (x) Q_s with the A "
                "index first"
            )
        raw = np.linalg.eigvalsh(hermitian_part(block))
        if bool(np.any(raw < -tolerance)):
            raise DeclarationError(
                f"the joint sector {pair}: the block is not positive "
                f"semidefinite (minimum eigenvalue {float(np.min(raw)):.3e})"
            )
        total += float(np.real(np.trace(block)))
    if abs(total - 1.0) > tolerance:
        raise DeclarationError(
            f"eq:feas-general (normalization): sum_(t,s) tr omega^(t,s) = "
            f"{total!r}, not 1"
        )
    if declaration.is_trusted_source:
        marginals = marginal_per_alice_sector(declaration, state)
        for alice_sector in declaration.alice_sectors:
            tau = declaration.marginal_block(alice_sector)
            if not bool(
                np.allclose(marginals[alice_sector], tau, atol=tolerance, rtol=0.0)
            ):
                raise DeclarationError(
                    "eq:feas-general (marginal, trusted-source mode): the "
                    f"A-marginal on the Alice sector {alice_sector!r} is not "
                    "tau_A^(t) (maximum deviation "
                    f"{float(np.max(np.abs(marginals[alice_sector] - tau))):.3e})"
                )
    for index, entry in enumerate(declaration.constraint_list):
        if entry.is_party_local:
            for key, value in party_local_value(declaration, index, state).items():
                if not _relation_holds(entry.relation, value, tolerance):
                    raise DeclarationError(
                        "eq:feas-general (party_local): the row at "
                        f"{key} of entry {index} ({entry.relation.value}) is "
                        "violated at this point"
                    )
            continue
        if declaration.is_trusted_source:
            values = entry_value_per_alice_sector(declaration, index, state)
            for alice_sector in declaration.alice_sectors:
                difference = values[alice_sector] - declaration.right_hand_side(
                    index, alice_sector
                )
                if not _relation_holds(entry.relation, difference, tolerance):
                    raise DeclarationError(
                        "eq:feas-general (trusted): constraint "
                        f"{index} ({entry.relation.value}) is violated on the "
                        f"Alice sector {alice_sector!r}"
                    )
            continue
        residual = entry_trace_value(declaration, index, state) - entry.scalar_bound
        if not _scalar_relation_holds(entry.relation, residual, tolerance):
            raise DeclarationError(
                "eq:feas-general (scalar entry, untrusted-source mode): "
                f"constraint {index} ({entry.relation.value}) is violated"
            )


def joint_constraint_residual(
    parametrization: JointChoiParametrization,
    choi: Mapping[JointSector, Matrix],
) -> float:
    """Worst residual of the imposed conjugated rows, rem:feas-tol.

    Evaluate in the original comparison space via chi, so a non-tight frame
    never silently replaces a conjugated row with the stronger W-free row.
    """
    declaration = parametrization.declaration
    if not declaration.constraint_list:
        # No row is imposed, so the worst residual is the empty maximum, 0.0,
        # exactly what the loop below returns; forming every chi(J) block
        # first would cost a matrix product per joint sector for nothing.
        return 0.0
    state = parametrization.state_from_choi(choi)
    worst = 0.0
    for index, entry in enumerate(declaration.constraint_list):
        if entry.is_party_local:
            differences = list(party_local_value(declaration, index, state).values())
        elif declaration.is_trusted_source:
            values = entry_value_per_alice_sector(declaration, index, state)
            differences = [
                values[t] - declaration.right_hand_side(index, t)
                for t in declaration.alice_sectors
            ]
        else:
            differences = [
                np.asarray(
                    [
                        [
                            entry_trace_value(declaration, index, state)
                            - entry.scalar_bound
                        ]
                    ],
                    np.complex128,
                )
            ]
        for difference in differences:
            if entry.relation is ConstraintRelation.EQ:
                residual = float(np.max(np.abs(difference)))
            elif entry.relation is ConstraintRelation.SUCCEQ:
                residual = -float(
                    np.min(np.linalg.eigvalsh(hermitian_part(difference)))
                )
            else:
                residual = float(np.max(np.linalg.eigvalsh(hermitian_part(difference))))
            worst = max(worst, residual)
    return worst
