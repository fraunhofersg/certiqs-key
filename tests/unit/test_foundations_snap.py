"""The snapping table of spec/architecture.md 2.9, by its INVARIANTS.

The table does not merely *reduce* a defect; it
**produces exact admissibility** or refuses. So the invariants this file
carries are the ones a later reader of a run record, and every consumer
downstream, is entitled to assume:

1. what comes back is **exactly** admissible -- exactly Hermitian, exactly
   positive semidefinite (decided by ``is_psd_exact``, never by an eigenvalue),
   exactly complete, on the declared ``2^-k`` lattice, and with the
   declared-order completeness sum rounding nowhere in binary64;
2. an exactly-zero element stays **exactly** zero, and is never the designated
   element that absorbs the completeness residue;
3. a snap whose measured PRE-SNAP defect exceeds the declared tolerance is
   **not performed**: the function raises and the caller refuses;
4. every record's ``defect`` is the number the binary64 KERNEL measures on the
   un-snapped object, so the record is auditable against ``foundations/numeric.py``
   and not only against itself -- and everything that is not a ``float``
   (the lattice exponent, the designated element, the lift weight, which
   number decided) lives in ``detail``.

Positivity IS in the table, and the reason is asserted here
rather than left as a gap: a consumer decides it exactly, so there is no
tolerance window left for a rounding to pass through.
"""

from __future__ import annotations

import json
from fractions import Fraction

import numpy as np
import pytest

from certiqs_key.foundations import snap as snap_module
from certiqs_key.foundations.exact_admission import (
    admit_family_exact,
    is_hermitian_exact,
    is_psd_exact,
    sum_rounds_nowhere,
)
from certiqs_key.foundations.numeric import (
    column_residue,
    completeness_residue,
    hermiticity_defect,
    min_eigenvalue,
)
from certiqs_key.foundations.snap import (
    LIFT_LADDER,
    REFUSAL_REASONS,
    SnapPredicate,
    SnapRecord,
    SnapRefusedError,
    SnapRule,
    SnapSettings,
    designated_element_index,
    dyadic_uniform_weights,
    is_on_lattice,
    snap_column_stochasticity,
    snap_completeness,
    snap_family_exact,
    snap_forbidden_entries,
    snap_hermiticity,
    snap_measurement_family,
    snap_positivity,
    snap_to_lattice,
    verify_family_exact,
)

#: The lattice spec/architecture.md 2.9 fixes, as measured. Never a default in
#: the module; always passed.
K = 40

#: Hermiticity defect exactly 1: ``a - a^dag = [[0, i], [i, 0]]``.
NON_HERMITIAN = np.array([[1.0, 2.0 + 1.0j], [2.0, 1.0]], dtype=np.complex128)


def one_ulp_family() -> list[np.ndarray]:
    """Return the family the trace-weight rule cannot close.

    ``0.06 + 0.57 + 0.37`` is ``1 - 1.11e-16`` in binary64: the pre-snap
    completeness residue is the ADR's measured post-snap number, and the
    trace-weight rule makes it WORSE rather than closing it (asserted below).
    """
    return [np.array([[0.06]]), np.array([[0.57]]), np.array([[0.37]])]


def trace_weight_snap(family: list[np.ndarray]) -> list[np.ndarray]:
    """Return what the trace-weight completeness rule produces.

    Reproduced here rather than imported, because the module does not offer
    it: it is what this file's first test measures the new rule AGAINST.
    """
    total = family[0]
    for element in family[1:]:
        total = total + element
    residue = np.eye(total.shape[0]) - total
    traces = [float(np.trace(element).real) for element in family]
    mass = sum(traces)
    return [
        element + (trace / mass) * residue
        for element, trace in zip(family, traces, strict=True)
    ]


def rank_one_family() -> list[np.ndarray]:
    """Return a complex family whose first element is a rank-one projector.

    ``vv^dag`` for a dyadic ``v`` is exactly positive semidefinite and
    ``numpy.linalg.eigvalsh`` reports a slightly NEGATIVE smallest eigenvalue
    for it. That disagreement was once attributed to a non-dyadic lift weight.
    """
    v = np.array([[0.25 + 0.5j], [0.5 - 0.125j]], dtype=np.complex128)
    projector = v @ v.conj().T
    return [projector, np.eye(2, dtype=np.complex128) - projector]


def indefinite_by_a_rounding() -> list[np.ndarray]:
    """Return a lattice family whose first element misses the cone by ``2^-38``.

    Every entry is already an integer multiple of ``2^-40``, so the lattice
    step cannot repair it and the positivity lift has to. The determinant is
    ``-2^-39``, so ``is_psd_exact`` refuses it exactly.
    """
    epsilon = 2.0**-38
    element = np.array([[0.5, 0.5], [0.5, 0.5 - epsilon]])
    return [element, np.eye(2) - element]


def indefinite_and_incomplete() -> list[np.ndarray]:
    """Return the same family with a completeness residue of ``1e-13`` on top.

    Exercises the completeness absorb and the positivity lift in one call, so
    that both records exist to be read.
    """
    epsilon = 2.0**-38
    first = np.array([[0.5, 0.5], [0.5, 0.5 - epsilon]])
    second = np.array([[0.5, -0.5], [-0.5, 0.5 + epsilon + 1e-13]])
    return [first, second]


def genuinely_indefinite() -> list[np.ndarray]:
    """Return a family no rung can lift: the defect is not a rounding."""
    element = np.array([[0.5, 0.5], [0.5, 0.0]])
    return [element, np.eye(2) - element]


