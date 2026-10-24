"""The Fock functor on the photon-number sectors (registry RC1), vs the registry.

Golden replay of ``FOCK_CASES`` (oracle entry ``O-RP-FOCK``). Four things the
entry says an implementation can get wrong, and each has a test here: the
grading, the block dimensions, the OCCUPATION-VECTOR BASIS ORDER and the index
reversal it causes, the ``sqrt2`` of the two-photon block, the projector case,
and the spectrum with its two attained bounds.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE, assert_matches, mat_value, sorted_spectrum
from registry_receiver_povm import FOCK_CASES, rp_oracle

from certiqs_key.receiver import (
    block_dimension,
    block_spectrum_from_eigenvalues,
    fock_block,
    occupation_vectors,
)
from certiqs_key.receiver.numerics import eigenvalues


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_fock_block_is_reproduced() -> None:
    """Eq. eq:fockfunctor on every frozen block of O-RP-FOCK."""
    assert rp_oracle("O-RP-FOCK").claims == ("RC1",)
    for case in FOCK_CASES:
        operator = mat_value(case.operator)
        computed = fock_block(operator, case.photon_number)
        assert_matches(computed, mat_value(case.block), TOLERANCE.eps_4, case.case_id)


@pytest.mark.contract
def test_the_occupation_order_is_ascending_lexicographic() -> None:
    """The `subsystem_order` convention, last clause, and the index reversal."""
    for case in FOCK_CASES:
        dimension = len(case.mode_labels)
        assert occupation_vectors(dimension, case.photon_number) == case.basis_order, (
            case.case_id
        )
    # The trap, stated in the registry: the ONE-photon block of Fock(X) is the
    # matrix of X in the REVERSED mode basis.
    operator = np.asarray([[0.5, 0.25], [0.0, 0.5]], dtype=np.complex128)
    block = fock_block(operator, 1)
    reversed_basis = operator[::-1, ::-1]
    assert_matches(block, reversed_basis, TOLERANCE.eps_4, "one-photon reversal")
    assert block[0, 1] == pytest.approx(0.0)
    assert block[1, 0] == pytest.approx(0.25)


@pytest.mark.contract
def test_the_block_dimension_is_the_outputs_formula() -> None:
    """`outputs.block_dimensions`: binom(|Inp_C| + n - 1, n)."""
    for case in FOCK_CASES:
        dimension = len(case.mode_labels)
        expected = math.comb(dimension + case.photon_number - 1, case.photon_number)
        assert block_dimension(dimension, case.photon_number) == expected, case.case_id
        assert len(case.basis_order) == expected, case.case_id
        assert mat_value(case.block).shape == (expected, expected), case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_frozen_spectra_are_the_computed_ones() -> None:
    """Eq. eq:spectrum, on the cases where the operator is normal."""
    for case in FOCK_CASES:
        if case.spectrum is None:
            continue
        block = fock_block(mat_value(case.operator), case.photon_number)
        computed = sorted(float(value) for value in eigenvalues(block))
        assert_matches(
            computed, sorted_spectrum(case.spectrum), TOLERANCE.eps_2, case.case_id
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_eq_spectrum_and_both_attained_bounds_of_eq_blockbounds() -> None:
    """Lemma lem:fock-block-spectrum on FOCK-SPECTRUM-n2, with both endpoints."""
    case = next(c for c in FOCK_CASES if c.case_id == "FOCK-SPECTRUM-n2")
    # The frozen operator is 1 - A with A = [[1/2, 1/4], [1/4, 1/2]].
    gram = np.asarray([[0.5, 0.25], [0.25, 0.5]], dtype=np.complex128)
    spectrum_of_a = [float(value) for value in eigenvalues(gram)]
    predicted = block_spectrum_from_eigenvalues(spectrum_of_a, case.photon_number)
    assert_matches(
        sorted(predicted),
        sorted_spectrum(case.spectrum or ()),
        TOLERANCE.eps_2,
        "eq:spectrum",
    )
    block = fock_block(mat_value(case.operator), case.photon_number)
    observed = [float(value) for value in eigenvalues(block)]
    lower = (1.0 - max(spectrum_of_a)) ** case.photon_number
    upper = (1.0 - min(spectrum_of_a)) ** case.photon_number
    assert min(observed) == pytest.approx(lower, abs=TOLERANCE.eps_2)
    assert max(observed) == pytest.approx(upper, abs=TOLERANCE.eps_2)


@pytest.mark.contract
def test_the_projector_case_of_lemma_fock_functor_iv() -> None:
    """Lemma lem:fock-functor (iv): Fock(P) is a projector, and which one."""
    projector = np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
    for photons in (1, 2):
        block = fock_block(projector, photons)
        assert_matches(block @ block, block, TOLERANCE.eps_4, "idempotence")
        assert_matches(block, block.conj().T, TOLERANCE.eps_4, "self-adjointness")
        # Exactly the occupation vectors carrying no photon outside ran P.
        expected_rank = sum(
            1 for vector in occupation_vectors(2, photons) if vector[1] == 0
        )
        assert round(float(np.trace(block).real)) == expected_rank


@pytest.mark.contract
def test_the_two_photon_block_carries_its_sqrt_two_exactly_once() -> None:
    """The sqrt2 of |1,1> is in the block and is not a rounding artifact."""
    case = next(c for c in FOCK_CASES if c.case_id == "FOCK-TRI-n2")
    block = fock_block(mat_value(case.operator), 2)
    root_two_over_eight = math.sqrt(2.0) / 8.0
    assert float(block[1, 0].real) == pytest.approx(root_two_over_eight, abs=1e-12)
    assert float(block[2, 1].real) == pytest.approx(root_two_over_eight, abs=1e-12)
    assert float(block[0, 1].real) == pytest.approx(0.0, abs=1e-12)
