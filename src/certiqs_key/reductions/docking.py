"""The emitted artifact, in the records the consumer already reads.

THIS IS THE ONLY FILE OF THIS PACKAGE THAT NAMES A CONSUMER'S TYPES
===================================================================
PRINCIPLES.md section 4 lets imports point downward only, and
:mod:`certiqs_key.reductions` is a MODULE: it may not import ``runs``, and nothing
above it may be on its import path. This file is the sanctioned exception and is
deliberately NOT imported from :mod:`certiqs_key.reductions` -- a caller that wants
it imports it by name, so the package surface stays clean whether or not the
consumer is installed. A unit test asserts both halves.

The conversion happens HERE, ONCE, IN ONE DIRECTION:

    ``ProofReductionArtifact``  ->  the frozen wire records of
    :mod:`certiqs_key.domain` (``chain``, ``constraints``) over the block form of
    :mod:`certiqs_key.foundations.blocks`.

Nothing outside this module is modified and nothing reads back the other way.
The artifact this module OWNS is the
:class:`~certiqs_key.reductions.artifact.ProofReductionArtifact` of the outputs
table of interface.yaml; what it does NOT own is the type the consuming
declaration carries a reduction chain in, and that type is a frozen shared type
of ``spec/architecture.md`` 2.9, which every module may read.

WHAT SURVIVES THE CONVERSION
============================
Everything the consumer's own conditions read. ``protocol-compiler``'s
Definition ``def:chaincond`` decides (C1) descriptor agreement, (C2) the
outcome correspondence, (C3) that ``{F_v}`` is a POVM with every element
sector-block-diagonal, and (C5); this module's target descriptor, target POVM,
sector decomposition and identity correspondence carry all four exactly, over
exact rationals on both sides. The source segment of every artefact emitted
today is EMPTY -- which is DATA the artefact carries and is no assumption of
this module -- so (S1), (S2), (S3) and (S4) are vacuous there.

WHAT DOES NOT CROSS, AND WHY IT IS NOT A GAP
============================================
Building the compiler's ``ChainContext`` and running its ``check_chain`` is NOT
done here: it is the COMPILER'S EVALUATION OF ITS OWN CHAIN CONDITIONS, which is
a consumer's behaviour and not a shared record
(:mod:`certiqs_key.protocol_compiler.docking_reductions`). What this file converts is
the ARTIFACT into the frozen wire records of :mod:`certiqs_key.domain`, which is a
conversion and not an evaluation.

AND THE NUMBERS THEMSELVES ARE NOT CONVERTED AT ALL. ONE exact pair lives in
:mod:`certiqs_key.foundations.exact`, which both sides import, so there is no
rebuilding of entries as another class, no rounding, no tolerance and no
numeric conversion here.

SIX THINGS THE CONSUMER'S TYPES CANNOT CARRY, NAMED RATHER THAN PAPERED OVER
============================================================================
Each is a limitation OF THIS DOCKING, not a defect of either contract, and none
is repaired by inventing a value.

1. **THE PHYSICAL SYSTEM'S DIMENSION.** ``SystemDescriptor.dim`` is typed
   ``int``; ``H(B) = H(C) (x) H(Bl)`` has ``H(C)`` a Fock space, which
   Definition ``def:system-setting`` permits exactly here -- ``H(B)`` "is
   separable and may be infinite-dimensional". There is no integer to put
   there and this module INVENTS NONE: :func:`reduction_chain` takes the
   physical descriptor as an ARGUMENT, supplied by the consuming declaration,
   which is where a finite description of the physical side belongs.
   ``interface.yaml`` records the same mismatch under
   ``link_record.wire_form_comparison_note``.

2. **THE CHANNEL AS DATA.** ``ChainLink.channel`` is a Kraus tuple or ``None``,
   and every link here supplies ``None``. That is not a gap in the conversion:
   The outputs table says the emitted ``squashing_channel`` is "A SYMBOLIC CONSTRUCTOR
   RECORD, NOT EVALUABLE DATA" because "THE SUPPLIER EMITS NO ABOVE-CUTOFF BLOCK
   AT ALL, so neither map can be materialised from the artifact -- and neither
   need be, SINCE THE CONSUMER NEVER APPLIES IT". The consumer's (C4) therefore
   returns ``not checked`` and names its Assumption A-LINK, which is the
   correct outcome; the function that REPORTS it is the compiler's own
   (see "What does not cross" above).

3. **THE CARRIED OPERATOR PAIR AND THE REACHABLE-SET STATEMENT.** Two of
   Definition ``def:link``'s ten slots have NO wire field at all. They are
   carried in this module's own artifact and are dropped by the conversion; a
   consumer needing them reads the artifact.

4. **THE TRUSTED-MODE RIGHT-HAND SIDE IS THE DECLARATION'S ``tau_A``, AND IS
   TAKEN AS AN ARGUMENT.** ``ConstraintEntry.rhs`` is a Hermitian operator on
   ``A`` in trusted-source mode and a real scalar in untrusted-source mode, and
   the consumer's own check refuses a scalar in the first case ("the marginal
   slot is filled, so Theta must be a Hermitian operator on A; a real scalar
   was declared"), which is a check of the protocol compiler and arrives with
   it. This module emits ``(O^_k, bowtie_k, c_k)`` and NEVER declares
   ``tau_A``: Theorem ``thm:licence`` (iv) says "the identification of the
   right-hand side is THE DECLARATION'S AND NOT THIS CONTRACT'S", and Remark
   ``rem:notlicensed`` (a) is blunter -- "Nothing here licenses declaring
   ``tau_A``."

   Those two facts do not conflict, and the resolution is the one the docking
   already uses for the physical descriptor: **the caller supplies the declared
   ``tau_A``**, and :func:`constraint_entries` forms ``c_k tau_A`` from it. The
   identification stays the declaration's -- the state comes from the
   declaration, not from here -- and what crosses the boundary is an entry the
   consumer's V6 accepts. WITH NO ``tau_A`` SUPPLIED IN TRUSTED MODE THE
   CONVERSION REFUSES, rather than emitting a scalar the consumer will reject:
   the docking's own rule is "once, in one direction", and an object no
   consuming declaration accepts is not a conversion.

   In untrusted-source mode ``Theta_k = c_k`` IS the consumer's type and no
   marginal is involved (Definition ``def:licensed``: "a comparison of real
   numbers").

5. **THE LICENCE RECORD.** ``AttackSetLicense`` carries a ``supplier`` and a
   ``statement`` -- two strings, "carried, never read, never verified and never
   synthesized". This module's licence NAMES FIVE THINGS (the theorem, the
   per-entry hypothesis, the discharging receiver fact with the artifact's
   version, the source mode, and the adjoint-form set), and the conversion
   flattens them into the statement string. Nothing is lost to a reader; what is
   lost is the structure.

6. **THE SECTOR LABELS.** ``SystemDescriptor.sectors`` is a tuple of
   ``(str, int)``; an instance's sector labels are PAIRS ``(group, name)``
   (``def:reduction-instance`` (I2)). They are joined as ``"group:name"``,
   which is injective on the emitted set because no declared group contains a
   colon -- :func:`target_descriptor` refuses the conversion rather than
   colliding two sectors if one ever does.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from fractions import Fraction

from certiqs_key.domain.chain import (
    ChainLink,
    LinkStatus,
    ReductionChain,
    Segment,
    Side,
    SystemDescriptor,
)
from certiqs_key.domain.constraints import AttackSetLicense, ConstraintEntry, RhsTag
from certiqs_key.domain.constraints import Relation as WireRelation
from certiqs_key.foundations.blocks import (
    BlockKind,
    BlockOperator,
    Label,
    SectorStructure,
)
from certiqs_key.foundations.exact import Matrix, direct_sum
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.companion import ReferenceCompanion
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.factors import FactorEmission, factor_sector_map
from certiqs_key.reductions.inputs import outcome_label, probe_settings_of
from certiqs_key.reductions.reasons import Relation
from certiqs_key.reductions.sectors import joined_sector_label

__all__ = [
    "PartyLocalView",
    "attack_set_license",
    "companion_constraint_entries",
    "constraint_entries",
    "docking_limitations",
    "factor_attack_set_license",
    "factor_constraint_entries",
    "outcome_label",
    "physical_family",
    "preserved_block",
    "probe_settings_of",
    "reduction_chain",
    "sector_projectors",
    "target_descriptor",
]


class PartyLocalView(StrEnum):
    """Which already-licensed reading crosses the consumer boundary."""

    OPERATOR = "operator"
    LICENSED_SCALAR = "licensed_scalar"


def _licensed_scalar_rows(emission: FactorEmission) -> dict[tuple[str, str], str]:
    """Return the licence's scalar consequence per tagged entry, or refuse."""
    licence = emission.licence
    if licence is None:
        raise MalformedInputError(
            "the licensed_scalar view requires the factor emission's licence"
        )
    rows = {
        (row.entry_label, row.factor): row.also_admissible_as_a_scalar
        for row in licence.party_local_entries
    }
    for entry in emission.entries:
        if entry.tag is not None:
            key = (entry.label, str(entry.scope))
            if key not in rows:
                raise MalformedInputError(
                    "the licensed_scalar view requires thm:licence (v)'s "
                    f"also_admissible_as_a_scalar row for {key!r}"
                )
    return rows


