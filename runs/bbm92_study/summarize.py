"""Condense a sweep's point folders into one CSV, the figures' only input.

::

    python -m runs.bbm92_study.summarize loss qber --to runs/bbm92_study/data

One row per point, in the sweep's declared order. A point not yet run is a row
with ``status = missing``, so a partial sweep is visible as partial. The columns:

- the point's axis labels (``loss_db``, ``qber``, ``rounds``, ...), as declared;
- the result: ``key_length``, ``rate_per_round``, ``h_lb``, ``h_low``, ``gap``
  (the record's ``frank_wolfe_gap``: the gap of the candidate h_lb came from;
  h_low may belong to another candidate, so ``h_low - h_lb`` is not a gap),
  ``first_order_minus_estimate`` (the record's; positive where h_lb exceeds the
  returned estimate, which can happen because the estimate's point is only in
  the relaxed feasible set),
  ``alpha`` (the alpha the chosen run used: the record's ``stages.key_rate.alpha``,
  not ``config.parameters.alpha``, which keeps the declared default),
  ``alpha_searched``, ``lambda_ec``, ``reason`` and ``refusal``;
- the solve: ``termination`` (the portfolio's last attempt, so read it with
  ``gap``), ``solver_seconds`` and ``oracle``, the linear oracle a point
  chose (empty for the default, QICS);
- the counts a practitioner quotes: ``p_coincidence`` and
  ``expected_coincidences`` (both stations register a click, single or multiple,
  in a round), and ``p_pass`` and ``expected_sifted`` (rounds passing sifting),
  computed exactly from the honest raw joint distribution;
- the snap disclosure: ``rests_on_a_snap``, the run's decision whether some
  moved block or emission sector rests on A-SNAP
  (``snaps.reference_companion``), so the route variants are readable from the
  table, and
  ``evaluated_off_snap_count``, the blocks whose bound was evaluated on the
  receiver's reference rather than on their snap;
- the reference bracket (``stages.key_rate.reference_bracket``, record 0.27.0):
  ``bracket_status`` (``counted``, ``withdrawn`` or ``not_evaluated``) and the
  snapped run's own bound, ``snapped_h_lb`` and ``snapped_key_length``, which
  the record keeps as a diagnostic beside the key length it reports;
- ``assumption_ids`` and ``git_commit`` / ``git_dirty``.

The coincidence count reads bbm92's outcome spelling: a raw outcome is
``x|<alice letter>__<bob letter>``, where Alice's letter is ``(<outcome>,<role>)``
and a no-click is ``nc``. It is this study's reading of this instance and is
not an engine output.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

from runs.bbm92_study.run import DEFAULT_OUT
from runs.bbm92_study.sweeps import SWEEPS, Point

__all__ = ["COLUMNS", "coincidence_probability", "main", "row", "summarize"]

DEFAULT_TO = Path("runs/bbm92_study/data")

RESULT_COLUMNS = (
    "status",
    "key_length",
    "rate_per_round",
    "h_lb",
    "h_low",
    "gap",
    "first_order_minus_estimate",
    "alpha",
    "alpha_searched",
    "lambda_ec",
    "f_ec",
    "reason",
    "refusal",
    "termination",
    "solver_seconds",
    "oracle",
    "p_coincidence",
    "expected_coincidences",
    "p_pass",
    "expected_sifted",
    "route",
    "rests_on_a_snap",
    "evaluated_off_snap_count",
    "bracket_status",
    "snapped_h_lb",
    "snapped_key_length",
    "assumption_ids",
    "git_commit",
    "git_dirty",
)
#: The leading columns; the labels of each sweep come between them and the rest.
COLUMNS = ("sweep", "point")


def coincidence_probability(raw_joint: Mapping[str, str]) -> Fraction:
    """Return the honest probability that both stations click, exactly."""
    total = Fraction(0)
    for pair, value in raw_joint.items():
        _x, _, v = pair.partition("|")
        alice, _, bob = v.partition("__")
        alice_outcome = alice.strip("()").split(",")[0]
        if alice_outcome != "nc" and bob != "nc":
            total += Fraction(value)
    return total


def _searched(payload: Mapping[str, Any]) -> bool:
    """Whether the record's solve stage says the outer search chose its alpha."""
    for stage in (payload.get("composition_flow") or {}).get("stages", []):
        for child in stage.get("children", []):
            if child.get("name") == "alpha" and (child.get("detail") or {}).get(
                "searched"
            ):
                return True
    return False


