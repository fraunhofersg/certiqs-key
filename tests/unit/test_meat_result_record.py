"""The result record every run writes: its refusals, and that it is data.

ONE RECORD. These tests hold
:class:`~certiqs_key.solvers.frank_wolfe.general_keyrate.GeneralKeyRateResult`,
which every declaration's run emits. Three properties carry obligations rather
than convenience:

* ``reported_tier`` is ``first-order`` exactly when a lower bound is present
  and a ``key_length`` was emitted from it, and an estimate emits no length --
  enforced by the record (the structural refusals are in
  ``tests/golden/test_fail_closed_against_registry.py``);
* ``key_length`` is ``None`` when no key-length claim may be emitted, with a
  machine-readable reason -- never a number standing in for "we could not
  tell";
* the payload is DATA: matrices, tables, scalars and status records, never a
  callable, a solver handle, or a backend-library object.
"""

from __future__ import annotations

import json
import math
from dataclasses import replace
from fractions import Fraction
from typing import Any

import pytest

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core.errors import SecurityStatementVacuousError
from certiqs_key.meat_core.finitekey.keylength import (
    key_length as key_length_of,
)
from certiqs_key.meat_core.finitekey.keylength import (
    key_length_from_bound,
)
from certiqs_key.meat_core.finitekey.result import deductions_of
from certiqs_key.meat_core.reasons import RefusalReason
from certiqs_key.solvers.frank_wolfe.general_keyrate import (
    GeneralKeyRateResult,
    key_length_from_first_order,
)

#: The two rows (there is no ``tolerance_report``), both
#: REQUIRED: ``map_validation_report`` and ``assumption_ledger``. A minimal
#: record fills both, which is what a required field is for.
EXACT_VALIDATION_REPORT = {"declaration_admitted_exactly": True}
#: The two rows are emitted with a key length only (``declaration_valid``,
#: ``purifier_dim_ok`` and ``acceptance_convex`` are no rows), and a run that
#: reports neither a bound nor a length emits none, so this is the first-order
#: record's ledger and the estimate record's is empty.
EXACT_LEDGER = ("key_register", "pa_hash_family")
#: Beside each row, the declared values it binds: one entry per row,
#: in the ledger's order.
EXACT_BINDINGS = (
    ("key_register", (("lambda_ec", 200_000), ("key_holder", "A"))),
    (
        "pa_hash_family",
        (("key_length", 799_881), ("ideal_hash", True), ("ev_hash_bits", 30)),
    ),
)

#: A certificate on a run that EARNED the rung, with the per-iterate evidence
#: its label is a statement about.
FIRST_ORDER_CERTIFICATE: dict[str, Any] = {
    "solver_status": "converged",
    "iterations": 3,
    "frank_wolfe_gap": 1e-12,
    "accumulation_rule": "maximum over the contributing iterates of Eq. eq:hlb",
    "per_iterate": [
        {
            "iteration": 3,
            "objective": 1.0,
            "linearization": 0.5,
            "oracle_optimal": True,
            "oracle_status": "optimal",
            "min_block_eigenvalue": 0.125,
            "coupling_residual": 0.0,
            "constraint_row_residual": 0.0,
            "acceptance_iterate_exact": True,
            "withdrawal": None,
        }
    ],
    "assurance_reason": "first_order_reported",
}
#: The same run reporting only the estimate: no contributing iterate.
ESTIMATE_CERTIFICATE: dict[str, Any] = {
    **FIRST_ORDER_CERTIFICATE,
    "per_iterate": [],
    "assurance_reason": "iterate_not_feasible",
}


