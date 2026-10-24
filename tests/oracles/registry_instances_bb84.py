"""The BB84 instance's half of the frozen ``protocol-compiler`` registry.

WHAT THIS FILE IS AND WHY IT EXISTS SEPARATELY. Every value below was derived
BY HAND by run A of the G4 band, before any implementation of
what it pins existed, and it is under that freeze still: an oracle registry
"moves with its module and is never regenerated from the code it tests"
(PRINCIPLES.md section 2.3).

THE INSTANCE IS DATA AND NOT A CLAIM (PRINCIPLES.md section 5). The worked BB84
declaration was PC12 and the conjugation pair ``ex:conj`` in the compiler's
contract; here they are ``instances/bb84/`` -- a
constructor module (``specification.py``) and a parameters file, with
developer notes in ``NOTES.md`` -- and NO CLAIM OF THE COMPILER DEPENDS ON
THEM. The worked derivations live HERE, in the ``derivation`` and
``arithmetic`` fields below, and not in any document of the instance: these
two entries are the instance's executable memory.

THE ``claims`` TUPLES STILL READ ``PC12``, AND THAT IS DELIBERATE: it is the id
the derivation was written against and it is history. Re-labelling it would be
editing frozen evidence to agree with a later structure.

THE CUT IS CHECKED AND NOT TRUSTED:
``tests/oracles/test_protocol_compiler_registry_partition.py`` asserts that the
three halves are disjoint, that their union is the original
``__all__``, that the compiler's half names nothing in this one, and that the
oracle entries are partitioned and complete.

WHAT CAME ACROSS: groups PC-I and PC-J whole -- the alphabets, the key map,
``phi``, the three weight pairs with their emitted matrices and D-verdicts, the
gate verdicts, ``O-PC-BB84``, and the conjugation branch pair with
``O-PC-CONJUGATION``.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

from registry_protocol_compiler import (
    PERP,
    Matrix,
    PCOracleEntry,
    gz,
    real_matrix,
)

__all__ = [
    "BB84_ALPHABETS",
    "BB84_CASES",
    "BB84_D_VERDICTS",
    "BB84_GATE_VERDICTS",
    "BB84_KEY_MAP",
    "BB84_PC_ORACLES",
    "BB84_PHI",
    "CONJUGATION_BRANCHES",
    "BB84Case",
    "ConjugationBranch",
    "bb84_pc_oracle",
]



# ===========================================================================
#  Group PC-I -- the source-replacement BB84 declaration (PC12)
# ===========================================================================
#
#  The Band-A worked instance, emitted field for field. THE ALPHABETS, THE
#  ANNOUNCEMENT MAPS, THE SIFTING PREDICATE AND phi ARE THE SAME AT EVERY WEIGHT
#  PAIR -- only the four weights move -- so they are frozen once, below, and the
#  three BB84Case records carry what depends on the weights.

#: X, V, C_A, C_B, Chat, Z_perp, in the emitted order. Their cardinalities are
#: 4, 4, 3, 3, 4, 3, which is exactly what the proof of Theorem thm:pc12 (ii)
#: writes out; |K| = |C_A| |C_B| = 9.
BB84_ALPHABETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("X", ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")),
    ("V", ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")),
    ("C_A", ("Z", "(X,0)", "(X,1)")),
    ("C_B", ("Z", "(X,0)", "(X,1)")),
    ("Chat", ("gen", "ok", "err", "disc")),
    ("Z_perp", ("0", "1", "perp")),
)

#: phi of Eq. eq:bb84phi, TOTAL on the nine-element K, as (c_A, c_B) -> value.
BB84_PHI: tuple[tuple[str, str, str], ...] = (
    ("Z", "Z", "gen"),
    ("Z", "(X,0)", "disc"),
    ("Z", "(X,1)", "disc"),
    ("(X,0)", "Z", "disc"),
    ("(X,1)", "Z", "disc"),
    ("(X,0)", "(X,0)", "ok"),
    ("(X,1)", "(X,1)", "ok"),
    ("(X,0)", "(X,1)", "err"),
    ("(X,1)", "(X,0)", "err"),
)

#: r of Eq. eq:rdef on X x V. Theorem thm:pc12 (iv): a when b = b' = Z, else
#: perp. Sixteen cells, written out.
BB84_KEY_MAP: tuple[tuple[str, str, int | str], ...] = (
    ("(Z,0)", "(Z,0)", 0),
    ("(Z,0)", "(Z,1)", 0),
    ("(Z,1)", "(Z,0)", 1),
    ("(Z,1)", "(Z,1)", 1),
    ("(Z,0)", "(X,0)", PERP),
    ("(Z,0)", "(X,1)", PERP),
    ("(Z,1)", "(X,0)", PERP),
    ("(Z,1)", "(X,1)", PERP),
    ("(X,0)", "(Z,0)", PERP),
    ("(X,0)", "(Z,1)", PERP),
    ("(X,1)", "(Z,0)", PERP),
    ("(X,1)", "(Z,1)", PERP),
    ("(X,0)", "(X,0)", PERP),
    ("(X,0)", "(X,1)", PERP),
    ("(X,1)", "(X,0)", PERP),
    ("(X,1)", "(X,1)", PERP),
)


@dataclass(frozen=True)
class BB84Case:
    """The emitted BB84 declaration at one named pair of basis weights."""

    case_id: str
    alice_weights: tuple[F, F]
    bob_weights: tuple[F, F]
    dyadic: bool
    tau_a: Matrix
    #: M_{(b,a)} in the order of BB84_ALPHABETS' X.
    alice_povm: tuple[Matrix, ...]
    #: F_{(b',y)} in the order of BB84_ALPHABETS' V.
    bob_povm: tuple[Matrix, ...]
    #: tr_A[(M_{(b,a)} (x) 1)|Phi^+><Phi^+|], aligned with alice_povm.
    sr2_values: tuple[Matrix, ...]
    #: p_{(b,a)} rho_{(b,a)}, aligned. Equal to sr2_values entry by entry.
    sr2_expected: tuple[Matrix, ...]
    #: P_D[omega] at omega = |Phi^+><Phi^+|, row x and column v.
    joint: tuple[tuple[F, ...], ...]
    #: Phi[omega] on (gen, ok, err, disc).
    phi_vector: tuple[F, F, F, F]
    phi_total: F
    #: The Bob-basis marginals (b' = Z, b' = X) of Remark rem:bb84checks.
    bob_basis_marginals: tuple[F, F]
    #: The Alice-basis marginals (b = Z, b = X), the same check on the other side.
    alice_basis_marginals: tuple[F, F]
    arithmetic: str


BB84_CASES: tuple[BB84Case, ...] = (
    BB84Case(
        case_id="BB84-w1-symmetric-dyadic",
        alice_weights=(F(1, 2), F(1, 2)),
        bob_weights=(F(1, 2), F(1, 2)),
        dyadic=True,
        tau_a=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        alice_povm=(
            real_matrix(((F(1, 2), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(1, 2)))),
            real_matrix(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4)))),
            real_matrix(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4)))),
        ),
        bob_povm=(
            real_matrix(((F(1, 2), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(1, 2)))),
            real_matrix(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4)))),
            real_matrix(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4)))),
        ),
        sr2_values=(
            real_matrix(((F(1, 4), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(1, 4)))),
            real_matrix(((F(1, 8), F(1, 8)), (F(1, 8), F(1, 8)))),
            real_matrix(((F(1, 8), F(-1, 8)), (F(-1, 8), F(1, 8)))),
        ),
        sr2_expected=(
            real_matrix(((F(1, 4), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(1, 4)))),
            real_matrix(((F(1, 8), F(1, 8)), (F(1, 8), F(1, 8)))),
            real_matrix(((F(1, 8), F(-1, 8)), (F(-1, 8), F(1, 8)))),
        ),
        joint=(
            (F(1, 8), F(0), F(1, 16), F(1, 16)),
            (F(0), F(1, 8), F(1, 16), F(1, 16)),
            (F(1, 16), F(1, 16), F(1, 8), F(0)),
            (F(1, 16), F(1, 16), F(0), F(1, 8)),
        ),
        phi_vector=(F(1, 4), F(1, 4), F(0), F(1, 2)),
        phi_total=F(1),
        bob_basis_marginals=(F(1, 2), F(1, 2)),
        alice_basis_marginals=(F(1, 2), F(1, 2)),
        arithmetic="""\
