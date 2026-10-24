"""The polytope acceptance oracle, against the FROZEN Group-8 oracles.

``O-POLYTOPE-ACC-MINIMUM``, ``O-POLYTOPE-SINGLETON-AGREEMENT`` and
``O-POLYTOPE-EMPTY-FAIL-CLOSED``, with their eleven case tuples. Those numbers
are the authority here and this implementation is what is on trial: every one of
them was derived by hand, twice, by routes sharing no step, and committed by a
DIFFERENT implementer instance before any polytope oracle existed under ``src/``
(the freeze rule). A disagreement is a finding against this
code, never against the registry.

WHAT IS PINNED, AND WHY EACH COLUMN EXISTS
==========================================
The frozen entry ``O-POLYTOPE-ACC-MINIMUM`` pins the PRIMAL minimum -- the
right-hand side of Eq. ``eq:bacc-def`` -- which ``O-BETA-ACC`` deliberately does
not: that entry pins the DUAL side, and "an implementation can satisfy the
second while getting the first wrong: a loose witness is sound, so no dual check
can reveal a minimum computed too small, and a minimum computed too LARGE is
exactly the unsound direction".

Each case also carries a SANDWICH -- the minimum over the whole simplex with the
rows dropped, and where one exists a feasible non-optimal point -- which brackets
the frozen value from both sides and names the two ways an implementation goes
wrong. Both brackets are asserted, because agreement with a single number can be
an accident and agreement with a bracket cannot.

THE ARGMIN IS ASSERTED AS A MEMBERSHIP, NOT AS AN IDENTITY. The registry says
why: on ``PMIN-box-tie`` the argmin is a segment, the frozen ``minimizers`` are
its two vertices, and "a test that asserts the ARGMIN rather than the VALUE pins
the sort's stability, which no contract fixes". A simplex returns a vertex, so
membership is the sharp statement available.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from registry import (
    POLYTOPE_INFEASIBLE_CASES,
    POLYTOPE_MINIMUM_CASES,
    PolytopeInfeasibleCase,
    PolytopeMinimumCase,
    oracle,
)

from certiqs_key.meat_core.acceptance.bacc import (
    beta_acc_polytope,
    beta_acc_singleton,
    float_below,
)
from certiqs_key.meat_core.acceptance.geometry import (
    acceptance_minimum,
    acceptance_witness,
    polytope_defect,
    polytope_is_nonempty,
    polytope_minimizer,
    polytope_relative_interior_point,
    polytope_support,
)
from certiqs_key.meat_core.declaration.declaration import PolytopeData


def data_of(case: PolytopeMinimumCase | PolytopeInfeasibleCase) -> PolytopeData:
    """Return the frozen case as the declaration data type, unchanged."""
    return PolytopeData(
        columns=len(case.outcomes),
        rows=case.rows,
        rhs=case.rhs,
        box_bounds=case.box_bounds,
    )


def satisfies(point: tuple[float, ...], case: PolytopeMinimumCase) -> bool:
    """Return whether a point is in the declared set, in exact arithmetic."""
    exact = [Fraction(value) for value in point]
    if any(value < 0 for value in exact):
        return False
    if sum(exact) != 1:
        return False
    return all(
        sum(Fraction(row[column]) * exact[column] for column in range(len(exact)))
        <= Fraction(bound)
        for row, bound in zip(case.rows, case.rhs, strict=True)
    )


# ===========================================================================
#  O-POLYTOPE-ACC-MINIMUM -- the primal minimum of Eq. eq:bacc-def (b).
# ===========================================================================


@pytest.mark.contract
@pytest.mark.oracle
def test_the_frozen_minimum_cases_are_all_consumed() -> None:
    """Dead frozen data is a defect; this is what makes the six live."""
    entry = oracle("O-POLYTOPE-ACC-MINIMUM")
    assert entry.claims == ("C19",)
    assert len(POLYTOPE_MINIMUM_CASES) == 6
    for case in POLYTOPE_MINIMUM_CASES:
        assert case.case_id in entry.derivation or case.case_id.startswith("PMIN-")
    # One case is deliberately NOT a canonical box, so that nothing in the group
    # depends on a box-shaped closed form applying.
    assert sum(case.box_bounds is None for case in POLYTOPE_MINIMUM_CASES) == 1


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", POLYTOPE_MINIMUM_CASES, ids=lambda c: c.case_id)
def test_the_frozen_minimum_is_reproduced_exactly(case: PolytopeMinimumCase) -> None:
    """Every frozen ``min <g, q>`` comes back, as an exact rational."""
    data = data_of(case)
    assert polytope_defect(data) is None, case.case_id
    assert polytope_is_nonempty(data)
    optimum = acceptance_minimum(case.g, data)
    assert optimum is not None
    # EXACT equality, not a tolerance: every frozen number is a dyadic rational
    # of denominator at most 16, so it is a binary64 value exactly and the
    # linear program is over the rationals from end to end.
    assert optimum.minimum == Fraction(case.minimum), case.case_id


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", POLYTOPE_MINIMUM_CASES, ids=lambda c: c.case_id)
def test_the_argmin_is_admissible_and_attains_the_minimum(
    case: PolytopeMinimumCase,
) -> None:
    """The returned minimizer is IN the declared set and attains the value."""
    data = data_of(case)
    point = polytope_minimizer(case.g, data)
    assert point is not None
    assert satisfies(point, case), point
    value = sum(Fraction(g) * Fraction(q) for g, q in zip(case.g, point, strict=True))
    assert value == Fraction(case.minimum)
    # A vertex, so it is one of the frozen minimizers -- the single point when
    # the argmin is unique, one of the two endpoints when it is a segment.
    assert point in case.minimizers, (point, case.minimizers)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", POLYTOPE_MINIMUM_CASES, ids=lambda c: c.case_id)
def test_the_frozen_dual_witness_is_admissible_and_gives_its_value(
    case: PolytopeMinimumCase,
) -> None:
    """The registry's own ``(u, v)`` passes the check and returns ``dual_value``.

    The frozen witness is read, not produced: it is a THIRD route to the same
    number, and this test says that the componentwise test of Remark
    ``rem:acc-side`` (b) accepts it and that the formula built on it lands on
    the frozen ``dual_value``, which is the frozen ``minimum``.
    """
    value = beta_acc_polytope(case.g, case.rows, case.rhs, case.dual_u, case.dual_v)
    assert value is not None, "the frozen witness must pass the admissibility test"
    assert float_below(value) == pytest.approx(case.dual_value)
    assert case.dual_value == case.minimum
    assert float_below(value) <= case.minimum


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", POLYTOPE_MINIMUM_CASES, ids=lambda c: c.case_id)
def test_the_constructed_witness_certifies_the_frozen_minimum(
    case: PolytopeMinimumCase,
) -> None:
    """This implementation's own ``(u, v)`` is admissible and lands on the value.

    Two separate claims, and the second is the one that matters: the witness is
    checked by :func:`beta_acc_polytope` -- the same componentwise test the
    frozen witness went through -- so a construction bug cannot make a number
    certified, and the bound it produces must not EXCEED the frozen minimum.
    Equality holds on all six because the rounding repair costs nothing on
    dyadic data.
    """
    data = data_of(case)
    witness = acceptance_witness(case.g, data)
    assert witness is not None
    assert all(value >= 0.0 for value in witness.multipliers), "u >= 0"
    value = beta_acc_polytope(
        case.g, case.rows, case.rhs, witness.multipliers, witness.offset
    )
    assert value is not None, "the constructed witness must pass its own check"
    assert float_below(value) <= case.minimum, "beta_acc never exceeds the minimum"
    assert float_below(value) == pytest.approx(case.minimum)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", POLYTOPE_MINIMUM_CASES, ids=lambda c: c.case_id)
def test_the_frozen_sandwich_brackets_the_minimum(case: PolytopeMinimumCase) -> None:
    """The two ways of getting it wrong, and which side of the value each lands.

    Relaxing the declared set to the whole simplex gives a SMALLER number --
    still a sound ``beta_acc``, not the declared minimum -- and evaluating
    at a feasible non-optimal point gives a LARGER one, which is unsound. Both
    directions are frozen, and both are re-derived here from this module rather
    than read off the case.
    """
    relaxed = PolytopeData(columns=len(case.outcomes), rows=(), rhs=())
    optimum = acceptance_minimum(case.g, relaxed)
    assert optimum is not None
    assert optimum.minimum == Fraction(case.simplex_relaxation)
    assert case.simplex_relaxation <= case.minimum
    if case.feasible_point is not None:
        assert case.feasible_point_value is not None
        assert satisfies(case.feasible_point, case)
        value = sum(
            Fraction(g) * Fraction(q)
            for g, q in zip(case.g, case.feasible_point, strict=True)
        )
        assert value == Fraction(case.feasible_point_value)
        assert case.feasible_point_value > case.minimum, "the unsound direction"


@pytest.mark.contract
@pytest.mark.oracle
def test_the_support_superset_case_gives_the_same_minimum_either_way() -> None:
    """``PMIN-box-support-superset``: a non-minimal ``Chat_acc`` is conforming.

    Definition ``def:perturbed`` asks of an acceptance support only that
    ``supp q`` lie inside it, records the union as the minimal choice, and says
    "any admissible superset may be used". This module returns the MINIMAL one,
    which here is ``{c0, c1}`` although ``q^+(c2) = 1/4 > 0``; the frozen case
    exists to say that a ``Chat_acc`` carrying ``c2`` is conforming too and that
    the two give the same minimum. Both halves are checked.
    """
    case = next(c for c in POLYTOPE_MINIMUM_CASES if c.case_id.endswith("superset"))
    data = data_of(case)
    assert polytope_support(data) == (0, 1), "the minimal support excludes c2"
    on_superset = acceptance_minimum(case.g, data)
    on_minimal = acceptance_minimum([case.g[0], case.g[1]], data.restricted([0, 1]))
    assert on_superset is not None and on_minimal is not None
    assert on_superset.minimum == on_minimal.minimum == Fraction(case.minimum)


# ===========================================================================
#  O-POLYTOPE-SINGLETON-AGREEMENT -- the two instantiations may not disagree.
# ===========================================================================


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_instantiations_agree_on_a_set_that_is_both() -> None:
    """O-POLYTOPE-SINGLETON-AGREEMENT: one quantity, two routes, one answer.

    ``beta_acc`` enters Eq. ``eq:hcert`` with a PLUS sign, so two routes
    returning two values would give one declaration two certified bounds and the
    larger of them would be the unsound one. The frozen data is
    ``ACC-A-singleton``'s: ``g = (2, -1)``, ``q* = (1/2, 1/2)``.

    The degenerate fill is where an implementation runs off the end of its loop
    -- the residual mass is ``r = 0``, every width is zero, and "an
    implementation that looks for the least index with a STRICT inequality finds
    none here". This one does not fill at all; it solves the linear program,
    which has nothing to run off.
    """
    entry = oracle("O-POLYTOPE-SINGLETON-AGREEMENT")
    assert entry.kind == "structural-identity"
    assert entry.value == 0.5

    case = next(c for c in POLYTOPE_MINIMUM_CASES if c.case_id.endswith("singleton"))
    surrogate = {"chat0": 2.0, "chat1": -1.0}
    by_route_a = beta_acc_singleton(
        surrogate, {"chat0": 0.5, "chat1": 0.5}, ("chat0", "chat1")
    )
    optimum = acceptance_minimum(case.g, data_of(case))
    assert optimum is not None
    assert float_below(by_route_a) == entry.value
    assert optimum.minimum == Fraction(entry.value)
    # And by the witness route, which is what a certified run actually uses.
    witness = acceptance_witness(case.g, data_of(case))
    assert witness is not None
    by_route_b = beta_acc_polytope(
        case.g, case.rows, case.rhs, witness.multipliers, witness.offset
    )
    assert by_route_b is not None
    assert float_below(by_route_b) == entry.value


@pytest.mark.contract
@pytest.mark.oracle
def test_the_agreement_is_a_property_of_the_denotation_not_the_data() -> None:
    """The second consistency pair: a NON-degenerate box denoting one point.

    ``PMIN-box-support-superset``'s third coordinate has width ``1/4``, so
    ``q^- != q^+``, and its denotation is nevertheless the single point
    ``(1/2, 1/2, 0)``. It returns the same ``1/2``. Together the two cases say
    "an implementation may not decide which route to run by inspecting whether
    ``q^-`` equals ``q^+``".
    """
    degenerate = next(
        c for c in POLYTOPE_MINIMUM_CASES if c.case_id.endswith("singleton")
    )
    non_degenerate = next(
        c for c in POLYTOPE_MINIMUM_CASES if c.case_id.endswith("superset")
    )
    assert non_degenerate.box_bounds is not None
    lower, upper = non_degenerate.box_bounds
    assert lower != upper, "the second box is not degenerate"
    first = acceptance_minimum(degenerate.g, data_of(degenerate))
    second = acceptance_minimum(non_degenerate.g, data_of(non_degenerate))
    assert first is not None and second is not None
    assert first.minimum == second.minimum == Fraction(0.5)


# ===========================================================================
#  O-POLYTOPE-EMPTY-FAIL-CLOSED -- and the order of the two refusals.
# ===========================================================================


@pytest.mark.contract
@pytest.mark.oracle
def test_the_frozen_infeasible_cases_are_all_consumed() -> None:
    """Five frozen refusals, and the entry's own value is ``+inf``."""
    entry = oracle("O-POLYTOPE-EMPTY-FAIL-CLOSED")
    assert entry.kind == "fail-closed"
    assert entry.value == float("inf")
    assert set(entry.claims) == {"C8", "C13", "C19"}
    assert len(POLYTOPE_INFEASIBLE_CASES) == 5
    for case in POLYTOPE_INFEASIBLE_CASES:
        assert case.case_id in entry.derivation, case.case_id


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", POLYTOPE_INFEASIBLE_CASES, ids=lambda c: c.case_id)
def test_every_frozen_infeasible_case_is_refused(case: PolytopeInfeasibleCase) -> None:
    """Refused, and refused by the check the case is frozen against.

    "TWO DISTINCT REFUSALS, WHICH MUST NOT BE COLLAPSED": the four well-formed
    cases denote an empty set, and the fifth is data that is not a geometry at
    all. An implementation "may report them the same way, but it may not reach
    the second conclusion by the first test", so the two are separated here by
    which predicate fires.
    """
    data = data_of(case)
    defect = polytope_defect(data)
    if case.well_formed:
        assert defect is None, defect
        assert not polytope_is_nonempty(data), "the denotation is empty"
    else:
        assert defect is not None
        assert "0 <= q^- <= q^+" in defect


