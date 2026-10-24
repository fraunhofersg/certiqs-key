"""The gradient of the (dropped) objective over joint sectors.

``cor:full-gradient`` read on a joint pair, which is what
``frank-wolfe/cor:fo-dropped``'s (H-NOPERT^D) names: ``eq:grad-q`` with
``K^{J,D}_chat`` in the scalar prefactors, and ``eq:grad-J`` per joint pair with
``Gamma^{(p)}_chat`` the operators ``W_t^dagger M_x^{(t)} W_t (x) F_v^{(s)}``
(which in ensemble form are the DECLARED ``N_x^{(t)} (x) F_v^{(s)}``) and with
the deficit piece carrying, in place of ``1[s in S_K(chat)]``, the indicator

    ``1[p in J_K(chat) and (chat, p) not in D]``.

On a fully dropped joint sector every deficit piece is absent, so the block is
``eq:drop-gradient`` -- "no matter power, no eigendecomposition and no support
condition of a fully dropped joint sector enters" (``cor:drop-program`` (iii)).

WHY THE PIECES NEED NO ``chi`` CONJUGATION HERE
==============================================
The generated maps of :mod:`certiqs_key.meat_core.objective.joint` are built IN
CHOI COORDINATES: the Kraus rows carry ``sqrt(N^W_x)`` and the statistics
operators carry ``N^W_x``, by ``lem:choi-factor`` (iii). So what
:func:`joint_gradient` returns is ``eq:grad-J`` outright, and the accepted
path's habit of conjugating a state-form gradient has no counterpart -- which is
also what makes the ensemble form work at every rank, there being no ``M_x`` to
conjugate.

(H-SUPP^D) IS ASKED OF A KEPT KEY-ACTIVE PAIR AND OF NOTHING ELSE
=================================================================
``cor:fo-dropped``, Step 1: a key-inert pair's deficit is constant along every
segment and "no support hypothesis on it is consumed"; a dropped pair is absent
from the sum altogether. So the rank comparison
``rank X_{chat,p} = dim W_{chat,p}`` of ``eq:Wcs-joint`` runs at the kept
key-active pairs, once per pair, against the reference computed from the
declaration and the frame and never from an iterate.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from certiqs_key.foundations.kernel import (
    divergence_kernel_du,
    divergence_kernel_dv,
)
from certiqs_key.meat_core.errors import GradientHypothesisError
from certiqs_key.meat_core.objective.branch import ClassBranch
from certiqs_key.meat_core.objective.gradient import (
    attains_the_reference_rank,
    pullback_trace_power_gradient,
)
from certiqs_key.meat_core.objective.joint import (
    NOTHING_DROPPED,
    DroppedSet,
    JointBranchValues,
    JointClassBranch,
    JointMaps,
    JointSector,
    evaluate_joint_branches,
)
from certiqs_key.meat_core.objective.linalg import (
    Matrix,
    as_matrix,
    hermitian_part,
    support_rank,
)
from certiqs_key.meat_core.objective.objective import check_alpha_structural

#: The withdrawal reasons of ``frank-wolfe/req:first-order-withdrawal`` this module
#: can raise, spelled as the contract spells them. THE DROPPED PROGRAM ADDS NO
#: STRING: "a run with a non-empty dropped set withdraws ``h_lb_dropped`` under
#: THE SAME SIX STRINGS, read of the dropped program's hypotheses".
_POSITIVITY_REASON = "gradient_hypothesis_positivity"
_SUPPORT_REASON = "gradient_hypothesis_support"


@dataclass(frozen=True)
class JointObjectiveGradient:
    """The gradient of ``O^{J,D}_alpha`` at a point, in Choi coordinates."""

    #: ``eq:grad-q`` read as a vector in ``R^{Chat_acc}`` (``lem:fo-khyp``
    #: (iii)), with ``K^{J,D}`` in the prefactors.
    q: Mapping[str, float]
    #: ``eq:grad-J`` per joint sector.
    blocks: Mapping[JointSector, Matrix]
    #: Which pairs' deficit pieces were absent because the pair was dropped,
    #: and which because it was key-inert. The two are recorded apart because
    #: the second is an identity and the first is a run's choice.
    dropped_pieces: tuple[tuple[str, JointSector], ...] = ()
    key_inert_pieces: tuple[tuple[str, JointSector], ...] = ()
    perturbations: Mapping[tuple[str, JointSector], float] = field(default_factory=dict)


def _as_class_branch(klass: JointClassBranch) -> ClassBranch:
    """Adapt a joint class branch to the shared pullback routine.

    The pullback of ``grad T`` reads a class' Kraus operator and its raw-key
    labels and nothing else, so the general format reuses the accepted path's
    own routine rather than carrying a second copy of ``eq:gradT``. The
    announcement field is presentation only and carries the transcript.
    """
    return ClassBranch(
        announcement=("transcript", "|".join(klass.transcript)),
        pairs=klass.pairs,
        kraus=klass.kraus,
        labels=klass.labels,
    )


def check_joint_gradient_hypotheses(
    q: Mapping[str, float],
    values: Mapping[str, JointBranchValues],
    chat_key: tuple[str, ...],
    acceptance_support: tuple[str, ...],
) -> None:
    """Raise unless (H-POS^D) holds, quantified on ``Chat_acc``.

    ``cor:fo-dropped`` (H-POS^D) is (H-POS) "with ``K^{J,D}_chat`` in place of
    ``K^J_chat``", and the implication runs one way only: ``K^D >= K`` by
    ``prop:drop-bound`` (i), so (H-POS) implies (H-POS^D) and a run that
    satisfied the undropped hypothesis satisfies this one.
    """
    live = set(chat_key)
    for chat in acceptance_support:
        weight = q[chat]
        value = values[chat]
        if weight <= 0.0 or value.p <= 0.0 or not np.isfinite(value.p):
            raise GradientHypothesisError(
                "hypothesis (H-POS^D) of frank-wolfe/cor:fo-dropped, on the "
                "acceptance support of lem:fo-khyp (iii): q(chat) > 0 and "
                f"P_chat > 0 for every chat in Chat_acc; at {chat!r} they are "
                f"{weight!r} and {value.p!r}",
                reason=_POSITIVITY_REASON,
            )
        if chat in live and value.k <= 0.0:
            raise GradientHypothesisError(
                "hypothesis (H-POS^D) of frank-wolfe/cor:fo-dropped: "
                "K^D_chat > 0 is required for every chat in "
                f"Chat_key n Chat_acc; at {chat!r} it is {value.k!r}",
                reason=_POSITIVITY_REASON,
            )


def joint_deficit_gradient(
    maps: JointMaps,
    chat: str,
    pair: JointSector,
    choi_block: Matrix,
    alpha: float,
    *,
    perturbation: float = 0.0,
) -> Matrix:
    """Return ``grad_J f_{chat,p}`` at one joint pair, in Choi coordinates.

    (H-SUPP^D) is decided here, ONCE PER PAIR AND ON THE AGGREGATE operator
    over the pass classes, against ``dim W_{chat,(t,s)}`` of ``eq:Wcs-joint``
    -- the reference the maps carry, computed from the declaration and the
    frame. Deciding it per class would measure each class against its own
    spectral radius and admit a point the claim refuses, which the accepted
    path avoids in the same way.
    """
    check_alpha_structural(alpha)
    branch = maps.branches[(chat, pair)]
    dimension = maps.parametrization.block_dim(pair)
    block = as_matrix(choi_block)
    established = perturbation > 0.0
    if not established:
        aggregate = _aggregate(branch.classes, block)
        reference = maps.support_references[(chat, pair)]
        if not attains_the_reference_rank(aggregate, reference):
            raise GradientHypothesisError(
                "hypothesis (H-SUPP^D) of frank-wolfe/cor:fo-dropped, Step 0: "
                "the branch operator of the KEPT KEY-ACTIVE joint pair "
                f"{pair} at {chat!r} does not attain the maximal support of "
                f"that pair -- rank X = {support_rank(aggregate)} against "
                f"dim W_(chat,(t,s)) = {reference}, the rank on the AGGREGATE "
                "over the pass classes. Nothing is asked of a key-inert or "
                "dropped pair; this one is neither. Supply an explicit "
                "perturbation, or move the iterate",
                reason=_SUPPORT_REASON,
            )
        established = True
    total = np.zeros((dimension, dimension), dtype=np.complex128)
    for klass in branch.classes:
        total = total + pullback_trace_power_gradient(
            _as_class_branch(klass),
            block,
            alpha,
            admissible=None,
            perturbation=perturbation,
            support_established=established,
        )
    return hermitian_part(total)


def _aggregate(classes: tuple[JointClassBranch, ...], block: Matrix) -> Matrix:
    """Return ``X_{chat,p}``, the direct sum over the pass classes.

    The classes occupy orthogonal output blocks (``lem:joint-sectors`` (ii) and
    the accepted path's ``aggregate_branch_operator``), so the sum IS the direct
    sum and the aggregate rank is what ``eq:Wcs-joint`` counts.
    """
    blocks = [
        np.asarray(klass.kraus @ block @ klass.kraus.conj().T, dtype=np.complex128)
        for klass in classes
    ]
    if not blocks:
        return np.zeros((0, 0), dtype=np.complex128)
    total = sum(item.shape[0] for item in blocks)
    aggregate = np.zeros((total, total), dtype=np.complex128)
    offset = 0
    for item in blocks:
        size = item.shape[0]
        aggregate[offset : offset + size, offset : offset + size] = item
        offset += size
    return aggregate


def joint_gradient(
    maps: JointMaps,
    q: Mapping[str, float],
    choi: Mapping[JointSector, Matrix],
    alpha: float,
    *,
    dropped: DroppedSet = NOTHING_DROPPED,
    skip_key_inert: bool = True,
    perturbation: float = 0.0,
) -> JointObjectiveGradient:
    """Return the gradient of ``O^{J,D}_alpha`` of ``cor:fo-dropped``.

    ``eq:grad-q`` and ``eq:grad-J``, with ``K^{J,D}`` in the scalar prefactors
    and the deficit piece present exactly at a KEPT KEY-ACTIVE pair. At
    ``D = empty`` and one Alice sector this is ``cor:full-gradient``'s Choi form
    of the same declaration.

    ``skip_key_inert`` governs the ``K^D`` VALUES the prefactors read and
    NOT the deficit pieces: the gradient always omits a key-inert pair's
    piece, because evaluating it needs a differentiability hypothesis that fails
    exactly where the term vanishes -- the branch operator is zero there. (The
    accepted path's ``state_gradient`` takes the same restriction for the same
    reason.)

    HOW IT IS SUMMED. Per joint sector the block is
    ``sum_chat w_chat Gamma_chat + sum_{chat live, kept key-active}
    c_chat grad f_chat``, with ``w_chat = dv(q, P) + dv(q, K) / (alpha - 1)`` at
    a key-live value, ``(alpha / (alpha - 1)) dv(q, P)`` otherwise, and
    ``c_chat = dv(q, K) / (alpha - 1)``. The linear part is ONE product with the
    precomputed :attr:`JointMaps.statistics_map` (whose rows hold
    ``Gamma^T``), and the deficit pieces are formed only at the pairs
    :meth:`JointMaps.branch_plan` keeps. That is the expression of
    :func:`_joint_gradient_reference` regrouped, equal to rounding.
    """
    check_alpha_structural(alpha)
    values = evaluate_joint_branches(
        maps, choi, alpha, dropped=dropped, skip_key_inert=skip_key_inert
    )
    support = maps.acceptance_support
    check_joint_gradient_hypotheses(q, values, maps.chat_key, support)
    key_live = set(maps.chat_key)
    live = tuple(chat for chat in support if chat in key_live)
    applied: dict[tuple[str, JointSector], float] = {}

    q_gradient: dict[str, float] = {}
    linear_weight: dict[str, float] = {}
    deficit_weight: dict[str, float] = {}
    for chat in support:
        weight = q[chat]
        value = values[chat]
        if chat in key_live:
            q_gradient[chat] = divergence_kernel_du(weight, value.p) + (
                divergence_kernel_du(weight, value.k) / (alpha - 1.0)
            )
            coefficient = divergence_kernel_dv(weight, value.k) / (alpha - 1.0)
            deficit_weight[chat] = coefficient
            linear_weight[chat] = divergence_kernel_dv(weight, value.p) + coefficient
        else:
            q_gradient[chat] = (alpha / (alpha - 1.0)) * divergence_kernel_du(
                weight, value.p
            )
            linear_weight[chat] = (alpha / (alpha - 1.0)) * divergence_kernel_dv(
                weight, value.p
            )

    layout = maps.statistics_map
    weights = np.asarray(
        [linear_weight.get(chat, 0.0) for chat in layout.acceptance_values],
        dtype=np.float64,
    )
    stacked = weights @ layout.matrix
    blocks: dict[JointSector, Matrix] = {}
    offset = 0
    for pair, dim in zip(layout.pairs, layout.dims, strict=True):
        # Rows hold Gamma^T flattened, so the slice reshaped is sum w Gamma^T.
        blocks[pair] = stacked[offset : offset + dim * dim].reshape(dim, dim).T
        offset += dim * dim

    kept = frozenset(dropped)
    for chat in live:
        for pair in maps.branch_plan(chat, kept, True).evaluated:
            deficit = joint_deficit_gradient(
                maps, chat, pair, choi[pair], alpha, perturbation=perturbation
            )
            if perturbation > 0.0:
                applied[(chat, pair)] = perturbation
            blocks[pair] = blocks[pair] + deficit_weight[chat] * deficit

    # The pieces left out, recorded in the reference's order: joint sector
    # outermost, then acceptance value. Dropped before key-inert, as there.
    dropped_pieces: list[tuple[str, JointSector]] = []
    inert_pieces: list[tuple[str, JointSector]] = []
    for pair in maps.joint_sectors:
        for chat in live:
            if (chat, pair) in dropped:
                dropped_pieces.append((chat, pair))
            elif maps.key_inert[(chat, pair)]:
                inert_pieces.append((chat, pair))
    return JointObjectiveGradient(
        q=q_gradient,
        blocks={
            pair: hermitian_part(np.asarray(blocks[pair], dtype=np.complex128))
            for pair in maps.joint_sectors
        },
        dropped_pieces=tuple(dropped_pieces),
        key_inert_pieces=tuple(inert_pieces),
        perturbations={
            key: applied[key]
            for pair in maps.joint_sectors
            for chat in live
            if (key := (chat, pair)) in applied
        },
    )


def _joint_gradient_reference(
    maps: JointMaps,
    q: Mapping[str, float],
    choi: Mapping[JointSector, Matrix],
    alpha: float,
    *,
    dropped: DroppedSet = NOTHING_DROPPED,
    skip_key_inert: bool = True,
    perturbation: float = 0.0,
) -> JointObjectiveGradient:
    """Return :func:`joint_gradient` by the per-(sector, value) loop it replaced.

    Kept verbatim as the reference the restructured path is tested against.
    The gradient of ``O^{J,D}_alpha`` of ``cor:fo-dropped``.

    ``eq:grad-q`` and ``eq:grad-J``, with ``K^{J,D}`` in the scalar prefactors
    and the deficit piece present exactly at a KEPT KEY-ACTIVE pair. At
    ``D = empty`` and one Alice sector this is ``cor:full-gradient``'s Choi form
    of the same declaration.

    ``skip_key_inert`` governs the ``K^D`` VALUES the prefactors read and
    NOT the deficit pieces: the gradient always omits a key-inert pair's
    piece, because evaluating it needs a differentiability hypothesis that fails
    exactly where the term vanishes. The body says so where it happens.
    """
    check_alpha_structural(alpha)
    values = evaluate_joint_branches(
        maps, choi, alpha, dropped=dropped, skip_key_inert=skip_key_inert
    )
    support = maps.acceptance_support
    check_joint_gradient_hypotheses(q, values, maps.chat_key, support)
    live = {chat for chat in support if chat in set(maps.chat_key)}
    applied: dict[tuple[str, JointSector], float] = {}
    dropped_pieces: list[tuple[str, JointSector]] = []
    inert_pieces: list[tuple[str, JointSector]] = []

    q_gradient: dict[str, float] = {}
    for chat in support:
        weight = q[chat]
        value = values[chat]
        if chat in live:
            q_gradient[chat] = divergence_kernel_du(weight, value.p) + (
                divergence_kernel_du(weight, value.k) / (alpha - 1.0)
            )
        else:
            q_gradient[chat] = (alpha / (alpha - 1.0)) * divergence_kernel_du(
                weight, value.p
            )

    blocks: dict[JointSector, Matrix] = {}
    for pair in maps.joint_sectors:
        dimension = maps.parametrization.block_dim(pair)
        total = np.zeros((dimension, dimension), dtype=np.complex128)
        for chat in support:
            weight = q[chat]
            value = values[chat]
            gamma = as_matrix(maps.statistics_operator[(chat, pair)])
            if chat not in live:
                total = (
                    total
                    + (alpha / (alpha - 1.0))
                    * divergence_kernel_dv(weight, value.p)
                    * gamma
                )
                continue
            total = total + divergence_kernel_dv(weight, value.p) * gamma
            if (chat, pair) in dropped:
                deficit = np.zeros((dimension, dimension), dtype=np.complex128)
                dropped_pieces.append((chat, pair))
            elif maps.key_inert[(chat, pair)]:
                # THE RESTRICTION IS NOT OPTIONAL IN THE GRADIENT, and
                # ``skip_key_inert`` does not reach it. The deficit of a
                # key-inert pair is identically zero
                # (``lem:joint-sectors`` (iii)), but EVALUATING its gradient
                # needs the differentiability hypothesis of
                # ``thm:gradient`` (ii), which fails at exactly the points
                # where the term vanishes -- the branch operator is zero there.
                # Adding a zero is free; deriving it is not. The accepted
                # path's ``state_gradient`` takes the same restriction for the
                # same reason, and the flag governs the OBJECTIVE's sum alone.
                deficit = np.zeros((dimension, dimension), dtype=np.complex128)
                inert_pieces.append((chat, pair))
            else:
                deficit = joint_deficit_gradient(
                    maps, chat, pair, choi[pair], alpha, perturbation=perturbation
                )
                if perturbation > 0.0:
                    applied[(chat, pair)] = perturbation
            total = total + (divergence_kernel_dv(weight, value.k) / (alpha - 1.0)) * (
                gamma + deficit
            )
        blocks[pair] = hermitian_part(total)
    return JointObjectiveGradient(
        q=q_gradient,
        blocks=blocks,
        dropped_pieces=tuple(dropped_pieces),
        key_inert_pieces=tuple(inert_pieces),
        perturbations=applied,
    )
