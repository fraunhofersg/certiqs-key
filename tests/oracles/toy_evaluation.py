"""Evaluate the contracted objective at a point of a toy's feasible set.

This is the glue between :mod:`toy_declarations` (hand-authored instances) and
:mod:`reference` (the naive evaluator). It computes ``P``, ``T``, ``tr G``,
``K``, the sector deficits and ``O_alpha`` at a *given* feasible point.

IT IS NOT A SOLVER. The only search it offers is
:func:`minimum_over_sector_weights`, a uniform grid over the sector-weight
simplex, and its sole job is to CHECK a hand-derived minimizer -- never to
produce a golden value. Every ``h_low`` in :mod:`registry` is a closed form
derived on paper; the grid confirms that the claimed argmin is where the
derivation says it is.

Why a sector-weight simplex is a complete parametrization of these toys
-----------------------------------------------------------------------
For every toy in the registry ``d_A = 1`` (or Alice has the single POVM element
``M_x0 = 1_A``) and every declared sector is one-dimensional. The feasible set
of contract Eq. ``eq:feas`` then asks for ``omega >= 0`` that is
sector-block-diagonal with ``tr_Q omega = tau_A``, which on
``A ⊗ Q = C^{|S|}`` is exactly

    omega = diag(w_s)_{s in S},   w_s >= 0,   sum_s w_s = 1,

plus whatever the declared constraint list adds. So a grid over that simplex
covers the whole feasible set and a minimum over it is a genuine (discretized)
global minimum, not a local one.

Every toy's acceptance set is a singleton, so the outer infimum over ``q`` in
contract Eq. ``eq:hlow-def`` is trivial and no optimization over ``q`` happens
anywhere in this tree.

Toys whose statistics are not a function of the sector weights
--------------------------------------------------------------
The 0.3.0 additions include declarations with ``d_A >= 2``, where the argument
above fails: ``Phi[omega]`` then depends on more of ``omega`` than its sector
weights, and the trusted marginal restricts exactly that extra freedom. Those
toys carry ``statistics_operators`` -- the Hermitian ``Gamma^{(s)}_chat`` of
contract Eq. ``eq:Phimap`` -- and are evaluated by
:func:`statistics_from_blocks` and :func:`objective_from_blocks`, which take
the sector BLOCKS ``omega_s`` rather than weights. They carry no branch maps
(``Chat_key`` is empty for all of them), so the objective there is the pure KL
penalty of Eq. ``eq:objective`` and still needs no solver.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from reference import (
    branch_operator,
    k_from_identity,
    objective,
    sector_deficit,
    trace_power_pinched,
)
from toy_declarations import ToyDeclaration


@dataclass(frozen=True)
class BranchValues:
    """The four scalars of contract Eq. eq:fK for one acceptance value."""

    p: float
    t: float
    trace_g: float
    k: float
    deficits: dict[str, float]


def acceptance_point(toy: ToyDeclaration) -> dict[str, float]:
    """Return the single accepted frequency vector ``q`` of ``toy``."""
    frequencies = toy.acceptance_set["frequencies"]
    return dict(zip(toy.acceptance_values, frequencies, strict=True))


def statistics(toy: ToyDeclaration, weights: Mapping[str, float]) -> dict[str, float]:
    """Return ``Phi[omega]`` (contract Eq. eq:Phimap) at the given sector weights.

    Uses the per-sector statistics weights recorded with the toy: for a
    one-dimensional sector with ``d_A = 1`` the summand
    ``tr[(M_x x F_v) omega]`` reduces to ``w_s`` times a declared scalar.
    """
    return {
        chat: sum(share * weights[sector] for sector, share in per_sector.items())
        for chat, per_sector in toy.statistics.items()
    }


def branch_values(
    toy: ToyDeclaration, alpha: float, weights: Mapping[str, float]
) -> dict[str, BranchValues]:
    """Return ``P``, ``T``, ``tr G``, ``K`` and the deficits, per acceptance value."""
    phi = statistics(toy, weights)
    out: dict[str, BranchValues] = {}
    for chat in toy.acceptance_values:
        t_total = 0.0
        trace_total = 0.0
        deficits: dict[str, float] = {}
        for branch in toy.branches.get(chat, ()):
            omega_s = np.array([[weights[branch.sector]]], dtype=np.float64)
            operator = branch_operator(branch.kraus, omega_s)
            t_total += trace_power_pinched(operator, alpha, branch.row_key_values)
            trace_total += float(np.trace(operator))
            deficits[branch.sector] = sector_deficit(
                operator, alpha, branch.row_key_values
            )
        out[chat] = BranchValues(
            p=phi[chat],
            t=t_total,
            trace_g=trace_total,
            k=k_from_identity(t_total, phi[chat], trace_total),
            deficits=deficits,
        )
    return out


def objective_at(
    toy: ToyDeclaration, alpha: float, weights: Mapping[str, float]
) -> float:
    """Return ``O_alpha(q, omega)`` (contract Eq. eq:objective) at a feasible point."""
    values = branch_values(toy, alpha, weights)
    return objective(
        alpha=alpha,
        q=acceptance_point(toy),
        p_chat={chat: value.p for chat, value in values.items()},
        k_chat={chat: value.k for chat, value in values.items()},
        chat_key=toy.chat_key,
    )


def statistics_from_blocks(
    toy: ToyDeclaration, blocks: Mapping[str, np.ndarray]
) -> dict[str, float]:
    """Return ``Phi[omega]`` from the sector BLOCKS ``omega_s``.

    contract Eq. ``eq:Phimap``, written through the Hermitian operators
    ``Gamma^{(s)}_chat = sum_{(x,v): phi(a(x,v)) = chat} M_x x F_v^{(s)}``:
    ``Phi[omega](chat) = sum_s tr[Gamma^{(s)}_chat omega_s]``. Requires the toy
    to carry ``statistics_operators``.
    """
    if not toy.statistics_operators:
        raise ValueError(
            f"{toy.toy_id} carries no statistics_operators; use statistics()"
        )
    return {
        chat: sum(
            float(np.real(np.trace(operator @ blocks[sector])))
            for sector, operator in per_sector.items()
        )
        for chat, per_sector in toy.statistics_operators.items()
    }


def objective_from_blocks(
    toy: ToyDeclaration, alpha: float, blocks: Mapping[str, np.ndarray]
) -> float:
    """Return ``O_alpha(q, omega)`` for a toy given by its sector blocks.

    Only defined where ``Chat_key`` is empty, which is the case for every toy
    that carries ``statistics_operators``: contract Eq. ``eq:objective`` then
    reduces to the KL penalty ``(alpha/(alpha-1)) D(q || Phi[omega])`` and no
    branch operator is needed. Raising rather than silently dropping the
    ``K``-terms is the point -- a toy with a key-live branch and a
    matrix-valued ``omega`` would need the branch machinery, and this function
    must not pretend otherwise.
    """
    if toy.chat_key:
        raise ValueError(
            f"{toy.toy_id} has a key-live acceptance value; the K-terms of "
            "Eq. eq:objective need branch operators, which this path has not"
        )
    phi = statistics_from_blocks(toy, blocks)
    return objective(
        alpha=alpha,
        q=acceptance_point(toy),
        p_chat=phi,
        k_chat=dict.fromkeys(phi, 0.0),
        chat_key=(),
    )


def sector_weight_grid(sectors: Sequence[str], steps: int) -> list[dict[str, float]]:
    """Return a uniform grid over the sector-weight simplex with ``steps`` divisions."""
    points: list[dict[str, float]] = []
    count = len(sectors)
    for combination in itertools.product(range(steps + 1), repeat=count - 1):
        used = sum(combination)
        if used > steps:
            continue
        counts = (*combination, steps - used)
        points.append({s: c / steps for s, c in zip(sectors, counts, strict=True)})
    return points


def minimum_over_sector_weights(
    toy: ToyDeclaration,
    alpha: float,
    *,
    steps: int = 200,
    feasible: Callable[[Mapping[str, float]], bool] | None = None,
) -> tuple[float, dict[str, float]]:
    """Return the grid minimum of the objective and where it is attained.

    A CHECK on a hand-derived argmin, not a solver: see the module docstring.
    ``feasible`` adds the declared constraint list, which the simplex alone does
    not encode.
    """
    best = math.inf
    best_at: dict[str, float] = {}
    for point in sector_weight_grid(toy.sector_index_set, steps):
        if feasible is not None and not feasible(point):
            continue
        value = objective_at(toy, alpha, point)
        if value < best:
            best, best_at = value, point
    return best, best_at
