"""Shared candidate-search records and structural capability decisions.

``frank-wolfe/rem:fo-reachability`` prescribes no optimizer. These components
propose points; only the shared original assessor can contribute a bound.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np

from certiqs_key.meat_core.objective.joint import JointSector
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.solvers.frank_wolfe.q_rule import q_rule_for
from certiqs_key.solvers.oracles.acceptance import SingletonAcceptanceOracle

if TYPE_CHECKING:
    from certiqs_key.solvers.problem import PreparedProblem

Point = Mapping[JointSector, Matrix]
Checkpoint = Callable[[Point, Mapping[str, Fraction]], bool]


#: The iteration and evaluation caps handed to L-BFGS-B where a search runs
#: uncapped (``max_iterations=None``): large enough never to bind before a
#: deadline, small enough for the solver's C integers.
UNCAPPED_NATIVE_WORK = 2**31 - 1


def check_capped(max_iterations: int | None, deadline: float | None) -> None:
    """Refuse an uncapped search that has no deadline either.

    ``max_iterations=None`` means a search runs to its own convergence or its
    deadline (method auto's factor, entropy polish and corrective stages).
    Without a deadline
    nothing would bound it, which is a caller's error.
    """
    if max_iterations is None and deadline is None:
        raise ValueError("an uncapped candidate search needs a deadline")


@dataclass(frozen=True)
class FactorSettings:
    """Search effort and coordinate choices, never proof tolerances.

    ``max_iterations=None`` runs L-BFGS-B to its own tolerances or the
    deadline, with no iteration or evaluation cap.

    ``blend`` (the anchor's share of every candidate) stays 1e-10, unlike
    :class:`CorrectiveSettings`'s: the factor search refuses a declaration
    with constraint rows (:func:`capability_reason`), so its anchor is never
    the zero-cost QICS vertex the corrective search meets there but the
    full-rank initial point, and the encoded route's points pass H-SUPP^D
    with it at every cutoff the study runs.
    """

    max_iterations: int | None = 500
    blend: float = 1e-10
    ftol: float = 1e-15
    gtol: float = 1e-8
    maxcor: int = 30
    checkpoint_every: int = 25

    def __post_init__(self) -> None:
        """Refuse invalid effort settings before any numerical work."""
        cap = 1 if self.max_iterations is None else self.max_iterations
        if min(cap, self.maxcor, self.checkpoint_every) < 1:
            raise ValueError(
                "factor iteration, memory and checkpoint limits are positive"
            )
        if not math.isfinite(self.blend) or not 0 < self.blend < 1:
            raise ValueError("factor blend must be finite and in (0, 1)")
        if any(not math.isfinite(x) or x < 0 for x in (self.ftol, self.gtol)):
            raise ValueError("factor search tolerances must be finite and nonnegative")


#: The corrective blend a series moves to after an H-SUPP^D rank refusal
#: (:class:`CorrectiveSettings`, ``blend``). On the BBM92 licensed route at
#: cutoff 2 and 3 it keeps the zero-anchor-weight mixtures' thinnest support
#: direction several thousand times above the 1e-12 cutoff; 1e-8 left cutoff
#: 3 failing in the diagnosis's trial.
SUPPORT_FALLBACK_BLEND = 1e-6


@dataclass(frozen=True)
class CorrectiveSettings:
    """Bounded active-simplex search effort.

    ``max_iterations=None`` runs outer iterations until the search stagnates
    or the deadline passes.

    ``blend``, THE ANCHOR'S SHARE OF EVERY ATOM, starts at 1e-10, and the
    coordinator raises it to :data:`SUPPORT_FALLBACK_BLEND` for the rest of a
    series only after one of its probes ends in an H-SUPP^D rank refusal
    (``solvers/solve.py``, "THE BLEND"). On a declaration with constraint rows
    the anchor is the QICS zero-cost vertex (``solvers/problem.py``), and an
    SLSQP trial in the inner solve can put zero weight on atom 0, the anchor
    itself, which then survives only through this blend. At 1e-10, on the
    BBM92 licensed route at cutoff 2 and 3, the kept key-active pair ('A',
    'C_1__C_1') of such a mixture had four eigenvalues at 5.9e-13 of its
    spectral radius, below H-SUPP^D's 1e-12 relative rank cutoff
    (``frank-wolfe/cor:fo-dropped``), and the stage ended without a key. A
    fixed 1e-6 cured that (343,075 and 343,115 bits) but COST KEY where 1e-10
    never failed: the licensed route at cutoff 1 fell from 343,213 to 342,853
    bits and its relative gap rose from 3.1e-4 to 1.3e-3. So the larger blend
    is a fallback, not a default. A blend scaled to the anchor's smallest
    eigenvalue was not taken: the rank test reads the aggregate branch
    operator relative to its own radius, not the anchor's block, so such a
    scale gives no stated margin on the tested quantity either; the margin
    actually tested is recorded per probe (``support_margin``). Every
    candidate is still certified by the one assessor.
    """

    max_iterations: int | None = 20
    inner_iterations: int = 100
    max_atoms: int = 40
    blend: float = 1e-10
    ftol: float = 1e-12
    fold_below: float = 1e-12
    checkpoint_every: int = 5

    def __post_init__(self) -> None:
        """Require finite search settings and a bounded nontrivial active set."""
        cap = 1 if self.max_iterations is None else self.max_iterations
        if min(cap, self.inner_iterations, self.checkpoint_every) < 1:
            raise ValueError("corrective iteration and checkpoint limits are positive")
        if self.max_atoms < 2:
            raise ValueError("corrective search needs at least two atoms")
        if not math.isfinite(self.blend) or not 0 < self.blend < 1:
            raise ValueError("corrective blend must be finite and in (0, 1)")
        if any(not math.isfinite(x) or x < 0 for x in (self.ftol, self.fold_below)):
            raise ValueError("corrective search tolerances are finite and nonnegative")


@dataclass(frozen=True)
class EntropySettings:
    """Real entropy-limit cone effort followed by finite-order factor polish."""

    max_iterations: int = 100
    tolerance_gap: float = 1e-7
    tolerance_feasibility: float = 1e-8
    max_assembly_bytes: int = 512 * 1024 * 1024
    polish: FactorSettings = field(default_factory=FactorSettings)

    def __post_init__(self) -> None:
        """Validate numerical effort without altering original oracle gates."""
        if self.max_iterations < 1 or self.max_assembly_bytes < 1:
            raise ValueError("entropy iteration and assembly limits must be positive")
        if any(
            not math.isfinite(x) or x <= 0
            for x in (self.tolerance_gap, self.tolerance_feasibility)
        ):
            raise ValueError("entropy search tolerances must be finite and positive")


@dataclass(frozen=True)
class SearchOutcome:
    """A candidate and search diagnostics; none of these numbers is a bound."""

    point: Point
    q_exact: Mapping[str, Fraction]
    search_objective: float | None
    termination: str
    iterations: int = 0
    evaluations: int = 0
    oracle_calls: int = 0
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


class SearchStopped(Exception):
    """An internal bounded-search interruption, carrying its reason."""

    def __init__(self, reason: str) -> None:
        """Keep the reason separate from numerical/backend failure."""
        super().__init__(reason)
        self.reason = reason


def check_deadline(deadline: float | None) -> None:
    """Interrupt at a work boundary using the coordinator's monotonic clock."""
    if deadline is not None and time.perf_counter() >= deadline:
        raise SearchStopped("budget_exhausted")


def capability_reason(problem: PreparedProblem, method: str) -> str | None:
    """Return a refusal based on declared structure, never a protocol name."""
    if method not in ("factor", "corrective", "entropy"):
        return f"unknown candidate method {method!r}"
    if (
        not isinstance(problem.acceptance, SingletonAcceptanceOracle)
        and q_rule_for(problem.acceptance, problem.maps, problem.alpha) is None
    ):
        return "candidate method requires singleton or exact canonical box acceptance"
    if method in ("factor", "entropy") and problem.maps.declaration.constraint_list:
        return "normalized factor search does not impose additional declared rows"
    if method == "entropy":
        matrices = list(problem.maps.statistics_operator.values())
        matrices.extend(
            klass.kraus
            for branch in problem.maps.branches.values()
            for klass in branch.classes
        )
        if any(np.any(matrix.imag != 0) for matrix in matrices):
            return "entropy initializer supports exactly real data only"
    return None


def initial_q(problem: PreparedProblem) -> dict[str, Fraction]:
    """Return the prepared exact starting member (fixed for a singleton)."""
    from certiqs_key.solvers.oracles.acceptance import ExactAcceptanceOracle

    if isinstance(problem.acceptance, ExactAcceptanceOracle):
        return problem.acceptance.exact_start()
    return {chat: Fraction(value) for chat, value in problem.acceptance.start().items()}
