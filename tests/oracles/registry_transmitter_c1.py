"""The hand-derived registry of the transmitter ensemble and decoy cases.

WHAT THIS FILE IS. Every number below was derived BY HAND from the claim files of
transmitter 0.2.0 and transmitter/decoy 0.1.0 -- ``def:srcert``'s block form and
ensemble presentation, ``lem:ensemble-presentation``, ``def:tagged-source`` and
``cor:emitted-decoy`` -- and NOT read off the implementation. An oracle registry
"moves with its module and is NEVER REGENERATED FROM THE CODE IT TESTS"
(PRINCIPLES.md section 2.3), so the derivations are written out beside the values
and a reader can redo each of them with a pencil.

WHY A NEW FILE RATHER THAN A SECTION IN ``registry_transmitter.py``. That file is
the transmitter's half of the frozen protocol-compiler registry, and
``test_protocol_compiler_registry_partition.py`` asserts that the union of the
three halves is the original ``__all__`` plus exactly the accessors the
split created. Adding a name there would break that check, and the check is
right: it is what makes the cut of that registry unable to lose or invent a value.
These derivations are new evidence for new claims, so they get a file of their
own.

THE FOUR GROUPS, and each is one claim's executable memory:

* ``PRESENTATION_CASES`` -- ``lem:ensemble-presentation`` (iii) and (v) on the
  ACCEPTED qubit BB84 ensemble, which is the degenerate case the design rule is
  about;
* ``BLOCK_CERTIFICATE_CASES`` -- ``def:srcert``'s block form and Eq.
  ``eq:srblock`` on the smallest two-sector certificate that is not pure as a
  whole;
* ``DECOY_CASES`` -- ``def:tagged-source`` (T2), (T3), (T4) and
  ``cor:emitted-decoy`` (i), (iv) on one tagged declaration;
* ``TAGGING_REGISTRY_TRIPLE`` -- ``def:source-segment`` (A1) and
  ``cor:emitted-decoy`` (ii): the one entry of the closed soundness registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

__all__ = [
    "BLOCK_CERTIFICATE_CASES",
    "DECOY_CASES",
    "PRESENTATION_CASES",
    "TAGGING_REGISTRY_TRIPLE",
    "BlockCertificateCase",
    "DecoyCase",
    "PresentationCase",
]

#: A matrix of exact rationals, as a tuple of tuples. The registry writes REAL
#: entries only: every declared block of the worked cases is real, and a
#: complex entry would have to be derived as such rather than written as one.
Rational = F
RealMatrix = tuple[tuple[F, ...], ...]


# ===========================================================================
#  Group TX-C1-A -- the ensemble presentation of the accepted qubit ensemble
# ===========================================================================


@dataclass(frozen=True)
class PresentationCase:
    """One ensemble presentation, with ``tau_A`` and ``{N_x}`` derived by hand."""

    case_id: str
    #: ``(sector label, dim S_t)`` in the declared order.
    sectors: tuple[tuple[str, int], ...]
    #: The declared weights, aligned with :attr:`alphabet`.
    alphabet: tuple[str, ...]
    weights: tuple[F, ...]
    #: ``sigma^{v,(t)}_x`` per letter, per sector, in the two declared orders.
    weighted_blocks: tuple[tuple[RealMatrix, ...], ...]
    #: ``tau^{(t)}_A`` of Eq. ``eq:enspres``, per sector.
    alice_marginal_blocks: tuple[RealMatrix, ...]
    #: ``N^{(t)}_x`` of ``lem:ensemble-presentation`` (v), per letter, per sector.
    alice_operators: tuple[tuple[RealMatrix, ...], ...]
    #: ``d_A = sum_t dim S_t``, which is DEFINED and not declared.
    alice_dim: int
    derivation: str


_HALF = F(1, 2)
_QUARTER = F(1, 4)
_EIGHTH = F(1, 8)

PRESENTATION_CASES: tuple[PresentationCase, ...] = (
    PresentationCase(
        case_id="PRES-bb84-qubit-degenerate",
        sectors=(("A", 2),),
        alphabet=("(Z,0)", "(Z,1)", "(X,0)", "(X,1)"),
        weights=(_QUARTER, _QUARTER, _QUARTER, _QUARTER),
        weighted_blocks=(
            (((_QUARTER, F(0)), (F(0), F(0))),),
            (((F(0), F(0)), (F(0), _QUARTER)),),
            (((_EIGHTH, _EIGHTH), (_EIGHTH, _EIGHTH)),),
            (((_EIGHTH, -_EIGHTH), (-_EIGHTH, _EIGHTH)),),
        ),
        alice_marginal_blocks=(((_HALF, F(0)), (F(0), _HALF)),),
        alice_operators=(
            (((_QUARTER, F(0)), (F(0), F(0))),),
            (((F(0), F(0)), (F(0), _QUARTER)),),
            (((_EIGHTH, _EIGHTH), (_EIGHTH, _EIGHTH)),),
            (((_EIGHTH, -_EIGHTH), (-_EIGHTH, _EIGHTH)),),
        ),
        alice_dim=2,
        derivation=(
            "The ACCEPTED qubit BB84 declaration of instances/bb84, re-declared "
            "as an ensemble presentation with the one-sector structure. Its "
            "specified ensemble is p_x = 1/4 at each of the four letters with "
            "rho_(Z,0) = |0><0|, rho_(Z,1) = |1><1| and rho_(X,b) the two "
            "conjugate-basis projectors (1/2)[[1, +/-1], [+/-1, 1]], so the "
            "weighted members sigma_x = p_x rho_x are the four blocks above -- "
            "1/4 on a diagonal entry for the Z letters, 1/8 on every entry for "
            "the X letters. "
            "tau_A: eq:enspres puts tau_A = (sum_x sigma_x)^T. The sum is "
            "(1/4)(|0><0| + |1><1|) + (1/8)([[1,1],[1,1]] + [[1,-1],[-1,1]]) = "
            "(1/4) 1_2 + (1/8)[[2,0],[0,2]] = (1/4) 1_2 + (1/4) 1_2 = 1_2/2, "
            "which is symmetric, so its transpose is itself: tau_A = 1_A/2, "
            "WHICH IS THE MARGINAL THE ACCEPTED INSTANCE DECLARES. "
            "N_x: part (v) gives N_x = sigma_x^T, and every block here is "
            "symmetric, so N_x = sigma_x entry for entry. The identity part (v) "
            "asserts is N_x = tau_A^(1/2) M_x tau_A^(1/2); with tau_A = 1_A/2 "
            "the right-hand side is M_x/2, and the instance's "
            "M_(b,a) = p^A_b |conj(a^b)><conj(a^b)| at p^A_Z = p^A_X = 1/2 is "
            "half the corresponding real projector, so M_x/2 is a quarter of it "
            "-- which is sigma_x. The conjugation is invisible here because "
            "every BB84 amplitude is real; the transpose in part (v) is not, and "
            "the identity is asserted with it."
        ),
    ),
)


# ===========================================================================
#  Group TX-C1-B -- the block form and Eq. eq:srblock
# ===========================================================================


@dataclass(frozen=True)
class BlockCertificateCase:
    """One block-form certificate, with the two identities' values per sector."""

    case_id: str
    sectors: tuple[tuple[str, int, int], ...]
    alphabet: tuple[str, ...]
    #: ``Psi_t`` on ``A_t S_t``, per sector.
    psi_blocks: tuple[RealMatrix, ...]
    #: ``tr Psi_t`` per sector, and the total, which (SR)'s trace condition reads.
    block_traces: tuple[F, ...]
    total_trace: F
    #: ``tr_{S_t} Psi_t`` per sector: the left-hand side of (SR1).
    sr1_computed: tuple[RealMatrix, ...]
    #: ``M^{(t)}_x`` per letter, per sector.
    povm_blocks: tuple[tuple[RealMatrix, ...], ...]
    #: ``tr_{A_t}[(M^{(t)}_x (x) 1) Psi_t]`` per letter, per sector: (SR2)'s
    #: left-hand side, which the declared ``sigma^{v,(t)}_x`` must equal.
    sr2_computed: tuple[tuple[RealMatrix, ...], ...]
    weights: tuple[F, ...]
    derivation: str


