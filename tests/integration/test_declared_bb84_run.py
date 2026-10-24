"""A document declaring every user-declared kind runs and is reported.

A custom document declaring every user-declared kind runs end to end: its
record validates against ``record.schema.json``, carries the document, and its
key-rate report lists each item.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from tests.support.declared_documents import coverage_surface

from certiqs_key.runs.config import SolverSettings
from certiqs_key.runs.record import RECORD_SCHEMA_VERSION, record_run
from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_markdown,
    report_schema,
)
from certiqs_key.runs.surface import InstanceIdentity

pytestmark = pytest.mark.requires_qics

SOLVER = SolverSettings(method="fw", max_iterations=5)


def _record(surface: Any, config: Any, directory: Path) -> dict[str, Any]:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    outcome = surface.runner(QicsSectorChoiOracle(), directory, created_by="parity")(
        config, 0
    )
    record = record_run(
        outcome,
        config,
        created_by="parity",
        instance=InstanceIdentity(surface.DESCRIPTOR, surface.PARAMETERS),
    ).as_dict()
    return record


def test_a_document_declaring_everything_runs_and_is_reported(tmp_path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    surface = coverage_surface("explicit_entries_with_licence")
    record = _record(surface, surface.default_config(solver=SOLVER), tmp_path)
    assert record["schema_version"] == RECORD_SCHEMA_VERSION
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "certiqs_key"
        / "runs"
        / "record.schema.json"
    )
    jsonschema.validate(record, json.loads(schema_path.read_text(encoding="utf-8")))
    assert json.loads(json.dumps(record)) == record
    document = record["payload"]["protocol_document"]
    assert document["digest"] == surface.digest
    report = build_report(record)
    jsonschema.validate(report, report_schema())
    kinds = {item["kind"] for item in report["sections"]["result"]["user_declared"]}
    assert kinds == {
        "retention_attestation",
        "receiver_povm",
        "constraint_entry",
        "attack_set_license",
        "feasibility_witness",
    }
    assert report["sections"]["assumptions"]["user_declared"]
    # THE PREMISES A DECLARED POVM NAMES ARE THE ONES THE ROUTE ENGAGES:
    # A-SPEC and A-IDEAL are in R3, so the "vouched for by you" row
    # links them inside the report rather than out to a contract.
    engaged = {
        entry["short_id"]
        for group in report["sections"]["assumptions"]["groups"]
        for family in group["families"]
        for entry in (family["head"], *family["members"])
    }
    assert {"A-SPEC", "A-IDEAL"} <= engaged
    markdown = render_markdown(report, contract_link=default_contract_link())
    declared = markdown[markdown.index("vouched for by you") :]
    assert "(#A-SPEC)" in declared and "(#A-IDEAL)" in declared