THE SYMMETRIC DYADIC INSTANCE, p^A_Z = p^A_X = p^B_Z = p^B_X = 1/2. Every number
below has a power of two as denominator.
EMITTED MATRICES, Eq. eq:bb84data. M_{(b,a)} = p^A_b |conj(a^b)><conj(a^b)| and
F_{(b',y)} = p^B_{b'} |y^{b'}><y^{b'}|. All four BB84 states are REAL in the
declared basis, so conj is the identity on them and the bar is invisible here --
see Remark rem:bb84checks and Group PC-J. At weight 1/2:
  M_{(Z,0)} = [[1/2, 0], [0, 0]] , M_{(Z,1)} = [[0, 0], [0, 1/2]] ,
  M_{(X,0)} = [[1/4, 1/4], [1/4, 1/4]] , M_{(X,1)} = [[1/4, -1/4], [-1/4, 1/4]] .
COMPLETENESS: the four sum entrywise to (0,0): 1/2 + 1/4 + 1/4 = 1;
(1,1): 1/2 + 1/4 + 1/4 = 1; (0,1) and (1,0): 1/4 - 1/4 = 0. So sum = 1_A, which
is Lemma lem:weighted (i) with choice alphabet (Z, X). Bob's family is the same
four matrices at the same weights.
(SR1): tr_{A'}|Phi^+><Phi^+| = 1_A/2 = tau_A.
(SR2) at all four x, by Eq. eq:transpose-trick's first identity
tr_1[(Y (x) 1)|Phi^+><Phi^+|] = (1/2) Y^T:
  (Z,0) : (1/2)(1/2)|0><0| = (1/4)|0><0| = p_{(Z,0)} rho_{(Z,0)} ;
  (Z,1) : (1/4)|1><1| ;
  (X,0) : (1/4)|+><+| = [[1/8, 1/8], [1/8, 1/8]] ;
  (X,1) : (1/4)|-><-| .
  with p_{(b,a)} = p^A_b/2 = 1/4 throughout. ALL FOUR HOLD.
Eq. eq:bb84stats CELL BY CELL, P = (1/2) p^A_b p^B_{b'} |<a^b|y^{b'}>|^2 with
|<a^Z|y^Z>|^2 = |<a^X|y^X>|^2 = delta_{ay} and |<a^b|y^{b'}>|^2 = 1/2 for
b != b':
  matched, agreeing  : (1/2)(1/2)(1/2)(1)   = 1/8
  matched, disagreeing: 0
  mismatched          : (1/2)(1/2)(1/2)(1/2) = 1/16
which is the 4x4 table above. TOTAL MASS: 4 x 1/8 + 8 x 1/16 = 1/2 + 1/2 = 1.
THE FOUR-ENTRY Phi VECTOR on (gen, ok, err, disc):
  gen  = p^A_Z p^B_Z = 1/4 -- the (Z,.)x(Z,.) block, 1/8 + 0 + 0 + 1/8 ;
  ok   = p^A_X p^B_X = 1/4 -- the agreeing X cells, 1/8 + 1/8 ;
  err  = 0            -- the disagreeing X cells, 0 + 0 ; THE NOISELESS LIMIT ;
  disc = p^A_Z p^B_X + p^A_X p^B_Z = 1/4 + 1/4 = 1/2 -- the eight mismatched
         cells, 8 x 1/16 .
  TOTAL 1/4 + 1/4 + 0 + 1/2 = 1, as Theorem thm:measurements-and-statistics (iv) requires and as
  (p^A_Z + p^A_X)(p^B_Z + p^B_X) = 1 . 1 = 1 predicts.
THE Remark rem:bb84checks EXACTNESS CHECK: summing the emitted distribution over
everything but Bob's basis gives p^B_{b'} EXACTLY. b' = Z: the two Z columns sum
to (1/8 + 0 + 1/16 + 1/16) + (0 + 1/8 + 1/16 + 1/16) = 1/4 + 1/4 = 1/2 = p^B_Z.
b' = X: 1/2 = p^B_X. The Alice-side marginals are 1/2 and 1/2 likewise. THAT IS
Eq. eq:choicemass VISIBLE IN THE INSTANCE, and it holds "for this and for every
other state".""",
    ),
    BB84Case(
        case_id="BB84-w2-asymmetric-dyadic",
        alice_weights=(F(7, 8), F(1, 8)),
        bob_weights=(F(3, 4), F(1, 4)),
        dyadic=True,
        tau_a=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        alice_povm=(
            real_matrix(((F(7, 8), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(7, 8)))),
            real_matrix(((F(1, 16), F(1, 16)), (F(1, 16), F(1, 16)))),
            real_matrix(((F(1, 16), F(-1, 16)), (F(-1, 16), F(1, 16)))),
        ),
        bob_povm=(
            real_matrix(((F(3, 4), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(3, 4)))),
            real_matrix(((F(1, 8), F(1, 8)), (F(1, 8), F(1, 8)))),
            real_matrix(((F(1, 8), F(-1, 8)), (F(-1, 8), F(1, 8)))),
        ),
        sr2_values=(
            real_matrix(((F(7, 16), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(7, 16)))),
            real_matrix(((F(1, 32), F(1, 32)), (F(1, 32), F(1, 32)))),
            real_matrix(((F(1, 32), F(-1, 32)), (F(-1, 32), F(1, 32)))),
        ),
        sr2_expected=(
            real_matrix(((F(7, 16), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(7, 16)))),
            real_matrix(((F(1, 32), F(1, 32)), (F(1, 32), F(1, 32)))),
            real_matrix(((F(1, 32), F(-1, 32)), (F(-1, 32), F(1, 32)))),
        ),
        joint=(
            (F(21, 64), F(0), F(7, 128), F(7, 128)),
            (F(0), F(21, 64), F(7, 128), F(7, 128)),
            (F(3, 128), F(3, 128), F(1, 64), F(0)),
            (F(3, 128), F(3, 128), F(0), F(1, 64)),
        ),
        phi_vector=(F(21, 32), F(1, 32), F(0), F(5, 16)),
        phi_total=F(1),
        bob_basis_marginals=(F(3, 4), F(1, 4)),
        alice_basis_marginals=(F(7, 8), F(1, 8)),
        arithmetic="""\
THE ASYMMETRIC DYADIC INSTANCE, p^A = (7/8, 1/8) and p^B = (3/4, 1/4) -- the
biased-basis regime a real protocol uses, and chosen so that the two parties'
biases DIFFER, which the symmetric case cannot show.
EMITTED MATRICES: M_{(Z,a)} = (7/8)|a><a| and
M_{(X,a)} = (1/8)|a^X><a^X| = [[1/16, +-1/16], [+-1/16, 1/16]]; Bob's at 3/4 and
1/4. Completeness on Alice's side, entrywise: (0,0): 7/8 + 1/16 + 1/16 = 1;
(1,1): the same; off-diagonals 1/16 - 1/16 = 0. On Bob's: 3/4 + 1/8 + 1/8 = 1.
tau_A IS UNCHANGED AT 1_A/2, and that is worth noticing: the marginal of
|Phi^+> does not depend on the weights at all, so (SR1) is the same identity at
every weight pair. WHAT DOES MOVE IS (SR2), whose value carries p^A_b/2:
  (Z,a) : (7/16)|a><a| = p_{(Z,a)} rho_{(Z,a)} with p_{(Z,a)} = 7/16 ;
  (X,a) : (1/16)|a^X><a^X| = [[1/32, +-1/32], [+-1/32, 1/32]] with
          p_{(X,a)} = 1/16 . ALL FOUR HOLD.
Eq. eq:bb84stats, the four distinct cell values:
  matched Z, agreeing : (1/2)(7/8)(3/4)      = 21/64
  matched X, agreeing : (1/2)(1/8)(1/4)      = 1/64
  b = Z, b' = X       : (1/2)(7/8)(1/4)(1/2) = 7/128
  b = X, b' = Z       : (1/2)(1/8)(3/4)(1/2) = 3/128
TOTAL MASS over the common denominator 128:
  2 x 42 + 2 x 2 + 4 x 7 + 4 x 3 = 84 + 4 + 28 + 12 = 128 . EXACTLY ONE.
Phi = (p^A_Z p^B_Z, p^A_X p^B_X, 0, p^A_Z p^B_X + p^A_X p^B_Z)
    = (21/32, 1/32, 0, 7/32 + 3/32 = 10/32 = 5/16), summing over 32nds to
21 + 1 + 0 + 10 = 32. NOTE HOW UNEVEN IT IS: 21/32 of the mass is generation and
1/32 is the test statistic that carries the error information. THAT IS THE POINT
OF A BIASED BASIS, and it is visible in the emitted declaration without any
state-independent fraction anywhere -- which is the output_state convention.
THE EXACTNESS CHECK, both sides. Bob: the two Z columns sum to
(21/64 + 0 + 3/128 + 3/128) + (0 + 21/64 + 3/128 + 3/128) = 3/8 + 3/8 = 3/4
= p^B_Z, and the X columns to 1/4 = p^B_X. Alice: the two Z rows sum to
(21/64 + 0 + 7/128 + 7/128) + (0 + 21/64 + 7/128 + 7/128) = 7/16 + 7/16 = 7/8
= p^A_Z, and the X rows to 1/8 = p^A_X. FOUR EXACT AGREEMENTS, none of which
would be exact under a fixed-fraction encoding.""",
    ),
    BB84Case(
        case_id="BB84-w3-non-dyadic",
        alice_weights=(F(2, 3), F(1, 3)),
        bob_weights=(F(4, 5), F(1, 5)),
        dyadic=False,
        tau_a=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        alice_povm=(
            real_matrix(((F(2, 3), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(2, 3)))),
            real_matrix(((F(1, 6), F(1, 6)), (F(1, 6), F(1, 6)))),
            real_matrix(((F(1, 6), F(-1, 6)), (F(-1, 6), F(1, 6)))),
        ),
        bob_povm=(
            real_matrix(((F(4, 5), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(4, 5)))),
            real_matrix(((F(1, 10), F(1, 10)), (F(1, 10), F(1, 10)))),
            real_matrix(((F(1, 10), F(-1, 10)), (F(-1, 10), F(1, 10)))),
        ),
        sr2_values=(
            real_matrix(((F(1, 3), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(1, 3)))),
            real_matrix(((F(1, 12), F(1, 12)), (F(1, 12), F(1, 12)))),
            real_matrix(((F(1, 12), F(-1, 12)), (F(-1, 12), F(1, 12)))),
        ),
        sr2_expected=(
            real_matrix(((F(1, 3), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(1, 3)))),
            real_matrix(((F(1, 12), F(1, 12)), (F(1, 12), F(1, 12)))),
            real_matrix(((F(1, 12), F(-1, 12)), (F(-1, 12), F(1, 12)))),
        ),
        joint=(
            (F(4, 15), F(0), F(1, 30), F(1, 30)),
            (F(0), F(4, 15), F(1, 30), F(1, 30)),
            (F(1, 15), F(1, 15), F(1, 30), F(0)),
            (F(1, 15), F(1, 15), F(0), F(1, 30)),
        ),
        phi_vector=(F(8, 15), F(1, 15), F(0), F(2, 5)),
        phi_total=F(1),
        bob_basis_marginals=(F(4, 5), F(1, 5)),
        alice_basis_marginals=(F(2, 3), F(1, 3)),
        arithmetic="""\
THE DELIBERATELY NON-DYADIC INSTANCE, p^A = (2/3, 1/3) and p^B = (4/5, 1/5). The
denominators 3 and 5 are ODD, so NOT ONE of these numbers is a binary floating-
point value, and run B's exact-to-machine conversion boundary is forced into the
open rather than hidden behind a fixture that happens to convert without loss.
WEIGHTS ARE A FIXTURE CHOICE: Definition def:bb84spec requires only
p^A_Z, p^A_X > 0 with sum 1, and likewise on Bob's side. NOTHING IN THE CONTRACT
PREFERS A DYADIC WEIGHT, and an implementation that was exact only on dyadic
fixtures would pass BB84-w1 and BB84-w2 and be wrong here.
EMITTED MATRICES: M_{(X,a)} = (1/3)|a^X><a^X| = [[1/6, +-1/6], [+-1/6, 1/6]] and
F_{(X,y)} = (1/5)|y^X><y^X| = [[1/10, +-1/10], [+-1/10, 1/10]]. Completeness:
2/3 + 1/6 + 1/6 = 1 and 4/5 + 1/10 + 1/10 = 1, exactly.
(SR2) values carry p^A_b/2: (1/3)|a><a| in the Z rows and
(1/6)|a^X><a^X| = [[1/12, +-1/12], [+-1/12, 1/12]] in the X rows, matching
p_{(Z,a)} = 1/3 and p_{(X,a)} = 1/6. ALL FOUR HOLD.
Eq. eq:bb84stats, over the common denominator 30:
  matched Z, agreeing : (1/2)(2/3)(4/5)      = 4/15  = 8/30
  matched X, agreeing : (1/2)(1/3)(1/5)      = 1/30
  b = Z, b' = X       : (1/2)(2/3)(1/5)(1/2) = 1/30
  b = X, b' = Z       : (1/2)(1/3)(4/5)(1/2) = 1/15  = 2/30
TOTAL: 2 x 8 + 2 x 1 + 4 x 1 + 4 x 2 = 16 + 2 + 4 + 8 = 30 over 30. EXACTLY ONE
-- and it is exactly one only because the arithmetic is exact; the same sum in
binary64 is not 1.
Phi = (8/15, 1/15, 0, 2/5) = (16, 2, 0, 12)/30, summing to 30/30 = 1. Compare
the closed form: gen = (2/3)(4/5) = 8/15; ok = (1/3)(1/5) = 1/15; err = 0;
disc = (2/3)(1/5) + (1/3)(4/5) = 2/15 + 4/15 = 6/15 = 2/5.
THE EXACTNESS CHECK: Bob's Z columns sum to 2/5 + 2/5 = 4/5 = p^B_Z and the X
columns to 1/5; Alice's Z rows to 1/3 + 1/3 = 2/3 = p^A_Z and the X rows to 1/3.
FOUR EXACT AGREEMENTS AT ODD DENOMINATORS.""",
    ),
)


