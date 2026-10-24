"""``receiver``: the module that owns the physical measurement model.

Implements the contract of ``spec/modules/receiver``, whose interface is
``spec/modules/receiver/interface.yaml``. The module turns a declared receiver
-- a Gram family, an instrument matrix, or a graph of standard optical
components -- into the click-pattern POVM it performs, its photon-number
blocks, its dark-count channel and the high-photon multiclick bounds -- one
per probe setting, with their minimum -- a weight-preserving squasher consumes;
and it refuses, fail-closed and with a named reason, wherever the declared data
do not support one.

WHAT THIS PACKAGE DOES NOT DO
=============================
It emits no squashed POVM, no flag space, no cutoff-truncated "squashing" of
any kind, no sector decomposition of a system and no constraint list
(``interface.yaml`` ``not_emitted``). The emitted photon-number blocks are a
decomposition of the physical POVM and never a squashing argument (Remark
``rem:blockmeaning``; ``not_emitted_note``): spec/architecture.md section 3.2
gives this module the physical measurement model and not its downstream
security proof, which is ``reductions``'s.

Four more things no code path here can do:

* verify what an assumption about the physical receiver or the run says
  beyond its clauses on the declared data, or ``ass:eig``, a statement about
  the arithmetic: each of them carries ``verification: never``
  (spec/claim-format.md section 3.2; Remark ``rem:unchecked-assumptions``)
  and is a member of ``never_verified_set``. The emitted
  ``calibration_coverage`` records A-TRUST as a statement, never as a
  verdict;
* assume one optical mode per detector. Every block, bound and conditioned
  quantity is computed for arbitrary ``{A_k}``; the rank-one criterion of
  Theorem ``thm:representation-independence`` (iv) is REPORTED and never
  consumed (Remark ``rem:rankone``, Requirement ``req:one-mode-per-port``);
* produce a ``certified`` label. Requirement ``req:evaluation-label`` and
  Theorem ``thm:exact-and-evaluated`` (iii): no path in this module produces
  a label stronger than the floating-point one, and every artifact carries
  ``bound_evaluation: floating_point``;
* multiply by a ``q_t``. The module emits the CONDITIONAL family
  ``{M_{v|t}}`` of a setting family (Definition ``def:setting-family`` (a)),
  complete for each fixed ``t``, and the weights that turn it into a joint
  family belong to the protocol declaration (Definition ``def:probe``).

LAYOUT: ONE MODULE PER CLAIM GROUP, THE CANONICAL OBJECT FIRST
==============================================================
The contract's own seam runs between the CANONICAL OBJECT -- the port Gram
family, on which the three input routes converge (``interface.yaml``
``input_routes.convergence``) -- and the request-to-artifact machine that
validates a request and emits or refuses.

    errors        hard errors -- and the rule that A REFUSAL IS NOT ONE
    reasons       refusal reasons, the assumption IDs, the never-verified set
    numerics      THE NUMERIC SUBSTRATE, decided at this one named site, with
                  the declared tolerances and the residual norm
    modes         Def. def:modes, Def. def:instrument, and the two mode orders
    catalogue     component-catalogue/def:catalogue-entries C1-C10, their
                  domains and their lossless verdicts (thm:catalogue-admissibility)
    graph         Def. def:graph (E1)-(E3), the linear extensions, Def.
                  def:compile and Thm. thm:compilation-well-defined
    grams         Thm. thm:port-grams and thm:representation-independence:
                  Eq. eq:gramdef, the deficiency, the dilation
    fock          Def. def:fock and lem:fock-functor: the photon-number sectors
    povm          Thm. thm:click-povm: the no-click family and the blocks
    coarse        Thm. thm:coarse-graining: the declared coarse-graining onto
                  the emitted alphabet
    efficiency    detector-imperfections/thm:efficiency: layer L1, Eq.
                  eq:etagram, and the composition record
    dark          detector-imperfections/thm:dark-counts: Def. def:darkadm,
                  Eq. eq:darkR, and the r_min trap
    settings      Def. def:probe and req:probe-diagonal-admission: the
                  settings axis, and THE ONE SEAM to the removable
                  probe-conditioning submodule, whose code (``probe``) no
                  module here imports
    bound         Thm. thm:multiclick-bound and thm:emitted-bound: Eq.
                  eq:beta, the two branches, and Def. def:pmc
    residuals     Def. def:residuals: the residuals and their declared
                  tolerances
    enclosure     Def. def:complex-enclosure and Lem. lem:enclosure-arithmetic:
                  complex enclosures in exact rational arithmetic, and the
                  square-root and angle enclosures
    radicals      the exact arithmetic of Req. req:exact-route-decision (ii):
                  Q(i) adjoined square roots, over a coprime base
    generic       THE CONSTRUCTION, GENERIC OVER THE NUMBER TYPE: catalogue
                  entries, compilation, port Grams, permanents, inclusion and
                  exclusion, conditioning and dark composition, in binary64,
                  in enclosures or exactly
    reference     Req. req:exact-route-decision and detector-imperfections/
                  req:dark-composed-reference: the exact-route decision and the
                  dark-composed reference offered for a snap
    snapfix       detector-imperfections/req:snap-fix: the fix a
                  receiver block resting on its snap records
    validation    the cross-cutting input rules of the inputs and parameters
                  tables (``interface.yaml`` ``inputs``, ``parameters``)

    request       ``interface.yaml`` ``inputs``: the input keys and their
                  validator
    artifact      ``interface.yaml`` ``outputs``: the fifteen output keys and
                  their wire form
    construct     the request-to-artifact machine, and the fail-closed tier

Every name below is re-exported from those modules; nothing here computes.
"""

