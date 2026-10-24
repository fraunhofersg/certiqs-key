"""The sector classes in the general format, and the two ``removable`` refusals.

``def:classes``, the general-format paragraph: "the four classes remain
predicates of the sectors ``s in S`` of the measured system, decided as above,
with ``O_k^{(s)}`` the block of the lifted operator of an entry", the finer
notion along Alice's sectors is ``def:joint-sectors``, and

    **the flag ``removable`` is set for NO sector** of a declaration whose list
    carries an entry declared ``party_local``, nor of a declaration with more
    than one measured factor.

THE TWO GROUNDS ARE NOT THE SAME KIND OF GROUND, and this module keeps them
apart because the claim does. The party-local ground is a HYPOTHESIS of
``thm:removal``, which is stated for a list carrying no such entry, so clause
(d) is unsatisfiable there and no sector carries a witness in its sense. The
multi-factor ground is a FLAG-LEVEL refusal: the theorem's proof reads the
sector blocks as operators and needs no factorisation, so its hypotheses can
hold, and what fails is that "this module's own decision procedure has no
declared datum to run (W1) and (W6) on" -- the blocks ``F_v^{(s)}`` being
products that are never formed as data. Both retain sectors, which is
unconditionally sound: ``h_low`` is defined as the infimum over the WHOLE
feasible set, and a removal is only ever a licence to restrict it.

NO WITNESS IS SEARCHED FOR HERE. On a declaration where the flag could be set
-- one measured factor, no party-local entry -- the accepted path's own
procedure is what decides it, and this module reports the ground that keeps the
flag off rather than duplicating that procedure for the general format.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.objective.joint import JointMaps, JointSector
from certiqs_key.meat_core.objective.linalg import as_matrix


class RemovableRefusal(StrEnum):
    """Why ``removable`` is off for every sector of a declaration.

    NOT A REFUSAL REASON OF THE INTERFACE: the run is not refused and no
    machine-readable refusal string is emitted. These are the two grounds
    ``def:classes`` names, recorded in the sector report beside the flag they
    keep off.
    """

    #: ``thm:removal`` is stated for a list carrying no such entry, so clause
    #: (d) of ``def:classes`` is unsatisfiable: a SOUNDNESS ground.
    PARTY_LOCAL_ENTRY = "party_local_entry"
    #: The blocks are products that are never formed as data, so (W1)'s
    #: bit-level test and (W6)'s residuals have nothing to read: a FLAG-LEVEL
    #: ground, and the theorem is in fact true there.
    SEVERAL_MEASURED_FACTORS = "several_measured_factors"


@dataclass(frozen=True)
class GeneralSectorRecord:
    """The four classes of one measured-system sector, in the general format."""

    sector: str
    key_active: bool
    constraint_active: bool
    state_blind: bool
    removable: bool
    #: Why the flag is off, where a ground applies; ``None`` where the sector
    #: simply carries no witness.
    removable_refused_because: RemovableRefusal | None


@dataclass(frozen=True)
class GeneralSectorReport:
    """The ``sector_report`` of a general-format declaration.

    :attr:`joint_pairs` is the ``sector_report.joint_pairs`` output row: which
    pairs ``(chat, (t, s))`` carry a deficit (``def:joint-sectors``), so that a
    sector key-active here may have key-inert JOINT pairs and the record says
    which.
    """

    records: tuple[GeneralSectorRecord, ...]
    joint_pairs: Mapping[str, tuple[JointSector, ...]]
    removable_refused_because: tuple[RemovableRefusal, ...]

    def record(self, sector: str) -> GeneralSectorRecord:
        """Return the record of one sector."""
        for entry in self.records:
            if entry.sector == sector:
                return entry
        raise KeyError(sector)


def removable_refusals(
    declaration: GeneralDeclaration,
) -> tuple[RemovableRefusal, ...]:
    """Return the grounds on which ``removable`` is off for every sector.

    ``def:classes``, the general format. Both grounds may apply at once -- BBM92
    is one such declaration, untrusted-source with party-local entries and two
    measured factors -- and the record names each.
    """
    grounds: list[RemovableRefusal] = []
    if declaration.has_party_local_entry:
        grounds.append(RemovableRefusal.PARTY_LOCAL_ENTRY)
    if len(declaration.factors) > 1:
        grounds.append(RemovableRefusal.SEVERAL_MEASURED_FACTORS)
    return tuple(grounds)


def is_state_blind(declaration: GeneralDeclaration, sector: str) -> bool:
    """Return whether ``s`` is state-blind, ``def:classes`` (c).

    The scalar-multiple test is a BIT-LEVEL IDENTITY on the declared data:
    ``c_{v,s}`` is read off the block as its first diagonal entry and every
    entry of ``F_v^{(s)} - c_{v,s} 1`` must be the datum ``0``. With SEVERAL
    MEASURED FACTORS the block is a product that is never formed as declared
    data, so the test runs PER FACTOR -- a product of scalar multiples of
    identities is one, and a product with a non-scalar factor is not -- which
    decides the same predicate on declared numbers. No subtraction, no norm and
    no window enters, and a block that is only NEARLY scalar fails.
    """
    parts = declaration.split_sector(sector)
    for letter in declaration.bob_outcomes:
        letters = declaration.split_letter(letter)
        for factor, part, block_label in zip(
            declaration.factors, letters, parts, strict=True
        ):
            block = as_matrix(factor.blocks[part][block_label])
            scalar = complex(block[0, 0])
            if scalar.imag != 0.0 or scalar.real < 0.0:
                return False
            if not np.array_equal(
                block, scalar.real * np.eye(block.shape[0], dtype=np.complex128)
            ):
                return False
    for entry in declaration.constraint_list:
        position = next(
            index
            for index, factor in enumerate(declaration.factors)
            if factor.label == entry.scope
        )
        block = as_matrix(entry.operator_blocks[parts[position]])
        scalar = complex(block[0, 0])
        if scalar.imag != 0.0:
            return False
        if not np.array_equal(
            block, scalar.real * np.eye(block.shape[0], dtype=np.complex128)
        ):
            return False
    return True


def general_sector_report(maps: JointMaps) -> GeneralSectorReport:
    """Return the sector classes and the joint-pair record of a declaration.

    ``def:classes`` in the general format, with ``def:joint-sectors``'s finer
    notion beside it. ``removable`` is FALSE for every sector: on a declaration
    carrying either ground because ``def:classes`` says so, and otherwise
    because no witness is exhibited here (this module searches for none, and an
    absent witness retains the sector, which is the direction ``def:classes``
    fixes throughout).
    """
    declaration = maps.declaration
    grounds = removable_refusals(declaration)
    ground = grounds[0] if grounds else None
    records: list[GeneralSectorRecord] = []
    for sector in declaration.sector_index_set:
        # def:keyinert reads M_x != 0 on the WHOLE Alice space. Taking
        # constancy separately on each t would miss different constants in
        # different sectors (lem:joint-sectors (iv)).
        active = any(
            len(
                {
                    declaration.raw_key(x, v)
                    for x in declaration.alice_alphabet
                    if any(
                        not declaration.alice_block_is_zero(x, t)
                        for t in declaration.alice_sectors
                    )
                    for v in declaration.bob_outcomes
                    if declaration.announcement(x, v) == kappa
                    and not declaration.bob_block_is_zero(v, sector)
                }
            )
            > 1
            for kappa, passes in maps.sifting.items()
            if passes
        )
        records.append(
            GeneralSectorRecord(
                sector=sector,
                key_active=active,
                constraint_active=not active,
                state_blind=is_state_blind(declaration, sector),
                removable=False,
                removable_refused_because=ground,
            )
        )
    joint_pairs = {
        chat: maps.key_active_pairs(chat) for chat in declaration.acceptance_values
    }
    return GeneralSectorReport(
        records=tuple(records),
        joint_pairs=joint_pairs,
        removable_refused_because=grounds,
    )
