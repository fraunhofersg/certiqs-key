"""The outer alpha search: the Renyi order chosen from the honest model, before the run.

``meat-core`` is a function of one alpha and states no search: Eq.
``eq:keylength`` holds at every alpha of the profile domain, and choosing one
is a caller's business (:mod:`certiqs_key.runs.pipeline`, "WHAT IS NOT HERE").
``meat-core/design.md`` names this module's place: "``cor:keylength-bound`` (a)
with ``prop:monotone`` is what a search over alpha in the profile domain reads.
The search is the run tier's", and ``spec/architecture.md`` §6 draws it
between the configuration and the run.

WHY A SEARCH IS SOUND HERE
==========================
Every evaluation is an ordinary run at a fixed alpha, and every key length it
reports is that run's own, by ``cor:keylength-bound`` (a) at that alpha. The
search reads the HONEST MODEL only: the same configuration at different alpha,
with no observed data, so the chosen alpha is fixed before the protocol's first
round, which is when A-FIXED (``meat-core/ass:fixed``) fixes the output length.
Choosing alpha from a run's OBSERVED statistics would make the length
data-dependent, a variable-length protocol, and is not what this module does.

WHAT IT RANKS
=============
The engine's key length, where positive. Where every point clamps to zero the
key length cannot rank them, so the search ranks the unclamped right-hand side
of ``eq:keylength-h`` at ``h = h_lb`` (:func:`unclamped_length`). That number is
used to compare candidates and for nothing else: no key length is ever taken
from it, and the chosen point's key length is the engine's.

HOW IT SEARCHES
===============
The key length need not be unimodal in alpha once h_lb's own alpha-dependence
is counted, so the search first evaluates a coarse grid, log-spaced in
``alpha - 1``. It then runs a golden-section refinement in ``log(alpha - 1)``
on the bracket around the best grid point. Every evaluation is kept, refused
ones included, and the result records them all, so a reader sees what was
tried and not just what won.

AN EVALUATION WHOSE SOLVE RAISED. An alpha whose run stopped on a linear
oracle left unsolved (an :class:`~certiqs_key.solvers.oracles.protocol.OracleFailure`
whose ``unsolved`` holds: a status neither optimal nor an infeasibility
verdict) is recorded as refused, reason ``solve: oracle_failure``
(:attr:`~certiqs_key.runs.errors.RunRefusalReason.ORACLE_FAILURE`), and the
search goes on with its other alphas. The search's lowest grid points are its
worst-conditioned ones and the least likely to give a key, so one failure
there does not decide the point. An infeasibility verdict says the
declaration is empty at every alpha and still stops the search, as does every
other exception.

AN EVALUATION WHOSE BRACKET STAYED WIDE. A solve can end with a valid but
wide bracket: its key length is certified, only far below what the alpha
could give. The search must not read that as the alpha's value. At cutoff 3
of the BBM92 study the solves at alpha - 1 = 2.7e-3 and 7.0e-3 stopped with
h_lb -0.031 and -0.051 against h_low 0.024 (gaps of 2 and 3 times the value,
where the converged evaluations around them had relative gaps of 3e-4 and
less); taking both as real values would move the golden-section step away
from the alpha its neighbours chose and keep a worse one.

So every evaluation that returned a key length is read with its bracket: its
relative gap ``(h_low - h_lb) / |h_low|``, BOTH SIDES ON THE DECLARATION THE
SOLVE SEARCHED. On the direct route a run's reported ``h_lb`` can be the
bound evaluated again on the receiver's reference declaration
(``reference_bracket``, where counted), while ``h_low`` is the solve's
objective on the snapped copy; their difference would add the snap offset
(1e-5 to 5e-5 absolute on the licensed probes, 4e-4 to 2e-3 relative to
``h_low``, the size of the floor below) to the convergence gap. So the gap
reads the snapped run's own bound, ``reference_bracket.snapped.h_lb`` where
the reference bound is counted and ``h_lb`` otherwise
(``AlphaPoint.h_lb_searched``); where the reference bound is counted but the
searched declaration has no bound of its own, no gap is judged and the
evaluation is not set aside. The score, and so the
choice, still read the reported ``h_lb`` and key length. It is SET ASIDE when
that gap exceeds both

- a floor, :data:`WIDE_RELATIVE_GAP` (1e-3), or the run's own gap target
  relative to its ``h_low`` where the configuration sets one and it is the
  larger: a bracket 1e-3 open can hide about 0.1 % of ``n h``,
  already the size of the key differences the refinement resolves between
  neighbouring alphas, so below it no bracket is too wide to rank by; and a
  solve asked only to close its gap to the target cannot be called wide for
  stopping there; and
- :data:`WIDE_FACTOR` (10) times the median relative gap of the search's
  OTHER evaluations, so that an evaluation is wide against the solves of the
  same point, not against a fixed scale: where every solve of a point is
  equally open (a hard declaration at its budget), none is set aside and
  the search runs as before.

The coarse grid is judged once it is complete, each grid point against the
other five; a refinement evaluation against every evaluation made before it,
since it must be judged before the next step. The median of the others makes
the rule robust to a minority of wide evaluations, which is the case it is
for. Each gap is relative to its own ``h_low`` and not to the largest in the
search: the recorded ``relative_gap`` is then the judged quantity, an
evaluation's verdict does not move with which others happened to run, and
across the alphas the refinement compares (one coarse step either side of
the best) ``h_low`` varies by a few per cent, so the two normalisations
agree where the rule acts.

A SET-ASIDE EVALUATION IS ONLY A LOWER BOUND, AND IS READ AS ONE. Its
certified score is still a valid lower bound on what its alpha gives; what is unreliable
is how far below the truth it is. So it is valid evidence in every comparison it WINS
and unreliable only in one it loses:

- the coarse point with the best certified score centres the refinement,
  set aside or not, since the truth there is at least that good;
- in a golden-section comparison a set-aside point takes part when its score
  is at or above the value it is compared with; where it would lose, the
  comparison cannot be made on its value, and the refinement stops there
  (``refinement_stopped`` says at which alpha) rather than move away from
  an alpha whose true value is unknown -- the defect this guards against.

Its key length, certified whatever its bracket, stays eligible for the
choice: choosing alpha is a heuristic, and the reported key length is always
the chosen run's own. The record names every set-aside evaluation and why
(``set_aside``), with its ``h_low`` and ``relative_gap``. A retry was not
chosen: an evaluation reruns the same configuration, and the same solve
would end the same way.

NO ALPHA GIVES A KEY. Where some evaluation formed a bound and none reported
a positive key length, the search chooses no alpha: ranking key lengths of
zero by the unclamped surrogate ranks the bound's own offsets, which on the
direct route grow with ``alpha/(alpha-1)``, so the upper end of the grid won
and the run reported the estimate ``h_low`` of the alpha least suited to it.
The result carries ``no_positive_key`` instead: the evaluation with the
largest ``h_low`` (a tie going to the one evaluated first; where no
evaluation has a finite ``h_low``, the highest score, as before) is the run
the search returns, so its record's estimate is the best one the search saw
and its key length the 0 every evaluation reported; the largest ``h_lb`` the
search saw is recorded beside it as a diagnostic, and with it, where the
reported bound is the reference companion's, the largest bound on the
declaration the solve searched, which says where the key was lost; and a
sentence says why the key is 0 (:func:`_no_key_reason`). The child's status
is ``no_positive_key`` and ``chosen_alpha`` null (record schema 0.40.0). A
search in which some evaluation gives a positive key length chooses exactly
as before. The refinement still runs, since it may find a positive key.

A PROVED CONTRADICTION REFUSES THE RUN. An evaluation refused by the run tier's
plausibility check, ``solve: entropy_bound_above_key_ceiling``, is not one bad alpha
among good ones. Its bound above the ceiling proves ``D_min > 0``: no feasible state of
the declaration reproduces any accepted statistic, a fact about the
declaration and the acceptance set that does not depend on alpha
(:mod:`certiqs_key.runs.plausibility`, "A BOUND ABOVE THE CEILING PROVES A
CONTRADICTION"). At every other alpha the bound is the same declared model's,
inflated by ``alpha/(alpha-1) D_min``; scoring the refusal ``-inf`` and
choosing the best evaluation that passed is how the reproduction ended
``done`` with a key six times too large. So the search STOPS at the first
such evaluation: no other alpha can change the verdict. The result carries
that evaluation as ``contradiction`` and chooses none, every evaluation made
up to it is kept, and :func:`run_searched` returns that evaluation's own
refusal, its detail saying that the search refused the run as a whole at
that alpha. The proof wins over a set-aside: a set-aside reads a wide
bracket, the proof a bound above the ceiling, and a search that stops on the
coarse grid judges no bracket at all. Every other refusal of an evaluation
still scores ``-inf`` and the search goes on, and a run at one alpha refuses
at its own alpha, as before.

THE STATISTICS CHECK, ONCE FOR THE SEARCH. A run whose honest statistics are
supplied or whose declaration carries a constraint entry the caller declared
is checked against the feasible statistics
(``meat-core/req:unreachable-acceptance-set``;
:mod:`certiqs_key.runs.statistics_check`). The search holds one check for all
its evaluations (:func:`~certiqs_key.runs.statistics_check.searched_run`):
the penalty-only program is solved once, at ``alpha_0`` (:func:`alpha_zero`:
the lowest order the search evaluates, the first point of its coarse grid as
evaluated, which the search fixes before it evaluates any, or the lower end
of the declared domain where that is lower; :func:`alpha_zero_rule` records
which), which no evaluated alpha is below, before the first evaluation's own
solve, and the cap on the pass probability of devices as declared is decided
with it. The cap is one number per run, so where it refuses (item (iv)) the
evaluation that formed it is refused before its own solve,
``solve: acceptance_set_unreachable``, the search STOPS there, chooses no
alpha, and the run is refused as a whole with that evaluation's refusal, the
alpha child's status ``acceptance_set_unreachable``. Every evaluation records
the check's diagnostic at its own alpha; the run's whole check is the
returned outcome's ``statistics_consistency``.

HOW IT IS WIRED
===============
Opt in, per configuration (the declared alpha stays the default).
:attr:`RunConfig.alpha_search <certiqs_key.runs.config.RunConfig.alpha_search>`
holds an :class:`~certiqs_key.runs.config.AlphaSearchSettings`, written into
the configuration's payload only where set, and a configuration that also
fixes ``alpha`` is refused (``alpha_and_alpha_search_both_set``).

Every instance's runner is built by :func:`searching_runner`, which takes the
instance's one-alpha run and the bundle directory. A configuration without
the search runs once, in ``run-NNNN/``, exactly as before. One with it runs
:func:`run_searched`: :func:`search_alpha` drives the instance's one-alpha
run at each candidate (the same configuration with ``alpha`` fixed and the
search removed), each in its own sub-directory ``run-NNNN/alpha-KK/``, and
the chosen run's own outcome is returned with the search attached
(:func:`attach_alpha_search`): on the outcome's ``alpha_search`` field, and in
the record through the solve stage's ``alpha`` child, which then says
``searched: true`` and carries :meth:`AlphaSearchResult.as_payload` -- the
settings, every evaluation with its alpha, key length, h_lb, score, reason,
seconds, h_low, relative gap and set-aside reason, the set-aside rule, why
the refinement stopped early if it did, and the chosen alpha (record schema
0.34.0), the alpha that proved a contradiction with its rule (0.35.0), and
the no-positive-key outcome with its rule (0.40.0).
Where an evaluation proved a contradiction, its own refusal is returned with
the search attached, ``chosen_alpha`` null and the child's status
``contradiction``. Where every evaluation refused, the first
evaluation's outcome is returned, refusal and all, with the search attached
and ``chosen_alpha`` null -- the first evaluation that returned one; where
every evaluation raised, the first one's failure is raised again, as an
unsearched run raises it. :func:`~certiqs_key.runs.pipeline.run_slice` itself
still runs one alpha.

WHAT IS NOT HERE. Warm starts between alpha values, and reuse of the
alpha-independent preparation across evaluations. Both are run cost, not
soundness; every evaluation reruns its point from scratch, preparation
included, which keeps each one an ordinary run.
"""

