"""The report says why a solver stage stopped and why the alpha search set a run aside.

The record has carried each corrective probe's ``stop_reason``, each stage's
``resumed``, each alpha-search evaluation's ``set_aside`` and the search's
``refinement_stopped`` since record 0.34.0; the report rendered only the
termination, so a probe cut by its slice and one cut by the stage both read
``budget_exhausted``, and the headline was the last attempt's word. The
search reports below are written by hand
in the shape ``solvers/solve.py`` records.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from tests.support.report_records import completed_record

from certiqs_key.runs.report import build_report, default_contract_link, report_schema
from certiqs_key.runs.report.explain import solve_stop, solver_attempts
from certiqs_key.runs.report.render_markdown import render_markdown

ROOT = Path(__file__).resolve().parents[2]

#: A licensed run: the fw stage stopped at its iteration cap, a corrective
#: probe found no bracket progress, a resumed probe ended in a numerical
#: failure; 51 of 600 seconds spent.
STOPPED_EARLY: dict[str, Any] = {
    "termination": "numerical_failure",
    "budget_seconds": 600.0,
    "gap_target": 1e-6,
    "max_iterations": 30,
    "max_iterations_caps": ["fw"],
    "attempts": [
        {"method": "fw", "termination": "budget_exhausted", "iterations": 30,
         "seconds": 40.0, "resumed": False},
        {"method": "corrective", "termination": "stagnated", "iterations": 4,
         "seconds": 6.0, "resumed": False, "probe": 1,
         "stop_reason": "no_bracket_progress"},
        {"method": "corrective", "termination": "numerical_failure",
         "iterations": 2, "seconds": 5.0, "resumed": True, "probe": 1,
         "stop_reason": "search_numerical_failure"},
    ],
}


def test_each_attempt_carries_why_it_stopped_and_whether_it_resumed() -> None:
    rows = solver_attempts(STOPPED_EARLY)
    assert [(row["stop_reason"], row["resumed"]) for row in rows] == [
        (None, False),
        ("no_bracket_progress", False),
        ("search_numerical_failure", True),
    ]


def test_the_headline_describes_the_whole_solve() -> None:
    text = solve_stop(STOPPED_EARLY, {"h_low": 0.5, "h_lb": 0.4999998})
    assert text is not None
    assert text.startswith("The search did not meet its gap target (1e-06).")
    assert "relative gap of 4e-07" in text
    assert ("3 attempts ended 1 budget_exhausted, 1 stagnated, 1 numerical_failure"
            in text)
    assert "stopped by search_numerical_failure" in text
    assert ("It used 51 s of its 600 s time limit, stopping well before the "
            "limit") in text
    assert "The iteration cap (max_iterations = 30) ended the fw stage." in text
    assert text.endswith("The record's termination field reads numerical_failure.")


def test_a_met_target_reads_as_met_whatever_the_last_attempt_said() -> None:
    report = copy.deepcopy(STOPPED_EARLY)
    report["attempts"][1]["termination"] = "target_met"
    text = solve_stop(report, {})
    assert text is not None
    assert text.startswith("The search met its gap target")
    assert "stopping before" not in text


def test_no_search_report_gives_no_headline() -> None:
    assert solve_stop(None, {}) is None


def test_the_page_renders_the_stop_detail_and_validates() -> None:
    jsonschema = pytest.importorskip("jsonschema")

    def edit(record: dict[str, Any]) -> None:
        record["payload"]["stages"]["key_rate"]["search_report"] = copy.deepcopy(
            STOPPED_EARLY)

    report = build_report(completed_record(edit=edit))
    jsonschema.validate(report, report_schema())
    text = render_markdown(report, contract_link=default_contract_link())
    assert "How the search stopped, as a whole: The search did not meet" in text
    assert "Why it stopped" in text and "no_bracket_progress" in text
    assert "| yes |" in text


def test_the_alpha_search_marks_set_aside_runs_and_the_refinement_stop() -> None:
    record = json.loads((ROOT / "runs" / "report_examples" / "alpha-search-bb84"
                         / "record.json").read_text(encoding="utf-8"))
    for stage in record["payload"]["composition_flow"]["stages"]:
        for child in stage.get("children") or ():
            if child.get("name") == "alpha" and child["detail"].get("searched"):
                child["detail"]["evaluations"][1]["set_aside"] = "wide bracket: test"
                child["detail"]["refinement_stopped"] = "stopped at alpha 1.01: test"
    report = build_report(record)
    search = report["sections"]["numerics"]["alpha_search"]
    assert search is not None
    assert search["refinement_stopped"] == "stopped at alpha 1.01: test"
    assert [row["set_aside"] for row in search["evaluations"]][:2] == [
        None, "wide bracket: test"]
    text = render_markdown(report, contract_link=default_contract_link())
    assert "wide bracket: test" in text and "stopped at alpha 1.01: test" in text