BLOCK_CERTIFICATE_CASES: tuple[BlockCertificateCase, ...] = (
    BlockCertificateCase(
        case_id="BLOCK-qubit-and-flag-half-and-half",
        sectors=(("q", 2, 2), ("flag", 1, 1)),
        alphabet=("x0", "x1"),
        psi_blocks=(
            (
                (_QUARTER, F(0), F(0), _QUARTER),
                (F(0), F(0), F(0), F(0)),
                (F(0), F(0), F(0), F(0)),
                (_QUARTER, F(0), F(0), _QUARTER),
            ),
            ((_HALF,),),
        ),
        block_traces=(_HALF, _HALF),
        total_trace=F(1),
        sr1_computed=(((_QUARTER, F(0)), (F(0), _QUARTER)), ((_HALF,),)),
        povm_blocks=(
            (((F(1), F(0)), (F(0), F(0))), ((_HALF,),)),
            (((F(0), F(0)), (F(0), F(1))), ((_HALF,),)),
        ),
        sr2_computed=(
            (((_QUARTER, F(0)), (F(0), F(0))), ((_QUARTER,),)),
            (((F(0), F(0)), (F(0), _QUARTER)), ((_QUARTER,),)),
        ),
        weights=(_HALF, _HALF),
        derivation=(
            "TWO SECTORS OF WEIGHT ONE HALF EACH, which is the smallest case in "
            "which the whole Psi is NOT pure: def:srcert's block form denotes "
            "the direct sum, and 'it is the state of the source that first draws "
            "t with probability tr Psi_t and then prepares Psi_t / tr Psi_t'. "
            "Psi_q = (1/2)|Phi+><Phi+| on A_q S_q = C^2 (x) C^2: the operator "
            "|Phi+><Phi+| has the entry 1/2 at the four corners (0,0), (0,3), "
            "(3,0), (3,3) and zero elsewhere, so half of it has 1/4 there. "
            "Psi_flag = [1/2] on a one-dimensional joint sector. "
            "TRACES: tr Psi_q = 1/4 + 0 + 0 + 1/4 = 1/2 and tr Psi_flag = 1/2, "
            "so sum_t tr Psi_t = 1, and both additions are exact. NO PURITY "
            "CONDITION IS READ: Psi_q^2 = Psi_q/2 != Psi_q, and the form carries "
            "no idempotence condition. "
            "(SR1): tr_{S_q} (1/2)|Phi+><Phi+| = (1/2)(1_2/2) = (1/4) 1_2, the "
            "maximally entangled operator having the maximally mixed marginal; "
            "tr_{S_flag} [1/2] = [1/2]. "
            "(SR2): for the maximally entangled operator, "
            "tr_A[(M (x) 1)|Phi+><Phi+|] = M^T/2, so with the extra factor one "
            "half the q-sector value is M^T/4. With M^(q)_x0 = |0><0| and "
            "M^(q)_x1 = |1><1| -- real and diagonal, hence their own transposes "
            "-- the values are |0><0|/4 and |1><1|/4. On the one-dimensional "
            "flag sector (SR2) reads m_x tr Psi_flag = m_x/2, and m_x = 1/2 at "
            "both letters gives 1/4 at both. "
            "WEIGHTS: p_x = sum_t tr sigma^{v,(t)}_x = 1/4 + 1/4 = 1/2 at each "
            "of the two letters, and the POVM condition holds per block: "
            "|0><0| + |1><1| = 1_2 on q and 1/2 + 1/2 = 1 on the flag."
        ),
    ),
)


