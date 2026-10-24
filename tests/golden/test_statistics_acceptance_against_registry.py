"""``statistics-acceptance`` against its FROZEN registry -- all fifty-five cases.

``tests/oracles/registry_statistics_acceptance.py`` is the authority here and
this implementation is what is on trial. Every value in it was derived BY HAND
from the accepted ``contract.tex`` 0.1.2, re-checked by an independent exact
route, and committed by a DIFFERENT implementer instance before
``src/certiqs_key/statistics/`` existed at all (the freeze rule). A disagreement is a
finding against this code, never
against the registry, and no expected value may be edited to make a test green.

WHAT IS COVERED, AND IT IS EVERY CASE THE REGISTRY FREEZES
==========================================================
    6  BINOMIAL_TAIL_CASES          SA2, both tail forms at every k
    8  GEOMETRY_VALIDATION_CASES    SA1, both predicates and the witness
    7  GUARD_CASES                  SA3, both regimes of Remark rem:guard
   12  CONSTRUCTION_CASES           SA4, SA5, SA1, SA7 -- Acc end to end
    6  BOX_MINIMUM_CASES            SA8 (ii)-(iii), all three fill regimes
    7  SINGLETON_CASES              SA9, both degenerate routes
    9  INPUT_DOMAIN_VIOLATION_CASES SA6 (iii), one input per code
   --
   55

THREE FROZEN COLUMNS ARE ASSERTED AS THINGS THIS MODULE MUST **NOT** PRODUCE.
``tight_lower`` / ``tight_upper`` are the denoted set's exact coordinate ranges
and ``minimal_support`` is the union of the supports over it. The registry
records them APART from the emitted columns and says why: Remark
``rem:selector`` requires the RAW bounds to be emitted, so "an implementation
that tightens the emitted bounds emits a different artifact", and Theorem
``thm:box-oracle`` (i) claims minimality for the ``singleton`` tag alone. The tests
below therefore assert that the emitted box DIFFERS from the tight one exactly
where the registry says it does.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from registry_statistics_acceptance import (
    BINOMIAL_TAIL_CASES,
    BOX_MINIMUM_CASES,
    CONSTRUCTION_CASES,
    GEOMETRY_VALIDATION_CASES,
    GUARD_CASES,
    INPUT_DOMAIN_VIOLATION_CASES,
    REASON_CODES,
    SINGLETON_CASES,
    BinomialTailCase,
    BoxMinimumCase,
    ConstructionCase,
    GeometryValidationCase,
    GuardCase,
    InputDomainViolationCase,
    SingletonCase,
)
from statistics_requests import request_of

from certiqs_key.statistics import (
    AcceptanceRequest,
    BudgetAllocation,
    GeometryDefect,
    InfeasibilityReason,
    PolytopeGeometry,
    SingletonGeometry,
    binomial_cdf,
    binomial_pmf,
    box_minimum,
    box_witness_point,
    canonical_box,
    construct,
    lower_tail,
    outcome_interval,
    regularized_incomplete_beta,
    singleton_completeness,
    upper_tail,
    validate_geometry,
)


def geometry_of(case: GeometryValidationCase) -> SingletonGeometry | PolytopeGeometry:
    """Return the frozen declared geometry as this module's record."""
    if case.tag == "singleton":
        assert case.q_star is not None
        return SingletonGeometry(case.outcomes, case.q_star)
    assert case.box_bounds is not None
    lower, upper = case.box_bounds
    return canonical_box(case.outcomes, lower, upper)


# ---------------------------------------------------------------------------
#  SA2 -- the exact binomial tails
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", BINOMIAL_TAIL_CASES, ids=lambda c: c.case_id)
def test_the_frozen_mass_and_tail_tables_are_reproduced(case: BinomialTailCase) -> None:
    """Theorem thm:binomial-tails and Eq. eq:tails-used, at every k of every frozen table."""  # noqa: E501
    for count in range(case.n + 1):
        expected = Fraction(case.pmf_numerators[count], case.denominator)
        assert binomial_pmf(case.n, case.p, count) == expected, count
        cdf = binomial_cdf(case.n, case.p, count)
        assert cdf.exact is True
        assert cdf.value == Fraction(case.cdf_numerators[count], case.denominator)
        above = upper_tail(case.n, case.p, count)
        assert above.exact is True
        assert above.value == Fraction(
            case.upper_tail_numerators[count], case.denominator
        )
    for count in range(case.n + 2):
        below = lower_tail(case.n, case.p, count)
        assert below.exact is True
        assert below.value == Fraction(
            case.lower_tail_numerators[count], case.denominator
        )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", BINOMIAL_TAIL_CASES, ids=lambda c: c.case_id)
