"""Exercise benchmark failure accounting, not solver mathematics."""

from __future__ import annotations

import json
import os
import signal
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, call

import pytest
from runs.solver_benchmark import run as runner
from runs.solver_benchmark.common import write_json
from runs.solver_benchmark.run import execute, main
from runs.solver_benchmark.summarize import rows
from runs.solver_benchmark.worker import configuration, summarize


@pytest.mark.parametrize(
    ("status", "declaration", "refused", "expected"),
    [
        ("completed", "reference_companion", False, True),
        ("timeout", "reference_companion", False, False),
        ("completed", "searched", False, False),
        ("completed", "reference_companion", True, False),
    ],
)
@pytest.mark.parametrize("null_declaration", [False, True])
def test_target_needs_completed_matching_declaration(
    tmp_path: Path,
    status: str,
    declaration: str,
    refused: bool,
    expected: bool,
    null_declaration: bool,
) -> None:
    case: dict[str, Any] = {"id": "case", "target_bound": 0.5}
    if null_declaration:
        case["target_declaration"] = None
    write_json(
        tmp_path / "manifest.json",
        {
            "revision": "example",
            "tasks": [
                {
                    "id": "task",
                    "case": case,
                    "variant": {"id": "variant", "method": "factor"},
                    "repeat": 0,
                    "seconds": 1,
                }
            ],
        },
    )
    write_json(
        tmp_path / "task" / "completion.json",
        {
            "status": status,
            "elapsed_seconds": 2,
            "process_cap_seconds": 3,
        },
    )
    write_json(
        tmp_path / "task" / "summary.json",
        {
            "certificate_valid": True,
            "certified_bound": 0.6,
            "certified_declaration": declaration,
            "refused": refused,
        },
    )
    row = rows(tmp_path)[0]
    assert row["target_declaration"] == "reference_companion"
    assert row["target_met"] is expected
    assert row["certified_target_observed_seconds"] == (2 if expected else None)
    assert row["process_cap_seconds"] == 3


def test_summary_retains_refusal_and_dropped_diagnostics() -> None:
    observed = [{"backend": "clarabel", "linear_solver": {"threads": 1}}]
    request = {"method": "fw", "max_iterations": 200, "gap_target": 1e-10}
    result = summarize(
        {
            "refused": True,
            "stages": {
                "solve": {"refused": True, "reason": "example", "detail": "why"},
                "key_rate": {
                    "h_low_dropped": 0.4,
                    "h_lb_dropped": 0.3,
                    "oracle_diagnostics": observed,
                    "solver_request": request,
                },
            },
        }
    )
    assert result["refusals"]["solve"]["reason"] == "example"
    assert result["h_low_searched_diagnostic"] == 0.4
    assert result["certificate_valid"] is False
    assert result["oracle_diagnostics"] == observed
    assert result["solver_request"] == request


def test_large_round_configuration_uses_enclosure() -> None:
    _, config = configuration(
        {
            "instance": "bbm92",
            "rounds": 10**10,
            "alpha": 1.005,
            "device": {"alice_efficiency": "0.8"},
        },
        {"method": "factor"},
        1,
    )
    assert str(config.tail_evaluation) == "enclosure"
    assert len(config.device["alice_efficiency"]) == 4


def test_watchdog_terminates_actual_interpreter(tmp_path: Path) -> None:
    result = execute(
        [
            getattr(sys, "_base_executable", sys.executable),
            "-c",
            "import time; time.sleep(60)",
        ],
        tmp_path,
        0.2,
        dict(os.environ),
    )
    assert result["status"] == "timeout"
    assert result["elapsed_seconds"] < 5


@pytest.mark.parametrize(
    ("instance", "iterations"), [("bbm92", None), ("decoy_bb84", 2000)]
)
def test_native_solver_effort_preserves_instance_defaults(
    instance: str, iterations: int | None
) -> None:
    _, config = configuration(
        {"instance": instance, "rounds": 10**8, "alpha": 1.005},
        {"method": "native", "native_solver_settings": True},
        1,
    )
    assert config.solver.method is None
    assert config.solver.advanced is None
    assert config.solver.max_iterations == iterations
    assert config.solver.budget_seconds is None


def test_zero_budget_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="2"):
        main(["--seconds", "0", "--out", str(tmp_path), "--dry-run"])


