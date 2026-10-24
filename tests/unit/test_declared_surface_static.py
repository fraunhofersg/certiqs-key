"""A template's static part reproduces each instance's static surface.

For bb84, optical_bb84, decoy_bb84 and bbm92 the configuration-independent blocks of the
packaged template ``instances/<id>/protocol.yaml``, read as a static fragment, yield the
instance's ``DESCRIPTOR``, ``PARAMETERS``, ``PRESETS`` and ``default_config(...)``. The
instance is the template read in full (``instances/<id>/surface.py``), so the comparison
holds the static read equal to the full one. Every comparison is of PAYLOADS, not of
``==``, because ``Fraction(1) == 1`` while ``_jsonable_default`` renders ``"1"`` against
``1``. The ``default_config`` grid is the equivalence gate's: the defaults, every
preset, every value of every choice parameter, three numeric edits, and the
partial-section calls the instances' own tests make.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from instances import surface_of
from instances.declared import DocumentSurface, load_packaged
from tests.support.declared_equivalence import IDS, config_grid, copied

from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.surface import Kind, Section

ROOT = Path(__file__).resolve().parents[2]


def fragment(instance: str) -> DocumentSurface:
    """Load an instance's template as a static fragment, packaged, from its place."""
    return load_packaged(ROOT / "instances" / instance / "protocol.yaml", static=True)


def _pair(instance: str) -> tuple[ModuleType, DocumentSurface]:
    return surface_of(instance), fragment(instance)


@pytest.fixture(params=IDS)
def pair(request: pytest.FixtureRequest) -> tuple[ModuleType, DocumentSurface]:
    return _pair(request.param)


def test_descriptor(pair: tuple[ModuleType, DocumentSurface]) -> None:
    python, document = pair
    assert document.DESCRIPTOR.as_payload() == python.DESCRIPTOR.as_payload()


def test_parameters_row_for_row(pair: tuple[ModuleType, DocumentSurface]) -> None:
    python, document = pair
    assert [spec.as_payload() for spec in document.PARAMETERS] == [
        spec.as_payload() for spec in python.PARAMETERS
    ]


def test_parameter_defaults_are_fractions(
    pair: tuple[ModuleType, DocumentSurface],
) -> None:
    """However a default is written, a numeric one is a ``Fraction``."""
    _python, document = pair
    for spec in document.PARAMETERS:
        if spec.default is None or spec.kind is Kind.CHOICE:
            continue
        values = (
            spec.default.values() if isinstance(spec.default, dict) else [spec.default]
        )
        assert all(type(value) is Fraction for value in values), spec.name


def test_presets(pair: tuple[ModuleType, DocumentSurface]) -> None:
    python, document = pair
    assert [preset.as_payload() for preset in document.PRESETS] == [
        preset.as_payload() for preset in python.PRESETS
    ]


def test_bb84_presets_are_parameters_yaml() -> None:
    """The presets in the document equal ``parameters.yaml``'s weights."""
    import yaml

    path = Path(surface_of("bb84").__file__).parent / "parameters.yaml"
    fixtures = yaml.safe_load(path.read_text(encoding="utf-8"))["basis_weights"]
    _python, document = _pair("bb84")
    expected = [
        {
            "alice_z": Fraction(entry["alice"]["Z"]),
            "alice_x": Fraction(entry["alice"]["X"]),
            "bob_z": Fraction(entry["bob"]["Z"]),
            "bob_x": Fraction(entry["bob"]["X"]),
        }
        for entry in fixtures
        if "alice" in entry
    ]
    assert [dict(preset.device) for preset in document.PRESETS] == expected


def _payload(config: RunConfig) -> dict[str, Any]:
    return config.to_payload()


@pytest.mark.parametrize("instance", IDS)
def test_default_config_on_the_grid(instance: str) -> None:
    python, document = _pair(instance)
    for label, overrides in config_grid(python):
        expected = python.default_config(**copied(overrides))
        produced = document.default_config(**copied(overrides))
        assert _payload(produced) == _payload(expected), label


def test_bbm92_window_defaults_from_its_cutoff() -> None:
    """test_bbm92_surface.py's three calls, int cutoff included, payload-equal."""
    python, document = _pair("bbm92")
    device = {**document.default_config().device, "alice_photon_cutoff": 3}
    del device["alice_exact_window"]
    configured = document.default_config(device=dict(device))
    assert configured.device["alice_exact_window"] == 4
    expected = python.default_config(device=dict(device))
    assert _payload(configured) == _payload(expected)
    assert configured.device["bob_exact_window"] == 2
    explicit = document.default_config(device={**device, "alice_exact_window": None})
    assert explicit.device.get("alice_exact_window") is None
    assert _payload(explicit) == _payload(
        python.default_config(device={**device, "alice_exact_window": None})
    )


def test_policies_and_order() -> None:
    assert _pair("optical_bb84")[1].device_absent == "default"
    assert _pair("bb84")[1].device_absent == "refuse"
    assert _pair("bbm92")[1].check_order == (Section.DEVICE, Section.MODEL)
    assert _pair("decoy_bb84")[1].check_order == (Section.MODEL, Section.DEVICE)


def test_numeric_device_fields(pair: tuple[ModuleType, DocumentSurface]) -> None:
    python, document = pair
    expected = tuple(
        spec.name
        for spec in python.PARAMETERS
        if spec.section is Section.DEVICE and spec.kind is not Kind.CHOICE
    )
    assert document.numeric_device_fields == expected
