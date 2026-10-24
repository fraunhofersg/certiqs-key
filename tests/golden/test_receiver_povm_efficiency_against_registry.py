"""Detection efficiency, exactly once (registry RC10), against the registry.

Golden replay of ``EFFICIENCY_CASES``, ``D_ETA_CASES``, ``EFFICIENCY_RECORD``
and ``PATH_PRODUCT_CASES`` (oracle entry ``O-RP-EFFICIENCY``).

TWO TRAPS ARE FROZEN AS WRONG ANSWERS AND ARE TESTED AS SUCH: ``D_eta`` without
its second summand, which annihilates every unmonitored mode and breaks
``D_eta = 1`` at unit efficiency; and the path-product audit, which at a
balanced Mach-Zehnder reports a spurious 50 per cent loss that does not exist.
Neither is implemented in :mod:`certiqs_key.receiver`; the tests below show the
module produces the CORRECT answer and that the frozen wrong one differs.
"""

from __future__ import annotations

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE, assert_matches, mat_value
from registry_receiver_povm import (
    D_ETA_CASES,
    DECIBEL_CONVERSIONS,
    EFFICIENCY_CASES,
    EFFICIENCY_RECORD,
    INSTRUMENT_CASES,
    PATH_PRODUCT_CASES,
    rp_oracle,
)

from certiqs_key.receiver import (
    GramFamily,
    Loss,
    apply_uniform_efficiency,
    beamsplitter_core,
    decibel_to_transmittance,
    deficiency_identity,
    detector_layer_matrix,
    efficiency_record,
    is_multiple_of_a_sigma,
    nonuniform_effective_gram,
    port_grams,
    weighted_total,
)


def _family(case_id: str) -> tuple[np.ndarray, GramFamily]:
    """Return the frozen instrument matrix and its Gram family."""
    case = next(c for c in INSTRUMENT_CASES if c.case_id == case_id)
    gamma_inp = mat_value(case.gamma_inp)
    labels = tuple(label for label, _ in case.port_map)
    rows = [modes for _, modes in case.port_map]
    return gamma_inp, GramFamily(labels, port_grams(gamma_inp, rows))


@pytest.mark.contract
@pytest.mark.oracle
def test_uniform_efficiency_is_a_scalar_on_the_gram_and_preserves_rank() -> None:
    """Theorem thm:efficiency (i), Eq. eq:etagram, on the two frozen uniform cases."""
    assert rp_oracle("O-RP-EFFICIENCY").claims == ("RC10",)
    _, family = _family("I-BB84")
    for case in EFFICIENCY_CASES:
        if not case.uniform_within_port:
            continue
        efficiencies = [float(eta) for _, eta, _, _ in case.ports]
        ranks_before = tuple(rank for _, _, rank, _ in case.ports)
        ranks_after = tuple(rank for _, _, _, rank in case.ports)
        assert family.ranks(TOLERANCE.eps_2) == ranks_before, case.case_id
        scaled = apply_uniform_efficiency(family, efficiencies)
        assert scaled.ranks(TOLERANCE.eps_2) == ranks_after, case.case_id
        for before, after, eta in zip(
            family.matrices, scaled.matrices, efficiencies, strict=True
        ):
            assert_matches(after, eta * before, TOLERANCE.eps_2, case.case_id)
        assert_matches(
            weighted_total(family, efficiencies),
            mat_value(case.weighted_total),
            TOLERANCE.eps_2,
            case.case_id,
        )
        assert (
            is_multiple_of_a_sigma(family, efficiencies, TOLERANCE.eps_2)
            is case.is_multiple_of_a_sigma
        ), case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_a_non_uniform_within_port_attenuation_can_lower_the_rank() -> None:
    """Theorem thm:efficiency (ii) and Remark rem:effrank's own example."""
    case = next(c for c in EFFICIENCY_CASES if c.case_id == "EFF-NONUNIFORM-RANK-DROPS")
    # A port collecting TWO modes with rows (1, 0) and (0, 1/2).
    gamma_inp = np.asarray([[1.0, 0.0], [0.0, 0.5]], dtype=np.complex128)
    before = port_grams(gamma_inp, [(0, 1)])[0]
    _, _, rank_before, rank_after = case.ports[0]
    assert np.linalg.matrix_rank(before) == rank_before
    after = nonuniform_effective_gram(gamma_inp, (0, 1), (1.0, 0.0))
    assert np.linalg.matrix_rank(after) == rank_after
    assert_matches(after, mat_value(case.weighted_total), TOLERANCE.eps_2, case.case_id)
    # The rank test of Theorem thm:representation-independence (iv) must be run AFTER,
    # never before.
    assert rank_before > rank_after


