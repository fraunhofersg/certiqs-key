"""Interface vocabulary: the two declared orders, the IDs, and the ledger.

Golden replay of ``MODE_ORDER_CASES``, ``OUTCOME_ALPHABET`` and
``ASSUMPTION_ROWS`` (oracle entry ``O-RP-INTERFACE``).

THE PRECEDENCE RULE IS THE WHOLE POINT. The ``subsystem_order`` convention
(``interface.yaml`` ``conventions``): the two orders disagree "exactly when a
probe path label sorts before a channel path label", and the subsystem order
takes PRECEDENCE, being the order that indexes ``C^Inp``, every Gram and every
block matrix, while the order of Definition ``def:modes`` is the order in which
``M`` is listed in the artifact. An implementation that indexed the Grams by the
``M`` order where the two disagree would permute every one of them, silently --
so the test below builds both and shows they differ.
"""

from __future__ import annotations

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE, assert_matches
from registry_receiver_povm import (
    ASSUMPTION_ROWS_0_3_0,
    MODE_ORDER_CASES,
    NEVER_VERIFIED_0_3_0,
    OUTCOME_ALPHABET,
    is_superseded_0_3_0,
)

from certiqs_key.receiver import (
    ASSUMPTION_MACHINE_KEYS,
    NEVER_VERIFIED,
    AssumptionId,
    CoarseGraining,
    InputModes,
    Mode,
    ModeSpace,
    Polarization,
    check_coarse_graining,
    check_input_modes,
    check_mode_space,
    mode_space_order,
    port_grams,
    raw_alphabet,
    restrict_to_inputs,
)
from certiqs_key.receiver.reasons import CONDITIONALLY_INVOKED


