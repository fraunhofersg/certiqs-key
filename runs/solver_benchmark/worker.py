"""One capped full-pipeline experiment, with the production certifier unchanged.

Motivation: solver-reported success and a small search gap are not a certified
key. Preserve the ordinary record and summarize the actual achieved tier.
Native-effort comparisons must retain the instance's iteration defaults.
"""

from __future__ import annotations

import argparse
import faulthandler
import gzip
import importlib.util
import json
import platform
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from .common import (
    ROOT,
    finite,
    git_revision,
    memory_limit,
    memory_snapshot,
    write_json,
)


def load_plugin(path: str, name: str = "solver_gym_experiment") -> Any:
    """Load an explicitly requested experimental candidate or oracle adapter."""
    resolved = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(name, resolved)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import experiment {resolved}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def configuration(case: dict[str, Any], variant: dict[str, Any], seconds: float) -> Any:
    """Use the instance's own parameter kinds and preparation conventions."""
    from fractions import Fraction

    from instances import surface_of

    from certiqs_key.runs.config import (
        AdvancedSolverSettings,
        AlphaSearchSettings,
        SolverSettings,
    )
    from certiqs_key.solvers.types import ADVANCED_METHODS

    surface = surface_of(case["instance"])
    config = surface.default_config()
    if variant.get("literal_defaults") is True:
        # Entry-point behavior: the instance document's run defaults unchanged,
        # optionally with only the method swapped: auto or fw as
        # solver.method, an expert method as solver.advanced.method, the other
        # tier's method cleared. No rounds, alpha, tail or EC override; the
        # search allowance does not apply.
        if variant.get("method") is None:
            return surface, config
        from dataclasses import replace

        base = config.solver or SolverSettings()
        advanced = base.advanced or AdvancedSolverSettings()
        method = variant["method"]
        solver = (
            replace(base, method=None, advanced=replace(advanced, method=method))
            if method in ADVANCED_METHODS
            else replace(base, method=method, advanced=replace(advanced, method=None))
        )
        return surface, config.with_(solver=solver)
    specifications = {p.name: p for p in surface.PARAMETERS}
    updates: dict[str, Any] = {}
    for section in ("model", "device"):
        values = dict(getattr(config, section))
        for name, raw in case.get(section, {}).items():
            spec = specifications[name]
            if str(spec.kind) == "per_port_fraction":
                values[name] = {
                    p: Fraction(str(raw[p] if isinstance(raw, dict) else raw))
                    for p in spec.per_port_labels
                }
            elif str(spec.kind) == "choice":
                values[name] = str(raw)
            else:
                values[name] = Fraction(str(raw))
        updates[section] = values
    native = variant.get("native_solver_settings") is True
    solver = (
        config.solver or SolverSettings()
        if native
        else SolverSettings.from_choices(
            method=variant["method"],
            oracle=variant.get("oracle", "qics"),
            max_iterations=1_000_000,
            gap_tolerance=1e-8,
            budget_seconds=seconds,
            certified_evaluation="on",
        )
    )
    updates.update(
        rounds=case["rounds"],
        alpha=case.get("alpha"),
        tail_evaluation="enclosure",
        solver=solver,
    )
    if case.get("alpha_search"):
        updates["alpha"] = None
        updates["alpha_search"] = AlphaSearchSettings.from_payload(case["alpha_search"])
    return surface, config.with_(**updates)