def assert_exactly_admissible(family: tuple[np.ndarray, ...], lattice: int) -> None:
    """Assert every condition the rewritten table promises of its output."""
    admission = admit_family_exact(list(family))
    assert admission.admissible, admission.failures
    assert admission.hermitian
    assert admission.positive_semidefinite
    assert admission.complete
    assert admission.completeness_residue_squared == 0
    assert sum_rounds_nowhere(list(family)).ok
    for element in family:
        assert is_hermitian_exact(element)
        assert is_psd_exact(element)
        assert is_on_lattice(element, lattice_exponent=lattice)


# ---------------------------------------------------------------------------
#  1. Completeness: exact, into ONE designated element
# ---------------------------------------------------------------------------


def test_the_trace_weight_rule_cannot_close_this_family():
    """spec/architecture.md 2.9's premise, measured here rather than quoted.

    The section 3 rule "reduces the residue; it does not close it", because the
    corrected sum re-rounds. On this family it does not even reduce it.
    """
    family = one_ulp_family()
    assert completeness_residue(family) == pytest.approx(1.11e-16, rel=1e-2)
    assert completeness_residue(trace_weight_snap(family)) > 0.0


def test_a_family_the_trace_weight_rule_leaves_at_a_residue_sums_exactly_to_one():
    family = one_ulp_family()
    snapped, records = snap_family_exact(
        family, tolerance=1e-12, lattice_exponent=K, site="bob_povm", block="m0"
    )
    assert completeness_residue(snapped) == 0.0
    assert_exactly_admissible(snapped, K)

    completeness = [
        record for record in records if record.predicate is SnapPredicate.COMPLETENESS
    ]
    assert len(completeness) == 1
    record = completeness[0]
    assert record.rule is SnapRule.ABSORB_INTO_DESIGNATED_ELEMENT
    assert record.defect == completeness_residue(family)
    # 0.57 carries the largest exact trace, so it is the designated element.
    assert record.detail["designated_element"] == 1
    # An exact rational, rendered as a string: putting it in the record as a
    # float would restore the rounding this table exists to remove.
    trace = Fraction(record.detail["designated_element_trace"])
    assert float(trace) == pytest.approx(0.57, abs=2.0**-40)
    assert record.detail["lattice_exponent"] == K


def test_the_designated_element_is_the_one_of_largest_exact_trace():
    family = [
        np.array([[0.25, 0.0], [0.0, 0.125]]),
        np.array([[0.5, 0.0], [0.0, 0.75]]),
        np.array([[0.25, 0.0], [0.0, 0.125]]),
    ]
    assert designated_element_index(family) == 1


def test_ties_in_the_exact_trace_break_by_the_declared_order():
    family = [np.eye(2) * 0.5, np.eye(2) * 0.5]
    assert designated_element_index(family) == 0


def test_a_structurally_zero_element_is_never_designated():
    """THE property spec/architecture.md 2.9 constraint (1) requires be kept.

    An outcome that cannot occur in a photon-number block must come back
    exactly zero. Under the old trace-weight rule that fell out of a zero
    weight; under this rule it is the designated-element choice that carries
    it, so the choice is what is asserted.
    """
    family = [
        np.zeros((2, 2)),
        np.array([[0.06, 0.0], [0.0, 0.5]]),
        np.array([[0.94, 0.0], [0.0, 0.5]]),
    ]
    assert designated_element_index(family) == 2
    snapped, _ = snap_family_exact(
        family, tolerance=1e-12, lattice_exponent=K, site="bob_povm"
    )
    assert np.array_equal(snapped[0], np.zeros((2, 2)))
    assert not snapped[0].any()
    assert_exactly_admissible(snapped, K)


def test_a_zero_trace_element_is_preferred_over_a_structurally_zero_one():
    """The rule excludes the zero ELEMENT, not merely the zero trace."""
    family = [np.zeros((2, 2)), np.array([[0.0, 0.5], [0.5, 0.0]])]
    assert designated_element_index(family) == 1


def test_a_family_of_only_zero_elements_has_no_designated_element():
    with pytest.raises(SnapRefusedError) as caught:
        designated_element_index([np.zeros((2, 2)), np.zeros((2, 2))])
    assert caught.value.reason == "no_designated_element"
    assert caught.value.predicate is SnapPredicate.COMPLETENESS


def test_snap_completeness_requires_its_input_on_the_declared_lattice():
    """The table's order is lattice, THEN completeness, and it is enforced."""
    family = one_ulp_family()
    with pytest.raises(ValueError, match="multiple of 2\\^-40"):
        snap_completeness(family, tolerance=1e-12, lattice_exponent=K, site="bob_povm")


def test_snap_completeness_closes_the_residue_exactly_on_the_lattice():
    family = [
        np.array([[Fraction(3, 8) - Fraction(1, 2**40), 0.0], [0.0, 0.5]], dtype=float),
        np.array([[0.625, 0.0], [0.0, 0.5]]),
    ]
    snapped, record = snap_completeness(
        family, tolerance=1e-9, lattice_exponent=K, site="bob_povm", setting="t0"
    )
    assert completeness_residue(snapped) == 0.0
    assert record.rule is SnapRule.ABSORB_INTO_DESIGNATED_ELEMENT
    assert record.detail["residue_entries_moved"] == 1
    assert record.setting == "t0"


# ---------------------------------------------------------------------------
#  2. Positivity: decided exactly, never by an eigenvalue
# ---------------------------------------------------------------------------


