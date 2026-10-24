"""End to end: an operator bundle on disk, the result record out.

ONE RECORD (one Frank-Wolfe driver): every run returns the general record, so
the certificate is a mapping and the frame fields are keyed by Alice sector.

The runtime boundary of spec/architecture.md 7.1 in one go -- write a bundle,
read it back, validate it (5.6), probe the oracle (10.3), run the Frank-Wolfe
loop (10.2), report (6.7) -- on the hand-authored dummy bundles that stand in
for ``protocol-compiler``.

The subject of this file: the solver returns the expected value on the dummy
bundle and agrees with the oracles inside recorded tolerances.
"""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

import pytest

for _tree in ("oracles", "support"):
    _path = str(Path(__file__).resolve().parents[1] / _tree)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from dummy_bundles import build_bundle  # noqa: E402
from mode_bundles import build_bundle as build_mode_bundle  # noqa: E402
from tests.support.provenance import COMPILED  # noqa: E402
from tiers import BRACKET_TIER  # noqa: E402
from toy_declarations import SOURCE_MODE_TOYS, toy  # noqa: E402

from certiqs_key.domain.bundle import read_bundle, write_bundle  # noqa: E402
from certiqs_key.foundations.assurance import Assurance  # noqa: E402
from certiqs_key.solvers.frank_wolfe import (  # noqa: E402
    ACCUMULATION_RULE,
    solve_bundle,
)
from certiqs_key.solvers.types import SearchRequest  # noqa: E402

#: Recorded in tests/golden/test_hlow_against_registry.py; the same bar applies
#: here, for the same two reasons (the step cap and the oracle tolerance).
SOLVER = 1e-8

pytestmark = pytest.mark.requires_qics


def oracle_instance():
    """Return a fresh QICS-backed linear oracle."""
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    return QicsSectorChoiOracle()


def round_trip(toy_id: str, directory: Path):
    """Write the dummy bundle of a toy to disk and read it back.

    The 0.3.0 declarations -- an absent marginal, a source-replacement licence,
    a non-default party partition, a scalar constraint bound -- are built by
    ``tests/support/mode_bundles``: the frozen builder of the frozen oracle registry
    predates the manifest fields that express them and refuses them by name.
    """
    candidate = toy(toy_id)
    builder = build_mode_bundle if candidate in SOURCE_MODE_TOYS else build_bundle
    write_bundle(directory, builder(candidate))
    assert (directory / "manifest.json").is_file()
    assert (directory / "arrays.h5").is_file()
    return read_bundle(directory)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_dummy_bundle_survives_the_disk_and_produces_a_key_length(
    tmp_path: Path,
) -> None:
    """The whole path, on the toy whose h_low is exactly one bit per round."""
    bundle = round_trip("TOY-3(m=2)", tmp_path / "bundle")
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)

    assert result.mathematical_spec_version == "meat-core@1.28.0"
    assert result.h_low == pytest.approx(1.0, abs=SOLVER)
    # The bundle declares the KL-1 parameter set: n = 1e6, lambda_EC = 200 000,
    # both budgets 2^-30, alpha = 1.5. The frozen expected value is 799 881,
    # the first-order length (its h_lb rounds to 1), recorded beside the
    # certified one.
    assert result.certified["first_order_key_length"] == 799_881
    # The KL-1
    # expression is an integer at h = 1, so the certified bound, enclosed and
    # just below 1 (h_low = 1 exactly), floors to one bit less where the ball
    # arithmetic is installed (frank-wolfe/cor:certified-keylength).
    certified = BRACKET_TIER is Assurance.CERTIFIED
    assert result.key_length == (799_880 if certified else 799_881)
    assert result.rate_per_round == pytest.approx(0.799881, abs=2e-6)
    # THE DEFAULT TIER IS `first-order` AT 1.0.0 (Section 2.4): the bracket
    # is accumulated during the same solver run, so requesting it costs a
    # run nothing it was not already doing; the certified evaluation runs by
    # default too and certifies this toy.
    assert result.assurance is BRACKET_TIER
    assert result.certificate["accumulation_rule"] == ACCUMULATION_RULE


