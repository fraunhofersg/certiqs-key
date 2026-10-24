"""Hypothesis properties over the two endpoint rules.

Every property here is a CLAUSE OF A CLAIM quantified over its own hypothesis,
which is what the frozen cases cannot be: a case is one point, and these are
universal statements. Nothing generated makes a mathematical claim -- the
inputs are arbitrary admissible ones and the contract is required to hold on
all of them.

    def:endpoint-rule (a)      every rule's endpoints meet their budgets
    def:endpoint-rule (b), (c) the two conventions, on every rule
    lem:guard (i)              the ordering chain, hence honest containment
    prop:rule-bernstein (ii)   monotone in the allocation
    prop:rule-bernstein (iii)  the half-width decreases in n, and the interval
                               is never narrower than the exact quantiles'
    prop:bracketed-endpoints (i)  the enclosure box contains the sweep's
    prop:bracketed-endpoints (ii) equal where the bracket is decided
    thm:completeness-bound / rem:epsstar      the reported figure is at least the exact
                               epsilon-star of the route's OWN set, and at most
                               the budget, on all four routes

ONE PROPERTY IS ASSERTED CONDITIONALLY AND SAYS SO: the enclosure evaluation is
NOT claimed monotone in the allocation (``binomial-box/interface.yaml``,
``rule_table``), and what is checked is the condition
``rem:local-evaluation`` names -- that where the certified set is an up-set of
the index range, the bisection returns its least element, and the evaluation is
then monotone. A failure of the unconditional statement would not be a defect;
a failure of the conditional one would.

THE ROUND COUNTS ARE SMALL ON PURPOSE. These properties are about the rules,
not about scale, and the exact sweep is the witness for every one of them; the
scale claim is the slow test
``tests/golden/test_statistics_scaling_slow.py``.
"""

from __future__ import annotations

import itertools
from dataclasses import fields
from fractions import Fraction

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from certiqs_key.statistics import (
    AcceptanceRequest,
    BernsteinParameters,
    EnclosureParameters,
    EndpointRuleName,
    TailEvaluation,
    construct,
    extremal_endpoints,
    guarded_endpoints,
    lower_tail,
    resolve_rule,
    upper_tail,
)

_ZERO = Fraction(0)
_ONE = Fraction(1)

ROUTES = (
    (EndpointRuleName.EXACT, TailEvaluation.SWEEP),
    (EndpointRuleName.EXACT, TailEvaluation.ENCLOSURE),
    (EndpointRuleName.BERNSTEIN, TailEvaluation.SWEEP),
    (EndpointRuleName.BERNSTEIN, TailEvaluation.ENCLOSURE),
)


@st.composite
def masses(draw: st.DrawFn) -> Fraction:
    """Return a rational honest mass in ``[0, 1]``, the two ends included."""
    denominator = draw(st.integers(min_value=1, max_value=16))
    numerator = draw(st.integers(min_value=0, max_value=denominator))
    return Fraction(numerator, denominator)


@st.composite
def budgets(draw: st.DrawFn) -> Fraction:
    """Return a rational budget in ``[0, 1)``, zero included."""
    denominator = draw(st.integers(min_value=2, max_value=64))
    numerator = draw(st.integers(min_value=0, max_value=denominator - 1))
    return Fraction(numerator, denominator)


@st.composite
def settings_of(draw: st.DrawFn) -> tuple[int, Fraction, Fraction, Fraction]:
    """Return ``(n, p, eps^-, eps^+)`` in the input domain."""
    rounds = draw(st.integers(min_value=1, max_value=24))
    honest = draw(masses())
    lower = draw(budgets())
    upper = draw(budgets())
    return rounds, honest, lower, upper