def test_a_rank_deficient_block_the_eigenvalue_maligns_is_admitted_unlifted():
    """Misattributed once: the refusal was ``eigvalsh``, not a weight.

    ``is_psd_exact`` says PSD, ``numpy.linalg.eigvalsh`` says ``-8.3e-17``.
    The exact decision decides, so nothing is lifted -- and the record says so,
    because the disagreement is what spec/architecture.md 2.9 constraint (4) exists
    to make visible.
    """
    family = rank_one_family()
    assert min_eigenvalue(family[0]) < 0.0
    assert is_psd_exact(family[0])

    snapped, records = snap_family_exact(
        family, tolerance=1e-9, lattice_exponent=K, site="bob_povm"
    )
    assert np.array_equal(snapped[0], family[0])
    assert_exactly_admissible(snapped, K)

    positivity = [
        record for record in records if record.predicate is SnapPredicate.POSITIVITY
    ]
    assert len(positivity) == 1
    record = positivity[0]
    assert record.rule is SnapRule.DECIDED_EXACTLY
    assert record.detail["lift_weight"] is None
    assert record.detail["float_diagnostic_disagreed"] is True
    assert record.detail["decided_by"].endswith("is_psd_exact")
    assert record.detail["min_eigenvalue"] == min_eigenvalue(family[0])
    assert record.defect == max(0.0, -min_eigenvalue(family[0]))


def test_an_exactly_positive_family_the_eigenvalue_agrees_with_records_nothing():
    family = [np.array([[0.25, 0.0], [0.0, 0.5]]), np.array([[0.75, 0.0], [0.0, 0.5]])]
    _, record = snap_positivity(
        family, tolerance=1e-9, lattice_exponent=K, site="bob_povm"
    )
    assert record is None


def test_a_block_indefinite_by_a_rounding_is_lifted_at_the_smallest_weight():
    family = indefinite_by_a_rounding()
    assert not is_psd_exact(family[0])
    assert all(is_on_lattice(element, lattice_exponent=K) for element in family)

    snapped, records = snap_family_exact(
        family, tolerance=1e-9, lattice_exponent=K, site="bob_povm", block="m1"
    )
    assert_exactly_admissible(snapped, K)

    positivity = [
        record for record in records if record.predicate is SnapPredicate.POSITIVITY
    ]
    assert len(positivity) == 1
    record = positivity[0]
    assert record.rule is SnapRule.MIX_WITH_DYADIC_UNIFORM
    assert record.detail["lift_weight"] == str(LIFT_LADDER[0])
    assert record.detail["lift_exponent"] == 36
    assert record.detail["indefinite_elements"] == [0]
    assert record.detail["uniform_weights"] == ["1/2", "1/2"]
    assert record.defect == max(0.0, -min_eigenvalue(family[0]))


def test_the_positivity_ceiling_is_read_off_the_declaration_not_an_intermediate():
    """The lattice step must not be able to launder a positivity defect.

    ``0.5 - 2^-50`` rounds to ``0.5`` on the ``2^-40`` lattice, so the family
    below is exactly positive semidefinite AFTER the lattice step and would
    pass any ceiling measured there. The ceiling is the pre-snap one, measured
    on the declaration, so a ``tau`` below the declared defect refuses it.
    """
    epsilon = 2.0**-50
    first = np.array([[0.5, 0.5], [0.5, 0.5 - epsilon]])
    family = [first, np.eye(2) - first]
    assert completeness_residue(family) == 0.0
    assert hermiticity_defect(first) == 0.0
    assert not is_psd_exact(first)

    with pytest.raises(SnapRefusedError) as caught:
        snap_family_exact(family, tolerance=1e-17, lattice_exponent=K, site="b")
    assert caught.value.reason == "defect_above_tolerance"
    assert caught.value.predicate is SnapPredicate.POSITIVITY
    assert caught.value.detail["decided_by"].endswith("is_psd_exact")

    # The same family at a tolerance that admits it is snapped, and the lattice
    # step alone carries it onto the cone -- no lift is needed.
    snapped, records = snap_family_exact(
        family, tolerance=1e-12, lattice_exponent=K, site="b"
    )
    assert_exactly_admissible(snapped, K)
    assert not [
        record for record in records if record.rule is SnapRule.MIX_WITH_DYADIC_UNIFORM
    ]


def test_the_lift_moves_the_declaration_far_below_the_devices_own_scale():
    """The displacement is a modelling act; this says how big it is.

    The receiver declares six residual budgets at ``1e-3``, so a lift at the
    ladder's smallest weight moves the declaration eight orders of magnitude
    below the accuracy the device is characterized to.
    """
    family = indefinite_by_a_rounding()
    snapped, _ = snap_family_exact(
        family, tolerance=1e-9, lattice_exponent=K, site="bob_povm"
    )
    displacement = max(
        float(np.max(np.abs(after - before)))
        for before, after in zip(family, snapped, strict=True)
    )
    assert 0.0 < displacement < 1e-9


def test_a_genuinely_indefinite_block_is_refused_by_the_whole_ladder():
    family = genuinely_indefinite()
    with pytest.raises(SnapRefusedError) as caught:
        snap_family_exact(
            family, tolerance=1.0, lattice_exponent=K, site="bob_povm", block="m2"
        )
    assert caught.value.reason == "positivity_not_restored"
    assert caught.value.predicate is SnapPredicate.POSITIVITY
    assert caught.value.block == "m2"
    assert caught.value.detail["ladder"] == [str(w) for w in LIFT_LADDER]