@pytest.mark.contract
@pytest.mark.oracle
def test_a_declaration_with_no_trusted_marginal_runs_end_to_end(
    tmp_path: Path,
) -> None:
    """The visible point of contract 0.3.0: a bundle whose marginal slot is empty.

    TOY-10 is the ``d_A = 1`` EMBEDDING of Remark ``rem:source-mode`` (b) -- a
    protocol with no trusted source, declared in untrusted-source mode with both
    parties' outcome components inside ``v`` and a non-default party partition
    naming who holds which. It exercises all three new slots at once, and it
    reproduces TOY-1's value, because it is TOY-1's protocol re-declared.
    """
    bundle = round_trip("TOY-10", tmp_path / "bundle")
    declaration = bundle.manifest.payload.declaration
    assert declaration.alice_marginal is None
    assert declaration.source_replacement_license is None
    assert declaration.party_partition is not None

    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    assert result.mathematical_spec_version == "meat-core@1.28.0"
    assert result.h_low == pytest.approx(0.0, abs=SOLVER)
    assert result.key_length == 0
    # THE DEFAULT TIER IS `first-order` AT 1.0.0 (Section 2.4): the bracket
    # is accumulated during the same solver run, so requesting it costs a
    # run nothing it was not already doing; the certified evaluation runs by
    # default too and certifies this toy.
    assert result.assurance is BRACKET_TIER
    # No A-SRC attestation is demanded, because none is asserted; and no Choi
    # input register exists, so the basis field is ABSENT.
    gates = result.certificate["security_gates"]
    assert gates["source_mode"] == "untrusted"
    assert gates["source_replacement_license_required"] is False
    assert "choi_input_basis" not in result.certificate
    assert "choi_input_basis" not in result.as_payload()["optimizer_certificate"]


@pytest.mark.contract
@pytest.mark.oracle
def test_dropping_the_trusted_marginal_lowers_the_key_length(tmp_path: Path) -> None:
    """Remark ``rem:source-mode`` (a), end to end, on the TOY-8 pair.

    The same declaration data, differing only in whether the marginal slot is
    filled. The untrusted twin's feasible set is the larger, so its ``h_low``
    is the smaller and its key length shorter -- which is why dropping the
    marginal is the CONSERVATIVE direction and declaring one without the A-SRC
    attestation overstates the key.
    """
    trusted = solve_bundle(
        round_trip("TOY-8-T", tmp_path / "t"), oracle_instance(), compiled=COMPILED
    )
    untrusted = solve_bundle(
        round_trip("TOY-8-UN", tmp_path / "u"), oracle_instance(), compiled=COMPILED
    )
    assert untrusted.h_low < trusted.h_low
    assert untrusted.h_low == pytest.approx(0.0, abs=SOLVER)
    assert untrusted.key_length == 0
    assert trusted.key_length is not None and trusted.key_length > 0
    assert trusted.certificate["security_gates"]["source_replacement_license_present"]


@pytest.mark.contract
@pytest.mark.oracle
def test_a_singular_trusted_marginal_runs_and_records_its_declared_basis(
    tmp_path: Path,
) -> None:
    """TOY-9 has ``rank tau_A = 2 < 3 = d_A``.

    Section 2.5 forbids refusing it and requires the ``iota`` used to be
    recorded. Both are checked here through the serialized path, and the
    recorded record is JSON-serializable like the rest of the payload.
    """
    import json

    bundle = round_trip("TOY-9", tmp_path / "bundle")
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    assert math.isfinite(result.h_low)
    assert result.key_length is not None
    # ONE FRAME PER ALICE SECTOR, naming its construction (the support frame
    # in POVM form, lem:choi-factor): the frame is RECORDED, not canonicalized.
    (record,) = result.certificate["choi_input_basis"].values()
    assert record["alice_dim"] == 3
    assert record["input_dim"] == 2
    assert record["frame"] == "support"
    payload = result.as_payload()
    json.dumps(payload)
    (frame,) = payload["optimizer_certificate"]["choi_input_basis"].values()
    assert frame["input_dim"] == 2


@pytest.mark.contract
@pytest.mark.oracle
def test_an_untrusted_declaration_with_a_scalar_entry_blocks_the_key_length(
    tmp_path: Path,
) -> None:
    """Remark ``rem:cgate``: part (i) is vacuous here and must read as vacuous."""
    bundle = round_trip("TOY-5-UN", tmp_path / "bundle")
    entry = bundle.manifest.payload.declaration.constraint_list[0]
    assert entry.bound == 0.5  # a real scalar, not a 1 x 1 array
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    assert result.key_length is None
    assert "attack_set_license" in result.key_length_reason
    assert math.isfinite(result.h_low) and result.h_low > 0.0
    gates = result.certificate["security_gates"]
    assert gates["licensed_class_passed"] is True
    assert gates["licensed_class_vacuous"] is True