from __future__ import annotations

from certiqs_key.receiver.artifact import (
    BOUND_EVALUATION,
    COMPOSITION_RULE,
    MATHEMATICAL_SPEC_VERSION,
    OUTPUT_KEYS,
    AssumptionRecord,
    BlockDimension,
    BoundQuantifierDomain,
    DarkCountRecord,
    EmittedBlocks,
    HighPhotonBounds,
    InputModeSpace,
    OutcomeAlphabet,
    ReceiverConstruction,
    ReceiverMeasurementArtifact,
    ResidualGap,
    SlotEntry,
    ValidationResults,
)
from certiqs_key.receiver.bound import (
    BoundData,
    Branch,
    ExactWindowRecord,
    SettingBound,
    StrengtheningSlot,
    bound_data_from_family,
    bound_function,
    check_bound_data,
    check_bound_data_admissible,
    collapse_slack,
    emitted_weight,
    emitted_weights,
    exact_block_bound,
    exact_composite,
    exact_window_values,
    multiclick_eigenvalue,
    residual_gap,
    setting_bound,
    tail_value,
    underline_beta,
    window_floor,
    window_indices,
    window_minimum,
)
from certiqs_key.receiver.catalogue import (
    CATALOGUE_IDS,
    Beamsplitter,
    Component,
    GenericBlock,
    Loss,
    Mirror,
    ModeRouting,
    PhaseShifter,
    Polarizer,
    PolarizingBeamsplitter,
    Retarder,
    Rotator,
    beamsplitter_core,
    decibel_to_transmittance,
    rotation,
    splitting_ratio_presentation,
)
from certiqs_key.receiver.coarse import (
    CoarseGraining,
    check_coarse_graining,
    coarse_block,
    coarse_blocks,
    fibre_bound,
)
from certiqs_key.receiver.construct import (
    ReceiverEmission,
    construct_receiver,
    resolve_assurance,
)
from certiqs_key.receiver.dark import (
    DarkCountChannel,
    DarkCountRoute,
    capped_coefficient,
    check_dark_channel,
    check_dark_count_source,
    compose_blocks,
    composed_slack,
    composition_correction,
    improved_bound,
    improves_on_weight,
    minimum_multiclick_mass,
    multiclick_mass,
    overstatement,
    product_form,
)
from certiqs_key.receiver.efficiency import (
    EfficiencyNormalization,
    EfficiencyRecord,
    EfficiencyRow,
    NormalizationReason,
    NormalizedPort,
    apply_uniform_efficiency,
    detector_layer_matrix,
    efficiency_record,
    is_multiple_of_a_sigma,
    nonuniform_effective_gram,
    normalize_efficiencies,
    weighted_total,
)
from certiqs_key.receiver.errors import (
    HypothesisError,
    MalformedInputError,
    ReceiverError,
)
from certiqs_key.receiver.fock import (
    block_dimension,
    block_spectrum_from_eigenvalues,
    fock_block,
    occupation_vectors,
    symmetrizer,
)
from certiqs_key.receiver.grams import (
    DeficiencyIdentity,
    ExtinctionVerdict,
    GramFamily,
    check_gram_family_admissible,
    check_rank_against_port_sizes,
    deficiency_identity,
    extinction_criterion,
    one_mode_per_port,
    port_grams,
    realizing_instrument,
    restrict_to_inputs,
    unitary_dilation,
)
from certiqs_key.receiver.graph import (
    Element,
    ElementGraph,
    check_element_graph,
    compile_element_graph,
    embed,
    linear_extensions,
    topological_order,
)
from certiqs_key.receiver.modes import (
    InputModes,
    Mode,
    ModeSpace,
    Polarization,
    PortMap,
    check_input_modes,
    check_mode_space,
    check_port_map,
    mode_space_order,
)
from certiqs_key.receiver.numerics import (
    RESIDUAL_NORM,
    TOLERANCE_DOMAIN,
    TOLERANCE_KEYS,
    TOLERANCE_KEYS_ALL,
    TOLERANCE_KEYS_CONDITIONAL,
    Angle,
    Matrix,
    NumericalTolerances,
    PiMultiple,
    Scalar,
    epsilon_rank,
    hermiticity_positivity_defect,
    tolerance_is_in_declared_domain,
    tolerances_from_declaration,
)
from certiqs_key.receiver.povm import (
    NoClickFamily,
    coarse_elements,
    completeness_defect,
    element_block,
    emitted_photon_blocks,
    multiclick_block,
    multiclick_patterns,
    no_click_block,
    raw_alphabet,
    single_click_block,
    single_click_patterns,
    subset_sum_blocks,
    unconditioned_family,
)
from certiqs_key.receiver.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    CALIBRATION_COVERAGE_STATEMENT,
    NEVER_VERIFIED,
    REASON_VOCABULARY,
    REFUSAL_REASONS_VERBATIM,
    AssumptionId,
    Refusal,
    RefusalReason,
)
from certiqs_key.receiver.reference import (
    ExactRouteCause,
    ExactRouteDecision,
    OfferedBlock,
    ReferenceCause,
    SettingReference,
    dark_composed_reference,
    enclose_port_grams,
)
from certiqs_key.receiver.request import (
    Assurance,
    DetectorPort,
    InputRoute,
    ReceiverRequest,
    ValidatedRequest,
    factored_loss,
    normalized_station,
    validate_request,
)
from certiqs_key.receiver.residuals import (
    Residual,
    block_positivity_residual,
    check_residuals,
    evaluate_residuals,
    window_consistency_residual,
)
from certiqs_key.receiver.settings import (
    OFF_SETTING,
    ProbeDeclaration,
    ProbeSetting,
    check_probe_declaration,
    predicate_x_holds,
)
from certiqs_key.receiver.snapfix import (
    SnapFixContext,
    receiver_fix,
    receiver_fixes,
    snap_fix_context,
)
from certiqs_key.receiver.validation import (
    ROUTE_KEYS,
    check_exact_window,
    check_exactly_one_route,
    check_parameter_tolerances,
    check_photon_cutoff,
    check_tail_window,
)