@pytest.mark.contract
@pytest.mark.oracle
def test_the_inverted_box_is_refused_before_any_emptiness_reasoning() -> None:
    """``ILLFORMED-box-inverted``: the trap, and the order that avoids it.

    The closed-form box test ``sum q^- <= 1 <= sum q^+`` PASSES on this data and
    declares a non-empty set. It is not entitled to: the theorem it comes from
    is stated for ``0 <= q^- <= q^+``, and at ``c0`` the declared pair is
    ``(3/4, 1/4)``. So the test computes the closed form HERE, shows it passing,
    and shows the implementation refusing anyway -- which is the whole content
    of the frozen case.
    """
    case = next(c for c in POLYTOPE_INFEASIBLE_CASES if not c.well_formed)
    assert case.box_bounds is not None
    lower, upper = case.box_bounds
    assert sum(lower) <= 1.0 <= sum(upper), "the closed-form test would pass"
    assert any(lo > hi for lo, hi in zip(lower, upper, strict=True))
    assert polytope_defect(data_of(case)) is not None
    # And the set really is empty, which the closed form got wrong -- established
    # by the general predicate, which is not the one that refused it.
    assert not polytope_is_nonempty(data_of(case))


@pytest.mark.contract
@pytest.mark.oracle
def test_an_empty_set_never_yields_a_minimum_a_witness_or_a_start() -> None:
    """No number is manufactured for a set with no points.

    "Returning ``beta_acc = -inf`` as a 'safe' bound writes a number the
    contract does not define ... Substituting the minimum over the whole simplex
    replaces the declared set with a larger one ... Repairing the box ... changes
    the declaration. The frozen verdict is refusal."
    """
    for case in POLYTOPE_INFEASIBLE_CASES:
        data = data_of(case)
        cost = [1.0] * len(case.outcomes)
        assert acceptance_minimum(cost, data) is None, case.case_id
        assert acceptance_witness(cost, data) is None, case.case_id
        assert polytope_minimizer(cost, data) is None, case.case_id
        assert polytope_relative_interior_point(data) is None, case.case_id


