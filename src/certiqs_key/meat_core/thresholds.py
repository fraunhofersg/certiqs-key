"""The interface's declared threshold rows -- one row, one constant.

SEVENTEEN LIVE ROWS IN TWO GROUPS, AND SIX RETIRED. The carrying rule is the
interface's and this module is written to it: MACHINE KEYS ARE BINDING FOR THE
IMPLEMENTATION; which constant carries a row is the implementation's business,
but EVERY ROW MUST BE CARRIED BY EXACTLY ONE, AND NO ROW MAY BE CARRIED BY TWO.

Collecting the numbers here, rather than as local constants across several
modules (some deciding two predicates at one value), is what makes the
one-to-one rule checkable, and :func:`carrying_table` is the check.

THE TWO GROUPS ARE NOT TWO KINDS OF THE SAME THING
==================================================
**Group A -- predicates on DECLARED data.** EVERY ROW IS DECIDED EXACTLY AND
CARRIES NO WINDOW. There is no number in this group, and no row has a value
to fill beyond the zero it is decided at. The reading is ``def:declaration``'s
exact-admissibility paragraph, which is the compiler's
``protocol-compiler/def:exact`` read on the numbers this module was handed, and
it is the STRICTER of the readings spec/architecture.md 2.8 licenses: it admits
a subset of what any window would, so nothing that passes here could have
failed the policy.

NO ROW OF THE TABLE IS DECIDED AT A DECLARED TOLERANCE: none exists, and
``bob_povm_admission`` is decided at exactly zero like the rest. One row,
``constraint_operator_exact``, is the interface's rather than a claim's.
Hermiticity of a constraint operator is a predicate on the declared numbers and
not a type condition, so it has a row.

**Group B -- predicates on objects THIS MODULE COMPUTED.** These are NOT
instances of the instance's tolerance AND MUST NOT BE DECLARED UNDER IT. Each is
a number of its own, declared BESIDE it and recorded in the run's
``optimizer_certificate`` and ``map_validation_report`` together with the worst
quantity it was compared against. The reason is stated once, for the group: what
these decide is ACCUMULATED ARITHMETIC ON ITERATES AND ON ORACLE RETURNS, not a
property of anybody's declaration -- so a window sized on declaration defects
would REFUSE CORRECT RUNS, and conversely a declaration admitted exactly says
nothing about them.

THE DIRECTION IS NOT OPEN. A Group B number may never be read as an instance of
the instance's tolerance, and that tolerance may never be read as a bound on one
(``frank-wolfe/rem:fo-oracle-repair``; ``frank-wolfe/rem:fo-iterate-repair``).

WHAT THE THRESHOLDS DO NOT BUY, recorded here because the contract records it in
the same breath as the rows. NO CLAIM OF THIS CONTRACT BOUNDS THE ERROR OF ANY
OF THE THREE QUANTITIES ``frank-wolfe/rem:fo-iterate-checks`` COMPARES (the third
exposure of ``frank-wolfe/rem:fo-check-exposures``):
``lambda_min`` of an iterate block is itself computed, so a block whose true
minimum eigenvalue is negative within the eigensolver's own backward error
passes at exactly 0 and is not repaired; and the coupling and ``bowtie_k``
residuals are formed by partial traces and sums that round, so a point whose
TRUE residual exceeds its window can be measured inside it. SO THE CONSUMED
POINT LIES IN ``Feas^J(epsilon)`` BY CONSTRUCTION ONLY UP TO THAT ARITHMETIC.
What the rows DO buy: that each comparison is well posed, that its reference is
fixed by this contract rather than chosen by an implementation, and that NO
WINDOW THIS CONTRACT DECLARES ADMITS A POINT AT WHICH THE THEOREM DOES NOT
APPLY.

THE VALUES ARE THE IMPLEMENTATION'S AND THE KEYS ARE NOT
========================================================
What the contract fixes: the machine key of every row, the object each decides,
whether the row is entrywise, a spectral floor, or exact, which rows are at
exactly 0, what each declared number is measured RELATIVE TO where it says so,
the one-to-one carrying rule, and that every Group B row is recorded with the
result. What it leaves open: the VALUES of the declared Group B numbers, and
whether they arrive as module constants, as fields of the run configuration, or
as instance declarations.

THE CHOICE MADE, AND IT IS THE LEAST-COMMITTAL ONE AVAILABLE: module constants,
at the values the engine runs at. Every number below is the engine's working
value, not a pick made here.

MOVING THEM TO THE RUN CONFIGURATION IS THE OTHER READING and is not taken here:
it is a decision about who declares them, which belongs to the run tier
(spec/architecture.md 3.3) and not to this module.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class ThresholdGroup(StrEnum):
    """Which of the interface's three threshold groups a row belongs to."""

    #: Predicates on DECLARED data. DECIDED EXACTLY, AT NO WINDOW.
    A = "group_a"
    #: Predicates on objects this module computed. Declared BESIDE the
    #: instance's tolerance, never under it.
    B = "group_b"
    #: Retired, each with the statement that replaced it.
    C = "group_c"


