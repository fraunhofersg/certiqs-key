"""The consumer's side of the reductions docking: its context and its report.

``ChainContext``, ``ChainReport``, ``ConditionOutcome`` and ``check_chain``
are the COMPILER'S EVALUATION OF ITS OWN CHAIN CONDITIONS (C1)-(C5) -- a
consumer's behaviour, not a shared wire record -- so they live with the module
that owns them, beside the conversion in :mod:`certiqs_key.reductions.docking`
that builds the chain itself.

WHY IT IS HERE AND NOT IN :mod:`certiqs_key.reductions`. The two functions
below EVALUATE THIS MODULE'S CONDITIONS on an artefact another module emitted.
A reductions-side implementation would have to name this module's records,
which would make a supplier import its consumer; imports point downward only
(PRINCIPLES.md section 4). So the direction is the other one: this file names
:mod:`certiqs_key.reductions.docking`, which converts the emitted artefact into
the frozen records of :mod:`certiqs_key.domain.chain`, and then runs
:func:`certiqs_key.protocol_compiler.chain.check_chain` over them.

WHAT THE CALLER SUPPLIES AND WHY. ``physical_descriptor`` and ``physical_povm``
are the CALLER'S, exactly as they are on the reductions side: the physical
family lives on the receiver's own space and "the supplier emits no
above-cutoff block, so this module cannot materialise it". Where the caller has
none, the empty mapping is passed and (C4) -- the only condition that reads it
-- is ``not checked`` already, because no link of an emitted chain supplies its
channel as data. That outcome NAMES A-LINK, which is the correct answer rather
than a gap: the necessary condition was not decidable and the obligation is
transferred, not discharged.

THE OUTCOME CORRESPONDENCE IS THE IDENTITY ON ``V``, and that is the
supplier's statement and not this module's: "squashing does not relabel
outcomes, and every relabelling has already happened" before the emission. So
``V^ph = V`` and ``gamma = id``, which is a total surjection and satisfies (C2)
by construction.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from certiqs_key.domain.chain import (
    ChainLink,
    LinkStatus,
    ReductionChain,
    Segment,
    Side,
    SystemDescriptor,
)
from certiqs_key.domain.constraints import (
    AttackSetLicense,
    ConstraintEntry,
)
from certiqs_key.domain.families import FactorisedFamily
from certiqs_key.foundations.blocks import (
    BlockKind,
    BlockOperator,
    FactorisedSectorMap,
    Label,
    SectorFactor,
    SectorStructure,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Matrix
from certiqs_key.protocol_compiler.chain import ChainContext, ChainReport, check_chain
from certiqs_key.reductions import docking
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.factors import FactorEmission
from certiqs_key.transmitter.links import SourceLink, WitnessKind

__all__ = [
    "FactorisedSlots",
    "chain_context",
    "chain_report",
    "dock_source_segment",
    "factorised_slots",
    "source_chain_segment",
]


def dock_source_segment(
    receiver_chain: ReductionChain, links: tuple[SourceLink, ...]
) -> ReductionChain:
    """Return ``receiver_chain`` with the typed constructor segment attached."""
    if receiver_chain.source_segment:
        raise MalformedInputError(
            "dock_source_segment attaches the one source segment to a receiver "
            "chain whose source segment is empty; two carriers could disagree"
        )
    return ReductionChain(
        source_segment=source_chain_segment(links),
        receiver_segment=receiver_chain.receiver_segment,
        outcome_correspondence=receiver_chain.outcome_correspondence,
    )


def source_chain_segment(links: tuple[SourceLink, ...]) -> tuple[ChainLink, ...]:
    """Adapt theorem-constructor source links to the compiler chain record.

    The original typed links remain on :class:`SourcePart` for (A1)--(A3).
    This projection carries only the data (S1)--(S3) read.  A constructor has
    no numerical channel, so S3 is ``not checked`` and names A-LINK.  The
    transmitter's data-link witness is indexed by signal rather than a Kraus
    representation and is deliberately unsupported here instead of coerced.
    """
    adapted: list[ChainLink] = []
    for position, link in enumerate(links, start=1):
        if link.witness_kind is not WitnessKind.THEOREM_CONSTRUCTOR:
            raise MalformedInputError(
                "source_chain_segment currently adapts theorem-constructor "
                "links only; a data SourceLink carries a per-signal witness, "
                "not the Kraus tuple ChainLink.channel requires"
            )

        def descriptor(source: object) -> SystemDescriptor:
            from certiqs_key.transmitter.links import AliceSideDescriptor

            if not isinstance(source, AliceSideDescriptor):  # pragma: no cover
                raise MalformedInputError("a source-link end is an Alice descriptor")
            return SystemDescriptor(
                name=source.name,
                dim=source.system_dim,
                side=Side.ALICE,
            )

        adapted.append(
            ChainLink(
                link_id=f"Xi_{position}",
                segment=Segment.SOURCE,
                link_type=str(link.kind),
                source_descriptor=descriptor(link.source_descriptor),
                target_descriptor=descriptor(link.target_descriptor),
                status=LinkStatus(str(link.status)),
                channel=None,
            )
        )
    return tuple(adapted)


def chain_context(
    artifact: ProofReductionArtifact,
    physical_descriptor: SystemDescriptor,
    physical_povm: Mapping[str, Matrix] | None = None,
    target_name: str = "Q",
    *,
    sector_block_kind: BlockKind | str,
) -> ChainContext:
    """Return the context ``check_chain`` reads this module's conditions against.

    Built from the emitted reductions artefact and from the two data the caller
    owns, so that no second argument can disagree with either. The emitted
    alphabet and family are the artefact's target POVM in ITS declared order --
    the order ``def:compile`` takes rather than choosing one -- and ``gamma``
    is the identity on it.
    """
    order = artifact.wpfss_data.flag_basis
    settings = docking.probe_settings_of(order)
    labels = tuple(docking.outcome_label(v, settings) for v in order)
    descriptor = docking.target_descriptor(
        artifact, target_name, sector_block_kind=sector_block_kind
    )
    # THE SECTOR MAP IS READ OFF THE DOCKED DESCRIPTOR AND NOWHERE ELSE, which
    # is (C1)'s own rule: "the last link's target descriptor IS THE SECTOR
    # MAP". Building a second one here from the artefact would be a second
    # carrier of one object, and the two could then disagree.
    sector_map = descriptor.sector_map()
    if sector_map is None:
        raise MalformedInputError(
            "the docked target descriptor carries no sector map: its "
            "identifiers or its block kind are missing, and this module "
            "supplies neither for somebody else's map (the "
            "`decide_never_infer` convention; (C1))"
        )
    emitted: dict[str, BlockOperator] = {
        docking.outcome_label(v, settings): BlockOperator.of(
            sector_map, artifact.target_povm[v]
        )
        for v in order
    }
    return ChainContext(
        physical_descriptor=physical_descriptor,
        physical_alphabet=labels,
        physical_povm=dict(physical_povm or {}),
        target_descriptor=descriptor,
        emitted_alphabet=labels,
        emitted_povm=emitted,
        gamma=dict(zip(labels, labels, strict=True)),
    )


def chain_report(
    artifact: ProofReductionArtifact,
    physical_descriptor: SystemDescriptor,
    physical_povm: Mapping[str, Matrix] | None = None,
    target_name: str = "Q",
    *,
    sector_block_kind: BlockKind | str,
) -> ChainReport:
    """Run THIS MODULE'S OWN chain checker on a docked reductions chain.

    The check is this module's, not a re-implementation of it: the function
    builds the two records and calls
    :func:`certiqs_key.protocol_compiler.chain.check_chain`. What it is good
    for is exactly what a round-trip test needs -- that the artefact the
    reductions module emits is accepted by the type it is docked into, WHERE
    THIS MODULE'S CONDITIONS ARE DECIDABLE. (C4) is not, and says so.
    """
    return check_chain(
        docking.reduction_chain(
            artifact,
            physical_descriptor,
            target_name,
            sector_block_kind=sector_block_kind,
        ),
        chain_context(
            artifact,
            physical_descriptor,
            physical_povm,
            target_name,
            sector_block_kind=sector_block_kind,
        ),
    )

# ---------------------------------------------------------------------------
#  THE FACTOR EMISSION, DOCKED: one function, and it is the only one
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FactorisedSlots:
    """What ``reductions``' factor emission fills of a general-format declaration.

    The slots of ``def:declaration`` (DX1), (DX3) and (DX6) that
    ``reductions/thm:emitted-product``'s artefact list supplies, and NOTHING ELSE:
    Alice's side is the transmitter's (DX2), (DX4), the transcript is the public
    part's (DX5), and neither is here.

    ``sector_factorisation`` CARRIES THE EMISSION'S FACTOR LABELS. That is the one
    thing this record does rather than copies: the emitted
    :class:`~certiqs_key.foundations.blocks.FactorisedSectorMap` names each factor's
    party and the labels travel beside it on
    :attr:`~certiqs_key.reductions.factors.FactorEmission.factors`, so the docking
    puts them ON the factors -- which is where check V6 compares an entry's scope
    against them (:meth:`
    ~certiqs_key.protocol_compiler.declaration.CandidateDeclaration.measured_factor`).
    """

    sector_factorisation: FactorisedSectorMap
    bob_factors: FactorisedFamily
    sectors: SectorStructure
    bob_alphabet: tuple[Label, ...]
    constraint_entries: tuple[ConstraintEntry, ...]
    attack_set_license: AttackSetLicense | None


def factorised_slots(
    emission: FactorEmission,
    *,
    sector_block_kind: BlockKind | str,
    party_local_view: docking.PartyLocalView = docking.PartyLocalView.OPERATOR,
) -> FactorisedSlots:
    """Dock ``reductions``' factor emission into this module's declaration slots.

    THE ONE ADAPTATION POINT FOR THE FACTOR EMISSION, and it is named so that a
    reader looking for the seam finds one function rather than a pattern. The
    direction is the one :mod:`certiqs_key.protocol_compiler.docking_reductions`
    already takes: this module names ``reductions``, never the other way round
    (PRINCIPLES.md section 4).

    WHAT IT DOES, and each is a pass-through and not a construction:

    * the FACTOR LIST of (DX1), which is the emission's own map with the
      emission's own labels attached -- a factor label is not a party label, and a
      party may hold two factors, so the labels are what a scope is compared
      against and they must reach the declaration;
    * the PER-FACTOR FAMILY of (DX3) and the derived product map and alphabet,
      taken from the emission and formed here by nothing: the product is the rule
      ``eq:productfamily``;
    * the CONSTRAINT ENTRIES with THEIR SCOPE AND THEIR TAG. The operator, the
      relation and the real ``c_k`` are converted by ``reductions``' own accepted
      adapter, per artefact, on the artefact's UNTAGGED entries -- which is the
      only thing that adapter converts, it raising on a tagged one because the
      record it was written for "carries no scope slot and no ``party_local`` tag
      value". THIS DECLARATION HAS BOTH, so the scope and the tag
      are read off the emission's entry at the same position, where they are
      declared, and ``thm:emitted-product`` (iii) is what says the two entries are
      the same entry: "each entry scoped to its factor and carrying THE SAME
      OPERATOR, THE SAME RELATION AND THE SAME CONSTANT";
    * the licence, carried and never read.

    NOTHING OF ALICE'S SIDE IS HERE. (DX2) and (DX4) are the transmitter
    artefact's, and a function that filled them from a receiver-side emission
    would be inventing Alice's declaration.
    """
    labelled = FactorisedSectorMap(
        factors=tuple(
            SectorFactor(
                party=factor.party,
                sectors=factor.sectors,
                system=factor.system,
                label=label,
            )
            for factor, label in zip(
                emission.sector_map.factors, emission.factors, strict=True
            )
        )
    )
    family = FactorisedFamily.of(labelled, emission.family.factors)
    entries = docking.factor_constraint_entries(
        emission, party_local_view=party_local_view
    )
    return FactorisedSlots(
        sector_factorisation=labelled,
        bob_factors=family,
        sectors=family.flattened(),
        bob_alphabet=family.alphabet(),
        constraint_entries=entries,
        attack_set_license=docking.factor_attack_set_license(
            emission, party_local_view=party_local_view
        ),
    )
