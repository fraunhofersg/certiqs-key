"""The ``receiver-povm`` oracle registry -- hand-derived golden values.

The implementation bands run under the freeze rule, in two instances each. **This
file is run A's output, in three passes.**

PASS 1: every value in the 0.1.3 sections below was derived BY HAND
from the accepted ``contract.tex`` 0.1.3 before any implementation existed.

PASS 2: the **0.2.0 AMENDMENT** section at the end was derived BY
HAND from the accepted ``contract.tex`` 0.2.0 before any code changed, in the
scoped implementation band the rulings opened. **NO FILE UNDER
``src/`` WAS CREATED OR MODIFIED BY EITHER PASS.** That pass is PURELY ADDITIVE:
not one 0.1.3 value is edited or deleted. Where the amendment invalidates a
0.1.3 case's input shape or expected value, or leaves its framing stale, the
case is MARKED in ``SUPERSEDED_BY_0_2_0`` with the contract site and its
replacement, and run B retires or rewrites it deliberately.

PASS 3: the **0.3.0 AMENDMENT** section was derived BY HAND from the
accepted ``contract.tex`` 0.3.0 before any code changed, in the two-instance
band the freeze rule requires. **NO FILE UNDER ``src/`` WAS
CREATED OR MODIFIED BY ANY OF THE THREE PASSES.** It is PURELY ADDITIVE in the
same sense, and in one respect more strictly so: it marks only WHOLE
module-level objects in ``SUPERSEDED_BY_0_3_0`` and NOT rows, because marking a
row would mean writing a ``superseded_by`` field an earlier pass froze. **NOT
ONE FROZEN NUMBER IS SUPERSEDED BY 0.3.0** -- no beta value, no p_mc, no window
minimum, no tail, no residual gap -- and the reason is the amendment's own
opt-in rule: a declaration carrying no ``exact_window`` depth emits exactly what
0.2.0 emits, forms no block above the cutoff, and does not invoke
Assumption ``ass:eig``. What IS marked is the set of objects that ENUMERATE the
interface: the input key tuple, the tolerance tuple, the reason vocabulary, the
assumption ledger, the residual presence rule and the def:tolmap tables.

In both passes run B is a different implementer instance, which writes the code
against these values and may read but not modify them. An expected value that
turns out to be wrong is a FINDING, reported and corrected deliberately with its
derivation, never edited in passing to make a test green.

WHY A SIBLING FILE AND NOT A NEW GROUP IN ``registry.py``
========================================================
``registry.py`` is "the ``meat-core`` oracle registry" and its integrity test
binds every entry's ``claims`` to ``meat-core``'s C1-C20;
``registry_statistics_acceptance.py`` and ``registry_protocol_compiler.py`` are
the same construction for SA1-SA9 and PC1-PC12. The claims pinned here are
RC1-RC12 of a FOURTH module at its own contract version, resolving in
``docs/mathematical-contracts/receiver-povm/interface.yaml``. So this is a PURE
INSERTION: a new module beside the other three, none of which is edited by so
much as a byte. ``KINDS`` and ``INADMISSIBLE_SOURCES`` are IMPORTED from
``registry.py`` rather than restated, so the registries cannot drift on what an
admissible oracle is.

NUMERIC REPRESENTATION, AND THE RATIONALE FOR IT
================================================
Every value in this file is EXACT. Not one float appears, and not one tolerance
is invented. Four facts of the contract force that, and the fourth is the one
that decides the hard cases.

1. THE MATHEMATICS IS EXACT AND THE EVALUATION IS NOT, and the contract
   separates them explicitly. Theorem ``thm:exact-and-evaluated`` (i): "Every statement of
   Sections 4.1-4.8 and 4.10-4.12 is an identity or inequality between EXACTLY
   SPECIFIED QUANTITIES; NONE OF THEM CONTAINS AN ERROR TERM, A TOLERANCE, OR A
   NUMERICAL HYPOTHESIS." Theorem ``thm:exact-and-evaluated`` (ii) then says the version-1
   EVALUATION is floating point (Definition ``def:evaluation-model``; Section 2.5
   ``numerics``; the emitted ``bound_evaluation: floating_point``). An oracle
   pins the STATEMENT, not the evaluation, so it is exact or it is pinning the
   wrong object.

2. TOLERANCES ARE A DECLARED INPUT, NEVER A DEFAULT. Section 2.1's
   ``numerical_tolerances`` row: the four residual bounds, the gap bound and the
   branch margin are "DECLARED, NEVER DEFAULTED", because "without them the
   ``fail_closed`` convention has no threshold to test". Definition
   ``def:residuals`` compares each residual "against A DECLARED numerical
   tolerance", and predicate (C) of Definition ``def:pmc`` tests against "THE
   DECLARED margin". A frozen expected value that carried a tolerance of its own
   would therefore invent the one input the contract insists on being given. The
   single tolerance object in this file is ``TOLERANCE_FIXTURE``, and it is
   documented and used AS A FIXTURE PLAYING THE ROLE OF THAT DECLARED INPUT --
   never as a property of a frozen number.

3. WHERE THE CLOSED FORM IS EXACT, IT IS FROZEN EXACTLY, as a
   ``fractions.Fraction``. That covers Gram entries, block dimensions, ranks,
   the deficiency identity, ``r_min``, the dark-count matrices, the bound
   function ``beta(n)``, the window and tail quantities, the residual gap, and
   ``p_mc`` at every configuration frozen here -- all of them rational at the
   parameters chosen.

4. WHERE AN AMPLITUDE IS IRRATIONAL, IT IS STILL FROZEN EXACTLY, IN A RING THAT
   CONTAINS IT. This is the case the contract makes unavoidable: a 50:50
   beamsplitter has amplitudes ``1/sqrt2`` while its port GRAMS are rational
   (Theorem ``thm:representation-independence`` (i) is exactly the statement that only the Grams are
   observable), a half-wave plate carries the physical phase
   ``exp(-i delta / 2) = -i`` that Section 2.5 ``waveplate_convention`` forbids
   dropping, and the two-photon block of the Fock functor carries ``sqrt2``
   factors from the normalization of the symmetrized basis vector ``|1,1>``.
   EVERY ONE OF THOSE LIES IN ``Q[sqrt2] + i Q[sqrt2]``, which is a field,
   closed under the operations Eq. ``eq:gramdef`` needs. So a scalar here is an
   exact pair of pairs of ``Fraction``:

       Q2  = (p, q)        meaning  p + q * sqrt(2)
       Alg = (re, im)      each a Q2, meaning  re + i * im

   PARAMETERS WERE CHOSEN TO MAKE THIS SMALL, NOT TO DODGE IT. Beamsplitters are
   frozen at ``x = 9/25`` (so ``sqrt(x) = 3/5`` and ``sqrt(1-x) = 4/5`` are
   rational) AND at ``x = 1/2`` (where they are not, and the ``sqrt2`` is
   carried); rotations at ``cos = 3/5, sin = 4/5``; and the BB84 receiver at
   ``p_Z = 1/2``, where the instrument matrix carries ``sqrt2`` and ``i`` and
   the Grams are rational. NOTHING IS APPROXIMATED ANYWHERE.

THE ONE PLACE A TOLERANCE APPEARS, AND WHAT IT IS
=================================================
Definition ``def:residuals`` writes ``r_1``, ``r_3`` and ``r_4`` with an
UNQUALIFIED matrix norm and names none. That is recorded in ``interface.yaml``
as open implementation choice OIC-3 and is NOT decided here. The consequence for
this file is precise and is honoured entry by entry:

* every PASSING residual is frozen as EXACTLY ZERO, which is norm-independent;
* every FAILING residual is frozen under BOTH natural readings -- the spectral
  norm and the squared Frobenius norm, both exact rationals on the frozen
  matrices -- so that THE REFUSAL VERDICT IS FROZEN WHILE THE NUMBER IS NOT;
* the verdict is taken against ``TOLERANCE_FIXTURE``, and every failing case
  fails under both readings, so no verdict depends on the undecided choice.

ADMISSIBILITY (ADR-0003)
========================
No MATLAB, OpenQKDSecurity, CVX, MOSEK or Julia value is admissible and none is
used; the guard is asserted against ``INADMISSIBLE_SOURCES``. Every number below
is an exact closed form or a hand-computed rational. THE ONLY MATHEMATICAL
SOURCE IS ``contract.tex``: the 0.1.3 sections were derived from 0.1.3 at sha256
3b9eaabe80b0cc5c6b0e755abe5e0e64d40226e583036d1ad6fa7904bb10c7a0, the 0.2.0
AMENDMENT section from 0.2.0 at sha256
7482735f1386e33510b7d6f013f2157cdc9d455b5c92412509207021616f80c8, and the 0.3.0
AMENDMENT section from 0.3.0 at sha256
3b8853f6ba77e1f90a76350fb2537656ce31c694884e1769b9a7e9fd67028f45 (git blob
8349493327284fdeeb8343f9a9a2456d61556a90), each superseding the one before it.

WHAT THIS REGISTRY DOES NOT DO
==============================
It does not certify anything. Section 1.3 of that contract says the ceiling is
NOT REACHED in version 1 -- "the module therefore emits ``bound_evaluation:
floating_point`` on every artifact, and a ``certified`` request that depends on
a compiled receiver falls back to ``estimate``" -- and Theorem ``thm:exact-and-evaluated`` (iii)
adds "NO PATH IN THIS MODULE CAN PRODUCE A ``certified`` LABEL". ``ASSURANCE``
below is the ORACLE's own evidential status and is ``estimate`` for every entry.
The tier ceiling in STATUS.yaml (``certified``) is an ELIGIBILITY statement
about the mathematics and is not a property any value here has.

It also does not implement the module. No function in this file compiles a
graph, builds a POVM, evaluates a bound, applies an efficiency or conditions on
a probe. Every frozen field is a LITERAL; the only functions are the exact
arithmetic of ``Q[sqrt2] + i Q[sqrt2]``, which exists so that the integrity
tests can CHECK a frozen Gram against a frozen instrument matrix through
Eq. ``eq:gramdef`` rather than take both on trust, and so that a reader can see
that ``sqrt2`` is carried and not rounded.

THE SPELLING TRAP
=================
AT 0.1.3 the contract named EXACTLY ONE machine-readable reason string verbatim,
and only that one is frozen as a string in the 0.1.3 sections:
``receiver_grams_not_enclosed`` (Theorem ``thm:exact-and-evaluated`` (iii); Section 1.3).

AT 0.2.0 Section 2.6 ("Refusal rules with a named reason string") spells FIVE
refusal reasons and names that sixth string beside them as a TIER FALLBACK
rather than a refusal. All six are frozen in ``REASON_VOCABULARY_0_2_0`` and
nowhere else, and ``REFUSAL_REASONS_VERBATIM`` -- the 0.1.3 one-element tuple --
is MARKED in ``SUPERSEDED_BY_0_2_0`` rather than edited.

AT 0.3.0 that table has EIGHT refusal rows: the five of 0.2.0 unchanged plus
``exact_window_declared_without_required_tolerance``,
``exact_window_depth_outside_declared_range`` and
``window_eigenvalue_consistency_residual_above_tolerance``. All nine strings --
the eight refusals and the unchanged tier fallback -- are frozen in
``REASON_VOCABULARY_0_3_0``, and ``REFUSAL_REASONS_VERBATIM_0_2_0`` and
``REASON_VOCABULARY_0_2_0`` are MARKED in ``SUPERSEDED_BY_0_3_0`` rather than
edited.

IN THIS REPOSITORY THE NINTH STRING IS NOT IN THE CODE, the ``certified`` tier
that reached it having been dropped by ``PRINCIPLES.md`` section 10. Nothing
above is rewritten for that -- it records the contract as frozen -- and the
hand edit is an ADDITION at ``REASON_VOCABULARY_0_3_0``:
``REASON_VOCABULARY_RECEIVER_0_1_2`` and
``RETIRED_FROM_THE_CODE_RECEIVER_0_1_2``, with the reason written at them.

THE UNSPELLED LIST GROWS TOO, from six sites to SEVEN, and the seventh
is not in Section 2.6's preamble: ``def:tolmap`` (iv) now states that its
failure is a refusal under ``fail_closed`` -- which 0.2.0 omitted -- and
DELIBERATELY ADDS NO STRING, "because fixing a contract-verbatim key here would
settle an interface detail that no claim of this contract consumes". None is
invented here; ``REF-TOLMAP-IV-C-REFUSED-NO-SPELLING`` freezes the verdict, the
threshold and the fail-closed consequence and freezes no key.

EVERYWHERE ELSE, AT BOTH VERSIONS, what is frozen is the naming OBLIGATION
(Section 2.5 ``fail_closed``: "a refusal with a machine-readable reason and NO
artifact") and the IDENTITY of the failing check -- (E1), (E2), (E3), (D1),
(D2), the residuals, predicate (X) -- never an invented spelling. Section 2.6's
own preamble enumerates six further refusals that refuse "WITH A REASON STRING
THE IMPLEMENTER NAMES", and they are frozen without one in
``REFUSALS_NAMED_WITHOUT_A_SPELLING``.

Two REASON PHRASES are carried as prose because that is how the contract
writes them, in its own quotation marks: "parameter uncertainty sets
are out of scope" (Section 2.4) and the ``calibration_coverage`` statement
(Section 2.2). They are marked as prose and are not machine keys.

WHAT IS PINNED, BY GROUP
========================
RP-A  RC1  the Fock functor on the 0-, 1- and 2-photon sectors of a two-mode
           contraction, diagonal and non-diagonal; the photon-number grading and
           block dimensions; the OCCUPATION-VECTOR BASIS ORDER and the index
           reversal it causes; the projector case; the spectrum and its two
           attained bounds
RP-B  RC2  a declared graph compiled to its instrument matrix; the same graph
           under two linear extensions and under a layering; a graph whose EDGE
           is what fixes the order; one refusal each for (E1), (E2), (E3) with
           the failing condition named; the contraction property; isometry iff
           lossless, both ways
RP-C  RC3  every catalogue entry C1-C10 at an interior and a boundary parameter
           tuple with its lossless verdict; the retarder's KEPT phase and the
           dropped-phase variant beside it; the beamsplitter real at phi = 0
           with det = -1; the 50:50 case whose Gram is rational though its
           amplitudes are not; the symmetric-convention comparison of
           rem:bsconv, exactly, which is change request CR-3's evidence
RP-D  RC4  two hand-computed instruments and their Grams; admissibility, the
           rank bound and the deficiency; the sub-unitary description and its
           unitary dilation with a vacuum ancilla giving IDENTICAL Grams
RP-E  RC5  two distinct instrument matrices with the same Grams; a rank-one
           family that a one-mode-per-port device reproduces and a rank-two port
           that it does not; the realizing instrument A_k^{1/2}; the extinction
           criterion
RP-F  RC6  the click-pattern blocks M_S^{(n)} for n = 0, 1, 2 of two receivers;
           positivity, completeness and block-diagonality per block; the
           n-photon block, its spectrum, and the inclusion-exclusion identities
RP-G  RC7  a declared surjective coarse-graining and a second one on the same
           receiver; the coarse blocks; additivity; and the one-directional
           losslessness with the contract's own counterexample
RP-H  RC8  p_mc at small cutoffs where it is exact, including one receiver where
           it is ZERO and one where it is POSITIVE; the quantifier domain;
           predicate (X) at a probe-free receiver and a probe-off setting;
           PREDICATE (C) SHOWN UNREACHABLE (change request CR-4); branch 2 with
           its window, tail and residual gap at a probe-on setting; the
           refusals; the strengthening slot
RP-I  RC9  the four residual identities passing and failing; the certified ->
           estimate fallback with its verbatim reason; bound_evaluation
RP-J  RC10 the efficiency substitution and rank preservation; a non-uniform
           attenuation that lowers rank; the single structural site and the
           D_eta second summand; the efficiency record; the deficiency identity
           against a path-product audit that disagrees; the decibel conversion
RP-K  RC11 the per-port dark-count matrix at K = 2 and K = 3 in full;
           column-stochasticity, monotonicity, multiclick absorption; r_min WITH
           the no-click column and the wrong value without it; the improved
           bound; a non-monotone R refused
RP-L  RC12 a thermal-probe conditioning case in closed form, prefactors and
           Schur-complement effective Grams; the vacuum probe reproducing the
           unconditioned Grams; completeness of the conditional family at fixed
           t; Fock-diagonality by construction
RP-M  the interface: the two-route refusal, the non-zero tolerance refusal, the
           out-of-domain refusal, the mirror-handedness default, the
           subsystem_order precedence case, the outcome alphabet, and the
           receiver_construction presence rule on all three routes

AND, IN THE 0.2.0 AMENDMENT SECTION:

RP-N  RC9  the FIFTH residual r_5: the Hermiticity-and-positivity defect of an
           emitted block, on a Hermiticity defect and on a negative eigenvalue,
           refused; on two blocks the artifact really emits, where it is exactly
           zero; the expectation bounds of prop:res5 (iii) at vectors that
           attain them; and which residuals exist on which input route
RP-O  RC9  the declared tolerance domain [0, 1) at both endpoints; and
           def:tolmap item by item -- Gram admissibility and the eps_2-rank rule
           at eps_2 with BOTH directions of its two-sided cutoff, the unclamped
           c at eps_2 with BOTH parities of rem:cdirection, and route-(ii)
           contractivity and C10's (E1) at eps_1 with the identity eq:r1islmax
RP-P  RC11 the dark-count slack: r_min unmodified, the capped coefficient rbar,
           delta_dc by route; the composed eq:darkpmcslack on both routes,
           including rem:d2slack's witness channel at the BB84 receiver of
           ex:bb84bound; (D1) and (D2) admit/refuse pairs; route exclusivity
RP-Q  RC8  the (X)-only branch selector, both clauses; the collapse slack
           sigma = -beta(0), never positive, over every frozen bound-data case;
           and the one refusal def:pmc now states
RP-R  ---  Section 2.6 as a key vocabulary: five verbatim refusal reasons, the
           tier-fallback string, and the six refusals named WITHOUT a spelling

AND, IN THE 0.3.0 AMENDMENT SECTION:

RP-S  RC8  the exact block quantity beta*(n) of def:exactbnd, computed by hand
           from the constructed receiver: the BB84 two-photon block at three
           values of p_Z and the three-photon block at one, where the sqrt3
           cancels exactly; the one-dimensional channel spaces where
           beta* = beta and the window buys nothing; and rem:exactpositivity's
           counterexample, where beta* = -3 and the two halves of
           lem:exactbasic come apart
RP-T  RC8  lem:exactwindow's composite on admissible reals, including both P = 0
           branches and the upper limit P = 1; the emitted eq:pmcex at thirteen
           declarations on both branches, with the empty middle minimum, the
           outer maximum, the analytic floor and the analytic remainder each
           binding somewhere; prop:exactnoworse case by case with the one step
           of its proof that does not survive an evaluation; the settings mixed
           in one declaration; and the OPT-IN invariant over every frozen
           bound-data case
RP-U  RC9  the sixth residual r_6: its exact value 0, its request-dependent
           presence rule beside the route-dependent one, refusals over indices
           and over settings, an undershoot admitted inside eps_6 -- and,
           frozen as a PASS, the one direction it is BLIND to, with the
           over-large lower bound a violated ass:eig then emits
RP-V  RC8+RC9  the exact window's input validation: both depth constraints with
           their boundaries admitted, the conditional requirement on eps_eig and
           eps_6, and the three verbatim reason strings Section 2.6 adds
RP-W  RC9  def:tolmap (iv) decides c ALONE: the band eq:tolmapband bracketed on
           both sides, its half-open right endpoint, its emptiness at
           eps_1 = eps_2, the four derivation steps, the quantitative cost of
           the losing reading, and the refusal the contract deliberately leaves
           UNSPELLED

CHANGE-REQUEST CANDIDATES: see ``CHANGE_REQUEST_CANDIDATES`` (the 0.1.3 pass),
``CHANGE_REQUEST_CANDIDATES_0_2_0`` and ``CHANGE_REQUEST_CANDIDATES_0_3_0`` at
the end of this module, each of which names every candidate and the reading
taken. NONE OF THE THREE ROUTES A CHANGE REQUEST AGAINST AN ACCEPTED CONTRACT
that is still open. The 0.3.0 list carries ONE item that is not a candidate at
all and is labelled so: an OBSERVATION about the tree, routed to the driver --
contract.tex's own contract-version macro still reads ``0.3.0-draft`` after
the G3 signature, where STATUS.yaml reads ``contract_version: 0.3.0``. Dropping
the suffix is the typographic correction permitted in
place and this module executed at both previous signatures; this freeze binds
the ACCEPTED version on STATUS.yaml's authority and reports the residue rather
than editing a contract frozen at G3. See ``CONTRACT_VERSION_RESIDUE_0_3_0``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as F

from registry import INADMISSIBLE_SOURCES, KINDS

__all__ = [
    "ADDITIVITY_CASES",
    "ALL_CLAIMS",
    "AMENDMENT_SPEC_VERSION_MARKER",
    "AMENDMENT_SPEC_VERSION_MARKER_0_3_0",
    "ASSUMPTION_ROWS",
    "ASSUMPTION_ROWS_0_3_0",
    "ASSURANCE",
    "A_EIG_WITNESS",
    "BB84_EXACT_BLOCK_FORM",
    "BETA_ZERO_AND_C_SLACK",
    "BOUND_DATA_CASES",
    "BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0",
    "BOUND_EVALUATION_RIGOROUS",
    "BOUND_EVALUATION_V1",
    "CATALOGUE_CASES",
    "CATALOGUE_IDS",
    "CHANGE_REQUEST_CANDIDATES",
    "CHANGE_REQUEST_CANDIDATES_0_2_0",
    "CHANGE_REQUEST_CANDIDATES_0_3_0",
    "CLAIM_IDS",
    "COARSE_GRAINING_CASES",
    "COHERENT_BREAK",
    "COLLAPSE_SLACK_CASES",
    "COLLAPSE_SLACK_COUNTS",
    "COMPILE_CASES",
    "CONDITIONAL_COMPLETENESS_CASES",
    "CONTRACT_VERSION_RESIDUE_0_3_0",
    "CONVENTION_KEYS",
    "CONVENTION_KEYS_0_2_0",
    "CONVENTION_KEYS_0_3_0",
    "C_DIRECTION_BOUNDS",
    "C_DIRECTION_CASES",
    "D2_SLACK_CASES",
    "DARK_CASES",
    "DARK_COMPOSITION_N2",
    "DARK_IMPROVEMENT_CASES",
    "DARK_ROUTE_EXCLUSIVITY_CASES",
    "DARK_SLACK_CASES",
    "DECIBEL_CONVERSIONS",
    "D_ETA_CASES",
    "EFFICIENCY_CASES",
    "EFFICIENCY_RECORD",
    "ENCLOSURE_DIRECTIONS",
    "EXACTBASIC_HALVES",
    "EXACT_BLOCK_CASES",
    "EXACT_COMPOSITE_CASES",
    "EXACT_WINDOW_ADMISSIBLE_CHOICES",
    "EXACT_WINDOW_BRANCH_REMAINDERS",
    "EXACT_WINDOW_CASES",
    "EXACT_WINDOW_VALIDATION_CASES",
    "EXTINCTION_CASES",
    "FOCK_CASES",
    "HALF_R2",
    "INADMISSIBLE_SOURCES",
    "INCLUSION_EXCLUSION_CASES",
    "INPUT_KEYS",
    "INPUT_KEYS_0_3_0",
    "INPUT_ROUTES",
    "INSTRUMENT_CASES",
    "KINDS",
    "MATHEMATICAL_SPEC_VERSION_0_2_0",
    "MATHEMATICAL_SPEC_VERSION_0_3_0",
    "MATHEMATICAL_SPEC_VERSION_RECEIVER_0_1_2",
    "MINUS_I",
    "MIXED_SETTING_CASES",
    "MODE_ORDER_CASES",
    "NEVER_VERIFIED_0_3_0",
    "NOSLACK_STATEMENTS",
    "NOT_SUPERSEDED_BY_0_2_0",
    "NOT_SUPERSEDED_BY_0_3_0",
    "NO_WORSE_CASES",
    "NO_WORSE_UNDER_EVALUATION",
    "ONE_MODE_PER_PORT_CASES",
    "OPT_IN_INVARIANT",
    "OUTCOME_ALPHABET",
    "OUTPUT_KEYS",
    "OUTPUT_KEYS_0_3_0",
    "OUTPUT_PRESENCE",
    "PATH_PRODUCT_CASES",
    "PENDING_RETIREMENT_AT_RUN_B",
    "PENDING_RETIREMENT_AT_RUN_B_0_3_0",
    "PMC_BRANCH_CASES",
    "PMC_X_CLAUSE_CASES",
    "POVM_BLOCK_CASES",
    "POVM_DEFECT_UNDER_WIDENED_D1",
    "PROBE_CASES",
    "Q2",
    "R2",
    "REASON_EMITS_ARTIFACT",
    "REASON_EMITS_ARTIFACT_0_3_0",
    "REASON_VOCABULARY_0_2_0",
    "REASON_VOCABULARY_0_3_0",
    "REASON_VOCABULARY_RECEIVER_0_1_2",
    "RECEIVER_CONSTRUCTION_PRESENCE",
    "REFUSALS_NAMED_WITHOUT_A_SPELLING",
    "REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0",
    "REFUSAL_CASES",
    "REFUSAL_CASES_0_2_0",
    "REFUSAL_CASES_0_3_0",
    "REFUSAL_REASONS_ADDED_AT_0_3_0",
    "REFUSAL_REASONS_VERBATIM",
    "REFUSAL_REASONS_VERBATIM_0_2_0",
    "REFUSAL_REASONS_VERBATIM_0_3_0",
    "REPRESENTATION_INDEPENDENCE_CASES",
    "RES5_EXPECTATION_CASES",
    "RESIDUAL5_CASES",
    "RESIDUAL6_CASES",
    "RESIDUAL6_REQUEST_PRESENCE",
    "RESIDUAL_CASES",
    "RESIDUAL_NORM_0_2_0",
    "RESIDUAL_ROUTE_PRESENCE",
    "RESIDUAL_SCOPING_0_3_0",
    "RETIRED_FROM_THE_CODE_RECEIVER_0_1_2",
    "RMIN_TRAP_CASES",
    "RP_ORACLES",
    "SLOT_RECORD",
    "SUPERSEDED_BY_0_2_0",
    "SUPERSEDED_BY_0_3_0",
    "THERMAL_OCCUPATION_WEIGHTS",
    "TIER_CASES",
    "TIER_FALLBACK_REASON_VERBATIM",
    "TOLERANCES_ALWAYS_REQUIRED_0_3_0",
    "TOLERANCES_CONDITIONALLY_REQUIRED_0_3_0",
    "TOLERANCES_UNUSED_ON_ROUTE_I",
    "TOLERANCE_DOMAIN",
    "TOLERANCE_DOMAIN_CASES",
    "TOLERANCE_DOMAIN_CLOSED_AT",
    "TOLERANCE_DOMAIN_DEGENERACIES",
    "TOLERANCE_FIXTURE",
    "TOLERANCE_FIXTURE_0_2_0",
    "TOLERANCE_FIXTURE_0_3_0",
    "TOLERANCE_UPPER_BOUND_CONSUMERS",
    "TOLMAP_II_RANK_CASES",
    "TOLMAP_ITEMS",
    "TOLMAP_IV_BAND",
    "TOLMAP_IV_BAND_CLOSED_AT",
    "TOLMAP_IV_BAND_COST",
    "TOLMAP_IV_BAND_EMPTY_AT_EQUAL_EPS",
    "TOLMAP_IV_BAND_FIXTURE",
    "TOLMAP_IV_C_CASES",
    "TOLMAP_IV_DERIVATION",
    "TOLMAP_IV_NO_BEHAVIOUR_CHANGE",
    "TOLMAP_IV_PRECEDENCE_CASES",
    "TOLMAP_I_CASES",
    "TOLMAP_NOT_A_TEST_0_3_0",
    "TOLMAP_OTHER_VALIDATION_KINDS",
    "TOLMAP_OTHER_VALIDATION_KINDS_0_3_0",
    "TOLMAP_RESIDUALS_ALREADY_COUNTED",
    "TOLMAP_V_CONTRACTIVITY_CASES",
    "WINDOW_REQUIREMENT_CASES",
    "Alg",
    "AssumptionRow",
    "BoundDataCase",
    "CatalogueCase",
    "CoarseGrainingCase",
    "CompileCase",
    "DarkCase",
    "DarkSlackCase",
    "EfficiencyCase",
    "ExactBlockCase",
    "ExactCompositeCase",
    "ExactWindowCase",
    "ExactWindowValidationCase",
    "FockCase",
    "InstrumentCase",
    "Mat",
    "MixedSettingCase",
    "ModeOrderCase",
    "POVMBlockCase",
    "ProbeCase",
    "RPOracleEntry",
    "RefusalCase",
    "RepresentationCase",
    "Residual5Case",
    "Residual6Case",
    "ResidualCase",
    "Supersession",
    "Supersession0_3_0",
    "ToleranceDomainCase",
    "TolmapCase",
    "TolmapPrecedenceCase",
    "alg",
    "alg_add",
    "alg_conj",
    "alg_mul",
    "im_",
    "is_superseded",
    "is_superseded_0_3_0",
    "mat_real",
    "q2",
    "q2_add",
    "q2_mul",
    "q2_neg",
    "rp_oracle",
    "rt",
    "supersession",
    "supersession_0_3_0",
]

#: The ORACLE's own evidential tier. ``estimate`` for every entry: Theorem
#: thm:exact-and-evaluated (iii) says "no path in this module can produce a ``certified``
#: label", and agreement with an oracle is not a runtime check in any case.
ASSURANCE = "estimate"

#: The ONE machine-readable reason string contract.tex spells. Theorem
#: thm:exact-and-evaluated (iii); Section 1.3. No second string is frozen anywhere in this file.
REFUSAL_REASONS_VERBATIM: tuple[str, ...] = ("receiver_grams_not_enclosed",)


# ===========================================================================
#  Exact arithmetic in Q[sqrt2] + i Q[sqrt2]
# ===========================================================================
#
#  A Q2 is the pair (p, q) standing for p + q * sqrt(2), with p and q exact
#  rationals. An Alg is the pair (re, im) of Q2s, standing for re + i * im. A
#  Mat is a tuple of tuples of Algs.
#
#  These functions are NOT an implementation of anything in the contract. They
#  are field arithmetic, and they exist for exactly one purpose: so that
#  test_receiver_povm_registry.py can verify a frozen Gram against a frozen
#  instrument matrix through Eq. eq:gramdef, and a frozen r_min against a frozen
#  dark-count matrix through Eq. eq:rmin, rather than take both on trust. No
#  function here multiplies matrices, diagonalizes anything, or evaluates a
#  bound; the tests assemble what they need from these scalars.

Q2 = tuple[F, F]
Alg = tuple[Q2, Q2]
Mat = tuple[tuple[Alg, ...], ...]


def q2(p: int | F = 0, q: int | F = 0) -> Q2:
    """Return the exact element ``p + q * sqrt(2)`` of ``Q[sqrt2]``."""
    return (F(p), F(q))


def alg(re: Q2 | int | F = 0, im: Q2 | int | F = 0) -> Alg:
    """Return the exact element ``re + i * im`` of ``Q[sqrt2] + i Q[sqrt2]``."""
    return (
        re if isinstance(re, tuple) else q2(re),
        im if isinstance(im, tuple) else q2(im),
    )


def rt(p: int | F = 0, q: int | F = 0) -> Alg:
    """Shorthand for the REAL element ``p + q * sqrt(2)``."""
    return alg(q2(p, q))


def im_(p: int | F = 0, q: int | F = 0) -> Alg:
    """Shorthand for the PURELY IMAGINARY element ``i * (p + q * sqrt(2))``."""
    return alg(q2(), q2(p, q))


def q2_add(a: Q2, b: Q2) -> Q2:
    return (a[0] + b[0], a[1] + b[1])


def q2_mul(a: Q2, b: Q2) -> Q2:
    # (p + q r2)(s + t r2) = (p s + 2 q t) + (p t + q s) r2, with r2^2 = 2.
    return (a[0] * b[0] + 2 * a[1] * b[1], a[0] * b[1] + a[1] * b[0])


def alg_add(a: Alg, b: Alg) -> Alg:
    return (q2_add(a[0], b[0]), q2_add(a[1], b[1]))


def q2_neg(a: Q2) -> Q2:
    return (-a[0], -a[1])


def alg_mul(a: Alg, b: Alg) -> Alg:
    real = q2_add(q2_mul(a[0], b[0]), q2_neg(q2_mul(a[1], b[1])))
    imag = q2_add(q2_mul(a[0], b[1]), q2_mul(a[1], b[0]))
    return (real, imag)


def alg_conj(a: Alg) -> Alg:
    return (a[0], q2_neg(a[1]))


def mat_real(rows: tuple[tuple[int | F, ...], ...]) -> Mat:
    """Assemble a matrix all of whose entries are exact RATIONALS."""
    return tuple(tuple(rt(value) for value in row) for row in rows)


#: sqrt(2) / 2 = 1 / sqrt(2), exactly. The 50:50 beamsplitter amplitude, and the
#: normalization of the symmetrized two-photon basis vector |1,1>.
HALF_R2: Alg = rt(0, F(1, 2))

#: -i, exactly. The retarder phase exp(-i delta / 2) at delta = pi
#: (Eq. eq:retarder; Section 2.5 `waveplate_convention`), and the factor an
#: implementation that writes HWP as a real matrix silently drops.
MINUS_I: Alg = im_(-1)

#: sqrt(2), exactly. It appears in the two-photon block of the Fock functor,
#: from the normalization of |1,1>, and nowhere else in this file.
R2: Alg = rt(0, 1)


# ===========================================================================
#  The declared numerical tolerances, AS A FIXTURE
# ===========================================================================
#
#  THIS IS NOT A PROPERTY OF ANY FROZEN VALUE. Section 2.1's
#  `numerical_tolerances` row makes the four residual bounds, the gap bound and
#  the branch margin a DECLARED INPUT that is "declared, never defaulted"; a
#  frozen expected value that carried a tolerance of its own would invent that
#  input. Everything below that is a NUMBER is exact and needs no tolerance at
#  all. What DOES need one is a VERDICT: "residual r_3 above tolerance, so the
#  request is refused" is a statement about a declared threshold, and this
#  object plays the role of the declaration that supplies it.
#
#  The values are round rationals chosen only so that a reader can see the
#  verdicts do not turn on them: every frozen PASSING residual is exactly zero
#  and every frozen FAILING residual exceeds its bound by at least two orders of
#  magnitude, under either reading of the unnamed matrix norm (OIC-3).
#
#  eps_hyp is included and is STRICTLY POSITIVE because Definition def:pmc
#  requires it so ("eps_hyp > 0", and "a declaration supplying no eps_hyp ... is
#  refused rather than defaulted") -- and because the requirement is
#  UNCONDITIONAL, so even the probe-free cases frozen here must carry one. See
#  CHANGE_REQUEST_CANDIDATES: no frozen value is computed through the predicate
#  it is the margin for, because that predicate cannot fire.
TOLERANCE_FIXTURE: dict[str, F] = {
    "eps_1": F(1, 1000),
    "eps_2": F(1, 1000),
    "eps_3": F(1, 1000),
    "eps_4": F(1, 1000),
    "eps_gap": F(1, 100),
    "eps_hyp": F(1, 1000),
}


# ===========================================================================
#  The registry entry, and the case records
# ===========================================================================


@dataclass(frozen=True)
class RPOracleEntry:
    """One frozen expected value with the derivation that produced it.

    The field set mirrors ``registry.OracleEntry`` and its two siblings; the
    alpha-dependent fields are dropped, no claim of this contract depending on
    the Renyi order (Section 2.5, second bullet, which says this contract
    "states no Renyi quantity, imports no alpha-dependent fact, and therefore
    intersects the domain with nothing").
    """

    oracle_id: str
    claims: tuple[str, ...]
    kind: str
    subject: str
    derivation: str
    #: Single golden value where there is one; the case tuples carry the rest.
    value: F | int | str | None = None
    #: Hypotheses a consuming theorem carries that must hold for this entry.
    hypotheses: tuple[str, ...] = field(default_factory=tuple)
    assurance: str = ASSURANCE
    #: "0.2.0" where the amendment marks this entry; see SUPERSEDED_BY_0_2_0.
    superseded_by: str | None = None


def rp_oracle(oracle_id: str) -> RPOracleEntry:
    """Return the registry entry with the given ``oracle_id``."""
    for entry in RP_ORACLES:
        if entry.oracle_id == oracle_id:
            return entry
    raise KeyError(f"no oracle entry {oracle_id!r}")


@dataclass(frozen=True)
class FockCase:
    """One frozen photon-number block of the functor Fock (Def. def:fock)."""

    case_id: str
    mode_labels: tuple[str, ...]
    #: The operator X on the MODE space, rows and columns in mode order.
    operator: Mat
    photon_number: int
    #: Occupation vectors in the lexicographic order of Section 2.5.
    basis_order: tuple[tuple[int, ...], ...]
    #: Fock(X) restricted to that block, in that basis order.
    block: Mat
    #: The exact eigenvalues, where the operator is normal and they are known.
    spectrum: tuple[F, ...] | None
    derives_from: str


@dataclass(frozen=True)
class CompileCase:
    """One declared element graph and what it compiles to (Thm. thm:compilation-well-defined)."""

    case_id: str
    mode_labels: tuple[str, ...]
    #: (element name, catalogue entry id, support as mode indices, parameters).
    elements: tuple[tuple[str, str, tuple[int, ...], str], ...]
    edges: tuple[tuple[str, str], ...]
    #: Every linear extension of the graph, by element name.
    linear_extensions: tuple[tuple[str, ...], ...]
    #: The compiled matrix, or None when the graph is refused.
    compiled: Mat | None
    #: None when the graph is well formed; else "E1", "E2" or "E3".
    refused_condition: str | None
    lossless: bool | None
    derives_from: str


@dataclass(frozen=True)
class CatalogueCase:
    """One catalogue entry at one parameter tuple (Table tab:catalogue)."""

    case_id: str
    entry_id: str
    #: "interior" or "boundary" of the declared parameter domain.
    position: str
    parameters: str
    matrix: Mat
    lossless: bool
    #: The determinant, where the contract states it (C1 only).
    determinant: Alg | None
    derives_from: str


@dataclass(frozen=True)
class InstrumentCase:
    """One receiver instrument and its port Grams (Def. def:gram)."""

    case_id: str
    input_mode_labels: tuple[str, ...]
    output_mode_labels: tuple[str, ...]
    #: Port label -> the output-mode indices it collects.
    port_map: tuple[tuple[str, tuple[int, ...]], ...]
    #: Output-mode indices in NO port (Rem. rem:unmonitored).
    unmonitored: tuple[int, ...]
    #: Gamma restricted to the declared input columns; rows are OUTPUTS.
    gamma_inp: Mat
    #: Port label -> A_k on C^Inp, in the subsystem_order basis.
    grams: tuple[tuple[str, Mat], ...]
    a_sigma: Mat
    deficiency: Mat
    ranks: tuple[tuple[str, int], ...]
    #: LOSSLESS IN THE SENSE OF Definition def:embed APPLIED TO Gamma_Inp: the
    #: restriction to the declared input columns is an ISOMETRY,
    #: Gamma_Inp^dagger Gamma_Inp = 1. THAT IS NOT THE SAME AS ZERO DEFICIENCY,
    #: and I-DILATION-UNITARY is the case that separates them: it is an isometry
    #: whose deficiency is 16/25, because the amplitude reaches an UNMONITORED
    #: DECLARED MODE rather than leaving through the dilation. Eq.
    #: eq:deficiencyid is exactly the decomposition of the deficiency into those
    #: two summands, and an instrument can be lossless with either one non-zero.
    lossless: bool
    derives_from: str


@dataclass(frozen=True)
class POVMBlockCase:
    """One photon-number block of the click-pattern POVM (Thm. thm:click-povm)."""

    case_id: str
    instrument_case_id: str
    photon_number: int
    basis_order: tuple[tuple[int, ...], ...]
    #: Click pattern (as a sorted tuple of port labels) -> its block.
    elements: tuple[tuple[tuple[str, ...], Mat], ...]
    #: The multiclick block, and its exact spectrum.
    multiclick: Mat
    multiclick_spectrum: tuple[F, ...]
    #: The bound of Theorem thm:multiclick-bound at this n, for comparison.
    beta_at_n: F
    derives_from: str


@dataclass(frozen=True)
class CoarseGrainingCase:
    """One declared coarse-graining and its blocks (Def. def:coarse)."""

    case_id: str
    port_labels: tuple[str, ...]
    #: The emitted alphabet, in the emitted order, with its stable IDs.
    alphabet: tuple[tuple[int, str], ...]
    #: Emitted letter -> the click patterns in its fibre.
    fibres: tuple[tuple[str, tuple[tuple[str, ...], ...]], ...]
    surjective: bool
    derives_from: str


@dataclass(frozen=True)
class BoundDataCase:
    """One admissible bound-data tuple and what Def. def:pmc makes of it."""

    case_id: str
    port_count: int
    gamma: F
    betas: tuple[F, ...]
    c: F
    ds: tuple[F, ...]
    #: (n, beta(n)) at the indices the case needs, exactly.
    beta_values: tuple[tuple[int, F], ...]
    photon_cutoff: int
    #: "1" or "2"; and, for branch 1, which predicate selected it.
    branch: str
    predicate: str | None
    #: The declared window, where branch 2 applies; else None.
    window: int | None
    window_minimum: F | None
    tail: F | None
    residual_gap: F | None
    #: p_mc at this setting, exactly.
    p_mc: F
    derives_from: str
    #: "0.2.0" where the amendment marks this row; see SUPERSEDED_BY_0_2_0.
    superseded_by: str | None = None


@dataclass(frozen=True)
class DarkCase:
    """One dark-count channel on 2^[K] (Def. def:darkadm, Thm. thm:dark-counts)."""

    case_id: str
    port_count: int
    #: The per-port probabilities, where the product form generated it.
    p_dc: tuple[F, ...] | None
    #: (column S', ((row S, entry), ...)) with S, S' sorted port-index tuples.
    columns: tuple[tuple[tuple[int, ...], tuple[tuple[tuple[int, ...], F], ...]], ...]
    #: R_{MC|S'} per column.
    mc_mass: tuple[tuple[tuple[int, ...], F], ...]
    #: The correct r_min, minimizing over EVERY non-multiclick column.
    r_min: F
    #: The WRONG value a single-click-only minimum would give, or None.
    r_min_without_noclick: F | None
    column_stochastic: bool
    monotone: bool
    derives_from: str
    #: "0.2.0" where the amendment marks this row; see SUPERSEDED_BY_0_2_0.
    superseded_by: str | None = None


@dataclass(frozen=True)
class ProbeCase:
    """One probe setting, conditioned in closed form (Thm. thm:gaussian-schur)."""

    case_id: str
    channel_modes: tuple[str, ...]
    probe_modes: tuple[str, ...]
    #: The diagonal second-moment matrix, as its diagonal.
    gamma_diagonal: tuple[F, ...]
    #: Port label -> A_k on C^Inp, channel block first (subsystem_order).
    grams: tuple[tuple[str, Mat], ...]
    #: J (as a sorted tuple of port labels) -> (prefactor, effective Gram).
    conditioned: tuple[tuple[tuple[str, ...], F, Mat], ...]
    #: The bound data this setting supplies to Theorem thm:multiclick-bound.
    bound_data_case_id: str
    derives_from: str


@dataclass(frozen=True)
class ResidualCase:
    """One residual of Def. def:residuals, evaluated on frozen data."""

    case_id: str
    residual_id: str
    #: The spectral norm of the frozen residual matrix, exactly. AT 0.2.0 this
    #: is THE value: Def. def:residuals names the spectral norm, closing OIC-3.
    value_spectral: F
    #: Its SQUARED Frobenius norm, exactly. The 0.1.3 second reading of the
    #: then-unnamed norm; see SUPERSEDED_BY_0_2_0.
    value_frobenius_squared: F
    tolerance_key: str
    passes: bool
    derives_from: str
    #: "0.2.0" where the amendment marks this row; see SUPERSEDED_BY_0_2_0.
    superseded_by: str | None = None


@dataclass(frozen=True)
class EfficiencyCase:
    """One efficiency application (Thm. thm:efficiency)."""

    case_id: str
    #: Port label -> (eta_k, rank before, rank after).
    ports: tuple[tuple[str, F, int, int], ...]
    uniform_within_port: bool
    #: sum_k eta_k A_k, and whether it is a multiple of A_Sigma.
    weighted_total: Mat
    is_multiple_of_a_sigma: bool
    derives_from: str


@dataclass(frozen=True)
class RepresentationCase:
    """One representation-independence case (Thm. thm:representation-independence)."""

    case_id: str
    gamma_a: Mat
    gamma_b: Mat
    #: Port -> the row indices it collects, for each instrument. The two need
    #: not agree: REP-REALIZE-RANK2 has different shapes and different maps.
    port_map_a: tuple[tuple[int, ...], ...]
    port_map_b: tuple[tuple[int, ...], ...]
    #: The port Grams of each, in port order, on the same C^Inp basis.
    grams_a: tuple[Mat, ...]
    grams_b: tuple[Mat, ...]
    matrices_equal: bool
    grams_equal: bool
    #: Whether a one-mode-per-port instrument reproduces the POVM.
    one_mode_per_port: bool
    max_rank: int
    derives_from: str


@dataclass(frozen=True)
class RefusalCase:
    """One fail-closed refusal, with the failing check NAMED, never spelled."""

    case_id: str
    subject: str
    #: The contract's own identifier for the failing condition.
    failing_condition: str
    #: True only where contract.tex spells a machine-readable reason string.
    reason_is_verbatim: bool
    reason: str | None
    derives_from: str
    #: True only for the TIER FALLBACK, which emits an artifact at `estimate`;
    #: a refusal emits none (Section 2.5 `fail_closed`, Section 2.6).
    emits_artifact: bool = False
    #: "0.2.0" where the amendment marks this row; see SUPERSEDED_BY_0_2_0.
    superseded_by: str | None = None


@dataclass(frozen=True)
class ModeOrderCase:
    """The two mode orders, and which one indexes what (subsystem_order)."""

    case_id: str
    #: Mode labels as (path, polarization, tau).
    labels: tuple[tuple[str, str, int], ...]
    #: The Def. def:modes order: lexicographic in (p, tau, pi), H before V.
    mode_space_order: tuple[int, ...]
    #: The subsystem_order: Inp_C first, then Inp_S, each inheriting M's order.
    input_index_order: tuple[int, ...]
    orders_disagree: bool
    derives_from: str


@dataclass(frozen=True)
class AssumptionRow:
    """One row of the assumption ledger (Section 5)."""

    assumption_id: str
    machine_key: str
    supports: tuple[str, ...]
    never_verified: bool


# ===========================================================================
#  The interface vocabulary, frozen from interface.yaml / contract.tex Section 2
# ===========================================================================

#: The twelve claims of Section 1.2, in the claims table's order.
CLAIM_IDS: tuple[str, ...] = (
    "RC1",
    "RC2",
    "RC3",
    "RC4",
    "RC5",
    "RC6",
    "RC7",
    "RC8",
    "RC9",
    "RC10",
    "RC11",
    "RC12",
)

#: The fourteen input machine keys of Section 2.1, in the table's order (six in
#: the first tabular, eight in the second).
INPUT_KEYS: tuple[str, ...] = (
    "mode_space",
    "input_modes",
    "port_map",
    "port_grams",
    "instrument_matrix",
    "element_graph",
    "detector_layer",
    "dark_count_channel",
    "probe_declaration",
    "photon_cutoff",
    "tail_window",
    "numerical_tolerances",
    "outcome_coarse_graining",
    "requested_assurance",
)

#: The three MUTUALLY EXCLUSIVE input routes. Section 2.1's preamble: "Exactly
#: one ... is present; the module REFUSES a request carrying two of them rather
#: than choosing."
INPUT_ROUTES: tuple[str, ...] = ("port_grams", "instrument_matrix", "element_graph")

#: The fifteen output machine keys of Section 2.2, in the table's order (six in
#: the first tabular, nine in the second).
OUTPUT_KEYS: tuple[str, ...] = (
    "input_mode_space",
    "outcome_alphabet",
    "port_grams",
    "receiver_construction",
    "photon_blocks",
    "block_dimensions",
    "efficiency_record",
    "dark_count_channel",
    "high_photon_bounds",
    "bound_quantifier_domain",
    "validation_results",
    "bound_evaluation",
    "assumption_ledger",
    "calibration_coverage",
    "mathematical_spec_version",
)

#: The presence rule per output key. EXACTLY ONE key is conditional, and
#: Section 2.2 states both halves of its rule: `receiver_construction` is
#: "present exactly when route (iii) was used ... Absent exactly when the Grams
#: or the instrument matrix were supplied directly".
OUTPUT_PRESENCE: tuple[tuple[str, str], ...] = tuple(
    (key, "route (iii) only" if key == "receiver_construction" else "always")
    for key in OUTPUT_KEYS
)

#: The ten catalogue entry types of Table tab:catalogue. The two LAYERS L1 and
#: L2 are deliberately NOT rows of it (Section 4.3; Section 1.1 item 6).
CATALOGUE_IDS: tuple[str, ...] = (
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "C6",
    "C7",
    "C8",
    "C9",
    "C10",
)

#: The sixteen convention bullets of Section 2.5, by the key each declares.
CONVENTION_KEYS: tuple[str, ...] = (
    "log_base",
    "entropy_variant",
    "test_statistics_model",
    "round_homogeneity",
    "matrix_convention",
    "composition_order",
    "embedding",
    "subsystem_order",
    "polarization_basis",
    "waveplate_convention",
    "beamsplitter_convention",
    "mirror_handedness",
    "povm_index_convention",
    "numerics",
    "fail_closed",
    "artifact_bindings_mathematical_spec_version",
)

#: The twelve rows of the assumption ledger (Section 5), with their machine
#: keys and their Supports columns read claim by claim. `never_verified` is TRUE
#: for exactly the two the section preamble names as DEVICE statements "that
#: this module names and can never verify".
ALL_CLAIMS = CLAIM_IDS
ASSUMPTION_ROWS: tuple[AssumptionRow, ...] = (
    AssumptionRow("A-TRUST", "receiver_trusted_exact", ALL_CLAIMS, True),
    AssumptionRow("A-PASSIVE", "passive_optics", ALL_CLAIMS, False),
    AssumptionRow("A-VAC", "undeclared_inputs_vacuum", ALL_CLAIMS[3:], False),
    AssumptionRow("A-MODES", "no_undeclared_paths", ALL_CLAIMS[3:], True),
    AssumptionRow("A-THRESH", "threshold_memoryless_detectors", ALL_CLAIMS[5:], False),
    AssumptionRow("A-PORT", "mode_insensitive_ports", ALL_CLAIMS[4:], False),
    AssumptionRow("A-EXACT", "exact_parameters", ALL_CLAIMS[1:], False),
    AssumptionRow("A-NOSEL", "device_not_adversarial", ALL_CLAIMS, False),
    AssumptionRow("A-ACYC", "acyclic_element_graph", ("RC2", "RC3"), False),
    AssumptionRow("A-PROBE-DIAG", "probe_fock_diagonal", ("RC8", "RC12"), False),
    AssumptionRow("A-ROUND", "round_homogeneity", ALL_CLAIMS, False),
    AssumptionRow("A-FLOAT", "floating_point_evaluation", ("RC8", "RC9"), False),
)

#: The K = 4 emitted alphabet of Remark req:declared-alphabet, with stable integer
#: IDs and presentation labels. The IDs are the fixture's; which particular IDs
#: are assigned is open implementation choice OIC-1 and is NOT decided here --
#: what is frozen is that they are STABLE and that the labels are METADATA.
OUTCOME_ALPHABET: tuple[tuple[int, str], ...] = (
    (0, "nc"),
    (1, "sc_H"),
    (2, "sc_V"),
    (3, "sc_+"),
    (4, "sc_-"),
    (5, "mc"),
)

#: The version-1 strengthening slot (Def. def:slot): r = 1, one pair, the
#: multiclick set and p_mc. Proposition prop:slotvalid gives 0 <= p_mc <= 1.
SLOT_RECORD: tuple[tuple[str, str], ...] = (
    ("entry_count", "1"),
    ("outcome_set", "MC_K = {S subset of [K] : |S| >= 2}"),
    ("weight", "p_mc of Definition def:pmc, the MINIMUM over the probe alphabet"),
    ("per_setting", "one p_mc value per t in T is emitted beside the minimum"),
)


# ===========================================================================
#  Group RP-A -- the Fock functor and the occupation basis order (RC1)
# ===========================================================================
#
#  Four cases on a TWO-MODE space, blocks n = 0, 1, 2. The block dimensions are
#  binom(2 + n - 1, n) = 1, 2, 3, which is the emitted `block_dimensions` rule
#  of Section 2.2 at |Inp_C| = 2.
#
#  THE BASIS ORDER IS THE POINT OF THE GROUP. Section 2.5 `subsystem_order`
#  ends "within a block, occupation vectors in LEXICOGRAPHIC ORDER of the
#  occupation vector", read as ASCENDING (interface.yaml,
#  conventions.occupation_vector_order_note). At two modes that gives
#
#      n = 0 :  [(0, 0)]
#      n = 1 :  [(0, 1), (1, 0)]        -- the photon in the LAST mode first
#      n = 2 :  [(0, 2), (1, 1), (2, 0)]
#
#  and the consequence, which is the trap: the ONE-PHOTON block of Fock(X) is
#  the matrix of X in the REVERSED mode basis. For X = [[a, b], [c, d]] in the
#  mode basis (e_0, e_1),
#
#      Fock(X)^(1) = [[d, c], [b, a]]
#
#  because the first basis vector of the block is (0, 1), i.e. e_1.
#
#  THE TWO-PHOTON BLOCK, derived once here and used by every case below.
#  Definition def:fock normalizes |1,1> = (e_0 (x) e_1 + e_1 (x) e_0)/sqrt2,
#  and Eq. eq:fockfunctor restricts X (x) X to Sym^2. Expanding,
#      (X (x) X)|2,0> = a^2 |2,0> + sqrt2 a c |1,1> + c^2 |0,2>
#      (X (x) X)|1,1> = sqrt2 a b |2,0> + (a d + b c) |1,1> + sqrt2 c d |0,2>
#      (X (x) X)|0,2> = b^2 |2,0> + sqrt2 b d |1,1> + d^2 |0,2>
#  so in the order [(0,2), (1,1), (2,0)],
#
#      Fock(X)^(2) = [[ d^2,      sqrt2 c d,   c^2      ],
#                     [ sqrt2 b d, a d + b c,  sqrt2 a c],
#                     [ b^2,      sqrt2 a b,   a^2      ]] .
#
#  THE sqrt2 IS WHY THIS REGISTRY IS NOT RATIONAL. It comes from the
#  normalization of |1,1> and from nowhere else, and it is carried exactly.

_N0: tuple[tuple[int, ...], ...] = ((0, 0),)
_N1: tuple[tuple[int, ...], ...] = ((0, 1), (1, 0))
_N2: tuple[tuple[int, ...], ...] = ((0, 2), (1, 1), (2, 0))

FOCK_CASES: tuple[FockCase, ...] = (
    # --- diagonal X = diag(1/2, 1/4) -------------------------------------
    FockCase(
        case_id="FOCK-DIAG-n0",
        mode_labels=("e0", "e1"),
        operator=mat_real(((F(1, 2), 0), (0, F(1, 4)))),
        photon_number=0,
        basis_order=_N0,
        block=mat_real(((1,),)),
        spectrum=(F(1),),
        derives_from="Eq. eq:fockfunctor: Fock(X) restricted to Sym^0 is 1.",
    ),
    FockCase(
        case_id="FOCK-DIAG-n1",
        mode_labels=("e0", "e1"),
        operator=mat_real(((F(1, 2), 0), (0, F(1, 4)))),
        photon_number=1,
        basis_order=_N1,
        block=mat_real(((F(1, 4), 0), (0, F(1, 2)))),
        spectrum=(F(1, 4), F(1, 2)),
        derives_from=(
            "Fock(X)^(1) = X in the occupation order [(0,1), (1,0)], i.e. the "
            "REVERSED mode basis: [[d, c], [b, a]] = [[1/4, 0], [0, 1/2]]."
        ),
    ),
    FockCase(
        case_id="FOCK-DIAG-n2",
        mode_labels=("e0", "e1"),
        operator=mat_real(((F(1, 2), 0), (0, F(1, 4)))),
        photon_number=2,
        basis_order=_N2,
        block=mat_real(((F(1, 16), 0, 0), (0, F(1, 8), 0), (0, 0, F(1, 4)))),
        spectrum=(F(1, 16), F(1, 8), F(1, 4)),
        derives_from=(
            "Eq. eq:spectrum: the eigenvalue at the occupation vector m is the "
            "product over j of x_j^{m_j}. At m = (0,2), (1,1), (2,0) with "
            "x = (1/2, 1/4) that is (1/4)^2 = 1/16, (1/2)(1/4) = 1/8 and "
            "(1/2)^2 = 1/4. The block is diagonal because X is."
        ),
    ),
    # --- non-diagonal, NON-HERMITIAN X, which exposes the reversal ---------
    FockCase(
        case_id="FOCK-TRI-n1",
        mode_labels=("e0", "e1"),
        operator=mat_real(((F(1, 2), F(1, 4)), (0, F(1, 2)))),
        photon_number=1,
        basis_order=_N1,
        block=mat_real(((F(1, 2), 0), (F(1, 4), F(1, 2)))),
        spectrum=None,
        derives_from=(
            "X = [[1/2, 1/4], [0, 1/2]] is a contraction: 1 - X^dagger X = "
            "[[3/4, -1/8], [-1/8, 11/16]] has trace 23/16 > 0 and determinant "
            "(3/4)(11/16) - 1/64 = 1/2 > 0, hence is positive definite, so "
            "X^dagger X < 1 strictly (Def. def:embed). Its one-photon block is "
            "[[d, c], [b, a]] = [[1/2, 0], [1/4, 1/2]] -- THE TRANSPOSE-LOOKING "
            "REVERSAL OF X, and the case that would pass unnoticed if the "
            "occupation order were read the other way round."
        ),
    ),
    FockCase(
        case_id="FOCK-TRI-n2",
        mode_labels=("e0", "e1"),
        operator=mat_real(((F(1, 2), F(1, 4)), (0, F(1, 2)))),
        photon_number=2,
        basis_order=_N2,
        block=(
            (rt(F(1, 4)), rt(0), rt(0)),
            (rt(0, F(1, 8)), rt(F(1, 4)), rt(0)),
            (rt(F(1, 16)), rt(0, F(1, 8)), rt(F(1, 4))),
        ),
        spectrum=None,
        derives_from=(
            "a = 1/2, b = 1/4, c = 0, d = 1/2 in the two-photon formula above: "
            "d^2 = 1/4; sqrt2 c d = 0; c^2 = 0; sqrt2 b d = sqrt2/8; "
            "a d + b c = 1/4; sqrt2 a c = 0; b^2 = 1/16; sqrt2 a b = sqrt2/8; "
            "a^2 = 1/4. THE TWO sqrt2 ENTRIES ARE FROZEN EXACTLY, as (0, 1/8) "
            "in Q[sqrt2]."
        ),
    ),
    # --- the projector case, Lemma lem:fock-functor (iv) ----------------------
    FockCase(
        case_id="FOCK-PROJ-n1",
        mode_labels=("e0", "e1"),
        operator=mat_real(((1, 0), (0, 0))),
        photon_number=1,
        basis_order=_N1,
        block=mat_real(((0, 0), (0, 1))),
        spectrum=(F(0), F(1)),
        derives_from=(
            "Lemma lem:fock-functor (iv): for an orthogonal projector P, Fock(P) is "
            "the projector onto the span of the occupation vectors carrying NO "
            "PHOTON OUTSIDE ran P. At P = diag(1, 0) and n = 1 the only such "
            "vector is (1, 0), which is the SECOND basis vector in the "
            "occupation order, so the block is diag(0, 1)."
        ),
    ),
    FockCase(
        case_id="FOCK-PROJ-n2",
        mode_labels=("e0", "e1"),
        operator=mat_real(((1, 0), (0, 0))),
        photon_number=2,
        basis_order=_N2,
        block=mat_real(((0, 0, 0), (0, 0, 0), (0, 0, 1))),
        spectrum=(F(0), F(0), F(1)),
        derives_from=(
            "Same lemma at n = 2: only (2, 0) puts both photons inside ran P, "
            "and it is the LAST basis vector in the occupation order."
        ),
    ),
    # --- the spectrum and its two attained bounds, Lemma lem:fock-block-spectrum --
    FockCase(
        case_id="FOCK-SPECTRUM-n2",
        mode_labels=("e0", "e1"),
        operator=mat_real(((F(1, 2), F(-1, 4)), (F(-1, 4), F(1, 2)))),
        photon_number=2,
        basis_order=_N2,
        block=(
            (rt(F(1, 4)), rt(0, F(-1, 8)), rt(F(1, 16))),
            (rt(0, F(-1, 8)), rt(F(5, 16)), rt(0, F(-1, 8))),
            (rt(F(1, 16)), rt(0, F(-1, 8)), rt(F(1, 4))),
        ),
        spectrum=(F(1, 16), F(3, 16), F(9, 16)),
        derives_from=(
            "X = 1 - A with A = [[1/2, 1/4], [1/4, 1/2]], whose eigenvalues are "
            "1/2 +- 1/4 = 3/4 and 1/4, so 0 <= A <= 1 and Lemma lem:fock-block-spectrum "
            "applies. Eq. eq:spectrum gives the two-photon spectrum "
            "{(1 - lambda_j)^{m_j}} = {(1/4)^2, (1/4)(3/4), (3/4)^2} = "
            "{1/16, 3/16, 9/16}, whose sum 13/16 is the trace of the frozen "
            "block (1/4 + 5/16 + 1/4). Eq. eq:blockbounds then reads "
            "(1 - lmax(A))^2 = 1/16 <= block <= (3/4)^2 = 9/16, AND BOTH "
            "ENDPOINTS ARE ATTAINED, at the occupation vectors putting both "
            "photons on an eigenvector for lmax(A), respectively lmin(A). "
            "The entries: a = 1/2, b = c = -1/4, d = 1/2 give d^2 = 1/4, "
            "sqrt2 c d = -sqrt2/8, c^2 = 1/16, a d + b c = 1/4 + 1/16 = 5/16."
        ),
    ),
)


O_RP_FOCK = RPOracleEntry(
    oracle_id="O-RP-FOCK",
    claims=("RC1",),
    kind="structural-identity",
    subject=(
        "The second-quantization functor on the 0-, 1- and 2-photon sectors of "
        "a two-mode contraction; the photon-number grading, the block "
        "dimensions, the occupation-vector basis order and the index reversal "
        "it causes; the projector case; the spectrum and its attained bounds."
    ),
    derivation="""\
Definition def:fock, Eq. eq:fockfunctor, and Lemmas lem:fock-functor and
lem:fock-block-spectrum. Seven blocks are frozen in FOCK_CASES; the derivation of the
two-photon matrix is written out in the comment above that tuple and is not
repeated here.

WHAT THIS ENTRY PINS THAT AN IMPLEMENTATION CAN GET WRONG.

(1) THE GRADING. Lemma lem:fock-functor (i): Fock(X) commutes with every
photon-number projector, so it is BLOCK DIAGONAL and the blocks are independent
objects. Every case here is one block; no case relates two blocks, because
nothing in the contract does.

(2) THE BLOCK DIMENSIONS. Section 2.2 `block_dimensions` fixes them as
binom(|Inp_C| + n - 1, n). At |Inp_C| = 2 that is 1, 2, 3 for n = 0, 1, 2, which
is the number of occupation vectors of weight n on two modes, and is the length
of `basis_order` in each frozen case.

(3) THE BASIS ORDER, and the reversal. ASCENDING lexicographic on the occupation
vector puts (0, 1) before (1, 0), so the FIRST basis vector of the one-photon
block is the photon in the LAST mode. FOCK-TRI-n1 is the case that exposes it:
X = [[1/2, 1/4], [0, 1/2]] is upper triangular and its one-photon block
[[1/2, 0], [1/4, 1/2]] is LOWER triangular. An implementation that read the
occupation order the other way round would agree with the contract on every
symmetric matrix and disagree here, which is exactly why a non-Hermitian
operator is frozen alongside the Hermitian ones.

(4) THE sqrt2. It enters only through the normalization of |1,1> and it is
carried exactly, as (0, 1/8) and (0, -1/8) in Q[sqrt2]. No rounding, and no
tolerance: the contract's statements are exact (Theorem thm:exact-and-evaluated (i)).

(5) THE PROJECTOR CASE. Lemma lem:fock-functor (iv) is what Definition
def:physmodel's port projectors are, so getting it wrong would break RC6 rather
than RC1: Pi^0_k = Fock(1 - E_{P_k}) IS the projector case at the coordinate
projector of the port.

(6) THE SPECTRUM AND ITS TWO ATTAINED BOUNDS. Lemma lem:fock-block-spectrum is the
engine of the whole high-photon bound -- Eq. eq:blockbounds is what Theorem
thm:multiclick-bound's Eq. eq:blockopbounds applies to B and to each B_k -- so the
sharpness statement "both bounds being attained as eigenvalues" is not
decoration. FOCK-SPECTRUM-n2 freezes both endpoints and the whole spectrum.

WHAT IS DELIBERATELY NOT PINNED. Multiplicativity (Lemma lem:fock-functor (ii)) and
order monotonicity (Lemma lem:fock-monotone) are relations between Fock(X) at
DIFFERENT X, and checking them here would require this file to multiply or
compare matrices, which is the implementation. What is frozen instead is the
data those relations are ABOUT, in enough cases that an implementation
reproducing every block must have got the functor right. Proposition
prop:normord is not pinned at all: Remark rem:whyprojector states it "is not
used in the proof of any claim".
""",
)


# ===========================================================================
#  Group RP-B -- compilation of a declared element graph (RC2)
# ===========================================================================
#
#  All graphs are on M = (m0, m1), one path with its two polarization modes.
#  `compiled` is the matrix of Definition def:compile BEFORE the terminal
#  detector layer D_eta; where D_eta enters is Group RP-J.

COMPILE_CASES: tuple[CompileCase, ...] = (
    CompileCase(
        case_id="G-PARALLEL",
        mode_labels=("m0", "m1"),
        elements=(
            ("e_a", "C6", (0,), "phi_{m0} = pi"),
            ("e_b", "C7", (1,), "eta_{m1} = 1/4"),
        ),
        edges=(),
        linear_extensions=(("e_a", "e_b"), ("e_b", "e_a")),
        compiled=mat_real(((-1, 0), (0, F(1, 2)))),
        refused_condition=None,
        lossless=False,
        derives_from=(
            "Theorem thm:compilation-well-defined (i). The two elements have DISJOINT supports "
            "({m0} and {m1}), so (E3) holds vacuously and Proposition "
            "prop:mode-algebra (iii) makes their embeddings commute; the graph "
            "has no edge, so BOTH orders are linear extensions, and both "
            "compile to diag(-1, 1/2) by Eq. eq:compile. This is also the "
            "LAYERED form of thm:compilation-well-defined (i): one layer L_1 = {e_a, e_b} whose "
            "members have pairwise disjoint supports, with the intra-layer "
            "product order-independent. C6 at phi = pi is the scalar -1 and C7 "
            "at eta = 1/4 is sqrt(1/4) = 1/2 (Section 4.3, entries C6 and C7). "
            "Gamma^dagger Gamma = diag(1, 1/4) <= 1 with strict inequality on "
            "the second mode, so thm:compilation-well-defined (ii) holds and thm:compilation-well-defined (iii) says it "
            "is NOT unitary -- correctly, since e_b is not lossless."
        ),
    ),
    CompileCase(
        case_id="G-LOSSLESS",
        mode_labels=("m0", "m1"),
        elements=(("e_a", "C6", (0,), "phi_{m0} = pi"),),
        edges=(),
        linear_extensions=(("e_a",),),
        compiled=mat_real(((-1, 0), (0, 1))),
        refused_condition=None,
        lossless=True,
        derives_from=(
            "Theorem thm:compilation-well-defined (iii), the FORWARD direction: every element of the "
            "graph is lossless (C6 is unitary at every parameter tuple, Table "
            "tab:catalogue) and the compiled matrix diag(-1, 1) is unitary. "
            "Together with G-PARALLEL this is the iff in both directions: there "
            "one element is lossy and the compiled matrix is not unitary."
        ),
    ),
    CompileCase(
        case_id="G-ORDERED",
        mode_labels=("m0", "m1"),
        elements=(
            ("e_1", "C4", (0, 1), "rho with cos rho = 3/5, sin rho = 4/5"),
            ("e_2", "C8", (0, 1), "theta = 0, t = 1, t_perp = 0"),
        ),
        edges=(("e_1", "e_2"),),
        linear_extensions=(("e_1", "e_2"),),
        compiled=mat_real(((F(3, 5), F(-4, 5)), (0, 0))),
        refused_condition=None,
        lossless=False,
        derives_from=(
            "The `composition_order` convention of Section 2.5 -- LATER "
            "ELEMENTS MULTIPLY FROM THE LEFT -- made load-bearing. The supports "
            "intersect and the EDGE orders them, so (E3) holds and there is "
            "exactly one linear extension. Eq. eq:compile gives "
            "Gamma = Ghat_{e_2} Ghat_{e_1} = diag(1, 0) R(rho) = "
            "[[3/5, -4/5], [0, 0]]. THE REVERSED PRODUCT IS DIFFERENT: "
            "R(rho) diag(1, 0) = [[3/5, 0], [4/5, 0]]. Gamma^dagger Gamma = "
            "[[9/25, -12/25], [-12/25, 16/25]] is a rank-one projector "
            "(trace 1, determinant (9)(16)/625 - (12/25)^2 = 0), so it is <= 1 "
            "with equality on one eigenvector: a contraction, not an isometry, "
            "as thm:compilation-well-defined (ii)-(iii) require of a graph containing a polarizer "
            "with t_perp = 0."
        ),
    ),
    CompileCase(
        case_id="G-E3-VIOLATION",
        mode_labels=("m0", "m1"),
        elements=(
            ("e", "C4", (0, 1), "rho with cos rho = 3/5, sin rho = 4/5"),
            ("f", "C8", (0, 1), "theta = 0, t = 1, t_perp = 0"),
        ),
        edges=(),
        linear_extensions=(("e", "f"), ("f", "e")),
        compiled=None,
        refused_condition="E3",
        lossless=None,
        derives_from=(
            "Remark rem:e3, verbatim as an instance: the SAME two elements as "
            "G-ORDERED with THE EDGE REMOVED. The graph is acyclic and every "
            "element is admissible, so (E1) and (E2) pass; but the supports "
            "intersect and the elements are incomparable, so (E3) FAILS and "
            "Theorem thm:compilation-well-defined (iv) refuses, naming the condition and the "
            "offending pair. THE REFUSAL IS NOT PEDANTRY: the two linear "
            "extensions compile to [[3/5, -4/5], [0, 0]] and [[3/5, 0], "
            "[4/5, 0]] respectively, and -- because both are contractions with "
            "the same declared port map -- BOTH WOULD PASS EVERY OTHER "
            "VALIDATION IN THE CONTRACT. Without (E3), 'the declared receiver' "
            "does not denote."
        ),
    ),
    CompileCase(
        case_id="G-E2-VIOLATION",
        mode_labels=("m0", "m1"),
        elements=(
            ("e", "C6", (0,), "phi_{m0} = pi"),
            ("f", "C7", (1,), "eta_{m1} = 1/4"),
        ),
        edges=(("e", "f"), ("f", "e")),
        linear_extensions=(),
        compiled=None,
        refused_condition="E2",
        lossless=None,
        derives_from=(
            "Definition def:graph (E2). The two edges "
            "make a cycle, so the reachability relation is not a partial order "
            "and there is NO linear extension -- the frozen tuple is empty, "
            "which is the whole content of the refusal. Remark rem:noloops: "
            "compiling one 'would require solving a fixed-point equation on the "
            "mode graph, and the resulting matrix is a contraction only under a "
            "spectral condition that would itself have to be certified. Version "
            "1 does neither.' A receiver that needs one is A NEW CLAIM, NOT A "
            "BIGGER COMPUTATION. Note that the ELEMENTS here are exactly "
            "G-PARALLEL's, and G-PARALLEL compiles: the refusal is a property "
            "of the declared graph, not of the components."
        ),
    ),
    CompileCase(
        case_id="G-E1-VIOLATION",
        mode_labels=("m0", "m1"),
        elements=(("e", "C3", (0, 1), "delta = 2 pi, theta = 0, y = 0"),),
        edges=(),
        linear_extensions=(("e",),),
        compiled=None,
        refused_condition="E1",
        lossless=None,
        derives_from=(
            "Definition def:graph (E1) with Table tab:catalogue. C3's declared "
            "retardance domain is delta in [0, 2 pi), HALF-OPEN, so delta = "
            "2 pi is OUTSIDE it -- by exactly one endpoint. Section 2.4, third "
            "bullet: 'A parameter outside its domain is REFUSED; IT IS NEVER "
            "CLIPPED TO THE BOUNDARY.' The clipped value delta = 0 would give "
            "the identity, which is admissible and wrong, and the difference "
            "would be silent. The same half-open trap sits at C3's theta in "
            "[0, pi), C5's and C6's phi in [0, 2 pi), and C4's rho in "
            "[0, 2 pi)."
        ),
    ),
)


O_RP_COMPILE = RPOracleEntry(
    oracle_id="O-RP-COMPILE",
    claims=("RC2",),
    kind="structural-identity",
    subject=(
        "Compilation is well defined: one graph under two linear extensions and "
        "under a layering, one graph whose edge fixes the order, the "
        "contraction property, isometry iff lossless both ways, and one refusal "
        "each for (E1), (E2) and (E3) with the failing condition named."
    ),
    derivation="""\
Definition def:graph, Definition def:compile and Theorem thm:compilation-well-defined. Six graphs are
frozen in COMPILE_CASES with their derivations; what follows is what the SET of
them pins, which no single case does.

THE THREE WELL-FORMEDNESS CONDITIONS ARE INDEPENDENT, and the frozen set shows
it. G-PARALLEL passes all three. G-E1-VIOLATION fails only (E1): it is acyclic
and its single element cannot violate support comparability. G-E2-VIOLATION
fails only (E2): its elements are G-PARALLEL's, admissible and disjointly
supported. G-E3-VIOLATION fails only (E3): it is acyclic and both its elements
are admissible. So no two of the three conditions can be conflated by an
implementation that reproduces these six.

THE REFUSAL IS NAMED, NOT SPELLED. Theorem thm:compilation-well-defined (iv) requires the failing
condition AND the offending element pair to be named; Section 2.5 `fail_closed`
requires a machine-readable reason and NO artifact. contract.tex spells no
reason string for any of the three, so `refused_condition` carries the
contract's own identifier -- "E1", "E2", "E3" -- and no invented string appears
anywhere. That is the discipline of the whole file: the IDENTITY of the check is
the contract's, the SPELLING is code's.

INDEPENDENCE OF THE SORT IS AN EQUALITY BETWEEN TWO PRODUCTS, and G-PARALLEL
freezes both orders with one compiled matrix. The layered form of thm:compilation-well-defined (i) is
the same case read differently: L_1 = {e_a, e_b} is a single layer of pairwise
disjointly supported elements, and its intra-layer product is order-independent
by Proposition prop:mode-algebra (iii).

COMPOSITION ORDER IS LOAD-BEARING AND G-ORDERED IS WHERE IT BITES. The two
products differ, the graph's EDGE is what selects one of them, and both are
contractions -- so an implementation that multiplied in the wrong order would
produce a perfectly valid instrument for a different receiver. Section 2.5
`composition_order` fixes the direction; Remark rem:edgemeaning fixes what the
edge means ("light leaving e enters f: it is the ROUTING of the receiver").

WHAT IS NOT PINNED. No case here exercises the terminal detector layer D_eta of
Definition def:compile: Gamma = D_eta Gamma_G, and D_eta is Group RP-J, where
Theorem thm:efficiency (iii)'s "one structural site" is the point. The frozen
`compiled` field is Gamma_G, the product of the graph's elements, and the cases
say so.
""",
)


# ===========================================================================
#  Group RP-C -- the component catalogue (RC3)
# ===========================================================================
#
#  Table tab:catalogue, entry by entry, at one INTERIOR and one BOUNDARY
#  parameter tuple, with the lossless verdict of the table's last column.
#
#  PARAMETER CHOICES. Where a catalogue matrix carries a square root, the
#  parameter is chosen so that the root is rational -- x = 9/25 gives
#  sqrt(x) = 3/5 and sqrt(1-x) = 4/5; the rotation angle is the one with
#  cos = 3/5, sin = 4/5; the losses are y = 3/4 (sqrt(1-y) = 1/2) and
#  eta = 1/4 (sqrt(eta) = 1/2). TWO CASES DELIBERATELY DO NOT: the 50:50
#  beamsplitter (amplitudes sqrt2/2) and the HWP at pi/8 (amplitudes -i sqrt2/2),
#  because those are the two the project's own target receiver uses, and
#  carrying them exactly is the point of the Q[sqrt2] substrate.
#
#  C1 and C2 are frozen as the CORE matrices Eq. eq:bs and Eq. eq:pbs display;
#  the full element is the core tensored with the identity on polarization (C1)
#  or conjugated by the basis permutation Xi (C2, already applied below).

CATALOGUE_CASES: tuple[CatalogueCase, ...] = (
    # --- C1 beamsplitter --------------------------------------------------
    CatalogueCase(
        case_id="C1-interior",
        entry_id="C1",
        position="interior",
        parameters="x = 9/25, phi = 0, y_1 = y_2 = 0",
        matrix=mat_real(((F(3, 5), F(4, 5)), (F(4, 5), F(-3, 5)))),
        lossless=True,
        determinant=rt(-1),
        derives_from=(
            "Eq. eq:bs at sqrt(x) = 3/5, sqrt(1-x) = 4/5, e^{i phi} = 1. REAL "
            "AT phi = 0, as Section 2.5 `beamsplitter_convention` states, WITH "
            "det B = (3/5)(-3/5) - (4/5)(4/5) = -9/25 - 16/25 = -1. Unitary by "
            "the column check of the Theorem thm:catalogue-admissibility proof: 9/25 + 16/25 = 1 "
            "for each column and the inner product is "
            "(3/5)(4/5) + (4/5)(-3/5) = 0. Lossless exactly at y_1 = y_2 = 0."
        ),
    ),
    CatalogueCase(
        case_id="C1-boundary-x1",
        entry_id="C1",
        position="boundary",
        parameters="x = 1, phi = 0, y_1 = y_2 = 0",
        matrix=mat_real(((1, 0), (0, -1))),
        lossless=True,
        determinant=rt(-1),
        derives_from=(
            "Eq. eq:bs at the transmittance endpoint x = 1: sqrt(1-x) = 0, so "
            "the core is diag(1, -1). Still det = -1, and still unitary: the "
            "domain endpoint is INSIDE the declared domain x in [0, 1] and "
            "Theorem thm:catalogue-admissibility covers the WHOLE declared domain."
        ),
    ),
    CatalogueCase(
        case_id="C1-boundary-x0",
        entry_id="C1",
        position="boundary",
        parameters="x = 0, phi = 0, y_1 = y_2 = 0",
        matrix=mat_real(((0, 1), (1, 0))),
        lossless=True,
        determinant=rt(-1),
        derives_from=(
            "The other transmittance endpoint: sqrt(x) = 0 and the core is the "
            "swap, det = -1."
        ),
    ),
    CatalogueCase(
        case_id="C1-lossy",
        entry_id="C1",
        position="interior",
        parameters="x = 9/25, phi = 0, y_1 = 3/4, y_2 = 0",
        matrix=mat_real(((F(3, 10), F(2, 5)), (F(4, 5), F(-3, 5)))),
        lossless=False,
        determinant=rt(F(-1, 2)),
        derives_from=(
            "Eq. eq:bs with the per-output loss factor "
            "diag(sqrt(1-y_1), sqrt(1-y_2)) = diag(1/2, 1) applied on the LEFT "
            "(outputs). Row 0 halves. Lemma lem:attenuated gives admissibility "
            "and equality EXACTLY at D_1 = D_2 = 1, i.e. y_1 = y_2 = 0, so this "
            "element is a contraction and is NOT lossless -- Table "
            "tab:catalogue's last column for C1."
        ),
    ),
    CatalogueCase(
        case_id="C1-phase",
        entry_id="C1",
        position="interior",
        parameters="x = 9/25, phi = pi/2, y_1 = y_2 = 0",
        matrix=(
            (rt(F(3, 5)), im_(F(4, 5))),
            (im_(F(-4, 5)), rt(F(-3, 5))),
        ),
        lossless=True,
        determinant=rt(-1),
        derives_from=(
            "Eq. eq:bs at e^{i phi} = i and e^{-i phi} = -i. det = "
            "(3/5)(-3/5) - (4i/5)(-4i/5) = -9/25 - (-16 i^2 / 25) = "
            "-9/25 - 16/25 = -1. THE REFLECTION PHASE IS CARRIED, not dropped: "
            "Section 1.1 item 9, 'a phase that is global on one element is "
            "RELATIVE as soon as that element sits on one arm of an "
            "interferometer, so no catalogue entry drops one'."
        ),
    ),
    CatalogueCase(
        case_id="C1-half",
        entry_id="C1",
        position="interior",
        parameters="x = 1/2, phi = 0, y_1 = y_2 = 0",
        matrix=(
            (HALF_R2, HALF_R2),
            (HALF_R2, alg(q2(0, F(-1, 2)))),
        ),
        lossless=True,
        determinant=rt(-1),
        derives_from=(
            "THE 50:50 BEAMSPLITTER, and the case the module docstring names: "
            "its amplitudes sqrt(1/2) = sqrt2/2 ARE NOT RATIONAL, and are frozen "
            "exactly as (0, 1/2) in Q[sqrt2]. det = (sqrt2/2)(-sqrt2/2) - "
            "(sqrt2/2)(sqrt2/2) = -1/2 - 1/2 = -1. ITS PORT GRAMS ARE "
            "RATIONAL: with two single-mode ports collecting the two outputs, "
            "Eq. eq:gramdef gives A_1 = (1/2)[[1, 1], [1, 1]] and "
            "A_2 = (1/2)[[1, -1], [-1, 1]], both rational, with "
            "A_1 + A_2 = 1 -- lossless, as thm:compilation-well-defined (iii) requires. That is "
            "Theorem thm:representation-independence (i) in miniature: THE GRAMS CARRY EXACTLY WHAT THE "
            "CLICK STATISTICS CAN REVEAL, and they are rational where the "
            "amplitudes are not. Frozen as instrument case I-BS in Group RP-D."
        ),
    ),
    # --- C2 polarizing beamsplitter ---------------------------------------
    CatalogueCase(
        case_id="C2-boundary-ideal",
        entry_id="C2",
        position="boundary",
        parameters="t_H = 1, t_V = 0, phi_H = phi_V = 0, y_1 = y_2 = 0",
        matrix=mat_real(
            (
                (1, 0, 0, 0),
                (0, 0, 0, 1),
                (0, 0, -1, 0),
                (0, 1, 0, 0),
            )
        ),
        lossless=True,
        determinant=None,
        derives_from=(
            "Eq. eq:pbs in the declared ordering (p1H, p1V, p2H, p2V). "
            "B(1, 0) = diag(1, -1) acts on (p1H, p2H) and B(0, 0) = the swap "
            "acts on (p1V, p2V). The Theorem thm:catalogue-admissibility proof states the answer in "
            "words -- 'the signed permutation p1H -> p1H, p1V -> p2V, "
            "p2H -> -p2H, p2V -> p1V, THE INTENDED ROUTING UP TO PER-MODE "
            "PHASES, WHICH IS THE USEFUL EARLY CONSISTENCY CHECK FOR AN "
            "IMPLEMENTATION' -- and the frozen matrix is that sentence written "
            "out with rows = outputs. Note that the MINUS SIGN on p2H is real "
            "and is not dropped."
        ),
    ),
    CatalogueCase(
        case_id="C2-interior",
        entry_id="C2",
        position="interior",
        parameters="t_H = 9/25, t_V = 16/25, phi_H = phi_V = 0, y_1 = y_2 = 0",
        matrix=mat_real(
            (
                (F(3, 5), 0, F(4, 5), 0),
                (0, F(4, 5), 0, F(3, 5)),
                (F(4, 5), 0, F(-3, 5), 0),
                (0, F(3, 5), 0, F(-4, 5)),
            )
        ),
        lossless=True,
        determinant=None,
        derives_from=(
            "Eq. eq:pbs with B(9/25, 0) = [[3/5, 4/5], [4/5, -3/5]] on the H "
            "pair and B(16/25, 0) = [[4/5, 3/5], [3/5, -4/5]] on the V pair, "
            "conjugated back to the declared ordering by Xi. A direct sum of "
            "unitaries conjugated by a permutation is unitary (Theorem thm:catalogue-admissibility "
            "proof, case C2), and y_1 = y_2 = 0 makes it lossless."
        ),
    ),
    CatalogueCase(
        case_id="C2-lossy",
        entry_id="C2",
        position="interior",
        parameters="t_H = 1, t_V = 0, phi_H = phi_V = 0, y_1 = 3/4, y_2 = 0",
        matrix=mat_real(
            (
                (F(1, 2), 0, 0, 0),
                (0, 0, 0, F(1, 2)),
                (0, 0, -1, 0),
                (0, 1, 0, 0),
            )
        ),
        lossless=False,
        determinant=None,
        derives_from=(
            "The ideal core with the output-loss prefactor "
            "diag(sqrt(1-y_1), sqrt(1-y_1), sqrt(1-y_2), sqrt(1-y_2)) = "
            "diag(1/2, 1/2, 1, 1): the loss is PER PATH, so it scales BOTH "
            "polarization rows of path 1. Not lossless, y_1 != 0."
        ),
    ),
    # --- C3 retarder ------------------------------------------------------
    CatalogueCase(
        case_id="C3-hwp-pi8",
        entry_id="C3",
        position="interior",
        parameters="delta = pi, theta = pi/8, y = 0  (the HWP preset)",
        matrix=(
            (im_(0, F(-1, 2)), im_(0, F(-1, 2))),
            (im_(0, F(-1, 2)), im_(0, F(1, 2))),
        ),
        lossless=True,
        determinant=None,
        derives_from=(
            "Eq. eq:hwpqwp, which states the answer: HWP(pi/8) = "
            "-(i/sqrt2) [[1, 1], [1, -1]], 'the 22.5-degree plate that maps the "
            "rectilinear basis to the diagonal one'. Every entry is purely "
            "imaginary with modulus sqrt2/2 and is frozen exactly as "
            "i(0, -1/2) or i(0, 1/2) in Q[sqrt2]. THE FACTOR -i IS THE PHYSICAL "
            "PHASE e^{-i delta / 2} AT delta = pi and Section 2.5 "
            "`waveplate_convention` forbids dropping it."
        ),
    ),
    CatalogueCase(
        case_id="C3-hwp-rational",
        entry_id="C3",
        position="interior",
        parameters="delta = pi, theta with cos 2theta = 3/5, sin 2theta = 4/5, y = 0",
        matrix=(
            (im_(F(-3, 5)), im_(F(-4, 5))),
            (im_(F(-4, 5)), im_(F(3, 5))),
        ),
        lossless=True,
        determinant=None,
        derives_from=(
            "Eq. eq:hwpqwp: HWP(theta) = -i [[cos 2theta, sin 2theta], "
            "[sin 2theta, -cos 2theta]]. The angle is the one with "
            "cos 2theta = 3/5 and sin 2theta = 4/5, which lies in the declared "
            "domain theta in [0, pi). Unitary: -i is unimodular and the real "
            "matrix is a reflection."
        ),
    ),
    CatalogueCase(
        case_id="C3-hwp-DROPPED-PHASE",
        entry_id="C3",
        position="interior",
        parameters=(
            "delta = pi, cos 2theta = 3/5 -- THE PHASE DROPPED. "
            "NOT THE CONTRACT'S ELEMENT."
        ),
        matrix=mat_real(((F(3, 5), F(4, 5)), (F(4, 5), F(-3, 5)))),
        lossless=True,
        determinant=None,
        derives_from=(
            "THE TRAP, FROZEN BESIDE THE CORRECT ELEMENT SO THAT AN "
            "IMPLEMENTATION CANNOT PASS BY PRODUCING IT. This is the real "
            "matrix [[cos 2theta, sin 2theta], [sin 2theta, -cos 2theta]] that "
            "Example ex:bb84 says 'an implementation that writes HWP as the "
            "real matrix ... SILENTLY DROPS'. It differs from C3-hwp-rational "
            "by the factor -i on EVERY entry, it is unitary, and it will pass "
            "every admissibility check in the contract. WHETHER THE DIFFERENCE "
            "MATTERS IS A THEOREM WITH A HYPOTHESIS, NOT A REFLEX: Corollary "
            "cor:phases says a unitary acting INSIDE ONE PORT'S MODES AND AFTER "
            "ALL INTERFERENCE changes no click statistic, and Example ex:bb84 "
            "checks that hypothesis for its own receiver and finds it met -- "
            "'that is a statement about THIS receiver and THIS factor, NOT "
            "ABOUT PHASES IN GENERAL'. Put this element on one arm of an "
            "interferometer and the factor is relative, and the Grams change."
        ),
    ),
    CatalogueCase(
        case_id="C3-boundary-delta0",
        entry_id="C3",
        position="boundary",
        parameters="delta = 0, theta arbitrary, y = 0",
        matrix=mat_real(((1, 0), (0, 1))),
        lossless=True,
        determinant=None,
        derives_from=(
            "Eq. eq:retarder at delta = 0: e^{-i delta/2} = 1 and "
            "diag(1, e^{i delta}) = 1, so W = R(theta) R(theta)^T = 1 for every "
            "theta, R being real orthogonal. The retardance endpoint 0 is IN "
            "the declared domain [0, 2 pi); the endpoint 2 pi is NOT, and is "
            "the (E1) refusal G-E1-VIOLATION."
        ),
    ),
    CatalogueCase(
        case_id="C3-qwp-theta0",
        entry_id="C3",
        position="interior",
        parameters="delta = pi/2, theta = 0, y = 0  (the QWP preset)",
        matrix=(
            (alg(q2(0, F(1, 2)), q2(0, F(-1, 2))), rt(0)),
            (rt(0), alg(q2(0, F(1, 2)), q2(0, F(1, 2)))),
        ),
        lossless=True,
        determinant=None,
        derives_from=(
            "Eq. eq:hwpqwp: QWP(theta) = W(pi/2, theta). At theta = 0, "
            "R(0) = 1 so W = e^{-i pi/4} diag(1, i). "
            "e^{-i pi/4} = sqrt2/2 - i sqrt2/2, and "
            "e^{-i pi/4} i = sqrt2/2 + i sqrt2/2. BOTH ENTRIES CARRY sqrt2 AND "
            "i TOGETHER, which is why the substrate is Q[sqrt2] + i Q[sqrt2] "
            "and not either half of it."
        ),
    ),
    CatalogueCase(
        case_id="C3-lossy",
        entry_id="C3",
        position="interior",
        parameters="delta = pi, cos 2theta = 3/5, y = 3/4",
        matrix=(
            (im_(F(-3, 10)), im_(F(-2, 5))),
            (im_(F(-2, 5)), im_(F(3, 10))),
        ),
        lossless=False,
        determinant=None,
        derives_from=(
            "Gamma_C3 = sqrt(1-y) W(delta, theta) with sqrt(1-3/4) = 1/2. A "
            "scalar contraction times a unitary: admissible by Lemma "
            "lem:attenuated, lossless exactly at y = 0 (Table tab:catalogue)."
        ),
    ),
    # --- C4 rotator -------------------------------------------------------
    CatalogueCase(
        case_id="C4-interior",
        entry_id="C4",
        position="interior",
        parameters="rho with cos rho = 3/5, sin rho = 4/5",
        matrix=mat_real(((F(3, 5), F(-4, 5)), (F(4, 5), F(3, 5)))),
        lossless=True,
        determinant=None,
        derives_from=(
            "Section 4.3 entry C4: Gamma_C4 = R(rho), real orthogonal, hence "
            "unitary at EVERY rho -- Table tab:catalogue's 'always'. Note the "
            "SIGN PATTERN: R(theta) = [[cos, -sin], [sin, cos]], not its "
            "transpose; the C4 generator sign was corrected in the revision "
            "answering finding F-1-05 and Eq. eq:retgen "
            "is now stated as an exact identity."
        ),
    ),
    CatalogueCase(
        case_id="C4-boundary-rho0",
        entry_id="C4",
        position="boundary",
        parameters="rho = 0",
        matrix=mat_real(((1, 0), (0, 1))),
        lossless=True,
        determinant=None,
        derives_from="R(0) = 1. The endpoint 0 is in the declared domain [0, 2 pi).",
    ),
    # --- C5 mirror --------------------------------------------------------
    CatalogueCase(
        case_id="C5-boundary-ideal",
        entry_id="C5",
        position="boundary",
        parameters="R_H = R_V = 1, phi_H = phi_V = 0, fl = false (THE DEFAULT)",
        matrix=mat_real(((1, 0), (0, 1))),
        lossless=True,
        determinant=None,
        derives_from=(
            "Eq. eq:mirror with F = 1 at the DEFAULT fl = false, which Section "
            "2.5 `mirror_handedness` fixes ('an explicit boolean per mirror, "
            "DEFAULT false ... and NEVER APPLIED IMPLICITLY'). Lossless exactly "
            "at R_H = R_V = 1 (Table tab:catalogue)."
        ),
    ),
    CatalogueCase(
        case_id="C5-flip",
        entry_id="C5",
        position="boundary",
        parameters="R_H = R_V = 1, phi_H = phi_V = 0, fl = true",
        matrix=mat_real(((1, 0), (0, -1))),
        lossless=True,
        determinant=None,
        derives_from=(
            "The same element with the handedness flip DECLARED true: "
            "F = diag(1, -1). It differs from C5-boundary-ideal, it is still "
            "unitary, and the difference is observable downstream -- which is "
            "why Section 2.5 makes it an explicit boolean 'documented as A "
            "COORDINATE-FRAME CHOICE and never applied implicitly'."
        ),
    ),
    CatalogueCase(
        case_id="C5-interior",
        entry_id="C5",
        position="interior",
        parameters="R_H = 9/25, R_V = 1, phi_H = 0, phi_V = pi, fl = false",
        matrix=mat_real(((F(3, 5), 0), (0, -1))),
        lossless=False,
        determinant=None,
        derives_from=(
            "Eq. eq:mirror: diag(sqrt(R_H), sqrt(R_V)) diag(e^{i phi_H}, "
            "e^{i phi_V}) = diag(3/5, 1) diag(1, -1) = diag(3/5, -1). NOT "
            "lossless (R_H != 1). This is the entry's own reason for existing: "
            "'a real dielectric mirror has phi_H != phi_V, and that s/p phase "
            "difference is A COMMON AND EASILY FORGOTTEN SOURCE OF POLARIZATION "
            "ROTATION in a folded receiver'."
        ),
    ),
    # --- C6 phase shifter -------------------------------------------------
    CatalogueCase(
        case_id="C6-boundary",
        entry_id="C6",
        position="boundary",
        parameters="phi = (0, pi)",
        matrix=mat_real(((1, 0), (0, -1))),
        lossless=True,
        determinant=None,
        derives_from=(
            "Section 4.3 entry C6: diagonal with unimodular entries, unitary at "
            "every parameter tuple (Table tab:catalogue, 'always')."
        ),
    ),
    CatalogueCase(
        case_id="C6-interior",
        entry_id="C6",
        position="interior",
        parameters="phi = (pi/2, pi/2)",
        matrix=((im_(1), rt(0)), (rt(0), im_(1))),
        lossless=True,
        determinant=None,
        derives_from=(
            "diag(i, i). Unitary. Note that this element is a GLOBAL phase on "
            "its support and would be invisible if that support were one port's "
            "modes and nothing recombined downstream (Corollary cor:phases) -- "
            "and visible otherwise. The catalogue carries it either way."
        ),
    ),
    # --- C7 loss ----------------------------------------------------------
    CatalogueCase(
        case_id="C7-boundary-unit",
        entry_id="C7",
        position="boundary",
        parameters="eta = (1, 1)",
        matrix=mat_real(((1, 0), (0, 1))),
        lossless=True,
        determinant=None,
        derives_from=(
            "Section 4.3 entry C7: diag(sqrt(eta_m)). Lossless exactly when "
            "EVERY eta_m = 1 (Table tab:catalogue)."
        ),
    ),
    CatalogueCase(
        case_id="C7-interior",
        entry_id="C7",
        position="interior",
        parameters="eta = (1, 1/4)",
        matrix=mat_real(((1, 0), (0, F(1, 2)))),
        lossless=False,
        determinant=None,
        derives_from=(
            "diag(1, sqrt(1/4)) = diag(1, 1/2). One eta below 1 is enough to "
            "lose losslessness, and the element is still a contraction (Lemma "
            "lem:attenuated with V = 1, D_1 = 1)."
        ),
    ),
    CatalogueCase(
        case_id="C7-boundary-zero",
        entry_id="C7",
        position="boundary",
        parameters="eta = (1, 0)",
        matrix=mat_real(((1, 0), (0, 0))),
        lossless=False,
        determinant=None,
        derives_from=(
            "The other endpoint: eta = 0 blocks the mode entirely. Still a "
            "local element -- Gamma^dagger Gamma = diag(1, 0) <= 1 -- so "
            "Theorem thm:catalogue-admissibility covers it, and it is not lossless."
        ),
    ),
    CatalogueCase(
        case_id="C7-decibel-20",
        entry_id="C7",
        position="interior",
        parameters="L_dB = 20 on mode m1, converted at validation to eta = 1/100",
        matrix=mat_real(((1, 0), (0, F(1, 10)))),
        lossless=False,
        determinant=None,
        derives_from=(
            "Section 2.4, first bullet: 'A parameter offered in decibels "
            "(eta = 10^{-L_dB/10}) ... IS CONVERTED AT VALIDATION AND THE "
            "CONVERTED VALUE IS WHAT THE ARTIFACT CARRIES; THE PRESENTATION IS "
            "NOT A SECOND SOURCE OF TRUTH.' At L_dB = 20, eta = 10^{-2} = "
            "1/100 EXACTLY and sqrt(eta) = 1/10 EXACTLY, so the whole element "
            "is rational. THE THREE EXACT DECADES ARE FROZEN AS PARAMETER "
            "CONVERSIONS in DECIBEL_CONVERSIONS: L_dB = 0 -> eta = 1, "
            "L_dB = 10 -> eta = 1/10, L_dB = 20 -> eta = 1/100. Only L_dB = 0 "
            "and L_dB = 20 have a rational AMPLITUDE, so only those two can be "
            "frozen as matrices; at L_dB = 10 the amplitude 1/sqrt(10) is "
            "irrational AND IS NOT IN Q[sqrt2], so this file freezes the "
            "converted PARAMETER and no matrix, rather than approximating one."
        ),
    ),
    # --- C8 polarizer -----------------------------------------------------
    CatalogueCase(
        case_id="C8-interior",
        entry_id="C8",
        position="interior",
        parameters="theta with cos = 3/5, sin = 4/5, t = 1, t_perp = 0",
        matrix=mat_real(((F(9, 25), F(12, 25)), (F(12, 25), F(16, 25)))),
        lossless=False,
        determinant=None,
        derives_from=(
            "Eq. eq:polarizer in its second form, R(theta) diag(sqrt t, "
            "sqrt t_perp) R(theta)^T = [[c^2, c s], [s c, s^2]] at t = 1, "
            "t_perp = 0. It is the rank-one projector onto |e_theta>: trace 1, "
            "determinant (9/25)(16/25) - (12/25)^2 = 0. A contraction, and NOT "
            "lossless -- 'THE BLOCKED POLARIZATION IS LOSS' -- with equality "
            "exactly at t = t_perp = 1."
        ),
    ),
    CatalogueCase(
        case_id="C8-boundary-identity",
        entry_id="C8",
        position="boundary",
        parameters="theta arbitrary, t = t_perp = 1",
        matrix=mat_real(((1, 0), (0, 1))),
        lossless=True,
        determinant=None,
        derives_from=(
            "Table tab:catalogue for C8: lossless exactly when "
            "t = t_perp = 1, 'THEN THE ELEMENT IS THE IDENTITY' -- because "
            "R(theta) diag(1, 1) R(theta)^T = 1 for every theta. The one "
            "parameter tuple at which a polarizer is lossless is the one at "
            "which it is not a polarizer."
        ),
    ),
    CatalogueCase(
        case_id="C8-partial",
        entry_id="C8",
        position="interior",
        parameters="theta = 0, t = 1, t_perp = 1/4",
        matrix=mat_real(((1, 0), (0, F(1, 2)))),
        lossless=False,
        determinant=None,
        derives_from=(
            "A LEAKY polarizer: diag(sqrt 1, sqrt(1/4)) = diag(1, 1/2) at "
            "theta = 0. Contractive, not lossless. Note that it has the SAME "
            "matrix as C7-interior: the catalogue entries are distinguished by "
            "their declared parameters and their SITE, not by their matrices, "
            "which is why the efficiency record of Theorem thm:efficiency (iv) lists "
            "the declaring ELEMENT beside every transmittance."
        ),
    ),
    # --- C9 mode routing --------------------------------------------------
    CatalogueCase(
        case_id="C9-swap",
        entry_id="C9",
        position="interior",
        parameters="the transposition of m0 and m1",
        matrix=mat_real(((0, 1), (1, 0))),
        lossless=True,
        determinant=None,
        derives_from=(
            "Section 4.3 entry C9: (Gamma_C9)_{ij} = delta_{i, pi(j)}, a "
            "permutation matrix, unitary always. Remark rem:edgemeaning: this "
            "is 'how the declared graph's edges become matrix entries'."
        ),
    ),
    CatalogueCase(
        case_id="C9-identity",
        entry_id="C9",
        position="boundary",
        parameters="the identity permutation",
        matrix=mat_real(((1, 0), (0, 1))),
        lossless=True,
        determinant=None,
        derives_from="The identity permutation, the trivial endpoint of C9's domain.",
    ),
    # --- C10 generic block ------------------------------------------------
    CatalogueCase(
        case_id="C10-admissible",
        entry_id="C10",
        position="interior",
        parameters="the supplied matrix diag(1/2, 1/2), CHECKED",
        matrix=mat_real(((F(1, 2), 0), (0, F(1, 2)))),
        lossless=False,
        determinant=None,
        derives_from=(
            "Section 4.3 entry C10: admitted AFTER the explicit check "
            "Gamma^dagger Gamma <= 1, here diag(1/4, 1/4) <= 1. Not lossless: "
            "the check with equality fails. C10 is 'THE ONLY ENTRY for which "
            "the check of Theorem thm:compilation-well-defined (iv)(E1) IS NOT "
            "REDUNDANT-BY-THEOREM'."
        ),
    ),
    CatalogueCase(
        case_id="C10-lossless",
        entry_id="C10",
        position="boundary",
        parameters="the supplied matrix [[0, 1], [1, 0]], CHECKED",
        matrix=mat_real(((0, 1), (1, 0))),
        lossless=True,
        determinant=None,
        derives_from=(
            "The same check with EQUALITY: Gamma^dagger Gamma = 1, so the "
            "supplied block is lossless. C10 'is what makes ROUTE (ii) A "
            "SPECIAL CASE OF ROUTE (iii)': the original fixed-device scope is "
            "recovered by declaring exactly one C10 block spanning the whole "
            "receiver."
        ),
    ),
)

#: The decibel conversions of Section 2.4, at the three exponents where
#: 10^{-L_dB/10} is exactly rational. THE CONVERTED VALUE IS WHAT THE ARTIFACT
#: CARRIES. The splitting-ratio presentation named in the same sentence is
#: given NO conversion rule by the contract and is routed as change request
#: CR-2; NO frozen case uses one.
DECIBEL_CONVERSIONS: tuple[tuple[int, F], ...] = (
    (0, F(1)),
    (10, F(1, 10)),
    (20, F(1, 100)),
)


O_RP_CATALOGUE = RPOracleEntry(
    oracle_id="O-RP-CATALOGUE",
    claims=("RC3",),
    kind="toy-instance",
    subject=(
        "Every catalogue entry C1-C10 at an interior and a boundary parameter "
        "tuple, with its lossless verdict; the retarder's KEPT phase beside the "
        "dropped-phase variant; the beamsplitter real at phi = 0 with "
        "det = -1; and the 50:50 case whose Grams are rational though its "
        "amplitudes are not."
    ),
    derivation="""\
Table tab:catalogue with Theorem thm:catalogue-admissibility and Lemma lem:attenuated. Twenty-eight
cases are frozen in CATALOGUE_CASES, each with its own derivation; what follows
is what the SET pins.

EVERY ENTRY IS COVERED, INTERIOR AND BOUNDARY. Theorem thm:catalogue-admissibility is a statement
about THE WHOLE DECLARED DOMAIN -- "for every entry type C1-C10 and EVERY
parameter tuple in the domain declared above" -- so a set of interior points
alone would not exercise it. Each entry therefore carries at least one case at a
domain endpoint: x = 0 and x = 1 (C1), the ideal t_H = 1, t_V = 0 (C2),
delta = 0 (C3), rho = 0 (C4), R = 1 (C5), phi = 0 (C6), eta = 1 and eta = 0
(C7), t = t_perp = 1 (C8), the identity permutation (C9), and the equality case
of the explicit check (C10).

THE LOSSLESS COLUMN IS PART OF THE CLAIM, not a gloss: Theorem thm:catalogue-admissibility says the
element is lossless "EXACTLY on the subfamily named in Table tab:catalogue", an
IFF. Every case carries its verdict, and each entry has at least one case on
each side of its own iff except C4, C6 and C9, whose column reads "always" and
for which no lossy case exists to freeze.

THE HALF-OPEN DOMAINS ARE A TRAP AND ARE MARKED. C3's delta lies in
[0, 2 pi) and its theta in [0, pi); C4's rho and C5's and C6's phi in [0, 2 pi).
The endpoint that is IN the domain is frozen as a case; the endpoint that is
OUT of it is frozen as the (E1) refusal G-E1-VIOLATION in Group RP-B, at
delta = 2 pi, where the clipped value delta = 0 would be admissible and wrong.

THE RETARDER PHASE IS FROZEN TWICE, ON PURPOSE. C3-hwp-rational carries the
physical factor exp(-i delta / 2) = -i that Section 2.5
`waveplate_convention` forbids dropping; C3-hwp-DROPPED-PHASE is the real
matrix an implementation produces if it drops it. THE TWO DIFFER, BOTH ARE
UNITARY, AND BOTH PASS EVERY ADMISSIBILITY CHECK IN THE CONTRACT. Whether the
difference is observable is Corollary cor:phases, a theorem WITH A HYPOTHESIS --
the unitary must act inside one port's modes and after all interference -- and
Example ex:bb84 verifies that hypothesis for its own receiver and says in as
many words that the conclusion is "a statement about THIS receiver and THIS
factor, not about phases in general". Freezing only the correct matrix would let
an implementation that drops phases pass on the BB84 instance; freezing both
records the difference.

THE BEAMSPLITTER SIGN. Section 2.5 `beamsplitter_convention` fixes the core as
"real at phi = 0 with det B = -1", and every C1 case carries its determinant:
-1 at the three lossless tuples, -1/2 at the lossy one. The sign is "a
convention artifact" (Theorem thm:catalogue-admissibility proof, case C1) and is exactly what
distinguishes this convention from the symmetric one -- which is compared,
exactly, in Group RP-E and routed as change request CR-3.

THE 50:50 CASE IS THE REPRESENTATION ARGUMENT IN MINIATURE. C1-half has
amplitudes sqrt2/2, which are not rational; its port Grams under two single-mode
ports are (1/2)[[1, 1], [1, 1]] and (1/2)[[1, -1], [-1, 1]], which are. Theorem
thm:representation-independence (i) says the click statistics see only the Grams. So the irrational part
of a beamsplitter is exactly the part no measurement reveals -- and freezing the
amplitudes exactly anyway, in Q[sqrt2], is what lets the integrity test verify
the Grams against them through Eq. eq:gramdef instead of asserting both.

WHAT IS DELIBERATELY NOT FROZEN. The decibel presentation is frozen as a
PARAMETER conversion at the three exponents where it is exactly rational
(DECIBEL_CONVERSIONS), and as a matrix only at L_dB = 0 and L_dB = 20, where the
AMPLITUDE sqrt(eta) is also rational. At L_dB = 10 the amplitude is 1/sqrt(10),
which is irrational AND OUTSIDE Q[sqrt2]; approximating it would be the one
thing this file must not do, so no matrix is frozen there. THE SPLITTING-RATIO
PRESENTATION NAMED IN THE SAME SENTENCE OF SECTION 2.4 IS GIVEN NO CONVERSION
RULE BY THE CONTRACT AND IS ROUTED AS CHANGE REQUEST CR-2; no frozen case uses
one, and every beamsplitter case declares x directly.
""",
)


# ===========================================================================
#  Group RP-D -- port Grams, the deficiency, and exact vacuum elimination (RC4)
# ===========================================================================
#
#  Every instrument below is written with rows = OUTPUTS and columns = the
#  DECLARED INPUT MODES, which is Section 2.5 `matrix_convention` restricted to
#  the columns Inp (Def. def:gram writes Gamma_Inp for exactly that). The Grams
#  are then Eq. eq:gramdef, (A_k)_{j j'} = sum over i in P_k of
#  conj(Gamma_{i j}) Gamma_{i j'}, and the integrity test recomputes every one
#  of them from the frozen Gamma_Inp rather than taking both on trust.

INSTRUMENT_CASES: tuple[InstrumentCase, ...] = (
    InstrumentCase(
        case_id="I-BB84",
        input_mode_labels=("Chan_H", "Chan_V"),
        output_mode_labels=("Z_H", "Z_V", "X_H", "X_V"),
        port_map=(("H", (0,)), ("V", (1,)), ("+", (2,)), ("-", (3,))),
        unmonitored=(),
        gamma_inp=(
            (HALF_R2, rt(0)),
            (rt(0), HALF_R2),
            (im_(F(-1, 2)), im_(F(-1, 2))),
            (im_(F(-1, 2)), im_(F(1, 2))),
        ),
        grams=(
            ("H", mat_real(((F(1, 2), 0), (0, 0)))),
            ("V", mat_real(((0, 0), (0, F(1, 2))))),
            ("+", mat_real(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4))))),
            ("-", mat_real(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4))))),
        ),
        a_sigma=mat_real(((1, 0), (0, 1))),
        deficiency=mat_real(((0, 0), (0, 0))),
        ranks=(("H", 1), ("V", 1), ("+", 1), ("-", 1)),
        lossless=True,
        derives_from=(
            "THE CHANNEL-ONLY RECEIVER OF EXAMPLE ex:bb84, at p_Z = p_X = 1/2. "
            "Eq. eq:bb84G with the Led columns dropped -- which is the vacuum "
            "elimination of Theorem thm:port-grams (iv), an IDENTITY and not a second "
            "model -- leaves the left 4x2 block with rows ordered (H, V, +, -) "
            "and columns (Chan_H, Chan_V): row H = (sqrt(p_Z), 0) = "
            "(sqrt2/2, 0); row V = (0, sqrt2/2); row + = "
            "(-i sqrt(p_X/2), -i sqrt(p_X/2)) = (-i/2, -i/2), since "
            "p_X/2 = 1/4; row - = (-i/2, +i/2). THE FACTOR -i IS THE HWP PHASE "
            "and is carried. Eq. eq:gramdef then gives Eq. eq:bb84grams: "
            "A_H = p_Z |H><H| = (1/2) diag(1, 0); A_V = (1/2) diag(0, 1); "
            "A_+ = p_X |+><+| = (1/4)[[1, 1], [1, 1]]; A_- = "
            "(1/4)[[1, -1], [-1, 1]] -- the -i cancels in every Gram, since "
            "conj(-i)(-i) = 1 and conj(-i)(+i) = -1. A_Sigma = "
            "(1/2)(|H><H| + |V><V|) + (1/2)(|+><+| + |-><-|) = 1, so the "
            "deficiency is ZERO and the receiver is lossless, as the "
            "construction promises. Every Gram has rank one, so by Theorem "
            "thm:representation-independence (iv) THIS RECEIVER IS EXACTLY A ONE-MODE-PER-PORT DEVICE "
            "-- a CERTIFIED branch, never a default (Remark rem:rankone)."
        ),
    ),
    InstrumentCase(
        case_id="I-BS",
        input_mode_labels=("Chan",),
        output_mode_labels=("out_0", "out_1"),
        port_map=(("1", (0,)), ("2", (1,))),
        unmonitored=(),
        gamma_inp=((HALF_R2,), (HALF_R2,)),
        grams=(("1", mat_real(((F(1, 2),),))), ("2", mat_real(((F(1, 2),),)))),
        a_sigma=mat_real(((1,),)),
        deficiency=mat_real(((0,),)),
        ranks=(("1", 1), ("2", 1)),
        lossless=True,
        derives_from=(
            "THE TWO-DETECTOR BEAMSPLITTER RECEIVER: catalogue entry C1 at "
            "x = 1/2, phi = 0, y = 0 (case C1-half), with ONE declared channel "
            "input mode and the second input of the beamsplitter left "
            "UNDECLARED. Assumption ass:vac puts vacuum on it and Lemma "
            "lem:vacelim eliminates its column EXACTLY, so Gamma_Inp is the "
            "single column (sqrt2/2, sqrt2/2)^T. Eq. eq:gramdef gives "
            "A_1 = A_2 = 1/2 on the ONE-DIMENSIONAL input space, A_Sigma = 1, "
            "deficiency 0. THE BLOCKS ARE ONE-DIMENSIONAL AT EVERY PHOTON "
            "NUMBER -- binom(1 + n - 1, n) = 1 -- which is why this receiver is "
            "the one where the multiclick BOUND and the multiclick EIGENVALUE "
            "can be compared exactly (Group RP-F)."
        ),
    ),
    InstrumentCase(
        case_id="I-RANK2",
        input_mode_labels=("Chan_0", "Chan_1"),
        output_mode_labels=("out_0", "out_1", "out_2"),
        port_map=(("1", (0, 1)), ("2", (2,))),
        unmonitored=(),
        gamma_inp=mat_real(((F(1, 2), 0), (0, F(1, 4)), (0, F(1, 2)))),
        grams=(
            ("1", mat_real(((F(1, 4), 0), (0, F(1, 16))))),
            ("2", mat_real(((0, 0), (0, F(1, 4))))),
        ),
        a_sigma=mat_real(((F(1, 4), 0), (0, F(5, 16)))),
        deficiency=mat_real(((F(3, 4), 0), (0, F(11, 16)))),
        ranks=(("1", 2), ("2", 1)),
        lossless=False,
        derives_from=(
            "A PORT THAT COLLECTS TWO MODES, which is the case Remark "
            "rem:rankone insists the contract does not assume away: 'a "
            "multimode fiber onto one active area, two spatial modes onto one "
            "detector, simply has rk A_k > 1'. Port 1 collects out_0 and "
            "out_1, so A_1 = (row 0)^dagger (row 0) + (row 1)^dagger (row 1) = "
            "diag(1/4, 0) + diag(0, 1/16) = diag(1/4, 1/16), OF RANK TWO. "
            "Theorem thm:port-grams (ii)'s bound rk A_k <= min(|Inp|, |P_k|) = "
            "min(2, 2) = 2 IS ATTAINED. Port 2 collects one mode and has rank "
            "one, so the bound min(2, 1) = 1 is attained there too. "
            "A_Sigma = diag(1/4, 5/16) <= 1 and the deficiency "
            "diag(3/4, 11/16) is positive semidefinite (Theorem thm:port-grams (i)). "
            "By Theorem thm:representation-independence (iv) NO one-mode-per-port instrument "
            "reproduces this POVM."
        ),
    ),
    InstrumentCase(
        case_id="I-UNMONITORED",
        input_mode_labels=("Chan_0", "Chan_1"),
        output_mode_labels=("out_0", "out_1"),
        port_map=(("1", (0,)),),
        unmonitored=(1,),
        gamma_inp=mat_real(((F(1, 2), 0), (0, F(1, 2)))),
        grams=(("1", mat_real(((F(1, 4), 0), (0, 0)))),),
        a_sigma=mat_real(((F(1, 4), 0), (0, 0))),
        deficiency=mat_real(((F(3, 4), 0), (0, 1))),
        ranks=(("1", 1),),
        lossless=False,
        derives_from=(
            "AN OUTPUT MODE IN NO PORT, which Remark rem:unmonitored says is a "
            "DECLARATION and never an inference. out_1 is undetected, so it "
            "contributes to no A_k, and the deficiency picks up both summands "
            "of Eq. eq:deficiencyid: "
            "1 - Gamma_Inp^dagger Gamma_Inp = 1 - diag(1/4, 1/4) = "
            "diag(3/4, 3/4) ('left through the dilation') plus "
            "Gamma_Inp^dagger E_un Gamma_Inp = diag(0, 1/4) ('reached an "
            "unmonitored declared mode'), summing to diag(3/4, 1) = "
            "1 - A_Sigma. THIS IS THE CASE THAT DISTINGUISHES THE TWO SUMMANDS: "
            "in every other instrument frozen here one of them is zero."
        ),
    ),
    InstrumentCase(
        case_id="I-DILATION-SUB",
        input_mode_labels=("m0",),
        output_mode_labels=("m0",),
        port_map=(("1", (0,)),),
        unmonitored=(),
        gamma_inp=mat_real(((F(3, 5),),)),
        grams=(("1", mat_real(((F(9, 25),),))),),
        a_sigma=mat_real(((F(9, 25),),)),
        deficiency=mat_real(((F(16, 25),),)),
        ranks=(("1", 1),),
        lossless=False,
        derives_from=(
            "THE SUB-UNITARY DESCRIPTION: a bare contraction on the declared "
            "modes, catalogue entry C7 at eta = 9/25 so that sqrt(eta) = 3/5. "
            "A_1 = 9/25, deficiency 16/25, and Eq. eq:deficiencyid's SECOND "
            "summand is zero because there is no unmonitored declared mode -- "
            "the missing amplitude 'left through the dilation'. Paired with "
            "I-DILATION-UNITARY below."
        ),
    ),
    InstrumentCase(
        case_id="I-DILATION-UNITARY",
        input_mode_labels=("m0",),
        output_mode_labels=("m0", "env"),
        port_map=(("1", (0,)),),
        unmonitored=(1,),
        gamma_inp=mat_real(((F(3, 5),), (F(4, 5),))),
        grams=(("1", mat_real(((F(9, 25),),))),),
        a_sigma=mat_real(((F(9, 25),),)),
        deficiency=mat_real(((F(16, 25),),)),
        ranks=(("1", 1),),
        lossless=True,
        derives_from=(
            "THE UNITARY-DILATION DESCRIPTION OF THE SAME DEVICE, and the point "
            "of the pair: Theorem thm:port-grams (v) says the two 'induce THE SAME "
            "measurement'. Here U = B(9/25, 0) = [[3/5, 4/5], [4/5, -3/5]] is "
            "the unitary of catalogue case C1-interior on the declared mode m0 "
            "plus one ancilla env, which carries vacuum at the input "
            "(Assumption ass:vac) and is monitored by no port -- it is the "
            "environment and is DISCARDED. Gamma_Inp is U's first column. "
            "Eq. eq:gramdef gives A_1 = |U_{00}|^2 = 9/25, IDENTICAL to "
            "I-DILATION-SUB's, so the Grams, the deficiency and hence every "
            "POVM element agree EXACTLY -- not approximately. What differs is "
            "WHERE Eq. eq:deficiencyid puts the missing 16/25: here "
            "1 - Gamma_Inp^dagger Gamma_Inp = 1 - (9/25 + 16/25) = 0 and the "
            "unmonitored summand |U_{10}|^2 = 16/25 carries all of it, the "
            "mirror image of I-DILATION-SUB. Theorem thm:port-grams (v)'s hypothesis "
            "is met by construction: U is unitary and its block from Inp to the "
            "port modes is Gamma's. "
            "NOTE THE `lossless` FIELD, WHICH IS TRUE HERE AND FALSE FOR "
            "I-DILATION-SUB ALTHOUGH THE TWO DESCRIBE ONE DEVICE. The field is "
            "Definition def:embed's property of Gamma_Inp -- is the restriction "
            "to the declared input columns an ISOMETRY -- and here it is, "
            "9/25 + 16/25 = 1, because the dilation retains the amplitude the "
            "sub-unitary description discards. THE DEFICIENCY IS 16/25 IN BOTH: "
            "losslessness of Gamma_Inp and zero deficiency are DIFFERENT "
            "properties, and Eq. eq:deficiencyid is precisely the statement "
            "that the deficiency splits into what left through the dilation "
            "and what reached an unmonitored declared mode. An implementation "
            "that conflated the two would report this receiver as lossy in one "
            "description and lossless in the other WITHOUT NOTICING THAT BOTH "
            "ANSWERS ARE ABOUT DIFFERENT QUESTIONS."
        ),
    ),
    InstrumentCase(
        case_id="I-SINGULAR",
        input_mode_labels=("Chan_0", "Chan_1"),
        output_mode_labels=("out_0", "out_1"),
        port_map=(("1", (0,)), ("2", (1,))),
        unmonitored=(),
        gamma_inp=((HALF_R2, rt(0)), (HALF_R2, rt(0))),
        grams=(
            ("1", mat_real(((F(1, 2), 0), (0, 0)))),
            ("2", mat_real(((F(1, 2), 0), (0, 0)))),
        ),
        a_sigma=mat_real(((1, 0), (0, 0))),
        deficiency=mat_real(((0, 0), (0, 1))),
        ranks=(("1", 1), ("2", 1)),
        lossless=False,
        derives_from=(
            "A RECEIVER WITH AN INPUT DIRECTION NO PORT SEES, which is the "
            "hypothesis Theorem thm:coarse-graining (iii) needs: A_Sigma = diag(1, 0) is "
            "SINGULAR, lmin(A_Sigma) = 0. The second input mode reaches neither "
            "port -- both ports read only Chan_0, through a 50:50 splitter -- "
            "so the deficiency diag(0, 1) is the whole of that direction. By "
            "Lemma lem:fock-block-spectrum, lmax(M_empty^{(n)}) = "
            "(1 - lmin(A_Sigma))^n = 1 at every n, so the no-click element "
            "reaches eigenvalue one in every block and every other element has "
            "a zero eigenvalue there. Used in Group RP-G for thm:coarse-graining (iii) and "
            "in Group RP-H for the bound that correctly returns zero."
        ),
    ),
    InstrumentCase(
        case_id="I-MZ",
        input_mode_labels=("in_0", "in_1"),
        output_mode_labels=("out_0", "out_1"),
        port_map=(("1", (0,)), ("2", (1,))),
        unmonitored=(),
        gamma_inp=mat_real(((1, 0), (0, 1))),
        grams=(
            ("1", mat_real(((1, 0), (0, 0)))),
            ("2", mat_real(((0, 0), (0, 1)))),
        ),
        a_sigma=mat_real(((1, 0), (0, 1))),
        deficiency=mat_real(((0, 0), (0, 0))),
        ranks=(("1", 1), ("2", 1)),
        lossless=True,
        derives_from=(
            "THE BALANCED MACH-ZEHNDER OF REMARK rem:wrongcheck AT phi = 0, and "
            "the case where the deficiency identity and a path-product audit "
            "DISAGREE. Eq. eq:mz: Gamma = B(1/2, 0) diag(1, e^{i phi}) "
            "B(1/2, 0) = (1/2)[[1 + e^{i phi}, 1 - e^{i phi}], "
            "[1 - e^{i phi}, 1 + e^{i phi}]], which at phi = 0 is the IDENTITY. "
            "Every declared transmittance in the chain is 1 (two lossless "
            "beamsplitters and a unitary phase shifter), the Grams are "
            "diag(1, 0) and diag(0, 1), A_Sigma = 1 and the deficiency is ZERO "
            "-- correctly, since all the light entering path 1 reaches port 1. "
            "The two sqrt2 factors of the individual beamsplitters cancel "
            "against each other, which is why this instrument is rational "
            "although its factors are not. Used in Group RP-J."
        ),
    ),
    InstrumentCase(
        case_id="I-PROBE",
        input_mode_labels=("Chan", "Led"),
        output_mode_labels=("out_0", "out_1"),
        port_map=(("1", (0,)), ("2", (1,))),
        unmonitored=(),
        gamma_inp=mat_real(((F(1, 2), F(1, 2)), (F(1, 2), F(-1, 2)))),
        grams=(
            ("1", mat_real(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4))))),
            ("2", mat_real(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4))))),
        ),
        a_sigma=mat_real(((F(1, 2), 0), (0, F(1, 2)))),
        deficiency=mat_real(((F(1, 2), 0), (0, F(1, 2)))),
        ranks=(("1", 1), ("2", 1)),
        lossless=False,
        derives_from=(
            "THE PROBE RECEIVER of Group RP-L: ONE channel mode and ONE "
            "declared source mode, the input basis ordered CHANNEL FIRST as "
            "Section 2.5 `subsystem_order` requires. It is catalogue entry C1 "
            "at x = 1/2, phi = 0 with per-output loss y_1 = y_2 = 1/2, so "
            "Gamma_Inp = diag(sqrt(1/2), sqrt(1/2)) B(1/2, 0) = "
            "(1/2)[[1, 1], [1, -1]] -- the two sqrt2 factors cancel and the "
            "instrument is rational. Eq. eq:gramdef gives "
            "A_1 = (1/4)[[1, 1], [1, 1]] and A_2 = (1/4)[[1, -1], [-1, 1]], "
            "both of rank one, with A_Sigma = diag(1/2, 1/2) and deficiency "
            "diag(1/2, 1/2). BOTH PORTS COUPLE TO THE PROBE MODE -- "
            "(A_1)_{Led,Led} = (A_2)_{Led,Led} = 1/4 -- which is what makes the "
            "prefactors of Theorem thm:gaussian-schur non-trivial and the collapse "
            "hypothesis fail (Remark rem:rc12tobound: 'gamma < 1 exactly when "
            "the probe is on AND couples to a port')."
        ),
    ),
    InstrumentCase(
        case_id="I-REM-N0",
        input_mode_labels=("Chan_0", "Chan_1"),
        output_mode_labels=("out_0", "out_1"),
        port_map=(("1", (0,)), ("2", (1,))),
        unmonitored=(),
        gamma_inp=((HALF_R2, rt(0)), (rt(0), HALF_R2)),
        grams=(
            ("1", mat_real(((F(1, 2), 0), (0, 0)))),
            ("2", mat_real(((0, 0), (0, F(1, 2))))),
        ),
        a_sigma=mat_real(((F(1, 2), 0), (0, F(1, 2)))),
        deficiency=mat_real(((F(1, 2), 0), (0, F(1, 2)))),
        ranks=(("1", 1), ("2", 1)),
        lossless=False,
        derives_from=(
            "REMARK rem:n0's OWN REALIZATION, at a = 1/2: 'K = 2 on two input "
            "modes with A_1 = a |0><0|, A_2 = a |1><1|, a in (0, 1): there "
            "c = 1 - a and d_1 = d_2 = 1'. Each port sees exactly one input "
            "direction, at amplitude sqrt(1/2). A_Sigma = (1/2) 1 gives "
            "lmax = 1/2 and c = 1/2; A_{[2] minus {1}} = A_2 = (1/2) diag(0, 1) "
            "gives lmin = 0 and d_1 = 1, and symmetrically d_2 = 1. Used in "
            "Group RP-H as the case where the collapse STEP fails at n = 0."
        ),
    ),
)


O_RP_GRAMS = RPOracleEntry(
    oracle_id="O-RP-GRAMS",
    claims=("RC4",),
    kind="toy-instance",
    subject=(
        "Port Grams from hand-computed instruments: positivity, the total "
        "bound, the rank bound and the deficiency; and the sub-unitary and "
        "unitary-dilation descriptions of one device giving IDENTICAL Grams."
    ),
    derivation="""\
Definition def:gram (Eq. eq:gramdef, Eq. eq:deficiency) and Theorem thm:port-grams.
Nine instruments are frozen in INSTRUMENT_CASES, each with its derivation. What
the SET pins:

(i) ADMISSIBILITY, on every one of them: A_k >= 0 (each is a sum of terms
(row)^dagger (row), manifestly positive semidefinite), sum_k A_k <= 1, and the
deficiency 1 - A_Sigma >= 0. Three are lossless with deficiency exactly zero
(I-BB84, I-BS, I-MZ) and six are not.

(ii) THE RANK BOUND rk A_k <= min(|Inp|, |P_k|) of Theorem thm:port-grams (ii), WITH
BOTH ARGUMENTS OF THE MINIMUM ATTAINED. I-RANK2's port 1 collects two modes on a
two-dimensional input space and has rank 2, attaining min(2, 2); its port 2
collects one mode and has rank 1, attaining min(2, 1). Every port of I-BB84 has
rank 1 = min(2, 1). No frozen instrument violates the bound, and none could: it
is a statement about the Gram of a matrix with |P_k| non-zero rows.

(iii) THE DEFICIENCY IDENTITY Eq. eq:deficiencyid, WITH BOTH SUMMANDS EXERCISED
SEPARATELY. In I-DILATION-SUB the second summand is zero and the whole 16/25 is
"left through the dilation"; in I-DILATION-UNITARY the FIRST summand is zero and
the whole 16/25 "reached an unmonitored declared mode"; in I-UNMONITORED both are
non-zero, diag(3/4, 3/4) and diag(0, 1/4), summing to diag(3/4, 1). An
implementation that dropped either summand would agree with the contract on some
of these and not on others.

(iv) VACUUM ELIMINATION IS EXACT, AND THE DILATION CHANGES NOTHING. I-BS drops
the beamsplitter's second input column outright (Lemma lem:vacelim), and
I-DILATION-SUB and I-DILATION-UNITARY are the same physical device described
both ways, with A_1 = 9/25 in each. Theorem thm:port-grams (iv) calls the column
restriction "an identity, not an approximation", and (v) says any dilation whose
block from Inp to the port modes agrees with Gamma's yields the same POVM. The
frozen pair is that statement as two matrices of different shapes with one Gram.

(v) THE OPERATIONAL INDEX ORDER. Section 3's closing paragraph fixes
(A_k)_{j j'} = sum over i in P_k of conj(Gamma_{i j}) Gamma_{i j'}, "which is
the operational reading of the Gram and fixes its index order beyond doubt". The
integrity test recomputes every frozen Gram from the frozen Gamma_Inp by that
formula, in exact Q[sqrt2] + i Q[sqrt2] arithmetic, so a transposed index is a
test failure and not a reading of a comment. I-BB84 is the case that would catch
it: its Grams A_+ and A_- are NOT symmetric under exchanging the two roles until
the -i phases cancel, and they cancel in exactly one of the two index orders.
""",
)


# ===========================================================================
#  Group RP-E -- representation independence (RC5)
# ===========================================================================

REPRESENTATION_INDEPENDENCE_CASES: tuple[RepresentationCase, ...] = (
    RepresentationCase(
        case_id="REP-BB84-PORT-PHASE",
        gamma_a=(
            (HALF_R2, rt(0)),
            (rt(0), HALF_R2),
            (im_(F(-1, 2)), im_(F(-1, 2))),
            (im_(F(-1, 2)), im_(F(1, 2))),
        ),
        gamma_b=(
            (HALF_R2, rt(0)),
            (rt(0), HALF_R2),
            (rt(F(1, 2)), rt(F(1, 2))),
            (im_(F(1, 2)), im_(F(-1, 2))),
        ),
        port_map_a=((0,), (1,), (2,), (3,)),
        port_map_b=((0,), (1,), (2,), (3,)),
        grams_a=(
            mat_real(((F(1, 2), 0), (0, 0))),
            mat_real(((0, 0), (0, F(1, 2)))),
            mat_real(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4)))),
            mat_real(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4)))),
        ),
        grams_b=(
            mat_real(((F(1, 2), 0), (0, 0))),
            mat_real(((0, 0), (0, F(1, 2)))),
            mat_real(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4)))),
            mat_real(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4)))),
        ),
        matrices_equal=False,
        grams_equal=True,
        one_mode_per_port=True,
        max_rank=1,
        derives_from=(
            "TWO DISTINCT INSTRUMENT MATRICES WITH THE SAME GRAMS, and hence "
            "the same POVM by Theorem thm:representation-independence (i). Gamma_b is I-BB84's "
            "Gamma_Inp with the '+' row multiplied by i and the '-' row by -1: "
            "i(-i/2, -i/2) = (1/2, 1/2) and -(-i/2, +i/2) = (i/2, -i/2). Each "
            "port collects ONE mode, so multiplying its row by a phase is "
            "exactly the port-local unitary of Theorem thm:representation-independence (iii), "
            "Gamma' = (direct sum of V_k) Gamma, and the Grams are unchanged "
            "because (e^{i phi} g)^dagger (e^{i phi} g) = g^dagger g. The "
            "frozen families are IDENTICAL matrix for matrix; the instrument "
            "matrices are not. Corollary cor:phases is the reading, WITH ITS "
            "HYPOTHESIS: the unitary acts inside one port's modes and after all "
            "interference has taken place."
        ),
    ),
    RepresentationCase(
        case_id="REP-BSCONV-OUTPUT-PHASE",
        gamma_a=mat_real(((F(3, 5), F(4, 5)), (F(4, 5), F(-3, 5)))),
        gamma_b=(
            (rt(F(3, 5)), rt(F(4, 5))),
            (im_(F(4, 5)), im_(F(-3, 5))),
        ),
        port_map_a=((0,), (1,)),
        port_map_b=((0,), (1,)),
        grams_a=(
            mat_real(((F(9, 25), F(12, 25)), (F(12, 25), F(16, 25)))),
            mat_real(((F(16, 25), F(-12, 25)), (F(-12, 25), F(9, 25)))),
        ),
        grams_b=(
            mat_real(((F(9, 25), F(12, 25)), (F(12, 25), F(16, 25)))),
            mat_real(((F(16, 25), F(-12, 25)), (F(-12, 25), F(9, 25)))),
        ),
        matrices_equal=False,
        grams_equal=True,
        one_mode_per_port=True,
        max_rank=1,
        derives_from=(
            "THE HALF OF REMARK rem:bsconv THAT COROLLARY cor:phases ACTUALLY "
            "COVERS. Gamma_b = diag(1, i) B(9/25, 0), an OUTPUT-side per-port "
            "phase, which is literally Theorem thm:representation-independence (iii)'s hypothesis, so "
            "the Grams agree: row 1 becomes (4i/5, -3i/5) and "
            "conj(4i/5)(4i/5) = 16/25, conj(4i/5)(-3i/5) = -12/25, exactly as "
            "before. Paired with REP-BSCONV-SYMMETRIC below, which is the half "
            "that is NOT covered."
        ),
    ),
    RepresentationCase(
        case_id="REP-BSCONV-SYMMETRIC",
        gamma_a=mat_real(((F(3, 5), F(4, 5)), (F(4, 5), F(-3, 5)))),
        gamma_b=(
            (rt(F(3, 5)), im_(F(4, 5))),
            (im_(F(4, 5)), rt(F(3, 5))),
        ),
        port_map_a=((0,), (1,)),
        port_map_b=((0,), (1,)),
        grams_a=(
            mat_real(((F(9, 25), F(12, 25)), (F(12, 25), F(16, 25)))),
            mat_real(((F(16, 25), F(-12, 25)), (F(-12, 25), F(9, 25)))),
        ),
        grams_b=(
            (
                (rt(F(9, 25)), im_(F(12, 25))),
                (im_(F(-12, 25)), rt(F(16, 25))),
            ),
            (
                (rt(F(16, 25)), im_(F(-12, 25))),
                (im_(F(12, 25)), rt(F(9, 25))),
            ),
        ),
        matrices_equal=False,
        grams_equal=False,
        one_mode_per_port=True,
        max_rank=1,
        derives_from=(
            "THE EVIDENCE FOR CHANGE REQUEST CR-4's SIBLING CR-3, computed "
            "exactly at x = 9/25 where every amplitude is rational. Gamma_b is "
            "the SYMMETRIC beamsplitter convention "
            "[[sqrt x, i sqrt(1-x)], [i sqrt(1-x), sqrt x]] that Remark "
            "rem:bsconv compares against B(x, 0). THE EXACT RELATION IS "
            "Gamma_b = diag(1, i) B(9/25, 0) diag(1, i): multiplying out, "
            "B diag(1, i) = [[3/5, 4i/5], [4/5, -3i/5]] and then "
            "diag(1, i) times that is [[3/5, 4i/5], [4i/5, -3 i^2 / 5]] = "
            "[[3/5, 4i/5], [4i/5, 3/5]]. SO THE TWO CONVENTIONS DIFFER BY AN "
            "OUTPUT-side phase AND AN INPUT-side one. Corollary cor:phases -- "
            "which is Theorem thm:representation-independence (iii) -- covers the output factor only, "
            "and REP-BSCONV-OUTPUT-PHASE freezes that it changes nothing. The "
            "INPUT factor conjugates every Gram: "
            "A_k^sym = diag(1, -i) A_k diag(1, i), which on A_1 gives "
            "[[9/25, (12/25) i], [-(12/25) i, 16/25]] -- the frozen grams_b. "
            "THE TWO GRAM FAMILIES ARE THEREFORE DIFFERENT, not equal, and are "
            "unitarily equivalent under a fixed input-path phase. Nothing in "
            "the contract depends on the resolution: Section 2.5 FIXES the "
            "convention to B(x, phi), and rem:bsconv is a remark no claim "
            "consumes. Routed, with this pair as the evidence."
        ),
    ),
    RepresentationCase(
        case_id="REP-REALIZE-RANK2",
        gamma_a=mat_real(((F(1, 2), 0), (0, F(1, 4)), (0, F(1, 2)))),
        gamma_b=mat_real(((F(1, 2), 0), (0, F(1, 4)), (0, 0), (0, F(1, 2)))),
        port_map_a=((0, 1), (2,)),
        port_map_b=((0, 1), (2, 3)),
        grams_a=(
            mat_real(((F(1, 4), 0), (0, F(1, 16)))),
            mat_real(((0, 0), (0, F(1, 4)))),
        ),
        grams_b=(
            mat_real(((F(1, 4), 0), (0, F(1, 16)))),
            mat_real(((0, 0), (0, F(1, 4)))),
        ),
        matrices_equal=False,
        grams_equal=True,
        one_mode_per_port=False,
        max_rank=2,
        derives_from=(
            "THEOREM thm:representation-independence (ii), REALIZABILITY, ON I-RANK2's ADMISSIBLE "
            "FAMILY. The construction in the proof is C_k = A_k^{1/2}, the "
            "positive semidefinite square root, stacked as the rows of port k: "
            "A_1 = diag(1/4, 1/16) has A_1^{1/2} = diag(1/2, 1/4) and "
            "A_2 = diag(0, 1/4) has A_2^{1/2} = diag(0, 1/2), so Gamma_b has "
            "four rows in two ports of two. Gamma_b^dagger Gamma_b = "
            "diag(1/4, 1/16 + 1/4) = diag(1/4, 5/16) <= 1, so it IS a "
            "contraction, and its Grams are the declared family. THE TWO "
            "INSTRUMENTS HAVE DIFFERENT SHAPES, DIFFERENT PORT MAPS AND THE "
            "SAME GRAMS -- which is what makes route (i) a primitive route and "
            "not a convenience: an admissible family is a receiver, and the "
            "matrix that realizes it is not unique, not even up to phase, once "
            "a port has rank above one. The proof's remark that 'discarding the "
            "zero rows of C_k leaves rk A_k monitored modes in port k' is "
            "visible here: port 2's first row is zero and its rank is one."
        ),
    ),
)

#: The one-mode-per-port criterion of Theorem thm:representation-independence (iv), decided from the
#: emitted Grams and NEVER assumed. Remark rem:rankone: it is 'a CERTIFIED
#: branch, never a default', and Remark rem:effrank names the one operation
#: that can change the answer (Group RP-J).
ONE_MODE_PER_PORT_CASES: tuple[tuple[str, bool, int, str], ...] = (
    (
        "I-BB84",
        True,
        1,
        "Every A_k = p |u><u| has rank one, so a one-mode-per-port instrument "
        "reproduces the POVM, and its rows are unique up to a phase: for "
        "A_H = (1/2)|H><H| the row is e^{i phi} sqrt(1/2) <H|, and I-BB84's own "
        "row H = (sqrt2/2, 0) is that at phi = 0; for A_+ = (1/2)|+><+| it is "
        "e^{i phi} (1/2)(1, 1), and I-BB84's row + = (-i/2, -i/2) is that at "
        "phi = -pi/2. THE PHASE IS THE HWP FACTOR, and Theorem thm:representation-independence (iv)'s "
        "'unique up to phase' is exactly why it is unobservable here.",
    ),
    (
        "I-RANK2",
        False,
        2,
        "A_1 = diag(1/4, 1/16) has rank TWO, so by Theorem thm:representation-independence (iv) NO "
        "one-mode-per-port instrument induces this POVM. The direction that "
        "matters is the contrapositive: assuming one mode per port here would "
        "silently replace the receiver by a different one, which is the "
        "ARCHITECTURE_SPEC.md Section 5.2 prohibition Remark rem:rankone "
        "quotes.",
    ),
    (
        "I-PROBE",
        True,
        1,
        "Both Grams are rank-one projectors scaled by 1/2, on the FULL input "
        "space C^Inp including the probe mode. The criterion is about the "
        "Grams on Inp, not about the channel block: the conditioned effective "
        "Grams of Theorem thm:gaussian-schur are a different object and the "
        "criterion is not applied to them anywhere in the contract.",
    ),
)

#: Corollary cor:extinction at |Inp| = 2, and the case that shows it does NOT
#: generalize.
EXTINCTION_CASES: tuple[tuple[str, str, bool, int, str], ...] = (
    (
        "EXT-BB84-H",
        "I-BB84 port H, A_H = (1/2) diag(1, 0)",
        True,
        1,
        "|Inp| = 2 and the unit vector v = |V> has v^dagger A_H v = 0 -- a "
        "polarization the port extinguishes completely -- so by Corollary "
        "cor:extinction rk A_H <= 1, and it is exactly 1.",
    ),
    (
        "EXT-RANK2",
        "I-RANK2 port 1, A_1 = diag(1/4, 1/16)",
        False,
        2,
        "No null direction exists: A_1 is positive DEFINITE. So the criterion "
        "correctly reports rank 2, and there is no extinguished polarization.",
    ),
    (
        "EXT-DIM3-CAVEAT",
        "a positive semidefinite A on C^3 with a one-dimensional kernel",
        False,
        2,
        "THE CAVEAT, frozen because it is stated and is easy to over-read: "
        "Corollary cor:extinction says 'for |Inp| > 2 the two conditions are "
        "NOT equivalent: the existence of one null direction of a positive "
        "semidefinite A_k says only rk A_k <= |Inp| - 1'. At |Inp| = 3 a single "
        "extinguished direction leaves rank 2, not rank 1, so the rank test of "
        "Theorem thm:representation-independence (iv) may NOT be replaced by an extinction measurement "
        "above two input modes.",
    ),
)


O_RP_REPRESENTATION = RPOracleEntry(
    oracle_id="O-RP-REPRESENTATION",
    claims=("RC5",),
    kind="structural-identity",
    subject=(
        "The POVM depends on the instrument only through the Grams: two "
        "distinct matrices with identical Grams; a realizing instrument of a "
        "different shape; the rank-one criterion holding and failing; and the "
        "extinction criterion with its dimension caveat."
    ),
    derivation="""\
Theorem thm:representation-independence with Corollaries cor:phases and cor:extinction. Four
representation cases, three one-mode-per-port verdicts and three extinction
verdicts are frozen above with their derivations.

WHAT THE SET PINS.

(1) thm:representation-independence (i), the DETERMINATION, in the direction an implementation can
violate: REP-BB84-PORT-PHASE freezes two different instrument matrices with
matrix-for-matrix identical Gram families. An implementation that carried the
instrument matrix into any emitted quantity other than the Grams would
distinguish them, and the contract's emitted object is the Gram family
(Section 2.2 `port_grams`), with NO output key carrying Gamma.

(2) thm:representation-independence (ii), REALIZABILITY, on a family with a rank-two port:
REP-REALIZE-RANK2 freezes the A_k^{1/2} construction, of a different shape and
with a different port map from the instrument it reproduces.

(3) thm:representation-independence (iv), the ONE-MODE-PER-PORT criterion, HOLDING and FAILING, with
the row uniqueness in the case where it holds and the phase identified as the
retarder phase. Remark rem:rankone: it is a CERTIFIED branch, never a default.

(4) cor:phases WITH ITS HYPOTHESIS, and the half of Remark rem:bsconv that goes
beyond it. REP-BSCONV-OUTPUT-PHASE is the covered half and the Grams agree;
REP-BSCONV-SYMMETRIC is the uncovered half and they do not. That pair is the
evidence for change request CR-3 and is frozen as a computation, not as an
opinion.

(5) cor:extinction AND ITS DIMENSION CAVEAT. The caveat is frozen because it is
the kind of statement a reader takes one clause too far: at three or more input
modes, one extinguished direction bounds the rank by |Inp| - 1 and NOT by one.
""",
)


# ===========================================================================
#  Group RP-F -- the click-pattern POVM (RC6)
# ===========================================================================
#
#  Blocks are frozen for the SIX COARSE ELEMENTS of Theorem thm:click-povm (iv) --
#  no-click, the K single-click elements, and the multiclick aggregate -- which
#  is exactly what Section 2.2 `photon_blocks` emits after the coarse-graining
#  of Definition def:coarse. At K = 2 the multiclick aggregate IS the single
#  raw pattern {1, 2}, so the raw and coarse pictures coincide there.
#
#  `elements` holds the no-click and single-click blocks; `multiclick` holds
#  their complement in the identity. Completeness is then
#  sum(elements) + multiclick = 1 on the block, which is Theorem thm:click-povm (i)
#  restricted to a photon-number sector, and the integrity test checks it.

POVM_BLOCK_CASES: tuple[POVMBlockCase, ...] = (
    # --- the two-detector beamsplitter receiver, one input mode ------------
    POVMBlockCase(
        case_id="PB-BS-n0",
        instrument_case_id="I-BS",
        photon_number=0,
        basis_order=((0,),),
        elements=(
            ((), mat_real(((1,),))),
            (("1",), mat_real(((0,),))),
            (("2",), mat_real(((0,),))),
        ),
        multiclick=mat_real(((0,),)),
        multiclick_spectrum=(F(0),),
        beta_at_n=F(0),
        derives_from=(
            "Theorem thm:click-povm (iii): blk M^{(=0)}_S = delta_{S, empty} -- NO "
            "PHOTON, NO CLICK. Eq. eq:Mnc at n = 0 is Fock(1 - A_Sigma)^{(0)} "
            "= 1 and every other element vanishes, by the binomial identity "
            "sum over T of (-1)^{|T|} = (1 - 1)^{|S|}. The bound agrees "
            "exactly: beta(0) = 1 + (K-1) gamma - sum_k beta_k = 1 + 1 - 2 = 0 "
            "with gamma = beta_k = 1 and the convention 0^0 = 1."
        ),
    ),
    POVMBlockCase(
        case_id="PB-BS-n1",
        instrument_case_id="I-BS",
        photon_number=1,
        basis_order=((1,),),
        elements=(
            ((), mat_real(((0,),))),
            (("1",), mat_real(((F(1, 2),),))),
            (("2",), mat_real(((F(1, 2),),))),
        ),
        multiclick=mat_real(((0,),)),
        multiclick_spectrum=(F(0),),
        beta_at_n=F(0),
        derives_from=(
            "A_1 = A_2 = 1/2 and A_Sigma = 1 on the one-dimensional input "
            "space, so Fock(1 - A_J)^{(n)} = (1 - A_J)^n. Eq. eq:Mnc: "
            "M_empty = (1 - 1)^1 = 0. Eq. eq:Msc: M_{1} = "
            "Fock(1 - A_2)^{(1)} - Fock(1 - A_Sigma)^{(1)} = 1/2 - 0 = 1/2, "
            "and likewise M_{2}. Eq. eq:Mmc: M_mc = 1 + (K-1) times 0 - "
            "(1/2 + 1/2) = 0 -- ONE PHOTON CANNOT MAKE TWO DETECTORS CLICK, "
            "and the formula says so without being told. Completeness: "
            "0 + 1/2 + 1/2 + 0 = 1. The bound: c = 1 - lmax(A_Sigma) = 0 and "
            "d_k = 1 - lmin(A_{[2] minus {k}}) = 1/2, so "
            "beta(1) = 1 + 0 - 2(1/2) = 0, EQUAL to lmin here because the "
            "block is one-dimensional."
        ),
    ),
    POVMBlockCase(
        case_id="PB-BS-n2",
        instrument_case_id="I-BS",
        photon_number=2,
        basis_order=((2,),),
        elements=(
            ((), mat_real(((0,),))),
            (("1",), mat_real(((F(1, 4),),))),
            (("2",), mat_real(((F(1, 4),),))),
        ),
        multiclick=mat_real(((F(1, 2),),)),
        multiclick_spectrum=(F(1, 2),),
        beta_at_n=F(1, 2),
        derives_from=(
            "Same closed forms at n = 2: M_empty = 0^2 = 0; "
            "M_{k} = (1/2)^2 - 0 = 1/4; M_mc = 1 + 0 - 2(1/4) = 1/2. "
            "Completeness 0 + 1/4 + 1/4 + 1/2 = 1. THE BOUND IS EXACT HERE: "
            "beta(2) = 1 - 2(1/2)^2 = 1/2 = lmin(M_mc^{(2)}), because the "
            "block is one-dimensional and Lemma lem:fock-block-spectrum's inequality "
            "Eq. eq:blockopbounds is an equality on a one-dimensional space. "
            "Remark rem:notsharp's warning that 'beta(n) bounds three operators "
            "separately and is therefore not tight' is about the general case; "
            "the BB84 blocks of PB-BB84-n2 are where the slack is visible."
        ),
    ),
    # --- the polarizing BB84 receiver, two input modes, K = 4 --------------
    POVMBlockCase(
        case_id="PB-BB84-n0",
        instrument_case_id="I-BB84",
        photon_number=0,
        basis_order=((0, 0),),
        elements=(
            ((), mat_real(((1,),))),
            (("H",), mat_real(((0,),))),
            (("V",), mat_real(((0,),))),
            (("+",), mat_real(((0,),))),
            (("-",), mat_real(((0,),))),
        ),
        multiclick=mat_real(((0,),)),
        multiclick_spectrum=(F(0),),
        beta_at_n=F(0),
        derives_from=(
            "Theorem thm:click-povm (iii) again: no photon, no click. beta(0) = "
            "1 + 3 - 4 = 0 at gamma = beta_k = 1, agreeing exactly."
        ),
    ),
    POVMBlockCase(
        case_id="PB-BB84-n1",
        instrument_case_id="I-BB84",
        photon_number=1,
        basis_order=((0, 1), (1, 0)),
        elements=(
            ((), mat_real(((0, 0), (0, 0)))),
            (("H",), mat_real(((0, 0), (0, F(1, 2))))),
            (("V",), mat_real(((F(1, 2), 0), (0, 0)))),
            (("+",), mat_real(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4))))),
            (("-",), mat_real(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4))))),
        ),
        multiclick=mat_real(((0, 0), (0, 0))),
        multiclick_spectrum=(F(0), F(0)),
        beta_at_n=F(-1),
        derives_from=(
            "Eq. eq:blockMS at n = 1, in the occupation order [(0,1), (1,0)], "
            "which REVERSES the mode basis (H, V). A_Sigma = 1 gives "
            "M_empty = 0. For the single-click blocks, Eq. eq:Msc reduces to "
            "Fock(1 - A_{[K] minus {k}})^{(1)} because the second term "
            "vanishes; and "
            "A_{[K] minus {H}} = A_V + A_+ + A_- = (1/2) diag(0, 1) + (1/2) 1 "
            "= diag(1/2, 1), so 1 - it = diag(1/2, 0) in the MODE basis and "
            "diag(0, 1/2) in the occupation order. Symmetrically for V. For + "
            "and -: A_{[K] minus {+}} = [[3/4, -1/4], [-1/4, 3/4]] and "
            "1 - it = (1/2)|+><+| = [[1/4, 1/4], [1/4, 1/4]], which the "
            "reversal leaves fixed; and the - case likewise. THE FOUR SUM TO "
            "diag(1/2, 1/2) + diag(1/2, 1/2) = 1, so M_mc^{(1)} = 1 - 1 = 0: "
            "one photon, four ports, NO multiclick. The bound at n = 1 is "
            "beta(1) = 1 + 3 times 0 - 4(1/2) = -1, valid and far from tight "
            "-- which is correct, and is why Definition def:pmc takes the "
            "positive part."
        ),
    ),
    POVMBlockCase(
        case_id="PB-BB84-n2",
        instrument_case_id="I-BB84",
        photon_number=2,
        basis_order=((0, 2), (1, 1), (2, 0)),
        elements=(
            ((), mat_real(((0, 0, 0), (0, 0, 0), (0, 0, 0)))),
            (("H",), mat_real(((0, 0, 0), (0, 0, 0), (0, 0, F(1, 4))))),
            (("V",), mat_real(((F(1, 4), 0, 0), (0, 0, 0), (0, 0, 0)))),
            (
                ("+",),
                (
                    (rt(F(1, 16)), rt(0, F(1, 16)), rt(F(1, 16))),
                    (rt(0, F(1, 16)), rt(F(1, 8)), rt(0, F(1, 16))),
                    (rt(F(1, 16)), rt(0, F(1, 16)), rt(F(1, 16))),
                ),
            ),
            (
                ("-",),
                (
                    (rt(F(1, 16)), rt(0, F(-1, 16)), rt(F(1, 16))),
                    (rt(0, F(-1, 16)), rt(F(1, 8)), rt(0, F(-1, 16))),
                    (rt(F(1, 16)), rt(0, F(-1, 16)), rt(F(1, 16))),
                ),
            ),
        ),
        multiclick=mat_real(
            (
                (F(5, 8), 0, F(-1, 8)),
                (0, F(3, 4), 0),
                (F(-1, 8), 0, F(5, 8)),
            )
        ),
        multiclick_spectrum=(F(1, 2), F(3, 4), F(3, 4)),
        beta_at_n=F(0),
        derives_from=(
            "Eq. eq:blockMS at n = 2, using the two-photon formula derived "
            "above the FOCK_CASES tuple with the operators Y_k = "
            "1 - A_{[K] minus {k}} in the MODE basis (H, V):\n"
            "  Y_H = diag(1/2, 0) -> [[0,0,0],[0,0,0],[0,0,1/4]];\n"
            "  Y_V = diag(0, 1/2) -> [[1/4,0,0],[0,0,0],[0,0,0]];\n"
            "  Y_+ = [[1/4,1/4],[1/4,1/4]] -> all nine entries non-zero, with "
            "d^2 = c^2 = b^2 = a^2 = 1/16, a d + b c = 1/8 and the four sqrt2 "
            "entries equal to sqrt2/16;\n"
            "  Y_- = [[1/4,-1/4],[-1/4,1/4]] -> the same with the four sqrt2 "
            "entries NEGATED, since b = c = -1/4.\n"
            "M_empty = 0 because A_Sigma = 1. Their sum is "
            "[[3/8, 0, 1/8], [0, 1/4, 0], [1/8, 0, 3/8]] -- THE sqrt2 ENTRIES "
            "CANCEL BETWEEN + AND -, which is why the multiclick block is "
            "rational although two of its summands are not -- and Eq. eq:Mmc "
            "gives M_mc^{(2)} = 1 - that sum = "
            "[[5/8, 0, -1/8], [0, 3/4, 0], [-1/8, 0, 5/8]]. ITS SPECTRUM: the "
            "(1,1) entry 3/4 is an eigenvalue on |1,1>, and the 2x2 block "
            "[[5/8, -1/8], [-1/8, 5/8]] on span{|0,2>, |2,0>} has eigenvalues "
            "5/8 -+ 1/8 = 3/4 and 1/2. So lmin(M_mc^{(2)}) = 1/2. THE BOUND AT "
            "THIS BLOCK IS beta(2) = 1 - 4(1/2)^2 = 0, STRICTLY BELOW 1/2: "
            "this is Remark rem:notsharp's slack, exhibited. Version 1 emits "
            "the analytic bound because it is uniform in n and an exact "
            "per-block computation is not."
        ),
    ),
    # --- the singular receiver, for thm:coarse-graining (iii) -------------------------
    POVMBlockCase(
        case_id="PB-SINGULAR-n2",
        instrument_case_id="I-SINGULAR",
        photon_number=2,
        basis_order=((0, 2), (1, 1), (2, 0)),
        elements=(
            ((), mat_real(((1, 0, 0), (0, 0, 0), (0, 0, 0)))),
            (
                ("1",),
                mat_real(((0, 0, 0), (0, F(1, 2), 0), (0, 0, F(1, 4)))),
            ),
            (
                ("2",),
                mat_real(((0, 0, 0), (0, F(1, 2), 0), (0, 0, F(1, 4)))),
            ),
        ),
        multiclick=mat_real(((0, 0, 0), (0, 0, 0), (0, 0, F(1, 2)))),
        multiclick_spectrum=(F(0), F(0), F(1, 2)),
        beta_at_n=F(-1),
        derives_from=(
            "I-SINGULAR has A_1 = A_2 = (1/2) diag(1, 0), so A_Sigma = "
            "diag(1, 0) and 1 - A_Sigma = diag(0, 1) in the mode basis. The "
            "two-photon formula at a = 0, d = 1 gives Fock(1 - A_Sigma)^{(2)} = "
            "diag(1, 0, 0): the no-click element has EIGENVALUE ONE at the "
            "occupation vector (0, 2), both photons in the direction no port "
            "sees. That is Lemma lem:fock-block-spectrum's "
            "lmax(M_empty^{(n)}) = (1 - lmin(A_Sigma))^n = 1. Then "
            "1 - A_{[2] minus {1}} = 1 - A_2 = diag(1/2, 1) gives "
            "Fock^{(2)} = diag(1, 1/2, 1/4) and "
            "M_{1}^{(2)} = diag(1, 1/2, 1/4) - diag(1, 0, 0) = "
            "diag(0, 1/2, 1/4), symmetrically for port 2, and Eq. eq:Mmc gives "
            "M_mc^{(2)} = 1 + diag(1,0,0) - 2 diag(1, 1/2, 1/4) = "
            "diag(0, 0, 1/2). Completeness: diag(1,0,0) + 2 diag(0,1/2,1/4) + "
            "diag(0,0,1/2) = 1. lmin(M_mc^{(2)}) = 0 EXACTLY, and the bound "
            "beta(2) = 1 + 0^2 - 2 = -1 is valid and returns zero after the "
            "positive part -- correctly, because a receiver with an input "
            "direction no port sees can guarantee NO multiclick weight at any "
            "photon number."
        ),
    ),
)

#: Eq. eq:recoverpivac and Theorem thm:click-povm (i): the joint no-click element of a
#: port set J is the sum of the elements whose click set AVOIDS J. Frozen as
#: (case id, block case, J, Pi_vac(J) on that block, the patterns that sum to
#: it). The integrity test performs the sum on the frozen blocks.
INCLUSION_EXCLUSION_CASES: tuple[
    tuple[str, str, tuple[str, ...], Mat, tuple[tuple[str, ...], ...]], ...
] = (
    (
        "IE-BS-J1-n2",
        "PB-BS-n2",
        ("1",),
        mat_real(((F(1, 4),),)),
        ((), ("2",)),
    ),
    (
        "IE-BS-J12-n2",
        "PB-BS-n2",
        ("1", "2"),
        mat_real(((0,),)),
        ((),),
    ),
    (
        "IE-BB84-JH-n1",
        "PB-BB84-n1",
        ("H",),
        mat_real(((1, 0), (0, F(1, 2)))),
        ((), ("V",), ("+",), ("-",)),
    ),
)


O_RP_POVM = RPOracleEntry(
    oracle_id="O-RP-POVM",
    claims=("RC6",),
    kind="toy-instance",
    subject=(
        "The click-pattern POVM blocks for n = 0, 1, 2 of two receivers: "
        "positivity and completeness per block, block-diagonality in total "
        "photon number, the explicit n-photon block, its spectrum, and the "
        "inclusion-exclusion identities."
    ),
    derivation="""\
Theorem thm:click-povm with Eqs. eq:MSdef, eq:incexc, eq:blockMS, eq:Mnc, eq:Msc and
eq:Mmc. Seven blocks and three inclusion-exclusion identities are frozen above,
each with its derivation.

THE TWO RECEIVERS ARE CHOSEN TO SEPARATE TWO THINGS.

I-BS has ONE declared input mode, so binom(1 + n - 1, n) = 1 and every block is
one-dimensional. There the bound of Theorem thm:multiclick-bound and the smallest
eigenvalue of the multiclick element COINCIDE at every n, because
Eq. eq:blockopbounds is an equality on a one-dimensional space. That is the
control case.

I-BB84 has TWO declared input modes and K = 4, so the blocks are of dimensions
1, 2, 3 and the bound is strictly loose at n = 2: lmin = 1/2 against
beta(2) = 0. That is Remark rem:notsharp exhibited, and it is the reason an
implementation must emit beta and not a per-block eigenvalue as the slot value
(Section 2.2 `high_photon_bounds`).

WHAT EVERY BLOCK PINS.

(a) POSITIVITY, which Remark rem:positivity insists does NOT come from the
alternating sum: "Formula eq:incexc is an alternating sum of positive operators
and NOTHING ABOUT ITS FORM MAKES IT POSITIVE; at K = 4 it has eight terms with
four minus signs." Positivity comes from the physical construction of
Definition def:physmodel -- commuting binary projective measurements on disjoint
output mode sets, pulled back through an isometry. Every frozen block is
positive semidefinite and the integrity test checks it; the frozen M_mc at
PB-BB84-n2 has FOUR NEGATIVE-COEFFICIENT SUMMANDS and is still positive
semidefinite, with spectrum {1/2, 3/4, 3/4}.

(b) COMPLETENESS, blockwise: the six coarse elements sum to the identity on
every frozen block. That is residual r_4 of Definition def:residuals set to
zero, and Group RP-I freezes it as such.

(c) BLOCK-DIAGONALITY IN TOTAL PHOTON NUMBER. Every frozen object is ONE block;
none relates two, because Theorem thm:click-povm (iii) says the elements are direct
sums over n and nothing in the contract couples the summands. Remark
rem:blockmeaning adds the caveat that with a probe declared the TOTAL-input
grading is not the CHANNEL grading -- and both receivers here declare none, so
the two coincide, which is what the remark says.

(d) blk M^{(=0)}_S = delta_{S, empty} at n = 0, on both receivers: NO PHOTON, NO
CLICK, from the binomial identity in the proof of thm:click-povm (iii).

(e) THE INCLUSION-EXCLUSION IDENTITIES, in the direction Theorem thm:representation-independence (i)
uses to invert the construction: Pi_vac(J) = sum over S avoiding J of M_S
(Eq. eq:recoverpivac). Three are frozen, and IE-BB84-JH-n1 is the substantive
one -- the sum over the fifteen patterns avoiding H reduces, at n = 1, to the
four whose blocks are non-zero, and equals Fock(1 - A_H)^{(1)} = diag(1, 1/2) in
the occupation order. An implementation that had the occupation order reversed
would get diag(1/2, 1) and fail here.

WHAT IS NOT FROZEN. The RAW blocks M_S for |S| >= 2 individually, at K = 4: the
contract's emitted object is the COARSE-GRAINED family (Section 2.2
`photon_blocks`, Definition def:coarse) and the slot value is the multiclick
AGGREGATE (Definition def:slot), and Theorem thm:coarse-graining (iii) proves that a bound
on the aggregate says nothing about its fibres -- so freezing eleven individual
raw blocks would pin objects no emitted key carries. At K = 2 the aggregate IS
the single raw pattern, and PB-BS freezes it as such.
""",
)


# ===========================================================================
#  Group RP-G -- declared coarse-graining (RC7)
# ===========================================================================

_MC4: tuple[tuple[str, ...], ...] = (
    ("H", "V"),
    ("H", "+"),
    ("H", "-"),
    ("V", "+"),
    ("V", "-"),
    ("+", "-"),
    ("H", "V", "+"),
    ("H", "V", "-"),
    ("H", "+", "-"),
    ("V", "+", "-"),
    ("H", "V", "+", "-"),
)

COARSE_GRAINING_CASES: tuple[CoarseGrainingCase, ...] = (
    CoarseGrainingCase(
        case_id="CG-SIX",
        port_labels=("H", "V", "+", "-"),
        alphabet=OUTCOME_ALPHABET,
        fibres=(
            ("nc", ((),)),
            ("sc_H", (("H",),)),
            ("sc_V", (("V",),)),
            ("sc_+", (("+",),)),
            ("sc_-", (("-",),)),
            ("mc", _MC4),
        ),
        surjective=True,
        derives_from=(
            "Remark req:declared-alphabet's own instance, and the contract is "
            "explicit that it is ONE INSTANCE AMONG MANY and not the "
            "definition: at K = 4, cg(empty) = nc, cg({k}) = sc_k, and "
            "cg(S) = mc for every S in MC_4. The fibres PARTITION 2^[4]: "
            "1 + 4 + 11 = 16, which is what makes sum_v F_v = sum_S M_S = 1 in "
            "the proof of Theorem thm:coarse-graining (i). The map is surjective onto the "
            "six-letter alphabet, as Definition def:coarse requires. 'A module "
            "that fixed six outcomes over four detectors internally would make "
            "the outcome alphabet AN IMPLEMENTATION DETAIL OF THE RECEIVER "
            "rather than a declared property of the protocol.'"
        ),
    ),
    CoarseGrainingCase(
        case_id="CG-THREE",
        port_labels=("H", "V", "+", "-"),
        alphabet=((0, "nc"), (1, "click_Z"), (2, "other")),
        fibres=(
            ("nc", ((),)),
            ("click_Z", (("H",), ("V",))),
            ("other", (("+",), ("-",), *_MC4)),
        ),
        surjective=True,
        derives_from=(
            "A SECOND declared coarse-graining ON THE SAME RECEIVER, frozen so "
            "that the alphabet is visibly DATA and not a property of the "
            "optics. Same port map, same Grams, same blocks; a different "
            "declared surjection, a different emitted alphabet, and by Theorem "
            "thm:coarse-graining (i) a POVM either way. The fibres again partition 2^[4]: "
            "1 + 2 + 13 = 16."
        ),
    ),
    CoarseGrainingCase(
        case_id="CG-CONSTANT",
        port_labels=("1", "2"),
        alphabet=((0, "v"),),
        fibres=(("v", ((), ("1",), ("2",), ("1", "2"))),),
        surjective=True,
        derives_from=(
            "THE COUNTEREXAMPLE OF THEOREM thm:coarse-graining (iii), which needs a "
            "CONSTANT cg on K = 2, applied to I-SINGULAR. Then F_v = "
            "sum_S M_S = 1 and the bound F_v >= 1 times 1 is available and "
            "TRUE -- and it says NOTHING about the fibres: PB-SINGULAR-n2 "
            "freezes lmin(M_{1,2}^{(2)}) = 0. 'Coarsening is lossy in ONE "
            "DIRECTION ONLY', which is why Definition def:slot indexes the "
            "strengthening slot by OUTCOME SETS and not by emitted letters."
        ),
    ),
)

#: Theorem thm:coarse-graining (ii): per-outcome-set lower bounds ADD under coarse-graining.
#: Frozen as (case id, block case, the outcome set, its bound, the letter whose
#: fibre contains it, the resulting bound on that letter).
_AdditivityRow = tuple[str, str, tuple[tuple[str, ...], ...], F, str, F]
ADDITIVITY_CASES: tuple[_AdditivityRow, ...] = (
    (
        "ADD-BB84-MC",
        "PB-BB84-n2",
        _MC4,
        F(0),
        "mc",
        F(0),
    ),
    (
        "ADD-BS-MC",
        "PB-BS-n2",
        (("1", "2"),),
        F(1, 2),
        "mc",
        F(1, 2),
    ),
)


O_RP_COARSE = RPOracleEntry(
    oracle_id="O-RP-COARSE",
    claims=("RC7",),
    kind="structural-identity",
    subject=(
        "A declared surjective coarse-graining onto an emitted alphabet, a "
        "second one on the same receiver, the coarse blocks, the additivity of "
        "per-outcome-set lower bounds, and the one-directional losslessness."
    ),
    derivation="""\
Definition def:coarse and Theorem thm:coarse-graining. Three coarse-grainings and two
additivity cases are frozen above.

(i) THE POVM AND ITS BLOCK STRUCTURE. thm:coarse-graining (i): the fibres of a MAP partition
the raw alphabet, so sum_v F_v = sum_S M_S = 1 and block-diagonality is
inherited summand by summand. Every frozen case records its fibres explicitly
and the integrity test checks that they partition 2^[K] -- which is the whole
content of "cg is a total map onto V" and is the one hypothesis the proof uses.

(ii) BOUNDS ADD. thm:coarse-graining (ii) is a Loewner-order statement about a sum, and at
the version-1 slot it is applied with a SINGLE outcome set: O = MC_K, p = p_mc,
and cg^{-1}(mc) = MC_K exactly, so the emitted bound on the letter `mc` is
p_mc itself. ADD-BB84-MC and ADD-BS-MC freeze that at the two receivers of Group
RP-F. THE SECOND SENTENCE OF thm:coarse-graining (ii) IS THE ONE THAT MATTERS FOR A
COARSE-GRAINING THAT IS NOT EXACTLY MC_K: if cg^{-1}(v) STRICTLY CONTAINS O, the
bound still holds, because "the remaining, positive, elements of the fibre" are
added. So a declaration whose `mc` letter also absorbs some single-click pattern
inherits the same p_mc, never less.

(iii) LOSSY IN ONE DIRECTION ONLY. CG-CONSTANT with I-SINGULAR is the contract's
own counterexample, and the numbers are frozen in PB-SINGULAR-n2: the coarse
element is the identity with the perfect bound 1, and one of its fibres has
smallest eigenvalue 0 on the same block. That is why Definition def:slot indexes
the slot by outcome SETS.

(iv) THE ALPHABET IS DECLARED. CG-SIX and CG-THREE are two declared surjections
on ONE receiver with one port map and one Gram family. Nothing in the frozen
optics changes between them, which is Remark req:declared-alphabet's point.

WHAT IS NOT DECIDED HERE. The ID assignment and the emitted order of V are open
implementation choice OIC-1 in interface.yaml; the IDs in OUTCOME_ALPHABET are
this fixture's, and the integrity test asserts only that they are STABLE (a
bijection onto a set of integers) and that the labels are metadata -- never that
a particular integer belongs to a particular letter of the contract.
""",
)


# ===========================================================================
#  Group RP-H -- the uniform high-photon multiclick bound (RC8)
# ===========================================================================
#
#  beta(n) = 1 + (K-1) gamma c^n - sum_k beta_k d_k^n  (Eq. eq:beta), with the
#  convention 0^0 = 1 that Definition def:bounddata states. Every value below is
#  that expression evaluated exactly at rational admissible bound data.
#
#  THE FROZEN SET COVERS, DELIBERATELY: p_mc ZERO and p_mc POSITIVE at the same
#  receiver at different cutoffs; branch 1 by predicate (X)'s FIRST clause (no
#  probe modes) and by its SECOND (vacuum probe); branch 2 with its window, its
#  tail and its residual gap at a probe-on setting; the residual gap at the
#  minimal window m = N + 1, where Lemma lem:windowtail (ii) gives it in closed
#  form as (K-1) gamma c^{N+1}; the collapse step failing at n = 0 (Remark
#  rem:n0); the sharpness case (Remark rem:collapsesharp); the contract's own
#  collapse-hypothesis failure (Remark rem:collapse-fails); and the c = 1
#  counterexample to the limit clause of Lemma lem:windowtail (iv).

BOUND_DATA_CASES: tuple[BoundDataCase, ...] = (
    BoundDataCase(
        case_id="BD-BB84-N2",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        beta_values=(
            (0, F(0)),
            (1, F(-1)),
            (2, F(0)),
            (3, F(1, 2)),
            (4, F(3, 4)),
        ),
        photon_cutoff=2,
        branch="1",
        predicate="X",
        window=None,
        window_minimum=None,
        tail=None,
        residual_gap=None,
        p_mc=F(1, 2),
        derives_from=(
            "EXAMPLE ex:bb84bound, VERBATIM, at p_Z = p_X = 1/2. The receiver "
            "is I-BB84, the channel-only receiver of the last paragraph of "
            "Example ex:bb84, which declares Inp_S EMPTY and therefore has "
            "T = {off} by Definition def:probe. So gamma = beta_k = 1, "
            "A_Sigma = 1 gives c = 1 - lmax(A_Sigma) = 0, and "
            "A_Sigma - A_H = 1 - p_Z |H><H| has lmin = 1 - p_Z = p_X, so "
            "d_H = 1 - p_X = p_Z, and likewise d_V = p_Z, d_+ = d_- = p_X. "
            "Eq. eq:bb84beta: beta(n) = 1 - 2 p_Z^n - 2 p_X^n = 1 - 2^{2-n} at "
            "p_Z = 1/2. Hence beta(1) = -1, beta(2) = 0, beta(3) = 1/2, "
            "beta(4) = 3/4 -- NON-DECREASING FROM THE FIRST NON-NEGATIVE "
            "INDEX, as Lemma lem:collapse requires. PREDICATE (X) HOLDS BY ITS "
            "FIRST CLAUSE (no probe modes declared), branch 1 is taken, and NO "
            "tail_window is declared or required (Remark rem:windowdecidable). "
            "Since T = {off}, the minimum over T is over that one setting, SO "
            "THE PRINTED 1/2 IS THE EMITTED p_mc AND NOT A PER-SETTING VALUE "
            "-- which is the closure of round-3 finding F-3-01. At N = 2, "
            "p_mc = max{0, beta(3)} = 1/2."
        ),
    ),
    BoundDataCase(
        case_id="BD-BB84-N3",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        beta_values=((3, F(1, 2)), (4, F(3, 4))),
        photon_cutoff=3,
        branch="1",
        predicate="X",
        window=None,
        window_minimum=None,
        tail=None,
        residual_gap=None,
        p_mc=F(3, 4),
        derives_from=(
            "The same receiver at N = 3: p_mc = max{0, beta(4)} = 3/4, the "
            "second worked cutoff of Example ex:bb84bound. 'Note that p_mc -> 1 "
            "exponentially exactly when max(p_Z, p_X) < 1, i.e. when no single "
            "basis absorbs the whole input.'"
        ),
    ),
    BoundDataCase(
        case_id="BD-BB84-N1-ZERO",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        beta_values=((1, F(-1)), (2, F(0))),
        photon_cutoff=1,
        branch="1",
        predicate="X",
        window=None,
        window_minimum=None,
        tail=None,
        residual_gap=None,
        p_mc=F(0),
        derives_from=(
            "THE SAME RECEIVER AT A LOWER CUTOFF, WHERE p_mc IS EXACTLY ZERO. "
            "At N = 1 the first index above the cutoff is n = 2 and "
            "beta(2) = 1 - 2^{2-2} = 0, so p_mc = max{0, 0} = 0. The bound is "
            "VALID and USELESS, and Definition def:pmc's positive part is what "
            "makes it valid rather than negative. Proposition prop:slotvalid "
            "then still holds -- p_mc = 0 in [0, 1] -- so the "
            "ARCHITECTURE_SPEC.md Section 7.3 failure conditions are not "
            "triggered. FROZEN BECAUSE AN IMPLEMENTATION THAT SILENTLY RAISED "
            "A ZERO BOUND TO SOMETHING POSITIVE WOULD BE UNSAFE AND WOULD LOOK "
            "LIKE AN IMPROVEMENT."
        ),
    ),
    BoundDataCase(
        case_id="BD-BB84-PZ-QUARTER-N2",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 4), F(1, 4), F(3, 4), F(3, 4)),
        beta_values=((2, F(-1, 4)), (3, F(1, 8))),
        photon_cutoff=2,
        branch="1",
        predicate="X",
        window=None,
        window_minimum=None,
        tail=None,
        residual_gap=None,
        p_mc=F(1, 8),
        derives_from=(
            "THE SAME RECEIVER AT AN UNBALANCED BASIS CHOICE, p_Z = 1/4 and "
            "p_X = 3/4, so that d_H = d_V = 1/4 and d_+ = d_- = 3/4 by the "
            "same computation as BD-BB84-N2. Eq. eq:bb84beta: "
            "beta(n) = 1 - 2(1/4)^n - 2(3/4)^n. At n = 2: "
            "1 - 2/16 - 18/16 = -1/4, NEGATIVE. At n = 3: "
            "1 - 2/64 - 54/64 = 8/64 = 1/8, POSITIVE. So at N = 2 the emitted "
            "p_mc is 1/8 -- a POSITIVE bound at a receiver whose balanced "
            "version gives 1/2 at the same cutoff. The asymmetry costs bound, "
            "exactly as the closing sentence of Example ex:bb84bound predicts: "
            "the convergence is governed by max(p_Z, p_X)."
        ),
    ),
    BoundDataCase(
        case_id="BD-BS-N1",
        port_count=2,
        gamma=F(1),
        betas=(F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2)),
        beta_values=((0, F(0)), (1, F(0)), (2, F(1, 2)), (3, F(3, 4))),
        photon_cutoff=1,
        branch="1",
        predicate="X",
        window=None,
        window_minimum=None,
        tail=None,
        residual_gap=None,
        p_mc=F(1, 2),
        derives_from=(
            "I-BS, the two-detector 50:50 receiver with ONE declared input "
            "mode and no probe. c = 1 - lmax(A_Sigma) = 1 - 1 = 0 and "
            "d_k = 1 - lmin(A_{[2] minus {k}}) = 1 - 1/2 = 1/2, so "
            "beta(n) = 1 + 0^n - 2(1/2)^n = 1 - 2^{1-n} for n >= 1, and "
            "beta(0) = 1 + 1 - 2 = 0. At N = 1, p_mc = max{0, beta(2)} = 1/2. "
            "HERE THE BOUND IS THE EIGENVALUE: PB-BS-n2 freezes "
            "lmin(M_mc^{(2)}) = 1/2 exactly, because the blocks are "
            "one-dimensional."
        ),
    ),
    BoundDataCase(
        case_id="BD-SINGULAR-N1",
        port_count=2,
        gamma=F(1),
        betas=(F(1), F(1)),
        c=F(0),
        ds=(F(1), F(1)),
        beta_values=((0, F(0)), (1, F(-1)), (2, F(-1))),
        photon_cutoff=1,
        branch="1",
        predicate="X",
        window=None,
        window_minimum=None,
        tail=None,
        residual_gap=None,
        p_mc=F(0),
        derives_from=(
            "I-SINGULAR: A_1 = A_2 = (1/2) diag(1, 0), so A_Sigma = diag(1, 0) "
            "with lmax = 1 and c = 0, while A_{[2] minus {k}} = (1/2) diag(1, 0) "
            "has lmin = 0 and d_k = 1. beta(n) = 1 + 0^n - 2 is 0 at n = 0 and "
            "-1 at every n >= 1, so p_mc = 0 at every cutoff. CORRECTLY: the "
            "receiver has an input direction no port sees, PB-SINGULAR-n2 "
            "freezes lmin(M_mc^{(2)}) = 0, and no multiclick weight can be "
            "guaranteed at any photon number."
        ),
    ),
    BoundDataCase(
        case_id="BD-REM-N0",
        port_count=2,
        gamma=F(1),
        betas=(F(1), F(1)),
        c=F(1, 2),
        ds=(F(1), F(1)),
        beta_values=((0, F(0)), (1, F(-1, 2)), (2, F(-3, 4))),
        photon_cutoff=0,
        branch="1",
        predicate="X",
        window=None,
        window_minimum=None,
        tail=None,
        residual_gap=None,
        p_mc=F(0),
        derives_from=(
            "REMARK rem:n0's DATA, realized by I-REM-N0 at a = 1/2. "
            "gamma = beta_k = 1 and d_k = 1 with c = 1/2 < 1 give "
            "beta(n) = 1 + (1/2)^n - 2, so beta(0) = 0 >= 0 while "
            "beta(1) = -1/2 < 0: THE COLLAPSE STEP Eq. eq:collapsestep GENUINELY "
            "FAILS AT n = 0, and the remark says why -- 'the substitution "
            "u_k = beta_k d_k^n DEGENERATES AT n = 0, which is precisely where "
            "the proof breaks'. NOTHING IS LOST, because the infimum of "
            "Eq. eq:collapseinf runs over n > N >= 0 and the induction never "
            "starts below n = 1. Frozen so that an implementation cannot "
            "'improve' Lemma lem:collapse by starting the induction at zero. "
            "beta is DECREASING here, so p_mc = max{0, beta(1)} = 0 at N = 0."
        ),
    ),
    BoundDataCase(
        case_id="BD-COLLAPSE-SHARP",
        port_count=2,
        gamma=F(1),
        betas=(F(1), F(1)),
        c=F(1, 2),
        ds=(F(1), F(1, 2)),
        beta_values=((0, F(0)), (1, F(0)), (2, F(0)), (3, F(0))),
        photon_cutoff=1,
        branch="1",
        predicate="X",
        window=None,
        window_minimum=None,
        tail=None,
        residual_gap=None,
        p_mc=F(0),
        derives_from=(
            "REMARK rem:collapsesharp: 'Equality holds in Eq. eq:target at the "
            "data gamma = beta_k = 1, d_1 = 1, d_2 = ... = d_K = c.' At K = 2 "
            "and c = 1/2 that is d = (1, 1/2), and "
            "beta(n) = 1 + (1/2)^n - 1 - (1/2)^n = 0 IDENTICALLY. So beta is "
            "CONSTANT and 'the implication Eq. eq:collapsestep CANNOT BE "
            "STRENGTHENED TO STRICT INCREASE'. Physically: 'the receiver in "
            "which some input polarization reaches only port 1: no multiclick "
            "weight can be guaranteed at any photon number, AND THE BOUND "
            "CORRECTLY RETURNS 0.'"
        ),
    ),
    BoundDataCase(
        case_id="BD-PROBE-OFF-N1",
        port_count=2,
        gamma=F(1),
        betas=(F(1), F(1)),
        c=F(1, 2),
        ds=(F(3, 4), F(3, 4)),
        beta_values=(
            (0, F(0)),
            (1, F(0)),
            (2, F(1, 8)),
            (3, F(9, 32)),
            (4, F(55, 128)),
        ),
        photon_cutoff=1,
        branch="1",
        predicate="X",
        window=None,
        window_minimum=None,
        tail=None,
        residual_gap=None,
        p_mc=F(1, 8),
        derives_from=(
            "I-PROBE AT THE VACUUM SETTING, Gamma^(t) = 0, which is PREDICATE "
            "(X)'s SECOND CLAUSE. Theorem thm:gaussian-schur (iii) gives "
            "c(A, 0) = 1 and A^eff = A_ChanChan for every A, so "
            "gamma = beta_k = 1 EXACTLY and the conditioned Grams are the "
            "channel blocks: B = (A_Sigma)_ChanChan = 1/2 and "
            "B_k = (A_{[2] minus {k}})_ChanChan = 1/4. Hence "
            "c = 1 - 1/2 = 1/2 and d_k = 1 - 1/4 = 3/4, and "
            "beta(n) = 1 + (1/2)^n - 2(3/4)^n: beta(0) = 1 + 1 - 2 = 0 "
            "EXACTLY (so Eq. eq:collapsehyp holds with equality, which is what "
            "(X) certifies without arithmetic), beta(1) = 1 + 1/2 - 3/2 = 0, "
            "beta(2) = 1 + 1/4 - 9/8 = 1/8, beta(3) = 1 + 1/8 - 27/32 = 9/32, "
            "beta(4) = 1 + 1/16 - 81/64 ... = 55/128. NON-DECREASING from the "
            "first non-negative index. At N = 1, p_mc = max{0, beta(2)} = 1/8. "
            "THIS IS ALSO THE VACUUM-ELIMINATION CHECK: the same numbers arise "
            "from the unconditioned channel-only receiver with the Led column "
            "dropped, which is Theorem thm:gaussian-schur (iii) = Lemma "
            "lem:vacelim."
        ),
    ),
    BoundDataCase(
        case_id="BD-PROBE-ON-N1-M3",
        superseded_by="0.2.0",
        port_count=2,
        gamma=F(2, 3),
        betas=(F(4, 5), F(4, 5)),
        c=F(1, 2),
        ds=(F(4, 5), F(4, 5)),
        beta_values=(
            (0, F(1, 15)),
            (1, F(4, 75)),
            (2, F(107, 750)),
            (3, F(1981, 7500)),
        ),
        photon_cutoff=1,
        branch="2",
        predicate=None,
        window=3,
        window_minimum=F(107, 750),
        tail=F(113, 625),
        residual_gap=F(0),
        p_mc=F(107, 750),
        derives_from=(
            "I-PROBE AT THE THERMAL SETTING nbar = 1, the case Group RP-L "
            "derives in closed form. There gamma = 2/3, beta_1 = beta_2 = 4/5, "
            "B = 1/2 and B_1 = B_2 = 1/5, so Eq. eq:cd gives c = 1 - 1/2 = 1/2 "
            "and d_k = 1 - 1/5 = 4/5. Admissible bound data: "
            "0 <= 2/3 <= 4/5 <= 1 and 0 <= 1/2 <= 4/5 <= 1.\n"
            "beta(n) = 1 + (2/3)(1/2)^n - (8/5)(4/5)^n:\n"
            "  beta(0) = 1 + 2/3 - 8/5 = (15 + 10 - 24)/15 = 1/15;\n"
            "  beta(1) = 1 + 1/3 - 32/25 = (75 + 25 - 96)/75 = 4/75;\n"
            "  beta(2) = 1 + 1/6 - 128/125 = (750 + 125 - 768)/750 = 107/750;\n"
            "  beta(3) = 1 + 1/12 - 512/625 = (7500 + 625 - 6144)/7500 = "
            "1981/7500.\n"
            "beta(0) = 1/15 > 0, SO Eq. eq:collapsehyp FAILS: predicate (X) "
            "fails (probe modes are declared and Gamma^(t) is non-zero) and "
            "predicate (C) fails (its slack is -beta(0) = -1/15 < 0, and by "
            "change request CR-4 it could never have succeeded). BRANCH 2 IS "
            "TAKEN and a window is REQUIRED (Remark rem:windowdecidable: "
            "required exactly at the settings whose probe is on).\n"
            "At N = 1 and the declared window m = 3, Eq. eq:windowtail takes "
            "the minimum over N < n <= m, i.e. over {2, 3}: "
            "W = min{107/750, 1981/7500} = min{1070, 1981}/7500 = 107/750; and "
            "T_3 = 1 - sum_k beta_k d_k^3 = 1 - 2(4/5)(64/125) = "
            "1 - 512/625 = 113/625 = 1356/7500. Since W = 1070/7500 < T_3, "
            "the window minimum is the binding one: "
            "underline-beta = 107/750 and the residual gap "
            "g = max{0, W - T} = 0. p_mc = max{0, 107/750} = 107/750. "
            "Lemma lem:windowtail (i) is satisfied WITH EQUALITY here: "
            "inf over n > 1 of beta(n) is beta(2) = 107/750, since beta rises "
            "from n = 2 onwards to the limit 1."
        ),
    ),
    BoundDataCase(
        case_id="BD-PROBE-ON-N1-M2",
        port_count=2,
        gamma=F(2, 3),
        betas=(F(4, 5), F(4, 5)),
        c=F(1, 2),
        ds=(F(4, 5), F(4, 5)),
        beta_values=((2, F(107, 750)),),
        photon_cutoff=1,
        branch="2",
        predicate=None,
        window=2,
        window_minimum=F(107, 750),
        tail=F(-3, 125),
        residual_gap=F(1, 6),
        p_mc=F(0),
        derives_from=(
            "THE SAME SETTING AT THE MINIMAL WINDOW m = N + 1 = 2, which is "
            "where Lemma lem:windowtail (ii) gives the residual gap in CLOSED "
            "FORM. The window {n : 1 < n <= 2} is the single index 2, so "
            "W = beta(2) = 107/750; and T_2 = 1 - 2(4/5)(16/25) = "
            "1 - 128/125 = -3/125, NEGATIVE. So underline-beta = "
            "min{107/750, -3/125} = -3/125 and p_mc = max{0, -3/125} = 0: A "
            "WINDOW TOO SHORT COSTS THE WHOLE BOUND, and it costs it "
            "CONSERVATIVELY, never unsafely (Lemma lem:windowtail (i) holds "
            "for every m > N).\n"
            "THE GAP CHECKS THE CLOSED FORM: g_{1,2} = max{0, W - T} = "
            "107/750 + 3/125 = 107/750 + 18/750 = 125/750 = 1/6, and Lemma "
            "lem:windowtail (ii) says g_{N,N+1} = (K-1) gamma c^{N+1} = "
            "1 times (2/3) times (1/2)^2 = 1/6. THEY AGREE EXACTLY. Compared "
            "with BD-PROBE-ON-N1-M3, underline-beta rose from -3/125 to "
            "107/750 as m went from 2 to 3, which is the monotonicity of "
            "lem:windowtail (ii); the emitted g_{N,m} is what 'bounds what "
            "widening the window could still recover'."
        ),
    ),
    BoundDataCase(
        case_id="BD-COLLAPSE-FAILS-M4",
        port_count=4,
        gamma=F(1, 100),
        betas=(F(1, 100), F(1, 100), F(1, 100), F(1, 100)),
        c=F(1, 2),
        ds=(F(1), F(1), F(1), F(1)),
        beta_values=(
            (0, F(99, 100)),
            (3, F(771, 800)),
            (4, F(1539, 1600)),
        ),
        photon_cutoff=2,
        branch="2",
        predicate=None,
        window=4,
        window_minimum=F(1539, 1600),
        tail=F(24, 25),
        residual_gap=F(3, 1600),
        p_mc=F(24, 25),
        derives_from=(
            "REMARK rem:collapse-fails' OWN INSTANCE: 'K = 4, "
            "gamma = beta_k = 1/100 and d_k = 1 for every k give "
            "beta(n) = 96/100 + (3/100) c^n, which is positive and STRICTLY "
            "DECREASING in n, with infimum 96/100 approached only as "
            "n -> infinity'. Frozen at c = 1/2, N = 2, m = 4.\n"
            "beta(n) = 1 + 3(1/100)(1/2)^n - 4/100 = 96/100 + (3/100) 2^{-n}: "
            "beta(0) = 99/100, beta(3) = 96/100 + 3/800 = 771/800, "
            "beta(4) = 96/100 + 3/1600 = 1539/1600.\n"
            "beta(0) = 99/100 > 0 so Eq. eq:collapsehyp FAILS and branch 2 is "
            "taken. The window {3, 4} gives W = min{1542, 1539}/1600 = "
            "1539/1600 (beta is decreasing), and T_4 = 1 - 4(1/100)(1)^4 = "
            "96/100 = 1536/1600. So underline-beta = 1536/1600 = 24/25 and "
            "g = 3/1600, and p_mc = 24/25. The TAIL is what binds, and it "
            "equals the infimum EXACTLY: lim beta(n) = 96/100 = 24/25. THAT IS "
            "WHY BRANCH 2 IS NOT A WEAKENING -- Lemma lem:windowtail (ii) says "
            "underline-beta -> inf as m grows whenever c < 1, and here it has "
            "already arrived. Remark rem:collapse-fails' reading of the "
            "failure: beta(0) is 'the probability that THE PROBE LIGHT ALONE "
            "makes two detectors click', so 'the failure is NOT AN ARTIFACT OF "
            "THE BOUND; it is a real property of a receiver whose probe already "
            "multiclicks'."
        ),
    ),
    BoundDataCase(
        case_id="BD-COLLAPSE-FAILS-M3",
        port_count=4,
        gamma=F(1, 100),
        betas=(F(1, 100), F(1, 100), F(1, 100), F(1, 100)),
        c=F(1, 2),
        ds=(F(1), F(1), F(1), F(1)),
        beta_values=((3, F(771, 800)),),
        photon_cutoff=2,
        branch="2",
        predicate=None,
        window=3,
        window_minimum=F(771, 800),
        tail=F(24, 25),
        residual_gap=F(3, 800),
        p_mc=F(24, 25),
        derives_from=(
            "THE SAME DATA AT THE MINIMAL WINDOW m = N + 1 = 3, the second "
            "check of Lemma lem:windowtail (ii)'s closed form: W = beta(3) = "
            "771/800, T_3 = 1 - 4/100 = 768/800, so underline-beta = 768/800 = "
            "24/25 -- THE SAME p_mc as at m = 4, the monotone sequence having "
            "already converged -- and g_{2,3} = 771/800 - 768/800 = 3/800, "
            "against the closed form (K-1) gamma c^{N+1} = "
            "3 times (1/100) times (1/2)^3 = 3/800. THEY AGREE EXACTLY."
        ),
    ),
    BoundDataCase(
        case_id="BD-WINDOWTAIL-IV-C1",
        port_count=2,
        gamma=F(1),
        betas=(F(1), F(1)),
        c=F(1),
        ds=(F(1), F(1)),
        beta_values=((0, F(0)), (1, F(0)), (2, F(0)), (3, F(0))),
        photon_cutoff=0,
        branch="lemma-only",
        predicate=None,
        window=3,
        window_minimum=F(0),
        tail=F(-1),
        residual_gap=F(1),
        p_mc=F(0),
        derives_from=(
            "LEMMA lem:windowtail (iv)'s OWN c = 1 COUNTEREXAMPLE, which is why "
            "part (iv) carries the hypothesis c < 1 (round-2 finding F-2-03). "
            "The lemma states it: 'at c = 1 admissibility forces d_k = 1 for "
            "every k, beta is constant, and under Lemma lem:collapse's "
            "hypothesis with beta(N+1) >= 0 that constant is 0 while "
            "T_m = 1 - sum_k beta_k = -(K-1) gamma for every m, so the limit "
            "clause fails whenever gamma > 0 and K >= 2'. Here K = 2, "
            "gamma = beta_k = 1: beta(n) = 1 + 1 - 2 = 0 for EVERY n, "
            "T_m = 1 - 2 = -1 for every m, W = 0, underline-beta = -1 and "
            "g = 1 AT EVERY WINDOW -- the gap never closes and "
            "underline-beta never converges to inf beta = 0.\n"
            "THE BRANCH FIELD READS `lemma-only` AND THAT IS DELIBERATE: "
            "Definition def:pmc would NOT take branch 2 at this data, because "
            "gamma = beta_k = 1 means the receiver is probe-free or probe-off "
            "and predicate (X) selects branch 1, giving "
            "p_mc = max{0, beta(N+1)} = 0. The case exists to freeze the "
            "LEMMA's hypothesis, not a selector outcome, and the lemma itself "
            "closes 'NOTHING CONSUMES (iv): Definition def:pmc branch 1 invokes "
            "Lemma lem:collapse directly.' Both routes give 0 here, so the "
            "emitted value is the same either way."
        ),
    ),
)

#: beta(0) AT EVERY FROZEN BOUND-DATA CASE, and the slack predicate (C) tests.
#: THE SLACK IS -beta(0) AND IS NEVER POSITIVE. This tuple is the evidence for
#: change request CR-4: (case id, beta(0), the (C) slack, whether (C) fires).
BETA_ZERO_AND_C_SLACK: tuple[tuple[str, F, F, bool], ...] = tuple(
    (case.case_id, b0, -b0, False)
    for case, b0 in (
        (BOUND_DATA_CASES[0], F(0)),
        (BOUND_DATA_CASES[1], F(0)),
        (BOUND_DATA_CASES[2], F(0)),
        (BOUND_DATA_CASES[3], F(0)),
        (BOUND_DATA_CASES[4], F(0)),
        (BOUND_DATA_CASES[5], F(0)),
        (BOUND_DATA_CASES[6], F(0)),
        (BOUND_DATA_CASES[7], F(0)),
        (BOUND_DATA_CASES[8], F(0)),
        (BOUND_DATA_CASES[9], F(1, 15)),
        (BOUND_DATA_CASES[10], F(1, 15)),
        (BOUND_DATA_CASES[11], F(99, 100)),
        (BOUND_DATA_CASES[12], F(99, 100)),
        (BOUND_DATA_CASES[13], F(0)),
    )
)

#: Which settings must declare a tail_window, decided from the DECLARATION
#: alone and before any arithmetic (Remark rem:windowdecidable). Frozen as
#: (setting description, predicate (X) holds, a window is required, outcome of
#: supplying one anyway).
WINDOW_REQUIREMENT_CASES: tuple[tuple[str, bool, bool, str], ...] = (
    (
        "a probe-free receiver: Inp_S is empty, so T = {off} by def:probe",
        True,
        False,
        "declares no window at all; one supplied anyway is UNUSED, NOT AN ERROR",
    ),
    (
        "a declared probe at the setting off, Gamma^(t) = 0",
        True,
        False,
        "no window required; one supplied anyway is UNUSED, NOT AN ERROR",
    ),
    (
        "a declared probe at a setting with Gamma^(t) non-zero",
        False,
        True,
        "a window m_t > N is REQUIRED; a missing one is REFUSED",
    ),
    (
        "a probe on but DECOUPLED from every port, Gamma^{1/2} A_LedLed "
        "Gamma^{1/2} = 0",
        False,
        True,
        "a window is REQUIRED: (X) fails on the declaration although "
        "gamma = beta_k = 1 in fact. def:pmc says so in as many words -- such a "
        "receiver 'fails (X), fails (C), and is served by branch 2. THAT IS "
        "CONSERVATIVE, and lem:windowtail (i) makes it sound.'",
    ),
)


O_RP_BOUND = RPOracleEntry(
    oracle_id="O-RP-BOUND",
    superseded_by="0.2.0",
    claims=("RC8",),
    kind="analytic-limit",
    subject=(
        "The uniform high-photon multiclick weight p_mc at small cutoffs where "
        "it is exact -- zero at one configuration and positive at another; the "
        "quantifier domain; predicate (X) at a probe-free receiver and at a "
        "probe-off setting; branch 2 with its window, tail and residual gap; "
        "the closed form of the gap at the minimal window; and the "
        "strengthening slot."
    ),
    derivation="""\
Theorem thm:multiclick-bound, Lemmas lem:collapse and lem:windowtail, Definition
def:pmc, Theorem thm:emitted-bound and Definition def:slot. Fourteen bound-data cases
are frozen above with their arithmetic; what follows is what the SET pins, and
the one finding it produced.

THE QUANTIFIER DOMAIN, WHICH IS THE CLAIM. Eq. eq:pmcstatement is
blk M^{(>N)}_{mc|t} >= p_mc times the identity FOR EVERY t IN T, with the blocks
running over ALL n > N. ARCHITECTURE_SPEC.md Section 7.3 fails a certified
request whose bounds are not uniform over all photon numbers above the cutoff,
so an implementation that emitted beta(N+1) without discharging the infimum
would be emitting a different, weaker object under the same key. The frozen
`branch` and `predicate` fields are exactly the record Section 2.2
`bound_quantifier_domain` requires: N, T, the branch taken, which predicate
selected branch 1, and the window where branch 2 was.

BRANCH 1 IS SELECTED BY (X) IN EVERY CASE FROZEN HERE, and by BOTH of its
clauses: BD-BB84-*, BD-BS-N1, BD-SINGULAR-N1, BD-REM-N0 and BD-COLLAPSE-SHARP by
the FIRST clause (no probe modes declared), and BD-PROBE-OFF-N1 by the SECOND
(the setting carries the vacuum probe, Gamma^(t) = 0). In every one of them
gamma = beta_k = 1 EXACTLY -- by Theorem thm:click-povm (iv) in the first case and
Theorem thm:gaussian-schur (iii) in the second -- so Eq. eq:collapsehyp reads K >= K
and holds WITH EQUALITY, no arithmetic having been performed. That is the
round-2 repair (finding F-2-01) exercised: a strict margin would have excluded
precisely these.

BRANCH 2 IS SELECTED IN THREE CASES, all with a declared window, and the two
window widths at each of two data sets are frozen so that the MONOTONICITY of
Lemma lem:windowtail (ii) is visible: at the probe-on data, underline-beta rises
from -3/125 at m = 2 to 107/750 at m = 3; at the collapse-failure data it is
already 24/25 at m = 3 and stays there at m = 4. AND THE RESIDUAL GAP IS CHECKED
AGAINST ITS CLOSED FORM AT BOTH MINIMAL WINDOWS: lem:windowtail (ii) says
g_{N,N+1} = (K-1) gamma c^{N+1}, which is 1 x (2/3) x (1/2)^2 = 1/6 and
3 x (1/100) x (1/2)^3 = 3/800 respectively, and both agree with the frozen
max{0, W - T} to the last digit. That identity is a genuine cross-check: the two
sides are computed by different routes.

p_mc IS ZERO AT ONE CONFIGURATION AND POSITIVE AT ANOTHER, ON THE SAME RECEIVER.
BD-BB84-N1-ZERO gives 0 and BD-BB84-N2 gives 1/2, differing only in N. Two more
receivers give zero for structural reasons (BD-SINGULAR-N1, BD-COLLAPSE-SHARP),
and BD-PROBE-ON-N1-M2 gives zero because the declared window was too short. THE
ZERO CASES ARE THE LOAD-BEARING HALF: an implementation that raised a zero bound
would look like an improvement and would be unsafe.

THE STRENGTHENING SLOT. SLOT_RECORD freezes Definition def:slot's version-1
shape: r = 1, the single pair (MC_K, p_mc), with the per-setting values emitted
beside the minimum over T (Section 2.2 `high_photon_bounds`). Proposition
prop:slotvalid gives p_i >= 0 and sum_i p_i <= 1, and every frozen p_mc lies in
[0, 1], so the ARCHITECTURE_SPEC.md Section 7.3 failure conditions "p_y < 0" and
"sum_y p_y > 1" cannot be triggered.

=====================================================================
A FINDING: PREDICATE (C) OF DEFINITION def:pmc IS UNREACHABLE.
=====================================================================
Routed as change request CR-4 in interface.yaml. It does not block this freeze
and it is not a soundness defect. The derivation, in full:

STEP 1. Predicate (C) reads
    sum_k beta_k - 1 - (K-1) gamma  >=  eps_hyp  >  0 .
The left-hand side is exactly -beta(0), because Eq. eq:beta at n = 0 under the
convention 0^0 = 1 is
    beta(0) = 1 + (K-1) gamma c^0 - sum_k beta_k d_k^0
            = 1 + (K-1) gamma - sum_k beta_k .
So (C) asserts beta(0) <= -eps_hyp, i.e. beta(0) STRICTLY NEGATIVE. (Note that
Eq. eq:collapsehyp, the hypothesis of Lemma lem:collapse, is the NON-STRICT form
beta(0) <= 0, and the lemma says so in the parenthesis of Eq. eq:collapsehyp.)

STEP 2. beta(0) >= 0 ALWAYS. Remark rem:collapse-fails states the identity: 'the
channel-vacuum block of the conditioned multiclick element is
blk M^{(=0)}_mc = beta(0) EXACTLY (the block is one-dimensional and every
Fock(.)^{(0)} = 1)'. Reading it off Eq. eq:condmc, or off Eq. eq:Mmc in the
unconditioned case: at n = 0 every Fock factor is 1, so
M_mc^{(=0)} = 1 + (K-1) gamma - sum_k beta_k = beta(0). And M_mc is a sum of
POVM elements over MC_K -- positive semidefinite by Theorem thm:click-povm (i) with no
probe declared and by Theorem thm:conditional-povm (ii) with one -- so each of its
photon-number diagonal blocks is positive semidefinite, and the n = 0 block,
being one-dimensional, is a NON-NEGATIVE REAL.

STEP 3. Therefore Eq. eq:collapsehyp holds IF AND ONLY IF beta(0) = 0 exactly,
and predicate (C), which demands strict slack, CAN NEVER FIRE -- for any
receiver this contract describes, at any probe setting, at any parameters.

THE FROZEN EVIDENCE. BETA_ZERO_AND_C_SLACK records beta(0) at every bound-data
case above together with the (C) slack -beta(0) and the verdict False. NINE of
the fourteen have beta(0) = 0 EXACTLY, which is the equality case (X) exists to
admit; the other five have beta(0) > 0 -- 1/15 at the thermal probe, 99/100 at
the contract's own collapse-failure instance -- and there the slack is NEGATIVE.
No case anywhere in this file has a positive slack, and by Step 2 none could.

WHY IT IS NOT A SOUNDNESS DEFECT. Branch 2 is valid for EVERY admissible bound
data with no hypothesis at all (Lemma lem:windowtail (i)), so a setting that
fails both predicates is served conservatively. (C) never firing costs
TIGHTNESS, never SAFETY -- and it costs tightness only where (X) also fails,
which by Remark rem:windowdecidable is exactly where a window is required and
declared.

WHAT AN IMPLEMENTATION MUST DO WHILE THE ITEM IS OPEN, and what this registry
freezes: EVALUATE (C) EXACTLY AS DEFINITION def:pmc STATES IT, with the strict
declared margin eps_hyp, AND NEVER RELAX, WEAKEN OR SKIP IT. The tempting
'repair' -- testing |beta(0)| <= eps_hyp instead -- would license branch 1 on a
COMPUTED near-equality, which is precisely what round-1 finding F-1-03 and
round-2 finding F-2-01 were about, and it is a change of mathematical substance
that belongs to a human at G3, not to an implementer. Interface.yaml records the
three readings a human might take; this file takes none of them.
""",
)


# ===========================================================================
#  Group RP-I -- version-1 numerics and the four residuals (RC9)
# ===========================================================================
#
#  Definition def:residuals writes r_1, r_3 and r_4 with an UNQUALIFIED matrix
#  norm (open implementation choice OIC-3). So: every PASSING residual is frozen
#  as EXACTLY ZERO, which no choice of norm can change, and every FAILING one is
#  frozen under BOTH readings -- the spectral norm and the SQUARED Frobenius
#  norm, both exact rationals here -- and fails under both against
#  TOLERANCE_FIXTURE. r_2 is a scalar and the question does not arise for it;
#  its `value_frobenius_squared` is simply its square.

RESIDUAL_CASES: tuple[ResidualCase, ...] = (
    ResidualCase(
        case_id="R1-PASS-BB84",
        residual_id="r_1",
        value_spectral=F(0),
        value_frobenius_squared=F(0),
        tolerance_key="eps_1",
        passes=True,
        derives_from=(
            "Eq. eq:res1, the CONTRACTIVITY DEFECT: the POSITIVE PART of "
            "Gamma^dagger Gamma - 1 must be zero. I-BB84's Gamma_Inp is an "
            "isometry on the declared columns -- A_Sigma = 1 -- so "
            "Gamma_Inp^dagger Gamma_Inp - 1 = 0 and its positive part is the "
            "zero matrix, at every norm."
        ),
    ),
    ResidualCase(
        case_id="R1-FAIL",
        residual_id="r_1",
        value_spectral=F(5, 4),
        value_frobenius_squared=F(25, 16),
        tolerance_key="eps_1",
        passes=False,
        derives_from=(
            "A SUPPLIED instrument matrix Gamma = diag(3/2, 0) that is NOT a "
            "contraction -- route (ii)'s validity condition "
            "Gamma^dagger Gamma <= 1 violated. Gamma^dagger Gamma - 1 = "
            "diag(9/4 - 1, -1) = diag(5/4, -1), whose POSITIVE PART is "
            "diag(5/4, 0). Spectral norm 5/4; squared Frobenius norm 25/16. "
            "BOTH EXCEED eps_1 = 1/1000 BY THREE ORDERS OF MAGNITUDE, so the "
            "verdict does not turn on OIC-3. Definition def:residuals: 'a "
            "residual above tolerance is A REFUSAL, NOT A WARNING'."
        ),
    ),
    ResidualCase(
        case_id="R2-PASS-RANK2",
        residual_id="r_2",
        value_spectral=F(0),
        value_frobenius_squared=F(0),
        tolerance_key="eps_2",
        passes=True,
        derives_from=(
            "Eq. eq:res2, GRAM POSITIVITY: max over k of max{0, -lmin(A_k)}. "
            "I-RANK2's Grams are diag(1/4, 1/16) and diag(0, 1/4), with "
            "lmin = 1/16 and 0 respectively, both non-negative, so the residual "
            "is exactly 0. r_2 IS A SCALAR and no norm is involved."
        ),
    ),
    ResidualCase(
        case_id="R2-FAIL",
        residual_id="r_2",
        value_spectral=F(1, 2),
        value_frobenius_squared=F(1, 4),
        tolerance_key="eps_2",
        passes=False,
        derives_from=(
            "A DECLARED route-(i) family whose first member is "
            "diag(1, -1/2) -- Hermitian, as the input type requires, but NOT "
            "positive semidefinite, so it is not admissible in the sense of "
            "Definition def:gram. lmin = -1/2 and the residual is "
            "max{0, 1/2} = 1/2, three orders above eps_2 = 1/1000. THE "
            "FROZEN `value_frobenius_squared` IS SIMPLY THE SQUARE OF THE "
            "SCALAR, recorded so that the field means the same thing in every "
            "row of this tuple."
        ),
    ),
    ResidualCase(
        case_id="R3-PASS-UNMONITORED",
        residual_id="r_3",
        value_spectral=F(0),
        value_frobenius_squared=F(0),
        tolerance_key="eps_3",
        passes=True,
        derives_from=(
            "Eq. eq:res3, THE DEFICIENCY IDENTITY Eq. eq:deficiencyid, on "
            "I-UNMONITORED, which is the instrument where BOTH summands are "
            "non-zero. 1 - A_Sigma = diag(3/4, 1); "
            "Gamma_Inp^dagger E_un Gamma_Inp = diag(0, 1/4) (out_1 lies in no "
            "port); 1 - Gamma_Inp^dagger Gamma_Inp = 1 - diag(1/4, 1/4) = "
            "diag(3/4, 3/4). The residual is the norm of "
            "diag(3/4, 1) - diag(0, 1/4) - diag(3/4, 3/4) = 0, EXACTLY, at "
            "every norm. Theorem thm:efficiency (v) proves this identity 'holds for "
            "EVERY receiver instrument and is the correct check that loss was "
            "accounted for exactly once'."
        ),
    ),
    ResidualCase(
        case_id="R3-FAIL-DROPPED-UNMONITORED-TERM",
        residual_id="r_3",
        value_spectral=F(1, 4),
        value_frobenius_squared=F(1, 16),
        tolerance_key="eps_3",
        passes=False,
        derives_from=(
            "THE SAME INSTRUMENT WITH THE UNMONITORED TERM DROPPED, which is "
            "the mistake Eq. eq:deficiencyid exists to catch: taking "
            "E_un = 0 leaves diag(3/4, 1) - 0 - diag(3/4, 3/4) = "
            "diag(0, 1/4), of spectral norm 1/4 and squared Frobenius norm "
            "1/16. Both are 250 times eps_3 = 1/1000, so the verdict is a "
            "refusal under either reading. NOTE WHAT THE ERROR LOOKS LIKE: the "
            "Grams, the ranks and the POVM are all still correct; only the LOSS "
            "ACCOUNTING is wrong, and only in the one direction that a "
            "path-product audit would also miss (Remark rem:wrongcheck)."
        ),
    ),
    ResidualCase(
        case_id="R4-PASS-BB84-n2",
        residual_id="r_4",
        value_spectral=F(0),
        value_frobenius_squared=F(0),
        tolerance_key="eps_4",
        passes=True,
        derives_from=(
            "Eq. eq:res4, BLOCKWISE POVM COMPLETENESS, on PB-BB84-n2: the "
            "identity minus the sum of the six coarse blocks is exactly the "
            "zero 3x3 matrix, because M_mc^{(2)} was DEFINED as the complement "
            "and the five others sum to [[3/8, 0, 1/8], [0, 1/4, 0], "
            "[1/8, 0, 3/8]]. The sqrt2 entries of the + and - blocks cancel in "
            "the sum, which is why the residual is zero in Q[sqrt2] and not "
            "merely small."
        ),
    ),
    ResidualCase(
        case_id="R4-FAIL-MULTICLICK-OMITTED",
        superseded_by="0.2.0",
        residual_id="r_4",
        value_spectral=F(3, 4),
        value_frobenius_squared=F(11, 8),
        tolerance_key="eps_4",
        passes=False,
        derives_from=(
            "THE SAME BLOCK WITH THE MULTICLICK ELEMENT OMITTED FROM THE SUM -- "
            "the error an implementation makes when it enumerates the six "
            "emitted letters but forgets that `mc` aggregates ELEVEN raw "
            "patterns. The residual matrix is then M_mc^{(2)} itself, "
            "[[5/8, 0, -1/8], [0, 3/4, 0], [-1/8, 0, 5/8]], whose spectral norm "
            "is its largest eigenvalue 3/4 (spectrum {1/2, 3/4, 3/4}) and whose "
            "SQUARED Frobenius norm is "
            "25/64 + 1/64 + 36/64 + 1/64 + 25/64 = 88/64 = 11/8. THIS IS THE "
            "ONE FROZEN CASE WHERE THE TWO READINGS OF THE UNNAMED NORM GIVE "
            "GENUINELY DIFFERENT NUMBERS -- 3/4 against 11/8, and the "
            "unsquared Frobenius norm sqrt(11/8) is irrational -- WHICH IS "
            "EXACTLY WHY OIC-3 IS RECORDED AND NOT DECIDED. The VERDICT is the "
            "same under both: 3/4 and 11/8 both exceed eps_4 = 1/1000."
        ),
    ),
)

#: The fail-closed tier rule of Theorem thm:exact-and-evaluated (iii)-(iv). `bound_evaluation`
#: is `floating_point` on EVERY artifact and no path produces `certified`.
TIER_CASES: tuple[tuple[str, str, str, str, str | None], ...] = (
    (
        "TIER-ROUTE-III",
        "(iii) element_graph",
        "certified",
        "estimate",
        "receiver_grams_not_enclosed",
    ),
    (
        "TIER-ROUTE-II",
        "(ii) instrument_matrix",
        "certified",
        "estimate",
        "receiver_grams_not_enclosed",
    ),
    (
        "TIER-ROUTE-I",
        "(i) port_grams",
        "certified",
        "estimate",
        "receiver_grams_not_enclosed",
    ),
    (
        "TIER-ESTIMATE-REQUESTED",
        "any route",
        "estimate",
        "estimate",
        None,
    ),
)

#: Section 2.2 `bound_evaluation`, and Section 1.3: the value is
#: `floating_point` on EVERY artifact in version 1.
#: RE-DERIVED BY HAND from receiver/req:evaluation-label as amended: "bound_evaluation is `rigorous`
#: where every setting's weight was formed by req:rigorous-weight and
#: `floating_point` otherwise"; req:rigorous-weight (i): "On every declaration
#: whose port Grams the engine encloses ... the engine evaluates the weight of
#: every setting" rigorously. These requests are on the exact route, so their
#: artifacts are `rigorous`; `floating_point` stays the label of the fallback.
BOUND_EVALUATION_V1: str = "floating_point"
#: The rigorous label of req:evaluation-label, re-derived as above.
BOUND_EVALUATION_RIGOROUS: str = "rigorous"

#: Remark rem:ia, the DIRECTION the deferred interval enclosures must round.
#: Frozen so that the deferred extension cannot be implemented the wrong way
#: round; NOTHING HERE IS IMPLEMENTED, and no interval assumption is imported.
ENCLOSURE_DIRECTIONS: tuple[tuple[str, str, str], ...] = (
    (
        "lmax(B)",
        "UPPER enclosure",
        "beta is non-decreasing in c = 1 - lmax(B), so over-estimating lmax "
        "under-estimates c and under-estimates beta: the conservative "
        "direction.",
    ),
    (
        "lmin(B_k)",
        "LOWER enclosure",
        "beta is non-increasing in each d_k = 1 - lmin(B_k), so "
        "under-estimating lmin over-estimates d_k and under-estimates beta: "
        "again conservative.",
    ),
)


O_RP_NUMERICS = RPOracleEntry(
    oracle_id="O-RP-NUMERICS",
    superseded_by="0.2.0",
    claims=("RC9",),
    kind="fail-closed",
    subject=(
        "The four residual identities, passing exactly and failing a declared "
        "tolerance; the certified-to-estimate fallback with its verbatim "
        "machine-readable reason on every route; and bound_evaluation."
    ),
    derivation="""\
Definition def:residuals, Theorem thm:exact-and-evaluated and Remark rem:ia.

THE FOUR RESIDUALS, EACH PASSING AND FAILING. Eight cases are frozen above.
Every passing residual is EXACTLY ZERO -- not small, zero -- because the frozen
data are exact and the identities are exact (Theorem thm:exact-and-evaluated (i)). Every failing
one is a REAL mistake an implementation makes, not an arbitrary perturbation:
a supplied non-contraction (r_1), a supplied non-positive Gram (r_2), the
deficiency identity with the unmonitored term dropped (r_3), and blockwise
completeness with the multiclick aggregate forgotten (r_4).

WHAT THE RESIDUALS ARE, AND ARE NOT. Theorem thm:exact-and-evaluated (ii): they are
DIAGNOSTICS. 'Passing them is NECESSARY for the artifact to be self-consistent
and IS NOT SUFFICIENT FOR ANY ENCLOSURE STATEMENT ... a compilation that lost
precision uniformly would satisfy every residual.' So no entry in this file
treats a zero residual as evidence of anything beyond self-consistency, and
`assurance` stays `estimate` throughout.

THE TIER RULE IS FAIL-CLOSED ON EVERY ROUTE. TIER_CASES freezes it: a
`certified` request is answered `estimate` with the reason
`receiver_grams_not_enclosed`, and NOT ONLY ON ROUTE (iii). Theorem thm:exact-and-evaluated
(iii) states the rule for a compiled receiver; (iv) adds that where the Grams
are DECLARED 'the eigenvalue quantities of Theorem thm:multiclick-bound are STILL
EVALUATED IN FLOATING POINT in version 1, SO (iii) STILL APPLIES'. And (iii)
closes: 'NO PATH IN THIS MODULE CAN PRODUCE A certified LABEL.' Section 1.3 says
the same. AN IMPLEMENTATION THAT EXEMPTED ROUTE (i) WOULD BE READING (iv) AS A
LICENCE WHEN IT IS A NARROWING OF SCOPE.

THE REASON STRING IS THE ONE THE CONTRACT SPELLS, and it is the only one frozen
as a string anywhere in this file: `receiver_grams_not_enclosed`. Theorem
thm:exact-and-evaluated (iii); Section 1.3.

THE ENCLOSURE DIRECTIONS ARE FROZEN AND NOT IMPLEMENTED. Remark rem:ia records
which way the deferred interval arithmetic must round -- an UPPER enclosure of
lmax and a LOWER enclosure of lmin -- 'so that the extension cannot be
implemented with the enclosures the wrong way round'. ENCLOSURE_DIRECTIONS
freezes both with the monotonicity that justifies each. NOTHING IN VERSION 1
USES THEM: Remark rem:notopen is explicit that RC9 'does not assert that
floating-point evaluation is sound, it asserts that version 1 DOES NOT CLAIM
soundness and behaves fail-closed in consequence'.

THE NORM. Definition def:residuals names none; see OIC-3, the module docstring,
and R4-FAIL-MULTICLICK-OMITTED, the one frozen case where the two readings
differ numerically and agree on the verdict.
""",
)


# ===========================================================================
#  Group RP-J -- detection efficiency, exactly once (RC10)
# ===========================================================================

EFFICIENCY_CASES: tuple[EfficiencyCase, ...] = (
    EfficiencyCase(
        case_id="EFF-UNIFORM-UNEQUAL",
        ports=(
            ("H", F(9, 25), 1, 1),
            ("V", F(1), 1, 1),
            ("+", F(1), 1, 1),
            ("-", F(1), 1, 1),
        ),
        uniform_within_port=True,
        weighted_total=mat_real(((F(17, 25), 0), (0, 1))),
        is_multiple_of_a_sigma=False,
        derives_from=(
            "Theorem thm:efficiency (i) on I-BB84: A_k -> eta_k A_k, and 'for "
            "eta_k > 0 this PRESERVES rk A_k, so it leaves the "
            "one-mode-per-port criterion of Theorem thm:representation-independence (iv) UNTOUCHED' -- "
            "every rank stays 1. The total becomes "
            "sum_k eta_k A_k = (9/25)(1/2) diag(1, 0) + (1/2) diag(0, 1) + "
            "(1/4)[[1,1],[1,1]] + (1/4)[[1,-1],[-1,1]] = "
            "diag(9/50, 0) + diag(0, 1/2) + diag(1/2, 1/2) = "
            "diag(9/50 + 25/50, 1) = diag(17/25, 1). THIS IS NOT A MULTIPLE OF "
            "A_Sigma = 1, which is the clause of thm:efficiency (i) an implementation "
            "can get wrong: A_Sigma -> sum_k eta_k A_k 'is a multiple of "
            "A_Sigma ONLY WHEN THE eta_k AGREE'. Scaling A_Sigma by a single "
            "average efficiency would give a different -- and, since 17/25 < 1, "
            "a WRONG -- lmax and hence a wrong c in Eq. eq:cd."
        ),
    ),
    EfficiencyCase(
        case_id="EFF-UNIFORM-EQUAL",
        ports=(
            ("H", F(9, 25), 1, 1),
            ("V", F(9, 25), 1, 1),
            ("+", F(9, 25), 1, 1),
            ("-", F(9, 25), 1, 1),
        ),
        uniform_within_port=True,
        weighted_total=mat_real(((F(9, 25), 0), (0, F(9, 25)))),
        is_multiple_of_a_sigma=True,
        derives_from=(
            "The same receiver with EQUAL efficiencies, the one case where the "
            "shortcut happens to be right: sum_k eta_k A_k = eta A_Sigma = "
            "(9/25) times 1. Frozen beside EFF-UNIFORM-UNEQUAL so that an "
            "implementation cannot pass by testing only the symmetric case."
        ),
    ),
    EfficiencyCase(
        case_id="EFF-NONUNIFORM-RANK-DROPS",
        ports=(("k", F(1), 2, 1),),
        uniform_within_port=False,
        weighted_total=mat_real(((1, 0), (0, 0))),
        is_multiple_of_a_sigma=False,
        derives_from=(
            "REMARK rem:effrank's OWN EXAMPLE at epsilon = 1/2. A port "
            "collecting TWO modes with rows (1, 0) and (0, 1/2) has "
            "A_k = diag(1, 1/4), OF RANK 2. Attenuating the second of those "
            "modes to zero -- a diagonal D with entries 1 and 0 INSIDE THE SAME "
            "PORT -- gives, by Eq. eq:noneffgram, "
            "A_k^eff = Gamma^dagger D E_k D Gamma = diag(1, 0), OF RANK 1. So "
            "'a device that did NOT satisfy the one-mode-per-port criterion of "
            "Theorem thm:representation-independence (iv) SATISFIES IT AFTER a within-port attenuation, "
            "and THE CERTIFIED RANK MUST THEREFORE BE RECOMPUTED AFTER EVERY "
            "EFFICIENCY IS APPLIED, NEVER BEFORE.' Theorem thm:efficiency (ii) bounds "
            "it: rk A_k^eff <= rk A_k, WITH STRICT INEQUALITY POSSIBLE, and "
            "this is the case that realizes the strictness. 'This is the ONE "
            "OPERATION IN THIS CONTRACT THAT CAN CHANGE THE ANSWER TO THE RANK "
            "TEST', and Remark rem:rankone points here."
        ),
    ),
)

#: The terminal detector layer D_eta of Definition def:compile, on a mode space
#: with an UNMONITORED mode -- which is where its second summand earns its keep.
#: (case id, per-port etas, the diagonal of D_eta, whether it equals 1).
D_ETA_CASES: tuple[tuple[str, tuple[F, ...], tuple[F, ...], bool, str], ...] = (
    (
        "DETA-UNIT",
        (F(1), F(1)),
        (F(1), F(1), F(1)),
        True,
        "At unit efficiency D_eta = 1 -- which Theorem thm:compilation-well-defined (iii) needs, "
        "since 'if in addition every eta_k = 1 then Gamma is unitary'. The "
        "third entry is the unmonitored mode and it is 1, from the SECOND "
        "summand E_{M minus the union of the ports}.",
    ),
    (
        "DETA-INTERIOR",
        (F(9, 25), F(1)),
        (F(3, 5), F(1), F(1)),
        False,
        "D_eta = sum_k sqrt(eta_k) E_{P_k} + E_{M minus the ports} = "
        "diag(3/5, 1, 1) on the mode space (o_0, o_1, o_2) with ports {o_0} "
        "and {o_1} and o_2 unmonitored.",
    ),
    (
        "DETA-WITHOUT-SECOND-SUMMAND",
        (F(9, 25), F(1)),
        (F(3, 5), F(1), F(0)),
        False,
        "THE TRAP, FROZEN AS THE WRONG ANSWER. Section 3's notation table says "
        "of the second summand: 'the second summand IS NOT DECORATION: without "
        "it D_eta would ANNIHILATE EVERY UNMONITORED MODE, and D_eta = 1 at "
        "unit efficiency (Theorem thm:compilation-well-defined (iii)) WOULD FAIL.' Dropping it gives "
        "diag(3/5, 1, 0), which zeroes the unmonitored mode -- changing no A_k "
        "(Remark rem:unmonitored) but breaking the losslessness statement and "
        "the deficiency identity, since the amplitude that reached o_2 would "
        "vanish from Gamma_Inp^dagger E_un Gamma_Inp.",
    ),
)

#: Theorem thm:efficiency (iv), the composition record: EVERY declared transmittance,
#: the element that declares it, and THE SINGLE SITE at which it enters Gamma.
#: 'Two elements may carry EQUAL NUMERICAL VALUES; they are still two losses and
#: appear as TWO ROWS.' Rows two and three below are that case.
EFFICIENCY_RECORD: tuple[tuple[F, str, str], ...] = (
    (F(9, 25), "C1 beamsplitter bs_1, parameter x", "chain position 1"),
    (F(1, 2), "C7 loss element loss_a, parameter eta_{m0}", "chain position 2"),
    (F(1, 2), "C8 polarizer pol_b, parameter t_perp", "chain position 3"),
    (F(9, 25), "L1 detector layer, parameter eta_H", "terminal factor D_eta"),
)

#: Remark rem:wrongcheck: the deficiency identity against a path-product audit,
#: at the balanced Mach-Zehnder I-MZ where they DISAGREE.
#: (case id, the true deficiency trace, the path-product audit's claim, the
#: discrepancy).
PATH_PRODUCT_CASES: tuple[tuple[str, F, F, F, str], ...] = (
    (
        "MZ-PHI-0",
        F(0),
        F(1, 2),
        F(1, 2),
        "I-MZ at phi = 0. EVERY DECLARED TRANSMITTANCE IS 1 -- two lossless "
        "beamsplitters and a unitary phase shifter -- and Eq. eq:deficiencyid "
        "CORRECTLY RETURNS zero: the compiled matrix is the identity and all "
        "the light entering path 1 reaches port 1. 'A path-product audit sees "
        "TWO PATHS from input 1 to output 1 -- transmit-transmit and "
        "reflect-reflect -- each of power weight (1/2)(1/2) = 1/4, and "
        "concludes a throughput of 1/2, REPORTING A SPURIOUS 50 PER CENT LOSS "
        "THAT DOES NOT EXIST. The missing 1/2 is the INTERFERENCE CROSS TERM, "
        "which no product of transmittances can see.' The checkable invariant "
        "is Eq. eq:deficiencyid and it is what the artifact reports, as "
        "residual r_3.",
    ),
)


O_RP_EFFICIENCY = RPOracleEntry(
    oracle_id="O-RP-EFFICIENCY",
    claims=("RC10",),
    kind="structural-identity",
    subject=(
        "Uniform-within-port attenuation as a scalar on the Gram with rank "
        "preserved; a non-uniform attenuation that lowers rank; the single "
        "structural site and the D_eta second summand; the composition record; "
        "the deficiency identity against a path-product audit that disagrees; "
        "and the decibel conversion at validation."
    ),
    derivation="""\
Theorem thm:efficiency with Remarks rem:effrank, rem:wrongcheck and rem:powervsclick.

(i) UNIFORM WITHIN A PORT IS A SCALAR ON THE GRAM, Eq. eq:etagram, and it
PRESERVES RANK for eta_k > 0. EFF-UNIFORM-UNEQUAL and EFF-UNIFORM-EQUAL freeze
the substitution and the clause that separates them: the total is a multiple of
A_Sigma ONLY when the efficiencies agree.

(ii) NON-UNIFORM WITHIN A PORT IS NOT, AND THE RANK CAN DROP.
EFF-NONUNIFORM-RANK-DROPS is Remark rem:effrank's own instance, and the
consequence is the one an implementation orders wrongly: the rank test of
Theorem thm:representation-independence (iv) must be run AFTER every efficiency, never before.

(iii) ONE STRUCTURAL SITE. Definition def:compile applies D_eta as the single
terminal LEFT factor, after every chain element, so 'it is therefore NOT AN
AUDIT BUT AN INVARIANT OF THE COMPILER: there is exactly ONE SITE at which it
can enter.' D_ETA_CASES freezes the layer at unit and interior efficiency AND
the wrong version without its second summand -- the one that annihilates
unmonitored modes and breaks D_eta = 1 at unit efficiency. The input schema
keeps a C7 loss element and a detector efficiency in DIFFERENT FIELDS
(`element_graph` versus `detector_layer`), and thm:efficiency (iii) says so.

(iv) THE COMPOSITION RECORD, with two elements carrying equal numerical values
appearing as TWO ROWS -- rows 2 and 3 of EFFICIENCY_RECORD both read 1/2 and
name different elements at different sites. Rows 1 and 4 also share a value,
9/25, and one is a chain parameter while the other is the detector layer: the
distinction Remark rem:powervsclick says is 'not inferable from the numbers, so
it is a declared field, AND THE efficiency_record IS WHERE THE ANSWER IS WRITTEN
DOWN'.

(v) THE DEFICIENCY IDENTITY IS THE CORRECT CHECK AND A PRODUCT OF TRANSMITTANCES
IS NOT. PATH_PRODUCT_CASES freezes the balanced Mach-Zehnder where the two
disagree by 1/2 -- a spurious 50 per cent loss that a path-product audit reports
and that does not exist. The frozen instrument I-MZ carries the deficiency zero
and the compiled matrix the identity.

(vi) A DECIBEL-PRESENTED PARAMETER IS CONVERTED AT VALIDATION.
DECIBEL_CONVERSIONS freezes the three exponents where 10^{-L_dB/10} is exactly
rational, and catalogue case C7-decibel-20 freezes the resulting element at the
one of them where the AMPLITUDE is also rational. 'The converted value is what
the artifact carries; THE PRESENTATION IS NOT A SECOND SOURCE OF TRUTH.'
""",
)


# ===========================================================================
#  Group RP-K -- dark counts as a classical outcome channel (RC11)
# ===========================================================================
#
#  Ports are 0-based indices and a click pattern is a SORTED tuple of them, so
#  () is no-click and (0, 1) is the two-port multiclick. Only the NON-ZERO
#  entries of each column are frozen; (D2) makes every other entry zero by
#  definition, and the integrity test checks column-stochasticity on what is
#  frozen.

DARK_CASES: tuple[DarkCase, ...] = (
    DarkCase(
        case_id="DARK-K2",
        port_count=2,
        p_dc=(F(1, 10), F(1, 5)),
        columns=(
            (
                (),
                (
                    ((), F(18, 25)),
                    ((0,), F(2, 25)),
                    ((1,), F(9, 50)),
                    ((0, 1), F(1, 50)),
                ),
            ),
            ((0,), (((0,), F(4, 5)), ((0, 1), F(1, 5)))),
            ((1,), (((1,), F(9, 10)), ((0, 1), F(1, 10)))),
            ((0, 1), (((0, 1), F(1)),)),
        ),
        mc_mass=(
            ((), F(1, 50)),
            ((0,), F(1, 5)),
            ((1,), F(1, 10)),
            ((0, 1), F(1)),
        ),
        r_min=F(1, 50),
        r_min_without_noclick=F(1, 10),
        column_stochastic=True,
        monotone=True,
        derives_from=(
            "Eq. eq:darkR at K = 2 with p_dc|1 = 1/10 and p_dc|2 = 1/5: "
            "R_{S|S'} = 1[S' subset of S] times the product of p_k over "
            "S minus S' times the product of (1 - p_k) over the complement of "
            "S. Column S' = empty: "
            "(9/10)(4/5) = 18/25, (1/10)(4/5) = 2/25, (1/5)(9/10) = 9/50, "
            "(1/10)(1/5) = 1/50, summing to 36/50 + 4/50 + 9/50 + 1/50 = 1. "
            "Column {1}: (4/5) and (1/5). Column {2}: (9/10) and (1/10). "
            "Column {1,2}: 1. Theorem thm:dark-counts (i) proves column-stochasticity "
            "in general by the product expansion, and (D2) is the indicator.\n"
            "MULTICLICK ABSORPTION, thm:dark-counts (iii): R_{MC|S'} = 1 for every "
            "S' in MC_2 -- here for the single column {1,2} -- because (D2) "
            "forces every non-zero entry of a multiclick column into MC.\n"
            "r_min, Eq. eq:rmin: the minimum over EVERY non-multiclick column, "
            "THE NO-CLICK COLUMN INCLUDED: min{1/50, 1/5, 1/10} = 1/50, AND "
            "THE NO-CLICK COLUMN IS WHERE THE MINIMUM SITS. Dropping it would "
            "give min{1/5, 1/10} = 1/10, FIVE TIMES TOO LARGE and an INVALID "
            "bound (Remark rem:rmintrap)."
        ),
    ),
    DarkCase(
        case_id="DARK-K3",
        port_count=3,
        p_dc=(F(1, 10), F(1, 10), F(1, 10)),
        columns=(
            (
                (),
                (
                    ((), F(729, 1000)),
                    ((0,), F(81, 1000)),
                    ((1,), F(81, 1000)),
                    ((2,), F(81, 1000)),
                    ((0, 1), F(9, 1000)),
                    ((0, 2), F(9, 1000)),
                    ((1, 2), F(9, 1000)),
                    ((0, 1, 2), F(1, 1000)),
                ),
            ),
            (
                (0,),
                (
                    ((0,), F(81, 100)),
                    ((0, 1), F(9, 100)),
                    ((0, 2), F(9, 100)),
                    ((0, 1, 2), F(1, 100)),
                ),
            ),
            (
                (1,),
                (
                    ((1,), F(81, 100)),
                    ((0, 1), F(9, 100)),
                    ((1, 2), F(9, 100)),
                    ((0, 1, 2), F(1, 100)),
                ),
            ),
            (
                (2,),
                (
                    ((2,), F(81, 100)),
                    ((0, 2), F(9, 100)),
                    ((1, 2), F(9, 100)),
                    ((0, 1, 2), F(1, 100)),
                ),
            ),
            ((0, 1), (((0, 1), F(9, 10)), ((0, 1, 2), F(1, 10)))),
            ((0, 2), (((0, 2), F(9, 10)), ((0, 1, 2), F(1, 10)))),
            ((1, 2), (((1, 2), F(9, 10)), ((0, 1, 2), F(1, 10)))),
            ((0, 1, 2), (((0, 1, 2), F(1)),)),
        ),
        mc_mass=(
            ((), F(7, 250)),
            ((0,), F(19, 100)),
            ((1,), F(19, 100)),
            ((2,), F(19, 100)),
            ((0, 1), F(1)),
            ((0, 2), F(1)),
            ((1, 2), F(1)),
            ((0, 1, 2), F(1)),
        ),
        r_min=F(7, 250),
        r_min_without_noclick=F(19, 100),
        column_stochastic=True,
        monotone=True,
        derives_from=(
            "Eq. eq:darkR at K = 3 with equal p = 1/10, THE FULL 8-COLUMN "
            "MATRIX. Column empty: p^{|S|} (1-p)^{3-|S|}, i.e. 729, 81, 9, 1 "
            "over 1000 by cardinality, summing to "
            "729 + 3(81) + 3(9) + 1 = 1000. Column {k}: the two other ports "
            "fire independently, giving 81, 9, 9, 1 over 100. Column of a pair: "
            "9/10 and 1/10. Column of the triple: 1.\n"
            "THE MULTICLICK MASSES SHOW THE TRAP AT ITS FULL SIZE: "
            "R_{MC|empty} = 1 - 729/1000 - 3(81/1000) = 28/1000 = 7/250 = "
            "0.028, while R_{MC|{k}} = 1 - (9/10)^2 = 19/100 = 0.19 -- almost "
            "SEVEN TIMES larger. r_min = 7/250, and the single-click-only "
            "minimum 19/100 would be invalid."
        ),
    ),
    DarkCase(
        case_id="DARK-NOT-MONOTONE-REFUSED",
        superseded_by="0.2.0",
        port_count=2,
        p_dc=None,
        columns=(
            ((), (((), F(1)),)),
            ((0,), (((0,), F(1)),)),
            ((1,), (((1,), F(1)),)),
            ((0, 1), (((0,), F(1, 2)), ((0, 1), F(1, 2)))),
        ),
        mc_mass=(
            ((), F(0)),
            ((0,), F(0)),
            ((1,), F(0)),
            ((0, 1), F(1, 2)),
        ),
        r_min=F(0),
        r_min_without_noclick=None,
        column_stochastic=True,
        monotone=False,
        derives_from=(
            "A DECLARED R THAT IS COLUMN-STOCHASTIC BUT NOT MONOTONE, AND IS "
            "THEREFORE REFUSED. Every column sums to 1, so (D1) holds; but "
            "R_{{1}|{1,2}} = 1/2 > 0 with {1,2} NOT a subset of {1}, so (D2) "
            "fails -- 'a dark count ADDS a click and NEVER REMOVES ONE'. "
            "THE CONSEQUENCE IS VISIBLE IN THE MASSES: multiclick absorption "
            "(Theorem thm:dark-counts (iii)) requires R_{MC|S'} = 1 for every "
            "S' in MC, and here the multiclick column {1,2} has "
            "R_{MC|{1,2}} = 1/2 -- HALF THE MULTICLICK WEIGHT LEAKS OUT. "
            "Eq. eq:darkimprove would then be false and the improved bound "
            "unsound, so the channel is refused naming (D2) and NO r_min IS "
            "EMITTED; the frozen r_min = 0 is a placeholder and "
            "r_min_without_noclick is None. Remark rem:corrdark: for a declared "
            "R 'what must then be CHECKED rather than derived is EXACTLY (D2)'."
        ),
    ),
)

#: Remark rem:rmintrap's own numbers, Eq. eq:rmintrapnum, at K = 4 and two
#: probabilities. (case id, K, p, R_MC|empty, R_MC|{k}, r_min, the WRONG value).
RMIN_TRAP_CASES: tuple[tuple[str, int, F, F, F, F, F], ...] = (
    (
        "TRAP-K4-P10",
        4,
        F(1, 10),
        F(523, 10000),
        F(271, 1000),
        F(523, 10000),
        F(271, 1000),
    ),
    (
        "TRAP-K4-P100",
        4,
        F(1, 100),
        F(59203, 100000000),
        F(29701, 1000000),
        F(59203, 100000000),
        F(29701, 1000000),
    ),
)

#: Theorem thm:dark-counts (iv), the improved bound: (1 - r_min) p_mc + r_min, which is
#: >= p_mc since p_mc <= 1. (case id, r_min, p_mc, the improved value).
DARK_IMPROVEMENT_CASES: tuple[tuple[str, F, F, F], ...] = (
    ("IMP-K2-HALF", F(1, 50), F(1, 2), F(51, 100)),
    ("IMP-K2-ZERO", F(1, 50), F(0), F(1, 50)),
    ("IMP-K3-HALF", F(7, 250), F(1, 2), F(257, 500)),
)

#: Theorem thm:dark-counts (ii): the composed elements on a photon-number block, at
#: I-BS's n = 2 block with DARK-K2. (pattern, the composed value).
DARK_COMPOSITION_N2: tuple[tuple[tuple[int, ...], F], ...] = (
    ((), F(0)),
    ((0,), F(1, 5)),
    ((1,), F(9, 40)),
    ((0, 1), F(23, 40)),
)


O_RP_DARK = RPOracleEntry(
    oracle_id="O-RP-DARK",
    claims=("RC11",),
    kind="toy-instance",
    subject=(
        "The per-port independent dark-count matrix at K = 2 and K = 3 in full; "
        "column-stochasticity, monotonicity and multiclick absorption; r_min "
        "computed WITH the no-click column and the wrong value without it; the "
        "improved bound; and a declared R that is not multiclick-absorbing, "
        "refused."
    ),
    derivation="""\
Definition def:darkadm, Theorem thm:dark-counts and Remark rem:rmintrap. Three
channels, two trap cases, three improvement cases and one composed block are
frozen above.

(i) THE PRODUCT FORM IS ADMISSIBLE, thm:dark-counts (i): DARK-K2 and DARK-K3 are
Eq. eq:darkR written out in full, and every column sums to 1 by the product
expansion in the proof. The integrity test re-adds every frozen column.

(ii) STRUCTURE IS PRESERVED, thm:dark-counts (ii): DARK_COMPOSITION_N2 freezes
M-tilde_S = sum_{S'} R_{S|S'} M_{S'} on I-BS's two-photon block, where the bare
blocks are 0, 1/4, 1/4, 1/2 (PB-BS-n2). The composed values are
0; (4/5)(1/4) = 1/5; (9/10)(1/4) = 9/40; and
(1/5)(1/4) + (1/10)(1/4) + 1 x (1/2) = 1/20 + 1/40 + 1/2 = 23/40, summing to
8/40 + 9/40 + 23/40 = 1: STILL A POVM ON THE BLOCK. 'R acts on the outcome label
alone: it commutes with every operation on the optical modes.'

(iii) MULTICLICK ABSORPTION, thm:dark-counts (iii), holds on both admissible channels
and FAILS on the refused one, where the multiclick column carries mass 1/2
instead of 1. That is what (D2) buys, and the refused case is frozen so that the
implication is visible as a computation rather than as a citation.

(iv) THE r_min TRAP, WHICH THE CONTRACT NAMES AND THIS GROUP IS BUILT AROUND.
Eq. eq:rmin minimizes over EVERY non-multiclick column, THE NO-CLICK COLUMN
INCLUDED, and Remark rem:rmintrap says why: 'Minimizing only over the
single-click columns gives an INVALID bound whenever
R_{MC|empty} < R_{MC|{k}}, AND THAT IS THE GENERIC CASE RATHER THAN A CORNER
ONE.' Every frozen channel exhibits it, and the ratio grows with K and with
1/p: 5x at K = 2 with p = (1/10, 1/5); 6.8x at K = 3 with p = 1/10; 5.2x at
K = 4 with p = 1/10; 50x at K = 4 with p = 1/100. RMIN_TRAP_CASES freezes
Eq. eq:rmintrapnum's own instance exactly:
R_{MC|empty} = 1 - (1-p)^4 - 4p(1-p)^3 and R_{MC|{k}} = 1 - (1-p)^3, which at
p = 1/100 are 59203/10^8 and 29701/10^6 -- and the contract's own leading orders
6p^2 and 3p are 6/10^4 = 60000/10^8 and 3/100, matching. THE REASON THE COLUMN
CANNOT BE EXCLUDED is that the no-click element does NOT vanish in the
high-photon sectors of a lossy receiver: by Lemma lem:fock-block-spectrum,
lmin(M_empty^{(n)}) = c^n > 0 whenever lmax(A_Sigma) < 1, 'so IN EXACTLY THE
REGIME WHERE THE HIGH-PHOTON BOUND MATTERS, THE COLUMN THAT THE SHORTCUT
DISCARDS CARRIES WEIGHT'. The contract closes: 'an implementation that computes
r_min MUST BE TESTED AGAINST Eq. eq:rmintrapnum' -- which is TRAP-K4-P100.

(v) THE BOUND IMPROVES, thm:dark-counts (iv): Eq. eq:darkpmc gives
(1 - r_min) p_mc + r_min, and the final comparison is
(1 - r_min) p_mc + r_min - p_mc = r_min (1 - p_mc) >= 0 since p_mc <= 1.
DARK_IMPROVEMENT_CASES freezes three, including the p_mc = 0 case where the
improvement is the whole of r_min. AND THE COMPOSITION IS THE CONSUMER'S:
Section 2.2 says both `photon_blocks` and `high_photon_bounds` are the BARE,
PRE-DARK-COUNT objects, 'R is emitted separately and THE CONSUMER COMPOSES'. So
no frozen p_mc anywhere in this file has r_min folded into it, and an
implementation that folded it in would be emitting a different object under the
same key.
""",
)


# ===========================================================================
#  Group RP-L -- probe conditioning (RC12)
# ===========================================================================
#
#  One channel mode and one declared source mode, the input basis ordered
#  CHANNEL FIRST (Section 2.5 `subsystem_order`), on the instrument I-PROBE.
#  With |Inp_S| = 1 the second-moment matrix Gamma^(t) is the single mean photon
#  number nbar, and Eq. eq:schur becomes scalar arithmetic:
#      c(A, Gamma) = 1 / (1 + nbar A_{ss})
#      A^eff       = A_cc - A_cs (1/nbar + A_ss)^{-1} A_sc
#                  = A_cc - A_cs (1 + A_ss)^{-1} A_sc      at nbar = 1.
#  Every value below is that, evaluated exactly.

PROBE_CASES: tuple[ProbeCase, ...] = (
    ProbeCase(
        case_id="PROBE-THERMAL-NBAR1",
        channel_modes=("Chan",),
        probe_modes=("Led",),
        gamma_diagonal=(F(1),),
        grams=(
            ("1", mat_real(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4))))),
            ("2", mat_real(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4))))),
        ),
        conditioned=(
            (("1", "2"), F(2, 3), mat_real(((F(1, 2),),))),
            (("2",), F(4, 5), mat_real(((F(1, 5),),))),
            (("1",), F(4, 5), mat_real(((F(1, 5),),))),
        ),
        bound_data_case_id="BD-PROBE-ON-N1-M3",
        derives_from=(
            "THEOREM thm:gaussian-schur ON I-PROBE AT A SINGLE-MODE THERMAL PROBE "
            "WITH nbar = 1. The Grams on C^Inp in the subsystem_order basis "
            "(Chan, Led) are A_1 = (1/4)[[1,1],[1,1]] and "
            "A_2 = (1/4)[[1,-1],[-1,1]], so "
            "A_Sigma = A_{[2]} = diag(1/2, 1/2).\n"
            "THE PREFACTORS, Eq. eq:schur: c(A, Gamma) = "
            "1/det(1 + Gamma A_LedLed) = 1/(1 + nbar A_ss) here.\n"
            "  gamma  = c^{(t)}_{[2]}        = 1/(1 + 1/2) = 2/3   "
            "(A_Sigma has (A_Sigma)_ss = 1/2);\n"
            "  beta_1 = c^{(t)}_{[2] minus {1}} = c(A_2, Gamma) = "
            "1/(1 + 1/4) = 4/5;\n"
            "  beta_2 = c(A_1, Gamma) = 1/(1 + 1/4) = 4/5.\n"
            "Theorem thm:gaussian-schur (i) requires c in (0, 1] -- 2/3 and 4/5 "
            "both are -- and (iv) requires gamma <= beta_k, which is "
            "2/3 <= 4/5, the monotonicity J subset of J' implies "
            "c_{J'} <= c_J applied to {2} subset of {1,2}.\n"
            "THE EFFECTIVE GRAMS, the Schur complement of Eq. eq:schur:\n"
            "  B = A_Sigma^eff: A_Sigma is DIAGONAL, so A_cs = 0 and the "
            "subtrahend vanishes: B = 1/2;\n"
            "  B_1 = A_2^eff = 1/4 - (-1/4)(1 + 1/4)^{-1}(-1/4) = "
            "1/4 - (1/16)(4/5) = 1/4 - 1/20 = 1/5;\n"
            "  B_2 = A_1^eff = 1/4 - (1/4)(4/5)(1/4) = 1/5.\n"
            "LEMMA lem:schurmono IS SATISFIED AND IS CHECKABLE HERE: "
            "A_2 <= A_Sigma because A_Sigma - A_2 = A_1 >= 0, and the Schur "
            "map preserves that -- B_1 = 1/5 <= B = 1/2 <= 1 -- which is "
            "Eq. eq:bbkhyp, the first hypothesis of Theorem thm:multiclick-bound. "
            "NOTE THAT THE SCHUR MAP IS NOT ADDITIVE (Remark rem:condpair): "
            "B_1 + B_2 = 2/5 while B = 1/2, so 'the additive hypothesis would "
            "NOT have covered it' and the round-1 restatement of thm:multiclick-bound "
            "on two operators is what makes the conditioned receiver a LITERAL "
            "instance.\n"
            "Eq. eq:cd then gives c = 1 - lmax(B) = 1/2 and "
            "d_k = 1 - lmin(B_k) = 4/5, which is BD-PROBE-ON-N1-M3's data."
        ),
    ),
    ProbeCase(
        case_id="PROBE-VACUUM",
        channel_modes=("Chan",),
        probe_modes=("Led",),
        gamma_diagonal=(F(0),),
        grams=(
            ("1", mat_real(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4))))),
            ("2", mat_real(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4))))),
        ),
        conditioned=(
            (("1", "2"), F(1), mat_real(((F(1, 2),),))),
            (("2",), F(1), mat_real(((F(1, 4),),))),
            (("1",), F(1), mat_real(((F(1, 4),),))),
        ),
        bound_data_case_id="BD-PROBE-OFF-N1",
        derives_from=(
            "THE SAME RECEIVER AT Gamma^(t) = 0, WHICH REPRODUCES THE "
            "UNCONDITIONED GRAMS EXACTLY. Theorem thm:gaussian-schur (iii): 'At "
            "Gamma = 0, Gamma^{1/2} = 0 kills the subtrahend and "
            "det(1 + 0) = 1', so c = 1 for every J and "
            "A^eff = A_ChanChan -- the CHANNEL BLOCK, which is 'exactly the "
            "vacuum elimination of Lemma lem:vacelim'. Reading the blocks off "
            "the frozen Grams: (A_Sigma)_ChanChan = 1/2, "
            "(A_1)_ChanChan = (A_2)_ChanChan = 1/4. So gamma = beta_k = 1 "
            "EXACTLY, WHICH IS PREDICATE (X)'s SECOND CLAUSE, and Eq. eq:cd "
            "gives c = 1/2, d_k = 3/4 -- BD-PROBE-OFF-N1's data. THE PAIR "
            "WITH PROBE-THERMAL-NBAR1 IS THE POINT: same optics, same Grams, "
            "two declared settings, and the bound data differ."
        ),
    ),
)

#: Theorem thm:conditional-povm (ii): the conditional family is COMPLETE AT EACH FIXED
#: t. Frozen on the channel photon-number blocks of PROBE-THERMAL-NBAR1, which
#: are one-dimensional because |Inp_C| = 1.
#: (case id, probe case, n, ((pattern, value), ...), the sum).
CONDITIONAL_COMPLETENESS_CASES: tuple[
    tuple[str, str, int, tuple[tuple[tuple[str, ...], F], ...], F], ...
] = (
    (
        "COND-THERMAL-n0",
        "PROBE-THERMAL-NBAR1",
        0,
        (
            ((), F(2, 3)),
            (("1",), F(2, 15)),
            (("2",), F(2, 15)),
            (("1", "2"), F(1, 15)),
        ),
        F(1),
    ),
    (
        "COND-THERMAL-n1",
        "PROBE-THERMAL-NBAR1",
        1,
        (
            ((), F(1, 3)),
            (("1",), F(23, 75)),
            (("2",), F(23, 75)),
            (("1", "2"), F(4, 75)),
        ),
        F(1),
    ),
    (
        "COND-VACUUM-n0",
        "PROBE-VACUUM",
        0,
        (
            ((), F(1)),
            (("1",), F(0)),
            (("2",), F(0)),
            (("1", "2"), F(0)),
        ),
        F(1),
    ),
)

#: The occupation weights of a single-mode thermal state, which is what makes
#: Definition def:probe's occupation-diagonality hold BY CONSTRUCTION in the
#: Gaussian tier.
#: nbar^m / (1 + nbar)^{m+1}, frozen at nbar = 1 for m = 0..3.
THERMAL_OCCUPATION_WEIGHTS: tuple[tuple[int, F], ...] = (
    (0, F(1, 2)),
    (1, F(1, 4)),
    (2, F(1, 8)),
    (3, F(1, 16)),
)

#: Remark rem:coherent-breaks: a phase-STABLE coherent probe destroys the
#: channel photon-number grading, by a term FIRST ORDER in the amplitude and
#: non-zero at EVERY non-zero amplitude. Frozen structurally, with the
#: maximizing amplitude, which is exact; the modulus at the maximum involves e
#: and is NOT frozen as a number.
COHERENT_BREAK: tuple[tuple[str, str], ...] = (
    (
        "matrix element",
        "(M_{empty|alpha})_{1_Chan, 0_Chan} = -(A_1)_{cs} alpha "
        "exp(-|alpha|^2 (A_1)_{ss})  (Eq. eq:cohbreak)",
    ),
    (
        "vanishes only when",
        "alpha = 0, or the port does not couple channel to probe, (A_1)_{cs} = 0",
    ),
    (
        "order in the amplitude",
        "FIRST -- 'the failure is not an artifact of a bright probe or of a "
        "dim one; it is present at EVERY non-zero amplitude'",
    ),
    (
        "maximizing |alpha|^2 at (A_1)_ss = 1/4",
        "|alpha| = (2 (A_1)_ss)^{-1/2} = sqrt(2), so |alpha|^2 = 2 EXACTLY",
    ),
    (
        "admissible alternative",
        "a phase-RANDOMIZED coherent probe, being a Poisson mixture of Fock "
        "states, is admissible -- IN THE GENERAL FOCK-DIAGONAL TIER, WHICH IS "
        "A NAMED EXTENSION (Section 1.3) and NOT version 1",
    ),
)


O_RP_PROBE = RPOracleEntry(
    oracle_id="O-RP-PROBE",
    claims=("RC12",),
    kind="toy-instance",
    subject=(
        "A thermal-probe conditioning case with its prefactor and "
        "Schur-complement effective Gram in closed form; the vacuum probe "
        "reproducing the unconditioned Grams; completeness of the conditional "
        "family at each fixed t; and Fock-diagonality by construction from a "
        "diagonal second-moment matrix."
    ),
    derivation="""\
Theorem thm:conditional-povm, Theorem thm:gaussian-schur, Lemma lem:schurmono, Theorem
thm:channel-block-diagonal and Remark rem:rc12tobound. Two probe settings, three completeness
cases and the thermal weights are frozen above.

(i) THE CONDITIONAL POVM IS A POVM AT EACH FIXED t.
CONDITIONAL_COMPLETENESS_CASES freezes the four conditioned elements on the
channel photon-number blocks n = 0 and n = 1 of the thermal setting, and they
sum to 1 exactly:
  n = 0:  2/3 + 2/15 + 2/15 + 1/15 = 10/15 + 5/15 = 1;
  n = 1:  1/3 + 23/75 + 23/75 + 4/75 = 25/75 + 50/75 = 1.
The values come from Eq. eq:condmc with the frozen prefactors and effective
Grams: M_empty^{(n)} = gamma (1 - B)^n; M_{k}^{(n)} = beta_k (1 - B_k)^n
- gamma (1 - B)^n; M_mc^{(n)} = 1 + gamma (1 - B)^n - sum_k beta_k (1 - B_k)^n
= beta(n). At n = 0 that is 2/3, 4/5 - 2/3 = 2/15, and beta(0) = 1/15; at n = 1,
(2/3)(1/2) = 1/3, (4/5)(4/5) - 1/3 = 16/25 - 1/3 = 23/75, and
beta(1) = 4/75. THE MULTICLICK ELEMENT IS beta(n) EXACTLY here, because
|Inp_C| = 1 makes every channel block one-dimensional -- which is also why
Remark rem:collapse-fails' identity blk M^{(=0)}_mc = beta(0) is directly
visible: 1/15, POSITIVE, at the thermal setting.

(ii) THE GAUSSIAN CLOSED FORM. PROBE-THERMAL-NBAR1 freezes the prefactor
gamma = 2/3, the two beta_k = 4/5, and the Schur-complement effective Grams
B = 1/2, B_k = 1/5, with the arithmetic in its `derives_from`. THE PREFACTOR IS
NOT ABSORBABLE INTO THE GRAM (Remark rem:condpair: 'c Fock(1 - A) is not
Fock(1 - A') for any A' unless c = 1, evaluate on the vacuum block'), which is
why the emitted canonical object stays the UNCONDITIONED family on the full
input space and conditioning is a named downstream map -- and why exactly one
claim carries prefactors.

(iii) THE VACUUM PROBE REPRODUCES THE UNCONDITIONED GRAMS. PROBE-VACUUM freezes
c = 1 and A^eff = A_ChanChan for all three subsets, which is Theorem
thm:gaussian-schur (iii) and is 'exactly the vacuum elimination of Lemma
lem:vacelim'. Frozen as a SEPARATE case on the SAME optics, so that an
implementation that conditioned wrongly would differ from itself between two
settings of one receiver.

(iv) LOEWNER MONOTONICITY OF THE SCHUR MAP, Lemma lem:schurmono, is checkable on
the frozen numbers: A_2 <= A_Sigma (their difference is A_1 >= 0) and the
effective Grams inherit it, 1/5 <= 1/2. That is Eq. eq:bbkhyp, the hypothesis
Theorem thm:multiclick-bound was RESTATED on in the revision answering
finding F-1-01, and Remark rem:rc12tobound discharges it here. The
other hypothesis, gamma <= beta_k, is Theorem thm:gaussian-schur (iv) and reads
2/3 <= 4/5 on the frozen values.

(v) FOCK-DIAGONALITY BY CONSTRUCTION. Theorem thm:channel-block-diagonal makes probe
block-diagonality NECESSARY AND SUFFICIENT for channel block-diagonality, and
Definition def:probe demands the stronger occupation-diagonality that
'the Gaussian tier satisfies BY CONSTRUCTION'. THERMAL_OCCUPATION_WEIGHTS
freezes the single-mode thermal weights nbar^m / (1 + nbar)^{m+1} at nbar = 1 --
1/2, 1/4, 1/8, 1/16, summing to 1 -- which is the state the proof of
thm:gaussian-schur (ii) verifies mode by mode from the
Glauber-Sudarshan representation Eq. eq:Prep. COHERENT_BREAK freezes the
counterexample structurally: a phase-STABLE coherent probe gives a non-zero
matrix element BETWEEN CHANNEL SECTORS, first order in the amplitude, maximized
at |alpha|^2 = 2 for the frozen (A_1)_ss = 1/4. The modulus at that maximum
involves e and is NOT frozen as a number -- it is irrational and outside
Q[sqrt2], and this file approximates nothing.

(vi) CONDITIONING IS ON DECLARED CLASSICAL DATA. Remark rem:tsm and Section 2.5
`test_statistics_model: output_state`: the module emits the CONDITIONAL family,
complete for each fixed t, and 'NOTHING IN THIS CONTRACT MULTIPLIES BY A q_t'.
NO FROZEN VALUE ANYWHERE IN THIS FILE CARRIES A PROBE-SETTING WEIGHT, and the
completeness cases above sum to 1 AT EACH SETTING SEPARATELY rather than jointly
across settings -- which is the difference between a conditional family and a
state-independent fraction.
""",
)


# ===========================================================================
#  Group RP-M -- the interface (all twelve claims, through Section 2)
# ===========================================================================

MODE_ORDER_CASES: tuple[ModeOrderCase, ...] = (
    ModeOrderCase(
        case_id="ORDER-PROBE-SORTS-FIRST",
        labels=(("A", "H", 0), ("A", "V", 0), ("Z", "H", 0), ("Z", "V", 0)),
        mode_space_order=(0, 1, 2, 3),
        input_index_order=(2, 3, 0, 1),
        orders_disagree=True,
        derives_from=(
            "THE PRECEDENCE CASE OF Section 2.5 `subsystem_order`, which states "
            "that the two orders disagree 'EXACTLY WHEN A PROBE PATH LABEL "
            "SORTS BEFORE A CHANNEL PATH LABEL'. Here the probe path is A and "
            "the channel path is Z. Definition def:modes orders M "
            "LEXICOGRAPHICALLY IN (p, tau, pi) WITH H BEFORE V -- note the key "
            "is (p, tau, pi) and NOT the order the components are written in -- "
            "which puts (A,H,0), (A,V,0), (Z,H,0), (Z,V,0) in that order, so "
            "the PROBE modes are listed first in M. But subsystem_order puts "
            "Inp_C BEFORE Inp_S, each block internally in the order it inherits "
            "from M, so C^Inp is indexed (Z,H), (Z,V), (A,H), (A,V) -- indices "
            "2, 3, 0, 1 of the M listing. THE PRECEDENCE RULE SAYS WHICH WINS "
            "WHERE: 'THIS ORDER TAKES PRECEDENCE: it is the order that indexes "
            "C^Inp, EVERY GRAM AND EVERY BLOCK MATRIX, while the Definition "
            "def:modes order is the order in which M IS LISTED IN THE "
            "ARTIFACT.' An implementation that indexed the Grams by the M order "
            "here would transpose every one of them by a permutation, silently."
        ),
    ),
    ModeOrderCase(
        case_id="ORDER-AGREE",
        labels=(("A", "H", 0), ("A", "V", 0), ("Z", "H", 0), ("Z", "V", 0)),
        mode_space_order=(0, 1, 2, 3),
        input_index_order=(0, 1, 2, 3),
        orders_disagree=False,
        derives_from=(
            "THE SAME MODE SPACE WITH THE ROLES SWAPPED: A is now the CHANNEL "
            "path and Z the PROBE path. The Definition def:modes listing is "
            "unchanged -- it depends only on the labels -- but Inp_C is now "
            "{(A,H), (A,V)} and comes first, so the two orders AGREE and the "
            "identity permutation indexes C^Inp. Frozen beside "
            "ORDER-PROBE-SORTS-FIRST so that the precedence rule is exercised "
            "in both directions: an implementation that ALWAYS reordered, or "
            "that NEVER did, fails one of the two."
        ),
    ),
)

#: The `receiver_construction` presence rule, on ALL THREE routes.
#: Section 2.2: 'PRESENT EXACTLY WHEN ROUTE (iii) WAS USED ... ABSENT EXACTLY
#: WHEN THE GRAMS OR THE INSTRUMENT MATRIX WERE SUPPLIED DIRECTLY.'
RECEIVER_CONSTRUCTION_PRESENCE: tuple[tuple[str, str, bool, str], ...] = (
    (
        "RC-ROUTE-I",
        "port_grams",
        False,
        "ABSENT. The Grams were supplied directly, so there is no reproducible "
        "input they were computed from. Theorem thm:exact-and-evaluated (iv) records what "
        "changes on this route -- 'the compilation error of (ii) DOES NOT "
        "EXIST -- THERE IS NO COMPILATION' -- and (iii) still applies, so the "
        "tier verdict is unchanged.",
    ),
    (
        "RC-ROUTE-II",
        "instrument_matrix",
        False,
        "ABSENT, by the second half of the rule, which names the instrument "
        "matrix explicitly. AND NO OUTPUT KEY CARRIES Gamma EITHER: the "
        "fifteen keys of Section 2.2 do not include the instrument matrix, so "
        "a route-(ii) request emits its Grams and not its matrix. That is "
        "consistent with Theorem thm:representation-independence (i) -- only the Grams are observable "
        "-- and with (ii), which says every admissible family is realized by "
        "SOME instrument, so no particular one is canonical.",
    ),
    (
        "RC-ROUTE-III",
        "element_graph",
        True,
        "PRESENT. It carries 'the declared element graph WITH EVERY PARAMETER, "
        "the port map, and the probe declaration -- THE REPRODUCIBLE INPUT THE "
        "GRAMS WERE COMPUTED FROM'. This is the route on which Theorem "
        "thm:exact-and-evaluated (iii) names its fallback reason, and the two facts are the "
        "same fact: a computed Gram needs its provenance recorded and cannot "
        "carry a rigorous enclosure.",
    ),
)

REFUSAL_CASES: tuple[RefusalCase, ...] = (
    RefusalCase(
        case_id="REF-TWO-ROUTES",
        subject="a request carrying BOTH port_grams AND element_graph",
        failing_condition=(
            "exactly one of port_grams / instrument_matrix / element_graph"
        ),
        reason_is_verbatim=False,
        reason=None,
        derives_from=(
            "Section 2.1, preamble: 'EXACTLY ONE of port_grams, "
            "instrument_matrix, element_graph is present; THE MODULE REFUSES A "
            "REQUEST CARRYING TWO OF THEM RATHER THAN CHOOSING.' No precedence "
            "and no reconciliation: the three routes converge on one canonical "
            "object (Section 2.0) and two presentations of it are not "
            "guaranteed to agree, so choosing would be inventing a check the "
            "contract does not state. contract.tex SPELLS NO REASON STRING for "
            "this refusal, so none is frozen; what is frozen is the failing "
            "CONDITION."
        ),
    ),
    RefusalCase(
        case_id="REF-NONZERO-TOLERANCE",
        subject="a declared parameter carrying tolerance = 1/1000",
        failing_condition=(
            "A-EXACT: the reserved tolerance field is absent or exactly zero"
        ),
        reason_is_verbatim=False,
        reason="parameter uncertainty sets are out of scope",
        derives_from=(
            "Section 2.4, second bullet, and Assumption ass:exact: 'Version 1 "
            "validates it as ABSENT OR EXACTLY ZERO and REFUSES otherwise, with "
            'the reason "parameter uncertainty sets are out of scope". IT IS '
            "REFUSED RATHER THAN IGNORED BECAUSE AN IGNORED TOLERANCE IS A "
            "SILENT CLAIM THAT THE DEVICE IS EXACT.' THE QUOTED PHRASE IS THE "
            "CONTRACT'S OWN PROSE, IN ITS OWN QUOTATION MARKS, AND IS NOT A "
            "DECLARED MACHINE KEY -- `reason_is_verbatim` is False accordingly, "
            "and an implementation is free to spell its machine-readable reason "
            "differently. Section 1.1 item 5 gives the design intent: 'the "
            "eventual device-family work is A SEMANTIC CHANGE TO AN EXISTING "
            "FIELD rather than a breaking schema change'. NOTE THE ONE VALUE "
            "THAT IS NOT REFUSED: tolerance = 0 exactly, which is admitted."
        ),
    ),
    RefusalCase(
        case_id="REF-OUT-OF-DOMAIN-NOT-CLIPPED",
        subject="catalogue entry C1 declared with x = 3/2",
        failing_condition="(E1)",
        reason_is_verbatim=False,
        reason=None,
        derives_from=(
            "Definition def:graph (E1) and Section 2.4, third bullet: 'A "
            "parameter outside its domain is REFUSED; IT IS NEVER CLIPPED TO "
            "THE BOUNDARY.' C1's declared transmittance domain is x in [0, 1], "
            "so x = 3/2 is outside it, and sqrt(1 - x) is not even real. THE "
            "CLIPPED VALUE x = 1 WOULD BE ADMISSIBLE AND WRONG -- it is frozen "
            "as catalogue case C1-boundary-x1 -- WHICH IS WHY CLIPPING IS "
            "FORBIDDEN RATHER THAN MERELY DISCOURAGED. Compare "
            "G-E1-VIOLATION, where the out-of-domain value is a half-open "
            "endpoint and the clipped value is the identity."
        ),
    ),
    RefusalCase(
        case_id="REF-C10-NOT-A-CONTRACTION",
        subject="catalogue entry C10 with the supplied matrix diag(2, 0)",
        failing_condition="(E1)",
        reason_is_verbatim=False,
        reason=None,
        derives_from=(
            "Section 4.3 entry C10: the supplied matrix is 'admitted AFTER THE "
            "EXPLICIT CHECK' that it is a contraction. Here "
            "Gamma^dagger Gamma = diag(4, 0), which is not <= 1, so the check "
            "fails and (E1) refuses. C10 is 'THE ONLY ENTRY for which the check "
            "of Theorem thm:compilation-well-defined (iv)(E1) IS NOT REDUNDANT-BY-THEOREM' -- for "
            "every other entry Theorem thm:catalogue-admissibility has already proved the whole "
            "declared domain admissible, so (E1) reduces to a domain "
            "membership test."
        ),
    ),
    RefusalCase(
        case_id="REF-CYCLE",
        subject="a declared element graph with the edges e -> f and f -> e",
        failing_condition="(E2)",
        reason_is_verbatim=False,
        reason=None,
        derives_from=(
            "Definition def:graph (E2), Remark "
            "rem:noloops. Frozen as compile case G-E2-VIOLATION, whose "
            "linear_extensions tuple is EMPTY -- there is no topological sort "
            "at all, which is the whole content of the refusal. 'A cycle in G "
            "-- a cavity, a ring resonator, any feedback path -- IS REFUSED. "
            "Compiling one would require solving a fixed-point equation whose "
            "contractivity would itself have to be certified.'"
        ),
    ),
    RefusalCase(
        case_id="REF-SUPPORT-INCOMPARABLE",
        subject=("two elements with intersecting supports and no path between them"),
        failing_condition="(E3)",
        reason_is_verbatim=False,
        reason=None,
        derives_from=(
            "Definition def:graph (E3) and Remark rem:e3. Frozen as compile "
            "case G-E3-VIOLATION with the two DIFFERENT compiled matrices the "
            "two sorts would produce. Theorem thm:compilation-well-defined (iv) requires the failing "
            "condition AND THE OFFENDING ELEMENT PAIR to be named. 'Without it, "
            "THE DECLARED RECEIVER DOES NOT DENOTE.'"
        ),
    ),
    RefusalCase(
        case_id="REF-WINDOW-TOO-SMALL",
        subject="tail_window declaring m_t = N at a setting whose probe is on",
        failing_condition="tail_window: m_t > N",
        reason_is_verbatim=False,
        reason=None,
        derives_from=(
            "Section 2.1 `tail_window`: 'm_t > N, VALIDATED ... A value "
            "m_t <= N, or a missing one at a setting that needs it, IS "
            "REFUSED.' The reason it cannot be relaxed: the window of "
            "Eq. eq:windowtail is {n : N < n <= m}, which at m <= N IS EMPTY, "
            "so W_{N,m} would be a minimum over nothing and the residual gap "
            "Eq. eq:resgap would not be a finite real -- which "
            "Lemma lem:windowtail (ii) and Section 2.2 `validation_results` "
            "both require it to be. THAT EMPTY-WINDOW DEFECT WAS ROUND-2 "
            "FINDING F-2-02, closed by fixing the convention to N < n <= m in "
            "BOTH Eq. eq:windowtail and Eq. eq:resgap."
        ),
    ),
    RefusalCase(
        case_id="REF-WINDOW-MISSING",
        superseded_by="0.2.0",
        subject=(
            "no m_t declared at a setting where predicate (X) fails "
            "-- i.e. whose probe is on"
        ),
        failing_condition="def:pmc: no m_t at a setting where (X) fails",
        reason_is_verbatim=False,
        reason=None,
        derives_from=(
            "Definition def:pmc, 'Refusals': 'A declaration supplying no "
            "eps_hyp, or NO m_t AT A SETTING WHERE (X) FAILS, IS REFUSED RATHER "
            "THAN DEFAULTED; by Remark rem:windowdecidable that condition is "
            "DECIDABLE AT INPUT VALIDATION FROM DECLARED DATA ALONE.' That is "
            "the load-bearing part: the requirement is a property of the "
            "DECLARATION -- is Inp_S empty, and is Gamma^(t) zero -- 'without "
            "computing a Gram, a determinant or an eigenvalue', so an "
            "implementation can enforce it while validating input and never "
            "reaches a state where it must default. WINDOW_REQUIREMENT_CASES "
            "freezes all four settings."
        ),
    ),
    RefusalCase(
        case_id="REF-EPS-HYP-MISSING",
        superseded_by="0.2.0",
        subject="a declaration supplying no eps_hyp",
        failing_condition="def:pmc: no eps_hyp declared",
        reason_is_verbatim=False,
        reason=None,
        derives_from=(
            "Definition def:pmc, 'Refusals', and Section 2.1 "
            "`numerical_tolerances`: 'without them the fail_closed convention "
            "HAS NO THRESHOLD TO TEST, so they are DECLARED, NEVER DEFAULTED'. "
            "THE REQUIREMENT IS UNCONDITIONAL AS WRITTEN -- it is not scoped to "
            "receivers that declare a probe -- so even a probe-free receiver, "
            "which can only take branch 1 through predicate (X) and never "
            "evaluates (C), must declare one. That reading is transcribed and "
            "not narrowed: the round-3 verifier recorded it as a standing "
            "wording observation, the scoped prose pass deliberately left it, "
            "and the G3 signature records it as standing."
        ),
    ),
    RefusalCase(
        case_id="REF-DARK-NOT-MONOTONE",
        subject="a declared dark-count channel that is not multiclick-absorbing",
        failing_condition="(D2)",
        reason_is_verbatim=False,
        reason=None,
        derives_from=(
            "Definition def:darkadm (D2) and Remark rem:corrdark: for a "
            "declared R 'what must then be CHECKED rather than derived is "
            "EXACTLY (D2)'. Frozen as DARK-NOT-MONOTONE-REFUSED, which is "
            "column-stochastic and still refused, and whose multiclick column "
            "carries mass 1/2 where Theorem thm:dark-counts (iii) requires 1."
        ),
    ),
    RefusalCase(
        case_id="REF-RESIDUAL-ABOVE-TOLERANCE",
        subject="residual r_3 = 1/4 against the declared eps_3 = 1/1000",
        failing_condition="def:residuals: a residual above its declared tolerance",
        reason_is_verbatim=False,
        reason=None,
        derives_from=(
            "Definition def:residuals: 'Each is compared against A DECLARED "
            "NUMERICAL TOLERANCE, and a residual above tolerance is A REFUSAL, "
            "NOT A WARNING.' Frozen as residual case "
            "R3-FAIL-DROPPED-UNMONITORED-TERM. THE TOLERANCE IS THE DECLARED "
            "INPUT, NOT A CONSTANT OF THE MODULE: TOLERANCE_FIXTURE plays that "
            "role here and is documented as a fixture."
        ),
    ),
    RefusalCase(
        case_id="FALLBACK-CERTIFIED-TO-ESTIMATE",
        subject="a certified request whose Grams were computed by the compiler",
        failing_condition="thm:exact-and-evaluated (iii): floating-point evaluation, no enclosure",
        reason_is_verbatim=True,
        reason="receiver_grams_not_enclosed",
        derives_from=(
            "THE ONE REFUSAL-LIKE OUTCOME WHOSE REASON STRING THE CONTRACT "
            "SPELLS, and it is NOT a no-artifact refusal but a FALLBACK: "
            "Theorem thm:exact-and-evaluated (iii) says the request 'is answered `estimate` "
            "with the machine-readable reason `receiver_grams_not_enclosed`', "
            "and an artifact IS emitted, at the lower tier. Its soundness is "
            "'the trivial direction of ARCHITECTURE_SPEC.md Section 3.5: A "
            "LABEL WITHHELD IS NEVER UNSAFE.' TIER_CASES freezes that the "
            "fallback applies on ALL THREE ROUTES, by thm:exact-and-evaluated (iv)'s '(iii) "
            "still applies' and (iii)'s 'NO PATH IN THIS MODULE CAN PRODUCE A "
            "certified LABEL'."
        ),
    ),
)


O_RP_INTERFACE = RPOracleEntry(
    oracle_id="O-RP-INTERFACE",
    superseded_by="0.2.0",
    claims=CLAIM_IDS,
    kind="fail-closed",
    subject=(
        "The interface of Section 2: the mutually exclusive input routes and "
        "the two-route refusal, the non-zero tolerance refusal, the "
        "out-of-domain refusal that is never clipped, the mirror-handedness "
        "default, the subsystem_order precedence case, the emitted outcome "
        "alphabet, and the receiver_construction presence rule on all three "
        "routes."
    ),
    derivation="""\
contract.tex Section 2 in full, transcribed into interface.yaml at G4 and pinned
here. The entry names EVERY claim because Section 2 is not the property of one:
it says of itself that it IS the interface, and 'anything an implementer needs
and cannot find here is A CONTRACT GAP AND A CHANGE REQUEST, NEVER AN
IMPROVISATION'.

THE VOCABULARY. INPUT_KEYS (fourteen), OUTPUT_KEYS (fifteen), INPUT_ROUTES
(three), CATALOGUE_IDS (ten), CONVENTION_KEYS (sixteen) and ASSUMPTION_ROWS
(twelve) are the machine keys of Sections 2.1, 2.2, 2.5 and 5, in the order the
contract lists them. The integrity test binds each to interface.yaml, so the
transcription and the freeze cannot drift.

THE ROUTES ARE MUTUALLY EXCLUSIVE AND A DOUBLE REQUEST IS REFUSED, not resolved
by precedence (REF-TWO-ROUTES). That is the same discipline as the (E3) refusal:
where two presentations could disagree, the contract refuses rather than
choosing, and Section 2.0 makes the three routes CONVERGE on one canonical
object before any physics happens.

A NON-ZERO TOLERANCE IS REFUSED WITH THE CONTRACT'S OWN REASON, AS PROSE
(REF-NONZERO-TOLERANCE). The one admitted value is exactly zero.

A PARAMETER OUTSIDE ITS DOMAIN IS REFUSED AND NEVER CLIPPED
(REF-OUT-OF-DOMAIN-NOT-CLIPPED, and G-E1-VIOLATION at a half-open endpoint). In
both frozen cases THE CLIPPED VALUE IS ADMISSIBLE AND WRONG, which is why the
prohibition is stated rather than assumed.

THE MIRROR HANDEDNESS DEFAULT IS A DEFAULT THE CONTRACT ITSELF FIXES, and is
recorded as such rather than as an open choice: Section 2.5 says 'an explicit
boolean per mirror, DEFAULT false, documented as a coordinate-frame choice and
NEVER APPLIED IMPLICITLY', and catalogue entry C5 repeats it in its parameter
list. Catalogue cases C5-boundary-ideal (fl = false) and C5-flip (fl = true) are
frozen as different matrices, so the flag is visibly not cosmetic. IT IS THE
ONLY DEFAULT VALUE FIXED ANYWHERE IN THE INTERFACE; every other missing datum is
a refusal under `fail_closed`.

THE subsystem_order PRECEDENCE CASE IS FROZEN IN BOTH DIRECTIONS
(MODE_ORDER_CASES). The two orders disagree exactly when a probe path label
sorts before a channel path label, and the convention says which one indexes
what: subsystem_order indexes C^Inp and every Gram and block matrix; the
Definition def:modes order is the order M is LISTED in. Note also that def:modes
sorts on the key (p, tau, pi) -- NOT in the order the label components are
written -- with H before V.

THE OUTCOME ALPHABET IS ORDERED WITH STABLE IDS AND PRESENTATION LABELS
(OUTCOME_ALPHABET, and the coarse-graining cases of Group RP-G). What is frozen
is that the IDs are stable and the labels are metadata; WHICH IDs are assigned,
and whether the emitted order comes from V's declaration or from an ordering of
2^[K] through cg, is open implementation choice OIC-1 and is NOT decided here.

THE receiver_construction PRESENCE RULE IS FROZEN ON ALL THREE ROUTES
(RECEIVER_CONSTRUCTION_PRESENCE), with both halves of the contract's sentence:
present exactly on route (iii), absent exactly on (i) and (ii). It is the ONLY
conditional output key; the other fourteen are always present.

WHAT IS FROZEN AS A NAMED CHECK AND NOT AS A SPELLING. Eleven refusal cases are
frozen above and exactly ONE carries `reason_is_verbatim = True`:
`receiver_grams_not_enclosed`. Every other case carries the contract's own
IDENTIFIER for the failing condition -- (E1), (E2), (E3), (D2), a residual above
its declared tolerance, a missing m_t or eps_hyp, the exactly-one-route rule,
the tolerance field -- and no invented string. Section 2.5 `fail_closed` fixes
the OBLIGATION ('a refusal with a machine-readable reason and NO artifact') and
the contract fixes the identity of the check; THE SPELLING IS CODE'S, and
inventing one in frozen evidence would decide what the contract leaves open.
""",
)


# ===========================================================================
#  THE 0.2.0 AMENDMENT -- run A's freeze of the delta
# ===========================================================================
#
#  Everything from here to the registry tuple was derived BY HAND from
#  contract.tex 0.2.0 (sha256
#  7482735f1386e33510b7d6f013f2157cdc9d455b5c92412509207021616f80c8) BEFORE any
#  code changed, in the scoped implementation band the rulings
#  opened. IT IS PURELY ADDITIVE: not one value frozen at 0.1.3 is edited or
#  deleted. Where the amendment invalidates a 0.1.3 case's INPUT SHAPE or
#  EXPECTED VALUE, or leaves its framing stale, the case is MARKED in
#  SUPERSEDED_BY_0_2_0 below with the contract site and its replacement, and
#  run B retires or rewrites it deliberately.
#
#  WHY ADDITIVE RATHER THAN IN PLACE. The freeze rule says
#  an expected value that turns out to be wrong "is a FINDING, reported and
#  corrected deliberately with its derivation, NEVER EDITED IN PASSING TO MAKE
#  A TEST GREEN". Editing TOLERANCE_FIXTURE or REFUSAL_REASONS_VERBATIM in
#  place would silently change what the 0.1.3 golden tests replay, at the exact
#  moment nobody has yet decided what those tests should say. So the 0.1.3
#  objects stand, byte for byte, and the marks say what run B must do to them.
#
#  THE DECLARED TOLERANCES ARE A FIXTURE, AS BEFORE. TOLERANCE_FIXTURE_0_2_0
#  plays the role of the declared input for every case below, exactly as
#  TOLERANCE_FIXTURE did at 0.1.3, and for the same reason: Section 2.1 makes
#  the tuple "declared, never defaulted", so a frozen expected value carrying a
#  tolerance of its own invention would invent the one input the contract
#  insists on being given. Every case below states which fixture value it is
#  read against.

# ---------------------------------------------------------------------------
#  The declared tolerance tuple at 0.2.0, AS A FIXTURE
# ---------------------------------------------------------------------------
#
#  SIX members, as at 0.1.3, but different ones: eps_5 is new and eps_hyp is
#  gone (Section 1.1, "Interface deltas"). Every member lies in the DECLARED
#  DOMAIN [0, 1) (Section 2.1 `numerical_tolerances`; Rem. rem:tolerancedomain),
#  and the values are round rationals chosen only so that a reader can see the
#  verdicts do not turn on them.

#: The declared tolerance tuple of contract.tex 0.2.0, as a fixture.
TOLERANCE_FIXTURE_0_2_0: dict[str, F] = {
    "eps_1": F(1, 1000),
    "eps_2": F(1, 1000),
    "eps_3": F(1, 1000),
    "eps_4": F(1, 1000),
    "eps_5": F(1, 1000),
    "eps_gap": F(1, 100),
}

#: The declared domain of every member, as the half-open interval it is.
#: Rem. rem:tolerancedomain: "Each of eps_1, ..., eps_5 and eps_gap is declared
#: in [0, 1), validated at input, and a value outside that interval is refused."
TOLERANCE_DOMAIN: tuple[F, F] = (F(0), F(1))

#: Whether the endpoints belong: 0 does, 1 does not.
TOLERANCE_DOMAIN_CLOSED_AT: tuple[bool, bool] = (True, False)


# ---------------------------------------------------------------------------
#  The reason strings contract.tex 0.2.0 SPELLS
# ---------------------------------------------------------------------------

#: The FIVE machine-readable REFUSAL reasons of Section 2.6, in the table's own
#: order. Transcribed character for character; the LaTeX `\allowbreak` macros
#: in the source are line-break hints and are not part of the key.
REFUSAL_REASONS_VERBATIM_0_2_0: tuple[str, ...] = (
    "dark_count_channel_declared_twice",
    "splitting_ratio_presentation_unsupported",
    "port_gram_rank_exceeds_port_size",
    "photon_block_positivity_residual_above_tolerance",
    "tolerance_outside_declared_domain",
)

#: The SIXTH spelled string, which is NOT a refusal. Section 2.6's closing
#: paragraph: "A certified request that depends on compiled Grams is answered
#: estimate with the reason receiver_grams_not_enclosed. THAT IS A TIER
#: FALLBACK, AND AN ARTIFACT IS EMITTED; it is named here only so the two kinds
#: of machine-readable reason are not confused."
TIER_FALLBACK_REASON_VERBATIM: str = "receiver_grams_not_enclosed"

#: The key vocabulary: the five refusals plus the one fallback. NO SEVENTH
#: STRING IS SPELLED ANYWHERE IN contract.tex 0.2.0, and none is invented here.
REASON_VOCABULARY_0_2_0: tuple[str, ...] = (
    *REFUSAL_REASONS_VERBATIM_0_2_0,
    TIER_FALLBACK_REASON_VERBATIM,
)

#: Which of the six emits an artifact. The five refusals do not ("a refusal
#: with a machine-readable reason and NO artifact", Section 2.5 `fail_closed`);
#: the fallback does, at the lower tier.
REASON_EMITS_ARTIFACT: tuple[tuple[str, bool], ...] = tuple(
    (reason, reason == TIER_FALLBACK_REASON_VERBATIM)
    for reason in REASON_VOCABULARY_0_2_0
)

#: The SIX further refusals Section 2.6's preamble enumerates WITHOUT a
#: spelling: "every further failed validation named in Section 2 ... refuses
#: under the same convention at the site that states it, WITH A REASON STRING
#: THE IMPLEMENTER NAMES". The identity of the check is contract; the spelling
#: is code's, and none is invented here. (condition, stated at)
REFUSALS_NAMED_WITHOUT_A_SPELLING: tuple[tuple[str, str], ...] = (
    ("two input routes supplied at once", "Section 2.1 preamble"),
    ("a violated condition (E1), (E2) or (E3)", "Def. def:graph; Thm. thm:compilation-well-defined (iv)"),
    ("a non-zero `tolerance` field", "Section 2.4, second bullet; Ass. ass:exact"),
    ("a missing or too-small m_t", "Section 2.1 `tail_window`; Def. def:pmc"),
    ("a missing declared tolerance", "Section 2.1 `numerical_tolerances`"),
    (
        "a probe state outside the Gaussian tier",
        "Def. def:probe; Req. req:probe-diagonal-admission",
    ),
)

#: The SEVENTEEN convention bullets of Section 2.5 at 0.2.0, by the key each
#: declares. Sixteen at 0.1.3 plus `numerical_tolerance_assignment`, inserted
#: between `numerics` and `fail_closed`.
CONVENTION_KEYS_0_2_0: tuple[str, ...] = (
    "log_base",
    "entropy_variant",
    "test_statistics_model",
    "round_homogeneity",
    "matrix_convention",
    "composition_order",
    "embedding",
    "subsystem_order",
    "polarization_basis",
    "waveplate_convention",
    "beamsplitter_convention",
    "mirror_handedness",
    "povm_index_convention",
    "numerics",
    "numerical_tolerance_assignment",
    "fail_closed",
    "artifact_bindings_mathematical_spec_version",
)

#: The version string the artifact binds at 0.2.0 (Section 2.5, last bullet;
#: Section 2.2 `mathematical_spec_version`).
MATHEMATICAL_SPEC_VERSION_0_2_0: str = "receiver-povm@0.2.0"


# ---------------------------------------------------------------------------
#  Group RP-N -- the fifth residual r_5 (RC9)
# ---------------------------------------------------------------------------
#
#  Eq. eq:res5: r_5 = max over v, n, t of rho(blk M^{(=n)}_{v|t}), with the
#  Hermiticity-and-positivity defect of Eq. eq:rhodef
#
#      rho(X) = max{ ||X - X^dagger|| , (-lmin((X + X^dagger)/2))_+ }
#
#  and "||.|| IS THE SPECTRAL NORM throughout Eq. eq:res1-Eq. eq:rhodef". That
#  sentence CLOSES the 0.1.3 open implementation choice OIC-3, so no case below
#  carries a second reading of the norm: rho is a determinate number.
#
#  THE DIRECTION IS REFUSE-ONLY, and it is the one thing an implementation is
#  most likely to get wrong here. Def. def:residuals: "No block is Hermitized,
#  symmetrized, projected onto the positive cone, clamped or repaired in any
#  way: WHAT THE ARTIFACT CARRIES IS THE COMPUTED BLOCK ITSELF, and r_5 reports
#  that block's own defect." Every failing case below therefore freezes a
#  REFUSAL and NO repaired block.


@dataclass(frozen=True)
class Residual5Case:
    """One evaluation of Eq. eq:rhodef on a frozen block (Def. def:residuals)."""

    case_id: str
    #: The block X, as it would be emitted -- never a repaired version of it.
    block: Mat
    #: ||X - X^dagger||, the SPECTRAL norm, exactly.
    hermiticity_defect: F
    #: (-lmin((X + X^dagger)/2))_+, exactly.
    negativity_defect: F
    #: rho(X), the maximum of the two.
    rho: F
    tolerance_key: str
    passes: bool
    #: The verbatim reason where the case refuses; None where it passes.
    refusal_reason: str | None
    #: True where X is Hermitian, so that Prop. prop:res5 (ii) applies.
    hermitian: bool
    derives_from: str


RESIDUAL5_CASES: tuple[Residual5Case, ...] = (
    Residual5Case(
        case_id="R5-FAIL-HERMITICITY-DEFECT",
        block=mat_real(((F(1, 2), F(1, 4)), (F(0), F(1, 2)))),
        hermiticity_defect=F(1, 4),
        negativity_defect=F(0),
        rho=F(1, 4),
        tolerance_key="eps_5",
        passes=False,
        refusal_reason="photon_block_positivity_residual_above_tolerance",
        hermitian=False,
        derives_from=(
            "AN EMITTED BLOCK WITH A HERMITICITY DEFECT AND NO NEGATIVITY "
            "DEFECT, which is the case r_2 and r_4 cannot see: r_2 lives on the "
            "Grams, one compilation stage earlier, and r_4 constrains only the "
            "SUM over S (Rem. rem:res5why).\n"
            "X = [[1/2, 1/4], [0, 1/2]].\n"
            "  X - X^dagger = [[0, 1/4], [-1/4, 0]]. That matrix A is real "
            "skew-symmetric, so A^dagger A = [[1/16, 0], [0, 1/16]] and both "
            "singular values are 1/4; the SPECTRAL norm is therefore 1/4 "
            "EXACTLY.\n"
            "  H = (X + X^dagger)/2 = [[1/2, 1/8], [1/8, 1/2]], whose "
            "eigenvalues are 1/2 -/+ 1/8 = {3/8, 5/8}. lmin(H) = 3/8 > 0, so "
            "(-lmin(H))_+ = 0.\n"
            "  rho(X) = max{1/4, 0} = 1/4.\n"
            "AGAINST eps_5 = 1/1000 THIS IS 250 TIMES THE TOLERANCE, so the "
            "request is REFUSED with the verbatim reason "
            "`photon_block_positivity_residual_above_tolerance` (Section 2.6). "
            "NO REPAIR: the Hermitized block (X + X^dagger)/2 is a DIFFERENT "
            "OPERATOR and no claim of this contract holds for it."
        ),
    ),
    Residual5Case(
        case_id="R5-FAIL-NEGATIVE-EIGENVALUE",
        block=mat_real(((F(3, 4), F(0)), (F(0), F(-1, 8)))),
        hermiticity_defect=F(0),
        negativity_defect=F(1, 8),
        rho=F(1, 8),
        tolerance_key="eps_5",
        passes=False,
        refusal_reason="photon_block_positivity_residual_above_tolerance",
        hermitian=True,
        derives_from=(
            "AN EMITTED BLOCK THAT IS HERMITIAN AND HAS A NEGATIVE EIGENVALUE.\n"
            "X = diag(3/4, -1/8).\n"
            "  X - X^dagger = 0, so the first entry of the maximum is 0.\n"
            "  H = X and lmin(X) = -1/8, so (-lmin(X))_+ = 1/8.\n"
            "  rho(X) = max{0, 1/8} = 1/8, which is 125 times eps_5 = 1/1000: "
            "REFUSED, same reason.\n"
            "THIS CASE IS ALSO Prop. prop:res5 (ii) FROZEN: 'If X = X^dagger "
            "then rho(X) = (-lmin(X))_+, WHICH IS THE FORM Eq. eq:res2 TAKES ON "
            "A GRAM.' Compare residual case R2-FAIL, where the same expression "
            "on a declared Gram gives 1/2: the two residuals are the same "
            "quantity at two different stages, which is why they carry "
            "different tolerances and are reported separately."
        ),
    ),
    Residual5Case(
        case_id="R5-PASS-BB84-MULTICLICK-N2",
        block=mat_real(
            (
                (F(5, 8), F(0), F(-1, 8)),
                (F(0), F(3, 4), F(0)),
                (F(-1, 8), F(0), F(5, 8)),
            )
        ),
        hermiticity_defect=F(0),
        negativity_defect=F(0),
        rho=F(0),
        tolerance_key="eps_5",
        passes=True,
        refusal_reason=None,
        hermitian=True,
        derives_from=(
            "AN ACTUAL EMITTED BLOCK, taken unchanged from POVM block case "
            "PB-BB84-n2: the two-photon multiclick block "
            "M_mc^{(2)} = [[5/8, 0, -1/8], [0, 3/4, 0], [-1/8, 0, 5/8]]. It is "
            "real symmetric, so X - X^dagger = 0; its spectrum is "
            "{1/2, 3/4, 3/4} (the 2x2 corner [[5/8, -1/8], [-1/8, 5/8]] has "
            "eigenvalues 5/8 -/+ 1/8, and the middle entry is 3/4), so "
            "lmin = 1/2 > 0 and (-lmin)_+ = 0. rho = max{0, 0} = 0 EXACTLY.\n"
            "THIS IS Prop. prop:res5 (iv), NOT AN ACCIDENT OF THE NUMBERS: "
            "'Every block the artifact emits satisfies rho = 0 EXACTLY', "
            "because blk M^{(=n)}_{v|t} is the compression Pi_n F_{v|t} Pi_n of "
            "a positive operator by an orthogonal projector, read on the range "
            "of Pi_n, and such a compression is Hermitian and positive "
            "semidefinite. 'So r_5 is a residual in exactly the sense of the "
            "other four: THE EXACT VALUE IS 0, AND WHAT IS EMITTED IS THE "
            "FLOATING-POINT EVALUATION.'"
        ),
    ),
    Residual5Case(
        case_id="R5-PASS-VACUUM-BLOCK-N0",
        block=mat_real(((F(1),),)),
        hermiticity_defect=F(0),
        negativity_defect=F(0),
        rho=F(0),
        tolerance_key="eps_5",
        passes=True,
        refusal_reason=None,
        hermitian=True,
        derives_from=(
            "THE SMALLEST EMITTED BLOCK THERE IS: the n = 0 block of the "
            "no-click element, the 1x1 matrix [1]. Theorem thm:click-povm (iii) gives "
            "blk M^{(=0)}_empty = 1 and blk M^{(=0)}_S = 0 for every non-empty "
            "S, and every Fock(.)^{(0)} = 1. rho([1]) = max{0, (-1)_+} = 0. "
            "FROZEN BECAUSE THE MAXIMUM OF Eq. eq:res5 RUNS OVER EVERY EMITTED "
            "v, n AND t -- 'exactly the blocks the artifact emits' -- so the "
            "one-dimensional n = 0 blocks are in it, and an implementation that "
            "skipped them would be reporting a maximum over a smaller set."
        ),
    ),
)

#: Prop. prop:res5 (iii), the expectation bounds, on the two FAILING cases
#: above. For every unit vector psi: Re <psi|X|psi> >= -rho(X) and
#: |Im <psi|X|psi>| <= rho(X)/2. Frozen at vectors where each bound is ATTAINED
#: WITH EQUALITY, so that a weaker constant would be visible immediately.
#: (case id, vector description, Re part, Im part, -rho, rho/2, which bound is
#: tight)
RES5_EXPECTATION_CASES: tuple[tuple[str, str, F, F, F, F, str], ...] = (
    (
        "R5-FAIL-HERMITICITY-DEFECT",
        "psi = (1, 0)",
        F(1, 2),
        F(0),
        F(-1, 4),
        F(1, 8),
        "neither",
    ),
    (
        "R5-FAIL-HERMITICITY-DEFECT",
        "psi = (1, i)/sqrt2",
        F(1, 2),
        F(1, 8),
        F(-1, 4),
        F(1, 8),
        "imaginary",
    ),
    (
        "R5-FAIL-NEGATIVE-EIGENVALUE",
        "psi = (0, 1)",
        F(-1, 8),
        F(0),
        F(-1, 8),
        F(1, 16),
        "real",
    ),
)

#: Which residuals EXIST on which route (Def. def:residuals, "Which residuals
#: exist on which route"; Section 2.2 `validation_results`; Thm. thm:exact-and-evaluated (iv)).
#: On route (i) the keys of r_1 and r_3 are ABSENT -- absent, NOT ZERO.
#: (route, present, absent)
RESIDUAL_ROUTE_PRESENCE: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("port_grams", ("r_2", "r_4", "r_5"), ("r_1", "r_3")),
    ("instrument_matrix", ("r_1", "r_2", "r_3", "r_4", "r_5"), ()),
    ("element_graph", ("r_1", "r_2", "r_3", "r_4", "r_5"), ()),
)

#: The tolerances that are DECLARED on every route but UNUSED on route (i).
#: Section 2.1: "eps_1 and eps_3 are UNUSED on route (i), where r_1 and r_3 do
#: not exist and no contractivity check is made, and AN UNUSED TOLERANCE IS
#: UNUSED, NOT AN ERROR."
TOLERANCES_UNUSED_ON_ROUTE_I: tuple[str, ...] = ("eps_1", "eps_3")

#: Def. def:residuals now names the norm. This closes OIC-3.
RESIDUAL_NORM_0_2_0: str = "spectral"


O_RP_RES5 = RPOracleEntry(
    oracle_id="O-RP-RES5",
    claims=("RC9",),
    kind="structural-identity",
    subject=(
        "The fifth residual r_5: the Hermiticity-and-positivity defect of an "
        "emitted photon-number block, on a block with a Hermiticity defect, on "
        "a Hermitian block with a negative eigenvalue, and on two blocks the "
        "artifact actually emits, where it is exactly zero; the refuse-only "
        "direction with its verbatim reason; the expectation bounds of "
        "Proposition prop:res5 (iii) at vectors that attain them; and which "
        "residuals exist on which input route."
    ),
    derivation="""\
Definition def:residuals (Eq. eq:res5, Eq. eq:rhodef), Proposition prop:res5,
Remark rem:res5why, Section 2.2 `validation_results`, Section 2.6.

WHAT rho MEASURES, AND WHY IT IS A MAXIMUM OF TWO THINGS. Eq. eq:rhodef splits
a square X into its Hermitian and skew-Hermitian parts, X = H + S/2 with
H = (X + X^dagger)/2 and S = X - X^dagger, and takes
rho(X) = max{ ||S||, (-lmin(H))_+ } in the SPECTRAL norm. Proposition
prop:res5 (i): rho(X) = 0 if and only if X = X^dagger AND X >= 0 -- both
conditions, which is exactly what a consumer validating an operator row
checks. R5-FAIL-HERMITICITY-DEFECT has the first entry non-zero and the second
zero; R5-FAIL-NEGATIVE-EIGENVALUE has it the other way round. Freezing both
separately is the point: a defect in either factor is invisible to the other.

THE NORM IS NAMED, AND THAT IS NEW. 0.1.3 wrote r_1, r_3 and r_4 with an
unqualified matrix norm and this registry froze every FAILING residual under
BOTH natural readings so that the verdict was frozen while the number was not
(open implementation choice OIC-3). Definition def:residuals 0.2.0 states
"||.|| IS THE SPECTRAL NORM throughout Eq. eq:res1-Eq. eq:rhodef", so rho is a
determinate number and no case here carries a second reading. Section 1.1's
first disclosure records that the statement "CAN CHANGE A COMPUTED RESIDUAL
VALUE" and is therefore recorded rather than passed off as prose. IT CHANGES
NO VALUE FROZEN AT 0.1.3: each of the four failing residuals there was frozen
with its spectral norm in `value_spectral`, and those four numbers -- 5/4,
1/2, 1/4 and 3/4 -- are the spectral norms the amendment now mandates. What is
superseded is the SECOND reading, not the first.

REFUSE-ONLY, WITH A SPELLED REASON. r_5 > eps_5 refuses with
`photon_block_positivity_residual_above_tolerance`, one of the five strings
Section 2.6 spells verbatim, and "no block is Hermitized, symmetrized,
projected onto the positive cone, clamped or repaired in any way". The two
failing cases above therefore freeze a refusal and NOT a repaired block. Remark
rem:res5why names the second thing r_5 is not: an enclosure. "r_5 = 0 says that
the COMPUTED block is Hermitian and positive, NOT THAT IT IS CLOSE TO THE
EXACT ONE, which is Theorem thm:exact-and-evaluated (ii) exactly as for r_1, ..., r_4."

THE EXACT VALUE IS ZERO ON EVERY EMITTED BLOCK, and the two passing cases are
blocks the artifact really emits rather than convenient matrices:
M_mc^{(2)} of the BB84 receiver, taken unchanged from PB-BB84-n2, and the
one-dimensional n = 0 no-click block. Proposition prop:res5 (iv) proves the
general statement -- an emitted block is the compression Pi_n F_{v|t} Pi_n of a
positive operator, hence Hermitian positive semidefinite -- so a NON-zero r_5
is always a numerical artefact and never a property of the mathematics. That is
what makes it a residual in the sense of the other four.

THE EXPECTATION BOUNDS ARE FROZEN AT VECTORS THAT ATTAIN THEM.
Proposition prop:res5 (iii) gives Re <psi|X|psi> >= -rho(X) and
|Im <psi|X|psi>| <= rho(X)/2 for every unit psi. On
R5-FAIL-HERMITICITY-DEFECT at psi = (1, i)/sqrt2 the expectation is
1/2 + i/8 exactly -- the arithmetic is
(1/2)[1 * (1/2 + i/4) + (-i) * (i/2)] = (1/2)[1/2 + i/4 + 1/2] = 1/2 + i/8 --
so |Im| = 1/8 = rho/2 EXACTLY: the imaginary bound is TIGHT. On
R5-FAIL-NEGATIVE-EIGENVALUE at psi = (0, 1) the expectation is -1/8 = -rho
EXACTLY: the real bound is TIGHT. A weaker constant in either place would be
visible against these two numbers, which is why they are frozen rather than a
generic vector.

WHICH RESIDUALS EXIST ON WHICH ROUTE. RESIDUAL_ROUTE_PRESENCE freezes the rule
and the ABSENCE: r_2, r_4 and r_5 on all three routes, r_1 and r_3 on routes
(ii) and (iii) only. Definition def:residuals argues it rather than asserting
it: r_1 and r_3 "are written on Gamma and Gamma_Inp, and ROUTE (i) SUPPLIES NO
INSTRUMENT MATRIX ... so r_1 and r_3 are NOT DEFINED and their keys are ABSENT
from validation_results -- ABSENT, NOT ZERO. Emitting 0 would report a check
that was not made, and SYNTHESIZING A Gamma FROM Theorem thm:representation-independence (ii) TO
EVALUATE THEM ON WOULD TEST THE SYNTHESIS RATHER THAN THE DECLARATION."
Theorem thm:exact-and-evaluated (iv) says the same from the numerics side. The two tolerances
that go with them are still declared on route (i) and are simply unused:
"AN UNUSED TOLERANCE IS UNUSED, NOT AN ERROR."
""",
)


# ---------------------------------------------------------------------------
#  Group RP-O -- the tolerance domain and Definition def:tolmap (RC9)
# ---------------------------------------------------------------------------
#
#  Def. def:tolmap fixes, item by item, WHICH DECLARED TOLERANCE DECIDES WHICH
#  EXACT CONDITION, and Section 2.5's `numerical_tolerance_assignment` bullet
#  carries the same list once as a convention. Every case below is read against
#  TOLERANCE_FIXTURE_0_2_0 and states the item it exercises.
#
#  THE CASES COME IN ADMIT/REFUSE PAIRS AT THE DECLARED TOLERANCE, and where
#  the comparison has a side (<=, >=, strict >) the pair sits exactly ON the
#  boundary and exactly one unit beyond it, so that an implementation which got
#  the side or the strictness wrong fails on one of the two.


@dataclass(frozen=True)
class ToleranceDomainCase:
    """One declared tolerance value against the domain [0, 1)."""

    case_id: str
    key: str
    value: F
    admitted: bool
    refusal_reason: str | None
    derives_from: str


TOLERANCE_DOMAIN_CASES: tuple[ToleranceDomainCase, ...] = (
    ToleranceDomainCase(
        case_id="TOL-DOM-ZERO-ADMIT",
        key="eps_5",
        value=F(0),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE CLOSED END. Rem. rem:tolerancedomain writes the domain as "
            "[0, 1), so 0 IS ADMISSIBLE: a declarer who wants a condition "
            "decided EXACTLY declares 0, and every test of Def. def:tolmap "
            "then reduces to the exact one -- lmin(A_k) >= 0, "
            "lmax <= 1, an entry counts as positive when it exceeds 0, "
            "c >= 0. Nothing in the contract prefers a positive value; the "
            "domain is 'A FLOOR, NOT SIZING ADVICE'."
        ),
    ),
    ToleranceDomainCase(
        case_id="TOL-DOM-INTERIOR-ADMIT",
        key="eps_2",
        value=F(1, 1000),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE FIXTURE'S OWN VALUE, admitted. Frozen so that the fixture is "
            "itself checked against the domain it plays the role of declaring: "
            "every member of TOLERANCE_FIXTURE_0_2_0 lies in [0, 1)."
        ),
    ),
    ToleranceDomainCase(
        case_id="TOL-DOM-NEAR-ONE-ADMIT",
        key="eps_gap",
        value=F(999, 1000),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "ADMITTED AND UNWISE, WHICH THE CONTRACT DISTINGUISHES. "
            "Rem. rem:tolerancedomain: 'The domain is A FLOOR, NOT SIZING "
            "ADVICE. Nothing here says a tolerance near 1 is sensible.' At "
            "eps_gap = 999/1000 the gap test is very nearly no constraint -- a "
            "value >= 1 'permits the emitted bound to sit below the attainable "
            "one BY THE WHOLE RANGE OF THE QUANTITY' -- but it is inside the "
            "declared domain and IS NOT REFUSED. Frozen so that an "
            "implementation does not add a sizing rule the contract does not "
            "state."
        ),
    ),
    ToleranceDomainCase(
        case_id="TOL-DOM-ONE-REFUSE",
        key="eps_5",
        value=F(1),
        admitted=False,
        refusal_reason="tolerance_outside_declared_domain",
        derives_from=(
            "THE OPEN END, AND THE SHARPEST CASE IN THIS TUPLE. The domain is "
            "[0, 1) and 1 is NOT IN IT, so a declared eps_5 = 1 is refused with "
            "`tolerance_outside_declared_domain` (Section 2.6). "
            "Rem. rem:tolerancedomain gives the reason test by test: at eps >= 1 "
            "the corresponding test is 'NOT MERELY LOOSE, IT IS VACUOUS OR "
            "DEGENERATE, AND NAMABLY SO' -- Def. def:tolmap (i) 'would admit "
            "every Hermitian family with lmin >= -1'; Eq. eq:eps2rank 'would "
            "return rk = 0 for EVERY port Gram, so the rank check could never "
            "refuse'; (iii) 'would call every declared matrix monotone'; (iv) "
            "'would admit every computed c'; and (v) 'would admit a Gamma of "
            "operator norm sqrt2'. AN IMPLEMENTATION THAT MADE THE DOMAIN "
            "CLOSED AT 1 WOULD ADMIT EXACTLY THIS DECLARATION."
        ),
    ),
    ToleranceDomainCase(
        case_id="TOL-DOM-ABOVE-ONE-REFUSE",
        key="eps_2",
        value=F(3, 2),
        admitted=False,
        refusal_reason="tolerance_outside_declared_domain",
        derives_from=(
            "PLAINLY OUTSIDE. eps_2 = 3/2 refuses. It is frozen beside "
            "TOL-DOM-ONE-REFUSE because the two fail for the same reason and an "
            "implementation that checked only `value > 1` would admit the "
            "endpoint and refuse this one, which is half the rule."
        ),
    ),
    ToleranceDomainCase(
        case_id="TOL-DOM-NEGATIVE-REFUSE",
        key="eps_4",
        value=F(-1, 1000),
        admitted=False,
        refusal_reason="tolerance_outside_declared_domain",
        derives_from=(
            "BELOW THE CLOSED END. A negative tolerance refuses. The domain has "
            "TWO sides and Rem. rem:tolerancedomain states both by writing the "
            "interval; a negative eps_4 would make Def. def:tolmap (iii)'s "
            "entrywise test R_{S|S'} >= -eps_4 STRICTER than the exact "
            "condition R_{S|S'} >= 0, which is not a tolerance at all."
        ),
    ),
)

#: Rem. rem:tolerancedomain's own degeneracy list, frozen as prose so that the
#: reason the domain is bounded above is visible where the cases are.
#: (def:tolmap item, what it would do at eps >= 1)
TOLERANCE_DOMAIN_DEGENERACIES: tuple[tuple[str, str], ...] = (
    ("(i)", "would admit every Hermitian family with lmin >= -1"),
    (
        "(ii)",
        "Eq. eq:eps2rank would return rk_{eps_2}(A_k) = 0 for EVERY port Gram, "
        "so the rank check could never refuse -- the under-reporting direction "
        "of Rem. rem:ranktwosided taken to its limit",
    ),
    ("(iii)", "would call every declared matrix monotone"),
    ("(iv)", "would admit every computed c"),
    ("(v)", "would admit a Gamma of operator norm sqrt2"),
)

#: The two error terms of this amendment that CONSUME the upper bound, named by
#: Rem. rem:tolerancedomain "so that they are not rediscovered".
TOLERANCE_UPPER_BOUND_CONSUMERS: tuple[tuple[str, str], ...] = (
    (
        "rem:cdirection, even n",
        "uses eps_2^n <= eps_2^2 for every even n >= 2, which is exactly eps_2 <= 1",
    ),
    (
        "eq:eps2rank",
        "its justification -- that the spectrum it thresholds is normalized to "
        "[0, 1] -- is an argument about a threshold INSIDE that interval",
    ),
)

#: Def. def:tolmap's five items and the DECLARED tolerance that decides each.
#: Section 2.5 `numerical_tolerance_assignment` carries the same list.
TOLMAP_ITEMS: tuple[tuple[str, str, str], ...] = (
    (
        "(i)",
        "eps_2",
        "route-(i) Gram admissibility: lmin(A_k) >= -eps_2 for every k and "
        "lmax(A_Sigma) <= 1 + eps_2 (Def. def:gram)",
    ),
    (
        "(ii)",
        "eps_2",
        "the route-(i) rank consistency check rk_{eps_2}(A_k) <= |P_k|, by the "
        "eps_2-rank rule Eq. eq:eps2rank",
    ),
    (
        "(iii)",
        "eps_4 and eps_2",
        "dark-channel admissibility for a DECLARED R: (D1) at eps_4, (D2) at "
        "eps_2 (Def. def:darkadm)",
    ),
    (
        "(iv)",
        "eps_2",
        "bound-data admissibility 0 <= c of Eq. eq:bounddata, widened to "
        "c >= -eps_2, with the computed c entering Eq. eq:beta UNCLAMPED",
    ),
    (
        "(v)",
        "eps_1",
        "route-(ii) contractivity Gamma^dagger Gamma <= 1 and the (E1) "
        "predicate of catalogue entry C10, with C10's lossless sub-case decided "
        "TWO-SIDEDLY",
    ),
)

#: Def. def:tolmap's closing paragraph: every OTHER validation is one of three
#: kinds, and none of them adds a threshold. Frozen so that the completeness
#: claim is checkable rather than asserted. (kind, what it covers)
TOLMAP_OTHER_VALIDATION_KINDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "a comparison of declared data against a declared domain",
        (
            "every parameter domain of Table tab:catalogue except C10's",
            "the detector-layer ranges",
            "m_t > N",
            "N >= 0",
            "the tolerance domain itself (Rem. rem:tolerancedomain)",
            "the `tolerance`-field test of Ass. ass:exact",
            "the diagonal non-negativity of Gamma^(t)",
        ),
    ),
    (
        "a combinatorial predicate on the declaration decided by finite inspection",
        (
            "(E2) and (E3) of Def. def:graph",
            "route exclusivity",
            "the port map's disjointness",
            "totality and surjectivity of cg",
            "the single-valued tau of Ass. ass:thresh",
            "the dark-count route exclusivity of Section 2.1",
            "predicate (X) of Def. def:pmc",
        ),
    ),
    (
        "the residual tests themselves, on COMPUTED quantities",
        (
            "r_3 against eps_3",
            "r_4 against eps_4",
            "r_5 against eps_5",
            "the residual gap g_{N,m_t} against eps_gap",
        ),
    ),
)

#: Why r_1 and r_2 are NOT a fourth kind: Def. def:tolmap's closing paragraph
#: (c). By Eq. eq:r1islmax the test r_1 <= eps_1 IS item (v), and
#: r_2 <= eps_2 is the positivity half of item (i) written as a residual.
TOLMAP_RESIDUALS_ALREADY_COUNTED: tuple[tuple[str, str], ...] = (
    ("r_1", "item (v), by the identity Eq. eq:r1islmax"),
    ("r_2", "the positivity half of item (i), written as a residual"),
)


@dataclass(frozen=True)
class TolmapCase:
    """One admit/refuse decision at a declared tolerance (Def. def:tolmap)."""

    case_id: str
    item: str
    tolerance_key: str
    #: The quantity the test compares, named as the contract writes it.
    quantity: str
    #: Its exact value on the frozen data.
    value: F
    #: The threshold the test compares it against, exactly.
    threshold: F
    admitted: bool
    #: The verbatim reason where the contract spells one; else None.
    refusal_reason: str | None
    derives_from: str


TOLMAP_I_CASES: tuple[TolmapCase, ...] = (
    TolmapCase(
        case_id="TOLMAP-I-LMIN-BOUNDARY-ADMIT",
        item="(i)",
        tolerance_key="eps_2",
        quantity="lmin(A_1)",
        value=F(-1, 1000),
        threshold=F(-1, 1000),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "A DECLARED route-(i) family A_1 = diag(1/2, -1/1000), "
            "A_2 = diag(1/4, 0). Def. def:tolmap (i) admits when "
            "lmin(A_k) >= -eps_2 for every k. Here lmin(A_1) = -1/1000 = -eps_2 "
            "EXACTLY, so the family is ADMITTED: the comparison is >=, not >. "
            "lmin(A_2) = 0 >= -eps_2. A_Sigma = diag(3/4, -1/1000) has "
            "lmax = 3/4 <= 1 + eps_2. THE RESIDUAL SIDE AGREES BY "
            "CONSTRUCTION: Eq. eq:res2 gives "
            "r_2 = max_k max{0, -lmin(A_k)} = 1/1000 = eps_2, and "
            "r_2 <= eps_2 passes. That is the point of item (i)'s closing "
            "sentence -- 'THE SAME DECLARED NUMBER BOUNDS THE RESIDUAL AND "
            "DECIDES THE ADMISSION, IN THE SAME UNITS' -- and it is why no "
            "separate tolerance is added for admissibility."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-I-LMIN-REFUSE",
        item="(i)",
        tolerance_key="eps_2",
        quantity="lmin(A_1)",
        value=F(-1, 500),
        threshold=F(-1, 1000),
        admitted=False,
        refusal_reason=None,
        derives_from=(
            "THE SAME FAMILY WITH A_1 = diag(1/2, -1/500). "
            "lmin(A_1) = -1/500 < -1/1000 = -eps_2, so the family is REFUSED. "
            "Eq. eq:res2 gives r_2 = 1/500 > eps_2 and refuses too: ONE TEST, "
            "ONE VERDICT. contract.tex SPELLS NO REASON STRING for a Gram "
            "admissibility failure, so none is frozen; what is frozen is the "
            "failing CONDITION and the number that decided it."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-I-LMAX-BOUNDARY-ADMIT",
        item="(i)",
        tolerance_key="eps_2",
        quantity="lmax(A_Sigma)",
        value=F(1001, 1000),
        threshold=F(1001, 1000),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "A DECLARED family A_1 = diag(1001/1000, 0), A_2 = diag(0, 0), for "
            "which lmax(A_Sigma) = 1001/1000 = 1 + eps_2 EXACTLY. "
            "Def. def:tolmap (i) admits when lmax(A_Sigma) <= 1 + eps_2, so "
            "this is admitted AT the boundary. The exact condition "
            "sum_k A_k <= 1 EXCLUDES it, and that is deliberate: the same "
            "argument item (iv) gives for c, 'a lossless receiver has "
            "lmax(B) = 1 exactly, so a computed lmax one rounding unit above 1 "
            "makes c negative ON A RECEIVER THAT IS ADMISSIBLE; refusing it "
            "would refuse the simplest legitimate device'. lmin(A_1) = 0 and "
            "lmin(A_2) = 0, so the positivity half passes exactly."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-I-LMAX-REFUSE",
        item="(i)",
        tolerance_key="eps_2",
        quantity="lmax(A_Sigma)",
        value=F(501, 500),
        threshold=F(1001, 1000),
        admitted=False,
        refusal_reason=None,
        derives_from=(
            "THE SAME family with A_1 = diag(501/500, 0). "
            "lmax(A_Sigma) = 501/500 = 1002/1000 > 1001/1000 = 1 + eps_2, so it "
            "is REFUSED -- by ONE PART IN A THOUSAND past the boundary the "
            "previous case sits on. The pair is frozen so that an "
            "implementation using < in place of <= fails on "
            "TOLMAP-I-LMAX-BOUNDARY-ADMIT and one using 1 + 2 eps_2 fails "
            "here."
        ),
    ),
)

TOLMAP_II_RANK_CASES: tuple[TolmapCase, ...] = (
    TolmapCase(
        case_id="TOLMAP-II-RANK-EXACT-ONE-ADMIT",
        item="(ii)",
        tolerance_key="eps_2",
        quantity="rk_{eps_2}(A_1)",
        value=F(1),
        threshold=F(1),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "A DECLARED A_1 = diag(1/2, 0) on a SINGLE-MODE port, |P_1| = 1. "
            "Eq. eq:eps2rank counts the eigenvalues of (A_1 + A_1^dagger)/2 = "
            "A_1 that EXCEED eps_2: 1/2 > 1/1000 counts, 0 does not, so "
            "rk_{eps_2}(A_1) = 1 <= 1 and the declaration is ADMITTED. The "
            "exact rank is also 1, so the count and the rank agree here; the "
            "next three cases are where they do not."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-II-RANK-BOUNDARY-NOT-COUNTED-ADMIT",
        item="(ii)",
        tolerance_key="eps_2",
        quantity="rk_{eps_2}(A_1)",
        value=F(1),
        threshold=F(1),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "A DECLARED A_1 = diag(1/2, 1/1000) on a single-mode port. The "
            "second eigenvalue is EXACTLY eps_2, and Eq. eq:eps2rank counts "
            "eigenvalues that are STRICTLY GREATER than eps_2 -- the contract "
            "writes '> eps_2' -- so it is NOT counted, rk_{eps_2}(A_1) = 1, and "
            "the declaration is ADMITTED. THE STRICTNESS IS THE WHOLE OF THIS "
            "CASE: an implementation using >= here reports rank 2 and refuses a "
            "declaration the contract admits. Item (ii)'s own argument turns on "
            "the same edge: a Gram admitted by item (i) 'has its "
            "numerically-zero eigenvalues in [-eps_2, eps_2] and the two "
            "thresholds CANNOT DISAGREE ABOUT WHICH THEY ARE'."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-II-RANK-UNDER-REPORTED-ADMIT",
        item="(ii)",
        tolerance_key="eps_2",
        quantity="rk_{eps_2}(A_1)",
        value=F(1),
        threshold=F(1),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE UNDER-REPORTING DIRECTION OF Rem. rem:ranktwosided, FROZEN AS "
            "AN ADMISSION RATHER THAN AS A REFUSAL, because that is what makes "
            "the cutoff two-sided. A DECLARED A_1 = diag(1/2, 1/2000) on a "
            "single-mode port has EXACT RANK 2, but 1/2000 < 1/1000 = eps_2 is "
            "not counted, so rk_{eps_2}(A_1) = 1 <= 1 AND THE DECLARATION IS "
            "ADMITTED. Rem. rem:ranktwosided states exactly this: 'A Gram whose "
            "exact rank is 2 but whose second eigenvalue is genuinely small, "
            "below tau, is counted as rank 1, AND A DECLARATION INCONSISTENT "
            "WITH ITS PORT MAP IS ADMITTED ON A SINGLE-MODE PORT. So the check "
            "is NOT REFUSE-ONLY, and the choice of tau is a choice about which "
            "declarations are accepted, NOT A NUMERICAL DETAIL.' The contract "
            "does not repair this -- 'no threshold can remove them' -- it makes "
            "both directions consequences of a DECLARED number: 'the rank the "
            "check used is a function of {A_k} and eps_2 ALONE.'"
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-II-RANK-OVER-REPORTED-REFUSE",
        item="(ii)",
        tolerance_key="eps_2",
        quantity="rk_{eps_2}(A_1)",
        value=F(2),
        threshold=F(1),
        admitted=False,
        refusal_reason="port_gram_rank_exceeds_port_size",
        derives_from=(
            "THE OVER-REPORTING DIRECTION, AND THE REFUSAL Section 2.6 SPELLS. "
            "A DECLARED A_1 = diag(1/2, 1/500) on a single-mode port: "
            "1/500 = 2 eps_2 > eps_2 counts, so rk_{eps_2}(A_1) = 2 > 1 = "
            "|P_1| and the request is REFUSED with "
            "`port_gram_rank_exceeds_port_size`. Rem. rem:ranktwosided's "
            "over-reported case is exactly this shape: 'An exactly singular "
            "declared Gram whose zero eigenvalue evaluates at +2 tau -- "
            "rounding noise in the declared entries, or in the eigenvalue "
            "routine -- is counted as one rank higher, and A DECLARATION "
            "CONSISTENT WITH ITS PORT MAP IS REFUSED.' The threshold is "
            "ABSOLUTE and it is eps_2: a RELATIVE cutoff would make the "
            "decision at a nearly dark port 'A MILLION TIMES TIGHTER than at a "
            "lossless one, WHICH IS A PROPERTY OF THE PORT'S THROUGHPUT AND NOT "
            "OF THE DECLARER'S NUMERICS', and the usual library default "
            "lmax * max(D_1, D_2) * eps_mach is 'RELATIVE, UNDECLARED, AND "
            "INVISIBLE IN THE ARTIFACT'."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-II-RANK-TWO-MODE-PORT-ADMIT",
        item="(ii)",
        tolerance_key="eps_2",
        quantity="rk_{eps_2}(A_1)",
        value=F(2),
        threshold=F(2),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE SAME DECLARED A_1 = diag(1/2, 1/500) ON A TWO-MODE PORT, "
            "|P_1| = 2: rk_{eps_2}(A_1) = 2 <= 2 and it is ADMITTED. Frozen "
            "beside the previous case because THE GRAM IS IDENTICAL AND ONLY "
            "THE PORT MAP DIFFERS -- the check is a CONSISTENCY check between "
            "two declared objects, not a property of the Gram. Rem. rem:rankone "
            "makes the same point from the other side: a port that collects "
            "several modes 'simply has rk A_k > 1', and the rank-one branch is "
            "'A CERTIFIED BRANCH, NEVER A DEFAULT'."
        ),
    ),
)

TOLMAP_IV_C_CASES: tuple[TolmapCase, ...] = (
    TolmapCase(
        case_id="TOLMAP-IV-C-ZERO-ADMIT",
        item="(iv)",
        tolerance_key="eps_2",
        quantity="c = 1 - lmax(B)",
        value=F(0),
        threshold=F(0),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE LOSSLESS RECEIVER, WHERE lmax(B) = 1 EXACTLY and c = 0. This "
            "is the case item (iv)'s widening exists for: 'a lossless receiver "
            "has lmax(B) = 1 exactly, so A COMPUTED lmax(B) ONE ROUNDING UNIT "
            "ABOVE 1 MAKES c NEGATIVE ON A RECEIVER THAT IS ADMISSIBLE; "
            "refusing it would refuse the simplest legitimate device.' Frozen "
            "as the anchor of the pair below. The BB84 receiver of "
            "Ex. ex:bb84bound is such a receiver: A_Sigma = 1 gives c = 0."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-IV-C-BOUNDARY-ADMIT",
        item="(iv)",
        tolerance_key="eps_2",
        quantity="c = 1 - lmax(B)",
        value=F(-1, 1000),
        threshold=F(-1, 1000),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "A COMPUTED lmax(B) = 1001/1000, so c = -1/1000 = -eps_2 EXACTLY. "
            "Def. def:tolmap (iv) admits when c >= -eps_2, so this is ADMITTED "
            "-- AND THE VALUE IS NOT CLAMPED. 'NOTHING IS CLAMPED: the computed "
            "c enters Eq. eq:beta EXACTLY AS IT STANDS.' What that costs is "
            "Rem. rem:cdirection, frozen as C_DIRECTION_CASES, and it is stated "
            "on BOTH sides. The contrast with the deferred interval pipeline is "
            "explicit in Rem. rem:ia and matters here: there the enclosure of c "
            "IS taken in [0, 1], soundly, 'because c_ex in [0, 1] is A "
            "THEOREM', whereas here 'no enclosure exists, the computed c is not "
            "known to bound c_ex on either side, and CLAMPING IT TO 0 WOULD "
            "ASSERT A RELATION TO THE EXACT VALUE THAT NOTHING SUPPORTS'."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-IV-C-REFUSE",
        item="(iv)",
        tolerance_key="eps_2",
        quantity="c = 1 - lmax(B)",
        value=F(-1, 500),
        threshold=F(-1, 1000),
        admitted=False,
        refusal_reason=None,
        derives_from=(
            "A COMPUTED lmax(B) = 501/500, so c = -1/500 < -eps_2 and the bound "
            "data are REFUSED. The remaining inequalities of Eq. eq:bounddata "
            "-- gamma <= beta_k <= 1 and c <= d_k <= 1 -- are NOT separately "
            "tested and NO THRESHOLD DECIDES THEM: 'they are REDUNDANT BY "
            "THEOREM, discharged by the admissibility paragraph of Theorem "
            "thm:multiclick-bound from Eq. eq:bbkhyp and Theorem thm:gaussian-schur (iv), "
            "and their floating-point evaluation is governed by Theorem "
            "thm:exact-and-evaluated (ii) like every other computed quantity.' So this is the "
            "ONLY threshold decision item (iv) makes."
        ),
    ),
)

#: Rem. rem:cdirection: the direction of the UNCLAMPED c, on BOTH sides, at the
#: boundary value c = -eps_2 that TOLMAP-IV-C-BOUNDARY-ADMIT admits. The data
#: are K = 2, gamma = 1, beta_k = 1, d_k = 1/2, so
#: beta(n) = 1 + c^n - 2 (1/2)^n. THESE ARE NOT ADMISSIBLE BOUND DATA in the
#: sense of Eq. eq:bounddata -- c < 0 -- and that is the point: they are what a
#: floating-point evaluation ADMITS under item (iv) and feeds to Eq. eq:beta
#: unchanged.
#: (n, parity, beta(n) at c = -eps_2, beta(n) at c = 0, signed difference
#:  evaluated minus at-zero, the magnitude (K-1) gamma |c|^n that
#:  Rem. rem:cdirection identifies that difference with)
C_DIRECTION_CASES: tuple[tuple[int, str, F, F, F, F], ...] = (
    (1, "odd", F(-1, 1000), F(0), F(-1, 1000), F(1, 1000)),
    (
        2,
        "even",
        F(500001, 1000000),
        F(1, 2),
        F(1, 1000000),
        F(1, 1000000),
    ),
    (
        3,
        "odd",
        F(749999999, 1000000000),
        F(3, 4),
        F(-1, 1000000000),
        F(1, 1000000000),
    ),
    (
        4,
        "even",
        F(875000000001, 1000000000000),
        F(7, 8),
        F(1, 1000000000000),
        F(1, 1000000000000),
    ),
)

#: The two bounds Rem. rem:cdirection states, at K = 2 and eps_2 = 1/1000, so
#: that the parity split is checkable as a number and not only as a direction.
#: ODD: the deficit against the value at c = 0 is (K-1) gamma |c|^n, and at
#: n = 1 that is at most (K-1) eps_2 -- ATTAINED at these data.
#: EVEN: the excess is at most (K-1) eps_2^2 -- ATTAINED at n = 2.
C_DIRECTION_BOUNDS: tuple[tuple[str, F, str], ...] = (
    (
        "odd n, conservative (below)",
        F(1, 1000),
        "(K-1) eps_2 at n = 1, with K = 2 and eps_2 = 1/1000; the frozen "
        "deficit at n = 1 is 1/1000, so the bound is ATTAINED",
    ),
    (
        "even n >= 2, can exceed (above)",
        F(1, 1000000),
        "(K-1) eps_2^2, using gamma <= 1, |c| <= eps_2 and eps_2 <= 1 -- the "
        "last step being where the declared upper bound of "
        "Rem. rem:tolerancedomain is consumed, 'since eps_2^n <= eps_2^2 for "
        "even n >= 2 holds exactly on eps_2 <= 1 AND FAILS ABOVE IT'; the "
        "frozen excess at n = 2 is 1/1000000, so the bound is ATTAINED",
    ),
)

TOLMAP_V_CONTRACTIVITY_CASES: tuple[TolmapCase, ...] = (
    TolmapCase(
        case_id="TOLMAP-V-BB84-UNITARY-ADMIT",
        item="(v)",
        tolerance_key="eps_1",
        quantity="lmax(Gamma^dagger Gamma)",
        value=F(1),
        threshold=F(1001, 1000),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE WORKED INSTRUMENT Eq. eq:bb84G, frozen as instrument case "
            "I-BB84 at p_Z = p_X = 1/2, WHICH IS EXACTLY UNITARY. "
            "Example ex:bb84 checks it: 'each column has squared norm "
            "p_Z + 2 (p_X / 2) = 1 or p_X + 2 (p_Z / 2) = 1, and the six "
            "pairwise inner products vanish'. So Gamma_Inp^dagger Gamma_Inp = 1 "
            "and lmax = 1 <= 1 + eps_1: ADMITTED.\n"
            "AND THE IDENTITY Eq. eq:r1islmax HOLDS EXACTLY HERE: "
            "r_1 = ||(Gamma^dagger Gamma - 1)_+|| = ||0_+|| = 0, and "
            "(lmax - 1)_+ = (1 - 1)_+ = 0. The two are the same number, which "
            "is what item (v) means by 'not merely the analogue of the dual "
            "role eps_2 plays at (i) but LITERALLY THE SAME TEST'. "
            "Def. def:tolmap (v) names this receiver for the same reason: "
            "'a lossless receiver has lmax(Gamma^dagger Gamma) = 1 EXACTLY -- "
            "the worked instrument Eq. eq:bb84G is unitary -- so a computed "
            "value one rounding unit above 1 would refuse it'."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-V-ADMITTED-ABOVE-ONE",
        item="(v)",
        tolerance_key="eps_1",
        quantity="lmax(Gamma^dagger Gamma)",
        value=F(16008001, 16000000),
        threshold=F(1001, 1000),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "A DECLARED Gamma = diag(4001/4000, 0), WHICH IS NOT A CONTRACTION "
            "AND IS ADMITTED ANYWAY. Gamma^dagger Gamma = "
            "diag((4001/4000)^2, 0) = diag(16008001/16000000, 0), so "
            "lmax = 16008001/16000000. The threshold is "
            "1 + eps_1 = 1001/1000 = 16016000/16000000, and "
            "16008001 <= 16016000, so it is ADMITTED.\n"
            "THIS IS THE ONE-SIDED CLAUSE OF ITEM (v) MADE CONCRETE: "
            "'the test relaxes in ONE DIRECTION ONLY: IT ADMITS "
            "lmax(Gamma^dagger Gamma) in (1, 1 + eps_1], WHICH THE EXACT "
            "CONDITION EXCLUDES, and it refuses nothing that the exact "
            "condition, applied to the same computed number, would admit.' "
            "Eq. eq:r1islmax gives r_1 = (lmax - 1)_+ = 8001/16000000, and "
            "eps_1 = 16000/16000000, so r_1 <= eps_1 PASSES -- the same "
            "verdict from the residual side.\n"
            "WHAT THE SLACK COSTS IS TRANSPORTED, NOT LOST: 'route (ii) "
            "carries NO separate Gram admissibility check, because Theorem "
            "thm:port-grams (i) DERIVES sum_k A_k <= Gamma_Inp^dagger Gamma_Inp <= 1 "
            "from contractivity, so an admitted Gamma yields "
            "lmax(A_Sigma) <= 1 + eps_1' -- which is the route-(ii) counterpart "
            "of what item (i) admits at eps_2, 'and it is what reaches "
            "B <= 1 in Eq. eq:bbkhyp and c = 1 - lmax(B) in item (iv)'."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-V-REFUSE-JUST-ABOVE",
        item="(v)",
        tolerance_key="eps_1",
        quantity="lmax(Gamma^dagger Gamma)",
        value=F(4004001, 4000000),
        threshold=F(1001, 1000),
        admitted=False,
        refusal_reason=None,
        derives_from=(
            "A DECLARED Gamma = diag(2001/2000, 0), REFUSED BY ONE PART IN FOUR "
            "MILLION. Gamma^dagger Gamma = diag((2001/2000)^2, 0) = "
            "diag(4004001/4000000, 0), and the threshold is "
            "1 + eps_1 = 1001/1000 = 4004000/4000000. Since "
            "4004001 > 4004000 the matrix is REFUSED.\n"
            "THE RESIDUAL SIDE AGREES AT THE SAME MARGIN: "
            "r_1 = (lmax - 1)_+ = 4001/4000000 against "
            "eps_1 = 1/1000 = 4000/4000000, so r_1 > eps_1 by ONE PART IN FOUR "
            "MILLION as well. FROZEN AT THIS SEPARATION DELIBERATELY: it is the "
            "sharpest available check that Eq. eq:r1islmax is an IDENTITY and "
            "not an approximation -- an implementation whose two tests "
            "disagreed anywhere would disagree here."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-V-C10-E1-REFUSE",
        item="(v)",
        tolerance_key="eps_1",
        quantity="lmax(Gamma_Sigma^dagger Gamma_Sigma)",
        value=F(4),
        threshold=F(1001, 1000),
        admitted=False,
        refusal_reason=None,
        derives_from=(
            "CATALOGUE ENTRY C10 WITH THE SUPPLIED BLOCK diag(2, 0), the same "
            "block refusal case REF-C10-NOT-A-CONTRACTION freezes -- now WITH "
            "THE DECLARED TOLERANCE THAT DECIDES IT. "
            "Gamma_Sigma^dagger Gamma_Sigma = diag(4, 0), lmax = 4, and "
            "4 > 1 + eps_1, so (E1) fails. Item (v): 'The same test, on the "
            "supplied block Gamma_Sigma, decides the (E1) predicate of "
            "catalogue entry C10 -- THE ONE ENTRY WHOSE (E1) IS A SPECTRAL "
            "CONDITION rather than a parameter-domain comparison, and the one "
            "Theorem thm:compilation-well-defined (iv) names as NOT REDUNDANT BY THEOREM.'"
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-V-C10-LOSSLESS-ADMIT",
        item="(v)",
        tolerance_key="eps_1",
        quantity="||Gamma_Sigma^dagger Gamma_Sigma - 1||",
        value=F(8001, 16000000),
        threshold=F(1, 1000),
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "C10'S LOSSLESS SUB-CASE, DECIDED TWO-SIDEDLY. Item (v): 'C10's "
            "lossless sub-case Gamma_Sigma^dagger Gamma_Sigma = 1 is an "
            "EQUALITY and is decided TWO-SIDEDLY, as "
            "||Gamma_Sigma^dagger Gamma_Sigma - 1|| <= eps_1.' On the supplied "
            "block Gamma_Sigma = diag(4001/4000, 1) the difference is "
            "diag(8001/16000000, 0), whose spectral norm is 8001/16000000; "
            "against eps_1 = 16000/16000000 that PASSES, so the element is "
            "declared LOSSLESS. Note that the same block is a contraction only "
            "under the widened test of the previous cases -- it is admitted at "
            "eps_1 and is not exactly a contraction -- which is consistent: the "
            "lossless sub-case is a STRONGER statement decided by the SAME "
            "declared number."
        ),
    ),
    TolmapCase(
        case_id="TOLMAP-V-C10-NOT-LOSSLESS",
        item="(v)",
        tolerance_key="eps_1",
        quantity="||Gamma_Sigma^dagger Gamma_Sigma - 1||",
        value=F(3, 4),
        threshold=F(1, 1000),
        admitted=False,
        refusal_reason=None,
        derives_from=(
            "A C10 BLOCK THAT IS A CONTRACTION AND IS NOT LOSSLESS, which is "
            "the case that shows the two tests are different. "
            "Gamma_Sigma = diag(1/2, 1): "
            "Gamma_Sigma^dagger Gamma_Sigma = diag(1/4, 1), so "
            "lmax = 1 <= 1 + eps_1 and the element IS ADMITTED AS A "
            "CONTRACTION; but Gamma_Sigma^dagger Gamma_Sigma - 1 = "
            "diag(-3/4, 0) has spectral norm 3/4 > eps_1, so it is NOT "
            "declared lossless. `admitted` reads False for the LOSSLESS "
            "verdict, which is what `quantity` names; the element itself "
            "passes (E1). THE TWO-SIDEDNESS IS LOAD-BEARING: a one-sided test "
            "lmax <= 1 + eps_1 would have called this block lossless."
        ),
    ),
)


O_RP_TOLMAP = RPOracleEntry(
    oracle_id="O-RP-TOLMAP",
    claims=("RC9",),
    kind="fail-closed",
    subject=(
        "The declared tolerance domain [0, 1) with its two endpoints and its "
        "verbatim refusal; and Definition def:tolmap item by item -- route-(i) "
        "Gram admissibility and the eps_2-rank rule at eps_2 with both "
        "directions of its two-sided cutoff, dark-channel (D1) at eps_4 and "
        "(D2) at eps_2, the unclamped c at eps_2 with both parities of its "
        "direction, and route-(ii) contractivity and C10's (E1) at eps_1 with "
        "the identity eq:r1islmax."
    ),
    derivation="""\
Definition def:tolmap, Remark rem:tolerancedomain, Remark rem:ranktwosided,
Remark rem:cdirection, Equations eq:eps2rank and eq:r1islmax, and Section 2.5's
`numerical_tolerance_assignment` bullet, which carries the same list once as a
convention.

WHAT THE AMENDMENT ADDED HERE. 0.1.3 stated the exact conditions and left the
threshold that decides each of them unstated, which meant a library default
could decide one -- and Remark rem:ranktwosided is the argument that a rank
cutoff is exactly the wrong thing to leave to one, because it is TWO-SIDED and
'the difference is NOT FAIL-CLOSED IN EITHER' direction. 0.2.0 fixes five
assignments and claims they are the complete set. TOLMAP_ITEMS freezes the five;
TOLMAP_OTHER_VALIDATION_KINDS freezes the three kinds the closing paragraph
enumerates so that the completeness claim is CHECKABLE rather than asserted; and
TOLMAP_RESIDUALS_ALREADY_COUNTED freezes why r_1 and r_2 are not a fourth kind.

EVERY PAIR SITS ON THE BOUNDARY. The admit case of each pair is at the exact
threshold and the refuse case is one declared unit past it, so a wrong side
(< for <=), a wrong strictness (>= for >) or a doubled threshold each fails one
half of a pair. Item (ii) is the extreme case, at TOLMAP-II-RANK-BOUNDARY-
NOT-COUNTED-ADMIT: Eq. eq:eps2rank counts eigenvalues STRICTLY above eps_2, and
an implementation using >= refuses a declaration the contract admits.

THE RANK CUTOFF IS FROZEN IN BOTH DIRECTIONS, WHICH IS THE POINT OF FIXING IT.
TOLMAP-II-RANK-UNDER-REPORTED-ADMIT is a Gram of exact rank 2 ADMITTED on a
single-mode port, and TOLMAP-II-RANK-OVER-REPORTED-REFUSE is the shape
Remark rem:ranktwosided describes as a consistent declaration refused. Both are
consequences of a DECLARED number and both are recorded in the artifact: 'the
rank the check used is a function of {A_k} and eps_2 ALONE'. The refusal is one
of the five Section 2.6 spells: `port_gram_rank_exceeds_port_size`.

NOTHING IS CLAMPED, AND THE ONE EXEMPTION IS NAMED. Item (iv) admits
c in [-eps_2, 0) and feeds it to Eq. eq:beta unchanged; C_DIRECTION_CASES
freezes what that does at n = 1, 2, 3, 4, and the two bounds of
Remark rem:cdirection are ATTAINED at n = 1 and n = 2 on these data -- the
odd-n deficit is exactly (K-1) eps_2 = 1/1000 and the even-n excess is exactly
(K-1) eps_2^2 = 1/1000000. The even-n estimate is one of the two places the
DECLARED UPPER BOUND of the tolerance domain is consumed, since
eps_2^n <= eps_2^2 for even n >= 2 'holds exactly on eps_2 <= 1 AND FAILS ABOVE
IT'. The one place a declared tolerance changes a COEFFICIENT rather than a
decision is Eq. eq:rbar, and it is frozen in DARK_SLACK_CASES, not here.

eps_1 CARRIES THE SAME DUAL ROLE AT ROUTE (ii) THAT eps_2 CARRIES AT ROUTE (i),
and Eq. eq:r1islmax makes that an IDENTITY rather than an analogy:
r_1 = ||(Gamma^dagger Gamma - 1)_+|| = (lmax(Gamma^dagger Gamma) - 1)_+,
because Gamma^dagger Gamma is Hermitian positive semidefinite and the positive
part has eigenvalues (lambda_i - 1)_+. Every contractivity case above freezes
BOTH numbers, and TOLMAP-V-REFUSE-JUST-ABOVE freezes them at a separation of one
part in four million, where an implementation whose two tests disagreed anywhere
would disagree. The two routes admit the same object under two different
declared numbers, and the contract says what a declarer does about that: 'A
declarer who wants one slack on lmax(A_Sigma) regardless of route declares
eps_1 = eps_2.'

THE DOMAIN IS HALF-OPEN AND BOTH ENDS ARE FROZEN. TOL-DOM-ZERO-ADMIT is the
closed end -- a declarer who wants an exact decision declares 0 -- and
TOL-DOM-ONE-REFUSE is the open one, refused with
`tolerance_outside_declared_domain`. TOLERANCE_DOMAIN_DEGENERACIES carries
Remark rem:tolerancedomain's item-by-item account of what each test would do at
eps >= 1, which is why the bound exists; TOLERANCE_UPPER_BOUND_CONSUMERS names
the two error terms of this amendment that actually use it. And
TOL-DOM-NEAR-ONE-ADMIT is frozen to keep the two apart: a tolerance near 1 is
unwise and IS NOT REFUSED, because 'the domain is A FLOOR, NOT SIZING ADVICE'.
""",
)


# ---------------------------------------------------------------------------
#  Group RP-P -- the dark-count slack: rbar, delta_dc and eq:darkpmcslack
#                (RC11 through Def. def:tolmap (iii) and Rem. rem:d2slack)
# ---------------------------------------------------------------------------
#
#  What the artifact emits at 0.2.0 is R, r_min AS Eq. eq:rmin COMPUTES IT, the
#  capped coefficient rbar = min{r_min, 1} of Eq. eq:rbar, and the composition
#  correction delta_dc of Eq. eq:darkdelta -- FOUR OBJECTS UNDER DISTINCT
#  NAMES -- and the inequality a consumer composes with is Eq. eq:darkpmcslack,
#  NOT Eq. eq:darkpmc.
#
#  Eq. eq:darkdelta:  delta_dc = 0                        (generated route)
#                     delta_dc = eps_4 + (K + 1) eps_2    (declared route)
#  Eq. eq:rbar:       rbar = min{r_min, 1}
#  Eq. eq:darkpmcslack:
#      blk Mtilde^{(>N)}_{MC} >= ((1 - rbar) p_mc + rbar - delta_dc) id^{(>N)}
#  Eq. eq:darkpmc (the EXACTLY-admissible form, kept for comparison):
#      blk Mtilde^{(>N)}_{MC} >= ((1 - r_min) p_mc + r_min) id^{(>N)}
#  Eq. eq:darkoverstate (what using the latter costs):
#      (r_min - rbar)(1 - p_mc) + delta_dc
#
#  EVERY CASE BELOW IS READ AGAINST TOLERANCE_FIXTURE_0_2_0, and the delta_dc
#  of a declared case is a function of THE DECLARED TOLERANCES AND K ALONE --
#  not of how much slack the channel actually used. The witness channel of
#  Rem. rem:d2slack, for instance, occupies no (D2)-forbidden position at all
#  and is admitted at eps_2 = 0, yet its delta_dc still carries the
#  (K + 1) eps_2 term of the declaration it arrived under.


@dataclass(frozen=True)
class DarkSlackCase:
    """One dark-count channel with its emitted scalars and its composition."""

    case_id: str
    port_count: int
    #: "generated" (the product form Eq. eq:darkR) or "declared".
    route: str
    #: (column S', ((row S, entry), ...)) with S, S' sorted port-index tuples.
    #: Only NON-ZERO entries are frozen.
    columns: tuple[tuple[tuple[int, ...], tuple[tuple[tuple[int, ...], F], ...]], ...]
    #: R_{MC|S'} per column.
    mc_mass: tuple[tuple[tuple[int, ...], F], ...]
    #: (D1) and (D2) at the declared tolerances; THEOREMS on the generated route.
    d1_admitted: bool
    d2_admitted: bool
    admitted: bool
    #: The failing condition where the channel refuses; else None. No reason
    #: string: contract.tex spells none for a (D1) or (D2) failure.
    failing_condition: str | None
    #: Eq. eq:rmin, EMITTED UNMODIFIED. None where the channel is refused.
    r_min: F | None
    #: Eq. eq:rbar. None where the channel is refused.
    r_bar: F | None
    #: Eq. eq:darkdelta. None where the channel is refused.
    delta_dc: F | None
    #: Eq. eq:rminupper, the upper bound on any column's multiclick mass.
    r_min_upper_bound: F | None
    #: Eq. eq:rbarcost: 0 <= r_min - rbar <= (K + 2) eps_4.
    r_bar_cost: F | None
    r_bar_cost_bound: F | None
    #: The bare pre-dark-count bound the composition is applied to.
    p_mc: F | None
    #: Eq. eq:darkpmcslack, the coefficient a consumer composes with.
    composed_slack: F | None
    #: Eq. eq:darkpmc, the exactly-admissible form, FOR COMPARISON ONLY.
    composed_exact_form: F | None
    #: Eq. eq:darkoverstate, the difference between the two.
    overstatement: F | None
    #: Whether Eq. eq:darkpmcslack improves on p_mc: rbar (1 - p_mc) >= delta_dc.
    improves_on_p_mc: bool | None
    derives_from: str


DARK_SLACK_CASES: tuple[DarkSlackCase, ...] = (
    DarkSlackCase(
        case_id="DS-GENERATED-K2",
        port_count=2,
        route="generated",
        columns=(
            (
                (),
                (
                    ((), F(18, 25)),
                    ((0,), F(2, 25)),
                    ((1,), F(9, 50)),
                    ((0, 1), F(1, 50)),
                ),
            ),
            ((0,), (((0,), F(4, 5)), ((0, 1), F(1, 5)))),
            ((1,), (((1,), F(9, 10)), ((0, 1), F(1, 10)))),
            ((0, 1), (((0, 1), F(1)),)),
        ),
        mc_mass=(
            ((), F(1, 50)),
            ((0,), F(1, 5)),
            ((1,), F(1, 10)),
            ((0, 1), F(1)),
        ),
        d1_admitted=True,
        d2_admitted=True,
        admitted=True,
        failing_condition=None,
        r_min=F(1, 50),
        r_bar=F(1, 50),
        delta_dc=F(0),
        r_min_upper_bound=F(1),
        r_bar_cost=F(0),
        r_bar_cost_bound=F(1, 250),
        p_mc=F(1, 2),
        composed_slack=F(51, 100),
        composed_exact_form=F(51, 100),
        overstatement=F(0),
        improves_on_p_mc=True,
        derives_from=(
            "DARK-K2 -- the per-port product form Eq. eq:darkR at K = 2 with "
            "p_dc = (1/10, 1/5) -- CARRIED FORWARD UNCHANGED and given its "
            "0.2.0 scalars. THE MATRIX AND r_min ARE THE 0.1.3 VALUES: "
            "r_min = min{1/50, 1/5, 1/10} = 1/50, the minimum running over "
            "EVERY non-multiclick column with the no-click column included "
            "(Rem. rem:rmintrap).\n"
            "ON THE GENERATED ROUTE THERE IS NO SLACK TO CARRY, and "
            "Eq. eq:darkdelta says so by cases: (D1) and (D2) are THEOREMS "
            "here (Theorem thm:dark-counts (i)) and not tests, 'so there is no slack "
            "to carry and the correction is EXACTLY 0'. delta_dc = 0.\n"
            "r_min <= 1 FOR FREE, and the contract gives the one-line reason: "
            "'entries are non-negative and columns sum to 1, so "
            "R_{MC|S'} <= sum_S R_{S|S'} = 1'. Hence "
            "rbar = min{1/50, 1} = 1/50 = r_min, and Eq. eq:rbarcost's "
            "cost r_min - rbar is 0 (the bound (K + 2) eps_4 = 4/1000 = 1/250 "
            "is not binding).\n"
            "THE COMPOSITION COINCIDES WITH THE 0.1.3 FORM, WHICH IS THE POINT: "
            "at p_mc = 1/2, Eq. eq:darkpmcslack gives "
            "(1 - 1/50)(1/2) + 1/50 - 0 = 49/100 + 2/100 = 51/100, and "
            "Eq. eq:darkpmc gives the same 51/100 -- the value frozen at 0.1.3 "
            "as DARK_IMPROVEMENT_CASES row IMP-K2-HALF. 'On the generated route "
            "delta_dc = 0 and r_min <= 1, so rbar = r_min and "
            "Eq. eq:darkpmcslack IS Eq. eq:darkpmc.' Eq. eq:darkoverstate is "
            "therefore 0.\n"
            "IT IMPROVES: rbar (1 - p_mc) = (1/50)(1/2) = 1/100 >= 0 = "
            "delta_dc."
        ),
    ),
    DarkSlackCase(
        case_id="DS-GENERATED-K3",
        port_count=3,
        route="generated",
        columns=(),
        mc_mass=(
            ((), F(7, 250)),
            ((0,), F(19, 100)),
            ((1,), F(19, 100)),
            ((2,), F(19, 100)),
            ((0, 1), F(1)),
            ((0, 2), F(1)),
            ((1, 2), F(1)),
            ((0, 1, 2), F(1)),
        ),
        d1_admitted=True,
        d2_admitted=True,
        admitted=True,
        failing_condition=None,
        r_min=F(7, 250),
        r_bar=F(7, 250),
        delta_dc=F(0),
        r_min_upper_bound=F(1),
        r_bar_cost=F(0),
        r_bar_cost_bound=F(1, 200),
        p_mc=F(1, 2),
        composed_slack=F(257, 500),
        composed_exact_form=F(257, 500),
        overstatement=F(0),
        improves_on_p_mc=True,
        derives_from=(
            "DARK-K3 -- the product form at K = 3 with equal p = 1/10 -- given "
            "its 0.2.0 scalars. THE FULL EIGHT-COLUMN MATRIX IS FROZEN AT 0.1.3 "
            "as DARK_CASES row DARK-K3 and IS NOT REPEATED HERE; `columns` is "
            "empty for that reason and `mc_mass` carries the multiclick masses "
            "the composition uses, which are the 0.1.3 values.\n"
            "r_min = 7/250 = R_{MC|empty}, and the single-click columns carry "
            "19/100 -- 'ALMOST SEVEN TIMES LARGER', which is Rem. rem:rmintrap's "
            "trap at K = 3.\n"
            "Generated route: delta_dc = 0, rbar = r_min = 7/250, cost 0 "
            "(bound (K + 2) eps_4 = 5/1000 = 1/200). At p_mc = 1/2, "
            "Eq. eq:darkpmcslack gives (1 - 7/250)(1/2) + 7/250 = "
            "243/500 + 14/500 = 257/500, which is IMP-K3-HALF, and "
            "Eq. eq:darkpmc gives the same. Overstatement 0. Improves: "
            "(7/250)(1/2) = 7/500 >= 0."
        ),
    ),
    DarkSlackCase(
        case_id="DS-DECLARED-WITNESS-K4",
        port_count=4,
        route="declared",
        columns=(
            ((), (((0, 1, 2, 3), F(1001, 1000)),)),
            ((0,), (((0, 1, 2, 3), F(1001, 1000)),)),
            ((1,), (((0, 1, 2, 3), F(1001, 1000)),)),
            ((2,), (((0, 1, 2, 3), F(1001, 1000)),)),
            ((3,), (((0, 1, 2, 3), F(1001, 1000)),)),
            ((0, 1), (((0, 1, 2, 3), F(999, 1000)),)),
            ((0, 2), (((0, 1, 2, 3), F(999, 1000)),)),
            ((0, 3), (((0, 1, 2, 3), F(999, 1000)),)),
            ((1, 2), (((0, 1, 2, 3), F(999, 1000)),)),
            ((1, 3), (((0, 1, 2, 3), F(999, 1000)),)),
            ((2, 3), (((0, 1, 2, 3), F(999, 1000)),)),
            ((0, 1, 2), (((0, 1, 2, 3), F(999, 1000)),)),
            ((0, 1, 3), (((0, 1, 2, 3), F(999, 1000)),)),
            ((0, 2, 3), (((0, 1, 2, 3), F(999, 1000)),)),
            ((1, 2, 3), (((0, 1, 2, 3), F(999, 1000)),)),
            ((0, 1, 2, 3), (((0, 1, 2, 3), F(999, 1000)),)),
        ),
        mc_mass=(
            ((), F(1001, 1000)),
            ((0,), F(1001, 1000)),
            ((1,), F(1001, 1000)),
            ((2,), F(1001, 1000)),
            ((3,), F(1001, 1000)),
            ((0, 1), F(999, 1000)),
            ((0, 2), F(999, 1000)),
            ((0, 3), F(999, 1000)),
            ((1, 2), F(999, 1000)),
            ((1, 3), F(999, 1000)),
            ((2, 3), F(999, 1000)),
            ((0, 1, 2), F(999, 1000)),
            ((0, 1, 3), F(999, 1000)),
            ((0, 2, 3), F(999, 1000)),
            ((1, 2, 3), F(999, 1000)),
            ((0, 1, 2, 3), F(999, 1000)),
        ),
        d1_admitted=True,
        d2_admitted=True,
        admitted=True,
        failing_condition=None,
        r_min=F(1001, 1000),
        r_bar=F(1),
        delta_dc=F(3, 500),
        r_min_upper_bound=F(503, 500),
        r_bar_cost=F(1, 1000),
        r_bar_cost_bound=F(3, 500),
        p_mc=F(1, 2),
        composed_slack=F(497, 500),
        composed_exact_form=F(2001, 2000),
        overstatement=F(13, 2000),
        improves_on_p_mc=True,
        derives_from=(
            "REMARK rem:d2slack'S OWN WITNESS CHANNEL, WRITTEN OUT AT K = 4 AND "
            "COMPOSED AT THE BB84 RECEIVER OF Ex. ex:bb84bound. This is the "
            "channel the contract exhibits to show that r_min > 1 IS REACHABLE "
            "under the widened (D1): 'a declared R placing mass 1 + eps_4 on "
            "the row S = [K] in every column S' not in MC and 1 - eps_4 on that "
            "same row in every column S' in MC occupies NO (D2)-FORBIDDEN "
            "POSITION AT ALL, is admitted at (eps_2, eps_4) = (0, eps_4), and "
            "has r_min = 1 + eps_4.'\n"
            "THE CHANNEL. Every column puts all its mass on the single row "
            "S = (0, 1, 2, 3). The five non-multiclick columns -- empty, and the "
            "four singletons, which is K + 1 = 5 of them -- carry "
            "1 + eps_4 = 1001/1000; the eleven multiclick columns carry "
            "1 - eps_4 = 999/1000.\n"
            "(D1) AT eps_4 = 1/1000: every entry is non-negative, hence "
            ">= -eps_4; every column sum is 1001/1000 or 999/1000, so "
            "|sum - 1| = 1/1000 <= eps_4. ADMITTED, at the boundary on both "
            "sides.\n"
            "(D2) AT eps_2: the only non-zero row is (0, 1, 2, 3), which "
            "CONTAINS EVERY S', so no entry sits in a forbidden position and "
            "nothing has to be compared against eps_2 at all. ADMITTED at any "
            "eps_2, including 0 -- which is what the contract means by "
            "'admitted at (eps_2, eps_4) = (0, eps_4)'.\n"
            "Eq. eq:rmin: the minimum over the five non-multiclick columns of "
            "R_{MC|S'} is 1001/1000, since the row (0, 1, 2, 3) lies in MC. So "
            "r_min = 1 + eps_4 = 1001/1000 > 1, EXACTLY AS THE CONTRACT "
            "PREDICTS, and it is EMITTED UNMODIFIED: 'r_min as computed is what "
            "Eq. eq:rmin defines and is the only one from which a reader can "
            "see that a declared channel produced r_min > 1 at all -- ITSELF A "
            "SIGNAL THAT THE DECLARATION IS OFF BY MORE THAN ROUNDING.'\n"
            "Eq. eq:rminupper CHECKS: R_{MC|S'} <= (1 + eps_4) + (K + 1) eps_4 "
            "= 1 + (K + 2) eps_4 = 1 + 6/1000 = 503/500, and "
            "1001/1000 = 1002/1000 <= 1006/1000.\n"
            "Eq. eq:rbar: rbar = min{1001/1000, 1} = 1. Eq. eq:rbarcost: "
            "r_min - rbar = 1/1000, and the bound (K + 2) eps_4 = 6/1000 = "
            "3/500 holds with room -- 'first order in eps_4 and no larger'.\n"
            "Eq. eq:darkdelta, DECLARED ROUTE: "
            "delta_dc = eps_4 + (K + 1) eps_2 = 1/1000 + 5 (1/1000) = 6/1000 = "
            "3/500. Note that the (K + 1) eps_2 term is carried EVEN THOUGH "
            "THIS CHANNEL USED NO (D2) SLACK: delta_dc is a function of the "
            "declared tolerances and K, not of the channel.\n"
            "THE COMPOSITION, AT THE BB84 RECEIVER OF Ex. ex:bb84bound WITH "
            "N = 2, WHERE p_mc = 1/2 EXACTLY (bound-data case BD-BB84-N2; "
            "K = 4 there too, so the two fit).\n"
            "  Eq. eq:darkpmcslack: (1 - rbar) p_mc + rbar - delta_dc = "
            "0 * (1/2) + 1 - 3/500 = 497/500.\n"
            "  Eq. eq:darkpmc: (1 - r_min) p_mc + r_min = "
            "(-1/1000)(1/2) + 1001/1000 = -1/2000 + 2002/2000 = 2001/2000.\n"
            "  Eq. eq:darkoverstate: (r_min - rbar)(1 - p_mc) + delta_dc = "
            "(1/1000)(1/2) + 3/500 = 1/2000 + 12/2000 = 13/2000. AND THE THREE "
            "AGREE: 2001/2000 - 497/500 = 2001/2000 - 1988/2000 = 13/2000 "
            "EXACTLY.\n"
            "WHY THIS MATTERS AND IS NOT A ROUNDING QUESTION: 2001/2000 EXCEEDS "
            "1. Proposition prop:slotvalid puts every emitted weight in [0, 1], "
            "and no lower bound on a POVM element can exceed the identity, so "
            "Eq. eq:darkpmc HERE IS NOT MERELY LOOSE, IT IS FALSE -- 'in the "
            "unsafe direction -- by (r_min - 1)(1 - p_mc)', which is "
            "(1/1000)(1/2) = 1/2000, the first term of the overstatement. That "
            "is the whole of the work Eq. eq:rbar does: '1 - rbar >= 0 BY "
            "CONSTRUCTION'.\n"
            "IT STILL IMPROVES: rbar (1 - p_mc) = 1 * (1/2) = 1/2 >= 3/500 = "
            "delta_dc, so 497/500 > 1/2 = p_mc."
        ),
    ),
    DarkSlackCase(
        case_id="DS-DECLARED-BELOW-THRESHOLD-K2",
        port_count=2,
        route="declared",
        columns=(
            ((), (((), F(999, 1000)), ((0, 1), F(1, 1000)))),
            ((0,), (((0,), F(1)),)),
            ((1,), (((1,), F(1)),)),
            ((0, 1), (((0, 1), F(1)),)),
        ),
        mc_mass=(
            ((), F(1, 1000)),
            ((0,), F(0)),
            ((1,), F(0)),
            ((0, 1), F(1)),
        ),
        d1_admitted=True,
        d2_admitted=True,
        admitted=True,
        failing_condition=None,
        r_min=F(0),
        r_bar=F(0),
        delta_dc=F(1, 250),
        r_min_upper_bound=F(251, 250),
        r_bar_cost=F(0),
        r_bar_cost_bound=F(1, 250),
        p_mc=F(1, 2),
        composed_slack=F(62, 125),
        composed_exact_form=F(1, 2),
        overstatement=F(1, 250),
        improves_on_p_mc=False,
        derives_from=(
            "THE CASE THE CONTRACT SAYS A CONSUMER SHOULD NOT HAVE TO DERIVE: A "
            "DECLARED CHANNEL WHOSE ADMITTED SLACK COSTS MORE THAN ITS DARK "
            "COUNTS GAIN. Rem. rem:d2slack: 'Eq. eq:darkpmcslack improves on "
            "p_mc -- which is the point of Theorem thm:dark-counts (iv) -- ONLY WHERE "
            "rbar (1 - p_mc) >= delta_dc; below that threshold the declared "
            "channel's admitted slack costs more than its dark counts gain, AND "
            "THE TWO EMITTED NUMBERS SAY SO.'\n"
            "THE CHANNEL, at K = 2: the no-click column leaks 1/1000 into the "
            "two-port multiclick and keeps 999/1000; the other three columns "
            "are the identity. Every column sums to 1 exactly and every entry "
            "is non-negative, so (D1) holds at any eps_4; every non-zero entry "
            "has S' contained in S, so no (D2)-forbidden position exists and "
            "(D2) holds at any eps_2. ADMITTED.\n"
            "Eq. eq:rmin over the three non-multiclick columns: "
            "R_{MC|empty} = 1/1000, R_{MC|{0}} = 0, R_{MC|{1}} = 0, so "
            "r_min = 0 -- BECAUSE THE SINGLE-CLICK COLUMNS CARRY NO MULTICLICK "
            "MASS AT ALL. rbar = min{0, 1} = 0; cost 0.\n"
            "Eq. eq:darkdelta, declared route at K = 2: "
            "delta_dc = eps_4 + 3 eps_2 = 1/1000 + 3/1000 = 4/1000 = 1/250.\n"
            "COMPOSITION AT p_mc = 1/2: Eq. eq:darkpmcslack gives "
            "(1 - 0)(1/2) + 0 - 1/250 = 125/250 - 1/250 = 124/250 = 62/125, "
            "WHICH IS BELOW p_mc = 1/2. Eq. eq:darkpmc would give 1/2 exactly, "
            "and Eq. eq:darkoverstate is (0)(1/2) + 1/250 = 1/250 -- the whole "
            "difference, 1/2 - 62/125 = 125/250 - 124/250 = 1/250.\n"
            "SO THE THRESHOLD TEST READS FALSE: rbar (1 - p_mc) = 0 < 1/250 = "
            "delta_dc. FROZEN BECAUSE AN IMPLEMENTATION THAT CLAMPED THE "
            "COMPOSED VALUE UP TO p_mc HERE WOULD BE ASSERTING A BOUND THE "
            "WIDENED HYPOTHESES DO NOT SUPPORT, and one that simply reported "
            "Eq. eq:darkpmc would overstate by exactly delta_dc."
        ),
    ),
    DarkSlackCase(
        case_id="DS-DECLARED-D2-BOUNDARY-ADMIT-K2",
        port_count=2,
        route="declared",
        columns=(
            ((), (((), F(1)),)),
            ((0,), (((0,), F(1)),)),
            ((1,), (((1,), F(1)),)),
            ((0, 1), (((0,), F(1, 1000)), ((0, 1), F(999, 1000)))),
        ),
        mc_mass=(
            ((), F(0)),
            ((0,), F(0)),
            ((1,), F(0)),
            ((0, 1), F(999, 1000)),
        ),
        d1_admitted=True,
        d2_admitted=True,
        admitted=True,
        failing_condition=None,
        r_min=F(0),
        r_bar=F(0),
        delta_dc=F(1, 250),
        r_min_upper_bound=F(251, 250),
        r_bar_cost=F(0),
        r_bar_cost_bound=F(1, 250),
        p_mc=F(1, 2),
        composed_slack=F(62, 125),
        composed_exact_form=F(1, 2),
        overstatement=F(1, 250),
        improves_on_p_mc=False,
        derives_from=(
            "(D2) AT ITS BOUNDARY, ADMITTED. Def. def:tolmap (iii): 'an entry "
            "counts as positive when R_{S|S'} > eps_2, SO THE CHANNEL IS "
            "REFUSED EXACTLY WHEN some entry with S' not a subset of S EXCEEDS "
            "eps_2.' Here the multiclick column (0, 1) leaks "
            "R_{{0}|{0,1}} = 1/1000 into the single-click row {0} -- a "
            "FORBIDDEN position, since {0, 1} is not a subset of {0} -- and "
            "1/1000 = eps_2 DOES NOT EXCEED eps_2, so the channel is ADMITTED. "
            "An implementation using >= refuses it.\n"
            "(D1): every column sums to 1 exactly.\n"
            "MULTICLICK ABSORPTION IS VIOLATED, AND BY EXACTLY THE ADMITTED "
            "AMOUNT. Theorem thm:dark-counts (iii) requires R_{MC|S'} = 1 for every "
            "S' in MC on an EXACTLY admissible R; here R_{MC|{0,1}} = 999/1000. "
            "Eq. eq:d2slack is the widened replacement and it holds: "
            "R_{MC|S'} >= (1 - eps_4) - (K + 1) eps_2 = 1 - delta_dc = "
            "1 - 1/250 = 249/250 = 996/1000, and 999/1000 >= 996/1000. THE "
            "SLACK IS NOT TIGHT HERE because the bound allows every one of the "
            "K + 1 = 3 rows with |S| <= 1 to leak eps_2 and this channel leaks "
            "from one.\n"
            "Eq. eq:rmin over the non-multiclick columns: all three carry zero "
            "multiclick mass, so r_min = 0 and rbar = 0. delta_dc = "
            "eps_4 + 3 eps_2 = 1/250. At p_mc = 1/2 the composed value is "
            "1/2 - 1/250 = 62/125, again below p_mc, and the overstatement "
            "1/250 is the whole of delta_dc."
        ),
    ),
    DarkSlackCase(
        case_id="DS-DECLARED-D2-REFUSE-K2",
        port_count=2,
        route="declared",
        columns=(
            ((), (((), F(1)),)),
            ((0,), (((0,), F(1)),)),
            ((1,), (((1,), F(1)),)),
            ((0, 1), (((0,), F(1, 500)), ((0, 1), F(499, 500)))),
        ),
        mc_mass=(
            ((), F(0)),
            ((0,), F(0)),
            ((1,), F(0)),
            ((0, 1), F(499, 500)),
        ),
        d1_admitted=True,
        d2_admitted=False,
        admitted=False,
        failing_condition="(D2)",
        r_min=None,
        r_bar=None,
        delta_dc=None,
        r_min_upper_bound=None,
        r_bar_cost=None,
        r_bar_cost_bound=None,
        p_mc=None,
        composed_slack=None,
        composed_exact_form=None,
        overstatement=None,
        improves_on_p_mc=None,
        derives_from=(
            "THE SAME CHANNEL WITH THE LEAK DOUBLED TO 1/500 = 2 eps_2, WHICH "
            "EXCEEDS eps_2 AND THEREFORE REFUSES. Def. def:tolmap (iii) again: "
            "refused exactly when a forbidden entry EXCEEDS eps_2. (D1) still "
            "holds -- the columns sum to 1 -- so this is a (D2) refusal and "
            "nothing else, which is what makes the pair with "
            "DS-DECLARED-D2-BOUNDARY-ADMIT-K2 informative: THE ONLY DIFFERENCE "
            "BETWEEN THE TWO CHANNELS IS ONE ENTRY, MOVED FROM eps_2 TO "
            "2 eps_2.\n"
            "NO SCALAR IS EMITTED. `fail_closed` produces 'a refusal with a "
            "machine-readable reason and NO artifact', so r_min, rbar and "
            "delta_dc are None here rather than placeholders. contract.tex "
            "SPELLS NO REASON STRING for a (D2) failure -- Section 2.6's table "
            "does not carry one and its preamble leaves the spelling to the "
            "implementer -- so none is frozen; what is frozen is the failing "
            "CONDITION."
        ),
    ),
    DarkSlackCase(
        case_id="DS-DECLARED-D1-COLSUM-REFUSE-K2",
        port_count=2,
        route="declared",
        columns=(
            ((), (((), F(501, 500)),)),
            ((0,), (((0,), F(1)),)),
            ((1,), (((1,), F(1)),)),
            ((0, 1), (((0, 1), F(1)),)),
        ),
        mc_mass=(
            ((), F(0)),
            ((0,), F(0)),
            ((1,), F(0)),
            ((0, 1), F(1)),
        ),
        d1_admitted=False,
        d2_admitted=True,
        admitted=False,
        failing_condition="(D1)",
        r_min=None,
        r_bar=None,
        delta_dc=None,
        r_min_upper_bound=None,
        r_bar_cost=None,
        r_bar_cost_bound=None,
        p_mc=None,
        composed_slack=None,
        composed_exact_form=None,
        overstatement=None,
        improves_on_p_mc=None,
        derives_from=(
            "(D1) COLUMN-SUM FAILURE, ONE DECLARED UNIT PAST THE BOUNDARY. "
            "Def. def:tolmap (iii): (D1) is admitted when every entry is "
            ">= -eps_4 AND |sum_S R_{S|S'} - 1| <= eps_4 for every column. The "
            "no-click column here sums to 501/500 = 1002/1000, so "
            "|sum - 1| = 2/1000 > 1/1000 = eps_4 and the channel is REFUSED. "
            "Compare DS-DECLARED-WITNESS-K4, whose columns sum to "
            "1 +/- eps_4 exactly and are ADMITTED: the pair fixes the side of "
            "the comparison. (D2) holds throughout -- every non-zero entry has "
            "S' contained in S -- so this is a (D1) refusal and nothing else."
        ),
    ),
    DarkSlackCase(
        case_id="DS-DECLARED-D1-NEGATIVE-ADMIT-K2",
        port_count=2,
        route="declared",
        columns=(
            ((), (((), F(1001, 1000)), ((0, 1), F(-1, 1000)))),
            ((0,), (((0,), F(1)),)),
            ((1,), (((1,), F(1)),)),
            ((0, 1), (((0, 1), F(1)),)),
        ),
        mc_mass=(
            ((), F(-1, 1000)),
            ((0,), F(0)),
            ((1,), F(0)),
            ((0, 1), F(1)),
        ),
        d1_admitted=True,
        d2_admitted=True,
        admitted=True,
        failing_condition=None,
        r_min=F(-1, 1000),
        r_bar=F(-1, 1000),
        delta_dc=F(1, 250),
        r_min_upper_bound=F(251, 250),
        r_bar_cost=F(0),
        r_bar_cost_bound=F(1, 250),
        p_mc=F(1, 2),
        composed_slack=F(991, 2000),
        composed_exact_form=F(999, 2000),
        overstatement=F(1, 250),
        improves_on_p_mc=False,
        derives_from=(
            "A NEGATIVE ENTRY AT EXACTLY -eps_4, ADMITTED, AND A NEGATIVE "
            "r_min WITH IT. Def. def:tolmap (iii) admits (D1) when "
            "R_{S|S'} >= -eps_4 for every entry; here the no-click column "
            "carries 1001/1000 on the row empty and -1/1000 = -eps_4 on the row "
            "(0, 1), summing to 1 exactly. Every non-zero entry has S' "
            "contained in S, so (D2) holds. ADMITTED at the boundary.\n"
            "Eq. eq:rmin over the three non-multiclick columns: "
            "R_{MC|empty} = -1/1000, R_{MC|{0}} = 0, R_{MC|{1}} = 0, so "
            "r_min = -1/1000, NEGATIVE. rbar = min{-1/1000, 1} = -1/1000 = "
            "r_min, so Eq. eq:rbarcost's cost is 0.\n"
            "THIS IS THE CASE THAT FREEZES A CLAUSE AN IMPLEMENTATION IS LIKELY "
            "TO 'FIX'. Rem. rem:d2slack's proof of Eq. eq:darkimproveslack ends: "
            "'NO STEP USES A BOUND ON r_min FROM EITHER SIDE, AND NO STEP USES "
            "THE SIGN OF r_min OR OF rbar.' So a negative rbar is admissible in "
            "Eq. eq:darkpmcslack and must not be clamped to 0; the inequality "
            "holds because replacing each coefficient of a sum of positive "
            "operators by a SMALLER real gives a Loewner-smaller operator, "
            "whatever the sign.\n"
            "COMPOSITION AT p_mc = 1/2: Eq. eq:darkpmcslack gives "
            "(1 - (-1/1000))(1/2) + (-1/1000) - 1/250 = "
            "1001/2000 - 2/2000 - 8/2000 = 991/2000. Eq. eq:darkpmc gives "
            "1001/2000 - 2/2000 = 999/2000. Eq. eq:darkoverstate is "
            "(r_min - rbar)(1 - p_mc) + delta_dc = 0 + 1/250 = 8/2000, and "
            "999/2000 - 991/2000 = 8/2000 EXACTLY.\n"
            "Both are below p_mc = 1000/2000, correctly: rbar (1 - p_mc) = "
            "-1/2000 < 8/2000 = delta_dc, so the threshold test reads False."
        ),
    ),
    DarkSlackCase(
        case_id="DS-DECLARED-D1-NEGATIVE-REFUSE-K2",
        port_count=2,
        route="declared",
        columns=(
            ((), (((), F(501, 500)), ((0, 1), F(-1, 500)))),
            ((0,), (((0,), F(1)),)),
            ((1,), (((1,), F(1)),)),
            ((0, 1), (((0, 1), F(1)),)),
        ),
        mc_mass=(
            ((), F(-1, 500)),
            ((0,), F(0)),
            ((1,), F(0)),
            ((0, 1), F(1)),
        ),
        d1_admitted=False,
        d2_admitted=True,
        admitted=False,
        failing_condition="(D1)",
        r_min=None,
        r_bar=None,
        delta_dc=None,
        r_min_upper_bound=None,
        r_bar_cost=None,
        r_bar_cost_bound=None,
        p_mc=None,
        composed_slack=None,
        composed_exact_form=None,
        overstatement=None,
        improves_on_p_mc=None,
        derives_from=(
            "THE SAME SHAPE WITH THE NEGATIVE ENTRY DOUBLED TO -1/500 = "
            "-2 eps_4, WHICH IS BELOW -eps_4 AND THEREFORE REFUSES. The column "
            "still sums to 1 exactly, so THE COLUMN-SUM HALF OF (D1) PASSES AND "
            "THE ENTRYWISE HALF FAILS -- which is why (D1) has two halves and "
            "why an implementation testing only the sums would admit this "
            "channel. Paired with DS-DECLARED-D1-NEGATIVE-ADMIT-K2, which sits "
            "exactly on -eps_4."
        ),
    ),
)

#: Eq. eq:d2slack on the one admitted case that actually uses (D2) slack:
#: R_{MC|S'} >= (1 - eps_4) - (K + 1) eps_2 = 1 - delta_dc for every S' in MC,
#: against the exact value 1 of Theorem thm:dark-counts (iii).
#: (case id, S', the achieved mass, the bound 1 - delta_dc, the exact value)
D2_SLACK_CASES: tuple[tuple[str, tuple[int, ...], F, F, F], ...] = (
    (
        "DS-DECLARED-D2-BOUNDARY-ADMIT-K2",
        (0, 1),
        F(999, 1000),
        F(249, 250),
        F(1),
    ),
    (
        "DS-DECLARED-WITNESS-K4",
        (0, 1),
        F(999, 1000),
        F(497, 500),
        F(1),
    ),
    (
        "DS-DECLARED-WITNESS-K4",
        (0, 1, 2, 3),
        F(999, 1000),
        F(497, 500),
        F(1),
    ),
)

#: Theorem thm:dark-counts (ii) is OUTSIDE the widened hypotheses and is stated, not
#: repaired: for an R admitted at (eps_2, eps_4) the composed family need not be
#: a POVM. Rem. rem:d2slack bounds both defects by eps_4.
#: (what fails, the exact statement, the widened replacement)
POVM_DEFECT_UNDER_WIDENED_D1: tuple[tuple[str, str, str], ...] = (
    (
        "completeness",
        "sum_S Mtilde_S = id",
        "(1 - eps_4) id <= sum_S Mtilde_S <= (1 + eps_4) id, since "
        "sigma_{S'} = sum_S R_{S|S'} lies in [1 - eps_4, 1 + eps_4]",
    ),
    (
        "positivity",
        "Mtilde_S >= 0",
        "Mtilde_S >= -eps_4 id, from a single entry at -eps_4",
    ),
)


#: The two dark-count routes are EXCLUSIVE (Section 2.1 `dark_count_channel`;
#: Def. def:darkadm; Section 2.6). CR-1 of the 0.1.3 freeze, closed by a
#: ruling in favour of a REFUSAL rather than a precedence rule or
#: a consistency check. The converse is fixed too: "a declared R therefore
#: requires p_dc|k = 0 for every k", so a declared R beside all-zero per-port
#: probabilities is ADMITTED and takes the declared route.
#: (case id, declares an explicit R, some p_dc|k non-zero, admitted, the route
#:  the artifact records, the verbatim reason where it refuses)
DARK_ROUTE_EXCLUSIVITY_CASES: tuple[
    tuple[str, bool, bool, bool, str | None, str | None], ...
] = (
    ("DRX-GENERATED", False, True, True, "generated", None),
    ("DRX-GENERATED-ALL-ZERO", False, False, True, "generated", None),
    ("DRX-DECLARED", True, False, True, "declared", None),
    (
        "DRX-BOTH-REFUSED",
        True,
        True,
        False,
        None,
        "dark_count_channel_declared_twice",
    ),
)


O_RP_DARKSLACK = RPOracleEntry(
    oracle_id="O-RP-DARKSLACK",
    claims=("RC11",),
    kind="toy-instance",
    subject=(
        "The three scalars the artifact emits beside a dark-count channel at "
        "0.2.0 -- r_min unmodified, the capped coefficient rbar, and the "
        "composition correction delta_dc by route -- with the composed value of "
        "eq:darkpmcslack computed exactly on both routes, including the "
        "witness channel of rem:d2slack at the BB84 receiver of ex:bb84bound; "
        "the (D1) and (D2) admit/refuse pairs at their declared tolerances; and "
        "the exclusivity of the two dark-count routes."
    ),
    derivation="""\
Definition def:darkadm, Definition def:tolmap (iii), Theorem thm:dark-counts and
Remark rem:d2slack, with Equations eq:rmin, eq:rbar, eq:darkdelta, eq:d2slack,
eq:rminupper, eq:rbarcost, eq:darkimproveslack, eq:darkpmcslack, eq:darkpmc and
eq:darkoverstate.

WHAT CHANGED, AND WHY IT IS NOT A def:evaluation-model MATTER. Definition def:tolmap (iii)
admits a declared R that violates (D2) by up to eps_2 in every forbidden
position and (D1) by up to eps_4 in every column. Remark rem:d2slack is careful
about the kind of thing that is: 'the datum is EXACTLY AS DECLARED, and what is
relaxed is A HYPOTHESIS, not the precision of an evaluation, so Theorem
thm:exact-and-evaluated (ii) DOES NOT REACH IT.' The cost is therefore carried to the
inequality a consumer composes with, and the artifact emits it.

BOTH SIDES OF BOTH TESTS ARE USED, and the cases are frozen so that each side
is visible. The LOWER side of (D1)'s column sum with the UPPER side of (D2)'s
entry bound gives eq:d2slack, R_{MC|S'} >= 1 - delta_dc for S' in MC, against
the exact value 1 of Theorem thm:dark-counts (iii); D2_SLACK_CASES freezes it on the
two admitted channels that have a multiclick column to test. The UPPER side of
(D1)'s column sum is what permits r_min > 1 (eq:rminupper) and is absorbed by
rbar. Reading eq:d2slack off an exact column sum 'would drop the eps_4 and
OVERSTATE THE BOUND FOR EVERY CHANNEL THIS CONTRACT ADMITS'.

THE WITNESS CHANNEL IS THE CENTRE OF THIS GROUP. DS-DECLARED-WITNESS-K4 is the
channel Remark rem:d2slack constructs, written out at K = 4 and composed at the
BB84 receiver of Example ex:bb84bound, where p_mc = 1/2 exactly at N = 2
(bound-data case BD-BB84-N2, which is a K = 4 receiver, so the two fit). It is
admitted, it occupies no (D2)-forbidden position at all, and it has
r_min = 1 + eps_4 = 1001/1000 > 1. Composing with eq:darkpmc there would give
2001/2000, WHICH EXCEEDS 1 -- an impossible lower bound on a POVM element, since
Proposition prop:slotvalid puts every emitted weight in [0, 1]. Composing with
eq:darkpmcslack gives 497/500, and the difference is eq:darkoverstate's
(r_min - rbar)(1 - p_mc) + delta_dc = 13/2000 exactly. That arithmetic closes:
2001/2000 - 1988/2000 = 13/2000. It is the whole of the work eq:rbar does, and
the contract names the failure it prevents: the coefficient 1 - r_min 'would
not be' non-negative 'and the composed bound would fail -- IN THE UNSAFE
DIRECTION -- by (r_min - 1)(1 - p_mc)'.

NOTHING IS CLAMPED, AND rbar IS NOT A REPAIR. 'R is emitted as declared, r_min
is emitted as eq:rmin computes it, and rbar is a SEPARATE NAMED SCALAR appearing
as a COEFFICIENT in a stated inequality. Lowering that coefficient WEAKENS the
bound, and needs nothing beyond id - M_MC >= 0; no claim is made that rbar
approximates r_min or any exact quantity.' Its cost is bounded by eq:rbarcost,
0 <= r_min - rbar <= (K + 2) eps_4, and every case above freezes both the cost
and the bound.

THE SIGN OF r_min IS NOT USED, AND THAT IS FROZEN.
DS-DECLARED-D1-NEGATIVE-ADMIT-K2 has an entry at exactly -eps_4, is admitted,
and has r_min = rbar = -1/1000 < 0. Remark rem:d2slack's proof ends 'NO STEP
USES A BOUND ON r_min FROM EITHER SIDE, AND NO STEP USES THE SIGN OF r_min OR
OF rbar', so an implementation that clamped a negative rbar to zero would be
strengthening a stated inequality without a warrant.

ON THE GENERATED ROUTE THE TWO FORMS COINCIDE, and DS-GENERATED-K2 and
DS-GENERATED-K3 freeze that they reproduce the 0.1.3 numbers exactly: 51/100 at
K = 2 and 257/500 at K = 3, which are DARK_IMPROVEMENT_CASES rows IMP-K2-HALF
and IMP-K3-HALF. 'On the generated route delta_dc = 0 and r_min <= 1, so
rbar = r_min and eq:darkpmcslack IS eq:darkpmc.' NO 0.1.3 DARK VALUE CHANGES.

THE IMPROVEMENT THRESHOLD IS FROZEN ON BOTH SIDES.
DS-DECLARED-BELOW-THRESHOLD-K2 is a channel whose composed value 62/125 sits
BELOW its own p_mc = 1/2, because rbar (1 - p_mc) = 0 < 1/250 = delta_dc. The
contract states the rule and says the artifact reports it: eq:darkpmcslack
improves on p_mc 'ONLY WHERE rbar (1 - p_mc) >= delta_dc; below that threshold
the declared channel's admitted slack costs more than its dark counts gain, AND
THE TWO EMITTED NUMBERS SAY SO'. An implementation that clamped the composed
value up to p_mc there would assert a bound the widened hypotheses do not
support.

THE ADMIT/REFUSE PAIRS SIT ON THE BOUNDARY. (D2) at eps_2 exactly is admitted
and at 2 eps_2 is refused, the two channels differing in ONE ENTRY. (D1)'s two
halves are separated: DS-DECLARED-D1-COLSUM-REFUSE-K2 fails the column sum with
every entry non-negative, and DS-DECLARED-D1-NEGATIVE-REFUSE-K2 fails the
entrywise bound with the column summing to 1 exactly, so an implementation
testing only one half admits one of them.

THEOREM thm:dark-counts (ii) IS OUTSIDE THE WIDENED HYPOTHESES AND IS NOT REPAIRED
EITHER. POVM_DEFECT_UNDER_WIDENED_D1 freezes both defects and their eps_4
bounds. 'Both are properties of the declared datum, and NEITHER IS REPAIRED.
They are not silent: the composed rows are exactly the operators a consumer
validates for Hermiticity and positivity against its own declared tolerance --
THE SAME BOUNDARY r_5 WATCHES FROM THIS SIDE.'

THE TWO ROUTES ARE EXCLUSIVE, which closes CR-1 of the 0.1.3 freeze.
DARK_ROUTE_EXCLUSIVITY_CASES freezes all four combinations, including the two
that are ADMITTED and the converse the contract states explicitly -- 'a declared
R therefore requires p_dc|k = 0 for every k'. The refusing combination carries
one of the five verbatim reasons Section 2.6 spells,
`dark_count_channel_declared_twice`, and the ruling was a refusal rather than a
precedence rule: the two routes 'supply the channel twice with no rule that
makes the two agree', and Remark rem:corrdark's record of which route the
emitted R came from 'presupposes that exactly one was taken'.
""",
)


# ---------------------------------------------------------------------------
#  Group RP-Q -- the (X)-only branch selector of Def. def:pmc (RC8)
# ---------------------------------------------------------------------------
#
#  0.2.0 deletes predicate (C). The branch-1 selector is predicate (X) ALONE:
#  "no probe modes are declared (Inp_S empty), or the setting carries the
#  vacuum probe (Gamma^(t) = 0)". Branch 2 -- the window-and-tail evaluation of
#  Lem. lem:windowtail, valid with NO hypothesis by its part (i) -- serves every
#  other setting. NO COMPUTED VALUE CHANGES (Section 1.1 (b)), and the frozen
#  0.1.3 bound-data cases are the evidence: every one of them took branch 1 by
#  (X) or branch 2 already.

#: Which branch Def. def:pmc takes and why, on the bound-data cases frozen at
#: 0.1.3 (BOUND_DATA_CASES, unchanged) and on the declaration-level settings the
#: contract names. (case id or setting, (X) holds, branch, the lemma that makes
#: the branch valid, a window is required)
PMC_BRANCH_CASES: tuple[tuple[str, bool, str, str, bool], ...] = (
    ("BD-BB84-N2", True, "1", "lem:collapse", False),
    ("BD-BB84-N3", True, "1", "lem:collapse", False),
    ("BD-BB84-N1-ZERO", True, "1", "lem:collapse", False),
    ("BD-BB84-PZ-QUARTER-N2", True, "1", "lem:collapse", False),
    ("BD-BS-N1", True, "1", "lem:collapse", False),
    ("BD-SINGULAR-N1", True, "1", "lem:collapse", False),
    ("BD-REM-N0", True, "1", "lem:collapse", False),
    ("BD-COLLAPSE-SHARP", True, "1", "lem:collapse", False),
    ("BD-PROBE-OFF-N1", True, "1", "lem:collapse", False),
    ("BD-PROBE-ON-N1-M3", False, "2", "lem:windowtail", True),
    ("BD-PROBE-ON-N1-M2", False, "2", "lem:windowtail", True),
    ("BD-COLLAPSE-FAILS-M4", False, "2", "lem:windowtail", True),
    ("BD-COLLAPSE-FAILS-M3", False, "2", "lem:windowtail", True),
)

#: Which clause of predicate (X) applies where it holds. (X) has TWO clauses
#: and they are decided on the DECLARATION, before any arithmetic
#: (Rem. rem:windowdecidable). (case id, clause, what makes gamma = beta_k = 1
#: exactly)
PMC_X_CLAUSE_CASES: tuple[tuple[str, str, str], ...] = (
    (
        "BD-BB84-N2",
        "first: no probe modes are declared (Inp_S is empty)",
        "Theorem thm:click-povm (iv): the unconditioned receiver has "
        "gamma = beta_k = 1, so Eq. eq:collapsehyp reads K >= K and holds WITH "
        "EQUALITY, no arithmetic having been performed",
    ),
    (
        "BD-PROBE-OFF-N1",
        "second: the setting carries the vacuum probe (Gamma^(t) = 0)",
        "Theorem thm:gaussian-schur (iii): c(A, 0) = 1 and A^eff = A_ChanChan for "
        "every A, so gamma = beta_k = 1 exactly and Eq. eq:collapsehyp again "
        "holds with equality",
    ),
    (
        "a probe on but DECOUPLED from every port",
        "NEITHER: (X) FAILS ON THE DECLARATION although gamma = beta_k = 1 in fact",
        "Def. def:pmc names this case itself: '(X) is SUFFICIENT, NOT "
        "NECESSARY: a receiver whose slack happens to be zero for some other "
        "reason -- a probe that is on but decoupled from every port, where "
        "Gamma^{1/2} A_LedLed Gamma^{1/2} = 0 makes gamma = beta_k = 1 as well "
        "-- FAILS (X) AND IS SERVED BY BRANCH 2. That is conservative, and "
        "Lemma lem:windowtail (i) makes it sound.'",
    ),
)

#: Rem. rem:noslack, frozen as a computation over every bound-data case
#: BOUND_DATA_CASES carries. The slack in Eq. eq:collapsehyp is
#: sigma = sum_k beta_k - 1 - (K-1) gamma = -beta(0), and beta(0) is the
#: channel-vacuum block of a positive operator, hence >= 0. So sigma <= 0
#: ALWAYS, Eq. eq:collapsehyp holds IF AND ONLY IF beta(0) = 0 exactly, and no
#: computed branch-1 test can fire.
#: (case id, beta(0), sigma = -beta(0), eq:collapsehyp holds)
COLLAPSE_SLACK_CASES: tuple[tuple[str, F, F, bool], ...] = (
    ("BD-BB84-N2", F(0), F(0), True),
    ("BD-BB84-N3", F(0), F(0), True),
    ("BD-BB84-N1-ZERO", F(0), F(0), True),
    ("BD-BB84-PZ-QUARTER-N2", F(0), F(0), True),
    ("BD-BS-N1", F(0), F(0), True),
    ("BD-SINGULAR-N1", F(0), F(0), True),
    ("BD-REM-N0", F(0), F(0), True),
    ("BD-COLLAPSE-SHARP", F(0), F(0), True),
    ("BD-PROBE-OFF-N1", F(0), F(0), True),
    ("BD-PROBE-ON-N1-M3", F(1, 15), F(-1, 15), False),
    ("BD-PROBE-ON-N1-M2", F(1, 15), F(-1, 15), False),
    ("BD-COLLAPSE-FAILS-M4", F(99, 100), F(-99, 100), False),
    ("BD-COLLAPSE-FAILS-M3", F(99, 100), F(-99, 100), False),
    ("BD-WINDOWTAIL-IV-C1", F(0), F(0), True),
)

#: The counts over COLLAPSE_SLACK_CASES, recorded because the 0.1.3 entry
#: O-RP-BOUND's prose states them as "nine of the fourteen ... and five" while
#: its own frozen tuple BETA_ZERO_AND_C_SLACK has TEN zeros and FOUR positives.
#: The tuple was right and the sentence miscounted; the integrity test recomputes
#: beta(0) from the data, so nothing rested on the sentence. Reported as a
#: finding of this freeze rather than edited in the 0.1.3 entry.
COLLAPSE_SLACK_COUNTS: tuple[tuple[str, int], ...] = (
    ("total", 14),
    ("beta(0) = 0 exactly, so eq:collapsehyp holds", 10),
    ("beta(0) > 0, so eq:collapsehyp fails", 4),
    ("sigma > 0 anywhere", 0),
)

#: Rem. rem:noslack's conclusion, frozen as the statement an implementation must
#: not contradict. (statement, why)
NOSLACK_STATEMENTS: tuple[tuple[str, str], ...] = (
    (
        "sigma <= 0 at every receiver, every setting and every parameter",
        "sigma = -beta(0) and beta(0) = blk M^{(=0)}_{mc|t} exactly -- the "
        "block is one dimensional and every Fock(.)^{(0)} = 1 -- so beta(0) is "
        "a diagonal block of a positive operator (Theorem thm:click-povm (i) with no "
        "probe, Theorem thm:conditional-povm (ii) with one), hence a NON-NEGATIVE "
        "REAL",
    ),
    (
        "eq:collapsehyp holds if and only if beta(0) = 0 exactly",
        "beta(0) >= 0 and eq:collapsehyp says beta(0) <= 0",
    ),
    (
        "a test demanding sigma >= eps > 0 is UNSATISFIABLE",
        "it would assert beta(0) <= -eps < 0",
    ),
    (
        "a test demanding sigma >= 0 adds nothing to (X)",
        "it is satisfied only in the exact-equality case, 'WHICH IS WHAT (X) "
        "ALREADY CERTIFIES FROM THE DECLARATION WITHOUT COMPUTING ANYTHING'",
    ),
    (
        "the only way branch 1 is ever taken is (X)",
        "'IT IS NOT AN OMISSION THAT NO ARITHMETIC DECIDES IT'",
    ),
    (
        "nothing is lost either way",
        "branch 2 is unconditionally valid (Lemma lem:windowtail (i)) and, by "
        "Lemma lem:windowtail (ii), recovers branch 1's value in the limit of a "
        "widening window whenever c^(t) < 1",
    ),
)


O_RP_PMC_BRANCH = RPOracleEntry(
    oracle_id="O-RP-PMC-BRANCH",
    claims=("RC8",),
    kind="analytic-limit",
    subject=(
        "The branch selector of Definition def:pmc at 0.2.0: predicate (X) "
        "alone, in both of its clauses, with branch 2 serving every other "
        "setting; the collapse slack sigma = -beta(0), frozen as never positive "
        "over every bound-data case; and the one refusal the definition now "
        "states."
    ),
    derivation="""\
Definition def:pmc, Remark rem:noslack, Remark rem:windowdecidable, Lemma
lem:collapse, Lemma lem:windowtail, Theorem thm:emitted-bound, Section 1.1 (b).

WHAT THE AMENDMENT DID, AND WHAT IT DID NOT DO. Predicate (C) -- 'take branch 1
when the evaluated slack clears a declared margin' -- is DELETED, and the input
eps_hyp with it. The branch-1 selector is predicate (X) alone. Section 1.1 (b)
states the consequence in bold: 'NO COMPUTED VALUE CHANGES: every setting that
took branch 1 took it by (X), and every setting that failed (X) took branch 2
already. Lemma lem:collapse and its use under (X) are untouched.' PMC_BRANCH_
CASES is that statement checked against the thirteen bound-data cases frozen at
0.1.3 whose branch Definition def:pmc decides: nine take branch 1 by (X), four
take branch 2, and NOT ONE of them was ever selected by (C).

THE ARGUMENT IS NOW IN THE CONTRACT. Remark rem:noslack proves what the 0.1.3
freeze derived in this registry and routed as change request CR-4: the slack
sigma = sum_k beta_k - 1 - (K-1) gamma equals -beta(0); beta(0) is the
channel-vacuum block of the conditioned multiclick element EXACTLY, that block
being one dimensional with every Fock(.)^{(0)} = 1; and it is a diagonal block
of a positive operator, hence a non-negative real. So sigma <= 0 always,
eq:collapsehyp holds if and only if beta(0) = 0 exactly, and a margin test is
unsatisfiable. COLLAPSE_SLACK_CASES freezes beta(0) and sigma on all fourteen
frozen tuples: ten have beta(0) = 0 and four have it strictly positive, and NOT
ONE has positive slack.

THE COUNT IS RECORDED BECAUSE THE 0.1.3 ENTRY MISSTATES IT. O-RP-BOUND's
derivation says 'Nine of the fourteen frozen bound-data cases have beta(0) = 0
exactly and five have it strictly positive'; the frozen tuple it refers to has
TEN and FOUR. The tuple is right, the sentence is not, and the integrity test
recomputes beta(0) from each case's own data rather than reading either -- so
nothing rested on the sentence. It is recorded in COLLAPSE_SLACK_COUNTS and
reported as a finding of this freeze rather than corrected inside a 0.1.3
entry, which run A does not edit.

(X) HAS TWO CLAUSES AND BOTH ARE EXERCISED. PMC_X_CLAUSE_CASES freezes the
first at a probe-free receiver (Theorem thm:click-povm (iv) gives gamma = beta_k = 1)
and the second at a vacuum-probe setting (Theorem thm:gaussian-schur (iii) gives the
same), together with the case Definition def:pmc itself names as showing that
(X) is SUFFICIENT AND NOT NECESSARY: a probe that is on but decoupled from every
port has gamma = beta_k = 1 in fact, FAILS (X) ON THE DECLARATION, and is served
by branch 2. 'That is conservative, and Lemma lem:windowtail (i) makes it
sound.'

WHY THE PREDICATE IS DECIDED ON THE DECLARATION AND NOT ON THE ARITHMETIC.
Branch 1 needs eq:collapsehyp and would, where that fails, 'return a value
STRICTLY ABOVE inf_{n>N} beta(n) (Remark rem:collapse-fails) -- AN OVER-LARGE
LOWER BOUND, WHICH IS THE UNSAFE DIRECTION'. (X) is decided before any
arithmetic and admits the equality case, 'which is the generic one'. Remark
rem:windowdecidable makes the corresponding input requirement decidable at
validation: a window is required at exactly the settings where (X) fails, 'which
is the rule Section 2.1 states and the rule an implementer can enforce while
validating input', and 'a window supplied at a setting where (X) holds is
UNUSED, NOT AN ERROR'.

ONE REFUSAL, NOT TWO. Definition def:pmc's 'Refusals' paragraph at 0.2.0 reads
in full: 'A declaration supplying no m_t at a setting where (X) fails is refused
rather than defaulted; by Remark rem:windowdecidable that condition is decidable
at input validation from declared data alone.' The eps_hyp half is gone with the
predicate, and the definition adds that 'there is no such predicate here, and
THERE IS NO DECLARED MARGIN AMONG THE INPUTS'. Refusal case
REF-WINDOW-MISSING-0-2-0 freezes the 0.2.0 text; the 0.1.3 rows
REF-WINDOW-MISSING and REF-EPS-HYP-MISSING are marked in SUPERSEDED_BY_0_2_0.

NOSLACK_STATEMENTS carries Remark rem:noslack's six conclusions as prose, in the
contract's own words, because they are what an implementation must not
contradict: in particular that a NON-STRICT companion test -- |beta(0)| <=
eps -- is the change of mathematical substance the 0.1.3 freeze flagged and the
human did not take, and that its absence costs tightness and never safety.
""",
)


# ---------------------------------------------------------------------------
#  Group RP-R -- Section 2.6, the refusal rules with a named reason string
# ---------------------------------------------------------------------------
#
#  NEW AT 0.2.0. 0.1.3 spelled exactly ONE machine-readable reason,
#  `receiver_grams_not_enclosed`, and that one is a TIER FALLBACK rather than a
#  refusal. Section 2.6 gathers FIVE refusal reasons "because AN IMPLEMENTER
#  BINDS THE STRING, NOT THE PROSE", and names the fallback beside them "only so
#  the two kinds of machine-readable reason are not confused".
#
#  THE SPELLING TRAP DID NOT GO AWAY, IT MOVED. Section 2.6's own preamble says
#  the table "does not supersede or replace any other refusal stated in this
#  document", and enumerates six further failed validations that "refuse under
#  the same convention at the site that states it, WITH A REASON STRING THE
#  IMPLEMENTER NAMES". Those six are frozen in
#  REFUSALS_NAMED_WITHOUT_A_SPELLING WITHOUT a key, and no key is invented for
#  them here.

REFUSAL_CASES_0_2_0: tuple[RefusalCase, ...] = (
    RefusalCase(
        case_id="REF-DARK-DECLARED-TWICE",
        subject=(
            "a request declaring an explicit dark-count channel R while some "
            "p_dc|k in detector_layer is non-zero"
        ),
        failing_condition=(
            "Section 2.1 / Def. def:darkadm: the two dark-count routes are exclusive"
        ),
        reason_is_verbatim=True,
        reason="dark_count_channel_declared_twice",
        emits_artifact=False,
        derives_from=(
            "SECTION 2.6, ROW 1, AND THE CLOSURE OF CHANGE REQUEST CR-1 OF THE "
            "0.1.3 FREEZE. Section 2.1 `dark_count_channel`: 'THE TWO ROUTES "
            "ARE EXCLUSIVE: a request that declares an explicit R while some "
            "p_dc|k is non-zero in detector_layer is REFUSED, because it "
            "supplies the channel twice with no rule that makes the two agree, "
            "and Rem. rem:corrdark -- the artifact records which route the "
            "emitted R came from -- PRESUPPOSES THAT EXACTLY ONE WAS TAKEN. A "
            "declared R therefore requires p_dc|k = 0 for every k.' "
            "Def. def:darkadm closes with the same sentence and Section 1.1 (d) "
            "records the ruling.\n"
            "THE RULING WAS A REFUSAL, NOT A PRECEDENCE RULE AND NOT A "
            "CONSISTENCY CHECK. The 0.1.3 freeze put three readings and "
            "declined to choose; (b) was chosen. "
            "DARK_ROUTE_EXCLUSIVITY_CASES freezes all four combinations, "
            "including the two admitted ones and the converse the contract "
            "states."
        ),
    ),
    RefusalCase(
        case_id="REF-SPLITTING-RATIO",
        subject="a beamsplitter parameter offered as a splitting ratio a : b",
        failing_condition=(
            "Section 2.4: the splitting-ratio presentation is struck and is "
            "not admitted"
        ),
        reason_is_verbatim=True,
        reason="splitting_ratio_presentation_unsupported",
        emits_artifact=False,
        derives_from=(
            "SECTION 2.6, ROW 2, AND THE CLOSURE OF CHANGE REQUEST CR-2. "
            "Section 2.4's Units bullet at 0.2.0: 'EXACTLY ONE ALTERNATIVE "
            "PRESENTATION IS ADMITTED: a POWER loss in decibels ... A SPLITTING "
            "RATIO IS NOT ADMITTED AND IS REFUSED. A declaration offering a "
            "beamsplitter as a : b is refused with the reason "
            "`splitting_ratio_presentation_unsupported`, and the transmittance "
            "x of Eq. eq:bs IS DECLARED DIRECTLY.'\n"
            "STRUCK RATHER THAN CONVERTED, and Section 1.1 (e) gives the "
            "reason the 0.1.3 freeze gave for routing it: the string a : b "
            "'does not carry the two facts a conversion needs -- WHETHER THE "
            "RATIO IS OF POWER OR OF AMPLITUDE, AND WHICH OF THE TWO DECLARED "
            "OUTPUT PATHS THE FIRST TERM NAMES -- so admitting it would make "
            "the contract IMPOSE A READING on a declared datum whose meaning "
            "the declaration does not fix, WHICH IS EXACTLY THE SUBSTITUTION "
            "`fail_closed` FORBIDS; and a wrong reading is SILENT, since 90:10 "
            "read as an amplitude ratio gives x = 81/100 rather than x = 9/10 "
            "and every compiled matrix downstream is wrong WITHOUT ANY CHECK "
            "FAILING.'\n"
            "THE DECIBEL PRESENTATION SURVIVES, and the distinction is stated: "
            "'eta = 10^(-L_dB/10) fixes both the quantity and its argument and "
            "THERE IS NO ARM TO CHOOSE.' DECIBEL_CONVERSIONS, frozen at 0.1.3 "
            "at the three exponents where the conversion is exactly rational, "
            "is UNAFFECTED by this amendment; no frozen value anywhere in this "
            "file uses a splitting ratio, at 0.1.3 or here."
        ),
    ),
    RefusalCase(
        case_id="REF-RANK-EXCEEDS-PORT-SIZE",
        subject=(
            "route (i): a declared port Gram whose eps_2-rank exceeds its port's size"
        ),
        failing_condition="Def. def:tolmap (ii): rk_{eps_2}(A_k) > |P_k|",
        reason_is_verbatim=True,
        reason="port_gram_rank_exceeds_port_size",
        emits_artifact=False,
        derives_from=(
            "SECTION 2.6, ROW 3, with Section 2.1 `port_grams`, "
            "Def. def:tolmap (ii) and Eq. eq:eps2rank. Frozen as tolmap case "
            "TOLMAP-II-RANK-OVER-REPORTED-REFUSE: A_1 = diag(1/2, 1/500) on a "
            "single-mode port has rk_{eps_2}(A_1) = 2 > 1.\n"
            "THE REFUSAL IS ROUTE-(i) ONLY, and Section 2.1 says so by putting "
            "the consistency condition on the `port_grams` row: on routes (ii) "
            "and (iii) the Grams are DERIVED from a supplied or compiled "
            "matrix and Theorem thm:port-grams (ii) bounds their rank by construction, "
            "so there is nothing to check against the port map. THE THRESHOLD "
            "IS DECLARED AND ABSOLUTE, which is the whole of "
            "Rem. rem:ranktwosided: no library default and no "
            "machine-epsilon-relative cutoff decides it."
        ),
    ),
    RefusalCase(
        case_id="REF-R5-ABOVE-TOLERANCE",
        subject=(
            "an emitted photon-number block failing Hermiticity or positivity: "
            "r_5 > eps_5"
        ),
        failing_condition="Def. def:residuals: r_5 > eps_5",
        reason_is_verbatim=True,
        reason="photon_block_positivity_residual_above_tolerance",
        emits_artifact=False,
        derives_from=(
            "SECTION 2.6, ROW 4, with Def. def:residuals Eq. eq:res5 and "
            "Prop. prop:res5. Frozen as Residual5Cases "
            "R5-FAIL-HERMITICITY-DEFECT (rho = 1/4, a Hermiticity defect with "
            "no negative eigenvalue) and R5-FAIL-NEGATIVE-EIGENVALUE "
            "(rho = 1/8, a Hermitian block with a negative eigenvalue), both "
            "against eps_5 = 1/1000.\n"
            "REFUSE-ONLY, AND THAT IS THE POINT OF THE ROW. 'No block is "
            "Hermitized, symmetrized, projected onto the positive cone, "
            "clamped or repaired in any way: WHAT THE ARTIFACT CARRIES IS THE "
            "COMPUTED BLOCK ITSELF.' Rem. rem:res5why: a repaired block 'is a "
            "DIFFERENT OPERATOR and NO CLAIM OF THIS CONTRACT HOLDS FOR IT'. "
            "The residual exists on ALL THREE ROUTES, since every route "
            "produces emitted blocks."
        ),
    ),
    RefusalCase(
        case_id="REF-TOLERANCE-OUTSIDE-DOMAIN",
        subject="a declared tolerance lying outside [0, 1)",
        failing_condition=(
            "Section 2.1 / Rem. rem:tolerancedomain: the declared domain is [0, 1)"
        ),
        reason_is_verbatim=True,
        reason="tolerance_outside_declared_domain",
        emits_artifact=False,
        derives_from=(
            "SECTION 2.6, ROW 5, with Section 2.1 `numerical_tolerances` and "
            "Rem. rem:tolerancedomain. Frozen as TOLERANCE_DOMAIN_CASES rows "
            "TOL-DOM-ONE-REFUSE (the open end, eps_5 = 1), "
            "TOL-DOM-ABOVE-ONE-REFUSE and TOL-DOM-NEGATIVE-REFUSE, against the "
            "three admitted rows including TOL-DOM-ZERO-ADMIT at the closed "
            "end.\n"
            "VALIDATED AT INPUT, which matters for the ordering of an "
            "implementation's checks: the tolerances decide the other "
            "validations (Def. def:tolmap), so a tolerance outside its own "
            "domain must refuse BEFORE it is used to decide anything. "
            "Rem. rem:tolerancedomain gives the reason the domain exists at "
            "all: at eps >= 1 each governed test 'is NOT MERELY LOOSE, IT IS "
            "VACUOUS OR DEGENERATE, AND NAMABLY SO', and "
            "TOLERANCE_DOMAIN_DEGENERACIES freezes the five named degeneracies."
        ),
    ),
    RefusalCase(
        case_id="REF-WINDOW-MISSING-0-2-0",
        subject=(
            "no m_t declared at a setting where predicate (X) fails -- i.e. "
            "whose probe is on"
        ),
        failing_condition="Def. def:pmc: no m_t at a setting where (X) fails",
        reason_is_verbatim=False,
        reason=None,
        emits_artifact=False,
        derives_from=(
            "THE 0.2.0 TEXT OF Def. def:pmc'S 'Refusals' PARAGRAPH, WHICH NAMES "
            "EXACTLY ONE REFUSAL: 'A declaration supplying no m_t at a setting "
            "where (X) fails is REFUSED RATHER THAN DEFAULTED; by Remark "
            "rem:windowdecidable that condition is DECIDABLE AT INPUT "
            "VALIDATION FROM DECLARED DATA ALONE.' The eps_hyp half of the "
            "0.1.3 sentence is gone with predicate (C), and the definition adds "
            "that 'THERE IS NO DECLARED MARGIN AMONG THE INPUTS'.\n"
            "THIS ROW REPLACES REF-WINDOW-MISSING, whose verdict was and "
            "remains correct but whose quoted sentence is the 0.1.3 one; that "
            "row is marked in SUPERSEDED_BY_0_2_0. contract.tex SPELLS NO "
            "REASON STRING for this refusal -- Section 2.6's preamble lists 'a "
            "missing or too-small m_t' among the six that refuse 'WITH A REASON "
            "STRING THE IMPLEMENTER NAMES' -- so none is frozen; what is frozen "
            "is the failing CONDITION."
        ),
    ),
    RefusalCase(
        case_id="FALLBACK-CERTIFIED-TO-ESTIMATE-0-2-0",
        subject="a certified request that depends on compiled Grams",
        failing_condition="thm:exact-and-evaluated (iii): floating-point evaluation, no enclosure",
        reason_is_verbatim=True,
        reason="receiver_grams_not_enclosed",
        emits_artifact=True,
        derives_from=(
            "THE SIXTH SPELLED STRING, AND THE ONLY ONE THAT IS NOT A REFUSAL. "
            "Section 2.6's closing paragraph: 'ONE REASON STRING IN THIS "
            "CONTRACT IS NOT A REFUSAL. A `certified` request that depends on "
            "compiled Grams is answered `estimate` with the reason "
            "`receiver_grams_not_enclosed` (Theorem thm:exact-and-evaluated (iii)). THAT IS A "
            "TIER FALLBACK, AND AN ARTIFACT IS EMITTED; it is named here only "
            "so the two kinds of machine-readable reason are not confused.'\n"
            "UNCHANGED FROM 0.1.3 IN SUBSTANCE, and frozen again here only "
            "because `emits_artifact` now distinguishes it from the five: the "
            "0.1.3 row FALLBACK-CERTIFIED-TO-ESTIMATE carries the same verdict "
            "and the same string and is NOT superseded. TIER_CASES, frozen at "
            "0.1.3, still applies on all three routes by Theorem "
            "thm:exact-and-evaluated (iv)'s '(iii) still applies' and (iii)'s 'NO PATH IN THIS "
            "MODULE CAN PRODUCE A `certified` LABEL'."
        ),
    ),
)


O_RP_REASONS = RPOracleEntry(
    oracle_id="O-RP-REASONS",
    claims=CLAIM_IDS,
    kind="fail-closed",
    subject=(
        "Section 2.6 as a key vocabulary: the five machine-readable refusal "
        "reasons contract.tex 0.2.0 spells verbatim, the sixth string that is a "
        "tier fallback and not a refusal, and the six further refusals the "
        "section enumerates WITHOUT a spelling."
    ),
    derivation="""\
Section 2.6 (sec:refusals), Section 2.5 `fail_closed`, Theorem thm:exact-and-evaluated (iii).

WHAT THE SECTION IS FOR, IN ITS OWN WORDS: the rules gathered there are stated
"together with THE REASON STRING THEY EMIT; they are gathered here because AN
IMPLEMENTER BINDS THE STRING, NOT THE PROSE". That is a change of kind from
0.1.3, where the contract fixed the naming OBLIGATION everywhere and the
spelling nowhere but one, and where this registry recorded a spelling trap
accordingly. FIVE strings are now contract text and are transcribed character
for character in REFUSAL_REASONS_VERBATIM_0_2_0, in the table's own order. The
LaTeX `\\allowbreak` macros in the source are line-break hints and are not part
of a key.

THE SIXTH STRING IS NOT A REFUSAL, and the section is explicit that this is why
it is named at all: `receiver_grams_not_enclosed` is a TIER FALLBACK and AN
ARTIFACT IS EMITTED, at `estimate`. REASON_EMITS_ARTIFACT freezes the
distinction across all six, and REASON_VOCABULARY_0_2_0 is the six together --
the complete set of reason spellings contract.tex 0.2.0 states. AN
IMPLEMENTATION THAT EMITTED A SEVENTH UNDER ONE OF THESE SIX CONDITIONS, OR
REUSED ONE OF THESE SIX FOR A CONDITION THE TABLE DOES NOT NAME, WOULD BE
REPORTING SOMETHING THE CONTRACT DOES NOT STATE.

THE TABLE IS NOT THE WHOLE OF fail_closed, and the preamble says so: it "does
not supersede or replace any other refusal stated in this document: every
further failed validation named in Section 2 -- two input routes supplied at
once, a violated condition (E1), (E2) or (E3), a non-zero `tolerance` field, a
missing or too-small m_t, a missing declared tolerance, a probe state outside
the Gaussian tier -- refuses under the same convention at the site that states
it, WITH A REASON STRING THE IMPLEMENTER NAMES".
REFUSALS_NAMED_WITHOUT_A_SPELLING freezes those six with their sites and WITHOUT
a key. The 0.1.3 refusal rows for the first four of them --
REF-TWO-ROUTES, REF-OUT-OF-DOMAIN-NOT-CLIPPED, REF-C10-NOT-A-CONTRACTION,
REF-CYCLE, REF-SUPPORT-INCOMPARABLE, REF-NONZERO-TOLERANCE,
REF-WINDOW-TOO-SMALL -- carry `reason_is_verbatim = False` and no key, and NONE
of them is superseded: their verdicts and their unspelled status are what 0.2.0
still says.

TWO REASON PHRASES REMAIN PROSE. "parameter uncertainty sets are out of scope"
(Section 2.4, in the contract's own quotation marks) and the emitted
`calibration_coverage` statement (Section 2.2) are sentences, not machine keys,
and are carried as prose exactly as at 0.1.3. The 0.1.3 row
REF-NONZERO-TOLERANCE holds the first and is unchanged.

WHAT IS SUPERSEDED HERE IS THE VOCABULARY OBJECT, NOT A VERDICT.
REFUSAL_REASONS_VERBATIM, the one-element tuple frozen at 0.1.3, was a true
statement about contract.tex 0.1.3 and is a false one about 0.2.0; it is marked
in SUPERSEDED_BY_0_2_0 with REASON_VOCABULARY_0_2_0 as its replacement. It is
not edited: run B repoints the golden test that replays it, deliberately.
""",
)


# ---------------------------------------------------------------------------
#  What the amendment supersedes in the 0.1.3 freeze
# ---------------------------------------------------------------------------
#
#  EXPLICIT, AND IN THIS FILE. Every 0.1.3 frozen case or table whose INPUT
#  SHAPE or EXPECTED VALUE the amendment invalidates, or whose framing it makes
#  stale, is listed below with the contract site and its replacement. NOTHING IS
#  DELETED AND NOTHING IS SILENTLY EDITED: the 0.1.3 objects stand byte for byte
#  and run B retires or rewrites them deliberately, which is what the
#  freeze rule requires of a value that must change.
#
#  `kind` says what sort of mark it is, because the three are not the same
#  obligation:
#    superseded -- the input shape or the expected value is INVALIDATED. Run B
#                  must retire or rewrite it; asserting it as it stands would
#                  assert something contract.tex 0.2.0 does not say.
#    incomplete -- every value in it is still correct, but the object no longer
#                  covers what the contract now states. Run B extends it.
#    reframed   -- every value in it is still correct and the object still
#                  covers its subject, but its narrative names something the
#                  amendment removed. Run B rewrites the narrative.
#
#  NOT ON THIS LIST, AND DELIBERATELY: the splitting-ratio presentation. The
#  0.1.3 freeze declared x directly in every beamsplitter case and froze the
#  decibel conversion only ("No frozen value uses a splitting ratio"), so
#  striking the presentation invalidates NOTHING frozen. Recording the absence
#  is part of the list being complete.


@dataclass(frozen=True)
class Supersession:
    """One 0.1.3 frozen object the 0.2.0 amendment marks."""

    #: The module-level name, or the case_id inside the table named by `table`.
    name: str
    #: The module-level table it lives in; equal to `name` for a whole table.
    table: str
    kind: str
    superseded_by: str
    #: The element of contract.tex 0.2.0 that invalidates or restates it.
    contract_site: str
    reason: str
    #: The 0.2.0 case ids or table names that replace it. Empty where the
    #: object is retired outright because the thing it tested no longer exists.
    replacement: tuple[str, ...]


SUPERSEDED_BY_0_2_0: tuple[Supersession, ...] = (
    Supersession(
        name="TOLERANCE_FIXTURE",
        table="TOLERANCE_FIXTURE",
        kind="superseded",
        superseded_by="0.2.0",
        contract_site=(
            "Section 2.1 `numerical_tolerances`; Rem. rem:tolerancedomain; "
            "Section 1.1 (a) and (b)"
        ),
        reason=(
            "THE DECLARED TUPLE'S MEMBERS CHANGED. It carries eps_hyp, which "
            "0.2.0 removes with predicate (C), and lacks eps_5, which 0.2.0 "
            "adds; and its members carry no declared domain, where 0.2.0 "
            "declares [0, 1) for each with a verbatim refusal outside it. The "
            "ARITY is six before and after, which is exactly why an "
            "implementation could pass an arity check on the wrong tuple."
        ),
        replacement=("TOLERANCE_FIXTURE_0_2_0", "TOLERANCE_DOMAIN_CASES"),
    ),
    Supersession(
        name="REF-EPS-HYP-MISSING",
        table="REFUSAL_CASES",
        kind="superseded",
        superseded_by="0.2.0",
        contract_site="Section 1.1 (b); Def. def:pmc, 'Refusals'",
        reason=(
            "THE INPUT IT REFUSES THE ABSENCE OF NO LONGER EXISTS. eps_hyp is "
            "removed with predicate (C), and Def. def:pmc now names exactly one "
            "refusal. RETIRED OUTRIGHT: there is no 0.2.0 successor, because a "
            "declaration supplying no eps_hyp is now a declaration supplying a "
            "key the contract does not define. The 0.1.3 standing observation "
            "about the UNCONDITIONAL eps_hyp requirement goes with it."
        ),
        replacement=(),
    ),
    Supersession(
        name="REF-WINDOW-MISSING",
        table="REFUSAL_CASES",
        kind="reframed",
        superseded_by="0.2.0",
        contract_site="Def. def:pmc, 'Refusals'",
        reason=(
            "THE VERDICT STANDS AND THE QUOTATION DOES NOT. Its `derives_from` "
            "quotes the 0.1.3 sentence 'A declaration supplying no eps_hyp, or "
            "NO m_t AT A SETTING WHERE (X) FAILS, IS REFUSED', of which 0.2.0 "
            "keeps only the second half. A missing m_t at a setting where (X) "
            "fails is still refused, and still decidably so at input "
            "validation."
        ),
        replacement=("REF-WINDOW-MISSING-0-2-0",),
    ),
    Supersession(
        name="REFUSAL_REASONS_VERBATIM",
        table="REFUSAL_REASONS_VERBATIM",
        kind="superseded",
        superseded_by="0.2.0",
        contract_site="Section 2.6; Thm. thm:exact-and-evaluated (iii)",
        reason=(
            "IT IS THE STATEMENT 'contract.tex SPELLS EXACTLY ONE "
            "MACHINE-READABLE REASON STRING', which was true of 0.1.3 and is "
            "FALSE of 0.2.0: Section 2.6 spells five refusal reasons and names "
            "the fallback as a sixth string of a different kind. The one string "
            "it contains is still spelled by the contract and still means what "
            "it meant; what is invalidated is the TUPLE AS A VOCABULARY."
        ),
        replacement=(
            "REFUSAL_REASONS_VERBATIM_0_2_0",
            "TIER_FALLBACK_REASON_VERBATIM",
            "REASON_VOCABULARY_0_2_0",
        ),
    ),
    Supersession(
        name="BETA_ZERO_AND_C_SLACK",
        table="BETA_ZERO_AND_C_SLACK",
        kind="superseded",
        superseded_by="0.2.0",
        contract_site="Section 1.1 (b); Def. def:pmc; Rem. rem:noslack",
        reason=(
            "ITS FOURTH FIELD IS 'WHETHER PREDICATE (C) FIRES', AND PREDICATE "
            "(C) DOES NOT EXIST AT 0.2.0. The first three fields -- the case "
            "id, beta(0) and the slack -- are correct and are carried into "
            "COLLAPSE_SLACK_CASES unchanged, where the fourth field becomes "
            "'eq:collapsehyp holds', which is what the quantity actually "
            "decides. The 0.1.3 tuple was CR-4's evidence; the amendment made "
            "the derivation the contract's own, as Rem. rem:noslack."
        ),
        replacement=("COLLAPSE_SLACK_CASES", "COLLAPSE_SLACK_COUNTS"),
    ),
    Supersession(
        name="WINDOW_REQUIREMENT_CASES",
        table="WINDOW_REQUIREMENT_CASES",
        kind="reframed",
        superseded_by="0.2.0",
        contract_site="Def. def:pmc; Rem. rem:windowdecidable",
        reason=(
            "EVERY VERDICT STANDS -- a window is required at exactly the "
            "settings where (X) fails, and one supplied where it holds is "
            "'UNUSED, NOT AN ERROR' -- but its fourth row quotes the 0.1.3 "
            "sentence in which the decoupled-probe receiver 'fails (X), FAILS "
            "(C), and is served by branch 2'. 0.2.0 writes the same case "
            "without the (C) clause."
        ),
        replacement=("PMC_BRANCH_CASES", "PMC_X_CLAUSE_CASES"),
    ),
    Supersession(
        name="BD-PROBE-ON-N1-M3",
        table="BOUND_DATA_CASES",
        kind="reframed",
        superseded_by="0.2.0",
        contract_site="Def. def:pmc; Rem. rem:noslack",
        reason=(
            "THE NUMBERS ARE UNCHANGED AND THE BRANCH IS UNCHANGED. Its "
            "`derives_from` says 'predicate (C) fails (its slack is "
            "-beta(0) = -1/15 < 0, and by change request CR-4 it could never "
            "have succeeded)'; at 0.2.0 there is no predicate (C) to fail and "
            "CR-4 is closed. The setting fails (X) because its probe is on, "
            "and branch 2 serves it -- which is what the case already froze."
        ),
        replacement=("PMC_BRANCH_CASES",),
    ),
    Supersession(
        name="RESIDUAL_CASES",
        table="RESIDUAL_CASES",
        kind="incomplete",
        superseded_by="0.2.0",
        contract_site=(
            "Def. def:residuals (Eq. eq:res5, and 'Which residuals exist on "
            "which route'); Section 2.2 `validation_results`"
        ),
        reason=(
            "EVERY VALUE IN IT IS STILL CORRECT AND NONE CHANGES. The four "
            "failing residuals were frozen with their SPECTRAL norms in "
            "`value_spectral` -- 5/4, 1/2, 1/4 and 3/4 -- and those are the "
            "numbers Def. def:residuals now mandates. What the table does not "
            "cover is r_5, which does not appear in it, and the route rule, "
            "which makes r_1 and r_3 ABSENT on route (i) rather than emitted."
        ),
        replacement=("RESIDUAL5_CASES", "RESIDUAL_ROUTE_PRESENCE"),
    ),
    Supersession(
        name="R4-FAIL-MULTICLICK-OMITTED",
        table="RESIDUAL_CASES",
        kind="reframed",
        superseded_by="0.2.0",
        contract_site="Def. def:residuals; Section 1.1, first disclosure",
        reason=(
            "ITS SPECTRAL VALUE 3/4 IS UNCHANGED AND IS NOW THE ONLY ADMISSIBLE "
            "READING. The case exists because 0.1.3 named no norm, so it froze "
            "the squared Frobenius reading 11/8 BESIDE the spectral one 'so "
            "that THE REFUSAL VERDICT IS FROZEN WHILE THE NUMBER IS NOT'. "
            "Def. def:residuals 0.2.0 names the SPECTRAL norm, closing open "
            "implementation choice OIC-3, so the second reading is no longer a "
            "reading of anything. IT IS THE ONLY FROZEN CASE WHERE THE TWO "
            "NUMBERS DIFFER, which is why it alone is marked."
        ),
        replacement=("RESIDUAL_NORM_0_2_0",),
    ),
    Supersession(
        name="DARK_CASES",
        table="DARK_CASES",
        kind="incomplete",
        superseded_by="0.2.0",
        contract_site=(
            "Section 2.2 `dark_count_channel`; Eq. eq:rbar, Eq. eq:darkdelta; "
            "Rem. rem:d2slack"
        ),
        reason=(
            "EVERY MATRIX AND EVERY r_min IN IT IS STILL CORRECT. What the "
            "DarkCase record has no field for is what the artifact now emits "
            "BESIDE r_min: the capped coefficient rbar of Eq. eq:rbar and the "
            "composition correction delta_dc of Eq. eq:darkdelta, and which of "
            "the two routes the channel came from. A dark-count record without "
            "those three is not the 0.2.0 emitted shape."
        ),
        replacement=("DARK_SLACK_CASES",),
    ),
    Supersession(
        name="DARK-NOT-MONOTONE-REFUSED",
        table="DARK_CASES",
        kind="reframed",
        superseded_by="0.2.0",
        contract_site="Def. def:tolmap (iii)",
        reason=(
            "THE VERDICT STANDS AT 0.2.0 AND IS NOW DECIDED BY A DECLARED "
            "NUMBER. Its forbidden entry R_{{0}|{0,1}} = 1/2 exceeds "
            "eps_2 = 1/1000 by a wide margin, so the channel refuses under "
            "Def. def:tolmap (iii) exactly as it did under the exact condition. "
            "What its `derives_from` does not say is that (D2) is now decided "
            "AT eps_2, with 'an entry counts as positive when R_{S|S'} > eps_2'."
        ),
        replacement=(
            "DS-DECLARED-D2-BOUNDARY-ADMIT-K2",
            "DS-DECLARED-D2-REFUSE-K2",
        ),
    ),
    Supersession(
        name="DARK_IMPROVEMENT_CASES",
        table="DARK_IMPROVEMENT_CASES",
        kind="reframed",
        superseded_by="0.2.0",
        contract_site="Rem. rem:d2slack; Eq. eq:darkpmcslack; Section 2.2",
        reason=(
            "ALL THREE VALUES ARE CORRECT AND ARE REPRODUCED EXACTLY by "
            "DS-GENERATED-K2 and DS-GENERATED-K3, because all three rows are "
            "GENERATED-route channels, where 'delta_dc = 0 and r_min <= 1, so "
            "rbar = r_min and Eq. eq:darkpmcslack IS Eq. eq:darkpmc'. What is "
            "superseded is the FORM: the table freezes Eq. eq:darkpmc as 'the "
            "improved bound', and at 0.2.0 'THE INEQUALITY A CONSUMER COMPOSES "
            "WITH IS Eq. eq:darkpmcslack', which coincides with it only on that "
            "route."
        ),
        replacement=("DARK_SLACK_CASES",),
    ),
    Supersession(
        name="CONVENTION_KEYS",
        table="CONVENTION_KEYS",
        kind="incomplete",
        superseded_by="0.2.0",
        contract_site="Section 2.5, bullet 15; Def. def:tolmap; Section 1.1 (c)",
        reason=(
            "SIXTEEN BULLETS AT 0.1.3, SEVENTEEN AT 0.2.0: "
            "`numerical_tolerance_assignment` is inserted between `numerics` "
            "and `fail_closed`. The sixteen names in it are unchanged and are "
            "still the right sixteen; the tuple is short by one."
        ),
        replacement=("CONVENTION_KEYS_0_2_0",),
    ),
    Supersession(
        name="CHANGE_REQUEST_CANDIDATES",
        table="CHANGE_REQUEST_CANDIDATES",
        kind="reframed",
        superseded_by="0.2.0",
        contract_site="Section 1.1 (b), (d), (e), (f); the amendment's rulings",
        reason=(
            "ITS FOUR ROUTED ITEMS -- CR-1 to CR-4 -- ARE ALL CLOSED BY THIS "
            "AMENDMENT, each by a ruling, so their 'ROUTED "
            "-- does not block this freeze' verdicts no longer describe the "
            "module's state. THE SIX CLEARED ITEMS STAND AS CLEARED: three of "
            "them are re-checked against 0.2.0 in "
            "CHANGE_REQUEST_CANDIDATES_0_2_0 and none changed."
        ),
        replacement=("CHANGE_REQUEST_CANDIDATES_0_2_0",),
    ),
    Supersession(
        name="O-RP-NUMERICS",
        table="RP_ORACLES",
        kind="incomplete",
        superseded_by="0.2.0",
        contract_site="Def. def:residuals; Def. def:tolmap",
        reason=(
            "ITS SUBJECT AND DERIVATION SAY 'THE FOUR RESIDUALS' AND RECORD THE "
            "NORM AS OPEN (OIC-3). Both statements were true of 0.1.3. The "
            "eight residual cases it pins are unaffected, the tier rule it "
            "pins is unaffected, and Rem. rem:ia's enclosure directions are "
            "unaffected."
        ),
        replacement=("O-RP-RES5", "O-RP-TOLMAP"),
    ),
    Supersession(
        name="O-RP-BOUND",
        table="RP_ORACLES",
        kind="reframed",
        superseded_by="0.2.0",
        contract_site="Def. def:pmc; Rem. rem:noslack; Section 1.1 (b)",
        reason=(
            "ITS DERIVATION CARRIES THE CR-4 ARGUMENT AND DISCUSSES PREDICATE "
            "(C) AT LENGTH; the amendment made that argument the contract's own "
            "(Rem. rem:noslack) and deleted the predicate. Every p_mc, window, "
            "tail and residual gap it pins is unchanged. IT ALSO MISCOUNTS: "
            "'Nine of the fourteen frozen bound-data cases have beta(0) = 0 "
            "exactly and five have it strictly positive', where its own frozen "
            "tuple has TEN and FOUR. See COLLAPSE_SLACK_COUNTS; the integrity "
            "test recomputes beta(0) from each case's data, so nothing rested "
            "on the sentence."
        ),
        replacement=("O-RP-PMC-BRANCH", "COLLAPSE_SLACK_CASES"),
    ),
    Supersession(
        name="O-RP-INTERFACE",
        table="RP_ORACLES",
        kind="reframed",
        superseded_by="0.2.0",
        contract_site="Section 2.6",
        reason=(
            "IT PINS THE 0.1.3 SPELLING TRAP -- one verbatim string, the "
            "obligation everywhere else -- and every interface case it carries "
            "(the two-route refusal, the non-zero tolerance refusal, the "
            "out-of-domain-parameter refusal, the mirror-handedness default, "
            "the subsystem_order precedence, the outcome alphabet, the "
            "receiver_construction presence rule) IS UNCHANGED AT 0.2.0. What "
            "changed is that five refusal reasons are now contract text."
        ),
        replacement=("O-RP-REASONS",),
    ),
)

#: The 0.1.3 objects the amendment does NOT mark, recorded because a
#: supersession list is only useful if it is complete in both directions.
NOT_SUPERSEDED_BY_0_2_0: tuple[tuple[str, str], ...] = (
    (
        "every catalogue case, compile case, Fock case, Gram case, "
        "representation case, POVM block case, coarse-graining case, "
        "efficiency case and probe case",
        "Section 1.1: the amendment 'executes seven human rulings and nothing "
        "else; EVERY OTHER STATEMENT OF 0.1.3 STANDS UNCHANGED and is not "
        "re-opened here'. None of the seven touches RC1-RC7, RC10 or RC12.",
    ),
    (
        "DECIBEL_CONVERSIONS",
        "The decibel presentation is KEPT (Section 2.4). Only the "
        "splitting-ratio presentation is struck, and no frozen value uses one "
        "-- at 0.1.3 or here.",
    ),
    (
        "the r_1..r_4 values of RESIDUAL_CASES",
        "All four failing residuals were frozen with their SPECTRAL norms, "
        "which is the norm Def. def:residuals now names. NO RESIDUAL VALUE "
        "CHANGES UNDER THE AMENDMENT.",
    ),
    (
        "TIER_CASES, BOUND_EVALUATION_V1, ENCLOSURE_DIRECTIONS",
        "Theorem thm:exact-and-evaluated (iii) and (iv) and Remark rem:ia are untouched; the "
        "fallback string and its behaviour are the same on all three routes.",
    ),
    (
        "every p_mc, window minimum, tail and residual gap in BOUND_DATA_CASES",
        "Section 1.1 (b), in bold: 'NO COMPUTED VALUE CHANGES.' The branch each "
        "case takes is unchanged too, and PMC_BRANCH_CASES records it.",
    ),
    (
        "RMIN_TRAP_CASES and the r_min values of DARK_CASES",
        "Rem. rem:rmintrap: 'Which columns the minimum runs over is a question "
        "about the index set and is UNTOUCHED BY EITHER WIDENED TEST.'",
    ),
    (
        "ASSUMPTION_ROWS",
        "'No assumption is added, none is removed' (Section 1.1). The TEXT of "
        "Ass. ass:float changed -- four residuals to those of the five that "
        "exist on the route taken -- but its id, machine key and Supports cell "
        "are the same, and this registry freezes the id, the key and the cell.",
    ),
    (
        "INPUT_KEYS, OUTPUT_KEYS, OUTPUT_PRESENCE, INPUT_ROUTES, CATALOGUE_IDS",
        "No input or output KEY NAME is added or removed at 0.2.0; the "
        "fourteen and the fifteen are the same names. What three output rows "
        "and two input rows CONTAIN changed, which is not a change to these "
        "tuples.",
    ),
)


def supersession(name: str) -> Supersession | None:
    """Return the mark on a 0.1.3 object, or None if it carries none."""
    for entry in SUPERSEDED_BY_0_2_0:
        if entry.name == name:
            return entry
    return None


def is_superseded(name: str) -> bool:
    """Report whether the 0.2.0 amendment marks the named 0.1.3 object."""
    return supersession(name) is not None


#: WHERE THE MARKED OBJECTS ARE STILL ASSERTED, AS RUN A LEAVES THE TREE.
#: Computed by scanning the run-B test files -- tests/golden/test_receiver_povm_*
#: , tests/unit/test_receiver_* and tests/property/test_receiver_povm_* -- for a
#: whole-word occurrence of each marked name. It is RUN B'S CHECKLIST, and the
#: integrity test asserts the real scan is a SUBSET of it: run B may only remove
#: references, never add one.
#:
#: NOTHING HERE IS A FAILURE TODAY. No code changed in this run, so every one of
#: these tests still replays a 0.1.3 value against a 0.1.3 implementation and
#: still passes. The invariant that bites is the other one: a run-B test file
#: that has moved to the amendment -- which it declares by naming
#: `receiver-povm@0.2.0` -- may NOT assert a marked object without naming
#: SUPERSEDED_BY_0_2_0 itself. (file, marked name)
PENDING_RETIREMENT_AT_RUN_B: tuple[tuple[str, str], ...] = (
    (
        "tests/golden/test_receiver_povm_artifact_against_registry.py",
        "BD-PROBE-ON-N1-M3",
    ),
    ("tests/golden/test_receiver_povm_artifact_against_registry.py", "CONVENTION_KEYS"),
    ("tests/golden/test_receiver_povm_artifact_against_registry.py", "O-RP-NUMERICS"),
    ("tests/golden/test_receiver_povm_artifact_against_registry.py", "O-RP-INTERFACE"),
    (
        "tests/golden/test_receiver_povm_bound_against_registry.py",
        "BETA_ZERO_AND_C_SLACK",
    ),
    (
        "tests/golden/test_receiver_povm_bound_against_registry.py",
        "WINDOW_REQUIREMENT_CASES",
    ),
    ("tests/golden/test_receiver_povm_bound_against_registry.py", "BD-PROBE-ON-N1-M3"),
    ("tests/golden/test_receiver_povm_bound_against_registry.py", "O-RP-BOUND"),
    ("tests/golden/test_receiver_povm_dark_against_registry.py", "DARK_CASES"),
    (
        "tests/golden/test_receiver_povm_dark_against_registry.py",
        "DARK_IMPROVEMENT_CASES",
    ),
    ("tests/golden/test_receiver_povm_interface_against_registry.py", "O-RP-INTERFACE"),
    (
        "tests/golden/test_receiver_povm_refusals_against_registry.py",
        "TOLERANCE_FIXTURE",
    ),
    (
        "tests/golden/test_receiver_povm_refusals_against_registry.py",
        "REF-EPS-HYP-MISSING",
    ),
    (
        "tests/golden/test_receiver_povm_refusals_against_registry.py",
        "REF-WINDOW-MISSING",
    ),
    (
        "tests/golden/test_receiver_povm_refusals_against_registry.py",
        "REFUSAL_REASONS_VERBATIM",
    ),
    ("tests/golden/test_receiver_povm_refusals_against_registry.py", "O-RP-INTERFACE"),
    ("tests/golden/test_receiver_povm_residuals_against_registry.py", "RESIDUAL_CASES"),
    (
        "tests/golden/test_receiver_povm_residuals_against_registry.py",
        "R4-FAIL-MULTICLICK-OMITTED",
    ),
    ("tests/golden/test_receiver_povm_residuals_against_registry.py", "O-RP-NUMERICS"),
    ("tests/unit/test_receiver_fail_closed.py", "TOLERANCE_FIXTURE"),
)

#: The string a run-B test file names when it has moved to the amendment. While
#: a file still declares `receiver-povm@0.1.3` it is pre-amendment and its
#: references to marked objects are the pending work above; the moment it
#: declares 0.2.0 the exemption is gone.
AMENDMENT_SPEC_VERSION_MARKER: str = MATHEMATICAL_SPEC_VERSION_0_2_0


# ---------------------------------------------------------------------------
#  Change-request candidates cleared -- the 0.2.0 pass
# ---------------------------------------------------------------------------
#
#  The freeze rule requires that
#  anything the contract leaves this freeze unable to derive exactly be reported
#  as a change request rather than worked around. NOTHING WAS.
#
#  ELEVEN items were carried into this freeze as candidates: the four the 0.1.3
#  freeze routed, which the amendment CLOSES; three of the six the 0.1.3 freeze
#  cleared, re-checked against the amended text because the amendment touched
#  their sites; and four raised NEW by this pass, all of which the contract
#  answers. EVERY ONE IS CLEARED. `change_requests_open` in interface.yaml is
#  empty and no change request is raised against contract.tex 0.2.0.

CHANGE_REQUEST_CANDIDATES_0_2_0: tuple[tuple[str, str, str], ...] = (
    (
        "CLOSED BY 0.2.0 -- interface.yaml CR-1",
        "`dark_count_channel` admitted either route with no rule for a request "
        "supplying both, although rem:corrdark presupposed that exactly one was "
        "taken.",
        "DECIDED AS A REFUSAL -- reading (b) of the "
        "three the 0.1.3 freeze put, and not a precedence rule or a "
        "consistency check. Section 2.1, Def. def:darkadm and the Section 2.6 "
        "table all state it, and the table gives it the verbatim reason "
        "`dark_count_channel_declared_twice`. The converse is fixed with it: "
        "'a declared R therefore requires p_dc|k = 0 for every k'. FROZEN as "
        "REF-DARK-DECLARED-TWICE and DARK_ROUTE_EXCLUSIVITY_CASES, which "
        "carries all four combinations including the two admitted ones. The "
        "0.1.3 freeze's statement that NO frozen case supplied both remains "
        "true, so no 0.1.3 dark case is invalidated by the ruling.",
    ),
    (
        "CLOSED BY 0.2.0 -- interface.yaml CR-2",
        "Section 2.4 named a splitting-ratio presentation as converted at "
        "validation and gave no conversion rule.",
        "STRUCK, NOT CONVERTED. Section 2.4 now admits EXACTLY ONE alternative "
        "presentation, the decibel one, and refuses a splitting ratio with the "
        "verbatim reason `splitting_ratio_presentation_unsupported`. Section "
        "1.1 (e) gives the reason and it is the one the 0.1.3 freeze gave: the "
        "string a : b does not carry whether the ratio is of power or of "
        "amplitude nor which output the first term names, and a wrong reading "
        "is silent. FROZEN as REF-SPLITTING-RATIO. NO FROZEN VALUE IS "
        "AFFECTED: every beamsplitter case declares x directly and "
        "DECIBEL_CONVERSIONS is untouched.",
    ),
    (
        "CLOSED BY 0.2.0 -- interface.yaml CR-3",
        "rem:bsconv claimed the symmetric beamsplitter convention gives the "
        "same port Grams 'by Corollary cor:phases', which is an OUTPUT-side "
        "statement, while the exact factorization carries an INPUT-side factor "
        "too.",
        "QUALIFIED, NOT EXTENDED, and the reading the 0.1.3 freeze checked "
        "exactly at x = 9/25 is the reading the amendment adopted. Section 2.5 "
        "`beamsplitter_convention` now states TWO conditions -- the two output "
        "paths never interfere again downstream, AND the input-side factor of "
        "Eq. eq:bssym is a scalar on the declared input space -- and Section "
        "1.1 (f) records that no input-path phase convention is added because "
        "'none is needed once the claim is true as stated, and NO CLAIM OF THIS "
        "CONTRACT CONSUMES THE REMARK'. The 0.1.3 frozen pair "
        "REP-BSCONV-OUTPUT-PHASE and REP-BSCONV-SYMMETRIC stands unchanged and "
        "is now the check of a stated relation rather than of a routed "
        "question.",
    ),
    (
        "CLOSED BY 0.2.0 -- interface.yaml CR-4",
        "Predicate (C) of Def. def:pmc was unreachable: its slack is -beta(0), "
        "beta(0) is a diagonal block of a positive operator and is therefore "
        ">= 0, so a predicate demanding strict slack could fire only on "
        "floating-point noise.",
        "DELETED, AND THE MARGIN INPUT WITH IT -- 'Delete "
        "(C), drop the margin input.' Reading (b), the non-strict companion "
        "the 0.1.3 freeze flagged as A CHANGE OF MATHEMATICAL SUBSTANCE, was "
        "NOT taken. The derivation is now the contract's own, as "
        "Rem. rem:noslack, and Def. def:pmc says in its own text that a "
        "computed companion 'would never fire' and that 'THERE IS NO SUCH "
        "PREDICATE HERE, AND THERE IS NO DECLARED MARGIN AMONG THE INPUTS'. "
        "FROZEN as COLLAPSE_SLACK_CASES, NOSLACK_STATEMENTS and "
        "PMC_BRANCH_CASES. No computed value changes, and the thirteen frozen "
        "bound-data cases whose branch def:pmc decides confirm it.",
    ),
    (
        "CLEARED (re-checked at 0.2.0)",
        "Is the DIRECTION of Def. def:tolmap (iv)'s widened test conservative? "
        "An unclamped negative c enters Eq. eq:beta, and Eq. eq:beta is "
        "increasing in c^n.",
        "ANSWERED ON BOTH SIDES BY Rem. rem:cdirection, AND THE ANSWER IS NOT "
        "ONE-SIDED. Odd n: the evaluated bound is BELOW the exact one, "
        "conservative, by (K-1) gamma |c|^n, at most (K-1) eps_2 at n = 1. Even "
        "n >= 2: it can EXCEED the exact one, by at most (K-1) eps_2^2. "
        "Section 1.1's second disclosure records why the contract states both: "
        "'the one-sided description of its direction would have been the same "
        "defect this module's implementation record already caught once in a "
        "different cutoff'. FROZEN as C_DIRECTION_CASES at n = 1, 2, 3, 4, "
        "where both stated bounds are ATTAINED WITH EQUALITY at n = 1 and "
        "n = 2. NOTHING IS IMPROVISED: the rule is widen and never clamp, and "
        "the contract says why leaving the choice open would leave the emitted "
        "number undetermined.",
    ),
    (
        "CLEARED (re-checked at 0.2.0)",
        "How is a declared parameter REPRESENTED, given A-EXACT's exactness and "
        "A-FLOAT's floating-point evaluation? (0.1.3 open implementation "
        "choice OIC-2.)",
        "STILL OPEN, STILL NOT DECIDED, AND STILL THE REASON THIS FILE FREEZES "
        "EXACT VALUES. The amendment does not touch Ass. ass:exact and touches "
        "Ass. ass:float only to say 'those of the FIVE residuals that exist on "
        "the input route taken'. Thm. thm:exact-and-evaluated (i), (ii) and (iv) are unchanged, "
        "including (iv)'s contemplation of Grams 'DECLARED AS EXACT RATIONAL OR "
        "ALGEBRAIC DATA'. Recorded as OIC-2 in interface.yaml, not decided.",
    ),
    (
        "CLEARED (re-checked at 0.2.0)",
        "Which matrix norm do the residuals use? (0.1.3 open implementation "
        "choice OIC-3.)",
        "CLOSED BY THE CONTRACT: '||.|| IS THE SPECTRAL NORM throughout "
        "Eq. eq:res1-Eq. eq:rhodef' (Def. def:residuals). NO 0.1.3 VALUE "
        "CHANGES: each of the four failing residuals was frozen with its "
        "spectral norm in `value_spectral`, and 5/4, 1/2, 1/4 and 3/4 are the "
        "numbers the amendment now mandates. What is superseded is the SECOND "
        "reading -- the squared Frobenius one, which differs only at "
        "R4-FAIL-MULTICLICK-OMITTED -- and that row is marked. Recorded as "
        "closed in interface.yaml `closed_implementation_choices`.",
    ),
    (
        "CLEARED (new at this freeze)",
        "delta_dc = eps_4 + (K + 1) eps_2 on the DECLARED route. Is it a "
        "function of the declared tolerances, or of how much slack the channel "
        "actually used?",
        "OF THE DECLARED TOLERANCES AND K, AND THE CONTRACT LEAVES NO ROOM. "
        "Eq. eq:darkdelta is a two-case definition on THE ROUTE, not on the "
        "channel: '0 -- generated route: R is the product form Eq. eq:darkR' "
        "and 'eps_4 + (K + 1) eps_2 -- declared route: R admitted under "
        "Def. def:tolmap (iii)'. Rem. rem:d2slack's own witness channel makes "
        "the question concrete and answers it the same way: that channel "
        "'occupies NO (D2)-FORBIDDEN POSITION AT ALL' and is 'admitted at "
        "(eps_2, eps_4) = (0, eps_4)', yet nothing in Eq. eq:darkdelta reduces "
        "its delta_dc on that account. FROZEN so at DS-DECLARED-WITNESS-K4, "
        "where delta_dc = 6/1000 although the channel used no eps_2 slack.",
    ),
    (
        "CLEARED (new at this freeze)",
        "Eq. eq:rbar caps r_min at 1. May an implementation also floor rbar at "
        "0, since a negative coefficient looks like a defect?",
        "NO, AND THE CONTRACT SAYS SO IN THE PROOF. Rem. rem:d2slack's "
        "derivation of Eq. eq:darkimproveslack ends: 'NO STEP USES A BOUND ON "
        "r_min FROM EITHER SIDE, AND NO STEP USES THE SIGN OF r_min OR OF "
        "rbar.' The inequality holds because replacing each coefficient of a "
        "sum of positive operators by a SMALLER real gives a Loewner-smaller "
        "operator, which is sign-blind; flooring rbar at 0 would RAISE a "
        "coefficient and strengthen a stated inequality without a warrant. "
        "FROZEN as DS-DECLARED-D1-NEGATIVE-ADMIT-K2, where rbar = -1/1000 and "
        "the composed value is 991/2000.",
    ),
    (
        "CLEARED (new at this freeze)",
        "Eq. eq:eps2rank writes '> eps_2'. Is the comparison strict, and does "
        "it matter?",
        "STRICT, AS WRITTEN, AND IT DECIDES CASES. Def. def:tolmap (ii) writes "
        "the count as #{i : lambda_i > eps_2} and its own argument turns on the "
        "edge: a Gram admitted by item (i) 'has its numerically-zero "
        "eigenvalues in [-eps_2, eps_2] AND THE TWO THRESHOLDS CANNOT DISAGREE "
        "ABOUT WHICH THEY ARE', which is true for '>' and false for '>='. "
        "FROZEN as TOLMAP-II-RANK-BOUNDARY-NOT-COUNTED-ADMIT, an eigenvalue at "
        "exactly eps_2 that is NOT counted, beside "
        "TOLMAP-II-RANK-OVER-REPORTED-REFUSE at 2 eps_2, which is.",
    ),
    (
        "CLEARED (new at this freeze)",
        "The maximum in Eq. eq:res5 runs 'over exactly the blocks the artifact "
        "emits'. Does it include the n = 0 blocks, which are one dimensional "
        "and trivially Hermitian?",
        "YES, AND THE CONTRACT ENUMERATES THE INDEX SET RATHER THAN LEAVING IT "
        "TO INFERENCE: 'every emitted outcome letter v in V, every photon "
        "number 0 <= n <= N, and every declared probe setting t in T at which "
        "the conditioned family differs (ONE SETTING WHEN Inp_S IS EMPTY, by "
        "Definition def:probe)'. n = 0 is in 0 <= n <= N for every declared "
        "N >= 0. FROZEN as R5-PASS-VACUUM-BLOCK-N0. An implementation that "
        "skipped the one-dimensional blocks would report a maximum over a "
        "smaller set, which is not the quantity Eq. eq:res5 defines.",
    ),
)


# ===========================================================================
#  THE 0.3.0 AMENDMENT -- run A's freeze of the exact window
# ===========================================================================
#
#  Everything from here to the registry tuple was derived BY HAND from
#  contract.tex 0.3.0 (sha256
#  3b8853f6ba77e1f90a76350fb2537656ce31c694884e1769b9a7e9fd67028f45; git blob
#  8349493327284fdeeb8343f9a9a2456d61556a90) BEFORE any code changed, in the
#  two-instance implementation band the freeze rule requires.
#  IT IS PURELY ADDITIVE: not one value frozen at 0.1.3 or at 0.2.0 is edited or
#  deleted. Where the amendment invalidates an earlier object's SHAPE or
#  EXPECTED VALUE, or leaves its framing stale, the object is MARKED in
#  SUPERSEDED_BY_0_3_0 below with the contract site and its replacement, and
#  run B retires or rewrites it deliberately.
#
#  NOT ONE FROZEN p_mc, WINDOW MINIMUM, TAIL OR RESIDUAL GAP OF BOUND_DATA_CASES
#  IS SUPERSEDED, and the reason is the amendment's own opt-in rule rather than
#  an accident. Definition def:pmc's closing paragraph: "A declaration carrying
#  no depth at any setting is governed by Eq. eq:pmcdef ALONE: no beta* is
#  formed, no eigenvalue of any block above the cutoff is computed, and
#  Assumption ass:eig is not invoked." Every one of the fourteen frozen
#  bound-data cases declares no `exact_window` depth -- the key did not exist
#  when they were frozen -- so every one of them is still exactly what 0.3.0
#  emits. BD-BB84-N1-ZERO (p_mc = 0), BD-BB84-N2 (1/2), BD-BB84-N3 (3/4) and
#  BD-BB84-PZ-QUARTER-N2 (1/8) are named here because they are the cases the
#  exact window would change IF a depth were declared, and the 0.3.0 successors
#  that show it are EX-BB84-N1-M2-EIG-ZERO, EX-BB84-N2-M3-EIG-ZERO and
#  EX-BB84-PZ-QUARTER-N1-M2. THE TWO SETS COEXIST: they are different
#  declarations of the same device.
#
#  WHAT WAS RE-DERIVED FROM SCRATCH RATHER THAN CARRIED. Every eigenvalue below
#  was computed by hand from Eq. eq:exactbnd on the constructed receiver, not
#  read off Example ex:bb84exact's closed form: the n = 2 spectrum from the
#  projector decomposition Eq. eq:bb84exactvec, the n = 3 spectrum from the
#  4 x 4 matrix in the occupation basis {|3_H>, |2_H 1_V>, |1_H 2_V>, |3_V>}
#  that Section 2.5 `subsystem_order` fixes. The closed form
#  beta*(2) = 1 - p_Z^2 - p_X^2 is then a CHECK on the derivation and not its
#  source, and it is recorded as such on each case.
#
#  THE DECLARED TOLERANCES ARE A FIXTURE, AS BEFORE. TOLERANCE_FIXTURE_0_3_0
#  plays the role of the declared input for every case below, exactly as
#  TOLERANCE_FIXTURE_0_2_0 did, and for the same reason: Section 2.1 makes the
#  tuple "declared, never defaulted", so a frozen expected value carrying a
#  tolerance of its own invention would invent the one input the contract
#  insists on being given. eps_eig is the one member that is NOT a threshold --
#  it is subtracted -- so several cases below vary it deliberately and say so.

# ---------------------------------------------------------------------------
#  The declared tolerance tuple at 0.3.0, AS A FIXTURE
# ---------------------------------------------------------------------------
#
#  EIGHT members where 0.2.0 had six: eps_6 and eps_eig are added, and NOTHING
#  is removed (Section 1.1, "Interface deltas"). SIX are required on every
#  declaration -- eps_1..eps_5 and eps_gap, exactly the 0.2.0 six -- and TWO are
#  required EXACTLY where an `exact_window` depth is declared. Every member lies
#  in the declared domain [0, 1) (Section 2.1; Rem. rem:tolerancedomain), and
#  the values are round rationals chosen only so that a reader can see the
#  verdicts do not turn on them.

#: The declared tolerance tuple of contract.tex 0.3.0, as a fixture.
TOLERANCE_FIXTURE_0_3_0: dict[str, F] = {
    "eps_1": F(1, 1000),
    "eps_2": F(1, 1000),
    "eps_3": F(1, 1000),
    "eps_4": F(1, 1000),
    "eps_5": F(1, 1000),
    "eps_6": F(1, 1000),
    "eps_gap": F(1, 100),
    "eps_eig": F(1, 1000),
}

#: Which members are required on EVERY declaration and which only on the opt-in
#: route. Section 2.1: the tuple is "six reals in [0, 1) always, TWO MORE ON THE
#: OPT-IN ROUTE", and eps_6 and eps_eig are "required exactly where an
#: exact_window depth is declared, refused when missing there, and NEITHER
#: REQUIRED NOR AN ERROR when no depth is declared anywhere".
TOLERANCES_ALWAYS_REQUIRED_0_3_0: tuple[str, ...] = (
    "eps_1",
    "eps_2",
    "eps_3",
    "eps_4",
    "eps_5",
    "eps_gap",
)

#: The two conditionally required members, with the condition they are required
#: under, verbatim from Section 2.1.
TOLERANCES_CONDITIONALLY_REQUIRED_0_3_0: tuple[tuple[str, str], ...] = (
    (
        "eps_6",
        "required exactly where an `exact_window` depth is declared; it bounds "
        "the residual r_6 of Eq. eq:res6",
    ),
    (
        "eps_eig",
        "required exactly where an `exact_window` depth is declared; it DECIDES "
        "NOTHING and is SUBTRACTED from a computed eigenvalue in Eq. eq:elldef, "
        "and it is the one input on which Ass. ass:eig is stated",
    ),
)

#: A SECOND fixture, for the Def. def:tolmap (iv) band alone. The main fixture
#: declares eps_1 = eps_2 = 1/1000, which EMPTIES Eq. eq:tolmapband -- item (v)
#: closes with exactly that observation, "a declarer who wants one slack on
#: lmax(A_Sigma) regardless of route declares eps_1 = eps_2, WHICH ALSO EMPTIES
#: Eq. eq:tolmapband". The band is only reachable at eps_1 > eps_2, "the
#: ORDINARY declaration" in item (iv)'s own words, so it gets its own fixture.
TOLMAP_IV_BAND_FIXTURE: dict[str, F] = {
    "eps_1": F(1, 100),
    "eps_2": F(1, 1000),
}

#: The band Eq. eq:tolmapband at that fixture, as the half-open interval it is:
#: c in [-eps_1, -eps_2). CLOSED at the left, OPEN at the right.
TOLMAP_IV_BAND: tuple[F, F] = (F(-1, 100), F(-1, 1000))

#: Whether the endpoints belong: -eps_1 does, -eps_2 does not.
TOLMAP_IV_BAND_CLOSED_AT: tuple[bool, bool] = (True, False)


# ---------------------------------------------------------------------------
#  The reason strings contract.tex 0.3.0 SPELLS
# ---------------------------------------------------------------------------

#: The EIGHT machine-readable REFUSAL reasons of Section 2.6, in the table's own
#: order: the five of 0.2.0 unchanged, then the three the exact window adds.
#: Transcribed character for character; the LaTeX `\allowbreak` macros in the
#: source are line-break hints and are not part of the key.
REFUSAL_REASONS_VERBATIM_0_3_0: tuple[str, ...] = (
    "dark_count_channel_declared_twice",
    "splitting_ratio_presentation_unsupported",
    "port_gram_rank_exceeds_port_size",
    "photon_block_positivity_residual_above_tolerance",
    "tolerance_outside_declared_domain",
    "exact_window_declared_without_required_tolerance",
    "exact_window_depth_outside_declared_range",
    "window_eigenvalue_consistency_residual_above_tolerance",
)

#: The three the amendment adds, named separately so that a reader can see the
#: delta without differencing two tuples.
REFUSAL_REASONS_ADDED_AT_0_3_0: tuple[str, ...] = (
    "exact_window_declared_without_required_tolerance",
    "exact_window_depth_outside_declared_range",
    "window_eigenvalue_consistency_residual_above_tolerance",
)

#: The key vocabulary at 0.3.0: the eight refusals plus the one tier fallback.
#: NO TENTH STRING IS SPELLED ANYWHERE IN contract.tex 0.3.0, and none is
#: invented here. TIER_FALLBACK_REASON_VERBATIM is the 0.2.0 object and is
#: unchanged -- the fallback string is byte-identical across all three versions.
REASON_VOCABULARY_0_3_0: tuple[str, ...] = (
    *REFUSAL_REASONS_VERBATIM_0_3_0,
    TIER_FALLBACK_REASON_VERBATIM,
)

#: Which of the nine emits an artifact. The eight refusals do not ("a refusal
#: with a machine-readable reason and NO artifact", Section 2.5 `fail_closed`);
#: the fallback does, at the lower tier.
REASON_EMITS_ARTIFACT_0_3_0: tuple[tuple[str, bool], ...] = tuple(
    (reason, reason == TIER_FALLBACK_REASON_VERBATIM)
    for reason in REASON_VOCABULARY_0_3_0
)

# An ADDITION (hand-written, as is every value here) beside the three frozen
# objects above, none of which is touched, in the pattern of
# MATHEMATICAL_SPEC_VERSION_RECEIVER_0_1_2. REASON_VOCABULARY_0_3_0 is what the
# contract 0.3.0 SPELLED and stays the nine; the two objects below
# say what THIS REPOSITORY'S `receiver` module carries: `receiver_grams_not_enclosed`
# is not in `RefusalReason`. The
# `certified` rung that was the only way to reach it is dropped by
# PRINCIPLES.md section 10, so the string is unreachable and is recorded only
# in this frozen file.
#: The reason spellings of the contract that THE CODE CARRIES:
#: the nine minus the retired tier fallback, which is the eight refusals.
REASON_VOCABULARY_RECEIVER_0_1_2: tuple[str, ...] = tuple(
    reason
    for reason in REASON_VOCABULARY_0_3_0
    if reason != TIER_FALLBACK_REASON_VERBATIM
)

#: What is NOT in the code, frozen so that a test can assert it is no
#: longer a member of the enum and no path spells it. It stays in
#: REASON_VOCABULARY_0_3_0 and in spec/modules/receiver/interface.yaml, which
#: record the contract as frozen and not the code.
RETIRED_FROM_THE_CODE_RECEIVER_0_1_2: tuple[str, ...] = (TIER_FALLBACK_REASON_VERBATIM,)

#: The SEVEN refusals contract.tex 0.3.0 names WITHOUT a spelling. The first six
#: are Section 2.6's preamble enumeration, verbatim and in its order, unchanged
#: from 0.2.0. THE SEVENTH IS NEW AND IS NOT IN THAT PREAMBLE: Def. def:tolmap
#: (iv) now states that its failure is a refusal under `fail_closed` -- which
#: 0.2.0 omitted -- and adds no reason string, in terms: "The reason string is
#: THE IMPLEMENTER'S TO NAME ... and THIS AMENDMENT DELIBERATELY ADDS NONE,
#: because fixing a contract-verbatim key here would settle an interface detail
#: that no claim of this contract consumes." None is invented here.
#: (condition, stated at)
REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0: tuple[tuple[str, str], ...] = (
    ("two input routes supplied at once", "Section 2.1 preamble"),
    ("a violated condition (E1), (E2) or (E3)", "Def. def:graph; Thm. thm:compilation-well-defined (iv)"),
    ("a non-zero `tolerance` field", "Section 2.4, second bullet; Ass. ass:exact"),
    ("a missing or too-small m_t", "Section 2.1 `tail_window`; Def. def:pmc"),
    ("a missing declared tolerance", "Section 2.1 `numerical_tolerances`"),
    (
        "a probe state outside the Gaussian tier",
        "Def. def:probe; Req. req:probe-diagonal-admission",
    ),
    (
        "bound data whose computed c falls below -eps_2, which includes the "
        "whole band c in [-eps_1, -eps_2) that item (v)'s test would admit",
        "Def. def:tolmap (iv), 'The failure is a refusal'",
    ),
)

#: The SEVENTEEN convention bullets of Section 2.5 at 0.3.0 -- THE SAME
#: SEVENTEEN AS AT 0.2.0, in the same order. No bullet is added and none is
#: removed; EXACTLY TWO change text (`numerical_tolerance_assignment` and the
#: version bullet). Counted mechanically in contract.tex as seventeen `\item` at
#: column zero inside the itemize of sec:conventions.
CONVENTION_KEYS_0_3_0: tuple[str, ...] = CONVENTION_KEYS_0_2_0

#: The FIFTEEN input key names at 0.3.0. FOURTEEN at 0.2.0 plus `exact_window`,
#: which Section 2.1 places in its own tabular between `tail_window` and
#: `numerical_tolerances`. Section 1.1's delta paragraph: "Added: the declared
#: depth {m*_t} (exact_window), optional per setting ... Removed: nothing."
INPUT_KEYS_0_3_0: tuple[str, ...] = (
    "mode_space",
    "input_modes",
    "port_map",
    "port_grams",
    "instrument_matrix",
    "element_graph",
    "detector_layer",
    "dark_count_channel",
    "probe_declaration",
    "photon_cutoff",
    "tail_window",
    "exact_window",
    "numerical_tolerances",
    "outcome_coarse_graining",
    "requested_assurance",
)

#: The FIFTEEN output key names at 0.3.0 -- THE SAME FIFTEEN AS AT 0.2.0. What
#: THREE of them CONTAIN changes (`high_photon_bounds`,
#: `bound_quantifier_domain`, `validation_results`); no key is added or removed.
OUTPUT_KEYS_0_3_0: tuple[str, ...] = OUTPUT_KEYS

#: The THIRTEEN assumption ledger rows at 0.3.0: the twelve of 0.2.0 unchanged
#: plus A-EIG. Its Supports cell reads "RC9 (v), and the exact-window branch of
#: RC8", so it reaches RC8 and RC9 and no other claim.
ASSUMPTION_ROWS_0_3_0: tuple[AssumptionRow, ...] = (
    *ASSUMPTION_ROWS,
    AssumptionRow(
        assumption_id="A-EIG",
        machine_key="exact_window_eigenvalue_slack",
        supports=("RC8", "RC9"),
        never_verified=True,
    ),
)

#: The NEVER-VERIFIED set at 0.3.0: THREE, where 0.2.0 had two, and the third is
#: of a different KIND. Section 5's preamble: "Two of these (ass:trust and
#: ass:modes) are DEVICE statements that this module names and can never verify.
#: A THIRD, Assumption ass:eig, is A STATEMENT ABOUT THE ARITHMETIC, is likewise
#: never verified here, and IS INVOKED ONLY WHERE A CALLER DECLARES AN
#: EXACT-WINDOW DEPTH -- a declaration that does not is unaffected by it."
#: (assumption id, kind, conditional on a declaration)
NEVER_VERIFIED_0_3_0: tuple[tuple[str, str, bool], ...] = (
    ("A-TRUST", "device", False),
    ("A-MODES", "device", False),
    ("A-EIG", "arithmetic", True),
)

#: The version string the artifact binds at 0.3.0 (Section 2.5, last bullet;
#: Section 2.2 `mathematical_spec_version`, "of the ACCEPTED contract").
MATHEMATICAL_SPEC_VERSION_0_3_0: str = "receiver-povm@0.3.0"

# An ADDITION beside the frozen value above, which is not touched. The value
# above is what the 0.3.0 freeze bound and stays that; the value
# below is what the code binds (spec/modules/receiver/module.yaml, accepted
# 0.1.2). Both are written by hand and neither is regenerated from the code
# they test.
#: The version string the artifact binds IN THIS REPOSITORY: the module id is
#: `receiver` here where the frozen string has `receiver-povm`, and the version
#: is spec/modules/receiver/module.yaml's accepted 0.1.2.
MATHEMATICAL_SPEC_VERSION_RECEIVER_0_1_2: str = "receiver@0.1.2"

#: WHAT RUN A FOUND IN THE TREE AND DID NOT REPAIR. contract.tex's own version
#: macro still reads `0.3.0-draft` (\ContractVersion, line 198) after the G3
#: signature, while STATUS.yaml reads `contract_version: 0.3.0`,
#: `state: accepted` and gates.g3 `signed_version: "0.3.0"`. Dropping the suffix
#: at the signature is the TYPOGRAPHIC CORRECTION permitted in place, and this module executed it at both previous signatures. It
#: is routed to the driver as interface.yaml `observations_routed` OBS-1 and is
#: NOT a change request against the mathematics: no claim, no bound and no
#: emitted value depends on it. The registry and interface.yaml both bind the
#: ACCEPTED version, on STATUS.yaml's authority.
#: (what, where, what this freeze did)
CONTRACT_VERSION_RESIDUE_0_3_0: tuple[str, str, str] = (
    "contract.tex \\ContractVersion still reads `0.3.0-draft`",
    "contract.tex line 198; STATUS.yaml contract_version and gates.g3 say 0.3.0",
    "BOUND `receiver-povm@0.3.0` on STATUS.yaml's authority and ROUTED the "
    "residue to the driver; contract.tex is frozen at G3 and the implementer "
    "does not edit it.",
)


# ---------------------------------------------------------------------------
#  Group RP-S -- the exact block quantity beta*(n) (RC8)
# ---------------------------------------------------------------------------
#
#  Definition def:exactbnd, Eq. eq:exactbnd:
#
#      beta*(n) = lmin(blk M^{(=n)}_mc)
#               = lmin( id^{(=n)} + (K-1) gamma Fock(id - B)^{(n)}
#                                 - sum_k beta_k Fock(id - B_k)^{(n)} )
#
#  "The operator inside is a Hermitian matrix of dimension binom(D + n - 1, n),
#  where D is the dimension of the space B acts on: D = |Inp_C| at every
#  declared setting." AND: "NO NEW OBJECT IS INTRODUCED. Each Fock(.)^{(n)} is
#  the construction Eq. eq:blockMS ALREADY USES for the blocks the artifact
#  emits at n <= N, in the occupation basis and order Definition def:fock and
#  Section 2.5 fix, EVALUATED AT AN INDEX ABOVE THE CUTOFF INSTEAD OF BELOW IT."
#
#  LEMMA lem:exactbasic HAS TWO HALVES AND THEY NEED DIFFERENT HYPOTHESES, which
#  is the substance of Round-11 finding F-11-01 and is why the lemma is stated
#  in two parts:
#
#      Eq. eq:exactbasic   beta(n) <= beta*(n) <= 1
#                          from thm:multiclick-bound's hypotheses ALONE -- the lower
#                          half is Eq. eq:mcbound, the upper half is the
#                          operator form Eq. eq:mcupper of that theorem's own
#                          beta <= 1 argument;
#
#      beta*(n) >= 0       ONLY under the ADDED hypothesis Eq. eq:mcpos,
#                          M_mc >= 0.
#
#  Remark rem:exactpositivity is the instance that shows the second half is not
#  free, and it is frozen below as EB-POSITIVITY-COUNTEREXAMPLE-N1 and -N2.
#
#  EVERY SPECTRUM BELOW WAS COMPUTED FROM THE CONSTRUCTED RECEIVER, not read off
#  a closed form. Where Example ex:bb84exact states a closed form, it appears in
#  `derives_from` as a CHECK on the hand computation.


@dataclass(frozen=True)
class ExactBlockCase:
    """One exact block minimum eigenvalue beta*(n) (Def. def:exactbnd)."""

    case_id: str
    #: The receiver, by the identifier the 0.1.3 sections use for it.
    receiver: str
    #: The photon-number block index n. Above the cutoff wherever it is used.
    photon_number: int
    #: D = |Inp_C|, the dimension of the space B acts on (Def. def:exactbnd).
    channel_modes: int
    #: binom(D + n - 1, n), the dimension of the Hermitian matrix.
    block_dimension: int
    #: The full spectrum of blk M^{(=n)}_mc, ASCENDING, with multiplicity.
    spectrum: tuple[F, ...]
    #: beta*(n) = lmin, the first entry of `spectrum`.
    beta_star: F
    #: beta(n) of Eq. eq:beta on the same bound data.
    beta_analytic: F
    #: beta*(n) - beta(n) >= 0, the slack Eq. eq:mcbound leaves.
    gap: F
    #: Whether Eq. eq:mcpos holds -- i.e. whether M_mc is a sum of POVM
    #: elements at this receiver (Thm. thm:emitted-bound discharges it there).
    mcpos_holds: bool
    derives_from: str


EXACT_BLOCK_CASES: tuple[ExactBlockCase, ...] = (
    ExactBlockCase(
        case_id="EB-BB84-N2-PZ-HALF",
        receiver="I-BB84 (channel-only, Ex. ex:bb84bound)",
        photon_number=2,
        channel_modes=2,
        block_dimension=3,
        spectrum=(F(1, 2), F(3, 4), F(3, 4)),
        beta_star=F(1, 2),
        beta_analytic=F(0),
        gap=F(1, 2),
        mcpos_holds=True,
        derives_from=(
            "THE CENTRAL CASE OF THE AMENDMENT, DERIVED FROM THE CONSTRUCTED "
            "RECEIVER. I-BB84 is the channel-only receiver of the last "
            "paragraph of Example ex:bb84: K = 4, gamma = beta_k = 1, "
            "Inp_C = {Chan_H, Chan_V} so D = 2, and the Grams Eq. eq:bb84grams "
            "A_H = p_Z |H><H|, A_V = p_Z |V><V|, A_+ = p_X |+><+|, "
            "A_- = p_X |-><-| with A_Sigma = id_2.\n"
            "THE BOUND DATA. B = A_Sigma = id_2 and B_k = A_{[4] minus {k}} = "
            "id - A_k, so id - B = 0 and id - B_k = A_k. Eq. eq:exactbnd then "
            "reads, for n >= 1,\n"
            "  blk M^{(=n)}_mc = id^{(=n)} - sum_k Fock(A_k)^{(n)}\n"
            "                  = id^{(=n)} - p_Z^n (|n_H><n_H| + |n_V><n_V|)\n"
            "                                - p_X^n (|n_+><n_+| + |n_-><n_-|),\n"
            "by two steps: Fock(0)^{(n)} = 0 for n >= 1 kills the gamma term; "
            "and for a rank-one A_k = p |psi><psi|, (p |psi><psi|)^{tensor n} "
            "is p^n times the projector onto (span |psi|)^{tensor n}, whose "
            "restriction to Sym^n is |n_psi><n_psi| (Lem. lem:fock-functor (iv)).\n"
            "THE TWO-PHOTON BLOCK, BY HAND. Sym^2(C^2) has dimension "
            "binom(2 + 2 - 1, 2) = 3 and occupation basis "
            "{|2_H>, |1_H 1_V>, |2_V>} in the lexicographic order Section 2.5 "
            "`subsystem_order` fixes. Then\n"
            "  |2_H><2_H| + |2_V><2_V| = id - |1_H 1_V><1_H 1_V|,\n"
            "  |2_+><2_+| + |2_-><2_-| = id - |1_+ 1_-><1_+ 1_-|,\n"
            "and expanding |+-> = (|H> +- |V>)/sqrt2,\n"
            "  |1_+ 1_-> = (|+> tensor |-> + |-> tensor |+>)/sqrt2\n"
            "            = (|2_H> - |2_V>)/sqrt2   (Eq. eq:bb84exactvec),\n"
            "which is ORTHOGONAL to |1_H 1_V>. Substituting,\n"
            "  blk M^{(=2)}_mc = (1 - p_Z^2 - p_X^2) id\n"
            "                    + p_Z^2 |1_H 1_V><1_H 1_V|\n"
            "                    + p_X^2 |1_+ 1_-><1_+ 1_-|,\n"
            "whose spectrum is therefore {1 - p_X^2, 1 - p_Z^2, "
            "1 - p_Z^2 - p_X^2} -- the first two on the two displayed "
            "orthonormal vectors and the third on (|2_H> + |2_V>)/sqrt2.\n"
            "AT p_Z = p_X = 1/2: 1 - p_X^2 = 3/4, 1 - p_Z^2 = 3/4, and "
            "1 - 1/4 - 1/4 = 1/2. SPECTRUM {1/2, 3/4, 3/4}, so "
            "beta*(2) = 1/2.\n"
            "AGAINST THE ANALYTIC BOUND. Eq. eq:bb84beta gives "
            "beta(n) = 1 - 2 p_Z^n - 2 p_X^n = 1 - 2^{2-n} at p_Z = 1/2, so "
            "beta(2) = 0 and the gap is 1/2 -- HALF THE BLOCK'S WEIGHT, "
            "DISCARDED BY Eq. eq:pmcdef AT THE CUTOFF N = 1. Section 1.1 states "
            "exactly this as the defect the amendment answers, and Eq. "
            "eq:bb84exactvalue records the closed form "
            "beta*(2) = 1 - p_Z^2 - p_X^2 against beta(2) = 1 - 2p_Z^2 - 2p_X^2 "
            "with 'a gap of p_Z^2 + p_X^2 > 0 at every (p_Z, p_X)'. THAT CLOSED "
            "FORM IS A CHECK ON THE COMPUTATION ABOVE AND NOT ITS SOURCE: "
            "p_Z^2 + p_X^2 = 1/4 + 1/4 = 1/2, which is the gap frozen here.\n"
            "Eq. eq:mcpos HOLDS: M_mc = sum over S in MC_K of M_S is a sum of "
            "elements of a POVM (Thm. thm:click-povm (i), no probe declared), so "
            "beta*(2) in [0, 1] by Lem. lem:exactbasic."
        ),
    ),
    ExactBlockCase(
        case_id="EB-BB84-N2-PZ-SEVEN-TENTHS",
        receiver="I-BB84 (channel-only, Ex. ex:bb84bound)",
        photon_number=2,
        channel_modes=2,
        block_dimension=3,
        spectrum=(F(21, 50), F(51, 100), F(91, 100)),
        beta_star=F(21, 50),
        beta_analytic=F(-4, 25),
        gap=F(29, 50),
        mcpos_holds=True,
        derives_from=(
            "THE SAME BLOCK AT A SECOND p_Z, so that the closed form is checked "
            "at more than one point and the spectrum is not a coincidence of "
            "the symmetric case. p_Z = 7/10, p_X = 3/10.\n"
            "SPECTRUM, from the same decomposition: 1 - p_X^2 = 1 - 9/100 = "
            "91/100; 1 - p_Z^2 = 1 - 49/100 = 51/100; and "
            "1 - p_Z^2 - p_X^2 = 1 - 49/100 - 9/100 = 42/100 = 21/50. "
            "ASCENDING: {21/50, 51/100, 91/100}, so beta*(2) = 21/50.\n"
            "THE ANALYTIC BOUND: beta(2) = 1 - 2(49/100) - 2(9/100) = "
            "1 - 116/100 = -16/100 = -4/25, NEGATIVE. The gap is "
            "21/50 + 4/25 = 21/50 + 8/50 = 29/50, and the closed-form check "
            "p_Z^2 + p_X^2 = 49/100 + 9/100 = 58/100 = 29/50 AGREES.\n"
            "WHY THIS ONE MATTERS. At an unbalanced basis choice the analytic "
            "bound is not merely slack, it is NEGATIVE, so Eq. eq:pmcdef's "
            "outer max{0, .} emits ZERO at the cutoff N = 1 while 21/50 of the "
            "two-photon block's weight is guaranteed."
        ),
    ),
    ExactBlockCase(
        case_id="EB-BB84-N2-PZ-QUARTER",
        receiver="I-BB84 (channel-only, Ex. ex:bb84bound)",
        photon_number=2,
        channel_modes=2,
        block_dimension=3,
        spectrum=(F(3, 8), F(7, 16), F(15, 16)),
        beta_star=F(3, 8),
        beta_analytic=F(-1, 4),
        gap=F(5, 8),
        mcpos_holds=True,
        derives_from=(
            "A THIRD p_Z, AT THE RECEIVER BD-BB84-PZ-QUARTER-N2 ALREADY "
            "FREEZES ANALYTICALLY. p_Z = 1/4, p_X = 3/4.\n"
            "SPECTRUM: 1 - p_X^2 = 1 - 9/16 = 7/16; 1 - p_Z^2 = 1 - 1/16 = "
            "15/16; 1 - p_Z^2 - p_X^2 = 1 - 1/16 - 9/16 = 6/16 = 3/8. "
            "ASCENDING: {3/8, 7/16, 15/16}, so beta*(2) = 3/8.\n"
            "THE ANALYTIC BOUND: beta(2) = 1 - 2(1/16) - 2(9/16) = "
            "1 - 20/16 = -4/16 = -1/4, which is the value BD-BB84-PZ-QUARTER-N2 "
            "already freezes. The gap is 3/8 + 1/4 = 5/8, and the closed-form "
            "check p_Z^2 + p_X^2 = 1/16 + 9/16 = 10/16 = 5/8 AGREES.\n"
            "NOTE THAT BD-BB84-PZ-QUARTER-N2 IS NOT SUPERSEDED BY THIS CASE. "
            "That case declares NO exact-window depth and takes cutoff N = 2, "
            "where Eq. eq:pmcdef emits max{0, beta(3)} = 1/8; this case is the "
            "exact two-photon block of the same device, which a DIFFERENT "
            "declaration would read at N = 1. The two coexist."
        ),
    ),
    ExactBlockCase(
        case_id="EB-BB84-N3-PZ-HALF",
        receiver="I-BB84 (channel-only, Ex. ex:bb84bound)",
        photon_number=3,
        channel_modes=2,
        block_dimension=4,
        spectrum=(F(13, 16), F(13, 16), F(15, 16), F(15, 16)),
        beta_star=F(13, 16),
        beta_analytic=F(1, 2),
        gap=F(5, 16),
        mcpos_holds=True,
        derives_from=(
            "A SECOND INDEX, AND THE ONE THE CONTRACT DOES NOT WORK OUT. "
            "Example ex:bb84exact stops at n = 2; the three-photon block is "
            "derived here from Eq. eq:exactbnd directly, in the occupation "
            "basis {|3_H>, |2_H 1_V>, |1_H 2_V>, |3_V>} of Sym^3(C^2), of "
            "dimension binom(2 + 3 - 1, 3) = 4.\n"
            "THE TWO PROJECTORS. P_Z := |3_H><3_H| + |3_V><3_V| = "
            "diag(1, 0, 0, 1). For P_X := |3_+><3_+| + |3_-><3_-|, expand\n"
            "  |3_+> = |+>^{tensor 3} = (|3_H> + sqrt3 |2_H 1_V> "
            "+ sqrt3 |1_H 2_V> + |3_V>) / (2 sqrt2),\n"
            "  |3_-> = |->^{tensor 3} = (|3_H> - sqrt3 |2_H 1_V> "
            "+ sqrt3 |1_H 2_V> - |3_V>) / (2 sqrt2),\n"
            "the sqrt3 being the normalization of the symmetrized occupation "
            "vectors (three terms each) and the signs (-1)^{#V}. Both are unit "
            "vectors, (1 + 3 + 3 + 1)/8 = 1, and they are ORTHOGONAL, "
            "(1 - 3 + 3 - 1)/8 = 0, so P_X is a rank-2 orthogonal projector. "
            "Its matrix is\n"
            "  P_X = (1/4) [[1, 0, sqrt3, 0], [0, 3, 0, sqrt3], "
            "[sqrt3, 0, 3, 0], [0, sqrt3, 0, 1]],\n"
            "with trace 1/4 + 3/4 + 3/4 + 1/4 = 2, as a rank-2 projector must "
            "have.\n"
            "THE BLOCK AT p_Z = p_X = 1/2, where p_Z^3 = p_X^3 = 1/8:\n"
            "  M = id - (1/8) P_Z - (1/8) P_X,\n"
            "  M_11 = M_44 = 1 - 1/8 - 1/32 = 27/32,\n"
            "  M_22 = M_33 = 1 - 3/32 = 29/32,\n"
            "  M_13 = M_31 = M_24 = M_42 = -sqrt3/32, all other entries 0.\n"
            "IT DECOUPLES INTO TWO 2x2 BLOCKS, on {|3_H>, |1_H 2_V>} and on "
            "{|2_H 1_V>, |3_V>}. Each has trace 56/32 = 7/4, hence mean 7/8, "
            "half-difference 1/32 and off-diagonal magnitude sqrt3/32, so its "
            "eigenvalues are\n"
            "  7/8 +- sqrt( (1/32)^2 + (sqrt3/32)^2 ) = 7/8 +- sqrt(4/1024) "
            "= 7/8 +- 1/16,\n"
            "that is 15/16 and 13/16. BOTH blocks give the same pair, so the "
            "spectrum is {13/16, 13/16, 15/16, 15/16} and beta*(3) = 13/16. "
            "TRACE CHECK: 2(13/16) + 2(15/16) = 7/2, against "
            "tr M = 4 - 2/8 - 2/8 = 7/2. THEY AGREE.\n"
            "AGAINST THE ANALYTIC BOUND: beta(3) = 1 - 2^{2-3} = 1/2, so the "
            "gap is 13/16 - 8/16 = 5/16. THE sqrt3 CANCELS EXACTLY and the "
            "answer is rational, which is why n = 3 is frozen at p_Z = 1/2 and "
            "at no other p_Z: at p_Z = 7/10 the same computation gives "
            "163/200 - sqrt(436468)/4000 with 436468 = 4 x 19 x 5743, which is "
            "NOT in Q[sqrt2] and could not be frozen exactly in this file's "
            "ring. Saying so is part of the derivation."
        ),
    ),
    ExactBlockCase(
        case_id="EB-BS-N2",
        receiver="I-BS (two detectors, ONE channel input mode, no probe)",
        photon_number=2,
        channel_modes=1,
        block_dimension=1,
        spectrum=(F(1, 2),),
        beta_star=F(1, 2),
        beta_analytic=F(1, 2),
        gap=F(0),
        mcpos_holds=True,
        derives_from=(
            "THE CASE WHERE THE EXACT WINDOW BUYS NOTHING, AND IT IS NOT AN "
            "EDGE CASE -- it is every receiver with a one-dimensional channel "
            "space. I-BS has D = |Inp_C| = 1, so Sym^n(C^1) has dimension "
            "binom(1 + n - 1, n) = 1 at EVERY n and every block is a scalar.\n"
            "THE BOUND DATA (BD-BS-N1): K = 2, gamma = beta_k = 1, "
            "A_1 = A_2 = 1/2, so A_Sigma = 1 gives B = 1, c = 1 - 1 = 0, and "
            "B_k = A_{[2] minus {k}} = 1/2 gives d_k = 1 - 1/2 = 1/2.\n"
            "THE BLOCK, from Eq. eq:exactbnd with scalars: id - B = 0 and "
            "id - B_k = 1/2, so\n"
            "  blk M^{(=n)}_mc = 1 + 1 * 0^n - 2 * (1/2)^n = 1 - 2^{1-n} "
            "for n >= 1,\n"
            "WHICH IS beta(n) ITSELF. So beta*(n) = beta(n) at every n, the "
            "gap is 0, and Eq. eq:mcbound holds WITH EQUALITY. At n = 2: "
            "beta*(2) = beta(2) = 1 - 2^{-1} = 1/2.\n"
            "FROZEN BECAUSE AN IMPLEMENTATION MUST NOT 'IMPROVE' IT. "
            "Prop. prop:exactnoworse says the exact window is never worse; it "
            "does not say it is ever better, and here it is exactly equal. The "
            "0.1.3 entry for BD-BS-N1 already said 'HERE THE BOUND IS THE "
            "EIGENVALUE', and this case is that sentence made into an "
            "Eq. eq:exactbnd evaluation."
        ),
    ),
    ExactBlockCase(
        case_id="EB-BS-N3",
        receiver="I-BS (two detectors, ONE channel input mode, no probe)",
        photon_number=3,
        channel_modes=1,
        block_dimension=1,
        spectrum=(F(3, 4),),
        beta_star=F(3, 4),
        beta_analytic=F(3, 4),
        gap=F(0),
        mcpos_holds=True,
        derives_from=(
            "THE SAME RECEIVER ONE INDEX UP, so that the equality is seen to "
            "hold at more than one n rather than at a lucky one: "
            "beta*(3) = beta(3) = 1 - 2^{1-3} = 1 - 1/4 = 3/4, the block again "
            "being one dimensional. beta* is INCREASING here, which is what "
            "Lem. lem:collapse gives for beta once beta(N+1) >= 0."
        ),
    ),
    ExactBlockCase(
        case_id="EB-PROBE-OFF-N2",
        receiver="I-PROBE at the VACUUM setting (predicate (X), second clause)",
        photon_number=2,
        channel_modes=1,
        block_dimension=1,
        spectrum=(F(1, 8),),
        beta_star=F(1, 8),
        beta_analytic=F(1, 8),
        gap=F(0),
        mcpos_holds=True,
        derives_from=(
            "THE PROBE-OFF SETTING OF BD-PROBE-OFF-N1, where "
            "Thm. thm:gaussian-schur (iii) gives gamma = beta_k = 1 exactly and the "
            "conditioned Grams are the channel blocks: B = 1/2, B_k = 1/4, so "
            "c = 1/2 and d_k = 3/4. D = |Inp_C| = 1, so the block is again a "
            "scalar and\n"
            "  blk M^{(=n)}_mc = 1 + 1 * (1/2)^n - 2 * (3/4)^n = beta(n).\n"
            "At n = 2: 1 + 1/4 - 2(9/16) = 1 + 1/4 - 9/8 = 1/8. beta*(2) = "
            "beta(2) = 1/8, gap 0. Eq. eq:mcpos holds by "
            "Thm. thm:conditional-povm (ii)."
        ),
    ),
    ExactBlockCase(
        case_id="EB-PROBE-ON-N2",
        receiver="I-PROBE at the THERMAL setting nbar = 1 (predicate (X) FAILS)",
        photon_number=2,
        channel_modes=1,
        block_dimension=1,
        spectrum=(F(107, 750),),
        beta_star=F(107, 750),
        beta_analytic=F(107, 750),
        gap=F(0),
        mcpos_holds=True,
        derives_from=(
            "THE BRANCH-2 SETTING OF BD-PROBE-ON-N1-M3, frozen so that the "
            "exact window is exercised where PREDICATE (X) FAILS and not only "
            "where it holds. gamma = 2/3, beta_1 = beta_2 = 4/5, B = 1/2, "
            "B_1 = B_2 = 1/5, so c = 1/2 and d_k = 4/5, and D = |Inp_C| = 1.\n"
            "THE BLOCK: 1 + (K-1) gamma (1 - B)^n - sum_k beta_k (1 - B_k)^n "
            "= 1 + (2/3)(1/2)^n - 2(4/5)(4/5)^n = beta(n), the block being a "
            "scalar. At n = 2: 1 + 1/6 - 128/125 = (750 + 125 - 768)/750 = "
            "107/750, which is the value BD-PROBE-ON-N1-M3 already freezes for "
            "beta(2). beta*(2) = beta(2), gap 0.\n"
            "Eq. eq:mcpos HOLDS AT A PROBE-ON SETTING TOO: Thm. thm:emitted-bound "
            "discharges it 'at every setting, because M_{mc|t} = sum over S in "
            "MC_K of M_{S|t} is a sum of elements of a POVM "
            "(Thm. thm:conditional-povm (ii) with a probe declared)'."
        ),
    ),
    ExactBlockCase(
        case_id="EB-POSITIVITY-COUNTEREXAMPLE-N1",
        receiver=(
            "Rem. rem:exactpositivity's instance (NOT a receiver of this contract)"
        ),
        photon_number=1,
        channel_modes=2,
        block_dimension=2,
        spectrum=(F(-3), F(-3)),
        beta_star=F(-3),
        beta_analytic=F(-3),
        gap=F(0),
        mcpos_holds=False,
        derives_from=(
            "REMARK rem:exactpositivity's OWN INSTANCE, frozen because it is "
            "what makes Eq. eq:mcpos a HYPOTHESIS rather than a consequence -- "
            "the substance of Round-11 finding F-11-01. Take K = 4, "
            "gamma = beta_k = 1, B = id and B_k = 0.\n"
            "EVERY HYPOTHESIS OF Thm. thm:multiclick-bound HOLDS: "
            "0 <= B_k <= B <= id reads 0 <= 0 <= id <= id, and "
            "gamma <= beta_k <= 1 reads 1 <= 1 <= 1.\n"
            "THE OPERATOR Eq. eq:prefactorform THEN DISPLAYS: "
            "M_mc = id + 3 Fock(0) - 4 Fock(id). On every block n >= 1, "
            "Fock(0)^{(n)} = 0 and Fock(id)^{(n)} = id^{(=n)}, so "
            "blk M^{(=n)}_mc = id - 4 id = -3 id^{(=n)} and "
            "beta*(n) = -3 < 0. AT n = 1 WITH D = 2 the block is 2 x 2 and the "
            "spectrum is {-3, -3}; the VALUE is independent of D, the remark "
            "saying only 'on every block n >= 1'.\n"
            "AND Thm. thm:multiclick-bound IS UNTOUCHED, WHICH IS THE POINT RATHER "
            "THAN A COINCIDENCE: the same data give c = 1 - lmax(B) = 0 and "
            "d_k = 1 - lmin(B_k) = 1, hence "
            "beta(n) = 1 + 3 * 0^n - 4 = -3 for n >= 1, and Eq. eq:mcbound "
            "HOLDS WITH EQUALITY. 'A LOWER bound on lmin needs no positivity; "
            "beta* >= 0 is a statement about the operator itself AND DOES.'\n"
            "THE UPPER HALF STILL HOLDS: beta*(1) = -3 <= 1, which is "
            "Eq. eq:exactbasic's second inequality, proved from "
            "thm:multiclick-bound's hypotheses ALONE via Eq. eq:mcupper. So this case "
            "separates the two halves of Lem. lem:exactbasic exactly.\n"
            "WHAT THE INSTANCE EXCLUDES IS THE OPERATOR, NOT THE NUMBERS: 'no "
            "receiver of this contract produces it, because there the "
            "left-hand sides of Eq. eq:prefactorform are the joint no-click "
            "elements of a POVM and M_mc is a sum of that POVM's elements.' "
            "Thm. thm:emitted-bound discharges Eq. eq:mcpos at both instances, and "
            "NO EMITTED VALUE DEPENDS ON THE DIFFERENCE."
        ),
    ),
    ExactBlockCase(
        case_id="EB-POSITIVITY-COUNTEREXAMPLE-N2",
        receiver=(
            "Rem. rem:exactpositivity's instance (NOT a receiver of this contract)"
        ),
        photon_number=2,
        channel_modes=2,
        block_dimension=3,
        spectrum=(F(-3), F(-3), F(-3)),
        beta_star=F(-3),
        beta_analytic=F(-3),
        gap=F(0),
        mcpos_holds=False,
        derives_from=(
            "THE SAME INSTANCE ONE INDEX UP, frozen so that '-3 ON EVERY BLOCK "
            "n >= 1' is checked at more than one n and not mistaken for a "
            "one-index accident. Sym^2(C^2) has dimension 3 and the block is "
            "-3 id, so the spectrum is {-3, -3, -3} and beta*(2) = -3 = "
            "beta(2). The n = 0 block is DIFFERENT and is not frozen as an "
            "ExactBlockCase because it is below every cutoff: there every "
            "Fock(.)^{(0)} = 1, so blk M^{(=0)}_mc = 1 + 3 - 4 = 0 = beta(0), "
            "which is also why Eq. eq:collapsehyp holds with equality on this "
            "data and Rem. rem:noslack's sigma = 0."
        ),
    ),
)

#: THE STRUCTURAL IDENTITY Eq. eq:bb84exactblock, frozen as a statement rather
#: than as numbers, because it is what an implementation forms before it takes
#: an eigenvalue. For the I-BB84 channel-only receiver and n >= 1:
#:   blk M^{(=n)}_mc = id^{(=n)} - p_Z^n (|n_H><n_H| + |n_V><n_V|)
#:                                - p_X^n (|n_+><n_+| + |n_-><n_-|),
#: the gamma term vanishing because Fock(0)^{(n)} = 0 for n >= 1 and each
#: Fock(A_k)^{(n)} being p^n times the rank-one occupation projector by
#: Lem. lem:fock-functor (iv). (statement, the contract site that fixes it)
BB84_EXACT_BLOCK_FORM: tuple[tuple[str, str], ...] = (
    (
        "blk M^{(=n)}_mc = id - p_Z^n (|n_H><n_H| + |n_V><n_V|) "
        "- p_X^n (|n_+><n_+| + |n_-><n_-|), for n >= 1",
        "Eq. eq:bb84exactblock",
    ),
    (
        "Fock(0)^{(n)} = 0 for n >= 1, which is why the (K-1) gamma term is "
        "absent although gamma = 1",
        "Lem. lem:fock-block-spectrum; Ex. ex:bb84exact, step one",
    ),
    (
        "for a rank-one A_k = p |psi><psi|, Fock(A_k)^{(n)} = p^n |n_psi><n_psi| "
        "with |n_psi> the occupation vector carrying all n photons in |psi>",
        "Lem. lem:fock-functor (iv) with P = |psi><psi|; Ex. ex:bb84exact, step two",
    ),
    (
        "|1_+ 1_-> = (|2_H> - |2_V>)/sqrt2, orthogonal to |1_H 1_V>",
        "Eq. eq:bb84exactvec",
    ),
    (
        "beta*(2) = 1 - p_Z^2 - p_X^2 against beta(2) = 1 - 2 p_Z^2 - 2 p_X^2, "
        "a gap of p_Z^2 + p_X^2 > 0 at every (p_Z, p_X)",
        "Eq. eq:bb84exactvalue",
    ),
    (
        "the dimension of the Hermitian matrix is binom(D + n - 1, n) with "
        "D = |Inp_C| at every declared setting",
        "Def. def:exactbnd; Thm. thm:emitted-bound, computability clause",
    ),
    (
        "NO NEW OBJECT IS INTRODUCED: each Fock(.)^{(n)} is the construction "
        "Eq. eq:blockMS already uses, in the occupation basis and order "
        "Def. def:fock and Section 2.5 fix, evaluated above the cutoff",
        "Def. def:exactbnd, closing sentences",
    ),
)

#: LEMMA lem:exactbasic, ITS TWO HALVES AND THE HYPOTHESIS EACH NEEDS. Frozen as
#: prose because what an implementation must not do is assume the second half
#: where the first is all it has. (statement, hypotheses it needs, site)
EXACTBASIC_HALVES: tuple[tuple[str, str, str], ...] = (
    (
        "beta(n) <= beta*(n)",
        "the hypotheses of Thm. thm:multiclick-bound ALONE",
        "Eq. eq:exactbasic, first inequality; it IS Eq. eq:mcbound",
    ),
    (
        "beta*(n) <= 1",
        "the hypotheses of Thm. thm:multiclick-bound ALONE",
        "Eq. eq:exactbasic, second inequality, proved by the operator form "
        "Eq. eq:mcupper of thm:multiclick-bound's own beta <= 1 argument: "
        "sum_k beta_k Fock(id - B_k) >= (sum_k beta_k) Fock(id - B) "
        ">= K gamma Fock(id - B) >= (K-1) gamma Fock(id - B), hence "
        "M_mc <= id, and the n-photon block inherits it by compression",
    ),
    (
        "beta*(n) >= 0",
        "Eq. eq:mcpos, M_mc >= 0 -- AN ADDED HYPOTHESIS, NOT A CONSEQUENCE",
        "Lem. lem:exactbasic, second sentence; Rem. rem:exactpositivity is the "
        "instance that shows it does not follow from Eq. eq:bbkhyp and "
        "Eq. eq:prefactorform",
    ),
    (
        "Eq. eq:mcpos holds at both instances of Rem. rem:twoinstances",
        "M_mc = sum over S in MC_K of M_S is a sum of elements of a POVM",
        "Lem. lem:exactbasic, closing sentences; discharged by "
        "Thm. thm:emitted-bound at each of the two instances "
        "(Thm. thm:click-povm (i) with no probe, Thm. thm:conditional-povm (ii) with one)",
    ),
    (
        "Eq. eq:mcpos enters the exact-window lemma at EXACTLY ONE STEP",
        "the P = 0 branch that the outer max{0, .} of Eq. eq:exactcomposite creates",
        "Rem. rem:exactscope; Lem. lem:exactwindow's proof, which marks the "
        "step: 'this is the ONE step that uses Eq. eq:mcpos'",
    ),
)


# ---------------------------------------------------------------------------
#  Group RP-T -- Lemma lem:exactwindow and the emitted Eq. eq:pmcex (RC8)
# ---------------------------------------------------------------------------
#
#  LEMMA lem:exactwindow, Eq. eq:exactcomposite:
#
#      P = max{ 0, min{ min_{N < n <= m*} ell(n), tau } }
#
#  under Eq. eq:ellhyp (ell(n) <= beta*(n) on the window) and Eq. eq:tailadm
#  (tau <= 0 OR tau <= inf_{n > m*} beta*(n)); the conclusion is
#  Eq. eq:exactstatement, blk M^{(>N)}_mc >= P id^{(>N)}, together with
#  0 <= P <= 1.
#
#  THE HYPOTHESES ARE ON ARBITRARY REALS, WHICH IS WHY THE FIRST TABLE BELOW IS
#  LEMMA-LEVEL AND NOT RECEIVER-LEVEL. Rem. rem:exactscope: "What the lemma does
#  NOT do is make an exact eigenvalue available. It is stated on beta*, an exact
#  quantity, and Eq. eq:ellhyp is a HYPOTHESIS ON WHATEVER NUMBERS ARE SUPPLIED
#  FOR IT. Definition def:pmcex is where those numbers come from."
#
#  THREE ADMISSIBLE CHOICES, ALL THREE USED BY THE CONTRACT: (i) tau = T_{m*} of
#  Eq. eq:windowtail, with NO hypothesis; (ii) tau = beta(m* + 1) under
#  Eq. eq:collapsehyp; (iii) ell(n) = beta(n), and the pointwise maximum of
#  finitely many admissible ell is admissible -- which is exactly what
#  Eq. eq:elldef takes.

#: The three admissible choices of Lem. lem:exactwindow, and the hypothesis each
#: needs. (part, what it supplies, hypothesis, where Def. def:pmcex uses it)
EXACT_WINDOW_ADMISSIBLE_CHOICES: tuple[tuple[str, str, str, str], ...] = (
    (
        "(i)",
        "tau = T_{m*} = 1 - sum_k beta_k d_k^{m*}, the analytic tail of "
        "Eq. eq:windowtail",
        "NONE -- 'satisfies Eq. eq:tailadm for every admissible bound data, "
        "with no hypothesis'. The proof is the tail step inside "
        "Lem. lem:windowtail (i) plus beta*(n) >= beta(n).",
        "BRANCH 2 of Eq. eq:pmcex, applied with m* = m_t: 'branch 2 has no "
        "hypothesis available and keeps its own analytic window and tail above "
        "the exact one'",
    ),
    (
        "(ii)",
        "tau = beta(m* + 1)",
        "Eq. eq:collapsehyp. Proof: if beta(m*+1) <= 0 the FIRST disjunct of "
        "Eq. eq:tailadm holds; otherwise Lem. lem:collapse read at cutoff m* "
        "gives inf_{n > m*} beta(n) = beta(m*+1), and beta* >= beta pointwise "
        "lifts it to beta*.",
        "BRANCH 1 of Eq. eq:pmcex: 'branch 1 has Eq. eq:collapsehyp EXACTLY, "
        "by predicate (X)'",
    ),
    (
        "(iii)",
        "ell(n) = beta(n) is admissible, and the POINTWISE MAXIMUM of finitely "
        "many admissible choices of ell is admissible",
        "the first statement is Lem. lem:exactbasic; the second is that a "
        "maximum of finitely many numbers each at most beta*(n) is at most "
        "beta*(n)",
        "Eq. eq:elldef, which is exactly such a maximum of two: the analytic "
        "beta(n) and the computed beta-hat*(n) - eps_eig",
    ),
)

#: WHICH REMAINDER EACH BRANCH OF Def. def:pmcex KEEPS, AND WHY. Def. def:pmcex,
#: "Why each branch keeps its own remainder": "The exact window covers
#: N < n <= m*_t AND NOTHING ABOVE IT, so a remainder admissible in the sense of
#: Eq. eq:tailadm is STILL REQUIRED, and each branch already has one ... NEITHER
#: REMAINDER IS NEW AND NEITHER IS WEAKENED."
#: (branch, predicate (X), remainder, admissible by, the m* constraint)
EXACT_WINDOW_BRANCH_REMAINDERS: tuple[tuple[str, bool, str, str, str], ...] = (
    (
        "1",
        True,
        "beta^(t)(m*_t + 1)",
        "Lem. lem:exactwindow (ii), 'the remainder being admissible by part "
        "(ii) BECAUSE PREDICATE (X) MAKES Eq. eq:collapsehyp HOLD'",
        "m*_t > N only; NO tail_window is required at a setting where (X) "
        "holds, so nothing bounds m*_t from above",
    ),
    (
        "2",
        False,
        "the analytic middle window min_{m*_t < n <= m_t} beta^(t)(n) AND the "
        "tail T^(t)_{m_t}",
        "Lem. lem:exactwindow (i), applied with m* = m_t and the window "
        "function ell(n) = ell^(t)(n) on N < n <= m*_t and ell(n) = "
        "beta^(t)(n) on m*_t < n <= m_t",
        "m*_t > N AND m*_t <= m_t, 'so that the two windows compose into the "
        "single window N < n <= m_t that Lem. lem:exactwindow is applied to'",
    ),
)


@dataclass(frozen=True)
class ExactCompositeCase:
    """One evaluation of Eq. eq:exactcomposite on admissible reals."""

    case_id: str
    photon_cutoff: int
    exact_depth: int
    #: (n, ell(n)) over N < n <= m*, in increasing n.
    ell_values: tuple[tuple[int, F], ...]
    tau: F
    #: Which disjunct of Eq. eq:tailadm the tau satisfies: "nonpositive" or
    #: "below the infimum".
    tailadm_disjunct: str
    #: min over the window of ell.
    window_minimum: F
    #: min{window_minimum, tau}, BEFORE the outer max{0, .}.
    inner_minimum: F
    #: P of Eq. eq:exactcomposite.
    p_value: F
    #: True where the outer max{0, .} is what produces the value -- the ONE
    #: branch of the proof that uses Eq. eq:mcpos (Rem. rem:exactscope).
    uses_mcpos_branch: bool
    derives_from: str


EXACT_COMPOSITE_CASES: tuple[ExactCompositeCase, ...] = (
    ExactCompositeCase(
        case_id="EW-TAU-BINDS",
        photon_cutoff=1,
        exact_depth=2,
        ell_values=((2, F(1, 2)),),
        tau=F(1, 4),
        tailadm_disjunct="below the infimum",
        window_minimum=F(1, 2),
        inner_minimum=F(1, 4),
        p_value=F(1, 4),
        uses_mcpos_branch=False,
        derives_from=(
            "THE REMAINDER BINDS. A single-index window with ell(2) = 1/2 and a "
            "remainder tau = 1/4 <= inf_{n > 2} beta*(n). Eq. eq:exactcomposite "
            "gives P = max{0, min{1/2, 1/4}} = 1/4. FROZEN BECAUSE AN "
            "IMPLEMENTATION THAT REPORTED THE WINDOW MINIMUM WOULD EMIT 1/2, "
            "which the lemma does not license: the window covers "
            "N < n <= m* AND NOTHING ABOVE IT."
        ),
    ),
    ExactCompositeCase(
        case_id="EW-ELL-BINDS",
        photon_cutoff=1,
        exact_depth=2,
        ell_values=((2, F(1, 4)),),
        tau=F(1, 2),
        tailadm_disjunct="below the infimum",
        window_minimum=F(1, 4),
        inner_minimum=F(1, 4),
        p_value=F(1, 4),
        uses_mcpos_branch=False,
        derives_from=(
            "THE MIRROR OF EW-TAU-BINDS: the same two numbers exchanged, so "
            "that P = max{0, min{1/4, 1/2}} = 1/4 comes from the WINDOW this "
            "time. The pair together fixes that Eq. eq:exactcomposite is a "
            "MINIMUM of the two and not a choice between them by branch."
        ),
    ),
    ExactCompositeCase(
        case_id="EW-P-ZERO-NEGATIVE-ELL",
        photon_cutoff=1,
        exact_depth=2,
        ell_values=((2, F(-1, 3)),),
        tau=F(1, 2),
        tailadm_disjunct="below the infimum",
        window_minimum=F(-1, 3),
        inner_minimum=F(-1, 3),
        p_value=F(0),
        uses_mcpos_branch=True,
        derives_from=(
            "THE P = 0 BRANCH, WHICH IS THE ONE STEP OF THE PROOF THAT USES "
            "Eq. eq:mcpos. The inner minimum is -1/3 and the outer max{0, .} "
            "raises it to 0, at which point Eq. eq:exactstatement asserts "
            "blk M^{(>N)}_mc >= 0 -- and the lemma's proof says in terms: 'If "
            "P = 0 the assertion is blk M^{(>N)}_mc >= 0, AND THIS IS THE ONE "
            "STEP THAT USES Eq. eq:mcpos: that hypothesis gives "
            "blk M^{(=n)}_mc >= 0 on every block (Lem. lem:exactbasic), hence "
            "on their direct sum.'\n"
            "SO A CONFORMING IMPLEMENTATION MAY EMIT 0 HERE AND MAY NOT EMIT "
            "-1/3: Def. def:slot requires p_i >= 0, and Prop. prop:slotvalid's "
            "ARCHITECTURE_SPEC.md Section 7.3 failure condition 'p_y < 0' is "
            "exactly what the outer maximum forecloses."
        ),
    ),
    ExactCompositeCase(
        case_id="EW-P-ZERO-TAU-NONPOSITIVE",
        photon_cutoff=1,
        exact_depth=2,
        ell_values=((2, F(1, 2)),),
        tau=F(-1, 5),
        tailadm_disjunct="nonpositive",
        window_minimum=F(1, 2),
        inner_minimum=F(-1, 5),
        p_value=F(0),
        uses_mcpos_branch=True,
        derives_from=(
            "THE FIRST DISJUNCT OF Eq. eq:tailadm, WHICH IS OTHERWISE EASY TO "
            "MISS. The condition on tau is 'tau <= 0 OR tau <= inf_{n > m*} "
            "beta*(n)', so a NON-POSITIVE tau is admissible with NO further "
            "hypothesis whatever -- and it then drives the whole expression to "
            "0 regardless of how good the window is: P = max{0, min{1/2, "
            "-1/5}} = 0.\n"
            "THAT IS NOT A DEFECT, IT IS THE SHAPE OF THE STATEMENT. The proof "
            "reads: 'so let P > 0. Then tau >= P > 0, SO THE FIRST DISJUNCT OF "
            "Eq. eq:tailadm FAILS AND THE SECOND HOLDS.' The first disjunct "
            "exists so that a branch which cannot bound the tail at all still "
            "yields a VALID (if useless) statement rather than an invalid one. "
            "THE RECEIVER-LEVEL INSTANCE IS EX-PROBE-ON-N1-M2-MSTAR2, where "
            "T_2 = -3/125 < 0 and the emitted p_mc is 0."
        ),
    ),
    ExactCompositeCase(
        case_id="EW-UPPER-LIMIT-ONE",
        photon_cutoff=0,
        exact_depth=1,
        ell_values=((1, F(1)),),
        tau=F(1),
        tailadm_disjunct="below the infimum",
        window_minimum=F(1),
        inner_minimum=F(1),
        p_value=F(1),
        uses_mcpos_branch=False,
        derives_from=(
            "THE UPPER LIMIT OF THE RANGE Lem. lem:exactwindow ASSERTS. The "
            "lemma states 0 <= P <= 1 and proves the upper half thus: 'either "
            "P = 0, or P <= ell(N+1) <= beta*(N+1) <= 1 by Eq. eq:ellhyp and "
            "Eq. eq:exactbasic -- WHICH NEEDS NO MORE THAN THE HYPOTHESES OF "
            "Thm. thm:multiclick-bound -- the window being non-empty because "
            "m* > N.' At ell = tau = 1 the bound is ATTAINED. Frozen so that "
            "the range statement Thm. thm:emitted-bound and Prop. prop:slotvalid "
            "rest on is exercised at its endpoint and not only in its "
            "interior."
        ),
    ),
    ExactCompositeCase(
        case_id="EW-MULTI-INDEX",
        photon_cutoff=1,
        exact_depth=4,
        ell_values=((2, F(3, 4)), (3, F(1, 2)), (4, F(7, 8))),
        tau=F(9, 10),
        tailadm_disjunct="below the infimum",
        window_minimum=F(1, 2),
        inner_minimum=F(1, 2),
        p_value=F(1, 2),
        uses_mcpos_branch=False,
        derives_from=(
            "A WINDOW OF THREE INDICES, WHOSE MINIMUM IS IN THE MIDDLE. "
            "N = 1, m* = 4, ell(2) = 3/4, ell(3) = 1/2, ell(4) = 7/8, "
            "tau = 9/10. The window minimum is ell(3) = 1/2, NOT ell(2) and "
            "NOT the last index, so P = max{0, min{1/2, 9/10}} = 1/2. FROZEN "
            "BECAUSE Eq. eq:exactcomposite MINIMISES OVER THE WHOLE WINDOW and "
            "an implementation that read only the first index -- the one "
            "Eq. eq:pmcdef's branch 1 reads -- would emit 3/4, which the lemma "
            "does not license. beta* IS NOT MONOTONE IN GENERAL: "
            "Lem. lem:collapse is a statement about beta, and it is stated "
            "under Eq. eq:collapsehyp."
        ),
    ),
)


@dataclass(frozen=True)
class ExactWindowCase:
    """One emitted p_mc^(t) under Def. def:pmcex, beside Def. def:pmc's."""

    case_id: str
    receiver: str
    port_count: int
    gamma: F
    betas: tuple[F, ...]
    c: F
    ds: tuple[F, ...]
    photon_cutoff: int
    #: Whether predicate (X) of Def. def:pmc holds at this setting.
    predicate_x: bool
    #: "1" or "2", the branch of Eq. eq:pmcex.
    branch: str
    #: The declared tail_window m_t, or None where (X) holds and none is
    #: required (Rem. rem:windowdecidable).
    tail_window: int | None
    #: The declared exact_window depth m*_t.
    exact_depth: int
    #: The declared eps_eig, SUBTRACTED in Eq. eq:elldef. It decides nothing.
    eps_eig: F
    #: (n, beta(n), beta-hat*(n), ell(n)) over N < n <= m*_t, increasing n.
    window: tuple[tuple[int, F, F, F], ...]
    #: min over the exact window of ell.
    window_minimum: F
    #: Branch 2 only: min over m*_t < n <= m_t of beta(n). None where the index
    #: set is EMPTY (m*_t = m_t), where Eq. eq:pmcex makes it +infinity and
    #: INACTIVE, and None on branch 1.
    middle_window_minimum: F | None
    #: True where m*_t = m_t on branch 2, so the middle minimum is over the
    #: empty index set.
    middle_window_empty: bool
    #: The branch's own remainder: beta(m*+1) on branch 1, T_{m_t} on branch 2.
    remainder: F
    remainder_kind: str
    #: max{0, min{...}} -- the emitted value of Eq. eq:pmcex.
    p_mc: F
    #: What Eq. eq:pmcdef emits at the same setting on the same bound data,
    #: i.e. what a declaration WITHOUT a depth emits. Prop. prop:exactnoworse.
    p_mc_without_depth: F
    #: r_6 of Eq. eq:res6 on this window.
    r6: F
    #: Whether Eq. eq:eigassumption holds at the frozen beta-hat* values.
    eig_assumption_holds: bool
    derives_from: str


EXACT_WINDOW_CASES: tuple[ExactWindowCase, ...] = (
    ExactWindowCase(
        case_id="EX-BB84-N1-M2-EIG-ZERO",
        receiver="I-BB84 at p_Z = p_X = 1/2",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        photon_cutoff=1,
        predicate_x=True,
        branch="1",
        tail_window=None,
        exact_depth=2,
        eps_eig=F(0),
        window=((2, F(0), F(1, 2), F(1, 2)),),
        window_minimum=F(1, 2),
        middle_window_minimum=None,
        middle_window_empty=False,
        remainder=F(1, 2),
        remainder_kind="beta(m* + 1) = beta(3)",
        p_mc=F(1, 2),
        p_mc_without_depth=F(0),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "EXAMPLE ex:bb84exact's OWN CASE, AT eps_eig = 0. 'At the cutoff "
            "N = 1, Definition def:pmc emits max{0, beta(2)} = 0: THE "
            "TWO-PHOTON BLOCK IS DISCARDED ENTIRELY, although half of its "
            "weight is guaranteed. Declare the minimal depth m* = N + 1 = 2.'\n"
            "PREDICATE (X) HOLDS by its first clause -- this receiver declares "
            "Inp_S EMPTY -- so Eq. eq:pmcex takes BRANCH 1 with the remainder "
            "beta(m* + 1) = beta(3) = 1/2, admissible by "
            "Lem. lem:exactwindow (ii).\n"
            "THE WINDOW IS THE SINGLE INDEX n = 2. Eq. eq:elldef: "
            "ell(2) = max{beta(2), beta-hat*(2) - eps_eig} = max{0, 1/2 - 0} = "
            "1/2, from beta(2) = 0 (Eq. eq:bb84beta at p_Z = 1/2) and "
            "beta*(2) = 1/2 (EB-BB84-N2-PZ-HALF).\n"
            "THE EMITTED VALUE: p_mc = max{0, min{ell(2), beta(3)}} = "
            "max{0, min{1/2, 1/2}} = 1/2. BOTH ARGUMENTS OF THE INNER MINIMUM "
            "ARE 1/2 HERE, which is a coincidence of this receiver at this "
            "cutoff and not a structural fact; EX-BB84-N2-M3-EIG-ZERO is the "
            "case where the remainder is the strictly binding one.\n"
            "AGAINST 0.2.0: Eq. eq:pmcdef emits max{0, beta(N+1)} = "
            "max{0, beta(2)} = 0, which BD-BB84-N1-ZERO freezes and which is "
            "NOT superseded -- that case declares no depth. THE GAIN IS THE "
            "WHOLE VALUE: 0 -> 1/2. Ex. ex:bb84exact: 'Example ex:bb84bound "
            "reaches p_mc = 1/2 ONLY AT THE CUTOFF N = 2; the exact window "
            "reaches it at N = 1, from a single 3x3 eigenvalue problem, and N "
            "is the parameter every downstream target dimension grows with.'\n"
            "r_6 = (beta(2) - beta-hat*(2))_+ = (0 - 1/2)_+ = 0."
        ),
    ),
    ExactWindowCase(
        case_id="EX-BB84-N1-M2-EIG-1E3",
        receiver="I-BB84 at p_Z = p_X = 1/2",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        photon_cutoff=1,
        predicate_x=True,
        branch="1",
        tail_window=None,
        exact_depth=2,
        eps_eig=F(1, 1000),
        window=((2, F(0), F(1, 2), F(499, 1000)),),
        window_minimum=F(499, 1000),
        middle_window_minimum=None,
        middle_window_empty=False,
        remainder=F(1, 2),
        remainder_kind="beta(m* + 1) = beta(3)",
        p_mc=F(499, 1000),
        p_mc_without_depth=F(0),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "THE SAME DECLARATION AT THE FIXTURE eps_eig = 1/1000, so that the "
            "declared slack is seen to be SUBTRACTED ONCE and from a number "
            "that was 0 under Eq. eq:pmcdef. ell(2) = max{0, 1/2 - 1/1000} = "
            "499/1000, and 499/1000 < 1/2 = beta(3), so the window binds and "
            "p_mc = 499/1000.\n"
            "Eq. eq:bb84exactemit STATES THE WHOLE FAMILY: p_mc = "
            "max{0, 1/2 - eps_eig}, 'since ell(2) = max{beta(2), "
            "beta-hat*(2) - eps_eig} = max{0, 1/2 - eps_eig}, WHICH IS "
            "<= 1/2 = beta(3) ON THE WHOLE DECLARED DOMAIN eps_eig in [0, 1), "
            "so the minimum is ell(2) throughout'. At eps_eig = 1/1000 that is "
            "1/2 - 1/1000 = 499/1000.\n"
            "THE COST OF THE SLACK IS VISIBLE AND RECOMPUTABLE, which is why "
            "Section 2.2 carries beta-hat* unmodified: 1/2 is in the artifact "
            "and 499/1000 is what the inequality used."
        ),
    ),
    ExactWindowCase(
        case_id="EX-BB84-N1-M2-EIG-HALF",
        receiver="I-BB84 at p_Z = p_X = 1/2",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        photon_cutoff=1,
        predicate_x=True,
        branch="1",
        tail_window=None,
        exact_depth=2,
        eps_eig=F(1, 2),
        window=((2, F(0), F(1, 2), F(0)),),
        window_minimum=F(0),
        middle_window_minimum=None,
        middle_window_empty=False,
        remainder=F(1, 2),
        remainder_kind="beta(m* + 1) = beta(3)",
        p_mc=F(0),
        p_mc_without_depth=F(0),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "THE DOMAIN SPLIT OF Eq. eq:bb84exactemit, AT THE SPLIT POINT. "
            "'The value is 1/2 - eps_eig at eps_eig <= 1/2 and 0 above it; "
            "THE OUTER max{0, .} IS CARRIED THROUGH THE CHAIN RATHER THAN "
            "DROPPED, BECAUSE THE DECLARED DOMAIN REACHES PAST 1/2.' At "
            "eps_eig = 1/2 exactly, ell(2) = max{0, 1/2 - 1/2} = 0 and "
            "p_mc = max{0, min{0, 1/2}} = 0 -- THE SAME VALUE Eq. eq:pmcdef "
            "emits, so the declaration paid for one 3x3 eigenvalue problem and "
            "bought nothing. Prop. prop:exactnoworse holds WITH EQUALITY.\n"
            "eps_eig = 1/2 IS INSIDE THE DECLARED DOMAIN [0, 1) and is "
            "therefore admissible; Rem. rem:tolerancedomain says the domain is "
            "'A FLOOR, NOT SIZING ADVICE'. This case is what that costs."
        ),
    ),
    ExactWindowCase(
        case_id="EX-BB84-N1-M2-EIG-THREE-QUARTERS",
        receiver="I-BB84 at p_Z = p_X = 1/2",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        photon_cutoff=1,
        predicate_x=True,
        branch="1",
        tail_window=None,
        exact_depth=2,
        eps_eig=F(3, 4),
        window=((2, F(0), F(1, 2), F(0)),),
        window_minimum=F(0),
        middle_window_minimum=None,
        middle_window_empty=False,
        remainder=F(1, 2),
        remainder_kind="beta(m* + 1) = beta(3)",
        p_mc=F(0),
        p_mc_without_depth=F(0),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "ABOVE THE SPLIT, WHERE THE SECOND ENTRY OF Eq. eq:elldef IS "
            "NEGATIVE. beta-hat*(2) - eps_eig = 1/2 - 3/4 = -1/4, so "
            "ell(2) = max{0, -1/4} = 0 by the INNER maximum, before the outer "
            "one is reached, and p_mc = 0.\n"
            "THIS IS Eq. eq:elldef's FLOOR DOING THE WORK, and it is the "
            "one-sided direction Rem. rem:exacteig names: 'A computed "
            "eigenvalue landing BELOW the exact one costs tightness and "
            "nothing else, and Eq. eq:elldef FLOORS THE VALUE AT beta^(t)(n), "
            "which is sound with no assumption at all -- SO THAT DIRECTION "
            "CANNOT TAKE THE EMITTED WEIGHT BELOW WHAT 0.2.0 EMITS.' Here the "
            "floor is beta(2) = 0, which is what 0.2.0 emits, and the emitted "
            "value is exactly that. Rem. rem:tolerancedomain's degeneracy "
            "argument for eps_eig >= 1 is the same argument taken further: "
            "there 'the second entry of Eq. eq:elldef IS NEVER POSITIVE and "
            "the exact window is never the binding term'."
        ),
    ),
    ExactWindowCase(
        case_id="EX-BB84-N1-M3-EIG-1E3",
        receiver="I-BB84 at p_Z = p_X = 1/2",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        photon_cutoff=1,
        predicate_x=True,
        branch="1",
        tail_window=None,
        exact_depth=3,
        eps_eig=F(1, 1000),
        window=(
            (2, F(0), F(1, 2), F(499, 1000)),
            (3, F(1, 2), F(13, 16), F(1623, 2000)),
        ),
        window_minimum=F(499, 1000),
        middle_window_minimum=None,
        middle_window_empty=False,
        remainder=F(3, 4),
        remainder_kind="beta(m* + 1) = beta(4)",
        p_mc=F(499, 1000),
        p_mc_without_depth=F(0),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "A DEEPER WINDOW THAT BUYS NOTHING, WHICH IS A RESULT AND NOT A "
            "DEFECT. The same declaration as EX-BB84-N1-M2-EIG-1E3 with "
            "m* = 3 instead of 2, so the window is {2, 3} and TWO eigenvalue "
            "problems are paid for -- a 3x3 and a 4x4.\n"
            "ell(2) = max{0, 1/2 - 1/1000} = 499/1000 (as before);\n"
            "ell(3) = max{beta(3), beta-hat*(3) - eps_eig} = "
            "max{1/2, 13/16 - 1/1000}. Now 13/16 = 13000/16000 and "
            "1/1000 = 16/16000, so 13/16 - 1/1000 = 12984/16000 = 1623/2000, "
            "which exceeds 1/2 = 1000/2000; hence ell(3) = 1623/2000.\n"
            "THE WINDOW MINIMUM IS min{499/1000, 1623/2000} = "
            "min{998/2000, 1623/2000} = 998/2000 = 499/1000, ATTAINED AT "
            "n = 2. The remainder is beta(4) = 3/4 = 1500/2000, larger still. "
            "So p_mc = 499/1000, IDENTICAL to the m* = 2 declaration.\n"
            "WHY IT IS WORTH FREEZING: the depth is 'the caller's because the "
            "cost is the caller's' (Section 1.1 (b)), and this case is the "
            "concrete instance of a caller paying for depth that the binding "
            "index does not use. beta*(3) = 13/16 (EB-BB84-N3-PZ-HALF) is much "
            "better than beta*(2) = 1/2, and it changes nothing, because the "
            "emitted value is a MINIMUM over the window."
        ),
    ),
    ExactWindowCase(
        case_id="EX-BB84-N2-M3-EIG-ZERO",
        receiver="I-BB84 at p_Z = p_X = 1/2",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        photon_cutoff=2,
        predicate_x=True,
        branch="1",
        tail_window=None,
        exact_depth=3,
        eps_eig=F(0),
        window=((3, F(1, 2), F(13, 16), F(13, 16)),),
        window_minimum=F(13, 16),
        middle_window_minimum=None,
        middle_window_empty=False,
        remainder=F(3, 4),
        remainder_kind="beta(m* + 1) = beta(4)",
        p_mc=F(3, 4),
        p_mc_without_depth=F(1, 2),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "THE REMAINDER STRICTLY BINDS, AND THE EMITTED VALUE STILL "
            "IMPROVES. At the cutoff N = 2 the window is the single index "
            "n = 3, where beta(3) = 1/2 and beta*(3) = 13/16 "
            "(EB-BB84-N3-PZ-HALF), so ell(3) = 13/16 at eps_eig = 0. The "
            "remainder is beta(m* + 1) = beta(4) = 1 - 2^{2-4} = 3/4.\n"
            "min{13/16, 3/4} = min{13/16, 12/16} = 12/16 = 3/4, SO THE "
            "REMAINDER IS THE BINDING TERM and p_mc = 3/4.\n"
            "AGAINST 0.2.0: Eq. eq:pmcdef emits max{0, beta(3)} = 1/2, which "
            "BD-BB84-N2 freezes and which is NOT superseded. THE GAIN IS "
            "1/2 -> 3/4, and it is bounded by the ANALYTIC remainder rather "
            "than by the exact eigenvalue -- which is exactly what "
            "Def. def:pmcex means by 'each branch keeps its own remainder'. AN "
            "IMPLEMENTATION THAT DROPPED THE REMAINDER WOULD EMIT 13/16, AND "
            "THAT WOULD BE UNSOUND: nothing in this contract bounds "
            "lmin(blk M^{(=n)}_mc) below 13/16 for n >= 4."
        ),
    ),
    ExactWindowCase(
        case_id="EX-BB84-N2-M3-EIG-1E3",
        receiver="I-BB84 at p_Z = p_X = 1/2",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        photon_cutoff=2,
        predicate_x=True,
        branch="1",
        tail_window=None,
        exact_depth=3,
        eps_eig=F(1, 1000),
        window=((3, F(1, 2), F(13, 16), F(1623, 2000)),),
        window_minimum=F(1623, 2000),
        middle_window_minimum=None,
        middle_window_empty=False,
        remainder=F(3, 4),
        remainder_kind="beta(m* + 1) = beta(4)",
        p_mc=F(3, 4),
        p_mc_without_depth=F(1, 2),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "THE SAME DECLARATION AT THE FIXTURE eps_eig = 1/1000, FROZEN "
            "BECAUSE THE SLACK COSTS NOTHING HERE. ell(3) = "
            "max{1/2, 13/16 - 1/1000} = 1623/2000 = 0.8115, which still "
            "exceeds the remainder 3/4 = 1500/2000, so the minimum is the "
            "remainder and p_mc = 3/4 -- THE SAME VALUE AS AT eps_eig = 0.\n"
            "THE POINT IS THAT eps_eig IS NOT A UNIFORM TAX. It is subtracted "
            "from a computed eigenvalue inside a MINIMUM, so it changes the "
            "emitted value only where the exact window is the binding term. "
            "Compare EX-BB84-N1-M2-EIG-1E3, where it costs exactly 1/1000."
        ),
    ),
    ExactWindowCase(
        case_id="EX-BB84-PZ7-N1-M2-EIG-ZERO",
        receiver="I-BB84 at p_Z = 7/10, p_X = 3/10",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(7, 10), F(7, 10), F(3, 10), F(3, 10)),
        photon_cutoff=1,
        predicate_x=True,
        branch="1",
        tail_window=None,
        exact_depth=2,
        eps_eig=F(0),
        window=((2, F(-4, 25), F(21, 50), F(21, 50)),),
        window_minimum=F(21, 50),
        middle_window_minimum=None,
        middle_window_empty=False,
        remainder=F(13, 50),
        remainder_kind="beta(m* + 1) = beta(3)",
        p_mc=F(13, 50),
        p_mc_without_depth=F(0),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "A SECOND p_Z, WHERE THE ANALYTIC BOUND IS NEGATIVE AND THE "
            "REMAINDER BINDS. p_Z = 7/10 gives d_H = d_V = 7/10 and "
            "d_+ = d_- = 3/10 by the computation of BD-BB84-N2, so "
            "beta(n) = 1 - 2(7/10)^n - 2(3/10)^n:\n"
            "  beta(2) = 1 - 98/100 - 18/100 = -16/100 = -4/25;\n"
            "  beta(3) = 1 - 686/1000 - 54/1000 = 260/1000 = 13/50.\n"
            "beta*(2) = 21/50 (EB-BB84-N2-PZ-SEVEN-TENTHS), so at eps_eig = 0 "
            "ell(2) = max{-4/25, 21/50} = 21/50. THE REMAINDER beta(3) = 13/50 "
            "IS SMALLER, so min{21/50, 13/50} = 13/50 and p_mc = 13/50.\n"
            "AGAINST 0.2.0: max{0, beta(2)} = max{0, -4/25} = 0. THE GAIN IS "
            "0 -> 13/50, AND IT IS CAPPED BY THE ANALYTIC REMAINDER RATHER "
            "THAN BY THE EIGENVALUE: 21/50 is guaranteed on the two-photon "
            "block, but nothing here guarantees more than beta(3) = 13/50 "
            "above it. THAT IS THE STRUCTURE OF Lem. lem:exactwindow AND NOT A "
            "LOSS: the window covers finitely many blocks and the remainder "
            "covers the rest."
        ),
    ),
    ExactWindowCase(
        case_id="EX-BB84-PZ-QUARTER-N1-M2-EIG-ZERO",
        receiver="I-BB84 at p_Z = 1/4, p_X = 3/4",
        port_count=4,
        gamma=F(1),
        betas=(F(1), F(1), F(1), F(1)),
        c=F(0),
        ds=(F(1, 4), F(1, 4), F(3, 4), F(3, 4)),
        photon_cutoff=1,
        predicate_x=True,
        branch="1",
        tail_window=None,
        exact_depth=2,
        eps_eig=F(0),
        window=((2, F(-1, 4), F(3, 8), F(3, 8)),),
        window_minimum=F(3, 8),
        middle_window_minimum=None,
        middle_window_empty=False,
        remainder=F(1, 8),
        remainder_kind="beta(m* + 1) = beta(3)",
        p_mc=F(1, 8),
        p_mc_without_depth=F(0),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "THE RECEIVER BD-BB84-PZ-QUARTER-N2 ALREADY FREEZES, AT A LOWER "
            "CUTOFF AND WITH A DEPTH. p_Z = 1/4: beta(2) = "
            "1 - 2(1/16) - 2(9/16) = -1/4 and beta(3) = "
            "1 - 2(1/64) - 2(27/64) = 8/64 = 1/8, both of which that case "
            "already carries. beta*(2) = 3/8 (EB-BB84-N2-PZ-QUARTER).\n"
            "ell(2) = max{-1/4, 3/8} = 3/8; the remainder beta(3) = 1/8 binds; "
            "p_mc = max{0, min{3/8, 1/8}} = 1/8.\n"
            "TWO DECLARATIONS OF ONE DEVICE, AND BOTH ARE CORRECT. "
            "BD-BB84-PZ-QUARTER-N2 declares N = 2 and NO depth and emits 1/8. "
            "This case declares N = 1 AND a depth and ALSO emits 1/8. So the "
            "exact window buys the same value at a cutoff one lower, which is "
            "the whole point of the amendment (Ex. ex:bb84exact: 'N is the "
            "parameter every downstream target dimension grows with'). NEITHER "
            "CASE SUPERSEDES THE OTHER."
        ),
    ),
    ExactWindowCase(
        case_id="EX-BS-N1-M2-EIG-1E3",
        receiver="I-BS (ONE channel input mode, no probe)",
        port_count=2,
        gamma=F(1),
        betas=(F(1), F(1)),
        c=F(0),
        ds=(F(1, 2), F(1, 2)),
        photon_cutoff=1,
        predicate_x=True,
        branch="1",
        tail_window=None,
        exact_depth=2,
        eps_eig=F(1, 1000),
        window=((2, F(1, 2), F(1, 2), F(1, 2)),),
        window_minimum=F(1, 2),
        middle_window_minimum=None,
        middle_window_empty=False,
        remainder=F(3, 4),
        remainder_kind="beta(m* + 1) = beta(3)",
        p_mc=F(1, 2),
        p_mc_without_depth=F(1, 2),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "THE ANALYTIC FLOOR OF Eq. eq:elldef WINNING, AND THE DECLARED "
            "SLACK COSTING NOTHING. At I-BS the channel space is "
            "one-dimensional, so beta*(n) = beta(n) exactly (EB-BS-N2), and\n"
            "  ell(2) = max{beta(2), beta-hat*(2) - eps_eig} "
            "= max{1/2, 1/2 - 1/1000} = 1/2,\n"
            "THE FIRST ENTRY WINNING. The remainder beta(3) = 3/4 is larger, "
            "so p_mc = 1/2 -- EXACTLY what Eq. eq:pmcdef emits (BD-BS-N1).\n"
            "PROPOSITION prop:exactnoworse WITH EQUALITY, and the reason is "
            "structural rather than numerical: Eq. eq:elldef is a MAXIMUM whose "
            "first entry is the analytic bound, so the emitted value can never "
            "fall below it however badly the eigenvalue routine behaves. "
            "Rem. rem:exacteig: 'a computed eigenvalue landing BELOW the exact "
            "one costs tightness and nothing else'.\n"
            "AND THE COST IS REAL: this declaration paid for an eigenvalue "
            "problem and bought nothing, because the bound was already tight. "
            "THAT IS WHY THE DEPTH IS OPT-IN."
        ),
    ),
    ExactWindowCase(
        case_id="EX-PROBE-ON-N1-M3-MSTAR2",
        receiver="I-PROBE at the THERMAL setting nbar = 1 (predicate (X) FAILS)",
        port_count=2,
        gamma=F(2, 3),
        betas=(F(4, 5), F(4, 5)),
        c=F(1, 2),
        ds=(F(4, 5), F(4, 5)),
        photon_cutoff=1,
        predicate_x=False,
        branch="2",
        tail_window=3,
        exact_depth=2,
        eps_eig=F(1, 1000),
        window=((2, F(107, 750), F(107, 750), F(107, 750)),),
        window_minimum=F(107, 750),
        middle_window_minimum=F(1981, 7500),
        middle_window_empty=False,
        remainder=F(113, 625),
        remainder_kind="T_{m_t} = T_3",
        p_mc=F(107, 750),
        p_mc_without_depth=F(107, 750),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "BRANCH 2 OF Eq. eq:pmcex, WITH ALL THREE OF ITS ARGUMENTS ACTIVE. "
            "Predicate (X) FAILS at this setting -- probe modes are declared "
            "and Gamma^(t) is non-zero -- so a tail_window is REQUIRED "
            "(Rem. rem:windowdecidable) and the depth must satisfy "
            "m*_t <= m_t. Here N = 1, m_t = 3 and m*_t = 2.\n"
            "THE THREE ARGUMENTS, over the common denominator 7500:\n"
            "  min over 1 < n <= 2 of ell(n): the block is one dimensional so "
            "beta*(2) = beta(2) = 107/750 (EB-PROBE-ON-N2), and Eq. eq:elldef's "
            "floor gives ell(2) = max{107/750, 107/750 - 1/1000} = 107/750 = "
            "1070/7500;\n"
            "  min over 2 < n <= 3 of beta(n) = beta(3) = 1981/7500, the "
            "ANALYTIC middle window;\n"
            "  T_{m_t} = T_3 = 1 - 2(4/5)(64/125) = 1 - 512/625 = 113/625 = "
            "1356/7500.\n"
            "THE MINIMUM IS 1070/7500 = 107/750, so p_mc = 107/750 -- "
            "IDENTICAL to what BD-PROBE-ON-N1-M3 freezes for Eq. eq:pmcdef. "
            "Prop. prop:exactnoworse holds WITH EQUALITY, and branch 2's "
            "equality case is exact rather than approximate: Rem. rem:noworsefl "
            "says branch 2's comparison 'survives an evaluation term for term, "
            "because it compares evaluated numbers with each other'.\n"
            "WHY THE EXACT WINDOW GAINS NOTHING HERE: D = |Inp_C| = 1, so "
            "every block is a scalar and Eq. eq:mcbound holds with equality "
            "(EB-PROBE-ON-N2). THE EXACT WINDOW IS WORTH DECLARING ONLY WHERE "
            "THE BLOCK HAS ROOM TO BE BETTER THAN ITS BOUND."
        ),
    ),
    ExactWindowCase(
        case_id="EX-PROBE-ON-N1-M3-MSTAR3-EMPTY-MIDDLE",
        receiver="I-PROBE at the THERMAL setting nbar = 1 (predicate (X) FAILS)",
        port_count=2,
        gamma=F(2, 3),
        betas=(F(4, 5), F(4, 5)),
        c=F(1, 2),
        ds=(F(4, 5), F(4, 5)),
        photon_cutoff=1,
        predicate_x=False,
        branch="2",
        tail_window=3,
        exact_depth=3,
        eps_eig=F(1, 1000),
        window=(
            (2, F(107, 750), F(107, 750), F(107, 750)),
            (3, F(1981, 7500), F(1981, 7500), F(1981, 7500)),
        ),
        window_minimum=F(107, 750),
        middle_window_minimum=None,
        middle_window_empty=True,
        remainder=F(113, 625),
        remainder_kind="T_{m_t} = T_3",
        p_mc=F(107, 750),
        p_mc_without_depth=F(107, 750),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "THE EMPTY MIDDLE MINIMUM, WHICH IS A CONVENTION THE CONTRACT FIXES "
            "AND AN IMPLEMENTATION MUST NOT GUESS. Here m*_t = m_t = 3, which "
            "is admitted (the constraint is m*_t <= m_t), and Def. def:pmcex "
            "says of branch 2's middle term that it runs 'over THE EMPTY INDEX "
            "SET -- AND SO EQUAL TO +INFINITY AND INACTIVE -- when "
            "m*_t = m_t'.\n"
            "SO THE EXPRESSION HAS TWO ACTIVE ARGUMENTS: the exact window "
            "min{ell(2), ell(3)} = min{1070, 1981}/7500 = 1070/7500 = 107/750, "
            "and T_3 = 1356/7500. The minimum is 107/750 and p_mc = 107/750, "
            "the same as at m*_t = 2 and the same as Eq. eq:pmcdef's.\n"
            "AN IMPLEMENTATION THAT TREATED THE EMPTY MINIMUM AS 0 WOULD EMIT "
            "0 HERE, which is valid but strictly worse, and would violate "
            "Prop. prop:exactnoworse's conclusion at the one place the contract "
            "bothered to state a convention for. THAT IS WHY THIS CASE IS "
            "FROZEN AT ALL."
        ),
    ),
    ExactWindowCase(
        case_id="EX-PROBE-ON-N1-M2-MSTAR2-ZERO",
        receiver="I-PROBE at the THERMAL setting nbar = 1 (predicate (X) FAILS)",
        port_count=2,
        gamma=F(2, 3),
        betas=(F(4, 5), F(4, 5)),
        c=F(1, 2),
        ds=(F(4, 5), F(4, 5)),
        photon_cutoff=1,
        predicate_x=False,
        branch="2",
        tail_window=2,
        exact_depth=2,
        eps_eig=F(1, 1000),
        window=((2, F(107, 750), F(107, 750), F(107, 750)),),
        window_minimum=F(107, 750),
        middle_window_minimum=None,
        middle_window_empty=True,
        remainder=F(-3, 125),
        remainder_kind="T_{m_t} = T_2",
        p_mc=F(0),
        p_mc_without_depth=F(0),
        r6=F(0),
        eig_assumption_holds=True,
        derives_from=(
            "THE OUTER max{0, .} FIRING AT A RECEIVER, WHICH IS THE "
            "RECEIVER-LEVEL INSTANCE OF EW-P-ZERO-TAU-NONPOSITIVE. The same "
            "setting at the MINIMAL tail window m_t = N + 1 = 2, with "
            "m*_t = m_t = 2 so the middle minimum is again empty.\n"
            "T_2 = 1 - 2(4/5)(16/25) = 1 - 128/125 = -3/125, NEGATIVE -- which "
            "BD-PROBE-ON-N1-M2 already freezes. The exact window contributes "
            "ell(2) = 107/750, but min{107/750, -3/125} = -3/125 = -18/750, so "
            "p_mc = max{0, -3/125} = 0.\n"
            "A WINDOW TOO SHORT COSTS THE WHOLE BOUND, AND THE EXACT WINDOW "
            "DOES NOT RESCUE IT, because Def. def:pmcex keeps branch 2's own "
            "tail: 'the exact window covers N < n <= m*_t AND NOTHING ABOVE "
            "IT'. Prop. prop:exactnoworse holds with equality at 0. AN "
            "IMPLEMENTATION THAT DROPPED T_{m_t} BECAUSE AN EXACT WINDOW WAS "
            "DECLARED WOULD EMIT 107/750 HERE, AND THAT WOULD BE UNSOUND."
        ),
    ),
)


# ---------------------------------------------------------------------------
#  Group RP-U -- the sixth residual r_6, and what it is blind to (RC9)
# ---------------------------------------------------------------------------
#
#  Eq. eq:res6:
#
#      r_6 = max over t and over N < n <= m*_t of
#            ( beta^(t)(n) - beta-hat*^(t)(n) )_+
#
#  "the window consistency defect ... whose exact value is 0 by
#  Theorem thm:multiclick-bound" (Section 1.1 (d); Rem. rem:exacteig). It is
#  REQUEST-DEPENDENT, NOT ROUTE-DEPENDENT: it exists on all three routes but
#  only at the settings carrying a depth, over exactly the indices the depth
#  names, and its key is ABSENT -- not zero -- elsewhere.
#
#  WHAT IT CATCHES, in the contract's own list: "an evaluation that contradicts
#  an inequality this contract proves -- A BLOCK FORMED AT THE WRONG INDEX, A
#  WRONGLY ORDERED OCCUPATION BASIS, A CONDITIONED FAMILY TAKEN AT THE WRONG
#  SETTING, AN ITERATION THAT HAS NOT CONVERGED -- which is the failure mode
#  most likely to be gross."
#
#  WHAT IT DOES NOT DO, AND THIS IS THE CASE R6-PASS-OVERSHOOT-BLIND EXISTS FOR:
#  "It does NOT verify Assumption ass:eig: r_6 fires when beta-hat* lands too
#  LOW, and Assumption ass:eig constrains it from landing too HIGH. SAYING SO IS
#  THE POINT OF STATING IT. NO TEST IN THIS CONTRACT BOUNDS THE UNSAFE
#  DIRECTION; the assumption is what carries it, and Section 1.3 fires the
#  escalation trigger that goes with saying so."


@dataclass(frozen=True)
class Residual6Case:
    """One evaluation of Eq. eq:res6 (Def. def:residuals)."""

    case_id: str
    receiver: str
    photon_cutoff: int
    #: (setting, n, beta(n), beta-hat*(n), the EXACT beta*(n), the positive
    #: part of beta(n) - beta-hat*(n)). The exact value is carried so that
    #: `is_overshoot` is CHECKABLE rather than asserted: r_6 itself never sees
    #: it, which is the whole point of Rem. rem:exacteig's blindness clause.
    entries: tuple[tuple[str, int, F, F, F, F], ...]
    #: r_6, the maximum of the frozen defects over settings and indices.
    r6: F
    tolerance_key: str
    passes: bool
    #: The verbatim reason where the case refuses; None where it passes.
    refusal_reason: str | None
    #: True where beta-hat* lands ABOVE the exact value -- the direction r_6 is
    #: BLIND to and Assumption ass:eig constrains.
    is_overshoot: bool
    derives_from: str


RESIDUAL6_CASES: tuple[Residual6Case, ...] = (
    Residual6Case(
        case_id="R6-PASS-BB84-EXACT",
        receiver="I-BB84 at p_Z = 1/2",
        photon_cutoff=1,
        entries=(("off", 2, F(0), F(1, 2), F(1, 2), F(0)),),
        r6=F(0),
        tolerance_key="eps_6",
        passes=True,
        refusal_reason=None,
        is_overshoot=False,
        derives_from=(
            "THE EXACT VALUE OF THE RESIDUAL, AT THE DECLARATION "
            "EX-BB84-N1-M2-EIG-ZERO MAKES. beta(2) = 0 and beta-hat*(2) = 1/2, "
            "the exact eigenvalue, so the defect is (0 - 1/2)_+ = 0 and "
            "r_6 = 0. Rem. rem:exacteig: 'Since beta(n) <= beta*(n) is a "
            "theorem (Lem. lem:exactbasic), the window consistency defect r_6 "
            "HAS EXACT VALUE 0, and it is a residual in exactly the sense of "
            "the other five: WHAT IS EMITTED IS ITS FLOATING-POINT EVALUATION, "
            "and a value above eps_6 refuses.'"
        ),
    ),
    Residual6Case(
        case_id="R6-PASS-BB84-WINDOW-OF-TWO",
        receiver="I-BB84 at p_Z = 1/2",
        photon_cutoff=1,
        entries=(
            ("off", 2, F(0), F(1, 2), F(1, 2), F(0)),
            ("off", 3, F(1, 2), F(13, 16), F(13, 16), F(0)),
        ),
        r6=F(0),
        tolerance_key="eps_6",
        passes=True,
        refusal_reason=None,
        is_overshoot=False,
        derives_from=(
            "THE SAME AT THE TWO-INDEX WINDOW OF EX-BB84-N1-M3-EIG-1E3, so "
            "that the maximum is seen to run over the WHOLE window "
            "N < n <= m*_t and not over its first index. Both defects are 0: "
            "(0 - 1/2)_+ = 0 and (1/2 - 13/16)_+ = 0, the second using "
            "beta*(3) = 13/16 (EB-BB84-N3-PZ-HALF)."
        ),
    ),
    Residual6Case(
        case_id="R6-PASS-UNDERSHOOT-WITHIN-TOLERANCE",
        receiver="I-BB84 at p_Z = 1/2",
        photon_cutoff=2,
        entries=(("off", 3, F(1, 2), F(999, 2000), F(13, 16), F(1, 2000)),),
        r6=F(1, 2000),
        tolerance_key="eps_6",
        passes=True,
        refusal_reason=None,
        is_overshoot=False,
        derives_from=(
            "A SMALL UNDERSHOOT THAT THE DECLARED TOLERANCE ADMITS, WHICH IS "
            "WHAT MAKES r_6 A RESIDUAL RATHER THAN AN EXACT-ZERO ASSERTION. "
            "At N = 2 and m* = 3 the window is {3}, where beta(3) = 1/2. An "
            "evaluation returning beta-hat*(3) = 999/2000 -- BELOW the "
            "analytic bound, which is impossible for the exact beta*(3) = "
            "13/16 -- gives a defect of 1000/2000 - 999/2000 = 1/2000. "
            "Against the fixture eps_6 = 1/1000 = 2/2000 the test PASSES.\n"
            "AND THE EMITTED VALUE IS UNHARMED: Eq. eq:elldef floors ell(3) at "
            "beta(3) = 1/2, so an undershoot 'COSTS TIGHTNESS AND NOTHING "
            "ELSE' (Rem. rem:exacteig). This case is the pair of "
            "R6-FAIL-UNDERSHOOT: the same direction, one side of eps_6 each."
        ),
    ),
    Residual6Case(
        case_id="R6-FAIL-UNDERSHOOT",
        receiver="I-BB84 at p_Z = 1/2",
        photon_cutoff=2,
        entries=(("off", 3, F(1, 2), F(1, 4), F(13, 16), F(1, 4)),),
        r6=F(1, 4),
        tolerance_key="eps_6",
        passes=False,
        refusal_reason="window_eigenvalue_consistency_residual_above_tolerance",
        is_overshoot=False,
        derives_from=(
            "A GROSS UNDERSHOOT, REFUSED. beta(3) = 1/2 and an evaluation "
            "returning beta-hat*(3) = 1/4 give a defect of 1/4, far above the "
            "fixture eps_6 = 1/1000, so the artifact is REFUSED with the "
            "verbatim reason "
            "`window_eigenvalue_consistency_residual_above_tolerance` "
            "(Section 2.6, row 8).\n"
            "THIS IS THE FAILURE MODE THE RESIDUAL EXISTS FOR: 'an evaluation "
            "that CONTRADICTS AN INEQUALITY THIS CONTRACT PROVES -- a block "
            "formed at the wrong index, a wrongly ordered occupation basis, a "
            "conditioned family taken at the wrong setting, AN ITERATION THAT "
            "HAS NOT CONVERGED -- which is the failure mode most likely to be "
            "gross.' THE DIRECTION IS REFUSE-ONLY: nothing is repaired, no "
            "eigenvalue is recomputed and no value is clamped."
        ),
    ),
    Residual6Case(
        case_id="R6-FAIL-AT-THE-SECOND-INDEX",
        receiver="I-BB84 at p_Z = 1/2",
        photon_cutoff=1,
        entries=(
            ("off", 2, F(0), F(1, 2), F(1, 2), F(0)),
            ("off", 3, F(1, 2), F(0), F(13, 16), F(1, 2)),
        ),
        r6=F(1, 2),
        tolerance_key="eps_6",
        passes=False,
        refusal_reason="window_eigenvalue_consistency_residual_above_tolerance",
        is_overshoot=False,
        derives_from=(
            "THE MAXIMUM RUNS OVER THE WHOLE WINDOW, AND AN IMPLEMENTATION "
            "THAT CHECKED ONLY THE FIRST INDEX WOULD ADMIT THIS. At the "
            "two-index window {2, 3} the first evaluation is exact -- "
            "beta-hat*(2) = 1/2, defect (0 - 1/2)_+ = 0 -- and the second is "
            "not: beta-hat*(3) = 0 against beta(3) = 1/2 gives a defect of "
            "1/2. Eq. eq:res6 takes the MAXIMUM, so r_6 = 1/2 and the request "
            "is REFUSED.\n"
            "FROZEN BECAUSE THE ARITHMETIC IS EASY TO SHORT-CIRCUIT: the "
            "emitted p_mc reads a MINIMUM over the window, so a badly low "
            "beta-hat* at one index is already floored by beta at that index "
            "and changes nothing about the emitted value -- and r_6 is the "
            "only place it becomes visible."
        ),
    ),
    Residual6Case(
        case_id="R6-FAIL-ACROSS-SETTINGS",
        receiver="I-PROBE, both settings carrying a depth",
        photon_cutoff=1,
        entries=(
            ("off", 2, F(1, 8), F(1, 8), F(1, 8), F(0)),
            ("thermal", 2, F(107, 750), F(1, 10), F(107, 750), F(16, 375)),
        ),
        r6=F(16, 375),
        tolerance_key="eps_6",
        passes=False,
        refusal_reason="window_eigenvalue_consistency_residual_above_tolerance",
        is_overshoot=False,
        derives_from=(
            "THE MAXIMUM RUNS OVER SETTINGS AS WELL AS INDICES, which "
            "Eq. eq:res6 writes as 'max over t, N < n <= m*_t'. A declaration "
            "carrying a depth at BOTH settings of I-PROBE, with N = 1 and "
            "m* = 2 at each:\n"
            "  off: beta(2) = 1/8 and an exact beta-hat*(2) = 1/8 "
            "(EB-PROBE-OFF-N2), defect 0;\n"
            "  thermal: beta(2) = 107/750 and an evaluation beta-hat*(2) = "
            "1/10 = 75/750, defect (107 - 75)/750 = 32/750 = 16/375.\n"
            "r_6 = max{0, 16/375} = 16/375, far above eps_6 = 1/1000, so the "
            "request is REFUSED. A per-setting test that reported the OFF "
            "setting's clean residual would report a check the contract does "
            "not define: r_6 is ONE number over the whole declaration."
        ),
    ),
    Residual6Case(
        case_id="R6-PASS-OVERSHOOT-BLIND",
        receiver="I-BS (ONE channel input mode, no probe)",
        photon_cutoff=1,
        entries=(("off", 2, F(1, 2), F(3, 4), F(1, 2), F(0)),),
        r6=F(0),
        tolerance_key="eps_6",
        passes=True,
        refusal_reason=None,
        is_overshoot=True,
        derives_from=(
            "THE ONE DIRECTION r_6 IS BLIND TO, FROZEN AS A PASS BECAUSE THAT "
            "IS WHAT IT IS. At I-BS the exact beta*(2) = 1/2 (EB-BS-N2); an "
            "evaluation returning beta-hat*(2) = 3/4 OVERSHOOTS IT BY 1/4, "
            "which is 250 times the declared eps_eig = 1/1000, so "
            "Eq. eq:eigassumption IS VIOLATED. And the defect Eq. eq:res6 "
            "computes is (beta(2) - beta-hat*(2))_+ = (1/2 - 3/4)_+ = 0, so "
            "r_6 = 0 AND THE REQUEST IS ADMITTED.\n"
            "Rem. rem:exacteig, in the contract's own emphasis: r_6 'does NOT "
            "verify Assumption ass:eig: r_6 FIRES WHEN beta-hat* LANDS TOO "
            "LOW, AND ASSUMPTION ass:eig CONSTRAINS IT FROM LANDING TOO HIGH. "
            "Saying so is the point of stating it. NO TEST IN THIS CONTRACT "
            "BOUNDS THE UNSAFE DIRECTION; the assumption is what carries it.'\n"
            "WHAT THE ADMITTED REQUEST THEN EMITS IS FROZEN SEPARATELY, AS "
            "A_EIG_WITNESS, AND IT IS AN OVER-LARGE LOWER BOUND."
        ),
    ),
)

#: THE PRESENCE RULE FOR r_6, WHICH IS A DIFFERENT RULE FROM r_1 AND r_3's.
#: Def. def:residuals: "r_6 is REQUEST-DEPENDENT, NOT ROUTE-DEPENDENT ... it
#: exists on all three routes BUT ONLY AT THE SETTINGS WHOSE DECLARATION CARRIES
#: AN EXACT-WINDOW DEPTH, over exactly the indices N < n <= m*_t that depth
#: names. A declaration that requests no exact window computes no beta-hat* and
#: HAS NOTHING TO COMPARE, so the key of r_6 is ABSENT there -- absent, not
#: zero, by the same rule and for the same reason as r_1 and r_3 on route (i).
#: eps_6 is then NOT DECLARED EITHER, being conditionally required on the same
#: condition; THIS IS WHERE eps_6 DIFFERS FROM eps_1 AND eps_3, WHICH ARE
#: DECLARED ON EVERY ROUTE AND MERELY UNUSED ON ONE."
#: (declaration, route, r_6 present, eps_6 declared)
RESIDUAL6_REQUEST_PRESENCE: tuple[tuple[str, str, bool, bool], ...] = (
    ("no exact_window depth anywhere", "port_grams", False, False),
    ("no exact_window depth anywhere", "instrument_matrix", False, False),
    ("no exact_window depth anywhere", "element_graph", False, False),
    ("a depth at some setting", "port_grams", True, True),
    ("a depth at some setting", "instrument_matrix", True, True),
    ("a depth at some setting", "element_graph", True, True),
)

#: THE SIX RESIDUALS AT 0.3.0, AND WHICH AXIS EACH IS SCOPED ON. Frozen because
#: the amendment gives the presence rule a SECOND AXIS and an implementation
#: that flattened the two would emit the wrong key set.
#: (residual, scoping axis, present when)
RESIDUAL_SCOPING_0_3_0: tuple[tuple[str, str, str], ...] = (
    ("r_1", "route", "routes (ii) and (iii) only; ABSENT on route (i)"),
    ("r_2", "none", "every route, always"),
    ("r_3", "route", "routes (ii) and (iii) only; ABSENT on route (i)"),
    ("r_4", "none", "every route, always"),
    ("r_5", "none", "every route, always"),
    (
        "r_6",
        "request",
        "every route, but ONLY at the settings carrying an exact_window depth; "
        "ABSENT where none is declared",
    ),
)


# ---------------------------------------------------------------------------
#  Proposition prop:exactnoworse, case by case
# ---------------------------------------------------------------------------
#
#  "At every setting carrying a declared depth, the value Eq. eq:pmcex is AT
#  LEAST the value Eq. eq:pmcdef gives at that setting ON THE SAME BOUND DATA."
#
#  THE COMPARISON IS EXACT-ARITHMETIC, AND Rem. rem:noworsefl SAYS WHERE THAT
#  MATTERS: two of the three steps "survive an evaluation term for term, because
#  they compare evaluated numbers with each other", and the one that does not is
#  "branch 1's beta(m*_t + 1) >= beta(N + 1): that is Lem. lem:collapse, a
#  statement about EXACT values, and beta(m*_t + 1) is a quantity Eq. eq:pmcdef
#  NEVER EVALUATES. So on branch 1 the emitted value CAN SIT BELOW the one
#  Eq. eq:pmcdef would produce BY THE EVALUATION ERROR OF ONE FURTHER beta, and
#  this contract claims no bound on that error." SO `never worse` IS A STATEMENT
#  ABOUT THE MATHEMATICS AND NOT A RUNTIME INVARIANT AN IMPLEMENTATION MAY
#  ASSERT AS A CHECK.
#
#  (case id, p_mc without a depth, p_mc with one, the relation)
NO_WORSE_CASES: tuple[tuple[str, F, F, str], ...] = (
    ("EX-BB84-N1-M2-EIG-ZERO", F(0), F(1, 2), "strictly greater"),
    ("EX-BB84-N1-M2-EIG-1E3", F(0), F(499, 1000), "strictly greater"),
    ("EX-BB84-N1-M2-EIG-HALF", F(0), F(0), "equal"),
    ("EX-BB84-N1-M2-EIG-THREE-QUARTERS", F(0), F(0), "equal"),
    ("EX-BB84-N1-M3-EIG-1E3", F(0), F(499, 1000), "strictly greater"),
    ("EX-BB84-N2-M3-EIG-ZERO", F(1, 2), F(3, 4), "strictly greater"),
    ("EX-BB84-N2-M3-EIG-1E3", F(1, 2), F(3, 4), "strictly greater"),
    ("EX-BB84-PZ7-N1-M2-EIG-ZERO", F(0), F(13, 50), "strictly greater"),
    ("EX-BB84-PZ-QUARTER-N1-M2-EIG-ZERO", F(0), F(1, 8), "strictly greater"),
    ("EX-BS-N1-M2-EIG-1E3", F(1, 2), F(1, 2), "equal"),
    ("EX-PROBE-ON-N1-M3-MSTAR2", F(107, 750), F(107, 750), "equal"),
    ("EX-PROBE-ON-N1-M3-MSTAR3-EMPTY-MIDDLE", F(107, 750), F(107, 750), "equal"),
    ("EX-PROBE-ON-N1-M2-MSTAR2-ZERO", F(0), F(0), "equal"),
)

#: WHICH STEP OF Prop. prop:exactnoworse's PROOF SURVIVES AN EVALUATION AND
#: WHICH DOES NOT (Rem. rem:noworsefl). Frozen as prose because it is the one
#: place an implementation could turn a theorem into a runtime assertion that
#: this contract does not support.
#: (step, survives evaluation, why)
NO_WORSE_UNDER_EVALUATION: tuple[tuple[str, bool, str], ...] = (
    (
        "ell(n) >= beta(n) on the exact window",
        True,
        "it is an EVALUATED maximum -- Eq. eq:elldef's first entry IS beta(n) "
        "as the implementation computed it",
    ),
    (
        "branch 2 minimises over exactly the evaluated beta(n) that "
        "Eq. eq:pmcdef minimises over",
        True,
        "the two expressions read the SAME evaluated numbers, so the "
        "inequality between them is between evaluated quantities",
    ),
    (
        "branch 1's beta(m*_t + 1) >= beta(N + 1)",
        False,
        "that is Lem. lem:collapse, A STATEMENT ABOUT EXACT VALUES, and "
        "beta(m*_t + 1) is a quantity Eq. eq:pmcdef NEVER EVALUATES. On branch "
        "1 the emitted value can therefore sit BELOW Eq. eq:pmcdef's by the "
        "evaluation error of one further beta, and this contract claims no "
        "bound on that error (Thm. thm:exact-and-evaluated (ii)) -- 'as it claims none on the "
        "evaluation of beta(N+1) itself'",
    ),
)


# ---------------------------------------------------------------------------
#  The A-EIG witness: what a violated Eq. eq:eigassumption emits
# ---------------------------------------------------------------------------
#
#  FROZEN SEPARATELY FROM EXACT_WINDOW_CASES, AND DELIBERATELY. Every case in
#  that table satisfies Eq. eq:eigassumption, so every value in it is one the
#  contract supports. This one does NOT, so nothing about it is a theorem of
#  this contract -- it is the concrete instance of what Ass. ass:eig's "If
#  violated" column describes: "the emitted p_mc can EXCEED
#  inf_{n > N} lmin(blk M^{(=n)}_{mc|t}) by the excess overshoot -- AN
#  OVER-LARGE LOWER BOUND, THE UNSAFE DIRECTION, first order in that excess,
#  reaching a key length through Def. def:slot WITH NO LATER CHECK CATCHING IT."
#
#  (field, value or statement)
A_EIG_WITNESS: tuple[tuple[str, str], ...] = (
    ("case", "EX-BS-N1-M2-OVERSHOOT, the I-BS receiver at N = 1, m* = 2"),
    ("declared eps_eig", "1/1000"),
    ("exact beta*(2)", "1/2 (EB-BS-N2; the block is one dimensional)"),
    ("computed beta-hat*(2)", "3/4 -- an overshoot of 1/4"),
    (
        "Eq. eq:eigassumption",
        "VIOLATED: beta-hat*(2) - eps_eig = 749/1000 > 1/2 = beta*(2)",
    ),
    (
        "ell(2)",
        "max{beta(2), beta-hat*(2) - eps_eig} = max{1/2, 749/1000} = 749/1000",
    ),
    ("remainder beta(3)", "3/4 = 750/1000"),
    (
        "emitted p_mc",
        "max{0, min{749/1000, 750/1000}} = 749/1000",
    ),
    (
        "the true uniform bound it claims",
        "inf_{n > 1} lmin(blk M^{(=n)}_mc) = min over n >= 2 of (1 - 2^{1-n}) "
        "= 1/2, attained at n = 2 and increasing thereafter",
    ),
    (
        "the excess",
        "749/1000 - 1/2 = 249/1000, AN OVER-LARGE LOWER BOUND",
    ),
    ("r_6", "0 -- IT PASSES (R6-PASS-OVERSHOOT-BLIND)"),
    (
        "ARCHITECTURE_SPEC.md Section 7.3",
        "NOT TRIGGERED: 749/1000 lies in [0, 1], so neither 'p_y < 0' nor "
        "'sum_y p_y > 1' fires. Rem. rem:exacteig states exactly this: an "
        "overshoot 'large enough to push p_mc above 1 WOULD be caught ... but "
        "AN OVERSHOOT OF THE SIZE eps_eig EXISTS TO BOUND SITS FAR BELOW THAT "
        "THRESHOLD, AND IS CAUGHT BY NOTHING'",
    ),
    (
        "what catches it",
        "NOTHING IN THIS MODULE. That is why Ass. ass:eig is stated, why it is "
        "one-sided, why it is carried in the assumption ledger beside the "
        "settings at which it was invoked, and why Section 1.3 fires the "
        "numerical-lower-bound-certificate escalation trigger from 0.3.0.",
    ),
    (
        "what would discharge it",
        "a rigorous LOWER enclosure of beta*(n) (Rem. rem:ia's fifth "
        "direction), or an exact-arithmetic PSD certificate for "
        "blk M^{(=n)}_mc - s id at a declared rational s on route (i). "
        "NEITHER IS CLAIMED HERE.",
    ),
    (
        "what run B must NOT do with this case",
        "assert it as an expected emitted value. It is frozen as the WITNESS "
        "of a violated assumption, not as a value the contract supports, and "
        "a conforming implementation reaches it only by having an "
        "eigenvalue routine that violates Eq. eq:eigassumption.",
    ),
)


# ---------------------------------------------------------------------------
#  The opt-in invariant, and the settings mixed in one declaration
# ---------------------------------------------------------------------------
#
#  THE INVARIANT THAT MAKES 0.3.0 A STRICT EXTENSION, stated four times in the
#  contract and frozen once here. Def. def:pmc: "A declaration carrying no depth
#  at any setting is governed by Eq. eq:pmcdef ALONE: NO beta* IS FORMED, NO
#  EIGENVALUE OF ANY BLOCK ABOVE THE CUTOFF IS COMPUTED, AND ASSUMPTION ass:eig
#  IS NOT INVOKED."
#
#  THIS IS WHY NOT ONE FROZEN BOUND-DATA CASE IS SUPERSEDED. Each row below
#  names a 0.1.3 case, records that it declares no depth, and states what 0.3.0
#  emits for it -- which is what 0.2.0 emitted, expression for expression.
#  (case id, declares a depth, beta* formed, Ass. ass:eig invoked, r_6 emitted,
#   p_mc unchanged)
OPT_IN_INVARIANT: tuple[tuple[str, bool, bool, bool, bool, bool], ...] = tuple(
    (case.case_id, False, False, False, False, True) for case in BOUND_DATA_CASES
)

#: THE FOUR CASES THE BRIEF FOR THIS FREEZE NAMED, RE-DERIVED RATHER THAN
#: ASSERTED, because "superseded by nothing" is a claim about the amendment and
#: not a convenience. Each row: the case, its cutoff, what it emits, and the
#: 0.3.0 sentence that leaves it standing.
BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0: tuple[tuple[str, int, F, str], ...] = (
    (
        "BD-BB84-N1-ZERO",
        1,
        F(0),
        "N = 1 and NO depth, so Eq. eq:pmcdef applies unchanged: "
        "max{0, beta(2)} = max{0, 0} = 0. The exact window would emit 1/2 at "
        "the same cutoff (EX-BB84-N1-M2-EIG-ZERO), and that is a DIFFERENT "
        "DECLARATION of the same device. Section 1.1 (b), in bold: 'Where no "
        "depth is declared, Definition def:pmc stands EXPRESSION FOR "
        "EXPRESSION, no block above the cutoff is formed, and the emitted "
        "value is the one 0.2.0 emits.'",
    ),
    (
        "BD-BB84-N2",
        2,
        F(1, 2),
        "N = 2 and no depth: max{0, beta(3)} = 1/2, the worked cutoff of "
        "Ex. ex:bb84bound. Eq. eq:pmcdef, Eq. eq:beta and Thm. thm:multiclick-bound "
        "are all byte-identical to 0.2.0's (STATUS.yaml gates.g1, re-checked "
        "by sha256 at every pass), so the value cannot have moved.",
    ),
    (
        "BD-BB84-N3",
        3,
        F(3, 4),
        "N = 3 and no depth: max{0, beta(4)} = 3/4, the second worked cutoff "
        "of Ex. ex:bb84bound, whose closing sentence adds that p_mc -> 1 "
        "exponentially exactly when max(p_Z, p_X) < 1. The same reasoning as "
        "BD-BB84-N2: predicate (X) selects branch 1, Eq. eq:pmcdef applies "
        "unchanged, and the six pinned objects are byte-identical to 0.2.0's.",
    ),
    (
        "BD-BB84-PZ-QUARTER-N2",
        2,
        F(1, 8),
        "N = 2, p_Z = 1/4 and no depth: max{0, beta(3)} = 1/8. The same value "
        "is what a depth at N = 1 emits (EX-BB84-PZ-QUARTER-N1-M2-EIG-ZERO), "
        "which is the amendment's point -- the same bound at a cutoff one "
        "lower -- AND NEITHER CASE SUPERSEDES THE OTHER.",
    ),
)


@dataclass(frozen=True)
class MixedSettingCase:
    """One declaration mixing settings with and without a depth."""

    case_id: str
    receiver: str
    photon_cutoff: int
    #: (setting, depth declared, m*_t or None, the definition that governs it,
    #:  p_mc^(t))
    per_setting: tuple[tuple[str, bool, int | None, str, F], ...]
    #: p_mc = min over t in T of p_mc^(t).
    p_mc: F
    #: Whether Ass. ass:eig is invoked anywhere in this declaration.
    eig_invoked: bool
    derives_from: str


MIXED_SETTING_CASES: tuple[MixedSettingCase, ...] = (
    MixedSettingCase(
        case_id="MIX-NO-DEPTH-ANYWHERE",
        receiver="I-PROBE, T = {off, thermal}, N = 1, m_thermal = 3",
        photon_cutoff=1,
        per_setting=(
            ("off", False, None, "Eq. eq:pmcdef branch 1 (predicate (X))", F(1, 8)),
            ("thermal", False, None, "Eq. eq:pmcdef branch 2", F(107, 750)),
        ),
        p_mc=F(1, 8),
        eig_invoked=False,
        derives_from=(
            "THE 0.2.0 BASELINE, AND THE 0.3.0 VALUE, WHICH ARE THE SAME "
            "NUMBER. No depth is declared, so Eq. eq:pmcdef governs both "
            "settings: at `off` predicate (X) holds by its SECOND clause "
            "(Gamma^(t) = 0, Thm. thm:gaussian-schur (iii)) and branch 1 emits "
            "max{0, beta_off(2)} = 1/8 (BD-PROBE-OFF-N1); at `thermal` (X) "
            "fails and branch 2 with m_t = 3 emits 107/750 "
            "(BD-PROBE-ON-N1-M3).\n"
            "p_mc = min{1/8, 107/750}. Over 750ths that is "
            "min{93.75, 107}/750, so THE MINIMUM IS 1/8. Neither eps_6 nor "
            "eps_eig is declared and neither is an error: Section 2.1 says "
            "they are 'NEITHER REQUIRED NOR AN ERROR when no depth is declared "
            "anywhere'."
        ),
    ),
    MixedSettingCase(
        case_id="MIX-DEPTH-AT-OFF-ONLY",
        receiver="I-PROBE, T = {off, thermal}, N = 1, m_thermal = 3",
        photon_cutoff=1,
        per_setting=(
            ("off", True, 2, "Eq. eq:pmcex branch 1 (predicate (X))", F(1, 8)),
            ("thermal", False, None, "Eq. eq:pmcdef branch 2", F(107, 750)),
        ),
        p_mc=F(1, 8),
        eig_invoked=True,
        derives_from=(
            "THE TWO KINDS OF SETTING MIXED IN ONE DECLARATION, which "
            "Def. def:pmc licenses in terms: 'p_mc = min over T is unchanged, "
            "AND THE TWO KINDS OF SETTING MAY BE MIXED IN ONE DECLARATION'.\n"
            "AT `off`, WITH m* = 2: predicate (X) holds, so Eq. eq:pmcex takes "
            "branch 1. The block is one dimensional (D = |Inp_C| = 1), so "
            "beta*_off(2) = beta_off(2) = 1/8 (EB-PROBE-OFF-N2) and "
            "ell(2) = max{1/8, 1/8 - 1/1000} = 1/8; the remainder is "
            "beta_off(m* + 1) = beta_off(3) = 9/32, and "
            "min{1/8, 9/32} = min{4, 9}/32 = 1/8. So p_mc^(off) = 1/8, "
            "UNCHANGED.\n"
            "AT `thermal`, WITH NO DEPTH: Eq. eq:pmcdef branch 2 gives 107/750, "
            "unchanged. p_mc = min{1/8, 107/750} = 1/8.\n"
            "eps_6 AND eps_eig ARE REQUIRED HERE, because a depth is declared "
            "SOMEWHERE: Section 2.1 scopes the requirement to the declaration, "
            "not to the setting. And Ass. ass:eig IS INVOKED -- at the `off` "
            "setting only, which is what Section 2.2 records per setting."
        ),
    ),
    MixedSettingCase(
        case_id="MIX-DEPTH-AT-THERMAL-ONLY",
        receiver="I-PROBE, T = {off, thermal}, N = 1, m_thermal = 3",
        photon_cutoff=1,
        per_setting=(
            ("off", False, None, "Eq. eq:pmcdef branch 1 (predicate (X))", F(1, 8)),
            ("thermal", True, 2, "Eq. eq:pmcex branch 2", F(107, 750)),
        ),
        p_mc=F(1, 8),
        eig_invoked=True,
        derives_from=(
            "THE SENTENCE Def. def:pmcex CLOSES ITS REFUSALS PARAGRAPH WITH, "
            "MADE CONCRETE: 'The depth is optional and per setting, and since "
            "p_mc = min over t in T of p_mc^(t) A CALLER WHO DECLARES ONE AT "
            "SOME SETTINGS AND NOT AT OTHERS IS BOUNDED BY THE SETTINGS "
            "WITHOUT ONE.'\n"
            "Here the depth is at `thermal`, where EX-PROBE-ON-N1-M3-MSTAR2 "
            "shows it changes nothing (107/750), and `off` carries none and "
            "emits 1/8 by Eq. eq:pmcdef. p_mc = min{1/8, 107/750} = 1/8, AND "
            "THE BOUNDING SETTING IS THE ONE WITHOUT A DEPTH.\n"
            "SO THE COST WAS PAID AT ONE SETTING AND THE ANSWER WAS DECIDED AT "
            "THE OTHER. An implementation that reported the improved setting's "
            "value would be reporting a per-setting quantity as the emitted "
            "one, which Ex. ex:bb84bound's own closure (round-3 finding "
            "F-3-01) warns against."
        ),
    ),
    MixedSettingCase(
        case_id="MIX-DEPTH-AT-BOTH",
        receiver="I-PROBE, T = {off, thermal}, N = 1, m_thermal = 3",
        photon_cutoff=1,
        per_setting=(
            ("off", True, 2, "Eq. eq:pmcex branch 1 (predicate (X))", F(1, 8)),
            ("thermal", True, 2, "Eq. eq:pmcex branch 2", F(107, 750)),
        ),
        p_mc=F(1, 8),
        eig_invoked=True,
        derives_from=(
            "A DEPTH EVERYWHERE, AND STILL NOTHING GAINED, WHICH IS A PROPERTY "
            "OF THIS RECEIVER AND NOT OF THE AMENDMENT. I-PROBE has "
            "|Inp_C| = 1, so every channel block is one dimensional and "
            "Eq. eq:mcbound holds WITH EQUALITY at every index and both "
            "settings (EB-PROBE-OFF-N2, EB-PROBE-ON-N2). Eq. eq:elldef's "
            "analytic floor therefore wins everywhere and both per-setting "
            "values are exactly what Eq. eq:pmcdef gives.\n"
            "p_mc = min{1/8, 107/750} = 1/8, THE SAME AS "
            "MIX-NO-DEPTH-ANYWHERE. The declaration paid for two eigenvalue "
            "problems and bought nothing.\n"
            "THE IMPROVEMENT IS EXERCISED AT I-BB84 INSTEAD, which has "
            "|Inp_C| = 2 and one setting: EX-BB84-N1-M2-EIG-ZERO (0 -> 1/2) "
            "and EX-BB84-N2-M3-EIG-ZERO (1/2 -> 3/4). NO FROZEN RECEIVER OF "
            "THIS REGISTRY HAS BOTH A MULTI-DIMENSIONAL CHANNEL SPACE AND MORE "
            "THAN ONE PROBE SETTING, so the two facts -- that the window can "
            "improve a value, and that the minimum over T is taken afterwards "
            "-- are frozen at two different receivers rather than at one. "
            "RECORDED SO THAT THE GAP IS VISIBLE RATHER THAN INFERRED."
        ),
    ),
)


# ---------------------------------------------------------------------------
#  Group RP-V -- the three new refusals and the exact-window validation matrix
# ---------------------------------------------------------------------------
#
#  Section 2.6 gains THREE rows at 0.3.0 and loses none. Section 2.1
#  `exact_window` and Def. def:pmcex's Refusals paragraph state the conditions;
#  the table gives them their verbatim spellings. Every validation below is a
#  comparison against a declared domain or a combinatorial predicate on the
#  declaration -- Def. def:tolmap's closing enumeration lists m*_t > N and
#  m*_t <= m_t under kind (a) and the conditional presence of eps_eig and eps_6
#  under kind (b) -- so NO NEW THRESHOLD DECIDES ANY OF THEM.


@dataclass(frozen=True)
class ExactWindowValidationCase:
    """One admit/refuse decision on an `exact_window` declaration."""

    case_id: str
    photon_cutoff: int
    #: Whether predicate (X) of Def. def:pmc holds at the setting.
    predicate_x: bool
    #: The declared tail_window m_t, or None where none is declared.
    tail_window: int | None
    #: The declared depth m*_t, or None where none is declared.
    exact_depth: int | None
    eps_eig_declared: bool
    eps_6_declared: bool
    admitted: bool
    #: The verbatim reason where the case refuses; None where it is admitted.
    refusal_reason: str | None
    derives_from: str


EXACT_WINDOW_VALIDATION_CASES: tuple[ExactWindowValidationCase, ...] = (
    ExactWindowValidationCase(
        case_id="XW-ADMIT-NO-DEPTH-NO-CONDITIONAL-TOLERANCES",
        photon_cutoff=1,
        predicate_x=True,
        tail_window=None,
        exact_depth=None,
        eps_eig_declared=False,
        eps_6_declared=False,
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE OPT-OUT, ADMITTED WITH NEITHER CONDITIONAL TOLERANCE. "
            "Section 2.1 `numerical_tolerances`: eps_6 and eps_eig are "
            "'required exactly where an exact_window depth is declared, "
            "refused when missing there, AND NEITHER REQUIRED NOR AN ERROR "
            "WHEN NO DEPTH IS DECLARED ANYWHERE'. This is every 0.2.0 "
            "declaration, and it is why no frozen 0.1.3 or 0.2.0 case is "
            "invalidated by the amendment."
        ),
    ),
    ExactWindowValidationCase(
        case_id="XW-ADMIT-MINIMAL-DEPTH",
        photon_cutoff=1,
        predicate_x=True,
        tail_window=None,
        exact_depth=2,
        eps_eig_declared=True,
        eps_6_declared=True,
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE MINIMAL DEPTH m* = N + 1 = 2, which Ex. ex:bb84exact declares "
            "('Declare the minimal depth m* = N + 1 = 2') and which is "
            "ADMITTED because the constraint is m*_t > N, strictly. Predicate "
            "(X) holds, so no tail_window is declared and none constrains the "
            "depth. Both conditional tolerances are supplied.\n"
            "MINIMAL IS NOT DEFAULT. The contract states no default for the "
            "depth -- 'the depth is the caller's and this contract states no "
            "default for it' -- so an implementation that supplied N + 1 where "
            "the caller supplied nothing would be declaring an input on the "
            "caller's behalf (Section 1.2, decision dd:exactwindow: 'a "
            "platform default would be an undeclared number')."
        ),
    ),
    ExactWindowValidationCase(
        case_id="XW-ADMIT-DEEP-DEPTH-WHERE-X-HOLDS",
        photon_cutoff=1,
        predicate_x=True,
        tail_window=None,
        exact_depth=5,
        eps_eig_declared=True,
        eps_6_declared=True,
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "A DEPTH FAR ABOVE THE CUTOFF WHERE (X) HOLDS, ADMITTED BECAUSE "
            "NOTHING BOUNDS IT FROM ABOVE THERE. Def. def:pmcex constrains the "
            "depth by 'm*_t > N and, WHERE PREDICATE (X) FAILS AT t, ALSO "
            "m*_t <= m_t' -- so at a setting where (X) HOLDS the second "
            "constraint does not apply, and it cannot: no tail_window is "
            "required there at all (Rem. rem:windowdecidable, 'a probe-free "
            "receiver declares no window'). Branch 1's remainder "
            "beta(m* + 1) = beta(6) is defined at every depth.\n"
            "WHAT IT COSTS IS THE CALLER'S PROBLEM AND IS STATED: four "
            "eigenvalue problems of dimensions binom(|Inp_C| + n - 1, n) for "
            "n = 2, 3, 4, 5."
        ),
    ),
    ExactWindowValidationCase(
        case_id="XW-ADMIT-DEPTH-EQUALS-TAIL-WINDOW",
        photon_cutoff=1,
        predicate_x=False,
        tail_window=3,
        exact_depth=3,
        eps_eig_declared=True,
        eps_6_declared=True,
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE BOUNDARY OF THE SECOND CONSTRAINT, ADMITTED. The constraint "
            "is m*_t <= m_t, so equality is inside it. This is the "
            "declaration EX-PROBE-ON-N1-M3-MSTAR3-EMPTY-MIDDLE evaluates, "
            "where Eq. eq:pmcex's middle minimum runs 'OVER THE EMPTY INDEX "
            "SET -- and so equal to +infinity and INACTIVE'."
        ),
    ),
    ExactWindowValidationCase(
        case_id="XW-ADMIT-DEPTH-EXCEEDS-UNUSED-TAIL-WINDOW",
        photon_cutoff=1,
        predicate_x=True,
        tail_window=3,
        exact_depth=5,
        eps_eig_declared=True,
        eps_6_declared=True,
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE SECOND CONSTRAINT IS SCOPED, AND THE SCOPE IS WRITTEN INTO "
            "IT. Here predicate (X) HOLDS, a tail_window IS supplied -- which "
            "Rem. rem:windowdecidable calls 'UNUSED, NOT AN ERROR' -- and the "
            "depth m* = 5 EXCEEDS it. THE DECLARATION IS ADMITTED.\n"
            "Def. def:pmcex constrains the depth by 'm*_t > N and, WHERE "
            "PREDICATE (X) FAILS AT t, ALSO m*_t <= m_t'. Where (X) holds the "
            "second clause does not apply, and it could not sensibly: branch 1 "
            "is taken, its remainder is beta(m*_t + 1), and m_t enters no "
            "expression Eq. eq:pmcex evaluates. The reading is SOUND as well "
            "as literal -- branch 1's remainder is admissible at every depth "
            "by Lem. lem:exactwindow (ii), which needs only Eq. eq:collapsehyp, "
            "which predicate (X) supplies EXACTLY.\n"
            "THE CONTRAST IS XW-REFUSE-DEPTH-EXCEEDS-TAIL-WINDOW: THE SAME "
            "ARITHMETIC at a setting where (X) FAILS, and there it is REFUSED, "
            "because branch 2 keeps its own analytic window above the exact "
            "one and the two must compose."
        ),
    ),
    ExactWindowValidationCase(
        case_id="XW-REFUSE-DEPTH-AT-THE-CUTOFF",
        photon_cutoff=1,
        predicate_x=True,
        tail_window=None,
        exact_depth=1,
        eps_eig_declared=True,
        eps_6_declared=True,
        admitted=False,
        refusal_reason="exact_window_depth_outside_declared_range",
        derives_from=(
            "m*_t = N, WHICH FAILS THE STRICT INEQUALITY AND IS REFUSED. "
            "Def. def:pmcex requires m*_t > N; Section 2.6 row 7 gives the "
            "verbatim reason `exact_window_depth_outside_declared_range`.\n"
            "WHY STRICT: the exact window is over N < n <= m*_t, and at "
            "m*_t = N that index set is EMPTY. Lem. lem:exactwindow requires "
            "m* > N and uses it -- its proof of P <= 1 reads 'the window being "
            "NON-EMPTY BECAUSE m* > N'. A depth at the cutoff would leave "
            "Eq. eq:pmcex minimising over nothing."
        ),
    ),
    ExactWindowValidationCase(
        case_id="XW-REFUSE-DEPTH-BELOW-THE-CUTOFF",
        photon_cutoff=2,
        predicate_x=True,
        tail_window=None,
        exact_depth=1,
        eps_eig_declared=True,
        eps_6_declared=True,
        admitted=False,
        refusal_reason="exact_window_depth_outside_declared_range",
        derives_from=(
            "m*_t < N, THE SAME REFUSAL ONE STEP FURTHER OUT. At N = 2 a depth "
            "of 1 names a block the artifact EMITS EXACTLY "
            "(`photon_blocks`, 0 <= n <= N) rather than one above the cutoff, "
            "so it is not merely empty but wrong in kind. Refused under the "
            "same rule and with the same verbatim reason; the contract states "
            "one condition, m*_t > N, and not two."
        ),
    ),
    ExactWindowValidationCase(
        case_id="XW-REFUSE-DEPTH-EXCEEDS-TAIL-WINDOW",
        photon_cutoff=1,
        predicate_x=False,
        tail_window=3,
        exact_depth=4,
        eps_eig_declared=True,
        eps_6_declared=True,
        admitted=False,
        refusal_reason="exact_window_depth_outside_declared_range",
        derives_from=(
            "THE SECOND CONSTRAINT, AT A SETTING WHERE PREDICATE (X) FAILS. "
            "m*_t = 4 > 3 = m_t is REFUSED, and Def. def:pmcex gives the "
            "reason in the sentence that states the constraint: branch 2 "
            "'keeps its own analytic window and tail above the exact one -- "
            "WHICH IS WHY m*_t <= m_t IS REQUIRED THERE, SO THAT THE TWO "
            "WINDOWS COMPOSE INTO THE SINGLE WINDOW N < n <= m_t THAT "
            "Lem. lem:exactwindow IS APPLIED TO'.\n"
            "AT m*_t > m_t THE COMPOSITION BREAKS: the analytic middle window "
            "m*_t < n <= m_t would be empty in the WRONG direction, and the "
            "tail T_{m_t} would cover indices the exact window has already "
            "claimed, so Lem. lem:exactwindow's hypotheses would not be met by "
            "the expression Eq. eq:pmcex writes. THE REFUSAL IS NOT A "
            "CONVENIENCE."
        ),
    ),
    ExactWindowValidationCase(
        case_id="XW-REFUSE-DEPTH-WITHOUT-EPS-EIG",
        photon_cutoff=1,
        predicate_x=True,
        tail_window=None,
        exact_depth=2,
        eps_eig_declared=False,
        eps_6_declared=True,
        admitted=False,
        refusal_reason="exact_window_declared_without_required_tolerance",
        derives_from=(
            "A DEPTH WITHOUT ITS SLACK, REFUSED RATHER THAN DEFAULTED. "
            "Def. def:pmcex: 'Declaring a depth at any setting requires "
            "eps_eig and eps_6; A MISSING ONE IS REFUSED RATHER THAN "
            "DEFAULTED, EXACTLY AS A MISSING m_t IS.' Section 2.6 row 6 gives "
            "the verbatim reason.\n"
            "IT MATTERS THAT IT IS NOT DEFAULTED TO ZERO. eps_eig = 0 is "
            "inside the declared domain and is admissible, but declaring it is "
            "declaring that 'the eigenvalue routine never overshoots at all' "
            "(the G3 packet's item (1), signed with); SUPPLYING IT SILENTLY "
            "WOULD MAKE THAT ASSERTION ON THE CALLER'S BEHALF."
        ),
    ),
    ExactWindowValidationCase(
        case_id="XW-REFUSE-DEPTH-WITHOUT-EPS-6",
        photon_cutoff=1,
        predicate_x=True,
        tail_window=None,
        exact_depth=2,
        eps_eig_declared=True,
        eps_6_declared=False,
        admitted=False,
        refusal_reason="exact_window_declared_without_required_tolerance",
        derives_from=(
            "THE OTHER HALF OF THE SAME ROW, AND IT SHARES THE REASON STRING. "
            "Section 2.6's condition column reads 'An exact_window depth is "
            "declared AND eps_eig OR eps_6 IS NOT', so ONE reason covers both "
            "omissions and an implementation must not invent a second. "
            "Without eps_6 there is no threshold for r_6, and without a "
            "threshold the `fail_closed` convention 'has no threshold to test' "
            "(Section 2.1)."
        ),
    ),
)

#: The three new refusals as REFUSAL_CASES rows, so that the vocabulary check
#: covers them the way it covers the 0.2.0 five.
REFUSAL_CASES_0_3_0: tuple[RefusalCase, ...] = (
    RefusalCase(
        case_id="REF-EXACT-WINDOW-MISSING-TOLERANCE",
        subject=(
            "a declaration carrying an `exact_window` depth at some setting "
            "while eps_eig or eps_6 is absent"
        ),
        failing_condition=(
            "Section 2.1 / Def. def:pmcex: declaring a depth anywhere requires "
            "eps_eig AND eps_6"
        ),
        reason_is_verbatim=True,
        reason="exact_window_declared_without_required_tolerance",
        emits_artifact=False,
        derives_from=(
            "SECTION 2.6, ROW 6. Def. def:pmcex's Refusals paragraph: "
            "'Declaring a depth at any setting requires eps_eig and eps_6; a "
            "missing one is REFUSED RATHER THAN DEFAULTED, exactly as a "
            "missing m_t is.' Section 2.1 `numerical_tolerances` states the "
            "same requirement from the tolerance side and adds the negative "
            "half: the two are 'NEITHER REQUIRED NOR AN ERROR when no depth is "
            "declared anywhere'. ONE STRING COVERS BOTH OMISSIONS, the "
            "condition column reading 'eps_eig OR eps_6 is not'. Frozen with "
            "XW-REFUSE-DEPTH-WITHOUT-EPS-EIG and XW-REFUSE-DEPTH-WITHOUT-EPS-6."
        ),
    ),
    RefusalCase(
        case_id="REF-EXACT-WINDOW-DEPTH-OUT-OF-RANGE",
        subject=(
            "a declared depth violating m*_t > N, or violating m*_t <= m_t at "
            "a setting where predicate (X) fails"
        ),
        failing_condition=(
            "Def. def:pmcex: m*_t > N always, and m*_t <= m_t where (X) fails"
        ),
        reason_is_verbatim=True,
        reason="exact_window_depth_outside_declared_range",
        emits_artifact=False,
        derives_from=(
            "SECTION 2.6, ROW 7. TWO CONDITIONS UNDER ONE STRING, and the "
            "second applies ONLY where predicate (X) fails: 'A depth violating "
            "m*_t > N, OR violating m*_t <= m_t AT A SETTING WHERE (X) FAILS, "
            "is refused.' Both are kind (a) of Def. def:tolmap's closing "
            "enumeration -- 'a comparison of declared data against a declared "
            "domain' -- which now lists m*_t > N and m*_t <= m_t explicitly, "
            "so NO TOLERANCE DECIDES EITHER. Frozen with "
            "XW-REFUSE-DEPTH-AT-THE-CUTOFF, XW-REFUSE-DEPTH-BELOW-THE-CUTOFF "
            "and XW-REFUSE-DEPTH-EXCEEDS-TAIL-WINDOW, and with the two admits "
            "at the boundaries, XW-ADMIT-MINIMAL-DEPTH and "
            "XW-ADMIT-DEPTH-EQUALS-TAIL-WINDOW."
        ),
    ),
    RefusalCase(
        case_id="REF-R6-ABOVE-TOLERANCE",
        subject=(
            "a computed exact window that contradicts Thm. thm:multiclick-bound: r_6 > eps_6"
        ),
        failing_condition=(
            "Def. def:residuals Eq. eq:res6: the window consistency defect "
            "exceeds its declared tolerance"
        ),
        reason_is_verbatim=True,
        reason="window_eigenvalue_consistency_residual_above_tolerance",
        emits_artifact=False,
        derives_from=(
            "SECTION 2.6, ROW 8, AND Def. def:residuals. 'Each residual that "
            "exists is compared against its declared numerical tolerance, and "
            "a residual above tolerance is a REFUSAL, NOT A WARNING; in "
            "particular ... r_6 > eps_6 [refuses] with the reason "
            "`window_eigenvalue_consistency_residual_above_tolerance`.' THE "
            "DIRECTION IS REFUSE-ONLY: 'The same holds of r_6: IT REFUSES, IT "
            "REPAIRS NOTHING, and Rem. rem:exacteig states which direction of "
            "failure it is blind to.' Frozen with R6-FAIL-UNDERSHOOT, "
            "R6-FAIL-AT-THE-SECOND-INDEX and R6-FAIL-ACROSS-SETTINGS, and "
            "with the blind direction as R6-PASS-OVERSHOOT-BLIND."
        ),
    ),
    RefusalCase(
        case_id="REF-TOLMAP-IV-C-REFUSED-NO-SPELLING",
        subject=(
            "bound data whose computed c = 1 - lmax(B) falls below -eps_2, "
            "including the whole band c in [-eps_1, -eps_2) that item (v)'s "
            "test would admit"
        ),
        failing_condition=(
            "Def. def:tolmap (iv): the bound-data admissibility test "
            "c >= -eps_2, which decides this ALONE on every input route"
        ),
        reason_is_verbatim=False,
        reason=None,
        emits_artifact=False,
        derives_from=(
            "NEW AT 0.3.0, AND THE ONLY 0.3.0 REFUSAL WITH NO SPELLED REASON. "
            "0.2.0 stated the test and did NOT state that its failure is a "
            "refusal; item (iv) now does: 'Bound data failing item (iv) is a "
            "failed validation, so `fail_closed` (Section 2.5) APPLIES AT THIS "
            "SITE: NO ARTIFACT IS EMITTED.'\n"
            "AND IT DELIBERATELY ADDS NO STRING: 'The reason string is THE "
            "IMPLEMENTER'S TO NAME, under the rule the preamble of Section 2.6 "
            "states for the validations that section does not tabulate -- NONE "
            "OF ITS TABULATED STRINGS COVERS THIS CHECK -- and this amendment "
            "deliberately adds none, because fixing a contract-verbatim key "
            "here would settle an interface detail that no claim of this "
            "contract consumes.' Section 1.1 (f) calls it 'the one place the "
            "narrower option was taken', and the G3 packet put the "
            "alternative to the signer as item (2); he signed without it. SO "
            "`reason` IS None HERE AND NO SPELLING IS INVENTED. The verdict, "
            "the threshold and the fail-closed consequence are frozen; the "
            "key is not."
        ),
    ),
)


# ---------------------------------------------------------------------------
#  Group RP-W -- Definition def:tolmap (iv) decides c ALONE (RC9)
# ---------------------------------------------------------------------------
#
#  THE SECOND HUMAN RULING THIS AMENDMENT EXECUTES, and it was routed to this
#  drafter at the 0.2.0 G5. 0.2.0 left open which of items (iv) and (v) decides
#  the admissibility of c, "AND IT IS REACHABLE: item (v) admits a route-(ii)
#  Gamma at eps_1 while item (iv) decides the derived c at eps_2, so at the
#  ORDINARY declaration eps_1 > eps_2 the band c in [-eps_1, -eps_2)
#  (Eq. eq:tolmapband) is ADMITTED BY ONE AND REFUSED BY THE OTHER."
#
#  ITEM (iv) WINS. The band is REFUSED. NO INTERFACE KEY CHANGES AND NO EMITTED
#  VALUE CHANGES: "an implementation of 0.2.0 that refused the band is ALREADY
#  CONFORMING and needs no change at G4; the other reading is the one that would
#  have been a change, AND IT IS THE ONE THAT LOSES."
#
#  THE MAIN FIXTURE CANNOT EXHIBIT THE BAND, and that is itself a fact worth
#  freezing: at eps_1 = eps_2 = 1/1000 the interval [-1/1000, -1/1000) is EMPTY.
#  Item (v)'s closing sentence says so: "A declarer who wants one slack on
#  lmax(A_Sigma) regardless of route declares eps_1 = eps_2, WHICH ALSO EMPTIES
#  Eq. eq:tolmapband." So these cases use TOLMAP_IV_BAND_FIXTURE.


@dataclass(frozen=True)
class TolmapPrecedenceCase:
    """One computed c decided under Def. def:tolmap (iv), with (v) beside it."""

    case_id: str
    #: The computed c = 1 - lmax(B), UNCLAMPED as Eq. eq:beta receives it.
    c: F
    eps_1: F
    eps_2: F
    #: Whether c lies in the band Eq. eq:tolmapband = [-eps_1, -eps_2).
    in_band: bool
    #: Item (iv)'s verdict: admitted when c >= -eps_2.
    item_iv_admits: bool
    #: What the LOSING reading would have said -- the derived c inheriting
    #: eps_1 from item (v)'s route-(ii) admission.
    losing_reading_admits: bool
    #: The contract's verdict, which is item (iv)'s.
    admitted: bool
    #: None at every row: the contract deliberately spells no reason here.
    refusal_reason: str | None
    derives_from: str


TOLMAP_IV_PRECEDENCE_CASES: tuple[TolmapPrecedenceCase, ...] = (
    TolmapPrecedenceCase(
        case_id="TOLMAP-IV-BAND-INTERIOR-REFUSE",
        c=F(-1, 200),
        eps_1=F(1, 100),
        eps_2=F(1, 1000),
        in_band=True,
        item_iv_admits=False,
        losing_reading_admits=True,
        admitted=False,
        refusal_reason=None,
        derives_from=(
            "THE BAND'S INTERIOR, WHERE THE TWO READINGS DISAGREE AND THE "
            "CONTRACT NOW DECIDES. At eps_1 = 1/100 and eps_2 = 1/1000 the "
            "band Eq. eq:tolmapband is [-1/100, -1/1000), and c = -1/200 = "
            "-0.005 lies strictly inside it: -0.01 <= -0.005 < -0.001.\n"
            "ITEM (iv) REFUSES, because its test is c >= -eps_2 and "
            "-1/200 < -1/1000. THE LOSING READING WOULD ADMIT, because it lets "
            "the derived c inherit eps_1 from item (v)'s route-(ii) admission "
            "and -1/200 >= -1/100.\n"
            "ITEM (iv) WINS, on two independent grounds the contract derives. "
            "(2) 'Item (v) NEVER ESTABLISHES ITS EXACT CONDITION. It admits "
            "under a widened test on a COMPUTED number, and Thm. thm:exact-and-evaluated (ii) "
            "bounds the distance from that number to the exact one BY NOTHING "
            "AT ALL. So what step (1) transports is an implication between "
            "exact quantities and NO IMPLICATION WHATEVER BETWEEN THE TWO "
            "COMPUTED QUANTITIES, which are separated by at least one matrix "
            "product and, at a probe-on setting, by a Schur complement as "
            "well. Reading item (v) as admitting anything under item (iv) is "
            "READING AN EXACT IMPLICATION AS A BOUND ON AN EVALUATION, WHICH "
            "IS THE ONE SUBSTITUTION Thm. thm:exact-and-evaluated (ii) EXISTS TO FORBID.' "
            "(3) is quantitative and is frozen as "
            "TOLMAP_IV_BAND_COST.\n"
            "NO REASON STRING IS FROZEN, because the contract spells none "
            "here (REF-TOLMAP-IV-C-REFUSED-NO-SPELLING)."
        ),
    ),
    TolmapPrecedenceCase(
        case_id="TOLMAP-IV-BAND-LEFT-ENDPOINT-REFUSE",
        c=F(-1, 100),
        eps_1=F(1, 100),
        eps_2=F(1, 1000),
        in_band=True,
        item_iv_admits=False,
        losing_reading_admits=True,
        admitted=False,
        refusal_reason=None,
        derives_from=(
            "THE LEFT ENDPOINT, WHICH IS IN THE BAND. Eq. eq:tolmapband is "
            "written c in [-eps_1, -eps_2), CLOSED ON THE LEFT, so c = -eps_1 "
            "= -1/100 belongs to it. Item (iv) refuses (-1/100 < -1/1000); "
            "the losing reading would admit at exactly its own boundary, its "
            "test being c >= -eps_1 with the same non-strict comparison item "
            "(iv) uses at eps_2. REFUSED."
        ),
    ),
    TolmapPrecedenceCase(
        case_id="TOLMAP-IV-BAND-RIGHT-ENDPOINT-EXCLUDED-ADMIT",
        c=F(-1, 1000),
        eps_1=F(1, 100),
        eps_2=F(1, 1000),
        in_band=False,
        item_iv_admits=True,
        losing_reading_admits=True,
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE RIGHT ENDPOINT, WHICH IS NOT IN THE BAND, AND THE HALF-OPEN "
            "INTERVAL IS WHY. c = -eps_2 = -1/1000 satisfies item (iv)'s "
            "c >= -eps_2 WITH EQUALITY, so it is ADMITTED -- and it is "
            "therefore excluded from Eq. eq:tolmapband, which is written "
            "[-eps_1, -eps_2) with the right end OPEN precisely so that the "
            "band is exactly the set the two readings disagree about.\n"
            "THE 0.2.0 CASE TOLMAP-IV-C-BOUNDARY-ADMIT FREEZES THE SAME "
            "NUMBER AT eps_1 = eps_2 = 1/1000 AND IS NOT SUPERSEDED: the "
            "verdict is the same, the reasoning is the same, and only the "
            "surrounding fixture differs. AND NOTHING IS CLAMPED: 'the "
            "computed c enters Eq. eq:beta EXACTLY AS IT STANDS'."
        ),
    ),
    TolmapPrecedenceCase(
        case_id="TOLMAP-IV-BELOW-THE-BAND-BOTH-REFUSE",
        c=F(-1, 50),
        eps_1=F(1, 100),
        eps_2=F(1, 1000),
        in_band=False,
        item_iv_admits=False,
        losing_reading_admits=False,
        admitted=False,
        refusal_reason=None,
        derives_from=(
            "BELOW THE BAND, WHERE THE TWO READINGS AGREE. c = -1/50 = -0.02 "
            "is below -eps_1 = -0.01, so BOTH item (iv)'s test and the losing "
            "reading's refuse it. FROZEN BECAUSE THE BAND IS EXACTLY WHERE "
            "THEY DISAGREE and a case outside it on either side is not "
            "evidence about the ruling. The pair with "
            "TOLMAP-IV-BAND-RIGHT-ENDPOINT-EXCLUDED-ADMIT brackets the band "
            "from both sides."
        ),
    ),
    TolmapPrecedenceCase(
        case_id="TOLMAP-IV-LOSSLESS-C-ZERO-ADMIT",
        c=F(0),
        eps_1=F(1, 100),
        eps_2=F(1, 1000),
        in_band=False,
        item_iv_admits=True,
        losing_reading_admits=True,
        admitted=True,
        refusal_reason=None,
        derives_from=(
            "THE LOSSLESS RECEIVER, ADMITTED BY BOTH READINGS AND BY THE EXACT "
            "CONDITION. c = 1 - lmax(B) = 0 at the BB84 receiver of "
            "Ex. ex:bb84bound, where A_Sigma = id. Frozen as the anchor: the "
            "widening exists for 'a lossless receiver whose computed lmax(B) "
            "sits a rounding unit above 1', and item (iv)'s step (4) says "
            "'NOTHING IS LOST BY ITEM (iv) DECIDING' precisely because THAT "
            "case is admitted by item (iv)'s own -eps_2."
        ),
    ),
)

#: THE BAND AT eps_1 = eps_2, WHERE IT IS EMPTY AND THE QUESTION CANNOT ARISE.
#: Item (v)'s closing sentence, and the main fixture's own configuration.
#: (eps_1, eps_2, the band as an interval, whether it is empty)
TOLMAP_IV_BAND_EMPTY_AT_EQUAL_EPS: tuple[F, F, tuple[F, F], bool] = (
    F(1, 1000),
    F(1, 1000),
    (F(-1, 1000), F(-1, 1000)),
    True,
)

#: STEP (3) OF ITEM (iv)'s DERIVATION, QUANTITATIVELY. "Rem. rem:cdirection
#: bounds the even-n overshoot of the unclamped evaluation by
#: (K-1) |c|^n <= (K-1) eps_2^2, AND THAT BOUND IS STATED IN eps_2 BECAUSE ITEM
#: (iv) IS WHAT BOUNDS |c|. Admitting Eq. eq:tolmapband would make |c| as large
#: as eps_1 and the true bound (K-1) eps_1^2 -- larger by the factor
#: (eps_1/eps_2)^2, which at an ordinary pair of declared numbers is many orders
#: of magnitude. A STATED ERROR TERM OF THIS CONTRACT WOULD THEN BE FALSE ON
#: VALUES THIS CONTRACT ADMITS, in the direction where the evaluated beta(n)
#: EXCEEDS the exact one, WHICH IS THE DIRECTION THAT REACHES A KEY LENGTH."
#: Frozen at K = 4, gamma = 1 and the band fixture. (quantity, value)
TOLMAP_IV_BAND_COST: tuple[tuple[str, F], ...] = (
    ("K - 1, at the BB84 receiver's K = 4", F(3)),
    ("the STATED even-n bound (K-1) eps_2^2, at eps_2 = 1/1000", F(3, 1000000)),
    (
        "the bound that would be TRUE under the losing reading, "
        "(K-1) eps_1^2 at eps_1 = 1/100",
        F(3, 10000),
    ),
    ("the factor between them, (eps_1 / eps_2)^2", F(100)),
    (
        "the ACTUAL even-n = 2 overshoot at the admitted band value "
        "c = -1/200, namely (K-1) gamma |c|^2",
        F(3, 40000),
    ),
    (
        "by what factor that actual overshoot exceeds the STATED bound (K-1) eps_2^2",
        F(25),
    ),
)

#: THE FOUR STEPS OF ITEM (iv)'s DERIVATION, as prose, because they are what an
#: implementation must not contradict and what a verifier re-derives.
#: (step, statement)
TOLMAP_IV_DERIVATION: tuple[tuple[str, str], ...] = (
    (
        "(1)",
        "IN EXACT ARITHMETIC ITEM (v)'s CONDITION IMPLIES ITEM (iv)'s, SO ITEM "
        "(iv) IS REDUNDANT -- EXACTLY. Gamma^dagger Gamma <= id gives "
        "A_Sigma <= Gamma_Inp^dagger Gamma_Inp <= id by Thm. thm:port-grams (i), "
        "hence lmax(A_Sigma) <= 1 and c >= 0; and at a probe-on setting "
        "B = A^{(t),eff}_{[K]} <= id by Lem. lem:schurmono, hence c >= 0 again.",
    ),
    (
        "(2)",
        "BUT ITEM (v) NEVER ESTABLISHES ITS EXACT CONDITION. It admits under a "
        "widened test on a COMPUTED number, and Thm. thm:exact-and-evaluated (ii) bounds the "
        "distance from that number to the exact one by nothing at all. So step "
        "(1) transports an implication between exact quantities and NO "
        "IMPLICATION WHATEVER between the two computed quantities. This step is "
        "also why item (iv) is NOT REDUNDANT ON ROUTE (i), where step (1) holds "
        "just as well from sum_k A_k <= id: 'REDUNDANCY OF THE EXACT CONDITION "
        "IS NOT ADMISSION OF THE COMPUTED ONE'.",
    ),
    (
        "(3)",
        "THE BAND IS NOT EMPTY OF CONSEQUENCE, AND THE CONSEQUENCE IS "
        "QUANTITATIVE AND UNSAFE. Rem. rem:cdirection's even-n overshoot bound "
        "is stated in eps_2 BECAUSE item (iv) is what bounds |c|; admitting the "
        "band would make a stated error term of this contract FALSE on values "
        "the contract admits, in the direction where the evaluated beta(n) "
        "exceeds the exact one. Frozen numerically as TOLMAP_IV_BAND_COST.",
    ),
    (
        "(4)",
        "NOTHING IS LOST BY ITEM (iv) DECIDING. The case the widening exists "
        "for -- a lossless receiver whose computed lmax(B) sits a rounding unit "
        "above 1 -- is admitted by item (iv)'s own -eps_2; and item (iv) tests "
        "THE VERY QUANTITY THAT ENTERS Eq. eq:beta, where item (v) tests one "
        "two computations upstream. 'A declarer who wants the wider band "
        "declares a wider eps_2, which is what a declared tolerance is for and "
        "WHICH CARRIES THE STATED ERROR TERM WITH IT, rather than leaving it "
        "behind.'",
    ),
    (
        "the reading that loses, recorded",
        "'item (v), being the route's own admission rule, settles admissibility "
        "for everything derived downstream on that route, so the derived c "
        "inherits eps_1 and Eq. eq:tolmapband is admitted. IT IS NOT AN ABSURD "
        "READING -- it is what 0.2.0's phrase THE SLACK IS TRANSPORTED RATHER "
        "THAN LOST invites -- AND IT LOSES TWICE OVER', on step (2) and "
        "independently on step (3). 'NEITHER READING IS UNSOUND: branch "
        "selection and p_mc are unaffected either way, and THE COST OF THE "
        "LOSING READING IS A FALSE STATED ERROR BOUND, NOT A FALSE BOUND ON "
        "lmin.'",
    ),
    (
        "the failure is a refusal",
        "'Bound data failing item (iv) is a failed validation, so `fail_closed` "
        "(Section 2.5) applies at this site: NO ARTIFACT IS EMITTED.' 0.2.0 "
        "omitted this sentence; adding it is the one behavioural statement the "
        "second ruling makes, and it changes nothing for an implementation that "
        "already refused.",
    ),
)

#: WHAT THE SECOND RULING DOES *NOT* CHANGE, frozen because 'no behaviour
#: change' is a claim a verifier checks rather than takes. Section 1.1: "The
#: precedence rule adds no key, removes none, and CHANGES NO EMITTED VALUE ...
#: An implementation of 0.2.0 that refused there is ALREADY CONFORMING."
#: (what, unchanged)
TOLMAP_IV_NO_BEHAVIOUR_CHANGE: tuple[tuple[str, bool], ...] = (
    ("any input key", True),
    ("any output key", True),
    ("any emitted value, including p_mc and every emitted key", True),
    ("any reason string in Section 2.6", True),
    ("any assumption of the ledger", True),
    ("branch selection in Def. def:pmc", True),
    ("Rem. rem:cdirection's stated bounds, which stay in eps_2", True),
)


#: Def. def:tolmap's closing enumeration at 0.3.0. THE SAME THREE KINDS, each
#: with entries the amendment adds: kind (a) gains m*_t > N and m*_t <= m_t;
#: kind (b) gains "the conditional presence of eps_eig and eps_6 at a
#: declaration carrying an exact-window depth (Def. def:pmcex)"; kind (c) gains
#: r_6 against eps_6. AND ONE EXCLUSION IS STATED IN THE SAME PARAGRAPH:
#: "Neither is eps_eig, which is NOT A TEST OF ANY KIND: it is subtracted from
#: beta-hat* in Eq. eq:elldef and changes AN EMITTED VALUE, NOT AN ADMISSION."
TOLMAP_OTHER_VALIDATION_KINDS_0_3_0: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "a comparison of declared data against a declared domain",
        (
            "every parameter domain of Table tab:catalogue except C10's",
            "the detector-layer ranges",
            "m_t > N",
            "m*_t > N",
            "m*_t <= m_t",
            "N >= 0",
            "the tolerance domain itself (Rem. rem:tolerancedomain)",
            "the `tolerance`-field test of Ass. ass:exact",
            "the diagonal non-negativity of Gamma^(t)",
        ),
    ),
    (
        "a combinatorial predicate on the declaration decided by finite inspection",
        (
            "(E2) and (E3) of Def. def:graph",
            "route exclusivity",
            "the port map's disjointness",
            "totality and surjectivity of cg",
            "the single-valued tau of Ass. ass:thresh",
            "the dark-count route exclusivity of Section 2.1",
            "predicate (X) of Def. def:pmc",
            "the conditional presence of eps_eig and eps_6 at a declaration "
            "carrying an exact-window depth (Def. def:pmcex)",
        ),
    ),
    (
        "the residual tests themselves, on COMPUTED quantities",
        (
            "r_3 against eps_3",
            "r_4 against eps_4",
            "r_5 against eps_5",
            "r_6 against eps_6",
            "the residual gap g_{N,m_t} against eps_gap",
        ),
    ),
)

#: WHAT IS NOT A TEST AT ALL, named by the same paragraph so that the
#: enumeration reads as complete. (declared number, why it is not a test)
TOLMAP_NOT_A_TEST_0_3_0: tuple[tuple[str, str], ...] = (
    (
        "eps_eig",
        "'NOT A TEST OF ANY KIND: it is subtracted from beta-hat* in "
        "Eq. eq:elldef and CHANGES AN EMITTED VALUE, NOT AN ADMISSION.' "
        "Def. def:tolmap's preamble adds that it 'decides nothing at all' and "
        "is 'the one declared number this contract spends on a HYPOTHESIS "
        "(Assumption ass:eig) rather than on a TEST'; Section 2.5's "
        "tolerance-assignment bullet says it 'appears in NO ITEM of Definition "
        "def:tolmap'.",
    ),
    (
        "eps_6",
        "it BOUNDS THE RESIDUAL r_6 and 'decides no exact condition' "
        "(Def. def:tolmap's preamble), so it is kind (c) -- a threshold "
        "decision on a COMPUTED quantity -- and not one of the five items.",
    ),
)

#: The string a run-B test file names when it has moved to THIS amendment.
AMENDMENT_SPEC_VERSION_MARKER_0_3_0: str = MATHEMATICAL_SPEC_VERSION_0_3_0


# ---------------------------------------------------------------------------
#  Oracle entries for the 0.3.0 amendment
# ---------------------------------------------------------------------------

O_RP_EXACT_BLOCK = RPOracleEntry(
    oracle_id="O-RP-EXACT-BLOCK",
    claims=("RC8",),
    kind="toy-instance",
    subject=(
        "The exact block quantity beta*(n) = lmin(blk M^{(=n)}_mc) of "
        "Definition def:exactbnd, computed by hand from the constructed "
        "receiver at three values of p_Z and two photon numbers; the two "
        "halves of Lemma lem:exactbasic and the hypothesis each needs; and "
        "Remark rem:exactpositivity's counterexample, where beta* = -3."
    ),
    derivation="""\
Definition def:exactbnd (Eq. eq:exactbnd), Lemma lem:exactbasic
(Eq. eq:exactbasic, Eq. eq:mcpos, Eq. eq:mcupper), Remark rem:exactpositivity,
Example ex:bb84exact (Eq. eq:bb84exactblock, Eq. eq:bb84exactvec,
Eq. eq:bb84exact2, Eq. eq:bb84exactvalue), Remark rem:exactscope.

WHAT beta* IS, AND WHAT IT IS NOT. It is the exact minimum eigenvalue of the
n-photon block of the multiclick element, "a Hermitian matrix of dimension
binom(D + n - 1, n), where D is the dimension of the space B acts on:
D = |Inp_C| at every declared setting". Definition def:exactbnd is emphatic that
NO NEW OBJECT IS INTRODUCED: each Fock(.)^{(n)} is the construction
Eq. eq:blockMS already uses for the blocks the artifact emits at n <= N, in the
occupation basis and order Definition def:fock and Section 2.5 fix, EVALUATED AT
AN INDEX ABOVE THE CUTOFF INSTEAD OF BELOW IT.

EVERY SPECTRUM WAS COMPUTED FROM THE OPERATOR, NOT FROM A CLOSED FORM. At n = 2
the block reduces, by Eq. eq:bb84exactvec, to a multiple of the identity plus
two rank-one projectors on orthogonal vectors, giving
{1 - p_X^2, 1 - p_Z^2, 1 - p_Z^2 - p_X^2}; the closed form
beta*(2) = 1 - p_Z^2 - p_X^2 of Eq. eq:bb84exactvalue then CHECKS the
computation at each of p_Z = 1/2, 7/10 and 1/4. At n = 3 -- an index the
contract does not work out -- the 4 x 4 matrix in the occupation basis
{|3_H>, |2_H 1_V>, |1_H 2_V>, |3_V>} decouples into two 2 x 2 blocks, each with
mean 7/8, half-difference 1/32 and off-diagonal sqrt3/32, so the spectrum is
{13/16, 13/16, 15/16, 15/16} and the sqrt3 CANCELS EXACTLY. The trace check
2(13/16) + 2(15/16) = 7/2 against tr M = 4 - 1/4 - 1/4 = 7/2 agrees.

WHY n = 3 IS FROZEN AT p_Z = 1/2 AND NOWHERE ELSE. The same computation at
p_Z = 7/10 gives 163/200 - sqrt(436468)/4000 with 436468 = 4 x 19 x 5743, which
is irrational and NOT in the ring Q[sqrt2] + i Q[sqrt2] this file works in. The
limit is recorded rather than worked around: an approximate value would be a
float, and this registry carries none.

THE TWO HALVES OF LEMMA lem:exactbasic, WHICH IS ROUND-11 FINDING F-11-01'S
SUBSTANCE. beta(n) <= beta*(n) <= 1 follows from Theorem thm:multiclick-bound's
hypotheses ALONE -- the lower half is Eq. eq:mcbound, the upper half is the
operator form Eq. eq:mcupper of that theorem's own beta <= 1 argument. But
beta*(n) >= 0 needs the ADDED hypothesis Eq. eq:mcpos, and
EB-POSITIVITY-COUNTEREXAMPLE-N1 and -N2 are the instance that shows so:
K = 4, gamma = beta_k = 1, B = id, B_k = 0 satisfy every hypothesis of
Theorem thm:multiclick-bound and give M_mc = -3 id on every block n >= 1, so
beta* = -3 < 0 while beta*(n) <= 1 still holds. Theorem thm:multiclick-bound is
untouched there: the same data give c = 0 and d_k = 1, hence beta(n) = -3 too,
and Eq. eq:mcbound holds WITH EQUALITY.

WHERE THE EXACT WINDOW BUYS NOTHING, AND WHY THAT IS NOT AN EDGE CASE. At
I-BS and at both settings of I-PROBE the channel space is ONE DIMENSIONAL, so
every block is a scalar, beta*(n) = beta(n) at every index, and the gap is
exactly 0. That is a property of |Inp_C| = 1 and not of those particular
devices, and it is why the amendment's improvement is exercised at I-BB84,
where |Inp_C| = 2.
""",
    hypotheses=(
        "Eq. eq:bbkhyp and Eq. eq:prefactorform at every case (the hypotheses "
        "of Thm. thm:multiclick-bound)",
        "Eq. eq:mcpos at every case EXCEPT the two counterexample rows, where "
        "it fails and beta* < 0",
    ),
)

O_RP_EXACT_WINDOW = RPOracleEntry(
    oracle_id="O-RP-EXACT-WINDOW",
    claims=("RC8",),
    kind="analytic-limit",
    subject=(
        "Lemma lem:exactwindow's composite Eq. eq:exactcomposite on admissible "
        "reals, including the P = 0 branch that is the one use of Eq. eq:mcpos; "
        "the emitted Eq. eq:pmcex at thirteen declarations, on both branches, "
        "with the empty middle minimum and the outer maximum both exercised; "
        "Proposition prop:exactnoworse case by case; the settings mixed in one "
        "declaration; and the OPT-IN invariant that leaves every 0.1.3 "
        "bound-data case standing."
    ),
    derivation="""\
Lemma lem:exactwindow (Eq. eq:ellhyp, Eq. eq:tailadm, Eq. eq:exactcomposite,
Eq. eq:exactstatement and its three admissible choices), Remark rem:exactscope,
Definition def:pmcex (Eq. eq:elldef, Eq. eq:pmcex), Proposition
prop:exactnoworse, Remark rem:noworsefl, Theorem thm:emitted-bound, Example
ex:bb84exact (Eq. eq:bb84exactemit), Definition def:pmc's closing paragraph.

THE LEMMA IS STATED ON ARBITRARY REALS, so EXACT_COMPOSITE_CASES is
lemma-level: six evaluations of P = max{0, min{min ell, tau}} that separate the
window from the remainder (EW-TAU-BINDS against EW-ELL-BINDS), exercise the
minimum over a window of three indices whose smallest value is in the MIDDLE
(EW-MULTI-INDEX -- beta* is not monotone in general), attain the upper limit
P = 1, and hit the P = 0 branch twice: once from a negative window value and
once from the FIRST disjunct of Eq. eq:tailadm, tau <= 0, which is admissible
with no hypothesis whatever. That branch is the ONE step of the proof that uses
Eq. eq:mcpos, as Remark rem:exactscope records.

THE EMITTED VALUES. Thirteen declarations of five receivers. On BRANCH 1
(predicate (X)) the remainder is beta(m* + 1), admissible by part (ii) because
(X) makes Eq. eq:collapsehyp hold; on BRANCH 2 the branch keeps its own analytic
middle window and tail, admissible by part (i) with no hypothesis, which is why
m*_t <= m_t is required there. Both binding patterns occur: the exact window
binds at EX-BB84-N1-M2-EIG-ZERO (0 -> 1/2) and the ANALYTIC REMAINDER binds at
EX-BB84-N2-M3-EIG-ZERO (1/2 -> 3/4) and at EX-BB84-PZ7-N1-M2-EIG-ZERO
(0 -> 13/50). An implementation that dropped the remainder would emit 13/16 at
the second of those, and nothing in this contract bounds
lmin(blk M^{(=n)}_mc) below 13/16 for n >= 4.

THE DECLARED SLACK IS SUBTRACTED, NEVER USED AS A THRESHOLD, AND IT IS NOT A
UNIFORM TAX. At EX-BB84-N1-M2-EIG-1E3 it costs exactly 1/1000 because the exact
window binds; at EX-BB84-N2-M3-EIG-1E3 it costs nothing because the remainder
binds; at EX-BS-N1-M2-EIG-1E3 it costs nothing because Eq. eq:elldef's analytic
floor wins. Eq. eq:bb84exactemit's whole family, p_mc = max{0, 1/2 - eps_eig}
with the split at eps_eig = 1/2, is frozen at four points of the declared
domain [0, 1) including the split itself and a value above it.

TWO CONVENTIONS AN IMPLEMENTATION COULD GUESS WRONG, AND BOTH ARE FIXED. The
middle minimum of branch 2 runs "over THE EMPTY INDEX SET -- and so equal to
+infinity and INACTIVE -- when m*_t = m_t", not zero
(EX-PROBE-ON-N1-M3-MSTAR3-EMPTY-MIDDLE); and branch 2 keeps its tail even where
an exact window is declared, so a negative T_{m_t} still drives the emitted
value to zero (EX-PROBE-ON-N1-M2-MSTAR2-ZERO).

PROPOSITION prop:exactnoworse HOLDS AT ALL THIRTEEN, seven strictly and six with
equality, and NO_WORSE_UNDER_EVALUATION records the one step of its proof that
does not survive an evaluation term for term -- branch 1's
beta(m*_t + 1) >= beta(N + 1), a statement about EXACT values -- so `never
worse` is a statement about the mathematics and NOT a runtime invariant.

THE OPT-IN INVARIANT IS WHY NOTHING EARLIER IS SUPERSEDED. Every one of the
fourteen frozen bound-data cases declares no depth, so Definition def:pmc
"stands expression for expression, no block above the cutoff is formed, and the
emitted value is the one 0.2.0 emits". The four the amendment would change if a
depth were declared are named with their 0.3.0 counterparts, and THE TWO SETS
COEXIST: they are different declarations of the same device.
""",
    hypotheses=(
        "Eq. eq:ellhyp at every window value: the analytic entry by "
        "Lem. lem:exactbasic and the computed entry by Ass. ass:eig",
        "Eq. eq:tailadm at every remainder: part (i) with no hypothesis on "
        "branch 2, part (ii) under Eq. eq:collapsehyp on branch 1",
        "Eq. eq:mcpos, discharged by Thm. thm:emitted-bound at every receiver here "
        "and used at exactly one step",
    ),
)

O_RP_RES6 = RPOracleEntry(
    oracle_id="O-RP-RES6",
    claims=("RC9",),
    kind="fail-closed",
    subject=(
        "The sixth residual r_6 of Eq. eq:res6: its exact value 0, its "
        "request-dependent presence rule, its refusals over indices and over "
        "settings, the undershoot it admits inside the declared tolerance, and "
        "-- frozen as a PASS -- the one direction it is blind to, together "
        "with the over-large lower bound a violated Assumption ass:eig then "
        "emits."
    ),
    derivation="""\
Definition def:residuals (Eq. eq:res6 and the paragraph "r_6 is
request-dependent, not route-dependent"), Remark rem:exacteig, Assumption
ass:eig (Eq. eq:eigassumption), Theorem thm:exact-and-evaluated (ii) and (v), Section 2.6 row 8,
Section 1.3's escalation bullet.

WHAT r_6 IS. The window consistency defect
max over t and over N < n <= m*_t of (beta^(t)(n) - beta-hat*^(t)(n))_+, whose
EXACT value is 0 because beta(n) <= beta*(n) is a theorem
(Lemma lem:exactbasic). It is a residual in exactly the sense of the other five:
what is emitted is its floating-point evaluation, and a value above eps_6
REFUSES with a verbatim reason. The direction is refuse-only -- "it refuses, IT
REPAIRS NOTHING".

ITS PRESENCE RULE IS A SECOND AXIS, NOT THE FIRST ONE AGAIN. r_1 and r_3 are
ROUTE-dependent and absent on route (i); r_6 is REQUEST-dependent and exists on
all three routes but only at the settings carrying a depth, over exactly the
indices that depth names. Where no depth is declared its key is ABSENT -- absent,
not zero -- and eps_6 is then not declared either, which is where eps_6 differs
from eps_1 and eps_3, "which are declared on every route and merely unused on
one". RESIDUAL_SCOPING_0_3_0 sets the six side by side.

THE REFUSALS COVER BOTH QUANTIFIERS. R6-FAIL-UNDERSHOOT is a gross defect at a
single index; R6-FAIL-AT-THE-SECOND-INDEX has an exact first index and a wrong
second, so an implementation that short-circuited on the first would admit it;
R6-FAIL-ACROSS-SETTINGS has a clean setting and a defective one, so a
per-setting report would hide it. And R6-PASS-UNDERSHOOT-WITHIN-TOLERANCE is the
pair of the first: the same direction, one side of eps_6 each, which is what
makes r_6 a residual rather than an exact-zero assertion.

THE BLIND DIRECTION, FROZEN AS A PASS BECAUSE THAT IS WHAT IT IS.
R6-PASS-OVERSHOOT-BLIND has beta-hat*(2) = 3/4 against an exact 1/2 -- an
overshoot 250 times the declared eps_eig, so Eq. eq:eigassumption is VIOLATED --
and the defect Eq. eq:res6 computes is (1/2 - 3/4)_+ = 0. Remark rem:exacteig
says so in terms: r_6 "does NOT verify Assumption ass:eig: r_6 fires when
beta-hat* lands too LOW, and Assumption ass:eig constrains it from landing too
HIGH ... NO TEST IN THIS CONTRACT BOUNDS THE UNSAFE DIRECTION".

WHAT THE ADMITTED REQUEST EMITS IS FROZEN AS A_EIG_WITNESS, and it is the
concrete instance of Assumption ass:eig's "If violated" column: the emitted
p_mc is 749/1000 where the true uniform bound is 1/2, an excess of 249/1000 in
the unsafe direction, reaching a key length through Definition def:slot. And
ARCHITECTURE_SPEC.md Section 7.3 does NOT catch it, because 749/1000 lies in
[0, 1] -- exactly the asymmetry Remark rem:exacteig makes exact: an overshoot
large enough to push p_mc above 1 would be caught, "but an overshoot of the size
eps_eig exists to bound sits far below that threshold, AND IS CAUGHT BY
NOTHING". That sentence is why Section 1.3 fires the
numerical-lower-bound-certificate trigger from 0.3.0.
""",
    hypotheses=(
        "Lem. lem:exactbasic, which is what makes the exact value of r_6 zero",
        "Ass. ass:eig at every row EXCEPT R6-PASS-OVERSHOOT-BLIND, where it is "
        "deliberately violated and the case is the witness of that violation",
    ),
)

O_RP_EXACT_WINDOW_VALIDATION = RPOracleEntry(
    oracle_id="O-RP-EXACT-WINDOW-VALIDATION",
    claims=("RC8", "RC9"),
    kind="fail-closed",
    subject=(
        "The exact window's input validation: the two depth constraints and "
        "the conditional requirement on eps_eig and eps_6, with the three "
        "verbatim reason strings Section 2.6 adds, the admits at both "
        "boundaries, and the opt-out admitted with neither conditional "
        "tolerance declared."
    ),
    derivation="""\
Section 2.1 `exact_window` and `numerical_tolerances`, Definition def:pmcex's
Refusals paragraph, Section 2.6 rows 6 to 8, Definition def:tolmap's closing
enumeration, Section 2.5 `fail_closed`.

FOUR VALIDATIONS, AND NOT ONE OF THEM CONSUMES A TOLERANCE. Definition
def:tolmap's closing enumeration classifies every one: m*_t > N and
m*_t <= m_t are kind (a), "a comparison of declared data against a declared
domain", and the conditional presence of eps_eig and eps_6 is kind (b), "a
combinatorial predicate on the declaration decided by finite inspection". So the
amendment adds four checks and NO NEW THRESHOLD, which is what makes the
completeness claim of that definition still true at 0.3.0 -- "every exact
condition this contract decides under a threshold is one of the five items".

THE FIRST CONSTRAINT IS STRICT AND THE STRICTNESS IS USED. m*_t > N: at
m*_t = N the exact window N < n <= m*_t is EMPTY, and Lemma lem:exactwindow's
proof of P <= 1 reads "the window being NON-EMPTY BECAUSE m* > N". Both
XW-REFUSE-DEPTH-AT-THE-CUTOFF and XW-REFUSE-DEPTH-BELOW-THE-CUTOFF are refused
under it, and XW-ADMIT-MINIMAL-DEPTH sits on its admissible side at
m* = N + 1 -- which Example ex:bb84exact declares and which is NOT a default:
"the depth is the caller's and this contract states no default for it".

THE SECOND CONSTRAINT APPLIES ONLY WHERE PREDICATE (X) FAILS, and the reason is
structural rather than defensive: branch 2 "keeps its own analytic window and
tail above the exact one -- WHICH IS WHY m*_t <= m_t IS REQUIRED THERE, so that
the two windows compose into the single window N < n <= m_t that Lemma
lem:exactwindow is applied to". At a setting where (X) holds no tail_window is
required at all, so nothing bounds the depth from above and
XW-ADMIT-DEEP-DEPTH-WHERE-X-HOLDS is admitted at m* = 5 with N = 1.

THE CONDITIONAL TOLERANCES ARE REFUSED WHEN MISSING AND ARE NOT AN ERROR WHEN
ABSENT. One verbatim string covers both omissions, Section 2.6's condition
column reading "eps_eig OR eps_6 is not", so an implementation must not invent a
second. And XW-ADMIT-NO-DEPTH-NO-CONDITIONAL-TOLERANCES is every 0.2.0
declaration: neither is required, neither is an error, and that is what makes
the amendment a strict extension rather than a widened obligation.

WHY A MISSING eps_eig IS NOT DEFAULTED TO ZERO. Zero is inside the declared
domain and is admissible, but declaring it is declaring that the eigenvalue
routine never overshoots at all -- the item the G3 packet put to the signer --
so supplying it silently would make that assertion on the caller's behalf. The
contract's own word is "refused rather than defaulted, EXACTLY AS A MISSING m_t
IS".
""",
    hypotheses=(),
)

O_RP_TOLMAP_IV = RPOracleEntry(
    oracle_id="O-RP-TOLMAP-IV",
    claims=("RC9",),
    kind="fail-closed",
    subject=(
        "Definition def:tolmap (iv) decides the admissibility of c ALONE, on "
        "every input route: the band Eq. eq:tolmapband bracketed on both "
        "sides, its half-open right endpoint, its emptiness at eps_1 = eps_2, "
        "the four derivation steps, the quantitative cost of the losing "
        "reading, and the refusal the contract deliberately leaves unspelled."
    ),
    derivation="""\
Definition def:tolmap (iv) and (v), Eq. eq:tolmapband, Remark rem:cdirection,
Remark rem:tolerancedomain, Theorem thm:exact-and-evaluated (ii), Theorem thm:port-grams (i), Lemma
lem:schurmono, Section 2.5's tolerance-assignment bullet, Section 1.1 (f).

THE QUESTION 0.2.0 LEFT OPEN, AND IT IS REACHABLE. Item (v) admits a route-(ii)
Gamma at eps_1 while item (iv) decides the derived c at eps_2, so at the
ordinary declaration eps_1 > eps_2 the band c in [-eps_1, -eps_2) is admitted by
one and refused by the other. THE MAIN FIXTURE CANNOT EXHIBIT IT: at
eps_1 = eps_2 = 1/1000 the interval is EMPTY, which is item (v)'s own closing
observation and is frozen as TOLMAP_IV_BAND_EMPTY_AT_EQUAL_EPS. So these cases
carry their own fixture, eps_1 = 1/100 and eps_2 = 1/1000.

ITEM (iv) WINS, AND THE BAND IS REFUSED. Five cases bracket it: two inside
(the interior and the CLOSED left endpoint), one at the OPEN right endpoint
where item (iv) admits with equality and the band therefore excludes it, one
below the band where both readings refuse, and the lossless c = 0 that both
admit. The band is exactly the set the two readings disagree about, and cases
outside it on either side are not evidence about the ruling.

THE DERIVATION IS FOUR STEPS AND THE SECOND IS THE LOAD-BEARING ONE. In exact
arithmetic item (v)'s condition implies item (iv)'s, so item (iv) is redundant
-- exactly. "BUT ITEM (v) NEVER ESTABLISHES ITS EXACT CONDITION. It admits under
a widened test on a COMPUTED number, and Theorem thm:exact-and-evaluated (ii) bounds the
distance from that number to the exact one BY NOTHING AT ALL." Reading item (v)
as admitting anything under item (iv) is "reading an exact implication as a
bound on an evaluation, WHICH IS THE ONE SUBSTITUTION Theorem thm:exact-and-evaluated (ii)
EXISTS TO FORBID". The same step is why item (iv) is not a formality on
route (i): "redundancy of the EXACT condition is not admission of the COMPUTED
one".

STEP (3) IS QUANTITATIVE AND IS FROZEN AS NUMBERS. Remark rem:cdirection bounds
the even-n overshoot by (K-1) eps_2^2, and that bound is stated in eps_2
BECAUSE item (iv) is what bounds |c|. At K = 4 and eps_2 = 1/1000 the stated
bound is 3/1000000; under the losing reading |c| could reach eps_1 = 1/100 and
the true bound would be 3/10000, larger by (eps_1/eps_2)^2 = 10000. And at the
admitted band value c = -1/200 the ACTUAL even-n = 2 overshoot is 3/40000, which
exceeds the stated bound BY A FACTOR OF 25. A stated error term of this contract
would then be false on values this contract admits, "in the direction where the
evaluated beta(n) EXCEEDS the exact one, WHICH IS THE DIRECTION THAT REACHES A
KEY LENGTH".

WHAT THE RULING DOES NOT CHANGE, and it is most of the interface: no key, no
emitted value, no reason string, no assumption, and no branch selection. "An
implementation of 0.2.0 that refused the band is ALREADY CONFORMING." What IS
new is that item (iv) states its failure to be a refusal under `fail_closed` --
which 0.2.0 omitted -- and that this refusal carries NO tabulated reason string,
deliberately: the contract says the spelling is the implementer's and "this
amendment deliberately adds none". So REF-TOLMAP-IV-C-REFUSED-NO-SPELLING freezes
the verdict, the threshold and the fail-closed consequence, and freezes no key.
""",
    hypotheses=(
        "Thm. thm:exact-and-evaluated (ii), which is what makes step (2) work: no bound "
        "whatever between a computed quantity and the exact one",
    ),
)


# ---------------------------------------------------------------------------
#  What the 0.3.0 amendment supersedes in the earlier freezes
# ---------------------------------------------------------------------------
#
#  EXPLICIT, AND IN THIS FILE. Every earlier frozen object whose SHAPE or
#  EXPECTED VALUE the amendment invalidates, or whose framing it makes stale, is
#  listed below with the contract site and its replacement. NOTHING IS DELETED
#  AND NOTHING IS SILENTLY EDITED.
#
#  EVERY MARK IS ON A WHOLE MODULE-LEVEL OBJECT AND NOT ON A ROW, and that is
#  deliberate rather than incidental: marking a row would mean setting its
#  `superseded_by` field, which would EDIT a value an earlier pass froze. The
#  0.2.0 pass could mark rows because it was the first to write those fields;
#  this pass may not, so it marks the tables that carry them. THE PRACTICAL
#  CONSEQUENCE IS THAT NO ROW OF RESIDUAL_CASES, REFUSAL_CASES, DARK_CASES,
#  BOUND_DATA_CASES OR RP_ORACLES CHANGES BY SO MUCH AS A BYTE.
#
#  THE LIST IS SHORT, AND THE REASON IS THE AMENDMENT'S OWN OPT-IN RULE. What
#  0.3.0 changes for a declaration that requests nothing new is NOTHING, so the
#  only objects invalidated are the ones that ENUMERATE the interface -- key
#  tuples, the reason vocabulary, the tolerance tuple, the ledger, the presence
#  rules -- and not one frozen NUMBER. In particular NOT ONE p_mc, window
#  minimum, tail, residual gap or beta value is superseded.


@dataclass(frozen=True)
class Supersession0_3_0:
    """One earlier frozen object the 0.3.0 amendment marks."""

    #: The module-level name. Equal to `table`: this pass marks whole objects.
    name: str
    table: str
    kind: str
    superseded_by: str
    #: The element of contract.tex 0.3.0 that invalidates or restates it.
    contract_site: str
    reason: str
    #: The 0.3.0 names that replace it.
    replacement: tuple[str, ...]


SUPERSEDED_BY_0_3_0: tuple[Supersession0_3_0, ...] = (
    Supersession0_3_0(
        name="INPUT_KEYS",
        table="INPUT_KEYS",
        kind="superseded",
        superseded_by="0.3.0",
        contract_site="Section 2.1 `exact_window`; Section 1.1, Interface deltas",
        reason=(
            "THE INPUT SURFACE GAINS A KEY. 0.3.0 adds `exact_window`, the "
            "declared depth {m*_t}, optional per setting, in its own tabular "
            "between `tail_window` and `numerical_tolerances`, so the input "
            "names are FIFTEEN where this tuple has fourteen. Section 1.1's "
            "delta paragraph: 'Added: the declared depth {m*_t} "
            "(exact_window), optional per setting ... REMOVED: NOTHING.' The "
            "fourteen names in this tuple are all still input keys and all "
            "still mean what they meant; what is invalidated is the tuple AS "
            "AN ENUMERATION OF THE INPUT SURFACE."
        ),
        replacement=("INPUT_KEYS_0_3_0",),
    ),
    Supersession0_3_0(
        name="TOLERANCE_FIXTURE_0_2_0",
        table="TOLERANCE_FIXTURE_0_2_0",
        kind="superseded",
        superseded_by="0.3.0",
        contract_site=(
            "Section 2.1 `numerical_tolerances`; Def. def:pmcex; "
            "Rem. rem:tolerancedomain"
        ),
        reason=(
            "THE DECLARED TUPLE GAINS TWO MEMBERS AND A REQUIREMENT RULE. "
            "0.3.0 adds eps_6 and eps_eig, so the tuple is "
            "{eps_1, ..., eps_6}, eps_gap, eps_eig -- ARITY EIGHT where this "
            "fixture has six -- and it introduces a distinction the six-member "
            "fixture cannot express: SIX are required on every declaration and "
            "TWO are required EXACTLY where an exact_window depth is declared, "
            "refused when missing there, and neither required nor an error "
            "otherwise. Every value in this fixture is still a legal "
            "declaration of the six it names; what is invalidated is the "
            "fixture AS THE DECLARED TUPLE."
        ),
        replacement=(
            "TOLERANCE_FIXTURE_0_3_0",
            "TOLERANCES_ALWAYS_REQUIRED_0_3_0",
            "TOLERANCES_CONDITIONALLY_REQUIRED_0_3_0",
        ),
    ),
    Supersession0_3_0(
        name="REFUSAL_REASONS_VERBATIM_0_2_0",
        table="REFUSAL_REASONS_VERBATIM_0_2_0",
        kind="superseded",
        superseded_by="0.3.0",
        contract_site="Section 2.6, rows 6 to 8; Def. def:pmcex; Def. def:residuals",
        reason=(
            "IT IS THE STATEMENT 'Section 2.6 SPELLS FIVE REFUSAL REASONS', "
            "which was true of 0.2.0 and is FALSE of 0.3.0: the table has "
            "EIGHT rows, the three added being "
            "`exact_window_declared_without_required_tolerance`, "
            "`exact_window_depth_outside_declared_range` and "
            "`window_eigenvalue_consistency_residual_above_tolerance`. The "
            "five strings in this tuple are unchanged character for character "
            "and still refuse under the same conditions; what is invalidated "
            "is the tuple AS THE REFUSAL VOCABULARY."
        ),
        replacement=(
            "REFUSAL_REASONS_VERBATIM_0_3_0",
            "REFUSAL_REASONS_ADDED_AT_0_3_0",
        ),
    ),
    Supersession0_3_0(
        name="REASON_VOCABULARY_0_2_0",
        table="REASON_VOCABULARY_0_2_0",
        kind="superseded",
        superseded_by="0.3.0",
        contract_site="Section 2.6; Thm. thm:exact-and-evaluated (iii)",
        reason=(
            "THE SAME INVALIDATION ONE LEVEL UP: this tuple is the five "
            "refusals plus the tier fallback, SIX strings, and 0.3.0 spells "
            "NINE. The fallback string `receiver_grams_not_enclosed` is "
            "BYTE-IDENTICAL across all three versions and is still the only "
            "spelled string that is NOT a refusal, so what is invalidated is "
            "the vocabulary's EXTENT and not any member of it. An "
            "implementation checking that an emitted reason lies in this tuple "
            "would reject three strings the contract now spells."
        ),
        replacement=("REASON_VOCABULARY_0_3_0",),
    ),
    Supersession0_3_0(
        name="REASON_EMITS_ARTIFACT",
        table="REASON_EMITS_ARTIFACT",
        kind="superseded",
        superseded_by="0.3.0",
        contract_site="Section 2.6; Section 2.5 `fail_closed`",
        reason=(
            "IT IS DERIVED FROM REASON_VOCABULARY_0_2_0 AND INHERITS ITS "
            "EXTENT: six rows where 0.3.0 has nine. The RULE it encodes is "
            "unchanged and is the one thing worth carrying forward -- a "
            "refusal emits NO artifact ('a refusal with a machine-readable "
            "reason and NO artifact'), the tier fallback emits one at the "
            "lower tier -- and the three new strings are all refusals, so all "
            "three carry False. The mark is on the table's completeness, not "
            "on its rule."
        ),
        replacement=("REASON_EMITS_ARTIFACT_0_3_0",),
    ),
    Supersession0_3_0(
        name="MATHEMATICAL_SPEC_VERSION_0_2_0",
        table="MATHEMATICAL_SPEC_VERSION_0_2_0",
        kind="superseded",
        superseded_by="0.3.0",
        contract_site=(
            "Section 2.5, last bullet; Section 2.2 `mathematical_spec_version`; "
            "STATUS.yaml gates.g3, signed_version 0.3.0"
        ),
        reason=(
            "THE ARTIFACT BINDS THE ACCEPTED CONTRACT VERSION, AND THE "
            "ACCEPTED VERSION IS NOW 0.3.0. Section 2.2 requires "
            "`receiver-povm@<contract_version>` OF THE ACCEPTED CONTRACT and "
            "adds that 'an artifact may not claim a draft version'; STATUS.yaml "
            "records contract_version 0.3.0, state accepted, and a G3 signed "
            "at signed_version 0.3.0. The 0.2.0 string "
            "remains correct about the version it names and is superseded as "
            "the string an artifact binds. See CONTRACT_VERSION_RESIDUE_0_3_0 "
            "for the `-draft` residue in contract.tex's own macro, which this "
            "freeze reports and does not follow."
        ),
        replacement=("MATHEMATICAL_SPEC_VERSION_0_3_0",),
    ),
    Supersession0_3_0(
        name="AMENDMENT_SPEC_VERSION_MARKER",
        table="AMENDMENT_SPEC_VERSION_MARKER",
        kind="superseded",
        superseded_by="0.3.0",
        contract_site="Section 2.5, last bullet; STATUS.yaml gates.g3",
        reason=(
            "IT IS THE HAND-OFF MARKER, and it names 0.2.0. Its job is to say "
            "which string a run-B test file prints once it HAS MOVED to the "
            "amendment under discussion, and for this band that string is "
            "`receiver-povm@0.3.0`. The 0.2.0 marker keeps its meaning for the "
            "0.2.0 hand-off, whose invariant still holds and is still "
            "asserted; it is superseded as THE marker of the current band. A "
            "single marker cannot serve two amendments, which is exactly why "
            "the 0.2.0 pass gave it a name of its own rather than a literal."
        ),
        replacement=("AMENDMENT_SPEC_VERSION_MARKER_0_3_0",),
    ),
    Supersession0_3_0(
        name="ASSUMPTION_ROWS",
        table="ASSUMPTION_ROWS",
        kind="incomplete",
        superseded_by="0.3.0",
        contract_site="Ass. ass:eig; Section 5 preamble and ledger table",
        reason=(
            "THE LEDGER GAINS A THIRTEENTH ROW AND EVERY ONE OF THE TWELVE "
            "HERE IS UNCHANGED. A-EIG, machine key "
            "`exact_window_eigenvalue_slack`, Supports 'RC9 (v), and the "
            "exact-window branch of RC8', NEVER VERIFIED, invoked only where a "
            "caller declares a depth. No id, no machine key and no Supports "
            "cell of the twelve moves -- 'no assumption is removed' -- so the "
            "mark is INCOMPLETE and not SUPERSEDED: an implementation that "
            "emitted these twelve would emit twelve true rows and omit a "
            "thirteenth the contract requires."
        ),
        replacement=("ASSUMPTION_ROWS_0_3_0", "NEVER_VERIFIED_0_3_0"),
    ),
    Supersession0_3_0(
        name="RESIDUAL_ROUTE_PRESENCE",
        table="RESIDUAL_ROUTE_PRESENCE",
        kind="incomplete",
        superseded_by="0.3.0",
        contract_site=(
            "Def. def:residuals, the paragraph 'r_6 is request-dependent, not "
            "route-dependent'; Section 2.2 `validation_results`"
        ),
        reason=(
            "THE PRESENCE RULE GAINS A SECOND AXIS, AND THE FIRST ONE IS "
            "UNCHANGED. This table says which of r_1 to r_5 exist on which "
            "ROUTE, and every row of it is still true. What it cannot express "
            "is r_6, which 'exists on ALL THREE ROUTES but ONLY AT THE "
            "SETTINGS WHOSE DECLARATION CARRIES AN EXACT-WINDOW DEPTH' -- a "
            "REQUEST-dependent rule, not a route-dependent one. The contract "
            "names the difference itself: eps_1 and eps_3 'are declared on "
            "every route and merely unused on one', where eps_6 'is then not "
            "declared either'."
        ),
        replacement=("RESIDUAL6_REQUEST_PRESENCE", "RESIDUAL_SCOPING_0_3_0"),
    ),
    Supersession0_3_0(
        name="REFUSALS_NAMED_WITHOUT_A_SPELLING",
        table="REFUSALS_NAMED_WITHOUT_A_SPELLING",
        kind="incomplete",
        superseded_by="0.3.0",
        contract_site=(
            "Def. def:tolmap (iv), 'The failure is a refusal'; Section 1.1 (f)"
        ),
        reason=(
            "A SEVENTH UNSPELLED SITE, AND IT IS NOT IN Section 2.6's "
            "PREAMBLE. The six rows here are that preamble's enumeration, "
            "verbatim and in its order, and all six stand. What is missing is "
            "Def. def:tolmap (iv)'s own refusal, which 0.3.0 states for the "
            "first time -- 'Bound data failing item (iv) is a failed "
            "validation, so `fail_closed` applies at this site: NO ARTIFACT IS "
            "EMITTED' -- and for which the amendment DELIBERATELY ADDS NO "
            "STRING, the spelling being the implementer's. An implementation "
            "reading this table as the complete list of unspelled refusals "
            "would miss a refusal the contract requires."
        ),
        replacement=("REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0",),
    ),
    Supersession0_3_0(
        name="TOLMAP_ITEMS",
        table="TOLMAP_ITEMS",
        kind="incomplete",
        superseded_by="0.3.0",
        contract_site=(
            "Def. def:tolmap (iv) and (v); Eq. eq:tolmapband; Section 1.1 (f)"
        ),
        reason=(
            "THE FIVE ITEMS ARE STILL FIVE AND ITEM (iv) NOW CARRIES A "
            "DERIVATION. Every row here is still a true summary of the item it "
            "names, including (iv)'s 'bound-data admissibility 0 <= c ... "
            "widened to c >= -eps_2, with the computed c entering Eq. eq:beta "
            "UNCLAMPED'. What it does not carry is the 0.3.0 ruling: that item "
            "(iv) decides that admission ALONE on every input route, that item "
            "(v) transports NO admission, that the band Eq. eq:tolmapband is "
            "therefore REFUSED, and that item (iv)'s failure is a refusal "
            "under `fail_closed`. INCOMPLETE, not superseded: nothing here is "
            "false, and an implementation could pass on this table and still "
            "admit the band."
        ),
        replacement=(
            "TOLMAP_IV_DERIVATION",
            "TOLMAP_IV_PRECEDENCE_CASES",
            "TOLMAP_IV_BAND_COST",
            "TOLMAP_IV_NO_BEHAVIOUR_CHANGE",
        ),
    ),
    Supersession0_3_0(
        name="TOLMAP_OTHER_VALIDATION_KINDS",
        table="TOLMAP_OTHER_VALIDATION_KINDS",
        kind="incomplete",
        superseded_by="0.3.0",
        contract_site="Def. def:tolmap, closing enumeration",
        reason=(
            "THE THREE KINDS ARE STILL THREE AND EACH GAINS ENTRIES. Kind (a) "
            "gains m*_t > N and m*_t <= m_t; kind (b) gains 'the conditional "
            "presence of eps_eig and eps_6 at a declaration carrying an "
            "exact-window depth'; kind (c) gains r_6 against eps_6. And the "
            "same paragraph adds an EXCLUSION this table has no row for: "
            "'Neither is eps_eig, which is NOT A TEST OF ANY KIND: it is "
            "subtracted from beta-hat* in Eq. eq:elldef and changes an emitted "
            "value, NOT AN ADMISSION.' The completeness claim of "
            "Def. def:tolmap is what this table exists to make checkable, so "
            "an incomplete copy of it defeats its purpose."
        ),
        replacement=(
            "TOLMAP_OTHER_VALIDATION_KINDS_0_3_0",
            "TOLMAP_NOT_A_TEST_0_3_0",
        ),
    ),
    Supersession0_3_0(
        name="TOLERANCE_DOMAIN",
        table="TOLERANCE_DOMAIN",
        kind="reframed",
        superseded_by="0.3.0",
        contract_site="Rem. rem:tolerancedomain",
        reason=(
            "THE INTERVAL IS RIGHT AND ITS FRAMING NAMES THE WRONG NUMBER OF "
            "TOLERANCES. The value stands exactly: [0, 1), closed at 0 and "
            "open at 1, for every declared tolerance at 0.3.0 as at 0.2.0, and "
            "TOLERANCE_DOMAIN_CLOSED_AT with it. What is stale is the sentence "
            "the object is documented by, which quotes "
            "Rem. rem:tolerancedomain's 0.2.0 form 'each of eps_1, ..., eps_5 "
            "and eps_gap'; at 0.3.0 the remark reads 'each of eps_1, ..., "
            "eps_6, eps_gap and eps_eig' and argues the two new members on the "
            "same ground -- eps_6 bounding a defect between two numbers in "
            "[0, 1], and eps_eig being subtracted from a quantity whose exact "
            "value lies in [0, 1]. REFRAMED: no value moves, and run B "
            "rewrites the narrative."
        ),
        replacement=(
            "TOLERANCE_FIXTURE_0_3_0",
            "TOLERANCES_CONDITIONALLY_REQUIRED_0_3_0",
        ),
    ),
)

#: The earlier objects the 0.3.0 amendment does NOT mark, recorded because a
#: supersession list is only useful if it is complete in both directions.
NOT_SUPERSEDED_BY_0_3_0: tuple[tuple[str, str], ...] = (
    (
        "EVERY FROZEN NUMBER IN BOUND_DATA_CASES -- every beta value, p_mc, "
        "window minimum, tail and residual gap",
        "Def. def:pmc's closing paragraph: 'A declaration carrying no depth at "
        "any setting is governed by Eq. eq:pmcdef ALONE: no beta* is formed, "
        "no eigenvalue of any block above the cutoff is computed, and "
        "Assumption ass:eig is not invoked.' Every one of the fourteen cases "
        "declares no depth, so every one of them is exactly what 0.3.0 emits. "
        "OPT_IN_INVARIANT records it case by case and "
        "BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0 re-derives it for the four the "
        "amendment would otherwise be expected to touch.",
    ),
    (
        "BD-BB84-N1-ZERO, BD-BB84-N2, BD-BB84-N3 and BD-BB84-PZ-QUARTER-N2 "
        "(p_mc = 0, 1/2, 3/4 and 1/8)",
        "Named individually because they are the cases the exact window WOULD "
        "change if a depth were declared. They declare none. The 0.3.0 "
        "counterparts EX-BB84-N1-M2-EIG-ZERO, EX-BB84-N2-M3-EIG-ZERO and "
        "EX-BB84-PZ-QUARTER-N1-M2-EIG-ZERO are DIFFERENT DECLARATIONS OF THE "
        "SAME DEVICE, and the two sets coexist. Eq. eq:pmcdef, Eq. eq:beta, "
        "Eq. eq:mcbound, Eq. eq:windowtail, Eq. eq:collapsehyp and the whole "
        "statement of Thm. thm:multiclick-bound are BYTE-IDENTICAL to 0.2.0's "
        "(STATUS.yaml gates.g1, re-checked by sha256 at every pass), so the "
        "values cannot have moved.",
    ),
    (
        "CONVENTION_KEYS_0_2_0",
        "Section 2.5 has SEVENTEEN bullets at 0.3.0, the same seventeen in the "
        "same order. EXACTLY TWO change text -- "
        "`numerical_tolerance_assignment` and the version bullet -- and this "
        "tuple carries KEYS and not text. CONVENTION_KEYS_0_3_0 is defined as "
        "this tuple rather than as a copy of it, so the identity is asserted "
        "rather than restated.",
    ),
    (
        "OUTPUT_KEYS and OUTPUT_PRESENCE",
        "NO OUTPUT KEY IS ADDED OR REMOVED at 0.3.0 and the one conditional "
        "key is still `receiver_construction` (route (iii) only). Three output "
        "rows change what they CONTAIN -- `high_photon_bounds`, "
        "`bound_quantifier_domain`, `validation_results` -- which is not a "
        "change to these tuples. OUTPUT_KEYS_0_3_0 is defined as OUTPUT_KEYS.",
    ),
    (
        "TOLMAP_I_CASES, TOLMAP_II_RANK_CASES, TOLMAP_V_CONTRACTIVITY_CASES "
        "and C_DIRECTION_CASES",
        "Items (i), (ii) and (v) of Def. def:tolmap are untouched, and "
        "Rem. rem:cdirection's bounds are untouched and STAY IN eps_2 -- which "
        "is step (3) of item (iv)'s derivation rather than an oversight. "
        "TOLMAP_IV_C_CASES is likewise not marked: its three rows decide c at "
        "eps_2 exactly as 0.3.0 requires, and at its fixture eps_1 = eps_2 the "
        "band is empty, so no row of it can be on the wrong side of the "
        "ruling.",
    ),
    (
        "RESIDUAL5_CASES, RES5_EXPECTATION_CASES and RESIDUAL_CASES",
        "r_1 to r_5 are untouched by the amendment. Prop. prop:res5 (iv)'s "
        "sentence now reads 'the other FIVE' where it read 'the other four', "
        "which is a count of residuals in prose and not a property of any "
        "frozen value; Def. def:residuals still names the SPECTRAL norm "
        "throughout, so no residual value moves.",
    ),
    (
        "DARK_CASES, DARK_SLACK_CASES, D2_SLACK_CASES, RMIN_TRAP_CASES and "
        "DARK_ROUTE_EXCLUSIVITY_CASES",
        "RC11 is untouched. Eq. eq:darkpmcslack composes with p_mc as the "
        "emitted bound whatever definition produced it, so the composition "
        "rule is indifferent to the exact window and no dark-count value "
        "changes.",
    ),
    (
        "COLLAPSE_SLACK_CASES, COLLAPSE_SLACK_COUNTS, PMC_BRANCH_CASES, "
        "PMC_X_CLAUSE_CASES and NOSLACK_STATEMENTS",
        "Predicate (X) is STILL the sole branch-1 selector and "
        "Rem. rem:noslack is untouched but for one added clause: 'The declared "
        "eps_eig of Definition def:pmcex is NOT A MARGIN OF THIS KIND AND "
        "DECIDES NO PREDICATE.' Section 1.1 (g) lists predicate (X), "
        "Lem. lem:collapse, Lem. lem:windowtail, Rem. rem:noslack and "
        "Rem. rem:windowdecidable as deliberately unchanged.",
    ),
    (
        "TIER_CASES, BOUND_EVALUATION_V1, ENCLOSURE_DIRECTIONS and "
        "TIER_FALLBACK_REASON_VERBATIM",
        "Thm. thm:exact-and-evaluated (iii) and (iv) are unchanged and (v) confirms the "
        "fail-closed tier rule reaches the opt-in route: 'no path in this "
        "module produces a certified label, SO NO ARTIFACT RESTING ON "
        "Assumption ass:eig CAN CARRY ONE.' The fallback string is "
        "byte-identical across all three versions.",
    ),
    (
        "every catalogue case, compile case, Fock case, Gram case, "
        "representation case, POVM block case, coarse-graining case and "
        "efficiency case; CATALOGUE_IDS and INPUT_ROUTES",
        "Section 1.1: the amendment 'executes two human rulings AND NOTHING "
        "ELSE; every other statement of 0.2.0 stands unchanged and is not "
        "re-opened here'. Neither ruling touches RC1-RC7, RC10, RC11 or RC12, "
        "and the three input ROUTES are the same three.",
    ),
    (
        "SUPERSEDED_BY_0_2_0, NOT_SUPERSEDED_BY_0_2_0 and PENDING_RETIREMENT_AT_RUN_B",
        "The 0.2.0 hand-off record is HISTORY and stays exactly as that pass "
        "left it. Its invariant still holds and is still asserted; this pass "
        "adds a parallel record rather than editing it, which is the same rule "
        "that stops it from marking rows in place.",
    ),
)


def supersession_0_3_0(name: str) -> Supersession0_3_0 | None:
    """Return the 0.3.0 mark on an earlier object, or None if it carries none."""
    for entry in SUPERSEDED_BY_0_3_0:
        if entry.name == name:
            return entry
    return None


def is_superseded_0_3_0(name: str) -> bool:
    """Report whether the 0.3.0 amendment marks the named object."""
    return supersession_0_3_0(name) is not None


#: WHERE THE 0.3.0-MARKED OBJECTS ARE STILL ASSERTED, AS RUN A LEAVES THE TREE.
#: Computed by scanning the run-B test files -- tests/golden/test_receiver_povm_*
#: , tests/unit/test_receiver_* and tests/property/test_receiver_povm_* -- for a
#: whole-word occurrence of each marked name. It is RUN B'S CHECKLIST, and the
#: integrity test asserts the real scan is a SUBSET of it: run B may only remove
#: references, never add one.
#:
#: NOTHING HERE IS A FAILURE TODAY. No code changed in this run, so every one of
#: these tests still replays a 0.2.0 value against a 0.2.0 implementation and
#: still passes. The invariant that bites is the other one: a run-B test file
#: that has moved to THIS amendment -- which it declares by naming
#: `receiver-povm@0.3.0` -- may NOT assert a 0.3.0-marked object without naming
#: SUPERSEDED_BY_0_3_0 itself. (file, marked name)
PENDING_RETIREMENT_AT_RUN_B_0_3_0: tuple[tuple[str, str], ...] = (
    ("tests/golden/test_receiver_povm_artifact_against_registry.py", "INPUT_KEYS"),
    (
        "tests/golden/test_receiver_povm_interface_against_registry.py",
        "ASSUMPTION_ROWS",
    ),
    (
        "tests/golden/test_receiver_povm_reasons_against_registry.py",
        "REFUSAL_REASONS_VERBATIM_0_2_0",
    ),
    (
        "tests/golden/test_receiver_povm_reasons_against_registry.py",
        "REASON_VOCABULARY_0_2_0",
    ),
    (
        "tests/golden/test_receiver_povm_reasons_against_registry.py",
        "REASON_EMITS_ARTIFACT",
    ),
    (
        "tests/golden/test_receiver_povm_reasons_against_registry.py",
        "MATHEMATICAL_SPEC_VERSION_0_2_0",
    ),
    (
        "tests/golden/test_receiver_povm_reasons_against_registry.py",
        "REFUSALS_NAMED_WITHOUT_A_SPELLING",
    ),
    (
        "tests/golden/test_receiver_povm_refusals_against_registry.py",
        "TOLERANCE_FIXTURE_0_2_0",
    ),
    (
        "tests/golden/test_receiver_povm_refusals_against_registry.py",
        "REFUSAL_REASONS_VERBATIM_0_2_0",
    ),
    (
        "tests/golden/test_receiver_povm_refusals_against_registry.py",
        "REASON_VOCABULARY_0_2_0",
    ),
    (
        "tests/golden/test_receiver_povm_refusals_against_registry.py",
        "REASON_EMITS_ARTIFACT",
    ),
    (
        "tests/golden/test_receiver_povm_refusals_against_registry.py",
        "REFUSALS_NAMED_WITHOUT_A_SPELLING",
    ),
    (
        "tests/golden/test_receiver_povm_residual5_against_registry.py",
        "RESIDUAL_ROUTE_PRESENCE",
    ),
    (
        "tests/golden/test_receiver_povm_tolmap_against_registry.py",
        "TOLERANCE_FIXTURE_0_2_0",
    ),
    ("tests/golden/test_receiver_povm_tolmap_against_registry.py", "TOLMAP_ITEMS"),
    (
        "tests/golden/test_receiver_povm_tolmap_against_registry.py",
        "TOLERANCE_DOMAIN",
    ),
    ("tests/unit/test_receiver_amendment_fail_closed.py", "TOLERANCE_FIXTURE_0_2_0"),
    ("tests/unit/test_receiver_fail_closed.py", "TOLERANCE_FIXTURE_0_2_0"),
    ("tests/unit/test_receiver_fail_closed.py", "TOLERANCE_DOMAIN"),
)


# ---------------------------------------------------------------------------
#  Change-request candidates cleared -- the 0.3.0 pass
# ---------------------------------------------------------------------------
#
#  The freeze rule requires that
#  anything the contract leaves this freeze unable to derive exactly be reported
#  as a change request rather than worked around. NOTHING WAS.
#
#  TEN items were carried into this freeze as candidates: ONE the 0.2.0 band's
#  G5 routed to this amendment, which the amendment CLOSES; two of the 0.2.0
#  pass's cleared items re-checked because the amendment touched their sites;
#  six raised NEW by this pass, all of which the contract answers; and ONE
#  OBSERVATION about the TREE rather than about the contract, routed to the
#  driver. `change_requests_open` in interface.yaml is empty and NO CHANGE
#  REQUEST IS RAISED AGAINST contract.tex 0.3.0.

CHANGE_REQUEST_CANDIDATES_0_3_0: tuple[tuple[str, str, str], ...] = (
    (
        "CLOSED BY 0.3.0 -- the item the 0.2.0 G5 routed to this amendment",
        "Which of Def. def:tolmap (iv) and (v) decides the admissibility of "
        "c? At the ordinary declaration eps_1 > eps_2 the band "
        "c in [-eps_1, -eps_2) is admitted by item (v)'s test and refused by "
        "item (iv)'s, and 0.2.0 stated no precedence. Routed at the "
        "0.2.0 G5 to 'whoever drafts this module's "
        "next Section 3 amendment'.",
        "ITEM (iv) WINS, AND THE BAND IS REFUSED. The ruling is DERIVED in "
        "item (iv) itself, in four steps, with the losing reading recorded and "
        "the reason it loses. The load-bearing step is (2): item (v)'s "
        "transport is an implication between EXACT quantities and 'transports "
        "no admission, because the computed lmax(Gamma^dagger Gamma) and the "
        "computed c are SEPARATE EVALUATIONS that Thm. thm:exact-and-evaluated (ii) relates by "
        "nothing'. Step (3) is independent and quantitative: admitting the "
        "band would falsify Rem. rem:cdirection's even-n bound, which is "
        "stated in eps_2 because item (iv) is what bounds |c|. FROZEN as "
        "TOLMAP_IV_PRECEDENCE_CASES (five cases bracketing the band), "
        "TOLMAP_IV_DERIVATION, TOLMAP_IV_BAND_COST and "
        "TOLMAP_IV_NO_BEHAVIOUR_CHANGE. NO EMITTED VALUE AND NO INTERFACE KEY "
        "CHANGES; what is new is that item (iv)'s failure is stated to be a "
        "refusal, and that refusal carries no tabulated reason string.",
    ),
    (
        "CLEARED (new at this freeze)",
        "Def. def:pmcex states no default depth. Should an implementation "
        "supply m*_t = N + 1, the minimal depth Ex. ex:bb84exact itself "
        "declares, when the caller supplies none?",
        "NO, AND THE CONTRACT SAYS SO TWICE RATHER THAN BEING SILENT. "
        "Section 2.1 `exact_window`: 'OPT-IN, NEVER DEFAULTED ... the depth is "
        "the caller's and THIS CONTRACT STATES NO DEFAULT FOR IT.' Section 1.2 "
        "decision dd:exactwindow: 'It is REQUESTED, NEVER DEFAULTED: the cost "
        "is a caller's to accept AND A PLATFORM DEFAULT WOULD BE AN UNDECLARED "
        "NUMBER.' And the consequence of supplying one is not merely a "
        "different value: it would invoke Ass. ass:eig on a declaration that "
        "did not ask for it, which Ass. ass:eig's own first sentence forbids. "
        "FROZEN as XW-ADMIT-NO-DEPTH-NO-CONDITIONAL-TOLERANCES beside "
        "XW-ADMIT-MINIMAL-DEPTH, so that the admissible minimum and the absent "
        "default are two different rows.",
    ),
    (
        "CLEARED (new at this freeze)",
        "Branch 2 of Eq. eq:pmcex has a middle minimum over m*_t < n <= m_t. "
        "At m*_t = m_t that index set is empty. Is the empty minimum 0 or "
        "+infinity?",
        "+INFINITY AND INACTIVE, STATED IN THE DEFINITION ITSELF: 'the middle "
        "minimum in the second case running OVER THE EMPTY INDEX SET -- AND SO "
        "EQUAL TO +INFINITY AND INACTIVE -- when m*_t = m_t'. The reading "
        "matters: taking it as 0 would drive the emitted value to 0 at every "
        "declaration with m*_t = m_t, which is valid but strictly worse and "
        "would contradict Prop. prop:exactnoworse at the one place the "
        "contract bothered to state a convention. FROZEN as "
        "EX-PROBE-ON-N1-M3-MSTAR3-EMPTY-MIDDLE, where the emitted value is "
        "107/750 and not 0, and as XW-ADMIT-DEPTH-EQUALS-TAIL-WINDOW, which "
        "admits the declaration that produces it.",
    ),
    (
        "CLEARED (new at this freeze)",
        "Are eps_6 and eps_eig required PER SETTING that carries a depth, or "
        "PER DECLARATION that carries one anywhere?",
        "PER DECLARATION, and both statements of the rule say 'anywhere' or "
        "'any setting'. Def. def:pmcex: 'DECLARING A DEPTH AT ANY SETTING "
        "requires eps_eig and eps_6.' Section 2.1 `numerical_tolerances`: "
        "'required exactly where an exact_window depth is declared, refused "
        "when missing there, and neither required nor an error WHEN NO DEPTH "
        "IS DECLARED ANYWHERE.' The two tolerances are single declared numbers "
        "and not per-setting families, unlike m_t and m*_t, so a per-setting "
        "requirement would have no object to attach to. FROZEN as "
        "MIX-DEPTH-AT-OFF-ONLY, where a depth at ONE of two settings requires "
        "both, and as XW-ADMIT-NO-DEPTH-NO-CONDITIONAL-TOLERANCES, where a "
        "declaration with no depth anywhere requires neither.",
    ),
    (
        "CLEARED (new at this freeze)",
        "Eq. eq:res6 takes a maximum 'over t, N < n <= m*_t'. Is r_6 one "
        "number for the whole declaration or one per setting?",
        "ONE NUMBER, and the quantifier is explicit in the equation. r_6 is "
        "'max over t and over N < n <= m*_t of (beta^(t)(n) - "
        "beta-hat*^(t)(n))_+', so a clean setting cannot mask a defective one "
        "and a defective index cannot be reported per setting. Section 2.2 "
        "`validation_results` carries it beside r_1 to r_5, which are likewise "
        "single numbers (r_5's own maximum runs over v, n AND t). FROZEN as "
        "R6-FAIL-ACROSS-SETTINGS, where the `off` setting contributes 0 and "
        "the `thermal` setting contributes 16/375 and the request is REFUSED, "
        "and as R6-FAIL-AT-THE-SECOND-INDEX, where the first index is exact "
        "and the second is not.",
    ),
    (
        "CLEARED (new at this freeze)",
        "Def. def:exactbnd forms blocks at N < n <= m*_t. Does the artifact "
        "then emit those blocks under `photon_blocks`, whose range is "
        "0 <= n <= N?",
        "NO. Section 2.2 `photon_blocks` fixes the range at 0 <= n <= N and "
        "the amendment does not touch it; what the exact window emits is a "
        "SCALAR into the strengthening slot and the computed EIGENVALUES into "
        "`bound_quantifier_domain`. Rem. rem:notsharp settles the permissive "
        "half in terms: 'an implementation is free to ALSO REPORT BLOCK "
        "EIGENVALUES AS A DIAGNOSTIC, the value entering the strengthening "
        "slot is p_mc, and the artifact says which definition produced it and "
        "at what depth'. AND THE PROHIBITION OF Section 2.2's CLOSING "
        "PARAGRAPH IS UNTOUCHED: calling a finite truncation of the blocks a "
        "squashing proof is 'exactly what ARCHITECTURE_SPEC.md Section 5.2 "
        "forbids this module to do'.",
    ),
    (
        "CLEARED (new at this freeze)",
        "At a setting where predicate (X) HOLDS, a tail_window may be supplied "
        "and is 'unused, not an error' (Rem. rem:windowdecidable). If a depth "
        "is also declared there, does m*_t <= m_t apply to that unused window?",
        "NO, AND THE SCOPE IS WRITTEN INTO THE CONSTRAINT. Def. def:pmcex: the "
        "depth is 'an integer with m*_t > N and, WHERE PREDICATE (X) FAILS AT "
        "t, ALSO m*_t <= m_t'. Where (X) holds the second clause does not "
        "apply, and it could not sensibly: branch 1 is taken, its remainder is "
        "beta(m*_t + 1), and m_t enters no expression Eq. eq:pmcex evaluates. "
        "The reading is sound as well as literal -- branch 1's remainder is "
        "admissible at every depth by Lem. lem:exactwindow (ii), which needs "
        "only Eq. eq:collapsehyp, which (X) supplies. FROZEN as "
        "XW-ADMIT-DEPTH-EXCEEDS-UNUSED-TAIL-WINDOW beside "
        "XW-REFUSE-DEPTH-EXCEEDS-TAIL-WINDOW, which is the same arithmetic at "
        "a setting where (X) FAILS and is REFUSED.",
    ),
    (
        "CLEARED (new at this freeze)",
        "Section 2.2 requires `bound_quantifier_domain` to carry 'the computed "
        "window values beta-hat*^(t)(n) ... THAT Eq. eq:elldef READ p_mc^(t) "
        "FROM'. Where the branch's remainder binds, p_mc was not read from any "
        "beta-hat*. Are they still carried?",
        "YES, ALL OF THEM ON THE WINDOW. The relative clause DESCRIBES the set "
        "-- the values on N < n <= m*_t, which is the range the same sentence "
        "names -- rather than filtering it by which one turned out to bind, "
        "and Rem. rem:exacteig states the purpose that settles it: "
        "beta-hat*^(t)(n) 'is carried in the artifact EXACTLY AS COMPUTED, and "
        "eps_eig enters only as a subtracted declared slack, SO A READER CAN "
        "RECOMPUTE Eq. eq:elldef AND SEE WHAT THE SLACK COST'. A reader cannot "
        "recompute Eq. eq:elldef from a filtered set. FROZEN implicitly by "
        "EX-BB84-N2-M3-EIG-ZERO and EX-BB84-PZ7-N1-M2-EIG-ZERO, where the "
        "remainder binds and the window value is nonetheless part of the "
        "frozen case.",
    ),
    (
        "CLEARED (re-checked at 0.3.0)",
        "How is a declared parameter REPRESENTED, given A-EXACT's exactness "
        "and A-FLOAT's floating-point evaluation? (Open implementation choice "
        "OIC-2.)",
        "STILL OPEN, STILL NOT DECIDED, AND STILL THE REASON THIS FILE FREEZES "
        "EXACT VALUES. The amendment does not touch Ass. ass:exact and touches "
        "Ass. ass:float only to say 'those of the SIX residuals that exist on "
        "the input route taken AND FOR THE EVALUATION REQUESTED' and to name "
        "Ass. ass:eig as the one asserted relation between a computed number "
        "and an exact one. Thm. thm:exact-and-evaluated (iv) is unchanged, including its "
        "contemplation of Grams 'DECLARED AS EXACT RATIONAL OR ALGEBRAIC "
        "DATA'. Section 1.3 now names an exact-arithmetic PSD certificate on "
        "route (i) as one of the two later claims that would discharge "
        "Ass. ass:eig -- A NAMED EXTENSION POINT, NOT A REQUIREMENT ON VERSION "
        "1, and it does not decide OIC-2.",
    ),
    (
        "OBSERVATION ROUTED TO THE DRIVER (not a change request against the contract)",
        "contract.tex's own version macro still reads `0.3.0-draft` "
        "(\\ContractVersion, line 198) after the G3 signature, "
        "while STATUS.yaml reads contract_version 0.3.0, state accepted, and "
        "gates.g3 signed_version 0.3.0.",
        "NOT A CHANGE REQUEST, AND NOT REPAIRED HERE. Dropping the `-draft` "
        "suffix at the signature is the TYPOGRAPHIC CORRECTION "
        "permitted in place -- 'a change that "
        "provably alters no claim, no symbol, and no number ... THE ONLY "
        "PERMITTED IN-PLACE EDIT' -- and this module executed it at both "
        "previous signatures (STATUS.yaml gates.g3 for 0.1.3 and for 0.2.0, "
        "each of which says so in terms). No claim, no bound and no emitted "
        "value depends on it. THIS FREEZE BINDS `receiver-povm@0.3.0` ON "
        "STATUS.yaml's AUTHORITY, which is the single source of truth for a "
        "module's version, and reports the residue rather than editing a "
        "contract that is frozen at G3. Recorded as "
        "CONTRACT_VERSION_RESIDUE_0_3_0 and as interface.yaml "
        "`observations_routed` OBS-1. The sentence "
        "above says what this freeze bound; the pin the CODE emits is "
        "`receiver@0.1.2`, this repository's accepted contract "
        "(spec/modules/receiver/module.yaml), recorded beside it as "
        "MATHEMATICAL_SPEC_VERSION_RECEIVER_0_1_2.",
    ),
)


# ===========================================================================
#  The registry
# ===========================================================================

RP_ORACLES: tuple[RPOracleEntry, ...] = (
    # Group RP-A -- the Fock functor and the occupation basis order.
    O_RP_FOCK,
    # Group RP-B -- compilation of a declared element graph.
    O_RP_COMPILE,
    # Group RP-C -- the component catalogue.
    O_RP_CATALOGUE,
    # Group RP-D -- port Grams, the deficiency, and vacuum elimination.
    O_RP_GRAMS,
    # Group RP-E -- representation independence.
    O_RP_REPRESENTATION,
    # Group RP-F -- the click-pattern POVM.
    O_RP_POVM,
    # Group RP-G -- declared coarse-graining.
    O_RP_COARSE,
    # Group RP-H -- the uniform high-photon multiclick bound.
    O_RP_BOUND,
    # Group RP-I -- version-1 numerics and the four residuals.
    O_RP_NUMERICS,
    # Group RP-J -- detection efficiency, exactly once.
    O_RP_EFFICIENCY,
    # Group RP-K -- dark counts as a classical outcome channel.
    O_RP_DARK,
    # Group RP-L -- probe conditioning.
    O_RP_PROBE,
    # Group RP-M -- the interface.
    O_RP_INTERFACE,
    # --- the 0.2.0 amendment -----------------------------------------------
    # Group RP-N -- the fifth residual r_5.
    O_RP_RES5,
    # Group RP-O -- the tolerance domain and Definition def:tolmap.
    O_RP_TOLMAP,
    # Group RP-P -- the dark-count slack: rbar, delta_dc, eq:darkpmcslack.
    O_RP_DARKSLACK,
    # Group RP-Q -- the (X)-only branch selector of Definition def:pmc.
    O_RP_PMC_BRANCH,
    # Group RP-R -- Section 2.6 as a key vocabulary.
    O_RP_REASONS,
    # --- the 0.3.0 amendment -----------------------------------------------
    # Group RP-S -- the exact block quantity beta*(n).
    O_RP_EXACT_BLOCK,
    # Group RP-T -- Lemma lem:exactwindow and the emitted Eq. eq:pmcex.
    O_RP_EXACT_WINDOW,
    # Group RP-U -- the sixth residual r_6 and the A-EIG witness.
    O_RP_RES6,
    # Group RP-V -- the exact window's input validation and its refusals.
    O_RP_EXACT_WINDOW_VALIDATION,
    # Group RP-W -- Definition def:tolmap (iv) decides c alone.
    O_RP_TOLMAP_IV,
)


# ===========================================================================
#  Change-request candidates cleared
# ===========================================================================
#
#  Ten items were carried into this freeze as candidates for a change request
#  against the accepted contract. EACH IS RECORDED BELOW WITH THE READING TAKEN.
#  SIX ARE CLEARED -- the contract answers them, and the answer is transcribed
#  rather than improvised. FOUR ARE ROUTED for the driver, and NONE OF THE FOUR
#  BLOCKS THIS FREEZE: nothing frozen here depends on any of them, and a
#  conforming implementation exists on every reading. The four routed items are
#  CR-1 to CR-4 of interface.yaml.

CHANGE_REQUEST_CANDIDATES: tuple[tuple[str, str, str], ...] = (
    (
        "CLEARED",
        "The mode label's reserved index tau 'may take only a single declared "
        "value in version 1' (Definition def:modes) -- but no section says "
        "WHERE that is validated, and no check is given an identifier.",
        "READING TAKEN, NO RULE ADDED. The restriction is stated TWICE -- "
        "Definition def:modes and Assumption ass:thresh ('the reserved index "
        "tau of Definition def:modes takes a single value, and NO ELEMENT "
        "READS IT') -- and it is decidable BY INSPECTION OF THE INPUT KEY "
        "`mode_space`, since every declared label carries its tau. The "
        "`fail_closed` convention of Section 2.5 then makes a declaration with "
        "two distinct tau values a refusal with a machine-readable reason and "
        "no artifact, exactly as it makes every other failed validation one. "
        "THE CONTRACT NAMES NO SEPARATE CHECK ID AND NONE IS INVENTED: no "
        "frozen refusal case here carries one, and every frozen mode space "
        "declares a single tau = 0.",
    ),
    (
        "ROUTED -- does not block this freeze; interface.yaml CR-1",
        "`dark_count_channel` admits 'EITHER the per-port independent form "
        "from {p_dc|k}, OR a declared column-stochastic multiclick-absorbing "
        "R' -- but `detector_layer` carries p_dc|k UNCONDITIONALLY, so both "
        "are always expressible, and no precedence rule or refusal is stated "
        "for a request supplying both inconsistently.",
        "NO PRECEDENCE IS INVENTED. Remark rem:corrdark presupposes that "
        "exactly one route was taken -- 'the artifact records WHICH OF THE TWO "
        "ROUTES the emitted R came from' -- and the `fail_closed` convention "
        "together with the exactly-one-route rule the THREE INPUT ROUTES "
        "already carry points at a refusal, but that is a reading and not the "
        "text. WHAT IS FROZEN INSTEAD: DARK-K2 and DARK-K3 are per-port product "
        "forms with no declared R; DARK-NOT-MONOTONE-REFUSED is a declared R "
        "with no per-port form; NO FROZEN CASE SUPPLIES BOTH. A human decides "
        "between precedence, refusal, and a consistency check.",
    ),
    (
        "CLEARED",
        "A tail_window declared at a setting that does NOT need one -- refused, "
        "carried, or ignored?",
        "ANSWERED VERBATIM BY REMARK rem:windowdecidable: 'A WINDOW SUPPLIED AT "
        "A SETTING WHERE (X) HOLDS IS UNUSED, NOT AN ERROR.' So the three cases "
        "are settled and distinct, and WINDOW_REQUIREMENT_CASES freezes all "
        "four settings: missing where needed -> REFUSED; m_t <= N -> REFUSED; "
        "present where not needed -> CARRIED AND UNUSED, never a refusal.",
    ),
    (
        "CLEARED",
        "Are eps_hyp and eps_gap required inputs when NO PROBE is declared, "
        "where predicate (C) is never evaluated and no window exists?",
        "TRANSCRIBED AS WRITTEN, WITH THE STANDING OBSERVATION NAMED. "
        "Definition def:pmc's 'Refusals' paragraph is UNCONDITIONAL: 'A "
        "declaration supplying no eps_hyp ... is refused rather than "
        "defaulted', with no scoping to probe-declaring receivers. So a "
        "probe-free receiver must declare eps_hyp although it can only ever "
        "take branch 1 through (X). The round-3 verifier recorded exactly this "
        "as a non-blocking wording observation ('the unconditional eps_hyp "
        "requirement'), the scoped prose-only pass deliberately did not touch "
        "it, and THE G3 SIGNATURE RECORDS IT AS STANDING -- so it is signed "
        "text, not an oversight, and this freeze transcribes rather than "
        "narrows it (REF-EPS-HYP-MISSING). eps_gap by contrast IS scoped by its "
        "own clause, 'where a window is declared', and Section 2.2 "
        "`validation_results` reports the achieved gap 'at each setting THAT "
        "DECLARES A WINDOW'.",
    ),
    (
        "ROUTED -- does not block this freeze; interface.yaml CR-2",
        "Section 2.4's Units bullet names TWO presentations that are converted "
        "at validation -- decibels and A SPLITTING RATIO -- and gives a formula "
        "for only the first.",
        "NO CONVERSION IS INVENTED. A ratio 'a : b' does not by itself fix "
        "whether it is a POWER or an AMPLITUDE ratio, which of the two declared "
        "C1 output paths the first term refers to, or whether it fixes x or "
        "1 - x; and Eq. eq:bs's x is a TRANSMITTANCE, so two of those three "
        "ambiguities change the compiled matrix and the third permutes the "
        "ports. A wrong reading is SILENT: 90:10 read as an amplitude ratio "
        "gives x = 81/100 instead of 9/10. WHAT IS FROZEN INSTEAD: every "
        "beamsplitter case declares x DIRECTLY, and the only presentation "
        "conversion frozen is the decibel one, at the three exponents where it "
        "is exactly rational (DECIBEL_CONVERSIONS).",
    ),
    (
        "CLEARED",
        "Is the instrument matrix Gamma itself emitted on route (ii), given "
        "that Theorem thm:representation-independence makes the Grams canonical?",
        "NO. The output table of Section 2.2 has FIFTEEN keys and none carries "
        "Gamma; `receiver_construction`, the only key that could, is 'ABSENT "
        "EXACTLY WHEN THE GRAMS OR THE INSTRUMENT MATRIX WERE SUPPLIED "
        "DIRECTLY'. That is consistent rather than lossy: Theorem thm:representation-independence (i) "
        "says the click statistics depend on the instrument ONLY through the "
        "Grams, and (ii) says every admissible family is realized by SOME "
        "instrument, so no particular Gamma is canonical -- REP-REALIZE-RANK2 "
        "freezes two of different shapes with one Gram family. Frozen as "
        "RECEIVER_CONSTRUCTION_PRESENCE row RC-ROUTE-II.",
    ),
    (
        "CLEARED, WITH AN OPEN CHOICE RECORDED",
        "Who fixes the ORDER of the emitted alphabet V that "
        "outcome_coarse_graining maps onto?",
        "THE PROTOCOL DECLARATION DOES, AS DATA. Definition def:coarse: cg is "
        "'supplied AS DATA by the protocol declaration', and Section 2.1's "
        "closing paragraph names V a DATA-FLOW input, 'supplied at run time by "
        "the protocol declaration', not a contract dependency. Section 2.2 then "
        "fixes what the module emits: 'the canonical ORDERED emitted alphabet "
        "... STABLE IDS, LABELS ARE PRESENTATION METADATA'. WHAT IS NOT FIXED "
        "-- which particular IDs, and whether the order is V's declared order "
        "or one derived from 2^[K] through cg -- IS RECORDED AS OPEN "
        "IMPLEMENTATION CHOICE OIC-1 AND IS NOT DECIDED. No theorem "
        "distinguishes two choices: Theorem thm:coarse-graining indexes by the LETTER and "
        "sums over a FIBRE, which is a set. Section 3(a) additionally discloses "
        "that V collides with the declaration's JOINT alphabet in the pinned "
        "SYMBOLS.md and states which is meant: 'AN IMPLEMENTER BINDING THAT KEY "
        "AT G4 BINDS THE RECEIVER ALPHABET, NOT THE DECLARATION'S.' This freeze "
        "so binds it.",
    ),
    (
        "CLEARED, WITH AN OPEN CHOICE RECORDED",
        "How is a declared parameter such as x = 1/3 REPRESENTED, given "
        "A-EXACT's 'exactly zero tolerance' and A-FLOAT's floating-point "
        "evaluation?",
        "THE TWO ARE ABOUT DIFFERENT OBJECTS AND DO NOT CONFLICT. Assumption "
        "ass:exact is about the DATUM: 'every declared component parameter ... "
        "is EXACT', and the reserved tolerance field is refused unless absent "
        "or zero. Assumption ass:float is about the EVALUATION: version 1 "
        "'EVALUATES them in IEEE-754 double precision' and asserts no enclosure. "
        "Theorem thm:exact-and-evaluated (i)-(ii) states the separation directly, and (iv) "
        "explicitly contemplates Grams 'DECLARED AS EXACT RATIONAL OR ALGEBRAIC "
        "DATA' without requiring or forbidding it. THE REPRESENTATION IS "
        "THEREFORE CODE'S, recorded as open implementation choice OIC-2 and not "
        "decided -- and it is exactly why THIS FILE FREEZES EXACT VALUES: an "
        "exactly declared parameter has an exact answer, and a frozen expected "
        "value carrying a tolerance of its own invention would decide what the "
        "contract leaves open. The one tolerance object here, "
        "TOLERANCE_FIXTURE, plays the role of the DECLARED input and is "
        "documented as such.",
    ),
    (
        "ROUTED -- does not block this freeze; interface.yaml CR-3",
        "Remark rem:bsconv claims the symmetric beamsplitter convention gives "
        "THE SAME PORT GRAMS as B(x, 0) 'by Corollary cor:phases' -- but "
        "cor:phases is Theorem thm:representation-independence (iii), an OUTPUT-side statement.",
        "CHECKED EXACTLY, AND THE CLAIM DOES NOT FOLLOW AS STATED. At "
        "x = 9/25, where every amplitude is rational, the symmetric matrix is "
        "diag(1, i) B(9/25, 0) diag(1, i): an output-side phase AND AN "
        "INPUT-side one. REP-BSCONV-OUTPUT-PHASE freezes that the output factor "
        "alone leaves every Gram unchanged, which IS thm:representation-independence (iii); "
        "REP-BSCONV-SYMMETRIC freezes that the full symmetric convention's "
        "Grams are the CONJUGATES A_k -> diag(1,-i) A_k diag(1,i) and are "
        "therefore DIFFERENT matrices. The two families are unitarily "
        "equivalent under a fixed input-path phase, so the two conventions "
        "describe the same device relative to an INPUT-PATH PHASE CONVENTION -- "
        "which Section 2.5 fixes for polarization and not for spatial input "
        "paths. SEVERITY LOW: rem:bsconv is a remark, no claim consumes it, and "
        "`beamsplitter_convention` FIXES the core to B(x, phi), so no emitted "
        "number depends on the resolution. The frozen pair is the evidence.",
    ),
    (
        "ROUTED -- does not block this freeze; interface.yaml CR-4",
        "Predicate (C) of Definition def:pmc -- 'sum_k beta_k - 1 - (K-1) gamma "
        ">= eps_hyp > 0' -- appears to be UNREACHABLE for every receiver this "
        "contract describes.",
        "DERIVED IN FULL IN O-RP-BOUND AND FROZEN IN BETA_ZERO_AND_C_SLACK. The "
        "(C) slack is exactly -beta(0); Remark rem:collapse-fails states that "
        "blk M^{(=0)}_mc = beta(0) EXACTLY; that block is a diagonal block of a "
        "sum of POVM elements and is one-dimensional, hence a NON-NEGATIVE "
        "REAL; so beta(0) >= 0 always, Eq. eq:collapsehyp holds iff "
        "beta(0) = 0, and (C) -- which demands STRICT slack -- can never fire. "
        "Nine of the fourteen frozen bound-data cases have beta(0) = 0 exactly "
        "and five have it strictly positive; NONE has a positive slack. NOT A "
        "SOUNDNESS DEFECT: branch 2 is unconditionally valid "
        "(Lemma lem:windowtail (i)), so (C) never firing costs tightness and "
        "never safety. WHAT THIS FREEZE DOES: it freezes that a conforming "
        "implementation EVALUATES (C) EXACTLY AS WRITTEN, with the strict "
        "declared margin, and NEVER relaxes it -- the tempting repair, testing "
        "|beta(0)| <= eps_hyp, would license branch 1 on a COMPUTED "
        "near-equality, which is what round-1 finding F-1-03 and round-2 "
        "finding F-2-01 were about, and is a change of mathematical substance "
        "that belongs to a human at G3. No frozen p_mc is computed through (C).",
    ),
)


#: THE RUN-A MARKER. This registry's own header: run A derives by hand and writes no source file; run B writes the code
#: against these values and MAY READ BUT NOT MODIFY THEM.
TWO_INSTANCE_FREEZE_RP_X: str = (
    "run A. Derived by hand by an agent that wrote none of the "
    "fixtures these values concern, edited no file under the worktree, and "
    "imported no part of the earlier package. Run B re-points "
    "tests/golden/test_receiver_povm_docking.py against these values and "
    "invents no expected number."
)

#: The evidential status of every entry here, as everywhere in this registry.
ASSURANCE_RP_X: str = "estimate"

#: The consuming contract these statements are about.
CONSUMER_CONTRACT_SHA256_RP_X: str = (
    "f12d712fed3c20c9f5736b5af69e9822aa9aba9ca0075d55811a5bd88a004df6"
)

#: The largest lattice exponent this file's declarations admit, and why. The
#: ``lattice_exponent`` row validates 1 <= kappa <= 53 AND
#: kappa + ceil(log2 max{|V|,|Y|,|T|}) <= 53. Both receivers here emit a
#: six-letter alphabet at one or two settings, so the ceiling term is 3.
KAPPA_MAX_RP_X: int = 50
#: One ulp of one in binary64, which is the size of the BB84 defect.
ULP_OF_ONE: F = F(1, 2**52)


@dataclass(frozen=True)
class DyadicObstruction:
    """One statement of the form: no dyadic device parameter makes this land.

    ``statement`` is the proposition; ``proof`` is the argument in full;
    ``witness`` is the exact non-dyadic value the current fixture produces;
    ``consequence`` names the row of proof-reductions 1.0.1 that then refuses.
    """

    case_id: str
    claims: tuple[str, ...]
    fixture: str
    statement: str
    proof: str
    witness: tuple[tuple[str, F], ...]
    consequence: str
    what_would_fix_it: str
    labels: tuple[str, ...]
    route_a: str
    route_b: str
    agreement: str


RPX_1 = DyadicObstruction(
    case_id="RPX-1-no-dyadic-beamsplitter",
    claims=("RC2", "RC3", "RC4"),
    fixture="bb84_channel_only_request (tests/support/receiver_povm_support.py)",
    statement=(
        "A lossless two-port beamsplitter of transmissivity x has amplitudes "
        "sqrt(x) and sqrt(1 - x). BOTH ARE DYADIC RATIONALS ONLY FOR x = 0 AND "
        "x = 1, i.e. only for the trivial device that splits nothing. "
        "Consequently no choice of x puts a compiled instrument matrix carrying "
        "a beamsplitter on any dyadic lattice, and the same argument forbids a "
        "dyadic pair of mutually unbiased bases -- which is what a BB84 receiver "
        "measures."
    ),
    proof=(
        "Suppose sqrt(x) = A/2^m and sqrt(1 - x) = B/2^m with A, B non-negative "
        "integers over a common power-of-two denominator. Squaring and adding "
        "gives A^2 + B^2 = 2^(2m) = (2^m)^2, so (A, B, 2^m) is a Pythagorean "
        "triple. Every Pythagorean triple with A, B > 0 is a positive integer "
        "multiple of a PRIMITIVE one, and the hypotenuse of a primitive triple "
        "is odd and strictly greater than 1 -- it is a product of primes "
        "congruent to 1 mod 4. So every hypotenuse with A, B > 0 has an odd "
        "factor above 1. The integer 2^m has none. Hence A = 0 or B = 0, i.e. "
        "x = 0 or x = 1. QED. "
        "THE SAME ARGUMENT KILLS THE X-BASIS PORTS: a unit vector with dyadic "
        "components in a two-dimensional real space is (+-1, 0) or (0, +-1) up "
        "to the same triple condition, so |+> = (|H> + |V>)/sqrt2 has no dyadic "
        "presentation and no rotation of the H/V basis by anything other than a "
        "multiple of a quarter turn does either."
    ),
    witness=(
        ("the declared transmissivity x", F(1, 2)),
        ("the EXACT Gram entry (A_Sigma)_HH at p_Z = 1/2", F(1)),
        ("the EMITTED binary64 value of the same entry", 1 + F(1, 2**52)),
        ("the defect, one ulp of one", F(1, 2**52)),
    ),
    consequence=(
        "The emitted block carries 1 + 2^-52, which FAILS |x| <= 1 of "
        "Eq. eq:latinv OUTRIGHT -- before any lattice question arises -- so "
        "proof-reductions 1.0.1 refuses the declaration under "
        "`declaration_not_exactly_admissible` (Section 4.14, the declared-blocks "
        "row; def:exactadm (b), (c)). At 0.3.0 the same datum was refused under "
        "`declaration_outside_tolerance`, and at 0.1.3 under "
        "`no_block_structure`, on a block whose smallest eigenvalue the file's "
        "own docstring records as -2.2e-16."
    ),
    what_would_fix_it=(
        "THE INSTANCE'S SNAP, and nothing this freeze can supply. The exact "
        "Grams at p_Z = 1/2 ARE dyadic -- A_H = (1/2)diag(1,0), "
        "A_+ = (1/4)[[1,1],[1,1]] -- so the mathematics is already on the "
        "lattice and only the evaluation is not. ADR-0008 Section 7.2 and "
        "ARCHITECTURE_SPEC.md Section 3.8 put the repair at the instance, by the "
        "documented table, with the pre-snap defect and the displacement "
        "recorded; proof-reductions 1.0.1's ``photon_blocks`` row says that "
        "record 'is the instance's and is not an input of this module'. The "
        "golden file docks the receiver artifact into ``reduce`` with NO "
        "INSTANCE BETWEEN THEM, which is a composition 1.0.0 does not sanction. "
        "A SECOND, LESSER OPTION: declare the receiver on route (ii) with an "
        "exactly representable instrument matrix, which is what makes the probe "
        "receiver's optics dyadic and the BB84 receiver's not."
    ),
    labels=("def:exactadm", "eq:latinv", "sec:failclosed"),
    route_a=(
        "ROUTE A -- THE NUMBER-THEORETIC ROUTE, above: a power of two is not a "
        "Pythagorean hypotenuse, so no non-trivial beamsplitter has dyadic "
        "amplitudes."
    ),
    route_b=(
        "ROUTE B -- INDEPENDENTLY, BY THE EVALUATION RATHER THAN BY THE ALGEBRA, "
        "and it reaches the same refusal without using the triple argument at "
        "all. binary64 has no exact square root of 1/2: the correctly rounded "
        "sqrt(0.5) is s = 6369051672525773 * 2^-53 (verified against the exact "
        "rational, not asserted), and s * s rounds to 1/2 + 2^-53 rather than "
        "to 1/2. A Gram diagonal that is the sum of two such squares therefore "
        "returns 1 + 2^-52 -- which is exactly the 1 + 2.2e-16 the golden "
        "file's own docstring records for A_Sigma, and 2 * cos(pi/4)^2 "
        "evaluates to the same number for the same reason. Since 1 + 2^-52 > 1, "
        "Eq. eq:latinv's SECOND clause, |x| <= 1, fails for EVERY kappa, so the "
        "refusal does not depend on the choice of lattice at all -- which route "
        "A's argument alone would not have shown."
    ),
    agreement=(
        "Route A shows no re-parametrisation can make the amplitudes dyadic; "
        "route B shows that at the declared parametrisation the emitted value is "
        "1 + 2^-52 and already outside eq:latinv's modulus bound. Both land on "
        "the same refusal, `declaration_not_exactly_admissible`, and on the same "
        "conclusion: THE FIX IS NOT A DEVICE PARAMETER."
    ),
)

RPX_2 = DyadicObstruction(
    case_id="RPX-2-no-dyadic-schur-prefactor",
    claims=("RC8", "RC12"),
    fixture="probe_receiver_request at the 'on' (thermal) setting",
    statement=(
        "For a single-mode thermal probe of mean photon number nbar the Schur "
        "prefactors are gamma = 1/(1 + nbar * s) and beta_k = 1/(1 + nbar * s_k) "
        "with s = s_1 + s_2 the probe-mode diagonal entries of the port Grams. "
        "IF THE PROBE COUPLES TO BOTH PORTS -- s_1 > 0 and s_2 > 0 -- THEN "
        "gamma AND BOTH beta_k CANNOT ALL BE DYADIC, AT ANY nbar > 0. The "
        "obstruction is exact rather than numerical: no rounding is involved and "
        "no snap at the instance is contemplated by the receiver's own model."
    ),
    proof=(
        "A reciprocal 1/(1 + u) with u >= 0 is a dyadic rational of modulus at "
        "most 1 exactly when 1 + u is a non-negative power of two. Write "
        "1 + nbar*s = 2^a, 1 + nbar*s_1 = 2^b1, 1 + nbar*s_2 = 2^b2. Adding the "
        "last two and using s_1 + s_2 = s gives "
        "(2^b1 - 1) + (2^b2 - 1) = 2^a - 1, i.e. 2^b1 + 2^b2 = 2^a + 1. "
        "The right-hand side is odd, so the left-hand side must be odd, so "
        "exactly one of b1, b2 is zero; say b1 = 0. Then 2^b2 = 2^a and b2 = a, "
        "and b1 = 0 forces nbar*s_1 = 0, hence s_1 = 0 for nbar > 0. So the "
        "probe couples to at most one port. QED."
    ),
    witness=(
        ("nbar as declared", F(1)),
        ("(A_Sigma)_ss for the two ports", F(1, 2)),
        ("(A_k)_ss for each port", F(1, 4)),
        ("gamma = 1/(1 + 1 * 1/2)", F(2, 3)),
        ("beta_k = 1/(1 + 1 * 1/4)", F(4, 5)),
    ),
    consequence=(
        "gamma = 2/3 and beta_k = 4/5 are EXACT non-dyadic rationals, and they "
        "pass straight into the conditioned blocks the receiver emits and into "
        "the high-photon weight it certifies. Any declaration carrying this "
        "setting therefore presents proof-reductions with declared blocks off "
        "every dyadic lattice, refused under "
        "`declaration_not_exactly_admissible`, and with a declared p_i that "
        "def:exactadm (b) also binds to eq:latinv. THE ONLY nbar THAT ESCAPES "
        "IS nbar = 0, which is the vacuum setting and is a different declared "
        "setting, not a re-parametrisation of this one."
    ),
    what_would_fix_it=(
        "Either the instance's snap (as in RPX-1 -- and here the snap really "
        "would be doing arithmetic work rather than undoing a rounding, since "
        "2/3 is not near any coarse dyadic), or a declaration in which the probe "
        "couples to ONE port only, which is the single family the proof leaves "
        "open and which is a different receiver rather than a different "
        "parameter. NEITHER IS THIS FREEZE'S TO CHOOSE."
    ),
    labels=("def:exactadm", "eq:latinv"),
    route_a=(
        "ROUTE A -- THE DIOPHANTINE ROUTE, above: 2^b1 + 2^b2 = 2^a + 1 forces "
        "one of the exponents to zero by a parity argument."
    ),
    route_b=(
        "ROUTE B -- BY EXHAUSTION OVER THE DECLARABLE nbar, WITHOUT THE PARITY "
        "ARGUMENT. At the declared Grams s = 1/2 and s_k = 1/4, gamma is dyadic "
        "iff 1 + nbar/2 is a power of two, i.e. nbar in {0, 2, 6, 14, 30, ...} = "
        "{2(2^a - 1)}; beta_k is dyadic iff 1 + nbar/4 is, i.e. nbar in "
        "{0, 4, 12, 28, 60, ...} = {4(2^b - 1)}. The two sets are compared term "
        "by term: 2(2^a - 1) = 4(2^b - 1) requires 2^a = 2^(b+1) - 1, and a "
        "power of two is one less than a power of two only at 1 = 2 - 1, giving "
        "a = 0 and nbar = 0. THE INTERSECTION IS {0}, which is the vacuum "
        "setting. The two sets are listed here rather than characterised, so a "
        "reader can check the first four terms of each by hand."
    ),
    agreement=(
        "Route A proves the impossibility for arbitrary Grams; route B "
        "instantiates it at the declared Grams and finds the two dyadicity sets "
        "meeting only at nbar = 0. Both return: gamma = 2/3 and beta_k = 4/5 at "
        "the declared nbar = 1, no admissible nbar > 0, and the refusal "
        "`declaration_not_exactly_admissible` on any declaration carrying this "
        "setting."
    ),
)


@dataclass(frozen=True)
class DyadicDarkCountCase:
    """The one row of the docking map a device choice reaches: the raw R."""

    case_id: str
    claims: tuple[str, ...]
    ports: int
    #: (port, 0.3.0 per-port dark-count probability, dyadic replacement, j).
    per_port: tuple[tuple[str, F, F, int], ...]
    #: The RAW R over 2^[K], column by column, in the docked (1-based) indexing.
    raw_matrix: tuple[tuple[str, tuple[tuple[str, F], ...]], ...]
    column_sums: tuple[tuple[str, F], ...]
    min_entry: F
    monotone: bool
    #: The single r_min this module emits, over the raw non-multiclick columns.
    r_min: F
    r_min_before: F
    lattice_exponent_reached: int
    labels: tuple[str, ...]
    route_a: str
    route_b: str
    agreement: str


RPX_3 = DyadicDarkCountCase(
    case_id="RPX-3-dyadic-dark-counts-K2",
    claims=("RC11",),
    ports=2,
    per_port=(("1", F(1, 10), F(3, 32), 5), ("2", F(1, 5), F(3, 16), 4)),
    raw_matrix=(
        (
            "e",
            (
                ("e", F(377, 512)),
                ("1", F(39, 512)),
                ("2", F(87, 512)),
                ("12", F(9, 512)),
            ),
        ),
        ("1", (("e", F(0)), ("1", F(13, 16)), ("2", F(0)), ("12", F(3, 16)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(29, 32)), ("12", F(3, 32)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(1)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(0),
    monotone=True,
    r_min=F(9, 512),
    r_min_before=F(1, 50),
    lattice_exponent_reached=9,
    labels=("lem:descent", "cor:oneabsorbing", "sec:failclosed"),
    route_a="""\
ROUTE A. THE ONE ROW OF THE FIELD-TO-ROW MAP WHOSE VALUES ARE DECLARED DEVICE
CONSTANTS RATHER THAN EVALUATED ONES, and therefore the one this freeze can
reach. The per-port dark-count probabilities are declared on the detector layer;
the docked ``dark_count_channel`` carries their product form and nothing else.

DYADIC REPLACEMENT under the selection rule of freeze/parameters.md: 1/10 ->
3/32 (nearest at j = 5, displacement 1/160) and 1/5 -> 3/16 (nearest at j = 4,
displacement 1/80). Both are exactly representable in binary64 with a two-bit
significand, so the product form below is evaluated WITHOUT ROUNDING -- which is
what makes this row, and only this row, reachable.

THE PRODUCT FORM, R_{S|S'} = 0 unless S' subset S and otherwise
prod_{k in S\\S'} p_k prod_{k not in S} (1 - p_k), with a = 3/32 and b = 3/16:
  col e  : ((29/32)(13/16), (3/32)(13/16), (29/32)(3/16), (3/32)(3/16))
         = (377/512, 39/512, 87/512, 9/512), summing to
           (377 + 39 + 87 + 9)/512 = 512/512 = 1 ;
  col 1  : (0, 13/16, 0, 3/16) ;
  col 2  : (0, 0, 29/32, 3/32) ;
  col 12 : (0, 0, 0, 1) .
Every entry is an integer multiple of 2^-9, so eq:latinv holds at every
kappa >= 9 and in particular at the file's own kappa = 12. Every column sums to
1 exactly and the smallest entry is 0, so the column-stochasticity row admits;
every non-zero entry has S' subset S, so the monotonicity half of the descent
row admits.

r_min, THE ONE THIS MODULE EMITS, is the minimum over the RAW non-multiclick
columns of the multiclick row: min(ab, b, a) = min(9/512, 3/16, 3/32) = 9/512,
from the empty column, which needs BOTH ports to fire spuriously. The 0.3.0
fixture's value was (1/10)(1/5) = 1/50 = 0.02, which the golden file asserts
through ``pytest.approx``; the dyadic value is 9/512 = 0.017578125, and a
re-pointed assertion must be EXACT rather than approximate, since nothing about
it is approximate any more.

WHAT THIS DOES NOT BUY. It makes one docked row lattice-clean. It does nothing
for ``photon_blocks`` or for the ``high_photon_bounds`` weight, which are RPX-1's
and RPX-2's subjects, and a declaration is admitted or refused as a whole.""",
    route_b="""\
ROUTE B -- BY THE COMPLEMENT AND BY INTEGERS, NOT BY THE PRODUCT FORM.

Over 2^-9 the empty column is (377, 39, 87, 9) out of 512. Route A formed all
four by multiplying; route B forms three and takes the fourth by subtraction,
which is the column-stochasticity identity rather than the product rule:
  R_{1|e}  = a(1 - b) = 3 * 13   = 39 ;
  R_{2|e}  = (1 - a)b = 29 * 3   = 87 ;
  R_{12|e} = ab       = 3 * 3    = 9 ;
  R_{e|e}  = 512 - 39 - 87 - 9   = 377 ,
and route A's direct product (1 - a)(1 - b) = 29 * 13 = 377 AGREES. The
factorisation 512 = 32 * 16 is what makes both routes integer arithmetic.

r_min WITHOUT A MINIMUM. cor:oneabsorbing's inequality direction gives it: the
three candidates are ab, a and b with a, b in (0, 1), and ab < a and ab < b
strictly, so the minimum IS the empty column's entry and no comparison of a
against b is needed. 9/512 either way.

THE MONOTONICITY, AS A COUNT. There are 16 positions and 7 of them are forbidden
(S' not subset S). All seven carry the entry 0 here, so the implication
R_{S|S'} > 0 => S' subset S is vacuous at every forbidden position and true at
every permitted one. Seven zeros, checked as a count rather than as a scan.""",
    agreement="""\
Route A multiplies out the empty column; route B builds three of its entries and
takes the fourth as 512 minus the rest, and both return 377/512. Route A takes
r_min as a three-way minimum; route B takes it from ab < min(a, b) without
comparing. Both return r_min = 9/512, the four unit column sums, min_entry = 0
and monotone = True.""",
)


#: WHAT THIS GROUP DELIBERATELY DOES NOT FREEZE, AND ON WHOSE AUTHORITY.
#: A list beside the entries, never a field inside one.
NOT_FROZEN_AND_WHY_RP_X: tuple[tuple[str, str], ...] = (
    (
        "the emitted photon blocks and p_mc of either receiver, at any setting",
        "THEY ARE receiver-povm QUANTITIES AND THIS RUN DID NOT OPEN THAT "
        "CONTRACT. Deriving beta(n), the window minimum, the tail and p_mc "
        "requires def:pmc, lem:windowtail and def:blockMS of receiver-povm at "
        "its accepted version, and a value derived from a contract the freezer "
        "has not read character for character at its locator is evidence, never "
        "authority. "
        "RPX-1 and RPX-2 establish that no dyadic device choice makes them "
        "land, which is all this freeze needs to decide the retarget plan; the "
        "numbers themselves belong to a receiver-povm run-A band.",
    ),
    (
        "the vacuum ('off') setting of the probe receiver, where the obstruction "
        "of RPX-2 is absent",
        "AT Gamma^(t) = 0 the Schur prefactors are exactly 1 (thm:gaussian-schur "
        "(iii): 'at Gamma = 0, Gamma^{1/2} = 0 kills the subtrahend and "
        "det(1 + 0) = 1'), so RPX-2's Diophantine obstruction does not arise "
        "and the conditioned Grams are the channel blocks. WHETHER THE "
        "RESULTING BLOCKS AND p_mc THEN LIE ON A LATTICE IS THE PRECEDING "
        "ENTRY'S QUESTION and is not decided here. It would not clear the file "
        "in any case: ``probe_receiver_request`` declares T = {off, on} and a "
        "declaration is admitted or refused as a whole, so the 'on' setting's "
        "blocks reach the same row.",
    ),
    (
        "any replacement for ``operator_tolerance`` in the golden file's request "
        "builder",
        "The field is GONE at 1.0.0, replaced by ``lattice_exponent`` "
        "(sec:inputs; SCOPE_MARKS_1_0_0 of group PR-Q). That is a signature "
        "change in the consuming module and its repair is run B's edit to the "
        "test, not a frozen value. It is recorded in freeze/retarget_plan.md "
        "because it makes two of this file's eight functions fail for a reason "
        "that has nothing to do with dyadic data.",
    ),
)

OBSTRUCTIONS_RP_X: tuple[DyadicObstruction, ...] = (RPX_1, RPX_2)
DARK_COUNT_CASES_RP_X: tuple[DyadicDarkCountCase, ...] = (RPX_3,)


#: THE ONE LINE the consumption mark below is made under.
CONSUMPTION_MARK_AUTHORITY_RP_X: str = (
    "Driver decision DR-S2-2, taken on the Stage 2 fix band's "
    "raised item 1. RPX-3 is DERIVED AND CORRECT AND IS NOT ADOPTED. The "
    "freezer's retarget plan made its adoption conditional -- 'IF the driver "
    "adopts RPX-3's dyadic detector layer' -- and the driver ruled it out."
)

#: WHAT THIS GROUP FREEZES THAT NO TEST READS, AND ON WHOSE AUTHORITY.
#: A list beside the entries, never a field inside one. NOT ONE VALUE OF RPX-3
#: IS EDITED OR DELETED BY THIS MARK: the case stays byte-for-byte as run A
#: derived it, and the mark records only that nothing consumes it and why.
NOT_CONSUMED_AND_WHY_RP_X: tuple[tuple[str, str, str], ...] = (
    (
        "RPX-3 in its entirety: the dyadic per-port dark counts (3/32, 3/16), "
        "the raw matrix, the four unit column sums, min_entry, monotone, "
        "r_min = 9/512 and r_min_before = 1/50",
        "derived-not-consumed",
        "DRIVER DECISION DR-S2-2 (see "
        "CONSUMPTION_MARK_AUTHORITY_RP_X). WHAT ADOPTING IT WOULD HAVE BOUGHT: "
        "tests/golden/test_receiver_povm_docking.py's "
        "`test_the_four_things_the_consumer_s_types_cannot_carry` asserts "
        "`artifact.dark_count_channel.r_min == pytest.approx(0.02)`, and at "
        "RPX-3's detector layer that becomes `== Fraction(9, 512)` EXACTLY, "
        "the `approx` going with it -- nothing about the value being "
        "approximate once the inputs are exactly representable. WHY IT IS NOT "
        "TAKEN: the layer is declared in "
        "tests/support/receiver_povm_support.py's `probe_receiver_request`, "
        "which is SHARED BY FOUR GOLDEN FILES -- the docking file plus "
        "test_receiver_povm_artifact_against_registry.py, "
        "test_receiver_povm_exact_window_against_registry.py and the residual5 "
        "and residual6 files -- and THREE OF THEM ASSERT FROZEN BAND-1 "
        "receiver-povm VALUES derived at (1/10, 1/5). Moving the fixture would "
        "move frozen values in a module this band does not open, which the "
        "two-instance freeze forbids. The "
        "case is therefore kept as evidence that the dyadic layer EXISTS and "
        "what it gives, and its adoption is a receiver-povm band's to make.",
    ),
)