# ===========================================================================
#  Group TX-C1-C -- the tagged decoy declaration
# ===========================================================================


@dataclass(frozen=True)
class DecoyCase:
    """One tagged declaration, with its index set, tail weights and marginal."""

    case_id: str
    entropy_cutoff: int
    source_cutoff: int
    polarisations: tuple[str, ...]
    #: ``(intensity name, mu)`` in the declared order.
    intensities: tuple[tuple[str, F], ...]
    #: ``ptilde(n | mu)`` keyed by ``(n, intensity)``.
    sector_weights: dict[tuple[int, str], F]
    #: ``wtilde_mu`` of Eq. ``eq:tailweight``, per intensity.
    tail_weights: dict[str, F]
    #: The DECLARED INDEX SET of Eq. ``eq:tset``, in order, with the dimensions.
    sector_index_set: tuple[tuple[str, int], ...]
    #: ``d_A = sum_t dim S_t``.
    alice_dim: int
    #: ``sigma^{v,(t)}_x`` for two chosen letters, keyed by the sector label.
    weighted_blocks: dict[str, dict[str, RealMatrix]]
    #: ``tau^{(t)}_A`` per sector label.
    alice_marginal_blocks: dict[str, RealMatrix]
    derivation: str


_DECOY_WEIGHTS: dict[tuple[int, str], F] = {
    (0, "signal"): _HALF,
    (1, "signal"): _QUARTER,
    (2, "signal"): F(1, 16),
    (0, "decoy"): F(7, 8),
    (1, "decoy"): F(1, 16),
    (2, "decoy"): F(1, 256),
}

