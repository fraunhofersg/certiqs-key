"""Prepare and record one explicitly configured two-sided numerical run."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import platform
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

from certiqs_key.receiver.catalogue import decibel_to_transmittance
from certiqs_key.runs.config import RunConfig, SolverSettings
from certiqs_key.runs.iterate_file import (
    WarmStartFileError,
    attach_final_iterate,
    load_warm_start,
    seed_of,
)
from certiqs_key.runs.record import RunRecord, record_run, write_record
from certiqs_key.runs.surface import InstanceIdentity
from certiqs_key.solvers.frank_wolfe.joint_options import ORACLE_CHOICES
from certiqs_key.solvers.types import ADVANCED_METHODS, ORDINARY_METHODS

CREATED_BY = "runs/two_sided/point.py"
INSTANCES = ("bb84", "optical_bb84", "decoy_bb84", "bbm92")


def parser() -> argparse.ArgumentParser:
    """Return the single-point command-line parser."""
    result = argparse.ArgumentParser(description=__doc__)
    add_point_options(result)
    result.add_argument(
        "--loss-db",
        type=float,
        required=True,
        help="channel loss in dB (per arm on bbm92; must be 0 on bb84)",
    )
    result.add_argument(
        "--output",
        type=Path,
        required=True,
        help="the point's output directory; refused if it exists",
    )
    return result


def add_point_options(result: argparse.ArgumentParser) -> None:
    """Add every option of one point except its loss and its output directory.

    Shared with :mod:`runs.two_sided.chain`, which takes a LIST of losses and
    an output root instead.
    """
    result.add_argument(
        "--instance", choices=INSTANCES, required=True, help="the packaged instance"
    )
    result.add_argument(
        "--route",
        choices=("encoded", "licensed", "licensed+two-sector"),
        required=True,
        help="device.route: which reduction is declared (must be encoded on bb84)",
    )
    result.add_argument(
        "--map",
        dest="acceptance_map",
        help="device.acceptance_map: one of the instance's own acceptance maps",
    )
    result.add_argument(
        "--rounds", type=int, required=True, help="the number of rounds n"
    )
    result.add_argument(
        "--lambda-ec",
        type=int,
        required=True,
        help="parameters.lambda_ec: the error-correction leakage in bits",
    )
    result.add_argument(
        "--lambda-ec-purpose",
        required=True,
        help="why this leakage was chosen, written to provenance.json",
    )
    result.add_argument(
        "--zero-ec-label",
        help="required with --lambda-ec 0: the label marking the run a diagnostic",
    )
    result.add_argument(
        "--source-model",
        choices=("ideal_pair", "spdc"),
        help="bbm92 only: device.source_model (default ideal_pair)",
    )
    result.add_argument(
        "--party-local-view",
        choices=("operator", "licensed_scalar"),
        help="BBM92's supplier-owned constraint reading (surface default: operator)",
    )
    result.add_argument(
        "--dark-count",
        default="0",
        help="every detector's dark-count probability, a decimal or p/q (default 0)",
    )
    result.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="SECTION.KEY=VALUE",
        help=(
            "one scalar parameter of the instance's own table, SECTION being "
            "model or device (e.g. device.led_timing=every-round); a number is "
            "read exactly as a decimal or p/q, anything else as a string, and "
            "the instance's own key check refuses an unknown name"
        ),
    )
    result.add_argument(
        "--iterations",
        type=int,
        default=2000,
        help="solver.max_iterations: the method-native work cap (default 2000)",
    )
    result.add_argument(
        "--method",
        choices=ORDINARY_METHODS + ADVANCED_METHODS,
        default="fw",
        help=(
            "candidate search: auto or fw is solver.method, an expert method "
            "solver.advanced.method; default fw, the method this driver's "
            "committed sweeps ran with --iterations"
        ),
    )
    result.add_argument(
        "--budget-seconds",
        type=float,
        help="global solver wall budget across all methods",
    )
    result.add_argument(
        "--gap-target",
        type=float,
        help=(
            "solver.advanced.gap_tolerance: a diagnostic stopping target, not a "
            "proof tolerance"
        ),
    )
    result.add_argument(
        "--alpha",
        type=float,
        help=(
            "the Renyi order to solve at; absent takes the instance's declared "
            "default. A fixed order costs rate that does not vanish with n, so a "
            "measurement at large n declares one (alpha - 1 ~ n^(-1/2))"
        ),
    )
    result.add_argument(
        "--endpoint-rule",
        choices=("exact", "bernstein"),
        default="bernstein",
        help="statistics' endpoint rule for the acceptance box",
    )
    # The driver's solver choices (solvers.frank_wolfe.joint_options), open to
    # every instance (there is one driver): optical_bb84's
    # accepted-format declaration takes them as decoy_bb84's and bbm92's do.
    # Absent means the solver's own default, recorded as absent.
    result.add_argument(
        "--oracle",
        choices=ORACLE_CHOICES,
        help=(
            "solver.advanced.oracle: the linear-oracle backend; absent takes the "
            "solver's own (qics)"
        ),
    )
    result.add_argument(
        "--warm-start",
        type=Path,
        help=(
            "solver.advanced.warm_start: a prior point's output directory (or "
            "its final-iterate.json); start from its final iterate, identified "
            "by the file's sha256"
        ),
    )


def _fraction(text: str) -> Fraction:
    """Read an ordinary decimal or fraction without a binary64 detour."""
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f"expected a decimal or fraction, got {text!r}") from error


def _override(item: str) -> tuple[str, str, Fraction | str]:
    """Read one ``--set SECTION.KEY=VALUE`` into its section, key and value."""
    target, separator, raw = item.partition("=")
    section, dot, key = target.partition(".")
    if not separator or not dot or not key or section not in ("model", "device"):
        raise ValueError(
            f"--set takes SECTION.KEY=VALUE with SECTION model or device; got {item!r}"
        )
    try:
        return section, key, Fraction(raw)
    except (ValueError, ZeroDivisionError):
        return section, key, raw


def _transmittance(loss_db: float, *, per_arm: bool) -> Fraction:
    if not math.isfinite(loss_db) or loss_db < 0:
        raise ValueError("loss_db must be finite and non-negative")
    effective_loss = loss_db / 2.0 if per_arm else loss_db
    # The physical dB conversion is evaluated in binary64, then recorded as the
    # exact decimal supplied to the instances' shared preparation boundary.
    return Fraction(str(decibel_to_transmittance(effective_loss)))


def _uniform_dark_count(surface: Any, value: Fraction) -> dict[str, Fraction]:
    spec = next(row for row in surface.PARAMETERS if row.name == "dark_count")
    return dict.fromkeys(spec.per_port_labels, value)


def build_config(arguments: argparse.Namespace) -> tuple[Any, RunConfig]:
    """Build one public instance configuration from explicit CLI declarations."""
    if arguments.rounds < 1:
        raise ValueError("rounds must be positive")
    if arguments.lambda_ec < 0:
        raise ValueError("lambda_ec must be a non-negative integer")
    if arguments.lambda_ec == 0 and not arguments.zero_ec_label:
        raise ValueError("lambda_ec=0 requires --zero-ec-label to mark the diagnostic")
    if arguments.lambda_ec != 0 and arguments.zero_ec_label:
        raise ValueError("--zero-ec-label applies only when lambda_ec=0")
    if arguments.instance != "bbm92" and arguments.source_model is not None:
        raise ValueError("--source-model is a BBM92 option")
    party_local_view = getattr(arguments, "party_local_view", None)
    if arguments.instance != "bbm92" and party_local_view is not None:
        raise ValueError("--party-local-view is a BBM92 option")

    surface = importlib.import_module(f"instances.{arguments.instance}.surface")
    base: RunConfig = surface.default_config()
    model = dict(base.model)
    device = dict(base.device)
    transmittance = _transmittance(
        arguments.loss_db, per_arm=arguments.instance == "bbm92"
    )
    if arguments.instance == "bbm92":
        model["alice_transmittance"] = transmittance
        model["bob_transmittance"] = transmittance
        device["source_model"] = arguments.source_model or "ideal_pair"
        for prefix in ("alice", "bob"):
            key = f"{prefix}_dark_count"
            spec = next(row for row in surface.PARAMETERS if row.name == key)
            device[key] = dict.fromkeys(
                spec.per_port_labels, _fraction(arguments.dark_count)
            )
    elif arguments.instance != "bb84":
        model["transmittance"] = transmittance
        device["dark_count"] = _uniform_dark_count(
            surface, _fraction(arguments.dark_count)
        )
    # Each instance's own table names its acceptance maps and checks the name.
    if arguments.acceptance_map is not None:
        device["acceptance_map"] = arguments.acceptance_map
    if arguments.instance != "bb84":
        device["route"] = arguments.route
    elif arguments.loss_db != 0 or arguments.route != "encoded":
        raise ValueError("qubit BB84 has no loss model or physical receiver route")
    # Applied last, so a --set names exactly what the record then carries.
    for item in getattr(arguments, "overrides", None) or ():
        section, key, value = _override(item)
        if section == "device":
            device[key] = value
        elif isinstance(value, Fraction):
            model[key] = value
        else:
            raise ValueError(f"a model parameter is a number; got {item!r}")
    if party_local_view is not None:
        device["party_local_view"] = party_local_view
    parameters = replace(base.parameters, lambda_ec=arguments.lambda_ec)
    config = base.with_(
        rounds=arguments.rounds,
        parameters=parameters,
        model=model,
        device=device,
        solver=SolverSettings.from_choices(
            max_iterations=arguments.iterations,
            method=getattr(arguments, "method", None),
            budget_seconds=getattr(arguments, "budget_seconds", None),
            gap_tolerance=getattr(arguments, "gap_target", None),
            oracle=getattr(arguments, "oracle", None),
            warm_start=(
                None
                if getattr(arguments, "warm_start", None) is None
                else seed_of(arguments.warm_start)
            ),
        ),
        endpoint_rule=arguments.endpoint_rule,
    )
    alpha = getattr(arguments, "alpha", None)
    if alpha is not None:
        if not math.isfinite(alpha) or alpha <= 1:
            raise ValueError("alpha must be a finite number above 1")
        config = config.with_(alpha=alpha)
    return surface, config


def run_point(
    arguments: argparse.Namespace,
    *,
    oracle: object,
    runner_builder: Callable[..., Callable[[RunConfig, int], object]] | None = None,
    record_builder: Callable[..., RunRecord] = record_run,
    record_writer: Callable[[Path, RunRecord], None] = write_record,
) -> RunRecord:
    """Run and record one point, refusing an existing output directory."""
    output = arguments.output
    if output.exists():
        raise FileExistsError(f"output directory already exists: {output}")
    surface, config = build_config(arguments)
    # A WARM-START FILE IS VERIFIED BEFORE ANYTHING IS WRITTEN: a missing,
    # altered or foreign seed raises WarmStartFileError with its reason and
    # leaves no directory behind. (A seed that reads but does not fit this
    # point's feasible set is refused later by the solver, as a recorded
    # SliceRefusal with a warm_start_* reason.)
    advanced = None if config.solver is None else config.solver.advanced
    if advanced is not None and advanced.warm_start is not None:
        load_warm_start(advanced.warm_start)
    output.mkdir(parents=True)
    # Save the request before expensive preparation or solving. An interrupted
    # directory remains evidence of the attempted point, never a completed run.
    (output / "config.json").write_text(
        json.dumps(config.to_payload(), indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    repository = Path(__file__).resolve().parents[2]
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository, text=True
        ).strip()
        tracked_changes = subprocess.check_output(
            ["git", "diff", "HEAD", "--name-only"], cwd=repository, text=True
        ).splitlines()
    except (OSError, subprocess.CalledProcessError):
        revision, tracked_changes = None, None
    (output / "provenance.json").write_text(
        json.dumps(
            {
                "revision": revision,
                "tracked_changes": tracked_changes,
                "python": sys.version,
                "platform": platform.platform(),
                "lambda_ec_purpose": arguments.lambda_ec_purpose,
                "zero_ec_diagnostic_label": arguments.zero_ec_label,
                "loss_db": arguments.loss_db,
                "instance": arguments.instance,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    build = surface.runner if runner_builder is None else runner_builder
    run = build(oracle, output / "bundles", created_by=CREATED_BY)
    outcome = run(config, 0)
    record = record_builder(
        outcome,
        config,
        created_by=CREATED_BY,
        instance=InstanceIdentity(surface.DESCRIPTOR, tuple(surface.PARAMETERS)),
    )
    payload = dict(record.payload)
    payload["two_sided_point"] = {
        "instance": arguments.instance,
        "route": arguments.route,
        "loss_db": arguments.loss_db,
        "loss_interpretation": (
            "total symmetric link loss; each BBM92 arm receives half"
            if arguments.instance == "bbm92"
            else "channel power loss"
        ),
        "zero_ec_diagnostic_label": arguments.zero_ec_label,
        "lambda_ec_purpose": arguments.lambda_ec_purpose,
    }
    enriched = RunRecord(record.kind, record.schema_version, record.created_by, payload)
    # THE FINAL ITERATE, BESIDE THE RECORD AND NAMED BY ITS HASH, so a later
    # point can warm-start from it. The run tier's one writer of that key
    # decides whether this run has one (every completed run does).
    enriched = attach_final_iterate(enriched, outcome, config, output)
    record_writer(output / "record.json", enriched)
    return enriched


def main(argv: Sequence[str] | None = None) -> int:
    """Run one configured point with the public QICS oracle."""
    arguments = parser().parse_args(argv)
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    try:
        run_point(arguments, oracle=QicsSectorChoiOracle())
    except WarmStartFileError as refused:
        print(f"refused: {refused.reason}: {refused}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
