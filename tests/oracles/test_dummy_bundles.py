"""The dummy operator bundles: they are well-formed, and they say what the toys say.

The oracle set calls for "dummy operator bundles small enough to reason
about"; the solver takes one of these as its input. So two things must
hold: each bundle is valid in the versioned format of spec/architecture.md
Section 6.1 and survives a write/read round trip, and its declaration is the
same declaration whose answer the registry has frozen.

The mathematical conditions the format deliberately does NOT check -- positivity,
POVM completeness, block-diagonality of the Bob POVM, tau_A-homogeneity of the
constraint list -- are checked here instead, against the toys, because they are
what make each instance a legitimate ``meat-core`` input.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from dummy_bundles import SPEC_VERSION, build_bundle, bundle_documents
from toy_declarations import ALL_TOYS, ToyDeclaration

from certiqs_key.domain.arrays import DenseArray
from certiqs_key.domain.bundle import (
    ARRAYS_FILENAME,
    MANIFEST_FILENAME,
    dump_manifest,
    parse_manifest,
    read_bundle,
    write_bundle,
)
from certiqs_key.domain.validation import validate_bundle


@pytest.mark.contract
@pytest.mark.parametrize("toy", ALL_TOYS, ids=lambda t: t.toy_id)
def test_every_toy_is_a_valid_operator_bundle(toy: ToyDeclaration) -> None:
    """The format accepts every toy declaration as data."""
    bundle = build_bundle(toy)
    validate_bundle(bundle.manifest, bundle.arrays)
    assert bundle.manifest.mathematical_spec_version == SPEC_VERSION


@pytest.mark.contract
@pytest.mark.parametrize("toy", ALL_TOYS, ids=lambda t: t.toy_id)
def test_bundles_round_trip_through_disk(toy: ToyDeclaration, tmp_path: Path) -> None:
    """A bundle written out and read back is the same bundle."""
    bundle = build_bundle(toy)
    directory = tmp_path / toy.toy_id.replace("(", "_").replace(")", "_")
    write_bundle(directory, bundle)
    assert (directory / MANIFEST_FILENAME).is_file()
    assert (directory / ARRAYS_FILENAME).is_file()

    restored = read_bundle(directory)
    assert restored.manifest == bundle.manifest
    assert set(restored.arrays) == set(bundle.arrays)
    for path, payload in bundle.arrays.items():
        assert isinstance(payload, DenseArray)
        other = restored.arrays[path]
        assert isinstance(other, DenseArray)
        assert np.allclose(other.values, payload.values)
        assert other.values.dtype == payload.values.dtype


@pytest.mark.contract
@pytest.mark.parametrize("toy", ALL_TOYS, ids=lambda t: t.toy_id)
def test_manifest_serializes_to_json_and_parses_back(toy: ToyDeclaration) -> None:
    """The manifest is plain JSON; no Python objects leak into the artifact."""
    manifest, _ = bundle_documents(toy)
    text = json.dumps(manifest)
    assert parse_manifest(json.loads(text)) == parse_manifest(manifest)
    assert json.loads(dump_manifest(parse_manifest(manifest))) is not None


@pytest.mark.contract
@pytest.mark.parametrize("toy", ALL_TOYS, ids=lambda t: t.toy_id)
def test_bundle_declaration_matches_the_toy(toy: ToyDeclaration) -> None:
    """The serialized declaration is the one the registry froze an answer for."""
    declaration = build_bundle(toy).manifest.payload.declaration
    assert declaration.alice_dim == toy.alice_dim
    assert declaration.sector_index_set == toy.sector_index_set
    assert declaration.sector_dims == toy.sector_dims
    assert declaration.key_holder.value == toy.key_holder
    assert len(declaration.constraint_list) == len(toy.constraint_list)
    assert (declaration.attack_set_license is None) is (toy.attack_set_license is None)
    for (x, v), value in toy.key_map.items():
        assert declaration.key_map[x][v] == value


@pytest.mark.contract
@pytest.mark.parametrize("toy", ALL_TOYS, ids=lambda t: t.toy_id)
def test_the_mathematics_the_format_does_not_check(toy: ToyDeclaration) -> None:
    """Admissibility, checked here because the format deliberately does not.

    The boundary is stated in ``certiqs_key.domain.validation``: positivity, POVM
    completeness, Hermiticity and block-diagonality are ``meat-core`` bundle
    validation (spec/architecture.md 3.6), not format validation.
    """
    # (ii) tau_A is a normalized state.
    tau = np.asarray(toy.alice_marginal, dtype=np.float64)
    assert np.allclose(tau, tau.conj().T)
    assert float(np.trace(tau)) == pytest.approx(1.0)
    assert float(np.min(np.linalg.eigvalsh(tau))) >= -1e-12

    # (iii) {M_x} is a POVM on A.
    alice_total = sum(np.asarray(m, dtype=np.float64) for m in toy.alice_povm.values())
    assert np.allclose(alice_total, np.eye(toy.alice_dim))
    for element in toy.alice_povm.values():
        assert float(np.min(np.linalg.eigvalsh(np.asarray(element)))) >= -1e-12

    # (iii) {F_v} is a POVM on Q and every element is sector-block-diagonal.
    for sector in toy.sector_index_set:
        blocks = [
            np.asarray(toy.bob_povm[v][sector], dtype=np.float64) for v in toy.bob_povm
        ]
        for block in blocks:
            assert block.shape == (toy.sector_dims[sector],) * 2
            assert float(np.min(np.linalg.eigvalsh(block))) >= -1e-12
        assert np.allclose(sum(blocks), np.eye(toy.sector_dims[sector]))

    # (v) sifting is announcement-determined: r(x, v) = perp depends on the
    # announcement class alone.
    by_class: dict[tuple[str, str], set[bool]] = {}
    for (x, v), value in toy.key_map.items():
        klass = (toy.announce_alice[x], toy.announce_bob[v])
        by_class.setdefault(klass, set()).add(value is None)
    for klass, flags in by_class.items():
        assert len(flags) == 1, (toy.toy_id, klass)

    # (vi) the constraint operators are Hermitian, block-diagonal and sized.
    for entry in toy.constraint_list:
        assert set(entry.operator_blocks) == set(toy.sector_index_set)
        for sector, block in entry.operator_blocks.items():
            matrix = np.asarray(block, dtype=np.float64)
            assert matrix.shape == (toy.sector_dims[sector],) * 2
            assert np.allclose(matrix, matrix.conj().T)
        bound = np.asarray(entry.bound, dtype=np.float64)
        assert bound.shape == (toy.alice_dim, toy.alice_dim)
        assert np.allclose(bound, bound.conj().T)


@pytest.mark.contract
@pytest.mark.parametrize("toy", ALL_TOYS, ids=lambda t: t.toy_id)
def test_recorded_homogeneity_matches_the_operators(toy: ToyDeclaration) -> None:
    """Definition def:homog: Theta_k = c_k tau_A, mechanically checkable."""
    tau = np.asarray(toy.alice_marginal, dtype=np.float64)
    for entry in toy.constraint_list:
        bound = np.asarray(entry.bound, dtype=np.float64)
        if entry.homogeneous_scalar is None:
            assert not any(
                np.allclose(bound, c * tau) for c in np.linspace(-4.0, 4.0, 1601)
            ), toy.toy_id
        else:
            assert np.allclose(bound, entry.homogeneous_scalar * tau), toy.toy_id


@pytest.mark.contract
@pytest.mark.parametrize("toy", ALL_TOYS, ids=lambda t: t.toy_id)
def test_key_holder_can_actually_compute_the_raw_key(toy: ToyDeclaration) -> None:
    """Admissibility (viii): r factors through the holder's outcome and a(x, v)."""
    seen: dict[tuple[str, str, str], int | None] = {}
    for (x, v), value in toy.key_map.items():
        klass = (toy.announce_alice[x], toy.announce_bob[v])
        own = x if toy.key_holder == "A" else v
        signature = (own, *klass)
        if signature in seen:
            assert seen[signature] == value, (toy.toy_id, signature)
        seen[signature] = value


