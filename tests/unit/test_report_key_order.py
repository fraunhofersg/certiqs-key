"""A run's report does not depend on the key order of its record's mappings.

The job worker builds the report from the record it holds in memory, whose
mappings keep their insertion order; a reader builds it from ``record.json``,
written with sorted keys. The two reports must be equal
(``tests/integration/test_run_facade.py``). Equality of the built reports is
checked, and also of their JSON written in order (``sort_keys=False``), so a
mapping copied into the report in a different order is caught too.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

import pytest

from certiqs_key.runs.report import build_report

ROOT = Path(__file__).resolve().parents[2]
#: A realistic run's record beside the report examples. It lives with the
#: dated analyses, which do not ship, so it is read only where it exists.
READABILITY_RECORD = (
    ROOT / "reports" / "2026-10-07-key-rate-report-readability-review" / "run"
    / "record.json.gz"
)
RECORDS = sorted(
    [
        *(ROOT / "runs" / "report_examples").glob("*/record.json"),
        *(ROOT / "runs" / "report_examples").glob("*/record.json.gz"),
        *([READABILITY_RECORD] if READABILITY_RECORD.exists() else []),
    ]
)


def _load(path: Path) -> dict[str, Any]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            data: dict[str, Any] = json.load(handle)
            return data
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def _reversed(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _reversed(value[key]) for key in reversed(list(value))}
    if isinstance(value, list):
        return [_reversed(item) for item in value]
    return value


@pytest.mark.parametrize(
    "path", [path for path in RECORDS if path.is_file()],
    ids=lambda path: path.parent.name,
)
def test_the_report_is_the_same_whatever_the_key_order(path: Path) -> None:
    record = _load(path)
    report = build_report(record)
    written = json.dumps(report, ensure_ascii=False)
    for other in (json.loads(json.dumps(record, sort_keys=True)), _reversed(record)):
        again = build_report(other)
        assert again == report
        assert json.dumps(again, ensure_ascii=False) == written