def test_a_positivity_defect_above_the_tolerance_is_not_lifted():
    """The spectral floor ``lambda_min >= -tau`` is the pre-snap ceiling."""
    family = genuinely_indefinite()
    with pytest.raises(SnapRefusedError) as caught:
        snap_family_exact(family, tolerance=1e-9, lattice_exponent=K, site="b")
    assert caught.value.reason == "defect_above_tolerance"
    assert caught.value.predicate is SnapPredicate.POSITIVITY
    assert caught.value.defect == pytest.approx(-min_eigenvalue(family[0]))


def test_the_uniform_family_the_lift_mixes_with_is_dyadic():
    """The legacy lift's ``1/|Y|`` is not dyadic at ``|Y| = 6``, and that broke it.

    The spike measured that this single fact accounts for every
    representability failure at ``p_dc = 0``, twelve of twenty-four grid points
    at ``k = 40``. Every weight here has a power-of-two denominator, and they
    sum exactly to one.
    """
    for count in (1, 2, 3, 5, 6, 8, 9):
        weights = dyadic_uniform_weights(count)
        assert len(weights) == count
        assert sum(weights, Fraction(0)) == 1
        for weight in weights:
            assert weight > 0
            assert weight.denominator & (weight.denominator - 1) == 0
    assert dyadic_uniform_weights(6) == (
        Fraction(3, 8),
        *([Fraction(1, 8)] * 5),
    )
    assert Fraction(1, 6) not in dyadic_uniform_weights(6)


def test_the_lift_ladder_is_dyadic_and_ascending():
    assert all(weight.numerator == 1 for weight in LIFT_LADDER)
    assert all(
        weight.denominator & (weight.denominator - 1) == 0 for weight in LIFT_LADDER
    )
    assert list(LIFT_LADDER) == sorted(LIFT_LADDER)


def test_snap_positivity_refuses_a_family_that_is_not_exactly_hermitian():
    with pytest.raises(ValueError, match="exactly Hermitian"):
        snap_positivity(
            [NON_HERMITIAN, np.eye(2, dtype=np.complex128)],
            tolerance=1.0,
            lattice_exponent=K,
            site="bob_povm",
        )


# ---------------------------------------------------------------------------
#  3. Hermiticity: exact, not merely within a tolerance
# ---------------------------------------------------------------------------


def test_a_hermiticity_snap_returns_an_exactly_hermitian_operator():
    snapped, record = snap_hermiticity(
        NON_HERMITIAN, tolerance=1.0, site="bob_povm", setting="t0", block="s1"
    )
    assert is_hermitian_exact(snapped)
    assert hermiticity_defect(snapped) == 0.0
    assert snapped[0, 1] == 2.0 + 0.5j
    assert snapped[1, 0] == 2.0 - 0.5j
    assert record.predicate is SnapPredicate.HERMITICITY
    assert record.rule is SnapRule.HERMITIAN_PART
    assert record.site == "bob_povm"
    assert (record.setting, record.block) == ("t0", "s1")
    assert record.defect == hermiticity_defect(NON_HERMITIAN)
    assert record.detail["exactly_hermitian"] is True


def test_a_hermiticity_defect_above_the_tolerance_is_not_snapped():
    with pytest.raises(SnapRefusedError) as caught:
        snap_hermiticity(NON_HERMITIAN, tolerance=0.5, site="bob_povm", block="s1")
    assert caught.value.reason == "defect_above_tolerance"
    assert caught.value.predicate is SnapPredicate.HERMITICITY
    assert caught.value.block == "s1"
    assert caught.value.defect == 1.0
    assert caught.value.tolerance == 0.5


def test_the_tolerance_comparison_admits_equality():
    """Non-strict on both sides, as every tolerance inequality on this platform.

    ``proof-reductions`` Lemma ``lem:exactpsd`` (ii): "an implementation using a
    strict comparison anywhere in the chain refuses this declaration and is
    wrong".
    """
    snapped, record = snap_hermiticity(NON_HERMITIAN, tolerance=1.0, site="s")
    assert record.defect == 1.0 == record.tolerance
    assert is_hermitian_exact(snapped)


def test_the_family_entry_point_records_the_hermitian_part_when_it_moves():
    family = [
        np.array([[0.5, 0.25 + 1e-15j], [0.25, 0.5]], dtype=np.complex128),
        np.array([[0.5, -0.25], [-0.25, 0.5]], dtype=np.complex128),
    ]
    snapped, records = snap_family_exact(
        family, tolerance=1e-9, lattice_exponent=K, site="bob_povm"
    )
    assert_exactly_admissible(snapped, K)
    hermiticity = [
        record for record in records if record.predicate is SnapPredicate.HERMITICITY
    ]
    assert len(hermiticity) == 1
    assert hermiticity[0].defect == max(hermiticity_defect(e) for e in family)


# ---------------------------------------------------------------------------
#  4. The lattice, and (D-LAT)
# ---------------------------------------------------------------------------


def test_the_lattice_snap_puts_every_part_on_an_integer_multiple_of_two_to_the_k():
    a = np.array([[0.1, 0.2 + 0.3j], [0.2 - 0.3j, 0.4]], dtype=np.complex128)
    assert not is_on_lattice(a, lattice_exponent=K)
    snapped, record = snap_to_lattice(
        a, lattice_exponent=K, tolerance=1e-12, site="bob_povm"
    )
    assert is_on_lattice(snapped, lattice_exponent=K)
    assert is_hermitian_exact(snapped)
    assert record.predicate is SnapPredicate.LATTICE
    assert record.rule is SnapRule.ROUND_TO_LATTICE
    assert record.detail["lattice_exponent"] == K
    assert 0.0 < record.defect <= 2.0 ** -(K + 1) * 2**0.5
    assert record.detail["entries_moved"] == 4