@pytest.mark.contract
@pytest.mark.parametrize("route", ROUTES, ids=lambda r: f"{r[0]}-{r[1]}")
@given(case=settings_of())
@settings(max_examples=60, deadline=None)
def test_every_rule_meets_its_budgets_and_the_ordering_chain(
    route: tuple[EndpointRuleName, TailEvaluation],
    case: tuple[int, Fraction, Fraction, Fraction],
) -> None:
    """``def:endpoint-rule`` (a) and ``lem:guard`` (i)-(ii), on every route.

    The tails are evaluated by the SWEEP whatever the route, because the point
    is that the rule's endpoints meet the budgets of the true binomial law and
    not of whatever the rule used to find them.
    """
    rounds, honest, eps_lower, eps_upper = case
    rule = resolve_rule(*route)
    endpoints = rule.endpoints(rounds, honest, eps_lower, eps_upper)
    assert 0 <= endpoints.lower <= rounds
    assert 0 <= endpoints.upper <= rounds
    assert lower_tail(rounds, honest, endpoints.lower).upper <= eps_lower
    assert upper_tail(rounds, honest, endpoints.upper).upper <= eps_upper
    # lem:guard (i): the guarded endpoints straddle the honest value.
    low, high = guarded_endpoints(rounds, honest, endpoints.lower, endpoints.upper)
    assert 0 <= low <= rounds * honest <= high <= rounds
    # lem:guard (ii): the guarded endpoints meet the budgets too.
    assert lower_tail(rounds, honest, low).upper <= eps_lower
    assert upper_tail(rounds, honest, high).upper <= eps_upper


@pytest.mark.contract
@pytest.mark.parametrize("route", ROUTES, ids=lambda r: f"{r[0]}-{r[1]}")
@given(
    rounds=st.integers(min_value=1, max_value=24),
    eps_lower=budgets(),
    eps_upper=budgets(),
    honest=masses(),
)
@settings(max_examples=60, deadline=None)
def test_the_two_conventions_hold_on_every_rule(
    route: tuple[EndpointRuleName, TailEvaluation],
    rounds: int,
    eps_lower: Fraction,
    eps_upper: Fraction,
    honest: Fraction,
) -> None:
    """``def:endpoint-rule`` (b) and (c), which are REQUIREMENTS on every rule.

    They are what make ``thm:monotonicity-limits`` (iii) and (vi) and ``rem:epsstar``
    hold for every rule rather than for the exact one alone.
    """
    rule = resolve_rule(*route)
    # (c) degenerate mass, for EVERY budget.
    assert rule.endpoints(rounds, _ZERO, eps_lower, eps_upper).lower == 0
    assert rule.endpoints(rounds, _ZERO, eps_lower, eps_upper).upper == 0
    assert rule.endpoints(rounds, _ONE, eps_lower, eps_upper).lower == rounds
    assert rule.endpoints(rounds, _ONE, eps_lower, eps_upper).upper == rounds
    # (b) zero budget, at 0 < p < 1.
    if _ZERO < honest < _ONE:
        zero_side = rule.endpoints(rounds, honest, _ZERO, _ZERO)
        assert zero_side.lower == 0
        assert zero_side.upper == rounds


@pytest.mark.contract
@given(
    rounds=st.integers(min_value=1, max_value=40),
    honest=masses(),
    first=budgets(),
    second=budgets(),
)
@settings(max_examples=120, deadline=None)
def test_the_bernstein_rule_is_monotone_in_the_allocation(
    rounds: int, honest: Fraction, first: Fraction, second: Fraction
) -> None:
    """``prop:rule-bernstein`` (ii), UNCONDITIONALLY.

    "eps^- -> R^- non-decreasing and eps^+ -> R^+ non-increasing", which is the
    hypothesis ``thm:monotonicity-limits`` (i) and (ii) read, and which the bare
    integer-square-root rounding does not give: the grid of
    ``lem:log-enclosure``'s iteration is what restores it.
    """
    low, high = sorted((first, second))
    rule = resolve_rule(EndpointRuleName.BERNSTEIN, TailEvaluation.SWEEP)
    at_low = rule.endpoints(rounds, honest, low, low)
    at_high = rule.endpoints(rounds, honest, high, high)
    assert at_low.lower <= at_high.lower
    assert at_low.upper >= at_high.upper


