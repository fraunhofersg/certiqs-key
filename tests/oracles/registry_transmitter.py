"""The transmitter's half of the frozen ``protocol-compiler`` registry.

WHAT THIS FILE IS AND WHY IT EXISTS SEPARATELY. Every value below was derived
BY HAND by run A of the G4 band, before any implementation of
what it pins existed, and it is under that freeze still: an oracle registry
"moves with its module and is never regenerated from the code it tests"
(PRINCIPLES.md section 2.3). The labels these entries pin -- PC10 and PC11 of
the protocol-compiler -- belong to ``transmitter`` (``fact:sr``, ``rem:import``,
``def:srcert``, ``thm:certificate-sufficiency``, ``rem:xreg``, ``rem:boundary``,
``cor:noncanonical``), so their executable memory travels with them.

THE ``claims`` TUPLES STILL READ ``PC10`` AND ``PC11``, AND THAT IS
DELIBERATE. They are the ids the derivation was written against and they are
history; re-labelling them would be editing frozen evidence to make it agree
with a later structure, which is the one thing a freeze forbids. The mapping
is: PC10 -> transmitter/fact:sr and rem:import; PC11 -> transmitter/def:srcert,
thm:certificate-sufficiency, rem:xreg, rem:boundary and cor:noncanonical.

THE CUT IS CHECKED AND NOT TRUSTED:
``tests/oracles/test_protocol_compiler_registry_partition.py`` asserts that the
three halves are disjoint, that their union is the original
``__all__``, that the compiler's half names nothing in this one, and that the
oracle entries are partitioned and complete.

WHAT CAME ACROSS: group PC-H whole -- the certificate cases, the consistency
criterion of ``thm:certificate-sufficiency`` (ii), the (SR3) record, ``O-PC-CERTIFICATE`` and
``O-PC-SR-BOUNDARY`` -- together with ``O-PC-CERTIFICATE-OPERATOR`` of group
PC-M, which pins the 0.3.0 change from a declared VECTOR to the declared
OPERATOR ``Psi``. The two case tables that entry reads,
``CertificateOperatorCase`` and ``CERTIFICATE_OPERATOR_CASES``, STAYED in the
compiler's half: three other entries of group PC-M name them in their
derivations, and splitting a table away from three of its four readers would
have bought nothing. They are imported below.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

from registry_protocol_compiler import (
    ID_2,
    P_X0,
    P_X1,
    P_Z0,
    P_Z1,
    Matrix,
    PCOracleEntry,
    gz,
    real_matrix,
)

__all__ = [
    "CERTIFICATE_CASES",
    "CONSISTENCY_CRITERION_CASES",
    "SR3_RECORD",
    "TRANSMITTER_PC_ORACLES",
    "CertificateCase",
    "ConsistencyCriterionCase",
    "transmitter_pc_oracle",
]



# ===========================================================================
#  Group PC-H -- source replacement and its certificate (PC10, PC11)
# ===========================================================================


@dataclass(frozen=True)
class CertificateCase:
    """One source-replacement certificate, checked against (SR1) and (SR2)."""

    case_id: str
    alice_dim: int
    virtual_dim: int
    #: The certificate vector, frozen as an exact UNNORMALIZED Gaussian-INTEGER
    #: vector (basis label, integer amplitude) together with its squared norm.
    #: Rank-one objects are frozen as projectors wherever the projector is small
    #: enough to write; where the joint space is large the vector is named this
    #: way instead, as the module docstring's fourth rationale line allows.
    psi_integer_amplitudes: tuple[tuple[str, int], ...]
    psi_squared_norm: int
    #: The DECLARED marginal.
    tau_a: Matrix
    #: The value (SR1) computes, tr_{A''} |Psi><Psi|.
    sr1_computed: Matrix
    sr1_holds: bool
    #: (label, M_x) in the emitted order.
    povm: tuple[tuple[str, Matrix], ...]
    #: The declared virtual weights p_x, aligned with ``povm``.
    virtual_weights: tuple[F, ...]
    #: The declared virtual states rho^v_x, aligned with ``povm``.
    virtual_states: tuple[Matrix, ...]
    #: The value (SR2) computes, tr_A[(M_x (x) 1) |Psi><Psi|], aligned.
    sr2_computed: tuple[Matrix, ...]
    sr2_holds: bool
    canonical_form: bool
    arithmetic: str


CERTIFICATE_CASES: tuple[CertificateCase, ...] = (
    CertificateCase(
        case_id="CERT-canonical-with-shield",
        alice_dim=4,
        virtual_dim=2,
        psi_integer_amplitudes=(("|000>", 15), ("|100>", 12), ("|111>", 16)),
        psi_squared_norm=625,
        tau_a=(
            (gz(F(9, 25)), gz(0), gz(F(36, 125)), gz(0)),
            (gz(0), gz(0), gz(0), gz(0)),
            (gz(F(36, 125)), gz(0), gz(F(144, 625)), gz(0)),
            (gz(0), gz(0), gz(0), gz(F(256, 625))),
        ),
        sr1_computed=(
            (gz(F(9, 25)), gz(0), gz(F(36, 125)), gz(0)),
            (gz(0), gz(0), gz(0), gz(0)),
            (gz(F(36, 125)), gz(0), gz(F(144, 625)), gz(0)),
            (gz(0), gz(0), gz(0), gz(F(256, 625))),
        ),
        sr1_holds=True,
        povm=(
            (
                "M_x0",
                real_matrix(((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
            ),
            (
                "M_x1",
                real_matrix(((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))),
            ),
        ),
        virtual_weights=(F(9, 25), F(16, 25)),
        virtual_states=(
            P_Z0,
            real_matrix(((F(9, 25), 0), (0, F(16, 25)))),
        ),
        sr2_computed=(
            real_matrix(((F(9, 25), 0), (0, 0))),
            real_matrix(((F(144, 625), 0), (0, F(256, 625)))),
        ),
        sr2_holds=True,
        canonical_form=True,
        arithmetic="""\