def test_warm_chain_is_variant_local_and_resets_each_repeat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases_file, out = tmp_path / "cases.json", tmp_path / "matrix"
    write_json(cases_file, [{"id": name} for name in ("first", "second", "third")])
    monkeypatch.setattr(runner, "git_revision", lambda: "example")
    monkeypatch.setattr(runner, "memory_snapshot", lambda: {})
    attempted: list[dict[str, Any]] = []

    def execute_fake(
        command: list[str],
        folder: Path,
        seconds: float,
        environment: dict[str, str],
    ) -> dict[str, Any]:
        task = json.loads(Path(command[-1]).read_text())
        attempted.append(task)
        case, variant = task["case"]["id"], task["variant"]["id"]
        # A timed-out attempt's leftover iterate is deliberately ineligible.
        status = "timeout" if (case, variant) == ("first", "pairwise") else "completed"
        if (case, variant) != ("second", "factor"):
            write_json(
                folder / "final-iterate.json", {"test": "worker admission is separate"}
            )
        write_json(folder / "summary.json", {"alpha": 1.002})
        return {
            "status": status,
            "elapsed_seconds": 1.0,
            "process_cap_seconds": seconds,
        }

    monkeypatch.setattr(runner, "execute", execute_fake)
    arguments = [
        "--cases",
        str(cases_file),
        "--methods",
        "factor",
        "pairwise",
        "--warm-chain",
        "--repeats",
        "2",
        "--seconds",
        "1",
        "--process-seconds",
        "10",
        "--total-seconds",
        "100",
        "--out",
        str(out),
    ]
    assert main(arguments) == 0
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["warm_chain"] is True
    assert len(attempted) == 12
    planned = {task["id"]: task for task in manifest["tasks"]}
    actual = {task["id"]: task for task in attempted}
    for repeat in range(2):
        for variant in ("factor", "pairwise"):
            first = f"first--{variant}--r{repeat}"
            second = f"second--{variant}--r{repeat}"
            third = f"third--{variant}--r{repeat}"
            assert planned[first]["warm_predecessor"] is None
            assert planned[second]["warm_predecessor"] == first
            assert planned[third]["warm_predecessor"] == second
            assert actual[first]["warm_start"] is None
            assert actual[first]["warm_start_reason"] == "chain_first"
            if variant == "factor":
                assert actual[second]["warm_start"] == str(
                    out / first / "final-iterate.json"
                )
                assert actual[third]["warm_start"] is None
                assert (
                    actual[third]["warm_start_reason"]
                    == "predecessor_missing_final_iterate"
                )
            else:
                assert actual[second]["warm_start"] is None
                assert (
                    actual[second]["warm_start_reason"] == "predecessor_not_completed"
                )
                assert actual[third]["warm_start"] == str(
                    out / second / "final-iterate.json"
                )
    assert all("warm_start" not in task for task in planned.values())
    summaries = {row["task"]: row for row in rows(out)}
    assert (
        summaries["second--factor--r0"]["warm_start"]
        == actual["second--factor--r0"]["warm_start"]
    )
    assert summaries["third--pairwise--r0"]["warm_chain_elapsed_seconds"] == 3.0
    assert summaries["first--factor--r1"]["warm_chain_elapsed_seconds"] == 1.0
    assert summaries["third--factor--r0"]["alpha"] == 1.002
    # Resume never reruns predecessors or changes their recorded seed choice.
    assert main([*arguments, "--resume"]) == 0
    assert len(attempted) == 12
    with pytest.raises(SystemExit, match="2"):
        main([arg for arg in arguments if arg != "--warm-chain"] + ["--resume"])


def test_warm_resume_charges_predecessor_and_shortened_interrupted_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases_file, out = tmp_path / "cases.json", tmp_path / "matrix"
    write_json(cases_file, [{"id": name} for name in ("first", "second", "third")])
    monkeypatch.setattr(runner, "git_revision", lambda: "example")
    monkeypatch.setattr(runner, "memory_snapshot", lambda: {})
    calls: list[float] = []

    def execute_fake(
        command: list[str],
        folder: Path,
        seconds: float,
        environment: dict[str, str],
    ) -> dict[str, Any]:
        calls.append(seconds)
        if len(calls) == 2:
            raise KeyboardInterrupt
        write_json(folder / "final-iterate.json", {"test": "seed"})
        return {
            "status": "completed",
            "elapsed_seconds": 4.0,
            "process_cap_seconds": seconds,
        }

    monkeypatch.setattr(runner, "execute", execute_fake)
    arguments = [
        "--cases",
        str(cases_file),
        "--methods",
        "factor",
        "--warm-chain",
        "--seconds",
        "1",
        "--process-seconds",
        "4",
        "--total-seconds",
        "5",
        "--out",
        str(out),
    ]
    with pytest.raises(KeyboardInterrupt):
        main(arguments)
    interrupted_task = out / "second--factor--r0" / "task.json"
    recorded = interrupted_task.read_bytes()
    assert json.loads(recorded)["process_cap_seconds"] == 1.0
    assert main([*arguments, "--resume"]) == 0
    assert calls == [4.0, 1.0]
    assert interrupted_task.read_bytes() == recorded
    results = rows(out)
    assert [row["status"] for row in results] == [
        "completed",
        "interrupted",
        "not_started",
    ]
    assert results[1]["elapsed_seconds"] == results[1]["process_cap_seconds"] == 1.0
    assert results[1]["warm_chain_elapsed_seconds"] == 5.0
    assert results[1]["warm_start_reason"] == "completed_predecessor"
    assert results[2]["warm_start_reason"] == "not_started"
    assert results[2]["warm_chain_elapsed_seconds"] is None


