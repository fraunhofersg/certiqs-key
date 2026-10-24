"""The line-search budget, its refinement, and the status a stall may report.

THE STATUS FIX IS IN; A CUT TO TWENTY-FIVE STEPS IS NOT, AND THE REASON IS
MEASURED. A cut to twenty-five steps measures at two bits on the nominal point,
and the stall-break status fix does not move the nominal point at the
sixty-step budget, where the run reaches the iteration limit honestly, but
without it a smaller budget reports a false ``iteration-limit``. A criterion
that fixes the point and lets the budget vary is insufficient, and the budget
is the axis a coarse search is unsafe on: at the default 200 iterations
25 steps costs two bits, and at the 800 of
``tests/integration/test_optical_bb84_slice.py`` it costs a factor of twelve on
the combined Frank-Wolfe gap -- 3.31e-2 against 2.67e-3 -- which is more than
the qubit-limit comparison there can resolve its deficit against. 40 steps
fails the same test on the qubit bundle (9.75e-3). The table and the decision
are recorded at ``FrankWolfeOptions.line_search_iterations``.

WHAT THE DEFECT IS. A golden-section search resolves its segment to ``0.618 **
iterations`` of it and no further. When the minimizer along a Frank-Wolfe
segment lies nearer ``0`` than that, every point the search samples is past the
minimum on the rising side, the search reports a value ABOVE the one it started
from, and the driver would read that as "no improving step exists" and stop. It
would then report ``iteration-limit`` with most of its iteration budget unspent
-- a status that names a cause that did not occur.

MEASURED, on the nominal optical point of the fig. 1 smoke sweep (route
``encoded``), at ``alpha = 1.05``, without the fix:

    line-search steps   iterations   status            gap        key length
    60                  200          iteration-limit   2.16e-2    1105
    25                  200          iteration-limit   8.54e-3    1103
    15                   41          iteration-limit   3.73e-2    1085   <- false
    10                    4          iteration-limit   7.24e-2     708   <- false
     5                    2          iteration-limit   9.07e-1       0   <- false

and at the first stall of the 15-step run, ``f(0) = 0.18904006066744147`` while
the search returned ``f = 0.18904666625418118`` at ``step = 2.8003e-4`` -- yet
``f(1e-5) = 0.1890399757167215`` improves, and ONE refinement on ``[0, step]``
found ``step = 4.0524e-5`` with ``f = 0.18903986435357886``. So the improving
step was there and the resolution was not.

WHY THE FIX IS A REFINEMENT AND NOT A NEW STATUS STRING. The contract names two
statuses, at Section 2.6's ``optimizer_gap`` row -- "the solver's stopping rule
and its converged / iteration-limit status" -- and a status string is contract
vocabulary rather than an implementation's to invent. The exit is therefore
removed rather than named: a search that cannot improve is re-run on the
sub-interval convexity puts the minimizer in, and if even that finds nothing
the iterate takes NO STEP and the loop runs on. That leaves exactly the two
exits the contract describes, and the reported status is true at both.

WHY THE DRIVER-LEVEL ROW BELOW STUBS THE SEARCH. Reproducing a real stall needs
the optical declaration and a QICS solve -- half a minute for a single point,
and a test may not spend that. The stub reproduces the CONDITION the fix is
about, exactly and deterministically: a line search that reports no improvement.
Nothing about the branch under test is weakened by it, and the measured case it
stands in for is the table above.

ONE DRIVER. The joint driver carries the search, the refinement and the
no-step rule, and the rows below run it.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pytest
from withdrawal_toys import StubAcceptanceOracle, interior_start, toy_setup

from certiqs_key.solvers.capabilities.probe import Capability, OracleCapabilities
from certiqs_key.solvers.frank_wolfe import joint_driver as driver_module
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions, _line_search
from certiqs_key.solvers.frank_wolfe.joint_driver import run_joint_frank_wolfe
from certiqs_key.solvers.oracles.protocol import OracleSolution, SectorChoiProblem

#: The segment objective of the measured stall, in miniature: convex, minimized
#: at a step far below what a coarse golden-section search can resolve, and
#: rising steeply on either side of it so that a sample past the minimum is
#: worse than the point the search started from.
_MINIMIZER = 1e-9


def _convex_segment(step: float) -> float:
    """Return a convex function of the step with its minimum at ``_MINIMIZER``."""
    return (step - _MINIMIZER) ** 2


@dataclass
class _GreedyOracle:
    """The exact linear minimizer over TOY-1's feasible set.

    TOY-1 carries two one-by-one sector blocks and ``d_{A_0} = 1``, so
    Eq. ``eq:choi-feas``'s coupling condition reads ``w_0 + w_1 = 1`` with both
    weights non-negative: the feasible set is a segment and its linear minimizer
    is the endpoint with the smaller cost. Returning that endpoint -- rather
    than a fixed point a stub declares -- is what makes the Frank-Wolfe gap
    below a real gap, so the runs here stop for the reasons a run stops for.
    """

    calls: int = field(default=0)

    def capabilities(self) -> OracleCapabilities:
        """Declare what the driver probes; nothing here is backend-specific."""
        return OracleCapabilities(
            name="greedy",
            version="0",
            capabilities=frozenset(
                {
                    Capability.COMPLEX_HERMITIAN_PSD,
                    Capability.DIRECT_SUM_SECTORS,
                    Capability.CHOI_FORM,
                    Capability.EQUALITY_ROWS,
                    Capability.INEQUALITY_ROWS,
                }
            ),
        )

    def minimize(self, problem: SectorChoiProblem) -> OracleSolution:
        """Return all the weight on the sector with the smaller cost."""
        self.calls += 1
        cost: Mapping[str, np.ndarray] = problem.cost
        best = min(cost, key=lambda name: float(np.real(cost[name][0, 0])))
        return OracleSolution(
            blocks={
                name: np.array([[1.0 if name == best else 0.0]], dtype=np.complex128)
                for name in cost
            },
            objective=0.0,
            diagnostics={"sol_status": "optimal"},
        )


def _toy_run(options: FrankWolfeOptions) -> Any:
    """Run the driver on TOY-1 from its interior start, with a true minimizer."""
    declaration, maps = toy_setup("TOY-1")
    return run_joint_frank_wolfe(
        maps,
        _GreedyOracle(),
        StubAcceptanceOracle(
            frequencies=dict.fromkeys(declaration.acceptance_values, 1.0),
            exact_island=True,
        ),
        interior_start(declaration),
        alpha=1.5,
        options=options,
    )


# ===========================================================================
#  The budget.
# ===========================================================================


def test_the_shipped_line_search_budget_is_sixty_steps() -> None:
    """The number a measurement chose, pinned where a silent change would go unnoticed.

    Not a mathematical claim -- contract Remark ``rem:fo-reachability`` says
    "THIS CONTRACT PRESCRIBES NO OPTIMIZER AND DOES NOT REQUIRE ONE", so no row
    of Section 2.6 carries this number and none could. What the assertion pins
    is which value the runs use, and that a cut to 25 steps was measured and DECLINED:
    at 800 iterations it leaves a combined gap of 3.31e-2 where 60 leaves
    2.67e-3, and the qubit-limit comparison of
    ``tests/integration/test_optical_bb84_slice.py`` needs the deficit
    (2.30e-2) to exceed three times that combined gap.
    """
    assert FrankWolfeOptions().line_search_iterations == 60
    assert FrankWolfeOptions().line_search_refinements == 3


# ===========================================================================
#  The resolution artifact, on a function whose minimum is known.
# ===========================================================================


def test_a_coarse_search_misses_a_minimizer_below_its_resolution() -> None:
    """The defect, in isolation: the search is out of resolution, not out of steps.

    Twenty-five golden-section steps narrow ``[0, 1]`` to about ``5e-6`` of
    itself, and the minimizer here is at ``1e-9``. Every point the search
    samples therefore lies past the minimum, where the function is already
    above its value at ``0`` -- so the search returns NO IMPROVEMENT even
    though the segment descends from ``0``.
    """
    at_zero = _convex_segment(0.0)
    step, value = _line_search(_convex_segment, 1.0, 25)

    assert value >= at_zero, "the coarse search is expected to miss the minimum"
    assert step > _MINIMIZER, "and to return a point past it"
    assert _convex_segment(_MINIMIZER) < at_zero, "while an improving step exists"


def test_refining_on_the_returned_step_finds_what_the_coarse_search_missed() -> None:
    """The fix, in isolation, together with the interval it is entitled to use.

    Convexity of the segment objective (Theorem ``thm:convexity``) turns
    ``f(step) >= f(0)`` into "the minimizer lies at or below ``step``": were it
    above, ``f`` would be non-increasing on ``[0, step]`` and ``f(step)`` could
    not exceed ``f(0)``. So re-searching ``[0, step]`` discards no minimizer,
    and one round of it is enough here.
    """
    at_zero = _convex_segment(0.0)
    step, value = _line_search(_convex_segment, 1.0, 25)
    assert value >= at_zero

    refined_step, refined_value = _line_search(_convex_segment, step, 25)

    assert refined_value < at_zero, "the refinement improves on the starting point"
    assert refined_step <= step, "and stays inside the interval it was given"


# ===========================================================================
#  The status, at the shipped budget and at a search that cannot improve.
# ===========================================================================


def test_a_run_that_meets_the_gap_rule_reports_converged() -> None:
    """The shipped budget, unchanged: the gap rule fires and says so.

    Contract Section 2.6, ``optimizer_gap``: this threshold decides "the
    solver's stopping rule and its converged / iteration-limit status".
    """
    result = _toy_run(FrankWolfeOptions(max_iterations=30))

    assert result.status == "converged"
    assert result.gap <= FrankWolfeOptions().gap_tolerance
    assert result.iterations < 30, "it converged before its budget was spent"


def test_a_run_that_spends_its_budget_reports_the_iteration_limit() -> None:
    """The other exit, at the shipped budget: the limit is reported when reached.

    ``max_iterations = 1`` is below what this toy needs -- at the shipped
    sixty-step budget it converges at iteration 2 -- so the run leaves the loop
    by exhausting it, and the count it reports IS the limit, which is what
    makes the status true.
    """
    result = _toy_run(FrankWolfeOptions(max_iterations=1))

    assert result.status == "iteration-limit"
    assert result.iterations == 1
    assert result.gap > FrankWolfeOptions().gap_tolerance


def test_a_search_that_cannot_improve_does_not_end_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The status fix: no ``iteration-limit`` while iterations remain.

    The stubbed search reports no improvement at every call, which is the
    condition a coarse search creates on the real declaration (the module
    docstring's 15-step row: it stopped at iteration 41 of 200 and reported
    ``iteration-limit``). The run must now spend its budget before reporting
    that it reached the limit, and the iterate must not move: nothing better
    was found, so nothing is stepped to.
    """
    calls: list[float] = []

    def never_improves(
        evaluate: Any, upper: float, iterations: int
    ) -> tuple[float, float]:
        del evaluate, iterations
        calls.append(upper)
        return upper, math.inf

    monkeypatch.setattr(driver_module, "_line_search", never_improves)
    options = FrankWolfeOptions(max_iterations=4, line_search_refinements=3)

    result = _toy_run(options)

    assert result.status == "iteration-limit"
    assert result.iterations == options.max_iterations, (
        "the limit is reported only when it is reached"
    )
    assert result.gap > options.gap_tolerance, "and the gap rule did not fire"
    # One search plus its refinements, at every iteration: the refinement bound
    # is what stops a search that cannot improve from being retried forever.
    assert len(calls) == options.max_iterations * (1 + options.line_search_refinements)


