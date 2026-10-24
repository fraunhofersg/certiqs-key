"""The declared acceptance geometries: well-formedness, emptiness, and the LP.

Unit level. The NUMBERS are pinned by the frozen Group-8 oracles and asserted in
``tests/golden/test_polytope_acceptance_against_registry.py``; what is tested
here is the behaviour around them -- which check fires first, what a malformed
declaration does, where the refusals land, and the properties the Frank-Wolfe
start has to have for a gradient to exist at it.
"""

from __future__ import annotations

import math
from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest
from mode_bundles import build_bundle, bundle_documents
from polytope_toys import (
    BOX_LOWER,
    BOX_UPPER,
    POLYTOPE_ACCEPTANCE_SET,
    POLYTOPE_START,
    general_polytope_toy,
    polytope_toy,
)
from toy_declarations import toy

from certiqs_key.domain.bundle import OperatorBundle, parse_manifest
from certiqs_key.meat_core.acceptance.geometry import (
    GEOMETRY_TAGS,
    POLYTOPE,
    SINGLETON,
    AcceptanceDefect,
    acceptance_floors,
    acceptance_minimum,
    acceptance_start,
    acceptance_verdict,
    acceptance_witness,
    minimal_acceptance_support,
    polytope_coordinate_minima,
    polytope_defect,
    polytope_is_nonempty,
    polytope_of,
    polytope_relative_interior_point,
    polytope_support,
)
from certiqs_key.meat_core.acceptance.simplex import (
    LinearProgramStatus,
    solve_standard_form,
)
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    PolytopeData,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.declaration.validation import validate_declaration
from certiqs_key.meat_core.errors import DeclarationError, UnsupportedDeclarationError
from certiqs_key.meat_core.objective.support import acceptance_support
from certiqs_key.solvers.oracles.acceptance import (
    PolytopeAcceptanceOracle,
    SingletonAcceptanceOracle,
    acceptance_oracle,
)

BOX = PolytopeData(
    columns=2,
    rows=((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)),
    rhs=(BOX_UPPER[0], BOX_UPPER[1], -BOX_LOWER[0], -BOX_LOWER[1]),
    box_bounds=(BOX_LOWER, BOX_UPPER),
)


def build(document: dict, arrays: dict) -> OperatorBundle:
    """Return a parsed bundle from a mutated manifest."""
    return OperatorBundle(manifest=parse_manifest(document), arrays=arrays)


def replace_acceptance(
    declaration: ProtocolDeclaration, data: PolytopeData
) -> ProtocolDeclaration:
    """Return the declaration with a different declared polytope, unvalidated."""
    return replace(
        declaration,
        acceptance_set=AcceptanceSet(geometry=POLYTOPE, polytope=data),
    )


# ===========================================================================
#  The taxonomy is read as data, and nothing is invented.
# ===========================================================================


@pytest.mark.contract
def test_exactly_the_two_declared_tags_are_read() -> None:
    """statistics-acceptance 0.1.2: "There is no third tag"."""
    assert GEOMETRY_TAGS == (SINGLETON, POLYTOPE)


@pytest.mark.contract
def test_an_unread_tag_is_refused_with_a_reason_that_names_the_taxonomy() -> None:
    """A ball is a closed convex subset of the simplex, and is still refused."""
    declaration = declaration_from_bundle(build_bundle(toy("TOY-8-T")))
    widened = replace(
        declaration,
        acceptance_set=replace(declaration.acceptance_set, geometry="ball"),
    )
    verdict = acceptance_verdict(widened)
    assert verdict.defect is AcceptanceDefect.UNSUPPORTED_GEOMETRY
    assert "not read by this implementation" in verdict.detail
    with pytest.raises(UnsupportedDeclarationError, match="not read by this"):
        validate_declaration(widened)
    with pytest.raises(UnsupportedDeclarationError):
        acceptance_oracle(widened)


# ===========================================================================
#  Well-formedness FIRST, emptiness SECOND.
# ===========================================================================


@pytest.mark.contract
def test_a_well_formed_box_has_no_defect() -> None:
    assert polytope_defect(BOX) is None
    assert polytope_is_nonempty(BOX)


