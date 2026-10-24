"""Bounded corrective simplex search, retaining the best evaluated mixture.

Oracle returns supply search atoms only. The original assessor obtains its
own unchanged oracle return at the actual candidate. Mixing an atom with the
anchor is candidate formation, never a replacement security-oracle return.
"""

from __future__ import annotations

import time
from itertools import count
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy.optimize import minimize  # type: ignore[import-untyped]

from certiqs_key.meat_core.errors import GradientHypothesisError, MeatError
from certiqs_key.meat_core.objective.joint import JointSector
from certiqs_key.meat_core.objective.linalg import Matrix, Vector
from certiqs_key.solvers.frank_wolfe.joint_driver import _oracle_vertex
from certiqs_key.solvers.search import stable
from certiqs_key.solvers.search.common import (
    Checkpoint,
    CorrectiveSettings,
    Point,
    SearchOutcome,
    SearchStopped,
    capability_reason,
    check_capped,
    check_deadline,
    initial_q,
)

if TYPE_CHECKING:
    from certiqs_key.solvers.problem import PreparedProblem

DEFAULT_SETTINGS = CorrectiveSettings()

#: The backend statuses under which the corrective search takes an oracle
#: return as a SEARCH ATOM: the optimal ones and QICS's ``near_optimal``,
#: which the adapter already accepts as an extreme point
#: (``oracles/qics/adapter.py`` ACCEPTED_STATUSES). At cutoff 2 and 3 of the
#: BBM92 licensed route the search's own oracle call returned near_optimal
#: and the stage ended with "candidate oracle did not report optimality". An
#: atom only proposes a direction; the assessor's own oracle calls, which
#: form every bracket, are not touched by this.
SEARCH_ATOM_STATUSES: frozenset[str] = frozenset(
    {"optimal", "solved", "near_optimal"}
)

#: The withdrawal reason of H-SUPP^D (``req:first-order-withdrawal``), which
#: :class:`~certiqs_key.meat_core.errors.GradientHypothesisError` carries.
SUPPORT_REFUSAL_REASON = "gradient_hypothesis_support"


def mixture(atoms: list[Point], weights: Vector) -> dict[JointSector, Matrix]:
    """Form a convex candidate with normalized nonnegative floating weights."""
    weights = np.maximum(weights, 0)
    mass = float(np.sum(weights))
    if not np.isfinite(mass) or mass <= 0:
        raise ArithmeticError("empty active simplex")
    weights = weights / mass
    return {
        pair: np.asarray(
            sum(w * atom[pair] for w, atom in zip(weights, atoms, strict=True)),
            dtype=np.complex128,
        )
        for pair in atoms[0]
    }


def compress(
    atoms: list[Point], weights: Vector, limit: int, threshold: float
) -> tuple[list[Point], Vector]:
    """Fold discarded atoms into their weighted mean, preserving the candidate."""
    keep = [i for i, weight in enumerate(weights) if weight >= threshold and weight > 0]
    keep = sorted(keep, key=lambda i: (-weights[i], i))[: max(0, limit - 1)]
    folded = [i for i in range(len(atoms)) if i not in keep and weights[i] > 0]
    result, masses = [atoms[i] for i in keep], [float(weights[i]) for i in keep]
    if folded:
        mass = sum(float(weights[i]) for i in folded)
        result.append(mixture([atoms[i] for i in folded], weights[folded]))
        masses.append(mass)
    normalized = np.asarray(masses, dtype=np.float64)
    return result, normalized / np.sum(normalized)