class ThresholdKind(StrEnum):
    """What sort of comparison a row makes."""

    #: An entrywise maximum modulus, per sector block.
    ENTRYWISE = "entrywise"
    #: A minimum eigenvalue. Never converted into an entrywise quantity or
    #: back: Eq. ``eq:normconv`` composes the two IN ONE DIRECTION ONLY.
    SPECTRAL_FLOOR = "spectral_floor"
    #: A bit-level identity of binary64 data, or an exact rational decision.
    #: No window of any kind.
    EXACT = "exact"
    #: A declared number read RELATIVE to a scale the contract names.
    RELATIVE = "relative"
    #: Not an operator predicate at all.
    NOT_A_PREDICATE = "not_a_predicate"


@dataclass(frozen=True)
class Threshold:
    """One row of the interface's ``declared_thresholds``.

    ``value`` is the declared number. EVERY GROUP A ROW CARRIES ``0.0``, the
    value it is decided at, and none of them carries a window: a windowed row
    would belong to a declared-tolerance apparatus that does not exist, and is
    named in :data:`RETIRED`.
    """

    #: The machine key, BINDING and transcribed from ``interface.yaml``.
    key: str
    group: ThresholdGroup
    kind: ThresholdKind
    #: The declared number, or ``None``. See the class docstring.
    value: float | None
    #: What the row decides, in one line.
    decides: str
    #: What the number is measured relative to, where the contract says so.
    relative_to: str | None = None
    #: Which module carries the comparison. EXACTLY ONE per row.
    carried_by: str = ""


#: Group A, row 1 of 7. Decided at exactly zero: there is no window
#: (:data:`RETIRED`).
BOB_POVM_ADMISSION = Threshold(
    key="bob_povm_admission",
    group=ThresholdGroup.A,
    kind=ThresholdKind.EXACT,
    value=0.0,
    decides=(
        "On the declared {F_v}, PER SECTOR BLOCK: the SECTOR MAP compared in "
        "its three components; Hermiticity; positive semidefiniteness, by an "
        "EXACT decision and never by a floating-point eigenvalue; and "
        "completeness, the sector sum being the identity. DECIDED EXACTLY, AT "
        "NO WINDOW: this module declares no numerical tolerance, reads none "
        "and emits none"
    ),
    carried_by="certiqs_key.meat_core.declaration.admission.admit_bob_povm_exact",
)

#: Group A, row 2. A ROW OF ITS OWN and not part of the one above: a
#: completeness defect of zero on a sum THAT ROUNDED does not say the family is
#: complete as declared, and the two differ in the unsafe direction by an
#: amount no declared number bounds.
BOB_POVM_SUMMATION_EXACT = Threshold(
    key="bob_povm_summation_exact",
    group=ThresholdGroup.A,
    kind=ThresholdKind.EXACT,
    value=0.0,
    decides=(
        "Every entrywise addition of eq:declorder is EXACT in binary64, so "
        "that the computed Sigma^{(s)} IS the real sum. A completeness defect "
        "is a defect of the COMPUTED sum while every consumer of it reads it "
        "as a defect of the REAL sum; without this row the two differ, IN THE "
        "UNSAFE DIRECTION AND BY AN AMOUNT NO DECLARED NUMBER BOUNDS"
    ),
    carried_by="certiqs_key.foundations.exact_admission.sum_rounds_nowhere",
)

