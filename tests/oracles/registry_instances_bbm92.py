"""The frozen oracle registry of the ``instances/bbm92`` instance.

WHAT THIS FILE IS. The hand-derived expected values of the
BBM92 targets B-1 to B-6 of
``reports/2026-09-21-generalized-reductions-plan/05-validation.md`` section
5.3, each with the derivation that produced it, the fixed instance it is
stated on, and the hypotheses under which it holds.

WHY IT IS A FILE OF ITS OWN, beside
``registry_instances_decoy_bb84.py``. The two are different INSTANCES, and an
instance is data (``PRINCIPLES.md`` section 5): deleting one instance must
leave the other's evidence standing, which is the reason a removable
submodule's registry is a file of its own and is the reason here. The
dependency runs one way and only to the shared vocabulary: both files import
``KINDS`` and ``INADMISSIBLE_SOURCES`` from ``registry.py`` rather than
restating them, as ``registry_statistics_rules.py`` does, so the registries
cannot drift on what an admissible oracle is. NEITHER FILE IMPORTS THE OTHER.
The one piece of mathematics they share -- the Bell-diagonal closed form of
``derivations/06`` target OT4 -- is DERIVED AGAIN HERE, for ``d_A = 1`` and a
product receiver, because a registry whose derivation lives in another
instance's file is not evidence for its own instance.

WHY IT EXISTS BEFORE THE CODE. ``PRINCIPLES.md`` section 2.3. Authored and
committed by an ORACLE AUTHOR, who is not the implementer, before any
of ``src/certiqs_key/`` supporting a two-station declaration, a factorised
sector map or a party-local entry existed, and before the claims that carry
it.
The implementer may read it and may not modify it. An expected value that turns
out to be wrong is a FINDING, reported with its derivation.

ADMISSIBILITY. No MATLAB, OpenQKDSecurity, CVX, MOSEK or Julia value, and no
value from running anything under ``src/``. Every number is an exact closed
form, an elementary evaluation of one, or a hand-computed rational; the closed
forms are the functions of this module and the frozen tables are their
evaluations on :data:`registry.ALPHA_GRID`, which exist to catch a
transcription typo. THE DERIVATION IS AUTHORITATIVE.

WHAT BBM92 IS, IN THE TREE'S OWN SLOTS (``derivations/05-bbm92-check.md``
section 5.1). ``d_A = 1``, ``tau_A = [1]``, a one-letter ``X`` with
``M_{x_0} = [1]``; ``Q = Q_A (x) Q_B``, each factor a squashed receiver with
its own sector map, the declared map being the ``FactorisedSectorMap`` with two
party-scoped factors; ``V = V_A x V_B`` with
``F_{(v_A,v_B)} = F^A_{v_A} (x) F^B_{v_B}``; readouts
``rd_A(x, v) = v_A`` and ``rd_B(x, v) = v_B``; the test coin through
``protocol-compiler/def:weighted``; and NO CERTIFICATE, because at ``d_A = 1``
none is demanded (``transmitter/rem:da1``). The untrusted feasible set carries
NO marginal condition -- declaring ``tau_A = 1/d_A`` to stand for an unknown
source stays forbidden (the plan's section 2.8 item 5) -- and that absence is
the whole content of B-3.

THE NORMALISATION, FIXED ONCE. The acceptance map sends a SIFTED generation
round -- matching bases, exactly one click on each side -- to the letter
``gen``, and an unsifted one to a letter of its own; test rounds carry the test
tuple. ``P_gen`` is therefore the sifted generation probability and "per sifted
generation round" divides by it and by nothing else. This is convention A of
``registry_instances_decoy_bb84.py``, named again here so that this file stands
alone. Under the other convention -- one ``gen`` letter for every generation
round -- the failing branch enters ``K`` linearly and every per-round figure
below is strictly smaller at every ``alpha > 1``; that comparison is frozen in
the decoy registry and is not repeated.

WHAT THIS REGISTRY DOES NOT DO. It pins no ``h_low`` from a solver, computes no
key rate and asserts no equality the plan marks as expected: B-3's equality is
RECORDED, NOT ASSERTED, and carries ``recorded_not_asserted = True``. B-3 and
B-6 are inequalities between two programs and are frozen as RELATIONS with
their hypotheses, with a hand-computed witness where one exists.

THE CLAIMS PINNED, AND THE RE-PIN. When this file was written the
consumer's side of the party-local form, the two-party declaration shape and the
transcript protocol were not yet claims, so each entry pinned what existed and
listed the rest in ``repin_after_c3`` under the plan's proposed ids, which are
suggestions and nothing more.

**The claims are accepted (reductions 0.2.0; protocol-compiler 0.2.0 and
meat-core 1.1.0), and the re-pin is done, deliberately.** All
four ids this file guessed turned out not to exist, and none of them was needed:
there is no ``thm:tensor-instance`` (the factorised emission is
``reductions/thm:emitted-product``, pinned here from the start), no
``def:licensed-party-local`` and no ``def:homog-party-local`` (the party-local
form is a paragraph inside the accepted ``reductions/def:licensed`` and
``meat-core/def:homog``, with ``def:attset``, ``thm:licence`` (v) and
``lem:party-local``, all pinned from the start), and no ``def:transcript`` (the
transcript is (DX5) of both modules' ``def:declaration``, with
``protocol-compiler/ex:transcript``). What the re-pin adds is the consumer's
side, which genuinely did not exist before: ``def:declaration`` (DX6),
``meat-core/def:roundmodel``'s party-local admissibility set, ``lem:range``'s
transport of it, and ``protocol-compiler/ex:two-party-shape``, which writes out
this instance's own declaration shape slot by slot. ``repin_after_c3`` is now
empty on every entry and the integrity test keeps the ratchet for the next batch.

**NO FROZEN NUMBER MOVED, and every entry carries a ``revalidation``.** Two facts
of the accepted claims were checked rather than assumed, and neither contradicts
anything here: the ensemble form of ``def:declaration`` (DX4) exists in
trusted-source mode only, and this instance declares Alice's slot in POVM form
with ``M_{x_0} = [1]``, so no entry reads it; and ``meat-core/thm:removal`` makes
no sector removable when the list carries a party-local entry or the declaration
has more than one measured factor, which BBM92 does -- no entry of this file
asserts removability, and the restriction only forbids a reading of B-6 that B-6
never made. ``meat-core/lem:rank-one-sector`` is deliberately pinned NOWHERE
here: it is stated in trusted-source mode with the default readouts, and this
instance has neither.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from fractions import Fraction as F

from registry import ALPHA_GRID, ASSURANCE, INADMISSIBLE_SOURCES, KINDS

__all__ = [
    "ALPHA_GRID",
    "ASSURANCE",
    "BBM92_IDEAL",
    "BBM92_INSTANCES",
    "BBM92_KINDS",
    "BBM92_ORACLES",
    "BBM92_SYMMETRIC_ERROR",
    "INADMISSIBLE_SOURCES",
    "KINDS",
    "PARTY_LOCAL_SEPARATION",
    "Bbm92Instance",
    "Bbm92OracleEntry",
    "Matrix",
    "bbm92_instance",
    "bbm92_oracle",
    "bell_diagonal_bits",
    "bell_diagonal_sum",
    "binary_entropy",
    "conditional_phase_entropy",
    "honest_point_bits",
    "independent_error_bits",
]


#: The one addition to ``registry.KINDS``, with its motivation, as the decoy
#: registry makes the same one: B-3 and B-6 are INEQUALITIES between two
#: programs. A number would freeze a solver run, which an oracle may not be
#: (PRINCIPLES.md section 2.3); a ``structural-identity`` would claim an
#: equality that is not asserted. A ``relation`` entry MUST carry a
#: ``relation`` string and no other kind may; a number beside it is a BOUND or
#: a RECORDED coincidence and says which in ``value_closed_form``.
BBM92_KINDS: frozenset[str] = KINDS | frozenset({"relation"})


# ===========================================================================
#  The closed forms, written from the derivations and from nothing else
# ===========================================================================


def binary_entropy(x: float) -> float:
    """Return ``h2(x) = -x log2 x - (1-x) log2(1-x)``, in bits."""
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


def bell_diagonal_sum(
    lambdas: tuple[float, float, float, float], alpha: float
) -> float:
    """Return ``S = sum_i (lambda_{i0}^{1/alpha} + lambda_{i1}^{1/alpha})^alpha``.

    ``lambdas`` is ``(lambda_00, lambda_01, lambda_10, lambda_11)``, first index
    the BIT-error index and second the PHASE index, which in the Bell order
    ``(Phi+, Phi-, Psi+, Psi-)`` is that same order.
    """
    beta = 1.0 / alpha
    total = 0.0
    for pair in (lambdas[0:2], lambdas[2:4]):
        if pair[0] > 0.0 or pair[1] > 0.0:
            total += (pair[0] ** beta + pair[1] ** beta) ** alpha
    return total


def bell_diagonal_bits(
    lambdas: tuple[float, float, float, float], alpha: float
) -> float:
    """Return the matched-basis class's bits per sifted round: ``1 - log2 S/(a-1)``."""
    return 1.0 - math.log2(bell_diagonal_sum(lambdas, alpha)) / (alpha - 1.0)


