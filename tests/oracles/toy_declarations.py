"""Hand-authored toy protocol declarations for the ``meat-core`` oracle registry.

The toys are hand-authored ``ProofInstance``s with dummy operator
bundles small enough to reason about, with independently known answers.

Every object here is written out by hand from ``contract.tex`` (0.3.0 for the
first two groups, 0.4.0 for the third) and is
small enough to check on paper. In particular the **branch Kraus operators are
literal matrices**, not generated: assembling them from a declaration is
Definition ``def:branch`` of claim C2, which is solver-side work under
``src/certiqs_key/meat/`` and is deliberately absent from this tree. Each toy
records the by-hand assembly in its ``derivation`` string so that a reader can
redo it, and each toy carries *two independently hand-written* Kraus pictures --
per sector and dense -- whose agreement is the C2(iii) sector-decomposition
oracle rather than an assumption.

Conventions, transcribed from ``contract.tex`` Section 2.5 and mirrored in
``interface.yaml``:

* ``log_base: 2``, ``entropy_units: bits``;
* ``entropy_variant: sandwiched-renyi``, ``arrow: up``;
* ``test_statistics_model: output_state`` -- the round type is a component of
  the declared joint outcome ``v``, never a separately split test fraction;
* ``subsystem_order`` for states is ``A, Q, Etilde``;
* ``source_model`` is **derived** and never separately declared: it is
  ``trusted`` exactly when the marginal slot carries a ``tau_A`` and
  ``untrusted`` when it carries ``none``. A second field holding the mode
  would be a second source of truth and the contract forbids it, so this
  module has none: :func:`source_mode` reads it off ``alice_marginal``.

The three groups of toys
------------------------
``ALL_TOYS`` holds the twelve declarations frozen at the G4 against
``contract.tex`` 0.2.4. Every one of them is still a well-formed 0.3.0
declaration -- they are all in trusted-source mode with the DEFAULT party
partition, which ``contract.tex`` Definition ``def:declaration`` says
"reproduces versions 0.2.x of this contract verbatim". Not one number changed.

``SOURCE_MODE_TOYS`` holds the seven declarations added for the material 0.3.0
introduces: the untrusted-source mode, the singular trusted marginal, and the
party partition. They are kept in a separate tuple for one concrete reason:
the operator-bundle manifest of ``certiqs_key.domain`` (schema 0.1.0) cannot yet
serialize ``alice_marginal: null``, ``source_replacement_license`` or
``party_partition``, so :mod:`dummy_bundles` cannot build a bundle for them and
every consumer that iterates ``ALL_TOYS`` and serializes would break. Extending
the manifest and the schema is solver-side work under ``src/`` and
``schemas/``; see the run report accompanying this freeze. ``ALL_TOYS_0_3_0``
is the union of those two groups.

``CERTIFICATE_TOYS`` holds the two declarations added at ``contract.tex``
0.4.0 for the certificate chain C18-C20 / C13: one trusted-source and one
untrusted-source declaration carrying **one constraint of each relation
symbol** of Assumption ``A-DECL`` (vi), which no earlier toy does -- TOY-5 and
TOY-6 carry ``succeq``, TOY-7 carries ``preceq``, and nothing carried ``eq``,
whose dual variable is the one Theorem ``thm:weak-duality`` leaves unrestricted
in sign. They are a third tuple for the same reason the second one exists: the
frozen 0.3.0 consumers iterate ``ALL_TOYS`` and ``ALL_TOYS_0_3_0`` and must
keep seeing exactly what they saw. ``ALL_TOYS_0_4_0`` is the union of all three
and is what a consumer that does not serialize should iterate; :func:`toy`
resolves against it.

Index conventions used by the literal matrices below
----------------------------------------------------
A branch Kraus operator ``K^{(s)}_kappa`` of Eq. ``eq:kraus`` maps
``H(A ⊗ Q_s)`` into ``H(R ⊗ XY ⊗ C_A C_B ⊗ A ⊗ Q_s)``. In every toy here
``d_A = 1`` or Alice has a single outcome, and every branch has exactly one
announcement class, so the surviving output basis is indexed by ``(v, q)``
with ``v`` Bob's outcome and ``q`` the sector -- the ``R`` value of a row is
``r(x, v)`` and the ``XY`` label is ``(x, v)``, both functions of ``v``.

``row_key_values`` records the ``R`` eigenvalue of each output row. That is
exactly the data the key pinching ``Z(tau) = sum_j Z_j tau Z_j`` of Definition
``def:maps`` needs: ``Z`` keeps matrix entries whose two rows carry the same
``R`` value and kills the rest.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np
import numpy.typing as npt

Matrix = npt.NDArray[np.float64]

# Sifting failure. contract.tex Definition def:declaration writes the raw-key
# alphabet as Z_perp = Z u {perp}; `None` is the JSON/bundle spelling of perp
# (src/certiqs_key/domain/manifest.py, `key_map: dict[str, dict[str, int | None]]`).
PERP: None = None

# The value of the MARGINAL SLOT in untrusted-source mode. contract.tex
# Definition def:declaration types the slot as S_=(A) disjoint-union {none};
# Section 2.1 gives `none` the machine value `null`, and the Notation section
# records that it is "deliberately not perp, which is the sifting-failure key
# value, and not 0, which is inadmissible". Python spells both `null` values
# `None`; the two constants are kept apart here so that the distinction the
# contract insists on is visible at every use site.
NOMARG: None = None


@dataclass(frozen=True)
class SectorBranch:
    """One sector block of one branch map ``G_{chat,s}`` (contract Def. def:branch).

    ``kraus`` holds ``K^{(s)}_kappa`` for each PASS announcement class kappa in
    ``phi^{-1}(chat)``; ``G_{chat,s}(sigma) = sum_kappa K sigma K^dagger``.
    ``row_key_values[i]`` is the ``R`` value carried by output row ``i``.
    """

    sector: str
    kraus: tuple[Matrix, ...]
    row_key_values: tuple[int, ...]


@dataclass(frozen=True)
class DenseBranch:
    """The same branch map written on the whole of ``A ⊗ Q`` (no sector split).

    Written out independently of :class:`SectorBranch` so that the C2(iii)
    identity ``G_chat(omega) = direct_sum_s G_{chat,s}(omega_s)`` is checked
    between two hand-authored objects rather than assumed.
    """

    kraus: tuple[Matrix, ...]
    row_key_values: tuple[int, ...]
    row_sectors: tuple[str, ...]


@dataclass(frozen=True)
class PartyPartition:
    """The party partition ``P`` of contract Def. ``def:declaration``.

    Part (a), the READOUT MAPS, is the only part any derivation consumes, and
    it is consumed only through Assumption ``A-DECL`` (viii): each party
    announces a function of its own readout, and the declared key holder
    computes the raw key from ITS OWN readout and the announcements
    (Eq. ``eq:partycomp``). Part (b) is system metadata -- a party label for
    ``A`` and one per declared tensor factor of each ``H(Q_s)`` -- carrying a
    supplier obligation that ``meat-core`` never verifies and no claim depends
    on.

    ``readout_alice`` and ``readout_bob`` are total maps on ``X x V``. The
    DEFAULT partition of ``def:declaration`` is ``pi_A(x, v) = x``,
    ``pi_B(x, v) = v`` with ``A`` labelled ``A`` and every ``Q_s`` labelled
    ``B``; it is spelled by ``ToyDeclaration.party_partition = None`` and
    materialized by :func:`party_partition_of`, because it "reproduces
    versions 0.2.x of this contract verbatim" and the twelve frozen 0.2.4-era
    toys carry it.
    """

    readout_alice: dict[tuple[str, str], str]
    readout_bob: dict[tuple[str, str], str]
    alphabet_alice: tuple[str, ...]
    alphabet_bob: tuple[str, ...]
    party_of_alice_system: str  # party label of the register A
    # sector -> per declared tensor factor of H(Q_s), the party label.
    party_of_sector_factors: dict[str, tuple[str, ...]]
    is_default: bool = False


@dataclass(frozen=True)
class ToyConstraint:
    """One entry ``(O_k, bowtie_k, Theta_k)`` of the declared list ``L``.

    ``bound`` is ``Theta_k``, whose TYPE is set by the declared source mode
    (contract Def. ``def:declaration``; Assumption ``A-DECL`` (vi)): a
    Hermitian matrix on ``A`` in trusted-source mode, and a real scalar ``c_k``
    in untrusted-source mode. ``relation`` keeps the three machine keys of
    contract Section 2.1 in both modes -- that table writes
    ``bowtie_k in {preceq, =, succeq}`` once and types only ``Theta_k`` by
    mode; in untrusted-source mode they denote the order of the reals.
    """

    operator_blocks: dict[str, Matrix]
    # Spelled as the operator relations of contract Def. def:declaration
    # (bowtie_k in {preceq, =, succeq}); the strings are the machine keys of
    # certiqs_key.domain.manifest.ConstraintRelation.
    relation: str  # "preceq" | "eq" | "succeq"
    bound: Matrix | float
    #: c_k. In TRUSTED-source mode: the scalar with Theta_k = c_k tau_A when
    #: the entry is tau_A-homogeneous, else None (def:homog (a)). In
    #: UNTRUSTED-source mode: the right-hand side itself, which IS a real
    #: scalar for every well-formed declaration (def:homog (b)), so it is
    #: never None there.
    homogeneous_scalar: float | None


@dataclass(frozen=True)
class ToyDeclaration:
    """A complete, hand-checkable declaration (contract Def. def:declaration)."""

    toy_id: str
    summary: str
    derivation: str
    alice_dim: int
    #: The MARGINAL SLOT: ``tau_A`` in ``S_=(A)`` (trusted-source mode) or
    #: :data:`NOMARG` (untrusted-source mode). Its two values ARE the two
    #: source modes, which is why no separate mode field exists; read the mode
    #: with :func:`source_mode`.
    alice_marginal: Matrix | None
    sector_index_set: tuple[str, ...]
    sector_dims: dict[str, int]
    alice_povm: dict[str, Matrix]
    bob_povm: dict[str, dict[str, Matrix]]  # v -> sector -> block F_v^{(s)}
    announce_alice: dict[str, str]
    announce_bob: dict[str, str]
    accept_statistic: dict[tuple[str, str], str]
    key_map: dict[tuple[str, str], int | None]
    key_holder: str
    key_value_count: int
    acceptance_values: tuple[str, ...]
    chat_key: tuple[str, ...]
    acceptance_set: dict[str, Any]
    branches: dict[str, tuple[SectorBranch, ...]]  # chat -> per-sector branches
    dense_branches: dict[str, DenseBranch]  # chat -> dense branch
    statistics: dict[str, dict[str, float]]  # chat -> sector -> Phi_s weight
    sector_classes: dict[str, str]  # "key-active" | "constraint-active"
    state_blind: dict[str, bool]
    removable: dict[str, bool]
    constraint_list: tuple[ToyConstraint, ...] = ()
    attack_set_license: dict[str, Any] | None = None
    #: contract Section 2.1: optional, REQUIRED whenever ``alice_marginal`` is
    #: present, and VACUOUS at ``d_A = 1``, where it "must not be demanded"
    #: (Assumption ``A-SRC``; Remark ``rem:modes-da1`` (b5)).
    source_replacement_license: dict[str, Any] | None = None
    #: ``None`` spells the DEFAULT partition of contract Def. ``def:declaration``.
    party_partition: PartyPartition | None = None
    #: ``chat -> sector -> Gamma^{(s)}_chat``, the Hermitian operator on
    #: ``A x Q_s`` with ``Phi[omega](chat) = sum_s tr[Gamma^{(s)}_chat
    #: omega_s]`` (contract Eq. ``eq:Phimap``, and the same operator as
    #: Eq. ``eq:grad-pieces-un``). Present on the toys whose statistics depend
    #: on more of ``omega`` than its sector weights -- i.e. those with
    #: ``d_A >= 2`` -- where the scalar ``statistics`` shares cannot express
    #: the dependence; those toys carry ``statistics = {}`` instead.
    statistics_operators: dict[str, dict[str, Matrix]] = field(default_factory=dict)
    notes: tuple[str, ...] = field(default_factory=tuple)


def source_mode(declaration: ToyDeclaration) -> str:
    """Return the DERIVED source mode of ``declaration``.

    contract.tex Section 2.5: "``source_model``: ``trusted`` or ``untrusted``,
    *derived*, never separately declared -- it is ``trusted`` exactly when
    ``alice_marginal`` is present. A second key carrying the mode would be a
    second source of truth and is forbidden."
    """
    return "untrusted" if declaration.alice_marginal is None else "trusted"


def party_partition_of(declaration: ToyDeclaration) -> PartyPartition:
    """Return ``declaration``'s party partition, materializing the default.

    The default of contract Def. ``def:declaration`` is ``pi_A(x, v) = x``,
    ``pi_B(x, v) = v``, with ``A`` labelled ``A`` and every ``Q_s`` labelled
    ``B`` (one declared tensor factor per sector).
    """
    if declaration.party_partition is not None:
        return declaration.party_partition
    pairs = [(x, v) for x in declaration.alice_povm for v in declaration.bob_povm]
    return PartyPartition(
        readout_alice={(x, v): x for x, v in pairs},
        readout_bob={(x, v): v for x, v in pairs},
        alphabet_alice=tuple(declaration.alice_povm),
        alphabet_bob=tuple(declaration.bob_povm),
        party_of_alice_system="A",
        party_of_sector_factors=dict.fromkeys(declaration.sector_index_set, ("B",)),
        is_default=True,
    )


_HALF = math.sqrt(0.5)


# ---------------------------------------------------------------------------
# TOY-1 -- the retention instance of contract.tex Proposition prop:retention.
# ---------------------------------------------------------------------------

TOY1_RETENTION = ToyDeclaration(
    toy_id="TOY-1",
    summary=(
        "Two one-dimensional sectors: s0 key-active (unbiased response), s1 "
        "key-inert hence constraint-active. The declaration of contract.tex "
        "Proposition prop:retention (C10b)."
    ),
    derivation="""\
