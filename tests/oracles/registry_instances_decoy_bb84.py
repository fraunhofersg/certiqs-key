"""The frozen oracle registry of the ``instances/decoy_bb84`` instance.

WHAT THIS FILE IS. The hand-derived expected values of the
decoy targets -- D-1 to D-5 of
``reports/2026-09-21-generalized-reductions-plan/05-validation.md`` section 5.3
and OT1 to OT5 of that plan's ``derivations/06-decoy-declaration.md`` section
6.3 -- each with the derivation that produced it, the fixed instance it is
stated on, and the hypotheses under which it holds. It is a registry in the
sense of ``registry.py``: a frozen expected value together with the derivation
that produced it, in enough detail to redo on paper.

WHY IT EXISTS BEFORE THE CODE. ``PRINCIPLES.md`` section 2.3: the oracle
registries "are the executable memory of every derivation; they move with their
module and are never regenerated from the code they test". This file was
authored and committed by an ORACLE AUTHOR, who is not the
implementer, BEFORE any of ``src/certiqs_key/`` supporting an Alice-side sector
map, a tagged decoy source or a dropped sector existed, and before the claims
that carry that mathematics were drafted. The implementer may
read it and may not modify it. **An expected value that turns out to be wrong
is a finding**, reported with its derivation and corrected deliberately --
never edited in passing to make a test go green.

ADMISSIBILITY (the rule of ``registry.py``, unchanged). No MATLAB,
OpenQKDSecurity, CVX, MOSEK or Julia value is admissible and none is used. No
number below came from running any code under ``src/``: every one is an exact
closed form, an elementary evaluation of one, or a hand-computed rational. The
closed forms are written out in the derivations AND exposed as the functions of
this module, which contain no import of ``certiqs_key``; the frozen tables are
evaluations of those functions on :data:`registry.ALPHA_GRID` and exist to
catch a transcription typo. THE DERIVATION, NOT THE TABLE, IS AUTHORITATIVE.

WHY EVERY INSTANCE HERE IS STATED IN THE TERMS OF THE WEIGHTED ENSEMBLE. A
decoy source is declared by its WEIGHTED ENSEMBLE and by nothing else
(``transmitter/decoy/cor:emitted-decoy``, "Declare weighted blocks"): the declared data are the alphabet with its weights ``p_x``, the
sector structure, and the blocks

    sigma^{v,(t)}_x = p_x * p~(n|mu) * |n,a><n,a|      (a quantum sector)
    sigma^{v,(t)}_x = p_x * w~_mu                     (a tail flag)

as block lists (``eq:decoy-blocks``). The retained system, Alice's POVM, the
marginal ``tau_A`` and the certificate are then NOT declared but DEFINED from
those blocks (``transmitter/lem:ensemble-presentation``): ``tau^{(t)}_A`` is the
TRANSPOSE of the declared sum ``sum_x sigma^{v,(t)}_x``, every certificate
block is pure, and the operators through which a consumer reads Alice's side
are ``N^{(t)}_x = (sigma^{v,(t)}_x)^T`` -- entrywise the declared numbers. NO
SQUARE ROOT IS FORMED ANYWHERE, and nothing is compressed, snapped or rounded
by the emission: the round-1 shield certificate with its support compression is
withdrawn. Every instance below therefore names its blocks and never a POVM
element, and every derivation that needs Alice's side uses ``N^{(t)}_x``.

Two consequences used throughout. (a) Declared weights are ROUNDED DOWN from
Poisson and the shortfall goes into the tail
(``transmitter/decoy/prop:tagging``; ``cor:emitted-decoy`` (v) "rounding a
weight down is a theorem"), so the dyadic weights of the instances below are
legitimate declarations and not approximations -- which is why exact rational
arithmetic is available at all. (b) Every formed entry must be a binary64
number or the declaration is refused (``cor:emitted-decoy`` (iv)); all weights
below are dyadic, so no entry is refused.

THE TWO NORMALISATION CONVENTIONS, NAMED ONCE HERE BECAUSE THE PLAN'S PHRASE
"PER SIFTED GENERATION ROUND" IS AMBIGUOUS AND THE AMBIGUITY MOVES NUMBERS.
The acceptance map ``phi`` decides what the ``gen`` letter's mass is, and the
objective (``meat-core/def:feasible``, Eq. ``eq:objective``) reads that mass:

  CONVENTION A (used by every entry below unless it says otherwise). A
  generation round that is SIFTED -- a click in the announced basis -- carries
  the letter ``gen``; a generation round that is not sifted carries its own
  letter. This is the resolved acceptance map of the plan's section 4.1
  ("multi-clicks ... are their own letter in the acceptance alphabet") and it
  is the convention under which ``P_gen`` IS the sifted generation
  probability, so that "one bit per sifted generation round" is the statement
  ``O_alpha = P_gen`` and is exact at every ``alpha``.

  CONVENTION B. ``phi(kappa) = gen`` on every class with ``z = gen``, pass and
  fail alike, so ``P_gen = 1 - gamma`` is state independent
  (``derivations/06`` section 6.1, "Acceptance alphabet"). Under B the failing
  branch enters ``K`` LINEARLY -- ``Theta`` is untouched by the pinching
  (``meat-core/thm:branch-formula``, ``(Theta^{1/alpha})^alpha = Theta``) -- and the key
  term is NO LONGER the sifted probability: it is strictly smaller for every
  ``alpha > 1`` and agrees only in the limit ``alpha -> 1+``.

``O-DECOY-D2-VACUUM-BIT`` freezes both numbers on one instance, so that no
implementation can satisfy a per-round claim by reinterpreting the
normalisation.

WHAT THIS REGISTRY DOES NOT DO. It computes no key rate, runs no solver, and
pins no ``h_low``: every number here is either a closed form of the objective
AT A NAMED POINT -- which bounds ``h_low`` from ABOVE and never from below --
or a state-independent identity of one sector's deficit, or a RELATION between
two programs. The inequality and monotonicity targets (D-3, D-4) are frozen as
relations with their hypotheses and never as numbers, because a number would
pin a solver run; where a relation has a hand-computable WITNESS the witness is
frozen beside it.

THE CLAIMS PINNED, AND THE RE-PIN. When this file was written the
meat-core mathematics these entries consume -- the Alice-side sector licence,
the rank-one sector lemma (``derivations/06`` Lemma 6.1), the dropped sector,
the consumer's ensemble form -- was not yet written as claims, so each entry
pinned what existed and listed the rest in ``repin_after_c3`` under the plan's
proposed ids, which are suggestions and nothing more.

**The claims are accepted (reductions 0.2.0; protocol-compiler 0.2.0
and meat-core 1.1.0), and the re-pin is done, deliberately.**
Every id was looked up rather than guessed, and three of the plan's names moved:
there is no ``def:ensemble-form`` (the form is ``meat-core/def:declaration``
(DX4), made a definition by ``meat-core/lem:ensemble-form``), the transcript is
``def:declaration`` (DX5) with ``protocol-compiler/ex:transcript``, and the
key-inert reading on a joint sector has its own definition,
``meat-core/def:joint-sectors``. The ids that landed as the plan proposed them
are ``meat-core/lem:rank-one-sector``, ``prop:a-neutral``, ``def:dropped``,
``prop:drop-bound``, ``cor:drop-program``, ``reductions/lem:precomposition`` and
``lem:source-transfer``. ``repin_after_c3`` is empty on every entry and the
integrity test keeps the ratchet.

**NO FROZEN NUMBER MOVED, and every entry carries a ``revalidation`` recording
what the accepted claim says of it.** The derivations themselves are untouched:
an oracle is never edited to agree with a later structure, and a contradiction
would be a finding. Two things the re-read found worth naming. (a) The
accepted ``lem:rank-one-sector`` (iv) carries, in its own round-2 pass, the
qualifier that the one bit is one bit PER UNIT OF PASS WEIGHT -- which is
exactly the convention split ``O-DECOY-D2-VACUUM-BIT`` froze as a finding, and
the two agree. (b) ``lem:rank-one-sector`` does NOT cover OT4: its hypothesis is
a rank-one Alice marginal and the one-photon sector's is rank two, so that entry
pins the joint-sector definition and keeps its own derivation, and says so.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from fractions import Fraction as F

from registry import ALPHA_GRID, ASSURANCE, INADMISSIBLE_SOURCES, KINDS

__all__ = [
    "ACCEPTANCE_CONVENTIONS",
    "ALPHA_GRID",
    "ASSURANCE",
    "DECOY_IDEAL_TWO_SECTOR",
    "DECOY_INSTANCES",
    "DECOY_KINDS",
    "DECOY_ORACLES",
    "DECOY_TOY",
    "DECOY_VACUUM",
    "INADMISSIBLE_SOURCES",
    "KINDS",
    "OT3_FOIL_MARGINAL",
    "OT3_FOIL_STATE",
    "OT3_WITNESS_MARGINAL",
    "OT3_WITNESS_STATE",
    "DecoyInstance",
    "DecoyOracleEntry",
    "Matrix",
    "bell_diagonal_bits",
    "bell_diagonal_sum",
    "binary_entropy",
    "d1_objective_with_tail",
    "d2_objective_convention_b",
    "decoy_instance",
    "decoy_oracle",
    "dropped_objective",
    "flagged_single_photon_objective",
    "pinched_weight_sum",
    "sector_deficit_factor",
    "sifted",
]


#: A FIFTH kind beside the four of ``registry.KINDS``. MOTIVATION, as every
#: addition to a shared vocabulary owes one: D-3, D-4 and the BBM92 targets
#: B-3 and B-6 are INEQUALITIES between two programs, not values. Recording one
#: as a ``toy-instance`` with a number would freeze a solver run, which
#: PRINCIPLES.md section 2.3 forbids an oracle to be; recording it as a
#: ``structural-identity`` would claim an equality that is not asserted. A
#: ``relation`` entry MUST carry a ``relation`` string and no other kind may;
#: a number beside it is a BOUND or a RECORDED coincidence and says which in
#: ``value_closed_form``. The integrity test holds every entry to that.
DECOY_KINDS: frozenset[str] = KINDS | frozenset({"relation"})

#: The two acceptance-map conventions of the module docstring, as data, so that
#: an entry names one rather than describing it again.
ACCEPTANCE_CONVENTIONS: tuple[tuple[str, str], ...] = (
    (
        "A",
        "phi sends a SIFTED generation round to `gen` and an unsifted one to a "
        "letter of its own (plan section 4.1). P_gen is then the sifted "
        "generation probability.",
    ),
    (
        "B",
        "phi sends every generation round to `gen`, pass and fail alike, so "
        "P_gen = 1 - gamma is state independent (derivations/06 section 6.1).",
    ),
)


# ===========================================================================
#  The closed forms, written from the derivations and from nothing else
# ===========================================================================
#
#  None of these functions imports or calls anything under ``src/``. Each is
#  the formula its docstring names, transcribed from the derivation of the
#  entry that cites it, and each frozen table below is its evaluation on
#  ALPHA_GRID.


def binary_entropy(x: float) -> float:
    """Return ``h2(x) = -x log2 x - (1-x) log2(1-x)``, in bits."""
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


def pinched_weight_sum(weights: tuple[float, ...], alpha: float) -> float:
    """Return ``sum_z pi(z)^alpha`` for the key distribution ``pi``.

    This is the whole alpha dependence of a RANK-ONE Alice sector's deficit.
    ``derivations/06`` Lemma 6.1 writes that deficit with the factor
    ``1 - 2^{(1-alpha) H_alpha(pi)}`` and
    ``H_alpha(pi) = (1/(1-alpha)) log2 sum_z pi(z)^alpha``; substituting the
    second into the first gives ``2^{(1-alpha)H_alpha} = sum_z pi(z)^alpha``
    exactly, so no logarithm and no exponential is needed at all. For the
    uniform binary ``pi`` the sum is ``2^{1-alpha}``.
    """
    return math.fsum(w**alpha for w in weights if w > 0.0)


def sector_deficit_factor(alpha: float, weights: tuple[float, ...]) -> float:
    """Return ``1 - sum_z pi(z)^alpha``, the rank-one sector's deficit factor.

    The deficit of a rank-one Alice sector under direct reconciliation is
    ``f = -(1 - sum_z pi(z)^alpha) * tr G`` (``derivations/06`` Lemma 6.1).
    """
    return 1.0 - pinched_weight_sum(weights, alpha)


def bell_diagonal_sum(
    lambdas: tuple[float, float, float, float], alpha: float
) -> float:
    """Return ``S = sum_i (lambda_{i0}^{1/alpha} + lambda_{i1}^{1/alpha})^alpha``.

    ``lambdas`` is ``(lambda_00, lambda_01, lambda_10, lambda_11)`` with the
    FIRST index the bit-error index ``i`` and the second the phase index ``j``,
    which in the Bell basis ordered ``(Phi+, Phi-, Psi+, Psi-)`` is that same
    order (``derivations/06`` target OT4).
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
    """Return ``h = 1 - log2 S / (alpha - 1)``: the sector's bits per round.

    Target OT4. The identity that makes this the sector's ``h`` in the sense of
    ``meat-core/thm:branch-formula`` is ``T / tr G = 2^{1-alpha} S = 2^{(1-alpha) h}``.
    """
    return 1.0 - math.log2(bell_diagonal_sum(lambdas, alpha)) / (alpha - 1.0)


def _key_term(p_gen: float, kernel: float, alpha: float) -> float:
    """Return ``(P_gen/(alpha-1)) log2(P_gen/K_gen)``, Eq. ``eq:objective``.

    At ``q = Phi[omega]`` every divergence term of Eq. ``eq:objective``
    vanishes and this single key term is the whole objective; it equals
    ``P_gen`` times the conditional entropy of ``meat-core/thm:branch-formula``
    Eq. ``eq:c5``.
    """
    return (p_gen / (alpha - 1.0)) * math.log2(p_gen / kernel)


def sifted(instance: DecoyInstance, sector: str) -> float:
    """Return ``g_t``, the probability of "generation, sifted, sector t"."""
    for name, weight in instance.sifted_generation:
        if name == sector:
            return float(weight)
    raise KeyError(f"{instance.instance_id} has no sector {sector!r}")


def dropped_objective(alpha: float) -> float:
    """Return ``O^D_alpha`` at the honest point of :data:`DECOY_TOY`. OT5.

    ``K^D_gen = P_gen - (1 - 2^{1-alpha}) g_0 - (1 - 2^{(1-alpha)h_1}) g_1``
    with ``g_n`` the probability of "generation, sifted, sector n", ``h_1`` the
    one-photon bits of :func:`bell_diagonal_bits`, and every tail-flag pair
    dropped -- which is an IDENTITY here, not a loss, because those pairs are
    key inert (OT2).
    """
    g_0 = sifted(DECOY_TOY, "vacuum")
    g_1 = sifted(DECOY_TOY, "one-photon")
    p_gen = float(DECOY_TOY.sifted_generation_total)
    deficit_0 = sector_deficit_factor(alpha, (0.5, 0.5)) * g_0
    bits = bell_diagonal_bits(DECOY_TOY.one_photon_lambdas, alpha)
    deficit_1 = (1.0 - 2.0 ** ((1.0 - alpha) * bits)) * g_1
    return _key_term(p_gen, p_gen - deficit_0 - deficit_1, alpha)