@pytest.mark.contract
@given(
    rounds=st.integers(min_value=1, max_value=20),
    honest=masses(),
    first=budgets(),
    second=budgets(),
)
@settings(max_examples=60, deadline=None)
def test_the_enclosure_is_monotone_where_the_certified_set_is_an_up_set(
    rounds: int, honest: Fraction, first: Fraction, second: Fraction
) -> None:
    """The CONDITIONAL statement of ``rem:local-evaluation``, and only that.

    Monotonicity in the allocation is NOT claimed for this route
    (``rule_table``), and this test does not assert it. What it asserts is the
    condition the remark names: where the bisection returns the LEAST certified
    index -- which it does exactly when the certified set is an up-set of the
    index range -- the evaluation is monotone, because the certified set grows
    with the budget when the logarithm of the budget is enclosed monotonically,
    as the grid root bounds are. The up-set property is checked directly, on
    the indices the two searches returned.
    """
    low, high = sorted((first, second))
    rule = resolve_rule(EndpointRuleName.EXACT, TailEvaluation.ENCLOSURE)
    at_low = rule.endpoints(rounds, honest, low, low)
    at_high = rule.endpoints(rounds, honest, high, high)
    from certiqs_key.statistics import certify_upper
    from certiqs_key.statistics.enclosure import (
        DEFAULT_ENCLOSURE_PARAMETERS,
        Verdict,
    )

    if honest in (_ZERO, _ONE) or low == _ZERO:
        # The conventions answer both, and they are asserted elsewhere.
        return
    certified_high = [
        certify_upper(rounds, honest, index, high, DEFAULT_ENCLOSURE_PARAMETERS)
        is Verdict.CERTIFIED_ADMISSIBLE
        for index in range(rounds + 1)
    ]
    is_up_set = all(
        later or not earlier
        for earlier, later in itertools.pairwise(certified_high)
    )
    if is_up_set:
        assert at_low.upper >= at_high.upper


@pytest.mark.contract
@given(
    rounds=st.integers(min_value=1, max_value=30),
    honest=masses(),
    eps_lower=budgets(),
    eps_upper=budgets(),
)
@settings(max_examples=120, deadline=None)
def test_the_bernstein_interval_contains_the_exact_quantile_interval(
    rounds: int, honest: Fraction, eps_lower: Fraction, eps_upper: Fraction
) -> None:
    """``prop:rule-bernstein`` (iii), last sentence.

    The exact rule's quantiles are the EXTREMAL admissible indices
    (``prop:rule-exact`` (iii)) and the Bernstein endpoints are admissible by
    its (i), so the Bernstein interval contains the quantile interval. The
    sweep is the witness and shares no step with the closed form.
    """
    rule = resolve_rule(EndpointRuleName.BERNSTEIN, TailEvaluation.SWEEP)
    endpoints = rule.endpoints(rounds, honest, eps_lower, eps_upper)
    kappa_lower, kappa_upper, exact = extremal_endpoints(
        rounds, honest, eps_lower, eps_upper
    )
    assert exact is True
    assert endpoints.lower <= kappa_lower
    assert endpoints.upper >= kappa_upper


