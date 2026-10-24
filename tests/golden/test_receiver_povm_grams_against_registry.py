"""Port Grams and representation independence (registry RC4, RC5), vs the registry.

Golden replay of ``INSTRUMENT_CASES``, ``REPRESENTATION_INDEPENDENCE_CASES``,
``ONE_MODE_PER_PORT_CASES`` and ``EXTINCTION_CASES`` (oracle entries
``O-RP-GRAMS`` and ``O-RP-REPRESENTATION``).

Five things the entries say the SET pins, each with a test here: admissibility
on every instrument; the rank bound with BOTH arguments of its minimum
attained; the deficiency identity WITH BOTH SUMMANDS EXERCISED SEPARATELY;
vacuum elimination and the dilation changing nothing; and the operational index
order, which the frozen ``I-BB84`` would catch a transposition of because its
``-i`` phases cancel in exactly one of the two orders.
"""

from __future__ import annotations

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE, assert_matches, mat_value
from registry_receiver_povm import (
    EXTINCTION_CASES,
    INSTRUMENT_CASES,
    ONE_MODE_PER_PORT_CASES,
    REPRESENTATION_INDEPENDENCE_CASES,
    rp_oracle,
)

from certiqs_key.receiver import (
    GramFamily,
    check_gram_family_admissible,
    check_rank_against_port_sizes,
    deficiency_identity,
    extinction_criterion,
    one_mode_per_port,
    port_grams,
    realizing_instrument,
    unitary_dilation,
)