def factor_constraint_entries(
    emission: FactorEmission,
    *,
    party_local_view: PartyLocalView = PartyLocalView.OPERATOR,
) -> tuple[ConstraintEntry, ...]:
    """Convert scoped entries under one of their two producer-licensed readings."""
    if party_local_view is PartyLocalView.LICENSED_SCALAR:
        _licensed_scalar_rows(emission)
    artefact_by_label = dict(zip(emission.factors, emission.artefacts, strict=True))
    converted: list[ConstraintEntry] = []
    for entry in emission.entries:
        scope = entry.scope
        if scope is None:
            if len(emission.artefacts) != 1:
                raise MalformedInputError(
                    "an unscoped factor entry is admitted only in a one-factor emission"
                )
            artefact = emission.artefacts[0]
        else:
            artefact = artefact_by_label[scope]
        sectors = factor_sector_map(
            artefact,
            emission.family.sector_map.block_kind,
        )
        converted.append(
            ConstraintEntry(
                operator=BlockOperator.of(sectors, entry.operator),
                relation=_RELATIONS[entry.relation],
                rhs=Fraction(entry.constant),
                arriving_tag=(
                    None
                    if entry.tag is None
                    or party_local_view is PartyLocalView.LICENSED_SCALAR
                    else RhsTag(str(entry.tag))
                ),
                scope=scope,
            )
        )
    return tuple(converted)


