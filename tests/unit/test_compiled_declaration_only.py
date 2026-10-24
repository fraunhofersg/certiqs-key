"""The provenance gate: a key length only on a declaration the compiler emitted.

WHY THIS EXISTS. ``meat-core/req:compiled-declaration-only``: "The engine reports a key
length ... only on a declaration that the protocol compiler emitted; on any other
declaration it reports none." The engine knows it by an in-memory token the run tier
passes (:class:`~certiqs_key.meat_core.provenance.CompilerEmission`); the bundle and the
wire carry nothing of it. Without the token the length is WITHHELD: not a refusal, every
other number reported, and ``key_length_reason`` opening with
``declaration_not_compiled``.

What is held here: the token and its mint; the gate on the declaration-level
entry points; and, on one solve, that the token decides whether the length is
reported and nothing else -- the bound, the estimate and the length's value
are the same with it and without it. The run tier's passing of the token is
held end to end by the integration tests that read a key length off
``run_slice`` (tests/integration/test_bb84_slice.py and its siblings).
"""

from __future__ import annotations

from fractions import Fraction as F
from typing import Any

import pytest
from dummy_bundles import build_bundle
from tests.support.provenance import COMPILED
from tests.support.tiers import BRACKET_TIER
from toy_declarations import toy

from certiqs_key.domain.claim_closure import ESTIMATE_ROOT, FIRST_ORDER_ROOT
from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.docking import compiler_emission
from certiqs_key.meat_core.errors import SecurityGateError
from certiqs_key.meat_core.finitekey.keylength import (
    check_declaration_compiled,
    declaration_provenance_failure,
    key_length,
    key_length_for_declaration,
    key_length_from_bound,
    key_length_from_bound_for_declaration,
)
from certiqs_key.meat_core.provenance import CompilerEmission
from certiqs_key.meat_core.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    DECLARATION_NOT_COMPILED,
    KEY_LENGTH_ROWS,
)

pytestmark = pytest.mark.contract


def test_the_code_is_the_one_the_reason_opens_with() -> None:
    assert DECLARATION_NOT_COMPILED == "declaration_not_compiled"
    reason = declaration_provenance_failure(None)
    assert reason is not None
    assert reason.startswith("declaration_not_compiled (req:compiled-declaration-only)")
    assert declaration_provenance_failure(COMPILED) is None


def test_the_token_names_what_vouches_and_nothing_else_passes() -> None:
    with pytest.raises(ValueError, match="emitted_by"):
        CompilerEmission(emitted_by="  ")
    with pytest.raises(TypeError, match="CompilerEmission"):
        declaration_provenance_failure(True)  # type: ignore[arg-type]


def test_the_mint_reads_the_compiler_s_declaration() -> None:
    """The run tier's token is minted from the compiler's emitted declaration."""
    from instances.bb84.specification import bb84_specification

    from certiqs_key.protocol_compiler import (
        MATHEMATICAL_SPEC_VERSION,
        compile_specification,
    )

    half = F(1, 2)
    result = compile_specification(bb84_specification(half, half, half, half))
    assert result.declaration is not None
    token = compiler_emission(result.declaration)
    assert token == CompilerEmission(emitted_by=MATHEMATICAL_SPEC_VERSION)
    assert token.emitted_by.startswith("protocol-compiler@")
    with pytest.raises(TypeError, match="CandidateDeclaration"):
        compiler_emission(declaration_from_bundle(build_bundle(toy("TOY-1"))))  # type: ignore[arg-type]


def test_the_declaration_level_entry_points_withhold_without_the_token() -> None:
    """The two declaration-level doors raise the gate's reason, as on any gate."""
    declaration = declaration_from_bundle(build_bundle(toy("TOY-1")))
    with pytest.raises(SecurityGateError, match=r"^declaration_not_compiled"):
        check_declaration_compiled(None)
    with pytest.raises(SecurityGateError, match=r"^declaration_not_compiled"):
        key_length_from_bound_for_declaration(declaration, 0.5, alpha=1.5)
    # With the token the door computes the corollary's own value.
    parameters = declaration.parameters
    expected = key_length_from_bound(
        rounds=declaration.rounds,
        h=0.5,
        lambda_ec=parameters.lambda_ec,
        eps_ev=parameters.eps_ev,
        eps_pa=parameters.eps_pa,
        alpha=1.5,
    )
    assert (
        key_length_from_bound_for_declaration(
            declaration, 0.5, compiled=COMPILED, alpha=1.5
        )
        == expected
    )
    expected = key_length(
        rounds=declaration.rounds,
        h_low=0.5,
        lambda_ec=parameters.lambda_ec,
        eps_ev=parameters.eps_ev,
        eps_pa=parameters.eps_pa,
        alpha=1.5,
    )
    assert (
        key_length_for_declaration(declaration, 0.5, compiled=COMPILED, alpha=1.5)
        == expected
    )
    with pytest.raises(SecurityGateError, match=r"^declaration_not_compiled"):
        key_length_for_declaration(declaration, 0.5, alpha=1.5)


