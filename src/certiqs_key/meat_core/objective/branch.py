"""The maps a declaration generates, and the pointwise ``P``, ``T``, ``K``.

This module realises claims C1, C2, C5, C6 and C7 of ``meat-core``.

**C1/C2 -- what is built.** contract Definition ``def:branch`` writes the branch
Kraus operator of one announcement class ``kappa`` as::

    K^{(s)}_kappa = sum_{(x,v) in a^{-1}(kappa)}
                    |r(x,v)>_R |x,v>_XY |kappa>_CC (sqrt(M_x) x sqrt(F_v^{(s)}))

Because ``R``, ``XY`` and ``C_A C_B`` all carry values that are functions of the
pair ``(x, v)``, the surviving output basis of one class is indexed by that pair
alone, and the operator is the vertical stack of the row blocks
``sqrt(M_x) x sqrt(F_v^{(s)})``. Each row remembers its raw-key value
``r(x, v)``, which is the only thing the key pinching ``Z`` needs.

**Why the classes stay separate.** Remark ``rem:inert`` permits dropping a
register component that is constant across all Kraus terms of a branch, and
requires retaining every component that varies -- the class label ``kappa``
among them, because it carries the orthogonality the derivations use. Distinct
classes therefore occupy orthogonal output subspaces, so ``G_{chat,s}`` is the
direct sum of its per-class blocks. Powers, the pinching ``Z`` (whose projectors
act on ``R`` and commute with the class label) and the trace all act blockwise,
so ``T`` and ``tr G`` are sums over classes. Nothing is approximated by working
per class; the direct sum is simply never materialised.

**C5.** ``P``, ``T``, ``tr G`` and ``K = T + P - tr G`` are Eq. ``eq:fK``; the
sector deficits ``f_{chat,s} = T_{chat,s} - tr G_{chat,s}`` are Eq. ``eq:f-def``
and the sector form ``K = P + sum_s f`` is Eq. ``eq:c5-sector``, a theorem which
this module computes both ways so that a caller can compare them.

**C7.** The key-inertness predicate of Definition ``def:keyinert`` is decided
here, from the declaration alone. It is *reported*, and it is deliberately not
used to shorten the sum: Proposition ``prop:exact-cancellation`` says a key-inert pair
contributes ``f == 0`` for every input, so summing over all sectors is an
identity, and computing the identity is safer than trusting the predicate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.linalg import (
    Matrix,
    as_matrix,
    pinch,
    psd_power,
    psd_trace_power,
)
from certiqs_key.meat_core.objective.support import (
    BranchSupport,
    acceptance_support,
    branch_support,
)

#: An announcement class ``kappa = (c_A, c_B)``.
Announcement = tuple[str, str]

#: An outcome pair ``(x, v)``.
OutcomePair = tuple[str, str]


@dataclass(frozen=True)
class ClassBranch:
    """One class' Kraus operator ``K^{(s)}_kappa`` of Eq. ``eq:kraus``.

    ``kraus`` has shape ``(n_pairs * dim, dim)`` with ``dim`` the dimension of
    the input block; ``labels`` gives the raw-key value ``r(x, v)`` carried by
    each output index, which is what the key pinching reads.
    """

    announcement: Announcement
    pairs: tuple[OutcomePair, ...]
    kraus: Matrix
    labels: npt.NDArray[np.int64]


@dataclass(frozen=True)
class BranchMap:
    """The generation map ``G_{chat,s}`` of Eq. ``eq:GTheta``, held per class."""

    chat: str
    sector: str
    classes: tuple[ClassBranch, ...]

    @property
    def is_zero(self) -> bool:
        """Return whether the branch has no pass class.

        Lemma ``lem:branch-maps`` (iv).
        """
        return not self.classes


@dataclass(frozen=True)
class BranchValues:
    """The four scalars of Eq. ``eq:fK`` at one acceptance value."""

    p: float
    t: float
    trace_g: float
    k: float
    deficits: Mapping[str, float]

    @property
    def k_from_sector_form(self) -> float:
        """Return ``P + sum_s f_{chat,s}``, Eq. ``eq:c5-sector``.

        Equal to :attr:`k` as a theorem (Theorem ``thm:branch-formula``) rather than by
        construction: :attr:`k` is assembled from ``T + P - tr G``.
        """
        return self.p + sum(self.deficits.values())


def sifting_map(declaration: ProtocolDeclaration) -> dict[Announcement, bool]:
    """Return ``varsigma``: which realized announcement classes pass sifting.

    def:admissible-declaration (v) requires sifting to be announcement-determined:
    ``r(x, v) = perp`` exactly when ``varsigma(a(x, v)) = fail``. That makes the
    pass/fail flag a function of the class, and the requirement is checkable --
    every realized outcome pair of one class must agree.

    A class that no outcome pair realises is absent from the returned map. Its
    ``varsigma`` value is not determined by the declaration, and it cannot
    matter: a branch with no Kraus term has ``G_chat = 0``, hence
    ``K_chat = P_chat`` (Eq. ``eq:fK``), and the objective's key-live term
    ``d(q,P) + d(q,K)/(alpha-1)`` then equals its non-key-live term
    ``(alpha/(alpha-1)) d(q,P)`` exactly. Both readings give the same objective.

    Raises:
        DeclarationError: if a class mixes sifted and unsifted outcome pairs.
    """
    verdict: dict[Announcement, bool] = {}
    witness: dict[Announcement, OutcomePair] = {}
    for x in declaration.alice_outcomes:
        for v in declaration.bob_outcomes:
            kappa = declaration.announcement(x, v)
            passes = declaration.raw_key(x, v) is not None
            if kappa in verdict and verdict[kappa] != passes:
                raise DeclarationError(
                    "def:admissible-declaration (v): sifting is not announcement-"
                    f"determined. Announcement class {kappa} contains both a "
                    f"sifted and an unsifted outcome pair: {witness[kappa]} "
                    f"and {(x, v)}"
                )
            verdict[kappa] = passes
            witness[kappa] = (x, v)
    return verdict


def key_live_values(declaration: ProtocolDeclaration) -> tuple[str, ...]:
    """Return ``Chat_key`` of Eq. ``eq:chkey``, in the declared alphabet order.

    An acceptance value is key-live when some realized announcement class that
    maps to it passes sifting.
    """
    passing = sifting_map(declaration)
    live = {
        declaration.accept_statistic[kappa]
        for kappa, passes in passing.items()
        if passes
    }
    return tuple(c for c in declaration.acceptance_values if c in live)


def effective_outcomes(
    declaration: ProtocolDeclaration, kappa: Announcement, sector: str
) -> tuple[OutcomePair, ...]:
    """Return ``E^{(s)}_kappa`` of contract Definition ``def:keyinert``.

    The outcome pairs of the class whose operators do not vanish on the sector:
    ``M_x != 0`` and ``F_v^{(s)} != 0``. Vanishing is decided exactly -- an
    operator counts as nonzero when it has a nonzero entry -- because the
    predicate is a property of the DECLARATION. Numerical dust in a supplied
    declaration is a defect of the supplier, and treating dust as nonzero
    enlarges ``E``, which can only make ``r`` harder to be constant, i.e. can
    only classify a sector as key-active. That is the conservative direction.
    """
    pairs: list[OutcomePair] = []
    for x in declaration.alice_outcomes:
        if not np.any(declaration.alice_povm[x] != 0.0):
            continue
        for v in declaration.bob_outcomes:
            if declaration.announcement(x, v) != kappa:
                continue
            if not np.any(declaration.bob_povm[v][sector] != 0.0):
                continue
            pairs.append((x, v))
    return tuple(pairs)


def is_key_inert(declaration: ProtocolDeclaration, chat: str, sector: str) -> bool:
    """Return whether the pair ``(chat, sector)`` is key-inert.

    contract Definition ``def:keyinert``: for every pass class ``kappa`` of
    ``chat``, the raw-key map ``r`` is constant on ``E^{(s)}_kappa``. A finite,
    mechanically checkable predicate on the declaration.
    """
    passing = sifting_map(declaration)
    for kappa, passes in passing.items():
        if not passes or declaration.accept_statistic[kappa] != chat:
            continue
        values = {
            declaration.raw_key(x, v)
            for x, v in effective_outcomes(declaration, kappa, sector)
        }
        if len(values) > 1:
            return False
    return True


def _pair_row_block(
    declaration: ProtocolDeclaration, x: str, v: str, sector: str
) -> Matrix:
    """Return ``sqrt(M_x) x sqrt(F_v^{(s)})``, one row block of Eq. eq:kraus."""
    root_m = psd_power(as_matrix(declaration.alice_povm[x]), 0.5)
    root_f = psd_power(as_matrix(declaration.bob_povm[v][sector]), 0.5)
    return np.asarray(np.kron(root_m, root_f), dtype=np.complex128)


def _class_branch(
    declaration: ProtocolDeclaration,
    kappa: Announcement,
    sector: str,
    pairs: Sequence[OutcomePair],
) -> ClassBranch:
    """Assemble one :class:`ClassBranch` from its outcome pairs."""
    dim = declaration.block_dim(sector)
    blocks = [_pair_row_block(declaration, x, v, sector) for x, v in pairs]
    labels: list[int] = []
    for x, v in pairs:
        value = declaration.raw_key(x, v)
        if value is None:
            raise DeclarationError(
                "def:admissible-declaration (v): a pass class must not contain an "
                f"unsifted outcome pair, but {(x, v)} in class {kappa} is perp"
            )
        labels.extend([value] * dim)
    kraus = np.vstack(blocks) if blocks else np.zeros((0, dim), dtype=np.complex128)
    return ClassBranch(
        announcement=kappa,
        pairs=tuple(pairs),
        kraus=np.asarray(kraus, dtype=np.complex128),
        labels=np.asarray(labels, dtype=np.int64),
    )


@dataclass(frozen=True)
class GeneratedMaps:
    """Everything C1 and C2 derive from a declaration, built once.

    Nothing here depends on the state ``omega`` or on the Renyi order
    ``alpha``: the maps are a function of the declaration alone, which is what
    makes them shareable across a whole Frank-Wolfe run.
    """

    declaration: ProtocolDeclaration
    chat_key: tuple[str, ...]
    #: ``Chat_acc`` of Eq. ``eq:chacc-def``, the ACCEPTANCE SUPPORT -- built
    #: here because Lemma ``lem:fo-khyp`` (C22b) makes it the index set the
    #: positivity hypothesis is STATED ON and the set the gradient sums are
    #: RESTRICTED TO, and because it is "a property of the DECLARATION alone",
    #: which is exactly what these maps are. Computing it once is not an
    #: optimization: on the ``polytope`` geometry it is a linear program per
    #: coordinate, and taking it per iterate would pay that at every step for
    #: an answer that cannot move.
    acceptance_support: tuple[str, ...]
    sifting: Mapping[Announcement, bool]
    statistics_operator: Mapping[str, Mapping[str, Matrix]]
    pass_operator: Mapping[str, Mapping[str, Matrix]]
    branches: Mapping[str, Mapping[str, BranchMap]]
    key_inert: Mapping[tuple[str, str], bool]
    #: ``dim W_{chat,s}``, ONE NUMBER PER PAIR -- the RIGHT-HAND SIDE of Eq.
    #: ``eq:hsupp-check``, which ``frank-wolfe/req:support-rank-check`` requires
    #: to be "computed once per ``(chat, s)`` from the declaration and
    #: ``W_tau`` and never from an iterate". It is computed HERE because that
    #: is what these maps are: a function of the declaration alone, built once
    #: and shared across the whole run. A reference recomputed per iterate
    #: could not drift -- no iterate enters it -- but it would not be
    #: read off the object whose whole property is not moving.
    #:
    #: ONE NUMBER AND NOT ONE PER CLASS.
    #: ``eq:Kstack`` lists the classes SIDE BY SIDE and ``eq:Kstack-rank``
    #: reads ``dim W_{chat,s}`` as the rank of that one matrix; the comparison
    #: it is the reference for is likewise one comparison, on the aggregate.
    support_references: Mapping[tuple[str, str], int]
    #: Per pair, the directions of ``ran K_{chat,s}`` whose singular value lies
    #: in ``(support_cutoff, sqrt(support_cutoff)]`` relative to the largest --
    #: set aside by the one-ruler reading of ``dim W_{chat,s}``
    #: (:class:`~certiqs_key.meat_core.objective.support.BranchSupport`). A
    #: diagnostic for the run record; nothing reads it to decide anything.
    support_bands: Mapping[tuple[str, str], int]

    @property
    def sectors(self) -> tuple[str, ...]:
        """Return the declared sector index set, in its declared order."""
        return self.declaration.sector_index_set

    def key_active_sectors(self, chat: str) -> tuple[str, ...]:
        """Return ``S_K(chat)`` of contract Definition ``def:keyactive``."""
        return tuple(s for s in self.sectors if not self.key_inert[(chat, s)])

    @property
    def key_acceptance_support(self) -> tuple[str, ...]:
        """Return ``Chat_key n Chat_acc``, in the declared order.

        The index set Lemma ``lem:fo-khyp`` (iii) weakens the ``K_chat > 0``
        clause of (H-POS) to, and the set the ``K``-bearing terms of
        Eq. ``eq:grad-J`` are summed over. Both restrictions "are IDENTITIES on
        that set, not truncations".
        """
        live = set(self.chat_key)
        return tuple(chat for chat in self.acceptance_support if chat in live)


def generate_maps(declaration: ProtocolDeclaration) -> GeneratedMaps:
    """Build the generated maps of C1/C2 from a validated declaration.

    The declaration should already have passed
    :func:`certiqs_key.meat_core.declaration.validation.validate_declaration`; this
    function re-derives the sifting map and therefore still rejects a
    declaration violating def:admissible-declaration (v).
    """
    passing = sifting_map(declaration)
    chat_key = key_live_values(declaration)

    by_class: dict[Announcement, list[OutcomePair]] = {}
    for x in declaration.alice_outcomes:
        for v in declaration.bob_outcomes:
            by_class.setdefault(declaration.announcement(x, v), []).append((x, v))

    statistics_operator: dict[str, dict[str, Matrix]] = {}
    pass_operator: dict[str, dict[str, Matrix]] = {}
    branches: dict[str, dict[str, BranchMap]] = {}
    for chat in declaration.acceptance_values:
        statistics_operator[chat] = {}
        pass_operator[chat] = {}
        branches[chat] = {}
        for sector in declaration.sector_index_set:
            dim = declaration.block_dim(sector)
            total = np.zeros((dim, dim), dtype=np.complex128)
            passed = np.zeros((dim, dim), dtype=np.complex128)
            class_branches: list[ClassBranch] = []
            for kappa, pairs in by_class.items():
                if declaration.accept_statistic[kappa] != chat:
                    continue
                block = np.zeros((dim, dim), dtype=np.complex128)
                for x, v in pairs:
                    block = block + np.kron(
                        as_matrix(declaration.alice_povm[x]),
                        as_matrix(declaration.bob_povm[v][sector]),
                    )
                total = total + block
                if passing[kappa]:
                    passed = passed + block
                    class_branches.append(
                        _class_branch(declaration, kappa, sector, pairs)
                    )
            statistics_operator[chat][sector] = total
            pass_operator[chat][sector] = passed
            branches[chat][sector] = BranchMap(
                chat=chat, sector=sector, classes=tuple(class_branches)
            )

    key_inert = {
        (chat, sector): is_key_inert(declaration, chat, sector)
        for chat in declaration.acceptance_values
        for sector in declaration.sector_index_set
    }
    # THE RIGHT-HAND SIDE OF Eq. eq:hsupp-check, once per pair. See
    # :func:`branch_support_reference` for what is computed and
    # :data:`GeneratedMaps.support_references` for why it is computed here.
    supports = {
        (chat, sector): branch_support_of(declaration, branches[chat][sector])
        for chat in declaration.acceptance_values
        for sector in declaration.sector_index_set
    }
    return GeneratedMaps(
        declaration=declaration,
        chat_key=chat_key,
        # Eq. eq:chacc-def, through the one function that owns it. Read here
        # and not recomputed downstream: Lemma lem:fo-khyp states (H-POS) and
        # both gradient restrictions on this set, and a set recomputed per
        # iterate could drift from the one the hypothesis was checked against.
        acceptance_support=acceptance_support(declaration),
        sifting=passing,
        statistics_operator=statistics_operator,
        pass_operator=pass_operator,
        branches=branches,
        key_inert=key_inert,
        support_references={
            pair: support.dimension for pair, support in supports.items()
        },
        support_bands={pair: support.band for pair, support in supports.items()},
    )


def admissible_isometry(declaration: ProtocolDeclaration, sector: str) -> Matrix:
    """Return the isometry onto ``S_A (x) H(Q_s)`` of Eq. ``eq:SA``.

    ``W_tau`` tensored with the identity on the sector block. Built from the
    declaration alone, so it is the same in every coordinate system and does
    not move with the iterate; in untrusted-source mode and for a full-rank
    ``tau_A`` it is the identity.

    ONE CONSTRUCTION AND ONE ONLY. Two places need it -- the reference
    dimensions below, computed once per pair, and the gradient's
    maximal-support test, taken per iterate -- and a second spelling of it
    would let the reference and the test be about different subspaces.
    """
    return np.asarray(
        np.kron(
            declaration.admissible_alice_isometry(),
            np.eye(declaration.sector_dims[sector], dtype=np.complex128),
        ),
        dtype=np.complex128,
    )


def branch_support_reference(
    declaration: ProtocolDeclaration, branch: BranchMap
) -> int:
    """Return ``dim W_{chat,s}``, the right side of Eq. ``eq:hsupp-check``.

    ``frank-wolfe/rem:fo-one-ruler``: (H-SUPP) is the RANK EQUALITY
    ``rank X_{chat,s} = dim W_{chat,s}``, and BOTH SIDES ARE COMPUTED, with
    ONE RULER. This is the right-hand side: ``rank K_{chat,s}`` of Eq.
    ``eq:Kstack``, read at ``sqrt(support_cutoff)`` relative to THAT MATRIX'S
    largest singular value -- the ``support_cutoff`` row read on
    ``X(1) = K K^dagger``, derived and not declared --
    from the declaration and ``W_tau`` and never from an iterate.

    ONE MATRIX OVER ALL THE PASSING CLASSES, WHICH IS WHAT ``eq:Kstack``
    WRITES: the operators ``K^{(s)}_kappa (W_tau (x) 1)`` listed SIDE BY SIDE,
    a map out of the direct sum over ``kappa``, whose rank ``eq:Kstack-rank``
    equals ``dim W_{chat,s}``. One reference per class compared class by class
    would look the stricter reading; IT IS NOT, AND THE ARGUMENT IS WRONG IN
    THE UNSAFE DIRECTION. The windows are RELATIVE:
    a class whose branch operator is smaller than the largest by more than
    ``1 / support_cutoff`` contributes nothing to the aggregate rank while
    attaining its own per-class rank in full, so the per-class comparison
    ADMITS where the claim's refuses -- on the hypothesis whose failure
    ``rem:fo-danger`` puts on the unsafe side. The claim's number is the
    aggregate one and this is it.
    """
    return branch_support_of(declaration, branch).dimension


def branch_support_of(
    declaration: ProtocolDeclaration, branch: BranchMap
) -> BranchSupport:
    """Return ``dim W_{chat,s}`` and its band count, from one decomposition.

    The stack :func:`branch_support_reference` describes;
    :func:`~certiqs_key.meat_core.objective.support.branch_support` reads it.
    """
    lift = admissible_isometry(declaration, branch.sector)
    return branch_support([klass.kraus @ lift for klass in branch.classes])


def aggregate_branch_operator(branch: BranchMap, omega_s: Matrix) -> Matrix:
    """Return ``X_{chat,s} = G_{chat,s}(omega_s)``, over the passing classes.

    THE LEFT SIDE OF Eq. ``eq:hsupp-check`` IS ONE OPERATOR. ``lem:fo-face``
    defines ``X := G^J_{chat,s}(J_s)``, the sum over ``kappa in K_pass(chat)``,
    and ``frank-wolfe/rem:fo-one-ruler`` counts its eigenvalues "RELATIVE
    TO THAT BLOCK'S OWN SPECTRAL RADIUS" -- the aggregate block's, which is why
    the aggregate must be formed rather than the classes compared one by one.

    THE CLASSES OCCUPY ORTHOGONAL OUTPUT BLOCKS in this implementation (see the
    module docstring), so the sum is the DIRECT SUM of the per-class operators
    and is assembled as one block-diagonal matrix. In exact arithmetic the
    aggregate rank is then the sum of the per-class ranks; in the arithmetic
    that runs it is not, the cutoff being relative to the one radius, and the
    difference is why the aggregate is formed.
    """
    blocks = [branch_operator(klass, omega_s) for klass in branch.classes]
    if not blocks:
        return np.zeros((0, 0), dtype=np.complex128)
    total = sum(block.shape[0] for block in blocks)
    aggregate = np.zeros((total, total), dtype=np.complex128)
    offset = 0
    for block in blocks:
        size = block.shape[0]
        aggregate[offset : offset + size, offset : offset + size] = block
        offset += size
    return aggregate


def branch_operator(branch: ClassBranch, omega_s: Matrix) -> Matrix:
    """Return ``K_kappa omega K_kappa^dagger`` for one announcement class."""
    return np.asarray(
        branch.kraus @ omega_s @ branch.kraus.conj().T, dtype=np.complex128
    )


def trace_power_pinched(
    operator: Matrix, alpha: float, labels: npt.NDArray[np.int64]
) -> float:
    """Return ``tr[(Z(X^{1/alpha}))^alpha]`` -- the one nonlinear ingredient."""
    if operator.size == 0:
        return 0.0
    return psd_trace_power(pinch(psd_power(operator, 1.0 / alpha), labels), alpha)


def statistics(maps: GeneratedMaps, omega: Mapping[str, Matrix]) -> dict[str, float]:
    """Return ``Phi[omega]`` of Eq. ``eq:Phimap``, per acceptance value.

    Affine in ``omega`` (Theorem ``thm:protocol-channel`` (iii)) and, on a
    block-diagonal state, a sum over sectors (Lemma ``lem:branch-maps`` (iii)).
    """
    out: dict[str, float] = {}
    for chat in maps.declaration.acceptance_values:
        total = 0.0
        for sector in maps.sectors:
            operator = maps.statistics_operator[chat][sector]
            total += float(np.real(np.trace(operator @ omega[sector])))
        out[chat] = total
    return out


def evaluate_branch(
    maps: GeneratedMaps,
    chat: str,
    omega: Mapping[str, Matrix],
    alpha: float,
    p_chat: float,
) -> BranchValues:
    """Return ``P``, ``T``, ``tr G``, ``K`` and the sector deficits at ``omega``."""
    t_total = 0.0
    trace_total = 0.0
    deficits: dict[str, float] = {}
    for sector in maps.sectors:
        branch = maps.branches[chat][sector]
        t_sector = 0.0
        trace_sector = 0.0
        for klass in branch.classes:
            operator = branch_operator(klass, omega[sector])
            t_sector += trace_power_pinched(operator, alpha, klass.labels)
            trace_sector += float(np.real(np.trace(operator)))
        deficits[sector] = t_sector - trace_sector
        t_total += t_sector
        trace_total += trace_sector
    return BranchValues(
        p=p_chat,
        t=t_total,
        trace_g=trace_total,
        k=t_total + p_chat - trace_total,
        deficits=deficits,
    )


def evaluate_branches(
    maps: GeneratedMaps, omega: Mapping[str, Matrix], alpha: float
) -> dict[str, BranchValues]:
    """Return :func:`evaluate_branch` for every declared acceptance value."""
    phi = statistics(maps, omega)
    return {
        chat: evaluate_branch(maps, chat, omega, alpha, phi[chat])
        for chat in maps.declaration.acceptance_values
    }


def sector_indices(
    declaration: ProtocolDeclaration, sector: str
) -> npt.NDArray[np.int64]:
    """Return the positions of the block ``A x Q_s`` inside ``A x Q``.

    With the ``A``-first ordering of the conventions, the index of
    ``(a, q)`` in ``A x Q`` is ``a * d_Q + q`` while the index of ``(a, q_s)``
    in ``A x Q_s`` is ``a * d_s + q_s``, and the sectors partition ``q`` into
    consecutive ranges. The embedding is therefore an interleaved selection,
    not a contiguous slice -- writing it out is what keeps the dense and block
    pictures comparable (Lemma ``lem:branch-maps`` (iii)).
    """
    offset = 0
    for name in declaration.sector_index_set:
        if name == sector:
            break
        offset += declaration.sector_dims[name]
    else:
        raise DeclarationError(f"unknown sector {sector!r}")
    receiver = declaration.receiver_dim
    width = declaration.sector_dims[sector]
    return np.asarray(
        [
            a * receiver + offset + q
            for a in range(declaration.alice_dim)
            for q in range(width)
        ],
        dtype=np.int64,
    )


def embed_state(
    declaration: ProtocolDeclaration, omega: Mapping[str, Matrix]
) -> Matrix:
    """Return the block-diagonal ``omega`` as a dense operator on ``A x Q``.

    A TEST-ONLY CROSS-CHECK AID, and it is marked as one rather than deleted.
    The conventions fix ``operator_form: sector_blocks``: a declared operator
    "arrives as the LIST OF ITS SECTOR BLOCKS ... and NEVER as a d_Q x d_Q
    array", and spec/architecture.md 2.9 removes the ambient form from the
    format. NO PRODUCTION PATH ASSEMBLES ONE.

    What it is still FOR is the check Lemma ``lem:branch-maps`` (iii) invites: the
    sector decomposition can be CHECKED against two separately assembled
    objects rather than assumed, and doing so needs an ambient object to check
    against. That is a property of the tests and not of a run, so this function
    and its two companions below are the module's cross-check surface and must
    not acquire a caller under ``solve``.
    """
    dimension = declaration.alice_dim * declaration.receiver_dim
    dense = np.zeros((dimension, dimension), dtype=np.complex128)
    for sector in declaration.sector_index_set:
        index = sector_indices(declaration, sector)
        dense[np.ix_(index, index)] = omega[sector]
    return dense


def dense_bob_povm_element(declaration: ProtocolDeclaration, v: str) -> Matrix:
    """Return ``F_v`` on the whole receiver space, from its declared blocks.

    A TEST-ONLY CROSS-CHECK AID (see :func:`embed_state`). The declared datum is
    the list of blocks; this assembles an ambient operator FROM them, placing
    each declared entry where it was declared and exact zeros nowhere else, so
    that a test may compare a sectorwise computation against an ambient one.
    """
    receiver = declaration.receiver_dim
    full = np.zeros((receiver, receiver), dtype=np.complex128)
    offset = 0
    for sector in declaration.sector_index_set:
        width = declaration.sector_dims[sector]
        full[offset : offset + width, offset : offset + width] = declaration.bob_povm[
            v
        ][sector]
        offset += width
    return full


def dense_branch(maps: GeneratedMaps, chat: str) -> BranchMap:
    """Return ``G_chat`` written on the whole of ``A x Q``, without sectors.

    A TEST-ONLY CROSS-CHECK AID (see :func:`embed_state`). Built independently
    of the per-sector branches so that the sector decomposition of Lemma
    ``lem:branch-maps`` (iii) can be CHECKED against two separately assembled objects
    rather than assumed -- which is the whole of its purpose, and the reason it
    survives the removal of the ambient operator form.
    """
    declaration = maps.declaration
    dim = declaration.alice_dim * declaration.receiver_dim
    grouped: dict[Announcement, list[OutcomePair]] = {}
    for x in declaration.alice_outcomes:
        for v in declaration.bob_outcomes:
            kappa = declaration.announcement(x, v)
            if declaration.accept_statistic[kappa] != chat or not maps.sifting[kappa]:
                continue
            grouped.setdefault(kappa, []).append((x, v))
    classes: list[ClassBranch] = []
    for kappa, pairs in grouped.items():
        blocks: list[Matrix] = []
        labels: list[int] = []
        for x, v in pairs:
            blocks.append(
                np.asarray(
                    np.kron(
                        psd_power(as_matrix(declaration.alice_povm[x]), 0.5),
                        psd_power(dense_bob_povm_element(declaration, v), 0.5),
                    ),
                    dtype=np.complex128,
                )
            )
            value = declaration.raw_key(x, v)
            if value is None:
                raise DeclarationError(
                    "def:admissible-declaration (v): a pass class must not contain an "
                    f"unsifted outcome pair, but {(x, v)} in class {kappa} is perp"
                )
            labels.extend([value] * dim)
        classes.append(
            ClassBranch(
                announcement=kappa,
                pairs=tuple(pairs),
                kraus=np.asarray(np.vstack(blocks), dtype=np.complex128),
                labels=np.asarray(labels, dtype=np.int64),
            )
        )
    return BranchMap(chat=chat, sector="<dense>", classes=tuple(classes))
