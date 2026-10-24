"""An optical protocol document runs end to end and its premises are reported.

A custom optical
station declared by its port Grams -- numbers the engine takes as the device,
not catalogue optics -- runs at ``SolverSettings(method="fw", max_iterations=5)``. Its
record validates against ``record.schema.json`` and carries the
``receiver_characterisation`` item under A-TRUST; the key-rate report lists it
in the result and the assumption sections, and the rendered "vouched for by
you" row links A-TRUST inside the report, because the optical route engages it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.support.declared_optical_documents import coverage_surface

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

ROOT = Path(__file__).resolve().parents[2]


def test_a_port_gram_document_runs_and_its_characterisation_is_reported(
    tmp_path: Path,
) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = coverage_surface("port_grams")
    config = surface.default_config(
        solver=SolverSettings(method="fw", max_iterations=5)
    )
    outcome = surface.runner(QicsSectorChoiOracle(), tmp_path, created_by="test")(
        config, 0
    )
    record = record_run(
        outcome,
        config,
        created_by="test",
        instance=InstanceIdentity(surface.DESCRIPTOR, surface.PARAMETERS),
    ).as_dict()
    assert record["schema_version"] == RECORD_SCHEMA_VERSION
    schema = json.loads(
        (ROOT / "src" / "certiqs_key" / "runs" / "record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(record, schema)
    items = record["payload"]["protocol_document"]["user_declared"]
    assert [(item["kind"], item["assumptions"]) for item in items] == [
        ("receiver_characterisation", ["A-TRUST"])
    ]
    report = build_report(record)
    jsonschema.validate(report, report_schema())
    kinds = [item["kind"] for item in report["sections"]["result"]["user_declared"]]
    assert kinds == ["receiver_characterisation"]
    engaged = {
        entry["short_id"]
        for group in report["sections"]["assumptions"]["groups"]
        for family in group["families"]
        for entry in (family["head"], *family["members"])
    }
    assert "A-TRUST" in engaged
    markdown = render_markdown(report, contract_link=default_contract_link())
    declared = markdown[markdown.index("vouched for by you") :]
    assert "(#A-TRUST)" in declared
