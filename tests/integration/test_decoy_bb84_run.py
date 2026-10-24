"""Run-path smoke test: actual public inputs reach the general solver and bundle.

Two iterations exercise composition, not convergence or the numerical study's
2000-iteration performance target. No key-rate oracle is manufactured here.
"""

import json
from fractions import Fraction as F
from pathlib import Path

import pytest
from instances.decoy_bb84 import default_config, runner
from tests.support.manifest_spelling import assert_bindings_in_declared_spelling

from certiqs_key.runs.config import SolverSettings
from certiqs_key.runs.pipeline import SliceResult


def test_vacuum_public_runner_writes_the_general_bundle(tmp_path: Path):
    pytest.importorskip("qics")
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    config = default_config(
        rounds=10_000,
        solver=SolverSettings(method="fw", max_iterations=2),
        device={
            "mu_signal": 0,
            "mu_weak": 0,
            "mu_vacuum": 0,
            "dark_count": dict.fromkeys(("H", "V", "D", "A"), F(1, 64)),
        },
    )
    outcome = runner(
        QicsSectorChoiOracle(), tmp_path, created_by="decoy integration test"
    )(config, 0)
    assert isinstance(outcome, SliceResult), outcome
    assert outcome.bundle_directory.is_dir()
    assert outcome.channel_interface is not None
    assert (
        outcome.channel_interface.as_payload()["source_shape"] == "mode_and_intensity"
    )
    assert outcome.rows_adaptation is not None
    assert "input_preparation" in outcome.rows_adaptation