from __future__ import annotations

import math
import statistics
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from itertools import count
from pathlib import Path
from typing import Any

from certiqs_key.meat_core.finitekey.consistency import Alpha0Rule
from certiqs_key.runs.config import AlphaSearchError, AlphaSearchSettings, RunConfig
from certiqs_key.runs.errors import RunRefusalReason
from certiqs_key.runs.flow import StageChild
from certiqs_key.runs.pipeline import SliceOutcome, SliceRefusal
from certiqs_key.runs.record import RunRecord, record_run
from certiqs_key.runs.stages import SliceStage
from certiqs_key.runs.statistics_check import (
    UNREACHABLE_REASON,
    RunCheck,
    run_check,
    searched_run,
)
from certiqs_key.runs.surface import InstanceIdentity, Runner
from certiqs_key.solvers.oracles.protocol import OracleFailure

__all__ = [
    "CONTRADICTION_REASON",
    "CONTRADICTION_RULE",
    "NO_POSITIVE_KEY_RULE",
    "UNREACHABLE_EVALUATION_REASON",
    "AlphaEvaluation",
    "AlphaPoint",
    "AlphaSearchError",
    "AlphaSearchResult",
    "AlphaSearchSettings",
    "alpha_zero",
    "alpha_zero_rule",
    "attach_alpha_search",
    "point_from_outcome",
    "point_from_record",
    "run_searched",
    "run_tier_evaluator",
    "search_alpha",
    "searching_runner",
    "unclamped_length",
]

