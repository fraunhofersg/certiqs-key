"""A preparation's expected runtime, stated before it runs; past a budget, a job.

A long expected runtime, with its reason, is transparent to any user: every
preparation is estimated from its configuration before it runs
(``runs/facade/estimate.py``), the estimate and its reason are in every
reply about it, and a preparation expected past the budget
(``$CERTIQS_KEY_PREPARE_BUDGET_S``) runs in the background as a preparation
job whose summary is the synchronous one. A budget of 0 s stands in for a
slow configuration here, so no test waits for a slow preparation.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import anyio
import pytest
from runs.facade import core, estimate, jobs, worker
from tests.support.declared_documents import bb84_tree, y_basis


@pytest.fixture(autouse=True)
def default_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test starts at the default budget; a test lowers it itself."""
    monkeypatch.delenv(estimate.BUDGET_ENV, raising=False)


@pytest.fixture
def jobs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv(jobs.JOBS_ENV, str(tmp_path / "jobs"))
    monkeypatch.setenv(jobs.MAX_JOBS_ENV, "50")
    return tmp_path / "jobs"


@pytest.fixture
def clean_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    """Report a clean engine identity, so that an identical request is reused."""
    identity = core.engine_identity()
    monkeypatch.setattr(
        core,
        "engine_identity",
        lambda: {**identity, "commit": "c" * 40, "dirty": False},
    )


