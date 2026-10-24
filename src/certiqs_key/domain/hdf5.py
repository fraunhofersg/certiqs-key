"""Reading and writing ``arrays.h5``: the numerical half of a bundle.

The HDF5 file is deliberately dumb. It holds numbers and nothing else: no
attributes, no metadata, no type tags. Everything that says what an array
*means* lives in ``manifest.json``, so reading is manifest-driven -- a
descriptor is consulted first and the file is read the way it says.

Layout. Each array is a group at its declared dataset path, holding:

===================  ==========================================================
storage / dtype      datasets in the group
===================  ==========================================================
dense, float64       ``data``
dense, complex128    ``real``, ``imag``
sparse_csc, float64  ``data``, ``indices``, ``indptr``, ``shape``
sparse_csc, cplx128  ``real``, ``imag``, ``indices``, ``indptr``, ``shape``
===================  ==========================================================

A complex array is therefore *always* two real datasets. A NumPy complex dtype
is never handed to HDF5 (spec/architecture.md 4.1), and neither is anything
that could carry a pickle: object, compound, opaque, variable-length, reference
and string dtypes are refused on write and on read (4.1). The refusal is
enforcement, not documentation -- a file produced by some other tool that
smuggles a pickled object into a dataset does not load.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import numpy.typing as npt

from certiqs_key.domain._base import (
    BundleValidationError,
    UnsupportedArrayEncodingError,
)
from certiqs_key.domain.arrays import (
    ArrayDescriptor,
    ArrayPayload,
    DenseArray,
    Dtype,
    SparseCSCArray,
    Storage,
)

_VALUE_DATASETS = {Dtype.FLOAT64: ("data",), Dtype.COMPLEX128: ("real", "imag")}
_CSC_DATASETS = ("indices", "indptr", "shape")

#: NumPy dtype kinds a bundle may hold *anywhere*. This is the pickle ban and
#: nothing more: everything else -- ``O`` (object), ``V`` (void/opaque, the
#: shape a pickled blob takes in HDF5), ``U``/``S`` (text), ``M``/``m`` (times)
#: -- is refused. It covers the value payloads (``data``, and the ``real`` and
#: ``imag`` halves of a complex array), where ``f`` and ``c`` are legitimate.
_ALLOWED_KINDS = frozenset("fciu")

#: Dtype kinds the CSC *index* arrays may have -- ``indices`` and ``indptr``
#: only, never the value payloads. Narrower than ``_ALLOWED_KINDS`` on purpose:
#: a float index array would be truncated by the cast to ``int64`` on its way
#: to disk, so ``1.7`` would come back as ``1`` with nothing said.
_INDEX_KINDS = frozenset("iu")


def _check_dtype(dtype: np.dtype[Any], where: str) -> None:
    """Raise unless a NumPy dtype is a plain numeric one this format allows."""
    if dtype.names is not None:
        raise UnsupportedArrayEncodingError(
            f"{where}: compound dtype {dtype!r} is forbidden; a bundle holds "
            "plain numeric datasets only (spec/architecture.md 4.1)"
        )
    if dtype.kind not in _ALLOWED_KINDS:
        raise UnsupportedArrayEncodingError(
            f"{where}: dtype {dtype!r} (kind {dtype.kind!r}) is forbidden; "
            "object arrays and pickle never enter a bundle "
            "(spec/architecture.md 4.1)"
        )


def _check_index_dtype(dtype: np.dtype[Any], where: str) -> None:
    """Raise unless a CSC index array is stored in an integer dtype.

    Applies to ``indices`` and ``indptr`` only. They are cast to ``int64`` on
    the way to disk, so a float or complex index array would be truncated
    rather than refused -- a silent repair in a format that has none.
    """
    _check_dtype(dtype, where)
    if dtype.kind not in _INDEX_KINDS:
        raise UnsupportedArrayEncodingError(
            f"{where}: dtype {dtype!r} (kind {dtype.kind!r}) is not an integer "
            "dtype; CSC index arrays are never truncated into one"
        )


def _read_dataset(
    group: Any, name: str, expected_kinds: str, where: str
) -> npt.NDArray[Any]:
    """Read one dataset, refusing every encoding that could carry a pickle."""
    if name not in group:
        raise BundleValidationError(f"{where}: dataset {name!r} is missing")
    dataset = group[name]
    if not isinstance(dataset, h5py.Dataset):
        raise BundleValidationError(f"{where}: {name!r} is a group, not a dataset")
    dtype = dataset.dtype
    if (
        h5py.check_vlen_dtype(dtype) is not None
        or h5py.check_string_dtype(dtype) is not None
        or h5py.check_opaque_dtype(dtype)
        or h5py.check_dtype(ref=dtype) is not None
    ):
        raise UnsupportedArrayEncodingError(
            f"{where}: dataset {name!r} uses HDF5 dtype {dtype!r}, which can "
            "carry a pickled object; a bundle holds plain numeric datasets "
            "only (spec/architecture.md 4.1)"
        )
    _check_dtype(dtype, f"{where}: dataset {name!r}")
    if dtype.kind not in expected_kinds:
        raise BundleValidationError(
            f"{where}: dataset {name!r} has dtype {dtype!r}, expected one of "
            f"kinds {sorted(expected_kinds)}"
        )
    values: npt.NDArray[Any] = np.asarray(dataset[()])
    return values


def _check_group_members(group: Any, expected: tuple[str, ...], where: str) -> None:
    """Raise if a group holds anything other than the datasets expected."""
    actual = tuple(group.keys())
    unexpected = sorted(set(actual) - set(expected))
    if unexpected:
        raise BundleValidationError(
            f"{where}: unexpected datasets {unexpected}; the group holds "
            f"exactly {sorted(expected)}"
        )


def write_arrays(
    path: Path,
    descriptors: Mapping[str, ArrayDescriptor],
    arrays: Mapping[str, ArrayPayload],
) -> None:
    """Write every array to ``path``, in the layout its descriptor declares."""
    with h5py.File(path, "w") as handle:
        for dataset_path, descriptor in descriptors.items():
            payload = arrays[dataset_path]
            group = handle.create_group(dataset_path)
            if isinstance(payload, DenseArray):
                _write_values(group, descriptor, payload.values, dataset_path)
                continue
            _write_values(group, descriptor, payload.data, dataset_path)
            _check_index_dtype(payload.indices.dtype, f"{dataset_path}: indices")
            _check_index_dtype(payload.indptr.dtype, f"{dataset_path}: indptr")
            group.create_dataset("indices", data=payload.indices.astype(np.int64))
            group.create_dataset("indptr", data=payload.indptr.astype(np.int64))
            group.create_dataset(
                "shape", data=np.asarray(payload.shape, dtype=np.int64)
            )


def _write_values(
    group: Any, descriptor: ArrayDescriptor, values: npt.NDArray[Any], where: str
) -> None:
    """Write the value datasets, splitting a complex array into real and imag."""
    _check_dtype(values.dtype, where)
    if descriptor.dtype is Dtype.COMPLEX128:
        _require_declared_dtype(values, np.complex128, descriptor, where)
        group.create_dataset("real", data=np.ascontiguousarray(values.real))
        group.create_dataset("imag", data=np.ascontiguousarray(values.imag))
        return
    if np.iscomplexobj(values):
        raise UnsupportedArrayEncodingError(
            f"{where}: dtype is declared 'float64' but the array is complex; a "
            "complex array is stored as separate 'real' and 'imag' datasets "
            "and must declare dtype 'complex128'"
        )
    _require_declared_dtype(values, np.float64, descriptor, where)
    group.create_dataset("data", data=np.ascontiguousarray(values))


def _require_declared_dtype(
    values: npt.NDArray[Any],
    expected: type[np.floating[Any] | np.complexfloating[Any, Any]],
    descriptor: ArrayDescriptor,
    where: str,
) -> None:
    """Raise unless an array already has the dtype its descriptor declares.

    The writer converts nothing. ``write_bundle`` reaches here only after
    validation has compared the same two dtypes, but ``write_arrays`` is
    callable on its own, and a cast at this point would turn a mislabelled
    float32 array into a float64 file with nothing said -- the silent repair
    spec/architecture.md 3.6 rules out, arriving through the back door.
    """
    if values.dtype != np.dtype(expected):
        raise BundleValidationError(
            f"{where}: array dtype is {values.dtype}, declared "
            f"{descriptor.dtype.value}; the writer converts nothing"
        )


def read_arrays(
    path: Path, descriptors: Mapping[str, ArrayDescriptor]
) -> dict[str, ArrayPayload]:
    """Read every declared array from ``path`` into memory.

    Raises:
        BundleValidationError: if a declared group is absent or malformed, or
            if ``arrays.h5`` holds a dataset no descriptor claims.
        UnsupportedArrayEncodingError: if a dataset uses a forbidden encoding.
    """
    arrays: dict[str, ArrayPayload] = {}
    with h5py.File(path, "r") as handle:
        _check_no_unreferenced_datasets(handle, descriptors)
        for dataset_path, descriptor in descriptors.items():
            if dataset_path not in handle:
                raise BundleValidationError(
                    f"arrays.h5: group {dataset_path!r} is missing"
                )
            group = handle[dataset_path]
            if not isinstance(group, h5py.Group):
                raise BundleValidationError(
                    f"arrays.h5: {dataset_path!r} is a dataset, not a group; "
                    "every array is a group of plain numeric datasets"
                )
            arrays[dataset_path] = _read_group(group, descriptor, dataset_path)
    return arrays


def _check_no_unreferenced_datasets(
    handle: Any, descriptors: Mapping[str, ArrayDescriptor]
) -> None:
    """Raise if the file holds a dataset no descriptor claims."""
    declared = set(descriptors)
    seen: list[str] = []

    def visit(name: str, obj: Any) -> None:
        if isinstance(obj, h5py.Dataset):
            seen.append("/" + name)

    handle.visititems(visit)
    stray = sorted(
        path
        for path in seen
        if not any(path.startswith(root + "/") for root in declared)
    )
    if stray:
        raise BundleValidationError(
            f"arrays.h5 holds datasets no descriptor claims: {stray}; an "
            "unreferenced array has no declared meaning"
        )


def _require_float64(values: npt.NDArray[Any], name: str, where: str) -> None:
    """Raise unless a value dataset is stored as plain float64.

    Real and imaginary parts are always float64 on disk: a bundle stores the
    numbers it declares, and a narrower on-disk type would be a silent
    conversion rather than a round trip.
    """
    if values.dtype != np.float64:
        raise BundleValidationError(
            f"{where}: dataset {name!r} has dtype {values.dtype}, expected float64"
        )


def _read_group(group: Any, descriptor: ArrayDescriptor, where: str) -> ArrayPayload:
    """Read one array group in the layout its descriptor declares."""
    expected = _VALUE_DATASETS[descriptor.dtype]
    if descriptor.storage is Storage.SPARSE_CSC:
        expected = expected + _CSC_DATASETS
    _check_group_members(group, expected, where)

    if descriptor.dtype is Dtype.COMPLEX128:
        real = _read_dataset(group, "real", "f", where)
        imag = _read_dataset(group, "imag", "f", where)
        _require_float64(real, "real", where)
        _require_float64(imag, "imag", where)
        if real.shape != imag.shape:
            raise BundleValidationError(
                f"{where}: 'real' has shape {list(real.shape)} and 'imag' "
                f"{list(imag.shape)}"
            )
        values: npt.NDArray[Any] = real.astype(np.complex128)
        values += 1j * imag
    else:
        values = _read_dataset(group, "data", "f", where)
        _require_float64(values, "data", where)

    if descriptor.storage is Storage.DENSE:
        return DenseArray(values=values)

    indices = _read_dataset(group, "indices", "iu", where)
    indptr = _read_dataset(group, "indptr", "iu", where)
    shape = _read_dataset(group, "shape", "iu", where)
    if shape.shape != (2,):
        raise BundleValidationError(
            f"{where}: 'shape' holds {shape.size} entries, expected 2"
        )
    if values.ndim != 1 or indices.ndim != 1 or indptr.ndim != 1:
        raise BundleValidationError(
            f"{where}: CSC value, 'indices' and 'indptr' datasets are 1-D"
        )
    return SparseCSCArray(
        data=values,
        indices=indices.astype(np.int64),
        indptr=indptr.astype(np.int64),
        shape=(int(shape[0]), int(shape[1])),
    )