@pytest.mark.contract
@pytest.mark.parametrize(
    ("mutation", "fragment"),
    [
        ({"columns": 0}, "acceptance alphabet is empty"),
        ({"rows": ((1.0, 0.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0))}, "columns"),
        ({"rhs": (0.75, 0.75, -0.25)}, "read positionally"),
        (
            {"rows": ((float("nan"), 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0))},
            "not a real number",
        ),
        ({"rhs": (float("inf"), 0.75, -0.25, -0.125)}, "not a real number"),
        ({"box_bounds": ((0.25,), (0.75, 0.75))}, "one (q^-, q^+) pair"),
        ({"box_bounds": ((0.9, 0.125), (0.75, 0.75))}, "0 <= q^- <= q^+"),
        ({"box_bounds": ((-0.1, 0.125), (0.75, 0.75))}, "0 <= q^- <= q^+"),
        ({"box_bounds": ((0.125, 0.25), (0.75, 0.75))}, "canonical floor row"),
        ({"box_bounds": ((0.25, 0.125), (0.5, 0.75))}, "canonical cap row"),
    ],
)
def test_ill_formed_data_names_the_check_it_fails(
    mutation: dict, fragment: str
) -> None:
    """Each failure names its own check, so a reader learns what is wrong."""
    defect = polytope_defect(replace(BOX, **mutation))
    assert defect is not None
    assert fragment in defect, defect


@pytest.mark.contract
def test_a_box_whose_rows_are_not_its_rows_is_refused() -> None:
    """Declared data that contradicts itself is refused, not reconciled.

    ``box_bounds`` CLAIMS canonical box form, and Eq. ``eq:boxrows`` says what
    the rows of that form are. If they disagree, one half is wrong and this
    module cannot decide which -- so it refuses rather than picking a winner.
    """
    swapped = replace(BOX, rows=(BOX.rows[2], BOX.rows[1], BOX.rows[0], BOX.rows[3]))
    assert polytope_defect(swapped) is not None
    too_few = replace(BOX, rows=BOX.rows[:2], rhs=BOX.rhs[:2])
    assert "m_row" in str(polytope_defect(too_few))


@pytest.mark.contract
def test_a_general_polytope_needs_no_box_record() -> None:
    """``box_bounds`` is a sub-form, not a tag: dropping it changes nothing."""
    general = replace(BOX, box_bounds=None)
    assert polytope_defect(general) is None
    with_box = acceptance_minimum([1.0, 2.0], BOX)
    without = acceptance_minimum([1.0, 2.0], general)
    assert with_box is not None and without is not None
    assert with_box.minimum == without.minimum


@pytest.mark.contract
def test_emptiness_uses_all_three_conditions_of_the_validation_predicate() -> None:
    """``q >= 0``, ``sum q = 1`` and ``B q <= b`` together, never a subset.

    The row ``q(c0) + q(c1) + q(c2) <= 1/2`` is satisfiable in the non-negative
    orthant -- ``q = 0`` satisfies it -- and empty on the simplex. A path that
    checked only ``{q >= 0, B q <= b}`` would accept it.
    """
    data = PolytopeData(columns=3, rows=((1.0, 1.0, 1.0),), rhs=(0.5,))
    assert polytope_defect(data) is None
    assert not polytope_is_nonempty(data)


# ===========================================================================
#  The Frank-Wolfe start, and the acceptance support.
# ===========================================================================


@pytest.mark.contract
def test_the_start_is_in_the_set_and_positive_on_the_whole_support() -> None:
    """Corollary cor:full-gradient is stated at a point with ``q(chat) > 0``.

    A vertex would not do: it sets some coordinate to zero, where the
    ``q``-derivative is ``-inf`` and the gradient the driver needs does not
    exist. The average of one maximizer per coordinate is in the set by
    convexity and is positive exactly on the minimal acceptance support.
    """
    point = polytope_relative_interior_point(BOX)
    assert point is not None
    assert point == (0.5, 0.5)
    assert sum(Fraction(value) for value in point) == 1
    for index in polytope_support(BOX):
        assert point[index] > 0.0


