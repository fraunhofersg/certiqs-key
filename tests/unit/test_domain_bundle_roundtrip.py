from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from bundle_format_fixtures import (
    ALICE_MARGINAL,
    ALICE_POVM,
    BOB_V0_BLOCKS,
    BOB_V1,
    SECTOR_DIMS,
    array_descriptor,
    minimal_arrays,
    minimal_manifest,
)

from certiqs_key.domain._base import BundleValidationError
from certiqs_key.domain.arrays import DenseArray, SparseCSCArray, dense_from_csc
from certiqs_key.domain.bundle import (
    ARRAYS_FILENAME,
    MANIFEST_FILENAME,
    OperatorBundle,
    dump_manifest,
    parse_manifest,
    read_bundle,
    write_bundle,
)


def build(
    document: dict[str, Any], arrays: dict[str, Any], directory: Path
) -> OperatorBundle:
    manifest = parse_manifest(document)
    write_bundle(directory, OperatorBundle(manifest=manifest, arrays=arrays))
    return read_bundle(directory)


def test_bundle_is_a_directory_of_two_files(tmp_path: Path):
    out = tmp_path / "bundle"
    build(minimal_manifest(), minimal_arrays(), out)
    assert sorted(p.name for p in out.iterdir()) == [ARRAYS_FILENAME, MANIFEST_FILENAME]


def test_minimal_bundle_round_trips_exactly(tmp_path: Path):
    """The hand-authored 2-dimensional Alice, two-sector bundle."""
    document = minimal_manifest()
    arrays = minimal_arrays()
    back = build(document, arrays, tmp_path / "bundle")

    assert dump_manifest(back.manifest) == dump_manifest(parse_manifest(document))
    assert set(back.arrays) == set(arrays)
    for path, original in arrays.items():
        restored = back.arrays[path]
        if isinstance(original, DenseArray):
            assert isinstance(restored, DenseArray)
            assert restored.values.dtype == original.values.dtype
            assert np.array_equal(restored.values, original.values)
        else:
            assert isinstance(restored, SparseCSCArray)
            assert restored.shape == original.shape
            assert np.array_equal(restored.data, original.data)
            assert np.array_equal(restored.indices, original.indices)
            assert np.array_equal(restored.indptr, original.indptr)