__all__ = [
    "ASSUMPTION_MACHINE_KEYS",
    "BOUND_EVALUATION",
    "CALIBRATION_COVERAGE_STATEMENT",
    "CATALOGUE_IDS",
    "COMPOSITION_RULE",
    "MATHEMATICAL_SPEC_VERSION",
    "NEVER_VERIFIED",
    "OFF_SETTING",
    "OUTPUT_KEYS",
    "REASON_VOCABULARY",
    "REFUSAL_REASONS_VERBATIM",
    "RESIDUAL_NORM",
    "ROUTE_KEYS",
    "TOLERANCE_DOMAIN",
    "TOLERANCE_KEYS",
    "TOLERANCE_KEYS_ALL",
    "TOLERANCE_KEYS_CONDITIONAL",
    "Angle",
    "AssumptionId",
    "AssumptionRecord",
    "Assurance",
    "Beamsplitter",
    "BlockDimension",
    "BoundData",
    "BoundQuantifierDomain",
    "Branch",
    "CoarseGraining",
    "Component",
    "DarkCountChannel",
    "DarkCountRecord",
    "DarkCountRoute",
    "DeficiencyIdentity",
    "DetectorPort",
    "EfficiencyNormalization",
    "EfficiencyRecord",
    "EfficiencyRow",
    "Element",
    "ElementGraph",
    "EmittedBlocks",
    "ExactRouteCause",
    "ExactRouteDecision",
    "ExactWindowRecord",
    "ExtinctionVerdict",
    "GenericBlock",
    "GramFamily",
    "HighPhotonBounds",
    "HypothesisError",
    "InputModeSpace",
    "InputModes",
    "InputRoute",
    "Loss",
    "MalformedInputError",
    "Matrix",
    "Mirror",
    "Mode",
    "ModeRouting",
    "ModeSpace",
    "NoClickFamily",
    "NormalizationReason",
    "NormalizedPort",
    "NumericalTolerances",
    "OfferedBlock",
    "OutcomeAlphabet",
    "PhaseShifter",
    "PiMultiple",
    "Polarization",
    "Polarizer",
    "PolarizingBeamsplitter",
    "PortMap",
    "ProbeDeclaration",
    "ProbeSetting",
    "ReceiverConstruction",
    "ReceiverEmission",
    "ReceiverError",
    "ReceiverMeasurementArtifact",
    "ReceiverRequest",
    "ReferenceCause",
    "Refusal",
    "RefusalReason",
    "Residual",
    "ResidualGap",
    "Retarder",
    "Rotator",
    "Scalar",
    "SettingBound",
    "SettingReference",
    "SlotEntry",
    "SnapFixContext",
    "StrengtheningSlot",
    "ValidatedRequest",
    "ValidationResults",
    "apply_uniform_efficiency",
    "beamsplitter_core",
    "block_dimension",
    "block_positivity_residual",
    "block_spectrum_from_eigenvalues",
    "bound_data_from_family",
    "bound_function",
    "capped_coefficient",
    "check_bound_data",
    "check_bound_data_admissible",
    "check_coarse_graining",
    "check_dark_channel",
    "check_dark_count_source",
    "check_element_graph",
    "check_exact_window",
    "check_exactly_one_route",
    "check_gram_family_admissible",
    "check_input_modes",
    "check_mode_space",
    "check_parameter_tolerances",
    "check_photon_cutoff",
    "check_port_map",
    "check_probe_declaration",
    "check_rank_against_port_sizes",
    "check_residuals",
    "check_tail_window",
    "coarse_block",
    "coarse_blocks",
    "coarse_elements",
    "collapse_slack",
    "compile_element_graph",
    "completeness_defect",
    "compose_blocks",
    "composed_slack",
    "composition_correction",
    "construct_receiver",
    "dark_composed_reference",
    "decibel_to_transmittance",
    "deficiency_identity",
    "detector_layer_matrix",
    "efficiency_record",
    "element_block",
    "embed",
    "emitted_photon_blocks",
    "emitted_weight",
    "emitted_weights",
    "enclose_port_grams",
    "epsilon_rank",
    "evaluate_residuals",
    "exact_block_bound",
    "exact_composite",
    "exact_window_values",
    "extinction_criterion",
    "factored_loss",
    "fibre_bound",
    "fock_block",
    "hermiticity_positivity_defect",
    "improved_bound",
    "improves_on_weight",
    "is_multiple_of_a_sigma",
    "linear_extensions",
    "minimum_multiclick_mass",
    "mode_space_order",
    "multiclick_block",
    "multiclick_eigenvalue",
    "multiclick_mass",
    "multiclick_patterns",
    "no_click_block",
    "nonuniform_effective_gram",
    "normalize_efficiencies",
    "normalized_station",
    "occupation_vectors",
    "one_mode_per_port",
    "overstatement",
    "port_grams",
    "predicate_x_holds",
    "product_form",
    "raw_alphabet",
    "realizing_instrument",
    "receiver_fix",
    "receiver_fixes",
    "residual_gap",
    "resolve_assurance",
    "restrict_to_inputs",
    "rotation",
    "setting_bound",
    "single_click_block",
    "single_click_patterns",
    "snap_fix_context",
    "splitting_ratio_presentation",
    "subset_sum_blocks",
    "symmetrizer",
    "tail_value",
    "tolerance_is_in_declared_domain",
    "tolerances_from_declaration",
    "topological_order",
    "unconditioned_family",
    "underline_beta",
    "unitary_dilation",
    "validate_request",
    "weighted_total",
    "window_consistency_residual",
    "window_floor",
    "window_indices",
    "window_minimum",
]