def conditional_phase_entropy(lambdas: tuple[float, float, float, float]) -> float:
    """Return ``H(phase | bit)`` under the Bell weights, in bits.

    The ``alpha -> 1+`` value of :func:`bell_diagonal_bits` is
    ``1 - H(phase | bit)``.
    """
    total = 0.0
    for pair in (lambdas[0:2], lambdas[2:4]):
        weight = pair[0] + pair[1]
        if weight > 0.0:
            total += weight * binary_entropy(pair[1] / weight)
    return total


def independent_error_bits(error: float, alpha: float) -> float:
    """Return the bits per sifted round at the INDEPENDENT-error state.

    ``lambda = ((1-e)^2, e(1-e), e(1-e), e^2)``: the Bell-diagonal state whose
    bit and phase errors are both ``e`` and are independent. Its
    ``alpha -> 1+`` value is ``1 - h2(e)``.
    """
    complement = 1.0 - error
    lambdas = (
        complement * complement,
        complement * error,
        error * complement,
        error * error,
    )
    return bell_diagonal_bits(lambdas, alpha)


def honest_point_bits(error: float, alpha: float) -> float:
    """Return the bits per sifted round at the DEPOLARISED honest state.

    ``lambda = (1 - 3e/2, e/2, e/2, e/2)``. Strictly LARGER than
    :func:`independent_error_bits` at the same ``e``, and comparing a solver's
    infimum against it would be comparing against the wrong number.
    """
    half = error / 2.0
    return bell_diagonal_bits((1.0 - 3.0 * half, half, half, half), alpha)


def _freeze(form: Callable[[float], float]) -> tuple[tuple[float, float], ...]:
    """Evaluate ``form`` on :data:`registry.ALPHA_GRID`, as ``registry`` does."""
    return tuple((a, form(a)) for a in ALPHA_GRID)


# ===========================================================================
#  The fixed instances. THESE CHOICES ARE MINE.
# ===========================================================================
#
#  Section 5.3 names B-1 to B-6 on "BBM92" without fixing a coin bias, basis
#  weights, a key class or an error rate, and rule (3) of the oracle author's
#  brief says to fix the instance and say so. What is common to both instances
#  below:
#
#  * two stations, each an IDEAL projective qubit receiver -- unit efficiency,
#    no dark counts, exactly one click per round, no flag sector. This is the
#    "ideal pair" preset of the plan's section 4.2 at unit transmittance and is
#    NOT the passive four-detector station the instance will carry. Every
#    number below is the mathematics', not the apparatus's;
#  * basis weights p^A_Z = p^A_X = p^B_Z = p^B_X = 1/2 on both stations, drawn
#    independently each round and announced;
#  * a public test coin of bias gamma = 1/5 held by Alice, entering through
#    ``protocol-compiler/def:weighted`` as a weight INSIDE the POVM elements
#    and never as a fraction applied afterwards (A-TSM);
#  * KEY FROM THE MATCHED-Z GENERATION ROUNDS ONLY. Matched-X rounds are a test
#    statistic. THE PLAN'S INSTANCE SIFTS IN BOTH MATCHED BASES, and this is a
#    deliberate narrowing: it makes B-1 and B-2 the exact analogues of T1 and
#    T2 of ``tests/support/bb84_targets.py``, whose gen class is (Z, Z) and
#    whose ok/err classes are (X, X), so that the BBM92 numbers can be read
#    against the qubit ones. With both bases keyed, every figure below is
#    multiplied by (p_Z^2 + p_X^2)/p_Z^2 = 2 and nothing else changes;
#  * test rounds announce both outcomes in whichever bases were chosen, so BOTH
#    the Z-basis and the X-basis error rates are observed. That matters: B-2's
#    minimiser is decided by having both;
#  * the key holder is ALICE, direct reconciliation, r(x, v) = bit(v_A);
#  * d_A = 1: untrusted-source mode, no marginal condition, no certificate.


@dataclass(frozen=True)
class Bbm92Instance:
    """One fixed BBM92 instance: the data every entry on it reads."""

    instance_id: str
    #: The test coin's bias gamma; the generation branch carries 1 - gamma.
    test_coin: F
    #: (p^A_Z, p^A_X) and (p^B_Z, p^B_X).
    alice_basis_weights: tuple[F, F]
    bob_basis_weights: tuple[F, F]
    #: The probability of a SIFTED generation round: matching bases and one
    #: click on each side. At ideal stations this is (1-gamma) p^A_Z p^B_Z for
    #: a Z-keyed instance.
    sifted_generation: F
    #: The honest symmetric error rate, equal in both bases.
    error_rate: F
    #: The honest state's Bell weights, in the (bit, phase) index order.
    honest_lambdas: tuple[float, float, float, float]
    honest_lambdas_exact: tuple[F, F, F, F]
    #: The Bell weights of the state that MINIMISES the entropy term at the
    #: same statistics.
    minimiser_lambdas: tuple[float, float, float, float]
    minimiser_lambdas_exact: tuple[F, F, F, F]
    notes: str


BBM92_IDEAL = Bbm92Instance(
    instance_id="BBM92-IDEAL",
    test_coin=F(1, 5),
    alice_basis_weights=(F(1, 2), F(1, 2)),
    bob_basis_weights=(F(1, 2), F(1, 2)),
    sifted_generation=F(1, 5),
    error_rate=F(0),
    honest_lambdas=(1.0, 0.0, 0.0, 0.0),
    honest_lambdas_exact=(F(1), F(0), F(0), F(0)),
    minimiser_lambdas=(1.0, 0.0, 0.0, 0.0),
    minimiser_lambdas_exact=(F(1), F(0), F(0), F(0)),
    notes="""\
THE INSTANCE B-1, B-4 AND B-5 ARE STATED ON: an ideal pair, no loss, no error,
ideal detectors.

THE HONEST STATE IS |Phi^+>, i.e. lambda = (1, 0, 0, 0) in the (bit, phase)
order, delivered one arm to each station every round.

THE SIFTED GENERATION PROBABILITY. A round is a generation round with
probability 1 - gamma = 4/5; both stations click (ideal detectors at unit
transmittance); their bases match in Z with probability
p^A_Z p^B_Z = 1/4. So
  P_gen = (1 - gamma) p^A_Z p^B_Z = (4/5)(1/4) = 1/5 ,
and the matched-X generation rounds -- another 1/5 of all rounds -- carry the
unsifted letter, as do the mismatched ones.

WHAT MAKES IT THE ANALOGUE OF T1. In the (Z, Z) class Alice's outcome is
uniform and Bob's is perfectly correlated with it, so the branch operator has
two equally weighted rows carrying key values 0 and 1: exactly the structure
that makes tests/support/bb84_targets.honest_point_objective
alpha-independent.""",
)