def factor_attack_set_license(
    emission: FactorEmission,
    *,
    party_local_view: PartyLocalView = PartyLocalView.OPERATOR,
) -> AttackSetLicense | None:
    """Carry the joint factor licence as the consumer's pass-through record."""
    licence = emission.licence
    if licence is None:
        return None
    versions = ", ".join(
        artefact.mathematical_spec_version for artefact in emission.artefacts
    )
    scalar_provenance = ""
    if party_local_view is PartyLocalView.LICENSED_SCALAR:
        rows = _licensed_scalar_rows(emission)
        scalar_provenance = (
            " Scalar view selected under Theorem thm:licence (v), using the "
            "licence's also_admissible_as_a_scalar consequence per entry: "
            + "; ".join(
                f"{label}@{factor}: {statement}"
                for (label, factor), statement in rows.items()
            )
            + "."
        )
    return AttackSetLicense(
        supplier=f"reductions factors ({versions})",
        statement=(
            f"{licence.theorem}: {licence.admissible_set}. "
            "Hypothesis discharged per entry -- "
            + "; ".join(licence.hypothesis_per_entry)
            + ". Discharged per entry -- "
            + licence.discharge_statement()
            + ". Source mode: "
            f"{licence.source_mode}. Technique: {licence.technique}."
            + scalar_provenance
        ),
    )

#: The three relation symbols, in the two spellings. This module writes the
#: OPERATOR spelling of Definition ``def:attset``; the consumer's enum spells
#: the same three symbols as words. Definition ``def:attset``'s note is why the
#: map is a rename and not a reinterpretation: "The two spellings denote THE
#: SAME THREE RELATIONS at the two levels."
_RELATIONS: Mapping[Relation, WireRelation] = {
    Relation.LE: WireRelation.LE,
    Relation.EQ: WireRelation.EQ,
    Relation.GE: WireRelation.GE,
}


def _block_kind(value: BlockKind | str) -> BlockKind:
    """Return the declared block kind as the SHARED FORMAT'S enum member.

    THE VOCABULARY IS THE SHARED FORMAT'S AND NOT THIS MODULE'S.
    ``spec/architecture.md`` 2.9 puts the three kinds in
    :class:`certiqs_key.foundations.blocks.BlockKind`, a frozen shared type, and
    "the word 'block' never appears in this format without one of these three
    kinds attached, because a positional ``blockDims`` list is not a stable
    public contract". So this module neither enumerates the kinds nor invents
    one: it PASSES THROUGH the member the instance declared.

    A ``str`` is accepted only by ``BlockKind(value)``, which is a lookup in
    that enum and not a parse, and what crosses the boundary is THE MEMBER --
    ``protocol-compiler`` 0.3.0 types both ``SectorStructure.block_kind`` and
    ``SystemDescriptor.sector_block_kind`` as :class:`BlockKind`, and its (C1)
    compares members with ``is``, so handing it a bare string would be handing
    it a value its own comparison cannot match. A value outside the enum is a
    MALFORMED DECLARATION and is refused as one -- not defaulted, not coerced
    to a nearest member,
    and not passed on for the consumer to trip over at its own (C1). Section
    2.5's ``fail_closed`` convention forbids substituting a default for a datum
    the declaration does not supply, and a kind outside the shared vocabulary
    is exactly that.

    Raises:
        MalformedInputError: if ``value`` is not one of the three kinds.
    """
    try:
        return BlockKind(value)
    except ValueError as error:
        raise MalformedInputError(
            f"sector_block_kind = {value!r} is not one of the shared format's "
            "block kinds "
            + ", ".join(repr(str(kind.value)) for kind in BlockKind)
            + " (spec/architecture.md 2.9; certiqs_key.foundations.blocks."
            "BlockKind, a frozen shared type). The kind is the INSTANCE'S "
            "declaration, passed through here and never defaulted, so a value "
            "outside the vocabulary is a malformed declaration rather than "
            "something this module completes"
        ) from error


