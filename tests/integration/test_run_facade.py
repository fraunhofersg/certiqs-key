"""The run facade (``runs/facade``): refusals as data, a job to a record and report.

The facade decides nothing of its own, so these tests hold it to passing the
engine's decisions through: the engine's reason codes for a refused input, a
preparation that is the engine's ``preparation_record``, and a background job
whose record and report are the ones ``record_run`` and ``build_report``
produce. The run test uses a five-iteration cap; its key length is not
asserted, because it pins nothing (``runs/report_examples`` README).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest
from runs.facade import core, jobs


@pytest.fixture
def jobs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv(jobs.JOBS_ENV, str(tmp_path / "jobs"))
    return tmp_path / "jobs"


def test_every_instance_is_listed_and_described() -> None:
    listed = [entry["id"] for entry in core.list_instances()]
    assert listed == [s.DESCRIPTOR.id for s in __import__("instances").discover()]
    for instance in listed:
        described = core.describe_instance(instance)
        assert described["instance"]["id"] == instance
        assert core.read_config(instance, described["default_config"]) is not None


@pytest.mark.parametrize(
    ("instance", "change", "reason"),
    [
        ("nope", {}, "unknown_instance"),
        ("bb84", {"model": {"qbr": "0"}}, "unknown_parameter"),
        ("bb84", {"model": {"qber": "2"}}, "outside_domain"),
        ("bb84", {"declared_tolerance": None}, "declared_tolerance_absent"),
    ],
)
def test_a_refused_input_carries_the_engines_reason(
    instance: str, change: dict[str, Any], reason: str
) -> None:
    config = {**core.describe_instance("bb84")["default_config"], **change}
    refused = core.prepare(instance, config)
    assert refused["refused"] is True
    assert refused["stage"] == core.INPUT_STAGE
    assert refused["reason"] == reason


@pytest.mark.parametrize(
    "name",
    [
        "certify_snaps",
        "certified_weight_ceiling",
        "strict_certification",
        "contradiction_share",
    ],
)
def test_a_retired_parameter_is_refused_with_its_code(name: str) -> None:
    """A retired parameter is refused with its code through the facade too."""
    config = core.describe_instance("bb84")["default_config"]
    config = {**config, "parameters": {**config["parameters"], name: True}}
    refused = core.prepare("bb84", config)
    assert refused["refused"] is True
    assert refused["stage"] == core.INPUT_STAGE
    assert refused["reason"] == "retired_parameter"
    assert name in refused["detail"]


def _untimed(value: Any) -> Any:
    """Drop wall times, the one part of a preparation that differs between calls."""
    if isinstance(value, dict):
        return {k: _untimed(v) for k, v in value.items() if k != "wall_time_s"}
    if isinstance(value, list):
        return [_untimed(v) for v in value]
    return value


@pytest.mark.parametrize("instance", ["bb84", "optical_bb84", "bbm92"])
def test_preparation_is_the_engines_record_in_an_envelope(instance: str) -> None:
    from certiqs_key.runs import preparation_record

    s = core.surface(instance)
    config = s.default_config()
    envelope = core.prepare(instance, config.to_payload())
    assert envelope["kind"] == "preparation"
    assert envelope["config_digest"] == config.digest()
    assert _untimed(envelope["preparation"]) == _untimed(
        json.loads(json.dumps(preparation_record(s.preparation(config))))
    )
    summary = core.preparation_summary(envelope)
    assert (
        summary["acceptance_alphabet"] == envelope["preparation"]["acceptance_alphabet"]
    )
    assert len(json.dumps(summary)) < 60_000


def test_an_honest_override_is_checked_and_named() -> None:
    malformed = core.honest_override({"table": {"ok": "1"}}, "bb84")
    assert isinstance(malformed, dict)
    assert malformed["reason"] == "honest_override_malformed"
    checked = core.honest_override(
        {"table": {"ok": "1"}, "source": "lab counts"}, "bb84"
    )
    assert not isinstance(checked, dict)
    provider, note = checked
    assert provider is not None and note is not None
    assert note["overridden"] is True and note["source"] == "lab counts"
    config = core.describe_instance("bb84")["default_config"]
    envelope = core.prepare("bb84", config, {"table": {"ok": "1"}, "source": "lab"})
    assert envelope["honest_override_labels"]["missing"] == ["disc", "err", "gen"]


def test_a_refused_request_costs_no_job(jobs_dir: Path) -> None:
    refused = jobs.start_run("bb84", {"rounds": 0})
    assert refused["refused"] is True
    assert not any(jobs.jobs_root().iterdir())


def _wait(job: str, seconds: float = 300.0) -> dict[str, Any]:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        status = jobs.job_status(job)
        if status["state"] in jobs.FINAL_STATES:
            return status
        time.sleep(1.0)
    raise AssertionError(f"job {job} did not finish in {seconds} s")


@pytest.mark.requires_qics
def test_a_job_runs_to_a_record_and_its_report(jobs_dir: Path) -> None:
    from certiqs_key.runs.report import build_report

    config = core.describe_instance("bb84")["default_config"]
    config["solver"] = {"max_iterations": 5}
    started = jobs.start_run("bb84", config)
    assert started["reused"] is False
    status = _wait(started["job"])
    assert status["state"] == "done", status
    directory = Path(status["directory"])
    record = json.loads((directory / "record.json").read_text(encoding="utf-8"))
    assert record["payload"]["config"]["config_digest"] == status["config_digest"]
    assert core.read_report(directory) == json.loads(json.dumps(build_report(record)))
    assert status["key_length"] == record["payload"]["stages"]["key_rate"]["key_length"]
    again = jobs.start_run("bb84", config)
    if core.engine_identity()["dirty"]:
        # a dirty tree may have changed code between the two: never reused
        assert again["job"] != started["job"] and again["reused"] is False
        _wait(again["job"])
    else:
        assert again["job"] == started["job"] and again["reused"] is True
    report = core.read_report(directory)
    summary = core.report_summary(report)
    assert summary["assumptions_to_vouch_for"]
    # Each assumption has its plain statement; each item the shipped template
    # declared itself (bb84's Band-A POVM) its text: the user vouches for both.
    for entry in summary["assumptions_to_vouch_for"]:
        assert entry["text"] if entry.get("user_declared") else entry["user_statement"]
    declared = report["sections"]["result"]["user_declared"]
    assert [item["kind"] for item in declared] == ["receiver_povm"]
    assert report["sections"]["assumptions"]["user_declared"] == declared
    assert [
        entry["kind"]
        for entry in summary["assumptions_to_vouch_for"]
        if entry.get("user_declared")
    ] == ["receiver_povm"]


@pytest.mark.requires_qics
def test_a_cancelled_job_ends_cancelled_without_a_record(jobs_dir: Path) -> None:
    config = core.describe_instance("decoy_bb84")["default_config"]
    started = jobs.start_run("decoy_bb84", config, reuse=False)
    time.sleep(3.0)
    status = jobs.cancel_job(started["job"])
    if status["state"] not in jobs.FINAL_STATES:
        status = _wait(started["job"], 60.0)
    if status["state"] == "done":
        pytest.skip("the run finished before the cancel reached it")
    assert status["state"] == "cancelled"
    assert "record.json" not in status["files"]


# --- job and request hygiene, one test each


def test_a_status_being_replaced_is_never_read_as_lost(jobs_dir: Path) -> None:
    """Windows locks a file being replaced; a reader retries."""
    import threading

    directory = jobs_dir / "bb84-000000000000-1"
    directory.mkdir(parents=True)
    core.write_json_atomic(directory / "request.json", {"created": time.time()})
    core.write_json_atomic(
        directory / "status.json", {"state": "running", "heartbeat": time.time()}
    )
    stop = threading.Event()
    failures: list[BaseException] = []

    def writer() -> None:
        try:
            while not stop.is_set():
                core.write_json_atomic(
                    directory / "status.json",
                    {"state": "running", "heartbeat": time.time()},
                )
        except BaseException as error:
            failures.append(error)

    thread = threading.Thread(target=writer)
    thread.start()
    try:
        states = {jobs._state(directory)["state"] for _ in range(400)}
    finally:
        stop.set()
        thread.join()
    assert not failures
    assert "lost" not in states
    assert states <= {"running", "unknown"}
    assert not list(directory.glob("*.partial"))


@pytest.mark.parametrize(
    "job", ["E:foo", "../x", "..", "bb84-abc-1", "C:/Windows", "bb84-000000000000-1/.."]
)
def test_a_job_id_never_becomes_a_path_outside_the_jobs(
    jobs_dir: Path, job: str
) -> None:
    """A job id is a name inside the jobs folder, never a path."""
    with pytest.raises(KeyError):
        jobs.job_directory(job)


@pytest.mark.parametrize(
    "name",
    [
        "../optical_bb84/README.md",
        "../../README.md",
        str(core.repo_root() / "AGENTS.md"),
    ],
)
def test_a_document_name_never_leaves_the_instance_folder(name: str) -> None:
    """A document name is a name inside the instance folder, never a path."""
    with pytest.raises(KeyError):
        core.instance_document("bb84", name)
    assert core.instance_document("bb84")["name"] == "README.md"


def test_an_honest_probability_must_be_an_exact_string() -> None:
    """0.1 as a JSON number is not 1/10."""
    for value in (0.1, 1, True):
        refused = core.honest_override(
            {"table": {"ok": value}, "source": "lab"}, "bb84"
        )
        assert isinstance(refused, dict)
        assert refused["reason"] == "honest_override_malformed"
    checked = core.honest_override({"table": {"ok": "0.1"}, "source": "lab"}, "bb84")
    assert not isinstance(checked, dict)
    _provider, note = checked
    assert note is not None and len(note["digest"]) == 64


def test_every_snap_source_is_summarised() -> None:
    """Per-station snaps (bbm92) and the input preparation.

    A station's snap is its measurement-family snap, one record per setting
    with a record per block (``measurement_snaps``), and the summary has one
    entry per block, with the run's certification settings and whether some
    block rests on A-SNAP. Before the reduction runs, only the instance's own
    record is known, which cannot say whether a positive certified weight is
    carried; the key is named for what it reads, and such blocks are listed as
    pending the domination record.
    """
    envelope = core.prepare("bbm92", core.describe_instance("bbm92")["default_config"])
    summary = core.preparation_summary(envelope)
    adaptation = envelope["preparation"]["rows_adaptation"]
    expected = sum(
        len(snap["blocks"])
        for station in adaptation["stations"]
        for snap in station["measurement_snaps"]
    )
    assert expected > 0
    assert summary["snaps"]["count"] == expected
    assert {snap["station"] for snap in summary["snaps"]["entries"]} - {None}
    assert summary["snaps"]["snap_settings"] == {
        "reference_enclosure": True,
        "strict_snaps": False,
    }
    assert summary["snaps"]["rests_on_a_snap_by_the_instance_record"] is False
    assert summary["snaps"]["moved_blocks_pending_the_run"] == []
    assert summary["input_preparation"]
    assert len(json.dumps(summary)) < 60_000


def test_an_override_is_the_distribution_shown() -> None:
    """Under an override the instance's own model is not shown."""
    table = {"gen": "1/4", "ok": "1/4", "err": "0", "disc": "1/2"}
    config = core.describe_instance("bb84")["default_config"]
    envelope = core.prepare("bb84", config, {"table": table, "source": "lab"})
    summary = core.preparation_summary(envelope)
    assert summary["honest_model"].startswith("REPLACED")
    assert summary["honest_distribution_approx"] == {
        "gen": "0.25",
        "ok": "0.25",
        "err": "0",
        "disc": "0.5",
    }
    assert summary["honest_override_labels"] == {"missing": [], "unknown": []}