@pytest.mark.contract
def test_a_coordinate_that_must_vanish_is_outside_the_support_and_zero() -> None:
    """A box whose floors exhaust the normalization pins the rest at zero."""
    data = PolytopeData(
        columns=3,
        rows=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, -1.0),
        ),
        rhs=(0.5, 0.5, 0.25, -0.5, -0.5, 0.0),
        box_bounds=((0.5, 0.5, 0.0), (0.5, 0.5, 0.25)),
    )
    assert polytope_support(data) == (0, 1)
    point = polytope_relative_interior_point(data)
    assert point == (0.5, 0.5, 0.0)


@pytest.mark.contract
def test_the_coordinate_floors_are_the_minima_over_the_set_not_the_declared_box() -> (
    None
):
    """The quantity Theorem ``thm:oracle`` (H1) is stated over, by hand.

    ``BOX`` declares ``q^- = (1/4, 1/8)``, ``q^+ = (3/4, 3/4)``, whose
    denotation on the 2-simplex is the segment ``{(a, 1-a) : 1/4 <= a <= 3/4}``
    -- the normalization cuts the box down, because ``q(chat1) = 1 - a`` cannot
    reach ``1/8`` while ``a <= 3/4``. So the minima over the SET are
    ``(1/4, 1/4)`` and the declared floor ``q^-(chat1) = 1/8`` is not one of
    them. An implementation that read (H1) off ``box_bounds`` would answer
    about a larger set; one that read it off a declared frequency vector would
    have no vector to read.
    """
    assert BOX_LOWER == (0.25, 0.125), "the hand derivation above reads this pair"
    assert polytope_coordinate_minima(BOX) == (Fraction(1, 4), Fraction(1, 4))
    declaration = declaration_from_bundle(build_bundle(polytope_toy()))
    assert acceptance_floors(declaration) == {"chat0": 0.25, "chat1": 0.25}
    # The singleton reading is the same rule on a one-point set, not a second
    # one: the minimum over ``{q*}`` is ``q*``.
    singleton = declaration_from_bundle(build_bundle(toy("TOY-8-T")))
    assert acceptance_floors(singleton) == {"chat0": 0.5, "chat1": 0.5}


@pytest.mark.contract
def test_no_floor_is_offered_for_a_set_that_has_none() -> None:
    """Both ways ``acceptance_floors`` declines, so a caller can fail closed.

    An empty polytope has no minimum in any coordinate, and a column count that
    disagrees with the acceptance alphabet cannot be matched to one. Neither may
    come back as a number, and neither may come back as an untyped exception
    from a mismatched zip.
    """
    empty = PolytopeData(
        columns=2,
        rows=((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)),
        rhs=(0.25, 0.25, 0.0, 0.0),
        box_bounds=((0.0, 0.0), (0.25, 0.25)),
    )
    assert not polytope_is_nonempty(empty)
    assert polytope_coordinate_minima(empty) is None
    declaration = declaration_from_bundle(build_bundle(polytope_toy()))
    assert acceptance_floors(replace_acceptance(declaration, empty)) is None
    mismatched = PolytopeData(columns=1, rows=((1.0,),), rhs=(1.0,))
    assert polytope_coordinate_minima(mismatched) == (Fraction(1),)
    assert acceptance_floors(replace_acceptance(declaration, mismatched)) is None


@pytest.mark.contract
def test_the_h1_floor_is_rounded_downward_on_a_non_dyadic_minimum() -> None:
    """Theorem thm:oracle (H1) is a floor EVERY member of the set meets.

    ``acceptance_floors`` reports a machine number for a minimum that need not
    be one, so the rounding direction is load-bearing: rounding UP would claim
    a ``p_0`` no member of the declared set attains, which is unsound in the
    one direction (H1) cares about, while rounding DOWN is a weaker hypothesis
    and never a wrong one.

    Every polytope elsewhere in the suite has DYADIC coordinate minima --
    ``1/4``, ``0``, ``1`` -- where both roundings return the same double and
    the direction is untested. Here the single row is ``-3 q0 <= -1``, so on
    the 2-simplex the denotation is ``{(a, 1 - a) : 1/3 <= a <= 1}``: the
    coordinate minima are ``1/3`` and ``0``, and ``1/3`` is not a machine
    number. The two assertions below determine the answer uniquely -- the
    largest double at or below ``1/3`` -- so any other rounding rule fails.
    """
    assert Fraction(float(Fraction(1, 3))) != Fraction(1, 3), (
        "the premise: 1/3 is not a machine number, so rounding down and "
        "rounding up give different answers here"
    )
    data = PolytopeData(columns=2, rows=((-3.0, 0.0),), rhs=(-1.0,))
    assert polytope_coordinate_minima(data) == (Fraction(1, 3), Fraction(0))
    declaration = declaration_from_bundle(build_bundle(polytope_toy()))
    floors = acceptance_floors(replace_acceptance(declaration, data))
    assert floors is not None
    floor = floors["chat0"]
    # Sound: every q in the declared set satisfies q(chat0) >= floor.
    assert Fraction(floor) <= Fraction(1, 3)
    # And no weaker than it must be: the largest machine number that is.
    assert Fraction(math.nextafter(floor, math.inf)) > Fraction(1, 3)
    assert floors["chat1"] == 0.0