DECOY_CASES: tuple[DecoyCase, ...] = (
    DecoyCase(
        case_id="DECOY-four-polarisations-two-intensities-Nent1-Nsrc2",
        entropy_cutoff=1,
        source_cutoff=2,
        polarisations=("H", "V", "+", "-"),
        intensities=(("signal", _HALF), ("decoy", _EIGHTH)),
        sector_weights=dict(_DECOY_WEIGHTS),
        tail_weights={"signal": F(3, 16), "decoy": F(15, 256)},
        sector_index_set=(
            ("n0", 1),
            ("n1", 2),
            ("flag-n2-H", 1),
            ("flag-n2-V", 1),
            ("flag-n2-+", 1),
            ("flag-n2--", 1),
            ("tail-H-signal", 1),
            ("tail-H-decoy", 1),
            ("tail-V-signal", 1),
            ("tail-V-decoy", 1),
            ("tail-+-signal", 1),
            ("tail-+-decoy", 1),
            ("tail---signal", 1),
            ("tail---decoy", 1),
        ),
        alice_dim=15,
        weighted_blocks={
            "H-signal": {
                "n0": ((F(1, 16),),),
                "n1": ((F(1, 32), F(0)), (F(0), F(0))),
                "flag-n2-H": ((F(1, 128),),),
                "flag-n2-V": ((F(0),),),
                "tail-H-signal": ((F(3, 128),),),
                "tail-H-decoy": ((F(0),),),
            },
            "+-decoy": {
                "n0": ((F(7, 64),),),
                "n1": ((F(1, 256), F(1, 256)), (F(1, 256), F(1, 256))),
                "flag-n2-+": ((F(1, 2048),),),
                "flag-n2-H": ((F(0),),),
                "tail-+-decoy": ((F(15, 2048),),),
                "tail-+-signal": ((F(0),),),
            },
        },
        alice_marginal_blocks={
            "n0": ((F(11, 16),),),
            "n1": ((F(5, 64), F(0)), (F(0), F(5, 64))),
            "flag-n2-H": ((F(17, 2048),),),
            "flag-n2-V": ((F(17, 2048),),),
            "flag-n2-+": ((F(17, 2048),),),
            "flag-n2--": ((F(17, 2048),),),
            "tail-H-signal": ((F(3, 128),),),
            "tail-V-signal": ((F(3, 128),),),
            "tail-+-signal": ((F(3, 128),),),
            "tail---signal": ((F(3, 128),),),
            "tail-H-decoy": ((F(15, 2048),),),
            "tail-V-decoy": ((F(15, 2048),),),
            "tail-+-decoy": ((F(15, 2048),),),
            "tail---decoy": ((F(15, 2048),),),
        },
        derivation=(
            "THE DECLARATION. Four polarisations H, V, +, -; two intensities, "
            "'signal' at mu = 1/2 and 'decoy' at mu = 1/8; eight letters "
            "(a, mu, gen), one per pair, of equal weight p_x = 1/8; cutoffs "
            "N_ent = 1 and N_src = 2, which puts exactly ONE photon number "
            "between them and so exercises the polarisation-flag summand of (T3) "
            "that the published lemma does not carry. The declared ptilde are "
            "dyadic rationals BELOW the Poisson weights, which eq:weightineq "
            "permits: at mu = 1/2 those are 0.6065, 0.3033, 0.0758 and the "
            "declaration carries 1/2, 1/4, 1/16; at mu = 1/8 they are 0.8825, "
            "0.1103, 0.0069 and it carries 7/8, 1/16, 1/256. "
            "TAIL WEIGHTS, eq:tailweight, the sum in increasing n: "
            "wtilde_signal = 1 - (1/2 + 1/4 + 1/16) = 1 - 13/16 = 3/16; "
            "wtilde_decoy = 1 - (7/8 + 1/16 + 1/256) = 1 - 241/256 = 15/256. "
            "Both are positive, so every (a, mu) carries a tail flag. "
            "THE INDEX SET, eq:tset, in the declared order: the quantum sectors "
            "n <= N_ent, which are n = 0 of dimension one (the vacuum, shared by "
            "every polarisation) and n = 1 of dimension two (span of |1,H> and "
            "|1,V>); then the polarisation flags at N_ent < n <= N_src, which is "
            "n = 2 alone, one per polarisation and SHARED ACROSS THE TWO "
            "INTENSITIES -- four one-dimensional sectors and not eight, which is "
            "the sharing rem:no-intensity-split is about; then the tail flags, "
            "one per (a, mu) a letter carries, which is eight one-dimensional "
            "sectors. Fourteen sectors, d_A = 1 + 2 + 4 + 8 = 15. "
            "THE TAIL FLAGS RUN IN THE DECLARED ORDER OF (a, mu), which is read "
            "exactly as the (n, a) of the polarisation flags is read: the "
            "model's declared POLARISATION order outer and its declared "
            "INTENSITY order inner, so the list is (H, signal), (H, decoy), "
            "(V, signal), (V, decoy), (+, signal), (+, decoy), (-, signal), "
            "(-, decoy). It is NOT the order of the alphabet, which is a third "
            "declared order that def:tagged-source (T3) does not name and which "
            "for this model -- intensity-major -- gives a different list; that "
            "was the implementation review's F-4, and the entry above is the "
            "corrected one. The order is a datum: it fixes the position of "
            "every block a consumer reads off a block list. "
            "THE BLOCKS, eq:decoy-blocks, sigma = p_x w_{x,t} |phi><phi|. For "
            "the letter (H, signal): on n0, (1/8)(1/2)(1) = 1/16; on n1, "
            "(1/8)(1/4)|1,H><1,H| = (1/32) diag(1, 0); on flag-n2-H, "
            "(1/8)(1/16) = 1/128 and on the other polarisation flags zero, the "
            "weight being zero there; on tail-H-signal, (1/8)(3/16) = 3/128 and "
            "zero on every other tail flag. The traces sum to "
            "1/16 + 1/32 + 1/128 + 3/128 = 16/128 = 1/8 = p_x, which is (E2). "
            "For the letter (+, decoy): on n0, (1/8)(7/8) = 7/64; on n1, "
            "(1/8)(1/16)|1,+><1,+| with |1,+><1,+| = (1/2)[[1,1],[1,1]] gives "
            "1/256 at every entry; on flag-n2-+, (1/8)(1/256) = 1/2048; on "
            "tail-+-decoy, (1/8)(15/256) = 15/2048. Traces: "
            "7/64 + 2/256 + 1/2048 + 15/2048 = 256/2048 = 1/8 = p_x. "
            "tau_A, the transposed sum of (E3), sector by sector. On n0 every "
            "letter contributes p_x ptilde(0 | mu_x): four signal letters give "
            "4 (1/8)(1/2) = 1/4 and four decoy letters 4 (1/8)(7/8) = 7/16, so "
            "tau^(n0) = 11/16. On n1 the four one-photon projectors of one "
            "intensity sum to 2 x 1_2, since |1,H><1,H| + |1,V><1,V| = 1_2 and "
            "|1,+><1,+| + |1,-><1,-| = 1_2; the signal letters carry "
            "p_x ptilde = 1/32 each and the decoy letters 1/128, so the sum is "
            "(1/32)(2) 1_2 + (1/128)(2) 1_2 = (1/16 + 1/64) 1_2 = (5/64) 1_2, "
            "and the transpose of a multiple of the identity is itself. On the "
            "polarisation flag of a given a, the two letters of that "
            "polarisation contribute (1/8)(1/16) + (1/8)(1/256) = "
            "16/2048 + 1/2048 = 17/2048. On a tail flag exactly one letter "
            "contributes: 3/128 for a signal flag and 15/2048 for a decoy one. "
            "The total trace is 1408/2048 + 320/2048 + 4(68)/2048 ... written "
            "out: 11/16 + 2(5/64) + 4(17/2048) + 4(3/128) + 4(15/2048) = "
            "(1408 + 320 + 68 + 192 + 60)/2048 = 2048/2048 = 1, which is the "
            "sum_x p_x = 1 of (E2) read through the marginal."
        ),
    ),
)