@pytest.mark.contract
@pytest.mark.oracle
def test_the_result_payload_is_serializable_and_carries_the_backend_identity(
    tmp_path: Path,
) -> None:
    """spec/architecture.md 7.3: full backend capability identity, as data."""
    import json

    bundle = round_trip("TOY-5", tmp_path / "bundle")
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    payload = result.as_payload()
    json.dumps(payload)

    backend = payload["optimizer_certificate"]["backend"]
    assert backend["oracle"]["name"] == "qics-sector-choi"
    assert backend["qics"] is not None
    assert backend["python"] and backend["numpy"]
    diagnostics = payload["optimizer_certificate"]["oracle_diagnostics"]
    assert diagnostics
    for entry in diagnostics:
        assert entry["backend"] == "qics"
        assert entry["sol_status"] in {"optimal", "near_optimal"}
        assert "opt_gap" in entry and "primal_feasibility" in entry
    # THE TWO FIELDS ARE DIFFERENT QUESTIONS AND TOY-5 SEPARATES THEM, which
    # is why they are asserted together here. The result's `assurance` is the
    # ACHIEVED assurance (a reading of the bound's presence, not a
    # certificate field): the bracket was earned, every hypothesis held.
    # `reported_tier` NAMES WHICH NUMBER CARRIES THE RUN'S CLAIM and is
    # `first-order` "EXACTLY WHEN h_lb is present AND a key_length is emitted
    # from it" (Section 2.2) -- TOY-5's constraint gate is closed for want of
    # an attack_set_license, so no length is emitted and the run claims the
    # estimate. A withheld length is no claim. The achieved tier is
    # `first-order` even where the certified evaluation certified a point: the
    # frank-wolfe interface's `optimizer_certificate` row gives the certified
    # tier only "where the certified evaluation certified a point and the run
    # is reported at it".
    assert result.assurance is Assurance.FIRST_ORDER
    if BRACKET_TIER is Assurance.CERTIFIED:
        assert result.certified is not None
        assert result.certified["status"] == "certified"
    assert payload["optimizer_certificate"]["assurance_reason"] == (
        "first_order_reported"
    )
    assert payload["h_lb"] is not None
    assert payload["key_length"] is None
    assert payload["reported_tier"] == "estimate"
    assert "sector_weight_report" in payload


@pytest.mark.contract
@pytest.mark.oracle
def test_the_sector_report_and_block_contributions_reach_the_result(
    tmp_path: Path,
) -> None:
    """The ``sector_report`` output of Section 2.2, end to end.

    The general report (one record): one record per measured
    sector with its predicates, and the key-active joint pairs. The block
    contributions list the key-ACTIVE pairs; a key-inert pair's deficit is
    identically zero (Proposition prop:exact-cancellation; lem:joint-sectors (iii))
    and is
    skipped, not formed.
    """
    bundle = round_trip("TOY-6", tmp_path / "bundle")
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    report = {row["sector"]: row for row in result.sector_report["records"]}
    assert set(report) == {"s0", "s1", "s2"}
    assert report["s0"]["key_active"] is True
    assert report["s1"]["key_active"] is False
    assert report["s1"]["constraint_active"] is True
    assert report["s2"]["key_active"] is False
    assert report["s2"]["constraint_active"] is True
    # THE GENERAL REPORT SEARCHES FOR NO REMOVAL WITNESS, and an absent witness
    # retains the sector -- the direction def:classes fixes. The one-factor
    # report found s2 removable toward s1 (thm:removal); that search lives on
    # in meat_core.declaration.sectors and its own tests, and the solver keeps
    # every declared sector either way, so no number depends on it.
    assert report["s2"]["removable"] is False
    assert report["s2"]["removable_refused_because"] is None
    contributions = result.block_contributions["chat0"]
    assert set(contributions) == {str(("t0", "s0"))}
    assert contributions[str(("t0", "s0"))] < 0.0


