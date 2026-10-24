"""The measuring kernel of spec/architecture.md 2.9, on hand-computed defects.

Every expected number below is written down by hand from the definition in
that section's table, on a matrix small enough that the arithmetic is exact
in binary64.
Nothing here compares the kernel against another implementation in the tree:
the point of the kernel is that it REPLACES those, so agreeing with one would
prove nothing about the convention it is supposed to fix.
"""

from __future__ import annotations

import inspect
from typing import Any

import numpy as np
import pytest

from certiqs_key.foundations.numeric import (
    Aggregate,
    BlockMeasurement,
    column_residue,
    column_residue_by_block,
    completeness_residue,
    completeness_residue_by_block,
    hermitian_part,
    hermiticity_defect,
    hermiticity_defect_by_block,
    min_eigenvalue,
    min_eigenvalue_by_block,
    trace_residue,
    trace_residue_by_block,
)

#: Deliberately NOT Hermitian. ``a - a^dag`` is ``[[0, i], [i, 0]]``, whose
#: largest entrywise modulus is exactly 1.
NON_HERMITIAN = np.array([[1.0, 2.0 + 1.0j], [2.0, 1.0]], dtype=np.complex128)

#: Hermitian, eigenvalues 0 and 2, so ``min_eigenvalue`` is exactly 0.
RANK_ONE = np.array([[1.0, 1.0j], [-1.0j, 1.0]], dtype=np.complex128)

#: Hermitian and INDEFINITE: eigenvalues 1 and -1/4.
INDEFINITE = np.array([[1.0, 0.0], [0.0, -0.25]], dtype=np.float64)


# ---------------------------------------------------------------------------
#  hermiticity_defect
# ---------------------------------------------------------------------------


def test_the_hermiticity_defect_of_a_hermitian_matrix_is_exactly_zero():
    assert hermiticity_defect(RANK_ONE) == 0.0
    assert hermiticity_defect(np.eye(3)) == 0.0


def test_the_hermiticity_defect_is_the_largest_entrywise_modulus():
    """``a - a^dag = [[0, i], [i, 0]]``, so the entrywise maximum modulus is 1."""
    assert hermiticity_defect(NON_HERMITIAN) == 1.0


def test_a_real_non_symmetric_matrix_has_the_defect_of_its_skew_part():
    """``[[0, 1], [0, 0]]`` minus its transpose is ``[[0, 1], [-1, 0]]``."""
    assert hermiticity_defect(np.array([[0.0, 1.0], [0.0, 0.0]])) == 1.0


def test_the_defect_is_entrywise_and_not_spectral():
    """The two conventions differ, and the ADR names the entrywise one.

    ``a - a^dag`` here is ``i`` times the all-ones 2x2 matrix: every entry has
    modulus 1, and its spectral norm is 2. The kernel must return 1.
    """
    a = np.array([[1.0j, 1.0j], [1.0j, 1.0j]], dtype=np.complex128) / 2.0
    assert hermiticity_defect(a) == 1.0
    assert float(np.linalg.norm(a - a.conj().T, ord=2)) == pytest.approx(2.0)


# ---------------------------------------------------------------------------
#  min_eigenvalue
# ---------------------------------------------------------------------------


def test_the_smallest_eigenvalue_of_an_indefinite_matrix_is_negative():
    assert min_eigenvalue(INDEFINITE) == pytest.approx(-0.25, abs=1e-15)


def test_the_smallest_eigenvalue_is_taken_of_the_hermitian_part():
    """``[[0, 2], [0, 0]]`` has both eigenvalues 0; its Hermitian part has -1.

    The measurement is of the Hermitian part, so the answer is -1 and not 0.
    An eigenvalue of a non-Hermitian matrix is not a real number and there is
    nothing to compare against ``-tau``.
    """
    a = np.array([[0.0, 2.0], [0.0, 0.0]])
    assert float(np.linalg.eigvals(a).real.min()) == 0.0
    assert min_eigenvalue(a) == pytest.approx(-1.0, abs=1e-15)


def test_a_rank_deficient_projector_sits_exactly_on_the_boundary():
    assert min_eigenvalue(RANK_ONE) == pytest.approx(0.0, abs=1e-15)


# ---------------------------------------------------------------------------
#  completeness_residue -- a family whose residue is written down
# ---------------------------------------------------------------------------