#: Theorem thm:pc12 (ii)-(iv): the D-verdicts, each with the route the proof
#: takes, and the gate verdicts. Weight-independent, so frozen once.
BB84_D_VERDICTS: tuple[tuple[str, bool, str], ...] = (
    (
        "D(i)",
        True,
        "A and Q are qubits; |X| = |V| = 4, |C_A| = |C_B| = 3, |Chat| = 4, "
        "|Z_perp| = 3, and phi of Eq. eq:bb84phi is TOTAL on the nine-element K "
        "BY ITS LAST CASE (`disc' otherwise); the remaining maps are total by "
        "inspection. Route: Theorem thm:pc12 (ii), and check V1.",
    ),
    (
        "D(ii)",
        True,
        "tau_A = 1_A/2 is positive semidefinite with trace 1. TWO ROUTES, both "
        "available: check V2 on the emitted matrix, and (SR1) via the proof of "
        "Theorem thm:typing's D(ii) clause, which is what makes the emitted "
        "marginal THE CERTIFICATE'S marginal.",
    ),
    (
        "D(iii)",
        True,
        "Alice's family is a POVM by Lemma lem:weighted (i) applied with choice "
        "alphabet (Z, X), weights p^A_b and the conditional projective "
        "measurements {|conj(a^b)><conj(a^b)|}_a -- complete for each b BECAUSE "
        "CONJUGATION MAPS AN ORTHONORMAL BASIS TO AN ORTHONORMAL BASIS. Bob's "
        "likewise. The sector condition is VACUOUS by Theorem thm:band-a (i), "
        "|S| = 1. Route: Theorem thm:pc12 (ii).",
    ),
    (
        "D(iv)",
        True,
        "By Theorem thm:sifting-and-key, whose SIDE CONDITION is met because "
        "r^0_A((b,a), kappa) = a returns a value in {0, 1} = Z.",
    ),
    ("D(v)", True, "By Theorem thm:sifting-and-key (ii), announcement-determined sifting."),
    ("D(vi)", True, "VACUOUS at m = 0: the constraint list is empty."),
    (
        "D(vii)",
        True,
        "By Theorem thm:feasibility (i): CList is empty, so the default witness "
        "Eq. eq:witness-empty applies and omega^* = tau_A (x) 1_Q/2 "
        "= 1_{AQ}/4 lies in W. V7 passes by its FIRST branch.",
    ),
    ("D(viii)", True, "By Theorem thm:sifting-and-key (iii), party computability."),
)