@pytest.mark.contract
@pytest.mark.oracle
def test_an_unlicensed_constraint_list_blocks_the_key_length_not_the_value(
    tmp_path: Path,
) -> None:
    """Section 4.19: hard-fail the key length, keep the numerical output."""
    bundle = round_trip("TOY-5", tmp_path / "bundle")
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    assert result.key_length is None
    assert "attack_set_license" in result.key_length_reason
    assert math.isfinite(result.h_low)
    assert result.h_low > 0.0


@pytest.mark.contract
@pytest.mark.oracle
def test_an_unreachable_acceptance_set_emits_no_key_length(tmp_path: Path) -> None:
    """Remark rem:hlow-range: +inf is propagated and stops the key length."""
    bundle = round_trip("TOY-4c", tmp_path / "bundle")
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    assert math.isinf(result.h_low)
    assert result.key_length is None
    assert "rem:hlow-range" in result.key_length_reason
    assert result.certificate["solver_status"] == "objective-infinite-at-start"


@pytest.mark.contract
@pytest.mark.oracle
def test_a_structural_alpha_computes_h_low_and_refuses_the_key_length(
    tmp_path: Path,
) -> None:
    """req:objective-alpha-domain and req:key-length-alpha-domain.

    ``(1, inf)`` for the objective, ``(1, 2)`` for a key length.
    """
    bundle = round_trip("TOY-3(m=2)", tmp_path / "bundle")
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED, alpha=3.5)
    assert result.alpha == 3.5
    assert result.h_low == pytest.approx(1.0, abs=SOLVER)
    assert result.key_length is None
    assert "req:key-length-alpha-domain" in result.key_length_reason


@pytest.mark.contract
@pytest.mark.oracle
def test_the_first_order_bracket_is_a_bound_and_carries_its_rule(
    tmp_path: Path,
) -> None:
    """Theorem ``thm:firstorder``: the accumulated number IS the claim.

    The gate is what makes it a claim: under (H-POS), (H-SUPP), (H-NOPERT) and the
    membership it lower-bounds ``h_low`` IN EXACT REAL ARITHMETIC, and the tier moves to
    ``first-order`` exactly then. Its feasible side is the bound verified from the
    oracle's dual (``req:verified-feasible-side``), not the pairing under ``ass:lmo``,
    and the rule says so.

    It sits below the attained value on a converged
    run, and it is not a certificate. The accumulation rule is written down
    beside it, because spec/architecture.md 7.2 asks the driver to document
    which rule it uses -- "a bound obtained by copying whichever expression
    happened to be in scope elsewhere is not a bound this platform can label".
    """
    bundle = round_trip("TOY-5", tmp_path / "bundle")
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    certificate = result.certificate
    assert result.h_lb is not None
    assert result.h_lb > -math.inf
    assert result.h_lb <= result.h_low + 1e-6
    assert "Eq. eq:hlb" in certificate["accumulation_rule"]
    assert "ass:lmo" not in certificate["accumulation_rule"]
    assert "req:verified-feasible-side" in certificate["accumulation_rule"]
    assert "CONTRIBUTING" in certificate["accumulation_rule"]
    # TOY-5's gate is closed, so no tier above the estimate is reported and the
    # achieved tier is first-order.
    assert result.assurance is Assurance.FIRST_ORDER
    assert certificate["frank_wolfe_gap"] <= 1e-6