@pytest.mark.contract
@pytest.mark.oracle
def test_the_detector_layer_keeps_its_second_summand() -> None:
    """Definition def:compile's D_eta, and the frozen WRONG version beside it."""
    ports = [(0,), (1,)]
    mode_count = 3  # (o_0, o_1, o_2) with o_2 unmonitored
    frozen = {row[0]: row for row in D_ETA_CASES}
    for case_id in ("DETA-UNIT", "DETA-INTERIOR"):
        _, etas, diagonal, is_identity, _ = frozen[case_id]
        computed = detector_layer_matrix(ports, [float(v) for v in etas], mode_count)
        assert_matches(
            computed,
            np.diag([float(value) for value in diagonal]).astype(np.complex128),
            TOLERANCE.eps_1,
            case_id,
        )
        equals_identity = bool(
            np.max(np.abs(computed - np.eye(mode_count))) <= TOLERANCE.eps_1
        )
        assert equals_identity is is_identity, case_id
    # THE TRAP: the second summand dropped would annihilate the unmonitored
    # mode. The module does not produce it.
    _, etas, wrong_diagonal, _, _ = frozen["DETA-WITHOUT-SECOND-SUMMAND"]
    computed = detector_layer_matrix(ports, [float(v) for v in etas], mode_count)
    wrong = np.diag([float(value) for value in wrong_diagonal]).astype(np.complex128)
    assert np.max(np.abs(computed - wrong)) == pytest.approx(1.0, abs=1e-12)
    assert float(computed[2, 2].real) == pytest.approx(1.0, abs=1e-15)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_composition_record_lists_two_equal_values_as_two_rows() -> None:
    """Requirements req:efficiency-record and req:efficiency-convention."""
    chain = (
        ("bs_1", "C1", ((float(EFFICIENCY_RECORD[0][0]), "x"),)),
        ("loss_a", "C7", ((float(EFFICIENCY_RECORD[1][0]), "eta_m0"),)),
        ("pol_b", "C8", ((float(EFFICIENCY_RECORD[2][0]), "t_perp"),)),
    )
    detector = (("H", float(EFFICIENCY_RECORD[3][0])),)
    rows = efficiency_record(chain, detector)
    assert len(rows) == len(EFFICIENCY_RECORD)
    for row, (value, element, site) in zip(rows, EFFICIENCY_RECORD, strict=True):
        assert row.value == pytest.approx(float(value), abs=1e-15)
        # The registry's `element` and `site` strings are its own prose; what is
        # reproduced is their CONTENT: the declaring element and the one site.
        assert row.element.startswith(element.split()[0])
        assert row.site.split()[0] in site
    # Two elements carrying EQUAL numerical values are still two rows.
    equal = [row for row in rows if row.value == pytest.approx(0.5)]
    assert len(equal) == 2
    assert equal[0].element != equal[1].element
    assert equal[0].site != equal[1].site
    # And so are the two rows that share 9/25 across the chain and the layer.
    shared = [row for row in rows if row.value == pytest.approx(9 / 25)]
    assert len(shared) == 2
    assert shared[1].site == "terminal factor D_eta"


@pytest.mark.contract
@pytest.mark.oracle
def test_the_deficiency_identity_disagrees_with_a_path_product_audit() -> None:
    """Remark rem:wrongcheck at the balanced Mach-Zehnder, Eq. eq:mz."""
    core = beamsplitter_core(0.5, 0.0)
    phase = np.diag([1.0, 1.0]).astype(np.complex128)  # phi = 0
    compiled = core @ phase @ core
    frozen = next(c for c in INSTRUMENT_CASES if c.case_id == "I-MZ")
    assert_matches(compiled, mat_value(frozen.gamma_inp), TOLERANCE.eps_1, "eq:mz")
    labels = tuple(label for label, _ in frozen.port_map)
    family = GramFamily(
        labels, port_grams(compiled, [modes for _, modes in frozen.port_map])
    )
    terms = deficiency_identity(compiled, family, frozen.unmonitored)
    trace = float(np.trace(terms.deficiency).real)
    case_id, true_value, audit_claim, discrepancy, _ = PATH_PRODUCT_CASES[0]
    assert case_id == "MZ-PHI-0"
    assert trace == pytest.approx(float(true_value), abs=TOLERANCE.eps_3)
    # The audit's claim is a statement about frozen numbers: this module does
    # not compute a product of transmittances, because the contract proves it
    # is the wrong check.
    assert float(audit_claim) - float(true_value) == pytest.approx(
        float(discrepancy), abs=1e-15
    )
    assert float(discrepancy) > 0.0


@pytest.mark.contract
@pytest.mark.oracle
def test_the_converted_transmittance_is_what_the_efficiency_record_carries() -> None:
    """`parameters.units`, read through Requirement req:efficiency-record.

    THE MODULE'S OWN CONVERSION, not this test's arithmetic: an earlier version
    recomputed ``10^(-L/10)`` here and never called the module, so it could not
    have failed on a wrong conversion. What is checked now is the thing
    Requirement req:efficiency-record is about -- that the CONVERTED value, and
    not the presentation, is what reaches the composition record: the converted
    value is what the artifact carries, and THE PRESENTATION IS NOT A SECOND
    SOURCE OF TRUTH (``interface.yaml`` ``parameters.units``).
    """
    assert len(DECIBEL_CONVERSIONS) == 3
    for decibels, expected in DECIBEL_CONVERSIONS:
        assert decibel_to_transmittance(float(decibels)) == pytest.approx(
            float(expected), rel=1e-12
        )
    element = Loss.from_decibels(tuple(float(row[0]) for row in DECIBEL_CONVERSIONS))
    assert isinstance(element, Loss)
    # Requirement req:efficiency-record: every declared transmittance, by its
    # declared name.
    declared = [value for value, _ in element.loss_parameters()]
    assert declared == pytest.approx(
        [float(expected) for _, expected in DECIBEL_CONVERSIONS], rel=1e-12
    )
    rows = efficiency_record(
        (("loss_db", "C7", element.loss_parameters()),), (("H", 1.0),)
    )
    carried = [row.value for row in rows if row.site == "chain position 1"]
    assert carried == pytest.approx(
        [float(expected) for _, expected in DECIBEL_CONVERSIONS], rel=1e-12
    )
    # And no decibel figure survives into the record.
    assert all(row.value <= 1.0 for row in rows)
