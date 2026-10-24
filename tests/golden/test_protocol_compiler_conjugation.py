"""The ``conjugation_basis`` discriminator -- the only line of defence there is.

Remark ``rem:bb84checks`` withdraws a claim the contract's first draft made,
and the withdrawal is why this file exists as its own test rather than as one
more assertion among the BB84 ones:

    "ALL FOUR BB84 SIGNAL STATES HAVE REAL COEFFICIENTS in the declared
    computational basis, so ``conj(a^b) = a^b`` and THE CONJUGATION IS THE
    IDENTITY ON THIS SIGNAL SET: emitting ``M = p^A_b |a^b><a^b|`` in place of
    ``p^A_b |conj(a^b)><conj(a^b)|`` CHANGES ``P_D[omega]`` AT NO STATE, IN NO
    BASIS. A reversed convention is exactly as silent here as anywhere else,
    and A REGRESSION TEST BUILT ON THIS INSTANCE TO CATCH IT CANNOT FAIL."

So every BB84 assertion in this suite would pass unchanged if the bar were
dropped from the compilation map. THE TESTS BELOW ARE THE ONLY ONES THAT WOULD
NOT. They are written in the mutation style the situation demands: the
conforming branch is asserted to reproduce its frozen values, AND the mutated
branch is asserted to be OBSERVABLY WRONG at the same frozen numbers -- because
a test that only pinned the right answer would be satisfied by an
implementation that computed it by accident.

THE THREE OBSERVABLE DIFFERENCES, all frozen and all exact, and each at a
different point of the pipeline:

    1. THE EMITTED ELEMENT      ``[[1/4, i/4], [-i/4, 1/4]]`` against
                                ``[[1/4, -i/4], [i/4, 1/4]]`` -- the same
                                matrix with the off-diagonal imaginary sign
                                reversed.
    2. THE (SR2) VERDICT        holds in one branch, FAILS in the other, so
                                gate (G2) refuses the second at ``d_A >= 2``.
    3. THE MATCHED-BASIS TABLE  diagonal ``[[1/8, 0], [0, 1/8]]`` against
                                ANTI-diagonal ``[[0, 1/8], [1/8, 0]]`` -- "a
                                noiseless channel reported at ERROR RATE ONE in
                                that basis".

All three are asserted, because "an implementation could get the first right
and the third wrong by re-deriving the statistics from the specification
instead of from the emitted declaration".
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from instances.bb84.specification import (
    P_Y0,
    P_Y1,
    ConjugationConvention,
    conjugate_projector,
    conjugation_example_specification,
)
from registry_instances_bb84 import BB84_CASES, CONJUGATION_BRANCHES

from certiqs_key.foundations.exact import Cx, Matrix, equal, matrix
from certiqs_key.protocol_compiler import (
    compile_specification,
    joint_distribution,
    resolve_povm,
)

pytestmark = [pytest.mark.contract, pytest.mark.oracle]

PHI_PLUS = matrix(
    (
        (F(1, 2), 0, 0, F(1, 2)),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (F(1, 2), 0, 0, F(1, 2)),
    )
)
CONTRACT_BRANCH, OMITTED_BRANCH = CONJUGATION_BRANCHES


def reg(frozen: object) -> Matrix:
    """Return a frozen registry matrix in the implementation's substrate."""
    assert isinstance(frozen, tuple)
    return tuple(
        tuple(Cx(entry[0], entry[1]) for entry in row)  # type: ignore[index]
        for row in frozen
    )


def test_conjugation_swaps_the_two_y_labels() -> None:
    """Eq. ``eq:ystates``: the defect is a LABEL PERMUTATION, not a phase."""
    assert equal(conjugate_projector(P_Y0), P_Y1)
    assert equal(conjugate_projector(P_Y1), P_Y0)
    # Conjugating twice returns the original, which is what makes the emitted
    # element and the (SR2) value inverse operations of one another.
    assert equal(conjugate_projector(conjugate_projector(P_Y0)), P_Y0)