def _sector_map(
    artifact: ProofReductionArtifact, block_kind: BlockKind | str
) -> SectorStructure:
    """Return the instance's sector set as the shared ``SectorStructure``.

    ``block_kind`` IS THE CALLER'S AND HAS NO DEFAULT HERE. See
    :func:`target_descriptor` and :func:`_block_kind`.
    """
    return SectorStructure(
        labels=_joined_sector_labels(artifact),
        dims=tuple(artifact.target_descriptor.sectors.dimensions),
        block_kind=_block_kind(block_kind),
    )


def _joined_sector_labels(artifact: ProofReductionArtifact) -> tuple[str, ...]:
    """Return the sector identifiers joined as one label, refusing a collision."""
    labels = artifact.target_descriptor.sectors.labels
    joined = tuple(joined_sector_label(label) for label in labels)
    if len(set(joined)) != len(joined):
        raise MalformedInputError(
            "two sectors of the instance's sector set (def:reduction-instance "
            "(I2)) collide when their (group, name) pair is joined into one "
            "label; the docking refuses rather than merging two sectors of the "
            "emitted target"
        )
    return joined


def _block_operator(
    blocks: tuple[Matrix, ...],
    artifact: ProofReductionArtifact,
    block_kind: BlockKind | str,
) -> BlockOperator:
    """Return a ``Q``-operator, carried as its block list, in the consumer's type.

    THE CONSUMER TYPES EVERY ``Q``-OPERATOR AS A LIST OF SECTOR BLOCKS, and so
    does the artifact: ``def:reduction-instance`` (I2) assigns ``F_v`` ONE
    SECTOR BLOCK AT A TIME, so that ``F_v = bigoplus_s F_v^(s)`` is "what that
    list MEANS, not an object the artifact carries", and no full
    ``dim H(Q) x dim H(Q)`` array is emitted "here or anywhere in this
    artifact" (the outputs table, ``target_descriptor``).

    SO THIS FUNCTION CONVERTS NOTHING AND SPLITS NOTHING: it pairs the list the
    artifact already carries with the sector map, and
    :class:`~certiqs_key.foundations.blocks.BlockOperator` decides the one thing
    left to decide -- that there is one square block per sector, of the
    declared dimension. The artifact carries no dense direct sum to slice the
    blocks back out of (the ambient construction spec/architecture.md 2.9
    excludes); there is nothing to slice and nothing to verify, since "there is no
    off-sector entry to write, and therefore none to verify".

    IT SERVES EVERY ``Q``-OPERATOR THE ARTIFACT CARRIES, the sector projectors
    and a ``CList`` ENTRY'S ``hat O_k`` alike: an entry is a list of sector blocks in
    the artifact, so there is one reader for both and no place left where an
    off-sector entry could be truncated in silence.
    """
    return BlockOperator.of(_sector_map(artifact, block_kind), blocks)


def target_descriptor(
    artifact: ProofReductionArtifact,
    name: str = "Q",
    *,
    sector_block_kind: BlockKind | str,
) -> SystemDescriptor:
    """Return ``(Q, S, (d_s)_s)`` as the consumer's receiver-side descriptor.

    The sector labels are joined as ``"mode:flag"``; see limitation 6 in the
    module docstring. The join is refused rather than allowed to collide.

    ``sector_block_kind`` IS REQUIRED, KEYWORD-ONLY AND HAS NO DEFAULT, AND
    ITS VOCABULARY IS THE SHARED FORMAT'S. The consuming compiler makes the
    block kind the third machine key of a sector map and its comparison part
    of (C1): "a chain whose last link carries no block kind is REFUSED naming
    (C1)". This module emits one -- the ``target_descriptor`` output row is
    THE SECTOR MAP, "the block kind, the sector identifiers IN THE DECLARED
    ORDER, and the per-sector dimensions" -- and ``def:exactadm`` (c) clause
    (a) makes it the subject of a comparison a consumer refuses on.

    WHERE THE VALUE COMES FROM, which is NOT a contract matter:
    the three kinds are :class:`certiqs_key.foundations.blocks.BlockKind`
    (spec/architecture.md 2.9, a frozen shared type), THE
    INSTANCE DECLARES WHICH MEMBER, and this module PASSES IT THROUGH --
    required, never defaulted. That is why the contract fixes no string: the
    string is not this contract's to fix, and the datum is the declaring
    party's exactly as ``kappa`` is. A value outside the enum is a malformed
    declaration and is refused as one (:func:`_block_kind`); choosing one here
    would decide, in source, the value of a comparison the consuming module
    refuses on -- a declaring party's datum settled by the implementer, which a
    default would hide.
    """
    return SystemDescriptor(
        name=name,
        dim=artifact.target_descriptor.dimension,
        side=Side.RECEIVER,
        sectors=tuple(
            zip(
                _joined_sector_labels(artifact),
                artifact.target_descriptor.sectors.dimensions,
                strict=True,
            )
        ),
        sector_block_kind=_block_kind(sector_block_kind),
    )


