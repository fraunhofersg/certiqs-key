"""The linear subproblem of the general format: ONE PROGRAM PER ALICE SECTOR.

``thm:choi``'s general format: "Every constraint of ``Feas^J`` involves the
blocks of one Alice sector only, so ``Feas^J = prod_t Feas^J_t``, and a linear
function of ``(J_{t,s})`` is minimised over ``Feas^J`` by minimising,
independently for each ``t``, its part on the blocks of ``t``." That is
``frank-wolfe/rem:fo-general-format`` (2), which states the
consequence for the oracle: "one independent conic program per Alice sector,
each with its own coupling constraint of size ``d_{A_{0,t}}``", and the
feasible side of a bracket is the sum of per-sector lower bounds
(``lem:feasible-side-dual`` (ii)).

IN UNTRUSTED-SOURCE MODE NOTHING SPLITS, and that is the same remark's next
sentence: "the single normalization and every scalar entry couple all joint
sectors". :func:`joint_program_untrusted` builds the one program, with the
Choi input register of dimension one -- which is what ``rem:modes-da1`` (b4)
says the two couplings coincide at -- so that each joint block ``A_t (x) Q_s``
is one positive semidefinite variable of its own size and the coupling is the
single scalar equation ``sum_{(t,s)} tr J_{t,s} = 1``.

WHAT IS FORMED HERE AND WHY IT IS ALLOWED TO BE
===============================================
A conic backend consumes matrices, so the lifted operator of an entry
(``def:declaration`` (DX6)) and the coefficient of a party-local row are formed
in floating point at this boundary. Neither is declared data and no exact
predicate reads either (``meat_core.objective.joint_rows``, the module
docstring). The engine's own reading of a row forms neither.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

import numpy as np

from certiqs_key.meat_core.declaration.general import SEPARATOR
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.choi import Coupling as StateCoupling
from certiqs_key.meat_core.objective.joint import (
    JointChoiParametrization,
    JointSector,
)
from certiqs_key.meat_core.objective.joint_rows import (
    factor_position,
    lifted_block,
    other_factor_label,
    split_dims,
)
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix
from certiqs_key.solvers.oracles.protocol import (
    AffineRow,
    Coupling,
    GeneralOperatorRow,
    SectorChoiProblem,
    hermitian_basis,
)


def _joint_labeller(alice_sector: str) -> Callable[[str], str]:
    """Return the block labeller of one Alice sector for the untrusted program."""

    def label(sector: str) -> str:
        return joint_label((alice_sector, sector))

    return label


def joint_label(pair: JointSector) -> str:
    """Return the block label of a joint sector, ``t`` then ``s``.

    The flattened joint identifier of ``def:declaration`` (DX1), joined by the
    one declared separator, so that a block label a backend reports back names
    the joint sector it came from.
    """
    return SEPARATOR.join(pair)


def split_joint_label(label: str) -> JointSector:
    """Return the joint sector of a block label built by :func:`joint_label`."""
    alice_sector, _, sector = label.partition(SEPARATOR)
    return (alice_sector, sector)


def _trusted_rows_of_one_alice_sector(
    parametrization: JointChoiParametrization, alice_sector: str
) -> tuple[tuple[AffineRow, ...], tuple[GeneralOperatorRow, ...]]:
    """Return the conjugated rows of one Alice sector, ``thm:choi``'s general form.

    A lifted-operator entry gives one :class:`AffineRow` per Alice sector, with
    the congruence ``W_t`` carrying the conjugation and ``Theta_k^{(t)}``
    CONSTRUCTED from the declared ``c_k`` and ``tau_A^{(t)}`` for a
    ``homogeneous`` entry, never read. A party-local entry gives one general row
    per ``s_{f^c}``.
    """
    declaration = parametrization.declaration
    frame = parametrization.frames[alice_sector]
    affine: list[AffineRow] = []
    general: list[GeneralOperatorRow] = []
    for index, entry in enumerate(declaration.constraint_list):
        if entry.is_party_local:
            general.extend(
                _party_local_rows(
                    parametrization,
                    alice_sector,
                    index,
                    block_label=lambda sector: sector,
                )
            )
            continue
        position = factor_position(declaration, entry.scope)
        affine.append(
            AffineRow(
                blocks={
                    sector: lifted_block(
                        declaration,
                        entry.scope,
                        sector,
                        as_matrix(
                            entry.operator_blocks[
                                declaration.split_sector(sector)[position]
                            ]
                        ),
                    )
                    for sector in declaration.sector_index_set
                },
                relation=entry.relation,
                rhs=declaration.right_hand_side(index, alice_sector),
                congruence=frame.w,
            )
        )
    return tuple(affine), tuple(general)


def _party_local_rows(
    parametrization: JointChoiParametrization,
    alice_sector: str,
    index: int,
    *,
    block_label: Callable[[str], str],
) -> tuple[GeneralOperatorRow, ...]:
    """Return one general row per ``s_{f^c}`` for a party-local entry.

    ``thm:choi``, the general format: "for a ``party_local`` entry the last line
    of ``eq:feas-general`` at ``J``, conjugated by ``W_t (x) 1``"; in
    untrusted-source mode there is no conjugation and the row is imposed as
    written. Testing the conjugated value against a Hermitian basis element
    ``E`` of the comparison space ``A_t (x) Q_{f^c}`` gives one real equation
    per element, whose coefficient on the block ``J_{t,s}`` is

        ``C[(b,l',j,r'),(a,l,i,r)] = G[(b,l',r'),(a,l,r)] D[j,i]``,

    with ``G = (W_t^dagger (x) 1) E (W_t (x) 1)`` and
    ``D = O_k^{(s_f)} - c_k 1``. The arrangement interleaves the scoped factor
    between the others, which is why it is not a product ``G (x) H_s``.
    """
    declaration = parametrization.declaration
    entry = declaration.constraint_list[index]
    frame = parametrization.frames[alice_sector]
    constant = entry.scalar_bound
    position = factor_position(declaration, entry.scope)
    input_dim = frame.input_dim
    by_other: dict[str, list[str]] = {}
    for sector in declaration.sector_index_set:
        by_other.setdefault(
            other_factor_label(declaration, entry.scope, sector), []
        ).append(sector)
    rows: list[GeneralOperatorRow] = []
    for other, sectors in by_other.items():
        left, _, right = split_dims(declaration, entry.scope, sectors[0])
        comparison = int(frame.w.shape[0]) * left * right
        congruence = np.kron(frame.w, np.eye(left * right, dtype=np.complex128))
        coefficients: list[Mapping[str, Matrix]] = []
        targets: list[float] = []
        for element in hermitian_basis(comparison):
            g_matrix = np.asarray(
                congruence.conj().T @ element @ congruence, dtype=np.complex128
            )
            g_tensor = g_matrix.reshape(
                input_dim, left, right, input_dim, left, right
            )
            per_block: dict[str, Matrix] = {}
            for sector in sectors:
                _, scoped, _ = split_dims(declaration, entry.scope, sector)
                scoped_label = declaration.split_sector(sector)[position]
                deviation = as_matrix(
                    entry.operator_blocks[scoped_label]
                ) - constant * np.eye(scoped, dtype=np.complex128)
                tensor = np.einsum("BLRalr,ji->BLjRalir", g_tensor, deviation)
                size = input_dim * left * scoped * right
                per_block[str(block_label(sector))] = np.asarray(
                    tensor.reshape(size, size), dtype=np.complex128
                )
            coefficients.append(per_block)
            targets.append(0.0)
        rows.append(
            GeneralOperatorRow(
                coefficients=tuple(coefficients),
                targets=tuple(targets),
                relation=entry.relation,
                slack_dim=comparison,
                label=f"party_local[{index}]@{alice_sector}|{other}",
            )
        )
    return tuple(rows)


PrebuiltRows = tuple[tuple[AffineRow, ...], tuple[GeneralOperatorRow, ...]]


def prebuilt_rows(
    parametrization: JointChoiParametrization,
) -> dict[str, PrebuiltRows]:
    """Return the conjugated rows of every Alice sector, built ONCE.

    The rows of a subproblem are a
    function of the declaration and the frame alone -- ``Theta_k^{(t)}`` is
    constructed from the declared ``c_k`` and ``tau_A^{(t)}``, the lifted blocks
    from the declared operator, the party-local coefficients from the frame --
    and ONLY THE COST CHANGES from iteration to iteration. Building them once
    per solve takes the assembly, whose party-local part is an index
    rearrangement per Hermitian basis element, out of the loop. What it does not
    do is build the BACKEND's model once: that is the same item's other half and
    is not landed here.
    """
    declaration = parametrization.declaration
    if not declaration.is_trusted_source:
        raise DeclarationError(
            "the per-Alice-sector rows exist in trusted-source mode; in "
            "untrusted-source mode there is one program over every joint "
            "sector (joint_program_untrusted)"
        )
    return {
        alice_sector: _trusted_rows_of_one_alice_sector(parametrization, alice_sector)
        for alice_sector in declaration.alice_sectors
    }


def joint_program_for_alice_sector(
    parametrization: JointChoiParametrization,
    alice_sector: str,
    cost: Mapping[JointSector, Matrix],
    *,
    rows: PrebuiltRows | None = None,
) -> SectorChoiProblem:
    """Return the independent conic program of ONE Alice sector.

    Trusted-source mode only: there the coupling constraint of ``t``, its
    lifted-operator rows and its party-local rows involve the blocks
    ``J_{t,s}`` of that ``t`` alone (``thm:choi``, the general format), so this
    is a program in its own right and the sum of the per-sector minima is the
    minimum over the product.
    """
    declaration = parametrization.declaration
    if not declaration.is_trusted_source:
        raise DeclarationError(
            "thm:choi's product structure is stated in trusted-source mode: "
            "there the coupling constraint of one Alice sector involves that "
            "sector's blocks alone. In untrusted-source mode the single "
            "normalization couples every joint sector and nothing splits "
            "(frank-wolfe/rem:fo-general-format (2)); use "
            "joint_program_untrusted"
        )
    affine, general = (
        _trusted_rows_of_one_alice_sector(parametrization, alice_sector)
        if rows is None
        else rows
    )
    return SectorChoiProblem(
        input_dim=parametrization.input_dim(alice_sector),
        block_dims={
            sector: declaration.sector_dims[sector]
            for sector in declaration.sector_index_set
        },
        cost={
            sector: as_matrix(cost[(alice_sector, sector)])
            for sector in declaration.sector_index_set
        },
        rows=affine,
        coupling=Coupling.INPUT_IDENTITY,
        general_rows=general,
    )


def joint_program_untrusted(
    parametrization: JointChoiParametrization,
    cost: Mapping[JointSector, Matrix],
) -> SectorChoiProblem:
    """Return the ONE program of untrusted-source mode, over every joint sector.

    The Choi step is the identity there (``def:untrusted-choi``), so ``J`` is
    ``omega``, each joint block is a variable of size ``d_{A_t} d_s`` and the
    coupling is the single scalar equation ``sum_{(t,s)} tr omega^{(t,s)} = 1``.
    THE INPUT REGISTER HAS DIMENSION ONE, which is not a substitution of
    ``W_tau = 1_A`` into the operator coupling -- the mistake
    ``def:untrusted-choi`` (b) names -- but the scalar coupling written as the
    operator one at input dimension one, the coincidence ``rem:modes-da1`` (b4)
    records.
    """
    declaration = parametrization.declaration
    if declaration.is_trusted_source:
        raise DeclarationError(
            "this program is the untrusted-source-mode one; in trusted-source "
            "mode the marginal is fixed per Alice sector and the program splits "
            "(joint_program_for_alice_sector)"
        )
    affine: list[AffineRow] = []
    general: list[GeneralOperatorRow] = []
    for index, entry in enumerate(declaration.constraint_list):
        if entry.is_party_local:
            # A PARTY-LOCAL ROW IS PER ALICE SECTOR EVEN HERE: its value is an
            # operator on A_t and the other factors (eq:partylocal-entry), and
            # an operator block diagonal along T is 0 exactly when each of its
            # blocks is -- the last line of eq:feas-general quantifies over
            # (t, s_{f^c}).
            for alice_sector in declaration.alice_sectors:
                general.extend(
                    _party_local_rows(
                        parametrization,
                        alice_sector,
                        index,
                        block_label=_joint_labeller(alice_sector),
                    )
                )
            continue
        # A SCALAR ENTRY IS ONE ROW OVER EVERY JOINT SECTOR, NOT ONE PER ALICE
        # SECTOR: the fourth line of eq:feas-general sums over (t, s) and
        # compares real numbers.
        position = factor_position(declaration, entry.scope)
        blocks: dict[str, Matrix] = {}
        for alice_sector in declaration.alice_sectors:
            width = declaration.alice_dim_of(alice_sector)
            for sector in declaration.sector_index_set:
                scoped = entry.operator_blocks[
                    declaration.split_sector(sector)[position]
                ]
                lifted = lifted_block(
                    declaration, entry.scope, sector, as_matrix(scoped)
                )
                blocks[joint_label((alice_sector, sector))] = np.asarray(
                    np.kron(np.eye(width, dtype=np.complex128), lifted),
                    dtype=np.complex128,
                )
        affine.append(
            AffineRow(
                blocks=blocks,
                relation=entry.relation,
                rhs=entry.scalar_bound,
                congruence=None,
            )
        )
    return SectorChoiProblem(
        input_dim=1,
        block_dims={
            joint_label(pair): declaration.joint_block_dim(*pair)
            for pair in parametrization.joint_sectors
        },
        cost={
            joint_label(pair): as_matrix(cost[pair])
            for pair in parametrization.joint_sectors
        },
        rows=tuple(affine),
        coupling=Coupling.UNIT_TRACE,
        general_rows=tuple(general),
    )


def state_coupling(parametrization: JointChoiParametrization) -> StateCoupling:
    """Return the coupling the parametrization declares, for a record."""
    return parametrization.coupling