#: Group A, row 3.
ALICE_POVM_EXACT = Threshold(
    key="alice_povm_exact",
    group=ThresholdGroup.A,
    kind=ThresholdKind.EXACT,
    value=0.0,
    decides=(
        "M_x Hermitian and sum_x M_x = 1_A entrywise, M_x >= 0 by the exact "
        "decision, AND the completeness sum verified to ROUND NOWHERE in an "
        "order this module fixes and records. A defect of 0 on the COMPUTED "
        "sum does not say the identity holds of the declared numbers, and the "
        "sites that consume it read it as an identity of REAL operators"
    ),
    carried_by="certiqs_key.meat_core.declaration.admission.admit_alice_povm_exact",
)

#: Group A, row 4.
ALICE_MARGINAL_EXACT = Threshold(
    key="alice_marginal_exact",
    group=ThresholdGroup.A,
    kind=ThresholdKind.EXACT,
    value=0.0,
    decides=(
        "tau_A Hermitian, tr tau_A = 1 and tau_A >= 0 by the exact decision, "
        "with the TRACE FORMED BY ADDITIONS OVER THE ROW INDEX VERIFIED TO "
        "ROUND NOWHERE. tr tau_A = 1 is read as an identity of REAL numbers in "
        "the proof of thm:choi, and diag(1, 2^-60, 2^-60) would otherwise pass "
        "with a computed trace of 1. A SINGULAR tau_A IS ADMISSIBLE"
    ),
    carried_by="certiqs_key.meat_core.declaration.admission.admit_alice_marginal_exact",
)

#: Group A, row 6. THE EXACT ISLAND: the one exception to the binary64 number
#: model, and the only row of this table decided over the rationals.
ACCEPTANCE_DATA_EXACT = Threshold(
    key="acceptance_data_exact",
    group=ThresholdGroup.A,
    kind=ThresholdKind.EXACT,
    value=0.0,
    decides=(
        "The declared acceptance data are a probability vector, resp. define a "
        "closed convex subset of the simplex (def:admissible-acceptance-set). Decided "
        "in EXACT "
        "RATIONAL ARITHMETIC on the platform's exact island"
    ),
    carried_by="certiqs_key.meat_core.declaration.validation.validate_acceptance_set",
)

#: Group A, row 5. THE INTERFACE'S RATHER THAN A CLAIM'S (its
#: ``fixed_by_this_file``). Hermiticity is a predicate on the declared NUMBERS
#: and not a type condition, so it is given a row; the tag and the typing are
#: recorded beside it and COMPARE NO NUMBERS.
CONSTRAINT_OPERATOR_EXACT = Threshold(
    key="constraint_operator_exact",
    group=ThresholdGroup.A,
    kind=ThresholdKind.EXACT,
    value=0.0,
    decides=(
        "Each declared hat O_k HERMITIAN BLOCK BY BLOCK and sector-block "
        "diagonal, and its right-hand side of the type its tag declares -- a "
        "real scalar for a `homogeneous` entry, a Hermitian Theta_k on A for a "
        "`general` one (def:admissible-declaration (iii), (vi); def:homog). POSITIVITY "
        "IS ASKED "
        "OF NO CONSTRAINT OPERATOR: no proof of this module reads it, and the "
        "compiler decides and emits exactly Hermiticity"
    ),
    carried_by="certiqs_key.meat_core.declaration.validation._validate_constraints",
)

#: Group A, row 7.
SECTOR_CRITERION = Threshold(
    key="sector_criterion",
    group=ThresholdGroup.A,
    kind=ThresholdKind.EXACT,
    value=0.0,
    decides=(
        "The six conditions (W1)-(W6) of def:classes that set `removable`, on "
        "the exhibited removal witness, plus the composition hypothesis of "
        "prop:removal-compose on the set a run actually deletes. A TOLERANCE "
        "MAY ONLY REFUSE A REMOVAL, NEVER LICENSE ONE"
    ),
    carried_by="certiqs_key.meat_core.declaration.sectors",
)

#: Group B, row 1 of 10. AT EXACTLY 0, and Group B rather than Group A BECAUSE
#: iota IS COMPUTED HERE, not declared; a Group A row at a declared tolerance
#: would be a category error as well as a window.
CHOI_ISOMETRY = Threshold(
    key="choi_isometry",
    group=ThresholdGroup.B,
    kind=ThresholdKind.EXACT,
    value=0.0,
    decides=(
        "iota^dagger iota - 1_{A_0} and iota iota^dagger tau_A - tau_A of "
        "eq:iota, ON THE ISOMETRY THIS MODULE CONSTRUCTED. Both constructions "
        "of lem:choi-marginal meet it by {0, 1} arithmetic; anything else is "
        "refused with choi_isometry_inexact"
    ),
    carried_by="certiqs_key.meat_core.objective.choi",
)

