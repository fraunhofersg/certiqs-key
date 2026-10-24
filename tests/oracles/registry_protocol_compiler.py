"""The ``protocol-compiler`` oracle registry -- hand-derived golden values.

The implementation band runs under the freeze rule, in two instances. **This
file is run A's output.** Every value below was derived BY HAND from the
accepted ``contract.tex`` 0.1.3 before any implementation existed: when that
derivation was written, ``src/certiqs_key/protocol_compiler/`` -- the package
that implements this module -- did not exist. Run B, a different implementer instance,
wrote the code against these values and may read but not modify them. An
expected value that turns out to be wrong is a FINDING, reported and corrected
deliberately with its derivation, never edited in passing to make a test green.

THE 0.1.4 RE-POINT: THE LOCATORS MOVED AND THE VALUES DID NOT
============================================================
contract.tex is accepted at 0.1.4 (G3), which amends 0.1.3 on
PRESENTATION ALONE -- a Part I / Part II split, the worked instance relocated
verbatim into the annex, one forward citation, a summary figure, the amendment
record Section 1.4, and the SYMBOLS.md re-pin 0.2.1 -> 0.3.0. That section says
it in as many words: "No claim, no symbol and no number changes." SO THIS PASS
UPDATED LOCATORS AND TOUCHED NO VALUE, AND NO VALUE BELOW WAS RE-DERIVED FROM
A DIFFERENT TEXT: they remain the 0.1.3 hand derivations, re-read against 0.1.4.

What moved, recorded so that a reader is not misled by a number:

* SECTION NUMBERS. Labels are stable and numbers are not, so a citation below
  reading "Section 2.3" is the number AS OF 0.1.4. Two of the numbers this file
  used were also wrong at 0.1.3 and are corrected by the same pass: ``sec:inputs``
  renders as Section 2.2 (not 2.1) and ``sec:outputs`` as Section 2.3 (not 2.2)
  at BOTH versions, Section 2.1 being ``sec:target``. The two citations that did
  mean ``sec:target`` are written with their label so they cannot be confused
  with the Inputs table again.
* THE WORKED INSTANCE. Definition ``def:bb84spec``, Theorem ``thm:pc12``, Remark
  ``rem:bb84checks``, Example ``ex:conj`` and Remark ``rem:bb84notclaim`` now
  stand in Part II, Section 7.1 (``sec:instances`` / ``sec:pc12``), instead of at
  the end of the derivations. THEIR LABELS AND EQUATION LABELS DID NOT CHANGE,
  which is why not one citation of them in this file had to move.

THE INSTANCE'S VALUES WERE RE-READ AGAINST THE RELOCATED TEXT rather than
assumed to have travelled. The ``revalidation`` field of ``O-PC-BB84`` and of
``O-PC-CONJUGATION`` records what was re-read and the result.

WHY A SIBLING FILE AND NOT A NEW GROUP IN ``registry.py``
========================================================
``registry.py`` is "the ``meat-core`` oracle registry" and its integrity test
binds every entry's ``claims`` to ``meat-core``'s C1-C20;
``registry_statistics_acceptance.py`` is the same construction for SA1-SA9. The
claims pinned here are PC1-PC12 of a THIRD module at a THIRD contract version,
resolving in ``docs/mathematical-contracts/protocol-compiler/interface.yaml``.
So this is a PURE INSERTION: a new module beside the other two, neither of which
is edited by so much as a byte. ``KINDS`` and ``INADMISSIBLE_SOURCES`` are
IMPORTED from ``registry.py`` rather than restated, so the three registries
cannot drift on what an admissible oracle is.

ONE DELIBERATE DEPARTURE: EXACT GAUSSIAN RATIONALS, NOT FLOATS
==============================================================
``registry.py`` freezes ``float`` values because the quantities it pins are
transcendental; ``registry_statistics_acceptance.py`` freezes ``Fraction``
because its contract's Assumption A-EXACT demands exact rationals. THIS contract
has neither. Four lines of rationale, and they are the whole justification:

1. Every check this contract states is "finitely many arithmetic operations on
   the declared/emitted data" (Theorem ``thm:feasibility`` (ii), Theorem ``thm:validator-soundness``
   (iv), Theorem ``thm:chain-consumption`` (i), Theorem ``thm:certificate-sufficiency`` (i)). EXACTNESS IS THE
   FAITHFUL READING of "finitely many arithmetic operations": a tolerance would
   turn a decidable check into an approximate one and would decide, in this
   file, something the contract leaves to code.
2. The contract fixes NO numeric type, NO tolerance and NO rounding rule
   anywhere, and carries no exactness or interval-arithmetic assumption. So a
   frozen expected value that carried a tolerance would be inventing the one
   thing the contract is silent about. See ``interface.yaml``,
   ``numeric_substrate_note``, whose open implementation choice is
   identified as ``OC-sec-parameters``.
3. Complex numbers are unavoidable here and are the POINT in one place:
   Example ``ex:conj`` exists precisely because the four BB84 signal states are
   real and cannot exercise ``conjugation_basis``. Its Y-basis projectors have
   entries +-i/2. Every scalar is therefore a ``fractions.Fraction`` and every
   MATRIX ENTRY is an exact pair ``(Fraction real, Fraction imaginary)``.
4. Rank-one objects are frozen as PROJECTORS, whose entries are
   Gaussian-rational even where the amplitudes are not -- ``|Phi^+><Phi^+|`` has
   entries in {0, 1/2} while its amplitudes are ``1/sqrt(2)``. Where a VECTOR
   must be named it is frozen as an exact unnormalized GAUSSIAN-INTEGER vector
   together with its squared norm (Group PC-H, ``CANON``).

DYADIC AND NON-DYADIC WEIGHTS, ON PURPOSE. Weights are fixture choices: the
contract requires only that they be positive and sum to one
(Definition ``def:weighted``; Definition ``def:bb84spec``). The main instances
use DYADIC weights, which a binary float represents exactly. ONE case is
deliberately NON-DYADIC -- ``BB84-w3``, with ``p^A = (2/3, 1/3)`` and
``p^B = (4/5, 1/5)`` -- so that run B's exact-to-machine conversion boundary is
forced into the open rather than hidden behind fixtures that happen to convert
without loss. No float appears anywhere in this file.

ADMISSIBILITY (ADR-0003)
========================
No MATLAB, OpenQKDSecurity, CVX, MOSEK or Julia value is admissible and none is
used; the guard is asserted against ``INADMISSIBLE_SOURCES``. Every number below
is an exact closed form or a hand-computed rational. THE ONLY MATHEMATICAL
SOURCE IS ``contract.tex``, and it is pinned twice because a re-point pass has
two honest pins:

  DERIVED FROM  0.1.3, sha256
                73f80a28afeef87a4880bbc102422cec1eaeb7daaa67e4d4e1808f404d0d028a
                -- the accepted text at the time every value below was computed
                by hand, now superseded;
  RE-CHECKED    0.1.4, sha256
  AGAINST       f14a495a8b20e12c19593ad545c8711fca98e47bd923563aa968e88e76c97e2d
                -- the currently accepted text, whose amendment is presentation
                only. See the re-point section above.

WHAT THIS REGISTRY DOES NOT DO
==============================
It does not certify anything. ``protocol-compiler`` 0.1.4 declares NO per-result
assurance label at all -- Section 1.3 says "nothing this module emits is ITSELF
tiered: a declaration is well-formed or it is refused" -- so ``ASSURANCE`` below
is the ORACLE's own evidential status and is ``estimate`` for every entry. The
tier ceiling in STATUS.yaml (``certified``) is an ELIGIBILITY statement about
the mathematics and is not a property any value here has.

It also does not implement the module. No function in this file compiles a
specification, runs a validator check, evaluates a gate, or composes a channel.
Every frozen field is a LITERAL; the only computation is the exact arithmetic
that assembles a literal from integers a reader can check (``gz``,
``real_matrix``), which widens a rational to a Gaussian pair and nothing more.

THE SPELLING TRAP
=================
The contract names EXACTLY TWO refusal-reason strings verbatim, and only those
two are frozen as strings: ``fixed_fraction_requested`` (Theorem ``thm:choice-encoding``
(iv); Section 2.5) and ``no_feasibility_witness`` (Theorem ``thm:feasibility`` (ii);
Remark ``rem:completeness``). EVERYWHERE ELSE what is frozen is the naming
OBLIGATION and the IDENTITY of the named check -- V1-V8, (C1)-(C5), (S1)-(S4),
(X1), (G1)-(G3), (SR1)-(SR3) -- never an invented spelling. Inventing a spelling
in frozen evidence would decide what the contract leaves to code, which is
exactly what run A must not do.

WHAT IS PINNED, BY GROUP
========================
PC-A  PC1  one hand-built specification MINI, emitted slot by slot; the nine
           label-to-index bijections with inverses; the eq:rdef key map; the
           D(i)/(ii)/(iv)/(vi) verdicts with the route each takes
PC-B  PC2, PC3  the joint alphabet as a disjoint union, two-sided weighted
           families, joint distributions at named states, Phi fibre sums, the
           state-independent choice mass, block-diagonality holding and failing,
           the fixed_fraction refusal, and a partial-phi refusal via V1
PC-C  PC4  r and r_h including unrealized pairs; the side-condition violation
           refused by V5; a V8-discriminating case; the rem:vacuous split
PC-D  PC5, thm:validator-soundness (iii)  the default witness in both modes; a supplied witness
           that rescues a list the default fails; the worked counterexample
           field for field; one failure per verification leg; rem:wellposed
PC-E  PC6  an all-pass declaration; one refusal per check V1-V8; the V5 and V8
           reconstructions; the decidability counts at two named instances
PC-F  PC7, PC8  the Band-A chain record field for field; a proper
           coarse-graining with eq:pullback and eq:pullbackstats; the
           wrong-direction refusal; wrong-segment and descriptor failures; (S2)
           and eq:srcmap failures; and (C4)/(S3) frozen as NOT CHECKED
PC-G  PC9  the EXHAUSTIVE case enumeration over seven axes, with its
           consistency rules, proved total and mutually exclusive; both
           rem:degenerate vacuous passes; the rem:dA1 equality;
           prop:conservative pointwise; the rem:notfallback anti-case
PC-H  PC10, PC11  (SR1)/(SR2) passing and failing; the thm:certificate-sufficiency (ii) criterion
           with a non-POVM family; canonical and non-canonical certificates;
           the rem:xreg overwriting refutation; (SR3) as presence only
PC-I  PC12  the BB84 declaration field for field at three weight pairs, with
           cardinalities, certificate, D-verdicts, gates, r, statistics and Phi
PC-J  ex:conj  BOTH branches of the conjugation convention and the two matched-
           basis distributions that differ -- THE PAIR IS THE POINT
PC-K  the interface vocabulary as frozen tuples
PC-L  the assumption ledger and the never-verified set

CHANGE-REQUEST CANDIDATES: see ``CHANGE_REQUEST_CANDIDATES`` at the end of this
module, which names each one and the reading taken.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as F

from registry import INADMISSIBLE_SOURCES, KINDS

__all__ = [
    "ASSURANCE",
    "CERTIFICATE_OPERATOR_CASES",
    "CHAIN_CASES",
    "CHANGE_REQUEST_CANDIDATES",
    "COMPILER_ONLY_KEYS",
    "DECIDABILITY_COUNTS",
    "DECLARATION_SLOT_KEYS",
    "DECLARED_ORDER_CASES",
    "DIMENSION_ONE_EQUALITIES",
    "EMISSION_REPRESENTABILITY_CASES",
    "FEASIBLE_SET_COMPARISONS",
    "FL_NINE_TENTHS",
    "FL_NINE_TENTHS_PLUS_ONE_TENTH",
    "FL_ONE_TENTH",
    "GATE_AXES",
    "GATE_CASES",
    "GATE_CONSISTENCY_RULES",
    "GATE_OUTCOME_CELLS_0_3_0",
    "GATE_VERDICT_VOCABULARY",
    "INADMISSIBLE_SOURCES",
    "INDEXED_ALPHABETS",
    "INDEX_MAP_CASES",
    "INPUT_KEYS",
    "JOINT_DISTRIBUTION_CASES",
    "KEY_MAP_CASES",
    "KINDS",
    "LEDGER_ROWS",
    "LINK_STATUS_VOCABULARY",
    "NEVER_VERIFIED",
    "NOT_MARKED_AT_0_3_0",
    "NOT_OUTPUTS",
    "ORIGINAL_REGISTRY_NAMES",
    "OUTPUT_KEYS",
    "PC_ORACLES",
    "PERP",
    "RECONSTRUCTION_CASES",
    "REFUSAL_REASONS_VERBATIM",
    "REPOINT_AT_RUN_B_0_3_0",
    "RESTORED_AT_0_3_0",
    "RHS_TAG_CASES",
    "SCOPE_SUPERSESSION_LINE_0_3_0",
    "SECTOR_MAP_COMPARISON_CASES",
    "SUMMATION_CASES",
    "SUPERSEDED_BY_SCOPE_0_3_0",
    "VALIDATOR_CASES",
    "WEIGHTED_FAMILY_CASES",
    "WITNESS_CASES",
    "WITNESS_LEG_FAILURES",
    "CertificateOperatorCase",
    "ChainCase",
    "ChainLink",
    "DecidabilityCount",
    "DeclaredOrderCase",
    "DimensionOneEquality",
    "EmissionRepresentabilityCase",
    "FeasibleSetComparison",
    "GateCase",
    "GateConsistencyRule",
    "GateOutcomeCell",
    "Gauss",
    "IndexMapCase",
    "JointDistributionCase",
    "KeyMapCase",
    "LedgerRow",
    "Matrix",
    "PCOracleEntry",
    "ReconstructionCase",
    "RhsTagCase",
    "SectorMapComparisonCase",
    "SummationCase",
    "ValidatorCase",
    "WeightedFamilyCase",
    "WitnessCase",
    "gz",
    "pc_oracle",
    "real_matrix",
]

#: The ORACLE's own evidential tier. ``estimate`` for every entry: the module's
#: contract declares no per-result assurance label of any kind (Section 1.3,
#: "nothing this module emits is itself tiered").
ASSURANCE = "estimate"

#: The exactly two refusal-reason strings contract.tex names VERBATIM. No third
#: string is frozen anywhere in this file; see the module docstring.
REFUSAL_REASONS_VERBATIM: tuple[str, ...] = (
    "fixed_fraction_requested",
    "no_feasibility_witness",
)

#: The three-valued gate_report vocabulary of the Outputs table, Section 2.3.
#: ``passed vacuously`` is REQUIRED where Remark rem:degenerate applies.
GATE_VERDICT_VOCABULARY: tuple[str, ...] = ("passed", "failed", "passed vacuously")


# ===========================================================================
#  Exact Gaussian-rational representation
# ===========================================================================
#
#  A scalar is a Fraction. A matrix entry is the pair (real, imaginary), each a
#  Fraction. ``gz`` and ``real_matrix`` are NOTATION, not computation: they
#  widen a rational to a Gaussian pair and assemble a tuple of tuples. Nothing
#  in this file multiplies, inverts or diagonalizes a matrix.

Gauss = tuple[F, F]
Matrix = tuple[tuple[Gauss, ...], ...]


def gz(re: int | F = 0, im: int | F = 0) -> Gauss:
    """Return one Gaussian-rational scalar as the exact pair (real, imag)."""
    return (F(re), F(im))


def real_matrix(rows: tuple[tuple[int | F, ...], ...]) -> Matrix:
    """Assemble a Gaussian-rational matrix all of whose entries are real."""
    return tuple(tuple(gz(value) for value in row) for row in rows)


#: The declared computational basis of a qubit, and the four BB84 projectors.
#: Every entry is an exact rational; the amplitudes 1/sqrt(2) never appear.
P_Z0: Matrix = real_matrix(((1, 0), (0, 0)))
P_Z1: Matrix = real_matrix(((0, 0), (0, 1)))
P_X0: Matrix = real_matrix(((F(1, 2), F(1, 2)), (F(1, 2), F(1, 2))))
P_X1: Matrix = real_matrix(((F(1, 2), F(-1, 2)), (F(-1, 2), F(1, 2))))
ID_2: Matrix = real_matrix(((1, 0), (0, 1)))

#: The two Y-basis projectors of Eq. eq:ystates. THE ONLY GENUINELY COMPLEX
#: OBJECTS IN THIS FILE, and the reason the representation is Gaussian:
#:   |0^Y> = (|0> + i|1>)/sqrt2  =>  |0^Y><0^Y| = 1/2 [[1, -i], [i, 1]] ,
#:   |1^Y> = (|0> - i|1>)/sqrt2  =>  |1^Y><1^Y| = 1/2 [[1, +i], [-i, 1]] .
P_Y0: Matrix = (
    (gz(F(1, 2)), gz(0, F(-1, 2))),
    (gz(0, F(1, 2)), gz(F(1, 2))),
)
P_Y1: Matrix = (
    (gz(F(1, 2)), gz(0, F(1, 2))),
    (gz(0, F(-1, 2)), gz(F(1, 2))),
)

#: |Phi^+><Phi^+| on two qubits, basis order (00, 01, 10, 11). A PROJECTOR, so
#: its entries are rational although its amplitudes are not.
PHI_PLUS: Matrix = real_matrix(
    (
        (F(1, 2), 0, 0, F(1, 2)),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (F(1, 2), 0, 0, F(1, 2)),
    )
)


@dataclass(frozen=True)
class PCOracleEntry:
    """One frozen expected value with the derivation that produced it.

    The field set mirrors ``registry.OracleEntry`` and its
    ``statistics-acceptance`` sibling; the alpha-dependent fields are dropped,
    no claim of this contract depending on the Renyi order (Section 2.4, which
    says in as many words that alpha is not a parameter of this contract).
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
    #: What was re-read, and with what result, when the contract's text moved
    #: under an entry without changing. EMPTY FOR EVERY ENTRY WHOSE LOCATORS
    #: DID NOT MOVE: only the annexed worked instance did, at 0.1.4.
    revalidation: str = ""


def pc_oracle(oracle_id: str) -> PCOracleEntry:
    """Return the registry entry with the given ``oracle_id``."""
    for entry in PC_ORACLES:
        if entry.oracle_id == oracle_id:
            return entry
    raise KeyError(f"no oracle entry {oracle_id!r}")


# ===========================================================================
#  Group PC-A -- the specification, the compilation map, and typing (PC1)
# ===========================================================================
#
#  ONE hand-built specification, deliberately smaller than and independent of
#  the BB84 instance of Group PC-I, so that the two do not check each other.
#
#  MINI, in the five parts of Definition def:spec:
#    (a) source     -- X = (x0, x1); A a qubit, d_A = 2; M_{x0} = |0><0|,
#                      M_{x1} = |1><1|; UNTRUSTED mode, so no certificate and no
#                      marginal (def:spec (a), last sentence).
#    (b) receiver   -- Q a qubit, one sector s0 with d_{s0} = 2;
#                      F^ph_{v0} = |0><0|, F^ph_{v1} = |1><1|.
#    (c) chain      -- the Band-A chain of Definition def:bandA: L_s = 0, L = 1,
#                      Lambda_1 = id, status `exact', both slots empty.
#    (d) public     -- DEFAULT party partition (pi_A(x,v) = x, pi_B(x,v) = v);
#                      C_A = (alpha0, alpha1) with a_A(x_i) = alpha_i;
#                      C_B = (beta0, beta1) with a_B(v_i) = beta_i;
#                      varsigma(kappa) = pass iff kappa is MATCHED, i.e.
#                      (alpha0,beta0) or (alpha1,beta1); Chat = (g, d) with
#                      phi(kappa) = g on the matched classes and d otherwise;
#                      holder h = A; Z = (0, 1) so d_Z = 2; key rule
#                      r^0_A(x_i, kappa) = i, which lands in Z as
#                      Definition def:spec (d) requires.
#    (e) constraints-- ONE entry, untrusted typing: (|0><0|_Q, >=, 1/4).
#
#  MINI is used again by Group PC-C (the r and r_h tables), Group PC-E (the
#  all-pass declaration and the decidability counts) and Group PC-G.


@dataclass(frozen=True)
class IndexMapCase:
    """One component of the emitted label-to-index map ``idx``.

    Definition ``def:compile``: for each of X, V, S, O_A, O_B, C_A, C_B, Chat
    and Z_perp, a bijection onto an INITIAL SEGMENT of the non-negative
    integers, with the inverse table emitted alongside (Theorem ``thm:typing``).
    """

    alphabet: str
    labels: tuple[str, ...]
    #: (label, index) pairs, in the emitted order.
    forward: tuple[tuple[str, int], ...]
    #: (index, label) pairs -- the emitted inverse table.
    inverse: tuple[tuple[int, str], ...]
    arithmetic: str


INDEX_MAP_CASES: tuple[IndexMapCase, ...] = tuple(
    IndexMapCase(
        alphabet=name,
        labels=labels,
        forward=tuple((label, i) for i, label in enumerate(labels)),
        inverse=tuple((i, label) for i, label in enumerate(labels)),
        arithmetic=note,
    )
    for name, labels, note in (
        (
            "X",
            ("x0", "x1"),
            """\
Alice's outcome alphabet of MINI. Two labels, indices 0 and 1: a bijection onto
the initial segment {0, 1}. THE INDEX IS BINDING AND THE LABEL IS METADATA
(Section 2.3, `label_index_map`), so the emitted alice_povm list is
(M_{x0}, M_{x1}) in exactly this order and a consumer reads position 0 as
M_{x0}. The inverse table is emitted with it, which is what makes the semantic
label of an index recoverable (Theorem thm:typing, last paragraph of its proof).""",
        ),
        (
            "V",
            ("v0", "v1"),
            """\
Bob's outcome alphabet. Two labels, indices 0 and 1. The emitted bob_povm list
is (F_{v0}, F_{v1}) in that order, and `subsystem_order` fixes that operator
pairs are written M_x (x) F_v with the A-factor first, so the joint index is
(idx(x), idx(v)) and never the reverse.""",
        ),
        (
            "S",
            ("s0",),
            """\
The sector index set. ONE label, index 0 -- the singleton of Definition
def:bandA (a), where Pi_{s0} = 1_Q. Section 2.5 (`subsystem_order`) says sector
blocks appear "in the declared total order of S recorded by idx", which at
|S| = 1 is the one-element order. The block conditions of D(iii) are indexed by
ordered pairs s != s', of which there are |S|(|S|-1) = 0 here (Theorem
thm:band-a (i)).""",
        ),
        (
            "O_A",
            ("x0", "x1"),
            """\
Alice's READOUT alphabet. Under the default party partition pi_A(x, v) = x
(Definition def:target, closing sentence), the readout alphabet is X itself and
the readout map is the first projection. IT IS STILL A SEPARATE ALPHABET OF THE
NINE Definition def:compile lists, and is indexed separately: a declaration with
a NON-default partition has O_A different from X, and an implementation that
identified the two would be correct only by accident of the default.""",
        ),
        (
            "O_B",
            ("v0", "v1"),
            """\
Bob's readout alphabet, equal to V under the default partition for the same
reason as O_A, and indexed separately for the same reason.""",
        ),
        (
            "C_A",
            ("alpha0", "alpha1"),
            """\
Alice's announcement alphabet. a_A is declared ON O_A (Definition def:spec (d)),
which is what makes Theorem thm:sifting-and-key (i) -- announcement locality -- true by
typing rather than by check: "the announcement maps are DECLARED ON THE READOUT
ALPHABETS, so no other signature is expressible".""",
        ),
        (
            "C_B",
            ("beta0", "beta1"),
            """\
Bob's announcement alphabet. K = C_A x C_B has 2 x 2 = 4 classes
(Eq. eq:jointann), and both varsigma and phi must be TOTAL on all four
(Definition def:spec (d); Remark rem:phitotal).""",
        ),
        (
            "Chat",
            ("g", "d"),
            """\
The acceptance alphabet. It is EMITTED (Section 2.3, `acceptance_alphabet`) FOR
`statistics-acceptance`, which builds the acceptance set on it; this module
emits no acceptance set. Two values here: g on the matched classes, d on the
mismatched ones.""",
        ),
        (
            "Z_perp",
            ("0", "1", "perp"),
            """\
The raw-key alphabet INCLUDING the sifting-failure value:
Z_perp = Z sqcup {perp} with Z = (0, 1), so d_Z = |Z| = 2 and |Z_perp| = 3.
THE THREE ARE INDEXED TOGETHER, because key_map is a function table into
Z_perp (Section 2.3). Note that perp is NOT the untrusted-mode marginal value:
Section 3 records that nomarg is "deliberately not perp, which is the
sifting-failure key value, and not 0, which is inadmissible".""",
        ),
    )
)


O_PC_TYPING = PCOracleEntry(
    oracle_id="O-PC-TYPING",
    claims=("PC1",),
    kind="toy-instance",
    subject=(
        "Definition def:spec, Definition def:compile and Theorem thm:typing on the "
        "hand-built specification MINI: the emitted declaration slot by slot, "
        "the nine label-to-index bijections with their inverses, the Eq. eq:rdef "
        "key map, and the D(i), D(ii), D(iv), D(vi) verdicts with the route "
        "each one takes."
    ),
    derivation="""\
contract.tex 0.1.4 Definition def:spec, Definition def:compile, Eq. eq:rdef and
Theorem thm:typing. MINI is specified in the header comment of this group.

THE EMITTED DECLARATION, SLOT BY SLOT (Eq. eq:declaration, filled by
Definition def:compile):
  A, d_A          <- S_src : a qubit, d_A = 2.
  tau_A           <- nomarg. UNTRUSTED mode, so def:compile's rule
                    "tau_A from the certificate in trusted mode and
                    tau_A = nomarg otherwise" fills the slot with the machine
                    value null. NO THIRD VALUE IS EMITTED (proof of thm:typing,
                    D(ii)).
  Q, S, (d_s)     <- the last link of R_rec : (Q, {s0}, (2)), d_Q = 2.
  {M_x}           <- S_src : M_{x0} = |0><0|, M_{x1} = |1><1|.
  {F_v}           <- the last link's target POVM : F_{v0} = |0><0|,
                    F_{v1} = |1><1|.
  P, a_A, a_B,
  phi, h          <- VERBATIM from S_pub (def:compile).
  CList           <- the concatenation of S_con's entries with those transported
                    by the links of R_src and then those of R_rec. R_src is
                    empty and the single R_rec link has an empty constraint
                    slot, so CList is S_con's one entry: (|0><0|_Q, >=, 1/4).
  r               <- BUILT by Eq. eq:rdef, never accepted (Remark rem:rbuilt).
  idx             <- the nine bijections of INDEX_MAP_CASES.

THE KEY MAP, Eq. eq:rdef, CELL BY CELL. With a(x, v) = (a_A(x), a_B(v)) under
the default partition:
  (x0, v0) : a = (alpha0, beta0), MATCHED, varsigma = pass
             -> r = r^0_A(x0, ...) = 0
  (x0, v1) : a = (alpha0, beta1), varsigma = fail -> r = perp
  (x1, v0) : a = (alpha1, beta0), varsigma = fail -> r = perp
  (x1, v1) : a = (alpha1, beta1), MATCHED, varsigma = pass
             -> r = r^0_A(x1, ...) = 1
That table is frozen in Group PC-C as KEY-MINI, together with the two DIFFERENT
total extensions r_h admits.

THE FOUR VERDICTS, EACH WITH ITS ROUTE. Theorem thm:typing proves exactly D(i),
D(ii), D(iv) and D(vi) -- the typing conditions -- and no others; D(iii) is
PC2, D(v) and D(viii) are PC4, D(vii) is PC5.
  D(i)  HOLDS, by three separate steps of the thm:typing proof. Each system is
        declared finite-dimensional and each alphabet finite and non-empty
        (Assumption ass:spec); Q is finite-dimensional BECAUSE
        d_Q = sum_s d_s = 2 is a finite sum of finite terms; and r is TOTAL
        because Eq. eq:rdef is a case distinction on the value of the total map
        varsigma o a, both branches of which are defined on all of X x V. The
        cardinalities are |X| = |V| = |O_A| = |O_B| = |C_A| = |C_B| = 2,
        |S| = 1, |Chat| = 2, |Z_perp| = 3, |K| = 4.
  D(ii) HOLDS by the UNTRUSTED route: the slot holds nomarg and no third value
        is emitted. The (SR1) route of the thm:typing proof is NOT taken here and
        is not available -- there is no certificate in untrusted mode
        (def:spec (a)) -- which is why MINI is the right instance for this
        branch and the BB84 instance of Group PC-I is the right one for the
        other.
  D(iv) HOLDS: the range of Eq. eq:rdef is contained in
        ran r^0_A u {perp} which is inside Z sqcup {perp}, BECAUSE r^0_A maps
        into Z by Definition def:spec (d). The frozen range is {0, 1, perp},
        which is all of Z_perp here.
  D(vi) HOLDS by the UNTRUSTED branch: bowtie_1 = ">=" is in {<=, =, >=} and
        Theta_1 = 1/4 is a real number. The proof of thm:typing records that this
        is the clause where the theorem's hypothesis does its work -- nothing in
        Assumption ass:spec stops a link transporting an entry of the wrong
        typing, and check V6 is what rejects one.

idx IS A BIJECTION ON EACH ALPHABET. Each component maps onto an INITIAL SEGMENT
of the non-negative integers, so the indices are 0..N-1 with no gaps, and the
inverse table is emitted with it. WHICH bijection is code's choice and is
recorded as open implementation choice 3 of 8 in interface.yaml; what is frozen
here is that there are NINE of them, over exactly the nine alphabets
Definition def:compile lists, and that each is total, injective, onto an initial
segment, and accompanied by its inverse.
""",
    hypotheses=(
        "Assumption A-SPEC: the specification's declared data are as declared.",
        "Theorem thm:typing additionally hypothesises that the declaration was "
        "EMITTED, i.e. that no check of Definition def:validator refused; MINI "
        "passes all of V1-V8, which Group PC-E freezes as ALLPASS-MINI.",
        "In trusted-source mode thm:typing would also carry (SR1) as a hypothesis. "
        "MINI is UNTRUSTED, so that hypothesis is absent here and the BB84 "
        "instance of Group PC-I is where it is exercised.",
    ),
)


# ===========================================================================
#  Group PC-B -- weights, not fractions; the statistics functional (PC2, PC3)
# ===========================================================================
#
#  WEIGHT is a TWO-SIDED choice instance, deliberately not BB84: Alice declares
#  a choice with DYADIC weights (3/4, 1/4) and Bob one with (1/2, 1/2), and the
#  conditional POVMs are the Z and X projective measurements on each side.
#
#  Definition def:weighted indexes the emitted family by the DISJOINT UNION
#      V := sqcup_{t in T_pub} U_t x {t} ,
#  so the emitted alphabet on each side has |U_{t0}| + |U_{t1}| = 2 + 2 = 4
#  elements, NOT 2. The choice value t is a component of the outcome and is
#  recoverable from the outcome index alone (Theorem thm:choice-encoding (iii)).


@dataclass(frozen=True)
class WeightedFamilyCase:
    """One choice-weighted family, and whether its blocks stay diagonal."""

    case_id: str
    party: str
    #: The public-choice alphabet T_pub, in the declared order.
    choices: tuple[str, ...]
    #: The declared weights q_t, aligned with ``choices``.
    weights: tuple[F, ...]
    #: The emitted joint alphabet, sqcup_t U_t x {t}, in the emitted order.
    joint_alphabet: tuple[str, ...]
    #: The emitted matrices N_{u,t} = q_t N_{u|t}, aligned with the alphabet.
    emitted: tuple[Matrix, ...]
    #: The choice each emitted element belongs to, aligned with the alphabet.
    choice_of: tuple[str, ...]
    #: The sector projectors of Q, or () when the family lives on A.
    sector_projectors: tuple[Matrix, ...]
    block_diagonal: bool
    arithmetic: str


#: Sector projectors for the three-dimensional Q of the block-diagonality pair:
#: S = (s0, s1) with d_{s0} = 2 and d_{s1} = 1.
PI_S0_3: Matrix = real_matrix(((1, 0, 0), (0, 1, 0), (0, 0, 0)))
PI_S1_3: Matrix = real_matrix(((0, 0, 0), (0, 0, 0), (0, 0, 1)))


WEIGHTED_FAMILY_CASES: tuple[WeightedFamilyCase, ...] = (
    WeightedFamilyCase(
        case_id="WEIGHT-alice",
        party="A",
        choices=("t0", "t1"),
        weights=(F(3, 4), F(1, 4)),
        joint_alphabet=("(0,t0)", "(1,t0)", "(0,t1)", "(1,t1)"),
        emitted=(
            real_matrix(((F(3, 4), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(3, 4)))),
            real_matrix(((F(1, 8), F(1, 8)), (F(1, 8), F(1, 8)))),
            real_matrix(((F(1, 8), F(-1, 8)), (F(-1, 8), F(1, 8)))),
        ),
        choice_of=("t0", "t0", "t1", "t1"),
        sector_projectors=(),
        block_diagonal=True,
        arithmetic="""\
ALICE'S SIDE OF WEIGHT. T_pub = (t0, t1) with DYADIC weights q_{t0} = 3/4 and
q_{t1} = 1/4, which are positive and sum to one as Definition def:weighted
requires. The conditional POVMs are the two qubit measurements
  {N_{u|t0}} = (|0><0|, |1><1|) ,   {N_{u|t1}} = (|+><+|, |-><-|) ,
each complete on its own: |0><0| + |1><1| = 1_A and |+><+| + |-><-| = 1_A.
Eq. eq:weighted multiplies the weight IN:
  M_{(0,t0)} = (3/4)|0><0| = [[3/4, 0], [0, 0]] ,
  M_{(1,t0)} = (3/4)|1><1| = [[0, 0], [0, 3/4]] ,
  M_{(0,t1)} = (1/4)|+><+| = [[1/8, 1/8], [1/8, 1/8]] ,
  M_{(1,t1)} = (1/4)|-><-| = [[1/8, -1/8], [-1/8, 1/8]] .
COMPLETENESS, Lemma lem:weighted (i), added entry by entry:
  (0,0): 3/4 + 0 + 1/8 + 1/8 = 1 ;  (1,1): 0 + 3/4 + 1/8 + 1/8 = 1 ;
  (0,1): 0 + 0 + 1/8 - 1/8 = 0 ;    (1,0): 0 + 0 + 1/8 - 1/8 = 0 .
So sum = 1_A exactly, which is the lemma's computation
sum_t q_t sum_u N_{u|t} = sum_t q_t 1_A = 1_A.
POSITIVITY: each element is a non-negative multiple of a rank-one projector.
THE JOINT ALPHABET IS THE DISJOINT UNION and has FOUR elements, not two: the
choice value is a component of the outcome, and t is recoverable from the index
alone (Theorem thm:choice-encoding (iii)). NO FACTOR q_t IS EMITTED ANYWHERE OUTSIDE A POVM
ELEMENT -- that is the whole content of the output_state convention, and the
alternative is refused (Theorem thm:choice-encoding (iv)).""",
    ),
    WeightedFamilyCase(
        case_id="WEIGHT-bob",
        party="B",
        choices=("r0", "r1"),
        weights=(F(1, 2), F(1, 2)),
        joint_alphabet=("(0,r0)", "(1,r0)", "(0,r1)", "(1,r1)"),
        emitted=(
            real_matrix(((F(1, 2), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(1, 2)))),
            real_matrix(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4)))),
            real_matrix(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4)))),
        ),
        choice_of=("r0", "r0", "r1", "r1"),
        sector_projectors=(ID_2,),
        block_diagonal=True,
        arithmetic="""\
BOB'S SIDE OF WEIGHT, on Q a qubit with the SINGLE sector s0, Pi_{s0} = 1_Q.
T_pub = (r0, r1) with weights 1/2 and 1/2; the same two conditional
measurements as Alice's. Eq. eq:weighted gives
  F_{(0,r0)} = (1/2)|0><0| , F_{(1,r0)} = (1/2)|1><1| ,
  F_{(0,r1)} = (1/2)|+><+| = [[1/4, 1/4], [1/4, 1/4]] ,
  F_{(1,r1)} = (1/2)|-><-| = [[1/4, -1/4], [-1/4, 1/4]] .
Entrywise sum: (0,0): 1/2 + 0 + 1/4 + 1/4 = 1 ; (1,1): likewise 1 ;
off-diagonals: 1/4 - 1/4 = 0. So sum = 1_Q.
BLOCK-DIAGONALITY IS VACUOUS at |S| = 1 (Theorem thm:band-a (i)): the conditions of
D(iii) are indexed by ordered pairs s != s', of which there are none. The
NON-vacuous pair is SECTOR-holds / SECTOR-fails below, and Lemma
lem:weighted (ii) is what reduces the check on a weighted family to the check on
the conditional families, IN BOTH DIRECTIONS, because q_t != 0.""",
    ),
    WeightedFamilyCase(
        case_id="SECTOR-holds",
        party="B",
        choices=("r0",),
        weights=(F(1),),
        joint_alphabet=("(0,r0)", "(1,r0)", "(2,r0)"),
        emitted=(
            real_matrix(((F(1, 2), F(1, 2), 0), (F(1, 2), F(1, 2), 0), (0, 0, 0))),
            real_matrix(((F(1, 2), F(-1, 2), 0), (F(-1, 2), F(1, 2), 0), (0, 0, 0))),
            real_matrix(((0, 0, 0), (0, 0, 0), (0, 0, 1))),
        ),
        choice_of=("r0", "r0", "r0"),
        sector_projectors=(PI_S0_3, PI_S1_3),
        block_diagonal=True,
        arithmetic="""\
A GENUINELY TWO-SECTOR RECEIVER: Q = C^3 with S = (s0, s1),
d_{s0} = 2, d_{s1} = 1, Pi_{s0} = diag(1, 1, 0), Pi_{s1} = diag(0, 0, 1), and
d_Q = 2 + 1 = 3 as V1 requires.
The family is |+><+| and |-><-| INSIDE the s0 block, and the s1 projector:
  F_{v0} = [[1/2, 1/2, 0], [1/2, 1/2, 0], [0, 0, 0]] ,
  F_{v1} = [[1/2, -1/2, 0], [-1/2, 1/2, 0], [0, 0, 0]] ,
  F_{v2} = diag(0, 0, 1) .
Sum = diag(1, 1, 1) = 1_Q, entrywise: (0,0): 1/2 + 1/2 = 1; (1,1): 1/2 + 1/2 = 1;
(0,1): 1/2 - 1/2 = 0; (2,2): 1.
BLOCK-DIAGONALITY, checked as V3 states it -- Pi_s F_v Pi_{s'} = 0 for the
finitely many pairs s != s'. There are |S|(|S|-1) = 2 ordered pairs, (s0, s1)
and (s1, s0). Pi_{s0} F_v Pi_{s1} picks out the (row in {0,1}, column 2) block
of F_v, which is zero in all three; Pi_{s1} F_v Pi_{s0} picks out the
(row 2, column in {0,1}) block, also zero. SO ALL SIX CONDITIONS HOLD.
Equivalently F_v = (+)_s F_v^{(s)}, which is the formulation Theorem
thm:measurements-and-statistics (ii) proves equivalent by writing F = sum_{s,s'} Pi_s F Pi_{s'}.""",
    ),
    WeightedFamilyCase(
        case_id="SECTOR-fails",
        party="B",
        choices=("r0",),
        weights=(F(1),),
        joint_alphabet=("(0,r0)", "(1,r0)", "(2,r0)"),
        emitted=(
            real_matrix(((F(1, 2), 0, F(1, 2)), (0, 0, 0), (F(1, 2), 0, F(1, 2)))),
            real_matrix(((F(1, 2), 0, F(-1, 2)), (0, 0, 0), (F(-1, 2), 0, F(1, 2)))),
            real_matrix(((0, 0, 0), (0, 1, 0), (0, 0, 0))),
        ),
        choice_of=("r0", "r0", "r0"),
        sector_projectors=(PI_S0_3, PI_S1_3),
        block_diagonal=False,
        arithmetic="""\
THE SAME SECTOR STRUCTURE, A FAMILY THAT IS STILL A PERFECTLY GOOD POVM, AND
BLOCK-DIAGONALITY FAILS. The first two elements are the rank-one projectors onto
(|0> +- |2>)/sqrt2 -- frozen as PROJECTORS, so their entries are rational:
  F'_{v0} = [[1/2, 0, 1/2], [0, 0, 0], [1/2, 0, 1/2]] ,
  F'_{v1} = [[1/2, 0, -1/2], [0, 0, 0], [-1/2, 0, 1/2]] ,
  F'_{v2} = diag(0, 1, 0) .
POVM: each is positive semidefinite (two are projectors, one is a diagonal 0/1
matrix) and the entrywise sum is (0,0): 1/2 + 1/2 = 1; (2,2): 1/2 + 1/2 = 1;
(1,1): 1; (0,2): 1/2 - 1/2 = 0. So sum = 1_Q. V3's COMPLETENESS half PASSES.
BLOCK-DIAGONALITY FAILS at the very first pair:
  Pi_{s0} F'_{v0} Pi_{s1} has the single non-zero entry (0, 2) = 1/2 != 0 .
So V3 refuses, naming the block condition. THE POINT OF THE PAIR is that
completeness and block-diagonality are INDEPENDENT halves of V3: this family
would pass a checker that tested only sum_v F_v = 1_Q, and it superposes the two
sectors, which is exactly what the declared sector decomposition exists to
forbid. The same matrix used as a constraint operator O^_k fails the
Pi_s O^_k Pi_{s'} = 0 half of V3 for the same reason.""",
    ),
)


@dataclass(frozen=True)
class JointDistributionCase:
    """P_D[omega] and Phi[omega] on the WEIGHT declaration at one named state."""

    case_id: str
    state_name: str
    #: The state omega on A (x) Q, in the basis order (00, 01, 10, 11).
    state: Matrix
    #: Alice's emitted alphabet, in the emitted order.
    alice_alphabet: tuple[str, ...]
    #: Bob's emitted alphabet, in the emitted order.
    bob_alphabet: tuple[str, ...]
    #: P_D[omega](x, v), row x and column v, in those orders.
    joint: tuple[tuple[F, ...], ...]
    #: The acceptance alphabet Chat, in the emitted order.
    acceptance_alphabet: tuple[str, ...]
    #: Phi[omega], aligned with ``acceptance_alphabet``.
    phi_vector: tuple[F, ...]
    #: The (x, v) index pairs in each fibre of phi o a, aligned with Chat.
    phi_fibres: tuple[tuple[tuple[int, int], ...], ...]
    #: (choice label, declared weight, the mass Eq. eq:choicemass computes).
    choice_mass: tuple[tuple[str, F, F], ...]
    arithmetic: str


JOINT_DISTRIBUTION_CASES: tuple[JointDistributionCase, ...] = (
    JointDistributionCase(
        case_id="PDIST-phiplus",
        state_name="omega = |Phi^+><Phi^+| on A Q",
        state=PHI_PLUS,
        alice_alphabet=("(0,t0)", "(1,t0)", "(0,t1)", "(1,t1)"),
        bob_alphabet=("(0,r0)", "(1,r0)", "(0,r1)", "(1,r1)"),
        joint=(
            (F(3, 16), F(0), F(3, 32), F(3, 32)),
            (F(0), F(3, 16), F(3, 32), F(3, 32)),
            (F(1, 32), F(1, 32), F(1, 16), F(0)),
            (F(1, 32), F(1, 32), F(0), F(1, 16)),
        ),
        acceptance_alphabet=("match", "cross"),
        phi_vector=(F(1, 2), F(1, 2)),
        phi_fibres=(
            ((0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 3), (3, 2), (3, 3)),
            ((0, 2), (0, 3), (1, 2), (1, 3), (2, 0), (2, 1), (3, 0), (3, 1)),
        ),
        choice_mass=(
            ("t0", F(3, 4), F(3, 4)),
            ("t1", F(1, 4), F(1, 4)),
            ("r0", F(1, 2), F(1, 2)),
            ("r1", F(1, 2), F(1, 2)),
        ),
        arithmetic="""\
Eq. eq:jointdist, P_D[omega](x, v) = tr[(M_x (x) F_v) omega], on the maximally
entangled state. Every cell uses the identity
tr[(Y (x) Y') |Phi^+><Phi^+|] = (1/2) tr[Y^T Y'] (Eq. eq:transpose-trick,
second identity), and every M_x and F_v here is REAL SYMMETRIC, so Y^T = Y and
the cells reduce to (1/2) tr[M_x F_v]. The pairwise traces of the four qubit
projectors are tr[|0><0| |0><0|] = 1, tr[|0><0| |1><1|] = 0,
tr[|0><0| |+-><+-|] = 1/2, tr[|+><+| |+><+|] = 1, tr[|+><+| |-><-|] = 0.
ROW BY ROW, with the weights carried along:
  x = (0,t0), weight 3/4 :
      v = (0,r0), weight 1/2 : (1/2)(3/4)(1/2)(1)   = 3/16
      v = (1,r0)             : (1/2)(3/4)(1/2)(0)   = 0
      v = (0,r1)             : (1/2)(3/4)(1/2)(1/2) = 3/32
      v = (1,r1)             : 3/32
  x = (1,t0) : 0, 3/16, 3/32, 3/32 by the same four products with |1><1|.
  x = (0,t1), weight 1/4 :
      v = (0,r0)             : (1/2)(1/4)(1/2)(1/2) = 1/32
      v = (1,r0)             : 1/32
      v = (0,r1)             : (1/2)(1/4)(1/2)(1)   = 1/16
      v = (1,r1)             : (1/2)(1/4)(1/2)(0)   = 0
  x = (1,t1) : 1/32, 1/32, 0, 1/16.
TOTAL MASS, Theorem thm:measurements-and-statistics (iv): the row sums are 3/8, 3/8, 1/8, 1/8, adding to
1 exactly. Over the common denominator 32 the whole table is
(6,0,3,3 | 0,6,3,3 | 1,1,2,0 | 1,1,0,2)/32, and 6+3+3 + 6+3+3 + 1+1+2 + 1+1+2
= 32.
Phi, Eq. eq:jointdist second half. Here a_A((u,t)) = t and a_B((y,r)) = r, so
phi o a depends only on the CHOICE PAIR: phi = match on (t0,r0) and (t1,r1),
cross on (t0,r1) and (t1,r0). The fibres are therefore whole 2x2 blocks:
  match : (t0,r0) block 3/16 + 0 + 0 + 3/16 = 3/8 ; (t1,r1) block
          1/16 + 0 + 0 + 1/16 = 1/8 ; total 1/2 .
  cross : (t0,r1) block 4 x 3/32 = 3/8 ; (t1,r0) block 4 x 1/32 = 1/8 ;
          total 1/2 .
Sum 1/2 + 1/2 = 1, as Theorem thm:measurements-and-statistics (iv) requires, and the fibres PARTITION
X x V because phi o a is total -- which is Remark rem:phitotal's point and is
checked by V1, not assumed.
Eq. eq:choicemass, the STATE-INDEPENDENT choice mass: summing the table over
Alice's outcome at fixed t gives 3/8 + 3/8 = 3/4 = q_{t0} and 1/8 + 1/8 = 1/4 =
q_{t1}; summing over Bob's at fixed r gives (6+0+1+1)/32 + (0+6+1+1)/32 = 1/2 =
q_{r0} and (3+3+2+0)/32 + (3+3+0+2)/32 = 1/2 = q_{r1}. COMPARE THE SAME FOUR
NUMBERS IN PDIST-product BELOW, WHERE THE JOINT TABLE IS COMPLETELY DIFFERENT.""",
    ),
    JointDistributionCase(
        case_id="PDIST-product",
        state_name="omega = |0><0|_A (x) |0><0|_Q",
        state=real_matrix(((1, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
        alice_alphabet=("(0,t0)", "(1,t0)", "(0,t1)", "(1,t1)"),
        bob_alphabet=("(0,r0)", "(1,r0)", "(0,r1)", "(1,r1)"),
        joint=(
            (F(3, 8), F(0), F(3, 16), F(3, 16)),
            (F(0), F(0), F(0), F(0)),
            (F(1, 16), F(0), F(1, 32), F(1, 32)),
            (F(1, 16), F(0), F(1, 32), F(1, 32)),
        ),
        acceptance_alphabet=("match", "cross"),
        phi_vector=(F(1, 2), F(1, 2)),
        phi_fibres=(
            ((0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 3), (3, 2), (3, 3)),
            ((0, 2), (0, 3), (1, 2), (1, 3), (2, 0), (2, 1), (3, 0), (3, 1)),
        ),
        choice_mass=(
            ("t0", F(3, 4), F(3, 4)),
            ("t1", F(1, 4), F(1, 4)),
            ("r0", F(1, 2), F(1, 2)),
            ("r1", F(1, 2), F(1, 2)),
        ),
        arithmetic="""\
THE SECOND STATE, chosen to be as unlike |Phi^+><Phi^+| as a product state can
be. Here omega = |0><0| (x) |0><0| is a product, so
P_D[omega](x, v) = tr[M_x |0><0|] . tr[F_v |0><0|] and the table is an outer
product of two marginals:
  Alice : tr[M_{(0,t0)}|0><0|] = 3/4 , tr[M_{(1,t0)}|0><0|] = 0 ,
          tr[M_{(0,t1)}|0><0|] = (1/4)(1/2) = 1/8 , likewise (1,t1) = 1/8 ;
          sum 3/4 + 0 + 1/8 + 1/8 = 1 .
  Bob   : 1/2 , 0 , 1/4 , 1/4 ; sum 1 .
Outer product, row by row:
  (0,t0) : 3/4 x (1/2, 0, 1/4, 1/4) = (3/8, 0, 3/16, 3/16)
  (1,t0) : 0   x (...)              = (0, 0, 0, 0)
  (0,t1) : 1/8 x (1/2, 0, 1/4, 1/4) = (1/16, 0, 1/32, 1/32)
  (1,t1) : same as (0,t1) .
TOTAL MASS 3/4 . 1 = 1, again exactly.
Phi: match = (t0,r0) block 3/8 + (t1,r1) block (1/32 + 1/32 + 1/32 + 1/32) = 1/8
     -> 1/2 ; cross = (t0,r1) block (3/16 + 3/16) = 3/8 plus (t1,r0) block
     (1/16 + 0 + 1/16 + 0) = 1/8 -> 1/2 . Sum 1.
WHAT THE PAIR OF CASES DEMONSTRATES, AND IT IS THE WHOLE POINT OF PC3 (ii). The
joint tables differ in almost every cell -- one row of this one is identically
zero -- yet the FOUR CHOICE MASSES ARE THE SAME FOUR NUMBERS, 3/4, 1/4, 1/2,
1/2, and they equal the declared weights. That is Eq. eq:choicemass holding
"independently of omega": the number q_t appears only AFTER summing over u, and
the individual terms tr[N_{u,t} omega] plainly do depend on omega, which is what
Remark rem:exactness says the whole difference between the two models is.
A SECOND OBSERVATION, RECORDED BECAUSE IT IS A LIMIT OF THIS INSTANCE AND NOT A
THEOREM: here phi factors through the choice pair alone, so Phi[omega] is the
PRODUCT of the two choice-weight distributions at EVERY state, and both cases
report (1/2, 1/2). An outcome-sensitive phi -- where Phi genuinely moves with
the state -- is Group PC-I's BB84 instance, whose Phi has a zero error entry at
the noiseless state and would not at a noisy one.""",
    ),
)


O_PC_WEIGHTS = PCOracleEntry(
    oracle_id="O-PC-WEIGHTS",
    claims=("PC2", "PC3"),
    kind="toy-instance",
    subject=(
        "Definition def:weighted, Lemma lem:weighted and Theorem thm:choice-encoding on the "
        "two-sided instance WEIGHT: the joint alphabet as a disjoint union, the "
        "emitted weighted matrices, the joint distribution and Phi fibre sums "
        "at two named states, and Eq. eq:choicemass reproducing the declared "
        "weight at both -- state-independence being the point."
    ),
    derivation="""\
contract.tex 0.1.4 Definition def:weighted (Eq. eq:weighted), Lemma lem:weighted
(i)-(iii) with Eq. eq:choicemass, Theorem thm:measurements-and-statistics (iv), Theorem thm:choice-encoding (i)-(iv),
Remark rem:exactness and Definition def:phi (Eq. eq:jointdist).

THE ALPHABET IS A DISJOINT UNION, NOT A PRODUCT. Definition def:weighted sets
V := sqcup_{t} U_t x {t}. With |U_{t0}| = |U_{t1}| = 2 that is four elements on
each side. The distinction matters when the residual alphabets DIFFER between
choices -- a probe setting with three outcomes beside a basis with two -- where
a product would not even type. WEIGHT keeps them equal so that the arithmetic is
checkable, and the disjoint-union SHAPE is frozen in `joint_alphabet` and
`choice_of` rather than being inferred.

THE THREE PARTS OF LEMMA lem:weighted, each visible in the frozen data.
(i) POVM: every N_{u,t} = q_t N_{u|t} is positive because q_t > 0, and the sum
telescopes, sum_t q_t sum_u N_{u|t} = sum_t q_t 1 = 1. Both sums are written out
entry by entry in WEIGHT-alice and WEIGHT-bob.
(ii) BLOCK-DIAGONALITY BOTH WAYS: Pi_s N_{u,t} Pi_{s'} = q_t Pi_s N_{u|t} Pi_{s'}
vanishes IF AND ONLY IF Pi_s N_{u|t} Pi_{s'} does, because q_t != 0. The
non-vacuous instances are SECTOR-holds and SECTOR-fails, on a Q = C^3 carrying
two sectors of dimensions 2 and 1.
(iii) Eq. eq:choicemass, sum_{u} tr[N_{u,t} omega] = q_t FOR EVERY omega. Frozen
in the `choice_mass` column of both distribution cases, on Alice's side and on
Bob's, at two states between which the joint table changes completely.

THE BIPARTITE FORM AND subsystem_order. Lemma lem:weighted (iii)'s second half
is stated party-neutrally with a complementary system R, and spells out both
placements: for a choice on Bob's side, sum_u tr[(1_A (x) N_{u,t}) omega] = q_t,
and for one on Alice's side, sum_u tr[(N_{u,t} (x) 1_Q) omega] = q_t. THE FACTOR
ORDER IS THE CONVENTION'S -- Section 2.5 (`subsystem_order`) puts A first -- and
the value is insensitive to it because the trace is. Both placements are
exercised: the t-masses are Alice-side, the r-masses Bob-side.

THE EXCLUSIVITY CLAUSE, Theorem thm:choice-encoding (iii)-(iv). No factor q_t is emitted
anywhere outside a POVM element: the frozen `emitted` matrices ALREADY CARRY the
weight, and the `weights` field records the declared q_t only so that
Eq. eq:choicemass can be checked against it. The refused alternative -- the
conditional families together with a separate state-independent fraction applied
outside the operators -- is never emitted, and a specification requesting it is
refused with the reason `fixed_fraction_requested`, frozen verbatim in
REFUSAL_REASONS_VERBATIM and discussed in O-PC-FIXED-FRACTION-REFUSAL.
""",
    hypotheses=(
        "Assumption A-COIN: every declared public choice is drawn from a "
        "private random source with the declared weights, independently of the "
        "quantum systems, of the other party's choice and of the adversary. "
        "Remark rem:exactness: this is where the physical content sits, and no "
        "encoding repairs its violation.",
        "Assumption A-SPEC: the conditional families are POVMs and the weights "
        "are strictly positive and sum to one.",
    ),
)


O_PC_FIXED_FRACTION_REFUSAL = PCOracleEntry(
    oracle_id="O-PC-FIXED-FRACTION-REFUSAL",
    claims=("PC3",),
    kind="fail-closed",
    subject=(
        "Theorem thm:choice-encoding (iv), Requirement req:no-fixed-fraction and "
        "Section 2.5 (`test_statistics_model`): the "
        "fixed_fraction encoding is never emitted, and a specification "
        "requesting it is refused with the VERBATIM reason "
        "`fixed_fraction_requested`. The reason string is frozen; the input key "
        "through which such a request would arrive is NOT, because the contract "
        "does not carry one."
    ),
    derivation="""\
contract.tex 0.1.4 Theorem thm:choice-encoding (iv), Section 2.5 bullet 3, Definition
def:compile and Definition def:weighted.

WHAT IS FROZEN VERBATIM: the single string `fixed_fraction_requested`, which is
one of exactly TWO refusal reasons contract.tex spells out. It appears twice --
in thm:choice-encoding (iv) and in the `test_statistics_model` convention -- with the same
spelling, and REFUSAL_REASONS_VERBATIM carries it unchanged.

WHAT THE REFUSAL SAYS. The alternative encoding is "declaring the conditional
families {N_{u|t}} TOGETHER WITH a separate state-independent fraction q_t TO BE
APPLIED OUTSIDE THE OPERATORS". Theorem thm:choice-encoding (iv) records that this is a RULE
OF THE COMPILATION MAP and not a derived statement, and that no path in the
compiler produces a fixed_fraction artifact.

THE SUBSTANTIVE OBLIGATION IS SATISFIED BY CONSTRUCTION, WHICH IS WHY NO INPUT
KEY IS INVENTED HERE. Definition def:compile fills {M_x} "weighted by Definition
def:weighted where a choice family is presented", so the emitted element is
q_t N_{u|t} and Theorem thm:choice-encoding (iii) proves that no other emitted slot carries
q_t. The WEIGHT case above is that emission written out; the refused alternative
would emit the four CONDITIONAL matrices |0><0|, |1><1|, |+><+|, |-><-| on
Alice's side together with the loose numbers 3/4 and 1/4, and no frozen case in
this file contains that pair, deliberately.

THE THIN SPOT, RECORDED AND NOT FILLED. Section 2.2 types `public_choices` as
the record (T_pub, q, {N_{u|t}}) and carries NO model selector; no other input
row carries one either. So within the input type of Section 2.2 the request has
no field to arrive in. TWO READINGS, BOTH CONFORMING, NEITHER DECIDED HERE:
  (A) the request is INEXPRESSIBLE in the typed input, so the check is
      unreachable and the obligation "a fixed_fraction model is never emitted"
      holds vacuously -- which is exactly what def:compile guarantees anyway;
  (B) the request arrives out of band, as a caller-level test-statistics-model
      selection, and is refused with the verbatim string.
An implementation must NOT invent an input machine key for it: Section 2.2 says
"machine keys are binding for interface.yaml", and adding one would be a
Section 3 scope change, not an implementation decision. The same two readings
are recorded in interface.yaml under conventions.fixed_fraction_arrival_note,
and the item is listed in CHANGE_REQUEST_CANDIDATES below.

THE VERDICT THAT IS NOT IN DOUBT, whichever reading is taken: NO DECLARATION IS
EMITTED ON A REFUSAL (Section 2.3, `refusal`), and no artifact of this module
ever carries a fixed_fraction test-statistics model.
""",
    value="fixed_fraction_requested",
    hypotheses=(
        "The reason string is the contract's own spelling and is not invented "
        "here. Everything else about the refusal path -- the container of the "
        "refusal record, and the key a request would arrive under -- is left "
        "to code or routed as a change request.",
    ),
)


O_PC_PARTIAL_PHI = PCOracleEntry(
    oracle_id="O-PC-PARTIAL-PHI",
    claims=("PC2",),
    kind="fail-closed",
    subject=(
        "Remark rem:phitotal: a specification whose acceptance-statistic map is "
        "not tabulated on all of K is refused by check V1, not completed with a "
        "default value; and the exact mass that would otherwise be lost."
    ),
    derivation="""\
contract.tex 0.1.4 Remark rem:phitotal, Definition def:validator V1, Theorem
thm:measurements-and-statistics (iv) and Definition def:spec (d).

THE INSTANCE. Take the WEIGHT declaration of this group unchanged, and delete
ONE ROW from the phi table: the class (t1, r0) is left untabulated, so phi is
partial on K = C_A x C_B, |K| = 4.

WHAT CHECK CATCHES IT. V1 (finiteness and totality) asks that "every declared
map is tabulated on all of its stated domain". phi's stated domain is K, and one
of its four classes has no entry, so V1 REFUSES. That is a GENUINE D(i)
violation -- D(i) requires all declared maps total -- so the refusal is
informative in the sense of Remark rem:completeness: V1 and D(i) are literal
restatements of one another in both directions (proof of thm:validator-soundness, (i) and (ii)),
so a refusal here names a real defect and never a limitation of the checker.

THE EXACT MASS THAT WOULD BE LOST, WHICH IS WHY THE REMARK CALLS TOTALITY
LOAD-BEARING. The fibres of a partial phi do not partition X x V, so Phi[omega]
is subnormalized. At omega = |Phi^+><Phi^+| the (t1, r0) block carries
1/32 + 1/32 + 1/32 + 1/32 = 1/8, so the surviving entries are
  Phi(match) = 1/2 ,  Phi(cross) = 3/8 ,  total 7/8 ,
a deficit of exactly 1/8 = the mass of the dropped class. At the product state
omega = |0><0| (x) |0><0| the (t1, r0) block is 1/16 + 0 + 1/16 + 0 = 1/8, so
the totals are the same: Phi(match) = 1/2, Phi(cross) = 3/8, sum 7/8.
THAT IS WHAT THE REMARK MEANS BY "a defect that LOOKS LIKE A LOST PROBABILITY
and reads downstream as an acceptance statistic that does not sum to one": the
consuming module builds an acceptance set on Chat and would be handed a
sub-probability vector with no indication that anything was dropped.

WHAT AN IMPLEMENTATION MUST NOT DO. Complete the table with a default value.
Remark rem:phitotal says the specification "is REFUSED rather than completed
with a default value", and Section 2.5 (`fail_closed`) says no default value is
ever substituted for a missing datum. A `disc`-like catch-all class is a
DECLARED phi value when the specification declares it -- Definition
def:bb84spec's phi has exactly such a last case -- and an INVENTED one when the
compiler supplies it.
""",
    value=F(7, 8),
    hypotheses=(
        "The deficit 1/8 is computed on the WEIGHT declaration of this group; "
        "the general statement is that the deficit equals the mass of the "
        "untabulated classes, which depends on the state through P_D.",
    ),
)


# ===========================================================================
#  Group PC-C -- sifting and party computability (PC4)
# ===========================================================================
#
#  Three declarations, and the third is a CANDIDATE that Definition def:compile
#  could not have emitted -- which is the point: Theorem thm:sifting-and-key proves D(v) and
#  D(viii) BY CONSTRUCTION for an emitted declaration, so a V5 or V8 failure can
#  only be exhibited on a candidate whose r was supplied rather than built, or
#  whose key rule violates the side condition of Definition def:spec (d).
#  Definition def:validator is stated on "a candidate declaration", and Theorem
#  thm:validator-soundness applies to candidates, so this is inside the contract's scope and not
#  a stretch of it.

#: perp, the sifting-failure key value, written as a sentinel string so that no
#: integer of Z can ever collide with it in a frozen table.
PERP = "perp"


@dataclass(frozen=True)
class KeyMapCase:
    """One key map r, with the two total r_h extensions the contract admits."""

    case_id: str
    holder: str
    alice_alphabet: tuple[str, ...]
    bob_alphabet: tuple[str, ...]
    announcement_classes: tuple[str, ...]
    #: a(x, v) as (x index, v index) -> class label.
    announcement: tuple[tuple[int, int, str], ...]
    #: varsigma as class label -> "pass" or "fail", TOTAL on K.
    sifting: tuple[tuple[str, str], ...]
    #: r(x, v) as (x index, v index) -> key value or PERP.
    key_map: tuple[tuple[int, int, int | str], ...]
    #: The holder readout alphabet O_h, in the emitted order.
    holder_readouts: tuple[str, ...]
    #: Eq. eq:rhold: (readout, class) -> value. TOTAL, including unrealized.
    r_hold_eq_rhold: tuple[tuple[str, str, int | str], ...]
    #: The proof of thm:validator-soundness's V8 => D(viii) reconstruction, which puts PERP on
    #: unrealized pairs. Also total, and DIFFERENT from the line above.
    r_hold_reconstructed: tuple[tuple[str, str, int | str], ...]
    #: The (readout, class) pairs realized by some (x, v).
    realized_pairs: tuple[tuple[str, str], ...]
    v5_passes: bool
    v8_passes: bool
    joint_pair_reading_passes: bool
    arithmetic: str


KEY_MAP_CASES: tuple[KeyMapCase, ...] = (
    KeyMapCase(
        case_id="KEY-MINI",
        holder="A",
        alice_alphabet=("x0", "x1"),
        bob_alphabet=("v0", "v1"),
        announcement_classes=(
            "(alpha0,beta0)",
            "(alpha0,beta1)",
            "(alpha1,beta0)",
            "(alpha1,beta1)",
        ),
        announcement=(
            (0, 0, "(alpha0,beta0)"),
            (0, 1, "(alpha0,beta1)"),
            (1, 0, "(alpha1,beta0)"),
            (1, 1, "(alpha1,beta1)"),
        ),
        sifting=(
            ("(alpha0,beta0)", "pass"),
            ("(alpha0,beta1)", "fail"),
            ("(alpha1,beta0)", "fail"),
            ("(alpha1,beta1)", "pass"),
        ),
        key_map=(
            (0, 0, 0),
            (0, 1, PERP),
            (1, 0, PERP),
            (1, 1, 1),
        ),
        holder_readouts=("x0", "x1"),
        r_hold_eq_rhold=(
            ("x0", "(alpha0,beta0)", 0),
            ("x0", "(alpha0,beta1)", PERP),
            ("x0", "(alpha1,beta0)", PERP),
            ("x0", "(alpha1,beta1)", 0),
            ("x1", "(alpha0,beta0)", 1),
            ("x1", "(alpha0,beta1)", PERP),
            ("x1", "(alpha1,beta0)", PERP),
            ("x1", "(alpha1,beta1)", 1),
        ),
        r_hold_reconstructed=(
            ("x0", "(alpha0,beta0)", 0),
            ("x0", "(alpha0,beta1)", PERP),
            ("x0", "(alpha1,beta0)", PERP),
            ("x0", "(alpha1,beta1)", PERP),
            ("x1", "(alpha0,beta0)", PERP),
            ("x1", "(alpha0,beta1)", PERP),
            ("x1", "(alpha1,beta0)", PERP),
            ("x1", "(alpha1,beta1)", 1),
        ),
        realized_pairs=(
            ("x0", "(alpha0,beta0)"),
            ("x0", "(alpha0,beta1)"),
            ("x1", "(alpha1,beta0)"),
            ("x1", "(alpha1,beta1)"),
        ),
        v5_passes=True,
        v8_passes=True,
        joint_pair_reading_passes=True,
        arithmetic="""\
THE EMITTED MINI DECLARATION OF GROUP PC-A, read through Theorem thm:sifting-and-key.
r is Eq. eq:rdef evaluated at the four pairs: pass on the two MATCHED classes,
where r = r^0_A(x_i, .) = i, and perp on the two mismatched ones. So
r = (0, perp | perp, 1) reading the rows x0, x1.
D(v) HOLDS BY CONSTRUCTION (thm:sifting-and-key (ii)): if varsigma(a(x,v)) = fail then
eq:rdef gives perp directly, and if it is pass then
r = r^0_A(...) lies in Z, and perp is not in Z because Z_perp = Z sqcup {perp}.
The two implications are the two directions of the equivalence.
V5 PASSES: it quantifies over pairs with EQUAL announcements, and here a is
injective on X x V, so every class is realized by exactly one pair and every
comparison is a pair with itself.
D(viii) HOLDS BY CONSTRUCTION (thm:sifting-and-key (iii)) with r_h of Eq. eq:rhold, and V8
PASSES for the same injectivity reason.

THE TWO TOTAL EXTENSIONS, AND WHY BOTH ARE CORRECT. O_A x K has 2 x 4 = 8 pairs
and only FOUR of them are realized by some (x, v) -- the realized_pairs column.
  Eq. eq:rhold defines r_h(o, kappa) = r^0_A(o, kappa) on the passing classes
  and perp on the failing ones, WITHOUT reference to realizability. On the
  unrealized pair (x0, (alpha1,beta1)) that gives 0, and on (x1, (alpha0,beta0))
  it gives 1.
  The proof of Theorem thm:validator-soundness's V8 => D(viii) direction instead defines
  r_h(o, kappa) := r(x, v) for any realizing pair and perp on pairs that are NOT
  REALIZED. On the same two pairs that gives perp and perp.
THE TWO TABLES DIFFER IN EXACTLY THOSE FOUR CELLS, AND BOTH SATISFY
Eq. eq:partycomp: that equation quantifies over (x, v) only, and the contract
says so in as many words -- "The value chosen on unrealized pairs is immaterial".
FROZEN AS A PAIR because an implementation that emitted one and a test that
expected the other would look like a defect and would not be one; and because a
test asserting a particular value on an unrealized pair would be asserting
something the contract explicitly leaves free.""",
    ),
    KeyMapCase(
        case_id="KEY-SIDECOND",
        holder="A",
        alice_alphabet=("x0", "x1"),
        bob_alphabet=("v0", "v1"),
        announcement_classes=("(alpha,beta0)", "(alpha,beta1)"),
        announcement=(
            (0, 0, "(alpha,beta0)"),
            (1, 0, "(alpha,beta0)"),
            (0, 1, "(alpha,beta1)"),
            (1, 1, "(alpha,beta1)"),
        ),
        sifting=(("(alpha,beta0)", "pass"), ("(alpha,beta1)", "fail")),
        key_map=(
            (0, 0, PERP),
            (1, 0, 1),
            (0, 1, PERP),
            (1, 1, PERP),
        ),
        holder_readouts=("x0", "x1"),
        r_hold_eq_rhold=(
            ("x0", "(alpha,beta0)", PERP),
            ("x0", "(alpha,beta1)", PERP),
            ("x1", "(alpha,beta0)", 1),
            ("x1", "(alpha,beta1)", PERP),
        ),
        r_hold_reconstructed=(
            ("x0", "(alpha,beta0)", PERP),
            ("x0", "(alpha,beta1)", PERP),
            ("x1", "(alpha,beta0)", 1),
            ("x1", "(alpha,beta1)", PERP),
        ),
        realized_pairs=(
            ("x0", "(alpha,beta0)"),
            ("x0", "(alpha,beta1)"),
            ("x1", "(alpha,beta0)"),
            ("x1", "(alpha,beta1)"),
        ),
        v5_passes=False,
        v8_passes=True,
        joint_pair_reading_passes=True,
        arithmetic="""\
THE SIDE CONDITION OF Remark rem:sidecond, VIOLATED, AND THE CHECK THAT CATCHES
IT. Definition def:spec (d) types the key rule as
r^0_h : O_h x K -> Z, INTO Z and not into Z_perp. Here the specification
supplies r^0_A(x0, .) = perp, which is outside Z.
THE ANNOUNCEMENT STRUCTURE IS CHOSEN SO THAT THE VIOLATION IS VISIBLE. Alice
announces a single letter alpha for both outcomes, so C_A = (alpha) and the
class (alpha, beta0) is realized by TWO pairs, (x0, v0) and (x1, v0). That is
what a singleton-fibre instance cannot do, and it is why KEY-MINI -- where a is
injective -- would NOT expose the same violation.
Eq. eq:rdef then gives
  (x0, v0) : class (alpha,beta0), varsigma = PASS, r = r^0_A(x0, .) = perp
  (x1, v0) : class (alpha,beta0), varsigma = PASS, r = r^0_A(x1, .) = 1
  (x0, v1), (x1, v1) : class (alpha,beta1), varsigma = fail, r = perp .
V5 (sifting consistency) REFUSES: for (x, v) = (x0, v0) and
(x', v') = (x1, v0), a(x, v) = a(x', v') = (alpha, beta0), and r(x0, v0) = perp
while r(x1, v0) != perp. The check's biconditional fails.
THE REFUSAL IS INFORMATIVE, i.e. it names a real defect: D(v) genuinely fails.
No varsigma whatsoever witnesses r(x, v) = perp <=> varsigma(a(x, v)) = fail
here, because within the single class (alpha, beta0) one pair sifts out and the
other does not, so the right-hand side has one truth value and the left-hand
side has two. That is the completeness half of Theorem thm:validator-soundness (ii) at V5, whose
proof constructs varsigma from r and a and needs V5 for well-definedness.
WHAT IS LOST WITHOUT THE SIDE CONDITION, in the remark's own words: "a sifting
event becomes INVISIBLE TO THE PUBLIC RECORD". The public announcement says the
round passed; the key holder silently has no key value.
V8 STILL PASSES HERE, which is the reason this case and KEY-V8 are separate: the
two pairs of the offending class have DIFFERENT holder readouts (x0 and x1), so
V8 never compares them. A checker that ran V8 and not V5 would accept this
declaration.""",
    ),
    KeyMapCase(
        case_id="KEY-V8",
        holder="A",
        alice_alphabet=("x0",),
        bob_alphabet=("v0", "v1"),
        announcement_classes=("(alpha,beta)",),
        announcement=((0, 0, "(alpha,beta)"), (0, 1, "(alpha,beta)")),
        sifting=(("(alpha,beta)", "pass"),),
        key_map=((0, 0, 0), (0, 1, 1)),
        holder_readouts=("x0",),
        r_hold_eq_rhold=(),
        r_hold_reconstructed=(),
        realized_pairs=(("x0", "(alpha,beta)"),),
        v5_passes=True,
        v8_passes=False,
        joint_pair_reading_passes=True,
        arithmetic="""\
THE V8-DISCRIMINATING CASE, AND THE rem:vacuous SPLIT.
A CANDIDATE declaration -- Definition def:validator is stated on candidates and
Theorem thm:validator-soundness applies to them -- with a SUPPLIED r rather than one built by
Eq. eq:rdef. It has to be supplied: for an emitted declaration
r(x, v) = r^0_h(pi_h(x, v), a(x, v)) is a function of the holder readout and the
announcements by construction, so V8 cannot fail on one (Theorem thm:sifting-and-key (iii)).
THE SHAPE IS THE d_A = 1 EMBEDDING OF Remark rem:dA1: A is trivial, X = (x0) is
a singleton, and both parties' data sit in Bob's outcome symbol v. The holder is
A, so O_A = (x0) and pi_A(x, v) = x0 for both pairs; a_B is constant, so both
pairs carry the same class (alpha, beta).
  r(x0, v0) = 0 ,  r(x0, v1) = 1 .
V5 PASSES: within the one class, neither value is perp, so the biconditional
"r = perp iff r' = perp" holds (false iff false).
V8 REFUSES: pi_A(x0, v0) = pi_A(x0, v1) = x0 and a(x0, v0) = a(x0, v1), yet
r(x0, v0) = 0 != 1 = r(x0, v1). That is exactly Remark rem:vacuous's criterion,
"two pairs with the same holder readout and the same announcements carry
different key values".
THE rem:vacuous SPLIT, FROZEN AS TWO VERDICTS ON THE SAME DECLARATION.
  READ AGAINST THE JOINT PAIR (x, v): Eq. eq:partycomp is SATISFIED, and
  trivially so -- take r_h := r itself, which is by definition a function of
  (x, v). The remark says this reading "would be satisfied by EVERY r
  whatsoever". `joint_pair_reading_passes` is True.
  READ AGAINST THE READOUT pi_h, which is what D(viii) and V8 actually say: it
  FAILS. `v8_passes` is False.
AND THE REMARK'S POINT IS THAT THE TWO READINGS DIVERGE PRECISELY ON THE SHAPES
THAT NEED THE CONDITION MOST -- "those which place both parties' data in one
outcome symbol, AS THE d_A = 1 EMBEDDING OF Remark rem:dA1 DOES". This case is
that shape. A checker that read eq:partycomp against the pair would accept a
declaration in which the holder cannot compute its own key.
The r_h columns are empty here because no total r_h exists: that is the content
of the refusal, and writing one would contradict it.""",
    ),
)


O_PC_SIFTING = PCOracleEntry(
    oracle_id="O-PC-SIFTING",
    claims=("PC4", "PC6"),
    kind="toy-instance",
    subject=(
        "Theorem thm:sifting-and-key (i)-(iii) with Eq. eq:rdef and Eq. eq:rhold: the key "
        "map and BOTH total r_h extensions including their differing values on "
        "unrealized pairs; the Remark rem:sidecond violation refused by V5; and "
        "a V8-discriminating candidate on which the joint-pair reading of "
        "Eq. eq:partycomp passes and the readout reading fails."
    ),
    derivation="""\
contract.tex 0.1.4 Theorem thm:sifting-and-key, Eq. eq:rdef, Eq. eq:rhold,
Eq. eq:partycomp, Eq. eq:jointann, Remark rem:sidecond, Remark rem:vacuous,
Remark rem:rbuilt and Definition def:validator V5, V8.

ANNOUNCEMENT LOCALITY IS A TYPING FACT, NOT A CHECK. Theorem thm:sifting-and-key (i) holds
because Definition def:spec (d) declares a_A on O_A and a_B on O_B, so "no other
signature is expressible". All three cases carry announcement tables of that
signature and none of them could carry a different one. V8's FIRST clause -- that
a_A and a_B are tabulated on O_A and O_B -- is the check-side of the same fact,
and is the announcement clause of D(viii).

THE THREE CASES AND WHAT EACH ISOLATES.
  KEY-MINI    both checks pass; the two r_h extensions differ on the four
              unrealized pairs of O_A x K and both satisfy Eq. eq:partycomp.
  KEY-SIDECOND  V5 fails, V8 passes. The side condition of Definition
              def:spec (d) is violated and the class (alpha, beta0) is realized
              by two pairs with different holder readouts, so only V5 sees it.
  KEY-V8      V5 passes, V8 fails. One class, one holder readout, two key
              values, so only V8 sees it.
THE PAIR OF LAST TWO IS THE POINT: NEITHER CHECK SUBSUMES THE OTHER, and an
implementation that ran one of them would accept a declaration the contract
refuses. That is a property of the frozen data, not of a proof, and the
integrity test asserts it.

THE DEFAULT-PARTITION SPECIALIZATION, frozen in the tables' shape. Under
pi_A(x, v) = x and pi_B(x, v) = v (Definition def:target, closing sentence),
Theorem thm:sifting-and-key reads a_A : X -> C_A, a_B : V -> C_B and
r(x, v) = r_A(x, a(x, v)) for h = A. All three cases use the default partition,
so O_A = X and O_B = V; the alphabets are nevertheless indexed separately in
Group PC-A because a non-default partition separates them.

WHAT REMARK rem:rbuilt BUYS, and it is the reason PC4 is short. A specification
that SUPPLIED r would have to be checked for D(v) and D(viii) -- two whole-table
checks. Built by Eq. eq:rdef, r satisfies both by construction and the only
residual obligation is the ONE side condition that r^0_h maps into Z, decided by
inspecting one function table. KEY-SIDECOND is that inspection failing, and
KEY-V8 is what the two whole-table checks are for when r is supplied anyway.
""",
    hypotheses=(
        "Assumption A-SPEC, including the clause that r^0_h is valued in Z. "
        "KEY-SIDECOND is a specification that violates that clause, and is "
        "frozen to show which check catches the violation.",
        "KEY-V8 is a CANDIDATE declaration, not one Definition def:compile "
        "emitted: for an emitted declaration Theorem thm:sifting-and-key (iii) proves V8 "
        "cannot fail.",
    ),
)


# ===========================================================================
#  Group PC-D -- the feasible set is non-empty (PC5, thm:validator-soundness (iii))
# ===========================================================================


@dataclass(frozen=True)
class WitnessCase:
    """One feasibility witness, verified condition by condition."""

    case_id: str
    source_mode: str
    alice_dim: int
    q_dim: int
    #: The sector dimensions (d_s), in the declared order of S.
    sector_dims: tuple[int, ...]
    #: tau_A, or None in untrusted-source mode where the slot holds nomarg.
    tau_a: Matrix | None
    #: (operator, relation, right-hand side) with the rhs a scalar in untrusted
    #: mode and a matrix in trusted mode. Empty tuple at m = 0.
    constraints: tuple[tuple[Matrix, str, F | Matrix], ...]
    #: Whether the witness is the DEFAULT of Eq. eq:witness-empty.
    is_default_witness: bool
    #: The witness omega^*, or None when none is supplied.
    witness: Matrix | None
    #: Per verification leg of Theorem thm:feasibility (ii), the verdict.
    leg_positive: bool | None
    leg_trace_one: bool | None
    leg_sector_blocks: bool | None
    leg_marginal: bool | None
    leg_constraints: bool | None
    #: The evaluated left-hand side of each constraint entry, aligned with
    #: ``constraints``; a scalar in untrusted mode.
    constraint_values: tuple[F, ...]
    v7_passes: bool
    #: The verbatim refusal reason where V7 refuses, else None.
    refusal_reason: str | None
    arithmetic: str


WITNESS_CASES: tuple[WitnessCase, ...] = (
    WitnessCase(
        case_id="WIT-default-trusted-maxmixed",
        source_mode="trusted",
        alice_dim=2,
        q_dim=2,
        sector_dims=(2,),
        tau_a=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        constraints=(),
        is_default_witness=True,
        witness=real_matrix(
            (
                (F(1, 4), 0, 0, 0),
                (0, F(1, 4), 0, 0),
                (0, 0, F(1, 4), 0),
                (0, 0, 0, F(1, 4)),
            )
        ),
        leg_positive=True,
        leg_trace_one=True,
        leg_sector_blocks=True,
        leg_marginal=True,
        leg_constraints=True,
        constraint_values=(),
        v7_passes=True,
        refusal_reason=None,
        arithmetic="""\
Eq. eq:witness-empty, TRUSTED branch: omega^* = tau_A (x) 1_Q / d_Q. With
tau_A = 1_A/2 and d_Q = 2 that is 1_{AQ}/4 = diag(1/4, 1/4, 1/4, 1/4) in the
basis order (00, 01, 10, 11) fixed by `subsystem_order` (A first).
THE FOUR CONDITIONS OF Definition def:feasible, one at a time, as the proof of
Theorem thm:feasibility (i) takes them.
  POSITIVE SEMIDEFINITE: a tensor product of two positive semidefinite
  operators; here diagonal with entries 1/4 >= 0.
  TRACE ONE: a product of traces, 1 . 1 = 1; entrywise 4 x 1/4 = 1.
  SECTOR BLOCKS: chi := 1_Q/d_Q satisfies Pi_s chi Pi_{s'} = Pi_s Pi_{s'}/d_Q
  = 0 for s != s' by orthogonality of the sector projectors, hence
  (1_A (x) Pi_s) omega^* (1_A (x) Pi_{s'}) = tau_A (x) Pi_s chi Pi_{s'} = 0. At
  |S| = 1 there is no such pair and the conjunction is empty.
  MARGINAL: omega^*_A = tau_A . tr chi = tau_A . 1 = tau_A, using D(ii) for
  tr tau_A = 1.
  CONSTRAINTS: CList is empty, so the conjunction of Eq. eq:feas-modes is empty
  and holds vacuously. THAT IS WHY PART (i) IS A THEOREM AND NOT A CHECK.
V7 passes by its FIRST branch, "CList = empty".""",
    ),
    WitnessCase(
        case_id="WIT-default-trusted-singular",
        source_mode="trusted",
        alice_dim=2,
        q_dim=2,
        sector_dims=(2,),
        tau_a=P_Z0,
        constraints=(),
        is_default_witness=True,
        witness=real_matrix(
            (
                (F(1, 2), 0, 0, 0),
                (0, F(1, 2), 0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
            )
        ),
        leg_positive=True,
        leg_trace_one=True,
        leg_sector_blocks=True,
        leg_marginal=True,
        leg_constraints=True,
        constraint_values=(),
        v7_passes=True,
        refusal_reason=None,
        arithmetic="""\
THE SAME DEFAULT WITNESS AT A SINGULAR MARGINAL, which the Outputs table admits
in as many words: "A SINGULAR tau_A IS ADMISSIBLE; tau_A = 0 IS NOT".
tau_A = |0><0| has rank one and eigenvalues (1, 0). Eq. eq:witness-empty gives
omega^* = |0><0| (x) 1_Q/2 = diag(1/2, 1/2, 0, 0).
  POSITIVE: eigenvalues (1/2, 1/2, 0, 0), all >= 0. The two zeros are what
  distinguishes a singular marginal from an inadmissible one -- a zero
  EIGENVALUE is fine; a zero MATRIX is not, because tr tau_A = 1 fails.
  TRACE: 1/2 + 1/2 = 1.
  MARGINAL: omega^*_A = |0><0| . tr(1_Q/2) = |0><0| = tau_A, entry by entry.
  SECTORS, CONSTRAINTS: as in the previous case.
WHY IT IS FROZEN. An implementation that tested the marginal by inverting
tau_A, or that treated a rank-deficient marginal as a defect, would refuse a
declaration the contract admits. Note also that the gate (G3)(a) test of
Theorem thm:gates (i) is explicitly written to survive a singular tau_A: "pick any
index pair where tau_A is non-zero, form the candidate ratio, and compare d_A^2
entries; IF tau_A HAS A ZERO ENTRY WHERE Theta_k DOES NOT, THE TEST FAILS".""",
    ),
    WitnessCase(
        case_id="WIT-default-untrusted-twosector",
        source_mode="untrusted",
        alice_dim=2,
        q_dim=3,
        sector_dims=(2, 1),
        tau_a=None,
        constraints=(),
        is_default_witness=True,
        witness=real_matrix(
            (
                (F(1, 6), 0, 0, 0, 0, 0),
                (0, F(1, 6), 0, 0, 0, 0),
                (0, 0, F(1, 6), 0, 0, 0),
                (0, 0, 0, F(1, 6), 0, 0),
                (0, 0, 0, 0, F(1, 6), 0),
                (0, 0, 0, 0, 0, F(1, 6)),
            )
        ),
        leg_positive=True,
        leg_trace_one=True,
        leg_sector_blocks=True,
        leg_marginal=True,
        leg_constraints=True,
        constraint_values=(),
        v7_passes=True,
        refusal_reason=None,
        arithmetic="""\
Eq. eq:witness-empty, UNTRUSTED branch: omega^* = (1_A/d_A) (x) (1_Q/d_Q). At
d_A = 2 and Q = C^3 with S = (s0, s1) and (d_s) = (2, 1) that is
1_{AQ}/6, a 6 x 6 diagonal matrix with entries 1/6.
  d_Q = sum_s d_s = 2 + 1 = 3, which V1 checks.
  POSITIVE: diagonal, entries 1/6 >= 0.  TRACE: 6 x 1/6 = 1.
  SECTOR BLOCKS, THE NON-VACUOUS CHECK HERE: with two sectors there are
  |S|(|S|-1) = 2 ordered pairs. Pi_{s0} chi Pi_{s1} = Pi_{s0} Pi_{s1}/3 = 0 and
  likewise the transpose, so both off-diagonal blocks of omega^* vanish. On the
  6-dimensional space that is the statement that the (rows 0-3, columns 4-5)
  block and its mirror are zero, which a diagonal matrix satisfies.
  MARGINAL: in untrusted-source mode there is NO condition beyond tr omega = 1
  (Definition def:feasible), so this leg is discharged by the trace leg and by
  nothing else. `leg_marginal` is True in the sense "no condition to violate".
  CONSTRAINTS: empty list, vacuous.
THIS IS THE CASE THAT SHOWS THE UNTRUSTED DEFAULT IS NOT tau_A = 1_A/d_A IN
DISGUISE. The witness happens to have maximally mixed A-marginal, but the
declaration imposes NO marginal condition, so states with any A-marginal are
feasible -- see Remark rem:notfallback and the ANTI-FALLBACK case in Group PC-G,
where |0><0|_A (x) 1_Q/2 is feasible untrusted and infeasible at
tau_A = 1_A/2.""",
    ),
    WitnessCase(
        case_id="WIT-default-satisfies-list",
        source_mode="untrusted",
        alice_dim=2,
        q_dim=2,
        sector_dims=(2,),
        tau_a=None,
        constraints=((P_Z0, ">=", F(1, 4)),),
        is_default_witness=True,
        witness=real_matrix(
            (
                (F(1, 4), 0, 0, 0),
                (0, F(1, 4), 0, 0),
                (0, 0, F(1, 4), 0),
                (0, 0, 0, F(1, 4)),
            )
        ),
        leg_positive=True,
        leg_trace_one=True,
        leg_sector_blocks=True,
        leg_marginal=True,
        leg_constraints=True,
        constraint_values=(F(1, 2),),
        v7_passes=True,
        refusal_reason=None,
        arithmetic="""\
m = 1 AND THE DEFAULT CANDIDATE ALREADY SATISFIES THE LIST, so no further witness
is needed -- Theorem thm:feasibility (ii), last sentence: "In particular
Eq. eq:witness-empty is CHECKED FIRST, and a list it satisfies needs no further
witness". THIS IS THE MINI DECLARATION OF GROUP PC-A.
The entry is (|0><0|_Q, >=, 1/4), untrusted typing. Its untrusted left-hand side
is the SCALAR tr[(1_A (x) O^_1) omega], and at omega^* = 1_{AQ}/4 the product
(1_A (x) |0><0|) omega^* is diag(1/4, 0, 1/4, 0) in the basis (00, 01, 10, 11),
whose trace is 1/4 + 1/4 = 1/2.
  1/2 >= 1/4 : the entry HOLDS, with slack 1/4.
Equivalently, and independent of d_A:
tr[(1_A (x) |0><0|)(1_A/d_A (x) 1_Q/2)] = (tr 1_A / d_A) . (1/2) = 1 . 1/2 = 1/2.
V7 passes by its SECOND branch with the DEFAULT witness, so the specification
need supply nothing. That is the m >= 1 case an implementation must not refuse
for want of an input.""",
    ),
    WitnessCase(
        case_id="WIT-supplied-rescues",
        source_mode="untrusted",
        alice_dim=2,
        q_dim=2,
        sector_dims=(2,),
        tau_a=None,
        constraints=((P_Z0, ">=", F(3, 4)),),
        is_default_witness=False,
        witness=real_matrix(
            (
                (F(1, 2), 0, 0, 0),
                (0, 0, 0, 0),
                (0, 0, F(1, 2), 0),
                (0, 0, 0, 0),
            )
        ),
        leg_positive=True,
        leg_trace_one=True,
        leg_sector_blocks=True,
        leg_marginal=True,
        leg_constraints=True,
        constraint_values=(F(1),),
        v7_passes=True,
        refusal_reason=None,
        arithmetic="""\
THE DEFAULT FAILS AND A SUPPLIED WITNESS PASSES -- the second branch of Theorem
thm:feasibility (ii) doing the work it exists for.
The entry is tightened to (|0><0|_Q, >=, 3/4).
  DEFAULT CANDIDATE Eq. eq:witness-empty = 1_{AQ}/4 gives, by the computation of
  the previous case, the value 1/2, and 1/2 >= 3/4 IS FALSE. So the first branch
  of thm:feasibility (ii) does not close the case.
  SUPPLIED WITNESS omega^* = (1_A/2) (x) |0><0| = diag(1/2, 0, 1/2, 0).
    POSITIVE: diagonal with entries 1/2, 0, 1/2, 0, all >= 0.
    TRACE: 1/2 + 1/2 = 1.
    SECTOR BLOCKS: |S| = 1, vacuous.
    MARGINAL: untrusted, no condition.
    CONSTRAINT: (1_A (x) |0><0|) omega^* = omega^* itself, whose trace is 1, and
    1 >= 3/4 HOLDS with slack 1/4.
  So V7 passes by the second branch and D(vii) holds, with the witness lying in
  W by Theorem thm:feasibility (ii)'s verification.
THE CONTRAST WITH THE NEXT CASE IS THE ENTIRE CONTENT OF thm:validator-soundness (iii): tighten
the right-hand side from 3/4 to 1 and the SAME witness still works
(tr = 1 >= 1), but a specification that supplies NO witness is refused even
though the feasible set is non-empty.""",
    ),
    WitnessCase(
        case_id="WIT-pc6iii-counterexample",
        source_mode="untrusted",
        alice_dim=2,
        q_dim=2,
        sector_dims=(2,),
        tau_a=None,
        constraints=((P_Z0, ">=", F(1)),),
        is_default_witness=True,
        witness=real_matrix(
            (
                (F(1, 4), 0, 0, 0),
                (0, F(1, 4), 0, 0),
                (0, 0, F(1, 4), 0),
                (0, 0, 0, F(1, 4)),
            )
        ),
        leg_positive=True,
        leg_trace_one=True,
        leg_sector_blocks=True,
        leg_marginal=True,
        leg_constraints=False,
        constraint_values=(F(1, 2),),
        v7_passes=False,
        refusal_reason="no_feasibility_witness",
        arithmetic="""\
THE WORKED COUNTEREXAMPLE OF THEOREM thm:validator-soundness (iii), FIELD FOR FIELD. The
contract states it as: untrusted-source mode with Q a qubit carrying the single
sector S = (s0), every other slot well-formed, and the one-entry list
CList = ((|0><0|_Q, >=, 1)), whose entry reads
tr[(1_A (x) |0><0|) omega] >= 1.
d_A IS NOT FIXED BY THE CONTRACT HERE and is frozen as 2; the arithmetic below
is independent of it, which is recorded so that no reader takes 2 for a
hypothesis.
D(i)-D(viii) ALL HOLD, condition by condition:
  D(i)   alphabets finite non-empty, maps total -- "every other slot
         well-formed" is the contract's hypothesis;
  D(ii)  the slot holds nomarg;
  D(iii) O^_1 = |0><0| is HERMITIAN, and block-diagonal VACUOUSLY at |S| = 1;
  D(iv)  r is valued in Z sqcup {perp};
  D(v)   announcement-determined sifting, from the well-formed slots;
  D(vi)  untrusted typing: bowtie in {<=, =, >=} and Theta_1 = 1 real;
  D(vii) HOLDS: omega = tau (x) |0><0| is feasible FOR ANY tau in S_=(A) --
         positive, trace 1, block-diagonal vacuously, no marginal condition, and
         tr[(1_A (x) |0><0|)(tau (x) |0><0|)] = tr tau . tr|0><0| = 1 >= 1;
  D(viii) party computability, from the well-formed slots.
V7 NEVERTHELESS FAILS. CList is non-empty, so the first branch does not apply.
The default candidate Eq. eq:witness-empty that Theorem thm:feasibility (ii) tries first
gives
  tr[(1_A (x) |0><0|)(1_A/d_A (x) 1_Q/2)] = 1/2 ,
and 1/2 >= 1 IS FALSE. With no witness supplied the second branch fails too, so
V7 refuses with the VERBATIM reason `no_feasibility_witness`.
THIS IS THE ONLY PLACE WHERE V1-V8 REFUSE A WELL-FORMED DECLARATION. Theorem
thm:validator-soundness (ii) proves completeness for D(i)-D(vi) and D(viii), so every other
refusal names a real defect. The contract adds that the example is not exotic:
"exactly the same happens for EVERY declaration with CList non-empty presented
without a witness whose feasible set is non-empty but does not contain
Eq. eq:witness-empty".
HOW THE REFUSAL MUST BE READ, Remark rem:completeness: it means "I WAS NOT SHOWN
A FEASIBLE STATE", never "there is none", and MUST NOT be reported to a user as
a defect in the protocol. The supplier has a remedy inside the interface --
supply omega^* -- and no other check has that character. WIT-supplied-rescues is
that remedy exercised.""",
    ),
)


#: Five supplied witnesses, one failing each verification leg of Theorem
#: thm:feasibility (ii). Every one passes every OTHER leg, so each names exactly one.
WITNESS_LEG_FAILURES: tuple[WitnessCase, ...] = (
    WitnessCase(
        case_id="LEG-positivity",
        source_mode="untrusted",
        alice_dim=1,
        q_dim=2,
        sector_dims=(2,),
        tau_a=None,
        constraints=(),
        is_default_witness=False,
        witness=real_matrix(((2, 0), (0, -1))),
        leg_positive=False,
        leg_trace_one=True,
        leg_sector_blocks=True,
        leg_marginal=True,
        leg_constraints=True,
        constraint_values=(),
        v7_passes=False,
        refusal_reason=None,
        arithmetic="""\
THE POSITIVITY LEG. omega = diag(2, -1) on A Q with d_A = 1 and Q a qubit, so
the whole space is 2-dimensional.
  HERMITIAN: yes, it is real diagonal.
  TRACE ONE: 2 + (-1) = 1, so THE TRACE LEG PASSES -- chosen that way, so that a
  checker testing only the trace accepts it.
  SECTOR BLOCKS: |S| = 1, vacuous.
  POSITIVITY FAILS: the eigenvalues are 2 and -1, and -1 < 0. Definition
  def:feasible asks for omega in Pos(A Q), and Theorem thm:feasibility (ii) names the
  test explicitly -- "positivity by a Hermitian eigenvalue or Cholesky-type test
  on a d_A d_Q-dimensional matrix".
NO REFUSAL STRING IS FROZEN. The contract fixes only `no_feasibility_witness`
for the V7 refusal as a whole; which leg failed is named by the OBLIGATION of
Section 2.3 ("a machine-readable reason naming the failed check") and its
spelling is code's. `refusal_reason` is None here rather than an invented
string.""",
    ),
    WitnessCase(
        case_id="LEG-trace",
        source_mode="untrusted",
        alice_dim=2,
        q_dim=2,
        sector_dims=(2,),
        tau_a=None,
        constraints=(),
        is_default_witness=False,
        witness=real_matrix(
            (
                (F(1, 8), 0, 0, 0),
                (0, F(1, 8), 0, 0),
                (0, 0, F(1, 8), 0),
                (0, 0, 0, F(1, 8)),
            )
        ),
        leg_positive=True,
        leg_trace_one=False,
        leg_sector_blocks=True,
        leg_marginal=True,
        leg_constraints=True,
        constraint_values=(),
        v7_passes=False,
        refusal_reason=None,
        arithmetic="""\
THE TRACE LEG, and the mirror of the previous case: everything else passes.
omega = 1_{AQ}/8 = diag(1/8, 1/8, 1/8, 1/8).
  POSITIVE: diagonal with entries 1/8 >= 0. PASSES.
  SECTOR BLOCKS: vacuous at |S| = 1. PASSES.
  MARGINAL: untrusted, no condition. PASSES.
  TRACE FAILS: 4 x 1/8 = 1/2, and Definition def:feasible requires
  tr omega = 1 exactly.
A SUB-NORMALIZED WITNESS IS THE FAILURE MODE THAT LOOKS HARMLESS. It is
positive, it is block-diagonal, and every constraint of the form
tr[...] >= c is EASIER to satisfy after scaling down only if c <= 0 -- but
Definition def:feasible's set is a set of NORMALIZED states, and the consuming
engine minimizes over it. A checker that normalized the supplied witness before
testing would be repairing the supplier's data, which Section 2.5
(`fail_closed`) forbids: "no default value is ever substituted for a missing
datum".""",
    ),
    WitnessCase(
        case_id="LEG-sector-blocks",
        source_mode="untrusted",
        alice_dim=1,
        q_dim=3,
        sector_dims=(2, 1),
        tau_a=None,
        constraints=(),
        is_default_witness=False,
        witness=real_matrix(
            (
                (F(1, 2), 0, F(1, 2)),
                (0, 0, 0),
                (F(1, 2), 0, F(1, 2)),
            )
        ),
        leg_positive=True,
        leg_trace_one=True,
        leg_sector_blocks=False,
        leg_marginal=True,
        leg_constraints=True,
        constraint_values=(),
        v7_passes=False,
        refusal_reason=None,
        arithmetic="""\
THE SECTOR-BLOCK LEG, which needs |S| >= 2 to have any content. d_A = 1 and
Q = C^3 with S = (s0, s1), (d_s) = (2, 1), Pi_{s0} = diag(1, 1, 0),
Pi_{s1} = diag(0, 0, 1).
omega is the rank-one PROJECTOR onto (|0> + |2>)/sqrt2, frozen as a projector so
that its entries are rational:
  omega = [[1/2, 0, 1/2], [0, 0, 0], [1/2, 0, 1/2]] .
  POSITIVE: a projector, eigenvalues (1, 0, 0). PASSES.
  TRACE: 1/2 + 0 + 1/2 = 1. PASSES.
  SECTOR BLOCKS FAIL: (1_A (x) Pi_{s0}) omega (1_A (x) Pi_{s1}) has the single
  non-zero entry (0, 2) = 1/2 != 0. Definition def:feasible's first condition is
  exactly that this vanishes for every s != s'.
WHAT IT MEANS PHYSICALLY, and why the condition is in the feasible set and not
only in D(iii): the witness is a COHERENT SUPERPOSITION ACROSS TWO SECTORS. The
sector decomposition is the declaration's statement that no such coherence is
reachable, and a witness that violates it does not witness anything about the
declared model.""",
    ),
    WitnessCase(
        case_id="LEG-marginal",
        source_mode="trusted",
        alice_dim=2,
        q_dim=2,
        sector_dims=(2,),
        tau_a=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        constraints=(),
        is_default_witness=False,
        witness=real_matrix(
            (
                (F(1, 2), 0, 0, 0),
                (0, F(1, 2), 0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
            )
        ),
        leg_positive=True,
        leg_trace_one=True,
        leg_sector_blocks=True,
        leg_marginal=False,
        leg_constraints=True,
        constraint_values=(),
        v7_passes=False,
        refusal_reason=None,
        arithmetic="""\
THE MARGINAL LEG, which exists only in TRUSTED-source mode. tau_A = 1_A/2, and
the supplied witness is omega = |0><0|_A (x) 1_Q/2 = diag(1/2, 1/2, 0, 0).
  POSITIVE: entries 1/2, 1/2, 0, 0 >= 0. PASSES.
  TRACE: 1/2 + 1/2 = 1. PASSES.
  SECTOR BLOCKS: vacuous. PASSES.
  MARGINAL FAILS: omega_A = diag(1/2 + 1/2, 0 + 0) = diag(1, 0) = |0><0|, and
  |0><0| != 1_A/2 -- the two differ in both diagonal entries, 1 against 1/2 and
  0 against 1/2. Theorem thm:feasibility (ii) names the test: "the marginal condition by
  comparing d_A^2 entries", four entries here.
THE SAME STATE IS FEASIBLE IN UNTRUSTED MODE, where there is no marginal
condition at all. That is not an accident of this case: it is
Proposition prop:conservative's inclusion being STRICT, and the same omega is
frozen again in Group PC-G as the rem:notfallback witness -- the state that
tau_A = 1_A/d_A would exclude and nomarg admits.""",
    ),
    WitnessCase(
        case_id="LEG-constraint",
        source_mode="untrusted",
        alice_dim=2,
        q_dim=2,
        sector_dims=(2,),
        tau_a=None,
        constraints=((P_Z0, ">=", F(3, 4)),),
        is_default_witness=False,
        witness=real_matrix(
            (
                (0, 0, 0, 0),
                (0, F(1, 2), 0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, F(1, 2)),
            )
        ),
        leg_positive=True,
        leg_trace_one=True,
        leg_sector_blocks=True,
        leg_marginal=True,
        leg_constraints=False,
        constraint_values=(F(0),),
        v7_passes=False,
        refusal_reason="no_feasibility_witness",
        arithmetic="""\
THE CONSTRAINT LEG. The list is (|0><0|_Q, >=, 3/4) -- the same entry
WIT-supplied-rescues satisfies -- and the supplied witness is
omega = (1_A/2) (x) |1><1| = diag(0, 1/2, 0, 1/2).
  POSITIVE, TRACE ONE, BLOCKS: all pass, by inspection of the diagonal.
  MARGINAL: untrusted, no condition.
  CONSTRAINT FAILS: (1_A (x) |0><0|) omega = 0, because omega is supported
  entirely on the |1> subspace of Q, so the value is tr[0] = 0 and
  0 >= 3/4 IS FALSE.
V7 REFUSES with the verbatim reason `no_feasibility_witness`, which Theorem
thm:feasibility (ii) attaches to BOTH branches of the second case -- "when no witness is
supplied OR THE SUPPLIED ONE FAILS". THIS CASE IS THE SECOND BRANCH, and it is
frozen with the reason string because that string is the contract's own; the
four legs above are frozen WITHOUT one, because they are stages of the same
verification and the contract names no per-leg spelling.
THE PAIR (WIT-supplied-rescues, LEG-constraint) SHOWS THE CHECK IS TWO-SIDED ON
DATA: same entry, same declaration, two different supplied witnesses, one
accepted and one refused, and the difference is one exactly computed rational --
1 against 0.""",
    ),
)


O_PC_FEASIBILITY = PCOracleEntry(
    oracle_id="O-PC-FEASIBILITY",
    claims=("PC5", "PC6"),
    kind="toy-instance",
    subject=(
        "Theorem thm:feasibility (i)-(ii): the default witness Eq. eq:witness-empty in "
        "both source modes at named dimensions, verified condition by "
        "condition; an m >= 1 list the default satisfies and one it does not "
        "but a supplied witness does; the Theorem thm:validator-soundness (iii) counterexample "
        "field for field with its `no_feasibility_witness` refusal; and one "
        "supplied witness failing each verification leg."
    ),
    derivation="""\
contract.tex 0.1.4 Definition def:feasible (Eq. eq:feas, Eq. eq:feas-modes),
Theorem thm:feasibility (i)-(ii) with Eq. eq:witness-empty, Remark rem:nosearch, Theorem
thm:validator-soundness (iii), Remark rem:completeness and Definition def:validator V7.

THE TWO CASES OF PC5, AND WHY ONLY ONE IS A THEOREM. At CList empty,
Eq. eq:witness-empty is exhibited and verified, so D(vii) is PROVED -- the
hypothesis is D(i)-D(iii) alone, which is exactly what makes it usable inside
the proof of Theorem thm:validator-soundness (i). At CList non-empty, D(vii) is equivalent to
the existence of some omega satisfying Eq. eq:feas, which is a semidefinite
feasibility problem; the contract does not solve it and makes V7 a WITNESS
CHECK instead. Remark rem:nosearch gives the reason and the direction: "the
supplier that produced the entries produced them from a reachable-state argument
and CAN EXHIBIT A REACHABLE STATE", and the fail-closed direction is the safe
one because an empty feasible set would make the consuming engine's infimum an
infimum over the empty set.

THE FIVE LEGS OF THE VERIFICATION, named by Theorem thm:feasibility (ii) itself:
positivity, the trace, the off-diagonal block conditions, the marginal condition
(trusted mode only, compared over d_A^2 entries), and each constraint entry
evaluated against Theta_k in the ordering bowtie_k -- as a d_A x d_A matrix
comparison in trusted mode and as a scalar comparison in untrusted mode,
ACCORDING TO THE EMITTED SOURCE MODE (D(vi)). WITNESS_LEG_FAILURES has one case
per leg, each passing every other leg, so no case can be made to pass by fixing
a different leg.

WHY THE LEG CASES CARRY NO REFUSAL STRING BUT LEG-constraint DOES. The contract
names `no_feasibility_witness` for the V7 refusal, and thm:feasibility (ii) attaches it
both to "no witness is supplied" and to "the supplied one fails". LEG-constraint
is the second branch and carries it. The other four are frozen with
`refusal_reason` None, because inventing four per-leg spellings would decide
what Section 2.3 leaves to code -- it fixes the OBLIGATION to name the failed
check and no vocabulary.

THE ONE-SIDEDNESS, WHICH IS THE MOST CONSEQUENTIAL FACT IN THIS GROUP.
WIT-pc6iii-counterexample is a declaration on which D(i)-D(viii) ALL HOLD and V7
REFUSES. The gap is exactly D(vii) and exactly V7: the proof of thm:validator-soundness lists
V1/D(i), V2/D(ii), V3/D(iii), V4/D(iv), V6/D(vi) as literal restatements in both
directions and proves V5 <=> D(v) and V8 <=> D(viii), so the converse of
soundness fails only there. AN IMPLEMENTATION MUST NOT CLOSE THE GAP BY
SEARCHING -- that is Remark rem:nosearch -- AND MUST NOT REPORT THE REFUSAL AS A
DEFECT IN THE PROTOCOL.
""",
    hypotheses=(
        "Theorem thm:feasibility's hypothesis is D(i)-D(iii) on a CANDIDATE "
        "declaration, and the contract says in place that nothing in the proof "
        "uses that the declaration was emitted by Definition def:compile.",
        "In trusted mode the marginal leg uses tr tau_A = 1 from D(ii).",
    ),
)


O_PC_WELLPOSED = PCOracleEntry(
    oracle_id="O-PC-WELLPOSED",
    claims=("PC5", "PC6"),
    kind="structural-identity",
    subject=(
        "Remark rem:wellposed: with a NON-Hermitian constraint operator both "
        "lines of Eq. eq:feas-modes lose their meaning, not merely their "
        "soundness -- two exact witnesses, one non-Hermitian partial trace and "
        "one non-real scalar -- and check V3 is what refuses such an entry."
    ),
    derivation="""\
contract.tex 0.1.4 Remark rem:wellposed, Eq. eq:feas-modes, Eq. eq:ptrcyc,
Definition def:declaration, target condition D(iii) and Definition
def:validator V3.

WHAT THE REMARK PROVES, and it is worth restating because it is easy to read as
a soundness point when it is a WELL-POSEDNESS point. The trusted line of
Eq. eq:feas-modes compares two operators on A in the LOEWNER ORDER, which is
defined on Hermitian operators. That the left-hand side
tr_Q[(1_A (x) O^_k) omega] is Hermitian does NOT follow from omega = omega^dag
alone -- a product of two Hermitian operators need not be Hermitian. It follows
from D(iii), via Eq. eq:ptrcyc and the chain
(tr_Q[X omega])^dag = tr_Q[(X omega)^dag] = tr_Q[omega X] = tr_Q[X omega] with
X = 1_A (x) O^_k. The untrusted line needs the same hypothesis for the weaker
reason that tr[X omega] must be REAL before it can be compared with c_k.

WITNESS 1 -- THE TRUSTED LINE. Take Q a qubit, A a qubit, and the NON-Hermitian
Gaussian-rational operator
  O^ = [[0, 1], [0, 0]] ,  which satisfies O^ != O^dag = [[0, 0], [1, 0]] .
At omega = |Phi^+><Phi^+| the partial trace is computed from
|Phi^+><Phi^+| = (1/2) sum_{i,j} |i><j| (x) |i><j| :
  tr_Q[(1_A (x) O^) omega] = (1/2) sum_{i,j} |i><j| tr[O^ |i><j|]
                           = (1/2) sum_{i,j} <j|O^|i> |i><j|
                           = (1/2) O^T = (1/2) [[0, 0], [1, 0]] .
THAT MATRIX IS NOT HERMITIAN: its (1,0) entry is 1/2 and its (0,1) entry is 0.
So the left-hand side of the trusted line is not an object the Loewner order
compares, whatever Theta_k is. The comparison has no truth value -- which is the
remark's "lose their meaning rather than merely their soundness".

WITNESS 2 -- THE UNTRUSTED LINE. Take the Gaussian-rational, non-Hermitian
  O^' = [[i, 0], [0, 0]] ,   O^'^dag = [[-i, 0], [0, 0]] != O^' ,
and omega = 1_{AQ}/4 with d_A = 2. Then
  tr[(1_A (x) O^') omega] = (1/4) tr[1_A] . tr[O^'] = (1/4)(2)(i) = i/2 ,
which is NOT REAL and cannot be compared with c_k in R. Note that O^' has
Gaussian-rational entries, so the failure is exhibited exactly and not by an
approximation.

WHAT THE COMPILER DOES ABOUT IT. Hermiticity is a condition of Definition
def:declaration AND of D(iii) -- "and not only a check" -- and check V3 tests
O^_k = O^_k^dag on the emitted matrices. So both witnesses above describe
declarations that are REFUSED, naming V3, before any feasible-set computation is
attempted. Section 2.2's `constraint_entries` row carries the same condition on
the input side, and Assumption ass:spec asserts it of the specification; the
check is what makes the assertion checkable on the emitted data.
THE ROUTE MATTERS FOR RUN B: an implementation must test Hermiticity BEFORE it
evaluates Eq. eq:feas-modes, because after that point there is no well-defined
comparison to report a failure of.
""",
    hypotheses=(
        "Both witnesses are exact: the Gaussian-rational representation is what "
        "makes 'the trace is i/2, which is not real' a checkable statement "
        "rather than a floating-point observation.",
    ),
)


# ===========================================================================
#  Group PC-E -- the validator is sound and complete (PC6)
# ===========================================================================


@dataclass(frozen=True)
class ValidatorCase:
    """One declaration and the verdict of the check it is built to exercise."""

    case_id: str
    #: The check of Definition def:validator this case exercises, "V1".."V8",
    #: or None for the all-pass declaration.
    check: str | None
    #: The target condition of Definition def:target the check pairs with.
    target_condition: str | None
    #: Whether the target condition GENUINELY fails. False at V7, where the
    #: declaration is well-formed and refused anyway (Theorem thm:validator-soundness (iii)).
    genuine_violation: bool
    #: Whether all of D(i)-D(viii) hold for this declaration.
    well_formed: bool
    refuses: bool
    offending_datum: str
    arithmetic: str


VALIDATOR_CASES: tuple[ValidatorCase, ...] = (
    ValidatorCase(
        case_id="ALLPASS-MINI",
        check=None,
        target_condition=None,
        genuine_violation=False,
        well_formed=True,
        refuses=False,
        offending_datum="none -- every check passes",
        arithmetic="""\
THE ALL-PASS DECLARATION. MINI of Group PC-A, emitted, with its one untrusted
constraint entry (|0><0|_Q, >=, 1/4).
  V1 finiteness and totality: |X| = |V| = |O_A| = |O_B| = |C_A| = |C_B| = 2,
     |S| = 1, |Chat| = 2, |Z_perp| = 3, |K| = 4; every declared map is tabulated
     on all of its stated domain -- a_A on O_A, a_B on O_B, varsigma and phi on
     all four classes of K, r on all four pairs of X x V; and
     d_Q = sum_s d_s = 2. PASSES.
  V2 marginal slot: holds nomarg. PASSES by the first disjunct, without any
     matrix test.
  V3 operators: M_{x0} + M_{x1} = |0><0| + |1><1| = 1_A and both are projectors,
     so positive; F_{v0} + F_{v1} = 1_Q likewise; O^_1 = |0><0| is Hermitian;
     the block conditions are indexed by ordered pairs s != s' and there are
     none at |S| = 1. PASSES.
  V4 key alphabet: the tabulated values of r are (0, perp, perp, 1), all inside
     Z sqcup {perp} = (0, 1, perp). PASSES.
  V5 sifting consistency: a is injective on X x V here, so every class is
     realized once and every comparison is a pair with itself. PASSES.
  V6 constraint typing: the slot holds nomarg, so the untrusted branch applies:
     bowtie_1 = ">=" is in {<=, =, >=} and Theta_1 = 1/4 is in R. PASSES.
  V7 feasibility: CList is NOT empty, so the second branch applies; the default
     candidate Eq. eq:witness-empty gives the value 1/2 >= 1/4 and passes, so no
     supplied witness is needed (WIT-default-satisfies-list). PASSES.
  V8 party computability: a_A and a_B are tabulated on O_A and O_B; and the
     second clause compares pairs with equal holder readout AND equal
     announcements, which by injectivity of a is again only pairs with
     themselves. PASSES.
BY THE SOUNDNESS HALF Theorem thm:validator-soundness (i), D(i)-D(viii) THEREFORE ALL HOLD --
which is how the `well_formed` verdict is obtained here, rather than by checking
the conditions a second time.""",
    ),
    ValidatorCase(
        case_id="V1-partial-phi",
        check="V1",
        target_condition="D(i)",
        genuine_violation=True,
        well_formed=False,
        refuses=True,
        offending_datum="phi is not tabulated on the class (t1, r0) of K",
        arithmetic="""\
V1 asks that "every declared map is tabulated on all of its stated domain". The
WEIGHT declaration of Group PC-B with one row deleted from the phi table leaves
the class (t1, r0) unhandled, so phi is partial on K.
GENUINE D(i) VIOLATION: D(i) requires all declared maps TOTAL, and V1 and D(i)
are literal restatements of one another (proof of thm:validator-soundness, (i) and (ii)), so the
refusal names a real defect.
THE COST OF NOT CHECKING IT is exactly computed in O-PC-PARTIAL-PHI: Phi[omega]
sums to 7/8 rather than 1, at both frozen states, the deficit being the 1/8 mass
of the dropped class. Remark rem:phitotal: totality "is therefore CHECKED (V1),
not assumed, and a specification with an unhandled announcement class is REFUSED
rather than completed with a default value".""",
    ),
    ValidatorCase(
        case_id="V2-zero-marginal",
        check="V2",
        target_condition="D(ii)",
        genuine_violation=True,
        well_formed=False,
        refuses=True,
        offending_datum="tau_A = [[0, 0], [0, 0]]",
        arithmetic="""\
V2 asks that the slot hold nomarg, OR a Hermitian tau_A >= 0 with tr tau_A = 1.
The offending datum is the ZERO MATRIX on a qubit, which the contract singles
out twice: D(ii) says "in particular tau_A >= 0 and tr tau_A = 1, SO tau_A = 0
IS INADMISSIBLE", and the Outputs table repeats it -- "A singular tau_A is
admissible; tau_A = 0 is not".
  HERMITIAN: yes. POSITIVE SEMIDEFINITE: yes, trivially.
  TRACE: 0 + 0 = 0 != 1. V2 REFUSES on the trace clause alone.
GENUINE D(ii) VIOLATION, and the pair (V2, D(ii)) is a literal restatement in
both directions.
A SECOND OFFENDING DATUM FOR THE SAME CHECK, recorded so that an implementation
does not test only the trace: tau_A = diag(2, -1) is Hermitian with trace
2 + (-1) = 1 and is NOT positive semidefinite, eigenvalue -1. Either clause
alone is insufficient; V2 states both.
NOTE THE SENTINEL DISCIPLINE. Section 3 records that nomarg is "deliberately not
perp, which is the sifting-failure key value, and not 0, which is inadmissible".
So an implementation may not spell the empty slot as a zero matrix: the machine
value is null, and 0 is a matrix V2 refuses.""",
    ),
    ValidatorCase(
        case_id="V3-block-diagonality",
        check="V3",
        target_condition="D(iii)",
        genuine_violation=True,
        well_formed=False,
        refuses=True,
        offending_datum=(
            "F'_{v0} = [[1/2, 0, 1/2], [0, 0, 0], [1/2, 0, 1/2]] on Q = C^3 "
            "with S = (s0, s1), (d_s) = (2, 1)"
        ),
        arithmetic="""\
THE SECTOR-fails FAMILY OF GROUP PC-B, read as a validator case.
V3 tests five things: M_x >= 0 and sum_x M_x = 1_A; F_v >= 0 and
sum_v F_v = 1_Q; O^_k = O^_k^dag; and Pi_s F_v Pi_{s'} = 0 and
Pi_s O^_k Pi_{s'} = 0 for every pair s != s'.
THE FAMILY PASSES THE COMPLETENESS HALF -- the entrywise sums are
diag(1, 1, 1) -- AND FAILS THE BLOCK HALF: Pi_{s0} F'_{v0} Pi_{s1} has the entry
(0, 2) = 1/2 != 0. That is a genuine D(iii) violation, D(iii) carrying the same
conjunct.
TWO MORE OFFENDING DATA FOR THE SAME CHECK, each isolating a different conjunct,
recorded because V3 is the widest check of the eight:
  INCOMPLETE POVM -- the one-element family (|0><0|) on a qubit, whose sum is
  |0><0| != 1_Q, positive but not complete;
  NON-HERMITIAN CONSTRAINT OPERATOR -- O^ = [[0, 1], [0, 0]], for which
  O^ != O^dag = [[0, 0], [1, 0]]. That is the operator of O-PC-WELLPOSED, and
  the reason V3 must run BEFORE Eq. eq:feas-modes is evaluated: after that point
  there is no well-defined comparison to report a failure of.
THE NUMBER OF BLOCK CONDITIONS IS FINITE AND IS COUNTED BY thm:validator-soundness (iv):
|V| |S| (|S| - 1) + m |S| (|S| - 1). At |V| = 3, |S| = 2, m = 1 that is
3 . 2 . 1 + 1 . 2 . 1 = 6 + 2 = 8 conditions, of which this family fails one.""",
    ),
    ValidatorCase(
        case_id="V4-key-value-outside-alphabet",
        check="V4",
        target_condition="D(iv)",
        genuine_violation=True,
        well_formed=False,
        refuses=True,
        offending_datum="r(x0, v0) = 2 with Z = (0, 1), d_Z = 2",
        arithmetic="""\
V4 asks that every TABULATED value of r lie in Z sqcup {perp}. Take MINI with
its key map altered in one cell, r(x0, v0) = 2, and Z = (0, 1) unchanged so that
d_Z = 2 and Z_perp = (0, 1, perp).
  2 is not in (0, 1, perp), so V4 REFUSES on that cell.
GENUINE D(iv) VIOLATION: D(iv) is "r maps into Z sqcup {perp}", and V4 is its
literal restatement over the tabulated cells.
WHY IT IS REACHABLE AT ALL, given that Theorem thm:typing proves D(iv) for an
EMITTED declaration: the theorem's proof runs through
ran r subset ran r^0_h u {perp} subset Z sqcup {perp}, and the last inclusion is
Definition def:spec (d)'s typing of the key rule. A CANDIDATE declaration whose
r was supplied directly, or a specification whose r^0_h is mis-typed, has no
such guarantee -- which is Remark rem:rbuilt's point about what "generation, not
transcription" buys and where the residual obligation sits.
THE COUNT: V4 enumerates |X| |V| = 4 pairs here (thm:validator-soundness (iv)).""",
    ),
    ValidatorCase(
        case_id="V5-sifting-consistency",
        check="V5",
        target_condition="D(v)",
        genuine_violation=True,
        well_formed=False,
        refuses=True,
        offending_datum=(
            "r(x0, v0) = perp and r(x1, v0) = 1 with a(x0, v0) = a(x1, v0) = "
            "(alpha, beta0), which varsigma calls pass"
        ),
        arithmetic="""\
KEY-SIDECOND OF GROUP PC-C, read as a validator case. V5 asks that for all
(x, v) and (x', v') with a(x, v) = a(x', v'), r(x, v) = perp iff
r(x', v') = perp. The class (alpha, beta0) is realized by (x0, v0) and (x1, v0),
with r = perp and r = 1 respectively, so the biconditional fails.
GENUINE D(v) VIOLATION, and this one needs an argument rather than a
restatement, which is why thm:validator-soundness's proof gives V5 <=> D(v) a paragraph of its
own. NO varsigma whatsoever witnesses D(v) here: the right-hand side
varsigma(a(x, v)) = fail has ONE truth value on the class, while the left-hand
side r(x, v) = perp has TWO.
THE COUNT: V5 enumerates (|X| |V|)^2 ordered pairs (thm:validator-soundness (iv)); at
|X| = |V| = 2 that is 16.""",
    ),
    ValidatorCase(
        case_id="V6-constraint-typing",
        check="V6",
        target_condition="D(vi)",
        genuine_violation=True,
        well_formed=False,
        refuses=True,
        offending_datum=(
            "the slot holds nomarg while Theta_1 = [[1/2, 0], [0, 0]] is a "
            "Hermitian matrix on A and bowtie_1 is the operator order"
        ),
        arithmetic="""\
V6 asks for the typing to match the SLOT: bowtie_k in {preceq, =, succeq} with
Theta_k Hermitian on A WHEN THE MARGINAL SLOT IS FILLED, and
bowtie_k in {<=, =, >=} with Theta_k in R WHEN IT HOLDS nomarg.
The offending declaration is MINI -- untrusted, slot nomarg -- carrying an entry
whose right-hand side is the Hermitian matrix |0><0|/2 on A and whose relation
is the OPERATOR order succeq. Neither half matches: the mode demands a real
scalar and an order on R.
GENUINE D(vi) VIOLATION, the pair being a literal restatement in both
directions.
THIS IS THE CLAUSE THE PROOF OF THEOREM thm:typing NAMES AS THE ONE WHERE THE
EMISSION HYPOTHESIS DOES ITS WORK: "nothing in Assumption ass:spec prevents a
link from transporting an entry whose typing does not match the emitted source
mode -- THAT IS A PROPERTY OF THE SUPPLIER'S DATA, NOT OF THE COMPILATION MAP --
so this clause is where the hypothesis of the theorem does its work: CHECK V6
REJECTS EXACTLY SUCH AN ENTRY, and a declaration that is emitted at all is one
for which V6 did not refuse."
AND IT IS THE SAME CHECK THAT ANSWERS THE SOURCE-LINK CONSTRAINT SLOT. A source
link's descriptors are Alice-side -- Definition def:chaincond (S1) says "no
condition of the segment mentions Q, V or V^ph" -- while every emitted
constraint operator must be Hermitian and sector-block-diagonal ON Q. An entry
transported from that segment therefore fails V3 or V6 and the declaration is
refused, naming the check. Definition def:compile transports LITERALLY, "each
entry emitted with its relation symbol and right-hand side unchanged", and NO
TRANSFORMATION RULE IS ADDED HERE. Band A never exercises it: L_s = 0.""",
    ),
    ValidatorCase(
        case_id="V7-well-formed-but-refused",
        check="V7",
        target_condition="D(vii)",
        genuine_violation=False,
        well_formed=True,
        refuses=True,
        offending_datum=(
            "CList = ((|0><0|_Q, >=, 1)) with NO supplied witness; the feasible "
            "set is non-empty and does not contain Eq. eq:witness-empty"
        ),
        arithmetic="""\
THE ONE CHECK THAT REFUSES A WELL-FORMED DECLARATION. This is
WIT-pc6iii-counterexample of Group PC-D, and its full field-by-field derivation
is there.
  `well_formed` is TRUE: D(i)-D(viii) all hold, D(vii) because
  omega = tau (x) |0><0| is feasible for any tau in S_=(A).
  `genuine_violation` is FALSE: nothing about the declaration is defective.
  `refuses` is TRUE: CList is non-empty, the default candidate gives
  1/2 >= 1 which is false, and no witness was supplied.
V7 IS THEREFORE NOT PAIRED WITH ITS TARGET CONDITION IN BOTH DIRECTIONS, and the
contract says so in three places rather than one: Theorem thm:validator-soundness (iii), Remark
rem:completeness, and design decision 5 of Section 1.1, which adds the reason --
"A CHECKER THAT IS ONE-SIDED SOMEWHERE AND DOES NOT NAME WHERE IS WORSE THAN ONE
THAT IS ONE-SIDED AND DOES."
THE INTEGRITY TEST ASSERTS THAT THIS IS THE ONLY CASE IN THIS TUPLE WITH
`genuine_violation` FALSE AND `refuses` TRUE. Any other would be a checker
rejecting a good declaration somewhere the contract proves it does not.""",
    ),
    ValidatorCase(
        case_id="V8-party-computability",
        check="V8",
        target_condition="D(viii)",
        genuine_violation=True,
        well_formed=False,
        refuses=True,
        offending_datum=(
            "r(x0, v0) = 0 and r(x0, v1) = 1 with pi_A(x0, v0) = pi_A(x0, v1) "
            "= x0 and a(x0, v0) = a(x0, v1)"
        ),
        arithmetic="""\
KEY-V8 OF GROUP PC-C, read as a validator case. V8's second clause asks that
equal holder readouts and equal announcements force equal key values; here they
do not, so V8 REFUSES.
GENUINE D(viii) VIOLATION, and again one that needs an argument: thm:validator-soundness's
proof gives V8 <=> D(viii), the forward direction by taking r_h from
Eq. eq:partycomp and the reverse by CONSTRUCTING r_h from r, which is well
defined "precisely by V8's implication". Here no total r_h exists, because the
construction would have to give the single pair (x0, (alpha, beta)) two values.
V8'S FIRST CLAUSE is the announcement clause of D(viii) -- a_A and a_B tabulated
on O_A and O_B -- and it PASSES here; the failure is entirely in the second
clause. An implementation that checked only the first would accept a declaration
whose holder cannot compute its own key.
THE COUNT: V8 enumerates (|X| |V|)^2 ordered pairs; at |X| = 1, |V| = 2 that is
4.""",
    ),
)


@dataclass(frozen=True)
class ReconstructionCase:
    """One output of the two reconstructions inside the proof of thm:validator-soundness."""

    case_id: str
    reconstructed: str
    #: Declared and reconstructed values, as (argument, declared, rebuilt).
    rows: tuple[tuple[str, str, str], ...]
    agree_everywhere: bool
    arithmetic: str


RECONSTRUCTION_CASES: tuple[ReconstructionCase, ...] = (
    ReconstructionCase(
        case_id="RECON-varsigma-MINI",
        reconstructed="varsigma, from r and a (V5 => D(v))",
        rows=(
            ("(alpha0,beta0)", "pass", "pass"),
            ("(alpha0,beta1)", "fail", "fail"),
            ("(alpha1,beta0)", "fail", "fail"),
            ("(alpha1,beta1)", "pass", "pass"),
        ),
        agree_everywhere=True,
        arithmetic="""\
THE V5 => D(v) RECONSTRUCTION ON MINI. The proof of Theorem thm:validator-soundness defines
  varsigma(kappa) := fail if there EXISTS (x, v) in a^{-1}(kappa) with
                     r(x, v) = perp, and pass otherwise.
On MINI every class is realized by exactly one pair, so the rebuilt map reads
its verdict off that pair's key value: (alpha0,beta0) has r = 0, so pass;
(alpha0,beta1) has r = perp, so fail; (alpha1,beta0) has r = perp, so fail;
(alpha1,beta1) has r = 1, so pass.
THE REBUILT MAP EQUALS THE DECLARED ONE IN ALL FOUR CELLS, which is not an
accident here but is also not guaranteed in general -- see the next case.""",
    ),
    ReconstructionCase(
        case_id="RECON-varsigma-unrealized",
        reconstructed="varsigma on a class OUTSIDE the range of a",
        rows=(
            ("(alpha0,beta0)", "pass", "pass"),
            ("(alpha0,beta1)", "fail", "fail"),
            ("(alpha1,beta0)", "fail", "fail"),
            ("(alpha1,beta1)", "pass", "pass"),
            ("(alpha0,beta2)", "fail", "pass"),
            ("(alpha1,beta2)", "fail", "pass"),
        ),
        agree_everywhere=False,
        arithmetic="""\
THE CLAUSE THE PROOF PUTS IN PARENTHESES, MADE VISIBLE. Extend MINI's C_B by a
third letter beta2 that a_B never produces, so C_B = (beta0, beta1, beta2) and
|K| = 2 x 3 = 6 while only FOUR classes are realized by some (x, v). Let the
specification declare varsigma = fail on both unrealized classes; it must
declare SOMETHING, being total on K (Definition def:spec (d)).
The reconstruction of thm:validator-soundness's proof assigns PASS on an unrealized class,
because there is no witnessing pair with r = perp: "in particular on
kappa not in ran a, WHERE THE CHOICE IS IMMATERIAL because the condition of D(v)
quantifies over pairs (x, v)".
SO THE DECLARED AND REBUILT MAPS DIFFER IN EXACTLY THE TWO UNREALIZED CELLS, AND
BOTH WITNESS D(v) FOR THE SAME r. `agree_everywhere` is False, deliberately.
WHAT AN IMPLEMENTATION MUST NOT DO: assert that a rebuilt varsigma equals the
declared one, or treat a disagreement off ran a as a defect. What it MAY assert
is agreement on the realized classes, which is what D(v) quantifies over.""",
    ),
    ReconstructionCase(
        case_id="RECON-rhold-MINI",
        reconstructed="r_h, from r (V8 => D(viii))",
        rows=(
            ("(x0, (alpha0,beta0))", "0", "0"),
            ("(x0, (alpha0,beta1))", "perp", "perp"),
            ("(x0, (alpha1,beta0))", "perp", "perp"),
            ("(x0, (alpha1,beta1))", "0", "perp"),
            ("(x1, (alpha0,beta0))", "1", "perp"),
            ("(x1, (alpha0,beta1))", "perp", "perp"),
            ("(x1, (alpha1,beta0))", "perp", "perp"),
            ("(x1, (alpha1,beta1))", "1", "1"),
        ),
        agree_everywhere=False,
        arithmetic="""\
THE V8 => D(viii) RECONSTRUCTION ON MINI, set against Eq. eq:rhold. The
`declared` column is Eq. eq:rhold -- r^0_A on the passing classes, perp on the
failing ones -- and the `rebuilt` column is the proof's construction:
r_h(o, kappa) := r(x, v) for any realizing pair, AND perp on pairs that are not
realized.
O_A x K has 2 x 4 = 8 pairs and four are realized. The two columns agree on all
four realized pairs -- they must, both being r(x, v) there -- and DIFFER on
exactly two of the four unrealized ones, (x0, (alpha1,beta1)) where eq:rhold
gives 0 and the reconstruction gives perp, and (x1, (alpha0,beta0)) where
eq:rhold gives 1 and the reconstruction gives perp. On the other two unrealized
pairs both give perp, because the class fails.
BOTH ARE TOTAL ON O_A x K AND BOTH SATISFY Eq. eq:partycomp, which quantifies
over (x, v) only. The proof says so: "The value chosen on unrealized pairs is
IMMATERIAL".
THE SAME TWO TABLES ARE FROZEN IN GROUP PC-C AS KEY-MINI's `r_hold_eq_rhold` and
`r_hold_reconstructed`, and the integrity test asserts they agree exactly on
KEY-MINI's `realized_pairs` and differ somewhere off it.""",
    ),
)


@dataclass(frozen=True)
class DecidabilityCount:
    """The finite enumeration sizes of Theorem thm:validator-soundness (iv) at one instance."""

    case_id: str
    x_size: int
    v_size: int
    sector_count: int
    constraint_count: int
    #: |V| |S| (|S|-1) + m |S| (|S|-1), the block conditions of V3.
    block_conditions: int
    #: |X| |V|, the pairs V4 enumerates.
    v4_pairs: int
    #: (|X| |V|)^2, the ordered pairs V5 and V8 enumerate.
    ordered_pairs: int
    arithmetic: str


DECIDABILITY_COUNTS: tuple[DecidabilityCount, ...] = (
    DecidabilityCount(
        case_id="COUNT-MINI",
        x_size=2,
        v_size=2,
        sector_count=1,
        constraint_count=1,
        block_conditions=0,
        v4_pairs=4,
        ordered_pairs=16,
        arithmetic="""\
Theorem thm:validator-soundness (iv) at MINI: |X| = 2, |V| = 2, |S| = 1, m = 1.
  BLOCK CONDITIONS, the count the theorem writes out:
    |V| |S| (|S| - 1) + m |S| (|S| - 1) = 2 . 1 . 0 + 1 . 1 . 0 = 0 .
  ZERO IS THE RIGHT ANSWER AND IS NOT A DEGENERACY TO BE PATCHED: at |S| = 1
  there is no ordered pair s != s', so the conjunction of D(iii)'s block clause
  is empty and holds (Theorem thm:band-a (i)). An implementation that looped over
  s and s' would execute the body zero times, which is exactly right.
  V4 enumerates |X| |V| = 4 pairs.
  V5 and V8 enumerate (|X| |V|)^2 = 16 ordered pairs.
V1 compares finitely many declared integers -- here d_Q = 2 against
sum_s d_s = 2 -- and V2, V3, V6 evaluate finitely many matrix identities,
Hermiticity tests and positivity tests on matrices of dimension 2 and 4. V7 is
Theorem thm:feasibility (ii), whose own count is the five legs of Group PC-D.""",
    ),
    DecidabilityCount(
        case_id="COUNT-SECTOR",
        x_size=2,
        v_size=3,
        sector_count=2,
        constraint_count=1,
        block_conditions=8,
        v4_pairs=6,
        ordered_pairs=36,
        arithmetic="""\
Theorem thm:validator-soundness (iv) at the two-sector receiver of Group PC-B (SECTOR-holds and
SECTOR-fails): |X| = 2, |V| = 3, |S| = 2, m = 1.
  BLOCK CONDITIONS:
    |V| |S| (|S| - 1) + m |S| (|S| - 1) = 3 . 2 . 1 + 1 . 2 . 1 = 6 + 2 = 8 .
  Six for the three POVM elements at the two ordered pairs (s0, s1) and
  (s1, s0), and two for the single constraint operator at the same two pairs.
  SECTOR-fails fails ONE of the eight, Pi_{s0} F'_{v0} Pi_{s1} != 0, which is
  what makes the count worth freezing: a checker that tested only the UNORDERED
  pair would run four conditions and could still catch this one, but would miss
  a family whose only non-zero off-diagonal block is the lower one.
  V4 enumerates |X| |V| = 6 pairs; V5 and V8 enumerate 36 ordered pairs.
d_Q = sum_s d_s = 2 + 1 = 3 is the V1 comparison here, and it is non-trivial:
a declaration with (d_s) = (2, 1) and d_Q = 4 is refused by V1 before any
operator is examined.""",
    ),
)


O_PC_VALIDATOR = PCOracleEntry(
    oracle_id="O-PC-VALIDATOR",
    claims=("PC6",),
    kind="fail-closed",
    subject=(
        "Definition def:validator and Theorem thm:validator-soundness (i)-(iv): an all-pass "
        "declaration; ONE refusal case per check V1-V8, genuine D-violations "
        "everywhere except V7 where the declaration is well-formed and refused; "
        "the V5 and V8 reconstructions with their values off the realized set; "
        "and the decidability counts at two named instances."
    ),
    derivation="""\
contract.tex 0.1.4 Definition def:validator (V1-V8), Definition def:target
(D(i)-D(viii)), Theorem thm:validator-soundness (i)-(iv), Remark rem:completeness and design
decision 5 of Section 1.1.

THE SHAPE OF THE CLAIM, and it is not symmetric. SOUNDNESS holds for ALL EIGHT
conditions: if V1-V8 all pass then D(i)-D(viii) all hold. COMPLETENESS holds for
SEVEN: if D(i)-D(vi) and D(viii) hold then V1-V6 and V8 all pass. The missing
direction is exactly D(vii) => V7, and Theorem thm:validator-soundness (iii) exhibits the
counterexample. Remark rem:completeness says what each direction buys:
soundness is the safety direction, "without it the compiler could emit a
declaration that passes every check and is nonetheless ill-formed, which is the
failure this module exists to prevent"; completeness is what makes a REFUSAL
informative, "so a refusal names a real defect and not a limitation of the
checker".

WHICH PAIRS ARE RESTATEMENTS AND WHICH NEED A PROOF. V1/D(i), V2/D(ii),
V3/D(iii), V4/D(iv) and V6/D(vi) are literal restatements in both directions,
using for V3 the equivalence of the two block-diagonality formulations from
Theorem thm:measurements-and-statistics (ii). V5/D(v) and V8/D(viii) are equivalences that need an
argument, and the arguments are constructions -- of varsigma from r and a, and
of r_h from r -- whose OUTPUTS are frozen in RECONSTRUCTION_CASES. Both
constructions are non-unique off the realized set, and both non-uniquenesses are
frozen rather than smoothed over, because a test asserting a particular value
there would assert something the contract explicitly calls immaterial.

THE EIGHT REFUSAL CASES, each naming a DISTINCT check. The integrity test
asserts that the eight `check` values are exactly V1..V8 with no repeat, that
exactly one case has `genuine_violation` False, and that that one is V7. An
implementation whose V-checks overlap -- so that one datum is refused by two --
is not thereby wrong, but a REGISTRY whose cases did not separate the checks
would not be evidence that each check is individually necessary. Two pairs are
built specifically to defeat a half-check: KEY-SIDECOND passes V8 and fails V5,
KEY-V8 passes V5 and fails V8; and V3's three offending data isolate the
completeness conjunct, the Hermiticity conjunct and the block conjunct.

THE DECIDABILITY COUNTS ARE THE CONTRACT'S OWN ARITHMETIC, not a complexity
claim. thm:validator-soundness (iv) writes the block-condition count as
|V| |S| (|S| - 1) + m |S| (|S| - 1) and says V4, V5 and V8 enumerate |X| |V|
pairs, respectively (|X| |V|)^2 ordered pairs. Both frozen instances instantiate
those formulas exactly, one at |S| = 1 where the block count is 0 and one at
|S| = 2 where it is 8.
""",
    hypotheses=(
        "Theorem thm:validator-soundness is stated 'for a candidate declaration with finite "
        "tabulated data'. Several cases here are candidates that Definition "
        "def:compile could not have emitted, which is inside the theorem's "
        "scope and is what makes V5 and V8 exhibitable at all.",
        "The `well_formed` verdict on ALLPASS-MINI is obtained through the "
        "soundness half thm:validator-soundness (i) and not by re-deriving D(i)-D(viii).",
    ),
)


# ===========================================================================
#  Group PC-F -- consuming the reduction chain (PC7, PC8)
# ===========================================================================
#
#  A NOTE ON THE VERDICT WORDS USED IN THIS GROUP, so that they are not mistaken
#  for a contract vocabulary. Section 2.3 fixes a three-valued report vocabulary
#  for `gate_report` ONLY. For the interface conditions of Definition
#  def:chaincond the contract fixes no report tokens at all; what it fixes is
#  that a chain failing any of them "is REFUSED with that condition NAMED"
#  (Requirement req:chain-refusals (i)), that (C4) and (S3) are checkable only "where every
#  link supplies its channel as data" and are otherwise "carried instead as the
#  supplier obligation Assumption ass:link", and that at an empty segment the
#  conditions are "VACUOUS, quantifying over an empty list of links"
#  (Theorem thm:band-a (ii)). The four words below -- holds, fails, vacuous,
#  not checked -- are THIS REGISTRY'S descriptive labels for those four
#  situations. NO CHAIN-CONDITION REPORT SPELLING IS FROZEN AS A MACHINE TOKEN.

#: The three link status tags, VERBATIM from the Section 2.2 `reduction_chain`
#: row. No theorem, gate or output row of the contract reads the status, so a
#: status must be carried through and must not be allowed to decide anything.
LINK_STATUS_VOCABULARY: tuple[str, ...] = (
    "exact",
    "certified_outer",
    "exploratory_numeric",
)


@dataclass(frozen=True)
class ChainLink:
    """One typed link of one segment, with every slot the contract names."""

    link_id: str
    #: "source" for a link of R_src, "receiver" for a link of R_rec.
    segment: str
    link_type: str
    source_descriptor: str
    target_descriptor: str
    status: str
    #: Whether the link supplies its channel AS DATA. False for a link that
    #: supplies only a theorem constructor, where (C4) or (S3) is not decidable.
    channel_supplied: bool
    #: The constraint entries this link transports; empty tuple is EMITTED, not
    #: omitted (Remark req:chain-record-slots).
    transported_constraints: tuple[str, ...]
    #: The licence slot is always PRESENT; it may be empty.
    license_slot_present: bool
    license_slot_empty: bool


@dataclass(frozen=True)
class ChainCase:
    """One presented chain and the verdict of every interface condition."""

    case_id: str
    source_segment: tuple[ChainLink, ...]
    receiver_segment: tuple[ChainLink, ...]
    l_s: int
    l_r: int
    physical_alphabet: tuple[str, ...]
    emitted_alphabet: tuple[str, ...]
    #: The declared outcome correspondence gamma, as (w, v) pairs.
    gamma: tuple[tuple[str, str], ...]
    #: (condition, verdict) with verdict in
    #: ("holds", "fails", "vacuous", "not checked") -- see the group note.
    verdicts: tuple[tuple[str, str], ...]
    #: The condition a refusal names, or None where nothing is refused.
    failing_condition: str | None
    #: The assumption named where a condition is NOT decided, else None.
    named_assumption: str | None
    refuses: bool
    arithmetic: str


_BAND_A_LINK = ChainLink(
    link_id="Lambda_1",
    segment="receiver",
    link_type="squashing (identity)",
    source_descriptor="(Q, (s0), (2))",
    target_descriptor="(Q, (s0), (2))",
    status="exact",
    channel_supplied=True,
    transported_constraints=(),
    license_slot_present=True,
    license_slot_empty=True,
)


CHAIN_CASES: tuple[ChainCase, ...] = (
    ChainCase(
        case_id="CHAIN-bandA",
        source_segment=(),
        receiver_segment=(_BAND_A_LINK,),
        l_s=0,
        l_r=1,
        physical_alphabet=("v0", "v1"),
        emitted_alphabet=("v0", "v1"),
        gamma=(("v0", "v0"), ("v1", "v1")),
        verdicts=(
            ("C1", "holds"),
            ("C2", "holds"),
            ("C3", "holds"),
            ("C4", "holds"),
            ("C5", "holds"),
            ("S1", "vacuous"),
            ("S2", "vacuous"),
            ("S3", "vacuous"),
            ("S4", "vacuous"),
            ("X1", "holds"),
        ),
        failing_condition=None,
        named_assumption=None,
        refuses=False,
        arithmetic="""\
THE BAND-A CHAIN RECORD, FIELD FOR FIELD -- the record Slice 1 consumes.
Definition def:bandA (b): L_s = 0 and L = 1 with Lambda_1 = id_Q, status
`exact', empty constraint slot and empty licence slot. Definition def:bandA (a)
fixes the emitted sector set as the singleton S = (s0) with Pi_{s0} = 1_Q.
  R = (R_src, R_rec) with R_src = () and R_rec = (Lambda_1) .
  Lambda_1 : type squashing/identity; source descriptor (Q, (s0), (2)); target
  descriptor (Q, (s0), (2)); status `exact'; channel SUPPLIED AS DATA, namely
  id_Q; transported constraint entries: NONE, and the slot is EMITTED EMPTY;
  licence slot: PRESENT and EMPTY.
  gamma = the identity bijection on V = V^ph.
THE TEN VERDICTS, exactly as Theorem thm:band-a (ii) takes them.
  (C1) source and target descriptors of id_Q are both (Q, (s0), (2)), and the
       physical receiver space IS Q by def:bandA (a). HOLDS.
  (C2) the identity map on V is a tabulated bijection, in particular a total
       surjection with singleton fibres. HOLDS.
  (C3) the declared receiver family is a POVM, together with the vacuous sector
       condition of thm:band-a (i). HOLDS.
  (C4) for every operator Y and state rho, tr[Y id(rho)] = tr[Y rho], so
       id^dag = id and Eq. eq:pullback reads F_v = F^ph_v, every fibre
       gamma^{-1}(v) being a singleton. HOLDS -- and it is CHECKED, not carried,
       because the link supplies its channel as data.
  (C5) the constraint and licence slots are present and empty. HOLDS.
  (S1)-(S4) quantify over the links of R_src, and that list is EMPTY. VACUOUS.
       Eq. eq:srcmap holds with Xi the identity, A'' = A' and rho^v_x = rho_x.
  (X1) the shape of the record, with nothing in the first component. HOLDS.
WHY EVERY EMPTY SLOT IS STILL EMITTED, Remark req:chain-record-slots: "a record shape
that omits an empty slot cannot later distinguish 'no entries' from 'entries not
carried', and a record with one undifferentiated list of links cannot later be
asked which of them were source maps". THIS COSTS NOTHING NOW AND IS NOT
RETROFITTABLE, which is why the empty source segment and the two empty slots are
frozen as PRESENT rather than absent.
THE CONSEQUENCE FOR CList, Theorem thm:band-a (iii): CList is the concatenation of
the specification's entry list -- empty in Band A -- with the entries the links
transport, and the single link's constraint slot is empty. A concatenation of
empty lists is empty, so m = 0, the two-part gate of thm:gates is NOT ENGAGED,
Assumption ass:link's second clause is vacuous, and Assumption ass:lic is not
invoked.
AND THE FIRST CLAUSE OF ass:link IS DISCHARGED BY EXHIBITION here -- id IS a
channel -- which is what thm:band-a (iv) means by "no emitted slot, and no claim
used in the Band-A path, depends on a `receiver-povm` or `proof-reductions`
artifact". What remains is Assumption ass:ideal, an IDEALIZATION of the receiver
and not a reduction of it.""",
    ),
    ChainCase(
        case_id="CHAIN-coarse-proper",
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment="receiver",
                link_type="squashing",
                source_descriptor="C^3 (physical receiver space)",
                target_descriptor="(Q, (s0), (2))",
                status="exact",
                channel_supplied=True,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=True,
            ),
        ),
        l_s=0,
        l_r=1,
        physical_alphabet=("w0", "w1", "w2"),
        emitted_alphabet=("v0", "v1"),
        gamma=(("w0", "v0"), ("w1", "v1"), ("w2", "v1")),
        verdicts=(
            ("C1", "holds"),
            ("C2", "holds"),
            ("C3", "holds"),
            ("C4", "holds"),
            ("C5", "holds"),
            ("S1", "vacuous"),
            ("S2", "vacuous"),
            ("S3", "vacuous"),
            ("S4", "vacuous"),
            ("X1", "holds"),
        ),
        failing_condition=None,
        named_assumption=None,
        refuses=False,
        arithmetic="""\
A PROPER COARSE-GRAINING, with a NON-INJECTIVE total surjection, and
Eq. eq:pullback and Eq. eq:pullbackstats evaluated on named matrices.
THE DATA. The physical receiver space is C^3 with the projective family
  F^ph_{w0} = diag(1, 0, 0) , F^ph_{w1} = diag(0, 1, 0) ,
  F^ph_{w2} = diag(0, 0, 1) ,   sum = 1_3 .
The emitted Q is a qubit with one sector and F_{v0} = |0><0|, F_{v1} = |1><1|.
The declared correspondence is gamma(w0) = v0, gamma(w1) = v1, gamma(w2) = v1 --
TOTAL and SURJECTIVE, and NOT INJECTIVE: the fibre gamma^{-1}(v1) = (w1, w2) has
two elements. THAT IS THE DIRECTION (C2) FIXES, from the PHYSICAL alphabet onto
the EMITTED one, of which a bijection is the special case.
THE CHANNEL, supplied as data by its two Kraus operators
  K_0 = [[1, 0, 0], [0, 1, 0]] ,  K_1 = [[0, 0, 0], [0, 0, 1]] ,
which is trace preserving because
K_0^dag K_0 + K_1^dag K_1 = diag(1, 1, 0) + diag(0, 0, 1) = 1_3.
Eq. eq:pullback, Lambda^dag(Y) = K_0^dag Y K_0 + K_1^dag Y K_1, evaluated
entry by entry:
  Lambda^dag(F_{v0}) = K_0^dag diag(1,0) K_0 + K_1^dag diag(1,0) K_1
                     = diag(1, 0, 0) + 0 = diag(1, 0, 0) = F^ph_{w0} ,
  and gamma^{-1}(v0) = (w0), so the right-hand side is F^ph_{w0}. HOLDS.
  Lambda^dag(F_{v1}) = K_0^dag diag(0,1) K_0 + K_1^dag diag(0,1) K_1
                     = diag(0, 1, 0) + diag(0, 0, 1) = diag(0, 1, 1) ,
  and the right-hand side is F^ph_{w1} + F^ph_{w2} = diag(0, 1, 1). HOLDS.
  THE FIBRE IS SUMMED, which is the whole difference from a bare index map.
Eq. eq:pullbackstats, Theorem thm:chain-consumption (iii), at TWO named states.
  rho = diag(1/2, 1/4, 1/4):
    Lambda(rho) = K_0 rho K_0^dag + K_1 rho K_1^dag
                = diag(1/2, 1/4) + diag(0, 1/4) = diag(1/2, 1/2) .
    tr[F_{v0} Lambda(rho)] = 1/2  and  tr[F^ph_{w0} rho] = 1/2 . EQUAL.
    tr[F_{v1} Lambda(rho)] = 1/2  and  tr[F^ph_{w1} rho] + tr[F^ph_{w2} rho]
                                     = 1/4 + 1/4 = 1/2 . EQUAL.
  rho' = the rank-one PROJECTOR onto (|1> + |2>)/sqrt2, frozen as a projector so
  that its entries are rational:
    rho' = [[0, 0, 0], [0, 1/2, 1/2], [0, 1/2, 1/2]] , trace 1 .
    K_0 rho' K_0^dag = [[0, 0], [0, 1/2]] and K_1 rho' K_1^dag = [[0, 0],
    [0, 1/2]] , so Lambda(rho') = [[0, 0], [0, 1]] = |1><1| .
    tr[F_{v0} Lambda(rho')] = 0 = tr[F^ph_{w0} rho'] . EQUAL.
    tr[F_{v1} Lambda(rho')] = 1 = 1/2 + 1/2 . EQUAL.
  NOTE WHAT THE SECOND STATE SHOWS AND THE FIRST CANNOT: the coherence between
  |1> and |2> is DESTROYED by Lambda -- the off-diagonal 1/2 entries do not
  survive -- and the statistics identity still holds outcome by outcome, because
  it is a statement about the two families and not about coherences.
CONSISTENCY WITH COMPLETENESS, the last part of thm:chain-consumption (iii): summing
Eq. eq:pullback over v and using unitality of Lambda^dag gives
1_3 = sum_w F^ph_w, which is completeness of the physical family and therefore
NO RESTRICTION AT ALL. Here diag(1,0,0) + diag(0,1,1) = 1_3, as computed.""",
    ),
    ChainCase(
        case_id="CHAIN-coarse-wrong-direction",
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment="receiver",
                link_type="squashing",
                source_descriptor="C^2 (physical receiver space)",
                target_descriptor="(Q, (s0), (2))",
                status="exact",
                channel_supplied=True,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=True,
            ),
        ),
        l_s=0,
        l_r=1,
        physical_alphabet=("w0", "w1"),
        emitted_alphabet=("v0", "v1", "v2"),
        gamma=(("v0", "w0"), ("v1", "w1"), ("v2", "w1")),
        verdicts=(
            ("C1", "holds"),
            ("C2", "fails"),
            ("C3", "holds"),
            ("C4", "not checked"),
            ("C5", "holds"),
            ("S1", "vacuous"),
            ("S2", "vacuous"),
            ("S3", "vacuous"),
            ("S4", "vacuous"),
            ("X1", "holds"),
        ),
        failing_condition="C2",
        named_assumption=None,
        refuses=True,
        arithmetic="""\
THE WRONG-DIRECTION CORRESPONDENCE OF REMARK rem:coarse, AND ITS REFUSAL. The
`gamma` column here is deliberately written EMITTED -> PHYSICAL, which is the
direction (C2) forbids, and the pairs are read (v, w).
THE ARITHMETIC OF THEOREM thm:chain-consumption (iii), STEP 3, instantiated. Suppose a total surjection
gamma' : V -> V^ph with |V| = 3 and |V^ph| = 2, gamma'(v0) = w0,
gamma'(v1) = gamma'(v2) = w1, and the pullback read as
Lambda^dag(F_v) = F^ph_{gamma'(v)}. Summing over v and using unitality of
Lambda^dag:
  1 = sum_v Lambda^dag(F_v) = F^ph_{w0} + F^ph_{w1} + F^ph_{w1}
    = F^ph_{w0} + 2 F^ph_{w1} .
Against completeness F^ph_{w0} + F^ph_{w1} = 1 this gives
  sum_w (|gamma'^{-1}(w)| - 1) F^ph_w = 0 ,  i.e.  F^ph_{w1} = 0 ,
every coefficient being a non-negative integer and every F^ph_w positive
semidefinite. HERE THE COEFFICIENTS ARE (1 - 1) = 0 AT w0 AND (2 - 1) = 1 AT w1,
so the surviving family is (F^ph_{w0}, 0) = (1_2, 0): the only non-injective
gamma' that survives has NULL extra outcomes, i.e. no coarse-graining at all.
THE VERDICT: (C2) FAILS and the chain is REFUSED, naming (C2). The direction is
not a convention that could have gone the other way -- "Coarse-graining is a
REAL operation -- a squashed family is typically COARSER than the physical one
-- so the correspondence must run from the finer alphabet to the coarser".
(C4) IS `not checked' HERE, and deliberately so: with (C2) failed there are no
well-defined fibres gamma^{-1}(v) to sum over, so Eq. eq:pullback has no
right-hand side. An implementation that evaluated (C4) first and reported it
`passed' would be reporting a computation on an ill-formed input.
WHAT EMITTING THE PAIR BUYS, the remark's closing sentence: "Emitting the pair
(gamma, Eq. eq:pullback) rather than a bare index map is what keeps the
statistics identity Eq. eq:pullbackstats true OUTCOME BY OUTCOME".""",
    ),
    ChainCase(
        case_id="CHAIN-source-link-in-receiver-segment",
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment="receiver",
                link_type="source map, PRESENTED IN THE RECEIVER SEGMENT",
                source_descriptor="A'' (virtual transmitted system, a qubit)",
                target_descriptor="A' (transmitted system, a qubit)",
                status="exact",
                channel_supplied=True,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=True,
            ),
        ),
        l_s=0,
        l_r=1,
        physical_alphabet=("w0", "w1"),
        emitted_alphabet=("v0", "v1"),
        gamma=(("w0", "v0"), ("w1", "v1")),
        verdicts=(
            ("C1", "fails"),
            ("C2", "holds"),
            ("C3", "holds"),
            ("C4", "not checked"),
            ("C5", "holds"),
            ("S1", "vacuous"),
            ("S2", "vacuous"),
            ("S3", "vacuous"),
            ("S4", "vacuous"),
            ("X1", "holds"),
        ),
        failing_condition="C1",
        named_assumption=None,
        refuses=True,
        arithmetic="""\
A WRONG-SEGMENT LINK, FIRST DIRECTION: a SOURCE map written into R_rec.
Definition def:chaincond (X1) says the order rule "is NOT a tag and is NOT
CHECKED: it is the SHAPE of the record", and then says exactly what happens to a
misplaced link -- "a link presented in the wrong segment FAILS THAT SEGMENT'S
DESCRIPTOR RULE ... (C1) for a source map, since A' IS NOT THE PHYSICAL RECEIVER
SPACE".
HERE: the link's source descriptor is A'' and its target descriptor is A', both
Alice-side. (C1) requires the source descriptor of Lambda_1 to be THE PHYSICAL
RECEIVER SPACE of S_rec and the target descriptor of Lambda_L to be
(Q, S, (d_s)). Neither holds: A'' is not the physical receiver space and A' is
not (Q, S, (d_s)). (C1) FAILS and the chain is REFUSED naming (C1).
(X1) ITSELF IS RECORDED AS `holds', NOT AS THE FAILING CONDITION, and that is
the point of the design decision: Theorem thm:chain-consumption (i) says "(X1) is NOT DECIDED,
because it is not a condition on data: it is the TYPE of the record", and its
proof adds that (X1) "is a statement about WHICH OF THE TWO LISTS a link was
written into, which the record answers by construction". A misplaced link does
not violate the order rule; it violates a descriptor rule. AN IMPLEMENTATION
THAT REFUSED NAMING (X1) WOULD BE NAMING A CONDITION THE CONTRACT SAYS IS NOT
CHECKED.""",
    ),
    ChainCase(
        case_id="CHAIN-squashing-link-in-source-segment",
        source_segment=(
            ChainLink(
                link_id="Xi_1",
                segment="source",
                link_type="squashing map, PRESENTED IN THE SOURCE SEGMENT",
                source_descriptor="C^3 (physical receiver space)",
                target_descriptor="(Q, (s0), (2))",
                status="exact",
                channel_supplied=True,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=True,
            ),
        ),
        receiver_segment=(_BAND_A_LINK,),
        l_s=1,
        l_r=1,
        physical_alphabet=("v0", "v1"),
        emitted_alphabet=("v0", "v1"),
        gamma=(("v0", "v0"), ("v1", "v1")),
        verdicts=(
            ("C1", "holds"),
            ("C2", "holds"),
            ("C3", "holds"),
            ("C4", "holds"),
            ("C5", "holds"),
            ("S1", "fails"),
            ("S2", "not checked"),
            ("S3", "not checked"),
            ("S4", "holds"),
            ("X1", "holds"),
        ),
        failing_condition="S1",
        named_assumption=None,
        refuses=True,
        arithmetic="""\
A WRONG-SEGMENT LINK, SECOND DIRECTION: a SQUASHING map written into R_src. The
contract names this half too -- "(S1) for a squashing map, since Q IS NOT AN
ALICE-SIDE DESCRIPTOR".
(S1) requires that the target descriptor of Xi_{L_s} be the transmitted system
A' named by S_src, that the source descriptor of Xi_1 be the virtual transmitted
system A'', and -- the clause that decides this case -- that EVERY DESCRIPTOR OF
THE SEGMENT BE AN ALICE-SIDE DESCRIPTOR: "no condition of the segment mentions
Q, V or V^ph". This link's descriptors are the physical receiver space and
(Q, (s0), (2)). (S1) FAILS and the chain is REFUSED naming (S1).
(S2) AND (S3) ARE `not checked': (S2) asks that the link carry the signal index
x through unchanged with the weights p_x untouched, and (S3) asks
Xi(rho^v_x) = rho_x -- neither is even TYPED for a channel out of the receiver
space, so there is nothing to evaluate. Recording them as `not checked' rather
than `fails' keeps the refusal pointing at the ONE condition that decided it,
which is what "refused WITH THAT CONDITION NAMED" requires.
THE TWO WRONG-SEGMENT CASES TOGETHER ARE THE EVIDENCE FOR THE DESIGN DECISION.
Design decision 3 of Section 1.1: "A source map replaces Alice's signal ensemble
on the TRANSMITTED system; a squashing map replaces Bob's measurement on the
RECEIVER system. These are different types, and A SINGLE LIST OF LINKS CANNOT
CARRY BOTH". The composition-order rule is then a property of the record's SHAPE
rather than a tag to be checked, "WHICH IS THE STRONGER FORM OF THE SAME SAFETY
RULE".""",
    ),
    ChainCase(
        case_id="CHAIN-receiver-descriptor-mismatch",
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment="receiver",
                link_type="squashing",
                source_descriptor="C^4 (physical receiver space)",
                target_descriptor="C^2",
                status="exact",
                channel_supplied=True,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=True,
            ),
            ChainLink(
                link_id="Lambda_2",
                segment="receiver",
                link_type="squashing",
                source_descriptor="C^3",
                target_descriptor="(Q, (s0), (2))",
                status="exact",
                channel_supplied=True,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=True,
            ),
        ),
        l_s=0,
        l_r=2,
        physical_alphabet=("w0", "w1"),
        emitted_alphabet=("v0", "v1"),
        gamma=(("w0", "v0"), ("w1", "v1")),
        verdicts=(
            ("C1", "fails"),
            ("C2", "holds"),
            ("C3", "holds"),
            ("C4", "not checked"),
            ("C5", "holds"),
            ("S1", "vacuous"),
            ("S2", "vacuous"),
            ("S3", "vacuous"),
            ("S4", "vacuous"),
            ("X1", "holds"),
        ),
        failing_condition="C1",
        named_assumption=None,
        refuses=True,
        arithmetic="""\
A DESCRIPTOR MISMATCH INSIDE THE RECEIVER SEGMENT, at L = 2.
(C1) has three clauses: the target descriptor of Lambda_i equals the source
descriptor of Lambda_{i+1} for 1 <= i < L; the source descriptor of Lambda_1 is
the physical receiver space; and the target descriptor of Lambda_L is
(Q, S, (d_s)).
Here the SECOND and THIRD clauses hold -- C^4 is the declared physical receiver
space and Lambda_2's target is (Q, (s0), (2)) -- while the FIRST fails at i = 1:
Lambda_1's target is C^2 and Lambda_2's source is C^3, and 2 != 3. THE COMPOSITE
Lambda_2 o Lambda_1 DOES NOT EVEN TYPE, so (C4) is `not checked': there is no
composite whose adjoint could be applied to F_v.
THE CHECK IS A COMPARISON OF DECLARED DESCRIPTORS AND NOTHING MORE -- Theorem
thm:chain-consumption (i): "(C1) and (S1) compare finitely many declared descriptors". At
L = 2 that is 1 adjacency comparison plus the two end comparisons, three in all.
A CHECKER THAT VERIFIED ONLY THE ENDS would accept this chain, which is why the
adjacency clause is frozen as the failing one.""",
    ),
    ChainCase(
        case_id="CHAIN-source-descriptor-mismatch",
        source_segment=(
            ChainLink(
                link_id="Xi_1",
                segment="source",
                link_type="source map",
                source_descriptor="A'' (a qubit)",
                target_descriptor="A_mid (a qubit)",
                status="exact",
                channel_supplied=True,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=True,
            ),
            ChainLink(
                link_id="Xi_2",
                segment="source",
                link_type="source map",
                source_descriptor="A_mid' (a QUTRIT)",
                target_descriptor="A' (a qubit)",
                status="exact",
                channel_supplied=True,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=True,
            ),
        ),
        receiver_segment=(_BAND_A_LINK,),
        l_s=2,
        l_r=1,
        physical_alphabet=("v0", "v1"),
        emitted_alphabet=("v0", "v1"),
        gamma=(("v0", "v0"), ("v1", "v1")),
        verdicts=(
            ("C1", "holds"),
            ("C2", "holds"),
            ("C3", "holds"),
            ("C4", "holds"),
            ("C5", "holds"),
            ("S1", "fails"),
            ("S2", "holds"),
            ("S3", "not checked"),
            ("S4", "holds"),
            ("X1", "holds"),
        ),
        failing_condition="S1",
        named_assumption=None,
        refuses=True,
        arithmetic="""\
A DESCRIPTOR MISMATCH INSIDE THE SOURCE SEGMENT, at L_s = 2, and the mirror of
the receiver case above.
(S1)'s adjacency clause asks that the target descriptor of Xi_i equal the source
descriptor of Xi_{i+1} for 1 <= i < L_s. Xi_1's target is the qubit A_mid and
Xi_2's source is the QUTRIT A_mid', so the composite Xi_2 o Xi_1 does not type
and (S1) FAILS. The two end clauses hold: Xi_1's source is A'' and Xi_2's target
is A', both Alice-side, as (S1)'s last sentence requires.
(S3) IS `not checked' for the same reason (C4) was in the receiver case: there
is no composite Xi to evaluate Eq. eq:srcmap on.
(S2) HOLDS AND IS RECORDED SEPARATELY, because it is independent of the
descriptors: each link carries the signal index x through unchanged, mapping a
family indexed by X to a family indexed by X with the weights p_x untouched. A
chain can satisfy (S2) and fail (S1), and CHAIN-index-failure below is the
converse.""",
    ),
    ChainCase(
        case_id="CHAIN-index-failure",
        source_segment=(
            ChainLink(
                link_id="Xi_1",
                segment="source",
                link_type="source map",
                source_descriptor="A'' (a qubit)",
                target_descriptor="A' (a qubit)",
                status="exact",
                channel_supplied=True,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=True,
            ),
        ),
        receiver_segment=(_BAND_A_LINK,),
        l_s=1,
        l_r=1,
        physical_alphabet=("v0", "v1"),
        emitted_alphabet=("v0", "v1"),
        gamma=(("v0", "v0"), ("v1", "v1")),
        verdicts=(
            ("C1", "holds"),
            ("C2", "holds"),
            ("C3", "holds"),
            ("C4", "holds"),
            ("C5", "holds"),
            ("S1", "holds"),
            ("S2", "fails"),
            ("S3", "not checked"),
            ("S4", "holds"),
            ("X1", "holds"),
        ),
        failing_condition="S2",
        named_assumption=None,
        refuses=True,
        arithmetic="""\
AN (S2) FAILURE, WITH THE DESCRIPTORS CORRECT. (S2) asks that each link carry the
signal index x through unchanged: "it maps a family indexed by X to a family
indexed by X, WITH THE WEIGHTS p_x UNTOUCHED". Two independent halves, and this
case fails the SECOND one so that a checker testing only the index set accepts
it.
THE DATA. X = (x0, x1) on both sides -- the index set IS preserved -- but the
link presents the virtual family with weights (p_{x0}, p_{x1}) = (1/2, 1/2) and
the specified family with weights (3/4, 1/4). The weights are NOT untouched:
1/2 != 3/4 and 1/2 != 1/4.
(S2) FAILS and the chain is REFUSED naming (S2).
WHY IT MATTERS DOWNSTREAM AND IS NOT BOOKKEEPING. Theorem thm:chain-consumption (iv) applies
id_X (x) Xi to the classical-quantum source state
sum_x p_x |x><x|_X (x) rho^v_x and concludes that it is carried onto
sum_x p_x |x><x|_X (x) rho_x, "index by index, WITH THE WEIGHTS UNCHANGED BY
(S2)". A link that reweighted would give a different classical-quantum state,
and the certificate condition (SR2) -- which reads
tr_A[(M_x (x) 1) |Psi><Psi|] = p_x rho^v_x, weight and state TOGETHER -- would
be checked against the wrong p_x.
THE COUNT: thm:chain-consumption (i) says (S2) "compares two finite index sets and |X|
declared weights", so two set comparisons and two weight comparisons here.""",
    ),
    ChainCase(
        case_id="CHAIN-srcmap-failure",
        source_segment=(
            ChainLink(
                link_id="Xi_1",
                segment="source",
                link_type="source map (completely dephasing in the Z basis)",
                source_descriptor="A'' (a qubit)",
                target_descriptor="A' (a qubit)",
                status="exact",
                channel_supplied=True,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=True,
            ),
        ),
        receiver_segment=(_BAND_A_LINK,),
        l_s=1,
        l_r=1,
        physical_alphabet=("v0", "v1"),
        emitted_alphabet=("v0", "v1"),
        gamma=(("v0", "v0"), ("v1", "v1")),
        verdicts=(
            ("C1", "holds"),
            ("C2", "holds"),
            ("C3", "holds"),
            ("C4", "holds"),
            ("C5", "holds"),
            ("S1", "holds"),
            ("S2", "holds"),
            ("S3", "fails"),
            ("S4", "holds"),
            ("X1", "holds"),
        ),
        failing_condition="S3",
        named_assumption=None,
        refuses=True,
        arithmetic="""\
AN Eq. eq:srcmap FAILURE, exhibited exactly. (S3) asks Xi(rho^v_x) = rho_x for
every x, WHERE THE CHANNEL RUNS FROM THE VIRTUAL STATES TO THE SPECIFIED ONES --
the direction the contract fixes and records the locator for.
THE DATA. X = (x0, x1) with p = (1/2, 1/2). The virtual ensemble is
rho^v_{x0} = |0><0| and rho^v_{x1} = |1><1|; the SPECIFIED ensemble is
rho_{x0} = |+><+| = [[1/2, 1/2], [1/2, 1/2]] and rho_{x1} = |1><1|. The link
supplies as data the completely dephasing channel in the declared basis,
Xi(rho) = diag(rho_00, rho_11).
  Xi(rho^v_{x0}) = Xi(|0><0|) = diag(1, 0) = |0><0| ,
  and rho_{x0} = |+><+| = [[1/2, 1/2], [1/2, 1/2]] .
  THEY DIFFER IN ALL FOUR ENTRIES: 1 against 1/2 at (0,0), 0 against 1/2 at
  (0,1) and (1,0), 0 against 1/2 at (1,1). (S3) FAILS at x0.
  At x1 the identity does hold: Xi(|1><1|) = |1><1| = rho_{x1}. ONE INDEX IS
  ENOUGH TO REFUSE, the condition being universally quantified over x.
A PASSING COMPANION, so that the check is two-sided on data: with the same
virtual ensemble, the SPECIFIED ensemble rho_{x0} = |1><1|, rho_{x1} = |0><0|
and Xi the bit-flip unitary channel Xi(rho) = X rho X, both identities hold --
X|0><0|X = |1><1| and X|1><1|X = |0><0| -- and (S3) HOLDS. Every matrix in both
branches is Gaussian-rational.
WHAT IS AND IS NOT CLAIMED, Theorem thm:chain-consumption (iv): the compiler "checks this
identity AND NOTHING BEYOND IT". That security of the virtual protocol transfers
to the real one is Assumption ass:link, a supplier obligation this contract
never verifies and never asserts.""",
    ),
    ChainCase(
        case_id="CHAIN-not-decided-C4-S3",
        source_segment=(
            ChainLink(
                link_id="Xi_1",
                segment="source",
                link_type="source map (theorem constructor, NO channel data)",
                source_descriptor="A'' (a qubit)",
                target_descriptor="A' (a qubit)",
                status="certified_outer",
                channel_supplied=False,
                transported_constraints=("O^_1 transported by this link",),
                license_slot_present=True,
                license_slot_empty=False,
            ),
        ),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment="receiver",
                link_type="squashing (theorem constructor, NO channel data)",
                source_descriptor="C^3 (physical receiver space)",
                target_descriptor="(Q, (s0), (2))",
                status="exploratory_numeric",
                channel_supplied=False,
                transported_constraints=(),
                license_slot_present=True,
                license_slot_empty=False,
            ),
        ),
        l_s=1,
        l_r=1,
        physical_alphabet=("w0", "w1", "w2"),
        emitted_alphabet=("v0", "v1"),
        gamma=(("w0", "v0"), ("w1", "v1"), ("w2", "v1")),
        verdicts=(
            ("C1", "holds"),
            ("C2", "holds"),
            ("C3", "holds"),
            ("C4", "not checked"),
            ("C5", "holds"),
            ("S1", "holds"),
            ("S2", "holds"),
            ("S3", "not checked"),
            ("S4", "holds"),
            ("X1", "holds"),
        ),
        failing_condition=None,
        named_assumption="A-LINK",
        refuses=False,
        arithmetic="""\
THE CASE WHERE (C4) AND (S3) ARE NOT DECIDED, AND A-LINK IS NAMED. THIS IS THE
ONE CASE IN THE GROUP THAT MUST NOT BE RECORDED AS `passed'.
BOTH conditions are conditional on the data: (C4) reads "IF EVERY LINK OF R_rec
SUPPLIES ITS CHANNEL AS DATA then, with Lambda = Lambda_L o ... o Lambda_1,
Eq. eq:pullback holds", and adds "Where some link supplies only A THEOREM
CONSTRUCTOR AND NO CHANNEL, the identity is NOT DECIDABLE FROM THE EMITTED DATA
and is carried instead as the supplier obligation Assumption ass:link". (S3)
carries the same clause, "writing Xi for the composite WHEN EVERY LINK SUPPLIES
ITS CHANNEL AS DATA".
HERE NEITHER LINK SUPPLIES A CHANNEL, so both composites are undefined and
neither identity has an evaluable left-hand side. THE RECORD SAYS `not checked'
AND NAMES A-LINK. It does NOT say `passed', and it does not refuse: the chain is
admissible, and the obligation is transferred, not discharged.
THE EIGHT CONDITIONS THAT ARE STILL DECIDED, so that "not checked" is confined
to exactly two: (C1) and (S1) compare declared descriptors -- available whether
or not a channel is; (C2) counts preimages in a tabulated table -- gamma is the
proper coarse-graining of CHAIN-coarse-proper, total and surjective with the
two-element fibre gamma^{-1}(v1); (C3) is check V3 restricted to the emitted
{F_v}, evaluated ON THE EMITTED MATRICES THEMSELVES and not inferred from the
physical family (Theorem thm:chain-consumption (ii): "a chain that merely CLAIMS a block
structure cannot smuggle one past the check"); (S2) compares index sets and
weights; (C5) and (S4) check the PRESENCE of fields, and both links here carry a
NON-EMPTY licence slot and the source link a non-empty constraint slot, which
(C5)/(S4) record and do not evaluate.
THE STATUS TAGS ARE `certified_outer' AND `exploratory_numeric', the other two
values of the Section 2.2 vocabulary. NOTHING IN THE CONTRACT READS THEM: no
theorem, no gate and no output row. They are carried through, and an
implementation that let a status decide a verdict would be inventing a rule.
WHAT THE TRANSPORTED ENTRY MEANS HERE. Assumption ass:link's second clause --
"every reachable state after the reduction satisfies every constraint entry the
link transports" -- is a supplier obligation, and the entry itself is still
subject to V3 and V6 on the emitted data. A SOURCE-SEGMENT ENTRY IS THE HARD
CASE: its descriptors are Alice-side while every emitted constraint operator
must be Hermitian and sector-block-diagonal ON Q, so such an entry is refused by
V3 or V6 rather than transformed. See V6-constraint-typing in Group PC-E; the
reading is recorded and no rule is added.""",
    ),
)


O_PC_CHAIN = PCOracleEntry(
    oracle_id="O-PC-CHAIN",
    claims=("PC7", "PC8"),
    kind="structural-identity",
    subject=(
        "Definition def:chaincond (C1)-(C5), (S1)-(S4), (X1) and Theorem "
        "thm:chain-consumption: the Band-A chain record field for field; a proper "
        "coarse-graining with Eq. eq:pullback and Eq. eq:pullbackstats on named "
        "matrices; the Remark rem:coarse wrong-direction refusal; wrong-segment "
        "links in both directions; descriptor mismatches in each segment; an "
        "(S2) and an Eq. eq:srcmap failure; and the case where (C4) and (S3) "
        "are NOT DECIDED and Assumption A-LINK is named."
    ),
    derivation="""\
contract.tex 0.1.4 Definition def:chaincond, Eq. eq:pullback,
Eq. eq:pullbackstats, Eq. eq:srcmap, Theorem thm:chain-consumption (i)-(v) and Step 3 of its proof, Remark rem:coarse,
Remark req:chain-record-slots, Definition def:bandA, Theorem thm:band-a and Assumption
ass:link.

THE RECORD IS A PAIR OF SEGMENTS, AND THAT IS THE SAFETY RULE. Design decision 3
of Section 1.1: a source map acts on the TRANSMITTED system and a squashing map
on the RECEIVER system, "these are different types, and a single list of links
cannot carry both". So R = (R_src, R_rec) with L_s >= 0 and L >= 1, composed
source segment first, and the composition-order rule is a property of the
record's SHAPE. Theorem thm:chain-consumption (i) draws the consequence that must not be
blurred: (C1)-(C5) and (S1)-(S4) are DECIDED by finite enumeration and finitely
many arithmetic operations, while (X1) IS NOT DECIDED, "because it is not a
condition on data: it is the type of the record".

WHAT IS DECIDED, AND WITH WHAT WORK (thm:chain-consumption (i)):
  (C1), (S1)  compare finitely many declared descriptors;
  (C2)        enumerates a finite table and checks totality and surjectivity by
              COUNTING PREIMAGES;
  (C3)        is check V3 restricted to {F_v}, on the EMITTED matrices;
  (C4)        evaluates |V| matrix identities, the adjoint of a channel given as
              data being computable by finitely many operations, each right-hand
              side a finite sum over the tabulated fibre;
  (S2)        compares two finite index sets and |X| declared weights;
  (S3)        evaluates |X| matrix identities;
  (C5), (S4)  check the PRESENCE of fields.
EVERY ONE OF THOSE IS EXERCISED BY A FROZEN CASE, and each failure case names
exactly one condition, so that a refusal points where the contract says it
points -- "refused WITH THAT CONDITION NAMED".

THE DIRECTION OF (C2) IS FORCED, NOT CHOSEN, and Theorem thm:chain-consumption (iii),
Step 3 of its proof, proves it by an integer argument that the frozen wrong-direction case instantiates: summing
the reversed pullback over v and using unitality forces
sum_w (|gamma'^{-1}(w)| - 1) F^ph_w = 0, hence F^ph_w = 0 at every over-covered
outcome. The only surviving non-injective correspondence has null extra
outcomes, i.e. no coarse-graining at all.

WHAT IS NAMED AND NEVER DISCHARGED (thm:chain-consumption (v)). That each link is a SOUND
reduction, that a theorem-constructor link's channel exists as claimed, that
every reachable state after the reduction satisfies every transported entry, and
that any restricted attack set is licensed -- Assumptions ass:link and ass:lic,
obligations of `proof-reductions'. NO CLAIM OF THIS CONTRACT HOLDS THEM AND NONE
DEPENDS ON THEM. CHAIN-not-decided-C4-S3 is the case that makes the boundary
visible in DATA: two conditions recorded as `not checked' with A-LINK named,
never as `passed'.

BAND A IS THE WHOLE OF SLICE 1'S CHAIN. CHAIN-bandA is Theorem thm:band-a (ii)
worked condition by condition, and the record it freezes -- an empty source
segment, one identity link, both slots present and empty, status `exact', gamma
the identity bijection -- is what the first vertical slice consumes. Remark
req:chain-record-slots is why the empty slots are frozen as PRESENT.
""",
    hypotheses=(
        "Theorem thm:chain-consumption is stated for a chain PRESENTED with the interface "
        "conditions; the failure cases are presentations that violate one of "
        "them, which is what the checks exist to catch.",
        "The four verdict words used in this group are the registry's "
        "descriptive labels, not a contract report vocabulary. The contract "
        "fixes report tokens for `gate_report` only.",
        "Assumption A-LINK and Assumption A-RECV are supplier obligations this "
        "module names and NEVER verifies; nothing frozen here asserts either.",
    ),
)


# ===========================================================================
#  Group PC-G -- the emission gates (PC9): the EXHAUSTIVE enumeration
# ===========================================================================
#
#  THIS IS THE BAND'S TOP-RISK ITEM. The claim being frozen is not that some
#  cases behave as stated but that THE CASE SPACE IS COVERED: every point of the
#  seven-axis product is either ruled out by a NAMED consistency rule derived
#  from the contract, or matched by EXACTLY ONE case. The integrity test proves
#  both halves by iterating all 2 x 2 x 2 x 3 x 2 x 2 x 2 = 192 points.
#
#  THE SEVEN AXES, and what each ranges over.

GATE_AXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("validator", ("pass", "fail")),
    ("request", ("trusted", "untrusted")),
    ("alice_dim", ("1", ">=2")),
    ("certificate", ("absent", "present_passing", "present_failing")),
    ("m", ("0", ">=1")),
    ("list", ("licensed", "unlicensed")),
    ("license", ("present", "absent")),
)


@dataclass(frozen=True)
class GateConsistencyRule:
    """A product point excluded because the contract makes it impossible."""

    rule_id: str
    #: A point is EXCLUDED when its value on every named axis is in the tuple.
    pattern: tuple[tuple[str, tuple[str, ...]], ...]
    reason: str
    locator: str


GATE_CONSISTENCY_RULES: tuple[GateConsistencyRule, ...] = (
    GateConsistencyRule(
        rule_id="CR1",
        pattern=(("m", ("0",)), ("list", ("unlicensed",))),
        reason=(
            "The EMPTY LIST lies in the licensed class VACUOUSLY, its condition "
            "being an empty conjunction, so `m = 0 and unlicensed' is not a "
            "state of affairs the contract admits. Applies at BOTH validator "
            "values: it is a fact about the empty conjunction and not about any "
            "emitted declaration."
        ),
        locator="proof of Theorem thm:gates (i); Definition def:homog",
    ),
    GateConsistencyRule(
        rule_id="CR2",
        pattern=(
            ("request", ("untrusted",)),
            ("certificate", ("present_passing", "present_failing")),
        ),
        reason=(
            "A source-replacement certificate is TRUSTED MODE ONLY, so an "
            "untrusted request cannot carry one. Applies at both validator "
            "values: it is an input-typing fact."
        ),
        locator=(
            "Section 2.2, `source_replacement_certificate` domain cell "
            "('trusted mode only'); Definition def:spec (a), last sentence "
            "('In untrusted mode there is no certificate and no marginal')"
        ),
    ),
    GateConsistencyRule(
        rule_id="CR3a",
        pattern=(
            ("validator", ("pass",)),
            ("request", ("untrusted",)),
            ("m", (">=1",)),
            ("list", ("unlicensed",)),
        ),
        reason=(
            "In UNTRUSTED-source mode the entry type is already scalar by "
            "D(vi), so gate (G3)(a) degenerates into a type check that a "
            "well-formed declaration passes BY CONSTRUCTION. With V6 passed "
            "there is no unlicensed list to have. Conditional on the validator "
            "passing, because the degeneration argument runs through D(vi)."
        ),
        locator="Remark rem:degenerate, second vacuous case; Definition def:homog (b)",
    ),
    GateConsistencyRule(
        rule_id="CR3b",
        pattern=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", ("1",)),
            ("certificate", ("absent", "present_passing")),
            ("m", (">=1",)),
            ("list", ("unlicensed",)),
        ),
        reason=(
            "At d_A = 1 every 1x1 Hermitian Theta_k equals Theta_k . tau_A with "
            "tau_A = [1], SO NO DECLARATION CAN FAIL (G3)(a). Restricted to the "
            "certificates that reach an EMISSION -- absent or present-passing "
            "-- because a present-but-failing certificate is refused and no "
            "emitted mode exists against which `licensed' would be evaluated."
        ),
        locator="Remark rem:degenerate, first vacuous case; Definition def:compile",
    ),
    GateConsistencyRule(
        rule_id="CR3c",
        pattern=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", (">=2",)),
            ("certificate", ("absent",)),
            ("m", (">=1",)),
            ("list", ("licensed",)),
        ),
        reason=(
            "On a trusted-mode request at d_A >= 2 whose certificate is ABSENT "
            "there is NO tau_A at all -- tau_A reaches the emitted data only "
            "through the certificate -- so the test Theta_k = c_k tau_A has no "
            "right-hand side to be run against and NO LIST WITH m >= 1 CAN LIE "
            "IN THE LICENSED CLASS. The list axis is forced to `unlicensed'."
        ),
        locator=(
            "Theorem thm:gates (i), last two sentences and their proof; "
            "Table tab:gateoutcome, row 4"
        ),
    ),
)


@dataclass(frozen=True)
class GateCase:
    """One reachable region of the case space and the outcome it maps to."""

    case_id: str
    #: The axis values this case admits; the case matches a point iff the
    #: point's value lies in the tuple on EVERY axis.
    axes: tuple[tuple[str, tuple[str, ...]], ...]
    #: "refusal" or "emission".
    outcome: str
    #: The source mode of the EMITTED declaration, or None on a refusal.
    emitted_mode: str | None
    #: The value of the key_length_eligible flag, or None on a refusal.
    key_length_eligible: bool | None
    #: True only on the Table tab:gateoutcome row 2 fallback.
    fallback_recorded: bool
    #: Whether `source_replacement_license` is emitted (Section 2.3).
    emits_source_replacement_license: bool
    #: Per gate: (gate, engaged, verdict). `engaged` is None where the contract
    #: determines no engagement -- on a refusal there is no emitted declaration
    #: to gate -- and `verdict` is None wherever the contract fixes no token.
    #: NO FOURTH TOKEN IS EVER WRITTEN: see GATE_VERDICT_VOCABULARY.
    gates: tuple[tuple[str, bool | None, str | None], ...]
    #: What a refusal names, in the contract's own identifiers; None otherwise.
    named_check: str | None
    #: The clause or table row this outcome derives from.
    derives_from: str
    arithmetic: str


GATE_CASES: tuple[GateCase, ...] = (
    GateCase(
        case_id="G-VALIDATOR-FAIL",
        axes=(
            ("validator", ("fail",)),
            ("request", ("trusted", "untrusted")),
            ("alice_dim", ("1", ">=2")),
            ("certificate", ("absent", "present_passing", "present_failing")),
            ("m", ("0", ">=1")),
            ("list", ("licensed", "unlicensed")),
            ("license", ("present", "absent")),
        ),
        outcome="refusal",
        emitted_mode=None,
        key_length_eligible=None,
        fallback_recorded=False,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "failed"),
            ("G2", None, None),
            ("G3a", None, None),
            ("G3b", None, None),
        ),
        named_check="the failed check among V1-V8",
        derives_from="Table tab:gateoutcome, row 1",
        arithmetic="""\
(G1) DOMINATES EVERY OTHER AXIS. Row 1 of Table tab:gateoutcome: "(G1): any of
V1-V8 -> `refusal', NAMING THE CHECK", with the reason "THERE IS NO DECLARATION
TO EMIT: the candidate is not well-formed, or -- at V7 -- has not been shown to
be. NOTHING DOWNSTREAM MAY CONSUME IT, AT ANY TIER."
So this case admits every value of the other six axes, subject only to CR1 and
CR2, which are input-side facts and hold whatever the validator does. It covers
48 of the 96 validator-fail points; the other 48 are excluded by CR1 or CR2.
WHY (G2), (G3)(a) AND (G3)(b) CARRY NO VERDICT HERE, and why none is invented.
Definition def:eligible opens "AN EMITTED DECLARATION is key-length-eligible
when ...", so all three remaining gates are conditions ON AN EMITTED
DECLARATION. There is none. The contract states no gate_report content for a
refused compilation, so `engaged` is None and `verdict` is None -- NOT a fourth
token such as `not evaluated', which would be inventing vocabulary in a place
Section 2.3 fixes exactly three values. The container shape of gate_report on a
refusal is recorded in interface.yaml as open implementation choice 2 of 8.
WHAT IS NOT IN DOUBT: no declaration is emitted, and the refusal names the
failed check among V1-V8 -- the IDENTITY of the check, not a spelling.""",
    ),
    GateCase(
        case_id="G-U-M0",
        axes=(
            ("validator", ("pass",)),
            ("request", ("untrusted",)),
            ("alice_dim", ("1", ">=2")),
            ("certificate", ("absent",)),
            ("m", ("0",)),
            ("list", ("licensed",)),
            ("license", ("present", "absent")),
        ),
        outcome="emission",
        emitted_mode="untrusted",
        key_length_eligible=True,
        fallback_recorded=False,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "passed"),
            ("G2", False, None),
            ("G3a", False, None),
            ("G3b", False, None),
        ),
        named_check=None,
        derives_from="Definition def:eligible (G1)-(G3); Definition def:compile",
        arithmetic="""\
THE SIMPLEST EMISSION. An untrusted request with an empty constraint list.
  EMITTED MODE: untrusted. Definition def:compile fills the marginal slot with
  nomarg "otherwise", i.e. in every non-trusted case.
  (G1) PASSED, the validator having passed.
  (G2) NOT ENGAGED: its premise is "if the marginal slot is filled AND
  d_A >= 2", and the slot holds nomarg at every d_A. So the axis alice_dim is
  free here and both values map to this case.
  (G3) NOT ENGAGED: its premise is m >= 1.
  KEY_LENGTH_ELIGIBLE = TRUE. Definition def:eligible makes the flag true when
  all three hold, and a conditional with a false antecedent holds. Nothing else
  gates it.
  THE LICENSE AXIS IS FREE AND IRRELEVANT: (G3)(b) is a presence test demanded
  only at m >= 1, so an attack-set licence supplied at m = 0 changes no verdict
  and is carried through as a pass-through if supplied (Section 2.3,
  `attack_set_license`: "present only if supplied").
  `source_replacement_license' IS NOT EMITTED: the Outputs table emits it
  "exactly when TRUSTED mode is emitted at d_A >= 2".
WHY NO VERDICT TOKEN IS WRITTEN FOR AN UNENGAGED GATE. Theorem thm:band-a (iii)
uses the contract's own phrase, "the two-part gate of Theorem thm:gates is NOT
ENGAGED", and Section 2.3 fixes exactly three tokens for gate_report without
saying which one an unengaged gate carries. `engaged` is therefore False and
`verdict` is None. Recording the ENGAGEMENT is faithful; picking a token is not.""",
    ),
    GateCase(
        case_id="G-U-M1-LIC",
        axes=(
            ("validator", ("pass",)),
            ("request", ("untrusted",)),
            ("alice_dim", ("1", ">=2")),
            ("certificate", ("absent",)),
            ("m", (">=1",)),
            ("list", ("licensed",)),
            ("license", ("present",)),
        ),
        outcome="emission",
        emitted_mode="untrusted",
        key_length_eligible=True,
        fallback_recorded=False,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "passed"),
            ("G2", False, None),
            ("G3a", True, "passed vacuously"),
            ("G3b", True, "passed"),
        ),
        named_check=None,
        derives_from="Definition def:eligible (G3); Remark rem:degenerate",
        arithmetic="""\
THE FIRST OF THE TWO REMARK rem:degenerate VACUOUS PASSES. An untrusted emission
with a non-empty constraint list and the attack-set licence supplied.
  (G3) IS ENGAGED, m >= 1.
  (G3)(a) IS `passed vacuously' AND NOT `passed'. Remark rem:degenerate: "In
  UNTRUSTED-SOURCE MODE AT ANY d_A the entry type is already scalar by D(vi), so
  (G3)(a) DEGENERATES from a mathematical condition into a type check that a
  well-formed declaration passes by construction ... The compiler therefore
  emits PASSED VACUOUSLY rather than PASSED in gate_report, AND MUST NOT REPORT
  THE VACUOUS PASS AS EVIDENCE OF ANYTHING."
  THAT IS A REQUIREMENT ON THE REPORT, not a preference, and it is why the
  three-valued vocabulary exists at all. The remark's closing sentence is the
  reason: "A gate that reads as two independent checks and IS IN FACT ONE is
  exactly the kind of thing a later reader assumes is still load-bearing."
  (G3)(b) IS `passed': the attack_set_license record is PRESENT. Theorem
  thm:gates (iii): "Passing (G3)(b) RECORDS THAT AN ATTESTATION WAS SUPPLIED. It
  asserts nothing about attack-set inclusion, and no claim of this contract
  does." The whole gate here rests on (G3)(b), WHICH NO PROGRAM CAN VERIFY.
  KEY_LENGTH_ELIGIBLE = TRUE, all three gates holding.""",
    ),
    GateCase(
        case_id="G-U-M1-NOLIC",
        axes=(
            ("validator", ("pass",)),
            ("request", ("untrusted",)),
            ("alice_dim", ("1", ">=2")),
            ("certificate", ("absent",)),
            ("m", (">=1",)),
            ("list", ("licensed",)),
            ("license", ("absent",)),
        ),
        outcome="emission",
        emitted_mode="untrusted",
        key_length_eligible=False,
        fallback_recorded=False,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "passed"),
            ("G2", False, None),
            ("G3a", True, "passed vacuously"),
            ("G3b", True, "failed"),
        ),
        named_check=None,
        derives_from="Table tab:gateoutcome, row 6",
        arithmetic="""\
THE SAME DECLARATION WITH THE ATTESTATION MISSING. Row 6 of Table
tab:gateoutcome: "(G3)(b): attack_set_license ABSENT -> EMISSION WITH
KLE = false", with the reason "The compiler NEVER SUPPLIES THE MISSING
ATTESTATION AND NEVER PROCEEDS AS THOUGH IT HAD ONE".
  (G3)(a) is again `passed vacuously' -- the degeneration does not depend on the
  licence -- and (G3)(b) is `failed'.
  THE OUTCOME IS AN EMISSION, NOT A REFUSAL. Row 5's reason applies to row 6 by
  its own "As the row above": "The declaration is WELL-FORMED and may be
  EXPLORED NUMERICALLY; it is the KEY-LENGTH CLAIM, not the object, that is
  unsupported."
  KEY_LENGTH_ELIGIBLE = FALSE, and Section 2.3 states the consequence: such a
  declaration "MAY be used for numerical exploration AND MUST NOT REACH A
  KEY-LENGTH OUTPUT".
THE PAIR (G-U-M1-LIC, G-U-M1-NOLIC) IS THE WHOLE OF THE UNTRUSTED CONSTRAINT
GATE: one presence test, two outcomes, and the mechanical half vacuous in both.""",
    ),
    GateCase(
        case_id="G-T-D1-CERTFAIL",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", ("1",)),
            ("certificate", ("present_failing",)),
            ("m", ("0", ">=1")),
            ("list", ("licensed", "unlicensed")),
            ("license", ("present", "absent")),
        ),
        outcome="refusal",
        emitted_mode=None,
        key_length_eligible=None,
        fallback_recorded=False,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "passed"),
            ("G2", False, None),
            ("G3a", None, None),
            ("G3b", None, None),
        ),
        named_check="(SR1) or (SR2), whichever failed",
        derives_from=(
            "Definition def:compile, the d_A = 1 clause -- NOT a row of "
            "Table tab:gateoutcome"
        ),
        arithmetic="""\
THE ANSWER THAT IS NOT IN THE TABLE, AND THE REASON THIS CASE IS FROZEN
SEPARATELY. Table tab:gateoutcome's rows 2, 3 and 4 all carry the scope
"at d_A >= 2" -- row 3 acquired it in the 0.1.3 revision -- so the table is
SILENT on a present-but-failing certificate at d_A = 1. THE ANSWER IS IN
DEFINITION def:compile, which is the normative rule for that corner:
  "at d_A = 1, where Definition def:eligible (G2) does not demand a certificate,
   a trusted-mode request is served with tau_A = [1], the unique element of
   S_=(A) (Remark rem:dA1), UNLESS THAT REQUEST CARRIES A CERTIFICATE FAILING
   (SR1) OR (SR2), IN WHICH CASE IT IS REFUSED EXACTLY AS AT d_A >= 2
   (Table tab:gateoutcome, row 3) -- a certificate that does not verify is A
   DEFECT IN THE SUPPLIED DATA, NOT A WEAKER CLAIM."
AN IMPLEMENTATION MUST NOT IMPROVISE FROM THE TABLE'S SILENCE. Reading the table
alone one could conclude that at d_A = 1 a failing certificate is ignored,
because (G2) does not demand one there -- and that would silently accept
mis-specified source data. The contract closes the corner in place.
THE GATE VERDICTS. (G1) passed, the validator having passed. (G2) is NOT ENGAGED
-- its premise carries d_A >= 2 and Theorem thm:gates (i) says "(G2) DOES NOT
DEMAND A CERTIFICATE AT ALL" there -- so the refusal comes from the COMPILATION
MAP and not from a gate. (G3)(a) and (G3)(b) carry no verdict: no declaration is
emitted.
THE OTHER AXES ARE FREE. m, list and license are unevaluated because there is no
emitted declaration; CR1 still removes the (m = 0, unlicensed) points, leaving
six.""",
    ),
    GateCase(
        case_id="G-T-D1-M0",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", ("1",)),
            ("certificate", ("absent", "present_passing")),
            ("m", ("0",)),
            ("list", ("licensed",)),
            ("license", ("present", "absent")),
        ),
        outcome="emission",
        emitted_mode="trusted",
        key_length_eligible=True,
        fallback_recorded=False,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "passed"),
            ("G2", False, None),
            ("G3a", False, None),
            ("G3b", False, None),
        ),
        named_check=None,
        derives_from="Definition def:compile, the d_A = 1 clause; Remark rem:dA1",
        arithmetic="""\
THE d_A = 1 TRUSTED EMISSION, with an empty list.
  THE MARGINAL SLOT HOLDS tau_A = [1]. Definition def:compile fills it so, and
  Theorem thm:gates (i) argues in place that this is NOT a default substituted for
  a missing datum -- which Section 2.5 (`fail_closed`) would forbid -- "because
  S_=(A) = {[1]} IS A SINGLETON, so D(ii) admits that value AND NO OTHER, and
  because by Remark rem:dA1 the resulting feasible set is the UNTRUSTED one, so
  THE FILLED SLOT EXCLUDES NOTHING".
  (G2) NOT ENGAGED, premise d_A >= 2. Remark rem:dA1 states the obligation
  positively: "the compiler MUST NOT DEMAND the attestation there, and (G2) is
  stated with the hypothesis d_A >= 2 for exactly that reason".
  `source_replacement_license' IS NOT EMITTED: "Vacuous at d_A = 1 and then NOT
  EMITTED AND NOT DEMANDED" (Section 2.3).
  (G3) NOT ENGAGED, m = 0. KEY_LENGTH_ELIGIBLE = TRUE.
THE CERTIFICATE AXIS IS FREE OVER (absent, present_passing) AND THE TWO MERGE.
With the certificate absent, def:compile supplies tau_A = [1]; with a
present-passing certificate, (SR1) says tau_A = tr_{A''}|Psi><Psi|, which at
d_A = 1 is the 1x1 partial trace of a unit vector and is therefore [1] as well.
SAME MARGINAL, SAME GATES, SAME EMITTED LICENCE (none). The merge is recorded
rather than assumed, because it is the one place where a passing certificate
changes nothing at all.""",
    ),
    GateCase(
        case_id="G-T-D1-M1-LIC",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", ("1",)),
            ("certificate", ("absent", "present_passing")),
            ("m", (">=1",)),
            ("list", ("licensed",)),
            ("license", ("present",)),
        ),
        outcome="emission",
        emitted_mode="trusted",
        key_length_eligible=True,
        fallback_recorded=False,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "passed"),
            ("G2", False, None),
            ("G3a", True, "passed vacuously"),
            ("G3b", True, "passed"),
        ),
        named_check=None,
        derives_from="Remark rem:degenerate, first vacuous case",
        arithmetic="""\
THE SECOND REMARK rem:degenerate VACUOUS PASS, and the one that is easiest to
mistake for a real check.
  (G3)(a) IS `passed vacuously'. Remark rem:degenerate: "At d_A = 1 every 1x1
  Hermitian Theta_k equals Theta_k . tau_A with tau_A = [1], SO NO DECLARATION
  CAN FAIL IT." The licensed class of Definition def:homog (a) is the whole
  space of admissible entries there, so the mechanical half of the gate carries
  no information whatsoever.
  CONTRAST WITH d_A >= 2, which the same remark states: "Gate (G3)(a) is a
  GENUINE RESTRICTION in trusted-source mode at d_A >= 2: the real multiples of
  tau_A are a ONE-DIMENSIONAL SUBSPACE of the d_A^2-dimensional real space of
  Hermitian operators on A, and a declaration CAN fail it." That is case
  G-T-D2-CERT-M1-UNLIC-* below.
  (G3)(b) IS `passed': the licence record is present. IN BOTH VACUOUS CASES "the
  gate rests ENTIRELY on (G3)(b), which no program can verify."
  KEY_LENGTH_ELIGIBLE = TRUE.
THE DEGENERATION RECORD. Section 2.3 says gate_report carries, per gate,
"passed / failed / PASSED VACUOUSLY, WITH THE DEGENERATION RECORD OF Remark
rem:degenerate WHERE IT APPLIES". The record is REQUIRED here; its SHAPE is not
fixed and is recorded in interface.yaml as open implementation choice 2 of 8.""",
    ),
    GateCase(
        case_id="G-T-D1-M1-NOLIC",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", ("1",)),
            ("certificate", ("absent", "present_passing")),
            ("m", (">=1",)),
            ("list", ("licensed",)),
            ("license", ("absent",)),
        ),
        outcome="emission",
        emitted_mode="trusted",
        key_length_eligible=False,
        fallback_recorded=False,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "passed"),
            ("G2", False, None),
            ("G3a", True, "passed vacuously"),
            ("G3b", True, "failed"),
        ),
        named_check=None,
        derives_from="Table tab:gateoutcome, row 6",
        arithmetic="""\
THE d_A = 1 MIRROR OF G-U-M1-NOLIC. The mechanical half is vacuously true, the
attestation is absent, so (G3)(b) fails and row 6 gives EMISSION WITH
KLE = false.
THE COMBINATION IS THE MOST MISLEADING IN THE WHOLE ENUMERATION, and is frozen
for that reason: a gate_report that read
  (G1) passed, (G2) not engaged, (G3)(a) passed, (G3)(b) failed
would suggest three of four checks in hand and one attestation outstanding. The
truth is that (G2) is vacuous at d_A = 1 (Remark rem:dA1), (G3)(a) is vacuous at
d_A = 1 (Remark rem:degenerate), and the ONLY substantive gate beyond the
validator is the one that failed. THE THIRD TOKEN IS WHAT KEEPS THAT VISIBLE,
which is exactly why the contract requires it and requires that a vacuous pass
"MUST NOT BE REPORTED AS EVIDENCE OF ANYTHING".""",
    ),
    GateCase(
        case_id="G-T-D2-CERT-M0",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", (">=2",)),
            ("certificate", ("present_passing",)),
            ("m", ("0",)),
            ("list", ("licensed",)),
            ("license", ("present", "absent")),
        ),
        outcome="emission",
        emitted_mode="trusted",
        key_length_eligible=True,
        fallback_recorded=False,
        emits_source_replacement_license=True,
        gates=(
            ("G1", True, "passed"),
            ("G2", True, "passed"),
            ("G3a", False, None),
            ("G3b", False, None),
        ),
        named_check=None,
        derives_from="Definition def:eligible (G1)-(G3)",
        arithmetic="""\
THE TRUSTED EMISSION THE BAND-A BB84 INSTANCE LANDS IN (Theorem thm:pc12 (iii)).
  (G2) IS ENGAGED -- the marginal slot is filled and d_A >= 2 -- and PASSES on
  its checkable half: the certificate is present and (SR1)-(SR2) verify, which
  Theorem thm:certificate-sufficiency (i) says are "finitely many matrix identities on the emitted
  data".
  WHAT REMAINS IS THE ATTESTATION (SR3), which is decided by NO function of the
  emitted data. Definition def:eligible (G2) names only (SR1)-(SR2) as the
  conditions that "verify"; (SR3) travels in the emitted
  `source_replacement_license' record as a PASS-THROUGH. Remark rem:boundary:
  what this module "may NEVER do is ASSERT (SR3) of a physical apparatus: IT
  RECORDS THE ATTESTATION IT WAS GIVEN."
  `source_replacement_license' IS EMITTED here and only here among the trusted
  cases -- "emitted exactly when trusted mode is emitted at d_A >= 2"
  (Section 2.3) -- which is why this case and G-T-D1-M0 differ in that field
  although both emit trusted mode.
  (G3) NOT ENGAGED at m = 0; KEY_LENGTH_ELIGIBLE = TRUE.
NOTE THAT KLE = TRUE HERE DOES NOT MEAN THE ATTESTATION WAS VERIFIED. It means
it was SUPPLIED. Assumption ass:ret's "If violated" cell states the cost: "A is
in fact accessible to the adversary although a tau_A was declared: the marginal
condition of Eq. eq:feas is UNSUPPORTED and the key length is OVERSTATED --
security break in the UNSAFE direction.""",
    ),
    GateCase(
        case_id="G-T-D2-CERT-M1-LIC-LICENCE",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", (">=2",)),
            ("certificate", ("present_passing",)),
            ("m", (">=1",)),
            ("list", ("licensed",)),
            ("license", ("present",)),
        ),
        outcome="emission",
        emitted_mode="trusted",
        key_length_eligible=True,
        fallback_recorded=False,
        emits_source_replacement_license=True,
        gates=(
            ("G1", True, "passed"),
            ("G2", True, "passed"),
            ("G3a", True, "passed"),
            ("G3b", True, "passed"),
        ),
        named_check=None,
        derives_from="Definition def:eligible (G3)(a)-(b); Definition def:homog (a)",
        arithmetic="""\
THE ONLY CASE IN THE WHOLE ENUMERATION IN WHICH (G3)(a) IS A GENUINE, NON-VACUOUS
`passed'. Trusted mode at d_A >= 2 with a verified certificate, a non-empty
list, the list IN the licensed class, and the attestation supplied.
  (G3)(a) IS `passed' AND NOT `passed vacuously'. Remark rem:degenerate: at
  d_A >= 2 in trusted mode "the real multiples of tau_A are a ONE-DIMENSIONAL
  SUBSPACE of the d_A^2-dimensional real space of Hermitian operators on A, and
  A DECLARATION CAN FAIL IT". At d_A = 2 that is a 1-dimensional subspace of a
  4-dimensional space.
  HOW IT IS DECIDED, Theorem thm:gates (i): "the condition Theta_k = c_k tau_A
  with c_k in R is decided by testing whether Theta_k is a REAL MULTIPLE of
  tau_A -- pick any index pair where tau_A is NON-ZERO, form the candidate
  ratio, and compare d_A^2 entries; IF tau_A HAS A ZERO ENTRY WHERE Theta_k DOES
  NOT, THE TEST FAILS." Finitely many exact comparisons, and the procedure is
  written to survive a SINGULAR tau_A.
  (G3)(b) `passed' on presence. KEY_LENGTH_ELIGIBLE = TRUE.
THE ENUMERATION'S OWN EVIDENCE FOR Remark rem:degenerate'S POINT, and the exact
form of it. A GENUINE (non-vacuous) (G3)(a) = `passed' occurs in exactly TWO of
the sixteen cases -- this one and G-T-D2-CERT-M1-LIC-NOLICENCE, which differ
ONLY in the licence axis, so the mechanical half carries information in exactly
ONE CORNER OF THE CASE SPACE: trusted mode, d_A >= 2, a verified certificate and
a non-empty list. Everywhere else (G3)(a) is `passed vacuously' (four cases),
`failed' (two cases), or not engaged. The integrity test asserts that partition.""",
    ),
    GateCase(
        case_id="G-T-D2-CERT-M1-LIC-NOLICENCE",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", (">=2",)),
            ("certificate", ("present_passing",)),
            ("m", (">=1",)),
            ("list", ("licensed",)),
            ("license", ("absent",)),
        ),
        outcome="emission",
        emitted_mode="trusted",
        key_length_eligible=False,
        fallback_recorded=False,
        emits_source_replacement_license=True,
        gates=(
            ("G1", True, "passed"),
            ("G2", True, "passed"),
            ("G3a", True, "passed"),
            ("G3b", True, "failed"),
        ),
        named_check=None,
        derives_from="Table tab:gateoutcome, row 6",
        arithmetic="""\
THE MECHANICAL HALF GENUINELY PASSES AND THE ATTESTATION IS MISSING. Row 6:
emission with KLE = false, and "The compiler NEVER SUPPLIES THE MISSING
ATTESTATION AND NEVER PROCEEDS AS THOUGH IT HAD ONE."
THIS IS THE PAIR THAT SHOWS (G3) IS TWO INDEPENDENT HALVES. Against
G-T-D2-CERT-M1-LIC-LICENCE the only axis that moves is `license', and the flag
flips. Against G-T-D2-CERT-M1-UNLIC-LICENCE the only axis that moves is `list',
and the flag flips for the other reason. The four combinations of (list,
license) at this corner are the four cases 9-12, and they are the only place in
the enumeration where both halves are non-vacuous and independent.
NO ENTRY IS DROPPED. Theorem thm:gates (ii): the compiler "NEVER DROPS A
CONSTRAINT ENTRY SILENTLY, never substitutes a default, and never synthesizes a
licence". The constraint list is emitted in full with KLE = false beside it.""",
    ),
    GateCase(
        case_id="G-T-D2-CERT-M1-UNLIC-LICENCE",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", (">=2",)),
            ("certificate", ("present_passing",)),
            ("m", (">=1",)),
            ("list", ("unlicensed",)),
            ("license", ("present",)),
        ),
        outcome="emission",
        emitted_mode="trusted",
        key_length_eligible=False,
        fallback_recorded=False,
        emits_source_replacement_license=True,
        gates=(
            ("G1", True, "passed"),
            ("G2", True, "passed"),
            ("G3a", True, "failed"),
            ("G3b", True, "passed"),
        ),
        named_check=None,
        derives_from="Table tab:gateoutcome, row 5",
        arithmetic="""\
THE MECHANICAL HALF FAILS WITH THE ATTESTATION IN HAND. Row 5: "(G3)(a): CList
NOT IN THE LICENSED CLASS -> EMISSION WITH KLE = false", reason: "The
declaration is WELL-FORMED and may be explored numerically; IT IS THE KEY-LENGTH
CLAIM, NOT THE OBJECT, THAT IS UNSUPPORTED."
A CONCRETE UNLICENSED ENTRY AT d_A = 2, so that `unlicensed' is not an abstract
label. Let tau_A = diag(3/4, 1/4) and Theta_1 = diag(1/2, 1/2) = 1_A/2. Is
Theta_1 a real multiple of tau_A? Following Theorem thm:gates (i): pick the index
pair (0,0), where tau_A is non-zero, and form the candidate ratio
c = (1/2)/(3/4) = 2/3. Compare all d_A^2 = 4 entries: at (1,1) the test needs
1/2 = (2/3)(1/4) = 1/6, and 1/2 != 1/6. THE TEST FAILS, exactly and in one
comparison. So the list is unlicensed and (G3)(a) is `failed'.
WHY THIS IS AN EMISSION AND NOT A REFUSAL, while the certificate-ABSENT case
with m >= 1 (G-T-D2-NOCERT-M1-REFUSE) is a refusal: here a tau_A EXISTS, so the
question "is Theta_k a multiple of it" has an answer and the answer is no --
which unsupports the key-length claim and nothing else. There a tau_A does not
exist, so the fallback of Proposition prop:conservative has no scalar to fall
back TO, and dropping the entry is forbidden.""",
    ),
    GateCase(
        case_id="G-T-D2-CERT-M1-UNLIC-NOLICENCE",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", (">=2",)),
            ("certificate", ("present_passing",)),
            ("m", (">=1",)),
            ("list", ("unlicensed",)),
            ("license", ("absent",)),
        ),
        outcome="emission",
        emitted_mode="trusted",
        key_length_eligible=False,
        fallback_recorded=False,
        emits_source_replacement_license=True,
        gates=(
            ("G1", True, "passed"),
            ("G2", True, "passed"),
            ("G3a", True, "failed"),
            ("G3b", True, "failed"),
        ),
        named_check=None,
        derives_from="Table tab:gateoutcome, rows 5 AND 6",
        arithmetic="""\
BOTH HALVES OF (G3) FAIL. Rows 5 and 6 prescribe the SAME outcome -- emission
with KLE = false -- so the case is unambiguous even though two rows select it.
IT IS FROZEN SEPARATELY FROM THE OTHER THREE (list, license) COMBINATIONS
BECAUSE THE gate_report DIFFERS, and the report is an output of this module
(Section 2.3). An enumeration that merged on the licence axis wherever the
outcome agreed would lose the distinction between "the mechanical half failed
and the attestation is in hand" and "neither is in hand", which is precisely the
diagnostic information a supplier needs to fix the declaration.
NOTE WHAT IS *NOT* DIFFERENT: `key_length_eligible' is False in both, and both
are emissions. Theorem thm:gates (ii) says the outcome "is FIXED by Table
tab:gateoutcome and IS NOT AN IMPLEMENTER'S CHOICE", so an implementation may
not escalate a double failure to a refusal.""",
    ),
    GateCase(
        case_id="G-T-D2-CERTFAIL",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", (">=2",)),
            ("certificate", ("present_failing",)),
            ("m", ("0", ">=1")),
            ("list", ("licensed", "unlicensed")),
            ("license", ("present", "absent")),
        ),
        outcome="refusal",
        emitted_mode=None,
        key_length_eligible=None,
        fallback_recorded=False,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "passed"),
            ("G2", True, "failed"),
            ("G3a", None, None),
            ("G3b", None, None),
        ),
        named_check="(SR1) or (SR2), whichever failed",
        derives_from="Table tab:gateoutcome, row 3",
        arithmetic="""\
A CERTIFICATE THAT DOES NOT VERIFY IS A DEFECT IN THE SUPPLIED DATA. Row 3:
"(G2): trusted mode requested at d_A >= 2, certificate PRESENT but (SR1) or
(SR2) fails -> `refusal', NAMING THE CONDITION", with the reason "A certificate
that does not verify is A DEFECT IN THE SUPPLIED DATA, NOT A WEAKER CLAIM;
SILENTLY DEMOTING IT WOULD HIDE A MIS-SPECIFIED SOURCE."
THE TEMPTING WRONG BEHAVIOUR IS EXACTLY THE ONE ROW 2 AUTHORIZES IN A DIFFERENT
CASE: falling back to untrusted mode. Proposition prop:conservative proves the
fallback safe when the attestation is ABSENT; it says nothing about one that is
present and false, and row 3 forbids the demotion. The distinction is the whole
reason rows 2 and 3 are separate rows.
THE NAMED CONDITION IS (SR1) OR (SR2) -- the IDENTITY of the failed condition,
which the row requires be named. NO SPELLING IS FROZEN: the contract fixes only
two refusal strings and neither is this one.
(G3)(a) AND (G3)(b) CARRY NO VERDICT: no declaration is emitted, so m, list and
license are unevaluated and all three axes are free here, CR1 aside. Six product
points.""",
    ),
    GateCase(
        case_id="G-T-D2-NOCERT-M0-FALLBACK",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", (">=2",)),
            ("certificate", ("absent",)),
            ("m", ("0",)),
            ("list", ("licensed",)),
            ("license", ("present", "absent")),
        ),
        outcome="emission",
        emitted_mode="untrusted",
        key_length_eligible=True,
        fallback_recorded=True,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "passed"),
            ("G2", True, "failed"),
            ("G3a", False, None),
            ("G3b", False, None),
        ),
        named_check=None,
        derives_from="Table tab:gateoutcome, row 2; Proposition prop:conservative",
        arithmetic="""\
THE ONE ROW THAT EMITS IN A DIFFERENT MODE THAN THE ONE REQUESTED, AND THE ONLY
CASE WITH `fallback_recorded' TRUE. Row 2: "(G2): trusted mode requested at
d_A >= 2, certificate ABSENT, and m = 0 -- equivalently, CList licensed or
empty: with no certificate there is no tau_A, so the licensed class of
Definition def:homog (a) is inhabited only by the empty list -> UNTRUSTED-MODE
EMISSION, KLE DECIDED BY THE REMAINING GATES, FALLBACK RECORDED IN gate_report."
READ THE TWO (G2) ENTRIES CAREFULLY; THIS IS THE SUBTLEST CELL IN THE
ENUMERATION. The row is INDEXED by a (G2) failure -- of the REQUEST, which asked
for trusted mode and supplied no certificate -- and that is what
`gates' records as (G2) `failed'. The declaration that is EMITTED is the
UNTRUSTED one, whose marginal slot holds nomarg, and for THAT declaration (G2)'s
premise is false. The row resolves the apparent tension in its own words: KLE is
"decided by THE REMAINING GATES". Here (G1) passed and (G3) is not engaged at
m = 0, so KEY_LENGTH_ELIGIBLE = TRUE.
AN IMPLEMENTATION THAT READ def:eligible LITERALLY AND SET KLE = FALSE BECAUSE
(G2) IS REPORTED FAILED WOULD BE STRICTLY CONSERVATIVE BUT WOULD CONTRADICT THE
ROW, which is normative under Theorem thm:gates (ii): the outcome "IS FIXED BY
TABLE tab:gateoutcome AND IS NOT AN IMPLEMENTER'S CHOICE".
WHY THE FALLBACK IS SAFE, and the exact form of the argument. Row 2's "Why that
one" cell: "Proposition prop:conservative applies, UNIFORMLY IN THE MARGINAL: at
m = 0 the emitted feasible set contains the trusted-mode feasible set of EVERY
tau_A in S_=(A) the request might have carried, SO THE CHANGE CAN ONLY LOSE
RATE." The pointwise instance is frozen in CONSERVATIVE_FALLBACK below.
`source_replacement_license' IS NOT EMITTED: the emitted mode is untrusted.
THE LICENSE AXIS IS FREE at m = 0, as in G-U-M0.""",
    ),
    GateCase(
        case_id="G-T-D2-NOCERT-M1-REFUSE",
        axes=(
            ("validator", ("pass",)),
            ("request", ("trusted",)),
            ("alice_dim", (">=2",)),
            ("certificate", ("absent",)),
            ("m", (">=1",)),
            ("list", ("unlicensed",)),
            ("license", ("present", "absent")),
        ),
        outcome="refusal",
        emitted_mode=None,
        key_length_eligible=None,
        fallback_recorded=False,
        emits_source_replacement_license=False,
        gates=(
            ("G1", True, "passed"),
            ("G2", True, "failed"),
            ("G3a", None, None),
            ("G3b", None, None),
        ),
        named_check="(G2) with the list unlicensed for want of a tau_A",
        derives_from="Table tab:gateoutcome, row 4; Theorem thm:gates (i)-(ii)",
        arithmetic="""\
THE SAME MISSING CERTIFICATE, WITH A NON-EMPTY LIST, AND THE OUTCOME FLIPS FROM
FALLBACK TO REFUSAL. Row 4: "(G2): trusted mode requested at d_A >= 2,
certificate absent, and m >= 1 -- i.e. CList UNLICENSED, by the same absence of
tau_A -> `refusal'", reason: "THE FALLBACK IS UNAVAILABLE: with Theta_k not of
the form c_k tau_A THERE IS NO UNTRUSTED ENTRY TO FALL BACK *TO*, AND DROPPING
THE ENTRY IS FORBIDDEN."
WHY THE LIST AXIS IS FORCED TO `unlicensed' HERE (rule CR3c). The proof of
Theorem thm:gates (i): "tau_A reaches the emitted data ONLY through the
certificate -- Definition def:compile fills the marginal slot from it in trusted
mode and with nomarg otherwise, and NO INPUT ROW OF SECTION 2.2 CARRIES A
MARGINAL SEPARATELY. So on a trusted-mode request presented WITHOUT a
certificate the test Theta_k = c_k tau_A of Definition def:homog (a) HAS NO
RIGHT-HAND SIDE TO BE RUN AGAINST, and no list with m >= 1 can lie in the
licensed class; the empty list lies in it vacuously."
THAT SENTENCE IS ALSO WHAT MAKES ROWS 2 AND 4 A PARTITION, and the proof says so
explicitly: "the two certificate-absent rows of Table tab:gateoutcome PARTITION
THE CASES BY m: row 2 is exactly m = 0, row 4 exactly m >= 1, AND NO CASE FALLS
BETWEEN THEM OR REQUIRES AN UNDECIDABLE TEST." The enumeration's totality at
this corner is therefore the contract's own argument, not an inference.
THE THIRD ALTERNATIVE THAT THE CONTRACT FORBIDS: emitting the untrusted
declaration with the entries dropped. Theorem thm:gates (ii): the compiler "NEVER
DROPS A CONSTRAINT ENTRY SILENTLY". Between "keep an entry you cannot type" and
"drop it", the contract chooses neither and refuses.""",
    ),
)


@dataclass(frozen=True)
class FeasibleSetComparison:
    """Two feasible sets and a named state that separates or joins them."""

    case_id: str
    alice_dim: int
    q_dim: int
    tau_a: Matrix | None
    #: (operator, relation, trusted rhs, untrusted rhs) for each entry.
    licensed_entries: tuple[tuple[Matrix, str, Matrix | None, F], ...]
    state_name: str
    state: Matrix
    #: The A-marginal of the state.
    state_marginal: Matrix
    in_trusted_set: bool
    in_untrusted_set: bool
    #: The trusted left-hand side tr_Q[(1_A (x) O^) omega], per entry.
    trusted_values: tuple[Matrix, ...]
    #: The untrusted left-hand side tr[(1_A (x) O^) omega], per entry.
    untrusted_values: tuple[F, ...]
    arithmetic: str


FEASIBLE_SET_COMPARISONS: tuple[FeasibleSetComparison, ...] = (
    FeasibleSetComparison(
        case_id="CONSERVATIVE-inside",
        alice_dim=2,
        q_dim=2,
        tau_a=real_matrix(((F(3, 4), 0), (0, F(1, 4)))),
        licensed_entries=(
            (
                P_Z0,
                "succeq",
                real_matrix(((F(3, 16), 0), (0, F(1, 16)))),
                F(1, 4),
            ),
        ),
        state_name="omega = tau_A (x) |0><0|",
        state=real_matrix(
            (
                (F(3, 4), 0, 0, 0),
                (0, 0, 0, 0),
                (0, 0, F(1, 4), 0),
                (0, 0, 0, 0),
            )
        ),
        state_marginal=real_matrix(((F(3, 4), 0), (0, F(1, 4)))),
        in_trusted_set=True,
        in_untrusted_set=True,
        trusted_values=(real_matrix(((F(3, 4), 0), (0, F(1, 4)))),),
        untrusted_values=(F(1),),
        arithmetic="""\
PROPOSITION prop:conservative POINTWISE, ON A NAMED LICENSED LIST.
THE DATA. d_A = 2, Q a qubit with one sector, tau_A = diag(3/4, 1/4) -- chosen
NOT maximally mixed, so that the marginal condition has content -- and the
one-entry LICENSED list of Definition def:homog (a):
  ( |0><0|_Q , succeq , c_1 tau_A )   with c_1 = 1/4 ,
so the trusted right-hand side is (1/4) diag(3/4, 1/4) = diag(3/16, 1/16), and
the untrusted declaration that prop:conservative constructs replaces it by the
SCALAR c_1 = 1/4, all other slots unchanged.
THE STATE. omega = tau_A (x) |0><0| = diag(3/4, 0, 1/4, 0) in the basis order
(00, 01, 10, 11) fixed by `subsystem_order`.
  POSITIVE: diagonal, entries >= 0.   TRACE: 3/4 + 1/4 = 1.
  SECTOR BLOCKS: vacuous at |S| = 1.
  MARGINAL: omega_A = diag(3/4 + 0, 1/4 + 0) = diag(3/4, 1/4) = tau_A.
  TRUSTED ENTRY: tr_Q[(1_A (x) |0><0|) omega] = tau_A . tr[|0><0| |0><0|]
  = tau_A = diag(3/4, 1/4). Is diag(3/4, 1/4) succeq diag(3/16, 1/16)? The
  difference is diag(3/4 - 3/16, 1/4 - 1/16) = diag(9/16, 3/16), whose
  eigenvalues 9/16 and 3/16 are both >= 0. YES.
  So omega is in W^tr.
THE PROOF'S STEP, INSTANTIATED. Taking traces of the Loewner inequality and
using that Y succeq Y' implies tr Y >= tr Y':
  tr[(1_A (x) |0><0|) omega] = tr( tr_Q[(1_A (x) |0><0|) omega] )
                             = tr diag(3/4, 1/4) = 1 ,
  and  tr(c_1 tau_A) = c_1 tr tau_A = c_1 = 1/4 , using tr tau_A = 1 from D(ii).
  1 >= 1/4 . THAT IS THE UNTRUSTED ENTRY WITH >=, so omega is in W^un.
Eq. eq:inclusion W^tr subset W^un HOLDS AT THIS POINT, and the direction of the
consequence is the one the proposition states: an infimum over a superset is not
larger, so the fallback LOWERS any minimized quantity. "IT CAN ONLY COST RATE;
IT CAN NEVER TURN AN UNSUPPORTED DECLARATION INTO A SUPPORTED-LOOKING ONE."
THE THREE RELATIONS. The proof does succeq first, notes that preceq is
"identical with the inequality reversed", and gets = by applying both. Frozen
here at succeq; the preceq instance is the same numbers with the relation and
the inequality both reversed, and the = instance is their conjunction.""",
    ),
    FeasibleSetComparison(
        case_id="CONSERVATIVE-strict",
        alice_dim=2,
        q_dim=2,
        tau_a=real_matrix(((F(3, 4), 0), (0, F(1, 4)))),
        licensed_entries=(
            (
                P_Z0,
                "succeq",
                real_matrix(((F(3, 16), 0), (0, F(1, 16)))),
                F(1, 4),
            ),
        ),
        state_name="omega' = |0><0|_A (x) |0><0|_Q",
        state=real_matrix(
            (
                (1, 0, 0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
            )
        ),
        state_marginal=P_Z0,
        in_trusted_set=False,
        in_untrusted_set=True,
        trusted_values=(real_matrix(((1, 0), (0, 0))),),
        untrusted_values=(F(1),),
        arithmetic="""\
THE SAME DECLARATION, A STATE IN W^un AND NOT IN W^tr: THE INCLUSION IS STRICT.
omega' = |0><0|_A (x) |0><0|_Q = diag(1, 0, 0, 0).
  POSITIVE, TRACE 1, SECTOR BLOCKS VACUOUS: all hold.
  UNTRUSTED ENTRY: tr[(1_A (x) |0><0|) omega'] = 1, and 1 >= 1/4. HOLDS. There
  is no marginal condition in untrusted mode, so omega' is in W^un.
  MARGINAL: omega'_A = diag(1, 0) = |0><0|, and |0><0| != tau_A = diag(3/4, 1/4)
  -- they differ in BOTH diagonal entries, 1 against 3/4 and 0 against 1/4. So
  omega' is NOT in W^tr.
STRICTNESS MATTERS FOR THE READING OF Eq. eq:inclusion. The fallback of row 2
does not merely re-label the same set: it ENLARGES it, admitting states the
trusted declaration excluded, and an infimum over the larger set is not larger.
THE PAIR (CONSERVATIVE-inside, CONSERVATIVE-strict) IS THE INCLUSION AND ITS
STRICTNESS ON ONE DECLARATION, both verified by exact arithmetic on four
diagonal entries.""",
    ),
    FeasibleSetComparison(
        case_id="NOTFALLBACK-anti-case",
        alice_dim=2,
        q_dim=2,
        tau_a=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        licensed_entries=(),
        state_name="omega'' = |0><0|_A (x) 1_Q/2",
        state=real_matrix(
            (
                (F(1, 2), 0, 0, 0),
                (0, F(1, 2), 0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
            )
        ),
        state_marginal=P_Z0,
        in_trusted_set=False,
        in_untrusted_set=True,
        trusted_values=(),
        untrusted_values=(),
        arithmetic="""\
REMARK rem:notfallback, AS AN ANTI-CASE: tau_A = 1_A/d_A IS NOT A NEUTRAL WAY TO
SAY "NOTHING IS KNOWN ABOUT THE SOURCE", AND THE COMPILER NEVER SUBSTITUTES IT.
THE COMPARISON. Take the empty constraint list and set the marginal slot two
ways: tau_A = 1_A/2 (trusted) against nomarg (untrusted). The witness is
  omega'' = |0><0|_A (x) 1_Q/2 = diag(1/2, 1/2, 0, 0) ,
a perfectly ordinary normalized, sector-block-diagonal state.
  IN W^un: positive, trace 1/2 + 1/2 = 1, no marginal condition, empty list. YES.
  IN W^tr AT tau_A = 1_A/2: omega''_A = diag(1/2 + 1/2, 0 + 0) = diag(1, 0)
  = |0><0|, and |0><0| != diag(1/2, 1/2). NO.
SO tau_A = 1_A/d_A EXCLUDES omega'' WHILE nomarg ADMITS IT: the substitution
"fixes the marginal to maximally mixed and EXCLUDES EVERY SOURCE THAT SENDS
ANYTHING ELSE, WHICH IS A STRICTLY STRONGER CLAIM THAN nomarg."
THE DIRECTION Proposition prop:conservative LICENSES IS THE OTHER ONE. It
"licenses DROPPING a marginal, NEVER ADDING OR WEAKENING ONE". Row 2 of the gate
table drops one; nothing in the contract adds one.
THIS SAME STATE IS THE NON-VACUITY WITNESS OF THEOREM thm:pc12 (iii), where it
shows that at d_A = 2 the BB84 marginal tau_A = 1_A/2 "DELETES STATES from
Eq. eq:feas and the attestation IS DOING WORK", in contrast with Remark rem:dA1
where it deletes none. One state, two uses, and they are the same computation
read in opposite directions.""",
    ),
)


@dataclass(frozen=True)
class DimensionOneEquality:
    """Remark rem:dA1: at d_A = 1 the two feasible sets coincide."""

    case_id: str
    q_dim: int
    tau_a: Matrix
    state_name: str
    state: Matrix
    #: The 1x1 A-marginal of the state, which IS its trace.
    marginal: Matrix
    trace: F
    marginal_equals_tau: bool
    trace_is_one: bool
    in_trusted_set: bool
    in_untrusted_set: bool
    arithmetic: str


DIMENSION_ONE_EQUALITIES: tuple[DimensionOneEquality, ...] = (
    DimensionOneEquality(
        case_id="DA1-normalized",
        q_dim=2,
        tau_a=real_matrix(((1,),)),
        state_name="omega = diag(1/3, 2/3) on Q, with A trivial",
        state=real_matrix(((F(1, 3), 0), (0, F(2, 3)))),
        marginal=real_matrix(((1,),)),
        trace=F(1),
        marginal_equals_tau=True,
        trace_is_one=True,
        in_trusted_set=True,
        in_untrusted_set=True,
        arithmetic="""\
REMARK rem:dA1, THE EQUALITY, ON A NORMALIZED STATE. At d_A = 1:
  S_=(A) = {[1]}, so the ONLY marginal a trusted declaration can carry is
  tau_A = [1] -- there is literally no other 1x1 positive matrix of trace one;
  and for omega in Pos(A Q) the A-marginal is the 1x1 matrix [tr omega].
  SO THE CONDITIONS omega_A = tau_A AND tr omega = 1 COINCIDE.
HERE omega = diag(1/3, 2/3) on Q (A being trivial, A Q is just Q):
  tr omega = 1/3 + 2/3 = 1 , and omega_A = [1] = tau_A .
Both conditions hold, and they hold FOR THE SAME REASON. By Definition
def:feasible the trusted-mode and untrusted-mode feasible sets are therefore
EQUAL, and "the two emissions are the same declaration".
THE CONSEQUENCE THE CONTRACT DRAWS: "The source-replacement certificate at
d_A = 1 licenses the condition tr omega = 1, WHICH EVERY NORMALIZED STATE
SATISFIES, so IT EXCLUDES NOTHING: the compiler MUST NOT DEMAND THE ATTESTATION
THERE, and (G2) is stated with the hypothesis d_A >= 2 for exactly that reason."
CONTRAST WITH NOTFALLBACK-anti-case AT d_A = 2, where the marginal deletes
states. The two cases are the same computation at two dimensions, and the
attestation is vacuous in one and load-bearing in the other.""",
    ),
    DimensionOneEquality(
        case_id="DA1-subnormalized",
        q_dim=2,
        tau_a=real_matrix(((1,),)),
        state_name="omega = diag(1/3, 1/3) on Q, with A trivial",
        state=real_matrix(((F(1, 3), 0), (0, F(1, 3)))),
        marginal=real_matrix(((F(2, 3),),)),
        trace=F(2, 3),
        marginal_equals_tau=False,
        trace_is_one=False,
        in_trusted_set=False,
        in_untrusted_set=False,
        arithmetic="""\
THE SAME EQUALITY SEEN FROM THE FAILING SIDE, so that it is an EQUIVALENCE and
not a one-way implication. omega = diag(1/3, 1/3) has
  tr omega = 1/3 + 1/3 = 2/3 != 1 , and omega_A = [2/3] != [1] = tau_A .
BOTH CONDITIONS FAIL, AND THEY FAIL TOGETHER, which is what "the conditions
coincide" means. omega is in neither feasible set.
THIS IS THE CASE THAT RULES OUT A PLAUSIBLE MISREADING: that at d_A = 1 the
trusted mode is the weaker of the two because its marginal is trivial. It is
neither weaker nor stronger; it is THE SAME SET, and a state fails both
conditions or neither.""",
    ),
)


O_PC_GATES = PCOracleEntry(
    oracle_id="O-PC-GATES",
    claims=("PC9",),
    kind="fail-closed",
    subject=(
        "Definition def:eligible, Theorem thm:gates and Table tab:gateoutcome: an "
        "EXHAUSTIVE enumeration of the reachable case space over seven axes -- "
        "mode request, d_A, certificate, m, list, licence, validator -- with "
        "five named consistency rules, each reachable point mapped to its "
        "outcome and its per-gate three-valued report, and the d_A = 1 "
        "present-but-failing-certificate answer taken from Definition "
        "def:compile because the table is deliberately silent there."
    ),
    derivation="""\
contract.tex 0.1.4 Definition def:eligible ((G1), (G2), (G3)(a)-(b)), Definition
def:homog, Definition def:compile, Theorem thm:gates (i)-(iii), Table
tab:gateoutcome (six rows), Remark rem:degenerate, Remark rem:dA1, Proposition
prop:conservative with Eq. eq:inclusion, and Remark rem:notfallback.

WHAT IS BEING CLAIMED. Not that the sixteen cases behave as stated -- each has
its own derivation -- but that TOGETHER THEY COVER THE CASE SPACE. The seven
axes have 2 x 2 x 2 x 3 x 2 x 2 x 2 = 192 points. Of these, 106 are excluded by
one of the five consistency rules CR1, CR2, CR3a, CR3b, CR3c, each of which is a
sentence of the contract turned into a pattern; the remaining 86 are matched by
EXACTLY ONE case. The integrity test proves both halves by iteration, and a
seventeenth case or a missing one would fail it.
THE COUNTS, so that a reader can check the bookkeeping:
  validator = fail : 96 points, 48 excluded (CR1 or CR2), 48 in
                     G-VALIDATOR-FAIL;
  validator = pass : 96 points, 48 excluded by CR1 or CR2 and 10 more by CR3a
                     (4), CR3b (4) and CR3c (2), leaving 38 across fifteen
                     cases: 4 + 2 + 2 + 6 + 4 + 2 + 2 + 2 + 1 + 1 + 1 + 1 + 6
                     + 2 + 2 = 38.
  86 matched + 106 excluded = 192.

THE THREE PERMITTED OUTCOMES AND NOTHING ELSE. Theorem thm:gates (ii): if any gate
fails, "which of the THREE PERMITTED OUTCOMES it produces -- refusal, emission
with key_length_eligible = false, or emission in the weaker source mode with the
fallback recorded -- IS FIXED BY TABLE tab:gateoutcome AND IS NOT AN
IMPLEMENTER'S CHOICE". Every frozen case carries one of the three, and exactly
one case carries the third: G-T-D2-NOCERT-M0-FALLBACK.

THE THREE-VALUED REPORT, AND THE DISCIPLINE ABOUT WHAT IS NOT WRITTEN. Section
2.2 fixes `passed`, `failed`, `passed vacuously` for gate_report, and Remark
rem:degenerate makes the third REQUIRED in its two cases. Where a gate is NOT
ENGAGED -- (G2) with the marginal slot empty or d_A = 1, (G3) at m = 0 -- the
contract states the ENGAGEMENT (Theorem thm:band-a (iii) uses the phrase "not
engaged") and fixes no token, so `verdict` is None. Where NO DECLARATION IS
EMITTED, the gates of Definition def:eligible have no subject at all and
`engaged` is None too. NO FOURTH TOKEN IS EVER WRITTEN.

WHERE (G3)(a) IS AND IS NOT INFORMATIVE, which the enumeration turns into a
countable fact. It is `passed vacuously` in four cases (both untrusted m >= 1
cases and both d_A = 1 m >= 1 cases), `failed` in two, and a GENUINE `passed` in
exactly ONE -- G-T-D2-CERT-M1-LIC-LICENCE. Remark rem:degenerate's warning is
therefore literally true of the case space: outside one corner "the gate rests
ENTIRELY on (G3)(b), WHICH NO PROGRAM CAN VERIFY".

THE CORNER THE TABLE DOES NOT COVER. Rows 2, 3 and 4 all carry the scope
"at d_A >= 2". A present-but-failing certificate at d_A = 1 is therefore not in
the table, and the answer is in Definition def:compile: REFUSED, "exactly as at
d_A >= 2 ... a certificate that does not verify is a defect in the supplied
data, not a weaker claim". G-T-D1-CERTFAIL is that clause, and its
`derives_from` field says in as many words that it is NOT a table row -- because
improvising from the table's silence would silently accept mis-specified source
data.

WHAT IS DECIDABLE AND WHAT IS NOT (Theorem thm:gates (i)). (G1) by thm:validator-soundness;
(SR1)-(SR2) by thm:certificate-sufficiency (i); (G3)(a) by an entrywise comparison over d_A^2
entries, written to survive a singular tau_A; (G3)(b) by a presence test. AND
NOT: "(G2)'s clause (SR3) and (G3)(b)'s record are ATTESTATIONS and are NOT
DECIDABLE: THE COMPILER TESTS PRESENCE, NEVER TRUTH." No frozen case anywhere in
this registry records a verdict on (SR3) or on the attack-set licence's CONTENT.
""",
    hypotheses=(
        "Definition def:eligible's gates are conditions on an EMITTED "
        "declaration, which is why every refusal case leaves (G3) without a "
        "verdict rather than assigning one.",
        "The consistency rules CR3a, CR3b and CR3c are conditional on the "
        "validator passing, because each runs through a target condition -- "
        "D(vi) for CR3a, D(ii) and the emitted marginal for CR3b and CR3c.",
        "Assumption A-LIC is a supplier obligation this module names and never "
        "verifies; passing (G3)(b) records that an attestation was supplied and "
        "asserts nothing about attack-set inclusion.",
    ),
)


O_PC_CONSERVATIVE = PCOracleEntry(
    oracle_id="O-PC-CONSERVATIVE",
    claims=("PC9",),
    kind="structural-identity",
    subject=(
        "Proposition prop:conservative with Eq. eq:inclusion, Remark "
        "rem:notfallback and Remark rem:dA1: the inclusion W^tr subset W^un "
        "verified pointwise on a named licensed list, its STRICTNESS on the "
        "same declaration, the anti-case showing that 1_A/d_A is never "
        "substituted, and the d_A = 1 equality in both directions."
    ),
    derivation="""\
contract.tex 0.1.4 Proposition prop:conservative and its proof, Eq. eq:inclusion,
Remark rem:notfallback, Remark rem:dA1, Definition def:feasible and Definition
def:homog.

THE PROPOSITION, AND EXACTLY WHAT IT COMPARES. A specification requests trusted
mode with marginal tau_A and a LICENSED list {(O^_k, bowtie_k, c_k tau_A)}; the
untrusted declaration is obtained by replacing the marginal slot with nomarg AND
EACH RIGHT-HAND SIDE c_k tau_A BY THE SCALAR c_k, all other slots unchanged.
Then W^tr subset W^un, and consequently for ANY functional J on Pos(A Q),
inf over W^un of J <= inf over W^tr of J.
THE HYPOTHESIS THAT THE LIST BE LICENSED IS NOT DECORATIVE. Theorem thm:gates's
proof: where it fails -- "a trusted-mode request with an UNLICENSED list and no
attestation -- the untrusted declaration obtained by replacing each Theta_k by a
scalar is NOT a relaxation of the trusted one, SINCE THERE IS NO SCALAR THE
ENTRY NAMES, so the inclusion Eq. eq:inclusion is UNAVAILABLE and the row reads
refusal". That is gate-table row 4 and case G-T-D2-NOCERT-M1-REFUSE.

THE POINTWISE VERIFICATION, on tau_A = diag(3/4, 1/4) and c_1 = 1/4, is
CONSERVATIVE-inside: the trusted Loewner condition
diag(3/4, 1/4) succeq diag(3/16, 1/16) holds with difference diag(9/16, 3/16),
and taking traces gives the untrusted condition 1 >= 1/4. Both by exact
arithmetic on four entries.
THE STRICTNESS is CONSERVATIVE-strict: |0><0|_A (x) |0><0|_Q lies in W^un and
not in W^tr, so the inclusion is proper and the fallback genuinely enlarges the
set. THE DIRECTION IS THE SAFE ONE, and the proposition says why in the
sharpest available form: "the fallback LOWERS any minimized quantity, so IT CAN
ONLY COST RATE; IT CAN NEVER TURN AN UNSUPPORTED DECLARATION INTO A
SUPPORTED-LOOKING ONE."

THE ANTI-CASE, which is the mirror image and the one an implementation is most
likely to get wrong. Remark rem:notfallback: prop:conservative "licenses
DROPPING a marginal, NEVER ADDING OR WEAKENING ONE. In particular
tau_A = 1_A/d_A is NOT a neutral way to say 'nothing is known about the source':
it fixes the marginal to maximally mixed and EXCLUDES EVERY SOURCE THAT SENDS
ANYTHING ELSE, which is a STRICTLY STRONGER CLAIM than nomarg. THE COMPILER
NEVER SUBSTITUTES IT." NOTFALLBACK-anti-case exhibits the excluded state.

THE d_A = 1 EQUALITY, in both directions. Remark rem:dA1: S_=(A) = {[1]}, the
A-marginal of omega is the 1x1 matrix [tr omega], so omega_A = tau_A and
tr omega = 1 COINCIDE and the two feasible sets are EQUAL. DA1-normalized has
both conditions holding, DA1-subnormalized has both failing -- frozen as a PAIR,
because an equivalence tested only where it holds is not tested.
""",
    hypotheses=(
        "Proposition prop:conservative requires the list to be LICENSED in the "
        "sense of Definition def:homog (a); the inclusion is unavailable "
        "otherwise, and the gate table refuses there.",
        "The trace step uses tr tau_A = 1 from D(ii), and the implication "
        "Y succeq Y' => tr Y >= tr Y' via the non-negativity of the trace of a "
        "positive semidefinite operator applied to Y - Y'.",
    ),
)


# ===========================================================================
#  Group PC-K -- the interface vocabulary, as frozen tuples
# ===========================================================================

#: The TWELVE input machine keys of Section 2.2, in the table's order (six rows
#: in the first tabular, six in the second).
INPUT_KEYS: tuple[str, ...] = (
    "source_mode_request",
    "alice_system",
    "alice_povm_spec",
    "source_replacement_certificate",
    "receiver_povm",
    "public_choices",
    "reduction_chain",
    "target_sectors",
    "public_structure",
    "constraint_entries",
    "attack_set_license",
    "feasibility_witness",
)

#: The TWENTY-ONE output machine keys of Section 2.3, in the table's order: the
#: fifteen DECLARATION SLOTS first, then the six COMPILER-ONLY keys.
OUTPUT_KEYS: tuple[str, ...] = (
    "alice_dim",
    "alice_marginal",
    "source_replacement_license",
    "party_partition",
    "sector_index_set",
    "sector_dims",
    "alice_povm",
    "bob_povm",
    "announce_alice",
    "announce_bob",
    "accept_statistic",
    "key_map",
    "key_holder",
    "constraint_list",
    "attack_set_license",
    "acceptance_alphabet",
    "label_index_map",
    "reduction_chain_record",
    "key_length_eligible",
    "gate_report",
    "refusal",
)

#: The SIX compiler-only keys -- the second tabular of Section 2.3. None of them
#: is a slot of Eq. eq:declaration and none appears in the consuming engine's
#: wire Declaration.
COMPILER_ONLY_KEYS: tuple[str, ...] = (
    "acceptance_alphabet",
    "label_index_map",
    "reduction_chain_record",
    "key_length_eligible",
    "gate_report",
    "refusal",
)

#: The FIFTEEN declaration slots, which coincide VERBATIM with the fields of the
#: consuming engine's wire Declaration minus `acceptance_set` and `rounds`.
DECLARATION_SLOT_KEYS: tuple[str, ...] = tuple(
    key for key in OUTPUT_KEYS if key not in COMPILER_ONLY_KEYS
)

#: The two inputs of the consuming engine that are NOT outputs of this module,
#: with their owners, as Section 2.3's preamble names them.
NOT_OUTPUTS: tuple[tuple[str, str], ...] = (
    ("acceptance_set", "statistics-acceptance"),
    ("rounds", "a run parameter; no module emits it"),
)

#: The nine alphabets Definition def:compile indexes through idx, in its order.
INDEXED_ALPHABETS: tuple[str, ...] = (
    "X",
    "V",
    "S",
    "O_A",
    "O_B",
    "C_A",
    "C_B",
    "Chat",
    "Z_perp",
)


O_PC_VOCABULARY = PCOracleEntry(
    oracle_id="O-PC-VOCABULARY",
    claims=("PC1", "PC9"),
    kind="structural-identity",
    subject=(
        "Sections 2.1, 2.2 and 2.5: the machine-key vocabulary as frozen "
        "tuples -- twelve input keys, twenty-one output keys, which fifteen "
        "coincide verbatim with the consuming engine's wire Declaration, which "
        "six are compiler-only, that `acceptance_set` and `rounds` are NOT "
        "outputs of this module, the three-valued gate vocabulary, and the "
        "exactly two verbatim refusal strings."
    ),
    derivation="""\
contract.tex 0.1.4 Section 2.2 (Inputs), Section 2.3 (Outputs) and Section 2.5
(Conventions), transcribed key by key.

TWELVE INPUT KEYS. The Inputs section is split across two tabulars for page fit,
six rows then six, and its preamble says "MACHINE KEYS ARE BINDING FOR
interface.yaml". The twelve are frozen in INPUT_KEYS in the table's order. THERE
IS NO THIRTEENTH, and in particular there is NO test-statistics-model selector --
see O-PC-FIXED-FRACTION-REFUSAL and the change-request note below.

TWENTY-ONE OUTPUT KEYS, again in two tabulars: FIFTEEN declaration slots then
SIX compiler-only keys. The preamble draws the boundary: "The declaration slots
below are emitted under exactly the machine keys the consuming engine reads. TWO
of that engine's inputs are NOT outputs of this module and are listed as such:
`acceptance_set` is owned by `statistics-acceptance`, and `rounds` is a run
parameter."
NOTE THAT TWO ROWS CARRY TWO KEYS EACH -- "sector_index_set, sector_dims" and
"announce_alice, announce_bob" -- so the first tabular has THIRTEEN ROWS AND
FIFTEEN KEYS. Counting rows instead of keys is the transcription error this
tuple exists to prevent.

THE COINCIDENCE WITH THE CONSUMING WIRE FORMAT, checked against the existing
manifest and asserted by the integrity test. The operator-bundle Declaration
carries seventeen fields; removing `acceptance_set` and `rounds` -- which the
contract names as NOT outputs of this module -- leaves exactly the fifteen
declaration slots, name for name. THAT COINCIDENCE IS A FACT ABOUT NAMES AND NOT
A CLAIM OF THIS CONTRACT: the closing paragraph of Section 2.1 (`sec:target`)
calls the agreement with the consuming engine "the diff a HUMAN runs at G3", and
lists SIX interface
points at which the restated conditions must agree. The registry checks the
names; the mathematics is agreed at G3.
NO BUNDLE-SCHEMA EXTENSION IS AUTHORIZED BY THIS BAND for the six compiler-only
keys: the wire Declaration carries none of them, and adding a field to a frozen
wire format is a band-entry human decision, not an implementation one.

THE THREE-VALUED GATE VOCABULARY, from the Section 2.3 `gate_report` row: "per
gate: PASSED / FAILED / PASSED VACUOUSLY, with the degeneration record of Remark
rem:degenerate where it applies". Three tokens, frozen in
GATE_VERDICT_VOCABULARY, and Group PC-G writes no fourth one anywhere.

THE EXACTLY TWO VERBATIM REFUSAL STRINGS, frozen in REFUSAL_REASONS_VERBATIM:
`fixed_fraction_requested` (Theorem thm:choice-encoding (iv); Section 2.5, bullet 3) and
`no_feasibility_witness` (Theorem thm:feasibility (ii); Remark rem:completeness). FOR
EVERY OTHER REFUSAL the contract fixes the OBLIGATION and the IDENTITY of the
named check and NOT a spelling -- Section 2.3 ("a machine-readable reason NAMING
THE FAILED CHECK"), Section 2.5 `fail_closed`, Table tab:gateoutcome rows 1 and
3 ("naming the check", "naming the condition"), Theorem thm:chain-consumption (i) ("refused
WITH THAT CONDITION NAMED"). The nameable identifiers are V1-V8, (C1)-(C5),
(S1)-(S4), (G1)-(G3) with (G3)(a)/(G3)(b), and (SR1)/(SR2). NO REGISTRY ENTRY
FREEZES A THIRD STRING.

THE NINE INDEXED ALPHABETS of Definition def:compile, in its order, frozen in
INDEXED_ALPHABETS and instantiated in Group PC-A. WHICH bijection idx uses is
code's choice; that there are nine, each onto an INITIAL SEGMENT, each with its
inverse emitted, is the contract's.

THE THREE LINK STATUS TAGS, frozen in LINK_STATUS_VOCABULARY from the Section
2.1 `reduction_chain` row: exact, certified_outer, exploratory_numeric. NO
THEOREM, GATE OR OUTPUT ROW OF THE CONTRACT READS A STATUS, so an implementation
carries it through and must not let it decide anything.
""",
    hypotheses=(
        "The coincidence of the fifteen declaration-slot names with the wire "
        "Declaration is checked against the existing manifest module and is a "
        "fact about NAMES; the mathematical agreement is the human G3 diff of "
        "Section 2.1 (`sec:target`)'s six interface points.",
    ),
)


# ===========================================================================
#  Group PC-L -- the assumption ledger and the never-verified set
# ===========================================================================


@dataclass(frozen=True)
class LedgerRow:
    """One row of the Section 5 assumption ledger."""

    assumption_id: str
    machine_key: str
    #: The claims the Supports column names, transcribed and NOT widened.
    supports: tuple[str, ...]
    supplier: str | None
    never_verified: bool
    band_a_only: bool
    note: str


LEDGER_ROWS: tuple[LedgerRow, ...] = (
    LedgerRow(
        assumption_id="A-SPEC",
        machine_key="specification_valid",
        supports=(
            "PC1",
            "PC2",
            "PC3",
            "PC4",
            "PC5",
            "PC6",
            "PC7",
            "PC8",
            "PC9",
            "PC11",
            "PC12",
        ),
        supplier=None,
        never_verified=False,
        band_a_only=False,
        note=(
            "The Supports cell reads `PC1--PC9, PC11, PC12', i.e. ELEVEN of the "
            "twelve claims and NOT PC10, which is a quoted import. Every "
            "violation decidable from the emitted data is caught by V1-V8 and "
            "REFUSED; an invisible one propagates a declaration that "
            "misdescribes the apparatus -- a security break in the unsafe "
            "direction. The G3 signature records as judgement call (c) that "
            "A-SPEC's hypothesis does not cover the d_A = 1 emission Definition "
            "def:compile adds, safe via thm:validator-soundness (i)'s independent route."
        ),
    ),
    LedgerRow(
        assumption_id="A-SEQ",
        machine_key="sequential_round_model",
        supports=("PC1", "PC11", "PC12"),
        supplier=None,
        never_verified=False,
        band_a_only=False,
        note=(
            "Preparation and transmission, then measurement by both parties, "
            "then public announcements, then announcement-determined sifting. "
            "It is Fact fact:sr's hypothesis and Theorem thm:certificate-sufficiency (iii)'s, and "
            "it is what makes Remark rem:xreg's register restriction cost "
            "nothing: the announcements come AFTER both measurements."
        ),
    ),
    LedgerRow(
        assumption_id="A-RHOM",
        machine_key="round_homogeneity",
        supports=("PC1", "PC11", "PC12"),
        supplier=None,
        never_verified=False,
        band_a_only=False,
        note=(
            "One declaration describes every round. Section 2.5 states the "
            "behaviour: a specification whose rounds differ is REFUSED, NOT "
            "AVERAGED. Violation is a rate loss or an inapplicability, NOT a "
            "silent break."
        ),
    ),
    LedgerRow(
        assumption_id="A-ENS",
        machine_key="source_ensemble",
        supports=("PC11", "PC12"),
        supplier=None,
        never_verified=False,
        band_a_only=False,
        note=(
            "The Supports cell reads `PC11, PC12 (trusted mode)'. A "
            "DEVICE-CHARACTERIZATION statement about the sender, not verified "
            "here. Its violation is the case where (SR2) holds for the DECLARED "
            "DATA and not for the DEVICE -- unsafe direction."
        ),
    ),
    LedgerRow(
        assumption_id="A-RET",
        machine_key="source_replacement_license",
        supports=("PC11", "PC12"),
        supplier=None,
        never_verified=True,
        band_a_only=False,
        note=(
            "The Supports cell reads `PC11, PC12; gate (G2)'. This is (SR3), "
            "and it is in the NEVER-VERIFIED set for a different reason from "
            "the three supplier obligations: it is the attestation THIS module "
            "CARRIES, and Theorem thm:certificate-sufficiency (i) says it 'is decided by no "
            "function of the emitted data'. Remark rem:boundary forbids "
            "asserting it of an apparatus. VACUOUS at d_A = 1."
        ),
    ),
    LedgerRow(
        assumption_id="A-COIN",
        machine_key="public_choice_weights",
        supports=("PC3", "PC12"),
        supplier=None,
        never_verified=False,
        band_a_only=False,
        note=(
            "Public choices are private coins of declared bias, independent of "
            "the quantum systems, of the other party's choice and of the "
            "adversary. Remark rem:exactness: this is where the physical "
            "content sits, and NO ENCODING REPAIRS ITS VIOLATION."
        ),
    ),
    LedgerRow(
        assumption_id="A-LINK",
        machine_key="reduction_chain_sound",
        supports=("PC7", "PC8"),
        supplier="proof-reductions",
        never_verified=True,
        band_a_only=False,
        note=(
            "The Supports cell reads `PC7, PC8 (first clause discharged by "
            "exhibition there)'. SUPPLIER OBLIGATION. The contract checks "
            "Eq. eq:pullback and Eq. eq:srcmap WHERE THE DATA MAKE THEM "
            "CHECKABLE -- necessary conditions, NOT the obligation -- and "
            "records `not checked' naming A-LINK where they do not "
            "(CHAIN-not-decided-C4-S3)."
        ),
    ),
    LedgerRow(
        assumption_id="A-LIC",
        machine_key="attack_set_license",
        supports=("PC9",),
        supplier="proof-reductions",
        never_verified=True,
        band_a_only=False,
        note=(
            "The Supports cell reads `PC9, gate (G3)(b)'. SUPPLIER OBLIGATION. "
            "The compiler tests PRESENCE, NEVER TRUTH (Theorem thm:gates (i)), "
            "and passing (G3)(b) 'asserts nothing about attack-set inclusion, "
            "and no claim of this contract does' (thm:gates (iii)). NOT ENGAGED "
            "when CList is empty."
        ),
    ),
    # THE ONE KEY STRING OF THIS REGISTRY THAT MOVED, AND IT MOVED BY DECISION
    # ("A-RECV: one machine key"). It was
    # "receiver_povm_characterized"; it is now the owner's key, the one
    # reductions/ass:recv and reductions' own ledger give, so that a run
    # manifest reading both ledgers carries A-RECV under one key. The id, the
    # supports, the supplier, the flags and the note are unchanged.
    LedgerRow(
        assumption_id="A-RECV",
        machine_key="receiver_artifact_accepted",
        supports=("PC7",),
        supplier="receiver-povm",
        never_verified=True,
        band_a_only=False,
        note=(
            "SUPPLIER OBLIGATION, and the only one with nothing at all to "
            "check: the physical receiver POVM presented is the measurement the "
            "receiver performs. REPLACED BY A-IDEAL IN BAND A, where there is "
            "no characterization step."
        ),
    ),
    LedgerRow(
        assumption_id="A-IDEAL",
        machine_key="ideal_qubit_receiver",
        supports=("PC8", "PC12"),
        supplier=None,
        never_verified=False,
        band_a_only=True,
        note=(
            "BAND A ONLY. Unit detection efficiency, no dark counts, no loss, "
            "no multi-photon events, no misalignment, and a transmitted system "
            "that is exactly a qubit. AN IDEALIZATION, NOT A REDUCTION: 'no "
            "squashing argument is made and none is needed, because nothing "
            "infinite-dimensional is being reduced.'"
        ),
    ),
)

#: The four things NO CODE PATH OF THIS MODULE MAY DECIDE. Three are supplier
#: obligations the module names and never verifies; the fourth is the
#: attestation it carries, which is decided by no function of the emitted data.
NEVER_VERIFIED: tuple[str, ...] = ("A-LINK", "A-LIC", "A-RECV", "A-RET")


O_PC_LEDGER = PCOracleEntry(
    oracle_id="O-PC-LEDGER",
    claims=("PC7", "PC8", "PC9", "PC11"),
    kind="fail-closed",
    subject=(
        "The Section 5 assumption ledger: the ten assumption IDs with their "
        "machine keys and their Supports map, transcribed and not widened; and "
        "the NEVER-VERIFIED set {A-LINK, A-LIC, A-RECV, A-RET/(SR3)}, so that a "
        "test can assert no code path decides any of them."
    ),
    derivation="""\
contract.tex 0.1.4 Section 5, its preamble and its two tabulars, plus Theorem
thm:gates (i) and (iii), Theorem thm:certificate-sufficiency (i), Remark rem:boundary and Assumption
ass:link's closing sentence.

TEN ROWS AND NO MORE. A-SPEC, A-SEQ, A-RHOM, A-ENS, A-RET in the first tabular;
A-COIN, A-LINK, A-LIC, A-RECV, A-IDEAL in the second. The Supports column is
transcribed CLAIM BY CLAIM and is not widened anywhere. Two transcription facts
worth naming because they look like omissions and are not:
  NO ROW NAMES PC10. A-SPEC reads "PC1--PC9, PC11, PC12" and the others name
  subsets of {PC1, PC3, PC7, PC8, PC9, PC11, PC12}. PC10 IS A QUOTED IMPORT --
  Fact fact:sr -- whose own hypotheses are named in the symbol-map paragraph of
  Section 4.10 (A-ENS for the device, A-SEQ for the structure) rather than in
  the ledger. Recording both facts and widening neither is what a transcription
  does.
  THREE ROWS CARRY A PARENTHETICAL NARROWING inside the Supports cell -- A-ENS
  "(trusted mode)", A-RET "; gate (G2)", A-LINK "(first clause discharged by
  exhibition there)" -- and each is preserved in the row's note rather than
  being flattened away.

THE NEVER-VERIFIED SET, AND WHY IT HAS FOUR MEMBERS AND NOT THREE. The section
preamble names THREE supplier obligations "that this module NAMES AND NEVER
VERIFIES": A-LINK, A-LIC, A-RECV. The fourth, A-RET, is not another module's
obligation -- it is "the attestation THIS MODULE ITSELF CARRIES into the artifact
and which the consuming engine imports as its source-replacement licence" -- but
it is equally undecidable here: Theorem thm:certificate-sufficiency (i) says (SR3) "is a statement
about the apparatus, not about matrices; NO MATRIX FUNCTION DECIDES IT", and
Remark rem:boundary says what this module "may NEVER do is ASSERT (SR3) of a
physical apparatus: IT RECORDS THE ATTESTATION IT WAS GIVEN."
SO THE CONFORMING BEHAVIOUR, PER MEMBER:
  A-RET, A-LIC : PRESENCE TEST AND PASS-THROUGH. Theorem thm:gates (i): "the
                 compiler TESTS PRESENCE, NEVER TRUTH."
  A-LINK       : check the NECESSARY conditions Eq. eq:pullback and
                 Eq. eq:srcmap where the data make them checkable, and record
                 `not checked' NAMING A-LINK where they do not. Assumption
                 ass:link: the checks "are NECESSARY CONDITIONS AND NOT THE
                 OBLIGATION".
  A-RECV       : nothing to check at all; the obligation is only named.
AND THE NEGATIVE FORM, which is what the integrity test can assert: NO FROZEN
CASE ANYWHERE IN THIS REGISTRY RECORDS A VERDICT ON (SR3), ON THE CONTENT OF AN
ATTACK-SET LICENCE, ON THE SOUNDNESS OF A REDUCTION LINK, OR ON WHETHER A
PRESENTED RECEIVER POVM IS THE MEASUREMENT PERFORMED. Every gate case records
PRESENCE; every chain case records `not checked' where the data run out.

WHAT VIOLATION COSTS, IN THE LEDGER'S OWN DIRECTIONS. Six rows say "security
break in the UNSAFE direction" -- A-SPEC (invisible violations only), A-ENS,
A-RET, A-COIN, A-LINK, A-LIC, A-RECV, A-IDEAL -- and two do not: A-RHOM is
"rate loss or inapplicability, NOT a silent break", and A-SPEC's decidable half
is "a REFUSAL, not a bad declaration". THAT ASYMMETRY IS THE POINT OF THE
LEDGER: the assumptions this module can check, it checks and refuses on; the
ones it cannot, it names.
""",
    hypotheses=(
        "The Supports map is transcribed from the ledger and is NOT the set of "
        "assumptions a claim's proof uses; where the two could differ -- PC10 "
        "most visibly -- the ledger is what this registry freezes.",
    ),
)


# ===========================================================================
#  0.3.0 -- THE EXACT NUMBER MODEL, THE DECLARED TAG, AND THE OPERATOR Psi
#
#  AUTHORED BY RUN A OF THE B3 IMPLEMENTATION BAND, UNDER THE TWO-INSTANCE
#  FREEZE, BEFORE ANY IMPLEMENTATION
#  OF WHAT THEY PIN EXISTS. `src/certiqs_key/protocol_compiler/` was written
#  against the 0.1.3 text and does not implement 0.3.0; run B, a different implementer
#  instance, writes that code against these values and MAY READ BUT NOT MODIFY
#  THEM. An expected value that turns out to be wrong is a FINDING, reported
#  and corrected deliberately with its derivation, never edited in passing to
#  make a test green.
#
#  DERIVED FROM  contract.tex 0.3.0, sha256 (LF)
#                f1441567c99618859890151c990d4e7e47c6cfad42fa385bd0ce3b8835dbe65d
#                -- the RELEASED blob (STATUS.yaml
#                gates.g3.released_blob_sha256_lf), 5674 lines. The blob the
#                signature was written against is 7ad386f3..., which differs in
#                the one line \ContractVersion 0.3.0-draft -> 0.3.0.
#
#  WHAT THIS GROUP PINS, AND WHY IT IS A GROUP AND NOT A REVISION. 0.3.0
#  changes what the compiler DECIDES and what it EMITS, in seven places that no
#  0.1.4-era value covers:
#      (a) condition (S) -- a declared-order sum ROUNDING NOWHERE -- which can
#          refuse a family every one of whose entries is exactly representable
#          and whose COMPUTED completeness sum is exactly the identity;
#      (b) the `homogeneous`/`general` TAG, read off the right-hand side's TYPE;
#      (c) the certificate OPERATOR Psi, replacing a declared vector, with the
#          five conditions gate (G2) decides;
#      (d) V1's sector-map comparison, scoped to the two declaration slots that
#          carry a Q-operator, and V7 branch (c)'s separate comparison of a
#          supplied witness's map;
#      (e) the ONE emission obligation this module carries, on q_t N_{u|t};
#      (f) the binding rule that fixes idx from a supplier's declared order,
#          and the `sector_block_kind` key;
#      (g) the gate-outcome cells over (mode, m, certificate), including
#          d_A = 1 with a present-but-failing certificate.
#
#  EXACTNESS IS RESTORED, NOT INTRODUCED. This registry has frozen exact
#  rationals since 0.1.3, on the ground that "EXACTNESS IS THE FAITHFUL READING
#  of 'finitely many arithmetic operations'" (the module docstring's four lines
#  of rationale). 0.2.0 made that reading wrong by adding a tolerance; 0.3.0
#  makes it right again and states it in the contract rather than leaving it to
#  a registry's judgement. NO 0.1.4-ERA NUMBER IS RE-DERIVED BELOW, and the
#  entries whose statements 0.3.0 restores are listed in `RESTORED_AT_0_3_0`.
#
#  THE ARITHMETIC WAS DONE TWICE, BY ROUTES SHARING NO STEP: once from the
#  binary64 mantissa/exponent decomposition using integer arithmetic on
#  (mantissa, exponent) pairs, and once with `fractions.Fraction`, which never
#  sees a mantissa. Both routes are recorded in each `arithmetic` field and
#  they agreed at every value.
# ===========================================================================


#: fl(0.9) and fl(0.1) as EXACT dyadic rationals, with the mantissa/exponent
#: decomposition the contract writes (Theorem thm:pc12 (ii)). Reduced to lowest
#: terms, which is how the contract writes them; ``math.frexp`` returns an
#: unreduced mantissa in [2**52, 2**53) and a reader comparing the two must
#: reduce first.
FL_NINE_TENTHS: F = F(8106479329266893, 2**53)
FL_ONE_TENTH: F = F(3602879701896397, 2**55)

#: Their EXACT sum, which is 1 + 2**-55 and is therefore NOT 1 -- while the
#: binary64 addition of the two returns exactly 1, the successor of 1 being
#: 1 + 2**-52 and 2**-55 lying below half that step. This one number is the
#: whole reason condition (S) is in Definition def:exact.
FL_NINE_TENTHS_PLUS_ONE_TENTH: F = F(36028797018963969, 2**55)


@dataclass(frozen=True)
class SummationCase:
    """One declared-order summation, decided for (C) and for (S) separately.

    The point of the pair of fields ``computed_sum_is_identity`` and
    ``sum_rounds_nowhere`` is that they can DISAGREE, and that a presentation
    on which they disagree is refused. Definition ``def:exact``: "(C) alone
    says that the COMPUTED sum is the identity, and NOT that sum_j a_j = 1
    holds OF THE DECLARED NUMBERS ... (S) is exactly what makes the two the
    same statement, and it is the reason A FAMILY WHOSE ENTRIES ARE ALL EXACTLY
    REPRESENTABLE MAY STILL BE REFUSED: the condition is on the ADDITIONS, not
    on the operands."
    """

    case_id: str
    #: The family being summed, named by its emitted machine key.
    family: str
    #: The declared weights, exactly.
    weights: tuple[tuple[str, F], ...]
    #: Every emitted entry is a binary64 number -- decided before (S).
    every_entry_is_binary64: bool
    #: The sum of the DECLARED NUMBERS, exactly, as a multiple of the identity.
    exact_total_multiple_of_identity: F
    #: (C) read on the COMPUTED binary64 total.
    computed_sum_is_identity: bool
    #: (S): every one of the |J| entrywise binary64 additions is exact.
    sum_rounds_nowhere: bool
    #: 1-based index in the declared order of the first element whose addition
    #: was inexact, or ``None`` where (S) holds.
    first_inexact_addition_index: int | None
    #: Every (element index, flat matrix entry index) at which an addition was
    #: inexact. The contract counts these: "a computed total of exactly 1_A
    #: THROUGH FOUR INEXACT ADDITIONS".
    inexact_addition_sites: tuple[tuple[int, int], ...]
    #: Emitted verbatim by the contract where the presentation is refused.
    refusal_reason: str | None
    arithmetic: str
    #: How Alice's family reaches the compiler. ``"public_choices"``: the
    #: declared weight list with its conditional families, which
    #: req:weight-list decides before any product is decided. ``"direct"``:
    #: the matrices themselves, the artefact's own ``alice_povm``, with no
    #: weight list for req:weight-list to decide. Added with the
    #: re-freeze of S-ALICE-DECIMAL-LITERALS (see O-PC-EXACT-SUMMATION's
    #: ``revalidation``); every case frozen before it is ``"public_choices"``.
    presentation: str = "public_choices"
    #: Where req:weight-list refuses: the 1-based addition of the declared
    #: weight list's declared-order accumulation that rounds first, which the
    #: refusal names. ``None`` where the list is not refused or does not
    #: round. Added with the same re-freeze.
    weight_list_first_inexact_addition: int | None = None


#: (a) The exact decisions on the BB84 instance's declared weight
#: presentations. Every family is a GENUINE POVM and every entry of each is a
#: binary64 number. The balanced family is admitted. The decimal-literal family
#: fails condition (S) alone on its completeness sum; presented through the
#: public-choice record it is refused first by req:weight-list on the weight
#: list it was built from, and presented directly it is refused by check V3's
#: (S) leg (re-frozen; O-PC-EXACT-SUMMATION's ``revalidation``).
SUMMATION_CASES: tuple[SummationCase, ...] = (
    SummationCase(
        case_id="S-ALICE-BALANCED",
        family="alice_povm",
        weights=(("p^A_Z", F(1, 2)), ("p^A_X", F(1, 2))),
        every_entry_is_binary64=True,
        exact_total_multiple_of_identity=F(1),
        computed_sum_is_identity=True,
        sum_rounds_nowhere=True,
        first_inexact_addition_index=None,
        inexact_addition_sites=(),
        refusal_reason=None,
        arithmetic="""\
THE BALANCED PRESENTATION, ADMITTED, AND WHY EVERY PARTIAL SUM IS ON THE
LATTICE. Theorem thm:pc12 (ii): condition (S) "holds at the balanced weights
p^A_Z = p^A_X = p^B_Z = p^B_X = 1/2, where EVERY PARTIAL SUM of
Eq. eq:declorder IS A MULTIPLE OF 1/4 and every addition forming it is exact".

The emitted family, in the declared order (Z,0), (Z,1), (X,0), (X,1), with the
conjugation the identity on this signal set (all four states have real
coefficients in the declared basis -- Remark rem:bb84checks, which is also why
this instance CANNOT test `conjugation_basis`):

  M_(Z,0) = 1/2 [[1,0],[0,0]]     = [[1/2, 0  ], [0  , 0  ]]
  M_(Z,1) = 1/2 [[0,0],[0,1]]     = [[0  , 0  ], [0  , 1/2]]
  M_(X,0) = 1/2 [[1/2,1/2],[1/2,1/2]]  = [[1/4, 1/4], [1/4, 1/4]]
  M_(X,1) = 1/2 [[1/2,-1/2],[-1/2,1/2]] = [[1/4,-1/4], [-1/4,1/4]]

Partial sums of Eq. eq:declorder, entrywise, left to right:
  Sigma_1 = [[1/2, 0  ], [0  , 0  ]]
  Sigma_2 = [[1/2, 0  ], [0  , 1/2]]
  Sigma_3 = [[3/4, 1/4], [1/4, 3/4]]
  Sigma_4 = [[1  , 0  ], [0  , 1  ]] = 1_A

ROUTE 1 (mantissa/exponent). Every entry of every partial sum is an integer
multiple of 2**-2 of modulus at most 1, so its numerator over 2**-2 is at most
4 in modulus -- 3 bits, against binary64's 53. Every addition is therefore
exact, in this order and in every other. This is exactly the sufficient
condition Section 2.5 (`summation_order`) records: |J| 2**k = 4 * 4 = 16 <=
2**53. The contract does NOT assume that condition of any family, and neither
does this entry: the four additions were carried out.
ROUTE 2 (Fraction). The same four partial sums computed with `Fraction`,
comparing each intermediate against `Fraction(float(...))` to decide
representability. (S) holds; the exact total is 1_A; (C) holds on both the
exact and the computed total. The two routes agreed at every entry.""",
    ),
    SummationCase(
        case_id="S-ALICE-DECIMAL-LITERALS",
        family="alice_povm",
        weights=(("p^A_Z", FL_NINE_TENTHS), ("p^A_X", FL_ONE_TENTH)),
        every_entry_is_binary64=True,
        exact_total_multiple_of_identity=FL_NINE_TENTHS_PLUS_ONE_TENTH,
        computed_sum_is_identity=True,
        sum_rounds_nowhere=False,
        first_inexact_addition_index=3,
        inexact_addition_sites=((3, 0), (3, 3), (4, 0), (4, 3)),
        # RE-FROZEN ("Re-derive and re-freeze"): was "alice_povm_summation_rounds". The
        # derivation is the paragraph RE-DERIVED ... at the end of
        # `arithmetic` and O-PC-EXACT-SUMMATION's `revalidation`.
        refusal_reason="choice_weights_not_normalized",
        weight_list_first_inexact_addition=2,
        arithmetic="""\
THE CASE CONDITION (S) IS IN THE LIST FOR, AND THE ONE PLACE THE BB84 INSTANCE
CAN FAIL TO COMPILE END TO END. Theorem thm:pc12 (ii) writes the arithmetic out
"because the presentation PASSES (C)", and Remark rem:bb84checks adds that "IT
IS (S) THAT REFUSES THAT PRESENTATION AND NOT (C) ... which is why the
presentation WOULD PASS A TEST WRITTEN ON THE COMPUTED TOTAL ALONE".

ROUTE 1 (mantissa/exponent, integer arithmetic only).
  fl(0.9) = 8106479329266893 * 2**-53      [reduced; frexp gives it unreduced]
  fl(0.1) = 3602879701896397 * 2**-55
Both agree with the values the contract writes at Theorem thm:pc12 (ii),
checked digit for digit against the released blob.
On the common exponent 2**-55:
  fl(0.9) = 8106479329266893 * 2**2 * 2**-55 = 32425917317067572 * 2**-55
  fl(0.1) =                                     3602879701896397 * 2**-55
  sum     = 36028797018963969 * 2**-55
and 36028797018963969 = 2**55 + 1, so the exact sum is 1 + 2**-55.
WHY THE BINARY64 ADDITION NEVERTHELESS RETURNS EXACTLY 1: the successor of 1 in
binary64 is 1 + 2**-52, and 2**-55 < 2**-53 = half that step, so the exact sum
rounds to 1 under round-to-nearest. Hence (C) passes on the computed total.

WHERE THE FIRST INEXACT ADDITION IS, WHICH THE REFUSAL MUST CARRY. The emitted
family is
  M_(Z,0) = fl(0.9) [[1,0],[0,0]]        M_(Z,1) = fl(0.9) [[0,0],[0,1]]
  M_(X,0) = fl(0.1) [[1/2,1/2],[1/2,1/2]] M_(X,1) = fl(0.1) [[1/2,-1/2],[-1/2,1/2]]
Every entry is binary64: fl(0.9) * 1 and fl(0.9) * 0 are exact, and fl(0.1) *
(+-1/2) is a pure exponent shift, 3602879701896397 * 2**-56.
Accumulating entrywise in the declared order, the (0,0) entry is
  Sigma_1 = Sigma_2 = fl(0.9)                       = 8106479329266893 * 2**-53
  Sigma_3 = fl(0.9) + fl(0.1)/2
          = (8106479329266893 * 8 + 3602879701896397) * 2**-56
          = 68454714336031541 * 2**-56
and 68454714336031541 is ODD with bit length 56, while a value in [1/2, 1) must
be a multiple of 2**-53 to be binary64. So THE THIRD ADDITION IS THE FIRST
INEXACT ONE. The same happens at (1,1) by symmetry, and again at the fourth
element at both diagonal entries: FOUR INEXACT ENTRYWISE ADDITIONS, at
(element 3, entries (0,0) and (1,1)) and (element 4, entries (0,0) and (1,1)),
which is exactly the count Theorem thm:pc12 (ii) states -- "a computed total of
exactly 1_A THROUGH FOUR INEXACT ADDITIONS". The off-diagonal entries of
Sigma_3 and Sigma_4 are +-fl(0.1)/2 and 0, both exact.
The total OF THE DECLARED NUMBERS is (1 + 2**-55) 1_A, not 1_A.

ROUTE 2 (Fraction). The whole accumulation repeated with `Fraction`, deciding
each addition's exactness by `Fraction(float(x + y)) == x + y`, and the
computed total repeated in native `float`. Fraction gives the exact total
36028797018963969/36028797018963968 = 1 + 2**-55 at both diagonal entries and 0
off-diagonal; float gives exactly [[1.0, 0.0], [0.0, 1.0]]. The inexact sites
came out as ((3,0), (3,3), (4,0), (4,3)) in flat-entry indexing, matching route
1. The two routes agreed at every value.

THE REMEDY IS AT THE INSTANCE AND NOT HERE. Remark rem:bb84checks: "The
instance is then REFUSED rather than admitted within a margin, and the remedy
is to declare weights that satisfy it ... it is A PROPERTY OF THE PRESENTATION
AND NOT OF THE MATHEMATICS." This module never repairs what it was handed
(Section 2.5, `no_snapping`).

RE-DERIVED BY HAND FROM protocol-compiler/req:weight-list, AND
RE-FROZEN. The requirement: "The engine decides the conditions of
Definition def:weighted on the declared weights (q_t) of a choice-weighted
presentation: each q_t > 0 by its sign, and sum_t q_t = 1 exactly, with the
sum accumulated in the declared order of T_pub ... and required to round
nowhere. ... A weight list whose exact sum is not 1, or whose declared-order
accumulation rounds at some addition, is refused with
choice_weights_not_normalized, and no declaration is emitted." On this case:
  (1) The declared order of T_pub is the record's listing, (Z, X).
  (2) q_Z = fl(0.9) = 8106479329266893 * 2**-53 > 0 and q_X = fl(0.1) =
      3602879701896397 * 2**-55 > 0, both binary64: nothing is refused by
      type.
  (3) Addition 1: 0 + q_Z = q_Z, a binary64 number: exact.
  (4) Addition 2: q_Z + q_X = 36028797018963969 * 2**-55 = 1 + 2**-55
      (route 1 above). In [1, 2) the binary64 spacing is 2**-52 and 2**-55 is
      not a multiple of it, so the sum is not a binary64 number: THE SECOND
      ADDITION ROUNDS (to exactly 1).
  (5) The exact sum is 1 + 2**-55, NOT 1.
  (6) Both legs fail, either alone suffices, and the one reason is
      choice_weights_not_normalized, naming addition 2 as the first that
      rounds.
  (7) The decision is on the declared weights, so it precedes every decision
      on the family M_x = q_t N_{u|t} built from them: check V3 is not
      reached, and the completeness-sum arithmetic above, which is unchanged,
      no longer names this case's refusal. Bob's list (1/2, 1/2) passes (1/2
      and 1 are binary64, and the exact sum is 1), and the conditional
      families are the four BB84 projectors, exactly complete, so nothing
      refuses before Alice's weight list does.
Before the re-freeze this case pinned "alice_povm_summation_rounds", the
refusal of V3's (S) leg at element 3; that refusal is now pinned by
S-ALICE-DECIMAL-LITERALS-DIRECT, where no weight list is declared.""",
    ),
    SummationCase(
        case_id="S-ALICE-DECIMAL-LITERALS-DIRECT",
        family="alice_povm",
        weights=(("p^A_Z", FL_NINE_TENTHS), ("p^A_X", FL_ONE_TENTH)),
        every_entry_is_binary64=True,
        exact_total_multiple_of_identity=FL_NINE_TENTHS_PLUS_ONE_TENTH,
        computed_sum_is_identity=True,
        sum_rounds_nowhere=False,
        first_inexact_addition_index=3,
        inexact_addition_sites=((3, 0), (3, 3), (4, 0), (4, 3)),
        refusal_reason="alice_povm_summation_rounds",
        presentation="direct",
        arithmetic="""\
ADDED WITH THE RE-FREEZE OF S-ALICE-DECIMAL-LITERALS, SO THAT
CHECK V3'S CONDITION-(S) LEG ON {M_x} STAYS EXERCISED ON THE BB84 INSTANCE.

THE SAME FAMILY, PRESENTED DIRECTLY. The BB84 specification at the decimal
literals with no public-choice record on Alice's side: the compiler reads the
transmitter artefact's own `alice_povm`, the four matrices
  M_(Z,0) = fl(0.9) [[1,0],[0,0]]        M_(Z,1) = fl(0.9) [[0,0],[0,1]]
  M_(X,0) = fl(0.1) [[1/2,1/2],[1/2,1/2]] M_(X,1) = fl(0.1) [[1/2,-1/2],[-1/2,1/2]]
which are the entries S-ALICE-DECIMAL-LITERALS works out, every one a binary64
number. A direct presentation declares no weight list, so req:weight-list has
no subject and decides nothing, and the conditional-family decision has no
record to read either (def:weighted decides it of a `public_choices` record).
Nothing upstream refuses: the receiver presentation is Bob's balanced one.

WHAT REFUSES IS V3, BY (S) ALONE. The completeness sum in the declared order
(Z,0), (Z,1), (X,0), (X,1) is S-ALICE-DECIMAL-LITERALS' arithmetic verbatim,
both routes: the third addition is the first inexact one, at entries (0,0) and
(1,1), and again at the fourth, FOUR INEXACT ENTRYWISE ADDITIONS at
((3,0), (3,3), (4,0), (4,3)); the computed total is exactly 1_A, so (C) holds,
and the exact total is (1 + 2**-55) 1_A. Check V3 refuses with
alice_povm_summation_rounds, naming element 3 (def:validator V3; def:exact
(S)). The refusal's reason and index are the ones S-ALICE-DECIMAL-LITERALS
pinned before its re-freeze, and no number moves.

`weights` records what the matrices were built from; no weight reaches the
compiler on this presentation.""",
    ),
)


@dataclass(frozen=True)
class RhsTagCase:
    """One right-hand-side datum, and the tag check V6 runs on it.

    The tag IS the type (Definition ``def:homog``), so `expected_tag` is a
    function of `rhs_type` alone and never of a number. No case below records a
    matrix entry, because the check reads none.
    """

    case_id: str
    source_mode: str
    #: What the entry's right-hand-side slot holds.
    rhs_type: str
    #: An explicit tag field the arriving entry carried, or ``None``.
    arriving_tag_field: str | None
    #: The tag V6 reads off the type, or ``None`` where the entry is refused.
    expected_tag: str | None
    v6_passes: bool
    #: True where the entry is licensed for the emitted source mode, gate
    #: (G3)(a). ``general`` in trusted mode is admissible and NEVER licensed.
    licensed: bool
    arithmetic: str


#: (b) V6's tag typing, over the reachable (mode, rhs type, arriving tag) space.
#: NOTHING IN THIS TUPLE IS A NUMBER, and that is the content of the change:
#: Definition def:homog, "LICENSING IS THEREFORE A TYPE CHECK ON THE TAG, AND IT
#: COMPARES NO NUMBERS."
RHS_TAG_CASES: tuple[RhsTagCase, ...] = (
    RhsTagCase(
        case_id="TAG-trusted-scalar-untagged",
        source_mode="trusted",
        rhs_type="real scalar",
        arriving_tag_field=None,
        expected_tag="homogeneous",
        v6_passes=True,
        licensed=True,
        arithmetic="""\
A SCALAR RIGHT-HAND SIDE -> `homogeneous`, AND AN ENTRY CARRYING NO TAG FIELD
IS NOT REFUSED. Definition def:homog: "an entry whose right-hand-side slot
holds a REAL SCALAR is `homogeneous`". Check V6: "An entry carrying no tag
field is NOT refused: the tag is the type and is read off it, WHICH IS WHAT
LETS AN ENTRY DECLARED AS A REAL CONSTANT AND CARRYING NO TAG FIELD DOCK HERE."
LICENSED: `homogeneous` is the licensed form in trusted-source mode
(Definition def:homog (a)), so gate (G3)(a) passes on it.
THIS IS THE PATH THE PINNED SUPPLIER TAKES, and 0.3.0 is what opened it: through
0.2.0 check V6 "REQUIRED A MATRIX WHENEVER THE MARGINAL SLOT WAS FILLED, WHICH
REFUSED THE CONSUMING ENGINE'S OWN LICENSED FORM BY TYPE BEFORE ANY GATE RAN".
No arithmetic: the decision inspects which of two objects a slot holds.""",
    ),
    RhsTagCase(
        case_id="TAG-trusted-scalar-tagged-agreeing",
        source_mode="trusted",
        rhs_type="real scalar",
        arriving_tag_field="homogeneous",
        expected_tag="homogeneous",
        v6_passes=True,
        licensed=True,
        arithmetic="""\
AN EXPLICIT TAG THAT AGREES WITH THE TYPE. Definition def:homog: the pinned
reduction supplier "emits the form beside it as THE TAG VALUE `homogeneous` IN
TRUSTED-SOURCE MODE (`proof-reductions` 1.0.0, its `constraint_list` output
row) ... and the arriving field AGREES WITH THE TYPE V6 READS OFF THE DATUM,
WHICH IS ALL THAT COMPARISON ASKS OF IT."
The emitted `constraint_rhs_tag` is `homogeneous` either way: V6 reads it off
the datum, never off the field. No arithmetic.""",
    ),
    RhsTagCase(
        case_id="TAG-trusted-matrix",
        source_mode="trusted",
        rhs_type="Hermitian matrix on A",
        arriving_tag_field=None,
        expected_tag="general",
        v6_passes=True,
        licensed=False,
        arithmetic="""\
A HERMITIAN MATRIX RIGHT-HAND SIDE -> `general`: ADMISSIBLE INPUT, NEVER
LICENSED. Definition def:homog: "A `general` entry is ADMISSIBLE INPUT -- every
structural claim of this contract is proved for it -- BUT IT IS NOT LICENSED,
so a list containing one CARRIES NO KEY-LENGTH CLAIM (Theorem thm:gates), WHICH
IS THE FAIL-CLOSED DIRECTION." The declaration is emitted with
key_length_eligible = false (Table tab:gateoutcome, row 5).
ONE EXACT PREDICATE IS DECIDED HERE AND IT IS THE ONLY ONE IN THIS TUPLE: V6
decides Theta_k = Theta_k^dagger on the matrix, "the one decision of that check
that is on DATA rather than on a type" (Section 2.3's gate_report enumeration),
required by D(vi) and counted in Eq. eq:predcount. Deciding Hermiticity does
not make the TAG a measured property: the tag is still the type.""",
    ),
    RhsTagCase(
        case_id="TAG-trusted-tag-disagrees-with-type",
        source_mode="trusted",
        rhs_type="real scalar",
        arriving_tag_field="general",
        expected_tag=None,
        v6_passes=False,
        licensed=False,
        arithmetic="""\
AN EXPLICIT TAG DISAGREEING WITH THE TYPE IS A REFUSAL, AND THE TAG IS NEVER
TAKEN ON A SUPPLIER'S WORD. Definition def:homog: "Where an entry does arrive
carrying an explicit tag field, V6 compares that field against THE TYPE OF THE
DATUM IT NAMES and A DISAGREEMENT IS A REFUSAL; the tag is NEVER TAKEN ON A
SUPPLIER'S WORD AGAINST THE OBJECT THE ENTRY HOLDS."
THE SCOPE OF THAT SENTENCE IS ARRIVING ENTRIES ONLY, and the contract scopes it
rather than leaving it to pair with a clause of D(vi) that does not exist: "An
entry of Eq. eq:declaration is the triple (O^_k, bowtie_k, rhs_k) and HOLDS NO
TAG FIELD INDEPENDENT OF THAT TYPE ... so ON A CANDIDATE DECLARATION THIS
SENTENCE HAS NO SUBJECT, REFUSES NOTHING, and is NOT among the conjuncts D(vi)
is paired with (Theorem thm:validator-soundness, proof)." So this case is reachable on the
INPUT side (`constraint_entries`, or an entry transported by a link) and NOT on
a candidate declaration -- which is what keeps V6 complete for D(vi).
The refusal string is not fixed by the contract (open choice `OC-refusal`); what
is fixed is that the reason names V6. No arithmetic.""",
    ),
    RhsTagCase(
        case_id="TAG-trusted-neither-type",
        source_mode="trusted",
        rhs_type="neither a real scalar nor a Hermitian matrix on A",
        arriving_tag_field=None,
        expected_tag=None,
        v6_passes=False,
        licensed=False,
        arithmetic="""\
A SLOT HOLDING NEITHER ADMITTED OBJECT IS REFUSED BY TYPE AND NOT MEASURED.
Definition def:homog reads the tag off the type for the two untagged forms
only; check V6: "an entry whose right-hand-side slot holds neither admitted
object, or A COMPLEX-TYPED RIGHT-HAND SIDE IN UNTRUSTED MODE, is REFUSED BY TYPE
AND NOT MEASURED." No arithmetic, by construction.""",
    ),
    RhsTagCase(
        case_id="TAG-untrusted-scalar",
        source_mode="untrusted",
        rhs_type="real scalar",
        arriving_tag_field=None,
        expected_tag="homogeneous",
        v6_passes=True,
        licensed=True,
        arithmetic="""\
IN UNTRUSTED-SOURCE MODE ONLY THE SCALAR FORM EXISTS. Definition def:homog: "In
untrusted-source mode ONLY THE SCALAR FORM EXISTS", and D(vi) types the
right-hand side there as Theta_k = c_k in R with bowtie_k in {<=, =, >=}.
SO GATE (G3)(a) DEGENERATES THERE AND THE REPORT MUST SAY SO. Remark
rem:degenerate: it "is VACUOUSLY TRUE in untrusted-source mode at any d_A, where
the entry type is already scalar by D(vi), so the gate degenerates there from a
restriction INTO A TYPE CHECK THAT A WELL-FORMED DECLARATION PASSES BY
CONSTRUCTION, and rests entirely on (G3)(b), WHICH NO PROGRAM CAN VERIFY. The
compiler therefore emits `passed vacuously` rather than `passed` in gate_report,
and MUST NOT REPORT THE VACUOUS PASS AS EVIDENCE OF ANYTHING." No arithmetic.""",
    ),
)


@dataclass(frozen=True)
class CertificateOperatorCase:
    """One declared certificate OPERATOR Psi, and gate (G2)'s five conditions.

    0.3.0 changes this input's TYPE from a vector to the operator, so every
    field below is a function of Psi and none of a declared amplitude. The five
    conditions are decided independently and are recorded independently: gate
    ``(G2)`` is stated on all five and Section 2.3's ``gate_report`` keys them
    per predicate, so a case failing two records two failures.
    """

    case_id: str
    alice_dim: int
    virtual_dim: int
    #: The distinct entries of Psi, exactly. All must be binary64.
    psi_entries: tuple[F, ...]
    every_entry_is_binary64: bool
    #: The five decidable conditions of Definition def:eligible (G2), in the
    #: order that definition states them.
    psi_hermitian: bool
    psi_idempotent: bool
    psi_trace_is_one: bool
    psi_trace_rounds_nowhere: bool
    sr1_holds: bool
    sr2_holds: bool
    #: The partial sums of tr Psi, accumulated over the row index in increasing
    #: order, which is the order Section 2.5 (`summation_order`) fixes.
    trace_partial_sums: tuple[F, ...]
    gate_g2_passes: bool
    arithmetic: str


#: (c) Gate (G2) on the certificate operator. The passing case is the Band-A
#: instance's own Psi = |Phi+><Phi+|, which is also the contract's NON-VACUITY
#: WITNESS for the certificate class (head of Section 7, cited forward by
#: Corollary cor:noncanonical as a proof step).
CERTIFICATE_OPERATOR_CASES: tuple[CertificateOperatorCase, ...] = (
    CertificateOperatorCase(
        case_id="G2-PHI-PLUS",
        alice_dim=2,
        virtual_dim=2,
        psi_entries=(F(0), F(1, 2)),
        every_entry_is_binary64=True,
        psi_hermitian=True,
        psi_idempotent=True,
        psi_trace_is_one=True,
        psi_trace_rounds_nowhere=True,
        sr1_holds=True,
        sr2_holds=True,
        trace_partial_sums=(F(1, 2), F(1, 2), F(1, 2), F(1)),
        gate_g2_passes=True,
        arithmetic="""\
Psi = |Phi+><Phi+| ON A A'', THE ONE CASE Definition def:srcert CHANGED THE
INPUT TYPE FOR. In the declared computational basis, with A first
(`subsystem_order`), Psi is the 4x4 matrix with 1/2 at (0,0), (0,3), (3,0),
(3,3) and 0 elsewhere. EVERY ENTRY IS 0 OR 1/2, BOTH BINARY64 -- which is the
whole point: Theorem thm:pc12 (i), "the certificate IS DECLARABLE ... the
VECTOR |Phi+> having amplitudes 1/sqrt2 THAT NO BINARY64 NUMBER SQUARES TO 1/2".

THE FIVE CONDITIONS, EACH DECIDED SEPARATELY AND EXACTLY.
 (1) Psi = Psi^dagger: the matrix is real symmetric, entry by entry. PASS.
 (2) Psi^2 = Psi: the only non-zero products are over the index set {0,3}, and
     each of the four entries of Psi^2 there is 1/2 * 1/2 + 1/2 * 1/2 = 1/2.
     PASS, exactly.
 (3) tr Psi = 1, accumulated over the row index in increasing order:
     1/2, 1/2, 1/2, 1. Every addition adds 0 or adds 1/2 to 1/2, both exact, so
     the trace ROUNDS NOWHERE. PASS.
 (4) (SR1) tr_{A''} Psi = tau_A: tracing out the second factor gives
     [[1/2, 0], [0, 1/2]] = 1_A / 2, which is the tau_A of Eq. eq:bb84data.
     PASS, exactly, as an identity between the closed-form values.
 (5) (SR2) tr_A[(M_x (x) 1) Psi] = p_x rho^v_x for all four x. At balanced
     weights M_(b,a) = (1/2) |a^b><a^b| and p_(b,a) = 1/4, rho^v_(b,a) =
     |a^b><a^b| (the Band-A chain has L_s = 0, so A'' = A' and rho^v_x = rho_x
     by Definition def:chaincond (S3)). By Eq. eq:transpose-trick,
     tr_1[(Y (x) 1)|Phi+><Phi+|] = (1/2) Y^T, so the left side is
     (1/2) M_(b,a)^T = (1/4) (|a^b><a^b|)^T = (1/4) |a^b><a^b| -- the transpose
     being the identity here because all four projectors are real symmetric --
     which is p_(b,a) rho^v_(b,a). PASS at all four signals, exactly.

ROUTE 1 (mantissa/exponent). Every entry of Psi, of tau_A, of every M_x and of
every rho^v_x is an integer multiple of 2**-2 of modulus at most 1. Every
product and every sum in (2), (3), (4), (5) is therefore an integer multiple of
2**-4 of modulus at most 1, and the longest accumulation is over 4 terms, so
every intermediate has a numerator of at most 16 over 2**-4 -- 5 bits against
53. Every operation is exact.
ROUTE 2 (Fraction). All five conditions re-decided with `Fraction` matrices, the
partial traces computed by explicit index sums and (SR2) computed by forming
(M_x (x) 1) Psi and tracing the first factor -- NOT by the transpose trick, so
that the identity is checked rather than assumed. All five passed; the trace
partial sums came out (1/2, 1/2, 1/2, 1). The two routes agreed at every value.

WHAT THIS ENTRY DOES NOT PIN: (SR3). It "carries NO NUMBER, is NOT decidable,
and is TESTED FOR PRESENCE ONLY" (Definition def:eligible (G2)); Theorem
thm:gates (i), "the compiler TESTS PRESENCE, NEVER TRUTH". And no condition of
(G2) is stated on a vector: "the unit vector |psi> with Psi = |psi><psi| EXISTS
BY Psi^2 = Psi AND tr Psi = 1 and is NEVER ITSELF DECLARED".""",
    ),
    CertificateOperatorCase(
        case_id="G2-MAXIMALLY-MIXED-NOT-IDEMPOTENT",
        alice_dim=2,
        virtual_dim=2,
        psi_entries=(F(0), F(1, 4)),
        every_entry_is_binary64=True,
        psi_hermitian=True,
        psi_idempotent=False,
        psi_trace_is_one=True,
        psi_trace_rounds_nowhere=True,
        sr1_holds=True,
        sr2_holds=False,
        trace_partial_sums=(F(1, 4), F(1, 2), F(3, 4), F(1)),
        gate_g2_passes=False,
        arithmetic="""\
Psi_mix = 1_4 / 4: HERMITIAN, TRACE ONE, AND NOT A PROJECTOR -- SO THE
CERTIFICATE IS REFUSED. This is the case that shows the three conditions on Psi
are decided INDEPENDENTLY: two of them pass and the declaration is still
refused.

THE FIVE CONDITIONS.
 (1) Psi_mix = Psi_mix^dagger: diagonal and real. PASS.
 (2) Psi_mix^2 = Psi_mix: the square is 1_4/16, whose diagonal entry 1/16 is
     not the required 1/4. FAIL -- and this is the condition the case exists
     for. Definition def:eligible (G2) is what makes it decidable: "the unit
     vector |psi> with Psi = |psi><psi| EXISTS BY Psi^2 = Psi and tr Psi = 1",
     so a Psi failing idempotence IS NOT A RANK-ONE PROJECTOR and the
     certificate has no |psi> behind it at all.
 (3) tr Psi_mix = 1/4 + 1/4 + 1/4 + 1/4, accumulated over the row index:
     1/4, 1/2, 3/4, 1. Every partial sum is a multiple of 1/4 of modulus at
     most 1, so every addition is exact. PASS, and the trace ROUNDS NOWHERE --
     which is why this case isolates (2) rather than confounding it with (3).
 (4) (SR1) tr_{A''}(1_4/4) = (1/4) * 2 * 1_2 = 1_2/2 = tau_A. PASS, exactly.
     THE FAILURE IS THEREFORE NOT VISIBLE TO (SR1), which is the sharp part of
     this entry: an implementation deciding (SR1) alone would admit it.
 (5) (SR2) tr_A[(M_(b,a) (x) 1)(1_4/4)] = (1/4) tr(M_(b,a)) 1_2 =
     (1/4) p^A_b 1_2 = (1/8) 1_2 at balanced weights, while the required value
     is p_(b,a) rho^v_(b,a) = (1/4) |a^b><a^b|. Those differ: the left side is
     a multiple of the identity and the right side is rank one. FAIL, at all
     four signals.

SO TWO OF THE FIVE FAIL AND THREE PASS, and this entry records all five rather
than a single verdict. WHICH CONDITION THE REFUSAL NAMES IS NOT FIXED BY THE
CONTRACT and is not decided here: Table tab:gateoutcome row 3 says "refusal,
NAMING THE CONDITION", and the spelling and the ordering fall under open choice
`OC-refusal`. What IS fixed, and what run B must satisfy, is that gate_report
carries an outcome PER PREDICATE (Section 2.3), so both failures are recorded
whichever is named in the refusal.

ROUTE 1 (mantissa/exponent). Every entry is an integer multiple of 2**-2; every
product is a multiple of 2**-4 and every accumulation is over at most 4 terms,
so every intermediate is exact in binary64 by the same 5-bits-against-53
argument as the passing case. The DECISIONS are nonetheless taken in exact
arithmetic, not inherited from that (Section 2.5, `exact_decisions`).
ROUTE 2 (Fraction). The same five conditions re-decided with `Fraction`
matrices, (SR2) formed explicitly rather than through the transpose trick. The
verdicts came out (True, False, True, True, True, False) in the order
(hermitian, idempotent, trace_is_one, trace_rounds_nowhere, SR1, SR2). The two
routes agreed at every value.""",
    ),
)


@dataclass(frozen=True)
class SectorMapComparisonCase:
    """Where a sector map is compared, and by which check.

    The whole content of this tuple is the SCOPE of check V1 and the fact that
    a supplied witness is compared somewhere else. Definition ``def:validator``
    V1 names the compared families BY MACHINE KEY "because at a non-trivial
    chain TWO DIFFERENT FAMILIES COULD ANSWER TO 'THE RECEIVER POVM'".
    """

    case_id: str
    #: The object whose map is being compared.
    compared_object: str
    #: The check that compares it, or ``None`` where nothing compares it.
    compared_by: str | None
    #: Which of the four components disagrees, or ``None`` where all agree.
    disagreeing_component: str | None
    refuses: bool
    #: Verbatim where the contract fixes it.
    refusal_reason: str | None
    arithmetic: str


#: (d) V1's comparison, scoped to the two declaration slots that carry a
#: Q-operator, and V7 branch (c)'s separate comparison of a supplied witness.
#: THE FOUR COMPONENTS ARE THE SAME AT BOTH SITES -- block kind, identifiers,
#: their order, their dimensions -- AND THE REFUSAL REASONS ARE DIFFERENT.
SECTOR_MAP_COMPARISON_CASES: tuple[SectorMapComparisonCase, ...] = (
    SectorMapComparisonCase(
        case_id="MAP-bob-povm-agrees",
        compared_object="bob_povm, {F_v}",
        compared_by="V1",
        disagreeing_component=None,
        refuses=False,
        refusal_reason=None,
        arithmetic="""\
ONE OF EXACTLY TWO SLOTS V1 COMPARES. Definition def:validator V1: "The
families compared are EXACTLY THE Q-OPERATOR FAMILIES of Eq. eq:declaration --
which is the list D(i) quantifies over, AND NO WIDER ONE ... the emitted Bob
family `bob_povm`, {F_v}, which the last link of R_rec delivers as its target
POVM against the map its supplier wrote it against; AND EACH CONSTRAINT ENTRY of
CList ... Those two slots are THE WHOLE of Eq. eq:declaration that carries a
Q-operator, so THE LIST IS EXHAUSTIVE BY CONSTRUCTION RATHER THAN BY
ENUMERATION."
The comparison "is COMBINATORIAL -- it compares LABELS AND INTEGERS, NEVER
MATRIX ENTRIES". No arithmetic.""",
    ),
    SectorMapComparisonCase(
        case_id="MAP-constraint-entry-disagrees-on-order",
        compared_object="a constraint entry O^_k of CList",
        compared_by="V1",
        disagreeing_component="order of the block identifiers",
        refuses=True,
        refusal_reason="sector_map_mismatch",
        arithmetic="""\
THE SECOND SLOT, AND THE ONE THE CONTRACT CALLS LOAD-BEARING. Definition
def:validator V1: "That S_con's OWN entries are in the list and not only the
transported ones IS LOAD-BEARING: Definition def:compile fills CList from BOTH
sources, Definition def:spec (e) has EACH DECLARED O^_k CARRY ITS OWN SECTOR
MAP, and AN ENTRY WRITTEN AGAINST A DIFFERENT MAP IS EXACTLY THE ERROR THIS
CHECK EXISTS FOR, whichever source it arrived from."
The refusal is `sector_map_mismatch`, "NAMING THE FIRST POSITION AT WHICH THE
LISTS DIFFER" (V1), and the four grounds are fixed by Section 2.2
(`target_sectors`): "a disagreement in KIND, in an IDENTIFIER, in the ORDER or
in a DIMENSION". An order disagreement is chosen for this case because it is
the one a naive implementation is likeliest to normalize away -- and the order
is exactly what D(i)'s last clause and interface point (7) turn on.
No arithmetic: labels and integers only.""",
    ),
    SectorMapComparisonCase(
        case_id="MAP-witness-permuted-refused-at-V7",
        compared_object="a supplied feasibility witness omega^*",
        compared_by="V7 branch (c)",
        disagreeing_component="order of the block identifiers (a permutation)",
        refuses=True,
        refusal_reason="no_feasibility_witness",
        arithmetic="""\
THE CASE THAT SEPARATES THE TWO SITES, AND THE REASON IS NOT V1's. A witness
carrying a PERMUTED sector map is refused, and it is refused AT V7 AND NOT AT
V1, WITH `no_feasibility_witness` AND NOT `sector_map_mismatch`.

WHY V1 DOES NOT READ IT. Definition def:validator V1: "A supplied feasibility
witness is NOT A Q-OPERATOR AT ALL: omega^* is a block list ON A Q, an input key
CONSUMED AND NEVER EMITTED, and BRANCH (c) OF V7 ALREADY REQUIRES IT TO BE A
BLOCK LIST AGAINST Smap, WHICH IS THE ONE PLACE ITS MAP IS COMPARED." Carrying
it at V1 "would make V1 REFUSE A CANDIDATE THAT D(i)-D(viii) ADMIT and so
FALSIFY Theorem thm:validator-soundness (ii)" -- the completeness half.
WHERE IT IS READ. V7 (c): the witness is supplied "AS A BLOCK LIST AGAINST Smap
-- the map it carries compared with Smap IN BLOCK KIND, IN IDENTIFIERS, IN THEIR
ORDER AND IN THEIR DIMENSIONS, EXACTLY AS V1 COMPARES the map of a declared
Q-operator family". SAME FOUR COMPONENTS, DIFFERENT CHECK, DIFFERENT REASON.
WHAT THE REASON CARRIES. V7: `no_feasibility_witness` "NAMES, WHERE A WITNESS
WAS SUPPLIED AND REJECTED ON ITS MAP, THE FIRST POSITION AT WHICH THE TWO LISTS
DIFFER" -- so the position travels with the refusal even though the string is
V7's and not V1's.
AND THE READING RULE SURVIVES. Remark rem:completeness: the reason means "I WAS
NOT SHOWN A FEASIBLE STATE", never "there is none", and must not be reported to
a user as a defect in the protocol. A witness rejected on its MAP is a fortiori
not a demonstration that Feas is empty.
No arithmetic: the comparison is of labels and integers, and it happens BEFORE
any leg of the verification is evaluated.""",
    ),
    SectorMapComparisonCase(
        case_id="MAP-physical-receiver-not-compared",
        compared_object="receiver_povm, {F^ph_w}",
        compared_by=None,
        disagreeing_component=None,
        refuses=False,
        refusal_reason=None,
        arithmetic="""\
DELIBERATELY COMPARED BY NOTHING, AND AN IMPLEMENTATION MUST NOT ADD A CHECK.
Definition def:validator V1: "The physical family `receiver_povm`, {F^ph_w}, is
DELIBERATELY NOT IN THAT LIST: at a non-trivial receiver segment it lives on the
PHYSICAL RECEIVER SPACE, WHICH IS NOT Q, so it is NOT A Q-OPERATOR FAMILY and
HAS NO MAP TO COMPARE AGAINST Smap; its descriptor is matched instead by (C1),
against the source descriptor of Lambda_1 ... INCLUDING IT AT A NON-TRIVIAL
CHAIN WOULD NOT BE FAIL-CLOSED IN THE USEFUL SENSE: IT WOULD REFUSE EVERY SUCH
CHAIN, and V1 is claimed COMPLETE for D(i)."
IN BAND A THE TWO COINCIDE: Lambda_1 = id and F_v = F^ph_v, "and there the
comparison is the same one either way". That is why this case can be frozen at
all without a non-trivial chain.
THE CHAIN'S LAST TARGET DESCRIPTOR IS THE OTHER DELIBERATE OMISSION, and it is
decided at (C1) "AND NOWHERE ELSE ... by the SAME FOUR-COMPONENT COMPARISON V1
makes", a chain failing it being refused naming (C1).
No arithmetic.""",
    ),
)


@dataclass(frozen=True)
class EmissionRepresentabilityCase:
    """The one emission obligation this module carries: q_t N_{u|t}.

    Definition ``def:weighted``: "The products q_t N_{u|t} are formed EXACTLY on
    the declared dyadic numbers. A product of two binary64 numbers NEED NOT BE
    ONE, so the compiler decides, BEFORE EMITTING ANYTHING, that every entry of
    every N_{u,t} is a binary64 number".
    """

    case_id: str
    #: The declared weights, exactly. Each must be > 0 and they must sum to 1
    #: with that sum rounding nowhere, in the order `public_choices` lists them.
    weights: tuple[F, ...]
    weights_sum_rounds_nowhere: bool
    #: The declared conditional-family entry the weight multiplies.
    conditional_entry: F
    conditional_family_exactly_admissible: bool
    #: The exact product, which is what the compiler decides on.
    exact_product: F
    product_is_binary64: bool
    emits: bool
    refusal_reason: str | None
    arithmetic: str


#: (e) Definition def:weighted's emission decision.
EMISSION_REPRESENTABILITY_CASES: tuple[EmissionRepresentabilityCase, ...] = (
    EmissionRepresentabilityCase(
        case_id="EMIT-balanced-half-times-lattice",
        weights=(F(1, 2), F(1, 2)),
        weights_sum_rounds_nowhere=True,
        conditional_entry=F(1, 2),
        conditional_family_exactly_admissible=True,
        exact_product=F(1, 4),
        product_is_binary64=True,
        emits=True,
        refusal_reason=None,
        arithmetic="""\
THE CASE THE CONTRACT SAYS THE REFUSAL CANNOT TRIGGER IN. Definition
def:weighted: "On BOTH INSTANCES THIS PLATFORM RUNS TODAY the public choice is
BALANCED -- q_t = 1/2, so k_q = 1 -- and the product is ONE STEP FINER and
representable at every k <= 52: THE REFUSAL CANNOT TRIGGER THERE."

q_t = 1/2 is an integer multiple of 2**-1; the conditional entry 1/2 (an
X-basis projector entry) is an integer multiple of 2**-1 of modulus at most 1.
ROUTE 1 (mantissa/exponent). Multiplying a binary64 number by 1/2 is a PURE
EXPONENT SHIFT: the mantissa is unchanged, so the product 1/4 = 1 * 2**-2 is
exactly binary64 with a 1-bit numerator. The lattice moves from 2**-1 to 2**-2,
which is the "one step finer" the contract names, and 2 * 2**2 = 8 <= 2**53.
ROUTE 2 (Fraction). F(1,2) * F(1,2) = F(1,4), and
Fraction(float(F(1,4))) == F(1,4). The weights sum: F(1,2) + F(1,2) = 1 and
Fraction(float(1.0)) == 1, so (S) holds on the weights. The two routes agreed.

THE FAMILY IS ALSO DECIDED, NOT ONLY THE ENTRIES: "the result is emitted ONLY IF
every entry of it is a binary64 number AND the family it forms satisfies
Definition def:exact -- (H), (P), (C) and, on its own declared-order sum over V,
(S)." Both decisions pass here.""",
    ),
    EmissionRepresentabilityCase(
        case_id="EMIT-not-representable",
        weights=(F(2**52 + 1, 2**53), F(2**52 - 1, 2**53)),
        weights_sum_rounds_nowhere=True,
        conditional_entry=F(2**52 + 1, 2**53),
        conditional_family_exactly_admissible=True,
        exact_product=F((2**52 + 1) ** 2, 2**106),
        product_is_binary64=False,
        emits=False,
        refusal_reason="emitted_value_not_representable",
        arithmetic="""\
A PRODUCT OF DECLARED BINARY64 NUMBERS THAT IS NOT A BINARY64 NUMBER. This case
is constructed so that EVERY PRIOR DECISION PASSES and the refusal is isolated
to the representability of the product -- which is what makes it a test of
`emitted_value_not_representable` and not of something upstream of it.

THE DECLARED DATA.
  q_1 = (2**52 + 1) * 2**-53 = 4503599627370497 * 2**-53  (approx 0.5000000000000001)
  q_2 = (2**52 - 1) * 2**-53 = 4503599627370495 * 2**-53  (approx 0.4999999999999999)
  N_{0|t} = diag(q_1, q_2),  N_{1|t} = diag(q_2, q_1)   on a qubit.

WHY EVERY PRIOR DECISION PASSES.
 * q_1, q_2 are binary64: each numerator is odd with bit length 53 and 52
   respectively, against binary64's 53 significant bits, at exponent 2**-53.
 * q_t > 0 for both -- the domain condition of Definition def:weighted, decided
   by SIGN and not by any of the five conditions.
 * sum_t q_t = 1 EXACTLY and the addition ROUNDS NOWHERE: q_1 + q_2 =
   (2**52 + 1 + 2**52 - 1) * 2**-53 = 2**53 * 2**-53 = 1, and 1 is binary64.
   Accumulated in the order `public_choices` lists T_pub in: Sigma_1 = q_1
   (exact), Sigma_2 = 1 (exact). (S) HOLDS ON THE WEIGHTS.
 * {N_{u|t}} is exactly admissible: Hermitian (real diagonal); positive
   semidefinite (both diagonal entries strictly positive); complete, since
   N_0 + N_1 = diag(q_1 + q_2, q_2 + q_1) = 1_2 with both additions exact, so
   (S) holds on the conditional family too.

THE PRODUCT.
ROUTE 1 (mantissa/exponent, integer arithmetic only).
  q_1 * (N_{0|t})_{00} = (2**52 + 1) * 2**-53 * (2**52 + 1) * 2**-53
                       = (2**52 + 1)**2 * 2**-106
  (2**52 + 1)**2 = 2**104 + 2 * 2**52 + 1 = 2**104 + 2**53 + 1
                 = 20282409603651679431146506027009
which is ODD, so it cannot be halved: it needs ALL 105 of its bits, against
binary64's 53. THE PRODUCT IS NOT A BINARY64 NUMBER.
ROUTE 2 (Fraction). F(2**52+1, 2**53) ** 2 == F((2**52+1)**2, 2**106), and
Fraction(float(that)) != that. The two routes agreed, and route 2 also confirmed
the numerator 20282409603651679431146506027009 and its bit length 105.

SO THE COMPILER REFUSES WITH `emitted_value_not_representable` AND EMITS NO
DECLARATION. Definition def:weighted: "IT DOES NOT ROUND, AND IT DOES NOT SNAP
ITS OWN EMISSION: a specification whose weighting does not land exactly on the
lattice is A SPECIFICATION TO BE RE-DECLARED AT THE INSTANCE. Section 3.8 would
LICENSE a producer to snap what it emits instead, and THIS MODULE DECLINES THAT
ROUTE." Which of ADR-0008 Section 7.2.1's three producer routes that is: "THIS
MODULE REFUSES, AND IT DECLARES NO k."

THE SCOPE OF THE REASON IS NARROWER THAN ITS NAME, AND THE CONTRACT FIXES IT:
"it covers exactly that case -- an exact product of declared numbers that is NOT
a binary64 number. It does NOT cover an entry that IS binary64 but lies OFF
WHATEVER LATTICE THE INSTANCE DECLARED ITS OWN DATA ON -- SUCH AN ENTRY IS
EMITTED, and the five conditions the consumer states are decided on it exactly
and on it alone."
""",
    ),
)


@dataclass(frozen=True)
class DeclaredOrderCase:
    """Which order idx takes on an alphabet, and whether the choice is free."""

    case_id: str
    alphabet: str
    #: Where the order comes from.
    order_source: str
    #: True where the compiler is BOUND and false where the bijection is free.
    binding: bool
    #: True where idx indexes the alphabet at all.
    indexed_by_idx: bool
    arithmetic: str


#: (f) The binding rule of Definition def:compile, and the two alphabets it
#: does not leave free. NINE alphabets are indexed by idx; T_pub is not one.
DECLARED_ORDER_CASES: tuple[DeclaredOrderCase, ...] = (
    DeclaredOrderCase(
        case_id="ORDER-V-from-supplier",
        alphabet="V (the emitted outcome alphabet)",
        order_source=(
            "the order the supplier declared `target_povm` in; the compilation "
            "map takes THAT order as idx's component there"
        ),
        binding=True,
        indexed_by_idx=True,
        arithmetic="""\
THE BINDING RULE, AND IT PROTECTS A SUPPLIER RATHER THAN CONSTRAINING ONE.
Definition def:compile: "Where a supplied family arrives with a declared order
on the alphabet that indexes it -- AS THE TARGET POVM OF THE LAST LINK OF R_rec
DOES, ITS SUPPLIER HAVING ESTABLISHED ITS OWN COMPLETENESS SUM IN THAT ORDER --
the compiler takes THAT ORDER as idx's component there. So the order in which
condition (S) of Definition def:exact is decided on a supplied family here IS
THE ORDER THAT FAMILY WAS DECLARED IN, and it is ALSO the order the consuming
engine re-accumulates in (interface point (7)): ONE ORDER AT ALL THREE PLACES,
AND NO FAMILY IS REFUSED HERE FOR AN ORDERING ITS SUPPLIER NEVER CHOSE."
THIS IS THE ONE ACCUMULATION ORDER THE CONSUMING ENGINE'S TEXT ALSO FIXES
(interface point (7)), which is why `target_povm` needed a machine key of its
own at 0.3.0: through 0.2.0 the family arrived as an unkeyed component of a
chain link and the order had no name on the wire.
No arithmetic: the rule fixes a bijection, not a number. Its CONSEQUENCE is
arithmetical and is pinned by S-ALICE-DECIMAL-LITERALS, whose first inexact
addition index is a function of the order.""",
    ),
    DeclaredOrderCase(
        case_id="ORDER-S-is-the-sector-map",
        alphabet="S (the sector index set)",
        order_source=(
            "the total order the sector map Smap already fixes -- and NOT a "
            "second choice"
        ),
        binding=True,
        indexed_by_idx=True,
        arithmetic="""\
NOT A CHOICE AT ALL, AND 0.3.0 PUT THAT INTO A TARGET CONDITION. Definition
def:compile: idx's "component on S IS THE TOTAL ORDER THE SECTOR MAP Smap
ALREADY FIXES, AND NOT A SECOND CHOICE: one order on the sectors, required by
the last clause of D(i) and DECIDED BY V1."
WHY IT IS IN D(i) AND NOT ONLY IN V1. Definition def:target, D(i): "the sector
order a consumer compares against its own map AND the summation order it reads
off the emitted `label_index_map` MUST BE THE SAME ORDER -- so the agreement has
to be A PROPERTY OF THE DECLARATION THAT REACHES THE CONSUMER and not only of
the check that admits it ... Through 0.2.0 the two orders were declared
INDEPENDENTLY and nothing required them to agree; 0.3.0 put the requirement into
check V1, into the compilation map and into the output row, AND INTO NO TARGET
CONDITION -- WHICH LEFT V1 WITH A CLAUSE D(i) DID NOT CONTAIN, and it is
repaired by STATING THE CLAUSE HERE rather than by dropping the check."
SO V1 REPORTS IT: Section 2.3's gate_report enumeration lists "its comparison of
idx's sector order against Smap's, WHICH IS THE LAST CLAUSE OF D(i)" beside the
four-component map comparison. No arithmetic.""",
    ),
    DeclaredOrderCase(
        case_id="ORDER-T-pub-not-indexed-by-idx",
        alphabet="T_pub (the public-choice alphabet)",
        order_source=(
            "the order the `public_choices` record lists T_pub in, declared "
            "WITH THE RECORD and not through the index map"
        ),
        binding=True,
        indexed_by_idx=False,
        arithmetic="""\
THE ONE DECLARED ALPHABET idx DOES NOT INDEX, AND ITS SUM IS DECIDED HERE AND
RE-ACCUMULATED BY NO CONSUMER. Section 2.5 (`summation_order`): the weight sum
sum_{t in T_pub} q_t is accumulated "in the order the `public_choices` record
lists T_pub in -- THAT ALPHABET BEING ONE idx DOES NOT INDEX (Definition
def:compile), so ITS ORDER IS DECLARED WITH THE RECORD AND NOT THROUGH THE INDEX
MAP, and THE SUM IS DECIDED HERE AND RE-ACCUMULATED BY NO CONSUMER."
Definition def:compile lists the NINE alphabets idx does index -- X, V, S, O_A,
O_B, C_A, C_B, Chat, Z_perp -- and T_pub is not among them.
AN IMPLEMENTATION MUST THEREFORE NOT ROUTE THIS SUM THROUGH `label_index_map`,
and must preserve the record's own listing order. The decision is recorded in
gate_report UNDER THE COMPILATION MAP as its source, that being "where a
decision taken in FILLING Eq. eq:declaration rather than in CHECKING it is
recorded" (Section 2.3). No arithmetic here; the arithmetic is in
EMIT-not-representable, whose weights sum in this order.""",
    ),
    DeclaredOrderCase(
        case_id="ORDER-trace-is-the-row-order",
        alphabet="(none -- the row index of an emitted array)",
        order_source=(
            "the row order of the emitted array in increasing order, which the "
            "array itself determines"
        ),
        binding=True,
        indexed_by_idx=False,
        arithmetic="""\
A TRACE IS NOT INDEXED BY idx, AND THE CONTRACT SAYS SO TWICE. Section 2.3
(`label_index_map`): idx "does NOT index the basis of a matrix on A or on Q_s: a
trace is accumulated IN THE ROW ORDER OF THE EMITTED ARRAY, WHICH THE ARRAY
ITSELF DETERMINES." Section 2.1, interface point (7): the trace order "is
determinate from the array itself and is NOT carried by idx, THAT MAP INDEXING
ALPHABETS AND NOT THE BASIS OF A MATRIX".
TWO TRACES CARRY CONDITION (S) UNDER THIS ORDER: tr tau_A = 1 at check V2
(refusal `alice_marginal_trace_rounds`) and tr Psi = 1 at gate (G2). Both are
"read as an IDENTITY OF REAL NUMBERS exactly as a completeness sum is"
(Definition def:exact).
The partial sums of tr Psi under this order are frozen in
CERTIFICATE_OPERATOR_CASES: (1/2, 1/2, 1/2, 1) for |Phi+><Phi+| and
(1/4, 1/2, 3/4, 1) for 1_4/4. No further arithmetic here.""",
    ),
)


@dataclass(frozen=True)
class GateOutcomeCell:
    """One (mode requested, d_A, certificate, m) cell and its fixed outcome.

    Theorem ``thm:gates`` (ii) makes these BINDING: which of the three permitted
    outcomes a failure produces "IS FIXED BY Table tab:gateoutcome AND IS NOT AN
    IMPLEMENTER'S CHOICE".
    """

    case_id: str
    mode_requested: str
    alice_dim: str
    certificate: str
    m: str
    outcome: str
    emitted_mode: str | None
    key_length_eligible: bool | None
    fallback_recorded: bool
    #: The table row, or the definition, that fixes this cell.
    derives_from: str
    arithmetic: str


#: (g) The (mode, d_A, certificate, m) cells, including the two at d_A = 1 that
#: Table tab:gateoutcome does not carry as rows of its own.
GATE_OUTCOME_CELLS_0_3_0: tuple[GateOutcomeCell, ...] = (
    GateOutcomeCell(
        case_id="G-CELL-trusted-d2-absent-m0",
        mode_requested="trusted",
        alice_dim=">=2",
        certificate="absent",
        m="0",
        outcome="untrusted-mode emission, fallback recorded",
        emitted_mode="untrusted",
        key_length_eligible=None,
        fallback_recorded=True,
        derives_from="Table tab:gateoutcome, row 2",
        arithmetic="""\
THE ONE ROW WHERE A FALLBACK IS TAKEN, AND ITS SCOPE IS EXACTLY m = 0. Table
tab:gateoutcome row 2: "Proposition prop:conservative applies, UNIFORMLY IN THE
MARGINAL: at m = 0 the emitted feasible set CONTAINS the trusted-mode feasible
set of EVERY tau_A the request might have carried, so the change CAN ONLY LOSE
RATE -- and NO CONSTRAINT ENTRY IS RE-READ IN THE PASSAGE, THERE BEING NONE."
KLE is then "decided by the remaining gates", so it is not fixed by this cell:
with m = 0 gate (G3) is not engaged (Theorem thm:band-a (iii)) and (G2) is
satisfied in untrusted mode, so KLE follows from (G1) alone. Recorded as None
rather than guessed.
THE MARGINAL SLOT HOLDS nomarg HERE (Theorem thm:gates (i)). No arithmetic.""",
    ),
    GateOutcomeCell(
        case_id="G-CELL-trusted-d2-absent-m1",
        mode_requested="trusted",
        alice_dim=">=2",
        certificate="absent",
        m=">=1",
        outcome="refusal",
        emitted_mode=None,
        key_length_eligible=None,
        fallback_recorded=False,
        derives_from="Table tab:gateoutcome, row 4",
        arithmetic="""\
THE OUTCOME IS UNCHANGED FROM 0.2.0 AND THE REASON IS NOT, AND THIS CELL IS
FROZEN FOR THE REASON. Table tab:gateoutcome row 4: "Through 0.2.0 it was
ARITHMETICAL -- no entry carried a c_k, so there was NO UNTRUSTED ENTRY TO FALL
BACK TO. Under the declared tag a `homogeneous` entry CARRIES ONE, and
Proposition prop:conservative EVEN GIVES THE SET INCLUSION; WHAT IS MISSING IS
THE SUPPLIER'S CONSTRAINT-SOUNDNESS ATTESTATION, WHICH WAS MADE AGAINST
c_k tau_A AND HAS NO REFERENT WITHOUT A CERTIFICATE."
Theorem thm:gates (i) heads the argument "WHY ROW 4 STAYS A REFUSAL ALTHOUGH THE
DATUM FOR A FALLBACK NOW EXISTS, WHICH IS THE ONE PLACE THE DECLARED TAG CHANGES
WHAT COULD BE DONE AND THIS CONTRACT DECLINES TO DO IT", and states the rule:
"Re-reading the entry as a scalar comparison is A RE-INTERPRETATION OF ANOTHER
MODULE'S ATTESTATION AGAINST A LARGER REACHABLE SET, and THIS MODULE DOES NOT
PERFORM ONE: it NEVER DROPS AN ENTRY, NEVER SYNTHESIZES A LICENCE, AND DOES NOT
RE-READ ONE EITHER."
RUN B MUST NOT "IMPROVE" THIS CELL INTO A FALLBACK ON THE STRENGTH OF THE TAG.
The feasible-set direction is safe; the attestation is not. No arithmetic.""",
    ),
    GateOutcomeCell(
        case_id="G-CELL-trusted-d2-failing",
        mode_requested="trusted",
        alice_dim=">=2",
        certificate="present, one of the five conditions fails",
        m="any",
        outcome="refusal, naming the condition",
        emitted_mode=None,
        key_length_eligible=None,
        fallback_recorded=False,
        derives_from="Table tab:gateoutcome, row 3",
        arithmetic="""\
A CERTIFICATE THAT DOES NOT VERIFY IS A DEFECT IN THE SUPPLIED DATA, NOT A
WEAKER CLAIM. Table tab:gateoutcome row 3: "silently demoting it would HIDE A
MIS-SPECIFIED SOURCE."
THE FIVE CONDITIONS ARE Definition def:eligible (G2)'s and are stated once
there: Psi Hermitian; Psi^2 = Psi; tr Psi = 1 with the trace ROUNDING NOWHERE;
(SR1); (SR2) -- "every other site that names (G2) QUOTES THESE FIVE AND ADDS
NOTHING TO THEM". They are pinned per predicate in
CERTIFICATE_OPERATOR_CASES/G2-MAXIMALLY-MIXED-NOT-IDEMPOTENT. No arithmetic
here.""",
    ),
    GateOutcomeCell(
        case_id="G-CELL-trusted-d1-absent",
        mode_requested="trusted",
        alice_dim="1",
        certificate="absent",
        m="any",
        outcome="trusted-mode emission with tau_A = [1]",
        emitted_mode="trusted",
        key_length_eligible=None,
        fallback_recorded=False,
        derives_from="Definition def:compile (NOT a row of Table tab:gateoutcome)",
        arithmetic="""\
NOT A TABLE ROW, AND THE ANSWER IS IN THE COMPILATION MAP. Every row of Table
tab:gateoutcome that mentions an absent certificate carries the scope
"at d_A >= 2"; the d_A = 1 behaviour is Definition def:compile's: "at d_A = 1,
where Definition def:eligible (G2) does not demand a certificate, a trusted-mode
request IS SERVED WITH tau_A = [1], THE UNIQUE ELEMENT OF S_=(A)".
AND IT IS NOT A DEFAULT SUBSTITUTED FOR A MISSING DATUM, which `fail_closed`
would forbid. Theorem thm:gates (i) argues it in place: "because S_=(A) = {[1]} IS
A SINGLETON, so D(ii) ADMITS THAT VALUE AND NO OTHER, and because by Remark
rem:dA1 THE RESULTING FEASIBLE SET IS THE UNTRUSTED ONE, so THE FILLED SLOT
EXCLUDES NOTHING."
WHY (G2) MUST NOT BE DEMANDED THERE. Remark rem:dA1: at d_A = 1 "the conditions
omega_A = tau_A and tr omega = 1 are THE SAME CONDITION ON THE SAME NUMBER", the
two feasible sets are EQUAL, and the certificate "LICENSES THE CONDITION
tr omega = 1, WHICH EVERY NORMALIZED STATE SATISFIES, SO IT EXCLUDES NOTHING:
the compiler MUST NOT DEMAND THE ATTESTATION THERE."
CONTRAST Remark rem:notfallback: tau_A = 1_A / d_A is NEVER substituted at any
dimension -- it is a strictly STRONGER claim than nomarg, not a neutral one.
No arithmetic: [1] is the 1x1 identity.""",
    ),
    GateOutcomeCell(
        case_id="G-CELL-trusted-d1-failing",
        mode_requested="trusted",
        alice_dim="1",
        certificate="present, one of the five conditions fails",
        m="any",
        outcome="refusal, naming the condition",
        emitted_mode=None,
        key_length_eligible=None,
        fallback_recorded=False,
        derives_from=(
            "Table tab:gateoutcome, row 3, whose scope 0.3.0 states as EVERY "
            "d_A; pointed at by Definition def:compile's d_A = 1 clause"
        ),
        arithmetic="""\
THE CELL 0.3.0 CLOSED BY WIDENING ROW 3's SCOPE, AND IT IS THE ONE A READER OF
THE 0.1.4 TABLE COULD NOT RESOLVE. Definition def:compile serves a d_A = 1
trusted request with tau_A = [1] "UNLESS THAT REQUEST CARRIES A CERTIFICATE
FAILING ANY OF THE FIVE CONDITIONS of Definition def:eligible (G2), IN WHICH
CASE IT IS REFUSED, WHICH IS WHAT ROW 3 OF Table tab:gateoutcome PROVIDES AT
EVERY d_A -- a certificate that does not verify is A DEFECT IN THE SUPPLIED
DATA, NOT A WEAKER CLAIM."
Row 3 itself now carries the scope in its own text: "THE SCOPE IS EVERY d_A: at
d_A = 1 the gate DEMANDS NO CERTIFICATE (Remark rem:dA1), BUT ONE SUPPLIED THERE
AND FAILING IS THE SAME DEFECT IN THE SAME DATA, so this is the row Definition
def:compile's d_A = 1 clause points at."
SO "NOT DEMANDED" AND "IGNORED IF PRESENT AND BROKEN" ARE DIFFERENT, and an
implementation that skips (G2) entirely at d_A = 1 gets this cell wrong. No
arithmetic.""",
    ),
    GateOutcomeCell(
        case_id="G-CELL-g3a-general-in-trusted",
        mode_requested="trusted",
        alice_dim="any",
        certificate="present and passing",
        m=">=1",
        outcome="emission with key_length_eligible = false",
        emitted_mode="trusted",
        key_length_eligible=False,
        fallback_recorded=False,
        derives_from="Table tab:gateoutcome, row 5; Remark rem:degenerate",
        arithmetic="""\
(G3)(a) IS A TYPE CHECK AT EVERY d_A, AND THAT IS A DISCLOSED DIVERGENCE FROM
THE CONSUMER. Table tab:gateoutcome row 5: an entry declared `general` in
trusted-source mode fails the licensed class; "the declaration IS WELL-FORMED
and may be explored numerically; it is THE KEY-LENGTH CLAIM, NOT THE OBJECT,
that is unsupported."
THE d_A = 1 VACUOUS PASS OF 0.1.4-0.2.0 IS WITHDRAWN, AND AN IMPLEMENTATION MUST
NOT CARRY IT OVER. Remark rem:degenerate: "Under the operator form of
0.1.4--0.2.0 it WAS vacuous there, every 1x1 Hermitian Theta_k being
Theta_k . [1]; UNDER THE DECLARED TAG IT IS NOT, because an entry tagged
`general` DECLARES A MATRIX AND FAILS A TYPE CHECK AT EVERY DIMENSION. The
consuming engine's accepted contract RECORDS THE GATE AS VACUOUSLY TRUE AT
d_A = 1 in its input table while making licensing a type check in its own
definition of the licensed class, and THE TWO READINGS DIFFER EXACTLY ON A
`general`-TAGGED 1x1 ENTRY. THIS MODULE TAKES THE STRICTER READING ... That is
FAIL-CLOSED -- it emits KLE = false where the other reading would emit true,
COSTING A RATE AND NEVER CLAIMING ONE."
SO `passed vacuously` IS EMITTED IN UNTRUSTED MODE ONLY, at any d_A, and NOT at
d_A = 1 in trusted mode. The G3 signature discloses the divergence as its item
(b), against meat-core PATCH backlog items DF-24 and DF-25. No arithmetic.

[THE DIVERGENCE THIS DISCLOSES IS CLOSED. Under the owner's reading
of the gate at d_A = 1, the consuming engine's part (i) is a type check at every d_A
as well (meat-core/rem:cgate, def:homog), so both modules leave a
`general`-tagged 1x1 entry unlicensed and agree on every entry;
protocol-compiler/rem:degenerate states the one reading. No verdict, value or id
of this entry moved; the text above is kept as frozen.]""",
    ),
)


# ---------------------------------------------------------------------------
#  Group PC-M -- the 0.3.0 exact number model, the tag, and the operator Psi
# ---------------------------------------------------------------------------

O_PC_EXACT_SUMMATION = PCOracleEntry(
    oracle_id="O-PC-EXACT-SUMMATION",
    claims=("PC2", "PC3", "PC6", "PC12"),
    kind="fail-closed",
    subject=(
        "Definition def:exact condition (S), Theorem thm:pc12 (ii) and "
        "Requirement req:weight-list: the BB84 family at the balanced and at "
        "the decimal-literal weights, genuine POVMs with every entry binary64 "
        "and a computed completeness sum of exactly the identity. The balanced "
        "one is admitted. The decimal-literal one fails (S) alone on its "
        "completeness sum: presented through the public-choice record it is "
        "refused first, by req:weight-list on its weight list "
        "(choice_weights_not_normalized); presented directly it is refused by "
        "check V3's (S) leg (alice_povm_summation_rounds)."
    ),
    derivation="""\
THE ONE PLACE THE BB84 INSTANCE CAN FAIL TO COMPILE END TO END, and the case
condition (S) exists for. Frozen in SUMMATION_CASES, three cases since the
re-freeze (see `revalidation`).

WHY (S) IS A CONDITION AND NOT A REMARK. Definition def:exact: "(C) alone says
that the COMPUTED sum is the identity, and NOT that sum_j a_j = 1 holds OF THE
DECLARED NUMBERS -- which is what every derivation below that consumes
completeness reads it as, and what a consumer of the emitted declaration reads
it as. (S) is exactly what makes the two the same statement, and IT IS THE
REASON A FAMILY WHOSE ENTRIES ARE ALL EXACTLY REPRESENTABLE MAY STILL BE
REFUSED: the condition is ON THE ADDITIONS, NOT ON THE OPERANDS."

WHAT THE TWO CASES SEPARATE. Both families are POVMs; every entry of both is a
binary64 number; both have a COMPUTED completeness sum of exactly 1_A. They
differ only in whether the additions forming that sum were exact. So a test
written on the computed total alone passes both, which is precisely what
Remark rem:bb84checks warns of: the 0.9/0.1 presentation "WOULD PASS A TEST
WRITTEN ON THE COMPUTED TOTAL ALONE".

THE ARITHMETIC IS IN EACH CASE'S `arithmetic` FIELD, done twice by routes
sharing no step, and the mantissa/exponent values agree digit for digit with
those the contract writes at Theorem thm:pc12 (ii): fl(0.9) =
8106479329266893 * 2**-53, fl(0.1) = 3602879701896397 * 2**-55, exact sum
36028797018963969 * 2**-55 = 1 + 2**-55. The inexact-addition COUNT computed
here -- four entrywise additions, at elements 3 and 4 and at the two diagonal
entries -- also agrees with the contract's own "a computed total of exactly 1_A
THROUGH FOUR INEXACT ADDITIONS".

THE WEIGHT SUM HAS ITS OWN STRING. Requirement req:weight-list decides
sum_t q_t = 1 exactly on the declared weights, accumulated in the declared
order and required to round nowhere, and spells the refusal of a list failing
either leg: choice_weights_not_normalized. It is decided before any decision
on the family the weights build, so S-ALICE-DECIMAL-LITERALS pins it, with the
first rounding addition (2) of the weight list; the three (S) strings of the
`refusal` row stay the three FAMILIES' and S-ALICE-DECIMAL-LITERALS-DIRECT
pins the one for {M_x}. This paragraph previously read: "WHAT IS NOT
FROZEN HERE. The refusal string for a condition-(S) failure of the
PUBLIC-CHOICE WEIGHT SUM sum_t q_t = 1. ... the `refusal` row spells no string
for it ... That falls under open choice `OC-refusal` and is not decided
here." """,
    hypotheses=(
        "Round-to-nearest, ties-to-even, which is the binary64 default and what "
        "makes fl(0.9) + fl(0.1) return exactly 1; the contract's own argument "
        "at Theorem thm:pc12 (ii) uses it ('2**-55 is below half that step').",
        "The declared order on X is (Z,0), (Z,1), (X,0), (X,1). The FIRST "
        "INEXACT ADDITION INDEX IS A FUNCTION OF THAT ORDER; the verdict "
        "(S) fails is not.",
        "The declared order of T_pub on Alice's record is (Z, X); the first "
        "rounding addition of the weight list (2) is a function of that order "
        "and the verdict is not.",
    ),
    revalidation="""\
RE-FROZEN, the one frozen-registry change authorised for the weight sum
("Re-derive and re-freeze"; the decision behind it: "Refuse in core, snap at
entry").

WHAT CHANGED. protocol-compiler/req:weight-list (amended) now states the outcome of a failed weight list:
"A weight list whose exact sum is not 1, or whose declared-order accumulation
rounds at some addition, is refused with choice_weights_not_normalized, and no
declaration is emitted." The withdrawn reading -- the equality read on the
computed binary64 total, the rounding left to check V3 on the completeness sum
the weights carry -- was what S-ALICE-DECIMAL-LITERALS pinned.

THE HAND DERIVATION, from the requirement and not from the code. Declared
order (Z, X); q_Z = fl(0.9) = 8106479329266893 * 2**-53 and q_X = fl(0.1) =
3602879701896397 * 2**-55, positive binary64 numbers. Addition 1 is exact.
Addition 2 gives 36028797018963969 * 2**-55 = 1 + 2**-55, which is not a
binary64 number (the spacing in [1, 2) is 2**-52), so it rounds; and the exact
sum is 1 + 2**-55, not 1. Both legs fail; the reason is
choice_weights_not_normalized, the first rounding addition 2. The decision is
on the declared weights and precedes V3, so S-ALICE-DECIMAL-LITERALS'
refusal_reason moves from alice_povm_summation_rounds to
choice_weights_not_normalized, with weight_list_first_inexact_addition = 2.
Its completeness-sum fields are arithmetic of the family and do not move.

WHAT KEEPS V3'S (S) LEG EXERCISED. S-ALICE-DECIMAL-LITERALS-DIRECT, the same
matrices presented directly (no weight list declared), refused by V3 with
alice_povm_summation_rounds at element 3 -- the reason and index the old
case pinned.

NO NUMBER MOVES. No key length, rate or emitted declaration is involved: the
case is refused before and after, only its reason differs.""",
)

O_PC_RHS_TAG = PCOracleEntry(
    oracle_id="O-PC-RHS-TAG",
    claims=("PC1", "PC6", "PC9"),
    kind="structural-identity",
    subject=(
        "Definition def:homog, check V6 and gate (G3)(a): the declared "
        "`homogeneous`/`general` tag read off the right-hand side's TYPE, and "
        "the licensed class as a type check that COMPARES NO NUMBERS."
    ),
    derivation="""\
THE SINGLE LARGEST BEHAVIOURAL CHANGE AT 0.3.0, AND NOT ONE NUMBER IS FROZEN
FOR IT. Frozen in RHS_TAG_CASES, six cases over the reachable (mode, rhs type,
arriving tag field) space.

WHAT IT REPLACED. Section 1.1, design decision 4: "(G3)(a), was a NUMERICAL TEST
of an operator against c_k tau_A and was ONE-SIDED BY A FACTOR OF TWO. It is now
a TYPE check on the right-hand side's declared tag, COMPARING NO NUMBERS AND
DECIDING EXACTLY (Definition def:homog, Theorem thm:gates (i)), which is THE FORM
THE CONSUMING ENGINE'S ACCEPTED CONTRACT FIXED AT ITS VERSION 1.0.0 and the form
this module must emit against."

WHAT IT UNBLOCKED. Definition def:declaration: "through 0.2.0 this module
emitted A MATRIX WITH NO TAG, which that engine reads as `general`, and a
`general` entry is admissible input there BUT IS NEVER LICENSED -- so THE
CONSTRAINED TRUSTED-MODE KEY-LENGTH BRANCH WAS UNREACHABLE THROUGH THIS PRODUCER
AT d_A >= 2." And check V6: "through 0.2.0 this check REQUIRED A MATRIX WHENEVER
THE MARGINAL SLOT WAS FILLED, WHICH REFUSED THE CONSUMING ENGINE'S OWN LICENSED
FORM BY TYPE BEFORE ANY GATE RAN."

WHY READING THE TAG OFF THE TYPE IS NOT AN INFERENCE. Definition def:homog:
"THAT READING IS A TYPE DECISION: it inspects WHICH OF TWO OBJECTS A SLOT HOLDS,
compares no numbers, reads no matrix entry and measures nothing -- so it is what
`decide_never_infer` PERMITS AND NOT WHAT IT FORBIDS, nothing being inferred
from a property of an object the entry was built from."

THE ONE EXACT PREDICATE IN THE NEIGHBOURHOOD, and it is not the tag: V6 decides
Theta_k = Theta_k^dagger on a `general` entry's matrix, "the one decision of
that check that is on DATA rather than on a type" (Section 2.3), required by
D(vi) and counted in Eq. eq:predcount.

THREE THINGS AN IMPLEMENTATION MUST NOT DO, each pinned by a case: construct
c_k tau_A (the CONSUMER does that, "this module does not" -- Section 2.3);
refuse an entry carrying no tag field (V6: it "is NOT refused"); take an
explicit tag on trust (V6 compares it against the type and refuses on
disagreement).""",
    hypotheses=(
        "The scoped sentence of V6 about an ARRIVING tag field has no subject "
        "on a CANDIDATE DECLARATION -- an entry of Eq. eq:declaration is a "
        "triple and holds no independent tag field -- which is what keeps V6 "
        "complete for D(vi) (Theorem thm:validator-soundness, proof).",
    ),
)


O_PC_SECTOR_MAP_SCOPE = PCOracleEntry(
    oracle_id="O-PC-SECTOR-MAP-SCOPE",
    claims=("PC1", "PC5", "PC6"),
    kind="structural-identity",
    subject=(
        "Definition def:validator V1 and V7 (c): the sector-map comparison is "
        "the WHOLE of the structural verification, it is scoped to the two "
        "declaration slots that carry a Q-operator, and a supplied witness's "
        "map is compared at V7 and nowhere else."
    ),
    derivation="""\
WHAT REPLACED THE OFF-BLOCK CHECKS, AND WHAT DID NOT. Frozen in
SECTOR_MAP_COMPARISON_CASES, four cases.

THE DELETION. Check V3: "THE OFF-BLOCK CONDITIONS OF THE 0.1.4 VALIDATOR ARE
GONE: an emitted Q-operator IS a block list, so there is NO Pi_s F_v Pi_{s'} or
Pi_s O^_k Pi_{s'} TO EVALUATE and NOTHING THAT COULD BE NON-ZERO. WHAT REPLACED
THEM IS V1'S SECTOR-MAP COMPARISON, AND NOTHING ELSE DID."

THE SCOPE. V1 compares "EXACTLY THE Q-OPERATOR FAMILIES of Eq. eq:declaration --
which is the list D(i) quantifies over, AND NO WIDER ONE": `bob_povm` and each
constraint entry. "Those two slots are THE WHOLE of Eq. eq:declaration that
carries a Q-operator, so the list is EXHAUSTIVE BY CONSTRUCTION rather than by
enumeration."

THE TWO DELIBERATE OMISSIONS, each with its own site, and each frozen: the
chain's last target descriptor, decided at (C1) "AND NOWHERE ELSE"; and a
supplied witness, compared at V7 branch (c). Widening V1 to either "would make
V1 REFUSE A CANDIDATE THAT D(i)-D(viii) ADMIT and so FALSIFY Theorem
thm:validator-soundness (ii)". The physical family {F^ph_w} is a third and is not compared at
all -- including it "WOULD REFUSE EVERY SUCH CHAIN".

THE CASE THAT DISCRIMINATES. MAP-witness-permuted-refused-at-V7: a witness with
a permuted map is refused with `no_feasibility_witness` and NOT with
`sector_map_mismatch`. The four compared components are the same at both sites;
the check and the reason are not. An implementation that routes the witness's
map through V1 gets the right verdict for the wrong reason and emits the wrong
string.

AND THE COMPARISON IS THE WHOLE BUDGET. V1: it "is COMBINATORIAL -- it compares
LABELS AND INTEGERS, NEVER MATRIX ENTRIES -- and it is THE WHOLE of the
structural verification the emitted declaration receives: block-diagonality is
CARRIED BY THE TYPE, so the one structural error that can still arise is TWO
PARTIES DISAGREEING ABOUT WHAT THE SECTORS ARE, and this is the check for it."
""",
    hypotheses=(
        "The four components are block kind, block identifiers, their order "
        "and their dimensions, at V1, at (C1) and at V7 (c) alike. The BLOCK "
        "KIND VOCABULARY is not fixed by the contract and no case below names "
        "a kind: open choice `OC-sector-block-kind`.",
    ),
)

O_PC_EMISSION_OBLIGATION = PCOracleEntry(
    oracle_id="O-PC-EMISSION-OBLIGATION",
    claims=("PC3",),
    kind="fail-closed",
    subject=(
        "Definition def:weighted: the ONE family this module constructs rather "
        "than passes through, the decision that every entry of it is binary64, "
        "and `emitted_value_not_representable` -- with the producer route "
        "ADR-0008 Section 7.2.1 leaves open and this module's choice of it."
    ),
    derivation="""\
THE ONLY PLACE THIS MODULE'S OWN NUMBERS, RATHER THAN A SUPPLIER'S, MUST LAND ON
THE LATTICE. Frozen in EMISSION_REPRESENTABILITY_CASES, two cases.

THE OBLIGATION. Definition def:weighted: "The products q_t N_{u|t} are formed
EXACTLY on the declared dyadic numbers. A PRODUCT OF TWO BINARY64 NUMBERS NEED
NOT BE ONE, so the compiler DECIDES, BEFORE EMITTING ANYTHING, that every entry
of every N_{u,t} is a binary64 number AND that the emitted family satisfies
Definition def:exact -- (H), (P), (C) and, on its own declared-order sum over V,
(S). If either decision fails, the compiler REFUSES -- with
`emitted_value_not_representable` in the first case and WITH THE PREDICATE THAT
FAILED in the second -- and emits no declaration."

THE ROUTE TAKEN, WHICH IS A CHOICE AND NOT A RULE. ADR-0008 Section 7.2.1 gives
a producer three routes; "THIS MODULE REFUSES, AND IT DECLARES NO k. It
establishes the five DIRECTLY, on the numbers it is about to emit, and refuses
otherwise; IT NEVER DECLARES A NEARBY FAMILY, which is what `no_snapping` rules
out; and it states NO (D-LAT) OBLIGATION of its own, because (D-LAT) is a
SUFFICIENT condition for the five to be establishable and IS NOT AMONG THE
CONDITIONS THE CONSUMING ENGINE STATES." The G3 signature discloses this as its
item (c).

WHAT IT COSTS, STATED RATHER THAN ROUTED AROUND. "Let the arriving entries be
integer multiples of 2**-k of modulus at most 1, and let each q_t be an integer
multiple of 2**-k_q; then every entry of q_t N_{u|t} is an integer multiple of
2**-(k+k_q) of modulus at most 1, so the constructed family lies on a lattice
k_q STEPS FINER than the one it was handed and is exactly binary64 whenever
k + k_q <= 53. On BOTH INSTANCES THIS PLATFORM RUNS TODAY the public choice is
BALANCED -- q_t = 1/2, so k_q = 1 -- and the product is one step finer and
representable at every k <= 52: THE REFUSAL CANNOT TRIGGER THERE."

SO THE TWO CASES ARE THE REACHABLE ONE AND THE UNREACHABLE-ON-TODAY'S-INSTANCES
ONE, and the second is constructed so that EVERY PRIOR DECISION PASSES -- the
weights are positive, sum to 1 with the addition exact, and the conditional
family is exactly admissible -- so that the refusal is isolated to the product.
Its arithmetic is done twice and the numerator 20282409603651679431146506027009
= 2**104 + 2**53 + 1 is odd with bit length 105.

AND THE REASON'S SCOPE IS NARROWER THAN ITS NAME: it does NOT cover "an entry
that IS binary64 but lies off whatever lattice the instance declared its own
data on -- SUCH AN ENTRY IS EMITTED".""",
    hypotheses=(
        "The weights and the conditional families are DECLARED data of the "
        "specification, not this module's construction; only the product is "
        "this module's. Assumption ass:spec assumes the families as declared "
        "and Definition def:weighted DECIDES their exact admissibility.",
    ),
)

O_PC_DECLARED_ORDER = PCOracleEntry(
    oracle_id="O-PC-DECLARED-ORDER",
    claims=("PC1", "PC2"),
    kind="structural-identity",
    subject=(
        "Section 2.5 (`summation_order`) and Definition def:compile: the four "
        "accumulation rules, the binding rule that fixes idx from a supplier's "
        "declared order, the D(i) clause on idx|_S, and the two orders idx "
        "does not carry."
    ),
    derivation="""\
THE ORDER IS PART OF THE DATUM, AND WHICH ORDER IT IS DECIDES WHETHER (S)
HOLDS. Frozen in DECLARED_ORDER_CASES, four cases.

WHY. Section 2.5 (`summation_order`): "A binary64 sum is a determinate number
ONLY ONCE THE ACCUMULATION ORDER IS FIXED, so the order is PART OF THE DATUM and
this contract NAMES IT." Definition def:exact adds: "In exact arithmetic the
order is IMMATERIAL. In binary64 it is not -- addition there is COMMUTATIVE BUT
NOT ASSOCIATIVE -- so the order is part of the datum, and this contract NAMES IT
RATHER THAN LEAVING EACH PARTY TO CHOOSE ONE."

THE FOUR RULES, and they are all of them: completeness sums over the family's
alphabet in the emitted idx order; sums over sector blocks in the idx order of
S; traces over the row index of the emitted array in increasing order; and the
public-choice weight sum in the order the `public_choices` record lists T_pub
in.

TWO OF THE FOUR ARE NOT FREE CHOICES AT ALL, which is what these cases pin: the
component on S IS the sector map's order (Definition def:compile, "AND NOT A
SECOND CHOICE"), required by D(i)'s last clause and decided by V1; and on any
alphabet that arrives ORDERED the compiler is BOUND to the supplier's order, so
that "NO FAMILY IS REFUSED HERE FOR AN ORDERING ITS SUPPLIER NEVER CHOSE".

AND TWO ORDERS idx DOES NOT CARRY: T_pub, whose order is declared with the
`public_choices` record because "that alphabet BEING ONE idx DOES NOT INDEX";
and the row order of a matrix, which "the array itself determines", idx
"INDEXING ALPHABETS AND NOT THE BASIS OF A MATRIX".

THE CONSEQUENCE IS ARITHMETICAL AND IS PINNED ELSEWHERE: the first inexact
addition index of SUMMATION_CASES/S-ALICE-DECIMAL-LITERALS is a function of the
declared order, and the trace partial sums of CERTIFICATE_OPERATOR_CASES are a
function of the row order.

WHAT REMAINS OPEN. WHICH bijection is chosen on an alphabet that arrives with no
order: open choice `OC-label-index-map`, narrowed at 0.3.0 but not closed.""",
    hypotheses=(
        "The nine alphabets idx indexes are X, V, S, O_A, O_B, C_A, C_B, Chat "
        "and Z_perp, in Definition def:compile's order. T_pub is NOT among "
        "them at 0.3.0 and was not at 0.1.4 either; what is new is that the "
        "contract now says so and fixes its order elsewhere.",
    ),
)

O_PC_GATE_CELLS = PCOracleEntry(
    oracle_id="O-PC-GATE-CELLS",
    claims=("PC9", "PC12"),
    kind="fail-closed",
    subject=(
        "Table tab:gateoutcome and Definition def:compile over the "
        "(mode requested, d_A, certificate, m) cells, including the two at "
        "d_A = 1 that the table carries no row for and the withdrawal of the "
        "d_A = 1 vacuous pass of (G3)(a)."
    ),
    derivation="""\
THE OUTCOMES ARE BINDING AND NOT EXPLANATORY. Frozen in GATE_OUTCOME_CELLS_0_3_0,
six cells. Theorem thm:gates (ii): which of the three permitted outcomes a gate
failure produces "IS FIXED BY Table tab:gateoutcome AND IS NOT AN IMPLEMENTER'S
CHOICE. It never drops a constraint entry silently, never substitutes a default,
and never synthesizes a licence."

WHAT 0.3.0 CHANGED IN THE TABLE: NOT ONE OUTCOME AND NOT THE ROW COUNT. Row 3's
SCOPE is now stated as every d_A and its five conditions are restated on the
operator Psi; row 4's REASON changed from an arithmetical one -- now false -- to
the missing attestation; row 5's failing condition is now a TYPE and not a
number. Six rows, six outcomes, unchanged.

THE TWO CELLS AT d_A = 1 ARE NOT ROWS AND THE CONTRACT RESOLVES BOTH.
G-CELL-trusted-d1-absent is Definition def:compile's: served with tau_A = [1],
"the unique element of S_=(A)", and Theorem thm:gates (i) argues in place that
this is NOT a default substituted for a missing datum. G-CELL-trusted-d1-failing
is row 3 read at its stated scope: "at d_A = 1 the gate DEMANDS NO CERTIFICATE,
BUT ONE SUPPLIED THERE AND FAILING IS THE SAME DEFECT IN THE SAME DATA". So
"not demanded" and "ignored if present and broken" are DIFFERENT, and an
implementation that skips (G2) entirely at d_A = 1 gets the second wrong.

THE WITHDRAWAL AN IMPLEMENTATION MUST NOT CARRY OVER. Remark rem:degenerate:
(G3)(a) was vacuous at d_A = 1 under the operator form of 0.1.4-0.2.0 and IS NOT
under the declared tag, "because an entry tagged `general` DECLARES A MATRIX AND
FAILS A TYPE CHECK AT EVERY DIMENSION". This module takes the STRICTER of the
two readings that differ there, and the divergence from the consuming engine is
disclosed in the G3 signature as item (b) against meat-core PATCH backlog DF-24
and DF-25. `passed vacuously` therefore survives in UNTRUSTED MODE ONLY.

[THE DIVERGENCE THIS DISCLOSES IS CLOSED. Under the owner's reading
of the gate at d_A = 1, the consuming engine's part (i) is a type check at every d_A
as well (meat-core/rem:cgate, def:homog), so both modules leave a
`general`-tagged 1x1 entry unlicensed and agree on every entry;
protocol-compiler/rem:degenerate states the one reading. No verdict, value or id
of this entry moved; the text above is kept as frozen.]

WHAT IS RECORDED AS None RATHER THAN GUESSED: `key_length_eligible` on the
cells where the table says it is "decided by the remaining gates". Filling it in
would decide what the table leaves to the other gates.""",
    hypotheses=(
        "These cells are about the SOURCE-MODE and CONSTRAINT-LIST axes only. "
        "The existing O-PC-GATES entry enumerates the full seven-axis reachable "
        "space at 0.1.4 and is NOT superseded: its axes survive and its "
        "(G3)(a) mechanism and d_A = 1 vacuity do not. It is marked for "
        "re-pointing at run B.",
    ),
)


# ===========================================================================
#  The registry
# ===========================================================================

PC_ORACLES: tuple[PCOracleEntry, ...] = (
    # Group PC-A -- the specification, the compilation map and typing.
    O_PC_TYPING,
    # Group PC-B -- weights, not fractions; the statistics functional.
    O_PC_WEIGHTS,
    O_PC_FIXED_FRACTION_REFUSAL,
    O_PC_PARTIAL_PHI,
    # Group PC-C -- sifting and party computability.
    O_PC_SIFTING,
    # Group PC-D -- the feasible set and the one-sided check.
    O_PC_FEASIBILITY,
    O_PC_WELLPOSED,
    # Group PC-E -- the validator.
    O_PC_VALIDATOR,
    # Group PC-F -- the reduction chain.
    O_PC_CHAIN,
    # Group PC-G -- the emission gates and the exhaustive enumeration.
    O_PC_GATES,
    O_PC_CONSERVATIVE,
    # Group PC-H -- source replacement and its certificate: in
    # registry_transmitter.py (PC10, PC11 are transmitter claims).
    # Groups PC-I and PC-J -- the BB84 instance and the conjugation pair:
    # in registry_instances_bb84.py (an instance is data).
    # Group PC-K -- the interface vocabulary.
    O_PC_VOCABULARY,
    # Group PC-L -- the assumption ledger.
    O_PC_LEDGER,
    # Group PC-M -- 0.3.0: the exact number model, the declared tag and
    # the certificate operator. Authored by run A of the B3 band before
    # any implementation of what they pin existed.
    O_PC_EXACT_SUMMATION,
    O_PC_RHS_TAG,
    O_PC_SECTOR_MAP_SCOPE,
    O_PC_EMISSION_OBLIGATION,
    O_PC_DECLARED_ORDER,
    O_PC_GATE_CELLS,
)


# ===========================================================================
#  Change-request candidates cleared
# ===========================================================================
#
#  Seven items were carried into this freeze as candidates for a change request
#  against the accepted contract. EACH IS RECORDED BELOW WITH THE READING TAKEN.
#  Six are CLEARED -- the contract answers them, and the answer is transcribed
#  rather than improvised. ONE IS ROUTED as a change-request candidate for the
#  driver, and it does NOT block this freeze: nothing frozen here depends on it,
#  and a conforming implementation exists on either reading.

CHANGE_REQUEST_CANDIDATES: tuple[tuple[str, str, str], ...] = (
    (
        "CLEARED",
        "Source links carry a constraint slot, but an Alice-side entry has no "
        "expressible form: every emitted constraint operator must be Hermitian "
        "and sector-block-diagonal ON Q (Definition def:declaration, D(iii), "
        "Section 2.2 `constraint_entries`), while Definition def:chaincond (S1) "
        "says no condition of the source segment mentions Q, V or V^ph.",
        "READING TAKEN, WHICH IS THE CONTRACT'S OWN TEXT AND ADDS NO RULE: "
        "Definition def:compile transports LITERALLY -- 'each entry is emitted "
        "with its relation symbol and right-hand side unchanged' -- and the "
        "proof of Theorem thm:typing (D(vi)) says that an entry whose typing does "
        "not match the emitted source mode is 'a property of the supplier's "
        "data, not of the compilation map' and that 'CHECK V6 REJECTS EXACTLY "
        "SUCH AN ENTRY'. An Alice-side operator likewise fails V3's Hermitian "
        "and block-diagonal clauses on Q. So the declaration is REFUSED naming "
        "the check, and NO TRANSFORMATION RULE IS INVENTED. Band A never "
        "exercises it: L_s = 0. Frozen in V6-constraint-typing (Group PC-E) and "
        "CHAIN-not-decided-C4-S3 (Group PC-F).",
    ),
    (
        "CLEARED",
        "`feasibility_witness` is an INPUT key with no output key, yet Theorem "
        "thm:feasibility (ii) says the compiler 'EMITS a witness omega^* and verifies "
        "those conditions on it'.",
        "BOTH READINGS RECORDED, NEITHER DECIDED -- in interface.yaml under "
        "inputs.feasibility_witness.emits_versus_verifies_note. What is NOT in "
        "doubt on either reading, and is what this registry freezes: the "
        "default candidate Eq. eq:witness-empty is tried FIRST; a supplied "
        "witness is verified condition by condition against Definition "
        "def:feasible; and where neither passes the reason is "
        "`no_feasibility_witness` verbatim. Whether a passing witness is "
        "carried out of the compiler is an interface question the contract does "
        "not settle, and no frozen case depends on the answer.",
    ),
    (
        "ROUTED -- does not block this freeze",
        "The `fixed_fraction_requested` refusal exists (Theorem thm:choice-encoding (iv); "
        "Section 2.5 bullet 3), but SECTION 2.2 GIVES THE REQUEST NO FIELD TO "
        "ARRIVE IN: `public_choices` is typed as the record "
        "(T_pub, q, {N_{u|t}}) with no model selector, and no other input row "
        "carries one.",
        "NO KEY IS INVENTED. Two conforming readings are recorded in "
        "interface.yaml (conventions.fixed_fraction_arrival_note) and in "
        "O-PC-FIXED-FRACTION-REFUSAL: (A) within the typed input the request is "
        "INEXPRESSIBLE, so the check is unreachable and the substantive "
        "obligation -- that no fixed_fraction artifact is ever emitted -- holds "
        "BY CONSTRUCTION, since Definition def:compile weights every presented "
        "choice family by Definition def:weighted and Theorem thm:choice-encoding (iii) "
        "proves no q_t is emitted outside a POVM element; (B) the request "
        "arrives out of band as a caller-level model selection and is refused "
        "with the verbatim string. THE FREEZE IS UNAFFECTED because reading (A) "
        "needs no invention and violates nothing; the item is routed so that a "
        "human decides whether Section 2.2 should carry a selector, which would "
        "be a Section 3 scope change.",
    ),
    (
        "CLEARED",
        "There is no sifting-predicate slot in the emitted declaration, so "
        "Chat_key of Eq. eq:chkey cannot be read off an emitted field.",
        "NO SLOT IS ADDED. The G3 signature records as judgement "
        "call (b) that 'THE SIFTING PREDICATE STAYS OUTSIDE THE DECLARATION "
        "OBJECT, the ambiguity touching only zero-probability acceptance "
        "values, and ANY FUTURE PINNING IS A SCOPE CHANGE UNDER SECTION 3'. "
        "Where a derivation needs the accept-supported key-value set it "
        "computes it INSIDE THE DERIVATION from r, a and the specification's "
        "declared varsigma -- which is what Theorem thm:pc12 (iv) does to "
        "obtain Chat_key = {gen}, and what Group PC-I freezes. D(v) asks only "
        "that SOME varsigma exist, and the proof of Theorem thm:validator-soundness "
        "reconstructs one from r and a alone (RECON-varsigma-MINI).",
    ),
    (
        "CLEARED",
        "A-SPEC's hypothesis may not cover the d_A = 1 emission that Definition "
        "def:compile adds: a trusted-mode request served with tau_A = [1] where "
        "no certificate is present.",
        "DEFINITION def:compile IS THE NORMATIVE RULE AND IS FOLLOWED. The gap "
        "is recorded in interface.yaml (assumptions.A-SPEC.coverage_gap_note) "
        "and is the G3 signature's judgement call (c), signed as safe 'via "
        "thm:validator-soundness (i)'s independent route' -- check V2 tests tau_A >= 0 and "
        "tr tau_A = 1 on the EMITTED matrix whatever its origin, so D(ii) holds "
        "for the emitted declaration by the validator and not by A-SPEC. Frozen "
        "in G-T-D1-M0 (Group PC-G), whose derivation quotes Theorem thm:gates "
        "(i)'s argument that [1] is not a substituted default.",
    ),
    (
        "CLEARED",
        "Table tab:gateoutcome has NO d_A = 1 row for a present-but-failing "
        "certificate: rows 2, 3 and 4 all carry the scope `at d_A >= 2'.",
        "THE ANSWER IS IN Definition def:compile AND IS NOT IMPROVISED FROM THE "
        "TABLE'S SILENCE: such a request 'is REFUSED exactly as at d_A >= 2 "
        "(Table tab:gateoutcome, row 3) -- a certificate that does not verify "
        "is a DEFECT IN THE SUPPLIED DATA, NOT A WEAKER CLAIM'. Frozen as case "
        "G-T-D1-CERTFAIL, whose `derives_from` field says in as many words that "
        "it is NOT a table row.",
    ),
    (
        "CLEARED",
        "`source_replacement_license` could be mistaken for an assertion of "
        "(SR3) by this module.",
        "IT IS A PASS-THROUGH AND NOTHING ELSE. Theorem thm:certificate-sufficiency (i): (SR3) 'is "
        "decided by NO function of the emitted data'. Theorem thm:gates (i): 'the "
        "compiler TESTS PRESENCE, NEVER TRUTH'. Remark rem:boundary: what it "
        "'may NEVER do is ASSERT (SR3) of a physical apparatus: IT RECORDS THE "
        "ATTESTATION IT WAS GIVEN'. Frozen in SR3_RECORD, whose three rows all "
        "carry `asserted by this module' FALSE, and in NEVER_VERIFIED, which "
        "lists A-RET beside the three supplier obligations.",
    ),
)


# ===========================================================================
#  MARKS -- WHAT 0.3.0 DID TO THE 0.1.4 VALUES, AND WHAT IT DID NOT
#
#  NOTHING BELOW DELETES OR EDITS A FROZEN VALUE. Every entry, every case
#  tuple and every field of Groups PC-A..PC-L is byte-unchanged by the run that
#  wrote these lists: the marks are carried BESIDE the entries, which is what
#  a run-A instance may do, and an entry
#  that is superseded is still readable, still cited, and still evidence of
#  what the 0.1.4 text said.
#
#  THE ONE FACT THAT SHAPES THESE LISTS, AND IT IS NOT THE OBVIOUS ONE. This
#  registry was frozen at 0.1.3 and re-pointed at 0.1.4; IT WAS NEVER AUTHORED
#  AGAINST 0.2.0. So it contains NO tolerance apparatus to mark superseded --
#  no `declared_tolerance` domain, no Feas(theta), no measured gate_report
#  defect, no pivot ratio for (G3)(a), no normalization-defect functional. A
#  reader expecting a long SUPERSEDED_BY_SCOPE list on that ground will not
#  find one, and the absence is a fact about the registry's history rather
#  than an omission by this run.
# ===========================================================================

#: The dated line every supersession mark below is taken under. One line, cited
#: by each mark, so that a reader can check the licence once.
SCOPE_SUPERSESSION_LINE_0_3_0: str = (
    "Run A of the protocol-compiler 0.3.0 implementation band "
    "(B3): superseded BY SCOPE under "
    "the two-instance freeze, against "
    "contract.tex 0.3.0 sha256 (LF) f1441567c99618859890151c990d4e7e47c6cfad"
    "42fa385bd0ce3b8835dbe65d, accepted at the G3. The value is "
    "NOT withdrawn as wrong: it is a correct reading of a superseded text "
    "whose SUBJECT 0.3.0 removed."
)

#: Frozen values whose SUBJECT 0.3.0 removes outright, so that no correct
#: implementation of 0.3.0 can exhibit them. Each row is
#: (holder, sub-case or field, ground).
SUPERSEDED_BY_SCOPE_0_3_0: tuple[tuple[str, str, str], ...] = (
    (
        "VALIDATOR_CASES",
        "V3-block-diagonality",
        "V3's OFF-BLOCK CONDITIONS ARE DELETED. Check V3 at 0.3.0: 'The "
        "off-block conditions of the 0.1.4 validator ARE GONE: an emitted "
        "Q-operator is a block list, so there is NO Pi_s F_v Pi_{s'} or "
        "Pi_s O^_k Pi_{s'} TO EVALUATE and NOTHING THAT COULD BE NON-ZERO. "
        "What replaced them is V1'S SECTOR-MAP COMPARISON, AND NOTHING ELSE "
        "DID.' The case's D(iii) target survives and its MECHANISM does not; "
        "its replacement is frozen in SECTOR_MAP_COMPARISON_CASES.",
    ),
    (
        "WEIGHTED_FAMILY_CASES",
        "SECTOR-fails (block_diagonal=False)",
        "A FAMILY THAT IS NOT SECTOR-BLOCK-DIAGONAL IS NOW INEXPRESSIBLE. "
        "Section 2.5 (`operator_form`): 'Sector-block-diagonality HOLDS BY "
        "CONSTRUCTION; nothing verifies that the off-sector entries are zero, "
        "BECAUSE NOTHING CAN WRITE THEM.' Definition def:exact calls an "
        "off-block entry 'NOT SMALL BUT INEXPRESSIBLE'. So this case's input "
        "cannot be presented to a 0.3.0 compiler at all. Lemma lem:weighted "
        "(ii) survives in its blockwise form -- N_{u,t}^{(s)} = q_t "
        "N_{u|t}^{(s)} -- which the SECTOR-holds case already pins.",
    ),
    (
        "CERTIFICATE_CASES",
        "the fields psi_integer_amplitudes and psi_squared_norm, on all four cases",
        "THE CERTIFICATE DECLARES AN OPERATOR AND NOT A VECTOR. Definition "
        "def:srcert: the datum is Psi in L(A A''), and 'NO CONDITION OF (G2) "
        "IS STATED ON A VECTOR ... the unit vector |psi> EXISTS BY Psi^2 = Psi "
        "and tr Psi = 1 and is NEVER ITSELF DECLARED'. An exact unnormalized "
        "Gaussian-integer vector with its squared norm is exactly the "
        "presentation the type change removed. THE (SR1) AND (SR2) VALUES OF "
        "THOSE CASES ARE NOT SUPERSEDED: they are functions of Psi = "
        "|psi><psi| and are unchanged -- see RESTORED_AT_0_3_0.",
    ),
    (
        "REFUSAL_REASONS_VERBATIM",
        "the tuple read as a COMPLETE list",
        "TWO STRINGS AT 0.1.4, SEVEN AT 0.3.0. Section 2.3 (`refusal`) now "
        "fixes `sector_map_mismatch`, `alice_marginal_trace_rounds`, "
        "`alice_povm_summation_rounds`, `bob_povm_summation_rounds` and "
        "`emitted_value_not_representable` beside the two. BOTH EXISTING "
        "STRINGS REMAIN CORRECT AND ARE NOT WITHDRAWN; what is superseded is "
        "the completeness of the tuple, which the integrity test reads as "
        "'and no third'.",
    ),
    (
        "INPUT_KEYS, OUTPUT_KEYS, COMPILER_ONLY_KEYS, DECLARATION_SLOT_KEYS",
        "each tuple read as a COMPLETE list",
        "TWELVE/TWENTY-ONE AT 0.1.4, THIRTEEN/TWENTY-THREE AT 0.3.0. The "
        "input `target_povm` and the outputs `sector_block_kind` and "
        "`constraint_rhs_tag` are new (Sections 2.2 and 2.3). NO EXISTING KEY "
        "IS REMOVED OR RENAMED, so every name in every tuple is still a "
        "machine key of this module; what is superseded is the count and the "
        "position of the insertions.",
    ),
    (
        "LEDGER_ROWS and the assumption count",
        "the ledger read as TEN rows",
        "ELEVEN AT 0.3.0. A-BLOCK (`block_diagonal_feasible_set`) was added at "
        "the round-9 revision of 0.2.0 and this registry was never authored "
        "against 0.2.0. Section 5's preamble types it: 'a fourth (Assumption "
        "ass:block) is a CONSUMER OBLIGATION of the same kind, named for the "
        "same reason'. THE FOUR-MEMBER NEVER-VERIFIED SET IS UNCHANGED and "
        "A-BLOCK is not in it. The other ten rows keep their machine keys and "
        "their Supports cells, EXCEPT that A-BLOCK's cell adds PC5.",
    ),
    (
        "GATE_CASES",
        "every case recording (G3)(a) as PASSED VACUOUSLY at d_A = 1",
        "THE d_A = 1 VACUOUS PASS IS WITHDRAWN. Remark rem:degenerate: under "
        "the operator form of 0.1.4-0.2.0 it WAS vacuous there; 'UNDER THE "
        "DECLARED TAG IT IS NOT, because an entry tagged `general` DECLARES A "
        "MATRIX AND FAILS A TYPE CHECK AT EVERY DIMENSION ... THIS MODULE "
        "TAKES THE STRICTER READING'. `passed vacuously` survives in "
        "UNTRUSTED-SOURCE MODE ONLY, at any d_A. The withdrawal is "
        "FAIL-CLOSED -- KLE = false where the other reading would emit true -- "
        "and is disclosed in the G3 signature as its item (b).",
    ),
    (
        "GATE_CASES and O-PC-GATES",
        "the MECHANISM of gate (G3)(a) wherever a case records it as a "
        "numerical condition on an operator against c_k tau_A",
        "(G3)(a) IS NOW A TYPE CHECK THAT COMPARES NO NUMBERS. Section 1.1, "
        "design decision 4: it 'was a NUMERICAL TEST of an operator against "
        "c_k tau_A and was ONE-SIDED BY A FACTOR OF TWO. It is now a TYPE "
        "check on the right-hand side's declared tag, COMPARING NO NUMBERS "
        "AND DECIDING EXACTLY.' The licensed/unlicensed AXIS survives and its "
        "MECHANISM does not; the replacement is frozen in RHS_TAG_CASES.",
    ),
)

#: Frozen values whose SUBJECT survives 0.3.0 and whose claim tuple, mechanism
#: or count is stale. RUN B RE-POINTS THESE AND CHANGES NOTHING ELSE ABOUT
#: THEM; none is superseded and none is re-derived.
REPOINT_AT_RUN_B_0_3_0: tuple[tuple[str, str], ...] = (
    (
        "O-PC-VOCABULARY",
        "the key tuples move 12 -> 13 and 21 -> 23, and the fifteen "
        "declaration slots become seventeen. The entry's subject -- the "
        "machine-key vocabulary as frozen tuples -- is unchanged, and so is "
        "its claim tuple (PC1, PC9).",
    ),
    (
        "O-PC-LEDGER",
        "the ledger moves 10 -> 11 rows with A-BLOCK, whose Supports cell "
        "names PC5. The entry's claim tuple (PC7, PC8, PC9, PC11) does NOT "
        "gain PC5: A-BLOCK is an assumption row, and this entry pins the "
        "ledger rather than the claims. The NEGATIVE FORM the entry asserts -- "
        "that no frozen case anywhere records a verdict on (SR3), on an "
        "attack-set licence, on a link's soundness or on a presented receiver "
        "POVM -- SURVIVES 0.3.0 UNCHANGED and must be re-asserted over the new "
        "cases too.",
    ),
    (
        "O-PC-GATES",
        "the seven-axis enumeration survives; two axes' CONTENT moves. The "
        "`list` axis (licensed / unlicensed) is now decided by a tag type "
        "check, and the `alice_dim` axis no longer carries a vacuous (G3)(a) "
        "pass at 1. The exhaustiveness argument is unaffected.",
    ),
    (
        "O-PC-CERTIFICATE",
        "the (SR1)/(SR2) values survive as functions of Psi; the vector "
        "PRESENTATION does not. Its claim tuple (PC10, PC11) is unchanged. "
        "The four cases' sr1_holds / sr2_holds verdicts are NOT re-derived -- "
        "see RESTORED_AT_0_3_0.",
    ),
    (
        "O-PC-VALIDATOR",
        "one case per check survives; V3's case loses its off-block mechanism, "
        "V6's gains the tag, and V7's acquires a THIRD branch (empty list; "
        "default candidate; supplied witness) where 0.1.4 read two. Claim "
        "tuple (PC6) unchanged.",
    ),
    (
        "O-PC-WEIGHTS",
        "Lemma lem:weighted's three parts survive; the EMISSION OBLIGATION on "
        "q_t N_{u|t} is new and is frozen separately in "
        "O-PC-EMISSION-OBLIGATION. Claim tuple (PC2, PC3) unchanged.",
    ),
    (
        "O-PC-FEASIBILITY",
        "the default candidate and the witness rule survive; the verification "
        "is now PER BLOCK, V7 has three branches, and PC5's assumption list "
        "gains A-BLOCK. Claim tuple (PC5, PC6) unchanged.",
    ),
    (
        "O-PC-BB84",
        "every value of Theorem thm:pc12 survives at its closed form; what is "
        "new is the (S) refusal at the decimal literals (frozen in "
        "SUMMATION_CASES) and the DECLARABILITY of Psi (frozen in "
        "CERTIFICATE_OPERATOR_CASES). Claim tuple (PC12, PC8) unchanged. Its "
        "`revalidation` field records the 0.1.4 relocation and is NOT "
        "extended by this run: nothing relocated at 0.3.0.",
    ),
)

#: 0.1.4-era statements that 0.2.0 made wrong and 0.3.0 RESTORES. They are
#: noted as restored and are NOT re-derived: the values stand as computed at
#: 0.1.3 and re-read at 0.1.4.
RESTORED_AT_0_3_0: tuple[tuple[str, str], ...] = (
    (
        "every exact rational in this registry, and the four lines of "
        "rationale in the module docstring that justify them",
        "THE REGISTRY'S OWN READING WAS RIGHT, WENT WRONG AT 0.2.0, AND IS "
        "RIGHT AGAIN. This file froze exact Gaussian rationals from 0.1.3 on "
        "the ground that 'EXACTNESS IS THE FAITHFUL READING of \"finitely many "
        'arithmetic operations": a tolerance would turn a decidable check '
        "into an approximate one'. 0.2.0 added exactly that tolerance and made "
        "the reading wrong. 0.3.0 puts it in the contract: Section 2.5 "
        "(`exact_decisions`), 'every predicate this module decides ... is "
        "decided EXACTLY on the declared dyadic numbers', and 'THIS MODULE "
        "CARRIES NO TOLERANCE'. So the substrate this registry chose is now "
        "the contract's, and NOT ONE VALUE NEEDED RE-DERIVING.",
    ),
    (
        "the exact per-block shape of every operator predicate",
        "0.1.4 decided Hermiticity, positivity and completeness at zero and "
        "per block; 0.2.0 decided them at a window; 0.3.0 decides them at zero "
        "and per block again (Definition def:exact, conditions (H), (P), (C)). "
        "WHAT IS GENUINELY NEW IS (S) AND (T) -- the declared-order sum "
        "rounding nowhere, and the sector map as a TYPE condition -- and "
        "neither has a 0.1.4 counterpart to restore. Both are frozen in "
        "SUMMATION_CASES and SECTOR_MAP_COMPARISON_CASES.",
    ),
    (
        "CERTIFICATE_CASES sr1_holds / sr2_holds, all four cases",
        "(SR1) and (SR2) are read at 0.3.0 exactly as at 0.1.4 -- as EXACT "
        "matrix identities on declared data, decided entry by entry -- after "
        "an interval at 0.2.0 where they were read at a tolerance. Definition "
        "def:srcert: 'NOTHING ELSE IN THIS CONTRACT CHANGED WITH THE TYPE: "
        "(SR1)-(SR3) read as they always did, with |Psi><Psi| replaced by Psi "
        "throughout.' The four verdicts stand unchanged and un-re-derived; "
        "only their PRESENTATION is superseded.",
    ),
    (
        "the one-sidedness of V7, read as a property of ONE branch",
        "0.1.4 read V7 as one-sided on D(vii); 0.3.0 scopes the one-sidedness "
        "to the THIRD branch and states the branch structure once, in "
        "Definition def:validator, 'with every other site quoting it'. Section "
        "1.1: 'WHERE V7 IS ONE-SIDED IS NARROWER THAN A READER OF THE 0.2.0 "
        "TEXT WOULD EXPECT'. This is a NARROWING of an existing statement and "
        "not a new one, so the frozen one-sidedness counterexample stands.",
    ),
)

#: Entries this run examined and did NOT mark, recorded because a mark list is
#: only checkable against the list of things deliberately left off it.
NOT_MARKED_AT_0_3_0: tuple[tuple[str, str], ...] = (
    (
        "O-PC-TYPING, O-PC-SIFTING, O-PC-CHAIN, O-PC-CONSERVATIVE, "
        "O-PC-SR-BOUNDARY, O-PC-CONJUGATION, O-PC-WELLPOSED, "
        "O-PC-FIXED-FRACTION-REFUSAL, O-PC-PARTIAL-PHI",
        "NOTHING 0.3.0 CHANGED REACHES THEM. The compilation map's slot "
        "filling, the key map and its two r_h extensions, the chain record "
        "field for field, the conservative inclusion, the interchange law, the "
        "conjugation branch pair, the well-posedness of the Lowner comparison, "
        "the fixed_fraction refusal and the partial-phi refusal are all stated "
        "at 0.3.0 in the same terms. Two carry a NEW READING that changes no "
        "frozen value: O-PC-CHAIN's (C4)/(S3) are now exact decisions rather "
        "than tolerance predicates (Definition def:chaincond, 'The tolerance "
        "predicates a chain engaged through 0.2.0 -- FOUR OF THEM -- are now "
        "four exact decisions'), which RESTORES the 0.1.4 reading; and "
        "O-PC-CONSERVATIVE's inclusion is now available at every m >= 0 while "
        "the ROW-4 OUTCOME is unchanged, for the attestation reason frozen in "
        "GATE_OUTCOME_CELLS_0_3_0/G-CELL-trusted-d2-absent-m1.",
    ),
    (
        "SR3_RECORD",
        "(SR3) IS UNCHANGED BY THE TYPE CHANGE. It 'carries no number, is not "
        "decidable, and is tested for presence only' at 0.3.0 exactly as at "
        "0.1.4, and all three rows keep `asserted by this module` FALSE.",
    ),
    (
        "GATE_VERDICT_VOCABULARY",
        "THREE VALUES AT 0.3.0 AS AT 0.1.4 -- `passed`, `failed`, `passed "
        "vacuously`. What moved is WHEN the third is required (untrusted mode "
        "only), not the vocabulary; that move is marked against GATE_CASES.",
    ),
    (
        "LINK_STATUS_VOCABULARY, INDEXED_ALPHABETS, NOT_OUTPUTS, "
        "INADMISSIBLE_SOURCES, KINDS",
        "UNCHANGED AT 0.3.0. The three link statuses, the nine indexed "
        "alphabets in Definition def:compile's order, the two not-outputs with "
        "their owners, and the two imported guards are as at 0.1.4. T_pub is "
        "still not among the nine, and 0.3.0 is merely the first version to "
        "say so in as many words.",
    ),
    (
        "CHANGE_REQUEST_CANDIDATES",
        "NOT REOPENED, AND ONE OF ITS CLEARED ITEMS IS NOW CLEARED BY THE "
        "TEXT ITSELF. The item recording that Table tab:gateoutcome has no "
        "d_A = 1 row for a present-but-failing certificate was cleared at "
        "0.1.4 by reading Definition def:compile; at 0.3.0 row 3 CARRIES THE "
        "SCOPE 'at any d_A' IN ITS OWN TEXT, so the clearance no longer rests "
        "on a cross-reference. That is a strengthening of an existing "
        "disposition and not a new candidate.",
    ),
)


# ===========================================================================
#  The partition, recorded so that the cut can be checked
# ===========================================================================
#
#  THIS REGISTRY IS PARTITIONED INTO THREE FILES. The tuple below is
#  the original single file's ``__all__``, carried here WHOLE and as a list of NAMES
#  rather than of values: it is what lets
#  ``test_protocol_compiler_registry_partition.py`` assert that the cut lost
#  nothing and invented nothing. Three names of it are gone from every half and
#  are listed in ``RETIRED_BY_THE_PARTITION`` below, with the reason.
#
#  WHAT WENT WHERE:
#    * group PC-H and ``O-PC-CERTIFICATE-OPERATOR`` -> registry_transmitter.py,
#      because PC10 and PC11 are ``transmitter`` claims;
#    * groups PC-I and PC-J -> registry_instances_bb84.py, because the worked
#      BB84 declaration and the conjugation pair are an INSTANCE and not claims;
#    * everything else stayed here.

ORIGINAL_REGISTRY_NAMES: tuple[str, ...] = (
    "ASSURANCE",
    "BB84_ALPHABETS",
    "BB84_CASES",
    "BB84_D_VERDICTS",
    "BB84_GATE_VERDICTS",
    "BB84_KEY_MAP",
    "BB84_PHI",
    "CERTIFICATE_CASES",
    "CERTIFICATE_OPERATOR_CASES",
    "CHAIN_CASES",
    "CHANGE_REQUEST_CANDIDATES",
    "COMPILER_ONLY_KEYS",
    "CONJUGATION_BRANCHES",
    "CONSISTENCY_CRITERION_CASES",
    "DECIDABILITY_COUNTS",
    "DECLARATION_SLOT_KEYS",
    "DECLARED_ORDER_CASES",
    "DIMENSION_ONE_EQUALITIES",
    "EMISSION_REPRESENTABILITY_CASES",
    "FEASIBLE_SET_COMPARISONS",
    "FL_NINE_TENTHS",
    "FL_NINE_TENTHS_PLUS_ONE_TENTH",
    "FL_ONE_TENTH",
    "GATE_AXES",
    "GATE_CASES",
    "GATE_CONSISTENCY_RULES",
    "GATE_OUTCOME_CELLS_0_3_0",
    "GATE_VERDICT_VOCABULARY",
    "INADMISSIBLE_SOURCES",
    "INDEXED_ALPHABETS",
    "INDEX_MAP_CASES",
    "INPUT_KEYS",
    "JOINT_DISTRIBUTION_CASES",
    "KEY_MAP_CASES",
    "KINDS",
    "LEDGER_ROWS",
    "LINK_STATUS_VOCABULARY",
    "NEVER_VERIFIED",
    "NOT_MARKED_AT_0_3_0",
    "NOT_OUTPUTS",
    "OUTPUT_KEYS",
    "PC_ORACLES",
    "PERP",
    "RECONSTRUCTION_CASES",
    "REFUSAL_REASONS_VERBATIM",
    "REPOINT_AT_RUN_B_0_3_0",
    "RESTORED_AT_0_3_0",
    "RHS_TAG_CASES",
    "SCOPE_SUPERSESSION_LINE_0_3_0",
    "SECTOR_MAP_COMPARISON_CASES",
    "SR3_RECORD",
    "SUMMATION_CASES",
    "SUPERSEDED_BY_SCOPE_0_3_0",
    "VALIDATOR_CASES",
    "WEIGHTED_FAMILY_CASES",
    "WITNESS_CASES",
    "WITNESS_LEG_FAILURES",
    "BB84Case",
    "CertificateCase",
    "CertificateOperatorCase",
    "ChainCase",
    "ChainLink",
    "ConjugationBranch",
    "ConsistencyCriterionCase",
    "DecidabilityCount",
    "DeclaredOrderCase",
    "DimensionOneEquality",
    "EmissionRepresentabilityCase",
    "FeasibleSetComparison",
    "GateCase",
    "GateConsistencyRule",
    "GateOutcomeCell",
    "Gauss",
    "IndexMapCase",
    "JointDistributionCase",
    "KeyMapCase",
    "LedgerRow",
    "Matrix",
    "PCOracleEntry",
    "ReconstructionCase",
    "RhsTagCase",
    "SectorMapComparisonCase",
    "SummationCase",
    "ValidatorCase",
    "WeightedFamilyCase",
    "WitnessCase",
    "gz",
    "pc_oracle",
    "real_matrix",
)

#: WHAT THE PARTITION NARROWED RATHER THAN RETIRED. ``PC_ORACLES`` and
#: ``pc_oracle`` keep their names and answer for THIS HALF ONLY; the other two
#: halves carry ``TRANSMITTER_PC_ORACLES`` / ``transmitter_pc_oracle`` and
#: ``BB84_PC_ORACLES`` / ``bb84_pc_oracle``. One tuple over three files would
#: make this half name the other two, and the dependency has to run one way --
#: this half must be readable, and deletable, without them. A caller that wants
#: an entry by id across the three asks all three accessors; the partition test
#: asserts that exactly one of them answers.
PARTITION_NARROWED: tuple[tuple[str, str], ...] = (
    (
        "PC_ORACLES",
        "one tuple over three files would make this half name the other two; "
        "it is PC_ORACLES here, TRANSMITTER_PC_ORACLES and BB84_PC_ORACLES "
        "there, and the partition test asserts the three are disjoint and "
        "complete against the original twenty-four",
    ),
    (
        "pc_oracle",
        "the accessor is narrowed with its tuple and refuses an id that left "
        "this half, which is what makes a stale lookup a loud failure instead "
        "of a silent None; transmitter_pc_oracle and bb84_pc_oracle answer for "
        "the other two",
    ),
)