def test_the_beta_route_agrees_with_the_summation_route(case: BinomialTailCase) -> None:
    """Theorem thm:binomial-tails itself: the two closed forms are the same function.

    Eq. eq:uppertail, ``Pr[N >= k] = I_p(k, n-k+1)``, checked at every ``k``
    the equation is stated for. The registry's own ``beta_cross_check`` does one
    ``k`` per table by hand; this does all of them, by a route that shares no
    step with the mass-point sum -- :func:`regularized_incomplete_beta`
    integrates the polynomial and normalizes by ``B(a, b)``.
    """
    for count in range(1, case.n + 1):
        frozen = Fraction(case.upper_tail_numerators[count - 1], case.denominator)
        assert regularized_incomplete_beta(case.p, count, case.n - count + 1) == frozen


# ---------------------------------------------------------------------------
#  SA1 -- the taxonomy, its predicates, and the rational witness
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", GEOMETRY_VALIDATION_CASES, ids=lambda c: c.case_id)
def test_the_validation_predicate_agrees_with_the_frozen_verdict(
    case: GeometryValidationCase,
) -> None:
    """Theorem thm:geometry-validation (ii)-(iii), on all eight declared geometries."""
    verdict = validate_geometry(geometry_of(case))
    assert verdict.admissible is case.predicate_holds
    well_formed = verdict.defect is not GeometryDefect.ILL_FORMED
    assert well_formed is case.well_formed
    if not case.well_formed:
        # ILLFORMED-box-inverted: the closed form Eq. eq:boxfeas would PASS on
        # this data, and the refusal must not come from it. The frozen case
        # exists to expose exactly that trap.
        assert case.box_sums is not None
        assert case.box_sums[0] <= 1 <= case.box_sums[1]


#: The declared geometries the closed form of Theorem thm:geometry-validation (iii)
#: applies to: a canonical box, i.e. one whose data satisfies ``0 <= q^- <= q^+``. The
#: inverted box is excluded here because the closed form is proved UNDER that
#: hypothesis and says nothing outside it -- which is the whole point of that
#: case, and is asserted where it belongs, in the validation test above.
WELL_FORMED_BOX_CASES = tuple(
    case
    for case in GEOMETRY_VALIDATION_CASES
    if case.box_bounds is not None and case.well_formed
)

#: Every declared geometry carrying box data, well formed or not.
DECLARED_BOX_CASES = tuple(
    case for case in GEOMETRY_VALIDATION_CASES if case.box_bounds is not None
)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", WELL_FORMED_BOX_CASES, ids=lambda c: c.case_id)
def test_the_rational_interpolation_witness_is_reproduced(
    case: GeometryValidationCase,
) -> None:
    """Theorem thm:geometry-validation (iii), the (<=) direction, and BOTH branches of the formula.

    ``VALID-box-interior`` exercises the general branch and
    ``VALID-box-both-sums-equal-one`` the degenerate one, whose denominator
    ``sum q^+ - sum q^-`` vanishes -- the box ``ACC-degenerate-honest-mass``
    actually emits. The two INVALID boxes are here too, and there the witness is
    ``None``: there is no point to exhibit.
    """  # noqa: E501
    assert case.box_bounds is not None
    lower, upper = case.box_bounds
    witness = box_witness_point(lower, upper)
    assert witness == case.witness_point
    if witness is not None:
        assert sum(witness) == 1
        for low, value, high in zip(lower, witness, upper, strict=True):
            assert low <= value <= high


