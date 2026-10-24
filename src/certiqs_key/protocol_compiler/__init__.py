"""``protocol-compiler``: the module that owns the protocol declaration.

It compiles a human-readable protocol description, together with a transmitter
artefact, a receiver POVM and a reduction chain, into the single input object a
fixed-length key-rate engine consumes -- and refuses, fail-closed and with a
named reason, wherever the supplied data do not support one. The claims are
spec/modules/protocol-compiler/claims/ and the machine keys are binding on this
implementation (spec/modules/protocol-compiler/interface.yaml).

WHAT THIS PACKAGE DOES NOT DO, IN THE CLAIMS' OWN WORDS
=======================================================
"It does not compute a key rate, an entropy, or a bound of any kind: everything
GENERATED FROM the declaration -- the single-round protocol channel, the branch
maps, the objective and the key length -- belongs to the consuming key-rate
engine." It does not characterize a receiver, does not establish a squashing
reduction, an attack-set inclusion, or the soundness of any constraint entry,
and does not construct an acceptance set from an honest distribution. It emits
the acceptance ALPHABET and the acceptance-statistic map; the acceptance SET is
not its output.

Four things it may never do, and which no code path here can:

* decide (SR3), the retention attestation -- "no matrix function decides it"
  (``transmitter/thm:certificate-sufficiency`` (i));
* verify the content of an attack-set licence -- "the compiler tests PRESENCE,
  NEVER TRUTH";
* assert the soundness of a reduction link, or that a presented receiver POVM
  is the measurement performed -- both are supplier obligations this module
  NAMES and never discharges (A-LINK, ``reductions/ass:recv``); it omits the
  A-LINK row only where the claims say the obligation is discharged (Band A,
  and the in-run instance link of ``req:link-row-provenance``, whose
  provenance the run passes beside the specification);
* search for a feasible state -- ``rem:nosearch``: deciding ``W != empty`` for
  a general list is a semidefinite feasibility problem, and requiring a witness
  "moves a numerical search out of the compiler and turns D(vii) into a check".

LAYOUT: ONE MODULE PER CLAIM GROUP, PREDICATES BEFORE EMISSION
==============================================================
The seam runs between statements about a CANDIDATE declaration and statements
about an EMITTED one: ``def:validator`` is stated "given a candidate
declaration", ``thm:feasibility`` says in place that "nothing below uses that ``D`` was
emitted", and ``thm:validator-soundness`` applies to candidates.

    reasons                refusal reasons, gate verdicts, condition outcomes,
                           the SEVEN own assumption identifiers and the
                           never-verified set
    spec                   PC1 inputs: ``def:spec`` (a)-(e), with the source
                           part A THIN READER of the transmitter artefact
    declaration            the module-owned declaration object, the label-index
                           map and the twenty-three machine keys
    weights                PC3: ``def:weighted`` in BOTH FORMS, ``lem:weighted``
                           and the refusals of ``thm:choice-encoding`` (viii)
    statistics             PC2 (iv): ``P_D[omega]`` and ``Phi[omega]``
    feasibility            PC5: Eq. ``eq:witness-empty``, the five verification
                           legs and the ``no_feasibility_witness`` refusal
    validation             PC6: THIS MODULE'S OWN V1-V8 and the two
                           reconstructions
    chain                  PC7, PC8: the interface conditions, read against the
                           frozen records of :mod:`certiqs_key.domain.chain`
    docking_reductions     the consumer's own evaluation of those conditions on
                           an emitted reductions artefact
    gates                  PC9: ``def:eligible`` and the gate outcome table as
                           one total function
    transcript             the ``gate_report`` row's per-predicate record: what
                           each decider decided, keyed by
                           (source, element, block)
    compile                PC1: ``def:compile`` and the pipeline

WHAT LIVES IN OTHER PACKAGES
============================
* The SOURCE SIDE. ``certificate.py`` is :mod:`certiqs_key.transmitter`'s: the
  seven labels PC10-PC11 belong to that module, and the
  artefact it emits is what ``def:spec`` (a) reads. This package decides the
  certificate's five conditions ONCE MORE, at gate (G2), on the emitted data.
* The EXACT SUBSTRATE and the BLOCK FORM. ``exact.py`` and ``blocks.py`` are
  :mod:`certiqs_key.foundations`'s, so that no module declares them twice.
* The HARD ERRORS. ``errors.py`` is :mod:`certiqs_key.foundations.errors`;
  ``CertiqsError`` is the one base.
* The WIRE RECORDS of a chain: :mod:`certiqs_key.domain.chain`.
* The BB84 INSTANCE: ``instances/bb84/`` -- data and not claims.

ONE FILE IS DELIBERATELY NOT HERE. The docking adapter that hands an emitted
declaration to the consuming engine lives with the meat core
(:mod:`certiqs_key.meat_core.docking`): it names the engine's own declaration
type.
"""

from __future__ import annotations

