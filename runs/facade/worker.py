"""``python -m runs.facade.worker JOB_DIR``: the one process a job is.

Reads ``request.json``, runs the instance with the QICS oracle, writes the
record and its key-rate report, and keeps ``status.json`` current (see
:mod:`runs.facade.jobs` for the files). The run itself is the gateway's
wiring, lifted: the instance's ``runner`` with an optional honest provider,
``record_run`` with the instance's identity, and the engine's one writer of
the final iterate.

A job of a protocol document rebuilds the document's surface from
the canonical tree and conversions ``request.json`` stores, with
``instances.declared.load_canonical`` -- the reader ``prepare`` used -- and
then runs and records exactly as an instance's job does.

A PREPARATION JOB (``kind: "prepare"``; a preparation the cost estimate puts
above the budget, :mod:`runs.facade.estimate`) runs the facade's own
``prepare_surface`` on the request as given and writes what a synchronous
``prepare`` returns: the envelope as ``preparation.json`` and the summary as
``summary.json``, both here. No oracle, no record.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

from runs.facade import core
from runs.facade.core import read_json, write_json_atomic

#: Progress events are written at most this often, so a long solve does not
#: produce a file larger than its record.
_ITERATION_EVERY_S = 1.0


class _Status:
    """The job's ``status.json``, written by this process only.

    ``recording`` is set, under ``cancel_lock``, once the worker begins to
    write its record; from then on a cancel request is ignored, so a record
    is never left half-written by one.
    """

    def __init__(self, directory: Path) -> None:
        self.path = directory / "status.json"
        self.lock = threading.Lock()
        self.cancel_lock = threading.Lock()
        self.recording = False
        self.fields: dict[str, Any] = dict(read_json(self.path) or {})

    def begin_recording(self) -> None:
        with self.cancel_lock:
            self.recording = True

    def update(self, **fields: Any) -> None:
        with self.lock:
            self.fields.update(fields, heartbeat=time.time())
            write_json_atomic(self.path, self.fields)


class _Events:
    def __init__(self, path: Path) -> None:
        self.handle = path.open("a", encoding="utf-8")
        self.lock = threading.Lock()
        self.last_iteration = 0.0

    def __call__(self, event: dict[str, Any]) -> None:
        if event.get("type") == "iteration":
            now = time.monotonic()
            if now - self.last_iteration < _ITERATION_EVERY_S:
                return
            self.last_iteration = now
        with self.lock:
            self.handle.write(
                json.dumps({"time": time.time(), **event}, default=str) + "\n"
            )
            self.handle.flush()


class _ProgressOracle:
    """Forward both oracle methods unchanged, counting ``minimize`` calls."""

    def __init__(self, inner: Any, on_call: Callable[[int], None]) -> None:
        self.inner = inner
        self.on_call = on_call
        self.calls = 0

    def capabilities(self) -> Any:
        return self.inner.capabilities()

    def minimize(self, problem: Any) -> Any:
        self.calls += 1
        self.on_call(self.calls)
        return self.inner.minimize(problem)


class _LogForwarder(logging.Handler):
    """Forward the run tier's structured log lines (logger ``certiqs_key.runs``)."""

    FIELDS = ("stage", "stage_module", "event", "wall_time_s", "reason")

    def __init__(self, emit: Callable[[dict[str, Any]], None]) -> None:
        super().__init__(level=logging.INFO)
        self.emit_event = emit

    def emit(self, record: logging.LogRecord) -> None:
        line: dict[str, Any] = {
            "type": "log",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        for name in self.FIELDS:
            if hasattr(record, name):
                line[name] = getattr(record, name)
        self.emit_event(line)


def _heartbeat(status: _Status, directory: Path) -> None:
    """Refresh the heartbeat; on a cancel request, record it and exit at once.

    The loop never dies: a failed write is reported and retried on the next
    beat, because a dead heartbeat turns a healthy run ``lost`` and disables
    cancelling.
    """
    beat = 0.0
    while True:
        time.sleep(1.0)
        try:
            if (directory / "cancel.request").exists():
                with status.cancel_lock:
                    if not status.recording:
                        status.update(
                            state="cancelled",
                            finished=time.time(),
                            detail="cancelled on request",
                        )
                        os._exit(3)
            if time.monotonic() - beat >= 5.0:
                status.update()
                beat = time.monotonic()
        except Exception:
            traceback.print_exc()


def load_request(request: dict[str, Any]) -> tuple[Any, Any] | dict[str, Any]:
    """Return the request's ``(surface, config)``, or a refusal.

    The surface is the instance's, or the stored document's rebuilt by
    :func:`runs.facade.core.stored_document`; the configuration is read and
    key-checked as ``prepare`` reads it. The request's fields must still give
    the key its job id was named by: a ``request.json`` edited
    after the start is refused, not run under the name of another request.

    NO PREPARATION HERE: the run prepares once, inside
    ``run_slice``, and a refusal there is the run's own outcome (a refused
    record and report). Preparing here as well cost a run job a second
    preparation, minutes at a far cutoff.
    """
    job = request.get("job")
    if isinstance(job, str):
        key = core.job_key(request)
        if job.rsplit("-", 2)[-2:-1] != [key[:12]]:
            return {
                "refused": True,
                "stage": "jobs",
                "reason": "job_request_mismatch",
                "detail": f"request.json's fields key the job {key[:12]}, but it "
                f"is named {job}; it was changed after the job started",
            }
    if request.get("document") is not None:
        s = core.stored_document(request)
    else:
        s = core.resolve(request["instance"])
    if isinstance(s, dict):
        return s
    config = core.config_for(s, request["config"])
    if isinstance(config, dict):
        return config
    return s, config


def _prepare(
    request: dict[str, Any], directory: Path, begin_recording: Callable[[], None]
) -> dict[str, Any]:
    """Prepare the request as ``prepare`` would; return the status fields to set.

    The envelope is written into the job's directory, after
    ``begin_recording``: from then on a cancel is ignored, so a job never ends
    ``cancelled`` with a summary written or a file half-written.
    """
    from runs.facade import jobs

    job = request.get("job")
    if isinstance(job, str) and job.rsplit("-", 2)[-2:-1] != [
        core.job_key(request)[:12]
    ]:
        return {
            "state": "refused",
            "refusal": {
                "refused": True,
                "stage": "jobs",
                "reason": "job_request_mismatch",
                "detail": "request.json was changed after the job started",
            },
        }
    if request.get("document") is not None:
        s = core.stored_document(request)
    else:
        s = core.resolve(request["instance"])
    if isinstance(s, dict):
        return {"state": "refused", "refusal": s}
    envelope = core.prepare_surface(s, request["config"], request.get("honest"))
    if envelope.get("refused"):
        return {"state": "refused", "refusal": envelope}
    begin_recording()
    summary = jobs.write_preparation(envelope, directory / jobs.PREPARATION_FILE)
    write_json_atomic(directory / jobs.SUMMARY_FILE, summary)
    if summary.get("refused"):
        return {
            "state": "refused",
            "refusal": {
                key: summary.get(key)
                for key in ("refused", "stage", "reason", "detail")
            },
        }
    return {"state": "done"}


def _run(
    request: dict[str, Any],
    directory: Path,
    emit: Callable[[dict[str, Any]], None],
    begin_recording: Callable[[], None],
) -> dict[str, Any]:
    """Run the request to a written record; return the status fields to set."""
    from certiqs_key.runs import SliceRefusal, record_run, write_record
    from certiqs_key.runs.iterate_file import WarmStartFileError, attach_final_iterate
    from certiqs_key.runs.surface import InstanceIdentity, solver_request
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    loaded = load_request(request)
    if isinstance(loaded, dict):
        return {"state": "refused", "refusal": loaded}
    s, config = loaded
    instance = s.DESCRIPTOR.id
    if (
        config.solver is not None
        and config.solver.advanced is not None
        and config.solver.advanced.warm_start is not None
    ):
        try:
            solver_request(config.solver)
        except WarmStartFileError as error:
            return {"state": "refused", "refusal": core.refusal_from(error)}
    honest = core.honest_override(request.get("honest"), instance)
    if isinstance(honest, dict):
        return {"state": "refused", "refusal": honest}
    provider, note = honest

    oracle = _ProgressOracle(
        QicsSectorChoiOracle(), lambda k: emit({"type": "iteration", "calls": k})
    )

    def on_stage(event: Any) -> None:
        line: dict[str, Any] = {
            "type": "stage",
            "kind": event.kind,
            "stage": str(event.stage),
            "wall_time_s": event.wall_time_s,
            "reason": event.reason,
        }
        for name in ("station", "iteration", "gap"):
            value = getattr(event, name, None)
            if value is not None:
                line[name] = value
        emit(line)

    logger = logging.getLogger("certiqs_key.runs")
    handler = _LogForwarder(emit)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        run_one = s.runner(
            oracle,
            directory / "bundles",
            created_by=core.CREATED_BY,
            observer=on_stage,
            honest_provider=provider,
            honest_model_note=note,
        )
        # An input the instance refuses while it prepares (the lowering of a
        # document, the shared input preparation) is a coded refusal, as
        # ``prepare`` returns it; a module's refusal is the run's outcome.
        outcome = core.guarded(lambda: run_one(config, 0))
    finally:
        logger.removeHandler(handler)
    if isinstance(outcome, dict):
        return {"state": "refused", "refusal": outcome}

    identity = InstanceIdentity(s.DESCRIPTOR, tuple(s.PARAMETERS))
    record = attach_final_iterate(
        record_run(outcome, config, created_by=core.CREATED_BY, instance=identity),
        outcome,
        config,
        directory,
    )
    begin_recording()
    write_record(directory / "record.json", record)
    record_dict = record.as_dict()
    core.write_report_files(record_dict, directory)
    key_rate = record_dict["payload"]["stages"].get("key_rate") or {}
    if isinstance(outcome, SliceRefusal):
        return {
            "state": "refused",
            "refusal": {
                "refused": True,
                "stage": str(outcome.stage),
                "reason": outcome.reason,
                "detail": outcome.detail,
            },
            "oracle_calls": oracle.calls,
        }
    return {
        "state": "done",
        "key_length": key_rate.get("key_length"),
        "oracle_calls": oracle.calls,
    }


def main(argv: list[str]) -> int:
    """Run the job in ``argv[0]``; the exit code is 0 unless the worker failed."""
    directory = Path(argv[0])
    status = _Status(directory)
    status.update(state="running", pid=os.getpid())
    threading.Thread(target=_heartbeat, args=(status, directory), daemon=True).start()
    events = _Events(directory / "events.jsonl")
    try:
        request = read_json(directory / "request.json")
        if request.get("kind") == "prepare":
            fields = _prepare(request, directory, status.begin_recording)
        else:
            fields = _run(request, directory, events, status.begin_recording)
        status.update(finished=time.time(), **fields)
    except Exception as error:
        traceback.print_exc()
        status.update(
            state="error",
            finished=time.time(),
            detail=f"{type(error).__name__}: {error}",
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