# ---------------------------------------------------------------------------
#  SA3 -- the interval, the guard, and both regimes of Remark rem:guard
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", GUARD_CASES, ids=lambda c: c.case_id)
def test_every_frozen_guard_field_is_reproduced(case: GuardCase) -> None:
    """Definition def:interval and Theorem thm:sa3, field for field.

    Both regimes Remark ``rem:guard`` separates are among these seven and the
    registry insists they be read apart: the ``lo1``/``up1`` pair (cost above
    one count) fails only at a near-unit single-tail budget, while the
    ``lo0``/``up0`` pair (guard active at all) fails AT ORDINARY BUDGETS UNDER
    THE DEFAULT UNIFORM RULE -- including at ``n = 10^6``, where the exact tail
    has some ten million digits and the registry deliberately freezes none.
    """
    interval = outcome_interval(case.n, case.p, case.eps_lower, case.eps_upper)
    assert interval.kappa_lower == case.kappa_lower
    assert interval.kappa_upper == case.kappa_upper
    assert interval.k_lower == case.k_lower
    assert interval.k_upper == case.k_upper
    assert interval.floor_np == case.floor_np
    assert interval.ceil_np == case.ceil_np
    assert interval.lower_enlargement == case.lower_enlargement
    assert interval.upper_enlargement == case.upper_enlargement
    assert interval.guard_lo0_holds is case.guard_lo0_holds
    assert interval.guard_lo1_holds is case.guard_lo1_holds
    assert interval.guard_up0_holds is case.guard_up0_holds
    assert interval.guard_up1_holds is case.guard_up1_holds
    assert interval.distance_below_p == case.distance_below_p
    assert interval.distance_above_p == case.distance_above_p


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", GUARD_CASES, ids=lambda c: c.case_id)
def test_the_evaluation_route_matches_what_the_registry_could_freeze(
    case: GuardCase,
) -> None:
    """``tails_frozen`` is the registry's account of which route the case needs.

    A case whose exact tails the registry could write down is one this module
    evaluates exactly; the one case it could not -- ``n = 10^6``, ``p = 10^-9``,
    whose determination "rests on the rigorous inequality" -- is the one this
    module decides by enclosure. The two accounts are independent: the registry
    fixed its flag by hand from the size of the number, and this module fixes
    its own from :data:`~certiqs_key.statistics.tails.EXACT_TAIL_BIT_BUDGET`.
    """
    interval = outcome_interval(case.n, case.p, case.eps_lower, case.eps_upper)
    assert interval.tails_exact is case.tails_frozen