# ---------------------------------------------------------------------------
#  The 1.0.0 FIRST-ORDER rung, end to end: the label, and the ways to lose it.
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.requires_qics
def test_a_first_order_run_reports_h_lb_and_a_length_computed_from_it(
    tmp_path: Path,
) -> None:
    """Theorem ``thm:firstorder`` and Corollary ``cor:fo-keylength``, end to end.

    BOTH LIVE TIERS ON EVERY RUN, AND NEITHER IS REQUESTED (``meat-core``, the
    interface's ``retired_parameter_rows``: "there is no
    ``requested_assurance``"), because the bracket is accumulated during the
    same solver run and suppressing it would report less about the same
    numbers. spec/architecture.md 2.8: "Every run reports both numbers and a
    ``reported_tier`` field saying which is the claim."

    So the comparison is: the estimate and the bracket come off ONE solve,
    the bracket carries the per-iterate evidence its label is a statement
    about, and the key length is computed from ``max{0, h_lb}``.
    """
    bundle = round_trip("TOY-3(m=2)", tmp_path)
    # THE FIRST-ORDER RUNG IS THE SUBJECT, so the certified evaluation is off;
    # the certified tier has its own tests
    # (tests/integration/test_certified_evaluation.py).
    result = solve_bundle(
        bundle,
        oracle_instance(),
        compiled=COMPILED,
        request=replace(SearchRequest.from_options(None), certified_evaluation="off"),
    )

    # THE ESTIMATE IS REPORTED ON EVERY RUN.
    assert math.isfinite(result.h_low)

    # SO IS THE BRACKET, with the evidence.
    assert result.h_lb is not None
    assert result.reported_tier is Assurance.FIRST_ORDER
    assert result.assurance is Assurance.FIRST_ORDER
    assert result.certificate["per_iterate"]
    for record in result.certificate["per_iterate"]:
        assert record["withdrawal"] is None
        # THE TWO FACTS THE LABEL IS A STATEMENT ABOUT, per iterate.
        # `thm:firstorder` holds under an OPTIMAL oracle
        # status and an EXACT acceptance iterate; a run where either is false
        # withdraws the rung, so asserting the rung without asserting them
        # asserts the conclusion and not the hypothesis.
        assert record["oracle_optimal"] is True
        assert record["acceptance_iterate_exact"] is True

    # AND THE LENGTH IS COMPUTED FROM max{0, h_lb}, WHICH THE REASON SAYS.
    # `is not None` alone would pass on a zero-length clamp and on a length
    # computed by any other route; the corollary's name in the reason is what
    # makes it this one.
    assert result.key_length is not None and result.key_length > 0
    assert "cor:fo-keylength" in result.key_length_reason

    # THE DIFFERENCE IS THE DIFFERENCE, and the 0.5.0 refusal that read one
    # MUST NOT BE RE-CREATED: the record carries `h_lb - h_low` WITH ITS SIGN
    # as a DIAGNOSTIC and refuses nothing on it (frank-wolfe/rem:fo-arithmetic
    # (b)), so a positive value is reported rather than treated as a defect.
    payload = result.as_payload()
    assert payload["first_order_minus_estimate"] == pytest.approx(
        result.h_lb - result.h_low, abs=1e-12
    )
    # And each Group B row with the worst quantity it met, where and when.
    worst = payload["optimizer_certificate"]["group_b_worst"]
    assert worst["optimizer_gap"]["worst"] == payload["optimizer_certificate"][
        "frank_wolfe_gap"
    ]
    assert worst["iterate_positivity"]["worst"] >= 0.0
    assert worst["iterate_positivity"]["iteration"] >= 1
    for entry in payload["optimizer_certificate"]["oracle_diagnostics"]:
        assert entry["iteration"] >= 1


@pytest.mark.contract
def test_the_certified_rung_is_reached_and_never_requested() -> None:
    """The ``certified`` tier is the third rung, achieved and never requested.

    The ``certified`` tier is an a-posteriori verification of the first-order
    bound, reached by the solver's certified evaluation
    (frank-wolfe/req:certified-evaluation). The member exists, above
    ``first-order``, and no request names a tier:
    the run option ``certified_evaluation`` says whether the evaluation runs,
    never which tier to report.
    """
    assert [str(tier) for tier in Assurance] == ["estimate", "first-order", "certified"]
    assert not hasattr(SearchRequest(), "requested_assurance")


@pytest.mark.contract
@pytest.mark.requires_qics
def test_the_infinite_branch_emits_no_length_on_either_tier(
    tmp_path: Path,
) -> None:
    """Remark ``rem:hlow-range``: ``+inf`` is propagated and no length claimed.

    One of the THREE INDEPENDENT GROUNDS on which ``key_length`` is ABSENT --
    not zero, not clamped. No tier is requested, and the ground binds the one
    run either way.
    """
    bundle = round_trip("TOY-4c", tmp_path)
    result = solve_bundle(bundle, oracle_instance(), compiled=COMPILED)
    assert math.isinf(result.h_low)
    assert result.key_length is None
    assert result.reported_tier is Assurance.ESTIMATE
    assert "rem:hlow-range" in result.key_length_reason