def test_warm_chain_missing_predecessor_is_explicit_cold(tmp_path: Path) -> None:
    task = {"warm_predecessor": "missing"}
    resolved = runner.warm_task(task, tmp_path)
    assert resolved["warm_start"] is None
    assert resolved["warm_start_reason"] == "predecessor_missing_completion"


def test_unsupported_polish_cannot_earn_solver_target(tmp_path: Path) -> None:
    write_json(
        tmp_path / "manifest.json",
        {
            "revision": "example",
            "tasks": [
                {
                    "id": "one",
                    "case": {"id": "case", "target_key_length": 5},
                    "variant": {"id": "factor", "method": "factor"},
                    "repeat": 0,
                    "seconds": 1,
                }
            ],
        },
    )
    write_json(
        tmp_path / "one/completion.json",
        {
            "status": "completed",
            "elapsed_seconds": 2,
        },
    )
    write_json(
        tmp_path / "one/summary.json",
        {
            "certificate_valid": True,
            "certified_declaration": "reference_companion",
            "key_length": 10,
            "search": {"termination": "unsupported"},
        },
    )
    row = rows(tmp_path)[0]
    assert row["certificate_valid"] is True
    assert row["key_length"] == 10
    assert row["candidate_supported"] is False
    assert row["target_met"] is False


def test_warm_key_target_charges_seed_and_alpha_bound_target_refuses(
    tmp_path: Path,
) -> None:
    tasks = [
        {
            "id": name,
            "case": {
                "id": name,
                "target_key_length": 5,
                "alpha_search": {"coarse_points": 3},
            },
            "variant": {"id": "factor", "method": "factor"},
            "repeat": 0,
            "seconds": 1,
            "warm_predecessor": predecessor,
        }
        for name, predecessor in [("first", None), ("second", "first")]
    ]
    manifest = {"revision": "example", "warm_chain": True, "tasks": tasks}
    write_json(tmp_path / "manifest.json", manifest)
    for task in tasks:
        write_json(
            tmp_path / task["id"] / "completion.json",
            {
                "status": "completed",
                "elapsed_seconds": 2,
            },
        )
        write_json(
            tmp_path / task["id"] / "summary.json",
            {
                "certificate_valid": True,
                "certified_declaration": "reference_companion",
                "key_length": 10,
                "search": {"termination": "budget_exhausted"},
            },
        )
    assert rows(tmp_path)[1]["certified_target_observed_seconds"] == 4
    tasks[0]["case"]["target_bound"] = 0.5
    write_json(tmp_path / "manifest.json", manifest)
    with pytest.raises(ValueError, match="bound targets require fixed alpha"):
        rows(tmp_path)


@pytest.mark.parametrize(
    ("restriction", "expected"),
    [(None, True), ("reference_companion", False), ("searched", True)],
)
def test_key_target_accepts_reported_declaration_unless_restricted(
    tmp_path: Path, restriction: str | None, expected: bool
) -> None:
    case: dict[str, Any] = {"id": "case", "target_key_length": 5}
    if restriction is not None:
        case["target_declaration"] = restriction
    write_json(
        tmp_path / "manifest.json",
        {
            "revision": "example",
            "tasks": [
                {
                    "id": "task",
                    "case": case,
                    "variant": {"id": "factor", "method": "factor"},
                    "repeat": 0,
                    "seconds": 1,
                }
            ],
        },
    )
    write_json(
        tmp_path / "task/completion.json",
        {"status": "completed", "elapsed_seconds": 2},
    )
    write_json(
        tmp_path / "task/summary.json",
        {
            "certificate_valid": True,
            "certified_declaration": "searched",
            "key_length": 10,
            "search": {"termination": "stagnated"},
        },
    )
    row = rows(tmp_path)[0]
    assert row["target_declaration"] == restriction
    assert row["target_met"] is expected
    assert row["certified_target_observed_seconds"] == (2 if expected else None)


def test_posix_cancellation_kills_worker_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    process = SimpleNamespace(
        pid=1234, wait=Mock(side_effect=[KeyboardInterrupt(), -9]), kill=Mock()
    )
    popen = Mock(return_value=process)
    kill_group = Mock()
    # Replace module bindings, not global os/sys state, so this runs on Windows
    # too without launching a process or depending on os.killpg being present.
    monkeypatch.setattr(runner, "os", SimpleNamespace(name="posix", killpg=kill_group))
    monkeypatch.setattr(runner, "sys", SimpleNamespace(platform="linux"))
    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    monkeypatch.setattr(signal, "SIGKILL", 9, raising=False)
    with pytest.raises(KeyboardInterrupt):
        execute(["unused"], tmp_path, 1, {})
    assert popen.call_args.kwargs["start_new_session"] is True
    kill_group.assert_called_once_with(process.pid, signal.SIGKILL)
    process.kill.assert_not_called()
    assert process.wait.call_args_list == [call(timeout=1), call(timeout=10)]
