"""The machine vocabulary of this module: refusal reasons, verdicts, assumptions.

THE REFUSAL STRINGS, IN THE CLASSES OF THE INTERFACE'S ``refusal_reasons``
==========================================================================
spec/modules/protocol-compiler/interface.yaml's ``refusal_reasons`` partitions
the strings this module emits into classes by what each string names:

* ``frozen_spellings`` -- seven strings whose spellings are frozen, which
  consumers already recognise and the oracle registry pins
  (:data:`REFUSAL_REASONS_VERBATIM`):

  * ``fixed_fraction_requested`` -- ``thm:choice-encoding`` (iv), and the
    ``test_statistics_model`` convention;
  * ``no_feasibility_witness`` -- ``thm:feasibility`` (ii), and
    ``rem:completeness``, which adds the reading rule: it means "I WAS NOT
    SHOWN A FEASIBLE STATE", never "there is none", and must not be reported
    to a user as a defect in the protocol;
  * ``sector_map_mismatch`` -- check V1's four-component comparison;
  * ``alice_marginal_trace_rounds``, ``alice_povm_summation_rounds`` and
    ``bob_povm_summation_rounds`` -- condition (S) on ``tr tau_A``, on
    ``sum_x M_x`` and on ``sum_v F_v^(s)`` respectively;
  * ``emitted_value_not_representable`` -- ``def:weighted``, "where the
    compiler's OWN EXACT CONSTRUCTION of a choice-weighted element does not
    land on a binary64 number", and no wider than that. It covers the
    products ``P(f | t(v)) F_v`` of the setting-dependent form as well as
    ``q_t N_{u|t}``.

* ``weight_list`` -- ``choice_weights_not_normalized``, ``req:weight-list``'s
  own spelling, for a declared weight list of the setting-independent form
  whose exact sum is not 1 or whose declared-order accumulation rounds
  (:data:`REFUSAL_REASONS_WEIGHT_LIST`).
* ``setting_dependent_weighting`` -- ``choice_weight_depends_on_outcome`` and
  ``choice_weight_not_stochastic`` (``def:weighted``'s setting-dependent
  form, ``thm:choice-encoding`` (viii), ``rem:relabel``;
  :data:`REFUSAL_REASONS_SETTING_DEPENDENT_WEIGHTING`).
* ``conditional_family`` -- ``conditional_family_not_admissible``, for a
  conditional family ``{N_{u|t}}_u`` of a declared ``public_choices`` record
  that is not exactly admissible (:data:`REFUSAL_REASONS_CONDITIONAL_FAMILY`).
  THE STRING IS ``def:weighted``'s OWN, and it is none of the emitted
  family's: of that family V3 decides (H), (P), (C) and (S) and V1 compares
  the map with ``sector_map_mismatch``, whose scope note pins it to the
  ``Q``-operator families of ``eq:declaration``, and a conditional family is
  no slot of that equation.
* ``physical_family`` -- ``physical_family_not_admissible``, for the
  physical receiver family as presented (each measured factor's) that is not
  exactly admissible on its physical receiver space read as one block
  (``def:well-formed-spec`` (iv); ``req:physical-family-decision``;
  :data:`REFUSAL_REASONS_PHYSICAL_FAMILY`). It is none of the emitted
  family's strings for the reason the conditional family's is not: at a
  non-trivial receiver segment the physical family is no slot of
  ``eq:declaration``.
* ``band_a_route`` -- two strings (:data:`REFUSAL_REASONS_BAND_A_ROUTE`):
  ``band_a_outside_ideal_receiver``, for a specification on the Band-A route
  outside the ideal qubit receiver its premise A-IDEAL describes: more than
  one measured factor, a dimension other than two, or a family as presented
  that is not projective (``req:band-a-ideal-receiver``); and
  ``band_a_link_not_identity``, for one whose one receiver link supplies no
  channel as data or whose outcome correspondence is not the identity on one
  alphabet (``req:band-a-identity-link``).
* ``source_identity_at_da1`` -- ``da1_source_identity_failed``, for a
  trusted-source specification at ``d_A = 1`` whose weighted ensemble members
  are not Alice's letter weights times their sum, (SR2) read at ``d_A = 1``
  (``req:da1-source-identity``; :data:`REFUSAL_REASONS_SOURCE_IDENTITY_AT_DA1`).
* ``general_format`` -- seven strings, every one spelled by a claim of this
  module (:data:`REFUSAL_REASONS_GENERAL_FORMAT`):
  ``ensemble_form_in_untrusted_mode`` (``def:compile``, decided at V3);
  ``alice_sector_marginal_zero`` (V2); ``alice_ensemble_marginal_mismatch``
  and ``alice_ensemble_sum_rounds`` (V3, the ensemble form's (C)- and
  (S)-analogues); ``constraint_scope_not_a_factor`` (V6);
  ``ensemble_presentation_without_ensemble_form`` (``thm:gates``, gate (G2));
  ``general_entry_beside_source_segment`` (``def:chaincond``, the
  licensed-only rule). FIVE OF THE SEVEN REFUSE AN OBJECT THE BASIC FORMAT
  CANNOT DECLARE; the other two are in the fail-closed direction -- a
  ``general`` entry beside a non-empty source segment would otherwise be
  EMITTED with the flag false, and an ensemble presentation beside a
  POVM-form declaration is already refused by ``transmitter/def:srcert``'s
  own rule, so that string names an existing refusal.
* ``source_mode_rule`` -- ``source_segment_in_untrusted_mode``
  (``req:chain-refusals``).
* ``this_files_own_spelling`` -- ``chain_interface_condition_failed``, for a
  chain that fails one of ``def:chaincond``'s conditions. No claim spells a
  string for it; what the claim requires is that the refusal NAME the
  condition, which this string plus the named condition does.

FIVE ARE THE TRANSMITTER'S AND ARE REUSED RATHER THAN RE-SPELLED. Gate (G2)
RE-DECIDES the five certificate conditions on the emitted data, and the
interface's ``fixed_by_this_file`` says why there is no second vocabulary for
them: "the five conditions are the same five on the same data, so a second
vocabulary would be two names for one refusal". The members below carry the
same strings as :class:`certiqs_key.transmitter.reasons.RefusalReason`'s, and a
test in tests/oracles/ holds the two lists together.

EVERYWHERE ELSE the claims fix the naming OBLIGATION and the IDENTITY of the
named check and NOT a spelling -- "a machine-readable reason NAMING THE FAILED
CHECK", "naming the check", "naming the condition", ``thm:chain-consumption`` (i)
("refused WITH THAT CONDITION NAMED"). THIS MODULE DECIDES IT, HERE, AND THE SPELLINGS
BELOW ARE MINE. The scheme is one rule and no exceptions: a reason is
``<family>_<identifier>_failed`` in lower case, with the identifier exactly the
claim's own -- ``v1``..``v8``, ``g1``, ``g2``, ``g3a``, ``g3b``. Nothing is
abbreviated and nothing is invented beyond the prefix, so every string names
the failed check's identity and a reader can go from the string to the clause
without a table.

THE CHAIN CONDITIONS ARE THE EXCEPTION AND THE INTERFACE IS WHY. The
interface.yaml fixes ONE spelling for all nine,
``chain_interface_condition_failed``, and the machine keys of that file are
binding on this implementation. The condition is named in the refusal's
detail and carried as a datum on the report, which is what ``def:chaincond``
and ``thm:chain-consumption`` (i) ask for. The nine finer spellings that
are NOT reasons are :data:`RETIRED_CHAIN_REFUSAL_REASONS`.

ONE CONSEQUENCE WORTH NAMING: THERE ARE SEVEN INVENTED ``V``-SPELLINGS, NOT
EIGHT. V7's refusal reason is fixed by the claims -- ``thm:feasibility`` (ii) attaches
``no_feasibility_witness`` to it, in both of its branches -- so the V7 slot of
:data:`CHECK_REFUSAL_REASONS` holds that verbatim string and no
``check_v7_failed`` exists. An implementation that emitted both would have two
names for one refusal.

A REFUSAL IS A RECORD AND NEVER AN EXCEPTION
============================================
The ``refusal`` output row types it as "a record or absent", present "exactly
when the compiler refuses", carrying "a machine-readable reason naming the
failed check"; and "A REFUSAL EMITS NO DECLARATION". :class:`Refusal` is that
record. The exceptions of :mod:`certiqs_key.foundations.errors` are for arguments no
clause can be read against, which is a different thing and must stay
distinguishable: a caller must not be able to turn a refusal into an exception
or an exception into a reason code.

THE THREE-VALUED GATE VOCABULARY IS THE CLAIMS'
===============================================
:class:`GateVerdict` carries ``passed`` / ``failed`` / ``passed vacuously``
from the ``gate_report`` output row, with the space, as written.
``rem:degenerate`` makes the third REQUIRED in its case and adds that the
compiler "must not report the vacuous pass as evidence of anything". NO FOURTH
TOKEN EXISTS.

THE EMITTED SOURCE MODE IS THE TRANSMITTER'S VOCABULARY AND NOT A SECOND ONE
============================================================================
:class:`~certiqs_key.transmitter.reasons.SourceMode` is re-exported here rather
than redeclared. The mode is read off the transmitter artefact's
``alice_marginal`` and off nothing else -- filled is trusted, nomarg is
untrusted (``def:compile``; ``def:spec`` (a)) -- so the enum that spells it
belongs to the module that decides it. A module that declared the same two
values a second time would be a vocabulary that can disagree with itself, which
is what :data:`certiqs_key.domain.chain.Segment` exists to avoid at the other
seam. THERE IS NO ``SourceModeRequest``: this module serves no request and
takes no fallback.

THE FOUR CONDITION OUTCOMES ARE MINE
====================================
For the interface conditions of ``def:chaincond`` the claims fix no report
tokens at all. What they fix is that a chain failing one "is REFUSED with that
condition NAMED" (``thm:chain-consumption`` (i)); that (C4) and (S3) are checkable only
"where every link supplies its channel as data" and are otherwise "carried
instead as the supplier obligation Assumption A-LINK"; and that at an empty
segment the conditions are "VACUOUS, quantifying over an empty list of links"
(``thm:band-a`` (ii)). :class:`ConditionOutcome`'s four values name those four
situations and are this module's spelling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from certiqs_key.domain.claim_closure import never_verified
from certiqs_key.transmitter.reasons import Refusal as TransmitterRefusal
from certiqs_key.transmitter.reasons import SourceMode

__all__ = [
    "ASSUMPTION_MACHINE_KEYS",
    "CERTIFICATE_CONDITION_REASONS",
    "CHAIN_REFUSAL_REASONS",
    "CHECK_REFUSAL_REASONS",
    "INHERITED_KEYS",
    "INHERITED_NEVER_VERIFIED_KEYS",
    "NEVER_VERIFIED",
    "REFUSAL_REASONS_BAND_A_ROUTE",
    "REFUSAL_REASONS_CONDITIONAL_FAMILY",
    "REFUSAL_REASONS_GENERAL_FORMAT",
    "REFUSAL_REASONS_PHYSICAL_FAMILY",
    "REFUSAL_REASONS_SETTING_DEPENDENT_WEIGHTING",
    "REFUSAL_REASONS_SOURCE_IDENTITY_AT_DA1",
    "REFUSAL_REASONS_VERBATIM",
    "REFUSAL_REASONS_WEIGHT_LIST",
    "RETIRED_CHAIN_REFUSAL_REASONS",
    "AssumptionId",
    "ConditionOutcome",
    "GateVerdict",
    "Refusal",
    "RefusalReason",
    "SourceMode",
    "refusal_from_transmitter",
]



class RefusalReason(StrEnum):
    """Every machine-readable reason this module can emit.

    Grouped as the interface's ``refusal_reasons`` classes are (the module
    docstring lists them): the seven frozen spellings, the weight list's,
    the setting-dependent weighting's two, the conditional family's, the
    physical family's, the Band-A route's, the source identity's at
    ``d_A = 1``, the general format's seven, the source-mode rule's, the interface's own
    spelling, the transmitter's reused at gate (G2) and at source-link
    admission, and this module's spellings of the claims' naming obligation,
    under the one rule the module docstring states.
    """

    # --- the SEVEN frozen spellings ------------------------------------------
    #: thm:choice-encoding (iv); the `test_statistics_model` convention.
    FIXED_FRACTION_REQUESTED = "fixed_fraction_requested"
    #: thm:feasibility (ii); rem:completeness. THE V7 REFUSAL.
    NO_FEASIBILITY_WITNESS = "no_feasibility_witness"
    #: Check V1: the four-component sector-map comparison, "naming the first
    #: position at which the lists differ".
    SECTOR_MAP_MISMATCH = "sector_map_mismatch"
    #: Check V2: `tr tau_A = 1` accumulated over the row index and required to
    #: round nowhere.
    ALICE_MARGINAL_TRACE_ROUNDS = "alice_marginal_trace_rounds"
    #: Check V3: `sum_x M_x = 1_A` in the emitted index order, condition (S).
    ALICE_POVM_SUMMATION_ROUNDS = "alice_povm_summation_rounds"
    #: Check V3: `sum_v F_v^(s) = 1_{Q_s}` per block, condition (S), "carrying
    #: the sector and the outcome index at which the first inexact addition
    #: occurred". The alphabet is V, or the support V_P in its product order
    #: where a setting-dependent weighting was applied.
    BOB_POVM_SUMMATION_ROUNDS = "bob_povm_summation_rounds"
    #: def:weighted: an exact product of declared binary64 numbers --
    #: `q_t N_{u|t}`, or `P(f | t(v)) F_v` -- that is NOT a binary64 number.
    #: Its scope is narrower than its name: it does NOT cover an entry that IS
    #: binary64 but lies off the instance's own lattice.
    EMITTED_VALUE_NOT_REPRESENTABLE = "emitted_value_not_representable"

    # --- the weight list ---------------------------------------------------
    #: req:weight-list: a declared weight list {q_t} of the
    #: setting-independent form whose EXACT sum is not 1, or whose
    #: declared-order accumulation rounds at some addition. The string is the
    #: requirement's own. One reason covers both legs, which separate in both
    #: directions (fl(0.9), fl(0.1); 2**-54, 1/2, 1/2 - 2**-54).
    CHOICE_WEIGHTS_NOT_NORMALIZED = "choice_weights_not_normalized"

    # --- the setting-dependent weighting -----------------------------------
    #: A Bob-side choice weighting presented indexed by V, by the device
    #: outcome, or by any component of v other than its setting. REFUSED BY
    #: TYPE, nothing being measured (def:weighted; ass:coin; rem:relabel).
    CHOICE_WEIGHT_DEPENDS_ON_OUTCOME = "choice_weight_depends_on_outcome"
    #: An entry of P is negative, or a row of P has a declared-order sum that
    #: is not exactly 1, or that sum rounds.
    CHOICE_WEIGHT_NOT_STOCHASTIC = "choice_weight_not_stochastic"

    # --- the conditional family ----------------------------------------------
    #: A conditional family ``{N_{u|t}}_u`` of a declared ``public_choices``
    #: record is not exactly admissible for the map those families carry. THE
    #: STRING IS def:weighted's OWN and is none of the emitted family's: of the
    #: emitted family V3 decides (H), (P), (C), (S) and V1 compares the map,
    #: and a conditional family is no slot of eq:declaration.
    CONDITIONAL_FAMILY_NOT_ADMISSIBLE = "conditional_family_not_admissible"

    # --- the physical family ---------------------------------------------------
    #: The physical receiver family as presented -- in the general format, a
    #: measured factor's -- is not exactly admissible on its physical receiver
    #: space read as one block: (H), (P) or (C) fails, or its declared-order
    #: completeness sum rounds; for a choice-weighted presentation, its own
    #: declared-order sum rounds (def:well-formed-spec (iv);
    #: req:physical-family-decision). Decided on every route, before any
    #: condition of the chain.
    PHYSICAL_FAMILY_NOT_ADMISSIBLE = "physical_family_not_admissible"

    # --- the Band-A route ------------------------------------------------------
    #: A specification on the Band-A route (def:banda read on the record) that
    #: declares more than one measured factor, a physical receiver system or,
    #: in trusted-source mode, a transmitted system of dimension other than
    #: two, or a physical family as presented that is not projective
    #: (req:band-a-ideal-receiver). The detail names the first failing clause.
    BAND_A_OUTSIDE_IDEAL_RECEIVER = "band_a_outside_ideal_receiver"
    #: A specification on the Band-A route, not refused with
    #: ``band_a_outside_ideal_receiver``, whose one receiver link supplies no
    #: channel as data, or whose outcome correspondence is not the identity on
    #: one alphabet, ``V = V^ph`` with ``gamma(w) = w``
    #: (req:band-a-identity-link). The detail names the first failing clause.
    BAND_A_LINK_NOT_IDENTITY = "band_a_link_not_identity"

    # --- the source identity at d_A = 1 ---------------------------------------
    #: Trusted-source mode at d_A = 1, where the identity
    #: ``sigma_x = m_x sum_y sigma_y`` ((SR2) read at d_A = 1) fails at some
    #: letter, decided exactly (req:da1-source-identity). The detail names the
    #: first such letter and the first differing entry.
    DA1_SOURCE_IDENTITY_FAILED = "da1_source_identity_failed"

    # --- the general format --------------------------------------------------
    # Each is spelled by a claim of this module and repeated in interface.yaml
    # identically; the partition class there is `general_format`, and its
    # preamble says which two of the seven refuse an object the basic format
    # CAN declare.
    #: def:compile / def:validator V3, which is D(iii)'s general-format clause:
    #: Alice's measurement slot is in ENSEMBLE form beside a marginal slot
    #: holding nomarg. A DECISION ON WHICH OF TWO SLOTS IS FILLED and not on a
    #: number; the ensemble form exists in trusted mode only (def:declaration
    #: (DX4)).
    ENSEMBLE_FORM_IN_UNTRUSTED_MODE = "ensemble_form_in_untrusted_mode"
    #: Check V2 in its general-format reading: Alice's measurement slot is in
    #: ensemble form and some declared block ``tau_A^(t)`` is ZERO. A comparison
    #: of declared entries with the datum 0 (eq:ensembleform's second condition),
    #: naming the sector. A SINGULAR block stays admissible.
    ALICE_SECTOR_MARGINAL_ZERO = "alice_sector_marginal_zero"
    #: Check V3, the ensemble form's (C)-analogue: ``sum_x N_x^(t)`` differs from
    #: the declared block ``tau_A^(t)``, decided ENTRY BY ENTRY, naming the sector
    #: and the first differing entry.
    ALICE_ENSEMBLE_MARGINAL_MISMATCH = "alice_ensemble_marginal_mismatch"
    #: Check V3, the ensemble form's (S)-analogue: that declared-order sum ROUNDS,
    #: naming the sector and the index of the first inexact addition. As
    #: everywhere else, (S) is on the ADDITIONS and not on the operands.
    ALICE_ENSEMBLE_SUM_ROUNDS = "alice_ensemble_sum_rounds"
    #: Check V6 in its general-format reading: an entry's SCOPE does not name a
    #: measured factor of the emitted sector map. A comparison of a label against
    #: the factor list, decided and never measured, naming the entry.
    CONSTRAINT_SCOPE_NOT_A_FACTOR = "constraint_scope_not_a_factor"
    #: Gate (G2): the transmitter artefact presents an ENSEMBLE PRESENTATION
    #: beside a POVM-form declaration, where "nothing ties the declared {M_x} to
    #: it" (def:eligible). It names an EXISTING refusal rather than a new one --
    #: transmitter/def:srcert's last paragraph already refuses a presentation to a
    #: POVM-form consumer -- and lands on row 3 of the gate outcome table.
    ENSEMBLE_PRESENTATION_WITHOUT_ENSEMBLE_FORM = (
        "ensemble_presentation_without_ensemble_form"
    )
    #: def:chaincond, the licensed-only rule: an entry declared ``general`` stands
    #: beside a NON-EMPTY source segment, where every entry must carry a real
    #: scalar. IT REFUSES A CASE THE ACCEPTED FORMAT ADMITS, which without the
    #: rule would be emitted with `key_length_eligible` false (row 5), and the
    #: refusal is strictly the more conservative outcome.
    GENERAL_ENTRY_BESIDE_SOURCE_SEGMENT = "general_entry_beside_source_segment"

    # --- the source-mode rule ------------------------------------------------
    #: def:chaincond, the declared-source-mode condition: a NON-EMPTY source
    #: segment is presented while the marginal slot holds ``nomarg``. Source
    #: maps are licensed in trusted-source mode only, so the untrusted case is
    #: refused before any declaration is emitted. This is separate from the
    #: trusted ``d_A = 1`` residual: its marginal slot holds ``[1]``, not
    #: ``nomarg``, and no new refusal is added for it.
    SOURCE_SEGMENT_IN_UNTRUSTED_MODE = "source_segment_in_untrusted_mode"
    # Source-link admission reasons are owned by transmitter and reused at the
    # compiler boundary when (A1)--(A3) are decided on its typed records.
    LINK_KIND_DEFERRED = "link_kind_deferred"
    SOURCE_LINK_ENTRY_PRESENT = "source_link_entry_present"
    SOURCE_LINK_FAMILY_EXCLUDES_ITS_DESCRIPTOR = (
        "source_link_family_excludes_its_descriptor"
    )
    SOURCE_LINK_NOT_IN_REGISTRY = "source_link_not_in_registry"
    SOURCE_LINK_ASSUMPTION_NOT_IN_LEDGER = "source_link_assumption_not_in_ledger"
    SOURCE_SEGMENT_NOT_FROM_ADMITTING_MODULE = (
        "source_segment_not_from_admitting_module"
    )
    SOURCE_LINK_KIND_NOT_ADMITTED = "source_link_kind_not_admitted"

    # --- the interface's own spelling -------------------------------------
    #: A presented chain fails one of def:chaincond's conditions. The refusal
    #: NAMES THE CONDITION beside this string.
    CHAIN_INTERFACE_CONDITION_FAILED = "chain_interface_condition_failed"

    # --- V1-V8 of def:validator (V7 is the verbatim one above) ------------
    CHECK_V1_FAILED = "check_v1_failed"
    CHECK_V2_FAILED = "check_v2_failed"
    CHECK_V3_FAILED = "check_v3_failed"
    CHECK_V4_FAILED = "check_v4_failed"
    CHECK_V5_FAILED = "check_v5_failed"
    CHECK_V6_FAILED = "check_v6_failed"
    CHECK_V8_FAILED = "check_v8_failed"

    # --- the transmitter's five, REUSED at gate (G2) ----------------------
    #: (SR3) HAS NO REASON AND CANNOT FAIL HERE: thm:certificate-sufficiency (i) says it
    #: "is decided by no function of the emitted data", and (G2) tests the licence
    #: record's PRESENCE.
    CERTIFICATE_NOT_HERMITIAN = "certificate_not_hermitian"
    CERTIFICATE_NOT_IDEMPOTENT = "certificate_not_idempotent"
    CERTIFICATE_TRACE_NOT_ONE = "certificate_trace_not_one"
    CERTIFICATE_MARGINAL_IDENTITY_FAILS = "certificate_marginal_identity_fails"
    CERTIFICATE_SIGNAL_IDENTITY_FAILS = "certificate_signal_identity_fails"

    # --- (G1)-(G3) of def:eligible ----------------------------------------
    GATE_G1_FAILED = "gate_g1_failed"
    GATE_G2_FAILED = "gate_g2_failed"
    # NO PATH CONSTRUCTS THE NEXT TWO, AND THE GATE OUTCOME TABLE IS WHY.
    # A (G3) failure is an EMISSION
    # with ``key_length_eligible = false`` -- rows 5 and 6 of the table of
    # ``def:gate-outcome-table`` -- and never a refusal, so ``resolve_gates``
    # records the verdict on the report and refuses nothing. THE NAMES ARE
    # KEPT, for the reason the naming scheme above gives: they are the machine
    # spellings of the gate IDENTITIES (3a) and (3b), the vocabulary a
    # consumer reads a gate report with, and dropping them would leave two of
    # the four gates unnamable while the other two are named. Unlike the nine
    # chain spellings, no interface row tables a competing spelling for them.
    GATE_G3A_FAILED = "gate_g3a_failed"
    GATE_G3B_FAILED = "gate_g3b_failed"


#: The SEVEN frozen spellings, in the order the frozen registry's tuple
#: extends: its two strings are a PREFIX of this tuple, and a prefix is what
#: the oracle asserts. The interface's `frozen_spellings` list is the same
#: seven in a different order and fixes no order.
REFUSAL_REASONS_VERBATIM: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.FIXED_FRACTION_REQUESTED,
    RefusalReason.NO_FEASIBILITY_WITNESS,
    RefusalReason.SECTOR_MAP_MISMATCH,
    RefusalReason.ALICE_MARGINAL_TRACE_ROUNDS,
    RefusalReason.ALICE_POVM_SUMMATION_ROUNDS,
    RefusalReason.BOB_POVM_SUMMATION_ROUNDS,
    RefusalReason.EMITTED_VALUE_NOT_REPRESENTABLE,
)

#: The weight list's one spelling, the interface's ``weight_list`` class.
REFUSAL_REASONS_WEIGHT_LIST: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.CHOICE_WEIGHTS_NOT_NORMALIZED,
)

#: The setting-dependent weighting's two spellings, the interface's
#: ``setting_dependent_weighting`` class.
REFUSAL_REASONS_SETTING_DEPENDENT_WEIGHTING: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.CHOICE_WEIGHT_DEPENDS_ON_OUTCOME,
    RefusalReason.CHOICE_WEIGHT_NOT_STOCHASTIC,
)

#: The conditional family's one spelling, the interface's
#: ``conditional_family`` class: def:weighted's own rather than that file's.
REFUSAL_REASONS_CONDITIONAL_FAMILY: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.CONDITIONAL_FAMILY_NOT_ADMISSIBLE,
)

#: The physical family's one spelling, the interface's ``physical_family``
#: class (``req:physical-family-decision``).
REFUSAL_REASONS_PHYSICAL_FAMILY: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.PHYSICAL_FAMILY_NOT_ADMISSIBLE,
)

#: The Band-A route's two spellings, the interface's ``band_a_route`` class
#: (``req:band-a-ideal-receiver``, ``req:band-a-identity-link``).
REFUSAL_REASONS_BAND_A_ROUTE: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER,
    RefusalReason.BAND_A_LINK_NOT_IDENTITY,
)

#: The source identity's one spelling, the interface's
#: ``source_identity_at_da1`` class (``req:da1-source-identity``).
REFUSAL_REASONS_SOURCE_IDENTITY_AT_DA1: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.DA1_SOURCE_IDENTITY_FAILED,
)

#: The general format's seven spellings, in the order interface.yaml's
#: ``general_format.strings`` lists them. Every one is a CLAIM's spelling
#: rather than that file's.
REFUSAL_REASONS_GENERAL_FORMAT: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.ENSEMBLE_FORM_IN_UNTRUSTED_MODE,
    RefusalReason.ALICE_SECTOR_MARGINAL_ZERO,
    RefusalReason.ALICE_ENSEMBLE_MARGINAL_MISMATCH,
    RefusalReason.ALICE_ENSEMBLE_SUM_ROUNDS,
    RefusalReason.CONSTRAINT_SCOPE_NOT_A_FACTOR,
    RefusalReason.ENSEMBLE_PRESENTATION_WITHOUT_ENSEMBLE_FORM,
    RefusalReason.GENERAL_ENTRY_BESIDE_SOURCE_SEGMENT,
)

#: The five certificate conditions to the reason gate (G2)'s re-decision
#: names, keyed by the condition as
#: ``CertificateVerification.failing_conditions`` of the transmitter
#: spells them. The strings are the transmitter's and are reused, not re-spelled.
CERTIFICATE_CONDITION_REASONS: Final[MappingProxyType[str, RefusalReason]] = (
    MappingProxyType(
        {
            "Psi = Psi^dag": RefusalReason.CERTIFICATE_NOT_HERMITIAN,
            "Psi^2 = Psi": RefusalReason.CERTIFICATE_NOT_IDEMPOTENT,
            "tr Psi = 1": RefusalReason.CERTIFICATE_TRACE_NOT_ONE,
            "tr Psi rounds nowhere": RefusalReason.CERTIFICATE_TRACE_NOT_ONE,
            "(SR1)": RefusalReason.CERTIFICATE_MARGINAL_IDENTITY_FAILS,
            "(SR2)": RefusalReason.CERTIFICATE_SIGNAL_IDENTITY_FAILS,
        }
    )
)

#: V1-V8 to the reason a refusal by that check carries. V7's entry is the
#: claims' own ``no_feasibility_witness``, which is why this map exists rather
#: than a mechanical ``f"check_{v}_failed"``.
CHECK_REFUSAL_REASONS: Final[MappingProxyType[str, RefusalReason]] = MappingProxyType(
    {
        "V1": RefusalReason.CHECK_V1_FAILED,
        "V2": RefusalReason.CHECK_V2_FAILED,
        "V3": RefusalReason.CHECK_V3_FAILED,
        "V4": RefusalReason.CHECK_V4_FAILED,
        "V5": RefusalReason.CHECK_V5_FAILED,
        "V6": RefusalReason.CHECK_V6_FAILED,
        "V7": RefusalReason.NO_FEASIBILITY_WITNESS,
        "V8": RefusalReason.CHECK_V8_FAILED,
    }
)

#: (C1)-(C5) and (S1)-(S4), each to the ONE reason a chain refusal names.
#:
#: THE NINE FINER SPELLINGS ARE NOT REASONS. A ``<family>_<identifier>_failed``
#: rule would give ``chain_condition_c1_failed`` ...
#: ``chain_condition_s4_failed``. NONE OF THEM IS IN THE
#: REFUSAL VOCABULARY: spec/modules/protocol-compiler/interface.yaml fixes
#: exactly one new spelling of its own, ``chain_interface_condition_failed``,
#: says so twice -- the ``chain_interface_conditions`` fail-closed row and
#: ``refusal_reasons.this_files_own_spelling`` -- and the ``refusal`` output
#: row says "The reason vocabulary is refusal_reasons below". THE INTERFACE'S
#: MACHINE KEYS ARE BINDING ON THIS IMPLEMENTATION, and a reason the interface
#: does not carry is a key a consumer cannot match.
#:
#: WHAT IS NOT LOST: the CONDITION. ``def:chaincond`` requires a failing chain
#: to be "refused, naming the condition", and ``thm:chain-consumption`` (i) says the
#: same; the refusal's ``detail`` names ``(C3)`` or ``(S2)`` in words and
#: :attr:`~certiqs_key.protocol_compiler.chain.ChainReport.failing_condition`
#: carries it as a datum beside the reason. The interface's own note says that
#: is what the naming requirement asks for: "both require that the refusal NAME
#: the failed condition, which this string plus the named condition does".
#:
#: (X1) IS ABSENT AND MUST STAY ABSENT: ``thm:chain-consumption`` (i) says it "is NOT
#: DECIDED, because it is not a condition on data: it is the type of the
#: record", and a misplaced link fails a DESCRIPTOR rule, never the order rule.
CHAIN_REFUSAL_REASONS: Final[MappingProxyType[str, RefusalReason]] = MappingProxyType(
    dict.fromkeys(
        ("C1", "C2", "C3", "C4", "C5", "S1", "S2", "S3", "S4"),
        RefusalReason.CHAIN_INTERFACE_CONDITION_FAILED,
    )
)

#: The nine spellings that are not reasons, kept as STRINGS so that a test can
#: assert that no member of :class:`RefusalReason` carries one. The same
#: pattern as :data:`~certiqs_key.protocol_compiler.gates.RETIRED_GATE_CASE_IDS`.
RETIRED_CHAIN_REFUSAL_REASONS: Final[tuple[str, ...]] = (
    "chain_condition_c1_failed",
    "chain_condition_c2_failed",
    "chain_condition_c3_failed",
    "chain_condition_c4_failed",
    "chain_condition_c5_failed",
    "chain_condition_s1_failed",
    "chain_condition_s2_failed",
    "chain_condition_s3_failed",
    "chain_condition_s4_failed",
)


@dataclass(frozen=True)
class Refusal:
    """The record under the machine key ``refusal``.

    ``reason`` is the machine-readable field and is the load-bearing one;
    ``detail`` names the offending datum in prose, for a human reading a
    refusal. A refusal is emitted INSTEAD OF a declaration, never beside one.
    """

    reason: RefusalReason
    detail: str

    def as_machine_record(self) -> dict[str, str]:
        """Return the refusal as a machine record."""
        return {"reason": str(self.reason), "detail": self.detail}


class GateVerdict(StrEnum):
    """The three values of the ``gate_report`` output row, and no fourth.

    ``PASSED_VACUOUSLY`` carries the space the claims write.
    ``rem:degenerate`` requires it in untrusted-source mode at any ``d_A`` --
    the entry type being already scalar by D(vi) -- and forbids reporting the
    vacuous pass "as evidence of anything".
    """

    PASSED = "passed"
    FAILED = "failed"
    PASSED_VACUOUSLY = "passed vacuously"


class ConditionOutcome(StrEnum):
    """The verdict of one interface condition of ``def:chaincond``.

    THIS MODULE'S SPELLING, not the claims' -- see the module docstring.
    ``NOT_CHECKED`` is the one that must never be confused with ``HOLDS``:
    A-LINK says the checks this module performs "are NECESSARY CONDITIONS AND
    NOT THE OBLIGATION", so where the data run out the record says
    ``not checked`` and NAMES the assumption, and the obligation is transferred
    rather than discharged.
    """

    HOLDS = "holds"
    FAILS = "fails"
    #: The condition quantifies over an empty list of links (thm:band-a (ii)).
    VACUOUS = "vacuous"
    #: Not decidable from the emitted data; an assumption is named beside it.
    NOT_CHECKED = "not checked"


class AssumptionId(StrEnum):
    """The SEVEN assumptions this module OWNS, in the interface ledger's order.

    THE INHERITED ROWS BELONG TO OTHER MODULES, SHORT IDS BEING
    REPOSITORY-WIDE: ``ass:seq`` (A-SEQ), ``ass:ens`` (A-ENS), A-SRC and the
    decoy submodule's A-WCP to the transmitter. This enum carries what this
    module's own claim files declare, and the inherited keys are READ OFF THE
    TRANSMITTER ARTEFACT rather than restated here -- which is why there is no
    member for any of them. Reductions' ``ass:recv`` (A-RECV) is no row of
    this ledger on any route (:data:`INHERITED_KEYS`). :data:`INHERITED_KEYS` names the
    inherited rows by machine key and :data:`INHERITED_NEVER_VERIFIED_KEYS`
    those of them nothing here may decide.

    The conditions the compiler decides form the definition
    ``def:well-formed-spec``; A-SPEC carries the apparatus clause and the
    key-rule clause; A-ALICE-MEAS is Alice's measurement where no
    source-replacement certificate is demanded.

    No assumption covers the restriction of the feasible set to
    sector-block-diagonal states: it is the remark ``rem:block-restriction``,
    which ``meat-core/thm:reduction``, step 1, proves. Nor is there one for the
    exact admissibility of the physical receiver family as presented: it is
    clause (iv) of ``def:well-formed-spec``, which the compiler decides on
    every route (``req:physical-family-decision``).
    """

    A_SPEC = "A-SPEC"
    #: Alice's per-round measurement where no source-replacement certificate
    #: is demanded (``ass:alice-meas``, refining A-SPEC). Emitted "wherever no
    #: source-replacement certificate is demanded (untrusted-source mode, or
    #: d_A = 1)".
    A_ALICE_MEAS = "A-ALICE-MEAS"
    A_RHOM = "A-RHOM"
    A_COIN = "A-COIN"
    A_LINK = "A-LINK"
    #: The attack-set licence, one file shared with the engine's A-ATK.
    A_ATK = "A-ATK"
    A_IDEAL = "A-IDEAL"


#: The ledger's machine keys, one per own assumption, transcribed from the
#: interface's `assumption_ledger.own_rows`.
#:
#: A-RHOM'S KEY IS ``round_homogeneity_declaration``, NOT ``round_homogeneity``:
#: machine keys are REPOSITORY-WIDE and ``receiver`` already owns that one for
#: its A-ROUND, as ``reductions`` owns ``round_homogeneity_squashing``.
#:
#: A-SPEC'S KEY NAMES WHAT THE ROW ASSERTS: that the declared data describe the
#: apparatus (the conditions the compiler decides are ``def:well-formed-spec``).
#:
#: A-ALICE-MEAS'S KEY IS NOT TIED TO UNTRUSTED-SOURCE MODE: its scope is
#: wherever no source-replacement certificate is demanded, d_A = 1 included.
ASSUMPTION_MACHINE_KEYS: Final[MappingProxyType[AssumptionId, str]] = MappingProxyType(
    {
        AssumptionId.A_SPEC: "specification_describes_apparatus",
        AssumptionId.A_ALICE_MEAS: "alice_measurement_as_declared",
        AssumptionId.A_RHOM: "round_homogeneity_declaration",
        AssumptionId.A_COIN: "public_choice_weights",
        AssumptionId.A_LINK: "reduction_chain_sound",
        AssumptionId.A_ATK: "attack_set_license",
        AssumptionId.A_IDEAL: "ideal_qubit_receiver",
    }
)

#: THE INHERITED ROWS, by the owner's short id and machine key: the
#: interface's ``assumption_ledger.inherited_rows``. Not members of
#: :class:`AssumptionId`, because this module does not own them; every one is
#: read off the transmitter artefact's own ledger.
#:
#: EACH KEY IS ITS OWNER'S, so one assumption travels under one key in a run
#: manifest that reads several ledgers. A-WCP is the decoy submodule's
#: (``transmitter/decoy/ass:wcp``), which its artefact carries in the place of
#: A-ENS.
#:
#: A-RECV (``reductions/ass:recv``) IS NO ROW OF THIS LEDGER, on any route
#: (the interface's ``assumption_ledger.a_recv_not_emitted_note``): this module
#: holds no receiver and no reductions artefact, so it can neither bind the
#: supplier's version nor tell an artefact the run built from one supplied
#: from outside. The row is the reductions artefact's own, emitted or omitted
#: there (``reductions/req:assumption-ledger``,
#: ``reductions/req:recv-row-provenance``).
INHERITED_KEYS: Final[MappingProxyType[str, str]] = MappingProxyType(
    {
        "A-SEQ": "sequential_round_model",
        "A-ENS": "source_ensemble",
        "A-SRC": "source_replacement_license",
        "A-WCP": "wcp_source_model",
    }
)

#: THE OWN ASSUMPTIONS NO CODE PATH OF THIS MODULE DECIDES BEYOND THEIR
#: CLAUSES ON THE DECLARED DATA, in the ledger's order: every member whose
#: ``verification`` header field is ``never`` (spec/claim-format.md section
#: 3.2), read from the shipped claim-closure table by machine key and not
#: listed here by hand. It is the interface's ``never_verified.own``.
#:
#: The conforming behaviour is: a PRESENCE TEST AND A PASS-THROUGH for A-ATK,
#: beside the type check of its licensed class;
#: for A-LINK, to decide the necessary conditions eq:pullback and the
#: transmitter's (S3) where the data make them decidable and to record
#: :attr:`ConditionOutcome.NOT_CHECKED`, NAMING A-LINK, where they do not; and
#: for A-SPEC, A-ALICE-MEAS, A-COIN, A-RHOM and A-IDEAL, to decide
#: what bears on the emitted data (the clauses of ``def:well-formed-spec``, the
#: declared weights, the refusal of an outcome-dependent weighting) and nothing
#: they say of the apparatus, the run or the physical receiver.
NEVER_VERIFIED: Final[tuple[AssumptionId, ...]] = tuple(
    identifier
    for identifier in AssumptionId
    if never_verified(ASSUMPTION_MACHINE_KEYS[identifier])
)

#: The INHERITED rows nothing here may decide, as their machine keys, in the
#: order of :data:`INHERITED_KEYS`: every inherited key whose assumption
#: carries ``verification: never``, read the same way. The transmitter's
#: attestations are passed through.
INHERITED_NEVER_VERIFIED_KEYS: Final[tuple[str, ...]] = tuple(
    key for key in INHERITED_KEYS.values() if never_verified(key)
)


def refusal_from_transmitter(refusal: TransmitterRefusal) -> Refusal:
    """Re-read a transmitter refusal in this module's vocabulary.

    ONE STRING, TWO ENUMS, AND THE CONVERSION IS EXPLICIT. Gate (G2)'s five
    certificate conditions and source-link admission's six reasons are owned
    by the transmitter. This module reuses those strings rather than spelling
    a second set. The two enums therefore carry the SAME string for the same
    condition, and this function crosses between them by that string -- never
    by position, and never by a table that could fall out of step.

    A :class:`KeyError`-style failure here would mean the two vocabularies had
    diverged, which is exactly what a test in tests/oracles/ holds them
    against; the constructor call below raises ``ValueError`` in that case
    rather than inventing a reason.
    """
    return Refusal(reason=RefusalReason(str(refusal.reason)), detail=refusal.detail)