# ---------------------------------------------------------------------------
#  SA4, SA5, SA6, SA7 -- the construction map, end to end
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_the_emitted_canonical_box_is_reproduced(case: ConstructionCase) -> None:
    """Definition def:construction and Theorem thm:box-construction, on all twelve runs."""  # noqa: E501
    result = construct(request_of(case))
    assert result.infeasibility_report is None
    box = result.acceptance_set
    assert box is not None
    assert box.tag == "polytope"
    assert box.box_bounds == (case.box_lower, case.box_upper)
    assert box.m_row == case.m_row
    assert box.rows == case.rows
    assert box.rhs == case.rhs
    # Theorem thm:box-construction (i): every entry of B is in {0, +-1}.
    assert all(value in (0, 1, -1) for row in box.rows for value in row)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_the_emitted_box_is_the_raw_one_and_is_never_tightened(
    case: ConstructionCase,
) -> None:
    """Remark rem:selector: the vacuous bounds are kept, not replaced.

    The frozen ``tight_lower`` / ``tight_upper`` columns are the denoted set's
    exact coordinate ranges, and six of the twelve cases have them strictly
    inside the emitted pair. This asserts the emitted pair is the RAW one in
    every case, and that on those six it is NOT the tight one -- the emitted box
    and the tightened box have the same denotation, which is exactly why
    substituting one for the other is tempting and why the registry freezes them
    apart.
    """
    result = construct(request_of(case))
    box = result.acceptance_set
    assert box is not None
    assert box.box_bounds == (case.box_lower, case.box_upper)
    tight = (case.tight_lower, case.tight_upper)
    if tight != (case.box_lower, case.box_upper):
        assert box.box_bounds != tight


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_honest_containment_and_non_emptiness(case: ConstructionCase) -> None:
    """Theorems thm:box-construction (iii) and thm:honest-containment (i), unconditionally on all twelve."""  # noqa: E501
    result = construct(request_of(case))
    box = result.acceptance_set
    assert box is not None
    assert box.box_bounds is not None
    lower, upper = box.box_bounds
    for low, honest, high in zip(lower, case.honest, upper, strict=True):
        assert low <= honest <= high
    assert case.honest_contained is True
    assert (sum(lower), sum(upper)) == case.box_sums
    assert sum(lower) <= 1 <= sum(upper)
    assert validate_geometry(box).admissible is True


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_the_acceptance_support_is_the_cap_positivity_set(
    case: ConstructionCase,
) -> None:
    """Theorem thm:box-oracle (i) and the Outputs-table formula, on all twelve.

    ``ACC-support-superset`` is the case that matters: the emitted support
    STRICTLY CONTAINS the union of the supports over the denoted set, which is
    conforming, and this test asserts the emitted one rather than the minimal
    one is what comes back.
    """
    result = construct(request_of(case))
    assert result.acceptance_support == case.acceptance_support
    if set(case.minimal_support) < set(case.acceptance_support):
        assert result.acceptance_support != case.minimal_support


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_epsilon_star_is_reproduced_and_stays_in_its_declared_domain(
    case: ConstructionCase,
) -> None:
    """Theorem thm:completeness-bound, Eq. eq:completeness, and the Outputs-table domain.

    The frozen ``true_failure_probability`` column is asserted as a BOUND and
    never as the reported figure: ``epsilon_star`` is DEFINED as the sum of the
    ``2|Chat_con|`` tails, and on a two-letter alphabet with ``Chat_con = Chat``
    that union bound double-counts by exactly a factor of two. Reporting the
    larger figure is the contracted output; reading it as the failure
    probability is the misreading the registry freezes three cases against.
    """  # noqa: E501
    result = construct(request_of(case))
    assert result.completeness_certified == case.epsilon_star
    assert result.completeness_exact is True
    assert 0 <= case.epsilon_star <= case.ecomp
    assert case.true_failure_probability <= case.epsilon_star


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_the_chebyshev_half_width_bound_holds_on_every_emitted_box(
    case: ConstructionCase,
) -> None:
    """Theorem thm:monotonicity-limits (iv), Eq. eq:width -- the frozen O-SA-WIDTH-BOUND entry.

    The registry freezes this bound in SQUARED FORM because the square root is
    "the only irrational quantity anywhere in this contract", and the squared
    form is equivalent once ``1/n`` is moved across:

        (q^+(chat) - p - 1/n)^2 <= p(1-p) / (n eps^+(chat))

    whenever ``q^+(chat) - p >= 1/n``, and trivially otherwise; symmetrically
    below. The ``1/n`` term is not decoration -- it absorbs the ceiling in the
    upper proof and the floor, clipped branch included, in the lower one -- so
    both the zero-deviation instances and the ``1/8``-deviation ones are
    exercised here.
    """  # noqa: E501
    result = construct(request_of(case))
    box = result.acceptance_set
    assert box is not None
    assert box.box_bounds is not None
    lower, upper = box.box_bounds
    shares = dict(
        zip(
            case.constrained,
            zip(case.eps_lower, case.eps_upper, strict=True),
            strict=True,
        )
    )
    step = Fraction(1, case.rounds)
    for outcome, honest, low, high in zip(
        case.outcomes, case.honest, lower, upper, strict=True
    ):
        # Theorem thm:monotonicity-limits (iv) is stated for chat in Chat_con with
        # 0 < p^hon(chat) < 1 and a POSITIVE tail budget.
        if outcome not in shares or not 0 < honest < 1:
            continue
        eps_lower, eps_upper = shares[outcome]
        variance = honest * (1 - honest)
        if eps_upper > 0 and high - honest >= step:
            assert (high - honest - step) ** 2 <= variance / (case.rounds * eps_upper)
        if eps_lower > 0 and honest - low >= step:
            assert (honest - low - step) ** 2 <= variance / (case.rounds * eps_lower)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_the_honest_model_record_carries_the_five_items(
    case: ConstructionCase,
) -> None:
    """Section 2.2: completeness is meaningful only relative to this record.

    The allocation it carries is the RESOLVED one, so where the case declares
    the ``uniform-default`` rule this checks the rule's own output against the
    frozen ``eps_lower`` / ``eps_upper`` columns.
    """
    result = construct(request_of(case))
    model = result.honest_model
    assert model is not None
    assert model.tag == "iid_honest_rounds"
    assert model.honest_distribution == case.honest
    assert model.rounds == case.rounds
    assert model.constrained_outcomes == case.constrained
    assert tuple(model.budget_allocation.lower) == case.eps_lower
    assert tuple(model.budget_allocation.upper) == case.eps_upper


