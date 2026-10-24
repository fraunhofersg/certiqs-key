"""PC1 -- ``def:compile``: the compilation map, and the pipeline.

``def:compile``, Eq. ``eq:rdef``, ``thm:typing``, and the sequencing the rest of
the module implies.

THE MAP, SLOT BY SLOT
=====================
Definition ``def:compile`` fills Eq. ``eq:declaration``:

    ``A``, ``d_A``, ``{M_x}``   from the TRANSMITTER ARTEFACT, which
                                ``S_src`` now reads (``def:spec`` (a));
    ``tau_A``                   from THE SAME ARTEFACT'S MARGINAL SLOT,
                                passed through unchanged, the ``d_A = 1``
                                fill included and recorded as filled
                                (``transmitter/req:marginal-fill``). THIS
                                MODULE FILLS NO SLOT and serves no
                                source-mode request;
    ``(Q, S, (d_s))``, ``{F_v}``  from THE LAST LINK of ``R_rec``, and
                                WEIGHTED after the chain by ``def:weighted``'s
                                setting-dependent form where a Bob-side
                                choice is declared (route C);
    ``P``, ``a_A``, ``a_B``, ``phi``, ``h``   VERBATIM from ``S_pub``;
    ``CList``                   the CONCATENATION of ``S_con``'s entries with
                                those transported by the links of ``R_src`` and
                                THEN those of ``R_rec``, each segment in its own
                                order;
    ``r``                       BUILT by Eq. ``eq:rdef``, never accepted;
    ``idx``                     the nine bijections.

THE ORDER OF THE STAGES, AND WHY IT IS THAT ORDER
=================================================
    conditional families -> physical family -> Band-A receiver -> chain
      -> slot filling (with the source identity at d_A = 1)
      -> validate (G1) -> gates (G2), (G3) -> emit | refuse

**The conditional families first.** ``def:weighted`` decides the exact admissibility of
each declared ``{N_{u|t}}_u`` "before it forms any product and therefore before the
interface conditions on the chain are decided", and the ``fail_closed`` table puts it at
row 1: where the presentation is the receiver's, the products ARE what the
chain row reads -- (C4)'s pullback sums them and in Band A (C3) decides them --
so a condition of the chain is never decided on a product whose conditional
families were not decided first.

**The physical receiver family next** (``req:physical-family-decision``). Clause (iv) of
``def:well-formed-spec`` reads the family as presented like every other
declared family, as one block on its physical receiver space, so the compiler
decides it on every route -- after the conditional families and the
representability of the products formed from them, and before any condition
of the chain, because (C4) reads it inside the pullback identity. A failure is
``physical_family_not_admissible``, naming the measured factor, the predicate
and the index of the first failure. Nothing of its exact admissibility is left
to the user.

**The ideal receiver on the Band-A route next** (``req:band-a-ideal-receiver``):
a specification the record puts on the route is refused with
``band_a_outside_ideal_receiver`` unless it has one measured factor, a
two-dimensional receiver system (and, with a trusted source, transmitted
system) and a projective family as presented -- the part of A-IDEAL that is
declared data. It reads the family the previous stage decided admissible.
Then the route's one link (``req:band-a-identity-link``): it must supply its
channel as data and keep the outcomes as they are (``gamma`` the identity on
``V = V^ph``), or the specification is refused with
``band_a_link_not_identity``; the chain stage's (C4) then decides that the
link delivers the declared family, ``F_v = F^ph_v``.

**The source identity at ``d_A = 1``** (``req:da1-source-identity``) is decided
once Alice's family has been resolved, before anything is emitted: in
trusted-source mode at ``d_A = 1``, ``sigma_x = m_x sum_y sigma_y`` for every
letter, exactly, or ``da1_source_identity_failed``. These decisions are
:mod:`certiqs_key.protocol_compiler.declared_premises`.

**The chain next**, because the emitted ``(Q, S, (d_s))`` and ``{F_v}`` ARE the
last link's target (Definition ``def:spec`` (c)): a chain failing an interface
condition has no target descriptor to build a declaration from, and Theorem
``thm:chain-consumption`` (i) says such a chain "is refused with that condition named".

**Validation before the gates**, because ``def:eligible`` (G1) is
literally "V1--V8 all pass" and row 1 of the gate outcome table makes a (G1)
failure dominate every other axis: "There is no declaration to emit ... Nothing
downstream may consume it, at any tier."

**The gates last**, because Definition ``def:eligible`` opens "AN EMITTED
DECLARATION is key-length-eligible when ...", so (G2) and (G3) are conditions on
an object the earlier stages must already have produced.

A REFUSAL EMITS NO DECLARATION
==============================
The ``refusal`` output row: it is "present exactly when the compiler
refuses; carries a machine-readable reason naming the failed check. A REFUSAL EMITS *NO*
DECLARATION." :class:`CompilationResult` enforces that in its constructor: a
result carries a refusal or a declaration and never both, and never neither. No
partial or best-effort declaration accompanies a refusal, at any tier.

THE FEASIBILITY WITNESS IS VERIFIED AND RECORDED, AND IS NOT A TWENTY-SECOND KEY
================================================================================
``interface.yaml`` records two readings of Theorem ``thm:feasibility`` (ii) and decides
neither: (A) the compiler VERIFIES a supplied witness, (B) it also EMITS one.
THE READING TAKEN HERE IS (A) PLUS A RECORD. The decision is forced by the one
thing that is not open: the outputs table has TWENTY-THREE keys, none of them
a witness, and the interface's machine keys are binding on this
implementation. Inventing a twenty-fourth output key would be a scope
change, so the witness that V7 accepted is carried on the RESULT --
:attr:`CompilationResult.
verified_witness`, a diagnostic beside the artifact -- and appears in no
machine record. What is not in doubt on either reading is satisfied either way:
the default candidate of Eq. ``eq:witness-empty`` is tried first, a supplied
witness is verified condition by condition, and where neither passes the reason
is ``no_feasibility_witness``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from certiqs_key.domain.bindings import (
    Binding,
    Bindings,
    LedgerBindings,
    exact,
    ledger_bindings_record,
)
from certiqs_key.domain.constraints import ConstraintEntry
from certiqs_key.domain.families import (
    AliceForm,
    FactorFamily,
    FactorisedFamily,
)
from certiqs_key.foundations.blocks import (
    BlockOperator,
    FactorisedSectorMap,
    JointBlockOperator,
    Label,
    SectorFactor,
    SectorStructure,
    SystemTag,
    default_factor_label,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Matrix,
    equal,
    identity,
    is_hermitian,
    is_positive_semidefinite,
    sum_in_declared_order,
)
from certiqs_key.protocol_compiler.chain import (
    ChainContext,
    ChainLink,
    ChainReport,
    FactorChainReport,
    LinkStatus,
    ReductionChain,
    SystemDescriptor,
    check_chain,
    check_factor_chains,
    check_licensed_only,
    check_source_segment,
)
from certiqs_key.protocol_compiler.declaration import (
    DECLARATION_SLOT_KEYS,
    INDEXED_ALPHABETS,
    MATHEMATICAL_SPEC_VERSION,
    CandidateDeclaration,
    LabelIndexMap,
    build_label_index_map,
)
from certiqs_key.protocol_compiler.declared_premises import (
    band_a_route,
    decide_band_a_ideal_receiver,
    decide_band_a_identity_link,
    decide_da1_source_identity,
)
from certiqs_key.protocol_compiler.docking_reductions import source_chain_segment
from certiqs_key.protocol_compiler.gates import (
    CertificateState,
    EmissionOutcome,
    GateInputs,
    GateReport,
    GateResolution,
    licensed_for_the_emitted_mode,
    resolve_gates,
)
from certiqs_key.protocol_compiler.provenance import ChainProvenance
from certiqs_key.protocol_compiler.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    AssumptionId,
    Refusal,
    RefusalReason,
    refusal_from_transmitter,
)
from certiqs_key.protocol_compiler.spec import (
    PERP,
    DirectPovm,
    KeyValue,
    Party,
    PovmPresentation,
    ProtocolSpecification,
    PublicChoices,
    PublicPart,
    ReceiverPart,
    Sifting,
    raw_key_map,
)
from certiqs_key.protocol_compiler.transcript import (
    SUMMATION_PREDICATE,
    PredicateOutcome,
    PredicateSource,
    PredicateTranscript,
    scoped_to_factor,
)
from certiqs_key.protocol_compiler.validation import ValidationResult, validate
from certiqs_key.protocol_compiler.weights import (
    ConditionalFamilyDecision,
    SettingWeightedFamily,
    decide_conditional_families,
    resolve_povm,
    setting_joint_label,
    setting_weighted_family,
)
from certiqs_key.transmitter.artifact import (
    alice_measurement_shape,
    source_segment_from_admitting_module,
)
from certiqs_key.transmitter.certificate import (
    CertificateVerification,
    RetentionAttestation,
    SourceReplacementCertificate,
    SourceReplacementLicense,
    verify_certificate,
)
from certiqs_key.transmitter.presentation import (
    EnsemblePresentation,
    EnsemblePresentationVerification,
    transpose,
    verify_ensemble_presentation,
)
from certiqs_key.transmitter.reasons import CertificateForm, SourceMode

__all__ = [
    "CompilationResult",
    "FactorWeighting",
    "PresentationVerification",
    "assemble_factor_list",
    "chain_record",
    "check_certificate_pair_typing",
    "compile_specification",
    "decide_every_conditional_family",
    "decide_physical_family",
    "emitted_constraint_list",
    "link_row_discharged",
    "public_choice_declared",
    "refuse_dense_alice_povm_at_several_sectors",
    "verify_presentation",
]


def emitted_constraint_list(
    specification: ProtocolSpecification, chain: ReductionChain
) -> tuple[ConstraintEntry, ...]:
    """Return ``CList``: the concatenation Definition ``def:compile`` prescribes.

    ``S_con``'s entries, then those transported by the links of ``R_src``, then
    those of ``R_rec``, EACH SEGMENT IN ITS OWN ORDER. Every entry is emitted
    "with its relation symbol and right-hand side unchanged" -- the transport is
    LITERAL and no transformation is applied. An entry whose typing does not
    match the emitted source mode is "a property of the supplier's data, not of
    the compilation map" and is what check V6 rejects (proof of Theorem
    ``thm:typing``, D(vi)); NOTHING HERE COERCES OR DROPS ONE.
    """
    entries = list(specification.constraints.entries)
    for link in chain.source_segment:
        entries.extend(link.transported_constraints)
    for link in chain.receiver_segment:
        entries.extend(link.transported_constraints)
    return tuple(entries)


def _source_segment_admission_refusal(
    specification: ProtocolSpecification, chain: ReductionChain
) -> Refusal | None:
    """Apply C4's mode and (A1)--(A3) decisions before either assembly path.

    THE TWO SEGMENTS ARE COMPARED WHENEVER EITHER IS NON-EMPTY. The chain
    record's source segment and the transmitter artefact's typed segment
    (:attr:`~certiqs_key.protocol_compiler.spec.SourcePart.source_links`,
    which ``SourcePart`` already makes the artefact's own) are one segment
    presented twice: ``def:spec`` (a) writes the certificate against the
    virtual ensemble "the source segment starts from", and (A3) of
    ``transmitter/def:source-segment`` accepts a segment only inside the
    artefact of the module that admits it. An artefact segment the chain does
    not carry is refused here with ``source_segment_not_from_admitting_module``
    like a chain segment the artefact does not carry; returning early on an
    empty chain segment would let a specification with ``L_s >= 1`` on its
    artefact be read as ``L_s = 0`` (on the Band-A route among others) with
    no (A1)--(A3) decision taken on its links.
    """
    if not chain.source_segment and not specification.source.source_links:
        return None
    untrusted = specification.source.source_mode is SourceMode.UNTRUSTED
    if chain.source_segment and untrusted:
        return Refusal(
            reason=RefusalReason.SOURCE_SEGMENT_IN_UNTRUSTED_MODE,
            detail=(
                "the presented chain carries a source segment of length "
                f"{len(chain.source_segment)} while the declaration's marginal "
                "slot holds nomarg (untrusted-source mode); def:chaincond "
                "licenses source maps in trusted-source mode only"
            ),
        )
    if source_chain_segment(specification.source.source_links) != chain.source_segment:
        return Refusal(
            reason=RefusalReason.SOURCE_SEGMENT_NOT_FROM_ADMITTING_MODULE,
            detail=(
                "the chain's source segment and the admitting artifact's typed "
                "segment must agree entry for entry; the chain carries "
                f"{len(chain.source_segment)} link(s) and the artifact carries "
                f"{len(specification.source.source_links)} typed link(s)"
            ),
        )
    return check_source_segment(
        specification.source.source_links,
        assumption_ledger=specification.source.artifact.assumption_ledger,
        from_admitting_module=source_segment_from_admitting_module(
            specification.source.artifact
        ),
        registry=specification.source.artifact.soundness_registry,
    )


def chain_record(chain: ReductionChain) -> dict[str, object]:
    """Return the ``reduction_chain_record`` output key.

    OPEN CHOICE ``OC-reduction-chain-record``, DECIDED HERE. The
    interface records that the claims fix the record's CONTENT
    exhaustively -- two segments in that order; per link a type tag, source and target
    descriptors, a status tag,
    its channel as data where the link type has one, its transported constraint
    entries and its licence slot; and the rule that every one of those slots is
    emitted whether or not it is empty -- and that it fixes NO WIRE FORM.

    THE FORM CHOSEN is a mapping with the two segments under their own names,
    each an ordered list of link records carrying every slot the contract names.
    Requirement ``req:chain-record-slots`` is the whole reason for the shape: "a
    record shape that omits an empty slot cannot later distinguish 'no entries'
    from 'entries not carried', and a record with one undifferentiated list of
    links cannot later be asked which of them were source maps". So
    ``source_segment`` is present and equal to ``[]`` in Band A rather than
    absent, and every link carries ``transported_constraints`` and
    ``license_slot_*`` whatever their contents.

    THE CHANNEL MATRICES ARE NOT SERIALIZED, and that is deliberate rather
    than an omission. The inputs table names the channel as data on the
    INPUT row; the output row names "its statuses, transported
    constraint entries and licence slots" and does not name the channel.
    What the record carries is therefore ``channel_supplied`` -- the fact (C4) and (S3)
    turn on, and the
    fact a reader needs to know whether the identity was CHECKED or carried as
    Assumption ``ass:link`` -- and not a Kraus set the output table does not
    ask for. Serializing one would be adding content to a record the contract
    enumerates.

    THE TRANSPORTED ENTRIES ARE COUNTED HERE AND CARRIED UNDER
    ``constraint_list``, WHICH IS THE ATTRIBUTION AND NOT A LOSS. The output row says
    the chain record carries "its statuses, transported constraint entries and licence
    slots", and what this link record carries is the COUNT. The entries themselves are
    on the wire in full, with their relation symbols and right-hand sides
    unchanged, under the ``constraint_list`` output key; and ``def:compile``
    fixes the concatenation order -- ``S_con``'s own entries, then those
    transported by the links of ``R_src``, then those of ``R_rec``, each
    segment in its own order -- so the per-link counts plus that order say
    which entry came from which link, exactly. Emitting the entries a second
    time would put one datum on the wire twice and make a consumer decide
    which copy is the record.

    This record travels in the module's own artifact; the run tier's wire
    record (an OPTIONAL ``reduction_chain`` on the manifest payload) is filled
    FROM it. The compiler never writes a bundle.
    """

    def _link(link: ChainLink) -> dict[str, object]:
        return {
            "link_id": link.link_id,
            "segment": str(link.segment),
            "link_type": link.link_type,
            "source_descriptor": _descriptor(link.source_descriptor),
            "target_descriptor": _descriptor(link.target_descriptor),
            "status": str(link.status),
            "channel_supplied": link.channel_supplied,
            "transported_constraints": len(link.transported_constraints),
            "license_slot_present": link.license_slot_present,
            "license_slot_empty": link.license_slot_empty,
        }

    return {
        "source_segment": [_link(link) for link in chain.source_segment],
        "receiver_segment": [_link(link) for link in chain.receiver_segment],
        "outcome_correspondence": [
            [physical, emitted]
            for physical, emitted in chain.outcome_correspondence.items()
        ],
    }


def _factor_chain_record(
    label: Label,
    chain: ReductionChain,
    part: ReceiverPart,
    weighting: SettingWeightedFamily | None,
) -> dict[str, object]:
    """Record one local chain through its declared public-choice weighting."""
    local = chain_record(chain)
    correspondence = local["outcome_correspondence"]
    if weighting is not None:
        expanded: list[list[str]] = []
        for physical, emitted in chain.outcome_correspondence.items():
            for weighted in weighting.members_of_outcome(emitted):
                choice = weighting.pairs[weighted][1]
                expanded.append(
                    [setting_joint_label(physical, choice), str(weighted)]
                )
        correspondence = expanded
    return {
        "factor_label": str(label),
        "party": str(part.party),
        "receiver_segment": local["receiver_segment"],
        "outcome_correspondence": correspondence,
    }


def _descriptor(descriptor: SystemDescriptor) -> dict[str, object]:
    """Return one system descriptor as a machine record."""
    return {
        "name": descriptor.name,
        "dim": descriptor.dim,
        "side": str(descriptor.side),
        "sectors": (
            None
            if descriptor.sectors is None
            else [[label, dim] for label, dim in descriptor.sectors]
        ),
        # THE THIRD COMPONENT OF THE MAP, beside the two the record
        # carries. `sectors` keeps its shape, and a reader that finds this key absent
        # refuses rather than inferring a kind (the ``decide_never_infer`` convention).
        "sector_block_kind": (
            None
            if descriptor.sector_block_kind is None
            else descriptor.sector_block_kind.value
        ),
    }


@dataclass(frozen=True)
class CompilationResult:
    """What one compilation produced: a declaration, or a refusal, never both.

    The twenty-three output keys are assembled by
    :meth:`as_machine_record`. The remaining fields are DIAGNOSTICS -- the
    validation result, the chain report, the certificate verification and the
    verified feasibility witness -- carried so that a caller can see why an
    outcome happened without re-running anything, and none of them is an output
    key.
    """

    declaration: CandidateDeclaration | None
    refusal: Refusal | None
    key_length_eligible: bool | None
    gate_report: GateReport | None
    reduction_chain_record: dict[str, object]
    validation: ValidationResult | None
    #: ``None`` on the one refusal that is taken BEFORE the chain stage runs:
    #: Definition ``def:weighted``'s emission decision on the receiver's
    #: choice-weighted family, which :func:`_chain_context` must construct in
    #: order to give check (C4) anything to compare. Absent rather than
    #: fabricated: a report whose nine conditions all read ``not checked``
    #: would name Assumption ``ass:link`` beside them and so would claim the
    #: obligation had been TRANSFERRED, which is what
    #: ``reasons.ConditionOutcome`` warns must never be
    #: confused with anything else. Nothing was checked and nothing was
    #: transferred; the compilation stopped earlier than that.
    chain: ChainReport | None
    gates: GateResolution | None
    certificate: CertificateVerification | None
    source_replacement_license: SourceReplacementLicense | None
    #: The witness V7 accepted. A DIAGNOSTIC AND NOT AN OUTPUT KEY -- see the
    #: module docstring on why there is no twenty-second key.
    verified_witness: JointBlockOperator | None
    #: The setting-dependent families this module CONSTRUCTED, one per
    #: measured factor at which a ``choice_weighting`` was declared, in the
    #: order of the factors, and ``()`` where none was. Unlike the four
    #: fields above it IS an output key -- ``choice_weighting_record``,
    #: emitted by :meth:`as_machine_record` -- because ``rem:relabel`` says
    #: the weighting is recorded beside the chain record as this module's
    #: own construction, and a consumer must be able to see what was
    #: applied and to what. ONE PER WEIGHTED FACTOR
    #: (``req:choice-weighting-record``: one entry per
    #: measured factor at which a weighting is applied, naming that factor).
    choice_weightings: tuple[FactorWeighting, ...] = ()
    #: THE PER-FACTOR CHAIN VERDICTS of ``def:chaincond``'s general reading,
    #: where the specification presented more than the accepted format's one
    #: receiver segment. A DIAGNOSTIC AND NOT AN OUTPUT KEY, like
    #: :attr:`chain`, which holds THE FIRST FACTOR'S report so that a consumer
    #: typed against the accepted format reads the report it always read: at one
    #: measured factor the two are the same record.
    factor_chain: FactorChainReport | None = None
    #: The ``assumption_ledger`` output key: the machine keys of the
    #: assumptions THE EMITTED DECLARATION rests on, assembled by
    #: :func:`_assumption_ledger` under the presence rule of each row
    #: of interface.yaml's ledger. EMPTY ON A REFUSAL, for the reason
    #: the seventeen declaration slots are ``None`` there: there is no
    #: declaration to rest on anything, and a ledger emitted beside a
    #: refusal would name assumptions no artefact carries.
    assumption_ledger: tuple[str, ...] = ()
    #: The ``assumption_bindings`` output key: beside each row of
    #: :attr:`assumption_ledger`, in its order, the declared values the row's
    #: assumption's clauses are about (:func:`_assumption_bindings`). EMPTY ON A
    #: REFUSAL, as the ledger is.
    assumption_bindings: LedgerBindings = ()
    #: WHETHER THE A-LINK ROW WAS OMITTED UNDER ``req:link-row-provenance``
    #: (ii): the run passed ``chain_provenance`` and every part of (ii) that is
    #: data held of the presented chain (:func:`link_row_discharged`). A
    #: DIAGNOSTIC AND NOT AN OUTPUT KEY; the run tier reads it to name that
    #: requirement among the compiler's roots, so that what the omission rests
    #: on is in the run's claim closure. ``False`` on Band A, where the row is
    #: omitted under (i), and on a refusal.
    link_row_omitted_on_provenance: bool = False

    def __post_init__(self) -> None:
        """Enforce the outputs table: a refusal emits NO declaration, and conversely."""
        if (self.declaration is None) == (self.refusal is None):
            raise MalformedInputError(
                "a compilation emits a declaration OR a refusal and never both "
                "and never neither (the ``refusal`` output row)"
            )
        if self.refusal is not None and self.key_length_eligible is not None:
            raise MalformedInputError(
                "a refusal carries no key_length_eligible flag: there is no "
                "declaration for the gates of Definition def:eligible to be about"
            )

    @property
    def refuses(self) -> bool:
        """Whether the compilation refused."""
        return self.refusal is not None

    def as_machine_record(self) -> dict[str, object]:
        """Return all TWENTY-SEVEN keys of the outputs table, in its order.

        Every key is present at every outcome; what changes is its value. On a
        refusal the seventeen declaration slots and ``label_index_map`` are
        ``None`` -- BECAUSE THERE IS NO DECLARATION, not because a default was
        substituted -- and ``refusal`` carries the record. On an emission
        ``refusal`` is ``None``.

        TWENTY-SEVEN AND NOT TWENTY-THREE. The outputs table is "the
        twenty-three plus the three this file fixes", and the three --
        ``assumption_ledger``, ``mathematical_spec_version`` and
        ``choice_weighting_record`` -- "travel with them". Two of them carry ``presence:
        always``; PRINCIPLES.md section 2.1 is what the
        ledger half is about ("a result is a number plus a
        machine-generated manifest of the assumption IDs"), and both
        sibling modules emit one.

        The twenty-seventh key, ``assumption_bindings``, travels beside
        ``assumption_ledger``: the declared values each of its rows binds,
        ``{}`` on a refusal.
        """
        record: dict[str, object] = {}
        if self.declaration is not None:
            record.update(self.declaration.as_machine_record())
        else:
            record.update(dict.fromkeys(DECLARATION_SLOT_KEYS))
            record["acceptance_alphabet"] = None
            record["label_index_map"] = None
        record["source_replacement_license"] = (
            None
            if self.source_replacement_license is None
            else self.source_replacement_license.as_machine_record()
        )
        record["reduction_chain_record"] = self.reduction_chain_record
        record["key_length_eligible"] = self.key_length_eligible
        record["gate_report"] = (
            None if self.gate_report is None else self.gate_report.as_machine_record()
        )
        record["refusal"] = (
            None if self.refusal is None else self.refusal.as_machine_record()
        )
        record["choice_weighting_record"] = _weighting_record(
            self.choice_weightings
        )
        record["assumption_ledger"] = list(self.assumption_ledger)
        record["assumption_bindings"] = ledger_bindings_record(
            self.assumption_bindings
        )
        record["mathematical_spec_version"] = MATHEMATICAL_SPEC_VERSION
        return record



@dataclass(frozen=True)
class FactorWeighting:
    """One applied ``choice_weighting``: where it was declared and what it built.

    ``req:choice-weighting-record``: the weightings are recorded one entry per
    measured factor at which a weighting is applied, each entry naming that
    factor. ``factor`` is the factor's name (its ``factor_label``, or the
    position default ``f<position>``) and ``family`` the setting-dependent
    family ``def:weighted`` constructed on that factor's own family. NO PARTY
    LABEL: in the basic format a factor's party label may differ by sector,
    so the entry names the factor only.
    """

    factor: Label
    family: SettingWeightedFamily


def _weighting_record(
    weightings: Sequence[FactorWeighting],
) -> list[dict[str, object]] | None:
    """Return the ``choice_weighting_record`` output key, or ``None``.

    ``rem:relabel``: the weighting is "recorded beside the chain in the emitted
    artefact as this module's own construction", and the row's presence rule is
    "emitted exactly when a ``choice_weighting`` was declared at some measured
    factor". ONE ENTRY PER WEIGHTED FACTOR, in the factors' order, each naming
    the factor (``req:choice-weighting-record``).
    THE FIELD LIST IS interface.yaml's: the factor, the declared matrix ``P``,
    the setting alphabet ``T``, the choice alphabet ``F`` with its declared
    order, the setting map ``t``, and THE PRODUCT ORDER OF THE EMITTED SUPPORT
    ``V_P``.

    THE SUPPORT IS RECORDED AS THE ORDERED PAIR LIST AND NOT AS A SET, because
    the order is the datum: ``def:weighted`` fixes it -- ``v`` in the declared
    order of ``V``, and within each ``v``, ``f`` in the declared order of
    ``F``, the pairs off the support omitted -- and it is the order
    ``label_index_map`` emits for ``V``.
    """
    if not weightings:
        return None
    return [_weighting_entry(item) for item in weightings]


def _weighting_entry(item: FactorWeighting) -> dict[str, object]:
    """Return one entry of ``choice_weighting_record``: one weighted factor."""
    weighting = item.family
    declared = weighting.weighting
    return {
        "factor": item.factor,
        "setting_alphabet": list(declared.setting_alphabet),
        "choice_alphabet": list(declared.choice_alphabet),
        "setting_map": {
            outcome: declared.setting_of[outcome]
            for outcome in weighting.source_alphabet
        },
        "matrix": {
            f"{setting}|{choice}": str(declared.weight(setting, choice))
            for setting in declared.setting_alphabet
            for choice in declared.choice_alphabet
        },
        "source_alphabet": list(weighting.source_alphabet),
        "support": [
            [label, *weighting.pairs[label]] for label in weighting.alphabet
        ],
    }


def link_row_discharged(
    specification: ProtocolSpecification,
    chain: ReductionChain,
    provenance: ChainProvenance | None,
) -> bool:
    """Whether ``req:link-row-provenance`` (ii) omits the A-LINK row here.

    THE PROVENANCE IS THE RUN'S AND THE REST IS DECIDED HERE. That each link
    is the instance link of a reductions artefact emitted in the same run, and
    that each presented physical family is that artefact's declared model or
    exactly its compression, cannot be read off the specification -- its link
    types and status tags are data a specification written by hand can carry
    equally (``def:spec`` (c)) -- so it arrives as ``chain_provenance``, beside
    the specification and never read from it. The parts of (ii) that are DATA
    are decided on the presented chain, and the row stays wherever one fails:

    * an empty source segment;
    * FOR EVERY MEASURED FACTOR (the joint
      discharge at several is ``reductions/thm:emitted-product`` (ii), (iii)
      with A-MEAS (iv), ``rem:obligations-discharged``): a receiver segment of
      one link -- a domination link after the instance link squashes another
      model -- whose id is the one the provenance names for that factor (a
      factor it does not name keeps the row); status ``exact`` and no channel
      supplied as data; the outcome correspondence the identity on that
      factor's target alphabet (its table, as (C2) reads it).

    The first factor's segment is ``chain``'s, a further factor's its own
    ``ReceiverPart.chain`` (``def:spec`` (c')), as the compilation reads them.
    """
    if provenance is None or chain.source_segment:
        return False
    for position, part in enumerate(specification.receiver_parts):
        factor_chain = chain if position == 0 else part.chain
        if not isinstance(factor_chain, ReductionChain):
            return False
        if factor_chain.source_segment or len(factor_chain.receiver_segment) != 1:
            return False
        label = (
            part.factor_label
            if part.factor_label is not None
            else default_factor_label(position)
        )
        link = factor_chain.receiver_segment[0]
        if link.link_id != provenance.link_of(label):
            return False
        if link.status is not LinkStatus.EXACT or link.channel_supplied:
            return False
        alphabet = link.target_alphabet
        if not alphabet:
            return False
        gamma = factor_chain.outcome_correspondence
        if set(gamma) != set(alphabet) or any(
            gamma[letter] != letter for letter in alphabet
        ):
            return False
    return True


def _assumption_ledger(
    specification: ProtocolSpecification,
    chain: ReductionChain,
    entries: tuple[ConstraintEntry, ...],
    key_length_eligible: bool,
    *,
    link_row_on_provenance: bool = False,
) -> tuple[str, ...]:
    """Return the ``assumption_ledger`` output key, row by row.

    PRINCIPLES.md section 2.1: "a result is a number plus a machine-generated
    manifest of the assumption IDs, module versions and claim graph it rests
    on". This is this module's contribution to that manifest, and both sibling
    modules emit the same shape.

    THE ORDER IS interface.yaml's -- the seven own rows in the order
    ``assumption_ledger.own_rows`` lists them, then the inherited ones -- and
    EACH ROW'S PRESENCE RULE IS THAT ROW'S OWN:

    * ``A-SPEC``, ``A-RHOM``: ``always``;
    * ``A-LINK``: "everywhere but Band A, where thm:band-a (v) proves every
      clause of the identity link": on Band A the chain is the
      identity link declared directly, ``thm:band-a`` does not assume
      A-LINK, and its part (v) shows that link satisfies every clause, so the
      row would name a premise the route does not rest on. AND
      "but one measured factor
      whose receiver segment is the single instance link of a reductions
      artefact of this run, exact, with no channel supplied as data, the
      identity outcome correspondence and an empty source segment"
      (``req:link-row-provenance`` (ii); :func:`link_row_discharged`), where
      ``reductions/thm:emit`` (iii), ``thm:chain`` (i)-(iii) and
      ``thm:transfer`` prove every clause (``rem:obligations-discharged``);
    * ``A-ALICE-MEAS``: "wherever no source-replacement certificate is
      demanded (untrusted-source mode, or d_A = 1)", the exact complement of
      ``transmitter/req:licence-scope``, which demands one only in
      trusted-source mode at ``d_A >= 2``. It is read off the transmitter
      artefact (:attr:`~certiqs_key.protocol_compiler.spec.SourcePart.source_mode`,
      its marginal slot holding nomarg, and
      :attr:`~certiqs_key.protocol_compiler.spec.SourcePart.alice_dim`) and
      KEYED TO THE DEMAND, NOT TO WHETHER A CERTIFICATE IS PRESENT: a trusted
      ``d_A = 1`` specification carrying a certificate voluntarily still
      emits the row;
    * ``A-COIN``: "whenever a public choice of EITHER FORM is declared", and
      ``inputs.public_choices`` types "ONE SUCH RECORD PER PARTY", so all
      THREE ways one arrives: a choice-weighted Alice presentation, a
      choice-weighted RECEIVER family (``def:spec`` (b): the physical POVM
      "possibly presented as a choice-weighted family"), or a declared
      Bob-side setting-dependent weighting;
    * ``A-ATK``: "whenever ``m >= 1`` AND a
      key-length-eligible declaration is wanted", which is ``thm:band-a`` (iii)'s
      "not engaged when CList is empty" read together with the flag the gates
      decided;
    * ``A-IDEAL``: Band A only (:func:`band_a_route`, which reads the
      emitted sector set, the joint one in the general format, as well as
      every factor's chain, because ``def:banda`` is a conjunction; a route
      with more than one measured factor was refused before emission).

    No row for the exact admissibility of the physical receiver family as
    presented: it is clause (iv) of ``def:well-formed-spec``, decided on every
    route (:func:`decide_physical_family`), and A-PRESENT, its key
    ``presented_receiver_family``, is not a ledger key.

    No row for the block restriction of the feasible set: it is the remark
    ``rem:block-restriction``, which ``meat-core/thm:reduction``, step 1,
    proves, and its key ``block_diagonal_feasible_set`` is not a ledger key.

    THE INHERITED KEYS ARE READ OFF THE SUPPLIER ARTEFACT WHERE THERE IS ONE.
    The transmitter's are literally its artefact's own
    ``assumption_ledger``, copied in its order and not re-derived here: that
    module decides which of A-ENS (or a source model's A-WCP in its place),
    A-SEQ and A-SRC its emission rests on, and re-deciding would be inferring
    rather than reading. The rows carry no flag: whether a run rests on each
    unverified is its assumption's ``verification`` field, which the run
    record reads by machine key.

    NO ROW OF ``reductions/ass:recv`` (A-RECV), ON ANY ROUTE (the interface's
    ``assumption_ledger.a_recv_not_emitted_note``). ``def:spec`` (c) hands this
    module a CHAIN and not the reductions artefact, so it can neither bind the
    supplier's version nor tell an artefact the run built from one supplied
    from outside. The row is the reductions artefact's own, emitted or omitted
    there (``reductions/req:recv-row-provenance``), and the run tier reads that
    module's ledger off each reductions artefact it consumed
    (spec/architecture.md 4.4). No claim of this module assumes A-RECV.

    ONE ROW IS CARRIED FOR ANOTHER MODULE'S RESULTS. No result of this module
    assumes A-ALICE-MEAS (``thm:typing``, ``thm:sifting-and-key`` and
    ``thm:measurements-and-statistics`` assume A-SPEC alone,
    ``thm:chain-consumption`` A-LINK alone): it is a premise of
    ``meat-core/thm:keylength``. This module emits it because it holds the
    declaration it describes. The run record needs no attribution (it
    reconciles against the union of every module's roots); the ledger check
    attributes it to that result through ``runs.assumptions.CARRIED_ROWS``.
    """
    band_a = band_a_route(specification)
    keys: list[str] = [ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SPEC]]
    # ass:alice-meas (i): no source-replacement certificate is demanded, the
    # complement of transmitter/req:licence-scope (trusted and d_A >= 2), AND
    # the letter alphabet has at least two letters: at one letter {M_x} is the identity
    # on A and the premise holds of every device.
    if _alice_measurement_engaged(specification):
        keys.append(ASSUMPTION_MACHINE_KEYS[AssumptionId.A_ALICE_MEAS])
    keys.append(ASSUMPTION_MACHINE_KEYS[AssumptionId.A_RHOM])
    if public_choice_declared(specification):
        keys.append(ASSUMPTION_MACHINE_KEYS[AssumptionId.A_COIN])
    # thm:band-a (v): the identity link of Band A satisfies every clause of
    # A-LINK, and req:band-a-identity-link has decided on the record that the
    # link is that identity link (channel as data, gamma the identity, (C4)
    # decided); req:link-row-provenance (ii): so do the reductions module's
    # theorems for its in-run single exact instance link. Everywhere else the
    # row is emitted.
    if not band_a and not link_row_on_provenance:
        keys.append(ASSUMPTION_MACHINE_KEYS[AssumptionId.A_LINK])
    if entries and key_length_eligible:
        keys.append(ASSUMPTION_MACHINE_KEYS[AssumptionId.A_ATK])
    if band_a:
        keys.append(ASSUMPTION_MACHINE_KEYS[AssumptionId.A_IDEAL])
    keys.extend(specification.source.artifact.assumption_ledger)
    return tuple(keys)


def public_choice_declared(specification: ProtocolSpecification) -> bool:
    """Whether a public choice of EITHER FORM is declared: A-COIN's presence rule.

    The interface's ``emission_rule``: "whenever a public choice of either
    form is declared anywhere in the specification: a choice-weighted
    presentation of Alice's measurement, a choice-weighted physical family of
    any measured factor, or a `choice_weighting` of any measured factor,
    whichever party's" (``ass:coin``). ALL THREE WAYS A PUBLIC CHOICE ARRIVES,
    the last two AT EVERY MEASURED FACTOR: reading the first
    factor only would emit no A-COIN for a choice declared at a second
    station, and A-COIN's if_violated is a "SECURITY BREAK
    IN THE UNSAFE DIRECTION", so a missing row is the direction that matters.
    Public so that the run tier reads the predicate the ledger is emitted
    under rather than a copy (``runs.assumptions._compiler_roots``).
    """
    return (
        specification.source.alice_form is AliceForm.POVM
        and isinstance(specification.source.alice_povm, PublicChoices)
    ) or any(
        isinstance(part.physical_povm, PublicChoices)
        or part.choice_weighting is not None
        for part in specification.receiver_parts
    )


def _alice_measurement_engaged(specification: ProtocolSpecification) -> bool:
    """Whether ``ass:alice-meas`` is non-trivial: A-ALICE-MEAS's emission rule.

    "Wherever no source-replacement certificate is demanded (untrusted-source
    mode, or d_A = 1) and the letter alphabet X has at least two letters; at
    one letter {M_x} is the identity on A and ass:alice-meas holds of every
    device" (the interface's emission_rule).
    A-SPEC binds ``alice_povm`` under the same condition.
    """
    return (
        _no_certificate_demanded(specification)
        and len(specification.source.alphabet) >= 2
    )


def _no_certificate_demanded(specification: ProtocolSpecification) -> bool:
    """Whether no source-replacement certificate is demanded: untrusted, or ``d_A = 1``.

    The scope of ``ass:alice-meas`` and of ``ass:spec`` (i)'s clause on
    ``{M_x}``, the exact complement of ``transmitter/req:licence-scope``, which
    demands one only in trusted-source mode at ``d_A >= 2``.
    """
    return (
        specification.source.source_mode is SourceMode.UNTRUSTED
        or specification.source.alice_dim == 1
    )


# ---------------------------------------------------------------------------
#  The assumption bindings
# ---------------------------------------------------------------------------


def _specification_shape(specification: ProtocolSpecification) -> Bindings:
    """Return the declared dimensions, alphabets and tables of ``Spec``, by shape.

    What ``ass:spec`` (i) says describes the apparatus, read off the parts of
    ``def:spec``: ``d_A``, ``X`` and the transmitted system of (a); the
    dimension of each physical receiver system of (b) and (b'); and of (d) the
    readout and announcement alphabets the tables are total on, the holder and
    the key alphabet ``Zval`` of ``ass:spec`` (ii), and ``Chat``. The tables
    themselves are the emitted ``announce_*``, ``key_map`` and
    ``accept_statistic`` keys, which this shape indexes and does not repeat.
    """
    source = specification.source
    public = specification.public
    partition = public.partition
    return (
        ("alice_dim", source.alice_dim),
        ("signal_alphabet", tuple(source.alphabet)),
        ("transmitted_dim", source.transmitted_dim),
        (
            "physical_receiver_dims",
            tuple(part.physical_dim for part in specification.receiver_parts),
        ),
        (
            "readout_alphabets",
            (
                (str(Party.ALICE), tuple(partition.alice_readout_alphabet)),
                (str(Party.BOB), tuple(partition.bob_readout_alphabet)),
            ),
        ),
        (
            "announcement_alphabets",
            (
                (str(Party.ALICE), tuple(public.alice_announcement_alphabet)),
                (str(Party.BOB), tuple(public.bob_announcement_alphabet)),
            ),
        ),
        ("key_holder", str(public.holder)),
        ("key_alphabet", tuple(public.key_alphabet)),
        ("acceptance_alphabet", tuple(public.acceptance_alphabet)),
    )


def _receiver_family_shape(part: ReceiverPart) -> Bindings:
    """Return one measured factor's physical family ``{F^ph_w}`` as presented.

    ``ass:spec`` (i) says this family is the measurement performed, and its
    presentation is bound with it: the alphabet ``V^ph`` of a direct family,
    the choice alphabet of a weighted one (whose weights are A-COIN's
    ``public_choices``). Its matrices are not inlined; their exact
    admissibility is decided (``req:physical-family-decision``).
    """
    povm = part.physical_povm
    presented: Bindings = (
        (("presentation", "direct"), ("alphabet", tuple(povm.alphabet)))
        if isinstance(povm, DirectPovm)
        else (("presentation", "choice-weighted"), ("choices", tuple(povm.choices)))
    )
    return (
        ("party", str(part.party)),
        ("physical_dim", part.physical_dim),
        *presented,
    )


def _choice_record(choices: PublicChoices) -> Bindings:
    """Return one ``public_choices`` record: ``T_pub`` and the weights ``q_t``."""
    return (
        ("party", str(choices.party)),
        ("choices", tuple(choices.choices)),
        (
            "weights",
            tuple(
                (choice, exact(choices.weights[choice])) for choice in choices.choices
            ),
        ),
    )


def _declared_public_choices(
    specification: ProtocolSpecification,
) -> tuple[Bindings, ...]:
    """Return every declared ``public_choices`` record, Alice's first."""
    records: list[Bindings] = []
    # IN THE POVM FORM ONLY: an ensemble presentation declares no {M_x} and
    # ``SourcePart.alice_povm`` refuses to present one there.
    if specification.source.alice_form is AliceForm.POVM:
        alice = specification.source.alice_povm
        if isinstance(alice, PublicChoices):
            records.append(_choice_record(alice))
    for part in specification.receiver_parts:
        if isinstance(part.physical_povm, PublicChoices):
            records.append(_choice_record(part.physical_povm))
    return tuple(records)


def _declared_weightings(
    specification: ProtocolSpecification,
) -> tuple[Bindings, ...]:
    """Return every declared ``choice_weighting``: ``F``, ``T`` and ``P(f | t)``.

    One record per measured factor that declares one, naming the factor (the
    interface's ``binds`` for A-COIN: "P(f | t) of each measured factor that
    declares one"). No party: in the basic format a factor's party label may
    differ by sector.
    """
    records: list[Bindings] = []
    for position, part in enumerate(specification.receiver_parts):
        weighting = part.choice_weighting
        if weighting is None:
            continue
        records.append(
            (
                (
                    "factor",
                    part.factor_label
                    if part.factor_label is not None
                    else default_factor_label(position),
                ),
                ("choice_alphabet", tuple(weighting.choice_alphabet)),
                ("setting_alphabet", tuple(weighting.setting_alphabet)),
                (
                    "matrix",
                    tuple(
                        (
                            f"{setting}|{choice}",
                            exact(weighting.weight(setting, choice)),
                        )
                        for setting in weighting.setting_alphabet
                        for choice in weighting.choice_alphabet
                    ),
                ),
            )
        )
    return tuple(records)


def _link_shape(link: ChainLink) -> Bindings:
    """Return one link as A-LINK binds it: the slots ``ass:link``'s clauses turn on.

    Its type (the receiver clause (i) or the source clause (ii)), its status,
    whether it supplies its channel as data (clause (iv); (i)(a) and (ii)(a)
    where it does not) and how many constraint entries it transports (clause
    (iii)). The slots of ``reduction_chain_record`` (:func:`chain_record`),
    the descriptors omitted.
    """
    return (
        ("link_id", link.link_id),
        ("link_type", link.link_type),
        ("status", str(link.status)),
        ("channel_supplied", link.channel_supplied),
        ("transported_constraints", len(link.transported_constraints)),
    )


def _chain_shape(
    specification: ProtocolSpecification, chain: ReductionChain
) -> Bindings:
    """Return the presented chain: both segments, every measured factor's included."""
    shape: list[Binding] = [
        ("source_segment", tuple(_link_shape(link) for link in chain.source_segment)),
        (
            "receiver_segment",
            tuple(_link_shape(link) for link in chain.receiver_segment),
        ),
    ]
    further = tuple(
        tuple(_link_shape(link) for link in part.chain.receiver_segment)
        for part in specification.further_receiver_factors
        if isinstance(part.chain, ReductionChain)
    )
    if further:
        shape.append(("further_receiver_segments", further))
    return tuple(shape)


def _assumption_bindings(
    specification: ProtocolSpecification,
    chain: ReductionChain,
    entries: tuple[ConstraintEntry, ...],
    ledger: tuple[str, ...],
) -> LedgerBindings:
    """Return the ``assumption_bindings`` output key, one entry per ledger row.

    Beside each row of the ledger, the
    declared values its assumption's clauses are about, each named by the
    declared input it comes from (:mod:`certiqs_key.domain.bindings` for the
    shape; an operator is bound by its shape and never inlined). The
    interface's ``assumption_ledger.binds`` lists the same names; the clause
    each comes from is said here, row by row:

    * A-SPEC (``ass:spec``): ``specification`` -- the declared dimensions,
      alphabets and tables of (i), with the holder and ``Zval`` of (ii);
      ``receiver_family`` -- the physical family (i) says is the measurement
      performed; and ``alice_povm`` -- ``{M_x}`` of (i), ONLY where no
      source-replacement certificate is demanded, the scope (i) states for it.
    * A-ALICE-MEAS (``ass:alice-meas`` (i)): ``alice_povm``, and the
      ``source_mode`` that, with ``d_A``, decides the clause's scope.
    * A-RHOM (``ass:rhom`` (i)): ``specification`` and ``source_mode`` -- the
      specification, declaration, source mode and operators (i) says are the
      same in every round. The round count is no input of this module.
    * A-COIN (``ass:coin``): ``public_choices`` -- ``T_pub`` and ``q_t`` of
      (i), each declared record; ``choice_weighting`` -- ``P(f | t)`` of (ii),
      where declared; and ``specification``, whose announcement tables are the
      public structure (iii) says announces or withholds each choice.
    * A-LINK (``ass:link``): ``reduction_chain`` -- every link of either
      segment, with the slots its clauses (i)-(iv) turn on.
    * A-ATK (``ass:atk``): ``constraint_entries`` -- the right-hand-side tag
      of each entry of the non-empty ``CList`` (i) says is licensed;
      ``source_mode`` -- the mode it is licensed for; ``reduction_chain`` and,
      where supplied, ``attack_set_license`` -- the chain (ii) says certifies
      the licensed reduction, and that certificate.
    * A-IDEAL (``ass:ideal``): ``declared_povm`` -- the receiver declared
      directly, of (i) and (ii); ``transmitted_dim`` -- the transmitted
      system (iii) says is exactly a qubit.
    * the transmitter's rows: the transmitter artefact's own
      ``assumption_bindings``, copied as its ledger is and not re-derived.
    """
    keys = ASSUMPTION_MACHINE_KEYS
    source = specification.source
    spec_shape: Binding = ("specification", _specification_shape(specification))
    receivers = tuple(
        _receiver_family_shape(part) for part in specification.receiver_parts
    )
    mode: Binding = ("source_mode", str(source.source_mode))
    alice: Binding = (
        "alice_povm",
        alice_measurement_shape(source.alphabet, source.alice_dim, source.alice_form),
    )
    chain_shape: Binding = ("reduction_chain", _chain_shape(specification, chain))

    coin: list[Binding] = []
    choices = _declared_public_choices(specification)
    if choices:
        coin.append(("public_choices", choices))
    weightings = _declared_weightings(specification)
    if weightings:
        coin.append(("choice_weighting", weightings))
    coin.append(spec_shape)

    tags = tuple(None if entry.tag is None else str(entry.tag) for entry in entries)
    attack: list[Binding] = [
        ("constraint_entries", (("count", len(entries)), ("rhs_tags", tags))),
        mode,
        chain_shape,
    ]
    licence = specification.constraints.attack_set_license
    if licence is not None:
        attack.append(("attack_set_license", (("supplier", licence.supplier),)))

    own: dict[str, Bindings] = {
        keys[AssumptionId.A_SPEC]: (
            spec_shape,
            ("receiver_family", receivers),
            *((alice,) if _alice_measurement_engaged(specification) else ()),
        ),
        keys[AssumptionId.A_ALICE_MEAS]: (alice, mode),
        keys[AssumptionId.A_RHOM]: (spec_shape, mode),
        keys[AssumptionId.A_COIN]: tuple(coin),
        keys[AssumptionId.A_LINK]: (chain_shape,),
        keys[AssumptionId.A_ATK]: tuple(attack),
        keys[AssumptionId.A_IDEAL]: (
            ("declared_povm", receivers),
            ("transmitted_dim", source.transmitted_dim),
        ),
    }
    inherited = dict(source.artifact.assumption_bindings)
    return tuple((key, own.get(key, inherited.get(key, ()))) for key in ledger)


def decide_every_conditional_family(
    specification: ProtocolSpecification,
) -> ConditionalFamilyDecision:
    """Decide each declared presentation's conditional families, BOTH PARTIES.

    Definition ``def:compile``: "wherever one is presented, ON EITHER PARTY'S
    SIDE, the map DECIDES, BEFORE IT FORMS A PRODUCT, that each declared
    conditional family ``{N_{u|t}}_u`` is exactly admissible for the map those
    families carry, refusing with ``conditional_family_not_admissible``
    otherwise". This is that clause, and it runs before stage 1.

    WHY BOTH PRESENTATIONS ARE DECIDED HERE AND NOT WHERE EACH IS CONSUMED.
    The receiver's presentation is resolved before the chain and Alice's when
    the slots are filled, so deciding each beside its own resolution would put
    Alice's decision AFTER the chain row -- and the fail-closed table puts this
    rule at ORDER 1, before ``chain_interface_conditions`` at order 2, with
    "ONE DECISION OF THE COMPILATION MAP IS TAKEN BEFORE THIS ROW, and it is
    row 1 ... Nothing else of the map precedes this row". The claim says the
    same of every presentation: "before it forms any product AND THEREFORE
    BEFORE THE INTERFACE CONDITIONS ON THE CHAIN ARE DECIDED".

    THE ORDER WITHIN THE ROW IS EACH MEASURED FACTOR'S, IN FACTOR ORDER, AND
    THEN ALICE'S, which is the order the stages consume them in and therefore
    the order the rest of the transcript is written in (:class:`
    ~certiqs_key.protocol_compiler.transcript.PredicateTranscript`: "THE ORDER
    IS THE DECISION ORDER"). The party prefix is what keeps two presentations
    carrying the same joint labels apart, which both shipped instances of BB84
    do.

    EVERY RECEIVER PART, NOT ONLY THE FIRST: ``def:well-formed-spec`` (iv) states
    the condition of each measured factor's physical family, and
    ``req:physical-family-decision`` decides a choice-weighted one's (S) alone
    because its conditional families were decided here first. Where the
    specification presents several factors, each presentation's transcript
    key and refusal also name its factor (``<factor>:``), since two factors
    may carry the same party label; at one factor the key is the party's
    alone, as it always was.

    WHICH ARRIVING ORDER EACH PRESENTATION IS GIVEN, and it is
    ``def:compile``'s binding rule and not a new rule:

    * ALICE'S IS ``X``, which "arrives ordered with the source part"
      (``def:spec`` (a)) and is
      :attr:`~certiqs_key.protocol_compiler.spec.SourcePart.alphabet`, the
      transmitter artefact's declared signal alphabet. Condition (S) on
      ``{N_{u|t}}_u`` is then read in the restriction of THAT order to the
      elements ``t`` contributes.
    * THE RECEIVER'S IS NONE, and that is a fact about this input shape rather
      than a choice: the alphabet that indexes a receiver presentation is the
      physical receiver alphabet, and here that alphabet IS what the weighting
      produces -- no separate declared order arrives with it -- so "the choice
      the compiler makes and emits is the record's own listing".

    NO PRESENTATION IS REFUSED FOR AN ORDER at either site
    (:func:`~certiqs_key.protocol_compiler.weights.conditional_family_order`).

    AND EACH PRESENTATION IS GIVEN THE DIMENSION OF THE SYSTEM IT MEASURES,
    which is what condition (C) is compared against: ``d_A`` from the
    transmitter artefact for Alice's, ``physical_dim`` from the receiver part
    for the receiver's. Reading (C) against the declared arrays' own dimension
    would admit a family that is a POVM on a space this specification does not
    declare.
    """
    recorded: list[PredicateOutcome] = []
    parts = specification.receiver_parts
    several = len(parts) > 1
    presentations: tuple[
        tuple[PovmPresentation, int, tuple[Label, ...] | None, Label | None], ...
    ] = tuple(
        (
            part.physical_povm,
            part.physical_dim,
            None,
            (
                (
                    part.factor_label
                    if part.factor_label is not None
                    else default_factor_label(position)
                )
                if several
                else None
            ),
        )
        for position, part in enumerate(parts)
    )
    # In ensemble form the artefact declares {N_x}, and its `alice_povm` table
    # is intentionally empty because the generally irrational POVM it denotes
    # is formed by no one.  There is therefore no Alice conditional POVM
    # presentation for this decision to read.
    if specification.source.alice_form is AliceForm.POVM:
        presentations = (
            *presentations,
            (
                specification.source.alice_povm,
                specification.source.alice_dim,
                specification.source.alphabet,
                None,
            ),
        )
    for presentation, system_dim, arriving, factor in presentations:
        if not isinstance(presentation, PublicChoices):
            continue
        decision = decide_conditional_families(
            presentation, system_dim, arriving, factor
        )
        recorded.extend(decision.predicates)
        if decision.refusal is not None:
            return ConditionalFamilyDecision(
                refusal=decision.refusal, predicates=tuple(recorded)
            )
    return ConditionalFamilyDecision(refusal=None, predicates=tuple(recorded))


@dataclass(frozen=True)
class PhysicalFamilyDecision:
    """``req:physical-family-decision`` on one measured factor's physical family.

    THE FIRST FAILURE AND NOTHING AFTER IT, as the conditional families'
    decision: ``predicates`` ends at the decision that failed and ``refusal``
    carries that one failure, ``physical_family_not_admissible``.
    """

    refusal: Refusal | None
    predicates: tuple[PredicateOutcome, ...] = ()


def decide_physical_family(
    part: ReceiverPart,
    resolved: DirectPovm,
    factor: Label,
) -> PhysicalFamilyDecision:
    """Decide the physical receiver family as presented exactly admissible.

    ``req:physical-family-decision``, on clause (iv) of
    ``def:well-formed-spec``: on every route, one measured factor at a time,
    on its physical receiver space READ AS ONE BLOCK -- that space carries no
    sector map this module holds, so (T) is empty for it as for Alice's data
    (``def:exact``):

    * PRESENTED DIRECTLY: (H), (P) and (C) of ``def:exact``, and (S) on the
      completeness sum in the declared order of its alphabet ``V^ph``. (C) is
      read on the computed total against the identity on the DECLARED
      physical receiver dimension, as the conditional families' (C) is.
    * PRESENTED CHOICE-WEIGHTED: (S) on its own declared-order sum, the order
      being the presentation's own listing (the order the weighted family
      arrives in, :func:`~certiqs_key.protocol_compiler.weights.resolve_povm`).
      Its conditional families were decided first
      (``req:conditional-family-decision``) and the representability of the
      products formed from them was decided on the path that formed
      ``resolved``; (T), (H) and (P) of it follow from the first and its (C)
      from that (S) with them (``rem:condfamily``'s converse), so (S) is the
      one condition decided on the family itself.

    The caller takes it before any condition of ``def:chaincond`` is decided
    on the chain. A failure refuses with ``physical_family_not_admissible``,
    naming the measured factor, the predicate and the index of the first
    failure (for (S), the index of the first inexact addition). Each decision
    is recorded in the transcript under the compilation map, keyed by the
    element ``<factor>:{F^ph_w}``.
    """
    element = f"{factor}:{{F^ph_w}}"
    named = f"measured factor {factor!r} (party {str(part.party)!r})"
    recorded: list[PredicateOutcome] = []

    def refusing(detail: str) -> PhysicalFamilyDecision:
        """Return the decision that stopped at the first failure."""
        return PhysicalFamilyDecision(
            refusal=Refusal(
                reason=RefusalReason.PHYSICAL_FAMILY_NOT_ADMISSIBLE,
                detail=detail,
            ),
            predicates=tuple(recorded),
        )

    order = resolved.alphabet
    elements = resolved.ordered()
    if isinstance(part.physical_povm, DirectPovm):
        for predicate, holds in (
            ("(H)", is_hermitian),
            ("(P)", is_positive_semidefinite),
        ):
            failed_at: int | None = None
            for index, element_matrix in enumerate(elements, start=1):
                # A non-Hermitian operator is not positive semidefinite, and
                # (H) is decided first, so (P) is asked only of Hermitian ones.
                if not holds(element_matrix):
                    failed_at = index
                    break
            recorded.append(
                PredicateOutcome(
                    source=PredicateSource.COMPILATION_MAP,
                    predicate=predicate,
                    element=element,
                    block=None,
                    outcome=failed_at is None,
                    first_failure_index=failed_at,
                )
            )
            if failed_at is not None:
                return refusing(
                    f"the physical receiver family of {named} is not exactly "
                    f"admissible: condition {predicate} of def:exact fails on "
                    "its physical receiver space read as one block, at element "
                    f"{failed_at} of its declared order, F^ph_{order[failed_at - 1]} "
                    "(def:well-formed-spec (iv); req:physical-family-decision)"
                )
    verdict = sum_in_declared_order(list(elements))
    if isinstance(part.physical_povm, DirectPovm):
        complete = verdict.computed_total_equals(identity(part.physical_dim))
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.COMPILATION_MAP,
                predicate="(C)",
                element=element,
                block=None,
                outcome=complete,
            )
        )
        if not complete:
            return refusing(
                f"the physical receiver family of {named} is not a measurement: "
                "its computed completeness sum over its declared alphabet is not "
                f"the identity on the declared {part.physical_dim}-dimensional "
                "physical receiver space, so condition (C) of def:exact fails "
                "(def:well-formed-spec (iv); req:physical-family-decision)"
            )
    recorded.append(
        PredicateOutcome(
            source=PredicateSource.COMPILATION_MAP,
            predicate=SUMMATION_PREDICATE,
            element=element,
            block=None,
            outcome=verdict.rounds_nowhere,
            first_failure_index=(
                None if verdict.rounds_nowhere else verdict.first_inexact_index
            ),
            first_inexact_index=(
                None if verdict.rounds_nowhere else verdict.first_inexact_index
            ),
        )
    )
    if not verdict.rounds_nowhere:
        presented = (
            "presented directly"
            if isinstance(part.physical_povm, DirectPovm)
            else "presented as a choice-weighted family"
        )
        return refusing(
            f"the completeness sum of the physical receiver family of {named}, "
            f"{presented}, ROUNDS: the first inexact addition is at element "
            f"{verdict.first_inexact_index} of its declared order "
            f"{list(order)}. Condition (S) of def:exact is on the ADDITIONS and "
            "not on the operands (def:well-formed-spec (iv); "
            "req:physical-family-decision)"
        )
    return PhysicalFamilyDecision(refusal=None, predicates=tuple(recorded))


def _index_map(declaration: CandidateDeclaration) -> LabelIndexMap:
    """Return ``idx`` over the nine alphabets Definition ``def:compile`` names.

    IN THE GENERAL FORMAT IT HAS THE DERIVED COMPONENTS BESIDE THEM, and they
    are derived and not chosen: "one component per factor alphabet ``V^f`` and
    one per factor sector set ``S^f``, and, where an ``A`` factor is emitted, one
    on ``T``, which is the total order that factor's own map fixes. Its
    components on ``V`` and on ``S`` are the product orders (DX1) and (DX3)
    derive from the factors' orders and are not further choices".

    So the nine are built exactly as they were -- a declaration of the accepted
    format gets the map it got, component for component -- and the per-factor
    components are added only where a factor list is declared.
    """
    alphabets: dict[str, tuple[Label, ...]] = {
        "X": declaration.alice_alphabet,
        "V": declaration.bob_alphabet,
        "S": declaration.sectors.labels,
        "O_A": declaration.partition.alice_readout_alphabet,
        "O_B": declaration.partition.bob_readout_alphabet,
        "C_A": declaration.alice_announcement_alphabet,
        "C_B": declaration.bob_announcement_alphabet,
        "Chat": declaration.acceptance_alphabet,
        "Z_perp": tuple(str(value) for value in declaration.raw_key_alphabet),
    }
    assert set(alphabets) == set(INDEXED_ALPHABETS)
    return build_label_index_map(
        alphabets, factor_components=_factor_components(declaration)
    )


def _factor_components(
    declaration: CandidateDeclaration,
) -> tuple[tuple[str, tuple[Label, ...]], ...]:
    """Return the general format's per-factor ``idxm`` components, in order.

    ``V[<factor>]`` and ``S[<factor>]`` per measured factor in the product order
    of ``F``, and ``T`` where an ``A`` factor is emitted. EMPTY FOR A DECLARATION
    OF THE ACCEPTED FORMAT, which declares no factor list: there the nine
    components are the whole map, as they have always been.

    THE NAMES ARE DERIVED FROM THE FACTOR LABELS and are not a vocabulary of
    their own: a factor's label is what a scoped entry names, so naming its two
    components after it is what lets a reader of the map find the order a
    per-factor condition (S) was decided in.
    """
    if declaration.sector_factorisation is None:
        return ()
    components: list[tuple[str, tuple[Label, ...]]] = []
    if declaration.alice_factor is not None:
        components.append(("T", declaration.alice_sectors.labels))
    family = declaration.bob_factors
    for position, (label, factor) in enumerate(
        zip(
            declaration.measured_factor_labels,
            declaration.measured_factors,
            strict=True,
        )
    ):
        if family is not None:
            components.append((f"V[{label}]", family.factor(position).alphabet))
        components.append((f"S[{label}]", factor.sectors.labels))
    return tuple(components)


def _refused(
    chain_report: ChainReport | None,
    record: dict[str, object],
    refusal: Refusal,
    *,
    validation: ValidationResult | None = None,
    gates: GateResolution | None = None,
    certificate: CertificateVerification | None = None,
    factor_chain: FactorChainReport | None = None,
) -> CompilationResult:
    """Return a refusing result: no declaration, no flag, no licence."""
    return CompilationResult(
        declaration=None,
        refusal=refusal,
        key_length_eligible=None,
        gate_report=None if gates is None else gates.report,
        reduction_chain_record=record,
        validation=validation,
        chain=chain_report,
        gates=gates,
        certificate=certificate,
        source_replacement_license=None,
        verified_witness=None,
        factor_chain=factor_chain,
    )


def check_certificate_pair_typing(
    specification: ProtocolSpecification, chain: ReductionChain
) -> None:
    """Re-decide that the licensed certificate is written against the ARTEFACT'S pair.

    THE COMPILER IS HANDED ONE PAIR -- the artefact's ``virtual_ensemble``, which
    ``def:spec`` (a) reads off
    :class:`~certiqs_key.transmitter.artifact.TransmitterArtifact` -- and the identity
    between the two pairs at ``L_s = 0`` is decided where both exist, in
    :func:`certiqs_key.transmitter.artifact.emit_artifact`. What is left on this side is
    what the ``decide_never_infer`` convention asks of every consumed datum: THE
    CERTIFICATE THIS MODULE RE-DECIDES (G2) ON MUST BE WRITTEN AGAINST THE PAIR THE
    ARTEFACT EMITS. A licence record whose certificate is internally consistent against
    a DIFFERENT pair would otherwise pass gate (G2) while the emitted declaration
    describes another source, which is the mis-specified-source hazard row 3 of the gate
    outcome table exists to prevent, reached by a route no gate covers.

    AT ``L_s >= 1`` IT DOES NOT APPLY AND MUST NOT. There the virtual pair and
    the specified pair are MEANT to differ and ``def:chaincond``'s source-side
    conditions -- ``transmitter/def:source-segment`` (S3) -- are what relate
    them; the artefact still emits the virtual pair, which is "the object a
    consumer receives", so the comparison below is with that and not with a
    pair this module never sees.

    THE CATEGORY IS :class:`~certiqs_key.foundations.errors.MalformedInputError`,
    symmetrically with the sibling guards on
    :meth:`certiqs_key.protocol_compiler.gates.GateInputs.__post_init__`: such
    a presentation is not a presentation of an input this module types, so no
    clause of ``def:validator`` can be read against it and refusing it with an
    invented reason code would be inventing vocabulary. The comparison is
    EXACT, in the substrate, with no tolerance.
    """
    source = specification.source
    licence = source.artifact.source_replacement_license
    if licence is None:
        return
    certificate = licence.certificate
    if certificate is None:
        return
    if certificate.virtual_dim != source.transmitted_dim:
        raise MalformedInputError(
            "the licensed certificate is written against a virtual system of "
            f"dimension {certificate.virtual_dim}, while the artefact emits "
            f"A^v of dimension {source.transmitted_dim}"
        )
    if set(certificate.virtual_weights) != set(source.signal_weights) or set(
        certificate.virtual_states
    ) != set(source.signal_states):
        raise MalformedInputError(
            "the licensed certificate and the artefact's virtual ensemble are "
            "indexed by different signal alphabets"
        )
    for label in source.alphabet:
        if certificate.virtual_weights[label] != source.signal_weights[label]:
            raise MalformedInputError(
                f"the licensed certificate declares p_{label!r} = "
                f"{certificate.virtual_weights[label]} against the artefact's "
                f"{source.signal_weights[label]}"
            )
        if not equal(certificate.virtual_states[label], source.signal_states[label]):
            raise MalformedInputError(
                f"the licensed certificate's rho^v_{label!r} differs from the "
                "one the artefact emits; gate (G2) would then re-decide the "
                "five conditions on a pair the declaration does not describe"
            )


def _certificate_predicates(
    verification: CertificateVerification,
) -> tuple[PredicateOutcome, ...]:
    """Return gate (G2)'s five conditions as the transcript keys them.

    THE DECISIONS ARE THE COMPILER'S AND THE KEYS ARE THE COMPILER'S, WHICH IS
    WHY THIS FUNCTION IS HERE AND NOT IN THE TRANSMITTER. ``def:eligible`` (G2)
    RE-DECIDES the five conditions "on the emitted data" (the
    ``decide_never_infer`` convention) and
    :func:`compile_specification` is where it does it; the record it re-decided
    them on is the transmitter's, and the vocabulary of the key --
    :class:`~certiqs_key.protocol_compiler.transcript.PredicateSource` -- is
    this module's, which a module the compiler depends on may not import
    (PRINCIPLES.md section 4, and
    :class:`~certiqs_key.transmitter.certificate.CertificateVerification`'s
    docstring).

    THE ROW'S "three conditions on ``Psi``" ARE FOUR ENTRIES, and the fourth is
    not an invention: ``def:srcert`` states them as "``Psi`` Hermitian,
    ``Psi^2 = Psi`` and ``tr Psi = 1``, EACH DECIDED EXACTLY AND THE TRACE
    SUMMED WITHOUT ROUNDING", so the trace condition has an identity leg and a
    condition-(S) leg, decided separately and recorded separately -- exactly as
    check V2 records them for ``tau_A``. Collapsing them would lose the index
    the row asks a failing (S) for.

    (SR3) GETS NO ENTRY. It "is decided by NO function of the emitted data"
    (``transmitter/thm:certificate-sufficiency`` (i)) and gate (G2) "tests
    PRESENCE, NEVER TRUTH", and the row's scope note excludes "the licence
    record and its clause (SR3) at gate (G2)" from the enumeration by name.
    """
    purity = verification.purity
    recorded: list[PredicateOutcome] = [
        PredicateOutcome(
            source=PredicateSource.G2,
            predicate="(H)",
            element="Psi",
            block=None,
            outcome=purity.hermitian,
        ),
        PredicateOutcome(
            source=PredicateSource.G2,
            predicate="Psi^2 = Psi",
            element="Psi",
            block=None,
            outcome=purity.idempotent,
        ),
        PredicateOutcome(
            source=PredicateSource.G2,
            predicate="tr Psi = 1",
            element="Psi",
            block=None,
            outcome=purity.trace_is_one,
        ),
        PredicateOutcome(
            source=PredicateSource.G2,
            predicate=SUMMATION_PREDICATE,
            element="Psi",
            block=None,
            outcome=purity.trace_rounds_nowhere,
            first_failure_index=(
                None if purity.trace_rounds_nowhere else purity.trace_first_inexact_row
            ),
            first_inexact_index=(
                None if purity.trace_rounds_nowhere else purity.trace_first_inexact_row
            ),
        ),
        PredicateOutcome(
            source=PredicateSource.SR1,
            predicate="tr_{A^v} Psi = tau_A",
            element="tau_A",
            block=None,
            outcome=verification.sr1_holds,
        ),
    ]
    # (SR2) IS RECORDED PER SIGNAL LABEL, which is what it is quantified over:
    # "ONE INDEX IS ENOUGH TO REFUSE, the condition being universally
    # quantified over x", and the row asks for the outcome per element.
    recorded.extend(
        PredicateOutcome(
            source=PredicateSource.SR2,
            predicate="tr_A[(M_x (x) 1) Psi] = p_x rho^v_x",
            element=f"x = {label}",
            block=None,
            outcome=holds,
            # THE SIGNAL INDEX, 1-based in the order (SR2) decided the labels
            # in, which is the alphabet it was given -- one of the four indices
            # the row names ("the block, outcome, signal or entry index").
            first_failure_index=None if holds else signal,
        )
        for signal, (label, holds) in enumerate(
            verification.sr2_verdicts().items(), start=1
        )
    )
    return tuple(recorded)


def compile_specification(
    specification: ProtocolSpecification,
    *,
    chain_provenance: ChainProvenance | None = None,
) -> CompilationResult:
    """Compile one specification: Definition ``def:compile`` end to end.

    Returns a :class:`CompilationResult` carrying a declaration or a refusal.

    ``chain_provenance`` is the interface's input row of that name: the run's
    word that the one receiver link is the instance link of a reductions
    artefact emitted in the same run (``req:link-row-provenance``). It is read
    for the presence rule of A-LINK and for nothing else
    (:func:`link_row_discharged`), and it is never read from the
    specification.
    RAISES only for arguments no clause of the inputs table can be read against --
    a specification with no reduction chain, a chain whose last receiver link
    declares no target POVM, or a certificate whose virtual pair diverges from
    the specified pair at ``L_s = 0``, none of which Definition ``def:spec``
    admits.
    """
    chain = specification.chain
    if not isinstance(chain, ReductionChain):
        raise MalformedInputError(
            "the specification carries no reduction chain; Definition def:spec "
            "(c) makes it the third part and it is never absent"
        )
    # def:spec (a)'s typing, before any stage runs: the licensed
    # certificate is written against the pair the artefact emits.
    check_certificate_pair_typing(specification, chain)
    record = chain_record(chain)
    source_admission = _source_segment_admission_refusal(specification, chain)
    if source_admission is not None:
        return _refused(None, record, source_admission)

    # --- THE GENERAL FORMAT TAKES THE OTHER ASSEMBLY, and only the assembly. --
    # def:compile's general paragraph differs from its accepted one in the three
    # stages BELOW the gates -- the conditional families of every receiver part,
    # one chain per measured factor, and the slots -- and in NOTHING ELSE: "at
    # one measured factor, POVM form, two messages and no scoped entry every
    # clause below is the clause of the same subject above, slot for slot, and
    # the map emits what it emits today". So the general path is another
    # assembly and the same :func:`_decide_and_emit`; (G1), (G2), (G3) and the
    # emission are one implementation for both formats, which is what makes
    # the gate outcome table (def:gate-outcome-table) one table.
    if specification.is_general_format:
        return _compile_general(specification, chain, record, chain_provenance)

    # --- Stage 0: the declared conditional families, BEFORE ANY PRODUCT. ----
    # def:weighted decides the exact admissibility of each {N_{u|t}}_u "on the
    # declared numbers, before it forms any product and therefore before the
    # interface conditions on the chain are decided", on either party's side
    # (def:compile), and refuses with `conditional_family_not_admissible`. It
    # is fail-closed ROW 1 and nothing else of the map precedes the chain row.
    # A refusal here carries no chain report: the compilation stopped before
    # the chain stage ran, and a report whose conditions all read `not checked`
    # would claim the obligation had been TRANSFERRED (CompilationResult.chain).
    conditional = decide_every_conditional_family(specification)
    if conditional.refusal is not None:
        return _refused(None, record, conditional.refusal)

    # --- Stage 1: the chain. Its last link IS the emitted receiver data. ----
    # The receiver's physical family is CONSTRUCTED here -- it is a
    # choice-weighted presentation on both instances -- so req:weight-list's
    # decision on its weight list and Definition def:weighted's emission
    # decision bear on it too, and both are taken before (C4) is given
    # anything to compare. The direction is fail-closed: a weight list that is
    # not normalized, or a constructed family off the binary64 lattice, stops
    # the compilation instead of being compared, rounded or snapped (the
    # ``no_snapping`` convention).
    physical_resolution = resolve_povm(specification.receiver.physical_povm)
    if physical_resolution.refusal is not None:
        return _refused(None, record, physical_resolution.refusal)
    # req:physical-family-decision: the presented physical family, decided
    # exactly admissible as one block BEFORE any condition of the chain.
    physical_decision = decide_physical_family(
        specification.receiver,
        physical_resolution.require(),
        specification.receiver.factor_label
        if specification.receiver.factor_label is not None
        else default_factor_label(0),
    )
    if physical_decision.refusal is not None:
        return _refused(None, record, physical_decision.refusal)
    # req:band-a-ideal-receiver: on the Band-A route, the declared-data part
    # of A-IDEAL -- one measured factor, dimension two, a projective family --
    # decided after the family's exact admissibility and before the chain.
    band_a_refusal = decide_band_a_ideal_receiver(specification)
    if band_a_refusal is not None:
        return _refused(None, record, band_a_refusal)
    # req:band-a-identity-link: on the route, the one link supplies its channel
    # as data and gamma is the identity on V = V^ph, so that (C4) below is
    # decided and reads F_v = F^ph_v.
    link_refusal = decide_band_a_identity_link(
        specification, physical_resolution.require().alphabet
    )
    if link_refusal is not None:
        return _refused(None, record, link_refusal)
    context = _chain_context(specification, chain, physical_resolution.require())
    chain_report = check_chain(chain, context)
    if chain_report.refusal is not None:
        return _refused(chain_report, record, chain_report.refusal)

    # --- Stage 2: fill the slots (Definition def:compile). ------------------
    last_link = chain.receiver_segment[-1]
    if last_link.target_alphabet is None or last_link.target_povm is None:
        raise MalformedInputError(
            "the last link of the receiver segment declares no target POVM; "
            "Definition def:spec (c) requires it to carry (Q, S, (d_s)) AND "
            "{F_v}"
        )
    # req:weight-list's decision on Alice's weight list and Definition
    # def:weighted's emission obligation, taken BEFORE anything is emitted and
    # on the one path from a choice record to matrices: "the compiler decides,
    # BEFORE EMITTING ANYTHING, that every entry of every N_{u,t} is a binary64
    # number ... otherwise it refuses ... and emits no declaration". The
    # refusals are `choice_weights_not_normalized` and
    # `emitted_value_not_representable`, and this is the only route by which
    # they reach a caller of this function for Alice's family.
    alice_resolution = resolve_povm(specification.source.alice_povm)
    if alice_resolution.refusal is not None:
        return _refused(chain_report, record, alice_resolution.refusal)
    alice = alice_resolution.require()
    # req:da1-source-identity: (SR2) read at d_A = 1, in trusted-source mode,
    # on the family just resolved (the weighted one where a choice is
    # presented), before anything is emitted.
    identity_refusal = decide_da1_source_identity(specification, dict(alice.elements))
    if identity_refusal is not None:
        return _refused(chain_report, record, identity_refusal)
    # GATE (G2) RE-DECIDES THE FIVE CONDITIONS ON THE EMITTED DATA, and
    # this is where it does it: the transmitter decided them first and
    # emitted the licence record, and a consumer decides and never infers
    # (def:eligible (G2); the `decide_never_infer` convention). The
    # certificate travels inside the licence record for exactly this.
    certificate: SourceReplacementCertificate | None = None
    licence_record = specification.source.artifact.source_replacement_license
    if licence_record is not None:
        certificate = licence_record.certificate
    verification = (
        None
        if certificate is None
        else verify_certificate(
            certificate, alice.alphabet, dict(alice.elements)
        )
    )
    # THE MARGINAL IS THE ARTEFACT'S, PASSED THROUGH UNCHANGED, including
    # the [1] the transmitter filled the slot with at d_A = 1 and recorded
    # as filled. THIS MODULE FILLS NO SLOT (def:compile; thm:gates, proof).
    marginal = specification.source.marginal
    entries = emitted_constraint_list(specification, chain)
    # --- WHAT A NON-EMPTY SOURCE SEGMENT BRINGS, decided in one place. -------
    # def:chaincond's source-segment paragraph is a LIST of conditions this module
    # decides IF such a segment is presented, and each is a function of its own in
    # `chain`, called here: the licensed-only rule below, and
    # `chain.check_source_segment` for (A1)-(A3) where the caller holds the typed
    # links. A FURTHER FAIL-CLOSED CHECK IS A LOCAL ADDITION -- one more call in
    # this block and one more function beside those two.
    #
    # The licensed-only rule is decided HERE, after the concatenation and before
    # anything is emitted, because its subject is the EMITTED CList and not a
    # link's own slot -- and it REFUSES a case the accepted format emits with the
    # flag false, which is why the refusal is taken rather than folded into a gate
    # verdict.
    licensed_only = check_licensed_only(
        entries, source_segment_is_non_empty=bool(chain.source_segment)
    )
    if licensed_only is not None:
        return _refused(chain_report, record, licensed_only)
    public = specification.public

    # ROUTE C, APPLIED HERE AND NOWHERE ELSE: after the chain has been
    # consumed and its interface conditions decided, and BEFORE the
    # validator and the gates read the emitted declaration
    # (def:compile; rem:relabel, "what is applied, and where"). The
    # emitted family is N_(v,f) = P(f | t(v)) F_v over the support, the
    # emitted outcome alphabet IS that support in its product order,
    # and idxm's V component follows from the declaration below.
    #
    # (C3) WAS DECIDED ON THE CHAIN'S FAMILY AND V3 IS DECIDED ON THIS
    # ONE, which is thm:chain-consumption (ii)'s own reading: lem:weighted (i)-(ii)
    # is what says the weighting cannot break what (C3) established,
    # and the identity of conjunct lists is between (C3) and D(iii) on
    # the CHAIN's family.
    bob_alphabet = last_link.target_alphabet
    bob_povm: Mapping[Label, BlockOperator] = last_link.target_povm
    weighting = specification.receiver.choice_weighting
    choice_weightings: tuple[FactorWeighting, ...] = ()
    if weighting is not None:
        weighted = setting_weighted_family(bob_alphabet, bob_povm, weighting)
        if isinstance(weighted, Refusal):
            # choice_weight_not_stochastic, or
            # emitted_value_not_representable on the products: both
            # emit NO declaration (thm:choice-encoding (viii)).
            return _refused(chain_report, record, weighted)
        choice_weightings = (
            FactorWeighting(
                factor=specification.receiver.factor_label
                if specification.receiver.factor_label is not None
                else default_factor_label(0),
                family=weighted,
            ),
        )
        bob_alphabet = weighted.alphabet
        bob_povm = weighted.elements
    declaration = CandidateDeclaration(
        alice_dim=specification.source.alice_dim,
        alice_marginal=marginal,
        sectors=specification.sectors,
        alice_alphabet=alice.alphabet,
        alice_povm=dict(alice.elements),
        bob_alphabet=bob_alphabet,
        bob_povm=dict(bob_povm),
        partition=public.partition,
        announce_alice=public.announce_alice,
        announce_bob=public.announce_bob,
        alice_announcement_alphabet=public.alice_announcement_alphabet,
        bob_announcement_alphabet=public.bob_announcement_alphabet,
        acceptance_alphabet=public.acceptance_alphabet,
        accept_statistic=public.accept_statistic,
        key_map=raw_key_map(public, alice.alphabet, bob_alphabet),
        key_alphabet=public.key_alphabet,
        key_holder=public.holder,
        constraint_list=entries,
        attack_set_license=specification.constraints.attack_set_license,
    )
    declaration = CandidateDeclaration(
        **{**declaration.__dict__, "label_index_map": _index_map(declaration)}
    )

    # --- Stages 3 to 5 ARE ONE IMPLEMENTATION FOR BOTH FORMATS. -------------
    recorded: list[PredicateOutcome] = list(conditional.predicates)
    if physical_resolution.emission is not None:
        recorded.extend(physical_resolution.emission.predicates)
    recorded.extend(physical_decision.predicates)
    recorded.extend(chain_report.predicates)
    if alice_resolution.emission is not None:
        recorded.extend(alice_resolution.emission.predicates)
    return _decide_and_emit(
        specification,
        chain,
        record,
        _Assembled(
            declaration=declaration,
            entries=entries,
            marginal=marginal,
            chain_report=chain_report,
            certificate=certificate,
            verification=verification,
            presentation=None,
            choice_weightings=choice_weightings,
            recorded=tuple(recorded),
        ),
        chain_provenance=chain_provenance,
    )


@dataclass(frozen=True)
class _Assembled:
    """What one assembly of ``def:compile`` produced, before the gates read it.

    THE ONE SEAM BETWEEN THE TWO ASSEMBLIES. The accepted clause of
    ``def:compile`` and its general paragraph fill the same declaration and
    decide the same things before the gates; what differs is HOW the slots are
    filled, so each assembly builds one of these and
    :func:`_decide_and_emit` runs (G1), (G2), (G3) and the emission on it.

    ``recorded`` is the transcript prefix IN THE ORDER THE DECISIONS WERE TAKEN
    -- the conditional families, the receiver's family, the chain, Alice's
    family -- to which the tail appends (G2)'s, route C's and the validator's, in
    that order, exactly as the accepted path always did.
    """

    declaration: CandidateDeclaration
    entries: tuple[ConstraintEntry, ...]
    marginal: Matrix | None
    chain_report: ChainReport
    certificate: SourceReplacementCertificate | None
    verification: CertificateVerification | None
    #: The ensemble presentation (G2) re-decided, where the artefact carries one.
    #: ``None`` for the two declared forms, where :attr:`verification` is what
    #: (G2) reads.
    presentation: PresentationVerification | None
    choice_weightings: tuple[FactorWeighting, ...]
    recorded: tuple[PredicateOutcome, ...]


def _decide_and_emit(
    specification: ProtocolSpecification,
    chain: ReductionChain,
    record: dict[str, object],
    assembled: _Assembled,
    factor_chain: FactorChainReport | None = None,
    chain_provenance: ChainProvenance | None = None,
) -> CompilationResult:
    """Run (G1), (G2), (G3) and the emission on an assembled declaration.

    STAGES 3 TO 5 OF THE MODULE DOCSTRING'S ORDER, for either format. It is one
    function because ``def:eligible`` is one definition and the gate outcome
    table (``def:gate-outcome-table``) is one table: the general format adds no
    row to it, and a second copy of these branches would be a second table to
    keep in step.
    """
    declaration = assembled.declaration
    entries = assembled.entries
    certificate = assembled.certificate
    verification = assembled.verification
    choice_weightings = assembled.choice_weightings
    chain_report = assembled.chain_report
    # --- Stage 3: (G1). -----------------------------------------------------
    validation = validate(declaration, specification.constraints.feasibility_witness)

    # --- Stage 4: (G2), (G3). ----------------------------------------------
    # THE THIRD CASE OF THE STATE AXIS IS THE PRESENTATION'S, and it is a
    # re-decision like the other two. For an ensemble presentation the licence
    # record carries NO certificate -- "(SR1), (SR2), positivity of the blocks,
    # the POVM condition and the purity of the blocks are THEOREMS of the
    # presentation and are decided by nothing" -- so what (G2) re-decides there
    # is "(E1) to (E3) and the entry-for-entry slot identity instead"
    # (def:eligible, the general format), which :func:`verify_presentation`
    # takes. A presentation whose conditions hold is PRESENT_PASSING and one
    # whose conditions fail is PRESENT_FAILING, which is row 3 at every d_A --
    # the same row a failing pure-form certificate lands on, and no row is added.
    if assembled.presentation is not None:
        state = (
            CertificateState.PRESENT_PASSING
            if assembled.presentation.passes
            else CertificateState.PRESENT_FAILING
        )
    elif (
        specification.source.artifact.certificate_form is CertificateForm.BLOCK
        and specification.source.artifact.source_replacement_license is not None
    ):
        # A BLOCK-FORM CERTIFICATE WHOSE LICENCE RECORD IS PRESENT FAILS (G2)
        # BY ITS FORM. def:eligible, (G2) by form of the certificate: "A
        # certificate declared in block form is refused at this gate by its
        # declared form, whatever its blocks, by row 3 of the gate outcome
        # table"; thm:gates Step 5: "the record is present, and the condition
        # of (G2) it fails is that (G2) admits no certificate declared in block
        # form ... so the outcome is a refusal naming the form". The licence
        # carries no Psi (certificate is None), so without this branch the
        # state would read ABSENT and GateInputs would refuse the record as
        # untyped input. resolve_gates names the form in the refusal.
        #
        # THE FORM IS DECIDED ONLY WHERE THE RECORD IS PRESENT, because Step 5
        # argues from that premise. At d_A = 1 the transmitter emits no licence
        # record in any form (transmitter/req:licence-scope; def:eligible (G2):
        # "At d_A = 1 no record is demanded, the licence being vacuous
        # there"), so a block-form artefact there reaches the state axis as
        # ABSENT, exactly as a pure-form one does, and is emitted on the row
        # its dimension and list select.
        state = CertificateState.PRESENT_FAILING
    elif certificate is None:
        state = CertificateState.ABSENT
    else:
        assert verification is not None
        state = (
            CertificateState.PRESENT_PASSING
            if verification.passes
            else CertificateState.PRESENT_FAILING
        )
    inputs = GateInputs(
        validator_passed=validation.passed,
        emitted_mode=specification.source.source_mode,
        alice_dim=specification.source.alice_dim,
        certificate=state,
        has_constraint_entries=bool(entries),
        list_licensed=licensed_for_the_emitted_mode(assembled.marginal, entries),
        license_present=specification.constraints.attack_set_license is not None,
        # (G2) BY FORM OF THE CERTIFICATE, AND (DX4)'s SLOT BESIDE IT. Both are
        # READ OFF THE ARTEFACT AND OFF THE DECLARATION and are never second data:
        # "which form a certificate is in is read off the artefact and is never a
        # second datum, exactly as the mode is" (def:spec (a')), and the Alice slot
        # is the one the declaration carries. The gate's one decision on the pair
        # is that a presentation is admitted only beside an ensemble-form
        # declaration (def:eligible).
        certificate_form=specification.source.artifact.certificate_form,
        alice_form=declaration.alice_form,
    )
    # --- THE PER-PREDICATE TRANSCRIPT, ASSEMBLED FROM THE FOUR DECIDERS -----
    # The ``gate_report`` row's second half (the ``recorded_predicates``
    # enumeration). It is assembled HERE because this function is where all
    # five decided records are in hand, and IN THE ORDER THE DECISIONS WERE
    # TAKEN by the stages above -- the conditional families of both declared
    # presentations, the receiver's choice-weighted family, the chain, Alice's
    # family, gate (G2) on the certificate, route C, the validator -- which is
    # the order the stages run in and not the order the contract lists the
    # sources in. NOTHING IS DECIDED HERE: every outcome below was decided by
    # the record it is read off, and the transcript is passed to
    # :func:`resolve_gates` as a KEYWORD argument that no branch of the gate
    # outcome table reads.
    recorded: list[PredicateOutcome] = list(assembled.recorded)
    if assembled.presentation is not None:
        recorded.extend(assembled.presentation.predicates)
    if verification is not None:
        # THE (G2), (SR1) AND (SR2) ENTRIES CAN STAND BESIDE A GATE LINE THAT
        # READS ``engaged: false``, and that is right rather than a slip
        # At ``d_A = 1`` the gate
        # DEMANDS no certificate (``transmitter/req:licence-scope``) and
        # :func:`resolve_gates` records (G2) as not engaged -- but a
        # certificate SUPPLIED there is still verified, because row 3 is
        # scoped "at any ``d_A``" and "one supplied there and failing is the
        # same defect in the same data". So the conditions were decided, and
        # what is recorded is what was decided; a record that dropped them
        # because the gate line reads not-engaged would hide the five
        # decisions the refusal at row 3 rests on.
        recorded.extend(_certificate_predicates(verification))
    # EVERY weighted factor's decisions, in the factors' order, each keyed to
    # its factor where more than one is presented (the transcript module's
    # factor rule).
    several_factors = len(declaration.measured_factors) > 1
    for applied in choice_weightings:
        recorded.extend(
            scoped_to_factor(applied.family.predicates, applied.factor)
            if several_factors
            else applied.family.predicates
        )
    recorded.extend(validation.predicates)

    failing = validation.failing_checks
    resolution = resolve_gates(
        inputs,
        failing[0] if failing else None,
        transcript=PredicateTranscript(tuple(recorded)),
    )

    # --- Stage 5: emit or refuse. ------------------------------------------
    if resolution.outcome is EmissionOutcome.REFUSAL:
        refusal = resolution.refusal
        assert refusal is not None
        if not validation.passed and validation.first_refusal is not None:
            # Row 1 refuses "naming the check": the reason a caller acts on is
            # the CHECK's, not a second gate-shaped restatement of it.
            refusal = validation.first_refusal
        elif state is CertificateState.PRESENT_FAILING and verification is not None:
            # Row 3 refuses "naming the condition", and the five strings that
            # name them are the transmitter's, reused here rather than spelled
            # a second time (the interface's `fixed_by_this_file`).
            certificate_refusal = verification.refusal()
            if certificate_refusal is not None:
                refusal = refusal_from_transmitter(certificate_refusal)
        elif state is CertificateState.PRESENT_FAILING and (
            assembled.presentation is not None
        ):
            # ROW 3 FOR A FAILING PRESENTATION, AND THE REASON STAYS
            # `gate_g2_failed`. The transmitter's own strings for (E1)-(E3) --
            # `ensemble_presentation_not_admissible`,
            # `formed_entry_not_declarable` -- are NOT members of this module's
            # refusal vocabulary, and adding one would be adding a refusal string
            # to an accepted interface table. So the failing condition travels in
            # the DETAIL, under the reason whose message
            # reads "or, for a certificate declared in another form, a
            # condition of that form". A READING TAKEN WHERE THE TEXT IS SILENT,
            # and it is the conservative one: the outcome is the refusal row 3
            # already provides, not a new one.
            refusal = Refusal(
                reason=refusal.reason,
                detail=(
                    f"{refusal.detail}. The condition that failed, re-decided "
                    "here on the artefact's own declared blocks: "
                    f"{assembled.presentation.detail}"
                ),
            )
        return _refused(
            chain_report,
            record,
            refusal,
            validation=validation,
            gates=resolution,
            certificate=verification,
            factor_chain=factor_chain,
        )

    # THE LICENCE THIS MODULE EMITS IS THE TRANSMITTER'S, PASSED ON after
    # (G2) has re-decided its five conditions on the emitted data. It is
    # rebuilt rather than forwarded so that the verdicts it carries are
    # THIS module's re-decision and not a copy of somebody else's; the
    # attestation and the certificate inside it are the ones supplied, and
    # nothing here asserts (SR3) (transmitter/req:attestation-record).
    # FOR A PRESENTATION IT IS THE PRESENTATION'S RECORD, rebuilt the same way:
    # `pass_through_presentation` is the constructor whose (SR1) and (SR2) are
    # THEOREMS of the presentation rather than verdicts, which is what
    # transmitter/def:srcert says of that form, and this module re-decided
    # (E1)-(E3) and the slot identity above instead.
    licence: SourceReplacementLicense | None = None
    if resolution.emits_source_replacement_license:
        if assembled.presentation is not None:
            licence = SourceReplacementLicense.pass_through_presentation(
                assembled.presentation.presentation,
                assembled.presentation.attestation,
            )
        elif verification is not None:
            licence = SourceReplacementLicense.pass_through(
                verification,
                None if certificate is None else certificate.retention_attestation,
                certificate,
            )
    emitted = CandidateDeclaration(
        **{**declaration.__dict__, "source_replacement_license": licence}
    )
    on_provenance = not band_a_route(specification) and (
        link_row_discharged(specification, chain, chain_provenance)
    )
    ledger = _assumption_ledger(
        specification,
        chain,
        entries,
        bool(resolution.key_length_eligible),
        link_row_on_provenance=on_provenance,
    )
    return CompilationResult(
        declaration=emitted,
        refusal=None,
        key_length_eligible=resolution.key_length_eligible,
        gate_report=resolution.report,
        reduction_chain_record=record,
        validation=validation,
        chain=chain_report,
        gates=resolution,
        certificate=verification,
        source_replacement_license=licence,
        verified_witness=validation.feasibility.witness,
        choice_weightings=choice_weightings,
        factor_chain=factor_chain,
        assumption_ledger=ledger,
        assumption_bindings=_assumption_bindings(specification, chain, entries, ledger),
        link_row_omitted_on_provenance=on_provenance,
    )


# ---------------------------------------------------------------------------
#  THE GENERAL FORMAT'S ASSEMBLY (``def:compile``, the appended paragraph)
# ---------------------------------------------------------------------------
#
#  NO PRODUCT BLOCK AND NO LIFTED OPERATOR IS FORMED BY ANY FUNCTION BELOW.
#  ``def:compile``: "The product sector map, its order, the product alphabet and
#  the joint sectors are DERIVED from that list by (DX1) and (DX3) and are
#  declared, formed and emitted by no one: what is emitted is the factor list and
#  the rules"; "no product of two factors' families is formed by this map,
#  whether emitted or handed on"; "the lifted operator 1 (x) O_k (x) 1 of (DX6)
#  is never formed as a datum either". A Kronecker product is how each of those
#  would be built, so no function of this file calls one --
#  ``tests/unit/test_protocol_general_format.py`` decides that STATICALLY over the
#  package, in the style of the reductions module's declared-kron-sites test, and
#  DYNAMICALLY on the verification path.


@dataclass(frozen=True)
class PresentationVerification:
    """Gate (G2)'s re-decision on an ENSEMBLE PRESENTATION, on the emitted data.

    ``def:eligible``, the general format: for a presentation the gate "decides
    (E1) to (E3) and the entry-for-entry slot identity instead" of the five
    conditions, "and at two or more Alice sectors the five do not hold and global
    purity is not demanded" -- which rests on
    ``transmitter/lem:ensemble-presentation`` (ii) and
    ``transmitter/thm:certificate-sufficiency`` (iii).

    THE TWO LEGS ARE DECIDED AND NOT READ OFF THE SUPPLIER'S RECORD, which is the
    ``decide_never_infer`` convention: (E1)--(E3) by the transmitter's own
    :func:`~certiqs_key.transmitter.presentation.verify_ensemble_presentation` on
    the presentation the licence record carries, and the slot identity by
    comparing the declaration's ``N^{(t)}_x`` with the transpose of the artefact's
    own ``sigma^{v,(t)}_x`` block by block -- ``def:eligible``'s "pins the
    declaration's Alice slots to the transposed declared blocks entry for entry".
    """

    presentation: EnsemblePresentation
    attestation: RetentionAttestation | None
    conditions: EnsemblePresentationVerification
    #: The first ``(letter, sector)`` at which the slot identity fails, or
    #: ``None``. ONE INDEX IS ENOUGH TO REFUSE, the identity being universally
    #: quantified over both.
    slot_failure: tuple[Label, Label] | None
    predicates: tuple[PredicateOutcome, ...]

    @property
    def passes(self) -> bool:
        """Whether (E1)--(E3) and the slot identity all hold."""
        return self.conditions.passes and self.slot_failure is None

    @property
    def detail(self) -> str:
        """Return the failing condition, for the refusal row 3 carries."""
        if self.slot_failure is not None:
            letter, sector = self.slot_failure
            return (
                f"the declaration's N_{letter!r} at Alice sector {sector!r} is "
                "not the transpose of the artefact's declared sigma^v block, so "
                "the gate's entry-for-entry pinning of the Alice slots fails"
            )
        refusal = self.conditions.refusal()
        return "(E1) to (E3) hold" if refusal is None else refusal.detail


def verify_presentation(
    specification: ProtocolSpecification,
    declaration: CandidateDeclaration,
) -> PresentationVerification | None:
    """Re-decide gate (G2) on an ensemble presentation, or return ``None``.

    ``None`` where the artefact declares no presentation, which is every artefact
    of the accepted format: there (G2) reads
    :func:`~certiqs_key.transmitter.certificate.verify_certificate` as it always
    did, and this function decides nothing.

    RAISES for a presentation the artefact carries without the blocks the
    identity is decided against, because that is not a presentation of an input
    this module types and refusing it would have to invent a reason.
    """
    licence = specification.source.artifact.source_replacement_license
    presentation = getattr(licence, "presentation", None)
    if not isinstance(presentation, EnsemblePresentation):
        return None
    alphabet = specification.source.alphabet
    conditions = verify_ensemble_presentation(
        presentation, alphabet, dict(specification.source.signal_weights)
    )
    sectors = specification.source.alice_sectors
    slot_failure: tuple[Label, Label] | None = None
    recorded: list[PredicateOutcome] = [
        PredicateOutcome(
            source=PredicateSource.G2,
            predicate="(E1) to (E3)",
            element="ensemble presentation",
            block=None,
            outcome=conditions.passes,
        )
    ]
    for letter in alphabet:
        declared = declaration.alice_operator(letter)
        weighted = presentation.weighted_blocks[letter]
        for position, sector in enumerate(sectors.labels):
            holds = equal(declared.blocks[position], transpose(weighted[position]))
            recorded.append(
                PredicateOutcome(
                    source=PredicateSource.G2,
                    predicate="N^(t)_x = (sigma^{v,(t)}_x)^T",
                    element=f"x = {letter}",
                    block=sector,
                    outcome=holds,
                )
            )
            if not holds and slot_failure is None:
                slot_failure = (letter, sector)
    return PresentationVerification(
        presentation=presentation,
        attestation=presentation.retention_attestation,
        conditions=conditions,
        slot_failure=slot_failure,
        predicates=tuple(recorded),
    )


def refuse_dense_alice_povm_at_several_sectors(
    specification: ProtocolSpecification,
) -> None:
    """Take the REFUSING READING for a POVM-form artefact with several Alice sectors.

    THE OPEN SEAM PART 1 REPORTED, AND THIS IS THE READING. ``def:compile``'s
    general clause takes Alice's measurement slot "from the artefact IN THE FORM
    THE ARTEFACT DECLARES -- the POVM slot or the ensemble slot of (DX4) --
    likewise passed through", and (DX4) types the POVM slot at several Alice
    sectors as block lists along ``T``. The transmitter's accepted outputs table
    has no per-sector POVM row: ``alice_povm`` is one matrix per letter, the
    direct sum over the sectors. So at ``|T| >= 2`` in POVM form there is no
    declared block list to pass through, and the two available readings are

    * SPLIT the dense matrix into blocks here, which forms a datum nobody
      declared on a basis-order assumption the artefact's table does not state,
      and would make V1's map comparison compare this module's own construction
      against the factor it derived it from; or
    * REFUSE, which is what this function does.

    No accepted claim says otherwise, so the refusing reading is taken and named
    here (the rule for an ambiguity). IT IS A HARD ERROR AND NOT A REFUSAL
    REASON: such an artefact is not a presentation of an input the inputs table
    types -- ``alice_sector_factor``'s row says Alice's sector map arrives "as the
    map Alice's blocks are written against", and there are no blocks -- so no
    clause of ``def:validator`` can be read against it and a reason string for it
    would be invented vocabulary. An ensemble presentation, the form a source
    with several Alice sectors takes, does not reach this guard.
    """
    source = specification.source
    if source.alice_form is AliceForm.ENSEMBLE:
        return
    if source.alice_sectors.count <= 1:
        return
    raise MalformedInputError(
        "the transmitter artefact declares "
        f"{source.alice_sectors.count} Alice sectors in POVM form, and its "
        "`alice_povm` row is ONE MATRIX PER LETTER: there is no declared block "
        "list along T for def:compile to pass through, and this module does not "
        "split a dense matrix into blocks -- that would form a datum nobody "
        "declared, on a basis-order assumption the artefact does not state. THE "
        "REFUSING READING IS TAKEN where the accepted text is silent "
        "(def:compile, Alice's slots; def:declaration (DX4)). An ensemble "
        "presentation, which is the form a source with several Alice sectors "
        "takes, is unaffected"
    )


def assemble_factor_list(
    specification: ProtocolSpecification,
    factor_sectors: Sequence[SectorStructure],
) -> FactorisedSectorMap | Refusal:
    """Return the factor list of (DX1), ASSEMBLED AND NOT DECLARED AS A WHOLE.

    ``def:compile``: "the factor tagged ``A`` is the Alice sector map the
    transmitter artefact declares, where it declares one, and it is the first of
    the list; where the artefact declares none, ``T = {t_0}`` and no ``A`` factor
    is emitted. The factors tagged ``Q`` are the entries of
    ``S_rec`` IN THEIR DECLARED ORDER, each carrying that entry's party label and
    the sector map of the last target descriptor of that entry's receiver
    segment, which ``def:chaincond`` (C1) decides per factor."

    THE ONE BLOCK KIND IS THE KIND THOSE MAPS CARRY and a disagreement between
    two factors is ``sector_map_mismatch`` "naming the first factor at which the
    kind differs". The maps are passed in by the caller because they are the
    CHAIN's -- read off each factor's last target descriptor, which is where (C1)
    puts them -- so this function reads no descriptor of its own and no second
    carrier of a factor's map exists.
    """
    factors: list[SectorFactor] = []
    if specification.source.declares_alice_sectors:
        factors.append(
            SectorFactor(
                party=str(specification.public.partition.alice_system_party),
                sectors=specification.source.alice_sectors,
                system=SystemTag.A,
            )
        )
    parts = specification.receiver_parts
    for position, (part, sectors) in enumerate(
        zip(parts, factor_sectors, strict=True)
    ):
        label = (
            part.factor_label
            if part.factor_label is not None
            else default_factor_label(position)
        )
        factors.append(
            SectorFactor(
                party=str(part.party),
                sectors=sectors,
                system=SystemTag.Q,
                label=label,
            )
        )
    kinds = {factor.sectors.block_kind for factor in factors}
    if len(kinds) > 1:
        first = next(
            position
            for position, factor in enumerate(factors)
            if factor.sectors.block_kind is not factors[0].sectors.block_kind
        )
        return Refusal(
            reason=RefusalReason.SECTOR_MAP_MISMATCH,
            detail=(
                f"factor {first} of the emitted factor list carries block kind "
                f"{factors[first].sectors.block_kind.value!r} where factor 0 "
                f"carries {factors[0].sectors.block_kind.value!r}. THE FACTORS OF "
                "ONE MAP CARRY ONE BLOCK KIND, because the flattened map carries "
                "one, and a product of differently-licensed factors is refused "
                "rather than assigned a kind (def:compile, the factor list; "
                "spec/architecture.md 2.9)"
            ),
        )
    try:
        return FactorisedSectorMap(factors=tuple(factors))
    except MalformedInputError as exc:
        return Refusal(
            reason=RefusalReason.SECTOR_MAP_MISMATCH,
            detail=(
                "the assembled factor list is not a factorised sector map of the "
                f"shared format: {exc}"
            ),
        )


def _compile_general(
    specification: ProtocolSpecification,
    chain: ReductionChain,
    record: dict[str, object],
    chain_provenance: ChainProvenance | None = None,
) -> CompilationResult:
    """Assemble the GENERAL FORMAT and hand it to the gates.

    Definition ``def:compile``'s appended paragraph, clause by clause, and it
    fills the same declaration the accepted clause fills: at one measured factor,
    POVM form, one Alice sector, two messages and no scoped entry every clause
    below is the clause of the same subject in :func:`compile_specification`, so
    :attr:`ProtocolSpecification.is_general_format` sends such a specification the
    other way and nothing this function does can move it.

    THE STAGES ARE THE MODULE DOCSTRING'S, PER FACTOR WHERE THE FACTORS DIFFER:
    the conditional families of EVERY declared presentation first (that rule's
    subject is "either party's side" and the list of parties is the list of
    factors), then each factor's own receiver segment, then the source segment
    once, then the slots, then the shared tail.
    """
    parts = specification.receiver_parts
    # --- Stage 0: the declared conditional families, BEFORE ANY PRODUCT. ----
    conditional = decide_every_conditional_family(specification)
    if conditional.refusal is not None:
        return _refused(None, record, conditional.refusal)
    # def:spec (a')'s typing: Alice's slot must be one of (DX4)'s two forms.
    refuse_dense_alice_povm_at_several_sectors(specification)

    # --- Stage 1: ONE RECEIVER SEGMENT PER MEASURED FACTOR. -----------------
    # "(C1) to (C5) are decided OF EACH SEGMENT SEPARATELY, AND OF NOTHING
    # ACROSS TWO SEGMENTS", and the source segment is decided ONCE below: the
    # segments handed to `check_factor_chains` are therefore source-free views
    # of each factor's own record.
    segments: list[tuple[Label, ReductionChain, ChainContext]] = []
    emissions: list[PredicateOutcome] = []
    factor_families: list[FactorFamily] = []
    factor_sectors: list[SectorStructure] = []
    weightings: list[FactorWeighting] = []
    factor_weightings: list[SettingWeightedFamily | None] = []
    first_physical: DirectPovm | None = None
    # The transcript's factor rule (transcript module docstring): with more
    # than one measured factor, every key of a decision on one factor's data
    # names that factor; at one factor the keys are the accepted format's.
    several_factors = len(parts) > 1
    for position, part in enumerate(parts):
        part_chain = chain if position == 0 else part.chain
        factor_label = (
            part.factor_label
            if part.factor_label is not None
            else default_factor_label(position)
        )
        if not isinstance(part_chain, ReductionChain):
            raise MalformedInputError(
                f"the receiver part of measured factor {position} carries no "
                "receiver segment; def:spec (c') gives one segment per measured "
                "factor and it is never absent"
            )
        physical = resolve_povm(part.physical_povm)
        if physical.refusal is not None:
            return _refused(None, record, physical.refusal)
        if physical.emission is not None:
            emissions.extend(
                scoped_to_factor(physical.emission.predicates, factor_label)
                if several_factors
                else physical.emission.predicates
            )
        # req:physical-family-decision, per measured factor and before any
        # factor's chain conditions are decided (check_factor_chains below).
        physical_decision = decide_physical_family(
            part, physical.require(), factor_label
        )
        emissions.extend(physical_decision.predicates)
        if physical_decision.refusal is not None:
            return _refused(None, record, physical_decision.refusal)
        if position == 0:
            first_physical = physical.require()
        receiver_only = ReductionChain(
            source_segment=(),
            receiver_segment=part_chain.receiver_segment,
            outcome_correspondence=dict(part_chain.outcome_correspondence),
        )
        last = receiver_only.receiver_segment[-1]
        if last.target_alphabet is None or last.target_povm is None:
            raise MalformedInputError(
                f"the last link of measured factor {position}'s receiver segment "
                "declares no target POVM; def:spec (c') requires it to carry "
                "(Q_f, S^f, (d_{f,s_f})) AND {F^f_{v_f}}"
            )
        sectors = last.target_descriptor.sector_map()
        if sectors is None:
            raise MalformedInputError(
                f"the last target descriptor of measured factor {position} "
                "carries no sector map; (C1) reads the factor's own map off it "
                "and this module supplies none for somebody else's map"
            )
        segments.append(
            (
                factor_label,
                receiver_only,
                ChainContext(
                    physical_descriptor=receiver_only.receiver_segment[
                        0
                    ].source_descriptor,
                    physical_alphabet=physical.require().alphabet,
                    physical_povm=dict(physical.require().elements),
                    target_descriptor=last.target_descriptor,
                    emitted_alphabet=last.target_alphabet,
                    emitted_povm=dict(last.target_povm),
                    gamma=dict(receiver_only.outcome_correspondence),
                ),
            )
        )
        # PER FACTOR: the target family of THAT factor's segment, weighted AFTER
        # THAT segment. "Each factor's weighting is applied to its own family and
        # to nothing else; no product of two factors' families is formed by this
        # map."
        alphabet = last.target_alphabet
        members = last.target_povm
        if part.choice_weighting is not None:
            weighted = setting_weighted_family(
                alphabet, members, part.choice_weighting
            )
            if isinstance(weighted, Refusal):
                return _refused(None, record, weighted)
            # AT MOST ONE PER MEASURED FACTOR, any number of factors (the
            # interface's `choice_weighting` presence): each recorded under
            # its factor.
            weightings.append(FactorWeighting(factor=factor_label, family=weighted))
            alphabet = weighted.alphabet
            members = weighted.elements
            factor_weightings.append(weighted)
        else:
            factor_weightings.append(None)
        factor_sectors.append(sectors)
        factor_families.append(
            FactorFamily.of(
                str(part.party),
                alphabet,
                tuple(members[letter] for letter in alphabet),
            )
        )
    # req:band-a-ideal-receiver, once every factor's family has been decided
    # exactly admissible and before any factor's chain conditions.
    band_a_refusal = decide_band_a_ideal_receiver(specification)
    if band_a_refusal is not None:
        return _refused(None, record, band_a_refusal)
    # req:band-a-identity-link, on the one measured factor the route has left
    # (its (C4) is decided by check_factor_chains below).
    if first_physical is not None:
        link_refusal = decide_band_a_identity_link(
            specification, first_physical.alphabet
        )
        if link_refusal is not None:
            return _refused(None, record, link_refusal)
    factor_report = check_factor_chains(segments)
    if len(segments) > 1:
        # The accepted one-factor record stays byte-for-byte unchanged.  In the
        # general format each receiver segment is a separate declared datum;
        # recording only the first would replace the product readout alphabet
        # by one station's local alphabet when the run tier reconstructs it.
        record = {
            "source_segment": chain_record(chain)["source_segment"],
            "receiver_factor_segments": [
                _factor_chain_record(label, local, part, weighting)
                for (label, local, _), part, weighting in zip(
                    segments, parts, factor_weightings, strict=True
                )
            ],
        }
    first_report = factor_report.per_factor[0][1]
    if factor_report.refusal is not None:
        return _refused(first_report, record, factor_report.refusal)

    # --- Stage 1b: WHAT A NON-EMPTY SOURCE SEGMENT BRINGS, decided once. -----
    # (S1)-(S4) by the accepted decider on the presented pair, and (A1)-(A3) by
    # `check_source_segment` on the typed links. The DECLARED SOURCE MODE is also
    # decided here: a source map is licensed only in trusted mode,
    # so a non-empty segment beside `nomarg` is refused before its link
    # conditions are used to assemble anything.
    source_predicates: tuple[PredicateOutcome, ...] = ()
    if chain.source_segment:
        assert first_physical is not None
        source_report = check_chain(
            chain, _chain_context(specification, chain, first_physical)
        )
        source_predicates = source_report.predicates
        if source_report.refusal is not None:
            return _refused(source_report, record, source_report.refusal)

    # --- Stage 2: fill the slots (def:compile, the general format). ----------
    factorisation = assemble_factor_list(specification, factor_sectors)
    if isinstance(factorisation, Refusal):
        return _refused(first_report, record, factorisation)
    family = FactorisedFamily.of(factorisation, factor_families)
    # ALICE'S SLOT IS PASSED THROUGH IN THE FORM THE ARTEFACT DECLARES, and in
    # ENSEMBLE FORM NOTHING IS RESOLVED: the artefact's `alice_povm` row is empty
    # there by construction -- "{M_x} is not declared and is formed by nobody" --
    # so def:weighted's emission decision has no subject on Alice's side and the
    # POVM the ensemble form denotes is formed by no one.
    alice_slot = specification.source.alice_slot
    alice_emission: tuple[PredicateOutcome, ...] = ()
    alice_alphabet = specification.source.alphabet
    alice_elements: Mapping[Label, Matrix] = {}
    if alice_slot is None:
        alice_resolution = resolve_povm(specification.source.alice_povm)
        if alice_resolution.refusal is not None:
            return _refused(first_report, record, alice_resolution.refusal)
        alice = alice_resolution.require()
        alice_alphabet = alice.alphabet
        alice_elements = dict(alice.elements)
        if alice_resolution.emission is not None:
            alice_emission = alice_resolution.emission.predicates
    # req:da1-source-identity, on the POVM form's resolved family or, in
    # ensemble form, on the slot's N_x.
    identity_refusal = decide_da1_source_identity(specification, alice_elements)
    if identity_refusal is not None:
        return _refused(first_report, record, identity_refusal)
    certificate: SourceReplacementCertificate | None = None
    licence_record = specification.source.artifact.source_replacement_license
    if licence_record is not None:
        certificate = licence_record.certificate
    verification = (
        None
        if certificate is None
        else verify_certificate(certificate, alice_alphabet, dict(alice_elements))
    )
    marginal = specification.source.marginal
    marginal_blocks = specification.source.marginal_blocks
    entries = emitted_constraint_list(specification, chain)
    for part in specification.further_receiver_factors:
        part_chain = part.chain
        if isinstance(part_chain, ReductionChain):
            for link in part_chain.receiver_segment:
                entries = (*entries, *link.transported_constraints)
    licensed_only = check_licensed_only(
        entries, source_segment_is_non_empty=bool(chain.source_segment)
    )
    if licensed_only is not None:
        return _refused(first_report, record, licensed_only)
    public = specification.public
    # THE DERIVED PRODUCT MAP AND ALPHABET, formed by nobody as data: the
    # flattened map is labels, dimensions and a block kind, and the alphabet is
    # the factors' letters joined -- both combinatorial (DX1), (DX3).
    product_sectors = family.flattened()
    bob_alphabet = family.alphabet()
    # WEIGHTINGS AT SEVERAL FACTORS ARE EMITTED, one record entry each (the
    # interface's `choice_weighting` is "at most one per factor" and
    # `choice_weighting_record` "one entry per measured factor at which a
    # weighting was applied").
    declaration = CandidateDeclaration(
        alice_dim=specification.source.alice_dim,
        alice_marginal=None if marginal_blocks is not None else marginal,
        sectors=product_sectors,
        alice_alphabet=alice_alphabet,
        alice_povm=dict(alice_elements),
        bob_alphabet=bob_alphabet,
        # THE PER-FACTOR FAMILY IS THE DATUM AND THE PRODUCT IS THE RULE, so the
        # accepted format's one-family slot is EMPTY here: no entry of any F_v is
        # declared, formed, rounded or decided on (DX3), (eq:productfamily).
        bob_povm={},
        partition=public.partition,
        announce_alice=public.announce_alice,
        announce_bob=public.announce_bob,
        alice_announcement_alphabet=public.alice_announcement_alphabet,
        bob_announcement_alphabet=public.bob_announcement_alphabet,
        acceptance_alphabet=public.acceptance_alphabet,
        accept_statistic=public.accept_statistic,
        key_map={},
        key_alphabet=public.key_alphabet,
        key_holder=public.holder,
        constraint_list=entries,
        attack_set_license=specification.constraints.attack_set_license,
        sector_factorisation=factorisation,
        alice_slot=alice_slot,
        alice_marginal_blocks=marginal_blocks,
        bob_factors=family,
        transcript=public.transcript,
        accept_statistic_general=public.accept_statistic_general,
    )
    # THE RAW KEY IS BUILT WITH THE DERIVED ``a`` and never with a declared one:
    # "the joint announcement function a is not a slot: it is the composition
    # eq:transcript of those tables, and r is eq:rdef with THAT a".
    declaration = CandidateDeclaration(
        **{
            **declaration.__dict__,
            "key_map": _general_key_map(public, declaration),
        }
    )
    declaration = CandidateDeclaration(
        **{**declaration.__dict__, "label_index_map": _index_map(declaration)}
    )
    presentation = verify_presentation(specification, declaration)
    recorded: list[PredicateOutcome] = list(conditional.predicates)
    recorded.extend(emissions)
    recorded.extend(factor_report.predicates)
    recorded.extend(source_predicates)
    recorded.extend(alice_emission)
    return _decide_and_emit(
        specification,
        chain,
        record,
        _Assembled(
            declaration=declaration,
            entries=entries,
            marginal=marginal,
            chain_report=first_report,
            certificate=certificate,
            verification=verification,
            presentation=presentation,
            choice_weightings=tuple(weightings),
            recorded=tuple(recorded),
        ),
        factor_chain=factor_report,
        chain_provenance=chain_provenance,
    )


def _general_key_map(
    public: PublicPart,
    declaration: CandidateDeclaration,
) -> dict[tuple[Label, Label], KeyValue]:
    """Return ``r`` of Eq. ``eq:rdef`` with the DERIVED announcement function.

    The same equation :func:`~certiqs_key.protocol_compiler.spec.raw_key_map`
    builds, read through
    :meth:`~certiqs_key.protocol_compiler.declaration.CandidateDeclaration.announcement`
    -- which is one function for both formats, "because (DX5) makes the accepted
    pair the transcript at ``L = 2``". It is here rather than in ``spec`` because
    the transcript's ``a`` is a function of the DECLARATION's tables and
    ``raw_key_map`` is stated on ``S_pub`` alone.
    """
    built: dict[tuple[Label, Label], KeyValue] = {}
    for x, v in declaration.outcome_pairs():
        kappa = declaration.announcement(x, v)
        if public.sifting[kappa] is Sifting.FAIL:
            built[(x, v)] = PERP
        else:
            readout = declaration.partition.readout(public.holder, x, v)
            built[(x, v)] = public.key_rule[(readout, kappa)]
    return built


def _chain_context(
    specification: ProtocolSpecification,
    chain: ReductionChain,
    physical: DirectPovm,
) -> ChainContext:
    """Return the data Definition ``def:chaincond`` is read against.

    Built FROM the specification and the chain, so that no second argument can
    disagree with either. ``gamma`` is the chain's own declared outcome
    correspondence (C2), and the emitted family is the last link's target.

    ``physical`` IS RESOLVED BY THE CALLER AND PASSED IN, so that Definition
    ``def:weighted``'s emission decision on the receiver's choice-weighted
    family is taken where its refusal can become a
    :class:`CompilationResult` rather than inside a helper that has no shape to
    return one in (the ``fail_closed`` convention).
    """
    first_link = chain.receiver_segment[0]
    last_link = chain.receiver_segment[-1]
    # THE ARTEFACT EMITS ONE ENSEMBLE, AND IT FILLS BOTH SLOTS.
    # transmitter/def:source-segment (S3): the virtual pair is "the object
    # a consumer receives", and "at L_s = 0 the pair is the specified
    # one". The two slots of the context are therefore filled from the
    # same record, and at L_s = 0 (S3) reads as the identity it is there.
    # AN ARTEFACT THAT CARRIES THE SPECIFIED PAIR BESIDE THE VIRTUAL ONE
    # would part these two lines; they are kept apart here so that nothing
    # has to be re-threaded then.
    weights = dict(specification.source.signal_weights)
    virtual_weights = dict(specification.source.signal_weights)
    virtual_states = dict(specification.source.signal_states)
    return ChainContext(
        physical_descriptor=first_link.source_descriptor,
        physical_alphabet=physical.alphabet,
        physical_povm=dict(physical.elements),
        target_descriptor=last_link.target_descriptor,
        emitted_alphabet=last_link.target_alphabet or (),
        emitted_povm=dict(last_link.target_povm or {}),
        gamma=dict(chain.outcome_correspondence),
        virtual_descriptor=(
            chain.source_segment[0].source_descriptor if chain.source_segment else None
        ),
        transmitted_descriptor=(
            chain.source_segment[-1].target_descriptor if chain.source_segment else None
        ),
        signal_alphabet=specification.source.alphabet,
        virtual_weights=virtual_weights,
        specified_weights=weights,
        virtual_states=virtual_states,
        specified_states=dict(specification.source.signal_states),
        link_index_sets={
            link.link_id: specification.source.alphabet for link in chain.source_segment
        },
    )
