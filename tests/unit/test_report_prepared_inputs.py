"""The report states the value a run analysed, not only the one requested.

A report can name the request and not the value analysed: a six-state run
requested a test probability of 10 %, its protocol document
prepared it on a 2^-11 grid to 205/2048 = 10.009765625 %, the value analysed,
and the report printed 205/2048 in the public choice and then called the test
fraction 1/10. A protocol document's preparation ``rebind``s the parameter to
the prepared member of its family; the record's configuration keeps the
request. The bbm92 example is a protocol document with exactly that
preparation (``bbm92.test_coin``, ``rebind: {test_fraction: 1}``); its
request is made 1/10 and its prepared family the one the 2^-11 grid gives,
written by hand: 1/10 * 2048 = 204.8 rounds to 205, and 1843 = 2048 - 205.

R3a: the summary says plainly that the calculation is model-based.
"""

from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path
from typing import Any

import pytest

from certiqs_key.runs.report import build_report, default_contract_link, report_schema
from certiqs_key.runs.report.inputs import analysed_config, prepared_inputs
from certiqs_key.runs.report.render_markdown import render_markdown

ROOT = Path(__file__).resolve().parents[2]


def _bbm92() -> dict[str, Any]:
    path = ROOT / "runs" / "report_examples" / "bbm92" / "record.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        record: dict[str, Any] = json.load(handle)
    return record


def _requested_one_tenth() -> dict[str, Any]:
    record = copy.deepcopy(_bbm92())
    payload = record["payload"]
    payload["config"]["device"]["test_fraction"] = "1/10"
    (entry,) = payload["snaps"]["instance"]["input_preparation"]
    entry["input_values"] = ["9/10", "1/10"]
    entry["prepared_values"] = ["1843/2048", "205/2048"]
    return record


def test_the_prepared_member_is_found_through_the_document_s_rebind() -> None:
    record = _requested_one_tenth()
    assert prepared_inputs(record) == {
        "test_fraction": (
            "205/2048",
            "/payload/snaps/instance/input_preparation/0/prepared_values/1",
        )
    }
    assert analysed_config(record)["device"]["test_fraction"] == "205/2048"
    assert record["payload"]["config"]["device"]["test_fraction"] == "1/10"


def test_a_record_without_a_document_preparation_has_none() -> None:
    record = _bbm92()
    del record["payload"]["protocol_document"]
    assert prepared_inputs(record) == {}


def test_the_report_states_the_analysed_value_with_the_request_beside_it() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    report = build_report(_requested_one_tenth())
    jsonschema.validate(report, report_schema())
    (row,) = [row for row in report["sections"]["protocol"]["inputs"]
              if row["name"] == "device.test_fraction"]
    assert (row["value"], row["prepared"]) == ("1/10", "205/2048")
    summary = report["sections"]["summary"]
    # Decimal first, the exact fraction and the request beside it.
    assert any("test fraction 0.100098 (exactly 205/2048; requested 0.1)" in line
               for line in summary["setup_brief"])
    text = render_markdown(report, contract_link=default_contract_link())
    assert ("The test fraction is 0.100098 (exactly 205/2048; requested 0.1)."
            in text)
    assert ("0.100098 (205/2048), prepared from the requested 0.1 and "
            "analysed") in text
    assert "The test fraction is 1/10." not in text


def test_an_unchanged_preparation_reads_as_before() -> None:
    report = build_report(_bbm92())
    (row,) = [row for row in report["sections"]["protocol"]["inputs"]
              if row["name"] == "device.test_fraction"]
    assert (row["value"], row["prepared"]) == ("1/8", "1/8")
    text = render_markdown(report, contract_link=default_contract_link())
    assert "The test fraction is 0.125." in text
    assert "requested" not in text.split("The test fraction is", 1)[1][:40]


def test_the_summary_says_the_calculation_is_model_based() -> None:
    record = _bbm92()
    glance = [item["lead"] + item["text"]
              for item in build_report(record)["sections"]["summary"]["at_a_glance"]]
    assert ("Model-based: no measured data analysed; the acceptance test is built "
            "around your honest model's predictions") in glance
    record["payload"]["honest_model_note"] = {"overridden": True, "model": "table"}
    glance = [item["text"]
              for item in build_report(record)["sections"]["summary"]["at_a_glance"]]
    assert any(text.endswith("the acceptance test is built around a "
                             "distribution supplied with the run in place of the "
                             "instance's honest model") for text in glance)
