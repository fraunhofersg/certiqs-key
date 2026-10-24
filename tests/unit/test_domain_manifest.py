from __future__ import annotations

import json
import re
from typing import Any

import pytest
from bundle_format_fixtures import minimal_manifest

from certiqs_key.domain._base import BundleValidationError
from certiqs_key.domain.bundle import dump_manifest, parse_manifest
from certiqs_key.domain.manifest import DEFERRED_ENVELOPE_FIELDS


def test_minimal_manifest_parses():
    manifest = parse_manifest(minimal_manifest())
    assert manifest.kind == "operator-bundle"
    assert manifest.schema_version == "0.3.0"
    assert manifest.mathematical_spec_version == "meat-core@0.5.0"


def test_manifest_json_round_trips_through_text():
    document = minimal_manifest()
    once = parse_manifest(document)
    twice = parse_manifest(json.loads(dump_manifest(once)))
    assert dump_manifest(once) == dump_manifest(twice)


@pytest.mark.parametrize("field", DEFERRED_ENVELOPE_FIELDS)
def test_deferred_envelope_field_is_rejected(field: str):
    """spec/architecture.md 4.1 defers these envelope fields.

    Accepting one would give it a meaning now that it must not carry until
    content-addressing switches on.
    """
    document = minimal_manifest()
    document[field] = "whatever"
    with pytest.raises(BundleValidationError, match=re.escape(field)):
        parse_manifest(document)


def test_unknown_envelope_field_is_rejected():
    document = minimal_manifest()
    document["extra_field"] = 1
    with pytest.raises(BundleValidationError, match="extra_field"):
        parse_manifest(document)


def test_unknown_declaration_key_is_rejected():
    document = minimal_manifest()
    document["payload"]["declaration"]["bob_dim"] = 2
    with pytest.raises(BundleValidationError, match="bob_dim"):
        parse_manifest(document)


@pytest.mark.parametrize(
    "version",
    ["meat-core@0.5.0-draft", "meat-core", "0.5.0", "Meat-Core@0.5.0", "meat-core@0.5"],
)
def test_bad_mathematical_spec_version_is_rejected(version: str):
    document = minimal_manifest()
    document["mathematical_spec_version"] = version
    with pytest.raises(BundleValidationError, match="mathematical_spec_version"):
        parse_manifest(document)


@pytest.mark.parametrize("version", ["0.5.0", "0.1", "1.0.0", "0.2.0-draft", ""])
def test_an_unsupported_schema_version_is_refused(version: str):
    """A reader accepts the versions it knows and refuses to guess at another.

    ``0.5.0`` is not a version the reader knows (spec/architecture.md 2.9), so
    the test exercises "the next version up" and not only malformed strings. The
    RETIRED versions 0.1.0 and 0.2.0 are not here either: they are refused by name and
    by their own type, in ``tests/unit/test_schema_030_operator_form.py``.
    """
    document = minimal_manifest()
    document["schema_version"] = version
    with pytest.raises(BundleValidationError, match="schema_version"):
        parse_manifest(document)


def test_the_supported_version_parses_and_reduction_chain_is_optional_in_it():
    """0.3.0 and 0.4.0 are the whole of the compatibility rule (2.9).

    ``reduction_chain`` entered at 0.2.0 and is carried here unchanged and
    optional; absent means no chain was recorded, and that is not a
    statement about which version stamped the bundle.
    """
    document = minimal_manifest()
    manifest = parse_manifest(document)
    assert manifest.schema_version == "0.3.0"
    assert manifest.payload.reduction_chain is None