Declaration (contract.tex Prop. prop:retention, transcribed):
  d_A = 1, tau_A = [1], X = {x0} with M_x0 = [1] (announcements trivial,
  one announcement class kappa0 = (cA0, cB0), sifting always passes,
  phi == chat0, Chat = Chat_key = {chat0}, AcceptSet = {delta_chat0}).
  Q = Q_s0 (+) Q_s1, both one-dimensional.
  V = {v0, v1}, r(x0, v) = v, so Z = {0, 1} and d_Z = 2.
  F^{(s0)}_v0 = F^{(s0)}_v1 = 1/2   (POVM completeness on s0: 1/2 + 1/2 = 1)
  F^{(s1)}_v0 = 1, F^{(s1)}_v1 = 0  (POVM completeness on s1: 1 + 0 = 1)
  key_holder h = B, since r(x, v) = v factors through Bob's own outcome and
  the announcements (Assumption A-DECL (viii)); L = {} (empty).

Branch Kraus, by hand from Eq. eq:kraus with the single pass class kappa0:
  K^{(s)}_kappa0 = sum_v |r(x0,v)>_R |x0,v>_XY |kappa0> (sqrt(M_x0) x sqrt(F^{(s)}_v))
  The surviving output rows are indexed by v; row v carries R = r(x0, v) = v.
    s0: column vector (sqrt(1/2), sqrt(1/2))^T, row_key_values = (0, 1)
    s1: column vector (1, 0)^T,                 row_key_values = (0, 1)

Objective ingredients on omega = diag(w0, w1), w0 + w1 = 1 (tr omega = tr tau_A = 1):
  Sector s0: G_{chat0,s0}(w0) = w0 |eta><eta| with |eta> = (1,1)/sqrt(2).
    G^{1/alpha} = w0^{1/alpha} |eta><eta|; Z(|eta><eta|) = (1/2) I_2;
    (Z(G^{1/alpha}))^alpha = w0 2^{-alpha} I_2, so T_{chat0,s0} = w0 * 2^{1-alpha}.
    tr G_{chat0,s0} = w0, hence f_{chat0,s0}(w0) = w0 (2^{1-alpha} - 1) < 0 for w0 > 0.
  Sector s1: G_{chat0,s1}(w1) = w1 diag(1, 0), already Z-block-diagonal, so
    T_{chat0,s1} = w1 = tr G_{chat0,s1} and f_{chat0,s1} == 0 (C7: s1 is key-inert,
    its effective outcome set E^{(s1)}_kappa0 = {(x0, v0)} is a singleton so r is
    constant on it).
  P_chat0 = 1 for every feasible omega, tr G_chat0 = w0 + w1 = 1, so
    K_chat0 = T + P - tr G = w0 2^{1-alpha} + w1 = 1 + w0 (2^{1-alpha} - 1).

Objective: q = delta_chat0 = Phi[omega], so the divergence term vanishes and
  O_alpha = (1/(alpha-1)) log2(1 / K_chat0), decreasing in K_chat0, hence
  minimized at the LARGEST K, i.e. at w0 = 0:
    h_low(TOY-1) = 0 for every alpha in (1, inf).
  Forcing the constraint-active sector s1 to zero (w0 = 1) gives K = 2^{1-alpha}
  and the strictly larger value (1/(alpha-1)) log2(2^{alpha-1}) = 1 bit.
""",
    alice_dim=1,
    alice_marginal=np.array([[1.0]]),
    sector_index_set=("s0", "s1"),
    sector_dims={"s0": 1, "s1": 1},
    alice_povm={"x0": np.array([[1.0]])},
    bob_povm={
        "v0": {"s0": np.array([[0.5]]), "s1": np.array([[1.0]])},
        "v1": {"s0": np.array([[0.5]]), "s1": np.array([[0.0]])},
    },
    announce_alice={"x0": "cA0"},
    announce_bob={"v0": "cB0", "v1": "cB0"},
    accept_statistic={("cA0", "cB0"): "chat0"},
    key_map={("x0", "v0"): 0, ("x0", "v1"): 1},
    key_holder="B",
    key_value_count=2,
    acceptance_values=("chat0",),
    chat_key=("chat0",),
    acceptance_set={"geometry": "singleton", "frequencies": (1.0,)},
    branches={
        "chat0": (
            SectorBranch(
                sector="s0",
                kraus=(np.array([[_HALF], [_HALF]]),),
                row_key_values=(0, 1),
            ),
            SectorBranch(
                sector="s1",
                kraus=(np.array([[1.0], [0.0]]),),
                row_key_values=(0, 1),
            ),
        )
    },
    dense_branches={
        # Rows (v, q) in the order (v0,s0), (v0,s1), (v1,s0), (v1,s1);
        # entry [(v,q), q'] = delta_{q,q'} sqrt(F^{(q)}_v).
        "chat0": DenseBranch(
            kraus=(
                np.array(
                    [
                        [_HALF, 0.0],
                        [0.0, 1.0],
                        [_HALF, 0.0],
                        [0.0, 0.0],
                    ]
                ),
            ),
            row_key_values=(0, 0, 1, 1),
            row_sectors=("s0", "s1", "s0", "s1"),
        )
    },
    statistics={"chat0": {"s0": 1.0, "s1": 1.0}},
    sector_classes={"s0": "key-active", "s1": "constraint-active"},
    state_blind={"s0": True, "s1": True},
    # Neither sector is removable: (RM1) needs
    # c_{v,s*} = sum_i mu_i tr[F^{(s_i)}_v chi_i]
    # with the s_i drawn from the OTHER sectors, and (1/2, 1/2) != (1, 0) either way.
    removable={"s0": False, "s1": False},
    notes=(
        "Every sector here is state-blind only because both are one-dimensional;"
        " state-blindness is not what makes a sector removable (RM1-RM3 also"
        " require a matching key-inert target).",
    ),
)


# ---------------------------------------------------------------------------
# TOY-2 -- the averaging obstruction of contract.tex Proposition prop:no-averaging.
# ---------------------------------------------------------------------------

TOY2_DETERMINISTIC = ToyDeclaration(
    toy_id="TOY-2",
    summary=(
        "Two one-dimensional sectors responding deterministically and "
        "differently: the raw key is a function of the sector index. Every "
        "pair (chat, s) is key-inert. The un-averaged declaration of "
        "contract.tex Proposition prop:no-averaging (C10c)."
    ),
    derivation="""\
Declaration: TOY-1 with the Bob POVM replaced by projective per-sector responses
  F^{(s0)}_v0 = 1, F^{(s0)}_v1 = 0,   F^{(s1)}_v0 = 0, F^{(s1)}_v1 = 1
(so sum_v F^{(s)}_v = 1 = identity on each one-dimensional sector). Everything
else -- d_A = 1, one announcement class, always pass, phi == chat0,
AcceptSet = {delta_chat0}, r(x0, v) = v, h = B, L = {} -- is unchanged.

Branch Kraus, by hand:
  s0: column (1, 0)^T with row_key_values = (0, 1)
  s1: column (0, 1)^T with row_key_values = (0, 1)
Each has a single nonzero row, so G_{chat0,s}(w_s) is supported in ONE R
eigenspace and is a fixed point of the key pinching Z. By Corollary
cor:f-nonpos (equality case) f_{chat0,s} == 0 for both sectors and every input;
equivalently, each effective outcome set E^{(s)}_kappa0 is the singleton
{(x0, v_{s})}, so r is constant on it and the pair is key-inert (Def. def:keyinert).

Hence K_chat0 = P_chat0 = 1 for every feasible omega, and
  h_low(TOY-2) = (1/(alpha-1)) log2(1/1) = 0 for every alpha in (1, inf).
This is the "deterministic / perfectly correlated" limit: the raw key is a
deterministic function of a register (the sector index) that the purifying
register may hold, so no secrecy is claimed. Zero is the CORRECT value, and it
is the value an implementation must return -- not a small positive number.
""",
    alice_dim=1,
    alice_marginal=np.array([[1.0]]),
    sector_index_set=("s0", "s1"),
    sector_dims={"s0": 1, "s1": 1},
    alice_povm={"x0": np.array([[1.0]])},
    bob_povm={
        "v0": {"s0": np.array([[1.0]]), "s1": np.array([[0.0]])},
        "v1": {"s0": np.array([[0.0]]), "s1": np.array([[1.0]])},
    },
    announce_alice={"x0": "cA0"},
    announce_bob={"v0": "cB0", "v1": "cB0"},
    accept_statistic={("cA0", "cB0"): "chat0"},
    key_map={("x0", "v0"): 0, ("x0", "v1"): 1},
    key_holder="B",
    key_value_count=2,
    acceptance_values=("chat0",),
    chat_key=("chat0",),
    acceptance_set={"geometry": "singleton", "frequencies": (1.0,)},
    branches={
        "chat0": (
            SectorBranch(
                sector="s0",
                kraus=(np.array([[1.0], [0.0]]),),
                row_key_values=(0, 1),
            ),
            SectorBranch(
                sector="s1",
                kraus=(np.array([[0.0], [1.0]]),),
                row_key_values=(0, 1),
            ),
        )
    },
    dense_branches={
        "chat0": DenseBranch(
            kraus=(
                np.array(
                    [
                        [1.0, 0.0],
                        [0.0, 0.0],
                        [0.0, 0.0],
                        [0.0, 1.0],
                    ]
                ),
            ),
            row_key_values=(0, 0, 1, 1),
            row_sectors=("s0", "s1", "s0", "s1"),
        )
    },
    statistics={"chat0": {"s0": 1.0, "s1": 1.0}},
    sector_classes={"s0": "constraint-active", "s1": "constraint-active"},
    state_blind={"s0": True, "s1": True},
    removable={"s0": False, "s1": False},
)


TOY2_AVERAGED = ToyDeclaration(
    toy_id="TOY-2-AVG",
    summary=(
        "The coarse-grained image of TOY-2: one sector carrying the averaged "
        "POVM Fbar_v = (F^{(s0)}_v + F^{(s1)}_v)/2 = 1/2. Reproduces TOY-2's "
        "outcome statistics at uniform sector weights and reports one whole "
        "bit per round that TOY-2 does not have."
    ),
    derivation="""\
Averaged declaration (contract.tex Prop. prop:no-averaging): one one-dimensional
sector sbar with Fbar_v0 = Fbar_v1 = 1/2 -- a valid POVM, and on its single
feasible state omegabar = 1 it reproduces TOY-2's statistics at the uniform
sector weights. Everything else unchanged.

Branch Kraus, by hand: column (sqrt(1/2), sqrt(1/2))^T with row_key_values (0, 1).
This is TOY-1's sector s0 at w0 = 1, so
  T = 2^{1-alpha}, tr G = 1, P = 1, K = 2^{1-alpha}, and
  h_low(TOY-2-AVG) = (1/(alpha-1)) log2(2^{alpha-1}) = 1 bit for every alpha.

