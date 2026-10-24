"""The first-order bound evaluated on the reference companion, and its polish.

``meat-core/frank-wolfe/req:bracket-on-reference``, by
``meat-core/frank-wolfe/cor:fo-reference``.

WHY THIS EXISTS. ``thm:firstorder`` asks nothing about where its points came
from. The search runs on the declaration ``D`` compiled from the snapped
measurement; after it ends, the bracket ``eq:hlb`` is formed on the compiled
reference companion ``D^ref`` (evaluation-only, that is with no run of its
own: ``meat-core/req:companion-admission``) at the points of two sets: a few
of the search's, and those of the POLISH, a short search continued on
``D^ref``'s own program from the best of them. Where some point contributes,
that bracket is the run's first-order number: no number the key length is
computed from reads the snapped family on a block the companion carries the
reference on (``foundations/def:evaluated-off-snap`` (ii)).

WHY THE POLISH. The search fits the acceptance-side component ``q`` to the
snapped statistics. Where the snap moved an entry that is small beside its
outcome's probability (a dark-count product near ``1e-12`` on the ``2^-40``
lattice), the companion's statistics at the same point differ from ``q`` by a
relative amount of the move's size, which the factor ``alpha/(alpha-1)``
magnifies: on BBM92 with an SPDC source, dark counts ``1e-6`` and a key-round
probability near ``2e-6`` per round, the bracket on ``D^ref`` at the search's
points was ``-4.7e-3`` against ``1.08e-6`` on ``D``, a key of 0 where a
corrective search on ``D^ref`` from the best of them recovers ``D``'s bound in
under a second. Its points are points like any other: the gate decides them as
it decides the search's.

WHAT IS HERE.

* :class:`ReferenceCandidates` keeps, while a search runs, the points of one
  set of item (i): the at most four contributing points with the largest
  brackets, ties broken by the order the search consumed them, and the last
  point it assessed, each with that order (:class:`KeptPoint`). The search on
  ``D`` feeds it every assessment it forms (the first set, brackets on ``D``);
  so does the polish (the second set, brackets on ``D^ref``).
* :func:`polish_on_reference` is the polish of item (i): a corrective search
  on ``D^ref``'s maps (Frank-Wolfe where the acceptance geometry admits no
  corrective search), started at the first set's point with the largest
  bracket on ``D`` with that point's exact ``q``, each point it consumes
  assessed by the gate of item (ii), within its share
  (:data:`REFERENCE_POLISH_SHARE`) of the wall budget of one evaluation and
  its iteration cap (:data:`POLISH_MAX_ITERATIONS`). It refuses nothing on
  the sign of an objective value: those are no estimate of the run
  (``req:negative-estimate-refused``). It does not run where the start
  point's ``q`` was not formed on the exact island (:data:`START_NOT_EXACT`).
* :func:`bracket_on_reference` is items (i)-(iv), (vi): the maps of ``D^ref``
  generated from its own slots (``def:maps``) over ``D``'s acceptance
  support, and at each point of the first set the gate the search itself uses
  (:func:`~certiqs_key.solvers.assessment.assess_first_order`): the objective
  of ``D^ref`` at the point, its gradient with no perturbation (the search's
  ``gradient_perturbation`` is set to zero here, whatever it was), the
  acceptance-side minimisation on the run's one acceptance set, and the
  feasible side of ``req:verified-feasible-side`` from a FRESH oracle call
  over ``D^ref``'s entries -- verified from that call's dual against the
  companion's own exact rows, and from the multipliers the solves left where
  the call returns a status that asserts nothing (no status withdraws a
  point, ``req:first-order-withdrawal``) -- with every check of
  ``req:iterate-checks`` against those entries, on the point. Each point is
  taken as the search consumed it, ``q_t`` included (item (i)). The polish's
  points were assessed by that same gate on ``D^ref`` as it consumed them,
  so their assessments are the brackets of item (ii) and are not formed
  twice.
* :meth:`ReferenceBracket.certification_points` is the selection of
  ``req:certified-evaluation`` (i) on a companion: the at most five points of
  the two sets together that contribute with the largest brackets on the
  companion, a point in both sets counted once, ties by the order the search
  and then the polish consumed them. A maximum over fewer certified brackets
  is still a lower bound, and the evaluation stays a small part of the run.

ITEM (iv)'S SECOND CAUSE is decided later, by the certified evaluation: where
it finds the two enclosures of a block the companion carries inconsistent
(``req:certified-evaluation`` (iv)(c)), the caller withdraws a bracket that
counted with :meth:`ReferenceBracket.withdrawn` and forms the run's
first-order number again on ``D``
(:func:`~certiqs_key.solvers.frank_wolfe.general_keyrate.solve_general`).

A FAILURE TO GENERATE THE COMPANION'S MAPS WITHDRAWS THE COMPANION, it never
stops the run (``maps_cross_validated`` is a
hard error of a declaration the engine solves, and the companion's evaluated
numbers need not be a POVM, so a refusal there is recorded and the run falls
back by item (iv)). A FAILED OR CUT POLISH KEEPS THE POINTS IT ASSESSED and
the run goes on with them and the first set's. A dropped set is not evaluated
on the companion: no claim states ``eq:hlb-dropped`` on it, and the run keeps
``cor:fo-dropped`` on ``D``; nor is it polished.
"""

