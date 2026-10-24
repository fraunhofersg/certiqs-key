"""Typed links and chains: Definitions ``def:link``, ``def:chain``, Thm. ``thm:chain``.

THE COUNT, STATED ONCE
======================
Definition ``def:link`` states it and this file reproduces it exactly: a link
has TEN slots, SIX of them REQUIRED -- source family, target, channel witness,
reachable-set statement, transported constraint entries, licence record -- and
the remaining FOUR ``stage``, ``kind``, the carried operator pair and
``status``. Wherever a claim says "the six required fields" it means the first
group; THE TUPLE ``eq:link`` IS THE WHOLE OF WHAT AN IMPLEMENTER BINDS
(``link_record`` of interface.yaml, ``count_note``).

:class:`Link` has exactly those ten fields and :data:`REQUIRED_SIX` names the
first group, so the count is checkable from the code rather than from a comment.

OPEN IMPLEMENTATION CHOICE 6 OF 12 IS DECIDED HERE: THE LINK IDENTIFIER
=======================================================================
``interface.yaml``: "The ten slots carry NO identifier and no index: a chain is
an ORDERED LIST, and 'the order is emitted as data and is never inferred from
artifact creation time' ... Whether an implementation additionally gives each
link a stable identifier -- as the existing wire ``ReductionLink.link_id`` does
-- IS NOT DECIDED HERE, and an identifier is NOT an eleventh slot."

THE DECISION: :class:`Link` carries a ``link_id``, AND IT IS NOT A SLOT. It is
declared after the ten in the class body, is excluded from :data:`SLOTS` and
from :meth:`Link.slot_values`, and plays no part in any condition of Definition
``def:chain``: (C1) compares ``(system, POVM)`` pairs and (C2) compares carried
tuples, neither of which reads an identifier. What the identifier buys is that a
constraint entry's ``certified_against`` and a refusal's ``detail`` can name a
link, and that a chain in an emitted artifact can be read back link by link
without positional counting. What it must not buy is ORDER: the chain is an
ordered list, :meth:`Chain.composite_order` reads the list, and no function here
sorts by identifier.

THE ORDERING RULE IS A REFUSAL WITH A REASON, NOT A CONVENTION
==============================================================
Remark ``rem:ordering`` states (C3) that way and gives the reason: a
``source``-stage link's security argument "re-parameterizes the first-round
attack as ``A_1 = A'_1 o Gamma`` RANGING OVER ALL CPTP MAPS", while a
``receiver``-stage link, by Theorem ``thm:licence``, "hands the analysis an
attack set that is A PROPER SUBSET of the CPTP maps. Applying a source link after
that is therefore NOT FREE: what must additionally hold is the inclusion
``A^real_1 o Gamma subset A^virtual_1``, and NOTHING IN THIS CONTRACT ESTABLISHES
IT FOR ANY ``Gamma``."

The refusal can only be reached by a declaration that populates the source
stage, and such a declaration also trips ``link_kind_deferred``, since
``source-map`` is reserved. BOTH REASONS EXIST
BECAUSE THEY ARE DIFFERENT FAILURES: one is about ORDER, the other about
AVAILABILITY, and a future version implementing source maps keeps the first and
drops the second.

WHAT (C3) RESTS ON IS THE REASON AND NOT THE RULE. The
order is decided and the refusal string is fixed. ``lem:precomposition`` establishes the
inclusion ``AttSet^real o Gamma`` inside ``AttSet^virtual`` for every LICENSED list, and
``thm:two-sided`` (i) proves that the two orders give ONE AND THE SAME map of
strategies, so (C3) records how the artefact presents its two segments and does not
carry the soundness. What stays a refusal is the ADMISSION RULE of
``def:chain`` -- a chain with a non-empty source segment is admitted only with
licensed entries and only in trusted-source mode -- and that rule bites where
an entry is DECLARED, which is the consuming declaration; this module adds no
reason string for it and can violate none, every entry it emits carrying a real
scalar (``thm:licence`` (iv)).

THE COMPOSITE STATUS IS A POLICY IN ONE DIRECTION AND A THEOREM IN THE OTHER
============================================================================
Theorem ``thm:chain`` (iv): "the composite ``status`` is ``exact`` whenever every
link's is; this module assigns no other composite value, and a chain mixing an
``exact`` link with one carrying an error term is REFUSED rather than given a
composite status, because no theorem of this contract converts an error term into
a security penalty. THAT SECOND HALF IS A POLICY OF THIS MODULE, NOT A CONVERSE
THIS CONTRACT PROVES." :meth:`Chain.composite_status` returns ``exact`` or
``None``, and ``None`` is the refusal ``approximate_squashing_unsupported`` --
never a third status.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final

from certiqs_key.foundations.exact import Matrix, equal
from certiqs_key.reductions.channels import ChannelWitness, compose_witnesses
from certiqs_key.reductions.constraints import AttackSetLicence, ConstraintEntry
from certiqs_key.reductions.reasons import LinkKind, LinkStage, LinkStatus

__all__ = [
    "REQUIRED_SIX",
    "SLOTS",
    "SOURCE_SEGMENT_DOCKING_POINT",
    "Chain",
    "ChainConditionOutcome",
    "Link",
    "SystemFamily",
    "identity_link",
    "source_stage_is_empty",
]

#: THE DOCKING POINT FOR THE TRANSMITTER'S SOURCE-LINK TYPE, named here so that
#: it is one place and not several.
#:
#: WHAT ``def:link`` NOW SAYS: "A link with ``stage = source`` is a SOURCE LINK
#: in the sense of Definition def:source-link of the transmitter ... The
#: transmitter's type is what this module reads, as that module now states it:
#: the channel witness is supplied either AS DATA ... or AS A THEOREM
#: CONSTRUCTOR, in which case the link carries an OBLIGATION RECORD -- the
#: triple of that module's Eq. eq:obligation ... which this module neither
#: computes nor re-decides -- together with the member of its DECLARED
#: DESCRIPTOR FAMILY that its descriptors are". Which kinds are admitted, and
#: which components a consumer decides on data, is that module's
#: ``def:source-segment`` (A1) to (A3), and "this module re-decides none of
#: them, adds none, and adds no source-stage kind".
#:
#: THE TYPED LINK EXISTS, AND THIS IS WHAT REMAINS.
#: :mod:`certiqs_key.transmitter.links` holds ``SourceLink`` (the ten slots of
#: ``eq:source-link``), ``SourceLinkKind``, ``AliceSideDescriptor``,
#: ``ObligationRecord``, ``SoundnessRegistryEntry`` and the closed
#: ``SOUNDNESS_REGISTRY`` -- so the type this module reads is not only a
#: list of kind strings.
#:
#: WHAT THIS MODULE READS, AND WHY IT IS THE STRINGS.
#: ``TransmitterArtifact.source_segment`` is the emitted row, typed
#: ``tuple[str | SourceLink, ...]``: always emitted, EMPTY in every artefact
#: the matrix-source path emits, and NON-EMPTY -- typed ``SourceLink``
#: records admitted by kind under ``transmitter/def:source-segment`` -- in the
#: artefact the decoy submodule emits (``DecoySourceDeclaration.
#: as_transmitter_artifact``). :attr:`Chain.source_segment` here is still typed
#: as kind strings, and no reductions artefact carries a non-empty segment:
#: :func:`certiqs_key.reductions.docking.reduction_chain` refuses one.
#:
#: THE REMAINING STEP, IN ONE PLACE. When the transmitter's artefact emits its
#: segment as ``tuple[SourceLink, ...]``, :attr:`Chain.source_segment` takes that
#: type in place of the kind strings and
#: :meth:`Chain.source_composite_witness` reads each link's own
#: ``channel_witness`` or ``obligation`` in place of naming its kind. NO OTHER
#: SITE OF THIS MODULE READS THE SEGMENT, which is what this constant exists to
#: keep true, and this module decides no condition of a source link either way
#: (``def:link``: "this module re-decides none of them, adds none, and adds no
#: source-stage kind"). :func:`certiqs_key.reductions.docking.reduction_chain`
#: refuses a non-empty segment rather than dropping it, the consumer's wire
#: record having no slot for one.
#:
#: The admission rule of ``def:chain`` -- licensed entries only, and only in
#: trusted-source mode -- is decided by the consumer that assembles a
#: declaration's source segment with its constraint list, which is the protocol
#: compiler. This module adds no refusal reason for it
#: and could not violate it: every entry it emits carries a real scalar
#: (``thm:licence`` (iv)).
SOURCE_SEGMENT_DOCKING_POINT: Final[str] = (
    "Chain.source_segment reads transmitter/TransmitterArtifact.source_segment, "
    "typed here as a tuple of declared source-link kinds; a non-empty segment "
    "is admitted by kind under transmitter/def:source-segment and refused by "
    "reduction_chain rather than dropped; the typed SourceLink of "
    "certiqs_key.transmitter.links plugs in at that field and at "
    "Chain.source_composite_witness when the transmitter's ARTEFACT emits its "
    "segment as those records, and nowhere else in this module"
)

#: The ten slots of Eq. ``eq:link``, in the tuple's own order.
SLOTS: Final[tuple[str, ...]] = (
    "stage",
    "kind",
    "source_family",
    "target",
    "channel_witness",
    "carried_operator_pair",
    "reachable_set_statement",
    "constraint_entries",
    "licence",
    "status",
)

#: The six REQUIRED fields of Definition ``def:link``, as ``link_record`` of
#: interface.yaml groups them. The other four are ``stage``, ``kind``, the
#: carried operator pair and ``status``.
REQUIRED_SIX: Final[tuple[str, ...]] = (
    "source_family",
    "target",
    "channel_witness",
    "reachable_set_statement",
    "constraint_entries",
    "licence",
)


@dataclass(frozen=True)
class SystemFamily:
    """``(B, M)``: THE SYSTEM AND THE POVM, which is half of each descriptor.

    Definition ``def:link`` slots 3 and 4 are pairs, and Definition ``def:chain``
    (C1) compares the PAIR: "``(B^out_i, M^out_i) = (B^in_{i+1}, M^in_{i+1})``".
    A chain whose systems agree and whose POVMs do not is ``chain_ill_formed``,
    and that is the case an implementation carrying only system dimensions would
    miss.

    ``povm`` IS A LIST OF SECTOR-BLOCK LISTS where it is present: one entry per
    outcome, each entry one square array per sector in the sector map's order,
    the form the emitted ``target_povm`` carries and the only form a
    ``Q``-operator takes here (spec/architecture.md 2.8-2.9). (C1)'s comparison is
    therefore block by block.

    ``povm`` is ``None`` where the family is declared symbolically -- the
    physical side of a receiver-stage link lives on a Fock space and its elements
    are not materialisable. Two families with ``povm = None`` compare by
    ``description`` alone, which is a comparison of DECLARED data and not of
    matrices; the description is what the declaration carries.
    """

    description: str
    dimension: int | None = None
    povm: tuple[tuple[Matrix, ...], ...] | None = None

    def matches(self, other: SystemFamily) -> bool:
        """Whether this family is the same ``(system, POVM)`` pair as ``other``."""
        if self.description != other.description:
            return False
        if self.dimension != other.dimension:
            return False
        if self.povm is None or other.povm is None:
            return self.povm is None and other.povm is None
        if len(self.povm) != len(other.povm):
            return False
        return all(
            len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b, strict=True))
            for a, b in zip(self.povm, other.povm, strict=True)
        )


@dataclass(frozen=True)
class Link:
    """A typed link: the TEN slots of Eq. ``eq:link``, and nothing else.

    ``link_id`` follows the ten and is NOT one of them; the module docstring
    records the decision and its bounds.

    ``carried_operator_pair`` is ``(O^_out, O_in)``: the operators the link
    carries on its target and their pull-backs on its source. Definition
    ``def:chain`` (C2) compares ``O^_out_i`` with ``O_in_{i+1}`` "so that each
    declared operator on the final target has a pull-back AT EVERY INTERMEDIATE
    STAGE".

    ``licence`` is present EXACTLY WHEN ``constraint_entries`` is non-empty; the
    invariant is checked by :meth:`licence_presence_holds` and enforced by the
    validation rule, whose two directions carry different reasons.
    """

    stage: LinkStage
    kind: LinkKind
    source_family: SystemFamily
    target: SystemFamily
    channel_witness: ChannelWitness
    carried_operator_pair: tuple[tuple[str, ...], tuple[str, ...]]
    reachable_set_statement: str
    constraint_entries: tuple[ConstraintEntry, ...]
    licence: AttackSetLicence | None
    status: LinkStatus
    link_id: str = field(default="")

    def slot_values(self) -> dict[str, object]:
        """Return the TEN slots by name; ``link_id`` is deliberately absent."""
        return {name: getattr(self, name) for name in SLOTS}

    def licence_presence_holds(self) -> bool:
        """Whether ``licence`` is present exactly when ``CList`` is non-empty."""
        return (self.licence is not None) == bool(self.constraint_entries)


def identity_link(
    family: SystemFamily,
    *,
    reachable_set_statement: str = "the whole declared input family S^ph",
    link_id: str = "L-identity",
    carried: tuple[str, ...] = (),
) -> Link:
    """Return the identity link of Example ``ex:identity``, field for field.

    "For an ALREADY-FINITE receiver -- an ideal qubit protocol, or any fixture
    whose POVM the engine can consume directly -- the chain has ONE link with
    ``stage = receiver``, ``kind = identity``, ``Lambda_l = id``,
    ``M^out = M^in``, the carried tuple EMPTY OR THE IDENTITY ON ANY DECLARED
    OPERATORS, ``S^rch_l`` the whole declared input family, ``CList_l`` empty, NO
    LICENCE, and ``status = exact``."

    IT IS RECORDED RATHER THAN OMITTED, and that is a design commitment: "AN
    EMPTY CHAIN WOULD LEAVE THE ARTIFACT UNABLE TO SAY WHETHER A REDUCTION WAS
    PERFORMED AND FOUND TRIVIAL OR NEVER CONSIDERED, and the composition order of
    decision (2) has to be carried EVEN WHEN THERE IS NOTHING TO ORDER."

    It is a squashing relation by reflexivity (Proposition ``prop:preorder``,
    ``M <=_id M``), so Theorem ``thm:chain`` applies and returns the physical
    model unchanged.
    """
    return Link(
        stage=LinkStage.RECEIVER,
        kind=LinkKind.IDENTITY,
        source_family=family,
        target=family,
        channel_witness=ChannelWitness(
            identity=f"{link_id}:id",
            equation="Lambda_l = id (ex:identity; prop:preorder reflexivity)",
        ),
        carried_operator_pair=(carried, carried),
        reachable_set_statement=reachable_set_statement,
        constraint_entries=(),
        licence=None,
        status=LinkStatus.EXACT,
        link_id=link_id,
    )


@dataclass(frozen=True)
class ChainConditionOutcome:
    """The verdict of Definition ``def:chain``'s three conditions.

    ``failing_index`` names the first position at which a condition fails, so
    that a refusal can say WHICH pair broke it rather than that some pair did.
    """

    composable: bool
    tuple_chained: bool
    stage_ordered: bool
    failing_index: int | None = None
    detail: str = ""

    @property
    def holds(self) -> bool:
        """Whether all three conditions hold."""
        return self.composable and self.tuple_chained and self.stage_ordered

    @property
    def first_failing_condition(self) -> str | None:
        """Return the first failing condition IN DEFINITION ``def:chain``'S ORDER.

        (C1), then (C2), then (C3) -- the order the definition lists them in,
        and therefore the one a refusal names. A chain failing more than one
        still names exactly one, and always the same one.
        """
        if not self.composable:
            return "C1"
        if not self.tuple_chained:
            return "C2"
        if not self.stage_ordered:
            return "C3"
        return None


@dataclass(frozen=True)
class Chain:
    """A reduction chain: THE PAIR of a source segment and a receiver segment.

    Definition ``def:chain``, "A reduction chain is a
    PAIR ``(Chain_src, Chain_rec)`` of a source segment and a receiver
    segment." The receiver segment ``(l_1, ..., l_k)``, ``k >= 1``, is
    :attr:`links` and is what every condition (C1)-(C3) is about; the source
    segment is the transmitter's (:attr:`source_segment`).

    The list is ORDERED and the order is the data: the conventions block
    ``composition_order`` says "LATER LINKS ACT LATER, so
    ``Lambda = Lambda_k o ... o Lambda_1`` ... THE ORDER IS EMITTED AS DATA AND
    IS NEVER INFERRED FROM ARTIFACT CREATION TIME".

    ITS COMPOSITE IS THE PAIR :meth:`composite` of Eq. ``eq:chaincomposite``:
    the SOURCE composite ``Xi = Xi_{L_s} o ... o Xi_1``, the identity when
    ``L_s = 0``, and the RECEIVER composite
    ``Lambda = Lambda_{l_k} o ... o Lambda_{l_1}``. "The two act on different
    systems and no condition above relates them"; what the pair composes to AS
    A REDUCTION is ``thm:two-sided``, and ``thm:chain`` (i)-(iv) -- which is
    what :meth:`composite_witness`, :meth:`composite_status` and
    :meth:`conditions` decide -- reads the SECOND MEMBER ALONE.
    """

    links: tuple[Link, ...]
    #: ``Chain_src``: the source segment, of the TRANSMITTER'S type, and EMPTY
    #: IN EVERY ARTEFACT THIS MODULE EMITS TODAY. See
    #: :data:`SOURCE_SEGMENT_DOCKING_POINT` for what it is typed as today and
    #: what plugs in here.
    source_segment: tuple[str, ...] = ()

    def conditions(self) -> ChainConditionOutcome:
        """Decide (C1) composable, (C2) tuple-chained, (C3) stage-ordered.

        ALL THREE ARE EVALUATED, always. Returning at the first failure would
        make the record say "stage-ordered holds" about a chain whose stages
        were never read, and the outputs table's ``verification_report`` carries
        outcomes rather than the first thing that went wrong. Which failure the
        REFUSAL names is a separate question, answered by
        :attr:`first_failing_condition` in Definition ``def:chain``'s own order
        -- the same discipline the consuming module states for its own chain
        checker, "so that a refusal points where the contract says it points
        rather than at whichever condition an implementation happened to test
        last".

        Each is decided from declared data: (C1) compares the ``(system, POVM)``
        pairs, (C2) compares the carried tuples, (C3) reads the stages. Nothing
        is inferred and nothing is repaired.
        """
        if not self.links:
            return ChainConditionOutcome(
                composable=False,
                tuple_chained=False,
                stage_ordered=False,
                failing_index=None,
                detail="a chain has at least one link (def:chain, k >= 1)",
            )
        composable = True
        tuple_chained = True
        stage_ordered = True
        failing_index: int | None = None
        details: list[str] = []
        for index in range(len(self.links) - 1):
            current, following = self.links[index], self.links[index + 1]
            if composable and not current.target.matches(following.source_family):
                composable = False
                failing_index = index if failing_index is None else failing_index
                details.append(
                    f"(C1) composable fails at link {index}: its target is not "
                    f"link {index + 1}'s source family; the PAIR (system, POVM) "
                    "must agree, not the system alone"
                )
            if (
                tuple_chained
                and current.carried_operator_pair[0]
                != following.carried_operator_pair[1]
            ):
                tuple_chained = False
                failing_index = index if failing_index is None else failing_index
                details.append(
                    f"(C2) tuple-chained fails at link {index}: its carried "
                    f"O^_out is not link {index + 1}'s O_in, so a declared "
                    "operator on the final target has no pull-back at that "
                    "intermediate stage"
                )
        seen_receiver = False
        for index, link in enumerate(self.links):
            if link.stage is LinkStage.RECEIVER:
                seen_receiver = True
            elif seen_receiver and stage_ordered:
                stage_ordered = False
                failing_index = index if failing_index is None else failing_index
                details.append(
                    f"(C3) stage-ordered fails at link {index}: a source-stage "
                    "link follows a receiver-stage link (rem:ordering)"
                )
        return ChainConditionOutcome(
            composable=composable,
            tuple_chained=tuple_chained,
            stage_ordered=stage_ordered,
            failing_index=failing_index,
            detail="; ".join(details),
        )

    def composite_status(self) -> LinkStatus | None:
        """Theorem ``thm:chain`` (iv): ``exact`` iff every link is, else ``None``.

        ``None`` is not a third status: it is the state in which this module
        REFUSES rather than assigning one, "because no theorem of this contract
        converts an error term into a security penalty".
        """
        if all(link.status is LinkStatus.EXACT for link in self.links):
            return LinkStatus.EXACT
        return None

    def composite_witness(self, identity_name: str = "Lambda-Chain") -> ChannelWitness:
        """Return ``Lambda_Chain = Lambda_{l_k} o ... o Lambda_{l_1}``.

        Theorem ``thm:chain`` (i) adds the adjoint's order, which is the
        opposite: ``Lambda_Chain^dagger = Lambda_{l_1}^dagger o ... o
        Lambda_{l_k}^dagger``. The record carries the LINK order, so a reader
        never has to know which of the two a field means.
        """
        return compose_witnesses(
            identity_name, [link.channel_witness for link in self.links]
        )

    def source_composite_witness(
        self, identity_name: str = "Xi-Chain"
    ) -> ChannelWitness:
        """Return ``Xi_Chain = Xi_{L_s} o ... o Xi_1``, THE IDENTITY WHEN EMPTY.

        Definition ``def:chain``, Eq. ``eq:chaincomposite`` and its closing
        paragraph: "Where the source segment is empty, ``L_s = 0``, the source
        composite is the identity, ``A^v = A^sig``, the virtual ensemble is the
        specified one, and the pair carries exactly the receiver composite."
        That is the case of every artefact this module emits today, so this
        witness is the identity on every one of them.

        WHAT IT IS NOT: a channel this module composes, decides or re-decides.
        A source link's witness, its declared descriptor family and its
        obligation record are the transmitter's, and ``def:link`` says this
        module "re-decides none of them, adds none, and adds no source-stage
        kind".
        """
        if not self.source_segment:
            # L_s = 0: THE IDENTITY, and it is written out rather than composed
            # from nothing -- a composite witness composes at least one witness,
            # and the identity of an empty composition is not one of them.
            return ChannelWitness(
                identity=f"{identity_name}:id",
                equation=(
                    "Xi_Chain = id: the source segment is EMPTY (L_s = 0), so "
                    "A^v = A^sig, the virtual ensemble is the specified one and "
                    "the pair carries exactly the receiver composite "
                    "(def:chain, eq:chaincomposite and its closing paragraph)"
                ),
            )
        return compose_witnesses(
            identity_name,
            [
                ChannelWitness(
                    identity=f"{identity_name}:{kind}",
                    equation=(
                        f"Xi_{position + 1} = the source link's declared "
                        f"witness for kind {kind!r} "
                        "(transmitter/def:source-link; this module re-decides "
                        "none of its conditions)"
                    ),
                )
                for position, kind in enumerate(self.source_segment)
            ],
        )

    def composite(self) -> tuple[ChannelWitness, ChannelWitness]:
        """Return the composite of ``def:chain``: THE PAIR ``(Xi, Lambda)``.

        Eq. ``eq:chaincomposite``. The first member is the source composite,
        the identity where the segment is empty; the second is the receiver
        composite :meth:`composite_witness`, which is what ``thm:chain``
        (i)-(iv) read and what every emitted record of this module carries.

        THE TWO ACT ON DIFFERENT SYSTEMS AND NOTHING HERE RELATES THEM:
        ``Xi_Chain`` carries the virtual transmitted system to the transmitted
        one, on Alice's side, and ``Lambda_Chain`` the measured system to the
        target, on the receiver's. What the pair composes to AS A REDUCTION is
        ``thm:two-sided``, which is mathematics of the generic layer and has no
        code of its own.
        """
        return (self.source_composite_witness(), self.composite_witness())

    def composite_order(self) -> tuple[str, ...]:
        """Return the link identifiers in the order the channels ACT.

        THE RECEIVER SEGMENT'S, which is where this module's links are: a
        source-stage link is the transmitter's and carries that module's
        identifiers, not these.
        """
        return tuple(link.link_id for link in self.links)

    def final_target(self) -> SystemFamily:
        """Return ``(B^out_k, M^out_k)``, the chain's final target."""
        return self.links[-1].target

    def initial_family(self) -> SystemFamily:
        """Return ``(B^in_1, M^in_1)``, the chain's physical starting point."""
        return self.links[0].source_family


def source_stage_is_empty(links: Sequence[Link]) -> bool:
    """Whether the declared receiver segment carries no source-stage link.

    WHAT THIS PREDICATE IS: a statement about DATA. Whether a chain's source
    segment is empty "is DATA a consumer reads, not an assumption it must
    inherit" -- the emitted ``reduction_chain`` carries the segment itself --
    and no claim of this module rests on its being empty, which is why no row
    of this ledger names it (``interface.yaml``,
    ``assumption_ledger.no_row_for_an_empty_source_segment``).

    The stage EXISTS, is ordered first, and is empty in every artefact this
    module emits; carrying it costs "one enumerated field", and not carrying it
    would cost "a later decoy-state link composed in the wrong order without
    anything in the artifact recording that there was an order".
    """
    return all(link.stage is LinkStage.RECEIVER for link in links)
