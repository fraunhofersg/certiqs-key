"""The two new routes at n = 10^9, which is what they exist for.

THE WALL THIS MOVES. The exact rule's sweep is linear to quadratic in ``n`` per
constrained outcome -- the running binomial sum is swept from zero -- so at
``n = 10^9`` it is not merely slow but out of reach: a billion exact rational
additions per endpoint, on mass points whose common denominator is ``b^n``.
The two routes are the answer:

* ``endpoint_rule = bernstein`` is CLOSED FORM, constant per endpoint;
* ``tail_evaluation = enclosure`` is about ``log2(n)`` enclosure evaluations
  per endpoint, each on rationals OF THE SIZE OF A LOGARITHM.

WHAT IS ASSERTED, AND WHAT DELIBERATELY IS NOT. This test asserts that both
routes FINISH and that what they emit is ADMISSIBLE -- the endpoints meet their
budgets, the honest point is inside, and the emitted box is a well-formed
canonical box -- and that the enclosure route's upper endpoint is at or below
the Bernstein route's, which is the ordering
``prop:rule-bernstein`` (iii) predicts (the Bernstein rule is never narrower
than the exact rule's quantile interval, and the enclosure evaluation is the
exact rule's up to a bounded conservatism).

IT ASSERTS NO ENDPOINT VALUE. There is no independent derivation of a binomial
quantile at ``n = 10^9`` to check one against -- the sweep cannot be run and
the frozen oracles stop at ``n`` in the thousands -- so a frozen integer here
would be the code checking itself. What CAN be checked without the code is
admissibility, and that is what is checked: the emitted endpoints are compared
against the Bernstein bound of ``lem:bernstein-tail``, which is a closed form a
reader can evaluate on paper.

MARKED ``slow`` and deselected by the default tier (``tests/conftest.py``). It
is the one test of this module that takes seconds rather than milliseconds.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from certiqs_key.statistics import (
    AcceptanceRequest,
    BudgetAllocation,
    EndpointRuleName,
    TailEvaluation,
    construct,
)

pytestmark = pytest.mark.slow

#: A billion rounds, an honest mass of one in a thousand -- an expected count
#: of a million, a standard deviation of about a thousand -- and a per-side
#: budget of 1e-9, which is the regime a fine-grained joint alphabet puts this
#: module in at the round counts the engine targets.
ROUNDS = 10**9
HONEST = Fraction(1, 1000)
BUDGET = Fraction(1, 10**9)


def _request(rule: EndpointRuleName, evaluation: TailEvaluation) -> AcceptanceRequest:
    """Return a ONE-OUTCOME request: the second outcome is unconstrained."""
    return AcceptanceRequest(
        alphabet=("c0", "c1"),
        honest={"c0": HONEST, "c1": Fraction(1) - HONEST},
        rounds=ROUNDS,
        budget=2 * BUDGET,
        constrained=("c0",),
        allocation=BudgetAllocation((BUDGET,), (BUDGET,)),
        endpoint_rule=rule,
        tail_evaluation=evaluation,
    )


def _bernstein_deviation(budget: Fraction) -> float:
    """Return ``t(L)`` of Eq. ``eq:bernstein-t`` as a float, for the comparison.

    A READING AID AND NOT AN ORACLE: it is used only to bound a difference that
    is already asserted exactly by other means, and the assertions below do not
    turn on its last digits. ``L = ln(1/eps)``, ``v = n p (1-p)``.
    """
    term = math.log(1 / float(budget))
    variance = float(ROUNDS) * float(HONEST) * (1 - float(HONEST))
    return term / 3 + math.sqrt((term / 3) ** 2 + 2 * variance * term)


@pytest.mark.contract
def test_both_new_routes_finish_at_a_billion_rounds_and_emit_admissible_boxes() -> None:
    """Both routes emit, and everything that can be checked without the sweep is.

    The sweep is not run and cannot be: that is the point of the two routes.
    What is checked is what ``thm:box-construction`` proves of every admissible rule --
    the bounds are exact rationals with denominator ``n``, they form a canonical
    box, and the honest point is inside -- plus the ordering between the two
    routes.
    """
    boxes: dict[str, tuple[int, int]] = {}
    for rule, evaluation in (
        (EndpointRuleName.EXACT, TailEvaluation.ENCLOSURE),
        (EndpointRuleName.BERNSTEIN, TailEvaluation.SWEEP),
    ):
        result = construct(_request(rule, evaluation))
        assert result.infeasibility_report is None
        assert result.acceptance_set is not None
        assert result.acceptance_set.box_bounds is not None
        lower, upper = result.acceptance_set.box_bounds
        # thm:box-construction (i): a multiple of 1/n on Chat_con, 0 and 1 off it.
        assert lower[0].denominator <= ROUNDS
        assert upper[0].denominator <= ROUNDS
        assert (lower[1], upper[1]) == (Fraction(0), Fraction(1))
        # thm:box-construction (ii) and (iii): a canonical box containing the honest
        # point.
        assert Fraction(0) <= lower[0] <= HONEST <= upper[0] <= Fraction(1)
        # thm:completeness-bound: the figure is in [0, ecomp].
        assert result.completeness_certified is not None
        assert Fraction(0) <= result.completeness_certified <= 2 * BUDGET
        interval = result.intervals[0]
        assert interval is not None
        boxes[str(rule)] = (interval.k_lower, interval.k_upper)

    # THE ORDERING: the enclosure evaluation is the exact rule's up to a
    # bounded conservatism, and the Bernstein rule is never narrower than the
    # exact rule's quantile interval (prop:rule-bernstein (iii)), so the
    # enclosure route's interval sits INSIDE the Bernstein route's.
    enclosure = boxes[str(EndpointRuleName.EXACT)]
    bernstein = boxes[str(EndpointRuleName.BERNSTEIN)]
    assert enclosure[1] <= bernstein[1]
    assert enclosure[0] >= bernstein[0]

    # AND BOTH SIT WHERE BERNSTEIN'S CLOSED FORM SAYS THEY MUST: within a few
    # counts of np +- t(L) on the Bernstein route, and inside it on the other.
    mean = float(ROUNDS) * float(HONEST)
    deviation = _bernstein_deviation(BUDGET)
    assert abs(bernstein[1] - (mean + deviation)) < 2
    assert abs(bernstein[0] - (mean - deviation)) < 2


@pytest.mark.contract
def test_the_enclosure_route_reports_its_bracket_verdict_at_a_billion_rounds() -> None:
    """The diagnostic the enclosure route exists to make legible.

    ``prop:bracketed-endpoints`` (ii) and the ``endpoint_exact`` output row: at
    this ``n`` the enclosure's width is dominated by the Wallis constant's
    contribution, about ``1.8e-4`` nats, against a per-count decay of about
    ``3e-3`` nats, so the bracket is expected to be decided on both sides --
    and the test asserts the DIAGNOSTIC IS EMITTED and is a boolean per side,
    not that it is true, because whether a particular bracket closes is a
    numerical fact and not a claim.
    """
    result = construct(
        _request(EndpointRuleName.EXACT, TailEvaluation.ENCLOSURE)
    )
    assert result.endpoint_exact is not None
    (row,) = result.endpoint_exact
    assert row.outcome == "c0"
    assert isinstance(row.lower_decided, bool)
    assert isinstance(row.upper_decided, bool)
    # AND THE PARAMETERS THAT PRODUCED IT ARE IN THE RECORD, which is what
    # makes the figure identifiable (interface.yaml, the honest_model row).
    assert result.honest_model is not None
    recorded = dict(result.honest_model.evaluation_parameters)
    assert recorded["the_enclosure_route.root_exponent_j"] > 0
    assert recorded["the_enclosure_route.wallis_length_M"] > 0
    assert result.honest_model.tail_evaluation == "enclosure"


@pytest.mark.contract
def test_the_bernstein_route_is_constant_per_endpoint_at_a_billion_rounds() -> None:
    """No tail is evaluated to find an endpoint, so ``n`` enters as a number.

    The rule's cost does not depend on ``n`` beyond the bit length of the
    integers it multiplies, which is what "constant per endpoint" means in
    ``rule_table``. Asserted by running the SAME request at two round counts
    nine orders of magnitude apart and checking both return: a route whose cost
    grew with ``n`` would not.
    """
    for rounds in (10**3, ROUNDS):
        request = AcceptanceRequest(
            alphabet=("c0", "c1"),
            honest={"c0": HONEST, "c1": Fraction(1) - HONEST},
            rounds=rounds,
            budget=2 * BUDGET,
            constrained=("c0",),
            allocation=BudgetAllocation((BUDGET,), (BUDGET,)),
            endpoint_rule=EndpointRuleName.BERNSTEIN,
            tail_evaluation=TailEvaluation.SWEEP,
        )
        result = construct(request)
        assert result.acceptance_set is not None
        interval = result.intervals[0]
        assert interval is not None
        assert 0 <= interval.k_lower <= interval.k_upper <= rounds
        # The allocation sum is what this route reports, and it needs no clamp.
        assert result.completeness_certified == 2 * BUDGET