#: Theorem thm:pc12 (iii): the gate verdicts. Case G-T-D2-CERT-M0 of Group PC-G.
BB84_GATE_VERDICTS: tuple[tuple[str, bool | None, str | None, str], ...] = (
    (
        "G1",
        True,
        "passed",
        "V1-V6 and V8 by Theorem thm:pc12 (ii) with the COMPLETENESS half "
        "Theorem thm:validator-soundness (ii), and V7 by its first branch since CList is empty.",
    ),
    (
        "G2",
        True,
        "passed",
        "APPLIES because the marginal slot is filled and d_A = 2 >= 2; its "
        "CHECKABLE half is (SR1)-(SR2), verified in part (i), LEAVING THE "
        "ATTESTATION. So the declaration is key-length-eligible EXACTLY WHEN "
        "(SR3) is supplied.",
    ),
    (
        "G3a",
        False,
        None,
        "NOT ENGAGED: the premise is m >= 1 and m = 0.",
    ),
    (
        "G3b",
        False,
        None,
        "NOT ENGAGED, for the same reason. No attack-set licence is declared "
        "(Definition def:bb84spec, constraints: 'none, and no attack-set "
        "licence') and none is demanded.",
    ),
)


O_PC_BB84 = PCOracleEntry(
    oracle_id="O-PC-BB84",
    claims=("PC12", "PC8"),
    kind="toy-instance",
    subject=(
        "Definition def:bb84spec and Theorem thm:pc12 (i)-(v): the emitted "
        "source-replacement BB84 declaration field for field at three named "
        "weight pairs, one asymmetric and one NON-DYADIC; the alphabet "
        "cardinalities and |K|; the certificate with its (SR1)/(SR2) values; "
        "the D(i)-D(viii) verdicts with routes; the gate verdicts including the "
        "non-vacuity witness; Chat_key; the key map; Eq. eq:bb84stats cell by "
        "cell; the four-entry Phi vector and its total mass; and the Remark "
        "rem:bb84checks exactness check on both sides."
    ),
    derivation="""\
contract.tex 0.1.4 Definition def:bb84spec, Eq. eq:bb84phi, Theorem thm:pc12
(i)-(v), Eq. eq:bb84data, Eq. eq:bb84stats, Eq. eq:transpose-trick, Eq. eq:chkey,
Remark rem:bb84checks and Remark rem:bb84notclaim.

WHAT THE INSTANCE IS AND IS NOT. It is an INSTANCE, not a theorem of its own:
"what is proved is that the emitted object satisfies THIS CONTRACT'S OWN
CONDITIONS". Remark rem:bb84notclaim: no key rate, no acceptance set, no
honest-channel model and no comparison with published numbers appears; the
distribution is "A CONSISTENCY CHECK OF THE EMITTED DECLARATION AT ONE NAMED
STATE, not an honest statistics model", and the declared receiver is an
IDEALIZATION carried as Assumption ass:ideal.

THE ONE ALGEBRAIC TOOL, Eq. eq:transpose-trick, and the one place its symmetric
reading is used. For any qubit operator Y,
  tr_1[(Y (x) 1)|Phi^+><Phi^+|] = (1/2) Y^T   and
  tr[(Y (x) Y')|Phi^+><Phi^+|] = (1/2) tr[Y^T Y'] ,
both from |Phi^+><Phi^+| = (1/2) sum_{i,j} |i><j| (x) |i><j|. (SR1) is the ONE
application that traces the SECOND factor, and thm:pc12 (i) licenses it in place:
"|Phi^+> is INVARIANT UNDER EXCHANGING THE TWO FACTORS, so the identity holds
with their roles swapped; every other application of its first identity, here
and in Example ex:conj, traces the first factor as stated."

THE FIVE PARTS, and where each is frozen.
 (i)   THE CERTIFICATE. |Psi> = |Phi^+>, and (SR1)-(SR2) hold at every weight
       pair -- (SR1) identically, since tr_{A'}|Phi^+><Phi^+| = 1_A/2 does not
       involve the weights, and (SR2) with the value p^A_b/2 . |a^b><a^b|. The
       Band-A chain has L_s = 0, so A'' = A' and rho^v_x = rho_x by Definition
       def:chaincond (S3), AND Definition def:srcert IS READ HERE ON THE
       SPECIFIED PAIR. Frozen per weight pair as `sr2_values` against
       `sr2_expected`.
 (ii)  D(i)-D(viii), in BB84_D_VERDICTS with the route each takes. THE
       CARDINALITIES ARE THE PROOF'S OWN: "|X|, |V|, |C_A|, |C_B|, |Chat|,
       |Z_perp| are finite with 4, 4, 3, 3, 4, 3 elements", and phi is total on
       THE NINE-ELEMENT K.
 (iii) THE GATES, in BB84_GATE_VERDICTS: (G1) passed, (G2) engaged and passed on
       its checkable half leaving the attestation, (G3) not engaged at m = 0.
       This is case G-T-D2-CERT-M0 of Group PC-G.
       THE NON-VACUITY WITNESS, which is the part an implementation could
       overlook: at d_A = 2 the trusted-mode feasible set imposes
       omega_A = 1_A/2, "which EXCLUDES for instance
       omega = |0><0|_A (x) 1_Q/2, a NORMALIZED SECTOR-BLOCK-DIAGONAL state; so
       the marginal DELETES STATES from Eq. eq:feas and the attestation IS DOING
       WORK (contrast Remark rem:dA1)". That state is frozen in Group PC-G as
       NOTFALLBACK-anti-case, where the same computation is read the other way.
 (iv)  Chat_key = (gen) AND THE KEY MAP. By Eq. eq:chkey a value is key-live iff
       some class in its phi-fibre passes; the only passing class is (Z, Z) and
       phi(Z, Z) = gen, so Chat_key = {gen}, A SINGLETON. The key map is
       Eq. eq:rdef with r^0_A((b,a), kappa) = a and the pass condition
       a(x, v) = (Z, Z), which by the definition of a_A, a_B holds iff
       b = b' = Z. Sixteen cells, in BB84_KEY_MAP: four carry a and twelve
       carry perp.
 (v)   THE STATISTICS, per weight pair, with the four-entry Phi vector and the
       total mass. The err entry is ZERO AT EVERY WEIGHT PAIR: "an ideal qubit
       channel produces no X-basis disagreement", which is the noiseless limit
       and is a check on the computation.

WHY THREE WEIGHT PAIRS. The symmetric dyadic one is the smallest; the asymmetric
dyadic one separates the two parties' biases, so an implementation that used one
weight for both would fail it; and THE NON-DYADIC ONE has odd denominators, so
no value in it is a binary float and the conversion boundary cannot hide. The
contract fixes no weights at all -- Definition def:bb84spec asks only that they
be positive and sum to one -- so all three are equally conforming fixtures.

WHAT THE INSTANCE CANNOT CHECK, and it is the reason Group PC-J exists. Remark
rem:bb84checks: the four BB84 signal states are REAL in the declared basis, so
the conjugation is the identity on this signal set and "A REGRESSION TEST BUILT
ON THIS INSTANCE TO CATCH [a reversed convention] CANNOT FAIL". The case that
does exercise `conjugation_basis` is Example ex:conj, frozen in Group PC-J, and
the contract says it "IS THE CASE AN IMPLEMENTER SHOULD ENCODE".
""",
    hypotheses=(
        "Assumption A-IDEAL: the declared receiver is exactly an ideal "
        "projective qubit measurement. Used for a device with loss, dark counts "
        "or multi-photon events, this declaration OVERSTATES THE KEY.",
        "Assumptions A-SPEC, A-SEQ, A-RHOM, A-ENS, A-RET and A-COIN, which are "
        "the ledger rows whose Supports column names PC12.",
        "The instance is key-length-eligible EXACTLY WHEN (SR3) is supplied; "
        "nothing frozen here asserts (SR3).",
    ),
    revalidation="""\
RE-READ AGAINST THE RELOCATED BLOCK AT 0.1.4, AND FOUND IDENTICAL.

The 0.1.4 amendment moved this instance out of the derivations and into Part II,
Section 7.1, and its Section 1.4 states that the environments were "carried over
unaltered". THAT WAS NOT TAKEN ON TRUST. Every value in Group PC-I was compared,
field by field, against the relocated text, and every one of them matches.

WHAT WAS RE-READ, BY LABEL:
  Definition def:bb84spec -- the declaration's input fields: the signal alphabet
    X = {Z, X} x {0, 1}, the weights p_{(b,a)} = p^A_b / 2, the signal states
    rho_{(b,a)} = |a^b><a^b|, the receiver's choice alphabet and conditional
    POVMs, S = {s_0} with d_{s_0} = 2, the announcement alphabets and maps, the
    sifting predicate (pass iff kappa = (Z, Z)), Eq. eq:bb84phi, the holder
    h = A, Z = {0, 1} with d_Z = 2, the key rule r^0_A((b,a), kappa) = a, and
    "constraints: none, and no attack-set licence";
  Eq. eq:bb84data -- tau_A = 1_A / 2, M_{(b,a)} = p^A_b |conj(a^b)><conj(a^b)|,
    F_{(b',y)} = p^B_{b'} |y^{b'}><y^{b'}|, CList = empty;
  Eq. eq:transpose-trick -- both identities, including the note that the (SR1)
    application is the one that traces the SECOND factor and why that is
    licensed;
  Theorem thm:pc12 (i) -- the certificate |Psi> = |Phi^+> and the L_s = 0
    reading of Definition def:srcert on the specified pair;
  Theorem thm:pc12 (ii) -- the D-verdicts and the cardinalities 4, 4, 3, 3, 4, 3
    with |K| = 9;
  Theorem thm:pc12 (iii) -- the gate verdicts AND THE NON-VACUITY WITNESS:
    omega_A = 1_A / 2 excludes omega = |0><0|_A (x) 1_Q / 2, so the attestation
    is doing work at d_A = 2;
  Theorem thm:pc12 (iv) -- Chat_key = {gen} and the sixteen key-map cells;
  Eq. eq:bb84stats -- the joint distribution cell by cell and the four-entry Phi
    vector, at all three frozen weight pairs including the non-dyadic one;
  Eq. eq:chkey, Remark rem:bb84checks and Remark rem:bb84notclaim -- the
    key-live derivation, the exactness check on both parties' marginals, and
    what the instance does not claim.

RESULT: IDENTICAL. No frozen value changed and none needed to. The only edits
this pass made to this file are locators (see the module docstring).""",
)


