"""Hypothesis properties over generated acceptance-set constructions.

Every property here is a THEOREM OF THE CONTRACT quantified over its own input
domain, which is what the frozen cases cannot be: a case is one point, and these
statements are universal ones. Nothing is generated that makes a mathematical
claim -- the inputs are arbitrary admissible ones, and the contract is required
to hold on all of them.

    lem:guard (i)                the ordering chain, hence honest containment per
                                 outcome
    lem:guard (ii)               the emitted endpoints meet their budgets
    thm:box-construction (i)     exact rationality: denominator n on Chat_con, else
                                 0 or 1
    thm:box-construction (ii)    0 <= q^- <= q^+ <= 1, so the emitted data IS a
                                 canonical box
    thm:box-construction (iii)   p^hon in AcceptSet, hence Eq. eq:boxfeas
    thm:completeness-bound       epsilon_star in [0, ecomp]
    thm:monotonicity-limits (i)  the set is non-increasing in ecomp
    thm:box-oracle (ii)          the closed-form fill is optimal, against an independent
                                 enumeration of the vertices
    thm:box-oracle (iii)         the witness is dual-feasible with equality, and tight

``thm:sa3`` IS SPLIT and its label names no claim here: what is the exact
rule's is ``binomial-box/prop:rule-exact`` and what holds for every rule is
``binomial-box/lem:guard``, clause for clause, and this file cites those. The frozen
registry keeps SA3 as its section id.
"""

from __future__ import annotations

import itertools
from fractions import Fraction

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from certiqs_key.statistics import (
    AcceptanceRequest,
    acceptance_support,
    box_minimum,
    box_witness_point,
    canonical_box,
    construct,
    emitted_tails,
    resolve,
    validate_geometry,
)

ALPHABET = ("c0", "c1", "c2", "c3")


@st.composite
def honest_laws(draw: st.DrawFn, size: int) -> tuple[Fraction, ...]:
    """Return an exact rational law on ``size`` outcomes, degenerate ones included."""
    weights = draw(
        st.lists(st.integers(min_value=0, max_value=12), min_size=size, max_size=size)
    )
    if sum(weights) == 0:
        weights = [1] + [0] * (size - 1)
    total = sum(weights)
    return tuple(Fraction(weight, total) for weight in weights)


@st.composite
def requests(draw: st.DrawFn) -> AcceptanceRequest:
    """Return an admissible input of contract Section 2.1, defaults included."""
    size = draw(st.integers(min_value=1, max_value=4))
    outcomes = ALPHABET[:size]
    honest = draw(honest_laws(size))
    rounds = draw(st.integers(min_value=1, max_value=24))
    budget = draw(
        st.fractions(min_value=0, max_value=Fraction(24, 25), max_denominator=25)
    )
    constrained = draw(
        st.one_of(
            st.none(),
            st.lists(
                st.sampled_from(outcomes), min_size=0, max_size=size, unique=True
            ).map(tuple),
        )
    )
    return AcceptanceRequest(
        alphabet=outcomes,
        honest=dict(zip(outcomes, honest, strict=True)),
        rounds=rounds,
        budget=budget,
        constrained=constrained,
    )


@st.composite
def canonical_boxes(
    draw: st.DrawFn,
) -> tuple[tuple[str, ...], tuple[Fraction, ...], tuple[Fraction, ...]]:
    """Return a NON-EMPTY canonical box, which is Theorem thm:box-oracle (ii)'s hypothesis."""  # noqa: E501
    size = draw(st.integers(min_value=1, max_value=4))
    outcomes = ALPHABET[:size]
    denominator = draw(st.integers(min_value=1, max_value=12))
    lower = tuple(
        Fraction(draw(st.integers(min_value=0, max_value=denominator)), denominator)
        for _ in range(size)
    )
    upper = tuple(
        low
        + Fraction(draw(st.integers(min_value=0, max_value=denominator)), denominator)
        for low in lower
    )
    upper = tuple(min(value, Fraction(1)) for value in upper)
    if not sum(lower) <= 1 <= sum(upper):
        # Rejecting here would bias the sample; repairing is a projection ONTO
        # the hypothesis Theorem thm:box-oracle (ii) is stated under, which is exactly
        # Eq. eq:boxfeas.
        lower = tuple(Fraction(0) for _ in lower)
        upper = tuple(Fraction(1) for _ in upper)
    return outcomes, lower, upper


