"""Public candidate-search effort, separate from proof-relevant thresholds."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NamedTuple

from certiqs_key.meat_core.declaration.validation import MATHEMATICAL_SPEC_VERSION
from certiqs_key.meat_core.objective.joint import JointSector
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_options import (
    JointFrankWolfeOptions,
    WarmStart,
    joint_choices,
)

SEARCH_METHODS = ("fw", "pairwise", "factor", "entropy", "corrective", "auto")

#: The run tier's PUBLIC split of :data:`SEARCH_METHODS`: the methods an
#: ordinary configuration chooses (``solver.method``) and the expert ones it
#: reaches only through ``solver.advanced.method``
#: (:class:`~certiqs_key.runs.config.SolverSettings`). The solver tier itself
#: admits all six alike; the split is presentation, and together the two are
#: exactly :data:`SEARCH_METHODS`.
ORDINARY_METHODS = ("auto", "fw")
ADVANCED_METHODS = ("pairwise", "factor", "entropy", "corrective")
assert sorted(ORDINARY_METHODS + ADVANCED_METHODS) == sorted(SEARCH_METHODS)


@dataclass(frozen=True)
class SearchRequest:
    """One solver-wide budget and a diagnostic target; no assurance controls.

    Native iterations are a per-attempt cap, not comparable work units.
    Under ``auto`` they cap the Frank-Wolfe stages only; its factor, entropy
    and corrective stages run to their own convergence or their deadline
    share (``solvers/solve.py``). Explicit FW with no wall budget retains
    historical iteration semantics.
    """

    method: str = "fw"
    budget_seconds: float | None = None
    max_iterations: int = 200
    gap_target: float = FrankWolfeOptions().gap_tolerance
    oracle: str = "qics"
    warm_start: WarmStart | None = None
    #: ``frank-wolfe/req:certified-evaluation``'s option: ``on``, ``off`` or
    #: ``strict``. Not a search choice; it rides here to reach the solve.
    certified_evaluation: str = "on"

    def __post_init__(self) -> None:
        """Validate effort without exposing proof thresholds."""
        if self.certified_evaluation not in ("on", "off", "strict"):
            raise ValueError(
                f"unknown certified_evaluation {self.certified_evaluation!r}"
            )
        if self.method not in SEARCH_METHODS:
            raise ValueError(f"unknown search method {self.method!r}")
        if self.oracle not in ("qics", "spectral"):
            raise ValueError(f"unknown linear oracle {self.oracle!r}")
        if self.budget_seconds is not None and (
            not math.isfinite(self.budget_seconds) or self.budget_seconds <= 0
        ):
            raise ValueError("budget_seconds must be finite and positive")
        if isinstance(self.max_iterations, bool) or self.max_iterations < 1:
            raise ValueError("max_iterations must be positive")
        if not math.isfinite(self.gap_target) or self.gap_target < 0:
            raise ValueError("gap_target must be finite and nonnegative")

    def fw_options(self) -> JointFrankWolfeOptions:
        """Resolve search choices while keeping the original threshold defaults."""
        return JointFrankWolfeOptions(
            max_iterations=self.max_iterations,
            gap_tolerance=self.gap_target,
            oracle=self.oracle,
            step_rule="pairwise" if self.method == "pairwise" else "vanilla",
            warm_start=self.warm_start,
        )

    @classmethod
    def from_options(cls, options: FrankWolfeOptions | None) -> SearchRequest:
        """Translate the internal explicit FW replay settings without changing them."""
        settings = options or FrankWolfeOptions()
        oracle, step, warm = joint_choices(settings)
        return cls(
            method="pairwise" if step == "pairwise" else "fw",
            max_iterations=settings.max_iterations,
            gap_target=settings.gap_tolerance,
            oracle=oracle,
            warm_start=warm,
        )


if TYPE_CHECKING:
    from certiqs_key.solvers.assessment import CandidateAssessment
    from certiqs_key.solvers.frank_wolfe.reference import KeptPoint


@dataclass
class StageTimings:
    """Per-stage wall time and call counts.

    A MEASUREMENT AND NEVER AN INPUT: no number a run reports depends on any
    field here, and nothing branches on one. The stages are the four an
    optimizer comparison's numerics section names -- the gradient, the linear oracle,
    the line search and the objective evaluations inside it -- plus the build of
    the generated maps, which a caller times around
    :func:`~certiqs_key.meat_core.objective.joint.build_joint_maps`.
    """

    seconds: dict[str, float] = field(default_factory=dict)
    calls: dict[str, int] = field(default_factory=dict)

    def record(self, stage: str, seconds: float) -> None:
        """Add one measurement to a stage."""
        self.seconds[stage] = self.seconds.get(stage, 0.0) + seconds
        self.calls[stage] = self.calls.get(stage, 0) + 1

    def as_payload(self) -> dict[str, Any]:
        """Return the record's serialisable form, seconds and calls per stage."""
        return {
            "seconds": dict(sorted(self.seconds.items())),
            "calls": dict(sorted(self.calls.items())),
        }


