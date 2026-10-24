"""What ``Acc`` emits, fed through the CONSUMER'S OWN validators, unchanged.

The point of this file is that neither side is adjusted for the other. The
producing module is ``statistics`` and the consuming checks are ``meat-core``'s;
no file of the engine was touched by the run that wrote this, and the geometry
crosses the boundary in the consumer's own record type
(:class:`certiqs_key.meat_core.declaration.declaration.PolytopeData`) rather
than in a parallel one invented here.

WHERE THE ADAPTER LIVES. The docking adapter is THE CONSUMER'S --
:mod:`certiqs_key.meat_core.docking_statistics` -- because imports point
downward only and the type it fills is ``meat-core``'s (the consumer reads the
supplier). THE ROUNDING DIRECTION: ``q^-`` down and ``q^+`` up, named where it
happens.

WHAT IT IS WORTH KEEPING FOR, in its own words.

For every one of the twelve frozen constructions:

* ``polytope_defect`` returns ``None`` -- the emitted rows ARE the canonical box
  rows of the emitted pair, which is the agreement check the consumer runs
  before it computes anything;
* ``polytope_is_nonempty`` returns ``True``, decided by the consumer's own exact
  simplex on ``{q >= 0, sum q = 1, B q <= b}`` -- not by the producing module's
  closed form, so the two routes to non-emptiness are independent;

and for every one of the six frozen box minima, the consumer's
``acceptance_minimum`` -- an exact rational simplex with a dual basis -- returns
the FROZEN minimum and agrees with the producer's closed-form fill.

THE ONE CONVERSION, AND ITS DIRECTION. ``PolytopeData`` types its numbers as
machine numbers and the producing module emits exact rationals, so the docking
adapter rounds: ``q^-`` DOWN and ``q^+`` UP, the one direction that module's
``binomial-box/lem:widening`` licenses. Where every bound is dyadic the conversion is
exact and there is nothing to check; where it is not, the test asserts what the
rounding is for -- the machine box CONTAINS the exact one, so the honest point
is still inside and the consumer's minimum can only fall.

NO ASSUMPTION IS NAMED. The condition is ``def:conservative-evaluation`` and
the direction this file pins is ``binomial-box/lem:widening``, which this file
names. Short ids are repository-wide and ``receiver/ass:exact`` owns A-EXACT
for a different assumption (the exact window). THE FROZEN REGISTRY KEEPS
A-EXACT wherever a derivation names it, and says at its own site why.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from registry_statistics_acceptance import (
    BOX_MINIMUM_CASES,
    CONSTRUCTION_CASES,
    BoxMinimumCase,
    ConstructionCase,
)
from statistics_requests import request_of

from certiqs_key.meat_core.acceptance.geometry import (
    acceptance_minimum,
    polytope_defect,
    polytope_is_nonempty,
    polytope_support,
)
from certiqs_key.meat_core.declaration.declaration import PolytopeData
from certiqs_key.meat_core.docking_statistics import (
    acceptance_set_record,
    conversion_is_exact,
    polytope_data,
)
from certiqs_key.statistics import box_minimum, canonical_box, construct


def emitted_data(case: ConstructionCase) -> PolytopeData:
    """Return the frozen construction, docked into the consumer's record type."""
    result = construct(request_of(case))
    assert result.acceptance_set is not None
    return polytope_data(result.acceptance_set)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_the_emitted_box_passes_the_consumers_well_formedness_check(
    case: ConstructionCase,
) -> None:
    """``polytope_defect`` is the check that the rows and the pair agree.

    The consumer refuses declared data that contradicts itself before it
    computes anything from it, and the shape it insists on is Eq.
    ``eq:boxrows``: row ``i`` is ``+e_i`` at ``q^+(c_i)`` and row ``m + i`` is
    ``-e_i`` at ``-q^-(c_i)``, with ``m_row = 2m``. Nothing in the adapter
    re-derives that shape from the consumer's expectations -- the rows are built
    from the contract's own equation and this is where the two are compared.
    """
    data = emitted_data(case)
    assert polytope_defect(data) is None
    assert data.columns == len(case.outcomes)
    assert data.m_row == case.m_row


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_the_emitted_box_is_non_empty_by_the_consumers_own_decision(
    case: ConstructionCase,
) -> None:
    """Theorem thm:honest-containment (iii), checked from the other side of the boundary.

    The consuming module decides emptiness with an exact simplex over
    ``{q >= 0, sum q = 1, B q <= b}`` and treats an empty acceptance set as a
    hard failure -- it makes the certificate's ``beta_acc`` vacuous, so
    ``h_low`` is ``+inf`` with no key-length claim. Theorem ``thm:honest-containment``
    (iii) is the promise that this can never happen for a set ``Acc`` built from an
    admissible input, and this is that promise tested rather than asserted.
    """  # noqa: E501
    assert polytope_is_nonempty(emitted_data(case)) is True


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_the_machine_box_contains_the_exact_one(case: ConstructionCase) -> None:
    """The conversion enlarges, or does nothing. It never shrinks.

    Lemma ``binomial-box/lem:widening``: lower bounds may move down and upper
    bounds up (its (i)-(iv)), never the reverse (its (v)). A shrunken box would
    report a completeness the set does not have; an enlarged one costs rate and
    never soundness.
    """
    result = construct(request_of(case))
    assert result.acceptance_set is not None
    exact_lower, exact_upper = case.box_lower, case.box_upper
    data = polytope_data(result.acceptance_set)
    assert data.box_bounds is not None
    machine_lower, machine_upper = data.box_bounds
    for low, machine in zip(exact_lower, machine_lower, strict=True):
        assert Fraction(machine) <= low
    for high, machine in zip(exact_upper, machine_upper, strict=True):
        assert Fraction(machine) >= high
    if conversion_is_exact(result.acceptance_set):
        assert tuple(Fraction(value) for value in machine_lower) == exact_lower
        assert tuple(Fraction(value) for value in machine_upper) == exact_upper
    # The honest point survives the conversion, which is what the direction is
    # for (Theorem thm:box-construction (iii)).
    for low, honest, high in zip(
        machine_lower, case.honest, machine_upper, strict=True
    ):
        assert Fraction(low) <= honest <= Fraction(high)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", BOX_MINIMUM_CASES, ids=lambda c: c.case_id)
