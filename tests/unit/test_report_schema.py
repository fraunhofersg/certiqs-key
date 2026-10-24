"""Built key-rate reports validate against the schema shipped beside the builder.

THE SCHEMA IS WRITTEN BY HAND AND NOT GENERATED FROM ``runs/report/model.py``
(the house rule of ``runs/record.schema.json``): a generated schema would agree with the
builder by construction and
say nothing. Completed, refused and estimate-tier reports and a sweep are
validated, and two content rules the schema states are shown to bite.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from tests.support.report_records import (
    completed_record,
    estimate_record,
    refused_record,
    synthetic_table,
)

from certiqs_key.runs.report import build_report, build_sweep_report, report_schema

jsonschema = pytest.importorskip("jsonschema")

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "src" / "certiqs_key" / "runs" / "report" / "report.schema.json"
)


def validate(document: Any) -> None:
    jsonschema.validate(document, report_schema())


def test_the_schema_is_valid_json_schema() -> None:
    jsonschema.Draft202012Validator.check_schema(report_schema())


def test_the_package_data_is_the_checked_in_file() -> None:
    assert report_schema() == json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "record",
    [completed_record(), refused_record(), estimate_record(),
     completed_record(lambda_ec=10, eps_auth=1e-12, k_auth=128)],
    ids=["completed", "refused", "estimate", "nonzero-parameters"],
)
def test_a_built_report_validates(record: dict[str, Any]) -> None:
    built = build_report(record, table=synthetic_table())
    validate(built)
    # And it is JSON, not merely dict-shaped.
    assert json.loads(json.dumps(built)) == built


def test_a_sweep_report_validates() -> None:
    records = [completed_record(qber=q) for q in ("1/50", "1/25")] + [refused_record()]
    validate(build_sweep_report(records, table=synthetic_table()))


def test_the_schema_refuses_a_numerical_trust_group_in_the_vouch_list() -> None:
    built: dict[str, Any] = copy.deepcopy(
        build_report(completed_record(), table=synthetic_table())  # type: ignore[arg-type]
    )
    built["sections"]["assumptions"]["groups"][0]["category"] = "numerical-trust"
    with pytest.raises(jsonschema.ValidationError):
        validate(built)


def test_the_schema_refuses_a_decided_row_in_the_vouch_list() -> None:
    built: dict[str, Any] = copy.deepcopy(
        build_report(completed_record(), table=synthetic_table())  # type: ignore[arg-type]
    )
    head = built["sections"]["assumptions"]["groups"][0]["families"][0]["head"]
    head["verification"] = "decided"
    with pytest.raises(jsonschema.ValidationError):
        validate(built)


def test_the_schema_refuses_an_aggregate_security_parameter_on_a_sweep() -> None:
    sweep: dict[str, Any] = copy.deepcopy(
        build_sweep_report([completed_record()], table=synthetic_table())  # type: ignore[arg-type]
    )
    sweep["common"]["security_parameter"] = 1e-9
    with pytest.raises(jsonschema.ValidationError):
        validate(sweep)
    del sweep["common"]["security_parameter"]
    sweep["total_security_parameter"] = 1e-9
    with pytest.raises(jsonschema.ValidationError):
        validate(sweep)