#: The golden ratio's conjugate, ``(sqrt(5) - 1) / 2``.
_INVERSE_PHI = (math.sqrt(5.0) - 1.0) / 2.0

#: The relative gap ``(h_low - h_lb) / |h_low|`` at or below which no
#: evaluation is set aside, raised to the run's gap target over ``|h_low|``
#: where that is larger (module docstring, "AN EVALUATION WHOSE BRACKET
#: STAYED WIDE").
WIDE_RELATIVE_GAP = 1e-3
#: How many times the median relative gap of the search's other evaluations
#: an evaluation's own must exceed to be set aside (the same section).
WIDE_FACTOR = 10.0
#: The rule as the record states it.
SET_ASIDE_RULE = (
    "an evaluation with a key length is set aside when its relative gap "
    "(h_low - h_lb)/|h_low| on the declaration the solve searched (h_lb there "
    "being the run's reference_bracket.snapped.h_lb where the reference bound "
    f"is counted) exceeds {WIDE_RELATIVE_GAP:g} (or the run's gap "
    f"target over |h_low|, where larger) and {WIDE_FACTOR:g} "
    "times the median relative gap of the search's other evaluations (the "
    "coarse grid judged when complete, a refinement evaluation against those "
    "before it); its certified score is a lower bound, so it centres the "
    "refinement where it is the best coarse score and takes part in a "
    "golden-section comparison it wins or ties, and a comparison it would "
    "lose stops the refinement; its key length stays eligible for the choice"
)
#: The reason, as an evaluation records it, of an evaluation whose bound the
#: plausibility check found above the ceiling: a proved contradiction (module
#: docstring, "A PROVED CONTRADICTION REFUSES THE RUN").
CONTRADICTION_REASON = (
    f"{SliceStage.SOLVE}: {RunRefusalReason.ENTROPY_BOUND_ABOVE_KEY_CEILING}"
)
#: The reason, as an evaluation records it, of the evaluation refused by
#: ``meat-core/req:unreachable-acceptance-set`` (iv), at which the search stops
#: (module docstring, "THE STATISTICS CHECK, ONCE FOR THE SEARCH").
UNREACHABLE_EVALUATION_REASON = f"{SliceStage.SOLVE}: {UNREACHABLE_REASON}"
#: The rule as the record states it.
CONTRADICTION_RULE = (
    "an evaluation refused with entropy_bound_above_key_ceiling proves that no "
    "feasible state of the declaration reproduces any accepted statistic "
    "(D_min > 0, meat-core/prop:value-range (i)-(ii)), which does not depend on "
    "alpha; the search stops there and the run refuses as a whole, with that "
    "evaluation's refusal and every evaluation made up to it"
)
#: The rule as the record states it (module docstring, "NO ALPHA GIVES A KEY").
NO_POSITIVE_KEY_RULE = (
    "where some evaluation formed a bound and none reported a positive key "
    "length, no alpha is chosen: the run reported is the evaluation with the "
    "largest h_low (a tie to the first evaluated; with no finite h_low, the "
    "highest score), and the largest h_lb the search saw, with the largest "
    "bound on the declaration the solve searched where the reported h_lb is "
    "the reference companion's, is recorded as a diagnostic beside why the "
    "key is 0"
)


@dataclass(frozen=True)
class AlphaPoint:
    """What one evaluation at a fixed alpha returned.

    ``score`` is what the search ranks (module docstring, "WHAT IT RANKS"):
    ``-inf`` on a refused run, so a refusal never wins.
    """

    score: float
    key_length: int | None
    h_lb: float | None = None
    #: The run's key-length reason code, or the refusal's reason.
    reason: str | None = None
    #: The run's ``h_low``, the estimate side of its bracket, where it has one.
    h_low: float | None = None
    #: Why :func:`search_alpha` set this evaluation aside (its bracket stayed
    #: wide), or ``None``. Set by the search, never by an evaluator.
    set_aside: str | None = None
    #: The bound on the declaration the solve searched, where the reported
    #: ``h_lb`` is the reference companion's (``reference_bracket.snapped``);
    #: ``None`` where ``h_lb`` is that bound itself, NaN where the reference
    #: bound is counted but the searched declaration has none (then no gap
    #: is judged). The relative gap reads it (module docstring). Not
    #: serialised: the run's record carries it.
    h_lb_searched: float | None = None
    #: The gap target the run's configuration set (``solver.advanced.gap_tolerance``),
    #: or ``None``; it raises the set-aside floor. Not serialised: the
    #: configuration carries it.
    gap_target: float | None = None
    #: The run itself, for a caller that keeps the chosen point's record. Not
    #: serialised.
    run: Any = field(default=None, compare=False, repr=False)
    #: The unsolved oracle failure this evaluation raised, kept on the FIRST
    #: evaluation that raised one only (module docstring, "AN EVALUATION WHOSE
    #: SOLVE RAISED"): its traceback holds that whole solve, so a search keeps
    #: one, as :func:`run_searched` holds one first outcome. Not serialised; its
    #: code is ``reason``.
    failure: OracleFailure | None = field(default=None, compare=False, repr=False)
    #: Whether a refusal carries a plausibility check that was exceeded (module
    #: docstring, "A PROVED CONTRADICTION REFUSES THE RUN"). Not serialised:
    #: the run's record carries the check on its refused stage.
    exceeded: bool = False

    @property
    def refused(self) -> bool:
        """Whether the run behind this point refused."""
        return self.key_length is None

    @property
    def proves_contradiction(self) -> bool:
        """Whether the plausibility check refused it, or was exceeded at it.

        A proved contradiction either way: the check's verdict is the same
        whether it refused the run or the statistics check refused it first.
        """
        return self.reason == CONTRADICTION_REASON or (
            self.refused and self.exceeded
        )

    @property
    def relative_gap(self) -> float | None:
        """``(h_low - h_lb) / |h_low|`` on the searched declaration, or ``None``.

        ``h_lb`` here is :attr:`h_lb_searched` where the run reports the
        reference companion's bound, so that both sides are the same
        declaration's (module docstring, "AN EVALUATION WHOSE BRACKET STAYED
        WIDE"). Read only by the set-aside rule; a refused run, or one whose
        numbers are not finite, has none.
        """
        bound = self.h_lb if self.h_lb_searched is None else self.h_lb_searched
        if self.refused or bound is None or self.h_low is None:
            return None
        if not (math.isfinite(bound) and math.isfinite(self.h_low)):
            return None
        if self.h_low == 0:
            return None
        return max(0.0, self.h_low - bound) / abs(self.h_low)