def test_a_part_of_modulus_above_one_is_refused_not_rounded():
    """(D-LAT)'s second half; no rounding repairs it."""
    with pytest.raises(SnapRefusedError) as caught:
        snap_to_lattice(
            np.array([[2.0, 0.0], [0.0, 0.5]]),
            lattice_exponent=K,
            tolerance=1.0,
            site="bob_povm",
        )
    assert caught.value.reason == "part_modulus_above_one"
    assert caught.value.predicate is SnapPredicate.LATTICE
    assert caught.value.detail["entry"] == [0, 0]


@pytest.mark.parametrize("lattice_exponent", [0, 54, 128, -1])
def test_a_lattice_exponent_outside_one_to_fifty_three_is_refused(
    lattice_exponent: int,
):
    with pytest.raises(ValueError, match="lattice_exponent"):
        snap_to_lattice(
            np.eye(2), lattice_exponent=lattice_exponent, tolerance=1.0, site="s"
        )


def test_the_lattice_exponent_has_no_default():
    with pytest.raises(TypeError):
        snap_family_exact(  # type: ignore[call-arg]
            one_ulp_family(), tolerance=1e-12, site="bob_povm"
        )


def test_is_on_lattice_decides_both_halves_of_the_invariant():
    assert is_on_lattice(np.array([[0.5, 0.25]]), lattice_exponent=2)
    assert not is_on_lattice(np.array([[0.125, 0.0]]), lattice_exponent=2)
    assert not is_on_lattice(np.array([[1.5, 0.0]]), lattice_exponent=2)
    assert is_on_lattice(np.array([[1.0, -1.0]]), lattice_exponent=1)


# ---------------------------------------------------------------------------
#  5. Condition (S): the declared-order sum, decided LAST
# ---------------------------------------------------------------------------


def test_the_sub_lattice_counterexample_is_removed_by_the_lattice_step():
    """``def:optol``'s ``(1, 2^-60, 2^-60)``, on a one-dimensional sector.

    Every entry is representable and non-negative, ``2^-60`` is below half an
    ulp of ``1``, so each binary64 addition returns its left operand: the
    computed sum is ``1`` and the family passes every tolerance including zero,
    while the real sum is ``1 + 2^-59``. The lattice step removes the
    sub-lattice mass and the family the run declares is the one whose sum is
    exactly one.
    """
    family = [np.array([[1.0]]), np.array([[2.0**-60]]), np.array([[2.0**-60]])]
    assert completeness_residue(family) == 0.0
    assert not sum_rounds_nowhere(family).ok

    snapped, records = snap_family_exact(
        family, tolerance=1e-12, lattice_exponent=K, site="alice_marginal"
    )
    assert [float(element[0, 0]) for element in snapped] == [1.0, 0.0, 0.0]
    assert_exactly_admissible(snapped, K)
    lattice = [
        record for record in records if record.predicate is SnapPredicate.LATTICE
    ]
    assert len(lattice) == 1
    assert lattice[0].detail["entries_moved"] == 2


def test_verify_family_exact_refuses_a_family_whose_sum_rounds():
    family = [np.array([[1.0]]), np.array([[2.0**-60]]), np.array([[-(2.0**-60)]])]
    with pytest.raises(SnapRefusedError) as caught:
        verify_family_exact(family, site="alice_marginal")
    assert caught.value.reason == "not_exactly_admissible"
    assert "declared_order_sum" in caught.value.detail["failures"]
    assert caught.value.detail["rounds_nowhere"]["first_inexact_index"] == 1


def test_verify_family_exact_names_the_predicate_that_failed():
    with pytest.raises(SnapRefusedError) as caught:
        verify_family_exact(
            [np.array([[0.5]]), np.array([[0.25]])], site="bob_povm", block="m0"
        )
    assert caught.value.reason == "not_exactly_admissible"
    assert caught.value.predicate is SnapPredicate.COMPLETENESS
    assert caught.value.detail["failures"] == ["completeness"]
    assert caught.value.block == "m0"


def test_verify_family_exact_decides_d_lat_when_it_is_given_k():
    family = [np.array([[0.1]]), np.array([[0.9]])]
    with pytest.raises(SnapRefusedError) as caught:
        verify_family_exact(family, site="s", lattice_exponent=K)
    assert caught.value.predicate is SnapPredicate.LATTICE
    assert caught.value.detail["off_lattice_elements"] == [0, 1]


def test_verify_family_exact_returns_the_admission_of_an_admissible_family():
    snapped, _ = snap_family_exact(
        one_ulp_family(), tolerance=1e-12, lattice_exponent=K, site="s"
    )
    admission = verify_family_exact(snapped, site="s", lattice_exponent=K)
    assert admission.admissible
    assert admission.failures == ()


# ---------------------------------------------------------------------------
#  6. Both declared lattices, and complex data
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lattice_exponent", [40, 50])
def test_the_table_produces_exact_admissibility_at_either_declared_lattice(
    lattice_exponent: int,
):
    for family in (
        one_ulp_family(),
        rank_one_family(),
        indefinite_by_a_rounding(),
        [
            np.array([[0.06, 0.0], [0.0, 0.5]]),
            np.array([[0.57, 0.0], [0.0, 0.3]]),
            np.array([[0.37, 0.0], [0.0, 0.2]]),
        ],
    ):
        snapped, _ = snap_family_exact(
            family,
            tolerance=1e-9,
            lattice_exponent=lattice_exponent,
            site="bob_povm",
        )
        assert_exactly_admissible(snapped, lattice_exponent)


