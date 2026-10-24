"""The reduction-chain wire records: descriptors, links, the two segments.

WHAT THIS FILE HOLDS. Six frozen types, here so that no module imports the
protocol compiler: :class:`LinkStatus`, :class:`LinkStage` (the compiler spells it
``Segment``), :class:`Side`, :class:`SystemDescriptor`, :class:`ChainLink` and
:class:`ReductionChain`.

WHAT IS NOT HERE, AND WHY IT IS NOT A GAP. ``ChainContext``, ``ChainReport``,
``ConditionOutcome`` and ``check_chain`` belong to the compiler: they are the
COMPILER'S EVALUATION OF ITS OWN CHAIN CONDITIONS (C1) to (C5) -- a consumer's
behaviour, not a shared record.

A LINK STATUS, NOT AN ASSURANCE TIER. The ``certified`` assurance tier of
foundations/def:tiers (a narrow a-posteriori verification,
PRINCIPLES.md section 10) is a property of a key-rate number.
:attr:`LinkStatus.CERTIFIED_OUTER` is NOT that tier: it is a LINK STATUS -- the
tag saying a squashing relation holds only up to an error term -- and the
reductions module refuses to emit it for a reason of its own (no theorem there
converts an error term into a security penalty). It is kept, in every place it
appeared.

ONE STAGE VOCABULARY, TWO SPELLINGS. A link's first slot is typed
``LinkStage`` by the reductions module and ``Segment`` by the compiler. They
are one frozen type here, with :data:`Segment` as the
compiler-facing name, because a shared record whose vocabulary is declared
twice is a vocabulary that can disagree with itself.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final

from certiqs_key.domain.constraints import ConstraintEntry
from certiqs_key.foundations.blocks import (
    BlockKind,
    BlockOperator,
    Label,
    SectorStructure,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Matrix

__all__ = [
    "LINK_STATUS_VOCABULARY",
    "ChainLink",
    "LinkStage",
    "LinkStatus",
    "ReductionChain",
    "Segment",
    "Side",
    "SystemDescriptor",
]


class LinkStatus(StrEnum):
    """The three status tags of a declared reduction chain.

    ``exact`` means the squashing identity holds WITH NO ERROR TERM. The other
    two are carried through and never read: no theorem, gate or output row of
    the consuming contract reads a status, so nothing branches on one.
    ``certified_outer`` is a LINK STATUS and not the dropped assurance tier;
    see the module docstring.
    """

    EXACT = "exact"
    CERTIFIED_OUTER = "certified_outer"
    EXPLORATORY_NUMERIC = "exploratory_numeric"


#: The three, in the row's order. There is no fourth.
LINK_STATUS_VOCABULARY: Final[tuple[LinkStatus, ...]] = tuple(LinkStatus)


class LinkStage(StrEnum):
    """Which of the two stages a link belongs to. THE ORDER IS A RULE.

    A ``source``-stage link re-parameterizes the first-round attack over all
    CPTP maps; a ``receiver``-stage link hands the analysis an attack set that
    is a PROPER SUBSET of them. Applying a source link after a receiver link is
    therefore not free, and no claim of the reductions module establishes the
    inclusion it would need. The compiler spells the same two values
    ``Segment``; see :data:`Segment`.
    """

    SOURCE = "source"
    RECEIVER = "receiver"


#: The compiler-facing spelling of :class:`LinkStage`. One frozen vocabulary,
#: two names, so that the vocabulary is declared once.
Segment = LinkStage


class Side(StrEnum):
    """Whether a system descriptor is Alice-side or receiver-side.

    "Every descriptor of the source segment is an ALICE-SIDE descriptor: no
    condition of the segment mentions ``Q``, ``V`` or ``V^ph``." The side is
    therefore part of what a descriptor IS, not a property inferred from a
    dimension.
    """

    ALICE = "alice"
    RECEIVER = "receiver"


@dataclass(frozen=True)
class SystemDescriptor:
    """One source or target descriptor of a link.

    Two descriptors are equal when their name, dimension, side and sector
    structure agree -- which is what "compare finitely many declared
    descriptors" means. ``sectors`` is present only on the target descriptor of
    the last receiver link, which the consumer requires to BE ``(Q, Smap)``.
    """

    name: str
    #: ``None`` only for an Alice-side source descriptor whose system is not
    #: finite dimensional (the WCP tagging target). Receiver descriptors are
    #: always finite because (C1), block maps and receiver channels read their
    #: dimension.
    dim: int | None
    side: Side
    #: The block identifiers with their dimensions, present only on the target
    #: descriptor of the last receiver link, which the consumer's (C1) requires
    #: to BE the sector map: "the last link's target descriptor IS THE SECTOR
    #: MAP".
    sectors: tuple[tuple[Label, int], ...] | None = None
    #: THE THIRD COMPONENT OF THE MAP, carried beside the other two, because
    #: (C1) is decided "BY THE SAME FOUR-COMPONENT COMPARISON" a declared
    #: operator family's map is checked by.
    #:
    #: ``None`` MEANS THE SUPPLIER DECLARED NO KIND, AND THAT IS A REFUSAL AND
    #: NOT A DEFAULT: a comparison whose datum is missing is not a comparison,
    #: and this record supplies no kind of its own for somebody else's map.
    sector_block_kind: BlockKind | None = None

    def __post_init__(self) -> None:
        """Admit an unknown dimension only on the Alice/source side."""
        if self.dim is None and self.side is not Side.ALICE:
            raise MalformedInputError(
                "only an Alice-side source descriptor may have dim=None; a "
                "receiver descriptor has a finite dimension read by (C1)"
            )
        if self.dim is not None and self.dim < 1:
            raise MalformedInputError("a declared finite system dimension is positive")

    def sector_map(self) -> SectorStructure | None:
        """Return the sector map this descriptor IS, or ``None``.

        ``None`` where the descriptor carries no sectors at all -- which every
        descriptor but the last receiver target does -- and where it carries
        identifiers without a block kind, which is the incomplete case a
        consumer refuses rather than completes.
        """
        if self.sectors is None or self.sector_block_kind is None:
            return None
        return SectorStructure(
            labels=tuple(label for label, _ in self.sectors),
            dims=tuple(dim for _, dim in self.sectors),
            block_kind=self.sector_block_kind,
        )


@dataclass(frozen=True)
class ChainLink:
    """One typed link, with every slot the consumer's chain conditions name.

    ``channel`` is the link's channel AS DATA, presented as a tuple of Kraus
    operators, or ``None`` where the link supplies only a theorem constructor
    -- which is exactly when the consumer's channel condition becomes
    undecidable and it names its own assumption. The constraint and licence
    slots are always PRESENT and possibly empty.
    """

    link_id: str
    segment: LinkStage
    link_type: str
    source_descriptor: SystemDescriptor
    target_descriptor: SystemDescriptor
    status: LinkStatus
    channel: tuple[Matrix, ...] | None = None
    transported_constraints: tuple[ConstraintEntry, ...] = ()
    license_slot: object | None = None
    #: The target POVM, present on the LAST link of the receiver segment: "the
    #: last link of the receiver segment has target descriptor
    #: ``(Q, S, (d_s)_s)`` with the sector projectors, AND TARGET POVM
    #: ``{F_v}``". It is carried on the LINK and not on a receiver part
    #: because that is where the consuming contract puts it: the emitted family
    #: is the target of the reduction, not the physical family.
    target_alphabet: tuple[Label, ...] | None = None
    target_povm: Mapping[Label, BlockOperator] | None = None

    @property
    def channel_supplied(self) -> bool:
        """Whether the link supplies its channel as data."""
        return self.channel is not None

    @property
    def license_slot_present(self) -> bool:
        """Whether the licence slot exists. ALWAYS TRUE: the slot is emitted."""
        return True

    @property
    def license_slot_empty(self) -> bool:
        """Whether the licence slot is empty."""
        return self.license_slot is None


@dataclass(frozen=True)
class ReductionChain:
    """``R = (R_src, R_rec)``: the pair of ordered lists, in composition order.

    ``L_s >= 0`` and ``L >= 1``. BOTH SEGMENTS ARE ALWAYS PRESENT, including
    when the source segment is empty.
    """

    source_segment: tuple[ChainLink, ...] = ()
    receiver_segment: tuple[ChainLink, ...] = ()
    #: ``gamma : V^ph -> V``, the declared outcome correspondence of the
    #: receiver segment. Part of the chain PRESENTATION, carried here so that a
    #: chain is checkable without a second argument that could disagree with it.
    outcome_correspondence: Mapping[Label, Label] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Refuse a record that is not a chain of the declared shape."""
        if not self.receiver_segment:
            raise MalformedInputError("the receiver segment has L >= 1 links")
        for link in self.source_segment:
            if link.segment is not LinkStage.SOURCE:
                raise MalformedInputError(
                    f"link {link.link_id!r} is tagged {link.segment} but sits in "
                    "the source segment; the segment is the shape of the record"
                )
        for link in self.receiver_segment:
            if link.segment is not LinkStage.RECEIVER:
                raise MalformedInputError(
                    f"link {link.link_id!r} is tagged {link.segment} but sits in "
                    "the receiver segment; the segment is the shape of the record"
                )

    @property
    def source_length(self) -> int:
        """Return ``L_s``, the number of source-stage links."""
        return len(self.source_segment)

    @property
    def receiver_length(self) -> int:
        """Return ``L``, the number of receiver-stage links."""
        return len(self.receiver_segment)
