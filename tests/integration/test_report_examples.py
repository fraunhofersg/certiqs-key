"""SNAPSHOTS, NOT ORACLES: the committed report examples render as committed.

A snapshot proves that the rendering is deterministic and that a change to it
was seen, not that it is right. Correctness of the report is held by the
hand-written expectations of ``tests/unit/test_report_build.py``,
``test_report_checks.py``, ``test_sweep_report.py`` and
``test_report_render.py`` and by the reconciliation tests of the route-exact
assumption set; the key lengths in the examples are whatever the engine
computed at the commit each record names, and pin nothing.

WHY THIS EXISTS. The report is built from the record and the shipped
claim-closure table and rendered by two writers; a change to any of them
changes what a reader is shown. Here every committed record under
``runs/report_examples/`` is re-rendered with the current code (never
re-solved: no QICS, a few seconds) and compared byte for byte with the
committed rendering, so that change shows up as a snapshot diff the reviewer
reads. When it is intended, regenerate::

    python -m runs.report_examples.generate --render-only

(``runs/report_examples/README.md``), and commit the diff with its reason.
A snapshot diff that moves a number with no engine change is a defect.

Also checked on the real records: the schema versions and both schemas, no
reconciliation discrepancy, every record pointer the report carries resolves,
the gzip rule and the 1 MB budget per committed file.
"""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path
from typing import Any

import pytest
from runs.report_examples.generate import (
    CONTRACT_BASE,
    EXAMPLES,
    EXAMPLES_ROOT,
    GZIP_ABOVE,
    Example,
    committed_files,
    read_record,
    record_paths,
    rendered,
)

import certiqs_key.runs as runs_package
from certiqs_key.runs.record import RECORD_SCHEMA_VERSION
from certiqs_key.runs.report import build_report, build_sweep_report, report_schema
from certiqs_key.runs.report.__main__ import main as report_cli
from certiqs_key.runs.report.inputs import resolve_pointer
from certiqs_key.runs.report.model import KeyRateReport, group_entries

#: The design's budget for any one committed example file.
SIZE_BUDGET = 1024 * 1024

REGENERATE = (
    "regenerate with `python -m runs.report_examples.generate --render-only` "
    "and read the snapshot diff before committing it"
)

_IDS = [example.name for example in EXAMPLES]


def _records(example: Example) -> list[dict[str, Any]]:
    return [read_record(path) for path in record_paths(example)]


def _record_schema() -> dict[str, Any]:
    path = Path(runs_package.__file__).resolve().parent / "record.schema.json"
    schema: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return schema


def test_the_generator_refuses_a_key_length_example_with_a_zero_key() -> None:
    """A ``key-length`` example stands for a positive key.

    The outcome reads only whether a key length is reported, so a run whose
    bound clamped to a key of 0 came out as a ``key-length`` example (the bbm92
    template at five iterations on the receiver's rigorous weight).
    """
    from runs.report_examples.generate import _refusal_to_write

    example = next(e for e in EXAMPLES if e.name == "bbm92")
    positive = [{"outcome": "key-length", "key_length": 7}]
    assert _refusal_to_write(example, positive) is None
    zero = _refusal_to_write(example, [{"outcome": "key-length", "key_length": 0}])
    assert zero is not None and "key length of 0" in zero
    other = _refusal_to_write(example, [{"outcome": "refused", "key_length": None}])
    assert other is not None and "came out" in other


def test_every_example_folder_is_one_the_generator_declares() -> None:
    folders = {
        path.name for path in EXAMPLES_ROOT.iterdir()
        if path.is_dir() and path.name != "__pycache__"
    }
    assert folders == {example.name for example in EXAMPLES}
    assert (EXAMPLES_ROOT / "README.md").is_file()


@pytest.mark.parametrize("example", EXAMPLES, ids=_IDS)
def test_the_committed_rendering_is_the_current_one(example: Example) -> None:
    expected = rendered(example)
    folder = EXAMPLES_ROOT / example.name
    differing = sorted(
        name for name, content in expected.items()
        if not (folder / name).is_file() or (folder / name).read_bytes() != content
    )
    assert differing == [], f"{example.name}: {differing} differ; {REGENERATE}"
    records = {path.name for path in record_paths(example)}
    assert committed_files(example) - set(expected) - records == set(), (
        f"{example.name}: files the generator does not write; {REGENERATE}"
    )


@pytest.mark.parametrize("example", EXAMPLES, ids=_IDS)
def test_records_are_of_the_current_schema_and_validate(example: Example) -> None:
    """A schema bump forces a regeneration (the report reads one version)."""
    jsonschema = pytest.importorskip("jsonschema")
    records = _records(example)
    assert len(records) == len(example.outcomes)
    schema = _record_schema()
    for record in records:
        assert record["schema_version"] == RECORD_SCHEMA_VERSION, (
            "re-run `python -m runs.report_examples.generate` after a record "
            "schema bump"
        )
        jsonschema.validate(record, schema)


@pytest.mark.parametrize("example", EXAMPLES, ids=_IDS)
def test_reports_validate_against_the_report_schema(example: Example) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    records = _records(example)
    reports: list[Any] = [build_report(record) for record in records]
    if example.kind == "sweep":
        reports.append(build_sweep_report(records))
    for report in reports:
        jsonschema.validate(report, report_schema())