def test_the_consumers_simplex_returns_the_frozen_minimum(
    case: BoxMinimumCase,
) -> None:
    """The frozen minimum, by the consumer's linear program and by the closed form.

    Remark ``rem:box-oracle-consumer``: for the representation this module emits the
    minimum is computable in closed form, exactly -- "no dual search and no
    linear-programming solve is needed". The consumer nevertheless solves one,
    and this is where the two answers meet. Every bound of these six boxes is
    dyadic, so the docking conversion is exact and the comparison is a
    comparison of the same numbers rather than of two roundings.
    """
    geometry = canonical_box(case.outcomes, case.box_lower, case.box_upper)
    assert conversion_is_exact(geometry) is True
    data = polytope_data(geometry)
    assert polytope_defect(data) is None
    surrogate = [float(value) for value in case.g]
    solved = acceptance_minimum(surrogate, data)
    assert solved is not None
    assert solved.minimum == case.minimum
    closed_form = box_minimum(geometry, case.g)
    assert closed_form is not None
    assert closed_form.minimum == solved.minimum
    # The consumer's argmin is a VERTEX and need not be this module's fill, so
    # membership and value are what is asserted -- the frozen `minimizers`
    # column exists because on a tie the argmin is a segment.
    assert sum(solved.argmin) == 1
    for low, value, high in zip(
        case.box_lower, solved.argmin, case.box_upper, strict=True
    ):
        assert low <= value <= high


@pytest.mark.contract
@pytest.mark.oracle
def test_the_emitted_support_may_exceed_the_consumers_minimal_one() -> None:
    """Two conforming answers to two different questions, and they must not be one.

    The Outputs table fixes this module's ``Chat_acc`` as the CAP-POSITIVITY set
    ``{chat : q^+(chat) > 0}``, and Theorem ``thm:box-oracle`` (i) asks only that
    ``supp q`` be inside it for every member. The consumer computes the MINIMAL
    acceptance support instead -- one linear program per coordinate -- because
    "a smaller ``Chat_acc`` means fewer hypotheses to certify". On
    ``ACC-support-superset`` the two differ, both are admissible in the sense of
    Definition ``def:perturbed``, and neither may be substituted for the other.
    """
    case = next(
        item for item in CONSTRUCTION_CASES if item.case_id == "ACC-support-superset"
    )
    result = construct(request_of(case))
    assert result.acceptance_support == ("c0", "c1")
    minimal = polytope_support(emitted_data(case))
    assert tuple(case.outcomes[index] for index in minimal) == ("c0",)
    assert set(case.minimal_support) < set(result.acceptance_support)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_acceptance_set_record_carries_the_tag_the_consumer_reads() -> None:
    """The machine key contract Section 1 names: ``acceptance_set``.

    ``meat-core`` "defines NO geometry vocabulary of its own" and reads the two
    tags of Definition ``def:taxonomy`` as data, refusing any other rather than
    guessing. The record this module hands over carries ``polytope``, which is
    the tag its construction map always emits.
    """
    case = next(
        item for item in CONSTRUCTION_CASES if item.case_id == "ACC-normal-2letter"
    )
    result = construct(request_of(case))
    assert result.acceptance_set is not None
    record = acceptance_set_record(result.acceptance_set)
    assert record.geometry == "polytope"
    assert record.polytope is not None
    assert polytope_defect(record.polytope) is None
    assert record.frequencies == ()