@pytest.mark.contract
@settings(max_examples=120, deadline=None)
@given(request=requests())
def test_the_emitted_box_is_admissible_and_contains_the_honest_point(
    request: AcceptanceRequest,
) -> None:
    """Theorem thm:box-construction (i)-(iv), on arbitrary admissible inputs.

    Honest containment is UNCONDITIONAL -- for every admissible ``ecomp``, every
    ``Chat_con`` and every admissible allocation -- and it is what makes the
    validation predicate hold on the output of ``Acc`` without a side condition,
    which is Theorem ``thm:honest-containment`` (iii)'s first sentence and the reason no
    infeasibility report can originate in the construction.
    """
    result = construct(request)
    assert result.infeasibility_report is None
    box = result.acceptance_set
    assert box is not None
    assert box.box_bounds is not None
    lower, upper = box.box_bounds
    constrained = set(
        request.alphabet if request.constrained is None else request.constrained
    )
    for outcome, low, high in zip(request.alphabet, lower, upper, strict=True):
        assert 0 <= low <= high <= 1
        assert low <= request.honest[outcome] <= high
        if outcome in constrained:
            assert (low * request.rounds).denominator == 1
            assert (high * request.rounds).denominator == 1
        else:
            assert (low, high) == (Fraction(0), Fraction(1))
    assert sum(lower) <= 1 <= sum(upper)
    assert validate_geometry(box).admissible is True
    assert box.m_row == 2 * len(request.alphabet)
    witness = box_witness_point(lower, upper)
    assert witness is not None
    assert sum(witness) == 1
    # Lemma lem:guard (ii), Eq. eq:budget-met, at the EMITTED endpoints and
    # against the allocation the DEFAULT rule resolved to.
    resolved = resolve(request)
    shares = dict(
        zip(
            resolved.constrained,
            zip(resolved.eps_lower, resolved.eps_upper, strict=True),
            strict=True,
        )
    )
    for outcome, interval in zip(request.alphabet, result.intervals, strict=True):
        if interval is None:
            assert outcome not in shares
            continue
        below, above = emitted_tails(interval)
        assert below.upper <= shares[outcome][0]
        assert above.upper <= shares[outcome][1]


@pytest.mark.contract
@settings(max_examples=120, deadline=None)
@given(request=requests())
def test_epsilon_star_stays_inside_the_declared_budget(
    request: AcceptanceRequest,
) -> None:
    """Theorem thm:completeness-bound and the Outputs-table domain ``[0, ecomp]``."""
    result = construct(request)
    reported = result.completeness_certified
    assert reported is not None
    assert 0 <= reported <= request.budget


@pytest.mark.contract
@settings(max_examples=120, deadline=None)
@given(request=requests())
def test_the_acceptance_support_is_the_cap_positivity_set(
    request: AcceptanceRequest,
) -> None:
    """SA8 (i) and the Outputs table, quantified rather than sampled."""
    result = construct(request)
    box = result.acceptance_set
    assert box is not None
    assert box.box_bounds is not None
    assert result.acceptance_support == acceptance_support(box)
    assert result.acceptance_support == tuple(
        outcome
        for outcome, cap in zip(request.alphabet, box.box_bounds[1], strict=True)
        if cap > 0
    )