@dataclass(frozen=True)
class AlphaEvaluation:
    """One evaluated alpha, in the order the search evaluated it."""

    alpha: float
    #: ``"coarse"`` or ``"refine"``.
    phase: str
    point: AlphaPoint
    seconds: float

    def as_payload(self) -> dict[str, Any]:
        """Return the evaluation as JSON (the run itself is not included)."""
        score = self.point.score
        h_low = self.point.h_low
        return {
            "alpha": self.alpha,
            "phase": self.phase,
            "key_length": self.point.key_length,
            "h_lb": self.point.h_lb,
            "score": score if math.isfinite(score) else None,
            "reason": self.point.reason,
            "seconds": self.seconds,
            # An infinite h_low (an empty acceptance set) is no JSON number.
            "h_low": h_low if h_low is not None and math.isfinite(h_low) else None,
            "relative_gap": self.point.relative_gap,
            "set_aside": self.point.set_aside,
        }


@dataclass(frozen=True)
class AlphaSearchResult:
    """Every evaluation, and the one chosen."""

    settings: AlphaSearchSettings
    evaluations: tuple[AlphaEvaluation, ...]
    #: The best-scoring evaluation, or ``None`` when every one refused, one
    #: proved a contradiction, or none gave a positive key length.
    chosen: AlphaEvaluation | None
    #: Why the refinement stopped before its steps were spent (a set-aside
    #: evaluation), or ``None``.
    refinement_stopped: str | None = None
    #: The evaluation that proved a contradiction, the last one made, or
    #: ``None`` (module docstring, "A PROVED CONTRADICTION REFUSES THE RUN").
    contradiction: AlphaEvaluation | None = None
    #: The evaluation the run reports where no alpha gives a positive key
    #: length, the one with the largest ``h_low``, or ``None`` (module
    #: docstring, "NO ALPHA GIVES A KEY").
    no_positive_key: AlphaEvaluation | None = None

    def __post_init__(self) -> None:
        """Reject a choice beside a proved contradiction or a no-key outcome."""
        if self.contradiction is not None and self.chosen is not None:
            raise ValueError("a search that proved a contradiction chooses no alpha")
        if self.no_positive_key is not None and (
            self.chosen is not None or self.contradiction is not None
        ):
            raise ValueError(
                "a search with no positive key length chooses no alpha and "
                "proved no contradiction"
            )

    def no_key_payload(self) -> dict[str, Any] | None:
        """Return the no-positive-key outcome as the record carries it, or ``None``."""
        reported = self.no_positive_key
        if reported is None:
            return None
        finite = [e for e in self.evaluations if math.isfinite(e.point.score)]
        bound = _largest(finite, lambda e: e.point.h_lb)
        searched = _largest(finite, lambda e: e.point.h_lb_searched)
        return {
            "reported_alpha": reported.alpha,
            "h_low": _finite_or_none(reported.point.h_low),
            "largest_h_lb": (
                None
                if bound is None
                else {"alpha": bound.alpha, "h_lb": bound.point.h_lb}
            ),
            "largest_h_lb_searched": (
                None
                if searched is None
                else {"alpha": searched.alpha, "h_lb": searched.point.h_lb_searched}
            ),
            "reason": _no_key_reason(self),
        }

    @property
    def alpha(self) -> float | None:
        """The chosen alpha, or ``None`` when none was chosen (``chosen``)."""
        return None if self.chosen is None else self.chosen.alpha

    def as_payload(self) -> dict[str, Any]:
        """Return the search as JSON, for a record's ``alpha`` stage."""
        return {
            "searched": True,
            "rule": (
                "coarse log grid in alpha - 1, then golden-section in log(alpha - 1)"
            ),
            "reads": "the honest model at fixed configuration; no observed data",
            "settings": self.settings.as_payload(),
            "chosen_alpha": self.alpha,
            "evaluations": [e.as_payload() for e in self.evaluations],
            "set_aside_rule": SET_ASIDE_RULE,
            "refinement_stopped": self.refinement_stopped,
            "contradiction_alpha": (
                None if self.contradiction is None else self.contradiction.alpha
            ),
            "contradiction_rule": CONTRADICTION_RULE,
            "no_positive_key": self.no_key_payload(),
            "no_positive_key_rule": NO_POSITIVE_KEY_RULE,
        }


Evaluator = Callable[[float], AlphaPoint]


def search_alpha(
    evaluate: Evaluator, settings: AlphaSearchSettings | None = None
) -> AlphaSearchResult:
    """Search alpha with ``evaluate`` and return every evaluation and the best.

    ``evaluate`` runs one point at the given alpha. It is called once per
    distinct alpha: a repeated alpha is served from the evaluations already
    made. The best point is the highest score; a tie goes to the point
    evaluated first. An evaluation that raises an unsolved
    :class:`~certiqs_key.solvers.oracles.protocol.OracleFailure` is a refused
    point with reason ``solve: oracle_failure``, the failure kept on the first
    such point only; any other exception propagates. An evaluation whose
    bracket stayed wide is set aside and read as the lower bound it is
    (module docstring, "AN EVALUATION WHOSE BRACKET STAYED WIDE"). The search
    stops at the first evaluation that proves a contradiction, and chooses
    none (module docstring, "A PROVED CONTRADICTION REFUSES THE RUN"), and at
    the evaluation the statistics check refuses, choosing none ("THE
    STATISTICS CHECK, ONCE FOR THE SEARCH").
    """
    settings = settings or AlphaSearchSettings()
    evaluations: list[AlphaEvaluation] = []
    seen: dict[float, int] = {}
    kept_failure = False

    def at(alpha: float, phase: str, *, judge: bool) -> AlphaEvaluation:
        nonlocal kept_failure
        key = float(f"{alpha:.12g}")
        if key not in seen:
            started = time.perf_counter()
            try:
                point = evaluate(key)
            except OracleFailure as failure:
                if not failure.unsolved:
                    raise
                point = AlphaPoint(
                    score=-math.inf,
                    key_length=None,
                    reason=f"{SliceStage.SOLVE}: {RunRefusalReason.ORACLE_FAILURE}",
                    failure=None if kept_failure else failure,
                )
                kept_failure = True
            if judge:
                point = _judged(point, [e.point for e in evaluations])
            seen[key] = len(evaluations)
            evaluations.append(
                AlphaEvaluation(
                    alpha=key,
                    phase=phase,
                    point=point,
                    seconds=time.perf_counter() - started,
                )
            )
            if point.proves_contradiction:
                raise _ContradictionProvedError(evaluations[-1])
            if point.reason == UNREACHABLE_EVALUATION_REASON:
                raise _RunRefusedError(evaluations[-1])
        return evaluations[seen[key]]

    try:
        stopped = _explore(at, evaluations, settings)
    except _ContradictionProvedError as proved:
        return AlphaSearchResult(
            settings=settings,
            evaluations=tuple(evaluations),
            chosen=None,
            contradiction=proved.evaluation,
        )
    except _RunRefusedError:
        # The statistics check refused the run as a whole (module docstring,
        # "THE STATISTICS CHECK, ONCE FOR THE SEARCH"): no alpha is chosen.
        return AlphaSearchResult(
            settings=settings, evaluations=tuple(evaluations), chosen=None
        )
    finite = [e for e in evaluations if math.isfinite(e.point.score)]
    chosen = (
        max(finite, key=lambda e: (e.point.score, -evaluations.index(e)))
        if finite
        else None
    )
    if chosen is not None and not any(
        (e.point.key_length or 0) > 0 for e in evaluations
    ):
        # NO ALPHA GIVES A KEY (module docstring): none is chosen.
        return AlphaSearchResult(
            settings=settings,
            evaluations=tuple(evaluations),
            chosen=None,
            refinement_stopped=stopped,
            no_positive_key=_largest(finite, lambda e: e.point.h_low) or chosen,
        )
    return AlphaSearchResult(
        settings=settings,
        evaluations=tuple(evaluations),
        chosen=chosen,
        refinement_stopped=stopped,
    )