def test_a_family_summing_to_the_identity_has_residue_exactly_zero():
    family = [
        np.array([[0.5, 0.25], [0.25, 0.5]]),
        np.array([[0.5, -0.25], [-0.25, 0.5]]),
    ]
    assert completeness_residue(family) == 0.0


def test_the_completeness_residue_is_the_largest_entry_of_the_defect():
    """``sum_v F_v = diag(1, 3/4)``, so ``sum_v F_v - 1 = diag(0, -1/4)``."""
    family = [
        np.array([[1.0, 0.0], [0.0, 0.0]]),
        np.array([[0.0, 0.0], [0.0, 0.75]]),
    ]
    assert completeness_residue(family) == 0.25


def test_an_off_diagonal_completeness_defect_is_seen():
    """The residue is entrywise, so an off-diagonal excess counts."""
    family = [np.array([[1.0, 0.125], [0.125, 1.0]])]
    assert completeness_residue(family) == 0.125


def test_a_single_element_family_is_measured_against_the_identity():
    assert completeness_residue([np.eye(4)]) == 0.0


# ---------------------------------------------------------------------------
#  column_residue and trace_residue
# ---------------------------------------------------------------------------


def test_the_column_residue_is_the_worst_column():
    """Column sums are 1 and 5/4, so the residue is 1/4."""
    m = np.array([[0.5, 0.25], [0.25, 0.5], [0.25, 0.5]])
    assert column_residue(m) == 0.25


def test_a_column_stochastic_matrix_has_residue_exactly_zero():
    assert column_residue(np.array([[0.5, 1.0], [0.5, 0.0]])) == 0.0


def test_the_column_residue_admits_a_rectangular_matrix():
    """A coarse-graining maps one alphabet into another and is not square."""
    assert column_residue(np.array([[1.0, 1.0, 1.0]])) == 0.0


def test_the_trace_residue_is_the_distance_of_the_trace_from_one():
    assert trace_residue(np.array([[0.5, 0.0], [0.0, 0.25]])) == 0.25
    assert trace_residue(np.eye(2) / 2.0) == 0.0


def test_the_trace_residue_reads_a_complex_trace_as_a_modulus():
    """A non-Hermitian argument may have a complex trace; the residue is its modulus."""
    a = np.array([[1.0 + 0.25j, 0.0], [0.0, 0.0]], dtype=np.complex128)
    assert trace_residue(a) == 0.25


# ---------------------------------------------------------------------------
#  The kernel never mutates and never decides
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "measure",
    [hermiticity_defect, min_eigenvalue, trace_residue, column_residue],
)
def test_no_measurement_modifies_its_argument(measure: Any):
    """spec/architecture.md 2.9: no function here modifies its input."""
    a = NON_HERMITIAN.copy()
    before = a.copy()
    measure(a)
    assert np.array_equal(a, before)


def test_completeness_does_not_modify_the_family():
    family = [np.eye(2) / 2.0, np.eye(2) / 3.0]
    before = [element.copy() for element in family]
    completeness_residue(family)
    for element, original in zip(family, before, strict=True):
        assert np.array_equal(element, original)


def test_the_hermitian_part_is_offered_but_is_not_a_measurement():
    """It returns a matrix, and the argument it was given is untouched."""
    a = NON_HERMITIAN.copy()
    part = hermitian_part(a)
    assert np.array_equal(a, NON_HERMITIAN)
    assert hermiticity_defect(part) == 0.0
    assert part[0, 1] == pytest.approx(2.0 + 0.5j)


def test_no_kernel_function_accepts_a_tolerance():
    """The signatures are the control: a tolerance argument would be a decision."""
    for measure in (
        hermiticity_defect,
        min_eigenvalue,
        completeness_residue,
        column_residue,
        trace_residue,
        hermiticity_defect_by_block,
        min_eigenvalue_by_block,
        completeness_residue_by_block,
        column_residue_by_block,
        trace_residue_by_block,
    ):
        names = set(inspect.signature(measure).parameters)
        assert not names & {"tolerance", "tau", "eps", "eps_op"}, measure.__name__


# ---------------------------------------------------------------------------
#  Argument faults are hard errors, and none of them is a tolerance decision
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("measure", [hermiticity_defect, min_eigenvalue, trace_residue])
def test_a_non_square_argument_is_refused(measure: Any):
    with pytest.raises(ValueError, match="square"):
        measure(np.ones((2, 3)))


@pytest.mark.parametrize("measure", [hermiticity_defect, column_residue])
def test_a_one_dimensional_argument_is_refused(measure: Any):
    with pytest.raises(ValueError, match="2-D"):
        measure(np.ones(3))


