"""The click-pattern POVM and the coarse-graining (registry RC6, RC7).

Golden replay of ``POVM_BLOCK_CASES``, ``INCLUSION_EXCLUSION_CASES``,
``COARSE_GRAINING_CASES`` and ``ADDITIVITY_CASES`` (oracle entries
``O-RP-POVM`` and ``O-RP-COARSE``).

What the frozen set pins, and what is tested here: POSITIVITY, which Remark
``rem:positivity`` insists does NOT come from the alternating sum -- the
``PB-BB84-n2`` multiclick block has four negative-coefficient summands and is
still positive semidefinite; COMPLETENESS blockwise, which is residual ``r_4``
set to zero; ``blk M^{(=0)}_S = delta_{S, empty}`` -- no photon, no click; the
INCLUSION-EXCLUSION identity in the direction Theorem
``thm:representation-independence`` (i) uses to invert the construction, which an
implementation with the occupation order reversed would fail; and the declared
coarse-graining, whose alphabet is DATA.
"""

from __future__ import annotations

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE, assert_matches, mat_value, sorted_spectrum
from registry_receiver_povm import (
    ADDITIVITY_CASES,
    COARSE_GRAINING_CASES,
    INCLUSION_EXCLUSION_CASES,
    INSTRUMENT_CASES,
    POVM_BLOCK_CASES,
    rp_oracle,
)

from certiqs_key.receiver import (
    CoarseGraining,
    GramFamily,
    bound_data_from_family,
    bound_function,
    check_coarse_graining,
    coarse_block,
    coarse_elements,
    completeness_defect,
    element_block,
    fibre_bound,
    occupation_vectors,
    port_grams,
    raw_alphabet,
    unconditioned_family,
)
from certiqs_key.receiver.numerics import eigenvalues
from certiqs_key.receiver.povm import NoClickFamily


def _instrument(case_id: str) -> tuple[tuple[str, ...], GramFamily]:
    """Return the port labels and the Gram family of a frozen instrument."""
    case = next(c for c in INSTRUMENT_CASES if c.case_id == case_id)
    gamma_inp = mat_value(case.gamma_inp)
    labels = tuple(label for label, _ in case.port_map)
    rows = [modes for _, modes in case.port_map]
    return labels, GramFamily(labels, port_grams(gamma_inp, rows))


