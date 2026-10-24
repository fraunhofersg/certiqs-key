"""The foundations definitions the domain code decides as stated.

Every expected value is derived by hand in
the comment beside it from the claim it tests; none is computed by the code
under test.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

import numpy as np
import pytest
from tests.support.declared_optical_documents import template_tree
from tests.support.lowered_templates import wcp_source as prepare_source

from certiqs_key.foundations.blocks import BlockKind, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    BINARY64_OVERFLOW_THRESHOLD,
    Cx,
    identity,
    round_to_binary64,
    sum_in_declared_order,
)
from certiqs_key.foundations.exact_admission import (
    ExactInputError,
    admit_family_exact,
    sum_rounds_nowhere,
    to_exact,
)
from certiqs_key.foundations.snap import (
    SnapPredicate,
    SnapRefusedError,
    is_on_lattice,
    snap_family_exact,
    snap_to_lattice,
)
from certiqs_key.protocol_compiler.reasons import RefusalReason
from certiqs_key.protocol_compiler.spec import Party, PublicChoices
from certiqs_key.protocol_compiler.weights import weighted_family

#: Decoy BB84's source lattice, ``2^-24``: the template's ``lattice_exponent``.
SOURCE_LATTICE = template_tree("decoy_bb84")["source"]["lattice_exponent"]
assert SOURCE_LATTICE == 24

#: def:binary64 (i): the largest element of B, m = 2^53 - 1 at q = 971.
_MAX = F(((1 << 53) - 1) << 971)
#: def:binary64 (ii): the overflow threshold 2^1024 - 2^970, the midpoint of
#: _MAX and 2^1024 (2^1024 - _MAX = 2^971, half of it 2^970).
_THRESHOLD = F((1 << 1024) - (1 << 970))


# ---------------------------------------------------------------------------
#  (1) def:binary64 (ii) and def:declared-order: overflow is a value
# ---------------------------------------------------------------------------


def test_the_overflow_threshold_is_the_one_def_binary64_states() -> None:
    assert BINARY64_OVERFLOW_THRESHOLD == _THRESHOLD
    assert _MAX + F(1 << 970) == _THRESHOLD


@pytest.mark.parametrize(
    ("value", "rounded"),
    [
        # An element of B is its own fl (def:binary64 (ii), last property).
        (_MAX, _MAX),
        # Below the threshold, nearest is _MAX: the next candidate is 2^1024.
        (_THRESHOLD - 1, _MAX),
        # At and beyond the threshold, a signed infinity.
        (_THRESHOLD, math.inf),
        (-_THRESHOLD, -math.inf),
        (2 * _MAX, math.inf),
        (-2 * _MAX, -math.inf),
        # fl(+-inf + y) = +-inf.
        (math.inf, math.inf),
        (-math.inf, -math.inf),
    ],
)
def test_round_to_binary64_maps_overflow_to_a_signed_infinity(
    value: F | float, rounded: F | float
) -> None:
    assert round_to_binary64(value) == rounded


def test_a_sum_that_overflows_does_not_round_nowhere_and_does_not_raise() -> None:
    """def:declared-order: [[MAX]] + [[MAX]]: the second addition overflows.

    MAX + MAX = 2^1025 - 2^972 >= the threshold, so fl gives +inf; the
    addition is not exact, so the accumulation does not round nowhere, and
    element 2 is the first inexact one (element 1's addition, 0 + MAX, is
    exact).
    """
    term = ((Cx(_MAX, F(0)),),)
    verdict = sum_in_declared_order([term, term])
    assert verdict.rounds_nowhere is False
    assert verdict.first_inexact_index == 2
    assert verdict.inexact_sites == ((2, 0),)
    assert verdict.computed_total is None
    assert not verdict.computed_total_equals(((Cx(2 * _MAX, F(0)),),))
    # The exact total is still the sum of the declared numbers.
    assert verdict.total == ((Cx(2 * _MAX, F(0)),),)


def test_a_sum_past_an_overflow_stays_infinite_and_inexact() -> None:
    """fl(+inf + y) = +inf: the addition after the overflow is inexact too.

    Terms MAX, MAX, -MAX: the exact partial sums are MAX, 2 MAX, MAX, but the
    computed second one is +inf, so the third addition starts from an
    infinite partial sum and is not exact either (def:declared-order asks
    every entry of the previous computed sum to be finite).
    """
    plus = ((Cx(_MAX, F(0)),),)
    minus = ((Cx(-_MAX, F(0)),),)
    verdict = sum_in_declared_order([plus, plus, minus])
    assert verdict.inexact_sites == ((2, 0), (3, 0))
    assert verdict.computed_total is None
    assert verdict.total == plus


def test_the_admission_boundary_reports_the_overflow_rather_than_raising() -> None:
    maximum = float(_MAX)
    blocks = [np.array([[maximum]]), np.array([[maximum]])]
    assert sum_rounds_nowhere(blocks).ok is False
    admission = admit_family_exact(blocks)
    assert admission.rounds_nowhere.ok is False
    assert "declared_order_sum" in admission.failures


def test_an_overflowing_weight_sum_is_refused_not_raised() -> None:
    """The compiler's weight sum: MAX + MAX is no binary64 number, and not 1.

    Weights (MAX, MAX, 1/2) are binary64 and positive, so they reach the
    accumulation. req:weight-list decides it on the declared numbers: the
    second addition rounds (to +inf) and the exact sum is not 1, so the list
    is refused with ``choice_weights_not_normalized`` -- a refusal record,
    never an OverflowError (not malformed input on its computed total).
    """
    labels = ("a", "b", "c")
    choices = PublicChoices(
        party=Party.ALICE,
        choices=labels,
        weights=dict(zip(labels, (_MAX, _MAX, F(1, 2)), strict=True)),
        conditional_alphabets=dict.fromkeys(labels, ("only",)),
        conditional_elements={label: {"only": identity(1)} for label in labels},
        joint_labels={("only", label): label for label in labels},
    )
    family = weighted_family(choices)
    assert family.refusal is not None
    assert family.refusal.reason is RefusalReason.CHOICE_WEIGHTS_NOT_NORMALIZED
    assert "addition 2" in family.refusal.detail


def test_a_finite_sum_keeps_its_computed_total() -> None:
    """The 0.9/0.1 case the SummationVerdict docstring names, unchanged.

    fl(0.9) + fl(0.1) in binary64 is exactly 1.0 although the exact sum of
    the two declared numbers is not 1 (0.9 and 0.1 are not dyadic, their
    binary64 values err in opposite directions by less than half an ulp of 1).
    """
    a = ((Cx(F(0.9), F(0)),),)
    b = ((Cx(F(0.1), F(0)),),)
    verdict = sum_in_declared_order([a, b])
    assert verdict.computed_total_equals(identity(1))
    assert verdict.rounds_nowhere is False


# ---------------------------------------------------------------------------
#  (2) def:sector-map: S non-empty, d_s >= 1
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dims", [(0,), (-2,), (2, 0)])
def test_a_sector_of_dimension_below_one_is_refused(dims: tuple[int, ...]) -> None:
    labels = tuple(f"s{index}" for index in range(len(dims)))
    with pytest.raises(MalformedInputError, match="d_s >= 1"):
        SectorStructure(labels=labels, dims=dims, block_kind=BlockKind.NUMERICAL_BLOCK)


def test_an_empty_sector_map_is_refused() -> None:
    with pytest.raises(MalformedInputError, match="non-empty"):
        SectorStructure(labels=(), dims=(), block_kind=BlockKind.NUMERICAL_BLOCK)


def test_a_sector_of_dimension_one_is_a_sector() -> None:
    structure = SectorStructure(
        labels=("s0",), dims=(1,), block_kind=BlockKind.NUMERICAL_BLOCK
    )
    assert structure.total_dim == 1


# ---------------------------------------------------------------------------
#  (3) req:declared-lattice: the modulus bound is on each PART
# ---------------------------------------------------------------------------


def test_a_complex_entry_with_both_parts_on_the_lattice_is_on_it() -> None:
    """0.75 + 0.75i at k = 2: each part is 3 * 2^-2 and at most 1 in modulus.

    Its modulus is 0.75 * sqrt 2 > 1, which req:declared-lattice does not
    bound: "the real and the imaginary part of the entry are integer
    multiples of 2^-k and have modulus at most 1".
    """
    entry = np.array([[0.75 + 0.75j]])
    assert is_on_lattice(entry, lattice_exponent=2)
    snapped, record = snap_to_lattice(
        entry, lattice_exponent=2, tolerance=0.0, site="s"
    )
    assert np.array_equal(snapped, entry)
    assert record.detail["entries_moved"] == 0


@pytest.mark.parametrize("value", [1.5 + 0j, 0.5 + 1.25j, -1.25 + 0j])
def test_a_part_of_modulus_above_one_is_off_the_lattice_and_refused(
    value: complex,
) -> None:
    entry = np.array([[value]])
    assert not is_on_lattice(entry, lattice_exponent=2)
    with pytest.raises(SnapRefusedError) as caught:
        snap_to_lattice(entry, lattice_exponent=2, tolerance=1.0, site="s")
    assert caught.value.reason == "part_modulus_above_one"
    assert caught.value.predicate is SnapPredicate.LATTICE


# ---------------------------------------------------------------------------
#  (4) def:exact-admissibility: (C) with a declared constant c
# ---------------------------------------------------------------------------


def test_completeness_is_decided_against_the_declared_constant() -> None:
    """(C): 1/4 + 1/4 = 1/2, so the family is complete with c = 1/2 only."""
    blocks = [np.array([[0.25]]), np.array([[0.25]])]
    with_half = admit_family_exact(blocks, constant=F(1, 2))
    assert with_half.admissible
    assert with_half.constant == F(1, 2)
    assert with_half.as_record()["constant"] == "1/2"
    at_one = admit_family_exact(blocks)
    assert not at_one.complete
    # The residue against 1 is 1/2, squared 1/4.
    assert at_one.completeness_residue_squared == F(1, 4)


def test_the_constant_is_a_declared_value() -> None:
    """def:exact-admissibility: c is a declared value, a binary64 number."""
    with pytest.raises(ExactInputError, match="constant"):
        admit_family_exact([np.array([[1.0]])], constant=F(1, 3))


# ---------------------------------------------------------------------------
#  (5) def:snap: the displacement is from the input to the output
# ---------------------------------------------------------------------------


def test_the_snap_records_its_displacement_from_the_input() -> None:
    """def:snap: "the largest entrywise modulus of D' - D".

    Input (0.3, 0.6) at k = 2, tolerance 0.2 (completeness defect 0.1). The
    lattice step alone moves 0.3 -> 0.25 and 0.6 -> 0.5 (the nearest
    multiples of 1/4), a step displacement of 0.1; the absorb then adds the
    residue 1/4 to the designated element, so the returned family is either
    (0.5, 0.5) or (0.25, 0.75), and the move from the input is 0.2 or 0.15.
    Either way it exceeds the lattice step's 0.1, which is what the record
    reported as the displacement.
    """
    family = [np.array([[0.3]]), np.array([[0.6]])]
    snapped, records = snap_family_exact(
        family, tolerance=0.2, lattice_exponent=2, site="s"
    )
    expected = max(
        abs(to_exact(after)[0][0].re - to_exact(before)[0][0].re)
        for before, after in zip(family, snapped, strict=True)
    )
    assert expected in (F(0.5) - F(0.3), F(0.75) - F(0.6))
    assert records
    for record in records:
        assert record.detail["snap_displacement_squared"] == str(expected * expected)
        assert record.detail["snap_displacement"] == pytest.approx(float(expected))
    (lattice,) = [r for r in records if r.predicate is SnapPredicate.LATTICE]
    assert lattice.detail["displacement"] < records[0].detail["snap_displacement"]


def test_the_snap_displacement_of_a_hand_pinned_case() -> None:
    """def:snap on dyadic data, every step fixed by hand; displacement 3/8.

    Input (1/8, 5/8) at k = 2, tolerance 1/4 (completeness defect exactly
    1/4). Lattice, ties to even on 4x: 1/2 -> 0 and 5/2 -> 2, giving
    (0, 1/2), a step displacement of 1/8. The designated element is the one
    of largest exact trace that is not zero: element 1 (1/2). It absorbs the
    residue 1 - 1/2 = 1/2, so the output is (0, 1), PSD, no lift. The
    displacement from the input: max(|0 - 1/8|, |1 - 5/8|) = 3/8.
    """
    family = [np.array([[0.125]]), np.array([[0.625]])]
    snapped, records = snap_family_exact(
        family, tolerance=0.25, lattice_exponent=2, site="s"
    )
    assert [float(a[0, 0]) for a in snapped] == [0.0, 1.0]
    (completeness,) = [r for r in records if r.predicate is SnapPredicate.COMPLETENESS]
    assert completeness.detail["designated_element"] == 1
    (lattice,) = [r for r in records if r.predicate is SnapPredicate.LATTICE]
    assert lattice.detail["displacement"] == 0.125
    for record in records:
        assert record.detail["snap_displacement_squared"] == "9/64"
        assert record.detail["snap_displacement"] == 0.375


def test_a_snap_that_moves_nothing_returns_no_record() -> None:
    family = [np.array([[0.25]]), np.array([[0.75]])]
    snapped, records = snap_family_exact(
        family, tolerance=0.0, lattice_exponent=2, site="s"
    )
    assert records == ()
    assert all(np.array_equal(a, b) for a, b in zip(family, snapped, strict=True))


# ---------------------------------------------------------------------------
#  (7) req:declared-tolerance, second paragraph: the decoy category vector
# ---------------------------------------------------------------------------


def test_the_decoy_category_vector_is_prepared_by_the_input_rule() -> None:
    """The exact products are the inputs: closed-point cells, defect 0.

    gamma = 1/2 and test probabilities (1/2, 1/2) give the category vector
    (1/2, 1/4, 1/4), exactly normalised and on the 2^-24 grid, so the
    admission ground is the declared tolerance and nothing moves.
    """
    source = prepare_source(
        intensities={"signal": 0.5, "weak": 0.1},
        test_intensity_probabilities=[F(1, 2), F(1, 2)],
        gamma=F(1, 2),
    )
    categories = source.record["categories"]
    assert categories["site"] == "decoy.source_category_lattice"
    assert categories["input_values"] == ["1/2", "1/4", "1/4"]
    assert categories["prepared_values"] == ["1/2", "1/4", "1/4"]
    assert categories["normalization_defect"] == "0"
    assert categories["admission"] == "declared_tolerance"
    assert categories["lattice_exponent"] == SOURCE_LATTICE
    assert all(
        cell["lower"] == cell["upper"] and cell["endpoints_closed"]
        for cell in categories["rounding_cells"]
    )


def test_the_decoy_category_masses_stay_on_the_24_bit_grid() -> None:
    """The snap puts the category masses on 2^-24, as the module needs.

    Products of two 24-bit values have 48-bit denominators, and the module
    docstring's no-rounding argument needs the masses on 2^-24, so they are
    snapped although the products are binary64 and sum to 1 exactly.

    gamma = 0.1 -> coin (1 - g24, g24) with g24 a multiple of 2^-24; test
    probabilities 0.1, 0.3, 0.6 likewise; their products are multiples of
    2^-48 and in general not of 2^-24.
    """
    source = prepare_source(
        intensities={"signal": 0.8, "weak": F(1, 5), "vacuum": 0},
        test_intensity_probabilities=[0.1, 0.3, 0.6],
        gamma=0.1,
    )
    prepared = [F(value) for value in source.record["categories"]["prepared_values"]]
    assert sum(prepared) == 1
    assert all((value * (1 << SOURCE_LATTICE)).denominator == 1 for value in prepared)
    inputs = [F(value) for value in source.record["categories"]["input_values"]]
    assert any((value * (1 << SOURCE_LATTICE)).denominator != 1 for value in inputs)