@pytest.mark.contract
def test_bundles_carry_the_declared_conventions() -> None:
    """Contract Section 2.5, mirrored into the bundle's machine-readable assumptions."""
    manifest, _ = bundle_documents(ALL_TOYS[0])
    assumptions = manifest["assumptions"]
    assert assumptions["test_statistics_model"] == "output_state"
    assert assumptions["round_homogeneity"] is True
    assert assumptions["log_base"] == 2
    assert assumptions["entropy_units"] == "bits"
    assert assumptions["entropy_variant"] == "sandwiched-renyi"
    assert assumptions["arrow"] == "up"


@pytest.mark.contract
def test_the_bundle_builder_refuses_the_0_3_0_declarations_it_cannot_express() -> None:
    """Fail-closed: the 0.1.0 manifest has no spelling for the new slots.

    Silently coercing ``alice_marginal = none`` into a matrix would serialize a
    TRUSTED-source declaration for an UNTRUSTED one -- the unsafe direction,
    measured by ``O-UNTRUSTED-CONSERVATIVE``. Extending the manifest and
    ``schemas/proof-instance/operator-bundle.schema.json`` is solver-side work,
    and until it happens the builder refuses rather than guesses.
    """
    from toy_declarations import SOURCE_MODE_TOYS

    for toy in SOURCE_MODE_TOYS:
        with pytest.raises(NotImplementedError):
            bundle_documents(toy)