THE CANONICAL FORM OF FACT fact:sr, WITH A NON-TRIVIAL SHIELD, AND EVERY NUMBER
GAUSSIAN-RATIONAL. Fact fact:sr's data are A = Abar Ahat with
dim Abar = |X|, M_x = |x><x|_Abar (x) 1_Ahat, and
|Psi> = sum_x sqrt(p_x) |x>_Abar |psi_x>_{Ahat A''} with |psi_x> a purification
of rho^v_x. Corollary cor:noncanonical proves those data satisfy (SR1)-(SR2).
THE FIXTURE IS CHOSEN SO THAT EVERY SQUARE ROOT IS RATIONAL, which is a fixture
choice and not a contract requirement: the contract fixes no weights.
  X = (x0, x1) with p = (9/25, 16/25), so sqrt(p) = (3/5, 4/5) EXACTLY;
  rho^v_{x0} = |0><0| , purified by |psi_0> = |0>_Ahat |0>_{A''} ;
  rho^v_{x1} = diag(9/25, 16/25) , purified by
  |psi_1> = (3/5)|0>_Ahat|0>_{A''} + (4/5)|1>_Ahat|1>_{A''} , again rational.
  So Abar and Ahat are qubits and d_A = dim H(A) = 2 . 2 = 4, WHILE THE
  PUBLISHED d_A OF Fact fact:sr IS |X| = 2. The contract discloses that
  collision in the symbol map of Section 4.10: "The two documents' d_A are NOT
  THE SAME NUMBER ... the published index runs over an orthonormal basis of
  Abar, so there d_A = |X|, whereas throughout this contract
  d_A = dim H(A) = dim H(Abar) . dim H(Ahat); the two agree exactly when the
  SHIELD SYSTEM IS TRIVIAL." This fixture has a non-trivial shield precisely so
  that the two numbers differ, 4 against 2.
THE CERTIFICATE VECTOR, in the basis |abar ahat a''>:
  |Psi> = (3/5)|000> + (4/5)[(3/5)|100> + (4/5)|111>]
        = (3/5)|000> + (12/25)|100> + (16/25)|111> .
FROZEN AS THE UNNORMALIZED GAUSSIAN-INTEGER VECTOR 25|Psi> =
15|000> + 12|100> + 16|111> with squared norm
15^2 + 12^2 + 16^2 = 225 + 144 + 256 = 625 = 25^2, so |Psi> is a UNIT vector as
Definition def:srcert requires.
(SR1), tau_A = tr_{A''} |Psi><Psi|, computed by grouping the amplitudes by the
A'' index. At a'' = 0 the AbarAhat vector is (3/5)|00> + (12/25)|10>; at a'' = 1
it is (16/25)|11>. The partial trace is the sum of the two outer products:
  (00,00) : (3/5)^2      = 9/25
  (00,10) : (3/5)(12/25) = 36/125     and (10,00) the same
  (10,10) : (12/25)^2    = 144/625
  (11,11) : (16/25)^2    = 256/625
and every other entry 0. TRACE: 9/25 + 144/625 + 256/625 =
225/625 + 144/625 + 256/625 = 625/625 = 1. So (SR1) HOLDS and, by Theorem
thm:certificate-sufficiency (i), tau_A is in S_=(A) -- positive as a partial trace of a positive
operator, trace one because <Psi|Psi> = 1.
(SR2), tr_A[(M_x (x) 1_{A''}) |Psi><Psi|] = p_x rho^v_x, for both x. Each M_x is
a PROJECTOR, so the value equals tr_A of the projected vector's outer product.
  x0 : (M_{x0} (x) 1)|Psi> = (3/5)|000> , since only the abar = 0 term survives.
       tr_{AbarAhat} of its outer product is (9/25)|0><0|_{A''} = diag(9/25, 0),
       and p_{x0} rho^v_{x0} = (9/25)|0><0| . EQUAL.
  x1 : (M_{x1} (x) 1)|Psi> = (12/25)|100> + (16/25)|111> . The two terms have
       DIFFERENT AbarAhat parts, |10> and |11>, so the cross terms vanish under
       the partial trace and the value is
       (144/625)|0><0|_{A''} + (256/625)|1><1|_{A''} = diag(144/625, 256/625),
       and p_{x1} rho^v_{x1} = (16/25) diag(9/25, 16/25)
       = diag(144/625, 256/625) . EQUAL.
BOTH CONDITIONS HOLD. This is Corollary cor:noncanonical's first sentence
verified on data: the canonical data DO satisfy (SR1) and (SR2). Its second
sentence -- that they are not the only such data -- is
CERT-noncanonical-bb84.""",
    ),
    CertificateCase(
        case_id="CERT-noncanonical-bb84",
        alice_dim=2,
        virtual_dim=2,
        psi_integer_amplitudes=(("|00>", 1), ("|11>", 1)),
        psi_squared_norm=2,
        tau_a=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        sr1_computed=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        sr1_holds=True,
        povm=(
            ("M_(Z,0)", real_matrix(((F(1, 2), 0), (0, 0)))),
            ("M_(Z,1)", real_matrix(((0, 0), (0, F(1, 2))))),
            ("M_(X,0)", real_matrix(((F(1, 4), F(1, 4)), (F(1, 4), F(1, 4))))),
            ("M_(X,1)", real_matrix(((F(1, 4), F(-1, 4)), (F(-1, 4), F(1, 4))))),
        ),
        virtual_weights=(F(1, 4), F(1, 4), F(1, 4), F(1, 4)),
        virtual_states=(P_Z0, P_Z1, P_X0, P_X1),
        sr2_computed=(
            real_matrix(((F(1, 4), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(1, 4)))),
            real_matrix(((F(1, 8), F(1, 8)), (F(1, 8), F(1, 8)))),
            real_matrix(((F(1, 8), F(-1, 8)), (F(-1, 8), F(1, 8)))),
        ),
        sr2_holds=True,
        canonical_form=False,
        arithmetic="""\