def result(key_length: int | None, h_low: float) -> GeneralKeyRateResult:
    """Return a result record with the given key length and entropy estimate.

    A ``first-order`` record when a length is emitted, an ``estimate`` one when
    it is not: the record enforces the equivalence rather than documenting it.
    """
    return GeneralKeyRateResult(
        alpha=1.5,
        rounds=1_000_000,
        h_low=h_low,
        h_lb=None if key_length is None else 0.5,
        h_lb_dropped=None,
        dropped_set=(),
        key_length=key_length,
        # cor:composed-security (iii) at the defaults: eps_PA + eps_EV and the
        # length itself, present exactly when the length is.
        security_parameter=None if key_length is None else 2.0**-29,
        net_key_length=key_length,
        key_length_reason="reason",
        # The closed reason code, first_order_reported exactly when a length is emitted.
        key_length_reason_code=(
            "iterate_not_feasible" if key_length is None else "first_order_reported"
        ),
        reported_tier=(
            Assurance.ESTIMATE if key_length is None else Assurance.FIRST_ORDER
        ),
        first_order_clamped=False,
        optimized_q={"chat0": 1.0},
        predicted_statistics={"chat0": 1.0},
        block_contributions={"chat0": {"s0": -0.25}},
        sector_weight_report={"weights": {}, "sum": 1.0, "residue_against_one": 0.0},
        certificate=(
            ESTIMATE_CERTIFICATE if key_length is None else FIRST_ORDER_CERTIFICATE
        ),
        sector_report={"records": []},
        map_validation_report=EXACT_VALIDATION_REPORT,
        assumption_ledger=() if key_length is None else EXACT_LEDGER,
        assumption_ids=() if key_length is None else ("A-KEYREG", "A-HASH"),
        assumption_bindings=() if key_length is None else EXACT_BINDINGS,
        deductions=deductions_of(
            lambda_ec=200_000,
            eps_ev=2.0**-30,
            eps_pa=2.0**-30,
            alpha=1.5,
            ideal_hash=True,
        ),
        constraint_entries_through_a_reductions_chain=0,
        estimate_point_relaxed_member=True,
    )


@pytest.mark.contract
def test_the_tier_is_achieved_and_the_bound_absent_rather_than_null() -> None:
    """The ladder, and a record acquires the stronger label only with its bound.

    Three members, all live, weakest first (foundations/def:tiers; PRINCIPLES.md
    section 10). ``h_lb`` IS PRESENT WHEN THE
    RUN CLAIMED THE RUNG AND ABSENT OTHERWISE -- "absent, not null: a key
    present with a null value would read as 'we had a bound and lost it'".
    """
    assert [member.value for member in Assurance] == [
        "estimate", "first-order", "certified"
    ]
    assert result(1, 1.0).reported_tier is Assurance.FIRST_ORDER
    assert result(None, 1.0).reported_tier is Assurance.ESTIMATE
    assert result(None, 1.0).h_lb is None
    assert "h_lb" not in result(None, 1.0).as_payload()
    assert result(1, 1.0).h_lb == 0.5
    # The record has no default tier to fall back on: claiming the rung
    # without a bound is refused.
    with pytest.raises(ValueError, match="first-order requires a lower bound"):
        replace(result(None, 1.0), reported_tier=Assurance.FIRST_ORDER)