# ===========================================================================
#  Group PC-J -- the case that exercises `conjugation_basis` (ex:conj)
# ===========================================================================
#
#  THE BRANCH PAIR IS THE POINT. A single branch proves nothing here: Remark
#  rem:bb84checks proves that the all-real BB84 instance CANNOT catch a reversed
#  conjugation convention, and Example ex:conj is "THE CASE AN IMPLEMENTER
#  SHOULD ENCODE" because on it the two conventions give DIFFERENT emitted
#  elements, DIFFERENT (SR2) verdicts and DIFFERENT matched-basis statistics.


@dataclass(frozen=True)
class ConjugationBranch:
    """One of the two conventions, on the Y-basis signal of Eq. eq:ystates."""

    branch_id: str
    #: "contract" or "omitted".
    convention: str
    #: The emitted element M_{(Y,0)}.
    emitted_element: Matrix
    #: tr_A[(M_{(Y,0)} (x) 1)|Phi^+><Phi^+|], i.e. (1/2) M^T.
    sr2_computed: Matrix
    #: p_{(Y,0)} rho_{(Y,0)}, what (SR2) requires.
    sr2_expected: Matrix
    sr2_holds: bool
    #: P_D[omega]((Y,a), (Y,y)) at omega = |Phi^+><Phi^+|, rows a, columns y.
    matched_basis_joint: tuple[tuple[F, F], tuple[F, F]]
    arithmetic: str