#: Group B, row 2. THE DISCHARGE OF HYPOTHESIS (H-SUPP), BOTH SIDES OF IT.
SUPPORT_CUTOFF = Threshold(
    key="support_cutoff",
    group=ThresholdGroup.B,
    kind=ThresholdKind.RELATIVE,
    value=1e-12,
    decides=(
        "Whether a branch operator X_{chat,s} at an iterate attains MAXIMAL "
        "SUPPORT, i.e. whether rank X_{chat,s} = dim W_{chat,s}; the numerical "
        "rank is the number of eigenvalues above the window. BOTH SIDES ARE "
        "READ WITH THIS ONE ROW: dim W_{chat,s} is rank K_{chat,s} of "
        "eq:Kstack at sqrt(support_cutoff) relative to its largest singular "
        "value, which is this row read on X(1) = K K^dagger -- a direction "
        "enters X with weight sigma^2, so a sigma window at this value would "
        "count directions X sees only at an ill-conditioned input "
        "(rem:fo-one-ruler)"
    ),
    relative_to=(
        "that block's own SPECTRAL RADIUS; on the reference side, the largest "
        "singular value of the Kraus stack, at the square root. The relative "
        "reading is right rather than convenient: Eq. eq:Wcs-bound's condition "
        "is a RANK condition, invariant under scaling the block, and grad T is "
        "positively homogeneous of degree zero, so a uniformly small block is "
        "not a degenerate one"
    ),
    # THE CARRIER IS `support_rank`, the symbol the row points at on both
    # sides (the carrying table checks that it exists).
    #
    # AND IT IS THE LEFT SIDE OF Eq. eq:hsupp-check, read by
    # `gradient.attains_the_reference_rank` against the reference
    # `support.branch_support` computes, at sqrt(support_cutoff) (no
    # `branch_support_dim` row reads it at 1e-12 on sigma; :data:`RETIRED`).
    # (H-SUPP) is not decided by the sufficient condition J_s > 0 alone: the
    # row describes a comparison that is performed. `support_rank` is the
    # carrier because it IS the count the row defines -- the eigenvalues above
    # the cutoff, relative to the block's own spectral radius -- and the
    # equality is one line on top of it.
    carried_by="certiqs_key.meat_core.objective.linalg.support_rank",
)

#: Group B, row 3.
DEGENERACY_WINDOW = Threshold(
    key="degeneracy_window",
    group=ThresholdGroup.B,
    kind=ThresholdKind.RELATIVE,
    value=1e-10,
    decides=(
        "Which eigenvalue pairs of an iterate's branch operator take the "
        "derivative value rather than the difference quotient in the kernel of "
        "Eq. eq:dk"
    ),
    relative_to="the scale of the eigenvalue pair",
    carried_by="certiqs_key.meat_core.objective.linalg.divided_difference",
)

#: Group B, row 4.
INTERNAL_HERMITICITY = Threshold(
    key="internal_hermiticity",
    group=ThresholdGroup.B,
    kind=ThresholdKind.RELATIVE,
    value=1e-10,
    decides=(
        "Hermiticity of an operator THIS MODULE FORMED -- a branch operator, a "
        "pinched power -- before a spectral decomposition is taken of it. What "
        "the run then consumes is the HERMITIAN PART, which is Hermitian by "
        "construction, the window bounding the discarded anti-Hermitian half; "
        "ABOVE THE WINDOW THE OPERATOR IS REFUSED, no spectral decomposition "
        "being taken of it"
    ),
    relative_to="the operator's own scale",
    # THE CARRIER IS `check_internal_hermiticity`, the row executed where its
    # own words put it: before the spectral decomposition, refusing above the
    # window rather than symmetrizing in silence. (`is_hermitian` is not the
    # carrier: its callers are the two DECLARED constraint-operator checks,
    # which are decided exactly.)
    carried_by="certiqs_key.meat_core.objective.linalg.check_internal_hermiticity",
)

