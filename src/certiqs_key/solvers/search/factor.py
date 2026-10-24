"""Full complex normalized-factor candidates with bounded L-BFGS storage.

For trusted sources, each Alice group's partial trace is normalized by an
inverse-square-root congruence. Untrusted sources use one total trace. An
explicit anchor mixture forms the actual candidate; no hidden perturbation
is applied in assessment. This search enforces no extra declared rows.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from scipy.optimize import minimize  # type: ignore[import-untyped]

from certiqs_key.meat_core.errors import MeatError
from certiqs_key.meat_core.objective.joint import JointSector
from certiqs_key.meat_core.objective.linalg import Matrix, Vector, hermitian_part
from certiqs_key.solvers.search import stable
from certiqs_key.solvers.search.common import (
    UNCAPPED_NATIVE_WORK,
    Checkpoint,
    FactorSettings,
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

DEFAULT_SETTINGS = FactorSettings()


def partial_trace(block: Matrix, input_dim: int, output_dim: int) -> Matrix:
    """Trace out Q with the repository's A tensor Q coordinate ordering."""
    return np.asarray(
        np.einsum(
            "aqbq->ab", block.reshape(input_dim, output_dim, input_dim, output_dim)
        ),
        dtype=np.complex128,
    )


@dataclass
class FactorCache:
    """One forward pass's data needed by the analytic real-coordinate pullback."""

    factors: dict[JointSector, Matrix]
    raw: dict[JointSector, Matrix]
    normalized: dict[JointSector, Matrix]
    groups: dict[str, tuple[Vector, Matrix, Matrix]]
    trace: float = 0.0


