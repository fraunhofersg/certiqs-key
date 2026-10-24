"""Run paired solver cases with one numerical worker and hard resource caps.

Motivation: comparable timing includes failures and setup, and a stalled solver
must not consume the remaining experiment budget. Ordinary JSON records and git
provide provenance; this runner creates no acceptance or security mechanism.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import site
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .cases import cases
from .common import ROOT, THREAD_ENV, git_revision, memory_snapshot, write_json


def warm_task(task: dict[str, Any], root: Path) -> dict[str, Any]:
    """Resolve one planned predecessor without bypassing worker seed admission."""
    seed: str | None = None
    if "warm_predecessor" not in task:
        reason = "disabled"
    elif task["warm_predecessor"] is None:
        reason = "chain_first"
    else:
        predecessor = root / task["warm_predecessor"]
        completion = predecessor / "completion.json"
        if not completion.is_file():
            reason = "predecessor_missing_completion"
        elif (
            json.loads(completion.read_text(encoding="utf-8")).get("status")
            != "completed"
        ):
            reason = "predecessor_not_completed"
        elif not (predecessor / "final-iterate.json").is_file():
            reason = "predecessor_missing_final_iterate"
        else:
            seed = str((predecessor / "final-iterate.json").resolve())
            reason = "completed_predecessor"
    return {**task, "warm_start": seed, "warm_start_reason": reason}


def execute(
    command: list[str], folder: Path, seconds: float, environment: dict[str, str]
) -> dict[str, Any]:
    """Run a child in a hidden window; kill its tree when the deadline expires."""
    started = time.perf_counter()
    with (folder / "worker.log").open("w", encoding="utf-8", newline="\n") as log:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=0x08000000 if os.name == "nt" else 0,
            start_new_session=os.name != "nt",
        )
        try:
            code = process.wait(timeout=seconds)
            status = "completed" if code == 0 else "failed"
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":
                # The worker owns a kill-on-close job, so terminating the
                # direct interpreter also terminates any descendants. Avoid
                # taskkill, whose cross-process access can be sandbox-blocked.
                process.kill()
            else:
                import signal

                os.killpg(process.pid, signal.SIGKILL)
            code = process.wait(timeout=10)
            status = "timeout"
        except BaseException:
            if sys.platform == "win32":
                process.kill()
            else:
                import signal

                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)
            raise
    return {
        "status": status,
        "returncode": code,
        "elapsed_seconds": time.perf_counter() - started,
        "process_cap_seconds": seconds,
    }


def main(argv: list[str] | None = None) -> int:
    """Run an explicit, serial, resumable matrix and retain every outcome."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("fast", "slow"), default="fast")
    parser.add_argument("--cases", type=Path, help="explicit JSON case list")
    parser.add_argument("--methods", nargs="+", default=["fw", "pairwise", "auto"])
    parser.add_argument(
        "--variants", type=Path, help="JSON variants with optional plugin"
    )
    parser.add_argument("--only", nargs="*", help="exact case IDs")
    parser.add_argument("--seconds", type=float)
    parser.add_argument("--process-seconds", type=float)
    parser.add_argument("--total-seconds", type=float, default=7200)
    parser.add_argument("--memory-gib", type=float, default=3.5)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--order-seed", type=int, default=20261018)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--warm-chain",
        action="store_true",
        help="seed each variant from its preceding ordered case within each repeat",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    seconds = (
        args.seconds
        if args.seconds is not None
        else (30.0 if args.profile == "fast" else 180.0)
    )
    process_seconds = (
        args.process_seconds
        if args.process_seconds is not None
        else (max(120.0, 3 * seconds + 60))
    )
    if args.repeats < 1 or any(
        not math.isfinite(n) or n <= 0
        for n in (seconds, process_seconds, args.total_seconds, args.memory_gib)
    ):
        parser.error("repeats and resource limits must be positive and finite")
    chosen = (
        json.loads(args.cases.read_text(encoding="utf-8"))
        if args.cases
        else cases(args.profile)
    )
    if args.only:
        missing = set(args.only) - {c["id"] for c in chosen}
        if missing:
            parser.error(f"unknown case IDs: {sorted(missing)}")
        chosen = [c for c in chosen if c["id"] in args.only]
    if any(
        c.get("target_bound") is not None
        and (c.get("target_key_length") is not None or c.get("alpha_search"))
        for c in chosen
    ):
        parser.error("bound targets require fixed alpha and no key target")
    variants = (
        json.loads(args.variants.read_text(encoding="utf-8"))
        if args.variants
        else [{"id": m, "method": m, "oracle": "qics"} for m in args.methods]
    )
    for variant in variants:
        for kind in ("plugin", "capture"):
            if variant.get(kind):
                variant[kind] = str(Path(variant[kind]).resolve())
    for group in (chosen, variants):
        names = [v["id"] for v in group]
        if len(names) != len(set(names)) or any(
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", n) is None for n in names
        ):
            parser.error("case/variant IDs must be unique plain path components")
    tasks = []
    rng = random.Random(args.order_seed)
    for repeat in range(args.repeats):
        predecessors: dict[str, str] = {}
        for case in chosen:
            ordered = variants[:]
            rng.shuffle(ordered)
            for variant in ordered:
                name = f"{case['id']}--{variant['id']}--r{repeat}"
                task = {
                    "id": name,
                    "case": case,
                    "variant": variant,
                    "seconds": seconds,
                    "memory_gib": args.memory_gib,
                    "repeat": repeat,
                }
                if args.warm_chain:
                    task["warm_predecessor"] = predecessors.get(variant["id"])
                    predecessors[variant["id"]] = name
                tasks.append(task)
    if len({t["id"] for t in tasks}) != len(tasks):
        parser.error("case and variant names produce duplicate task IDs")
    manifest = {
        "revision": git_revision(),
        "plugin_sources": {
            v[kind]: Path(v[kind]).read_text(encoding="utf-8")
            for v in variants
            for kind in ("plugin", "capture")
            if v.get(kind)
        },
        "profile": args.profile,
        "tasks": tasks,
        "process_seconds": process_seconds,
        "order_seed": args.order_seed,
        "total_seconds": args.total_seconds,
        "warm_chain": args.warm_chain,
        "resources": memory_snapshot(),
    }
    if args.dry_run:
        print(
            json.dumps(
                {
                    "attempts": len(tasks),
                    "cases": len(chosen),
                    "maximum_seconds": min(
                        args.total_seconds, len(tasks) * process_seconds
                    ),
                    "memory_gib": args.memory_gib,
                    "task_ids": [t["id"] for t in tasks],
                    "warm_chain": args.warm_chain,
                    "warm_predecessors": {
                        t["id"]: t["warm_predecessor"]
                        for t in tasks
                        if "warm_predecessor" in t
                    },
                },
                indent=2,
            )
        )
        return 0
    out = args.out.resolve()
    if (out / "manifest.json").exists():
        previous = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        if (
            not args.resume
            or previous.get("warm_chain", False) != args.warm_chain
            or any(
                previous[k] != manifest[k]
                for k in (
                    "revision",
                    "tasks",
                    "process_seconds",
                    "plugin_sources",
                    "total_seconds",
                    "order_seed",
                )
            )
        ):
            parser.error(
                "existing run requires --resume at the same revision/configuration"
            )
    elif out.exists() and any(out.iterdir()):
        parser.error("new output must be empty")
    else:
        write_json(out / "manifest.json", manifest)
    environment = {
        **os.environ,
        **THREAD_ENV,
        "PYTHONPATH": os.pathsep.join(
            [str(ROOT / "src"), str(ROOT), *site.getsitepackages()]
        ),
        "PYTHONUNBUFFERED": "1",
    }
    charged = 0.0
    for task in tasks:
        folder = out / task["id"]
        completion = folder / "completion.json"
        if completion.exists():
            charged += json.loads(completion.read_text())["elapsed_seconds"]
            continue
        # A parent interruption cannot silently rerun a partial attempt.
        if (folder / "task.json").exists():
            saved_task = json.loads((folder / "task.json").read_text(encoding="utf-8"))
            interrupted_cap = saved_task.get("process_cap_seconds", process_seconds)
            write_json(
                completion,
                {
                    "status": "interrupted",
                    "returncode": None,
                    "elapsed_seconds": interrupted_cap,
                    "process_cap_seconds": interrupted_cap,
                },
            )
            charged += interrupted_cap
            continue
        remaining = args.total_seconds - charged
        if remaining <= 0:
            print("aggregate allowance reached", flush=True)
            break
        cap = min(process_seconds, remaining)
        task = {**warm_task(task, out), "process_cap_seconds": cap}
        for kind in ("plugin", "capture"):
            if task["variant"].get(kind):
                snapshot = out / "plugins" / task["variant"]["id"] / (kind + ".py")
                snapshot.parent.mkdir(parents=True, exist_ok=True)
                snapshot.write_text(
                    manifest["plugin_sources"][task["variant"][kind]],
                    encoding="utf-8",
                    newline="\n",
                )
                task = {**task, kind + "_snapshot": str(snapshot)}
        write_json(folder / "task.json", task)
        print("starting " + task["id"], flush=True)
        # Windows venv python.exe is a redirector that starts another process.
        # Use the base interpreter with this environment's explicit site path
        # so the watchdog owns the actual worker handle, not the redirector.
        interpreter = getattr(sys, "_base_executable", sys.executable)
        result = execute(
            [
                interpreter,
                "-m",
                "runs.solver_benchmark.worker",
                str(folder / "task.json"),
            ],
            folder,
            cap,
            {**environment, **task["variant"].get("environment", {}), **THREAD_ENV},
        )
        write_json(completion, result)
        charged += result["elapsed_seconds"]
        print(json.dumps({"id": task["id"], **result}), flush=True)
    print(f"total worker wall seconds: {charged:.3f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
