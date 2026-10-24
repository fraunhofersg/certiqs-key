"""A run as a background job: one worker process, one directory of files.

WHY THIS EXISTS. A run takes from seconds to many minutes, and an adapter
cannot hold a call open that long: an MCP client gives a tool call about a
minute (Codex's default ``tool_timeout_sec`` is 60). So a run is STARTED,
then asked about, then read. An agent's local server needs no scheduler or
database; the files are the state:

    request.json    what was asked: instance, configuration, honest override,
                    engine identity (written once, before the worker starts);
                    for a protocol document, its canonical tree, conversions
                    and digest, which the worker reloads; the
                    preparation's cost estimate; ``kind: "prepare"`` for a
                    preparation job
    status.json     the worker's state and heartbeat, replaced atomically
    events.jsonl    progress: stages, iterations, log lines
    record.json     the run record (``write_record``; never overwritten)
    report.*        the key-rate report as JSON, Markdown and HTML
    summary.json    a preparation job's summary, as ``prepare`` returns it
    preparation.json  a preparation job's envelope, which prepare(job, part) reads
    worker.log      the worker's own output
    cancel.request  present once a cancel was asked for

No database and no PID probe: a worker that stops updating its heartbeat is
reported ``lost``, because asking an operating system whether a process lives
is not portable (on Windows ``os.kill(pid, 0)`` terminates it). A status that
is momentarily unreadable -- Windows locks a file being replaced -- is
retried and, failing that, reported ``unknown``, which is not final, never
``lost``.

A PREPARATION AS A JOB. A preparation expected to take
longer than the budget (:mod:`runs.facade.estimate`) is started here like a
run, by the same worker, with ``kind: "prepare"`` in its request: the worker
prepares, writes the envelope where a synchronous ``prepare`` writes it, and
the summary beside it, so :func:`preparation_result` returns what the
synchronous call would have. Every job carries the estimate, and its status
shows the expected seconds beside the elapsed ones.

The jobs directory is ``$CERTIQS_KEY_JOBS_DIR`` or ``~/.certiqs-key/jobs``,
outside the repository so that runs never appear in its working tree.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from runs.facade import core
from runs.facade.core import read_json, write_json_atomic
from runs.facade.estimate import estimate_preparation

__all__ = [
    "FINAL_STATES",
    "PREPARATION_FILE",
    "PREPARE",
    "SUMMARY_FILE",
    "cancel_job",
    "job_directory",
    "job_status",
    "jobs_root",
    "list_jobs",
    "preparation_result",
    "start_preparation",
    "start_run",
    "write_json_atomic",
    "write_preparation",
]

#: What a run job's estimate covers, said wherever it is shown: the worker
#: prepares once inside ``run_slice`` and then solves.
RUN_COVERS: Final[str] = (
    "the run's own preparation (its job prepares once; a separate prepare "
    "call beforehand is its own cost and is not reused by the run); the solve "
    "comes on top: seconds to many minutes, capped by config.solver."
    "budget_seconds or max_iterations"
)

#: The ``kind`` of a preparation job's request; a run's request has none.
PREPARE: Final[str] = "prepare"
#: A finished preparation job's summary, in its directory.
SUMMARY_FILE: Final[str] = "summary.json"
#: A preparation job's envelope, in its directory.
PREPARATION_FILE: Final[str] = "preparation.json"

JOBS_ENV: Final[str] = "CERTIQS_KEY_JOBS_DIR"
MAX_JOBS_ENV: Final[str] = "CERTIQS_KEY_MAX_JOBS"
#: Concurrent runs by default; each holds a solver and its memory.
DEFAULT_MAX_JOBS: Final[int] = 2
#: The worker refreshes its heartbeat every few seconds; this long without one
#: and a non-final job is ``lost``.
STALE_AFTER_S: Final[float] = 90.0
FINAL_STATES: Final[frozenset[str]] = frozenset(
    {"done", "refused", "error", "cancelled", "lost"}
)
#: A job in one of these states answers an identical request.
_REUSABLE: Final[frozenset[str]] = frozenset(
    {"starting", "running", "unknown", "done", "refused"}
)
#: What a job id looks like: ``<instance>-<12 hex>-<n>``, or
#: ``declared_<document id>-<12 hex>-<n>`` for a caller's protocol document
#: (never a packaged instance's namespace). Anything else is
#: refused before it becomes a path (a Windows ``E:foo`` would resolve to a
#: drive-relative path).
_JOB_ID: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_]+-[0-9a-f]{12}-[0-9]+$")

#: Workers this process started, reaped once finished (no zombies on POSIX).
_PROCESSES: dict[str, subprocess.Popen[bytes]] = {}
#: One start at a time in this process: the attempt number and the running
#: count are decided under it. Two server
#: processes sharing one jobs directory can still both start; the exclusive
#: directory creation keeps their attempts apart.
_START_LOCK = threading.Lock()


def jobs_root() -> Path:
    """Return the jobs directory, created on first use."""
    configured = os.environ.get(JOBS_ENV)
    root = Path(configured) if configured else Path.home() / ".certiqs-key" / "jobs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def job_directory(job: str) -> Path:
    """Return a job's directory; refuse a name that is not a job here."""
    if not _JOB_ID.fullmatch(job):
        raise KeyError(f"{job!r} is not a job id")
    root = jobs_root()
    directory = root / job
    if directory.resolve().parent != root.resolve():
        raise KeyError(f"{job!r} is not a job id")
    if not (directory / "request.json").is_file():
        raise KeyError(f"no job {job!r} in {root}")
    return directory