def row(sweep: str, point: Point, folder: Path) -> dict[str, Any]:
    """Return one point's CSV row from its folder."""
    out: dict[str, Any] = {"sweep": sweep, "point": point.id, **dict(point.labels)}
    path = folder / "record.json.gz"
    if not path.exists():
        out["status"] = "missing"
        return out
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        record = json.load(handle)
    payload = record.get("payload", record)
    stages: Mapping[str, Any] = payload.get("stages", {}) or {}
    key_rate: Mapping[str, Any] = stages.get("key_rate") or {}
    out["status"] = "refused" if not key_rate else "ok"
    out["refusal"] = _refusal(stages)
    out["alpha_searched"] = _searched(payload) or (
        # Drafts run before the search was wired (record 0.24.0) kept it
        # beside the record instead.
        (folder / "alpha-search.json").exists()
    )
    lam = _read(folder / "lambda-ec.json")
    out["f_ec"] = lam.get("f_ec")
    config = payload.get("config", {})
    out["lambda_ec"] = config.get("parameters", {}).get("lambda_ec")
    out["route"] = config.get("device", {}).get("route")
    # Under solver.advanced since record 0.43.0; a study record written
    # before carries it beside the method.
    solver = config.get("solver") or {}
    out["oracle"] = (solver.get("advanced") or {}).get("oracle", solver.get("oracle"))
    if key_rate:
        h_lb, h_low = key_rate.get("h_lb"), key_rate.get("h_low")
        search = key_rate.get("search_report") or {}
        out.update(
            key_length=key_rate.get("key_length"),
            rate_per_round=key_rate.get("rate_per_round"),
            h_lb=h_lb,
            h_low=h_low,
            gap=key_rate.get("frank_wolfe_gap"),
            first_order_minus_estimate=key_rate.get("first_order_minus_estimate"),
            alpha=key_rate.get("alpha"),
            reason=key_rate.get("key_length_reason_code"),
            termination=search.get("termination"),
            solver_seconds=search.get("solver_seconds"),
            assumption_ids=" ".join(key_rate.get("assumption_ids") or ()),
        )
    acceptance = stages.get("acceptance_construction") or {}
    raw = acceptance.get("raw_joint_distribution")
    rounds = int(point.rounds)
    if raw:
        p = coincidence_probability(raw)
        out["p_coincidence"] = float(p)
        out["expected_coincidences"] = float(p * rounds)
    if lam.get("p_pass") is not None:
        out["p_pass"] = lam["p_pass"]
        out["expected_sifted"] = lam["p_pass"] * rounds
    snaps = payload.get("snaps") or {}
    decision = snaps.get("reference_companion") if isinstance(snaps, Mapping) else None
    out["rests_on_a_snap"] = (
        str(decision.get("rests_on_a_snap")) if isinstance(decision, Mapping) else None
    )
    if isinstance(decision, Mapping):
        out["evaluated_off_snap_count"] = decision.get("evaluated_off_snap_count")
    bracket = key_rate.get("reference_bracket")
    if isinstance(bracket, Mapping):
        snapped = bracket.get("snapped") or {}
        out["bracket_status"] = bracket.get("status")
        out["snapped_h_lb"] = snapped.get("h_lb")
        out["snapped_key_length"] = snapped.get("key_length")
    engine = (payload.get("provenance") or {}).get("engine") or {}
    out["git_commit"] = engine.get("git_commit")
    out["git_dirty"] = engine.get("git_dirty")
    return out


def summarize(sweep: str, out: Path) -> list[dict[str, Any]]:
    """Return every row of ``sweep``, in declared order."""
    return [row(sweep, p, out / sweep / p.id) for p in SWEEPS[sweep].points()]


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _refusal(stages: Mapping[str, Any]) -> str | None:
    for name, stage in stages.items():
        if isinstance(stage, Mapping) and stage.get("refused"):
            return f"{name}:{stage.get('reason')}"
    return None


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    """Write ``rows`` with the leading, label and result columns, in that order."""
    labels: list[str] = []
    for r in rows:
        for key in r:
            if key not in COLUMNS and key not in RESULT_COLUMNS and key not in labels:
                labels.append(key)
    header = [*COLUMNS, *labels, *RESULT_COLUMNS]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in header})


def main(argv: list[str] | None = None) -> int:
    """Summarise the named sweeps into ``<to>/<sweep>/summary.csv``."""
    parser = argparse.ArgumentParser(prog="python -m runs.bbm92_study.summarize")
    parser.add_argument("sweeps", nargs="+", choices=sorted(SWEEPS))
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--to", type=Path, default=DEFAULT_TO)
    args = parser.parse_args(argv)
    for name in args.sweeps:
        rows = summarize(name, args.out)
        target = args.to / name / "summary.csv"
        write_csv(rows, target)
        done = sum(1 for r in rows if r.get("status") != "missing")
        print(f"{name}: {done}/{len(rows)} points -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