@pytest.mark.contract
def test_the_vacuous_security_corner_is_refused_with_its_own_reason() -> None:
    """``eps_PA + eps_EV >= 1``: the run is refused, not reported.

    THE GATE IS A DECISION AND NOT A READING. At ``eps_PA = eps_EV = 1``,
    ``lambda_EC = 0``, ``n = 1`` Eq. eq:keylength-h computes ``key_length =
    1``, and a run reporting that at ``reported_tier`` first-order would
    contradict ``cor:keylength-bound`` (b), which singles that corner out IN
    ITS OWN PROOF and disowns it: ``ell = 1`` satisfies the expression there
    "under a ``(eps_PA + eps_EV)``-security statement that is EMPTY; the corner
    carries no security claim, which is why the clause excludes it rather than
    claiming it".

    WHAT IS PINNED HERE IS THE DISPOSITION AND NOT THE ARITHMETIC. The value 1
    is the claim's, and ``eq:keylength-h`` is untouched; what this asserts is
    that no run reports it, that the refusal carries the machine-readable
    reason ``security_statement_vacuous``, and that a point JUST OUTSIDE the
    corner still computes -- so the gate is the corner and not a narrowing of
    either budget's declared domain ``(0, 1]``.

    THE PREDICATE IS THE SUM AT ``>= 1``, exactly: ``1/2 + 1/2`` is refused,
    because a security statement at exactly 1 is as empty as one above it.
    """
    corner = {"rounds": 1, "lambda_ec": 0, "eps_ev": 1.0, "eps_pa": 1.0, "alpha": 1.5}
    # THE THREE ENTRY POINTS THAT TAKE THE BUDGETS, all three refusing: the
    # core's two and the submodule's instance, which reaches the expression
    # only through the core's.
    with pytest.raises(SecurityStatementVacuousError) as refusal:
        key_length_of(h_low=0.0, **corner)
    assert refusal.value.reason == RefusalReason.SECURITY_STATEMENT_VACUOUS
    assert refusal.value.reason == "security_statement_vacuous"
    with pytest.raises(SecurityStatementVacuousError):
        key_length_from_bound(h=0.0, **corner)
    with pytest.raises(SecurityStatementVacuousError):
        key_length_from_first_order(h_lb=-1.0, **corner)

    # THE BOUNDARY IS CLOSED ON THE REFUSING SIDE.
    with pytest.raises(SecurityStatementVacuousError):
        key_length_of(
            rounds=1, h_low=0.0, lambda_ec=0, eps_ev=0.5, eps_pa=0.5, alpha=1.5
        )

    # AND THE SUM IS FORMED EXACTLY, NOT IN BINARY64. At
    # eps_PA = 1 - 2^-53 and eps_EV = 2^-54 the exact sum is 1 - 2^-54, BELOW
    # ONE -- the security statement is not empty and the run is admissible --
    # while the binary64 sum ties-to-even to exactly 1.0 and would refuse it.
    # The rule is about the sum, so it is decided on the sum and not on a
    # rounding of it, which is this module's discipline on every other
    # predicate over declared numbers.
    near = {"rounds": 10_000, "lambda_ec": 0, "eps_ev": 2.0**-54, "alpha": 1.5}
    eps_pa = 1.0 - 2.0**-53
    assert eps_pa + 2.0**-54 == 1.0
    assert Fraction(eps_pa) + Fraction(2.0**-54) == 1 - Fraction(1, 2**54)
    assert key_length_of(h_low=1.0, eps_pa=eps_pa, **near) > 0
    # The next representable budget up IS at the corner and is refused.
    with pytest.raises(SecurityStatementVacuousError):
        key_length_of(h_low=1.0, eps_pa=1.0, **near)

    # AND A POINT JUST OUTSIDE IT STILL COMPUTES. Neither budget is narrowed:
    # eps_EV = 1/2 and eps_PA = 1/4 sum to 3/4 and the length is an integer
    # again. n = 10 000 so that the length is positive and the assertion is
    # about a reported key and not about the clamp.
    outside = {
        "rounds": 10_000,
        "lambda_ec": 0,
        "eps_ev": 0.5,
        "eps_pa": 0.25,
        "alpha": 1.5,
    }
    length = key_length_of(h_low=1.0, **outside)
    assert length == 10_000 - 1 - 6 + 1
    assert key_length_from_bound(h=1.0, **outside) == (length, False)
    assert key_length_from_first_order(h_lb=1.0, **outside) == (length, False)
    # A NEGATIVE BRACKET OUTSIDE THE CORNER IS STILL CLAMPED AND FLAGGED rather
    # than refused: the corner gate is about the BUDGETS and says nothing about
    # the bound, which is clause (b) of cor:keylength-bound doing its own work.
    assert key_length_from_first_order(h_lb=-1.0, **outside) == (0, True)



@pytest.mark.contract
def test_the_corner_is_refused_before_the_solver_touches_the_oracle() -> None:
    """"Before any solve": the solver's paths refuse at parameter validation.

    THE GATE IS DECIDED ON THE DECLARED NUMBERS ALONE, so it is decided first --
    before the exact admission, before the capability probe, before the loop
    (refused "at parameter validation before any solve and before any key
    length is computed"). A run that solved and
    then discovered it had nothing to report would have spent an oracle on a
    result nobody may use.

    The stand-in oracle RAISES IF IT IS ASKED ANYTHING AT ALL, which is a
    stronger stand-in than the capability test's: there the probe is the thing
    under test, here the probe must never happen.
    """
    import sys
    from pathlib import Path

    oracle_tree = Path(__file__).resolve().parents[1] / "oracles"
    if str(oracle_tree) not in sys.path:
        sys.path.insert(0, str(oracle_tree))
    from dummy_bundles import build_bundle
    from toy_declarations import toy

    from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
    from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
    from certiqs_key.solvers.frank_wolfe.keyrate import solve, solve_declaration

    touched: list[str] = []

    class Untouchable:
        """An oracle that must never be consulted, and says so if it is."""

        def capabilities(self) -> object:
            touched.append("capabilities")
            raise AssertionError("the corner gate should have refused the run")

        def minimize(self, problem: object) -> object:
            touched.append("minimize")
            raise AssertionError("the corner gate should have refused the run")

    declaration = replace(
        declaration_from_bundle(build_bundle(toy("TOY-1"))),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=1.0, eps_ev=1.0, lambda_ec=0
        ),
    )
    for entry_point in (solve, solve_declaration):
        with pytest.raises(SecurityStatementVacuousError) as refusal:
            entry_point(declaration, Untouchable())  # type: ignore[arg-type]
        assert refusal.value.reason == "security_statement_vacuous"
    assert touched == []
    # AND THE SAME DECLARATION OUTSIDE THE CORNER REACHES THE PROBE, so what is
    # asserted above is the gate and not a fixture that could never have run.
    outside = replace(
        declaration,
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=0.25, eps_ev=0.5, lambda_ec=0
        ),
    )
    with pytest.raises(AssertionError, match="should have refused"):
        solve_declaration(outside, Untouchable())  # type: ignore[arg-type]
    assert touched == ["capabilities"]