def test_manifest_on_disk_is_json_without_the_deferred_fields(tmp_path: Path):
    out = tmp_path / "bundle"
    build(minimal_manifest(), minimal_arrays(), out)
    document = json.loads((out / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert set(document) == {
        "kind",
        "schema_version",
        "mathematical_spec_version",
        "created_by",
        "implementation_version",
        "assumptions",
        "warnings",
        "payload",
    }


def test_alphabet_basis_and_tensor_order_survive_the_round_trip(tmp_path: Path):
    document = minimal_manifest()
    declaration = document["payload"]["declaration"]
    declaration["alice_marginal"]["subsystem_order"] = ["A"]
    declaration["alice_marginal"]["basis_permutation"] = [1, 0]
    declaration["alice_marginal"]["subsystem_permutation"] = [0]
    back = build(document, minimal_arrays(), tmp_path / "bundle")

    payload = back.manifest.payload
    assert payload.alphabets.bob_announcement == ("cB0", "cB1")
    assert payload.alphabets.acceptance_value == ("chat0", "chat1")
    marginal = payload.declaration.alice_marginal
    assert marginal.basis == "computational.A"
    assert marginal.subsystem_order == ("A",)
    assert marginal.basis_permutation == (1, 0)
    assert marginal.subsystem_permutation == (0,)
    block = payload.declaration.bob_povm["v0"]
    assert block.block_kind.value == "proof_sector"  # type: ignore[union-attr]
    assert tuple(block.blocks) == ("s0", "s1")  # type: ignore[union-attr]


def test_three_message_transcript_and_general_statistic_round_trip(tmp_path: Path):
    """Schema 0.4 carries phi on an arbitrary transcript tuple."""
    document = minimal_manifest()
    document["schema_version"] = "0.4.0"
    alphabets = document["payload"]["alphabets"]
    alphabets["alice_announcement"] = []
    alphabets["bob_announcement"] = []
    declaration = document["payload"]["declaration"]
    declaration["announce_alice"] = {}
    declaration["announce_bob"] = {}
    declaration["accept_statistic"] = {}
    declaration["transcript"] = [
        {
            "sender": "A",
            "alphabet": ["a"],
            "table": [["x0", [], "a"], ["x1", [], "a"]],
        },
        {
            "sender": "B",
            "alphabet": ["b"],
            "table": [["v0", ["a"], "b"], ["v1", ["a"], "b"]],
        },
        {
            "sender": "A",
            "alphabet": ["c"],
            "table": [["x0", ["a", "b"], "c"], ["x1", ["a", "b"], "c"]],
        },
    ]
    declaration["accept_statistic_general"] = [[["a", "b", "c"], "chat0"]]

    back = build(document, minimal_arrays(), tmp_path / "bundle")
    restored = back.manifest.payload.declaration
    assert restored.accept_statistic == {}
    assert restored.accept_statistic_general == ((('a', 'b', 'c'), "chat0"),)
    assert len(restored.transcript or ()) == 3
    assert back.manifest.schema_version == "0.4.0"


def test_complex_values_survive_as_separate_real_and_imag(tmp_path: Path):
    document = minimal_manifest()
    arrays = minimal_arrays()
    hermitian = np.array([[0.5, 0.25j], [-0.25j, 0.5]], dtype=np.complex128)
    arrays[ALICE_MARGINAL] = DenseArray(hermitian)
    back = build(document, arrays, tmp_path / "bundle")
    restored = back.arrays[ALICE_MARGINAL]
    assert isinstance(restored, DenseArray)
    assert np.array_equal(restored.values, hermitian)

    import h5py

    with h5py.File(tmp_path / "bundle" / ARRAYS_FILENAME, "r") as handle:
        group = handle[ALICE_MARGINAL]
        assert sorted(group.keys()) == ["imag", "real"]
        assert group["real"].dtype == np.float64
        assert group["imag"].dtype == np.float64


def test_sparse_csc_round_trips_with_index_base_one(tmp_path: Path):
    document = minimal_manifest()
    document["payload"]["declaration"]["bob_povm"]["v1"]["blocks"]["s0"][
        "index_base"
    ] = 1
    arrays = minimal_arrays()
    arrays[BOB_V1] = SparseCSCArray(
        data=np.array([1.0 + 0.0j], dtype=np.complex128),
        indices=np.array([2], dtype=np.int64),
        indptr=np.array([1, 1, 2], dtype=np.int64),
        shape=(2, 2),
    )
    back = build(document, arrays, tmp_path / "bundle")
    restored = back.arrays[BOB_V1]
    assert isinstance(restored, SparseCSCArray)
    assert np.array_equal(restored.indices, np.array([2]))
    assert np.array_equal(restored.indptr, np.array([1, 1, 2]))
    assert np.array_equal(
        dense_from_csc(restored, 1),
        np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128),
    )


def test_real_dense_and_block_data_round_trip(tmp_path: Path):
    back = build(minimal_manifest(), minimal_arrays(), tmp_path / "bundle")
    dims = back.manifest.payload.declaration.sector_dims
    for sector, path in BOB_V0_BLOCKS.items():
        restored = back.arrays[path]
        assert isinstance(restored, DenseArray)
        assert restored.values.dtype == np.float64
        assert restored.values.shape == (dims[sector], dims[sector])
        assert sector in back.manifest.payload.declaration.sector_index_set


def test_acceptance_set_arrays_round_trip(tmp_path: Path):
    """Acceptance-set arrays are ordinary descriptors.

    The set is carried, not interpreted, and its arrays take part in the
    ordinary well-formedness checks.
    """
    document = minimal_manifest()
    path = "/acceptance_set/halfspace_normals"
    document["payload"]["declaration"]["acceptance_set"] = {
        "geometry": "halfspaces",
        "data": {"offsets": [0.6, 0.6]},
        "arrays": {
            "normals": array_descriptor(
                path,
                dtype="float64",
                shape=(2, 2),
                basis="acceptance_value",
                subsystem_order=("Chat",),
                storage="dense",
                semantic_role="acceptance_set_datum",
            )
        },
    }
    arrays = minimal_arrays()
    arrays[path] = DenseArray(np.eye(2, dtype=np.float64))
    back = build(document, arrays, tmp_path / "bundle")
    assert back.manifest.payload.declaration.acceptance_set.geometry == "halfspaces"
    assert path in back.arrays


def test_constraint_list_entries_round_trip(tmp_path: Path):
    document = minimal_manifest()
    # O_k crosses in the same sector-block form as a Bob POVM element
    # (spec/architecture.md 2.9); one array per proof sector, and no other form exists.
    operator_blocks = {
        sector: f"/declaration/constraint_list/0/operator/{sector}"
        for sector in ("s0", "s1")
    }
    bound_path = "/declaration/constraint_list/0/bound"
    document["payload"]["declaration"]["constraint_list"] = [
        {
            "operator": {
                "form": "block_diagonal",
                "block_kind": "proof_sector",
                "blocks": {
                    sector: array_descriptor(
                        path,
                        dtype="complex128",
                        shape=(SECTOR_DIMS[sector], SECTOR_DIMS[sector]),
                        basis=f"computational.Q.{sector}",
                        subsystem_order=("Q",),
                        storage="dense",
                        semantic_role="constraint_operator",
                    )
                    for sector, path in operator_blocks.items()
                },
            },
            "relation": "succeq",
            "bound": array_descriptor(
                bound_path,
                dtype="complex128",
                shape=(2, 2),
                basis="computational.A",
                subsystem_order=("A",),
                storage="dense",
                semantic_role="constraint_bound",
            ),
            # The DECLARED FORM, required by the manifest,
            # `general`: the bound above is an ARRAY on A, which
            # is Theta_k and not the scalar c_k of the licensed form.
            "constraint_rhs_tag": "general",
        }
    ]
    document["payload"]["declaration"]["attack_set_license"] = {
        "supplier": "proof-reductions",
        "certificate": "lemma-9.3-equivalence",
    }
    arrays = minimal_arrays()
    for sector, path in operator_blocks.items():
        arrays[path] = DenseArray(np.eye(SECTOR_DIMS[sector], dtype=np.complex128))
    arrays[bound_path] = DenseArray(np.eye(2, dtype=np.complex128) * 0.5)
    back = build(document, arrays, tmp_path / "bundle")
    constraint = back.manifest.payload.declaration.constraint_list[0]
    assert constraint.relation.value == "succeq"
    assert back.manifest.payload.declaration.attack_set_license == {
        "supplier": "proof-reductions",
        "certificate": "lemma-9.3-equivalence",
    }


def test_write_bundle_never_overwrites(tmp_path: Path):
    out = tmp_path / "bundle"
    build(minimal_manifest(), minimal_arrays(), out)
    manifest = parse_manifest(minimal_manifest())
    with pytest.raises(BundleValidationError, match="never overwrites"):
        write_bundle(out, OperatorBundle(manifest=manifest, arrays=minimal_arrays()))


def test_reading_an_incomplete_directory_fails(tmp_path: Path):
    out = tmp_path / "bundle"
    build(minimal_manifest(), minimal_arrays(), out)
    (out / ARRAYS_FILENAME).unlink()
    with pytest.raises(BundleValidationError, match="is missing"):
        read_bundle(out)


def test_reading_invalid_json_fails(tmp_path: Path):
    out = tmp_path / "bundle"
    build(minimal_manifest(), minimal_arrays(), out)
    (out / MANIFEST_FILENAME).write_text("{not json", encoding="utf-8")
    with pytest.raises(BundleValidationError, match="not valid JSON"):
        read_bundle(out)


def test_an_unreferenced_dataset_in_the_h5_file_is_refused(tmp_path: Path):
    import h5py

    out = tmp_path / "bundle"
    build(minimal_manifest(), minimal_arrays(), out)
    with h5py.File(out / ARRAYS_FILENAME, "a") as handle:
        handle.create_dataset("/smuggled/values", data=np.zeros(3))
    with pytest.raises(BundleValidationError, match="no descriptor claims"):
        read_bundle(out)


def test_a_stray_dataset_inside_an_array_group_is_refused(tmp_path: Path):
    import h5py

    out = tmp_path / "bundle"
    build(minimal_manifest(), minimal_arrays(), out)
    with h5py.File(out / ARRAYS_FILENAME, "a") as handle:
        handle.create_dataset(f"{ALICE_POVM['x0']}/extra", data=np.zeros(3))
    with pytest.raises(BundleValidationError, match="unexpected datasets"):
        read_bundle(out)


def test_manifest_json_bytes_are_lf_on_every_platform(tmp_path: Path):
    """Regression.

    spec/architecture.md 4.1 defers a content_hash this format is shaped to
    accept later. A hash over platform-dependent line endings would be
    worthless, so the canonical bytes carry no carriage return.
    """
    out = tmp_path / "bundle"
    build(minimal_manifest(), minimal_arrays(), out)
    raw = (out / MANIFEST_FILENAME).read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"}\n")