@pytest.mark.parametrize("measure", [hermiticity_defect, column_residue])
def test_an_empty_argument_is_refused(measure: Any):
    with pytest.raises(ValueError, match="zero-dimensional"):
        measure(np.zeros((0, 0)))


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_a_non_finite_entry_is_refused_because_nan_passes_every_tolerance(bad: float):
    """A NaN defect compares ``False`` against ``> tau`` and would sail through."""
    a = np.array([[1.0, 0.0], [0.0, bad]])
    with pytest.raises(ValueError, match="non-finite"):
        hermiticity_defect(a)
    assert not float("nan") > 1e-9


def test_an_integer_array_is_refused():
    with pytest.raises(ValueError, match="dtype"):
        hermiticity_defect(np.array([[1, 0], [0, 1]]))


def test_an_empty_family_has_no_completeness_to_measure():
    with pytest.raises(ValueError, match="non-empty family"):
        completeness_residue([])


def test_a_ragged_family_is_refused():
    with pytest.raises(ValueError, match="one dimension"):
        completeness_residue([np.eye(2), np.eye(3)])


# ---------------------------------------------------------------------------
#  The block-wise wrappers -- a refusal must be able to name the block
# ---------------------------------------------------------------------------


def test_a_block_wise_wrapper_returns_the_vector_and_names_the_worst_block():
    measurement = hermiticity_defect_by_block(
        {"s0": np.eye(2), "s1": NON_HERMITIAN, "s2": np.eye(2)}
    )
    assert isinstance(measurement, BlockMeasurement)
    assert measurement.per_block == {"s0": 0.0, "s1": 1.0, "s2": 0.0}
    assert measurement.worst_block == "s1"
    assert measurement.worst == 1.0
    assert measurement.aggregate is Aggregate.MAXIMUM


def test_the_min_eigenvalue_wrapper_aggregates_by_MINIMUM():
    """The one wrapper whose worst case is the smallest and not the largest.

    A caller compares the smallest eigenvalue over the blocks against ``-tau``;
    reporting the maximum would report the block furthest from failing.
    """
    measurement = min_eigenvalue_by_block({"s0": np.eye(2), "s1": INDEFINITE})
    assert measurement.aggregate is Aggregate.MINIMUM
    assert measurement.worst_block == "s1"
    assert measurement.worst == pytest.approx(-0.25, abs=1e-15)


def test_a_tie_is_broken_by_the_order_the_blocks_were_given():
    """Determinism: a refusal names the same block on every run."""
    blocks = {"s2": NON_HERMITIAN, "s0": NON_HERMITIAN}
    assert hermiticity_defect_by_block(blocks).worst_block == "s2"
    assert hermiticity_defect_by_block(dict(reversed(blocks.items()))).worst_block == (
        "s0"
    )


def test_the_completeness_wrapper_is_keyed_by_block_and_indexed_by_outcome():
    families = {
        "s0": [np.array([[0.5]]), np.array([[0.5]])],
        "s1": [np.array([[0.25]]), np.array([[0.5]])],
    }
    measurement = completeness_residue_by_block(families)
    assert measurement.per_block == {"s0": 0.0, "s1": 0.25}
    assert measurement.worst_block == "s1"


def test_the_remaining_wrappers_aggregate_by_maximum():
    columns = column_residue_by_block(
        {"s0": np.array([[1.0]]), "s1": np.array([[0.75]])}
    )
    assert columns.worst_block == "s1"
    assert columns.worst == 0.25
    traces = trace_residue_by_block({"s0": np.eye(1), "s1": np.array([[0.5]])})
    assert traces.worst_block == "s1"
    assert traces.worst == 0.5


@pytest.mark.parametrize(
    "wrapper",
    [
        hermiticity_defect_by_block,
        min_eigenvalue_by_block,
        completeness_residue_by_block,
        column_residue_by_block,
        trace_residue_by_block,
    ],
)
def test_a_wrapper_given_no_blocks_is_refused(wrapper: Any):
    with pytest.raises(ValueError, match="no blocks"):
        wrapper({})


def test_a_block_measurement_serializes_for_a_run_record():
    record = hermiticity_defect_by_block({"s0": NON_HERMITIAN}).as_record()
    assert record == {
        "per_block": {"s0": 1.0},
        "aggregate": "maximum",
        "worst_block": "s0",
        "worst": 1.0,
    }