@pytest.mark.contract
@pytest.mark.oracle
def test_the_budget_monotone_pair_is_nested_and_the_n_pair_is_not() -> None:
    """Theorem thm:monotonicity-limits (i) against (v), on the two frozen pairs.

    A LARGER BUDGET BUYS A SMALLER SET, strictly at all four endpoints; more
    ROUNDS can buy a larger one. Both are computed here rather than read off the
    registry's columns, so the direction is the implementation's.
    """
    cases = {case.case_id: case for case in CONSTRUCTION_CASES}
    small = construct(request_of(cases["ACC-normal-2letter"])).acceptance_set
    large = construct(request_of(cases["ACC-budget-large"])).acceptance_set
    assert small is not None and large is not None
    assert small.box_bounds is not None and large.box_bounds is not None
    for index in range(2):
        assert small.box_bounds[0][index] < large.box_bounds[0][index]
        assert large.box_bounds[1][index] < small.box_bounds[1][index]
    two = construct(request_of(cases["ACC-n2-singleton"])).acceptance_set
    three = construct(request_of(cases["ACC-n3-wider"])).acceptance_set
    assert two is not None and three is not None
    assert two.box_bounds is not None and three.box_bounds is not None
    # The n = 2 set is a single point strictly inside the n = 3 set.
    assert three.box_bounds[0][0] < two.box_bounds[0][0]
    assert two.box_bounds[1][0] < three.box_bounds[1][0]


# ---------------------------------------------------------------------------
#  SA8 (ii)-(iii) -- the closed-form minimum and its tight witness
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", BOX_MINIMUM_CASES, ids=lambda c: c.case_id)
def test_the_closed_form_box_minimum_is_reproduced(case: BoxMinimumCase) -> None:
    """Theorem thm:box-oracle (ii)-(iii), every frozen field, all three fill regimes."""
    geometry = canonical_box(case.outcomes, case.box_lower, case.box_upper)
    assert geometry.rhs == case.rhs
    minimum = box_minimum(geometry, case.g)
    assert minimum is not None
    assert minimum.sorted_order == case.sorted_order
    assert minimum.residual_r == case.residual_r
    assert minimum.widths == case.widths
    assert minimum.j_star == case.j_star
    assert minimum.fill_increment == case.fill_increment
    assert minimum.q_opt == case.q_opt
    assert minimum.minimum == case.minimum
    assert minimum.lam == case.lam
    assert minimum.dual_v == case.dual_v
    assert minimum.dual_u == case.dual_u
    assert minimum.dual_feasibility == case.dual_feasibility
    assert minimum.dual_value == case.dual_value
    # Eq. eq:dualfeas holds with EQUALITY, which is why the bound is tight.
    assert all(value == 0 for value in minimum.dual_feasibility)
    assert minimum.dual_value == minimum.minimum


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", BOX_MINIMUM_CASES, ids=lambda c: c.case_id)
def test_every_frozen_minimizer_is_feasible_and_attains_the_minimum(
    case: BoxMinimumCase,
) -> None:
    """The frozen ``minimizers`` column, including the tie's second vertex.

    ``PMIN-tie-in-g`` freezes TWO minimizers and ONE minimum: the tie-break is
    free and the value is not. This module sorts stably, so it returns the
    declaration-order vertex; the other is asserted to have the same value,
    which is the statement the contract makes.
    """
    for point in case.minimizers:
        assert sum(point) == 1
        for low, value, high in zip(case.box_lower, point, case.box_upper, strict=True):
            assert low <= value <= high
        paired = sum(
            weight * value for weight, value in zip(case.g, point, strict=True)
        )
        assert paired == case.minimum


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", DECLARED_BOX_CASES, ids=lambda c: c.case_id)
def test_no_minimum_is_returned_for_a_box_that_fails_its_predicate(
    case: GeometryValidationCase,
) -> None:
    """Theorem thm:box-oracle (ii) is stated for a NON-EMPTY box, and the fill knows it.

    On ``INVALID-box-floors-above-one`` the residual ``r = -1/5`` is NEGATIVE
    and "the least ``j`` whose prefix width reaches ``r``" is satisfied at the
    first index, so a fill that skips the feasibility test returns a number for
    a set with no points in it. On ``ILLFORMED-box-inverted`` a width is
    NEGATIVE, so the prefix sums are not monotone and "the least index whose
    prefix reaches ``r``" is not the index the exchange argument justifies.
    Both must return nothing instead.
    """
    assert case.box_bounds is not None
    geometry = canonical_box(case.outcomes, *case.box_bounds)
    objective = tuple(Fraction(index) for index in range(len(case.outcomes)))
    result = box_minimum(geometry, objective)
    assert (result is not None) is case.predicate_holds