class FactorLayout:
    """Square complex factors and their coupling-normalization derivative.

    The inverse-square-root divided difference is
    -1/(sqrt(a)*sqrt(b)*(sqrt(a)+sqrt(b))), including equal eigenvalues.
    Frozen zero-weight trusted sectors remain at their feasible anchor.
    """

    def __init__(
        self,
        dims: Mapping[JointSector, int],
        input_dims: Mapping[str, int],
        *,
        trusted: bool,
        anchor: Point,
        blend: float,
        frozen: frozenset[str] = frozenset(),
    ) -> None:
        """Fix sector order and the full real/imaginary coordinate slices."""
        self.dims = dict(dims)
        self.input_dims = dict(input_dims)
        self.trusted, self.anchor, self.blend = trusted, anchor, blend
        self.frozen = frozen
        self.pairs = tuple(dims)
        self.slices = {}
        offset = 0
        for pair, dim in dims.items():
            self.slices[pair] = slice(offset, offset + dim * dim)
            offset += dim * dim
        self.size = offset

    def pack(self, factors: Point) -> Vector:
        """Pack real and imaginary parts, retaining all complex directions."""
        vector = np.concatenate([factors[pair].ravel() for pair in self.pairs])
        return np.asarray(np.r_[vector.real, vector.imag], dtype=np.float64)

    def unpack(self, coordinates: Vector) -> dict[JointSector, Matrix]:
        """Recover square complex factors from real optimization coordinates."""
        vector = coordinates[: self.size] + 1j * coordinates[self.size :]
        return {
            pair: vector[self.slices[pair]].reshape(self.dims[pair], self.dims[pair])
            for pair in self.pairs
        }

    def from_point(
        self, point: Point, scales: Mapping[str, float] | None = None
    ) -> Vector:
        """Initialize factors by spectral roots with source-weight scaling.

        Clipping here proposes a search seed; it is not an oracle repair or
        a claim that the supplied point was feasible.
        """
        factors = {}
        for pair in self.pairs:
            values, vectors = np.linalg.eigh(hermitian_part(point[pair]))
            scale = 1.0 if scales is None else scales.get(pair[0], 1.0)
            factors[pair] = vectors * np.sqrt(np.maximum(values, 0) * scale)
        return self.pack(factors)

    def forward(
        self, coordinates: Vector
    ) -> tuple[dict[JointSector, Matrix], FactorCache]:
        """Form a PSD coupled point, then mix that point with the anchor."""
        factors = self.unpack(coordinates)
        raw = {pair: hermitian_part(b @ b.conj().T) for pair, b in factors.items()}
        normalized: dict[JointSector, Matrix] = {}
        groups = {}
        trace = 0.0
        if self.trusted:
            for alice, dimension in self.input_dims.items():
                pairs = [pair for pair in self.pairs if pair[0] == alice]
                if alice in self.frozen or dimension == 0:
                    normalized.update({pair: self.anchor[pair] for pair in pairs})
                    continue
                total = sum(
                    (
                        partial_trace(
                            raw[pair], dimension, self.dims[pair] // dimension
                        )
                        for pair in pairs
                    ),
                    np.zeros((dimension, dimension), dtype=np.complex128),
                )
                values, vectors = np.linalg.eigh(hermitian_part(total))
                if not np.all(np.isfinite(values)) or np.min(values) <= 0:
                    raise ArithmeticError("singular factor coupling")
                root = (vectors * values**-0.5) @ vectors.conj().T
                groups[alice] = (values, vectors, root)
                for pair in pairs:
                    lift = np.kron(root, np.eye(self.dims[pair] // dimension))
                    normalized[pair] = hermitian_part(lift @ raw[pair] @ lift)
        else:
            trace = sum(float(np.trace(block).real) for block in raw.values())
            if not np.isfinite(trace) or trace <= 0:
                raise ArithmeticError("zero factor norm")
            normalized = {pair: block / trace for pair, block in raw.items()}
        point = {
            pair: hermitian_part(
                (1 - self.blend) * block + self.blend * self.anchor[pair]
            )
            for pair, block in normalized.items()
        }
        return point, FactorCache(factors, raw, normalized, groups, trace)

    def pullback(self, cotangent: Point, cache: FactorCache) -> Vector:
        """Pull a real Hermitian pairing back to real and imaginary factors."""
        gradients = {
            pair: hermitian_part(g) * (1 - self.blend) for pair, g in cotangent.items()
        }
        raw_gradient: dict[JointSector, Matrix] = {}
        if self.trusted:
            for alice, dimension in self.input_dims.items():
                pairs = [pair for pair in self.pairs if pair[0] == alice]
                if alice in self.frozen or dimension == 0:
                    raw_gradient.update(
                        {pair: np.zeros_like(cache.raw[pair]) for pair in pairs}
                    )
                    continue
                values, vectors, root = cache.groups[alice]
                total = np.zeros((dimension, dimension), dtype=np.complex128)
                for pair in pairs:
                    output = self.dims[pair] // dimension
                    lift = np.kron(root, np.eye(output))
                    raw_gradient[pair] = lift @ gradients[pair] @ lift
                    total += partial_trace(
                        cache.raw[pair] @ lift @ gradients[pair]
                        + gradients[pair] @ lift @ cache.raw[pair],
                        dimension,
                        output,
                    )
                roots = np.sqrt(values)
                divided = -1 / (
                    roots[:, None] * roots[None, :] * (roots[:, None] + roots[None, :])
                )
                correction = hermitian_part(
                    vectors
                    @ (divided * (vectors.conj().T @ total @ vectors))
                    @ vectors.conj().T
                )
                for pair in pairs:
                    raw_gradient[pair] += np.kron(
                        correction, np.eye(self.dims[pair] // dimension)
                    )
        else:
            mean = sum(
                float(np.vdot(gradients[pair], cache.normalized[pair]).real)
                for pair in self.pairs
            )
            raw_gradient = {
                pair: (g - mean * np.eye(g.shape[0])) / cache.trace
                for pair, g in gradients.items()
            }
        return self.pack(
            {
                pair: 2 * hermitian_part(raw_gradient[pair]) @ cache.factors[pair]
                for pair in self.pairs
            }
        )


def search_factor(
    problem: PreparedProblem,
    initial: Point | None = None,
    *,
    settings: FactorSettings = DEFAULT_SETTINGS,
    deadline: float | None = None,
    checkpoint: Checkpoint | None = None,
) -> SearchOutcome:
    """Search for candidates; retain the best evaluation even on interruption."""
    check_capped(settings.max_iterations, deadline)
    started = time.perf_counter()
    point = dict(problem.anchor if initial is None else initial)
    exact = initial_q(problem)
    reason = capability_reason(problem, "factor")
    if reason:
        return SearchOutcome(
            point, exact, None, "unsupported", diagnostics={"reason": reason}
        )
    frames = problem.maps.parametrization.frames
    weights = {
        alice: float(np.trace(frame.gram).real) for alice, frame in frames.items()
    }
    frozen = frozenset(alice for alice, weight in weights.items() if weight == 0)
    layout = FactorLayout(
        {pair: block.shape[0] for pair, block in problem.anchor.items()},
        {alice: frame.input_dim for alice, frame in frames.items()},
        trusted=problem.maps.declaration.is_trusted_source,
        anchor=problem.anchor,
        blend=settings.blend,
        frozen=frozen,
    )
    scales = {alice: weight if weight > 0 else 1.0 for alice, weight in weights.items()}
    coordinates = layout.from_point(point, scales if layout.trusted else None)
    best_value: float | None = None
    evaluations = iterations = 0
    termination = "stagnated"
    message = ""

    def objective(x: Vector) -> tuple[float, Vector]:
        nonlocal point, exact, best_value, evaluations
        check_deadline(deadline)
        trial, cache = layout.forward(x)
        value, gradient, q = stable.evaluate(problem, trial)
        pullback = layout.pullback(gradient, cache)
        if not np.all(np.isfinite(pullback)):
            raise ArithmeticError("nonfinite factor search gradient")
        evaluations += 1
        if best_value is None or value < best_value:
            best_value, point, exact = value, trial, q
        return value, pullback

    def callback(x: Vector) -> None:
        nonlocal iterations
        del x
        iterations += 1
        check_deadline(deadline)
        if (
            checkpoint
            and iterations % settings.checkpoint_every == 0
            and checkpoint(point, exact)
        ):
            raise SearchStopped("target_met")

    options: dict[str, float] = {
        "maxiter": settings.max_iterations or UNCAPPED_NATIVE_WORK,
        "maxls": 50,
        "maxcor": settings.maxcor,
        "ftol": settings.ftol,
        "gtol": settings.gtol,
    }
    if settings.max_iterations is None:
        # Uncapped: the evaluation cap goes too, so that only the solver's
        # own tolerances or the deadline end the search.
        options["maxfun"] = UNCAPPED_NATIVE_WORK
    try:
        result = minimize(
            objective,
            coordinates,
            jac=True,
            method="L-BFGS-B",
            callback=callback,
            options=options,
        )
        message = str(result.message)
        if (
            settings.max_iterations is not None
            and iterations >= settings.max_iterations
        ):
            termination = "budget_exhausted"
    except SearchStopped as stopped:
        termination = stopped.reason
    except (ArithmeticError, ValueError, np.linalg.LinAlgError, MeatError) as error:
        termination, message = "numerical_failure", str(error)
    return SearchOutcome(
        point,
        exact,
        best_value,
        termination,
        iterations,
        evaluations,
        diagnostics={
            "seconds": time.perf_counter() - started,
            "message": message,
            "real_coordinates": 2 * layout.size,
            "source_weights": weights,
            "frozen_sectors": sorted(frozen),
        },
    )