ORACLE: h_low(TOY-2-AVG) - h_low(TOY-2) = 1 - 0 = 1 bit per round, at every
alpha in (1, inf). An engine that merged the two sectors would certify one
secret bit per round for a protocol whose key the adversary knows exactly. The
gap is exact, not asymptotic, and it is in the DANGEROUS direction.
""",
    alice_dim=1,
    alice_marginal=np.array([[1.0]]),
    sector_index_set=("sbar",),
    sector_dims={"sbar": 1},
    alice_povm={"x0": np.array([[1.0]])},
    bob_povm={
        "v0": {"sbar": np.array([[0.5]])},
        "v1": {"sbar": np.array([[0.5]])},
    },
    announce_alice={"x0": "cA0"},
    announce_bob={"v0": "cB0", "v1": "cB0"},
    accept_statistic={("cA0", "cB0"): "chat0"},
    key_map={("x0", "v0"): 0, ("x0", "v1"): 1},
    key_holder="B",
    key_value_count=2,
    acceptance_values=("chat0",),
    chat_key=("chat0",),
    acceptance_set={"geometry": "singleton", "frequencies": (1.0,)},
    branches={
        "chat0": (
            SectorBranch(
                sector="sbar",
                kraus=(np.array([[_HALF], [_HALF]]),),
                row_key_values=(0, 1),
            ),
        )
    },
    dense_branches={
        "chat0": DenseBranch(
            kraus=(np.array([[_HALF], [_HALF]]),),
            row_key_values=(0, 1),
            row_sectors=("sbar", "sbar"),
        )
    },
    statistics={"chat0": {"sbar": 1.0}},
    sector_classes={"sbar": "key-active"},
    state_blind={"sbar": True},
    removable={"sbar": False},
)


# ---------------------------------------------------------------------------
# TOY-3 -- the fully dephased family.
# ---------------------------------------------------------------------------


def fully_dephased(m: int) -> ToyDeclaration:
    """Return the ``m``-outcome fully dephased toy; ``h_low == log2(m)`` exactly.

    ``d_A = 1`` and ``dim Q = 1``, so the purifying register is trivial and the
    single branch operator is a pure state spread uniformly over ``m`` distinct
    raw-key values. The key pinching therefore dephases it completely.
    """
    outcomes = tuple(f"v{i}" for i in range(m))
    kraus = np.full((m, 1), 1.0 / math.sqrt(m))
    return ToyDeclaration(
        toy_id=f"TOY-3(m={m})",
        summary=(
            f"Trivial Alice and trivial receiver space, {m} equiprobable Bob "
            f"outcomes each carrying its own raw-key value: the branch operator "
            f"is fully dephased by Z and h_low = log2({m}) exactly, at every alpha."
        ),
        derivation=f"""\
Declaration: d_A = 1, tau_A = [1], X = {{x0}} with M_x0 = [1]; a single
one-dimensional sector s0 (so the ONLY feasible omega is [1] and the purifying
register is trivial); V = {{v0, ..., v{m - 1}}} with F_v = 1/{m} for every v
(POVM completeness: {m} * 1/{m} = 1); trivial announcements, one class, always
pass, phi == chat0, Chat = Chat_key = {{chat0}}, AcceptSet = {{delta_chat0}};
r(x0, v_i) = i, so Z = {{0, ..., {m - 1}}} and d_Z = {m}; h = B; L = {{}}.

Branch Kraus, by hand from Eq. eq:kraus: the column vector with every entry
1/sqrt({m}), row i carrying R = i. So G_chat0([1]) = |eta><eta| with
|eta> = (1, ..., 1)/sqrt({m}), and

  G^{{1/alpha}} = |eta><eta|,  Z(|eta><eta|) = (1/{m}) I_{m},
  (Z(G^{{1/alpha}}))^alpha = {m}^{{-alpha}} I_{m},
  T_chat0 = {m} * {m}^{{-alpha}} = {m}^{{1-alpha}},
  tr G_chat0 = 1, P_chat0 = 1, so K_chat0 = {m}^{{1-alpha}}.

  h_low = (1/(alpha-1)) log2(1 / {m}^{{1-alpha}}) = log2({m}),
  for every alpha in (1, inf).

INDEPENDENT CONFIRMATION (C5, Eq. eq:c5). With d_A = 1 and dim Q = 1 the
conditioning system I Etilde is trivial and the branch state is the uniform
distribution on {m} key values, whose sandwiched Renyi conditional entropy is
the Renyi entropy H_alpha(Unif({m})) = log2({m}) -- the same number, derived
without touching K or T. This also saturates the entropy-part ceiling of Remark
rem:hlow-range on the support: log2|supp p| = log2({m}) <= log2(d_Z + 1).
""",
        alice_dim=1,
        alice_marginal=np.array([[1.0]]),
        sector_index_set=("s0",),
        sector_dims={"s0": 1},
        alice_povm={"x0": np.array([[1.0]])},
        bob_povm={v: {"s0": np.array([[1.0 / m]])} for v in outcomes},
        announce_alice={"x0": "cA0"},
        announce_bob=dict.fromkeys(outcomes, "cB0"),
        accept_statistic={("cA0", "cB0"): "chat0"},
        key_map={("x0", v): i for i, v in enumerate(outcomes)},
        key_holder="B",
        key_value_count=m,
        acceptance_values=("chat0",),
        chat_key=("chat0",),
        acceptance_set={"geometry": "singleton", "frequencies": (1.0,)},
        branches={
            "chat0": (
                SectorBranch(
                    sector="s0", kraus=(kraus,), row_key_values=tuple(range(m))
                ),
            )
        },
        dense_branches={
            "chat0": DenseBranch(
                kraus=(kraus,),
                row_key_values=tuple(range(m)),
                row_sectors=("s0",) * m,
            )
        },
        statistics={"chat0": {"s0": 1.0}},
        sector_classes={"s0": "key-active"},
        state_blind={"s0": True},
        removable={"s0": False},
    )


TOY3_DEPHASED_2 = fully_dephased(2)
TOY3_DEPHASED_3 = fully_dephased(3)
TOY3_DEPHASED_4 = fully_dephased(4)


# ---------------------------------------------------------------------------
# TOY-4 -- zero generation: every round fails sifting, so Chat_key is empty.
# ---------------------------------------------------------------------------


def zero_generation(
    *, f0: float, accept: tuple[float, float], toy_id: str, comment: str
) -> ToyDeclaration:
    """Return a zero-generation toy: ``r == perp`` everywhere, so ``Chat_key`` is empty.

    ``f0`` is Bob's weight on the outcome announced as ``cB0``; ``accept`` is the
    single accepted frequency vector on ``(chat0, chat1)``. The whole objective
    is then the KL penalty ``(alpha/(alpha-1)) D(q || Phi[omega])``.
    """
    return ToyDeclaration(
        toy_id=toy_id,
        summary=comment,
        derivation=f"""\
Declaration: d_A = 1, tau_A = [1], X = {{x0}} with M_x0 = [1]; one
one-dimensional sector s0, so the only feasible omega is [1]; V = {{v0, v1}}
with F_v0 = {f0}, F_v1 = {1.0 - f0} (completeness: {f0} + {1.0 - f0} = 1);
a_B(v0) = cB0, a_B(v1) = cB1; phi(cA0, cB0) = chat0, phi(cA0, cB1) = chat1;
sifting FAILS on both classes, so r == perp, Chat_key = {{}} (Eq. eq:chkey) and
G_chat == 0 for every chat (Lemma lem:branch-maps (iv)); h = A; L = {{}};
AcceptSet = {{{accept}}}.

Statistics map (Eq. eq:Phimap): Phi[omega] = ({f0}, {1.0 - f0}).
Objective (Eq. eq:objective) with Chat_key empty:
  O_alpha(q, omega) = (alpha/(alpha-1)) * D(q || Phi[omega]),   D the base-2 KL
  divergence of Definition foundations/def:kl with 0 log2(0/p) = 0 and
  q log2(q/0) = +inf.
Both q and omega are forced, so h_low is that single number.

C2 trace identity (Eq. eq:traces) on this toy: tr G_chat + tr Theta_chat =
Phi[omega](chat) reads 0 + Phi(chat) = Phi(chat) -- the whole weight sits in
the fail branch.
""",
        alice_dim=1,
        alice_marginal=np.array([[1.0]]),
        sector_index_set=("s0",),
        sector_dims={"s0": 1},
        alice_povm={"x0": np.array([[1.0]])},
        bob_povm={
            "v0": {"s0": np.array([[f0]])},
            "v1": {"s0": np.array([[1.0 - f0]])},
        },
        announce_alice={"x0": "cA0"},
        announce_bob={"v0": "cB0", "v1": "cB1"},
        accept_statistic={("cA0", "cB0"): "chat0", ("cA0", "cB1"): "chat1"},
        key_map={("x0", "v0"): PERP, ("x0", "v1"): PERP},
        key_holder="A",
        key_value_count=1,
        acceptance_values=("chat0", "chat1"),
        chat_key=(),
        acceptance_set={"geometry": "singleton", "frequencies": accept},
        branches={"chat0": (), "chat1": ()},
        dense_branches={},
        statistics={"chat0": {"s0": f0}, "chat1": {"s0": 1.0 - f0}},
        sector_classes={"s0": "constraint-active"},
        state_blind={"s0": True},
        removable={"s0": False},
    )


TOY4A_ZERO_GENERATION = zero_generation(
    f0=0.25,
    accept=(0.25, 0.75),
    toy_id="TOY-4a",
    comment=(
        "Zero generation with a compatible acceptance set: no key rounds and "
        "no divergence penalty, so h_low = 0 exactly at every alpha."
    ),
)

TOY4B_DIVERGENCE_ONLY = zero_generation(
    f0=0.25,
    accept=(0.5, 0.5),
    toy_id="TOY-4b",
    comment=(
        "Zero generation with an INCOMPATIBLE but absolutely continuous "
        "acceptance set: the objective is the pure KL penalty, finite and "
        "strictly positive, and it diverges as alpha -> 1+."
    ),
)

TOY4C_INFEASIBLE = zero_generation(
    f0=0.0,
    accept=(0.5, 0.5),
    toy_id="TOY-4c",
    comment=(
        "Zero generation with an acceptance set NOT absolutely continuous with "
        "respect to the reachable statistics: h_low = +inf. The fail-closed "
        "branch of Remark rem:hlow-range."
    ),
)


# ---------------------------------------------------------------------------
# TOY-5 -- TOY-1 with a homogeneous constraint list; the only positive-rate
#          sector instance in the registry.
# ---------------------------------------------------------------------------

TOY5_CONSTRAINED = ToyDeclaration(
    toy_id="TOY-5",
    summary=(
        "TOY-1 plus one tau_A-homogeneous constraint pinning the key-active "
        "sector weight to w0 >= 1/2. Exercises the constrained feasible set, "
        "h_low(L) >= h_low({}), and the two-part security gate on L."
    ),
    derivation="""\
Declaration: TOY-1 with the constraint list
  L = { (O_1, succeq, Theta_1) },  O_1 = Pi_s0 = block-diag([1], [0]) on Q,
                               Theta_1 = (1/2) tau_A = [1/2].
O_1 is Hermitian and sector-block-diagonal, as Assumption A-DECL (iii)
requires. The list is tau_A-HOMOGENEOUS (Definition def:homog) with c_1 = 1/2,
because d_A = 1 makes every Hermitian Theta on A a scalar multiple of tau_A.

Feasible set (Eq. eq:feas): omega = diag(w0, w1) >= 0 with w0 + w1 = 1 and
  tr_Q[(1_A x O_1) omega] = w0 >= 1/2,   i.e. w0 in [1/2, 1].

Objective: as in TOY-1, O_alpha(w0) = (1/(alpha-1)) log2(1 / K(w0)) with
K(w0) = 1 + w0 (2^{1-alpha} - 1), which is DECREASING in w0 (the bracket is
negative for alpha > 1), so O_alpha is INCREASING in w0 and the infimum sits at
the constraint boundary w0 = 1/2:
  K = 1 + (1/2)(2^{1-alpha} - 1) = (1 + 2^{1-alpha}) / 2,
  h_low(L) = (1/(alpha-1)) log2( 2 / (1 + 2^{1-alpha}) ).

Sanity: h_low(L) >= h_low({}) = 0 for every alpha (Definition def:hqkd-list:
the constrained inner set is smaller), and h_low(L) -> 1/2 as alpha -> 1+,
which is the C16 value inf_{w0 >= 1/2} w0 = 1/2 (see the C16 oracle).