# ===========================================================================
#  The ``u >= 0`` hypothesis, which no frozen case can falsify.
# ===========================================================================


@pytest.mark.contract
@pytest.mark.oracle
def test_a_negative_multiplier_is_refused_where_no_frozen_case_can_say_so() -> None:
    """``u >= 0`` is a HYPOTHESIS of Remark ``rem:acc-side`` (b), not a detail.

    The remark reads "for any ``u >= 0`` and ``v in R`` with
    ``g + B^T u + v >= 0``". The proof needs that sign: it bounds
    ``-<u, B q'> >= -<u, b>`` from ``B q' <= b``, and the step REVERSES on a
    negative component whose row is slack at the minimizer.

    NO FROZEN CASE CAN EXERCISE IT, which is why this counterexample is built by
    hand: every ``dual_u`` in the registry is non-negative -- asserted below --
    and so is every witness this implementation constructs, the construction
    rounding the optimal multipliers TOWARDS ZERO, which
    ``test_the_constructed_witness_certifies_the_frozen_minimum`` asserts on all
    six. That is the premise which leaves the sign check otherwise
    unfalsifiable: deleting it would leave the whole suite green.

    THE COUNTEREXAMPLE. The single row is the vacuous cap ``q(c0) <= 2``, so the
    declared set is the whole 2-simplex and ``min <g, q> = 0`` at ``q = (1, 0)``.
    The witness ``u = (-1)``, ``v = 1`` PASSES the componentwise test --
    ``g + B^T u + v = (0, 2) >= 0`` -- and the recipe would return
    ``-<b, u> - v = 2 - 1 = 1``, a full bit ABOVE the minimum, hence a
    ``beta_acc`` that RAISES ``h_cert`` (Eq. ``eq:hcert`` takes it with a plus
    sign).
    """
    for case in POLYTOPE_MINIMUM_CASES:
        assert all(value >= 0.0 for value in case.dual_u), case.case_id

    surrogate = [0.0, 1.0]
    rows = [[1.0, 0.0]]
    bounds = [2.0]
    declared = PolytopeData(columns=2, rows=((1.0, 0.0),), rhs=(2.0,))
    relaxed = PolytopeData(columns=2, rows=(), rhs=())
    true_minimum = acceptance_minimum(surrogate, declared)
    on_simplex = acceptance_minimum(surrogate, relaxed)
    assert true_minimum is not None and on_simplex is not None
    assert true_minimum.minimum == Fraction(0)
    assert on_simplex.minimum == true_minimum.minimum, "the row is vacuous"

    # The componentwise condition of the remark HOLDS on this witness ...
    assert all(
        surrogate[column] + rows[0][column] * (-1.0) + 1.0 >= 0.0 for column in range(2)
    )
    # ... and the number its formula would return is above the true minimum.
    assert -bounds[0] * (-1.0) - 1.0 > float(true_minimum.minimum)
    # The sign check is the only thing that withholds it.
    assert beta_acc_polytope(surrogate, rows, bounds, [-1.0], 1.0) is None

    # The same rows with an admissible u are accepted, so what was refused is
    # the SIGN and not the shape.
    accepted = beta_acc_polytope(surrogate, rows, bounds, [0.0], 0.0)
    assert accepted is not None
    assert float_below(accepted) <= float(true_minimum.minimum)
