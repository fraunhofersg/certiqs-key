"""Real entropy-limit QICS initializer followed by finite-alpha factor polish.

The cone minimizes sum D(G(J)||Z(G(J))) with the declared accepted statistics
imposed on P(J). Its alpha=1 objective is a search diagnostic only, never the
finite-alpha reporting objective. QuantKeyDist's complex backend is not used:
every consumed operator must have exactly zero imaginary part. Unsupported
data are refused rather than projected to real data.

A TRANSCRIPT CLASS WITH NO OUTCOME PAIR GETS NO CONE. A branch can hold a class
that no outcome pair of its sector realises (on the BBM92 encoded route at
cutoff 1, one of the two classes of each sector with Bob's flag C_H, C_V, C_D
or C_A, whatever the source, losses or dark counts): its Kraus operator has
no rows, so its ``G`` is the zero map and its term ``D(G(J)||Z(G(J)))`` is
zero at every ``J``. QICS's ``QuantKeyDist`` cannot be built on it (it
divides the output dimension by the number of pinching projectors, here both
zero, and raised ``ZeroDivisionError``), so :func:`_live_classes` leaves such
classes out of the model and of its memory plan. The cone's objective is the
same sum without its zero terms: the program is the one the stage was always
meant to solve, only no longer refused by the backend.
"""

from __future__ import annotations

import math
import time
from collections.abc import Iterable, Iterator, Mapping
from typing import TYPE_CHECKING, Any

import numpy as np
import qics
from qics.vectorize import mat_to_vec, vec_to_mat

from certiqs_key.meat_core.errors import MeatError
from certiqs_key.meat_core.objective.joint import JointClassBranch, JointSector
from certiqs_key.meat_core.objective.linalg import Matrix, Vector
from certiqs_key.solvers.frank_wolfe.q_rule import q_rule_for
from certiqs_key.solvers.search.common import (
    Checkpoint,
    EntropySettings,
    Point,
    SearchOutcome,
    SearchStopped,
    capability_reason,
    check_deadline,
    initial_q,
)
from certiqs_key.solvers.search.factor import search_factor

if TYPE_CHECKING:
    from certiqs_key.solvers.problem import PreparedProblem

DEFAULT_SETTINGS = EntropySettings()
#: What the initializer can raise that ends its stage as a numerical failure
#: rather than the solve (search_entropy, and the coordinator's preflight).
INITIALIZER_FAILURES: tuple[type[BaseException], ...] = (
    ArithmeticError,
    ValueError,
    np.linalg.LinAlgError,
    MemoryError,
    MeatError,
)


def _real_basis(dimension: int, deadline: float | None = None) -> Iterator[Vector]:
    """Yield one real-symmetric pairing at a time, checking the deadline first."""
    for row in range(dimension):
        for column in range(row, dimension):
            check_deadline(deadline)
            element = np.zeros((dimension, dimension))
            element[row, column] = element[column, row] = 1.0
            yield np.asarray(mat_to_vec(element)).ravel()


def _live_classes(classes: Iterable[JointClassBranch]) -> list[JointClassBranch]:
    """Return the classes with at least one output row (module docstring)."""
    return [klass for klass in classes if klass.kraus.shape[0] > 0]


def _preflight_memory(
    problem: PreparedProblem,
    dims: Mapping[JointSector, int],
    box_size: int,
    limit: int,
    deadline: float | None,
) -> tuple[int, int, int]:
    """Budget the complete dense model and cone workspace before construction.

    This conservative capacity estimate covers our row list, dense/model copies,
    QICS equality/Schur work, cone computational bases, projected Kraus data,
    dense pinching projectors and Hessian work. The factors deliberately allow
    concurrent temporaries and double storage for LAPACK operations. It is an
    allocation-plan guard, not a measurement or cap of whole-process RSS (the
    prepared problem, Python runtime and numerical libraries already exist).
    All estimates use unreduced dimensions; facial reduction cannot enlarge them.
    """
    maps = problem.maps
    width = sum(dim**2 for dim in dims.values()) + 2 * box_size
    rows = (
        sum(
            frame.input_dim * (frame.input_dim + 1) // 2
            for frame in maps.parametrization.frames.values()
        )
        if maps.declaration.is_trusted_source
        else 1
    )
    rows += 2 * box_size if box_size else len(maps.declaration.acceptance_values)
    # PSD cone state, eigensolver temporaries and lazy assembly basis/coefficients.
    cone_elements = 32 * sum(dim**2 for dim in dims.values())
    work_shapes: list[tuple[int, int]] = []
    for chat in maps.chat_key:
        for pair in maps.branch_plan(chat, frozenset(problem.dropped), True).evaluated:
            for klass in _live_classes(maps.branches[chat, pair].classes):
                check_deadline(deadline)
                dimension, output = dims[pair], klass.kraus.shape[0]
                labels = len(set(klass.labels))
                width += 1 + dimension**2
                rows += dimension * (dimension + 1) // 2
                # QuantKeyDist constructs a computational basis eagerly itself.
                # Include its basis, compact operators, inverse-Hessian work and
                # facial-reduction/projector copies, before invoking its constructor.
                cone_elements += (
                    32 * dimension**4
                    + 16 * dimension**2 * output**2
                    + 8 * labels * output**2
                    + 32 * (output**2 + dimension * output)
                )
                work_shapes.append((dimension, output))
    # Dense A copies + equality Gram/Schur factors + point/work vectors. Cone
    # congruence work scales with all equality rows, not only that cone's rows.
    dense_elements = 8 * rows * width + 8 * rows**2 + 64 * (width + rows)
    cone_elements += sum(
        16 * rows * (dimension**2 + output**2 + dimension * output)
        for dimension, output in work_shapes
    )
    # Reserve object/index overhead as well as the binary64 array storage.
    planned_bytes = 8 * (dense_elements + cone_elements) + 512 * (
        rows + width + len(work_shapes)
    )
    if planned_bytes > limit:
        raise MemoryError(
            f"entropy allocation plan ({planned_bytes} bytes) exceeds assembly "
            f"memory budget ({limit} bytes)"
        )
    return width, rows, planned_bytes


