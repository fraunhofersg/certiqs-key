"""Small benchmark I/O and process limits.

Motivation: failed, nonfinite and interrupted attempts must remain visible, and
a high-cutoff experiment must not consume unbounded memory on the user's host.
"""

from __future__ import annotations

import ctypes
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
THREAD_ENV = dict.fromkeys(
    (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "BLIS_NUM_THREADS",
    ),
    "1",
)
_JOB_HANDLE: Any = None


def clean(value: Any) -> Any:
    """Keep nonfinite diagnostics explicit without nonstandard JSON numbers."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    return value


def write_json(path: Path, value: Any) -> None:
    """Replace a complete small result; a crash leaves its previous version."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(clean(value), indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def git_revision() -> str:
    """Identify the checkout supplying this runner."""
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def finite(value: Any) -> float | None:
    """Read a finite scalar, preserving absent/invalid results as absent."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def clarabel_linear_info(problem: Any) -> dict[str, Any]:
    """Observe native threads after a successful explicitly capped CVXPY solve.

    BLAS environment variables do not constrain Clarabel's Rayon pool. This
    optional diagnostic reads the installed adapter's private cache; version
    drift reports unavailable rather than changing candidate admission.
    Never call it after a solve exception, when a cache may contain old data.
    """
    result: dict[str, Any] = {"available": False, "requested_max_threads": 1}
    try:
        native = problem._solver_cache.get("CLARABEL")
        if native is None:
            result["unavailable_reason"] = "native_solver_not_cached"
            return result
        linear = native.get_info().linsolver
        settings = native.get_settings()
        result.update(
            available=True,
            name=str(linear.name),
            threads=int(linear.threads),
            direct=bool(linear.direct),
            nnzA=int(linear.nnzA),
            nnzL=int(linear.nnzL),
            effective_max_threads=int(settings.max_threads),
        )
    except Exception as error:
        result["unavailable_reason"] = f"{type(error).__name__}: {error}"
    return result


def memory_limit(gib: float) -> dict[str, Any]:
    """Apply an OS process memory cap before importing numerical libraries.

    Windows uses an unnamed nested job with process and aggregate committed
    memory limits. Keep its handle alive for this worker's lifetime. Failure
    to install the cap aborts the worker instead of silently running unbounded.
    POSIX uses RLIMIT_AS. This is an execution limit, never a proof tolerance.
    """
    if not math.isfinite(gib) or gib <= 0:
        raise ValueError("memory_gib must be finite and positive")
    limit = int(gib * 1024**3)
    if sys.platform != "win32":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        return {"kind": "RLIMIT_AS", "bytes": limit}
    else:
        from ctypes import wintypes as w

        class Basic(ctypes.Structure):
            _fields_ = [
                ("process_time", ctypes.c_int64),
                ("job_time", ctypes.c_int64),
                ("flags", w.DWORD),
                ("min_ws", ctypes.c_size_t),
                ("max_ws", ctypes.c_size_t),
                ("active", w.DWORD),
                ("affinity", ctypes.c_size_t),
                ("priority", w.DWORD),
                ("scheduling", w.DWORD),
            ]

        class Limits(ctypes.Structure):
            _fields_ = [
                ("basic", Basic),
                ("io", ctypes.c_uint64 * 6),
                ("process_memory", ctypes.c_size_t),
                ("job_memory", ctypes.c_size_t),
                ("peak_process", ctypes.c_size_t),
                ("peak_job", ctypes.c_size_t),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        kernel.CreateJobObjectW.restype = w.HANDLE
        kernel.SetInformationJobObject.argtypes = [
            w.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            w.DWORD,
        ]
        kernel.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        kernel.GetCurrentProcess.restype = w.HANDLE
        handle = kernel.CreateJobObjectW(None, None)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = Limits()
        limits.basic.flags = 0x100 | 0x200 | 0x2000
        limits.process_memory = limits.job_memory = limit
        if not kernel.SetInformationJobObject(
            handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()):
            raise ctypes.WinError(ctypes.get_last_error())
        global _JOB_HANDLE
        _JOB_HANDLE = handle
        return {"kind": "Windows job committed memory", "bytes": limit}


def memory_snapshot() -> dict[str, Any]:
    """Record available RAM and this process's peak working set where available."""
    if sys.platform != "win32":
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return {"peak_rss_bytes": peak * (1 if sys.platform == "darwin" else 1024)}
    else:
        from ctypes import wintypes as w

        class Status(ctypes.Structure):
            _fields_ = [("length", w.DWORD), ("load", w.DWORD)] + [
                (n, ctypes.c_uint64)
                for n in (
                    "total",
                    "available",
                    "total_page",
                    "available_page",
                    "virtual",
                    "available_virtual",
                    "extended",
                )
            ]

        class Counters(ctypes.Structure):
            _fields_ = [("cb", w.DWORD), ("faults", w.DWORD)] + [
                (n, ctypes.c_size_t)
                for n in (
                    "peak",
                    "working",
                    "peak_paged",
                    "paged",
                    "peak_nonpaged",
                    "nonpaged",
                    "pagefile",
                    "peak_pagefile",
                    "private",
                )
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = w.HANDLE
        status, counters = Status(), Counters()
        status.length, counters.cb = ctypes.sizeof(status), ctypes.sizeof(counters)
        kernel.GlobalMemoryStatusEx(ctypes.byref(status))
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [w.HANDLE, ctypes.c_void_p, w.DWORD]
        ok = psapi.GetProcessMemoryInfo(
            kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb
        )
        return {
            "total_ram_bytes": status.total,
            "available_ram_bytes": status.available,
            "peak_rss_bytes": counters.peak if ok else None,
            "peak_commit_bytes": counters.peak_pagefile if ok else None,
        }
