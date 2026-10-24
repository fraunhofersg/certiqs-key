"""Report every attempted solver case, preserving failures and censoring.

Motivation: fastest successful runs alone hide lost coverage. A backend's gap
and a searched-declaration objective are not a certified optimality interval.
Downstream polish must not earn an unsupported method credit; warm seeds cost
their complete chain, and different alpha objectives require key comparisons.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .common import finite, write_json


def rows(root: Path) -> list[dict[str, Any]]:
    """Include unstarted cases explicitly; compact evidence stays in JSON."""
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    result = []
    chain_costs: dict[str, float | None] = {}
    for task in manifest["tasks"]:
        folder = root / task["id"]
        completion = (
            json.loads((folder / "completion.json").read_text())
            if (folder / "completion.json").exists()
            else {}
        )
        summary = (
            json.loads((folder / "summary.json").read_text())
            if (folder / "summary.json").exists()
            else {}
        )
        actual_task = (
            json.loads((folder / "task.json").read_text(encoding="utf-8"))
            if (folder / "task.json").is_file()
            else {}
        )
        search = summary.get("search") or {}
        memory = summary.get("memory") or {}
        valid = summary.get("certificate_valid") is True
        target = task["case"].get("target_bound")
        key_target = task["case"].get("target_key_length")
        if target is not None and (
            key_target is not None or task["case"].get("alpha_search")
        ):
            raise ValueError("bound targets require fixed alpha and no key target")
        target_declaration = task["case"].get("target_declaration")
        if target_declaration is None and key_target is None:
            target_declaration = "reference_companion"
        bound = finite(summary.get("certified_bound"))
        supported = search.get("termination") != "unsupported" if search else None
        comparable = (
            valid
            and completion.get("status") == "completed"
            and not summary.get("refused")
            and supported is not False
            and (
                target_declaration is None
                or summary.get("certified_declaration") == target_declaration
            )
        )
        key_length = summary.get("key_length")
        target_met = (
            comparable and bound is not None and bound >= target
            if target is not None
            else comparable and key_length is not None and key_length >= key_target
            if key_target is not None
            else None
        )
        elapsed = finite(completion.get("elapsed_seconds"))
        predecessor = task.get("warm_predecessor")
        prior_cost = chain_costs.get(predecessor) if predecessor is not None else 0.0
        chain_costs[task["id"]] = (
            elapsed + prior_cost
            if elapsed is not None and prior_cost is not None
            else None
        )
        row = {
            "matrix": str(root),
            "revision": manifest["revision"],
            "task": task["id"],
            "case": task["case"]["id"],
            "variant": task["variant"]["id"],
            "method": task["variant"]["method"],
            "oracle_requested": None
            if task["variant"].get("native_solver_settings") is True
            else task["variant"].get("oracle", "qics"),
            "repeat": task["repeat"],
            "warm_chain": manifest.get("warm_chain", False),
            "warm_predecessor": task.get("warm_predecessor"),
            "warm_start": actual_task.get("warm_start"),
            "warm_start_reason": actual_task.get(
                "warm_start_reason", "unrecorded" if actual_task else "not_started"
            ),
            "warm_chain_elapsed_seconds": chain_costs[task["id"]]
            if manifest.get("warm_chain", False)
            else None,
            "alpha": summary.get("alpha"),
            "native_solver_settings": task["variant"].get("native_solver_settings")
            is True,
            "budget_seconds": None
            if task["variant"].get("native_solver_settings") is True
            else task["seconds"],
            "status": completion.get("status", "not_started"),
            "elapsed_seconds": completion.get("elapsed_seconds"),
            "elapsed_kind": "imputed_process_cap"
            if completion.get("status") == "interrupted"
            else "measured_parent"
            if elapsed is not None
            else "unavailable",
            "process_cap_seconds": completion.get("process_cap_seconds"),
            "error": summary.get("error"),
            "refused": summary.get("refused"),
            "tier": summary.get("reported_tier"),
            "certificate_valid": valid,
            "candidate_supported": supported,
            "candidate_methods_run": sorted(
                {
                    a["method"]
                    for a in search.get("attempts") or []
                    if a.get("method") and a.get("termination") != "unsupported"
                }
            ),
            "certified_declaration": summary.get("certified_declaration"),
            "certified_bound": bound,
            "key_length": summary.get("key_length"),
            "rate_per_round": summary.get("rate_per_round"),
            "diagnostic_gap": summary.get("search_gap_diagnostic"),
            "termination": search.get("termination"),
            "solver_seconds": search.get("solver_seconds"),
            "certification_seconds": summary.get("certification_seconds"),
            "peak_rss_bytes": memory.get("peak_rss_bytes"),
            "target_bound": target,
            "target_key_length": key_target,
            "target_declaration": target_declaration,
            "target_met": target_met,
        }
        # Certification is performed at final points: its endpoint time is an
        # observed upper bound on time to target, not an interpolated crossing.
        row["certified_target_observed_seconds"] = (
            (
                row["warm_chain_elapsed_seconds"]
                if manifest.get("warm_chain", False)
                else row["elapsed_seconds"]
            )
            if row["target_met"]
            else None
        )
        row["evidence"] = summary
        result.append(row)
    return result


def main() -> int:
    """Write compact JSON and CSV from completed or interrupted matrices."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    all_rows = [row for root in args.roots for row in rows(root)]
    args.out.mkdir(parents=True, exist_ok=True)
    write_json(args.out / "summary.json", all_rows)
    fields = [k for k in all_rows[0] if k != "evidence"] if all_rows else []
    with (args.out / "summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"wrote {len(all_rows)} attempted/planned cases to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