# ---------------------------------------------------------------------------
#  SA9 -- singleton completeness
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", SINGLETON_CASES, ids=lambda c: c.case_id)
def test_singleton_completeness_is_reproduced(case: SingletonCase) -> None:
    """Theorem thm:singleton-completeness, every frozen field, both degenerate routes included."""  # noqa: E501
    geometry = SingletonGeometry(case.outcomes, case.q_star)
    completeness = singleton_completeness(geometry, case.honest, case.rounds)
    assert completeness.counts_are_integral is case.counts_are_integral
    assert completeness.counts == case.counts
    assert completeness.absolutely_continuous is case.absolutely_continuous
    assert completeness.multinomial_coefficient == case.multinomial_coefficient
    assert completeness.accept_probability == case.accept_probability
    assert completeness.least_admissible_budget == case.least_admissible_budget
    if case.least_admissible_budget is None:
        # The admissible interval is [1, 1) = EMPTY. ecomp = 1 is NOT a
        # substitute: it lies outside the declared domain [0, 1).
        assert "EMPTY" in case.admissible_budget_interval
        assert completeness.admissible_budget_exists is False


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_completeness_routes_agree_on_the_one_set_both_apply_to() -> None:
    """Remark rem:singleton-honest: SA5 and SA9 must agree, and they are not the same.

    ``ACC-n2-singleton`` emits a box whose denotation is the single point
    ``(1/2, 1/2)``, and ``SING-n2-agrees-with-sa5`` is that point read as a
    declared ``singleton``. SA5 reaches ``1/2`` by a union bound over count
    tails and SA9 by an exact multinomial mass; they coincide only because the
    two tail events are disjoint and exhaust the complement of the accept event,
    so the agreement is a coincidence with a reason and not a general identity.
    """
    construction = next(
        case for case in CONSTRUCTION_CASES if case.case_id == "ACC-n2-singleton"
    )
    singleton = next(
        case for case in SINGLETON_CASES if case.case_id == "SING-n2-agrees-with-sa5"
    )
    result = construct(request_of(construction))
    completeness = singleton_completeness(
        SingletonGeometry(singleton.outcomes, singleton.q_star),
        singleton.honest,
        singleton.rounds,
    )
    assert result.completeness_certified == completeness.least_admissible_budget
    assert result.completeness_certified == Fraction(1, 2)


# ---------------------------------------------------------------------------
#  SA6 (iii) -- the nine input-domain violation codes
# ---------------------------------------------------------------------------
#
#  One request per frozen case, built from its `offending_input` field. The
#  cases are named in the registry's order, which is the theorem's order, and
#  the test below asserts that the mapping is onto all nine.


def _base_request(**overrides: object) -> AcceptanceRequest:
    """Return an admissible request with the named fields replaced."""
    fields: dict[str, object] = {
        "alphabet": ("c0", "c1"),
        "honest": {"c0": Fraction(1, 2), "c1": Fraction(1, 2)},
        "rounds": 4,
        "budget": Fraction(1, 2),
        "constrained": ("c0", "c1"),
        "allocation": None,
    }
    fields.update(overrides)
    return AcceptanceRequest(**fields)


