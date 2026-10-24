"""runs.bbm92_study.numbers on the committed study data.

The numbers it prints are what the whitepaper's prose is compared with, so
each must agree with the artefact a reader would check it against: the key
length and rate with the summary, the premise count with the rendered headline
report, and the ladder with the summary's rungs.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest
from runs.bbm92_study.numbers import DEFAULT_HEADLINE, numbers

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "runs" / "bbm92_study" / "data"

pytestmark = pytest.mark.skipif(not (DATA / "loss" / "summary.csv").is_file(),
                                reason="the study data is not in this tree")


@pytest.fixture(scope="module")
def result() -> dict:
    return numbers(DATA, DEFAULT_HEADLINE)


def test_headline_matches_summary(result: dict) -> None:
    head = result["headline"]
    with (DATA / "loss" / "summary.csv").open(encoding="utf-8", newline="") as handle:
        row = next(r for r in csv.DictReader(handle)
                   if r["point"] == "realistic-c1e6-L10")
    assert head["key_length"] == int(row["key_length"])
    assert head["rate_per_round"] == pytest.approx(float(row["rate_per_round"]))
    assert 0 < head["premises_security"] <= head["premises"]


def test_premises_match_rendered_report(result: dict) -> None:
    text = (DATA / "headline-report" / "report.md").read_text(encoding="utf-8")
    match = re.search(r"\*\*(\d+) premises\*\*", text)
    assert match is not None
    assert result["headline"]["premises"] == int(match.group(1))


def test_ladder_has_every_rung(result: dict) -> None:
    rates = result["ladder"]["rate_per_round"]
    assert set(rates) == {"c3e4", "c1e5", "c1e6", "n1e10"}
    assert all(len(rungs) == 8 for rungs in rates.values())
    assert result["engine"]["any_dirty"] is False
