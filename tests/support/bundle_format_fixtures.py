"""A hand-authored minimal operator bundle, used across the unit tests.

Two-dimensional Alice, two proof sectors of dimensions two and one, so that
``sum(sector_dims) == d_Q == 3``. It exercises all four array encodings the
format has to carry: dense real, dense complex, sparse CSC, and a
block-diagonal operator given one array per proof sector.

STAMPED 0.3.0, AND EVERY OPERATOR IS BLOCKED. There is no
other kind of bundle to fixture: an operator payload is a list of sector blocks
(spec/architecture.md 2.9) and 0.3.0 is the only version a reader accepts.
``v1``'s ``s0`` block is a sparse CSC array of 2x2 shape -- which is why ``s0``
has dimension two -- so that the dozen encoding tests addressing
:data:`BOB_V1` address the same array in the same layout.

It is a *format* fixture. Nothing here claims the numbers form a valid
security-proof input -- that judgement belongs to ``meat-core``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from certiqs_key.domain.arrays import ArrayPayload, DenseArray, SparseCSCArray

#: The proof sectors and their dimensions. ``s0`` is two-dimensional so that
#: the fixture carries a 2x2 sparse CSC array inside an operator block.
SECTOR_DIMS = {"s0": 2, "s1": 1}

ALICE_MARGINAL = "/declaration/alice_marginal"
ALICE_POVM = {"x0": "/declaration/alice_povm/x0", "x1": "/declaration/alice_povm/x1"}
BOB_V0_BLOCKS = {
    "s0": "/declaration/bob_povm/v0/s0",
    "s1": "/declaration/bob_povm/v0/s1",
}
BOB_V1_BLOCKS = {
    "s0": "/declaration/bob_povm/v1/s0",
    "s1": "/declaration/bob_povm/v1/s1",
}
#: The sparse CSC 2x2 array, now ``v1``'s ``s0`` block rather than a full-space
#: ``v1``. The name is kept because the encoding tests address it by name.
BOB_V1 = BOB_V1_BLOCKS["s0"]


def array_descriptor(
    dataset: str,
    *,
    dtype: str,
    shape: tuple[int, ...],
    basis: str,
    subsystem_order: tuple[str, ...],
    storage: str,
    semantic_role: str,
    **extra: Any,
) -> dict[str, Any]:
    """Build one array descriptor as it appears in ``manifest.json``."""
    descriptor: dict[str, Any] = {
        "form": "array",
        "dataset": dataset,
        "dtype": dtype,
        "shape": list(shape),
        "basis": basis,
        "subsystem_order": list(subsystem_order),
        "storage": storage,
        "semantic_role": semantic_role,
    }
    descriptor.update(extra)
    return descriptor


def minimal_manifest() -> dict[str, Any]:
    """Return the minimal bundle's manifest as a plain JSON document."""
    return {
        "kind": "operator-bundle",
        "schema_version": "0.3.0",
        "mathematical_spec_version": "meat-core@0.5.0",
        "created_by": "tests.support.bundle_format_fixtures.minimal_manifest",
        "implementation_version": "0.1.0.dev0",
        "assumptions": {
            "test_statistics_model": "output_state",
            "round_homogeneity": True,
        },
        "warnings": [],
        "payload": {
            "alphabets": {
                "alice_outcome": ["x0", "x1"],
                "bob_outcome": ["v0", "v1"],
                "alice_announcement": ["cA0"],
                "bob_announcement": ["cB0", "cB1"],
                "acceptance_value": ["chat0", "chat1"],
                "key_value_count": 2,
            },
            "declaration": {
                "alice_dim": 2,
                "alice_marginal": array_descriptor(
                    ALICE_MARGINAL,
                    dtype="complex128",
                    shape=(2, 2),
                    basis="computational.A",
                    subsystem_order=("A",),
                    storage="dense",
                    semantic_role="alice_marginal",
                ),
                "sector_index_set": ["s0", "s1"],
                "sector_dims": dict(SECTOR_DIMS),
                # THE THIRD COMPONENT OF THE ONE SECTOR MAP, required by the
                # manifest. Every operator on this
                # wire is an emitted one, and the shared format admits exactly
                # one kind on such an operator (spec/architecture.md 2.3).
                "sector_block_kind": "proof_sector",
                "alice_povm": {
                    outcome: array_descriptor(
                        path,
                        dtype="complex128",
                        shape=(2, 2),
                        basis="computational.A",
                        subsystem_order=("A",),
                        storage="dense",
                        semantic_role="alice_povm_element",
                    )
                    for outcome, path in ALICE_POVM.items()
                },
                "bob_povm": {
                    "v0": {
                        "form": "block_diagonal",
                        "block_kind": "proof_sector",
                        "blocks": {
                            sector: array_descriptor(
                                path,
                                dtype="float64",
                                shape=(SECTOR_DIMS[sector], SECTOR_DIMS[sector]),
                                basis=f"computational.Q.{sector}",
                                subsystem_order=("Q",),
                                storage="dense",
                                semantic_role="bob_povm_element",
                            )
                            for sector, path in BOB_V0_BLOCKS.items()
                        },
                        "block_permutation": [0, 1],
                    },
                    "v1": {
                        "form": "block_diagonal",
                        "block_kind": "proof_sector",
                        "blocks": {
                            "s0": array_descriptor(
                                BOB_V1_BLOCKS["s0"],
                                dtype="complex128",
                                shape=(2, 2),
                                basis="computational.Q.s0",
                                subsystem_order=("Q",),
                                storage="sparse_csc",
                                semantic_role="bob_povm_element",
                                index_base=0,
                            ),
                            "s1": array_descriptor(
                                BOB_V1_BLOCKS["s1"],
                                dtype="float64",
                                shape=(1, 1),
                                basis="computational.Q.s1",
                                subsystem_order=("Q",),
                                storage="dense",
                                semantic_role="bob_povm_element",
                            ),
                        },
                        "block_permutation": [0, 1],
                    },
                },
                "announce_alice": {"x0": "cA0", "x1": "cA0"},
                "announce_bob": {"v0": "cB0", "v1": "cB1"},
                "accept_statistic": {"cA0": {"cB0": "chat0", "cB1": "chat1"}},
                "key_map": {
                    "x0": {"v0": 0, "v1": None},
                    "x1": {"v0": 1, "v1": None},
                },
                "key_holder": "A",
                "constraint_list": [],
                "attack_set_license": None,
                "acceptance_set": {
                    "geometry": "singleton",
                    "data": {"frequencies": [0.5, 0.5]},
                    "arrays": {},
                },
                "rounds": 1000000,
            },
            "parameters": {
                "alpha": 1.05,
                "eps_pa": 1e-10,
                "eps_ev": 1e-10,
                "lambda_ec": 20000,
            },
        },
    }


def minimal_arrays() -> dict[str, ArrayPayload]:
    """Return the numerical payload matching :func:`minimal_manifest`."""
    return {
        ALICE_MARGINAL: DenseArray(np.eye(2, dtype=np.complex128) / 2.0),
        ALICE_POVM["x0"]: DenseArray(
            np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
        ),
        ALICE_POVM["x1"]: DenseArray(
            np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
        ),
        BOB_V0_BLOCKS["s0"]: DenseArray(
            np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.float64)
        ),
        BOB_V0_BLOCKS["s1"]: DenseArray(np.array([[0.0]], dtype=np.float64)),
        # v1's s0 block: the entry (1, 1), so that v0 + v1 is the identity on
        # s0. Column 0 is empty and column 1 holds row 1.
        BOB_V1_BLOCKS["s0"]: SparseCSCArray(
            data=np.array([1.0 + 0.0j], dtype=np.complex128),
            indices=np.array([1], dtype=np.int64),
            indptr=np.array([0, 0, 1], dtype=np.int64),
            shape=(2, 2),
        ),
        BOB_V1_BLOCKS["s1"]: DenseArray(np.array([[1.0]], dtype=np.float64)),
    }