@pytest.mark.parametrize(
    "door", [key_length_for_declaration, key_length_from_bound_for_declaration]
)
def test_the_declaration_level_doors_decide_provenance_last(door) -> None:  # noqa: ANN001
    """Another closed gate keeps its own reason.

    At ``alpha = 2.5`` the key-length confinement to ``(1, 2)``
    (``req:key-length-alpha-domain``) refuses the length with or without the
    token, and without the token it is still that gate's reason that is
    raised, not the provenance gate's.
    """
    declaration = declaration_from_bundle(build_bundle(toy("TOY-1")))
    for compiled in (None, COMPILED):
        with pytest.raises(SecurityGateError) as raised:
            door(declaration, 0.5, compiled=compiled, alpha=2.5)
        assert "req:key-length-alpha-domain" in str(raised.value)
        assert DECLARATION_NOT_COMPILED not in str(raised.value)


def test_the_acceptance_set_admission_symbol_decides_a_singleton() -> None:
    """``req:acceptance-set-admission``'s symbol.

    ``validate_acceptance_set`` decides both geometries; a singleton whose
    frequencies do not sum to one is refused there, exactly, naming the
    definition, and the TOY-1 singleton itself is admitted.
    """
    from dataclasses import replace

    from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
    from certiqs_key.meat_core.declaration.validation import validate_acceptance_set
    from certiqs_key.meat_core.errors import DeclarationError

    declaration = declaration_from_bundle(build_bundle(toy("TOY-1")))
    validate_acceptance_set(declaration)
    short = replace(
        declaration,
        acceptance_set=AcceptanceSet(geometry="singleton", frequencies=(0.5,)),
    )
    with pytest.raises(DeclarationError, match="def:admissible-acceptance-set"):
        validate_acceptance_set(short)


#: The fields of a result the token must not move: every number the solve
#: computed and every record but the length's. ``assurance`` is not in the
#: list: the certified tier is achieved only where the run is reported at it,
#: so a run the token lets report a certified length achieves
#: it and the same run without the token achieves first-order
#: (:func:`_assert_achieved_tiers`).
SAME_WITH_AND_WITHOUT = (
    "alpha",
    "rounds",
    "h_low",
    "h_lb",
    "h_lb_dropped",
    "dropped_set",
    "optimized_q",
    "predicted_statistics",
    "block_contributions",
    "sector_weight_report",
    "sector_report",
    "map_validation_report",
    "deductions",
    "constraint_entries_through_a_reductions_chain",
    "estimate_point_relaxed_member",
    "mathematical_spec_version",
)
SAME_CERTIFICATE_KEYS = (
    "solver_status",
    "iterations",
    "frank_wolfe_gap",
    "security_gates",
    "per_iterate",
    "assurance_reason",
    "module_versions",
)


@pytest.mark.requires_qics
@pytest.mark.parametrize("alpha", [1.5, 2.5])
def test_the_solve_decides_provenance_last(alpha: float) -> None:
    """On the solve path the gate is the last one.

    At ``alpha = 1.5`` every other gate opens and only the token withholds;
    at ``alpha = 2.5`` the key-length confinement withholds the length on
    both runs and its reason is reported, the token or not.
    """
    from certiqs_key.solvers.frank_wolfe import solve_bundle
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    bundle = build_bundle(toy("TOY-1"))
    given = solve_bundle(bundle, QicsSectorChoiOracle(), alpha=alpha, compiled=COMPILED)
    withheld = solve_bundle(bundle, QicsSectorChoiOracle(), alpha=alpha)
    assert withheld.key_length is None
    if alpha < 2:
        assert given.key_length is not None
        assert withheld.key_length_reason.startswith(DECLARATION_NOT_COMPILED)
    else:
        assert given.key_length is None
        for result in (given, withheld):
            assert "req:key-length-alpha-domain" in result.key_length_reason
            assert DECLARATION_NOT_COMPILED not in result.key_length_reason
        assert given.key_length_reason == withheld.key_length_reason
    for name in SAME_WITH_AND_WITHOUT:
        assert getattr(withheld, name) == getattr(given, name), name
    for key in SAME_CERTIFICATE_KEYS:
        assert withheld.certificate[key] == given.certificate[key], key
    _assert_achieved_tiers(given, withheld)


def _assert_achieved_tiers(given: Any, withheld: Any) -> None:
    """Check the achieved tier with the token and without it.

    Without the token no length is reported, so the run achieves first-order
    whatever the certified evaluation found; with it, the tier it reports
    with its length (the frank-wolfe interface's ``optimizer_certificate``
    row: certified "where the certified evaluation certified a point and the
    run is reported at it").
    """
    assert withheld.assurance is Assurance.FIRST_ORDER
    expected = (
        Assurance.FIRST_ORDER if given.key_length is None else given.reported_tier
    )
    assert given.assurance is expected


