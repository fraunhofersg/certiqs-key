"""The sixth residual r_6 (registry RC9), and the direction it is blind to.

Golden replay of group RP-U: ``RESIDUAL6_CASES``, ``RESIDUAL6_REQUEST_PRESENCE``,
``RESIDUAL_SCOPING_0_3_0`` and ``A_EIG_WITNESS`` (oracle entry ``O-RP-RES6``),
first frozen at registry 0.3.0 (a registry version is one of
tests/oracles/registry_receiver_povm.py, not of this module).

    r_6 = max over t and over N < n <= m*_t of
          ( beta^(t)(n) - beta-hat*^(t)(n) )_+                (Eq. eq:res6)

the window consistency defect, WHOSE EXACT VALUE IS 0 because
``beta(n) <= beta*(n)`` is Lemma ``lem:exactbasic`` (Remark ``rem:exacteig``).
It is a residual in exactly the sense of the other five: what is emitted is its
floating-point evaluation, and a value above ``eps_6`` REFUSES with the
contract-verbatim ``window_eigenvalue_consistency_residual_above_tolerance``.

IT IS REQUEST-DEPENDENT WHERE r_1 AND r_3 ARE ROUTE-DEPENDENT, and Definition
``def:residuals`` gives that its own paragraph: ``r_6`` exists on ALL THREE
ROUTES but only at the settings whose declaration carries an exact-window
depth; A DECLARATION THAT REQUESTS NO EXACT WINDOW COMPUTES NO ``beta-hat*``
AND HAS NOTHING TO COMPARE, so ``r_6`` is not defined there and its key is
ABSENT -- absent, not zero (Requirement ``req:residual-emission``). And
``eps_6`` is then not required either: ``interface.yaml``
``outputs.validation_results.r6_is_request_dependent_note``, "this is where
eps_6 differs from eps_1 and eps_3, which are declared on every route and
merely unused on one".

WHAT IT IS BLIND TO, AND WHY THAT IS THE POINT
==============================================
Remark ``rem:exacteig``: ``r_6`` does NOT verify Assumption ``ass:eig``. It
fires when ``beta-hat*`` lands too LOW, and the assumption constrains it from
landing too HIGH; NO TEST IN THE CONTRACT BOUNDS THE UNSAFE DIRECTION, and the
assumption carries it.

``A_EIG_WITNESS`` is the frozen instance of exactly that, and the registry
attaches an instruction to it: what an implementer must NOT do with the case is "assert
it as an expected emitted value. IT IS FROZEN AS THE WITNESS OF A VIOLATED
ASSUMPTION, NOT AS A VALUE THE CONTRACT LICENSES." So the test below asserts
what it demonstrates -- that an overshoot of ``249/1000`` reaches the emitted
``p_mc`` while ``r_6`` passes at ``0`` and nothing else fires -- and says so in
its own name.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from probe_presence import with_probe
from receiver_povm_support import (
    MACHINE_AGREEMENT,
    TOLERANCE,
    TOLERANCE_WITHOUT_EXACT_WINDOW,
    bb84_channel_only_request,
    bound_data_of,
    probe_receiver_request,
    tolerances_at,
)
from registry_receiver_povm import (
    A_EIG_WITNESS,
    EXACT_WINDOW_CASES,
    RESIDUAL6_CASES,
    RESIDUAL6_REQUEST_PRESENCE,
    RESIDUAL_SCOPING_0_3_0,
    rp_oracle,
)

from certiqs_key.receiver import (
    ExactWindowRecord,
    bound_function,
    check_residuals,
    construct_receiver,
    setting_bound,
    window_consistency_residual,
    window_floor,
)
from certiqs_key.receiver.errors import MalformedInputError
from certiqs_key.receiver.reasons import RefusalReason


def _rows_of(case: object) -> tuple[tuple[int, float, float, float], ...]:
    """Return one frozen r_6 case's window as the module's own record rows.

    ``(n, beta(n), beta-hat*(n), ell(n))``, with ``ell`` recomputed by
    Eq. ``eq:elldef`` at the fixture's ``eps_eig`` -- the frozen case fixes the
    first three and the fourth is this module's own evaluation of them.
    """
    eps_eig = TOLERANCE.eps_eig
    assert eps_eig is not None
    return tuple(
        (
            photons,
            float(beta),
            float(hat),
            window_floor(float(beta), float(hat), eps_eig),
        )
        for _setting, photons, beta, hat, _exact, _defect in case.entries  # type: ignore[attr-defined]
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_r6_is_the_window_consistency_defect_of_eq_res6() -> None:
    """Definition def:residuals, Eq. eq:res6, at every frozen case.

    The per-index positive parts AND their maximum, because Eq. ``eq:res6`` is a
    maximum over the WHOLE window and over EVERY setting carrying a depth: an
    implementation reading only the first index would pass
    ``R6-FAIL-AT-THE-SECOND-INDEX``, and one reading only the first setting
    would pass ``R6-FAIL-ACROSS-SETTINGS``.
    """
    assert rp_oracle("O-RP-RES6").claims == ("RC9",)
    for case in RESIDUAL6_CASES:
        rows = _rows_of(case)
        record = ExactWindowRecord(
            depth=max(n for n, *_ in rows),
            rows=rows,
            window_minimum=min(row[3] for row in rows),
            middle_minimum=None,
            middle_window_empty=False,
            remainder=1.0,
            remainder_kind="frozen",
        )
        defects = record.window_consistency_defects()
        frozen = [float(entry[5]) for entry in case.entries]
        for got, want in zip(defects, frozen, strict=True):
            assert abs(got - want) <= MACHINE_AGREEMENT, case.case_id
        residual = window_consistency_residual(defects, TOLERANCE)
        assert residual.residual_id == "r_6"
        assert abs(residual.value - float(case.r6)) <= MACHINE_AGREEMENT, case.case_id
        assert case.tolerance_key == "eps_6"
        assert residual.tolerance == TOLERANCE.residual_bound("r_6")
        assert residual.passes is case.passes, case.case_id
        # A residual above tolerance is a REFUSAL, not a warning, and the reason
        # is the contract's own.
        refusal = check_residuals([residual])
        if case.passes:
            assert refusal is None, case.case_id
            assert case.refusal_reason is None
        else:
            assert refusal is not None, case.case_id
            assert str(refusal.reason) == case.refusal_reason, case.case_id
            assert refusal.reason is (
                RefusalReason.WINDOW_EIGENVALUE_CONSISTENCY_RESIDUAL_ABOVE_TOLERANCE
            )


@pytest.mark.contract
@pytest.mark.oracle
def test_r6_does_not_see_the_direction_ass_eig_constrains() -> None:
    """Remark rem:exacteig: r_6 fires DOWNWARD, and ass:eig constrains UPWARD.

    ``R6-PASS-OVERSHOOT-BLIND`` is frozen AS A PASS, which is the finding rather
    than an oversight: the computed eigenvalue lands ABOVE the exact one, the
    defect ``(beta - beta-hat*)_+`` is ``0``, and ``r_6`` reports nothing.
    """
    overshoots = [case for case in RESIDUAL6_CASES if case.is_overshoot]
    assert len(overshoots) == 1
    case = overshoots[0]
    assert case.passes is True
    assert case.r6 == 0
    rows = _rows_of(case)
    record = ExactWindowRecord(
        depth=max(n for n, *_ in rows),
        rows=rows,
        window_minimum=min(row[3] for row in rows),
        middle_minimum=None,
        middle_window_empty=False,
        remainder=1.0,
        remainder_kind="frozen",
    )
    assert all(defect == 0.0 for defect in record.window_consistency_defects())
    assert window_consistency_residual(
        record.window_consistency_defects(), TOLERANCE
    ).passes
    # AND THE OVERSHOOT IS REAL: the frozen exact value is strictly below the
    # computed one at the overshooting index, so a test that DID bound the
    # unsafe direction would have something to fire on.
    overshoots = [
        (float(hat), float(exact))
        for _setting, _n, _beta, hat, exact, _defect in case.entries
        if hat > exact
    ]
    assert overshoots, case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_a_violated_eig_assumption_reaches_the_emitted_value_uncaught() -> None:
    """Assumption ass:eig, and the witness of what NOTHING in this module catches.

    THIS IS NOT AN ASSERTION THAT THE VALUE IS LICENSED. The registry says so of
    its own case: it "is frozen as the WITNESS OF A VIOLATED ASSUMPTION, NOT AS
    A VALUE THE CONTRACT LICENSES". What is asserted here is the CHAIN -- that
    with ``beta-hat*(2) = 3/4`` against an exact ``beta*(2) = 1/2`` and a
    declared ``eps_eig = 1/1000``, Eq. ``eq:eigassumption`` is violated, the
    emitted ``p_mc`` is ``749/1000`` against a true uniform bound of ``1/2``, the
    excess is ``249/1000`` IN THE UNSAFE DIRECTION, and ``r_6`` passes at ``0``
    while the two failure conditions Proposition ``prop:slotvalid`` names
    (spec/architecture.md section 5.4) are not triggered either, ``749/1000``
    lying inside ``[0, 1]``.

    Remark ``rem:exacteig`` states why: no range check catches it, whatever the
    size of the overshoot, because every branch of Eq. ``eq:pmcex`` is capped
    by an analytic remainder that is at most 1 and does not depend on
    ``beta-hat*^(t)`` -- "An overshoot of any size is caught by nothing." That
    is why Assumption ``ass:eig`` is stated, why it is one-sided, and why it is
    in the never-verified set.
    """
    witness = dict(A_EIG_WITNESS)
    assert "EX-BS-N1-M2-OVERSHOOT" in witness["case"]
    # The I-BS declaration the witness is built on, from its frozen bound data.
    base = next(c for c in EXACT_WINDOW_CASES if c.case_id == "EX-BS-N1-M2-EIG-1E3")
    data = bound_data_of(base)
    tolerances = tolerances_at(Fraction(1, 1000))
    record = setting_bound(
        "overshoot",
        data,
        base.photon_cutoff,
        base.predicate_x,
        tolerances,
        base.tail_window,
        base.exact_depth,
        ((2, 0.75),),  # the OVERSHOOTING computed value: 3/4 against an exact 1/2
    )
    exact_window = record.exact_window
    assert exact_window is not None
    # Eq. eq:elldef reads 749/1000 rather than the analytic floor 1/2.
    assert exact_window.rows[0][3] == pytest.approx(0.749, abs=MACHINE_AGREEMENT)
    assert exact_window.remainder == pytest.approx(0.75, abs=MACHINE_AGREEMENT)
    assert record.weight == pytest.approx(0.749, abs=MACHINE_AGREEMENT)
    # THE TRUE UNIFORM BOUND IS 1/2, so the excess is 249/1000, unsafe.
    assert record.weight - 0.5 == pytest.approx(0.249, abs=MACHINE_AGREEMENT)
    assert "249/1000" in witness["the excess"]
    # r_6 PASSES AT ZERO: the defect is (beta(2) - beta-hat*(2))_+ = 0.
    residual = window_consistency_residual(
        exact_window.window_consistency_defects(), tolerances
    )
    assert residual.value == 0.0
    assert residual.passes is True
    assert check_residuals([residual]) is None
    assert "IT PASSES" in witness["r_6"]
    # AND Prop. prop:slotvalid's two failure conditions are not triggered.
    assert 0.0 <= record.weight <= 1.0
    assert "NOT TRIGGERED" in witness["ARCHITECTURE_SPEC.md Section 7.3"]
    assert "NOTHING IN THIS MODULE" in witness["what catches it"]
    # The declared eps_eig is what the assumption is stated at, and the module
    # SUBTRACTS it rather than testing against it.
    assert bound_function(data, 2) == pytest.approx(0.5, abs=MACHINE_AGREEMENT)
    assert window_floor(0.5, 0.75, 0.001) == pytest.approx(0.749, abs=0.0)


@pytest.mark.contract
@pytest.mark.oracle
def test_r6_presence_is_request_dependent_where_r1_and_r3_are_route_dependent() -> None:
    """Def. def:residuals: absent where no depth is declared -- absent, not zero.

    Run end to end on both frozen receivers, with and without a depth, so that
    the presence rule is checked on the EMITTED ``validation_results`` and not
    on an intermediate.
    """
    presence = {
        (row[0], row[1]): (row[2], row[3]) for row in RESIDUAL6_REQUEST_PRESENCE
    }
    assert {row[0] for row in RESIDUAL6_REQUEST_PRESENCE} == {
        "no exact_window depth anywhere",
        "a depth at some setting",
    }
    for request, route, depths in (
        (bb84_channel_only_request(photon_cutoff=1), "element_graph", {}),
        (
            bb84_channel_only_request(photon_cutoff=1, exact_window={"off": 2}),
            "element_graph",
            {"off": 2},
        ),
        *with_probe(
            (probe_receiver_request(), "instrument_matrix", {}),
            (
                probe_receiver_request(exact_window={"off": 2}),
                "instrument_matrix",
                {"off": 2},
            ),
        ),
    ):
        emission = construct_receiver(request)
        assert emission.refusal is None, emission.refusal
        artifact = emission.artifact
        assert artifact is not None
        ids = [row.residual_id for row in artifact.validation_results.residuals]
        key = "a depth at some setting" if depths else "no exact_window depth anywhere"
        expected_present, expected_declared = presence[(key, route)]
        assert ("r_6" in ids) is expected_present, (route, depths)
        assert expected_present is expected_declared
        # ABSENT, NOT ZERO: no row at all, rather than a row reading 0.
        if not expected_present:
            assert not any(
                row.residual_id == "r_6"
                for row in artifact.validation_results.residuals
            )
    # AND eps_6 IS NOT DECLARED THERE EITHER, which is where it differs from
    # eps_1 and eps_3.
    scoping = {row[0]: (row[1], row[2]) for row in RESIDUAL_SCOPING_0_3_0}
    assert "r_6" in scoping
    assert TOLERANCE_WITHOUT_EXACT_WINDOW.eps_6 is None
    assert TOLERANCE_WITHOUT_EXACT_WINDOW.eps_1 is not None
    with pytest.raises(MalformedInputError, match="r_6"):
        TOLERANCE_WITHOUT_EXACT_WINDOW.residual_bound("r_6")