THE NON-CANONICAL CERTIFICATE OF COROLLARY cor:noncanonical: d_A = 2 for a
protocol whose CANONICAL form has d_A = 4. This is the BB84 instance of Theorem
thm:pc12 at the symmetric weights p^A_Z = p^A_X = 1/2, so p_{(b,a)} = 1/4 for
all four signals.
  |Psi> = |Phi^+> = (|00> + |11>)/sqrt2, frozen as the unnormalized
  Gaussian-INTEGER vector |00> + |11> with squared norm 1 + 1 = 2; the
  corresponding PROJECTOR |Phi^+><Phi^+| has the rational entries of PHI_PLUS.
  d_A = 2, while |X| = 4.
(SR1): tr_{A'} |Phi^+><Phi^+| = 1_A/2 = diag(1/2, 1/2) = tau_A. By
Eq. eq:transpose-trick with Y = 1: tr_1[(1 (x) 1)|Phi^+><Phi^+|] = (1/2) 1^T
= (1/2) 1_A. HOLDS.
(SR2) at all four x, using Eq. eq:transpose-trick's first identity
tr_1[(Y (x) 1)|Phi^+><Phi^+|] = (1/2) Y^T and
M_{(b,a)} = p^A_b |conj(a^b)><conj(a^b)| = (1/2)|a^b><a^b| for the REAL BB84
states:
  (Z,0) : (1/2) M^T = (1/2)(1/2)|0><0| = (1/4)|0><0| = p rho . HOLDS.
  (Z,1) : (1/4)|1><1| . HOLDS.
  (X,0) : (1/4)|+><+| = [[1/8, 1/8], [1/8, 1/8]] . HOLDS.
  (X,1) : (1/4)|-><-| = [[1/8, -1/8], [-1/8, 1/8]] . HOLDS.
WHY THE CANONICAL FORM WOULD BE WORSE HERE, Remark rem:import: "A compiler that
emitted only that form would be FORCED to declare d_A = |X| with a SINGULAR
marginal in every protocol whose signal states are not linearly independent --
including BB84, where the canonical tau_Abar HAS RANK TWO IN A FOUR-DIMENSIONAL
SPACE."
THAT RANK IS FROZEN AS AN INTEGER FACT AND NOT AS A MATRIX, deliberately. The
canonical tau_Abar = sum_{x,x'} sqrt(p_x p_x') <psi_{x'}|psi_x> |x><x'| involves
the overlaps <a^Z|a'^X> = +-1/sqrt2, which are IRRATIONAL, so its entries are
not Gaussian-rational and freezing them would violate this file's
representation. Its RANK is exact and elementary: tau_Abar is the Gram-type
operator of four vectors spanning a 2-dimensional space, so
rank tau_Abar = dim span{|a^b>} = 2 in a 4-dimensional Abar. THE FACT THAT THE
CANONICAL MARGINAL FOR THIS SIGNAL SET IS NOT EVEN GAUSSIAN-RATIONAL IN THE
DECLARED BASIS IS ITSELF AN ILLUSTRATION OF rem:import'S POINT.
THE CHECKER MUST ACCEPT BOTH FORMS. Theorem thm:certificate-sufficiency (iii) "applies to EVERY
triple satisfying (SR1)-(SR3)", and Definition def:eligible (G2) verifies
(SR1)-(SR2) and nothing about canonicity. An implementation that recognized only
the canonical shape would refuse the very instance PC12 emits.""",
    ),
    CertificateCase(
        case_id="CERT-sr1-fails",
        alice_dim=2,
        virtual_dim=2,
        psi_integer_amplitudes=(("|00>", 1), ("|11>", 1)),
        psi_squared_norm=2,
        tau_a=real_matrix(((F(3, 4), 0), (0, F(1, 4)))),
        sr1_computed=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        sr1_holds=False,
        povm=(
            ("M_x0", P_Z0),
            ("M_x1", P_Z1),
        ),
        virtual_weights=(F(1, 2), F(1, 2)),
        virtual_states=(P_Z0, P_Z1),
        sr2_computed=(
            real_matrix(((F(1, 2), 0), (0, 0))),
            real_matrix(((0, 0), (0, F(1, 2)))),
        ),
        sr2_holds=True,
        canonical_form=True,
        arithmetic="""\
(SR1) FAILS WITH (SR2) INTACT, so that the two conditions are seen to be
independent.
The certificate vector is |Phi^+> and the DECLARED marginal is
tau_A = diag(3/4, 1/4). (SR1) computes tr_{A''}|Phi^+><Phi^+| = diag(1/2, 1/2).
  THE TWO DIFFER IN BOTH DIAGONAL ENTRIES: 1/2 against 3/4 at (0,0) and 1/2
  against 1/4 at (1,1). (SR1) FAILS.
(SR2) NEVERTHELESS HOLDS for the family (|0><0|, |1><1|) against the virtual
ensemble p = (1/2, 1/2), rho^v = (|0><0|, |1><1|):
  tr_A[(|0><0| (x) 1)|Phi^+><Phi^+|] = (1/2)|0><0|^T = (1/2)|0><0| , and
  p_{x0} rho^v_{x0} = (1/2)|0><0| . EQUAL, and likewise at x1.
WHAT THE COMPILER DOES: gate (G2) fails at d_A = 2, and Table tab:gateoutcome
row 3 gives a REFUSAL naming the condition -- "A certificate that does not
verify is a DEFECT IN THE SUPPLIED DATA, NOT A WEAKER CLAIM; silently demoting
it would hide a mis-specified source." At d_A = 1 the same refusal follows from
Definition def:compile's clause, which is case G-T-D1-CERTFAIL of Group PC-G.
NOTE ALSO THE ROUTE THROUGH thm:typing's D(ii) PROOF: (SR1) is what makes the
emitted marginal THE CERTIFICATE'S marginal rather than an independently
declared number. Check V2 would still pass here -- diag(3/4, 1/4) is positive
with trace one -- which is exactly why (SR1) is checked separately and why the
thm:typing proof records both routes.""",
    ),
    CertificateCase(
        case_id="CERT-sr2-fails",
        alice_dim=4,
        virtual_dim=2,
        psi_integer_amplitudes=(("|000>", 15), ("|100>", 12), ("|111>", 16)),
        psi_squared_norm=625,
        tau_a=(
            (gz(F(9, 25)), gz(0), gz(F(36, 125)), gz(0)),
            (gz(0), gz(0), gz(0), gz(0)),
            (gz(F(36, 125)), gz(0), gz(F(144, 625)), gz(0)),
            (gz(0), gz(0), gz(0), gz(F(256, 625))),
        ),
        sr1_computed=(
            (gz(F(9, 25)), gz(0), gz(F(36, 125)), gz(0)),
            (gz(0), gz(0), gz(0), gz(0)),
            (gz(F(36, 125)), gz(0), gz(F(144, 625)), gz(0)),
            (gz(0), gz(0), gz(0), gz(F(256, 625))),
        ),
        sr1_holds=True,
        povm=(
            (
                "M_x0 (LABELS SWAPPED)",
                real_matrix(((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))),
            ),
            (
                "M_x1 (LABELS SWAPPED)",
                real_matrix(((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
            ),
        ),
        virtual_weights=(F(9, 25), F(16, 25)),
        virtual_states=(
            P_Z0,
            real_matrix(((F(9, 25), 0), (0, F(16, 25)))),
        ),
        sr2_computed=(
            real_matrix(((F(144, 625), 0), (0, F(256, 625)))),
            real_matrix(((F(9, 25), 0), (0, 0))),
        ),
        sr2_holds=False,
        canonical_form=False,
        arithmetic="""\
(SR2) FAILS WITH (SR1) INTACT: the mirror of the previous case, and the
INDEX-SWAP defect that a marginal check alone cannot see.
THE DATA ARE CERT-canonical-with-shield's, with the two POVM labels EXCHANGED:
the element declared as M_{x0} is |1><1|_Abar (x) 1_Ahat and the one declared as
M_{x1} is |0><0|_Abar (x) 1_Ahat.
(SR1) IS UNTOUCHED: it involves only |Psi> and tau_A, neither of which changed,
so tr_{A''}|Psi><Psi| is the same 4x4 matrix and equals the declared tau_A.
HOLDS.
(SR2) FAILS AT BOTH INDICES:
  x0 : the computed value is diag(144/625, 256/625) while
       p_{x0} rho^v_{x0} = (9/25)|0><0| = diag(9/25, 0) . They differ at (0,0)
       -- 144/625 against 225/625 -- and at (1,1) -- 256/625 against 0.
  x1 : the computed value is diag(9/25, 0) while
       p_{x1} rho^v_{x1} = diag(144/625, 256/625) . Differ likewise.
WHY IT MATTERS AND IS NOT A COSMETIC RELABELLING. (SR2) is the condition that
ties Alice's DECLARED MEASUREMENT to the signal she is said to send: with the
labels swapped, the emitted declaration describes a source that emits rho^v_{x1}
whenever the specification says rho^v_{x0}. That is the same class of defect as
the conjugation reversal of Example ex:conj (Group PC-J), which the BB84 signal
set cannot see and this ensemble can.
THE OUTCOME: gate (G2) fails, and Table tab:gateoutcome row 3 refuses naming the
condition.""",
    ),
)


@dataclass(frozen=True)
class ConsistencyCriterionCase:
    """Theorem thm:certificate-sufficiency (ii): Pi_S (sum_x M_x) Pi_S = Pi_S, and the identity."""

    case_id: str
    tau_a: Matrix
    #: The projector onto supp tau_A.
    pi_s: Matrix
    #: The declared family, which need not be a POVM.
    family: tuple[Matrix, ...]
    is_povm: bool
    #: sum_x M_x, written out.
    family_sum: Matrix
    #: Pi_S (sum_x M_x) Pi_S.
    projected_sum: Matrix
    criterion_holds: bool
    #: sum_x p_x rho^v_x, the left side of the identity.
    average_virtual_state: Matrix
    #: tr_A |Psi><Psi|, the right side.
    psi_signal_marginal: Matrix
    identity_holds: bool
    arithmetic: str


CONSISTENCY_CRITERION_CASES: tuple[ConsistencyCriterionCase, ...] = (
    ConsistencyCriterionCase(
        case_id="CONS-povm-holds",
        tau_a=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        pi_s=ID_2,
        family=(P_Z0, P_Z1),
        is_povm=True,
        family_sum=ID_2,
        projected_sum=ID_2,
        criterion_holds=True,
        average_virtual_state=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        psi_signal_marginal=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        identity_holds=True,
        arithmetic="""\
THE CRITERION AT A POVM, where Theorem thm:certificate-sufficiency (ii) says it "holds outright".
  |Psi> = |Phi^+>, tau_A = 1_A/2, so supp tau_A is the WHOLE space and
  Pi_S = 1_A.
  The family (|0><0|, |1><1|) sums to 1_A, so Y := sum_x M_x - 1_A = 0 and
  Pi_S (sum_x M_x) Pi_S = 1_A = Pi_S . THE CRITERION HOLDS.
  THE IDENTITY IT IS EQUIVALENT TO: (SR2) gives p_x rho^v_x = (1/2)|x><x|, so
  p = (1/2, 1/2) and rho^v_x = |x><x|, whence
  sum_x p_x rho^v_x = (1/2)|0><0| + (1/2)|1><1| = diag(1/2, 1/2) ;
  and tr_A |Phi^+><Phi^+| = 1_{A''}/2 = diag(1/2, 1/2) . EQUAL, entry by entry.
THE PROOF'S MECHANISM, so that the criterion is not mistaken for a coincidence.
Writing Y = sum_x M_x - 1_A and taking a Schmidt decomposition
|Psi> = sum_i sqrt(mu_i)|e_i>|f_i> with every mu_i > 0, (SR1) makes {|e_i|} an
orthonormal basis of S, and
  tr_A[(Y (x) 1)|Psi><Psi|] = sum_{i,j} sqrt(mu_i mu_j) <e_j|Y|e_i> |f_i><f_j| ,
which vanishes IF AND ONLY IF <e_j|Y|e_i> = 0 for all i, j, i.e. iff
Pi_S Y Pi_S = 0. THE PROJECTOR IS WHAT MAKES IT AN `IF AND ONLY IF' RATHER THAN
A SUFFICIENT CONDITION, and the next two cases are why that matters.""",
    ),
    ConsistencyCriterionCase(
        case_id="CONS-nonpovm-fails",
        tau_a=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        pi_s=ID_2,
        family=(P_Z0,),
        is_povm=False,
        family_sum=P_Z0,
        projected_sum=P_Z0,
        criterion_holds=False,
        average_virtual_state=real_matrix(((F(1, 2), 0), (0, 0))),
        psi_signal_marginal=real_matrix(((F(1, 2), 0), (0, F(1, 2)))),
        identity_holds=False,
        arithmetic="""\
A NON-POVM FAMILY THAT FAILS THE CRITERION, WHICH IS THE CASE THE THEOREM'S LAST
SENTENCE IS ABOUT: "a mismatch is therefore A DETECTED DEFECT AND NOT A SILENT
ONE."
  |Psi> = |Phi^+>, tau_A = 1_A/2, Pi_S = 1_A as before.
  THE FAMILY IS THE SINGLE ELEMENT (|0><0|), so sum_x M_x = |0><0| != 1_A: NOT A
  POVM, and check V3's completeness clause would refuse it.
  Pi_S (sum_x M_x) Pi_S = 1_A |0><0| 1_A = |0><0| , and |0><0| != 1_A = Pi_S .
  THE CRITERION FAILS.
  AND SO DOES THE IDENTITY, exactly as the equivalence predicts. (SR2) gives
  p_{x0} rho^v_{x0} = tr_A[(|0><0| (x) 1)|Phi^+><Phi^+|] = (1/2)|0><0|, so
  sum_x p_x rho^v_x = diag(1/2, 0), while tr_A |Phi^+><Phi^+| = diag(1/2, 1/2).
  THEY DIFFER AT (1,1): 0 against 1/2. The missing 1/2 is exactly the mass the
  incomplete family fails to account for.
WHAT THIS BUYS AN IMPLEMENTATION: the criterion is a CROSS-CHECK, not a
duplicate of V3. V3 refuses the family for incompleteness; the criterion says
what goes wrong downstream if one does not -- the virtual average signal state
computed from the certificate would not be the certificate vector's own signal
marginal, and the emitted description would silently lose probability.""",
    ),
    ConsistencyCriterionCase(
        case_id="CONS-nonpovm-holds",
        tau_a=P_Z0,
        pi_s=P_Z0,
        family=(P_Z0, real_matrix(((0, 0), (0, 2)))),
        is_povm=False,
        family_sum=real_matrix(((1, 0), (0, 2))),
        projected_sum=P_Z0,
        criterion_holds=True,
        average_virtual_state=real_matrix(((1, 0), (0, 0))),
        psi_signal_marginal=real_matrix(((1, 0), (0, 0))),
        identity_holds=True,
        arithmetic="""\
THE CASE THAT SHOWS THE POVM PROPERTY IS SUFFICIENT AND NOT NECESSARY -- which
is what the theorem's "IN PARTICULAR it holds whenever {M_x} is a POVM" leaves
open, and what the projector Pi_S is for.
  THE CERTIFICATE: |Psi> = |0>_A |0>_{A''}, a PRODUCT state, frozen as the
  Gaussian-integer vector |00> with squared norm 1. Then
  tr_{A''}|Psi><Psi| = |0><0| = tau_A, so (SR1) HOLDS and tau_A is SINGULAR,
  with supp tau_A = span{|0>} and Pi_S = |0><0|.
  THE FAMILY (|0><0| , 2|1><1|) is NOT a POVM: sum_x M_x = diag(1, 2) != 1_A.
  BUT Pi_S (sum_x M_x) Pi_S = |0><0| diag(1, 2) |0><0| = |0><0| = Pi_S .
  THE CRITERION HOLDS.
  AND THE IDENTITY HOLDS TOO, as it must. (SR2) gives
  p_{x0} rho^v_{x0} = tr_A[(|0><0| (x) 1)|00><00|] = |0><0|_{A''} , so p_{x0} = 1
  and rho^v_{x0} = |0><0|; and
  p_{x1} rho^v_{x1} = tr_A[(2|1><1| (x) 1)|00><00|] = 0 , so p_{x1} = 0.
  Hence sum_x p_x rho^v_x = |0><0|_{A''} = tr_A |00><00| . EQUAL.
THE MECHANISM: the defect 2|1><1| lives entirely OUTSIDE the support of tau_A,
and the Schmidt vectors |e_i> of |Psi> span only that support, so no matrix
element <e_j|Y|e_i> sees it. THE CRITERION IS ABOUT WHAT THE CERTIFICATE VECTOR
CAN DETECT, not about the family in isolation -- which is why V3 still refuses
this family and the criterion still passes it. THE TWO CHECKS ARE INDEPENDENT
AND BOTH ARE NEEDED.""",
    ),
)


O_PC_CERTIFICATE = PCOracleEntry(
    oracle_id="O-PC-CERTIFICATE",
    claims=("PC10", "PC11"),
    kind="toy-instance",
    subject=(
        "Definition def:srcert (SR1)-(SR3), Theorem thm:certificate-sufficiency (i)-(ii) and "
        "Corollary cor:noncanonical: (SR1) and (SR2) on named data, passing and "
        "failing independently; the consistency criterion including a non-POVM "
        "family that fails it and a non-POVM family that passes it; BOTH the "
        "canonical form and a non-canonical d_A = 2 instance; and (SR3) frozen "
        "as PRESENCE ONLY."
    ),
    derivation="""\
contract.tex 0.1.4 Fact fact:sr with the symbol map of Section 4.10, Remark
rem:import, Definition def:srcert, the "One reading at every L_s" paragraph,
Theorem thm:certificate-sufficiency (i)-(ii), Corollary cor:noncanonical and Remark rem:boundary.

WHAT THE CERTIFICATE IS WRITTEN AGAINST, and it has exactly one reading. The
pair (A'', {p_x, rho^v_x}) -- the VIRTUAL transmitted system and the ensemble the
source segment STARTS FROM (Definition def:chaincond (S1), (S3)) -- "is the only
pair a certificate is ever written against, AT EVERY LENGTH OF THE SOURCE
SEGMENT, because the object the compiler emits is the virtual protocol". At
L_s = 0 the two pairs are literally equal, A'' = A' and rho^v_x = rho_x, which
is the Band-A case and the case of CERT-noncanonical-bb84.

THE TWO CHECKABLE CONDITIONS ARE INDEPENDENT, and the frozen pair
(CERT-sr1-fails, CERT-sr2-fails) proves it on data: one fails (SR1) with (SR2)
intact, the other fails (SR2) with (SR1) intact. Theorem thm:certificate-sufficiency (i) fixes the
work: (SR1) "compares d_A^2 entries after a partial trace" and (SR2) "compares
|X| matrices of size dim H(A'')". Both are finite and both are exact here.
(SR1) ALSO IMPLIES tau_A in S_=(A) -- positive as a partial trace of a positive
operator, trace one because <Psi|Psi> = 1 -- which is the route the proof of
Theorem thm:typing records for D(ii) in trusted mode, alongside the independent V2
route.

THE CHECKER MUST ACCEPT BOTH SHAPES. Fact fact:sr supplies the CANONICAL source
replacement -- one particular purification and one particular measurement, with
Abar of dimension |X| -- and Remark rem:import says why that alone will not do:
it would force d_A = |X| with a singular marginal in every protocol whose signal
states are not linearly independent, "including BB84, where the canonical
tau_Abar has RANK TWO IN A FOUR-DIMENSIONAL SPACE". Theorem thm:certificate-sufficiency states the
PROPERTY that makes a triple a source replacement and proves any triple with
that property describes the same protocol; Corollary cor:noncanonical draws the
conclusion. CERT-canonical-with-shield and CERT-noncanonical-bb84 are the two
shapes, at d_A = 4 and d_A = 2, and both verify.

THE CONSISTENCY CRITERION IS AN EQUIVALENCE, NOT A SUFFICIENT CONDITION, and the
three CONSISTENCY_CRITERION_CASES cover its three regimes: a POVM (holds),
a non-POVM that fails it, and a NON-POVM THAT PASSES IT because its defect lies
outside supp tau_A. The last is the reason Pi_S appears in the statement at all,
and it is frozen so that no implementation "simplifies" the criterion to
sum_x M_x = 1_A.

(SR3) IS AN ATTESTATION AND IS FROZEN AS PRESENCE ONLY. Theorem thm:certificate-sufficiency (i):
"(SR3) is a statement about the APPARATUS, not about matrices; NO MATRIX
FUNCTION DECIDES IT". Remark rem:boundary: "what it may NEVER do is ASSERT (SR3)
of a physical apparatus: IT RECORDS THE ATTESTATION IT WAS GIVEN." Assumption
ass:ret carries the same content in the ledger and is vacuous at d_A = 1. NO
CASE IN THIS REGISTRY RECORDS A VERDICT ON (SR3); see SR3_RECORD below for the
two record shapes.
""",
    hypotheses=(
        "Assumption A-ENS for the physical device: the source emits the "
        "declared ensemble. (SR2) can hold for the declared data and fail for "
        "the device, which is exactly A-ENS's 'If violated' cell.",
        "Assumption A-SEQ, the sequential round structure, which is Fact "
        "fact:sr's hypothesis and Theorem thm:certificate-sufficiency (iii)'s.",
        "Assumption A-RET is (SR3) and is NEVER decided by this module.",
    ),
)


#: The (SR3) record in both cases. THE ONLY TWO FIELDS THE CONTRACT FIXES ARE
#: whether the attestation was SUPPLIED and whether the licence record is
#: EMITTED; the module's own verdict on (SR3) is, in both cases, ABSENT.
SR3_RECORD: tuple[tuple[str, bool, bool, bool, str], ...] = (
    (
        "supplied, trusted mode at d_A >= 2",
        True,
        True,
        False,
        "Section 2.3 emits `source_replacement_license' exactly here, carrying "
        "(SR1)-(SR3). The record is a PASS-THROUGH of the supplied attestation "
        "with its provenance; the module asserts nothing. Gate (G2) verifies "
        "(SR1)-(SR2) only.",
    ),
    (
        "not supplied, trusted mode at d_A >= 2",
        False,
        False,
        False,
        "No attestation, so nothing to pass through. Table tab:gateoutcome "
        "row 2 applies at m = 0 (untrusted-mode emission with the fallback "
        "recorded) and row 4 at m >= 1 (refusal). Either way the licence is "
        "NOT synthesized: Section 2.5 (`fail_closed`) -- 'no licence is ever "
        "synthesized'.",
    ),
    (
        "d_A = 1, any request",
        False,
        False,
        False,
        "Vacuous. Section 2.3: 'Vacuous at d_A = 1 and then NOT EMITTED AND NOT "
        "DEMANDED'; Remark rem:dA1: the certificate there licenses tr omega = 1, "
        "which every normalized state satisfies, so 'the compiler MUST NOT "
        "DEMAND the attestation there'.",
    ),
)


