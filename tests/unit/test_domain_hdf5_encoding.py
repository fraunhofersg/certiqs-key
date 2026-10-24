"""Object arrays and pickle are forbidden, and the ban is enforced.

spec/architecture.md 4.1 lists the ban; these tests are what makes it a
property of the code rather than of the prose. A bundle produced by some other
tool that smuggles a pickled object into a dataset must not load.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pytest
from bundle_format_fixtures import (
    ALICE_MARGINAL,
    BOB_V1,
    minimal_arrays,
    minimal_manifest,
)

from certiqs_key.domain._base import (
    BundleValidationError,
    UnsupportedArrayEncodingError,
)
from certiqs_key.domain.arrays import DenseArray, SparseCSCArray
from certiqs_key.domain.bundle import (
    OperatorBundle,
    parse_manifest,
    read_bundle,
    write_bundle,
)
from certiqs_key.domain.hdf5 import write_arrays
from certiqs_key.domain.validation import collect_descriptors


def written(tmp_path: Path) -> Path:
    out = tmp_path / "bundle"
    manifest = parse_manifest(minimal_manifest())
    write_bundle(out, OperatorBundle(manifest=manifest, arrays=minimal_arrays()))
    return out


def descriptors_of(document: dict[str, Any]) -> dict[str, Any]:
    return {
        dataset: descriptor
        for dataset, (descriptor, _) in collect_descriptors(
            parse_manifest(document)
        ).items()
    }


def test_writing_an_object_array_is_refused(tmp_path: Path):
    """An object array never reaches HDF5, whatever a descriptor claims."""
    document = minimal_manifest()
    arrays = minimal_arrays()
    arrays[ALICE_MARGINAL] = DenseArray(
        np.array([[object(), object()], [object(), object()]], dtype=object)
    )
    with pytest.raises(UnsupportedArrayEncodingError, match="object arrays and pickle"):
        write_arrays(tmp_path / "arrays.h5", descriptors_of(document), arrays)


def test_writing_an_object_array_also_fails_bundle_validation(tmp_path: Path):
    arrays = minimal_arrays()
    arrays[ALICE_MARGINAL] = DenseArray(
        np.array([[object(), object()], [object(), object()]], dtype=object)
    )
    manifest = parse_manifest(minimal_manifest())
    with pytest.raises(BundleValidationError, match="dtype on disk is object"):
        write_bundle(
            tmp_path / "bundle", OperatorBundle(manifest=manifest, arrays=arrays)
        )


def test_reading_a_pickled_dataset_is_refused(tmp_path: Path):
    """A pickled blob reaches HDF5 as an opaque void dtype. It does not load."""
    out = written(tmp_path)
    blob = np.void(pickle.dumps({"payload": "arbitrary code"}))
    with h5py.File(out / "arrays.h5", "a") as handle:
        del handle[f"{ALICE_MARGINAL}/real"]
        handle.create_dataset(f"{ALICE_MARGINAL}/real", data=blob)
    with pytest.raises(UnsupportedArrayEncodingError, match="object arrays and pickle"):
        read_bundle(out)


def test_reading_a_variable_length_dataset_is_refused(tmp_path: Path):
    out = written(tmp_path)
    with h5py.File(out / "arrays.h5", "a") as handle:
        del handle[f"{ALICE_MARGINAL}/real"]
        handle.create_dataset(
            f"{ALICE_MARGINAL}/real",
            shape=(2,),
            dtype=h5py.vlen_dtype(np.float64),
        )
    with pytest.raises(UnsupportedArrayEncodingError, match="pickled object"):
        read_bundle(out)


def test_reading_a_string_dataset_is_refused(tmp_path: Path):
    out = written(tmp_path)
    with h5py.File(out / "arrays.h5", "a") as handle:
        del handle[f"{ALICE_MARGINAL}/real"]
        handle.create_dataset(f"{ALICE_MARGINAL}/real", data=["a", "b"])
    with pytest.raises(UnsupportedArrayEncodingError, match="pickled object"):
        read_bundle(out)


def test_reading_a_compound_dataset_is_refused(tmp_path: Path):
    out = written(tmp_path)
    compound = np.zeros(2, dtype=[("re", "f8"), ("im", "f8")])
    with h5py.File(out / "arrays.h5", "a") as handle:
        del handle[f"{ALICE_MARGINAL}/real"]
        handle.create_dataset(f"{ALICE_MARGINAL}/real", data=compound)
    with pytest.raises(UnsupportedArrayEncodingError, match="compound dtype"):
        read_bundle(out)


def test_a_complex_dataset_is_never_written_directly(tmp_path: Path):
    """Complex values are two real datasets, never one native complex dataset."""
    out = written(tmp_path)
    with h5py.File(out / "arrays.h5", "r") as handle:
        seen: list[Any] = []

        def visit(_name: str, obj: Any) -> None:
            if isinstance(obj, h5py.Dataset):
                seen.append(obj.dtype)

        handle.visititems(visit)
    assert seen
    assert all(dtype.kind != "c" for dtype in seen)


def test_declaring_float64_while_holding_complex_values_is_refused(
    tmp_path: Path,
):
    """A complex array must declare complex128 and be split into real/imag.

    The mislabelled array is ``v1``'s ``s0`` BLOCK. An operator payload is a list of
    sector blocks (spec/architecture.md 2.9), so a full-space spelling is not
    expressible; the subject of the test -- the dtype rule -- is on the block just as it
    was on the element.
    """
    document = minimal_manifest()
    arrays = minimal_arrays()
    arrays[BOB_V1] = DenseArray(np.eye(2, dtype=np.complex128))
    document["payload"]["declaration"]["bob_povm"]["v1"]["blocks"]["s0"] = {
        "form": "array",
        "dataset": BOB_V1,
        "dtype": "float64",
        "shape": [2, 2],
        "basis": "computational.Q.s0",
        "subsystem_order": ["Q"],
        "storage": "dense",
        "semantic_role": "bob_povm_element",
    }
    with pytest.raises(UnsupportedArrayEncodingError, match="declared 'float64'"):
        write_arrays(tmp_path / "arrays.h5", descriptors_of(document), arrays)


@pytest.mark.parametrize("component", ["indices", "indptr"])
def test_writing_a_float_csc_index_array_is_refused(tmp_path: Path, component: str):
    """Regression: the write path narrows the dtype ban too.

    ``_ALLOWED_KINDS`` admits float and complex because the value payloads
    legitimately are; the index arrays are cast to int64 on their way to disk,
    so they get the narrower rule.
    """
    document = minimal_manifest()
    arrays = minimal_arrays()
    parts = {
        "data": np.array([1.0 + 0j], dtype=np.complex128),
        "indices": np.array([1], dtype=np.int64),
        "indptr": np.array([0, 0, 1], dtype=np.int64),
    }
    parts[component] = parts[component].astype(np.float64)
    arrays[BOB_V1] = SparseCSCArray(shape=(2, 2), **parts)
    with pytest.raises(UnsupportedArrayEncodingError, match="not an integer dtype"):
        write_arrays(tmp_path / "arrays.h5", descriptors_of(document), arrays)


def test_the_value_payloads_keep_the_wider_dtype_rule(tmp_path: Path):
    """Regression: narrowing the index rule did not narrow the rest.

    ``data``/``real``/``imag`` are float and complex by construction; only the
    index arrays are restricted.
    """
    document = minimal_manifest()
    arrays = minimal_arrays()
    write_arrays(tmp_path / "arrays.h5", descriptors_of(document), arrays)
    with h5py.File(tmp_path / "arrays.h5", "r") as handle:
        assert handle[f"{BOB_V1}/real"].dtype == np.float64
        assert handle[f"{BOB_V1}/indices"].dtype == np.int64


def test_the_writer_does_not_upcast_a_mislabelled_array(tmp_path: Path):
    """write_arrays refuses a mislabelled array rather than casting it.

    write_bundle validates first and so never reaches it, but write_arrays is
    callable on its own and would otherwise turn a float32 array declared float64
    into a float64 file with nothing said.
    """
    document = minimal_manifest()
    arrays = minimal_arrays()
    arrays[ALICE_MARGINAL] = DenseArray(np.eye(2, dtype=np.complex64))
    with pytest.raises(BundleValidationError, match="the writer converts nothing"):
        write_arrays(tmp_path / "arrays.h5", descriptors_of(document), arrays)