#: Group B, row 5. AT EXACTLY 0, AND THE RELAXED FAMILY DOES NOT RELAX IT.
ITERATE_POSITIVITY = Threshold(
    key="iterate_positivity",
    group=ThresholdGroup.B,
    kind=ThresholdKind.SPECTRAL_FLOOR,
    value=0.0,
    decides=(
        "Per-block MINIMUM EIGENVALUE of the point consumed at an iterate -- "
        "the Choi blocks J_{t,s} in trusted-source mode, the blocks omega_{t,s} "
        "in untrusted-source mode. AT NO WINDOW: 'the relaxed family of Remark "
        "rem:feas-tol DOES NOT RELAX POSITIVITY', so a point admitted at a "
        "positive window would lie in NO Feas^J(epsilon) and O^J_alpha would "
        "not be defined at it"
    ),
    carried_by=(
        "certiqs_key.solvers.frank_wolfe.joint_driver.run_joint_frank_wolfe -- "
        "AT EXACTLY 0, so "
        "NO CONSTANT CARRIES IT and none may: a number here would be the window "
        "the contract refuses"
    ),
)

#: Group B, row 6. One half of ``iterate_positivity`` taken apart: "THE TWO NEED
#: OPPOSITE WINDOWS AND CANNOT SHARE ONE."
ITERATE_REPAIR_WINDOW = Threshold(
    key="iterate_repair_window",
    group=ThresholdGroup.B,
    kind=ThresholdKind.SPECTRAL_FLOOR,
    value=1e-7,
    decides=(
        "How negative the spectrum of a block of a FORMED ITERATE may be before "
        "the iterate is rejected outright; below it the block is PROJECTED onto "
        "the positive semidefinite cone, the repair RECORDED, and the two "
        "residual rows RE-MEASURED on the repaired point. UNLIKE "
        "oracle_repair_window, which repairs a return only the search reads, it "
        "is what makes the point Theorem thm:firstorder is applied at per-block "
        "positive semidefinite BY CONSTRUCTION"
    ),
    carried_by="certiqs_key.solvers.frank_wolfe.driver.FrankWolfeOptions.iterate_repair_window",
)

#: Group B, row 7. The other half of ``iterate_positivity`` taken apart.
ITERATE_COUPLING = Threshold(
    key="iterate_coupling",
    group=ThresholdGroup.B,
    kind=ThresholdKind.ENTRYWISE,
    value=1e-7,
    decides=(
        "The COUPLING RESIDUAL ||sum_s tr_{Q_s} J_s - 1_{A_0}||_max on the "
        "point consumed at an iterate; in untrusted-source mode the scalar "
        "|sum_s tr omega_s - 1|, which is that residual at d_{A_0} = 1. The "
        "residual it decides is DRIFT OVER THE CONVEX COMBINATIONS THAT BUILT "
        "THE ITERATE and is measured orders above any declaration defect; "
        "PUTTING IT UNDER tau_num WOULD REFUSE EVERY RUN"
    ),
    carried_by="certiqs_key.solvers.frank_wolfe.driver.FrankWolfeOptions.iterate_coupling",
)

#: Group B, row 8. REQUIRED ON EVERY RUN: a requirement, not a diagnostic.
CONSTRAINT_ROWS = Threshold(
    key="constraint_rows",
    group=ThresholdGroup.B,
    kind=ThresholdKind.SPECTRAL_FLOOR,
    value=1e-7,
    decides=(
        "The declared constraint rows of Eq. eq:choi-feas, RELAXED as Remark "
        "rem:feas-tol defines them -- a SPECTRAL floor for an operator "
        "inequality, an ENTRYWISE ball for an equality -- on the point consumed "
        "at an iterate. With iterate_coupling it FIXES THE epsilon of Remark "
        "rem:feas-tol. Its window rests on the argument of rem:fo-iterate-checks "
        "RATHER THAN ON A MEASUREMENT: it is one of the three rows "
        "named as HAVING NEVER FIRED"
    ),
    carried_by="certiqs_key.solvers.frank_wolfe.driver.FrankWolfeOptions.constraint_rows",
)