def test_a_complex_family_stays_complex_and_is_admitted_exactly():
    family = rank_one_family()
    snapped, _ = snap_family_exact(
        family, tolerance=1e-9, lattice_exponent=K, site="bob_povm"
    )
    assert all(np.iscomplexobj(element) for element in snapped)
    assert_exactly_admissible(snapped, K)
    assert snapped[0][0, 1] == pytest.approx(family[0][0, 1])


def test_a_real_family_comes_back_real():
    snapped, _ = snap_family_exact(
        one_ulp_family(), tolerance=1e-12, lattice_exponent=K, site="s"
    )
    assert all(element.dtype == np.float64 for element in snapped)


def test_a_complex_element_makes_the_whole_family_complex():
    """One dtype per family: the residue is shared between its elements."""
    family = [
        np.array([[0.25, 0.25j], [-0.25j, 0.25]], dtype=np.complex128),
        np.array([[0.25, -0.25j], [0.25j, 0.25]], dtype=np.complex128),
        np.array([[0.5, 0.0], [0.0, 0.5]], dtype=np.float64),
    ]
    snapped, _ = snap_family_exact(
        family, tolerance=1e-9, lattice_exponent=K, site="bob_povm"
    )
    assert all(np.iscomplexobj(element) for element in snapped)
    assert_exactly_admissible(snapped, K)


# ---------------------------------------------------------------------------
#  7. Column-stochasticity and forbidden entries
# ---------------------------------------------------------------------------


def test_a_column_snap_carries_every_column_sum_EXACTLY_to_one():
    """Exactly one, not one to within binary64."""
    m = np.array([[0.5, 0.25], [0.25, 0.5], [0.25, 0.5]])
    assert column_residue(m) == 0.25
    snapped, record = snap_column_stochasticity(
        m,
        designated_row=0,
        lattice_exponent=K,
        tolerance=0.5,
        site="dark_count_channel",
    )
    for column in range(snapped.shape[1]):
        exact = sum(
            (Fraction(float(snapped[row, column])) for row in range(snapped.shape[0])),
            Fraction(0),
        )
        assert exact == 1
    assert column_residue(snapped) == 0.0
    assert is_on_lattice(snapped, lattice_exponent=K)
    assert record.predicate is SnapPredicate.COLUMN_STOCHASTICITY
    assert record.rule is SnapRule.RESCALE_AND_ABSORB
    assert record.defect == 0.25
    assert record.detail == {
        "designated_row": 0,
        "columns": 2,
        "lattice_exponent": K,
    }


def test_the_designated_row_is_the_one_that_moves_to_close_the_column():
    m = np.array([[0.25, 0.5], [0.25, 0.5]])
    snapped, _ = snap_column_stochasticity(
        m, designated_row=1, lattice_exponent=K, tolerance=1.0, site="channel"
    )
    assert snapped[0, 0] == 0.5
    assert snapped[1, 0] == 0.5


def test_a_column_residue_above_the_tolerance_is_not_snapped():
    m = np.array([[0.5, 0.25], [0.25, 0.5], [0.25, 0.5]])
    with pytest.raises(SnapRefusedError) as caught:
        snap_column_stochasticity(
            m, designated_row=0, lattice_exponent=K, tolerance=1e-9, site="channel"
        )
    assert caught.value.reason == "defect_above_tolerance"
    assert caught.value.defect == 0.25


def test_a_column_that_sums_to_zero_cannot_be_rescaled():
    m = np.array([[0.5, 0.0], [0.5, 0.0]])
    with pytest.raises(SnapRefusedError) as caught:
        snap_column_stochasticity(
            m, designated_row=0, lattice_exponent=K, tolerance=1.0, site="channel"
        )
    assert caught.value.reason == "degenerate_column"


def test_the_designated_row_must_exist():
    m = np.array([[0.5, 0.5], [0.5, 0.5]])
    with pytest.raises(ValueError, match="designated_row"):
        snap_column_stochasticity(
            m, designated_row=7, lattice_exponent=K, tolerance=1.0, site="channel"
        )


def test_a_forbidden_entry_below_the_tolerance_is_set_to_zero():
    a = np.array([[1.0, 1e-14], [2e-14, 1.0]])
    snapped, record = snap_forbidden_entries(
        a, [(0, 1), (1, 0)], tolerance=1e-12, site="bob_povm", block="s0"
    )
    assert snapped[0, 1] == 0.0
    assert snapped[1, 0] == 0.0
    assert snapped[0, 0] == 1.0
    assert record.predicate is SnapPredicate.FORBIDDEN_ENTRY
    assert record.rule is SnapRule.ZEROED
    assert record.defect == 2e-14
    assert record.detail == {"entries": 2, "worst_entry": [1, 0]}


def test_a_forbidden_entry_above_the_tolerance_is_not_zeroed():
    a = np.array([[1.0, 0.5], [0.0, 1.0]])
    with pytest.raises(SnapRefusedError) as caught:
        snap_forbidden_entries(a, [(0, 1)], tolerance=1e-12, site="bob_povm")
    assert caught.value.reason == "defect_above_tolerance"
    assert caught.value.defect == 0.5


def test_the_forbidden_set_is_the_callers_and_is_never_empty():
    with pytest.raises(ValueError, match="no entries"):
        snap_forbidden_entries(np.eye(2), [], tolerance=1.0, site="bob_povm")