@dataclass(frozen=True)
class JointIterateGate:
    """What the hypothesis gate found at one iterate of the general format."""

    iteration: int
    objective: float
    linearization: float
    oracle_optimal: bool
    min_block_eigenvalue: float
    coupling_residual: float
    withdrawal: str | None
    constraint_row_residual: float = 0.0
    acceptance_iterate_exact: bool = False
    #: The status the backend reported at this iterate's oracle call, the
    #: first that asserts no optimality where several groups were called, and
    #: ``not-called`` where the gradient failed before any call. A DIAGNOSTIC,
    #: like ``oracle_optimal``: no status withdraws an iterate
    #: (``req:first-order-withdrawal``).
    oracle_status: str = "not-called"
    #: The joint label of the block carrying ``min_block_eigenvalue``, and the
    #: Alice sector carrying ``coupling_residual`` (``*`` in untrusted mode).
    min_block_eigenvalue_at: str = ""
    coupling_residual_at: str = ""
    #: ``req:verified-feasible-side`` (vi), per bracket: ``b^F_t`` as it entered
    #: the bracket, rounded toward ``-inf`` (``None`` where no bracket was
    #: formed); the sum of the frame deductions it contains; the sum of the
    #: bounds on the row multipliers' norms it used. Only the first enters a
    #: number.
    feasible_side_bound: float | None = None
    frame_deduction: float = 0.0
    row_multiplier_norm: float = 0.0
    #: Diagnostics, entering no number: the gradient's pairing with the point
    #: the backend returned, where it returned one, and that pairing less
    #: ``b^F_t`` with its sign (``dual_gap``: positive where the return pairs
    #: above the verified bound, negative where an infeasible return pairs
    #: below it).
    oracle_pairing: float | None = None
    dual_gap: float | None = None
    #: Per group, whose multipliers the bound used: ``backend``, ``zero`` or
    #: ``rows_zeroed`` (:mod:`~certiqs_key.solvers.frank_wolfe.verified`).
    feasible_side_multipliers: Mapping[str, str] = field(default_factory=dict)

    @property
    def contributes(self) -> bool:
        """Return whether this iterate is a member of the index set of ``eq:hlb``."""
        return self.withdrawal is None