@pytest.mark.contract
def test_the_deductions_are_reported_term_by_term() -> None:
    """spec/architecture.md 4.4 asks which budget cost what, not one number."""
    deductions = deductions_of(
        lambda_ec=200_000,
        eps_ev=2.0**-30,
        eps_pa=2.0**-30,
        alpha=1.5,
        ideal_hash=True,
    )
    assert deductions["error_correction_lambda_ec"] == 200_000.0
    assert deductions["error_verification"] == 30.0
    assert deductions["privacy_amplification"] == pytest.approx(90.0)
    assert deductions["accepted_state_flag_bonus"] == 1.0
    assert deductions["two_universal_hash_penalty"] == 0.0
    penalised = deductions_of(
        lambda_ec=0, eps_ev=1.0, eps_pa=1.0, alpha=1.5, ideal_hash=False
    )
    assert penalised["two_universal_hash_penalty"] == 1.0




@pytest.mark.contract
def test_a_refused_key_length_is_none_and_not_a_number() -> None:
    """Remark rem:hlow-range: emit no claim, not a small one."""
    refused = result(None, math.inf)
    assert refused.key_length is None
    assert refused.rate_per_round is None
    assert refused.as_payload()["h_low"] == "inf"
    assert refused.as_payload()["h_low_is_infinite"] is True

    emitted = result(799_881, 1.0)
    assert emitted.rate_per_round == pytest.approx(0.799881)
    assert emitted.as_payload()["h_low"] == 1.0


@pytest.mark.contract
def test_the_payload_is_data_only() -> None:
    """No callable, solver handle or backend object; the final iterate stays out."""
    payload = result(799_881, 1.0).as_payload()
    encoded = json.dumps(payload)
    assert "function" not in encoded
    assert payload["optimizer_certificate"]["accumulation_rule"]
    assert payload["mathematical_spec_version"] == "meat-core@1.28.0"
    assert payload["reported_tier"] == "first-order"
    assert payload["h_lb"] == 0.5
    assert payload["first_order_clamped"] is False
    # THE TWO ROWS INSTEAD OF A tolerance_report, both emitted on every run and
    # both DATA. That key must appear nowhere.
    assert "tolerance_report" not in payload
    assert payload["map_validation_report"] == dict(EXACT_VALIDATION_REPORT)
    assert list(payload["assumption_ledger"]) == list(EXACT_LEDGER)
    # The bindings reach the record through the run's route-exact assumption
    # set, never twice. The composed statement and the reason code travel here.
    assert "assumption_bindings" not in payload
    assert payload["security_parameter"] == 2.0**-29
    assert payload["net_key_length"] == 799_881
    assert payload["key_length_reason_code"] == "first_order_reported"
    assert payload["reason_text"].startswith("every hypothesis")
    estimate = result(None, 1.0).as_payload()
    assert estimate["security_parameter"] is None
    assert estimate["net_key_length"] is None
    assert estimate["key_length_reason_code"] == "iterate_not_feasible"
    # The matrices a warm start reads are never inlined.
    assert "final_iterate" not in payload
    assert "final_iterate_rows_sha256" not in payload


