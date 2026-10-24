"""SA1 and SA8 (i) -- the taxonomy as a taxonomy, and the acceptance support.

Definition ``def:taxonomy`` admits EXACTLY TWO TAGS and says of the third that
"a consumer presented with any other tag refuses rather than guessing". The
canonical box is a SUB-FORM of ``polytope`` and not a third tag (Remark
``rem:two-tags``), which is why one record carries both here and why a consumer
that ignores ``box_bounds`` still reads a well-formed polytope.

WHAT THE MODULE DECLINES TO DECIDE, AND WHY THAT IS NOT A VERDICT. For a
declared ``polytope`` NOT in canonical box form the validation predicate is
rational feasibility of ``{q >= 0, sum q = 1, B q <= b}``, a linear program
rather than a closed form. The construction map never emits one, the consuming
package already decides it exactly at its own boundary, and a second exact
simplex here would be a parallel implementation of one decision -- so it raises
rather than returning "ill-formed", because refusing to answer is not a verdict
that the data is defective.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from certiqs_key.statistics import (
    GeometryDefect,
    GeometryTag,
    PolytopeGeometry,
    SingletonGeometry,
    UndecidedGeometryError,
    acceptance_support,
    box_witness_point,
    canonical_box,
    validate_geometry,
)

TWO = ("c0", "c1")
ZERO = Fraction(0)
ONE = Fraction(1)


@pytest.mark.contract
def test_there_are_exactly_two_tags() -> None:
    """Definition def:taxonomy: two, in one-to-one correspondence with rem:acc-side."""
    assert tuple(str(tag) for tag in GeometryTag) == ("singleton", "polytope")
    assert canonical_box(TWO, (ZERO, ZERO), (ONE, ONE)).tag is GeometryTag.POLYTOPE
    assert SingletonGeometry(TWO, (ONE, ZERO)).tag is GeometryTag.SINGLETON


@pytest.mark.contract
def test_the_canonical_box_rows_are_eq_boxrows() -> None:
    """Eq. eq:boxrows: the m cap rows first, then the m floor rows, in one order.

    The rows are BUILT from the pair rather than declared beside it, so the two
    cannot contradict each other -- which is the defect the consumer's
    well-formedness check exists to catch, and the construction map must not be
    able to produce one.
    """
    lower = (Fraction(1, 4), Fraction(1, 8), Fraction(0))
    upper = (Fraction(1, 2), Fraction(3, 8), Fraction(1))
    box = canonical_box(("c0", "c1", "c2"), lower, upper)
    assert box.m_row == 6
    assert box.rows == (
        (ONE, ZERO, ZERO),
        (ZERO, ONE, ZERO),
        (ZERO, ZERO, ONE),
        (-ONE, ZERO, ZERO),
        (ZERO, -ONE, ZERO),
        (ZERO, ZERO, -ONE),
    )
    assert box.rhs == (*upper, *(-value for value in lower))
    assert box.is_canonical_box is True
    assert all(value in (0, 1, -1) for row in box.rows for value in row)
    with pytest.raises(ValueError, match="pair per element of Chat"):
        canonical_box(TWO, (ZERO,), (ONE, ONE))


@pytest.mark.contract
def test_well_formedness_is_decided_before_emptiness() -> None:
    """The order is the content of the frozen ``ILLFORMED-box-inverted`` case.

    Eq. ``eq:boxfeas`` is proved UNDER ``0 <= q^- <= q^+``. On inverted data it
    returns a PASS while the set is empty, so a path that runs the sum test
    without the componentwise test admits a box and then computes a fill from a
    NEGATIVE width.
    """
    inverted = canonical_box(TWO, (Fraction(4, 5), ZERO), (Fraction(1, 5), ONE))
    verdict = validate_geometry(inverted)
    assert verdict.defect is GeometryDefect.ILL_FORMED
    assert "componentwise" in verdict.detail
    # The closed form alone WOULD have passed it.
    assert sum(inverted.box_bounds[0]) <= 1 <= sum(inverted.box_bounds[1])


@pytest.mark.contract
def test_a_general_polytope_is_declined_rather_than_judged() -> None:
    """A refusal, not a verdict -- and the shape is still checked first."""
    general = PolytopeGeometry(
        outcomes=TWO, rows=((ONE, ONE),), rhs=(Fraction(1, 2),), box_bounds=None
    )
    with pytest.raises(UndecidedGeometryError, match="rational feasibility"):
        validate_geometry(general)
    misshapen = PolytopeGeometry(outcomes=TWO, rows=((ONE,),), rhs=(ONE,))
    verdict = validate_geometry(misshapen)
    assert verdict.defect is GeometryDefect.ILL_FORMED
    assert "columns" in verdict.detail


@pytest.mark.contract
def test_the_singleton_predicate_has_two_independent_halves() -> None:
    """Theorem thm:geometry-validation (ii): non-negativity AND normalization, each on its own."""  # noqa: E501
    assert validate_geometry(SingletonGeometry(TWO, (ONE, ZERO))).admissible is True
    unnormalized = SingletonGeometry(TWO, (Fraction(1, 2), Fraction(1, 4)))
    assert validate_geometry(unnormalized).defect is GeometryDefect.EMPTY
    negative = SingletonGeometry(TWO, (Fraction(3, 2), Fraction(-1, 2)))
    assert sum(negative.frequencies) == 1
    assert validate_geometry(negative).defect is GeometryDefect.EMPTY


@pytest.mark.contract
def test_the_interpolation_witness_takes_both_branches() -> None:
    """Theorem thm:geometry-validation (iii), the (<=) direction, in closed rational form.

    The general branch divides by ``sum q^+ - sum q^-``; the degenerate one
    exists because that difference vanishes on exactly the box the construction
    map emits from a degenerate honest distribution.
    """  # noqa: E501
    general = box_witness_point((Fraction(1, 4),) * 3, (Fraction(1, 2),) * 3)
    assert general == (Fraction(1, 3),) * 3
    degenerate = box_witness_point((ONE, ZERO), (ONE, ZERO))
    assert degenerate == (ONE, ZERO)
    assert box_witness_point((ZERO, ZERO), (Fraction(1, 5), Fraction(1, 5))) is None
    assert box_witness_point((Fraction(4, 5),) * 2, (ONE, ONE)) is None


@pytest.mark.contract
def test_the_acceptance_support_is_cap_positivity_for_a_box() -> None:
    """SA8 (i) and the Outputs table: ``{chat : q^+(chat) > 0}``, not the minimal set.

    The emitted support NEED NOT BE MINIMAL and must not be tightened: Theorem
    ``thm:box-oracle`` (i) proves only the inclusion, and claims minimality for the
    ``singleton`` tag alone. Here every feasible point has ``q(c1) = 0`` -- the
    floor on ``c0`` exhausts the normalization -- and ``c1`` is in the support
    anyway, because its cap is positive.
    """
    box = canonical_box(TWO, (ONE, ZERO), (ONE, ONE))
    assert acceptance_support(box) == TWO
    closed = canonical_box(TWO, (ONE, ZERO), (ONE, ZERO))
    assert acceptance_support(closed) == ("c0",)


@pytest.mark.contract
def test_the_acceptance_support_of_a_singleton_is_its_support() -> None:
    """SA8 (i), last sentence: for a singleton the MINIMAL support is supp q^*."""
    assert acceptance_support(SingletonGeometry(TWO, (ONE, ZERO))) == ("c0",)
    assert acceptance_support(SingletonGeometry(TWO, (Fraction(1, 2),) * 2)) == TWO


@pytest.mark.contract
def test_a_general_polytope_has_no_cap_vector_to_read() -> None:
    """The Outputs-table formula has no instance, so the whole alphabet is returned.

    An acceptance support for any subset of the simplex -- trivially, and
    without pretending to more.
    """
    general = PolytopeGeometry(outcomes=TWO, rows=((ONE, ONE),), rhs=(ONE,))
    assert acceptance_support(general) == TWO