def _attempts(instance: str, key: str) -> list[Path]:
    prefix = f"{instance}-{key[:12]}-"
    found = [
        path
        for path in jobs_root().glob(prefix + "*")
        if path.name[len(prefix) :].isdigit()
    ]
    return sorted(found, key=lambda path: int(path.name[len(prefix) :]))


def _reap() -> None:
    for job, process in list(_PROCESSES.items()):
        if process.poll() is not None:
            del _PROCESSES[job]


def _running_count() -> int:
    return sum(
        1
        for path in jobs_root().iterdir()
        if (path / "request.json").is_file()
        and _state(path)["state"] not in FINAL_STATES
    )


def _max_jobs() -> int:
    try:
        return max(1, int(os.environ.get(MAX_JOBS_ENV, DEFAULT_MAX_JOBS)))
    except ValueError:
        return DEFAULT_MAX_JOBS


def _spawn(directory: Path) -> subprocess.Popen[bytes]:
    root = core.repo_root()
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(root / "src"), str(root), *filter(None, [env.get("PYTHONPATH")])]
    )
    env["PYTHONIOENCODING"] = "utf-8"
    log = (directory / "worker.log").open("wb")
    options: dict[str, Any] = {}
    if sys.platform == "win32":
        options["creationflags"] = (
            subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        options["start_new_session"] = True
    try:
        # stdin is NOT inherited: on an MCP server it is the protocol stream.
        return subprocess.Popen(
            [sys.executable, "-m", "runs.facade.worker", str(directory)],
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            **options,
        )
    finally:
        log.close()


def _reusable(directory: Path) -> dict[str, Any] | None:
    """Return the status of an earlier attempt that may answer this request.

    Never one whose engine was dirty: two runs on uncommitted trees are not
    known to have run the same code.
    """
    request = read_json(directory / "request.json") or {}
    if (request.get("engine") or {}).get("dirty") is not False:
        return None
    status = job_status(directory.name)
    return status if status["state"] in _REUSABLE else None


def start_run(
    instance: str,
    config: Mapping[str, Any],
    honest: Mapping[str, Any] | None = None,
    *,
    reuse: bool = True,
    document: Any = None,
    document_file: str | None = None,
) -> dict[str, Any]:
    """Start one run in the background and return its job status, or a refusal.

    The configuration is read, key-checked and PREPARED first (about a
    second), so a request the instance refuses costs no worker -- unless the
    preparation is expected to take longer than the budget
    (:mod:`runs.facade.estimate`): then the worker's own preparation is the
    check, and a refusal ends the job ``refused``. The reply carries the
    estimate either way (``estimate``). An identical
    request (instance, configuration digest, honest override, engine commit,
    and a document's digest) whose job is running or finished is answered
    with that job (``reused: true``), unless ``reuse`` is false or either tree
    was dirty.

    With a ``document`` or ``document_file`` in place of an instance
    (``instance`` empty or the document's id), ``request.json`` stores the
    document's canonical tree and conversions -- never a re-serialised parse
    -- and the worker reloads them with the reader ``prepare`` used. The job
    id is ``declared_<id>-<12 hex>-<n>``.
    """
    s = core.resolve(instance, document, document_file)
    if isinstance(s, dict):
        return s
    checked = _checked(s, config, honest)
    if isinstance(checked, dict):
        return checked
    estimate = estimate_preparation(s, checked)
    if estimate["background"]:
        payload, digest = checked.to_payload(), checked.digest()
        engine = core.engine_identity()
    else:
        prepared = core.prepare_surface(s, config, honest)
        if prepared.get("refused"):
            return dict(prepared)
        if prepared["preparation"].get("refused"):
            refusal = prepared["preparation"]
            refused = {
                "refused": True,
                "stage": refusal.get("stage"),
                "reason": refusal.get("reason"),
                "detail": refusal.get("detail"),
            }
            if prepared.get("document") is not None:
                refused["document"] = prepared["document"]
            return refused
        payload, digest = prepared["config"], prepared["config_digest"]
        engine = prepared["engine"]
    asked: dict[str, Any] = {
        "instance": s.DESCRIPTOR.id,
        "config": payload,
        "config_digest": digest,
        "honest": None if honest is None else dict(honest),
        "engine": engine,
    }
    return _start(s, asked, estimate, reuse=reuse)


def _checked(
    s: Any, config: Mapping[str, Any], honest: Mapping[str, Any] | None
) -> Any:
    """Return the configuration as read, or the refusal of it or of ``honest``."""
    checked = core.config_for(s, config)
    if isinstance(checked, dict):
        return checked
    if honest is not None:
        override = core.honest_override(honest, s.DESCRIPTOR.id)
        if isinstance(override, dict):
            return override
    return checked


def start_preparation(
    s: Any,
    config: Mapping[str, Any],
    honest: Mapping[str, Any] | None = None,
    *,
    estimate: Mapping[str, Any],
    reuse: bool = True,
) -> dict[str, Any]:
    """Start one preparation in the background and return its job status.

    For a preparation the estimate puts above the budget. ``config`` is kept
    as the caller gave it, so that the worker's ``prepare`` reads exactly what
    a synchronous one would; the job is keyed by its digest as read, and an
    identical request is answered with the same job, as for a run.
    """
    checked = _checked(s, config, honest)
    if isinstance(checked, dict):
        return checked
    asked: dict[str, Any] = {
        "kind": PREPARE,
        "instance": s.DESCRIPTOR.id,
        "config": dict(config),
        "config_digest": checked.digest(),
        "honest": None if honest is None else dict(honest),
        "engine": core.engine_identity(),
    }
    return _start(s, asked, estimate, reuse=reuse)


def _start(
    s: Any, asked: dict[str, Any], estimate: Mapping[str, Any], *, reuse: bool
) -> dict[str, Any]:
    """Create a job's directory and request, and spawn its worker."""
    engine = asked["engine"]
    instance = asked["instance"]
    label = instance
    if core.document_info(s) is not None:
        label = f"declared_{instance}"
        asked.update(
            document=s.canonical,
            document_conversions=[dict(record) for record in s.conversions],
            document_digest=s.digest,
        )
    key = core.job_key(asked)
    asked["estimate"] = {
        **estimate,
        **({} if asked.get("kind") == PREPARE else {"covers": RUN_COVERS}),
    }
    with _START_LOCK:
        _reap()
        attempts = _attempts(label, key)
        if reuse and attempts and engine["dirty"] is False:
            earlier = _reusable(attempts[-1])
            if earlier is not None:
                return {**earlier, "reused": True}
        if _running_count() >= _max_jobs():
            return {
                "refused": True,
                "stage": "jobs",
                "reason": "too_many_running_jobs",
                "detail": f"{_max_jobs()} jobs are already running "
                f"(${MAX_JOBS_ENV}); wait for one to finish or cancel one",
            }
        number = 1 + (int(attempts[-1].name.rsplit("-", 1)[1]) if attempts else 0)
        while True:
            job = f"{label}-{key[:12]}-{number}"
            directory = jobs_root() / job
            try:
                directory.mkdir()
                break
            except FileExistsError:
                number += 1
        now = time.time()
        write_json_atomic(
            directory / "request.json",
            {"job": job, **asked, "created": now},
        )
        write_json_atomic(
            directory / "status.json",
            {"state": "starting", "heartbeat": now, "started": now},
        )
        _PROCESSES[job] = _spawn(directory)
    return {**job_status(job), "reused": False}


def _state(directory: Path) -> dict[str, Any]:
    try:
        status = read_json(directory / "status.json")
    except (OSError, ValueError):
        return {
            "state": "unknown",
            "detail": "status.json is momentarily unreadable; ask again",
        }
    if status is None:
        request = read_json(directory / "request.json") or {}
        status = {"state": "starting", "heartbeat": request.get("created")}
    if status.get("state") not in FINAL_STATES:
        heartbeat = status.get("heartbeat") or 0.0
        if time.time() - float(heartbeat) > STALE_AFTER_S:
            status = {
                **status,
                "state": "lost",
                "detail": "the worker stopped without a final status; see worker.log",
            }
    return dict(status)


def _last_events(directory: Path, count: int = 5) -> list[Any]:
    path = directory / "events.jsonl"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-count:]
    except OSError:
        return []
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events


