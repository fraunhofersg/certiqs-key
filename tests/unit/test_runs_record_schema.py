"""A produced run record validates against the schema checked in beside it.

The record's JSON Schema is checked in (``runs/record.schema.json``), with a
test that a produced record validates. A consumer can then generate types, and
a schema change is visible in review.

THE SCHEMA IS WRITTEN BY HAND AND NOT GENERATED FROM THE CODE, and that is the
same rule the oracle registries are under (PRINCIPLES.md section 2.3): a schema
generated from the record builder would agree with it by construction and would
say nothing. This one states what a CONSUMER may rely on, and when the two
disagree the test says so.

Both routes are validated -- a completed run and a refused one -- because a
refusal is a record like any other and a consumer reads it with the same types.
"""

from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs import RunConfig
from certiqs_key.runs.pipeline import SliceRefusal, SliceStage
from certiqs_key.runs.record import RECORD_SCHEMA_VERSION, record_run

pytestmark = pytest.mark.contract

jsonschema = pytest.importorskip("jsonschema")

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "certiqs_key"
    / "runs"
    / "record.schema.json"
)


def schema() -> dict[str, object]:
    """Return the checked-in schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def config(**changes: object) -> RunConfig:
    base = {
        "rounds": 2_000,
        "completeness_budget": F(1, 1_000_000),
        "parameters": KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        "declared_tolerance": 0.0,
        "model": {"qber": F(1, 50)},
    }
    return RunConfig(**{**base, **changes})  # type: ignore[arg-type]


def test_the_schema_is_valid_json_schema() -> None:
    """A schema a validator refuses would check nothing."""
    jsonschema.Draft202012Validator.check_schema(schema())


def test_a_refused_run_s_record_validates() -> None:
    """A refusal is a record like any other, read with the same types."""
    outcome = SliceRefusal(
        stage=SliceStage.COMPILATION,
        reason="specification_not_well_formed",
        detail="a detail the module wrote",
    )
    record = record_run(outcome, config(), created_by="test").as_dict()
    jsonschema.validate(record, schema())


@pytest.mark.requires_qics
def test_a_completed_run_s_record_validates(tmp_path: Path) -> None:
    """The whole shape, on a run that reached a key length."""
    from instances.bb84.specification import bb84_specification
    from instances.common.honest.depolarized_bell_pair import honest_provider

    from certiqs_key.runs.pipeline import run_slice
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    outcome = run_slice(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        honest_provider=honest_provider(F(1, 50)),
        rounds=2_000,
        completeness_budget=F(1, 1_000_000),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        oracle=QicsSectorChoiOracle(),
        directory=tmp_path / "bundle",
        created_by="test",
        declared_tolerance=0.0,
        alpha=1.5,
        run_id=config().digest(),
    )
    assert not isinstance(outcome, SliceRefusal), outcome
    record = record_run(outcome, config(), created_by="test").as_dict()
    jsonschema.validate(record, schema())

    # AND THE RECORD IS JSON, not merely dict-shaped: the writer dumps it, and
    # a value the encoder refuses would be a record nobody can read back.
    assert json.loads(json.dumps(record)) == record

    # The route-exact manifest (0.20.0) on a real run: every entry engaged,
    # one per id, its text and field the table's; Band A's receiver route.
    manifest = record["payload"]["assumption_manifest"]
    ids = [entry["short_id"] for entry in manifest["assumptions"]]
    assert ids == sorted(set(ids))
    assert "A-AUTH" in ids
    assert record["payload"]["stages"]["receiver_construction"]["receiver_route"] == (
        "declared-finite-povm"
    )
    key_rate = record["payload"]["stages"]["key_rate"]
    assert (key_rate["key_length"] is None) is (key_rate["security_parameter"] is None)


def test_the_schema_and_the_code_agree_about_the_stage_vocabulary() -> None:
    """A renamed ``SliceStage`` moves a consumer's meaning; the schema catches it."""
    stage_schema = schema()["$defs"]["stage"]["properties"]["stage"]["enum"]  # type: ignore[index]
    assert set(stage_schema) == {str(stage) for stage in SliceStage}


def test_the_schema_and_the_code_agree_about_the_status_vocabulary() -> None:
    """The same for the four statuses a stage may have."""
    from certiqs_key.runs.flow import StageStatus

    status_schema = schema()["$defs"]["stage"]["properties"]["status"]["enum"]  # type: ignore[index]
    assert set(status_schema) == {str(status) for status in StageStatus}