CONJUGATION_BRANCHES: tuple[ConjugationBranch, ...] = (
    ConjugationBranch(
        branch_id="CONJ-contract-convention",
        convention="contract",
        emitted_element=(
            (gz(F(1, 4)), gz(0, F(1, 4))),
            (gz(0, F(-1, 4)), gz(F(1, 4))),
        ),
        sr2_computed=(
            (gz(F(1, 8)), gz(0, F(-1, 8))),
            (gz(0, F(1, 8)), gz(F(1, 8))),
        ),
        sr2_expected=(
            (gz(F(1, 8)), gz(0, F(-1, 8))),
            (gz(0, F(1, 8)), gz(F(1, 8))),
        ),
        sr2_holds=True,
        matched_basis_joint=((F(1, 8), F(0)), (F(0), F(1, 8))),
        arithmetic="""\
THE CONVENTION AS Section 2.5 (`conjugation_basis`) STATES IT: the transpose and
complex conjugate of the source-replacement construction are taken IN THE
DECLARED COMPUTATIONAL BASIS OF A, which the compiler RECORDS with the
certificate. "This is the ONE PLACE where a transposed index would be SILENT, so
the basis is NAMED RATHER THAN ASSUMED."
THE SIGNAL, Eq. eq:ystates:
  |0^Y> = (|0> + i|1>)/sqrt2 ,  |1^Y> = (|0> - i|1>)/sqrt2 ,
frozen as the PROJECTORS
  |0^Y><0^Y| = (1/2)[[1, -i], [i, 1]] ,  |1^Y><1^Y| = (1/2)[[1, i], [-i, 1]] ,
whose entries are Gaussian-rational although the amplitudes are not. CONJUGATION
IN THE DECLARED BASIS SWAPS THE TWO LABELS: conj(|0^Y>) = |1^Y> and
conj(|1^Y>) = |0^Y>, because conjugating the amplitude i gives -i.
WEIGHTS: p^A_Y = p^B_Y = 1/2, so p_{(Y,a)} = p^A_Y/2 = 1/4.
THE EMITTED ELEMENT AT a = 0, with the bar:
  M_{(Y,0)} = p^A_Y |conj(0^Y)><conj(0^Y)| = (1/2)|1^Y><1^Y|
            = (1/2)(1/2)[[1, i], [-i, 1]] = [[1/4, i/4], [-i/4, 1/4]] .
(SR2) BY THE FIRST IDENTITY OF Eq. eq:transpose-trick:
  tr_A[(M_{(Y,0)} (x) 1)|Phi^+><Phi^+|] = (1/2) M_{(Y,0)}^T .
  M_{(Y,0)}^T = [[1/4, -i/4], [i/4, 1/4]] = (1/2)|0^Y><0^Y| -- transposition in
  the declared basis conjugates the entries of a rank-one projector, and
  conjugating twice returns the original, which is exactly the contract's
  observation.
  So the value is (1/4)|0^Y><0^Y| = [[1/8, -i/8], [i/8, 1/8]] .
  AND p_{(Y,0)} rho_{(Y,0)} = (1/4)|0^Y><0^Y| = the same matrix, entry for
  entry. (SR2) HOLDS: "the emitted object DESCRIBES THE SPECIFIED SOURCE".
THE MATCHED-BASIS JOINT DISTRIBUTION at omega = |Phi^+><Phi^+|, by the second
identity of Eq. eq:transpose-trick with F_{(Y,y)} = (1/2)|y^Y><y^Y|:
  P((Y,a),(Y,y)) = (1/2) tr[M^T F] = (1/2)(1/2)(1/2) |<a^Y|y^Y>|^2
                 = (1/8) delta_{ay} ,
using <0^Y|1^Y> = (1/2)(1 . 1 + (-i)(-i)) = (1/2)(1 - 1) = 0 and
<0^Y|0^Y> = (1/2)(1 + 1) = 1. THE TABLE IS DIAGONAL:
  [[1/8, 0], [0, 1/8]] -- ALICE AND BOB AGREE WITH CERTAINTY on matched-basis Y
  rounds, which is what a noiseless channel should report.""",
    ),
    ConjugationBranch(
        branch_id="CONJ-omitted",
        convention="omitted",
        emitted_element=(
            (gz(F(1, 4)), gz(0, F(-1, 4))),
            (gz(0, F(1, 4)), gz(F(1, 4))),
        ),
        sr2_computed=(
            (gz(F(1, 8)), gz(0, F(1, 8))),
            (gz(0, F(-1, 8)), gz(F(1, 8))),
        ),
        sr2_expected=(
            (gz(F(1, 8)), gz(0, F(-1, 8))),
            (gz(0, F(1, 8)), gz(F(1, 8))),
        ),
        sr2_holds=False,
        matched_basis_joint=((F(0), F(1, 8)), (F(1, 8), F(0))),
        arithmetic="""\
THE SAME SPECIFICATION WITH THE CONJUGATION OMITTED -- the defect the convention
exists to prevent, exhibited exactly.
THE EMITTED ELEMENT AT a = 0, without the bar:
  M'_{(Y,0)} = p^A_Y |0^Y><0^Y| = (1/2)(1/2)[[1, -i], [i, 1]]
             = [[1/4, -i/4], [i/4, 1/4]] .
COMPARE THE CORRECT ELEMENT [[1/4, i/4], [-i/4, 1/4]]: THE TWO DIFFER IN THE
SIGN OF THE OFF-DIAGONAL IMAGINARY PART, and in nothing else. Every diagonal
entry agrees. THAT IS WHY THE DEFECT IS SILENT ON A REAL SIGNAL SET.
(SR2) BY THE SAME IDENTITY:
  (1/2) M'^T = (1/2)[[1/4, i/4], [-i/4, 1/4]] = (1/4)|1^Y><1^Y|
             = [[1/8, i/8], [-i/8, 1/8]] ,
  while p_{(Y,0)} rho_{(Y,0)} = (1/4)|0^Y><0^Y| = [[1/8, -i/8], [i/8, 1/8]] .
  THEY DIFFER IN BOTH OFF-DIAGONAL ENTRIES: +i/8 against -i/8 at (0,1) and
  -i/8 against +i/8 at (1,0). (SR2) FAILS.
WHAT THAT MEANS PHYSICALLY, in the contract's words: "the emitted declaration
describes a source that SENDS |1^Y> WHENEVER THE SPECIFICATION SAYS |0^Y>".
AND THE DEFECT IS VISIBLE IN THE STATISTICS, NOT ONLY IN THE CERTIFICATE. The
matched-basis joint distribution becomes
  P'((Y,a),(Y,y)) = (1/8) delta_{(1-a),y} ,  i.e.  [[0, 1/8], [1/8, 0]] ,
THE ANTI-DIAGONAL TABLE: "on matched-basis Y rounds Alice and Bob DISAGREE WITH
CERTAINTY -- A NOISELESS CHANNEL REPORTED AT ERROR RATE ONE IN THAT BASIS, under
whatever acceptance map the specification declares on those classes."
THE Z AND X ROWS ARE UNCHANGED EITHER WAY, "which is precisely why the
four-state instance cannot see the defect and this one can".""",
    ),
)