# ---------------------------------------------------------------------------
#  The certified evaluation at the solver: withheld, and off
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.requires_qics
def test_a_withheld_certification_keeps_the_first_order_number(
    tmp_path: Path,
) -> None:
    """``frank-wolfe/req:certified-evaluation`` (vii) at the solver.

    Where an upstream reason withholds the tier, "the run's number, key length
    and tier are those it has without this requirement";
    ``general_keyrate.py`` decides it on ``certification.reported``. On
    TOY-3(m=2) under KL-1 the two lengths differ by one bit (799,881
    first-order, 799,880 certified), so the tier and the length both show it.
    A test must pass ``certification_withheld`` to a solve, or forming the
    length from ``certified_bound`` whenever one exists would pass. The run
    tier's half of (vii) is
    ``tests/unit/test_item_vii_withholds_at_the_run_tier.py``.
    """
    pytest.importorskip("flint")
    bundle = round_trip("TOY-3(m=2)", tmp_path)
    result = solve_bundle(
        bundle,
        oracle_instance(),
        compiled=COMPILED,
        certification_withheld=("receiver_weight_floating_point",),
    )
    certified = result.certified
    assert certified is not None
    assert certified["status"] == "withheld"
    assert certified["reasons"] == ["receiver_weight_floating_point"]
    assert certified["certified_bound"] is not None
    assert result.reported_tier is Assurance.FIRST_ORDER
    assert result.assurance is Assurance.FIRST_ORDER
    assert result.key_length_reason_code == "first_order_reported"
    assert result.key_length == certified["first_order_key_length"] == 799_881


@pytest.mark.contract
@pytest.mark.requires_qics
def test_strict_refuses_where_the_run_is_not_reported_certified(
    tmp_path: Path,
) -> None:
    """``frank-wolfe/req:certified-evaluation`` (viii) in the default tier.

    ``strict``: "as ``on``, but a run not reported at the certified tier
    refuses with the core's ``certification_refused`` and reports no key
    length". TOY-3(m=2) certifies, so ``strict`` reports it at the certified
    tier; with the tier withheld upstream (item (vii)) the same run is not
    reported at it, and ``strict`` refuses, naming the reason. The default
    tier pins the refusal, so a strict run that did not refuse fails here.
    """
    pytest.importorskip("flint")
    from certiqs_key.meat_core.errors import CertificationRefusedError

    bundle = round_trip("TOY-3(m=2)", tmp_path)
    strict = replace(SearchRequest.from_options(None), certified_evaluation="strict")
    reported = solve_bundle(
        bundle, oracle_instance(), compiled=COMPILED, request=strict
    )
    assert reported.reported_tier is Assurance.CERTIFIED
    with pytest.raises(CertificationRefusedError) as refused:
        solve_bundle(
            bundle,
            oracle_instance(),
            compiled=COMPILED,
            request=strict,
            certification_withheld=("receiver_weight_floating_point",),
        )
    assert refused.value.reason == "certification_refused"
    assert "receiver_weight_floating_point" in str(refused.value)


@pytest.mark.requires_qics
def test_a_run_with_the_evaluation_off_never_imports_the_certifier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``certified_evaluation: off`` loads neither the evaluation nor its library.

    The frank-wolfe interface's option row: "``off``: the evaluation does not
    run, and the record says so". With python-flint unimportable, and the
    evaluation and the ball arithmetic unloaded, an ``off`` run reports its
    first-order number with the record of ``off`` and leaves both unloaded.
    No run with a bound imports the evaluation, and through it the library,
    first.
    """
    import certiqs_key.foundations as foundations_package
    import certiqs_key.solvers.frank_wolfe as frank_wolfe_package

    unloaded = (
        "certiqs_key.solvers.frank_wolfe.certified",
        "certiqs_key.foundations.balls",
    )
    monkeypatch.setitem(sys.modules, "flint", None)  # import flint raises
    for name in unloaded:
        monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.delattr(frank_wolfe_package, "certified", raising=False)
    monkeypatch.delattr(foundations_package, "balls", raising=False)

    bundle = round_trip("TOY-3(m=2)", tmp_path)
    result = solve_bundle(
        bundle,
        oracle_instance(),
        compiled=COMPILED,
        request=replace(SearchRequest.from_options(None), certified_evaluation="off"),
    )
    assert result.reported_tier is Assurance.FIRST_ORDER
    assert result.certified is not None
    assert result.certified["status"] == "off"
    assert result.certified["reasons"] == ["certified_evaluation_off"]
    assert [name for name in unloaded if name in sys.modules] == []
