"""The grid on which a packaged template is held equal to its reference.

WHY A SUPPORT MODULE. Two tests walk the grid: the static one
(``tests/unit/test_declared_surface_static.py``: ``default_config`` payloads,
the static read of a template against its full read) and the equivalence gate
(``tests/integration/test_declared_equivalence.py``: preparation records,
refusals and run records).

The grid, per instance: the defaults, every preset, every value of every
``choice`` parameter one at a time, three numeric edits (non-dyadic weights or
coin, dark counts 1e-6, efficiency 0.9 at cutoff 2 with window 3), the run
fields, the snap-certification run parameters, and the partial-section
``default_config`` calls the instances' own tests make. A
full call lays its section over the instance's own defaults, because
optical_bb84 and bbm92 REPLACE a section a caller supplies.
"""

from __future__ import annotations

from types import ModuleType
from typing import Any

from certiqs_key.runs.surface import Kind

__all__ = ["IDS", "config_grid", "copied"]

#: The four instances that are packaged templates.
IDS: tuple[str, ...] = ("bb84", "optical_bb84", "decoy_bb84", "bbm92")

_PORTS = ("H", "V", "D", "A")

#: Three numeric edits per instance, laid over its full device section.
_EDITS: dict[str, list[dict[str, Any]]] = {
    "bb84": [{"alice_z": "2/3", "alice_x": "1/3", "bob_z": "4/5", "bob_x": 0.2}],
    "optical_bb84": [
        {"basis_split": "1/3"},
        {"dark_count": dict.fromkeys(_PORTS, 1e-6)},
        {
            "efficiency": dict.fromkeys(_PORTS, 0.9),
            "photon_cutoff": 2,
            "exact_window": 3,
        },
    ],
    "decoy_bb84": [
        {
            "gamma": "1/3",
            "test_signal": "1/3",
            "test_weak": "1/3",
            "test_vacuum": "1/3",
        },
        {"dark_count": dict.fromkeys(_PORTS, 1e-6)},
        {
            "efficiency": dict.fromkeys(_PORTS, 0.9),
            "photon_cutoff": 2,
            "exact_window": 3,
        },
    ],
    "bbm92": [
        {"test_fraction": "1/3"},
        {"bob_dark_count": dict.fromkeys(_PORTS, 1e-6)},
        {
            "alice_efficiency": dict.fromkeys(_PORTS, 0.9),
            "alice_photon_cutoff": 2,
            "alice_exact_window": 3,
        },
    ],
}


def _without(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    return {name: value for name, value in mapping.items() if name != key}


def _partial(instance: str, full: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the partial-section calls the instances' own tests make (finding 1)."""
    if instance == "bb84":
        return [{"model": {"qber": "1/50"}}]
    if instance == "optical_bb84":
        return [
            {"device": {"route": "licensed"}},
            {"device": _without(full["device"], "exact_window")},
        ]
    if instance == "decoy_bb84":
        return [
            {"device": {"photon_cutoff": 2}},
            *(
                {"device": {"source_cutoff": 2, "route": route}}
                for route in ("encoded", "licensed", "licensed+two-sector")
            ),
        ]
    # test_bbm92_surface.py:90-99, with its int cutoff.
    return [
        {
            "device": _without(full["device"], "alice_exact_window")
            | {"alice_photon_cutoff": 3}
        },
        {
            "device": full["device"]
            | {"alice_photon_cutoff": 3, "alice_exact_window": None}
        },
    ]


def config_grid(python: ModuleType) -> list[tuple[str, dict[str, Any]]]:
    """Return the grid's ``default_config`` calls, as ``(label, overrides)``."""
    default = python.default_config()
    full = {"model": dict(default.model), "device": dict(default.device)}
    instance = python.DESCRIPTOR.id
    calls: list[tuple[str, dict[str, Any]]] = [("defaults", {})]
    for preset in python.PRESETS:
        calls.append(
            (
                f"preset {preset.name}",
                {
                    "model": {**full["model"], **dict(preset.model)},
                    "device": {**full["device"], **dict(preset.device)},
                },
            )
        )
    for spec in python.PARAMETERS:
        if spec.kind is not Kind.CHOICE:
            continue
        for value, _meaning in spec.domain.options:
            section = str(spec.section)
            calls.append(
                (
                    f"{spec.name}={value}",
                    {**full, section: {**full[section], spec.name: value}},
                )
            )
    for index, edit in enumerate(_EDITS[instance]):
        calls.append((f"edit {index}", {**full, "device": {**full["device"], **edit}}))
    calls.append(("run fields", {"rounds": 5000, "declared_tolerance": 1e-9}))
    # THE SNAP RUN PARAMETERS: the instances hand them to their snap and
    # their reduction request (``instances.common.declare.snap_settings``),
    # and so must the document.
    calls.append(
        (
            "certification settings",
            {"reference_enclosure": False, "strict_snaps": True},
        )
    )
    calls.append(("certification strict", {"strict_snaps": True}))
    for index, overrides in enumerate(_partial(instance, full)):
        calls.append((f"partial {index}", overrides))
    return calls


def copied(overrides: dict[str, Any]) -> dict[str, Any]:
    """Return ``overrides`` with each section copied: ``default_config`` pops them."""
    return {
        key: dict(value) if isinstance(value, dict) else value
        for key, value in overrides.items()
    }