@pytest.mark.contract
@given(
    honest=st.sampled_from(
        [Fraction(1, 2), Fraction(1, 3), Fraction(2, 5), Fraction(7, 8)]
    ),
    budget=st.sampled_from([Fraction(1, 8), Fraction(1, 32), Fraction(1, 128)]),
    start=st.integers(min_value=2, max_value=40),
)
@settings(max_examples=40, deadline=None)
def test_the_bernstein_half_width_decreases_in_n(
    honest: Fraction, budget: Fraction, start: int
) -> None:
    """``prop:rule-bernstein`` (iii): ``t(L)/n`` is strictly decreasing in ``n``.

    Asserted on the FREQUENCY half-width ``t/n``, which is the quantity the
    clause is about and the one a consumer sweeping ``n`` sees; the emitted
    endpoint is an integer and is not itself monotone, the floor and the
    ceiling being step functions.
    """
    from certiqs_key.statistics.bernstein import (
        DEFAULT_BERNSTEIN_PARAMETERS,
        bernstein_deviation,
        budget_term,
    )

    term = budget_term(budget, DEFAULT_BERNSTEIN_PARAMETERS)
    widths = []
    for rounds in (start, 2 * start, 4 * start):
        variance = rounds * honest * (_ONE - honest)
        deviation = bernstein_deviation(variance, term, DEFAULT_BERNSTEIN_PARAMETERS)
        widths.append(Fraction(deviation, rounds))
    assert widths[0] > widths[1] > widths[2] > _ZERO


@pytest.mark.contract
@pytest.mark.parametrize("route", ROUTES, ids=lambda r: f"{r[0]}-{r[1]}")
@given(
    rounds=st.integers(min_value=1, max_value=16),
    honest=masses(),
    budget=budgets(),
)
@settings(max_examples=40, deadline=None)
def test_the_reported_figure_bounds_its_own_sets_epsilon_star(
    route: tuple[EndpointRuleName, TailEvaluation],
    rounds: int,
    honest: Fraction,
    budget: Fraction,
) -> None:
    """``thm:completeness-bound`` and ``rem:epsstar``, on all four routes.

    The report is at least the EXACT ``epsilon_star`` OF THE SET THE ROUTE
    EMITTED -- the sum of the two binomial tails at the emitted guarded
    endpoints -- and at most ``ecomp``. The first half is the direction a
    conservative evaluation (``def:conservative-evaluation``) licenses and is
    the one that would break completeness if inverted; the second is the
    declared output domain.

    THE FIGURES OF TWO ROUTES ARE NOT COMPARABLE WITH EACH OTHER, and this test
    does not compare them: a wider box has a smaller honest failure
    probability, so an enclosure route's figure may be below the sweep's.
    """
    rule, evaluation = route
    request = AcceptanceRequest(
        alphabet=("c0", "c1"),
        honest={"c0": honest, "c1": _ONE - honest},
        rounds=rounds,
        budget=budget,
        constrained=("c0",),
        endpoint_rule=rule,
        tail_evaluation=evaluation,
    )
    result = construct(request)
    assert result.acceptance_set is not None
    assert result.completeness_certified is not None
    assert _ZERO <= result.completeness_certified <= budget
    interval = result.intervals[0]
    assert interval is not None
    exact_star = (
        lower_tail(rounds, honest, interval.k_lower).value
        + upper_tail(rounds, honest, interval.k_upper).value
    )
    assert result.completeness_certified >= min(budget, exact_star)


@pytest.mark.contract
@given(
    rounds=st.integers(min_value=1, max_value=24),
    honest=masses(),
    eps_lower=budgets(),
    eps_upper=budgets(),
)
@settings(max_examples=80, deadline=None)
def test_the_enclosure_box_contains_the_sweeps_and_equals_it_when_decided(
    rounds: int, honest: Fraction, eps_lower: Fraction, eps_upper: Fraction
) -> None:
    """``prop:bracketed-endpoints`` (i) and (ii), over the input domain.

    (i) is unconditional: every ``q^-`` is at most and every ``q^+`` at least
    the exact rule's, so the emitted box CONTAINS the sweep's. (ii) is the
    conditional half, and it is asserted exactly where its hypothesis holds.
    """
    sweep = resolve_rule(EndpointRuleName.EXACT, TailEvaluation.SWEEP).endpoints(
        rounds, honest, eps_lower, eps_upper
    )
    enclosure = resolve_rule(
        EndpointRuleName.EXACT, TailEvaluation.ENCLOSURE
    ).endpoints(rounds, honest, eps_lower, eps_upper)
    assert enclosure.lower <= sweep.lower
    assert enclosure.upper >= sweep.upper
    if enclosure.upper_decided:
        assert enclosure.upper == sweep.upper
    if enclosure.lower_decided:
        assert enclosure.lower == sweep.lower