def test_a_forbidden_entry_outside_the_array_is_refused():
    with pytest.raises(ValueError, match="outside an array"):
        snap_forbidden_entries(np.eye(2), [(0, 5)], tolerance=1.0, site="bob_povm")


# ---------------------------------------------------------------------------
#  8. Invariants that hold across the whole table
# ---------------------------------------------------------------------------


def every_snap() -> list[tuple[str, SnapRecord, float]]:
    """Run one of each snap, and return its record beside the kernel's number."""
    out: list[tuple[str, SnapRecord, float]] = []

    _, record = snap_hermiticity(NON_HERMITIAN, tolerance=1.0, site="s")
    out.append(("hermiticity", record, hermiticity_defect(NON_HERMITIAN)))

    family = one_ulp_family()
    _, records = snap_family_exact(
        family, tolerance=1e-12, lattice_exponent=K, site="s"
    )
    for record in records:
        if record.predicate is SnapPredicate.COMPLETENESS:
            out.append(("completeness", record, completeness_residue(family)))

    lifted = indefinite_by_a_rounding()
    _, records = snap_family_exact(lifted, tolerance=1e-9, lattice_exponent=K, site="s")
    for record in records:
        if record.predicate is SnapPredicate.POSITIVITY:
            worst = min(min_eigenvalue(element) for element in lifted)
            out.append(("positivity", record, max(0.0, -worst)))

    m = np.array([[0.5, 0.25], [0.25, 0.5], [0.25, 0.5]])
    _, record = snap_column_stochasticity(
        m, designated_row=0, lattice_exponent=K, tolerance=0.5, site="s"
    )
    out.append(("column", record, column_residue(m)))

    a = np.array([[1.0, 1e-14], [0.0, 1.0]])
    _, record = snap_forbidden_entries(a, [(0, 1)], tolerance=1e-12, site="s")
    out.append(("forbidden", record, float(abs(a[0, 1]))))
    return out


def test_every_record_carries_the_defect_the_binary64_kernel_measures():
    snaps = every_snap()
    assert {name for name, _, _ in snaps} == {
        "hermiticity",
        "completeness",
        "positivity",
        "column",
        "forbidden",
    }
    for name, record, measured in snaps:
        assert record.defect == measured, name


def test_every_record_carries_its_predicate_rule_site_and_tolerance():
    for name, record, _measured in every_snap():
        assert isinstance(record.predicate, SnapPredicate), name
        assert isinstance(record.rule, SnapRule), name
        assert record.site == "s", name
        assert record.tolerance > 0.0, name
        assert set(record.as_record()) == {
            "predicate",
            "rule",
            "site",
            "setting",
            "block",
            "pre_snap_defect",
            "declared_tolerance",
            "detail",
        }, name


def test_the_defect_field_is_a_float_and_everything_else_is_in_detail():
    """spec/architecture.md 2.9, constraint (3), asserted rather than trusted."""
    for name, record, _ in every_snap():
        assert isinstance(record.defect, float), name
        assert isinstance(record.tolerance, float), name
        for key, value in record.detail.items():
            assert isinstance(key, str), name
            assert not isinstance(value, Fraction), (name, key)


def test_every_record_is_json_ready():
    for name, record, _ in every_snap():
        rendered = json.loads(json.dumps(record.as_record()))
        assert rendered["predicate"] == str(record.predicate), name
        assert rendered["rule"] == str(record.rule), name


def test_the_lattice_and_positivity_records_carry_what_section_seven_names():
    _, records = snap_family_exact(
        indefinite_and_incomplete(),
        tolerance=1e-9,
        lattice_exponent=K,
        site="bob_povm",
    )
    by_predicate = {record.predicate: record for record in records}
    assert set(by_predicate) == {
        SnapPredicate.LATTICE,
        SnapPredicate.COMPLETENESS,
        SnapPredicate.POSITIVITY,
    }
    lattice = by_predicate[SnapPredicate.LATTICE]
    assert set(lattice.detail) >= {
        "lattice_exponent",
        "displacement",
        "entries_moved",
    }
    positivity = by_predicate[SnapPredicate.POSITIVITY]
    assert set(positivity.detail) >= {
        "lattice_exponent",
        "min_eigenvalue",
        "decided_by",
        "diagnostic",
        "lift_weight",
        "lift_exponent",
        "indefinite_elements",
        "uniform_weights",
        "designated_element",
    }
    completeness = by_predicate[SnapPredicate.COMPLETENESS]
    assert set(completeness.detail) >= {
        "elements",
        "lattice_exponent",
        "designated_element",
        "designated_element_trace",
        "residue_entries_moved",
    }


def test_no_snap_in_the_table_modifies_the_object_it_was_given():
    """A snap RETURNS a repaired object; it never repairs one in place.

    The distinction is what keeps the recorded pre-snap defect a measurement of
    something real: if the argument moved, a second measurement of it would no
    longer be the number the record carries.
    """
    a = NON_HERMITIAN.copy()
    snap_hermiticity(a, tolerance=1.0, site="s")
    assert np.array_equal(a, NON_HERMITIAN)

    for family in (one_ulp_family(), rank_one_family(), indefinite_by_a_rounding()):
        before = [element.copy() for element in family]
        snap_family_exact(family, tolerance=1e-9, lattice_exponent=K, site="s")
        for element, original in zip(family, before, strict=True):
            assert np.array_equal(element, original)

    m = np.array([[0.5, 0.25], [0.25, 0.5], [0.25, 0.5]])
    column_before = m.copy()
    snap_column_stochasticity(
        m, designated_row=0, lattice_exponent=K, tolerance=0.5, site="s"
    )
    assert np.array_equal(m, column_before)

    forbidden = np.array([[1.0, 1e-14], [0.0, 1.0]])
    forbidden_before = forbidden.copy()
    snap_forbidden_entries(forbidden, [(0, 1)], tolerance=1e-12, site="s")
    assert np.array_equal(forbidden, forbidden_before)