def test_the_schema_and_the_code_agree_about_the_artefact_kinds() -> None:
    """And about the artefact kinds, wherever the schema names them.

    THE ENUM IS IN ``$defs``. ``emits.items`` and
    ``consumes.artefact_kinds`` are two places a kind appears --
    a PLANNED stage names kinds where it cannot name ids -- and two inline
    copies of one vocabulary would be free to drift apart. So the schema has
    ONE ``$defs`` entry and both sites ``$ref`` it, and this test asserts that
    both refs point at it: an inline enum reintroduced at either site fails
    here.
    """
    from certiqs_key.runs.flow import ArtefactKind

    document = schema()
    kinds = document["$defs"]["artefact_kind"]["enum"]  # type: ignore[index]
    assert set(kinds) == {str(kind) for kind in ArtefactKind}

    stage = document["$defs"]["stage"]["properties"]  # type: ignore[index]
    reference = {"$ref": "#/$defs/artefact_kind"}
    assert stage["emits"]["items"]["properties"]["kind"] == reference
    assert stage["consumes"]["properties"]["artefact_kinds"]["items"] == reference


def test_the_schema_and_the_code_agree_about_the_two_request_vocabularies() -> None:
    """``endpoint_rule`` and ``tail_evaluation`` are ``statistics``' own."""
    from certiqs_key.statistics.rules import EndpointRuleName, TailEvaluation

    properties = schema()["$defs"]["config"]["properties"]  # type: ignore[index]
    assert set(properties["endpoint_rule"]["enum"]) == {
        str(name) for name in EndpointRuleName
    }
    assert set(properties["tail_evaluation"]["enum"]) == {
        str(name) for name in TailEvaluation
    }


def test_the_schema_names_no_deferred_envelope_field() -> None:
    """The four content-addressing fields stay deferred with the store.

    spec/future-scope.md section 1. Accepting a hash field that nothing hashes
    would give it a meaning incompatible with the one it will carry, which
    spec/architecture.md 4.1 forbids in terms.
    """
    text = SCHEMA_PATH.read_text(encoding="utf-8")
    for deferred in ("artifact_id", "content_hash", "input_artifact_hashes"):
        assert f'"{deferred}"' not in text.replace(
            f"-- {deferred},", ""
        ), deferred


def test_the_schema_and_the_code_agree_about_the_manifest_vocabularies() -> None:
    """The route-exact set's closed lists (record schema 0.20.0).

    An entry's ``section``, its ``verification`` and a discrepancy's ``kind``
    are strings a consumer files on; each is the code's own vocabulary.
    """
    from certiqs_key.domain.claim_closure import VERIFICATIONS
    from certiqs_key.runs.assumptions import DiscrepancyKind, Section

    definitions = schema()["$defs"]
    entry = definitions["assumptionEntry"]["properties"]  # type: ignore[index]
    assert set(entry["section"]["enum"]) == {str(section) for section in Section}
    assert set(entry["verification"]["enum"]) == set(VERIFICATIONS)
    kinds = definitions["manifest"]["properties"]["discrepancies"]["items"][  # type: ignore[index]
        "properties"
    ]["kind"]["enum"]
    assert set(kinds) == {str(kind) for kind in DiscrepancyKind}


def test_the_schema_and_the_code_agree_about_the_key_length_reason_codes() -> None:
    """The key-length reason codes are a closed list, not a regex."""
    from certiqs_key.solvers.frank_wolfe.general_keyrate import (
        KEY_LENGTH_REASON_CODES,
    )

    key_rate = schema()["$defs"]["payload"]["properties"]["stages"]["properties"][  # type: ignore[index]
        "key_rate"
    ]["properties"]
    assert set(key_rate["key_length_reason_code"]["enum"]) == KEY_LENGTH_REASON_CODES


def test_a_refused_record_names_its_instance_and_its_engine() -> None:
    """The two new blocks are on a refusal too: it is reproduced on the same code."""
    from instances.bb84.surface import DESCRIPTOR, PARAMETERS

    from certiqs_key.runs.surface import InstanceIdentity

    outcome = SliceRefusal(
        stage=SliceStage.COMPILATION, reason="whatever", detail="detail"
    )
    record = record_run(
        outcome,
        config(eps_auth=2.0**-40, k_auth=64),
        created_by="test",
        instance=InstanceIdentity(DESCRIPTOR, tuple(PARAMETERS)),
    ).as_dict()
    jsonschema.validate(record, schema())
    payload = record["payload"]
    assert payload["instance"]["id"] == DESCRIPTOR.id
    assert len(payload["instance"]["parameters"]) == len(PARAMETERS)
    engine = payload["provenance"]["engine"]
    assert set(engine) == {"distribution_version", "git_commit", "git_dirty"}
    assert payload["config"]["parameters"]["eps_auth"] == 2.0**-40
    assert payload["config"]["parameters"]["k_auth"] == 64
    # Without an instance the block is null, never absent.
    bare = record_run(outcome, config(), created_by="test").as_dict()
    assert bare["payload"]["instance"] is None
    jsonschema.validate(bare, schema())


def test_the_record_version_is_the_one_the_code_emits() -> None:
    """So that a schema change and a version bump travel together."""
    outcome = SliceRefusal(
        stage=SliceStage.COMPILATION, reason="whatever", detail="detail"
    )
    record = record_run(outcome, config(), created_by="test")
    assert record.schema_version == RECORD_SCHEMA_VERSION