from __future__ import annotations

import math
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from fractions import Fraction
from typing import TYPE_CHECKING, Any, Final, NamedTuple

import numpy as np

from certiqs_key.meat_core.errors import MeatError
from certiqs_key.meat_core.objective.joint import (
    JointMaps,
    JointSector,
    build_joint_maps,
    joint_choi_parametrization,
    joint_objective_value,
    normalise_dropped_set,
)
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.solvers.assessment import (
    CandidateAssessment,
    assess_candidate,
    assess_first_order,
)
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_options import (
    JointFrankWolfeOptions,
    joint_choices,
    oracle_assignment,
)
from certiqs_key.solvers.oracles.acceptance import AcceptanceOracle
from certiqs_key.solvers.oracles.joint_rows import prebuilt_rows
from certiqs_key.solvers.oracles.protocol import LinearOracle
from certiqs_key.solvers.types import JointIterateGate, StageTimings

if TYPE_CHECKING:
    from certiqs_key.meat_core.declaration.companion import AdmittedCompanion
    from certiqs_key.solvers.problem import PreparedProblem

__all__ = [
    "BEST_POINTS",
    "CERTIFIED_POINTS",
    "POLISH_MAX_ITERATIONS",
    "REFERENCE_BRACKET_WITHDRAWN",
    "REFERENCE_POLISH_SHARE",
    "START_NOT_EXACT",
    "EvaluatedPoint",
    "KeptPoint",
    "PointSet",
    "PolishOutcome",
    "PolishRecord",
    "ReferenceBracket",
    "ReferenceCandidates",
    "ReferencePoint",
    "ReferenceStatus",
    "bracket_on_reference",
    "feasible_side_record",
    "polish_on_reference",
    "reference_record",
]

#: Item (i): at most this many contributing points with the largest brackets
#: of each set, beside its last point (the best four, plus the last).
BEST_POINTS: Final[int] = 4

#: ``req:certified-evaluation`` (i): on a companion, at most this many points
#: of the two sets together are certified.
CERTIFIED_POINTS: Final[int] = 5

#: ``reference_polish_share`` (frank-wolfe interface, ``fixed_by_this_file``):
#: the share of the wall budget of one evaluation of the run set aside for the
#: polish before the search on ``D`` begins. The polish's points can only
#: raise a maximum of valid brackets, so the value bears on tightness and wall
#: time, on nothing a claim rests on.
REFERENCE_POLISH_SHARE: Final[Fraction] = Fraction(1, 10)

#: The polish's iteration cap, recorded with it: the corrective search's outer
#: iterations, or the Frank-Wolfe iterations where it runs that, at most the
#: run's own cap. The corrective default; the probes' polishes stopped by
#: their own stopping rule well within it.
POLISH_MAX_ITERATIONS: Final[int] = 20

#: Why the polish did not run: its start point's acceptance-side component
#: was not formed on the exact island (req:bracket-on-reference (i)).
START_NOT_EXACT: Final[str] = "start_not_exact"
#: Why the polish did not run: the search on ``D`` assessed no point.
NO_START_POINT: Final[str] = "no_start_point"

#: The one string the reference companion adds to the withdrawal vocabulary
#: (frank-wolfe ``the_reference_companion_adds_one_string``): no evaluated
#: point contributed on the companion, so the run's first-order number is the
#: bound on ``D`` (item (iv)). A record of which number counts; it withdraws no
#: first-order number.
REFERENCE_BRACKET_WITHDRAWN: Final[str] = "reference_bracket_withdrawn"


class ReferenceStatus(StrEnum):
    """Which number the run's first-order number is, and why."""

    #: Some evaluated point contributed: the number is ``h_lb[D^ref]`` (iii).
    COUNTED = "counted"
    #: No evaluated point contributed, or the companion's maps could not be
    #: generated: the number is ``h_lb[D]`` (iv).
    WITHDRAWN = "withdrawn"
    #: The companion was not admitted (``req:companion-admission`` (i)), or the
    #: run evaluates a dropped program: nothing was evaluated on it.
    NOT_EVALUATED = "not_evaluated"


class PointSet(StrEnum):
    """Which set of item (i) a point belongs to."""

    #: The first: points of the search on ``D``.
    SEARCH = "search"
    #: The second: points the polish on ``D^ref`` kept.
    POLISH = "polish"