def _modes(case_id: str) -> tuple[Mode, ...]:
    """Return the frozen mode labels of one order case."""
    case = next(c for c in MODE_ORDER_CASES if c.case_id == case_id)
    return tuple(
        Mode(path, Polarization(polarization), tau)
        for path, polarization, tau in case.labels
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_definition_def_modes_order_is_the_frozen_one() -> None:
    """Lexicographic in (p, tau, pi) with H before V -- NOT in label order."""
    for case in MODE_ORDER_CASES:
        modes = _modes(case.case_id)
        assert mode_space_order(modes) == case.mode_space_order, case.case_id
        space = ModeSpace.declare(modes)
        assert check_mode_space(space) is None, case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_the_subsystem_order_takes_precedence_over_the_mode_listing() -> None:
    """The `subsystem_order` convention, exercised in BOTH directions."""
    # ORDER-PROBE-SORTS-FIRST: the probe path A sorts before the channel path Z.
    case = next(c for c in MODE_ORDER_CASES if c.case_id == "ORDER-PROBE-SORTS-FIRST")
    inputs = InputModes(channel=(2, 3), source=(0, 1))
    assert inputs.subsystem_order() == case.input_index_order
    assert case.orders_disagree is True
    assert inputs.subsystem_order() != case.mode_space_order

    # ORDER-AGREE: the same labels with the roles swapped.
    case = next(c for c in MODE_ORDER_CASES if c.case_id == "ORDER-AGREE")
    inputs = InputModes(channel=(0, 1), source=(2, 3))
    assert inputs.subsystem_order() == case.input_index_order
    assert case.orders_disagree is False
    assert inputs.subsystem_order() == case.mode_space_order


@pytest.mark.contract
def test_indexing_a_gram_by_the_wrong_order_permutes_it() -> None:
    """Why the precedence rule is load-bearing, shown as two Gram families."""
    space = ModeSpace.declare(_modes("ORDER-PROBE-SORTS-FIRST"))
    inputs = InputModes(channel=(2, 3), source=(0, 1))
    assert check_input_modes(space, inputs) is None
    # A hand-built instrument on the four modes, with one single-mode port.
    gamma = np.asarray(
        [
            [0.5, 0.0, 0.25, 0.0],
            [0.0, 0.5, 0.0, 0.25],
            [0.0, 0.0, 0.5, 0.0],
            [0.0, 0.0, 0.0, 0.5],
        ],
        dtype=np.complex128,
    )
    correct = port_grams(restrict_to_inputs(gamma, inputs.subsystem_order()), [(0,)])[0]
    listed = port_grams(restrict_to_inputs(gamma, (0, 1, 2, 3)), [(0,)])[0]
    assert np.max(np.abs(correct - listed)) > TOLERANCE.eps_2
    # The two differ by exactly the permutation the convention fixes.
    permutation = np.zeros((4, 4), dtype=np.complex128)
    for position, index in enumerate(inputs.subsystem_order()):
        permutation[index, position] = 1.0
    assert_matches(
        correct, permutation.conj().T @ listed @ permutation, TOLERANCE.eps_2, "order"
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_emitted_alphabet_has_stable_identifiers_and_metadata_labels() -> None:
    """`outputs.outcome_alphabet`, and the id assignment this module decides."""
    alphabet = tuple(letter for _, letter in OUTCOME_ALPHABET)
    assignment: dict[frozenset[int], str] = {}
    for pattern in raw_alphabet(4):
        if not pattern:
            assignment[pattern] = "nc"
        elif len(pattern) == 1:
            assignment[pattern] = alphabet[next(iter(pattern)) + 1]
        else:
            assignment[pattern] = "mc"
    coarse = CoarseGraining(4, alphabet, assignment)
    assert check_coarse_graining(coarse) is None
    # THE DECISION: the stable ID is the letter's position in the DECLARED
    # order, so the IDs are a bijection onto {0, ..., |V| - 1} and no ID is
    # derived from a label.
    identifiers = [coarse.identifier(letter) for letter in alphabet]
    assert identifiers == list(range(len(alphabet)))
    assert len(set(identifiers)) == len(identifiers)
    # Re-declaring the SAME alphabet in another order gives another ID map,
    # which is exactly why the order is declared data and not derived here.
    reordered = tuple(reversed(alphabet))
    other = CoarseGraining(4, reordered, assignment)
    assert other.identifier(alphabet[0]) != coarse.identifier(alphabet[0])
    assert check_coarse_graining(other) is None


@pytest.mark.contract
@pytest.mark.oracle
def test_the_assumption_ledger_machine_keys_and_the_never_verified_set() -> None:
    """The assumption rows at registry 0.3.0, and the never-verified set.

    ``ASSUMPTION_ROWS`` -- the registry's twelve-row 0.2.0 tuple -- is marked in
    ``SUPERSEDED_BY_0_3_0`` as the enumeration the amendment widens, and
    ``ASSUMPTION_ROWS_0_3_0`` is its replacement: the same twelve plus A-EIG,
    whose Supports cell in the registry reads "RC9 (v), and the exact-window
    branch of RC8". The frozen rows mark THREE never verified; the module's
    set is read from the assumption files' ``verification`` fields.
    """
    assert is_superseded_0_3_0("ASSUMPTION_ROWS")
    assert len(ASSUMPTION_ROWS_0_3_0) == 13
    # A-ACYC, A-PROBE-DIAG
    # and A-FLOAT are not assumptions of the module -- (E2) of def:graph, def:probe
    # with req:probe-diagonal-admission, and def:evaluation-model -- so the
    # module's ledger is the frozen thirteen less those three, every other row
    # with its frozen machine key and in the frozen order. The frozen tuple is
    # not edited.
    retired = {"A-ACYC", "A-PROBE-DIAG", "A-FLOAT"}
    kept = [row for row in ASSUMPTION_ROWS_0_3_0 if row.assumption_id not in retired]
    assert len(ASSUMPTION_MACHINE_KEYS) == len(kept) == 10
    assert [str(identifier) for identifier in ASSUMPTION_MACHINE_KEYS] == [
        row.assumption_id for row in kept
    ]
    for row in kept:
        identifier = AssumptionId(row.assumption_id)
        assert ASSUMPTION_MACHINE_KEYS[identifier] == row.machine_key, row.assumption_id
    assert not {str(identifier) for identifier in AssumptionId} & retired
    # The registry-0.3.0 assumptions preamble named TWO device statements the
    # module "names and can never verify" and A THIRD that is "a statement about
    # the ARITHMETIC"; the frozen count is transcribed, never widened.
    frozen_never = {
        row.assumption_id for row in ASSUMPTION_ROWS_0_3_0 if row.never_verified
    }
    assert frozen_never == {"A-TRUST", "A-MODES", "A-EIG"}
    # The frozen three PLUS A-NOSEL and A-ROUND
    # (rem:unchecked-assumptions, req:decidable-assumptions). Both are
    # unconditional statements about the receiver and the run, of the device
    # kind; the frozen registry-0.3.0 tuples are not edited.
    # PLUS A-PASSIVE,
    # A-VAC, A-THRESH, A-PORT and A-EXACT, whose `verification` field is
    # `never`: each states a property of the physical optics, the
    # detectors or the device's parameters that validation decides only in
    # its clauses on the declared data. The frozen registry-0.3.0 tuples are not
    # edited.
    assert {str(identifier) for identifier in NEVER_VERIFIED} == frozen_never | {
        "A-NOSEL",
        "A-ROUND",
        "A-PASSIVE",
        "A-VAC",
        "A-THRESH",
        "A-PORT",
        "A-EXACT",
    }
    # And the third is of a DIFFERENT KIND and is CONDITIONAL, which the
    # registry records and which the module keeps apart from the other two.
    kinds = {row[0]: (row[1], row[2]) for row in NEVER_VERIFIED_0_3_0}
    assert kinds["A-EIG"] == ("arithmetic", True)
    assert kinds["A-TRUST"] == ("device", False)
    assert set(CONDITIONALLY_INVOKED) == {AssumptionId.A_EIG}