def sector_projectors(
    artifact: ProofReductionArtifact, *, sector_block_kind: BlockKind | str
) -> tuple[BlockOperator, ...]:
    """Return the sector projectors ``{Pi_s}`` in the consumer's representation.

    EACH AS A :class:`~certiqs_key.foundations.blocks.BlockOperator`, the consumer's
    operator type (spec/architecture.md 2.9) and the form everything else here
    hands over: ``1_{d_s}`` on its own block and the zero block on every other.
    No ``dim H(Q) x dim H(Q)`` array is built to say so.
    ``sector_block_kind`` is the instance's declared kind,
    passed through as everywhere else in this module and defaulted nowhere.

    NOT PASSED TO THE CONSUMER, AND KEPT DELIBERATELY. ``ChainContext`` has no
    ``sector_projectors`` field: the projectors
    of a sector map are determined by the map -- "the projector of the ``i``-th
    sector is the diagonal 0/1 operator on the ``i``-th consecutive block" -- so
    passing them beside the map handed the consumer a second copy of a datum it
    can form, and a second copy is a second thing that can disagree.

    This module still BUILDS them, because the outputs table's
    ``transported_operators`` row is where the sector-projector certificate
    ``(Pi_s, >=, 0)`` of every instance travels, on every route
    (``def:reduction-instance`` (I3), third consequence;
    ``cor:entries`` (i)), so a consumer holding the sector map and the row can
    match the two. IT DOES NOT SAY THAT THE ROW IS THESE PROJECTORS AND
    NOTHING ELSE: the row carries them TOGETHER WITH the sums of sector
    projectors the instance transports besides -- the two cutoff projectors of
    a target split at a cutoff, a branch projector of a branching instance --
    which are not the projector of any one sector. The two coincide only where the
    sector set is as coarse as the split. The chain context does not carry them.
    """
    return tuple(
        _block_operator(blocks, artifact, sector_block_kind)
        for blocks in artifact.target_descriptor.sectors.projectors()
    )


def constraint_entries(
    artifact: ProofReductionArtifact,
    *,
    sector_block_kind: BlockKind | str,
    factor_scope: Label | None = None,
) -> tuple[ConstraintEntry, ...]:
    """Return ``CList`` as the consumer's entries. ``rhs`` IS THE SCALAR ``c_k``.

    THE ONE PLACE 1.0.0 SIMPLIFIES THIS ADAPTER RATHER THAN COMPLICATING IT,
    and the sentence that does it is the outputs table's: every entry "CARRIES A REAL
    SCALAR ``c_k`` AS ITS THIRD COMPONENT, **IN BOTH SOURCE MODES**", and
    "**THIS MODULE EMITS NO OPERATOR Theta_k IN EITHER MODE**". In
    trusted-source mode the entry declares the real ``c_k`` and "THE RIGHT-HAND
    SIDE ``Theta_k := c_k tau_A`` IS **CONSTRUCTED BY THE CONSUMER** from it and
    from THE CONSUMER'S OWN ``tau_A``"; in untrusted-source mode the scalar form
    is "THE ONLY ONE THAT EXISTS THERE".

    SO THERE IS NO ``alice_marginal`` PARAMETER, AND NO REFUSALS BUILT
    AROUND ONE. Multiplying ``c_k`` by a caller-supplied marginal produced a
    MATRIX right-hand side, which the consumer's own type gate now reads as the
    tag ``general`` -- "admissible input but **NEVER LICENSED**, so a list
    containing one carries NO KEY-LENGTH CLAIM (Def. ``def:attset``)". An
    adapter that did so would convert a licensed list into an unlicensed one at
    the boundary, in trusted mode, which is the failure this row's typing is
    meant to prevent. The scalar crosses and the consumer builds the rest.

    THE DECLARED FORM IS PASSED, AS THE DATUM IT IS. The outputs table: "**THE FORM
    IS EMITTED WITH THE ENTRY**, as the tag value ``homogeneous`` in
    trusted-source mode, because the consumer's part (i) security gate is a
    TYPE check on the declared tag and COMPARES NO NUMBERS (``meat-core`` 1.0.0
    ``constraint_list`` input row, Rem. ``rem:cgate``): the docking is by key
    and **NOTHING ABOUT THE FORM IS INFERRED AT EITHER END**." So this adapter
    carries ``entry.form`` into the consumer's ``arriving_tag`` slot rather
    than leaving the consumer to read the tag off the type of ``rhs``: reading
    it off the type is precisely the inference that sentence forbids, and it
    leaves the consumer's V6 cross-check -- "where an ARRIVING entry carries an
    explicit tag field, V6 compares that field with the type of the datum it
    names and A DISAGREEMENT IS A REFUSAL" (its ``def:validator``) -- with
    nothing to compare.

    ``None`` CROSSES AS ``None`` AND IS NOT INVENTED INTO A STRING. In
    untrusted-source mode the entry carries "THE SCALAR FORM, THE ONLY ONE THAT
    EXISTS THERE" and this contract fixes no tag string for it, so
    :class:`~certiqs_key.reductions.constraints.DeclaredForm` is ``None`` there and
    the consumer's own rule applies unchanged: "an entry carrying no tag field
    is NOT REFUSED: the tag is the type and is read off it."

    The list is EMPTY on the encoded route, which is the contract's own rule and
    not a property of the conversion.

    ``factor_scope`` is the caller's declared factor label.  When supplied it
    is copied onto every entry of this one-factor artefact; it is never inferred
    from the party or target name.  This is the producer-side spelling needed
    when the same link is carried in a general-format receiver segment.

    A ``party_local`` ENTRY IS REFUSED AT THIS WIRE. This adapter converts an
    entry's operator, relation and scalar constant and carries no tag, so
    converting a tagged entry would hand the consumer
    (:class:`certiqs_key.domain.constraints.ConstraintEntry`) an entry it would
    read as ``homogeneous`` -- the scalar reading, which is "the producer's to
    emit and not the consumer's to infer" (the ``constraint_list`` row's
    ``the_consumer_does_not_read_the_tag_yet``) and which is STRICTLY WEAKER
    than the party-local one in untrusted-source mode at ``d_A > 1``.
    Dropping it silently would therefore turn a licensed party-local list into a
    differently-read one at the boundary, which is the failure the ``alice_marginal``
    typing above guards against. NO REFUSAL STRING IS ADDED FOR IT: this adapter decides
    no fail-closed row of the interface and refuses by raising, exactly as it does for a
    sector-label collision, and the refusal strings are the interface's.
    """
    tagged = [
        entry.label for entry in artifact.constraint_list if entry.tag is not None
    ]
    if tagged:
        raise MalformedInputError(
            f"the emitted entries {tagged!r} are tagged party_local with a "
            "factor scope, and this adapter converts no tag; docking one would "
            "hand the consumer an entry it reads as the scalar form, which is "
            "the producer's to emit and not the consumer's to infer, so a "
            "tagged entry is refused at this wire rather than converted"
        )
    return tuple(
        ConstraintEntry(
            operator=_block_operator(entry.operator, artifact, sector_block_kind),
            relation=_RELATIONS[entry.relation],
            rhs=Fraction(entry.constant),
            arriving_tag=(None if entry.form is None else RhsTag(str(entry.form))),
            scope=factor_scope,
        )
        for entry in artifact.constraint_list
    )


