"""The Frank-Wolfe driver's shared library: options, line search, statuses.

THE LOOP IS :func:`~certiqs_key.solvers.frank_wolfe.joint_driver.run_joint_frank_wolfe`,
and every declaration runs on it. There is no separate one-factor loop;
what the joint loop shares stays here: the settings
(:class:`FrankWolfeOptions`), the golden-section search (:func:`_line_search`),
the accumulation rule, the closed list of optimal oracle statuses and the
statuses a run reports at exits the gap rule does not decide.

THE ACCUMULATION RULE, CHOSEN AND STATED
========================================
"Frank-Wolfe lower-bound accumulation is a recorded design choice. The driver
documents which accumulation rule it uses and why; a bound obtained by copying
whichever expression happened to be in scope elsewhere is not a bound this
platform can label."

The rule is the **running maximum of the per-iteration linearizations**::

    h_lb = max over contributing iterates t of
           [ f(x_t) + b^A_t - <g_t, q_t> + b^F_t - <G_t, J_t> ]

with ``b^A_t`` the exact acceptance-side minimum and ``b^F_t`` a lower bound on
the feasible-side minimum over the EXACT ``Feas^J``. The first-order condition
for a convex ``f`` gives ``f(y) >= f(x_t) + <grad f(x_t), y - x_t>`` for every
feasible ``y``, and bounding the right-hand side's minimum over ``y`` from
below makes each bracket a valid lower bound on the infimum in exact
arithmetic. It is ``h_lb`` of Theorem ``thm:firstorder``, Eq. ``eq:hlb``, with
the lower bounds of its part (iv), under the three hypotheses (H-POS),
(H-SUPP), (H-NOPERT) at every contributing iterate; the GATE is what makes the
number a claim.

THREE THINGS IT IS NOT:

* NOT an assurance about floating-point arithmetic: ``h_lb <= h_low`` holds IN
  EXACT REAL ARITHMETIC and a computed ``h_lb`` may exceed the computed
  estimate (``rem:fo-arithmetic``);
* NOT a trust in the oracle: ``b^F_t`` is the bound of
  ``lem:feasible-side-dual``, verified exactly from the backend's dual
  (``req:verified-feasible-side``), and the point the backend returned enters
  no bracket;
* NOT a backend's DUAL OBJECTIVE, which an approximately dual-feasible return
  can put above the minimum: the multipliers are a candidate the bound is
  verified from, and the objective the backend reports is never read.

WITHDRAWAL, NOT WEAKENING. When a hypothesis fails at an iterate the bracket
it would contribute is WITHDRAWN; if no iterate survives, ``h_lb`` is absent
with a machine-readable reason. "There is no reduced form of the claim."
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from certiqs_key.meat_core import thresholds

#: The accumulation rule, in one line, recorded in every certificate.
#:
#: OPEN IMPLEMENTATION CHOICE OC-7, NARROWED AND NOT DECIDED. Theorem
#: ``thm:firstorder`` (ii) is stated about "a finite non-empty index set" and
#: prescribes no optimizer; WHICH iterates a run accumulates over -- every one,
#: the last k, the ones whose oracle status asserts optimality, or one -- is
#: left to the implementation. The choice made: EVERY ITERATE THE LOOP FORMS,
#: filtered by the hypothesis gate. It is the least-committal reading, because
#: the bracket is a MAXIMUM over the set and "adding a qualifying iterate can
#: only raise it and never lowers it below what a subset gives", so no smaller
#: choice could be better and none could be unsafe.
ACCUMULATION_RULE = (
    "maximum over the CONTRIBUTING iterates of the first-order linearization "
    "O^J_alpha(x_t) + <g_t, v_t - q_t> + b^F_t - <G_t, J_t> of Eq. eq:hlb with "
    "the lower bounds of Theorem thm:firstorder (iv): v_t the exact "
    "acceptance-side minimiser and b^F_t the feasible-side bound of Lemma "
    "lem:feasible-side-dual, verified exactly from the oracle's dual "
    "(req:verified-feasible-side) and rounded toward -inf, over every iterate "
    "the loop formed at which (H-POS), (H-SUPP) and (H-NOPERT) held and the "
    "point was established to lie in AcceptSet x Feas^J(epsilon). Under those "
    "hypotheses each bracket is a lower bound on h_low IN EXACT REAL "
    "ARITHMETIC (Theorem thm:firstorder (iiib), (iv)), and the maximum of "
    "lower bounds is a lower bound. An iterate failing any of them "
    "CONTRIBUTES NO BRACKET; the oracle's return and status withdraw none"
)

#: The oracle statuses that ASSERT OPTIMALITY, read for the diagnostic
#: ``oracle_optimal`` only: no bracket reads a status, and none withdraws an
#: iterate (``req:first-order-withdrawal``; the feasible side is verified from
#: the dual, ``req:verified-feasible-side``). A CLOSED LIST AND NOT A
#: PATTERN: an unknown status is recorded as not optimal.
OPTIMAL_ORACLE_STATUSES: frozenset[str] = frozenset({"optimal", "solved"})

#: THE STATUSES THIS MODULE REPORTS AT EXITS ``optimizer_gap`` DOES NOT DECIDE,
#: named here so that the whole vocabulary a consumer can see is in one place.
#:
#: `declared_thresholds`'s two status words describe what optimizer_gap decides
#: and are not a closed vocabulary; a truthful status is reported at exits that
#: threshold does not decide.
#:
#: WHAT THAT MEANS. `declared_thresholds`'s ``optimizer_gap``
#: row decides "the
#: solver's stopping rule and its converged / iteration-limit status", and a run
#: has exits that rule does not decide: an objective that is already infinite at
#: the starting point, where no gap was ever formed, and a hypothesis of Theorem
#: ``thm:firstorder`` failing at an iterate, which Requirement
#: ``req:first-order-withdrawal`` REQUIRES the run to survive and report.
#: Reporting ``iteration-limit`` there would name a cause that did not occur;
#: reporting the truth needs a word the row does not carry. The row's two words
#: bound what THAT THRESHOLD decides and not what a run may say.
#:
#: A CLOSED LIST, like ``OPTIMAL_ORACLE_STATUSES`` above and for the same
#: reason: a new exit gets a deliberate entry here, or it reports one of the two
#: statuses `declared_thresholds` does decide and is wrong.
STATUS_HYPOTHESIS_WITHDRAWN: str = "hypothesis-withdrawn"
STATUS_OBJECTIVE_INFINITE_AT_START: str = "objective-infinite-at-start"

#: The two of them together. ``optimizer_gap`` decides neither, and a reader
#: separating "what the stopping rule said" from "why the run stopped at all"
#: reads this set.
STATUSES_OUTSIDE_THE_GAP_RULE: frozenset[str] = frozenset(
    {STATUS_HYPOTHESIS_WITHDRAWN, STATUS_OBJECTIVE_INFINITE_AT_START}
)

#: Golden ratio conjugate, for the line search.
_GOLDEN = 0.5 * (math.sqrt(5.0) - 1.0)


@dataclass(frozen=True)
class FrankWolfeOptions:
    """Tuning of the driver. None of it changes what is computed, only how far."""

    max_iterations: int = 200
    #: `declared_thresholds`'s ``optimizer_gap`` row.
    gap_tolerance: float = thresholds.declared(thresholds.OPTIMIZER_GAP)
    #: Steps are capped strictly below 1 so that an iterate never lands ON the
    #: boundary of the PSD cone, where the gradient of the next iteration would
    #: not exist (Theorem ``thm:gradient`` (ii)). The residual distance to a
    #: vertex shrinks by this factor per step, so the cap costs accuracy only
    #: at the level of ``1 - max_step``.
    max_step: float = 1.0 - 1e-10
    #: Golden-section steps in the per-iterate line search. AN IMPLEMENTATION
    #: CHOICE AND NOT A DECLARED THRESHOLD: it decides no predicate on any
    #: object, carries no row of `declared_thresholds`, and "THIS
    #: CONTRACT
    #: PRESCRIBES NO OPTIMIZER AND DOES NOT REQUIRE ONE" (Remark
    #: ``rem:fo-reachability``). It is named here rather than defaulted
    #: silently because it moves the numbers a run reports.
    #:
    #: 60 IS KEPT, AND A CUT TO TWENTY-FIVE IS MEASURED AND DECLINED. Twenty-five
    #: steps measure at two bits on the nominal point, and at the nominal point
    #: it passes: the smoke sweep at the default 200 iterations gives key
    #: lengths
    #: 1105 -> 1103 and 1105 -> 1106, two bits down on one row and one up on the
    #: other, for about half the objective evaluations -- 27 per iteration
    #: against 62, which is what the step count buys and the only part of the
    #: saving that is not confounded by process warm-up.
    #: THAT MEASUREMENT IS TAKEN AT ONE BUDGET
    #: AND THE NUMBER IS NOT SAFE AT ANOTHER. Re-solving the two bundles
    #: ``tests/integration/test_optical_bb84_slice.py`` compares, at its
    #: ``CONVERGED_ITERATIONS`` of 800:
    #:
    #:     steps   optical gap   qubit gap   combined   deficit resolvable?
    #:     60      1.98e-3       6.88e-4     2.67e-3    yes (deficit 2.30e-2)
    #:     40      1.95e-3       9.75e-3     1.17e-2    NO
    #:     25      2.76e-2       5.46e-3     3.31e-2    NO
    #:
    #: -- and that test requires the deficit to exceed THREE TIMES the combined
    #: gap before it will call the qubit-limit comparison a measurement. A
    #: search resolving the segment to ``0.618 ** 25`` of it cannot place a step
    #: below that resolution, so a long run stops descending where a
    #: ``0.618 ** 60`` search keeps going: at 200 iterations the difference is
    #: invisible and at 800 it is a factor of twelve on the combined gap.
    #: THE CUT IS THEREFORE NOT TAKEN: a criterion that fixes the point and
    #: lets the budget vary is insufficient, because the budget is the axis this
    #: number is unsafe on.
    #:
    #: WHAT THE STALL FIX BELOW IS WORTH AT 60, measured on the same two
    #: bundles at 800 iterations: the optical gap is 1.98e-3 and the qubit gap
    #: is 6.88e-4.
    line_search_iterations: int = 60
    #: How many times a line search that returned NO IMPROVING STEP may be
    #: re-run on the sub-interval it narrowed to, before the driver accepts
    #: that no representable improving step exists. Convexity of the segment
    #: objective (Theorem ``thm:convexity``) puts the minimizer at or below the
    #: returned step when ``f(step) >= f(0)``, so ``[0, step]`` discards no
    #: minimizer; and an iterate that still finds nothing takes NO STEP and the
    #: loop runs on, so the status stays true (the measured stall is in
    #: ``tests/unit/test_frank_wolfe_line_search.py``). The first pass and three
    #: refinements together narrow the segment by ``0.618 ** 240``, far below
    #: the resolution of any binary64 step, so the bound is a formality rather
    #: than a tuning
    #: knob -- and, like the budget above, it decides no predicate and carries
    #: no row of `declared_thresholds`. AT 60 STEPS IT IS ALSO NEARLY
    #: INERT: on the two
    #: bundles of the qubit-limit comparison at 800 iterations, running with
    #: three refinements and with none gives the same numbers to every digit,
    #: because no iterate there stalls. It earns its place at SMALL budgets,
    #: where the stall is what a caller meets.
    line_search_refinements: int = 3
    #: Explicit gradient perturbation (Theorem ``thm:gradient`` (ii)). ``0.0``
    #: selects exact face compression, which needs a support-maximal iterate.
    gradient_perturbation: float = 0.0
    #: `declared_thresholds`'s ``iterate_coupling`` row: how far the
    #: COUPLING RESIDUAL of
    #: a formed iterate may drift, ENTRYWISE. It is separate from a single
    #: ``feasibility_tolerance`` that would decide this and per-block
    #: positivity at one value -- "THE TWO NEED OPPOSITE WINDOWS AND CANNOT
    #: SHARE ONE", and positivity is at exactly 0.
    iterate_coupling: float = thresholds.declared(thresholds.ITERATE_COUPLING)
    #: `declared_thresholds`'s ``iterate_repair_window`` row: how
    #: negative a formed
    #: iterate's block may be, a SPECTRAL floor, before the iterate is rejected
    #: outright; below it the block is projected and the repair recorded. Its
    #: natural size is the drift an ``iterate_positivity`` window would
    #: measure, "so no run that passed at that window is refused ON THE
    #: POSITIVITY CHECK -- what would be an unrecorded pass becomes a recorded
    #: projection".
    iterate_repair_window: float = thresholds.declared(thresholds.ITERATE_REPAIR_WINDOW)
    #: `declared_thresholds`'s ``constraint_rows`` row, REQUIRED ON
    #: EVERY RUN: the
    #: declared rows of Eq. ``eq:choi-feas``, relaxed as Remark
    #: ``rem:feas-tol`` defines them, on the point consumed at an iterate.
    constraint_rows: float = thresholds.declared(thresholds.CONSTRAINT_ROWS)


def _line_search(evaluate: Any, upper: float, iterations: int) -> tuple[float, float]:
    """Return the golden-section minimizer of a convex function on ``[0, upper]``.

    The objective along a Frank-Wolfe segment is convex (Theorem
    ``thm:convexity``) and may take the value ``+inf`` towards the far end, which
    the comparison handles without special-casing.

    IT RESOLVES THE SEGMENT TO ``0.618 ** iterations`` OF IT AND NO FURTHER,
    which is the whole reason the driver refines rather than believes a search
    that reports no improvement. A minimizer nearer ``0``
    than that resolution is invisible to this function: every point it samples
    then lies past the minimum, on the rising side, and the value it returns is
    ABOVE ``evaluate(0.0)`` even though improving steps exist. Measured on the
    nominal optical point at 15 steps: ``f(0) = 0.18904006066744147``, the
    search returns ``step = 2.8003e-4`` with ``f = 0.18904666625418118`` -- no
    improvement -- while ``f(1e-5) = 0.1890399757167215`` improves, and one
    refinement on ``[0, step]`` finds ``step = 4.0524e-5`` with
    ``f = 0.18903986435357886``.
    """
    low, high = 0.0, upper
    left = high - _GOLDEN * (high - low)
    right = low + _GOLDEN * (high - low)
    f_left, f_right = evaluate(left), evaluate(right)
    for _ in range(iterations):
        if f_left <= f_right:
            high, right, f_right = right, left, f_left
            left = high - _GOLDEN * (high - low)
            f_left = evaluate(left)
        else:
            low, left, f_left = left, right, f_right
            right = low + _GOLDEN * (high - low)
            f_right = evaluate(right)
    best = left if f_left <= f_right else right
    return best, min(f_left, f_right)