def _finite_or_none(value: float | None) -> float | None:
    """Return ``value`` where it is a finite number, else ``None``."""
    return value if value is not None and math.isfinite(value) else None


def _largest(
    evaluations: list[AlphaEvaluation],
    value: Callable[[AlphaEvaluation], float | None],
) -> AlphaEvaluation | None:
    """Return the evaluation with the largest finite ``value``, the first on a tie."""
    best: AlphaEvaluation | None = None
    best_value = -math.inf
    for evaluation in evaluations:
        found = _finite_or_none(value(evaluation))
        if found is not None and (best is None or found > best_value):
            best, best_value = evaluation, found
    return best


def _no_key_reason(result: AlphaSearchResult) -> str:
    """Return why the key is 0 where no alpha gives one, in one paragraph."""
    finite = [e for e in result.evaluations if math.isfinite(e.point.score)]
    best = max(finite, key=lambda e: (e.point.score, -result.evaluations.index(e)))
    text = (
        "No alpha the search evaluated gives a positive key length: each of "
        f"the {len(finite)} evaluations that formed a bound reported 0, n times "
        "the bound the key length is computed from not covering the deductions "
        "(error correction, the verification hash and privacy amplification)"
    )
    if best.point.score < 0:
        # The score reads the first-order h_lb; a certified run's length is
        # computed from h_cert, so the shortfall is the ranking's, not the
        # length's (module docstring, "WHAT IT RANKS").
        text += (
            f"; by the search's ranking, which reads the first-order h_lb, the "
            f"closest is alpha = {best.alpha!r}, where n h_lb falls "
            f"{-best.point.score:.4g} bits short"
        )
    text += "."
    bound = _largest(finite, lambda e: e.point.h_lb)
    searched = _largest(finite, lambda e: e.point.h_lb_searched)
    if (
        searched is not None
        and bound is not None
        and searched.point.h_lb_searched is not None
        and bound.point.h_lb is not None
        and searched.point.h_lb_searched > bound.point.h_lb
    ):
        text += (
            " On the declaration the solver searched the bound reaches "
            f"{searched.point.h_lb_searched:.4g} (alpha = {searched.alpha!r}); "
            "the reported bound is that bound formed again on the receiver's "
            "reference declaration (the reference companion), at most "
            f"{bound.point.h_lb:.4g} (alpha = {bound.alpha!r}), and the key is "
            "lost there."
        )
    return text


class _RunRefusedError(Exception):
    """Raised by the evaluation the statistics check refused: the search stops."""

    def __init__(self, evaluation: AlphaEvaluation) -> None:
        super().__init__(evaluation.alpha)
        self.evaluation = evaluation


class _ContradictionProvedError(Exception):
    """Raised by an evaluation that proved a contradiction: the search stops."""

    def __init__(self, evaluation: AlphaEvaluation) -> None:
        super().__init__(evaluation.alpha)
        self.evaluation = evaluation


def _explore(
    at: Callable[..., AlphaEvaluation],
    evaluations: list[AlphaEvaluation],
    settings: AlphaSearchSettings,
) -> str | None:
    """Run the coarse grid and the refinement through ``at``; why it stopped early.

    ``at(alpha, phase, judge=...)`` evaluates (or serves) one alpha and
    appends to ``evaluations``. Returns ``refinement_stopped`` (module
    docstring, "AN EVALUATION WHOSE BRACKET STAYED WIDE"), or ``None``.
    """
    grid = settings.coarse_grid()
    for alpha in grid:
        at(alpha, "coarse", judge=False)
    # The coarse grid is judged once complete, each point against the others.
    coarse = list(evaluations)
    for index, done in enumerate(coarse):
        others = [e.point for j, e in enumerate(coarse) if j != index]
        evaluations[index] = replace(done, point=_judged(done.point, others))
    # The best certified coarse score centres the refinement, set aside or
    # not: a set-aside score is a lower bound, so the truth there is at least
    # as good.
    scores = [e.point.score for e in evaluations[: len(grid)]]
    best = max(range(len(grid)), key=lambda i: (scores[i], -i))
    if not (math.isfinite(scores[best]) and settings.refine_steps > 0):
        return None
    ts = [math.log(alpha - 1.0) for alpha in grid]
    a = ts[max(best - 1, 0)]
    b = ts[min(best + 1, len(ts) - 1)]

    def value(t: float) -> tuple[float, bool]:
        done = at(1.0 + math.exp(t), "refine", judge=True)
        return done.point.score, done.point.set_aside is not None

    where = _golden(value, a, b, settings.refine_steps)
    if where is None:
        return None
    alpha = float(f"{1.0 + math.exp(where):.12g}")
    return (
        f"the evaluation at alpha {alpha!r} was set aside and would "
        "lose its golden-section comparison, so that step was not taken"
    )


def _judged(point: AlphaPoint, others: list[AlphaPoint]) -> AlphaPoint:
    """Return ``point`` with ``set_aside`` set where its bracket stayed wide.

    ``others`` are the evaluations it is judged against (module docstring,
    "AN EVALUATION WHOSE BRACKET STAYED WIDE"). With no other evaluation that
    has a relative gap there is nothing to be wide against, and nothing is
    set aside.
    """
    gap = point.relative_gap
    floor = WIDE_RELATIVE_GAP
    # The solve measures its gap target on an assessment's raw gap (that
    # point's objective minus its own bracket); here it is applied to the
    # run's h_low - h_lb, the best estimate against the best bracket, which
    # can come from different points. So the target is the scale below which
    # the solve was not asked to close, not an exact stopping rule.
    if (
        point.gap_target is not None
        and point.h_low is not None
        and math.isfinite(point.h_low)
        and point.h_low != 0
    ):
        floor = max(floor, point.gap_target / abs(point.h_low))
    if gap is None or gap <= floor:
        return point
    gaps = [g for g in (other.relative_gap for other in others) if g is not None]
    if not gaps:
        return point
    reference = statistics.median(gaps)
    if gap <= WIDE_FACTOR * reference:
        return point
    return replace(
        point,
        set_aside=(
            f"wide_bracket: relative gap {gap:.3g} exceeds the floor {floor:.3g} "
            f"and {WIDE_FACTOR:g} times the median {reference:.3g} of the "
            f"{len(gaps)} other evaluations"
        ),
    )