@pytest.mark.contract
def test_the_acceptance_support_of_a_polytope_declaration_is_the_minimal_one() -> None:
    """``acceptance_support`` dispatches on the geometry and stays minimal."""
    declaration = declaration_from_bundle(build_bundle(polytope_toy()))
    assert acceptance_support(declaration) == ("chat0", "chat1")
    assert minimal_acceptance_support(declaration) == ("chat0", "chat1")
    singleton = declaration_from_bundle(build_bundle(toy("TOY-8-T")))
    assert acceptance_support(singleton) == ("chat0", "chat1")


@pytest.mark.contract
def test_the_start_and_the_minimizer_are_the_hand_values_of_the_toy() -> None:
    """The toy's own derivation, checked against the oracle it describes."""
    declaration = declaration_from_bundle(build_bundle(polytope_toy()))
    oracle = acceptance_oracle(declaration)
    assert isinstance(oracle, PolytopeAcceptanceOracle)
    assert oracle.start() == POLYTOPE_START
    # A cost that prefers chat0 drives the LMO to the box cap; its mirror drives
    # it to the floor. Both are vertices of the declared segment.
    assert oracle.minimize({"chat0": -1.0, "chat1": 0.0}) == {
        "chat0": 0.75,
        "chat1": 0.25,
    }
    assert oracle.minimize({"chat0": 1.0, "chat1": 0.0}) == {
        "chat0": 0.25,
        "chat1": 0.75,
    }
    assert acceptance_start(declaration) == POLYTOPE_START


@pytest.mark.contract
def test_a_singleton_declaration_still_gets_the_singleton_oracle() -> None:
    """The cheaper route stays the cheaper route; the tag decides, not the data."""
    declaration = declaration_from_bundle(build_bundle(toy("TOY-8-T")))
    oracle = acceptance_oracle(declaration)
    assert isinstance(oracle, SingletonAcceptanceOracle)
    assert oracle.start() == {"chat0": 0.5, "chat1": 0.5}
    # Whatever the cost, the answer is the declared point -- so the direction is
    # identically zero and the driver's q block does not move.
    assert oracle.minimize({"chat0": -100.0, "chat1": 0.0}) == oracle.start()


# ===========================================================================
#  The wire format, and validation at the boundary.
# ===========================================================================


@pytest.mark.contract
def test_a_polytope_bundle_round_trips_and_validates() -> None:
    """The wire keys are statistics-acceptance's own, and no schema moved.

    The assertion is an exact version literal (``0.3.0``, the version the
    reader accepts, spec/architecture.md 2.9 §6), which is what makes "no
    schema moved" a check rather than a hope.
    """
    bundle = build_bundle(polytope_toy())
    block = bundle.manifest.payload.declaration.acceptance_set
    assert block.geometry == POLYTOPE
    assert set(block.data) == {"m_row", "B", "b", "box_bounds"}
    assert block.data["m_row"] == 4
    assert bundle.manifest.schema_version == "0.3.0"
    declaration = declaration_from_bundle(bundle)
    validate_declaration(declaration)
    data = polytope_of(declaration.acceptance_set)
    assert data is not None
    assert data.box_bounds == (BOX_LOWER, BOX_UPPER)
    assert data.m_row == 4