O_PC_CONJUGATION = PCOracleEntry(
    oracle_id="O-PC-CONJUGATION",
    claims=("PC12", "PC11"),
    kind="toy-instance",
    subject=(
        "Example ex:conj with Eq. eq:ystates, and Remark rem:bb84checks: BOTH "
        "BRANCHES of the conjugation convention -- the contract's, with its "
        "(SR2) value, and the omitted one, with its (SR2) value -- together "
        "with the two matched-basis joint distributions that differ. THE BRANCH "
        "PAIR IS THE POINT: a single branch is not evidence, because the "
        "all-real BB84 instance cannot distinguish the two at all."
    ),
    derivation="""\
contract.tex 0.1.4 Example ex:conj, Eq. eq:ystates, Eq. eq:transpose-trick,
Remark rem:bb84checks, Definition def:srcert (SR2) and Section 2.5
(`conjugation_basis`).

WHY THIS GROUP EXISTS AT ALL, AND IT IS A WITHDRAWN CLAIM. The 0.1.0 draft
asserted that the BB84 statistics check caught a reversed conjugation
convention. Remark rem:bb84checks WITHDRAWS that claim: "As the proof of (i)
records, ALL FOUR BB84 SIGNAL STATES HAVE REAL COEFFICIENTS in the declared
computational basis, so conj(a^b) = a^b and THE CONJUGATION IS THE IDENTITY ON
THIS SIGNAL SET: emitting M = p^A_b |a^b><a^b| in place of
p^A_b |conj(a^b)><conj(a^b)| CHANGES P_D[omega] AT NO STATE, IN NO BASIS. A
reversed convention is exactly as silent here as anywhere else, and A REGRESSION
TEST BUILT ON THIS INSTANCE TO CATCH IT CANNOT FAIL."
THAT IS A STATEMENT ABOUT DATA AND IS FROZEN AS ONE. Group PC-I's
`alice_povm` entries are the four BB84 elements; each is REAL, so its complex
conjugate is itself, so the two conventions emit the SAME MATRIX ENTRY FOR
ENTRY. The integrity test asserts exactly that: every BB84 element equals its own
entrywise complex conjugate, hence the branch pair collapses there.

WHAT ex:conj SUPPLIES INSTEAD. "The case that does exercise `conjugation_basis`
needs A SIGNAL WITH A GENUINELY COMPLEX AMPLITUDE in the declared basis;
Example ex:conj computes one and IS THE CASE AN IMPLEMENTER SHOULD ENCODE." The
Y-basis states of Eq. eq:ystates are the smallest such set, and conjugation on
them SWAPS THE TWO LABELS, so the defect is a label permutation and not a phase.

THE THREE OBSERVABLE DIFFERENCES, all frozen and all exact.
  1. THE EMITTED ELEMENT. [[1/4, i/4], [-i/4, 1/4]] against
     [[1/4, -i/4], [i/4, 1/4]] -- the same matrix with the off-diagonal
     imaginary sign reversed.
  2. THE (SR2) VERDICT. The contract convention gives (1/4)|0^Y><0^Y|, which IS
     p_{(Y,0)} rho_{(Y,0)}; the omitted convention gives (1/4)|1^Y><1^Y|, which
     is not. (SR2) HOLDS in one branch and FAILS in the other, so gate (G2)
     refuses the second at d_A >= 2 (Table tab:gateoutcome, row 3).
  3. THE MATCHED-BASIS STATISTICS. Diagonal [[1/8, 0], [0, 1/8]] against
     anti-diagonal [[0, 1/8], [1/8, 0]]. "A noiseless channel reported at ERROR
     RATE ONE in that basis."
EACH ALONE WOULD BE ENOUGH TO DISCRIMINATE; all three are frozen because they
sit at three different points of the pipeline -- the emitted operator, the
certificate check, and the declared statistics -- and an implementation could
get the first right and the third wrong by re-deriving the statistics from the
specification instead of from the emitted declaration.

THE STATUS OF ex:conj IN THE CONTRACT. It is "AN AUXILIARY ONE-SIGNAL
COMPUTATION, NOT PART OF THE DECLARATION OF Theorem thm:pc12": it exhibits the
smallest specification on which the convention is observable, "SO THAT THE
REGRESSION TEST BUILT FROM IT DISCRIMINATES". Nothing in Group PC-I depends on
it, and nothing here modifies the BB84 declaration.
""",
    hypotheses=(
        "The certificate vector is |Phi^+> and the source segment is empty, so "
        "A'' = A' and rho^v_x = rho_x, exactly as in the BB84 instance. Only "
        "the signal set changes.",
        "The weights p^A_Y = p^B_Y = 1/2 are a fixture choice; the "
        "discrimination is a statement about the OFF-DIAGONAL SIGNS and holds "
        "at every positive weight.",
    ),
    revalidation="""\
RE-READ AGAINST THE RELOCATED EXAMPLE AT 0.1.4, AND FOUND IDENTICAL.

Example ex:conj travelled into Part II, Section 7.1, with the rest of the
instance, and it is the ONE relocated environment the G3 signature discloses as
not byte-identical: two SUPERLATIVES were narrowed inside it by the prose pass
(round-6 observation 4). THAT MADE A RE-READ OF ITS MATHEMATICS OBLIGATORY
RATHER THAN OPTIONAL, and it was done.

WHAT WAS RE-READ, BY LABEL, IN BOTH BRANCHES:
  Eq. eq:ystates -- |0^Y> = (|0> + i|1>)/sqrt2 and |1^Y> = (|0> - i|1>)/sqrt2,
    and the statement that conjugation in the declared basis SWAPS THE TWO
    LABELS;
  the contract branch -- M_{(Y,a)} = p^A_Y |conj(a^Y)><conj(a^Y)|
    = p^A_Y |(1-a)^Y><(1-a)^Y|, its (SR2) value (1/2) M^T, and the identity of
    that value with p_{(Y,a)} rho_{(Y,a)};
  the omitted branch -- M'_{(Y,a)} = p^A_Y |a^Y><a^Y|, its (SR2) value, the
    failure of (SR2), and the reading "the emitted declaration describes a
    source that sends |1^Y> whenever the specification says |0^Y>";
  the two matched-basis distributions -- delta_{ay} against delta_{(1-a)y} on
    omega = |Phi^+><Phi^+|, and the statement that the Z and X rows are
    unchanged either way;
  Remark rem:bb84checks -- the withdrawn claim that the four-state instance
    catches a reversed convention, unchanged.

RESULT: IDENTICAL. The two wording edits are superlatives; they touch no
operator, no sign and no number, and every frozen matrix, verdict and
distribution in Group PC-J stands as derived.""",
)


#: The two oracle entries of this half, in the order the original
#: ``PC_ORACLES`` listed them.
BB84_PC_ORACLES: tuple[PCOracleEntry, ...] = (
    O_PC_BB84,
    O_PC_CONJUGATION,
)


def bb84_pc_oracle(oracle_id: str) -> PCOracleEntry:
    """Return the entry with this id, refusing an unknown one.

    The accessor the SPLIT created, and the one addition this half makes to the
    original vocabulary.
    """
    for entry in BB84_PC_ORACLES:
        if entry.oracle_id == oracle_id:
            return entry
    raise KeyError(f"no BB84 oracle entry with id {oracle_id!r}")
