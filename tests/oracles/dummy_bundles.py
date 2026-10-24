"""Serialize the oracle toy declarations as dummy operator bundles.

The oracle set calls for "hand-authored toy ``ProofInstance``s and dummy
operator bundles small enough to reason about". This module turns the toy
declarations of :mod:`toy_declarations` into real bundles in the versioned
operator-bundle format of spec/architecture.md Section 6.1, using only the
public surface of :mod:`certiqs_key.domain`.

Why it is here and not under ``src/``
-------------------------------------
``MODULES.yaml`` records the dummy bundle as "a non-proof-critical test
fixture, not a module, and not a dependency edge" -- it is what stands in for
``protocol-compiler`` until that module has an accepted contract. The bundles
below are exactly that fixture, and they give the step-3 solver a concrete
input whose answer is already frozen in :mod:`registry`.

What the format does and does not check
---------------------------------------
``certiqs_key.domain`` is not proof-critical and validates a bundle only as
*data*: shapes, dtypes, totality of the function tables, alphabet keying,
``sum(sector_dims) == d_Q``, parameter ranges. Positivity, POVM completeness,
block-diagonality of the Bob POVM, ``tau_A``-homogeneity of the constraint
list and convexity of the acceptance set are ``meat-core``'s own bundle
validation (spec/architecture.md 3.6) and are deliberately absent
there -- see the module docstring of ``certiqs_key.domain.validation``. The toys
here satisfy all of those mathematical conditions by hand; that they do is
recorded in each toy's ``derivation`` and checked in
``test_dummy_bundles.py`` against the registry rather than by the format.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from toy_declarations import ToyDeclaration

from certiqs_key.domain.arrays import ArrayPayload, DenseArray
from certiqs_key.domain.bundle import OperatorBundle, parse_manifest

#: contract.tex Section 2.5: artifact_bindings.mathematical_spec_version is
#: "<module-id>@<contract_version>" of the ACCEPTED contract, and no artifact
#: may claim a draft version.
SPEC_VERSION = "meat-core@1.28.0"

#: A key-length parameter block that is valid for every toy. alpha lies in the
#: (1, 2) domain that req:key-length-alpha-domain confines key lengths to; the
#: budgets are the KL-1 case of the registry.
DEFAULT_PARAMETERS: dict[str, float | int] = {
    "alpha": 1.5,
    "eps_pa": 2.0**-30,
    "eps_ev": 2.0**-30,
    "lambda_ec": 200_000,
}


def _dense(dataset: str, matrix: Any, *, basis: str, role: str) -> dict[str, Any]:
    """Return one dense array descriptor as it appears in ``manifest.json``."""
    array = np.asarray(matrix, dtype=np.float64)
    return {
        "form": "array",
        "dataset": dataset,
        "dtype": "float64",
        "shape": list(array.shape),
        "basis": basis,
        "subsystem_order": ["A"] if basis.startswith("computational.A") else ["Q"],
        "storage": "dense",
        "semantic_role": role,
    }


def bundle_documents(
    toy: ToyDeclaration, *, rounds: int = 1_000_000
) -> tuple[dict[str, Any], dict[str, ArrayPayload]]:
    """Return ``(manifest, arrays)`` for ``toy`` in the operator-bundle format.

    Raises ``NotImplementedError`` for the 0.3.0 declarations that the 0.1.0
    manifest cannot yet express -- an absent marginal, a source-replacement
    licence, a non-default party partition, or a scalar constraint right-hand
    side. Refusing is the fail-closed behaviour: silently coercing
    ``alice_marginal = none`` into a matrix would serialize a TRUSTED-source
    declaration for an UNTRUSTED one, which is the unsafe direction (registry
    entry ``O-UNTRUSTED-CONSERVATIVE``). Extending the manifest and
    ``schemas/proof-instance/operator-bundle.schema.json`` is solver-side work.
    """
    if toy.alice_marginal is None:
        raise NotImplementedError(
            f"{toy.toy_id} is in untrusted-source mode; the 0.1.0 operator-bundle "
            "manifest has no spelling for alice_marginal = none"
        )
    if toy.source_replacement_license is not None:
        raise NotImplementedError(
            f"{toy.toy_id} carries a source_replacement_license, which the 0.1.0 "
            "operator-bundle manifest has no field for"
        )
    if toy.party_partition is not None:
        raise NotImplementedError(
            f"{toy.toy_id} declares a non-default party partition, which the "
            "0.1.0 operator-bundle manifest has no field for"
        )
    for constraint in toy.constraint_list:
        if not isinstance(constraint.bound, np.ndarray):
            raise NotImplementedError(
                f"{toy.toy_id} carries a scalar constraint right-hand side; the "
                "0.1.0 operator-bundle manifest types every bound as an array"
            )

    arrays: dict[str, ArrayPayload] = {}

    marginal_path = "/declaration/alice_marginal"
    arrays[marginal_path] = DenseArray(np.asarray(toy.alice_marginal, np.float64))
    marginal = _dense(
        marginal_path,
        toy.alice_marginal,
        basis="computational.A",
        role="alice_marginal",
    )

    alice_povm: dict[str, Any] = {}
    for outcome, element in toy.alice_povm.items():
        path = f"/declaration/alice_povm/{outcome}"
        arrays[path] = DenseArray(np.asarray(element, np.float64))
        alice_povm[outcome] = _dense(
            path, element, basis="computational.A", role="alice_povm_element"
        )

    bob_povm: dict[str, Any] = {}
    for outcome, blocks in toy.bob_povm.items():
        block_descriptors: dict[str, Any] = {}
        for sector, block in blocks.items():
            path = f"/declaration/bob_povm/{outcome}/{sector}"
            arrays[path] = DenseArray(np.asarray(block, np.float64))
            block_descriptors[sector] = _dense(
                path,
                block,
                basis=f"computational.Q.{sector}",
                role="bob_povm_element",
            )
        bob_povm[outcome] = {
            "form": "block_diagonal",
            "block_kind": "proof_sector",
            "blocks": block_descriptors,
            "block_permutation": list(range(len(toy.sector_index_set))),
        }

    constraints: list[dict[str, Any]] = []
    for index, constraint in enumerate(toy.constraint_list):
        block_descriptors = {}
        for sector, block in constraint.operator_blocks.items():
            path = f"/declaration/constraint/{index}/operator/{sector}"
            arrays[path] = DenseArray(np.asarray(block, np.float64))
            block_descriptors[sector] = _dense(
                path,
                block,
                basis=f"computational.Q.{sector}",
                role="constraint_operator",
            )
        bound_path = f"/declaration/constraint/{index}/bound"
        arrays[bound_path] = DenseArray(np.asarray(constraint.bound, np.float64))
        constraints.append(
            {
                "operator": {
                    "form": "block_diagonal",
                    "block_kind": "proof_sector",
                    "blocks": block_descriptors,
                    "block_permutation": list(range(len(toy.sector_index_set))),
                },
                "relation": constraint.relation,
                "bound": _dense(
                    bound_path,
                    constraint.bound,
                    basis="computational.A",
                    role="constraint_bound",
                ),
                # THE DECLARED FORM, required by the manifest.
                # `general`: the bound above is written as an ARRAY on A, which
                # is Theta_k and not the scalar c_k of the licensed form. The
                # tag is read off what this builder DECLARED and never off the
                # bound's type, which is the rule the required key exists to
                # keep (`protocol-compiler` def:homog).
                "constraint_rhs_tag": "general",
            }
        )

    accept_statistic: dict[str, dict[str, str]] = {}
    for (c_a, c_b), chat in toy.accept_statistic.items():
        accept_statistic.setdefault(c_a, {})[c_b] = chat

    key_map: dict[str, dict[str, int | None]] = {}
    for (x, v), value in toy.key_map.items():
        key_map.setdefault(x, {})[v] = value

    manifest: dict[str, Any] = {
        "kind": "operator-bundle",
        # THE ONE EDIT THIS FROZEN MODULE HAS TAKEN. 0.1.0 is retired
        # (spec/architecture.md 2.9 §6) and unreadable, so the
        # stamp had to move or every consumer of this builder would refuse.
        # NO FROZEN VALUE MOVES WITH IT: every operator here was already in the
        # sector-block form 0.3.0 requires, so the declaration this builder
        # denotes is the one the registry was frozen against, character for
        # character apart from this string.
        "schema_version": "0.3.0",
        "mathematical_spec_version": SPEC_VERSION,
        "created_by": f"tests.oracles.dummy_bundles[{toy.toy_id}]",
        "implementation_version": "0.1.0.dev0",
        "assumptions": {
            # contract.tex Section 2.5, transcribed in interface.yaml.
            "test_statistics_model": "output_state",
            "round_homogeneity": True,
            "log_base": 2,
            "entropy_units": "bits",
            "entropy_variant": "sandwiched-renyi",
            "arrow": "up",
        },
        "warnings": [],
        "payload": {
            "alphabets": {
                "alice_outcome": list(toy.alice_povm),
                "bob_outcome": list(toy.bob_povm),
                "alice_announcement": sorted(set(toy.announce_alice.values())),
                "bob_announcement": sorted(set(toy.announce_bob.values())),
                "acceptance_value": list(toy.acceptance_values),
                "key_value_count": toy.key_value_count,
            },
            "declaration": {
                "alice_dim": toy.alice_dim,
                "alice_marginal": marginal,
                "sector_index_set": list(toy.sector_index_set),
                "sector_dims": dict(toy.sector_dims),
                # THE THIRD COMPONENT OF THE ONE SECTOR MAP, required by the
                # manifest. A toy bundle declares
                # `proof_sector` because its identifiers are the emitted
                # reduction's, which is what every operator on this wire is
                # (`domain/validation.py` admits no other kind on one).
                "sector_block_kind": "proof_sector",
                "alice_povm": alice_povm,
                "bob_povm": bob_povm,
                "announce_alice": dict(toy.announce_alice),
                "announce_bob": dict(toy.announce_bob),
                "accept_statistic": accept_statistic,
                "key_map": key_map,
                "key_holder": toy.key_holder,
                "constraint_list": constraints,
                "attack_set_license": toy.attack_set_license,
                "acceptance_set": {
                    "geometry": str(toy.acceptance_set["geometry"]),
                    "data": {
                        "frequencies": list(toy.acceptance_set["frequencies"]),
                    },
                    "arrays": {},
                },
                "rounds": rounds,
            },
            "parameters": dict(DEFAULT_PARAMETERS),
        },
    }
    return manifest, arrays


def build_bundle(toy: ToyDeclaration, *, rounds: int = 1_000_000) -> OperatorBundle:
    """Return ``toy`` as a parsed, format-validated :class:`OperatorBundle`."""
    manifest, arrays = bundle_documents(toy, rounds=rounds)
    return OperatorBundle(manifest=parse_manifest(manifest), arrays=arrays)