@pytest.mark.contract
def test_the_general_form_omits_box_bounds_and_still_validates() -> None:
    bundle = build_bundle(general_polytope_toy())
    block = bundle.manifest.payload.declaration.acceptance_set
    assert "box_bounds" not in block.data
    declaration = declaration_from_bundle(bundle)
    data = polytope_of(declaration.acceptance_set)
    assert data is not None and data.box_bounds is None


@pytest.mark.contract
@pytest.mark.parametrize(
    ("mutation", "fragment"),
    [
        ({"m_row": 3}, "contradicts itself"),
        ({"m_row": "four"}, "integer 'm_row'"),
        ({"B": "rows"}, "'B' list of rows"),
        ({"b": [0.75, 0.75, -0.25]}, "read positionally"),
        ({"box_bounds": [[0.25, 0.125]]}, "ordered pair"),
        ({"box_bounds": [[0.75, 0.75], [0.25, 0.125]]}, "0 <= q\\^- <= q\\^\\+"),
    ],
)
def test_a_malformed_polytope_payload_is_refused_at_the_boundary(
    mutation: dict, fragment: str
) -> None:
    """Every wire-level defect is a hard error, never a repair."""
    document, arrays = bundle_documents(polytope_toy())
    document["payload"]["declaration"]["acceptance_set"]["data"].update(mutation)
    with pytest.raises(DeclarationError, match=fragment):
        declaration_from_bundle(build(document, arrays))


@pytest.mark.contract
def test_an_empty_declared_polytope_is_refused_at_validation() -> None:
    """The refusal belongs upstream, and it names the check and its consequence."""
    document, arrays = bundle_documents(polytope_toy())
    # Caps that cannot carry the normalization: sum q^+ = 1/2 < 1.
    document["payload"]["declaration"]["acceptance_set"]["data"].update(
        {"b": [0.25, 0.25, 0.0, 0.0], "box_bounds": [[0.0, 0.0], [0.25, 0.25]]}
    )
    with pytest.raises(DeclarationError, match="EMPTY") as error:
        declaration_from_bundle(build(document, arrays))
    assert "h_low is +inf with no key-length claim" in str(error.value)
    # And it does not ATTRIBUTE the refusal to def:admissible-acceptance-set,
    # which an empty set SATISFIES -- it says the opposite in as many words.
    assert "satisfies def:admissible-acceptance-set" in str(error.value)
    assert not str(error.value).startswith("def:admissible-acceptance-set")


@pytest.mark.contract
def test_an_inverted_declared_box_is_refused_at_validation() -> None:
    """And refused as ILL-FORMED, not as empty: the two are not collapsed."""
    document, arrays = bundle_documents(polytope_toy())
    document["payload"]["declaration"]["acceptance_set"]["data"].update(
        {
            "b": [0.25, 0.75, -0.75, -0.125],
            "box_bounds": [[0.75, 0.125], [0.25, 0.75]],
        }
    )
    with pytest.raises(DeclarationError, match="not well formed") as error:
        declaration_from_bundle(build(document, arrays))
    assert "0 <= q^- <= q^+" in str(error.value)
    assert "EMPTY" not in str(error.value)


@pytest.mark.contract
def test_the_singleton_predicate_is_unchanged_by_the_widening() -> None:
    """The singleton checks fire, with their own messages."""
    declaration = declaration_from_bundle(build_bundle(toy("TOY-8-T")))
    negative = replace(
        declaration,
        acceptance_set=AcceptanceSet(geometry=SINGLETON, frequencies=(-0.25, 1.25)),
    )
    with pytest.raises(DeclarationError, match="negative"):
        validate_declaration(negative)
    unnormalized = replace(
        declaration,
        acceptance_set=AcceptanceSet(geometry=SINGLETON, frequencies=(0.25, 0.25)),
    )
    with pytest.raises(DeclarationError, match="def:admissible-acceptance-set"):
        validate_declaration(unnormalized)


# ===========================================================================
#  The linear program itself.
# ===========================================================================


@pytest.mark.contract
def test_the_program_refuses_shapes_that_do_not_match() -> None:
    with pytest.raises(ValueError, match="constraint matrix"):
        solve_standard_form([[Fraction(1), Fraction(1)]], [Fraction(1)], [Fraction(1)])


