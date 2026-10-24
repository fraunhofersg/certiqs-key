"""Running one configuration many times over, and keeping what came back.

A sweep is a GRID AND A LOOP, and deliberately nothing else. It performs no
search, fits nothing, and stops early for no reason: every point is run and every
outcome is recorded, including the ones that refuse. A sweep that dropped points
it judged uninteresting would be deciding something, and this module decides
nothing.

THE ALPHA AXIS. Choosing alpha is not a sweep's business either. A grid over
``alpha`` is a grid of runs like any other axis; the outer alpha SEARCH is the
run tier's own opt-in feature (:mod:`certiqs_key.runs.alpha_search`), set per
configuration by
:attr:`RunConfig.alpha_search <certiqs_key.runs.config.RunConfig.alpha_search>`
and run inside an instance's runner, so a sweep point whose configuration asks
for it is one runner call that returns the chosen run. This module neither
runs nor knows that search, and
:func:`~certiqs_key.runs.pipeline.run_slice` still runs one alpha.

WHY THE RUNNER IS AN ARGUMENT
=============================
:func:`sweep` takes a callable rather than constructing runs itself, because
wiring a run needs a linear oracle, an instance's providers and an output
directory -- and choosing any of those here would put backend and channel-model
knowledge in the orchestration tier. The caller owns the wiring; this module owns
the grid, the order, and the collection.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.pipeline import SliceOutcome
from certiqs_key.runs.record import RunRecord, record_run, write_record
from certiqs_key.runs.surface import InstanceIdentity

__all__ = ["SweptRun", "grid", "sweep"]


@dataclass(frozen=True)
class SweptRun:
    """One point of a sweep: what was asked, what came back, and where it went."""

    index: int
    config: RunConfig
    outcome: SliceOutcome
    record: RunRecord
    record_path: Path | None = None


def grid(
    base: RunConfig,
    *,
    model: Mapping[str, Sequence[Any]] | None = None,
    device: Mapping[str, Sequence[Any]] | None = None,
    **fields: Sequence[Any],
) -> tuple[RunConfig, ...]:
    """Return the cartesian product of the named axes, applied to ``base``.

    Three axis kinds, because :attr:`RunConfig.model` and
    :attr:`RunConfig.device` are opaque here and cannot be reached by attribute
    name:

        grid(
            base,
            rounds=[10**6, 10**7],
            model={"qber": [Fraction(1, 100)]},
            device={"photon_cutoff": [1, 2, 3]},
        )

    Args:
        base: the configuration every point is derived from. Fields no axis names
            are carried through unchanged.
        model: axes over the instance's channel-model parameters, keyed by the
            name the instance's provider reads.
        device: axes over the instance's physical-device parameters, keyed the
            same way. The photon-cutoff axis of an optical slice is one of these.
        fields: axes over :class:`RunConfig`'s own fields, keyed by field name.

    Returns:
        One config per grid point, in a deterministic order: axis names sorted
        within each kind, then the field axes, then ``model``, then ``device``,
        and :func:`itertools.product`'s last-axis-fastest ordering within that.
        Determinism is the point -- a sweep re-run must produce records in the
        same order on every run for two record sets to be comparable at all.
    """
    field_names = sorted(fields)
    model_names = sorted(model or {})
    device_names = sorted(device or {})
    axes: list[Sequence[Any]] = [fields[name] for name in field_names]
    axes += [(model or {})[name] for name in model_names]
    axes += [(device or {})[name] for name in device_names]

    split_model = len(field_names)
    split_device = split_model + len(model_names)

    configs: list[RunConfig] = []
    for point in itertools.product(*axes) if axes else [()]:
        field_values = dict(zip(field_names, point[:split_model], strict=True))
        model_values = dict(
            zip(model_names, point[split_model:split_device], strict=True)
        )
        device_values = dict(zip(device_names, point[split_device:], strict=True))
        candidate = base.with_(**field_values) if field_values else base
        if model_values:
            candidate = candidate.with_(model={**candidate.model, **model_values})
        if device_values:
            candidate = candidate.with_(device={**candidate.device, **device_values})
        configs.append(candidate)
    return tuple(configs)


def sweep(
    configs: Sequence[RunConfig],
    runner: Callable[[RunConfig, int], SliceOutcome],
    *,
    created_by: str,
    record_dir: Path | None = None,
    instance: InstanceIdentity | None = None,
) -> tuple[SweptRun, ...]:
    """Run every config in order and return one :class:`SweptRun` per point.

    Args:
        configs: the grid, typically from :func:`grid`.
        runner: wires and executes one point. Receives the config and its index;
            the index is passed so that a caller can give each run its own bundle
            directory, which :func:`certiqs_key.domain.write_bundle` requires.
        created_by: recorded on every record. Never an absolute path, timestamp
            or run ID (spec/architecture.md 2.6).
        record_dir: where records are written, one ``run-NNNN.json`` per point.
            ``None`` keeps them in memory only.
        instance: the instance every point is of,
            ``InstanceIdentity(DESCRIPTOR, PARAMETERS)``, written into every
            record's ``instance`` block (record schema 0.20.0); a sweep is of
            one instance, which the key-rate sweep report requires.

    Returns:
        One entry per config, in the order given. A refusal is an entry like any
        other; nothing is dropped and nothing is retried.
    """
    results: list[SweptRun] = []
    for index, config in enumerate(configs):
        outcome = runner(config, index)
        record = record_run(
            outcome, config, created_by=created_by, instance=instance
        )
        path: Path | None = None
        if record_dir is not None:
            path = record_dir / f"run-{index:04d}.json"
            write_record(path, record)
        results.append(
            SweptRun(
                index=index,
                config=config,
                outcome=outcome,
                record=record,
                record_path=path,
            )
        )
    return tuple(results)