@pytest.mark.requires_qics
def test_nonvacuum_record_resolves_source_receiver_and_roundtrips_ensemble(
    tmp_path: Path,
) -> None:
    """The actual prepared source licence and inherited receiver reach disk."""
    import jsonschema

    from certiqs_key.domain.bundle import read_bundle
    from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
    from certiqs_key.meat_core.declaration.general import GeneralDeclaration
    from certiqs_key.runs.record import record_run
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    config = default_config(
        rounds=100_000,
        solver=SolverSettings(method="fw", max_iterations=1),
        model={"transmittance": F(1, 10)},
        device={"dark_count": dict.fromkeys(("H", "V", "D", "A"), F(1, 1_000_000))},
    )
    outcome = runner(
        QicsSectorChoiOracle(), tmp_path, created_by="decoy manifest test"
    )(config, 0)
    assert isinstance(outcome, SliceResult), outcome
    record = record_run(outcome, config, created_by="decoy manifest test").as_dict()
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "certiqs_key"
        / "runs"
        / "record.schema.json"
    )
    jsonschema.validate(record, json.loads(schema_path.read_text(encoding="utf-8")))
    # One value per bound name, in the declared spelling (the decoy letters go
    # through the wire bijection too).
    assert_bindings_in_declared_spelling(record)
    # The manifest is the route-exact set, one entry per engaged assumption
    # with every emitter; each entry's `verification` is the closure table's
    # field. The facts below are read off the entries.
    manifest = record["payload"]["assumption_manifest"]
    entries = {entry["short_id"]: entry for entry in manifest["assumptions"]}
    assert len(entries) == len(manifest["assumptions"]), "one entry per id"

    def emitters(short_id: str) -> set[str]:
        return {emitter["module"] for emitter in entries[short_id]["emitted_by"]}

    def keys(short_id: str) -> set[str]:
        return {emitter["machine_key"] for emitter in entries[short_id]["emitted_by"]}

    assert keys("A-WCP") == {"wcp_source_model"}
    assert "receiver" in emitters("A-THRESH")
    # A-RECV: no compiler row on any route, and this run built its receiver
    # artefact itself, exact and with every weight rigorous, so the reductions
    # artefact omits its row and records why (req:recv-row-provenance): the
    # manifest names that requirement as a reductions root and lists A-RECV as
    # not engaged, discharged by it, while the receiver's own rows, which the
    # record carries with the artefact (condition (iii)), stay listed.
    assert "A-RECV" not in entries
    assert "receiver_artifact_accepted" not in outcome.compilation.assumption_ledger
    reduction = record["payload"]["stages"]["reduction"]
    assert reduction["receiver_bound_evaluation"] == "rigorous"
    (omitted,) = reduction["receiver_row_omitted_on_provenance"]
    assert omitted == reduction["receiver_spec_version"]
    assert omitted.startswith("receiver@")
    assert "reductions/req:recv-row-provenance" in manifest["roots"]["reductions"]
    (recv,) = [
        item for item in manifest["not_engaged"] if item["short_id"] == "A-RECV"
    ]
    assert recv["module"] == "reductions"
    assert recv["discharged_by"] == "reductions/req:recv-row-provenance"
    receiver_ledger = record["payload"]["stages"]["receiver_construction"][
        "assumption_ledger"
    ]
    assert receiver_ledger
    assert "A-TRUST" in entries and "receiver" in emitters("A-TRUST")
    assert manifest["discrepancies"] == []
    serialized_manifest = json.dumps(manifest)
    assert "receiver_povm_characterized" not in serialized_manifest
    # statistics' ledger reaches the manifest: the rows its interface's
    # emission_rule gives the canonical box the construction emits, and no
    # inherited A-TSM, which no result statistics reports rests on; the
    # honest-model keys are identifiers.
    statistics_ids = {
        short_id for short_id in entries if "statistics" in emitters(short_id)
    }
    assert statistics_ids == {"A-HON-ENV", "A-ALPHABET", "A-REACH"}
    assert keys("A-HON-ENV") == {"honest_rounds_within_envelope"}
    # A-TSM under ONE key, its owner's; statistics does not emit it, nor does
    # the engine, whose closures never held it; the reductions artefact emits
    # it, its flat squashing result resting on it, only where the station has
    # a private setting or a public choice is applied at it
    # (req:assumption-ledger); this decoy
    # receiver is probe-free (T = {off}) and its basis choice is Alice's
    # letter-side choice, so A-TSM is not engaged, nor is A-PROBE.
    assert "A-TSM" not in entries
    assert "A-PROBE" not in entries
    assert {"A-TSM", "A-PROBE"} <= {
        item["short_id"] for item in manifest["not_engaged"]
        if item["module"] == "reductions"
    }
    # The engine's machine keys on this decoy run with a bound are: the rows
    # whose `verification` field is `never` -- key_register and pa_hash_family
    # -- round_homogeneity_declaration, and the key-length premises meat-core
    # owns together with A-SEQ, every one `verification: never` and emitted on
    # every run that reports a key length (A-SEED, A-FIXED, A-CONFORM,
    # A-AUTH, A-LAB; transmitter/ass:seq). A-LAB is one key,
    # laboratory_sealed, emitted once per party.
    engine_keys = {"attack_set_license", "source_replacement_license"} | {
        "key_register", "pa_hash_family",
        "round_homogeneity_declaration",
    } | {
        "post_processing_seeds", "parameters_fixed_before_run",
        "post_processing_as_analysed", "classical_channel_authenticated",
        "laboratory_sealed",
        "sequential_round_model",
    }
    from_engine = {
        emitter["machine_key"]
        for entry in manifest["assumptions"]
        for emitter in entry["emitted_by"]
        if emitter["module"] == "meat-core"
    }
    assert from_engine <= engine_keys
    assert "source_replacement_license" in from_engine
    # There is no A-RATIONAL row: its condition is
    # statistics/def:conservative-evaluation.
    # A-ALPHABET's row is the clause no code decides, under its own key.
    assert keys("A-ALPHABET") == {"acceptance_recorded_every_round"}
    # ONE FIELD PER ASSUMPTION (by entry).
    # (A-TSM is not engaged on this probe-free run. A-LMO is superseded and no
    # ledger emits it, so it is in no manifest.)
    assert "A-LMO" not in entries
    for short_id in ("A-WCP",):
        assert entries[short_id]["verification"] == "never", short_id
    # There is no A-BLOCK row (rem:block-restriction).
    assert "block_diagonal_feasible_set" not in serialized_manifest
    # reductions' and receiver's never-verifiable assumptions reach it too.
    for module, short_id in (
        ("reductions", "A-MEAS"),
        ("reductions", "A-ROUND-SQ"),
        ("receiver", "A-NOSEL"),
        ("receiver", "A-ROUND"),
    ):
        assert module in emitters(short_id), short_id
        assert entries[short_id]["verification"] == "never", short_id
    assert "source_stage_empty" not in serialized_manifest
    assert manifest["discrepancies"] == []
    # No A-PROBE-DIAG row anywhere -- not in the receiver's ledger, the
    # reductions A-RECV inheritance, the record's receiver assumptions or its
    # manifest, on every receiver, probe-free or not. The other inherited
    # keys stay.
    assert outcome.receiver_artifact is not None
    assert "A-PROBE-DIAG" not in [
        str(row.assumption_id) for row in outcome.receiver_artifact.assumption_ledger
    ]
    serialized = json.dumps(record)
    assert "A-PROBE-DIAG" not in serialized
    assert "probe_fock_diagonal" not in serialized
    bundle = read_bundle(outcome.bundle_directory)
    restored = declaration_from_bundle(bundle)
    assert isinstance(restored, GeneralDeclaration)
    assert restored.is_ensemble_form and restored.is_trusted_source
    assert "n1" in restored.alice_sectors and len(restored.alice_sectors) > 2
    assert restored.source_replacement_license is not None
    chain = bundle.manifest.payload.reduction_chain
    assert chain is not None and chain.source_segment
    assert outcome.rows_adaptation is not None
    assert "input_preparation" in outcome.rows_adaptation