def flagged_single_photon_objective(alpha: float) -> float:
    """Return the same objective on :data:`DECOY_TOY` at ``N_ent = 0``. D-3.

    Lowering ``N_ent`` to zero turns the one-photon sector into the four
    polarisation flags ``f_{1,a}``, whose deficit is identically zero (OT2), so
    only the vacuum term survives.
    """
    g_0 = sifted(DECOY_TOY, "vacuum")
    p_gen = float(DECOY_TOY.sifted_generation_total)
    deficit = sector_deficit_factor(alpha, (0.5, 0.5)) * g_0
    return _key_term(p_gen, p_gen - deficit, alpha)


def d1_objective_with_tail(alpha: float) -> float:
    """Return the ``gen`` objective of :data:`DECOY_IDEAL_TWO_SECTOR`, noiseless.

    D-1. ``P_gen = g_1 + g_tail`` and
    ``K_gen = P_gen - (1 - 2^{1-alpha}) g_1``, the tail contributing mass to
    ``P_gen`` and NO deficit. The tail-free value would be ``g_1`` at every
    ``alpha``.
    """
    g_1 = sifted(DECOY_IDEAL_TWO_SECTOR, "one-photon")
    p_gen = float(DECOY_IDEAL_TWO_SECTOR.sifted_generation_total)
    deficit = sector_deficit_factor(alpha, (0.5, 0.5)) * g_1
    return _key_term(p_gen, p_gen - deficit, alpha)


def d2_objective_convention_b(alpha: float) -> float:
    """Return D-2's value under CONVENTION B on :data:`DECOY_VACUUM`.

    ``P_gen = 1 - gamma`` state independent, ``g_0 = (1-gamma) Y_0``, and
    ``K_gen = P_gen - (1 - 2^{1-alpha}) g_0``.
    """
    p_gen = float(1 - DECOY_VACUUM.test_coin)
    g_0 = sifted(DECOY_VACUUM, "vacuum")
    deficit = sector_deficit_factor(alpha, (0.5, 0.5)) * g_0
    return _key_term(p_gen, p_gen - deficit, alpha)


def _freeze(form: Callable[[float], float]) -> tuple[tuple[float, float], ...]:
    """Evaluate ``form`` on :data:`registry.ALPHA_GRID`, as ``registry`` does."""
    return tuple((a, form(a)) for a in ALPHA_GRID)


# ===========================================================================
#  The fixed instances. THE PLAN'S TARGETS ARE UNDERDETERMINED AND THESE
#  CHOICES ARE MINE.
# ===========================================================================
#
#  Section 5.3 names its targets on "decoy BB84" without fixing an intensity, a
#  cutoff, a receiver or an acceptance map, and rule (3) of the oracle author's
#  brief says to fix the instance and say so. Each instance below is therefore
#  MY choice, recorded with what it is not: none of them is
#  ``instances/decoy_bb84``, whose receiver is the four-detector passive one of
#  ``instances/optical_bb84`` with its efficiencies, dark counts and exact
#  window. What is common to all three:
#
#  * the source is a weak-coherent-pulse model with full phase randomisation
#    (``transmitter/decoy/def:wcp-model``, A-WCP), declared as a tagged source
#    (``def:tagged-source``) and emitted as the weighted ensemble of
#    ``cor:emitted-decoy``;
#  * the key holder is ALICE and reconciliation is DIRECT: ``h = A`` and
#    ``r(x, v) = bit(a)``, the key value being a function of Alice's label
#    alone. Every entry below is FALSE under reverse reconciliation, and each
#    says so where it matters (OT1, OT2);
#  * Bob announces the ``Z`` basis on every generation round, so no basis-match
#    factor enters the generation mass. This is a simplification of the plan's
#    instance, where Bob's basis is a public choice with its own weight;
#  * the receiver is a THRESHOLD PAIR in the announced basis with efficiency
#    ``eta`` and dark-count probability ``p_dc`` per round, so a round either
#    clicks or does not and there is no multi-click letter. Sector yields are
#    ``Y_n = 1 - (1 - p_dc)(1 - eta)^n``. This is NOT the plan's four-detector
#    passive receiver, and it is the one place these instances are cruder than
#    the instance they anticipate: the numbers are the mathematics' and not the
#    apparatus's;
#  * the acceptance convention is A unless the entry says otherwise.


@dataclass(frozen=True)
class DecoyInstance:
    """One fixed decoy instance: the data every entry on it reads."""

    instance_id: str
    #: The one signal intensity, as an exact rational where it is one.
    intensity: F
    n_ent: int
    n_src: int
    #: ``p~(n|mu)`` for ``n <= N_src``, keyed by sector name. Dyadic, and
    #: STRICTLY below the Poisson weight, which is what makes the declaration a
    #: rounded-down one (``cor:emitted-decoy`` (v)).
    declared_weights: tuple[tuple[str, F], ...]
    #: ``w~_mu``, the tail weight that absorbs the shortfall.
    tail_weight: F
    #: The test coin's bias ``gamma``; the generation-branch mass is
    #: ``1 - gamma`` (``protocol-compiler/def:weighted``).
    test_coin: F
    #: The receiver's efficiency and per-round dark-count probability.
    efficiency: F
    dark_count: F
    #: ``Y_n`` per sector, exact where the sector is below the cutoff. The tail
    #: flag's yield is NOT free: see ``tail_yield_closed_form``.
    sector_yields: tuple[tuple[str, F], ...]
    tail_yield_closed_form: str
    #: The probability of "generation, sifted, sector t", by sector name.
    #: Exact rationals for the sectors below the cutoff; the tail's is a closed
    #: form in one exponential and is carried as its evaluation.
    sifted_generation: tuple[tuple[str, F | float], ...]
    sifted_generation_total: F | float
    total_generation_mass_closed_form: str
    #: The honest one-photon block's Bell weights, in the OT4 index order.
    one_photon_lambdas: tuple[float, float, float, float]
    one_photon_lambdas_exact: tuple[F, F, F, F]
    #: The honest single-photon bit and phase error rates.
    error_rate: F
    acceptance_convention: str
    notes: str


DECOY_TOY = DecoyInstance(
    instance_id="DECOY-TOY",
    intensity=F(1, 2),
    n_ent=1,
    n_src=1,
    declared_weights=(("vacuum", F(1, 2)), ("one-photon", F(1, 4))),
    tail_weight=F(1, 4),
    test_coin=F(1, 2),
    efficiency=F(1, 4),
    dark_count=F(1, 64),
    sector_yields=(("vacuum", F(1, 64)), ("one-photon", F(67, 256))),
    tail_yield_closed_form="Y_tail = 949/256 - (63/16) e^{-1/8} = 0.2321996960731556",
    sifted_generation=(
        ("vacuum", F(1, 256)),
        ("one-photon", F(67, 2048)),
        ("tail", 0.02902496200914445),
    ),
    sifted_generation_total=0.06564605575914445,
    total_generation_mass_closed_form=(
        "P_gen = (1-gamma)[1 - (1-p_dc) e^{-eta mu}] = 1/2 - (63/128) e^{-1/8}"
    ),
    one_photon_lambdas=(13 / 16, 1 / 16, 1 / 16, 1 / 16),
    one_photon_lambdas_exact=(F(13, 16), F(1, 16), F(1, 16), F(1, 16)),
    error_rate=F(1, 8),
    acceptance_convention="A",
    notes="""\
THE INSTANCE OT4, OT5, D-3, D-4 AND D-5 ARE STATED ON, fixed here and chosen so
that every declared number is dyadic and every honest number is a closed form
in one exponential.

THE SOURCE. One intensity mu = 1/2, four polarisations, N_ent = N_src = 1 --
so there is no polarisation-flag summand at all and the sector list is
{vacuum, one-photon} together with the tail flags f_{a,mu}. Declared weights
p~(0|mu) = 1/2 and p~(1|mu) = 1/4, tail w~ = 1 - 1/2 - 1/4 = 1/4.

BOTH WEIGHT INEQUALITIES ARE STRICT, AND BOTH REDUCE TO e < 4, which a reader
can check without a table. eq:weightineq asks p~(n|mu) <= p_mu(n):
  p_mu(0) = e^{-1/2} > 1/2   <=>   e^{1/2} < 2   <=>   e < 4 ;
  p_mu(1) = (1/2) e^{-1/2} > 1/4   <=>   e^{-1/2} > 1/2, THE SAME INEQUALITY.
So the declaration is a genuinely ROUNDED-DOWN one (cor:emitted-decoy (v)),
with 0.1065... of vacuum weight and 0.0533... of one-photon weight pushed into
the tail. That is why dyadic weights are available and why the tail is heavy.

THE LABELS. gamma = 1/2. Generation labels (H, mu, gen) and (V, mu, gen) at
p_x = 1/4 each; test labels (a, mu, test) for a in {H, V, +, -} at p_x = 1/8
each. Sum 1/2 + 1/2 = 1.

THE DECLARED BLOCKS, which is all the declaration is. On the one-photon sector
sigma^{v,(1)}_x = p_x (1/4) |1,a_x><1,a_x| and on the vacuum sector
sigma^{v,(0)}_x = p_x (1/2) |vac><vac|; on the tail flag f_{a,mu} the number
p_x (1/4) for the letters with that polarisation. Hence
  tau^{(0)}_A = 1/2 (a number: the sector is one dimensional) ,
  tau^{(1)}_A = [(1/4 + 1/8)(|H><H| + |V><V|)
                 + (1/8)(|+><+| + |-><-|)]^T (1/4) = (1/8) 1_2 ,
using |H><H| + |V><V| = |+><+| + |-><-| = 1_2. The one-photon marginal is
therefore MAXIMALLY MIXED of weight 1/4, which is what puts the Bell-diagonal
family of OT4 inside the feasible set. Sector weights: g^A_0 = 1/2,
g^A_1 = 1/4, tail 1/4, summing to 1.

THE RECEIVER AND THE HONEST YIELDS. eta = 1/4, p_dc = 1/64, so
  Y_0 = 1 - (63/64) = 1/64 ,
  Y_1 = 1 - (63/64)(3/4) = 1 - 189/256 = 67/256 .
THE TAIL FLAG'S YIELD IS NOT A FREE NUMBER, and this is the one honest-model
trap of the instance. Xi_tag prepares from f_{a,mu} the NORMALISED REMAINDER
of the physical state -- the Poisson tail together with the shortfall rounded
out of the low sectors (prop:tagging) -- so
  Y_tail = [sum_n p_mu(n) Y_n - sum_{n<=1} p~(n|mu) Y_n] / w~ ,
and with sum_n p_mu(n) Y_n = 1 - (1-p_dc) e^{-eta mu} = 1 - (63/64) e^{-1/8}
(D-5) and sum_{n<=1} p~ Y_n = 1/128 + 67/1024 = 75/1024:
  Y_tail = 4[1 - (63/64) e^{-1/8} - 75/1024] = 949/256 - (63/16) e^{-1/8}
         = 0.2321996960731556 .
An implementation that gave the tail flag the two-photon yield, or a free one,
would satisfy no entry of this registry.

THE SIFTED GENERATION PROBABILITIES, g_t = (1 - gamma) p~_t Y_t:
  g_0 = (1/2)(1/2)(1/64)   = 1/256    = 0.00390625 ,
  g_1 = (1/2)(1/4)(67/256) = 67/2048  = 0.03271484375 ,
  g_tail = (1/8) Y_tail    = 949/2048 - (63/128) e^{-1/8} = 0.029024962009 ,
  P_gen = g_0 + g_1 + g_tail = 1/2 - (63/128) e^{-1/8} = 0.065646055759 ,
the last by the exact cancellation 8/2048 + 67/2048 + 949/2048 = 1024/2048,
which is the check that the three sector yields reproduce the physical click
probability: P_gen = (1 - gamma)[1 - (1 - p_dc) e^{-eta mu}].

THE HONEST ONE-PHOTON BLOCK. Conditioned on a one-photon detection in the
matched basis, the AQ state is Bell-diagonal with the depolarising weights
lambda = (13/16, 1/16, 1/16, 1/16) in the OT4 order, i.e. bit error
e_Z = lambda_10 + lambda_11 = 1/8 and phase error
e_X = lambda_01 + lambda_11 = 1/8.

WHAT THIS INSTANCE IS NOT. It is not instances/decoy_bb84: one intensity in
place of three, a threshold pair in place of the four-detector passive
receiver, no multi-click letter, and Bob's generation basis fixed. Its purpose
is to carry the per-sector mathematics exactly, and no number here is a
prediction about the real instance.""",
)


DECOY_IDEAL_TWO_SECTOR = DecoyInstance(
    instance_id="DECOY-IDEAL-TWO-SECTOR",
    intensity=F(1, 2),
    n_ent=1,
    n_src=1,
    declared_weights=(("vacuum", F(1, 2)), ("one-photon", F(1, 4))),
    tail_weight=F(1, 4),
    test_coin=F(1, 2),
    efficiency=F(1),
    dark_count=F(0),
    sector_yields=(("vacuum", F(0)), ("one-photon", F(1)), ("tail", F(1))),
    tail_yield_closed_form=(
        "Y_tail = 1 exactly: an ideal detector fires on every n >= 1"
    ),
    sifted_generation=(
        ("vacuum", F(0)),
        ("one-photon", F(1, 8)),
        ("tail", F(1, 8)),
    ),
    sifted_generation_total=F(1, 4),
    total_generation_mass_closed_form="P_gen = (1-gamma)(p~_1 + w~) = (1/2)(1/2) = 1/4",
    one_photon_lambdas=(1.0, 0.0, 0.0, 0.0),
    one_photon_lambdas_exact=(F(1), F(0), F(0), F(0)),
    error_rate=F(0),
    acceptance_convention="A",
    notes="""\
THE INSTANCE D-1 IS STATED ON: DECOY-TOY's source at an IDEAL receiver, eta = 1
and p_dc = 0, at the noiseless honest point lambda = (1, 0, 0, 0).

WHY THE IDEAL RECEIVER MATTERS TWICE. The vacuum sector never clicks, so
g_0 = 0 and the vacuum contributes NOTHING -- which is the plan's reason why
"the vacuum sector never clicks at an ideal receiver". And every n >= 1 round
clicks: with all photons of a phase-randomised pulse in one polarisation, a
threshold pair in the matched basis fires on the corresponding detector
whatever n is. So Y_1 = Y_tail = 1 and
  g_1 = (1 - gamma) p~_1 = (1/2)(1/4) = 1/8 ,
  g_tail = (1 - gamma) w~ = (1/2)(1/4) = 1/8 ,
  P_gen = 1/4 .
THE TAIL IS AS BIG AS THE SINGLE-PHOTON SECTOR HERE, on purpose: it is what
makes the plan's "scaled by the single-photon weight" checkable rather than
vacuous.

THE TAIL-FREE COMPARISON SOURCE, which is what D-1 as written asks for and
which is NOT a weak-coherent-pulse source: weights (3/4, 1/4) on n <= 1 and
w~ = 0. Its qubit targets are the frozen ones of tests/support/bb84_targets.py
with p^A_Z p^B_Z replaced by (1 - gamma) and scaled by w = p~_1 = 1/4.""",
)


