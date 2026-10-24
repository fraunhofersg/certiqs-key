"""Search-only stable arithmetic; never imported by the reporting assessor.

The expm1 deficit and generalized KL avoid subtracting order-one quantities
near alpha=1. The latter omits the floating normalization residual and the
former omits cutoff-tail traces. Thus this is explicitly a search surrogate.
Its direction uses the original deficit derivative with stable scalar values;
it is not an exact derivative through spectral cutoffs or rational q rounding.
The original objective, gradient and hypothesis gates are recomputed by the
assessor at the proposed point (``frank-wolfe/thm:firstorder``).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np

from certiqs_key.meat_core.objective.joint import (
    JointBranchValues,
    JointMaps,
    JointSector,
    joint_statistics,
)
from certiqs_key.meat_core.objective.joint_gradient import (
    _aggregate,
    joint_deficit_gradient,
)
from certiqs_key.meat_core.objective.linalg import (
    SUPPORT_CUTOFF,
    Matrix,
    hermitian_part,
    pinch,
)
from certiqs_key.solvers.frank_wolfe.q_rule import box_argmin, q_rule_for
from certiqs_key.solvers.search.common import Point, initial_q

if TYPE_CHECKING:
    from certiqs_key.solvers.problem import PreparedProblem


def stable_deficit(
    maps: JointMaps, chat: str, pair: JointSector, block: Matrix, alpha: float
) -> float:
    """Evaluate a candidate deficit via two small expm1 trace sums."""
    terms: list[float] = []
    epsilon = alpha - 1
    power_delta = -epsilon / alpha
    for klass in maps.branches[chat, pair].classes:
        operator = hermitian_part(klass.kraus @ block @ klass.kraus.conj().T)
        if not operator.size:
            continue
        spectrum, basis = np.linalg.eigh(operator)
        keep = spectrum > max(0.0, float(np.max(spectrum))) * SUPPORT_CUTOFF
        spectrum, basis = spectrum[keep], basis[:, keep]
        if not spectrum.size:
            continue
        powered = (basis * (spectrum * np.exp(power_delta * np.log(spectrum)))) @ (
            basis.conj().T
        )
        pinched = pinch(powered, klass.labels)
        mu = np.linalg.eigvalsh(hermitian_part(pinched))
        mu = mu[mu > max(0.0, float(np.max(mu))) * SUPPORT_CUTOFF]
        terms.extend((spectrum * np.expm1(power_delta * np.log(spectrum))).tolist())
        terms.extend((mu * np.expm1(epsilon * np.log(mu))).tolist())
    return math.fsum(terms)


def kl_piece(relative: float) -> float:
    """Return (1+t) log(1+t)-t stably near zero; t must exceed -1."""
    if abs(relative) < 1e-3:
        return relative**2 * (
            0.5
            + relative
            * (-1 / 6 + relative * (1 / 12 + relative * (-1 / 20 + relative / 30)))
        )
    return (1 + relative) * math.log1p(relative) - relative


def stable_value(
    maps: JointMaps,
    q: Mapping[str, float],
    values: Mapping[str, JointBranchValues],
    alpha: float,
) -> float:
    """Return the generalized-KL candidate surrogate in bits."""
    kl: list[float] = []
    entropy: list[float] = []
    for chat, weight in q.items():
        value = values[chat]
        if value.p <= 0:
            if weight > 0:
                return math.inf
            continue
        kl.append(
            value.p if weight == 0 else value.p * kl_piece((weight - value.p) / value.p)
        )
        if chat in maps.chat_key and weight > 0:
            delta = math.fsum(value.deficits.values()) / value.p
            if delta <= -1:
                return math.inf
            entropy.append(-weight * math.log1p(delta))
    return (alpha * math.fsum(kl) + math.fsum(entropy)) / ((alpha - 1) * math.log(2))


def centered_blocks(maps: JointMaps, costs: Point) -> dict[JointSector, Matrix]:
    """Remove the coupling equality gauge from search directions only."""
    if not maps.declaration.is_trusted_source:
        center = sum(float(np.trace(x).real) for x in costs.values()) / sum(
            x.shape[0] for x in costs.values()
        )
        return {pair: x - center * np.eye(x.shape[0]) for pair, x in costs.items()}
    result = {}
    for alice, frame in maps.parametrization.frames.items():
        pairs = [pair for pair in costs if pair[0] == alice]
        dimension = frame.input_dim
        if not dimension:
            result.update({pair: costs[pair] for pair in pairs})
            continue
        output_dims = {pair: costs[pair].shape[0] // dimension for pair in pairs}
        center = sum(
            np.einsum(
                "aqbq->ab",
                costs[pair].reshape(
                    dimension, output_dims[pair], dimension, output_dims[pair]
                ),
            )
            for pair in pairs
        ) / sum(output_dims.values())
        result.update(
            {
                pair: costs[pair] - np.kron(center, np.eye(output_dims[pair]))
                for pair in pairs
            }
        )
    return result


def support_margin(problem: PreparedProblem, point: Point) -> dict[str, Any] | None:
    """Return the thinnest support direction H-SUPP^D tests at ``point``.

    A DIAGNOSTIC: per kept key-active pair the branch operator
    aggregated over its pass classes, as ``joint_deficit_gradient`` forms it,
    and its ``r``-th largest eigenvalue relative to its spectral radius,
    ``r`` being the reference rank ``dim W`` the test asks for. H-SUPP^D
    holds while that relative eigenvalue exceeds the ``support_cutoff``
    (1e-12); the smallest one over the pairs is returned with the pair, the
    cutoff and their ratio, so a margin that thins toward a refusal is
    visible before it fails. ``None`` where no pair is tested. Nothing reads
    it.
    """
    maps = problem.maps
    worst: tuple[float, str, JointSector] | None = None
    for chat in maps.chat_key:
        if chat not in maps.acceptance_support:
            continue
        for pair in maps.branch_plan(chat, frozenset(problem.dropped), True).evaluated:
            reference = maps.support_references[(chat, pair)]
            if reference <= 0:
                continue
            aggregate = _aggregate(maps.branches[(chat, pair)].classes, point[pair])
            values = np.sort(np.linalg.eigvalsh(hermitian_part(aggregate)))[::-1]
            radius = float(np.max(np.abs(values))) if values.size else 0.0
            relative = (
                float(values[reference - 1]) / radius
                if radius > 0 and reference <= values.size
                else 0.0
            )
            if worst is None or relative < worst[0]:
                worst = (relative, chat, pair)
    if worst is None:
        return None
    relative, chat, pair = worst
    return {
        "smallest_relative_eigenvalue": relative,
        "cutoff": SUPPORT_CUTOFF,
        "margin_factor": relative / SUPPORT_CUTOFF,
        "chat": chat,
        "pair": list(pair),
    }


def evaluate(
    problem: PreparedProblem, point: Point
) -> tuple[float, dict[JointSector, Matrix], dict[str, Fraction]]:
    """Return search value, a partial-gradient direction, and an exact q member."""
    maps, alpha = problem.maps, problem.alpha
    statistics = joint_statistics(maps, point)
    values = {}
    for chat, probability in statistics.items():
        plan = maps.branch_plan(
            chat, frozenset(problem.dropped), problem.skip_key_inert
        )
        deficits = {
            pair: stable_deficit(maps, chat, pair, point[pair], alpha)
            for pair in plan.evaluated
        }
        values[chat] = JointBranchValues(
            probability,
            probability + math.fsum(deficits.values()),
            deficits,
            plan.dropped_pairs,
            plan.skipped_key_inert,
        )
    rule = q_rule_for(problem.acceptance, maps, alpha)
    if rule is None:
        exact = initial_q(problem)
    else:
        exponents = []
        for chat, live in zip(rule.values, rule.live, strict=True):
            value = values[chat]
            exponent = -math.inf
            if value.p > 0:
                exponent = math.log2(value.p)
                if live:
                    delta = math.fsum(value.deficits.values()) / value.p
                    exponent = (
                        exponent + math.log1p(delta) / (alpha * math.log(2))
                        if delta > -1
                        else -math.inf
                    )
            exponents.append(exponent)
        view = box_argmin(
            np.asarray(exponents),
            np.asarray([float(x) for x in rule.lower]),
            np.asarray([float(x) for x in rule.upper]),
        )
        exact = rule.exact_member(dict(zip(rule.values, view.tolist(), strict=True)))
    q = {chat: float(value) for chat, value in exact.items()}
    objective = stable_value(maps, q, values, alpha)
    if not math.isfinite(objective):
        raise ArithmeticError("candidate objective is not finite")
    linear: dict[str, float] = {}
    deficit_weights = {}
    for chat in maps.acceptance_support:
        value, weight = values[chat], q[chat]
        if weight <= 0 or value.p <= 0 or value.k <= 0:
            raise ArithmeticError("candidate lacks positive acceptance support")
        if chat in maps.chat_key:
            coefficient = -weight / (value.k * (alpha - 1) * math.log(2))
            deficit_weights[chat] = coefficient
            linear[chat] = -weight / (value.p * math.log(2)) + coefficient
        else:
            linear[chat] = -alpha * weight / (value.p * (alpha - 1) * math.log(2))
    layout = maps.statistics_map
    stacked = (
        np.asarray([linear.get(chat, 0.0) for chat in layout.acceptance_values])
        @ layout.matrix
    )
    blocks: dict[JointSector, Matrix] = {}
    offset = 0
    for pair, dim in zip(layout.pairs, layout.dims, strict=True):
        blocks[pair] = stacked[offset : offset + dim * dim].reshape(dim, dim).T.copy()
        offset += dim * dim
    for chat, coefficient in deficit_weights.items():
        for pair in maps.branch_plan(chat, frozenset(problem.dropped), True).evaluated:
            blocks[pair] += coefficient * joint_deficit_gradient(
                maps, chat, pair, point[pair], alpha
            )
    return objective, centered_blocks(maps, blocks), exact
