"""Array descriptors and the in-memory numerical payload of a bundle.

A bundle splits in two (spec/architecture.md 4.1): ``manifest.json``
carries every scalar, alphabet, function table and array *descriptor*, and
``arrays.h5`` carries nothing but numbers. A descriptor is therefore the only
place where an array's meaning is written down, and 4.1 fixes what it must
say: ``dtype``, ``shape``, ``basis``, ``subsystem_order``, ``storage`` and
``semantic_role``.

Three encoding rules are mandatory and are enforced, not merely documented:

* complex values are stored as separate ``real`` and ``imag`` datasets -- a
  NumPy complex dtype is never written to HDF5 directly (4.1);
* sparse arrays are canonical CSC with ``data``, ``indices``, ``indptr``,
  ``shape`` and a **declared** ``index_base`` (4.1);
* object arrays and pickle are forbidden (4.1), and so are the HDF5 dtypes
  that carry them.

The payload is solver-neutral. It holds matrices, tables and scalars, never a
callable, a solver handle or a backend-library object -- the ``meat-core``
contract 0.4.0 Section 2.3 states the same rule from the other side, and names
``gradient_oracle`` as an internal/test API that is never serialized.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Any, Literal

import numpy as np
import numpy.typing as npt
from pydantic import Field, field_validator, model_validator

from certiqs_key.domain._base import StrictModel
from certiqs_key.domain.identifiers import is_dataset_path, is_identifier

# THE BLOCK KIND IS ONE ENUM, AND IT IS ``blocks``'s. The WIRE spelling of
# spec/architecture.md 4.1 and the IN-MEMORY spelling of 2.9 are the same three
# members.
#
# The run tier is where the two meet: ``runs/wire.py`` writes the sector block
# kind of a compiled declaration into the manifest and ``meat_core`` reads it
# back. One enum needs no named conversion and no site that calls it, and it
# makes a comparison by ``.value`` unnecessary. It is re-exported here under
# its own name so that ``certiqs_key.domain.arrays.BlockKind`` says the same
# thing.
from certiqs_key.foundations.blocks import BlockKind


class Dtype(StrEnum):
    """The element types a bundle may store."""

    FLOAT64 = "float64"
    COMPLEX128 = "complex128"


class Storage(StrEnum):
    """The storage conventions a bundle may use (spec/architecture.md 4.1)."""

    DENSE = "dense"
    SPARSE_CSC = "sparse_csc"


class SemanticRole(StrEnum):
    """What an array *is* in the declaration it belongs to.

    The role is what makes an index reconstructable
    (spec/architecture.md 4.3): it says which key of the ``meat-core``
    Section 2.1 inputs table an array
    realises, so a reader never has to infer meaning from a dataset path.
    """

    ALICE_MARGINAL = "alice_marginal"
    ALICE_POVM_ELEMENT = "alice_povm_element"
    BOB_POVM_ELEMENT = "bob_povm_element"
    CONSTRAINT_OPERATOR = "constraint_operator"
    CONSTRAINT_BOUND = "constraint_bound"
    ACCEPTANCE_SET_DATUM = "acceptance_set_datum"


def _check_permutation(
    permutation: tuple[int, ...] | None, length: int, name: str
) -> None:
    """Raise unless ``permutation`` is absent or a permutation of a range."""
    if permutation is None:
        return
    if sorted(permutation) != list(range(length)):
        raise ValueError(
            f"{name} {list(permutation)} is not a permutation of "
            f"range({length}); a permutation is explicit or absent, never partial"
        )


class ArrayDescriptor(StrictModel):
    """Everything ``manifest.json`` says about one array in ``arrays.h5``."""

    form: Literal["array"]
    dataset: str
    dtype: Dtype
    shape: tuple[Annotated[int, Field(ge=1)], ...] = Field(min_length=1, max_length=2)
    basis: str = Field(min_length=1)
    subsystem_order: tuple[str, ...] = Field(min_length=1)
    storage: Storage
    semantic_role: SemanticRole
    index_base: int | None = None
    basis_permutation: tuple[int, ...] | None = None
    subsystem_permutation: tuple[int, ...] | None = None

    @field_validator("dataset")
    @classmethod
    def _check_dataset(cls, value: str) -> str:
        """Reject a dataset path HDF5 cannot address."""
        if not is_dataset_path(value):
            raise ValueError(
                f"{value!r} is not an absolute HDF5 dataset path "
                "(e.g. '/declaration/alice_marginal')"
            )
        return value

    @field_validator("subsystem_order")
    @classmethod
    def _check_subsystem_order(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Reject a malformed or duplicated subsystem ordering."""
        for name in value:
            if not is_identifier(name):
                raise ValueError(f"subsystem {name!r} is not a stable identifier")
        if len(set(value)) != len(value):
            raise ValueError(f"subsystem_order {list(value)} repeats a subsystem")
        return value

    @model_validator(mode="after")
    def _check_storage_consistency(self) -> ArrayDescriptor:
        """Enforce the declared-index-base and permutation-shape rules."""
        if self.storage is Storage.SPARSE_CSC:
            if self.index_base is None:
                raise ValueError(
                    "storage 'sparse_csc' requires a declared index_base "
                    "(spec/architecture.md 4.1); it is never assumed"
                )
            if self.index_base not in (0, 1):
                raise ValueError(f"index_base must be 0 or 1, got {self.index_base}")
            if len(self.shape) != 2:
                raise ValueError("storage 'sparse_csc' requires a 2-D shape")
        elif self.index_base is not None:
            raise ValueError(
                "index_base is meaningful only for storage 'sparse_csc'; "
                f"storage is {self.storage.value!r}"
            )
        _check_permutation(self.basis_permutation, self.shape[0], "basis_permutation")
        _check_permutation(
            self.subsystem_permutation,
            len(self.subsystem_order),
            "subsystem_permutation",
        )
        return self