def _golden(
    f: Callable[[float], tuple[float, bool]], a: float, b: float, steps: int
) -> float | None:
    """Spend at most ``steps`` evaluations of ``f`` maximising it on ``[a, b]``.

    ``f`` returns a point's score and whether it was set aside. A set-aside
    score is a lower bound: it takes part in a comparison it wins or ties,
    and where it would lose the search stops and returns that point (module
    docstring, "AN EVALUATION WHOSE BRACKET STAYED WIDE"); ``None`` when every
    step was taken.
    """
    c = b - _INVERSE_PHI * (b - a)
    d = a + _INVERSE_PHI * (b - a)
    fc, wide_c = f(c)
    used = 1
    if used >= steps:
        return None
    fd, wide_d = f(d)
    used += 1
    while used < steps:
        if fc >= fd:
            if wide_d and fd < fc:
                return d
            b, d, fd, wide_d = d, c, fc, wide_c
            c = b - _INVERSE_PHI * (b - a)
            fc, wide_c = f(c)
        else:
            if wide_c:
                return c
            a, c, fc, wide_c = c, d, fd, wide_d
            d = a + _INVERSE_PHI * (b - a)
            fd, wide_d = f(d)
        used += 1
    return None


def unclamped_length(
    *,
    rounds: int,
    h_lb: float,
    alpha: float,
    eps_pa: float,
    eps_ev: float,
    lambda_ec: int,
) -> float:
    """Return the right-hand side of ``eq:keylength-h`` at ``h = h_lb``, unclamped.

    ``n h - lambda_EC - ceil(log2 1/eps_EV) - alpha/(alpha-1) log2 1/eps_PA + 1``,
    with ``h_lb`` in place of ``max{0, h}`` so that a negative bracket still
    ranks. A RANKING SURROGATE ONLY (module docstring): no key length is taken
    from it.
    """
    return (
        rounds * h_lb
        - lambda_ec
        - math.ceil(math.log2(1.0 / eps_ev))
        - alpha / (alpha - 1.0) * math.log2(1.0 / eps_pa)
        + 1.0
    )


def run_tier_evaluator(
    config: RunConfig,
    runner: Callable[[RunConfig, int], SliceOutcome],
    *,
    created_by: str,
    instance: InstanceIdentity | None = None,
) -> Evaluator:
    """Return an evaluator that runs ``config`` at each alpha through ``runner``.

    ``runner`` is an instance's ``surface.runner(...)``. Each evaluation gets
    its own run index, so each writes its own bundle directory. The point's
    ``run`` is the :class:`~certiqs_key.runs.record.RunRecord`.
    """
    counter = iter(range(1 << 30))

    def evaluate(alpha: float) -> AlphaPoint:
        point_config = config.with_(alpha=alpha)
        outcome = runner(point_config, next(counter))
        record = record_run(
            outcome, point_config, created_by=created_by, instance=instance
        )
        return point_from_record(record, point_config)

    return evaluate


def point_from_record(record: RunRecord, config: RunConfig) -> AlphaPoint:
    """Read one run record as an :class:`AlphaPoint`."""
    payload = record.as_dict()
    payload = payload.get("payload", payload)
    stages: Mapping[str, Any] = payload.get("stages", {}) or {}
    key_rate = stages.get("key_rate") or {}
    if not key_rate:
        return AlphaPoint(
            score=-math.inf,
            key_length=None,
            reason=_refusal_reason(stages),
            exceeded=any(
                _exceeded(stage.get("plausibility"))
                for stage in stages.values()
                if isinstance(stage, Mapping) and stage.get("refused")
            ),
            run=record,
        )
    return _point(key_rate, config, run=record)


def point_from_outcome(outcome: SliceOutcome, config: RunConfig) -> AlphaPoint:
    """Read one run's outcome as an :class:`AlphaPoint`, with no record built.

    The same reading as :func:`point_from_record`, of the same fields: a
    refusal is ``"<stage>: <reason>"``, which is how the record names it, and
    a completed run is read off its key-rate result. The point's ``run`` is
    left empty; :func:`run_searched` keeps the outcomes it needs itself.
    """
    if isinstance(outcome, SliceRefusal):
        return AlphaPoint(
            score=-math.inf,
            key_length=None,
            reason=f"{outcome.stage}: {outcome.reason}",
            exceeded=_exceeded(outcome.plausibility),
        )
    rate = outcome.key_rate
    return _point(
        {
            "key_length": rate.key_length,
            "h_lb": rate.h_lb,
            "h_low": rate.h_low,
            "reference_bracket": rate.reference_bracket,
            "rounds": rate.rounds,
            "alpha": rate.alpha,
            "key_length_reason_code": rate.key_length_reason_code,
        },
        config,
        run=None,
    )


def _point(key_rate: Mapping[str, Any], config: RunConfig, *, run: Any) -> AlphaPoint:
    """Score one key-rate result (module docstring, "WHAT IT RANKS")."""
    reason = key_rate.get("key_length_reason_code")
    if key_rate.get("key_length") is None:
        return AlphaPoint(score=-math.inf, key_length=None, reason=reason, run=run)
    key_length = int(key_rate["key_length"])
    h_lb = key_rate.get("h_lb")
    h_low = key_rate.get("h_low")
    h_lb_searched = _searched_bound(key_rate.get("reference_bracket"))
    if key_length > 0:
        score = float(key_length)
    elif h_lb is None:
        score = -math.inf
    else:
        params = config.parameters
        score = min(
            0.0,
            unclamped_length(
                rounds=int(key_rate.get("rounds", config.rounds)),
                h_lb=float(h_lb),
                alpha=float(key_rate.get("alpha", config.alpha or params.alpha)),
                eps_pa=params.eps_pa,
                eps_ev=params.eps_ev,
                lambda_ec=params.lambda_ec,
            ),
        )
    return AlphaPoint(
        score=score,
        key_length=key_length,
        h_lb=None if h_lb is None else float(h_lb),
        reason=reason,
        h_low=None if h_low is None else float(h_low),
        h_lb_searched=h_lb_searched,
        gap_target=(
            None
            if config.solver is None or config.solver.advanced is None
            else config.solver.advanced.gap_tolerance
        ),
        run=run,
    )


def _searched_bound(reference: Mapping[str, Any] | None) -> float | None:
    """Return the bound on the searched declaration where ``h_lb`` is not it.

    Where the reference companion's bound is counted, the reported ``h_lb``
    is that bound and ``snapped.h_lb`` the searched declaration's
    (``GeneralKeyRateResult.reference_bracket``); otherwise ``h_lb`` is
    already the searched declaration's and ``None`` is returned. A counted
    reference bound beside no snapped one (no iterate contributed on the
    searched declaration) returns NaN: that declaration has no bracket, so
    :attr:`AlphaPoint.relative_gap` is ``None`` rather than the mixed pair.
    """
    if not reference or reference.get("counted") is not True:
        return None
    snapped = reference.get("snapped") or {}
    value = snapped.get("h_lb")
    return math.nan if value is None else float(value)