def job_status(job: str) -> dict[str, Any]:
    """Return one job's state, its latest progress and the files it has."""
    directory = job_directory(job)
    _reap()
    status = _state(directory)
    try:
        request = read_json(directory / "request.json") or {}
    except (OSError, ValueError):
        request = {}
    files = {
        name: str(directory / name)
        for name in (
            "record.json",
            *core.REPORT_FILES.values(),
            SUMMARY_FILE,
            PREPARATION_FILE,
            "events.jsonl",
            "worker.log",
        )
        if (directory / name).is_file()
    }
    kind = request.get("kind") or "run"
    reply: dict[str, Any] = {
        "job": job,
        "kind": kind,
        "instance": request.get("instance"),
        "document": _document_named(request),
        "config_digest": request.get("config_digest"),
        **status,
        "elapsed_s": round(
            float(status.get("finished") or time.time())
            - float(status.get("started") or request.get("created") or time.time()),
            1,
        ),
        "recent_events": []
        if status["state"] in FINAL_STATES
        else _last_events(directory),
        "directory": str(directory),
        "files": files,
    }
    estimate = request.get("estimate")
    if isinstance(estimate, Mapping):
        # THE EXPECTED RUNTIME, WITH ITS REASON, BESIDE THE ELAPSED ONE:
        # what the user was told before waiting, kept in view.
        reply["estimate"] = {
            key: estimate.get(key)
            for key in (
                "expected_seconds",
                "duration",
                "why",
                "extrapolated",
                "capped",
                "advice",
                "covers",
                "basis",
            )
            if estimate.get(key) is not None
        }
    if kind == PREPARE:
        reply["next"] = (
            "prepare(job=...) returns the preparation summary"
            if status["state"] in FINAL_STATES
            else "poll run_status(job) until the state is final, then prepare(job=...)"
        )
    return reply