def test_the_report_summary_keeps_what_the_user_must_see() -> None:
    """On the committed bb84 and optical_bb84 examples."""
    from certiqs_key.runs.report import build_report

    for instance in ("bb84", "optical_bb84"):
        record = json.loads(
            (
                core.repo_root() / "runs" / "report_examples" / instance / "record.json"
            ).read_text(encoding="utf-8")
        )
        report = json.loads(json.dumps(build_report(record)))
        summary = core.report_summary(report)
        result = report["sections"]["result"]
        assert summary["result"]["not_counted"] == result["not_counted"]
        assert summary["result"]["key_length_reason"] == result["key_length_reason"]
        assert all("summary" in row for row in summary["result"]["limitations"])
        vouch = summary["assumptions_to_vouch_for"]
        # A shipped template's own declarations (bb84's receiver POVM) are
        # listed too, by kind and label rather than by a ledger short id.
        declared = [entry for entry in vouch if entry.get("user_declared")]
        assert [(e["kind"], e["label"]) for e in declared] == [
            (item["kind"], item["label"]) for item in result["user_declared"]
        ]
        by_id = {entry["short_id"]: entry for entry in vouch if "short_id" in entry}
        assert len(by_id) + len(declared) == len(vouch)
        for entry in report["sections"]["numerics"]["entries"]:
            assert by_id[entry["short_id"]]["engine_numerics"] is True
        for group in report["sections"]["assumptions"]["groups"]:
            for family in group["families"]:
                for entry in (family["head"], *family["members"]):
                    shown = by_id[entry["short_id"]]
                    assert shown["category"] == entry["category"]
                    assert shown["refines"] == entry["refines"]