def companion_constraint_entries(
    companion: ReferenceCompanion,
    artifact: ProofReductionArtifact,
    *,
    sector_block_kind: BlockKind | str,
    factor_scope: Label | None = None,
) -> tuple[ConstraintEntry, ...]:
    """Return the reference companion's entries as the consumer's entries.

    ``reductions/req:reference-companion`` (iii): the relaxed entries of
    ``lem:row-relaxation``, each a binary64 operator against the ARTEFACT'S
    sector map (the companion's shape is the artefact's,
    ``cor:reference-companion`` (i)) with its constant moved outward. Converted
    as :func:`constraint_entries` converts the artefact's own entries: the
    relation renamed, the scalar constant carried, the declared form carried as
    the arriving tag and nothing inferred, the caller's factor scope copied.
    Where ``delta_k`` is zero the exact entry crosses as it is.
    """
    return tuple(
        ConstraintEntry(
            operator=_block_operator(item.entry.operator, artifact, sector_block_kind),
            relation=_RELATIONS[item.entry.relation],
            rhs=Fraction(item.entry.constant),
            arriving_tag=(
                None if item.entry.form is None else RhsTag(str(item.entry.form))
            ),
            scope=factor_scope,
        )
        for item in companion.entries
    )


def attack_set_license(
    artifact: ProofReductionArtifact,
) -> AttackSetLicense | None:
    """Return the licence as the consumer's two-string pass-through record.

    ``None`` exactly when the constraint list is empty, which is the presence
    rule the outputs table states and which the artifact already enforces.

    The consumer treats this record as "carried, never read, never verified and
    never synthesized" (its Theorem ``thm:gates`` (iii)), and its gate "records
    that an attestation was supplied. It asserts nothing about attack-set
    inclusion." THAT IS THE RIGHT READING OF WHAT CROSSES THE BOUNDARY: what
    asserts the inclusion is Theorem ``thm:licence`` of THIS contract, whose
    hypothesis and discharging assumption are named inside the statement string
    so that a reader can follow the assertion back to its theorem.
    """
    licence = artifact.attack_set_license
    if licence is None:
        return None
    hypotheses = "; ".join(licence.hypothesis_per_entry)
    return AttackSetLicense(
        supplier=f"reductions {artifact.mathematical_spec_version}",
        statement=(
            f"{licence.theorem}: every physical attack channel composes into the "
            f"adjoint-form set {licence.admissible_set}. "
            f"Hypothesis discharged per entry -- {hypotheses}. "
            f"Discharged per entry -- {licence.discharge_statement()}. "
            f"Source mode: {licence.source_mode}. "
            f"Technique: {licence.technique}."
        ),
    )