O_PC_SR_BOUNDARY = PCOracleEntry(
    oracle_id="O-PC-SR-BOUNDARY",
    claims=("PC11",),
    kind="structural-identity",
    subject=(
        "Theorem thm:certificate-sufficiency (iii) with Eq. eq:Nmsm and Eq. eq:srmain, and Remark "
        "rem:xreg: the interchange law at the compiler boundary, and the "
        "overwriting-channel refutation frozen as TWO DIFFERING outcome "
        "distributions -- one channel is enough to refute a commutation "
        "asserted for every channel."
    ),
    derivation="""\
contract.tex 0.1.4 Theorem thm:certificate-sufficiency (iii), Eq. eq:Nmsm, Eq. eq:srmain, Remark
rem:xreg and Remark rem:boundary.

WHAT (iii) SAYS. With N_A Alice's measurement channel of Eq. eq:Nmsm,
N_A(xi) = sum_x tr[M_x xi] |x><x|_X, and E ANY channel from A''E to E' -- the
adversary's attack and the rest of the round ON THE TRANSMITTED SYSTEM AND THE
ADVERSARY'S REGISTERS -- Eq. eq:srmain equates three states on XE':
  (id_X (x) E) o (N_A (x) id_{A''E}) (|Psi><Psi| (x) sigma)
  = (N_A (x) id_{E'}) o (id_A (x) E) (|Psi><Psi| (x) sigma)
  = (id_X (x) E) (rho_{X A''} (x) sigma) ,
with rho_{X A''} = sum_x p_x |x><x|_X (x) rho^v_x.

THE FIRST EQUALITY IS THE ELEMENTARY INTERCHANGE LAW and needs nothing about the
particular channels: N_A acts out of A alone, E out of A''E alone, A and A''E
are complementary tensor factors of the input, and the outputs X and E' are
distinct registers, so both sides equal N_A (x) E. THE SECOND uses (SR2) exactly
once, to identify (N_A (x) id)(|Psi><Psi|) with rho_{X A''}.
FROZEN AT THE CANONICAL DATA of CERT-canonical-with-shield: the X-marginal of
all three expressions is (p_{x0}, p_{x1}) = (9/25, 16/25), because E does not
touch X and the X register is created by N_A with exactly those weights, which
is (SR2) summed over the A'' index. 9/25 + 16/25 = 1.

THE REFUTATION, Remark rem:xreg, AND WHY THE HYPOTHESIS CANNOT BE DROPPED. Let
E' be the channel that OVERWRITES X with a fixed |x_0><x_0| and acts as the
identity elsewhere, and take the simplest data -- X = (x0, x1) with
p = (1/2, 1/2). Then
  E' o (N_A (x) id) produces the POINT DISTRIBUTION at x0 : (1, 0) ;
  any composition in which E' PRECEDES N_A leaves the outcome distribution
  intact : (1/2, 1/2) .
THE TWO DISTRIBUTIONS DIFFER -- at x0, 1 against 1/2, and at x1, 0 against 1/2 --
so the commutation FAILS for that channel. "ONE OVERWRITING CHANNEL IS ENOUGH TO
REFUTE A COMMUTATION ASSERTED FOR EVERY CHANNEL."
THE STATEMENT IS ALSO ILL-TYPED WITHOUT THE HYPOTHESIS: "X does not exist until
N_A creates it: on the right-hand side of Eq. eq:srmain the channel is applied to
|Psi><Psi| (x) sigma, A STATE ON A A'' E CARRYING NO SUCH REGISTER."

WHAT THE RESTRICTION COSTS, AND IT IS NOTHING. What it excludes is exactly the
operations that READ Alice's outcome -- in a QKD round, the public
announcements -- and Assumption ass:seq places those AFTER both parties'
measurements. "So the channel that models `the adversary's attack and the rest of
the round up to the announcements' IS OF THE ADMITTED FORM, and the
delayed-measurement reading survives in the form that is used -- ALICE'S
MEASUREMENT MAY BE MOVED ACROSS THE ATTACK, NOT ACROSS THE ANNOUNCEMENTS."
THE CORROBORATING LOCATOR IS RECORDED AND NOT USED: the PC11 provenance block
says the register restriction "is CORROBORATED by a published locator quoted in
Remark rem:xreg; that corroboration is recorded and NO STEP OF THE DERIVATION
USES IT". That is why the PC11 `refs` list in interface.yaml is EMPTY.

WHERE THE BOUNDARY IS, Remark rem:boundary. (iii) is a statement ABOUT THE
SOURCE. "It is NOT a security reduction, and it does NOT say that the consuming
engine's optimization is sound; that argument -- granting the adversary a
purification of A Q, restricting to the declared feasible set, accumulating over
rounds -- LIVES IN THE ENGINE'S CONTRACT." What this module owes is exactly
(SR1)-(SR3), and what it may never do is assert (SR3) of an apparatus.
""",
    value="the outcome distributions (1, 0) and (1/2, 1/2) differ",
    hypotheses=(
        "E acts on neither A nor X. That it does not act on A is (SR3); that it "
        "does not act on X is a hypothesis of the statement, and Remark "
        "rem:xreg shows it cannot be dropped.",
        "Assumption A-SEQ, which is what makes the restriction cost nothing.",
    ),
)