def test_kind_is_pinned():
    document = minimal_manifest()
    document["kind"] = "proof-instance"
    with pytest.raises(BundleValidationError, match="kind"):
        parse_manifest(document)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("alpha", 1.0),
        ("alpha", 2.0),
        ("alpha", 0.5),
        ("eps_pa", 0.0),
        ("eps_pa", 1.5),
        ("eps_ev", 0.0),
        ("eps_ev", -1e-12),
        ("lambda_ec", -1),
        ("lambda_ec", 1.5),
    ],
)
def test_parameter_domains_are_enforced(key: str, value: Any):
    document = minimal_manifest()
    document["payload"]["parameters"][key] = value
    with pytest.raises(BundleValidationError, match=key):
        parse_manifest(document)


def test_alpha_endpoints_are_outside_the_declared_domain():
    """meat-core 2.4 declares alpha in the OPEN interval (1, 2)."""
    document = minimal_manifest()
    document["payload"]["parameters"]["alpha"] = 1.9999999
    assert parse_manifest(document).payload.parameters.alpha == 1.9999999


def test_rounds_must_be_at_least_one():
    document = minimal_manifest()
    document["payload"]["declaration"]["rounds"] = 0
    with pytest.raises(BundleValidationError, match="rounds"):
        parse_manifest(document)


def test_key_holder_is_restricted_to_a_and_b():
    document = minimal_manifest()
    document["payload"]["declaration"]["key_holder"] = "C"
    with pytest.raises(BundleValidationError, match="key_holder"):
        parse_manifest(document)


@pytest.mark.parametrize("holder", ["A", "B"])
def test_both_key_holders_are_accepted(holder: str):
    document = minimal_manifest()
    document["payload"]["declaration"]["key_holder"] = holder
    assert parse_manifest(document).payload.declaration.key_holder.value == holder


def test_empty_constraint_list_is_the_default_and_is_legal():
    """meat-core 2.1 allows m >= 0, and m = 0 needs no attack-set license."""
    document = minimal_manifest()
    del document["payload"]["declaration"]["constraint_list"]
    manifest = parse_manifest(document)
    assert manifest.payload.declaration.constraint_list == ()
    assert manifest.payload.declaration.attack_set_license is None


def test_sparse_descriptor_requires_a_declared_index_base():
    document = minimal_manifest()
    del document["payload"]["declaration"]["bob_povm"]["v1"]["blocks"]["s0"][
        "index_base"
    ]
    with pytest.raises(BundleValidationError, match="index_base"):
        parse_manifest(document)


def test_dense_descriptor_may_not_declare_an_index_base():
    document = minimal_manifest()
    document["payload"]["declaration"]["alice_marginal"]["index_base"] = 0
    with pytest.raises(BundleValidationError, match="index_base"):
        parse_manifest(document)


def test_index_base_must_be_zero_or_one():
    document = minimal_manifest()
    document["payload"]["declaration"]["bob_povm"]["v1"]["blocks"]["s0"][
        "index_base"
    ] = 2
    with pytest.raises(BundleValidationError, match="index_base"):
        parse_manifest(document)


def test_dataset_path_must_be_addressable_in_hdf5():
    document = minimal_manifest()
    document["payload"]["declaration"]["alice_marginal"]["dataset"] = "relative/path"
    with pytest.raises(BundleValidationError, match="dataset"):
        parse_manifest(document)


def test_permutation_must_be_a_permutation():
    document = minimal_manifest()
    document["payload"]["declaration"]["alice_marginal"]["basis_permutation"] = [0, 0]
    with pytest.raises(BundleValidationError, match="basis_permutation"):
        parse_manifest(document)


def test_subsystem_order_may_not_repeat_a_subsystem():
    document = minimal_manifest()
    document["payload"]["declaration"]["alice_marginal"]["subsystem_order"] = ["A", "A"]
    with pytest.raises(BundleValidationError, match="subsystem_order"):
        parse_manifest(document)


def test_operator_form_is_explicit():
    """The array/block-diagonal union is tagged, never guessed."""
    document = minimal_manifest()
    del document["payload"]["declaration"]["bob_povm"]["v0"]["form"]
    with pytest.raises(BundleValidationError, match="form"):
        parse_manifest(document)