def _family(case_id: str) -> tuple[np.ndarray, GramFamily]:
    """Return the frozen instrument matrix and its RECOMPUTED Gram family."""
    case = next(c for c in INSTRUMENT_CASES if c.case_id == case_id)
    gamma_inp = mat_value(case.gamma_inp)
    labels = tuple(label for label, _ in case.port_map)
    rows = [modes for _, modes in case.port_map]
    return gamma_inp, GramFamily(labels, port_grams(gamma_inp, rows))


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_gram_is_recomputed_from_its_instrument_matrix() -> None:
    """Eq. eq:gramdef, with the operational index order of `matrix_convention`."""
    assert rp_oracle("O-RP-GRAMS").claims == ("RC4",)
    for case in INSTRUMENT_CASES:
        _, family = _family(case.case_id)
        for (label, frozen), computed in zip(case.grams, family.matrices, strict=True):
            assert_matches(
                computed,
                mat_value(frozen),
                TOLERANCE.eps_2,
                f"{case.case_id} port {label}",
            )
        assert_matches(
            family.a_sigma, mat_value(case.a_sigma), TOLERANCE.eps_2, case.case_id
        )
        assert_matches(
            family.deficiency,
            mat_value(case.deficiency),
            TOLERANCE.eps_2,
            case.case_id,
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_instrument_is_admissible_with_the_frozen_ranks() -> None:
    """Theorem thm:port-grams (i), (ii): admissibility and the rank bound."""
    for case in INSTRUMENT_CASES:
        _, family = _family(case.case_id)
        assert check_gram_family_admissible(family, TOLERANCE) is None, case.case_id
        frozen_ranks = tuple(rank for _, rank in case.ranks)
        # eq:eps2rank at the declared eps_2 (def:tolmap (ii)); the frozen
        # ranks are unchanged -- every eigenvalue here is far from eps_2.
        assert family.ranks(TOLERANCE.eps_2) == frozen_ranks, case.case_id
        port_sizes = [len(modes) for _, modes in case.port_map]
        assert check_rank_against_port_sizes(family, port_sizes, TOLERANCE) is None, (
            case.case_id
        )
        for rank, size in zip(frozen_ranks, port_sizes, strict=True):
            assert rank <= min(family.dimension, size), case.case_id


@pytest.mark.contract
def test_both_arguments_of_the_rank_minimum_are_attained() -> None:
    """Theorem thm:port-grams (ii) on I-RANK2: min(|Inp|, |P_k|) at 2 and at 1."""
    _, family = _family("I-RANK2")
    assert family.dimension == 2
    assert family.ranks(TOLERANCE.eps_2) == (2, 1)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_deficiency_identity_with_both_summands_separately() -> None:
    """Eq. eq:deficiencyid, and the three instruments that separate it."""
    expectations = {
        "I-DILATION-SUB": ("through", "zero"),
        "I-DILATION-UNITARY": ("zero", "unmonitored"),
        "I-UNMONITORED": ("both", "both"),
    }
    for case in INSTRUMENT_CASES:
        gamma_inp, family = _family(case.case_id)
        terms = deficiency_identity(gamma_inp, family, case.unmonitored)
        assert_matches(
            terms.defect,
            np.zeros_like(terms.defect),
            TOLERANCE.eps_3,
            f"{case.case_id} r_3",
        )
        # Both summands are positive semidefinite (Theorem thm:efficiency (v)).
        for summand in (terms.left_through_dilation, terms.reached_unmonitored):
            assert float(np.min(np.linalg.eigvalsh(summand).real)) >= -TOLERANCE.eps_2
        if case.case_id not in expectations:
            continue
        through = float(np.max(np.abs(terms.left_through_dilation)))
        reached = float(np.max(np.abs(terms.reached_unmonitored)))
        if case.case_id == "I-DILATION-SUB":
            assert through > 0.5 and reached == pytest.approx(0.0, abs=1e-12)
        elif case.case_id == "I-DILATION-UNITARY":
            assert through == pytest.approx(0.0, abs=1e-12) and reached > 0.5
        else:
            assert through > 0.0 and reached > 0.0


@pytest.mark.contract
@pytest.mark.oracle
def test_the_lossless_field_is_about_gamma_inp_and_not_the_deficiency() -> None:
    """Definition def:embed on Gamma_Inp, which I-DILATION-* separates."""
    for case in INSTRUMENT_CASES:
        gamma_inp, _ = _family(case.case_id)
        defect = gamma_inp.conj().T @ gamma_inp - np.eye(gamma_inp.shape[1])
        is_isometry = bool(np.max(np.abs(defect)) <= TOLERANCE.eps_1)
        assert is_isometry is case.lossless, case.case_id
    # The separating pair: one device, two descriptions, deficiency 16/25 in
    # both, and losslessness of Gamma_Inp TRUE in one and FALSE in the other.
    sub = next(c for c in INSTRUMENT_CASES if c.case_id == "I-DILATION-SUB")
    dil = next(c for c in INSTRUMENT_CASES if c.case_id == "I-DILATION-UNITARY")
    assert sub.lossless is False and dil.lossless is True
    assert_matches(
        mat_value(sub.deficiency), mat_value(dil.deficiency), 0.0, "deficiency 16/25"
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_unitary_dilation_reproduces_the_sub_unitary_grams() -> None:
    """Lemma lem:dilation and Theorem thm:port-grams (v): the same measurement."""
    gamma_sub, family_sub = _family("I-DILATION-SUB")
    dilated = unitary_dilation(gamma_sub)
    # A unitary on system plus environment ...
    assert_matches(
        dilated.conj().T @ dilated,
        np.eye(2, dtype=np.complex128),
        TOLERANCE.eps_1,
        "the dilation is unitary",
    )
    # ... whose first column is the frozen I-DILATION-UNITARY instrument ...
    gamma_dil, family_dil = _family("I-DILATION-UNITARY")
    assert_matches(dilated[:, [0]], gamma_dil, TOLERANCE.eps_1, "the dilated column")
    # ... and whose port Gram is IDENTICAL, not approximately equal.
    assert_matches(
        family_dil.matrices[0],
        family_sub.matrices[0],
        TOLERANCE.eps_2,
        "A_1 = 9/25 in both descriptions",
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_representation_cases_relate_grams_to_instrument_matrices() -> None:
    """Theorem thm:representation-independence (i), (iii) and Corollary cor:phases with its hypothesis."""  # noqa: E501
    assert rp_oracle("O-RP-REPRESENTATION").claims == ("RC5",)
    for case in REPRESENTATION_INDEPENDENCE_CASES:
        gamma_a = mat_value(case.gamma_a)
        gamma_b = mat_value(case.gamma_b)
        grams_a = port_grams(gamma_a, case.port_map_a)
        grams_b = port_grams(gamma_b, case.port_map_b)
        for computed, frozen in zip(grams_a, case.grams_a, strict=True):
            assert_matches(
                computed, mat_value(frozen), TOLERANCE.eps_2, f"{case.case_id} a"
            )
        for computed, frozen in zip(grams_b, case.grams_b, strict=True):
            assert_matches(
                computed, mat_value(frozen), TOLERANCE.eps_2, f"{case.case_id} b"
            )
        matrices_equal = gamma_a.shape == gamma_b.shape and bool(
            np.max(np.abs(gamma_a - gamma_b)) <= TOLERANCE.eps_1
        )
        assert matrices_equal is case.matrices_equal, case.case_id
        grams_equal = all(
            float(np.max(np.abs(left - right))) <= TOLERANCE.eps_2
            for left, right in zip(grams_a, grams_b, strict=True)
        )
        assert grams_equal is case.grams_equal, case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_the_symmetric_beamsplitter_grams_are_the_conjugates() -> None:
    """Remark rem:bsconv's evidence, recomputed: the input factor bites."""
    case = next(
        c
        for c in REPRESENTATION_INDEPENDENCE_CASES
        if c.case_id == "REP-BSCONV-SYMMETRIC"
    )
    gamma_a = mat_value(case.gamma_a)
    gamma_b = mat_value(case.gamma_b)
    input_phase = np.diag([1.0, 1.0j]).astype(np.complex128)
    output_phase = np.diag([1.0, 1.0j]).astype(np.complex128)
    # The exact factorization the registry freezes.
    assert_matches(
        gamma_b,
        output_phase @ gamma_a @ input_phase,
        TOLERANCE.eps_1,
        "representation independence",
    )
    # The OUTPUT factor alone changes no Gram (Theorem thm:representation-independence
    # (iii)) ...
    covered = next(
        c
        for c in REPRESENTATION_INDEPENDENCE_CASES
        if c.case_id == "REP-BSCONV-OUTPUT-PHASE"
    )
    assert covered.grams_equal is True
    # ... and the INPUT factor conjugates every Gram.
    for gram_a, frozen_b in zip(case.grams_a, case.grams_b, strict=True):
        conjugated = input_phase.conj().T @ mat_value(gram_a) @ input_phase
        assert_matches(
            conjugated,
            mat_value(frozen_b),
            TOLERANCE.eps_2,
            "representation independence, Gram",
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_realizability_on_a_family_with_a_rank_two_port() -> None:
    """Theorem thm:representation-independence (ii): the A_k^{1/2} construction, a different shape."""  # noqa: E501
    case = next(
        c for c in REPRESENTATION_INDEPENDENCE_CASES if c.case_id == "REP-REALIZE-RANK2"
    )
    declared = GramFamily(
        ("1", "2"), tuple(mat_value(matrix) for matrix in case.grams_a)
    )
    realized = realizing_instrument(declared)
    assert_matches(realized, mat_value(case.gamma_b), TOLERANCE.eps_1, "A_k^{1/2}")
    rebuilt = port_grams(realized, case.port_map_b)
    for computed, frozen in zip(rebuilt, case.grams_a, strict=True):
        assert_matches(computed, mat_value(frozen), TOLERANCE.eps_2, "realized Grams")
    # A contraction, and of a DIFFERENT SHAPE from the instrument it reproduces.
    assert realized.shape != mat_value(case.gamma_a).shape
    defect = realized.conj().T @ realized - np.eye(realized.shape[1])
    assert float(np.max(np.linalg.eigvalsh(defect).real)) <= TOLERANCE.eps_1


@pytest.mark.contract
@pytest.mark.oracle
def test_the_one_mode_per_port_criterion_holds_and_fails() -> None:
    """Thm. thm:representation-independence (iv); Req. req:one-mode-per-port.

    CERTIFIED, never a default.
    """
    for case_id, verdict, max_rank, _ in ONE_MODE_PER_PORT_CASES:
        _, family = _family(case_id)
        assert one_mode_per_port(family, TOLERANCE.eps_2) is verdict, case_id
        assert max(family.ranks(TOLERANCE.eps_2)) == max_rank, case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_the_extinction_criterion_and_its_dimension_caveat() -> None:
    """Corollary cor:extinction, and what it does NOT say above two modes."""
    frozen = {row[0]: row for row in EXTINCTION_CASES}
    _, bb84 = _family("I-BB84")
    verdict = extinction_criterion(bb84.matrices[0], TOLERANCE.eps_2)
    assert verdict.criterion_applies is True
    assert verdict.has_null_direction is True
    assert verdict.rank == frozen["EXT-BB84-H"][3]

    _, rank2 = _family("I-RANK2")
    verdict = extinction_criterion(rank2.matrices[0], TOLERANCE.eps_2)
    assert verdict.criterion_applies is True
    assert verdict.has_null_direction is False
    assert verdict.rank == frozen["EXT-RANK2"][3]

    # THE CAVEAT: at |Inp| = 3 one extinguished direction leaves rank 2.
    three_modes = np.diag([1.0, 0.5, 0.0]).astype(np.complex128)
    verdict = extinction_criterion(three_modes, TOLERANCE.eps_2)
    assert verdict.criterion_applies is False
    assert verdict.has_null_direction is True
    assert verdict.rank == frozen["EXT-DIM3-CAVEAT"][3]