def test_positivity_is_in_the_table_and_is_decided_exactly():
    """Positivity is a row of the table, asserted where its omission would be.

    A table without it would rest on "an eigenvalue
    above ``-tau`` passes at every consumer". Under 2.9 a consumer decides positivity
    exactly, so there is no window left for a rounding to pass through, and the
    lift is load-bearing.
    """
    assert "positivity" in {member.value for member in SnapPredicate}
    assert "snap_positivity" in snap_module.__all__
    assert {member.value for member in SnapPredicate} == {
        "hermiticity",
        "lattice",
        "completeness",
        "positivity",
        "column-stochasticity",
        "forbidden-entry",
        "declared-order-sum",
        # foundations/req:snap-reference (iv): the strict option refuses a
        # measurement-family block that would rest on A-SNAP; the refusal
        # names this predicate.
        "strict-option",
    }


def test_the_superseded_trace_weight_rule_survives_as_a_readable_name():
    """spec/architecture.md 2.9, constraint (5): earlier run records stay readable."""
    assert SnapRule.DISTRIBUTE_BY_TRACE_WEIGHT.value == "distribute-by-trace-weight"
    produced = {record.rule for _, record, _ in every_snap()}
    assert SnapRule.DISTRIBUTE_BY_TRACE_WEIGHT not in produced


def test_the_table_imports_a_public_name_from_the_measuring_kernel():
    """spec/architecture.md 2.9, constraint (5), second half."""
    from pathlib import Path

    from certiqs_key.foundations import numeric

    assert "checked_matrix" in numeric.__all__
    assert numeric.checked_matrix is numeric._checked
    assert snap_module.__file__ is not None
    source = Path(snap_module.__file__).read_text(encoding="utf-8")
    assert "_checked as" not in source
    assert "checked_matrix" in source


def test_every_declared_refusal_reason_is_one_a_snap_actually_raises():
    """The vocabulary is machine-readable, so it must not carry a dead name."""
    raised = set()
    for call in (
        lambda: snap_hermiticity(NON_HERMITIAN, tolerance=0.0, site="s"),
        lambda: snap_column_stochasticity(
            np.array([[0.5, 0.0], [0.5, 0.0]]),
            designated_row=0,
            lattice_exponent=K,
            tolerance=1.0,
            site="s",
        ),
        lambda: designated_element_index([np.zeros((2, 2)), np.zeros((2, 2))]),
        lambda: snap_to_lattice(
            np.array([[2.0, 0.0], [0.0, 0.5]]),
            lattice_exponent=K,
            tolerance=1.0,
            site="s",
        ),
        lambda: snap_family_exact(
            genuinely_indefinite(), tolerance=1.0, lattice_exponent=K, site="s"
        ),
        lambda: verify_family_exact([np.array([[0.5]]), np.array([[0.25]])], site="s"),
        # foundations/req:snap-reference (iv): a moved measurement family on
        # which no reference is handed rests on A-SNAP, and the strict option
        # refuses it.
        lambda: snap_measurement_family(
            {"m=0": [np.array([[0.3]]), np.array([[0.7]])]},
            alphabet=("a", "b"),
            tolerance=1e-9,
            lattice_exponent=3,
            site="s",
            settings=SnapSettings(strict=True),
        ),
    ):
        with pytest.raises(SnapRefusedError) as caught:
            call()
        raised.add(caught.value.reason)
    assert raised == set(REFUSAL_REASONS)


@pytest.mark.parametrize("tolerance", [-1e-12, float("nan"), float("inf")])
def test_a_number_that_is_not_a_tolerance_is_refused(tolerance: float):
    with pytest.raises(ValueError, match="not a declared numerical tolerance"):
        snap_hermiticity(NON_HERMITIAN, tolerance=tolerance, site="s")


def test_no_module_tier_package_imports_the_snapping_table():
    """spec/architecture.md 2.8: only a DECLARER may call this module.

    An instance about its own device, or a producer about its own emission. A
    module that snaps what it was handed is a defect caught by the
    import-direction rule of PRINCIPLES.md section 4 -- and by this test,
    which is cheaper than review. ``reductions`` re-establishes the lattice
    invariant on its own emission and does so inside its own package, which
    is why it is in the list rather than excepted from it.

    ``foundations`` holds the table, and its other files name it in their
    docstrings, so there the import statements are read rather than the text:
    no sibling of the table imports it.
    """
    import ast
    from pathlib import Path

    source_root = (
        Path(__file__).resolve().parents[2] / "src" / "certiqs_key"
    )
    module_tier = (
        "meat_core",
        "solvers",
        "protocol_compiler",
        "statistics",
        "receiver",
        "reductions",
        "transmitter",
    )
    offenders = [
        path.relative_to(source_root).as_posix()
        for package in module_tier
        for path in (source_root / package).rglob("*.py")
        if "foundations.snap" in path.read_text(encoding="utf-8")
    ]
    for path in sorted((source_root / "foundations").rglob("*.py")):
        if path.name == "snap.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                named = {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                named = {node.module} | {
                    f"{node.module}.{alias.name}" for alias in node.names
                }
            else:
                continue
            if "certiqs_key.foundations.snap" in named:
                offenders.append(path.relative_to(source_root).as_posix())
    assert offenders == []
