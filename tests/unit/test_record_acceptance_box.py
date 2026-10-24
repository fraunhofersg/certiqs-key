"""The acceptance box in the run record, and the report's acceptance categories.

The record carries the box ``[q^-, q^+]`` per outcome in its own labels
(``stages.acceptance_construction.box``), so a reader of the record alone sees
the intervals a key length rests on; the report turns each into a row of
"Acceptance categories": the honest probability, the frequency interval and
the counts it admits out of the run's rounds, ends included. The expected
counts below are worked by hand: ``ceil(n q^-)`` and ``floor(n q^+)``, with
bounds chosen so that both roundings bite.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest
from tests.support.report_records import completed_record

from certiqs_key.runs.record import _box_payload
from certiqs_key.runs.report import build_report, default_contract_link, report_schema
from certiqs_key.runs.report.render_markdown import render_markdown
from certiqs_key.runs.report.setup import build_setup
from certiqs_key.statistics.taxonomy import PolytopeGeometry, canonical_box

OUTCOMES = ("gen", "ok", "err", "disc")
LOWER = (Fraction(22785, 100000), Fraction(2279, 10000), Fraction(0),
         Fraction(4742, 10000))
UPPER = (Fraction(27255, 100000), Fraction(2725, 10000), Fraction(0),
         Fraction(5258, 10000))


def test_the_record_carries_the_box_per_outcome_label_exactly() -> None:
    box = _box_payload(canonical_box(OUTCOMES, LOWER, UPPER))
    assert box == {
        "gen": {"lower": "4557/20000", "upper": "5451/20000"},
        "ok": {"lower": "2279/10000", "upper": "109/400"},
        "err": {"lower": "0", "upper": "0"},
        "disc": {"lower": "2371/5000", "upper": "2629/5000"},
    }


def test_a_polytope_without_box_form_records_no_box() -> None:
    general = PolytopeGeometry(outcomes=("a", "b"), rows=((Fraction(1), Fraction(0)),),
                               rhs=(Fraction(1, 2),))
    assert _box_payload(general) is None


def _record() -> dict[str, Any]:
    record = completed_record()
    record["payload"]["config"]["rounds"] = 10_000
    stage = record["payload"]["stages"]["acceptance_construction"]
    stage["outcomes"] = list(OUTCOMES)
    stage["honest_distribution"] = {
        "gen": "1/4", "ok": "1/4", "err": "0", "disc": "1/2"}
    stage["box"] = _box_payload(canonical_box(OUTCOMES, LOWER, UPPER))
    return record


def test_each_category_gives_the_counts_its_interval_admits() -> None:
    acceptance = build_setup(_record())["acceptance"]
    assert acceptance is not None
    counts = {row["outcome"]: (row["count_min"], row["count_max"])
              for row in acceptance["categories"]}
    # 10000 * 0.22785 = 2278.5 rounds up; 10000 * 0.27255 = 2725.5 rounds down.
    assert counts == {"gen": (2279, 2725), "ok": (2279, 2725), "err": (0, 0),
                      "disc": (4742, 5258)}
    assert [row["probability"] for row in acceptance["categories"]] == [
        0.25, 0.25, 0.0, 0.5]
    assert "The table of acceptance categories" in acceptance["text"]


def test_the_page_prints_the_categories_and_validates() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    report = build_report(_record())
    jsonschema.validate(report, report_schema())
    text = render_markdown(report, contract_link=default_contract_link())
    assert "Acceptance categories" in text
    assert "Rows of the box" not in text
    assert "2,279 to 2,725 of 10,000" in text
    assert "exactly 0 of 10,000" in text
    assert "4,742 to 5,258 of 10,000" in text


def test_a_record_without_a_box_keeps_the_honest_table_and_its_note() -> None:
    record = _record()
    del record["payload"]["stages"]["acceptance_construction"]["box"]
    acceptance = build_setup(record)["acceptance"]
    assert acceptance is not None
    assert acceptance["categories"] == []
    assert "does not list the intervals themselves" in acceptance["text"]