@pytest.mark.parametrize("example", EXAMPLES, ids=_IDS)
def test_each_record_has_the_outcome_its_example_stands_for(example: Example) -> None:
    results = [
        build_report(record)["sections"]["result"] for record in _records(example)
    ]
    assert tuple(result["outcome"] for result in results) == example.outcomes
    # A key-length example stands for a positive key: the outcome alone cannot
    # see a key length of 0.
    for result in results:
        if result["outcome"] == "key-length":
            assert result["key_length"], f"{example.name}: a key length of 0"


@pytest.mark.parametrize("example", EXAMPLES, ids=_IDS)
def test_every_record_names_the_engine_commit_that_wrote_it(example: Example) -> None:
    """Generated from a checkout, and the README names that commit."""
    readme = (EXAMPLES_ROOT / "README.md").read_text(encoding="utf-8")
    for record in _records(example):
        engine = record["payload"]["provenance"]["engine"]
        assert re.fullmatch(r"[0-9a-f]{40}", str(engine["git_commit"])), engine
        assert isinstance(engine["git_dirty"], bool)
        assert engine["git_commit"] in readme, (
            "runs/report_examples/README.md names another engine commit; "
            "update its 'Which engine wrote them' section"
        )


@pytest.mark.parametrize("example", EXAMPLES, ids=_IDS)
def test_no_reconciliation_discrepancy(example: Example) -> None:
    """The route-exact set and the closures agree on every real route."""
    for record in _records(example):
        manifest = record["payload"].get("assumption_manifest")
        if manifest is None:
            assert record["payload"]["refused"]
            continue
        assert manifest["discrepancies"] == []


def _pointers(report: KeyRateReport) -> list[str]:
    sections = report["sections"]
    entries = [
        *group_entries(sections["assumptions"]["groups"]),
        *sections["numerics"]["entries"],
        *sections["checks"]["decided_rows"],
    ]
    pointers = [
        str(binding["pointer"])
        for entry in entries
        for binding in entry["bindings"]
        if binding.get("pointer")
    ]
    pointers += [
        str(row["pointer"]) for row in sections["protocol"]["inputs"]
        if row.get("pointer")
    ]
    return pointers


@pytest.mark.parametrize("example", EXAMPLES, ids=_IDS)
def test_every_record_pointer_of_the_report_resolves(example: Example) -> None:
    for record in _records(example):
        pointers = _pointers(build_report(record))
        if not record["payload"].get("refused"):
            assert pointers, "a completed record's report points into it"
        for pointer in pointers:
            resolve_pointer(record, pointer)


@pytest.mark.parametrize("example", EXAMPLES, ids=_IDS)
def test_records_follow_the_gzip_rule_and_every_file_fits_the_budget(
    example: Example,
) -> None:
    for path in record_paths(example):
        if path.name.endswith(".gz"):
            with gzip.open(path, "rb") as handle:
                assert len(handle.read()) > GZIP_ABOVE, path.name
        else:
            assert path.stat().st_size <= GZIP_ABOVE, path.name
    folder = EXAMPLES_ROOT / example.name
    oversized = [
        name for name in committed_files(example)
        if (folder / name).stat().st_size > SIZE_BUDGET
    ]
    assert oversized == []


def test_the_sweep_exercises_a_refused_point_and_its_marks() -> None:
    (example,) = [example for example in EXAMPLES if example.kind == "sweep"]
    sweep = build_sweep_report(_records(example))
    assert "refused" in [point["outcome"] for point in sweep["points"]]
    assert any(flag.get("points") == "all" for flag in sweep["common"]["not_counted"])
    assert "all completed points" in rendered(example)["sweep.md"].decode("utf-8")


@pytest.mark.parametrize("form", ["md", "html"])
def test_the_report_cli_writes_the_committed_files(form: str, tmp_path: Path) -> None:
    """The README's hand command gives the same bytes as the generator.

    The report and its record excerpts alike (report 0.7.0).
    """
    (run,) = [example for example in EXAMPLES if example.name == "bb84"]
    (record,) = record_paths(run)
    out = tmp_path / f"report.{form}"
    # The HTML is the page the Pages site serves (generate.py).
    site = ["--pages-site"] if form == "html" else []
    assert report_cli([str(record), "--format", form, "--out", str(out),
                       "--contract-base", CONTRACT_BASE,
                       "--repo-base", CONTRACT_BASE, *site]) == 0
    expected_run = {
        name: content for name, content in rendered(run).items()
        if name.endswith(f".{form}")
    }
    written_run = {
        path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()
    }
    assert written_run == expected_run

    (sweep,) = [example for example in EXAMPLES if example.kind == "sweep"]
    folder = tmp_path / "sweep"
    assert report_cli([*(str(path) for path in record_paths(sweep)), "--format", form,
                       "--out", str(folder), "--contract-base", CONTRACT_BASE,
                       "--repo-base", CONTRACT_BASE, *site]) == 0
    expected = {
        name: content for name, content in rendered(sweep).items()
        if name.endswith(f".{form}")
    }
    written = {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in folder.rglob("*") if path.is_file()
    }
    assert written == expected
