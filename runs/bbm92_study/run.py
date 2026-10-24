"""Run the BBM92 study's sweeps, resumably, one folder per point.

::

    python -m runs.bbm92_study.run loss qber --workers 3
    python -m runs.bbm92_study.run alpha --only n1e8-a1em03 --out build/bbm92-study

For each point of each named sweep (:mod:`runs.bbm92_study.sweeps`) the runner:

1. builds the configuration from the bbm92 document's defaults and the point's
   overrides;
2. estimates lambda_EC from the honest model where the point asks for it
   (:func:`certiqs_key.runs.error_correction.with_estimated_lambda_ec`);
3. opts the run into the outer alpha search (``RunConfig.alpha_search``, record
   schema 0.24.0), so the record carries the search and every evaluation; or
   runs at the point's fixed alpha, or at the alpha a sibling point's record
   chose (``Point.alpha_from``);
4. writes ``<out>/<sweep>/<point>/``: ``record.json.gz`` (the chosen run's
   record), ``point.json``, ``lambda-ec.json`` and, for a borrowed alpha,
   ``alpha-from.json``.

A point whose ``record.json.gz`` exists is skipped, so an interrupted sweep
resumes where it stopped; delete a point's folder to rerun it. Records go to
the git-ignored ``build/`` by default. What gets committed is the summary
(:mod:`runs.bbm92_study.summarize`) and the records, under
``runs/bbm92_study/data/``.

A sweep marked ``blocked`` in :mod:`runs.bbm92_study.sweeps` is refused unless
``--allow-blocked`` is given, and then only for a look at the current tree,
never for data to keep.

Every point runs in a worker process with its own scratch directory for the
runner's bundles; the scratch is deleted once the point's record is written.
The figures' numbers must come from one clean commit: check the records'
``provenance.git_dirty`` (the summary carries it).
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

__all__ = ["main", "run_point"]

CREATED_BY = "runs.bbm92_study"
DEFAULT_OUT = Path("build/bbm92-study")


def run_point(sweep_name: str, point_id: str, out: str) -> dict[str, Any]:
    """Run one point and write its folder; return a one-line summary."""
    from instances import surface_of

    from certiqs_key.runs.alpha_search import point_from_record
    from certiqs_key.runs.config import AlphaSearchSettings
    from certiqs_key.runs.error_correction import with_estimated_lambda_ec
    from certiqs_key.runs.pipeline import Preparation
    from certiqs_key.runs.record import record_run
    from certiqs_key.runs.surface import InstanceIdentity
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle
    from runs.bbm92_study.sweeps import SWEEPS, configure

    point = next(p for p in SWEEPS[sweep_name].points() if p.id == point_id)
    folder = Path(out) / sweep_name / point.id
    folder.mkdir(parents=True, exist_ok=True)
    scratch = folder / ".scratch"
    started = time.perf_counter()
    surface = surface_of("bbm92")
    identity = InstanceIdentity(surface.DESCRIPTOR, tuple(surface.PARAMETERS))
    config = configure(surface.default_config(), point)
    _dump(folder / "point.json", point.as_payload())

    if point.f_ec is not None:
        preparation = surface.preparation(config)
        if isinstance(preparation, Preparation):
            config, estimate = with_estimated_lambda_ec(
                config, preparation, f_ec=point.f_ec
            )
            _dump(folder / "lambda-ec.json", estimate.as_payload())
        else:
            _dump(
                folder / "lambda-ec.json",
                {"unavailable": f"the preparation refused: {preparation!r}"[:2000]},
            )

    runner = surface.runner(QicsSectorChoiOracle(), scratch, created_by=CREATED_BY)
    if point.alpha_from is not None:
        alpha = _chosen_alpha(folder.parent / point.alpha_from / "record.json.gz")
        if alpha is None:
            raise RuntimeError(
                f"{point.alpha_from} chose no alpha; {point.id} cannot run"
            )
        config = config.with_(alpha=alpha)
        _dump(folder / "alpha-from.json", {"from": point.alpha_from, "alpha": alpha})
    elif point.alpha is None:
        # Every alpha refused: the runner returns the first evaluation's
        # outcome, refusal and all, with the search attached, so the point
        # still has a record that says why.
        config = config.with_(alpha_search=AlphaSearchSettings())
    outcome = runner(config, 0)
    record = record_run(outcome, config, created_by=CREATED_BY, instance=identity)
    chosen = point_from_record(record, config)

    _write_gz(folder / "record.json.gz", record.as_dict())
    shutil.rmtree(scratch, ignore_errors=True)
    return {
        "sweep": sweep_name,
        "point": point.id,
        "key_length": chosen.key_length,
        "reason": chosen.reason,
        "seconds": round(time.perf_counter() - started, 1),
    }


def _chosen_alpha(path: Path) -> float | None:
    """Return the alpha a point's record solved at, or ``None`` if it refused.

    Where the point's alpha search found no alpha with a positive key length
    (record 0.40.0, the alpha child's status ``no_positive_key``), the record
    is the evaluation with the largest h_low, so this returns that alpha,
    which the search did not choose.
    """
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)["payload"]
    alpha = (payload.get("stages", {}).get("key_rate") or {}).get("alpha")
    return None if alpha is None else float(alpha)


def _dump(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_gz(path: Path, payload: Any) -> None:
    """Write ``payload`` gzipped, with no file name or time in the header."""
    data = (json.dumps(payload, indent=1, sort_keys=True) + "\n").encode("utf-8")
    partial = path.with_suffix(".partial")
    with (
        partial.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped,
    ):
        zipped.write(data)
    partial.replace(path)


def main(argv: list[str] | None = None) -> int:
    """Run the named sweeps; see the module docstring."""
    from runs.bbm92_study.sweeps import SWEEPS

    parser = argparse.ArgumentParser(prog="python -m runs.bbm92_study.run")
    parser.add_argument("sweeps", nargs="+", choices=sorted(SWEEPS))
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--only", nargs="*", default=None, help="point ids to run")
    parser.add_argument("--limit", type=int, default=None, help="at most this many")
    parser.add_argument("--allow-blocked", action="store_true")
    args = parser.parse_args(argv)

    todo: list[tuple[str, str]] = []
    for name in args.sweeps:
        sweep = SWEEPS[name]
        if sweep.blocked and not args.allow_blocked:
            print(f"{name}: blocked ({sweep.blocked}); skipped", file=sys.stderr)
            continue
        for point in sweep.points():
            if args.only and point.id not in args.only:
                continue
            if (args.out / name / point.id / "record.json.gz").exists():
                continue
            todo.append((name, point.id))
    if args.limit is not None:
        todo = todo[: args.limit]
    print(f"{len(todo)} point(s) to run with {args.workers} worker(s)", flush=True)
    failures = 0
    # Points that take alpha from a sibling run after every other point, so
    # the sibling's search has finished.
    dependent = {
        (s.name, p.id)
        for s in SWEEPS.values()
        for p in s.points()
        if p.alpha_from is not None
    }
    phases = [
        [t for t in todo if t not in dependent],
        [t for t in todo if t in dependent],
    ]
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for phase in phases:
            futures = {
                pool.submit(run_point, name, pid, str(args.out)): (name, pid)
                for name, pid in phase
            }
            for future in as_completed(futures):
                name, pid = futures[future]
                try:
                    print(json.dumps(future.result()), flush=True)
                except Exception as error:  # reported; the sweep goes on
                    failures += 1
                    print(
                        json.dumps(
                            {"sweep": name, "point": pid, "error": repr(error)[:500]}
                        ),
                        flush=True,
                    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