DECOY_VACUUM = DecoyInstance(
    instance_id="DECOY-VACUUM",
    intensity=F(0),
    n_ent=1,
    n_src=1,
    declared_weights=(("vacuum", F(1)), ("one-photon", F(0))),
    tail_weight=F(0),
    test_coin=F(1, 2),
    efficiency=F(1, 4),
    dark_count=F(1, 64),
    sector_yields=(("vacuum", F(1, 64)),),
    tail_yield_closed_form="no tail flag: w~_0 = 1 - p~(0|0) = 0 at mu = 0",
    sifted_generation=(("vacuum", F(1, 128)),),
    sifted_generation_total=F(1, 128),
    total_generation_mass_closed_form="P_gen = (1-gamma) Y_0 = (1/2)(1/64) = 1/128",
    one_photon_lambdas=(0.0, 0.0, 0.0, 0.0),
    one_photon_lambdas_exact=(F(0), F(0), F(0), F(0)),
    error_rate=F(1, 2),
    acceptance_convention="A",
    notes="""\
THE INSTANCE D-2 AND OT1 ARE STATED ON: every intensity ZERO, at a receiver
with dark counts.

AT mu = 0 THE POISSON LAW IS THE POINT MASS AT ZERO, so p~(0|0) = 1 satisfies
eq:weightineq with equality at the only sector that exists, the tail weight is
w~_0 = 0, and the sector list is the single vacuum sector. THIS IS THE ONE
DECLARATION IN THIS FILE WITH NO TAIL FLAG, and it has none because there is
no Poisson tail to absorb, not because a weight was rounded.

EVERY LABEL EMITS THE SAME STATE, so tau^{(0)}_A = 1 is rank one -- one
dimensional, in fact -- and by OT3 every feasible block is
omega^{(0)} = tau^{(0)}_A (x) sigma_0 with sigma_0 a state on Q. The signal
carries NO information about the label: Eve's system is uncorrelated with
Alice's bit whatever she does, and the clicks she sees are the receiver's dark
counts.

THE RECEIVER. eta = 1/4 and p_dc = 1/64 as in DECOY-TOY, but only p_dc can
act: Y_0 = 1 - (1 - p_dc) = p_dc = 1/64, and the click's outcome is uniform
over the two detectors of the announced pair, the dark counts of the two being
independent and identically distributed. Hence, with gamma = 1/2,
  g_0 = (1 - gamma) Y_0 = 1/128 ,
and under convention A, P_gen = g_0 = 1/128.

ZERO TRANSMITTANCE IS A DIFFERENT TARGET AND IS NOT THIS ONE (the plan says so
in D-2's own reason): at eta = 0 Eve still RECEIVES the signal and may hold a
copy of the label; here she receives the vacuum, which carries nothing.""",
)


DECOY_INSTANCES: tuple[DecoyInstance, ...] = (
    DECOY_TOY,
    DECOY_IDEAL_TWO_SECTOR,
    DECOY_VACUUM,
)


def decoy_instance(instance_id: str) -> DecoyInstance:
    """Return the instance with this id, refusing an unknown one."""
    for instance in DECOY_INSTANCES:
        if instance.instance_id == instance_id:
            return instance
    raise KeyError(f"no decoy instance with id {instance_id!r}")


# ===========================================================================
#  OT3's witness and foil, as exact rational matrices
# ===========================================================================

Matrix = tuple[tuple[F, ...], ...]

#: A rank-one marginal on a qubit ``A`` and a positive ``omega`` on
#: ``A (x) Q`` having it -- necessarily a product: OT3's content on the
#: smallest space that shows it. The index order is ``A`` OUTER, so the block
#: rows are ``(a, q) = (0,0), (0,1), (1,0), (1,1)`` and a product on
#: ``|0><0|_A`` occupies the top-left 2x2 block alone.
OT3_WITNESS_MARGINAL: Matrix = ((F(1), F(0)), (F(0), F(0)))
OT3_WITNESS_STATE: Matrix = (
    (F(1, 2), F(1, 4), F(0), F(0)),
    (F(1, 4), F(1, 2), F(0), F(0)),
    (F(0), F(0), F(0), F(0)),
    (F(0), F(0), F(0), F(0)),
)

#: The FOIL: a rank-TWO marginal with a positive ``omega`` that is not a
#: product, in the same index order. One row of the pair is not evidence; the
#: pair is.
OT3_FOIL_MARGINAL: Matrix = ((F(1, 2), F(0)), (F(0), F(1, 2)))
OT3_FOIL_STATE: Matrix = (
    (F(1, 2), F(0), F(0), F(0)),
    (F(0), F(0), F(0), F(0)),
    (F(0), F(0), F(0), F(0)),
    (F(0), F(0), F(0), F(1, 2)),
)


# ===========================================================================
#  The entry record
# ===========================================================================


@dataclass(frozen=True)
class DecoyOracleEntry:
    """One frozen expected value, or one relation, with its derivation."""

    oracle_id: str
    #: Claim ids of ``spec/modules/**`` AT HEAD. Verified to resolve by the
    #: integrity test; never a label invented for the occasion.
    claims: tuple[str, ...]
    kind: str
    subject: str
    #: The ``instance_id`` this entry is stated on.
    instance: str
    derivation: str
    #: The hypotheses, stated so that the entry cannot be satisfied by
    #: reinterpretation. Every entry names its reconciliation direction, its
    #: acceptance convention and what a per-round figure normalises by.
    hypotheses: tuple[str, ...]
    #: What the implementer's test must compare, once the code exists. THIS
    #: FILE WRITES NO SUCH TEST: it needs the future code and is not the oracle
    #: author's to write.
    observable: str
    #: The alpha-independent frozen value, where there is one.
    value: F | float | None = None
    #: Its closed form in ASCII. Present whenever ``value`` is.
    value_closed_form: str = ""
    #: The closed form in alpha, where the value depends on the Renyi order.
    closed_form: Callable[[float], float] | None = None
    #: ``(alpha, value)`` frozen from ``closed_form`` on ALPHA_GRID.
    frozen_values: tuple[tuple[float, float], ...] = ()
    #: For ``kind = "relation"``: the relation, with no number.
    relation: str | None = None
    #: True where the plan says a statement is "recorded, not asserted".
    recorded_not_asserted: bool = False
    #: Claim ids expected to be added and that this entry should then
    #: pin. The integrity test fails if one has appeared and is not pinned.
    repin_after_c3: tuple[str, ...] = field(default_factory=tuple)
    #: What a later re-read of the accepted claims found. The DERIVATION above
    #: is frozen evidence and is never edited to agree with a later structure
    #: (the mechanism ``registry_transmitter.PCOracleEntry.revalidation`` uses);
    #: a re-read is recorded here, and a contradiction would be a FINDING and
    #: not an edit.
    revalidation: str = ""
    assurance: str = ASSURANCE


# ===========================================================================
#  Group D -- the five targets of 05-validation.md section 5.3
# ===========================================================================


