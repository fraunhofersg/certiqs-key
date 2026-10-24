"""The component catalogue C1-C10 (registry RC3), against the registry.

Golden replay of ``CATALOGUE_CASES`` and ``DECIBEL_CONVERSIONS`` (oracle entry
``O-RP-CATALOGUE``). Every entry type is covered at an interior AND a boundary
parameter tuple, because Theorem ``thm:catalogue-admissibility`` is a statement about
THE WHOLE DECLARED DOMAIN; the lossless column is part of the claim, an IFF, and every
case carries its verdict.

TWO CASES ARE TRAPS AND ARE TESTED AS SUCH: the half-wave plate written as a
REAL matrix, which silently drops the physical phase ``exp(-i delta / 2)``, and
the half-open domain endpoint ``delta = 2 pi``, whose clipped value would be
admissible and wrong.

THE PARAMETER TUPLES ARE REBUILT FROM THE FROZEN DESCRIPTIONS. The registry
writes them as prose ("cos 2theta = 3/5"), so the builder below is the reading;
each entry is annotated with the frozen ``parameters`` string it realises, and
the frozen MATRIX is what decides whether the reading was right.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE, alg_value, assert_matches, mat_value
from registry_receiver_povm import (
    CATALOGUE_CASES,
    CATALOGUE_IDS,
    DECIBEL_CONVERSIONS,
    rp_oracle,
)

from certiqs_key.receiver import (
    CATALOGUE_IDS as MODULE_CATALOGUE_IDS,
)
from certiqs_key.receiver import (
    Beamsplitter,
    Component,
    GenericBlock,
    Loss,
    Mirror,
    ModeRouting,
    PhaseShifter,
    Polarizer,
    PolarizingBeamsplitter,
    Refusal,
    RefusalReason,
    Retarder,
    Rotator,
    decibel_to_transmittance,
    splitting_ratio_presentation,
)

#: The angle with cos = 3/5, sin = 4/5, and the plate angle with
#: cos 2theta = 3/5, sin 2theta = 4/5.
_ANGLE_3_4_5 = math.atan2(0.8, 0.6)
_PLATE_3_4_5 = _ANGLE_3_4_5 / 2.0


def _build(case_id: str) -> Component:
    """Return the component the frozen case declares."""
    builders: dict[str, Component] = {
        "C1-interior": Beamsplitter(F(9, 25), 0, 0, 0),
        "C1-boundary-x1": Beamsplitter(1, 0, 0, 0),
        "C1-boundary-x0": Beamsplitter(0, 0, 0, 0),
        "C1-lossy": Beamsplitter(F(9, 25), 0, F(3, 4), 0),
        "C1-phase": Beamsplitter(F(9, 25), math.pi / 2, 0, 0),
        "C1-half": Beamsplitter(F(1, 2), 0, 0, 0),
        "C2-boundary-ideal": PolarizingBeamsplitter(1, 0, 0, 0, 0, 0),
        "C2-interior": PolarizingBeamsplitter(F(9, 25), F(16, 25), 0, 0, 0, 0),
        "C2-lossy": PolarizingBeamsplitter(1, 0, 0, 0, F(3, 4), 0),
        "C3-hwp-pi8": Retarder.half_wave(math.pi / 8, 0),
        "C3-hwp-rational": Retarder.half_wave(_PLATE_3_4_5, 0),
        "C3-boundary-delta0": Retarder(0, 0, 0),
        "C3-qwp-theta0": Retarder.quarter_wave(0, 0),
        "C3-lossy": Retarder.half_wave(_PLATE_3_4_5, F(3, 4)),
        "C4-interior": Rotator(_ANGLE_3_4_5),
        "C4-boundary-rho0": Rotator(0),
        "C5-boundary-ideal": Mirror(1, 1, 0, 0),
        "C5-flip": Mirror(1, 1, 0, 0, handedness_flip=True),
        "C5-interior": Mirror(F(9, 25), 1, 0, math.pi),
        "C6-boundary": PhaseShifter((0, math.pi)),
        "C6-interior": PhaseShifter((math.pi / 2, math.pi / 2)),
        "C7-boundary-unit": Loss((1, 1)),
        "C7-interior": Loss((1, F(1, 4))),
        "C7-boundary-zero": Loss((1, 0)),
        "C8-interior": Polarizer(_ANGLE_3_4_5, 1, 0),
        "C8-boundary-identity": Polarizer(0, 1, 1),
        "C8-partial": Polarizer(0, 1, F(1, 4)),
        "C9-swap": ModeRouting((1, 0)),
        "C9-identity": ModeRouting((0, 1)),
        "C10-admissible": GenericBlock.of(((F(1, 2), 0), (0, F(1, 2)))),
        "C10-lossless": GenericBlock.of(((0, 1), (1, 0))),
    }
    if case_id == "C7-decibel-20":
        built = Loss.from_decibels((0, 20))
        assert isinstance(built, Loss)
        return built
    return builders[case_id]


def _element_matrix(case_id: str, component: Component) -> np.ndarray:
    """Return the matrix the registry freezes for this case.

    "C1 and C2 are frozen as the CORE matrices Eq. eq:bs and Eq. eq:pbs
    display; the full element is the core tensored with the identity on
    polarization (C1) or conjugated by the basis permutation Xi (C2, already
    applied below)."
    """
    if case_id.startswith("C1-"):
        assert isinstance(component, Beamsplitter)
        return component.core()
    return component.matrix()


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_catalogue_matrix_is_reproduced() -> None:
    """Table tab:catalogue, entry by entry, at every frozen parameter tuple."""
    assert rp_oracle("O-RP-CATALOGUE").claims == ("RC3",)
    for case in CATALOGUE_CASES:
        if case.case_id == "C3-hwp-DROPPED-PHASE":
            continue  # not the contract's element; see its own test below
        component = _build(case.case_id)
        assert component.entry_id == case.entry_id, case.case_id
        assert_matches(
            _element_matrix(case.case_id, component),
            mat_value(case.matrix),
            TOLERANCE.eps_1,
            case.case_id,
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_lossless_column_is_reproduced_as_an_iff() -> None:
    """Theorem thm:catalogue-admissibility: lossless EXACTLY on the subfamily the table names."""  # noqa: E501
    for case in CATALOGUE_CASES:
        if case.case_id == "C3-hwp-DROPPED-PHASE":
            continue
        component = _build(case.case_id)
        assert component.is_lossless() is case.lossless, case.case_id
        # And the verdict agrees with the matrix: lossless iff an isometry.
        matrix = _element_matrix(case.case_id, component)
        defect = matrix.conj().T @ matrix - np.eye(matrix.shape[1])
        is_isometry = bool(np.max(np.abs(defect)) <= TOLERANCE.eps_1)
        assert is_isometry is case.lossless, case.case_id


@pytest.mark.contract
def test_every_frozen_parameter_tuple_is_inside_its_declared_domain() -> None:
    """Definition def:graph (E1) at every frozen case: none is refused."""
    for case in CATALOGUE_CASES:
        if case.case_id == "C3-hwp-DROPPED-PHASE":
            continue
        component = _build(case.case_id)
        assert component.check_domain(TOLERANCE) is None, case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_the_beamsplitter_determinant_is_minus_one() -> None:
    """The `beamsplitter_convention`: real at phi = 0 with det B = -1."""
    for case in CATALOGUE_CASES:
        if case.determinant is None:
            continue
        component = _build(case.case_id)
        assert isinstance(component, Beamsplitter)
        determinant = complex(np.linalg.det(component.core()))
        assert determinant == pytest.approx(
            alg_value(case.determinant), abs=TOLERANCE.eps_1
        ), case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_the_retarder_carries_its_physical_phase_and_the_trap_does_not() -> None:
    """The `waveplate_convention`, with C3-hwp-DROPPED-PHASE beside it."""
    correct = _build("C3-hwp-rational").matrix()
    trap = mat_value(
        next(c for c in CATALOGUE_CASES if c.case_id == "C3-hwp-DROPPED-PHASE").matrix
    )
    # The module's element is NOT the real matrix ...
    assert np.max(np.abs(correct - trap)) > 1.0
    # ... and differs from it by exactly the factor exp(-i delta / 2) = -i.
    assert_matches(correct, -1j * trap, TOLERANCE.eps_1, "the dropped HWP phase")
    # The trap is unitary too, which is why it would pass every other check.
    assert np.max(np.abs(trap.conj().T @ trap - np.eye(2))) <= TOLERANCE.eps_1


@pytest.mark.contract
@pytest.mark.oracle
def test_the_fifty_fifty_beamsplitter_has_rational_grams() -> None:
    """Theorem thm:representation-independence (i) in miniature, on catalogue case C1-half."""  # noqa: E501
    core = _build("C1-half").core()
    assert isinstance(core, np.ndarray)
    root_half = math.sqrt(0.5)
    assert float(core[0, 0].real) == pytest.approx(root_half, abs=1e-15)
    # Two single-mode ports on the two outputs, one declared input mode.
    column = core[:, [0]]
    gram_1 = (column[[0], :].conj().T @ column[[0], :]).real
    gram_2 = (column[[1], :].conj().T @ column[[1], :]).real
    assert float(gram_1[0, 0]) == pytest.approx(0.5, abs=1e-15)
    assert float(gram_2[0, 0]) == pytest.approx(0.5, abs=1e-15)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_decibel_conversion_happens_at_validation() -> None:
    """`parameters.units`: the CONVERTED value is what the artifact carries."""
    for decibels, expected in DECIBEL_CONVERSIONS:
        assert decibel_to_transmittance(float(decibels)) == pytest.approx(
            float(expected), rel=1e-12
        )
    element = Loss.from_decibels((0, 20))
    assert isinstance(element, Loss)
    assert_matches(
        element.matrix(),
        np.diag([1.0, 0.1]).astype(np.complex128),
        TOLERANCE.eps_1,
        "C7-decibel-20",
    )
    refusal = Loss.from_decibels((-1,))
    assert isinstance(refusal, Refusal)
    assert refusal.reason is RefusalReason.DECIBEL_LOSS_NEGATIVE


@pytest.mark.contract
def test_a_splitting_ratio_presentation_is_refused_as_unsupported() -> None:
    """`parameters.units`: a splitting ratio is refused, with no conversion rule."""
    refusal = splitting_ratio_presentation((90, 10))
    assert isinstance(refusal, Refusal)
    assert refusal.reason is RefusalReason.SPLITTING_RATIO_PRESENTATION_UNSUPPORTED
    assert "x" in refusal.detail
    # Nothing is converted: no reading of "90:10" reaches a transmittance here.
    assert "0.9" not in refusal.detail and "0.81" not in refusal.detail


@pytest.mark.contract
def test_the_mirror_handedness_flag_defaults_to_false_and_is_never_implicit() -> None:
    """The `mirror_handedness` convention: the one default the contract fixes."""
    default = Mirror(1, 1, 0, 0)
    assert default.handedness_flip is False
    assert_matches(
        default.matrix(), np.eye(2, dtype=np.complex128), TOLERANCE.eps_1, "fl = false"
    )
    flipped = Mirror(1, 1, 0, 0, handedness_flip=True)
    assert_matches(
        flipped.matrix(),
        np.diag([1.0, -1.0]).astype(np.complex128),
        TOLERANCE.eps_1,
        "fl = true",
    )
    assert np.max(np.abs(default.matrix() - flipped.matrix())) == pytest.approx(2.0)


@pytest.mark.contract
def test_the_ten_catalogue_ids_are_the_table_s() -> None:
    """Table tab:catalogue has ten entry types and the module carries them."""
    assert MODULE_CATALOGUE_IDS == CATALOGUE_IDS
    covered = {case.entry_id for case in CATALOGUE_CASES}
    assert covered == set(CATALOGUE_IDS)
