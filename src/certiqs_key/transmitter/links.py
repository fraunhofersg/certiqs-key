"""Source links, the obligation triple, and the closed soundness registry.

spec/modules/transmitter/: Definition ``def:source-link`` (the tuple, its nine
slots, the two ways a witness is supplied) and Definition
``def:source-segment`` (which kinds are admitted, and the three conditions
(A1)--(A3) a consumer decides on data).

C4 makes the admitted decoy tagging path live. The core retains
``link_kind_deferred`` for ``source-map``, uses
``source_link_kind_not_admitted`` for unknown kinds, and refuses a raw
attempt to supply an admitted link without the admitting module's artifact.
Consumers decide the registered link and ledger conditions below, together
with supplier provenance; a matching tuple of links alone does not supply it.

WHY A REGISTRY AT ALL. The admission rule --- "no
source link kind is admitted unless the submodule that declares it supplies its
soundness claim" --- is a condition on the KIND, and "a consumer cannot decide
it of a claim it does not read". Without something decidable beside it, a
presented chain carrying a FALSE obligation record passed every decided
condition. :data:`SOUNDNESS_REGISTRY` is the decidable half: a finite closed
list emitted with every artefact, one entry per admitted kind, compared as
declared strings.

WHY THE REGISTRY'S THIRD COMPONENT IS NOT "THE CLAIM'S ASSUMPTIONS" (the
defect the field exists to prevent). ``decoy/prop:tagging``
declares ``assumes: []`` ON PURPOSE, being an identity among the model's
states, so its assumption closure -- what ``python -m harness.check_claims
--assumptions transmitter/decoy/prop:tagging`` computes -- IS EMPTY. A registry
built from the claim graph alone would produce the empty list and match no
emitted triple. ``def:source-segment`` (A1) gives the component two sources:
that closure, TOGETHER WITH the physical-source assumption the submodule
declares for the source model the claim is stated over, which is A-WCP and
which is not a premise of the proposition and must not be made one.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.blocks import Label, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Matrix, serialize_matrix
from certiqs_key.transmitter.reasons import Refusal, RefusalReason

__all__ = [
    "DECLARED_KINDS_WITHOUT_A_SOUNDNESS_CLAIM",
    "SOUNDNESS_REGISTRY",
    "AliceSideDescriptor",
    "ObligationRecord",
    "SoundnessRegistryEntry",
    "SourceLink",
    "SourceLinkKind",
    "SourceLinkStatus",
    "WitnessKind",
    "check_source_link",
    "source_link_kinds",
]


class SourceLinkKind(StrEnum):
    """The source-stage link kinds, THE CORE'S AND ITS SUBMODULES'.

    ``def:source-link`` (a): "The vocabulary is the kinds this module declares,
    of which there is exactly one, ``source-map``, together with the kinds a
    submodule of this module declares in its own interface."

    ``source-map`` IS DECLARED AND REFUSED: no claim of this repository proves
    the link's identity for it, so it has no registry entry a triple can match
    and a link of that kind is refused with ``link_kind_deferred``, the
    spelling carried verbatim from proof-reductions 1.0.1. ``tagging`` is the
    one kind a submodule adds and the one with a soundness claim
    (``decoy/interface.yaml``, ``link_kind``).
    """

    SOURCE_MAP = "source-map"
    TAGGING = "tagging"


class SourceLinkStatus(StrEnum):
    """``def:source-link`` (g).

    ``exact`` means the identity of (c1) holds WITH NO ERROR TERM -- for a
    constructor link, that the named claim concludes it with none.
    """

    EXACT = "exact"
    CERTIFIED_OUTER = "certified_outer"
    EXPLORATORY_NUMERIC = "exploratory_numeric"


class WitnessKind(StrEnum):
    """``def:source-link`` (c): a channel witness is supplied in one of two ways.

    ``DATA``: both systems finite dimensional and the channel declared, so the
    source identity is an exact matrix identity and is DECIDED on numbers
    (``def:source-segment`` (S3)).

    ``THEOREM_CONSTRUCTOR``: the witness is a named claim of a submodule that
    constructs one channel per member of a declared family and proves the
    identity for it. "(S3) IS THEN NOT DECIDED ON NUMBERS" and the link carries
    an obligation record instead. It is "how a link whose source or target is
    not a matrix is expressed at all" -- the decoy target is a Fock space -- and
    "it is the only way an obligation enters this module: no claim here
    discharges one".
    """

    DATA = "data"
    THEOREM_CONSTRUCTOR = "theorem_constructor"


@dataclass(frozen=True)
class AliceSideDescriptor:
    """One end of a source link: a transmitted system and an ensemble on it.

    ``def:source-link`` (b): both descriptors are read "through their WEIGHTED
    MEMBERS, as every ensemble of this module is", with
    ``tr sigma^in_x = tr sigma^out_x = p_x``, "which is what carrying the
    weights untouched means".

    ``system_dim`` AND ``weighted_members`` ARE OPTIONAL TOGETHER, and the
    reason is the only constructor link that exists: the target of the decoy
    tagging link is the two-mode Fock space, which is separable and infinite
    dimensional and has no matrix. A descriptor that carries neither is a
    descriptor a DATA link may not use, which :func:`check_source_link`
    decides; it is what a constructor link's named claim quantifies over.

    ALICE-SIDE IS PART OF WHAT A DESCRIPTOR IS and is not inferred. "Each names
    a transmitted system and an ensemble on it, and no condition on a source
    link mentions the receiver's systems, its outcome alphabets or its
    measurements."
    """

    #: The declaration's own name for the system, used in reports and in the
    #: declared descriptor family; it is a label and decides nothing.
    name: str
    alphabet: tuple[Label, ...]
    weights: Mapping[Label, Fraction]
    #: ``dim H``, or ``None`` where the system is not finite dimensional.
    system_dim: int | None = None
    #: ``sigma_x``, or ``None`` where the ensemble is fixed by a source model
    #: and not by matrices (``def:source-spec`` (b)).
    weighted_members: Mapping[Label, Matrix] | None = None

    def as_machine_record(self) -> dict[str, object]:
        """Describe a finite or optical source without losing exact entries."""
        return {
            "name": self.name,
            "alphabet": list(self.alphabet),
            "weights": dict(self.weights),
            "system_dim": self.system_dim,
            "weighted_members": (
                None if self.weighted_members is None else {
                    label: serialize_matrix(member)
                    for label, member in self.weighted_members.items()
                }
            ),
        }

    @property
    def is_finite_dimensional(self) -> bool:
        """Whether this descriptor carries matrices at all.

        A data witness's identity is decided on them; a descriptor without
        them is one only a theorem constructor can carry.
        """
        return self.system_dim is not None and self.weighted_members is not None


@dataclass(frozen=True)
class SoundnessRegistryEntry:
    """One row of the closed soundness registry: the triple of Eq. ``eq:registry``."""

    kind: SourceLinkKind
    #: The id of the claim that proves the link's identity at every member of
    #: its declared descriptor family.
    soundness_claim: str
    #: ``A(kind)``: the soundness claim's assumption closure TOGETHER WITH the
    #: physical-source assumption the submodule declares for the model the
    #: claim is stated over. Both halves, in the declared order.
    assumptions: tuple[str, ...]

    @property
    def triple(self) -> tuple[str, str, tuple[str, ...]]:
        """Return the entry as the three declared strings a link is compared against."""
        return (str(self.kind), self.soundness_claim, self.assumptions)


#: THE CLOSED LIST, emitted verbatim with every artefact, and it is the
#: registry of the MODULE VERSION that emitted the artefact rather than a datum
#: a request supplies (``def:source-segment`` (A1)). It is the
#: ``soundness_registry`` output row's table, transcribed: one entry, the decoy
#: submodule's kind ``tagging`` with ``decoy/prop:tagging`` and A-WCP.
#:
#: WHY THE CORE NAMES A SUBMODULE'S CLAIM AND A SUBMODULE'S ASSUMPTION. The
#: registry is emitted by the module that ADMITS the kinds, which is the core;
#: the entry is a datum of its version and is written out in its interface
#: (``transmitter/interface.yaml``, the ``soundness_registry`` output row).
#: Adding a kind is therefore a claim batch and not a configuration, which is
#: what "closed" means.
SOUNDNESS_REGISTRY: Final[tuple[SoundnessRegistryEntry, ...]] = (
    SoundnessRegistryEntry(
        kind=SourceLinkKind.TAGGING,
        soundness_claim="transmitter/decoy/prop:tagging",
        assumptions=("A-WCP",),
    ),
)

#: DECLARED AND NOT ADMITTED. The core declares ``source-map`` and no claim of
#: this repository proves it, so it has no registry entry and a link of that
#: kind is refused with ``link_kind_deferred``. It is named here so that a
#: reader sees the vocabulary and the registry side by side, exactly as the
#: interface's registry table lists it with a null claim.
DECLARED_KINDS_WITHOUT_A_SOUNDNESS_CLAIM: Final[tuple[SourceLinkKind, ...]] = (
    SourceLinkKind.SOURCE_MAP,
)


@dataclass(frozen=True)
class ObligationRecord:
    """Eq. ``eq:obligation``: the triple, plus the family member it asserts.

    ``def:source-link`` (c2): "ITS FIRST THREE COMPONENTS ARE DECIDED, against
    the soundness registry of the artefact that carries the link ... that
    comparison is of declared strings and is what makes an obligation a check
    rather than a label. The fourth is not: which member of the family the
    descriptors are is ASSERTED by the module that emits the link and re-proved
    by no consumer, and no verdict on a number is carried, there being none to
    decide."
    """

    kind: SourceLinkKind
    soundness_claim: str
    assumptions: tuple[str, ...]
    #: The member of the claim's declared descriptor family the emitted
    #: descriptors are. ASSERTED, DECIDED BY NO ONE.
    family_member: str

    @property
    def triple(self) -> tuple[str, str, tuple[str, ...]]:
        """Return the three decided components, in the order (A2) compares them."""
        return (str(self.kind), self.soundness_claim, self.assumptions)

    def as_machine_record(self) -> dict[str, object]:
        """Return the obligation as a machine record. IT CARRIES NO VERDICT."""
        return {
            "kind": str(self.kind),
            "soundness_claim": self.soundness_claim,
            "assumptions": list(self.assumptions),
            "family_member": self.family_member,
        }


@dataclass(frozen=True)
class SourceLink:
    """The tuple of Eq. ``eq:source-link``, slot for slot.

    TODAY'S FORMAT IS A LITERAL CASE OF IT, which this type is shaped to make
    true: "A link that supplies its
    channel as data, whose declared descriptor family is that one descriptor,
    whose sector-map slot is empty and whose entry list is empty, is the tuple
    this definition declared before the slots of (d) and (e) existed, entry for
    entry."
    """

    kind: SourceLinkKind
    source_descriptor: AliceSideDescriptor
    target_descriptor: AliceSideDescriptor
    #: ``Gamma_Xi`` as data, or ``None`` where the witness is a theorem
    #: constructor. The two are exclusive and ``__post_init__`` says so.
    channel_witness: Mapping[Label, Matrix] | None = None
    #: ``D_Xi``, the family of source descriptors the identity is asserted for,
    #: by the descriptors' names. For a DATA link it is that descriptor alone
    #: and the containment is decidable; for a CONSTRUCTOR link it is the
    #: extension of a claim's hypothesis and is named, never decided.
    declared_descriptor_family: tuple[str, ...] = ()
    #: ``Smap_Xi``: the MATCHED PAIR (on ``A``, on the Alice-side descriptor
    #: the certificate is written against). Empty means the one-sector
    #: structure (``def:source-link`` (e)).
    sector_map: tuple[SectorStructure, SectorStructure] | None = None
    #: ``CList_Xi``. A NON-EMPTY LIST IS REFUSED, whatever the kind.
    constraint_entries: tuple[object, ...] = ()
    #: Present exactly when ``constraint_entries`` is non-empty.
    licence: object | None = None
    status: SourceLinkStatus = SourceLinkStatus.EXACT
    #: Per constructor link. ``None`` for a data link, which carries none.
    obligation: ObligationRecord | None = field(default=None)

    def __post_init__(self) -> None:
        """Refuse a tuple that is not a presentation of the type at all."""
        if (self.channel_witness is None) == (self.obligation is None):
            raise MalformedInputError(
                "a source link supplies its channel witness EITHER as data "
                "OR as a theorem constructor with an obligation record "
                "(def:source-link (c)); a link with both or with neither is "
                "not a presentation of the tuple eq:source-link types"
            )
        if self.obligation is not None and self.obligation.kind is not self.kind:
            raise MalformedInputError(
                "an obligation record's first component IS the link's kind "
                f"(eq:obligation); the link declares {self.kind.value!r} and "
                f"the record {self.obligation.kind.value!r}"
            )

    @property
    def witness_kind(self) -> WitnessKind:
        """Return which of the two ways (c) the witness is supplied in.

        DERIVED FROM THE SLOT THAT IS FILLED and never a second declared datum,
        for the reason the source mode is derived from the marginal slot: two
        carriers of one fact are two facts that can disagree.
        """
        return (
            WitnessKind.DATA
            if self.channel_witness is not None
            else WitnessKind.THEOREM_CONSTRUCTOR
        )

    def as_machine_record(self) -> dict[str, object]:
        """Carry the declared link and obligation without inferring a verdict."""
        return {
            "kind": str(self.kind),
            "source_descriptor": self.source_descriptor.as_machine_record(),
            "target_descriptor": self.target_descriptor.as_machine_record(),
            "channel_witness": self.channel_witness,
            "declared_descriptor_family": list(self.declared_descriptor_family),
            "sector_map": self.sector_map,
            "constraint_entries": list(self.constraint_entries),
            "licence": self.licence,
            "status": str(self.status),
            "obligation": (
                None if self.obligation is None else self.obligation.as_machine_record()
            ),
        }


def source_link_kinds(segment: Sequence[str | SourceLink]) -> tuple[str, ...]:
    """Return the declared kind of each entry of a segment, in order.

    THE SEGMENT SLOT TAKES EITHER SPELLING, and this is the one place that
    matters. A specification may carry its segment as a tuple of
    KIND STRINGS, "so that the refusal names what arrived", or a submodule may
    supply typed links. Reading the kind off either keeps
    :func:`certiqs_key.transmitter.artifact.emit_artifact`'s segment decision
    the same decision, which is what the interface's ``source_segment`` row
    demands: "NOTHING AN IMPLEMENTATION REFUSES TODAY CHANGES".
    """
    return tuple(
        entry if isinstance(entry, str) else str(entry.kind) for entry in segment
    )


def check_source_link(
    link: SourceLink,
    *,
    assumption_ledger: Sequence[str],
    from_admitting_module: bool,
    registry: Sequence[SoundnessRegistryEntry] = SOUNDNESS_REGISTRY,
) -> Refusal | None:
    """Decide (A1)--(A3) and the two admission conditions, or return ``None``.

    Called by the admitting submodule and by consumers of its nonempty
    segment. The caller supplies the result of the supplier-admission check;
    the link data alone do not establish ``from_admitting_module``.

    THE ORDER OF THE DECISIONS IS THIS FILE'S and no claim fixes it. What the
    claims DO fix is which conditions there are, and each is taken below with
    its locator:

    * a link with a NON-EMPTY entry list is refused WHATEVER ITS KIND
      (``def:source-segment``, the admission rule; ``def:source-link`` (f)):
      no claim of this repository transports an Alice-side entry;
    * a link of a kind with no registry entry is refused with
      ``link_kind_deferred``, which for the core's ``source-map`` is the
      spelling it has always had;
    * (A3), provenance: a non-empty segment is accepted only inside an artefact
      emitted by the module that admits its links. IT IS DECIDED OF EVERY LINK,
      before the two branches below and not inside one of them: the condition is
      stated on the segment, "WHATEVER ITS TRIPLES", and a data link carries no
      triple, so a check that ran only where one exists would let through
      exactly the links (A3) is about;
    * a DATA link whose declared family does not contain its own source
      descriptor asserts nothing about the descriptor it carries and is
      refused. FOR A CONSTRUCTOR LINK THAT CONDITION IS NOT DECIDABLE and this
      reason does not fire, which ``def:source-link`` (d) says in terms rather
      than leaving an implementer to find that a named refusal cannot bite;
    * (A2), the triple against the registry, entry by entry as declared
      strings, and every assumption of the matched entry in the ledger.

    WHAT IT DOES NOT DECIDE, stated because the absence is the point: that the
    named claim's conclusion applies to THESE descriptors. "Family membership
    is asserted by the emitting module and recorded in the obligation record,
    and no consumer re-proves a theorem."

    ``assumption_ledger`` IS READ AS A LIST OF SHORT IDS. Eq. ``eq:registry``
    and (A2) are written on "the assumption SHORT IDS" on both sides, so that is
    what this function compares; the emitted
    :attr:`certiqs_key.transmitter.artifact.TransmitterArtifact.assumption_ledger`
    carries the MACHINE KEYS of
    :data:`~certiqs_key.transmitter.reasons.ASSUMPTION_MACHINE_KEYS`, and the
    declared mapping between the two spellings is the interface's
    ``assumption_ledger.ledger_spelling``. The two meet at the compiler's
    boundary, which adds to the ledger it passes here the short id of every
    machine key that ledger carries
    (:func:`certiqs_key.protocol_compiler.chain.check_source_segment`).
    """
    if link.constraint_entries:
        return Refusal(
            reason=RefusalReason.SOURCE_LINK_ENTRY_PRESENT,
            detail=(
                f"the {link.kind.value!r} link carries "
                f"{len(link.constraint_entries)} transported constraint "
                "entries; NO CLAIM OF THIS REPOSITORY TRANSPORTS AN ALICE-SIDE "
                "ENTRY, and a non-empty list is refused whatever the kind "
                "(def:source-segment, the admission rule)"
            ),
        )
    if link.licence is not None and not link.constraint_entries:
        return Refusal(
            reason=RefusalReason.SOURCE_LINK_ENTRY_PRESENT,
            detail=(
                f"the {link.kind.value!r} link carries a licence record with an "
                "EMPTY entry list; the licence is present exactly when the list "
                "is non-empty (def:source-link (f))"
            ),
        )
    entry = _registry_entry_for(link.kind, registry)
    if entry is None:
        return Refusal(
            reason=RefusalReason.LINK_KIND_DEFERRED,
            detail=(
                f"the kind {link.kind.value!r} is declared and has no entry in "
                "the emitted soundness registry: no claim of this repository "
                "proves the link's identity for it, so it is declared, "
                "reserved and refused (def:source-link (a))"
            ),
        )
    if not from_admitting_module:
        # (A3) IS DECIDED OF EVERY LINK AND NOT ONLY OF A CONSTRUCTOR ONE, and
        # it is decided BEFORE the split below. The condition is stated on the SEGMENT
        # -- "a non-empty source segment is accepted only inside an artefact
        # emitted by the module that admits its links. A segment assembled from
        # links a consumer received IN ANY OTHER WAY is refused, WHATEVER ITS
        # TRIPLES" -- and a data link has no triple at all, so a check that ran
        # only where one exists would let exactly the links (A3) is about
        # through: the ones a consumer assembled itself.
        return Refusal(
            reason=RefusalReason.SOURCE_SEGMENT_NOT_FROM_ADMITTING_MODULE,
            detail=(
                "a non-empty source segment is accepted only inside an artefact "
                "emitted by the module that admits its links; a segment "
                "assembled from links received in any other way is refused, "
                "WHATEVER ITS TRIPLES and whichever way its witness is supplied "
                "-- the registry says which kinds this repository has proved, "
                "not that a particular link was built by the module that proved "
                "them (def:source-segment (A3))"
            ),
        )
    if link.witness_kind is WitnessKind.DATA:
        if link.source_descriptor.name not in link.declared_descriptor_family:
            return Refusal(
                reason=RefusalReason.SOURCE_LINK_FAMILY_EXCLUDES_ITS_DESCRIPTOR,
                detail=(
                    "the declared descriptor family "
                    f"{list(link.declared_descriptor_family)} does not contain "
                    f"the link's own source descriptor "
                    f"{link.source_descriptor.name!r}, so the witness's "
                    "identity is asserted at no descriptor the link carries "
                    "(def:source-link (d))"
                ),
            )
        return None
    obligation = link.obligation
    assert obligation is not None  # witness_kind is THEOREM_CONSTRUCTOR
    if obligation.triple != entry.triple:
        return Refusal(
            reason=RefusalReason.SOURCE_LINK_NOT_IN_REGISTRY,
            detail=(
                f"the obligation triple {obligation.triple} matches no entry of "
                "the artefact's emitted soundness registry, which carries "
                f"{entry.triple} for this kind. BOTH COMPONENTS of the third "
                "slot are compared -- the soundness claim's assumption closure "
                "and the physical-source assumption the submodule declares for "
                "its model -- so a link naming one and omitting the other is "
                "refused exactly as one naming neither (def:source-segment "
                "(A1), (A2))"
            ),
        )
    missing = [name for name in entry.assumptions if name not in assumption_ledger]
    if missing:
        return Refusal(
            reason=RefusalReason.SOURCE_LINK_ASSUMPTION_NOT_IN_LEDGER,
            detail=(
                f"the registry entry of {link.kind.value!r} names "
                f"{missing}, which the emitted assumption ledger "
                f"{list(assumption_ledger)} does not carry; the assumptions an "
                "obligation carries must TRAVEL (def:source-segment (A2))"
            ),
        )
    return None


def _registry_entry_for(
    kind: SourceLinkKind, registry: Sequence[SoundnessRegistryEntry]
) -> SoundnessRegistryEntry | None:
    """Return the registry entry of a kind, or ``None`` where the kind has none."""
    for entry in registry:
        if entry.kind is kind:
            return entry
    return None
