"""The machine vocabulary of this module: refusal reasons and assumption keys.

NINE STRINGS ARE THE CONTRACT'S, AND THE REST ARE THIS MODULE'S
===============================================================
The refusal rules (``interface.yaml`` ``refusals``) gather the rules the
contract states TOGETHER WITH THE REASON STRING EACH EMITS, nine rows, and
they are transcribed here character for character in the table's own order
(:data:`REFUSAL_REASONS_VERBATIM`):

    dark_count_channel_declared_twice                  req:dark-route-exclusive
    splitting_ratio_presentation_unsupported           the parameters table
    port_gram_rank_exceeds_port_size                   def:tolmap (ii)
    photon_block_positivity_residual_above_tolerance   def:residuals, prop:res5
    tolerance_outside_declared_domain                  rem:tolerancedomain
    exact_window_declared_without_required_tolerance   req:exact-window-declaration
    exact_window_depth_outside_declared_range          req:exact-window-declaration
    window_eigenvalue_consistency_residual_above_tolerance
                                                       def:residuals Eq. res6
    efficiency_normalization_out_of_range              detector-imperfections/
                                                       req:efficiency-normalization

THE TIER-FALLBACK STRING IS NOT IN THIS VOCABULARY.
``receiver_grams_not_enclosed`` would not be a refusal -- an artifact would be
emitted, at a lower tier -- and Requirement ``req:evaluation-label`` says it is
never produced (``refusals.tier_fallback``). IT IS NOT A MEMBER OF
:class:`RefusalReason`. The ``certified`` rung it would answer a request down
from is dropped by PRINCIPLES.md section 10, so no request can name that tier
and no path of this module could emit the string.
:data:`REASON_VOCABULARY` is the NINE: it is what this module can emit of the
spellings the contract fixes, which is the whole of the refusal table and
nothing else. An implementation that emitted a tenth string under one of these
nine conditions, or reused one of the nine for a condition the table does
not name, would be reporting something the contract does not state.

THE RETIRED SPELLING IS KEPT where the frozen record belongs, and nowhere
else: the frozen ``TIER_FALLBACK_REASON_VERBATIM`` and
``REASON_VOCABULARY_0_3_0`` of tests/oracles/registry_receiver_povm.py, beside
which the hand-edited ``REASON_VOCABULARY_RECEIVER_0_1_2`` records what this
repository's module carries, and spec/modules/receiver/interface.yaml, whose
``refusals.tier_fallback`` row stays because the frozen registry's reason
vocabulary lists it and its test reads the row.

THE ONE REFUSAL THE CONTRACT DELIBERATELY LEAVES UNSPELLED
==========================================================
Requirement ``req:tolerance-tests``: bound data failing item (iv) of
Definition ``def:tolmap`` are a failed validation, so ``fail_closed`` APPLIES
AT THIS SITE: NO ARTIFACT IS EMITTED. And it adds NO reason string: the reason
string is THE IMPLEMENTER'S TO NAME, under the rule the refusal rules state
for the validations they do not tabulate, NONE OF THE TABULATED STRINGS
COVERING THIS CHECK; its lead-in gives the reason the contract adds none --
fixing a contract-verbatim key here would settle an interface detail that no
claim of the contract consumes (``refusals.named_without_a_spelling``). So
:attr:`RefusalReason.BOUND_DATA_NOT_ADMISSIBLE` STAYS THIS MODULE'S SPELLING
and is not promoted into :data:`REFUSAL_REASONS_VERBATIM`. The behaviour it
carries is contract text: item (iv) DECIDES ``c`` alone, and the band
``c in [-eps_1, -eps_2)`` that item (v)'s test would admit is REFUSED.

THE SPELLING TRAP. The refusal rules say that every validation their table
does not spell refuses under the ``fail_closed`` convention at the site that
states it, WITH A REASON STRING THE IMPLEMENTER NAMES
(``refusals.named_without_a_spelling_note``), and list the sites the contract
names -- two input routes supplied at once, a violated (E1)/(E2)/(E3), a
non-zero ``tolerance`` field, a missing or too-small ``m_t``, a missing
declared tolerance, a probe state outside the Gaussian tier, and bound data
failing item (iv). Those, and every further validation the interface states,
keep this module's own spellings.

THE SCHEME FOR THE UNSPELLED ONES: one rule and no exceptions. A reason names
the contract's own identifier for the failing check, in lower case, with a
prefix naming the object the check is about -- ``graph_condition_e1_failed``,
``dark_condition_d2_failed``, ``residual_r3_above_tolerance``,
``tail_window_missing``. Nothing is abbreviated and nothing is invented beyond
the prefix, so a reader can go from the string to the clause of the contract
without a table. Where the contract supplies a verbatim key for a condition
this module refuses, THE VERBATIM KEY WINS: ``r_5``'s reason is the
contract's own ``photon_block_positivity_residual_above_tolerance``, and no
``residual_r5_above_tolerance`` is spelled. There is no declared margin among
the inputs (Remark ``rem:pmc-branch-choice``), so no reason names one.

TWO REASON PHRASES ARE PROSE, NOT MACHINE KEYS
==============================================
The contract writes two reasons in its own quotation marks rather than as
declared keys: "parameter uncertainty sets are out of scope"
(``interface.yaml`` ``parameters.exactness``, whose ``reason_string_note``
says it is prose) and the ``calibration_coverage`` statement
(``outputs.calibration_coverage``). They are carried as prose in
:data:`PROSE_REASONS` and in the ``detail`` field of the refusals that quote
them; they are NOT :class:`RefusalReason` members, because promoting a
sentence to a machine key would invent a spelling the contract did not fix.

A REFUSAL IS A RECORD AND NEVER AN EXCEPTION
============================================
The ``fail_closed`` convention: "every failed validation produces a refusal
with a machine-readable reason and no artifact". :class:`Refusal` is that
record. The exceptions of :mod:`certiqs_key.receiver.errors` are for arguments
no clause can be read against, which is a different thing and must stay
distinguishable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from certiqs_key.domain.claim_closure import never_verified

__all__ = [
    "ASSUMPTION_MACHINE_KEYS",
    "CALIBRATION_COVERAGE_STATEMENT",
    "CONDITIONALLY_INVOKED",
    "DARK_CONDITION_REASONS",
    "GRAPH_CONDITION_REASONS",
    "NEVER_VERIFIED",
    "PROSE_REASONS",
    "REASON_VOCABULARY",
    "REFUSAL_REASONS_ADDED_AT_0_3_0",
    "REFUSAL_REASONS_ADDED_AT_0_7_0",
    "REFUSAL_REASONS_VERBATIM",
    "RESIDUAL_REASONS",
    "AssumptionId",
    "Refusal",
    "RefusalReason",
]


class RefusalReason(StrEnum):
    """Every machine-readable reason this module can emit.

    NINE are contract-verbatim -- the refusals of ``interface.yaml``
    ``refusals`` -- and every other is this module's spelling of the
    contract's naming obligation, under the one rule the module docstring
    states. The tier-fallback string `receiver_grams_not_enclosed`, which the
    refusal rules carry beside the nine as never produced, is not a member
    here (see the module docstring).
    """

    # --- the refusal rules: the nine the contract SPELLS -------------------
    #: The refusal rules, row 1; the inputs table `dark_count_channel`;
    #: Req. req:dark-route-exclusive; Rem. rem:corrdark. A REFUSAL, not a
    #: precedence rule and not a consistency check.
    DARK_COUNT_CHANNEL_DECLARED_TWICE = "dark_count_channel_declared_twice"
    #: The refusal rules, row 2; the parameters table, `units`. The
    #: presentation is REFUSED, not converted, and the transmittance x of
    #: Eq. eq:bs is declared directly.
    SPLITTING_RATIO_PRESENTATION_UNSUPPORTED = (
        "splitting_ratio_presentation_unsupported"
    )
    #: The refusal rules, row 3; Def. def:tolmap (ii), Eq. eq:eps2rank. Route (i)
    #: only: rk_{eps_2}(A_k) > |P_k| for some k.
    PORT_GRAM_RANK_EXCEEDS_PORT_SIZE = "port_gram_rank_exceeds_port_size"
    #: The refusal rules, row 4; Def. def:residuals Eq. eq:res5; Prop. prop:res5.
    #: REFUSE-ONLY: no block is repaired, Hermitized or projected.
    PHOTON_BLOCK_POSITIVITY_RESIDUAL_ABOVE_TOLERANCE = (
        "photon_block_positivity_residual_above_tolerance"
    )
    #: The refusal rules, row 5; the inputs table `numerical_tolerances`;
    #: Rem. rem:tolerancedomain. A declared tolerance outside [0, 1).
    TOLERANCE_OUTSIDE_DECLARED_DOMAIN = "tolerance_outside_declared_domain"
    #: The refusal rules, row 6; the inputs table `exact_window` and
    #: `numerical_tolerances`; Req. req:exact-window-declaration. ONE STRING COVERS
    #: BOTH OMISSIONS, the condition column reading "An `exact_window` depth is
    #: declared and eps_eig or eps_6 is not". The requirement is scoped to the
    #: DECLARATION and not to the setting: declaring a depth at ANY setting
    #: requires eps_eig and eps_6.
    EXACT_WINDOW_DECLARED_WITHOUT_REQUIRED_TOLERANCE = (
        "exact_window_declared_without_required_tolerance"
    )
    #: The refusal rules, row 7; the inputs table `exact_window`;
    #: Req. req:exact-window-declaration. TWO CONDITIONS UNDER ONE STRING, and
    #: the second applies ONLY where predicate (X) fails: "a depth violating
    #: m*_t > N, or violating m*_t <= m_t at a setting where (X) fails, is
    #: refused" (`exact_window.domain_detail`). Both are kind (a) of
    #: Def. def:tolmap's closing enumeration -- a comparison of declared data
    #: against a declared domain -- so NO TOLERANCE DECIDES EITHER.
    EXACT_WINDOW_DEPTH_OUTSIDE_DECLARED_RANGE = (
        "exact_window_depth_outside_declared_range"
    )
    #: The refusal rules, row 8; Def. def:residuals Eq. eq:res6;
    #: Rem. rem:exacteig; Req. req:residual-refusal. REFUSE-ONLY, like r_5: "it
    #: refuses and repairs nothing". And it is ONE-SIDED, which
    #: Rem. rem:exacteig states: r_6 fires when beta-hat* lands too LOW, while
    #: Ass. ass:eig constrains it from landing too HIGH.
    WINDOW_EIGENVALUE_CONSISTENCY_RESIDUAL_ABOVE_TOLERANCE = (
        "window_eigenvalue_consistency_residual_above_tolerance"
    )
    #: The refusal rules, row 9; the inputs table `efficiency_normalization`;
    #: detector-imperfections/req:efficiency-normalization. A declared factored
    #: loss outside [eta_max, 1], or a declared t < 1 in a request with source
    #: modes or with every efficiency zero, which is compiled at t = 1. Kind (a)
    #: of Def. def:tolmap's closing enumeration: declared data against a
    #: declared domain, decided exactly, NO TOLERANCE DECIDES IT.
    EFFICIENCY_NORMALIZATION_OUT_OF_RANGE = "efficiency_normalization_out_of_range"

    # --- input_routes: the three mutually exclusive routes -----------------
    INPUT_ROUTES_NOT_EXACTLY_ONE = "input_routes_not_exactly_one"

    # --- Definition def:modes, Definition def:instrument -------------------
    MODE_SPACE_MALFORMED = "mode_space_malformed"
    #: Definition def:modes ("a single declared value in this contract") with
    #: Assumption ass:thresh. The contract names no separate check ID for it
    #: and none is invented: the identity named here is the single-tau rule.
    MODE_SPACE_TAU_NOT_SINGLE_VALUED = "mode_space_tau_not_single_valued"
    INPUT_MODES_CHANNEL_EMPTY = "input_modes_channel_empty"
    INPUT_MODES_MALFORMED = "input_modes_malformed"
    PORT_MAP_MALFORMED = "port_map_malformed"

    # --- the inputs table: route domains -----------------------------------
    #: Def. def:tolmap (i), at eps_2. The rank half of the row is
    #: PORT_GRAM_RANK_EXCEEDS_PORT_SIZE above, which the refusal rules spell.
    PORT_GRAMS_NOT_ADMISSIBLE = "port_grams_not_admissible"
    #: Def. def:tolmap (iv), at eps_2: the bound data of Eq. eq:bounddata are
    #: admitted when c = 1 - lmax(B) >= -eps_2, and a computed c below that is
    #: REFUSED. The contract spells no reason for this check -- the refusal
    #: table does not carry it and `refusals.named_without_a_spelling` leaves
    #: the spelling to the implementer -- so this key is this module's, under
    #: the one rule the module docstring states, and is the exact analogue of
    #: item (i)'s PORT_GRAMS_NOT_ADMISSIBLE.
    BOUND_DATA_NOT_ADMISSIBLE = "bound_data_not_admissible"
    #: Def. def:tolmap (v), at eps_1; by Eq. eq:r1islmax the same test as
    #: r_1 <= eps_1 on the same number.
    INSTRUMENT_MATRIX_NOT_CONTRACTION = "instrument_matrix_not_contraction"

    # --- Definition def:graph (E1)-(E3), Requirement req:graph-refusal -----------
    GRAPH_CONDITION_E1_FAILED = "graph_condition_e1_failed"
    GRAPH_CONDITION_E2_FAILED = "graph_condition_e2_failed"
    GRAPH_CONDITION_E3_FAILED = "graph_condition_e3_failed"

    # --- the parameters table, exactness, and Assumption ass:exact ---------
    PARAMETER_TOLERANCE_NOT_ZERO = "parameter_tolerance_not_zero"
    DECIBEL_LOSS_NEGATIVE = "decibel_loss_negative"

    # --- Definition def:probe ----------------------------------------------
    PROBE_ALPHABET_EMPTY = "probe_alphabet_empty"
    #: Def. def:probe: T is an ALPHABET, a set of settings, so a label declared
    #: twice is refused rather than read as two settings or merged into one.
    PROBE_ALPHABET_LABEL_REPEATED = "probe_alphabet_label_repeated"
    PROBE_SETTING_OFF_MISSING = "probe_setting_off_missing"
    PROBE_MEAN_PHOTON_NUMBER_NEGATIVE = "probe_mean_photon_number_negative"
    PROBE_DECLARED_WITHOUT_SOURCE_MODES = "probe_declared_without_source_modes"
    #: A receiver with source modes, whose setting family the probe-conditioning
    #: submodule constructs, in an installation without that submodule (it is
    #: removable; receiver/settings.py). The contract spells no reason for it,
    #: so this key is this module's, named after the submodule that is absent.
    PROBE_CONDITIONING_SUBMODULE_ABSENT = "probe_conditioning_submodule_absent"

    # --- Definition def:coarse ---------------------------------------------
    COARSE_GRAINING_NOT_TOTAL = "coarse_graining_not_total"
    COARSE_GRAINING_NOT_SURJECTIVE = "coarse_graining_not_surjective"

    # --- Definition def:darkadm (D1), (D2); Remark rem:corrdark ------------
    #: (D1) at eps_4 and (D2) at eps_2, by Def. def:tolmap (iii). The contract
    #: spells no reason for either, so these two spellings are this module's.
    DARK_CONDITION_D1_FAILED = "dark_condition_d1_failed"
    DARK_CONDITION_D2_FAILED = "dark_condition_d2_failed"

    # --- the inputs table: photon_cutoff, tail_window, numerical_tolerances -
    PHOTON_CUTOFF_NEGATIVE = "photon_cutoff_negative"
    TAIL_WINDOW_NOT_ABOVE_CUTOFF = "tail_window_not_above_cutoff"
    #: Requirement req:window-declaration -- THE ONE REFUSAL IT NAMES:
    #: no m_t at a setting where (X) fails.
    TAIL_WINDOW_MISSING = "tail_window_missing"
    #: The inputs table `numerical_tolerances`, declared, never defaulted; one
    #: of the refusals `refusals.named_without_a_spelling` lists WITHOUT a
    #: spelling. A value outside [0, 1) is a different condition and carries the
    #: contract's own key, TOLERANCE_OUTSIDE_DECLARED_DOMAIN.
    NUMERICAL_TOLERANCE_MISSING = "numerical_tolerance_missing"

    # --- Definition def:residuals; a residual above its declared tolerance -
    #: r_5's reason is NOT spelled here: it is the contract's own
    #: PHOTON_BLOCK_POSITIVITY_RESIDUAL_ABOVE_TOLERANCE above, and inventing a
    #: `residual_r5_above_tolerance` beside it would be a string the contract
    #: does not state.
    RESIDUAL_R1_ABOVE_TOLERANCE = "residual_r1_above_tolerance"
    RESIDUAL_R2_ABOVE_TOLERANCE = "residual_r2_above_tolerance"
    RESIDUAL_R3_ABOVE_TOLERANCE = "residual_r3_above_tolerance"
    RESIDUAL_R4_ABOVE_TOLERANCE = "residual_r4_above_tolerance"
    #: Eq. eq:resgap against the declared eps_gap, at a setting that declares
    #: a window (the outputs table `validation_results`).
    RESIDUAL_GAP_ABOVE_TOLERANCE = "residual_gap_above_tolerance"


#: The NINE refusal reasons of the refusal rules (interface.yaml
#: `refusals.table`), in the table's own row order. Each refuses with NO
#: artifact.
REFUSAL_REASONS_VERBATIM: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.DARK_COUNT_CHANNEL_DECLARED_TWICE,
    RefusalReason.SPLITTING_RATIO_PRESENTATION_UNSUPPORTED,
    RefusalReason.PORT_GRAM_RANK_EXCEEDS_PORT_SIZE,
    RefusalReason.PHOTON_BLOCK_POSITIVITY_RESIDUAL_ABOVE_TOLERANCE,
    RefusalReason.TOLERANCE_OUTSIDE_DECLARED_DOMAIN,
    RefusalReason.EXACT_WINDOW_DECLARED_WITHOUT_REQUIRED_TOLERANCE,
    RefusalReason.EXACT_WINDOW_DEPTH_OUTSIDE_DECLARED_RANGE,
    RefusalReason.WINDOW_EIGENVALUE_CONSISTENCY_RESIDUAL_ABOVE_TOLERANCE,
    RefusalReason.EFFICIENCY_NORMALIZATION_OUT_OF_RANGE,
)

#: The one row whose `new_at` is receiver 0.7.0, the efficiency
#: normalization's (detector-imperfections/req:efficiency-normalization), named
#: apart as the 0.3.0 rows are.
REFUSAL_REASONS_ADDED_AT_0_7_0: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.EFFICIENCY_NORMALIZATION_OUT_OF_RANGE,
)

#: The three rows whose `new_at` is the frozen registry's 0.3.0 (interface.yaml
#: `refusals.table`; tests/oracles/registry_receiver_povm.py), the three of the
#: exact window, named apart so that the delta is visible without differencing
#: two tuples.
REFUSAL_REASONS_ADDED_AT_0_3_0: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.EXACT_WINDOW_DECLARED_WITHOUT_REQUIRED_TOLERANCE,
    RefusalReason.EXACT_WINDOW_DEPTH_OUTSIDE_DECLARED_RANGE,
    RefusalReason.WINDOW_EIGENVALUE_CONSISTENCY_RESIDUAL_ABOVE_TOLERANCE,
)

#: The complete set of reason spellings the contract states that this module
#: can emit: the nine refusals, the tier fallback being never produced (see
#: the module docstring). It coincides with :data:`REFUSAL_REASONS_VERBATIM`
#: -- which answers the other question, which rows of the refusal table refuse
#: with no artifact -- and would part from it the day the contract spells a
#: reason that is not one of those rows. Every OTHER member of
#: :class:`RefusalReason` is this module's own spelling of a naming obligation
#: -- including BOUND_DATA_NOT_ADMISSIBLE, which Def. def:tolmap (iv) declines
#: to spell in terms (see the module docstring).
REASON_VOCABULARY: Final[tuple[RefusalReason, ...]] = (*REFUSAL_REASONS_VERBATIM,)

#: interface.yaml `parameters.exactness` -- the contract's own prose, in its own
#: quotation marks, carried as the `detail` of a PARAMETER_TOLERANCE_NOT_ZERO
#: refusal. It is NOT a machine key (`reason_string_note`).
PROSE_REASONS: Final[MappingProxyType[str, str]] = MappingProxyType(
    {
        "parameter_tolerance": "parameter uncertainty sets are out of scope",
    }
)

#: The outputs table `calibration_coverage`, with Assumption ass:trust. The LITERAL
#: statement the artifact carries; prose, never a verdict this module reaches.
CALIBRATION_COVERAGE_STATEMENT: Final[str] = (
    "The receiver is trusted and exactly characterized (Assumption ass:trust): "
    "the declared instrument describes the physical receiver exactly and is "
    "under the legitimate party's control. No characterization data, "
    "uncertainty set or device family is represented."
)

#: (E1)-(E3) of Definition def:graph to the reason a refusal by that condition
#: names. Requirement req:graph-refusal requires the failing condition to be
#: named.
GRAPH_CONDITION_REASONS: Final[MappingProxyType[str, RefusalReason]] = MappingProxyType(
    {
        "E1": RefusalReason.GRAPH_CONDITION_E1_FAILED,
        "E2": RefusalReason.GRAPH_CONDITION_E2_FAILED,
        "E3": RefusalReason.GRAPH_CONDITION_E3_FAILED,
    }
)

#: (D1)-(D2) of Definition def:darkadm to the reason a refusal names. Remark
#: rem:corrdark: for a DECLARED R, (D1) and (D2) are what must be checked
#: rather than derived.
DARK_CONDITION_REASONS: Final[MappingProxyType[str, RefusalReason]] = MappingProxyType(
    {
        "D1": RefusalReason.DARK_CONDITION_D1_FAILED,
        "D2": RefusalReason.DARK_CONDITION_D2_FAILED,
    }
)

#: r_1..r_6 of Definition def:residuals to the reason an above-tolerance
#: residual names. FOUR ARE THIS MODULE'S SPELLINGS AND TWO ARE THE
#: CONTRACT'S: the refusal rules give r_5 the verbatim
#: `photon_block_positivity_residual_above_tolerance` and r_6 the verbatim
#: `window_eigenvalue_consistency_residual_above_tolerance`, and a key in this
#: module's own scheme beside either would be a string the contract does not
#: state. r_6 IS EMITTED ONLY WHERE A DEPTH IS DECLARED (Def. def:residuals:
#: r_6 depends on the request, not on the route), so this row is consulted
#: exactly there.
RESIDUAL_REASONS: Final[MappingProxyType[str, RefusalReason]] = MappingProxyType(
    {
        "r_1": RefusalReason.RESIDUAL_R1_ABOVE_TOLERANCE,
        "r_2": RefusalReason.RESIDUAL_R2_ABOVE_TOLERANCE,
        "r_3": RefusalReason.RESIDUAL_R3_ABOVE_TOLERANCE,
        "r_4": RefusalReason.RESIDUAL_R4_ABOVE_TOLERANCE,
        "r_5": RefusalReason.PHOTON_BLOCK_POSITIVITY_RESIDUAL_ABOVE_TOLERANCE,
        "r_6": (RefusalReason.WINDOW_EIGENVALUE_CONSISTENCY_RESIDUAL_ABOVE_TOLERANCE),
    }
)


@dataclass(frozen=True)
class Refusal:
    """A failed validation, as a record.

    ``reason`` is the machine-readable field and is the load-bearing one;
    ``detail`` names the offending datum in prose, for a human reading a
    refusal, and is where Requirement ``req:graph-refusal``'s "offending element
    pair" and the two contract prose reasons are carried. The ``fail_closed``
    convention: a refusal is emitted INSTEAD OF an artifact, never beside one.
    """

    reason: RefusalReason
    detail: str

    def as_machine_record(self) -> dict[str, str]:
        """Return the refusal as a machine record."""
        return {"reason": str(self.reason), "detail": self.detail}


class AssumptionId(StrEnum):
    """The assumption files of the ledger, by contract ID, one member per file.

    One member per row of ``interface.yaml`` ``outputs.assumption_ledger.rows``.
    A-EIG is INVOKED only where a caller declares an exact-window depth
    (Ass. ass:eig), and its ledger row exists on every artifact because the
    outputs table asks for the machine keys of the assumption files
    (``a_eig_row_note``) -- the row records where it was invoked, and an empty
    record is the honest one.

    EVERY MEMBER IS A ROW ON EVERY ARTIFACT: the ledger's presence rule is "one
    row per file and every row on every artifact" (``outputs.assumption_ledger``
    ``content``). The conditions the engine decides on the declared data --
    acyclicity, (E2) of ``def:graph``, and occupation-diagonal probe states,
    ``def:probe`` -- are definitions with requirements and have no row
    (``decided_conditions_note``).
    """

    A_TRUST = "A-TRUST"
    A_PASSIVE = "A-PASSIVE"
    A_VAC = "A-VAC"
    A_MODES = "A-MODES"
    A_THRESH = "A-THRESH"
    A_PORT = "A-PORT"
    A_EXACT = "A-EXACT"
    A_NOSEL = "A-NOSEL"
    A_ROUND = "A-ROUND"
    #: Ass. ass:eig: the value beta-hat*^(t)(n) an implementation computes
    #: satisfies beta-hat*^(t)(n) - eps_eig <= beta*^(t)(n) (Eq.
    #: eq:eigassumption). ONE-SIDED DELIBERATELY, on the side that matters.
    A_EIG = "A-EIG"


#: The ledger's machine keys, one per assumption file, transcribed from
#: interface.yaml `outputs.assumption_ledger.rows`.
ASSUMPTION_MACHINE_KEYS: Final[MappingProxyType[AssumptionId, str]] = MappingProxyType(
    {
        AssumptionId.A_TRUST: "receiver_trusted_exact",
        AssumptionId.A_PASSIVE: "passive_optics",
        AssumptionId.A_VAC: "undeclared_inputs_vacuum",
        AssumptionId.A_MODES: "no_undeclared_paths",
        AssumptionId.A_THRESH: "threshold_memoryless_detectors",
        AssumptionId.A_PORT: "mode_insensitive_ports",
        AssumptionId.A_EXACT: "exact_parameters",
        AssumptionId.A_NOSEL: "device_not_adversarial",
        AssumptionId.A_ROUND: "round_homogeneity",
        AssumptionId.A_EIG: "exact_window_eigenvalue_slack",
    }
)

#: THE ASSUMPTIONS NO CODE PATH OF THIS MODULE DECIDES BEYOND THEIR CLAUSES ON
#: THE DECLARED DATA, in the ledger's order: ``never_verified_set``
#: (``req:decidable-assumptions``). A member is exactly an assumption whose
#: ``verification`` header field is ``never`` (spec/claim-format.md section
#: 3.2), read from the shipped claim-closure table by machine key and not
#: listed here by hand. Remark ``rem:unchecked-assumptions`` says which
#: these are: every assumption about the physical receiver or the run, and
#: A-EIG, a statement about the ARITHMETIC that is invoked only where a caller
#: declares an exact-window depth -- that is, every assumption of the ledger.
#: The evaluation model is Definition ``def:evaluation-model``, a restriction the
#: contract places on itself and no assumption. No number depends on
#: membership; it sets the ledger's ``never_verified`` flag and nothing else.
#:
#: A-EIG'S PLACE HERE IS NOT A FORMALITY. Rem. rem:exacteig: r_6 does NOT
#: verify Assumption ass:eig -- r_6 fires when beta-hat* lands too LOW, and
#: the assumption constrains it from landing too HIGH -- and NO TEST IN THE
#: CONTRACT BOUNDS THE UNSAFE DIRECTION.
NEVER_VERIFIED: Final[tuple[AssumptionId, ...]] = tuple(
    identifier
    for identifier in AssumptionId
    if never_verified(ASSUMPTION_MACHINE_KEYS[identifier])
)

#: Which of the never-verified assumptions is INVOKED ONLY CONDITIONALLY, and
#: on what. Every other member of :data:`NEVER_VERIFIED` is invoked by every
#: declaration; A-EIG is invoked exactly where a caller declares an
#: `exact_window` depth, "and by no other declaration" (Ass. ass:eig).
CONDITIONALLY_INVOKED: Final[MappingProxyType[AssumptionId, str]] = MappingProxyType(
    {
        AssumptionId.A_EIG: (
            "invoked exactly at the settings whose declaration carries an "
            "`exact_window` depth and whose weight is evaluated in floating "
            "point (Ass. ass:eig; Def. def:pmcex; Req. req:eig-ledger-row)"
        ),
    }
)