class BlockDiagonalOperator(StrictModel):
    """An operator given as one array per block, in a declared block kind.

    THIS IS THE ONLY FORM AN OPERATOR PAYLOAD TAKES. Under spec/architecture.md
    2.9 and 2.8 a producer
    constructs one array per sector, so sector-block-diagonality holds BY
    CONSTRUCTION: nothing verifies that the off-sector entries vanish, because
    nothing can write them. What a consumer compares instead is the SECTOR MAP
    -- the block kind, the block identifiers and their ordering, against its
    own -- and a disagreement is a refusal with a machine-readable reason.

    THERE IS NO FULL-SPACE ESCAPE HATCH. A format that could *only* express the
    blocked form would force a caller holding a non-block-diagonal Bob POVM
    element to discard its off-diagonal part in order to serialize it at all,
    and ``meat-core`` could never detect the violation it is required to
    reject. That argument is correct in its own terms and is overturned by a
    change of premise rather than by a refutation (spec/architecture.md 2.9):
    once the producer emits per sector there is no off-sector part to discard
    and no expressible object for the consumer to catch, and the sector-map comparison
    rejects the case that *can* arise, which is two modules disagreeing about
    what the sectors are. 2.9's consequence travels with the deletion --
    "if a producer is ever allowed to construct an operator ambiently again,
    this decision must be revisited first".

    :class:`ArrayDescriptor` is not deleted with it. It remains the type of
    every payload that is not an operator -- ``alice_marginal``, an
    ``alice_povm`` element, an operator-valued constraint bound, an acceptance
    array -- and of each block below.
    """

    form: Literal["block_diagonal"]
    block_kind: BlockKind
    blocks: dict[str, ArrayDescriptor]
    block_permutation: tuple[int, ...] | None = None

    @model_validator(mode="after")
    def _check_blocks(self) -> BlockDiagonalOperator:
        """Reject empty, misnamed or partially permuted block structures."""
        if not self.blocks:
            raise ValueError("a block-diagonal operator declares no blocks")
        for name in self.blocks:
            if not is_identifier(name):
                raise ValueError(f"block index {name!r} is not a stable identifier")
        _check_permutation(
            self.block_permutation, len(self.blocks), "block_permutation"
        )
        return self


#: An operator payload: one array per sector block, and nothing else.
#:
#: There is no union to stand for (spec/architecture.md 2.9), so the ``form``
#: discriminator has one alternative. The NAME is kept because ``meat-core``
#: reads the bundle through it.
OperatorRef = BlockDiagonalOperator


@dataclass(frozen=True, eq=False)
class DenseArray:
    """A dense array as it is held in memory."""

    values: npt.NDArray[Any]


@dataclass(frozen=True, eq=False)
class SparseCSCArray:
    """A canonical CSC array as it is held in memory.

    ``indices`` and ``indptr`` are held exactly as they appear on disk, in the
    ``index_base`` the descriptor declares; nothing is rebased silently.
    """

    data: npt.NDArray[Any]
    indices: npt.NDArray[np.int64]
    indptr: npt.NDArray[np.int64]
    shape: tuple[int, int]


#: The numerical payload of one entry of ``arrays.h5``.
ArrayPayload = DenseArray | SparseCSCArray


def dense_from_csc(payload: SparseCSCArray, index_base: int) -> npt.NDArray[Any]:
    """Expand a CSC payload into a dense array, given its declared index base.

    A pure format conversion: it moves numbers from one layout to another and
    makes no statement about them.
    """
    rows, cols = payload.shape
    out: npt.NDArray[Any] = np.zeros((rows, cols), dtype=payload.data.dtype)
    indptr = payload.indptr - index_base
    indices = payload.indices - index_base
    for column in range(cols):
        start, stop = int(indptr[column]), int(indptr[column + 1])
        out[indices[start:stop], column] = payload.data[start:stop]
    return out