@pytest.mark.contract
def test_the_whole_simplex_is_the_zero_row_case() -> None:
    """``m_row = 0`` is admissible and denotes the simplex itself."""
    data = PolytopeData(columns=3, rows=(), rhs=())
    assert polytope_defect(data) is None
    optimum = acceptance_minimum([2.0, -1.0, 5.0], data)
    assert optimum is not None
    assert optimum.minimum == Fraction(-1)
    assert optimum.argmin == (Fraction(0), Fraction(1), Fraction(0))
    assert optimum.multipliers == ()
    witness = acceptance_witness([2.0, -1.0, 5.0], data)
    assert witness is not None
    assert witness.multipliers == () and witness.offset == 1.0
    assert witness.bound == Fraction(-1)


@pytest.mark.contract
def test_a_non_finite_cost_yields_no_minimum_rather_than_a_number() -> None:
    """A cost that is not a rational has no exact program to solve."""
    assert acceptance_minimum([float("nan"), 1.0], BOX) is None
    assert acceptance_witness([1.0, float("inf")], BOX) is None


@pytest.mark.contract
def test_the_multipliers_are_the_u_and_v_of_the_remark() -> None:
    """The sign identification, checked rather than asserted in a comment.

    Remark ``rem:acc-side`` (b) asks for ``u >= 0`` and ``v`` real with
    ``g + B^T u + v >= 0`` componentwise, and then ``-<b, u> - v`` is a lower
    bound. At an optimal basis the bound is TIGHT, which is the equality below.
    """
    cost = [3.0, -2.0]
    optimum = acceptance_minimum(cost, BOX)
    assert optimum is not None
    assert all(value >= 0 for value in optimum.multipliers)
    for column in range(BOX.columns):
        slack = Fraction(cost[column]) + optimum.offset
        for index, row in enumerate(BOX.rows):
            slack += Fraction(row[column]) * optimum.multipliers[index]
        assert slack >= 0, column
    bound = -optimum.offset
    for index, value in enumerate(optimum.multipliers):
        bound -= Fraction(BOX.rhs[index]) * value
    assert bound == optimum.minimum


@pytest.mark.contract
def test_an_infeasible_program_reports_infeasible_and_offers_no_dual() -> None:
    result = solve_standard_form(
        [[Fraction(1), Fraction(1)]], [Fraction(-1)], [Fraction(0), Fraction(0)]
    )
    assert result.status is LinearProgramStatus.INFEASIBLE
    assert result.primal == () and result.dual is None


@pytest.mark.contract
def test_the_verdict_of_a_declared_polytope_carries_its_defect() -> None:
    """The verdict type is what both validation and the certificate read."""
    declaration = declaration_from_bundle(build_bundle(polytope_toy()))
    assert acceptance_verdict(declaration).admissible
    empty = replace(
        declaration,
        acceptance_set=AcceptanceSet(
            geometry=POLYTOPE,
            polytope=PolytopeData(columns=2, rows=((1.0, 1.0),), rhs=(0.5,)),
        ),
    )
    verdict = acceptance_verdict(empty)
    assert verdict.defect is AcceptanceDefect.EMPTY
    assert not verdict.admissible
    missing = replace(
        declaration,
        acceptance_set=AcceptanceSet(geometry=POLYTOPE, polytope=None),
    )
    assert acceptance_verdict(missing).defect is AcceptanceDefect.ILL_FORMED
    for broken in (empty, missing):
        with pytest.raises(UnsupportedDeclarationError):
            acceptance_oracle(broken)


@pytest.mark.contract
def test_the_declared_acceptance_set_is_carried_without_a_second_source() -> None:
    """One slot per geometry, and the tag says which one is live."""
    singleton = AcceptanceSet(geometry=SINGLETON, frequencies=(0.5, 0.5))
    assert singleton.polytope is None
    assert np.array_equal(singleton.as_vector(), np.array([0.5, 0.5]))
    polytope = AcceptanceSet(geometry=POLYTOPE, polytope=BOX)
    assert polytope.frequencies == ()
    assert polytope_of(singleton) is None
    assert polytope_of(polytope) is BOX
    assert dict(POLYTOPE_ACCEPTANCE_SET)["m_row"] == BOX.m_row