# ===========================================================================
#  Group TX-C1-D -- the closed soundness registry
# ===========================================================================

#: ``def:source-segment`` (A1) Eq. ``eq:registry`` and ``cor:emitted-decoy`` (ii):
#: the ONE entry of the closed registry, derived rather than copied.
#:
#: The kind is ``tagging``, the one kind a submodule declares and supplies a
#: soundness claim for. The claim is ``transmitter/decoy/prop:tagging``, whose
#: conclusion Eq. ``eq:tagid`` is the source identity at every member of its
#: declared family. The third component is the UNION of two sources: the
#: assumption closure of that claim, which is EMPTY -- its header declares
#: ``assumes: []`` and it uses only ``def:wcp-model``, ``def:tagged-source`` and
#: ``transmitter/def:source-link``, none of which assumes anything, so the
#: transitive closure under ``uses`` and ``assumes`` contains no assumption --
#: TOGETHER WITH the physical-source assumption the submodule declares for the
#: model the claim is stated over, which is A-WCP. The union is ``(A-WCP,)``, and
#: a registry derived from the claim graph alone would have produced the empty
#: list and matched no emitted triple.
TAGGING_REGISTRY_TRIPLE: tuple[str, str, tuple[str, ...]] = (
    "tagging",
    "transmitter/decoy/prop:tagging",
    ("A-WCP",),
)
