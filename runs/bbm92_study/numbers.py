"""The numbers the whitepaper's prose and hand-set figures quote, read from the data.

::

    python -m runs.bbm92_study.numbers [--data DIR] [--headline SWEEP/POINT]

``--data`` defaults to ``runs/bbm92_study/data``, ``--headline`` to
``loss/realistic-c1e6-L10``.

Prints one JSON document. The whitepaper types its numbers into prose and into
the hand-set receiver-ladder figure, where no generator rewrites them, so after
a rerun each must be compared with the data; this is the data's side of that
comparison (the whitepaper's checker reads this JSON and reports where its text
disagrees). Every value names the file it was read from.

- ``headline``: the study's headline point (10 dB, 10^6 expected coincidences,
  realistic devices): key length, rounds, key rate per round, per expected
  coincidence, the security parameter, lambda_EC, alpha, and the premises its
  key-rate report lists (all of them, and those whose failure can break
  security), read from the report built from the point's record, so they count
  what a reader of that report sees;
- ``ladder``: the key rate per round of every rung of each block of the ladder
  sweep (the receiver-ladder figure's bars), in rung order;
- ``engine``: the commits the records name, with whether any was dirty.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from certiqs_key.runs.report import build_report, select

__all__ = ["DEFAULT_DATA", "DEFAULT_HEADLINE", "main", "numbers"]

DEFAULT_DATA = Path("runs/bbm92_study/data")
DEFAULT_HEADLINE = "loss/realistic-c1e6-L10"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(text: str) -> float | None:
    return float(text) if text not in ("", "None") else None


def _headline(data: Path, point: str) -> dict[str, Any]:
    sweep, _, name = point.partition("/")
    summary = data / sweep / "summary.csv"
    row = next((r for r in _rows(summary) if r["point"] == name), None)
    if row is None:
        raise SystemExit(f"{summary}: no point {name!r}")
    record_path = data / sweep / name / "record.json.gz"
    with gzip.open(record_path, "rt", encoding="utf-8") as handle:
        record = json.load(handle)
    report = build_report(record)
    summary_section = select(report, "summary")
    families = [f for group in select(report, "assumptions")["groups"]
                for f in group["families"]]
    epsilon = next(t["value"] for t in summary_section["guarantee"]["terms"]
                   if t["symbol"] == "ε")
    key_length = int(row["key_length"])
    rounds = int(row["rounds"])
    coincidences = float(row["expected_coincidences"])
    return {
        "point": point,
        "summary": summary.as_posix(),
        "record": record_path.as_posix(),
        "key_length": key_length,
        "rounds": rounds,
        "rate_per_round": key_length / rounds,
        "expected_coincidences": coincidences,
        "rate_per_coincidence": key_length / coincidences,
        "epsilon": epsilon,
        "lambda_ec": _float(row["lambda_ec"]),
        "alpha": _float(row["alpha"]),
        # A family is its head and its members, each a premise the report counts.
        "premises": sum(1 + len(f.get("members") or []) for f in families),
        "premises_security": summary_section["consequences"]["security"],
    }


def _ladder(data: Path) -> dict[str, Any]:
    summary = data / "ladder" / "summary.csv"
    blocks: dict[str, list[float | None]] = {}
    rounds: dict[str, int] = {}
    for row in _rows(summary):
        block = row["point"].split("-", 1)[0]
        blocks.setdefault(block, []).append(_float(row["rate_per_round"]))
        rounds.setdefault(block, int(row["rounds"]))
    return {"summary": summary.as_posix(), "rate_per_round": blocks, "rounds": rounds}


def _engine(data: Path) -> dict[str, Any]:
    commits: set[str] = set()
    dirty = False
    for summary in sorted(data.glob("*/summary.csv")):
        for row in _rows(summary):
            if row.get("git_commit"):
                commits.add(row["git_commit"])
            dirty = dirty or row.get("git_dirty") == "True"
    return {"commits": sorted(commits), "any_dirty": dirty}


def numbers(data: Path = DEFAULT_DATA,
            headline: str = DEFAULT_HEADLINE) -> dict[str, Any]:
    """Return the quoted numbers of the study data under ``data``."""
    return {
        "data": data.as_posix(),
        "headline": _headline(data, headline),
        "ladder": _ladder(data),
        "engine": _engine(data),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Print the numbers as JSON; return the exit status."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--headline", default=DEFAULT_HEADLINE,
                        help="<sweep>/<point> of the headline run")
    args = parser.parse_args(argv)
    result: Mapping[str, Any] = numbers(args.data, args.headline)
    json.dump(result, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
