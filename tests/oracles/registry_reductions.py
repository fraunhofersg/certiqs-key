"""The ``proof-reductions`` oracle registry -- hand-derived golden values.

The implementation bands run under the freeze rule ("the oracle set is frozen
before the solver is written"), in two instances each. **This file is run A's
output, in TWO BANDS.**

**Band 1, contract 0.1.3.** Everything above the ``Group PR-O``
banner. Every value there was derived BY HAND from the accepted ``contract.tex``
0.1.3 before any implementation existed.

**Band 2, the 0.1.3-to-0.2.0 amendment.** Everything from the
``Group PR-O`` banner to the ``Group PR-P`` banner, plus the ``superseded_by``
marks on six 0.1.3 cases and the ``SUPERSESSIONS`` table. Every value there was
derived BY HAND from the accepted ``contract.tex`` **0.2.0** (sha256
b4df5d8c07fd425288db279472d7f9caea1d0e31b1faeee9fb5d3dba2cf183e4) before any
code changed.

**Band 3, the 0.2.0-to-0.3.0 amendment.** Everything from the
``Group PR-P`` banner onward, and the ``SUPERSESSIONS_0_3_0`` table. Every value
there was derived BY HAND from the accepted ``contract.tex`` **0.3.0** (sha256
144e8f9aa1b8eccafdd1a2241fbc27afccc81df13739e0d6cd955b4aa8007f3b) before any
code changed.
BAND 3 IS SMALL BECAUSE THE AMENDMENT IS: ONE fail-closed row and ONE refusal
reason string (``dark_counts_not_column_stochastic``, rows 24 -> 25, reasons
26 -> 27), two version pins re-pointed (``receiver-povm`` 0.1.3 -> 0.2.0 and
``meat-core`` 0.4.0 -> 0.5.0), and prose. NOT ONE FROZEN NUMBER MOVES: "No
claim is added, none is removed, and no claim statement, constant, construction
or emitted number changes" (``sec:amendment030``). The single emitted VALUE that
moves is ``mathematical_spec_version``, and only because the convention writes
it as ``proof-reductions@<contract_version>``.

In both bands, run B (a different implementer instance) writes or changes the
code against these values and may read but not modify them. An expected value
that turns out to be wrong is a FINDING, reported and corrected deliberately
with its derivation, never edited in passing to make a test green.

**BAND 2 DELETES AND EDITS NOTHING FROZEN BY BAND 1.** What the amendment
invalidates is MARKED -- on the case through ``superseded_by`` where the case is
a dataclass instance, and in ``SUPERSESSIONS`` for every marked symbol including
the module-level tuples that have no instance to mark. Twelve symbols are
marked; ``NOT_SUPERSEDED_AND_WHY`` records what is deliberately left unmarked
and why. Run B retires or rewrites each marked case deliberately.

WHY A SIBLING FILE AND NOT A NEW GROUP IN ``registry.py``
========================================================
``registry.py`` is "the ``meat-core`` oracle registry" and its integrity test
binds every entry's ``claims`` to ``meat-core``'s C1-C20;
``registry_statistics_acceptance.py`` and ``registry_protocol_compiler.py`` are
the same construction for SA1-SA9 and PC1-PC12. The claims pinned here are
PR1-PR12 of a FOURTH module at its own contract version, resolving in
``docs/mathematical-contracts/proof-reductions/interface.yaml``. So this is a
PURE INSERTION: a new module beside the others, none of which is edited by so
much as a byte. ``KINDS`` and ``INADMISSIBLE_SOURCES`` are IMPORTED from
``registry.py`` rather than restated, so the registries cannot drift on what an
admissible oracle is.

THE NUMERIC REPRESENTATION, AND WHY
===================================
**Exact Gaussian rationals.** Every scalar is a ``fractions.Fraction`` and every
matrix entry is an exact pair ``(Fraction real, Fraction imaginary)``. No float
appears anywhere in this file. Four reasons, and they are the whole rationale:

1. THE CONTRACT'S OWN CHARACTERIZATION OF ITSELF. Section 1.4 states that this
   module "states no claim whose PROOF depends on a floating-point computation:
   every statement below is AN OPERATOR IDENTITY OR INEQUALITY BETWEEN EXACTLY
   DECLARED QUANTITIES, and the places a number is compared against a threshold
   -- the total weight ``p < 1``, the per-outcome weights ``p_v >= 0`` -- are
   REFUSAL TESTS, NOT BOUNDS". Exact rationals are the faithful representation
   of "exactly declared"; a tolerance would turn a decidable refusal test into
   an approximate one and would decide, in this file, something the contract
   leaves to code.
2. THE ONE ARITHMETIC EVALUATION IS EXACT IN THIS REPRESENTATION.
   Eq. ``eq:weightroute`` forms ``p_(y_i,t) = q_t((1 - r_min,i) p_i + r_min,i)``
   from declared data; over the Fractions every instance below evaluates
   exactly, so the ROUNDING RULE Section 1.4 states -- "if ``receiver-povm`` ever
   emits an exact or interval evaluation, this module must round ``p_(y_i,t)``
   TOWARD ZERO" -- is never engaged by a frozen value, and the direction is
   recorded in ``ROUNDING_RULE`` below rather than exercised.
3. COMPLEX ENTRIES ARE UNAVOIDABLE AND ARE THE POINT IN ONE PLACE. The
   adjoint convention Eq. ``eq:pairing`` and the uniqueness statement of Lemma
   ``lem:statistics`` are statements about Hermitian operators, not symmetric
   ones, and an implementation that conflated the two would pass every real
   instance. ``WP3`` below is therefore genuinely complex: its transported
   operator ``O_OFF`` pulls back to a matrix with entries ``-+ 7i/25`` under one
   realizing channel and to ZERO under another. Rank-one objects are frozen as
   PROJECTORS or as EXACT GAUSSIAN-RATIONAL UNIT VECTORS built from the
   Pythagorean triple (3, 4, 5), so no amplitude ``1/sqrt(2)`` ever appears.
4. ONE IRRATIONAL NUMBER OCCURS IN THE CONTRACT AND IS HANDLED WITHOUT
   DEPARTING FROM THE REPRESENTATION. Proposition ``prop:obstruction`` names
   ``p_* = (1 - 1/sqrt2)/2``. It is frozen by its EXACT MINIMAL POLYNOMIAL --
   the smaller root of ``lambda^2 - lambda + 1/8``, i.e. by the rational trace
   and determinant of ``M_1 + M_2`` -- together with a RATIONAL WITNESS
   ``1/8 < p_*`` whose positive-semidefiniteness certificate is exact
   (``tr = 3/4 > 0``, ``det = 1/64 > 0``). The obstruction proof uses only
   ``p_* > 0``, so either value drives the contradiction; see ``PR_OBSTRUCTION``.

NON-DYADIC WEIGHTS, ON PURPOSE. Weights are fixture choices: the contract
requires only ``p_v >= 0`` and ``p = sum_v p_v < 1``. Several instances use
DELIBERATELY NON-DYADIC values -- ``2/3`` and ``1/3`` for the preserved blocks of
``WP3``, ``q_t = (2/3, 1/3)``, ``p = 5/9`` in ``PROBE22``, ``r_min = 1/20`` and
``29/200`` in ``RC2`` -- so that run B's exact-to-machine conversion boundary is
forced into the open rather than hidden behind fixtures that happen to convert
without loss.

THE CODE'S SUBSTRATE IS NOT DECIDED HERE. ``interface.yaml`` records
``numeric_substrate: null`` as open implementation choice 1 of 10: the contract
fixes no numeric type, no tolerance and no rounding rule for any emitted matrix,
and carries no exactness or interval-arithmetic assumption. The choice above is
a choice about THE EVIDENCE, made so that a frozen value is checkable on paper;
run B chooses the code's substrate.

ADMISSIBILITY (ADR-0003)
========================
No MATLAB, OpenQKDSecurity, CVX, MOSEK or Julia value is admissible and none is
used; the guard is asserted against ``INADMISSIBLE_SOURCES``. Every number below
is an exact closed form or a hand-computed rational. THE ONLY MATHEMATICAL
SOURCES ARE ``contract.tex`` 0.1.3 at sha256
ad19d127bf06b5890f6808a356bc65cdc206199cc163b1518ab086b61429214b (band 1) and
``contract.tex`` 0.2.0 at sha256
b4df5d8c07fd425288db279472d7f9caea1d0e31b1faeee9fb5d3dba2cf183e4 (band 2) and
``contract.tex`` 0.3.0 at sha256
144e8f9aa1b8eccafdd1a2241fbc27afccc81df13739e0d6cd955b4aa8007f3b (band 3).
Each version SUPERSEDES the one before it, which is why earlier values are
MARKED rather than re-derived: each was correct against the contract that was
accepted when it was frozen, and the mark records what the amendment changed.

WHAT THIS REGISTRY DOES NOT DO
==============================
**It does not certify anything.** ``ASSURANCE`` below is the ORACLE's own
evidential status and is ``estimate`` for every entry. Section 1.4 of the
contract says why in its own words: eligibility is "A CEILING, NOT A LABEL", and
ARCHITECTURE_SPEC.md Section 3.5 "makes every result ``estimate`` until the
runtime certificate checks pass". Agreement with an oracle is not one of those
checks.

**It does not implement the module, and it does not import it.** No function
here squashes a POVM, composes a channel, validates a declaration or emits an
artifact. Every frozen field is a LITERAL; the only computation is the exact
arithmetic that assembles a literal from integers a reader can check (``gz``,
``real_matrix``, ``diag_matrix``), which widens a rational to a Gaussian pair and
assembles a tuple of tuples. It imports no part of the package it pins.

REFUSAL-REASON SPELLINGS ARE THE CONTRACT'S, VERBATIM
=====================================================
Unlike its sibling modules, THIS contract fixes every refusal-reason string.
At 0.1.3, ``sec:failclosed``'s two tables named TWENTY-FOUR of them across
TWENTY-ONE rows; at 0.2.0 its FOUR tables name TWENTY-SIX across TWENTY-FOUR;
at 0.3.0 its FIVE tables name TWENTY-SEVEN across TWENTY-FIVE. LaTeX sets each
with an escaped underscore and an allowbreak between words, purely for line
breaking; the machine string is the underscore-joined identifier without the
allowbreaks. The twenty-four are frozen in ``REFUSAL_REASONS`` (marked
superseded), the twenty-six in ``REFUSAL_REASONS_0_2_0`` (marked superseded at
0.3.0) and the twenty-seven in ``REFUSAL_REASONS_0_3_0``, with the added strings
in ``REFUSAL_REASONS_ADDED_0_2_0`` and ``REFUSAL_REASONS_ADDED_0_3_0``; every
0.1.3 string has at least one case in ``REFUSAL_CASES``, the 0.2.0 rows have
cases in ``TOL_ROW_CASES``, ``SLOT_VALIDATION_CASES``, ``TOL_SCOPE_CASES``,
``BRANCH_PROBE_WEIGHT_CASES`` and ``TOL_ENTRY_OUTSIDE_FORM``, and the 0.3.0 row
has cases in ``COLSTOCH_CASES``. At 0.2.0, THREE ROWS WERE ADDED AND ONLY TWO
STRINGS -- the licensed-route Hermiticity row is emitted under the existing
``constraint_without_certificate``; at 0.3.0 ONE ROW AND ONE STRING were added,
which is a coincidence and not a rule. NO TWENTY-EIGHTH STRING IS INVENTED
ANYWHERE.

**FOUR MACHINE STRINGS IN THE 0.3.0 TEXT ARE NOT THIS MODULE'S**, and a naive
sweep of the contract's ``texttt`` tokens would put the count at thirty-one.
``bob_povm_not_evaluable``, ``declared_operator_tolerance_open``,
``key_length`` and ``key_length_claim`` are ``meat-core`` 0.5.0's vocabulary,
quoted inside Remark ``rem:consumerdisposition`` and the ``target_povm`` row
while stating what the CONSUMER does with what this module emits. They are
frozen as a NEGATIVE list, ``CONSUMER_STRINGS_NOT_OURS_0_3_0``, so the exclusion
is checked rather than remembered.

WHAT IS PINNED, BY GROUP
========================
PR-A  PR1  the WP3 relation: exact Kraus operators from a 3-dimensional source
           to a flag-extended target, the pulled-back M = Lambda+(F), statistics
           equality on four inputs and two side-system pairings, and the
           uniqueness of the adjoint on the carried span with an operator off it
           where two realizing channels disagree
PR-B  PR2  the one-round measurement-factorizing transfer: the physical and the
           squashed run, output-state entry by entry
PR-C  PR3  one sound transported constraint of each certificate type, the
           intersection of sound families, the reachable state a constraint
           excludes, and the UNSOUND operator-form transplant of rem:unsound
PR-D  PR4  post-processing by a column-stochastic matrix; the joint alphabet
           with a private setting; pinching; and both legs of lem:obstructions,
           each with a refusing and a passing instance
PR-E  PR5  the two-branch instrument, the branch-weight constraint in both its
           operator and its scalar form, and the flag PVM as top element
PR-F  PR6  the FSS and multi-bound WPFSS targets, the transported cutoff
           projectors, the chain M <= F^WP <= F^FSS <= P^flag with exact
           composition, the encoded constraint, the reverse-relation failure,
           the p = 1 refusal with rem:peqone, rem:weightfree, and eq:two-sector-entry
PR-G  PR7  flags are enough on the zero-weight block, with two different source
           POVMs covered by one target
PR-H  PR8  the register-conditioned mixture with a non-projective register POVM,
           and the branch weights transported as OPERATORS
PR-I  PR9  the composed blinding squasher at |Blmode| = 2 and |Blmode| = 3: the
           emitted UNPADDED dimension, the sector set, per-sector dimensions,
           sector-block-diagonality, the party partition, and the degenerate
           no-blinding declaration
PR-J  PR10 the event-bound obstruction, frozen with its numbers
PR-K  PR11 licence entries typed for BOTH source modes, the adjoint-form
           admissible sets, the per-entry certificate, a composite attack landing
           in the set, and the cross-channel pairing at its tight end
PR-L  PR12 typed link records field for field for the six implemented kinds, a
           composed chain, and AT LEAST ONE REFUSAL CASE FOR EVERY ROW OF THE
           FAIL-CLOSED TABLE
PR-M  the receiver-artifact consumption path: RC2, RC1MIN, RC3, RCABS and the
           descent counterexample
PR-N  the interface vocabulary as frozen tuples, and the assumption ledger

PR-P  (BAND 3) the column-stochasticity row of contract 0.3.0: the raw declared
           R over 2^[K] with both subrules decided exactly, two honest anchors
           (one with a fibre of size two, so the descent implication is not a
           relabelling), the contract's own defect example -- columns summing to
           1 only within a rounding error -- and BOTH HALVES of the boundary
           Remark rem:darkcompose draws between this row and the descent row
           beside it

PR-O  PR13 (BAND 2) the declared operator tolerance: the exact substrate and the
           principal-minor predicate with three discriminators against the tests
           an implementation would substitute; the four rows of prop:tolrows as
           admit/refuse pairs at eps_op = 1/100 and eps_op = 0; A-OPTOL scope
           over the three declared operator families; the emitted constants of
           cor:tolentries (i)-(iv) frozen at BOTH tolerances, with the operator
           outside eq:tolgeneral form refused; eq:targetposcomp three amounts;
           the operator_tolerance_record and its null; the exact identity
           eq:branchprobeweight at every eps_op; the high-photon slot row with
           its masked negative; CR-1 carried-operator count; CR-B1 y-fastest
           order at the wpfss_data site; and the 0.2.0 vocabulary

CHANGE-REQUEST CANDIDATES: see ``CHANGE_REQUEST_CANDIDATES`` (band 1),
``CHANGE_REQUEST_CANDIDATES_0_2_0`` (band 2) and
``CHANGE_REQUEST_CANDIDATES_0_3_0`` (band 3) at the end of this module, each
naming the item, the reading taken, and whether it is routed. Band 1 cleared
nine by reading and routed one (CR-1, which the 0.2.0 amendment then closed).
Band 2 cleared six by reading and ROUTED ONE: the pinned supplier version, which
contract.tex 0.2.0 still named as ``receiver-povm 0.1.3`` while that module was
itself accepted at 0.2.0. THE 0.3.0 AMENDMENT CLOSED IT, and closed band 2's
consumer-boundary item with it. Band 3 clears five by reading and ROUTES ONE,
which is not a gap in the contract at all: the two hard-coded version strings in
earlier reductions package that the accepted 0.3.0
makes stale, reported to the driver because run A writes no source file.

THE REGISTRY IS PARTITIONED, AND THE BLINDING HALF IS A FILE OF ITS OWN
=======================================================================
``registry_reductions_blinding.py`` carries group PR-I -- the composed blinding
model -- and the one entry of ``PR_ORACLES`` that cites one of its values. The
cut is textual and no value moved, changed or was recomputed. The dependency
runs ONE WAY: that file imports the exact helpers and the entry record from
here, and nothing here names anything there, so deleting the blinding submodule
and its tests leaves this registry standing whole.

:data:`ORIGINAL_REGISTRY_NAMES` is the original ``__all__``, carried
here unchanged, and the partition test asserts that the two modules' public
names are disjoint and that their union is exactly it.

THE FILE IS NEVER REGENERATED
=============================
A frozen registry "moves with its module and is NEVER REGENERATED FROM THE CODE
IT TESTS" (PRINCIPLES.md section 2.3). No number, case, supersession mark or
oracle entry of it is recomputed or edited. The one structural edit is **THE
CUT** that produced ``registry_reductions_blinding.py``, described above: a
textual split, plus the two accessors it needed.

Four frozen module-level values -- :data:`CHANGE_REQUEST_CANDIDATES`,
:data:`CHANGE_REQUEST_CANDIDATES_0_3_0`,
:data:`CHANGE_REQUEST_CANDIDATES_1_0_0` and :data:`TWO_INSTANCE_FREEZE_PR_R` --
are a frozen record of what a run in ANOTHER REPOSITORY read and did, so the
package paths they name are those of that repository and not paths of this one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as F

from registry import INADMISSIBLE_SOURCES, KINDS

__all__ = [
    "ASSUMPTION_LEDGER",
    "ASSUMPTION_LEDGER_0_2_0",
    "ASSUMPTION_LEDGER_0_3_0",
    "ASSUMPTION_ROW_OPTOL",
    "ASSURANCE",
    "BLK_GT_V0",
    "BLK_GT_V1",
    "BRANCH_MIXTURE",
    "BRANCH_PROBE_WEIGHT_CASES",
    "CARRIED_DEFAULT_COUNT_CASES",
    "CARRIED_DEFAULT_SET",
    "CERTIFICATE_CASES",
    "CERTIFICATE_KINDS",
    "CERT_IDENTITY_PROBE",
    "CERT_POSITIVITY",
    "CERT_SPECTRAL",
    "CERT_TWO_SECTOR",
    "CHAIN_CASES",
    "CHAIN_LADDER",
    "CHAIN_WELL_FORMED",
    "CHANGE_REQUEST_CANDIDATES",
    "CHANGE_REQUEST_CANDIDATES_0_2_0",
    "CHANGE_REQUEST_CANDIDATES_0_3_0",
    "CLAIM_IDS_0_2_0",
    "CLAIM_IDS_0_3_0",
    "COLSTOCH_CANONICAL_ADMIT",
    "COLSTOCH_CASES",
    "COLSTOCH_CG_CANONICAL",
    "COLSTOCH_CG_MERGING",
    "COLSTOCH_COARSE_ADMIT",
    "COLSTOCH_COLSUM_REFUSE",
    "COLSTOCH_NEGATIVE_VACUOUS_REFUSE",
    "COLSTOCH_POSITIVE_FORBIDDEN_REFUSE",
    "COLSTOCH_PROBE_WEIGHTS",
    "COLSTOCH_SLOT_WEIGHT",
    "COLSTOCH_TOLERANCE_PROBE",
    "COLSTOCH_TOLERANCE_PROBE_NOTE",
    "COMPOSITE_ATTACK_CASE",
    "CONSUMER_PIN_0_2_0",
    "CONSUMER_PIN_0_3_0",
    "CONSUMER_STRINGS_NOT_OURS_0_3_0",
    "CONVENTIONS",
    "CONVENTIONS_0_2_0",
    "CONVENTIONS_0_3_0",
    "DESCENT_COUNTEREXAMPLE",
    "ENCODED_CONSTRAINT",
    "EXACT_ARITHMETIC_NEIGHBOURING_ROWS_0_3_0",
    "FAIL_CLOSED_ROWS_ADDED_0_2_0",
    "FAIL_CLOSED_ROWS_ADDED_0_3_0",
    "FAIL_CLOSED_ROW_COUNT_0_2_0",
    "FAIL_CLOSED_ROW_COUNT_0_3_0",
    "FAIL_CLOSED_TABULAR_COUNT_0_2_0",
    "FAIL_CLOSED_TABULAR_COUNT_0_3_0",
    "FLAGS_ENOUGH",
    "INADMISSIBLE_SOURCES",
    "INPUT_KEYS",
    "INPUT_KEYS_0_2_0",
    "INPUT_KEYS_0_3_0",
    "INTERSECTION_CASE",
    "KINDS",
    "LICENCE_CASES",
    "LICENCE_PROBE_IDENTITY",
    "LICENCE_TRUSTED",
    "LICENCE_UNTRUSTED",
    "LINK_FLAGS_ENOUGH",
    "LINK_FSS",
    "LINK_IDENTITY",
    "LINK_KINDS",
    "LINK_KINDS_DEFERRED",
    "LINK_KINDS_IMPLEMENTED",
    "LINK_PINCHING",
    "LINK_RECORDS",
    "LINK_REGISTER_MIXTURE",
    "LINK_STAGES",
    "LINK_STATUS_EMITTED",
    "LINK_STATUS_VOCABULARY",
    "LINK_WPFSS",
    "MIXTURE_CASE",
    "MIXTURE_N_J0",
    "MIXTURE_N_J1",
    "MIXTURE_SQRT_J0",
    "MIXTURE_SQRT_J1",
    "MP_V0",
    "MP_V1",
    "NEVER_VERIFIED_0_2_0",
    "NEVER_VERIFIED_0_3_0",
    "NOT_EMITTED",
    "NOT_SUPERSEDED_AND_WHY",
    "NOT_SUPERSEDED_AND_WHY_0_3_0",
    "OBSTRUCTION_CASES",
    "OBSTRUCTION_CASES_PR10",
    "OUTPUT_KEYS",
    "OUTPUT_KEYS_0_2_0",
    "OUTPUT_KEYS_0_3_0",
    "O_ID_OFFSPAN",
    "O_OFF",
    "O_OFF_PULLBACK_PRIME",
    "PINCHING_CASE",
    "PI_FLAG_Q",
    "PI_GT_B",
    "PI_LEQ_B",
    "PI_LEQ_Q",
    "POSTPROCESSING_CASE",
    "PROBE22",
    "PROBE22_CONDITIONAL",
    "PROBE22_JOINT",
    "PROBE22_MPRIME",
    "PROBE22_Q",
    "PROBE22_REACHABLE_FLAG",
    "PROBE22_SUM_T0",
    "PROBE22_TARGET",
    "PROBE22_TOTAL_WEIGHT",
    "PROBE22_UNSOUND",
    "PROBE22_V",
    "PROBE22_WEIGHTS",
    "PR_OBSTRUCTION",
    "PR_ORACLES",
    "PSI_0",
    "PSI_1",
    "P_EQUALS_ONE",
    "RC1MIN",
    "RC2",
    "RC3",
    "RCABS",
    "REFUSAL_CASES",
    "REFUSAL_REASONS",
    "REFUSAL_REASONS_0_2_0",
    "REFUSAL_REASONS_0_3_0",
    "REFUSAL_REASONS_ADDED_0_2_0",
    "REFUSAL_REASONS_ADDED_0_3_0",
    "RELATION_CASES",
    "ROUNDING_RULE",
    "ROUTES",
    "SLOT_VALIDATION_CASES",
    "SOURCE_MODES",
    "SPEC_VERSION_0_2_0",
    "SPEC_VERSION_0_3_0",
    "SUBSYSTEM_ORDER_CASE",
    "SUPERSEDED_SYMBOLS",
    "SUPERSEDED_SYMBOLS_0_3_0",
    "SUPERSESSIONS",
    "SUPERSESSIONS_0_3_0",
    "SUPPLIER_PIN_0_2_0",
    "SUPPLIER_PIN_0_3_0",
    "TIGHT",
    "TOL2_BLOCKS",
    "TOL2_BLOCK_Y0_T0",
    "TOL2_BLOCK_Y0_T1",
    "TOL2_BLOCK_Y1_T0",
    "TOL2_BLOCK_Y1_T1",
    "TOL2_BRANCH_FAIL",
    "TOL2_BRANCH_PASS",
    "TOL2_DCF",
    "TOL2_DELTA_T",
    "TOL2_EPS_OP",
    "TOL2_ETA",
    "TOL2_ETA_V",
    "TOL2_JOINT_NB",
    "TOL2_Q",
    "TOL2_RCG",
    "TOL2_ROUTED_WEIGHTS",
    "TOL2_SLOT",
    "TOL2_T",
    "TOL2_TARGETPOSCOMP",
    "TOL2_TILDE",
    "TOL2_TOLERANCE_RECORD",
    "TOL2_TOLERANCE_RECORD_ABSENT",
    "TOL2_TOTAL_WEIGHT",
    "TOL2_V",
    "TOL2_V_T_FASTEST_NOT_THE_CONTRACT_ORDER",
    "TOL2_Y",
    "TOL_ENTRY_CASES",
    "TOL_ENTRY_CLAUSES",
    "TOL_ENTRY_DEFAULT_CARRIED",
    "TOL_ENTRY_FLAG",
    "TOL_ENTRY_OUTSIDE_FORM",
    "TOL_ENTRY_PROBE_T0",
    "TOL_ENTRY_PROBE_T1",
    "TOL_ENTRY_TWO_SECTOR",
    "TOL_FLOAT_SENSITIVE_CASES",
    "TOL_ROW_CASES",
    "TOL_SCOPE_CASES",
    "TOP_ELEMENT",
    "TRANSFER_CASES",
    "TRANSFER_ONE_ROUND",
    "WEIGHT_FREEDOM",
    "WEIGHT_ROUTE_CASES",
    "WP3",
    "WP3_FFSS_V0",
    "WP3_FFSS_V1",
    "WP3_FWP_V0",
    "WP3_FWP_V1",
    "WP3_KRAUS",
    "WP3_KRAUS_ISO",
    "WP3_KRAUS_PRES",
    "WP3_KRAUS_PRIME",
    "WP3_KRAUS_V0",
    "WP3_KRAUS_V1",
    "WP3_M_V0",
    "WP3_M_V1",
    "WP3_RELATION_FSS",
    "WP3_RELATION_PRIME",
    "WP3_RELATION_WP",
    "WP3_STATISTICS",
    "AssumptionRow",
    "BranchProbeWeightCase",
    "CertificateCase",
    "ChainCase",
    "ColumnStochasticCase",
    "Gauss",
    "LicenceCase",
    "LinkRecord",
    "Matrix",
    "ObstructionCase",
    "PROracleEntry",
    "RefusalCase",
    "RelationCase",
    "SlotValidationCase",
    "StatisticsCase",
    "Supersession",
    "ToleranceEntryCase",
    "ToleranceRowCase",
    "ToleranceScopeCase",
    "TransferCase",
    "WeightRouteCase",
    "diag_matrix",
    "gz",
    "pr_oracle",
    "real_matrix",
]

#: The original ``__all__``, carried WHOLE. It is a list of
#: NAMES and not of oracle values, and it is what the partition test
#: compares the union of the two registry modules against.
ORIGINAL_REGISTRY_NAMES = [
    "ASSUMPTION_LEDGER",
    "ASSUMPTION_LEDGER_0_2_0",
    "ASSUMPTION_LEDGER_0_3_0",
    "ASSUMPTION_ROW_OPTOL",
    "ASSURANCE",
    "BLIND2",
    "BLIND2_ABOVE_CUTOFF",
    "BLIND2_F_A",
    "BLIND2_F_B",
    "BLIND2_MPRIME",
    "BLIND2_M_A",
    "BLIND2_M_B",
    "BLIND2_M_BL1_A",
    "BLIND2_M_BL1_B",
    "BLIND2_N_BL1",
    "BLIND2_N_NB",
    "BLIND2_PRESERVED",
    "BLIND2_TOTAL_WEIGHT",
    "BLIND2_TRANSPORT",
    "BLIND2_WEIGHTS",
    "BLIND3_SHAPE",
    "BLINDING_DIMENSION_CASES",
    "BLK_GT_V0",
    "BLK_GT_V1",
    "BRANCH_MIXTURE",
    "BRANCH_PROBE_WEIGHT_CASES",
    "CARRIED_DEFAULT_COUNT_CASES",
    "CARRIED_DEFAULT_SET",
    "CERTIFICATE_CASES",
    "CERTIFICATE_KINDS",
    "CERT_TWO_SECTOR",
    "CERT_IDENTITY_PROBE",
    "CERT_POSITIVITY",
    "CERT_SPECTRAL",
    "CHAIN_CASES",
    "CHAIN_LADDER",
    "CHAIN_WELL_FORMED",
    "CHANGE_REQUEST_CANDIDATES",
    "CHANGE_REQUEST_CANDIDATES_0_2_0",
    "CHANGE_REQUEST_CANDIDATES_0_3_0",
    "CLAIM_IDS_0_2_0",
    "CLAIM_IDS_0_3_0",
    "COLSTOCH_CANONICAL_ADMIT",
    "COLSTOCH_CASES",
    "COLSTOCH_CG_CANONICAL",
    "COLSTOCH_CG_MERGING",
    "COLSTOCH_COARSE_ADMIT",
    "COLSTOCH_COLSUM_REFUSE",
    "COLSTOCH_NEGATIVE_VACUOUS_REFUSE",
    "COLSTOCH_POSITIVE_FORBIDDEN_REFUSE",
    "COLSTOCH_PROBE_WEIGHTS",
    "COLSTOCH_SLOT_WEIGHT",
    "COLSTOCH_TOLERANCE_PROBE",
    "COLSTOCH_TOLERANCE_PROBE_NOTE",
    "COMPOSITE_ATTACK_CASE",
    "CONSUMER_PIN_0_2_0",
    "CONSUMER_PIN_0_3_0",
    "CONSUMER_STRINGS_NOT_OURS_0_3_0",
    "CONVENTIONS",
    "CONVENTIONS_0_2_0",
    "CONVENTIONS_0_3_0",
    "DESCENT_COUNTEREXAMPLE",
    "ENCODED_CONSTRAINT",
    "EXACT_ARITHMETIC_NEIGHBOURING_ROWS_0_3_0",
    "FAIL_CLOSED_ROWS_ADDED_0_2_0",
    "FAIL_CLOSED_ROWS_ADDED_0_3_0",
    "FAIL_CLOSED_ROW_COUNT_0_2_0",
    "FAIL_CLOSED_ROW_COUNT_0_3_0",
    "FAIL_CLOSED_TABULAR_COUNT_0_2_0",
    "FAIL_CLOSED_TABULAR_COUNT_0_3_0",
    "FLAGS_ENOUGH",
    "INADMISSIBLE_SOURCES",
    "INPUT_KEYS",
    "INPUT_KEYS_0_2_0",
    "INPUT_KEYS_0_3_0",
    "INTERSECTION_CASE",
    "KINDS",
    "LICENCE_CASES",
    "LICENCE_PROBE_IDENTITY",
    "LICENCE_TRUSTED",
    "LICENCE_UNTRUSTED",
    "LINK_FLAGS_ENOUGH",
    "LINK_FSS",
    "LINK_IDENTITY",
    "LINK_KINDS",
    "LINK_KINDS_DEFERRED",
    "LINK_KINDS_IMPLEMENTED",
    "LINK_PINCHING",
    "LINK_RECORDS",
    "LINK_REGISTER_MIXTURE",
    "LINK_STAGES",
    "LINK_STATUS_EMITTED",
    "LINK_STATUS_VOCABULARY",
    "LINK_WPFSS",
    "MIXTURE_CASE",
    "MIXTURE_N_J0",
    "MIXTURE_N_J1",
    "MIXTURE_SQRT_J0",
    "MIXTURE_SQRT_J1",
    "MP_V0",
    "MP_V1",
    "NEVER_VERIFIED_0_2_0",
    "NEVER_VERIFIED_0_3_0",
    "NOT_EMITTED",
    "NOT_SUPERSEDED_AND_WHY",
    "NOT_SUPERSEDED_AND_WHY_0_3_0",
    "NO_BLINDING_CASE",
    "OBSTRUCTION_CASES",
    "OBSTRUCTION_CASES_PR10",
    "OUTPUT_KEYS",
    "OUTPUT_KEYS_0_2_0",
    "OUTPUT_KEYS_0_3_0",
    "O_ID_OFFSPAN",
    "O_OFF",
    "O_OFF_PULLBACK_PRIME",
    "PINCHING_CASE",
    "PI_FLAG_Q",
    "PI_GT_B",
    "PI_LEQ_B",
    "PI_LEQ_Q",
    "POSTPROCESSING_CASE",
    "PROBE22",
    "PROBE22_CONDITIONAL",
    "PROBE22_JOINT",
    "PROBE22_MPRIME",
    "PROBE22_Q",
    "PROBE22_REACHABLE_FLAG",
    "PROBE22_SUM_T0",
    "PROBE22_TARGET",
    "PROBE22_TOTAL_WEIGHT",
    "PROBE22_UNSOUND",
    "PROBE22_V",
    "PROBE22_WEIGHTS",
    "PR_OBSTRUCTION",
    "PR_ORACLES",
    "PSI_0",
    "PSI_1",
    "P_EQUALS_ONE",
    "RC1MIN",
    "RC2",
    "RC3",
    "RCABS",
    "REFUSAL_CASES",
    "REFUSAL_REASONS",
    "REFUSAL_REASONS_0_2_0",
    "REFUSAL_REASONS_0_3_0",
    "REFUSAL_REASONS_ADDED_0_2_0",
    "REFUSAL_REASONS_ADDED_0_3_0",
    "RELATION_CASES",
    "ROUNDING_RULE",
    "ROUTES",
    "SLOT_VALIDATION_CASES",
    "SOURCE_MODES",
    "SPEC_VERSION_0_2_0",
    "SPEC_VERSION_0_3_0",
    "SUBSYSTEM_ORDER_CASE",
    "SUPERSEDED_SYMBOLS",
    "SUPERSEDED_SYMBOLS_0_3_0",
    "SUPERSESSIONS",
    "SUPERSESSIONS_0_3_0",
    "SUPPLIER_PIN_0_2_0",
    "SUPPLIER_PIN_0_3_0",
    "TIGHT",
    "TOL2_BLOCKS",
    "TOL2_BLOCK_Y0_T0",
    "TOL2_BLOCK_Y0_T1",
    "TOL2_BLOCK_Y1_T0",
    "TOL2_BLOCK_Y1_T1",
    "TOL2_BRANCH_FAIL",
    "TOL2_BRANCH_PASS",
    "TOL2_DCF",
    "TOL2_DELTA_T",
    "TOL2_EPS_OP",
    "TOL2_ETA",
    "TOL2_ETA_V",
    "TOL2_JOINT_NB",
    "TOL2_Q",
    "TOL2_RCG",
    "TOL2_ROUTED_WEIGHTS",
    "TOL2_SLOT",
    "TOL2_T",
    "TOL2_TARGETPOSCOMP",
    "TOL2_TILDE",
    "TOL2_TOLERANCE_RECORD",
    "TOL2_TOLERANCE_RECORD_ABSENT",
    "TOL2_TOTAL_WEIGHT",
    "TOL2_V",
    "TOL2_V_T_FASTEST_NOT_THE_CONTRACT_ORDER",
    "TOL2_Y",
    "TOL_ENTRY_CASES",
    "TOL_ENTRY_CLAUSES",
    "TOL_ENTRY_DEFAULT_CARRIED",
    "TOL_ENTRY_TWO_SECTOR",
    "TOL_ENTRY_FLAG",
    "TOL_ENTRY_OUTSIDE_FORM",
    "TOL_ENTRY_PROBE_T0",
    "TOL_ENTRY_PROBE_T1",
    "TOL_FLOAT_SENSITIVE_CASES",
    "TOL_ROW_CASES",
    "TOL_SCOPE_CASES",
    "TOP_ELEMENT",
    "TRANSFER_CASES",
    "TRANSFER_ONE_ROUND",
    "WEIGHT_FREEDOM",
    "WEIGHT_ROUTE_CASES",
    "WP3",
    "WP3_FFSS_V0",
    "WP3_FFSS_V1",
    "WP3_FWP_V0",
    "WP3_FWP_V1",
    "WP3_KRAUS",
    "WP3_KRAUS_ISO",
    "WP3_KRAUS_PRES",
    "WP3_KRAUS_PRIME",
    "WP3_KRAUS_V0",
    "WP3_KRAUS_V1",
    "WP3_M_V0",
    "WP3_M_V1",
    "WP3_RELATION_FSS",
    "WP3_RELATION_PRIME",
    "WP3_RELATION_WP",
    "WP3_STATISTICS",
    "AssumptionRow",
    "BlindingShape",
    "BranchProbeWeightCase",
    "CertificateCase",
    "ChainCase",
    "ColumnStochasticCase",
    "Gauss",
    "LicenceCase",
    "LinkRecord",
    "Matrix",
    "ObstructionCase",
    "PROracleEntry",
    "RefusalCase",
    "RelationCase",
    "SlotValidationCase",
    "StatisticsCase",
    "Supersession",
    "ToleranceEntryCase",
    "ToleranceRowCase",
    "ToleranceScopeCase",
    "TransferCase",
    "WeightRouteCase",
    "diag_matrix",
    "gz",
    "pr_oracle",
    "real_matrix",
]

#: The ORACLE's own evidential tier. ``estimate`` for every entry: contract
#: Section 1.4 makes eligibility "a ceiling, not a label", and
#: ARCHITECTURE_SPEC.md Section 3.5 keeps every result ``estimate`` until the
#: runtime certificate checks pass. Agreement here is not one of those checks.
ASSURANCE = "estimate"


# ===========================================================================
#  Exact Gaussian-rational representation
# ===========================================================================
#
#  A scalar is a Fraction. A matrix entry is the pair (real, imaginary), each a
#  Fraction. ``gz``, ``real_matrix`` and ``diag_matrix`` are NOTATION, not
#  computation: they widen a rational to a Gaussian pair and assemble a tuple of
#  tuples. Nothing in this file multiplies, inverts or diagonalizes a matrix.

Gauss = tuple[F, F]
Matrix = tuple[tuple[Gauss, ...], ...]


def gz(re: int | F = 0, im: int | F = 0) -> Gauss:
    """Return one Gaussian-rational scalar as the exact pair (real, imag)."""
    return (F(re), F(im))


def real_matrix(rows: tuple[tuple[int | F, ...], ...]) -> Matrix:
    """Assemble a Gaussian-rational matrix all of whose entries are real."""
    return tuple(tuple(gz(value) for value in row) for row in rows)


def diag_matrix(values: tuple[int | F, ...]) -> Matrix:
    """Assemble a real diagonal Gaussian-rational matrix from its diagonal."""
    n = len(values)
    return tuple(
        tuple(gz(values[i]) if i == j else gz(0) for j in range(n)) for i in range(n)
    )


@dataclass(frozen=True)
class PROracleEntry:
    """One frozen expected value with the derivation that produced it.

    The field set mirrors ``registry.OracleEntry`` and its siblings; the
    alpha-dependent fields are dropped. Contract Section 2.5 records
    ``alpha_domain: (1, 2)`` as an INTERSECTION ALONG THE CHAIN and states that
    this contract "states no Renyi quantity and imports no alpha-dependent
    fact", so no entry here depends on the Renyi order.
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


def pr_oracle(oracle_id: str) -> PROracleEntry:
    """Return the registry entry with the given ``oracle_id``."""
    for entry in PR_ORACLES:
        if entry.oracle_id == oracle_id:
            return entry
    raise KeyError(f"no oracle entry {oracle_id!r}")


# ===========================================================================
#  Interface vocabulary, frozen from contract.tex Section 2 (Group PR-N)
# ===========================================================================

#: Section 2.1, three groups: 7 + 5 + 4. Order is the contract's own.
INPUT_KEYS: tuple[str, ...] = (
    "receiver_artifact",
    "photon_blocks",
    "high_photon_bounds",
    "bound_quantifier_domain",
    "dark_count_channel",
    "outcome_coarse_graining",
    "bound_evaluation",
    "probe_declaration",
    "detection_alphabet",
    "photon_cutoff",
    "blinding_model",
    "source_mode",
    "link_declarations",
    "route",
    "carried_operators",
    "requested_assurance",
)

#: Section 2.3, two tabulars: 8 + 9.
OUTPUT_KEYS: tuple[str, ...] = (
    "source_descriptor",
    "target_descriptor",
    "target_povm",
    "outcome_correspondence",
    "squashing_channel",
    "exact_identity",
    "transported_operators",
    "reachable_set_statement",
    "constraint_list",
    "attack_set_license",
    "wpfss_data",
    "douglas_data",
    "reduction_chain",
    "status",
    "verification_report",
    "assumption_ledger",
    "mathematical_spec_version",
)

#: Section 2.3, "What is deliberately not emitted", as a checkable list.
NOT_EMITTED: tuple[str, ...] = (
    "entropy",
    "objective_value",
    "key_length",
    "acceptance_set",
    "honest_channel_statistics",
    "any_observed_number",
    "penalty_term",
    "error_parameter",
    "any_recomputed_receiver_quantity",
)

#: Section 2.1, `link_declarations`: the NINE kinds, in the contract's order.
LINK_KINDS: tuple[str, ...] = (
    "identity",
    "fss",
    "wpfss",
    "register-mixture",
    "flags-enough",
    "pinching",
    "source-map",
    "family-dominating",
    "label-space",
)

#: The six version-1 kinds and the three reserved-and-refused ones.
LINK_KINDS_IMPLEMENTED: tuple[str, ...] = LINK_KINDS[:6]
LINK_KINDS_DEFERRED: tuple[str, ...] = LINK_KINDS[6:]

#: Definition def:link, `stage`.
LINK_STAGES: tuple[str, ...] = ("source", "receiver")

#: Definition def:link, `status`, and the only value version 1 emits.
LINK_STATUS_VOCABULARY: tuple[str, ...] = (
    "exact",
    "certified_outer",
    "exploratory_numeric",
)
LINK_STATUS_EMITTED: tuple[str, ...] = ("exact",)

#: Section 2.1, `route`. `both` is refused (route_not_single_valued).
ROUTES: tuple[str, ...] = ("encoded", "licensed")

#: Definition def:licensed. The NULL spelling is NOT frozen: interface.yaml
#: records it as open implementation choice 2 of 10, the contract giving the
#: symbol `nomarg` and the type "state or null" and no machine string.
SOURCE_MODES: tuple[str, ...] = ("trusted", "untrusted")

#: Corollary cor:pullback (i)-(iii). Every constraint this module emits is of
#: Corollary cor:transported case (i), which carries these three.
CERTIFICATE_KINDS: tuple[str, ...] = ("identity", "positivity", "spectral")

#: Section 4.13, both tabulars, VERBATIM: 24 strings over 21 rows.
REFUSAL_REASONS: tuple[str, ...] = (
    "receiver_spec_not_accepted",
    "cutoff_mismatch",
    "no_block_structure",
    "bound_set_not_a_fibre",
    "dark_counts_do_not_descend",
    "bounded_letter_not_absorbing",
    "total_weight_not_below_one",
    "blinding_model_ill_formed",
    "probe_weights_ill_formed",
    "declared_relation_impossible",
    "chain_ill_formed",
    "source_link_after_receiver_link",
    "link_kind_deferred",
    "approximate_squashing_unsupported",
    "device_family_unsupported",
    "constraint_without_certificate",
    "data_dependent_constant",
    "licence_missing",
    "licence_without_constraints",
    "route_not_single_valued",
    "constraint_channel_mismatch",
    "alphabet_or_order_mismatch",
    "post_processing_order_violated",
    "unsound_constraint_requested",
)

#: Section 2.5, whose itemize environment carries TWELVE bullets, in the values
#: interface.yaml transcribes. Some bullets fix more than one machine key --
#: bullet 1 fixes log_base AND entropy_units, bullet 2 fixes entropy_variant,
#: arrow AND alpha_domain -- so this mapping has more entries than the section
#: has bullets, and interface.yaml records the bullet count separately.
CONVENTIONS: dict[str, str] = {
    "log_base": "2",
    "entropy_units": "bits",
    "entropy_variant": "sandwiched-renyi",
    "arrow": "up",
    "alpha_domain": "(1, 2)",
    "test_statistics_model": "output_state",
    "round_homogeneity": "required",
    "composition_order": "later links act later; source stage before receiver stage",
    "post_processing_order": "dark counts, then coarse-graining, then joint alphabet",
    "subsystem_order": "A before Q; nb first; blinded branches carry flags only",
    "povm_index_convention": "comma = joint outcome, bar = conditional POVM",
    "block_restriction": "blk M is a BLOCK, not a compression",
    "fail_closed": "refusal with a machine-readable reason and NO artifact",
    "artifact_bindings.mathematical_spec_version": "proof-reductions@0.1.3",
}

#: Section 1.4, the conditional rounding rule, frozen as a DIRECTION and not as
#: an exercised computation: "IF receiver-povm ever emits an exact or interval
#: evaluation, THIS MODULE MUST ROUND p_(y_i,t) TOWARD ZERO". Today the upstream
#: `bound_evaluation` is `floating_point`, so a certified request already falls
#: back before this module is reached, and no frozen value engages the rule --
#: every one of them is exact over the Fractions.
ROUNDING_RULE: dict[str, str] = {
    "quantity": "p_(y_i,t)",
    "equation": "eq:weightroute",
    "direction": "toward_zero",
    "engaged_when": "receiver-povm emits an exact or interval bound_evaluation",
    "today": "floating_point upstream; certified falls back before this module",
    "hazard": "a round-to-nearest result can exceed the true value, falsifying "
    "eq:certweights -- the failure A-RECV's ledger row calls a security break",
}


# ===========================================================================
#  Group PR-A -- the WP3 instance and the squashing relation (PR1)
# ===========================================================================
#
#  WP3 is the workhorse of this file: PR1, PR3, PR4, PR6 and PR11 all run on it.
#  It is deliberately GENUINELY COMPLEX and its source is 3-dimensional, so that
#  a real-only or 2-dimensional implementation cannot pass by accident.
#
#  THE SETTING, in the vocabulary of contract Section 4.6.
#    H(B)      = C^3 with basis (|0>, |1>, |2>);
#    H(B_<=N)  = span{|0>}          (the preserved block, dim 1)
#    H(B_>N)   = span{|1>, |2>}     (the above-cutoff block, dim 2)
#    V         = {v0, v1}
#    H(flag)   = C^2 with basis (|f_v0>, |f_v1>)
#    H(Q)      = H(B_<=N) (+) H(flag) = C^3, basis (|q>, |f_v0>, |f_v1>)
#
#  THE ABOVE-CUTOFF POVM IS BUILT BACKWARDS FROM A RANK-ONE PVM, so that every
#  entry is Gaussian-rational and every eigenvalue is visible by inspection:
#      psi_0 = (3/5)|1> + (4i/5)|2>,      psi_1 = (4/5)|1> - (3i/5)|2>
#  is an ORTHONORMAL BASIS of H(B_>N) -- <psi_0|psi_0> = 9/25 + 16/25 = 1,
#  likewise psi_1, and <psi_0|psi_1> = (3/5)(4/5) + (-4i/5)(-3i/5)
#  = 12/25 - 12/25 = 0 -- built from the Pythagorean triple (3, 4, 5) so that
#  the unit vectors themselves, and not merely their projectors, are exact.
#  Then M'_v := |psi_v><psi_v| is the POVM Eq. eq:Lwp measures on the
#  above-cutoff block, and the PHYSICAL blocks are RECONSTRUCTED from it by
#  inverting Eq. eq:Lwp's definition:
#      blk M^{>N}_v = (1 - p) M'_v + p_v 1,     p_0 = 1/4, p_1 = 1/8, p = 3/8.
#  Eq. eq:certweights then holds BY CONSTRUCTION and TIGHTLY IN THE RIGHT
#  DIRECTION: blk M^{>N}_v - p_v 1 = (5/8) M'_v >= 0, with equality of the
#  minimum eigenvalue exactly at p_v. The preserved blocks are the NON-DYADIC
#  2/3 and 1/3.

#: The two orthonormal vectors of H(B_>N), embedded in C^3, exact.
PSI_0: tuple[Gauss, ...] = (gz(0), gz(F(3, 5)), gz(0, F(4, 5)))
PSI_1: tuple[Gauss, ...] = (gz(0), gz(F(4, 5)), gz(0, F(-3, 5)))

#: M'_v = |psi_v><psi_v| on H(B_>N), the POVM of Eq. eq:Lwp. Rank one, trace
#: one, determinant zero: eigenvalues {1, 0}, so M'_0 + M'_1 = 1 exactly.
MP_V0: Matrix = (
    (gz(F(9, 25)), gz(0, F(-12, 25))),
    (gz(0, F(12, 25)), gz(F(16, 25))),
)
MP_V1: Matrix = (
    (gz(F(16, 25)), gz(0, F(12, 25))),
    (gz(0, F(-12, 25)), gz(F(9, 25))),
)

#: blk M^{>N}_v = (5/8) M'_v + p_v 1. Eigenvalues {5/8 + p_v, p_v}, i.e.
#: {7/8, 1/4} for v0 and {3/4, 1/8} for v1.
BLK_GT_V0: Matrix = (
    (gz(F(19, 40)), gz(0, F(-3, 10))),
    (gz(0, F(3, 10)), gz(F(13, 20))),
)
BLK_GT_V1: Matrix = (
    (gz(F(21, 40)), gz(0, F(3, 10))),
    (gz(0, F(-3, 10)), gz(F(7, 20))),
)

#: The physical POVM on C^3 = H(B_<=N) (+) H(B_>N), block diagonal at the
#: cutoff by construction -- which is what Definition def:targets requires and
#: what Section 4.13's `no_block_structure` check tests.
WP3_M_V0: Matrix = (
    (gz(F(2, 3)), gz(0), gz(0)),
    (gz(0), gz(F(19, 40)), gz(0, F(-3, 10))),
    (gz(0), gz(0, F(3, 10)), gz(F(13, 20))),
)
WP3_M_V1: Matrix = (
    (gz(F(1, 3)), gz(0), gz(0)),
    (gz(0), gz(F(21, 40)), gz(0, F(3, 10))),
    (gz(0), gz(0, F(-3, 10)), gz(F(7, 20))),
)

#: The multi-bound WPFSS target of Eq. eq:WPFSS at (p_0, p_1) = (1/4, 1/8):
#: F^WP_v = blk M^{<=N}_v (+) (p_v 1_flag + (1-p)|v><v|), so the flag block of
#: F^WP_v0 is diag(1/4 + 5/8, 1/4) = diag(7/8, 1/4).
WP3_FWP_V0: Matrix = diag_matrix((F(2, 3), F(7, 8), F(1, 4)))
WP3_FWP_V1: Matrix = diag_matrix((F(1, 3), F(1, 8), F(3, 4)))

#: The flag-state-squasher target of Eq. eq:FSS, the p_v = 0 case.
WP3_FFSS_V0: Matrix = diag_matrix((F(2, 3), 1, 0))
WP3_FFSS_V1: Matrix = diag_matrix((F(1, 3), 0, 1))

#: The block projectors. On Q: Pi_<=N and Pi_flag. On B: Pi_<=N and Pi_>N.
#: Eq. eq:transportproj transports the FIRST pair to the SECOND.
PI_LEQ_Q: Matrix = diag_matrix((1, 0, 0))
PI_FLAG_Q: Matrix = diag_matrix((0, 1, 1))
PI_LEQ_B: Matrix = diag_matrix((1, 0, 0))
PI_GT_B: Matrix = diag_matrix((0, 1, 1))

#: EXACT KRAUS OPERATORS OF Lambda^WP, all Gaussian-rational.
#: K_pres = |q><0|, K_v = |f_v><psi_v|; row f_v of K_v is <psi_v| = conj(psi_v).
#: sum_K K+ K = |0><0| + M'_0 + M'_1 = Pi_<=N + Pi_>N = 1, checked exactly by
#: the integrity test. Applying them reproduces Eq. eq:Lwp verbatim:
#: Lambda(rho) = <0|rho|0> |q><q| + sum_v <psi_v|rho|psi_v> |f_v><f_v|, and
#: <psi_v|rho|psi_v> = tr[M'_v Pi_>N rho Pi_>N] because psi_v lies in H(B_>N).
WP3_KRAUS_PRES: Matrix = real_matrix(((1, 0, 0), (0, 0, 0), (0, 0, 0)))
WP3_KRAUS_V0: Matrix = (
    (gz(0), gz(0), gz(0)),
    (gz(0), gz(F(3, 5)), gz(0, F(-4, 5))),
    (gz(0), gz(0), gz(0)),
)
WP3_KRAUS_V1: Matrix = (
    (gz(0), gz(0), gz(0)),
    (gz(0), gz(0), gz(0)),
    (gz(0), gz(F(4, 5)), gz(0, F(3, 5))),
)
WP3_KRAUS: tuple[Matrix, ...] = (WP3_KRAUS_PRES, WP3_KRAUS_V0, WP3_KRAUS_V1)

#: A SECOND CHANNEL REALIZING THE SAME RELATION, for the uniqueness clause of
#: Lemma lem:statistics and for Remark rem:channel-choice. Because M'_0 and M'_1
#: are ORTHOGONAL RANK-ONE projections, the flag half of Lambda^WP is the
#: isometry V: |psi_v> -> |f_v> followed by dephasing; dropping the dephasing
#: gives the ISOMETRIC channel Lambda'(rho) = <0|rho|0>|q><q| (+) V Pi_> rho
#: Pi_> V+, whose Kraus set is (K_pres, V_ISO) with V_ISO = K_v0 + K_v1.
WP3_KRAUS_ISO: Matrix = (
    (gz(0), gz(0), gz(0)),
    (gz(0), gz(F(3, 5)), gz(0, F(-4, 5))),
    (gz(0), gz(F(4, 5)), gz(0, F(3, 5))),
)
WP3_KRAUS_PRIME: tuple[Matrix, ...] = (WP3_KRAUS_PRES, WP3_KRAUS_ISO)

#: An operator OFF the carried span, on which the two realizing channels
#: DISAGREE. The span of {F^WP_v0, F^WP_v1, Pi_<=N, Pi_flag} is the whole space
#: of DIAGONAL matrices on Q -- F^WP_v0 - (2/3)Pi_<=N = diag(0, 7/8, 1/4) is
#: independent of Pi_flag = diag(0,1,1) because 7/8 != 1/4 -- so a witness must
#: be OFF-DIAGONAL, and this is the Hermitian one.
O_OFF: Matrix = real_matrix(((0, 0, 0), (0, 0, 1), (0, 1, 0)))

#: Lambda+(O_OFF) = 0: Eq. eq:WPadjoint reads only the DIAGONAL of the flag
#: block. Lambda'+(O_OFF) = |psi_0><psi_1| + h.c., computed exactly:
#:   |psi_0><psi_1| = [[12/25, 9i/25], [16i/25, -12/25]],
#: so the Hermitian sum is the matrix below -- traceless, non-zero, and
#: GENUINELY COMPLEX, which is what makes the disagreement observable.
O_OFF_PULLBACK_PRIME: Matrix = (
    (gz(0), gz(0), gz(0)),
    (gz(0), gz(F(24, 25)), gz(0, F(-7, 25))),
    (gz(0), gz(0, F(7, 25)), gz(F(-24, 25))),
)

#: A NON-TRIVIAL IDENTITY CERTIFICATE that is TIED TO ONE CHANNEL. Under
#: Lambda^WP the pull-back of 1_Q + O_OFF is 1_B exactly -- an identity
#: certificate with c = 1 whose operator is NOT c 1_Q -- while under Lambda' it
#: is 1_B + O_OFF_PULLBACK_PRIME, which is not a multiple of the identity. This
#: is Remark rem:channel-choice (b)-(c) with numbers: an operator OUTSIDE the
#: carried tuple yields a constraint tied to the construction, and imposing it
#: alongside a constraint sound for the other channel would void
#: Theorem thm:transfer.
O_ID_OFFSPAN: Matrix = (
    (gz(1), gz(0), gz(0)),
    (gz(0), gz(1), gz(1)),
    (gz(0), gz(1), gz(1)),
)


@dataclass(frozen=True)
class RelationCase:
    """One frozen squashing relation, with its adjoint checked entry by entry."""

    case_id: str
    claims: tuple[str, ...]
    alphabet: tuple[str, ...]
    source_dim: int
    target_dim: int
    #: (label, physical element M_v on B) pairs, in the alphabet's order.
    physical: tuple[tuple[str, Matrix], ...]
    #: (label, target element F_v on Q) pairs, in the alphabet's order.
    target: tuple[tuple[str, Matrix], ...]
    #: Exact Kraus operators of the channel witness where they are
    #: Gaussian-rational, else ``None`` -- see the group comment.
    kraus: tuple[Matrix, ...] | None
    #: (label, O^ on Q, pull-back Lambda+(O^) on B) triples.
    carried: tuple[tuple[str, Matrix, Matrix], ...]
    derivation: str


WP3_RELATION_WP = RelationCase(
    case_id="WP3-wpfss",
    claims=("PR1", "PR6"),
    alphabet=("v0", "v1"),
    source_dim=3,
    target_dim=3,
    physical=(("v0", WP3_M_V0), ("v1", WP3_M_V1)),
    target=(("v0", WP3_FWP_V0), ("v1", WP3_FWP_V1)),
    kraus=WP3_KRAUS,
    carried=(
        ("Pi_leq", PI_LEQ_Q, PI_LEQ_B),
        ("Pi_flag", PI_FLAG_Q, PI_GT_B),
    ),
    derivation="""\
Eq. eq:WPadjoint gives the adjoint of Lambda^WP on a block observable:
    Lambda^WP+(X_<=N (+) X_flag) = X_<=N (+) sum_v <v|X_flag|v> M'_v .
Evaluate it at F^WP_v0, whose flag block has diagonal (7/8, 1/4):

  (7/8) M'_0 + (1/4) M'_1
    (0,0): (7/8)(9/25) + (1/4)(16/25) = 63/200 + 32/200 = 95/200 = 19/40
    (0,1): (7/8)(-12i/25) + (1/4)(12i/25) = (-84i + 48i)/200 = -36i/200 ...

  -- done over the common denominator 200 with the 1/4 term written as 32/200,
  24i/200 and 18/200 the second matrix's entries scaled: explicitly
    (7/8) M'_0 = [[63/200, -84i/200], [84i/200, 112/200]]
    (1/4) M'_1 = [[32/200,  24i/200], [-24i/200, 18/200]]
    sum        = [[95/200, -60i/200], [60i/200, 130/200]]
               = [[19/40,  -3i/10 ], [3i/10,  13/20 ]]  =  blk M^{>N}_v0 .
With the preserved block passed through unchanged, Lambda^WP+(F^WP_v0) = M_v0.

At F^WP_v1, whose flag block has diagonal (1/8, 3/4):
    (1/8) M'_0 = [[ 9/200, -12i/200], [12i/200, 16/200]]
    (3/4) M'_1 = [[96/200,  72i/200], [-72i/200, 54/200]]
    sum        = [[105/200, 60i/200], [-60i/200, 70/200]]
               = [[21/40,   3i/10  ], [-3i/10,   7/20 ]]  =  blk M^{>N}_v1 .

THE TRANSPORTED PROJECTORS, Eq. eq:transportproj. X = Pi_<=N means X_<=N = 1,
X_flag = 0, and eq:WPadjoint returns Pi_<=N. X = Pi_flag means X_<=N = 0,
X_flag = 1_flag, and it returns 0 (+) (M'_0 + M'_1) = 0 (+) 1 = Pi_>N. Both
pull-backs are POSITIVE though NEITHER IS A MULTIPLE OF THE IDENTITY, which is
exactly the sentence Section 2.1's `carried_operators` row uses to admit the
default pair on the trivial certificate (c = 0, relation >=).

COMPLETENESS. sum_v F^WP_v = 1_{B_<=N} (+) (p 1_flag + (1-p) 1_flag) = 1_Q,
the flag block being diag(7/8 + 1/8, 1/4 + 3/4) = diag(1, 1).

THE KRAUS SET. sum_K K+ K = |0><0| + |psi_0><psi_0| + |psi_1><psi_1|
= Pi_<=N + Pi_>N = 1_B, since (psi_0, psi_1) is an orthonormal basis of the
above-cutoff block. Applying the set reproduces Eq. eq:Lwp verbatim.""",
)

WP3_RELATION_FSS = RelationCase(
    case_id="WP3-fss",
    claims=("PR1", "PR6"),
    alphabet=("v0", "v1"),
    source_dim=3,
    target_dim=3,
    physical=(("v0", WP3_M_V0), ("v1", WP3_M_V1)),
    target=(("v0", WP3_FFSS_V0), ("v1", WP3_FFSS_V1)),
    kraus=None,
    carried=(
        ("Pi_leq", PI_LEQ_Q, PI_LEQ_B),
        ("Pi_flag", PI_FLAG_Q, PI_GT_B),
    ),
    derivation="""\
The p_v = 0 case of the same computation, with M'_v replaced by
blk M^{>N}_v (Eq. eq:Lfss). F^FSS_v0 = blk M^{<=N}_v0 (+) |v0><v0| has flag
diagonal (1, 0), so eq:WPadjoint returns
    1 * blk M^{>N}_v0 + 0 * blk M^{>N}_v1 = blk M^{>N}_v0 ,
and F^FSS_v1, flag diagonal (0, 1), returns blk M^{>N}_v1. The transported
projectors are the same two: Pi_flag pulls back to sum_v blk M^{>N}_v = Pi_>N.

WHY `kraus` IS None HERE AND NOT FOR Lambda^WP. Lambda^FSS is the
measure-and-prepare channel of the POVM {blk M^{>N}_v}, whose Kraus operators
need a SQUARE ROOT of blk M^{>N}_v0 -- whose eigenvalues are 7/8 and 1/4, so
the square root is irrational and cannot be frozen in this representation. It
does not need to be: contract Section 2.3 states that `squashing_channel` is
"A SYMBOLIC CONSTRUCTOR RECORD, NOT EVALUABLE DATA", because "the supplier
emits no above-cutoff block at all, so neither map can be materialised from the
artifact -- and neither need be, SINCE THE CONSUMER NEVER APPLIES IT". What IS
frozen, and what every statement of the contract is about, is the ADJOINT,
which eq:WPadjoint gives in closed form and which is exactly rational here.
Lambda^WP's Kraus set is frozen only because THIS instance makes it rational --
M'_v being rank one with a Pythagorean unit vector -- not because the contract
requires one.""",
)

WP3_RELATION_PRIME = RelationCase(
    case_id="WP3-isometric",
    claims=("PR1", "PR3"),
    alphabet=("v0", "v1"),
    source_dim=3,
    target_dim=3,
    physical=(("v0", WP3_M_V0), ("v1", WP3_M_V1)),
    target=(("v0", WP3_FWP_V0), ("v1", WP3_FWP_V1)),
    kraus=WP3_KRAUS_PRIME,
    carried=(
        ("Pi_leq", PI_LEQ_Q, PI_LEQ_B),
        ("Pi_flag", PI_FLAG_Q, PI_GT_B),
    ),
    derivation="""\
A SECOND channel realizing the SAME relation, which is what makes the last
sentence of Lemma lem:statistics and the whole of Remark rem:channel-choice
checkable rather than abstract.

CONSTRUCTION. V := |f_v0><psi_0| + |f_v1><psi_1| is an isometry from H(B_>N)
onto H(flag), because (psi_0, psi_1) is orthonormal; V+ V = |psi_0><psi_0| +
|psi_1><psi_1| = Pi_>N, so (K_pres, V) is a Kraus set with
    K_pres+ K_pres + V+ V = Pi_<=N + Pi_>N = 1_B .
Its adjoint is Lambda'+(X) = X_qq |0><0| + V+ X V, and
    V+ X V = sum_{a,b} X_{f_a f_b} |psi_a><psi_b| .

AGREEMENT ON THE CARRIED SPAN. For X DIAGONAL in the target basis the off-
diagonal terms vanish and V+ X V = X_{f0f0} M'_0 + X_{f1f1} M'_1, which is
exactly eq:WPadjoint's flag term. Every element of
span({F^WP_v} u {Pi_<=N, Pi_flag}) is diagonal, so Lambda'+ = Lambda^WP+ on
the whole span -- the uniqueness clause of Lemma lem:statistics, verified on
all four operators.

DISAGREEMENT OFF IT. At the off-diagonal Hermitian O_OFF = |f_0><f_1| + h.c.,
Eq. eq:WPadjoint returns 0 (it reads only diagonal entries), while
    V+ O_OFF V = |psi_0><psi_1| + |psi_1><psi_0| .
Compute |psi_0><psi_1| with psi_0 = (3/5, 4i/5), psi_1 = (4/5, -3i/5) on the
basis (|1>, |2>):
    (0,0) = (3/5)(4/5)     = 12/25
    (0,1) = (3/5)(3i/5)    = 9i/25          [conj(-3i/5) = 3i/5]
    (1,0) = (4i/5)(4/5)    = 16i/25
    (1,1) = (4i/5)(3i/5)   = 12 i^2/25 = -12/25
Adding the Hermitian conjugate [[12/25, -16i/25], [-9i/25, -12/25]] gives
    [[24/25, -7i/25], [7i/25, -24/25]] ,
which is Hermitian, traceless and NON-ZERO. So the two channels' adjoints
differ off the span, and their REACHABLE SETS differ too: Lambda^WP's output is
always diagonal in the target basis, Lambda''s is not.

WHAT THIS PINS. Remark rem:channel-choice (c): "constraints sound for Lambda
and constraints sound for Lambda' may have an intersection excluding every
state reachable under either, and imposing them together would void
Theorem thm:transfer exactly as an unsound constraint does". The remedy the
contract states is the CARRIED TUPLE, and this case shows the boundary: the two
cutoff projectors ARE in the tuple and the adjoints agree on them, so every
constraint built from them belongs to the relation and not to the
construction.""",
)

RELATION_CASES: tuple[RelationCase, ...] = (
    WP3_RELATION_WP,
    WP3_RELATION_FSS,
    WP3_RELATION_PRIME,
)

#: The WP3 instance's declared data in one record, so that a consumer does not
#: have to reassemble it from the individual matrices.
WP3: dict[str, object] = {
    "instance_id": "WP3",
    "claims": ("PR1", "PR3", "PR4", "PR6", "PR11"),
    "alphabet": ("v0", "v1"),
    "source_dim": 3,
    "preserved_dim": 1,
    "above_cutoff_dim": 2,
    "target_dim": 3,
    "preserved_blocks": (("v0", F(2, 3)), ("v1", F(1, 3))),
    "above_cutoff_blocks": (("v0", BLK_GT_V0), ("v1", BLK_GT_V1)),
    "mprime": (("v0", MP_V0), ("v1", MP_V1)),
    "weights": (("v0", F(1, 4)), ("v1", F(1, 8))),
    "total_weight": F(3, 8),
    "one_minus_total": F(5, 8),
    "above_cutoff_eigenvalues": (
        ("v0", (F(7, 8), F(1, 4))),
        ("v1", (F(3, 4), F(1, 8))),
    ),
    "orthonormal_basis": (("psi_0", PSI_0), ("psi_1", PSI_1)),
}


@dataclass(frozen=True)
class StatisticsCase:
    """Statistics equality on one input, Lemma lem:statistics (ii) and (iii)."""

    case_id: str
    claims: tuple[str, ...]
    #: The physical input rho on B (or on B (x) R when ``side_operator`` is set).
    rho: Matrix | None
    #: Description of rho where it is not frozen as a matrix.
    rho_description: str
    #: The squashed image Lambda(rho), as the diagonal it always is here.
    squashed_diagonal: tuple[F, ...]
    #: (outcome, tr[M_v rho] = tr[F_v Lambda(rho)]) pairs.
    statistics: tuple[tuple[str, F], ...]
    #: Non-``None`` for the side-system cases of Lemma lem:statistics (iii).
    side_operator: str | None
    derivation: str


WP3_STATISTICS: tuple[StatisticsCase, ...] = (
    StatisticsCase(
        case_id="WP3-stat-vacuum",
        claims=("PR1",),
        rho=real_matrix(((1, 0, 0), (0, 0, 0), (0, 0, 0))),
        rho_description="|0><0|, supported entirely in the preserved block",
        squashed_diagonal=(F(1), F(0), F(0)),
        statistics=(("v0", F(2, 3)), ("v1", F(1, 3))),
        side_operator=None,
        derivation="""\
Lambda^WP(|0><0|) = <0|0><0|0> |q><q| + sum_v |<psi_v|0>|^2 |f_v><f_v|
= |q><q|, because psi_0 and psi_1 lie in the above-cutoff block and are
orthogonal to |0>. Then tr[F^WP_v0 |q><q|] = (F^WP_v0)_qq = 2/3, and
tr[M_v0 |0><0|] = (M_v0)_00 = 2/3 -- the preserved block passes through
untouched, which is the whole point of the FIRST branch of Eq. eq:Lwp.""",
    ),
    StatisticsCase(
        case_id="WP3-stat-psi0",
        claims=("PR1",),
        rho=None,
        rho_description="|psi_0><psi_0| = M'_v0 embedded in C^3, a pure state",
        squashed_diagonal=(F(0), F(1), F(0)),
        statistics=(("v0", F(7, 8)), ("v1", F(1, 8))),
        side_operator=None,
        derivation="""\
Lambda^WP(|psi_0><psi_0|) = |f_v0><f_v0|, since <psi_0|psi_0> = 1 and
<psi_1|psi_0> = 0. Target side: tr[F^WP_v0 |f_0><f_0|] = 7/8 and
tr[F^WP_v1 |f_0><f_0|] = 1/8. Physical side:
    <psi_0| blk M^{>N}_v0 |psi_0> = <psi_0| ((5/8) M'_0 + (1/4) 1) |psi_0>
                                   = 5/8 + 1/4 = 7/8 ,
    <psi_0| blk M^{>N}_v1 |psi_0> = <psi_0| ((5/8) M'_1 + (1/8) 1) |psi_0>
                                   = 0 + 1/8 = 1/8 ,
using M'_1 |psi_0> = 0. THE TWO AGREE, and note that the target value 7/8 is
literally the flag diagonal entry of F^WP_v0 -- which is why the WPFSS weights
are said to be ENCODED IN THE TARGET.""",
    ),
    StatisticsCase(
        case_id="WP3-stat-mixed",
        claims=("PR1",),
        rho=diag_matrix((F(1, 2), F(1, 2), 0)),
        rho_description="(|0><0| + |1><1|)/2, straddling the cutoff",
        squashed_diagonal=(F(1, 2), F(9, 50), F(8, 25)),
        statistics=(("v0", F(137, 240)), ("v1", F(103, 240))),
        side_operator=None,
        derivation="""\
<0|rho|0> = 1/2. <psi_0|rho|psi_0> = (1/2)|<psi_0|1>|^2 = (1/2)(9/25) = 9/50,
and <psi_1|rho|psi_1> = (1/2)(16/25) = 8/25; the three sum to
25/50 + 9/50 + 16/50 = 1. Target side:
    (2/3)(1/2) + (7/8)(9/50) + (1/4)(8/25)
      = 1/3 + 63/400 + 32/400 = 1/3 + 95/400 = 1/3 + 19/80
      = 80/240 + 57/240 = 137/240 .
Physical side, both operators being block diagonal so only the diagonal of rho
contributes: (1/2)(2/3) + (1/2)(19/40) = 1/3 + 19/80 = 137/240. The v1 values
are the complements, 1 - 137/240 = 103/240, and independently
(1/2)(1/3) + (1/2)(21/40) = 1/6 + 21/80 = 40/240 + 63/240 = 103/240.""",
    ),
    StatisticsCase(
        case_id="WP3-stat-coherent",
        claims=("PR1",),
        rho=real_matrix(
            ((F(9, 25), F(12, 25), 0), (F(12, 25), F(16, 25), 0), (0, 0, 0))
        ),
        rho_description=(
            "|chi><chi| with chi = (3/5)|0> + (4/5)|1>: a PURE state with "
            "COHERENCE ACROSS THE CUTOFF, which both channels discard"
        ),
        squashed_diagonal=(F(9, 25), F(144, 625), F(256, 625)),
        statistics=(("v0", F(68, 125)), ("v1", F(57, 125))),
        side_operator=None,
        derivation="""\
This input exists because Proposition prop:chain's composition proof says the
identity Lambda^FSS = Lambda~ o Lambda^WP "holds for every rho, INCLUDING
STATES WITH COHERENCES ACROSS THE CUTOFF, WHICH BOTH SIDES DISCARD"; a
diagonal-only fixture could not exhibit that.

<0|chi> = 3/5 so <0|rho|0> = 9/25. <psi_0|chi> = conj(3/5)(4/5) = 12/25, so
|<psi_0|chi>|^2 = 144/625; <psi_1|chi> = (4/5)(4/5) = 16/25, so
|<psi_1|chi>|^2 = 256/625. Sum: 225/625 + 144/625 + 256/625 = 1.
Target side, over the denominator 5000:
    (2/3)(9/25) + (7/8)(144/625) + (1/4)(256/625)
      = 1200/5000 + 1008/5000 + 512/5000 = 2720/5000 = 68/125 .
Physical side: M_v0 is block diagonal, so its (0,1) entry is ZERO and the
coherence of rho contributes nothing:
    (9/25)(2/3) + (16/25)(19/40) = 6/25 + 38/125 = 30/125 + 38/125 = 68/125.
THE AGREEMENT IS THE POINT: the physical operator's block-diagonality is what
makes the discarded coherence harmless, and it is Definition def:targets'
hypothesis and Section 4.13's `no_block_structure` check.""",
    ),
    StatisticsCase(
        case_id="WP3-side-flag",
        claims=("PR1",),
        rho=None,
        rho_description=(
            "(1/2)|psi_0><psi_0| (x) |r0><r0| + (1/2)|psi_1><psi_1| (x) |r1><r1| "
            "on B (x) R with R = C^2: classically correlated with the side system"
        ),
        squashed_diagonal=(F(0), F(1, 2), F(1, 2)),
        statistics=(("v0", F(5, 16)), ("v1", F(-5, 16))),
        side_operator="X = |r0><r0| - |r1><r1|, Hermitian and NOT positive",
        derivation="""\
Lemma lem:statistics (iii) quantifies over EVERY finite-dimensional side system
R, EVERY state on B (x) R and EVERY X in L(R) -- not merely positive X, and not
merely product states. The contract adds that "the side system R in (iii) is not
a technicality: in a security proof it holds Alice's retained register and Eve's
side information".

(Lambda (x) id)(rho) = (1/2)|f_0><f_0| (x) |r0><r0|
                     + (1/2)|f_1><f_1| (x) |r1><r1| .
Physical side:
    tr[(M_v0 (x) X) rho] = (1/2)<psi_0|M_v0|psi_0> - (1/2)<psi_1|M_v0|psi_1>
                         = (1/2)(7/8) - (1/2)(1/4) = 7/16 - 2/16 = 5/16 .
Target side:
    (1/2)(F^WP_v0)_{f0 f0} - (1/2)(F^WP_v0)_{f1 f1}
                         = (1/2)(7/8) - (1/2)(1/4) = 5/16 .
For v1: (1/2)(1/8) - (1/2)(3/4) = 1/16 - 6/16 = -5/16, and the target side is
(1/2)(1/8) - (1/2)(3/4) likewise. The NEGATIVE value is deliberate: it is only
reachable with a non-positive X, and it shows the identity is an identity of
OPERATORS ON R and not an inequality between probabilities.""",
    ),
    StatisticsCase(
        case_id="WP3-side-mixed",
        claims=("PR1", "PR2"),
        rho=None,
        rho_description=(
            "(1/2)|0><0| (x) |r0><r0| + (1/2)|psi_1><psi_1| (x) |r1><r1|: the "
            "same construction with one branch in the PRESERVED block"
        ),
        squashed_diagonal=(F(1, 2), F(0), F(1, 2)),
        statistics=(("v0", F(5, 24)), ("v1", F(-5, 24))),
        side_operator="X = |r0><r0| - |r1><r1|, Hermitian and NOT positive",
        derivation="""\
The companion of WP3-side-flag with one branch below the cutoff, so that BOTH
branches of Eq. eq:Lwp are exercised in one state.

(Lambda (x) id)(rho) = (1/2)|q><q| (x) |r0><r0|
                     + (1/2)|f_1><f_1| (x) |r1><r1| .
Physical: (1/2)<0|M_v0|0> - (1/2)<psi_1|M_v0|psi_1>
        = (1/2)(2/3) - (1/2)(1/4) = 1/3 - 1/8 = 8/24 - 3/24 = 5/24 .
Target:   (1/2)(F^WP_v0)_qq - (1/2)(F^WP_v0)_{f1 f1}
        = (1/2)(2/3) - (1/2)(1/4) = 5/24 .
For v1: (1/2)(1/3) - (1/2)(3/4) = 4/24 - 9/24 = -5/24, both sides.
THIS STATE IS REUSED BY GROUP PR-B as the input of the one-round transfer.""",
    ),
)


# ===========================================================================
#  Group PR-B -- security transfer with no penalty term (PR2)
# ===========================================================================


@dataclass(frozen=True)
class TransferCase:
    """One round of Theorem thm:factorization, output state entry by entry."""

    case_id: str
    claims: tuple[str, ...]
    rounds: int
    adversary_dim: int
    rho_description: str
    sigma_description: str
    #: ((outcome, side-basis label), value) for the PHYSICAL run.
    physical_output: tuple[tuple[tuple[str, str], F], ...]
    #: The same for the SQUASHED run. Theorem thm:factorization says EQUAL.
    squashed_output: tuple[tuple[tuple[str, str], F], ...]
    derivation: str


TRANSFER_ONE_ROUND = TransferCase(
    case_id="WP3-transfer-n1",
    claims=("PR2", "PR3"),
    rounds=1,
    adversary_dim=2,
    rho_description=(
        "rho = (1/2)|0><0| (x) |r0><r0| + (1/2)|psi_1><psi_1| (x) |r1><r1| on "
        "B (x) E, the state of WP3-side-mixed read with R = E"
    ),
    sigma_description=(
        "sigma = (Lambda^WP (x) id_E)(rho) = (1/2)|q><q| (x) |r0><r0| "
        "+ (1/2)|f_v1><f_v1| (x) |r1><r1|"
    ),
    physical_output=(
        (("v0", "r0"), F(1, 3)),
        (("v0", "r1"), F(1, 8)),
        (("v1", "r0"), F(1, 6)),
        (("v1", "r1"), F(3, 8)),
    ),
    squashed_output=(
        (("v0", "r0"), F(1, 3)),
        (("v0", "r1"), F(1, 8)),
        (("v1", "r0"), F(1, 6)),
        (("v1", "r1"), F(3, 8)),
    ),
    derivation="""\
Definition def:protocol at n = 1 with the remaining processing Gbar and the
end-of-protocol map K taken to be the IDENTITY on the classical outcome
register. That is not a weakening: Theorem thm:factorization's proof uses
NOTHING about Gbar_j or K except that they are UNCHANGED BETWEEN THE TWO RUNS
and touch no B_j, so the whole content of the theorem at n = 1 is the identity
of the measurement channel's output, and any further classical processing is a
fixed post-map applied to two equal states.

THE PHYSICAL RUN. (N_M (x) id_E)(rho) = sum_v |v><v|_Y (x) tr_B[(M_v (x) 1)rho],
and rho is a classical mixture of two product branches, so
    tr_B[(M_v (x) 1) rho] = (1/2)<0|M_v|0> |r0><r0|
                          + (1/2)<psi_1|M_v|psi_1> |r1><r1| .
With <0|M_v0|0> = 2/3, <psi_1|M_v0|psi_1> = 1/4 (= 0 + 1/4 from
(5/8)M'_0 + (1/4)1 annihilating psi_1), <0|M_v1|0> = 1/3 and
<psi_1|M_v1|psi_1> = 5/8 + 1/8 = 3/4:
    v0 -> (1/3) |r0><r0| + (1/8) |r1><r1|
    v1 -> (1/6) |r0><r0| + (3/8) |r1><r1|
Total trace 1/3 + 1/8 + 1/6 + 3/8 = 8/24 + 3/24 + 4/24 + 9/24 = 1.

THE SQUASHED RUN. (N_F (x) id_E)(sigma) with the SAME Gbar and K:
    tr_Q[(F^WP_v (x) 1) sigma] = (1/2)(F^WP_v)_qq |r0><r0|
                               + (1/2)(F^WP_v)_{f1 f1} |r1><r1| ,
which is (1/2)(2/3), (1/2)(1/4) for v0 and (1/2)(1/3), (1/2)(3/4) for v1 --
THE SAME FOUR NUMBERS.

WHAT IS PINNED. Eq. eq:sameoutput: the two protocols "do not merely have close
output states, they have THE SAME ONE. This is why the transfer costs nothing
and holds simultaneously for every criterion of the form eq:criterion, with the
SAME epsilon on both sides." No entry of this registry carries an epsilon, a
penalty term or an error parameter, and Section 2.3 forbids emitting one.

THE n-ROUND FORM is Eq. eq:factorization, E_M = E_F o (id (x) Lambda^{(x)n}),
and its proof is the commutation of Lambda_j with Gbar_i for i != j on disjoint
tensor factors. That is a structural statement with no numbers to freeze, and
Remark rem:coherent records that the tensor power is a hypothesis about BOB'S
DEVICE (Assumptions A-MEAS, A-ROUND) and NOT about the adversary: rho is an
arbitrary state on A^n B^n E and the attack sequence is arbitrary.""",
)

TRANSFER_CASES: tuple[TransferCase, ...] = (TRANSFER_ONE_ROUND,)


# ===========================================================================
#  Group PR-C -- sound constraints, certificates, and the unsound transplant
# ===========================================================================


@dataclass(frozen=True)
class CertificateCase:
    """One transported operator with the certificate case that discharges it."""

    case_id: str
    claims: tuple[str, ...]
    instance: str
    certificate_kind: str
    #: The operator O^ on Q.
    ohat: Matrix | None
    #: Its pull-back Lambda+(O^) on B.
    pullback: Matrix | None
    #: The relation symbol and constant of Eq. eq:certificate.
    relation: str
    constant: F
    #: Whether the resulting family of squashed states is SOUND.
    sound: bool
    derivation: str
    #: SUPERSESSION MARK, set by run A of the 0.2.0 band. ``None`` means the
    #: case stands as frozen. A version string means the 0.2.0 amendment
    #: invalidates it in whole or in scope; see ``SUPERSESSIONS`` for the
    #: contract site and the replacement, and the module banner for what
    #: "superseded" means here. NO MARKED VALUE WAS EDITED OR DELETED.
    superseded_by: str | None = None
    superseded_site: str = ""
    superseded_replacement: tuple[str, ...] = ()


CERT_POSITIVITY = CertificateCase(
    case_id="WP3-cert-positivity",
    claims=("PR3", "PR6", "PR11"),
    instance="WP3-fss",
    certificate_kind="positivity",
    ohat=diag_matrix((F(2, 3), F(3, 4), F(-1, 4))),
    pullback=(
        (gz(F(2, 3)), gz(0), gz(0)),
        (gz(0), gz(F(9, 40)), gz(0, F(-3, 10))),
        (gz(0), gz(0, F(3, 10)), gz(F(2, 5))),
    ),
    relation=">=",
    constant=F(0),
    sound=True,
    derivation="""\
THE DEFAULT LICENSED ENTRY, Corollary cor:fssinstance Eq. eq:fssentry:
    O^ = F^FSS_o - p_o Pi_flag,   relation >=,   c = 0,   at o = v0, p_o = 1/4.
On the target it is diag(2/3, 1 - 1/4, 0 - 1/4) = diag(2/3, 3/4, -1/4), and
NOTE THE NEGATIVE ENTRY: O^ is NOT positive on Q. What is positive is its
PULL-BACK, which is the whole content of the certificate:
    Lambda^FSS+(O^) = M_v0 - (1/4) Pi_>N
                    = blk M^{<=N}_v0 (+) (blk M^{>N}_v0 - (1/4) 1)
                    = [2/3] (+) (5/8) M'_v0
                    = [2/3] (+) [[9/40, -3i/10], [3i/10, 2/5]] ,
using blk M^{>N}_v0 = (5/8) M'_v0 + (1/4) 1 and (5/8)(9/25) = 9/40,
(5/8)(-12i/25) = -3i/10, (5/8)(16/25) = 2/5. The first summand is positive
because M_v0 is, and the second because M'_v0 is a projector -- exactly the two
sentences of cor:fssinstance's proof. So Eq. eq:certificate holds with c = 0
and the relation >=, Corollary cor:pullback (ii) applies, and the family
{sigma : tr[O^ sigma] >= 0} is SOUND for Lambda^FSS.

THE CONSTRAINT IS NOT VACUOUS, which is Proposition prop:chain (iii)'s closing
clause: at sigma = |f_v1><f_v1| the value is 0 - 1/4 = -1/4 < 0, so that target
state is EXCLUDED. Under Lambda^FSS it is also NOT REACHABLE, which is why the
exclusion costs nothing; under a different channel it might be, which is
Remark rem:channel-choice and the reason Section 4.13 refuses a constraint
certified against another link's witness (`constraint_channel_mismatch`).""",
)

CERT_SPECTRAL = CertificateCase(
    case_id="WP3-cert-spectral",
    claims=("PR3",),
    instance="WP3-wpfss",
    certificate_kind="spectral",
    ohat=PI_FLAG_Q,
    pullback=PI_GT_B,
    relation="spectral bound 0 <= O <= 1",
    constant=F(0),
    sound=True,
    derivation="""\
Corollary cor:pullback (iii) with a = 0 and b = 1. O^ = Pi_flag pulls back to
Pi_>N (Eq. eq:transportproj), and a PROJECTOR satisfies 0 <= Pi_>N <= 1 as
operators, so on every reachable sigma and every finite-dimensional side system
R,
    0 <= tr_Q[(Pi_flag (x) 1_R) sigma] <= sigma_R ,
and in particular 0 <= tr[Pi_flag sigma] <= 1. This is the certificate the
DEFAULT `carried_operators` pair carries; Section 2.1 admits the pair on the
TRIVIAL certificate (c = 0, relation >=) and notes that the pull-backs are
positive "THOUGH NOT MULTIPLES OF THE IDENTITY", and the spectral form above is
the sharper reading of the same fact.

Concretely on WP3, tr[Pi_flag Lambda^WP(rho)] is the weight the channel puts in
the flag sector: 0 at rho = |0><0|, 1 at rho = |psi_0><psi_0|, 1/2 at the mixed
input of WP3-stat-mixed (9/50 + 8/25 = 25/50), and 16/25 at the coherent input
of WP3-stat-coherent (144/625 + 256/625 = 400/625). All four lie in [0, 1].""",
)

CERT_IDENTITY_PROBE = CertificateCase(
    case_id="PROBE22-cert-identity",
    claims=("PR3", "PR6"),
    instance="PROBE22",
    certificate_kind="identity",
    ohat=None,
    pullback=None,
    relation="=",
    constant=F(2, 3),
    sound=True,
    derivation="""\
THE IDENTITY CERTIFICATE, Corollary cor:pullback (i), on the operator Remark
rem:unsound names: O^ = sum_y F_(y,t0) with c = q_t0 = 2/3.

On the PROBE22 instance (Group PR-D) the target is Q = C^1 (+) C^4 with V
ordered (y0t0, y1t0, y0t1, y1t1), and
    sum_y F_(y,t0) = [2/3] (+) diag(7/9, 7/9, 1/3, 1/3) ,
which is NOT (2/3) 1_Q: the flag sector carries 7/9 and 1/3, neither equal to
2/3. Its PULL-BACK, however, is exactly (2/3) 1_B:
    Lambda^WP+(sum_y F_(y,t0))
      = [2/3] (+) ( (7/9)M'_(y0t0) + (7/9)M'_(y1t0)
                    + (1/3)M'_(y0t1) + (1/3)M'_(y1t1) )
      = [2/3] (+) ( (7/9)diag(0,3/4) + (7/9)diag(3/4,0)
                    + (1/3)diag(0,1/4) + (1/3)diag(1/4,0) )
      = [2/3] (+) diag(7/12 + 1/12, 7/12 + 1/12)
      = [2/3] (+) (2/3) 1_2  =  (2/3) 1_B ,
because sum_y M_(y,t0) = q_t0 1_B is an operator identity of the PHYSICAL model
-- "the weight q_t is Bob's own" (Remark rem:unsound).

WHAT THIS BUYS AND WHAT IT DOES NOT. Corollary cor:pullback (i) turns it into
the SOUND constraint tr[(sum_y F_(y,t0)) sigma] = 2/3 on every reachable sigma;
that is an EXPECTATION identity. It does NOT license the OPERATOR identity on
Q, which is false -- and PROBE22-UNSOUND freezes a reachable state on which the
operator form fails. Section 2.3 records that this entry is not emitted by
default on either route but "remains AVAILABLE ON REQUEST: it is the entry
O^ = sum_y F_(y,t), relation =, c = q_t of Theorem thm:licence", on the
LICENSED route, its constant q_t being declared before the run (A-CONST).""",
    superseded_by="0.2.0",
    superseded_site=(
        "rem:unsound as narrowed (F-5-01); Section 4.13's "
        "constraint-certificate row; eq:branchprobeweight"
    ),
    superseded_replacement=(
        "TOL2-branchprobe-pass",
        "TOL2-branchprobe-fail-exact-povm",
    ),
)

CERT_TWO_SECTOR = CertificateCase(
    case_id="WP3-cert-two-sector",
    claims=("PR3", "PR6"),
    instance="WP3-fss",
    certificate_kind="positivity",
    ohat=diag_matrix((0, F(3, 4), F(-1, 4))),
    pullback=(
        (gz(0), gz(0), gz(0)),
        (gz(0), gz(F(9, 40)), gz(0, F(-3, 10))),
        (gz(0), gz(0, F(3, 10)), gz(F(2, 5))),
    ),
    relation=">=",
    constant=F(0),
    sound=True,
    derivation="""\
Eq. eq:two-sector-entry, the a > 0 entry of Remark rem:published:
    O^ = F^FSS_e - a Pi_<=N - b Pi_flag,
    a = lmin(blk M^{<=N}_e),  b = lmin(blk M^{>N}_e) .
At e = v0 on WP3: a = lmin([2/3]) = 2/3 and b = lmin(blk M^{>N}_v0) = 1/4, the
above-cutoff block having eigenvalues 5/8 + 1/4 = 7/8 and 0 + 1/4 = 1/4. So
    O^ = diag(2/3, 1, 0) - (2/3)diag(1,0,0) - (1/4)diag(0,1,1)
       = diag(0, 3/4, -1/4) ,
and the pull-back is
    M_v0 - (2/3)Pi_<=N - (1/4)Pi_>N
      = (blk M^{<=N}_v0 - (2/3)1) (+) (blk M^{>N}_v0 - (1/4)1)
      = [0] (+) (5/8) M'_v0  >=  0 ,
"by the definitions of a and b and the transported projectors of
eq:transportproj".

THE COMPARISON WITH THE a = 0 ENTRY, and it runs in the direction Remark
rem:published states rather than the naive one. With
O^|_{a=0} = F^FSS_v0 - (1/4)Pi_flag = diag(2/3, 3/4, -1/4) one has
O^ = O^|_{a=0} - a Pi_<=N with a >= 0 and Pi_<=N >= 0, so
tr[O^|_{a=0} sigma] >= tr[O^ sigma] for every sigma >= 0, hence
    {sigma : tr[O^ sigma] >= 0} SUBSET {sigma : tr[O^|_{a=0} sigma] >= 0} :
THE a > 0 ENTRY CUTS THE STRICTLY SMALLER SET AND IS THE STRONGER CONSTRAINT,
UNCONDITIONALLY.

A WITNESS OF STRICTNESS, frozen so that the inclusion is proper and not merely
asserted. At sigma = (1/2)|q><q| + (1/2)|f_v1><f_v1|:
    tr[O^|_{a=0} sigma] = (1/2)(2/3) + (1/2)(-1/4) = 1/3 - 1/8 = 5/24 >= 0 ,
    tr[O^        sigma] = (1/2)(0)   + (1/2)(-1/4) = -1/8 < 0 .
So sigma satisfies the DEFAULT entry and VIOLATES the a > 0 one.

WHAT MAY NEVER BE EMITTED, transcribed because it is a live hazard: the CAP
form of the published inequality, W <= (p(e) - a)/(b - a), "contains the run's
OBSERVED p(e), and Assumption A-CONST admits only constants declared before the
run. The admissible object is the OPERATOR ENTRY eq:two-sector-entry with relation >=
and c = 0, of which the cap is a run-time consequence and not a declaration."
Nothing in this registry freezes a cap.""",
    superseded_by="0.2.0",
    superseded_site=(
        "cor:tolentries (iv), eq:tolgeneral; Section 2.3 "
        "constraint_list clause (d); rem:published closing sentence "
        "as amended"
    ),
    superseded_replacement=("TOL_ENTRY_TWO_SECTOR",),
)

CERTIFICATE_CASES: tuple[CertificateCase, ...] = (
    CERT_POSITIVITY,
    CERT_SPECTRAL,
    CERT_IDENTITY_PROBE,
    CERT_TWO_SECTOR,
)

#: cor:sound (ii)-(iii): an arbitrary intersection of sound families is sound,
#: and soundness is established once per constraint and never again for the
#: combination -- PROVIDED they are sound FOR ONE AND THE SAME CHANNEL.
INTERSECTION_CASE: dict[str, str] = {
    "case_id": "WP3-intersection",
    "claims": "PR3",
    "families": "WP3-cert-positivity and WP3-cert-spectral, both for Lambda^FSS",
    "in_both": "sigma = |q><q|: tr[O^_pos sigma] = 2/3 >= 0 and "
    "tr[Pi_flag sigma] = 0 in [0, 1]",
    "in_spectral_only": "sigma = |f_v1><f_v1|: tr[Pi_flag sigma] = 1 in [0, 1] "
    "but tr[O^_pos sigma] = -1/4 < 0",
    "conclusion": "the intersection is strictly smaller than either family and "
    "is sound by cor:sound (ii); cor:sound (iv) adds that the tightest sound "
    "family is S^rch itself and the loosest is the whole state set, so "
    "enlarging a sound family costs TIGHTNESS AND NEVER SOUNDNESS",
    "common_channel_requirement": "Remark rem:channel-choice (c). Both families "
    "above are certified against Lambda^FSS. WP3-isometric and TIGHT below "
    "freeze what happens when they are not.",
}


# ===========================================================================
#  Group PR-D -- the calculus (PR4), and the PROBE22 instance
# ===========================================================================
#
#  PROBE22 carries the private probe setting, which WP3 does not: it is the
#  instance Lemma lem:linear (ii), Assumption A-TSM and Remark rem:unsound all
#  need. Y = {y0, y1}, T = {t0, t1}, q = (2/3, 1/3) -- NON-DYADIC on purpose --
#  so V = Y x T has FOUR elements, ordered with Y MAJOR as Section 2.5's
#  `subsystem_order` requires: (y0,t0), (y1,t0), (y0,t1), (y1,t1).
#
#  The channel system is C = C_<=N (+) C_>N with dim 1 and dim 2. THE
#  ABOVE-CUTOFF BLOCK IS TWO-DIMENSIONAL ON PURPOSE: with a one-dimensional one
#  the flag output of Lambda^WP would be a single fixed distribution and the
#  reachable set would be a segment, on which the unsound operator transplant
#  below happens not to bite. Two dimensions make the reachable flag
#  distributions vary, and the counterexample becomes a genuine one.

#: The conditional POVMs {M_{y|t}}, complete for EACH FIXED t
#: (SYMBOLS.md Section 2.6): a BAR is a conditional POVM.
PROBE22_CONDITIONAL: tuple[tuple[str, str, F, tuple[F, F]], ...] = (
    ("y0", "t0", F(3, 4), (F(1, 4), F(3, 4))),
    ("y1", "t0", F(1, 4), (F(3, 4), F(1, 4))),
    ("y0", "t1", F(1, 2), (F(1, 3), F(2, 3))),
    ("y1", "t1", F(1, 2), (F(2, 3), F(1, 3))),
)

#: The declared probe weights. q_t > 0 and sum_t q_t = 1 (A-PROBE).
PROBE22_Q: tuple[tuple[str, F], ...] = (("t0", F(2, 3)), ("t1", F(1, 3)))

#: The declared order of V = Y x T, Y MAJOR.
PROBE22_V: tuple[tuple[str, str], ...] = (
    ("y0", "t0"),
    ("y1", "t0"),
    ("y0", "t1"),
    ("y1", "t1"),
)

#: The JOINT family M_(y,t) = q_t M_{y|t} of Section 2.2 step 2, as
#: (outcome, preserved block, above-cutoff diagonal) triples. A COMMA denotes a
#: joint outcome (Section 2.5, `povm_index_convention`).
PROBE22_JOINT: tuple[tuple[tuple[str, str], F, tuple[F, F]], ...] = (
    (("y0", "t0"), F(1, 2), (F(1, 6), F(1, 2))),
    (("y1", "t0"), F(1, 6), (F(1, 2), F(1, 6))),
    (("y0", "t1"), F(1, 6), (F(1, 9), F(2, 9))),
    (("y1", "t1"), F(1, 6), (F(2, 9), F(1, 9))),
)

#: Certified weights, one per JOINT outcome (Definition def:targets is
#: multi-bound), each equal to the minimum eigenvalue of its above-cutoff block.
PROBE22_WEIGHTS: tuple[tuple[tuple[str, str], F], ...] = (
    (("y0", "t0"), F(1, 6)),
    (("y1", "t0"), F(1, 6)),
    (("y0", "t1"), F(1, 9)),
    (("y1", "t1"), F(1, 9)),
)
PROBE22_TOTAL_WEIGHT: F = F(5, 9)

#: M'_v = (blk M^{>N}_v - p_v 1)/(1 - p) with 1 - p = 4/9, so the factor is 9/4.
PROBE22_MPRIME: tuple[tuple[tuple[str, str], tuple[F, F]], ...] = (
    (("y0", "t0"), (F(0), F(3, 4))),
    (("y1", "t0"), (F(3, 4), F(0))),
    (("y0", "t1"), (F(0), F(1, 4))),
    (("y1", "t1"), (F(1, 4), F(0))),
)

#: F^WP_v = blk M^{<=N}_v (+) (p_v 1_4 + (4/9)|v><v|), as
#: (outcome, preserved entry, four flag diagonal entries).
PROBE22_TARGET: tuple[tuple[tuple[str, str], F, tuple[F, F, F, F]], ...] = (
    (("y0", "t0"), F(1, 2), (F(11, 18), F(1, 6), F(1, 6), F(1, 6))),
    (("y1", "t0"), F(1, 6), (F(1, 6), F(11, 18), F(1, 6), F(1, 6))),
    (("y0", "t1"), F(1, 6), (F(1, 9), F(1, 9), F(5, 9), F(1, 9))),
    (("y1", "t1"), F(1, 6), (F(1, 9), F(1, 9), F(1, 9), F(5, 9))),
)

#: sum_y F_(y,t0), diagonal on Q = C^1 (+) C^4: the operator Remark rem:unsound
#: is about. The PRESERVED entry is q_t0 = 2/3; THE FLAG ENTRIES ARE NOT.
PROBE22_SUM_T0: tuple[F, ...] = (F(2, 3), F(7, 9), F(7, 9), F(1, 3), F(1, 3))

#: The reachable flag distribution of Lambda^WP at the first above-cutoff basis
#: vector: the (0,0) entries of the four M'_v.
PROBE22_REACHABLE_FLAG: tuple[F, ...] = (F(0), F(3, 4), F(0), F(1, 4))

PROBE22 = {
    "instance_id": "PROBE22",
    "claims": ("PR3", "PR4", "PR6"),
    "alphabet": PROBE22_V,
    "probe_weights": PROBE22_Q,
    "conditional": PROBE22_CONDITIONAL,
    "joint": PROBE22_JOINT,
    "weights": PROBE22_WEIGHTS,
    "total_weight": PROBE22_TOTAL_WEIGHT,
    "mprime": PROBE22_MPRIME,
    "target": PROBE22_TARGET,
    "target_dim": 5,
    "channel_preserved_dim": 1,
    "channel_above_cutoff_dim": 2,
    "derivation": """\
LEMMA lem:linear (ii), THE PRIVATE CLASSICAL VARIABLE. Each {M_{y|t}}_y is
complete for its own t -- (3/4 + 1/4) on the preserved block and
(1/4 + 3/4, 3/4 + 1/4) on the above-cutoff one at t0, likewise at t1 -- and the
joint family {q_t M_{y|t}} is a POVM over V because
    sum_{y,t} q_t M_{y|t} = sum_t q_t 1 = 1 .
Checked entry by entry: preserved 1/2 + 1/6 + 1/6 + 1/6 = 1; above-cutoff
(0,0) 1/6 + 1/2 + 1/9 + 2/9 = 3/18 + 9/18 + 2/18 + 4/18 = 1; (1,1) likewise.

WHAT (ii) COSTS, AND IT IS NOTHING: "the private variable never enters Q: the
target space is unchanged, no block is opened, and NO CONSTRAINT IS PRODUCED,
the weights q_t being carried by the target effects themselves". Contrast the
branching rule of Section 4.5, which files its classical variable IN Q and does
cost something -- Group PR-E freezes that side.

CERTIFIED WEIGHTS. p_v = lmin(blk M^{>N}_v) exactly: 1/6, 1/6, 1/9, 1/9, with
total p = 2/6 + 2/9 = 3/9 + 2/9 = 5/9 < 1, so Section 4.13's
`total_weight_not_below_one` test PASSES. Then
M'_v = (9/4)(blk M^{>N}_v - p_v 1) gives diag(0, 3/4), diag(3/4, 0),
diag(0, 1/4), diag(1/4, 0), which sum to diag(1, 1) as Proposition
prop:chain (i) requires of a POVM on the above-cutoff block.

THE TARGET. F^WP_v = blk M^{<=N}_v (+) (p_v 1_4 + (4/9)|v><v|); at v = (y0,t0)
the flag diagonal is (1/6 + 4/9, 1/6, 1/6, 1/6) = (3/18 + 8/18, ...)
= (11/18, 1/6, 1/6, 1/6). Column sums: 11/18 + 3/18 + 2/18 + 2/18 = 1.

dim H(Q) = 1 + 4 = 5, which is Theorem thm:blinding (iii)'s formula at
|Blmode| = 1: sum_{m<=N} dim H(C_m) + |Blmode| |V| = 1 + 1*4 = 5.""",
}

#: THE UNSOUND OPERATOR-FORM TRANSPLANT, Remark rem:unsound, with the numbers
#: that show it fails. Frozen as a dict because what is pinned is a
#: CONTRADICTION, not a value.
PROBE22_UNSOUND: dict[str, object] = {
    "case_id": "PROBE22-unsound-transplant",
    "claims": ("PR3", "PR6"),
    "refusal_reason": "unsound_constraint_requested",
    "physical_identity": "sum_y M_(y,t0) = q_t0 1_B = (2/3) 1_B, TRUE on B",
    "target_operator": PROBE22_SUM_T0,
    "target_identity_would_be": F(2, 3),
    "reachable_state": PROBE22_REACHABLE_FLAG,
    "projector": "Pi = |f_(y1,t0)><f_(y1,t0)|",
    "operator_form_lhs": F(7, 12),
    "operator_form_rhs": F(1, 2),
    "expectation_form_value": F(2, 3),
    "derivation": """\
THE PHYSICAL IDENTITY IS TRUE: sum_y M_(y,t0) = q_t0 1_B, "because the weight
q_t is Bob's own". On the preserved block 1/2 + 1/6 = 2/3; on the above-cutoff
block 1/6 + 1/2 = 2/3 and 1/2 + 1/6 = 2/3.

THE TRANSPLANTED OPERATOR IDENTITY IS FALSE. Summing the target elements over y
at t = t0:
    sum_y F_(y,t0) = [1/2 + 1/6] (+) diag(11/18 + 1/6, 1/6 + 11/18,
                                          1/6 + 1/6,   1/6 + 1/6)
                   = [2/3] (+) diag(7/9, 7/9, 1/3, 1/3) ,
whereas q_t0 1_Q would be (2/3) 1_5 = diag(2/3, 2/3, 2/3, 2/3, 2/3). THE
PRESERVED ENTRY MATCHES AND THE FLAG SECTOR DOES NOT -- 7/9 != 2/3 and
1/3 != 2/3 -- which is exactly the sentence "the squashed operators generally
satisfy only Lambda+(sum_y F_(y,t)) = q_t 1_B, while
sum_y F_(y,t) != q_t 1_Q ON THE FLAG SECTOR of a flag-shaped target".

THE SOUND FORM HOLDS. The pull-back is (2/3) 1_B -- computed in
PROBE22-cert-identity -- so Corollary cor:pullback (i) gives the EXPECTATION
identity tr[(sum_y F_(y,t0)) sigma] = 2/3 on every reachable sigma. Check it on
the reachable flag state sigma = Lambda^WP(|1><1|), whose flag distribution is
the first column of the four M'_v, namely (0, 3/4, 0, 1/4):
    (7/9)(0) + (7/9)(3/4) + (1/3)(0) + (1/3)(1/4) = 7/12 + 1/12 = 8/12 = 2/3 .

THE TRANSPLANT EXCLUDES THAT REACHABLE STATE. The operator identity implies
tr[(sum_y F_(y,t0)) Pi sigma Pi] = q_t0 tr[Pi sigma Pi] for every projector Pi.
Take Pi = |f_(y1,t0)><f_(y1,t0)|, so Pi sigma Pi = (3/4) Pi:
    LHS = (7/9)(3/4) = 7/12 ,      RHS = (2/3)(3/4) = 1/2 = 6/12 .
7/12 != 6/12, so THE REACHABLE STATE VIOLATES THE TRANSPLANTED CONSTRAINT,
Eq. eq:inclusion fails, and Theorem thm:transfer is voided -- "A SECURITY BREAK
RATHER THAN A RATE LOSS". Version 1 therefore REFUSES the operator form with
`unsound_constraint_requested` (Section 4.13, last row).""",
}

#: Lemma lem:linear (i), post-processing by a column-stochastic matrix, applied
#: to BOTH SIDES AT ONCE -- which is why Section 2.2 puts the dark-count channel
#: and the coarse-graining BEFORE the first squashing link.
POSTPROCESSING_CASE: dict[str, object] = {
    "case_id": "WP3-postprocessing",
    "claims": ("PR4",),
    "matrix": (
        ("u0", "v0", F(2, 3)),
        ("u0", "v1", F(1, 4)),
        ("u1", "v0", F(1, 3)),
        ("u1", "v1", F(3, 4)),
    ),
    "pf_u0_diagonal": (F(19, 36), F(59, 96), F(17, 48)),
    "pm_u0": (
        (gz(F(19, 36)), gz(0), gz(0)),
        (gz(0), gz(F(43, 96)), gz(0, F(-1, 8))),
        (gz(0), gz(0, F(1, 8)), gz(F(25, 48))),
    ),
    "pf_u1_diagonal": (F(17, 36), F(37, 96), F(31, 48)),
    "derivation": """\
P(z|v) is column-stochastic: 2/3 + 1/3 = 1 and 1/4 + 3/4 = 1. Lemma
lem:linear (i) says both post-processed families are POVMs and
(PM) <= (PF) via the SAME channel.

(PF)_u0 = (2/3) F^WP_v0 + (1/4) F^WP_v1, diagonal entry by entry:
    preserved  (2/3)(2/3) + (1/4)(1/3) = 4/9 + 1/12 = 16/36 + 3/36 = 19/36
    flag 0     (2/3)(7/8) + (1/4)(1/8) = 7/12 + 1/32 = 56/96 + 3/96 = 59/96
    flag 1     (2/3)(1/4) + (1/4)(3/4) = 1/6 + 3/16  = 8/48 + 9/48  = 17/48
(PM)_u0 = (2/3) M_v0 + (1/4) M_v1:
    preserved  19/36, as above
    (0,0)      (2/3)(19/40) + (1/4)(21/40) = 19/60 + 21/160
               = 152/480 + 63/480 = 215/480 = 43/96
    (0,1)      (2/3)(-3i/10) + (1/4)(3i/10) = -8i/40 + 3i/40 = -i/8
    (1,1)      (2/3)(13/20) + (1/4)(7/20) = 13/30 + 7/80
               = 104/240 + 21/240 = 125/240 = 25/48
AND THE ADJOINT REPRODUCES IT: eq:WPadjoint at the flag diagonal (59/96, 17/48)
= (59/96, 34/96) gives, over the denominator 2400,
    (0,0) (59*9 + 34*16)/2400 = (531 + 544)/2400 = 1075/2400 = 43/96
    (0,1) 12i(-59 + 34)/2400  = -300i/2400 = -i/8
    (1,1) (59*16 + 34*9)/2400 = (944 + 306)/2400 = 1250/2400 = 25/48
so Lambda^WP+((PF)_u0) = (PM)_u0 exactly.

WHAT (i) DOES NOT SAY, Remark rem:intertwining: it does NOT say a classical map
applied before a FIXED squasher may be moved across it. That asks whether
P' M = P M has a stochastic solution P', "a linear feasibility problem in P'
that has NO SOLUTION IN GENERAL". Version 1 never asks it: the order of
Section 2.2 is fixed and a request to squash first is refused with
`post_processing_order_violated`.""",
}

#: Proposition prop:pinching and Corollary cor:blockdiag on the BLIND2 target.
PINCHING_CASE: dict[str, object] = {
    "case_id": "BLIND2-pinching",
    "claims": ("PR4", "PR9"),
    "sectors": (
        ("nb", 0),
        ("nb", "a"),
        ("nb", "b"),
        ("bl1", "a"),
        ("bl1", "b"),
    ),
    "sector_dims": (1, 1, 1, 1, 1),
    "derivation": """\
Proposition prop:pinching: for mutually orthogonal projections summing to 1_Q,
P_S(sigma) = sum_s Pi_s sigma Pi_s is a channel with P_S+ = P_S, and if every
F_v is block diagonal then F <= F via P_S. On BLIND2 every emitted F_v is
DIAGONAL in the target basis -- Theorem thm:blinding (iii) proves it, and the
frozen matrices show it -- so P_S+ FIXES each of them and
    Lambda = P_S o [ (+)_b Lambda_b o I_b ]
realizes the SAME relation as the bracket alone (Corollary cor:blockdiag (i)).

WHY IT IS EMITTED ANYWAY. Corollary cor:blockdiag (ii)-(iii): every state
reachable through P_S o Lambda is block diagonal in each round, so
"sigma is block diagonal in every round's sector decomposition" is a SOUND
constraint FOR THAT CHANNEL, and the squashed analysis may be restricted to
block-diagonal states without excluding a reachable one. "The artifact emits
P_S o Lambda as its channel witness, so that the block-diagonality restriction
and every other emitted constraint are sound for ONE channel, as Remark
rem:channel-choice requires." The sector pinching is therefore COMPOSED LAST
(Eq. eq:blindchannel), which is what `composition_order` records as data.""",
}

#: Lemma lem:obstructions, both legs, each with a refusing and a passing case.
OBSTRUCTION_CASES: tuple[dict[str, object], ...] = (
    {
        "case_id": "obstruction-i-refuse",
        "claims": ("PR4", "PR6"),
        "leg": "spectral inclusion",
        "refusal_reason": "declared_relation_impossible",
        "physical_norm": F(1),
        "target_norm": F(1, 2),
        "derivation": """\
Proposition prop:chain (iv)'s own counterexample, frozen: at
dim H(B_<=N) = dim H(B_>N) = 1 and V = {1, 2},
    M_1 = 1/2 (+) 1 ,  M_2 = 1/2 (+) 0 ,  p_1 = 1/2 ,  p_2 = 0 ,
so Eq. eq:certweights holds (1 >= 1/2 and 0 >= 0) and p = 1/2 < 1. Then
    F^FSS_2 = 1/2 (+) diag(0, 1)                  ,  ||F^FSS_2|| = 1 ,
    F^WP_2  = 1/2 (+) (0*1_2 + (1/2)diag(0,1))    ,  ||F^WP_2||  = 1/2 ,
and F^WP_1 = 1/2 (+) diag(1/2 + 1/2, 1/2) = 1/2 (+) diag(1, 1/2) completes the
target POVM (1 + 0 = 1 and 1/2 + 1/2 = 1 on the flag diagonal).

A DECLARED RELATION F^FSS <= F^WP IS REFUSED BY INSPECTION: Lemma
lem:obstructions (i) with F^FSS in the physical role would force
||F^FSS_2|| <= ||F^WP_2||, i.e. 1 <= 1/2. So the reverse relation FAILS, and
Proposition prop:chain (ii) with Corollary cor:monotone says which direction is
which: F^FSS is STRICTLY CLEANER than F^WP, so it hands the adversary more.""",
    },
    {
        "case_id": "obstruction-i-pass",
        "claims": ("PR4", "PR6"),
        "leg": "spectral inclusion",
        "refusal_reason": None,
        "physical_norm": F(7, 8),
        "target_norm": F(7, 8),
        "derivation": """\
The same test on the relation WP3 actually declares, M <= F^WP. The norms are
read off the eigenvalues computed in Group PR-A:
    ||M_v0||     = max(2/3, 7/8, 1/4) = 7/8   [blk M^{>N}_v0 has 7/8 and 1/4]
    ||F^WP_v0||  = max(2/3, 7/8, 1/4) = 7/8
    ||M_v1||     = max(1/3, 3/4, 1/8) = 3/4
    ||F^WP_v1||  = max(1/3, 1/8, 3/4) = 3/4
The test PASSES, and TIGHTLY at both outcomes -- which is not an accident:
Eq. eq:WPadjoint sends the flag diagonal entry (F^WP_v)_{f_v f_v} = p_v + (1-p)
to the coefficient of M'_v, and the largest eigenvalue of blk M^{>N}_v is
exactly (1-p) + p_v. A LOOSE PASS WOULD HAVE BEEN A WEAKER FIXTURE.""",
    },
    {
        "case_id": "obstruction-ii-refuse",
        "claims": ("PR4",),
        "leg": "span monotonicity",
        "refusal_reason": "declared_relation_impossible",
        "physical_norm": None,
        "target_norm": None,
        "derivation": """\
Lemma lem:obstructions (ii): dim span{M_v} <= dim span{F_v} <= (dim H(Q))^2,
and "every linear relation sum_v a_v F_v = c 1_Q FORCES sum_v a_v M_v = c 1_B".

THE COUNTEREXAMPLE. On H(B) = H(Q) = C^2 with V = {v0, v1}, declare
    M_v0 = |0><0| ,  M_v1 = |1><1| ,   F_v0 = F_v1 = 1/2 .
Both are POVMs. The target satisfies the linear relation F_v0 - F_v1 = 0 * 1_Q
with (a_v0, a_v1) = (1, -1) and c = 0, so unitality of Lambda+ would force
M_v0 - M_v1 = 0 * 1_B. But M_v0 - M_v1 = diag(1, -1) != 0. REFUSED, with
`declared_relation_impossible`, BEFORE ANY CONSTRUCTION IS ATTEMPTED.
Equivalently by the dimension count: dim span{M_v} = 2 > 1 = dim span{F_v}.

THE PASSING LEG on WP3: dim span{M_v0, M_v1} = 2 (their preserved entries 2/3
and 1/3 differ while their above-cutoff blocks are not proportional, so neither
is a multiple of the other), dim span{F^WP_v0, F^WP_v1} = 2 likewise, and
2 <= 2 <= 9 = (dim H(Q))^2. The only linear relation among the targets is
F^WP_v0 + F^WP_v1 = 1_Q, which forces M_v0 + M_v1 = 1_B -- TRUE, both being
POVMs.""",
    },
)


# ===========================================================================
#  Group PR-E -- the branching rule (PR5)
# ===========================================================================

#: Corollary cor:instances (i), the convex mixture with a KNOWN weight q = 1/4:
#: M_v = (1-q) G_v + q R_v with G characterized and R ARBITRARY.
BRANCH_MIXTURE: dict[str, object] = {
    "case_id": "BRANCH-convex",
    "claims": ("PR5",),
    "q": F(1, 4),
    "g_povm": (("v0", diag_matrix((1, 0))), ("v1", diag_matrix((0, 1)))),
    "r_povm": (
        ("v0", diag_matrix((F(1, 2), F(1, 2)))),
        ("v1", diag_matrix((F(1, 2), F(1, 2)))),
    ),
    "physical": (
        ("v0", diag_matrix((F(7, 8), F(1, 8)))),
        ("v1", diag_matrix((F(1, 8), F(7, 8)))),
    ),
    "target": (
        ("v0", diag_matrix((1, 0, 1, 0))),
        ("v1", diag_matrix((0, 1, 0, 1))),
    ),
    "branch_weight_operator_form": (
        ("branch 1 (characterized)", "Lambda+(Pi_1) = (3/4) 1_B"),
        ("branch 2 (flag)", "Lambda+(Pi_flag) = (1/4) 1_B"),
    ),
    "branch_weight_scalar_form": (("Pi_1", F(3, 4)), ("Pi_flag", F(1, 4))),
    "derivation": """\
Take G_v0 = |0><0|, G_v1 = |1><1| on C^2 (squashed by the IDENTITY, so
Lambda_G = id and F^(G) = G), and R_v = 1/2 for both v -- the UNCHARACTERIZED
branch, about which nothing is assumed. Then
    M_v0 = (3/4)|0><0| + (1/4)(1/2) = diag(3/4 + 1/8, 1/8) = diag(7/8, 1/8)
    M_v1 = (3/4)|1><1| + (1/4)(1/2) = diag(1/8, 7/8) ,
a POVM. The target is {G_v (+) |v><v|_flag} on C^2 (+) C^2, i.e.
diag(1, 0, 1, 0) and diag(0, 1, 0, 1), which sum to 1_4.

Lemma lem:master with I_1 = (3/4) id and I_2 = (1/4) id gives, by part (iii)
(coarse-graining the branch label away),
    Lambda+(G_v (+) |v><v|) = I_1+(Lambda_G+(G_v)) + I_2+(Lmp+(|v><v|))
                            = (3/4) G_v + (1/4) R_v = M_v .

THE BRANCH-WEIGHT CONSTRAINT, AND WHICH FORM TO IMPOSE. Part (iv) gives
Lambda+(Pi_j) = I_j+(1) = q_j 1_B, so BOTH forms are available. Remark
rem:reading-master says which is worth imposing: "the OPERATOR form is the one
worth imposing: it says the weight of block j is q_j CONDITIONED ON EVERYTHING
ALICE AND EVE HOLD... The SCALAR tr[Pi_j sigma] = q_j is ONLY ITS TRACE and is
STRICTLY WEAKER -- it still admits a squashed state whose block index is
PERFECTLY CORRELATED WITH EVE'S REGISTER." Both are frozen above so that an
implementation emitting only the scalar is observably weaker.

WHAT THE RULE DOES NOT MODEL, Remark rem:master-scope: the branch label ends up
as a BLOCK INDEX of Q, "and Q is the system the squashed model hands to the
adversary", so lem:master models a branch EVE MAY AS WELL KNOW. A setting Bob
draws PRIVATELY belongs to Lemma lem:linear (ii) instead -- PROBE22 above --
"and swapping the two would be a MODELLING ERROR in the direction of giving Eve
a register she does not have or withholding one she does".""",
}

#: Lemma lem:top: EVERY POVM squashes to a flag PVM, so existence is never the
#: difficulty. Frozen on the same two-outcome POVM.
TOP_ELEMENT: dict[str, object] = {
    "case_id": "TOP-flag-pvm",
    "claims": ("PR5",),
    "physical": (
        ("v0", diag_matrix((F(7, 8), F(1, 8)))),
        ("v1", diag_matrix((F(1, 8), F(7, 8)))),
    ),
    "target": (("v0", diag_matrix((1, 0))), ("v1", diag_matrix((0, 1)))),
    "channel_action": (
        ("|0><0|", (F(7, 8), F(1, 8))),
        ("|1><1|", (F(1, 8), F(7, 8))),
        ("|+><+|", (F(1, 2), F(1, 2))),
    ),
    "derivation": """\
Eq. eq:mpsquasher: Lmp(rho) = sum_v tr[M_v rho] |v><v| is a measure-and-prepare
channel, trace preserving because sum_v tr[M_v rho] = tr rho, and its adjoint is
Lmp+(X) = sum_v <v|X|v> M_v, which at X = |v'><v'| returns M_v'. Evaluated on
three inputs:
    |0><0| -> (tr[M_v0|0><0|], tr[M_v1|0><0|]) = (7/8, 1/8)
    |1><1| -> (1/8, 7/8)
    |+><+| -> ((7/8 + 1/8)/2, (1/8 + 7/8)/2) = (1/2, 1/2)
the last because M_v0 and M_v1 are DIAGONAL, so the coherence of |+><+|
contributes nothing.

WHAT THIS MEANS, and it is the sentence that tells a reader what the work in
Sections 4.6-4.9 actually is: "SO EVERY POVM SQUASHES TO A FLAG PVM. A squashing
relation on its own is therefore WORTH NOTHING: the target P^flag lets the
adversary prepare a flag state and FIX BOB'S OUTCOME OUTRIGHT. What buys a key
rate is a target whose elements are not all rank-one projectors, or a sound
constraint that excludes the flag states an adversary would use."

THE GENERAL CASE of lem:top -- any PVM P with P_v = 0 => M_v = 0 -- is frozen
by the degenerate instance V = {v0, v1, v2} with P_v2 = 0 and M_v2 = 0, where
the constructed channel omits the v2 term and the identity reads 0 = 0.""",
}


# ===========================================================================
#  Group PR-F -- the FSS/WPFSS chain and the weights (PR6)
# ===========================================================================

#: Eq. eq:ladder: M <= F^WP <= F^FSS <= P^flag, with EXACT composition
#: Lambda^FSS = Lambda~ o Lambda^WP on ALL of T(B).
CHAIN_LADDER: dict[str, object] = {
    "case_id": "WP3-ladder",
    "claims": ("PR6",),
    "steps": (
        ("M", "F^WP", "Lambda^WP", "eq:Lwp"),
        ("F^WP", "F^FSS", "Lambda~", "eq:Lnoise"),
        ("F^FSS", "P^flag", "Lambda_mp", "eq:mpsquasher"),
    ),
    "mu": (F(1, 4), F(1, 8)),
    "noise_adjoint_check": (
        ("F^FSS_v0", (F(2, 3), F(7, 8), F(1, 4))),
        ("F^FSS_v1", (F(1, 3), F(1, 8), F(3, 4))),
    ),
    "composition_check": (
        ("|0><0|", (F(1), F(0), F(0)), (F(1), F(0), F(0))),
        ("|psi_0><psi_0|", (F(0), F(1), F(0)), (F(0), F(7, 8), F(1, 8))),
        (
            "(|0><0| + |1><1|)/2",
            (F(1, 2), F(9, 50), F(8, 25)),
            (F(1, 2), F(19, 80), F(21, 80)),
        ),
        (
            "|chi><chi|",
            (F(9, 25), F(144, 625), F(256, 625)),
            (F(9, 25), F(38, 125), F(42, 125)),
        ),
    ),
    "derivation": """\
Lambda~ of Eq. eq:Lnoise with p = 3/8 and mu = sum_v p_v |v><v| =
diag(1/4, 1/8) on the flag block. Its adjoint on block observables,
Eq. eq:L2adjoint, is
    Lambda~+(X_<=N (+) X_flag) = X_<=N (+) ((1-p) X_flag + tr[mu X_flag] 1) .
At F^FSS_v0, flag diagonal (1, 0): (5/8)diag(1,0) + (1/4)1 = diag(7/8, 1/4),
which with the preserved 2/3 is F^WP_v0. At F^FSS_v1, flag diagonal (0, 1):
(5/8)diag(0,1) + (1/8)1 = diag(1/8, 3/4), which is F^WP_v1. SO F^WP <= F^FSS
via Lambda~, and by Corollary cor:monotone the FSS target is the CLEANER one --
it hands the adversary more, which Proposition prop:chain (iv) confirms by
||F^FSS_2|| > ||F^WP_2|| in the counterexample frozen under
`obstruction-i-refuse`.

EXACT COMPOSITION, checked on four inputs INCLUDING one with coherence across
the cutoff. The pairs above are (Lambda^WP(rho) diagonal, Lambda^FSS(rho)
diagonal), and Lambda~ carries the first to the second:
  * |0><0|:            (1,0,0) -> (5/8 + 3/8)(1) = 1 in the preserved slot,
    flag zero;  Lambda^FSS gives (1,0,0). Equal.
  * |psi_0><psi_0|:    (0,1,0) -> (5/8)diag(1,0) + 1*mu
    = diag(5/8 + 1/4, 1/8) = (7/8, 1/8);  and
    Lambda^FSS gives <psi_0|blk M^{>N}_v|psi_0> = (7/8, 1/8). Equal.
  * the mixed input:   (1/2, 9/50, 8/25) -> preserved 1/2, flag
    (5/8)(9/50) + (1/2)(1/4) = 45/400 + 50/400 ... over 80:
    (5/8)(9/50) = 9/80 and (1/2)(1/4) = 10/80, total 19/80; the other
    (5/8)(8/25) + (1/2)(1/8) = 1/5 + 1/16 = 16/80 + 5/80 = 21/80.
    Lambda^FSS gives (1/2)(19/40) = 19/80 and (1/2)(21/40) = 21/80. Equal.
  * |chi><chi|:        (9/25, 144/625, 256/625) -> preserved 9/25, flag
    (5/8)(144/625) + (16/25)(1/4) = 720/5000 + 800/5000 = 1520/5000 = 38/125
    and (5/8)(256/625) + (16/25)(1/8) = 1280/5000 + 400/5000 = 42/125.
    Lambda^FSS: Pi_>N|chi> = (4/5)|1>, so the flag values are
    (16/25)(19/40) = 38/125 and (16/25)(21/40) = 42/125. Equal.
THE LAST CASE IS THE POINT: both maps DISCARD the coherence between |0> and
|1>, and the identity "holds for every rho, INCLUDING STATES WITH COHERENCES
ACROSS THE CUTOFF, WHICH BOTH SIDES DISCARD".

THE LAST RUNG is Lemma lem:top applied to F^FSS: every POVM squashes to the
flag PVM, so the ladder terminates at P^flag with nothing left to prove.""",
}

#: Proposition prop:chain (iii), the constraint the WPFSS ENCODES: an operator
#: inequality ON THE TARGET, true of every state the adversary could prepare.
ENCODED_CONSTRAINT: dict[str, object] = {
    "case_id": "WP3-encoded",
    "claims": ("PR6",),
    "wp_differences": (
        ("v0", diag_matrix((F(2, 3), F(5, 8), 0))),
        ("v1", diag_matrix((F(1, 3), 0, F(5, 8)))),
    ),
    "fss_failure_state": "sigma = |f_v1><f_v1|",
    "fss_failure_value": F(-1, 4),
    "derivation": """\
UNDER F^WP the device fact is an operator inequality on Q:
    F^WP_v - p_v Pi_flag = blk M^{<=N}_v (+) (1-p)|v><v| >= 0 ,
which at v0 is diag(2/3, 7/8 - 1/4, 1/4 - 1/4) = diag(2/3, 5/8, 0) and at v1 is
diag(1/3, 1/8 - 1/8, 3/4 - 1/8) = diag(1/3, 0, 5/8). Both are positive
semidefinite ON THE NOSE, so tr[F^WP_v sigma] >= p_v tr[Pi_flag sigma] holds on
EVERY squashed state, REACHABLE OR NOT -- "it needs NO CONSTRAINT, NO LICENCE
AND NO ATTESTATION".

UNDER F^FSS the same fact is only a PULL-BACK constraint. Its pull-back is
positive (frozen under WP3-cert-positivity), so it holds on every REACHABLE
state; but the target inequality itself FAILS, at sigma = |f_v'><f_v'| for
v' != v with p_v > 0:
    tr[(F^FSS_v0 - p_v0 Pi_flag) |f_v1><f_v1|] = 0 - 1/4 = -1/4 < 0 .

THIS IS THE WHOLE DIFFERENCE BETWEEN THE TWO ROUTES. "Under F^FSS the same fact
is true ONLY ON THE IMAGE, so it must travel as a declared constraint entry, and
SOMETHING MUST CERTIFY THAT THE ADVERSARY CANNOT LEAVE THE IMAGE -- which is
exactly Theorem thm:licence."  encoded route -> F^WP, CList empty, no licence;
licensed route -> F^FSS, one entry, licence required.""",
}

#: Remark rem:weightfree: any SMALLER weight is also valid, and gives a CLEANER
#: target -- proved, not asserted, by the channel Psi of Eq. eq:weightmono.
WEIGHT_FREEDOM: dict[str, object] = {
    "case_id": "WP3-weightfree",
    "claims": ("PR6",),
    "weights_used": ((("v0"), F(1, 4)), (("v1"), F(1, 8))),
    "smaller_weights": ((("v0"), F(1, 8)), (("v1"), F(0))),
    "lambda_coefficient": F(5, 7),
    "nu_diagonal": (F(1, 7), F(1, 7)),
    "smaller_target": (
        ("v0", (F(2, 3), F(1), F(1, 8))),
        ("v1", (F(1, 3), F(0), F(7, 8))),
    ),
    "derivation": """\
Take p' = (1/8, 0) <= p = (1/4, 1/8), so p' = 1/8 and p = 3/8. Eq. eq:weightmono
sets
    lambda = (1 - p)/(1 - p') = (5/8)/(7/8) = 5/7 ,
    nu     = sum_v ((p_v - p'_v)/(1 - p')) |v><v|
           = ((1/8)/(7/8)) |f_0><f_0| + ((1/8)/(7/8)) |f_1><f_1| = (1/7) 1_flag,
and the channel check is lambda + tr nu = 5/7 + 2/7 = 1.

THE SMALLER-WEIGHT TARGET is F^WP[p']_v0 = [2/3] (+) ((1/8)1 + (7/8)|f_0><f_0|)
= [2/3] (+) diag(1, 1/8), and F^WP[p']_v1 = [1/3] (+) diag(0, 7/8); they sum to
1_Q. Psi+ carries it back to the larger-weight one:
    Psi+(X_<=N (+) X_flag) = X_<=N (+) (lambda X_flag + tr[nu X_flag] 1) ,
at X_flag = diag(1, 1/8):
    (5/7)diag(1, 1/8) + (1/7)(1 + 1/8) 1 = diag(5/7, 5/56) + (9/56) 1
      = diag(40/56 + 9/56, 5/56 + 9/56) = diag(49/56, 14/56)
      = diag(7/8, 1/4)  =  the flag block of F^WP[p]_v0 ;
at X_flag = diag(0, 7/8):
    (5/7)diag(0, 7/8) + (1/7)(7/8) 1 = diag(0, 5/8) + (1/8) 1
      = diag(1/8, 3/4)  =  the flag block of F^WP[p]_v1 .
SO F^WP[p] <= F^WP[p'] VIA Psi, and by Corollary cor:monotone the SMALLER-WEIGHT
TARGET IS THE CLEANER ONE -- it hands the adversary more.

WHAT THE MODULE DOES WITH THAT: "The module therefore uses the LARGEST weight
the artifact certifies, RECORDS it, is FREE TO BE GIVEN A SMALLER ONE, and
NEVER SILENTLY SUBSTITUTES A LARGER ONE." Taking p' == 0 recovers the flag-noise
channel Lambda~ of eq:Lnoise, "as it must".""",
}

#: Lemma lem:ple1 and Remark rem:peqone: the p = 1 refusal, and why it is
#: CONSERVATIVE rather than an obstruction.
P_EQUALS_ONE: dict[str, object] = {
    "case_id": "PEQONE",
    "claims": ("PR6",),
    "refusal_reason": "total_weight_not_below_one",
    "weights": ((("1"), F(1)), (("2"), F(0))),
    "total": F(1),
    "forced_blocks": ((("1"), F(1)), (("2"), F(0))),
    "recoverable_target": (
        ("1", (F(1, 2), F(1), F(1))),
        ("2", (F(1, 2), F(0), F(0))),
    ),
    "smaller_admissible": ((("1"), F(1, 2)), (("2"), F(0))),
    "derivation": """\
Lemma lem:ple1 bounds any certified weight family by 0 <= p <= 1: summing
eq:certweights over v and using block completeness gives 1 >= p 1 on the
above-cutoff block. "Neither p_v < 0 nor sum_v p_v > 1 can be produced by a
valid weight family, so they are NOT ERROR PATHS BUT IMPOSSIBILITIES." THE
BOUNDARY p = 1 IS A GENUINE REFUSAL: eq:Lwp divides by 1 - p.

A DECLARATION THAT REACHES IT, on the one-dimensional-blocks instance:
    M_1 = 1/2 (+) 1 ,  M_2 = 1/2 (+) 0 ,   p_1 = 1 ,  p_2 = 0 ,  p = 1 ,
certified (1 >= 1 and 0 >= 0) and REFUSED with `total_weight_not_below_one`.

WHY THE REFUSAL COSTS NOTHING, Remark rem:peqone. At p = 1 the weights are
FORCED EXACT: summing eq:certweights gives sum_v (blk M^{>N}_v - p_v 1) = 0 with
every summand positive semidefinite, so EVERY SUMMAND VANISHES and
blk M^{>N}_v = p_v 1. The relation then still holds with the target
F_v = blk M^{<=N}_v (+) p_v 1_flag -- i.e. eq:WPFSS at 1 - p = 0, so
F_1 = 1/2 (+) diag(1,1) and F_2 = 1/2 (+) diag(0,0), summing to 1_Q -- realized
by Lambda(rho) = Pi_<= rho Pi_<= (+) tr[Pi_> rho Pi_>] mu with
mu = |1><1|_flag. Its adjoint sends X_<= (+) X_flag to
X_<= (+) tr[mu X_flag] 1, which at F_1 returns 1/2 (+) 1 = M_1 and at F_2
returns 1/2 (+) 0 = M_2. "SO p = 1 IS NOT AN OBSTRUCTION; version 1 simply does
not construct that map, refuses instead, and THE REFUSAL COSTS NOTHING THAT ANY
DECLARATION REACHING p = 1 COULD NOT ALSO OBTAIN BY LOWERING ONE WEIGHT
INFINITESIMALLY" -- here p_1 = 1/2 gives p = 1/2 < 1 and is admitted.

THE TEST RUNS ON BOTH ROUTES, DELIBERATELY. Section 4.13 records that on the
licensed route the witness is Lambda^FSS, "which performs NO SUCH DIVISION, so
there THE TEST IS STRICTER THAN THE MATHEMATICS REQUIRES; version 1 applies it
on both routes deliberately -- ONE VALIDITY RULE RATHER THAN TWO, fail-closed
and conservative". It also runs UNCONDITIONALLY, because where the above-cutoff
block is trivial the certified-weight condition is vacuous "and this test is the
only thing constraining p".""",
}


# ===========================================================================
#  Group PR-G -- flags are enough (PR7)
# ===========================================================================

FLAGS_ENOUGH: dict[str, object] = {
    "case_id": "FLAGS-ENOUGH",
    "claims": ("PR7",),
    "source_povm": (
        ("v0", diag_matrix((1, 0, 1, 0))),
        ("v1", diag_matrix((0, 1, 0, 1))),
    ),
    "target_povm": (
        ("v0", diag_matrix((F(1, 2), F(1, 2), 1, 0))),
        ("v1", diag_matrix((F(1, 2), F(1, 2), 0, 1))),
    ),
    "second_source_povm": (
        ("v0", diag_matrix((F(3, 4), F(1, 4), 1, 0))),
        ("v1", diag_matrix((F(1, 4), F(3, 4), 0, 1))),
    ),
    "zero_weight_block": "Lambda(rho) is supported entirely in H(flag): the "
    "B_0 block of every reachable state is 0",
    "distinguishability_before": (F(1), F(0)),
    "distinguishability_after": (F(1, 2), F(1, 2)),
    "derivation": """\
Corollary cor:flagsenough, Eq. eq:flagsenough, on B_0 = C^2 with
G_v0 = |0><0|, G_v1 = |1><1| and the admissible replacement
H_v = (1/|V|) 1_{B_0} = (1/2) 1_2 that the corollary names explicitly.

    Lambda(rho) = 0_{B_0} (+) sum_v tr[(G_v (+) |v><v|) rho] |v><v| ,
a measure-and-prepare channel, trace preserving because
sum_v (G_v (+) |v><v|) = 1_{B_0} (+) 1_flag. ITS OUTPUT IS SUPPORTED IN THE FLAG
BLOCK, so its adjoint reads only the flag part of an observable:
    Lambda+(X_{B_0} (+) X_flag) = sum_v <v|X_flag|v> (G_v (+) |v><v|) ,
"THE B_0-PART OF THE OBSERVABLE CONTRIBUTES NOTHING", and evaluating at
X_{B_0} = H_v, X_flag = |v><v| returns G_v (+) |v><v| exactly. Checked on both
target elements.

THE POINT: "THE SQUASHING CHANNEL DEPENDS ON G WHILE THE TARGET DOES NOT -- so
ONE TARGET COVERS EVERY DEVICE WITH THE SAME FLAG STRUCTURE." The second source
POVM above, G'_v0 = diag(3/4, 1/4) and G'_v1 = diag(1/4, 3/4), is a DIFFERENT
device with a DIFFERENT channel and THE SAME target.

WHAT IT COSTS, Remark rem:flagcost: "by Corollary cor:monotone the move is NOT
FREE IN RATE: the target of eq:flagsenough is CLEANER than the source, so it
hands the adversary more, and every squashed state it admits is a flag state as
far as the B_0 block is concerned." Frozen concretely: on a state supported in
the B_0 block the SOURCE elements distinguish the outcomes perfectly --
tr[(G_v0 (+) |v0><v0|)|0><0|] = 1 while the v1 element gives 0 -- and the TARGET
elements do not, both giving 1/2. THE INFORMATION IS GONE, and that is the
price.

WHAT IT BUYS: "G appears NOWHERE in the target: a branch whose device is
unknown, adversarially chosen, or infinite-dimensional is covered by ONE FINITE
TARGET. In Section 4.9 that branch is the BLINDED one, where by construction
nothing is assumed and NOTHING MAY BE."

WHY VERSION 1 STILL DOES NOT PAD. Corollary cor:flagsenough is what would make
Theorem thm:blinding (v)'s padded variant available, and Remark
rem:paddednotemitted declines it: the padded variant "rests on an EXTRA
HYPOTHESIS, that every {M_{v|bl_i}} be block diagonal at the cutoff, which
Definition def:blindmodel (c) and Assumption A-BLIND DELIBERATELY DECLINE TO
ASSUME". So this corollary is used HERE and not there.""",
}


# ===========================================================================
#  Group PR-H -- the register-conditioned mixture (PR8)
# ===========================================================================
#
#  The register POVM is NON-PROJECTIVE ON PURPOSE -- decision 6 of Section 1.1
#  removes the projectivity hypothesis, and a projective fixture could not show
#  it. It is also chosen so that its SQUARE ROOTS ARE EXACTLY RATIONAL, using
#  the Pythagorean triple again: N_j0 = diag(9/25, 16/25) has
#  N_j0^{1/2} = diag(3/5, 4/5). Nothing in the contract requires the square root
#  to be evaluable -- Section 2.3 calls the channel a symbolic constructor
#  record -- but making it exact here means Eq. eq:regchannel is checkable on
#  paper and not only through its adjoint.

MIXTURE_N_J0: Matrix = diag_matrix((F(9, 25), F(16, 25)))
MIXTURE_N_J1: Matrix = diag_matrix((F(16, 25), F(9, 25)))
MIXTURE_SQRT_J0: Matrix = diag_matrix((F(3, 5), F(4, 5)))
MIXTURE_SQRT_J1: Matrix = diag_matrix((F(4, 5), F(3, 5)))

MIXTURE_CASE: dict[str, object] = {
    "case_id": "MIXTURE-2branch",
    "claims": ("PR5", "PR8"),
    "register_povm": (("j0", MIXTURE_N_J0), ("j1", MIXTURE_N_J1)),
    "register_is_projective": False,
    "branch_povms": (
        ("j0", "v0", diag_matrix((1, 0))),
        ("j0", "v1", diag_matrix((0, 1))),
        ("j1", "v0", diag_matrix((F(1, 2), F(1, 2)))),
        ("j1", "v1", diag_matrix((F(1, 2), F(1, 2)))),
    ),
    "physical": (
        ("v0", diag_matrix((F(17, 25), F(41, 50), F(8, 25), F(9, 50)))),
        ("v1", diag_matrix((F(8, 25), F(9, 50), F(17, 25), F(41, 50)))),
    ),
    "target": (
        ("v0", diag_matrix((1, 0, 1, 0))),
        ("v1", diag_matrix((0, 1, 0, 1))),
    ),
    "branch_weight_pullbacks": (
        ("Pi_j0", diag_matrix((F(9, 25), F(16, 25), F(9, 25), F(16, 25)))),
        ("Pi_j1", diag_matrix((F(16, 25), F(9, 25), F(16, 25), F(9, 25)))),
    ),
    "branch_weight_is_a_constraint": False,
    "derivation": """\
Theorem thm:mixture with B = B_0 D, B_0 = D = C^2, J = {j0, j1}. The register
POVM is N_j0 = diag(9/25, 16/25) and N_j1 = diag(16/25, 9/25), which sum to
1_D and are NOT PROJECTIONS -- their eigenvalues 9/25 and 16/25 are neither 0
nor 1 -- so Remark rem:povmreg's generalization is exercised, not sidestepped.

THE PHYSICAL POVM, Eq. eq:regmodel, on the basis (00, 01, 10, 11) with the B_0
index MAJOR:
    M_v0 = |0><0| (x) N_j0 + (1/2)1 (x) N_j1
         = diag(9/25, 16/25, 0, 0) + diag(8/25, 9/50, 8/25, 9/50)
         = diag(17/25, 41/50, 8/25, 9/50) ,
using (1/2)(16/25) = 8/25 and (1/2)(9/25) = 9/50. Similarly
M_v1 = diag(8/25, 9/50, 17/25, 41/50), and the two sum to 1_4.

THE TARGET is Q = Q_j0 (+) Q_j1 = C^2 (+) C^2, with the CHARACTERIZED branch
squashed by the identity (F_{|j0} = M_{|j0}) and the UNCHARACTERIZED one by the
flag PVM of Lemma lem:top:
    F_v0 = |0><0| (+) |v0><v0| = diag(1, 0, 1, 0) ,
    F_v1 = |1><1| (+) |v1><v1| = diag(0, 1, 0, 1) ,  summing to 1_4.

THE ADJOINT. Eq. eq:masteradjoint with I_j+(X) = X (x) N_j gives
    Lambda+((+)_j X_j) = sum_j Lambda_j+(X_j) (x) N_j ,
so Lambda+(F_v0) = |0><0| (x) N_j0 + Lmp+(|v0><v0|) (x) N_j1
= |0><0| (x) N_j0 + (1/2)1 (x) N_j1 = M_v0 EXACTLY. The instrument adjoint is
computed once in the theorem's proof: for K = 1 (x) N_j^{1/2}, cyclicity gives
tr[X tr_D(K rho K)] = tr[K (X (x) 1_D) K rho], so I_j+(X) = X (x) N_j, "the two
factors commuting because they act on different tensor factors".

THE BRANCH WEIGHTS ARE TRANSPORTED AS OPERATORS, thm:mixture (iii):
    Lambda+(Pi_j0) = 1_{B_0} (x) N_j0 = diag(9/25, 16/25, 9/25, 16/25) ,
    Lambda+(Pi_j1) = 1_{B_0} (x) N_j1 = diag(16/25, 9/25, 16/25, 9/25) ,
which sum to 1_B as unitality requires. NEITHER IS A MULTIPLE OF THE IDENTITY,
and the theorem's own clause says what follows: Eq. eq:branchweight "is AN
IDENTITY, NOT A CONSTRAINT, UNLESS the right-hand side is a DECLARED MULTIPLE of
rho_R". Contrast BRANCH-convex in Group PR-E, where I_j+(1) = q_j 1_B is a
multiple and the constraint tr[Pi_j sigma] = q_j IS produced. An implementation
that emitted a scalar branch weight here would be asserting something the
mathematics does not give.

THE PRICE OF THE GENERALIZATION, Remark rem:povmreg: keeping the register D
intact in the target would need {N_j} PROJECTIVE, because that proof turns on
P_i(X (x) N_j) = delta_ij X (x) N_j, "and that identity FAILS FOR A GENERAL
POVM". Filing each branch as a BLOCK removes the hypothesis; "the price is
bookkeeping and nothing else: the target is a DIRECT SUM rather than a tensor
product, WHICH IS THE FORM THE CONSUMING DECLARATION WANTS IN ANY CASE".""",
}


# ===========================================================================
#  Group PR-J -- the event-bound obstruction (PR10)
# ===========================================================================


@dataclass(frozen=True)
class ObstructionCase:
    """Proposition prop:obstruction, frozen with its numbers."""

    case_id: str
    claims: tuple[str, ...]
    povm: tuple[tuple[str, Matrix], ...]
    event: tuple[str, ...]
    #: Trace and determinant of sum_{v in event} M_v: the EXACT rational data
    #: from which p_* is the smaller root of x^2 - (trace)x + (det).
    event_sum_trace: F
    event_sum_det: F
    #: A rational lower bound on p_*, with its exact PSD certificate.
    rational_witness: F
    witness_shift_trace: F
    witness_shift_det: F
    derivation: str


PR_OBSTRUCTION = ObstructionCase(
    case_id="OBSTRUCTION-C2",
    claims=("PR10",),
    povm=(
        ("1", real_matrix(((F(1, 2), 0), (0, 0)))),
        ("2", real_matrix(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4))))),
        ("3", real_matrix(((F(1, 4), F(-1, 4)), (F(-1, 4), F(3, 4))))),
    ),
    event=("1", "2"),
    event_sum_trace=F(1),
    event_sum_det=F(1, 8),
    rational_witness=F(1, 8),
    witness_shift_trace=F(3, 4),
    witness_shift_det=F(1, 64),
    derivation="""\
Eq. eq:obstruction, on H(B) = C^2 with |+> = (|0> + |1>)/sqrt2:
    M_1 = (1/2)|0><0| = [[1/2, 0], [0, 0]] ,
    M_2 = (1/2)|+><+| = [[1/4, 1/4], [1/4, 1/4]] ,
    M_3 = 1 - M_1 - M_2 = [[1/4, -1/4], [-1/4, 3/4]] ,
    O_* = {1, 2} ,   p_* = (1/2)(1 - 1/sqrt2) .
EVERY MATRIX ENTRY IS RATIONAL, although |+> has irrational amplitudes: the
projectors are what appear.

THE DATA ARE ADMISSIBLE, checked exactly. M_1 + M_2 = [[3/4, 1/4], [1/4, 1/4]]
has trace 1 and determinant 3/16 - 1/16 = 1/8, so its eigenvalues are the roots
of x^2 - x + 1/8, namely (1 +- 1/sqrt2)/2. Hence
lmin(M_1 + M_2) = (1 - 1/sqrt2)/2 = p_* EXACTLY, which is the contract's number,
and lmax = (1 + 1/sqrt2)/2 < 1. M_3 >= 0 by trace 1 > 0 and determinant
3/16 - 1/16 = 1/8 > 0, so {M_1, M_2, M_3} is a POVM with M_1 + M_2 >= p_* 1.

HOW p_* IS FROZEN WITHOUT LEAVING THE RATIONALS, and it is the one place this
registry meets an irrational number. It is frozen BY ITS MINIMAL POLYNOMIAL --
the smaller root of x^2 - x + 1/8, i.e. by the pair (trace, det) = (1, 1/8) --
together with a RATIONAL WITNESS 1/8 whose certificate is exact:
    M_1 + M_2 - (1/8) 1 has trace 1 - 1/4 = 3/4 > 0 and determinant
    1/8 - (1/8)(1) + 1/64 = 1/64 > 0 , so BOTH EIGENVALUES ARE POSITIVE
and M_1 + M_2 >= (1/8) 1. Since 1/8 < p_*, the witness is a WEAKER admissible
bound, and THE PROOF USES ONLY p_* > 0, so either drives the contradiction.

THE OBSTRUCTION. Suppose a CLASSICAL target (F, Lambda) existed -- every F_v
diagonal in one fixed basis {|f>} -- with M <= F and
sum_{v in O_*} F_v >= p_* 1_Q. Put T_f := Lambda+(|f><f|). Then {T_f} is a POVM
on B: each T_f >= 0 by positivity of Lambda+, and sum_f T_f = Lambda+(1_Q) = 1_B
by unitality. Writing F_v = sum_f F_v(f)|f><f| with F_v(f) >= 0 and
sum_v F_v(f) = 1, linearity gives M_v = sum_f F_v(f) T_f.

The encoded bound reads ON THE DIAGONAL F_1(f) + F_2(f) >= p_* > 0 for EVERY f,
so every f has F_1(f) > 0 or F_2(f) > 0.
  * If F_1(f) > 0 then 0 <= F_1(f) T_f <= M_1 = (1/2)|0><0|, and a positive
    operator dominated by a rank-one positive operator is a non-negative
    multiple of it, so T_f is proportional to |0><0|.
  * Symmetrically F_2(f) > 0 forces T_f proportional to |+><+|.
  * A non-zero operator cannot be proportional to both distinct rank-one
    projections, so F_1(f)F_2(f) > 0 forces T_f = 0.
In every case T_f is 0, or a non-negative multiple of |0><0|, or one of |+><+|.
Summing, 1_B = alpha|0><0| + beta|+><+| for some alpha, beta >= 0. Testing
against |1>: 1 = beta/2, so beta = 2. Testing the (0,1) entry:
0 = beta/2, so beta = 0. CONTRADICTION.
(alpha and beta here are two non-negative scalars local to this argument; they
are NOT the Renyi order alpha, which this contract never computes with.)

WHAT IT FORCES, Remark rem:obstruction-scope, three design commitments:
 (a) the artifact carries a `constraint_list` and an `attack_set_license` field
     EVEN WHEN BOTH ARE EMPTY, "because a schema without them EXCLUDES A CLASS
     OF DEVICE KNOWLEDGE THAT NO TARGET DESIGN CAN RECOVER";
 (b) RE-DECLARING THE COARSE-GRAINING DOES NOT HELP -- merging the outcomes of
     O_* makes the bound encodable "only by DESTROYING THE DISTINCTION between
     the merged outcomes, which is precisely what 'must not be merged' forbids
     when they carry key information";
 (c) the counterexample is TWO-DIMENSIONAL with THREE outcomes, "so it is NOT an
     artefact of infinite dimension, of photon number, or of the optical
     setting".

AND WITH A GENERAL QUANTUM TARGET THE ENCODING IS TRIVIAL: take F = M and
Lambda = id, and the physical bound is itself an operator inequality on the
target. The content is that FLAG-SHAPED targets -- classical on the sector where
the bound must live -- cannot carry it.""",
)

OBSTRUCTION_CASES_PR10: tuple[ObstructionCase, ...] = (PR_OBSTRUCTION,)


# ===========================================================================
#  Group PR-K -- the A-ATK attack-set licence (PR11)
# ===========================================================================


@dataclass(frozen=True)
class LicenceCase:
    """One licence entry, typed for a source mode, with its certificate."""

    case_id: str
    claims: tuple[str, ...]
    instance: str
    source_mode: str
    #: The entry (O^_k, relation, c_k) of Definition def:licensed.
    ohat_label: str
    relation: str
    constant: F
    #: How Theta_k is TYPED in this mode: c_k tau_A or the real number c_k.
    theta_typing: str
    #: The adjoint-form admissible set of Eq. eq:attset / eq:attsetun.
    admissible_set: str
    #: Whether the artifact carries a licence record. Present iff CList != {}.
    licence_present: bool
    derivation: str
    #: SUPERSESSION MARK, set by run A of the 0.2.0 band. ``None`` means the
    #: case stands as frozen. A version string means the 0.2.0 amendment
    #: invalidates it in whole or in scope; see ``SUPERSESSIONS`` for the
    #: contract site and the replacement, and the module banner for what
    #: "superseded" means here. NO MARKED VALUE WAS EDITED OR DELETED.
    superseded_by: str | None = None
    superseded_site: str = ""
    superseded_replacement: tuple[str, ...] = ()


LICENCE_TRUSTED = LicenceCase(
    case_id="WP3-licence-trusted",
    claims=("PR11",),
    instance="WP3-fss",
    source_mode="trusted",
    ohat_label="O^ = F^FSS_v0 - (1/4) Pi_flag",
    relation=">=",
    constant=F(0),
    theta_typing="Theta = c tau_A = 0 * tau_A, the ZERO OPERATOR on A",
    admissible_set=(
        "A_CList(E', Q E'') = { A in CPTP(E', Q E'') : A+(O^ (x) 1_E'') >= 0 * 1_E' }"
    ),
    licence_present=True,
    derivation="""\
Theorem thm:licence (i), TRUSTED-SOURCE MODE. Eq. eq:attset, quoted verbatim in
Definition def:attset from meat-core 0.4.0 Def. def:roundmodel, is
    A_CList(E', Q E'') = { A in CPTP(E', Q E'') :
                           A+(O^_k (x) 1_E'') bowtie_k c_k 1_E'  for all k } ,
and Definition def:licensed types the right-hand side as Theta_k = c_k tau_A in
this mode, "the state-level entry reading
tr_Q[(1_A (x) O^_k) omega] bowtie_k c_k tau_A".

THE HYPOTHESIS IS eq:certificate, AND IT IS DISCHARGED IN Group PR-C:
    O = Lambda^FSS+(O^) = M_v0 - (1/4) Pi_>N = [2/3] (+) (5/8) M'_v0 >= 0
      = 0 * 1_B ,
so the entry is (O^, >=, 0). NOTHING ELSE IS REQUIRED: the proof uses ONLY
POSITIVITY AND UNITALITY OF AN ATTACK CHANNEL'S ADJOINT. For any
A in CPTP(E', B E''), writing A^sq = (Lambda (x) id_E'') o A,
    A^sq+ = A+ o (Lambda (x) id_E'')+ ,
and Fact fact:sep (ii) gives (Lambda (x) id)+(O^ (x) 1) = O (x) 1
(Eq. eq:compositeadjoint). Then, since A+ is positive and A+(1) = 1_E',
    A^sq+(O^ (x) 1_E'') - 0 * 1_E' = A+(O (x) 1_E'' - 0 * 1) >= 0 .
So A^sq lies in A_CList(E', Q E'') FOR EVERY PHYSICAL ATTACK CHANNEL A -- which
is the inclusion Eq. eq:seqcover needs and the whole point of the licence.

AT c = 0 THE TYPING IS DEGENERATE AND THAT IS RECORDED, NOT HIDDEN. Theta =
0 * tau_A is the zero operator, and Remark rem:gateweight says the consuming
gate "DEGENERATES: at d_A = 1 every 1x1 Hermitian right-hand side is a multiple
of tau_A, and in untrusted-source mode the entry type is scalar by
construction, so IN BOTH CASES PART (i) REJECTS NOTHING and the gate rests
ENTIRELY on part (ii)" -- the presence of this licence, "WHICH NO PROGRAM CAN
VERIFY". That is why thm:licence is a THEOREM WITH AN EXPLICIT HYPOTHESIS and
not an attestation.""",
    superseded_by="0.2.0",
    superseded_site=(
        "cor:tolentries (i), eq:tolfss; Section 2.3 constraint_list clause (a)"
    ),
    superseded_replacement=("TOL_ENTRY_FLAG",),
)

LICENCE_UNTRUSTED = LicenceCase(
    case_id="WP3-licence-untrusted",
    claims=("PR11",),
    instance="WP3-fss",
    source_mode="untrusted",
    ohat_label="O^ = F^FSS_v0 - (1/4) Pi_flag",
    relation=">=",
    constant=F(0),
    theta_typing="Theta = c = 0, the REAL NUMBER",
    admissible_set=(
        "A_CList(E', A Q E'') = { A in CPTP(E', A Q E'') : "
        "A+(1_A (x) O^ (x) 1_E'') >= 0 * 1_E' }"
    ),
    licence_present=True,
    derivation="""\
Theorem thm:licence (ii), UNTRUSTED-SOURCE MODE, THE SAME ENTRY AND THE SAME
CONSTANT. Eq. eq:attsetun differs from eq:attset in ONE THING: the constraint
operator is LIFTED to the larger supplied system, 1_A (x) O^ (x) 1_E'', because
in this mode A_j is an OUTPUT of the attack channel (Eq. eq:attackchannel) and
the composite is (id_A (x) Lambda (x) id_E'') o A (Eq. eq:composite).

The proof is "IDENTICAL, with eq:compositeadjoint replaced by
    (id_A (x) Lambda (x) id_E'')+(1_A (x) O^ (x) 1_E'') = 1_A (x) O (x) 1_E'' ,
again Fact fact:sep (ii), and with 1_A (x) O (x) 1_E'' >= c 1_{A B E''}
following from eq:certificate BY TENSORING WITH IDENTITIES."

Definition def:licensed types Theta = c = 0 as a REAL NUMBER here, "the entry
reading tr[(1_A (x) O^_k) omega] bowtie_k c_k -- A COMPARISON OF REAL NUMBERS".
Definition def:attset's note on the relation symbols records that the split
runs between LEVELS and not between MODES, and that everything this module
emits (">= with c = 0; = with c = q_t") IS ADMITTED UNDER EITHER SPELLING.

THE TRUSTED MARGINAL IS NOT THIS MODULE'S TO DECLARE, thm:licence (iv): in
trusted mode "the identification of the right-hand side is THE DECLARATION'S
AND NOT THIS CONTRACT'S: Corollary cor:pullback (iii) delivers
tr_Q[(1_A (x) O^_k)sigma] >= c_k sigma_A, and it is THE CONSUMER'S MARGINAL
CONDITION omega_A = tau_A ... that turns c_k sigma_A into c_k tau_A." Remark
rem:notlicensed (a) is blunter: "Nothing here licenses declaring tau_A."
""",
    superseded_by="0.2.0",
    superseded_site=(
        "cor:tolentries (i), eq:tolfss; Section 2.3 constraint_list clause (a)"
    ),
    superseded_replacement=("TOL_ENTRY_FLAG",),
)

LICENCE_PROBE_IDENTITY = LicenceCase(
    case_id="PROBE22-licence-identity",
    claims=("PR11", "PR3"),
    instance="PROBE22",
    source_mode="untrusted",
    ohat_label="O^ = sum_y F_(y,t0)",
    relation="=",
    constant=F(2, 3),
    theta_typing="Theta = c = 2/3, the REAL NUMBER q_t0",
    admissible_set=(
        "A_CList(E', A Q E'') = { A : A+(1_A (x) O^ (x) 1_E'') = (2/3) 1_E' }"
    ),
    licence_present=True,
    derivation="""\
The SECOND relation symbol, "=", with a NON-ZERO declared constant -- so that an
implementation handling only the ">= with c = 0" case is observably incomplete.
The entry is the one Remark rem:unsound says "remains AVAILABLE ON REQUEST":
O^ = sum_y F_(y,t), relation =, c = q_t, requested through `carried_operators`,
"ON THE LICENSED ROUTE AND UNDER THE LICENCE THAT ROUTE REQUIRES".

The certificate is the IDENTITY case, discharged in PROBE22-cert-identity:
Lambda^WP+(sum_y F_(y,t0)) = sum_y M_(y,t0) = q_t0 1_B = (2/3) 1_B. Theorem
thm:licence's proof then covers "=" in one line: "for bowtie_k = = BOTH
DIRECTIONS HOLD, or directly A+(c_k 1) = c_k 1_E'."

THE CONSTANT IS DECLARED, NOT OBSERVED. q_t0 = 2/3 is the protocol's declared
probe weight (input key `probe_declaration`), fixed before the run, so
Assumption A-CONST is satisfied. An entry whose constant were a run statistic
would be refused with `data_dependent_constant` -- see the refusal cases.""",
    superseded_by="0.2.0",
    superseded_site=(
        "cor:tolentries (ii), eq:tolprobe, eq:starprobeexact; "
        "rem:unsound as narrowed (F-5-01); Section 4.13's "
        "constraint-certificate row"
    ),
    superseded_replacement=(
        "TOL_ENTRY_PROBE_T0",
        "TOL_ENTRY_PROBE_T1",
        "TOL2-branchprobe-pass",
    ),
)

LICENCE_CASES: tuple[LicenceCase, ...] = (
    LICENCE_TRUSTED,
    LICENCE_UNTRUSTED,
    LICENCE_PROBE_IDENTITY,
)

#: A COMPOSITE ATTACK LANDING IN THE SET, frozen as an operator on E' so that
#: the conclusion is the OPERATOR inequality of Eq. eq:attset and not a scalar.
COMPOSITE_ATTACK_CASE: dict[str, object] = {
    "case_id": "WP3-composite-attack",
    "claims": ("PR11",),
    "instance": "WP3-fss",
    "attack": "A(sigma) = sum_e <e|sigma|e> rho_e in CPTP(E', B E''), with "
    "E' = C^2 basis (e0, e1), rho_e0 = |psi_0><psi_0| (x) tau_0 and "
    "rho_e1 = |psi_1><psi_1| (x) tau_1 for any states tau_0, tau_1 on E''",
    "composite": "A^sq = (Lambda^FSS (x) id_E'') o A",
    "result": diag_matrix((F(5, 8), F(0))),
    "constant": F(0),
    "in_set": True,
    "derivation": """\
A is a measure-and-prepare channel on E', so A+(X) = sum_e tr[X rho_e]|e><e| is
DIAGONAL on E' and A+(1) = 1_E' (unital, as any channel adjoint is). Then
    A^sq+(O^ (x) 1_E'') = A+((Lambda^FSS (x) id)+(O^ (x) 1_E''))
                        = A+(Lambda^FSS+(O^) (x) 1_E'')
                        = sum_e tr[(Lambda^FSS+(O^) (x) 1) rho_e] |e><e| .
With Lambda^FSS+(O^) = [2/3] (+) (5/8) M'_v0 (Group PR-C):
    e0: <psi_0| (5/8) M'_v0 |psi_0> = 5/8 , since M'_v0 |psi_0> = |psi_0| ;
    e1: <psi_1| (5/8) M'_v0 |psi_1> = 0    , since M'_v0 |psi_1> = 0 .
So A^sq+(O^ (x) 1) = diag(5/8, 0) >= 0 = c 1_E', AND A^sq LIES IN
A_CList(E', Q E''). NOTE THAT IT IS NOT A MULTIPLE OF 1_E': the conclusion is a
genuine OPERATOR inequality, which is what Eq. eq:attset asks for and what a
scalar-only implementation would get wrong.

CROSS-CHECK AGAINST THE TARGET SIDE. At E' = C (a state preparation) with
rho = |psi_0><psi_0|, the same computation reads tr[O^ Lambda^FSS(rho)]:
Lambda^FSS(|psi_0><psi_0|) has flag distribution (7/8, 1/8), and
    (7/8)(3/4) + (1/8)(-1/4) = 21/32 - 1/32 = 20/32 = 5/8 ,
using O^ = diag(2/3, 3/4, -1/4). THE TWO ROUTES AGREE, which is
Eq. eq:pairing.""",
}

#: TIGHT -- the cross-channel pairing of Eq. eq:crosspairing, frozen AT ITS
#: TIGHT END WHERE IT IS NEGATIVE. This is why `route: both` is refused.
TIGHT: dict[str, object] = {
    "case_id": "TIGHT-crosspairing",
    "claims": ("PR6", "PR11", "PR12"),
    "refusal_reasons": ("route_not_single_valued", "constraint_channel_mismatch"),
    "preserved": (("o", F(1, 2)), ("w", F(1, 2))),
    "above_cutoff": (("o", F(1, 5)), ("w", F(4, 5))),
    "weights": (("o", F(1, 5)), ("w", F(0))),
    "total_weight": F(1, 5),
    "mprime": (("o", F(0)), ("w", F(1))),
    "ohat_flag_block": (F(4, 5), F(-1, 5)),
    "pairing_with_own_channel": F(0),
    "pairing_with_other_channel": F(-1, 5),
    "reachable_flag_state": (F(0), F(1)),
    "derivation": """\
THE TIGHT END IS THE POINT. On the one-dimensional-blocks instance with
V = {o, w}:
    blk M^{<=N}_o = blk M^{<=N}_w = 1/2 ,
    blk M^{>N}_o = 1/5 ,  blk M^{>N}_w = 4/5 ,   p_o = 1/5 ,  p_w = 0 ,
so eq:certweights holds WITH EQUALITY AT o -- blk M^{>N}_o = p_o 1 -- which is
exactly the configuration Remark rem:tworoutes names: "at the tight end
blk M^{>N}_o = p_o 1 it equals -p_o 1, strictly negative for p_o > 0". Total
p = 1/5 < 1, so the declaration is otherwise admissible.

THE LICENSED ENTRY, on its OWN channel Lambda^FSS. O^ = F^FSS_o - p_o Pi_flag
= [1/2] (+) diag(1 - 1/5, 0 - 1/5) = [1/2] (+) diag(4/5, -1/5), and
    Lambda^FSS+(O^) flag block = (4/5)(1/5) + (-1/5)(4/5) = 4/25 - 4/25 = 0 ,
so the pull-back is [1/2] (+) 0 >= 0. THE CERTIFICATE HOLDS, tightly.

THE SAME ENTRY PAIRED WITH THE OTHER ROUTE'S CHANNEL, Eq. eq:crosspairing. Here
M'_o = (1/5 - 1/5)/(4/5) = 0 and M'_w = (4/5 - 0)/(4/5) = 1, so eq:WPadjoint
gives
    Lambda^WP+(O^) flag block = (4/5)(0) + (-1/5)(1) = -1/5  <  0 .
NEGATIVE. The certificate FAILS on the wrong channel, and the general form is
the contract's:
    Lambda^WP+(F^FSS_o - p_o Pi_flag)
      = blk M^{<=N}_o (+) ( (1/(1-p))(blk M^{>N}_o - p_o 1) - p_o 1 ) ,
whose flag block "is NOT implied positive by eq:certweights".

AND IT EXCLUDES A REACHABLE STATE, which is what makes it UNSOUND rather than
merely unproved. Under Lambda^WP the flag output of an above-cutoff input is
the distribution (M'_o, M'_w) = (0, 1), i.e. the state |f_w><f_w|, WHICH IS
REACHABLE; on it
    tr[O^ |f_w><f_w|] = -1/5 < 0 ,
so the constraint {sigma : tr[O^ sigma] >= 0} EXCLUDES A REACHABLE STATE,
Eq. eq:inclusion fails and Theorem thm:transfer is VOIDED -- "exactly the
failure Remark rem:unsound describes".

THE STRUCTURAL REMEDY, and it is a REFUSAL and not a warning: "Since the
emitted payload is single-valued and eq:link binds each link's constraint list
to THAT LINK'S channel witness, the structural remedy is to EMIT ONE ROUTE PER
ARTIFACT AND REFUSE `both` -- two requests give a caller both bundles WITH NO
SCHEMA IN WHICH THE UNSOUND PAIRING CAN BE EXPRESSED." Two refusal reasons
cover the two ways to reach it: `route_not_single_valued` for a request naming
both routes, and `constraint_channel_mismatch` for an entry certified against a
channel that is not its own link's witness.""",
}


# ===========================================================================
#  Group PR-L -- typed links, chains, and the fail-closed set (PR12)
# ===========================================================================


@dataclass(frozen=True)
class LinkRecord:
    """One typed link, Definition def:link Eq. eq:link, ALL TEN SLOTS.

    The contract states the count once: "A link has TEN slots. SIX of them are
    the fields the contract requires -- source family, target,
    channel witness, reachable-set statement, transported constraint entries,
    licence record -- and the remaining FOUR are ``stage``, ``kind``, the
    carried operator pair, and ``status``."
    """

    #: slot 1
    stage: str
    #: slot 2
    kind: str
    #: slot 3 -- the SOURCE FAMILY: the system AND the POVM it starts from.
    source_family: tuple[str, str]
    #: slot 4 -- the TARGET: system and POVM.
    target: tuple[str, str]
    #: slot 5 -- the CHANNEL WITNESS.
    channel_witness: str
    #: slot 6 -- the carried operator pair (O^_out, O_in).
    carried_operator_pair: tuple[str, str]
    #: slot 7 -- the reachable-set statement of Definition def:sound.
    reachable_set_statement: str
    #: slot 8 -- transported constraint entries, with the certificate case.
    constraint_entries: tuple[tuple[str, str, F, str], ...]
    #: slot 9 -- the licence record; present EXACTLY WHEN slot 8 is non-empty.
    licence: str | None
    #: slot 10
    status: str
    #: Not a slot: the registry's own label and provenance.
    link_id: str = ""
    derivation: str = ""


LINK_IDENTITY = LinkRecord(
    stage="receiver",
    kind="identity",
    source_family=("B = C^2 (an already-finite receiver)", "{M_v}"),
    target=("Q = C^2", "{M_v}"),
    channel_witness="id",
    carried_operator_pair=("()", "()"),
    reachable_set_statement="the whole declared input family S^ph",
    constraint_entries=(),
    licence=None,
    status="exact",
    link_id="L-identity",
    derivation="""\
Example ex:identity, field for field. "For an ALREADY-FINITE receiver -- an
ideal qubit protocol, or any fixture whose POVM the engine can consume directly
-- the chain has ONE link with stage = receiver, kind = identity,
Lambda_l = id, M^out = M^in, the carried tuple EMPTY OR THE IDENTITY ON ANY
DECLARED OPERATORS, S^rch_l the whole declared input family,
CList_l = empty, NO LICENCE, and status = exact."

It is a squashing relation by reflexivity (Proposition prop:preorder,
M <=_id M), so Theorem thm:chain applies and returns the physical model
unchanged.

WHY IT IS RECORDED RATHER THAN OMITTED, and this is a design commitment: "AN
EMPTY CHAIN WOULD LEAVE THE ARTIFACT UNABLE TO SAY WHETHER A REDUCTION WAS
PERFORMED AND FOUND TRIVIAL OR NEVER CONSIDERED, and the composition order of
decision (2) has to be carried EVEN WHEN THERE IS NOTHING TO ORDER."
LICENCE IS None BECAUSE THE CONSTRAINT LIST IS EMPTY -- the presence rule of
Definition def:link, whose two violations are `licence_missing` and
`licence_without_constraints`.""",
)

LINK_WPFSS = LinkRecord(
    stage="receiver",
    kind="wpfss",
    source_family=("B = C^3 with the cutoff split (1, 2)", "{M_v} of WP3"),
    target=("Q = H(B_<=N) (+) H(flag) = C^3", "{F^WP_v} of Eq. eq:WPFSS"),
    channel_witness="Lambda^WP of Eq. eq:Lwp, Kraus set WP3_KRAUS",
    carried_operator_pair=("(Pi_<=N, Pi_flag) on Q", "(Pi_<=N, Pi_>N) on B"),
    reachable_set_statement=(
        "{ (Lambda^WP (x) id)(rho) : rho in S^ph }, Definition def:sound"
    ),
    constraint_entries=(),
    licence=None,
    status="exact",
    link_id="L-wpfss",
    derivation="""\
THE `encoded` ROUTE'S LINK. The weights go INTO the target (Eq. eq:WPFSS), so
the constraint list is EMPTY and NO LICENCE is emitted -- Section 2.1's `route`
row: "`encoded` (default; the weights go into {F_v} and CList = empty)".

status = exact because Lambda^WP+(F^WP_v) = M_v "holds WITH NO ERROR TERM"
(Definition def:link), verified entry by entry in Group PR-A.

The carried pair is the DEFAULT of Section 2.1's `carried_operators` row, on
the trivial certificate (c = 0, relation >=), its pull-backs being positive
though not multiples of the identity (Eq. eq:transportproj).""",
)

LINK_FSS = LinkRecord(
    stage="receiver",
    kind="fss",
    source_family=("B = C^3 with the cutoff split (1, 2)", "{M_v} of WP3"),
    target=("Q = H(B_<=N) (+) H(flag) = C^3", "{F^FSS_v} of Eq. eq:FSS"),
    channel_witness="Lambda^FSS of Eq. eq:Lfss (symbolic constructor record)",
    carried_operator_pair=(
        "(Pi_<=N, Pi_flag, F^FSS_v0 - (1/4)Pi_flag) on Q",
        "(Pi_<=N, Pi_>N, M_v0 - (1/4)Pi_>N) on B",
    ),
    reachable_set_statement=(
        "{ (Lambda^FSS (x) id)(rho) : rho in S^ph }, Definition def:sound"
    ),
    constraint_entries=(
        (
            "F^FSS_v0 - (1/4) Pi_flag",
            ">=",
            F(0),
            "positivity (cor:pullback (ii)); pull-back [2/3] (+) (5/8)M'_v0",
        ),
    ),
    licence="Theorem thm:licence; hypothesis eq:certificate per entry; "
    "discharged by A-RECV with the receiver artifact's "
    "mathematical_spec_version; source mode as declared; the adjoint-form "
    "set of Eq. eq:attset (trusted) or eq:attsetun (untrusted)",
    status="exact",
    link_id="L-fss",
    derivation="""\
THE `licensed` ROUTE'S LINK. The weights are NOT encoded in the target; they
travel as the constraint entry of Corollary cor:fssinstance
(Theorem thm:blinding (vi)), and the licence record is therefore PRESENT --
"REQUESTING ANY ENTRY SELECTS THE `licensed` ROUTE, because a non-empty list
requires the licence" (Section 2.3, `constraint_list`).

The licence record NAMES FIVE THINGS and asserts none of them about a device:
the theorem, the hypothesis it was discharged on, the receiver fact that
discharges it WITH THE ARTIFACT'S VERSION, the source mode, and the
adjoint-form set. Remark rem:gateweight explains why it must be a theorem with
a named hypothesis rather than an attestation: in the cases that matter "THE
ATTESTATION IS THE SECURITY ARGUMENT".

WHY THIS LINK'S CHANNEL WITNESS MATTERS. Definition def:link binds the
constraint list to THIS link's witness, and TIGHT-crosspairing freezes what
goes wrong when the binding is broken: the same entry paired with Lambda^WP
pulls back to a NEGATIVE operator and excludes a reachable state. The refusal
is `constraint_channel_mismatch`.""",
)

LINK_REGISTER_MIXTURE = LinkRecord(
    stage="receiver",
    kind="register-mixture",
    source_family=("B = B_0 (x) D = C^2 (x) C^2", "{M_v} of Eq. eq:regmodel"),
    target=("Q = Q_j0 (+) Q_j1 = C^4", "{(+)_j F_{v|j}}"),
    channel_witness="Eq. eq:regchannel with N_j^{1/2} = diag(3/5, 4/5) etc.",
    carried_operator_pair=("(Pi_j0, Pi_j1) on Q", "(1 (x) N_j0, 1 (x) N_j1) on B"),
    reachable_set_statement="Definition def:sound for Eq. eq:regchannel",
    constraint_entries=(),
    licence=None,
    status="exact",
    link_id="L-register-mixture",
    derivation="""\
Theorem thm:mixture, the MIXTURE-2branch instance of Group PR-H. The carried
pair is the branch projectors and their pull-backs 1_{B_0} (x) N_j, which are
NOT multiples of the identity -- so this link transports an IDENTITY
(Eq. eq:branchweight) and NOT a constraint, and the constraint list is empty.
thm:mixture (iii) says so in as many words: "this is AN IDENTITY, NOT A
CONSTRAINT, UNLESS the right-hand side is a declared multiple of rho_R".""",
)

LINK_FLAGS_ENOUGH = LinkRecord(
    stage="receiver",
    kind="flags-enough",
    source_family=("B_0 (+) H(flag) = C^4", "{G_v (+) |v><v|}"),
    target=("B_0 (+) H(flag) = C^4", "{(1/2)1_{B_0} (+) |v><v|}"),
    channel_witness="Eq. eq:flagsenough (measure-and-prepare into the flag block)",
    carried_operator_pair=("(Pi_flag)", "(Pi_flag)"),
    reachable_set_statement=(
        "every reachable state has ZERO WEIGHT in the B_0 block: the channel's "
        "output is supported in H(flag)"
    ),
    constraint_entries=(),
    licence=None,
    status="exact",
    link_id="L-flags-enough",
    derivation="""\
Corollary cor:flagsenough, the FLAGS-ENOUGH instance of Group PR-G. NOTE THE
REACHABLE-SET SLOT: it is the ONE slot that carries the content here -- the
block on which the squashing channel puts NO WEIGHT is exactly the block that
may be replaced by any POVM at all, and the artifact records that fact rather
than leaving it implicit. The source and target SYSTEMS coincide; what changes
is the POVM.""",
)

LINK_PINCHING = LinkRecord(
    stage="receiver",
    kind="pinching",
    source_family=("Q = C^5 (the BLIND2 target)", "{F_v}"),
    target=("Q = C^5", "{F_v}, UNCHANGED"),
    channel_witness="P_S of Proposition prop:pinching, P_S+ = P_S",
    carried_operator_pair=(
        "(Pi_nb_leq, Pi_nb_flag, Pi_bl1)",
        "(Pi_nb_leq, Pi_nb_flag, Pi_bl1), UNCHANGED",
    ),
    reachable_set_statement=(
        "every reachable state is BLOCK DIAGONAL for the sector decomposition "
        "of Eq. eq:sectors -- a sound constraint by cor:blockdiag (ii)"
    ),
    constraint_entries=(),
    licence=None,
    status="exact",
    link_id="L-pinching",
    derivation="""\
Proposition prop:pinching and Corollary cor:blockdiag, the BLIND2-pinching case
of Group PR-D. The POVM and the carried operators are UNCHANGED because P_S+
FIXES every sector-block-diagonal operator, which Theorem thm:blinding (iii)
proves of all of them. What the link buys is the reachable-set statement, and
Eq. eq:blindchannel composes it LAST.""",
)

LINK_RECORDS: tuple[LinkRecord, ...] = (
    LINK_IDENTITY,
    LINK_WPFSS,
    LINK_FSS,
    LINK_REGISTER_MIXTURE,
    LINK_FLAGS_ENOUGH,
    LINK_PINCHING,
)


@dataclass(frozen=True)
class ChainCase:
    """A reduction chain, its three conditions, and its composite."""

    case_id: str
    claims: tuple[str, ...]
    links: tuple[str, ...]
    composable: bool
    tuple_chained: bool
    stage_ordered: bool
    composite_channel: str
    composite_status: str | None
    refusal_reason: str | None
    derivation: str


CHAIN_WELL_FORMED = ChainCase(
    case_id="CHAIN-wpfss-pinching",
    claims=("PR12",),
    links=("L-wpfss", "L-pinching"),
    composable=True,
    tuple_chained=True,
    stage_ordered=True,
    composite_channel="P_S o Lambda^WP",
    composite_status="exact",
    refusal_reason=None,
    derivation="""\
A TWO-LINK CHAIN satisfying all three conditions of Definition def:chain.
(C1) COMPOSABLE: link 1's target (Q, {F^WP_v}) is link 2's source family.
(C2) TUPLE-CHAINED: link 1's O^_out = (Pi_<=N, Pi_flag) is link 2's O_in, and
     P_S+ fixes both, so the tuple survives to the final target.
(C3) STAGE-ORDERED: both links are receiver-stage, so no source link follows a
     receiver link.

THE COMPOSITE, Definition def:chain: Lambda_Chain = Lambda_l2 o Lambda_l1
= P_S o Lambda^WP -- "LATER LINKS ACT LATER" (Section 2.5), and by Theorem
thm:chain (i) the adjoint composes in the OPPOSITE order,
Lambda_Chain+ = Lambda^WP+ o P_S+. On a sector-block-diagonal F^WP_v, P_S+ is
the identity, so Lambda_Chain+(F^WP_v) = Lambda^WP+(F^WP_v) = M_v -- THE SAME
RELATION, with the block-diagonality of the reachable set added.

THE COMPOSITE STATUS is `exact` because every link's is (thm:chain (iv)), and
"a composition of exact identities is an exact identity". THE SECOND HALF OF
THAT PART IS A POLICY AND NOT A CONVERSE: a chain mixing an exact link with one
carrying an error term is REFUSED rather than given a composite status,
"because NO THEOREM OF THIS CONTRACT CONVERTS AN ERROR TERM INTO A SECURITY
PENALTY".

WHAT thm:chain (ii)-(iii) ADD: Theorems thm:factorization and thm:transfer and
Corollary cor:sequential apply TO THE COMPOSITE, and an entry declared on the
FINAL target is sound for the composite EXACTLY WHEN eq:certificate holds for
its pull-back Lambda_Chain+(O^_k), "which (C2) computes LINK BY LINK".""",
)

CHAIN_CASES: tuple[ChainCase, ...] = (CHAIN_WELL_FORMED,)


@dataclass(frozen=True)
class RefusalCase:
    """One declared datum that trips one fail-closed rule of Section 4.13."""

    case_id: str
    claims: tuple[str, ...]
    reason: str
    #: The declared datum that trips the rule, stated so a reader can re-run it.
    declared: str
    #: The contract element that makes the rule necessary.
    why: str
    derivation: str = ""
    #: SUPERSESSION MARK, set by run A of the 0.2.0 band. ``None`` means the
    #: case stands as frozen. A version string means the 0.2.0 amendment
    #: invalidates it in whole or in scope; see ``SUPERSESSIONS`` for the
    #: contract site and the replacement, and the module banner for what
    #: "superseded" means here. NO MARKED VALUE WAS EDITED OR DELETED.
    superseded_by: str | None = None
    superseded_site: str = ""
    superseded_replacement: tuple[str, ...] = ()


REFUSAL_CASES: tuple[RefusalCase, ...] = (
    RefusalCase(
        case_id="R-receiver-draft",
        claims=("PR12",),
        reason="receiver_spec_not_accepted",
        declared="receiver_artifact.mathematical_spec_version = "
        "'receiver-povm@0.1.3-draft'",
        why="Assumption A-RECV; a draft version may not back an emitted artifact",
        derivation="""\
Section 2.1's `receiver_artifact` row requires a version that "resolves to an
ACCEPTED receiver-povm contract. A DRAFT VERSION IS REFUSED". The accepted
version at the time of writing is 0.1.3 WITHOUT the suffix; the suffixed string
is exactly what a draft artifact would carry, and the check is a STRING-LEVEL
resolution against the supplier's STATUS.yaml, not a numeric comparison -- a
`-draft` suffix on the SAME version number is still a refusal.""",
    ),
    RefusalCase(
        case_id="R-cutoff",
        claims=("PR12",),
        reason="cutoff_mismatch",
        declared="photon_cutoff = 1 while bound_quantifier_domain echoes N = 2",
        why="the quantifier domain of every weight is m > N",
        derivation="""\
Section 2.1: "The N echoed here MUST EQUAL `photon_cutoff`; a mismatch is
refused." The hazard is precise: the supplier certified
sum_{S in O_i} blk M^{>2}_{S|t} >= p_i 1 for m > 2, and consuming it at N = 1
would attach that weight to the block m = 2 as well, where NOTHING WAS
CERTIFIED -- ARCHITECTURE_SPEC.md Section 7.3's "bounds not uniform above the
cutoff", in the unsafe direction.""",
    ),
    RefusalCase(
        case_id="R-block-structure",
        claims=("PR9", "PR12"),
        reason="no_block_structure",
        declared="M_{a|nb} with a non-zero (0,1) entry, i.e. an UNBLINDED branch "
        "element with coherence between the m = 0 block and the above-cutoff one",
        why="hypothesis of Definition def:targets",
        derivation="""\
THE CHECK IS ON THE nb BRANCH ALONE, and BLIND2 is the case that proves the
scope matters: there M_{a|bl1} = |+><+| HAS a non-zero (0,1) entry and the
check PASSES, because Definition def:blindmodel (c) requires block-diagonality
of the UNBLINDED branch only and Remark rem:paddednotemitted says "Section
4.13's block-structure refusal tests {M_{v|nb}} ALONE". Move the same
non-block-diagonal element to the nb branch and the artifact is REFUSED: without
it, blk M^{<=N}_v and blk M^{>N}_v are not defined as BLOCKS, Eq. eq:WPFSS has
nothing to build on, and Section 2.5's `block_restriction` convention -- a block
is NOT a compression -- has no content.""",
        superseded_by="0.2.0",
        superseded_site=(
            "Section 4.13, first tabular, third row, as restated; Section "
            "2.5 exact_arithmetic, which calls that row a TYPE check"
        ),
        superseded_replacement=("TOL_ROW_CASES", "TOL-scope-receiver-block-admit"),
    ),
    RefusalCase(
        case_id="R-fibre-split",
        claims=("PR6", "PR12"),
        reason="bound_set_not_a_fibre",
        declared="O_1 = MC (the multiclick set) while cg SPLITS MC across two "
        "letters, so O_1 is not cg^{-1}(y) for any y",
        why="Remark rem:fibre",
        derivation="""\
Remark rem:fibre, the FIRST of its two failures: "If cg SPLITS O across two
emitted letters, NEITHER LETTER INHERITS A BOUND, and the natural repair --
bound each piece -- is UNAVAILABLE because the supplier certified ONLY THE SUM."
On RC2 the fibre condition holds, cg^{-1}(y_mc) = {{1,2}} = MC; splitting MC
into two letters leaves both without a certified weight.

THE SECOND FAILURE, in the opposite direction, is a MERGE: if cg merges O with
outcomes outside it, "the bound STILL HOLDS for the merged letter (adding
positive operators only helps), but the coarse blocks the supplier emits no
longer let this module recover the certified sum separately, so the emitted
weight is attached to a letter WHOSE FIBRE IS LARGER THAN THE CERTIFIED SET --
sound, and recorded as such, BUT ONLY IF THE CONTAINMENT IS VALIDATED RATHER
THAN ASSUMED. Version 1 therefore requires EQUALITY."  Both directions refuse
with the same reason.""",
    ),
    RefusalCase(
        case_id="R-descent",
        claims=("PR6", "PR12"),
        reason="dark_counts_do_not_descend",
        declared="the K = 4 monotone product channel at p = 1/3 with the "
        "coarse-graining of Remark rem:descentneedsconstant",
        why="Lemma lem:descent, Remark rem:descentneedsconstant",
        derivation="""\
See DESCENT_COUNTEREXAMPLE in Group PR-M for the numbers. THE ROW ALSO FIXES
HOW THE CHECK IS RUN: "R is monotone and DESCENDS through cg -- TESTED DIRECTLY,
NOT VIA THE SHORTCUT Eq. eq:canonicalcg". The counterexample is precisely an R
and a cg meeting TWO of eq:canonicalcg's three clauses for which R^cg is not
well defined, so an implementation testing the shortcut instead of the property
would ACCEPT a declaration it must refuse.""",
    ),
    RefusalCase(
        case_id="R-absorbing",
        claims=("PR6", "PR12"),
        reason="bounded_letter_not_absorbing",
        declared="a bounded SINGLE-CLICK letter y_1 under a monotone product "
        "dark-count channel with p_dc|2 = 1/4, giving R^cg_{y_1|y_1} = 3/4 < 1",
        why="Eq. eq:absorbing; without it eq:routebound is FALSE in the UNSAFE "
        "direction (Remark rem:absorbneeded)",
        derivation="""\
See RCABS in Group PR-M, which freezes the failure quantitatively: the formula
would assert q_t (1/5) while the truth is q_t (3/20), a gap of q_t/20 IN THE
UNSAFE DIRECTION.

THE COST OF REFUSING THE WHOLE ARTIFACT is named as the deliberate choice it is:
prop:route's proof "uses eq:absorbing ONLY AT y_i, so ONE non-absorbing letter
could in principle have been handled by dropping that entry's weight to zero and
keeping the rest. Version 1 REFUSES THE WHOLE ARTIFACT instead -- fail-closed,
and A RATE LOSS RATHER THAN A SOUNDNESS QUESTION -- because a partially honoured
slot would emit a target whose weights no longer correspond ENTRY-FOR-ENTRY to
the declared slot, and NO DECLARED FIELD RECORDS WHICH ENTRY WAS SILENTLY
ZEROED."  The canonical declaration's multiclick letter IS absorbing (RC2), so
the slot receiver-povm 0.1.3 actually emits is admitted.""",
    ),
    RefusalCase(
        case_id="R-total-weight",
        claims=("PR6", "PR12"),
        reason="total_weight_not_below_one",
        declared="p_1 = 1, p_2 = 0, so p = sum_v p_v = 1",
        why="the construction eq:Lwp divides by 1 - p",
        derivation="See PEQONE in Group PR-F for the full case, including "
        "Remark rem:peqone's proof that the refusal is CONSERVATIVE and that the "
        "test runs on BOTH ROUTES and UNCONDITIONALLY.",
    ),
    RefusalCase(
        case_id="R-blinding-model",
        claims=("PR8", "PR9", "PR12"),
        reason="blinding_model_ill_formed",
        declared="N_nb = diag(9/25, 16/25) and N_bl1 = diag(16/25, 8/25), whose "
        "sum is diag(1, 24/25) != 1_Bl",
        why="Definition def:blindmodel, Theorem thm:mixture",
        derivation="""\
Theorem thm:mixture's hypothesis is that {N_j} is A POVM on D: the instrument
condition sum_j tr o I_j = tr is EXACTLY sum_j I_j+(1) = sum_j N_j = 1, by
Fact fact:sep (i). With sum_b N_b = diag(1, 24/25) the maps I_b do not form a
generalized instrument, Lemma lem:master does not apply, and {M_v} of
Eq. eq:regmodel NEED NOT BE A POVM -- so there is no relation to emit. The
BLIND2 register POVM sums to 1_2 exactly and passes.""",
    ),
    RefusalCase(
        case_id="R-probe-weights",
        claims=("PR6", "PR12"),
        reason="probe_weights_ill_formed",
        declared="q = (2/3, 1/2), whose sum is 7/6 != 1; and separately "
        "q = (1, 0), which violates q_t > 0",
        why="Assumption A-PROBE, Lemma lem:linear (ii)",
        derivation="""\
Section 2.1 requires T finite non-empty, q_t > 0 and sum_t q_t = 1. BOTH
violations are frozen because they fail different things. A sum != 1 breaks
Lemma lem:linear (ii)'s completeness computation, sum_{y,t} q_t M_{y|t}
= sum_t q_t 1, so the joint family IS NOT A POVM. A zero weight keeps
completeness but breaks the STRICT positivity the row states, and with it the
reading that every declared setting actually occurs -- a setting of weight zero
would contribute a flag basis vector to V with no statistics behind it.""",
    ),
    RefusalCase(
        case_id="R-relation-impossible",
        claims=("PR4", "PR12"),
        reason="declared_relation_impossible",
        declared="F_v0 = F_v1 = 1/2 on C^2 against M_v0 = |0><0|, "
        "M_v1 = |1><1| (span leg); and F^FSS <= F^WP (norm leg)",
        why="Lemma lem:obstructions, a cheap refusal before any construction",
        derivation="See OBSTRUCTION_CASES in Group PR-D: both legs, each with a "
        "refusing and a passing instance.",
    ),
    RefusalCase(
        case_id="R-chain-not-composable",
        claims=("PR12",),
        reason="chain_ill_formed",
        declared="link 1's target is (Q, {F^WP_v}) and link 2's source family is "
        "(Q, {F^FSS_v}) -- the SYSTEMS agree and the POVMs do not",
        why="Definition def:chain (C1)",
        derivation="""\
(C1) requires the pair (system, POVM) to agree, not the system alone: THE POVM
IS HALF OF EACH DESCRIPTOR (Definition def:link slots 3 and 4). This case is the
one an implementation carrying only system dimensions on the wire would miss --
see interface.yaml's `link_record.wire_form_comparison_note`, where the existing
`ReductionSystemDescriptor` carries name, dim, side and sectors and NOT the
POVM.

A SECOND WAY TO TRIP THE SAME REASON is a violation of (C2), TUPLE-CHAINING:
link 1 carrying O^_out = (Pi_<=N) while link 2 declares O_in = (Pi_flag). Then
the declared operator on the final target HAS NO PULL-BACK at the intermediate
stage, Theorem thm:chain (i)'s hypothesis fails, and the composite pull-back
thm:chain (iii) needs cannot be computed link by link.""",
    ),
    RefusalCase(
        case_id="R-stage-order",
        claims=("PR12",),
        reason="source_link_after_receiver_link",
        declared="the chain (receiver-stage identity link, source-stage link)",
        why="Definition def:chain (C3), Remark rem:ordering",
        derivation="""\
THE RULE IS A REFUSAL WITH A REASON, NOT A CONVENTION. A source-stage link
"re-parameterizes the first-round attack as A_1 = A'_1 o Gamma ranging over ALL
CPTP maps"; a receiver-stage link, by Theorem thm:licence, "hands the analysis
an attack set that is A PROPER SUBSET of the CPTP maps". Composing them in that
order needs the inclusion A^real_1 o Gamma SUBSET A^virtual_1, "and NOTHING IN
THIS CONTRACT ESTABLISHES IT FOR ANY Gamma".

IN VERSION 1 THE SOURCE STAGE IS EMPTY (Assumption A-NOSRC), so this refusal can
only be reached by a declaration that populates it -- and such a declaration
also trips `link_kind_deferred`, since `source-map` is reserved. BOTH REASONS
EXIST BECAUSE THEY ARE DIFFERENT FAILURES: one is about ORDER, the other about
AVAILABILITY, and a future version implementing source maps will keep the first
and drop the second.""",
    ),
    RefusalCase(
        case_id="R-kind-source-map",
        claims=("PR12",),
        reason="link_kind_deferred",
        declared="link_declarations naming kind = 'source-map'",
        why="Section 1.3, first deferral; docking point is the `source` STAGE",
        derivation="Source maps, tagging and decoy states. FUTURE_SCOPE.md "
        "Section 9. The stage EXISTS, is ordered first, and is EMPTY in v1.",
    ),
    RefusalCase(
        case_id="R-kind-family-dominating",
        claims=("PR12",),
        reason="link_kind_deferred",
        declared="link_declarations naming kind = 'family-dominating'",
        why="Section 1.3, second deferral; the mathematics is prop:common",
        derivation="""\
"What is missing is NOT THE COMPOSITION RULE BUT THE FAMILY ITSELF: certified
outer sets of Gram tuples are deferred out of receiver-povm v1, and the operator
factorization such a link would rest on is douglas1966majorization Thm. 1."
Section 2.3's `douglas_data` output key is `null` for exactly this reason, "so
that adding one later IS NOT A SCHEMA CHANGE". A declaration naming a device
FAMILY additionally trips `device_family_unsupported`.""",
    ),
    RefusalCase(
        case_id="R-kind-label-space",
        claims=("PR12",),
        reason="link_kind_deferred",
        declared="link_declarations naming kind = 'label-space'",
        why="Section 1.3, fourth deferral -- the one with NO SOURCE AT ALL",
        derivation="""\
"It carries A WARNING THE OTHER THREE DO NOT: there is NO SOURCE AT ALL for it
-- the internal note that would have supported it DOES NOT EXIST -- so it is
originate-from-scratch work." Nothing in the contract depends on it: the
concrete blinding construction of Section 4.9 runs on a declared finite
blinding-mode set and a POVM on the blinding register.""",
    ),
    RefusalCase(
        case_id="R-approximate",
        claims=("PR12",),
        reason="approximate_squashing_unsupported",
        declared="a link declaring Lambda+(F_v) = M_v + E with ||E|| <= eps, "
        "i.e. status = 'certified_outer'",
        why="Theorem thm:transfer has NO PENALTY SLOT",
        derivation="""\
Section 1.3: approximate squashing is "deliberately NOT a parameter of Theorem
thm:transfer: that theorem is AN EQUALITY OF OUTPUT STATES WITH NO PENALTY SLOT,
so an approximate relation needs A NEW THEOREM converting the error into a
security penalty, and UNTIL THERE IS ONE THE REQUEST IS REFUSED." Section 2.3
adds that `exact_identity` carries "NO certified bound and NO approximation
EVER", and Section 2.3's `status` key emits `exact` only.

THE EXACT SUBSTITUTE THAT IS AVAILABLE is operator domination with a declared
weight, Corollary cor:instances (i) -- the BRANCH-convex case of Group PR-E --
whose published form is nahar2025imperfect Thm. 3, Eqs. (20)-(23). "A device has
the form (i) whenever its POVM DOMINATES a characterized one."
""",
    ),
    RefusalCase(
        case_id="R-device-family",
        claims=("PR12",),
        reason="device_family_unsupported",
        declared="a receiver artifact declaring a FAMILY {A_k^(xi)}_{xi in Xi} "
        "rather than one Gram tuple",
        why="ARCHITECTURE_SPEC.md Section 7.3; version 1 declares ONE device",
        derivation="""\
Assumption A-RECV: "a single device family, uncertainty set or characterization
protocol appears NOWHERE: VERSION 1 REDUCES ONE DECLARED RECEIVER." This refusal
is also one of the four reasons Section 1.4 gives for judging the
family-wide-optical-bound escalation trigger NOT to fire.""",
    ),
    RefusalCase(
        case_id="R-no-certificate",
        claims=("PR11", "PR12"),
        reason="constraint_without_certificate",
        declared="the entry O^ = F^FSS_v0 - (1/2) Pi_flag on WP3, where the "
        "declared weight is p_v0 = 1/4",
        why="Theorem thm:licence's hypothesis eq:certificate",
        derivation="""\
The pull-back is M_v0 - (1/2)Pi_>N = [2/3] (+) (blk M^{>N}_v0 - (1/2)1), whose
above-cutoff eigenvalues are 7/8 - 1/2 = 3/8 and 1/4 - 1/2 = -1/4. THE SECOND IS
NEGATIVE, so eq:certificate FAILS with the relation >= and c = 0, and no other
(relation, constant) pair rescues it: the operator is neither positive, nor
negative, nor a multiple of the identity. NO CERTIFICATE, NO ENTRY -- and by the
presence rule, no licence either.

The number 1/2 exceeds the certified weight 1/4, so this is precisely a
declaration asserting MORE than the receiver artifact certifies. Compare
WP3-cert-positivity, where the same shape at p_v0 = 1/4 pulls back to
[2/3] (+) (5/8)M'_v0 >= 0 and IS admitted.""",
    ),
    RefusalCase(
        case_id="R-data-dependent",
        claims=("PR11", "PR12"),
        reason="data_dependent_constant",
        declared="an entry whose c_k is declared as 'the observed relative "
        "frequency of outcome v0 in this run'",
        why="Assumption A-CONST, Remark rem:notlicensed (c)",
        derivation="""\
"Every constant c_k in an emitted entry is FIXED BEFORE THE PROTOCOL RUN by the
device fact that certifies it, and IS NOT A FUNCTION OF ANY STATISTIC OBSERVED
DURING THE RUN." Remark rem:notlicensed (c) adds that such an entry "would be
UNSOUND HERE REGARDLESS OF PROVENANCE, and the module REFUSES TO BUILD ONE".

Remark rem:published names the concrete live hazard: the CAP form
W <= (p(e) - a)/(b - a) contains the run's observed p(e), so "WHAT THIS MODULE
MAY NEVER EMIT IS THE CAP". The admissible object is the OPERATOR entry
eq:two-sector-entry with relation >= and c = 0, frozen in Group PR-C, "of which the cap
is A RUN-TIME CONSEQUENCE AND NOT A DECLARATION".

THE ONLY SANCTIONED CARRIER of observed data on the platform is the acceptance
set, "which belongs to a different module and appears NOWHERE in this
contract".""",
    ),
    RefusalCase(
        case_id="R-licence-missing",
        claims=("PR11", "PR12"),
        reason="licence_missing",
        declared="constraint_list carrying the cor:fssinstance entry while "
        "attack_set_license is absent",
        why="the presence rule of Section 2.3 and Definition def:link",
        derivation="""\
"`attack_set_license` is PRESENT EXACTLY WHEN CList != empty", and Section 2.5's
fail_closed convention adds "NO LICENCE IS EMITTED WITHOUT ITS CERTIFICATE".
ARCHITECTURE_SPEC.md Section 7.3's condition this discharges is "the squashed
attack set is not shown to contain the physical image" -- which is exactly what
a constraint list without a licence would leave unshown.""",
    ),
    RefusalCase(
        case_id="R-licence-without-constraints",
        claims=("PR11", "PR12"),
        reason="licence_without_constraints",
        declared="an EMPTY constraint_list with an attack_set_license present",
        why="the same presence rule, in the other direction",
        derivation="""\
THE RULE IS AN IFF, and both directions are refusals with DIFFERENT reasons. A
licence with nothing to license is not harmless: it would attest an attack-set
restriction that the artifact does not carry, and a consumer gating on PRESENCE
(Remark rem:gateweight: the gate "rests entirely on part (ii)") would treat the
declaration as licensed when its constraint list is empty. The `encoded` route
emits an empty list AND NO LICENCE.""",
    ),
    RefusalCase(
        case_id="R-route-both",
        claims=("PR6", "PR11", "PR12"),
        reason="route_not_single_valued",
        declared="route = 'both'",
        why="Remark rem:tworoutes; the cross-channel pairing eq:crosspairing "
        "is UNSOUND",
        derivation="See TIGHT in Group PR-K for the numbers that make the "
        "pairing unsound, and for why the remedy is STRUCTURAL: two requests "
        "give a caller both bundles with NO SCHEMA IN WHICH THE UNSOUND PAIRING "
        "CAN BE EXPRESSED.",
    ),
    RefusalCase(
        case_id="R-channel-mismatch",
        claims=("PR11", "PR12"),
        reason="constraint_channel_mismatch",
        declared="the cor:fssinstance entry emitted on a link whose channel "
        "witness is Lambda^WP",
        why="Definition def:link binds the two PER LINK; rem:channel-choice (c)",
        derivation="See TIGHT in Group PR-K: the same entry pulls back to 0 "
        "under its own channel and to -1/5 under the other, and the negative "
        "value excludes a state REACHABLE UNDER THAT OTHER CHANNEL.",
    ),
    RefusalCase(
        case_id="R-alphabet-order",
        claims=("PR12",),
        reason="alphabet_or_order_mismatch",
        declared="the receiver artifact declares Y in the order "
        "(y_empty, y_1, y_2, y_mc) while the request declares "
        "(y_1, y_empty, y_2, y_mc)",
        why="ARCHITECTURE_SPEC.md Section 7.3",
        derivation="""\
Section 2.5's `subsystem_order` makes the flag basis "IN THE DECLARED ORDER OF
V = Y x T WITH Y MAJOR", and Section 2.3's `wpfss_data` emits "the flag basis IN
THE DECLARED ORDER OF V". A permuted Y therefore permutes the flag basis, and
with it every emitted F_v and every sector label -- SILENTLY, because the
permuted objects are still POVMs summing to the identity. The refusal exists
because NO LATER CHECK WOULD CATCH IT. The same reason covers a disagreement in
SECTOR order or in the occupation-vector BASIS order, which Section 2.5 inherits
UNCHANGED from the receiver artifact.""",
    ),
    RefusalCase(
        case_id="R-post-processing-order",
        claims=("PR4", "PR12"),
        reason="post_processing_order_violated",
        declared="a request to apply the squashing link FIRST and the "
        "dark-count channel afterwards",
        why="Remark rem:intertwining",
        derivation="""\
Lemma lem:linear (i) applies a post-processing to BOTH SIDES AT ONCE, which is
why Section 2.2 puts the classical steps FIRST. It does NOT say a classical map
before a FIXED squasher may be moved across it: that asks whether P' M = P M has
a stochastic solution P', "A LINEAR FEASIBILITY PROBLEM IN P' THAT HAS NO
SOLUTION IN GENERAL, and none whenever the map P' -> P' M fails to have P M in
the image of the stochastic matrices". VERSION 1 NEVER ASKS IT: the order is
fixed and the request is refused.""",
    ),
    RefusalCase(
        case_id="R-unsound-transplant",
        claims=("PR3", "PR12"),
        reason="unsound_constraint_requested",
        declared="the OPERATOR-form entry sum_y F_(y,t) = q_t 1_Q",
        why="Remark rem:unsound",
        derivation="See PROBE22_UNSOUND in Group PR-D, which freezes the "
        "reachable state and the projector on which the operator form fails "
        "while the expectation form holds.",
    ),
)


# ===========================================================================
#  Group PR-M -- the receiver-artifact consumption path (Section 2.2)
# ===========================================================================
#
#  Every case here is a DECLARED CLASSICAL MATRIX and a DECLARED WEIGHT, and
#  nothing optical: Section 1.4's reason for judging the family-wide-optical-
#  bound escalation trigger not to fire is that "the improvement factor comes
#  from the DECLARED STOCHASTIC MATRIX R^cg AND NOT FROM OPTICS", and this group
#  is that sentence made checkable.


@dataclass(frozen=True)
class WeightRouteCase:
    """One receiver declaration routed through Section 2.2 and eq:weightroute."""

    case_id: str
    claims: tuple[str, ...]
    ports: int
    #: The declared letters of Y, in the emitted order.
    letters: tuple[str, ...]
    #: (column letter, ((row letter, value), ...)) -- R^cg column by column.
    descended_matrix: tuple[tuple[str, tuple[tuple[str, F], ...]], ...]
    #: (bounded letter, is-absorbing, r_min) triples, one per slot entry.
    bounded_letters: tuple[tuple[str, bool, F], ...]
    #: (bounded letter, p_i) -- the t-uniform slot weights.
    slot_weights: tuple[tuple[str, F], ...]
    #: (setting, q_t).
    probe_weights: tuple[tuple[str, F], ...]
    #: ((letter, setting), p_(y,t)) for the BOUNDED letters; zero elsewhere.
    emitted_weights: tuple[tuple[tuple[str, str], F], ...]
    total_weight: F | None
    refusal_reason: str | None
    derivation: str


RC2 = WeightRouteCase(
    case_id="RC2",
    claims=("PR6",),
    ports=2,
    letters=("y_empty", "y_1", "y_2", "y_mc"),
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(3, 5)),
                ("y_1", F(3, 20)),
                ("y_2", F(1, 5)),
                ("y_mc", F(1, 20)),
            ),
        ),
        (
            "y_1",
            (("y_empty", F(0)), ("y_1", F(3, 4)), ("y_2", F(0)), ("y_mc", F(1, 4))),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(4, 5)), ("y_mc", F(1, 5))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    bounded_letters=(("y_mc", True, F(1, 20)),),
    slot_weights=(("y_mc", F(1, 10)),),
    probe_weights=(("t_off", F(2, 3)), ("t_on", F(1, 3))),
    emitted_weights=(
        (("y_mc", "t_off"), F(29, 300)),
        (("y_mc", "t_on"), F(29, 600)),
    ),
    total_weight=F(29, 200),
    refusal_reason=None,
    derivation="""\
K = 2 with the CANONICAL declaration of Eq. eq:canonicalcg: cg is injective off
MC = {S : |S| >= 2} = {{1,2}} and constant on it, so
Y = {y_empty, y_1, y_2, y_mc} and cg^{-1}(y_mc) = MC -- THE FIBRE CONDITION
HOLDS, with the single slot entry (MC, p_mc) that receiver-povm 0.1.3 actually
emits.

THE DARK-COUNT CHANNEL is the independent per-port product form with
p_dc|1 = 1/5 and p_dc|2 = 1/4, so R_{S|S'} = 0 unless S' subset S (MONOTONE) and
otherwise R_{S|S'} = prod_{k in S\\S'} p_dc|k prod_{k not in S} (1 - p_dc|k).
Column by column, with a = 1/5, b = 1/4:
    col empty : (ab' , ab' ...) explicitly ((4/5)(3/4), (1/5)(3/4), (4/5)(1/4),
                (1/5)(1/4)) = (3/5, 3/20, 1/5, 1/20), summing to
                12/20 + 3/20 + 4/20 + 1/20 = 1 ;
    col {1}   : (0, 3/4, 0, 1/4)  -- port 2 silent, or a dark count at 2 ;
    col {2}   : (0, 0, 4/5, 1/5) ;
    col {1,2} : (0, 0, 0, 1)     -- multiclicks are absorbing under monotone R.

IT DESCENDS, and the test is DIRECT: P(y|S') = sum_{S in cg^{-1}(y)} R_{S|S'}
depends on S' only through cg(S'), trivially here since cg is injective off MC
and MC is a single pattern. The resulting R^cg is the matrix above and is
column-stochastic.

ABSORBING AT THE BOUNDED LETTER: R^cg_{y_mc|y_mc} = 1, which
Proposition prop:route's last sentence proves in general under
Eq. eq:canonicalcg.

r_min,1 = min over y' != y_mc of R^cg_{y_mc|y'} = min(1/20, 1/4, 1/5) = 1/20 --
THE MINIMUM IS OVER ROW y_mc ACROSS THE OTHER COLUMNS, and 1/20 comes from the
EMPTY column, which is the smallest because it needs BOTH ports to fire
spuriously.

EQ. eq:weightroute at p_1 = 1/10:
    (1 - r_min) p_1 + r_min = (19/20)(1/10) + 1/20 = 19/200 + 10/200 = 29/200 ,
so p_(y_mc, t_off) = (2/3)(29/200) = 29/300 and
p_(y_mc, t_on) = (1/3)(29/200) = 29/600, and p_(y,t) = 0 FOR EVERY OTHER (y,t).
Total p = 29/300 + 29/600 = 58/600 + 29/600 = 87/600 = 29/200 < 1, so the
`total_weight_not_below_one` test passes.

THE IMPROVEMENT IS REAL AND SMALL: 29/200 > 1/10 = 20/200, so the dark counts
SHARPEN the weight by 9/200. Corollary cor:oneabsorbing says this can happen
only when there is exactly ONE bounded letter -- as here, r = 1.""",
)

RC1MIN = WeightRouteCase(
    case_id="RC1MIN",
    claims=("PR6",),
    ports=2,
    letters=("y_1",),
    descended_matrix=(("y_1", (("y_1", F(1)),)),),
    bounded_letters=(("y_1", True, F(0)),),
    slot_weights=(("y_1", F(1, 2)),),
    probe_weights=(("t_off", F(2, 3)), ("t_on", F(1, 3))),
    emitted_weights=(
        (("y_1", "t_off"), F(1, 3)),
        (("y_1", "t_on"), F(1, 6)),
    ),
    total_weight=F(1, 2),
    refusal_reason=None,
    derivation="""\
THE EMPTY-MINIMUM CONVENTION, and the ONLY case that exercises it. Section 2.1
and Proposition prop:route both state it: "r_min,i := 0 when that minimum is
over the empty set (i.e. WHEN Y = {y_i}) -- THE CONSERVATIVE VALUE".

DECLARATION. K = 2 with the same monotone product dark-count channel, and a
coarse-graining that is CONSTANT on all of 2^[K], so Y = {y_1} is a SINGLETON.
Then P(y_1|S') = sum_S R_{S|S'} = 1 for every S', constant, so R DESCENDS with
R^cg = [1] -- a 1x1 column-stochastic matrix. The bounded set is
O_1 = cg^{-1}(y_1) = 2^[K], EXACTLY A FIBRE, and the letter is absorbing
because R^cg_{y_1|y_1} = 1.

THE MINIMUM IS OVER THE EMPTY SET: there is no y' != y_1. The convention sets
r_min,1 = 0, and eq:weightroute REDUCES TO THE UN-IMPROVED BOUND
p_(y_1,t) = q_t p_1 -- (2/3)(1/2) = 1/3 and (1/3)(1/2) = 1/6, total 1/2 < 1.

WHY THE CONVENTION IS THE CONSERVATIVE ONE AND NOT A TIE-BREAK. eq:weightroute
is q_t((1 - r)p_i + r), which is INCREASING in r for p_i <= 1; setting r = 0
gives the SMALLEST admissible weight, hence the CLEANEST target, hence the most
generous adversary (Corollary cor:monotone). Any other convention -- taking the
minimum over an empty set to be 1, say, as an infimum over the reals would --
would ASSERT A WEIGHT THE DEVICE HAS NOT BEEN SHOWN TO HAVE, which is the
unsafe direction A-RECV's ledger row calls a security break.

THE SLOT WEIGHT p_1 = 1/2 IS ADMISSIBLE because the certified quantity is
sum_{S in 2^[K]} blk M^{>N}_{S|t} = 1 >= (1/2) 1; p_1 = 1 would also be
certified and would be REFUSED at the p < 1 test, which is the case PEQONE
freezes.""",
)

RC3 = WeightRouteCase(
    case_id="RC3",
    claims=("PR6",),
    ports=3,
    letters=("y_0", "y_s", "y_mc"),
    descended_matrix=(
        ("y_0", (("y_0", F(1, 2)), ("y_s", F(1, 4)), ("y_mc", F(1, 4)))),
        ("y_s", (("y_0", F(0)), ("y_s", F(1)), ("y_mc", F(0)))),
        ("y_mc", (("y_0", F(0)), ("y_s", F(0)), ("y_mc", F(1)))),
    ),
    bounded_letters=(("y_s", True, F(0)), ("y_mc", True, F(0))),
    slot_weights=(("y_s", F(1, 5)), ("y_mc", F(1, 10))),
    probe_weights=(("t0", F(3, 4)), ("t1", F(1, 4))),
    emitted_weights=(
        (("y_s", "t0"), F(3, 20)),
        (("y_s", "t1"), F(1, 20)),
        (("y_mc", "t0"), F(3, 40)),
        (("y_mc", "t1"), F(1, 40)),
    ),
    total_weight=F(3, 10),
    refusal_reason=None,
    derivation="""\
THE r >= 2 CASE, Corollary cor:oneabsorbing, where EVERY r_min,i IS ZERO.

DECLARATION. K = 3; cg sends the empty pattern to y_0, all THREE single clicks
to y_s, and all multiclicks to y_mc, so Y has three letters and the two bounded
sets O_1 = cg^{-1}(y_s) = {{1},{2},{3}} and O_2 = cg^{-1}(y_mc) = MC are
DISJOINT AND EACH EXACTLY A FIBRE, as Section 2.1 requires. r = 2.

THE DARK-COUNT CHANNEL is a DECLARED column-stochastic monotone matrix -- which
Definition def:darkadm of the supplier's contract permits alongside the product
form -- acting only on the empty pattern:
    R_{empty|empty} = 1/2 , R_{{1}|empty} = 1/4 , R_{{1,2}|empty} = 1/4 ,
and the identity on every other column. Monotone: every non-zero entry has
S superset S'. It DESCENDS: the columns of the three single-click patterns are
all e_{{k}}, giving P(y_s|{k}) = 1 for each, and the multiclick columns are all
identities, giving P(y_mc|S') = 1 -- CONSTANT ON EACH FIBRE, which is what
descent requires.
    R^cg col y_0  = (1/2, 1/4, 1/4)   [rows y_0, y_s, y_mc]
    R^cg col y_s  = (0, 1, 0)
    R^cg col y_mc = (0, 0, 1)
BOTH BOUNDED LETTERS ARE ABSORBING.

AND THEN BOTH r_min VANISH, which is Corollary cor:oneabsorbing's content and
its proof in one line: "Column y_j of R^cg is a probability vector and
R^cg_{y_j|y_j} = 1 by eq:absorbing, so EVERY OTHER ENTRY OF THAT COLUMN
VANISHES; in particular R^cg_{y_i|y_j} = 0. Since y_j != y_i, the minimum
defining r_min,i ranges over a set CONTAINING y_j, so 0 <= r_min,i <= 0."
Concretely r_min at y_s = min(1/4, 0) = 0 and r_min at y_mc = min(1/4, 0) = 0 --
in each case the OTHER absorbing column supplies the zero, and the non-zero 1/4
from the y_0 column is irrelevant because a minimum only needs one zero.

EQ. eq:weightroute therefore reads p_(y_i,t) = q_t p_i throughout:
    (y_s, t0)  -> (3/4)(1/5)  = 3/20 ,   (y_s, t1)  -> (1/4)(1/5)  = 1/20 ,
    (y_mc, t0) -> (3/4)(1/10) = 3/40 ,   (y_mc, t1) -> (1/4)(1/10) = 1/40 ,
total 6/40 + 2/40 + 3/40 + 1/40 = 12/40 = 3/10 < 1, which also equals
sum_i p_i = 1/5 + 1/10 -- as it must, since sum_t q_t = 1 and every r_min is
zero. The input validation sum_i p_i <= 1 passes at 3/10.

"WHICH IS SOUND, MERELY NOT SHARPENED BY THE DARK COUNTS" (Section 2.2, fact
(c)). A positive r_min can occur "FOR AT MOST ONE BOUNDED LETTER, AND ONLY WHEN
r = 1" -- RC2 is that case.""",
)

RCABS = WeightRouteCase(
    case_id="RCABS",
    claims=("PR6", "PR12"),
    ports=2,
    letters=("y_empty", "y_1", "y_2", "y_mc"),
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(3, 4)),
                ("y_1", F(0)),
                ("y_2", F(1, 4)),
                ("y_mc", F(0)),
            ),
        ),
        (
            "y_1",
            (("y_empty", F(0)), ("y_1", F(3, 4)), ("y_2", F(0)), ("y_mc", F(1, 4))),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(1)), ("y_mc", F(0))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    bounded_letters=(("y_1", False, F(0)),),
    slot_weights=(("y_1", F(1, 5)),),
    probe_weights=(("t0", F(1)),),
    emitted_weights=(),
    total_weight=None,
    refusal_reason="bounded_letter_not_absorbing",
    derivation="""\
REMARK rem:absorbneeded, FROZEN IN THE UNSAFE DIRECTION. "Without eq:absorbing,
eq:routebound is NOT MERELY UNPROVED BUT FALSE, IN THE DIRECTION THAT CERTIFIES
A WEIGHT THE DEVICE DOES NOT HAVE."

DECLARATION. K = 2, the same canonical coarse-graining, and the monotone product
dark-count channel in the SUB-CASE the remark names: p_dc|1 = 0 and
p_dc|2 = 1/4. The bounded letter is the SINGLE-CLICK y_1 = cg({1}), not the
multiclick one. Then
    R^cg_{y_1|y_1} = prod_{k' != 1} (1 - p_dc|k') = 1 - 1/4 = 3/4  <  1 ,
because "a dark count at another port MOVES THE PATTERN {1} INTO THE MULTICLICK
SET AND NEVER BACK". NOT ABSORBING -> REFUSED.

AND r_min,1 = 0, so the formula would not be saved by it: monotonicity "kills AT
LEAST ONE other column -- any other single-click letter y' = cg({k''}) has
R^cg_{y_1|y'} = 0 since {k''} is not a subset of {1}", and here the y_empty
column also vanishes because p_dc|1 = 0. Row y_1 across the other three columns
is (0, 0, 0), so r_min,1 = 0.

THE FALSE ASSERTION, WITH NUMBERS. Take the above-cutoff block one-dimensional
(the argument is dimension-free; one dimension makes the operator inequality a
scalar one) with
    blk M^{>N}_{y|t} = (1/5, 1/5, 1/5, 2/5) over (y_empty, y_1, y_2, y_mc) ,
a complete family, and the declared slot weight p_1 = 1/5, which is exactly
certified at y_1. Eq. eq:weightroute WOULD ASSERT, at q_t = 1,
    (1 - 0)(1/5) + 0 = 1/5 .
THE TRUTH: row y_1 of R^cg is (0, 3/4, 0, 0), so
    blk M~^{>N}_{y_1|t} = (3/4) blk M^{>N}_{y_1|t} = (3/4)(1/5) = 3/20 .
1/5 = 4/20 > 3/20. THE ASSERTED WEIGHT EXCEEDS THE TRUE ONE BY 1/20 -- exactly
the factor R^cg_{y_1|y_1} = 3/4 the remark identifies, "and the columns that
remain DO NOT COMPENSATE".

WHY THAT IS A SECURITY BREAK AND NOT A RATE LOSS: "A weight asserted ABOVE the
true one makes eq:certweights FALSE, so F^WP is NOT A SQUASHING of the real
receiver and THE EMITTED LICENCE CERTIFIES AN INCLUSION THAT DOES NOT HOLD --
the failure Assumption A-RECV's ledger row calls a security break." Version 1
therefore takes eq:absorbing as a DECLARED INPUT VALIDITY CONDITION and refuses;
"IT STATES NO BOUND FOR THAT CASE".""",
)

WEIGHT_ROUTE_CASES: tuple[WeightRouteCase, ...] = (RC2, RC1MIN, RC3, RCABS)

#: Remark rem:descentneedsconstant: a MONOTONE R and a coarse-graining meeting
#: TWO of Eq. eq:canonicalcg's three clauses for which R^cg is NOT well defined.
DESCENT_COUNTEREXAMPLE: dict[str, object] = {
    "case_id": "DESCENT-K4",
    "claims": ("PR6", "PR12"),
    "refusal_reason": "dark_counts_do_not_descend",
    "ports": 4,
    "dark_count_probability": F(1, 3),
    "fibre_of_y_a": ("{1,2}", "{1,2,4}", "{1,2,3,4}"),
    "p_ya_given_12": F(7, 9),
    "p_ya_given_124": F(1),
    "closed_form": "P(y_a | {1,2}) = (1-p)^2 + p(1-p) + p^2 = 1 - p + p^2",
    "derivation": """\
K = 4, INDEPENDENT PER-PORT DARK COUNTS of common probability p = 1/3, and the
coarse-graining that sends {1,2}, {1,2,4} and {1,2,3,4} to y_a, every other
multiclick pattern to y_b, and is injective with distinct fresh letters off MC.

TWO OF eq:canonicalcg's THREE CLAUSES HOLD: cg is injective on
2^[K] \\ MC, and cg^{-1}({y_a, y_b}) = MC. THE CONSTANCY CLAUSE FAILS -- cg is
not constant on MC, splitting it across y_a and y_b -- and that is enough to
break descent:
    P(y_a | {1,2})   = (1-p)^2 + p(1-p) + p^2 = 1 - p + p^2 = 7/9 at p = 1/3 ,
    P(y_a | {1,2,4}) = (1-p) + p = 1 ,
"two columns with the SAME cg-IMAGE and DIFFERENT VALUES, so R^cg is NOT WELL
DEFINED."

THE FIRST COUNT is over the supersets of {1,2} lying in cg^{-1}(y_a): {1,2}
itself (ports 3 and 4 silent, (1-p)^2), {1,2,4} (a dark count at 4, port 3
silent, p(1-p)), and {1,2,3,4} (dark counts at both, p^2). At p = 1/3:
9/9 - 3/9 + 1/9 = 7/9. THE SECOND is over the supersets of {1,2,4} there,
namely itself (port 3 silent, 1-p) and {1,2,3,4} (p), summing to 1.

WHAT THE COUNTEREXAMPLE RULES OUT, and it is a statement about the CHECK and not
about the mathematics: "what it rules out is TESTING THE STATED CONDITION
Eq. eq:canonicalcg IN PLACE OF THE DESCENT PROPERTY ITSELF, which is why the
fail-closed set of Section 4.13 TESTS DESCENT DIRECTLY and treats eq:canonicalcg
ONLY AS A SHORTCUT THAT MUST ITSELF BE CHECKED IN FULL." The canonical
declaration maps all of MC to the single letter mc and is unaffected -- RC2 is
that case.""",
}


# ===========================================================================
#  Group PR-N -- the assumption ledger (Section 5)
# ===========================================================================


@dataclass(frozen=True)
class AssumptionRow:
    """One row of the assumption ledger, with its machine key and scope."""

    assumption_id: str
    machine_key: str
    supports: tuple[str, ...]
    #: True for the two the contract says this module CAN NEVER VERIFY.
    never_verifiable: bool
    #: The direction the "If violated" column records.
    violation_is_unsafe: bool
    note: str


ASSUMPTION_LEDGER: tuple[AssumptionRow, ...] = (
    AssumptionRow(
        assumption_id="A-DIM",
        machine_key="finite_target_and_side_registers",
        supports=(
            "PR1",
            "PR2",
            "PR3",
            "PR4",
            "PR5",
            "PR6",
            "PR7",
            "PR8",
            "PR9",
            "PR10",
            "PR11",
            "PR12",
        ),
        never_verifiable=False,
        violation_is_unsafe=False,
        note="Every constraint and the licence LOSE THEIR PROOF, not merely "
        "their tightness: Fact fact:sep (ii) is unavailable, so eq:transport "
        "and eq:compositeadjoint are not established.",
    ),
    AssumptionRow(
        assumption_id="A-MEAS",
        machine_key="measurement_only_receiver",
        supports=(
            "PR2",
            "PR3",
            "PR4",
            "PR5",
            "PR6",
            "PR7",
            "PR8",
            "PR9",
            "PR10",
            "PR11",
            "PR12",
        ),
        never_verifiable=False,
        violation_is_unsafe=True,
        note="A retained post-measurement quantum system is the concrete "
        "violation, and it is UNSAFE: the squashed model would describe A "
        "DIFFERENT PROTOCOL.",
    ),
    AssumptionRow(
        assumption_id="A-ROUND",
        machine_key="round_homogeneity",
        supports=(
            "PR2",
            "PR3",
            "PR4",
            "PR5",
            "PR6",
            "PR7",
            "PR8",
            "PR9",
            "PR10",
            "PR11",
            "PR12",
        ),
        never_verifiable=False,
        violation_is_unsafe=False,
        note="INAPPLICABILITY RATHER THAN A SILENT BREAK: the module must "
        "re-enter with per-round data, and the consuming engine's own "
        "round-homogeneity requirement fails first.",
    ),
    AssumptionRow(
        assumption_id="A-RECV",
        machine_key="receiver_artifact_accepted",
        supports=("PR6", "PR9", "PR11"),
        never_verifiable=True,
        violation_is_unsafe=True,
        note="SECURITY BREAK IN THE UNSAFE DIRECTION. This is the assumption "
        "the emitted licence record NAMES, and the reason it names the "
        "receiver artifact BY VERSION.",
    ),
    AssumptionRow(
        assumption_id="A-BLIND",
        machine_key="blinding_model_form",
        supports=("PR8", "PR9"),
        never_verifiable=True,
        violation_is_unsafe=True,
        note="What is NOT at risk: the blinded branch being uncharacterized is "
        "MODELLED, NOT ASSUMED AWAY (def:blindmodel (d)). What IS assumed is "
        "the FORM M_v = sum_b M_{v|b} (x) N_b.",
    ),
    AssumptionRow(
        assumption_id="A-PROBE",
        machine_key="probe_setting_private",
        supports=("PR6", "PR9"),
        never_verifiable=False,
        violation_is_unsafe=True,
        note="The setting register would have to be HANDED TO THE ADVERSARY "
        "(Remark rem:variants), and the joint family would not be a POVM with "
        "a common squashing channel.",
    ),
    AssumptionRow(
        assumption_id="A-TSM",
        machine_key="test_statistics_model",
        supports=("PR6", "PR9"),
        never_verifiable=False,
        violation_is_unsafe=True,
        note="A state-independent fraction would be assumed where none exists; "
        "the consuming engine's own A-TSM would be contradicted.",
    ),
    AssumptionRow(
        assumption_id="A-NOSRC",
        machine_key="source_stage_empty",
        supports=("PR12",),
        never_verifiable=False,
        violation_is_unsafe=True,
        note="The chain no longer records the order it was composed in, which "
        "is EXACTLY the silent failure decision (2) exists to prevent.",
    ),
    AssumptionRow(
        assumption_id="A-CONST",
        machine_key="declared_constants",
        supports=("PR11", "PR12"),
        never_verifiable=False,
        violation_is_unsafe=True,
        note="A data-dependent right-hand side makes the declaration depend on "
        "the run, so the licence certifies an inclusion that need not hold.",
    ),
)


# ===========================================================================
#  The registry entries
# ===========================================================================

PR_ORACLES: tuple[PROracleEntry, ...] = (
    PROracleEntry(
        oracle_id="O-PR-RELATION",
        claims=("PR1",),
        kind="toy-instance",
        subject=(
            "The squashing relation on WP3: exact Gaussian-rational Kraus "
            "operators, the pulled-back M = Lambda+(F) for both targets, and "
            "the transported cutoff projectors of Eq. eq:transportproj."
        ),
        derivation=WP3_RELATION_WP.derivation,
        value=None,
        hypotheses=("A-DIM",),
    ),
    PROracleEntry(
        oracle_id="O-PR-UNIQUENESS",
        claims=("PR1", "PR3"),
        kind="structural-identity",
        subject=(
            "Lemma lem:statistics' uniqueness clause: two channels realizing "
            "the SAME relation agree on span({F_v} u {O^_k}) and DISAGREE off "
            "it, with the disagreement frozen as an exact complex matrix."
        ),
        derivation=WP3_RELATION_PRIME.derivation,
        value=None,
        hypotheses=("A-DIM",),
    ),
    PROracleEntry(
        oracle_id="O-PR-STATISTICS",
        claims=("PR1",),
        kind="toy-instance",
        subject=(
            "Statistics equality on four inputs -- including one with coherence "
            "across the cutoff -- and on two correlated side-system pairings "
            "with a Hermitian, NON-POSITIVE side operator."
        ),
        derivation=WP3_STATISTICS[3].derivation,
        value=F(68, 125),
        hypotheses=("A-DIM",),
    ),
    PROracleEntry(
        oracle_id="O-PR-TRANSFER",
        claims=("PR2",),
        kind="toy-instance",
        subject=(
            "Theorem thm:factorization at n = 1: the physical and the squashed "
            "run return THE SAME output state, entry by entry."
        ),
        derivation=TRANSFER_ONE_ROUND.derivation,
        value=None,
        hypotheses=("A-DIM", "A-MEAS", "A-ROUND"),
    ),
    PROracleEntry(
        oracle_id="O-PR-SOUND",
        claims=("PR3",),
        kind="structural-identity",
        subject=(
            "One sound transported constraint of each certificate type of "
            "Corollary cor:pullback, their intersection, and the reachable "
            "state a constraint excludes."
        ),
        derivation=CERT_POSITIVITY.derivation,
        value=F(0),
        hypotheses=("A-DIM", "A-MEAS", "A-ROUND"),
    ),
    PROracleEntry(
        oracle_id="O-PR-UNSOUND",
        claims=("PR3", "PR6"),
        kind="fail-closed",
        subject=(
            "Remark rem:unsound: the operator-form transplant of a physical "
            "identity, frozen with the reachable state and the projector on "
            "which it fails while the expectation form holds."
        ),
        derivation=str(PROBE22_UNSOUND["derivation"]),
        value="unsound_constraint_requested",
        hypotheses=("A-TSM", "A-PROBE"),
    ),
    PROracleEntry(
        oracle_id="O-PR-CALCULUS",
        claims=("PR4",),
        kind="structural-identity",
        subject=(
            "Lemma lem:linear (i) post-processing and (ii) the private setting; "
            "Proposition prop:pinching; and both legs of Lemma lem:obstructions "
            "with a refusing and a passing instance each."
        ),
        derivation=str(POSTPROCESSING_CASE["derivation"]),
        value=None,
        hypotheses=("A-DIM", "A-PROBE"),
    ),
    PROracleEntry(
        oracle_id="O-PR-BRANCHING",
        claims=("PR5",),
        kind="toy-instance",
        subject=(
            "Corollary cor:instances (i), the branch-weight constraint in BOTH "
            "its operator and its scalar form, and Lemma lem:top -- every POVM "
            "squashes to the flag PVM."
        ),
        derivation=str(BRANCH_MIXTURE["derivation"]),
        value=F(3, 4),
        hypotheses=("A-DIM",),
    ),
    PROracleEntry(
        oracle_id="O-PR-CHAIN",
        claims=("PR6",),
        kind="structural-identity",
        subject=(
            "Eq. eq:ladder with EXACT composition Lambda^FSS = Lambda~ o "
            "Lambda^WP on four inputs, the encoded constraint, the "
            "reverse-relation failure, and Remark rem:weightfree."
        ),
        derivation=str(CHAIN_LADDER["derivation"]),
        value=None,
        hypotheses=("A-RECV", "A-PROBE", "A-TSM"),
    ),
    PROracleEntry(
        oracle_id="O-PR-WEIGHTROUTE",
        claims=("PR6",),
        kind="toy-instance",
        subject=(
            "Section 2.2 and Eq. eq:weightroute on four receiver declarations: "
            "the descended matrix tested DIRECTLY, the absorbing check per "
            "bounded letter, r_min including the EMPTY-MINIMUM convention, and "
            "the r >= 2 case of Corollary cor:oneabsorbing."
        ),
        derivation=RC2.derivation,
        value=F(29, 200),
        hypotheses=("A-RECV", "A-PROBE"),
    ),
    PROracleEntry(
        oracle_id="O-PR-FLAGS",
        claims=("PR7",),
        kind="structural-identity",
        subject=(
            "Corollary cor:flagsenough on the zero-weight block, with TWO "
            "different source POVMs covered by ONE target, and the "
            "distinguishability that is lost."
        ),
        derivation=str(FLAGS_ENOUGH["derivation"]),
        value=F(1, 2),
        hypotheses=("A-DIM",),
    ),
    PROracleEntry(
        oracle_id="O-PR-MIXTURE",
        claims=("PR8",),
        kind="toy-instance",
        subject=(
            "Theorem thm:mixture with a NON-PROJECTIVE register POVM: the "
            "composed channel, the block-diagonal target, and the branch "
            "weights transported AS OPERATORS rather than as numbers."
        ),
        derivation=str(MIXTURE_CASE["derivation"]),
        value=None,
        hypotheses=("A-BLIND",),
    ),
    PROracleEntry(
        oracle_id="O-PR-OBSTRUCTION",
        claims=("PR10",),
        kind="structural-identity",
        subject=(
            "Proposition prop:obstruction: no classical-flag target encodes an "
            "event-level minimum-eigenvalue bound, by explicit two-dimensional "
            "counterexample with three outcomes."
        ),
        derivation=PR_OBSTRUCTION.derivation,
        value=F(1, 8),
        hypotheses=("A-DIM",),
    ),
    PROracleEntry(
        oracle_id="O-PR-LICENCE",
        claims=("PR11",),
        kind="structural-identity",
        subject=(
            "Theorem thm:licence in BOTH source modes: the adjoint-form "
            "admissible sets of Eqs. eq:attset and eq:attsetun, the per-entry "
            "certificate, and a composite attack landing in the set as an "
            "OPERATOR inequality on E'."
        ),
        derivation=LICENCE_TRUSTED.derivation,
        value=F(0),
        hypotheses=("A-DIM", "A-RECV", "A-CONST"),
    ),
    PROracleEntry(
        oracle_id="O-PR-CROSSPAIRING",
        claims=("PR6", "PR11"),
        kind="fail-closed",
        subject=(
            "Eq. eq:crosspairing at its TIGHT END, where the licensed entry "
            "paired with the encoded route's channel pulls back to a NEGATIVE "
            "operator and excludes a REACHABLE state."
        ),
        derivation=str(TIGHT["derivation"]),
        value=F(-1, 5),
        hypotheses=("A-RECV",),
    ),
    PROracleEntry(
        oracle_id="O-PR-ARTIFACT",
        claims=("PR12",),
        kind="structural-identity",
        subject=(
            "Definition def:link's TEN slots for the six implemented kinds, "
            "Definition def:chain's three conditions, and Theorem thm:chain's "
            "composite with status `exact`."
        ),
        derivation=CHAIN_WELL_FORMED.derivation,
        value="exact",
        hypotheses=("A-NOSRC",),
    ),
    PROracleEntry(
        oracle_id="O-PR-FAILCLOSED",
        claims=("PR12",),
        kind="fail-closed",
        subject=(
            "Section 4.13: AT LEAST ONE refusal case for every one of the "
            "TWENTY-ONE rows, carrying all TWENTY-FOUR verbatim reason strings."
        ),
        derivation="""\
Every rule of Section 4.13 "is DECIDED FROM DECLARED DATA BEFORE ANYTHING IS
EMITTED; a failure produces a refusal with a machine-readable reason and NO
ARTIFACT". REFUSAL_CASES carries one case per reason, with the declared datum
that trips it and the contract element that makes the rule necessary; the
integrity test proves that the set of reasons in REFUSAL_CASES equals
REFUSAL_REASONS equals the set in interface.yaml, so a twenty-fifth string
cannot be introduced on either side without a failing test.

THE COUNT: 24 strings over 21 rows, three rows naming two reasons each --
the chain row (`chain_ill_formed` / `source_link_after_receiver_link`), the
constraint-certificate row (`constraint_without_certificate` /
`data_dependent_constant`) and the licence-presence row (`licence_missing` /
`licence_without_constraints`). Each pair is TWO DIFFERENT FAILURES and not a
spelling variant, and each is frozen separately.

WHAT SECTION 4.13 SAYS ABOUT THE FIVE ARCHITECTURE_SPEC.md Section 7.3
CONDITIONS THAT HAVE NO ROW: "TWO are discharged UPSTREAM and are re-checked
here ONLY AS CONSISTENCY... TWO ARE IMPOSSIBILITIES RATHER THAN FAILURES, by
Lemma lem:ple1. ONE -- the Douglas dominator and contraction witness -- belongs
to a link kind version 1 REFUSES OUTRIGHT." No case is invented for any of
them.""",
        value=24,
        hypotheses=(),
    ),
    # -----------------------------------------------------------------------
    #  Group PR-O -- the declared operator tolerance (PR13), NEW AT 0.2.0
    # -----------------------------------------------------------------------
    PROracleEntry(
        oracle_id="O-PR13-EXACT-PSD",
        claims=("PR13",),
        kind="structural-identity",
        subject=(
            "Lemma lem:exactpsd: X >= 0 iff every sum of k x k PRINCIPAL minors "
            "e_k(X) is >= 0, and ||Z|| <= delta iff delta^2 1 - Z-dagger Z >= 0"
        ),
        derivation="""\
THE PREDICATE, NOT THE ALGORITHM. Eq. eq:psdtest and Eq. eq:normtest are the two
decisions every tolerance row reduces to, "decided by FINITELY MANY FIELD
OPERATIONS AND SIGN COMPARISONS IN F: NO ROUNDING, NO THRESHOLD, AND NO
EIGENVALUE IS COMPUTED".

TOL_ROW_CASES freezes ELEVEN instances, each with its e_k and its decision:
six admits and five refusals, over Proposition prop:tolrows (i)-(iv). Three
are chosen to exclude the tests an implementation is most likely to substitute
for eq:psdtest:
  * TOL-posdef-refuse-e1-passes:            e_1 >= 0 and e_2 < 0 -- the TRACE
    alone admits and the contract refuses;
  * TOL-posdef-refuse-leading-minors-pass:  both LEADING principal minors are 0
    and e_1 < 0 -- SYLVESTER'S CRITERION admits and the contract refuses;
  * TOL-threshold-form-boundary-admit:      W = 0 exactly -- a STRICT
    comparison refuses and the contract admits.
The value pinned is the number of frozen row decisions.

WHY dim H(C_0) = 2 AND NOT 1: at dimension one eq:psdtest degenerates to "the
entry is >= 0" and all three discriminators above vanish.""",
        value=11,
        hypotheses=("A-OPTOL", "A-DIM"),
    ),
    PROracleEntry(
        oracle_id="O-PR13-TOLPROP",
        claims=("PR13",),
        kind="structural-identity",
        subject=(
            "Lemma lem:tolprop: dcf = max_y sum_y' R^cg_{y|y'} with 1 <= dcf <= "
            "|Y|, and eta_v = q_t dcf eps_op after the classical post-processing"
        ),
        derivation="""\
THE DECLARATION DEFECT AFTER STEPS 1-2 OF SECTION 2.2, on TOL2.
    R^cg = [[1, 1/5], [0, 4/5]] , row sums 6/5 and 4/5, so dcf = 6/5 (eq:dcf),
    and 1 <= 6/5 <= 2 = |Y| as the lemma asserts.
    eta_(y,t0) = (2/3)(6/5)(1/100) = 12/1500 = 1/125 ,
    eta_(y,t1) = (1/3)(6/5)(1/100) =  6/1500 = 1/250 ,
    eta       = (6/5)(1/100)       =  6/500  = 3/250 >= max_v eta_v = 2/250 .
The value pinned is dcf.

THE PROPAGATION IS OBSERVABLE ON MATERIALISED MATRICES, not only in the bound:
TOL2_TILDE and TOL2_JOINT_NB freeze the families steps 1 and 2 build, and
TOL2-postproc-herm-y0t0-admit shows the block-level defect 1/100 becoming
1/150 = (2/3)(1/100) while the threshold becomes 2/125 = (2/3)(1/50) -- both
scaled by q_t0, which is why the decision is unchanged.

dcf IS COMPUTED FROM THE DECLARED MATRIX AND IS EXACT. Remark rem:tolboundary:
"dcf and every eta_v are computed from EXACT SCALARS AND EXACT BLOCK ENTRIES, SO
THE TOLERANCE RECORD IS ITSELF EXACT."

THE LOWER BOUND dcf >= 1 IS NOT AN ASSUMPTION BUT A CONSEQUENCE: column
stochasticity gives sum_y sum_y' R^cg_{y|y'} = |Y|, so the largest row sum is at
least the average, which is 1.""",
        value=F(6, 5),
        hypotheses=("A-OPTOL", "A-RECV"),
    ),
    PROracleEntry(
        oracle_id="O-PR13-TOLROWS",
        claims=("PR13",),
        kind="structural-identity",
        subject=(
            "Proposition prop:tolrows (i)-(iv): the Hermiticity, negative-part "
            "and completeness defects, and the same three after post-processing"
        ),
        derivation="""\
THE NECESSARY CONDITIONS OF ASSUMPTION A-OPTOL, DECIDED EXACTLY. The value
pinned is the number of parts, four.

TOL2 IS BUILT SO THAT THE TOLERANCE IS LOAD-BEARING AND THE PAIRING IS
OBSERVABLE. The same declaration is ADMITTED at eps_op = 1/100 and REFUSED at
eps_op = 0, and the refusals are on two different parts:
  * part (i) at eps_op = 0: ||A - A-dagger|| = 1/100 > 0 = 2 eps_op ;
  * part (ii) at eps_op = 0: A_h = [[3/4, 0], [0, -1/200]] has e_2 = -3/800 < 0.
"A DECLARED TOLERANCE CHANGES WHICH DECLARATIONS ARE ACCEPTED; IT CHANGES
NOTHING ABOUT HOW THE ACCEPTANCE IS DECIDED" (Section 1.4).

PASSING ESTABLISHES NOTHING, and that is stated rather than left implicit:
"they are NECESSARY CONDITIONS OF AN ASSUMPTION THIS MODULE CANNOT VERIFY, in
exactly the sense in which every rule of Section 4.13 has always been a
necessary condition of Assumption A-RECV". No case in this registry asserts that
a passing declaration satisfies A-OPTOL.

THE ROW REACHES NO OTHER FAMILY: TOL_SCOPE_CASES freezes the two families it
does not reach, each refused at every eps_op.""",
        value=4,
        hypotheses=("A-OPTOL", "A-DIM"),
    ),
    PROracleEntry(
        oracle_id="O-PR13-TOLERANCE-TRANSFER",
        claims=("PR13", "PR6", "PR9", "PR12"),
        kind="structural-identity",
        subject=(
            "Theorem thm:tolerance (i)-(v): the constructions run on the "
            "starred model, the emitted numbers are eta_v-close to it, "
            "certificates survive at a shifted constant, and NO key-length "
            "bound is asserted"
        ),
        derivation="""\
THE TRANSFER THEOREM. The value pinned is the number of parts, five, and the
fifth is the one that says what is NOT established.

PART (i) NAMES FIVE RESULTS THAT APPLY TO THE STARRED DATA VERBATIM --
def:blindmodel, def:targets, prop:chain, thm:mixture, thm:blinding -- AND
DELIBERATELY EXCLUDES A SIXTH: "THEOREM thm:licence IS DELIBERATELY NOT IN THAT
LIST. It too applies to the starred model, BUT NOT WITH THE CONSTANTS AN ENTRY
BUILT FROM DECLARED NUMBERS CARRIES... READING THIS PART AS CARRYING THE 0.1.3
CONSTANTS OVER VERBATIM IS EXACTLY THE ERROR CORollARY cor:tolentries EXISTS TO
PREVENT, AND IT IS UNSAFE IN THE DIRECTION THAT MATTERS." TOL_ENTRY_CASES is
that warning made checkable: every entry is frozen at BOTH constants.

PART (ii) CONFINES THE DIFFERENCE TO ONE BLOCK (Eq. eq:targetdefect) and gives
the three amounts of Eq. eq:targetposcomp, frozen in TOL2_TARGETPOSCOMP as
2/125, 1/125 and 3/125. "No declared branch POVM -- AND NO UNDECLARED ONE --
ENTERS THE DIFFERENCE AT ALL."

PART (iv) IS THE SHIFT RULE: c - delta for >=, c + delta for <=, and both for =.
Its proof needs only positivity and unitality of a channel adjoint, which is why
it costs no hypothesis beyond A-OPTOL.

PART (v) IS FROZEN AS AN ABSENCE AND NOTHING IN THIS REGISTRY CONTRADICTS IT:
no case here relates a key length computed from {F_v} to one computed from
{F*_v}, and none could -- "for which this contract has NO THEOREM AND VERSION 1
EMITS NO STATUS".

AT eps_op = 0 EVERYTHING COLLAPSES: "the starred family IS the declared one,
eta_v = 0, every difference above vanishes, and (i)-(iv) are the statements of
Sections 4.6-4.12 UNCHANGED". TOL2-tolerance-record-absent freezes that half.""",
        value=5,
        hypotheses=("A-OPTOL", "A-RECV", "A-BLIND", "A-DIM"),
    ),
    PROracleEntry(
        oracle_id="O-PR13-EMITTED-CONSTANTS",
        claims=("PR13", "PR11"),
        kind="structural-identity",
        subject=(
            "Corollary cor:tolentries (i)-(iv): the four clauses that fix every "
            "constant this module emits at a positive tolerance"
        ),
        derivation="""\
THE BINDING STATEMENT FOR THE EMITTED CONSTANTS, "WHICH AN IMPLEMENTER BINDS
HERE" (Section 2.3). The value pinned is the number of clauses, four, and
cor:tolentries closes by asserting they are EXHAUSTIVE: "TOGETHER, (i)-(iv)
COVER EVERY ENTRY THIS MODULE CAN EMIT".

THE FOUR ON TOL2, each frozen at eps_op = 0 AND at eps_op = 1/100:
  (i)   flag-sector          0        ->  -1/125            = -eta_o
  (ii)  probe expectation    = 2/3    ->  [244/375, 256/375] = q_t0 -+ 2/125
        probe expectation    = 1/3    ->  [122/375, 128/375] = q_t1 -+ 1/125
  (iii) default carried      0        ->   0                 UNCHANGED
  (iv)  eq:two-sector-entry         0        ->  -1/125            = -eta_e
AND A FIFTH OUTCOME THAT IS NOT A CONSTANT: a requested operator OUTSIDE
Eq. eq:tolgeneral's form is REFUSED `constraint_without_certificate` "RATHER
THAN EMITTED AT ANY CONSTANT" (TOL_ENTRY_OUTSIDE_FORM).

THE DIRECTION IS THE SAFE ONE IN EVERY CASE and the integrity test asserts it:
a >= entry's constant never RISES and a <= entry's never FALLS, so the emitted
admissible set never SHRINKS. Section 2.3 states the hazard in the other
direction: "EMITTING A 0.1.3 CONSTANT AT eps_op > 0 IS UNSAFE -- it would
restrict A_CList MORE TIGHTLY than eq:certificate licenses, so a physical
composite attack could fall outside the declared admissible set and THE
INCLUSION thm:licence CERTIFIES WOULD FAIL."

CLAUSE (ii) IS THE ONE WHOSE SHIFT IS ENTIRELY THE RECEIVER'S. Eq.
eq:starprobeexact makes the starred pull-back EXACTLY q_t 1_B, "THERE BEING NO
BLINDED CONTRIBUTION TO THE SHIFT AT ALL, WHICH IS WHAT NARROWING THE TOLERANCE
TO THE RECEIVER BLOCKS BUYS HERE" -- and it stays decidable at eps_op > 0
because Eq. eq:branchprobeweight is exact declared data.""",
        value=4,
        hypotheses=("A-OPTOL", "A-CONST", "A-RECV"),
    ),
    PROracleEntry(
        oracle_id="O-PR13-SCOPE",
        claims=("PR13", "PR9", "PR8"),
        kind="fail-closed",
        subject=(
            "Assumption A-OPTOL's scope and Remark rem:tolboundary: the "
            "tolerance reaches the declared receiver blocks and NO other "
            "family, and the other two are refused at every eps_op"
        ),
        derivation="""\
THE BOUNDARY, FROZEN FROM BOTH SIDES. The value pinned is the number of declared
operator families the contract distinguishes, three: the receiver blocks that
A-OPTOL (a) covers, and the declared blinded-branch POVMs and {N_b} that clause
(b) excludes.

TOL_SCOPE_CASES freezes one case per family. The two excluded families are
refused `blinding_model_ill_formed` on a defect of 1/1000 -- TEN TIMES SMALLER
than the declared eps_op = 1/100 -- at EVERY eps_op, which is the sharpest form
the statement takes.

THE REASONS DIFFER AND ARE KEPT APART. A blinded branch is a POVM on the FULL
FOCK SPACE which def:blindmodel (c) "DELIBERATELY DECLINES to require block
diagonal", so it "HAS NO FINITE MATRIX PRESENTATION ANYWHERE IN THIS CONTRACT".
{N_b} lives on Bl, "A FACTOR OF THE PHYSICAL SYSTEM... WHICH ASSUMPTION A-DIM
SAYS IS SEPARABLE AND MAY BE INFINITE-DIMENSIONAL", and "dim H(Bl) IS NOWHERE
DECLARED OR BOUNDED".

Section 1.1 records that the FIRST draft of 0.2.0 extended A-OPTOL to all three
families and that the extension was WITHDRAWN, "the reason being decisive rather
than editorial": Lemma lem:exactpsd "was claimed for data the contract gives no
way to decide", and declaring a finite representation "IS A WIDENING OF THE
BLINDING MODEL RATHER THAN A TOLERANCE, AND IT IS A QUESTION FOR THE SIGNER".

THE DECLARED SCALARS ARE OUTSIDE IT TOO -- {q_t}, (O_i, p_i), N, cg, R -- and
Remark rem:tolboundary's second consequence is frozen in the slot cases: "a
declaration whose SCALAR data is only approximately valid... IS STILL
REFUSED".""",
        value=3,
        hypotheses=("A-OPTOL", "A-BLIND", "A-DIM"),
    ),
    PROracleEntry(
        oracle_id="O-PR13-BRANCHPROBE",
        claims=("PR9", "PR11", "PR13"),
        kind="fail-closed",
        subject=(
            "Eq. eq:branchprobeweight as the Section 4.13 certificate rule at "
            "EVERY eps_op: the F-5-01 narrowing, and the three refusals under "
            "`constraint_without_certificate`"
        ),
        derivation="""\
THE NARROWING RULED ("Narrow the precis"), made
checkable. The value pinned is the number of ways the certificate can fail under
one reason: an UNDECLARED blinded branch, a branch MISSING AN ELEMENT at a
declared joint outcome, and a branch VIOLATING eq:branchprobeweight -- "ALL
REFUSALS, UNDER THE SAME REASON".

BRANCH_PROBE_WEIGHT_CASES freezes a pass, a violation and an undeclared branch.
THE VIOLATION CASE IS THE DISCRIMINATING ONE: its branch IS AN EXACT POVM, so
`blinding_model_ill_formed` does not fire, and it violates eq:branchprobeweight
at both settings, so the probe entry is refused
`constraint_without_certificate`. The two conditions are independent and the
case proves it: weight is moved BETWEEN the t-blocks by diag(+-1/12, -+1/12),
which the POVM condition cannot see.

THE CONDITION IS EXACT AT EVERY eps_op AND THAT IS WHY THE SHIFT IS SMALL.
Section 4.13: "The identity eq:branchprobeweight is THE EXACT ONE AT EVERY
eps_op, INCLUDING eps_op > 0: a declared blinded branch lies OUTSIDE Assumption
A-OPTOL and is EXACT DECLARED DATA by its clause (b), so the condition is
decidable on the declaration AND IS WEAKENED BY NO TOLERANCE. THAT IS WHAT MAKES
CORollARY cor:tolentries (ii)'s CONSTANT AS SMALL AS IT IS."

AT |Blmode| = 1 THE CONDITION IS VACUOUS, which is why the 0.1.3 PROBE22 cases'
numbers stand while their READING is superseded (see SUPERSESSIONS).""",
        value=3,
        hypotheses=("A-BLIND", "A-OPTOL", "A-PROBE", "A-TSM"),
    ),
    PROracleEntry(
        oracle_id="O-PR13-SLOT-ROW",
        claims=("PR6", "PR12"),
        kind="fail-closed",
        subject=(
            "The high-photon slot row (F-4-08): p_i >= 0 and sum_i p_i <= 1, "
            "and why it is NOT the total-weight row"
        ),
        derivation="""\
THE NEW ROW AND THE REASON IT CANNOT BE FOLDED INTO AN EXISTING ONE. The value
pinned is the number of frozen slot declarations, three: well formed, negative
and masked, and sum exceeding one.

THE MASKING IS THE POINT. At r = 1 with r_min,0 = 1/5 > 0, a declared
p_1 = -1/10 routes to +3/25 through Eq. eq:weightroute, so sum_i p_i = -1/10 and
the routed total p = +3/25 HAVE OPPOSITE SIGNS and no test on the routed weights
can recover the defect. Section 2.1: "a NEGATIVE p_i CAN BE MASKED THERE
WHENEVER r_min,i > 0".

THE DIRECTION IS RECORDED AND IS CHECKABLE: at p_1 = 0 the route gives 1/5 =
5/25 > 3/25, so the p_1 < 0 declaration routes to a STRICTLY WEAKER certified
weight. Section 4.13: "NOT A SECURITY BREAK -- the routed bound at p_i < 0 is
WEAKER than at p_i = 0 -- BUT IT CONTRADICTS THE SUPPLIER'S OWN SLOT GUARANTEE
(Assumption A-RECV) AND IS REFUSED RATHER THAN CONSUMED."

THE THIRD CASE SHOWS THE OTHER SIDE: at r = 2 every r_min,i = 0 by Corollary
cor:oneabsorbing, the routed total EQUALS sum_i p_i = 6/5, and both rows refuse.
"The two agree ONLY WHEN EVERY r_min,i = 0."

THE UPSTREAM AUTHORITY is receiver-povm Def. def:slot with Prop. prop:slotvalid,
imported through Assumption A-RECV. This module VALIDATES what it consumes.""",
        value=3,
        hypotheses=("A-RECV", "A-PROBE"),
    ),
    PROracleEntry(
        oracle_id="O-PR13-INTERFACE-DELTA",
        claims=("PR13", "PR12"),
        kind="fail-closed",
        subject=(
            "The 0.1.3 -> 0.2.0 interface delta: 17 input keys, 18 output keys, "
            "26 refusal reasons over 24 rows, 13 conventions, 10 assumptions, "
            "13 claims"
        ),
        derivation="""\
THE VOCABULARY DELTA, FROZEN AS COUNTS AND AS TUPLES. The value pinned is the
refusal-reason count, twenty-six.

    input keys        16 -> 17   (+ operator_tolerance, request group)
    output keys       17 -> 18   (+ operator_tolerance_record)
    refusal reasons   24 -> 26   (+ declaration_outside_tolerance,
                                   + high_photon_slot_ill_formed)
    fail-closed rows  21 -> 24   (THREE rows for TWO strings: the
                                   licensed-route Hermiticity row carries the
                                   existing constraint_without_certificate)
    conventions       12 -> 13   (+ exact_arithmetic)
    assumptions        9 -> 10   (+ A-OPTOL); never-verified 2 -> 3
    claims            12 -> 13   (+ PR13), all newly-derived
    spec version      proof-reductions@0.1.3 -> @0.2.0

NOTHING IS REMOVED. Section 1.1: "None removed, AND NONE INVENTED WHERE AN
EXISTING ONE CARRIES THE REFUSAL: the missing-validation-record refusal is
decided by the receiver-spec row under `receiver_spec_not_accepted`, and BOTH the
probe-expectation certificate AND the licensed-route Hermiticity condition are
decided under `constraint_without_certificate`." NO TWENTY-SEVENTH STRING IS
INVENTED ANYWHERE, and Section 4.13's closing paragraph says of the one place a
reader might reach for one: "No separate reason string exists for it, AND NONE IS
TO BE INVENTED."

THE ROW COUNT AND THE STRING COUNT DO NOT DETERMINE EACH OTHER and are frozen
separately, in REFUSAL_REASONS_0_2_0 and FAIL_CLOSED_ROW_COUNT_0_2_0.

THE 0.1.3 TUPLES ARE NOT EDITED: each is marked in SUPERSESSIONS with its
replacement, so that run B retires them deliberately.""",
        value=26,
        hypotheses=("A-OPTOL",),
    ),
    PROracleEntry(
        oracle_id="O-PR13-EXACT-ARITHMETIC",
        claims=("PR13",),
        kind="structural-identity",
        subject=(
            "Section 2.5 `exact_arithmetic`: the rows decided by lem:exactpsd, "
            "the two neighbouring rows that are exact without being instances "
            "of it, and the cases a float comparison gets wrong"
        ),
        derivation="""\
THE QUANTIFIER, WHICH IS WHAT F-8-01 WAS ABOUT. The value pinned is the number
of rows the convention names as decided BY Lemma lem:exactpsd: ONE, the
tolerance row.

  DECIDED BY lem:exactpsd (1): the tolerance row, whose subject is a declared
    receiver block or a finite linear combination of such blocks formed with the
    declared scalars.
  EXACT WITHOUT BEING INSTANCES (2): the block-structure row, "a TYPE check",
    and the total-weight row, "a SIGN COMPARISON ON DECLARED SCALARS". "BOTH ARE
    DECIDED EXACTLY IN THE SUBSTRATE OF DEFINITION def:tolerance, AND NEITHER
    INVOKES LEMMA lem:exactpsd."
  UNCHANGED FROM 0.1.3 (the rest): "the conditions on the declared
    blinded-branch POVMs, on {N_b}, and on the declared scalars and classical
    maps ARE THE EXACT CONDITIONS 0.1.3 STATED, DECIDED AS 0.1.3 DECIDED THEM."

"NO ROW OF THIS MODULE IS DECIDED BY A FLOATING-POINT COMPARISON, with or
without a declared tolerance." TOL_FLOAT_SENSITIVE_CASES freezes TWO instances
where that sentence has teeth -- a boundary admit whose exact test yields W = 0,
and a cancellation whose exact e_1 is -1/50 while both leading minors are
exactly 0. In both, a float evaluation can return the other answer.

THE WHOLE FIXTURE IS NON-DYADIC: eps_op = 1/100, dcf = 6/5, q = (2/3, 1/3),
eta = 1/125 and 1/250, routed weights 14/75 and 7/75. None is exactly
representable in binary, so the float hazard is present before any comparison is
made rather than manufactured for the two cases.

THIS CONVENTION DOES NOT TOUCH `bound_evaluation`. Section 1.4's third fact:
every such rule is decided exactly "EVEN THOUGH THE NUMBERS THEY ARE MADE ON
WERE PRODUCED IN FLOATING POINT UPSTREAM", and a declared tolerance "DOES NOT
TOUCH `bound_evaluation`, WHICH CONTINUES TO BE INHERITED AND NEVER
UPGRADED".""",
        value=1,
        hypotheses=("A-OPTOL", "A-DIM"),
    ),
    PROracleEntry(
        oracle_id="O-PR13-SUPERSESSION",
        claims=("PR13", "PR11", "PR12"),
        kind="fail-closed",
        subject=(
            "The 0.1.3 frozen cases the amendment invalidates, marked and not "
            "deleted, each with its contract site and its replacement"
        ),
        derivation="""\
THE FREEZE DISCIPLINE APPLIED TO A SECOND BAND. Run A does not delete or edit a
frozen 0.1.3 value; it MARKS what the amendment invalidates. The value pinned is
the number of marked symbols.

FOUR KINDS OF MARK, and they are not the same thing:
  CONSTANT (4): LICENCE_TRUSTED, LICENCE_UNTRUSTED, LICENCE_PROBE_IDENTITY,
    CERT_TWO_SECTOR -- each value REMAINS the constant at eps_op = 0 and is superseded
    only above it, "EACH SHIFTED CONSTANT IS THE 0.1.3 CONSTANT" there.
  READING (1, plus one shared): CERT_IDENTITY_PROBE, and the second half of
    LICENCE_PROBE_IDENTITY -- the F-5-01 pre-narrowing quotation of the
    availability sentence. The numbers stand; the sentence does not.
  INPUT SHAPE (1): R-block-structure, whose declared datum -- an inter-block
    coherence in the nb branch -- has no slot in the per-m list the row now
    type-checks.
  VOCABULARY (5): INPUT_KEYS, OUTPUT_KEYS, REFUSAL_REASONS, CONVENTIONS,
    ASSUMPTION_LEDGER.
  SCOPE (1): ENCODED_CONSTRAINT, the one residual with no artifact field to sit
    in (Remark rem:tolscope's encoded-route bullet).

NOT_SUPERSEDED_AND_WHY records what is deliberately left unmarked and the reason
for each, because a supersession list is only as informative as its complement.
PROBE22_V IS THE CASE WORTH READING: the human ruled "y-fastest, AS FROZEN", so
the VALUE was already right and only the 0.1.3 comment wording is superseded.

THE INTEGRITY INVARIANT: a marked case must not remain asserted UNMARKED by a
golden test. AT THE FREEZE THAT FAILS BY CONSTRUCTION -- the code has not
changed and the golden suite still asserts the 0.1.3 constants -- AND THE
FAILURE IS THE SIGNAL, not a defect in the freeze. Run B clears it by retiring
or rewriting each marked case deliberately.""",
        value=12,
        hypotheses=("A-OPTOL",),
    ),
)


# ===========================================================================
#  Change-request candidates
# ===========================================================================
#
#  Run A was asked to read the contract and, for each item it could not resolve
#  from Section 2 alone, either REPORT THE READING THE TEXT FIXES with its
#  locator or ROUTE THE ITEM as a change request. Eight were named on entry and
#  two more were found while deriving. NOTHING BELOW IS DECIDED HERE: the
#  resolved items record a reading the contract states, and the routed ones are
#  reported to the driver.

CHANGE_REQUEST_CANDIDATES: tuple[tuple[str, str, str], ...] = (
    (
        "(a) carried_operators default vs. the unpadded target",
        "ROUTED -- patch level, non-blocking",
        """\
Section 2.1's `carried_operators` row says the default is "the two cutoff
projectors Pi_<=N, Pi_flag PER BRANCH". Under the UNPADDED target of
Eq. eq:blindtarget a blinded branch "contributes its flag block AND NO PRESERVED
BLOCK" (Remark rem:paddednotemitted), so there is no Pi_{bl_i,<=N} to carry and
the phrase yields 2 + (|Blmode| - 1) operators, not 2|Blmode|. The two agree
exactly at |Blmode| = 1.
THE OPERATIVE READING IS UNAMBIGUOUS AND IS WHAT THIS REGISTRY FREEZES:
Eq. eq:blindtransport enumerates exactly what the composed relation transports
-- Pi_{nb,<=N}, Pi_{nb,flag} and Pi_b per blinded branch -- and it is the only
set that EXISTS on the emitted target. So implementation is not blocked.
WHAT IS ROUTED is the SECTION 2.1 PHRASING, which reads as a propagation site
the F-3-01 repair (unpadded default) did not reach. The decision needed is
whether to restate the default as eq:blindtransport's set. Binding ID:
Section 2.1 `carried_operators`; claim PR9.""",
    ),
    (
        "(b) the receiver's per-setting p_mc values and their minimum over T",
        "RESOLVED from the text",
        """\
READING: THE MINIMUM IS THE SUPPLIER'S, TAKEN INSIDE ITS OWN CLAIM. Assumption
A-RECV names receiver-povm 0.1.3 Thm. thm:emitted-bound, "whose Eq. eq:pmcstatement
states blk M^{>N}_{mc|t} >= p_mc 1 FOR EVERY t in T with THE SINGLE t-UNIFORM
p_mc = min_t p^{(t)}_mc", and Def. def:slot, "whose slot guarantee is likewise a
single t-uniform p_i per entry". This module consumes the emitted slot value and
takes NO minimum of its own. Remark rem:minweight states the cost -- a rate loss
and never a soundness loss -- and the repair path: a future upstream amendment
stating the per-setting form would let a PATCH-LEVEL change here consume it.""",
    ),
    (
        "(c) the alphabet-name collision V (receiver-povm) vs Y and V here",
        "RESOLVED from the text",
        """\
READING: receiver-povm's emitted alphabet IS this module's Y. Section 3(a),
bullet "F_v and M_{y|t} across the module boundary": that contract "writes F_v
for the coarse-grained PHYSICAL POVM it emits (its Thm. thm:coarse-graining,
Eq. eq:coarse). This contract writes M_{y|t} FOR THAT SAME OBJECT... and
RESERVES F_v FOR THE SQUASHED TARGET." Section 2.1 types cg as 2^[K] -> Y and
declares V := Y x T. So the letter V denotes DIFFERENT SETS in the two
documents, and an implementation must not identify them. Recorded in
interface.yaml under `detection_alphabet.cross_module_letter_note`.""",
    ),
    (
        "(d) how the nb-branch POVM relates to the post-processed receiver POVM",
        "RESOLVED as a reading; the residual is recorded, not decided",
        """\
READING: THE nb BRANCH IS DERIVED FROM THE RECEIVER ARTIFACT, NOT INDEPENDENTLY
DECLARED. Definition def:blindmodel (c) says the unblinded branch "is block
diagonal at the cutoff -- WHICH IS WHAT THE RECEIVER ARTIFACT SUPPLIES
(Assumption A-RECV)", Section 2.2 fixes step by step how that artifact becomes
M_(y,t), and Proposition prop:route derives def:blindmodel (d)'s certified
weights FROM THAT POST-PROCESSED FAMILY.
THE RESIDUAL, recorded in interface.yaml as open implementation choice 7 of 10
and NOT decided here: Section 2.1 types `blinding_model` as the triple
(Blmode, {N_b}, {M_{v|b}}), so an nb entry is EXPRESSIBLE; and Section 4.13
states no equality rule and NAMES NO REFUSAL REASON for a disagreement between a
separately declared nb branch and the derived family. An implementation that
derives it needs no new rule; one that reads it as authoritative would need both
a rule and a reason string that do not exist. INVENTING A TWENTY-FIFTH REASON
WOULD DECIDE IT, so none is invented.""",
    ),
    (
        "(e) the wire form of source_descriptor for an infinite-dimensional Fock space",
        "RESOLVED as content; the SERIALIZATION is recorded as open",
        """\
READING: the contract fixes the CONTENT -- "the channel Fock space WITH ITS
DECLARED PHOTON-NUMBER GRADING, and the blinding register with its POVM {N_b}"
(Section 2.3) -- and states NO wire form. Assumption A-DIM explicitly permits
H(B) to be infinite-dimensional while every TARGET space and side register is
finite-dimensional with dimensions declared, so the source descriptor is the one
place a finite dimension is NOT available. Recorded in interface.yaml as open
implementation choice 3 of 10, together with the observation that the existing
`ReductionSystemDescriptor.dim` of the earlier domain manifest module is typed
`int >= 1` and CANNOT express it. THIS MODULE OWNS ITS OWN ARTIFACT
(`ProofReductionArtifact`), so nothing here requires that wire form to change.""",
    ),
    (
        "(f) what exact_identity and verification_report can assert at run time",
        "RESOLVED from the text",
        """\
READING: `exact_identity` asserts THE THEOREM, which holds BY CONSTRUCTION --
Theorem thm:blinding (i) proves Lambda+(F_v) = M_v "exactly, with no error term"
for the channel built from the declared branch data, and Definition def:link's
`status` = exact means the identity holds WITH NO ERROR TERM. It is NOT a
numerical residual check on materialised matrices, and could not be: Section
2.3's own `squashing_channel` row says the supplier emits no above-cutoff block,
so neither map can be materialised. `verification_report` carries "every
validation rule of Section 4.13 WITH ITS OUTCOME, and the dependency identity of
the receiver artifact", and Section 4.13's preamble says every such rule "is
DECIDED FROM DECLARED DATA BEFORE ANYTHING IS EMITTED" -- twenty-one decidable
checks over declared data. Section 2.3's closing paragraph forbids recomputing
any receiver quantity. The ENCODING of a rule's outcome is recorded in
interface.yaml as open implementation choice 9 of 10.""",
    ),
    (
        "(g) the weights on the licensed route, and how c_k is fixed from them",
        "RESOLVED from the text",
        """\
READING: THE SAME p_v, AND c_k = 0. Theorem thm:blinding (vi) says the licensed
variant holds "verbatim with Lambda_nb replaced by Lambda^FSS and F^WP by F^FSS
-- in which THE CERTIFIED WEIGHTS ARE NOT ENCODED IN THE TARGET AND TRAVEL
INSTEAD AS THE CONSTRAINT ENTRY of Corollary cor:fssinstance". That corollary
fixes the entry: O^ = F^FSS_o - p_o Pi_flag, relation >=, c = 0. SO THE WEIGHT
p_o ENTERS THE OPERATOR AND NOT THE CONSTANT, and c_k is 0 rather than a
function of p_o. Section 4.13 confirms the weights are still declared and
validated on both routes: the p < 1 test is applied "on both routes
deliberately". Frozen in Group PR-K.
ONE RESIDUAL is recorded and not decided (interface.yaml, open implementation
choice 5 of 10): Section 2.3 states no PRESENCE RULE for the `wpfss_data` key on
the licensed route, unlike `attack_set_license`, which carries one.""",
    ),
    (
        "(h) the spelling of the null source_mode and of the route default",
        "SPLIT: the route default is RESOLVED; the null spelling is OPEN",
        """\
THE ROUTE DEFAULT IS FIXED VERBATIM: Section 2.1's `route` row reads "`encoded`
(DEFAULT; the weights go into {F_v} and CList = empty)", and the two values are
`encoded` and `licensed` with `both` refused. Frozen in ROUTES.
THE NULL SOURCE-MODE SPELLING IS NOT FIXED: Section 2.1 types the key as
"tau_A or nomarg" with type "state or null" and renders the null symbol as the
upright word `none`. A YAML null, the literal string `none` and a `nomarg` enum
member all satisfy the row. Recorded in interface.yaml as open implementation
choice 2 of 10; SOURCE_MODES freezes only the two MODE names, `trusted` and
`untrusted`, which Definition def:licensed does fix.""",
    ),
    (
        "(i) the povm_index_convention bullet's step number",
        "RESOLVED -- an internal cross-reference, no mathematics at stake",
        """\
FOUND WHILE TRANSCRIBING. Section 2.5's `povm_index_convention` bullet says "the
weights q_t are applied at STEP 3 of Section 2.2", while Section 2.2 itself
numbers the weighting as STEP 2 ("Joint alphabet. Set M_(y,t) := q_t M~_{y|t}")
and step 3 as "Squash. Apply Section 4.9". BOTH READINGS PUT THE q_t WEIGHTING
BEFORE THE FIRST SQUASHING LINK, which is the entire content of
`post_processing_order` and of Remark rem:intertwining, so nothing mathematical
turns on it. The OPERATIVE order is Section 2.2's three enumerated steps.
Recorded in interface.yaml under `conventions.povm_index_convention_step_note`
with NO STEP RENUMBERED.""",
    ),
    (
        "(j) exact_identity's internal locator",
        "RESOLVED -- a pointer, no mathematics at stake",
        """\
FOUND WHILE TRANSCRIBING. Section 2.3's `exact_identity` row cites
"Thm. thm:blinding (ii)" for the identity Lambda+(F_v) = M_v, while it is
thm:blinding (i) that states that identity; part (ii) states the transported
projectors of Eq. eq:blindtransport. The row's CONTENT is unambiguous -- it
displays the identity itself -- and both parts are proved. Recorded here rather
than silently corrected; nothing in this registry or in interface.yaml depends
on which part number is written, and both are cited in the trace.""",
    ),
)


# ===========================================================================
#  Group PR-O -- the declared operator tolerance (PR13), NEW AT 0.2.0
# ===========================================================================
#
#  THE 0.1.3-TO-0.2.0 DELTA, AND NOTHING ELSE. Everything above this banner was
#  frozen by run A of the 0.1.3 band against ``contract.tex``
#  0.1.3 and is UNTOUCHED except for the supersession marks described under
#  ``SUPERSESSIONS`` at the end of this module. Every value below was derived BY
#  HAND from the ACCEPTED ``contract.tex`` 0.2.0 (sha256
#  b4df5d8c07fd425288db279472d7f9caea1d0e31b1faeee9fb5d3dba2cf183e4) before any
#  code changed. Run B changes the code against these values and may read but not
#  modify them.
#
#  THE REPRESENTATION IS UNCHANGED: exact Gaussian rationals, no float
#  anywhere. It is now also the CONTRACT'S OWN requirement on the rows these
#  cases pin, and not merely this file's choice about evidence: Section 2.5's
#  ``exact_arithmetic`` convention makes the tolerance row "decided IN THE EXACT
#  SUBSTRATE OF DEFINITION def:tolerance BY THE PREDICATE OF LEMMA lem:exactpsd:
#  finitely many field operations and sign comparisons on matrices of declared
#  finite dimension, NO ROUNDING, NO THRESHOLD", and adds that "NO ROW OF THIS
#  MODULE IS DECIDED BY A FLOATING-POINT COMPARISON, with or without a declared
#  tolerance". ``TOL_FLOAT_SENSITIVE_CASES`` freezes two instances whose exact
#  answer a float comparison can get wrong.
#
#  WHICH ORDERED FIELD IS NOT DECIDED HERE. Remark ``def:substrate`` leaves it
#  open and gives the reason it cannot matter -- "every rule below is A SIGN
#  COMPARISON IN F OF A POLYNOMIAL WITH INTEGER COEFFICIENTS in the declared
#  entries and in eps_op, so ANY TWO ADMISSIBLE FIELDS CONTAINING THOSE ENTRIES
#  RETURN THE SAME ANSWER". interface.yaml records it as open implementation
#  choice 10 of 12, the PSD ALGORITHM as 11, and the tolerance record's
#  SERIALIZATION as 12. NONE OF THE THREE IS DECIDED HERE.
#
#  THE WORKED INSTANCE IS ``TOL2`` AND EVERY NUMBER IN IT IS NON-DYADIC.
#  eps_op = 1/100, dcf = 6/5, q = (2/3, 1/3), eta = 1/125 and 1/250,
#  delta_t = 2/125 and 1/125, routed weights 14/75 and 7/75: not one of these is
#  a dyadic rational, so a binary floating-point representation of the fixture
#  is already inexact before any comparison is made.


# ---------------------------------------------------------------------------
#  TOL2 -- the worked tolerance instance
# ---------------------------------------------------------------------------
#
#  THE SETTING, in the vocabulary of contract Sections 2.1, 2.2 and 4.13.
#    Y = (y0, y1),  |Y| = 2
#    T = (t0, t1),  q_t0 = 2/3, q_t1 = 1/3          (A-PROBE; non-dyadic)
#    V = Y x T ordered y FASTEST, t SLOWEST          (Section 2.5, CR-B1)
#    N = 0 with dim H(C_0) = 2                       -- so every declared
#      receiver block is a 2 x 2 matrix and Lemma lem:exactpsd's principal-minor
#      sums are a genuine two-term computation rather than a sign test on a
#      scalar. THAT IS THE POINT OF dim = 2: at dim = 1 the predicate
#      eq:psdtest degenerates to "the entry is >= 0" and an implementation that
#      tested only the leading principal minors, or only the trace, would pass.
#    R^cg = [[1, 1/5], [0, 4/5]]                     (rows y, columns y')
#    slot: one entry, O_1 = cg^{-1}(y0), p_1 = 1/10
#    eps_op = 1/100
#
#  R^cg IS COLUMN STOCHASTIC (column y0: 1 + 0 = 1; column y1: 1/5 + 4/5 = 1),
#  ABSORBING at the bounded letter y0 (R^cg_{y0|y0} = 1, Eq. eq:absorbing), and
#  its per-letter constant is r_min,0 = min_{y' != y0} R^cg_{y0|y'} = 1/5.
#  ROW SUMS are 1 + 1/5 = 6/5 and 0 + 4/5 = 4/5, so Eq. eq:dcf gives
#      dcf = max_y sum_y' R^cg_{y|y'} = 6/5 ,
#  and 1 <= 6/5 <= 2 = |Y| as Lemma lem:tolprop requires.

#: Section 2.1. The declared detection alphabet and probe alphabet of TOL2.
TOL2_Y: tuple[str, ...] = ("y0", "y1")
TOL2_T: tuple[str, ...] = ("t0", "t1")

#: The declared probe weights, non-dyadic (A-PROBE).
TOL2_Q: tuple[tuple[str, F], ...] = (("t0", F(2, 3)), ("t1", F(1, 3)))

#: THE DECLARED ORDER OF V = Y x T AT 0.2.0: y VARIES FASTEST AND t SLOWEST.
#: Section 2.5 `subsystem_order`, rewritten by the amendment ("y-fastest, as frozen"): "writing Y = {y_1, ..., y_|Y|} and
#: T = {t_1, ..., t_|T|} in their declared orders, the flag basis is
#: |(y_1,t_1)>, ..., |(y_|Y|,t_1)>, |(y_1,t_2)>, ... EQUIVALENTLY, V IS
#: ENUMERATED AS T-BLOCKS OF Y-RUNS."
TOL2_V: tuple[tuple[str, str], ...] = (
    ("y0", "t0"),
    ("y1", "t0"),
    ("y0", "t1"),
    ("y1", "t1"),
)

#: THE FOIL. The t-fastest enumeration, which "with Y major" also admitted and
#: which 0.2.0's replacement of that phrase excludes. It differs from TOL2_V at
#: positions 2 and 3, so any consuming site that indexes V is observably wrong
#: under it. NOT A CONTRACT OBJECT: frozen only so the discriminator exists.
TOL2_V_T_FASTEST_NOT_THE_CONTRACT_ORDER: tuple[tuple[str, str], ...] = (
    ("y0", "t0"),
    ("y0", "t1"),
    ("y1", "t0"),
    ("y1", "t1"),
)

#: The descended dark-count matrix R^cg, rows indexed by y and columns by y'.
#: Column stochastic; absorbing at y0.
TOL2_RCG: Matrix = real_matrix(((1, F(1, 5)), (0, F(4, 5))))

#: Eq. eq:dcf. dcf = max_y sum_y' R^cg_{y|y'} = max(6/5, 4/5) = 6/5.
TOL2_DCF: F = F(6, 5)

#: Section 2.1, `operator_tolerance`. NON-DYADIC: 1/100 is not exactly
#: representable in binary floating point, so the fixture is inexact under a
#: float substrate before any comparison is made.
TOL2_EPS_OP: F = F(1, 100)

#: Eq. eq:etadef. eta_v = q_t dcf eps_op, in the declared order of V.
#:   t0: (2/3)(6/5)(1/100) = 12/1500 = 1/125
#:   t1: (1/3)(6/5)(1/100) =  6/1500 = 1/250
TOL2_ETA_V: tuple[tuple[tuple[str, str], F], ...] = (
    (("y0", "t0"), F(1, 125)),
    (("y1", "t0"), F(1, 125)),
    (("y0", "t1"), F(1, 250)),
    (("y1", "t1"), F(1, 250)),
)

#: Eq. eq:etadef. eta = dcf eps_op = (6/5)(1/100) = 3/250 >= max_v eta_v, the
#: maximum being 1/125 = 2/250.
TOL2_ETA: F = F(3, 250)

#: Corollary cor:tolentries (ii). delta_t = |Y| q_t dcf eps_op = |Y| eta_(y,t).
#:   t0: 2 * 1/125 = 2/125       t1: 2 * 1/250 = 1/125
TOL2_DELTA_T: tuple[tuple[str, F], ...] = (("t0", F(2, 125)), ("t1", F(1, 125)))

#: Section 2.1, `high_photon_bounds`: the declared slot, ONE entry whose bounded
#: set is exactly the fibre cg^{-1}(y0). Validated p_1 >= 0 and sum_i p_i <= 1
#: by the slot row (`high_photon_slot_ill_formed`, new at 0.2.0).
TOL2_SLOT: tuple[tuple[str, F], ...] = (("y0", F(1, 10)),)

#: Eq. eq:weightroute, in the declared order of V:
#:   p_(y0,t) = q_t ( (1 - 1/5)(1/10) + 1/5 ) = q_t (4/50 + 10/50) = q_t (14/50)
#:     t0: (2/3)(14/50) = 28/150 = 14/75        t1: (1/3)(14/50) = 7/75
#:   p_(y1,t) = 0, y1 not being a bounded letter.
#: Total p = 14/75 + 7/75 = 21/75 = 7/25 < 1, so the total-weight row passes.
TOL2_ROUTED_WEIGHTS: tuple[tuple[tuple[str, str], F], ...] = (
    (("y0", "t0"), F(14, 75)),
    (("y1", "t0"), F(0)),
    (("y0", "t1"), F(7, 75)),
    (("y1", "t1"), F(0)),
)
TOL2_TOTAL_WEIGHT: F = F(7, 25)


# ---------------------------------------------------------------------------
#  The declared receiver blocks of TOL2, and the exact rows they pass
# ---------------------------------------------------------------------------
#
#  N = 0, so there is exactly one block index m = 0, and the declared family is
#  four 2 x 2 matrices -- one per (y, t). They are DELIBERATELY NOT A POVM: at
#  eps_op = 0 this declaration is REFUSED, and at eps_op = 1/100 it is ADMITTED.
#  That is the whole content of the amendment on this row and it is frozen as a
#  pair, not as a single admit.

#: blk M^{=0}_{y0|t0}. NON-HERMITIAN (the (0,1) and (1,0) entries differ) and
#: with a NEGATIVE (1,1) entry. Both defects are inside the declared tolerance
#: and both would refuse at eps_op = 0.
TOL2_BLOCK_Y0_T0: Matrix = real_matrix(
    ((F(3, 4), F(1, 200)), (F(-1, 200), F(-1, 200))),
)

#: blk M^{=0}_{y1|t0}. Hermitian and positive; its (1,1) entry is 1.
TOL2_BLOCK_Y1_T0: Matrix = real_matrix(((F(1, 4), 0), (0, 1)))

#: blk M^{=0}_{y0|t1} and blk M^{=0}_{y1|t1}: EXACTLY a POVM at t1, so the same
#: declaration carries one setting that needs the tolerance and one that does
#: not. Eigenvalues 1/2 +- 1/10 = 3/5 and 2/5, both positive.
TOL2_BLOCK_Y0_T1: Matrix = real_matrix(((F(1, 2), F(1, 10)), (F(1, 10), F(1, 2))))
TOL2_BLOCK_Y1_T1: Matrix = real_matrix(((F(1, 2), F(-1, 10)), (F(-1, 10), F(1, 2))))

#: The declared family, keyed by (y, t) in the declared order of V.
TOL2_BLOCKS: tuple[tuple[tuple[str, str], Matrix], ...] = (
    (("y0", "t0"), TOL2_BLOCK_Y0_T0),
    (("y1", "t0"), TOL2_BLOCK_Y1_T0),
    (("y0", "t1"), TOL2_BLOCK_Y0_T1),
    (("y1", "t1"), TOL2_BLOCK_Y1_T1),
)

#: Section 2.2 step 1 applied to the declared blocks:
#: M~_{y|t} = sum_y' R^cg_{y|y'} M_{y'|t}. Frozen so that Lemma lem:tolprop's
#: propagation is checkable on materialised matrices rather than only in the
#: bound.
#:   M~_{y0|t0} = 1*A(y0,t0) + (1/5)*A(y1,t0)
#:              = [[3/4 + 1/20, 1/200], [-1/200, -1/200 + 1/5]]
#:              = [[4/5, 1/200], [-1/200, 39/200]]
#:   M~_{y1|t0} = (4/5)*A(y1,t0) = [[1/5, 0], [0, 4/5]]
#:   M~_{y0|t1} = A(y0,t1) + (1/5)A(y1,t1)
#:              = [[3/5, 1/10 - 1/50], [1/10 - 1/50, 3/5]] = [[3/5, 2/25], ...]
#:   M~_{y1|t1} = (4/5)A(y1,t1) = [[2/5, -2/25], [-2/25, 2/5]]
TOL2_TILDE: tuple[tuple[tuple[str, str], Matrix], ...] = (
    (
        ("y0", "t0"),
        real_matrix(((F(4, 5), F(1, 200)), (F(-1, 200), F(39, 200)))),
    ),
    (("y1", "t0"), real_matrix(((F(1, 5), 0), (0, F(4, 5))))),
    (("y0", "t1"), real_matrix(((F(3, 5), F(2, 25)), (F(2, 25), F(3, 5))))),
    (("y1", "t1"), real_matrix(((F(2, 5), F(-2, 25)), (F(-2, 25), F(2, 5))))),
)

#: Section 2.2 step 2: M_(y,t)|nb = q_t M~_{y|t}. THE FAMILY Proposition
#: prop:tolrows (iv) is read on.
#:   (2/3)[[4/5, 1/200], [-1/200, 39/200]] = [[8/15, 1/300], [-1/300, 13/100]]
#:   (2/3)[[1/5, 0], [0, 4/5]]             = [[2/15, 0], [0, 8/15]]
#:   (1/3)[[3/5, 2/25], [2/25, 3/5]]       = [[1/5, 2/75], [2/75, 1/5]]
#:   (1/3)[[2/5, -2/25], [-2/25, 2/5]]     = [[2/15, -2/75], [-2/75, 2/15]]
TOL2_JOINT_NB: tuple[tuple[tuple[str, str], Matrix], ...] = (
    (
        ("y0", "t0"),
        real_matrix(((F(8, 15), F(1, 300)), (F(-1, 300), F(13, 100)))),
    ),
    (("y1", "t0"), real_matrix(((F(2, 15), 0), (0, F(8, 15))))),
    (("y0", "t1"), real_matrix(((F(1, 5), F(2, 75)), (F(2, 75), F(1, 5))))),
    (("y1", "t1"), real_matrix(((F(2, 15), F(-2, 75)), (F(-2, 75), F(2, 15))))),
)


@dataclass(frozen=True)
class ToleranceRowCase:
    """One decision of the Section 4.13 tolerance row, taken exactly.

    Every field is a DECLARED datum or an exact consequence of one. ``admitted``
    is the decision Lemma ``lem:exactpsd`` returns, and ``e_k`` is the sequence
    of principal-minor sums the predicate compares against zero -- frozen so
    that the decision can be re-read on paper without running anything.
    """

    case_id: str
    claims: tuple[str, ...]
    #: Which part of Proposition prop:tolrows this instance exercises.
    row: str
    #: The declared tolerance the decision is taken at.
    eps_op: F
    #: The Hermitian matrix X of Eq. eq:psdtest that the predicate is applied to.
    tested_matrix: Matrix
    #: e_k(X) for k = 1..d, the sums of the k x k PRINCIPAL minors (Eq.
    #: eq:charpoly). X >= 0 iff every one of them is >= 0 (Eq. eq:psdtest).
    principal_minor_sums: tuple[F, ...]
    admitted: bool
    #: The refusal reason when ``admitted`` is False; empty otherwise.
    reason: str
    #: Contract labels this case is pinned to.
    labels: tuple[str, ...]
    derivation: str


#: THE FOUR DECLARED BLOCKS OF TOL2, ADMITTED AT eps_op = 1/100.
#: Each row of Proposition prop:tolrows is a separate case; the negative-part
#: row on blk M^{=0}_{y0|t0} is the one that needs the tolerance.
TOL_ROW_CASES: tuple[ToleranceRowCase, ...] = (
    ToleranceRowCase(
        case_id="TOL2-herm-y0t0-admit",
        claims=("PR13",),
        row="prop:tolrows (i) -- Hermiticity defect",
        eps_op=F(1, 100),
        tested_matrix=diag_matrix((F(3, 10000), F(3, 10000))),
        principal_minor_sums=(F(3, 5000), F(9, 100000000)),
        admitted=True,
        reason="",
        labels=("prop:tolrows", "eq:herm", "lem:exactpsd", "eq:normtest"),
        derivation="""\
PROPOSITION prop:tolrows (i), Eq. eq:herm, ON A = blk M^{=0}_{y0|t0}, DECIDED BY
LEMMA lem:exactpsd (ii). A is real, so A-dagger = A^T and
    Z := A - A-dagger = [[0, 1/200 - (-1/200)], [-1/200 - 1/200, 0]]
                      = [[0, 1/100], [-1/100, 0]] .
Z-dagger Z = Z^T Z = [[0, -1/100], [1/100, 0]] [[0, 1/100], [-1/100, 0]]
           = (1/10000) 1_2 , a scalar because Z is a real skew matrix with a
single off-diagonal magnitude. So ||Z|| = 1/100 exactly.

THE TEST, Eq. eq:normtest, at delta = 2 eps_op = 1/50:
    W := delta^2 1_2 - Z-dagger Z = (1/2500 - 1/10000) 1_2 = (3/10000) 1_2 ,
whose principal-minor sums are e_1 = 6/10000 = 3/5000 and
e_2 = det = 9/100000000. BOTH ARE >= 0, so W >= 0 by Eq. eq:psdtest, so
||Z|| <= 2 eps_op, and the row ADMITS. Slack: 1/100 against 1/50, a factor two.

AT eps_op = 0 THE SAME MATRIX REFUSES: delta = 0 gives W = -(1/10000) 1_2 with
e_1 = -1/5000 < 0. That is the pair the amendment turns on and it is frozen as
TOL2-herm-y0t0-refuse-at-zero.""",
    ),
    ToleranceRowCase(
        case_id="TOL2-herm-y0t0-refuse-at-zero",
        claims=("PR13",),
        row="prop:tolrows (i) -- Hermiticity defect, at eps_op = 0",
        eps_op=F(0),
        tested_matrix=diag_matrix((F(-1, 10000), F(-1, 10000))),
        principal_minor_sums=(F(-1, 5000), F(1, 100000000)),
        admitted=False,
        reason="declaration_outside_tolerance",
        labels=("prop:tolrows", "eq:herm", "lem:exactpsd", "eq:normtest"),
        derivation="""\
THE SAME BLOCK AT eps_op = 0, WHICH IS WHAT `operator_tolerance` ABSENT MEANS
(Section 2.1: "ABSENT IS eps_op = 0, AND AT eps_op = 0 EVERY RULE OF SECTION
4.13 IS THE EXACT TEST VERSION 0.1.3 APPLIED"). delta = 0, so
    W = 0 * 1_2 - (1/10000) 1_2 = -(1/10000) 1_2 ,
    e_1 = -1/5000 < 0  ==>  NOT >= 0  ==>  ||Z|| > 0  ==>  REFUSE.
NOTE THAT e_2 = det = 1/100000000 IS POSITIVE. A test that looked at the
determinant alone -- or at the leading principal minors alone, both of which are
here 1/10000 * (-1) < 0 for k = 1 but positive for k = 2 -- would not decide the
predicate; Eq. eq:psdtest requires EVERY e_k >= 0 and e_1 is the one that
fails.

WHAT THIS PAIR SHOWS. The declaration is IDENTICAL; only the declared tolerance
differs. "A declared tolerance CHANGES WHICH DECLARATIONS ARE ACCEPTED; it
changes NOTHING about how the acceptance is decided" (Section 1.4).""",
    ),
    ToleranceRowCase(
        case_id="TOL2-negpart-y0t0-admit",
        claims=("PR13",),
        row="prop:tolrows (ii) -- negative part of the spectrum",
        eps_op=F(1, 100),
        tested_matrix=diag_matrix((F(19, 25), F(1, 200))),
        principal_minor_sums=(F(153, 200), F(19, 5000)),
        admitted=True,
        reason="",
        labels=("prop:tolrows", "eq:negpart", "lem:exactpsd", "eq:psdtest"),
        derivation="""\
PROPOSITION prop:tolrows (ii), Eq. eq:negpart, ON A = blk M^{=0}_{y0|t0}. The
Hermitian part is
    A_h = (1/2)(A + A-dagger) = [[3/4, 0], [0, -1/200]] ,
the off-diagonal entries +-1/200 cancelling. THE (1,1) ENTRY IS NEGATIVE, so
A_h is NOT positive semidefinite: e_2 = det = (3/4)(-1/200) = -3/800 < 0. THAT
IS THE POINT OF THE FIXTURE -- at eps_op = 0 this block is refused.

THE TEST, Eq. eq:negpart, at eps_op = 1/100:
    X := A_h + eps_op 1_2 = [[3/4 + 1/100, 0], [0, -1/200 + 1/100]]
                          = [[76/100, 0], [0, 1/200]]
                          = [[19/25, 0], [0, 1/200]] ,
    e_1 = 19/25 + 1/200 = 152/200 + 1/200 = 153/200 >= 0 ,
    e_2 = det = (19/25)(1/200) = 19/5000 >= 0 ,
so X >= 0 by Eq. eq:psdtest and the row ADMITS. The tolerance is LOAD-BEARING
here: at eps_op = 0, X = A_h and e_2 = -3/800 < 0.

DECIDED DIRECTLY BY Eq. eq:psdtest, without eq:normtest: Proposition
prop:tolrows says of this row that "eq:negpart IS eq:psdtest DIRECTLY".""",
    ),
    ToleranceRowCase(
        case_id="TOL2-negpart-y0t0-refuse-at-zero",
        claims=("PR13",),
        row="prop:tolrows (ii) -- negative part, at eps_op = 0",
        eps_op=F(0),
        tested_matrix=diag_matrix((F(3, 4), F(-1, 200))),
        principal_minor_sums=(F(149, 200), F(-3, 800)),
        admitted=False,
        reason="declaration_outside_tolerance",
        labels=("prop:tolrows", "eq:negpart", "lem:exactpsd", "eq:psdtest"),
        derivation="""\
THE SAME BLOCK AT eps_op = 0. X = A_h = [[3/4, 0], [0, -1/200]], so
    e_1 = 3/4 - 1/200 = 150/200 - 1/200 = 149/200 >= 0 ,
    e_2 = det = -3/800 < 0  ==>  REFUSE .
e_1 IS POSITIVE AND e_2 IS NOT. An implementation that tested only the trace --
or only e_1, which for a 2 x 2 matrix IS the trace -- would ADMIT a declaration
the contract refuses, in the direction that matters: A_h has a negative
eigenvalue, so the declared block is not within any tolerance of a positive
operator smaller than 1/200. Eq. eq:psdtest's quantifier "for every
k = 1, ..., d" is what excludes it.""",
    ),
    ToleranceRowCase(
        case_id="TOL2-complete-t0-admit",
        claims=("PR13",),
        row="prop:tolrows (iii) -- completeness defect at t0",
        eps_op=F(1, 100),
        tested_matrix=real_matrix(
            ((F(15, 40000), F(-1, 40000)), (F(-1, 40000), F(14, 40000))),
        ),
        principal_minor_sums=(F(29, 40000), F(209, 1600000000)),
        admitted=True,
        reason="",
        labels=("prop:tolrows", "eq:compdefect", "lem:exactpsd", "eq:normtest"),
        derivation="""\
PROPOSITION prop:tolrows (iii), Eq. eq:compdefect, AT t = t0.
    sum_y blk M^{=0}_{y|t0}
      = [[3/4, 1/200], [-1/200, -1/200]] + [[1/4, 0], [0, 1]]
      = [[1, 1/200], [-1/200, 199/200]] ,
    Z := that sum - 1_2 = [[0, 1/200], [-1/200, -1/200]] .
Z is NOT skew and NOT normal, so its norm is a genuine two-by-two computation:
    Z-dagger Z = Z^T Z = [[0, -1/200], [1/200, -1/200]] [[0, 1/200], [-1/200, -1/200]]
               = (1/40000) [[1, 1], [1, 2]] .
    (1,1): 0*0 + (-1/200)(-1/200) = 1/40000
    (1,2): 0*(1/200) + (-1/200)(-1/200) = 1/40000
    (2,1): (1/200)*0 + (-1/200)(-1/200) = 1/40000
    (2,2): (1/200)(1/200) + (-1/200)(-1/200) = 2/40000

THE TEST, Eq. eq:normtest, at delta = |Y| eps_op = 2/100 = 1/50, so
delta^2 = 1/2500 = 16/40000:
    W := delta^2 1_2 - Z-dagger Z = (1/40000) [[15, -1], [-1, 14]] ,
    e_1 = (15 + 14)/40000 = 29/40000 >= 0 ,
    e_2 = det = (15*14 - 1)/40000^2 = 209/1600000000 >= 0 ,
so W >= 0 and the row ADMITS. ||Z|| is IRRATIONAL here -- the eigenvalues of
Z-dagger Z are (3 +- sqrt5)/(2*40000) -- WHICH IS EXACTLY WHY THE CONTRACT
STATES THE TEST AS eq:normtest AND NOT AS A NORM COMPUTATION: Lemma
lem:exactpsd (ii) decides ||Z|| <= delta without ever computing ||Z||, and
"NO EIGENVALUE IS COMPUTED".

AT t1 THE DEFECT IS ZERO: blk M^{=0}_{y0|t1} + blk M^{=0}_{y1|t1} = 1_2
exactly, so Z = 0, W = delta^2 1_2 >= 0, and the row admits at EVERY eps_op
including 0. One declaration, one setting that needs the tolerance and one that
does not.""",
    ),
    ToleranceRowCase(
        case_id="TOL2-postproc-herm-y0t0-admit",
        claims=("PR13",),
        row="prop:tolrows (iv) -- Hermiticity defect of the post-processed family",
        eps_op=F(1, 100),
        tested_matrix=diag_matrix((F(119, 562500), F(119, 562500))),
        principal_minor_sums=(F(119, 281250), F(14161, 316406250000)),
        admitted=True,
        reason="",
        labels=("prop:tolrows", "lem:tolprop", "eq:tolprop", "lem:exactpsd"),
        derivation="""\
PROPOSITION prop:tolrows (iv) ON THE POST-PROCESSED FAMILY, at v = (y0, t0),
where the threshold is 2 eta_v and NOT 2 eps_op. This is the row that makes
Lemma lem:tolprop's propagation observable.

    A := blk M^{=0}_{(y0,t0)|nb} = [[8/15, 1/300], [-1/300, 13/100]] ,
    Z := A - A-dagger = [[0, 2/300], [-2/300, 0]] = [[0, 1/150], [-1/150, 0]] ,
    Z-dagger Z = (1/22500) 1_2 ,  so ||Z|| = 1/150 .
Note Z = (2/3) times the block-level Z of TOL2-herm-y0t0-admit, exactly as step
2 of Section 2.2 multiplies by q_t0 = 2/3: (2/3)(1/100) = 1/150.

THE TEST at delta = 2 eta_(y0,t0) = 2/125, delta^2 = 4/15625:
    4/15625 = 144/562500 and 1/22500 = 25/562500 (LCM(15625, 22500) = 562500) ,
    W = (144 - 25)/562500 * 1_2 = (119/562500) 1_2 ,
    e_1 = 238/562500 = 119/281250 >= 0 ,
    e_2 = (119/562500)^2 = 14161/316406250000 >= 0 ,
so the row ADMITS. THE THRESHOLD SCALED AND SO DID THE DEFECT: both by q_t0,
which is why the decision is the same at both levels. Lemma lem:tolprop is the
statement that this is not an accident.""",
    ),
    ToleranceRowCase(
        case_id="TOL2-postproc-complete-t0-admit",
        claims=("PR13",),
        row="prop:tolrows (iv) -- completeness defect of the post-processed family",
        eps_op=F(1, 100),
        tested_matrix=real_matrix(
            ((F(551, 2250000), F(-25, 2250000)), (F(-25, 2250000), F(526, 2250000))),
        ),
        principal_minor_sums=(F(1077, 2250000), F(289201, 5062500000000)),
        admitted=True,
        reason="",
        labels=("prop:tolrows", "lem:tolprop", "lem:exactpsd", "eq:normtest"),
        derivation="""\
PROPOSITION prop:tolrows (iv), THE COMPLETENESS CLAUSE, "READ AT FIXED t
AGAINST q_t 1_{C_m}" and at the threshold q_t |Y| dcf eps_op.

    sum_y blk M^{=0}_{(y,t0)|nb} = [[8/15 + 2/15, 1/300], [-1/300, 13/100 + 8/15]]
      = [[2/3, 1/300], [-1/300, 199/300]] ,        13/100 + 8/15 = 39/300 + 160/300
    Z := that sum - q_t0 1_2 = [[0, 1/300], [-1/300, -1/300]] ,
which is (2/3) times the block-level Z of TOL2-complete-t0-admit, as step 2
requires. Hence
    Z-dagger Z = (4/9)(1/40000) [[1, 1], [1, 2]] = (1/90000) [[1, 1], [1, 2]] .

THE TEST at delta = q_t0 |Y| dcf eps_op = (2/3)(2)(6/5)(1/100) = 24/1500 =
2/125, delta^2 = 4/15625. With LCM(15625, 90000) = 2250000:
    4/15625 = 576/2250000 ,   1/90000 = 25/2250000 ,
    W = (1/2250000) ( [[576, 0], [0, 576]] - 25 [[1, 1], [1, 2]] )
      = (1/2250000) [[551, -25], [-25, 526]] ,
    e_1 = (551 + 526)/2250000 = 1077/2250000 >= 0 ,
    e_2 = (551*526 - 625)/2250000^2 = (289826 - 625)/2250000^2
        = 289201/5062500000000 >= 0 ,
so the row ADMITS. 551*526 = 551*500 + 551*26 = 275500 + 14326 = 289826.""",
    ),
    ToleranceRowCase(
        case_id="TOL-herm-refuse",
        claims=("PR13",),
        row="prop:tolrows (i) -- a block FAILING Hermiticity within eps_op",
        eps_op=F(1, 100),
        tested_matrix=diag_matrix((F(-8, 2500), F(-8, 2500))),
        principal_minor_sums=(F(-16, 2500), F(64, 6250000)),
        admitted=False,
        reason="declaration_outside_tolerance",
        labels=("prop:tolrows", "eq:herm", "lem:exactpsd", "eq:normtest"),
        derivation="""\
A DECLARED BLOCK WHOSE HERMITICITY DEFECT EXCEEDS THE DECLARED TOLERANCE:
    A = [[3/4, 3/100], [-3/100, 1/4]] ,
    Z = A - A-dagger = [[0, 6/100], [-6/100, 0]] = [[0, 3/50], [-3/50, 0]] ,
    Z-dagger Z = (9/2500) 1_2 ,   ||Z|| = 3/50 .
THE TEST at delta = 2 eps_op = 1/50, delta^2 = 1/2500:
    W = (1/2500 - 9/2500) 1_2 = -(8/2500) 1_2 ,
    e_1 = -16/2500 < 0  ==>  W is NOT >= 0  ==>  ||Z|| > 2 eps_op  ==>  REFUSE
    `declaration_outside_tolerance` .
Again e_2 = 64/6250000 IS POSITIVE and e_1 is the one that fails: for a negative
multiple of the identity in even dimension the determinant is positive.

WHY THE REFUSAL IS RIGHT AND NOT MERELY CONSERVATIVE. Proposition prop:tolrows
(i) is a NECESSARY condition of Assumption A-OPTOL: if a starred family existed
within eps_op of this block then, A* being Hermitian, ||A - A-dagger|| =
||Delta - Delta-dagger|| <= 2 eps_op. It does not, so "a declaration failing any
of them CONTRADICTS Assumption A-OPTOL, and Section 4.13 REFUSES IT" -- there is
no starred model for Theorem thm:tolerance to run on.""",
    ),
    ToleranceRowCase(
        case_id="TOL-posdef-refuse-e1-passes",
        claims=("PR13",),
        row="prop:tolrows (ii) -- positivity failure that e_1 alone does not catch",
        eps_op=F(1, 100),
        tested_matrix=diag_matrix((F(19, 25), F(-1, 100))),
        principal_minor_sums=(F(3, 4), F(-19, 2500)),
        admitted=False,
        reason="declaration_outside_tolerance",
        labels=("prop:tolrows", "eq:negpart", "lem:exactpsd", "eq:psdtest"),
        derivation="""\
A DECLARED BLOCK WHOSE NEGATIVE PART EXCEEDS THE DECLARED TOLERANCE, chosen so
that THE FIRST PRINCIPAL-MINOR SUM PASSES AND THE SECOND DOES NOT.
    A = [[3/4, 0], [0, -1/50]] , Hermitian, so A_h = A ,
    X := A_h + eps_op 1_2 = [[3/4 + 1/100, 0], [0, -1/50 + 1/100]]
                          = [[19/25, 0], [0, -1/100]] ,
    e_1 = 19/25 - 1/100 = 76/100 - 1/100 = 75/100 = 3/4  >= 0   (PASSES) ,
    e_2 = det = (19/25)(-1/100) = -19/2500  < 0            (FAILS) ,
so X is NOT >= 0 and the row REFUSES `declaration_outside_tolerance`.

THIS IS THE FIRST HALF OF THE PAIR THAT PINS Eq. eq:psdtest'S QUANTIFIER. Here
e_1 >= 0 and e_2 < 0. The second half, TOL-posdef-refuse-leading-minors-pass,
has both LEADING principal minors >= 0 and e_1 < 0. Together they exclude both
of the two tests an implementation is most likely to substitute: the trace
alone, and Sylvester's leading-minor criterion.""",
    ),
    ToleranceRowCase(
        case_id="TOL-posdef-refuse-leading-minors-pass",
        claims=("PR13",),
        row="prop:tolrows (ii) -- positivity failure the LEADING minors do not catch",
        eps_op=F(1, 100),
        tested_matrix=diag_matrix((0, F(-1, 50))),
        principal_minor_sums=(F(-1, 50), F(0)),
        admitted=False,
        reason="declaration_outside_tolerance",
        labels=("prop:tolrows", "eq:negpart", "lem:exactpsd", "eq:psdtest"),
        derivation="""\
THE SYLVESTER TRAP, FROZEN. Sylvester's criterion on the LEADING principal
minors characterizes POSITIVE DEFINITENESS, not positive SEMIdefiniteness, and
Eq. eq:psdtest is a semidefiniteness test. The classic counterexample is
diag(0, -1) and this case is it, scaled into the fixture:
    A = [[-1/100, 0], [0, -3/100]] ,  A_h = A ,
    X := A_h + eps_op 1_2 = [[-1/100 + 1/100, 0], [0, -3/100 + 1/100]]
                          = [[0, 0], [0, -1/50]] .
LEADING PRINCIPAL MINORS: the 1 x 1 top-left minor is 0 >= 0 and the 2 x 2
determinant is 0 >= 0. AN IMPLEMENTATION TESTING THOSE TWO WOULD ADMIT.
Eq. eq:psdtest's SUMS OF ALL k x k PRINCIPAL MINORS:
    e_1 = 0 + (-1/50) = -1/50  < 0    ==>  REFUSE ,
    e_2 = det = 0 .
X has eigenvalue -1/50, so it is genuinely not positive semidefinite and the
refusal is correct.

REMARK rem:psdalgorithm PERMITS ANY EXACT PROCEDURE FOR THE PREDICATE -- "the
Faddeev-Le Verrier recursion, ... any division-free characteristic-polynomial
method, or ... a rational LDL-dagger factorization with symmetric pivoting" --
BUT IT IS THE PREDICATE eq:psdtest THAT IS FIXED, and the leading-minor test is
a DIFFERENT PREDICATE, not a different algorithm for this one. That distinction
is what this case exists to make checkable.""",
    ),
    ToleranceRowCase(
        case_id="TOL-threshold-form-boundary-admit",
        claims=("PR13",),
        row="lem:exactpsd (ii) -- the threshold form, exactly on the boundary",
        eps_op=F(1, 100),
        tested_matrix=diag_matrix((F(0), F(0))),
        principal_minor_sums=(F(0), F(0)),
        admitted=True,
        reason="",
        labels=("lem:exactpsd", "eq:normtest", "prop:tolrows", "eq:herm"),
        derivation="""\
THE THRESHOLD FORM OF LEMMA lem:exactpsd (ii), TAKEN EXACTLY ON THE BOUNDARY,
where the relation is <= and the boundary is therefore ADMITTED.
    A = [[1/2, 1/100], [-1/100, 1/2]] ,
    Z = A - A-dagger = [[0, 2/100], [-2/100, 0]] = [[0, 1/50], [-1/50, 0]] ,
    Z-dagger Z = (1/2500) 1_2 ,   ||Z|| = 1/50 = 2 eps_op  EXACTLY .
THE TEST at delta = 2 eps_op = 1/50, delta^2 = 1/2500:
    W = (1/2500 - 1/2500) 1_2 = 0 ,
    e_1 = 0 >= 0 ,  e_2 = 0 >= 0     ==>  W >= 0  ==>  ADMIT .
Eq. eq:normtest states the equivalence with a NON-STRICT inequality on both
sides -- "||Z|| <= delta  <=>  delta^2 1 - Z-dagger Z >= 0" -- and eq:psdtest
likewise tests e_k >= 0, so the zero matrix is admitted and the boundary belongs
to the accepting side. AN IMPLEMENTATION USING A STRICT COMPARISON ANYWHERE IN
THE CHAIN REFUSES THIS DECLARATION AND IS WRONG.

THIS CASE IS ALSO ONE OF THE TWO FLOAT-SENSITIVE ONES: see
TOL_FLOAT_SENSITIVE_CASES.""",
    ),
)


# ---------------------------------------------------------------------------
#  The emitted constants at a positive tolerance (cor:tolentries)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToleranceEntryCase:
    """One emitted constraint entry, frozen at eps_op = 0 AND at eps_op > 0.

    The point of the pairing is Section 2.3's warning: "EMITTING A 0.1.3
    CONSTANT AT eps_op > 0 IS UNSAFE -- it would restrict A_CList MORE TIGHTLY
    than eq:certificate licenses, so a physical composite attack could fall
    outside the declared admissible set and the inclusion Thm. thm:licence
    certifies would fail." So both constants are frozen and the test asserts
    that the second is never STRONGER than the first.
    """

    case_id: str
    claims: tuple[str, ...]
    clause: str
    ohat_label: str
    #: (relation, constant) pairs emitted at eps_op = 0. One entry, except that
    #: the probe-expectation entry is a single EQUALITY there.
    at_zero: tuple[tuple[str, F], ...]
    #: (relation, constant) pairs emitted at the declared eps_op > 0. TWO for
    #: the probe-expectation entry (Cor. cor:tolentries (ii)).
    at_positive: tuple[tuple[str, F], ...]
    #: The shift the `operator_tolerance_record` carries for this entry.
    shift: str
    eps_op: F
    labels: tuple[str, ...]
    derivation: str


TOL_ENTRY_FLAG = ToleranceEntryCase(
    case_id="TOL2-entry-flag-sector",
    claims=("PR11", "PR13"),
    clause="cor:tolentries (i) -- the flag-sector entry",
    ohat_label="O^ = F^FSS_o|_nb - p_o Pi_{nb,flag},  o = (y0, t0),  p_o = 14/75",
    at_zero=((">=", F(0)),),
    at_positive=((">=", F(-1, 125)),),
    shift="-eta_o = -1/125",
    eps_op=F(1, 100),
    labels=("cor:tolentries", "eq:tolfss", "cor:fssinstance", "eq:fssentry"),
    derivation="""\
CORollARY cor:fssinstance GIVES THE ENTRY AND CORollARY cor:tolentries (i)
GIVES THE CONSTANT. Eq. eq:fssentry emits (O^, >=, 0) "for the family the target
is built from, WHICH IS WHAT THE EMITTED ARTIFACT CARRIES WHEN NO OPERATOR
TOLERANCE IS DECLARED". At eps_op > 0 the target is built from numbers that are
only eta_o-close to that family, and Eq. eq:tolfss reads
    Lambda*-dagger(O^)
      = ( (blkst M^{<=N}_{o|nb} + Delta_o) (+) (blkst M^{>N}_{o|nb} - p_o 1) )
        (x) N*_nb
      >= -eta_o 1_B ,
because blkst M^{<=N}_{o|nb} >= 0, the second summand is >= 0 by the certified
weights eq:certweights that A-OPTOL (a) asserts of the STARRED family, and
||Delta_o|| <= eta_o by eq:tolprop.

THE NUMBER ON TOL2. o = (y0, t0), so
    eta_o = q_t0 dcf eps_op = (2/3)(6/5)(1/100) = 12/1500 = 1/125 ,
and the emitted entry is (O^, >=, -1/125) AND NOT (O^, >=, 0) -- Section 2.3
clause (a), verbatim: "emitted as (O^, >=, -eta_o) and NOT as (O^, >=, 0)".

THE DIRECTION. -1/125 < 0, so the emitted constraint at eps_op > 0 ADMITS A
STRICTLY LARGER SET OF ATTACK CHANNELS than the 0.1.3 one: A_CList is
{A : A-dagger(O^ (x) 1) >= c 1}, monotone DECREASING in c. Emitting c = 0 at
eps_op > 0 would restrict the set more tightly than eq:certificate licenses,
which is exactly the unsafe direction Section 2.3 names.

WHAT DOES NOT CHANGE: the operator O^, the relation >=, the certificate CASE
(positivity, cor:pullback (ii)), the source-mode typing, and the presence rule
for the licence. ONLY THE CONSTANT MOVES.""",
)

TOL_ENTRY_PROBE_T0 = ToleranceEntryCase(
    case_id="TOL2-entry-probe-t0",
    claims=("PR11", "PR13", "PR9"),
    clause="cor:tolentries (ii) -- the probe-expectation entry at t0",
    ohat_label="O^ = sum_y F_(y,t0)",
    at_zero=(("=", F(2, 3)),),
    at_positive=((">=", F(244, 375)), ("<=", F(256, 375))),
    shift="+- delta_t0 = +- 2/125 around q_t0 = 2/3",
    eps_op=F(1, 100),
    labels=(
        "cor:tolentries",
        "eq:tolprobe",
        "eq:starprobeexact",
        "rem:unsound",
        "eq:branchprobeweight",
    ),
    derivation="""\
CORollARY cor:tolentries (ii). At eps_op = 0 the entry is the SINGLE EQUALITY
(O^, =, q_t) of Theorem thm:licence, which is what Remark rem:unsound says
"remains available on request UNDER THE CONDITION THAT MAKES ITS CERTIFICATE
DECIDABLE, AND NOT OTHERWISE". At eps_op > 0 it is REPLACED BY A PAIR:
    (O^, >=, q_t - delta_t)  and  (O^, <=, q_t + delta_t) ,
    delta_t = |Y| q_t dcf eps_op = |Y| eta_(y,t)   (Eq. eq:tolprobe) .

THE NUMBERS ON TOL2 AT t0. q_t0 = 2/3, |Y| = 2, eta_(y,t0) = 1/125, so
    delta_t0 = 2 * 1/125 = 2/125 ,
    q_t0 - delta_t0 = 250/375 - 6/375 = 244/375 ,
    q_t0 + delta_t0 = 250/375 + 6/375 = 256/375 ,
using 2/3 = 250/375 and 2/125 = 6/375.

THE WHOLE OF THE SHIFT COMES FROM THE nb BRANCH, and Eq. eq:starprobeexact is
why. The starred pull-back is EXACTLY q_t 1_B:
    Lambda*-dagger(O^*) = q_t sum_b 1_C (x) N*_b = q_t 1_B ,
because (1) the nb term is q_t 1_C (x) N*_nb by construction, (2) a declared
blinded branch is EXACT DECLARED DATA outside the tolerance -- A-OPTOL (b) gives
M*_{v|b} = M_{v|b} -- and the entry is emitted at all only once Section 4.13 has
decided the EXACT identity eq:branchprobeweight for that b at that t, and (3)
sum_b N*_b = sum_b N_b = 1_Bl exactly by def:blindmodel (b). "THERE IS THEREFORE
NO BLINDED CONTRIBUTION TO THE SHIFT AT ALL, WHICH IS WHAT NARROWING THE
TOLERANCE TO THE RECEIVER BLOCKS BUYS HERE."

The only defect left is the target's: ||O^ - O^*|| <= sum_y ||F_(y,t0) -
F*_(y,t0)|| <= sum_y eta_(y,t0) = |Y| eta = delta_t0, and Theorem thm:tolerance
(iv) applied TWICE -- once with >= and once with <=, both at c = q_t0 and
delta = delta_t0 -- gives the pair.

THE DIRECTION. The pair's feasible set CONTAINS the equality's: any A with
A-dagger(O^ (x) 1) = (2/3) 1 satisfies both >= 244/375 and <= 256/375. So the
0.2.0 entry is WEAKER, never stronger, which is the safe direction. At
eps_op = 0, delta_t0 = 0 and "the pair of (ii) COLLAPSES to the equality
entry".""",
)

TOL_ENTRY_PROBE_T1 = ToleranceEntryCase(
    case_id="TOL2-entry-probe-t1",
    claims=("PR11", "PR13", "PR9"),
    clause="cor:tolentries (ii) -- the probe-expectation entry at t1",
    ohat_label="O^ = sum_y F_(y,t1)",
    at_zero=(("=", F(1, 3)),),
    at_positive=((">=", F(122, 375)), ("<=", F(128, 375))),
    shift="+- delta_t1 = +- 1/125 around q_t1 = 1/3",
    eps_op=F(1, 100),
    labels=("cor:tolentries", "eq:tolprobe", "eq:starprobeexact"),
    derivation="""\
THE SECOND SETTING, frozen so that the t-DEPENDENCE of delta_t is observable and
an implementation cannot pass with a single global shift. q_t1 = 1/3,
eta_(y,t1) = (1/3)(6/5)(1/100) = 6/1500 = 1/250, so
    delta_t1 = |Y| eta_(y,t1) = 2/250 = 1/125 ,
    q_t1 - delta_t1 = 125/375 - 3/375 = 122/375 ,
    q_t1 + delta_t1 = 125/375 + 3/375 = 128/375 ,
using 1/3 = 125/375 and 1/125 = 3/375.

delta_t0 = 2/125 IS TWICE delta_t1 = 1/125, in the ratio q_t0 : q_t1 = 2 : 1,
which is the whole of the t-dependence: delta_t is linear in q_t and everything
else in it -- |Y|, dcf, eps_op -- is common to the two settings.""",
)

TOL_ENTRY_DEFAULT_CARRIED = ToleranceEntryCase(
    case_id="TOL2-entry-default-carried",
    claims=("PR11", "PR13", "PR9"),
    clause="cor:tolentries (iii) -- the default carried operators",
    ohat_label=(
        "the three operators of Eq. eq:blindtransport at |Blmode| = 2: "
        "Pi_{nb,<=N}, Pi_{nb,flag}, Pi_bl1"
    ),
    at_zero=((">=", F(0)),),
    at_positive=((">=", F(0)),),
    shift="0 -- unchanged at every eps_op",
    eps_op=F(1, 100),
    labels=("cor:tolentries", "eq:blindtransport", "thm:blinding", "eq:sectors"),
    derivation="""\
CORollARY cor:tolentries (iii), THE ONE FAMILY A POSITIVE TOLERANCE LEAVES
ALONE. Every operator of Eq. eq:blindtransport "is emitted with its 0.1.3
certificate UNCHANGED, c = 0 and relation >=: IT IS A SECTOR PROJECTOR,
IDENTICAL IN THE TWO MODELS by Theorem thm:tolerance (ii), and its pull-back
Pi_{<=N} (x) N*_nb, Pi_{>N} (x) N*_nb or 1_C (x) N*_b IS EXACTLY POSITIVE."

WHY IT IS IDENTICAL. Theorem thm:tolerance (ii)'s proof: "the operators of
eq:blindtransport -- Pi_{nb,<=N}, Pi_{nb,flag} and Pi_b -- are THE SECTOR
PROJECTORS OF eq:sectors, DETERMINED BY THE DECLARED DIMENSIONS AND ORDERS
ALONE, so they are the same operators in the two models." Nothing about them is
read off a declared block, so eq:targetdefect's difference is zero for them.

Section 2.1's `carried_operators` row says the same from the input side: "THAT
c = 0 IS UNCHANGED AT EVERY eps_op, these operators being exact sector
projectors (Cor. cor:tolentries (iii)); A REQUESTED OPERATOR IS A DIFFERENT
MATTER AND ITS CONSTANT SHIFTS."

THIS IS THE ONLY ENTRY IN THIS GROUP WHOSE at_zero AND at_positive AGREE, which
is what makes the group's monotonicity invariant non-vacuous rather than a
uniform strict inequality.""",
)

TOL_ENTRY_TWO_SECTOR = ToleranceEntryCase(
    case_id="TOL2-entry-two-sector",
    claims=("PR11", "PR13", "PR6"),
    clause="cor:tolentries (iv) -- a further requested entry, eq:two-sector-entry",
    ohat_label="O^ = F^FSS_e - a Pi_{<=N} - b Pi_flag,  e = (y0, t0)",
    at_zero=((">=", F(0)),),
    at_positive=((">=", F(-1, 125)),),
    shift="-delta(O^) = -eta_e = -1/125",
    eps_op=F(1, 100),
    labels=("cor:tolentries", "eq:tolgeneral", "eq:two-sector-entry", "rem:published"),
    derivation="""\
CORollARY cor:tolentries (iv), THE GENERAL RULE, ON THE ONE INSTANCE THE
CONTRACT WORKS OUT. Eq. eq:tolgeneral covers every requested entry of the form
    O^ = sum_v alpha_v F_v + Z ,
with declared real alpha_v and Z "a projector of eq:sectors or a declared real
combination of them", and gives
    ||O^ - O^*|| <= sum_v |alpha_v| eta_v =: delta(O^) .

FOR eq:two-sector-entry the operator is F^FSS_e - a Pi_{<=N} - b Pi_flag, so
alpha_e = 1 and every other alpha_v = 0, and Z = -a Pi_{<=N} - b Pi_flag is a
declared real combination of sector projectors. Hence
    delta(O^) = eta_e = eta_(y0,t0) = 1/125 ,
and the entry is emitted as (O^, >=, -1/125) AND NOT as (O^, >=, 0) --
Corollary cor:tolentries (iv), verbatim.

WHY a AND b DO NOT SHIFT. They "are DECLARED DEVICE CONSTANTS -- statements
about the PHYSICAL receiver, WHICH IS THE STARRED FAMILY -- and NOT quantities
recomputed from the declaration" (cor:tolentries (iv), proof; Assumptions
A-CONST and A-RECV). Z therefore "cancels because it is fixed by the declared
sector decomposition and so is common to the two models".

THE 0.1.3 CASE THIS SUPERSEDES is WP3-cert-two-sector, whose constant is 0; that value
stands AT eps_op = 0 and is marked superseded for eps_op > 0. Remark
rem:published closes with the same sentence: "The admissible object is the
operator entry eq:two-sector-entry with relation >= and c = 0 -- AT A DECLARED
eps_op > 0, WITH c = -eta_e INSTEAD, by Corollary cor:tolentries (iv)".""",
)

TOL_ENTRY_CASES: tuple[ToleranceEntryCase, ...] = (
    TOL_ENTRY_FLAG,
    TOL_ENTRY_PROBE_T0,
    TOL_ENTRY_PROBE_T1,
    TOL_ENTRY_DEFAULT_CARRIED,
    TOL_ENTRY_TWO_SECTOR,
)

#: CORollARY cor:tolentries, CLOSING PARAGRAPH: "TOGETHER, (i)-(iv) COVER EVERY
#: ENTRY THIS MODULE CAN EMIT". Frozen as the exhaustiveness list, so that a
#: fifth kind of emitted entry cannot appear without a failing test.
TOL_ENTRY_CLAUSES: tuple[str, ...] = (
    "cor:tolentries (i) -- the flag-sector entry",
    "cor:tolentries (ii) -- the probe-expectation entry",
    "cor:tolentries (iii) -- the default carried operators",
    "cor:tolentries (iv) -- any further requested entry of eq:tolgeneral's form",
)

#: A REQUESTED OPERATOR OUTSIDE Eq. eq:tolgeneral'S FORM. Refused, not emitted
#: at some other constant. THE WITNESS IS DECISIVE AND CHECKABLE: every operator
#: of the form sum_v alpha_v F_v + Z is SECTOR-BLOCK-DIAGONAL, the F_v by
#: Theorem thm:blinding (iii) and Z by construction, so an operator with a
#: non-zero entry BETWEEN two sectors of Eq. eq:sectors is not of that form --
#: there is no O^* and no delta for it.
TOL_ENTRY_OUTSIDE_FORM: dict[str, object] = {
    "case_id": "TOL2-entry-outside-tolgeneral-form",
    "claims": ("PR11", "PR13"),
    "eps_op": F(1, 100),
    "ohat_label": (
        "O^ = |q><f| + |f><q| with |q> in the nb preserved sector (nb, 0) and "
        "|f> the flag basis vector of the sector (nb, (y0,t0)) -- Hermitian, "
        "and NOT sector-block-diagonal for Eq. eq:sectors"
    ),
    "emitted": False,
    "reason": "constraint_without_certificate",
    "derivation": """\
CORollARY cor:tolentries, CLOSING PARAGRAPH, verbatim: "A REQUESTED OPERATOR
OUTSIDE THAT FORM IS NOT EMITTED AT SOME OTHER CONSTANT -- IT IS REFUSED: for
such an O^ there is NO STARRED COUNTERPART O^* AND NO delta, so Theorem
thm:tolerance (iv) DISCHARGES NO CERTIFICATE at eps_op > 0, Section 2.1's
requirement that each carried operator come with SOME certificate discharging
eq:certificate IS UNMET, and Section 4.13 REFUSES IT
`constraint_without_certificate`."

WHY THIS OPERATOR IS OUTSIDE THE FORM, AND WHY THAT IS DECIDABLE. Eq.
eq:tolgeneral's form is O^ = sum_v alpha_v F_v + Z with Z a projector of
Eq. eq:sectors or a declared real combination of them. EVERY F_v IS
SECTOR-BLOCK-DIAGONAL (Theorem thm:blinding (iii): "every F_v is
sector-block-diagonal, F_v = (+)_s F_v^(s), AND SO IS EVERY OPERATOR OF
eq:blindtransport"), and so is every real combination of sector projectors.
A sum of sector-block-diagonal operators is sector-block-diagonal. The frozen
O^ has a non-zero entry between the sector (nb, 0) and the sector (nb, (y0,t0)),
so IT IS NOT sector-block-diagonal and therefore NOT of eq:tolgeneral's form.

THE REFUSAL IS NOT NEW MATHEMATICS. Section 2.3's `constraint_list` row already
requires "EVERY O^_k IS SECTOR-BLOCK-DIAGONAL (Thm. thm:blinding (iii))", and
Section 2.1 already requires every carried operator to come with SOME
certificate. What 0.2.0 adds is the statement that at eps_op > 0 there is no
constant at which such an operator could be emitted instead.

NOTE WHAT IS NOT CLAIMED: that eq:tolgeneral's form and
sector-block-diagonality COINCIDE. They do not -- a sector-block-diagonal
operator need not lie in span{F_v} + {sector combinations}. This case freezes
one direction only, which is the direction the refusal needs: NOT
sector-block-diagonal ==> NOT of the form ==> refused.""",
}


# ---------------------------------------------------------------------------
#  eq:targetposcomp and the operator_tolerance_record
# ---------------------------------------------------------------------------

#: THEOREM thm:tolerance (ii), Eq. eq:targetposcomp: THE THREE AMOUNTS by which
#: the emitted target may violate meat-core 0.4.0 `ass:decl` (iii). Frozen at
#: v = (y0, t0) on TOL2, where eta_v = 1/125 and |Y| dcf eps_op = 3/125.
#:
#: They are DECLARED NUMBERS -- functions of eps_op, dcf, {q_t} and |Y| alone --
#: so they are frozen as the amounts and not reconstructed from a materialised
#: {F_v}: Theorem thm:tolerance (ii) derives each one FROM Proposition
#: prop:tolrows (iv) read on the nb preserved block, the flag blocks being
#: exactly common to the two models.
TOL2_TARGETPOSCOMP: dict[str, object] = {
    "case_id": "TOL2-targetposcomp",
    "claims": ("PR13", "PR9"),
    "outcome": ("y0", "t0"),
    "eps_op": F(1, 100),
    "hermiticity_defect": F(2, 125),
    "negative_part": F(1, 125),
    "completeness_defect": F(3, 125),
    "labels": ("thm:tolerance", "eq:targetposcomp", "eq:targetdefect"),
    "derivation": """\
EQ. eq:targetposcomp, THE THREE DISPLAYS, AT v = (y0, t0) ON TOL2:
    (1/2)(F_v + F_v-dagger) + eta_v 1_Q >= 0        with eta_v = 1/125 ,
    ||F_v - F_v-dagger|| <= 2 eta_v                 with 2 eta_v = 2/125 ,
    ||sum_v F_v - 1_Q|| <= |Y| dcf eps_op           = 2 * (6/5)(1/100) = 3/125 .

EVERY AMOUNT IS A DECLARED NUMBER. eta_v = q_t dcf eps_op = (2/3)(6/5)(1/100) =
1/125 and |Y| dcf eps_op = 12/500 = 3/125. NONE of the three is read off a
materialised target, and none needs to be: Theorem thm:tolerance (ii) derives
them from Eq. eq:targetdefect, which confines the whole difference to the nb
PRESERVED BLOCK -- "F_v - F*_v = (blk M^{<=N}_{v|nb} - blkst M^{<=N}_{v|nb})
(+) 0" -- and then reads Proposition prop:tolrows (iv) there.

THE COMPLETENESS AMOUNT IS v-INDEPENDENT while the other two are not: it is a
statement about sum_v F_v, and its proof runs sum_v M_{v|nb} = sum_t q_t sum_y
M~_{y|t}, "whose defect from 1_C is at most sum_t q_t |Y| dcf eps_op =
|Y| dcf eps_op" -- the q_t summing to one. So 3/125 is the same number at
(y1, t0), (y0, t1) and (y1, t1), while eta_v is 1/125 at t0 and 1/250 at t1.

WHAT THESE THREE ARE FOR, AND WHAT THEY ARE NOT. Section 2.3's `target_povm`
row: at eps_op > 0 the emitted numbers "NEED NOT THEMSELVES BE HERMITIAN,
POSITIVE SEMIDEFINITE, OR COMPLETE", and by these three amounts "they may
violate meat-core 0.4.0 ass:decl (iii)" -- (iii) ONLY, "(i) being the
finite-dimensionality and finite-alphabet condition, WHICH THE DECLARED
DESCRIPTOR SATISFIES EXACTLY AT EVERY eps_op". WHAT THE CONSUMER DOES WITH THAT
"IS THE CONSUMER'S RULE AND NOT THIS MODULE'S", and NOTHING ABOUT THE CONSUMER
IS FROZEN HERE.

SECTOR-BLOCK-DIAGONALITY IS NOT AMONG THE THREE and is not degraded: "it is a
property of the declared decomposition, EXACT AT EVERY eps_op".""",
}

#: SECTION 2.3, `operator_tolerance_record`. The contents at eps_op > 0, and the
#: `null` at eps_op = 0. FROZEN AS CONTENT AND PRESENCE, NOT AS A SCHEMA:
#: interface.yaml records the serialization as open implementation choice 12 of
#: 12, and nothing here decides it.
TOL2_TOLERANCE_RECORD: dict[str, object] = {
    "case_id": "TOL2-tolerance-record",
    "claims": ("PR13", "PR12"),
    "present": True,
    "operator_tolerance": F(1, 100),
    "norm": "operator norm",
    "dark_count_factor": F(6, 5),
    "eta_v": (
        (("y0", "t0"), F(1, 125)),
        (("y1", "t0"), F(1, 125)),
        (("y0", "t1"), F(1, 250)),
        (("y1", "t1"), F(1, 250)),
    ),
    "per_entry_shift": (
        ("TOL2-entry-flag-sector", F(-1, 125)),
        ("TOL2-entry-probe-t0", F(2, 125)),
        ("TOL2-entry-probe-t1", F(1, 125)),
        ("TOL2-entry-default-carried", F(0)),
        ("TOL2-entry-two-sector", F(-1, 125)),
    ),
    "carries_thm_tolerance_i_ii": True,
    "labels": (
        "thm:tolerance",
        "eq:dcf",
        "eq:etadef",
        "prop:tolrows",
        "cor:tolentries",
    ),
    "derivation": """\
SECTION 2.3, `operator_tolerance_record`, ITEM BY ITEM. "PRESENT EXACTLY WHEN
THE REQUEST DECLARES eps_op > 0; `null` OTHERWISE. It carries the declared
eps_op, THE NORM IT IS STATED IN, the dark-count factor dcf of Eq. eq:dcf, the
per-outcome eta_v = q_t dcf eps_op, and the MEASURED DEFECTS of Proposition
prop:tolrows. IT CARRIES TWO FURTHER THINGS, BOTH BINDING. FIRST, the
substantive content: THE STATEMENT OF THEOREM thm:tolerance (i)-(ii) -- there is
an exact POVM {F*_v} on the declared Q, block diagonal for the emitted sector
set eq:sectors, with ||F_v - F*_v|| <= eta_v for every v, FOR WHICH EVERY
ASSERTION OF THIS ARTIFACT HOLDS EXACTLY. SECOND, THE SHIFT APPLIED TO EVERY
EMITTED CONSTRAINT CONSTANT, ENTRY BY ENTRY, together with the part of Theorem
thm:tolerance (iv) and Cor. cor:tolentries that discharges it: -eta_o for the
flag-sector entry, +-delta_t around q_t for the probe-expectation pair, 0 for
each default carried operator, and delta(O^) of eq:tolgeneral for any further
requested entry -- SO THAT A READER OF THE ARTIFACT ALONE CAN SEE WHICH CONSTANT
WAS EMITTED AND WHY IT IS NOT THE 0.1.3 ONE."

THE PER-ENTRY SHIFTS ABOVE ARE MAGNITUDES KEYED BY CASE ID, and each resolves to
a ToleranceEntryCase in TOL_ENTRY_CASES. The flag-sector and two-sector shifts are
recorded as the SIGNED constants -1/125 the entries carry; the probe shifts as
the delta_t the pair is built around, the pair itself being
(q_t - delta_t, q_t + delta_t); the default carried operators as 0.

THE RECORD IS ITSELF EXACT. Remark rem:tolboundary, first consequence: "dcf and
every eta_v are computed from EXACT SCALARS AND EXACT BLOCK ENTRIES, SO THE
TOLERANCE RECORD IS ITSELF EXACT." Every number above is a rational.

WHAT THE RECORD DOES NOT ASSERT, transcribed because it is the one thing a
reader could take it to mean: "The emitted numbers are a declaration of the
starred target to accuracy eta_v AND NOTHING MORE; NO BOUND RELATING A KEY
LENGTH COMPUTED FROM {F_v} TO ONE COMPUTED FROM {F*_v} IS ASSERTED HERE OR
ANYWHERE IN THIS CONTRACT (Thm. thm:tolerance (v))."

NO SCHEMA IS FROZEN. The keying of "entry by entry" is open -- Definition
def:link gives a link no identifier (interface.yaml open choice 6) -- and so is
the machine form of "the norm it is stated in". interface.yaml records both
under open implementation choice 12.""",
}

#: THE `null` HALF OF THE PRESENCE RULE. At eps_op absent -- which IS eps_op = 0
#: -- the record is `null`, and every 0.1.3 decision and constant returns.
TOL2_TOLERANCE_RECORD_ABSENT: dict[str, object] = {
    "case_id": "TOL2-tolerance-record-absent",
    "claims": ("PR13", "PR12"),
    "present": False,
    "operator_tolerance": F(0),
    "record": None,
    "labels": ("thm:tolerance", "cor:tolentries"),
    "derivation": """\
SECTION 2.3: the record is "`null` OTHERWISE", and Section 2.1: "ABSENT IS
eps_op = 0, AND AT eps_op = 0 EVERY RULE OF SECTION 4.13 IS THE EXACT TEST
VERSION 0.1.3 APPLIED". Theorem thm:tolerance closes with the same:
"At eps_op = 0 the starred family IS the declared one, eta_v = 0, every
difference above vanishes, and (i)-(iv) are the statements of Sections 4.6-4.12
UNCHANGED", and Corollary cor:tolentries: "At eps_op = 0 every eta_v vanishes,
EACH SHIFTED CONSTANT IS THE 0.1.3 CONSTANT, and the pair of (ii) COLLAPSES to
the equality entry."

THE PRESENCE RULE IS AN IFF AND IS FROZEN AS ONE: record present <=> eps_op > 0.
There is no third state -- no empty record at eps_op = 0 and no absent record at
eps_op > 0 -- and the integrity test asserts the biconditional over
TOL_ENTRY_CASES and these two cases.

AT eps_op = 0 THE ASSUMPTION IS STILL NAMED AND STILL NOT VACUOUS. A-OPTOL's
ledger row: "AT eps_op = 0 THE ASSUMPTION IS NOT VACUOUS: it is then the
substantive statement that the declared blocks are the physical ones, WHICH
VERSION 0.1.3 RELIED ON WITHOUT STATING IT, and a violation there is the same
security break with eta_v = 0." So `assumption_ledger` carries A-OPTOL at every
eps_op even though `operator_tolerance_record` is null at zero.""",
}


# ---------------------------------------------------------------------------
#  A-OPTOL's scope: the tolerance reaches the receiver blocks and no other
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToleranceScopeCase:
    """One declared operator family, and whether the tolerance reaches it.

    The three families are Assumption ``ass:optol``'s: the receiver blocks it
    covers by clause (a), and the declared blinded-branch POVMs and ``{N_b}``
    it excludes by clause (b). ``decided_at_every_eps_op`` is True exactly for
    the two excluded families, whose conditions "keep version 0.1.3's EXACT
    conditions" and are "WEAKENED BY NO TOLERANCE".
    """

    case_id: str
    claims: tuple[str, ...]
    family: str
    covered_by_tolerance: bool
    admitted: bool
    reason: str
    decided_at_every_eps_op: bool
    labels: tuple[str, ...]
    derivation: str


TOL_SCOPE_CASES: tuple[ToleranceScopeCase, ...] = (
    ToleranceScopeCase(
        case_id="TOL-scope-receiver-block-admit",
        claims=("PR13",),
        family="the declared receiver photon-number blocks blk M^{=m}_{y|t}, m <= N",
        covered_by_tolerance=True,
        admitted=True,
        reason="",
        decided_at_every_eps_op=False,
        labels=("ass:optol", "def:tolerance", "prop:tolrows", "rem:tolboundary"),
        derivation="""\
THE COVERED FAMILY, Assumption A-OPTOL clause (a). TOL2's four declared blocks
pass every part of Proposition prop:tolrows at eps_op = 1/100 and FAIL two of
them at eps_op = 0 -- see TOL_ROW_CASES, whose admit/refuse pairs are exactly
that statement. "THE ASSUMPTION IS ABOUT ONE DECLARED FAMILY AND ONE ONLY: THE
RECEIVER'S PHOTON-NUMBER BLOCKS blk M^{=m}_{y|t}, m <= N, which is the family
the boundary-gap decision names AND THE ONLY OPERATOR DATUM THIS
CONTRACT REQUIRES TO BE PRESENTED AS A FINITE LIST OF MATRICES."

`decided_at_every_eps_op` IS FALSE HERE because that is precisely what the
tolerance buys on this family: the decision depends on eps_op.""",
    ),
    ToleranceScopeCase(
        case_id="TOL-scope-blinded-branch-refuse",
        claims=("PR13", "PR9"),
        family="a declared blinded-branch POVM {M_{v|bl1}}",
        covered_by_tolerance=False,
        admitted=False,
        reason="blinding_model_ill_formed",
        decided_at_every_eps_op=True,
        labels=("ass:optol", "def:blindmodel", "rem:tolboundary", "thm:mixture"),
        derivation="""\
A DECLARED BLINDED BRANCH FAILING AN EXACT CONDITION, REFUSED REGARDLESS OF
eps_op. The declared branch is
    M_((y0,t0)|bl1) = diag(1/2, 1/3)  ,  M_((y1,t0)|bl1) = diag(1/6, 1/3) ,
    M_((y0,t1)|bl1) = diag(1/6, 1/6)  ,  M_((y1,t1)|bl1) = diag(1/6, 1/6 - 1/1000) ,
whose sum over V is
    diag(1/2 + 1/6 + 1/6 + 1/6, 1/3 + 1/3 + 1/6 + 1/6 - 1/1000)
      = diag(1, 1 - 1/1000) ,
so it is NOT a POVM. Every element is positive semidefinite, so the only defect
is completeness, and IT IS 1/1000 -- TEN TIMES SMALLER THAN THE DECLARED
eps_op = 1/100.

IT IS REFUSED ANYWAY, AT EVERY eps_op INCLUDING eps_op = 1/100 AND
eps_op = 1000/1 IF ONE WERE DECLARED. Assumption A-OPTOL clause (b): the
declared blinded-branch POVMs "are OUTSIDE this assumption: M*_{v|b} = M_{v|b},
and THEY KEEP VERSION 0.1.3'S EXACT CONDITIONS -- each declared branch an EXACT
POVM on C over V... NO TOLERANCE IS OFFERED ON EITHER, and Lemma lem:exactpsd IS
NOT CLAIMED FOR EITHER." Section 4.13's `blinding_model_ill_formed` row says the
same of itself: "UNCHANGED FROM VERSION 0.1.3, AND THE DECLARED TOLERANCE DOES
NOT REACH THIS ROW."

THE REASON IS DECISIVE RATHER THAN EDITORIAL, and Remark rem:tolboundary gives
it: a blinded branch is a POVM on C, THE FULL FOCK SPACE, which Definition
def:blindmodel (c) "DELIBERATELY DECLINES to require block diagonal", so "IT HAS
NO FINITE MATRIX PRESENTATION ANYWHERE IN THIS CONTRACT, Lemma lem:exactpsd is
unavailable for it, and A DEFECT BOUND ON IT COULD NOT BE DECIDED FROM ANYTHING
THE INTERFACE DECLARES". THE 2 x 2 MATRICES ABOVE ARE A FIXTURE CONVENIENCE, NOT
A LICENCE: the contract requires no finite presentation and this registry
asserts none.

Section 1.1 records that the FIRST draft of 0.2.0 extended A-OPTOL to this
family and that the extension was WITHDRAWN, "the reason being decisive rather
than editorial". THIS CASE IS THAT WITHDRAWAL MADE CHECKABLE.""",
    ),
    ToleranceScopeCase(
        case_id="TOL-scope-register-povm-refuse",
        claims=("PR13", "PR8", "PR9"),
        family="the blinding-register family {N_b}",
        covered_by_tolerance=False,
        admitted=False,
        reason="blinding_model_ill_formed",
        decided_at_every_eps_op=True,
        labels=("ass:optol", "def:blindmodel", "rem:tolboundary", "ass:dim"),
        derivation="""\
THE BLINDING-REGISTER FAMILY FAILING AN EXACT CONDITION, REFUSED REGARDLESS OF
eps_op. The declaration is
    N_nb  = diag(9/25, 16/25) ,
    N_bl1 = diag(16/25, 9/25 - 1/1000) ,
whose sum is diag(1, 1 - 1/1000) != 1_Bl, so {N_b} is NOT a POVM on Bl. Again
the defect is 1/1000, ten times smaller than eps_op = 1/100, AND AGAIN THE
DECLARATION IS REFUSED AT EVERY eps_op.

THE REASON IS DIFFERENT FROM THE BLINDED BRANCH'S AND IS WORTH KEEPING APART.
Remark rem:tolboundary: "Bl is A FACTOR OF THE PHYSICAL SYSTEM B = C Bl, WHICH
ASSUMPTION A-DIM SAYS IS SEPARABLE AND MAY BE INFINITE-DIMENSIONAL; that
assumption's finiteness clause covers H(Q) and the side registers, NOT Bl, AND
dim H(Bl) IS NOWHERE DECLARED OR BOUNDED." So Lemma lem:exactpsd -- which is
stated for matrices of declared finite dimension d -- has nothing to run on.
"The same conclusion follows, and IT TOO KEEPS VERSION 0.1.3'S EXACT POVM
CONDITION."

THE FIXTURE'S 2 x 2 MATRICES DO NOT CONTRADICT THAT: a declaration MAY happen
to present a finite register, and the exact condition is then decided on it as
0.1.3 decided it. What the contract does not do is REQUIRE a finite
presentation, which is what a tolerance on this family would need.

THE 0.1.3 CASE R-blinding-model REMAINS VALID AND IS NOT SUPERSEDED: its row is
explicitly "UNCHANGED FROM VERSION 0.1.3". These two cases ADD the
at-every-eps_op quantifier that 0.1.3 had no way to state.""",
    ),
)


# ---------------------------------------------------------------------------
#  eq:branchprobeweight as the Section 4.13 rule at every eps_op (F-5-01)
# ---------------------------------------------------------------------------
#
#  THE NARROWING RULED ("Narrow the precis"), made
#  checkable. The probe-expectation certificate is discharged EXACTLY WHEN every
#  blinded mode has a DECLARED branch POVM and Eq. eq:branchprobeweight holds
#  for that b at EVERY declared t; otherwise the entry is REFUSED
#  `constraint_without_certificate`. The condition is decided on EXACT declared
#  data at every eps_op, "a declared blinded branch lying OUTSIDE Assumption
#  A-OPTOL and being EXACT DECLARED DATA by its clause (b)".

#: A DECLARED BLINDED BRANCH THAT SATISFIES Eq. eq:branchprobeweight.
#: sum_y M_((y,t)|bl1) = q_t 1_C for each t, and the branch is an exact POVM.
#: M_((y0,t0)|bl1) is |+><+| scaled by q_t0 and is NOT block diagonal at the
#: cutoff -- Definition def:blindmodel (c) permits exactly that.
TOL2_BRANCH_PASS: tuple[tuple[tuple[str, str], Matrix], ...] = (
    (("y0", "t0"), real_matrix(((F(1, 3), F(1, 3)), (F(1, 3), F(1, 3))))),
    (("y1", "t0"), real_matrix(((F(1, 3), F(-1, 3)), (F(-1, 3), F(1, 3))))),
    (("y0", "t1"), real_matrix(((F(1, 3), 0), (0, 0)))),
    (("y1", "t1"), real_matrix(((0, 0), (0, F(1, 3))))),
)

#: A DECLARED BLINDED BRANCH THAT IS AN EXACT POVM AND VIOLATES
#: Eq. eq:branchprobeweight. THE TWO CONDITIONS ARE INDEPENDENT AND THIS IS THE
#: WITNESS: `blinding_model_ill_formed` does NOT fire, and the probe-expectation
#: entry is refused `constraint_without_certificate` instead.
TOL2_BRANCH_FAIL: tuple[tuple[tuple[str, str], Matrix], ...] = (
    (("y0", "t0"), diag_matrix((F(1, 2), F(1, 3)))),
    (("y1", "t0"), diag_matrix((F(1, 4), F(1, 4)))),
    (("y0", "t1"), diag_matrix((F(1, 8), F(1, 4)))),
    (("y1", "t1"), diag_matrix((F(1, 8), F(1, 6)))),
)


@dataclass(frozen=True)
class BranchProbeWeightCase:
    """One declaration of the blinded branches, and the certificate decision.

    ``per_setting_sums`` freezes ``sum_y M_((y,t)|bl1)`` at each ``t``, which is
    the left-hand side of Eq. ``eq:branchprobeweight``; the condition is that it
    equal ``q_t 1_C`` EXACTLY.
    """

    case_id: str
    claims: tuple[str, ...]
    branch: tuple[tuple[tuple[str, str], Matrix], ...] | None
    per_setting_sums: tuple[tuple[str, Matrix], ...]
    branch_is_exact_povm: bool
    satisfies_branchprobeweight: bool
    certificate_discharged: bool
    reason: str
    #: The eps_op values at which the decision is asserted to be the same one.
    decided_identically_at: tuple[F, ...]
    labels: tuple[str, ...]
    derivation: str


BRANCH_PROBE_WEIGHT_CASES: tuple[BranchProbeWeightCase, ...] = (
    BranchProbeWeightCase(
        case_id="TOL2-branchprobe-pass",
        claims=("PR9", "PR11", "PR13"),
        branch=TOL2_BRANCH_PASS,
        per_setting_sums=(
            ("t0", diag_matrix((F(2, 3), F(2, 3)))),
            ("t1", diag_matrix((F(1, 3), F(1, 3)))),
        ),
        branch_is_exact_povm=True,
        satisfies_branchprobeweight=True,
        certificate_discharged=True,
        reason="",
        decided_identically_at=(F(0), F(1, 100)),
        labels=(
            "eq:branchprobeweight",
            "rem:unsound",
            "eq:probebranchsum",
            "cor:tolentries",
        ),
        derivation="""\
A DECLARED BLINDED BRANCH MEETING Eq. eq:branchprobeweight. The branch is
    M_((y0,t0)|bl1) = q_t0 |+><+| = [[1/3, 1/3], [1/3, 1/3]] ,
    M_((y1,t0)|bl1) = q_t0 (1 - |+><+|) = [[1/3, -1/3], [-1/3, 1/3]] ,
    M_((y0,t1)|bl1) = q_t1 diag(1, 0) = diag(1/3, 0) ,
    M_((y1,t1)|bl1) = q_t1 diag(0, 1) = diag(0, 1/3) .
EACH ELEMENT IS POSITIVE SEMIDEFINITE: |+><+| and 1 - |+><+| are orthogonal
rank-one projectors, diag(1,0) and diag(0,1) are projectors, and q_t > 0.
THE SUM OVER V IS 1_C: (2/3)(|+><+| + 1 - |+><+|) + (1/3)(diag(1,0) +
diag(0,1)) = (2/3)1 + (1/3)1 = 1. So the branch is an EXACT POVM and
`blinding_model_ill_formed` does not fire.

Eq. eq:branchprobeweight, sum_y M_((y,t)|b) = q_t 1_C for every blinded b and
every t:
    t0: (2/3)|+><+| + (2/3)(1 - |+><+|) = (2/3) 1_2 = q_t0 1_C  ,
    t1: (1/3)diag(1,0) + (1/3)diag(0,1) = (1/3) 1_2 = q_t1 1_C  .
BOTH HOLD EXACTLY, so the certificate for O^ = sum_y F_(y,t) is DISCHARGED and
the entry may be emitted on the licensed route.

M_((y0,t0)|bl1) IS NOT BLOCK DIAGONAL AT THE CUTOFF -- its (0,1) entry is 1/3 --
AND THAT IS DELIBERATE. Definition def:blindmodel (c) requires block-diagonality
of the UNBLINDED branch only, and Section 4.13's block-structure row "checks
{M_{v|nb}} ALONE". A branch can therefore satisfy eq:branchprobeweight while
having no photon-number structure at all, which is why the condition is stated
as an operator identity and not as a block condition.

THE DECISION IS THE SAME AT eps_op = 0 AND AT eps_op = 1/100. Section 4.13:
"The identity eq:branchprobeweight is THE EXACT ONE AT EVERY eps_op, INCLUDING
eps_op > 0: a declared blinded branch lies OUTSIDE Assumption A-OPTOL and is
EXACT DECLARED DATA by its clause (b), so the condition is decidable on the
declaration AND IS WEAKENED BY NO TOLERANCE."

WHAT THAT BUYS, quantitatively: Eq. eq:starprobeexact, and through it the
smallness of delta_t. "THERE IS THEREFORE NO BLINDED CONTRIBUTION TO THE SHIFT
AT ALL, WHICH IS WHAT NARROWING THE TOLERANCE TO THE RECEIVER BLOCKS BUYS
HERE." See TOL2-entry-probe-t0.""",
    ),
    BranchProbeWeightCase(
        case_id="TOL2-branchprobe-fail-exact-povm",
        claims=("PR9", "PR11", "PR13"),
        branch=TOL2_BRANCH_FAIL,
        per_setting_sums=(
            ("t0", diag_matrix((F(3, 4), F(7, 12)))),
            ("t1", diag_matrix((F(1, 4), F(5, 12)))),
        ),
        branch_is_exact_povm=True,
        satisfies_branchprobeweight=False,
        certificate_discharged=False,
        reason="constraint_without_certificate",
        decided_identically_at=(F(0), F(1, 100)),
        labels=("eq:branchprobeweight", "rem:unsound", "eq:probebranchsum"),
        derivation="""\
THE DISCRIMINATING CASE. This declared branch IS AN EXACT POVM and VIOLATES
Eq. eq:branchprobeweight, so the two conditions are shown to be independent and
the two refusal reasons cannot be conflated.
    M_((y0,t0)|bl1) = diag(1/2, 1/3) ,  M_((y1,t0)|bl1) = diag(1/4, 1/4) ,
    M_((y0,t1)|bl1) = diag(1/8, 1/4) ,  M_((y1,t1)|bl1) = diag(1/8, 1/6) .
EXACT POVM: every element is diagonal with non-negative entries, and
    sum_V = diag(1/2 + 1/4 + 1/8 + 1/8, 1/3 + 1/4 + 1/4 + 1/6)
          = diag(1, 4/12 + 3/12 + 3/12 + 2/12) = diag(1, 1) = 1_C ,
so `blinding_model_ill_formed` DOES NOT FIRE.

Eq. eq:branchprobeweight FAILS AT BOTH SETTINGS:
    t0: sum_y = diag(1/2 + 1/4, 1/3 + 1/4) = diag(3/4, 7/12) ,
        and q_t0 1_C = diag(2/3, 2/3) ;  3/4 != 2/3 .
    t1: sum_y = diag(1/8 + 1/8, 1/4 + 1/6) = diag(1/4, 5/12) ,
        and q_t1 1_C = diag(1/3, 1/3) ;  1/4 != 1/3 .
The defect is diag(1/12, -1/12) at t0 and diag(-1/12, 1/12) at t1, summing to
zero -- WHICH IS WHY THE BRANCH IS STILL A POVM. Weight has been moved BETWEEN
the t-blocks, which the POVM condition cannot see and eq:branchprobeweight can.

CONSEQUENCE: the probe-expectation entry O^ = sum_y F_(y,t) IS REFUSED
`constraint_without_certificate`, at EVERY eps_op. Section 4.13, verbatim: "it
is discharged when EVERY blinded mode has a DECLARED branch POVM and
eq:branchprobeweight holds for that b at EVERY declared t, AND REFUSED
OTHERWISE -- an UNDECLARED blinded branch, a branch MISSING AN ELEMENT at a
declared joint outcome, and A BRANCH VIOLATING eq:branchprobeweight ARE ALL
REFUSALS, UNDER THE SAME REASON."

WHY REFUSING IS THE ONLY SOUND ANSWER. Remark rem:unsound: emitting the entry
here "would impose tr[sum_y F_(y,t) sigma] = q_t on states THE BLINDED BRANCH
CAN REACH AND FOR WHICH IT IS FALSE -- the security break this remark is
about". By Eq. eq:probebranchsum the physical sum is
sum_b (sum_y M_((y,t)|b)) (x) N_b, and with this branch the bl1 term is not
q_t 1_C (x) N_bl1, so Eq. eq:probeidentity fails.

THIS IS THE F-5-01 NARROWING MADE CHECKABLE. The 0.1.3 registry's
PROBE22-licence-identity and PROBE22-cert-identity quote the availability
sentence WITHOUT this condition; both are marked superseded for that reading.
Note that on PROBE22 itself, where |Blmode| = 1, "the condition is VACUOUS and
the certificate is discharged by Lemma lem:linear (ii) alone", so their
NUMERICAL values stand.""",
    ),
    BranchProbeWeightCase(
        case_id="TOL2-branchprobe-undeclared-branch",
        claims=("PR9", "PR11"),
        branch=None,
        per_setting_sums=(),
        branch_is_exact_povm=False,
        satisfies_branchprobeweight=False,
        certificate_discharged=False,
        reason="constraint_without_certificate",
        decided_identically_at=(F(0), F(1, 100)),
        labels=("eq:branchprobeweight", "rem:unsound", "def:blindmodel", "ass:blind"),
        derivation="""\
AN UNDECLARED BLINDED BRANCH. Blmode = {nb, bl1} and no branch POVM is declared
for bl1. Definition def:blindmodel (d) and Assumption A-BLIND permit exactly
that -- "nothing is assumed about it, AND IT MAY BE UNDECLARED" -- so the
DECLARATION is well formed and `blinding_model_ill_formed` does not fire on this
ground.

THE PROBE-EXPECTATION ENTRY IS NONETHELESS REFUSED
`constraint_without_certificate`. Section 4.13 lists the undeclared branch first
among the three refusals under that reason, and Remark rem:unsound gives the
reason: "WHERE IT FAILS, OR WHERE A BLINDED BRANCH IS UNDECLARED,
eq:probeidentity MAY STILL HOLD OF THE DEVICE, BUT NOTHING DECLARED ESTABLISHES
IT, and Section 4.13 REFUSES RATHER THAN ASSUMING IT."

A DECLARATION CAN THEREFORE BE ADMITTED AS A BLINDING MODEL AND STILL BE UNABLE
TO CARRY THIS ENTRY. The two decisions are separate rows with separate reasons,
and this case pins the separation from the third side: exact POVM + satisfies
(TOL2-branchprobe-pass), exact POVM + violates
(TOL2-branchprobe-fail-exact-povm), and not declared at all (here).

DECIDED IDENTICALLY AT EVERY eps_op: a tolerance on the receiver blocks cannot
supply a branch that was never declared.""",
    ),
)


# ---------------------------------------------------------------------------
#  The high-photon slot row (F-4-08) and the slot guarantee through prop:route
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SlotValidationCase:
    """One declared strengthening slot, and the two rows that look at it.

    ``slot_row_admits`` is the NEW row (``high_photon_slot_ill_formed``) and
    ``total_weight_row_admits`` is the OLD one
    (``total_weight_not_below_one``). The whole point of F-4-08 is the case
    where the second admits and the first refuses.
    """

    case_id: str
    claims: tuple[str, ...]
    #: The declared slot as (bounded letter, p_i) pairs.
    slot: tuple[tuple[str, F], ...]
    #: r_min,i per bounded letter, from the declared R^cg.
    r_min: tuple[tuple[str, F], ...]
    #: The routed weights of Eq. eq:weightroute, in the declared order of V.
    routed_weights: tuple[tuple[tuple[str, str], F], ...]
    routed_total: F
    slot_row_admits: bool
    total_weight_row_admits: bool
    reason: str
    labels: tuple[str, ...]
    derivation: str


SLOT_VALIDATION_CASES: tuple[SlotValidationCase, ...] = (
    SlotValidationCase(
        case_id="TOL2-slot-wellformed",
        claims=("PR6", "PR12", "PR13"),
        slot=(("y0", F(1, 10)),),
        r_min=(("y0", F(1, 5)),),
        routed_weights=TOL2_ROUTED_WEIGHTS,
        routed_total=F(7, 25),
        slot_row_admits=True,
        total_weight_row_admits=True,
        reason="",
        labels=("prop:route", "eq:weightroute", "eq:absorbing", "prop:slotvalid"),
        derivation="""\
THE WELL-FORMED SLOT, AND THE ROUTE THROUGH Proposition prop:route. One entry,
whose bounded set is exactly the fibre cg^{-1}(y0) and whose letter is absorbing
(R^cg_{y0|y0} = 1), with p_1 = 1/10.
    SLOT ROW: p_1 = 1/10 >= 0 and sum_i p_i = 1/10 <= 1.  ADMITS.
    ROUTE, Eq. eq:weightroute, with r_min,0 = min_{y' != y0} R^cg_{y0|y'} = 1/5:
      (1 - r_min,0) p_1 + r_min,0 = (4/5)(1/10) + 1/5 = 4/50 + 10/50 = 14/50 ,
      p_(y0,t0) = q_t0 * 14/50 = (2/3)(14/50) = 28/150 = 14/75 ,
      p_(y0,t1) = q_t1 * 14/50 = (1/3)(14/50) = 14/150 = 7/75 ,
      p_(y1,t) = 0 for both t, y1 not being a bounded letter.
    TOTAL-WEIGHT ROW: every p_v >= 0 and p = 14/75 + 7/75 = 21/75 = 7/25 < 1.
    ADMITS.

THE DARK COUNTS SHARPEN THE BOUND HERE: 14/50 > 1/10 = p_1, the improvement
coming from r_min,0 = 1/5 and not from optics -- which is the reading Section
1.4 gives for judging the family-wide-optical-bound escalation trigger not to
fire ("the improvement factor comes from THE DECLARED STOCHASTIC MATRIX R^cg AND
NOT FROM OPTICS").

THESE ROUTED WEIGHTS ARE COMMON TO THE DECLARED AND THE STARRED MODEL. Theorem
thm:tolerance (i)'s proof: the starred family satisfies the slot guarantee at
the declared (O_i, p_i), "WHENCE THE ROUTED WEIGHTS eq:weightroute ARE THE
DECLARED (p_v) FOR THE STARRED FAMILY AS WELL, THOSE BEING COMPUTED FROM
DECLARED SCALARS ALONE". So a positive eps_op does not move a single number in
this case.""",
    ),
    SlotValidationCase(
        case_id="TOL2-slot-negative-masked",
        claims=("PR6", "PR12"),
        slot=(("y0", F(-1, 10)),),
        r_min=(("y0", F(1, 5)),),
        routed_weights=(
            (("y0", "t0"), F(2, 25)),
            (("y1", "t0"), F(0)),
            (("y0", "t1"), F(1, 25)),
            (("y1", "t1"), F(0)),
        ),
        routed_total=F(3, 25),
        slot_row_admits=False,
        total_weight_row_admits=True,
        reason="high_photon_slot_ill_formed",
        labels=("prop:route", "eq:weightroute", "cor:oneabsorbing", "ass:recv"),
        derivation="""\
THE CASE F-4-08 EXISTS FOR, AND THE WHOLE REASON THE SLOT ROW IS NOT THE
TOTAL-WEIGHT ROW. A negative declared p_1 = -1/10, WITH r_min,0 = 1/5 > 0.
    ROUTE: (1 - 1/5)(-1/10) + 1/5 = -4/50 + 10/50 = 3/25 ,
      p_(y0,t0) = (2/3)(3/25) = 6/75 = 2/25 ,
      p_(y0,t1) = (1/3)(3/25) = 3/75 = 1/25 ,
      p = 2/25 + 1/25 = 3/25 .
    TOTAL-WEIGHT ROW: every routed p_v >= 0 and p = 3/25 < 1.  IT ADMITS.
    SLOT ROW: p_1 = -1/10 < 0.  IT REFUSES `high_photon_slot_ill_formed`.

THE NEGATIVE WEIGHT IS INVISIBLE DOWNSTREAM. Section 2.1, verbatim: "THAT ROW IS
NOT THE TOTAL-WEIGHT ROW: the latter tests the ROUTED weights p = sum_v p_v of
eq:weightroute, WHICH EQUAL sum_i p_i ONLY WHEN EVERY r_min,i = 0, so A NEGATIVE
p_i CAN BE MASKED THERE WHENEVER r_min,i > 0." Here sum_i p_i = -1/10 and the
routed total is +3/25: the two have OPPOSITE SIGNS, so no test on the routed
weights can recover the defect.

THE DIRECTION, and it is why the refusal is about the supplier's guarantee
rather than about safety. Section 4.13: "Such a declaration is NOT A SECURITY
BREAK -- THE ROUTED BOUND AT p_i < 0 IS WEAKER THAN AT p_i = 0 -- but it
CONTRADICTS THE SUPPLIER'S OWN SLOT GUARANTEE (Assumption A-RECV) and is REFUSED
RATHER THAN CONSUMED." Checkable here: at p_1 = 0 the route gives
(4/5)(0) + 1/5 = 1/5 = 5/25, and 3/25 < 5/25, so the p_1 = -1/10 declaration
routes to a STRICTLY SMALLER -- hence weaker -- certified weight.

WHY r_min,0 > 0 IS AVAILABLE AT ALL: Corollary cor:oneabsorbing makes a positive
r_min,i possible ONLY AT r = 1, and TOL2 declares exactly one slot entry. At
r >= 2 every r_min,i = 0 and the two rows agree -- which is why a fixture with
two entries could not exhibit the masking.""",
    ),
    SlotValidationCase(
        case_id="TOL2-slot-sum-exceeds-one",
        claims=("PR6", "PR12"),
        slot=(("y0", F(3, 5)), ("y1", F(3, 5))),
        r_min=(("y0", F(0)), ("y1", F(0))),
        routed_weights=(
            (("y0", "t0"), F(2, 5)),
            (("y1", "t0"), F(2, 5)),
            (("y0", "t1"), F(1, 5)),
            (("y1", "t1"), F(1, 5)),
        ),
        routed_total=F(6, 5),
        slot_row_admits=False,
        total_weight_row_admits=False,
        reason="high_photon_slot_ill_formed",
        labels=("prop:route", "eq:weightroute", "cor:oneabsorbing", "prop:slotvalid"),
        derivation="""\
THE SECOND HALF OF THE SLOT ROW: sum_i p_i <= 1. Two declared entries at
p_1 = p_2 = 3/5, so sum_i p_i = 6/5 > 1 and the row REFUSES.

AT r = 2, EVERY r_min,i = 0 BY COROLLARY cor:oneabsorbing -- "a positive
r_min,i can occur ONLY AT r = 1" -- so Eq. eq:weightroute degenerates to the
un-improved p_(y_i,t) = q_t p_i:
    p_(y0,t0) = (2/3)(3/5) = 2/5 ,   p_(y1,t0) = (2/3)(3/5) = 2/5 ,
    p_(y0,t1) = (1/3)(3/5) = 1/5 ,   p_(y1,t1) = (1/3)(3/5) = 1/5 ,
    p = 2/5 + 2/5 + 1/5 + 1/5 = 6/5 = sum_i p_i .
THE TWO ROWS THEREFORE AGREE HERE and both refuse -- which is exactly what the
contract predicts: "the two agree ONLY WHEN EVERY r_min,i = 0".

THIS CASE IS FROZEN BESIDE TOL2-slot-negative-masked so that the pair shows both
sides of the relationship: at r = 1 with r_min > 0 the rows can disagree, and at
r >= 2 they cannot. AN IMPLEMENTATION THAT ROUTED THE SLOT ROW THROUGH THE
TOTAL-WEIGHT ROW WOULD PASS THIS CASE AND FAIL THE PREVIOUS ONE.

THE UPSTREAM AUTHORITY for both halves is Assumption A-RECV, which imports
receiver-povm Def. def:slot "with Prop. prop:slotvalid for p_i >= 0,
sum_i p_i <= 1". This module VALIDATES what it consumes rather than assuming the
supplier validated it -- "and is REFUSED RATHER THAN CONSUMED".""",
    ),
)


# ---------------------------------------------------------------------------
#  CR-1: the carried_operators default is Eq. eq:blindtransport's set
# ---------------------------------------------------------------------------

#: SECTION 2.1, `carried_operators`, AS 0.2.0 STATES IT: "EXACTLY THE SET
#: Eq. eq:blindtransport TRANSPORTS -- the two cutoff projectors Pi_{nb,<=N} and
#: Pi_{nb,flag} of the UNBLINDED branch, together with the branch projector Pi_b
#: for each blinded b in Blmode \\ {nb}; THAT IS 2 + (|Blmode| - 1) OPERATORS,
#: NOT TWO PER BRANCH."
#:
#: THE DISCRIMINATOR, as (|Blmode|, contract count, the 0.1.3 phrasing's count).
#: THE TWO AGREE EXACTLY AT |Blmode| = 1, which is why a degenerate fixture
#: cannot decide the question and why the |Blmode| >= 2 rows are frozen.
CARRIED_DEFAULT_COUNT_CASES: tuple[tuple[int, int, int], ...] = (
    (1, 2, 2),
    (2, 3, 4),
    (3, 4, 6),
    (4, 5, 8),
)

CARRIED_DEFAULT_SET: dict[str, object] = {
    "case_id": "CR1-carried-default",
    "claims": ("PR9", "PR11"),
    "blinding_modes": ("nb", "bl1"),
    "operators": ("Pi_nb_leq", "Pi_nb_flag", "Pi_bl1"),
    "count": 3,
    "count_formula": "2 + (|Blmode| - 1)",
    "count_not_this": "2 * |Blmode|",
    "certificate": (">=", F(0)),
    "certificate_unchanged_at_every_eps_op": True,
    "labels": (
        "eq:blindtransport",
        "thm:blinding",
        "eq:blindtarget",
        "cor:tolentries",
        "rem:paddednotemitted",
    ),
    "derivation": """\
CR-1, CLOSED BY THE 0.2.0 AMENDMENT. The 0.1.3 band ROUTED this as a change
request rather than reinterpreting it, and froze eq:blindtransport's set as the
operative one; the amendment rules that "the `carried_operators`
default is eq:blindtransport's set" and Section 2.1 now says so. THE FROZEN
VALUE IS UNCHANGED; what changed is that the contract now states it.

THE SET AT |Blmode| = 2, Eq. eq:blindtransport:
    Lambda-dagger(Pi_{nb,<=N})  = Pi_{<=N} (x) N_nb ,
    Lambda-dagger(Pi_{nb,flag}) = Pi_{>N}  (x) N_nb ,
    Lambda-dagger(Pi_bl1)       = 1_C      (x) N_bl1 ,
THREE operators, all with positive pull-backs, hence all with the trivial
certificate (relation >=, c = 0).

WHY NOT FOUR. Under the UNPADDED target of Eq. eq:blindtarget a blinded branch
"contributes its flag block AND NO PRESERVED BLOCK" (Remark
rem:paddednotemitted), so Pi_{bl1,<=N} DOES NOT EXIST and cannot be carried.
Section 2.1, verbatim: "Version 0.1.3 wrote 'the two cutoff projectors
Pi_{<=N}, Pi_flag per branch'. On the UNPADDED target eq:blindtarget A BLINDED
BRANCH CARRIES NO PRESERVED BLOCK, so Pi_{bl_i,<=N} DOES NOT EXIST and THE TWO
READINGS AGREE ONLY AT |Blmode| = 1; Theorem thm:blinding (ii) fixes the
operative set and this row now names it."

THE CERTIFICATE IS UNCHANGED AT EVERY eps_op, and that is now a stated fact
rather than an inference: Section 2.1, "THAT c = 0 IS UNCHANGED AT EVERY eps_op,
these operators being exact sector projectors (Cor. cor:tolentries (iii))". See
TOL2-entry-default-carried.

interface.yaml RETIRES the 0.1.3 open implementation choice 8 that recorded the
ambiguity, and records the retirement under
`retired_open_implementation_choices` rather than deleting it.""",
}


# ---------------------------------------------------------------------------
#  CR-B1: subsystem_order, y fastest and t slowest, at one consuming site
# ---------------------------------------------------------------------------

#: SECTION 2.5 `subsystem_order` AT 0.2.0, AT THE `wpfss_data` CONSUMING SITE.
#: The convention names four sites -- the flag basis of eq:blindtarget, the flag
#: sectors of eq:sectors, the `wpfss_data` weights of Section 2.3, and the
#: alphabet-agreement rule of Section 4.13 -- and this case pins the third,
#: which is the one that carries NUMBERS and therefore discriminates.
SUBSYSTEM_ORDER_CASE: dict[str, object] = {
    "case_id": "CRB1-subsystem-order-wpfss",
    "claims": ("PR6", "PR9", "PR12"),
    "alphabet_y": ("y0", "y1"),
    "alphabet_t": ("t0", "t1"),
    "declared_order": TOL2_V,
    "foil_order": TOL2_V_T_FASTEST_NOT_THE_CONTRACT_ORDER,
    "consuming_site": "the `wpfss_data` weights of Section 2.3",
    "weights_in_declared_order": TOL2_ROUTED_WEIGHTS,
    "weights_in_foil_order": (
        (("y0", "t0"), F(14, 75)),
        (("y0", "t1"), F(7, 75)),
        (("y1", "t0"), F(0)),
        (("y1", "t1"), F(0)),
    ),
    "refusal_reason_on_disagreement": "alphabet_or_order_mismatch",
    "labels": ("eq:blindtarget", "eq:sectors", "prop:route", "eq:weightroute"),
    "derivation": """\
CR-B1, CLOSED BY THE 0.2.0 AMENDMENT
("y-fastest, as frozen"). Section 2.5 `subsystem_order` now reads: "THE FLAG
BASIS IS IN THE DECLARED ORDER OF V = Y x T, WHICH IS THE ORDER IN WHICH y
VARIES FASTEST AND t SLOWEST: writing Y = {y_1, ..., y_|Y|} and
T = {t_1, ..., t_|T|} in their declared orders, the flag basis is
|(y_1,t_1)>, ..., |(y_|Y|,t_1)>, |(y_1,t_2)>, ..., |(y_|Y|,t_2)>, ...
EQUIVALENTLY, V IS ENUMERATED AS T-BLOCKS OF Y-RUNS. Version 0.1.3 wrote 'with Y
MAJOR', WHICH ADMITS BOTH GROUPINGS; THAT PHRASE IS REPLACED HERE and the
grouping just displayed is THE ONLY ONE THIS CONTRACT MEANS."

THE DECLARED ORDER ON TOL2:  (y0,t0), (y1,t0), (y0,t1), (y1,t1) .
THE FOIL, t FASTEST:         (y0,t0), (y0,t1), (y1,t0), (y1,t1) .
They agree at positions 1 and 4 and DIFFER AT POSITIONS 2 AND 3, which is the
smallest alphabet on which they can differ at all: at |Y| = 1 or |T| = 1 the two
coincide.

THE DISCRIMINATION IS NUMERICAL, NOT MERELY NOTATIONAL, and that is why the
`wpfss_data` site is the one frozen. The routed weights of Eq. eq:weightroute
are non-zero only at the bounded letter y0:
    DECLARED ORDER: (14/75, 0, 7/75, 0) ,
    FOIL ORDER:     (14/75, 7/75, 0, 0) .
An implementation emitting the weight VECTOR in the foil order attaches 7/75 --
the t1 weight of the BOUNDED letter -- to the position the declared order gives
(y1, t0), an UNBOUNDED letter whose certified weight is 0. That is an emitted
number in the wrong slot, and Eq. eq:certweights would be asserted where nothing
was certified.

WHY NO LATER CHECK CATCHES IT: both vectors have the same multiset of entries
and the same total p = 7/25 < 1, so the total-weight row admits either. The
refusal that exists for it is `alphabet_or_order_mismatch`, and Section 2.5
adds that the order "is VALIDATED against the product set Y x T AND AGAINST THIS
GROUPING, and NEVER CONSTRUCTED IN PLACE OF A MISSING DECLARATION".

THE 0.1.3 FROZEN VALUE STANDS AND IS NOT SUPERSEDED. PROBE22_V was already
frozen in the y-fastest grouping, which is why the human's ruling reads "as
frozen"; only the 0.1.3 comment wording "Y MAJOR" is superseded, and a comment
carries no expected value. The sector list of BLIND3_SHAPE is likewise already
in this grouping.""",
}


# ---------------------------------------------------------------------------
#  The 0.2.0 interface vocabulary
# ---------------------------------------------------------------------------
#
#  THE 0.1.3 TUPLES ABOVE ARE NOT EDITED. They are marked superseded in
#  ``SUPERSESSIONS`` and the 0.2.0 vocabulary is frozen beside them, so that a
#  reader can see both and run B can retire the old ones deliberately.

#: Section 2.1 at 0.2.0: SEVENTEEN keys, 7 + 5 + 5. The request group gains
#: `operator_tolerance`, which is the LAST row of its tabular.
INPUT_KEYS_0_2_0: tuple[str, ...] = (
    "receiver_artifact",
    "photon_blocks",
    "high_photon_bounds",
    "bound_quantifier_domain",
    "dark_count_channel",
    "outcome_coarse_graining",
    "bound_evaluation",
    "probe_declaration",
    "detection_alphabet",
    "photon_cutoff",
    "blinding_model",
    "source_mode",
    "link_declarations",
    "route",
    "carried_operators",
    "requested_assurance",
    "operator_tolerance",
)

#: Section 2.3 at 0.2.0: EIGHTEEN keys. `operator_tolerance_record` sits
#: immediately before `mathematical_spec_version` in the final tabular.
OUTPUT_KEYS_0_2_0: tuple[str, ...] = (
    "source_descriptor",
    "target_descriptor",
    "target_povm",
    "outcome_correspondence",
    "squashing_channel",
    "exact_identity",
    "transported_operators",
    "reachable_set_statement",
    "constraint_list",
    "attack_set_license",
    "wpfss_data",
    "douglas_data",
    "reduction_chain",
    "status",
    "verification_report",
    "assumption_ledger",
    "operator_tolerance_record",
    "mathematical_spec_version",
)

#: Section 4.13 at 0.2.0, BOTH NEW STRINGS, VERBATIM: 26 strings over 24 rows.
#: Section 1.1: "Refusal reasons added: TWO, 24 -> 26 ... NONE REMOVED, AND NONE
#: INVENTED WHERE AN EXISTING ONE CARRIES THE REFUSAL."
REFUSAL_REASONS_ADDED_0_2_0: tuple[str, ...] = (
    "declaration_outside_tolerance",
    "high_photon_slot_ill_formed",
)

#: THE FULL 26-STRING VOCABULARY, in the contract's own order: 0.1.3's
#: twenty-four with the two new strings inserted at the rows that carry them --
#: `declaration_outside_tolerance` after `no_block_structure` (first tabular,
#: fourth row) and `high_photon_slot_ill_formed` after
#: `blinding_model_ill_formed` (third tabular, first row).
REFUSAL_REASONS_0_2_0: tuple[str, ...] = (
    "receiver_spec_not_accepted",
    "cutoff_mismatch",
    "no_block_structure",
    "declaration_outside_tolerance",
    "bound_set_not_a_fibre",
    "dark_counts_do_not_descend",
    "bounded_letter_not_absorbing",
    "total_weight_not_below_one",
    "blinding_model_ill_formed",
    "high_photon_slot_ill_formed",
    "probe_weights_ill_formed",
    "declared_relation_impossible",
    "chain_ill_formed",
    "source_link_after_receiver_link",
    "link_kind_deferred",
    "approximate_squashing_unsupported",
    "device_family_unsupported",
    "constraint_without_certificate",
    "data_dependent_constant",
    "licence_missing",
    "licence_without_constraints",
    "route_not_single_valued",
    "constraint_channel_mismatch",
    "alphabet_or_order_mismatch",
    "post_processing_order_violated",
    "unsound_constraint_requested",
)

#: THE ROW COUNT AT 0.2.0: 24, from 21. THREE ROWS ARE ADDED and only TWO
#: strings, because the licensed-route Hermiticity row carries the EXISTING
#: `constraint_without_certificate`. The two counts do not determine each other
#: and are frozen separately.
FAIL_CLOSED_ROW_COUNT_0_2_0: int = 24
FAIL_CLOSED_ROWS_ADDED_0_2_0: tuple[tuple[str, str], ...] = (
    ("the declared-tolerance row", "declaration_outside_tolerance"),
    ("the high-photon slot row", "high_photon_slot_ill_formed"),
    ("the licensed-route exact-Hermiticity row", "constraint_without_certificate"),
)

#: Section 2.5 at 0.2.0: THIRTEEN bullets, from twelve. `exact_arithmetic` is
#: added and `fail_closed` gains the no-repair sentence; `subsystem_order`,
#: `povm_index_convention` and the artifact binding are restated.
CONVENTIONS_0_2_0: dict[str, str] = {
    "log_base": "2",
    "entropy_units": "bits",
    "entropy_variant": "sandwiched-renyi",
    "arrow": "up",
    "alpha_domain": "(1, 2)",
    "test_statistics_model": "output_state",
    "round_homogeneity": "required",
    "composition_order": "later links act later; source stage before receiver stage",
    "post_processing_order": "dark counts, then coarse-graining, then joint alphabet",
    "subsystem_order": "A before Q; nb first; flag basis with y FASTEST and t SLOWEST",
    "povm_index_convention": "comma = joint, bar = conditional; q_t at step 2",
    "block_restriction": "blk M is a BLOCK, not a compression",
    "fail_closed": "refusal with a reason and NO artifact; NEVER A REPAIR",
    "exact_arithmetic": "required, on the rows named",
    "artifact_bindings.mathematical_spec_version": "proof-reductions@0.2.0",
}

#: Section 5 at 0.2.0: A-OPTOL, the tenth row, with the Supports set Remark
#: rem:tolscope classifies. Frozen as a single row beside the 0.1.3 ledger,
#: which is marked superseded rather than edited.
ASSUMPTION_ROW_OPTOL = AssumptionRow(
    assumption_id="A-OPTOL",
    machine_key="operator_tolerance_hypothesis",
    supports=("PR6", "PR9", "PR11", "PR12", "PR13"),
    never_verifiable=True,
    violation_is_unsafe=True,
    note="There is NO exact POVM family within eps_op of the declared receiver "
    "blocks, so NOTHING THE ARTIFACT ASSERTS IS A STATEMENT ABOUT ANY "
    "MEASUREMENT -- a security break in the unsafe direction, OF THE SAME KIND "
    "AND SEVERITY AS A VIOLATION OF A-RECV. At eps_op = 0 it is NOT vacuous: it "
    "is then the substantive statement that the declared blocks are the "
    "physical ones, which 0.1.3 relied on without stating it.",
)

#: The 0.2.0 ledger: the 0.1.3 nine with A-DIM's Supports widened to PR1-PR13
#: and A-OPTOL appended in the contract's own order (after A-BLIND, before
#: A-PROBE). Built from the 0.1.3 tuple rather than restated, so the two cannot
#: drift on the eight rows the amendment does not touch.
ASSUMPTION_LEDGER_0_2_0: tuple[AssumptionRow, ...] = (
    AssumptionRow(
        assumption_id="A-DIM",
        machine_key="finite_target_and_side_registers",
        supports=(*ASSUMPTION_LEDGER[0].supports, "PR13"),
        never_verifiable=ASSUMPTION_LEDGER[0].never_verifiable,
        violation_is_unsafe=ASSUMPTION_LEDGER[0].violation_is_unsafe,
        note=ASSUMPTION_LEDGER[0].note
        + " AT 0.2.0 the Supports range widens from PR1-PR12 to PR1-PR13; "
        "Section 1.1: 'NO OTHER Supports RANGE IS TOUCHED'.",
    ),
    ASSUMPTION_LEDGER[1],
    ASSUMPTION_LEDGER[2],
    ASSUMPTION_LEDGER[3],
    ASSUMPTION_LEDGER[4],
    ASSUMPTION_ROW_OPTOL,
    ASSUMPTION_LEDGER[5],
    ASSUMPTION_LEDGER[6],
    ASSUMPTION_LEDGER[7],
    ASSUMPTION_LEDGER[8],
)

#: Section 5 preamble at 0.2.0: THREE assumptions this module "NAMES AND CAN
#: NEVER VERIFY", from two.
NEVER_VERIFIED_0_2_0: tuple[str, ...] = ("A-RECV", "A-BLIND", "A-OPTOL")

#: Section 1.2 at 0.2.0: THIRTEEN claims, all `newly-derived`.
CLAIM_IDS_0_2_0: tuple[str, ...] = tuple(f"PR{i}" for i in range(1, 14))

#: Section 2.5, `artifact_bindings`, and Section 2.3's last row at 0.2.0.
SPEC_VERSION_0_2_0: str = "proof-reductions@0.2.0"


# ---------------------------------------------------------------------------
#  exact_arithmetic: cases a float comparison gets wrong
# ---------------------------------------------------------------------------
#
#  Section 2.5, `exact_arithmetic`: "NO ROW OF THIS MODULE IS DECIDED BY A
#  FLOATING-POINT COMPARISON, with or without a declared tolerance." These two
#  cases are the ones where that sentence has teeth: the exact answer and the
#  answer a float comparison can return DIFFER.
#
#  NOTE ALSO that eps_op = 1/100 and dcf = 6/5 are NOT DYADIC RATIONALS, so a
#  binary floating-point representation of the fixture is inexact before any
#  comparison is made. That is a property of the whole of TOL2 and is stated
#  once here rather than repeated on every case.

TOL_FLOAT_SENSITIVE_CASES: tuple[tuple[str, str, bool, str], ...] = (
    (
        "TOL-threshold-form-boundary-admit",
        "||A - A-dagger|| = 1/50 and the threshold 2 eps_op = 1/50 are EQUAL, so "
        "the exact decision is ADMIT (Eq. eq:normtest's inequality is <=, and "
        "eq:psdtest's is >=, so W = 0 is accepted).",
        True,
        "Neither 1/100 nor 1/50 is a dyadic rational, so both the entries and "
        "the threshold are represented inexactly in IEEE-754 binary. The exact "
        "test computes delta^2 1 - Z-dagger Z = 0 and accepts; a float "
        "evaluation computes a quantity whose sign is decided by the "
        "accumulated rounding of two inexact squares, and can return a value "
        "of either sign. The decision therefore FLIPS TO A REFUSAL for some "
        "orderings of the arithmetic -- a declaration the contract admits, "
        "refused. Lemma lem:exactpsd is stated so that this cannot happen: "
        "'finitely many field operations and sign comparisons in F: NO "
        "ROUNDING, NO THRESHOLD, AND NO EIGENVALUE IS COMPUTED'.",
    ),
    (
        "TOL-posdef-refuse-leading-minors-pass",
        "X = [[0, 0], [0, -1/50]] has e_1 = -1/50 < 0, so the exact decision is "
        "REFUSE -- while both LEADING principal minors are exactly 0.",
        False,
        "The exact zero in the (1,1) entry is A CANCELLATION: it is "
        "-1/100 + 1/100, formed from the declared block entry and the declared "
        "eps_op, NEITHER OF WHICH IS DYADIC. In floating point the difference "
        "is a small non-zero quantity of either sign, so the 1 x 1 leading "
        "minor and the determinant become small non-zero numbers and a "
        "threshold-based test admits or refuses according to the threshold "
        "chosen -- which is precisely the 'threshold' Section 2.5 forbids. The "
        "exact test needs no threshold: e_1 = -1/50 is unambiguously negative.",
    ),
)


# ===========================================================================
#  SUPERSESSION -- what the 0.2.0 amendment invalidates, marked and not deleted
# ===========================================================================
#
#  RUN A DOES NOT DELETE OR EDIT A FROZEN 0.1.3 VALUE. Every case the amendment
#  invalidates is MARKED here and, where the case is a dataclass instance, on
#  the instance itself through its ``superseded_by`` field. Run B retires or
#  rewrites the marked cases deliberately, with the replacement named; an
#  expected value that is simply wrong would be a FINDING, and none of these is
#  -- every marked value was correct at 0.1.3 and remains correct in the scope
#  the mark records.
#
#  WHAT "SUPERSEDED" MEANS HERE, precisely, because it is not "wrong":
#    * a CONSTANT case is superseded when the amendment shifts the emitted
#      constant at eps_op > 0. The frozen value REMAINS THE CONSTANT AT
#      eps_op = 0 -- "At eps_op = 0 every eta_v vanishes, EACH SHIFTED CONSTANT
#      IS THE 0.1.3 CONSTANT" (cor:tolentries) -- so the mark records a NARROWED
#      SCOPE and names the 0.2.0 replacement, not an error.
#    * a VOCABULARY case is superseded when the key set or the string set
#      changed. There the 0.1.3 tuple is no longer the contract's list at all,
#      and the replacement is the ``*_0_2_0`` tuple frozen above.
#    * a READING case is superseded when the derivation records a reading the
#      amendment narrowed (F-5-01). The numbers stand; the sentence does not.
#
#  THE INTEGRITY INVARIANT run B must clear is stated in
#  ``test_proof_reductions_registry.py``: a marked case must not remain asserted
#  UNMARKED by a golden test. At the freeze that invariant FAILS BY
#  CONSTRUCTION, because the code has not changed yet and the golden suite still
#  asserts the 0.1.3 constants; that failure IS the freeze's signal and is
#  reported rather than suppressed.


@dataclass(frozen=True)
class Supersession:
    """One 0.1.3 frozen object the 0.2.0 amendment invalidates, in whole or in scope."""

    #: The registry symbol, and the ``case_id`` where the symbol is a container.
    symbol: str
    case_id: str
    superseded_by: str
    #: What kind of invalidation: constant / vocabulary / reading / input-shape.
    kind: str
    #: The contract element that makes the change.
    contract_site: str
    #: The 0.2.0 object that replaces it.
    replacement: tuple[str, ...]
    #: True when the frozen value is still correct at eps_op = 0.
    still_valid_at_zero_tolerance: bool
    note: str


SUPERSESSIONS: tuple[Supersession, ...] = (
    Supersession(
        symbol="LICENCE_TRUSTED",
        case_id="WP3-licence-trusted",
        superseded_by="0.2.0",
        kind="constant",
        contract_site=(
            "Corollary cor:tolentries (i), Eq. eq:tolfss; Section 2.3 "
            "`constraint_list` clause (a); Corollary cor:fssinstance, whose "
            "scope paragraph 0.2.0 adds"
        ),
        replacement=("TOL_ENTRY_FLAG",),
        still_valid_at_zero_tolerance=True,
        note="The flag-sector entry at c = 0. Corollary cor:fssinstance now "
        "says of that constant: 'Its c = 0 is the constant for the family the "
        "target is built from, which is what the emitted artifact carries WHEN "
        "NO OPERATOR TOLERANCE IS DECLARED. Under a declared eps_op > 0 the "
        "target is built from numbers that are only eta_o-close to that family, "
        "and THE CONSTANT THIS MODULE THEN EMITS IS -eta_o, NOT 0.' The frozen "
        "F(0) is therefore the eps_op = 0 constant and nothing else; emitting "
        "it at eps_op > 0 is what Section 2.3 calls UNSAFE.",
    ),
    Supersession(
        symbol="LICENCE_UNTRUSTED",
        case_id="WP3-licence-untrusted",
        superseded_by="0.2.0",
        kind="constant",
        contract_site=(
            "Corollary cor:tolentries (i), Eq. eq:tolfss; Section 2.3 "
            "`constraint_list` clause (a)"
        ),
        replacement=("TOL_ENTRY_FLAG",),
        still_valid_at_zero_tolerance=True,
        note="The same entry typed in untrusted-source mode. THE TYPING IS NOT "
        "WHAT CHANGES -- Definition def:licensed is untouched by the amendment "
        "-- ONLY THE CONSTANT. Both source modes are superseded together and by "
        "the same clause, because cor:tolentries (i) is stated on the entry and "
        "not on the mode.",
    ),
    Supersession(
        symbol="LICENCE_PROBE_IDENTITY",
        case_id="PROBE22-licence-identity",
        superseded_by="0.2.0",
        kind="constant and reading",
        contract_site=(
            "Corollary cor:tolentries (ii), Eqs. eq:tolprobe and "
            "eq:starprobeexact; Section 2.3 `constraint_list` clause (b); "
            "Remark rem:unsound as narrowed (F-5-01); Section 4.13's "
            "constraint-certificate row"
        ),
        replacement=(
            "TOL_ENTRY_PROBE_T0",
            "TOL_ENTRY_PROBE_T1",
            "TOL2-branchprobe-pass",
            "TOL2-branchprobe-fail-exact-povm",
        ),
        still_valid_at_zero_tolerance=True,
        note="TWO INDEPENDENT SUPERSESSIONS IN ONE CASE. (1) CONSTANT: the "
        "single equality entry (O^, =, q_t) at c = 2/3 is replaced at "
        "eps_op > 0 by the PAIR (O^, >=, q_t - delta_t), (O^, <=, q_t + "
        "delta_t); the equality is the eps_op = 0 form and 'the pair of (ii) "
        "COLLAPSES to the equality entry' there. (2) READING (F-5-01): the "
        "derivation quotes Section 2.3's pre-narrowing sentence that the entry "
        "'remains AVAILABLE ON REQUEST' with no mention of the condition "
        "Eq. eq:branchprobeweight that 0.2.0 restricts it to. THE NUMBER "
        "STANDS ON PROBE22 EITHER WAY, because PROBE22 declares no blinded "
        "branch and 'at |Blmode| = 1 the condition is VACUOUS and the "
        "certificate is discharged by Lemma lem:linear (ii) alone' -- but the "
        "SENTENCE no longer states the rule, and a reader taking it as the rule "
        "would emit the entry on a declaration that must be refused.",
    ),
    Supersession(
        symbol="CERT_IDENTITY_PROBE",
        case_id="PROBE22-cert-identity",
        superseded_by="0.2.0",
        kind="reading",
        contract_site=(
            "Remark rem:unsound as narrowed (F-5-01); Section 4.13's "
            "constraint-certificate row; Eq. eq:branchprobeweight"
        ),
        replacement=(
            "TOL2-branchprobe-pass",
            "TOL2-branchprobe-fail-exact-povm",
            "TOL2-branchprobe-undeclared-branch",
        ),
        still_valid_at_zero_tolerance=True,
        note="THE PULL-BACK COMPUTATION IS UNTOUCHED and is correct at every "
        "eps_op for the family it is read on: Lambda^WP-dagger(sum_y F_(y,t0)) "
        "= (2/3) 1_B. WHAT IS SUPERSEDED IS THE CLOSING PARAGRAPH'S READING, "
        "which quotes the availability sentence without the condition "
        "eq:branchprobeweight. 0.2.0 makes the certificate 'DECIDED FROM "
        "DECLARED DATA: discharged when EVERY blinded mode has a DECLARED "
        "branch POVM and eq:branchprobeweight holds for that b at EVERY "
        "declared t, AND REFUSED OTHERWISE'. At eps_op > 0 there is a second, "
        "smaller point: the identity is then asserted of the STARRED family "
        "(Eq. eq:starprobeexact) and not of the declared numbers, whose "
        "pull-back differs by at most delta_t.",
    ),
    Supersession(
        symbol="CERT_TWO_SECTOR",
        case_id="WP3-cert-two-sector",
        superseded_by="0.2.0",
        kind="constant",
        contract_site=(
            "Corollary cor:tolentries (iv), Eq. eq:tolgeneral; Section 2.3 "
            "`constraint_list` clause (d); Remark rem:published, closing "
            "sentence as amended"
        ),
        replacement=("TOL_ENTRY_TWO_SECTOR",),
        still_valid_at_zero_tolerance=True,
        note="The a > 0 entry at c = 0. Remark rem:published now closes: 'The "
        "admissible object is the operator entry eq:two-sector-entry with relation >= "
        "and c = 0 -- AT A DECLARED eps_op > 0, WITH c = -eta_e INSTEAD, by "
        "Corollary cor:tolentries (iv).' THE OPERATOR, THE PULL-BACK AND THE "
        "COMPARISON WITH THE a = 0 ENTRY ARE ALL UNCHANGED; the frozen matrices "
        "stand. Only the emitted constant is scoped to eps_op = 0.",
    ),
    Supersession(
        symbol="ENCODED_CONSTRAINT",
        case_id="WP3-encoded",
        superseded_by="0.2.0",
        kind="scope",
        contract_site="Remark rem:tolscope, the `encoded`-route bullet",
        replacement=("TOL2_TARGETPOSCOMP", "TOL2_TOLERANCE_RECORD"),
        still_valid_at_zero_tolerance=True,
        note="THE ONE PLACE WHERE A TOLERANCE-INDUCED RESIDUAL HAS NO ENTRY OF "
        "ITS OWN TO SIT IN, and the contract says so rather than leaving it to "
        "be discovered. Proposition prop:chain (iii)'s F^WP_v >= p_v Pi_flag is "
        "what the `encoded` route encodes INSTEAD OF a constraint entry. 'OF "
        "THE STARRED TARGET THAT REMAINS EXACTLY TRUE; OF THE EMITTED NUMBERS "
        "IT HOLDS ONLY WITHIN eta_v... AND BECAUSE THE ROUTE EMITS NO CList, NO "
        "FIELD OF THE ARTIFACT CARRIES THAT RESIDUAL: it is visible only "
        "through operator_tolerance_record's eta_v and the target_povm row's "
        "qualification.' The frozen differences stand exactly at eps_op = 0 and "
        "are eta_v-approximate above it; there is no 0.2.0 case that replaces "
        "them entry for entry, because there is no entry -- the replacements "
        "named are where the residual IS visible.",
    ),
    Supersession(
        symbol="REFUSAL_CASES",
        case_id="R-block-structure",
        superseded_by="0.2.0",
        kind="input shape",
        contract_site=(
            "Section 4.13, first tabular, third row, as restated; Section 2.5 "
            "`exact_arithmetic`, which calls that row 'a TYPE check'"
        ),
        replacement=("TOL_ROW_CASES", "TOL-scope-receiver-block-admit"),
        still_valid_at_zero_tolerance=False,
        note="THE ONLY MARK WHOSE FROZEN INPUT NO LONGER TYPE-CHECKS. The case "
        "declares 'M_{a|nb} with a non-zero (0,1) entry, i.e. an UNBLINDED "
        "branch element WITH COHERENCE BETWEEN THE m = 0 BLOCK AND THE "
        "ABOVE-CUTOFF ONE'. 0.2.0 restates the row as the STRUCTURAL HALF ONLY "
        "and says why: 'BLOCK DIAGONALITY BELOW THE CUTOFF IS CARRIED BY THE "
        "DECLARED TYPE -- the datum is a per-m list (Section 2.1), SO THERE IS "
        "NO OFF-BLOCK ENTRY TO TEST -- WHICH IS WHY THIS ROW IS THE STRUCTURAL "
        "HALF ONLY. THE NUMERICAL HALF IS THE NEXT ROW.' A declaration cannot "
        "present the frozen datum at all: an inter-block coherence has no slot "
        "in a per-m list of blocks. What the row now refuses is a MISSING or "
        "MIS-DIMENSIONED block, or one over the wrong alphabet or order. "
        "still_valid_at_zero_tolerance is FALSE because the invalidation is of "
        "the INPUT SHAPE and does not depend on eps_op.",
    ),
    Supersession(
        symbol="INPUT_KEYS",
        case_id="INPUT_KEYS",
        superseded_by="0.2.0",
        kind="vocabulary",
        contract_site="Section 2.1, request-group tabular, last row",
        replacement=("INPUT_KEYS_0_2_0",),
        still_valid_at_zero_tolerance=False,
        note="SIXTEEN keys, 7 + 5 + 4. At 0.2.0 the request group gains "
        "`operator_tolerance` and the count is SEVENTEEN, 7 + 5 + 5. The "
        "sixteen names are unchanged and in the same order; the tuple is "
        "superseded because it is no longer the contract's list, not because "
        "any member of it is wrong.",
    ),
    Supersession(
        symbol="OUTPUT_KEYS",
        case_id="OUTPUT_KEYS",
        superseded_by="0.2.0",
        kind="vocabulary",
        contract_site="Section 2.3, final tabular, second-to-last row",
        replacement=("OUTPUT_KEYS_0_2_0",),
        still_valid_at_zero_tolerance=False,
        note="SEVENTEEN keys, with `operator_tolerance_record` ABSENT. At 0.2.0 "
        "it is EIGHTEEN, the new key sitting immediately before "
        "`mathematical_spec_version`. NOTE THAT THE KEY IS PRESENT IN THE "
        "PAYLOAD EVEN AT eps_op = 0, carrying `null`: the presence RULE is "
        "about the VALUE ('null when no tolerance is declared'), not about the "
        "key, so an artifact emitted with no tolerance still has eighteen keys.",
    ),
    Supersession(
        symbol="REFUSAL_REASONS",
        case_id="REFUSAL_REASONS",
        superseded_by="0.2.0",
        kind="vocabulary",
        contract_site="Section 4.13, four tabulars; Section 1.1",
        replacement=("REFUSAL_REASONS_0_2_0", "REFUSAL_REASONS_ADDED_0_2_0"),
        still_valid_at_zero_tolerance=False,
        note="THE 24-STRING VOCABULARY, over 21 rows. At 0.2.0 it is 26 over "
        "24. 'NONE REMOVED, AND NONE INVENTED WHERE AN EXISTING ONE CARRIES THE "
        "REFUSAL' (Section 1.1), so the twenty-four are a PREFIX of the "
        "twenty-six in the sense of set inclusion and the supersession is a "
        "widening. THE THIRD ADDED ROW CARRIES NO NEW STRING -- the "
        "licensed-route Hermiticity row is emitted under the existing "
        "`constraint_without_certificate` -- which is why the row count moves "
        "by three and the string count by two.",
    ),
    Supersession(
        symbol="CONVENTIONS",
        case_id="CONVENTIONS",
        superseded_by="0.2.0",
        kind="vocabulary",
        contract_site=(
            "Section 2.5, bullets 8, 9, 11, 12 and 13 (subsystem_order, "
            "povm_index_convention, fail_closed, exact_arithmetic, "
            "artifact_bindings)"
        ),
        replacement=("CONVENTIONS_0_2_0",),
        still_valid_at_zero_tolerance=False,
        note="FOUR CHANGES IN ONE MAPPING. (1) `exact_arithmetic` is ADDED "
        "(bullet count 12 -> 13). (2) `subsystem_order` is REWRITTEN: 'with Y "
        "MAJOR' becomes 'y VARIES FASTEST AND t SLOWEST' (CR-B1); the 0.1.3 "
        "VALUES the registry froze are already in that grouping, so no number "
        "moves. (3) `povm_index_convention` says STEP 2 rather than step 3 "
        "(O-1). (4) `artifact_bindings.mathematical_spec_version` moves from "
        "proof-reductions@0.1.3 to @0.2.0. `fail_closed` additionally gains the "
        "no-repair sentence, which the summary string now carries.",
    ),
    Supersession(
        symbol="ASSUMPTION_LEDGER",
        case_id="ASSUMPTION_LEDGER",
        superseded_by="0.2.0",
        kind="vocabulary",
        contract_site=(
            "Assumption ass:optol and its ledger row; the A-DIM ledger row; "
            "Section 5 preamble; Section 1.1"
        ),
        replacement=(
            "ASSUMPTION_LEDGER_0_2_0",
            "ASSUMPTION_ROW_OPTOL",
            "NEVER_VERIFIED_0_2_0",
        ),
        still_valid_at_zero_tolerance=False,
        note="NINE ROWS, WITH A-DIM SUPPORTING PR1-PR12. At 0.2.0 there are TEN "
        "and A-DIM supports PR1-PR13. 'The ledger row for A-DIM widens from "
        "PR1-PR12 to PR1-PR13; NO OTHER Supports RANGE IS TOUCHED' (Section "
        "1.1), so the other eight rows are reused verbatim in "
        "ASSUMPTION_LEDGER_0_2_0 rather than restated -- the two tuples cannot "
        "drift on them. The never-verified set also moves from two to three.",
    ),
)

#: THE SET OF MARKED SYMBOLS, for the integrity invariant. A golden test that
#: still asserts one of these UNMARKED is asserting a 0.1.3 expectation against
#: 0.2.0 evidence, which is exactly what the freeze exists to make visible.
SUPERSEDED_SYMBOLS: tuple[str, ...] = tuple(
    dict.fromkeys(record.symbol for record in SUPERSESSIONS)
)

#: WHAT IS DELIBERATELY *NOT* MARKED, with the reason. Recorded because a
#: reader's first question about a supersession list is what it leaves out.
NOT_SUPERSEDED_AND_WHY: tuple[tuple[str, str], ...] = (
    (
        "PROBE22_V",
        "ALREADY IN THE 0.2.0 GROUPING. The ruling was "
        "'y-fastest, AS FROZEN', and PROBE22_V is (y0,t0), (y1,t0), (y0,t1), "
        "(y1,t1) -- y fastest. Only the 0.1.3 COMMENT wording 'Y MAJOR' is "
        "superseded, and a comment carries no expected value. Marking a "
        "correct value would make the list mean less, not more. Same for "
        "BLIND3_SHAPE.sectors, whose flag sectors are in the same grouping.",
    ),
    (
        "R-blinding-model",
        "THE ROW IS EXPLICITLY UNCHANGED. Section 4.13: 'UNCHANGED FROM VERSION "
        "0.1.3, AND THE DECLARED TOLERANCE DOES NOT REACH THIS ROW.' The 0.2.0 "
        "cases TOL-scope-blinded-branch-refuse and "
        "TOL-scope-register-povm-refuse ADD the at-every-eps_op quantifier that "
        "0.1.3 had no way to state; they do not replace the 0.1.3 case.",
    ),
    (
        "R-no-certificate",
        "STILL VALID AT EVERY eps_op. Its declared entry O^ = F^FSS_v0 - "
        "(1/2)Pi_flag has a pull-back with a negative eigenvalue -1/4, which no "
        "shift of size eta_v repairs, and the operator IS of eq:tolgeneral's "
        "form, so the refusal is decided the same way at 0.2.0. The two NEW "
        "carriers of `constraint_without_certificate` -- the licensed-route "
        "Hermiticity row and a requested operator outside eq:tolgeneral's form "
        "-- are frozen as new cases beside it.",
    ),
    (
        "the remaining 24 entries of REFUSAL_CASES",
        "EVERY ONE IS DECIDED IDENTICALLY AT eps_op = 0, which is what "
        "`operator_tolerance` ABSENT means, and none of their declared data is "
        "a receiver block whose row the tolerance moves. Section 2.1: 'ABSENT "
        "IS eps_op = 0, AND AT eps_op = 0 EVERY RULE OF SECTION 4.13 IS THE "
        "EXACT TEST VERSION 0.1.3 APPLIED.' R-block-structure is the single "
        "exception and it is marked.",
    ),
    (
        "the whole of groups PR-A, PR-B, PR-D, PR-E, PR-G, PR-H, PR-J and PR-M",
        "THE CLAIMS THEY PIN ARE UNTOUCHED BY THE AMENDMENT. Remark "
        "rem:tolscope: 'PR1, PR2, PR3, PR4, PR5, PR8, PR10 -- UNTOUCHED. None "
        "of them reads a declared number and none of them asserts anything "
        "about the emitted artifact.' Group PR-M's weight route is computed "
        "from declared SCALARS, which Remark rem:tolboundary puts outside the "
        "tolerance, and Theorem thm:tolerance (i) records that the routed "
        "weights are therefore the same in both models.",
    ),
)


# ---------------------------------------------------------------------------
#  Change-request candidates cleared by reading, for the 0.2.0 delta
# ---------------------------------------------------------------------------
#
#  As at 0.1.3: for each item run A could not resolve from Section 2 alone,
#  either THE READING THE TEXT FIXES with its locator, or the item is ROUTED.
#  NOTHING BELOW IS DECIDED HERE.

CHANGE_REQUEST_CANDIDATES_0_2_0: tuple[tuple[str, str, str], ...] = (
    (
        "(a) the pinned supplier version in A-RECV and Section 1.4",
        "ROUTED -- observation, non-blocking",
        """\
contract.tex 0.2.0 names `receiver-povm 0.1.3` in three places: A-RECV's four
imported-claim locators, Section 1.4's tier-chain sentence ("accepted at
0.1.3"), and Section 1.4's family-wide-bound escalation reading. The supplier's
own STATUS.yaml records contract_version 0.2.0, accepted at G3, with 0.1.3 superseded.
THE READING TAKEN: interface.yaml MIRRORS THE CONTRACT and writes 0.1.3.
"This section IS the interface", and the version string is the contract's, not
the implementer's to advance.
NOT BLOCKING, AND NO LOCATOR IS BROKEN: every label A-RECV names -- thm:click-povm,
thm:coarse-graining, thm:emitted-bound, def:slot, prop:slotvalid, def:darkadm, thm:dark-counts,
thm:conditional-povm, thm:channel-block-diagonal, and the equations eq:pmcstatement, eq:darkimprove,
eq:darkpmc -- exists exactly once in the accepted receiver-povm 0.2.0 text, so
each import resolves by label at either version.
DECISION NEEDED: whether the pin should be advanced, and if so whether the
supplier's amendment changes anything at those locators. Scope is a version
string in three named places on this reading, hence PATCH LEVEL -- but the level
is the human's call at G3, and whether the supplier's 0.2.0 changes what is
imported is a question for a drafter and a verifier, not for this run.""",
    ),
    (
        "(b) the emitted POVM at eps_op > 0, and what the consumer does with it",
        "FIXED BY THE HUMAN AND BY THE CONTRACT -- nothing frozen about the consumer",
        """\
READING, and it is the contract's own and the rulings': at eps_op > 0
the emitted POVM is A DECLARATION OF THE STARRED FAMILY {F*_v} TO ACCURACY
eta_v, and Section 2.3's `target_povm` row states in as many words that "WHAT
THE CONSUMING DECLARATION DOES WITH THAT IS THE CONSUMER'S RULE AND NOT THIS
MODULE'S". meat-core 0.4.0 validates ass:decl (iii) on the numbers it receives
and REFUSES them if they fail, "SO A POSITIVE TOLERANCE IS EMITTED HERE AND MAY
BE REFUSED THERE"; the consumer-side tolerance amendment (meat-core 0.5.0) is
"NAMED HERE AND NOT DECIDED HERE", as item (b) of "SIGNED WITH THE TEXT".
NOTHING ABOUT THE CONSUMER IS FROZEN IN THIS BAND -- no meat-core case, no
composition case, no key-length comparison. Theorem thm:tolerance (v) is why the
last of those could not be frozen even if it were wanted.""",
    ),
    (
        "(c) which ordered field carries the exact arithmetic",
        "RESOLVED as an open implementation choice -- recorded, not decided",
        """\
Definition def:tolerance fixes "an ordered field F with Q subset F subset R" and
Remark def:substrate declines to name one, with the reason: "the choice CANNOT
CHANGE ANY DECISION -- every rule below is a sign comparison in F of a polynomial
with integer coefficients in the declared entries and in eps_op, SO ANY TWO
ADMISSIBLE FIELDS CONTAINING THOSE ENTRIES RETURN THE SAME ANSWER. IEEE-754
binary floating-point values are dyadic rationals, so F = Q ALWAYS SUFFICES."
THIS REGISTRY'S EXACT GAUSSIAN RATIONALS ARE A CHOICE ABOUT THE EVIDENCE, NOT
ABOUT THE CODE, exactly as at 0.1.3. interface.yaml records the field as open
implementation choice 10 of 12. WHAT IS NOT OPEN and is frozen: a declaration
whose entries are not exactly representable in the chosen field is REFUSED
`declaration_outside_tolerance` RATHER THAN ROUNDED INTO IT.""",
    ),
    (
        "(d) how the PSD predicate is computed",
        "RESOLVED as an open implementation choice -- recorded, not decided",
        """\
Remark rem:psdalgorithm: "Lemma lem:exactpsd states WHAT is decided. HOW IS AN
IMPLEMENTATION MATTER", and it names three conforming procedures and one that is
never necessary. THE BOUND ON THE LATITUDE IS EXPLICIT AND IS FROZEN: "ANY
PROCEDURE THAT DECIDES eq:psdtest EXACTLY IN F CONFORMS TO THIS CONTRACT; ONE
THAT DECIDES IT APPROXIMATELY DOES NOT, WHATEVER ITS ERROR BOUND."
WHAT THIS REGISTRY FREEZES IS THE PREDICATE AND ITS ANSWER, not an algorithm:
every ToleranceRowCase carries the principal-minor sums e_k and the resulting
decision, so any conforming procedure reproduces the decision and a
leading-minor test does not (TOL-posdef-refuse-leading-minors-pass).
interface.yaml records the algorithm as open implementation choice 11 of 12.""",
    ),
    (
        "(e) the serialization of operator_tolerance_record, entry by entry",
        "RESOLVED as an open implementation choice -- recorded, not decided",
        """\
Section 2.3 fixes the record's CONTENT exhaustively and its PRESENCE rule exactly
("present exactly when the request declares eps_op > 0; null otherwise"), and
fixes NO SCHEMA for "the shift applied to every emitted constraint constant,
ENTRY BY ENTRY". Since Definition def:link gives a link NO IDENTIFIER
(interface.yaml open choice 6), the keying of "entry by entry" is code's.
TOL2_TOLERANCE_RECORD freezes the shifts KEYED BY THIS REGISTRY'S OWN CASE IDS,
which is a choice about the evidence and not about the wire. The machine form of
"the norm it is stated in" is likewise unfixed -- the contract names the operator
norm in prose and gives no enum. interface.yaml records both as open
implementation choice 12 of 12.""",
    ),
    (
        "(f) the nb branch under the tolerance, if declared rather than derived",
        "RESOLVED as part of the 0.1.3 open choice 7 -- recorded, not decided",
        """\
A-OPTOL covers the declared receiver BLOCKS; its clause (b) puts declared BRANCH
POVMs OUTSIDE the tolerance. On the reading Definition def:blindmodel (c) and
Proposition prop:route describe -- {M_{v|nb}} DERIVED from `receiver_artifact`
through Section 2.2's three steps -- the two never disagree, and that is the
reading this registry's TOL2_JOINT_NB freezes. On the alternative reading, where
an nb entry read from `blinding_model` is authoritative, THE SAME OPERATORS WOULD
SIT OUTSIDE THE TOLERANCE while the ones derived from `photon_blocks` sit inside
it. The contract states no rule for that case and NAMES NO REFUSAL REASON for a
disagreement, exactly as at 0.1.3. NOT DECIDED HERE, and inventing a
twenty-seventh reason string for it would decide it.""",
    ),
    (
        "(g) whether a positive tolerance may ever be emitted as certified_outer",
        "RESOLVED from the text -- it may not",
        """\
A READING WORTH RECORDING BECAUSE 0.2.0 IS THE VERSION AT WHICH IT COULD BE
TAKEN. Section 2.3's `status` row is qualified at eps_op > 0 but its VOCABULARY
is unchanged and version 1 emits `exact` or refuses: "`certified_outer` and
`exploratory_numeric` are NEVER EMITTED by version 1". Section 1.3's
approximate-squashing deferral docks at `certified_outer` and Theorem
thm:tolerance (v) says the tolerance does NOT close it: "converting an operator
perturbation of the target into a security penalty IS EXACTLY THE
APPROXIMATE-SQUASHING DEFERRAL, for which this contract has NO THEOREM AND
VERSION 1 EMITS NO STATUS". So a declared tolerance is not an approximate
relation, does not trip `approximate_squashing_unsupported`, and does not license
a second status value.""",
    ),
)
# ===========================================================================
#  Group PR-P (BAND 3) -- the column-stochasticity row, contract 0.3.0
# ===========================================================================
#
#  BAND 3 IS THE 0.2.0-to-0.3.0 AMENDMENT. Everything from this
#  banner onward was derived BY HAND from the accepted ``contract.tex`` 0.3.0
#  (sha256 144e8f9aa1b8eccafdd1a2241fbc27afccc81df13739e0d6cd955b4aa8007f3b)
#  before any code changed.
#
#  WHAT THE AMENDMENT ADDS, AND IT IS ALL THAT IS FROZEN HERE: ONE fail-closed
#  row and ONE refusal-reason string. Section ``sec:failclosed`` decides,
#  exactly, that the declared dark-count matrix R is COLUMN-STOCHASTIC --
#  ``R_{S|S'} >= 0`` for every entry and ``sum_S R_{S|S'} = 1`` for every column
#  -- and refuses otherwise under ``dark_counts_not_column_stochastic``. Rows
#  24 -> 25; reasons 26 -> 27; NONE REMOVED. Everything else the amendment does
#  is a PIN (``receiver-povm`` 0.1.3 -> 0.2.0, ``meat-core`` 0.4.0 -> 0.5.0) or
#  prose, and neither moves a number: "No claim is added, none is removed, and
#  no claim statement, constant, construction or emitted number changes"
#  (``sec:amendment030``).
#
#  WHY THE CASES BELOW ARE THE CASES BELOW. The row's whole subtlety is that it
#  does NOT cover, and is not covered by, the descent row beside it. Remark
#  ``rem:darkcompose`` states the boundary in one sentence: "a STRICTLY
#  POSITIVE entry in a (D2)-forbidden position fails monotonicity while leaving
#  column-stochasticity untouched, and a NEGATIVE entry in such a position does
#  the reverse -- it satisfies the monotonicity implication VACUOUSLY and fails
#  non-negativity." Both halves of that sentence are frozen, each as a
#  declaration that ONE row refuses and the other admits. Beside them sit two
#  honest declarations (the regression anchors, one with a non-trivial
#  coarse-graining) and the contract's own example of the defect the row exists
#  for -- "a dark-count matrix whose columns sum to 1 only to within a rounding
#  error" (Remark ``rem:tolboundary``).
#
#  NOTHING HERE IS INVENTED. Every decision below is the answer the two stated
#  predicates return on the frozen entries; no case exercises a rule the
#  contract does not state, and no case decides what a violation "ought" to be
#  refused under -- the contract names the row for each.


@dataclass(frozen=True)
class ColumnStochasticCase:
    """One declared dark-count matrix R, and the two rows that look at it.

    ``column_stochastic_row_admits`` is the NEW row
    (``dark_counts_not_column_stochastic``) and ``descent_row_admits`` is the
    one beside it (``dark_counts_do_not_descend``). The pair is the point: two
    of the cases below are refused by exactly one of them and admitted by the
    other, which is what "neither covers the other" means when it is checkable.
    """

    case_id: str
    claims: tuple[str, ...]
    ports: int
    #: The raw click patterns S subset [K], in the declared order. ``"e"`` is
    #: the empty pattern; ``"12"`` is {1,2}.
    patterns: tuple[str, ...]
    #: The RAW declared R over 2^[K], COLUMN BY COLUMN:
    #: (column pattern, ((row pattern, entry), ...)). This is the object the
    #: new row decides, and the contract says so: "DECIDED ON R, WHICH
    #: SUFFICES".
    raw_matrix: tuple[tuple[str, tuple[tuple[str, F], ...]], ...]
    #: sum_S R_{S|S'} per column, exact -- the row's second subrule.
    column_sums: tuple[tuple[str, F], ...]
    #: The smallest entry anywhere in R, exact -- the row's first subrule.
    min_entry: F
    non_negative: bool
    unit_columns: bool
    column_stochastic_row_admits: bool
    #: The declared coarse-graining, as (pattern, letter) pairs.
    coarse_graining: tuple[tuple[str, str], ...]
    #: The descended matrix R^cg, column by column, in the same shape. The new
    #: row does NOT test it a second time; it is frozen so that the implication
    #: Remark rem:colstoch states can be checked rather than asserted.
    descended_matrix: tuple[tuple[str, tuple[tuple[str, F], ...]], ...]
    descended_is_column_stochastic: bool
    #: The descent row's two halves on the SAME declaration.
    monotone: bool
    descends: bool
    descent_row_admits: bool
    #: The bounded letter, its absorbing entry and its r_min,i.
    bounded_letter: str
    absorbing: bool
    r_min: F
    #: Eq. eq:weightroute at the declared slot p_1 = 1/10 and q = (2/3, 1/3),
    #: and whether the total-weight row admits the result. This is how a case
    #: shows that the refusal did NOT arrive under another row's reason.
    routed_total: F
    total_weight_row_admits: bool
    #: The reason this declaration is refused under, or "" when every row
    #: exercised here admits it.
    reason: str
    labels: tuple[str, ...]
    derivation: str


#: The declared slot, probe weights and cutoff shared by every case in this
#: group, so that the only thing varying between them is R. Section 2.1's
#: `high_photon_bounds` and `probe_declaration`.
COLSTOCH_SLOT_WEIGHT: F = F(1, 10)
COLSTOCH_PROBE_WEIGHTS: tuple[tuple[str, F], ...] = (
    ("t_off", F(2, 3)),
    ("t_on", F(1, 3)),
)

#: THE CANONICAL COARSE-GRAINING of Eq. eq:canonicalcg at K = 2: cg is
#: injective off MC = {S : |S| >= 2} = {{1,2}} and constant on it, so with
#: |MC| = 1 it is a BIJECTION and every fibre is a singleton. RC2 uses it.
COLSTOCH_CG_CANONICAL: tuple[tuple[str, str], ...] = (
    ("e", "y_empty"),
    ("1", "y_1"),
    ("2", "y_2"),
    ("12", "y_mc"),
)

#: A coarse-graining with a FIBRE OF SIZE TWO, so that the descended entry
#: R^cg_{y_d|y'} is a genuine SUM of two entries of R rather than a relabelling.
#: Still total, still surjective, still with cg^{-1}(y_mc) = MC exactly.
COLSTOCH_CG_MERGING: tuple[tuple[str, str], ...] = (
    ("e", "y_0"),
    ("1", "y_d"),
    ("2", "y_d"),
    ("12", "y_mc"),
)


COLSTOCH_CANONICAL_ADMIT = ColumnStochasticCase(
    case_id="CS-canonical-admit",
    claims=("PR6", "PR12"),
    ports=2,
    patterns=("e", "1", "2", "12"),
    raw_matrix=(
        ("e", (("e", F(3, 5)), ("1", F(3, 20)), ("2", F(1, 5)), ("12", F(1, 20)))),
        ("1", (("e", F(0)), ("1", F(3, 4)), ("2", F(0)), ("12", F(1, 4)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(4, 5)), ("12", F(1, 5)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(1)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(0),
    non_negative=True,
    unit_columns=True,
    column_stochastic_row_admits=True,
    coarse_graining=COLSTOCH_CG_CANONICAL,
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(3, 5)),
                ("y_1", F(3, 20)),
                ("y_2", F(1, 5)),
                ("y_mc", F(1, 20)),
            ),
        ),
        (
            "y_1",
            (("y_empty", F(0)), ("y_1", F(3, 4)), ("y_2", F(0)), ("y_mc", F(1, 4))),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(4, 5)), ("y_mc", F(1, 5))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    descended_is_column_stochastic=True,
    monotone=True,
    descends=True,
    descent_row_admits=True,
    bounded_letter="y_mc",
    absorbing=True,
    r_min=F(1, 20),
    routed_total=F(29, 200),
    total_weight_row_admits=True,
    reason="",
    labels=(
        "lem:descent",
        "prop:route",
        "eq:weightroute",
        "eq:absorbing",
        "rem:colstoch",
    ),
    derivation="""\
THE REGRESSION ANCHOR, AND IT IS RC2's DECLARATION READ ONE LEVEL LOWER. Group
PR-M froze RC2 as its DESCENDED matrix R^cg; the new row's subject is the RAW R
over 2^[K], so the raw matrix is frozen here and the descended one beside it.
Under the canonical coarse-graining at K = 2 the two agree entry for entry,
because MC = {{1,2}} is a single pattern and cg is therefore a BIJECTION -- which
is exactly why a second case with a fibre of size two sits below this one.

THE DECLARATION. Independent per-port dark counts with p_dc|1 = 1/5 and
p_dc|2 = 1/4, so R_{S|S'} = 0 unless S' subset S (MONOTONE) and otherwise
R_{S|S'} = prod_{k in S\\S'} p_dc|k prod_{k not in S} (1 - p_dc|k). With
a = 1/5, b = 1/4:
    col e  : ((4/5)(3/4), (1/5)(3/4), (4/5)(1/4), (1/5)(1/4))
             = (3/5, 3/20, 1/5, 1/20) ;
    col 1  : (0, 3/4, 0, 1/4) ;
    col 2  : (0, 0, 4/5, 1/5) ;
    col 12 : (0, 0, 0, 1) .

THE NEW ROW, DECIDED EXACTLY, BOTH SUBRULES:
    NON-NEGATIVITY: the smallest entry anywhere is 0, and 0 >= 0.  ADMITS.
    UNIT COLUMNS: 12/20 + 3/20 + 4/20 + 1/20 = 1 ; 3/4 + 1/4 = 1 ;
      4/5 + 1/5 = 1 ; 1 = 1.  ADMITS.
NEITHER COMPARISON IS AN INSTANCE OF Lemma lem:exactpsd, and the contract says
so: the row is "a SIGN-AND-EQUALITY COMPARISON ON THE DECLARED ENTRIES OF R"
(Section sec:conventions, `exact_arithmetic`, whose enumeration of neighbouring
exact rows grows from two to three at this version).

WHAT THE ROW DOES NOT DO A SECOND TIME. Remark rem:colstoch: the fibres of cg
partition 2^[K], so R^cg_{y|y'} = sum_{S in cg^{-1}(y)} R_{S|S'} >= 0 as a sum
of non-negative entries and sum_y R^cg_{y|y'} = sum_S R_{S|S'} = 1. "Deciding it
on the declared matrix therefore DISCHARGES IT FOR THE DESCENDED ONE, AND NO
SECOND ROW IS STATED." The descended matrix is frozen here so that implication
is checkable; an implementation that adds a row on R^cg has added a rule the
contract does not state.

EVERYTHING ELSE ADMITS, WHICH IS THE POINT OF AN ANCHOR. Monotone and descends
(directly, not via the eq:canonicalcg shortcut, which is checked in full where
it is used); the bounded set is exactly the fibre cg^{-1}(y_mc) = MC; the letter
is absorbing, R^cg_{y_mc|y_mc} = 1; r_min = min(1/20, 1/4, 1/5) = 1/20 over the
columns y' != y_mc; and Eq. eq:weightroute at p_1 = 1/10 gives
(19/20)(1/10) + 1/20 = 29/200, routed to 29/300 and 29/600 and totalling
29/200 < 1. THESE ARE RC2's NUMBERS UNCHANGED: 0.3.0 refuses strictly more and
never less, and no conforming declaration changes hands.""",
)


COLSTOCH_COARSE_ADMIT = ColumnStochasticCase(
    case_id="CS-coarse-admit",
    claims=("PR6", "PR12"),
    ports=2,
    patterns=("e", "1", "2", "12"),
    raw_matrix=(
        (
            "e",
            (("e", F(16, 25)), ("1", F(4, 25)), ("2", F(4, 25)), ("12", F(1, 25))),
        ),
        ("1", (("e", F(0)), ("1", F(4, 5)), ("2", F(0)), ("12", F(1, 5)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(4, 5)), ("12", F(1, 5)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(1)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(0),
    non_negative=True,
    unit_columns=True,
    column_stochastic_row_admits=True,
    coarse_graining=COLSTOCH_CG_MERGING,
    descended_matrix=(
        ("y_0", (("y_0", F(16, 25)), ("y_d", F(8, 25)), ("y_mc", F(1, 25)))),
        ("y_d", (("y_0", F(0)), ("y_d", F(4, 5)), ("y_mc", F(1, 5)))),
        ("y_mc", (("y_0", F(0)), ("y_d", F(0)), ("y_mc", F(1)))),
    ),
    descended_is_column_stochastic=True,
    monotone=True,
    descends=True,
    descent_row_admits=True,
    bounded_letter="y_mc",
    absorbing=True,
    r_min=F(1, 25),
    routed_total=F(17, 125),
    total_weight_row_admits=True,
    reason="",
    labels=("lem:descent", "eq:descend", "prop:route", "rem:colstoch", "rem:fibre"),
    derivation="""\
THE SECOND ANCHOR, AND THE ONE THAT MAKES THE DESCENT IMPLICATION NON-TRIVIAL.
Here cg MERGES the two single-click patterns into one letter, so
cg^{-1}(y_d) = {{1}, {2}} is a FIBRE OF SIZE TWO and the descended entry
R^cg_{y_d|y'} is a genuine SUM of two entries of R. Under the canonical
coarse-graining of the case above, cg is a bijection and the "sum over the
fibre" of Remark rem:colstoch is a sum of one term; here it is not.

THE DECLARATION. Independent per-port dark counts with the SAME probability
p_dc = 1/5 at both ports -- symmetric, which is what makes the two single-click
columns agree and hence what makes R descend through this cg:
    col e  : ((4/5)^2, (1/5)(4/5), (4/5)(1/5), (1/5)^2)
             = (16/25, 4/25, 4/25, 1/25) ;
    col 1  : (0, 4/5, 0, 1/5) ;
    col 2  : (0, 0, 4/5, 1/5) ;
    col 12 : (0, 0, 0, 1) .

THE NEW ROW: every entry >= 0 (smallest is 0), and the columns sum to
16/25 + 4/25 + 4/25 + 1/25 = 25/25 = 1, 4/5 + 1/5 = 1, 4/5 + 1/5 = 1, 1.
ADMITS on both subrules.

DESCENT, TESTED DIRECTLY. P(y|S') = sum_{S in cg^{-1}(y)} R_{S|S'}:
    P(y_0|.)  = ( 16/25 , 0   , 0   , 0 )   over columns e, 1, 2, 12 ;
    P(y_d|.)  = ( 8/25  , 4/5 , 4/5 , 0 )   -- 4/25 + 4/25 = 8/25 in column e ;
    P(y_mc|.) = ( 1/25  , 1/5 , 1/5 , 1 ) .
THE TWO COLUMNS WITH THE SAME cg-IMAGE, namely {1} and {2} with cg-image y_d,
give IDENTICAL values in every row, so R^cg is WELL DEFINED and R descends. (Had
the two ports carried different dark-count probabilities, they would not, and
this declaration would be refused `dark_counts_do_not_descend` -- which is the
DESCENT half of that row, distinct from its monotonicity half.)

AND THE IMPLICATION Remark rem:colstoch STATES IS NON-TRIVIALLY TRUE HERE:
R^cg's y_0-column sums to 16/25 + 8/25 + 1/25 = 25/25 = 1, with the middle term
FORMED BY THE ADDITION the fibre of size two performs. No second row is needed
on R^cg, and none is stated.

THE ROUTE. cg^{-1}(y_mc) = {{1,2}} = MC exactly, so the fibre condition holds;
R^cg_{y_mc|y_mc} = 1, absorbing; r_min = min(1/25, 1/5) = 1/25 over the columns
y' != y_mc, the minimum coming from the EMPTY column, which needs both ports to
fire spuriously. Eq. eq:weightroute at p_1 = 1/10:
    (1 - 1/25)(1/10) + 1/25 = 24/250 + 10/250 = 34/250 = 17/125 ,
routed to (2/3)(17/125) = 34/375 and (1/3)(17/125) = 17/375, total 51/375 =
17/125 < 1.""",
)


COLSTOCH_COLSUM_REFUSE = ColumnStochasticCase(
    case_id="CS-colsum-refuse",
    claims=("PR6", "PR12"),
    ports=2,
    patterns=("e", "1", "2", "12"),
    raw_matrix=(
        ("e", (("e", F(3, 5)), ("1", F(3, 20)), ("2", F(1, 5)), ("12", F(1, 25)))),
        ("1", (("e", F(0)), ("1", F(3, 4)), ("2", F(0)), ("12", F(1, 4)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(4, 5)), ("12", F(1, 5)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(99, 100)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(0),
    non_negative=True,
    unit_columns=False,
    column_stochastic_row_admits=False,
    coarse_graining=COLSTOCH_CG_CANONICAL,
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(3, 5)),
                ("y_1", F(3, 20)),
                ("y_2", F(1, 5)),
                ("y_mc", F(1, 25)),
            ),
        ),
        (
            "y_1",
            (("y_empty", F(0)), ("y_1", F(3, 4)), ("y_2", F(0)), ("y_mc", F(1, 4))),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(4, 5)), ("y_mc", F(1, 5))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    descended_is_column_stochastic=False,
    monotone=True,
    descends=True,
    descent_row_admits=True,
    bounded_letter="y_mc",
    absorbing=True,
    r_min=F(1, 25),
    routed_total=F(17, 125),
    total_weight_row_admits=True,
    reason="dark_counts_not_column_stochastic",
    labels=("rem:tolboundary", "rem:colstoch", "prop:route", "lem:descent"),
    derivation="""\
THE CONTRACT'S OWN EXAMPLE, FROZEN. Remark rem:tolboundary: "a declaration whose
scalar data is only approximately valid -- A DARK-COUNT MATRIX WHOSE COLUMNS SUM
TO 1 ONLY TO WITHIN A ROUNDING ERROR, SAY -- IS STILL REFUSED, NOW BY THE
COLUMN-STOCHASTICITY ROW AND UNDER ITS OWN REASON STRING." The clause after the
comma is what 0.3.0 adds; version 0.2.0's promise stood against a rule that
section did not state.

THE DECLARATION IS CS-canonical-admit WITH ONE ENTRY MOVED, and only one: the
empty column's multiclick entry 1/20 = 5/100 becomes 1/25 = 4/100. Everything
else -- every other entry, the coarse-graining, the slot, the probe weights --
is identical, so the case is a MINIMAL PAIR with the anchor above.
    COLUMN SUM AT e : 60/100 + 15/100 + 20/100 + 4/100 = 99/100 .
THE DEFECT IS EXACTLY 1/100, which is the value eps_op takes throughout group
PR-O. That is deliberate: the tolerance DOES NOT REACH R (Remark
rem:tolboundary; Assumption ass:optol (b) covers the receiver blocks and this is
a declared scalar), so a defect of exactly the declared tolerance's size is
refused all the same, at eps_op = 1/100 as at eps_op = 0.

THE NEW ROW, SUBRULE BY SUBRULE:
    NON-NEGATIVITY: smallest entry 0 >= 0.  ADMITS.
    UNIT COLUMNS: the e column sums to 99/100 != 1.  REFUSES.
REASON `dark_counts_not_column_stochastic`. Note that ONE subrule failing is
enough; the row is a conjunction.

AND NO OTHER ROW CATCHES IT, WHICH IS WHY THE ROW EXISTS. This is the residue
Remark rem:colstoch's third paragraph identifies, and the checkable half is
frozen here:
    MONOTONE: every strictly positive entry sits at S with S' subset S.  ADMITS.
    DESCENDS: cg is a bijection here, so P(y|S') = R_{S_y|S'} depends on S' only
      through cg(S') trivially.  ADMITS.
    FIBRE: cg^{-1}(y_mc) = MC exactly.  ADMITS.
    ABSORBING: R^cg_{y_mc|y_mc} = 1.  ADMITS.
    SLOT: p_1 = 1/10 >= 0 and sum_i p_i = 1/10 <= 1.  ADMITS.
    TOTAL WEIGHT: r_min = min(1/25, 1/4, 1/5) = 1/25, so eq:weightroute gives
      (24/25)(1/10) + 1/25 = 34/250 = 17/125, routed to 34/375 and 17/375,
      total 17/125, which is >= 0 and < 1.  ADMITS.
So the FIRST of the two indirect paths Remark rem:colstoch names -- "any
r_min,i >= 1 makes the i-th summand at least 1 and hence p >= 1... either way
`total_weight_not_below_one`" -- DOES NOT FIRE HERE: r_min = 1/25 is nowhere
near 1. THE SECOND indirect path, Proposition prop:tolrows (iv) read against a
threshold, is a statement about the POST-PROCESSED RECEIVER BLOCKS and not about
R, so whether it fires depends on data this case does not declare; the contract
says the residue is a defect that "at eps_op > 0 neither lifts some r_min,i to 1
nor exceeds that part's tolerance budget", and NOTHING IS FROZEN HERE ABOUT THAT
BUDGET, because deciding it would need declared blocks this case does not carry.
What is frozen is the half that is decidable from R alone.

NOTE WHAT THE DESCENDED MATRIX DOES. R^cg's y_empty column sums to 99/100 as
well -- the defect travels, exactly as Remark rem:colstoch's implication says it
must, which is why deciding on R suffices AND why an implementation that tested
only R^cg would have found the same defect and still had no reason string for
it before 0.3.0.""",
)


COLSTOCH_NEGATIVE_VACUOUS_REFUSE = ColumnStochasticCase(
    case_id="CS-negative-vacuous-refuse",
    claims=("PR6", "PR12"),
    ports=2,
    patterns=("e", "1", "2", "12"),
    raw_matrix=(
        ("e", (("e", F(3, 5)), ("1", F(3, 20)), ("2", F(1, 5)), ("12", F(1, 20)))),
        ("1", (("e", F(-1, 20)), ("1", F(3, 4)), ("2", F(0)), ("12", F(3, 10)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(4, 5)), ("12", F(1, 5)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(1)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(-1, 20),
    non_negative=False,
    unit_columns=True,
    column_stochastic_row_admits=False,
    coarse_graining=COLSTOCH_CG_CANONICAL,
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(3, 5)),
                ("y_1", F(3, 20)),
                ("y_2", F(1, 5)),
                ("y_mc", F(1, 20)),
            ),
        ),
        (
            "y_1",
            (
                ("y_empty", F(-1, 20)),
                ("y_1", F(3, 4)),
                ("y_2", F(0)),
                ("y_mc", F(3, 10)),
            ),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(4, 5)), ("y_mc", F(1, 5))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    descended_is_column_stochastic=False,
    monotone=True,
    descends=True,
    descent_row_admits=True,
    bounded_letter="y_mc",
    absorbing=True,
    r_min=F(1, 20),
    routed_total=F(29, 200),
    total_weight_row_admits=True,
    reason="dark_counts_not_column_stochastic",
    labels=("rem:darkcompose", "rem:colstoch", "def:darkadm", "lem:descent"),
    derivation="""\
THE BOUNDARY, HALF ONE. Remark rem:darkcompose, verbatim: "THE TWO ROWS ARE
NEEDED TOGETHER AND NEITHER COVERS THE OTHER: a strictly positive entry in a
(D2)-forbidden position fails monotonicity while leaving column-stochasticity
untouched, and A NEGATIVE ENTRY IN SUCH A POSITION DOES THE REVERSE -- IT
SATISFIES THE MONOTONICITY IMPLICATION VACUOUSLY AND FAILS NON-NEGATIVITY." The
fail-closed descent row says the same from its own side: "a NEGATIVE entry in a
forbidden position satisfies it vacuously and IS REFUSED BY THE ROW ABOVE
INSTEAD (Rem. rem:colstoch)." This case is that sentence.

THE DECLARATION IS CS-canonical-admit WITH ONE COLUMN REDISTRIBUTED, chosen so
that the UNIT-COLUMN subrule still passes and the refusal is unambiguously on
NON-NEGATIVITY alone:
    col 1 : ( -1/20 , 3/4 , 0 , 3/10 )  instead of ( 0 , 3/4 , 0 , 1/4 ) .
    SUM: -1/20 + 15/20 + 6/20 = 20/20 = 1 .  EXACTLY ONE.
The negative entry sits at row e, column {1}: that is R_{empty | {1}}, and
{1} is NOT a subset of the empty set, so the position is (D2)-FORBIDDEN.

THE NEW ROW:
    NON-NEGATIVITY: the smallest entry is -1/20 < 0.  REFUSES.
    UNIT COLUMNS: 1, 1, 1, 1.  ADMITS.
REASON `dark_counts_not_column_stochastic`.

THE DESCENT ROW ADMITS IT, AND THAT IS THE WHOLE POINT.
    MONOTONICITY is the implication R_{S|S'} > 0 => S' subset S, "that exact
      implication and nothing more". Its only strictly positive entries are, by
      column: e at rows e, 1, 2, 12 (all supersets of the empty set); {1} at
      rows 1 and 12 (both supersets of {1}); {2} at rows 2 and 12; {1,2} at row
      12. The entry -1/20 at (e | 1) is NOT > 0, so the implication is
      VACUOUSLY SATISFIED there even though the position is forbidden.  ADMITS.
    DESCENT: cg is a bijection, so P(y|S') = R_{S_y|S'} depends on S' only
      through cg(S').  ADMITS.
    So the descent row -- monotone AND descends -- ADMITS this declaration
    ENTIRELY, and only the new row catches it.

AND NO OTHER ROW CATCHES IT EITHER: cg^{-1}(y_mc) = MC exactly (fibre);
R^cg_{y_mc|y_mc} = 1 (absorbing); r_min = min(1/20, 3/10, 1/5) = 1/20 over the
columns y' != y_mc, so eq:weightroute gives (19/20)(1/10) + 1/20 = 29/200,
routed to 29/300 and 29/600, total 29/200, which is >= 0 and < 1 (total weight
ADMITS); and the slot p_1 = 1/10 is well formed.

WHAT WAS AT STAKE, AND WHY THIS IS COVERAGE AND NOT SOUNDNESS. At 0.2.0 this
declaration met NO ROW and was consumed. The contract is careful about what that
did and did not mean: "Every result of this contract is proved for an exactly
column-stochastic R and asserts NOTHING WHATEVER about a declaration that is not
one; an out-of-type declaration was never one this contract made a statement
about." So no theorem was ever false; what was missing was the refusal. AT 0.3.0
THIS DECLARATION IS REFUSED, WITH ITS CAUSE NAMED, and it is the one class that
changes hands -- from admitted to refused, the conservative direction.""",
)


COLSTOCH_POSITIVE_FORBIDDEN_REFUSE = ColumnStochasticCase(
    case_id="CS-positive-forbidden-refuse",
    claims=("PR6", "PR12"),
    ports=2,
    patterns=("e", "1", "2", "12"),
    raw_matrix=(
        ("e", (("e", F(3, 5)), ("1", F(3, 20)), ("2", F(1, 5)), ("12", F(1, 20)))),
        ("1", (("e", F(1, 20)), ("1", F(7, 10)), ("2", F(0)), ("12", F(1, 4)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(4, 5)), ("12", F(1, 5)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(1)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(0),
    non_negative=True,
    unit_columns=True,
    column_stochastic_row_admits=True,
    coarse_graining=COLSTOCH_CG_CANONICAL,
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(3, 5)),
                ("y_1", F(3, 20)),
                ("y_2", F(1, 5)),
                ("y_mc", F(1, 20)),
            ),
        ),
        (
            "y_1",
            (
                ("y_empty", F(1, 20)),
                ("y_1", F(7, 10)),
                ("y_2", F(0)),
                ("y_mc", F(1, 4)),
            ),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(4, 5)), ("y_mc", F(1, 5))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    descended_is_column_stochastic=True,
    monotone=False,
    descends=True,
    descent_row_admits=False,
    bounded_letter="y_mc",
    absorbing=True,
    r_min=F(1, 20),
    routed_total=F(29, 200),
    total_weight_row_admits=True,
    reason="dark_counts_do_not_descend",
    labels=("rem:darkcompose", "lem:descent", "def:darkadm", "rem:colstoch"),
    derivation="""\
THE BOUNDARY, HALF TWO, AND THE CASE THAT PROVES THE NEW ROW DID NOT CAPTURE
WHAT BELONGS ELSEWHERE. Remark rem:darkcompose's other half: "A STRICTLY
POSITIVE ENTRY IN A (D2)-FORBIDDEN POSITION FAILS MONOTONICITY WHILE LEAVING
COLUMN-STOCHASTICITY UNTOUCHED."

THE DECLARATION IS CS-canonical-admit WITH ONE COLUMN REDISTRIBUTED, in the
mirror image of the case above:
    col 1 : ( 1/20 , 7/10 , 0 , 1/4 )  instead of ( 0 , 3/4 , 0 , 1/4 ) .
    SUM: 1/20 + 14/20 + 5/20 = 20/20 = 1 ,  and every entry is >= 0.
The moved entry is again at row e, column {1} -- the same (D2)-forbidden
position -- but it is +1/20 rather than -1/20.

THE NEW ROW ADMITS IT, ON BOTH SUBRULES:
    NON-NEGATIVITY: smallest entry 0 >= 0.  ADMITS.
    UNIT COLUMNS: 1, 1, 1, 1.  ADMITS.
So a declaration CAN pass the new row and still be refused, and this is one.

THE DESCENT ROW REFUSES IT, ON ITS MONOTONICITY HALF:
    R_{e | 1} = 1/20 > 0, and {1} is NOT a subset of the empty set. The
    implication R_{S|S'} > 0 => S' subset S therefore FAILS, and it fails
    NON-vacuously because the entry is strictly positive.  REFUSES.
    THE DESCENT HALF, by contrast, holds: cg is a bijection, so P(y|S')
    depends on S' only through cg(S'). The row is a conjunction of the two
    halves under ONE reason string, so the refusal is
    `dark_counts_do_not_descend`, decided on the monotonicity half alone.

AND THE DESCENDED MATRIX IS STILL COLUMN-STOCHASTIC -- 3/5 + 3/20 + 1/5 + 1/20 =
1 and 1/20 + 7/10 + 0 + 1/4 = 1 -- which is what "leaving column-stochasticity
untouched" means, checkably. An implementation that folded the two rows into one
test would emit the WRONG reason string here.

WHY IT MATTERS BEYOND DIAGNOSIS. receiver-povm 0.2.0's Def. def:darkadm calls R
admissible when it is (D1) column-stochastic AND (D2) monotone, and Remark
rem:darkcompose turns the two rows into the statement that "EVERY DECLARATION
THIS MODULE ADMITS IS EXACTLY ADMISSIBLE IN THE SUPPLIER'S SENSE" -- (D1) by the
new row, (D2) by this one. Drop either row and that sentence fails, and with it
the conclusion that r-bar = r_min and that the supplier's eq:darkoverstate terms
are nil as content.""",
)


#: THE FIVE CASES, in the order a reader should meet them: the two anchors, the
#: contract's own defect example, and the two halves of the boundary.
COLSTOCH_CASES: tuple[ColumnStochasticCase, ...] = (
    COLSTOCH_CANONICAL_ADMIT,
    COLSTOCH_COARSE_ADMIT,
    COLSTOCH_COLSUM_REFUSE,
    COLSTOCH_NEGATIVE_VACUOUS_REFUSE,
    COLSTOCH_POSITIVE_FORBIDDEN_REFUSE,
)

#: THE TOLERANCE PROBE. Section sec:failclosed's column-stochasticity row:
#: "DECIDED EXACTLY AT EVERY eps_op in the substrate of Def. def:tolerance: the
#: tolerance does not reach R (Rem. rem:tolboundary) and Lemma lem:exactpsd is
#: NOT INVOKED". So every decision above is INDEPENDENT of the declared
#: tolerance, and the two values probed are the two the rest of this file uses.
#: The 1/100 defect of CS-colsum-refuse is exactly the size of the larger probe,
#: which is what makes the invariance a claim with teeth rather than a truism.
COLSTOCH_TOLERANCE_PROBE: tuple[F, ...] = (F(0), F(1, 100))
COLSTOCH_TOLERANCE_PROBE_NOTE: str = (
    "The row is decided on DECLARED SCALARS, which Remark rem:tolboundary puts "
    "OUTSIDE the tolerance: 'the declared scalars and classical maps -- the "
    "probe weights, the slot weights, the cutoff, the coarse-graining, and the "
    "dark-count matrix R with its COLUMN-STOCHASTICITY, descent, monotonicity "
    "and absorbing conditions -- keep the exact rule [sec:failclosed] gives "
    "each'. Assumption ass:optol (b) says the same from the assumption's side. "
    "So no case above has a second decision to freeze at a positive eps_op, "
    "and freezing one would suggest the tolerance reaches R, which it does not."
)


# ===========================================================================
#  The 0.3.0 interface vocabulary (BAND 3)
# ===========================================================================

#: Section sec:inputs at 0.3.0: UNCHANGED, seventeen keys. Aliased to the 0.2.0
#: tuple rather than restated, so the two cannot drift.
INPUT_KEYS_0_3_0: tuple[str, ...] = INPUT_KEYS_0_2_0

#: Section sec:outputs at 0.3.0: UNCHANGED, eighteen keys. Same aliasing.
#: What moves is the VALUE of `mathematical_spec_version`, not the key set.
OUTPUT_KEYS_0_3_0: tuple[str, ...] = OUTPUT_KEYS_0_2_0

#: Section sec:failclosed at 0.3.0, THE ONE NEW STRING, VERBATIM.
#: sec:amendment030 item 1: "Fail-closed rows 24 -> 25; refusal reasons
#: 26 -> 27. None removed."
REFUSAL_REASONS_ADDED_0_3_0: tuple[str, ...] = ("dark_counts_not_column_stochastic",)

#: THE FULL 27-STRING VOCABULARY, in the contract's own order: 0.2.0's
#: twenty-six with the new string inserted at the row that carries it --
#: `dark_counts_not_column_stochastic` between `bound_set_not_a_fibre` and
#: `dark_counts_do_not_descend`. Built by INSERTION into the 0.2.0 tuple rather
#: than restated, so the twenty-six cannot drift.
REFUSAL_REASONS_0_3_0: tuple[str, ...] = (
    *REFUSAL_REASONS_0_2_0[: REFUSAL_REASONS_0_2_0.index("dark_counts_do_not_descend")],
    "dark_counts_not_column_stochastic",
    *REFUSAL_REASONS_0_2_0[REFUSAL_REASONS_0_2_0.index("dark_counts_do_not_descend") :],
)

#: THE ROW COUNT AT 0.3.0: 25, from 24. ONE ROW AND ONE STRING, so the two
#: counts move together here -- which is a coincidence of this amendment and
#: not a rule: at 0.2.0 three rows carried two strings. They stay frozen
#: separately for exactly that reason.
FAIL_CLOSED_ROW_COUNT_0_3_0: int = 25
FAIL_CLOSED_ROWS_ADDED_0_3_0: tuple[tuple[str, str], ...] = (
    ("the column-stochasticity row", "dark_counts_not_column_stochastic"),
)

#: THE TABULAR COUNT, frozen because it is what made every table-ordinal
#: locator stale: sec:failclosed goes from FOUR tabulars to FIVE (its 0.2.0
#: second tabular of five rows is split into a second of four and a third of
#: two), and sec:inputs from six to seven. NO ROW CONTENT MOVES WITH EITHER
#: SPLIT; they are page fit.
FAIL_CLOSED_TABULAR_COUNT_0_3_0: int = 5
FAIL_CLOSED_TABULAR_COUNT_0_2_0: int = 4

#: Section sec:conventions at 0.3.0: STILL THIRTEEN BULLETS. The
#: `exact_arithmetic` bullet's enumeration of neighbouring exact rows grows
#: from two to three; the bullet count does not move. Built from the 0.2.0
#: mapping with the ONE value the amendment changes.
CONVENTIONS_0_3_0: dict[str, str] = {
    **CONVENTIONS_0_2_0,
    "artifact_bindings.mathematical_spec_version": "proof-reductions@0.3.0",
}

#: The three rows sec:conventions names as EXACT WITHOUT BEING INSTANCES of
#: Lemma lem:exactpsd, at 0.3.0. Two at 0.2.0; the third is the new row.
EXACT_ARITHMETIC_NEIGHBOURING_ROWS_0_3_0: tuple[str, ...] = (
    "no_block_structure",
    "total_weight_not_below_one",
    "dark_counts_not_column_stochastic",
)

#: Section sec:assumptions at 0.3.0: UNCHANGED. Ten rows, the same Supports
#: ranges, the same three never verifiable. sec:amendment030 leaves "every
#: assumption... count untouched"; what changes inside A-RECV is the SUPPLIER
#: VERSION its imported claims are read at, and two prose additions.
ASSUMPTION_LEDGER_0_3_0: tuple[AssumptionRow, ...] = ASSUMPTION_LEDGER_0_2_0
NEVER_VERIFIED_0_3_0: tuple[str, ...] = NEVER_VERIFIED_0_2_0

#: Section sec:claims at 0.3.0: THIRTEEN claims, unchanged. "No claim is added,
#: none is removed."
CLAIM_IDS_0_3_0: tuple[str, ...] = CLAIM_IDS_0_2_0

#: sec:conventions `artifact_bindings` and sec:outputs' last row at 0.3.0. THE
#: ONE EMITTED VALUE THIS AMENDMENT MOVES, and it moves only because the
#: convention is written as `proof-reductions@<contract_version>` OF THE
#: ACCEPTED CONTRACT.
SPEC_VERSION_0_3_0: str = "proof-reductions@0.3.0"

#: THE TWO PINS, frozen as strings because they are what the amendment's items
#: 2 and 3 are, and because run B must move two code-side constants to match.
#: The SUPPLIER is an import (`depends_on`); the CONSUMER is not.
SUPPLIER_PIN_0_3_0: str = "receiver-povm 0.2.0"
SUPPLIER_PIN_0_2_0: str = "receiver-povm 0.1.3"
CONSUMER_PIN_0_3_0: str = "meat-core 0.5.0"
CONSUMER_PIN_0_2_0: str = "meat-core 0.4.0"

#: THE FOUR MACHINE STRINGS OF THE CONSUMER THAT ARE NOT THIS MODULE'S, frozen
#: as a NEGATIVE list. contract.tex 0.3.0 quotes them inside Remark
#: rem:consumerdisposition and the `target_povm` row while stating what
#: MEAT-CORE 0.5.0 does with what this module emits. A naive sweep of
#: `\texttt{}` machine strings finds them and would put the reason count at
#: thirty-one. They are NOT refusal reasons of this module, are NOT emitted
#: here, and must not appear in REFUSAL_REASONS_0_3_0.
CONSUMER_STRINGS_NOT_OURS_0_3_0: tuple[str, ...] = (
    "bob_povm_not_evaluable",
    "declared_operator_tolerance_open",
    "key_length",
    "key_length_claim",
)


# ===========================================================================
#  SUPERSESSION at 0.3.0 -- what the amendment invalidates, marked not deleted
# ===========================================================================
#
#  The same discipline as band 2, and a much shorter list, because the
#  amendment moves ONE emitted value and adds ONE rule. Nothing frozen in band
#  1 or band 2 is deleted or edited here.

SUPERSESSIONS_0_3_0: tuple[Supersession, ...] = (
    Supersession(
        symbol="SPEC_VERSION_0_2_0",
        case_id="artifact-binding",
        superseded_by="0.3.0",
        kind="vocabulary",
        contract_site=(
            "sec:conventions, the artifact-bindings bullet; sec:outputs, the "
            "`mathematical_spec_version` row"
        ),
        replacement=("SPEC_VERSION_0_3_0",),
        still_valid_at_zero_tolerance=False,
        note="THE ONE EMITTED VALUE THE 0.3.0 AMENDMENT MOVES. The bullet reads "
        "`proof-reductions@<contract_version>` OF THE ACCEPTED CONTRACT, and "
        "the accepted contract is now 0.3.0, so an artifact claiming "
        "`proof-reductions@0.2.0` claims a superseded version. Nothing about "
        "the tolerance is involved, which is why this mark does not stand at "
        "eps_op = 0 either: it is a version string, not a constant.",
    ),
    Supersession(
        symbol="CONVENTIONS_0_2_0",
        case_id="conventions-mapping",
        superseded_by="0.3.0",
        kind="vocabulary",
        contract_site="sec:conventions, the artifact-bindings bullet",
        replacement=("CONVENTIONS_0_3_0",),
        still_valid_at_zero_tolerance=False,
        note="ONE KEY OF THE MAPPING MOVES and twelve do not: "
        "CONVENTIONS_0_3_0 is built FROM this mapping with the artifact "
        "binding replaced, so the twelve unchanged values cannot drift. The "
        "`exact_arithmetic` VALUE is unchanged -- 'required, on the rows "
        "named' -- because what grew is the ENUMERATION inside the bullet, "
        "frozen separately as EXACT_ARITHMETIC_NEIGHBOURING_ROWS_0_3_0.",
    ),
    Supersession(
        symbol="REFUSAL_REASONS_0_2_0",
        case_id="reason-vocabulary",
        superseded_by="0.3.0",
        kind="vocabulary",
        contract_site="sec:failclosed, the column-stochasticity row; rem:colstoch",
        replacement=("REFUSAL_REASONS_0_3_0", "REFUSAL_REASONS_ADDED_0_3_0"),
        still_valid_at_zero_tolerance=False,
        note="TWENTY-SIX BECOMES TWENTY-SEVEN. None is removed and none is "
        "renamed, so the 0.2.0 tuple is a strict PREFIX-PRESERVING SUBSET of "
        "the 0.3.0 one and the replacement is BUILT FROM IT BY INSERTION. A "
        "consumer switching on a refusal reason sees one more case, which is "
        "the first of the two reasons sec:amendment030 gives for the level "
        "being minor rather than patch.",
    ),
    Supersession(
        symbol="FAIL_CLOSED_ROW_COUNT_0_2_0",
        case_id="row-count",
        superseded_by="0.3.0",
        kind="vocabulary",
        contract_site="sec:failclosed, all its tabulars",
        replacement=("FAIL_CLOSED_ROW_COUNT_0_3_0", "FAIL_CLOSED_ROWS_ADDED_0_3_0"),
        still_valid_at_zero_tolerance=False,
        note="TWENTY-FOUR BECOMES TWENTY-FIVE. Frozen separately from the "
        "reason count because the two do not determine each other: at 0.2.0 "
        "three rows carried two strings, and at 0.3.0 one row carries one.",
    ),
    Supersession(
        symbol="ASSUMPTION_LEDGER_0_2_0",
        case_id="a-recv-supplier-pin",
        superseded_by="0.3.0",
        kind="reading",
        contract_site="Assumption ass:recv; sec:openitems",
        replacement=("ASSUMPTION_LEDGER_0_3_0", "SUPPLIER_PIN_0_3_0"),
        still_valid_at_zero_tolerance=True,
        note="MARKED FOR ITS READING AND NOT FOR ITS VALUES, WHICH IS WHY THE "
        "REPLACEMENT IS THE SAME OBJECT. Every row, machine key, Supports "
        "range and never-verifiable flag is unchanged at 0.3.0. What changes "
        "is the VERSION A-RECV's imported facts are read at -- receiver-povm "
        "0.1.3 -> 0.2.0, at eight sites -- and two sentences added to that "
        "row: that the supplier's ADMISSION PROCEDURE for a declared R is not "
        "imported, and which of the supplier's two dark-count inequalities "
        "this module composes with (NEITHER). A test asserting the ledger's "
        "VALUES is unaffected; one asserting the pinned supplier version is "
        "not, and must read SUPPLIER_PIN_0_3_0.",
    ),
)

#: THE SET OF SYMBOLS MARKED AT 0.3.0, for the integrity invariant.
SUPERSEDED_SYMBOLS_0_3_0: tuple[str, ...] = tuple(
    dict.fromkeys(record.symbol for record in SUPERSESSIONS_0_3_0)
)

#: WHAT IS DELIBERATELY *NOT* MARKED AT 0.3.0, with the reason.
NOT_SUPERSEDED_AND_WHY_0_3_0: tuple[tuple[str, str], ...] = (
    (
        "every frozen NUMBER in bands 1 and 2",
        "NOT ONE MOVES. sec:amendment030: 'No claim is added, none is removed, "
        "and no claim statement, constant, construction or emitted number "
        "changes.' The amendment adds a REFUSAL RULE and re-points two version "
        "strings; it restates no formula. In particular eq:weightroute is "
        "listed under 'Deliberately not in this amendment', so every weight in "
        "group PR-M and every constant in group PR-O stands unchanged.",
    ),
    (
        "INPUT_KEYS_0_2_0 and OUTPUT_KEYS_0_2_0",
        "NO KEY IS ADDED, REMOVED OR REORDERED at 0.3.0, so the 0.3.0 tuples "
        "are ALIASES of the 0.2.0 ones rather than copies. The `target_povm` "
        "row's prose changes and the `mathematical_spec_version` VALUE changes; "
        "neither is a key-set change, and the value is marked through "
        "SPEC_VERSION_0_2_0.",
    ),
    (
        "the whole of group PR-O (PR13 and the declared operator tolerance)",
        "UNTOUCHED. The tolerance does not reach R (Remark rem:tolboundary), "
        "the new row does not invoke Lemma lem:exactpsd (sec:conventions, "
        "`exact_arithmetic`), and no part of A-OPTOL, def:tolerance, "
        "prop:tolrows, thm:tolerance or cor:tolentries is amended. The one "
        "thing 0.3.0 says about the tolerance surface is that the "
        "column-stochasticity row is decided identically at every eps_op, "
        "which COLSTOCH_TOLERANCE_PROBE records.",
    ),
    (
        "REFUSAL_CASES and the band-2 case tuples",
        "EVERY ONE IS DECIDED IDENTICALLY AT 0.3.0. The amendment adds a row "
        "that no existing case's declaration trips: each of them declares "
        "either no dark-count matrix at all or an exactly column-stochastic "
        "one. A case that DID trip it would have to be a declaration outside "
        "sec:inputs's declared type, and none of them is.",
    ),
)


# ---------------------------------------------------------------------------
#  Change-request candidates for the 0.3.0 delta
# ---------------------------------------------------------------------------
#
#  As in bands 1 and 2: for each item run A could not resolve from the
#  interface alone, either THE READING THE TEXT FIXES with its locator, or the
#  item is ROUTED. NOTHING BELOW IS DECIDED HERE.

CHANGE_REQUEST_CANDIDATES_0_3_0: tuple[tuple[str, str, str], ...] = (
    (
        "(a) the pinned supplier version -- band 2's routed item",
        "CLOSED BY 0.3.0 -- no longer a candidate",
        """\
Band 2 ROUTED exactly one item: contract.tex 0.2.0 named `receiver-povm 0.1.3`
while that module was itself accepted at 0.2.0, and an implementer may not
advance a contract's pin. THE 0.3.0 AMENDMENT ADVANCED IT, at eight sites, and
answered the mathematical half band 2 could not: Remark rem:darkcompose derives
that this module composes with NEITHER of the supplier's two dark-count
inequalities -- it re-derives eq:routebound inline -- and that every declaration
it admits is exactly admissible in the supplier's sense, so the supplier's slack
terms r-bar and delta_dc are nil as content and nothing in eq:weightroute is
restated. Assumption ass:recv now also says the supplier's ADMISSION PROCEDURE
for a declared R is not imported, only the definition it admits against. A
drafter and a verifier settled that, which is where it belonged.""",
    ),
    (
        "(b) what the consumer does with an eta_v-accurate POVM -- band 2's item (d)",
        "CLOSED BY 0.3.0 AT ITS SOURCE -- and it never became this module's rule",
        """\
Band 2 recorded that meat-core 0.4.0 validated ass:decl (iii) on the numbers it
received and that a consumer-side tolerance would need "a further amendment on
meat-core's side, named here and not decided here". THAT AMENDMENT LANDED:
meat-core 0.5.0 is accepted, and Remark rem:consumerdisposition reads its
five-rule interface consequence at its source. THE FINDING, in the contract's
own words: at eps_op > 0 this module does NOT IN GENERAL supply exactly
admissible numbers, and where it does not, no key length is reachable through
that consumer on those numbers -- refusal, or admission with the key length
withheld. THE EXCEPTION IS STATED AND IS NOT DECORATION: eps_op is a DECLARED
upper bound this module never verifies, so a caller may declare it positive over
blocks that are in fact exact, and then every defect is zero and a key length IS
reachable. NOTHING THIS MODULE EMITS CHANGES and no row is added. The four
machine strings the remark quotes are the CONSUMER's, are frozen in this file as
a NEGATIVE list (CONSUMER_STRINGS_NOT_OURS_0_3_0), and are not in
REFUSAL_REASONS_0_3_0.""",
    ),
    (
        "(c) whether the new row must also be stated on the descended matrix",
        "RESOLVED from the text -- it must not, and the reason is proved",
        """\
THE OBVIOUS IMPLEMENTATION QUESTION, AND THE CONTRACT ANSWERS IT IN A FULL
PARAGRAPH. Remark rem:colstoch: the fibres of cg partition 2^[K], cg being a
total surjection, so R^cg_{y|y'} = sum_{S in cg^{-1}(y)} R_{S|S'} >= 0 as a sum
of non-negative entries, and sum_y R^cg_{y|y'} = sum_S R_{S|S'} = 1. "Deciding
it on the declared matrix therefore DISCHARGES IT FOR THE DESCENDED ONE, AND NO
SECOND ROW IS STATED." The fail-closed row says the same in one clause:
"DECIDED ON R, WHICH SUFFICES: Lemma lem:descent carries BOTH HALVES to R^cg, so
no second row is stated on the descended matrix." A second row would be a rule
the contract does not state AND would need a reason string that does not exist.
COLSTOCH_CASES freezes both directions of the implication, including the
non-trivial one where a fibre has two elements (CS-coarse-admit) and the one
where the defect travels to R^cg (CS-colsum-refuse).""",
    ),
    (
        "(d) whether the coarse-graining's surjectivity gets a row too",
        "RESOLVED from the text -- it does not, and the contract says so twice",
        """\
sec:inputs's `outcome_coarse_graining` row gained a pointer at 0.3.0 that looks
like the dark-count row's and is NOT: surjectivity is "a hypothesis of Lemma
lem:descent THAT NO ROW OF [sec:failclosed] DECIDES HERE, AND NONE IS ADDED",
because totality and surjectivity are decided exactly, by finite inspection, in
receiver-povm 0.2.0 and reach this module through A-RECV and the receiver-spec
row. sec:amendment030 item 5 repeats it: the pointer "adds no row, no rule and
no reason string, the two cases being different for the reason it states" --
column-stochasticity being something the supplier admits only WITHIN A TOLERANCE
and surjectivity being something it decides exactly. NO CASE IS FROZEN FOR A
SURJECTIVITY REFUSAL, because there is no such refusal to freeze.""",
    ),
    (
        "(e) the reason-string count, and the four strings that are not ours",
        "RESOLVED from the text -- twenty-seven, and the four are the consumer's",
        """\
A COUNTING HAZARD WORTH RECORDING BECAUSE IT IS EASY TO GET WRONG IN THE UNSAFE
DIRECTION. contract.tex 0.3.0 carries FOUR `\\texttt{}` machine strings that a
naive sweep would add to this module's vocabulary --
`bob_povm_not_evaluable`, `declared_operator_tolerance_open`, `key_length`,
`key_length_claim` -- putting the count at thirty-one. All four are MEAT-CORE
0.5.0's, quoted inside Remark rem:consumerdisposition and the `target_povm` row
while stating what the CONSUMER does. The vocabulary is what sec:failclosed's
tables name, "and nowhere else", and that is TWENTY-SEVEN over TWENTY-FIVE rows.
The four are frozen here as CONSUMER_STRINGS_NOT_OURS_0_3_0 so that the
exclusion is a checked fact rather than a remembered one.""",
    ),
    (
        "(f) the two code-side version strings the amendment moves",
        "ROUTED -- an observation to the driver, and NOT a contract gap",
        """\
NOT A GAP IN THE CONTRACT: it is a consequence of one, and run A may not write
under src/. The convention fixes the emitted binding as
`proof-reductions@<contract_version>` OF THE ACCEPTED CONTRACT, so the accepted
0.3.0 makes it `proof-reductions@0.3.0`, and TWO hard-coded strings in the
implementation package are stale against that: the default of
`ProofReductionArtifact.mathematical_spec_version` in
the earlier reductions artifact module, which reads `proof-reductions@0.2.0`, and
the `technique` default in the earlier reductions constraints module, which names
"the squashed round model of meat-core 0.4.0 def:roundmodel" while Definition
def:roundmodel now quotes 0.5.0. `accepted_receiver_versions` in
the earlier reductions inputs module is NOT one of these -- it is a caller-supplied
tuple defaulting to empty, fail-closed by construction, and not a pin. Several
golden-test fixtures pass `receiver-povm@0.1.3` as FIXTURE DATA; those are
fixtures, not pins. NONE WAS CHANGED BY THIS RUN; run B changes the two.""",
    ),
)


# ===========================================================================
# ===========================================================================
#  Group PR-Q -- BAND 4: the 0.3.0-to-1.0.0 amendment
# ===========================================================================
# ===========================================================================
#
#  Every value below was derived BY HAND from the accepted ``contract.tex``
#  **1.0.0** (LF sha256
#  6430d3b9e06d8ae3f5d03b304cd0498a6b63ef47298f3c58830b205653586545, the
#  RELEASED blob of ``STATUS.yaml`` ``gates.g3.released_blob_sha256_lf``)
#  before any code changed.
#
#  BAND 4 IS LARGE BECAUSE THE AMENDMENT IS. 1.0.0 changes WHAT THE MODULE
#  EMITS: the emission normalizer (``def:emitnorm``), the downward-rounded
#  ``p_v`` (``eq:latdown``), the scalar ``c_k`` entries (``cor:entries``),
#  ``emission_record`` in place of ``operator_tolerance_record``, and
#  ``lattice_exponent`` in place of ``declared_tolerance``. Three fail-closed
#  rows and four refusal-reason strings are added, one string is removed, and
#  the tier ceiling moves from ``certified`` to ``first-order``.
#
#  BAND 4 DELETES AND EDITS NOTHING FROZEN BY BANDS 1-3. What the amendment
#  invalidates is MARKED, in ``SUPERSESSIONS_1_0_0`` and in
#  ``SCOPE_MARKS_1_0_0`` -- **a list BESIDE the entries and never a field
#  inside one**, so that byte-immutability of every frozen case is preserved.
#  ``NOT_SUPERSEDED_AND_WHY_1_0_0`` records what is deliberately left unmarked.
#
#  THE LATTICE EXPONENT USED THROUGHOUT THIS BAND IS kappa = 4, and it is a
#  CHOICE OF FIXTURE AND NOT A PLATFORM VALUE. The contract "fixes no value"
#  (``sec:inputs``, ``lattice_exponent``); ADR-0008 Section 7.2.1's preamble
#  records the platform's k = 40. kappa = 4 is legible by hand, satisfies
#  ``1 <= kappa <= 53`` and, at every alphabet size used below,
#  ``kappa + ceil(log2 max{|V|,|Y|,|T|}) <= 53``. Every value below is stated
#  as an exact ``Fraction``; nothing here is a float.

#: The contract blob band 4 was derived from, frozen so that a later reader can
#: check that the derivations belong to this text and not to another.
CONTRACT_SHA256_1_0_0: str = (
    "6430d3b9e06d8ae3f5d03b304cd0498a6b63ef47298f3c58830b205653586545"
)

#: The 1.0.1 PATCH blob (released), pinned BESIDE the 1.0.0 one and never in
#: place of it: every value of band 4 was derived against 1.0.0 and every one of
#: them is re-read against 1.0.1 below without moving.
CONTRACT_SHA256_1_0_1: str = (
    "f12d712fed3c20c9f5736b5af69e9822aa9aba9ca0075d55811a5bd88a004df6"
)

#: WHAT THE 1.0.1 PATCH DECIDED, and what it does to the frozen values of this
#: band. A LIST BESIDE THE ENTRIES, never a field inside one: no frozen value,
#: tuple or field below is edited, and the two-instance freeze holds. Band B2
#: run B re-read every PR-Q value against the amended text before writing a line
#: of source; the third element of each row is the re-read result.
TIE_RULES_1_0_1: tuple[tuple[str, str, str], ...] = (
    (
        "def:emitnorm (2), the rounding tie",
        "TIES TO EVEN -- 'a part lying exactly halfway between two multiples "
        "goes to the one whose integer numerator is even'. Answers change "
        "request (j) of interface.yaml, raised at 1.0.0.",
        "NO FROZEN VALUE MOVES. Every rounding in EN1-EN4 was chosen to avoid "
        "a tie and every derivation says so in terms: EN2 'each a rounding "
        "DOWN of a value whose fractional part is 1/4, and NO TIE ARISES'; "
        "EN3's re-application '7/4 = 1.75 -> 2 (no tie)' and "
        "'29/8 = 3.625 -> 4 (no tie)'; EN1 and EN4 round nothing at all. The "
        "witness the request was found on -- 7/32 at kappa = 4, an exact tie -- "
        "was DELIBERATELY NOT FROZEN and is not a case here.",
    ),
    (
        "def:emitnorm (3), the designated-element tie",
        "THE FIRST IN THE DECLARED ORDER OF Y at that fixed t, among the "
        "outcomes attaining the largest exact trace. Answers change request "
        "(h), first half.",
        "NO FROZEN VALUE MOVES. EN2 is the only case with a non-zero residue "
        "and its maximiser is UNIQUE (21/64 > 17/64 = 17/64 > 9/64 before "
        "step (2), 5/16 > 1/4 = 1/4 > 1/8 after it), so no tie is reached and "
        "y* = y0 under the amended rule as under the 1.0.0 one. EN1, EN3 and "
        "EN4 designate no element at all.",
    ),
    (
        "def:emitnorm (3), structurally-zero elements",
        "NO EXCLUSION: 'no exclusion of structurally-zero elements is stated "
        "and none is needed', because an exclusion 'would nominate none at all "
        "and leave this step undefined'. Answers change request (h), second "
        "half, AGAINST the reading domain/snap.py implements.",
        "NO FROZEN VALUE MOVES, and this is the row that BINDS THE SOURCE: "
        "reductions/emit.py may not route through domain/snap.py's "
        "designated_element_index, which excludes zero elements and refuses "
        "no_designated_element where every element is zero. This contract "
        "nominates the first such element and refuses nothing.",
    ),
)

#: The band's fixture lattice exponent, and the step it fixes.
KAPPA_FIXTURE: int = 4
LATTICE_STEP_FIXTURE: F = F(1, 2**KAPPA_FIXTURE)


def _on_lattice(value: F, kappa: int = KAPPA_FIXTURE) -> bool:
    """Eq. eq:latinv, decided exactly: 2^kappa x in Z and |x| <= 1."""
    return (value * 2**kappa).denominator == 1 and abs(value) <= 1


# ---------------------------------------------------------------------------
#  PR-Q1 -- the emission normalizer, def:emitnorm, on hand-authored blocks
# ---------------------------------------------------------------------------
#
#  Four blocks, one per behaviour def:emitnorm can exhibit. Each is a family
#  over a declared Y at ONE setting with q_t = 1, on ONE preserved block, and
#  each is a family THIS MODULE COMPUTED and is about to declare -- never a
#  family it was handed. def:emitnorm, fourth property: "THIS IS A SNAP OF WHAT
#  THIS MODULE DECLARES AND NEVER OF WHAT IT WAS HANDED."


@dataclass(frozen=True)
class EmissionNormalizerCase:
    """One preserved block put through def:emitnorm's five steps."""

    case_id: str
    claims: tuple[str, ...]
    kappa: int
    #: The declared outcome letters, in the emitted order.
    letters: tuple[str, ...]
    #: The declared probe weight at the single setting.
    q_t: F
    #: The CONSTRUCTED family, per letter, as an exact matrix (real entries).
    constructed: tuple[tuple[str, Matrix], ...]
    #: True when step (1), the Hermitian part, is the identity map.
    step1_is_identity: bool
    #: The family after step (2), lattice rounding to nearest.
    after_rounding: tuple[tuple[str, Matrix], ...]
    #: The step-(3) completeness residue, and the designated element it went to.
    residue: Matrix | None
    designated_element: str | None
    #: The step-(4) lift: the ladder weight and the dyadic vector, or None.
    lift_weight: F | None
    lift_vector: tuple[tuple[str, F], ...] | None
    #: The EMITTED family after step (5) has decided all six, or None on refusal.
    emitted: tuple[tuple[str, Matrix], ...] | None
    #: Eq. eq:displacement, per preserved block: max over v of the entrywise
    #: maximum modulus. None where the family is refused.
    delta_s: F | None
    #: The refusal reason where step (5) cannot establish the six, else None.
    refusal_reason: str | None
    #: Which of the six (D-EMIT) conditions the refusal names.
    refused_predicate: str | None
    derivation: str


#: The identity case: a block already on the lattice. The normalizer does
#: nothing, Delta_s = 0, and "nothing below has an antecedent"
#: (def:emitnorm, first property).
EMITNORM_ON_LATTICE = EmissionNormalizerCase(
    case_id="EN1-already-on-the-lattice",
    claims=("PR13",),
    kappa=4,
    letters=("y0", "y1"),
    q_t=F(1),
    constructed=(
        ("y0", real_matrix(((F(1, 2), F(1, 4)), (F(1, 4), F(1, 2))))),
        ("y1", real_matrix(((F(1, 2), F(-1, 4)), (F(-1, 4), F(1, 2))))),
    ),
    step1_is_identity=True,
    after_rounding=(
        ("y0", real_matrix(((F(1, 2), F(1, 4)), (F(1, 4), F(1, 2))))),
        ("y1", real_matrix(((F(1, 2), F(-1, 4)), (F(-1, 4), F(1, 2))))),
    ),
    residue=real_matrix(((F(0), F(0)), (F(0), F(0)))),
    designated_element=None,
    lift_weight=None,
    lift_vector=None,
    emitted=(
        ("y0", real_matrix(((F(1, 2), F(1, 4)), (F(1, 4), F(1, 2))))),
        ("y1", real_matrix(((F(1, 2), F(-1, 4)), (F(-1, 4), F(1, 2))))),
    ),
    delta_s=F(0),
    refusal_reason=None,
    refused_predicate=None,
    derivation="""\
def:emitnorm, FIRST PROPERTY: "M' = M and every Delta_s = 0 whenever the exact
construction already satisfies eq:latinv, in which case THE NORMALIZER IS THE
IDENTITY and nothing below has an antecedent. THAT IS THE ORDINARY CASE AT A
NOMINAL DECLARATION AND IS NOT THE GENERAL ONE."

THE FAMILY. Two outcomes on one 2x2 preserved block at one setting with
q_t = 1: A_y0 = [[1/2, 1/4], [1/4, 1/2]], A_y1 = [[1/2, -1/4], [-1/4, 1/2]].

STEP (1), the Hermitian part, IS THE IDENTITY: both matrices are real symmetric,
so A = A-dagger entry for entry. def:emitnorm names the step anyway "because the
table names it and because it is what makes the order of the remaining steps
meaningful".

STEP (2), lattice rounding at kappa = 4 (step 2^-4 = 1/16): every entry is
already an integer multiple of 1/16 -- 1/2 = 8/16, 1/4 = 4/16 -- so the step is
the identity. eq:latinv holds: 2^4 * 1/2 = 8, 2^4 * 1/4 = 4, both integers, and
every modulus is at most 1.

STEP (3), completeness: A_y0 + A_y1 = [[1, 0], [0, 1]] = q_t * 1 exactly, so the
residue is the zero matrix and NO ELEMENT IS DESIGNATED. Nothing is added.

STEP (4), positivity, decided by eq:psdtest and NOT by an eigenvalue routine.
For A_y0: e_1 = tr = 1/2 + 1/2 = 1 >= 0, and e_2 = det = (1/2)(1/2) - (1/4)^2 =
1/4 - 1/16 = 3/16 >= 0. Both principal-minor sums are non-negative, so
A_y0 >= 0 by lem:exactpsd (i). A_y1 is the same by symmetry: e_1 = 1,
e_2 = 3/16. NO LIFT IS APPLIED.

STEP (5), all six decided on the result: (a) the declared labels agree by
construction; (b) Hermiticity, entry for entry, holds; (c) positivity, above;
(d) completeness, above; (e) kappa + ceil(log2 |Y|) = 4 + 1 = 5 <= 53, so
lem:latsum gives the rounds-nowhere condition; and eq:latinv entry by entry.

Eq. eq:displacement: M' = M entry for entry, so Delta_s = max_v maxnorm(0) = 0.

SECOND ROUTE, INDEPENDENT OF THE FIRST. Read every entry as an integer number
of sixteenths: A_y0 = [[8, 4], [4, 8]]/16, A_y1 = [[8, -4], [-4, 8]]/16. The
sum is [[16, 0], [0, 16]]/16 = 1 exactly, in integers. Each entry is already an
integer, so rounding to the nearest integer is the identity. det(A_y0) in units
of 1/256 is 8*8 - 4*4 = 48 > 0, and tr in units of 1/16 is 16 > 0. The two
routes agree on every number.""",
)

#: The rounding case: a block one lattice step off, whose rounding leaves a
#: residue that step (3) absorbs into the largest-exact-trace element.
EMITNORM_ROUNDED = EmissionNormalizerCase(
    case_id="EN2-rounded-and-restored",
    claims=("PR13",),
    kappa=4,
    letters=("y0", "y1", "y2", "y3"),
    q_t=F(1),
    constructed=(
        ("y0", real_matrix(((F(21, 64),),))),
        ("y1", real_matrix(((F(17, 64),),))),
        ("y2", real_matrix(((F(17, 64),),))),
        ("y3", real_matrix(((F(9, 64),),))),
    ),
    step1_is_identity=True,
    after_rounding=(
        ("y0", real_matrix(((F(5, 16),),))),
        ("y1", real_matrix(((F(1, 4),),))),
        ("y2", real_matrix(((F(1, 4),),))),
        ("y3", real_matrix(((F(1, 8),),))),
    ),
    residue=real_matrix(((F(1, 16),),)),
    designated_element="y0",
    lift_weight=None,
    lift_vector=None,
    emitted=(
        ("y0", real_matrix(((F(3, 8),),))),
        ("y1", real_matrix(((F(1, 4),),))),
        ("y2", real_matrix(((F(1, 4),),))),
        ("y3", real_matrix(((F(1, 8),),))),
    ),
    delta_s=F(3, 64),
    refusal_reason=None,
    refused_predicate=None,
    derivation="""\
THE CASE def:emitnorm EXISTS FOR. sec:consume: "a product of two dyadic
rationals ADDS SIGNIFICAND WIDTHS, so the post-processed blocks need not be
binary64 numbers even though every factor is. THAT IS THE ONE PLACE IN THIS
CONTRACT WHERE EXACT ARITHMETIC OUTRUNS THE REPRESENTATION, it is where
Definition def:emitnorm acts."

THE FAMILY. Four outcomes on ONE 1x1 preserved block at one setting with
q_t = 1, the constructed values being exact rationals with denominator 64:
A_y0 = 21/64, A_y1 = 17/64, A_y2 = 17/64, A_y3 = 9/64. They sum to
(21 + 17 + 17 + 9)/64 = 64/64 = 1 EXACTLY, so the CONSTRUCTION is complete
before the normalizer runs. NONE of the four is on the kappa = 4 lattice:
2^4 * 21/64 = 21/4, 2^4 * 17/64 = 17/4, 2^4 * 9/64 = 9/4, none an integer.

STEP (1) is the identity: a 1x1 real block is its own adjoint.

STEP (2), rounding to the nearest multiple of 1/16. In units of 1/4 of a
sixteenth: 21/4 -> 5, 17/4 -> 4, 17/4 -> 4, 9/4 -> 2, each a rounding DOWN of a
value whose fractional part is 1/4, and NO TIE ARISES (a tie needs a fractional
part of exactly 1/2). So the rounded family is 5/16, 4/16, 4/16, 2/16 =
5/16, 1/4, 1/4, 1/8, and its sum is 15/16.

STEP (3), completeness restored EXACTLY and PER SETTING. The residue is
q_t * 1 - sum_y A_y = 1 - 15/16 = 1/16, ITSELF ON THE LATTICE, "being a
difference of lattice values" -- and it is exactly ONE lattice step. The
designated element is "the outcome of LARGEST EXACT TRACE in that block at that
setting": on a 1x1 block the trace is the value, and 21/64 > 17/64 = 17/64 >
9/64, so y* = y0, THE MAXIMISER BEING UNIQUE. The fixture is built so that the
same letter wins on the traces AFTER step (2) as well -- 5/16 > 1/4 = 1/4 >
1/8 -- so the frozen answer does not depend on which of the two readings of
"exact trace" is taken. THAT IT DOES NOT IS A PROPERTY OF THIS FIXTURE AND NOT
A FACT ABOUT THE CONTRACT.

The emitted family is therefore 5/16 + 1/16 = 3/8 at y0, and 1/4, 1/4, 1/8
unchanged. Its sum is 3/8 + 1/4 + 1/4 + 1/8 = (3 + 2 + 2 + 1)/8 = 1 EXACTLY.

STEP (4), positivity: a 1x1 block is positive semidefinite iff its single entry
is non-negative, and 3/8, 1/4, 1/4, 1/8 all are. eq:psdtest reduces to
e_1 = the entry >= 0. NO LIFT.

STEP (5), all six on the result: labels by construction; Hermiticity trivially;
positivity above; completeness above; kappa + ceil(log2 4) = 4 + 2 = 6 <= 53 for
lem:latsum; and eq:latinv, every emitted value being 6/16, 4/16, 4/16, 2/16.

Eq. eq:displacement, PER PRESERVED BLOCK and as a maximum over v of the
entrywise maximum modulus:
  y0: |3/8 - 21/64|   = |24/64 - 21/64| = 3/64
  y1: |1/4 - 17/64|   = |16/64 - 17/64| = 1/64
  y2: |1/4 - 17/64|   = 1/64
  y3: |1/8 - 9/64|    = |8/64 - 9/64|   = 1/64
  Delta_s = max = 3/64 = 0.046875 exactly.
NOTE THAT Delta_s IS EXACT HERE, and that this does not contradict the
contract: eq:displacement takes a maximum MODULUS of a COMPLEX difference, and
the modulus of a REAL difference is its absolute value, a rational. The
irrationality the contract names arises only where a displacement has both a
real and an imaginary part -- see EMITNORM_IRRATIONAL_DISPLACEMENT below.

SECOND ROUTE, INDEPENDENT OF THE FIRST: integer units of 2^-6. The constructed
family is (21, 17, 17, 9) units, summing to 64. One lattice step is 4 units, so
step (2) rounds each to the nearest multiple of 4: 21 -> 20, 17 -> 16, 17 -> 16,
9 -> 8, summing to 60. The residue is 64 - 60 = 4 units = 1/16. Adding it to y0
gives (24, 16, 16, 8), which sums to 64 = 1. The per-entry displacements are
|24 - 21| = 3, |16 - 17| = 1, |16 - 17| = 1, |8 - 9| = 1 units, so
Delta_s = 3 units = 3/64. THE TWO ROUTES AGREE ON EVERY NUMBER.""",
)

#: The lift case: a block that fails positivity after rounding and is repaired
#: by the smallest rung of the fixed dyadic ladder, with (2) and (3) re-applied.
EMITNORM_LIFTED = EmissionNormalizerCase(
    case_id="EN3-positivity-lift",
    claims=("PR13",),
    kappa=4,
    letters=("y0", "y1"),
    q_t=F(1),
    constructed=(
        ("y0", real_matrix(((F(0), F(1, 8)), (F(1, 8), F(3, 16))))),
        ("y1", real_matrix(((F(1), F(-1, 8)), (F(-1, 8), F(13, 16))))),
    ),
    step1_is_identity=True,
    after_rounding=(
        ("y0", real_matrix(((F(0), F(1, 8)), (F(1, 8), F(3, 16))))),
        ("y1", real_matrix(((F(1), F(-1, 8)), (F(-1, 8), F(13, 16))))),
    ),
    residue=real_matrix(((F(0), F(0)), (F(0), F(0)))),
    designated_element=None,
    lift_weight=F(1, 8),
    lift_vector=(("y0", F(1, 2)), ("y1", F(1, 2))),
    emitted=(
        ("y0", real_matrix(((F(1, 16), F(1, 8)), (F(1, 8), F(1, 4))))),
        ("y1", real_matrix(((F(15, 16), F(-1, 8)), (F(-1, 8), F(3, 4))))),
    ),
    delta_s=F(1, 16),
    refusal_reason=None,
    refused_predicate=None,
    derivation="""\
def:emitnorm STEP (4): "Where an element fails, THE FAMILY AT THAT SETTING AND
BLOCK is mixed with a trivial one, A -> (1 - w) A + w u_y q_t 1, with u a dyadic
probability vector on Y with EVERY u_y > 0, and w THE SMALLEST WEIGHT OF THE
FIXED DYADIC LADDER 2^-1, 2^-2, ..., 2^-kappa THAT RESTORES EXACT POSITIVITY."

THE FAMILY. Two outcomes on one 2x2 preserved block at one setting with
q_t = 1: A_y0 = [[0, 1/8], [1/8, 3/16]], A_y1 = [[1, -1/8], [-1/8, 13/16]].
They sum to the identity exactly and every entry is on the kappa = 4 lattice
(0, 2/16, 3/16, 16/16, 13/16), so STEPS (1), (2) AND (3) ARE ALL THE IDENTITY
and the case isolates step (4).

POSITIVITY IS DECIDED BY eq:psdtest AND FAILS AT y0. e_1(A_y0) = 0 + 3/16 =
3/16 >= 0, but e_2(A_y0) = det = 0 * 3/16 - (1/8)^2 = -1/64 < 0, so
A_y0 >= 0 is FALSE. A_y1 passes: e_1 = 1 + 13/16 = 29/16 >= 0 and
e_2 = 1 * 13/16 - 1/64 = 52/64 - 1/64 = 51/64 >= 0.

THE LADDER SEARCH, with u = (1/2, 1/2), every u_y > 0 and both dyadic, and
q_t = 1. Positivity of the mixture is MONOTONE in w -- a larger w mixes in more
of a positive definite matrix -- so the working weights are upward closed and
"the smallest that restores exact positivity" is well defined. Searching the
ladder 2^-4, 2^-3, 2^-2, 2^-1 from the smallest:
  w = 1/16: B_y0 = [[1/32, 15/128], [15/128, 53/256]] and
            e_2(B_y0) = (1/32)(53/256) - (15/128)^2
                      = 106/16384 - 225/16384 = -119/16384 < 0
            -- STILL NOT POSITIVE.
            [PROSE CORRECTION, finding F-S2-PR-12. This
            line printed the (1,1) entry as 47/256; it is
            (15/16)(3/16) + 1/32 = 45/256 + 8/256 = 53/256. NO FROZEN VALUE
            MOVES: the entry appears in no field of this case, and the e_2 the
            line concludes with was ALREADY the value at 53/256, so the ladder
            search and every frozen field are unchanged.]
  w = 1/8 : B_y0 = [[1/16, 7/64], [7/64, 29/128]] and
            e_1 = 37/128 >= 0, e_2 = (1/16)(29/128) - (7/64)^2
                = 29/2048 - 49/4096 = 58/4096 - 49/4096 = 9/4096 >= 0  -- POSITIVE.
            B_y1 = [[15/16, -7/64], [-7/64, 99/128]] likewise:
            e_1 = 219/128, e_2 = (15/16)(99/128) - 49/4096
                = 1485/2048 - 49/4096 = 2970/4096 - 49/4096 = 2921/4096 >= 0.
  SO w = 1/8, THE THIRD RUNG, and neither 1/16 nor any smaller rung exists.
The mixture preserves completeness at that setting, as def:emitnorm proves:
sum_y ((1-w) A_y + w u_y q_t 1) = (1-w) q_t 1 + w q_t 1 = q_t 1, and here
B_y0 + B_y1 = 1 exactly.

STEPS (2) AND (3) ARE RE-APPLIED, "because (1-w)A NEED NOT STAY ON THE LATTICE"
-- and here it does not: 7/64 and 29/128 are not multiples of 1/16.
  step (2): 2^4 * 7/64  = 7/4  = 1.75  -> 2  -> 1/8   (no tie)
            2^4 * 29/128 = 29/8 = 3.625 -> 4  -> 1/4   (no tie)
            2^4 * 1/16  = 1                  -> 1/16  (already on the lattice)
            and symmetrically for B_y1: 15/16, -1/8, 3/4.
  So C_y0 = [[1/16, 1/8], [1/8, 1/4]] and C_y1 = [[15/16, -1/8], [-1/8, 3/4]].
  step (3): C_y0 + C_y1 = [[1, 0], [0, 1]] EXACTLY, so the residue is zero and
  the step is the identity. THAT IS STRUCTURAL AT |Y| = 2 AND IS WORTH SAYING:
  1 is on the lattice and rounding to nearest satisfies rnd(1 - x) = 1 - rnd(x)
  for every non-tie x, so the two roundings are complementary and cannot leave
  a residue. A residue needs three or more outcomes -- which is why EN2 has
  four.

STEP (5), all six decided on C:
  (b) Hermiticity: C_y0 and C_y1 are real symmetric, entry for entry.
  (c) positivity: e_1(C_y0) = 1/16 + 1/4 = 5/16 >= 0 and
      e_2(C_y0) = (1/16)(1/4) - (1/8)^2 = 1/64 - 1/64 = 0 >= 0 -- POSITIVE AND
      EXACTLY SINGULAR. eq:psdtest decides that with e_2 >= 0 and no eigenvalue
      routine; a floating-point eigenvalue would return a small number of either
      sign here, which is why rem:psdalgorithm excludes one by name.
      e_1(C_y1) = 15/16 + 3/4 = 27/16 >= 0 and
      e_2(C_y1) = (15/16)(3/4) - 1/64 = 45/64 - 1/64 = 44/64 = 11/16 >= 0.
  (d) completeness: above.
  (e) kappa + ceil(log2 2) = 4 + 1 = 5 <= 53, so lem:latsum applies.
  (lat) eq:latinv: 1/16, 2/16, 4/16, 15/16, 12/16, all integers over 16.

Eq. eq:displacement, against the CONSTRUCTED family:
  y0: |1/16 - 0| = 1/16, |1/8 - 1/8| = 0, |1/4 - 3/16| = 1/16   -> 1/16
  y1: |15/16 - 1| = 1/16, |-1/8 + 1/8| = 0, |3/4 - 13/16| = 1/16 -> 1/16
  Delta_s = 1/16 = 0.0625 exactly.
emission_record carries, for this block: Delta_s = 1/16, NO designated element
(the residue was zero), the lift weight w = 1/8 and the lift vector
u = (1/2, 1/2). Those are "the two def:emitnorm (4) records".

SECOND ROUTE, INDEPENDENT OF THE FIRST: integer units of 2^-7 = 1/128. The
lifted family is B_y0 = [[8, 14], [14, 29]] and B_y1 = [[120, -14], [-14, 99]]
units. One lattice step is 8 units, so step (2) rounds each to the nearest
multiple of 8: 8 -> 8, 14 -> 16, 29 -> 32; 120 -> 120, -14 -> -16, 99 -> 96.
That is C_y0 = [[8, 16], [16, 32]]/128 = [[1/16, 1/8], [1/8, 1/4]] and
C_y1 = [[120, -16], [-16, 96]]/128 = [[15/16, -1/8], [-1/8, 3/4]], the same
matrices. The displacements in units of 1/128 are |8 - 0| = 8, |16 - 16| = 0,
|32 - 24| = 8 and |120 - 128| = 8, |-16 + 16| = 0, |96 - 104| = 8, so
Delta_s = 8 units = 8/128 = 1/16. THE TWO ROUTES AGREE ON EVERY NUMBER.""",
)

#: The refusal case: a block no rung of the ladder repairs.
EMITNORM_REFUSED = EmissionNormalizerCase(
    case_id="EN4-no-rung-repairs-it",
    claims=("PR13",),
    kappa=4,
    letters=("y0", "y1"),
    q_t=F(1),
    constructed=(
        ("y0", real_matrix(((F(0), F(3, 4)), (F(3, 4), F(0))))),
        ("y1", real_matrix(((F(1), F(-3, 4)), (F(-3, 4), F(1))))),
    ),
    step1_is_identity=True,
    after_rounding=(
        ("y0", real_matrix(((F(0), F(3, 4)), (F(3, 4), F(0))))),
        ("y1", real_matrix(((F(1), F(-3, 4)), (F(-3, 4), F(1))))),
    ),
    residue=real_matrix(((F(0), F(0)), (F(0), F(0)))),
    designated_element=None,
    lift_weight=None,
    lift_vector=(("y0", F(1, 2)), ("y1", F(1, 2))),
    emitted=None,
    delta_s=None,
    refusal_reason="emitted_family_not_admissible",
    refused_predicate="positivity, def:exactadm (c), decided by eq:psdtest",
    derivation="""\
def:emitnorm STEP (4), last sentence: "A BLOCK NO WEIGHT OF THE LADDER REPAIRS
IS A REFUSAL (emitted_family_not_admissible), NEVER A FURTHER APPROXIMATION."
sec:failclosed's emitted-family row: "where the ladder of that definition's step
(4) cannot restore exact positivity, THIS ROW FIRES", and "THE REFUSAL NAMES THE
PREDICATE THAT FAILED".

THE FAMILY. Two outcomes on one 2x2 preserved block at one setting with
q_t = 1: A_y0 = [[0, 3/4], [3/4, 0]], A_y1 = [[1, -3/4], [-3/4, 1]]. They sum to
the identity exactly; every entry is on the kappa = 4 lattice (0, 12/16, 16/16);
so steps (1), (2) and (3) are the identity and the case isolates the refusal.

POSITIVITY FAILS AT y0 AND CANNOT BE REPAIRED. e_1(A_y0) = 0, e_2(A_y0) =
0 * 0 - (3/4)^2 = -9/16 < 0. A_y1 passes: e_1 = 2, e_2 = 1 - 9/16 = 7/16 >= 0.
The ladder search with u = (1/2, 1/2), q_t = 1, from the smallest rung:
  w = 1/16: e_2(C_y0) = (1/32)^2 - (45/64)^2 = 1/1024 - 2025/4096
            = 4/4096 - 2025/4096 = -2021/4096 < 0.  FAILS.
            [PROSE CORRECTION, finding F-S2-PR-12. This
            line printed the off-diagonal as 15/64 and drew -221/4096 from it;
            the off-diagonal at w = 1/16 is (1 - w)(3/4) = (15/16)(3/4) =
            45/64, and the value is -2021/4096 -- which is what the line's own
            second form already gave, so the verdict FAILS is unchanged. NO
            FROZEN VALUE MOVES: neither number appears in any field of this
            case, whose frozen `lift_weight` is None and whose
            `refused_predicate` names positivity either way.]
  w = 1/8 : (1/16)^2 - (21/32)^2 = 1/256 - 441/1024 = -437/1024 < 0.  FAILS.
  w = 1/4 : (1/8)^2 - (9/16)^2 = 1/64 - 81/256 = -77/256 < 0.         FAILS.
  w = 1/2 : (1/4)^2 - (3/8)^2 = 1/16 - 9/64 = 4/64 - 9/64 = -5/64 < 0. FAILS.
EVERY RUNG OF THE LADDER FAILS, and 2^-1 is the largest rung there is, so the
family is not emitted. The general shape of the mixture at y0 is
[[w/2, (1-w)3/4], [(1-w)3/4, w/2]], whose e_2 is (w/2)^2 - ((1-w)3/4)^2; that is
non-negative only for w >= 3/5, and NO DYADIC RUNG 2^-k WITH k >= 1 IS AT LEAST
3/5. The refusal is therefore structural and not an artefact of kappa = 4:
raising kappa only ADDS SMALLER rungs.

WHAT IS EMITTED: NOTHING. sec:failclosed: "a failure produces a refusal with a
machine-readable reason and NO ARTIFACT". No Delta_s is recorded, because
emission_record is part of an artifact that is not produced.

SECOND ROUTE, INDEPENDENT OF THE FIRST: the threshold 3/5. Positivity of
[[a, b], [b, a]] is a >= |b|, so the mixture at y0 is positive iff
w/2 >= (1-w) * 3/4, i.e. 2w >= 3 - 3w, i.e. w >= 3/5. The dyadic ladder at
kappa = 4 is 1/2, 1/4, 1/8, 1/16, and 1/2 < 3/5, so no rung qualifies -- the
same answer as the four minor computations above, reached without computing a
determinant.""",
)

EMISSION_NORMALIZER_CASES: tuple[EmissionNormalizerCase, ...] = (
    EMITNORM_ON_LATTICE,
    EMITNORM_ROUNDED,
    EMITNORM_LIFTED,
    EMITNORM_REFUSED,
)

#: THE ONE EMITTED NUMBER THAT IS NOT FORMED IN THE EXACT SUBSTRATE, exhibited
#: on the smallest object that shows it: one entry's displacement.
#: thm:emit (i): eq:displacement "takes an entrywise maximum MODULUS of a
#: complex difference, WHICH IS A SQUARE ROOT OF AN EXACT RATIONAL AND IN
#: GENERAL LEAVES the field". Frozen as the exact square and the binary64 root,
#: because the square is what the substrate holds and the root is what
#: emission_record carries.
EMITNORM_IRRATIONAL_DISPLACEMENT: tuple[tuple[str, object], ...] = (
    ("entry_displacement_real", F(1, 64)),
    ("entry_displacement_imag", F(1, 64)),
    ("modulus_squared_exact", F(1, 2048)),
    ("modulus_is_rational", False),
    ("modulus_closed_form", "sqrt(2) / 64"),
    ("modulus_binary64_repr", "0.02209708691207961"),
    (
        "derivation",
        """\
A SINGLE ENTRY SUFFICES, and freezing a whole complex family would add nothing.
Let one entry of the declared family differ from the constructed one by
(1/64) + i(1/64), both parts on the kappa = 6 lattice and each one lattice step
at kappa = 6. Eq. eq:displacement takes the entrywise maximum MODULUS, and the
modulus of that difference is sqrt((1/64)^2 + (1/64)^2) = sqrt(2/4096) =
sqrt(1/2048) = sqrt(2)/64. THE SQUARE, 1/2048, IS AN EXACT RATIONAL AND LIVES IN
THE SUBSTRATE; THE ROOT IS IRRATIONAL AND DOES NOT. That is precisely
sec:openitems's "an entrywise maximum MODULUS, hence THE SQUARE ROOT OF AN EXACT
RATIONAL AND IN GENERAL IRRATIONAL, which ADR-0008 Section 7.1 records in terms
as the one forced divergence of the exact kernel".

WHAT FOLLOWS FOR AN IMPLEMENTATION, and it is the whole point of freezing this:
Delta_s IS EMITTED IN BINARY64 AND IS THE ONLY EMITTED NUMBER THAT MAY BE. Every
other emitted number is exact in the substrate (thm:emit (i)); a code path that
computes Delta_s in the substrate and then rounds is conforming, and one that
lets a float from that computation reach any OTHER emitted number is not.

NOTHING READS IT. sec:openitems: Delta_s "DECIDES NO PREDICATE, NO BOUND,
CONSTANT, CLAIM OR REFUSAL READS IT, and nothing below is proved from its
value". So no test may assert a downstream consequence of its value, and the
binary64 repr above is frozen as A RECORD OF WHAT IS EMITTED and not as an
input to anything.

SECOND ROUTE: 2/4096 = 1/2048 and sqrt(1/2048) = 1/(32 sqrt(2)) = sqrt(2)/64;
sqrt(2) = 1.4142135623730951 in binary64, and 1.4142135623730951/64 =
0.02209708691207961, which is what math.sqrt(1/2048) returns. The two agree
bit for bit.""",
    ),
)


# ---------------------------------------------------------------------------
#  PR-Q2 -- eq:latdown, the downward rounding of p_v, and the recomputed 1 - p
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WeightRoundingCase:
    """One weight routed by eq:weightroute and rounded down by eq:latdown."""

    case_id: str
    claims: tuple[str, ...]
    kappa: int
    q_t: F
    r_min: F
    p_i: F
    #: The EXACT rational of eq:weightroute, before any rounding.
    p_hat: F
    #: True when p_hat is already an integer multiple of 2^-kappa.
    p_hat_on_lattice: bool
    #: The EMITTED weight, eq:latdown applied to p_hat.
    p_emitted: F
    #: p_hat - p_emitted; non-negative by construction, since lat only lowers.
    lowered_by: F
    #: The full weight vector over V = Y x T, zero at every unbounded letter.
    #: The key is the JOINT outcome (letter, setting), as sec:conventions'
    #: `povm_index_convention` requires: "a COMMA denotes a JOINT outcome".
    weights: tuple[tuple[tuple[str, str], F], ...]
    #: p = sum_v p_v, and 1 - p RECOMPUTED from the rounded weights.
    total: F
    complement: F
    derivation: str


WEIGHT_ROUNDING_OFF_LATTICE = WeightRoundingCase(
    case_id="WR1-p-hat-off-the-lattice",
    claims=("PR6", "PR13"),
    kappa=4,
    q_t=F(1, 2),
    r_min=F(1, 8),
    p_i=F(1, 4),
    p_hat=F(11, 64),
    p_hat_on_lattice=False,
    p_emitted=F(1, 8),
    lowered_by=F(3, 64),
    weights=((("y0", "t0"), F(1, 8)), (("y1", "t0"), F(0))),
    total=F(1, 8),
    complement=F(7, 8),
    derivation="""\
sec:consume, Eq. eq:weightroute and Eq. eq:latdown: p^_(y_i,t) =
q_t((1 - r_min,i) p_i + r_min,i), then p_(y_i,t) = lat(p^_(y_i,t)) =
2^-kappa floor(2^kappa p^_(y_i,t)), "THE LARGEST INTEGER MULTIPLE OF 2^-kappa
THAT IS AT MOST p^, THE DOWNWARD ROUNDING onto the declared lattice".

THE DECLARED DATA, all three on the kappa = 4 lattice: q_t = 1/2 = 8/16,
r_min,i = 1/8 = 2/16, p_i = 1/4 = 4/16. The bounded letter is y0 and it is
absorbing; y1 is unbounded and takes weight zero, "p_(y,t) := 0 for every other
(y,t)".

THE EXACT RATIONAL: p^ = (1/2)((1 - 1/8)(1/4) + 1/8) = (1/2)((7/8)(1/4) + 1/8)
= (1/2)(7/32 + 4/32) = (1/2)(11/32) = 11/64. IT IS NOT ON THE LATTICE:
2^4 * 11/64 = 11/4, not an integer. THIS IS THE CASE THE ROUNDING EXISTS FOR,
and it arises from three lattice values because eq:weightroute MULTIPLIES.

THE EMITTED WEIGHT: lat(11/64) = 2^-4 * floor(2^4 * 11/64) = (1/16) floor(11/4)
= (1/16) * 2 = 2/16 = 1/8. The weight is LOWERED by 11/64 - 8/64 = 3/64 > 0.
THE DIRECTION IS THE WHOLE OF WHAT MAKES IT SAFE (sec:consume): "eq:certweights
IS PRESERVED WHEN A CERTIFIED WEIGHT IS LOWERED AND DESTROYED WHEN ONE IS
RAISED, and lat(.) ONLY LOWERS". Rounding to nearest would have given 11/4 ->
3 -> 3/16 = 12/64 > 11/64, RAISING the weight -- the unsafe direction, and the
reason (D-DIR) says "never to nearest".

NO CLAMP IS APPLIED AND NONE IS NEEDED (sec:consume (d)): p^ is a product of
non-negative declared numbers and "THE LARGEST LATTICE NUMBER AT MOST A
NON-NEGATIVE RATIONAL IS ITSELF NON-NEGATIVE". An implementation writing
max(0, .) here has added a clamp `fail_closed` forbids.

THE TOTAL AND ITS COMPLEMENT. p = sum_v p_v = 1/8 + 0 = 1/8, accumulated in the
declared order of V; every summand is a lattice value and kappa + ceil(log2 2) =
5 <= 53, so by lem:latsum the accumulation is exact and "THE NUMBER COMPARED
WITH 1 IS THE REAL TOTAL". p < 1, so the total-weight row admits.
1 - p IS RECOMPUTED from the rounded weights and IS NEVER ROUNDED ON ITS OWN:
1 - 1/8 = 7/8 = 14/16, on the lattice. The flag sector's completeness is then an
identity of lattice values: sum_v p_v + (1 - p) = 1/8 + 0 + 7/8 = 1 EXACTLY.

THE COUNTER-EXHIBIT, frozen because thm:emit (iv) names exactly this failure.
Had the complement been rounded independently as lat(1 - p^) = lat(1 - 11/64) =
lat(53/64) = (1/16) floor(53/4) = (1/16) * 13 = 13/16, then
sum_v p_v + lat(1 - p^) = 2/16 + 13/16 = 15/16, leaving a residue of 1/16 =
2^-kappa ON EVERY FLAG SECTOR and failing condition (d). thm:emit (iv):
"ROUNDING THE TWO INDEPENDENTLY WOULD LEAVE A RESIDUE OF UP TO 2^-kappa ON EVERY
FLAG SECTOR AND WOULD FAIL (d) -- which is the case ADR-0008 Section 7.2.1's
condition (D-DIR) closes by requiring THE COMPLEMENTARY QUANTITY TO BE
RECOMPUTED."

SECOND ROUTE, INDEPENDENT OF THE FIRST: integer units of 2^-6. q_t = 32,
r_min = 8, p_i = 16 units of 1/64; (1 - r_min) p_i = (56/64)(16/64) = 896/4096 =
14/64 units... taken in exact rationals to avoid a unit mismatch: 7/8 * 1/4 =
7/32 = 14/64, plus r_min = 8/64, gives 22/64, times q_t = 1/2 gives 11/64 -- 11
units. One lattice step is 4 units, and floor(11/4) = 2, so the emitted weight
is 8 units = 1/8, lowered by 3 units = 3/64. The complement is 64 - 8 = 56
units = 7/8. THE TWO ROUTES AGREE ON EVERY NUMBER.""",
)

WEIGHT_ROUNDING_CASES: tuple[WeightRoundingCase, ...] = (WEIGHT_ROUNDING_OFF_LATTICE,)


# ---------------------------------------------------------------------------
#  PR-Q3 -- lem:latsum at the boundary, and the lattice_exponent domain
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LatticeExponentCase:
    """One declared kappa against the two conditions sec:inputs states."""

    case_id: str
    claims: tuple[str, ...]
    kappa: int | None
    alphabet_sizes: tuple[tuple[str, int], ...]
    #: ceil(log2 max{|V|, |Y|, |T|}), computed by hand.
    ceil_log2_max: int | None
    #: 1 <= kappa <= 53.
    bounds_hold: bool
    #: kappa + ceil(log2 max) <= 53, Eq. eq:latsumcond.
    accumulation_holds: bool
    admitted: bool
    refusal_reason: str | None
    derivation: str


LATSUM_BOUNDARY_53 = LatticeExponentCase(
    case_id="LK1-boundary-53-admit",
    claims=("PR13",),
    kappa=50,
    alphabet_sizes=(("V", 8), ("Y", 4), ("T", 2)),
    ceil_log2_max=3,
    bounds_hold=True,
    accumulation_holds=True,
    admitted=True,
    refusal_reason=None,
    derivation="""\
sec:inputs, `lattice_exponent`: "Validated: 1 <= kappa <= 53 AND
kappa + ceil(log2 max{|V|, |Y|, |T|}) <= 53." Lemma lem:latsum's hypothesis is
Eq. eq:latsumcond, kappa + ceil(log2 L) <= 53 for an accumulation of length L.

THE DECLARATION: kappa = 50, |V| = 8, |Y| = 4, |T| = 2. max = 8 and
ceil(log2 8) = 3 exactly, 8 being a power of two. FIRST CONDITION: 1 <= 50 <= 53
holds. SECOND CONDITION: 50 + 3 = 53 <= 53 holds, WITH NO SLACK. THE DECLARATION
IS ADMITTED, AND THIS IS THE LAST kappa AT THIS ALPHABET SIZE THAT IS.

WHY THE BOUND IS EXACTLY HERE, from lem:latsum's proof: each x_i is an integer
multiple of 2^-kappa with |x_i| <= 1, so each partial sum Sigma_j is one too,
and |Sigma_j| <= sum |x_i| <= L. Hence 2^kappa Sigma_j is an INTEGER with
|2^kappa Sigma_j| <= L * 2^kappa = 8 * 2^50 = 2^53. Every integer of modulus at
most 2^53 is exactly representable in binary64; multiplication by 2^-kappa is
exact and changes no significand; so every partial sum is a binary64 number and
every one of the L - 1 additions is exact. Condition (e) of def:exactadm holds
BY CONSTRUCTION.

THE BOUND IS TIGHT AND NOT CONSERVATIVE. One might fear an accumulation like
8 + 2^-50, which would need 54 significand bits -- but it cannot arise: eight
terms each of modulus at most 1 sum to at most 8, so a partial sum strictly
greater than 8 is impossible. THAT IS WHY THE LEMMA'S |Sigma_j| <= L STEP IS
LOAD-BEARING and not decoration.

SECOND ROUTE, INDEPENDENT OF THE FIRST: 8 * 2^50 = 2^3 * 2^50 = 2^53 =
9007199254740992, and the largest integer every one of whose predecessors is
exactly representable in binary64 is 2^53 (2^53 + 1 is the first that is not).
So the worst-case accumulation lands exactly ON the representable boundary and
not past it.""",
)

LATSUM_BOUNDARY_54 = LatticeExponentCase(
    case_id="LK2-boundary-54-refuse",
    claims=("PR13",),
    kappa=51,
    alphabet_sizes=(("V", 8), ("Y", 4), ("T", 2)),
    ceil_log2_max=3,
    bounds_hold=True,
    accumulation_holds=False,
    admitted=False,
    refusal_reason="lattice_exponent_not_declared",
    derivation="""\
THE SAME DECLARATION WITH kappa ONE HIGHER. FIRST CONDITION: 1 <= 51 <= 53 still
holds -- SO THE REFUSAL IS NOT ABOUT THE RANGE. SECOND CONDITION: 51 + 3 = 54 >
53, so eq:latsumcond FAILS and the declaration is refused
`lattice_exponent_not_declared`. sec:inputs: the second inequality "is refused
UNDER THE SAME REASON" as a missing kappa, so no new string is invented for it.

A CONCRETE WITNESS THAT THE SUM REALLY ROUNDS, because the row would otherwise
be a bound with no exhibit. Take L = 8 lattice values at kappa = 51:
x_1 = x_2 = x_3 = x_4 = 1, x_5 = 2^-51, x_6 = x_7 = x_8 = 0. Every one satisfies
eq:latinv (|x| <= 1 and 2^51 x an integer). The fifth partial sum is exactly
4 + 2^-51, whose value in units of 2^-51 is 2^53 + 1 = 9007199254740993 --
THE SMALLEST POSITIVE INTEGER THAT IS NOT EXACTLY REPRESENTABLE IN BINARY64. So
the addition 4.0 + 2^-51 cannot return its exact sum: IEEE-754 returns the
correctly rounded value, which is 4.0. THE ADDITION IS INEXACT AND CONDITION (e)
FAILS.

CONTRAST WITH LK1 AT kappa = 50, where the same shape gives 4 + 2^-50, whose
value in units of 2^-50 is 2^52 + 1 <= 2^53, exactly representable, and
4.0 + 2^-50 = 4.000000000000001 -- an exact addition. ONE STEP OF kappa IS THE
WHOLE DIFFERENCE.

WHAT THE ROW PROTECTS, and it is why it runs first: this is A CONDITION ON
DECLARED COUNTS AND CARRIES NO ARITHMETIC (sec:inputs), decided before anything
is constructed. If it were not decided, condition (e) would fail LATER, on the
emitted family, under a different reason string and after the construction had
run.

SECOND ROUTE, INDEPENDENT OF THE FIRST: 8 * 2^51 = 2^54 = 18014398509481984 >
2^53 = 9007199254740992, so lem:latsum's bound |2^kappa Sigma_j| <= L 2^kappa <=
2^53 is unavailable and the lemma gives nothing. That is the same conclusion
reached without exhibiting an accumulation.""",
)

LATTICE_EXPONENT_CASES: tuple[LatticeExponentCase, ...] = (
    LatticeExponentCase(
        case_id="LK3-kappa-zero-refuse",
        claims=("PR13",),
        kappa=0,
        alphabet_sizes=(("V", 2), ("Y", 2), ("T", 1)),
        ceil_log2_max=1,
        bounds_hold=False,
        accumulation_holds=True,
        admitted=False,
        refusal_reason="lattice_exponent_not_declared",
        derivation="""\
1 <= kappa fails at kappa = 0. The accumulation condition 0 + 1 = 1 <= 53 holds,
so THE TWO CONDITIONS ARE INDEPENDENT and a declaration may fail either alone.
kappa = 0 would make the lattice the integers, on which the only admissible
entries are -1, 0 and 1 -- not a repair but a degenerate model, and the contract
excludes it by range rather than by argument.""",
    ),
    LatticeExponentCase(
        case_id="LK4-kappa-54-refuse",
        claims=("PR13",),
        kappa=54,
        alphabet_sizes=(("V", 2), ("Y", 2), ("T", 1)),
        ceil_log2_max=1,
        bounds_hold=False,
        accumulation_holds=False,
        admitted=False,
        refusal_reason="lattice_exponent_not_declared",
        derivation="""\
kappa <= 53 fails at 54, AND the accumulation condition 54 + 1 = 55 > 53 fails
too. BOTH FAIL, and the refusal carries one reason string either way. The
first-condition failure is the substantive one: a significand of 54 bits is not
a binary64 number at all, so no entry could satisfy eq:latinv.""",
    ),
    LatticeExponentCase(
        case_id="LK5-kappa-absent-refuse",
        claims=("PR13",),
        kappa=None,
        alphabet_sizes=(("V", 2), ("Y", 2), ("T", 1)),
        ceil_log2_max=1,
        bounds_hold=False,
        accumulation_holds=False,
        admitted=False,
        refusal_reason="lattice_exponent_not_declared",
        derivation="""\
sec:inputs: "REQUIRED; THERE IS NO DEFAULT AND NO FALLBACK... A request that
does not carry it is refused `lattice_exponent_not_declared` BEFORE ANYTHING IS
CONSTRUCTED, because A DEFAULTED LATTICE WOULD DECIDE A SECURITY-RELEVANT
PREDICATE ON NOBODY'S AUTHORITY." sec:conventions `fail_closed` names it in the
no-repair list: "NO DEFAULT IS SUBSTITUTED FOR A MISSING DATUM -- INCLUDING THE
DECLARED LATTICE EXPONENT ITSELF, WHOSE ABSENCE IS A REFUSAL."
THE PLATFORM VALUE k = 40 IS NOT A DEFAULT THIS MODULE MAY APPLY: ADR-0008
Section 7.2.1 "FIXES NO VALUE: it requires ONE DECLARED EXPONENT with
kappa <= 53 and PUTS THE DECLARING ON THE PRODUCER", and 40 is the measured rule
of that section's preamble, read by THE INSTANCE THAT DECLARES.""",
    ),
    LATSUM_BOUNDARY_53,
    LATSUM_BOUNDARY_54,
    LatticeExponentCase(
        case_id="LK6-fixture-kappa-admit",
        claims=("PR13",),
        kappa=4,
        alphabet_sizes=(("V", 4), ("Y", 4), ("T", 1)),
        ceil_log2_max=2,
        bounds_hold=True,
        accumulation_holds=True,
        admitted=True,
        refusal_reason=None,
        derivation="""\
THE BAND'S OWN FIXTURE EXPONENT, checked against its own rule so that the fixture
is not exempt from what it pins. kappa = 4 with the largest alphabet of the band
(|Y| = 4 in EN2): 1 <= 4 <= 53, and 4 + ceil(log2 4) = 4 + 2 = 6 <= 53. Every
EN and WR case above is therefore a declaration this row admits.""",
    ),
)


# ---------------------------------------------------------------------------
#  PR-Q4 -- cor:entries, the emitted constraint entries as scalar c_k
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScalarEntryCase:
    """One emitted CList entry at 1.0.0: the third component is a REAL SCALAR."""

    case_id: str
    claims: tuple[str, ...]
    ohat: str
    relation: str
    #: The emitted constant. A REAL SCALAR IN BOTH SOURCE MODES.
    c_k: F
    #: The declared form tag, emitted with the entry in trusted-source mode.
    form_tag: str | None
    source_mode: str
    #: The 0.3.0 constant this replaces, frozen so the change is checkable.
    superseded_constant_0_3_0: str
    entry_count: int
    derivation: str


ENTRY_FLAG_SECTOR = ScalarEntryCase(
    case_id="SE1-flag-sector-entry",
    claims=("PR11", "PR13"),
    ohat="F^FSS_o|_nb - p_o Pi_{nb,flag}",
    relation=">=",
    c_k=F(0),
    form_tag="homogeneous",
    source_mode="trusted",
    superseded_constant_0_3_0="-eta_o (Cor. cor:tolentries (i), Eq. eq:tolfss)",
    entry_count=1,
    derivation="""\
cor:entries (i), Eq. eq:entryfss: Lambda-dagger(O^) =
((blk M'^{<=N}_{o|nb}) (+) (blk M'^{>N}_{o|nb} - p_o 1)) (x) N_nb >= 0,
"SO THE ENTRY IS EMITTED AS (O^, >=, 0)".

THE PROOF OF THE BOUND, in two pieces, and both are decided rather than
estimated: blk M'^{<=N}_{o|nb} >= 0 by def:emitnorm (4) -- the emission
normalizer's own positivity step, decided by eq:psdtest -- and
blk M'^{>N}_{o|nb} - p_o 1 >= 0 by eq:certroute, which is a statement about the
ABOVE-CUTOFF blocks, "WHICH THE NORMALIZER DOES NOT TOUCH". A direct sum of
positive semidefinite blocks is positive semidefinite, and X >= 0 with N >= 0
gives X (x) N >= 0.

THE CONSTANT IS 0 AND IS EXACT. cor:entries, closing paragraph: "NO CONSTANT IS
SHIFTED AT 1.0.0. Versions 0.2.0--0.3.0 shifted each of (i), (ii) and (iv) by a
declared amount... both shifts paid for A DISPLACEMENT BETWEEN THE FAMILY A
CERTIFICATE WAS ASSERTED OF AND THE NUMBERS THE OPERATOR WAS ASSEMBLED FROM.
UNDER EXACT ADMISSIBILITY THERE IS NO SUCH DISPLACEMENT: each certificate is
discharged FOR THE EMITTED NUMBERS THEMSELVES."

WHAT CHANGED, AND IT IS A NUMBER: at 0.3.0 this entry was emitted at -eta_o and
band 2 froze it under TOL_ENTRY_FLAG. AT 1.0.0 IT IS EMITTED AT 0. 0 is on
every lattice (2^kappa * 0 = 0), so no rounding rule reaches it.

THE THIRD COMPONENT IS A SCALAR AND THE FORM IS EMITTED WITH THE ENTRY.
sec:outputs: in trusted-source mode the entry carries "the HOMOGENEOUS form of
meat-core 1.0.0 Def. def:homog -- THE ENTRY DECLARES THE REAL c_k AND THE
RIGHT-HAND SIDE Theta_k := c_k tau_A IS CONSTRUCTED BY THE CONSUMER from it and
from THE CONSUMER'S OWN tau_A"; the tag value `homogeneous` is emitted "BECAUSE
THE CONSUMER'S PART (i) SECURITY GATE IS A TYPE CHECK ON THE DECLARED TAG AND
COMPARES NO NUMBERS". THIS MODULE EMITS NO OPERATOR Theta_k IN EITHER MODE.

SECOND ROUTE, INDEPENDENT OF THE FIRST: the entry's constant is whatever the
certificate eq:certificate is discharged at, and the certificate here is
POSITIVITY (cor:transported case (ii), cor:pullback (ii)), whose constant is 0
by definition of the case. No arithmetic produces it and none can move it; the
0.3.0 shift came from thm:tolerance (iv) and nothing else, and that theorem is
gone.""",
)

ENTRY_PROBE_EXPECTATION = ScalarEntryCase(
    case_id="SE2-probe-expectation-entry",
    claims=("PR11", "PR13"),
    ohat="sum_y F_(y,t)",
    relation="=",
    c_k=F(1, 2),
    form_tag="homogeneous",
    source_mode="trusted",
    superseded_constant_0_3_0=(
        "a PAIR: (O^, >=, q_t - delta_t) and (O^, <=, q_t + delta_t) with "
        "delta_t = |Y| q_t dcf eps_op (Cor. cor:tolentries (ii), Eq. eq:tolprobe)"
    ),
    entry_count=1,
    derivation="""\
cor:entries (ii), Eq. eq:entryprobe: Lambda-dagger(O^) = q_t 1_B EXACTLY, "so
the entry is emitted as THE SINGLE EQUALITY ENTRY (O^, =, q_t) AT THE DECLARED
q_t". The declared q_t of this fixture is 1/2, on the kappa = 4 lattice as
8/16, so the emitted constant is c_k = 1/2 and no rounding rule reaches it.

WHY THE PULL-BACK IS EXACT, and both halves matter. The nb term is
q_t 1_C (x) N_nb: BELOW THE CUTOFF by def:emitnorm (3), "which restores
completeness AT EACH SETTING and therefore gives sum_y blk M'^{=m}_{(y,t)|nb} =
q_t 1_{C_m} for every m <= N"; ABOVE THE CUTOFF by step 2 of sec:consume with
column-stochasticity of R^cg, "THAT BLOCK BEING UNTOUCHED". For a blinded b the
entry is emitted only where sec:failclosed's certificate row has DISCHARGED
eq:branchprobeweight, "and the normalizer does not read a branch POVM", so
sum_y M'_(y,t)|b = sum_y M_(y,t)|b = q_t 1_C there as well. With
sum_b N_b = 1_Bl the total is q_t 1_B.

THAT IS WHY def:emitnorm (3) RESTORES COMPLETENESS PER SETTING AND NOT MERELY
OVER V: "the probe-expectation entry of cor:entries (ii) READS sum_y F_(y,t) AT
A FIXED t; summing over t and using sum_t q_t = 1 THEN GIVES COMPLETENESS OVER V
AS WELL". A normalizer that restored completeness only over V would break this
entry and nothing else -- which makes this the entry that pins step (3)'s
quantifier.

WHAT CHANGED, AND IT IS A COUNT AS WELL AS A NUMBER: at 0.3.0 this was TWO
entries, an upper and a lower inequality straddling q_t, frozen by band 2 as
TOL_ENTRY_PROBE_T0 and TOL_ENTRY_PROBE_T1. AT 1.0.0 IT IS ONE EQUALITY ENTRY.
An implementation that keeps the pair emits a list the contract does not
license, and one that keeps the pair's constants emits numbers that do not
exist.

AN OFF-LATTICE q_t CANNOT ARISE HERE: sec:inputs requires every q_t to satisfy
eq:latinv, decided by the probe-weights row. So the equality entry's constant is
always on the lattice, and cor:entries (iv)'s rule that "AN EQUALITY ENTRY WHOSE
CONSTANT IS OFF THE LATTICE IS REFUSED RATHER THAN SPLIT INTO A PAIR" bites only
on a CALLER-DECLARED constant, never on this one.

SECOND ROUTE, INDEPENDENT OF THE FIRST: the constant is the declared q_t and
nothing else; it enters the artifact by being READ, not computed. Its value is
1/2 because the fixture declares 1/2. There is no arithmetic to check, which is
itself the point cor:entries makes about every constant this module emits.""",
)

SCALAR_ENTRY_CASES: tuple[ScalarEntryCase, ...] = (
    ENTRY_FLAG_SECTOR,
    ENTRY_PROBE_EXPECTATION,
)


# ---------------------------------------------------------------------------
#  PR-Q5 -- the 1.0.0 vocabulary: rows, reasons, keys, tier
# ---------------------------------------------------------------------------

#: sec:failclosed at 1.0.0: FOUR strings added, ONE removed.
REFUSAL_REASONS_ADDED_1_0_0: tuple[str, ...] = (
    "lattice_exponent_not_declared",
    "requested_assurance_shelved",
    "declaration_not_exactly_admissible",
    "emitted_family_not_admissible",
)
REFUSAL_REASONS_REMOVED_1_0_0: tuple[str, ...] = ("declaration_outside_tolerance",)

#: THE FULL 30-STRING VOCABULARY at 1.0.0, in the contract's own row order.
#: Built by transformation of the 0.3.0 tuple rather than restated, so the
#: twenty-six strings that do not move cannot drift.
REFUSAL_REASONS_1_0_0: tuple[str, ...] = (
    "lattice_exponent_not_declared",
    "requested_assurance_shelved",
    *(
        "declaration_not_exactly_admissible"
        if reason == "declaration_outside_tolerance"
        else reason
        for reason in REFUSAL_REASONS_0_3_0
    ),
    "emitted_family_not_admissible",
)

#: A DATED NOTE BESIDE :data:`REFUSAL_REASONS_1_0_0`, NOT A FIELD INSIDE IT.
#: The tuple above is built by APPENDING ``emitted_family_not_admissible`` to
#: the transformed 0.3.0 tuple, so it stands LAST; ``sec:failclosed`` prints
#: that row FOURTH -- immediately after the declared-blocks row and before the
#: fibre row -- so it stands SEVENTH of thirty in the contract's own order.
#:
#: **THE CONTENT IS IDENTICAL AND ONLY THE ORDER DIFFERS**: the two tuples
#: agree as sets, on all thirty strings, and `interface.yaml`'s
#: ``fail_closed.refusal_reasons`` carries the contract's order.
#:
#: WHY IT IS RECORDED RATHER THAN FIXED. The order is not decoration:
#: ``RULE_ORDER`` is built from it and
#: ``VerificationReport.refusal`` is "THE FIRST REFUSAL IN THIS ORDER", so the
#: order decides WHICH REASON A CALLER RECEIVES when two rows would refuse.
#: Band B2 run B found the divergence, does not edit a frozen value under the
#: two-instance freeze, and does not weaken the check either:
#: ``test_refusal_reason_totality_registry_equals_interface`` asserts the
#: CONTRACT'S order against a literal transcription of the eleven tabulars and
#: compares this tuple for CONTENT as a set. Correcting the order here is run
#: A's, or a later band's, under a mark of its own.
#:
#: Recorded by band B2 run B.
REFUSAL_REASONS_1_0_0_ORDER_NOTE: str = (
    "REFUSAL_REASONS_1_0_0 lists emitted_family_not_admissible LAST; "
    "sec:failclosed introduces it SEVENTH of thirty, immediately after "
    "declaration_not_exactly_admissible and before bound_set_not_a_fibre. "
    "Content identical, order divergent; interface.yaml carries the "
    "contract's order and the totality test asserts it. Recorded "
    "by band B2 run B under the "
    "superseded-by-scope discipline: a note BESIDE the entry, never a field "
    "inside one."
)

#: THE ROW COUNT AT 1.0.0: 28, from 25. THREE ROWS ADDED (the lattice-exponent
#: row, which RUNS FIRST; the requested-assurance row; the emitted-family row)
#: and ONE REPLACED IN PLACE (the declared-blocks row). The two counts do NOT
#: move together here: three rows against four strings, because the replaced
#: row's string is renamed.
FAIL_CLOSED_ROW_COUNT_1_0_0: int = 28
FAIL_CLOSED_ROWS_ADDED_1_0_0: tuple[tuple[str, str], ...] = (
    ("the lattice-exponent row (RUNS FIRST)", "lattice_exponent_not_declared"),
    ("the requested-assurance row", "requested_assurance_shelved"),
    ("the emitted-family row (THE SECOND GATE)", "emitted_family_not_admissible"),
)
FAIL_CLOSED_ROWS_REPLACED_1_0_0: tuple[tuple[str, str, str], ...] = (
    (
        "the declared-blocks row",
        "declaration_outside_tolerance",
        "declaration_not_exactly_admissible",
    ),
)

#: THE TABULAR COUNT, frozen only so that a reader counting tables does not
#: conclude the rule set grew by six: sec:failclosed goes from FIVE tabulars to
#: ELEVEN, and every split is page fit.
FAIL_CLOSED_TABULAR_COUNT_1_0_0: int = 11

#: Section sec:inputs at 1.0.0: SEVENTEEN keys, the same count. `lattice_exponent`
#: REPLACES `operator_tolerance` in the request group -- a different datum with a
#: different type, domain and refusal reason, NOT a rename.
INPUT_KEYS_1_0_0: tuple[str, ...] = tuple(
    "lattice_exponent" if key == "operator_tolerance" else key
    for key in INPUT_KEYS_0_3_0
)

#: Section sec:outputs at 1.0.0: EIGHTEEN keys, the same count.
#: `emission_record` RENAMES AND RE-TYPES `operator_tolerance_record` in place.
OUTPUT_KEYS_1_0_0: tuple[str, ...] = tuple(
    "emission_record" if key == "operator_tolerance_record" else key
    for key in OUTPUT_KEYS_0_3_0
)

#: Section sec:conventions at 1.0.0: FOURTEEN bullets, from thirteen.
#: `exact_arithmetic` is REPLACED by `numerical_model`; `summation_order` is
#: ADDED; the artifact binding moves.
CONVENTIONS_1_0_0: dict[str, str] = {
    **{k: v for k, v in CONVENTIONS_0_3_0.items() if k != "exact_arithmetic"},
    "numerical_model": "binary64 on the wire, exact rational arithmetic inside",
    "summation_order": "declared",
    "artifact_bindings.mathematical_spec_version": "proof-reductions@1.0.0",
}
CONVENTION_BULLET_COUNT_1_0_0: int = 14
CONVENTION_BULLET_COUNT_0_3_0: int = 13

#: Section sec:assumptions at 1.0.0: NINE rows, from ten. A-OPTOL is REMOVED and
#: NOTHING REPLACES IT; A-RECV's Supports range gains PR13.
ASSUMPTION_KEYS_REMOVED_1_0_0: tuple[str, ...] = ("A-OPTOL",)
ASSUMPTION_COUNT_1_0_0: int = 9
NEVER_VERIFIED_1_0_0: tuple[str, ...] = ("A-RECV", "A-BLIND")
A_RECV_SUPPORTS_1_0_0: tuple[str, ...] = ("PR6", "PR9", "PR11", "PR13")

#: THE THIRTEEN SUPPLIER MACHINE KEYS the emitted ledger now carries, from
#: Assumption A-RECV, verbatim and in the contract's order. FOUR OF THEM DID NOT
#: CROSS THE DOCKING BOUNDARY BEFORE 1.0.0.
INHERITED_RECEIVER_KEYS_1_0_0: tuple[str, ...] = (
    "receiver_trusted_exact",
    "passive_optics",
    "undeclared_inputs_vacuum",
    "no_undeclared_paths",
    "threshold_memoryless_detectors",
    "mode_insensitive_ports",
    "exact_parameters",
    "device_not_adversarial",
    "acyclic_element_graph",
    "probe_fock_diagonal",
    "round_homogeneity",
    "floating_point_evaluation",
    "exact_window_eigenvalue_slack",
)
INHERITED_RECEIVER_KEYS_NEW_AT_1_0_0: tuple[str, ...] = (
    "acyclic_element_graph",
    "round_homogeneity",
    "floating_point_evaluation",
    "exact_window_eigenvalue_slack",
)

#: sec:claims and sec:openitems at 1.0.0. THE CEILING MOVES AND THE ARITHMETIC
#: DOES NOT: the `open` count is 0 + 0 = 0 as before, and `certified` is a
#: SHELVED NAME.
MAX_ATTAINABLE_TIER_1_0_0: str = "first-order"
MAX_ATTAINABLE_TIER_0_3_0: str = "certified"
LIVE_TIERS_1_0_0: tuple[str, ...] = ("estimate", "first-order")
SHELVED_TIER_1_0_0: str = "certified"
OPEN_CLAIM_COUNT_1_0_0: int = 0

#: sec:inputs `requested_assurance` at 1.0.0.
REQUESTED_ASSURANCE_VALUES_1_0_0: tuple[str, ...] = ("estimate", "first-order")
REQUESTED_ASSURANCE_REFUSED_1_0_0: tuple[tuple[str, str], ...] = (
    ("certified", "requested_assurance_shelved"),
)

#: THE THREE PINS at 1.0.0.
SUPPLIER_PIN_1_0_0: str = "receiver-povm 0.3.0"
CONSUMER_PIN_1_0_0: str = "meat-core 1.0.0"
SPEC_VERSION_1_0_0: str = "proof-reductions@1.0.0"

#: THE LINK STATUS VOCABULARY IS UNCHANGED, and `certified_outer` SURVIVES THE
#: SHELVING OF THE `certified` TIER. Frozen as a negative fact because it is the
#: one place the tier change could be wrongly propagated.
LINK_STATUS_VOCABULARY_1_0_0: tuple[str, ...] = LINK_STATUS_VOCABULARY
CERTIFIED_OUTER_IS_NOT_A_TIER: str = """\
sec:outputs, `status`: "NONE OF THE THREE IS A RESULT TIER: this is a LINK
status, it says whether the link's defining identity carries an error term, and
THE SHELVING OF THE `certified` RUNG LEAVES IT UNTOUCHED -- `certified_outer` is
THE RESERVED DOCKING POINT OF THE APPROXIMATE-SQUASHING DEFERRAL and is KEPT FOR
THAT REASON." sec:versionrecord says it from the other side: the value "is
UNAFFECTED and is KEPT... and HAS NEVER NAMED A RESULT TIER." An implementation
that renames or drops `certified_outer` while shelving the tier has removed a
live docking point."""


# ===========================================================================
#  SUPERSESSION at 1.0.0 -- what the amendment invalidates, MARKED not deleted
# ===========================================================================
#
#  TWO KINDS OF MARK, and the distinction is what keeps every frozen case
#  byte-immutable.
#
#  1. SUPERSESSIONS_1_0_0 -- individual symbols the amendment invalidates,
#     in the same dataclass bands 2 and 3 used.
#  2. SCOPE_MARKS_1_0_0 -- a LIST BESIDE THE ENTRIES, never a field inside one,
#     for the wholesale removal of the 0.2.0-0.3.0 tolerance apparatus. The
#     apparatus is out of scope at 1.0.0, not wrong at 0.3.0.

#: THE ONE LINE the scope marks are made under, quoted by every entry.
SCOPE_MARK_AUTHORITY_1_0_0: str = (
    "Superseded-by-scope at contract 1.0.0. The declared operator "
    "tolerance and its constant-shifting apparatus LEAVE THE CONTRACT "
    "(sec:versionrecord, first decision); these values remain correct of "
    "contract 0.3.0 and are pinned to a version no longer in force. Authority: "
    "the run A / run B split and the two-instance freeze, kept wherever a band "
    "writes or changes a frozen expected value."
)

#: EVERY REGISTRY SYMBOL THAT PINS THE 0.3.0 TOLERANCE APPARATUS, marked
#: superseded-by-scope. NOT ONE OF THEM IS EDITED OR DELETED: the mark is here,
#: beside them, and the values stay byte-for-byte as bands 2 and 3 froze them.
SCOPE_MARKS_1_0_0: tuple[tuple[str, str, str], ...] = (
    (
        "WEIGHT_ROUTE_CASES: the `emitted_weights` and `total_weight` fields",
        "superseded-by-scope",
        "ADDED BY BAND B2 RUN B, which found the gap while "
        "re-pointing the weight-route golden test. "
        "1.0.0 SPLITS THE QUANTITY THESE FIELDS FREEZE IN TWO. "
        "Eq. eq:weightroute now ends `p_(y_i,t) := lat(p^_(y_i,t))` with "
        "Eq. eq:latdown's DOWNWARD rounding onto the declared lattice, and "
        "sec:consume says in terms: 'THE EMITTED WEIGHT IS p_(y_i,t) AND NOT "
        "p^_(y_i,t), and the direction of that rounding is the whole of what "
        "makes it safe.' So the frozen values -- 29/300, 29/600, 1/3, 1/6, "
        "3/20, 1/20, 3/40, 1/40 and the totals -- ARE p^ AT 1.0.0 AND NOT p: "
        "not one of them is dyadic, so lat() strictly lowers every one at "
        "every kappa. THE NUMBERS ARE NOT EDITED AND ARE NOT WRONG; what the "
        "amendment renames is what they are the weight OF. Run B asserts them "
        "as p^ and asserts p = lat(p^) against the contract's rule beside "
        "them, which tests strictly more than the 0.3.0 assertion did. "
        "A SECOND, INDEPENDENT REASON THESE CASES CANNOT BE RUN END TO END AT "
        "1.0.0: RC2 and RC1MIN declare q_t in {2/3, 1/3}, which is on no "
        "dyadic lattice and is not a binary64 number at all, so sec:failclosed "
        "row 15 refuses them under `probe_weights_ill_formed` (def:exactadm "
        "(b) names the q_t among the declared real scalars eq:latinv is about, "
        "and it is the one of them that is EMITTED, as cor:entries (ii)'s "
        "constant). A 1.0.0-conforming end-to-end fixture needs DYADIC device "
        "parameters, which is a fresh Band-1 freeze and NOT run B's to write "
        "under the two-instance freeze.",
    ),
    (
        "TOLERANCE_ROW_CASES and every ToleranceRowCase instance",
        "superseded-by-scope",
        "The four necessary-condition rows of prop:tolrows, decided at a "
        "declared eps_op. THE PREDICATE IS GONE: def:exactadm decides FIVE "
        "conjuncts AT ZERO and the refusal string is renamed "
        "`declaration_not_exactly_admissible`. Run B RETIRES these and points "
        "the declared-blocks row at the new case set.",
    ),
    (
        "TOLERANCE_ENTRY_CASES and every ToleranceEntryCase instance",
        "superseded-by-scope",
        "The shifted constants of cor:tolentries: -eta_o, the +-delta_t pair, "
        "and delta(O^). cor:entries: 'NO CONSTANT IS SHIFTED AT 1.0.0.' "
        "Replaced by SCALAR_ENTRY_CASES above.",
    ),
    (
        "TOLERANCE_SCOPE_CASES and every ToleranceScopeCase instance",
        "superseded-by-scope",
        "The per-claim classification by tolerance exposure. rem:claimscope: "
        "'Version 0.3.0's classification of the claims BY TOLERANCE EXPOSURE... "
        "ARE GONE WITH THE TOLERANCE: under exact decisions THERE IS NO PARTIAL "
        "EXPOSURE LEFT TO CLASSIFY.'",
    ),
    (
        "the tau-derived constants: every frozen dcf, eta, eta_v and delta_t",
        "superseded-by-scope",
        "lem:tolprop with eq:dcf and eq:etadef is gone from the contract, and "
        "with it every number derived through it. NO REPLACEMENT CONSTANT "
        "EXISTS: the 1.0.0 emission carries a per-block DISPLACEMENT Delta_s, "
        "which is a record and not a bound, and nothing reads it.",
    ),
    (
        "`declaration_outside_tolerance` wherever it is frozen as a reason string",
        "superseded-by-scope",
        "Removed from the vocabulary at 1.0.0 and replaced in place by "
        "`declaration_not_exactly_admissible`. REFUSAL_REASONS_0_3_0 keeps it "
        "and is not edited; REFUSAL_REASONS_1_0_0 does not.",
    ),
    (
        "rem:obstructiondecide read at a declared tolerance",
        "superseded-by-scope",
        "The declared-relation row is decided EXACTLY at 1.0.0 as "
        "rem:obstructiondecide states it, with no tolerance anywhere: 'THE ONE "
        "ROW WHOSE DECISION COULD HAVE BEEN LOOSE AT NO COST, AND IT IS EXACT "
        "ANYWAY.' The frozen obstruction values are UNTOUCHED -- see "
        "NOT_SUPERSEDED_AND_WHY_1_0_0 -- and only the reading at a tolerance "
        "is marked.",
    ),
    (
        "GROUP PR-O IN ITS ENTIRETY",
        "superseded-by-scope",
        "The charter names this group. PR-O is band 2's operator-tolerance "
        "group and every value in it is pinned to an apparatus 1.0.0 removes. "
        "The values remain correct of contract 0.2.0 and 0.3.0 and are kept "
        "unedited as the record of two signed versions; NOTHING IN PR-O IS "
        "EVIDENCE FOR ANY 1.0.0 BEHAVIOUR.",
    ),
    (
        "SPEC_VERSION_0_3_0, SUPPLIER_PIN_0_3_0, CONSUMER_PIN_0_3_0",
        "superseded-by-scope",
        "Superseded by SPEC_VERSION_1_0_0 (`proof-reductions@1.0.0`), "
        "SUPPLIER_PIN_1_0_0 (`receiver-povm 0.3.0`) and CONSUMER_PIN_1_0_0 "
        "(`meat-core 1.0.0`). The pin move is a version change, not a "
        "mathematical one.",
    ),
    (
        "CONSUMER_STRINGS_NOT_OURS_0_3_0",
        "superseded-by-scope",
        "The four meat-core 0.5.0 strings the 0.3.0 contract quoted are not in "
        "contract.tex 1.0.0 at all: the remark that quoted them is gone with "
        "the consumer-side tolerance. THE NEGATIVE LIST IS THEREFORE EMPTY AT "
        "1.0.0 and the counting trap it guarded has a different shape -- see "
        "CONSUMER_STRINGS_NOT_OURS_1_0_0.",
    ),
    (
        "MAX_ATTAINABLE_TIER_0_3_0 and every frozen `certified` tier value",
        "superseded-by-scope",
        "`certified` is a SHELVED NAME at 1.0.0 and no claim may declare it. "
        "The ceiling is `first-order`. THIS IS A CHANGE OF LADDER AND NOT OF "
        "MATHEMATICS: the `open` count is 0 at both versions. NOTE THAT THE "
        "LINK STATUS `certified_outer` IS NOT AFFECTED -- see "
        "CERTIFIED_OUTER_IS_NOT_A_TIER.",
    ),
)

#: ENTRIES WHOSE SUBJECT SURVIVES BUT WHOSE CLAIM TUPLE IS STALE, marked for
#: RE-POINTING at run B. The value is right; the claim it is filed under moved.
CLAIM_TUPLE_REPOINTS_1_0_0: tuple[tuple[str, str, str, str], ...] = (
    (
        "every case whose claims tuple contains PR13",
        "PR13",
        "PR13",
        "THE ID IS THE SAME AND THE CLAIM IS NOT. PR13 was 'THE DECLARED "
        "OPERATOR TOLERANCE' and is now 'THE NUMBER MODEL: EXACT DECISIONS, AND "
        "THE NUMBERS THIS MODULE EMITS'. A case filed under PR13 at 0.3.0 is "
        "filed under a different statement at 1.0.0, and run B must re-read "
        "each rather than trusting the tuple.",
    ),
    (
        "WeightRouteCase instances (RC1-RC8 and siblings)",
        "PR6",
        "PR6, PR13",
        "The routed weights are unchanged in VALUE -- eq:weightroute's formula "
        "does not move -- but the EMITTED weight is now lat(p^) and the "
        "rounding is PR13's. Every WeightRouteCase whose p^ is off the "
        "kappa-lattice emits a DIFFERENT number at 1.0.0; run B must recompute "
        "each against a declared kappa and re-point the tuple.",
    ),
    (
        "LICENCE_* cases and CertificateCase instances",
        "PR11",
        "PR11, PR13",
        "The certificates are unchanged; the CONSTANTS they are emitted at are "
        "cor:entries' and no longer cor:tolentries'. See SCALAR_ENTRY_CASES.",
    ),
    (
        "LinkRecord instances asserting status = exact",
        "PR12",
        "PR12, PR13",
        "The value `exact` is unchanged; WHAT IT IS ASSERTED OF is not. "
        "thm:emit (iii) makes it an assertion about THE NUMBERS EMITTED for the "
        "declared model M'^ph, where 0.3.0 made it an assertion about the "
        "starred family.",
    ),
    (
        "AssumptionRow instances carrying A-OPTOL in a Supports range",
        "A-OPTOL",
        "(none)",
        "A-OPTOL does not exist at 1.0.0. A-RECV's range gains PR13; no other "
        "range moves. Run B removes the key from the emitted ledger and adds "
        "the thirteen supplier keys.",
    ),
)

#: WHAT IS DELIBERATELY LEFT UNMARKED, and why. Same discipline as bands 2 and 3.
NOT_SUPERSEDED_AND_WHY_1_0_0: tuple[tuple[str, str], ...] = (
    (
        "RELATION_CASES, WP3_STATISTICS, TRANSFER_CASES, OBSTRUCTION_CASES, "
        "MIXTURE_CASE, TOP_ELEMENT, FLAGS_ENOUGH, PINCHING_CASE",
        "rem:claimscope: PR1, PR2, PR3, PR4, PR5, PR7, PR8 and PR10 'READ NO "
        "DECLARED NUMBER and assert nothing about the emitted artifact'. Not "
        "one of these cases reads a tolerance, a lattice or an emitted family, "
        "so the amendment cannot touch them.",
    ),
    (
        "PR_OBSTRUCTION and its irrational p_* = (1 - 1/sqrt2)/2",
        "The counterexample is a statement about what CANNOT be encoded in a "
        "classical-flag target, and its irrational constant is a feature of the "
        "counterexample and not an emitted number. It is unaffected by the "
        "lattice, which constrains what may be DECLARED and EMITTED.",
    ),
    (
        "LINK_KINDS, LINK_STAGES, LINK_STATUS_VOCABULARY, the ten slots, the "
        "three chain conditions",
        "def:link and def:chain are unchanged at 1.0.0. `certified_outer` is "
        "EXPLICITLY KEPT (CERTIFIED_OUTER_IS_NOT_A_TIER), so the status "
        "vocabulary does not move with the tier.",
    ),
    (
        "COLSTOCH_CASES and the descent, monotonicity and absorbing cases",
        "The dark-count rows are unchanged in rule and in reason string. What "
        "1.0.0 adds is the LATTICE INVARIANT on R's entries and the statement "
        "that R^cg inherits column-stochasticity as a THEOREM; neither changes "
        "an admitted or refused declaration among these cases.",
    ),
    (
        "BRANCH_PROBE_WEIGHT cases (TOL2-branchprobe-*)",
        "DELIBERATELY UNMARKED THOUGH THEY CARRY `TOL` IN THEIR IDS. The "
        "condition eq:branchprobeweight and its three refusals are unchanged at "
        "1.0.0; what changes is the REASON the contract gives for the row, from "
        "'weakened by no tolerance' to 'a condition on data this contract "
        "presents no matrix for'. THE CASES ARE STILL CORRECT. Their ids are a "
        "band-2 naming artefact and renaming them would edit a frozen symbol.",
    ),
    (
        "SUPERSESSIONS, SUPERSESSIONS_0_3_0, NOT_SUPERSEDED_AND_WHY and its "
        "0.3.0 sibling",
        "History. They record what two earlier amendments invalidated and are "
        "correct of the versions they name. Band 4 adds beside them and edits "
        "nothing.",
    ),
)

#: THE 1.0.0 COUNTING TRAP, in the shape it now has. A naive sweep of
#: `\\texttt{}` machine strings inside sec:failclosed finds SEVENTEEN that are
#: not refusal reasons. They are frozen as a NEGATIVE list so that the exclusion
#: is a checked fact rather than a remembered one. NOTE THE SHAPE HAS CHANGED:
#: at 0.3.0 the four intruders were the CONSUMER's vocabulary; at 1.0.0 they are
#: this module's own tier names, route values, link kinds, input keys, output
#: key and convention keys, quoted inside the rows' own prose.
CONSUMER_STRINGS_NOT_OURS_1_0_0: tuple[str, ...] = ()
NON_REASON_STRINGS_IN_FAILCLOSED_1_0_0: tuple[str, ...] = (
    "ARCHITECTURE_SPEC.md",
    "receiver-povm",
    "estimate",
    "first-order",
    "certified",
    "encoded",
    "licensed",
    "both",
    "source-map",
    "family-dominating",
    "label-space",
    "dark_count_channel",
    "photon_blocks",
    "route",
    "attack_set_license",
    "fail_closed",
    "numerical_model",
)

SUPERSESSIONS_1_0_0: tuple[Supersession, ...] = (
    Supersession(
        symbol="SPEC_VERSION_0_3_0",
        case_id="artifact-binding",
        superseded_by="1.0.0",
        kind="vocabulary",
        contract_site=(
            "sec:conventions, the artifact-bindings bullet; sec:outputs, the "
            "`mathematical_spec_version` row"
        ),
        replacement=("SPEC_VERSION_1_0_0",),
        still_valid_at_zero_tolerance=False,
        note="`proof-reductions@0.3.0` -> `proof-reductions@1.0.0`. The "
        "convention is written as `proof-reductions@<contract_version>` OF THE "
        "ACCEPTED CONTRACT, so the string moves with the accepted version and "
        "with nothing else. `still_valid_at_zero_tolerance` is False because "
        "there is no tolerance at 1.0.0 for the field to be read at; the field "
        "is band 2's and is kept for shape.",
    ),
    Supersession(
        symbol="REFUSAL_REASONS_0_3_0",
        case_id="refusal-vocabulary",
        superseded_by="1.0.0",
        kind="vocabulary",
        contract_site="sec:failclosed, all eleven tabulars",
        replacement=("REFUSAL_REASONS_1_0_0",),
        still_valid_at_zero_tolerance=False,
        note="27 strings -> 30. FOUR ADDED (`lattice_exponent_not_declared`, "
        "`requested_assurance_shelved`, `declaration_not_exactly_admissible`, "
        "`emitted_family_not_admissible`), ONE REMOVED "
        "(`declaration_outside_tolerance`). Rows 25 -> 28. The 0.3.0 tuple is "
        "NOT edited; the 1.0.0 tuple is built from it by transformation.",
    ),
    Supersession(
        symbol="INPUT_KEYS_0_3_0",
        case_id="input-key-set",
        superseded_by="1.0.0",
        kind="input-shape",
        contract_site="sec:inputs, the `lattice_exponent` row",
        replacement=("INPUT_KEYS_1_0_0",),
        still_valid_at_zero_tolerance=False,
        note="SEVENTEEN KEYS AT BOTH VERSIONS, and the count is the least "
        "interesting fact about the change. `operator_tolerance` -- OPTIONAL, "
        "defaultable to 0, a non-negative scalar the CALLER asserts -- is "
        "replaced by `lattice_exponent` -- REQUIRED, with no default and no "
        "fallback, an integer fixing a SET of representable values, read by "
        "this module's own EMISSION as well as by its admission. NOT A RENAME.",
    ),
    Supersession(
        symbol="OUTPUT_KEYS_0_3_0",
        case_id="output-key-set",
        superseded_by="1.0.0",
        kind="input-shape",
        contract_site="sec:outputs, the `emission_record` row (two tabulars, one key)",
        replacement=("OUTPUT_KEYS_1_0_0",),
        still_valid_at_zero_tolerance=False,
        note="EIGHTEEN KEYS AT BOTH VERSIONS. `operator_tolerance_record` -- "
        "present exactly when eps_op > 0, carrying eps_op, the norm, dcf, the "
        "per-outcome eta_v, the measured defects and the per-entry shift -- is "
        "RENAMED AND RE-TYPED to `emission_record` -- ALWAYS PRESENT, carrying "
        "kappa, the six condition outcomes, Delta_s per preserved block, the "
        "designated element, the lift weight w and vector u, the three ADR-0008 "
        "disclosures and the per-bound rounding directions. NOT ONE FIELD "
        "SURVIVES.",
    ),
    Supersession(
        symbol="CONVENTIONS_0_3_0",
        case_id="convention-set",
        superseded_by="1.0.0",
        kind="vocabulary",
        contract_site="sec:conventions, `numerical_model` and `summation_order`",
        replacement=("CONVENTIONS_1_0_0",),
        still_valid_at_zero_tolerance=False,
        note="THIRTEEN BULLETS -> FOURTEEN. `exact_arithmetic` is REPLACED by "
        "`numerical_model` with its four consequences, and `summation_order: "
        "declared` is ADDED -- the latter binding on the code, because the "
        "consuming contract states its condition (S) ON THE ADDITIONS OF "
        "EXACTLY THAT ACCUMULATION.",
    ),
    Supersession(
        symbol="ASSUMPTION_LEDGER_0_3_0",
        case_id="assumption-ledger",
        superseded_by="1.0.0",
        kind="reading",
        contract_site="sec:assumptions preamble and ledger table",
        replacement=(
            "ASSUMPTION_COUNT_1_0_0",
            "NEVER_VERIFIED_1_0_0",
            "A_RECV_SUPPORTS_1_0_0",
            "INHERITED_RECEIVER_KEYS_1_0_0",
        ),
        still_valid_at_zero_tolerance=False,
        note="TEN ENTRIES -> NINE. A-OPTOL is REMOVED and NOTHING REPLACES IT: "
        "'what it hypothesized is NOW DECIDED'. A-RECV's Supports range gains "
        "PR13 and its If-violated column now says 'AT 1.0.0 IT CARRIES WHAT "
        "A-OPTOL USED TO CARRY BESIDE IT'. The never-verified set drops from "
        "three to two. The EMITTED ledger additionally carries the supplier's "
        "THIRTEEN machine keys, four of which did not cross the boundary "
        "before.",
    ),
    Supersession(
        symbol="MAX_ATTAINABLE_TIER_0_3_0",
        case_id="tier-ceiling",
        superseded_by="1.0.0",
        kind="vocabulary",
        contract_site="sec:claims (the Tier column); sec:openitems",
        replacement=("MAX_ATTAINABLE_TIER_1_0_0", "LIVE_TIERS_1_0_0"),
        still_valid_at_zero_tolerance=False,
        note="`certified` -> `first-order` for the ceiling and for every one of "
        "the thirteen claims. THE RULE DID NOT CHANGE AND NEITHER DID THIS "
        "MODULE'S ARITHMETIC -- the invariant is still defined on the `open` "
        "count, which is zero -- ONLY THE CEILING MOVED. `certified` survives "
        "as a SHELVED NAME and a request carrying it is REFUSED, not demoted.",
    ),
)


# ---------------------------------------------------------------------------
#  Change-request candidates for the 1.0.0 delta
# ---------------------------------------------------------------------------
#
#  As in bands 1-3: for each item run A could not resolve from the interface
#  alone, either THE READING THE TEXT FIXES with its locator, or the item is
#  ROUTED. NOTHING BELOW IS DECIDED HERE. TWO ARE ROUTED AS CHANGE REQUESTS,
#  and BOTH WERE FOUND BY TRYING TO FREEZE A VALUE -- which is what the freeze
#  is for.

CHANGE_REQUEST_CANDIDATES_1_0_0: tuple[tuple[str, str, str], ...] = (
    (
        "(h) the designated-element tie break of def:emitnorm (3)",
        "CHANGE REQUEST -- routed, NOT DECIDED HERE",
        """\
THE SENTENCE: def:emitnorm (3) adds the completeness residue to "THE SINGLE
DESIGNATED ELEMENT A_(y*,t), WHERE y* IS THE OUTCOME OF LARGEST EXACT TRACE IN
THAT BLOCK AT THAT SETTING, CHOSEN BY THAT STATED RULE AND RECORDED WITH THE
SNAP."

THE GAP: the rule is a MAXIMUM and the contract does not say what happens when
it is attained twice. The traces are exact rationals, so the comparison is exact
AND THE TIE IS EXACT TOO -- not a floating-point coincidence a tolerance would
absorb, and not rare: a symmetric two-outcome measurement at a uniform setting
produces one. No other sentence narrows the choice: `summation_order` fixes the
order sums are ACCUMULATED in and says nothing about selecting a maximiser, and
`fail_closed` forbids substituting a default for a MISSING datum while this one
is present and ambiguous.

WHY IT IS PROOF-RELEVANT: two conforming implementations that break the tie
differently ADD THE RESIDUE TO A DIFFERENT ELEMENT, so the emitted target
differs entry by entry in that block, Delta_s can differ in value, and
`emission_record` carries the designated element -- so the difference is visible
in the artifact.

HOW THIS BAND AVOIDED IT: EN2 is built so that the maximiser is UNIQUE both
before and after step (2). That is a property of the fixture and not a fact
about the contract, and it is said in EN2's own derivation.

WHAT IS NEEDED: one sentence in def:emitnorm (3). Candidates, neither chosen
here: THE FIRST IN THE DECLARED ORDER OF V among the maximisers, which invents
no new order; or A REFUSAL, which is fail-closed but would refuse ordinary
declarations. PATCH LEVEL on the first reading -- and THE LEVEL IS THE HUMAN'S
CALL AT G3.

THE SHARED KERNEL HAS ALREADY DECIDED IT, AND ADDED A SECOND RULE.
the earlier shared snap kernel's `designated_element_index` takes `max` over the
exact traces, which returns THE FIRST MAXIMAL ELEMENT IN THE DECLARED ORDER --
the first candidate above. IT ALSO EXCLUDES STRUCTURALLY ZERO ELEMENTS ("the
rule NEVER NOMINATES A ZERO ELEMENT", ADR-0008 Section 7.2 constraint (1)) and
refuses `no_designated_element` when every element is zero. def:emitnorm (3)
says ONLY "the outcome of LARGEST EXACT TRACE in that block at that setting".
THE TWO DIVERGE where the largest-trace element is zero, and that is REACHABLE
at step (3) because POSITIVITY IS NOT YET ESTABLISHED -- step (4) comes after --
so an element of negative trace can sit beside a zero one. SO THE AMENDMENT HAS
TWO THINGS TO SAY: the tie break, and whether the zero exclusion is this
contract's rule or only the kernel's.""",
    ),
    (
        "(j) the rounding tie of def:emitnorm (2)",
        "CHANGE REQUEST -- routed, NOT DECIDED HERE",
        """\
THE SENTENCE: def:emitnorm (2), "Lattice rounding: every real and imaginary part
of every entry TO THE NEAREST INTEGER MULTIPLE OF 2^-kappa."

THE GAP: no tie rule. ADR-0008 Section 7.2's table, which def:emitnorm says it
applies, says only "every real and imaginary part rounded to the nearest
multiple of 2^-k" and fixes none either. IEEE-754's round-half-to-even is NOT
inherited here: this step is defined on EXACT RATIONALS in the substrate of
def:substrate, not on binary64 operands, so the hardware default has no standing.

THE WITNESS, AND IT IS HOW THE GAP WAS FOUND. The first positivity-lift fixture
attempted for EN3 was L_y0 = [[1/16, 1/4], [1/4, 1/2]]. It fails positivity
(e_2 = -1/32), the ladder repairs it at w = 1/8, and the lift's off-diagonal
entry is (1 - 1/8) * 1/4 = 7/32 -- for which 2^4 * 7/32 = 7/2, AN EXACT TIE.
The fixture could not be frozen without deciding the tie, so it was replaced by
one that avoids it (EN3 as frozen has 2^4 * 7/64 = 7/4 and 2^4 * 29/128 = 29/8,
neither a tie).

WHY IT IS PROOF-RELEVANT: the same reason as (h). Rounding 7/32 up gives 1/4 and
down gives 3/16; the two differ by one lattice step in an EMITTED entry, they
give different Delta_s, and -- because step (3) then absorbs a different residue
-- they can differ in a second entry too.

WHAT IS NEEDED: one clause in def:emitnorm (2), or in ADR-0008 Section 7.2's
table. Candidates, neither chosen here: HALF AWAY FROM ZERO, which is what
"nearest" most often means informally; or HALF TO EVEN, which matches IEEE and
is what a naive implementation using a float will do accidentally. THE TWO
DISAGREE ON EVERY TIE, so the choice is observable. PATCH LEVEL on either
reading -- and THE LEVEL IS THE HUMAN'S CALL AT G3.

THE SHARED KERNEL HAS ALREADY DECIDED IT, AND ITS REASON BELONGS IN THE
CONTRACT. the earlier shared snap kernel's `_round_part` uses Python's `round`,
i.e. HALF TO EVEN, and `_round_exact`'s docstring gives an argument the contract
does not give: "Round-half-to-even, WHICH IS ODD-SYMMETRIC, so a Hermitian
matrix rounds to a Hermitian matrix: the two mirror entries have equal real
parts and opposite imaginary parts before rounding and therefore after it."
THAT ARGUMENT IS LOAD-BEARING FOR def:emitnorm's STEP ORDER: under
half-away-from-zero an imaginary part of +1/2 ulp rounds up while its mirror
-1/2 ulp rounds down, SO THE ROUNDED MATRIX NEED NOT BE HERMITIAN and step (1)
would have to run again after step (2) -- which the definition does not say it
does. Half-to-even is therefore the reading under which the STATED STEP ORDER IS
CORRECT, which is a reason to state it rather than to leave it in a sibling
module's code.

A NOTE ON WHERE IT BITES. It bites ONLY inside def:emitnorm, on numbers this
module computed. It does NOT bite on eq:latdown, which is a FLOOR and has no tie;
and it does not bite on a declared datum, which must already be on the lattice.""",
    ),
    (
        "(k) whether 'largest exact trace' is read before or after step (2)",
        "RESOLVED for this band's fixtures -- and the ambiguity is recorded",
        """\
def:emitnorm (3) designates the element of "LARGEST EXACT TRACE in that block at
that setting". Step (3) runs AFTER step (2), so the natural reading is the trace
of the element AS IT STANDS WHEN STEP (3) RUNS, i.e. after rounding. But the
word EXACT points the other way, at the trace of the constructed element before
any rounding.

THE READING TAKEN: none, because EN2 is built so that THE TWO READINGS AGREE --
21/64 > 17/64 = 17/64 > 9/64 before, and 5/16 > 1/4 = 1/4 > 1/8 after, the same
letter winning both times. The fixture therefore pins a value that is correct
under either reading, and the ambiguity is recorded here rather than decided.

IT IS NOT ROUTED AS A CHANGE REQUEST because it is plausibly resolvable from the
text -- step (3) runs on the output of step (2), and that is the family it
speaks of -- where (h) and (j) are not resolvable at all. A verifier who
disagrees should read this item as the drafter's own doubt, recorded.""",
    ),
    (
        "(l) the residue cannot be non-zero at |Y| = 2, and what that costs",
        "RESOLVED from the text -- a structural fact, recorded so it is not a gap",
        """\
EN3 has a ZERO residue after its re-rounding, and that is not a weakness of the
fixture: it is structural. At |Y| = 2 the two elements sum to q_t * 1 before
rounding, 1 is on the lattice, and rounding to nearest satisfies
rnd(c - x) = c - rnd(x) for every non-tie x and every lattice c. So the two
roundings are complementary and the residue vanishes identically.

THE CONSEQUENCE FOR THE FREEZE, and it is why EN2 has FOUR outcomes: a fixture
that exercises step (3)'s absorption needs THREE OR MORE outcomes. A run-B test
suite that only ever exercises |Y| = 2 will never execute the designated-element
branch at all.

NOT A CONTRACT GAP: def:emitnorm states step (3) for any |Y| and is silent about
|Y| = 2 because there is nothing to say.""",
    ),
    (
        "(o) the shared kernel's lift ladder is NOT def:emitnorm's ladder",
        "OBSERVATION -- a RUN-B HAZARD, reported; NOT a contract gap",
        """\
NOT A GAP IN THE CONTRACT: def:emitnorm (4) is unambiguous. It is a divergence
between what contract.tex 1.0.0 states and what a SIBLING MODULE'S code does,
and run B must not discover it late.

THE CONTRACT'S LADDER: "w THE SMALLEST WEIGHT OF THE FIXED DYADIC LADDER
2^-1, 2^-2, ..., 2^-kappa THAT RESTORES EXACT POSITIVITY" -- every power from
2^-1 down to 2^-kappa, kappa rungs, INCLUDING COARSE ONES DOWN TO 1/2.

THE KERNEL'S LADDER: the earlier shared snap kernel's LIFT_LADDER is
(2^-36, 2^-34, 2^-32, 2^-28, 2^-24, 2^-20, 2^-16) -- SEVEN hand-picked rungs,
NONE COARSER THAN 2^-16 -- and its own comment says where they come from: "Taken
from the exact-emission spike's measured normalizer... which restored exact
positivity on 24/24 grid points at every k tried". A MEASURED RECOMMENDATION,
not ADR-0008's normative text: ADR-0008 Section 7.2 licenses "a dyadic weight
from A FIXED LADDER, the smallest that restores exact positivity" and DOES NOT
FIX THE RUNGS.

THE CONSEQUENCE, AND IT IS NOT COSMETIC. A block the contract's ladder repairs
at w = 1/2 the kernel REFUSES, no rung being at least 2^-16. That is fail-closed
in DIRECTION but it REFUSES EMISSIONS THE CONTRACT REQUIRES, and it makes the
recorded lift weight w a value THE CONTRACT'S LADDER DOES NOT CONTAIN. THIS
BAND'S OWN EN3 FIXTURE NEEDS w = 1/8, WHICH IS NOT IN LIFT_LADDER: `snap_positivity`
would refuse it.

WHAT RUN B MUST DO: walk def:emitnorm's ladder, 2^-1 ... 2^-kappa, and NOT
LIFT_LADDER. See the run-B plan's emission-path item, which also records that
`snap_family_exact`, `snap_to_lattice`, `snap_completeness` and
`snap_positivity` all take a `tolerance` this module does not have.

WHETHER THE KERNEL SHOULD ALSO CHANGE IS NOT THIS BAND'S QUESTION:
domain/snap.py is band B0's file. Reported to the driver as a cross-band fact.""",
    ),
    (
        "(m) `round_homogeneity` is both an inherited key and a local one",
        "OBSERVATION -- reported to the driver, NOT a contract gap",
        """\
1.0.0 requires the emitted ledger to carry this module's NINE machine keys AND
the supplier's THIRTEEN (INHERITED_RECEIVER_KEYS_1_0_0 above). ONE STRING OCCURS
IN BOTH LISTS: `round_homogeneity`, which is A-ROUND's key here and the
supplier's own key there. A-RECV states the relation and not an identity: the
supplier's "round homogeneity IS ITS OWN STATEMENT OF WHAT THIS CONTRACT'S
A-ROUND ASSUMES DOWNSTREAM", and the two carry different If-violated directions.

THE CONTRACT STATES NO NAMESPACING RULE. AN EMITTED LEDGER THAT MERGES THEM HAS
LOST AN ENTRY. That is a run-B hazard rather than a contract question, and it is
recorded in interface.yaml under open implementation choice 9, which 1.0.0
NARROWS (the keys are now named) without CLOSING (the namespacing is not).""",
    ),
    (
        "(n) the two code-side version strings this amendment moves, again",
        "ROUTED -- an observation to the driver, and NOT a contract gap",
        """\
The same shape as band 3's item (f), at new values, and run A may not write
under src/. The convention fixes the emitted binding as
`proof-reductions@<contract_version>` OF THE ACCEPTED CONTRACT, so the accepted
1.0.0 makes it `proof-reductions@1.0.0`. The stale sites run B must move:
the default of `ProofReductionArtifact.mathematical_spec_version` in
the earlier reductions artifact module, and the `technique` default in
the earlier reductions constraints module, which names a meat-core version while
def:roundmodel now quotes meat-core 1.0.0. NONE WAS CHANGED BY THIS RUN.""",
    ),
)


#: THE RUN-A MARKER. Both registry headers: run A derives the expected values by hand from the accepted
#: contract and writes no source file; run B writes or changes the code against
#: them and MAY READ BUT NOT MODIFY THEM. An expected value that turns out to be
#: wrong is a FINDING, reported and corrected deliberately with its derivation,
#: never edited in passing to make a test green.
TWO_INSTANCE_FREEZE_PR_R: str = (
    "run A, band 5. Derived by hand from contract.tex 1.0.1 at LF "
    "sha256 f12d712fed3c20c9f5736b5af69e9822aa9aba9ca0075d55811a5bd88a004df6 "
    "by an agent that wrote none of the fixtures these values replace, that "
    "edited no file under the worktree, and that imported no part of "
    "the earlier package. Run B re-points the four golden files at these values and "
    "invents no expected number."
)

#: The contract blob band 5 was derived from. Band 4 already pins the same
#: string as ``CONTRACT_SHA256_1_0_1``; it is repeated here, not replaced, so
#: that this group is checkable on its own.
CONTRACT_SHA256_PR_R: str = (
    "f12d712fed3c20c9f5736b5af69e9822aa9aba9ca0075d55811a5bd88a004df6"
)

#: The evidential status of every entry in this group, as in every other group
#: of this registry: ``estimate``. Agreement with an oracle is not a runtime
#: certificate check (ARCHITECTURE_SPEC.md Section 3.5).
ASSURANCE_PR_R: str = "estimate"

#: The band's declared lattice exponent and its step.
KAPPA_FIXTURE_PR_R: int = 12
LATTICE_STEP_PR_R: F = F(1, 2**KAPPA_FIXTURE_PR_R)


def _on_lattice_pr_r(value: F, kappa: int = KAPPA_FIXTURE_PR_R) -> bool:
    """Eq. eq:latinv, decided exactly: 2^kappa x in Z and |x| <= 1."""
    return (value * 2**kappa).denominator == 1 and abs(value) <= 1


#: THE SUBSTITUTION TABLE, and it is the whole of what this band changes about
#: the four files' declarations. (what, the 0.3.0 value, the dyadic value, the
#: sub-lattice exponent j, the displacement |dyadic - 0.3.0|).
DYADIC_SUBSTITUTIONS: tuple[tuple[str, F, F, int, F], ...] = (
    ("q_t at t_off", F(2, 3), F(43, 64), 6, F(1, 192)),
    ("q_t at t_on", F(1, 3), F(21, 64), 6, F(1, 192)),
    ("slot weight p_1", F(1, 10), F(3, 32), 5, F(1, 160)),
    ("per-port dark count p_dc|1", F(1, 5), F(3, 16), 4, F(1, 80)),
    ("per-port dark count p_dc|2", F(1, 4), F(1, 4), 2, F(0)),
    ("symmetric dark count (coarse case)", F(1, 5), F(3, 16), 4, F(1, 80)),
    ("block at the bulk letter", F(1, 2), F(17, 32), 5, F(1, 32)),
    ("block at a minor letter", F(1, 6), F(5, 32), 5, F(1, 96)),
    ("preserved block, letter a", F(3, 5), F(19, 32), 5, F(1, 160)),
    ("preserved block, letter b", F(2, 5), F(13, 32), 5, F(1, 160)),
    ("certified weight p_a", F(1, 5), F(3, 16), 4, F(1, 80)),
    ("certified weight p_b", F(1, 10), F(3, 32), 5, F(1, 160)),
    ("register POVM entry N_nb[0]", F(9, 25), F(3, 8), 3, F(3, 200)),
    ("register POVM entry N_nb[1]", F(16, 25), F(5, 8), 3, F(3, 200)),
    ("column-sum defect (CS-colsum-refuse)", F(1, 100), F(1, 128), 7, F(7, 3200)),
    ("forbidden-position entry (boundary pair)", F(1, 20), F(3, 64), 6, F(1, 320)),
)


# ---------------------------------------------------------------------------
#  PR-R1 -- the RC2-shaped declaration, dyadic, end to end
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DyadicEmissionCase:
    """One 1.0.1-conforming declaration and everything the pipeline emits on it.

    The fields divide in three. The DECLARATION is what a fixture writes; the
    ROUTE is Eq. ``eq:weightroute`` with Eq. ``eq:latdown``; the EMISSION is
    ``def:emitnorm`` step by step and the target of Eq. ``eq:blindtarget``.
    """

    case_id: str
    claims: tuple[str, ...]
    kappa: int
    #: The declared letters of Y and settings of T, in the emitted order.
    letters: tuple[str, ...]
    settings: tuple[str, ...]
    #: (setting, q_t) and (bounded letter, p_i).
    probe_weights: tuple[tuple[str, F], ...]
    slot_weights: tuple[tuple[str, F], ...]
    #: The declared 1 x 1 block at m = 0, per letter; the same at every setting.
    declared_blocks: tuple[tuple[str, F], ...]
    #: R^cg column by column: (column letter, ((row letter, entry), ...)).
    descended_matrix: tuple[tuple[str, tuple[tuple[str, F], ...]], ...]
    #: (bounded letter, absorbing, r_min,i).
    bounded_letters: tuple[tuple[str, bool, F], ...]
    #: Eq. eq:weightroute BEFORE the lattice rounding, per (letter, setting).
    routed_weights_hat: tuple[tuple[tuple[str, str], F], ...]
    #: Eq. eq:latdown applied to each of them: THE EMITTED WEIGHT.
    emitted_weights: tuple[tuple[tuple[str, str], F], ...]
    total_weight_hat: F | None
    total_weight: F | None
    #: def:emitnorm on the single preserved block m = 0, per setting:
    #: (setting, ((letter, constructed), ...), ((letter, after step (2)), ...),
    #:  residue of step (3), the designated element or None, Delta_s).
    emission: tuple[
        tuple[
            str,
            tuple[tuple[str, F], ...],
            tuple[tuple[str, F], ...],
            F,
            str | None,
            F,
        ],
        ...,
    ]
    #: The step-(4) lift, or None where the ladder is never entered.
    lift_weight: F | None
    lift_vector: tuple[tuple[str, F], ...] | None
    #: The emitted target, per outcome, as the diagonal in the declared sector
    #: order; None where the declaration is refused.
    emitted_target: tuple[tuple[str, tuple[F, ...]], ...] | None
    sector_labels: tuple[tuple[str, object], ...] | None
    unpadded_dim: int | None
    padded_dim_not_emitted: int | None
    refusal_reason: str | None
    labels: tuple[str, ...]
    route_a: str
    route_b: str
    agreement: str


PR_R1 = DyadicEmissionCase(
    case_id="PRR-1-rc2-dyadic",
    claims=("PR6", "PR12", "PR13"),
    kappa=12,
    letters=("y_empty", "y_1", "y_2", "y_mc"),
    settings=("t_off", "t_on"),
    probe_weights=(("t_off", F(43, 64)), ("t_on", F(21, 64))),
    slot_weights=(("y_mc", F(3, 32)),),
    declared_blocks=(
        ("y_empty", F(17, 32)),
        ("y_1", F(5, 32)),
        ("y_2", F(5, 32)),
        ("y_mc", F(5, 32)),
    ),
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(39, 64)),
                ("y_1", F(9, 64)),
                ("y_2", F(13, 64)),
                ("y_mc", F(3, 64)),
            ),
        ),
        (
            "y_1",
            (("y_empty", F(0)), ("y_1", F(3, 4)), ("y_2", F(0)), ("y_mc", F(1, 4))),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(13, 16)), ("y_mc", F(3, 16))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    bounded_letters=(("y_mc", True, F(3, 64)),),
    routed_weights_hat=(
        (("y_mc", "t_off"), F(11997, 131072)),
        (("y_mc", "t_on"), F(5859, 131072)),
    ),
    emitted_weights=(
        (("y_mc", "t_off"), F(187, 2048)),
        (("y_mc", "t_on"), F(183, 4096)),
    ),
    total_weight_hat=F(279, 2048),
    total_weight=F(557, 4096),
    emission=(
        (
            "t_off",
            (
                ("y_empty", F(28509, 131072)),
                ("y_1", F(16899, 131072)),
                ("y_2", F(20683, 131072)),
                ("y_mc", F(21973, 131072)),
            ),
            (
                ("y_empty", F(891, 4096)),
                ("y_1", F(33, 256)),
                ("y_2", F(323, 2048)),
                ("y_mc", F(687, 4096)),
            ),
            F(0),
            None,
            F(11, 131072),
        ),
        (
            "t_on",
            (
                ("y_empty", F(13923, 131072)),
                ("y_1", F(8253, 131072)),
                ("y_2", F(10101, 131072)),
                ("y_mc", F(10731, 131072)),
            ),
            (
                ("y_empty", F(435, 4096)),
                ("y_1", F(129, 2048)),
                ("y_2", F(79, 1024)),
                ("y_mc", F(335, 4096)),
            ),
            F(0),
            None,
            F(11, 131072),
        ),
    ),
    lift_weight=None,
    lift_vector=None,
    emitted_target=None,
    sector_labels=None,
    unpadded_dim=9,
    padded_dim_not_emitted=9,
    refusal_reason=None,
    labels=(
        "def:exactadm",
        "eq:latinv",
        "lem:latsum",
        "eq:weightroute",
        "eq:latdown",
        "def:emitnorm",
        "eq:displacement",
        "lem:descent",
        "cor:oneabsorbing",
    ),
    route_a="""\
ROUTE A -- BY HAND FROM THE CONTRACT'S DEFINITIONS, IN EXACT RATIONALS.

THE DECLARATION. K = 2 under the canonical coarse-graining of Eq.
eq:canonicalcg, so Y = {y_empty, y_1, y_2, y_mc}, cg is a BIJECTION off
MC = {{1,2}}, and cg^{-1}(y_mc) = MC exactly -- the fibre condition of
Rem. rem:fibre. Independent per-port dark counts p_dc|1 = 3/16 and
p_dc|2 = 1/4, so R_{S|S'} = 0 unless S' subset S and otherwise
R_{S|S'} = prod_{k in S\\S'} p_dc|k prod_{k not in S} (1 - p_dc|k). With
a = 3/16 and b = 1/4:
  col e  : ((13/16)(3/4), (3/16)(3/4), (13/16)(1/4), (3/16)(1/4))
         = (39/64, 9/64, 13/64, 3/64), summing to (39+9+13+3)/64 = 1;
  col 1  : (0, 3/4, 0, 1/4);
  col 2  : (0, 0, 13/16, 3/16);
  col 12 : (0, 0, 0, 1).
Every entry is an integer multiple of 2^-6, hence of 2^-12: eq:latinv holds and
the ``dark_count_channel`` row's stated validity clause is met by construction.
cg is injective off MC and MC is one pattern, so R descends and R^cg = R
(lem:descent). R^cg_{y_mc|y_mc} = 1: ABSORBING (eq:absorbing).

r_min,1 = min over y' != y_mc of R^cg_{y_mc|y'} = min(3/64, 1/4, 3/16) = 3/64,
the minimum coming from the EMPTY column because that is the one needing both
ports to fire spuriously.

THE ROUTE, Eq. eq:weightroute at p_1 = 3/32:
  p^_(y_mc,t) = q_t((1 - 3/64)(3/32) + 3/64)
              = q_t((61/64)(3/32) + 3/64)
              = q_t(183/2048 + 96/2048) = q_t * 279/2048 ,
so p^_(y_mc,t_off) = (43/64)(279/2048) = 11997/131072 and
p^_(y_mc,t_on) = (21/64)(279/2048) = 5859/131072, and p^_(y,t) = 0 at every
other (y,t).

THE ROUNDING, Eq. eq:latdown, at kappa = 12. 131072 = 2^17 and 2^17 / 2^12 = 32:
  2^12 * 11997/131072 = 11997/32 = 374 + 29/32  ->  floor 374  ->  187/2048;
  2^12 *  5859/131072 =  5859/32 = 183 +  3/32  ->  floor 183  ->  183/4096.
BOTH ROUNDINGS BITE, and both LOWER. p = 187/2048 + 183/4096 = 557/4096, while
p^ = 279/2048 = 558/4096: THE EMITTED TOTAL IS STRICTLY BELOW THE ROUTED ONE, by
exactly one lattice step. That is the direction sec:consume calls "the whole of
what makes it safe" and ADR-0008 Section 7.2.1's condition (D-DIR) names.
p = 557/4096 < 1, so the total-weight row admits.

THE DECLARED BLOCKS ARE EXACTLY ADMISSIBLE, def:exactadm (c), CONDITION BY
CONDITION AND WITHOUT MEASURING ANYTHING. (a) the sector map is the declared
per-m list, one 1 x 1 block at m = 0 per (letter, setting), compared as labels;
(b) a real 1 x 1 block equals its own adjoint entry for entry; (c) eq:psdtest at
d = 1 is e_1(X) = X >= 0, and 17/32 and 5/32 are positive; (d)
17/32 + 5/32 + 5/32 + 5/32 = 32/32 = 1 = id_1 on the block at each (t, m);
(e) lem:latsum with L = |Y| = 4 and kappa + ceil(log2 4) = 14 <= 53. Every entry
satisfies eq:latinv at j = 5. NOTHING IS REPAIRED AND NO DEFECT IS MEASURED.

def:emitnorm, STEP BY STEP, ON THE ONE PRESERVED BLOCK m = 0.
Steps 1-2 of sec:consume first: M~_y = sum_y' R^cg_{y|y'} M_{y'|t}, then
M_(y,t) = q_t M~_y.
  M~_{y_empty} = (39/64)(17/32) = 663/2048;
  M~_{y_1}     = (9/64)(17/32) + (3/4)(5/32) = 153/2048 + 240/2048 = 393/2048;
  M~_{y_2}     = (13/64)(17/32) + (13/16)(5/32) = 221/2048 + 260/2048 = 481/2048;
  M~_{y_mc}    = (3/64)(17/32) + (1/4)(5/32) + (3/16)(5/32) + (1)(5/32)
               = (51 + 80 + 60 + 320)/2048 = 511/2048;
and 663 + 393 + 481 + 511 = 2048, so {M~_y} is a POVM exactly.
(1) HERMITIAN PART: the identity map, the blocks being real 1 x 1.
(2) LATTICE ROUNDING to the nearest multiple of 2^-12, ties to even. At t_off the
    constructed entries are (28509, 16899, 20683, 21973)/2^17 and 2^17/2^12 = 32,
    so the fractional parts of the scaled numerators are 29/32, 3/32, 11/32 and
    21/32 -- NONE OF THEM 1/2, SO NO TIE ARISES ANYWHERE and the amended tie
    rule of 1.0.1 decides nothing here. Rounding gives
    (28512, 16896, 20672, 21984)/2^17 = (891/4096, 33/256, 323/2048, 687/4096).
    At t_on the constructed entries are (13923, 8253, 10101, 10731)/2^17 with
    fractional parts 3/32, 29/32, 21/32, 11/32 -- again no tie -- giving
    (13920, 8256, 10112, 10720)/2^17 = (435/4096, 129/2048, 79/1024, 335/4096).
(3) COMPLETENESS. The residue is q_t id - sum_y A_(y,t). At t_off the rounded
    numerators over 2^-12 are 891 + 528 + 646 + 687 = 2752 and
    q_off * 2^12 = (43/64)(4096) = 43 * 64 = 2752: THE RESIDUE IS EXACTLY ZERO.
    At t_on they are 435 + 258 + 316 + 335 = 1344 and
    q_on * 2^12 = (21/64)(4096) = 21 * 64 = 1344: ZERO AGAIN. The step therefore
    moves nothing. The rule still NAMES a designated element -- the outcome of
    largest exact trace, ties broken by the declared order of Y -- and that is
    y_empty at both settings, uniquely (891 > 687 > 646 > 528 at t_off,
    435 > 335 > 316 > 258 at t_on). It is recorded as None here for the reason
    EN1 of group PR-Q records it as None: nothing was absorbed into it.
(4) POSITIVITY. Every entry above is a positive multiple of 2^-12, and
    eq:psdtest at d = 1 is the entry itself. THE LADDER IS NEVER ENTERED, EQ.
    eq:lift IS NEVER APPLIED, and the dyadic vector u of open finding
    F-S2-PR-06 is never needed. lift_weight and lift_vector are None.
(5) ALL SIX DECIDED, on the numbers about to be emitted: the sector map by
    construction, Hermiticity and positivity as above, completeness by the zero
    residue of (3), the rounds-nowhere condition by lem:latsum, and eq:latinv by
    the rounding of (2). Nothing refuses.

Eq. eq:displacement. On the single preserved block, Delta_s is the maximum over
v in V of the entrywise maximum modulus of M' - M. The per-entry moves are
+3, -3, -11, +11 over 2^-17 at t_off and -3, +3, +11, -11 at t_on, so
Delta_s = 11/131072 = 8.392333984375e-05. It is EXACT here because a 1 x 1
modulus is an absolute value; the general irrationality def:exactadm (a) warns
about does not arise. Nothing reads it.

THE EMITTED TARGET is not frozen entrywise in this case, and deliberately: with
Blmode = {nb}, N = 0 and dim H(C_0) = 1, thm:blinding (iii) gives
dim H(Q) = 1 + 1 * |V| = 1 + 8 = 9, the padded variant of thm:blinding (v) gives
1 * (1 + 8) = 9 as well, and the two AGREE -- this is the degenerate row of
BLINDING_DIMENSION_CASES and it discriminates nothing. Case PRR-2 carries the
discriminating target. What IS frozen here is M' after step (2), which is
exactly the preserved sector of the target (thm:blinding (iii)).""",
    route_b="""\
ROUTE B -- INDEPENDENTLY, IN INTEGERS ONLY, WITH NO FRACTION ARITHMETIC.

Put every declared number over 2^-6 as an integer numerator: the blocks over
2^-5 are (17, 5, 5, 5)/32 = (34, 10, 10, 10)/64; R^cg's columns are
(39, 9, 13, 3), (0, 48, 0, 16), (0, 0, 52, 12), (0, 0, 0, 64) over 64.

(i) COLUMN-STOCHASTICITY, as integer sums over 64: 39+9+13+3 = 64; 48+16 = 64;
    52+12 = 64; 64. Four identities between integers, no division.

(ii) THE POST-PROCESSED BLOCKS, by a DIFFERENT FORMULA. Route A summed row by
     row. Here use column-stochasticity instead: sum_y M~_y
     = sum_y' M_{y'} sum_y R^cg_{y|y'} = sum_y' M_{y'} = 1, so the FOURTH entry
     need not be computed at all -- it is 1 minus the other three. Over 2^-11:
     M~_{y_empty} = 39*34/(64*64) * 2048 ... more simply, with numerators over
     2^-11 (= 2048): 39*34 = 1326 over 4096, i.e. 663 over 2048;
     9*34 + 48*10 = 306 + 480 = 786 over 4096 = 393 over 2048;
     13*34 + 52*10 = 442 + 520 = 962 over 4096 = 481 over 2048;
     and the fourth is 2048 - 663 - 393 - 481 = 511 over 2048. THE ROW SUM ROUTE
     OF (ii) AND THE COLUMN ROUTE OF ROUTE A AGREE ON 511/2048, which is the one
     entry both compute: route A's (51 + 80 + 60 + 320)/2048 = 511/2048.

(iii) THE ROUNDING, by integer division rather than by a rational floor.
      floor(2^kappa x) for x = n/2^17 is the integer division n // 32 and the
      tie test is n mod 32 against 16. At t_off, 43 * 663 = 28509 with
      28509 = 891*32 - 3, so 28509 mod 32 = 29 > 16 and the nearest is 891;
      43 * 393 = 16899 = 528*32 + 3, remainder 3 < 16, nearest 528;
      43 * 481 = 20683 = 646*32 + 11, remainder 11 < 16, nearest 646;
      43 * 511 = 21973 = 687*32 - 11, remainder 21 > 16, nearest 687.
      NO REMAINDER IS 16, so no tie occurs and the ties-to-even clause of 1.0.1
      is not reached. At t_on: 21*663 = 13923 = 435*32 + 3 (nearest 435);
      21*393 = 8253 = 258*32 - 3, remainder 29 (nearest 258);
      21*481 = 10101 = 316*32 - 11, remainder 21 (nearest 316);
      21*511 = 10731 = 335*32 + 11 (nearest 335). Again no remainder is 16.

(iv) THE RESIDUE, as an integer identity. 891 + 528 + 646 + 687 = 2752 and
     43 * 64 = 2752; 435 + 258 + 316 + 335 = 1344 and 21 * 64 = 1344. Both are
     equalities between integers, and equality is what "residue zero" means.
     A SECOND CHECK ON THE SAME FACT, and it is why the residue is zero rather
     than small: the four remainders at each setting are {29, 3, 11, 21} and
     {3, 29, 21, 11}, which pair as 29 + 3 = 32 and 11 + 21 = 32, so the two
     upward roundings and the two downward ones cancel exactly.

(v) THE EMITTED WEIGHTS, by the same integer division applied to eq:latdown's
    FLOOR rather than to a nearest: 11997 // 32 = 374 (11997 = 374*32 + 29) and
    5859 // 32 = 183 (5859 = 183*32 + 3). 374/4096 = 187/2048 and 183/4096.

(vi) THE ROUTED TOTAL, from a formula route A did not use. sum_t q_t = 1
     exactly, so sum_t p^_(y_mc,t) = 279/2048 WITHOUT computing either term:
     279/2048 = 558/4096. The emitted total 374 + 183 = 557 over 4096 is one
     unit below it, which is the two floors' combined loss (29 + 3 = 32 = one
     unit at 2^-12 exactly).""",
    agreement="""\
THE LINE WHERE THE TWO ROUTES AGREE. Route A computes M~_{y_mc} = 511/2048 by
summing the y_mc ROW of R^cg against the declared blocks; route B computes it as
2048 minus the other three partial sums, using column-stochasticity and never
touching that row. Both return 511/2048. Route A takes the four roundings as
rational nearest-multiples; route B takes them as integer quotients with an
explicit remainder-versus-16 test, and both return
(891, 528, 646, 687) and (435, 258, 316, 335) over 2^-12. Route A computes the
routed total as q_off p^ + q_on p^; route B computes it as p^ * sum_t q_t
without evaluating either term, and both return 279/2048. The emitted weights
187/2048 and 183/4096, the emitted total 557/4096, the two zero residues and
Delta_s = 11/131072 are the values on which the two routes meet.""",
)


# ---------------------------------------------------------------------------
#  PR-R2 -- the BLIND2-shaped declaration, dyadic: the UNPADDED target
# ---------------------------------------------------------------------------

#: The dyadic replacements for BLIND2's declared data. The preserved blocks and
#: the certified weights are declared to this module; the register POVM and the
#: blinded-branch POVM are NOT (def:exactadm (d)), and are snapped anyway --
#: see PR_R2.route_a, "why N_b is snapped although (d) exempts it".
PR_R2_PRESERVED: tuple[tuple[str, F], ...] = (("a", F(19, 32)), ("b", F(13, 32)))
PR_R2_ABOVE_CUTOFF: tuple[tuple[str, F], ...] = (("a", F(1, 4)), ("b", F(3, 4)))
PR_R2_WEIGHTS: tuple[tuple[str, F], ...] = (("a", F(3, 16)), ("b", F(3, 32)))
PR_R2_TOTAL_WEIGHT: F = F(9, 32)
PR_R2_COMPLEMENT: F = F(23, 32)
#: M^WP of eq:Lwp -- NOT dyadic, and correctly not: at 1.0.0 it is a SYMBOLIC
#: CONSTRUCTOR RECORD inside ``squashing_channel``, "a DIFFERENT object from the
#: declared family M' of the row below, and carrying a different symbol at 1.0.0
#: for that reason". It is emitted as no array and no row decides it.
PR_R2_MWP: tuple[tuple[str, F], ...] = (("a", F(2, 23)), ("b", F(21, 23)))
#: The blinding-register POVM: still non-projective, now dyadic.
PR_R2_N_NB: tuple[F, ...] = (F(3, 8), F(5, 8))
PR_R2_N_BL1: tuple[F, ...] = (F(5, 8), F(3, 8))
#: The blinded-branch POVM, UNCHANGED: |+><+| and its complement are already
#: dyadic, and M_{a|bl1} still has a non-zero (0,1) entry, so it is still not
#: block diagonal at the cutoff -- which def:blindmodel (c) permits and which is
#: what makes the block-structure row's scope observable.
PR_R2_M_BL1_A: tuple[tuple[F, ...], ...] = (
    (F(1, 2), F(1, 2)),
    (F(1, 2), F(1, 2)),
)
PR_R2_M_BL1_B: tuple[tuple[F, ...], ...] = (
    (F(1, 2), F(-1, 2)),
    (F(-1, 2), F(1, 2)),
)
#: The physical POVM M_v = sum_b M_{v|b} (x) N_b on B = C (x) Bl = C^2 (x) C^2,
#: basis (c0 bl0, c0 bl1, c1 bl0, c1 bl1). Every entry on 2^-8.
PR_R2_M_A: tuple[tuple[F, ...], ...] = (
    (F(137, 256), F(0), F(5, 16), F(0)),
    (F(0), F(143, 256), F(0), F(3, 16)),
    (F(5, 16), F(0), F(13, 32), F(0)),
    (F(0), F(3, 16), F(0), F(11, 32)),
)
PR_R2_M_B: tuple[tuple[F, ...], ...] = (
    (F(119, 256), F(0), F(-5, 16), F(0)),
    (F(0), F(113, 256), F(0), F(-3, 16)),
    (F(-5, 16), F(0), F(19, 32), F(0)),
    (F(0), F(-3, 16), F(0), F(21, 32)),
)
#: THE EMITTED TARGET on the UNPADDED H(Q), basis
#: (nb-preserved, nb-f_a, nb-f_b, bl1-f_a, bl1-f_b): dimension 5 = 1 + 2*2.
PR_R2_F_A: tuple[F, ...] = (F(19, 32), F(29, 32), F(3, 16), F(1), F(0))
PR_R2_F_B: tuple[F, ...] = (F(13, 32), F(3, 32), F(13, 16), F(0), F(1))
#: Eq. eq:blindtransport, the three transported operators, on B.
PR_R2_TRANSPORT: tuple[tuple[str, tuple[F, ...]], ...] = (
    ("Pi_nb_leq", (F(3, 8), F(5, 8), F(0), F(0))),
    ("Pi_nb_flag", (F(0), F(0), F(3, 8), F(5, 8))),
    ("Pi_bl1", (F(5, 8), F(3, 8), F(5, 8), F(3, 8))),
)

PR_R2 = DyadicEmissionCase(
    case_id="PRR-2-blind2-dyadic",
    claims=("PR6", "PR9", "PR12"),
    kappa=12,
    letters=("a", "b"),
    settings=("t",),
    probe_weights=(("t", F(1)),),
    slot_weights=PR_R2_WEIGHTS,
    declared_blocks=PR_R2_PRESERVED,
    descended_matrix=(
        ("a", (("a", F(1)), ("b", F(0)))),
        ("b", (("a", F(0)), ("b", F(1)))),
    ),
    bounded_letters=(("a", True, F(0)), ("b", True, F(0))),
    routed_weights_hat=((("a", "t"), F(3, 16)), (("b", "t"), F(3, 32))),
    emitted_weights=((("a", "t"), F(3, 16)), (("b", "t"), F(3, 32))),
    total_weight_hat=F(9, 32),
    total_weight=F(9, 32),
    emission=(
        (
            "t",
            (("a", F(19, 32)), ("b", F(13, 32))),
            (("a", F(19, 32)), ("b", F(13, 32))),
            F(0),
            None,
            F(0),
        ),
    ),
    lift_weight=None,
    lift_vector=None,
    emitted_target=(("a", PR_R2_F_A), ("b", PR_R2_F_B)),
    sector_labels=(("nb", 0), ("nb", "a"), ("nb", "b"), ("bl1", "a"), ("bl1", "b")),
    unpadded_dim=5,
    padded_dim_not_emitted=6,
    refusal_reason=None,
    labels=(
        "eq:blindtarget",
        "thm:blinding",
        "rem:paddednotemitted",
        "eq:blindtransport",
        "eq:WPadjoint",
        "eq:Lwp",
        "def:emitnorm",
        "def:exactadm",
    ),
    route_a="""\
ROUTE A -- BY HAND FROM eq:blindtarget AND eq:Lwp.

THE DECLARATION. |Blmode| = 2 with Blmode = (nb, bl1); V = {a, b} at the single
setting t with q_t = 1; N = 0 with dim H(C_0) = 1; identity dark counts, so
R^cg = 1_2, both letters absorbing and -- there being r = 2 bounded letters --
every r_min,i = 0 by cor:oneabsorbing, directly confirmed by R^cg_{a|b} = 0.

THE DYADIC SUBSTITUTION. Preserved blocks 3/5, 2/5 -> 19/32, 13/32 (nearest at
j = 5, and their sum is exactly 1 as the completeness condition requires).
Certified weights 1/5, 1/10 -> 3/16, 3/32. Above-cutoff blocks 1/4 and 3/4 are
already dyadic and are UNCHANGED. eq:certweights survives the substitution:
1/4 >= 3/16 and 3/4 >= 3/32.

WHY N_b IS SNAPPED ALTHOUGH def:exactadm (d) EXEMPTS IT. Clause (d) is explicit
that the definition "is NOT available for the declared blinded-branch POVMs or
for the blinding-register family {N_b}", those being operators on Chan and Blreg
which this contract does not require to be presented as matrices; their
conditions "remain hypotheses of the model". So nothing forces N_nb onto the
lattice. It is snapped anyway -- diag(9/25, 16/25) -> diag(3/8, 5/8), still
non-projective, still summing with N_bl1 to 1_Bl -- because eq:blindtransport's
three carried operators are Pi_<=N (x) N_nb, Pi_>N (x) N_nb and 1_C (x) N_bl1,
whose entries ARE N_b's entries, and sec:outputs' ``emission_record`` row states
"that every emitted operator entry is an integer multiple of 2^-kappa of modulus
at most 1". THE CONTRACT DOES NOT SAY WHICH SIDE WINS; this freeze takes the
conservative side and records the fact as an observation.

THE ROUTE. r_min = 0 at both letters, so eq:weightroute reduces to
p^_(v,t) = q_t p_v = p_v, already on the lattice, so eq:latdown is the identity
and p_(a,t) = 3/16, p_(b,t) = 3/32. p = 9/32 < 1 and 1 - p = 23/32. THIS IS THE
ONE CASE IN THE GROUP WHERE THE ROUNDING DOES NOT BITE, and it is frozen beside
PRR-1 for exactly that contrast: the direction of eq:latdown is only observable
against a case where it is the identity.

M^WP, Eq. eq:Lwp: M^WP_v = (blk M^{>N}_v - p_v)/(1 - p), so
  M^WP_a = (1/4 - 3/16)/(23/32) = (1/16)(32/23) = 2/23 ,
  M^WP_b = (3/4 - 3/32)/(23/32) = (21/32)(32/23) = 21/23 ,   sum = 1 .
NEITHER IS DYADIC AND NEITHER NEEDS TO BE. At 1.0.0 M^WP is a symbolic
constructor record carried in ``squashing_channel`` -- "not evaluable data" --
and is a DIFFERENT OBJECT from def:emitnorm's declared family M'. No array
carries it and no row decides it.

def:emitnorm IS THE IDENTITY HERE, by its own first property: steps 1-2 of
sec:consume multiply the declared blocks by the identity R^cg and by q_t = 1, so
the constructed preserved blocks ARE the declared ones, 19/32 and 13/32, already
satisfying eq:latinv. "M' = M and every Delta_s = 0 ... in which case the
normalizer is the identity and NOTHING BELOW HAS AN ANTECEDENT." Residue zero,
no designated element, NO LIFT.

THE EMITTED TARGET, Eq. eq:blindtarget. H(Q) = (H(C_<=0) (+) H(flag))_nb (+)
(H(flag))_bl1, of dimension 1 + 2 + 2 = 5, and F_v = F^WP_v (+) |v><v|_{flag_1}
with F^WP_v = [preserved_v] (+) (p_v 1_{|V|} + (1 - p)|v><v|):
  F_a = diag(19/32, 3/16 + 23/32, 3/16, 1, 0) = diag(19/32, 29/32, 3/16, 1, 0),
  F_b = diag(13/32, 3/32, 3/32 + 23/32, 0, 1) = diag(13/32, 3/32, 13/16, 0, 1),
which sum entrywise to 1_5: 19/32 + 13/32 = 1, 29/32 + 3/32 = 1,
3/16 + 13/16 = 1, 1 + 0 = 1, 0 + 1 = 1. Every entry is an integer multiple of
2^-5 of modulus at most 1, so eq:latinv holds; the family is diagonal, so it is
exactly Hermitian; the entries are non-negative, so eq:psdtest at d = 1 gives
positivity per sector; and lem:latsum with L = |V| = 2 gives the rounds-nowhere
condition. ALL SIX OF (D-EMIT) ARE DECIDED AND NONE REFUSES.

THE DIMENSION DISCRIMINATOR SURVIVES THE SUBSTITUTION, which is the whole point
of keeping this case. thm:blinding (iii) gives dim H(Q) = 1 + 2*2 = 5; the padded
variant of thm:blinding (v) would give |Blmode|(1 + |V|) = 2*3 = 6; and
rem:paddednotemitted says the padded number is not emitted. 5 != 6, so an
implementation that padded is still observably wrong on this instance.""",
    route_b="""\
ROUTE B -- eq:WPadjoint, WHICH THE CONTRACT PROVES EQUAL TO THE DECLARED
ABOVE-CUTOFF BLOCKS AND WHICH ROUTE A NEVER USED.

Route A built F^WP_v from p_v and 1 - p and stopped. Route B runs the adjoint the
other way: Lambda^WP-dagger applied to the flag part of F^WP_v must return the
declared above-cutoff block, sum_w (F^WP_v)_{flag_w} M^WP_w = blk M^{>N}_v.
  v = a: (29/32)(2/23) + (3/16)(21/23) = 58/736 + 126/736 = 184/736 = 1/4 ,
         and the declared above-cutoff block at a is 1/4.  AGREES.
  v = b: (3/32)(2/23)  + (13/16)(21/23) = 6/736 + 546/736 = 552/736 = 3/4 ,
         and the declared above-cutoff block at b is 3/4.  AGREES.
The 23 in M^WP's denominator cancels against the 23/32 in the flag entries, which
is why the non-dyadic M^WP leaves no trace in an emitted number.

THE PHYSICAL POVM, BY A SECOND ROUTE. Route A would build M_a = sum_b M_{a|b} (x)
N_b. Route B builds M_b the same way and then checks M_a + M_b = 1_4 rather than
taking either on trust:
  M_{b|nb} = diag(13/32, 3/4), M_{b|bl1} = 1_2 - |+><+|, so
  (c0bl0): (13/32)(3/8) + (1/2)(5/8) = 39/256 + 80/256 = 119/256 ;
  (c0bl1): (13/32)(5/8) + (1/2)(3/8) = 65/256 + 48/256 = 113/256 ;
  (c1bl0): (3/4)(3/8)  + (1/2)(5/8)  =  9/32 + 10/32  = 19/32 ;
  (c1bl1): (3/4)(5/8)  + (1/2)(3/8)  = 15/32 +  6/32  = 21/32 ;
  off-diagonal (c0bl_j, c1bl_j): 0 + (-1/2)N_bl1[j] = -5/16 and -3/16 .
Adding to M_A entry for entry: 137 + 119 = 256, 143 + 113 = 256, 13 + 19 = 32,
11 + 21 = 32, and 5/16 - 5/16 = 0, 3/16 - 3/16 = 0. M_a + M_b = 1_4 EXACTLY.
The off-diagonal entries 5/16 and 3/16 come ENTIRELY from the blinded branch --
M_{a|bl1} contributes (1/2)N_bl1[j] to each -- which is the same structural fact
BLIND2 froze at 8/25 and 9/50, and it is why the block-structure row must test
{M_{v|nb}} alone.

THE TRANSPORT, BY UNITALITY RATHER THAN BY CONSTRUCTION. Route A read the three
carried operators off eq:blindtransport. Route B checks them by the property the
contract requires of them instead: Lambda-dagger is unital, so the three must sum
to 1_B because the three target projectors sum to 1_Q.
  (3/8, 5/8, 0, 0) + (0, 0, 3/8, 5/8) + (5/8, 3/8, 5/8, 3/8)
  = (3/8 + 5/8, 5/8 + 3/8, 3/8 + 5/8, 5/8 + 3/8) = (1, 1, 1, 1) .

THE DIMENSION, BY COUNTING SECTORS RATHER THAN BY THE FORMULA. Eq. eq:sectors
gives S = {(nb, m) : m <= 0} u {(nb, f) : f in V} u {(bl1, f) : f in V}, so
|S| = 1 + 2 + 2 = 5 sectors of dimension 1 each, total 5 -- which is
thm:blinding (iii)'s sum_{m<=N} dim H(C_m) + |Blmode||V| = 1 + 4 computed the
other way round.""",
    agreement="""\
THE LINE WHERE THE TWO ROUTES AGREE. Route A derives the flag entries 29/32,
3/16, 3/32, 13/16 from p_v and 1 - p; route B feeds those same four numbers
through eq:WPadjoint against M^WP = (2/23, 21/23) and recovers the DECLARED
above-cutoff blocks 1/4 and 3/4, which route A never used and which are an input
rather than an output. Route A builds M_a from the branch decomposition; route B
builds M_b the same way and the two sum to 1_4 entry for entry. Route A reads the
transported operators off eq:blindtransport; route B recovers them from
unitality. The values on which they meet are F_a = diag(19/32, 29/32, 3/16, 1, 0),
F_b = diag(13/32, 3/32, 13/16, 0, 1), the unpadded dimension 5 against the padded
6, the three transported diagonals, and Delta_s = 0.""",
)


# ---------------------------------------------------------------------------
#  PR-R3 -- the docking declaration: Blmode = {nb}, two letters, one setting
# ---------------------------------------------------------------------------

PR_R3 = DyadicEmissionCase(
    case_id="PRR-3-docking-dyadic",
    claims=("PR6", "PR11", "PR12"),
    kappa=12,
    letters=("a", "b"),
    settings=("t",),
    probe_weights=(("t", F(1)),),
    slot_weights=(("a", F(3, 16)), ("b", F(3, 32))),
    declared_blocks=(("a", F(19, 32)), ("b", F(13, 32))),
    descended_matrix=(
        ("a", (("a", F(1)), ("b", F(0)))),
        ("b", (("a", F(0)), ("b", F(1)))),
    ),
    bounded_letters=(("a", True, F(0)), ("b", True, F(0))),
    routed_weights_hat=((("a", "t"), F(3, 16)), (("b", "t"), F(3, 32))),
    emitted_weights=((("a", "t"), F(3, 16)), (("b", "t"), F(3, 32))),
    total_weight_hat=F(9, 32),
    total_weight=F(9, 32),
    emission=(
        (
            "t",
            (("a", F(19, 32)), ("b", F(13, 32))),
            (("a", F(19, 32)), ("b", F(13, 32))),
            F(0),
            None,
            F(0),
        ),
    ),
    lift_weight=None,
    lift_vector=None,
    emitted_target=(
        ("a", (F(19, 32), F(29, 32), F(3, 16))),
        ("b", (F(13, 32), F(3, 32), F(13, 16))),
    ),
    sector_labels=(("nb", 0), ("nb", "a"), ("nb", "b")),
    unpadded_dim=3,
    padded_dim_not_emitted=3,
    refusal_reason=None,
    labels=("eq:blindtarget", "def:emitnorm", "cor:entries", "thm:licence"),
    route_a="""\
ROUTE A. PRR-2 with the DEGENERATE no-blinding declaration Blmode = {nb},
N_nb = 1_Bl, which def:blindmodel names and which "every statement of the
contract specializes to". The declared data is PRR-2's minus the blinded branch:
preserved blocks 19/32 and 13/32, certified weights 3/16 and 3/32, identity dark
counts, q_t = 1 at the single setting.

Everything of PRR-2's route A that does not mention bl1 carries over verbatim:
r_min = 0 at both letters, p_(a,t) = 3/16 and p_(b,t) = 3/32 with eq:latdown the
identity, p = 9/32 < 1, 1 - p = 23/32, and def:emitnorm the identity map with
Delta_s = 0 and no lift.

THE EMITTED TARGET, Eq. eq:blindtarget at |Blmode| = 1:
H(Q) = H(C_<=0) (+) H(flag), dimension 1 + 2 = 3, sectors ((nb,0),(nb,a),(nb,b)):
  F_a = diag(19/32, 29/32, 3/16) ,  F_b = diag(13/32, 3/32, 13/16) ,
summing entrywise to 1_3. THE TWO DIMENSION FORMULAS COINCIDE HERE --
1 + 1*2 = 3 = 1*(1 + 2) -- which is the degenerate row of
BLINDING_DIMENSION_CASES and is why PRR-2 is frozen beside this case.

THE LICENSED ROUTE. On ``licensed`` the emitted list carries one entry per
outcome with relation >= and constant 0 (cor:entries: "each constant either 0, or
a declared q_t, or a declared device constant"). ZERO IS A LATTICE NUMBER AT
EVERY kappa, so no constant of this case is rounded and cor:entries' rounding
clause -- "a caller-requested entry whose declared constant is NOT a lattice
number is rounded in the direction that enlarges the feasible set" -- is not
reached. The caller's marginal tau_A = diag(1/2, 1/2) is dyadic, and no row of
this contract decides it: thm:licence (iv) makes the right-hand side THE
DECLARATION'S, supplied by the caller, and this module only multiplies it by the
constant it certifies -- which here is 0.""",
    route_b="""\
ROUTE B -- BY SPECIALIZATION RATHER THAN BY RE-DERIVATION, AND THE TWO MEET ON
THE PRESERVED SECTOR.

PRR-2's emitted F_a on the five-sector target is
diag(19/32, 29/32, 3/16, 1, 0). def:blindmodel's degenerate case says the
no-blinding declaration is the same construction with the bl1 branch absent, so
DELETING THE LAST TWO SECTORS of PRR-2's target must give this case's target.
It does: (19/32, 29/32, 3/16) and (13/32, 3/32, 13/16). That is a check with
teeth, because the flag entries depend on p and 1 - p, and p is the SAME here
(9/32) only because the two declarations carry the same certified weights -- had
the substitution changed either weight between the two cases, the specialization
would visibly fail.

THE COMPLETENESS, BY THE COMPLEMENT ROUTE. sec:outputs requires 1 - p to be
"RECOMPUTED from the rounded weights and not rounded on its own, because the flag
sector's completeness is the identity sum_v p_v + (1 - p) = 1". Check it as an
integer identity over 2^-5: p_a = 6/32, p_b = 3/32, 1 - p = 23/32, and
6 + 3 + 23 = 32. Then each flag column of the target sums to
p_a + p_b + (1 - p) = 1 without any further arithmetic, which is the second
route to the entrywise sums route A computed one at a time.

THE DIMENSION, BY THE SECTOR COUNT. |S| = 1 preserved + |V| = 2 flags = 3
sectors of dimension 1, total 3, against thm:blinding (iii)'s
sum_{m<=0} dim H(C_m) + |Blmode||V| = 1 + 1*2 = 3.""",
    agreement="""\
THE LINE WHERE THE TWO ROUTES AGREE. Route A constructs the three-sector target
from p_v and 1 - p; route B obtains it by deleting PRR-2's two blinded sectors
and checks completeness through the integer identity 6 + 3 + 23 = 32. Both return
F_a = diag(19/32, 29/32, 3/16) and F_b = diag(13/32, 3/32, 13/16), dimension 3,
p = 9/32, Delta_s = 0 and no lift.""",
)


# ---------------------------------------------------------------------------
#  PR-R4 .. PR-R6 -- the three refusing variants of the RC2-shaped fixture
# ---------------------------------------------------------------------------
#
#  Each is PRR-1's declaration with ONE datum changed, and each exists because a
#  golden test asserts a refusal that the 0.3.0 fixtures can no longer reach:
#  1.0.1 refuses them earlier, under `declaration_not_exactly_admissible` or
#  `probe_weights_ill_formed`, so the row under test is never decided. With the
#  dyadic declaration the intended row is reached and the reason string is the
#  contract's own.


@dataclass(frozen=True)
class DyadicRefusalCase:
    """PRR-1's declaration with one datum changed, and the row that fires."""

    case_id: str
    claims: tuple[str, ...]
    #: What is changed relative to PR_R1, in words and in numbers.
    change: str
    changed_data: tuple[tuple[str, F], ...]
    #: The reason string the contract writes for this row, VERBATIM.
    refusal_reason: str
    #: The fail-closed rule that decides it.
    rule: str
    #: The rows that still ADMIT, so that the refusal is attributable.
    admitting_rows: tuple[str, ...]
    labels: tuple[str, ...]
    route_a: str
    route_b: str
    agreement: str


PR_R4 = DyadicRefusalCase(
    case_id="PRR-4-non-absorbing",
    claims=("PR6", "PR12"),
    change=(
        "PRR-1 with per-port dark counts (0, 1/4) instead of (3/16, 1/4), and the "
        "bounded letter moved from y_mc to y_1 with slot weight 3/16 instead of "
        "1/5. Both new numbers are dyadic; the 0.3.0 fixture's dark counts were "
        "ALREADY dyadic and are unchanged in kind."
    ),
    changed_data=(("p_dc|1", F(0)), ("p_dc|2", F(1, 4)), ("p_1 at y_1", F(3, 16))),
    refusal_reason="bounded_letter_not_absorbing",
    rule="absorbing",
    admitting_rows=(
        "lattice_exponent",
        "requested_assurance",
        "receiver_spec",
        "cutoff",
        "block_structure",
        "exact_admissibility",
        "fibre",
        "column_stochastic",
        "descent",
        "probe_weights",
        "high_photon_slot",
    ),
    labels=("eq:absorbing", "rem:absorbneeded", "cor:oneabsorbing"),
    route_a="""\
ROUTE A. With p_dc|1 = 0 and p_dc|2 = 1/4 the product form gives
  col e  : ((1)(3/4), 0, (1)(1/4), 0) = (3/4, 0, 1/4, 0) ;
  col 1  : (0, 3/4, 0, 1/4) ;
  col 2  : (0, 0, 1, 0) ;
  col 12 : (0, 0, 0, 1) ,
every entry an integer multiple of 2^-2 and every column summing to 1, so the
column-stochasticity row ADMITS; every non-zero entry has S' subset S, so the
descent row ADMITS. The bounded letter is y_1, whose fibre is {{1}} exactly, so
the fibre row ADMITS.

Eq. eq:absorbing asks R^cg_{y_1|y_1} = 1. It is 3/4, because port 2 can still
fire spuriously and carry a {1} pattern to {1,2}. THE ROW REFUSES, under
``bounded_letter_not_absorbing``, and rem:absorbneeded is why it must:
without the hypothesis eq:weightroute is false IN THE UNSAFE DIRECTION.
No artifact is emitted and no weight is computed.""",
    route_b="""\
ROUTE B. The same conclusion from cor:oneabsorbing rather than from the matrix.
The corollary says a non-zero r_min can occur only at r = 1 and that under
Eq. eq:canonicalcg every bounded letter of a MONOTONE column-stochastic R is
absorbing WHEN THE BOUNDED SET IS MC. Here the bounded set is NOT MC -- it is the
singleton fibre of y_1 -- so the corollary's hypothesis fails and absorption is
not available. Reading the column directly: R^cg_{y_1|y_1} = 1 would require the
{1} column to have all its mass on rows in cg^{-1}(y_1) = {{1}}, i.e. no dark
count at port 2, which the declaration p_dc|2 = 1/4 contradicts by exactly 1/4.
So R^cg_{y_1|y_1} = 1 - 1/4 = 3/4, ARRIVED AT BY SUBTRACTION rather than by the
product form.""",
    agreement="""\
Both routes return R^cg_{y_1|y_1} = 3/4 != 1 and the refusal
``bounded_letter_not_absorbing``, route A by evaluating the product form and
route B by subtracting the escaping mass from 1.""",
)

PR_R5 = DyadicRefusalCase(
    case_id="PRR-5-total-weight-one",
    claims=("PR6", "PR12"),
    change=(
        "PRR-1's settings and q_t with the two-letter alphabet {a, b}, blocks 1/2 "
        "each, identity dark counts and a slot weight of 1 at letter a. Every one "
        "of those numbers was ALREADY dyadic in the 0.3.0 fixture; the only change "
        "is the q_t, and it is the change that lets the intended row fire."
    ),
    changed_data=(("block at a", F(1, 2)), ("block at b", F(1, 2)), ("p_1 at a", F(1))),
    refusal_reason="total_weight_not_below_one",
    rule="total_weight",
    admitting_rows=(
        "lattice_exponent",
        "probe_weights",
        "exact_admissibility",
        "high_photon_slot",
        "column_stochastic",
        "descent",
        "absorbing",
        "fibre",
    ),
    labels=("lem:ple1", "rem:peqone", "eq:latdown"),
    route_a="""\
ROUTE A. The slot row admits: p_1 = 1 >= 0 and sum_i p_i = 1 <= 1, which is the
row's stated bound and is NOT strict. Identity dark counts give r_min = 0, so
eq:weightroute gives p^_(a,t) = q_t * 1 = q_t, i.e. 43/64 and 21/64. Both are
already lattice numbers at kappa = 12, so eq:latdown is the identity and
p_(a,t_off) = 43/64, p_(a,t_on) = 21/64. Then
p = 43/64 + 21/64 = 64/64 = 1, accumulated in the declared order of V, and the
total-weight row tests p < 1 STRICTLY. IT REFUSES, under
``total_weight_not_below_one``.

WHY THIS IS THE CASE THAT SHOWS THE ROUNDING DOES NOT RESCUE IT. eq:latdown only
lowers, so a declaration whose ROUTED total is 1 could in principle be rounded
below 1 and admitted -- which would be a silent clip of exactly the kind
rem:peqone forbids. It is not, HERE, because both routed weights already lie on
the lattice: sum_t q_t = 1 exactly is a declared validity condition
(``probe_declaration`` row), so at p_1 = 1 and r_min = 0 the routed total is
sum_t q_t = 1 for EVERY admissible declaration, and each term rounds to itself.
"Refused, not clipped" (rem:peqone).""",
    route_b="""\
ROUTE B. Without computing either weight. eq:weightroute at r_min = 0 gives
p_(y_i,t) = lat(q_t p_i), and every q_t satisfies eq:latinv by the
``probe_declaration`` row, so at p_i = 1 the product q_t p_i IS q_t, a lattice
number, and lat fixes it. Hence sum_v p_v = sum_t q_t = 1 by the declared
validity condition, WITHOUT EVALUATING 43/64 OR 21/64 AT ALL. The comparison
1 < 1 is false and the row refuses. lem:ple1 is consistent: it forbids p > 1
when H(B_{>N}) is non-trivial, and says nothing about p = 1, which is exactly
why the row "runs unconditionally".""",
    agreement="""\
Both routes return p = 1 and the refusal ``total_weight_not_below_one``: route A
by evaluating 43/64 + 21/64 = 1, route B by the declared identity sum_t q_t = 1
without evaluating either term.""",
)

PR_R6 = DyadicRefusalCase(
    case_id="PRR-6-conditional-family-incomplete",
    claims=("PR6", "PR12", "PR13"),
    change=(
        "PRR-1 with every block set to 1/4 and the (y_mc, t_on) block set to 1/2, "
        "so the family sums to 5/4 at t_on and to 1 at t_off. Both values were "
        "ALREADY dyadic in the 0.3.0 fixture and are unchanged; what changes is "
        "the REASON STRING, because 1.0.0 removed `declaration_outside_tolerance` "
        "from the vocabulary."
    ),
    changed_data=(
        ("block at every (y, t)", F(1, 4)),
        ("block at (y_mc, t_on)", F(1, 2)),
    ),
    refusal_reason="declaration_not_exactly_admissible",
    rule="exact_admissibility",
    admitting_rows=(
        "lattice_exponent",
        "requested_assurance",
        "receiver_spec",
        "cutoff",
        "block_structure",
        "probe_weights",
        "column_stochastic",
        "descent",
        "absorbing",
        "fibre",
    ),
    labels=("def:exactadm", "eq:latinv", "lem:latsum"),
    route_a="""\
ROUTE A. The declared blocks are 1/4 at every (letter, setting) except
(y_mc, t_on), which is 1/2. Every entry satisfies eq:latinv at j = 2. The four
of def:exactadm (c)'s conditions that do not mention the sum are met: the sector
map is unchanged, a real 1 x 1 block is its own adjoint, and 1/4 and 1/2 are
positive. CONDITION (d) FAILS AT t_on: 1/4 + 1/4 + 1/4 + 1/2 = 5/4 != 1 = id_1
on the block. The row refuses under ``declaration_not_exactly_admissible``,
NAMING WHICH CONJUNCT FAILED, which is what that row's "the refusal names which
one failed" requires.

THE VERDICT AND THE DATUM ARE UNCHANGED FROM 0.3.0; only the reason moves.
0.1.3 refused this datum under ``no_block_structure``; 0.2.0/0.3.0 under
``declaration_outside_tolerance`` at eps_op = 0; 1.0.0 removed that string from
the vocabulary (SCOPE_MARKS_1_0_0) and decides the same conjunct under
``declaration_not_exactly_admissible``. The structural half stays with
``no_block_structure`` -- "a comparison of declared labels, kinds, dimensions and
orders; no arithmetic" -- and PASSES here, which is what makes the two rows
distinguishable on this one declaration.""",
    route_b="""\
ROUTE B. By the residue rather than by the sum. def:exactadm (e) is stated on the
ADDITIONS, so run the accumulation in the declared order of Y at t_on over 2^-2:
1 + 1 + 1 = 3 after three additions, then 3 + 2 = 5, against the required 4. The
computed sum EXCEEDS the identity by 1/4 = 2^-2, one lattice step at j = 2 and
1024 lattice steps at kappa = 12 -- a defect far too large to be a rounding
artefact of any kind, which is the point: lem:latsum guarantees every addition
here is exact (kappa + ceil(log2 4) = 14 <= 53), so the computed sum IS the sum,
and condition (d) rather than condition (e) is what fails. Had the accumulation
been the thing at fault, (e) would have named it and the refusal would still be
the same string -- which is why the row names the conjunct.""",
    agreement="""\
Both routes return a completeness failure of exactly 1/4 at t_on and the refusal
``declaration_not_exactly_admissible``: route A by the closed sum 5/4, route B by
the ordered accumulation 1 + 1 + 1 + 2 = 5 over 2^-2 against the required 4, with
lem:latsum ruling out (e) so that (d) is the named conjunct.""",
)


# ---------------------------------------------------------------------------
#  PR-R7 -- the five column-stochasticity cases, dyadic
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DyadicColumnStochasticCase:
    """One declared dark-count matrix R, dyadic, and the two rows that see it."""

    case_id: str
    claims: tuple[str, ...]
    ports: int
    patterns: tuple[str, ...]
    #: The RAW declared R over 2^[K], column by column:
    #: (column pattern, ((row pattern, entry), ...)). "e" is the empty pattern.
    raw_matrix: tuple[tuple[str, tuple[tuple[str, F], ...]], ...]
    column_sums: tuple[tuple[str, F], ...]
    min_entry: F
    non_negative: bool
    unit_columns: bool
    all_entries_on_lattice: bool
    column_stochastic_row_admits: bool
    coarse_graining: tuple[tuple[str, str], ...]
    descended_matrix: tuple[tuple[str, tuple[tuple[str, F], ...]], ...]
    monotone: bool
    descends: bool
    descent_row_admits: bool
    bounded_letter: str
    absorbing: bool
    r_min: F
    #: eq:weightroute at p_1 = 3/32 and q = (43/64, 21/64), before and after
    #: eq:latdown, and whether the total-weight row admits the result.
    routed_total_hat: F
    emitted_weights: tuple[tuple[str, F], ...]
    emitted_total: F
    total_weight_row_admits: bool
    #: The declared 1 x 1 blocks that let the case reach ``reduce``.
    declared_blocks: tuple[tuple[str, F], ...]
    #: def:emitnorm on that block, per setting: (setting, residue, Delta_s).
    emission: tuple[tuple[str, F, F], ...]
    lift_fires: bool
    reason: str
    labels: tuple[str, ...]
    route_a: str
    route_b: str
    agreement: str


#: The declared slot, probe weights and blocks shared by all five, so that the
#: only thing varying between them is R. The blocks give the first letter
#: 1 - 5(|Y| - 1)/32 and every other letter 5/32, so the family sums to 1
#: EXACTLY at every setting and def:exactadm (c) holds at every case.
CS_SLOT_WEIGHT_PR_R: F = F(3, 32)
CS_PROBE_WEIGHTS_PR_R: tuple[tuple[str, F], ...] = (
    ("t_off", F(43, 64)),
    ("t_on", F(21, 64)),
)
CS_CG_CANONICAL_PR_R: tuple[tuple[str, str], ...] = (
    ("e", "y_empty"),
    ("1", "y_1"),
    ("2", "y_2"),
    ("12", "y_mc"),
)
CS_CG_MERGING_PR_R: tuple[tuple[str, str], ...] = (
    ("e", "y_0"),
    ("1", "y_d"),
    ("2", "y_d"),
    ("12", "y_mc"),
)

CS_CANONICAL_ADMIT_PR_R = DyadicColumnStochasticCase(
    case_id="PRR-7a-cs-canonical-admit",
    claims=("PR6", "PR12"),
    ports=2,
    patterns=("e", "1", "2", "12"),
    raw_matrix=(
        ("e", (("e", F(39, 64)), ("1", F(9, 64)), ("2", F(13, 64)), ("12", F(3, 64)))),
        ("1", (("e", F(0)), ("1", F(3, 4)), ("2", F(0)), ("12", F(1, 4)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(13, 16)), ("12", F(3, 16)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(1)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(0),
    non_negative=True,
    unit_columns=True,
    all_entries_on_lattice=True,
    column_stochastic_row_admits=True,
    coarse_graining=CS_CG_CANONICAL_PR_R,
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(39, 64)),
                ("y_1", F(9, 64)),
                ("y_2", F(13, 64)),
                ("y_mc", F(3, 64)),
            ),
        ),
        (
            "y_1",
            (("y_empty", F(0)), ("y_1", F(3, 4)), ("y_2", F(0)), ("y_mc", F(1, 4))),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(13, 16)), ("y_mc", F(3, 16))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    monotone=True,
    descends=True,
    descent_row_admits=True,
    bounded_letter="y_mc",
    absorbing=True,
    r_min=F(3, 64),
    routed_total_hat=F(279, 2048),
    emitted_weights=(("t_off", F(187, 2048)), ("t_on", F(183, 4096))),
    emitted_total=F(557, 4096),
    total_weight_row_admits=True,
    declared_blocks=(
        ("y_empty", F(17, 32)),
        ("y_1", F(5, 32)),
        ("y_2", F(5, 32)),
        ("y_mc", F(5, 32)),
    ),
    emission=(("t_off", F(0), F(11, 131072)), ("t_on", F(0), F(11, 131072))),
    lift_fires=False,
    reason="",
    labels=("lem:descent", "rem:colstoch", "prop:route", "eq:weightroute"),
    route_a="""\
ROUTE A. THE REGRESSION ANCHOR, and it is PRR-1's declaration read one level
lower: PRR-1 freezes R^cg, and the column-stochasticity row's subject is the RAW
R over 2^[K]. Under the canonical cg at K = 2 the two agree entry for entry,
because MC = {{1,2}} is a single pattern and cg is therefore a BIJECTION -- which
is exactly why the merging case sits beside this one.

BOTH SUBRULES, DECIDED EXACTLY. NON-NEGATIVITY: the smallest entry anywhere is 0,
and 0 >= 0. UNIT COLUMNS: 39/64 + 9/64 + 13/64 + 3/64 = 1; 3/4 + 1/4 = 1;
13/16 + 3/16 = 1; 1 = 1. NEITHER IS AN INSTANCE OF lem:exactpsd: the row is a
sign-and-equality comparison on the declared entries of R.

WHAT THE ROW DOES NOT DO A SECOND TIME (rem:colstoch): the fibres of cg partition
2^[K], so R^cg_{y|y'} = sum_{S in cg^{-1}(y)} R_{S|S'} >= 0 as a sum of
non-negative entries and sum_y R^cg_{y|y'} = sum_S R_{S|S'} = 1. Deciding it on R
DISCHARGES IT FOR R^cg, and no second row is stated. 1.0.0 strengthens the
statement: "in the exact substrate a regrouped sum IS the sum it regroups", so
1.0.0 decides one matrix where its superseded draft measured two.

EVERYTHING ELSE ADMITS, which is what an anchor is for; the route is PRR-1's,
r_min = 3/64, p^ = 279/2048, emitted 187/2048 and 183/4096, total 557/4096 < 1.""",
    route_b="""\
ROUTE B. The column sums as integer identities over 2^-6 -- 39 + 9 + 13 + 3 = 64,
48 + 16 = 64, 52 + 12 = 64, 64 -- and the descent implication checked on the
DESCENDED matrix rather than assumed: R^cg's four column sums are the same four
integers, because each fibre is a singleton and the regrouping is trivial. A
second, non-trivial check of the same implication is the merging case below,
where the regrouping is a genuine two-term addition.""",
    agreement="""\
Both routes return non_negative = True, unit_columns = True, and the same four
unit column sums; the route numbers are PRR-1's and agree with it line for line.""",
)

CS_COARSE_ADMIT_PR_R = DyadicColumnStochasticCase(
    case_id="PRR-7b-cs-coarse-admit",
    claims=("PR6", "PR12"),
    ports=2,
    patterns=("e", "1", "2", "12"),
    raw_matrix=(
        (
            "e",
            (
                ("e", F(169, 256)),
                ("1", F(39, 256)),
                ("2", F(39, 256)),
                ("12", F(9, 256)),
            ),
        ),
        ("1", (("e", F(0)), ("1", F(13, 16)), ("2", F(0)), ("12", F(3, 16)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(13, 16)), ("12", F(3, 16)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(1)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(0),
    non_negative=True,
    unit_columns=True,
    all_entries_on_lattice=True,
    column_stochastic_row_admits=True,
    coarse_graining=CS_CG_MERGING_PR_R,
    descended_matrix=(
        ("y_0", (("y_0", F(169, 256)), ("y_d", F(39, 128)), ("y_mc", F(9, 256)))),
        ("y_d", (("y_0", F(0)), ("y_d", F(13, 16)), ("y_mc", F(3, 16)))),
        ("y_mc", (("y_0", F(0)), ("y_d", F(0)), ("y_mc", F(1)))),
    ),
    monotone=True,
    descends=True,
    descent_row_admits=True,
    bounded_letter="y_mc",
    absorbing=True,
    r_min=F(9, 256),
    routed_total_hat=F(1029, 8192),
    emitted_weights=(("t_off", F(345, 4096)), ("t_on", F(21, 512))),
    emitted_total=F(513, 4096),
    total_weight_row_admits=True,
    declared_blocks=(("y_0", F(11, 16)), ("y_d", F(5, 32)), ("y_mc", F(5, 32))),
    emission=(("t_off", F(0), F(5, 131072)), ("t_on", F(0), F(5, 131072))),
    lift_fires=False,
    reason="",
    labels=("lem:descent", "eq:descend", "rem:colstoch", "rem:fibre"),
    route_a="""\
ROUTE A. THE ANCHOR THAT MAKES THE DESCENT IMPLICATION NON-TRIVIAL. cg MERGES the
two single-click patterns, so cg^{-1}(y_d) = {{1},{2}} is a FIBRE OF SIZE TWO and
R^cg_{y_d|y'} is a genuine SUM of two entries of R.

THE DECLARATION. Independent per-port dark counts with the SAME probability
p_dc = 3/16 at BOTH ports -- symmetric, which is what makes the two single-click
columns agree and hence what makes R descend through this cg:
  col e  : ((13/16)^2, (3/16)(13/16), (13/16)(3/16), (3/16)^2)
         = (169/256, 39/256, 39/256, 9/256), summing to 256/256 = 1 ;
  col 1  : (0, 13/16, 0, 3/16) ;  col 2 : (0, 0, 13/16, 3/16) ;
  col 12 : (0, 0, 0, 1) .
The symmetry is FORCED BY THE FIXTURE'S MEANING, not chosen for convenience:
had the two ports carried different dark-count probabilities the two columns
would differ and the declaration would be refused ``dark_counts_do_not_descend``.

DESCENT, TESTED DIRECTLY. P(y|S') = sum_{S in cg^{-1}(y)} R_{S|S'}:
  P(y_0|.)  = (169/256, 0, 0, 0) over columns e, 1, 2, 12 ;
  P(y_d|.)  = (39/128, 13/16, 13/16, 0)  -- 39/256 + 39/256 = 39/128 in column e ;
  P(y_mc|.) = (9/256, 3/16, 3/16, 1) .
The two columns with cg-image y_d agree in every row, so R^cg is WELL DEFINED.

AND rem:colstoch's IMPLICATION IS NON-TRIVIALLY TRUE HERE: R^cg's y_0 column sums
to 169/256 + 78/256 + 9/256 = 256/256 = 1, with the middle term FORMED BY THE
ADDITION the fibre of size two performs.

THE ROUTE. cg^{-1}(y_mc) = MC exactly; R^cg_{y_mc|y_mc} = 1, absorbing;
r_min = min(9/256, 3/16) = 9/256 from the empty column. eq:weightroute at
p_1 = 3/32: (1 - 9/256)(3/32) + 9/256 = 741/8192 + 288/8192 = 1029/8192.
Then q_off (43/64) gives 44247/524288 and q_on (21/64) gives 21609/524288, and
524288/4096 = 128, so eq:latdown floors 44247/128 = 345 + 87/128 to 345 and
21609/128 = 168 + 105/128 to 168: emitted 345/4096 and 168/4096 = 21/512, total
513/4096 < 1029/8192 = 514.5/4096. BOTH ROUNDINGS BITE AND BOTH LOWER.

def:emitnorm ON THE DECLARED BLOCK. M~ = (1859/4096, 689/2048, 859/4096) summing
to 1; times q_t and rounded to 2^-12 gives (1249, 926, 577)/4096 at t_off with
1249 + 926 + 577 = 2752 = 43 * 64, and (610, 452, 282)/4096 at t_on -- written
in lowest terms as 305/2048, 113/1024, 141/2048 -- with
610 + 452 + 282 = 1344 = 21 * 64. BOTH RESIDUES ZERO. Every entry positive, so
eq:psdtest at d = 1 passes and NO LIFT FIRES. Delta_s = 10/262144 = 5/131072.""",
    route_b="""\
ROUTE B. Integers over 2^-8. The declared columns are (169, 39, 39, 9),
(0, 208, 0, 48), (0, 0, 208, 48), (0, 0, 0, 256) over 256, and the four column
sums are 169 + 39 + 39 + 9 = 256, 208 + 48 = 256, 208 + 48 = 256, 256.

DESCENT WITHOUT COMPUTING R^cg. R descends through cg iff the columns of any two
patterns with the same cg-image are equal AFTER regrouping the rows by fibre.
Columns 1 and 2 are (0, 208, 0, 48) and (0, 0, 208, 48); regrouping rows {1} and
{2} into y_d turns both into (0, 208, 48) over 256. EQUAL, so R descends -- and
the check never forms the y_0 column at all, which is the column route A used.

THE ROUTE, BY THE COMPLEMENTARY FORM. eq:weightroute is
p^ = p_1 + r_min(1 - p_1) as well as (1 - r_min)p_1 + r_min. Evaluate the first:
3/32 + (9/256)(29/32) = 768/8192 + 261/8192 = 1029/8192. AGREES with route A's
741/8192 + 288/8192.

THE FLOORS, BY INTEGER DIVISION. 43 * 1029 = 44247 and 44247 = 345 * 128 + 87, so
the floor is 345; 21 * 1029 = 21609 = 168 * 128 + 105, floor 168. And the two
remainders 87 + 105 = 192 = 128 + 64, i.e. one and a half lattice steps, so the
emitted total is 514 - 1 = 513 over 4096 against the routed 514.5 -- which is why
the total falls by exactly one step and not two.""",
    agreement="""\
Route A forms R^cg and reads its y_0 column; route B never forms it and decides
descent by regrouping the two single-click columns. Route A evaluates
eq:weightroute as (1 - r_min)p_1 + r_min; route B as p_1 + r_min(1 - p_1). Both
return R^cg's y_d entry 39/128, r_min = 9/256, p^ = 1029/8192, the emitted
345/4096 and 21/512, and the total 513/4096.""",
)

CS_COLSUM_REFUSE_PR_R = DyadicColumnStochasticCase(
    case_id="PRR-7c-cs-colsum-refuse",
    claims=("PR6", "PR12"),
    ports=2,
    patterns=("e", "1", "2", "12"),
    raw_matrix=(
        ("e", (("e", F(39, 64)), ("1", F(9, 64)), ("2", F(13, 64)), ("12", F(5, 128)))),
        ("1", (("e", F(0)), ("1", F(3, 4)), ("2", F(0)), ("12", F(1, 4)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(13, 16)), ("12", F(3, 16)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(127, 128)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(0),
    non_negative=True,
    unit_columns=False,
    all_entries_on_lattice=True,
    column_stochastic_row_admits=False,
    coarse_graining=CS_CG_CANONICAL_PR_R,
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(39, 64)),
                ("y_1", F(9, 64)),
                ("y_2", F(13, 64)),
                ("y_mc", F(5, 128)),
            ),
        ),
        (
            "y_1",
            (("y_empty", F(0)), ("y_1", F(3, 4)), ("y_2", F(0)), ("y_mc", F(1, 4))),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(13, 16)), ("y_mc", F(3, 16))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    monotone=True,
    descends=True,
    descent_row_admits=True,
    bounded_letter="y_mc",
    absorbing=True,
    r_min=F(5, 128),
    routed_total_hat=F(529, 4096),
    emitted_weights=(("t_off", F(355, 4096)), ("t_on", F(173, 4096))),
    emitted_total=F(33, 256),
    total_weight_row_admits=True,
    declared_blocks=(
        ("y_empty", F(17, 32)),
        ("y_1", F(5, 32)),
        ("y_2", F(5, 32)),
        ("y_mc", F(5, 32)),
    ),
    emission=(),
    lift_fires=False,
    reason="dark_counts_not_column_stochastic",
    labels=("rem:tolboundary", "rem:colstoch", "sec:failclosed"),
    route_a="""\
ROUTE A. THE CONTRACT'S OWN DEFECT EXAMPLE, dyadically: "a DARK-COUNT MATRIX
WHOSE COLUMNS SUM TO 1 ONLY TO WITHIN A ROUNDING ERROR, say -- IS STILL REFUSED,
NOW BY THE COLUMN-STOCHASTICITY ROW AND UNDER ITS OWN REASON STRING"
(rem:tolboundary). It is PRR-7a with the (12 | e) entry lowered from 3/64 = 6/128
to 5/128, so column e sums to 127/128.

WHY THE DEFECT IS 1/128 AND NOT THE 0.3.0 FIXTURE'S 1/100. A defect that is
itself off the lattice would make the declaration fail eq:latinv, and the
declaration would then be refused by a DIFFERENT row before the
column-stochasticity row was reached -- so the case would stop testing what it
exists to test. 1/128 is a lattice number at kappa = 12 (j = 7), it is the
nearest such to 1/100 at j = 7, and it is the smallest defect that is still
exactly representable at every kappa >= 7.

THE DECISION. NON-NEGATIVITY: the smallest entry is 0, ADMITS. UNIT COLUMNS:
39/64 + 9/64 + 13/64 + 5/128 = 78/128 + 18/128 + 26/128 + 5/128 = 127/128 != 1.
REFUSES, under ``dark_counts_not_column_stochastic``.

THE REFUSAL DOES NOT ARRIVE UNDER ANOTHER ROW, and that is why the route numbers
are frozen on a refused case. Monotonicity holds (every non-zero entry has
S' subset S); cg is a bijection so it descends; the bounded set is exactly MC;
R^cg_{y_mc|y_mc} = 1, absorbing; and the routed weights are below 1 --
r_min = min(5/128, 1/4, 3/16) = 5/128, p^ = (1 - 5/128)(3/32) + 5/128
= 369/4096 + 160/4096 = 529/4096, ALREADY A LATTICE NUMBER, and
lat((43/64)(529/4096)) = 355/4096, lat((21/64)(529/4096)) = 173/4096, total
528/4096 = 33/256 < 1. THE TOTAL-WEIGHT ROW ADMITS. Only the new row refuses.

AT 1.0.0 THERE IS NO SECOND DECISION TO FREEZE. The 0.3.0 case was run at
eps_op = 0 and eps_op = 1/100 to show which row carried the reason; the declared
operator tolerance LEAVES THE CONTRACT at 1.0.0 (SCOPE_MARKS_1_0_0), so there is
one decision and one reason, and the pair of runs is retired rather than
re-based.""",
    route_b="""\
ROUTE B. Over 2^-7 as integers: column e is (78, 18, 26, 5) over 128, summing to
127, one short of 128. The deficit is exactly 1 unit at 2^-7, which is the
defect as declared and not a residue of the arithmetic -- lem:latsum with
kappa = 12 and L = 4 makes every addition in the accumulation exact, so the
computed sum IS 127/128 and the comparison with 1 is decided rather than
measured.

THE ROUTE, INDEPENDENTLY. p^ = p_1 + r_min(1 - p_1) = 3/32 + (5/128)(29/32)
= 384/4096 + 145/4096 = 529/4096, agreeing with route A's
369/4096 + 160/4096. The two floors: 43 * 529 = 22747 = 355 * 64 + 27, floor 355;
21 * 529 = 11109 = 173 * 64 + 37, floor 173; and 27 + 37 = 64 = one lattice step,
so the emitted total is 529 - 1 = 528 over 4096 exactly.""",
    agreement="""\
Both routes return the column-e sum 127/128, the refusal
``dark_counts_not_column_stochastic``, r_min = 5/128, p^ = 529/4096 and the
emitted weights 355/4096 and 173/4096 with total 33/256 -- route A by rational
sums, route B by integer numerators over 2^-7 and 2^-12.""",
)

CS_NEGATIVE_VACUOUS_REFUSE_PR_R = DyadicColumnStochasticCase(
    case_id="PRR-7d-cs-negative-vacuous-refuse",
    claims=("PR6", "PR12"),
    ports=2,
    patterns=("e", "1", "2", "12"),
    raw_matrix=(
        ("e", (("e", F(39, 64)), ("1", F(9, 64)), ("2", F(13, 64)), ("12", F(3, 64)))),
        ("1", (("e", F(-3, 64)), ("1", F(3, 4)), ("2", F(0)), ("12", F(19, 64)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(13, 16)), ("12", F(3, 16)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(1)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(-3, 64),
    non_negative=False,
    unit_columns=True,
    all_entries_on_lattice=True,
    column_stochastic_row_admits=False,
    coarse_graining=CS_CG_CANONICAL_PR_R,
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(39, 64)),
                ("y_1", F(9, 64)),
                ("y_2", F(13, 64)),
                ("y_mc", F(3, 64)),
            ),
        ),
        (
            "y_1",
            (
                ("y_empty", F(-3, 64)),
                ("y_1", F(3, 4)),
                ("y_2", F(0)),
                ("y_mc", F(19, 64)),
            ),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(13, 16)), ("y_mc", F(3, 16))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    monotone=True,
    descends=True,
    descent_row_admits=True,
    bounded_letter="y_mc",
    absorbing=True,
    r_min=F(3, 64),
    routed_total_hat=F(279, 2048),
    emitted_weights=(("t_off", F(187, 2048)), ("t_on", F(183, 4096))),
    emitted_total=F(557, 4096),
    total_weight_row_admits=True,
    declared_blocks=(
        ("y_empty", F(17, 32)),
        ("y_1", F(5, 32)),
        ("y_2", F(5, 32)),
        ("y_mc", F(5, 32)),
    ),
    emission=(),
    lift_fires=False,
    reason="dark_counts_not_column_stochastic",
    labels=("rem:darkcompose", "sec:failclosed"),
    route_a="""\
ROUTE A. THE FIRST HALF OF rem:darkcompose'S BOUNDARY SENTENCE: "a NEGATIVE ENTRY
in a (D2)-forbidden position ... SATISFIES THE MONOTONICITY IMPLICATION VACUOUSLY
AND FAILS NON-NEGATIVITY."

PRR-7a with column 1 changed from (0, 3/4, 0, 1/4) to (-3/64, 3/4, 0, 19/64):
the forbidden position is row e, column {1}, where {1} is not a subset of the
empty set, and the compensating 3/64 goes to the multiclick row so the column
still sums to 1: -3/64 + 48/64 + 19/64 = 64/64.

THE COLUMN-STOCHASTICITY ROW REFUSES on the first subrule: the smallest entry is
-3/64 < 0. THE DESCENT ROW ADMITS: monotonicity is the IMPLICATION
R_{S|S'} > 0 => S' subset S, and -3/64 is not > 0, so the forbidden position
satisfies it VACUOUSLY; and cg is a bijection, so R descends. The two rows carry
DIFFERENT REASON STRINGS and an implementation that folded them into one test
would emit the wrong one here.

THE REFUSAL IS ATTRIBUTABLE: r_min = min(3/64, 19/64, 3/16) = 3/64 -- unchanged,
the negative entry not lying in row y_mc -- so the route numbers are PRR-1's
exactly and the total-weight row admits.""",
    route_b="""\
ROUTE B. Over 2^-6 as integers, column 1 is (-3, 48, 0, 19) summing to 64, so the
unit-column subrule is an integer identity and admits; and min over all 16
entries is -3, so the non-negativity subrule is an integer sign test and refuses.
Monotonicity checked as a truth table rather than as a scan: the forbidden
positions are the seven (S, S') pairs with S' not subset S, and the only one
carrying a non-zero entry is (e, {1}) at -3, which is not positive. THE
IMPLICATION IS TRUE AT EVERY POSITION, so the descent row's monotonicity half
admits without evaluating any product.""",
    agreement="""\
Both routes return min_entry = -3/64, four unit columns, the refusal
``dark_counts_not_column_stochastic`` from the column-stochasticity row and an
ADMIT from the descent row -- route A by inspecting the changed column, route B
by an integer sign test and a truth table over the forbidden positions.""",
)

CS_POSITIVE_FORBIDDEN_REFUSE_PR_R = DyadicColumnStochasticCase(
    case_id="PRR-7e-cs-positive-forbidden-refuse",
    claims=("PR6", "PR12"),
    ports=2,
    patterns=("e", "1", "2", "12"),
    raw_matrix=(
        ("e", (("e", F(39, 64)), ("1", F(9, 64)), ("2", F(13, 64)), ("12", F(3, 64)))),
        ("1", (("e", F(3, 64)), ("1", F(45, 64)), ("2", F(0)), ("12", F(1, 4)))),
        ("2", (("e", F(0)), ("1", F(0)), ("2", F(13, 16)), ("12", F(3, 16)))),
        ("12", (("e", F(0)), ("1", F(0)), ("2", F(0)), ("12", F(1)))),
    ),
    column_sums=(("e", F(1)), ("1", F(1)), ("2", F(1)), ("12", F(1))),
    min_entry=F(0),
    non_negative=True,
    unit_columns=True,
    all_entries_on_lattice=True,
    column_stochastic_row_admits=True,
    coarse_graining=CS_CG_CANONICAL_PR_R,
    descended_matrix=(
        (
            "y_empty",
            (
                ("y_empty", F(39, 64)),
                ("y_1", F(9, 64)),
                ("y_2", F(13, 64)),
                ("y_mc", F(3, 64)),
            ),
        ),
        (
            "y_1",
            (
                ("y_empty", F(3, 64)),
                ("y_1", F(45, 64)),
                ("y_2", F(0)),
                ("y_mc", F(1, 4)),
            ),
        ),
        (
            "y_2",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(13, 16)), ("y_mc", F(3, 16))),
        ),
        (
            "y_mc",
            (("y_empty", F(0)), ("y_1", F(0)), ("y_2", F(0)), ("y_mc", F(1))),
        ),
    ),
    monotone=False,
    descends=True,
    descent_row_admits=False,
    bounded_letter="y_mc",
    absorbing=True,
    r_min=F(3, 64),
    routed_total_hat=F(279, 2048),
    emitted_weights=(("t_off", F(187, 2048)), ("t_on", F(183, 4096))),
    emitted_total=F(557, 4096),
    total_weight_row_admits=True,
    declared_blocks=(
        ("y_empty", F(17, 32)),
        ("y_1", F(5, 32)),
        ("y_2", F(5, 32)),
        ("y_mc", F(5, 32)),
    ),
    emission=(),
    lift_fires=False,
    reason="dark_counts_do_not_descend",
    labels=("rem:darkcompose", "lem:descent", "sec:failclosed"),
    route_a="""\
ROUTE A. THE SECOND HALF OF rem:darkcompose'S SENTENCE: "a STRICTLY POSITIVE
entry in a (D2)-forbidden position FAILS MONOTONICITY WHILE LEAVING
COLUMN-STOCHASTICITY UNTOUCHED."

PRR-7a with column 1 changed from (0, 3/4, 0, 1/4) to (3/64, 45/64, 0, 1/4): the
positive 3/64 sits at row e, column {1}, and 3/4 - 3/64 = 45/64 keeps the column
summing to 1: 3/64 + 45/64 + 16/64 = 64/64.

THE COLUMN-STOCHASTICITY ROW ADMITS: the smallest entry is 0 and every column
sums to 1. THE DESCENT ROW REFUSES on its monotonicity half:
R_{e|{1}} = 3/64 > 0 but {1} is not a subset of the empty set. The row is a
conjunction of the two halves under ONE reason string, so the refusal is
``dark_counts_do_not_descend``, decided on the monotonicity half alone -- the
descent half itself holds, cg being a bijection.

WHY IT MATTERS BEYOND DIAGNOSIS. rem:darkcompose turns the two rows into the
statement that every declaration this module admits is exactly admissible in the
supplier's sense -- (D1) by the column-stochasticity row, (D2) by this one. Drop
either and that sentence fails.""",
    route_b="""\
ROUTE B. Over 2^-6, column 1 is (3, 45, 0, 16) summing to 64: an integer identity,
so column-stochasticity admits. Monotonicity as the same truth table used in
PRR-7d: the only forbidden position carrying a non-zero entry is (e, {1}), and
here the entry is +3, which IS positive, so the implication is FALSE at that
position and the monotonicity half fails. THE PAIR PRR-7d / PRR-7e DIFFERS IN
EXACTLY ONE SIGN, and the two rows swap verdicts, which is the checkable form of
"neither row covers the other".""",
    agreement="""\
Both routes return four unit columns, min_entry = 0, an ADMIT from the
column-stochasticity row and the refusal ``dark_counts_do_not_descend`` from the
descent row -- route A by reading the changed column, route B by the same
forbidden-position truth table as PRR-7d with the sign reversed.""",
)

CS_CASES_PR_R: tuple[DyadicColumnStochasticCase, ...] = (
    CS_CANONICAL_ADMIT_PR_R,
    CS_COARSE_ADMIT_PR_R,
    CS_COLSUM_REFUSE_PR_R,
    CS_NEGATIVE_VACUOUS_REFUSE_PR_R,
    CS_POSITIVE_FORBIDDEN_REFUSE_PR_R,
)

EMISSION_CASES_PR_R: tuple[DyadicEmissionCase, ...] = (PR_R1, PR_R2, PR_R3)
REFUSAL_CASES_PR_R: tuple[DyadicRefusalCase, ...] = (PR_R4, PR_R5, PR_R6)

#: EVERY REFUSAL REASON THIS GROUP FREEZES, and every one of them is a string
#: contract.tex 1.0.1 writes in Section 4.14. NO STRING IS INVENTED HERE, and
#: ``declaration_outside_tolerance`` -- which 1.0.0 removed -- appears nowhere.
REFUSAL_REASONS_USED_PR_R: tuple[str, ...] = (
    "bounded_letter_not_absorbing",
    "dark_counts_do_not_descend",
    "dark_counts_not_column_stochastic",
    "declaration_not_exactly_admissible",
    "total_weight_not_below_one",
)

#: WHAT THIS GROUP DOES NOT FREEZE, AND WHY. A list beside the entries, never a
#: field inside one.
NOT_FROZEN_AND_WHY_PR_R: tuple[tuple[str, str], ...] = (
    (
        "the positivity lift of def:emitnorm (4): its weight w and its dyadic vector u",
        "NO CASE IN THIS GROUP REACHES IT, and the reason is structural rather "
        "than lucky: every declared and every constructed preserved block here "
        "is 1 x 1 and real, so eq:psdtest at d = 1 is the single comparison "
        "e_1(X) = X >= 0; step (2) rounds to the NEAREST lattice multiple and "
        "the nearest multiple of 2^-kappa to a non-negative real is "
        "non-negative; and step (3)'s residue is exactly zero in every case, so "
        "it moves nothing into negative territory. The ladder is never entered. "
        "THAT IS DELIBERATE: the rule for u is the subject of open finding "
        "F-S2-PR-06 and is not fixed, so a case needing a lift could not be "
        "frozen here without deciding it.",
    ),
    (
        "the fail-closed row inventory and the emitted key vocabulary at 1.0.0",
        "Band 4 already froze them -- FAIL_CLOSED_ROW_COUNT_1_0_0 = 28, "
        "REFUSAL_REASONS_1_0_0, OUTPUT_KEYS_1_0_0 -- and this band re-points at "
        "them rather than restating them. A restatement would be a second home "
        "for one fact.",
    ),
    (
        "anything about tests/golden/test_receiver_povm_docking.py",
        "Its declarations are not hand-written device data: they are receiver "
        "REQUESTS whose artifact is produced by a floating-point evaluation, "
        "and no choice of dyadic device parameters puts that artifact on a "
        "lattice. See freeze/registry_group_RP_D.py, cases RPX-1 and RPX-2, for "
        "the two impossibility proofs, and freeze/parameters.md, family 5, for "
        "why the 1.0.0 answer is the instance's snap rather than new numbers.",
    ),
)