class KeptPoint(NamedTuple):
    """One kept point of a set: the assessment, its roles and its order.

    ``sequence`` is the position, counted from one, at which the search (or
    the polish) consumed the point among every point it assessed: the order
    of the run that breaks ties.
    """

    assessment: CandidateAssessment
    roles: tuple[str, ...]
    sequence: int


@dataclass(frozen=True)
class ReferencePoint:
    """Item (vi), per evaluated point: its set, brackets and the companion's reasons.

    ``bracket_snapped`` is the point's bracket on ``D``, for a point of the
    first set; ``None`` for a point of the polish, which assessed it on
    ``D^ref`` only. ``feasible_side_reference`` is the record
    ``req:verified-feasible-side`` (vi) asks of the companion's bracket at the
    point (``None`` where none was formed): the bound, its frame deduction and
    row-multiplier norm, the oracle's pairing and the dual gap, and per group
    whose multipliers it used.
    """

    iteration: int
    roles: tuple[str, ...]
    bracket_snapped: float | None
    bracket_reference: float | None
    objective_reference: float | None
    withdrawal_reference: str | None
    feasible_side_reference: Mapping[str, Any] | None = None
    point_set: PointSet = PointSet.SEARCH

    def as_record(self) -> dict[str, Any]:
        """JSON-ready."""
        return {
            "set": str(self.point_set),
            "iteration": self.iteration,
            "roles": list(self.roles),
            "bracket_snapped": self.bracket_snapped,
            "bracket_reference": self.bracket_reference,
            "objective_reference": self.objective_reference,
            "withdrawal_reference": self.withdrawal_reference,
            "feasible_side_reference": (
                None
                if self.feasible_side_reference is None
                else dict(self.feasible_side_reference)
            ),
        }


@dataclass(frozen=True)
class EvaluatedPoint:
    """One evaluated point, as the certified evaluation reads it.

    ``candidate`` is the point as the search or the polish consumed it, its
    ``q`` included; ``reference`` its assessment on ``D^ref`` by the gate of
    item (ii) (``None`` where that failed), whose solves the certified
    evaluation reads. For a polish point the two are the same assessment.
    ``sequence`` orders the search's points before the polish's, each in the
    order it consumed them.
    """

    point_set: PointSet
    sequence: int
    candidate: CandidateAssessment
    reference: CandidateAssessment | None

    @property
    def bracket(self) -> float | None:
        """The point's bracket on the companion, where it contributes there."""
        if self.reference is None:
            return None
        bracket = self.reference.bracket
        return None if bracket is None or math.isnan(bracket) else bracket


def feasible_side_record(gate: JointIterateGate) -> dict[str, Any] | None:
    """Return ``req:verified-feasible-side`` (vi)'s per-bracket record of a gate."""
    if gate.feasible_side_bound is None:
        return None
    return {
        "feasible_side_bound": gate.feasible_side_bound,
        "frame_deduction": gate.frame_deduction,
        "row_multiplier_norm": gate.row_multiplier_norm,
        "oracle_pairing": gate.oracle_pairing,
        "dual_gap": gate.dual_gap,
        "feasible_side_multipliers": dict(gate.feasible_side_multipliers),
    }