def test_the_bb84_signal_set_cannot_discriminate_and_says_so() -> None:
    """Remark rem:bb84checks, as a statement about DATA."""
    for case in BB84_CASES:
        for element in case.alice_povm:
            emitted = reg(element)
            assert equal(emitted, conjugate_projector(emitted))
    # So on the BB84 set the two conventions emit the SAME matrices, and no
    # assertion built on them can distinguish the two.
    from instances.bb84.specification import P_X0, P_X1, P_Z0, P_Z1

    for projector in (P_Z0, P_Z1, P_X0, P_X1):
        assert equal(conjugate_projector(projector), projector)


# ---------------------------------------------------------------------------
#  Difference 1: the emitted element
# ---------------------------------------------------------------------------


def test_difference_one_the_emitted_element_differs_in_the_off_diagonal_sign() -> None:
    contract = (
        resolve_povm(
            conjugation_example_specification(
                ConjugationConvention.CONTRACT
            ).source.alice_povm
        )
        .require()
        .elements["(Y,0)"]
    )
    omitted = (
        resolve_povm(
            conjugation_example_specification(
                ConjugationConvention.OMITTED
            ).source.alice_povm
        )
        .require()
        .elements["(Y,0)"]
    )

    assert equal(contract, reg(CONTRACT_BRANCH.emitted_element))
    assert equal(omitted, reg(OMITTED_BRANCH.emitted_element))
    # THE MUTATION IS OBSERVABLE: same diagonal, reversed off-diagonal sign.
    assert not equal(contract, omitted)
    assert contract[0][0] == omitted[0][0]
    assert contract[1][1] == omitted[1][1]
    assert contract[0][1] == Cx(F(0), F(1, 4))
    assert omitted[0][1] == Cx(F(0), F(-1, 4))
    assert contract[0][1] == Cx(F(0), -omitted[0][1].im)


# ---------------------------------------------------------------------------
#  Difference 2: the (SR2) verdict, and the refusal it earns
# ---------------------------------------------------------------------------


def test_difference_two_the_sr2_verdict_flips_and_the_gate_refuses() -> None:
    contract = compile_specification(
        conjugation_example_specification(ConjugationConvention.CONTRACT)
    )
    omitted = compile_specification(
        conjugation_example_specification(ConjugationConvention.OMITTED)
    )

    assert contract.certificate is not None
    assert omitted.certificate is not None
    assert contract.certificate.sr2_holds is CONTRACT_BRANCH.sr2_holds is True
    assert omitted.certificate.sr2_holds is OMITTED_BRANCH.sr2_holds is False
    # (SR1) is untouched by the mutation: it involves only |Psi> and tau_A.
    assert contract.certificate.sr1_holds is True
    assert omitted.certificate.sr1_holds is True

    assert equal(
        contract.certificate.sr2_computed["(Y,0)"],
        reg(CONTRACT_BRANCH.sr2_computed),
    )
    assert equal(
        omitted.certificate.sr2_computed["(Y,0)"], reg(OMITTED_BRANCH.sr2_computed)
    )
    # Both branches expect the SAME value: the specification's source is the
    # same, and only the emitted measurement moved.
    assert equal(reg(CONTRACT_BRANCH.sr2_expected), reg(OMITTED_BRANCH.sr2_expected))

    # THE OUTCOMES DIFFER, and the mutated one never reaches a declaration.
    assert contract.refuses is False
    assert omitted.refuses is True
    assert omitted.declaration is None
    assert omitted.refusal is not None
    # The frozen registry spells this refusal
    # `certificate_condition_sr2_failed`, a spelling invented under the rule
    # "<family>_<identifier>_failed".
    # The five certificate conditions are the TRANSMITTER's
    # and its interface spells them; the compiler's gate (G2)
    # RE-DECIDES the same five on the same data and REUSES those five
    # strings rather than spelling a second set (the compiler
    # interface's `fixed_by_this_file`: "a second vocabulary would be
    # two names for one refusal"). The CONDITION named is
    # (SR2), the signal identity -- and no registry value is edited: the
    # frozen enumeration fixes the naming obligation and the identity of
    # the named condition, never a spelling.
    assert str(omitted.refusal.reason) == "certificate_signal_identity_fails"
    assert omitted.gates is not None
    assert str(omitted.gates.case) == "G-T-D2-CERTFAIL"