SECURITY GATE (contract Section 4.19, "Interface consequence"). L is nonempty,
so a key_length output may be emitted only if BOTH (i) L is tau_A-homogeneous
-- it is, mechanically -- AND (ii) attack_set_license is present. The license
field of this toy is None, so the conforming behaviour is a HARD FAIL on any
key-length request, while the numerical value h_low(L) above remains available
for exploration.
""",
    alice_dim=1,
    alice_marginal=np.array([[1.0]]),
    sector_index_set=("s0", "s1"),
    sector_dims={"s0": 1, "s1": 1},
    alice_povm={"x0": np.array([[1.0]])},
    bob_povm={
        "v0": {"s0": np.array([[0.5]]), "s1": np.array([[1.0]])},
        "v1": {"s0": np.array([[0.5]]), "s1": np.array([[0.0]])},
    },
    announce_alice={"x0": "cA0"},
    announce_bob={"v0": "cB0", "v1": "cB0"},
    accept_statistic={("cA0", "cB0"): "chat0"},
    key_map={("x0", "v0"): 0, ("x0", "v1"): 1},
    key_holder="B",
    key_value_count=2,
    acceptance_values=("chat0",),
    chat_key=("chat0",),
    acceptance_set={"geometry": "singleton", "frequencies": (1.0,)},
    branches=TOY1_RETENTION.branches,
    dense_branches=TOY1_RETENTION.dense_branches,
    statistics={"chat0": {"s0": 1.0, "s1": 1.0}},
    sector_classes={"s0": "key-active", "s1": "constraint-active"},
    state_blind={"s0": True, "s1": True},
    removable={"s0": False, "s1": False},
    constraint_list=(
        ToyConstraint(
            operator_blocks={"s0": np.array([[1.0]]), "s1": np.array([[0.0]])},
            relation="succeq",
            bound=np.array([[0.5]]),
            homogeneous_scalar=0.5,
        ),
    ),
    attack_set_license=None,
)


# ---------------------------------------------------------------------------
# TOY-6 -- TOY-5 with a genuinely removable third sector (contract Thm. thm:removal).
# ---------------------------------------------------------------------------

TOY6_REMOVABLE = ToyDeclaration(
    toy_id="TOY-6",
    summary=(
        "TOY-5 with a third one-dimensional sector s2 that duplicates the "
        "key-inert sector s1. s2 satisfies (RM1)-(RM3), so deleting it changes "
        "neither the value of h_low nor its attainment."
    ),
    derivation="""\
Declaration: TOY-5 with a third one-dimensional sector s2 carrying exactly the
response of s1: F^{(s2)}_v0 = 1, F^{(s2)}_v1 = 0. The constraint operator gains
the block O_1^{(s2)} = [0]; the list stays tau_A-homogeneous with c_1 = 1/2.

REMOVABILITY OF s2, checked against Theorem thm:removal (criteria named
(RM1)-(RM3) there so as not to collide with the review-rubric lines R1-R3):
  s2 is STATE-BLIND: F^{(s2)}_v = c_{v,s2} * 1_{Q_s2} with (c_v0, c_v1) = (1, 0),
  and O_1^{(s2)} = o_{1,s2} * 1 with o_{1,s2} = 0 (both hold trivially because
  the sector is one-dimensional).
  Take L = 1 target sector s_1 = s1, chi_1 = [1] (the only state on Q_s1),
  mu_1 = 1.
  (RM1) response match:   c_{v,s2} = mu_1 tr[F^{(s1)}_v chi_1] reads
        v0: 1 = 1 * 1 = 1  and  v1: 0 = 1 * 0 = 0.                    OK
  (RM2) key-inert targets: (chat0, s1) is key-inert -- E^{(s1)}_kappa0 =
        {(x0, v0)} is a singleton, so r is constant on it.             OK
  (RM3) constraint match: o_{1,s2} = mu_1 tr[O_1^{(s1)} chi_1] reads 0 = 0. OK
So s2 may be deleted from the variable list without loss.

VALUE. With three sectors the feasible set is w0 + w1 + w2 = 1, w_i >= 0,
w0 >= 1/2, and K = 1 + w0 (2^{1-alpha} - 1) is unchanged (s1 and s2 are both
key-inert, so f_{chat0,s1} = f_{chat0,s2} == 0 by Proposition prop:exact-cancellation). The
infimum is again at w0 = 1/2:
  h_low(TOY-6) = (1/(alpha-1)) log2( 2 / (1 + 2^{1-alpha}) ) = h_low(TOY-5).
That equality, at a value that is NOT zero, is the removal oracle: it would
fail if a removal criterion were applied where it does not hold.