@dataclass(frozen=True)
class SearchResult:
    """Generic solver outcome with estimate and contributing candidate separated.

    ``h_lb`` and ``h_lb_dropped`` are never both present: the first is
    ``eq:hlb`` of ``thm:firstorder`` and exists exactly when the dropped set is
    empty; the second is ``eq:hlb-dropped`` of ``cor:fo-dropped`` and exists
    exactly when it is not. That is the interface's own rule -- "IT IS REPORTED
    UNDER ITS OWN NAME, WITH D BESIDE IT, AND NEVER AS h_lb" -- and a single
    field would have made the confusion expressible.
    """

    objective: float
    choi: Mapping[JointSector, Matrix]
    q: Mapping[str, float]
    #: Explicit FW native iterations, or assessment count for a portfolio.
    #: search_report["iteration_unit"] disambiguates; method counts stay in attempts.
    iterations: int
    gap: float
    h_lb: float | None
    h_lb_dropped: float | None
    dropped_set: tuple[tuple[str, JointSector], ...]
    withdrawal: str | None
    status: str
    gates: tuple[JointIterateGate, ...] = ()
    oracle_diagnostics: tuple[Mapping[str, Any], ...] = ()
    timings: StageTimings = field(default_factory=StageTimings)
    mathematical_spec_version: str = MATHEMATICAL_SPEC_VERSION
    reported_tier: str = "estimate"
    assumption_ledger: tuple[str, ...] = ()
    choi_input_basis: Mapping[str, Any] = field(default_factory=dict)
    constraint_row_form: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    #: HOW THE LOOP RAN: the oracle choice and the backend of every group, the
    #: step rule and its counts, and the eigen-residual evidence of the
    #: spectral backend (:func:`solver_report`). A record of the path, never an
    #: input to any number.
    solver_report: Mapping[str, Any] = field(default_factory=dict)
    #: WHAT THE POINT THE ESTIMATE IS TAKEN AT MEASURES, once, at loop exit:
    #: that point is ``choi``, and when the run ends by the iteration limit
    #: or at a hypothesis no gate consumed it. ``None`` only where no point
    #: was measured (a result formed outside this driver).
    returned_point: PointCheck | None = None
    #: Whether that point is ESTABLISHED in the relaxed set ``rem:fo-interface``
    #: rests the estimate on (``rem:fo-returned-point``): per-block positivity at
    #: exactly ``0``, the coupling at ``iterate_coupling`` and the declared rows
    #: at ``constraint_rows`` (``rem:fo-iterate-checks``). A RECORD, not a
    #: gate: it changes no bracket, no tier and no key length.
    estimate_point_relaxed_member: bool = False
    best_assessment: CandidateAssessment | None = None
    search_report: Mapping[str, Any] = field(default_factory=dict)
    #: THE FIRST SET OF POINTS ``meat-core/frank-wolfe/req:bracket-on-reference``
    #: (i) EVALUATES ON A REFERENCE COMPANION: the at most four contributing
    #: assessments with the largest brackets, then the last one the search
    #: formed, each with its roles (``best``, ``last``) and the position at
    #: which the search consumed it
    #: (:class:`~certiqs_key.solvers.frank_wolfe.reference.KeptPoint`). Kept by
    #: :class:`~certiqs_key.solvers.frank_wolfe.reference.ReferenceCandidates`
    #: while the search runs; the certified evaluation on the searched
    #: declaration reads the same points.
    reference_candidates: tuple[KeptPoint, ...] = field(
        default=(), repr=False, compare=False
    )


class PointCheck(NamedTuple):
    """What :func:`_check_point` measured on a point, and where."""

    #: The smallest block eigenvalue, and the joint label of its block.
    smallest: float
    smallest_at: str
    #: The worst coupling residual, and its Alice sector (``*`` untrusted).
    worst: float
    worst_at: str
    #: The worst declared-row residual (``0.0`` without rows).
    rows: float

    def relaxed_member(self, options: FrankWolfeOptions) -> bool:
        """Return whether the coupling and the rows each pass their own window.

        The two residual checks of ``rem:fo-iterate-checks`` (``rem:feas-tol``);
        positivity at exactly ``0`` is the caller's, being decided on the
        consumed point only.
        """
        return (
            self.worst <= options.iterate_coupling
            and self.rows <= options.constraint_rows
        )

    def established(self, options: FrankWolfeOptions) -> bool:
        """Return whether the point is in ``Feas^J(epsilon)`` by all three checks.

        ``rem:fo-iterate-checks``: positivity at exactly ``0`` and at no window,
        and :meth:`relaxed_member`.
        """
        return self.smallest >= 0.0 and self.relaxed_member(options)