VIOLATING_REQUESTS: dict[str, AcceptanceRequest] = {
    # VIOL-alphabet-empty: Chat = (), the empty alphabet.
    "alphabet_empty": _base_request(alphabet=(), honest={}, constrained=()),
    # VIOL-alphabet-not-finite: no finite datum exhibits this, so the argument
    # is an ITERATOR -- an alphabet that cannot be counted without consuming it.
    "alphabet_not_finite": _base_request(alphabet=iter(("c0", "c1"))),
    # VIOL-rounds-zero: n = 0.
    "rounds_out_of_range": _base_request(rounds=0),
    # VIOL-honest-not-normalized: p^hon = (1/2, 1/4), summing to 3/4.
    "honest_not_a_distribution": _base_request(
        honest={"c0": Fraction(1, 2), "c1": Fraction(1, 4)}
    ),
    # VIOL-budget-equal-one: ecomp = 1, the excluded right end.
    "budget_out_of_range": _base_request(budget=Fraction(1)),
    # VIOL-allocation-negative: one negative entry whose SUM is inside the
    # budget, so a check of the sum alone accepts it.
    "allocation_negative": _base_request(
        allocation=BudgetAllocation(
            lower=(Fraction(-1, 10), Fraction(1, 10)),
            upper=(Fraction(1, 10), Fraction(1, 10)),
        )
    ),
    # VIOL-allocation-exceeds-budget: every entry non-negative, sum outside the
    # budget, so a componentwise check alone accepts it.
    "allocation_exceeds_budget": _base_request(
        budget=Fraction(1, 10),
        constrained=("c0",),
        allocation=BudgetAllocation(lower=(Fraction(1, 10),), upper=(Fraction(1, 10),)),
    ),
    # VIOL-selector-not-a-subset: Chat = (c0, c1), Chat_con = (c0, c3).
    "selector_not_a_subset": _base_request(constrained=("c0", "c3")),
    # VIOL-inputs-not-rational: a float presented as if it were the intended
    # value. The registry names 1/sqrt(2) "or any binary floating-point value
    # presented as if exact"; 0.5 is dyadic and exactly representable, so it is
    # deliberately NOT used -- the refusal must not depend on the value.
    "inputs_not_rational": _base_request(honest={"c0": 0.1, "c1": Fraction(9, 10)}),
}


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", INPUT_DOMAIN_VIOLATION_CASES, ids=lambda c: c.case_id)
def test_every_input_domain_violation_emits_its_code_and_no_set(
    case: InputDomainViolationCase,
) -> None:
    """Theorem thm:honest-containment (iii): the code, and NO acceptance_set beside it."""  # noqa: E501
    result = construct(VIOLATING_REQUESTS[case.reason_code])
    report = result.infeasibility_report
    assert report is not None
    assert report.reason == case.reason_code
    assert report.detail.strip()
    # Section 2.2: a report and a set are MUTUALLY EXCLUSIVE. Not a flag on one
    # record -- the failure branch has no acceptance set to read.
    assert result.acceptance_set is None
    assert result.acceptance_support is None
    assert result.completeness_certified is None
    assert result.honest_model is None
    assert case.emits_acceptance_set is False


@pytest.mark.contract
@pytest.mark.oracle
def test_the_nine_codes_are_the_vocabulary_and_nothing_is_added_to_it() -> None:
    """The enum IS Theorem thm:honest-containment (iii)'s enumeration, in its order.

    ``thm:honest-containment`` (iii) enumerates ELEVEN codes: the registry's
    nine, in its order and with their spellings unchanged, plus
    ``endpoint_rule_unknown``, which belongs to the two request fields
    ``endpoint_rule`` and ``tail_evaluation``, and
    ``honest_envelope_not_admissible``. The frozen tuple is the registry's, so
    it is compared against the FIRST NINE
    and the tenth is named explicitly -- rather than the assertion being
    relaxed to a subset, which would stop catching a spelling drift or a
    reordering.

    The input ``honest_envelope`` has the ELEVENTH code,
    ``honest_envelope_not_admissible``, for an envelope no law lies in; the
    point form keeps ``honest_not_a_distribution``. It is named explicitly for
    the same reason.

    A TWELFTH member would still be invented vocabulary -- in particular for
    a matched alphabet and round count (``def:matched-alphabet``), which "is a
    relation between artefacts and not a property of an input" and carries no
    code at all (``req:matched-alphabet``: a hard error).
    """
    live = tuple(str(reason) for reason in InfeasibilityReason)
    # The eleventh sits beside the point-form code it mirrors, as in
    # thm:honest-containment (iii); the registry's nine keep their relative order around
    # it.
    envelope = "honest_envelope_not_admissible"
    assert live[live.index("honest_not_a_distribution") + 1] == envelope
    without = tuple(code for code in live if code != envelope)
    assert without[: len(REASON_CODES)] == REASON_CODES
    assert without[len(REASON_CODES) :] == ("endpoint_rule_unknown",)
    assert str(InfeasibilityReason.ENDPOINT_RULE_UNKNOWN) == "endpoint_rule_unknown"
    # The frozen violating requests cover the registry's nine and no more: the
    # tenth has no frozen case of this freeze, and the cases that pin it are
    # in tests/oracles/registry_statistics_rules.py.
    assert set(VIOLATING_REQUESTS) == set(REASON_CODES)