def reduction_chain(
    artifact: ProofReductionArtifact,
    physical_descriptor: SystemDescriptor,
    target_name: str = "Q",
    *,
    sector_block_kind: BlockKind | str,
    source_segment: tuple[ChainLink, ...] = (),
    factor_scope: Label | None = None,
) -> ReductionChain:
    """Return the emitted chain as the consumer's ``ReductionChain``.

    ``physical_descriptor`` IS THE CALLER'S and is required rather than
    synthesized: limitation 1 of the module docstring. ``H(B)`` may be
    infinite-dimensional (Definition ``def:system-setting``) and
    ``SystemDescriptor.dim`` is an ``int``, so this module invents no
    dimension for the physical side.

    THE SOURCE SEGMENT IS THE ARTEFACT'S OWN AND IS EMPTY IN EVERY ARTEFACT
    EMITTED TODAY. That is DATA and not an assumption of this module: the
    emitted ``reduction_chain`` carries the segment. The consumer's record
    carries both segments always, so the empty one is passed on as the empty
    tuple and its conditions go vacuous; a non-empty one is refused here rather
    than dropped, this adapter converting no source link (see the refusal
    below).

    Every link supplies ``channel=None``; see limitation 2. The constraint
    entries and the licence sit on the LAST receiver link, which is where the
    consumer reads the target POVM, and Definition ``def:link`` binds them to
    that link's channel witness on this side.

    ``factor_scope`` is likewise caller-owned data.  It scopes the transported
    entries on the final link so the compiler can pass that datum through
    unchanged, as ``def:compile`` requires for the general format.  Omitting it
    preserves the one-factor wire byte for byte.
    """
    order = artifact.wpfss_data.flag_basis
    # The consumer's ``Label`` is a ``str`` and its alphabets are flat; this
    # module's ``V = Y x T`` is a set of pairs, joined by the one function the
    # artifact's own machine record uses, so a reader moving between the two
    # sees one spelling.
    settings = probe_settings_of(order)
    if artifact.reduction_chain.source_segment:
        raise MalformedInputError(
            "the emitted chain carries a NON-EMPTY source segment "
            f"{list(artifact.reduction_chain.source_segment)}, and this adapter "
            "converts no source link: the consumer's wire record has no slot "
            "for a source link's declared descriptor family, its obligation "
            "record or its witness (transmitter/def:source-link), so docking "
            "one would drop what def:chain's admission rule is decided on. It "
            "is refused rather than emptied"
        )
    descriptor = target_descriptor(
        artifact, target_name, sector_block_kind=sector_block_kind
    )
    # Every link lands on the emitted target system, so every descriptor
    # after the first link is that finite target system with its sector map.
    intermediate = descriptor
    links: list[ChainLink] = []
    total = len(artifact.reduction_chain.links)
    for index, link in enumerate(artifact.reduction_chain.links):
        last = index == total - 1
        source = physical_descriptor if index == 0 else intermediate
        links.append(
            ChainLink(
                link_id=link.link_id,
                segment=Segment.RECEIVER,
                link_type=link.kind.value,
                source_descriptor=source,
                target_descriptor=descriptor if last else intermediate,
                status=LinkStatus(link.status.value),
                channel=None,
                transported_constraints=(
                    constraint_entries(
                        artifact,
                        sector_block_kind=sector_block_kind,
                        factor_scope=factor_scope,
                    )
                    if last
                    else ()
                ),
                license_slot=(attack_set_license(artifact) if last else None),
                target_alphabet=(
                    tuple(outcome_label(v, settings) for v in order)
                    if last
                    else None
                ),
                target_povm=(
                    {
                        outcome_label(v, settings): _block_operator(
                            tuple(artifact.target_povm[v]),
                            artifact,
                            sector_block_kind,
                        )
                        for v in order
                    }
                    if last
                    else None
                ),
            )
        )
    return ReductionChain(
        source_segment=source_segment,
        receiver_segment=tuple(links),
        outcome_correspondence={
            outcome_label(v, settings): outcome_label(
                artifact.outcome_correspondence[v], settings
            )
            for v in order
        },
    )


def preserved_block(element: tuple[Matrix, ...], preserved: int) -> Matrix:
    """Return one target element's block on ``H(C_{<=N})``, re-assembled.

    The emitted element is the list ``(F_v^(s))_s`` of its sector blocks, and
    ``F_v = (+)_s F_v^(s)`` is what that list MEANS (the ``target_povm``
    output row). The preserved summand ``H(C_{<=N})`` is the leading sectors
    of the emitted map, one per photon number, and the flag sectors follow;
    so the block is READ off the list and re-assembled, never cut out of a
    whole-space array. The dimension is compared rather than assumed, and a
    disagreement refuses.

    It lives beside :func:`physical_family`
    so that the run tier can compare a presented physical family with the
    read-off without importing an instance.
    """
    blocks: list[Matrix] = []
    total = 0
    for block in element:
        if total >= preserved:
            break
        blocks.append(block)
        total += len(block)
    if total != preserved:
        raise MalformedInputError(
            f"the target's leading sector blocks carry {total} dimensions and "
            f"the declared preserved dimension is {preserved}; the emitted "
            "sector map and the channel grading disagree about which summands "
            "are H(C_{<=N})"
        )
    return direct_sum(blocks)