@pytest.mark.contract
@pytest.mark.parametrize("route", ROUTES, ids=lambda r: f"{r[0]}-{r[1]}")
def test_the_record_names_every_parameter_the_figure_depends_on(
    route: tuple[EndpointRuleName, TailEvaluation],
) -> None:
    """Every parameter the route reads is a name in the record.

    ``interface.yaml``, ``outputs.honest_model``: the record exists so that a
    reader can tell what produced the number. THE LIST IS THE UNION of the
    rule's own parameters and the enclosure parameters in force wherever the
    evaluation is ``enclosure`` -- including on ``bernstein`` + ``enclosure``,
    where the endpoints are the Bernstein rule's and the FIGURE is the sum of
    the two enclosure upper bounds at the guarded endpoints
    (``completeness_report``, its fourth row). A record that listed
    only the Bernstein pair there would hide the enclosure parameters.

    EACH NAME CARRIES THE INTERFACE BLOCK IT COMES FROM, because the two blocks
    each declare a ``root_exponent_j`` and a ``root_precision_bits`` and on
    that one route the two carry different values.

    WHAT IS ASSERTED IS THE PROPERTY THE NAME STATES -- COVERAGE, not a list.
    A test that named three of the seven enclosure rows would pass while
    ``window_precision`` was recorded nowhere, a field that moves the emitted
    BOX at six bits. The
    assertion is therefore against :func:`dataclasses.fields` of the parameter
    objects actually in force: one recorded name per field, and the recorded
    VALUES equal to the field values, on parameter objects whose fields are
    pairwise distinct so that a duplicated row cannot stand in for a missing
    one. A field added to either dataclass and not recorded fails here.
    """
    rule, evaluation = route
    # Pairwise-distinct values, so that the multiset of recorded values pins
    # the mapping and not merely its size. Coarse, and every route stays
    # admissible at any setting (prop:bracketed-endpoints (i)).
    enclosure = EnclosureParameters(
        root_exponent=9,
        root_precision=17,
        wallis_length=33,
        window_start=5,
        window_cap=65,
        window_target_bits=7,
        window_precision=19,
    )
    bernstein = BernsteinParameters(root_exponent=11, root_precision=23)
    result = construct(
        AcceptanceRequest(
            alphabet=("c0", "c1"),
            honest={"c0": Fraction(1, 4), "c1": Fraction(3, 4)},
            rounds=30,
            budget=Fraction(1, 10),
            endpoint_rule=rule,
            tail_evaluation=evaluation,
        ),
        enclosure,
        bernstein,
    )
    assert result.honest_model is not None
    recorded = result.honest_model.evaluation_parameters
    names = {name for name, _ in recorded}
    # A NAME IS NEVER AMBIGUOUS: the record is a mapping, not a bag.
    assert len(names) == len(recorded)

    expected: dict[str, tuple[object, ...]] = {}
    if evaluation is TailEvaluation.ENCLOSURE:
        expected["the_enclosure_route"] = tuple(
            getattr(enclosure, field.name) for field in fields(enclosure)
        )
    if rule is EndpointRuleName.BERNSTEIN:
        expected["the_bernstein_rule"] = tuple(
            getattr(bernstein, field.name) for field in fields(bernstein)
        )
    for block, values in expected.items():
        block_rows = [
            value for name, value in recorded if name.startswith(f"{block}.")
        ]
        assert len(block_rows) == len(values), block
        assert sorted(block_rows) == sorted(values), block
    # AND NOTHING ELSE IS RECORDED: the union is the whole of it, so on
    # exact + sweep -- no enclosure evaluated, and the sweep takes no parameter
    # of its own -- the honest record is the empty one.
    assert len(recorded) == sum(len(values) for values in expected.values())