#: Group B, row 9. THE QICS ADAPTER'S POSITIVITY CLIP, which
#: spec/architecture.md 2.8 names by name: "a backend artefact on the
#: oracle RETURN -- a computed object, not declared data -- SO IT IS NOT UNDER
#: tau_num".
ORACLE_REPAIR_WINDOW = Threshold(
    key="oracle_repair_window",
    group=ThresholdGroup.B,
    kind=ThresholdKind.SPECTRAL_FLOOR,
    value=1e-7,
    decides=(
        "How negative the spectrum of a RETURNED block may be (a SPECTRAL "
        "floor, NEVER an entrywise defect) before the return is rejected "
        "outright; below it the block is projected onto the positive "
        "semidefinite cone and the repair RECORDED. The repaired return serves "
        "the search's step and the diagnostic pairing only, never a bracket "
        "(req:oracle-repair), and the repair is NOT TO BE CONFUSED WITH "
        "iterate_repair_window, which repairs a different object for a "
        "different reason"
    ),
    carried_by="certiqs_key.solvers.oracles.qics.adapter",
)

#: Group B, row 10. OUTSIDE ``tau_num``'s SCOPE ENTIRELY, and it decides no
#: operator predicate: "A RUN THAT STOPS AT ITS ITERATION LIMIT REPORTS EXACTLY
#: WHAT A CONVERGED RUN REPORTS."
OPTIMIZER_GAP = Threshold(
    key="optimizer_gap",
    group=ThresholdGroup.B,
    kind=ThresholdKind.NOT_A_PREDICATE,
    value=1e-10,
    decides="The solver's stopping rule and its converged / iteration-limit status",
    carried_by="certiqs_key.solvers.frank_wolfe.driver.FrankWolfeOptions.gap_tolerance",
)

#: Group B, row 11, AND THE ONE ROW OF THIS TABLE THE CONTRACT LISTS IN GROUP
#: C. `declared_thresholds` retires ``limit_membership`` CONDITIONALLY,
#: and this
#: implementation is on the side of the condition that keeps it: "IT GOES WITH
#: THE CODE IT GUARDS: an implementation that does not run the oracle carries
#: neither, and ONE THAT DOES DECLARES IT AS A GROUP B NUMBER, the object it
#: decides being one the module computed."
#:
#: THIS IMPLEMENTATION RUNS THE ORACLE. ``certiqs_key.meat_core.objective.limit`` is
#: the alpha -> 1+ validation oracle of Remark ``rem:oracle``, it is in
#: ``src/``, and its ``ACCEPTANCE_TOLERANCE`` decides the (H2) membership test
#: on ``Phi[omega]`` -- an object THIS MODULE COMPUTED, which is the Group B
#: criterion word for word. So the row is declared here and ``carrying_table``
#: covers it.
#:
#: THE ALTERNATIVE THE CONTRACT OFFERS IS TO MOVE THE ORACLE OUT OF ``src/``,
#: which would delete C16's live coverage; declaring the row is the reading
#: that keeps the code and states its number, and it is the disposition's own
#: second branch rather than a third option.
#:
#: THE VALUE IS THE ENGINE'S WORKING ONE, as every other Group B number here
#: is.
LIMIT_MEMBERSHIP = Threshold(
    key="limit_membership",
    group=ThresholdGroup.B,
    kind=ThresholdKind.ENTRYWISE,
    value=1e-9,
    decides=(
        "Hypothesis (H2) of Theorem thm:oracle: whether Phi[omega] COMPUTED AT "
        "THE WITNESS lies in the declared acceptance set. On a `singleton` the "
        "comparison is coordinatewise against the declared vector; on a "
        "`polytope` it is non-negativity, the normalization and each declared "
        "row of B q <= b. C16 is a VALIDATION statement and NO KEY-LENGTH "
        "CLAIM PASSES THROUGH IT, so this number is reached only on a run that "
        "invokes the oracle"
    ),
    carried_by="certiqs_key.meat_core.objective.limit.ACCEPTANCE_TOLERANCE",
)

#: The SIX Group A rows, in the contract's own order.
GROUP_A: tuple[Threshold, ...] = (
    BOB_POVM_ADMISSION,
    BOB_POVM_SUMMATION_EXACT,
    ALICE_POVM_EXACT,
    ALICE_MARGINAL_EXACT,
    CONSTRAINT_OPERATOR_EXACT,
    ACCEPTANCE_DATA_EXACT,
    SECTOR_CRITERION,
)