def _no_click(case_id: str) -> tuple[tuple[str, ...], NoClickFamily]:
    """Return the port labels and the unconditioned no-click family."""
    labels, family = _instrument(case_id)
    return labels, unconditioned_family(family)


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_povm_block_is_reproduced() -> None:
    """Eq. eq:blockMS, Eq. eq:Mnc, Eq. eq:Msc and Eq. eq:Mmc."""
    assert rp_oracle("O-RP-POVM").claims == ("RC6",)
    for case in POVM_BLOCK_CASES:
        labels, family = _no_click(case.instrument_case_id)
        blocks = coarse_elements(family, case.photon_number)
        for pattern, frozen in case.elements:
            key = "nc" if not pattern else f"sc_{labels.index(pattern[0])}"
            assert_matches(
                blocks[key],
                mat_value(frozen),
                TOLERANCE.eps_4,
                f"{case.case_id} {pattern}",
            )
        assert_matches(
            blocks["mc"],
            mat_value(case.multiclick),
            TOLERANCE.eps_4,
            f"{case.case_id} mc",
        )
        computed = sorted(float(value) for value in eigenvalues(blocks["mc"]))
        assert_matches(
            computed,
            sorted_spectrum(case.multiclick_spectrum),
            TOLERANCE.eps_2,
            f"{case.case_id} spectrum",
        )
        # The declared occupation-vector basis order and block dimension.
        dimension = family.dimension
        assert occupation_vectors(dimension, case.photon_number) == case.basis_order, (
            case.case_id
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_every_block_is_positive_semidefinite_and_complete() -> None:
    """Theorem thm:click-povm (i) restricted to a photon-number sector."""
    for case in POVM_BLOCK_CASES:
        _, family = _no_click(case.instrument_case_id)
        blocks = coarse_elements(family, case.photon_number)
        for key, block in blocks.items():
            assert_matches(
                block, block.conj().T, TOLERANCE.eps_4, f"{case.case_id} {key} herm"
            )
            smallest = float(np.min(eigenvalues(block)))
            assert smallest >= -TOLERANCE.eps_2, (case.case_id, key)
        total = sum(blocks.values())
        size = family.block_dimension(case.photon_number)
        assert_matches(
            total, np.eye(size), TOLERANCE.eps_4, f"{case.case_id} completeness"
        )
        # And residual r_4, summed over the RAW alphabet, is zero as well.
        assert_matches(
            completeness_defect(family, case.photon_number),
            np.zeros((size, size)),
            TOLERANCE.eps_4,
            f"{case.case_id} r_4",
        )


@pytest.mark.contract
def test_no_photon_no_click() -> None:
    """Theorem thm:click-povm (iii): blk M^{(=0)}_S = delta_{S, empty}."""
    for case_id in ("I-BS", "I-BB84", "I-RANK2", "I-PROBE"):
        _, family = _no_click(case_id)
        for pattern in raw_alphabet(family.port_count):
            block = element_block(family, pattern, 0)
            expected = 1.0 if not pattern else 0.0
            assert float(block[0, 0].real) == pytest.approx(
                expected, abs=TOLERANCE.eps_4
            ), (case_id, sorted(pattern))


@pytest.mark.contract
@pytest.mark.oracle
def test_the_multiclick_block_dominates_the_frozen_bound() -> None:
    """Eq. eq:mcbound, and Remark rem:notsharp where the slack is visible."""
    for case in POVM_BLOCK_CASES:
        _, family = _no_click(case.instrument_case_id)
        blocks = coarse_elements(family, case.photon_number)
        data = bound_data_from_family(family)
        beta = bound_function(data, case.photon_number)
        assert beta == pytest.approx(float(case.beta_at_n), abs=TOLERANCE.eps_2), (
            case.case_id
        )
        smallest = float(np.min(eigenvalues(blocks["mc"])))
        assert smallest >= beta - TOLERANCE.eps_2, case.case_id
    # I-BS: one input mode, so the bound IS the eigenvalue at every n.
    _, bs = _no_click("I-BS")
    data = bound_data_from_family(bs)
    for photons in range(4):
        block = coarse_elements(bs, photons)["mc"]
        assert float(np.min(eigenvalues(block))) == pytest.approx(
            bound_function(data, photons), abs=TOLERANCE.eps_2
        )
    # I-BB84 at n = 2: the bound is 0 and the eigenvalue is 1/2, strictly loose.
    _, bb84 = _no_click("I-BB84")
    loose = float(np.min(eigenvalues(coarse_elements(bb84, 2)["mc"])))
    assert loose == pytest.approx(0.5, abs=TOLERANCE.eps_2)
    assert bound_function(
        bound_data_from_family(bb84), 2
    ) == pytest.approx(0.0, abs=TOLERANCE.eps_2)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_inclusion_exclusion_identities() -> None:
    """Eq. eq:recoverpivac: Pvac(J) = sum over the S avoiding J of M_S."""
    for case_id, block_case_id, ports, frozen, patterns in INCLUSION_EXCLUSION_CASES:
        block_case = next(c for c in POVM_BLOCK_CASES if c.case_id == block_case_id)
        labels, family = _no_click(block_case.instrument_case_id)
        photons = block_case.photon_number
        subset = frozenset(labels.index(label) for label in ports)
        expected = mat_value(frozen)
        assert_matches(
            family.pi_vac_block(subset, photons), expected, TOLERANCE.eps_4, case_id
        )
        # The frozen fibre -- the patterns with a non-zero block -- sums to it,
        summed = sum(
            element_block(family, [labels.index(p) for p in pattern], photons)
            for pattern in patterns
        )
        assert_matches(summed, expected, TOLERANCE.eps_4, f"{case_id} frozen fibre")
        # and so does the FULL sum over every S avoiding J.
        full = sum(
            element_block(family, pattern, photons)
            for pattern in raw_alphabet(family.port_count)
            if not (pattern & subset)
        )
        assert_matches(full, expected, TOLERANCE.eps_4, f"{case_id} full sum")


def _coarse(case_id: str) -> tuple[tuple[str, ...], CoarseGraining]:
    """Return the port labels and the declared coarse-graining of a case."""
    case = next(c for c in COARSE_GRAINING_CASES if c.case_id == case_id)
    labels = case.port_labels
    assignment = {
        frozenset(labels.index(port) for port in pattern): letter
        for letter, patterns in case.fibres
        for pattern in patterns
    }
    alphabet = tuple(letter for _, letter in case.alphabet)
    return labels, CoarseGraining(len(labels), alphabet, assignment)


@pytest.mark.contract
@pytest.mark.oracle
def test_every_declared_coarse_graining_is_a_total_surjection() -> None:
    """Definition def:coarse: the fibres PARTITION the raw alphabet."""
    assert rp_oracle("O-RP-COARSE").claims == ("RC7",)
    for case in COARSE_GRAINING_CASES:
        labels, coarse = _coarse(case.case_id)
        assert check_coarse_graining(coarse) is None, case.case_id
        assert case.surjective is True
        sizes = [len(coarse.fibre(letter)) for letter in coarse.alphabet]
        assert sum(sizes) == 2 ** len(labels), case.case_id
        assert len({coarse.identifier(v) for v in coarse.alphabet}) == len(
            coarse.alphabet
        ), case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_two_declared_alphabets_on_one_receiver_give_two_povms() -> None:
    """Requirement req:declared-alphabet: the alphabet is DATA, not the optics."""
    _, family = _no_click("I-BB84")
    for case_id in ("CG-SIX", "CG-THREE"):
        _, coarse = _coarse(case_id)
        blocks = {
            letter: coarse_block(family, coarse, letter, 1)
            for letter in coarse.alphabet
        }
        total = sum(blocks.values())
        assert_matches(total, np.eye(2), TOLERANCE.eps_4, f"{case_id} completeness")
        for letter, block in blocks.items():
            assert float(np.min(eigenvalues(block))) >= -TOLERANCE.eps_2, (
                case_id,
                letter,
            )
    # Nothing in the optics changed between the two declarations.
    six_labels, six = _coarse("CG-SIX")
    three_labels, three = _coarse("CG-THREE")
    assert six_labels == three_labels
    assert six.alphabet != three.alphabet


@pytest.mark.contract
@pytest.mark.oracle
def test_bounds_add_under_the_coarse_graining() -> None:
    """Theorem thm:coarse-graining (ii), at the slot's single outcome set."""
    for _, block_case_id, patterns, weight, letter, expected in ADDITIVITY_CASES:
        block_case = next(c for c in POVM_BLOCK_CASES if c.case_id == block_case_id)
        labels, _ = _no_click(block_case.instrument_case_id)
        coarse_case_id = "CG-SIX" if len(labels) == 4 else "CG-CONSTANT"
        if coarse_case_id == "CG-CONSTANT":
            # The K = 2 receiver's multiclick set is the single pattern {1,2};
            # its emitted letter under the six-outcome declaration is `mc`.
            coarse = CoarseGraining(
                2,
                ("nc", "sc_0", "sc_1", "mc"),
                {
                    frozenset(): "nc",
                    frozenset({0}): "sc_0",
                    frozenset({1}): "sc_1",
                    frozenset({0, 1}): "mc",
                },
            )
        else:
            _, coarse = _coarse("CG-SIX")
        bounded = [
            ([labels.index(port) for port in pattern], float(weight) / len(patterns))
            for pattern in patterns
        ]
        assert fibre_bound(coarse, letter, bounded) == pytest.approx(
            float(expected), abs=TOLERANCE.eps_2
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_coarsening_is_lossy_in_one_direction_only() -> None:
    """Theorem thm:coarse-graining (iii) with the contract's own counterexample."""
    _, family = _no_click("I-SINGULAR")
    coarse = CoarseGraining(2, ("v",), dict.fromkeys(raw_alphabet(2), "v"))
    assert check_coarse_graining(coarse) is None
    block = coarse_block(family, coarse, "v", 2)
    assert_matches(block, np.eye(3), TOLERANCE.eps_4, "the constant coarse-graining")
    # The coarse element is the identity with the perfect bound 1 ...
    assert float(np.min(eigenvalues(block))) == pytest.approx(1.0, abs=TOLERANCE.eps_2)
    # ... and one of its fibres has smallest eigenvalue ZERO on the same block.
    fibre = element_block(family, (0, 1), 2)
    assert float(np.min(eigenvalues(fibre))) == pytest.approx(0.0, abs=TOLERANCE.eps_2)
    frozen = next(c for c in POVM_BLOCK_CASES if c.case_id == "PB-SINGULAR-n2")
    assert_matches(
        fibre, mat_value(frozen.multiclick), TOLERANCE.eps_4, "PB-SINGULAR-n2"
    )
