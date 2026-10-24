"""The two new routes against ``registry_statistics_rules``, value by value.

The companion of ``test_statistics_acceptance_against_registry.py``, which
reproduces the 55 frozen cases on the DEFAULT route. This file
reproduces the cases frozen for the two other routes:
the Bernstein rule of ``binomial-box/prop:rule-bernstein`` and the local
enclosure evaluation of ``binomial-box/prop:bracketed-endpoints``.

WHAT IS ASSERTED, AND WHY EACH ASSERTION IS WORTH ITS LINE.

* The Bernstein endpoints ARE the frozen integers, at the module's settled
  evaluation parameters and at two other settings. The frozen integers were
  derived over a bracket of ``L``, and the test asserts that ``L`` lands in
  that bracket at each pinned ``(j, s)`` (the registry's stated hypothesis),
  so a value that moved while ``L`` stayed inside would mean the derivation
  was wrong -- which is a finding, not a tolerance.
* The enclosure route's endpoints ARE the frozen ones, its bracket verdict IS
  the frozen verdict, and where the bracket is decided the emitted endpoint
  EQUALS the sweep's (``prop:bracketed-endpoints`` (ii)). Where it is not, the
  emitted endpoint still CONTAINS the sweep's, which is that proposition's (i).
* The relation that holds on every case whether the bracket is decided or not:
  the enclosure's upper endpoint is at or above the sweep's and its lower
  endpoint at or below, so the emitted box contains the box the sweep emits.

THE SWEEP IS THE SECOND WITNESS HERE, and that is deliberate: the frozen table
gives the exact quantiles independently, and the sweep computes them by a
different route (a running binomial sum). Where the three agree, three
independent derivations agree.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from registry_statistics_rules import (
    BERNSTEIN_CASES,
    ENCLOSURE_CASES,
    BernsteinCase,
    EnclosureCase,
)

from certiqs_key.statistics import (
    AcceptanceRequest,
    BernsteinParameters,
    BudgetAllocation,
    EnclosureParameters,
    EndpointRuleName,
    TailEvaluation,
    bernstein_lower_endpoint,
    bernstein_upper_endpoint,
    bracketed_lower_endpoint,
    bracketed_upper_endpoint,
    construct,
    extremal_endpoints,
    guarded_endpoints,
    lower_tail,
    resolve_rule,
    upper_tail,
)
from certiqs_key.statistics.bernstein import budget_term

#: Three settings of the Bernstein evaluation's parameters: the module's own,
#: one coarser and one finer. The frozen endpoints must be the same at all
#: three, which is what makes them facts about the RULE. The coarse one is
#: (18, 36) and not (16, 32): with the evaluation aligned with
#: prop:rule-bernstein (ii), the L for eps = 1/1000 (6.908129) at (16, 32)
#: leaves that case's bracket [6.907, 6.908], and at (18, 36) every L is inside.
BERNSTEIN_SETTINGS = (
    BernsteinParameters(),
    BernsteinParameters(root_exponent=18, root_precision=36),
    BernsteinParameters(root_exponent=40, root_precision=96),
)

#: Two settings of the enclosure evaluation's parameters: the module's own, and
#: one with a shorter window and a coarser root. At the small ``n`` of the
#: frozen cases the verdicts must agree, the margins being orders of magnitude
#: above either setting's width.
ENCLOSURE_SETTINGS = (
    EnclosureParameters(),
    EnclosureParameters(
        root_exponent=32, root_precision=96, wallis_length=512, window_cap=64
    ),
)


def _request(case: EnclosureCase, evaluation: TailEvaluation) -> AcceptanceRequest:
    """Return a one-outcome request that isolates the frozen ``(n, p, eps)``.

    The alphabet has a second outcome carrying the remaining honest mass and is
    left UNCONSTRAINED, so the frozen budget is spent entirely on the outcome
    the case is about and the emitted interval for it is the case's.
    """
    return AcceptanceRequest(
        alphabet=("c0", "c1"),
        honest={"c0": case.honest, "c1": Fraction(1) - case.honest},
        rounds=case.rounds,
        budget=case.eps_lower + case.eps_upper,
        constrained=("c0",),
        allocation=BudgetAllocation((case.eps_lower,), (case.eps_upper,)),
        endpoint_rule=EndpointRuleName.EXACT,
        tail_evaluation=evaluation,
    )


# ---------------------------------------------------------------------------
#  The Bernstein rule
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", BERNSTEIN_CASES, ids=lambda c: c.case_id)
@pytest.mark.parametrize(
    "parameters",
    BERNSTEIN_SETTINGS,
    ids=lambda p: f"j{p.root_exponent}s{p.root_precision}",
)
def test_the_frozen_bernstein_endpoints_are_reproduced(
    case: BernsteinCase, parameters: BernsteinParameters
) -> None:
    """Eq. ``eq:bernstein-endpoints``, at three settings of ``(j, s)``.

    The two convention cases go through the rule object, because
    ``def:endpoint-rule`` (b) and (c) are applied there and not inside the
    closed form -- that is the point of having one place that enforces them.
    """
    rule = resolve_rule(EndpointRuleName.BERNSTEIN, TailEvaluation.SWEEP)
    endpoints = rule.endpoints(
        case.rounds, case.honest, case.eps_lower, case.eps_upper
    )
    assert endpoints.lower == case.endpoint_lower, case.case_id
    assert endpoints.upper == case.endpoint_upper, case.case_id
    if case.honest in (Fraction(0), Fraction(1)) or case.eps_upper == Fraction(0):
        return
    assert (
        case.budget_low <= budget_term(case.eps_upper, parameters) <= case.budget_high
    ), case.case_id
    assert (
        bernstein_lower_endpoint(case.rounds, case.honest, case.eps_lower, parameters)
        == case.endpoint_lower
    )
    assert (
        bernstein_upper_endpoint(case.rounds, case.honest, case.eps_upper, parameters)
        == case.endpoint_upper
    )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", BERNSTEIN_CASES, ids=lambda c: c.case_id)
def test_the_bernstein_interval_contains_the_exact_quantile_interval(
    case: BernsteinCase,
) -> None:
    """``prop:rule-bernstein`` (iii), last sentence, on every frozen case.

    "It never emits an interval narrower than the exact rule's raw quantile
    interval", the quantiles being the extremal admissible indices
    (``prop:rule-exact`` (iii)). Checked against the sweep, which computes
    those quantiles by a route this rule shares no step with.
    """
    kappa_lower, kappa_upper, _ = extremal_endpoints(
        case.rounds, case.honest, case.eps_lower, case.eps_upper
    )
    assert case.endpoint_lower <= kappa_lower, case.case_id
    assert case.endpoint_upper >= kappa_upper, case.case_id


# ---------------------------------------------------------------------------
#  The enclosure evaluation
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", ENCLOSURE_CASES, ids=lambda c: c.case_id)
@pytest.mark.parametrize(
    "parameters", ENCLOSURE_SETTINGS, ids=lambda p: f"j{p.root_exponent}T{p.window_cap}"
)
def test_the_frozen_bracketed_endpoints_and_verdicts_are_reproduced(
    case: EnclosureCase, parameters: EnclosureParameters
) -> None:
    """The endpoints AND the bracket verdict, at two settings of the parameters."""
    lower = bracketed_lower_endpoint(
        case.rounds, case.honest, case.eps_lower, parameters
    )
    upper = bracketed_upper_endpoint(
        case.rounds, case.honest, case.eps_upper, parameters
    )
    assert lower.index == case.bracketed_lower, case.case_id
    assert upper.index == case.bracketed_upper, case.case_id
    assert lower.decided is case.lower_decided, case.case_id
    assert upper.decided is case.upper_decided, case.case_id


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", ENCLOSURE_CASES, ids=lambda c: c.case_id)
def test_the_enclosure_equals_the_sweep_where_the_bracket_is_decided(
    case: EnclosureCase,
) -> None:
    """``prop:bracketed-endpoints`` (i) and (ii), against the sweep itself.

    (ii) where the bracket is decided the emitted endpoint IS the exact
    quantile; (i) always, the emitted interval contains the sweep's. The sweep
    is the independent witness, and the frozen table is the third.
    """
    kappa_lower, kappa_upper, exact = extremal_endpoints(
        case.rounds, case.honest, case.eps_lower, case.eps_upper
    )
    assert exact is True
    assert (kappa_lower, kappa_upper) == (case.kappa_lower, case.kappa_upper)
    lower = bracketed_lower_endpoint(case.rounds, case.honest, case.eps_lower)
    upper = bracketed_upper_endpoint(case.rounds, case.honest, case.eps_upper)
    # (i) -- ALWAYS, decided or not.
    assert lower.index <= kappa_lower
    assert upper.index >= kappa_upper
    # (ii) -- where the bracket is decided.
    if upper.decided:
        assert upper.index == kappa_upper
    if lower.decided:
        assert lower.index == kappa_lower


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", ENCLOSURE_CASES, ids=lambda c: c.case_id)
def test_the_guarded_endpoints_and_the_emitted_box_are_the_frozen_ones(
    case: EnclosureCase,
) -> None:
    """Eq. ``eq:guard`` on the bracketed endpoints, through the construction map.

    The route is exercised END TO END here rather than at the rule: the
    request carries ``tail_evaluation = enclosure``, and what is compared is
    the emitted box bound and the ``endpoint_exact`` diagnostic.
    """
    lower, upper = guarded_endpoints(
        case.rounds, case.honest, case.bracketed_lower, case.bracketed_upper
    )
    assert (lower, upper) == (case.guarded_lower, case.guarded_upper)

    result = construct(_request(case, TailEvaluation.ENCLOSURE))
    assert result.acceptance_set is not None
    assert result.acceptance_set.box_bounds is not None
    box_lower, box_upper = result.acceptance_set.box_bounds
    assert box_lower[0] == Fraction(case.guarded_lower, case.rounds)
    assert box_upper[0] == Fraction(case.guarded_upper, case.rounds)
    assert result.endpoint_exact is not None
    (row,) = result.endpoint_exact
    assert row.outcome == "c0"
    assert row.lower_decided is case.lower_decided
    assert row.upper_decided is case.upper_decided


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", ENCLOSURE_CASES, ids=lambda c: c.case_id)
def test_the_enclosure_box_contains_the_sweep_box_end_to_end(
    case: EnclosureCase,
) -> None:
    """The emitted SET, not only the endpoints, on both routes of the same request.

    ``prop:bracketed-endpoints`` (i), last sentence: "the box
    ``Acc_{R_encl}`` emits contains the box the exact rule emits: every ``q^-``
    is at most and every ``q^+`` at least the exact rule's".

    AND THE TWO REPORTED FIGURES ARE NOT COMPARABLE ACROSS ROUTES, which is
    worth asserting the right way round rather than leaving to a reader. A
    WIDER box has a SMALLER honest failure probability, so the enclosure
    route's figure may be below the sweep's and routinely is: on the undecided
    case the enclosure emits ``[2, 8]`` where the sweep emits ``[3, 7]``, and
    the tails at ``2`` and ``8`` are a fifth of the tails at ``3`` and ``7``.
    What ``rem:epsstar`` requires, and what is asserted here, is that EACH
    route's figure is at least the exact ``epsilon_star`` OF ITS OWN EMITTED
    SET and at most ``ecomp``.
    """
    sweep = construct(_request(case, TailEvaluation.SWEEP))
    enclosure = construct(_request(case, TailEvaluation.ENCLOSURE))
    assert sweep.acceptance_set is not None
    assert enclosure.acceptance_set is not None
    assert sweep.acceptance_set.box_bounds is not None
    assert enclosure.acceptance_set.box_bounds is not None
    sweep_lower, sweep_upper = sweep.acceptance_set.box_bounds
    encl_lower, encl_upper = enclosure.acceptance_set.box_bounds
    for low, high in zip(encl_lower, sweep_lower, strict=True):
        assert low <= high
    for low, high in zip(sweep_upper, encl_upper, strict=True):
        assert low <= high
    budget = case.eps_lower + case.eps_upper
    for result, guarded in (
        (sweep, (case.kappa_lower, case.kappa_upper)),
        (enclosure, (case.guarded_lower, case.guarded_upper)),
    ):
        exact_star = (
            lower_tail(case.rounds, case.honest, guarded[0]).value
            + upper_tail(case.rounds, case.honest, guarded[1]).value
        )
        assert result.completeness_certified is not None
        assert result.completeness_certified >= exact_star
        assert result.completeness_certified <= budget
    # The sweep emits no diagnostic at all: it forms no bracket.
    assert sweep.endpoint_exact is None


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("mass", [Fraction(0), Fraction(1)])
def test_the_degenerate_mass_convention_reports_a_decided_bracket(
    mass: Fraction,
) -> None:
    """``def:endpoint-rule`` (c) decides the endpoint; the diagnostic says so.

    At ``p`` in ``{0, 1}`` both tails are exactly zero
    (``prop:rule-exact`` (v)) and the emitted endpoint IS the exact quantile --
    ``def:endpoint-rule`` (c) makes it a requirement of every rule -- so the
    ``endpoint_exact`` row, "whether the emitted endpoint is PROVED equal to
    the exact binomial quantile", is ``True`` on both sides.

    THE VERDICT IS SET ON THE CONVENTION BRANCH: leaving it unset would let
    the table coerce the absence to ``False``, reporting "not proved" of the
    one case the contract proves outright.
    """
    result = construct(
        AcceptanceRequest(
            alphabet=("c0", "c1"),
            honest={"c0": mass, "c1": Fraction(1) - mass},
            rounds=5,
            budget=Fraction(1, 10),
            constrained=("c0",),
            tail_evaluation=TailEvaluation.ENCLOSURE,
        )
    )
    assert result.endpoint_exact is not None
    (row,) = result.endpoint_exact
    assert row.outcome == "c0"
    assert row.lower_decided is True
    assert row.upper_decided is True
    # AND THE ENDPOINTS ARE THE CONVENTION'S, which is what makes the verdict
    # true rather than merely convenient.
    interval = result.intervals[0]
    assert interval is not None
    expected = 0 if mass == Fraction(0) else 5
    assert (interval.k_lower, interval.k_upper) == (expected, expected)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_zero_budget_convention_also_reports_a_decided_bracket() -> None:
    """``def:endpoint-rule`` (b), the sibling convention, for the same reason.

    At ``eps = 0`` and ``0 < p < 1`` the rule returns ``0`` and ``n``, and
    ``prop:rule-exact`` (ii) proves those ARE the exact quantiles there, so the
    bracket is decided on both sides without a search.
    """
    result = construct(
        AcceptanceRequest(
            alphabet=("c0", "c1"),
            honest={"c0": Fraction(1, 3), "c1": Fraction(2, 3)},
            rounds=7,
            budget=Fraction(0),
            tail_evaluation=TailEvaluation.ENCLOSURE,
        )
    )
    assert result.endpoint_exact is not None
    assert all(row.lower_decided and row.upper_decided for row in result.endpoint_exact)
    interval = result.intervals[0]
    assert interval is not None
    assert (interval.k_lower, interval.k_upper) == (0, 7)