def test_a_refinement_searches_the_interval_the_previous_search_returned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each refinement is handed ``[0, step]`` of the search before it.

    That interval, and not a smaller or arbitrary one, is what convexity
    licenses: ``f(step) >= f(0)`` puts the minimizer at or below ``step``.
    """
    uppers: list[float] = []

    def shrinking(evaluate: Any, upper: float, iterations: int) -> tuple[float, float]:
        del evaluate, iterations
        uppers.append(upper)
        return upper / 4.0, math.inf

    monkeypatch.setattr(driver_module, "_line_search", shrinking)
    options = FrankWolfeOptions(max_iterations=1, line_search_refinements=2)

    _toy_run(options)

    assert uppers[0] == options.max_step
    assert uppers[1] == pytest.approx(options.max_step / 4.0)
    assert uppers[2] == pytest.approx(options.max_step / 16.0)


def test_an_iterate_that_cannot_improve_takes_no_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The run reports the objective at the point it returned, and it did not move.

    Remark ``rem:fo-interface``: every run reports "the objective at the
    point it returned -- an upper estimate". Continuing the loop rather than
    breaking must not be read as licence to step to a point the search never
    found better.
    """

    def never_improves(
        evaluate: Any, upper: float, iterations: int
    ) -> tuple[float, float]:
        del iterations
        return upper, evaluate(0.0) + 1.0

    declaration, maps = toy_setup("TOY-1")
    start = interior_start(declaration)
    monkeypatch.setattr(driver_module, "_line_search", never_improves)

    result = run_joint_frank_wolfe(
        maps,
        _GreedyOracle(),
        StubAcceptanceOracle(
            frequencies=dict.fromkeys(declaration.acceptance_values, 1.0),
            exact_island=True,
        ),
        start,
        alpha=1.5,
        options=FrankWolfeOptions(max_iterations=3),
    )

    for sector, block in start.items():
        assert result.choi[sector] == pytest.approx(block)
    assert result.status == "iteration-limit"
    assert result.iterations == 3