def _exceeded(plausibility: Any) -> bool:
    """Whether a refusal carries a plausibility check that was exceeded."""
    return isinstance(plausibility, Mapping) and plausibility.get("exceeded") is True


def _refusal_reason(stages: Mapping[str, Any]) -> str:
    for name, stage in stages.items():
        if isinstance(stage, Mapping) and stage.get("refused"):
            return f"{name}: {stage.get('reason')}"
    return "no key-rate stage"


#: An instance's run at ONE alpha: a configuration and the bundle directory
#: that run writes, in; its outcome out. What :func:`searching_runner` wraps.
type OneAlphaRun = Callable[[RunConfig, Path], SliceOutcome]


def searching_runner(run_at: OneAlphaRun, directory: Path) -> Runner:
    """Return an instance's :data:`~certiqs_key.runs.surface.Runner`, search included.

    THE ONE PLACE EVERY INSTANCE GETS THE OUTER SEARCH. ``run_at`` is the
    instance's own wiring of :func:`~certiqs_key.runs.pipeline.run_slice` for
    one configuration at one alpha into one bundle directory. A configuration
    without :attr:`~certiqs_key.runs.config.RunConfig.alpha_search` runs once,
    into ``directory/run-NNNN``, as every runner did before the search; one
    with it runs :func:`run_searched`, each evaluation into
    ``directory/run-NNNN/alpha-KK``.
    """

    def run(config: RunConfig, index: int) -> SliceOutcome:
        bundle = directory / f"run-{index:04d}"
        if config.alpha_search is None:
            return run_at(config, bundle)
        return run_searched(
            config, lambda point, k: run_at(point, bundle / f"alpha-{k:02d}")
        )

    return run


def run_searched(
    config: RunConfig, run_one: Callable[[RunConfig, int], SliceOutcome]
) -> SliceOutcome:
    """Run ``config``'s alpha search and return the chosen run's outcome.

    ``run_one(point_config, k)`` runs the ``k``-th evaluation, ``point_config``
    being ``config`` with ``alpha`` fixed at the candidate and the search
    removed. The search is :func:`search_alpha` with ``config.alpha_search``;
    the outcome returned is the chosen evaluation's own, the refusal of the
    evaluation that proved a contradiction (module docstring, "A PROVED
    CONTRADICTION REFUSES THE RUN"), or the first returned outcome where every
    one refused, with the search attached (:func:`attach_alpha_search`).
    Where every evaluation raised an unsolved oracle failure there is no
    outcome at all, and the first failure is raised again.

    AT MOST FIVE OUTCOMES ARE HELD while the search runs: the first, for the
    all-refused case, the best so far, the one with the largest ``h_low`` so
    far, for the no-positive-key outcome (module docstring, "NO ALPHA GIVES A
    KEY"), the one the statistics check refused, and the one that proved a
    contradiction, after either of which the search stops. The best and the largest
    ``h_low`` are kept by :func:`search_alpha`'s own rules -- the highest
    score, and the largest finite ``h_low`` among evaluations with a finite
    score, a tie going to the point evaluated first -- so the outcome held is
    the one returned, and a disagreement is raised rather than papered over.
    """
    settings = config.alpha_search
    if settings is None:
        raise ValueError("run_searched needs a configuration with alpha_search")
    base = config.with_(alpha_search=None)
    held: dict[float, SliceOutcome] = {}
    first: list[float] = []
    best: list[tuple[float, float]] = []
    # The largest finite h_low among the evaluations that formed a bound, for
    # the no-positive-key outcome (module docstring, "NO ALPHA GIVES A KEY").
    estimate: list[tuple[float, float]] = []
    unreachable: list[float] = []
    proved: list[float] = []
    numbering = count()

    def evaluate(alpha: float) -> AlphaPoint:
        point_config = base.with_(alpha=alpha)
        try:
            outcome = run_one(point_config, next(numbering))
        except OracleFailure as failure:
            check = run_check()
            if failure.unsolved and check.scope is not None:
                # An order the run evaluated and that reports no key length:
                # the check notes its diagnostic there.
                check.note_order(alpha)
            raise
        point = point_from_outcome(outcome, point_config)
        if not first:
            first.append(alpha)
            held[alpha] = outcome
        if point.proves_contradiction:
            proved.append(alpha)
            held[alpha] = outcome
        if point.reason == UNREACHABLE_EVALUATION_REASON and not unreachable:
            # The evaluation the statistics check refused, at which the search
            # stops (module docstring).
            unreachable.append(alpha)
            held[alpha] = outcome
        if math.isfinite(point.score) and (not best or point.score > best[0][0]):
            best[:] = [(point.score, alpha)]
            held[alpha] = outcome
        h_low = _finite_or_none(point.h_low)
        if (
            math.isfinite(point.score)
            and h_low is not None
            and (not estimate or h_low > estimate[0][0])
        ):
            estimate[:] = [(h_low, alpha)]
            held[alpha] = outcome
        # Keep only the outcomes some rule may still return.
        keep = {*first, *unreachable, *proved}
        keep.update(alpha for _, alpha in (*best, *estimate))
        for stale in [alpha for alpha in held if alpha not in keep]:
            del held[stale]
        return point

    # ONE STATISTICS CHECK FOR THE WHOLE SEARCH, at alpha_0 fixed before any
    # order is evaluated and below none the search evaluates
    # (meat-core/req:unreachable-acceptance-set (i)): the lower end of the
    # declared domain, or the first grid point as the search evaluates it
    # (rounded to 12 significant digits), whichever is smaller.
    with searched_run(alpha_zero(settings), alpha_zero_rule(settings)) as check:
        result = search_alpha(evaluate, settings)
        # THE CHECK'S REFUSAL (item (iv)): the cap is the run's, so the run is
        # refused as a whole with the refusal of the evaluation that formed it.
        if check.refused:
            return _with_check(
                attach_alpha_search(held[unreachable[0]], result, unreachable=True),
                check,
            )
        return _with_check(_chosen_outcome(result, held, first), check)


def alpha_zero(settings: AlphaSearchSettings) -> float:
    """Return ``alpha_0`` of a searched run (``req:unreachable-acceptance-set`` (i)).

    Fixed before any order is evaluated and at most every order the search
    evaluates: the search fixes its coarse grid in advance, evaluates its
    first point, the lower end of its domain, as :func:`search_alpha` keys it
    (12 significant digits), and evaluates no order below it, the refinement
    staying between grid points. That is the lowest order it evaluates; the
    key's rounding can put it above ``1 + lower``, the lower end of the
    declared domain, and the smaller of the two is taken
    (:func:`alpha_zero_rule` says which). Where it does, ``alpha_0`` is
    ``1 + lower`` (``domain_lower_end``), below every evaluated order and
    about 1e-12 from the lowest one, which the claim's letter names.
    """
    first = float(f"{settings.coarse_grid()[0]:.12g}")
    return min(1.0 + settings.lower, first)