BBM92_SYMMETRIC_ERROR = Bbm92Instance(
    instance_id="BBM92-SYMMETRIC-ERROR",
    test_coin=F(1, 5),
    alice_basis_weights=(F(1, 2), F(1, 2)),
    bob_basis_weights=(F(1, 2), F(1, 2)),
    sifted_generation=F(1, 5),
    error_rate=F(1, 32),
    honest_lambdas=(61 / 64, 1 / 64, 1 / 64, 1 / 64),
    honest_lambdas_exact=(F(61, 64), F(1, 64), F(1, 64), F(1, 64)),
    minimiser_lambdas=(961 / 1024, 31 / 1024, 31 / 1024, 1 / 1024),
    minimiser_lambdas_exact=(F(961, 1024), F(31, 1024), F(31, 1024), F(1, 1024)),
    notes="""\
THE INSTANCE B-2, B-3 AND B-6 ARE STATED ON: BBM92-IDEAL with a symmetric
error e = 1/32 in both bases, the pair depolarised on its way to the stations.

WHY e = 1/32 AND NOT A ROUNDER NUMBER. The textbook figure B-2 quotes with the
leakage is 1 - 2 h2(e), which is NEGATIVE for every e above 0.11002786...
(the zero crossing Q* of tests/support/bb84_targets.py). At e = 1/8 it is
-0.0871..., so an instance at that error would freeze a "key rate" that does
not exist. At e = 1/32 it is +0.5987553513745707, positive and comfortably
inside the regime.

THE HONEST STATE, depolarised: lambda = (1 - 3e/2, e/2, e/2, e/2)
= (61/64, 1/64, 1/64, 1/64), whose bit error lambda_10 + lambda_11 = 1/32 and
phase error lambda_01 + lambda_11 = 1/32 are both e. EVERY WEIGHT IS DYADIC.

THE MINIMISER AT THE SAME STATISTICS, which is NOT the honest state:
lambda = ((1-e)^2, e(1-e), e(1-e), e^2) = (961, 31, 31, 1)/1024, the state
whose bit and phase errors are e and INDEPENDENT. Also dyadic. B-2's derivation
shows it is the worst state at these statistics, and the two values differ:
0.7993776756872853 against 0.8533563491773406 per sifted round in the
alpha -> 1+ limit.""",
)


BBM92_INSTANCES: tuple[Bbm92Instance, ...] = (BBM92_IDEAL, BBM92_SYMMETRIC_ERROR)


def bbm92_instance(instance_id: str) -> Bbm92Instance:
    """Return the instance with this id, refusing an unknown one."""
    for instance in BBM92_INSTANCES:
        if instance.instance_id == instance_id:
            return instance
    raise KeyError(f"no BBM92 instance with id {instance_id!r}")


# ===========================================================================
#  B-6's separation witness, as exact rational data
# ===========================================================================

Matrix = tuple[tuple[F, ...], ...]

#: ``reductions/lem:party-local`` (iv), transcribed as data: a state on
#: ``Q_{f^c} (x) Q_f`` that satisfies the SCALAR entry and violates the
#: PARTY-LOCAL one. It is what makes B-6's inclusion STRICT, hence B-6's
#: relation non-vacuous.
PARTY_LOCAL_SEPARATION: dict[str, object] = {
    "case_id": "PARTY-LOCAL-STRICT",
    "claim": "reductions/lem:party-local",
    #: omega = (|00><00| + |11><11|)/2 on Q_{f^c} (x) Q_f, the traced qubit
    #: written SECOND.
    "omega": (
        (F(1, 2), F(0), F(0), F(0)),
        (F(0), F(0), F(0), F(0)),
        (F(0), F(0), F(0), F(0)),
        (F(0), F(0), F(0), F(1, 2)),
    ),
    #: O_hat = |0><0| on Q_f, c = 1/2, so D = O_hat - c 1.
    "observable": ((F(1), F(0)), (F(0), F(0))),
    "constant": F(1, 2),
    "scalar_entry_value": F(1, 2),
    "scalar_entry_holds": True,
    #: tr_{Q_f}[(1 (x) D) omega] on Q_{f^c}: eigenvalues +1/4 and -1/4.
    "party_local_operator": ((F(1, 4), F(0)), (F(0), F(-1, 4))),
    "party_local_holds": False,
    "derivation": """\
Lemma lem:party-local (iv) exhibits a channel Lambda that DISCARDS its input
and prepares varsigma = (|00><00| + |11><11|)/2 on Q_{f^c} (x) Q_f. Then
Lambda^dagger(Y) = tr[Y varsigma] 1_B, so with O_hat = |0><0| on Q_f,
  Lambda^dagger(1 (x) O_hat) = (1/2) 1_B >= c 1_B  at c = 1/2 ,
and every squashed attack satisfies the SCALAR entry
tr[(1 (x) O_hat) omega] = 1/2 >= c tr omega = 1/2 -- with equality, which is
the sharpest case. But every such attack outputs omega = varsigma, and with
D = O_hat - (1/2) 1,
  tr_{Q_f}[(1 (x) D) omega] = (1/2)(1/2)|0><0| + (1/2)(-1/2)|1><1|
                            = (1/4)|0><0| - (1/4)|1><1| ,
whose eigenvalues are +1/4 and -1/4: NOT positive semidefinite. So the scalar
entry holds and the party-local one fails, and the feasible-set inclusion of
B-6 is STRICT. EVERY NUMBER HERE IS EXACT AND THE WHOLE CHECK IS FOUR
MULTIPLICATIONS.

WHAT IT ALSO SHOWS, and why the entry carries it rather than a BBM92-sized
example: the party-local form NEEDS the product structure of the channel. The
Lambda above is not a product, and the lemma's hypothesis is exactly what
excludes it. A party-local entry emitted for a factor the squasher does not
leave untouched would be unsound, which is the plan's section 2.8 item 10.""",
}


# ===========================================================================
#  The entry record
# ===========================================================================


@dataclass(frozen=True)
class Bbm92OracleEntry:
    """One frozen expected value, or one relation, with its derivation."""

    oracle_id: str
    #: Claim ids of ``spec/modules/**`` AT HEAD, verified to resolve by the
    #: integrity test.
    claims: tuple[str, ...]
    kind: str
    subject: str
    #: The ``instance_id`` this entry is stated on.
    instance: str
    derivation: str
    #: The hypotheses, stated so that the entry cannot be satisfied by
    #: reinterpretation: which receiver, which sifting, which reconciliation
    #: direction, which alpha, and what a per-round figure normalises by.
    hypotheses: tuple[str, ...]
    #: What the implementer's test must compare, once the code exists. THIS
    #: FILE WRITES NO SUCH TEST.
    observable: str
    value: F | float | None = None
    value_closed_form: str = ""
    closed_form: Callable[[float], float] | None = None
    frozen_values: tuple[tuple[float, float], ...] = ()
    #: For ``kind = "relation"``: the relation, with no number.
    relation: str | None = None
    #: True where the plan says a statement is "recorded, not asserted".
    recorded_not_asserted: bool = False
    repin_after_c3: tuple[str, ...] = field(default_factory=tuple)
    #: What a later re-read of the accepted claims found. The DERIVATION above
    #: is frozen evidence and is never edited to agree with a later structure
    #: (the mechanism ``registry_transmitter.PCOracleEntry.revalidation`` uses);
    #: a contradiction would be a FINDING and not an edit.
    revalidation: str = ""
    assurance: str = ASSURANCE


# ===========================================================================
#  Group B -- the six targets of 05-validation.md section 5.3
# ===========================================================================