def physical_family(
    artifact: ProofReductionArtifact, dimension: int
) -> dict[Label, Matrix]:
    """Return ``{M_v}`` on ``H(C_{<=N})``, read off the target's preserved block.

    ``dimension`` is the preserved block's dimension ``d_{<=N}``. The family a
    station's docked receiver declares: a READING of the emitted target, never
    a second construction, keyed by the consumer's outcome labels in the
    target's own order. For the flat instance it IS the compression
    ``iota^dag M' iota`` of the declared model onto ``H(C_{<=N})``: the
    declared model is block diagonal at the cutoff with the declared datum
    below it, and the target's data sectors carry that datum
    (``wpfss/prop:flat-instance`` (I1)-(I2); ``protocol-compiler/
    rem:obligations-discharged``), which is what the run tier attests in
    ``chain_provenance`` (``protocol-compiler/req:link-row-provenance`` (ii)).
    For a branching artefact it reads the flat branch's preserved block,
    and no claim shows that reading to be a compression of the branching model.
    """
    settings = probe_settings_of(artifact.wpfss_data.flag_basis)
    return {
        outcome_label(outcome, settings): preserved_block(element, dimension)
        for outcome, element in artifact.target_povm.items()
    }


def docking_limitations(artifact: ProofReductionArtifact) -> tuple[str, ...]:
    """Return, for this artifact, what the consumer's types cannot carry.

    A machine-readable form of the module docstring's items, so that a caller
    logging a docked chain can log what the conversion dropped rather than
    discovering it later. THREE are conditional on the artifact -- the
    trusted-mode right-hand side, the constraint entries, and
    the ``operator_tolerance_record`` -- and the rest hold of every one.
    """
    items = [
        "physical dimension: H(B) may be infinite (def:system-setting); "
        "SystemDescriptor.dim "
        "is an int, so the physical descriptor is the caller's and is not "
        "synthesized here",
        "channel data: every link supplies channel=None because the supplier "
        "emits no above-cutoff block (the outputs table), so the consumer's (C4) is "
        "not checked and names its A-LINK",
        "def:link slots dropped: the carried operator pair and the "
        "reachable-set statement have no wire field at all",
        "licence structure: five named things are flattened into one statement "
        "string; nothing is lost to a reader, the structure is",
    ]
    items.append(
        "the sector BLOCK KIND is the DECLARING PARTY'S and is not synthesized "
        "here: reductions requires the emitted target_descriptor to "
        "carry one (sec:outputs; def:exactadm (c) clause (a)) and "
        "protocol-compiler refuses a chain whose last link carries none, "
        "naming (C1). The vocabulary is the shared format's "
        "certiqs_key.foundations.blocks.BlockKind (spec/architecture.md 2.9), "
        "the instance declares the member, and this adapter passes it through "
        "required and never defaulted -- so a caller docking a chain must "
        "supply the kind its instance declared"
    )
    if artifact.constraint_list:
        items.append(
            "constraint entries are attached to the LAST receiver link, which "
            "is where the consumer reads the target POVM; def:link binds them "
            "to that link's channel witness on this side"
        )
    # THE ADAPTER passes the emitted NUMBERS through unchanged -- there is no
    # shift to re-derive, every constant being exact under exact admissibility
    # (cor:entries) -- but the consumer's wire types carry NO FIELD for
    # `emission_record`, so the record does not travel with them. What a
    # consumer does with a family a producer snapped is THE CONSUMER'S: "NO
    # BOUND RELATING A KEY LENGTH COMPUTED FROM THE EMITTED DECLARATION TO ONE
    # COMPUTED FROM ANY OTHER FAMILY IS ASSERTED HERE OR ANYWHERE IN THIS
    # CONTRACT" (thm:emit (v)), so nothing is decided about the consumer on
    # this side; the limitation is REPORTED instead.
    record = artifact.emission_record
    items.append(
        f"emission_record: the artifact declares kappa = "
        f"{record.lattice_exponent}, records the six (D-EMIT) outcomes and, "
        f"per preserved block, what def:emitnorm did -- "
        + (
            "every block was ALREADY on the declared lattice, so M' = M and "
            "every Delta_s = 0"
            if not record.displaced
            else "the normalizer ACTED, and the per-sector displacement "
            "Delta_s and every kept or moved class, with the step that moved "
            "it, are in the record"
        )
        + ". The consumer's types have NO FIELD for any of it, so a caller "
        "docking this chain must log the record separately; the emitted "
        "numbers pass through unchanged"
    )
    return tuple(items)