from certiqs_key.protocol_compiler.chain import (
    CHAIN_CONDITIONS,
    LINK_STATUS_VOCABULARY,
    ChainContext,
    ChainLink,
    ChainReport,
    LinkStage,
    LinkStatus,
    ReductionChain,
    Side,
    SystemDescriptor,
    band_a_chain,
    check_chain,
    compose_channel,
    identity_channel,
)
from certiqs_key.protocol_compiler.compile import (
    CompilationResult,
    PhysicalFamilyDecision,
    chain_record,
    check_certificate_pair_typing,
    compile_specification,
    decide_every_conditional_family,
    decide_physical_family,
    emitted_constraint_list,
    link_row_discharged,
)
from certiqs_key.protocol_compiler.declaration import (
    COMPILER_ONLY_KEYS,
    CONTRACT_VERSION,
    DECLARATION_SLOT_KEYS,
    INDEXED_ALPHABETS,
    MATHEMATICAL_SPEC_VERSION,
    NOT_OUTPUTS,
    OUTPUT_KEYS,
    CandidateDeclaration,
    LabelIndexMap,
    build_label_index_map,
    realized_readout_classes,
)
from certiqs_key.protocol_compiler.declared_premises import (
    band_a_route,
    decide_band_a_ideal_receiver,
    decide_band_a_identity_link,
    decide_da1_source_identity,
)
from certiqs_key.protocol_compiler.feasibility import (
    DEFAULT_CANDIDATE,
    SUPPLIED_WITNESS,
    WITNESS_UNQUALIFIED,
    FeasibilityCheck,
    WitnessVerification,
    check_feasibility,
    constraint_value,
    default_witness,
    in_feasible_set,
    verify_witness,
)
from certiqs_key.protocol_compiler.gates import (
    GATE_IDS,
    RETIRED_GATE_CASE_IDS,
    CertificateState,
    EmissionOutcome,
    GateCaseId,
    GateEntry,
    GateId,
    GateInputs,
    GateReport,
    GateResolution,
    licensed_for_the_emitted_mode,
    resolve_gates,
)
from certiqs_key.protocol_compiler.provenance import ChainProvenance, FactorProvenance
from certiqs_key.protocol_compiler.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    CERTIFICATE_CONDITION_REASONS,
    CHAIN_REFUSAL_REASONS,
    CHECK_REFUSAL_REASONS,
    INHERITED_KEYS,
    INHERITED_NEVER_VERIFIED_KEYS,
    NEVER_VERIFIED,
    REFUSAL_REASONS_BAND_A_ROUTE,
    REFUSAL_REASONS_CONDITIONAL_FAMILY,
    REFUSAL_REASONS_GENERAL_FORMAT,
    REFUSAL_REASONS_PHYSICAL_FAMILY,
    REFUSAL_REASONS_SETTING_DEPENDENT_WEIGHTING,
    REFUSAL_REASONS_SOURCE_IDENTITY_AT_DA1,
    REFUSAL_REASONS_VERBATIM,
    REFUSAL_REASONS_WEIGHT_LIST,
    AssumptionId,
    ConditionOutcome,
    GateVerdict,
    Refusal,
    RefusalReason,
    SourceMode,
)
from certiqs_key.protocol_compiler.spec import (
    INPUT_KEYS,
    PERP,
    RETIRED_INPUT_KEYS,
    AnnouncementClass,
    DirectPovm,
    KeyValue,
    Party,
    PartyPartition,
    PovmPresentation,
    ProtocolSpecification,
    PublicChoices,
    PublicPart,
    ReceiverPart,
    Sifting,
    SourcePart,
    SpecConstraints,
    default_party_partition,
    derived_holder_key_rule,
    joint_announcement,
    key_rule_side_condition,
    raw_key_map,
)
from certiqs_key.protocol_compiler.statistics import (
    AcceptanceStatistics,
    acceptance_fibres,
    announcement_class_mass,
    joint_distribution,
    phi_distribution,
)
from certiqs_key.protocol_compiler.transcript import (
    EMPTY_TRANSCRIPT,
    SUMMATION_PREDICATE,
    PredicateOutcome,
    PredicateSource,
    PredicateTranscript,
    sector_map_predicates,
)
from certiqs_key.protocol_compiler.validation import (
    CHECK_IDS,
    CHECK_TARGET_CONDITIONS,
    CheckOutcome,
    DecidabilityCounts,
    ValidationResult,
    check_v1,
    check_v2,
    check_v3,
    check_v4,
    check_v5,
    check_v6,
    check_v7,
    check_v8,
    decidability_counts,
    reconstruct_holder_key_rule,
    reconstruct_sifting_predicate,
    validate,
)
from certiqs_key.protocol_compiler.weights import (
    ChoiceWeighting,
    ConditionalFamilyDecision,
    EmissionDecision,
    PovmResolution,
    SettingWeightedFamily,
    WeightedFamily,
    choice_marginal,
    choice_mass,
    conditional_family_order,
    decide_conditional_families,
    decide_emission,
    decide_setting_emission,
    forget_choice,
    is_povm,
    refuse_fixed_fraction,
    refuse_outcome_dependent_weighting,
    resolve_povm,
    setting_weighted_family,
    weighted_family,
)