def _no_worker(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    spawned: list[Path] = []

    def spawn(directory: Path) -> Any:
        spawned.append(directory)
        return SimpleNamespace(poll=lambda: 0)

    monkeypatch.setattr(jobs, "_spawn", spawn)
    return spawned


def _request(ports: int, cutoff: int, window: int, modes: int = 2) -> Any:
    """Return a stand-in receiver request: the five fields the estimate reads."""
    return SimpleNamespace(
        port_map=SimpleNamespace(entries=tuple((f"p{i}", (i,)) for i in range(ports))),
        input_modes=SimpleNamespace(channel=tuple(range(modes)), source=()),
        photon_cutoff=cutoff,
        exact_window={"off": window},
        tail_window={},
    )


def _surface(*requests: Any) -> Any:
    return SimpleNamespace(receiver_requests=lambda config: requests)


def _estimate(*requests: Any) -> dict[str, Any]:
    return estimate.estimate_preparation(_surface(*requests), None)


def _seconds(*requests: Any) -> float:
    seconds = _estimate(*requests)["expected_seconds"]
    assert isinstance(seconds, float)
    return seconds


def _optical(**device: int) -> Any:
    from instances.optical_bb84 import surface

    return surface, surface.default_config(
        device={**dict(surface.default_config().device), **device}
    )


# ---------------------------------------------------------------------------
#  The estimate
# ---------------------------------------------------------------------------


def test_the_estimate_grows_with_the_cutoff_the_window_and_the_ports() -> None:
    by_cutoff = [_seconds(_request(4, n, n + 1)) for n in range(1, 17)]
    assert by_cutoff == sorted(by_cutoff) and by_cutoff[-1] > by_cutoff[0]
    by_window = [_seconds(_request(4, 1, m)) for m in range(2, 18)]
    assert by_window == sorted(by_window) and by_window[-1] > by_window[0]
    by_ports = [_seconds(_request(k, 3, 4)) for k in range(1, 11)]
    assert by_ports == sorted(by_ports) and by_ports[-1] > by_ports[0]
    one = _seconds(_request(4, 3, 4))
    assert _seconds(_request(4, 3, 4), _request(4, 3, 4)) > 2 * one


def test_past_the_measured_range_the_estimate_says_so() -> None:
    """Extrapolated, capped, human units, impractical."""
    inside = _estimate(_request(4, 3, 4))
    assert inside["extrapolated"] is False and inside["capped"] is False
    assert inside["practical"] is True and "advice" not in inside
    assert inside["duration"].endswith(" s")
    beyond = _estimate(_request(4, 12, 13))
    assert beyond["extrapolated"] is True
    assert "extrapolated" in beyond["why"].lower()
    far = _estimate(_request(4, 16, 17))
    assert far["capped"] is True
    assert far["duration"].startswith("more than ")
    assert far["expected_seconds"] == estimate.CAP_SECONDS
    assert far["practical"] is False
    assert "will not finish in practice" in far["advice"]
    assert "smaller photon cutoff or window" in far["advice"]
    assert far["background"] is True  # never refused: run in the background
    assert estimate.statement(far).endswith(far["advice"])


def test_durations_are_written_in_human_units() -> None:
    assert estimate.duration(4.2) == "about 4.2 s"
    assert estimate.duration(150) == "about 2.5 min"
    assert estimate.duration(3 * 3600) == "about 3 h"
    assert estimate.duration(3 * 86400) == "about 3 days"


def test_the_background_decision_keeps_a_safety_margin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Synchronous only while the estimate times the margin fits the budget."""
    monkeypatch.setenv(estimate.BUDGET_ENV, "10")
    for n in range(1, 12):
        value = _estimate(_request(4, n, n + 1))
        seconds = value["expected_seconds"]
        assert value["background"] is (seconds * estimate.SAFETY_FACTOR > 10), value


def test_the_estimate_is_unknown_where_it_cannot_be_read() -> None:
    def refuses(config: Any) -> Any:
        raise ValueError("refused")

    for s in (SimpleNamespace(), SimpleNamespace(receiver_requests=refuses)):
        value = estimate.estimate_preparation(s, None)
        assert value["expected_seconds"] is None
        assert value["background"] is False
        assert value["why"].startswith("unknown")


def test_the_packaged_instances_are_estimated_and_their_extremes_named() -> None:
    """Every default is quick; optical_bb84 at cutoff 10 is minutes, and why."""
    for s in __import__("instances").discover():
        value = estimate.estimate_preparation(s, s.default_config())
        assert value["expected_seconds"] is not None, s.DESCRIPTOR.id
        assert value["background"] is False, s.DESCRIPTOR.id
    surface, config = _optical(photon_cutoff=10, exact_window=11)
    started = time.perf_counter()
    value = estimate.estimate_preparation(surface, config)
    # Cheap: a lowering and some arithmetic, never a preparation (minutes).
    assert time.perf_counter() - started < 30.0
    assert value["expected_seconds"] > 60
    assert value["background"] is True
    assert "photon cutoff 10" in value["why"] and "4 detector ports" in value["why"]
    assert "photon cutoff" in value["why"].split("Mostly driven by")[1]


def test_every_description_names_what_drives_the_runtime() -> None:
    for entry in core.list_instances():
        assert "to prepare at the defaults" in entry["runtime"], entry["id"]
    runtime = core.describe_instance("optical_bb84")["runtime"]
    assert runtime["driven_by"] == ["photon_cutoff", "exact_window"]
    assert core.describe_instance("bb84")["runtime"]["driven_by"] == []
    # Only what the estimate reads: decoy's source and entropy cutoffs are not.
    decoy = core.describe_instance("decoy_bb84")["runtime"]["driven_by"]
    assert decoy == ["photon_cutoff", "exact_window"]
    bbm92 = core.describe_instance("bbm92")["runtime"]["driven_by"]
    assert set(bbm92) == {
        "alice_photon_cutoff",
        "alice_exact_window",
        "bob_photon_cutoff",
        "bob_exact_window",
    }


def test_every_prepare_summary_carries_the_estimate(jobs_dir: Path) -> None:
    envelope = core.prepare(
        "optical_bb84", core.describe_instance("optical_bb84")["default_config"]
    )
    summary = core.preparation_summary(envelope)
    value = summary["estimate"]
    assert value["expected_seconds"] is not None and value["background"] is False
    assert "the receiver: photon cutoff 1" in value["why"]
    assert "not reused by the run" in value["covers"]


# ---------------------------------------------------------------------------
#  Preparation jobs
# ---------------------------------------------------------------------------


def _finish(job: str, seconds: float = 300.0) -> dict[str, Any]:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        status = jobs.job_status(job)
        if status["state"] in jobs.FINAL_STATES:
            return status
        time.sleep(0.5)
    raise AssertionError(f"job {job} did not finish in {seconds} s")


def test_past_the_budget_prepare_is_a_job_whose_summary_is_the_synchronous_one(
    jobs_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A budget of 0 s: every estimate is past it, so prepare goes to a job."""
    pytest.importorskip("mcp")
    from mcp import Client
    from runs.mcp.server import MAX_REPLY_CHARS, build_server

    monkeypatch.setenv(estimate.BUDGET_ENV, "0")
    config = core.describe_instance("optical_bb84")["default_config"]
    tree = bb84_tree()
    del tree["identity"]["readme"], tree["identity"]["record_label"]
    tree["identity"]["id"] = "my_y_bb84"
    y_basis(tree)

    async def session() -> dict[str, Any]:
        async with Client(build_server()) as client:

            async def call(name: str, arguments: dict[str, Any]) -> Any:
                result = await client.call_tool(name, arguments)
                assert not result.is_error, result.content[0].text
                return result.structured_content or json.loads(result.content[0].text)

            replies: dict[str, Any] = {}
            replies["started"] = await call(
                "prepare", {"instance": "optical_bb84", "config": config}
            )
            job = replies["started"]["job"]
            with anyio.fail_after(300):
                status = await call("run_status", {"job": job})
                while status["state"] not in jobs.FINAL_STATES:
                    await anyio.sleep(0.5)
                    status = await call("run_status", {"job": job})
            replies["status"] = status
            replies["summary"] = await call("prepare", {"job": job})
            replies["part"] = await call(
                "prepare", {"job": job, "part": "acceptance_alphabet"}
            )
            described = await call("describe_instance", {"document": tree})
            replies["document"] = await call(
                "prepare", {"document": tree, "config": described["default_config"]}
            )
            report = await client.call_tool("get_report", {"job": job})
            replies["report_is_error"] = report.is_error
            return replies

    out = anyio.run(session)
    started = out["started"]
    assert started["state"] == "starting" and started["kind"] == "prepare"
    assert started["expected_seconds"] > 0
    assert "photon cutoff" in started["why"]
    assert "run_status" in started["next"] and "prepare(job" in started["next"]
    assert started["duration"] in started["tell_the_user"]
    assert "runs in the background" in started["tell_the_user"]
    status = out["status"]
    assert status["state"] == "done", status
    assert status["kind"] == "prepare"
    assert status["estimate"]["expected_seconds"] == started["expected_seconds"]
    assert status["estimate"]["why"] == started["why"]
    assert {"summary.json", "preparation.json"} <= set(status["files"])
    # THE SAME SUMMARY THE SYNCHRONOUS CALL GIVES, under the same budget; only
    # the file differs: a job keeps its envelope in its own directory.
    synchronous = jobs.write_preparation(
        core.prepare_surface(core.resolve("optical_bb84"), config)
    )
    background = dict(out["summary"])
    assert background.pop("file") == status["files"]["preparation.json"]
    synchronous.pop("file")
    assert background == json.loads(json.dumps(synchronous))
    assert background["estimate"]["background"] is True
    assert out["part"]["part"] == "acceptance_alphabet"
    assert out["part"]["file"] == status["files"]["preparation.json"]
    # A custom document goes the same way, its job in the declared namespace.
    assert out["document"]["job"].startswith("declared_my_y_bb84-")
    document = _finish(out["document"]["job"])
    assert document["state"] == "done", document
    summary = jobs.preparation_result(out["document"]["job"])["summary"]
    assert [item["kind"] for item in summary["user_declared"]] == ["receiver_povm"]
    assert out["report_is_error"] is True
    for key, value in out.items():
        assert len(json.dumps(value)) <= MAX_REPLY_CHARS, key


def test_a_reused_finished_preparation_is_not_said_to_run(
    jobs_dir: Path, monkeypatch: pytest.MonkeyPatch, clean_engine: None
) -> None:
    pytest.importorskip("mcp")
    from mcp import Client
    from runs.mcp.server import build_server

    monkeypatch.setenv(estimate.BUDGET_ENV, "0")
    config = core.describe_instance("optical_bb84")["default_config"]
    first = jobs.start_preparation(
        core.resolve("optical_bb84"), config, estimate={"expected_seconds": 1.0}
    )
    assert _finish(first["job"])["state"] == "done"

    async def again() -> Any:
        async with Client(build_server()) as client:
            result = await client.call_tool(
                "prepare", {"instance": "optical_bb84", "config": config}
            )
            return result.structured_content or json.loads(result.content[0].text)

    reply = anyio.run(again)
    assert reply["job"] == first["job"] and reply["reused"] is True
    assert reply["state"] == "done"
    assert "already finished" in reply["tell_the_user"]
    assert "background" not in reply["tell_the_user"]
    assert "poll" not in reply["next"]


def test_a_cancelled_preparation_job_leaves_no_summary(
    jobs_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A preparation of seconds, cancelled at once: no summary, no partial file."""
    config = _optical(photon_cutoff=7, exact_window=9)[1]
    started = jobs.start_preparation(
        core.resolve("optical_bb84"),
        config.to_payload(),
        estimate={"expected_seconds": 10.0},
    )
    status = jobs.cancel_job(started["job"])
    status = _finish(started["job"])
    assert status["state"] == "cancelled", status
    directory = Path(status["directory"])
    assert not (directory / jobs.SUMMARY_FILE).exists()
    assert not (directory / jobs.PREPARATION_FILE).exists()
    assert not list(directory.glob("*.partial*"))
    assert "summary" not in jobs.preparation_result(started["job"])


def test_the_worker_s_preparation_refusals(jobs_dir: Path, tmp_path: Path) -> None:
    """An input refusal ends ``refused`` with no summary; an engine one with one."""
    config = core.describe_instance("optical_bb84")["default_config"]
    directory = tmp_path / "job"
    directory.mkdir()
    recorded: list[bool] = []
    request = {"kind": jobs.PREPARE, "instance": "optical_bb84"}
    unknown = {**config, "device": {**config["device"], "no_such_key": 1}}
    fields = worker._prepare(
        {**request, "config": unknown}, directory, lambda: recorded.append(True)
    )
    assert fields["state"] == "refused" and fields["refusal"]["refused"] is True
    assert fields["refusal"]["reason"]
    assert not (directory / jobs.SUMMARY_FILE).exists() and not recorded
    empty_window = {
        **config,
        "device": {**config["device"], "photon_cutoff": 3, "exact_window": 2},
    }
    fields = worker._prepare(
        {**request, "config": empty_window}, directory, lambda: recorded.append(True)
    )
    assert fields["state"] == "refused", fields
    assert fields["refusal"]["reason"] == "exact_window_depth_outside_declared_range"
    summary = json.loads((directory / jobs.SUMMARY_FILE).read_text("utf-8"))
    assert summary["refused"] is True and recorded == [True]
    assert summary["file"] == str(directory / jobs.PREPARATION_FILE)


def test_a_preparation_job_and_a_run_job_of_one_request_are_two_jobs(
    jobs_dir: Path, monkeypatch: pytest.MonkeyPatch, clean_engine: None
) -> None:
    _no_worker(monkeypatch)
    monkeypatch.setenv(estimate.BUDGET_ENV, "0")
    surface = core.resolve("optical_bb84")
    config = core.describe_instance("optical_bb84")["default_config"]
    prepared = jobs.start_preparation(surface, config, estimate={})
    run = jobs.start_run("optical_bb84", config)
    assert prepared["job"] != run["job"]
    assert (prepared["kind"], run["kind"]) == ("prepare", "run")
    assert prepared["config_digest"] == run["config_digest"]


# ---------------------------------------------------------------------------
#  Run jobs
# ---------------------------------------------------------------------------


def test_start_run_states_the_estimate_and_skips_a_slow_check(
    jobs_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Past the budget the run's worker prepares; the reply still says how long."""
    spawned = _no_worker(monkeypatch)
    monkeypatch.setattr(
        core, "prepare_surface", lambda *args, **kwargs: pytest.fail("prepared")
    )
    monkeypatch.setenv(estimate.BUDGET_ENV, "0")
    started = jobs.start_run(
        "optical_bb84", core.describe_instance("optical_bb84")["default_config"]
    )
    assert started["kind"] == "run" and spawned
    assert started["estimate"]["expected_seconds"] > 0
    assert "photon cutoff" in started["estimate"]["why"]
    assert "solve comes on top" in started["estimate"]["covers"]
    assert "not reused by the run" in started["estimate"]["covers"]
    request = json.loads((Path(started["directory"]) / "request.json").read_text())
    assert "kind" not in request
    # The run's key is unchanged by the estimate: the worker recomputes it.
    assert started["job"].split("-")[-2] == core.job_key(request)[:12]


def test_the_run_worker_does_not_prepare_before_the_run(
    jobs_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``load_request`` reads the configuration; the run prepares once."""
    _no_worker(monkeypatch)
    started = jobs.start_run(
        "optical_bb84", core.describe_instance("optical_bb84")["default_config"]
    )
    request = json.loads((Path(started["directory"]) / "request.json").read_text())
    monkeypatch.setattr(
        core, "run_preparation", lambda *args: pytest.fail("prepared twice")
    )
    loaded = worker.load_request(request)
    assert not isinstance(loaded, dict) and len(loaded) == 2


@pytest.mark.requires_qics
def test_a_background_run_refused_at_its_preparation_is_refused_and_reused(
    jobs_dir: Path, monkeypatch: pytest.MonkeyPatch, clean_engine: None
) -> None:
    """Past the budget start_run does not prepare; the worker's run refuses."""
    monkeypatch.setenv(estimate.BUDGET_ENV, "0")
    config = core.describe_instance("optical_bb84")["default_config"]
    config["device"] = {**config["device"], "photon_cutoff": 3, "exact_window": 2}
    started = jobs.start_run("optical_bb84", config)
    assert started["reused"] is False and "refused" not in started, started
    status = _finish(started["job"])
    assert status["state"] == "refused", status
    assert status["refusal"]["reason"] == "exact_window_depth_outside_declared_range"
    again = jobs.start_run("optical_bb84", config)
    assert again["job"] == started["job"] and again["reused"] is True
    assert again["state"] == "refused"
    assert again["refusal"]["reason"] == status["refusal"]["reason"]