O_DECOY_D1_QUBIT_LIMIT = DecoyOracleEntry(
    oracle_id="O-DECOY-D1-QUBIT-LIMIT",
    claims=(
        "transmitter/decoy/prop:tagging",
        "transmitter/decoy/cor:emitted-decoy",
        "transmitter/lem:ensemble-presentation",
        "meat-core/thm:branch-formula",
        "meat-core/def:feasible",
        "meat-core/def:branch",
        "meat-core/lem:rank-one-sector",
        "meat-core/prop:a-neutral",
        "reductions/lem:source-transfer",
    ),
    kind="toy-instance",
    subject=(
        "D-1: what a source with weight only on the low sectors reproduces of "
        "the qubit targets T1 to T4 of tests/support/bb84_targets.py. The "
        "scaling by the single-photon weight holds EXACTLY for a tail-free "
        "source and in the alpha -> 1+ limit for a weak-coherent-pulse one; at "
        "finite alpha with a tail it FAILS, and the exact tail-corrected closed "
        "form is frozen against it. T4 does not scale at all."
    ),
    instance="DECOY-IDEAL-TWO-SECTOR",
    derivation="""\
WHAT D-1 SAYS AND WHAT IS ACTUALLY TRUE. The plan: "A source with weight only
on n <= 1 and no tail reproduces the qubit targets T1 to T4 of
tests/support/bb84_targets.py, scaled by the single-photon weight". Two things
have to be separated, and the separation is the entry.

STEP 1 -- THE SCALING IS EXACT FOR A TAIL-FREE SOURCE, and the reason is
POSITIVE HOMOGENEITY OF THE DEFICIT. With weight only on n <= 1 and no tail,
the sector list is {vacuum, one-photon}; at an ideal receiver the vacuum never
clicks, so tr G_{gen,0} = 0 and f_{gen,0} = 0 (the deficit of Eq. eq:f-def is
zero on a zero operator). The one-photon block is w times the qubit
declaration's own omega, with w = p~(1|mu):
  G_{gen,1}(w omega) = w G_{gen,1}(omega)          (G is linear) ,
  T_{gen,1}(w omega) = w T_{gen,1}(omega)          (G^{1/alpha} scales by
      w^{1/alpha}, the pinching is linear, the alpha-th power restores w) ,
so f and hence K - P scale by w, and P_gen scales by w because the vacuum
contributes no generation mass under convention A. Eq. eq:objective's key term
  (P_gen/(alpha-1)) log2(P_gen / K_gen)
is therefore w times the qubit one AT EVERY alpha: the ratio K/P is unchanged
and the prefactor carries the w. Hence
  T1 (the alpha-independent honest-point value)  scales by w ;
  T2 (the alpha -> 1+ limit)                     scales by w ;
  T3 (the Devetak-Winter ceiling per channel use) scales by w ;
  T4 (Q*, the zero crossing of 1 - 2 h2(Q))      DOES NOT SCALE. It is the
      root of an equation whose left side w multiplies, and a positive factor
      cannot move a root. FREEZING T4 AS "SCALED" WOULD BE THE ERROR THIS
      ENTRY EXISTS TO CATCH.
On DECOY-IDEAL-TWO-SECTOR's comparison source (weights (3/4, 1/4), w~ = 0),
with the qubit p^A_Z p^B_Z replaced by 1 - gamma = 1/2 and w = 1/4:
  T1 = w (1 - gamma) = 1/8 = 0.125 , at every alpha ;
  T2 = (1/8)(1 - h2(Q)) = 0.09992220946091067 at Q = 1/32 ;
  T3 = (1/8)(1 - 2 h2(Q)) = 0.07484441892182134 at Q = 1/32 ;
  T4 = Q* = 0.11002786443835955 , UNCHANGED.

STEP 2 -- A FINDING: NO WEAK-COHERENT-PULSE SOURCE IS TAIL-FREE, so D-1's
hypothesis is not available to this submodule. eq:weightineq asks
p~(n|mu) <= p_mu(n), and a tail-free declaration needs
p~(0|mu) + p~(1|mu) = 1, hence e^{-mu}(1 + mu) >= 1, i.e. 1 + mu >= e^{mu},
which is FALSE for every mu > 0 and an equality only at mu = 0. At mu = 0 the
source emits vacuum and there is no single-photon sector at all (that is
DECOY-VACUUM, a different target). So a tail-free source with weight on n = 1
is not a declaration of transmitter/decoy at all; it is a different source
model, and this entry records the tail-free numbers as the COMPARISON they are.

STEP 3 -- THE EXACT TAIL-CORRECTED VALUE, which is what an implementation of
the decoy instance must reproduce. At DECOY-IDEAL-TWO-SECTOR the tail flag's
rounds DO click (an ideal threshold pair fires on every n >= 1) and DO carry
the letter gen, while their deficit is IDENTICALLY ZERO (OT2: within a flag
sector the key value is constant). So the tail adds mass to P_gen and nothing
to the deficit:
  g_1 = 1/8 , g_tail = 1/8 , P_gen = 1/4 ,
  K_gen = P_gen - (1 - 2^{1-alpha}) g_1     (h_1 = 1 at lambda = (1,0,0,0)) ,
  O_gen(alpha) = (1/4)/(alpha-1) * log2( (1/4) / (1/4 - (1-2^{1-alpha})/8) ) .
At alpha = 2 this is (1/4) log2( (1/4)/(3/16) ) = (1/4) log2(4/3)
= 0.10375937481971094, against the scaled target 1/8 = 0.125: THE TAIL COSTS
0.0212... AT alpha = 2, and the alpha-INDEPENDENCE OF T1 IS DESTROYED. In the
limit alpha -> 1+ the two agree again, because 1 - 2^{1-alpha} ~ (alpha-1) ln2
makes the key term sum_t g_t h_t, and h_tail = 0 removes the tail: the frozen
table's approach to 1/8 is the check.

WHY h_1 = 1 AT THE NOISELESS POINT. lambda = (1, 0, 0, 0) gives S = 1 in
OT4's closed form, so h_1 = 1 - log2(1)/(alpha-1) = 1 exactly, at every alpha.
That is the one-photon sector being a perfect qubit channel, and it is where T1
comes from in bb84_targets.honest_point_objective.""",
    hypotheses=(
        "Direct reconciliation, key holder Alice, r(x, v) = bit(a). Under "
        "reverse reconciliation the tail flags are NOT key inert and step 3's "
        "zero deficit is false.",
        "Acceptance convention A: the gen letter carries a sifted generation "
        "round only, so P_gen IS the sifted generation probability. Under "
        "convention B the whole scaling argument fails, because P_gen = 1-gamma "
        "does not scale with w at all.",
        "An IDEAL receiver: eta = 1, p_dc = 0, one click per round with n >= 1 "
        "and none at n = 0. With dark counts the vacuum contributes a deficit "
        "of its own (OT1) and step 1's f_{gen,0} = 0 is false.",
        "The tail-free comparison source is NOT a weak-coherent-pulse source "
        "(step 2); its numbers are recorded as a comparison and nothing here "
        "asserts that transmitter/decoy can declare it.",
        "T1 to T4 are read with p^A_Z p^B_Z replaced by 1 - gamma, Bob "
        "announcing Z on every generation round.",
    ),
    observable=(
        "The engine's entropy term on the two-sector decoy declaration at the "
        "noiseless honest point, against d1_objective_with_tail(alpha) on the "
        "frozen grid; and its alpha -> 1+ limit against 1/8. Separately: that "
        "the value at alpha = 1.05 is NOT 1/8, which is what an implementation "
        "would report if it dropped the tail flag's mass from P_gen."
    ),
    closed_form=d1_objective_with_tail,
    frozen_values=(
        (1.05, 0.12391701172926643),
        (1.25, 0.11959154952300394),
        (1.5, 0.11422334841819404),
        (1.75, 0.1089340690603486),
        (1.9, 0.105813382233168),
    ),
    value=F(1, 8),
    value_closed_form=(
        "the tail-free target and the alpha -> 1+ limit: w (1 - gamma) = 1/8"
    ),
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (meat-core 1.1.0, reductions
0.2.0). EVERY NUMBER STANDS; nothing was edited.

WHAT NOW CARRIES STEP 1. The scaling argument used positive homogeneity of the
deficit and the vanishing of the vacuum's deficit at an ideal receiver. Both
are now claims: lem:rank-one-sector (iii) makes the deficit of a rank-one
Alice sector LINEAR in the block, with the constant eta_kappa of
eq:rank-one-weights, so homogeneity is a special case of linearity; and at
g_0 = 0 the linear form is zero. prop:a-neutral licenses the restriction to
Alice-block-diagonal states in either source mode.
THE TAIL'S ZERO DEFICIT is lem:rank-one-sector (iv)'s last sentence, "if the
key is constant on every X_kappa where mu_x > 0 then eta_kappa = 0 and f
vanishes on these blocks" -- an identity, as OT2 says.
STEP 2 IS UNTOUCHED: 1 + mu < e^mu is arithmetic, and
transmitter/decoy/cor:emitted-decoy (v) is unchanged by the accepted claims.
WHAT THE ACCEPTED CLAIM ADDS TO STEP 3, and it is the finding restated in the
claim's own words: lem:rank-one-sector (iv) carries the qualifier "what the
expression assigns to the pair is its fail weight plus d^{1-alpha} times its
pass weight, so with a non-zero fail weight in the same joint pair the
contribution is strictly less than that of a sector of conditional entropy
log_2 d, and equals it exactly when the pass weight is the whole of the pair's
weight" -- added by that claim's own round-2 pass (scope M F-5(a)). That is
this entry's step 3 for a tail and D-2's convention split, arrived at
independently and now agreeing.
lem:source-transfer is pinned for the comparison of step 2: it is stated in
TRUSTED-source mode, which is this instance's, and its source identity is what
makes the tail-free source a different declaration rather than a perturbation.""",
)


O_DECOY_D2_VACUUM_BIT = DecoyOracleEntry(
    oracle_id="O-DECOY-D2-VACUUM-BIT",
    claims=(
        "transmitter/decoy/def:wcp-model",
        "transmitter/decoy/prop:tagging",
        "transmitter/decoy/prop:decoy-cert",
        "meat-core/thm:branch-formula",
        "meat-core/def:branch",
        "foundations/def:pinching",
        "foundations/def:renyi",
        "meat-core/lem:rank-one-sector",
        "meat-core/prop:a-neutral",
    ),
    kind="toy-instance",
    subject=(
        "D-2: at a source whose every label emits vacuum and a receiver with "
        "dark counts, every sifted generation click carries exactly one bit at "
        "every alpha. Frozen under BOTH acceptance conventions, because the "
        "phrase 'per sifted generation round' is what decides the number."
    ),
    instance="DECOY-VACUUM",
    derivation="""\
THE MECHANISM, in the objective's own quantities. Every label emits |vac>, so
the vacuum is the only sector, tau^{(0)}_A = 1 is rank one, and by OT3 every
feasible block is omega^{(0)} = tau^{(0)}_A (x) sigma_0. By derivations/06
Lemma 6.1 the deficit of a rank-one Alice sector under direct reconciliation is
LINEAR in omega:
  f_{gen,(0,s)} = -(1 - sum_z pi(z)^alpha) tr G_{gen,(0,s)} ,
with pi(z) proportional to sum over the generation labels whose key value is z
of <v|M^{(0)}_x|v>. The two generation labels (H, 0, gen) and (V, 0, gen) carry
key values 0 and 1 and EQUAL weights p_x = 1/4, and in a one-dimensional sector
<v|M^{(0)}_x|v> is the declared number p_x itself (lem:ensemble-presentation
(v): the operator a consumer reads is N^{(0)}_x = p_x, the declared block). So
pi = (1/2, 1/2), sum_z pi^alpha = 2 * 2^{-alpha} = 2^{1-alpha}, and
  f_gen = -(1 - 2^{1-alpha}) tr G_gen , THE FULL BINARY FACTOR, at every alpha.
"Exactly one bit" is this factor being the one a uniform binary key value
gives: H_alpha(pi) = 1 for every order, which is the plan's own reason.

CONVENTION A -- THE NUMBER IS EXACT AND alpha-INDEPENDENT. P_gen = tr G_gen
= g_0 = (1 - gamma) Y_0 = (1/2)(1/64) = 1/128, so
  K_gen = P_gen - (1 - 2^{1-alpha}) P_gen = 2^{1-alpha} P_gen ,
  O_alpha = (P_gen/(alpha-1)) log2(P_gen / (2^{1-alpha} P_gen))
          = (P_gen/(alpha-1)) (alpha-1) = P_gen = 1/128 = 0.0078125 ,
AT EVERY alpha IN (1, inf). One bit per sifted generation round, exactly, with
the round count being 1/128 of all rounds. This is the vacuum sector's version
of bb84_targets.honest_point_objective's alpha cancellation: the 2^{1-alpha}
inside the logarithm cancels the 1/(alpha-1) outside it.

CONVENTION B -- THE SAME PHYSICS, A SMALLER NUMBER, AND WHY. Here
P_gen = 1 - gamma = 1/2 carries every generation round, sifted or not, so
  K_gen = 1/2 - (1 - 2^{1-alpha})(1/128) ,
  O_alpha = (1/2)/(alpha-1) * log2( (1/2) / (1/2 - (1-2^{1-alpha})/128) ) ,
which at alpha = 2 is (1/2) log2(128/127) = 0.0056576566139170635 -- strictly
BELOW 1/128 = 0.0078125. THE REASON IS STRUCTURAL AND NOT A ROUNDING: the
failing branch Theta enters K linearly and is untouched by the pinching
(thm:branch-formula's proof: (Theta^{1/alpha})^alpha = Theta), so a round that carries the
gen letter without carrying a key value dilutes the ratio K/P instead of
contributing its own bit. The two conventions agree only as alpha -> 1+, where
1 - 2^{1-alpha} ~ (alpha-1) ln 2 turns the key term into sum_t g_t h_t = g_0
= 1/128 under either. THE FROZEN TABLE'S APPROACH TO 1/128 IS THAT CHECK.

SO THE PLAN'S "EVERY SIFTED GENERATION CLICK CARRIES EXACTLY ONE BIT, AT EVERY
alpha" IS TRUE OF THE DEFICIT AND OF CONVENTION A, AND FALSE OF CONVENTION B'S
OBJECTIVE VALUE. That is a finding about the phrase and not about the
mathematics, and both numbers are frozen so that an implementation cannot pick
the convention that makes its output look right.

WHY DARK COUNTS ARE THE POINT. Without them Y_0 = 0, every quantity above is
zero, and the target is vacuous: the entry needs a receiver that clicks on
nothing. p_dc = 1/64 and eta arbitrary give Y_0 = p_dc exactly, the click's
outcome being uniform over the announced pair's two detectors because their
dark counts are independent and identically distributed. Alice's bit is
independent of Eve's system whatever Eve does, which is why the entry is
state independent: it holds at EVERY feasible sigma_0 and not only at an
honest one.""",
    hypotheses=(
        "Direct reconciliation with r(x, v) = bit(a) and the two generation "
        "labels of EQUAL weight. At unequal weights pi is not uniform and the "
        "factor becomes 1 - sum_z pi(z)^alpha < 1 - 2^{1-alpha}; "
        "O-DECOY-OT1-VACUUM-DEFICIT freezes that foil.",
        "Every intensity is zero, so the source emits vacuum for every label "
        "and there is no tail flag. Zero TRANSMITTANCE is a different "
        "situation and not this one.",
        "A receiver with a strictly positive dark-count probability, whose "
        "click outcome is uniform over the announced pair.",
        "Convention A for the frozen value 1/128; convention B for the frozen "
        "table. The entry states both and asserts each only of its own "
        "convention.",
        "The statement is state independent: it holds at every sigma_0 >= 0, "
        "so it is an exact test at any feasible point and not only at an "
        "honest one.",
    ),
    observable=(
        "Under convention A: the engine's entropy term on the all-vacuum "
        "declaration equals 1/128 at every alpha of the grid, to the run's "
        "declared tolerance, and the per-sifted-round figure is 1.0 bit. Under "
        "convention B: equals d2_objective_convention_b(alpha). Also: the "
        "sector deficit factor itself, if the objective code exposes it, "
        "equals 1 - 2^{1-alpha}."
    ),
    value=F(1, 128),
    value_closed_form="convention A: O_alpha = P_gen = (1-gamma) Y_0 = 1/128",
    closed_form=d2_objective_convention_b,
    frozen_values=(
        (1.05, 0.007680714400278997),
        (1.25, 0.007181991917993397),
        (1.5, 0.00661758528292456),
        (1.75, 0.0061117047158968695),
        (1.9, 0.005833450612698414),
    ),
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (meat-core 1.1.0). BOTH
NUMBERS STAND; nothing was edited, and the accepted claim states this entry's
finding itself.

THE CLOSED FORM IS NOW A CLAIM. lem:rank-one-sector (iii) gives the vacuum
sector's deficit as -sum_kappa eta_kappa m_kappa sum_v tr[F_v sigma] with
eta_kappa = 1 - sum_z (m_{kappa,z}/m_kappa)^alpha, which is this entry's
factor with pi(z) = m_{kappa,z}/m_kappa; (iv) at d = 2 equal weights gives
eta = 1 - 2^{1-alpha}, the frozen constant, and states it holds ON THE PASS
WEIGHT.
THE CONVENTION SPLIT IS THE CLAIM'S OWN QUALIFIER. (iv): the pair is assigned
"its fail weight plus d^{1-alpha} times its pass weight", so the contribution
"is strictly less than that of a sector of conditional entropy log_2 d" when
the fail weight is non-zero "and equals it exactly when the pass weight is the
whole of the pair's weight". Convention A puts the whole of the pair's weight
in the pass class, which is why 1/128 is exact at every alpha; convention B
leaves a fail weight in the same pair, which is why its table is strictly
below. The two agree in the limit, as frozen.
WHAT THE HYPOTHESES GAIN. This entry assumed "the default partition, so that
a^{-1}(kappa) is a product set". lem:rank-one-sector (ii) PROVES that from the
default readouts rd_A(x,v) = x, rd_B(x,v) = v for EVERY transcript protocol of
def:declaration (DX5) -- so the assumption is discharged rather than merely
stated, and it is discharged for the announcement shape this instance uses,
which is protocol-compiler/ex:transcript's (Alice announces the round type;
Bob discloses his bit on test rounds and only the detection on generation
rounds). The note's alternative rd_B(x, v) = (v, z), which reads Alice's round
type into BOB'S READOUT, is NOT covered by (ii) and is not this instance.""",
)


O_DECOY_D3_CUTOFF_MONOTONE = DecoyOracleEntry(
    oracle_id="O-DECOY-D3-CUTOFF-MONOTONE",
    claims=(
        "transmitter/decoy/prop:tagging",
        "transmitter/decoy/rem:cutoffs",
        "transmitter/decoy/rem:no-intensity-split",
        "meat-core/def:keyinert",
        "meat-core/def:joint-sectors",
        "meat-core/prop:exact-cancellation",
        "meat-core/thm:branch-formula",
        "meat-core/lem:rank-one-sector",
        "meat-core/prop:drop-bound",
        "reductions/lem:precomposition",
        "reductions/lem:source-transfer",
    ),
    kind="relation",
    subject=(
        "D-3: h_low is non-decreasing in N_ent and in N_src at fixed "
        "everything else. Frozen as a RELATION with its hypotheses, together "
        "with a hand-computed witness of the N_ent direction on DECOY-TOY."
    ),
    instance="DECOY-TOY",
    derivation="""\
THE RELATION, and it is two relations with two different mechanisms.

(a) N_ent. Let two declarations share the source model, the intensity set, the
label weights, the declared weights p~(n|mu) on every sector BELOW the smaller
cutoff, the receiver, the acceptance set and alpha, and differ only in
N_ent = m against N_ent = m' > m. Then the smaller-cutoff declaration's virtual
source is obtained from the larger one's by a CHANNEL Gamma that prepares
|n,a> from the polarisation flag f_{n,a} for m < n <= m' and is the identity
elsewhere: Xi_tag^{(m)} = Xi_tag^{(m')} o Gamma, both sides being the tagging
channel of prop:tagging for their own declaration. Composing an attack with a
channel on the virtual signal keeps it admissible for a LICENSED list, so
every attack the larger-cutoff protocol admits gives an attack the
smaller-cutoff protocol admits, and the smaller cutoff faces at least as large
a family. Hence h_low(m) <= h_low(m').
INSIDE THE ENGINE THE SAME ORDERING IS VISIBLE WITHOUT ANY SOURCE MAP, and
this is the half that is hand-checkable: pushing a feasible point of the
larger-cutoff program through Gamma's action on the blocks gives a feasible
point of the smaller-cutoff program whose newly-flagged sectors have RANK-ONE
marginals, hence (OT3) factorise, hence (OT2) have deficit IDENTICALLY ZERO,
while their deficit before the push was <= 0 (cor:f-nonpos). So
K_smaller >= K_larger at corresponding points, and Eq. eq:objective's key term
is non-increasing in K, giving O_smaller <= O_larger point by point.

(b) N_src. Raising N_src splits a tail flag into four one-dimensional
polarisation flags per photon number, shared across intensities
(rem:no-intensity-split: they may NOT be split by intensity). Splitting a
sector into sectors refines the block structure of the feasible set, so the
transported constraints bind per flag instead of in aggregate and the feasible
set shrinks; a smaller feasible set has a larger infimum. Neither direction
changes the entropy: every flag sector's deficit is zero either way (OT2), so
the gain is entirely in the STATISTICS. That is why the plan says raising N_src
"tightens the statistics" and never requires raising N_ent.

THE WITNESS, N_ent = 0 against N_ent = 1 on DECOY-TOY, at the honest point.
At N_ent = 0 the one-photon sector becomes the four polarisation flags f_{1,a}
(N_src = 1 is unchanged), so its deficit is zero and only the vacuum survives:
  K(N_ent = 0) = P_gen - (1 - 2^{1-alpha}) g_0 ,
  K(N_ent = 1) = P_gen - (1 - 2^{1-alpha}) g_0
                        - (1 - 2^{(1-alpha) h_1}) g_1 ,
so K(0) >= K(1) and O(0) <= O(1) with the frozen numbers
  alpha = 2 : O(0) = 0.002860531747143983 , O(1) = 0.013787477747325139 ,
and the whole grid frozen in ``frozen_values`` (N_ent = 0) against
O-DECOY-OT5-DROPPED-HONEST's table (N_ent = 1). THE WITNESS IS AT ONE POINT AND
IS NOT THE RELATION: both numbers are objective values at the honest point,
which bound h_low from above, and an upper bound moving up is not a proof that
an infimum does. What the witness does show is the DIRECTION and the
mechanism, and that the effect is not numerically negligible: a factor of about
five at alpha = 2.

WHAT MUST BE HELD FIXED, AND WHY THE RELATION IS EMPTY OTHERWISE. If raising
N_ent also raises the declared weight p~(n|mu) on a sector the two share, the
two declarations are not comparable: the weights, the ensemble, the tail states
and the sector list are all re-formed (cor:emitted-decoy (v), "the rounded
declaration is a different declaration, not a perturbation of one"). The extra
sector's weight must come out of the tail and out of nothing else.""",
    hypotheses=(
        "Both declarations share the source model, the label weights, the "
        "declared weights on the common sectors, the receiver, the acceptance "
        "set, alpha and the reconciliation direction. The extra sector's "
        "weight comes out of the tail.",
        "Direct reconciliation: (a)'s engine half and the witness both use "
        "OT2, which is false under reverse reconciliation.",
        "The constraint list is LICENSED throughout. A `general` entry beside "
        "a source segment is refused (reductions/rem:ordering and the plan's "
        "section 2.1), and the composition argument of (a) has no meaning for "
        "one.",
        "0 <= N_ent <= N_src, and N_ent <= 2 for a declaration this submodule "
        "will emit at all (cor:emitted-decoy (vi) refuses N_ent >= 3).",
        "The witness compares the OBJECTIVE AT THE HONEST POINT, not h_low.",
    ),
    observable=(
        "h_low at N_ent = 0, 1, 2 on one fixed decoy instance with everything "
        "else held fixed, asserted non-decreasing with the Frank-Wolfe gap "
        "beside each number, a difference below the gap named as solver noise. "
        "And, as the hand-checkable half: the objective at the honest point at "
        "N_ent = 0 against flagged_single_photon_objective(alpha)."
    ),
    relation=(
        "h_low(N_ent = m) <= h_low(N_ent = m') for m <= m', and "
        "h_low(N_src = k) <= h_low(N_src = k') for k <= k', at fixed source "
        "model, label weights, common declared weights, receiver, acceptance "
        "set, alpha and reconciliation direction."
    ),
    closed_form=flagged_single_photon_objective,
    frozen_values=(
        (1.05, 0.0038432314387314877),
        (1.25, 0.003603616017836517),
        (1.5, 0.0033303219278679116),
        (1.75, 0.003083506814872908),
        (1.9, 0.002947020534713077),
    ),
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (reductions 0.2.0, meat-core
1.1.0). THE RELATION AND THE WITNESS STAND; nothing was edited.

BOTH HALVES OF (a) NOW HAVE A CLAIM. The source-map half is
lem:precomposition: for a list of the licensed form -- Hermitian O_k, real c_k
-- and ANY channel Gamma into the attack's input register,
A in AttSet_CList implies A o Gamma in AttSet_CList, in either source mode
(parts (i) and (ii)), and part (iv) exhibits why a `general` right-hand side
would not survive it, which is why this entry's hypotheses confine it to a
licensed list. Note what a later pass removed: the finite-dimension
restriction on the released signal register, so the Fock-space decoy source is
covered -- which this entry needs and did not have when it was frozen.
The engine half is lem:rank-one-sector (iv) for the newly-flagged sector's zero
deficit, cor:f-nonpos for f <= 0 before the push, and prop:drop-bound (iii) for
the monotonicity of the infimum in what is dropped.
THE WITNESS IS UNCHANGED, and it remains what it was labelled: two objective
values at the honest point, bounding h_low from above, not h_low itself.
WHAT I CHECKED AND DID NOT ASSUME. lem:source-transfer is stated in
TRUSTED-source mode only; this instance is trusted, so the ordering argument
is available here and would not be for an untrusted-source protocol.""",
)


O_DECOY_D4_INFINITE_DECOY_CEILING = DecoyOracleEntry(
    oracle_id="O-DECOY-D4-INFINITE-DECOY-CEILING",
    claims=(
        "meat-core/thm:oracle",
        "meat-core/rem:oracle",
        "meat-core/def:feasible",
        "transmitter/decoy/cor:emitted-decoy",
        "transmitter/decoy/prop:tagging",
        "transmitter/decoy/def:wcp-model",
        "meat-core/lem:rank-one-sector",
        "meat-core/prop:a-neutral",
        "reductions/lem:source-transfer",
    ),
    kind="relation",
    subject=(
        "D-4: the alpha -> 1+ limit of the entropy term is bounded above by "
        "the infinite-decoy asymptotic term p_0 Y_0 + p_1 Y_1 (1 - h2(e_1)) of "
        "the honest model, per generation round. Frozen as a relation, with "
        "the feasible WITNESS POINT that proves it and both ceiling values."
    ),
    instance="DECOY-TOY",
    derivation="""\
THE CEILING AND ITS TWO READINGS. Per generation round the standard
infinite-decoy asymptotic entropy term is
  C_true = p_mu(0) Y_0 * 1 + p_mu(1) Y_1 (1 - h2(e_1)) ,
the vacuum contributing a full bit, the single photon 1 - h2 of its phase error
and every multi-photon round nothing. At DECOY-TOY, with p_mu(0) = e^{-1/2},
p_mu(1) = (1/2) e^{-1/2}, Y_0 = 1/64, Y_1 = 67/256 and e_1 = 1/8:
  C_true = e^{-1/2}[1/64 + (67/512)(1 - h2(1/8))] = 0.04570443350844794 ,
and per channel use (1 - gamma) C_true = 0.02285221675422397.
THE SAME EXPRESSION AT THE DECLARED (ROUNDED-DOWN) WEIGHTS IS SMALLER:
  C_decl = (1/2)(1/64) + (1/4)(67/256)(1 - h2(1/8)) ,
  (1 - gamma) C_decl = g_0 + g_1 (1 - h2(1/8)) = 0.018838467922669452 ,
and the gap is exactly the weight this declaration rounds into the tail.

WHY IT IS A CEILING, WITH NO MONOTONICITY IN alpha ANYWHERE IN THE ARGUMENT.
h_low is an INFIMUM (Eq. eq:hlow-def), so it is at most the objective at any
feasible point; the argument is therefore to exhibit one point.
THE WITNESS POINT: the block list whose vacuum block is
tau^{(0)}_A (x) sigma_0 with sigma_0 the honest dark-count state, whose tail
blocks are the honest tail-flag products, and whose one-photon block is
(1/4) times the INDEPENDENT-ERROR Bell-diagonal state
  lambda = ((1-e)^2, e(1-e), e(1-e), e^2)  at e = 1/8 ,
in the OT4 index order (bit index first). It is feasible: every block is
positive, the A-marginals are the declared tau^{(t)}_A (Bell-diagonal states
have maximally mixed marginal, which tau^{(1)}_A = (1/8) 1_2 is), the total
trace is one, and the DECLARED STATISTICS ARE REPRODUCED because the yields are
the honest ones and the state has bit error e and phase error e, which is what
the test rounds observe.
ITS VALUE IN THE LIMIT alpha -> 1+ is sum_t g_t h_t with h_0 = 1,
h_tail = 0 and h_1 = 1 - H(phase | bit) = 1 - h2(e), the conditional entropy of
the phase index given the bit index being EXACTLY h2(e) at the independent
point:
  lim_{alpha -> 1+} h_low <= g_0 + g_1 (1 - h2(1/8)) = 0.018838467922669452
                          <= (1 - gamma) C_true = 0.02285221675422397 ,
the second step by p~(n|mu) <= p_mu(n) with the same Y_n. THE FIRST NUMBER IS
THE SHARPER CEILING AND IS THE ONE A TEST SHOULD USE.

WHY THE INDEPENDENT-ERROR STATE AND NOT THE DEPOLARISED ONE. H(phase | bit)
<= H(phase) = h2(e) always, with equality iff the two are independent, so the
independent-error state is the WORST Bell-diagonal state at these statistics and
the depolarised honest state is not: at lambda = (13/16, 1/16, 1/16, 1/16) the
same functional gives 1 - [(7/8) h2(1/14) + 1/8] = 0.5501717141892338, well
ABOVE 1 - h2(1/8) = 0.4564355568004036. Comparing a solver's limit against the
honest state's value would be comparing against the wrong number, which is the
distinction tests/support/bb84_targets.limit_at_depolarized_state exists to
record for the qubit case; here it is the difference between a ceiling that
holds and one that does not.

WHAT IS NOT CLAIMED. Nothing here says h_low is monotone in alpha, and nothing
here uses that: the relation is stated for the alpha -> 1+ limit alone, which
is the quantity thm:oracle and rem:oracle define. At finite alpha the same two
numbers are recorded as a plausibility check and asserted of nothing. And the
inequality is STRICT at every finite round count for the reasons
bb84_targets.devetak_winter_ceiling gives: the acceptance polytope is larger
than the honest singleton, alpha is bounded away from 1 by the privacy
amplification cost, and the finite-size deductions are positive.""",
    hypotheses=(
        "The honest model of DECOY-TOY, whose yields are "
        "Y_n = 1 - (1 - p_dc)(1 - eta)^n and whose single-photon phase error "
        "is e_1 = 1/8.",
        "The alpha -> 1+ limit, as meat-core/thm:oracle defines it. No "
        "monotonicity in alpha is claimed or used.",
        "Direct reconciliation, convention A, Bob announcing Z on every "
        "generation round; the per-generation-round figures divide by "
        "1 - gamma and nothing else.",
        "The ceiling is a CEILING: it may never be used as a lower bound, and "
        "it is not h_low.",
        "The witness point is feasible only because the declared marginals are "
        "the ones the ensemble presentation defines; a declaration that "
        "compressed or snapped its blocks would not contain it.",
    ),
    observable=(
        "lim h_low as alpha -> 1+ on the decoy instance (or h_low at the "
        "smallest admissible alpha, with its gap) against 0.018838467922669452 "
        "as an upper bound; and the objective at the named witness point "
        "against that same number, which needs no solver."
    ),
    relation=(
        "lim_{alpha -> 1+} h_low <= g_0 + g_1 (1 - h2(e_1)) <= "
        "(1 - gamma)[p_mu(0) Y_0 + p_mu(1) Y_1 (1 - h2(e_1))], with g_t the "
        "sifted generation probabilities of the declared weights."
    ),
    value=0.018838467922669452,
    value_closed_form=(
        "g_0 + g_1 (1 - h2(1/8)) = 1/256 + (67/2048)(1 - h2(1/8)); the wider "
        "ceiling is (1/2) e^{-1/2}[1/64 + (67/512)(1 - h2(1/8))] "
        "= 0.02285221675422397"
    ),
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (meat-core 1.1.0). BOTH
CEILINGS STAND; nothing was edited.

THE WITNESS POINT IS FEASIBLE FOR THE REASONS THE CLAIMS NOW GIVE.
prop:a-neutral: the Alice-block-diagonal list is where the infimum lives, in
either source mode and with an arbitrary list, `general` and `party_local`
entries included -- so building the witness sector by sector is legitimate.
lem:rank-one-sector (i): on the vacuum and on every flag the block MUST be
tau^{(t)}_A (x) sigma_s, so the witness's vacuum and tail blocks are the only
shape available and their contribution is fixed by (iii)-(iv) at 1 and 0 bits.
The one-photon block is rank two and is where the witness's choice of state
does the work.
NO MONOTONICITY IN alpha IS CLAIMED, and nothing in the accepted claims supplies one: the
relation is stated for the alpha -> 1+ limit of thm:oracle alone, as frozen.
THE SHARPER NUMBER IS STILL THE SHARPER ONE: the declared-weight ceiling
0.018838467922669452 is below the Poisson one because p~(n|mu) <= p_mu(n), and
transmitter/decoy/cor:emitted-decoy (v) is untouched by the accepted claims.""",
)


O_DECOY_D5_STATISTICS = DecoyOracleEntry(
    oracle_id="O-DECOY-D5-STATISTICS",
    claims=(
        "transmitter/decoy/def:wcp-model",
        "transmitter/decoy/def:tagged-source",
        "transmitter/decoy/prop:tagging",
        "transmitter/decoy/cor:emitted-decoy",
        "meat-core/def:maps",
        "meat-core/thm:protocol-channel",
        "meat-core/lem:ensemble-form",
        "meat-core/def:declaration",
        "protocol-compiler/ex:transcript",
    ),
    kind="toy-instance",
    subject=(
        "D-5: at one intensity and N_src = N_ent the statistics map equals "
        "sum_n p_mu(n) Y_n on the honest channel, with the closed form "
        "1 - (1 - p_dc) e^{-eta mu}; and the tail flag's honest yield is "
        "FORCED by that identity and is not a free number."
    ),
    instance="DECOY-TOY",
    derivation="""\
THE IDENTITY, from the Poisson generating function and nothing else. For a
threshold receiver of efficiency eta and dark-count probability p_dc the
n-photon detection probability is Y_n = 1 - (1 - p_dc)(1 - eta)^n, and
  sum_{n>=0} e^{-mu} mu^n / n! * (1 - eta)^n = e^{-mu} e^{mu(1-eta)}
                                             = e^{-eta mu} ,
so
  sum_n p_mu(n) Y_n = 1 - (1 - p_dc) e^{-eta mu} .
At DECOY-TOY's mu = 1/2, eta = 1/4, p_dc = 1/64:
  sum_n p_mu(n) Y_n = 1 - (63/64) e^{-1/8} = 0.1312921115182889 .
THAT IS THE PHYSICAL CLICK PROBABILITY PER ROUND, and it is what the honest
model declares through the acceptance-frequency snap. It is NOT a function of
the declared weights p~: the declaration's weights are the source's virtual
description, the frequencies are the apparatus's.

HOW THE DECLARATION REPRODUCES IT, WHICH IS THE PART AN IMPLEMENTATION CAN GET
WRONG. In the Choi coordinates of derivations/06 section 6.1,
  tr[(M_x (x) F_v) omega]
    = p_x [ sum_{n <= N_src} p~(n|x) Y^{a,v}_n + w~_mu u^v_{a,mu} ] ,
so with N_src = N_ent = 1 the declared click probability per label is
  p~(0|mu) Y_0 + p~(1|mu) Y_1 + w~_mu Y_tail .
The tail flag's output state is whatever Xi_tag prepares from it, and
prop:tagging fixes that: the NORMALISED REMAINDER
  (rho_x - sum_{n <= N_src} p~(n|mu) |n,a><n,a|) / w~_mu ,
which carries the Poisson tail AND the shortfall rounded out of the low
sectors. Hence
  Y_tail = [ sum_n p_mu(n) Y_n - sum_{n <= 1} p~(n|mu) Y_n ] / w~_mu ,
and at DECOY-TOY, with sum_{n<=1} p~ Y_n = (1/2)(1/64) + (1/4)(67/256)
= 1/128 + 67/1024 = 75/1024:
  Y_tail = 4[1 - (63/64) e^{-1/8} - 75/1024] = 949/256 - (63/16) e^{-1/8}
         = 0.2321996960731556 .
THE IDENTITY IS THEN EXACT BY CONSTRUCTION: (1/2)(1/64) + (1/4)(67/256)
+ (1/4) Y_tail = 75/1024 + [1 - (63/64) e^{-1/8} - 75/1024]
= 1 - (63/64) e^{-1/8}. The integrity test does that cancellation in exact
rational arithmetic on the rational part.

THE TWO WAYS TO GET IT WRONG, both of which this entry refuses. (a) Giving the
tail flag the two-photon yield Y_2 = 1 - (63/64)(9/16) = 457/1024
= 0.4462890625, which is nearly twice the right number, because the tail is
dominated by the ROUNDED-OUT LOW-SECTOR WEIGHT and not by genuine
multi-photon events: at mu = 1/2 the true Poisson tail beyond n = 1 has mass
1 - (3/2) e^{-1/2} = 0.0902..., while w~ = 1/4. (b) Treating Y_tail as a free
yield to be bounded by the statistics. It is free in the FEASIBLE SET -- the
optimiser may move it -- but in the HONEST MODEL it is determined, and the
honest point is what D-5 is about.

WHY N_src = N_ent MATTERS. With N_src > N_ent there are polarisation flags
between the cutoffs, each with its own output state shared across intensities,
and the identity splits into one term per flag; the total is the same but the
per-label statistics carry more structure. At one intensity the decoy
statistics cannot separate the yields at all, which is why this entry pins the
honest identity and NOT any tightness of the constraints.""",
    hypotheses=(
        "One intensity, N_src = N_ent = 1, the threshold-pair receiver of "
        "DECOY-TOY with Y_n = 1 - (1 - p_dc)(1 - eta)^n.",
        "The honest channel: a phase-randomised coherent state through a lossy "
        "channel into a threshold detector. The identity is about the honest "
        "model and asserts nothing about the feasible set.",
        "The tail flag's honest output is the normalised remainder that Xi_tag "
        "prepares (prop:tagging), NOT a two-photon state and not a free yield.",
        "Declared weights strictly below Poisson, so w~_mu > 0 and the "
        "division defining Y_tail is legitimate.",
    ),
    observable=(
        "The instance's honest statistics vector: the total click probability "
        "per generation round against (1 - gamma)[1 - (1 - p_dc) e^{-eta mu}] "
        "= 1/2 - (63/128) e^{-1/8}, and the tail flag's declared honest output "
        "yield against 949/256 - (63/16) e^{-1/8}. Both to the instance's "
        "declared tolerance, since the closed forms are irrational."
    ),
    value=0.1312921115182889,
    value_closed_form=(
        "sum_n p_mu(n) Y_n = 1 - (1 - p_dc) e^{-eta mu} = 1 - (63/64) e^{-1/8}"
    ),
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (meat-core 1.1.0, protocol-compiler
0.2.0). THE IDENTITY AND BOTH CLOSED FORMS STAND.

THE CONSUMER'S ENSEMBLE FORM EXISTS AND IS NOT NAMED AS I GUESSED. There is no
`def:ensemble-form`: the form is def:declaration (DX4) -- Alice's measurement
slot holding block lists {N_x} with sum_x N^{(t)}_x = tau^{(t)}_A -- and what
makes it a definition is lem:ensemble-form, whose (ii) gives
tau^{1/2} M_x tau^{1/2} = N_x and (iii) M^{(t)}_x = 0 iff N^{(t)}_x = 0. Both
are pinned now. So the decoy declaration HAS a consumer, which
transmitter/decoy/cor:emitted-decoy (vii) said it did not when this entry was
frozen; that closes the second of its two fences and changes no number here.
TWO HYPOTHESES OF (DX4) I CHECKED RATHER THAN ASSUMED. (1) The ensemble form
exists in TRUSTED-SOURCE MODE ONLY. DECOY-TOY is trusted, so it is available;
an untrusted-source instance could not read this declaration at all, and no
entry of this file asks it to. (2) (DX4) requires tau^{(t)}_A /= 0 on every
declared sector. DECOY-TOY satisfies it on both its sectors. DECOY-VACUUM's
`declared_weights` records a Poisson weight of 0 at n = 1, which is NOT a
declared sector: the structure carries "the sectors that some letter puts
positive weight on" (def:tagged-source (T3), cor:emitted-decoy), so its sector
list is the vacuum alone, as that instance's notes say.
THE ANNOUNCEMENTS ARE AN ACCEPTED EXAMPLE'S. protocol-compiler/ex:transcript is
this instance's transcript, message for message, with DEFAULT readouts.""",
)


# ===========================================================================
#  Group OT -- the five analytic targets of derivations/06 section 6.3
# ===========================================================================


O_DECOY_OT1_VACUUM_DEFICIT = DecoyOracleEntry(
    oracle_id="O-DECOY-OT1-VACUUM-DEFICIT",
    claims=(
        "meat-core/thm:branch-formula",
        "meat-core/def:branch",
        "foundations/def:pinching",
        "foundations/def:renyi",
        "meat-core/lem:rank-one-sector",
        "meat-core/prop:a-neutral",
        "meat-core/lem:ensemble-form",
        "meat-core/def:joint-sectors",
        "transmitter/decoy/prop:decoy-cert",
        "transmitter/lem:ensemble-presentation",
    ),
    kind="structural-identity",
    subject=(
        "OT1: the vacuum sector's deficit under direct reconciliation is "
        "LINEAR with the closed form f = -(1 - sum_z pi(z)^alpha) tr G, state "
        "independent, and the factor is 1 - 2^{1-alpha} exactly when the two "
        "key labels have equal weight. The biased-weight foil is frozen beside "
        "it."
    ),
    instance="DECOY-VACUUM",
    derivation="""\
THE CLOSED FORM, derived where derivations/06 Lemma 6.1 derives it and restated
here in the form an implementation can check. Let the Alice sector t have a
rank-one marginal tau^{(t)}_A = p_t |v><v| -- the vacuum sector does, because
every label shares |vac> (prop:decoy-cert (iii): r_t = 1 on the vacuum and on
every flag) -- and let the key value be a function of Alice's label alone
(direct reconciliation). Then:

 1. By OT3 every feasible block is omega_{ts} = tau^{(t)}_A (x) sigma_s.
 2. Under the default partition the class preimage a^{-1}(kappa) is a product
    set, so the branch operator of Eq. eq:kraus factors as
    K^{(t,s)}_kappa = A_kappa (x) B_kappa (x) |kappa>, and
    G_kappa = p_t |a><a| (x) B with |a> = A_kappa|v>.
 3. Writing |a_z> = Z_z|a> for the components of |a> at key value z, these are
    mutually orthogonal with squared norms m_z, m = sum_z m_z, so
    Z(G^{1/alpha}) = p_t^{1/alpha} m^{1/alpha - 1} sum_z |a_z><a_z| (x)
    B^{1/alpha}, whose alpha-th power has trace
    p_t m^{1-alpha} sum_z m_z^alpha tr B = (sum_z pi(z)^alpha) tr G_kappa with
    pi(z) = m_z / m.
 4. Classes are orthogonal, so T sums over kappa and
    f_{chat,(t,s)} = T - tr G = -(1 - sum_z pi(z)^alpha) tr G_{chat,(t,s)} .
THE DEFICIT IS THEREFORE LINEAR IN omega AND NEEDS NO MATRIX FUNCTION AT ALL,
which is the plan's performance item P6 and the reason the vacuum is KEPT with
its closed form and never dropped.

THE FACTOR, AND THE ONE PLACE A NUMBER LIVES. The plan writes the factor as
1 - 2^{(1-alpha) H_alpha(pi)} with
H_alpha(pi) = (1/(1-alpha)) log2 sum_z pi(z)^alpha; substituting gives
2^{(1-alpha) H_alpha(pi)} = sum_z pi(z)^alpha identically, so the factor is
1 - sum_z pi(z)^alpha and no logarithm or exponential is needed. At DECOY-VACUUM
the two generation labels have EQUAL declared weight, pi = (1/2, 1/2), and
  sum_z pi(z)^alpha = 2 * 2^{-alpha} = 2^{1-alpha} ,
so the factor is 1 - 2^{1-alpha}: frozen on the grid in ``frozen_values``, and
1/2 at alpha = 2. "Exactly one bit per sifted vacuum round" is this factor
being the uniform binary one, i.e. H_alpha(pi) = 1 for every order.

THE FOIL, WITHOUT WHICH THE ENTRY WOULD PASS FOR A HARD-CODED CONSTANT. Declare
the two generation labels at weights 3/4 and 1/4 instead (a legitimate
declaration: def:wcp-model fixes no label weights). Then pi = (3/4, 1/4) and the
factor is 1 - (3/4)^alpha - (1/4)^alpha, which at the grid is
  1.05: 0.027452612098187057 , 1.25: 0.12526966037678844 ,
  1.5 : 0.225480947161671   , 1.75: 0.3071660657009392 ,
  1.9 : 0.3492892227700074 ,
strictly below the uniform factor at every alpha -- an unbalanced key bit
carries less than one bit, and an implementation that wrote 1 - 2^{1-alpha}
into the vacuum sector would be wrong exactly here. The two tables are frozen
together because a single one is not evidence.

WHERE <v|M^{(t)}_x|v> COMES FROM UNDER THE ENSEMBLE PRESENTATION. Nothing forms
Alice's POVM: by lem:ensemble-presentation (v) the operator a consumer reads is
N^{(t)}_x = (sigma^{v,(t)}_x)^T, entrywise the declared numbers, and
tau^{(t)}_A = sum_x N^{(t)}_x. On a one-dimensional sector N^{(0)}_x is the
number p_x p~(0|mu) itself, so pi is the normalised restriction of the declared
label weights to each key value -- a quotient of DECLARED numbers and never a
square root.

WHY THE STATEMENT IS STATE INDEPENDENT AND WHAT THAT BUYS. Steps 1 to 4 used no
property of sigma_s, so the identity holds at EVERY feasible point: it is an
exact test of an implementation anywhere in the optimisation, not only at an
honest point, and a returned point where it fails is either infeasible or
computed by the wrong formula.""",
    hypotheses=(
        "Direct reconciliation: r(x, v) = r_A(x, kappa) is a function of "
        "Alice's label and the class. UNDER REVERSE RECONCILIATION THE WHOLE "
        "DERIVATION FAILS at step 3, the key value then not being constant on "
        "|a>'s components.",
        "The default partition, so that a^{-1}(kappa) is a product set.",
        "A rank-one Alice sector: tau^{(t)}_A = p_t |v><v|. True of the vacuum "
        "and of every flag sector (prop:decoy-cert (iii)), false of a quantum "
        "sector with n >= 1 and two or more polarisations.",
        "The factor is 1 - 2^{1-alpha} only at EQUAL weights of the two key "
        "labels; the biased table is the same closed form at pi = (3/4, 1/4).",
        "alpha in (1, inf). Nothing here needs alpha < 2.",
    ),
    observable=(
        "The objective code's vacuum-sector deficit, evaluated at several "
        "random feasible points, against "
        "-(1 - sum_z pi(z)^alpha) * tr G computed from the same branch "
        "operator: equality to machine precision AT EVERY POINT, not only at "
        "the honest one. And that the code takes no matrix power on that "
        "sector (plan item P6)."
    ),
    closed_form=lambda alpha: sector_deficit_factor(alpha, (0.5, 0.5)),
    frozen_values=(
        (1.05, 0.03406367107515451),
        (1.25, 0.1591035847462855),
        (1.5, 0.2928932188134524),
        (1.75, 0.4053964424986395),
        (1.9, 0.46411326873185343),
    ),
    value_closed_form="factor = 1 - sum_z pi(z)^alpha; uniform pi: 1 - 2^{1-alpha}",
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (meat-core 1.1.0). THE CLOSED
FORM, BOTH TABLES AND THE FOIL STAND, and this entry's subject is now a claim:
lem:rank-one-sector, whose (iii) is eq:rank-one-deficit.

STEP BY STEP AGAINST THE ACCEPTED TEXT. Step 1 is (i), product blocks, proved
the same way (Pi^perp with zero trace against a positive block). Step 2 is
(ii), and it is STRONGER than what this entry assumed: the product-set property
of a^{-1}(kappa) is proved from the default readouts for EVERY transcript
protocol, not assumed of a two-message announcement. Steps 3 and 4 are (iii),
with eta_kappa = 1 - sum_z (m_{kappa,z}/m_kappa)^alpha and
m_{kappa,z} = sum over the letters of the class with key value z of
mu_x = <v|M^{(t)}_x|v>: this entry's pi is exactly that probability vector, so
the frozen factor is eta_kappa at the uniform pi and the biased table is
eta_kappa at pi = (3/4, 1/4). The claim also records 0 <= eta_kappa < 1, which
the foil's table satisfies strictly.
THE DECLARED-NUMBER READING IS THE CLAIM'S OWN. (iii): "In ensemble form
mu_x = tr N^{(t)}_x / p_t and p_t = tr tau^{(t)}_A, declared numbers", by
lem:ensemble-form (ii). That is this entry's sentence about N^{(t)}_x, with the
completion chosen proportional to tr N_x rather than on the first letter -- a
difference that lives on ker tau^{(t)}_A and is invisible on a one-dimensional
sector of positive weight, which the vacuum is.
WHAT THE CLAIM ADDS THAT THE ENTRY DID NOT SAY: (iv)'s qualifier that the one
bit is one bit PER UNIT OF PASS WEIGHT. This entry froze the factor and not an
objective value, so no number moves; the objective-level consequence is D-2's
two conventions.""",
)


O_DECOY_OT2_FLAG_KEY_INERT = DecoyOracleEntry(
    oracle_id="O-DECOY-OT2-FLAG-KEY-INERT",
    claims=(
        "meat-core/def:keyinert",
        "meat-core/def:joint-sectors",
        "meat-core/prop:exact-cancellation",
        "meat-core/thm:branch-formula",
        "meat-core/cor:f-nonpos",
        "meat-core/lem:rank-one-sector",
        "meat-core/def:dropped",
        "meat-core/prop:drop-bound",
        "transmitter/decoy/prop:decoy-cert",
    ),
    kind="structural-identity",
    subject=(
        "OT2: under direct reconciliation a tail flag's and a polarisation "
        "flag's deficit is IDENTICALLY ZERO, at every feasible point and every "
        "alpha -- an identity and not the bound 'the tail is bounded by zero'. "
        "Value: 0 exactly."
    ),
    instance="DECOY-TOY",
    derivation="""\
THE IDENTITY. A flag sector t = (a, mu) carries weight from the letters with
that polarisation and intensity alone: by prop:decoy-cert's w_{x,t}, the
declared block sigma^{v,(t)}_x is non-zero only for letters with a_x = a, so
the consumer's operator N^{(t)}_x = (sigma^{v,(t)}_x)^T is non-zero only there.
Under direct reconciliation r(x, v) = bit(a_x), so within that sector every
letter with positive weight carries the SAME key value. Hence, in the closed
form of OT1, pi is a point mass:
  sum_z pi(z)^alpha = 1 ,  H_alpha(pi) = 0 ,  f = -(1 - 1) tr G = 0 ,
identically in omega and in alpha. Equivalently the joint pair (chat, (t, s))
is KEY INERT in the sense of meat-core/def:keyinert read on the joint sector,
and prop:exact-cancellation makes the deficit of a key-inert pair zero as an identity.

WHY THIS IS AN IDENTITY AND NOT A BOUND, and why that distinction is the entry.
cor:f-nonpos gives f <= 0 on the whole cone, so "the tail contributes at most
zero" is true of every sector and says nothing. What OT2 says is that here the
bound is ATTAINED for every omega: the tail costs exactly nothing beyond its
mass. The note's phrase "tail bounded by zero" is therefore an identity in this
declaration, and an implementation that dropped the tail's entropy would be
making no approximation at all -- which is why the plan's dropped-sector
machinery is "not needed by decoy under direct reconciliation" and why OT5's
O^D equals O.

WHAT IT DOES NOT SAY. The flag sector is NOT removable from the program: its
mass enters P_chat and its blocks remain optimisation variables
(meat-core/prop:retention; the plan's section 2.8 item 2). Deleting a flag
sector, or dropping its weight from P_chat, is unsound and is a different
statement from its deficit being zero. At DECOY-TOY the tail carries
g_tail = 0.029024962009... of the sifted generation mass -- about 44 per cent
of P_gen -- so the difference between "no deficit" and "no mass" is the whole
key rate.

THE FOIL: REVERSE RECONCILIATION. With r(x, v) = bit(v) the key value inside a
flag sector is Bob's outcome and is NOT constant, so pi is not a point mass and
the deficit is strictly negative in general. The entry is scoped to direct
reconciliation for exactly that reason, and the plan's section 2.4 names
reverse reconciliation as the first use of the dropped-sector tool.

THE SAME ARGUMENT COVERS THE POLARISATION FLAGS f_{n,a} for
N_ent < n <= N_src, where the block is again non-zero at one polarisation only;
that is what D-3's witness uses at N_ent = 0.""",
    hypotheses=(
        "Direct reconciliation, r(x, v) = bit(a_x). FALSE under reverse "
        "reconciliation.",
        "A flag sector in the sense of def:tagged-source (T3): a tail flag "
        "f_{a,mu} or a polarisation flag f_{n,a}, whose declared blocks are "
        "non-zero at one polarisation only. A flag family finer or coarser "
        "than (T3) is refused (cor:emitted-decoy (vi)).",
        "The vacuum sector is NOT a flag sector: every label weights it, so "
        "its pi is uniform and its deficit is the full binary one (OT1).",
        "Identically in omega and in alpha: an exact test at every feasible "
        "point.",
    ),
    observable=(
        "The objective code's deficit on every flag sector, at several random "
        "feasible points and every alpha of the grid: exactly 0.0, not merely "
        "small. And the key-inert predicate's verdict on those joint pairs: "
        "true. Plan item P3 makes skipping them an identity, so both paths "
        "must agree."
    ),
    value=F(0),
    value_closed_form="f = -(1 - sum_z pi(z)^alpha) tr G with pi a point mass: 0",
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (meat-core 1.1.0). THE
IDENTITY STANDS, exactly zero, and every piece of it is now a claim.

THE ZERO IS lem:rank-one-sector (iv)'s LAST SENTENCE: "If the key is constant
on every X_kappa intersected with {x : mu_x > 0} then eta_kappa = 0 and
f_{hat c,(t,s)} vanishes on these blocks." The restriction to mu_x > 0 is this
entry's "non-zero at one polarisation only", and lem:ensemble-form (iii) makes
that predicate a comparison of a DECLARED block with zero: M^{(t)}_x = 0 iff
N^{(t)}_x = 0.
KEY-INERTNESS PER JOINT SECTOR IS NOW ITS OWN DEFINITION. This entry wrote
"key-inert in the sense of def:keyinert read on the joint sector"; the accepted
id for that reading is def:joint-sectors, whose eq:joint-effective restricts the
outcome set to the pairs with M^{(t)}_x /= 0 and F^{(s)}_v /= 0 and which
records that at |T| = 1 the two definitions coincide. Both are pinned.
THE BOUND-VERSUS-IDENTITY POINT IS prop:drop-bound (iv): "if every pair of D is
key-inert then K^D = K and O^D = O identically". That is this entry's reason
for OT5's tightness, in the claim's words.
WHAT STILL MAY NOT BE DONE. def:dropped's "What is not changed" paragraph
states that a dropped sector's block remains a variable and enters every
P_{hat c} with its full weight -- this entry's warning, now normative.""",
)


O_DECOY_OT3_RANK_ONE_PRODUCT = DecoyOracleEntry(
    oracle_id="O-DECOY-OT3-RANK-ONE-PRODUCT",
    claims=(
        "meat-core/def:feasible",
        "meat-core/lem:choi-marginal",
        "meat-core/thm:reduction",
        "meat-core/lem:rank-one-sector",
        "meat-core/prop:a-neutral",
        "transmitter/decoy/prop:decoy-cert",
        "transmitter/lem:matched-pinching",
        "transmitter/lem:ensemble-presentation",
    ),
    kind="structural-identity",
    subject=(
        "OT3: at every feasible point the vacuum block and every flag block "
        "FACTORISE, omega_{ts} = tau^{(t)}_A (x) sigma_s, because a positive "
        "operator with a rank-one marginal is a product. Frozen with an exact "
        "rational witness and a rank-two FOIL."
    ),
    instance="DECOY-TOY",
    derivation="""\
THE STATEMENT AND ITS PROOF, which is three lines of linear algebra and needs
no channel, no attack and no honest model. Let omega >= 0 on A (x) Q with
tr_Q omega = p |v><v|, p > 0. For any |u> orthogonal to |v>:
  tr[(|u><u| (x) 1) omega] = <u| tr_Q omega |u> = 0 ,
and (|u><u| (x) 1) omega (|u><u| (x) 1) is positive with trace zero, hence
zero. So the support of omega lies in |v> (x) Q: writing omega in a basis whose
first A-vector is |v>, the diagonal blocks off |v> vanish, and positivity of
the 2x2 compressions forces the off-diagonal blocks to vanish too. Therefore
  omega = |v><v| (x) sigma ,  sigma >= 0 ,  tr sigma = p .
"ALL LABELS SHARE ONE OUTPUT STATE" IS FORCED BY THE MARGINAL AND IS NOT
IMPOSED, which is the sentence derivations/06 section 6.2 makes and the reason
the vacuum needs no constraint of its own.

WHERE THE RANK-ONE MARGINALS COME FROM. prop:decoy-cert (iii):
r_t = dim span{|phi_{x,t}> : x in X_t}, which is 1 on the vacuum sector (all
labels share |vac>), 1 on every polarisation flag and 1 on every tail flag. It
is NOT 1 on a quantum sector with two or more polarisations -- there r_n can be
2, 3 or 4 -- so the factorisation is a statement about exactly those sectors
whose marginal the declaration makes rank one.

THE WITNESS, on the smallest space where the statement has content: A and Q
qubits, tau_A = |0><0| of weight 1, the index order A OUTER. Then every
positive omega with that marginal is |0><0| (x) sigma, and OT3_WITNESS_STATE is
one such, with sigma = [[1/2, 1/4], [1/4, 1/2]] in the top-left block -- note
that sigma itself is NOT diagonal and NOT pure, so the factorisation
constrains A's side only.

THE FOIL, because one row is not evidence. OT3_FOIL_MARGINAL is the rank-TWO
marginal diag(1/2, 1/2) and OT3_FOIL_STATE is
(|00><00| + |11><11|)/2 >= 0, which has that marginal and IS NOT A PRODUCT: no
sigma satisfies |v><v| (x) sigma = OT3_FOIL_STATE for any |v>. So the
implication really is about the rank of the marginal, and an implementation
that asserted factorisation from block diagonality alone would be wrong here.
THIS IS THE SAME ERROR THE PLAN'S SECTION 2.8 ITEM 1 FORBIDS in the other
direction: block diagonality of tau_A never implies block diagonality of omega.

WHAT THE ENTRY IS FOR. A returned point whose vacuum or flag block does not
factorise is INFEASIBLE -- the check is exact, cheap and independent of alpha --
and a solver that emits one has violated the marginal constraint, not merely
converged loosely. Beside it, the factorisation is what makes OT1's and OT2's
closed forms available at all, since both are stated on omega_{ts} = tau (x)
sigma.""",
    hypotheses=(
        "omega >= 0 with tr_Q omega = p |v><v| of rank one and p > 0. At p = 0 "
        "the block is zero and the statement is vacuous.",
        "Trusted-source mode, where the marginal condition omega_A = tau_A is "
        "part of the feasible set (meat-core/def:feasible). In untrusted mode "
        "there is no marginal and nothing here applies.",
        "The marginal is the one the ensemble presentation DEFINES, the "
        "transpose of the declared sum; a compressed or snapped marginal would "
        "not have exactly rank one and the argument would fail.",
        "Exact statement at every feasible point; no honest model, no attack "
        "and no alpha enter.",
    ),
    observable=(
        "For each rank-one Alice sector of a returned point: the block's "
        "distance from tau^{(t)}_A (x) (its Q-marginal / p_t), asserted below "
        "the run's declared tolerance; and the exact witness/foil pair "
        "reproduced by whatever routine the code uses to decide factorisation."
    ),
    value=F(0),
    value_closed_form=(
        "omega_{ts} - tau^{(t)}_A (x) sigma_s = 0 exactly on a rank-one sector"
    ),
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (meat-core 1.1.0). THE
STATEMENT, THE WITNESS AND THE FOIL STAND.

THIS ENTRY'S STATEMENT IS lem:rank-one-sector (i), and its proof is the one
frozen here: Pi^perp = 1 - |v><v| gives tr[(Pi^perp (x) 1) omega_t] = 0, and a
positive semidefinite operator with that trace has (Pi^perp (x) 1) omega_t = 0,
whence omega_t = |v><v| (x) sigma with sigma >= 0 and tr sigma = p_t. The claim
states it for every list of blocks with the right marginal sum, "in particular
the sector-t part of every omega in Feas", which is what the entry needs.
THE FOIL IS STILL NECESSARY AND IS STILL NOT IN ANY CLAIM: the accepted text
states the implication and not its failure at rank two. The frozen pair is what
makes "the rank of the marginal is what does it" falsifiable.
prop:a-neutral IS PINNED FOR THE CONTEXT AND NOT FOR THE ALGEBRA: it is what
licenses minimising over Alice-block-diagonal lists at all, in either source
mode and with `general` and `party_local` entries included, so that "every
feasible point" in this entry's statement is the right set.""",
)


O_DECOY_OT4_ONE_PHOTON_BELL = DecoyOracleEntry(
    oracle_id="O-DECOY-OT4-ONE-PHOTON-BELL",
    claims=(
        "meat-core/thm:branch-formula",
        "meat-core/def:branch",
        "foundations/def:pinching",
        "foundations/def:renyi",
        "meat-core/def:joint-sectors",
        "meat-core/prop:a-neutral",
        "meat-core/lem:ensemble-form",
        "transmitter/lem:ensemble-presentation",
        "transmitter/decoy/prop:decoy-cert",
    ),
    kind="toy-instance",
    subject=(
        "OT4: the one-photon sector's bits per sifted round at a Bell-diagonal "
        "point, h_1 = 1 - (alpha-1)^{-1} log2 sum_i "
        "(lambda_{i0}^{1/alpha} + lambda_{i1}^{1/alpha})^alpha, with its three "
        "exact checks and its exact value at alpha = 2."
    ),
    instance="DECOY-TOY",
    derivation="""\
THE CLOSED FORM. Let the one-photon-to-one-photon part of the Choi block be
2 eta rho with rho = sum_{ij} lambda_{ij} |Phi_{ij}><Phi_{ij}| Bell-diagonal,
|Phi_{ij}> = (1 (x) X^i Z^j)|Phi^+>, i the BIT-ERROR index and j the PHASE
index, and let the receiver's Z-basis effects on the one-photon block have
weight q_Z. Then for the generation pass class
  T / tr G = 2^{1-alpha} S ,
  S = sum_{i in {0,1}} (lambda_{i0}^{1/alpha} + lambda_{i1}^{1/alpha})^alpha ,
  h_1 = 1 - log2 S / (alpha - 1) ,
h_1 being defined by T / tr G = 2^{(1-alpha) h_1}, which is the sector's bits
per sifted round in the sense of meat-core/thm:branch-formula.

THE DERIVATION, in the two steps derivations/06 takes. (1) By the ensemble
presentation the objective reads Alice's side only through
N^{(1)}_x = (sigma^{v,(1)}_x)^T = p_x p~(1|mu) (|1,a><1,a|)^T, so the branch
operator is isometric to w q_Z eta 2 rho with R a copy of ALICE'S BIT and no
square root formed anywhere. (2) The pinching Z on R dephases A in the Z basis,
which maps |Phi_{ij}><Phi_{ij}| to
(1/2)(|Phi_{i0}><Phi_{i0}| + |Phi_{i1}><Phi_{i1}|): the bit index survives, the
phase index is averaged. Collecting the two bit blocks and taking the
alpha-th power of the pinched 1/alpha-power gives the sum S, each bit block
contributing (sum_j lambda_{ij}^{1/alpha})^alpha and the factor 2^{1-alpha}
coming from the two equally weighted rows of each block.

THE THREE CHECKS, ALL EXACT, AND THEY ARE WHY THIS IS AN ORACLE AND NOT A
FORMULA.
  (a) lambda = (1, 0, 0, 0): S = 1, so h_1 = 1 EXACTLY at every alpha -- a
      noiseless one-photon channel gives a full bit, which is the T1 mechanism
      of tests/support/bb84_targets.py.
  (b) lambda = (1/4, 1/4, 1/4, 1/4): each bit block gives
      (2 (1/4)^{1/alpha})^alpha = 2^alpha / 4, so S = 2^alpha / 2 = 2^{alpha-1}
      and h_1 = 1 - (alpha-1)/(alpha-1) = 0 EXACTLY -- a maximally mixed block
      gives no key.
  (c) alpha -> 1+: h_1 -> 1 - H(phase | bit), the conditional Shannon entropy
      of the phase index given the bit index under lambda. At DECOY-TOY's
      lambda = (13/16, 1/16, 1/16, 1/16) the bit distribution is (7/8, 1/8) and
      the conditional phase distributions are (13/14, 1/14) and (1/2, 1/2), so
      H(phase | bit) = (7/8) h2(1/14) + 1/8 = 0.4498282858107662 and the limit
      is 0.5501717141892338. The frozen grid approaches it from below.

THE EXACT VALUE AT alpha = 2, which a reader can redo with a square root and
nothing else. At alpha = 2, beta = 1/2 and
lambda = (13/16, 1/16, 1/16, 1/16):
  bit block i = 0 : (sqrt(13)/4 + 1/4)^2 = (14 + 2 sqrt 13)/16 ,
  bit block i = 1 : (2 * (1/4))^2 = 1/4 = 4/16 ,
  S = (18 + 2 sqrt 13)/16 = (9 + sqrt 13)/8 ,
  h_1 = 1 - log2((9 + sqrt 13)/8) = 0.3440126925102356 .

THE CROSS-CHECK, RECORDED AND NOT USED AS THE DERIVATION. With
lambda_10 = lambda_11 = 0 the formula collapses to
h_1 = 1 - (alpha/(alpha-1)) log2(lambda_00^{1/alpha} + lambda_01^{1/alpha}),
which is exactly 1 - renyi_pair_entropy(t, alpha) of
tests/support/bb84_targets.py at t = lambda_01, and the whole one-photon sector
becomes that file's reduced_objective_singleton key term. The agreement is
evidence that the qubit mathematics is the one-Alice-sector case of this one --
the plan's section 2.3 parity requirement -- and it is recorded as a
cross-check, the derivation above being the authority.""",
    hypotheses=(
        "Direct reconciliation with R a copy of ALICE'S bit; the pinching is "
        "then the Z-dephasing of A, which is what averages the phase index.",
        "A Bell-diagonal one-photon block, in the index order (bit, phase) = "
        "(Phi+, Phi-, Psi+, Psi-). At a non-Bell-diagonal point the formula "
        "does not apply and no number here does.",
        "Ideal Z-basis effects of weight q_Z on the one-photon receiver block, "
        "and one generation pass class. The weights w, q_Z and eta scale tr G "
        "and cancel from h_1 entirely, which is why h_1 is a per-round figure.",
        "h_1 is BITS PER SIFTED ROUND OF THIS SECTOR: the sector's "
        "contribution to the objective is -(1 - 2^{(1-alpha) h_1}) tr G, and "
        "tr G carries the sifting.",
        "alpha in (1, inf). The alpha -> 1+ value is a limit and not an "
        "evaluation.",
    ),
    observable=(
        "The objective code's one-photon sector deficit at the honest "
        "Bell-diagonal point, converted to bits by "
        "h = log2(1 + f / tr G) / (1 - alpha), against "
        "bell_diagonal_bits(lambda, alpha) on the frozen grid; and the three "
        "checks (a), (b), (c) at the same code path."
    ),
    closed_form=lambda alpha: bell_diagonal_bits(
        (13 / 16, 1 / 16, 1 / 16, 1 / 16), alpha
    ),
    frozen_values=(
        (1.05, 0.5358722773415907),
        (1.25, 0.4832727593201477),
        (1.5, 0.4276563963169059),
        (1.75, 0.3818587862964439),
        (1.9, 0.3583099172823756),
    ),
    value=0.3440126925102356,
    value_closed_form="h_1(alpha = 2) = 1 - log2((9 + sqrt 13)/8)",
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (meat-core 1.1.0). THE CLOSED
FORM, THE TABLE, THE THREE CHECKS AND THE alpha = 2 VALUE STAND.

WHAT THE ACCEPTED CLAIMS DO NOT COVER, AND THIS IS THE SCOPING CHECK THE RE-PIN OWED.
lem:rank-one-sector is NOT pinned here and must not be: its hypothesis is
tau^{(t)}_A = p_t |v><v| of RANK ONE, and the one-photon sector of DECOY-TOY has
tau^{(1)}_A = (1/8) 1_2, of rank TWO. That is exactly why this sector is the one
that costs a matrix function while thirty-odd others do not (the plan's item
P6), and why OT4 needed its own derivation. An implementation that routed the
one-photon sector through the rank-one closed form would be wrong here, and the
frozen table is what catches it.
WHAT IS PINNED AND WHY. def:joint-sectors gives the joint-sector deficit
f_{hat c,(t,s)} this entry computes, with the Kraus operators acting through
sqrt(M^{(t)}_x) (x) sqrt(F^{(s)}_v); prop:a-neutral licenses the per-Alice-
sector reading; lem:ensemble-form (ii) is the identity behind "the objective
reads Alice's side only through N^{(1)}_x", with N_x = tau^{1/2} M_x tau^{1/2}.
THE CROSS-CHECK AGAINST tests/support/bb84_targets.py IS UNCHANGED and is still
recorded as a cross-check, the derivation being the authority.""",
)


O_DECOY_OT5_DROPPED_HONEST = DecoyOracleEntry(
    oracle_id="O-DECOY-OT5-DROPPED-HONEST",
    claims=(
        "meat-core/thm:branch-formula",
        "meat-core/def:feasible",
        "meat-core/def:keyinert",
        "meat-core/def:joint-sectors",
        "meat-core/def:dropped",
        "meat-core/prop:drop-bound",
        "meat-core/cor:drop-program",
        "meat-core/lem:rank-one-sector",
        "meat-core/prop:exact-cancellation",
        "meat-core/prop:retention",
        "transmitter/decoy/cor:emitted-decoy",
    ),
    kind="toy-instance",
    subject=(
        "OT5: the dropped objective at an honest point of DECOY-TOY, "
        "O^D = (P_gen/(alpha-1)) log2(P_gen/K^D_gen) with K^D_gen = P_gen "
        "- (1-2^{1-alpha}) g_0 - (1-2^{(1-alpha)h_1}) g_1; every number in it "
        "comes from the honest model by hand, and here O^D = O exactly."
    ),
    instance="DECOY-TOY",
    derivation="""\
THE ASSEMBLY RULE, one line, which is what makes the whole entry hand-checkable.
By thm:branch-formula's sector form K_chat = P_chat + sum_s f_{chat,s}, and by OT1, OT2 and
OT4 every sector's deficit has the same shape
  f_t = -(1 - 2^{(1-alpha) h_t}) tr G_t ,
with h_t the sector's bits per sifted round: h_0 = 1 (OT1, equal key weights),
h_tail = 0 (OT2), h_1 from OT4. So
  K_gen = P_gen - sum_t (1 - 2^{(1-alpha) h_t}) g_t ,
  O_alpha = (P_gen/(alpha-1)) log2(P_gen / K_gen) ,
the second because at q = Phi[omega] every divergence term of
Eq. eq:objective vanishes and only the key term remains.

THE DROPPED SET, AND WHY DROPPING COSTS NOTHING HERE. Take D to be every
(acceptance value, joint sector) pair on a tail flag. Replacing their deficits
by zero gives the plan's
  K^D_gen = P_gen - (1 - 2^{1-alpha}) g_0 - (1 - 2^{(1-alpha) h_1}) g_1 ,
and by OT2 those deficits WERE zero, so K^D = K and O^D = O EXACTLY. The
dropped bound is therefore tight on this declaration -- "equality on key-inert
pairs" -- and the plan's own remark that the dropped set is "not needed by
decoy under direct reconciliation" is this identity. The entry freezes the
dropped form anyway, because it is the form the plan's claim will be stated in
and because the equality is the falsifiable content: an implementation whose
dropped objective differs from its undropped one on this instance has a defect
in one of the two.

THE NUMBERS, from DECOY-TOY's honest model and nothing else.
  g_0 = 1/256 = 0.00390625 , g_1 = 67/2048 = 0.03271484375 ,
  g_tail = 949/2048 - (63/128) e^{-1/8} = 0.029024962009144450 ,
  P_gen = 1/2 - (63/128) e^{-1/8} = 0.065646055759144450 ,
  lambda = (13/16, 1/16, 1/16, 1/16) , h_1 from OT4 .
AT alpha = 2 EVERYTHING IS A CLOSED FORM IN TWO IRRATIONALS, e^{-1/8} and
sqrt 13, and the two subtracted terms are rational:
  2^{1-alpha} = 1/2 ,  S = (9 + sqrt 13)/8 ,  2^{(1-alpha) h_1} = S/2 ,
  (1 - 2^{1-alpha}) g_0 = (1/2)(1/256) = 1/512 = 0.001953125 ,
  (1 - S/2) g_1 = ((7 - sqrt 13)/16)(67/2048) = 67(7 - sqrt 13)/32768
                = 0.0069405537275363995 ,
  K^D(2) = [1/2 - (63/128) e^{-1/8}] - 1/512 - 67(7 - sqrt 13)/32768
         = 0.05675237703160805 ,
  O^D(2) = P_gen log2(P_gen / K^D(2)) = 0.013787477747325156 .
The whole grid is in ``frozen_values``.

THE alpha -> 1+ LIMIT, WHICH IS THE ONE NUMBER MOST EASILY GOT WRONG.
1 - 2^{(1-alpha)h} ~ (alpha-1) h ln 2, so the key term tends to
sum_t g_t h_t:
  lim O^D = g_0 * 1 + g_1 * (1 - H(phase|bit)) + g_tail * 0
          = 1/256 + (67/2048)(0.5501717141892338)
          = 0.02190503166537044 ,
with h_1's limit taken AT THE HONEST lambda and NOT at 1 - h2(e_1). The second
would be 0.018838467922669452, which is D-4's ceiling and a DIFFERENT quantity:
that number is the value at the worst state with the same statistics, this one
the value at the honest state. The honest-point value is LARGER, as it must be
-- the objective at a feasible point bounds h_low from above -- and a test that
compared a solver's limit against this entry's number would be comparing
against the wrong one. Both numbers are frozen, here and in D-4, so the
confusion cannot survive.

WHAT THIS ENTRY IS NOT. It is not h_low: it is O at one named feasible point,
hence an upper bound. The dropped sectors remain optimisation variables and
their mass remains in P_gen (prop:retention); nothing here licenses deleting
them.""",
    hypotheses=(
        "DECOY-TOY's honest model exactly, including the FORCED tail-flag "
        "yield of D-5. With a free or two-photon tail yield every number here "
        "moves.",
        "Direct reconciliation, convention A, N_ent = N_src = 1, one "
        "generation pass class, equal weights of the two generation labels.",
        "The dropped set is every pair on a tail flag; by OT2 the dropped "
        "bound is an EQUALITY here, so the entry pins both O^D and O.",
        "The value is the objective AT A FEASIBLE POINT and bounds h_low from "
        "ABOVE. It is not h_low and must never be compared against one as an "
        "equality.",
        "The alpha -> 1+ limit uses h_1 at the honest lambda, not 1 - h2(e_1).",
    ),
    observable=(
        "The engine's objective (dropped and undropped) at the named honest "
        "point of the decoy declaration, against dropped_objective(alpha) on "
        "the frozen grid, with no solver involved -- the point is given, not "
        "found; and h_low <= that value at each alpha, with its gap."
    ),
    closed_form=dropped_objective,
    frozen_values=(
        (1.05, 0.02132815264614859),
        (1.25, 0.019232873362655774),
        (1.5, 0.017049290011703758),
        (1.75, 0.015263158136482867),
        (1.9, 0.0143453381606012),
    ),
    value=0.02190503166537044,
    value_closed_form=(
        "lim_{alpha -> 1+} O^D = g_0 + g_1 (1 - H(phase|bit)) = "
        "1/256 + (67/2048)(1 - (7/8) h2(1/14) - 1/8)"
    ),
    revalidation="""\
RE-READ AGAINST THE ACCEPTED CLAIMS (meat-core 1.1.0). EVERY
NUMBER OF THE TABLE, THE alpha = 2 CLOSED FORM AND THE LIMIT STAND.

THE DROPPED PROGRAM IS NOW DEFINED AS THIS ENTRY USES IT. def:dropped's
eq:KD is K^D_{hat c} = P_{hat c} + sum over the UNDROPPED pairs of
f_{hat c,(t,s)}, over pairs of a key-live acceptance value and a JOINT sector,
which is the frozen expression. prop:drop-bound (i)-(iii) give the ordering and
the non-negativity, and (iv) gives what this entry turns on: dropping
key-inert pairs is an IDENTITY, so O^D = O here and the two must agree in any
implementation. cor:drop-program (i)-(ii) add the concavity and convexity the
solver needs and change no value.
THE ASSEMBLY RULE IS TWO CLAIMS, NOT ONE. The vacuum term is
lem:rank-one-sector (iii)-(iv) at d = 2, the tail term is its zero case
(OT2), and the ONE-PHOTON term is not covered by it -- rank two -- and remains
this file's own derivation (OT4). The frozen K^D therefore rests on
lem:rank-one-sector for two of its three sectors and on OT4 for the third,
which is worth stating because an implementation may reach the same number by
routing all three through one code path.
THE TWO NUMBERS THAT MUST NOT BE CONFUSED ARE UNCHANGED, and the accepted claims supply no
reason to prefer either: 0.02190503166537044 is the honest point's limit, and
D-4's 0.018838467922669452 is the witness point's. Both stand.""",
)


DECOY_ORACLES: tuple[DecoyOracleEntry, ...] = (
    O_DECOY_D1_QUBIT_LIMIT,
    O_DECOY_D2_VACUUM_BIT,
    O_DECOY_D3_CUTOFF_MONOTONE,
    O_DECOY_D4_INFINITE_DECOY_CEILING,
    O_DECOY_D5_STATISTICS,
    O_DECOY_OT1_VACUUM_DEFICIT,
    O_DECOY_OT2_FLAG_KEY_INERT,
    O_DECOY_OT3_RANK_ONE_PRODUCT,
    O_DECOY_OT4_ONE_PHOTON_BELL,
    O_DECOY_OT5_DROPPED_HONEST,
)


def decoy_oracle(oracle_id: str) -> DecoyOracleEntry:
    """Return the entry with this id, refusing an unknown one.

    Refusing is the point: a silent ``None`` would let a test assert nothing
    while looking like it asserted something.
    """
    for entry in DECOY_ORACLES:
        if entry.oracle_id == oracle_id:
            return entry
    raise KeyError(f"no decoy oracle entry with id {oracle_id!r}")
