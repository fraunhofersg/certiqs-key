"""Every hard error the format defines, exercised once.

spec/architecture.md 3.6: "A failure is a hard error, never a warning and never
a repair." These tests are that sentence, made executable.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pytest
from bundle_format_fixtures import (
    ALICE_MARGINAL,
    ALICE_POVM,
    BOB_V0_BLOCKS,
    BOB_V1,
    minimal_arrays,
    minimal_manifest,
)

from certiqs_key.domain._base import BundleValidationError
from certiqs_key.domain.arrays import ArrayPayload, DenseArray, SparseCSCArray
from certiqs_key.domain.bundle import parse_manifest
from certiqs_key.domain.validation import validate_bundle


def check_rejected(
    mutate_manifest: Callable[[dict[str, Any]], None] | None = None,
    mutate_arrays: Callable[[dict[str, ArrayPayload]], None] | None = None,
    *,
    match: str,
) -> None:
    document = minimal_manifest()
    arrays = minimal_arrays()
    if mutate_manifest is not None:
        mutate_manifest(document)
    if mutate_arrays is not None:
        mutate_arrays(arrays)
    with pytest.raises(BundleValidationError, match=match):
        validate_bundle(parse_manifest(document), arrays)


def test_the_unmutated_minimal_bundle_validates():
    validate_bundle(parse_manifest(minimal_manifest()), minimal_arrays())


# No test checks a FULL-SPACE bob_povm element against sum(sector_dims), because
# its subject is unrepresentable (spec/architecture.md 2.9): an operator payload is a
# list of sector blocks, so there is no full-space shape left to disagree with the sum.
# What replaces it is the pair below -- each block against its own sector dimension, and
# the block set against the sector index set -- which is the sector-map comparison
# spec/architecture.md 2.9 puts in place of every zero-verification it removed.


def test_a_sector_block_must_match_its_sector_dimension():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["sector_dims"]["s1"] = 2

    check_rejected(mutate, match="declared dimension 2")


def test_sector_dims_must_be_keyed_by_the_sector_index_set():
    def mutate(document: dict[str, Any]) -> None:
        del document["payload"]["declaration"]["sector_dims"]["s1"]

    check_rejected(mutate, match="sector_dims: not total")


def test_a_matrix_declared_square_must_be_square():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["alice_marginal"]["shape"] = [2, 3]

    check_rejected(mutate, match="is not square")


def test_an_operator_shape_must_match_the_declared_dimension():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["alice_dim"] = 3

    check_rejected(mutate, match="declared dimension 3")


def test_a_function_table_must_be_total():
    def mutate(document: dict[str, Any]) -> None:
        del document["payload"]["declaration"]["announce_alice"]["x1"]

    check_rejected(mutate, match="announce_alice: not total")


def test_a_two_argument_function_table_must_be_total_on_both_arguments():
    def mutate(document: dict[str, Any]) -> None:
        del document["payload"]["declaration"]["accept_statistic"]["cA0"]["cB1"]

    check_rejected(mutate, match="accept_statistic")


def test_a_function_table_value_must_lie_in_its_codomain():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["announce_bob"]["v0"] = "cBX"

    check_rejected(mutate, match="not in the declared codomain")


def test_a_key_map_value_must_lie_in_the_key_alphabet():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["key_map"]["x0"]["v0"] = 5

    check_rejected(mutate, match="key value 5 is outside")


def test_the_key_map_must_be_total_over_bobs_outcomes():
    def mutate(document: dict[str, Any]) -> None:
        del document["payload"]["declaration"]["key_map"]["x1"]["v1"]

    check_rejected(mutate, match="key_map")


def test_a_povm_must_be_indexed_by_its_declared_alphabet():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["alphabets"]["bob_outcome"] = ["v0", "v1", "v2"]

    check_rejected(mutate, match="bob_povm: not total")


def test_an_alphabet_may_not_repeat_an_identifier():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["alphabets"]["acceptance_value"] = ["chat0", "chat0"]

    check_rejected(mutate, match="duplicate identifiers")


def test_an_identifier_must_be_addressable_in_hdf5():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["alphabets"]["acceptance_value"] = ["chat0", "a/b"]

    check_rejected(mutate, match="not a stable identifier")


def test_a_sector_decomposition_must_declare_the_proof_sector_kind():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["bob_povm"]["v0"]["block_kind"] = (
            "numerical_block"
        )

    check_rejected(mutate, match="proof_sector")


def test_blocks_must_be_total_over_the_sector_index_set():
    def mutate(document: dict[str, Any]) -> None:
        operator = document["payload"]["declaration"]["bob_povm"]["v0"]
        del operator["blocks"]["s1"]
        del operator["block_permutation"]

    def drop(arrays: dict[str, ArrayPayload]) -> None:
        del arrays[BOB_V0_BLOCKS["s1"]]

    check_rejected(mutate, drop, match="blocks: not total")


def test_a_semantic_role_must_match_where_the_array_sits():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["alice_marginal"]["semantic_role"] = (
            "constraint_bound"
        )

    check_rejected(mutate, match="semantic_role is 'constraint_bound'")


def test_one_space_carries_one_basis_label():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["alice_povm"]["x1"]["basis"] = "other.A"

    check_rejected(mutate, match="disagrees with")


def test_two_descriptors_may_not_claim_the_same_dataset():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["alice_povm"]["x1"]["dataset"] = ALICE_POVM[
            "x0"
        ]

    check_rejected(mutate, match="is already claimed by")


def test_a_declared_array_must_be_present():
    def drop(arrays: dict[str, ArrayPayload]) -> None:
        del arrays[ALICE_MARGINAL]

    check_rejected(None, drop, match="missing datasets")


def test_an_undeclared_array_is_refused():
    def add(arrays: dict[str, ArrayPayload]) -> None:
        arrays["/smuggled"] = DenseArray(np.zeros((1, 1), dtype=np.float64))

    check_rejected(None, add, match="no descriptor claims")


def test_a_dtype_on_disk_must_match_the_declaration():
    def swap(arrays: dict[str, ArrayPayload]) -> None:
        arrays[ALICE_MARGINAL] = DenseArray(np.eye(2, dtype=np.float64))

    check_rejected(None, swap, match="dtype on disk is float64")


def test_a_shape_on_disk_must_match_the_declaration():
    def swap(arrays: dict[str, ArrayPayload]) -> None:
        arrays[ALICE_MARGINAL] = DenseArray(np.eye(3, dtype=np.complex128))

    check_rejected(None, swap, match="shape on disk is")


def test_a_dense_declaration_refuses_a_sparse_payload():
    def swap(arrays: dict[str, ArrayPayload]) -> None:
        arrays[ALICE_MARGINAL] = SparseCSCArray(
            data=np.array([1.0 + 0j], dtype=np.complex128),
            indices=np.array([0], dtype=np.int64),
            indptr=np.array([0, 1, 1], dtype=np.int64),
            shape=(2, 2),
        )

    check_rejected(None, swap, match="storage is 'dense' but the payload is CSC")


def test_a_sparse_declaration_refuses_a_dense_payload():
    def swap(arrays: dict[str, ArrayPayload]) -> None:
        arrays[BOB_V1] = DenseArray(np.eye(2, dtype=np.complex128))

    check_rejected(None, swap, match="the payload is dense")


def test_csc_row_indices_must_be_in_range():
    def swap(arrays: dict[str, ArrayPayload]) -> None:
        arrays[BOB_V1] = SparseCSCArray(
            data=np.array([1.0 + 0j], dtype=np.complex128),
            indices=np.array([7], dtype=np.int64),
            indptr=np.array([0, 0, 1], dtype=np.int64),
            shape=(2, 2),
        )

    check_rejected(None, swap, match="row index is outside")


def test_csc_indptr_must_have_one_entry_per_column_boundary():
    def swap(arrays: dict[str, ArrayPayload]) -> None:
        arrays[BOB_V1] = SparseCSCArray(
            data=np.array([1.0 + 0j], dtype=np.complex128),
            indices=np.array([1], dtype=np.int64),
            indptr=np.array([0, 1], dtype=np.int64),
            shape=(2, 2),
        )

    check_rejected(None, swap, match="indptr has 2 entries")


def test_csc_indptr_must_start_at_the_declared_index_base():
    def swap(arrays: dict[str, ArrayPayload]) -> None:
        arrays[BOB_V1] = SparseCSCArray(
            data=np.array([1.0 + 0j], dtype=np.complex128),
            indices=np.array([1], dtype=np.int64),
            indptr=np.array([1, 1, 2], dtype=np.int64),
            shape=(2, 2),
        )

    check_rejected(None, swap, match="expected the declared index_base 0")


def test_csc_columns_must_be_sorted_and_duplicate_free():
    def swap(arrays: dict[str, ArrayPayload]) -> None:
        arrays[BOB_V1] = SparseCSCArray(
            data=np.array([1.0 + 0j, 2.0 + 0j], dtype=np.complex128),
            indices=np.array([1, 0], dtype=np.int64),
            indptr=np.array([0, 0, 2], dtype=np.int64),
            shape=(2, 2),
        )

    check_rejected(None, swap, match="not strictly")


def test_csc_indices_and_data_must_have_the_same_length():
    def swap(arrays: dict[str, ArrayPayload]) -> None:
        arrays[BOB_V1] = SparseCSCArray(
            data=np.array([1.0 + 0j, 2.0 + 0j], dtype=np.complex128),
            indices=np.array([1], dtype=np.int64),
            indptr=np.array([0, 0, 2], dtype=np.int64),
            shape=(2, 2),
        )

    check_rejected(None, swap, match="indices has 1 entries")


def test_an_empty_attack_set_license_is_refused():
    """An attestation that names no supplier certificate names nothing."""

    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["attack_set_license"] = {}

    check_rejected(mutate, match="attack_set_license")


def test_an_acceptance_set_array_must_carry_the_acceptance_role():
    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["acceptance_set"]["arrays"] = {
            "normals": document["payload"]["declaration"]["alice_marginal"]
        }

    check_rejected(mutate, match="acceptance_set")


def test_a_dataset_path_may_not_be_nested_inside_another():
    """Regression: ancestor collected first."""

    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["alice_povm"]["x0"]["dataset"] = (
            f"{ALICE_MARGINAL}/extra"
        )

    check_rejected(mutate, match="is nested inside")


def test_nested_dataset_paths_are_refused_in_either_order():
    """Regression: descendant collected first.

    collect_descriptors visits alice_marginal before alice_povm, so putting the
    ancestor second is the order that would escape as a raw h5py error
    instead of a BundleValidationError.
    """

    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["alice_marginal"]["dataset"] = (
            f"{ALICE_POVM['x0']}/child"
        )

    check_rejected(mutate, match="is nested inside")


def test_a_deeply_nested_dataset_path_is_refused():
    """Regression: nesting is detected at any depth, not just one."""

    def mutate(document: dict[str, Any]) -> None:
        document["payload"]["declaration"]["alice_povm"]["x0"]["dataset"] = (
            f"{ALICE_MARGINAL}/a/b/c"
        )

    check_rejected(mutate, match="is nested inside")


def test_a_sibling_sorting_between_a_path_and_its_child_does_not_hide_nesting():
    """Regression: '+', '-' and '.' sort before '/' in a path.

    A neighbour-comparison over sorted paths would miss this pair; walking each
    path's own ancestors does not.
    """

    def mutate(document: dict[str, Any]) -> None:
        declaration = document["payload"]["declaration"]
        declaration["alice_povm"]["x0"]["dataset"] = f"{ALICE_MARGINAL}/child"
        declaration["alice_povm"]["x1"]["dataset"] = f"{ALICE_MARGINAL}+sibling"

    check_rejected(mutate, match="is nested inside")


@pytest.mark.parametrize("component", ["indices", "indptr"])
def test_csc_index_arrays_must_be_integers(component: str):
    """Regression: a float index would be truncated, not refused."""

    def swap(arrays: dict[str, ArrayPayload]) -> None:
        parts = {
            "data": np.array([1.0 + 0j], dtype=np.complex128),
            "indices": np.array([1], dtype=np.int64),
            "indptr": np.array([0, 0, 1], dtype=np.int64),
        }
        parts[component] = parts[component].astype(np.float64)
        arrays[BOB_V1] = SparseCSCArray(shape=(2, 2), **parts)

    check_rejected(None, swap, match="expected an integer dtype")


def test_a_truncating_float_index_does_not_round_trip_silently():
    """Regression: 1.7 must not come back as 1."""

    def swap(arrays: dict[str, ArrayPayload]) -> None:
        arrays[BOB_V1] = SparseCSCArray(
            data=np.array([1.0 + 0j], dtype=np.complex128),
            indices=np.array([1.7], dtype=np.float64),
            indptr=np.array([0, 0, 1], dtype=np.int64),
            shape=(2, 2),
        )

    check_rejected(None, swap, match="expected an integer dtype")


@pytest.mark.parametrize("component", ["data", "indices", "indptr"])
def test_csc_component_arrays_must_be_one_dimensional(component: str):
    """Regression: the reader required 1-D and the writer did not."""

    def swap(arrays: dict[str, ArrayPayload]) -> None:
        parts = {
            "data": np.array([1.0 + 0j], dtype=np.complex128),
            "indices": np.array([1], dtype=np.int64),
            "indptr": np.array([0, 0, 1], dtype=np.int64),
        }
        parts[component] = parts[component].reshape(1, -1)
        arrays[BOB_V1] = SparseCSCArray(shape=(2, 2), **parts)

    check_rejected(None, swap, match="expected 1-D")