SECTOR s1 IS REMOVABLE TOO, AND THE PAIR IS NOT.
CORRECTED (by the driver, under the freeze rule: "an expected value
that turns out to be wrong is a finding, reported and corrected deliberately
with its derivation"). This field read removable["s1"] = False, on the
argument that "s2 is itself the sector we would be trying to justify against".
That is an argument about deleting s1 AND s2 TOGETHER; it is not a hypothesis
of Theorem thm:removal, which is stated for ONE sector s* with targets drawn
from SecSet \\ {s*}. Raised as finding F-2 by the solver implementation, which
reported the difference instead of editing this file, and confirmed here
before the correction was made.

REMOVABILITY OF s1, target s2, mu = 1 -- the mirror image of s2's:
  s1 is STATE-BLIND (one-dimensional, so trivially).
  (RM1) c_{v,s1} = (1, 0) = 1 * tr[F^{(s2)}_v chi_2] = (1, 0).       OK
  (RM2) (chat0, s2) is key-inert: its effective outcome set is the
        singleton {(x0, v0)}, so r is constant on it.                OK
  (RM3) o_{1,s1} = 0 = 1 * tr[O_1^{(s2)} chi_2] = 0.                 OK
Checked against the theorem's CONCLUSION, which is about the infimum, on the
naive evaluator of this same tree: restricting to omega_s1 = 0 leaves
w0 + w2 = 1 with w0 >= 1/2, so w0 ranges over [1/2, 1] exactly as before and
the value is unchanged to 1e-9 at every alpha in the grid.

Being constraint-active is no bar to being removable. Definition def:classes
makes key-active / constraint-active a partition and `removable` a SEPARATE
predicate (d), defined purely by thm:removal's hypotheses -- whose (RM2) in
fact REQUIRES the targets to be key-inert, i.e. constraint-active. Proposition
prop:retention (C10b) is an existence statement: dropping a constraint-active
sector *merely because* it is constraint-active is unsound. The s2 entry above
already relies on that reading.

WHAT REMAINS UNSOUND is deleting s1 AND s2 together, which forces w0 = 1 and
takes h_low from 0.4568... to 1 at alpha = 1.5 -- a whole bit, in the
overstating direction. That is Proposition prop:retention's move, and no
per-sector verdict licenses it: thm:removal is applied to one sector at a
time, and once s1 is deleted the only remaining candidate target for s2 is s0,
which is key-active and so fails (RM2). The iteration therefore terminates on
its own -- but an implementation must still re-verify a witness against the
REDUCED declaration rather than trust a verdict computed before the deletion.
""",
    alice_dim=1,
    alice_marginal=np.array([[1.0]]),
    sector_index_set=("s0", "s1", "s2"),
    sector_dims={"s0": 1, "s1": 1, "s2": 1},
    alice_povm={"x0": np.array([[1.0]])},
    bob_povm={
        "v0": {
            "s0": np.array([[0.5]]),
            "s1": np.array([[1.0]]),
            "s2": np.array([[1.0]]),
        },
        "v1": {
            "s0": np.array([[0.5]]),
            "s1": np.array([[0.0]]),
            "s2": np.array([[0.0]]),
        },
    },
    announce_alice={"x0": "cA0"},
    announce_bob={"v0": "cB0", "v1": "cB0"},
    accept_statistic={("cA0", "cB0"): "chat0"},
    key_map={("x0", "v0"): 0, ("x0", "v1"): 1},
    key_holder="B",
    key_value_count=2,
    acceptance_values=("chat0",),
    chat_key=("chat0",),
    acceptance_set={"geometry": "singleton", "frequencies": (1.0,)},
    branches={
        "chat0": (
            SectorBranch(
                sector="s0",
                kraus=(np.array([[_HALF], [_HALF]]),),
                row_key_values=(0, 1),
            ),
            SectorBranch(
                sector="s1",
                kraus=(np.array([[1.0], [0.0]]),),
                row_key_values=(0, 1),
            ),
            SectorBranch(
                sector="s2",
                kraus=(np.array([[1.0], [0.0]]),),
                row_key_values=(0, 1),
            ),
        )
    },
    dense_branches={
        "chat0": DenseBranch(
            kraus=(
                np.array(
                    [
                        [_HALF, 0.0, 0.0],
                        [0.0, 1.0, 0.0],
                        [0.0, 0.0, 1.0],
                        [_HALF, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                    ]
                ),
            ),
            row_key_values=(0, 0, 0, 1, 1, 1),
            row_sectors=("s0", "s1", "s2", "s0", "s1", "s2"),
        )
    },
    statistics={"chat0": {"s0": 1.0, "s1": 1.0, "s2": 1.0}},
    sector_classes={
        "s0": "key-active",
        "s1": "constraint-active",
        "s2": "constraint-active",
    },
    state_blind={"s0": True, "s1": True, "s2": True},
    # s1 corrected False -> True; derivation in the docstring above.
    removable={"s0": False, "s1": True, "s2": True},
    constraint_list=(
        ToyConstraint(
            operator_blocks={
                "s0": np.array([[1.0]]),
                "s1": np.array([[0.0]]),
                "s2": np.array([[0.0]]),
            },
            relation="succeq",
            bound=np.array([[0.5]]),
            homogeneous_scalar=0.5,
        ),
    ),
    attack_set_license=None,
)


# ---------------------------------------------------------------------------
# TOY-7 -- a NON-homogeneous constraint list; part (i) of the two-part gate.
# ---------------------------------------------------------------------------

TOY7_NON_HOMOGENEOUS = ToyDeclaration(
    toy_id="TOY-7",
    summary=(
        "A two-dimensional Alice with a feasible but NOT tau_A-homogeneous "
        "constraint list. Numerically usable (h_low = 0); a key-length request "
        "must hard-fail on part (i) of the two-part gate."
    ),
    derivation="""\
Declaration: d_A = 2, tau_A = I/2; one one-dimensional sector s0, so
Pos(A x Q) = Pos(A) and the marginal condition omega_A = tau_A forces
omega = I/2 -- a single feasible point; X = {x0} with M_x0 = I_2 (a valid
one-element POVM); V = {v0} with F_v0 = [1]; trivial announcements, one class;
sifting FAILS, so r == perp and Chat_key = {} ; phi == chat0;
AcceptSet = {delta_chat0} = {Phi[omega]}; h = A.

Constraint list:  L = { (O_1, preceq, Theta_1) },  O_1 = [1] (identity on Q),
                  Theta_1 = diag(1, 1/2)  (Hermitian on A).
Feasibility: tr_Q[(1_A x O_1) omega] = omega_A = diag(1/2, 1/2) and
  diag(1, 1/2) - diag(1/2, 1/2) = diag(1/2, 0) >= 0, so the entry HOLDS and
  the feasible set is nonempty (Assumption A-DECL (vii)).
Homogeneity: Theta_1 = c * tau_A = c * diag(1/2, 1/2) would need c = 2 from the
  first diagonal entry and c = 1 from the second. No such c exists, so L is NOT
  tau_A-homogeneous (Definition def:homog).

Value: Chat_key is empty and q = Phi[omega], so O_alpha = 0 and h_low = 0 for
every alpha in (1, inf).

GATE: L is nonempty and non-homogeneous, so part (i) of the two-part gate fails
and NO key-length output may be emitted, whatever attack_set_license says and
whatever h_low is. "Numerical use outside the security chain is unrestricted"
(contract Section 2.1), so h_low = 0 is still a legitimate value to report.
""",
    alice_dim=2,
    alice_marginal=np.eye(2) / 2.0,
    sector_index_set=("s0",),
    sector_dims={"s0": 1},
    alice_povm={"x0": np.eye(2)},
    bob_povm={"v0": {"s0": np.array([[1.0]])}},
    announce_alice={"x0": "cA0"},
    announce_bob={"v0": "cB0"},
    accept_statistic={("cA0", "cB0"): "chat0"},
    key_map={("x0", "v0"): PERP},
    key_holder="A",
    key_value_count=1,
    acceptance_values=("chat0",),
    chat_key=(),
    acceptance_set={"geometry": "singleton", "frequencies": (1.0,)},
    branches={"chat0": ()},
    dense_branches={},
    statistics={"chat0": {"s0": 1.0}},
    sector_classes={"s0": "constraint-active"},
    state_blind={"s0": True},
    removable={"s0": False},
    constraint_list=(
        ToyConstraint(
            operator_blocks={"s0": np.array([[1.0]])},
            relation="preceq",
            bound=np.diag([1.0, 0.5]),
            homogeneous_scalar=None,
        ),
    ),
    attack_set_license=None,
)


ALL_TOYS: tuple[ToyDeclaration, ...] = (
    TOY1_RETENTION,
    TOY2_DETERMINISTIC,
    TOY2_AVERAGED,
    TOY3_DEPHASED_2,
    TOY3_DEPHASED_3,
    TOY3_DEPHASED_4,
    TOY4A_ZERO_GENERATION,
    TOY4B_DIVERGENCE_ONLY,
    TOY4C_INFEASIBLE,
    TOY5_CONSTRAINED,
    TOY6_REMOVABLE,
    TOY7_NON_HOMOGENEOUS,
)


# ===========================================================================
#  0.3.0 additions -- the untrusted source mode, the singular trusted
#  marginal, and the party partition.
# ===========================================================================
#
# Three of the seven are UNTRUSTED TWINS of frozen toys: the same declaration
# data with the marginal slot emptied. They exist to pin Remark
# rem:modes-da1 (b), which says that at d_A = 1 the two modes are not merely
# equivalent but THE SAME DECLARATION -- so the twin must reproduce its
# original's value to the last digit, and a difference is a defect. They are
# built with `dataclasses.replace` deliberately: the point is that nothing but
# the slot changes.


TOY1_UNTRUSTED = replace(
    TOY1_RETENTION,
    toy_id="TOY-1-UN",
    alice_marginal=NOMARG,
    summary=(
        "TOY-1 with the marginal slot emptied: the same declaration in "
        "UNTRUSTED-source mode. At d_A = 1 this is the same declaration, and "
        "h_low = 0 at every alpha, exactly as for TOY-1."
    ),
    derivation="""\
TOY-1 with tau_A = none (contract Def. def:declaration: the marginal slot is
typed S_=(A) disjoint-union {none}, and its value IS the source mode).

WHY THE VALUE CANNOT MOVE, by Remark rem:modes-da1 (b), at d_A = 1:
  (b1) the two feasible sets of Eq. eq:feas COINCIDE. Trusted mode asks
       omega_A = tau_A = [1]; untrusted mode asks tr omega = 1. For
       omega >= 0 on A x Q with d_A = 1 the A-marginal IS the 1x1 matrix
       tr omega, so the two conditions are literally the same condition, and
       both read: omega = diag(w0, w1), w_s >= 0, w0 + w1 = 1.
  (b2) A-MARG's n-round condition omega_{A_1^n} = tau_A^{tensor n} holds for
       EVERY normalized state (A_1^n is one-dimensional): VACUOUSLY SATISFIED
       in trusted mode, NOT ASSERTED in untrusted mode. Neither is a violation.
  (b3) the licensed classes coincide -- vacuous here, L = {}.
  (b5) A-SRC is vacuous: what it licenses is tr omega = 1. An implementation
       must not demand source_replacement_license from TOY-1 either.
The objective ingredients of Eq. eq:fK are functions of omega alone and no
step of Eq. eq:objective mentions tau_A, so

  h_low(TOY-1-UN) = h_low(TOY-1) = 0   for every alpha in (1, inf),

and dropping the constraint-active sector s1 raises it to exactly 1 bit in
both modes (Proposition prop:retention, whose own proof takes d_A = 1 and
notes the equivalence).
""",
)

TOY3_DEPHASED_2_UNTRUSTED = replace(
    TOY3_DEPHASED_2,
    toy_id="TOY-3(m=2)-UN",
    alice_marginal=NOMARG,
    summary=(
        "TOY-3(m=2) with the marginal slot emptied. h_low = log2(2) = 1 "
        "exactly, at every alpha, as in trusted-source mode."
    ),
    derivation="""\
TOY-3(m=2) with tau_A = none. The argument of TOY-1-UN applies verbatim: at
d_A = 1, Eq. eq:feas reads the same in both modes (Remark rem:modes-da1
(b1)), and here the feasible set is the SINGLE state omega = [1] in either
mode. So every ingredient of Eq. eq:fK is unchanged and

  h_low(TOY-3(m=2)-UN) = h_low(TOY-3(m=2)) = log2(2) = 1

at every alpha in (1, inf). This twin is worth having beside TOY-1-UN because
its value is NON-ZERO: a mode-handling bug that returned 0 everywhere would
pass the TOY-1 pair and fail here.
""",
)

TOY5_CONSTRAINED_UNTRUSTED = replace(
    TOY5_CONSTRAINED,
    toy_id="TOY-5-UN",
    alice_marginal=NOMARG,
    constraint_list=(
        ToyConstraint(
            operator_blocks={"s0": np.array([[1.0]]), "s1": np.array([[0.0]])},
            relation="succeq",
            # UNTRUSTED-source mode: Theta_1 is the REAL SCALAR c_1 = 1/2, not
            # the 1x1 matrix [1/2] (contract Def. def:declaration; A-DECL (vi);
            # def:homog (b)). The two spellings agree numerically at d_A = 1 and
            # are different TYPES, which is the whole content of the licensed
            # class in untrusted-source mode.
            bound=0.5,
            homogeneous_scalar=0.5,
        ),
    ),
    summary=(
        "TOY-5 with the marginal slot emptied and its constraint right-hand "
        "side retyped as the scalar c_1 = 1/2. Same feasible set, same "
        "alpha-dependent closed form as TOY-5."
    ),
    derivation="""\
TOY-5 with tau_A = none and the entry retyped for the mode.

THE ENTRY. Trusted-source mode declares (O_1, succeq, Theta_1) with the
OPERATOR right-hand side Theta_1 = c_1 tau_A = [1/2] and reads it as
  tr_Q[(1_A x O_1) omega] succeq Theta_1        (Def. def:homog (a)).
Untrusted-source mode declares (O_1, >=, c_1) with the SCALAR right-hand side
c_1 = 1/2 and reads it as
  tr[(1_A x O_1) omega] >= c_1                  (Def. def:homog (b)).
At d_A = 1 the left-hand sides are the same 1x1 number w0 and the right-hand
sides are the same number 1/2, so both spell w0 >= 1/2 (Remark rem:modes-da1
(b3): every 1x1 Hermitian Theta equals c tau_A with c = Theta). The feasible
set is therefore w0 in [1/2, 1] in both modes, exactly as for TOY-5.

VALUE. The objective is unchanged, so

  h_low(TOY-5-UN) = h_low(TOY-5)
                  = (1/(alpha-1)) log2( 2 / (1 + 2^{1-alpha}) )

for every alpha in (1, inf).

GATE. L is nonempty, so contract Section 2.1's two-part gate applies. Part (i)
-- "the list lies in the licensed class of the declared source mode" -- is
VACUOUSLY TRUE here (Remark rem:cgate): the mode is untrusted, so part (i)
degenerates from a mathematical condition to a type check that a well-formed
declaration passes by construction; at d_A = 1 it would in any case reject only
a `general` tag a producer can avoid. attack_set_license is None, so part (ii)
FAILS and no key-length output may be emitted. The registry freezes that
verdict as O-CGATE-DEGENERATE: a passing part (i) is evidence of nothing here.
[Aligned with the owner's reading of the gate at d_A = 1; no verdict moved.
This previously read "VACUOUSLY TRUE here twice over ... and d_A = 1 would make it vacuous
anyway".]
""",
)


# ---------------------------------------------------------------------------
# TOY-8 -- the trusted/untrusted PAIR at d_A = 2, where the modes differ.
# ---------------------------------------------------------------------------
#
# The d_A = 1 twins above cannot separate the modes, because at d_A = 1 they
# are the same declaration. TOY-8 is the smallest instance that CAN: a trusted
# marginal deletes every state whose A-marginal differs, and here that is the
# whole of the freedom the objective sees.

_TOY8_DERIVATION = """\
Declaration data shared by both modes:
  d_A = 2. One sector s0 with d_{s0} = 1, so H(A x Q) = C^2 and a
  sector-block-diagonal omega is just a state on A.
  X = {x0, x1} with M_x0 = diag(1, 0), M_x1 = diag(0, 1)  (sum = 1_A).
  V = {v0} with F^{(s0)}_v0 = [1]                          (sum = 1_Q).
  a_A(x0) = cA0, a_A(x1) = cA1, a_B(v0) = cB0; phi(cA0, cB0) = chat0,
  phi(cA1, cB0) = chat1, so Chat = {chat0, chat1}.
  Sifting FAILS in both classes: r == perp, Chat_key = {} (Eq. eq:chkey), and
  by Lemma lem:branch-maps (iv) every branch map G_chat is 0. Party computability
  (A-DECL (viii)) holds for either holder because r is constant; h = A.
  AcceptSet = { (1/2, 1/2) }, a singleton.
  L = {} (empty), so no constraint gate applies in either mode.

Statistics. Phi[omega](chat) = sum_s tr[Gamma^{(s)}_chat omega_s] with
Gamma^{(s0)}_chat0 = M_x0 x F_v0 = diag(1, 0) and Gamma^{(s0)}_chat1 =
diag(0, 1) (Eq. eq:Phimap; the same operators Eq. eq:grad-pieces-un names).
So Phi[omega] = (omega_00, omega_11) -- the diagonal of omega.

Objective. Chat_key is empty, so Eq. eq:objective is the pure KL penalty
  O_alpha(q, omega) = (alpha/(alpha-1)) D( q || Phi[omega] ).
It depends on omega only through diag(omega); every omega >= 0 with
tr omega = 1 has diag(omega) = (p, 1-p) for some p in [0, 1], and every such
pair is realized by diag(p, 1-p). So the infimum over the feasible set is the
infimum over that one parameter, whichever mode restricts it.
"""

TOY8_TRUSTED_MARGINAL = ToyDeclaration(
    toy_id="TOY-8-T",
    summary=(
        "d_A = 2 with the trusted marginal tau_A = diag(7/8, 1/8), which "
        "pins the only degree of freedom the objective sees. h_low = "
        "(alpha/(alpha-1)) (2 - (1/2) log2 7) > 0."
    ),
    derivation=_TOY8_DERIVATION
    + """
TRUSTED-SOURCE MODE. tau_A = diag(7/8, 1/8) is declared, and
source_replacement_license is supplied (contract Section 2.1: the record is
REQUIRED whenever alice_marginal is present, and d_A = 2 > 1 so it is not
vacuous). Eq. eq:feas adds omega_A = tau_A, which on a one-dimensional Q is
omega = tau_A: the feasible set is a SINGLE POINT. Hence
  Phi[omega] = (7/8, 1/8)
is fixed, and
  D( (1/2, 1/2) || (7/8, 1/8) )
    = (1/2) log2( (1/2)/(7/8) ) + (1/2) log2( (1/2)/(1/8) )
    = (1/2) log2(4/7) + (1/2) log2(4)
    = (1/2)(2 - log2 7) + 1
    = 2 - (1/2) log2 7
    = 0.596322538971198...        (log2 7 = 2.807354922057604...)
so
  h_low(TOY-8-T) = (alpha/(alpha-1)) (2 - (1/2) log2 7)
for every alpha in (1, inf). It is POSITIVE because q is not the declared
marginal's statistics -- the declaration says the source produces (7/8, 1/8)
and the acceptance set insists on (1/2, 1/2), so every accepted run costs the
divergence between them.
""",
    alice_dim=2,
    alice_marginal=np.diag([0.875, 0.125]),
    sector_index_set=("s0",),
    sector_dims={"s0": 1},
    alice_povm={"x0": np.diag([1.0, 0.0]), "x1": np.diag([0.0, 1.0])},
    bob_povm={"v0": {"s0": np.array([[1.0]])}},
    announce_alice={"x0": "cA0", "x1": "cA1"},
    announce_bob={"v0": "cB0"},
    accept_statistic={("cA0", "cB0"): "chat0", ("cA1", "cB0"): "chat1"},
    key_map={("x0", "v0"): PERP, ("x1", "v0"): PERP},
    key_holder="A",
    key_value_count=1,
    acceptance_values=("chat0", "chat1"),
    chat_key=(),
    acceptance_set={"geometry": "singleton", "frequencies": (0.5, 0.5)},
    branches={"chat0": (), "chat1": ()},
    dense_branches={},
    statistics={},
    statistics_operators={
        "chat0": {"s0": np.diag([1.0, 0.0])},
        "chat1": {"s0": np.diag([0.0, 1.0])},
    },
    sector_classes={"s0": "constraint-active"},
    state_blind={"s0": True},
    removable={"s0": False},
    source_replacement_license={"certificate": "supplied by proof-reductions"},
)

TOY8_UNTRUSTED = replace(
    TOY8_TRUSTED_MARGINAL,
    toy_id="TOY-8-UN",
    alice_marginal=NOMARG,
    source_replacement_license=None,
    summary=(
        "TOY-8 with the marginal slot emptied. The adversary now prepares A "
        "as well, the accepted statistics become reachable, and h_low drops "
        "to exactly 0 at every alpha."
    ),
    derivation=_TOY8_DERIVATION
    + """
UNTRUSTED-SOURCE MODE. tau_A = none, so Eq. eq:feas carries only tr omega = 1
(Eq. eq:feas-modes, untrusted row) and there is no source_replacement_license
to supply -- A-SRC is not asserted and A-MARG is NOT ASSERTED either (not
violated; the ledger row distinguishes the two). Phi[omega] = (p, 1-p) now
ranges over the whole probability simplex on Chat, so
  inf_{omega in Feas} D( (1/2, 1/2) || Phi[omega] ) = 0,
attained at omega = diag(1/2, 1/2), and
  h_low(TOY-8-UN) = 0
for every alpha in (1, inf).

WHAT THE PAIR PINS. Remark transmitter/rem:source-mode (a) proves that every omega
feasible in trusted-source mode is feasible in untrusted-source mode, so the
untrusted feasible set is the larger and its infimum the smaller:
  h_low(untrusted) <= h_low(trusted)   ALWAYS.
TOY-8 shows the inequality is STRICT, by exactly
  (alpha/(alpha-1)) (2 - (1/2) log2 7) > 0,
so dropping the marginal is the CONSERVATIVE direction and can never turn an
unsound declaration into a sound-looking one. The converse move -- declaring a
tau_A without the attestation of A-SRC -- overstates the key by that same
amount here, which is why Section 4.19 gates it fail-closed.
""",
)


# ---------------------------------------------------------------------------
# TOY-9 -- a SINGULAR trusted marginal: F-01-01, closed at 0.2.5/0.3.0.
# ---------------------------------------------------------------------------

TOY9_SINGULAR_MARGINAL = ToyDeclaration(
    toy_id="TOY-9",
    summary=(
        "d_A = 3 with the SINGULAR marginal tau_A = diag(3/4, 1/4, 0), so "
        "rank(tau_A) = 2 < 3 = d_A and the Choi input register A_0 is a "
        "proper subspace. h_low = (alpha/(alpha-1)) (1/2) log2 3."
    ),
    derivation="""\
Declaration:
  d_A = 3, tau_A = diag(3/4, 1/4, 0). This is a legal marginal slot value:
  tau_A >= 0 and tr tau_A = 1 (Assumption A-DECL (ii)), and contract
  Section 2.1 says in so many words that "a SINGULAR tau_A is admissible" and
  that an implementation "must not refuse a singular tau_A on the ground that
  the contract names no canonical basis, because the contract deliberately
  names none". source_replacement_license is supplied (d_A = 3 > 1, so
  A-SRC is not vacuous).
  One sector s0 with d_{s0} = 2, so H(A x Q) = C^3 x C^2 = C^6.
  X = {x0, x1} with M_x0 = |e0><e0|, M_x1 = |e1><e1| + |e2><e2| (sum = 1_A).
  V = {v0} with F^{(s0)}_v0 = 1_{Q_s0} = I_2 (sum = 1_Q; s0 is state-blind).
  a_A(x0) = cA0, a_A(x1) = cA1, a_B(v0) = cB0; phi(cA0, cB0) = chat0,
  phi(cA1, cB0) = chat1. Sifting FAILS: r == perp, Chat_key = {}, h = A.
  AcceptSet = { (1/4, 3/4) }, a singleton. L = {} (empty).

VALUE. Gamma^{(s0)}_chat0 = M_x0 x I_2 and Gamma^{(s0)}_chat1 = M_x1 x I_2, so
  Phi[omega](chat) = tr[(M_x x 1_Q) omega] = tr[M_x omega_A],
which depends on omega ONLY through its A-marginal. In trusted-source mode
that marginal is pinned to tau_A, so
  Phi[omega] = (tr[M_x0 tau_A], tr[M_x1 tau_A]) = (3/4, 1/4)
for EVERY feasible omega, and with Chat_key empty the objective is the
constant
  O_alpha = (alpha/(alpha-1)) D( (1/4, 3/4) || (3/4, 1/4) )
          = (alpha/(alpha-1)) [ (1/4) log2((1/4)/(3/4))
                              + (3/4) log2((3/4)/(1/4)) ]
          = (alpha/(alpha-1)) [ -(1/4) log2 3 + (3/4) log2 3 ]
          = (alpha/(alpha-1)) (1/2) log2 3
          = (alpha/(alpha-1)) * 0.7924812503605781...
Hence h_low(TOY-9) = (alpha/(alpha-1)) (1/2) log2 3, and it is INDEPENDENT of
which feasible omega is chosen -- which is what makes it a clean invariance
target below.

THE CHOI INPUT REGISTER. d_{A_0} = rank(tau_A) = 2 and supp(tau_A) =
span{e0, e1}, a PROPER subspace of C^3. Eq. eq:iota asks for an isometry
iota : A_0 -> A with iota^dagger iota = 1_{A_0} and iota iota^dagger =
Pi_{supp tau_A}; the contract names no canonical one and Remark
rem:basis-invariance proves the choice immaterial. Two admissible choices are
frozen below as TOY9_IOTA_1 and TOY9_IOTA_2, together with the feasible state
TOY9_OMEGA and the two Choi coordinates TOY9_J_1, TOY9_J_2 it has in them.

  W_tau = tau_A^{1/2} iota  (Eq. eq:Wtau),  W_tau^+ = (W^dagger W)^{-1} W^dagger,
  J = (W_tau^+ x 1) omega (W_tau^{+dagger} x 1),
  chi(J) = (W_tau x 1) J (W_tau^dagger x 1)     (Lemma lem:choi-marginal).

  iota_1 = [e0, e1]:      W_1 = [[sqrt3/2, 0], [0, 1/2], [0, 0]],
                          W_1^+ = [[2/sqrt3, 0, 0], [0, 2, 0]],
                          J_1 = |f0><f0| x |0><0| + |f1><f1| x |1><1|.
  iota_2 = [(e0+e1)/sqrt2, (e0-e1)/sqrt2] = iota_1 H, H the 2x2 Hadamard
                          (unitary, so iota_2 is admissible by Eq. eq:iota):
                          W_2 = W_1 H, W_2^+ = H^dagger W_1^+, and
                          J_2 = (H^dagger x 1) J_1 (H x 1)
                              = (1/2) [[1,1],[1,1]] x |0><0|
                              + (1/2) [[1,-1],[-1,1]] x |1><1|.

  BOTH satisfy the coupling constraint of Eq. eq:choi-feas,
  sum_s tr_{Q_s} J_s = 1_{A_0} = I_2, and BOTH satisfy chi(J) = omega. They
  are DIFFERENT MATRICES (J_1 is diagonal, J_2 is not), which is exactly the
  content of Remark rem:basis-invariance: the reported J_s are relative to the
  declared basis, while h_low, key_length and sector_report are not. That is
  why contract Section 2.5 requires the implementation to RECORD the iota it
  used, as optimizer_certificate.choi_input_basis, whenever
  rank(tau_A) < d_A -- which is the case here and is not the case for any
  other toy in this registry.
""",
    alice_dim=3,
    alice_marginal=np.diag([0.75, 0.25, 0.0]),
    sector_index_set=("s0",),
    sector_dims={"s0": 2},
    alice_povm={
        "x0": np.diag([1.0, 0.0, 0.0]),
        "x1": np.diag([0.0, 1.0, 1.0]),
    },
    bob_povm={"v0": {"s0": np.eye(2)}},
    announce_alice={"x0": "cA0", "x1": "cA1"},
    announce_bob={"v0": "cB0"},
    accept_statistic={("cA0", "cB0"): "chat0", ("cA1", "cB0"): "chat1"},
    key_map={("x0", "v0"): PERP, ("x1", "v0"): PERP},
    key_holder="A",
    key_value_count=1,
    acceptance_values=("chat0", "chat1"),
    chat_key=(),
    acceptance_set={"geometry": "singleton", "frequencies": (0.25, 0.75)},
    branches={"chat0": (), "chat1": ()},
    dense_branches={},
    statistics={},
    statistics_operators={
        "chat0": {"s0": np.kron(np.diag([1.0, 0.0, 0.0]), np.eye(2))},
        "chat1": {"s0": np.kron(np.diag([0.0, 1.0, 1.0]), np.eye(2))},
    },
    sector_classes={"s0": "constraint-active"},
    state_blind={"s0": True},
    removable={"s0": False},
    source_replacement_license={"certificate": "supplied by proof-reductions"},
)

#: Two admissible declared isometries ``iota : A_0 -> A`` for TOY-9's singular
#: ``tau_A`` (contract Eq. ``eq:iota``). Hand-authored literals, like the branch
#: Kraus operators: constructing ``iota`` from a declaration is solver-side work.
TOY9_IOTA_1: Matrix = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
TOY9_IOTA_2: Matrix = np.array(
    [[_HALF, _HALF], [_HALF, -_HALF], [0.0, 0.0]],
)

#: A feasible point of TOY-9: correlated across ``A`` and ``Q_s0``, so that the
#: two declared bases give genuinely different Choi coordinates. ``omega_A =
#: diag(3/4, 1/4, 0) = tau_A`` and ``tr omega = 1``.
TOY9_OMEGA: Matrix = 0.75 * np.kron(
    np.diag([1.0, 0.0, 0.0]), np.diag([1.0, 0.0])
) + 0.25 * np.kron(np.diag([0.0, 1.0, 0.0]), np.diag([0.0, 1.0]))

#: The Choi coordinates of :data:`TOY9_OMEGA` in the two declared bases,
#: written out by hand. Both satisfy ``tr_{Q_s0} J = 1_{A_0}``, both satisfy
#: ``chi(J) = omega``, and they are different matrices.
TOY9_J_1: Matrix = np.kron(np.diag([1.0, 0.0]), np.diag([1.0, 0.0])) + np.kron(
    np.diag([0.0, 1.0]), np.diag([0.0, 1.0])
)
TOY9_J_2: Matrix = 0.5 * np.kron(
    np.array([[1.0, 1.0], [1.0, 1.0]]), np.diag([1.0, 0.0])
) + 0.5 * np.kron(np.array([[1.0, -1.0], [-1.0, 1.0]]), np.diag([0.0, 1.0]))


# ---------------------------------------------------------------------------
# TOY-10 -- the d_A = 1 EMBEDDING with a non-default party partition.
# ---------------------------------------------------------------------------

TOY10_EMBEDDED_PARTITION = PartyPartition(
    readout_alice={
        ("x0", "v00"): "a0",
        ("x0", "v01"): "a0",
        ("x0", "v10"): "a1",
        ("x0", "v11"): "a1",
    },
    readout_bob={
        ("x0", "v00"): "b0",
        ("x0", "v01"): "b1",
        ("x0", "v10"): "b0",
        ("x0", "v11"): "b1",
    },
    alphabet_alice=("a0", "a1"),
    alphabet_bob=("b0", "b1"),
    party_of_alice_system="A",
    party_of_sector_factors={"s0": ("A", "B"), "s1": ("A", "B")},
    is_default=False,
)

TOY10_EMBEDDED = ToyDeclaration(
    toy_id="TOY-10",
    summary=(
        "The d_A = 1 embedding of Remark rem:modes-da1 (b): a protocol with "
        "no trusted source, declared in untrusted-source mode with BOTH "
        "parties' outcome components inside v and a non-default party "
        "partition naming who holds which. h_low = 0, as for TOY-1."
    ),
    derivation="""\
Declaration:
  d_A = 1 and tau_A = none (untrusted-source mode). The register A is trivial;
  X = {x0} with M_x0 = [1].
  Q = Q_s0 (+) Q_s1, both one-dimensional. Each carries a declared tensor
  factorization H(Q_s) = H(Q_{s,A}) x H(Q_{s,B}) with both factors
  one-dimensional, labelled A and B respectively (part (b) of the party
  partition). That is not a degenerate reading: contract Section 1.1, design
  decision 1, says private per-round coins of known bias "are absorbed into
  the POVM elements ... never modelled as a separate trusted register", so a
  one-dimensional factor whose party reads a coin of declared bias is exactly
  how this contract carries a party's private randomness.
  V = {v00, v01, v10, v11}: the joint outcome carries Alice's component a and
  Bob's component b. The POVM elements factor accordingly --
    F^{(s0)}_{v_ab} = 1/4 = (1/2)(1/2)   : both coins fair on s0;
    F^{(s1)}_{v_ab} = [a = 0] * (1/2)    : Alice's coin deterministic on s1,
                                           Bob's fair.
  POVM completeness per sector: sum_v F^{(s0)}_v = 4 * 1/4 = 1 and
  sum_v F^{(s1)}_v = 1/2 + 1/2 + 0 + 0 = 1.
  Announcements are trivial: a_A(a0) = a_A(a1) = cA0 and a_B(b0) = a_B(b1) =
  cB0, one class kappa0, sifting always passes, phi == chat0,
  Chat = Chat_key = {chat0}, AcceptSet = {delta_chat0}.
  Raw key r(x0, v_ab) = a, so Z = {0, 1} and d_Z = 2.

PARTY PARTITION (part (a), the only part any derivation consumes):
  pi_A(x0, v_ab) = a  onto O_A = {a0, a1};
  pi_B(x0, v_ab) = b  onto O_B = {b0, b1}.
  Both readouts are total, and both announcement maps are defined on the
  party's own readout alphabet, as A-DECL (viii) requires.

KEY HOLDER, and why (viii) had to widen. r(x0, v_ab) = a factors through
Alice's readout: r = r_A(pi_A(x, v), a(x, v)) with r_A(a0, .) = 0 and
r_A(a1, .) = 1. So h = A is ADMISSIBLE. It does NOT factor through Bob's
readout: pi_B(x0, v00) = pi_B(x0, v10) = b0 while r(x0, v00) = 0 and
r(x0, v10) = 1, so no function of (pi_B, a) can produce r. So h = B is
INADMISSIBLE. Under the superseded 0.2.x reading of (viii) -- "r is a function
of the holder's own OUTCOME (x, v)" -- h = B would have passed, because r IS a
function of v; and the contract says exactly this: that reading "would make it
vacuous for any declaration that places both parties' data in v", which is the
declaration shape here. A-DECL (viii) is what makes the error-correction and
verification steps of Theorem thm:keylength physically executable, so the
distinction is not cosmetic.

BRANCH KRAUS, by hand from Eq. eq:kraus with the single pass class kappa0. The
surviving output rows are indexed by v; row v carries R = r(x0, v) = a(v), so
  row_key_values = (0, 0, 1, 1)  in the order (v00, v01, v10, v11).
    s0: column (1/2, 1/2, 1/2, 1/2)^T          (norm^2 = 1)
    s1: column (1/sqrt2, 1/sqrt2, 0, 0)^T      (norm^2 = 1)

OBJECTIVE on omega = diag(w0, w1), w0 + w1 = 1 -- which in untrusted-source
mode is Eq. eq:feas's tr omega = 1 and nothing else:
  Sector s0: G(w0) = w0 |eta><eta|, |eta> = (1,1,1,1)/2. Z keeps the two 2x2
    diagonal blocks (rows {v00, v01} carry key 0, rows {v10, v11} carry key 1),
    each equal to (1/4) * ones(2,2) with eigenvalues (1/2, 0). So
    Z(G^{1/alpha}) = w0^{1/alpha} * [eigenvalues 1/2, 1/2, 0, 0] and
    T_{chat0,s0} = w0 * 2 * 2^{-alpha} = w0 * 2^{1-alpha};
    tr G = w0, hence f_{chat0,s0}(w0) = w0 (2^{1-alpha} - 1).
  Sector s1: G(w1) = w1 |xi><xi|, |xi> = (1,1,0,0)/sqrt2, supported entirely in
    the key-0 block, so Z acts as the identity on it and T = w1 = tr G, giving
    f_{chat0,s1} == 0. Consistent with C7: (chat0, s1) is key-inert, its
    effective outcome set being {(x0, v00), (x0, v01)}, on which r = 0.
  P_chat0 = w0 * 1 + w1 * 1 = 1, so K = 1 + w0 (2^{1-alpha} - 1) and
  O_alpha = (1/(alpha-1)) log2(1 / K), minimized at w0 = 0:

    h_low(TOY-10) = 0 for every alpha in (1, inf),

the same value TOY-1 carries -- the same protocol, declared the 0.3.0 way.
Forcing the constraint-active sector s1 to zero (w0 = 1) again gives exactly
1 bit, so the retention statement of Proposition prop:retention survives the
re-declaration unchanged.
""",
    alice_dim=1,
    alice_marginal=NOMARG,
    sector_index_set=("s0", "s1"),
    sector_dims={"s0": 1, "s1": 1},
    alice_povm={"x0": np.array([[1.0]])},
    bob_povm={
        "v00": {"s0": np.array([[0.25]]), "s1": np.array([[0.5]])},
        "v01": {"s0": np.array([[0.25]]), "s1": np.array([[0.5]])},
        "v10": {"s0": np.array([[0.25]]), "s1": np.array([[0.0]])},
        "v11": {"s0": np.array([[0.25]]), "s1": np.array([[0.0]])},
    },
    announce_alice={"a0": "cA0", "a1": "cA0"},
    announce_bob={"b0": "cB0", "b1": "cB0"},
    accept_statistic={("cA0", "cB0"): "chat0"},
    key_map={
        ("x0", "v00"): 0,
        ("x0", "v01"): 0,
        ("x0", "v10"): 1,
        ("x0", "v11"): 1,
    },
    key_holder="A",
    key_value_count=2,
    acceptance_values=("chat0",),
    chat_key=("chat0",),
    acceptance_set={"geometry": "singleton", "frequencies": (1.0,)},
    branches={
        "chat0": (
            SectorBranch(
                sector="s0",
                kraus=(np.array([[0.5], [0.5], [0.5], [0.5]]),),
                row_key_values=(0, 0, 1, 1),
            ),
            SectorBranch(
                sector="s1",
                kraus=(np.array([[_HALF], [_HALF], [0.0], [0.0]]),),
                row_key_values=(0, 0, 1, 1),
            ),
        )
    },
    dense_branches={
        # Rows (v, q) in the order (v00,s0), (v00,s1), (v01,s0), (v01,s1),
        # (v10,s0), (v10,s1), (v11,s0), (v11,s1);
        # entry [(v,q), q'] = delta_{q,q'} sqrt(F^{(q)}_v).
        "chat0": DenseBranch(
            kraus=(
                np.array(
                    [
                        [0.5, 0.0],
                        [0.0, _HALF],
                        [0.5, 0.0],
                        [0.0, _HALF],
                        [0.5, 0.0],
                        [0.0, 0.0],
                        [0.5, 0.0],
                        [0.0, 0.0],
                    ]
                ),
            ),
            row_key_values=(0, 0, 0, 0, 1, 1, 1, 1),
            row_sectors=("s0", "s1", "s0", "s1", "s0", "s1", "s0", "s1"),
        )
    },
    statistics={"chat0": {"s0": 1.0, "s1": 1.0}},
    sector_classes={"s0": "key-active", "s1": "constraint-active"},
    state_blind={"s0": True, "s1": True},
    # Neither is removable, for the two different reasons of Thm. thm:removal:
    # s0 fails (RM1) -- the only other sector responds (1/2, 1/2, 0, 0) and no
    # convex combination of that gives 1/4 on v10 -- and s1 fails (RM2), the
    # only available target sector s0 being key-active.
    removable={"s0": False, "s1": False},
    party_partition=TOY10_EMBEDDED_PARTITION,
)


#: The seven declarations added for the 0.3.0 material. Kept apart from
#: :data:`ALL_TOYS` because the 0.1.0 operator-bundle manifest cannot serialize
#: them yet; see this module's docstring.
SOURCE_MODE_TOYS: tuple[ToyDeclaration, ...] = (
    TOY1_UNTRUSTED,
    TOY3_DEPHASED_2_UNTRUSTED,
    TOY5_CONSTRAINED_UNTRUSTED,
    TOY8_TRUSTED_MARGINAL,
    TOY8_UNTRUSTED,
    TOY9_SINGULAR_MARGINAL,
    TOY10_EMBEDDED,
)

#: Every declaration the 0.3.0 freeze knew, in either group.
ALL_TOYS_0_3_0: tuple[ToyDeclaration, ...] = ALL_TOYS + SOURCE_MODE_TOYS


# ---------------------------------------------------------------------------
# CERT-TOY-3REL -- the three relation symbols of Assumption A-DECL (vi) in one
# declaration, in both source modes. New at contract_version 0.4.0.
# ---------------------------------------------------------------------------
#
# WHY A NEW DECLARATION EXISTS AT ALL. Theorem ``thm:weak-duality`` (C19)
# partitions the constraint index set by relation symbol and gives each part
# its own dual term and its own sign in the slack Eq. ``eq:slack-tr`` /
# ``eq:slack-un``. No frozen toy carries an ``eq`` entry -- TOY-5 and TOY-6
# carry ``succeq``, TOY-7 carries ``preceq`` -- so no frozen toy can exercise
# the equality branch, whose dual variable is the one the theorem leaves
# UNRESTRICTED IN SIGN. This pair supplies one declaration with all three, once
# per source mode, so that the sign conventions are pinned rather than assumed.
#
# THE DECLARATION, shared by both modes:
#   d_A = 1, M_x0 = [1]; three one-dimensional sectors s0, s1, s2, so
#   Pos(A x Q) is the diagonal w = (w0, w1, w2) >= 0;
#   V = {v0} with F^{(s)}_v0 = [1] on each sector (POVM completeness per
#   sector, Assumption A-DECL (iii));
#   trivial announcements, one class; sifting FAILS, so r == perp,
#   Chat_key = {} and every branch map is empty (Definition def:branch);
#   phi == chat0; AcceptSet = {delta_chat0} = {Phi[omega]}; h = A.
# Because Chat_key is empty the objective Eq. eq:objective is the pure KL
# penalty and h_low = 0 at every alpha, in either mode. That is DELIBERATE:
# these toys exist for the LINEAR SUBPROBLEM mu(G) of Eq. eq:linsub, which
# depends on the feasible set alone and on nothing else in the declaration.
#
# THE CONSTRAINT LIST, three entries, one per relation symbol:
#   k = 1  (Pi_s0, succeq, c_1 = 1/4)   ->  w0 >= 1/4
#   k = 2  (Pi_s1, preceq, c_2 = 1/2)   ->  w1 <= 1/2
#   k = 3  (Pi_s2, eq,     c_3 = 1/8)   ->  w2 = 1/8
# Every operator is a sector projector, hence Hermitian and
# sector-block-diagonal (A-DECL (iii)). Feasibility (A-DECL (vii)): the point
# w = (3/8, 1/2, 1/8) satisfies all three, so the feasible set is nonempty --
# written out, it is
#   Feas = { (7/8 - w1, w1, 1/8) : w1 in [0, 1/2] } ,
# because w2 = 1/8 and the normalization force w0 = 7/8 - w1, and
# w0 >= 1/4 is then w1 <= 5/8, which the entry k = 2 already implies.
#
# THE TWO MODES. At d_A = 1 every Hermitian Theta on A is a scalar multiple of
# tau_A = [1] (Remark rem:modes-da1 (b3)), so the SAME three numbers are
# spelled as the operators Theta_k = c_k tau_A in trusted-source mode and as
# the real scalars c_k in untrusted-source mode -- different TYPES, the same
# feasible set. Theorem thm:weak-duality's closing sentence says the trusted
# bound (i) then reduces to the untrusted bound (ii), with the scalar
# Upsilon = [u] merging into y_0; the registry entries O-WEAK-DUALITY-TRUSTED
# and O-WEAK-DUALITY-UNTRUSTED freeze the SAME number 1/8 through the two
# formulas, which is what pins that reduction.
#
# attack_set_license is None in both, exactly as for TOY-5 and TOY-7: the list
# is nonempty, so part (ii) of the two-part gate of Section 2.1 fails and no
# key-length output may be emitted from either. Nothing here needs one -- the
# certificate's beta_feas is a numerical quantity, and "numerical use outside
# the security chain is unrestricted".

_CERT_3REL_SHARED = """\
Declaration (d_A = 1; three one-dimensional sectors s0, s1, s2):
  M_x0 = [1]; V = {v0} with F^{(s)}_v0 = [1] for every s; one announcement
  class; sifting FAILS (r == perp), so Chat_key = {} and every branch map is
  empty; phi == chat0; AcceptSet = {delta_chat0}; key_holder h = A.
  Pos(A x Q) is the diagonal w = (w0, w1, w2) >= 0 and Phi[omega](chat0) =
  w0 + w1 + w2 = tr omega.

Constraint list, ONE ENTRY PER RELATION SYMBOL of Assumption A-DECL (vi):
  k = 1   (Pi_s0, succeq, 1/4)    ->   w0 >= 1/4
  k = 2   (Pi_s1, preceq, 1/2)    ->   w1 <= 1/2
  k = 3   (Pi_s2, eq,     1/8)    ->   w2 = 1/8

Feasible set (Eq. eq:feas), after eliminating w0 = 1 - w1 - w2:
  Feas = { diag(7/8 - w1, w1, 1/8) : w1 in [0, 1/2] } ,
nonempty (A-DECL (vii)) -- e.g. w = (3/8, 1/2, 1/8) -- and the entry k = 1 is
implied by k = 2 on it, which is why a dual witness may take Lambda_1 = 0.

Objective: Chat_key is empty and q = Phi[omega] on every feasible point, so
Eq. eq:objective reduces to the KL penalty at coinciding arguments and
h_low = 0 for every alpha in (1, inf), in either source mode. These toys are
NOT here for h_low: they are here for the linear subproblem mu(G) of
Eq. eq:linsub, which sees only Feas.

THE LINEAR SUBPROBLEM the registry freezes, at the exact machine surrogate
G = (G_s0, G_s1, G_s2) = (1, -1, 2) (1 x 1 blocks):
  sum_s tr[G_s omega_s] = (7/8 - w1) - w1 + 1/4 = 9/8 - 2 w1 ,
decreasing in w1, so the minimum sits at the boundary w1 = 1/2:
  mu(G) = 9/8 - 1 = 1/8 , attained at w = (3/8, 1/2, 1/8).
That is the number Theorem thm:weak-duality must not exceed, and the entries
O-WEAK-DUALITY-TRUSTED / O-WEAK-DUALITY-UNTRUSTED exhibit witnesses attaining
it in both modes.

GATE: L is nonempty and attack_set_license is None, so part (ii) of the
two-part gate of Section 2.1 fails and NO key-length output may be emitted.
Numerical use outside the security chain is unrestricted, which is the only
use made of these toys.
"""

_CERT_3REL_COMMON: dict[str, Any] = {
    "alice_dim": 1,
    "sector_index_set": ("s0", "s1", "s2"),
    "sector_dims": {"s0": 1, "s1": 1, "s2": 1},
    "alice_povm": {"x0": np.array([[1.0]])},
    "bob_povm": {
        "v0": {
            "s0": np.array([[1.0]]),
            "s1": np.array([[1.0]]),
            "s2": np.array([[1.0]]),
        }
    },
    "announce_alice": {"x0": "cA0"},
    "announce_bob": {"v0": "cB0"},
    "accept_statistic": {("cA0", "cB0"): "chat0"},
    "key_map": {("x0", "v0"): PERP},
    "key_holder": "A",
    "key_value_count": 1,
    "acceptance_values": ("chat0",),
    "chat_key": (),
    "acceptance_set": {"geometry": "singleton", "frequencies": (1.0,)},
    "branches": {"chat0": ()},
    "dense_branches": {},
    "statistics": {"chat0": {"s0": 1.0, "s1": 1.0, "s2": 1.0}},
    "sector_classes": {
        "s0": "constraint-active",
        "s1": "constraint-active",
        "s2": "constraint-active",
    },
    "state_blind": {"s0": True, "s1": True, "s2": True},
    "removable": {"s0": False, "s1": False, "s2": False},
    "attack_set_license": None,
}

CERT_TOY_3REL_TRUSTED = ToyDeclaration(
    toy_id="CERT-TOY-3REL-T",
    summary=(
        "TRUSTED-source mode, d_A = 1, three one-dimensional sectors and one "
        "constraint of each relation symbol (succeq, preceq, eq). Exercises "
        "Theorem thm:weak-duality (i) with all three dual terms; mu(G) = 1/8."
    ),
    derivation=_CERT_3REL_SHARED
    + """
TRUSTED-SOURCE MODE. tau_A = [1] is declared. Assumption A-SRC's attestation
is VACUOUS at d_A = 1 and "must not be demanded" (Remark rem:modes-da1
(b5)), so source_replacement_license is None -- the same reading TOY-5 and
TOY-7 already carry. The marginal condition omega_A = tau_A reads tr omega = 1
here, which is Eq. eq:feas's normalization, so the feasible set is the one
above.

Each right-hand side is the OPERATOR Theta_k = c_k tau_A = [c_k], and the list
is tau_A-HOMOGENEOUS (Definition def:homog (a)) with c = (1/4, 1/2, 1/8),
because at d_A = 1 every Hermitian Theta on A is a scalar multiple of tau_A.
So part (i) of the two-part gate passes -- vacuously, per Remark rem:cgate,
and the registry records that a passing part (i) is evidence of nothing here.

WEAK DUALITY, Theorem thm:weak-duality (i) with Upsilon = [u], Lambda_k =
[lambda_k] (all 1 x 1 at d_A = 1):
  S_s0 = 1 - y_0 - u - lambda_1 ,
  S_s1 = -1 - y_0 - u + lambda_2 ,
  S_s2 = 2 - y_0 - u - lambda_3 ,
  bound = y_0 + u + lambda_1/4 - lambda_2/2 + lambda_3/8 .
Only the SUM t = y_0 + u appears, which is exactly the reduction Theorem
thm:weak-duality states for d_A = 1 -- "Upsilon = [u] is a scalar merging with
y_0 and (i) reduces to (ii)". The registry's witness takes y_0 = 0, u = 1,
lambda = (0, 2, 1) and attains mu(G) = 1/8.
""",
    alice_marginal=np.array([[1.0]]),
    source_replacement_license=None,
    constraint_list=(
        ToyConstraint(
            operator_blocks={
                "s0": np.array([[1.0]]),
                "s1": np.array([[0.0]]),
                "s2": np.array([[0.0]]),
            },
            relation="succeq",
            bound=np.array([[0.25]]),
            homogeneous_scalar=0.25,
        ),
        ToyConstraint(
            operator_blocks={
                "s0": np.array([[0.0]]),
                "s1": np.array([[1.0]]),
                "s2": np.array([[0.0]]),
            },
            relation="preceq",
            bound=np.array([[0.5]]),
            homogeneous_scalar=0.5,
        ),
        ToyConstraint(
            operator_blocks={
                "s0": np.array([[0.0]]),
                "s1": np.array([[0.0]]),
                "s2": np.array([[1.0]]),
            },
            relation="eq",
            bound=np.array([[0.125]]),
            homogeneous_scalar=0.125,
        ),
    ),
    **_CERT_3REL_COMMON,
)

CERT_TOY_3REL_UNTRUSTED = replace(
    CERT_TOY_3REL_TRUSTED,
    toy_id="CERT-TOY-3REL-UN",
    alice_marginal=NOMARG,
    constraint_list=(
        ToyConstraint(
            operator_blocks={
                "s0": np.array([[1.0]]),
                "s1": np.array([[0.0]]),
                "s2": np.array([[0.0]]),
            },
            relation="succeq",
            bound=0.25,
            homogeneous_scalar=0.25,
        ),
        ToyConstraint(
            operator_blocks={
                "s0": np.array([[0.0]]),
                "s1": np.array([[1.0]]),
                "s2": np.array([[0.0]]),
            },
            relation="preceq",
            bound=0.5,
            homogeneous_scalar=0.5,
        ),
        ToyConstraint(
            operator_blocks={
                "s0": np.array([[0.0]]),
                "s1": np.array([[0.0]]),
                "s2": np.array([[1.0]]),
            },
            relation="eq",
            bound=0.125,
            homogeneous_scalar=0.125,
        ),
    ),
    summary=(
        "UNTRUSTED-source mode twin of CERT-TOY-3REL-T: the marginal slot is "
        "emptied and the three right-hand sides are retyped as the real "
        "scalars c_k. Same feasible set, same mu(G) = 1/8."
    ),
    derivation=_CERT_3REL_SHARED
    + """
UNTRUSTED-SOURCE MODE. tau_A = none, so Eq. eq:feas carries only tr omega = 1
(Eq. eq:feas-modes, untrusted row); A-MARG is NOT ASSERTED and A-SRC is not
asserted either. Each right-hand side is the REAL SCALAR c_k, not the 1 x 1
matrix [c_k] (Definition def:declaration; A-DECL (vi); def:homog (b)), and
each entry is read as tr[(1_A x O_k) omega] bowtie_k c_k. At d_A = 1 the two
readings give the same three numbers, so the feasible set and mu(G) = 1/8 are
unchanged -- which is exactly the mode agreement Remark rem:modes-da1 (b)
predicts.

WEAK DUALITY, Theorem thm:weak-duality (ii), with the scalar duals
lambda_1, lambda_2 >= 0 and lambda_3 UNRESTRICTED IN SIGN:
  S_s0 = 1 - y_0 - lambda_1 ,
  S_s1 = -1 - y_0 + lambda_2 ,
  S_s2 = 2 - y_0 - lambda_3 ,
  bound = y_0 + lambda_1/4 - lambda_2/2 + lambda_3/8 .
The registry's witness takes y_0 = 1, lambda = (0, 2, 1) and attains
mu(G) = 1/8; a second witness takes lambda_3 = -1, which is admissible because
k = 3 is an EQUALITY, and certifies the weaker -1/8. Both are frozen: any
admissible witness certifies, and a suboptimal one only lowers the bound.

GATE DEGENERATION (Remark rem:cgate): the mode is untrusted, so part (i) of
the two-part gate degenerates to a type check that a well-formed declaration
passes by construction; at d_A = 1 it would in any case reject only a `general`
tag a producer can avoid. Part (ii) fails for want of an attestation, exactly
as in the trusted twin. [Aligned with the owner's reading of the
gate at d_A = 1; no verdict moved. This previously read "d_A = 1 would make it vacuous anyway".]
""",
)

#: The two declarations added for the 0.4.0 certificate chain. Kept apart from
#: :data:`ALL_TOYS_0_3_0` for the same reason :data:`SOURCE_MODE_TOYS` is kept
#: apart from :data:`ALL_TOYS`: the frozen 0.3.0 consumers iterate the older
#: tuples and must keep seeing exactly what they saw.
CERTIFICATE_TOYS: tuple[ToyDeclaration, ...] = (
    CERT_TOY_3REL_TRUSTED,
    CERT_TOY_3REL_UNTRUSTED,
)

#: Every declaration this registry knows at contract_version 0.4.0.
ALL_TOYS_0_4_0: tuple[ToyDeclaration, ...] = ALL_TOYS_0_3_0 + CERTIFICATE_TOYS

#: The untrusted twins, paired with the frozen originals they must reproduce.
#: Remark ``rem:modes-da1`` (b): at ``d_A = 1`` these are the SAME
#: declaration, so a difference in any computed quantity is a defect.
MODE_TWIN_PAIRS: tuple[tuple[ToyDeclaration, ToyDeclaration], ...] = (
    (TOY1_RETENTION, TOY1_UNTRUSTED),
    (TOY3_DEPHASED_2, TOY3_DEPHASED_2_UNTRUSTED),
    (TOY5_CONSTRAINED, TOY5_CONSTRAINED_UNTRUSTED),
)


def toy(toy_id: str) -> ToyDeclaration:
    """Return the toy declaration with the given ``toy_id``.

    Searches :data:`ALL_TOYS_0_4_0`, so the 0.4.0 certificate toys resolve by
    the same call as every earlier one. The lookup only WIDENS: every id that
    resolved at 0.3.0 resolves to the same object.
    """
    for candidate in ALL_TOYS_0_4_0:
        if candidate.toy_id == toy_id:
            return candidate
    raise KeyError(f"no toy declaration {toy_id!r}")