#: The ELEVEN Group B rows: the TEN `declared_thresholds` lists in
#: Group B, in the
#: contract's own order, and ``limit_membership`` LAST -- the Group C row whose
#: disposition says an implementation that runs the oracle "declares it as a
#: Group B number", which this one does. See :data:`LIMIT_MEMBERSHIP`.
GROUP_B: tuple[Threshold, ...] = (
    CHOI_ISOMETRY,
    SUPPORT_CUTOFF,
    DEGENERACY_WINDOW,
    INTERNAL_HERMITICITY,
    ITERATE_POSITIVITY,
    ITERATE_REPAIR_WINDOW,
    ITERATE_COUPLING,
    CONSTRAINT_ROWS,
    ORACLE_REPAIR_WINDOW,
    OPTIMIZER_GAP,
    LIMIT_MEMBERSHIP,
)

#: The rows THE INTERFACE lists as live: seven in Group A, ten in Group B.
#: Kept as its own name so that the CONTRACT's inventory stays readable beside
#: this implementation's, which differs from it by exactly one row and in a
#: direction the interface's own Group C disposition directs.
CONTRACT_LIVE: tuple[Threshold, ...] = GROUP_A + GROUP_B[:-1]

#: The rows THIS IMPLEMENTATION declares and carries: the interface's plus
#: ``limit_membership``, which the interface retires only for an
#: implementation that does not run the alpha -> 1+ oracle. This one does.
LIVE: tuple[Threshold, ...] = GROUP_A + GROUP_B

#: THE ROWS THAT ARE NOT CARRIED, each with the statement that covers it. They
#: are NAMED and not merely absent, because the interface disposes of each on a
#: STATED GROUND and a reader of this table should find the ground here rather
#: than reconstruct it from an omission.
#:
#: ``limit_membership`` IS NOT AMONG THEM AND IS NOT MISSING.
#: It is not carried CONDITIONALLY -- "an
#: implementation that does not run the oracle carries neither, and one that
#: does declares it AS A GROUP B NUMBER" -- and this implementation runs the
#: oracle, so for it the row is LIVE. It is declared at
#: :data:`LIMIT_MEMBERSHIP` and its Group C disposition is kept verbatim at
#: :data:`RETIRED_UNLESS_CARRIED` so that a reader comparing this table with
#: the contract's finds the ground here rather than an unexplained difference.
#:
#: THE THREE AFTER IT ARE OF THREE DIFFERENT KINDS: one decides nothing any run
#: exercised and has no claims to guard; two name predicates that are
#: DECIDED on every run -- "only not against a number, so there is no
#: threshold left to size". THE LAST, ``branch_support_dim``, is a DERIVED
#: number: its predicate is decided on every run, at the square root of
#: ``support_cutoff``.
RETIRED: Mapping[str, str] = {
    "the tolerance window on bob_povm_admission": (
        "NOT CARRIED. A window would decide the Hermiticity defect, the "
        "negative part and the completeness defect each at most a declared "
        "tolerance, with a nonzero defect admitted for exploration and "
        "carrying no key-length claim. There is no tolerance input, the "
        "predicate is decided at exactly zero, and no defect-named refusal "
        "exists. The bob_povm_admission row above carries the predicate; the "
        "reason a tolerance could never have licensed a key-length claim is "
        "prop:optol-nobound"
    ),
    "certificate_series": (
        "The series-truncation target of a numerical lower-bound certificate. "
        "NO CLAIM GUARDS IT: no "
        "statement of this contract mentions a series truncation and there is "
        "nothing left for it to guard. The rung it served is not built in this "
        "repository (PRINCIPLES.md section 10)"
    ),
    "homogeneity": (
        "The test Theta_k = c_k tau_A on a declared operator right-hand side. "
        "NOT CARRIED BECAUSE THE PREDICATE IS NOT NUMERICAL: a licensed entry "
        "declares its scalar c_k and the right-hand side c_k tau_A is "
        "CONSTRUCTED from it, so licensing is a TYPE check on the declared "
        "form (def:homog; rem:cgate). Nothing is compared, so NO WINDOW IS "
        "DECLARED"
    ),
    "branch_support_dim": (
        "The window at which dim W_{chat,s} -- the rank of the Kraus stack of "
        "eq:Kstack, the reference of eq:hsupp-check -- would be read at 1e-12 "
        "on the stack's singular values relative to the largest. NOT CARRIED "
        "BECAUSE IT WOULD MEASURE IN THE WRONG UNITS: a direction enters "
        "X_{chat,s} with weight sigma^2, so one with sigma between 1e-12 and "
        "1e-6 relative would be counted in dim W and counted in rank X only at "
        "an input with "
        "cond(J) > support_cutoff / sigma_rel^2, so the comparison would "
        "withdraw h_lb at every iterate. The predicate is decided on every "
        "run; the window is DERIVED from support_cutoff, sqrt(support_cutoff) "
        "on sigma, which is support_cutoff read on X(1) = K K^dagger "
        "(rem:fo-one-ruler). Carried by "
        "certiqs_key.meat_core.objective.support.branch_support"
    ),
    "marginal_support_floor": (
        "Which eigenvalues of the declared tau_A span supp(tau_A), and hence "
        "rank tau_A. NOT CARRIED BECAUSE NO RUN NEEDS THE RANK: eq:iota asks the "
        "Choi input register only to CONTAIN the support, the identity "
        "W_tau W_tau^dagger = tau_A then holds for every admissible frame, and "
        "thm:choi maps Feas^J onto Feas in each -- so the value is the same "
        "and the truncation the row would decide HAS NO SITE. The full frame "
        "iota = 1_A is always available and is exact"
    ),
}