@pytest.mark.contract
@settings(max_examples=60, deadline=None)
@given(request=requests(), step=st.integers(min_value=1, max_value=20))
def test_the_set_is_non_increasing_in_the_budget(
    request: AcceptanceRequest, step: int
) -> None:
    """Theorem thm:monotonicity-limits (i) under the DEFAULT uniform rule, which is monotone.

    The claim is false for an arbitrary pair of allocations, so the pair
    compared here differs in the budget alone and both are resolved by the same
    rule -- which is the hypothesis Definition ``def:monotone-rule`` states.
    """  # noqa: E501
    larger = min(request.budget + Fraction(step, 25), Fraction(99, 100))
    small = construct(request)
    large = construct(
        AcceptanceRequest(
            alphabet=request.alphabet,
            honest=request.honest,
            rounds=request.rounds,
            budget=larger,
            constrained=request.constrained,
        )
    )
    assert small.acceptance_set is not None
    assert large.acceptance_set is not None
    assert small.acceptance_set.box_bounds is not None
    assert large.acceptance_set.box_bounds is not None
    for before, after in zip(
        small.acceptance_set.box_bounds[0],
        large.acceptance_set.box_bounds[0],
        strict=True,
    ):
        assert before <= after
    for before, after in zip(
        small.acceptance_set.box_bounds[1],
        large.acceptance_set.box_bounds[1],
        strict=True,
    ):
        assert after <= before


@pytest.mark.contract
@settings(max_examples=120, deadline=None)
@given(data=canonical_boxes(), weights=st.data())
def test_the_closed_form_fill_is_optimal_against_an_independent_enumeration(
    data: tuple[tuple[str, ...], tuple[Fraction, ...], tuple[Fraction, ...]],
    weights: st.DataObject,
) -> None:
    """Theorem thm:box-oracle (ii), checked against every vertex of the set.

    A linear function over a polytope attains its minimum at a vertex, and the
    vertices of a box intersected with the simplex are exactly the greedy fills
    over the permutations of the coordinates -- fill from the floors upward in
    some order until the mass is spent. Enumerating them for ``|Chat| <= 4``
    gives an optimality check that shares NO step with Eq. ``eq:greedy``'s
    exchange argument: it never sorts by ``g`` and never forms ``lambda``.
    """
    outcomes, lower, upper = data
    objective = tuple(
        Fraction(weights.draw(st.integers(min_value=-6, max_value=6))) for _ in outcomes
    )
    geometry = canonical_box(outcomes, lower, upper)
    solved = box_minimum(geometry, objective)
    assert solved is not None
    residual = Fraction(1) - sum(lower, Fraction(0))
    best = None
    for order in itertools.permutations(range(len(outcomes))):
        point = list(lower)
        remaining = residual
        for index in order:
            take = min(remaining, upper[index] - lower[index])
            point[index] = lower[index] + take
            remaining -= take
        assert remaining == 0
        assert sum(point) == 1
        value = sum(
            (
                weight * coordinate
                for weight, coordinate in zip(objective, point, strict=True)
            ),
            Fraction(0),
        )
        best = value if best is None else min(best, value)
    assert solved.minimum == best
    # The fill's own point is feasible and attains it.
    assert sum(solved.q_opt) == 1
    for low, value, high in zip(lower, solved.q_opt, upper, strict=True):
        assert low <= value <= high


@pytest.mark.contract
@settings(max_examples=120, deadline=None)
@given(data=canonical_boxes(), weights=st.data())
def test_the_dual_witness_is_feasible_with_equality_and_tight(
    data: tuple[tuple[str, ...], tuple[Fraction, ...], tuple[Fraction, ...]],
    weights: st.DataObject,
) -> None:
    """Theorem thm:box-oracle (iii), Eqs. eq:dualfeas and eq:dualvalue.

    The consuming Remark ``rem:acc-side`` (b) requires only the componentwise
    INEQUALITY ``g + B^T u + v >= 0``; that it holds here with EQUALITY is
    exactly why the resulting bound is tight for a canonical box rather than
    conservative.
    """
    outcomes, lower, upper = data
    objective = tuple(
        Fraction(weights.draw(st.integers(min_value=-6, max_value=6))) for _ in outcomes
    )
    solved = box_minimum(canonical_box(outcomes, lower, upper), objective)
    assert solved is not None
    assert all(value >= 0 for value in solved.dual_u)
    assert all(value == 0 for value in solved.dual_feasibility)
    assert solved.dual_value == solved.minimum
    assert solved.dual_v == -solved.lam