@pytest.mark.requires_qics
def test_the_token_decides_whether_the_length_is_reported_and_nothing_else() -> None:
    """One bundle solved with and without the token.

    Without it: no length, no composed outputs, the estimate tier, the
    estimate's root beside the bound's, no
    key-length premise beyond what the bound carries, and
    the reason opening with the code. Everything the solve computed is the
    same number on both runs (:data:`SAME_WITH_AND_WITHOUT`).
    """
    from certiqs_key.meat_core.reasons import FIRST_ORDER_ROWS
    from certiqs_key.solvers.frank_wolfe import solve_bundle
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    bundle = build_bundle(toy("TOY-1"))
    given = solve_bundle(bundle, QicsSectorChoiOracle(), alpha=1.5, compiled=COMPILED)
    withheld = solve_bundle(bundle, QicsSectorChoiOracle(), alpha=1.5)

    assert given.key_length is not None
    # The certified evaluation runs by default and certifies this toy, so the tier
    # reported with the length is `certified` where the ball arithmetic is
    # installed (frank-wolfe/req:certified-evaluation (vi)); without the token
    # no length and no such tier.
    assert given.reported_tier is BRACKET_TIER
    assert withheld.key_length is None
    assert withheld.security_parameter is None
    assert withheld.net_key_length is None
    assert withheld.reported_tier is Assurance.ESTIMATE
    assert withheld.key_length_reason.startswith(DECLARATION_NOT_COMPILED)
    assert withheld.first_order_clamped is False
    # The bound the run still reports names its root.
    assert withheld.certificate["claim_roots"] == [ESTIMATE_ROOT, FIRST_ORDER_ROOT]

    # The bound is still earned and reported: a withholding is no withdrawal.
    # The achieved tier is first-order: the evaluation runs on the withheld run
    # too, but the certified tier is achieved only where the run is reported at
    # it (the frank-wolfe interface's optimizer_certificate row).
    assert withheld.assurance is Assurance.FIRST_ORDER
    assert given.assurance is BRACKET_TIER
    for name in SAME_WITH_AND_WITHOUT:
        assert getattr(withheld, name) == getattr(given, name), name
    for key in SAME_CERTIFICATE_KEYS:
        assert withheld.certificate[key] == given.certificate[key], key

    # The ledger: the premises of a reported length go, those of the bound stay.
    length_only = {
        ASSUMPTION_MACHINE_KEYS[member]
        for member in KEY_LENGTH_ROWS
        if member not in FIRST_ORDER_ROWS
    }
    assert length_only <= set(given.assumption_ledger)
    assert not length_only & set(withheld.assumption_ledger)
    # A-SEQ travels with the bound.
    assert "sequential_round_model" in withheld.assumption_ledger
    assert {ASSUMPTION_MACHINE_KEYS[member] for member in FIRST_ORDER_ROWS} <= set(
        withheld.assumption_ledger
    )


@pytest.mark.requires_qics
def test_the_pipeline_withholds_on_a_bundle_that_changed_on_the_disk(
    tmp_path, monkeypatch  # noqa: ANN001
) -> None:
    """The token only for the bundle written.

    ``run_slice`` reads back a bundle whose manifest differs from the one it
    wrote (a stand-in for any round-trip defect). It mints no token for it, so
    the engine withholds the length with its own reason, the read stage
    records ``round_trip_identical`` False and emits the bundle it read, and
    the run is not refused. The same run with the read untouched reports a
    length and records True.
    """
    from dataclasses import replace

    from instances.bb84.specification import bb84_specification
    from instances.common.honest.depolarized_bell_pair import honest_provider

    from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
    from certiqs_key.runs import pipeline
    from certiqs_key.runs.pipeline import SliceResult, SliceStage, run_slice
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    def run(directory):  # noqa: ANN001, ANN202
        half = F(1, 2)
        outcome = run_slice(
            bb84_specification(half, half, half, half),
            honest_provider=honest_provider(F(1, 50)),
            rounds=2_000,
            completeness_budget=F(1, 1_000_000),
            parameters=KeyLengthParameters(
                alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
            ),
            oracle=QicsSectorChoiOracle(),
            directory=directory,
            created_by="test",
            declared_tolerance=0.0,
            alpha=1.5,
        )
        assert isinstance(outcome, SliceResult), outcome
        (read,) = [r for r in outcome.stages if r.stage is SliceStage.BUNDLE_READ]
        return outcome, read

    intact, intact_read = run(tmp_path / "intact")
    assert intact_read.detail["round_trip_identical"] is True
    assert intact.key_rate.key_length is not None

    original = pipeline.read_bundle

    def altered(directory):  # noqa: ANN001, ANN202
        bundle = original(directory)
        manifest = bundle.manifest.model_copy(update={"created_by": "elsewhere"})
        return replace(bundle, manifest=manifest)

    monkeypatch.setattr(pipeline, "read_bundle", altered)
    changed, changed_read = run(tmp_path / "changed")
    assert changed_read.detail["round_trip_identical"] is False
    assert changed_read.emits[0].digest != intact_read.emits[0].digest
    assert changed.key_rate.key_length is None
    assert changed.key_rate.key_length_reason.startswith(DECLARATION_NOT_COMPILED)
    assert changed.key_rate.h_low == intact.key_rate.h_low