#: THE GROUP C ROW THIS IMPLEMENTATION DOES NOT INHERIT, kept verbatim beside
#: :data:`RETIRED` because the interface disposes of it on a STATED GROUND and
#: the ground is what decides which side of it a given implementation is on.
RETIRED_UNLESS_CARRIED: Mapping[str, str] = {
    "limit_membership": (
        "The membership test of the alpha -> 1 validation oracle (thm:oracle; "
        "rem:oracle). The oracle is a VALIDATION statement and no key-length "
        "claim passes through it, so this number is reached only on a run that "
        "invokes it. IT GOES WITH THE CODE IT GUARDS: an implementation that "
        "does not run the oracle carries neither, and ONE THAT DOES DECLARES "
        "IT AS A GROUP B NUMBER, the object it decides being one the module "
        "computed. THIS IMPLEMENTATION RUNS THE ORACLE, in "
        "certiqs_key.meat_core.objective.limit, so it is on the second side of "
        "that condition: the row is LIVE here, declared at LIMIT_MEMBERSHIP as "
        "a Group B number, carried by that module's ACCEPTANCE_TOLERANCE, and "
        "reported with every other Group B row"
    ),
}


def declared(row: Threshold) -> float:
    """Return a row's declared number, refusing a row that has none.

    EVERY ROW OF THIS TABLE CARRIES A NUMBER, and the refusal is kept as
    the type's own guard rather than removed: ``value`` is optional on the
    dataclass, and a row added later without one should be caught here rather
    than return ``None`` into a comparison.
    """
    if row.value is None:
        raise ValueError(
            f"the {row.key!r} threshold row declares no number. Every row of "
            "this table declares one: Group A at exactly zero, Group B at the "
            "value this implementation runs at. A row without one cannot be "
            "compared against and must not be read as a stand-in"
        )
    return row.value


def carrying_table() -> Mapping[str, str]:
    """Return the row-to-carrier map, and refuse a row carried twice.

    The interface's one-to-one rule, executed rather than described: EVERY ROW
    MUST BE CARRIED BY EXACTLY ONE, AND NO ROW MAY BE CARRIED BY TWO.

    Raises:
        ValueError: if two rows name the same carrier, which is the failure the
            rule exists to prevent -- one constant deciding two predicates, as
            one ``iterate_positivity`` would for a spectral floor and an
            entrywise residual.
    """
    table: dict[str, str] = {}
    seen: dict[str, str] = {}
    for row in LIVE:
        if row.carried_by in seen:
            raise ValueError(
                f"the declared_thresholds carrying rule: rows "
                f"{seen[row.carried_by]!r} and {row.key!r} are both carried by "
                f"{row.carried_by!r}. NO ROW MAY BE CARRIED BY TWO, and no "
                "carrier may decide two rows: one iterate_positivity deciding "
                "a spectral floor and an entrywise residual at one value "
                "would be that failure, because the two need opposite windows "
                "and cannot share one"
            )
        seen[row.carried_by] = row.key
        table[row.key] = row.carried_by
    return table