@pytest.mark.contract
def test_the_bindings_follow_the_ledger_row_for_row() -> None:
    """One entry per ``assumption_ledger`` row, in its order, or the record refuses."""
    record = result(799_881, 1.0)
    assert tuple(key for key, _ in record.assumption_bindings) == (
        record.assumption_ledger
    )
    with pytest.raises(ValueError, match="one entry per assumption_ledger row"):
        replace(record, assumption_bindings=tuple(reversed(EXACT_BINDINGS)))
    with pytest.raises(ValueError, match="one entry per assumption_ledger row"):
        replace(record, assumption_bindings=EXACT_BINDINGS[:1])


@pytest.mark.contract
def test_the_certificate_is_diagnostics_and_says_so() -> None:
    """spec/architecture.md 7.4: status and gap cannot promote a result.

    ``h_lb`` IS AN OUTPUT OF THE RESULT AND NOT A FIELD OF THE CERTIFICATE: the
    certificate records the per-iterate EVIDENCE, and the bound the evidence is
    for is an output row.
    """
    payload = result(None, 1.0).as_payload()["optimizer_certificate"]
    assert payload["solver_status"] == "converged"
    assert "h_lb" not in payload
    assert payload["per_iterate"] == []
    assert payload["assurance_reason"] == "iterate_not_feasible"


@pytest.mark.contract
def test_the_acceptance_geometry_narrowing_is_disclosed_where_it_refuses() -> None:
    """Where the acceptance-geometry narrowing is disclosed.

    def:admissible-acceptance-set admits ANY closed convex subset of the simplex, and a
    declaration may use the two representations the statistics taxonomy defines; every
    other tag hard-fails. The residual is stated in the refusal a
    third tag meets, which is where a caller holding such a set reads it. What
    this pins is that the disclosure is TRUE in both directions: the
    polytope is in, and the gap to def:admissible-acceptance-set is named with
    the requirement that refuses it (req:acceptance-geometries).
    """
    from certiqs_key.meat_core.acceptance.geometry import (
        AcceptanceDefect,
        acceptance_verdict,
    )
    from certiqs_key.meat_core.declaration.declaration import AcceptanceSet

    class _Declared:
        acceptance_set = AcceptanceSet(geometry="ball", frequencies=(0.5, 0.5))

    verdict = acceptance_verdict(_Declared())  # type: ignore[arg-type]
    assert verdict.defect is AcceptanceDefect.UNSUPPORTED_GEOMETRY
    assert "def:admissible-acceptance-set" in verdict.detail
    assert "closed convex" in verdict.detail
    assert "rem:acc-side" in verdict.detail
    assert "req:acceptance-geometries" in verdict.detail
    assert "refused at admission" in verdict.detail


@pytest.mark.contract
@pytest.mark.requires_qics
def test_the_frame_fields_are_absent_rather_than_null_in_untrusted_mode() -> None:
    """Both frame fields are ABSENT where there is no Choi input register.

    On a trusted-source run the frame is recorded ALWAYS, per Alice sector,
    naming the construction; in untrusted-source mode there is no Choi input
    register at all (def:untrusted-choi (a)), and a key present with a null
    value would read as "we had one and lost it".
    """
    import sys
    from pathlib import Path

    tests = Path(__file__).resolve().parents[1]
    for tree in (tests / "oracles", tests / "support"):
        if str(tree) not in sys.path:
            sys.path.insert(0, str(tree))
    from mode_bundles import build_bundle
    from toy_declarations import toy

    from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
    from certiqs_key.solvers.frank_wolfe import FrankWolfeOptions, solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    options = FrankWolfeOptions(max_iterations=2)
    untrusted = solve(
        declaration_from_bundle(build_bundle(toy("TOY-8-UN"))),
        QicsSectorChoiOracle(),
        options=options,
    )
    certificate = untrusted.as_payload()["optimizer_certificate"]
    assert "choi_input_basis" not in certificate
    assert "constraint_row_form" not in certificate

    trusted = solve(
        declaration_from_bundle(build_bundle(toy("TOY-8-T"))),
        QicsSectorChoiOracle(),
        options=options,
    )
    payload = trusted.as_payload()
    json.dumps(payload)
    (frame,) = payload["optimizer_certificate"]["choi_input_basis"].values()
    assert frame["alice_dim"] == 2
    assert frame["frame"] in {"full", "support"}
    assert {"real", "imag", "input_dim"} <= set(frame)
