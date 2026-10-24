"""Sector classification, removal, and the operations that are forbidden (C7, C10).

contract.tex Remark ``rem:classes`` is exhaustive about what an implementation
may do to the declared sector structure:

    (i)  evaluate the objective over key-active sectors only -- an identity, C7;
    (ii) delete removable sectors -- Theorem ``thm:removal``, checked by the
         removal criteria (RM1)-(RM3);
    (iii) nothing else.

Dropping a constraint-active sector (Proposition ``prop:retention``) and merging
or averaging sectors (Proposition ``prop:no-averaging``) are both unsound, and
both overstate the key -- the dangerous direction. **This module contains no
code path for either**, which is the only durable way to enforce "nothing else":
there is no averaging function to call by mistake, and the sector list is
treated as append-only input data.

Operation (i) is likewise not implemented as a *shortcut*: the objective sums
the deficits over every declared sector, because Proposition
``prop:exact-cancellation`` makes
that an identity and computing the identity does not rely on the predicate
being right. The classification here feeds the ``sector_report`` output of
the `outputs` table and the removal check, nothing else.

**What ``removable`` means here.** ``True`` is a claim with a checked witness:
sectors ``s_i``, states ``chi_i`` and weights ``mu_i`` satisfying (RM1)-(RM3)
were found and verified. ``False`` means no witness was found by the search
implemented below -- which is a restricted one -- and the sector is retained.
The asymmetry is deliberate and is in the safe direction: retaining a sector
that could have been deleted costs nothing but time, whereas deleting one that
could not is the failure Proposition ``prop:retention`` prices at a whole bit
per round.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum

import numpy as np

from certiqs_key.meat_core.declaration.declaration import (
    ConstraintEntry,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.errors import SectorOperationError
from certiqs_key.meat_core.objective.branch import GeneratedMaps
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix

#: Tolerance for the scalar-multiple test of Definition ``def:classes`` (c) and
#: for the (RM1)/(RM3) equalities. Tight on purpose: a witness that only nearly
#: satisfies the criteria does not justify a deletion.
CRITERION_TOLERANCE = 1e-12

#: Above this many candidate target sectors the witness SEARCH is not attempted
#: and the sector is reported as not removable. The bound keeps the search
#: finite; it never makes a removal unsound, only unfound.
MAX_SEARCH_TARGETS = 8


class SectorClass(StrEnum):
    """The two classes of contract Definition ``def:classes`` (a) and (b)."""

    KEY_ACTIVE = "key-active"
    CONSTRAINT_ACTIVE = "constraint-active"


@dataclass(frozen=True)
class RemovalTarget:
    """One ``(s_i, chi_i, mu_i)`` of Theorem ``thm:removal``."""

    sector: str
    state: Matrix
    weight: float


@dataclass(frozen=True)
class RemovalWitness:
    """A checked witness that a sector satisfies (RM1)-(RM3)."""

    sector: str
    targets: tuple[RemovalTarget, ...]


@dataclass(frozen=True)
class SectorRecord:
    """One row of the ``sector_report`` output of the `outputs` table."""

    sector: str
    sector_class: SectorClass
    state_blind: bool
    removable: bool
    key_inert: Mapping[str, bool]
    removal_witness: RemovalWitness | None = None
    removal_note: str = ""


@dataclass(frozen=True)
class SectorReport:
    """The ``sector_report`` output: one record per declared sector."""

    records: tuple[SectorRecord, ...]

    def record(self, sector: str) -> SectorRecord:
        """Return the record of one sector."""
        for entry in self.records:
            if entry.sector == sector:
                return entry
        raise KeyError(sector)

    def as_payload(self) -> list[dict[str, object]]:
        """Return the report as serializable data (no operators, no callables).

        WHAT IS NOT IN IT, AND WHY THE OMISSION IS DELIBERATE. The
        state-blindness CONSEQUENCE ``sum_v c_{v,s} = 1`` is not a field here
        and never was: it follows from ``def:classes`` (c) TOGETHER WITH
        completeness, and reporting a consequence of two conditions as though
        it were a datum invites a reader to take it for the condition. What
        survives is the DEFINING clause ``F^{(s)}_v = c_{v,s} 1_{Q_s}``, which
        is the ``state_blind`` flag below, and with it ``thm:removal`` and the
        ``removable`` flag; the coefficients ``c_{v,s}`` themselves stay where
        they are used (:func:`state_blind_response`) rather than being
        reported.

        A SECOND REASON would arise only under a declared-tolerance
        apparatus: on an admitted-with-defect branch the consequence would be
        false of the declared numbers while the defining clause held. No
        family is admitted with a defect, so that branch does not arise and the
        omission stands on the first reason alone.
        """
        return [
            {
                "sector": entry.sector,
                "class": str(entry.sector_class),
                "state_blind": entry.state_blind,
                "removable": entry.removable,
                "key_inert": dict(entry.key_inert),
                "removal_targets": (
                    [target.sector for target in entry.removal_witness.targets]
                    if entry.removal_witness is not None
                    else []
                ),
                "removal_note": entry.removal_note,
            }
            for entry in self.records
        ]


def _scalar_multiple(operator: Matrix, width: int) -> float | None:
    """Return ``c`` if ``operator = c * 1``, else ``None``."""
    candidate = float(np.real(np.trace(operator))) / width
    identity = candidate * np.eye(width, dtype=np.complex128)
    scale = max(float(np.max(np.abs(operator))) if operator.size else 0.0, 1.0)
    if bool(
        np.allclose(operator, identity, atol=CRITERION_TOLERANCE * scale, rtol=0.0)
    ):
        return candidate
    return None


def state_blind_response(
    declaration: ProtocolDeclaration, sector: str
) -> dict[str, float] | None:
    """Return ``{v: c_{v,s}}`` if the sector is state-blind, else ``None``.

    contract Definition ``def:classes`` (c): ``F^{(s)}_v = c_{v,s} 1_{Q_s}`` for
    every ``v``, and -- when the declared list is nonempty -- also
    ``O_k^{(s)} = o_{k,s} 1_{Q_s}`` for every ``k``.
    """
    width = declaration.sector_dims[sector]
    response: dict[str, float] = {}
    for v in declaration.bob_outcomes:
        scalar = _scalar_multiple(as_matrix(declaration.bob_povm[v][sector]), width)
        if scalar is None:
            return None
        response[v] = scalar
    for entry in declaration.constraint_list:
        if _scalar_multiple(as_matrix(entry.operator_blocks[sector]), width) is None:
            return None
    return response


def constraint_response(
    declaration: ProtocolDeclaration, sector: str
) -> tuple[float, ...] | None:
    """Return ``(o_{k,s})_k`` if every constraint block is a scalar multiple of 1."""
    width = declaration.sector_dims[sector]
    scalars: list[float] = []
    for entry in declaration.constraint_list:
        scalar = _scalar_multiple(as_matrix(entry.operator_blocks[sector]), width)
        if scalar is None:
            return None
        scalars.append(scalar)
    return tuple(scalars)


def is_state_blind(declaration: ProtocolDeclaration, sector: str) -> bool:
    """Return whether ``sector`` is state-blind (Definition ``def:classes`` (c))."""
    return state_blind_response(declaration, sector) is not None


def classify_sector(maps: GeneratedMaps, sector: str) -> SectorClass:
    """Return the class of ``sector`` (Definition ``def:classes`` (a), (b)).

    Key-active when some key-live acceptance value fails the key-inertness
    predicate; constraint-active when the sector is key-inert for every one of
    them. A constraint-active sector contributes nothing to any ``K_chat``
    (Proposition ``prop:exact-cancellation``) and yet REMAINS an optimization
    variable: it
    enters ``Phi``, every ``P_chat``, the normalization ``tr omega = 1``, the
    marginal condition where one is declared, and ``L``.
    """
    for chat in maps.chat_key:
        if not maps.key_inert[(chat, sector)]:
            return SectorClass.KEY_ACTIVE
    return SectorClass.CONSTRAINT_ACTIVE


def _constraint_block_value(
    entry: ConstraintEntry, sector: str, state: Matrix
) -> float:
    """Return ``tr[O_k^{(s)} chi]`` for one constraint entry."""
    return float(np.real(np.trace(as_matrix(entry.operator_blocks[sector]) @ state)))


def verify_removal_witness(maps: GeneratedMaps, witness: RemovalWitness) -> None:
    """Raise unless the witness satisfies Theorem ``thm:removal`` at ``sector``.

    Checks, in the theorem's order: ``s*`` state-blind; the weights non-negative
    and summing to one; each ``chi_i`` a state on its sector; (RM1) response
    match; (RM2) key-inert targets; (RM3) constraint match. Every removal an
    implementation performs must be justified by these checked hypotheses
    (Remark ``rem:classes``).
    """
    declaration = maps.declaration
    star = witness.sector
    if star not in declaration.sector_index_set:
        raise SectorOperationError(f"unknown sector {star!r}")
    response = state_blind_response(declaration, star)
    if response is None:
        raise SectorOperationError(
            f"Theorem thm:removal requires the removed sector to be "
            f"state-blind; {star!r} is not (Definition def:classes (c))"
        )
    if not witness.targets:
        raise SectorOperationError(
            "Theorem thm:removal needs at least one target sector"
        )
    weights = [target.weight for target in witness.targets]
    if any(weight < 0.0 for weight in weights):
        raise SectorOperationError("Theorem thm:removal requires mu_i >= 0")
    if abs(sum(weights) - 1.0) > CRITERION_TOLERANCE:
        raise SectorOperationError(
            f"Theorem thm:removal requires sum_i mu_i = 1; got {sum(weights)!r}"
        )
    for target in witness.targets:
        if target.sector == star:
            raise SectorOperationError(
                "a removal target must be a sector other than the removed one"
            )
        width = declaration.sector_dims[target.sector]
        state = as_matrix(target.state)
        if state.shape != (width, width):
            raise SectorOperationError(
                f"target state on {target.sector!r} has shape {state.shape}, "
                f"expected ({width}, {width})"
            )
        if abs(float(np.real(np.trace(state))) - 1.0) > CRITERION_TOLERANCE:
            raise SectorOperationError(
                f"target state on {target.sector!r} is not normalized"
            )
        if bool(np.any(np.linalg.eigvalsh(state) < -CRITERION_TOLERANCE)):
            raise SectorOperationError(
                f"target state on {target.sector!r} is not positive semidefinite"
            )
        for chat in maps.chat_key:
            if not maps.key_inert[(chat, target.sector)]:
                raise SectorOperationError(
                    f"(RM2) key-inert targets: the pair ({chat!r}, "
                    f"{target.sector!r}) is not key-inert"
                )
    for v in declaration.bob_outcomes:
        expected = response[v]
        got = sum(
            target.weight
            * float(
                np.real(
                    np.trace(
                        as_matrix(declaration.bob_povm[v][target.sector])
                        @ as_matrix(target.state)
                    )
                )
            )
            for target in witness.targets
        )
        if abs(got - expected) > CRITERION_TOLERANCE:
            raise SectorOperationError(
                f"(RM1) response match fails at outcome {v!r}: "
                f"c_{{v,s*}} = {expected!r} but the targets give {got!r}"
            )
    scalars = constraint_response(declaration, star)
    if scalars is None and declaration.constraint_list:
        raise SectorOperationError(
            "(RM3) constraint match needs the removed sector's constraint "
            "blocks to be multiples of the identity"
        )
    for index, entry in enumerate(declaration.constraint_list):
        assert scalars is not None
        expected = scalars[index]
        got = sum(
            target.weight
            * _constraint_block_value(entry, target.sector, as_matrix(target.state))
            for target in witness.targets
        )
        if abs(got - expected) > CRITERION_TOLERANCE:
            raise SectorOperationError(
                f"(RM3) constraint match fails at constraint {index}: "
                f"o_{{k,s*}} = {expected!r} but the targets give {got!r}"
            )


def find_removal_witness(
    maps: GeneratedMaps, sector: str
) -> tuple[RemovalWitness | None, str]:
    """Search for a witness that ``sector`` satisfies (RM1)-(RM3).

    A **restricted** search, and it says so in its second return value. It looks
    only at target sectors that are one-dimensional -- where the state ``chi_i``
    is forced and the criteria become a small linear feasibility problem in the
    weights -- and it gives up above :data:`MAX_SEARCH_TARGETS` candidates. A
    ``None`` result therefore means "no witness found", never "no witness
    exists", and the sector is retained either way.

    Every candidate the search proposes is then put through
    :func:`verify_removal_witness`, so a witness that is returned has been
    checked against the theorem rather than against the search's own arithmetic.
    """
    declaration = maps.declaration
    response = state_blind_response(declaration, sector)
    if response is None:
        return None, "not state-blind (Definition def:classes (c))"
    candidates = [
        other
        for other in declaration.sector_index_set
        if other != sector
        and declaration.sector_dims[other] == 1
        and all(maps.key_inert[(chat, other)] for chat in maps.chat_key)
    ]
    if not candidates:
        return None, "no key-inert one-dimensional target sector (RM2)"
    if len(candidates) > MAX_SEARCH_TARGETS:
        return None, (
            f"{len(candidates)} candidate targets exceeds the search bound "
            f"{MAX_SEARCH_TARGETS}; the search was not attempted"
        )

    rows: list[list[float]] = []
    rhs: list[float] = []
    for v in declaration.bob_outcomes:
        rows.append(
            [
                float(np.real(declaration.bob_povm[v][other][0, 0]))
                for other in candidates
            ]
        )
        rhs.append(response[v])
    scalars = constraint_response(declaration, sector)
    if scalars is None and declaration.constraint_list:
        return None, "the constraint blocks are not multiples of the identity (RM3)"
    for index, entry in enumerate(declaration.constraint_list):
        assert scalars is not None
        rows.append(
            [float(np.real(entry.operator_blocks[other][0, 0])) for other in candidates]
        )
        rhs.append(scalars[index])
    rows.append([1.0] * len(candidates))
    rhs.append(1.0)
    matrix = np.asarray(rows, dtype=np.float64)
    target = np.asarray(rhs, dtype=np.float64)

    for size in range(1, len(candidates) + 1):
        for subset in itertools.combinations(range(len(candidates)), size):
            columns = matrix[:, list(subset)]
            solution, *_ = np.linalg.lstsq(columns, target, rcond=None)
            if bool(np.any(solution < -CRITERION_TOLERANCE)):
                continue
            residual = float(np.max(np.abs(columns @ solution - target)))
            if residual > CRITERION_TOLERANCE:
                continue
            witness = RemovalWitness(
                sector=sector,
                targets=tuple(
                    RemovalTarget(
                        sector=candidates[index],
                        state=np.ones((1, 1), dtype=np.complex128),
                        weight=float(max(weight, 0.0)),
                    )
                    for index, weight in zip(subset, solution, strict=True)
                ),
            )
            try:
                verify_removal_witness(maps, witness)
            except SectorOperationError:
                continue
            return witness, "witness verified against (RM1)-(RM3)"
    return None, "no non-negative combination of the candidate targets matches"


def build_sector_report(maps: GeneratedMaps) -> SectorReport:
    """Return the ``sector_report`` output of the `outputs` table.

    Per sector: the class, the ``state-blind`` and ``removable`` flags, and the
    underlying key-inertness predicate per pair ``(chat, s)`` -- exactly the
    fields the Outputs table names, with every removal justified by the checked
    hypotheses (Remark ``rem:classes``).
    """
    records: list[SectorRecord] = []
    for sector in maps.sectors:
        witness, note = find_removal_witness(maps, sector)
        records.append(
            SectorRecord(
                sector=sector,
                sector_class=classify_sector(maps, sector),
                state_blind=is_state_blind(maps.declaration, sector),
                removable=witness is not None,
                key_inert={
                    chat: maps.key_inert[(chat, sector)]
                    for chat in maps.declaration.acceptance_values
                },
                removal_witness=witness,
                removal_note=note,
            )
        )
    return SectorReport(records=tuple(records))


def delete_sectors(
    maps: GeneratedMaps, witnesses: Sequence[RemovalWitness]
) -> ProtocolDeclaration:
    """Return the declaration with the witnessed sectors deleted.

    Operation (ii) of Remark ``rem:classes``, and the only structure-changing
    operation in this package. Every witness is re-verified before anything is
    deleted, and a witness whose targets are themselves being deleted is
    refused: the theorem moves the removed sector's weight ONTO its targets, so
    a target that is not there afterwards is not a target.
    """
    declaration = maps.declaration
    removed = {witness.sector for witness in witnesses}
    for witness in witnesses:
        verify_removal_witness(maps, witness)
        for target in witness.targets:
            if target.sector in removed:
                raise SectorOperationError(
                    f"the witness for {witness.sector!r} targets "
                    f"{target.sector!r}, which is itself being deleted"
                )
    keep = tuple(s for s in declaration.sector_index_set if s not in removed)
    if not keep:
        raise SectorOperationError("deleting every sector leaves no receiver space")
    partition = declaration.party_partition
    return ProtocolDeclaration(
        alice_dim=declaration.alice_dim,
        alice_marginal=declaration.alice_marginal,
        sector_index_set=keep,
        # Deleting a sector removes blocks from the map; it does not change
        # what KIND of blocks they are.
        sector_block_kind=declaration.sector_block_kind,
        sector_dims={s: declaration.sector_dims[s] for s in keep},
        alice_povm=dict(declaration.alice_povm),
        bob_povm={
            v: {s: blocks[s] for s in keep}
            for v, blocks in declaration.bob_povm.items()
        },
        announce_alice=dict(declaration.announce_alice),
        announce_bob=dict(declaration.announce_bob),
        accept_statistic=dict(declaration.accept_statistic),
        key_map=dict(declaration.key_map),
        key_holder=declaration.key_holder,
        acceptance_values=declaration.acceptance_values,
        key_value_count=declaration.key_value_count,
        acceptance_set=declaration.acceptance_set,
        rounds=declaration.rounds,
        parameters=declaration.parameters,
        constraint_list=tuple(
            ConstraintEntry(
                operator_blocks={s: entry.operator_blocks[s] for s in keep},
                relation=entry.relation,
                # The DECLARED tag travels with the entry: sector deletion
                # removes blocks of O_k and touches neither the right-hand
                # side nor the form it was declared in.
                rhs_tag=entry.rhs_tag,
                bound=entry.bound,
            )
            for entry in declaration.constraint_list
        ),
        attack_set_license=declaration.attack_set_license,
        # Every declared input travels with the declaration. Dropping the A-SRC
        # attestation would silently close a gate the supplier had opened, and
        # dropping the party partition would silently RE-OPEN one: under the
        # default partition an inadmissible key holder can pass Assumption
        # def:admissible-declaration (viii) vacuously (contract Def. def:declaration),
        # so a removal that lost the declared readouts could turn a refused declaration
        # into an accepted one.
        source_replacement_license=declaration.source_replacement_license,
        party_partition=(
            None
            if partition is None
            else replace(
                partition,
                party_of_sector_factors={
                    s: partition.party_of_sector_factors[s]
                    for s in keep
                    if s in partition.party_of_sector_factors
                },
            )
        ),
    )