@dataclass(frozen=True)
class PolishRecord:
    """Item (vi)'s record of the polish (the frank-wolfe interface's ``polish``).

    ``ran`` and, where it did not, ``reason`` (:data:`START_NOT_EXACT`,
    :data:`NO_START_POINT`); ``start_index``, the index in the first set of
    the point it started from; ``share`` and ``budget_seconds``, the share of
    the evaluation's wall budget set aside for it and the seconds that gave
    (``None`` where the evaluation has no wall budget); ``seconds``, the wall
    time it took; ``method`` and ``iteration_cap``; ``points_assessed``;
    ``stop_cause``: ``share_spent``, ``iteration_cap``, its own stopping rule
    (``stagnated``, ``gap_target``) or a failure (``oracle_failure``,
    ``numerical_failure``, ``assessment_failure``, ``preparation_failure``),
    with ``detail``.
    """

    ran: bool
    reason: str | None
    start_index: int | None
    share: Fraction
    budget_seconds: float | None
    seconds: float
    method: str | None
    iteration_cap: int | None
    points_assessed: int
    stop_cause: str | None
    detail: str = ""

    def as_record(self) -> dict[str, Any]:
        """JSON-ready."""
        return {
            "ran": self.ran,
            "reason": self.reason,
            "start_index": self.start_index,
            "share": str(self.share),
            "budget_seconds": self.budget_seconds,
            "seconds": self.seconds,
            "method": self.method,
            "iteration_cap": self.iteration_cap,
            "points_assessed": self.points_assessed,
            "stop_cause": self.stop_cause,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class PolishOutcome:
    """What the polish returns: its record and its kept points, on ``D^ref``."""

    record: PolishRecord
    kept: tuple[KeptPoint, ...] = ()


@dataclass(frozen=True)
class ReferenceBracket:
    """What ``req:bracket-on-reference`` formed, for the record (item (vi)).

    ``cause`` is the second cause of item (iv), ``factor_enclosure_inconsistent``,
    where the certified evaluation withdrew a bracket that counted
    (:meth:`withdrawn`); ``None`` otherwise, the first cause included (no
    evaluated point contributed).
    """

    status: ReferenceStatus
    reason: str | None
    h_lb_reference: float | None
    points: tuple[ReferencePoint, ...] = ()
    detail: str = ""
    #: Wall-clock seconds of the evaluation (maps, points and polish). A
    #: diagnostic.
    seconds: float = field(default=0.0, compare=False)
    #: The companion's maps and every evaluated point with its assessment on
    #: the companion: what the certified evaluation reads
    #: (``req:certified-evaluation`` (i), :meth:`certification_points`). Not
    #: recorded.
    maps: JointMaps | None = field(default=None, compare=False, repr=False)
    evaluations: tuple[EvaluatedPoint, ...] = field(
        default=(), compare=False, repr=False
    )
    cause: str | None = None
    #: The polish's record; ``None`` where nothing was evaluated on the
    #: companion or its maps could not be generated.
    polish: PolishRecord | None = None

    @property
    def counted(self) -> bool:
        """Whether the run's first-order number is the bound on the companion."""
        return self.status is ReferenceStatus.COUNTED

    def certification_points(self) -> tuple[EvaluatedPoint, ...]:
        """Return the points ``req:certified-evaluation`` (i) certifies on a companion.

        The at most :data:`CERTIFIED_POINTS` evaluated points, of the search
        and of the polish together, that contribute on the companion with the
        largest brackets there; a point in both sets (the polish's start,
        which it consumes first as the search consumed it) counted once, as
        the search's; ties broken by the order in which the search and then
        the polish consumed them.
        """
        pool: list[EvaluatedPoint] = []
        seen: set[tuple[Any, ...]] = set()
        for item in sorted(self.evaluations, key=lambda e: e.sequence):
            if item.bracket is None:
                continue
            key = _point_key(item.candidate)
            if key in seen:
                continue
            seen.add(key)
            pool.append(item)
        pool.sort(key=lambda e: (-(e.bracket or 0.0), e.sequence))
        return tuple(pool[:CERTIFIED_POINTS])

    def withdrawn(self, cause: str, detail: str) -> ReferenceBracket:
        """Return this bracket withdrawn by item (iv)'s second cause.

        Decided after the companion's number was formed, by the certified
        evaluation (``req:certified-evaluation`` (iv)(c)); the run forms its
        first-order number again on the searched declaration. The companion's
        number and its points stay in the record as formed, with the reason
        ``reference_bracket_withdrawn`` and the cause.
        """
        return replace(
            self,
            status=ReferenceStatus.WITHDRAWN,
            reason=REFERENCE_BRACKET_WITHDRAWN,
            cause=cause,
            detail=detail,
        )

    def as_record(self) -> dict[str, Any]:
        """JSON-ready."""
        return {
            "status": str(self.status),
            "reason": self.reason,
            "cause": self.cause,
            "detail": self.detail,
            "h_lb_reference": self.h_lb_reference,
            "points": [point.as_record() for point in self.points],
            "polish": None if self.polish is None else self.polish.as_record(),
            "seconds": self.seconds,
        }


def _point_key(assessment: CandidateAssessment) -> tuple[Any, ...]:
    """Return a key equal exactly for equal points ``(q_t, J_t)``."""
    q = assessment.q_iterate
    q_part: tuple[Any, ...] = (
        tuple(sorted((key, value) for key, value in q.exact.items()))
        if q.exact is not None
        else tuple(sorted(q.view.items()))
    )
    blocks = tuple(
        (str(pair), np.ascontiguousarray(block, dtype=np.complex128).tobytes())
        for pair, block in sorted(assessment.point.items(), key=lambda i: str(i[0]))
    )
    return (q_part, blocks)


class ReferenceCandidates:
    """The points of one set of item (i), kept while a search runs.

    Fed every :class:`~certiqs_key.solvers.assessment.CandidateAssessment` in
    the order the search formed them; keeps the :data:`BEST_POINTS`
    contributing ones with the largest brackets (an earlier point winning a
    tie) and the last one, each with its position in that order. Holding five
    assessments, not every iterate's, keeps the search's memory what it was.
    """

    def __init__(self) -> None:
        """Start with no point kept."""
        self._best: list[tuple[float, int, CandidateAssessment]] = []
        self._last: CandidateAssessment | None = None
        self._seen = 0

    @property
    def seen(self) -> int:
        """How many assessments were observed."""
        return self._seen

    def observe(self, assessment: CandidateAssessment) -> None:
        """Take one assessment, in the run's order."""
        self._seen += 1
        self._last = assessment
        bracket = assessment.bracket
        if bracket is None or math.isnan(bracket):
            return
        self._best.append((bracket, self._seen, assessment))
        self._best.sort(key=lambda item: (-item[0], item[1]))
        del self._best[BEST_POINTS:]

    def points(self) -> tuple[KeptPoint, ...]:
        """Return the kept points with their roles, best first, last after."""
        out: list[KeptPoint] = []
        last = self._last
        for _, sequence, assessment in self._best:
            roles = ("best",) if assessment is not last else ("best", "last")
            out.append(KeptPoint(assessment, roles, sequence))
        if last is not None and all(item.assessment is not last for item in out):
            out.append(KeptPoint(last, ("last",), self._seen))
        return tuple(out)


#: What ends the polish as a failure, its assessed points kept: an
#: engine refusal (an oracle failure among them), a numerical error.
_FAILURES: Final[tuple[type[Exception], ...]] = (
    MeatError,
    ValueError,
    ArithmeticError,
    np.linalg.LinAlgError,
)


def _reason(failure: Exception) -> str:
    reason = getattr(failure, "reason", None)
    return str(reason) if reason is not None else type(failure).__name__


class _PolishStop(Exception):
    """End the polish at a checkpoint, with its cause.

    Not a ``MeatError`` nor an ``ArithmeticError``, so the corrective search's
    own numerical catch cannot turn it into its termination.
    """

    def __init__(self, cause: str, detail: str = "") -> None:
        super().__init__(cause)
        self.cause = cause
        self.detail = detail


def _polish_settings(settings: FrankWolfeOptions) -> FrankWolfeOptions:
    """Return the polish's settings: no gradient perturbation, no warm start.

    Item (ii)'s gate forms the gradient with no perturbation, and the polish
    starts at its own point, which a warm start would contradict.
    """
    exact = replace(settings, gradient_perturbation=0.0)
    if isinstance(exact, JointFrankWolfeOptions) and exact.warm_start is not None:
        exact = replace(exact, warm_start=None)
    return exact


def _same_point(
    first: CandidateAssessment,
    point: Mapping[JointSector, Matrix],
    exact: Mapping[str, Fraction] | None,
) -> bool:
    """Return whether ``(exact, point)`` is the point ``first`` consumed."""
    if exact is None or first.q_iterate.exact is None:
        return False
    if dict(exact) != first.q_iterate.exact or first.point.keys() != point.keys():
        return False
    return all(np.array_equal(first.point[pair], point[pair]) for pair in point)


def polish_on_reference(
    reference_maps: JointMaps,
    oracle: LinearOracle,
    acceptance: AcceptanceOracle,
    alpha: float,
    settings: FrankWolfeOptions,
    start: KeptPoint | None,
    *,
    start_index: int | None = 0,
    budget_seconds: float | None = None,
    skip_key_inert: bool = True,
) -> PolishOutcome:
    """Run the polish of ``req:bracket-on-reference`` (i) on ``D^ref``.

    ``reference_maps`` are the companion's maps; ``start`` the first set's
    point with the largest bracket on ``D`` (its last point where ``D``'s
    index set is empty), at ``start_index`` in the first set; ``budget_seconds``
    the share of the evaluation's wall budget set aside for the polish
    (``None`` where the evaluation has none: the iteration cap alone bounds
    it). The polish consumes the start first, as the search consumed it, its
    exact ``q`` included, and then the points of a corrective search on the
    companion's maps from there (of the Frank-Wolfe driver where the
    acceptance geometry admits no corrective search, its ``q`` iterate seeded
    with the start's), each assessed by the gate of item (ii) on ``D^ref``;
    it keeps the four best contributing points and its last. Where the
    start's ``q`` was not formed on the exact island it does not run
    (:data:`START_NOT_EXACT`). It refuses nothing on the sign of an
    objective value (``req:negative-estimate-refused``: none is an estimate
    of the run), and a failure or a cut ends it with the points it assessed
    kept.
    """
    started = time.perf_counter()
    cap = min(POLISH_MAX_ITERATIONS, settings.max_iterations)

    def record(**fields: Any) -> PolishRecord:
        base: dict[str, Any] = {
            "ran": True,
            "reason": None,
            "start_index": start_index,
            "share": REFERENCE_POLISH_SHARE,
            "budget_seconds": budget_seconds,
            "seconds": time.perf_counter() - started,
            "method": None,
            "iteration_cap": cap,
            "points_assessed": 0,
            "stop_cause": None,
        }
        base.update(fields)
        return PolishRecord(**base)

    if start is None:
        return PolishOutcome(
            record(
                ran=False,
                reason=NO_START_POINT,
                start_index=None,
                detail="the search on the snapped declaration assessed no point",
            )
        )
    first_q = start.assessment.q_iterate
    if not first_q.on_island:
        return PolishOutcome(
            record(
                ran=False,
                reason=START_NOT_EXACT,
                detail=(
                    "the start point's acceptance-side component was not formed "
                    "on the exact island (req:acceptance-iterate-exact), so the "
                    "polish does not run and its set is empty "
                    "(req:bracket-on-reference (i))"
                ),
            )
        )
    from certiqs_key.solvers.problem import prepared_from_maps
    from certiqs_key.solvers.search.common import capability_reason

    deadline = None if budget_seconds is None else started + budget_seconds
    keeper = ReferenceCandidates()
    assessed: list[CandidateAssessment] = []
    timings = StageTimings()
    method: str | None = None
    try:
        problem = replace(
            prepared_from_maps(
                reference_maps,
                oracle,
                acceptance,
                alpha,
                _polish_settings(settings),
                start=start.assessment.point,
            ),
            skip_key_inert=skip_key_inert,
        )
        corrective = capability_reason(problem, "corrective") is None
        method = "corrective" if corrective else "fw"
    except _FAILURES as failure:
        return PolishOutcome(
            record(
                stop_cause="preparation_failure",
                detail=f"{_reason(failure)}: {failure}",
            )
        )

    def consume(
        point: Mapping[JointSector, Matrix], exact: Mapping[str, Fraction] | None
    ) -> CandidateAssessment:
        try:
            assessment = assess_candidate(
                problem,
                point,
                exact,
                iteration=len(assessed) + 1,
                timings=timings,
                bound_unsolved=True,
            )
        except _FAILURES as failure:
            raise _PolishStop(
                "assessment_failure", f"{_reason(failure)}: {failure}"
            ) from failure
        keeper.observe(assessment)
        assessed.append(assessment)
        if assessment.oracle_failure is not None:
            raise _PolishStop("oracle_failure", str(assessment.oracle_failure))
        return assessment

    def spent() -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    stop: str
    detail = ""
    try:
        if method == "corrective":
            stop, detail = _polish_corrective(
                problem, start, consume, spent, deadline, cap
            )
        else:
            stop = _polish_frank_wolfe(
                problem, start, keeper, assessed, deadline, cap, skip_key_inert
            )
    except _PolishStop as stopped:
        stop, detail = stopped.cause, stopped.detail
    except _FAILURES as failure:
        stop, detail = "numerical_failure", f"{_reason(failure)}: {failure}"
    return PolishOutcome(
        record(
            method=method,
            points_assessed=keeper.seen,
            stop_cause=stop,
            detail=detail,
        ),
        keeper.points(),
    )


def _polish_corrective(
    problem: PreparedProblem,
    start: KeptPoint,
    consume: Any,
    spent: Any,
    deadline: float | None,
    cap: int,
) -> tuple[str, str]:
    """Run the polish as one corrective search; return its stop cause and detail.

    One search, from the start point, to its own stagnation, the share or the
    cap. Measured on the BBM92 probes, restarting it from its best point (as
    the portfolio's corrective series does) or polishing with the factor
    search instead raised no bracket: the corrective step that moves ``q`` and
    ``J`` onto the companion's statistics is what recovers the bound.
    """
    from certiqs_key.solvers.search.common import CorrectiveSettings
    from certiqs_key.solvers.search.corrective import search_corrective

    before = time.perf_counter()
    first = consume(start.assessment.point, start.assessment.q_iterate.exact)
    # One assessment's time is kept back for the final one, as the portfolio
    # reserves it, so that the search's best point is assessed within the share.
    reserve = time.perf_counter() - before
    if spent():
        return "share_spent", ""
    last = first

    def checkpoint(
        point: Mapping[JointSector, Matrix], exact: Mapping[str, Fraction]
    ) -> bool:
        nonlocal last
        last = consume(point, exact)
        return bool(spent())

    outcome = search_corrective(
        problem,
        start.assessment.point,
        settings=CorrectiveSettings(max_iterations=cap),
        deadline=None if deadline is None else deadline - reserve,
        checkpoint=checkpoint,
    )
    if not _same_point(last, outcome.point, outcome.q_exact):
        consume(outcome.point, outcome.q_exact)
    termination = outcome.termination
    if termination == "stagnated":
        return "stagnated", ""
    if termination == "numerical_failure":
        return "numerical_failure", str(outcome.diagnostics.get("message", ""))
    if termination == "budget_exhausted" and outcome.iterations >= cap:
        return "iteration_cap", ""
    return "share_spent", ""


def _polish_frank_wolfe(
    problem: PreparedProblem,
    start: KeptPoint,
    keeper: ReferenceCandidates,
    assessed: list[CandidateAssessment],
    deadline: float | None,
    cap: int,
    skip_key_inert: bool,
) -> str:
    """Run the polish as a Frank-Wolfe search; return its stop cause.

    Its first iterate is the start with the start's exact ``q``; every
    iterate is assessed by the driver with the gate of item (ii).
    """
    from certiqs_key.solvers.frank_wolfe.joint_driver import run_joint_frank_wolfe

    def observe(assessment: CandidateAssessment) -> None:
        keeper.observe(assessment)
        assessed.append(assessment)

    run = run_joint_frank_wolfe(
        problem.maps,
        problem.oracle,
        problem.acceptance,
        start.assessment.point,
        problem.alpha,
        replace(problem.settings, max_iterations=cap),
        skip_key_inert=skip_key_inert,
        anchor=problem.anchor,
        deadline=deadline,
        assessment_observer=observe,
        start_q=start.assessment.q_iterate,
    )
    return {
        "converged": "gap_target",
        "iteration-limit": "iteration_cap",
        "budget_exhausted": "share_spent",
    }.get(run.status, str(run.status))


def bracket_on_reference(
    admitted: AdmittedCompanion,
    maps: JointMaps,
    oracle: LinearOracle,
    acceptance: AcceptanceOracle,
    alpha: float,
    settings: FrankWolfeOptions,
    candidates: Iterable[KeptPoint],
    *,
    dropped: Iterable[tuple[str, JointSector]] = (),
    skip_key_inert: bool = True,
    polish_budget_seconds: float | None = None,
) -> ReferenceBracket:
    """Form ``eq:hlb`` on ``D^ref`` at the points of item (i): items (i)-(iv), (vi).

    ``maps`` are ``D``'s, read for its acceptance support and its joint
    sectors only; the companion's maps are generated from its own slots.
    ``acceptance`` is the run's one acceptance oracle. ``candidates`` are the
    first set (:class:`ReferenceCandidates` of the search on ``D``), best
    first; the polish (:func:`polish_on_reference`) starts at the first of
    them, within ``polish_budget_seconds``, the share set aside for it.
    Returns the bracket record; the caller forms the number and the key
    length (item (iii)) or falls back (item (iv)).
    """
    started = time.perf_counter()
    candidates = tuple(candidates)
    if tuple(dropped):
        return ReferenceBracket(
            ReferenceStatus.NOT_EVALUATED,
            "dropped_set_not_covered",
            None,
            detail=(
                "the run evaluates a dropped program (cor:fo-dropped); no claim "
                "states its bound on the reference companion"
            ),
            seconds=time.perf_counter() - started,
        )
    try:
        parametrization = joint_choi_parametrization(admitted.declaration)
        if parametrization.joint_sectors != maps.parametrization.joint_sectors or any(
            parametrization.block_dim(pair) != maps.parametrization.block_dim(pair)
            for pair in parametrization.joint_sectors
        ):
            return ReferenceBracket(
                ReferenceStatus.NOT_EVALUATED,
                "companion_joint_sectors_differ",
                None,
                detail="prop:reference-companion (i): the joint sectors are D's",
                seconds=time.perf_counter() - started,
            )
        reference_maps = build_joint_maps(
            parametrization, acceptance_support=maps.acceptance_support
        )
    except (MeatError, ValueError, ArithmeticError) as failure:
        return ReferenceBracket(
            ReferenceStatus.WITHDRAWN,
            REFERENCE_BRACKET_WITHDRAWN,
            None,
            detail=(
                "the companion's maps could not be generated from its evaluated "
                f"family ({_reason(failure)}: {failure}); the run falls back to "
                "the bound on the searched declaration"
            ),
            seconds=time.perf_counter() - started,
        )
    choice, _, _ = joint_choices(settings)
    assignment = oracle_assignment(reference_maps.parametrization, choice)
    from certiqs_key.solvers.frank_wolfe.joint_driver import _spectral_backend

    spectral = _spectral_backend(reference_maps.parametrization, assignment)
    rows = (
        prebuilt_rows(reference_maps.parametrization)
        if reference_maps.declaration.is_trusted_source
        else None
    )
    chosen = normalise_dropped_set(reference_maps, None)
    # Item (ii): the companion's gradient is formed WITH NO PERTURBATION,
    # whatever the search used. A search with
    # gradient_perturbation != 0 would otherwise withdraw every companion point
    # as gradient_perturbation_applied and fall back to h_lb[D].
    exact = replace(settings, gradient_perturbation=0.0)
    timings = StageTimings()
    points: list[ReferencePoint] = []
    evaluations: list[EvaluatedPoint] = []
    for candidate, roles, sequence in candidates:
        q_iterate = candidate.q_iterate
        try:
            value = joint_objective_value(
                reference_maps,
                q_iterate.view,
                candidate.point,
                alpha,
                dropped=chosen,
                skip_key_inert=skip_key_inert,
            )
            assessment = assess_first_order(
                reference_maps,
                oracle,
                acceptance,
                candidate.point,
                q_iterate,
                alpha,
                exact,
                chosen,
                rows,
                assignment,
                spectral,
                candidate.gate.iteration,
                timings,
                [],
                value,
                skip_key_inert,
                # NO STATUS REMOVES AN ITERATE (req:first-order-withdrawal):
                # an unsolved status of the fresh call is bounded with the
                # multipliers the solves left (req:verified-feasible-side
                # (ii)), not withdrawn; an infeasibility verdict still raises.
                bound_unsolved=True,
            )
        except (MeatError, ValueError, ArithmeticError) as failure:
            points.append(
                ReferencePoint(
                    iteration=candidate.gate.iteration,
                    roles=roles,
                    bracket_snapped=candidate.bracket,
                    bracket_reference=None,
                    objective_reference=None,
                    withdrawal_reference=_reason(failure),
                )
            )
            evaluations.append(
                EvaluatedPoint(PointSet.SEARCH, sequence, candidate, None)
            )
            continue
        evaluations.append(
            EvaluatedPoint(PointSet.SEARCH, sequence, candidate, assessment)
        )
        points.append(
            ReferencePoint(
                iteration=candidate.gate.iteration,
                roles=roles,
                bracket_snapped=candidate.bracket,
                bracket_reference=assessment.bracket,
                objective_reference=assessment.objective,
                withdrawal_reference=assessment.gate.withdrawal,
                feasible_side_reference=feasible_side_record(assessment.gate),
            )
        )
    # THE POLISH (item (i)'s second set), from the first set's point with the
    # largest bracket on D: the first of the candidates, best first.
    polish = polish_on_reference(
        reference_maps,
        oracle,
        acceptance,
        alpha,
        exact,
        candidates[0] if candidates else None,
        start_index=0 if candidates else None,
        budget_seconds=polish_budget_seconds,
        skip_key_inert=skip_key_inert,
    )
    offset = max((sequence for _, _, sequence in candidates), default=0)
    for kept in polish.kept:
        assessment = kept.assessment
        evaluations.append(
            EvaluatedPoint(
                PointSet.POLISH, offset + kept.sequence, assessment, assessment
            )
        )
        points.append(
            ReferencePoint(
                iteration=assessment.gate.iteration,
                roles=kept.roles,
                bracket_snapped=None,
                bracket_reference=assessment.bracket,
                objective_reference=assessment.objective,
                withdrawal_reference=assessment.gate.withdrawal,
                feasible_side_reference=feasible_side_record(assessment.gate),
                point_set=PointSet.POLISH,
            )
        )
    brackets = [
        point.bracket_reference
        for point in points
        if point.bracket_reference is not None
        and not math.isnan(point.bracket_reference)
    ]
    seconds = time.perf_counter() - started
    if not brackets:
        return ReferenceBracket(
            ReferenceStatus.WITHDRAWN,
            REFERENCE_BRACKET_WITHDRAWN,
            None,
            tuple(points),
            detail=(
                "no evaluated point contributed on the reference companion; the "
                "run's first-order number is the bound on the searched declaration"
            ),
            seconds=seconds,
            polish=polish.record,
        )
    return ReferenceBracket(
        ReferenceStatus.COUNTED,
        None,
        max(brackets),
        tuple(points),
        seconds=seconds,
        maps=reference_maps,
        evaluations=tuple(evaluations),
        polish=polish.record,
    )


def reference_record(
    bracket: ReferenceBracket | None,
    admission: Mapping[str, Any] | None,
    *,
    snapped_bound: float | None,
    snapped_key_length: int | None,
) -> dict[str, Any] | None:
    """Return the key-rate record's ``reference_bracket`` (item (vi); the output row).

    ``snapped`` holds the bound on the searched declaration ``h_lb[D]`` and
    the key length it would give at the run's parameters, a diagnostic from
    which no key length is reported; ``difference`` is
    ``h_lb[D^ref] - h_lb[D]`` with its sign. ``admission`` is the companion's
    admission record, its measurements among it (``req:companion-admission``
    (iii)). ``polish`` is the polish's record (null where nothing was
    evaluated on the companion).
    """
    if bracket is None and admission is None:
        return None
    reference = None if bracket is None else bracket.h_lb_reference
    return {
        **({} if bracket is None else bracket.as_record()),
        **(
            {}
            if bracket is not None
            else {
                "status": str(ReferenceStatus.NOT_EVALUATED),
                "reason": None if admission is None else admission.get("reason"),
                "cause": None,
                "h_lb_reference": None,
                "points": [],
                "polish": None,
            }
        ),
        "counted": bracket is not None and bracket.counted,
        "snapped": {"h_lb": snapped_bound, "key_length": snapped_key_length},
        "difference": (
            None
            if reference is None or snapped_bound is None
            else reference - snapped_bound
        ),
        "admission": None if admission is None else dict(admission),
    }