# THE TWO VERSION CONSTANTS ARE ``declaration``'S AND ARE RE-EXPORTED HERE.
# The module that owns the emitted key list owns the emitted version, and a
# constant in this file would be a cycle: ``as_machine_record`` emits it and
# this file imports ``compile``. What the pin names is written at the
# constants themselves.

__all__ = [
    "ASSUMPTION_MACHINE_KEYS",
    "CERTIFICATE_CONDITION_REASONS",
    "CHAIN_CONDITIONS",
    "CHAIN_REFUSAL_REASONS",
    "CHECK_IDS",
    "CHECK_REFUSAL_REASONS",
    "CHECK_TARGET_CONDITIONS",
    "COMPILER_ONLY_KEYS",
    "CONTRACT_VERSION",
    "DECLARATION_SLOT_KEYS",
    "DEFAULT_CANDIDATE",
    "EMPTY_TRANSCRIPT",
    "GATE_IDS",
    "INDEXED_ALPHABETS",
    "INHERITED_KEYS",
    "INHERITED_NEVER_VERIFIED_KEYS",
    "INPUT_KEYS",
    "LINK_STATUS_VOCABULARY",
    "MATHEMATICAL_SPEC_VERSION",
    "NEVER_VERIFIED",
    "NOT_OUTPUTS",
    "OUTPUT_KEYS",
    "PERP",
    "REFUSAL_REASONS_BAND_A_ROUTE",
    "REFUSAL_REASONS_CONDITIONAL_FAMILY",
    "REFUSAL_REASONS_GENERAL_FORMAT",
    "REFUSAL_REASONS_PHYSICAL_FAMILY",
    "REFUSAL_REASONS_SETTING_DEPENDENT_WEIGHTING",
    "REFUSAL_REASONS_SOURCE_IDENTITY_AT_DA1",
    "REFUSAL_REASONS_VERBATIM",
    "REFUSAL_REASONS_WEIGHT_LIST",
    "RETIRED_GATE_CASE_IDS",
    "RETIRED_INPUT_KEYS",
    "SUMMATION_PREDICATE",
    "SUPPLIED_WITNESS",
    "WITNESS_UNQUALIFIED",
    "AcceptanceStatistics",
    "AnnouncementClass",
    "AssumptionId",
    "CandidateDeclaration",
    "CertificateState",
    "ChainContext",
    "ChainLink",
    "ChainProvenance",
    "ChainReport",
    "CheckOutcome",
    "ChoiceWeighting",
    "CompilationResult",
    "ConditionOutcome",
    "ConditionalFamilyDecision",
    "DecidabilityCounts",
    "DirectPovm",
    "EmissionDecision",
    "EmissionOutcome",
    "FactorProvenance",
    "FeasibilityCheck",
    "GateCaseId",
    "GateEntry",
    "GateId",
    "GateInputs",
    "GateReport",
    "GateResolution",
    "GateVerdict",
    "KeyValue",
    "LabelIndexMap",
    "LinkStage",
    "LinkStatus",
    "Party",
    "PartyPartition",
    "PhysicalFamilyDecision",
    "PovmPresentation",
    "PovmResolution",
    "PredicateOutcome",
    "PredicateSource",
    "PredicateTranscript",
    "ProtocolSpecification",
    "PublicChoices",
    "PublicPart",
    "ReceiverPart",
    "ReductionChain",
    "Refusal",
    "RefusalReason",
    "SettingWeightedFamily",
    "Side",
    "Sifting",
    "SourceMode",
    "SourcePart",
    "SpecConstraints",
    "SystemDescriptor",
    "ValidationResult",
    "WeightedFamily",
    "WitnessVerification",
    "acceptance_fibres",
    "announcement_class_mass",
    "band_a_chain",
    "band_a_route",
    "build_label_index_map",
    "chain_record",
    "check_certificate_pair_typing",
    "check_chain",
    "check_feasibility",
    "check_v1",
    "check_v2",
    "check_v3",
    "check_v4",
    "check_v5",
    "check_v6",
    "check_v7",
    "check_v8",
    "choice_marginal",
    "choice_mass",
    "compile_specification",
    "compose_channel",
    "conditional_family_order",
    "constraint_value",
    "decidability_counts",
    "decide_band_a_ideal_receiver",
    "decide_band_a_identity_link",
    "decide_conditional_families",
    "decide_da1_source_identity",
    "decide_emission",
    "decide_every_conditional_family",
    "decide_physical_family",
    "decide_setting_emission",
    "default_party_partition",
    "default_witness",
    "derived_holder_key_rule",
    "emitted_constraint_list",
    "forget_choice",
    "identity_channel",
    "in_feasible_set",
    "is_povm",
    "joint_announcement",
    "joint_distribution",
    "key_rule_side_condition",
    "licensed_for_the_emitted_mode",
    "link_row_discharged",
    "phi_distribution",
    "raw_key_map",
    "realized_readout_classes",
    "reconstruct_holder_key_rule",
    "reconstruct_sifting_predicate",
    "refuse_fixed_fraction",
    "refuse_outcome_dependent_weighting",
    "resolve_gates",
    "resolve_povm",
    "sector_map_predicates",
    "setting_weighted_family",
    "validate",
    "verify_witness",
    "weighted_family",
]