def compact_search(search: dict[str, Any]) -> dict[str, Any]:
    """Retain timing and attempts without duplicating matrix coordinates."""
    keys = (
        "method",
        "policy",
        "termination",
        "budget_seconds",
        "solver_seconds",
        "preparation_seconds",
        "relative_gap",
        "budget_overrun_seconds",
        "capabilities",
        "assessment_history",
        "attempts",
        "iteration_unit",
    )
    result = {k: search.get(k) for k in keys}
    best = search.get("best_contributing_candidate") or {}
    result["best_gate"] = best.get("gate")
    result["best_gap"] = best.get("gap")
    return result


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep searched and reference values separate; do not manufacture a gap."""
    stages = payload.get("stages") or {}
    key = stages.get("key_rate") or {}
    certified = key.get("certified") or {}
    search = key.get("search_report") or key.get("search") or {}
    reference = key.get("reference_bracket") or {}
    return {
        "refused": payload.get("refused"),
        "refusals": {
            name: stage
            for name, stage in stages.items()
            if isinstance(stage, dict) and stage.get("refused")
        },
        "reported_tier": key.get("reported_tier"),
        "key_length": key.get("key_length"),
        "rate_per_round": key.get("rate_per_round"),
        "key_reason": key.get("key_length_reason_code"),
        "alpha": key.get("alpha"),
        "alpha_search": next(
            (
                child["detail"]
                for stage in (payload.get("composition_flow") or {}).get("stages", [])
                for child in stage.get("children", [])
                if child.get("name") == "alpha"
                and child.get("detail", {}).get("searched")
            ),
            None,
        ),
        "h_low_searched_diagnostic": key.get("h_low", key.get("h_low_dropped")),
        "h_lb_reported_first_order": key.get("h_lb", key.get("h_lb_dropped")),
        "certified_bound": certified.get("certified_bound"),
        "certified_status": certified.get("status"),
        "certified_declaration": certified.get("declaration"),
        "certification_seconds": certified.get("seconds"),
        "certification_reasons": certified.get("reasons"),
        "search_gap_diagnostic": key.get("frank_wolfe_gap"),
        "dropped_set": key.get("dropped_set"),
        "reference_bracket": {
            k: v for k, v in reference.items() if k not in ("points", "candidates")
        },
        "joint_solver": key.get("joint_solver"),
        "oracle_diagnostics": key.get("oracle_diagnostics"),
        "solver_request": key.get("solver_request"),
        "timings": key.get("timings"),
        "search": compact_search(search),
        "statistics_consistency": payload.get("statistics_consistency"),
        "engine_provenance": payload.get("provenance"),
        "certificate_valid": key.get("reported_tier") == "certified"
        and certified.get("status") == "certified"
        and finite(certified.get("certified_bound")) is not None,
    }


def run(task: dict[str, Any], out: Path) -> dict[str, Any]:
    """Run one task; imports, EC estimation and serialization are timed too."""
    started = time.perf_counter()
    resources = memory_limit(task["memory_gib"])
    print("stage: imports", flush=True)
    from certiqs_key.runs.error_correction import with_estimated_lambda_ec
    from certiqs_key.runs.iterate_file import attach_final_iterate, seed_of
    from certiqs_key.runs.pipeline import Preparation
    from certiqs_key.runs.record import record_run
    from certiqs_key.runs.surface import InstanceIdentity
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    case, variant = task["case"], task["variant"]
    surface, config = configuration(case, variant, task["seconds"])
    if variant.get("capture"):
        capture = load_plugin(
            task.get("capture_snapshot", variant["capture"]), "solver_gym_capture"
        )
        capture.install(out / "certifier-inputs.jsonl")
    oracle: Any = QicsSectorChoiOracle()
    if variant.get("plugin"):
        plugin = load_plugin(task.get("plugin_snapshot", variant["plugin"]))
        if hasattr(plugin, "install"):
            plugin.install()
        if hasattr(plugin, "create_oracle"):
            oracle = plugin.create_oracle()
    if task.get("warm_start"):
        from dataclasses import replace

        from certiqs_key.runs.config import AdvancedSolverSettings, SolverSettings

        solver = config.solver or SolverSettings()
        config = config.with_(
            solver=replace(
                solver,
                advanced=replace(
                    solver.advanced or AdvancedSolverSettings(),
                    warm_start=seed_of(Path(task["warm_start"])),
                ),
            )
        )
    ec_start = time.perf_counter()
    print("stage: error-correction preparation", flush=True)
    if case.get("f_ec") is not None:
        prep = surface.preparation(config)
        if isinstance(prep, Preparation):
            config, estimate = with_estimated_lambda_ec(config, prep, f_ec=case["f_ec"])
            write_json(out / "error-correction.json", estimate.as_payload())
        else:
            write_json(
                out / "error-correction.json", {"preparation_refused": repr(prep)}
            )
    ec_seconds = time.perf_counter() - ec_start
    write_json(out / "config.json", config.to_payload())
    runner = surface.runner(oracle, out / "bundles", created_by="runs.solver_benchmark")
    run_start = time.perf_counter()
    print("stage: full pipeline", flush=True)
    outcome = runner(config, 0)
    run_seconds = time.perf_counter() - run_start
    print(f"stage: record; pipeline seconds {run_seconds:.6f}", flush=True)
    record = record_run(
        outcome,
        config,
        created_by="runs.solver_benchmark",
        instance=InstanceIdentity(surface.DESCRIPTOR, tuple(surface.PARAMETERS)),
    )
    record = attach_final_iterate(record, outcome, config, out)
    with gzip.open(out / "record.json.gz", "wt", encoding="utf-8") as handle:
        json.dump(record.as_dict(), handle)
    summary = summarize(dict(record.payload))
    summary.update(
        worker_seconds=time.perf_counter() - started,
        pipeline_seconds=run_seconds,
        ec_preparation_seconds=ec_seconds,
        memory={**resources, **memory_snapshot()},
        python=sys.version,
        platform=platform.platform(),
        runner_revision=git_revision(),
    )
    return summary


def main() -> int:
    """Write a terminal summary even when a numerical call raises."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    args = parser.parse_args()
    faulthandler.enable()
    faulthandler.dump_traceback_later(60, repeat=True)
    task = json.loads(args.task.read_text(encoding="utf-8"))
    out = args.task.parent
    try:
        summary = run(task, out)
        write_json(out / "summary.json", summary)
        return 0
    except Exception as error:
        write_json(
            out / "summary.json",
            {
                "error": repr(error),
                "traceback": traceback.format_exc(),
                "runner_root": str(ROOT),
            },
        )
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