O_PC_CERTIFICATE_OPERATOR = PCOracleEntry(
    oracle_id="O-PC-CERTIFICATE-OPERATOR",
    claims=("PC9", "PC11", "PC12"),
    kind="fail-closed",
    subject=(
        "Definition def:srcert and Definition def:eligible (G2): the "
        "certificate declares the OPERATOR Psi and not a vector, and the five "
        "decidable conditions -- Psi Hermitian, Psi^2 = Psi, tr Psi = 1 "
        "rounding nowhere, (SR1), (SR2) -- decided exactly and independently."
    ),
    derivation="""\
THE ONE INPUT TYPE 0.3.0 CHANGES, AND THE CHANGE IS FORCED BY EXACTNESS RATHER
THAN BY A TOLERANCE. Frozen in CERTIFICATE_OPERATOR_CASES, two cases.

WHY THE TYPE HAD TO CHANGE. Definition def:srcert: "Through 0.2.0 this row
declared a VECTOR |Psi>, normalized AT THE TOLERANCE, and read (SR1)-(SR2) at
the tolerance too -- and the reason given was that an exact reading WOULD BE
UNSATISFIABLE, the Band-A certificate vector having amplitudes 1/sqrt2. THAT
REASON WAS CORRECT ABOUT A DECLARED VECTOR AND IS WHAT FORCES THE TYPE CHANGE,
NOT A TOLERANCE. No binary64 number a satisfies a**2 = 1/2, so a declared vector
with entries fl(1/sqrt2) yields |Psi><Psi| with entries fl(1/sqrt2)**2 != 1/2
and (SR1) FAILS EXACTLY for the certificate AS THE INSTANCE DECLARES IT ... The
OPERATOR |Phi+><Phi+|, by contrast, has EVERY ENTRY EQUAL TO 1/2, WHICH IS A
BINARY64 NUMBER; and every quantity (SR1), (SR2), Theorem thm:certificate-sufficiency and the
compilation map reads off the certificate IS A FUNCTION OF Psi AND NEVER OF A
VECTOR. Declaring the operator is therefore THE MINIMAL CHANGE THAT MAKES THE
EXACT READING SATISFIABLE RATHER THAN MERELY STRICTER."

AND IT IS NOT A WEAKENING: "The purity conditions -- Psi^2 = Psi with
tr Psi = 1 -- are what RECOVER THE VECTOR where an argument needs one (Theorem
thm:certificate-sufficiency (ii)), and they are two exact identities on the declared matrix.
NOTHING ELSE IN THIS CONTRACT CHANGED WITH THE TYPE: (SR1)-(SR3) read as they
always did, with |Psi><Psi| replaced by Psi throughout."

THE TWO CASES. G2-PHI-PLUS is the Band-A instance's own certificate and is the
contract's NON-VACUITY WITNESS for the certificate class -- the head of Section
7 records that Corollary cor:noncanonical cites Theorem thm:pc12 forward for it
and that "THAT FORWARD CITATION IS A PROOF STEP AND NOT AN ILLUSTRATION ... it
is THE ONE PLACE WHERE PART I RESTS ON PART II". All five conditions pass
exactly. G2-MAXIMALLY-MIXED-NOT-IDEMPOTENT fails idempotence while PASSING
Hermiticity, the trace and (SR1), which is what makes it a test of the purity
condition rather than of the certificate as a whole: an implementation deciding
(SR1) alone would admit it.

WHAT NO CASE RECORDS. A verdict on (SR3). It "carries no number, is not
decidable, and is TESTED FOR PRESENCE ONLY" (Definition def:eligible (G2)), and
Remark rem:boundary forbids this module from asserting it of an apparatus. The
existing SR3_RECORD entries stand unchanged and are not superseded.""",
    hypotheses=(
        "subsystem_order puts A first, so Psi on A A'' is indexed with the "
        "A-factor outermost and tr_{A''} traces the SECOND factor; the "
        "partial traces below were computed under that convention.",
        "The Band-A chain has L_s = 0, so A'' = A' and rho^v_x = rho_x "
        "(Definition def:chaincond (S3)); (SR1)-(SR2) are therefore read on "
        "the specified pair, which Definition def:srcert's 'One reading at "
        "every L_s' paragraph licenses.",
    ),
)

#: The three oracle entries of this half, in the order the original
#: ``PC_ORACLES`` listed them.
TRANSMITTER_PC_ORACLES: tuple[PCOracleEntry, ...] = (
    O_PC_CERTIFICATE,
    O_PC_SR_BOUNDARY,
    O_PC_CERTIFICATE_OPERATOR,
)


def transmitter_pc_oracle(oracle_id: str) -> PCOracleEntry:
    """Return the entry with this id, refusing an unknown one.

    The accessor the SPLIT created, and the one addition this half makes to the
    original vocabulary. Refusing is the point: a silent ``None`` would
    let a test assert nothing while looking like it asserted something.
    """
    for entry in TRANSMITTER_PC_ORACLES:
        if entry.oracle_id == oracle_id:
            return entry
    raise KeyError(f"no transmitter oracle entry with id {oracle_id!r}")
