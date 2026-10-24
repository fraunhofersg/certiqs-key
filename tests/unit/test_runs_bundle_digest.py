"""The bundle and docked-declaration digests cover the operators' entries.

runs/artefact-digest-covers-arrays. An operator bundle is a manifest PLUS
arrays, and the manifest carries array descriptors and not one entry, so a
digest of the manifest alone gave two declarations that differ only in their
operators the same id. These tests would fail on that digest.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
from dummy_bundles import build_bundle
from toy_declarations import toy

from certiqs_key.domain.arrays import DenseArray, SparseCSCArray
from certiqs_key.domain.bundle import OperatorBundle
from certiqs_key.runs.flow import artefact_digest, bundle_digest


def test_two_declarations_differing_only_in_operator_entries_get_two_ids() -> None:
    """TOY-1 and TOY-1 with Bob's two POVM elements exchanged.

    Same alphabet, sectors, shapes, scalars and manifest; different operator
    entries. The manifest-only digest cannot tell them apart; this one does.
    """
    declared = toy("TOY-1")
    first, second = declared.bob_povm
    swapped = replace(
        declared,
        bob_povm={first: declared.bob_povm[second], second: declared.bob_povm[first]},
    )
    one, other = build_bundle(declared), build_bundle(swapped)
    manifest = one.manifest.model_dump(mode="json")
    assert manifest == other.manifest.model_dump(mode="json")
    assert artefact_digest(manifest) == artefact_digest(
        other.manifest.model_dump(mode="json")
    )
    assert bundle_digest(one) != bundle_digest(other)
    # ... and the digest is a function of the content, not of the object.
    assert bundle_digest(one) == bundle_digest(build_bundle(declared))


def _dense_bundle(values: np.ndarray) -> OperatorBundle:
    base = build_bundle(toy("TOY-1"))
    dataset = next(iter(base.arrays))
    return OperatorBundle(
        manifest=base.manifest, arrays={**base.arrays, dataset: DenseArray(values)}
    )


def test_an_entry_str_would_elide_still_moves_the_digest() -> None:
    """The trap the item names: ``str()`` of a large array truncates.

    A change deep inside a 4096-entry array is invisible to its ``str()``
    (NumPy summarises it with an ellipsis) and must still change the digest.
    """
    values = np.zeros((64, 64))
    changed = values.copy()
    changed[31, 31] = 1e-300
    assert str(values) == str(changed)
    assert bundle_digest(_dense_bundle(values)) != bundle_digest(
        _dense_bundle(changed)
    )


def test_shape_dtype_and_byte_order_are_read_as_the_numbers_are() -> None:
    values = np.arange(6, dtype=np.float64)
    # Same bytes, other shape: a different array.
    assert bundle_digest(_dense_bundle(values.reshape(2, 3))) != bundle_digest(
        _dense_bundle(values.reshape(3, 2))
    )
    # Same numbers, other dtype: a different array.
    assert bundle_digest(_dense_bundle(values)) != bundle_digest(
        _dense_bundle(values.astype(np.complex128))
    )
    # Same numbers in the other byte order or memory layout: the same array.
    square = np.arange(9, dtype=np.float64).reshape(3, 3)
    assert bundle_digest(_dense_bundle(square)) == bundle_digest(
        _dense_bundle(square.astype(square.dtype.newbyteorder(">")))
    )
    assert bundle_digest(_dense_bundle(square)) == bundle_digest(
        _dense_bundle(np.asfortranarray(square))
    )


def test_a_sparse_payload_is_covered_by_all_four_of_its_parts() -> None:
    base = build_bundle(toy("TOY-1"))
    dataset = next(iter(base.arrays))

    def with_csc(payload: SparseCSCArray) -> str:
        return bundle_digest(
            OperatorBundle(
                manifest=base.manifest, arrays={**base.arrays, dataset: payload}
            )
        )

    reference = SparseCSCArray(
        data=np.array([1.0, 2.0]),
        indices=np.array([0, 1], dtype=np.int64),
        indptr=np.array([0, 1, 2], dtype=np.int64),
        shape=(2, 2),
    )
    digest = with_csc(reference)
    assert with_csc(replace(reference, data=np.array([1.0, 3.0]))) != digest
    assert (
        with_csc(replace(reference, indices=np.array([1, 0], dtype=np.int64)))
        != digest
    )
    assert (
        with_csc(replace(reference, indptr=np.array([0, 2, 2], dtype=np.int64)))
        != digest
    )
    assert with_csc(replace(reference, shape=(3, 2))) != digest