def write_preparation(
    envelope: Mapping[str, Any], path: Path | None = None
) -> dict[str, Any]:
    """Write a preparation's envelope and return its summary, naming the file.

    The one writer for both paths. A synchronous ``prepare`` writes the
    envelope to ``<jobs>/preparations/<stem>.json``; a preparation job writes
    it into its own directory (``path``), where a later ``prepare`` of the
    same request cannot overwrite what ``prepare(job=..., part=...)`` serves.
    The summary is the same but for ``file``.
    """
    spill = path or (
        jobs_root() / "preparations" / f"{core.preparation_file_stem(envelope)}.json"
    )
    spill.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(spill, envelope)
    return {**core.preparation_summary(envelope), "file": str(spill)}


def preparation_result(job: str) -> dict[str, Any]:
    """Return a preparation job's summary once finished, else its status.

    ``{"summary": ...}`` when the worker wrote one (a preparation the engine
    refused has a summary with ``refused: true``, as a synchronous ``prepare``
    returns it); otherwise ``{"status": ...}``: not final yet, or a refusal of
    the input, an error, a cancel. A run's job is no preparation job
    (``KeyError``).
    """
    directory = job_directory(job)
    request = read_json(directory / "request.json") or {}
    if request.get("kind") != PREPARE:
        raise KeyError(f"{job!r} is a run, not a preparation; ask get_report")
    status = job_status(job)
    if status["state"] in FINAL_STATES and (directory / SUMMARY_FILE).is_file():
        return {"summary": read_json(directory / SUMMARY_FILE)}
    return {"status": status}


def _document_named(request: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return a job's document as every reply names it: ``{id, digest}`` or ``None``."""
    digest = request.get("document_digest")
    if digest is None:
        return None
    return {"id": request.get("instance"), "digest": digest}


def cancel_job(job: str) -> dict[str, Any]:
    """Ask a job to stop; a finished job is left as it is.

    The worker checks for ``cancel.request`` every second and stops with the
    state ``cancelled`` and no record -- unless it has begun writing its
    record, when it finishes as it would have (a record half-written by a
    cancel would be worse than a cancel that came too late). Nothing here
    terminates the process from outside.
    """
    directory = job_directory(job)
    if _state(directory)["state"] in FINAL_STATES:
        return job_status(job)
    (directory / "cancel.request").write_text(str(time.time()), encoding="utf-8")
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if _state(directory)["state"] in FINAL_STATES:
            break
        time.sleep(0.25)
    return job_status(job)


def list_jobs(limit: int = 20) -> list[dict[str, Any]]:
    """Return the most recent jobs, newest first, without their events."""
    _reap()
    directories = sorted(
        (path for path in jobs_root().iterdir() if (path / "request.json").is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[: max(1, limit)]
    summaries = []
    for directory in directories:
        status = _state(directory)
        try:
            request = read_json(directory / "request.json") or {}
        except (OSError, ValueError):
            request = {}
        summaries.append(
            {
                "job": directory.name,
                "instance": request.get("instance"),
                "document": _document_named(request),
                "kind": request.get("kind") or "run",
                "state": status.get("state"),
                "key_length": status.get("key_length"),
                "created": request.get("created"),
            }
        )
    return summaries
