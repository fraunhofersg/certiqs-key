"""The constraints layer: docking, explicit entries, licence, witness.

Part of the lowering package (:mod:`instances.declared.lowering`).
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING

from certiqs_key.domain.constraints import (
    AttackSetLicense,
    ConstraintEntry,
    Relation,
    RhsTag,
)
from certiqs_key.foundations import exact
from certiqs_key.foundations.blocks import (
    BlockOperator,
    JointBlockOperator,
    SectorStructure,
)
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.lowering.base import (
    _DECLARED,
    _Constraints,
    _fraction,
)
from instances.declared.lowering.public import _PublicLowering
from instances.declared.model import (
    Blocks,
    Expr,
    ParamRef,
    WitnessBlocks,
)
from instances.declared.values import unwrap

if TYPE_CHECKING:  # pragma: no cover - typing only
    pass


class _ConstraintLowering(_PublicLowering):
    """The constraints layer: the block, its entries, its licence."""

    # -- the constraints -------------------------------------------------------

    def constraints_block(self, *, docks: bool) -> _Constraints:
        """Read the constraints block once, flag what it declares, check its licence.

        ``docks`` says whether this document has anything to dock: an optical
        station's reduction does, a declared POVM does not. ``party_local_view``
        reads several stations' docked constraints, so it is refused where
        there is one station or nothing docked, rather than dropped.
        """
        node = self.model.constraints
        where = "/constraints"
        if node is None:
            return _Constraints(True, None, "", (), "", None, "auto", "")
        docked, _ = unwrap(node.docked, self.env, where + "/docked")
        view, view_path = unwrap(
            node.party_local_view, self.env, where + "/party_local_view"
        )
        if view is not None and not (docks and self.multi):
            raise DocumentError(
                "party_local_view reads several stations' docked constraints; "
                "this document docks " + ("one station's" if docks else "none"),
                reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                path=view_path,
            )
        entries, entries_path = unwrap(node.entries, self.env, where + "/entries")
        for index, entry in enumerate(entries):
            self.flag(
                "constraint_entry",
                entries_path + pointer(index),
                entry.label,
                f"Constraint entry {entry.label!r}. {_DECLARED} The key length "
                "holds only if this constraint holds for your device.",
            )
        licence: AttackSetLicense | None = None
        if node.attack_set_license is not None:
            licence = AttackSetLicense(
                supplier=f"user-declared:{self.document_id}",
                statement=node.attack_set_license.statement,
            )
            self.flag(
                "attack_set_license",
                where + "/attack_set_license",
                licence.supplier,
                f"The attack-set licence. {_DECLARED} The key length holds only "
                "if it holds for your device: that every attack is in the set "
                f"your constraints describe. Statement: {licence.statement}",
            )
        if entries and licence is None:
            raise DocumentError(
                "explicit constraint entries need an explicit attack_set_license "
                "statement; otherwise the record would credit your entries to "
                "a licence nobody gave",
                reason=DocumentReason.USER_ENTRIES_WITHOUT_LICENCE,
                path=entries_path,
            )
        witness, witness_path = unwrap(
            node.feasibility_witness, self.env, where + "/feasibility_witness"
        )
        if isinstance(witness, WitnessBlocks):
            self.flag(
                "feasibility_witness",
                witness_path,
                "feasibility_witness",
                f"The feasibility witness. {_DECLARED} The compiler verified it; "
                "it affects only whether a key length is produced.",
            )
        return _Constraints(
            bool(docked),
            view,
            view_path,
            entries,
            entries_path,
            licence,
            witness,
            witness_path,
        )

    def user_constraints(
        self,
        block: _Constraints,
        sectors: SectorStructure,
        alice: SectorStructure | int,
    ) -> tuple[tuple[ConstraintEntry, ...], JointBlockOperator | None]:
        """Return the explicit entries and witness, against the emitted sector map."""
        entries: list[ConstraintEntry] = []
        for index, entry in enumerate(block.entries):
            path = block.entries_path + pointer(index)
            entries.append(
                ConstraintEntry(
                    operator=self._blocks(entry.operator, sectors, path + "/operator"),
                    relation=Relation(entry.relation),
                    rhs=self._rhs(entry.rhs, alice, path + "/rhs"),
                    arriving_tag=self._tag(entry.tag, path + "/tag"),
                    scope=entry.scope,
                )
            )
        witness: JointBlockOperator | None = None
        if isinstance(block.witness, WitnessBlocks):
            witness = JointBlockOperator.of(
                sectors,
                alice,
                [
                    self.matrix(node, block.witness_path + pointer("blocks", i))
                    for i, node in enumerate(block.witness.blocks)
                ],
            )
        return tuple(entries), witness

    @staticmethod
    def joined_licence(
        docked: AttackSetLicense | None, user: AttackSetLicense | None
    ) -> AttackSetLicense | None:
        """Join the reductions' licence and the user's into one record."""
        if docked is None or user is None:
            return docked if user is None else user
        return AttackSetLicense(
            supplier=f"{docked.supplier} + {user.supplier}",
            statement=f"{docked.statement} Declared by the user: {user.statement}",
        )

    def _blocks(
        self, node: Blocks, sectors: SectorStructure, path: str
    ) -> BlockOperator:
        unknown = sorted(set(node.blocks) - set(sectors.labels))
        missing = [label for label in sectors.labels if label not in node.blocks]
        if unknown or missing:
            raise DocumentError(
                f"an operator is one block per sector {list(sectors.labels)}; "
                f"unknown {unknown}, missing {missing}",
                reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                path=path,
            )
        return BlockOperator.of(
            sectors,
            [
                self.matrix(node.blocks[label], path + pointer("blocks", label))
                for label in sectors.labels
            ],
        )

    def _rhs(
        self, node: object, alice: SectorStructure | int, path: str
    ) -> exact.Matrix | BlockOperator | Fraction:
        node, path = unwrap(node, self.env, path)
        if isinstance(node, Blocks):
            if not isinstance(alice, SectorStructure):
                raise DocumentError(
                    "this source declares no sector map of Alice's, so a "
                    "right-hand side is a matrix or a number, not blocks",
                    reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                    path=path,
                )
            return self._blocks(node, alice, path)
        if isinstance(node, int | str | ParamRef | Expr):
            return _fraction(node, self.env, path)
        return self.matrix(node, path)

    @staticmethod
    def _tag(tag: str | None, path: str) -> RhsTag | None:
        if tag is None:
            return None
        try:
            return RhsTag(tag)
        except ValueError:
            raise DocumentError(
                f"{tag!r} is not a constraint tag ({[str(m) for m in RhsTag]})",
                reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
                path=path,
            ) from None