O_BBM92_B1_IDEAL_ONE_BIT = Bbm92OracleEntry(
    oracle_id="O-BBM92-B1-IDEAL-ONE-BIT",
    claims=(
        "meat-core/thm:branch-formula",
        "meat-core/def:branch",
        "foundations/def:pinching",
        "meat-core/def:feasible",
        "meat-core/rem:modes-da1",
        "meat-core/def:declaration",
        "meat-core/def:joint-sectors",
        "transmitter/rem:da1",
        "protocol-compiler/def:weighted",
        "protocol-compiler/def:declaration",
        "protocol-compiler/ex:two-party-shape",
        "reductions/thm:emitted-product",
    ),
    kind="toy-instance",
    subject=(
        "B-1: at an ideal pair with no loss, no error and ideal detectors the "
        "entropy term is exactly one bit per sifted generation round at every "
        "alpha, so the objective at the honest point is P_gen = 1/5 exactly."
    ),
    instance="BBM92-IDEAL",
    derivation="""\
THE COMPUTATION, in the objective's own quantities and with d_A = 1 throughout.
The single label x_0 has M_{x_0} = [1], so the branch operator of
Eq. eq:kraus reduces to
  K_kappa = sum_{v in a^{-1}(kappa)} |r(x_0,v)>_R (x) |x_0,v>_{XY}
            (x) |kappa> (x) sqrt(F_v) ,
with F_{(b,y),(b',y')} = p^A_b p^B_{b'} |y^b><y^b| (x) |y'^{b'}><y'^{b'}| the
product effects of the two ideal stations (the factorised sector map of
derivations/05 section 5.1; each station has one trivial sector here, no flags
being possible at an ideal detector).

THE (Z, Z) PASS CLASS AT |Phi^+>. With the coin weight 1 - gamma inside the
elements (def:weighted, first form),
  sqrt(F_{(Z,y),(Z,y')}) |Phi^+> = sqrt((1-gamma) p^A_Z p^B_Z)
      delta_{y,y'} |yy> / sqrt 2 ,
so G_gen is supported on the two rows y = y' = 0 and y = y' = 1, of EQUAL
weight P_gen/2 each, and those two rows carry the key values 0 and 1 (the key
is Alice's outcome, r(x, v) = bit(v_A)). They are therefore already orthogonal
in R, the pinching Z changes nothing, and
  T_gen = 2 (P_gen/2)^alpha = 2^{1-alpha} P_gen ,   tr G_gen = P_gen ,
  K_gen = T_gen + P_gen - tr G_gen = 2^{1-alpha} P_gen .
At q = Phi[omega] every divergence term of Eq. eq:objective vanishes and
  O_alpha = (P_gen/(alpha-1)) log2(P_gen / (2^{1-alpha} P_gen)) = P_gen ,
AT EVERY alpha IN (1, inf): the 2^{1-alpha} inside the logarithm cancels the
1/(alpha-1) outside it, which is the same cancellation
tests/support/bb84_targets.honest_point_objective records for the qubit case.

THE NUMBER. P_gen = (1 - gamma) p^A_Z p^B_Z = (4/5)(1/2)(1/2) = 1/5 exactly,
and "one bit per sifted generation round" is O_alpha / P_gen = 1.

WHY THE UNTRUSTED MODE CHANGES NOTHING HERE. At d_A = 1 the two source modes
give the same feasible set (rem:modes-da1 (b)), and the honest point is
feasible in either: it is positive, has trace one and reproduces the declared
statistics. The value is the objective AT that point, so it bounds h_low from
above; at zero error the bound is attained in the limit alpha -> 1+, where
1 - h2(0) = 1.

THE FOIL THIS ENTRY CARRIES IMPLICITLY. An implementation that applied the coin
bias as a fraction AFTER computing a renormalised distribution would report
1/4 here instead of 1/5, because (1 - gamma) would cancel between P_gen and
K_gen. B-5 freezes that separately as the state-independent generation mass.""",
    hypotheses=(
        "Ideal stations: unit efficiency, no dark counts, exactly one click "
        "per round on each side, no flag sector. With loss the sifted mass "
        "changes and with dark counts the correlation does.",
        "Key from matched-Z generation rounds only, key holder Alice, direct "
        "reconciliation r(x, v) = bit(v_A).",
        "The acceptance map sends a sifted generation round to gen and an "
        "unsifted one to a letter of its own, so P_gen IS the sifted "
        "generation probability and the per-round figure divides by it.",
        "The coin enters through def:weighted's first form, as a weight inside "
        "the POVM elements (A-TSM), never as a fraction applied afterwards.",
        "d_A = 1, untrusted mode, no marginal condition and no certificate "
        "(transmitter/rem:da1). Declaring tau_A = 1/d_A stays forbidden.",
        "The value is the objective at the honest point: an UPPER bound on "
        "h_low, attained only in the alpha -> 1+ limit at zero error.",
    ),
    observable=(
        "The engine's entropy term on the BBM92 declaration at omega = "
        "|Phi^+><Phi^+| equals 1/5 at every alpha of the grid, to the run's "
        "declared tolerance, and the per-sifted-round figure is 1.0 bit. No "
        "solver: the point is given."
    ),
    value=F(1, 5),
    value_closed_form="O_alpha = P_gen = (1 - gamma) p^A_Z p^B_Z = 1/5",
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (reductions 0.2.0,
protocol-compiler 0.2.0, meat-core 1.1.0). THE VALUE 1/5 STANDS AT
EVERY alpha; nothing was edited.

THE SHAPE IS AN ACCEPTED EXAMPLE NOW. protocol-compiler/ex:two-party-shape
writes out exactly this declaration: untrusted mode with d_A = 1, the marginal
slot holding no marginal, X = {x_0} and M_{x_0} = [1]; a sector map with NO
factor tagged A and two factors tagged Q, one per party; the product family
F_{(v_a,v_b)} = F^a (x) F^b of def:declaration (DX3) with no product matrix
ever formed; and the readouts rd_A = v_a, rd_B = v_b, which that example names
as NOT the default partition. Every slot this entry's derivation uses is that
example's, so the shape is no longer something the entry has to argue for.
TWO HYPOTHESES I CHECKED RATHER THAN ASSUMED, both of which could have bitten.
(1) THE ENSEMBLE FORM IS REFUSED IN UNTRUSTED-SOURCE MODE (def:declaration
(DX4): it "exists in trusted-source mode only"). This instance declares Alice's
slot in POVM form, M_{x_0} = [1], so nothing here reads an ensemble form and
the refusal touches no entry of this file. (2) lem:rank-one-sector is stated in
TRUSTED-source mode with the DEFAULT readouts; this instance has neither, so
that lemma is NOT pinned anywhere in this file and the branch computation
frozen here remains its own derivation. The product-set property of the pass
class it needs follows from the same induction on the transcript as that
lemma's (ii), read for the readouts rd_A = v_a, rd_B = v_b: each message is a
function of one factor of v and of the earlier messages (def:declaration (DX5)).
reductions/thm:emitted-product is pinned as what supplies the product squashing
channel and the factorised emission the two stations' families come from; there
is NO `thm:tensor-instance`.""",
)


O_BBM92_B2_SYMMETRIC_ERROR = Bbm92OracleEntry(
    oracle_id="O-BBM92-B2-SYMMETRIC-ERROR",
    claims=(
        "meat-core/thm:branch-formula",
        "meat-core/thm:oracle",
        "meat-core/rem:oracle",
        "meat-core/def:feasible",
        "foundations/def:renyi",
        "meat-core/def:joint-sectors",
        "reductions/prop:tensor",
        "reductions/cor:blockdiag",
        "reductions/thm:emitted-product",
    ),
    kind="toy-instance",
    subject=(
        "B-2: with a symmetric error e the alpha -> 1+ limit of the entropy "
        "term is 1 - h2(e) per sifted round, attained at the INDEPENDENT-error "
        "state and not at the depolarised honest one; with the leakage h2(e) "
        "the textbook figure is 1 - 2 h2(e). All three numbers frozen."
    ),
    instance="BBM92-SYMMETRIC-ERROR",
    derivation="""\
THE CLOSED FORM FOR ONE MATCHED-BASIS CLASS AT A BELL-DIAGONAL POINT, derived
here for d_A = 1 and a product receiver. Let omega on Q_A (x) Q_B be
Bell-diagonal with weights lambda_{ij}, i the bit-error index and j the phase
index in the order (Phi+, Phi-, Psi+, Psi-). In the (Z, Z) class the four
output rows are indexed by the two stations' outcomes (y_A, y_B) and carry the
key value y_A. |Phi^{+-}> populate the rows (0,0) and (1,1); |Psi^{+-}>
populate (0,1) and (1,0). So G_gen is block diagonal with two 2x2 blocks,
  (P_gen/2) [[l_00 + l_01, l_00 - l_01], [l_00 - l_01, l_00 + l_01]]
      on the rows (0,0), (1,1) ,
  (P_gen/2) [[l_10 + l_11, l_10 - l_11], [l_10 - l_11, l_10 + l_11]]
      on the rows (0,1), (1,0) ,
whose eigenvalues are P_gen lambda_{ij} with the symmetric and antisymmetric
eigenvectors. IN BOTH BLOCKS THE TWO ROWS CARRY DIFFERENT KEY VALUES, so the
pinching Z deletes both off-diagonals and leaves Z(G^{1/alpha}) diagonal with
entries P_gen^{1/alpha}(l_{i0}^{1/alpha} + l_{i1}^{1/alpha})/2, twice each.
Raising to the alpha and tracing:
  T_gen = 2^{1-alpha} P_gen S ,
  S = sum_i (l_{i0}^{1/alpha} + l_{i1}^{1/alpha})^alpha ,
  K_gen = T_gen , since tr G_gen = P_gen in this class ,
  h = 1 - log2 S / (alpha - 1)    bits per sifted round .
THE SAME FORMULA APPEARS IN THE DECOY REGISTRY'S OT4 for the one-photon Alice
sector; it is derived again here because the systems and the pinched register
are different -- there Alice's retained qubit, here Alice's STATION -- and a
registry may not borrow another instance's derivation.

THE alpha -> 1+ LIMIT IS 1 - H(phase | bit). Expanding
(l_{i0}^{1/alpha} + l_{i1}^{1/alpha})^alpha to first order in alpha - 1 gives
sum_i p_i [1 - (alpha-1) h2(l_{i1}/p_i) ln 2] with p_i = l_{i0} + l_{i1}, so
log2 S / (alpha-1) -> -H(phase | bit) and h -> 1 - H(phase | bit).

THE MINIMUM AT SYMMETRIC STATISTICS IS 1 - h2(e), AND THE MINIMISER IS NOT THE
HONEST STATE. The test rounds announce both outcomes in both matched bases, so
the feasible set at the honest singleton has BOTH
  bit error  l_10 + l_11 = e ,   phase error  l_01 + l_11 = e .
Maximising H(phase | bit) over that set: conditioning never increases entropy,
so H(phase | bit) <= H(phase) = h2(e), with equality exactly when the bit and
phase indices are INDEPENDENT, i.e.
  lambda = ((1-e)^2, e(1-e), e(1-e), e^2) ,
which satisfies both constraints. Hence
  min h = 1 - h2(e) = 0.7993776756872853  at e = 1/32 ,
and the total entropy term is P_gen (1 - h2(e)) = (1/5)(0.7993776756872853)
= 0.15987553513745706.
AT THE DEPOLARISED HONEST STATE lambda = (61, 1, 1, 1)/64 the same functional
gives
  1 - [(31/32) h2(1/62) + 1/32] = 0.8533563491773406 ,
strictly larger, with the total 0.17067126983546812. FREEZING BOTH IS THE
POINT: a test that compared a solver's limit against the honest state's value
would be comparing against the wrong number, which is the distinction
tests/support/bb84_targets.limit_at_depolarized_state records for the qubit
case.

WITH THE LEAKAGE. Reconciling the sifted key costs h2(e) bits per sifted round
at the Shannon limit, so the textbook per-sifted-round figure is
1 - 2 h2(e) = 0.5987553513745707 at e = 1/32, and per channel use
P_gen (1 - 2 h2(e)) = 0.11975107027491414. lambda_EC IS A DECLARED PARAMETER
THAT NO PART OF meat-core DERIVES, so this is a statement about that choice and
not about the engine; it is the ceiling 05-validation.md section 5.4 records
against asymptotic BBM92.

THE FINITE-alpha TABLE, frozen from independent_error_bits at e = 1/32, is the
minimiser's bits per sifted round and decreases in alpha. It is NOT h_low at
finite alpha: the infimum there is over all feasible states and the
Bell-diagonal family's minimiser need not be the global one. The table is
frozen as the BELL-DIAGONAL value it is.""",
    hypotheses=(
        "Symmetric error e in both bases, observed on test rounds in both "
        "bases, so the feasible set constrains BOTH the bit and the phase "
        "error. With only the phase error constrained the minimiser is "
        "(1-e, e, 0, 0) and the value is the same 1 - h2(e); with only the bit "
        "error constrained it is not.",
        "The alpha -> 1+ limit, as meat-core/thm:oracle defines it. The "
        "frozen table at finite alpha is the BELL-DIAGONAL family's value, not "
        "h_low.",
        "Ideal stations, key from matched-Z rounds, direct reconciliation, "
        "P_gen the sifted generation probability, alpha in (1, inf).",
        "1 - 2 h2(e) assumes lambda_EC at the Shannon limit for the sifted "
        "key; lambda_EC is declared and never derived.",
        "d_A = 1, untrusted mode, no marginal condition.",
    ),
    observable=(
        "lim h_low as alpha -> 1+ on the BBM92 declaration at the honest "
        "singleton, per sifted round, against 0.7993776756872853 -- as an "
        "EQUALITY within the solver gap if the minimiser is reached, and as an "
        "upper bound otherwise; and the objective at the two named "
        "Bell-diagonal points against independent_error_bits and "
        "honest_point_bits on the frozen grid, which needs no solver."
    ),
    value=0.7993776756872853,
    value_closed_form=(
        "lim per sifted round = 1 - h2(1/32); total = (1/5)(1 - h2(1/32))"
    ),
    closed_form=lambda alpha: independent_error_bits(1 / 32, alpha),
    frozen_values=(
        (1.05, 0.7864654922258844),
        (1.25, 0.7349934309298087),
        (1.5, 0.6738478225010316),
        (1.75, 0.6184048161476179),
        (1.9, 0.5881411541270958),
    ),
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS. ALL THREE NUMBERS
STAND -- 0.7993776756872853 per sifted round, 0.8533563491773406 at the honest
point, 0.5987553513745707 with the leakage -- and nothing was edited.

WHAT CARRIES THE BLOCK STRUCTURE. def:joint-sectors makes the deficit a
joint-sector object whose Kraus operators act through
sqrt(M^{(t)}_x) (x) sqrt(F^{(s)}_v); at |T| = 1 it records that the joint
sectors ARE the product sectors of the two stations, which is the indexing the
frozen derivation uses. reductions/thm:emitted-product and prop:tensor supply
the product squasher and the product decomposition, cor:blockdiag the block
diagonality of the emitted family.
THE MINIMISER ARGUMENT IS UNTOUCHED BY THE ACCEPTED CLAIMS and remains this file's own: no
accepted claim states that H(phase | bit) <= h2(e) with equality iff
independence, and none needs to -- it is the data-processing statement the
derivation gives in one line. So the distinction between the infimum and the
honest point stays this entry's to carry, which is why both numbers are frozen.
THE FINITE-alpha TABLE IS STILL NOT h_low, and the accepted claims add no claim that would make
it one: it is the Bell-diagonal family's value, as labelled.""",
)


