"""The three 0.3.0 declaration slots, as data and as declarations.

contract 0.3.0 widened the declaration type in three places, and this file is
where the WIRE FORM of that widening is checked: the marginal slot may hold
``none``, a ``source_replacement_license`` may be carried, a non-default
``party_partition`` may be declared, and a constraint right-hand side may be a
real scalar.

Two properties are load-bearing and are asserted rather than assumed:

* an ABSENT key means what the contract says it means -- ``alice_marginal``
  absent is untrusted-source mode, ``party_partition`` absent is the DEFAULT
  partition of Definition ``def:declaration``, which "reproduces versions 0.2.x
  of this contract verbatim". Both defaults are the conservative reading;
* the frozen builder of ``tests/oracles/dummy_bundles.py`` and this run's
  ``tests/support/mode_bundles.py`` produce the SAME manifest for every 0.2.x
  toy, so the format extension changed nothing about the declarations that
  already existed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from dummy_bundles import bundle_documents as frozen_documents
from mode_bundles import build_bundle, bundle_documents
from toy_declarations import ALL_TOYS, SOURCE_MODE_TOYS, ToyDeclaration, toy

from certiqs_key.domain.bundle import (
    BundleValidationError,
    dump_manifest,
    parse_manifest,
    read_bundle,
    validate_bundle,
    write_bundle,
)
from certiqs_key.domain.manifest import PartyLabel
from certiqs_key.domain.validation import validate_manifest
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import SourceMode
from certiqs_key.meat_core.errors import DeclarationError


def document(toy_id: str) -> dict:
    """Return the manifest document of a 0.3.0 toy, as plain data."""
    manifest, _ = bundle_documents(toy(toy_id))
    return manifest


# ---------------------------------------------------------------------------
# The marginal slot
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_null_marginal_round_trips_as_untrusted_source_mode() -> None:
    """Def. ``def:declaration``: ``null`` is the slot value ``none``."""
    manifest = document("TOY-8-UN")
    assert manifest["payload"]["declaration"]["alice_marginal"] is None
    parsed = parse_manifest(manifest)
    assert parsed.payload.declaration.alice_marginal is None
    validate_manifest(parsed)
    declaration = declaration_from_bundle(build_bundle(toy("TOY-8-UN")))
    assert declaration.alice_marginal is None
    assert declaration.source_mode is SourceMode.UNTRUSTED


@pytest.mark.contract
def test_an_absent_marginal_key_is_the_same_as_an_explicit_null() -> None:
    """Absent and ``null`` are one value; the default is the safe direction.

    Remark ``transmitter/rem:source-mode`` (a): untrusted-source mode never RAISES
    ``h_low``, so a producer that omits the key loses rate and cannot overstate
    it. That is why the format defaults rather than refuses.
    """
    manifest = document("TOY-8-UN")
    del manifest["payload"]["declaration"]["alice_marginal"]
    parsed = parse_manifest(manifest)
    assert parsed.payload.declaration.alice_marginal is None
    validate_manifest(parsed)


@pytest.mark.contract
def test_a_zero_marginal_is_rejected_on_both_of_its_grounds() -> None:
    """Remark ``transmitter/rem:source-mode`` (c): ``tau_A = 0`` is neither mode.

    Both grounds are named in the error, because an implementation that rejects
    it for only one of them will accept the other spelling of the same mistake:
    def:admissible-declaration (ii) normalization, and the empty feasible set of
    def:admissible-declaration (vii).
    """
    from dataclasses import replace

    from certiqs_key.meat_core.declaration.validation import validate_declaration

    declaration = declaration_from_bundle(build_bundle(toy("TOY-9")))
    with pytest.raises(DeclarationError) as raised:
        validate_declaration(
            replace(declaration, alice_marginal=np.zeros((3, 3), dtype=np.complex128)),
        )
    message = str(raised.value)
    assert "transmitter/rem:source-mode (c)" in message
    assert "def:admissible-declaration (ii)" in message
    assert "def:admissible-declaration (vii)" in message


@pytest.mark.contract
def test_an_untrusted_bundle_survives_the_disk(tmp_path: Path) -> None:
    """No marginal array is written, and none is expected back."""
    bundle = build_bundle(toy("TOY-10"))
    directory = tmp_path / "bundle"
    write_bundle(directory, bundle)
    reloaded = read_bundle(directory)
    validate_bundle(reloaded.manifest, reloaded.arrays)
    assert "/declaration/alice_marginal" not in reloaded.arrays
    declaration = declaration_from_bundle(reloaded)
    assert declaration.source_mode is SourceMode.UNTRUSTED
    assert declaration.party_partition is not None


# ---------------------------------------------------------------------------
# The source-replacement licence
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_source_replacement_licence_round_trips() -> None:
    """Section 2.1: an optional attestation, carried and never interpreted."""
    manifest = document("TOY-9")
    record = manifest["payload"]["declaration"]["source_replacement_license"]
    assert record == {"certificate": "supplied by proof-reductions"}
    declaration = declaration_from_bundle(build_bundle(toy("TOY-9")))
    assert declaration.source_replacement_license == record


@pytest.mark.contract
def test_an_empty_source_replacement_licence_is_rejected() -> None:
    """An empty record names nothing; omit it instead (the untrusted mode)."""
    manifest = document("TOY-9")
    manifest["payload"]["declaration"]["source_replacement_license"] = {}
    with pytest.raises(BundleValidationError, match="source_replacement_license"):
        validate_manifest(parse_manifest(manifest))


# ---------------------------------------------------------------------------
# The party partition
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_party_partition_round_trips_with_both_of_its_parts() -> None:
    """Def. ``def:declaration``: readout maps, alphabets and system metadata."""
    manifest = document("TOY-10")
    record = manifest["payload"]["declaration"]["party_partition"]
    assert record["alphabet_alice"] == ["a0", "a1"]
    assert record["alphabet_bob"] == ["b0", "b1"]
    assert record["readout_alice"]["x0"]["v10"] == "a1"
    assert record["readout_bob"]["x0"]["v10"] == "b0"
    assert record["party_of_alice_system"] == "A"
    assert record["party_of_sector_factors"] == {"s0": ["A", "B"], "s1": ["A", "B"]}

    declaration = declaration_from_bundle(build_bundle(toy("TOY-10")))
    partition = declaration.partition
    assert partition.is_default is False
    assert partition.readout_alice[("x0", "v10")] == "a1"
    assert partition.party_of_alice_system is PartyLabel.ALICE
    assert partition.party_of_sector_factors["s0"] == (
        PartyLabel.ALICE,
        PartyLabel.BOB,
    )


@pytest.mark.contract
def test_an_absent_party_partition_is_the_default_one() -> None:
    """Def. ``def:declaration``: the default "reproduces versions 0.2.x verbatim"."""
    manifest = document("TOY-8-UN")
    assert manifest["payload"]["declaration"]["party_partition"] is None
    declaration = declaration_from_bundle(build_bundle(toy("TOY-8-UN")))
    assert declaration.party_partition is None
    assert declaration.partition.is_default is True


@pytest.mark.contract
def test_a_readout_map_that_is_not_total_is_rejected() -> None:
    """Part (a) is checked as data: both readouts are total on ``X x V``."""
    manifest = document("TOY-10")
    del manifest["payload"]["declaration"]["party_partition"]["readout_alice"]["x0"][
        "v11"
    ]
    with pytest.raises(BundleValidationError, match="readout_alice"):
        validate_manifest(parse_manifest(manifest))


@pytest.mark.contract
def test_a_readout_outside_its_declared_alphabet_is_rejected() -> None:
    """The codomain of ``pi_A`` is the declared ``O_A`` and nothing else."""
    manifest = document("TOY-10")
    manifest["payload"]["declaration"]["party_partition"]["readout_alice"]["x0"][
        "v11"
    ] = "a2"
    with pytest.raises(BundleValidationError, match="readout_alice"):
        validate_manifest(parse_manifest(manifest))


@pytest.mark.contract
def test_a_sector_without_a_party_label_is_rejected() -> None:
    """Part (b) is checked for coverage: one entry per declared sector."""
    manifest = document("TOY-10")
    del manifest["payload"]["declaration"]["party_partition"][
        "party_of_sector_factors"
    ]["s1"]
    with pytest.raises(BundleValidationError, match="party_of_sector_factors"):
        validate_manifest(parse_manifest(manifest))


@pytest.mark.contract
def test_the_announcement_tables_are_keyed_by_the_readout_alphabets() -> None:
    """Admissibility (viii): a party announces a function of its OWN readout."""
    manifest = document("TOY-10")
    assert set(manifest["payload"]["declaration"]["announce_alice"]) == {"a0", "a1"}
    manifest["payload"]["declaration"]["announce_alice"] = {"x0": "cA0"}
    with pytest.raises(BundleValidationError, match="announce_alice"):
        validate_manifest(parse_manifest(manifest))


# ---------------------------------------------------------------------------
# The scalar constraint right-hand side
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_scalar_constraint_bound_round_trips_as_a_number() -> None:
    """Def. ``def:homog`` (b): ``Theta_k = c_k`` is a real number, not a matrix."""
    manifest = document("TOY-5-UN")
    entry = manifest["payload"]["declaration"]["constraint_list"][0]
    assert entry["bound"] == 0.5
    assert not isinstance(entry["bound"], dict)
    declaration = declaration_from_bundle(build_bundle(toy("TOY-5-UN")))
    (constraint,) = declaration.constraint_list
    assert constraint.is_scalar is True
    assert constraint.scalar_bound == 0.5
    with pytest.raises(TypeError, match="rem:homog"):
        _ = constraint.operator_bound


@pytest.mark.contract
def test_a_boolean_constraint_bound_is_rejected() -> None:
    """JSON would widen ``true`` to ``1``; a bound is a real number, not a flag."""
    manifest = document("TOY-5-UN")
    manifest["payload"]["declaration"]["constraint_list"][0]["bound"] = True
    with pytest.raises(BundleValidationError, match="boolean"):
        parse_manifest(manifest)


@pytest.mark.contract
def test_a_non_finite_scalar_bound_is_rejected() -> None:
    """A bound is a real number; ``inf`` is not one."""
    manifest = document("TOY-5-UN")
    manifest["payload"]["declaration"]["constraint_list"][0]["bound"] = float("inf")
    with pytest.raises(BundleValidationError, match="not finite"):
        validate_manifest(parse_manifest(manifest))


@pytest.mark.contract
def test_a_scalar_bound_claims_no_dataset() -> None:
    """There is no array to claim, so no dataset is registered for it."""
    manifest, arrays = bundle_documents(toy("TOY-5-UN"))
    assert not any("bound" in path for path in arrays)
    parsed = parse_manifest(manifest)
    validate_bundle(parsed, arrays)


# ---------------------------------------------------------------------------
# The two builders agree on everything that already existed
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize("candidate", ALL_TOYS, ids=lambda t: t.toy_id)
def test_the_two_builders_agree_on_the_0_2_x_toys(candidate: ToyDeclaration) -> None:
    """The format extension changed nothing about the declarations that existed.

    The frozen builder writes no ``source_replacement_license`` and no
    ``party_partition`` key at all; this one writes them as ``null``. Those are
    the same declaration by construction, and every other key must match
    exactly.
    """
    mine, my_arrays = bundle_documents(candidate)
    theirs, their_arrays = frozen_documents(candidate)
    mine["created_by"] = theirs["created_by"]

    my_declaration = mine["payload"]["declaration"]
    assert my_declaration.pop("source_replacement_license") is None
    assert my_declaration.pop("party_partition") is None
    assert mine == theirs
    assert set(my_arrays) == set(their_arrays)
    for path, payload in my_arrays.items():
        assert np.allclose(payload.values, their_arrays[path].values)


@pytest.mark.contract
@pytest.mark.parametrize("candidate", SOURCE_MODE_TOYS, ids=lambda t: t.toy_id)
def test_the_frozen_builder_still_refuses_what_it_cannot_express(
    candidate: ToyDeclaration,
) -> None:
    """The frozen refusal is untouched, and it is not routed around.

    ``tests/oracles/`` is read-only for this run. Four of the seven 0.3.0 toys
    are refused there by name; the other three are refused for one of the same
    four reasons. Nothing here monkeypatches or shadows that module -- the new
    builder is a separate module in a separate tree.
    """
    if candidate.toy_id == "TOY-8-T":
        # A trusted, full-rank, default-partition declaration with a licence:
        # the frozen builder refuses it only for the licence.
        with pytest.raises(NotImplementedError, match="source_replacement_license"):
            frozen_documents(candidate)
        return
    with pytest.raises(NotImplementedError):
        frozen_documents(candidate)


@pytest.mark.contract
def test_every_0_3_0_bundle_serializes_and_validates(tmp_path: Path) -> None:
    """All seven, through ``manifest.json`` text and back."""
    for candidate in SOURCE_MODE_TOYS:
        manifest, arrays = bundle_documents(candidate)
        text = dump_manifest(parse_manifest(manifest))
        reparsed = parse_manifest(__import__("json").loads(text))
        validate_bundle(reparsed, arrays)
        directory = tmp_path / candidate.toy_id.replace("(", "_").replace(")", "_")
        write_bundle(directory, build_bundle(candidate))
        reloaded = read_bundle(directory)
        assert reloaded.manifest.payload.declaration.alice_dim == candidate.alice_dim
