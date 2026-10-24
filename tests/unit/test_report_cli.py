"""``python -m certiqs_key.runs.report``: one record, a sweep, the formats, refusals.

The formats are json, md and html; a directory
renders as a sweep; ``.json.gz`` is accepted; an old record exits 2 with its
reason. The closure table is the synthetic one (the CLI reads the shipped
table through the builder, which these tests point at the fixture).
"""

from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from tests.support.report_records import (
    completed_record,
    refused_record,
    synthetic_table,
)

from certiqs_key.runs.report import build as build_module
from certiqs_key.runs.report.__main__ import main

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def table(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build_module, "closure_table", synthetic_table)


def write(path: Path, record: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("form", "start"),
    [("json", "{"), ("md", "# Key-rate report"), ("html", "<!DOCTYPE html>")],
)
def test_one_record_in_each_format(tmp_path: Path, form: str, start: str) -> None:
    record = write(tmp_path / "record.json", completed_record())
    out = tmp_path / f"report.{form}"
    assert main([str(record), "--format", form, "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.startswith(start)
    if form == "json":
        assert json.loads(text)["kind"] == "key-rate-report"


def test_markdown_goes_to_standard_output_by_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    record = write(tmp_path / "record.json", completed_record())
    assert main([str(record)]) == 0
    assert capsys.readouterr().out.startswith("# Key-rate report")


def test_a_gzipped_record_is_read(tmp_path: Path) -> None:
    path = tmp_path / "record.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(completed_record(), handle)
    out = tmp_path / "report.json"
    assert main([str(path), "--format", "json", "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["kind"] == "key-rate-report"


def test_a_directory_renders_as_a_sweep_with_its_points(tmp_path: Path) -> None:
    records = tmp_path / "records"
    write(records / "run-0001.json", completed_record(qber="1/25"))
    write(records / "run-0000.json", completed_record(qber="1/50"))
    write(records / "run-0002.json", refused_record())
    (records / "notes.txt").write_text("not a record", encoding="utf-8")
    out = tmp_path / "out"
    assert main([str(records), "--format", "md", "--out", str(out)]) == 0
    sweep = (out / "sweep.md").read_text(encoding="utf-8")
    assert sweep.startswith("# Key-rate sweep report")
    assert "](points/0000.md)" in sweep
    for index in range(3):
        assert (out / "points" / f"{index:04d}.md").exists()
    # Records are ordered by file name: point 0 is run-0000 (qber 1/50).
    assert "| 0 | — | 0.02 |" in sweep
    assert "| 1 | — | 0.04 |" in sweep
    # A point's report sits one folder down: its contract links step up once.
    point = (out / "points" / "0000.md").read_text(encoding="utf-8")
    assert "](../spec/modules/meat-core/contract.pdf#nameddest=" in point


def test_a_sweep_in_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    first = write(tmp_path / "a.json", completed_record())
    second = write(tmp_path / "b.json", completed_record(qber="1/25"))
    assert main([str(first), str(second), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["kind"] == "key-rate-sweep-report"


def test_an_old_record_exits_2_with_its_reason(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    record = completed_record()
    record["schema_version"] = "0.19.0"
    path = write(tmp_path / "record.json", record)
    assert main([str(path)]) == 2
    assert "record_schema_version" in capsys.readouterr().err


def test_an_unreadable_record_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "record.json"
    path.write_text("{not json", encoding="utf-8")
    assert main([str(path)]) == 2
    assert "unreadable_record" in capsys.readouterr().err


def test_mixed_instances_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first = write(tmp_path / "a.json", completed_record())
    second = write(tmp_path / "b.json", completed_record(instance_id="decoy_bb84"))
    assert main([str(first), str(second)]) == 2
    assert "mixed_instances" in capsys.readouterr().err


def test_the_module_entry_point(tmp_path: Path) -> None:
    """``python -m`` reaches main; an old record is refused before any table read."""
    record = completed_record()
    record["schema_version"] = "0.19.0"
    path = write(tmp_path / "record.json", record)
    done = subprocess.run(
        [sys.executable, "-m", "certiqs_key.runs.report", str(path)],
        capture_output=True, text=True, cwd=ROOT, check=False,
    )
    assert done.returncode == 2
    assert "record_schema_version" in done.stderr


def test_a_truncated_record_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    record = completed_record()
    del record["payload"]["config"]
    path = write(tmp_path / "record.json", record)
    assert main([str(path)]) == 2
    assert "not_a_run_record" in capsys.readouterr().err


def test_a_corrupted_gzip_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = bytearray(gzip.compress(json.dumps(completed_record()).encode("utf-8")))
    data[len(data) // 2:len(data) // 2 + 16] = b"\xff" * 16
    path = tmp_path / "record.json.gz"
    path.write_bytes(bytes(data))
    assert main([str(path)]) == 2
    assert "unreadable_record" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("base", "absolute"),
    [("", False), ("contracts/", False), ("../engine/", False),
     ("https://engine.example/", True), ("file:///C:/repo/", True),
     ("/srv/engine/", True), ("C:/repo/", True), ("C:\\repo\\", True)],
)
def test_which_contract_bases_are_absolute(base: str, absolute: bool) -> None:
    from certiqs_key.runs.report.__main__ import _absolute

    assert _absolute(base) is absolute


def test_a_windows_drive_base_is_not_stepped_up_for_points(tmp_path: Path) -> None:
    write(tmp_path / "in" / "a.json", completed_record())
    write(tmp_path / "in" / "b.json", completed_record(qber="1/25"))
    out = tmp_path / "out"
    assert main([str(tmp_path / "in"), "--out", str(out),
                 "--contract-base", "C:/repo/"]) == 0
    point = (out / "points" / "0000.md").read_text(encoding="utf-8")
    assert "](C:/repo/spec/modules/" in point
    assert "../C:" not in point