def _cone_plan(
    problem: PreparedProblem, settings: EntropySettings, deadline: float | None
) -> tuple[dict[JointSector, int], Any, tuple[int, int, int]]:
    """Return the block dimensions, box rule and allocation plan of the cone."""
    maps = problem.maps
    dims = {pair: maps.parametrization.block_dim(pair) for pair in maps.joint_sectors}
    if any(dim == 0 for dim in dims.values()):
        raise ValueError("entropy cone requires nonempty Choi blocks")
    rule = q_rule_for(problem.acceptance, maps, problem.alpha)
    plan = _preflight_memory(
        problem,
        dims,
        0 if rule is None else len(rule.values),
        settings.max_assembly_bytes,
        deadline,
    )
    return dims, rule, plan


def entropy_preflight(
    problem: PreparedProblem, settings: EntropySettings = DEFAULT_SETTINGS
) -> int:
    """Return the cone's planned allocation bytes; raise ``MemoryError`` over budget.

    The same plan :func:`entropy_initializer` checks before it builds
    anything, without building anything, so a coordinator can learn before it
    allocates stage time that the stage's own guard would refuse it. A
    resource predicate only: it reads block dimensions, never protocol names.
    """
    return _cone_plan(problem, settings, None)[2][2]


def entropy_initializer(
    problem: PreparedProblem,
    *,
    settings: EntropySettings = DEFAULT_SETTINGS,
    deadline: float | None = None,
) -> tuple[dict[JointSector, Matrix], dict[str, Any]]:
    """Solve the constrained alpha=1 candidate cone, emitting no key or bound."""
    reason = capability_reason(problem, "entropy")
    if reason:
        raise ValueError(reason)
    started = time.perf_counter()
    check_deadline(deadline)
    maps = problem.maps
    pairs = maps.joint_sectors
    dims, rule, (planned_width, planned_rows, planned_bytes) = _cone_plan(
        problem, settings, deadline
    )
    cones: list[Any] = []
    offsets: list[int] = []
    width = 0

    def add_cone(cone: Any) -> int:
        nonlocal width
        check_deadline(deadline)
        index = len(cones)
        offsets.append(width)
        width += int(sum(cone.dim))
        cones.append(cone)
        if 8 * width > settings.max_assembly_bytes:
            raise MemoryError("entropy cone exceeds assembly memory budget")
        return index

    base = {
        pair: add_cone(qics.cones.PosSemidefinite(dims[pair], iscomplex=False))
        for pair in pairs
    }
    copies: list[tuple[JointSector, int]] = []
    for chat in maps.chat_key:
        for pair in maps.branch_plan(chat, frozenset(problem.dropped), True).evaluated:
            for klass in _live_classes(maps.branches[chat, pair].classes):
                check_deadline(deadline)
                labels = np.asarray(klass.labels)
                projections = [
                    np.diag((labels == label).astype(np.float64))
                    for label in sorted(set(labels))
                ]
                cone = qics.cones.QuantKeyDist(
                    [np.ascontiguousarray(klass.kraus.real)],
                    projections,
                    iscomplex=False,
                )
                copies.append((pair, add_cone(cone)))
    slack: list[int] = []
    if rule is not None:
        slack = [
            add_cone(qics.cones.NonNegOrthant(1)) for _ in range(2 * len(rule.values))
        ]
    cost = np.zeros((width, 1))
    for _, index in copies:
        cost[offsets[index], 0] = 1 / math.log(2)
    rows: list[Vector] = []
    targets: list[float] = []

    def add_row(row: Vector, target: float) -> None:
        check_deadline(deadline)
        # Account for rows plus the dense conversion/model copy; the guard is
        # search effort only and refuses assembly instead of swapping memory.
        if 24 * width * (len(rows) + 1) > settings.max_assembly_bytes:
            raise MemoryError("entropy equality matrix exceeds assembly memory budget")
        rows.append(row)
        targets.append(target)

    for pair, index in copies:
        size = dims[pair] ** 2
        for element in _real_basis(dims[pair], deadline):
            row = np.zeros(width)
            row[offsets[base[pair]] : offsets[base[pair]] + size] = -element
            row[offsets[index] + 1 : offsets[index] + 1 + size] = element
            add_row(row, 0.0)
    if maps.declaration.is_trusted_source:
        for alice, frame in maps.parametrization.frames.items():
            dimension = frame.input_dim
            for element in _real_basis(dimension, deadline):
                matrix = np.asarray(vec_to_mat(element, iscomplex=False))
                row = np.zeros(width)
                for pair in pairs:
                    if pair[0] != alice:
                        continue
                    operator = np.kron(matrix, np.eye(dims[pair] // dimension))
                    offset = offsets[base[pair]]
                    row[offset : offset + dims[pair] ** 2] = np.asarray(
                        mat_to_vec(operator)
                    ).ravel()
                add_row(row, float(np.trace(matrix)))
    else:
        row = np.zeros(width)
        for pair in pairs:
            offset = offsets[base[pair]]
            row[offset : offset + dims[pair] ** 2] = np.asarray(
                mat_to_vec(np.eye(dims[pair]))
            ).ravel()
        add_row(row, 1.0)
    fixed = initial_q(problem)
    for index, chat in enumerate(maps.declaration.acceptance_values):
        row = np.zeros(width)
        for pair in pairs:
            offset = offsets[base[pair]]
            statistic = maps.statistics_operator[chat, pair]
            row[offset : offset + dims[pair] ** 2] = np.asarray(
                mat_to_vec(np.ascontiguousarray(statistic.real))
            ).ravel()
        if rule is None:
            add_row(row, float(fixed[chat]))
        else:
            lower, upper = row.copy(), row.copy()
            lower[offsets[slack[2 * index]]] = -1
            upper[offsets[slack[2 * index + 1]]] = 1
            add_row(lower, float(rule.lower[index]))
            add_row(upper, float(rule.upper[index]))
    check_deadline(deadline)
    if (width, len(rows)) != (planned_width, planned_rows):
        raise ArithmeticError("entropy model dimensions disagree with allocation plan")
    model = qics.Model(
        c=cost, A=np.asarray(rows), b=np.asarray(targets).reshape(-1, 1), cones=cones
    )
    assembly_seconds = time.perf_counter() - started
    check_deadline(deadline)
    remaining = 120.0 if deadline is None else deadline - time.perf_counter()
    solver = qics.Solver(
        model,
        verbose=0,
        max_iter=settings.max_iterations,
        tol_gap=settings.tolerance_gap,
        tol_feas=settings.tolerance_feasibility,
        max_time=max(remaining, 1e-6),
        use_invhess=True,
    )
    cone_started = time.perf_counter()
    information = solver.solve()
    diagnostics = {
        "alpha1_objective": float(information["p_obj"]),
        "cone_status": str(information.get("sol_status")),
        "cone_exit": str(information.get("exit_status")),
        "cone_iterations": int(information.get("num_iter", 0)),
        "assembly_seconds": assembly_seconds,
        "cone_seconds": time.perf_counter() - cone_started,
        "variables": width,
        "equalities": len(rows),
        "cones": len(cones),
        "planned_allocation_bytes": planned_bytes,
    }
    if information.get("sol_status") not in ("optimal", "near_optimal"):
        raise ArithmeticError(f"entropy initializer failed: {diagnostics}")
    solution = np.asarray(information["x_opt"]).ravel()
    point = {
        pair: np.asarray(
            vec_to_mat(
                solution[offsets[index] : offsets[index] + dims[pair] ** 2],
                iscomplex=False,
            ),
            dtype=np.complex128,
        )
        for pair, index in base.items()
    }
    return point, diagnostics


def search_entropy(
    problem: PreparedProblem,
    initial: Point | None = None,
    *,
    settings: EntropySettings = DEFAULT_SETTINGS,
    deadline: float | None = None,
    checkpoint: Checkpoint | None = None,
) -> SearchOutcome:
    """Initialize independently at alpha=1, then polish the finite-alpha problem."""
    del initial  # Independent cold cone initialization is intentional.
    reason = capability_reason(problem, "entropy")
    if reason:
        return SearchOutcome(
            problem.anchor,
            initial_q(problem),
            None,
            "unsupported",
            diagnostics={"reason": reason},
        )
    try:
        point, diagnostics = entropy_initializer(
            problem, settings=settings, deadline=deadline
        )
    except SearchStopped as stopped:
        return SearchOutcome(problem.anchor, initial_q(problem), None, stopped.reason)
    except INITIALIZER_FAILURES as error:
        return SearchOutcome(
            problem.anchor,
            initial_q(problem),
            None,
            "numerical_failure",
            diagnostics={"reason": str(error)},
        )
    polished = search_factor(
        problem,
        point,
        settings=settings.polish,
        deadline=deadline,
        checkpoint=checkpoint,
    )
    return SearchOutcome(
        polished.point,
        polished.q_exact,
        polished.search_objective,
        polished.termination,
        polished.iterations,
        polished.evaluations,
        polished.oracle_calls,
        {**diagnostics, "polish": polished.diagnostics},
    )