# ---------------------------------------------------------------------------
#  Difference 3: the matched-basis statistics
# ---------------------------------------------------------------------------


def test_difference_three_the_matched_basis_table_flips_diagonal() -> None:
    """The defect is visible in the STATISTICS and not only in the certificate."""
    contract = compile_specification(
        conjugation_example_specification(ConjugationConvention.CONTRACT)
    )
    assert contract.declaration is not None
    joint = joint_distribution(contract.declaration, PHI_PLUS)
    for a, row in enumerate(CONTRACT_BRANCH.matched_basis_joint):
        for y, expected in enumerate(row):
            assert joint[(f"(Y,{a})", f"(Y,{y})")] == expected
    # DIAGONAL: Alice and Bob agree with certainty on matched-basis Y rounds.
    assert joint[("(Y,0)", "(Y,0)")] == F(1, 8)
    assert joint[("(Y,0)", "(Y,1)")] == F(0)

    # The mutated branch is refused, so its table has to be computed from the
    # family it WOULD have emitted -- which is what makes the third difference
    # assertable at all, and it is anti-diagonal.
    omitted_specification = conjugation_example_specification(
        ConjugationConvention.OMITTED
    )
    omitted_family = resolve_povm(omitted_specification.source.alice_povm).require()
    mutated = _mutated_joint(contract, omitted_family.elements)
    for a, row in enumerate(OMITTED_BRANCH.matched_basis_joint):
        for y, expected in enumerate(row):
            assert mutated[(f"(Y,{a})", f"(Y,{y})")] == expected
    assert mutated[("(Y,0)", "(Y,0)")] == F(0)
    assert mutated[("(Y,0)", "(Y,1)")] == F(1, 8)

    # THE TWO TABLES DIFFER EVERYWHERE ON THE MATCHED-BASIS BLOCK: a noiseless
    # channel reported at error rate ONE instead of zero.
    for a in (0, 1):
        for y in (0, 1):
            pair = (f"(Y,{a})", f"(Y,{y})")
            assert joint[pair] != mutated[pair]


def _mutated_joint(
    contract_result: object, mutated_alice: object
) -> dict[tuple[str, str], F]:
    """Return ``P_D`` with Alice's family replaced by the mutated one."""
    from certiqs_key.protocol_compiler import CandidateDeclaration

    assert isinstance(contract_result.declaration, CandidateDeclaration)  # type: ignore[attr-defined]
    declaration = contract_result.declaration  # type: ignore[attr-defined]
    mutated = CandidateDeclaration(
        **{**declaration.__dict__, "alice_povm": dict(mutated_alice)}  # type: ignore[arg-type]
    )
    return joint_distribution(mutated, PHI_PLUS)


# ---------------------------------------------------------------------------
#  The pair is the point
# ---------------------------------------------------------------------------


def test_the_branch_pair_disagrees_at_all_three_points_of_the_pipeline() -> None:
    """A single branch is not evidence; the DIFFERENCE is."""
    assert not equal(
        reg(CONTRACT_BRANCH.emitted_element), reg(OMITTED_BRANCH.emitted_element)
    )
    assert CONTRACT_BRANCH.sr2_holds is not OMITTED_BRANCH.sr2_holds
    assert CONTRACT_BRANCH.matched_basis_joint != OMITTED_BRANCH.matched_basis_joint