def alpha_zero_rule(settings: AlphaSearchSettings) -> Alpha0Rule:
    """Return which rule of item (i) fixed :func:`alpha_zero`: a record only."""
    first = float(f"{settings.coarse_grid()[0]:.12g}")
    return (
        Alpha0Rule.LOWEST_EVALUATED_ORDER
        if alpha_zero(settings) == first
        else Alpha0Rule.DOMAIN_LOWER_END
    )


def _with_check(outcome: SliceOutcome, check: RunCheck) -> SliceOutcome:
    """Return ``outcome`` carrying the whole search's statistics check.

    Every evaluation's outcome carries the check as it stood after that
    evaluation; the outcome returned carries it after the last. A runner
    that never reached :func:`~certiqs_key.runs.pipeline.run_slice` began no
    check, and its outcome is returned as it is.
    """
    record = check.record()
    if record is None:
        return outcome
    return replace(outcome, statistics_consistency=record)


def _chosen_outcome(
    result: AlphaSearchResult, held: Mapping[float, SliceOutcome], first: list[float]
) -> SliceOutcome:
    """Return the outcome :func:`run_searched` returns, the search attached."""
    if result.contradiction is not None:
        return attach_alpha_search(held[result.contradiction.alpha], result)
    if result.no_positive_key is not None:
        reported = result.no_positive_key.alpha
        if reported not in held:
            raise RuntimeError(
                f"the search reports alpha = {reported!r} with no positive key, "
                "whose run was not held; the held estimate and search_alpha's "
                "rule disagree"
            )
        return attach_alpha_search(held[reported], result)
    if result.alpha is None and not first:
        failure = next(
            e.point.failure for e in result.evaluations if e.point.failure is not None
        )
        raise failure
    alpha = result.alpha if result.alpha is not None else first[0]
    if alpha not in held:
        raise RuntimeError(
            f"the search chose alpha = {alpha!r}, whose run was not held; the "
            "held best and search_alpha's rule disagree"
        )
    return attach_alpha_search(held[alpha], result)


def attach_alpha_search(
    outcome: SliceOutcome, result: AlphaSearchResult, *, unreachable: bool = False
) -> SliceOutcome:
    """Return ``outcome`` carrying ``result``: on the outcome, and in its solve stage.

    The outcome's ``alpha_search`` field holds the search with every point's
    ``run`` dropped, so the chosen outcome does not carry the others. The
    solve stage's ``alpha`` child gains ``result.as_payload()``, whose
    ``searched: true`` replaces the one-alpha run's ``searched: false``; that
    child is what the run record carries. A solve that refused or did not run
    has no ``alpha`` child and gets one, so that a reader finds the search in
    one place on every record. Its status is ``chosen`` where the search chose
    an alpha, ``contradiction`` where an evaluation proved a contradiction,
    ``no_positive_key`` where evaluations formed bounds and none reported a
    positive key length (module docstring, "NO ALPHA GIVES A KEY") and
    ``none_chosen`` where every evaluation refused otherwise. Where a
    contradiction was proved, the refusal's detail, on the outcome and on its
    solve stage, says that the search refused the run as a whole there.
    ``unreachable``: the statistics check refuses the run as a whole (module
    docstring, "THE STATISTICS CHECK, ONCE FOR THE SEARCH"); the status is
    then ``acceptance_set_unreachable``, which takes precedence.
    """
    stripped = _without_runs(result)
    payload = stripped.as_payload()
    status = (
        "acceptance_set_unreachable"
        if unreachable
        else "contradiction"
        if stripped.contradiction is not None
        else "no_positive_key"
        if stripped.no_positive_key is not None
        else "none_chosen"
        if stripped.chosen is None
        else "chosen"
    )
    whole = (
        _unreachable_sentence(stripped)
        if unreachable
        else _whole_run_sentence(stripped)
    )
    stages = []
    for stage in outcome.stages:
        if stage.stage is SliceStage.SOLVE:
            children = list(stage.children)
            found = next(
                (i for i, child in enumerate(children) if child.name == "alpha"), None
            )
            if found is None:
                children.append(
                    StageChild(name="alpha", status=status, detail=dict(payload))
                )
            else:
                child = children[found]
                children[found] = replace(
                    child, status=status, detail={**child.detail, **payload}
                )
            stage = replace(stage, children=tuple(children))
            if whole is not None and stage.refusal_detail is not None:
                stage = replace(stage, refusal_detail=stage.refusal_detail + whole)
        stages.append(stage)
    attached = replace(outcome, stages=tuple(stages), alpha_search=stripped)
    if whole is not None and isinstance(attached, SliceRefusal):
        attached = replace(attached, detail=attached.detail + whole)
    return attached


def _unreachable_sentence(result: AlphaSearchResult) -> str:
    """Return what a refusal's detail adds where the statistics check refuses."""
    return (
        f". The outer alpha search stopped at its evaluation "
        f"{len(result.evaluations)}, where the check formed its bound: the cap "
        "is one number for the whole run, so no alpha is chosen"
    )


def _whole_run_sentence(result: AlphaSearchResult) -> str | None:
    """Return what a refusal's detail adds where the search proved a contradiction."""
    if result.contradiction is None:
        return None
    return (
        f". The outer alpha search stopped at alpha = {result.contradiction.alpha!r}, "
        f"its evaluation {len(result.evaluations)} of at most "
        f"{result.settings.coarse_points + result.settings.refine_steps}: the "
        "contradiction holds at every alpha, so the run is refused as a whole and "
        "no alpha is chosen"
    )


def _without_runs(result: AlphaSearchResult) -> AlphaSearchResult:
    """Return ``result`` with every point's ``run`` and ``failure`` dropped.

    The choice is kept, and every other field of the result (``replace``, so
    that a field added to the result cannot be dropped here unseen: the
    first version rebuilt the result and lost ``refinement_stopped``). A
    failure's traceback would hold its whole solve alive.
    """
    evaluations = tuple(
        replace(e, point=replace(e.point, run=None, failure=None))
        for e in result.evaluations
    )
    chosen = (
        None
        if result.chosen is None
        else evaluations[result.evaluations.index(result.chosen)]
    )
    contradiction = (
        None
        if result.contradiction is None
        else evaluations[result.evaluations.index(result.contradiction)]
    )
    no_positive_key = (
        None
        if result.no_positive_key is None
        else evaluations[result.evaluations.index(result.no_positive_key)]
    )
    return replace(
        result,
        evaluations=evaluations,
        chosen=chosen,
        contradiction=contradiction,
        no_positive_key=no_positive_key,
    )