def search_corrective(
    problem: PreparedProblem,
    initial: Point | None = None,
    *,
    settings: CorrectiveSettings = DEFAULT_SETTINGS,
    deadline: float | None = None,
    checkpoint: Checkpoint | None = None,
) -> SearchOutcome:
    """Jointly reoptimize active atoms with a bounded-memory SLSQP inner solve.

    ``settings.max_iterations=None`` runs outer iterations until the search
    stagnates or ``deadline`` passes.
    """
    check_capped(settings.max_iterations, deadline)
    started = time.perf_counter()
    point = dict(problem.anchor if initial is None else initial)
    exact = initial_q(problem)
    reason = capability_reason(problem, "corrective")
    if reason:
        return SearchOutcome(
            point, exact, None, "unsupported", diagnostics={"reason": reason}
        )
    atoms: list[Point] = [point]
    weights = np.ones(1, dtype=np.float64)
    best_value: float | None = None
    iterations = evaluations = 0
    calls: list[Any] = []
    trace: list[dict[str, Any]] = []
    termination, message = "budget_exhausted", ""
    support_refusal = False
    max_atoms_seen = 1
    try:
        outer = (
            count()
            if settings.max_iterations is None
            else range(settings.max_iterations)
        )
        for iteration in outer:
            check_deadline(deadline)
            atoms, weights = compress(
                atoms, weights, settings.max_atoms - 1, settings.fold_below
            )
            current = mixture(atoms, weights)
            value, gradient, q = stable.evaluate(problem, current)
            evaluations += 1
            if best_value is None or value < best_value:
                best_value, point, exact = value, current, q
            made = len(calls)
            vertex, optimal = _oracle_vertex(
                problem.maps,
                problem.oracle,
                gradient,
                calls,
                problem.rows,
                assignment=problem.assignment,
                spectral=problem.spectral,
                iteration=iteration,
            )
            check_deadline(deadline)
            usable = optimal or (
                len(calls) > made
                and all(
                    call.get("sol_status") in SEARCH_ATOM_STATUSES
                    for call in calls[made:]
                )
            )
            if not usable:
                raise ArithmeticError("candidate oracle did not report optimality")
            atom = {
                pair: (1 - settings.blend) * vertex[pair]
                + settings.blend * problem.anchor[pair]
                for pair in vertex
            }
            if any(
                all(np.array_equal(atom[pair], old[pair]) for pair in atom)
                for old in atoms
            ):
                termination = "stagnated"
                break
            atoms.append(atom)
            weights = np.r_[weights, 0.0]
            max_atoms_seen = max(max_atoms_seen, len(atoms))
            inner_best = value
            inner_weights = weights.copy()

            def objective(
                trial: Vector, active: list[Point] = atoms
            ) -> tuple[float, Vector]:
                nonlocal \
                    inner_best, \
                    inner_weights, \
                    point, \
                    exact, \
                    best_value, \
                    evaluations
                check_deadline(deadline)
                candidate = mixture(active, trial)
                cost, blocks, q_trial = stable.evaluate(problem, candidate)
                evaluations += 1
                masses = np.maximum(trial, 0)
                total = float(np.sum(masses))
                slopes = (
                    np.asarray(
                        [
                            sum(
                                float(
                                    np.vdot(
                                        blocks[pair], item[pair] - candidate[pair]
                                    ).real
                                )
                                for pair in candidate
                            )
                            for item in active
                        ]
                    )
                    / total
                )
                # The evaluated candidate is normalized, including SLSQP trials
                # off its equality manifold. Retain that exact same point.
                if cost < inner_best:
                    inner_best, inner_weights = cost, masses / total
                if best_value is None or cost < best_value:
                    best_value, point, exact = cost, candidate, q_trial
                return cost, slopes

            result = minimize(
                objective,
                weights,
                jac=True,
                method="SLSQP",
                bounds=[(0.0, 1.0)] * len(weights),
                constraints=[
                    {
                        "type": "eq",
                        "fun": lambda x: np.sum(x) - 1,
                        "jac": lambda x: np.ones_like(x),
                    }
                ],
                options={"maxiter": settings.inner_iterations, "ftol": settings.ftol},
            )
            weights = inner_weights
            iterations += 1
            trace.append(
                {
                    "iteration": iterations,
                    "objective": inner_best,
                    "atoms": len(atoms),
                    "inner_iterations": int(result.nit),
                    "inner_message": str(result.message),
                }
            )
            if (
                checkpoint
                and iterations % settings.checkpoint_every == 0
                and checkpoint(point, exact)
            ):
                raise SearchStopped("target_met")
            if inner_best >= value:
                termination = "stagnated"
                break
    except SearchStopped as stopped:
        termination = stopped.reason
    except (ArithmeticError, ValueError, np.linalg.LinAlgError, MeatError) as error:
        termination, message = "numerical_failure", str(error)
        # The H-SUPP^D rank refusal, told apart by its reason code: the
        # coordinator answers it with a larger blend (solve.py, "THE BLEND").
        support_refusal = (
            isinstance(error, GradientHypothesisError)
            and error.reason == SUPPORT_REFUSAL_REASON
        )
    try:
        margin = stable.support_margin(problem, point)
    except (ArithmeticError, ValueError, np.linalg.LinAlgError, MeatError):
        margin = None
    return SearchOutcome(
        point,
        exact,
        best_value,
        termination,
        iterations,
        evaluations,
        len(calls),
        {
            "seconds": time.perf_counter() - started,
            "message": message,
            "max_atoms": max_atoms_seen,
            "trace": trace,
            "oracle_diagnostics": calls,
            "support_refusal": support_refusal,
            "support_margin": margin,
        },
    )