def test_a_failed_array_write_leaves_no_bundle_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Regression: write_bundle is all or nothing."""
    out = tmp_path / "bundle"

    def explode(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("certiqs_key.domain.bundle.write_arrays", explode)
    manifest = parse_manifest(minimal_manifest())
    with pytest.raises(OSError, match="disk full"):
        write_bundle(out, OperatorBundle(manifest=manifest, arrays=minimal_arrays()))
    assert list(out.iterdir()) == []


def test_write_bundle_can_be_retried_after_a_failed_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Regression: a failed attempt does not wedge the path.

    A manifest.json surviving a failing write_arrays would get every later
    attempt refused by the never-overwrite rule.
    """
    out = tmp_path / "bundle"

    def explode(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("certiqs_key.domain.bundle.write_arrays", explode)
    manifest = parse_manifest(minimal_manifest())
    with pytest.raises(OSError, match="disk full"):
        write_bundle(out, OperatorBundle(manifest=manifest, arrays=minimal_arrays()))

    monkeypatch.undo()
    back = build(minimal_manifest(), minimal_arrays(), out)
    assert set(back.arrays) == set(minimal_arrays())


def test_a_failed_rename_leaves_no_bundle_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Regression: even a half-completed move is rolled back."""
    out = tmp_path / "bundle"
    calls: list[int] = []
    real_replace = os.replace

    def flaky(source: Any, destination: Any) -> None:
        calls.append(1)
        if len(calls) == 2:
            raise OSError("rename failed")
        real_replace(source, destination)

    monkeypatch.setattr("certiqs_key.domain.bundle.os.replace", flaky)
    manifest = parse_manifest(minimal_manifest())
    with pytest.raises(OSError, match="rename failed"):
        write_bundle(out, OperatorBundle(manifest=manifest, arrays=minimal_arrays()))
    assert list(out.iterdir()) == []
