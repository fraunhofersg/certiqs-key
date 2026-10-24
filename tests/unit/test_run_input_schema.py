"""The run-input schema describes what the engine reads, and agrees with the record's.

``run-input.schema.json`` is what a caller writing a configuration (the MCP
server's agents) checks its shape against; ``RunConfig.from_payload`` and the
instance's ``check_keys`` decide the values. Two ways it could rot: an
instance's own ``default_config()`` or ``InstanceIdentity`` stops validating,
or the record schema's ``config`` block gains a field this one lacks.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

import instances
import jsonschema
import pytest

from certiqs_key.runs.surface import RUN_PARAMETERS, InstanceIdentity
from certiqs_key.solvers.frank_wolfe.joint_options import ORACLE_CHOICES
from certiqs_key.solvers.types import (
    ADVANCED_METHODS,
    ORDINARY_METHODS,
    SEARCH_METHODS,
)


def _schema(name: str) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(
        resources.files("certiqs_key.runs").joinpath(name).read_text(encoding="utf-8")
    )
    return loaded


SCHEMA = _schema("run-input.schema.json")


def _validator(ref: str) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator({**SCHEMA, "$ref": ref})


def test_the_schema_is_a_valid_2020_12_schema() -> None:
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("surface", instances.discover(), ids=lambda s: s.DESCRIPTOR.id)
def test_every_default_config_is_a_valid_run_request(surface: Any) -> None:
    request = {
        "instance": surface.DESCRIPTOR.id,
        "config": surface.default_config().to_payload(),
    }
    _validator("#/$defs/run_request").validate(request)


@pytest.mark.parametrize("surface", instances.discover(), ids=lambda s: s.DESCRIPTOR.id)
def test_every_instance_identity_is_valid(surface: Any) -> None:
    identity = InstanceIdentity(surface.DESCRIPTOR, tuple(surface.PARAMETERS))
    _validator("#/$defs/instance").validate(identity.as_payload())
    for preset in surface.PRESETS:
        _validator("#/$defs/preset").validate(preset.as_payload())


def test_the_run_parameters_are_valid_parameter_rows() -> None:
    for spec in RUN_PARAMETERS:
        _validator("#/$defs/parameter").validate(spec.as_payload())


def test_the_config_block_names_the_record_schemas_fields() -> None:
    record_config = _schema("record.schema.json")["$defs"]["config"]["properties"]
    run_config = SCHEMA["$defs"]["run_config"]["properties"]
    # config_digest is the engine's to compute; the two discriminators are
    # payload fields the record keeps inside config without declaring them.
    assert set(record_config) - {"config_digest"} <= set(run_config)
    assert set(run_config) - set(record_config) <= {
        "device_name_fields",
        "input_preparation",
    }


def test_the_two_method_tiers_are_the_solver_s_six_methods() -> None:
    assert set(ORDINARY_METHODS) | set(ADVANCED_METHODS) == set(SEARCH_METHODS)
    assert not set(ORDINARY_METHODS) & set(ADVANCED_METHODS)


def test_the_schemas_solver_enums_are_the_method_and_oracle_constants() -> None:
    """Both schemas' solver blocks list the methods of their tier and the oracles."""
    run = SCHEMA["$defs"]["run_config"]["properties"]["solver"]["properties"]
    record = _schema("record.schema.json")["$defs"]["config"]["properties"]["solver"][
        "properties"
    ]
    for block in (run, record):
        advanced = block["advanced"]["properties"]
        assert {m for m in block["method"]["enum"] if m is not None} == set(
            ORDINARY_METHODS
        )
        assert {m for m in advanced["method"]["enum"] if m is not None} == set(
            ADVANCED_METHODS
        )
        assert {o for o in advanced["oracle"]["enum"] if o is not None} == set(
            ORACLE_CHOICES
        )
        assert advanced["gap_tolerance"]["exclusiveMinimum"] == 0
    assert set(run) == set(record)
    assert set(run["advanced"]["properties"]) == set(record["advanced"]["properties"])


def test_an_honest_override_needs_exactly_one_form_and_a_source() -> None:
    validator = _validator("#/$defs/honest_override")
    validator.validate({"table": {"ok": "1/2", "err": "1/2"}, "source": "lab"})
    for bad in (
        {"table": {"ok": "1"}},
        {"table": {}, "envelope": {"lower": {}, "upper": {}}, "source": "x"},
        {"source": "x"},
    ):
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(bad)