O_BBM92_B3_UNTRUSTED_IS_LARGER = Bbm92OracleEntry(
    oracle_id="O-BBM92-B3-UNTRUSTED-IS-LARGER",
    claims=(
        "meat-core/def:feasible",
        "meat-core/rem:modes-da1",
        "meat-core/lem:product-marginal",
        "meat-core/def:declaration",
        "transmitter/rem:da1",
        "transmitter/def:srcert",
        "reductions/thm:two-sided",
    ),
    kind="relation",
    subject=(
        "B-3: with ideal qubit measurements on both sides, "
        "h_low(BBM92, d_A = 1) <= h_low(BB84, tau_A = 1_A/2) at matched "
        "statistics, because the untrusted feasible set CONTAINS the trusted "
        "one. The expected EQUALITY at symmetric statistics is RECORDED, NOT "
        "ASSERTED."
    ),
    instance="BBM92-SYMMETRIC-ERROR",
    derivation="""\
THE IDENTIFICATION, which has to be exact or the comparison is empty. Take the
qubit BB84 declaration of instances/bb84 in trusted mode: A a qubit with
tau_A = 1_A/2, M_{(b,a)} = p^A_b |conj(a^b)><conj(a^b)|, Bob's ideal station
F_{(b',y)} = p^B_{b'} |y^{b'}><y^{b'}|. Take the BBM92 declaration of this
instance with d_A = 1 and F^A_{(b,a)} = p^A_b |conj(a^b)><conj(a^b)| on
Q_A -- Alice's STATION carrying the operators that were her source-replacement
POVM. Under the identification A <-> Q_A the two objectives are THE SAME
FUNCTIONAL of omega: Eq. eq:kraus reads Alice's side through sqrt(M_x) in one
case and sqrt(F^A_{v_A}) in the other, on the same operators, and the
announcement maps, the sifting predicate, the key rule and the acceptance map
are matched letter for letter (the conjugation convention is the compiler's and
is carried along unchanged).

THE ONE DIFFERENCE IS THE MARGINAL CONDITION. Eq. eq:feas in trusted mode
imposes omega_A = tau_A = 1_A/2; in untrusted mode it imposes NO marginal
condition, only tr omega = 1 and the entries (rem:modes-da1). Hence
  Feas(BB84) = Feas(BBM92) intersect {omega_{Q_A} = 1_{Q_A}/2}
             SUBSET OF Feas(BBM92) ,
and an infimum over a larger set is no larger:
  h_low(BBM92) <= h_low(BB84) .
"AN UNTRUSTED SOURCE IS THE LARGER ATTACK FAMILY", exactly. Nothing else is
needed: no channel, no attack, no honest model.

THE INCLUSION IS STRICT AS A SET. The state |0><0|_{Q_A} (x) 1_{Q_B}/2 is
positive, normalised and block diagonal, and it is excluded by the marginal
condition while satisfying every untrusted constraint of this declaration --
which is the non-vacuity witness protocol-compiler/thm:pc12 (iii) already
records the other way round ("the marginal DELETES STATES from Eq. eq:feas and
the attestation IS DOING WORK"). SO THE TWO PROGRAMS ARE GENUINELY DIFFERENT
PROGRAMS, and the relation is not an identity by accident.

THE EQUALITY AT SYMMETRIC STATISTICS IS RECORDED AND NOT ASSERTED, as the plan
asks. What IS derived, at one point and one limit: at e_Z = e_X = e and
alpha -> 1+ both programs have the value 1 - h2(e) per sifted round -- BBM92's
by B-2's independence argument, BB84's by
tests/support/bb84_targets.von_neumann_limit, whose minimiser (1-e, e, 0, 0)
is Bell-diagonal and therefore has omega_A = 1_A/2 and lies in BOTH feasible
sets. At e = 1/32 that common value is 0.7993776756872853. THAT COINCIDENCE IS
A RECORD AT ONE POINT IN ONE LIMIT AND IS NOT A CLAIM OF EQUALITY: at finite
alpha the untrusted program may reach strictly lower using a state with a
biased marginal, and nothing here excludes it. An implementation's test may
assert the INEQUALITY and may record the difference; it may not assert zero.

WHAT MATCHED STATISTICS MEANS HERE, since it is where the target is
underdetermined and the choice is mine: both declarations announce the same
things and observe the same acceptance vector, including BOTH basis error
rates. The plan's BB84 instance has no Z-basis statistic at all (its phi maps
the whole (Z, Z) class to gen), so a comparison against that instance would be
comparing two different acceptance sets; the entry fixes the BB84 side to
carry the same test statistics as the BBM92 side, and says so.""",
    hypotheses=(
        "Ideal qubit measurements on both sides, the same POVMs under the "
        "identification A <-> Q_A, the same announcements, sifting, key rule "
        "and acceptance map, the same alpha and the same acceptance set.",
        "Matched statistics means the same observed acceptance vector, both "
        "basis error rates included; the BB84 side is fixed to carry the "
        "Z-basis test statistic that its own instance does not.",
        "BB84 in TRUSTED mode with the marginal condition omega_A = 1_A/2 "
        "supplied by a verified certificate; BBM92 in untrusted mode at "
        "d_A = 1 with no marginal condition and no certificate.",
        "Both declarations key from the matched-Z rounds with ALICE as holder "
        "and direct reconciliation, and both per-sifted-round figures divide "
        "by their own P_gen, which the identification makes the same number.",
        "The equality at symmetric statistics is RECORDED AT ONE POINT IN THE "
        "alpha -> 1+ LIMIT and is not asserted at finite alpha or in general.",
    ),
    observable=(
        "h_low from the two declarations at the same acceptance vector and the "
        "same alpha: BBM92's <= BB84's, with both Frank-Wolfe gaps beside the "
        "numbers and a difference below the gap named as solver noise, never "
        "as equality. The recorded coincidence at alpha -> 1+ is a RECORD in "
        "the run log and not an assertion."
    ),
    relation=(
        "h_low(BBM92, d_A = 1) <= h_low(BB84, tau_A = 1_A/2) at matched "
        "statistics and matched POVMs, because Feas(BB84) is Feas(BBM92) "
        "intersected with the marginal condition."
    ),
    recorded_not_asserted=True,
    value=0.7993776756872853,
    value_closed_form=(
        "the RECORDED coincidence at alpha -> 1+ and e = 1/32: both sides "
        "1 - h2(1/32) per sifted round"
    ),
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS. THE RELATION AND
THE RECORDED COINCIDENCE STAND; the equality is still NOT asserted.

THE FEASIBLE-SET INCLUSION IS STILL THE WHOLE ARGUMENT, and def:declaration
(DX4)'s untrusted clause sharpens one half of it in this entry's favour: the
ensemble form exists in trusted mode only, so the untrusted side of the
comparison cannot even be declared in the form the trusted side may use. That
is a statement about the DECLARATION and not about the feasible sets, so it
changes no number; it is recorded because a reader might otherwise take the two
sides to be the same declaration in two modes, and they are not.
reductions/thm:two-sided is pinned as the claim that makes the trusted side's
certificate a reduction at all -- its (ii) now holding for a separable
specified system after a later pass -- and not as a step of this
relation, which reads only def:feasible's two modes.
WHAT THE ACCEPTED CLAIMS DO NOT GIVE, and the entry's mark stands because of it: no accepted
claim says the two infima agree at symmetric statistics, at any alpha. The
coincidence frozen here remains ONE POINT IN ONE LIMIT, recorded and not
asserted.""",
)


O_BBM92_B4_STATION_EXCHANGE = Bbm92OracleEntry(
    oracle_id="O-BBM92-B4-STATION-EXCHANGE",
    claims=(
        "meat-core/def:declaration",
        "meat-core/def:maps",
        "meat-core/thm:protocol-channel",
        "meat-core/ass:keyreg",
        "meat-core/def:joint-sectors",
        "reductions/prop:tensor",
        "reductions/thm:emitted-product",
        "protocol-compiler/ex:two-party-shape",
    ),
    kind="structural-identity",
    subject=(
        "B-4: exchanging the two stations TOGETHER WITH the key holder leaves "
        "h_low unchanged for identical devices -- an isomorphism of the "
        "declaration, not a numerical coincidence. For devices that differ the "
        "swapped declaration is a DIFFERENT declaration and no equality is "
        "asserted."
    ),
    instance="BBM92-IDEAL",
    derivation="""\
THE SWAP, written out as the map it is. Let SWAP be the unitary on
Q_A (x) Q_B exchanging the two factors, and consider the declaration obtained
by applying it everywhere:
  the sector map:      (s_A, s_B)  ->  (s_B, s_A) , the factorised map's two
      party-scoped factors exchanged together with their party labels
      (derivations/05 section 5.1);
  the effects:         F_{(v_A,v_B)} = F^A_{v_A} (x) F^B_{v_B}
                       ->  F^B_{v_B} (x) F^A_{v_A} ;
  the alphabet:        V = V_A x V_B -> V_B x V_A , and the announcement maps
      a_A, a_B exchanged with it;
  the readouts:        rd_A(x, v) = v_A  <->  rd_B(x, v) = v_B ;
  the key holder:      h = A -> h = B, with r(x, v) = bit(v_A) -> bit(v_B) .
FOR IDENTICAL DEVICES -- the same sector map, the same POVM, the same basis
weights, the same announcements on both stations -- THE SWAPPED DECLARATION IS
THE ORIGINAL ONE, field for field, after the relabelling: every emitted object
is the image of an emitted object of the same shape, and the relabelling of V
is a bijection of a finite alphabet.

WHY h_low CANNOT MOVE. The objective Eq. eq:objective is a function of the
acceptance masses P_chat and the kernels K_chat, both built from the branch
operators of Eq. eq:kraus. Conjugating omega by SWAP and applying the
relabelling above maps each K_kappa to K_{kappa'} up to a unitary on the
registers XY C_A C_B -- which is traced or dephased in every quantity thm:branch-formula
defines -- and carries the pinched register R to itself, because the key value
of a round is the SAME BIT after the swap (the holder swapped with the
stations). So T_chat, tr G_chat and P_chat are unchanged at the image point,
Feas maps onto Feas bijectively (omega -> SWAP omega SWAP^dagger preserves
positivity, trace and every entry, the entries being exchanged with their
parties), and the two infima are equal. THE STATEMENT IS AN ISOMORPHISM AND
NOT AN INEQUALITY: equality holds exactly, not to a tolerance.

WHAT MUST BE CHECKED FOR THE TEST NOT TO BE VACUOUS, and this is the half an
implementation gets wrong. For identical devices the swapped declaration is
BYTE-FOR-BYTE the original one after relabelling, so a test that merely ran the
solver twice on the same data would assert nothing about the swap. The test
must therefore (i) build the swapped declaration through the declaration
machinery -- exchanging the party labels, the factor order and the key holder
-- and check it EQUALS the original as data; and (ii) exhibit a pair of
stations that DIFFER (different basis weights, different efficiencies,
different cutoffs) and check the swapped declaration DIFFERS from the original
as data. Part (ii) asserts nothing about h_low: with different devices the two
declarations are different programs and this entry claims no relation between
their values.

WHY SWAPPING THE STATIONS WITHOUT THE HOLDER IS A DIFFERENT OPERATION and is
not covered: the key would then be the OTHER party's bit, which is reverse
reconciliation, and nothing here says that gives the same rate. B-4 is the
symmetry of the declaration, not a statement about the reconciliation
direction.""",
    hypotheses=(
        "IDENTICAL devices: the same sector map, POVM, basis weights, "
        "announcement maps and cutoffs on both stations. For devices that "
        "differ nothing is asserted about h_low.",
        "The swap exchanges the stations TOGETHER WITH the key holder, so the "
        "key value of every round is unchanged. Swapping the stations alone is "
        "reverse reconciliation and is a different question.",
        "The two-station timing premise: no round-j announcement of either "
        "party is released before both round-j systems have been delivered "
        "(derivations/05 section 5.3). It is symmetric under the swap, which "
        "is why the swapped declaration is admissible at all.",
        "Equality is EXACT, being an isomorphism of the declaration; a "
        "solver-level test still compares within the Frank-Wolfe gap, because "
        "the solver is not exact.",
    ),
    observable=(
        "(i) The swapped declaration, built by the declaration machinery, "
        "equals the original as data for identical stations, and h_low agrees "
        "within the gap. (ii) For stations that differ in one parameter the "
        "swapped declaration DIFFERS from the original as data -- without "
        "which (i) asserts nothing."
    ),
    value=F(0),
    value_closed_form="h_low(swapped) - h_low(original) = 0 exactly",
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS. THE EXACT ZERO
STANDS.

THE RE-PIN RESOLVED TO A CLAIM ALREADY PINNED. There is no
`reductions/thm:tensor-instance`: the factorised emission is
reductions/thm:emitted-product, which this entry pinned from the start, so this
entry's repin list closes with no addition to its authority --  and that is
worth recording rather than leaving silent.
WHAT IS ADDED IS THE SHAPE. protocol-compiler/ex:two-party-shape fixes the
component list the swap permutes -- two factors tagged Q with their party
labels, their own sector maps, alphabets and families, the readouts
rd_A = v_a and rd_B = v_b, the transcript and the key rule
r^0_A(v_a, kappa) = v_a -- so "the swapped declaration equals the original as
data" is now a statement about a named set of slots. def:joint-sectors is what
makes the permuted sector list the same joint-sector list.
ONE FACT OF THE ACCEPTED CLAIMS I CHECKED BECAUSE IT COULD HAVE BITTEN. meat-core/thm:removal
sets no sector removable when the list carries a party-local entry or the
declaration has more than one measured factor -- BBM92 has two. NO ENTRY OF
THIS FILE ASSERTS THAT ANY SECTOR IS REMOVABLE, here or anywhere, so the
restriction contradicts nothing; what it does mean is that the swap permutes a
sector list from which nothing may be deleted, which is if anything simpler
than what the derivation assumed.""",
)


O_BBM92_B5_COIN_MASS = Bbm92OracleEntry(
    oracle_id="O-BBM92-B5-COIN-MASS",
    claims=(
        "protocol-compiler/def:weighted",
        "protocol-compiler/lem:weighted",
        "meat-core/def:maps",
        "meat-core/thm:protocol-channel",
        "meat-core/def:declaration",
        "protocol-compiler/def:declaration",
        "protocol-compiler/ex:transcript",
        "reductions/ass:tsm",
    ),
    kind="structural-identity",
    subject=(
        "B-5: the test coin enters only through the public-choice weights, so "
        "the total mass of the generation branch is exactly 1 - gamma = 4/5 "
        "for EVERY feasible state; the split of that mass between the sifted "
        "and unsifted letters is state dependent and is not."
    ),
    instance="BBM92-IDEAL",
    derivation="""\
THE IDENTITY. By protocol-compiler/def:weighted (first form) a public choice
enters as a WEIGHT INSIDE the POVM elements: the coin value k in {gen, test}
with probability weights (1 - gamma, gamma) produces the family
  F_{(k, v)} = w_k F_v ,   sum_v F_v = 1_Q  for each k ,
so by lem:weighted (i) the whole family is a POVM and, for every omega with
tr omega = 1,
  sum_{v} tr[(1 (x) F_{(gen, v)}) omega] = (1 - gamma) tr omega = 1 - gamma .
The generation branch's mass is therefore STATE INDEPENDENT, which is
Eq. eq:choicemass visible in the instance, and it is 4/5 here.

WHAT IS AND IS NOT STATE INDEPENDENT, which is the whole content. The sum over
the generation branch is state independent; the individual letters are not. At
BBM92-IDEAL, with the acceptance map of this file,
  P_gen (sifted: matching bases, one click each side) = 1/5 at the honest
      point, and it MOVES with the state -- an adversary who suppresses clicks
      moves it ;
  P_gdisc (the unsifted generation letter) = 4/5 - P_gen = 3/5 at the honest
      point, and it moves oppositely ;
  P_gen + P_gdisc = 4/5 AT EVERY FEASIBLE POINT .
A test that pinned P_gen as state independent would be pinning the honest
model, not the declaration.

THE FOIL, and it is the reason A-TSM exists. An implementation that computed a
distribution over the generation rounds and then multiplied by (1 - gamma) at
the end would satisfy the identity above by construction while violating
A-TSM: the coin would no longer be inside the elements, the statistics would be
per SIFTED round rather than per channel use, and every per-channel-use figure
in this registry -- B-1's 1/5 among them -- would be wrong by the factor
1 - gamma. The discriminating observable is therefore not the total mass but
B-1's number beside it: 1/5 and not 1/4.

WHY IT IS FROZEN FOR BBM92 AND NOT ONLY FOR BB84. In BBM92 the coin is held by
ALICE, who has no source, and the plan's section 4.2 gives it to her
explicitly. Nothing in def:weighted cares which party holds a public choice --
the weights multiply the elements either way -- and that is exactly what this
entry records: the coin is not a property of the source side, and a d_A = 1
declaration carries it unchanged.""",
    hypotheses=(
        "The coin is a PUBLIC CHOICE in the sense of def:weighted, announced, "
        "with weights (1 - gamma, gamma) inside the POVM elements (A-TSM). "
        "Not a post-hoc fraction and not a fixed test-round count.",
        "tr omega = 1, which the untrusted feasible set imposes explicitly "
        "(def:feasible: normalisation is the only unconditional constraint "
        "there).",
        "The acceptance map may split the generation branch into as many "
        "letters as it likes; the identity is about their SUM.",
        "gamma = 1/5 is the instance's choice; the identity holds at every "
        "gamma in (0, 1).",
    ),
    observable=(
        "The declared acceptance vector at several feasible states: the sum of "
        "the generation-branch letters equals 1 - gamma = 4/5 at every one, "
        "exactly; and the individual sifted letter differs between them. "
        "Together with B-1's 1/5, which is what separates the coin-inside "
        "convention from a post-hoc fraction."
    ),
    value=F(4, 5),
    value_closed_form="sum over the generation branch = 1 - gamma = 4/5",
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (protocol-compiler 0.2.0, meat-core
1.1.0). THE STATE-INDEPENDENT MASS 4/5 STANDS.

THE TRANSCRIPT IS NOT A CLAIM OF ITS OWN. There is no
`protocol-compiler/def:transcript`: the transcript protocol is (DX5) of BOTH
modules' def:declaration -- an ordered list of messages, each a function of its
sender's readout and of the earlier messages of the same round and of nothing
else -- with protocol-compiler/ex:transcript as the worked three-message case.
All three are pinned now. (DX5) also states what this entry's foil is about:
"no measurement of a round depends on a message of that round, the measurements
being the fixed families of (DX3) and (DX4)", so the coin cannot be a
post-measurement renormalisation even in principle; the weights are inside the
families or the declaration is a different one.
def:weighted AND lem:weighted ARE UNCHANGED by the accepted claims, and the identity frozen here
is theirs. What the accepted claims add is only that the announcement side around it is now a
transcript rather than a pair of maps, which moves no mass: the generation
branch is selected by the coin's weight and not by any message.""",
)


O_BBM92_B6_PARTY_LOCAL_GAIN = Bbm92OracleEntry(
    oracle_id="O-BBM92-B6-PARTY-LOCAL-GAIN",
    claims=(
        "reductions/lem:party-local",
        "reductions/thm:licence",
        "reductions/def:licensed",
        "reductions/def:attset",
        "meat-core/def:feasible",
        "meat-core/def:homog",
        "meat-core/rem:homog",
        "meat-core/thm:reduction",
        "meat-core/def:declaration",
        "meat-core/def:roundmodel",
        "meat-core/lem:range",
        "reductions/lem:precomposition",
    ),
    kind="relation",
    subject=(
        "B-6: with party-local entries h_low is at least its value with the "
        "scalar entries, at every point, because the party-local feasible set "
        "is contained in the scalar one. The inclusion is STRICT, with the "
        "exact witness of lem:party-local (iv). The SIZE of the gain is a "
        "record and never an oracle."
    ),
    instance="BBM92-SYMMETRIC-ERROR",
    derivation="""\
THE INCLUSION, in one line. A party-local entry is
  tr_{Q_f}[(1 (x) (O_hat - c 1)) omega] >= 0   as an operator on the other
      party's factor
(lem:party-local (ii)). Pairing it with X = 1 on that factor -- the identity is
positive semidefinite -- gives
  tr[(1 (x) O_hat) omega] >= c tr omega ,
which is the SCALAR entry (lem:party-local (iii): "the scalar entry is its
trace"). So every omega satisfying the party-local entry satisfies the scalar
one:
  Feas(party-local) SUBSET OF Feas(scalar) ,
and an infimum over a smaller set is no smaller:
  h_low(party-local) >= h_low(scalar) ,
at every point of any sweep, at every alpha and at every acceptance vector.
THE DIRECTION IS THE ONE TO GET RIGHT: a tighter constraint set gives a LARGER
lower bound on the entropy, which is a better key rate.

THE INCLUSION IS STRICT, WITH AN EXACT WITNESS, so the relation is not vacuous.
:data:`PARTY_LOCAL_SEPARATION` transcribes lem:party-local (iv): a state
omega = (|00><00| + |11><11|)/2 and an observable O_hat = |0><0| with c = 1/2
for which the scalar entry holds with EQUALITY while
tr_{Q_f}[(1 (x) D) omega] = (1/4)|0><0| - (1/4)|1><1| has eigenvalues +-1/4 and
is not positive semidefinite. Four multiplications, all exact.

WHY THIS IS WORTH A LICENCE ROW AND NOT ONLY A REMARK -- the physics
derivations/05 section 5.4 records. With scalar entries only, a flag-state
entry of Bob's squasher bounds the TOTAL weight of his flag sector by the TOTAL
multi-click rate, and nothing stops the optimiser from putting the multi-clicks
where Alice's station sees vacuum and the flag weight where it clicks; the
bound on the SIFTED flag fraction is then weaker by roughly the inverse of
Alice's detection probability. The party-local entry bounds the flag weight
CONDITIONALLY ON ALICE'S SECTOR, which is what the physics supports: Bob's
premise Lambda_B^dagger(O_hat) >= c 1 is a property of his squasher alone and
holds for every input jointly with anything else.

WHAT IS NOT CLAIMED, AND THE PLAN IS EXPLICIT ABOUT IT. The SIZE of the gain at
any loss value is a Stage 4 RECORD and is the evidence for or against widening
gate (G3)(a); it is not an oracle and no number for it appears here. A measured
number under loss is a record, never an oracle (05-validation.md section 5).
Nor is it claimed that the party-local entry is NEEDED: BBM92 is sound with
scalar entries alone (derivations/05 section 5.4, "it is not needed for BBM92
to be sound").

THE ONE HYPOTHESIS THAT CANNOT BE DROPPED. The attack must factor through the
party's squasher with the other party's factor UNTOUCHED, and the squashing
channel must be a PRODUCT. lem:party-local (iv) is a channel that correlates
the parts, satisfies the scalar bound and violates the operator one -- so a
party-local entry emitted for a factor the squasher does not leave untouched
would be unsound, which is the plan's section 2.8 item 10. The witness above is
that same example read as a separation; it does double duty deliberately, and
the entry records both readings.""",
    hypotheses=(
        "The same O_hat and c in both programs; only the entry's FORM differs. "
        "Comparing a party-local entry against a scalar entry with a different "
        "constant compares nothing.",
        "The squashing channel is a PRODUCT over the two stations' factors and "
        "the attack leaves the other station's factor untouched "
        "(lem:party-local (i)); otherwise the party-local entry is not "
        "licensed at all.",
        "tr omega = 1, used when pairing with X = 1 to recover the scalar "
        "entry with the right-hand side c.",
        "The relation holds at every alpha, every acceptance vector and every "
        "point of a loss sweep. The SIZE of the gain is a record and is not "
        "frozen anywhere.",
    ),
    observable=(
        "h_low computed with the party-local entry set and with the scalar "
        "entry set on the same instance, same alpha, same acceptance vector: "
        "party-local >= scalar at every point, with both gaps beside the "
        "numbers. And the exact witness of PARTY_LOCAL_SEPARATION reproduced "
        "by whatever code decides entry admission: scalar admitted, "
        "party-local refused."
    ),
    relation=(
        "h_low(party-local entries) >= h_low(scalar entries) at every alpha, "
        "acceptance vector and loss point, with the same O_hat and c, because "
        "pairing the operator inequality with X = 1 gives the scalar one."
    ),
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS. THE RELATION AND
THE SEPARATION WITNESS STAND, and the relation's direction is now the accepted
text's own sentence.

THE TWO IDS I GUESSED DO NOT EXIST AND DID NOT NEED TO. There is no
`reductions/def:licensed-party-local` and no `meat-core/def:homog-party-local`:
the party-local form is a PARAGRAPH INSIDE the accepted def:licensed and inside
meat-core/def:homog, both of which this entry pinned from the start, with
def:attset's eq:attsetpl, thm:licence (v) and lem:party-local beside them --
also pinned from the start. So the re-pin adds no authority to this entry and
removes none; what it adds is the consumer's side, which did not exist in C2a:
def:declaration (DX6) types a `party_local` entry with its scope, def:roundmodel
now carries the party-local admissibility set beside the two it carried, and
lem:range (i) transports it to the state level in either mode. All three are
pinned now, and until then a party-local entry HAD NO CONSUMER (def:attset's own
note), which is why this entry could not name one when it was frozen.
THE DIRECTION IS THE CLAIM'S. def:homog's party-local paragraph: "A
`party_local` entry shrinks the feasible set further than its untagged reading
does" and, with more than one measured factor, it "implies, in either mode, the
untagged reading of the same entry, which is obtained from it by the partial
trace over the other measured factors (and over A in untrusted-source mode), and
it is in general not implied by it". That is this entry's inclusion and this
entry's pairing with X = 1, in the accepted words; def:attset records the same
containment at the channel level ("X = 1 gives the scalar condition").
THE WITNESS IS STILL THE LEMMA'S OWN EXAMPLE (iv) and still exact.
ONE FACT OF THE ACCEPTED CLAIMS I CHECKED BECAUSE IT COULD HAVE BITTEN. meat-core/thm:removal is
stated for a list carrying NO entry tagged `party_local`, so with the tagged
entry set no sector is removable at all -- and with BBM92's two measured factors
none would be anyway. NO ENTRY OF THIS FILE ASSERTS REMOVABILITY, so nothing is
contradicted; what the restriction forbids is reading the party-local gain as
licence to delete a flag sector, which this entry never claimed and which
def:dropped's own "what is not changed" paragraph forbids independently.
WHAT IS STILL NOT CLAIMED, and the accepted claims are explicit about it: def:homog records that
rem:homog's canonicity argument is NOT extended to the third form by that batch,
and that the third form's soundness rests on the supplier's certificate on the
scoped factor's channel. The SIZE of the gain remains a record and is frozen
nowhere.""",
)


BBM92_ORACLES: tuple[Bbm92OracleEntry, ...] = (
    O_BBM92_B1_IDEAL_ONE_BIT,
    O_BBM92_B2_SYMMETRIC_ERROR,
    O_BBM92_B3_UNTRUSTED_IS_LARGER,
    O_BBM92_B4_STATION_EXCHANGE,
    O_BBM92_B5_COIN_MASS,
    O_BBM92_B6_PARTY_LOCAL_GAIN,
)


def bbm92_oracle(oracle_id: str) -> Bbm92OracleEntry:
    """Return the entry with this id, refusing an unknown one.

    Refusing is the point: a silent ``None`` would let a test assert nothing
    while looking like it asserted something.
    """
    for entry in BBM92_ORACLES:
        if entry.oracle_id == oracle_id:
            return entry
    raise KeyError(f"no BBM92 oracle entry with id {oracle_id!r}")