def test_a_dirty_attempt_is_never_reused(jobs_dir: Path) -> None:
    """An attempt that is dirty or of unknown state is not reused."""
    for dirty, reusable in ((True, False), (None, False), (False, True)):
        directory = jobs_dir / f"bb84-{'0' * 12}-{len(list(jobs_dir.glob('*'))) + 1}"
        directory.mkdir(parents=True)
        now = time.time()
        core.write_json_atomic(
            directory / "request.json",
            {"instance": "bb84", "engine": {"dirty": dirty}, "created": now},
        )
        core.write_json_atomic(
            directory / "status.json", {"state": "done", "heartbeat": now}
        )
        assert (jobs._reusable(directory) is not None) is reusable


def test_a_refusal_at_preparation_costs_no_worker(jobs_dir: Path) -> None:
    """The basis weights of a side must sum to one."""
    config = core.describe_instance("bb84")["default_config"]
    config["device"] = {**config["device"], "alice_x": "1/3"}
    refused = jobs.start_run("bb84", config)
    assert refused["refused"] is True
    assert not [path for path in jobs.jobs_root().iterdir() if path.is_dir()]


@pytest.mark.requires_qics
def test_a_run_with_an_honest_override_records_and_reports_it(jobs_dir: Path) -> None:
    table = {"gen": "1/4", "ok": "1/4", "err": "0", "disc": "1/2"}
    config = core.describe_instance("bb84")["default_config"]
    config["solver"] = {"max_iterations": 5}
    started = jobs.start_run("bb84", config, {"table": table, "source": "lab counts"})
    status = _wait(started["job"])
    assert status["state"] == "done", status
    directory = Path(status["directory"])
    record = json.loads((directory / "record.json").read_text(encoding="utf-8"))
    note = record["payload"]["honest_model_note"]
    assert note["overridden"] is True and note["source"] == "lab counts"
    stage = record["payload"]["stages"]["acceptance_construction"]
    assert stage["honest_distribution"] == table
    summary = core.report_summary(core.read_report(directory))
    assert summary["honest_model"]["source"] == "lab counts"
