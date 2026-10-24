"""Serialize the 0.3.0 source-mode toys as operator bundles.

``tests/oracles/dummy_bundles.py`` is FROZEN and, at the time it was frozen,
the operator-bundle manifest had no spelling for an absent marginal, a
source-replacement licence, a non-default party partition or a scalar
constraint right-hand side. It therefore *refuses* those declarations
with a named ``NotImplementedError`` rather than coercing them -- silently
coercing ``alice_marginal = none`` into a matrix would serialize a TRUSTED
declaration for an UNTRUSTED one, which is the unsafe direction (registry entry
``O-UNTRUSTED-CONSERVATIVE``).

This module is the other half, written after the format was extended, and it is
deliberately **not** in the frozen tree: it is solver-side work under the run's
own write set, and the expected values it is checked against were committed
before it existed.

It builds the same manifest the frozen builder does, plus the three 0.3.0 slots:

* ``alice_marginal`` is ``null`` when the toy's marginal slot holds ``none``
  (contract Definition ``def:declaration``; Remark ``rem:modes-da1``);
* ``source_replacement_license`` is carried when the toy declares one;
* ``party_partition`` is carried when the toy declares one, with its readout
  maps re-keyed into the nested ``{x: {v: o}}`` form the wire format uses for
  every binary table;
* a scalar ``Theta_k = c_k`` is written as a JSON number, not as a ``1 x 1``
  array. That is the whole content of Definition ``def:homog`` (b) at the wire
  level, and writing it as an array would be the operator reading Remark
  ``rem:homog`` (a) rejects.

Every trusted-mode toy in ``ALL_TOYS`` serializes identically through either
builder, which ``tests/unit/test_source_mode_bundles.py`` asserts rather than
assumes.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from toy_declarations import ToyDeclaration

from certiqs_key.domain.arrays import ArrayPayload, DenseArray
from certiqs_key.domain.bundle import OperatorBundle, parse_manifest

#: contract.tex Section 2.5: ``artifact_bindings.mathematical_spec_version`` is
#: ``<module-id>@<contract_version>`` of the ACCEPTED contract.
SPEC_VERSION = "meat-core@1.28.0"

#: The same key-length parameter block the frozen builder uses, so that a value
#: computed here is comparable with one computed there.
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


def _party_partition(toy: ToyDeclaration) -> dict[str, Any] | None:
    """Return the declared party partition in its wire form, or ``None``.

    ``None`` spells the DEFAULT partition of contract Definition
    ``def:declaration``, which "reproduces versions 0.2.x of this contract
    verbatim" -- so an absent record is not a missing field.
    """
    partition = toy.party_partition
    if partition is None:
        return None
    nested_alice: dict[str, dict[str, str]] = {}
    for (x, v), value in partition.readout_alice.items():
        nested_alice.setdefault(x, {})[v] = value
    nested_bob: dict[str, dict[str, str]] = {}
    for (x, v), value in partition.readout_bob.items():
        nested_bob.setdefault(x, {})[v] = value
    return {
        "readout_alice": nested_alice,
        "readout_bob": nested_bob,
        "alphabet_alice": list(partition.alphabet_alice),
        "alphabet_bob": list(partition.alphabet_bob),
        "party_of_alice_system": partition.party_of_alice_system,
        "party_of_sector_factors": {
            sector: list(labels)
            for sector, labels in partition.party_of_sector_factors.items()
        },
    }


def _acceptance_set(toy: ToyDeclaration) -> dict[str, Any]:
    """Return the declared acceptance set in its wire form.

    The sub-keys of the ``data`` block are the ones the accepted
    ``statistics-acceptance`` contract 0.1.2 uses for the same objects --
    ``frequencies`` for a singleton, ``m_row``, ``B``, ``b`` and the optional
    ``box_bounds`` for a polytope -- which is the serialization decision
    ``certiqs_key.meat_core.declaration.bundle`` documents and reads. No schema version
    moved to carry them: the operator-bundle format already types ``data`` as a
    free-form object, deliberately, because the taxonomy is not its to
    enumerate.
    """
    declared = dict(toy.acceptance_set)
    geometry = str(declared["geometry"])
    if geometry == "singleton":
        return {
            "geometry": geometry,
            "data": {"frequencies": list(declared["frequencies"])},
            "arrays": {},
        }
    data: dict[str, Any] = {
        "m_row": int(declared["m_row"]),
        "B": [list(row) for row in declared["B"]],
        "b": list(declared["b"]),
    }
    bounds = declared.get("box_bounds")
    if bounds is not None:
        data["box_bounds"] = [list(bounds[0]), list(bounds[1])]
    return {"geometry": geometry, "data": data, "arrays": {}}


def bundle_documents(
    toy: ToyDeclaration, *, rounds: int = 1_000_000
) -> tuple[dict[str, Any], dict[str, ArrayPayload]]:
    """Return ``(manifest, arrays)`` for ``toy`` in the operator-bundle format."""
    arrays: dict[str, ArrayPayload] = {}

    marginal: dict[str, Any] | None = None
    if toy.alice_marginal is not None:
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
        bound: Any
        # THE BOUND AND ITS TAG ARE DECIDED IN ONE BRANCH, because they are one
        # datum. This module is the PRODUCER of these bundles, and a producer
        # reads the tag off the object it is writing -- which is what
        # ``protocol/spec.py``'s ``ConstraintRow.tag`` does, "READ OFF THE
        # DATUM". The rule that forbids reading a tag off ``bound`` binds the
        # CONSUMER, which was handed the entry and cannot know what its
        # producer meant (``domain/manifest.py``; ``meat-core`` Section 2.1).
        #
        # Writing a constant ``general`` here, as this builder did, DECLARED
        # THE WRONG FORM for every scalar entry: an untrusted-mode toy carries
        # ``Theta_k = c_k``, which is def:homog (b)'s scalar form, and a
        # `general` tag on it is a declaration the engine must refuse -- "in
        # untrusted-source mode only the scalar form exists".
        if isinstance(constraint.bound, np.ndarray):
            bound_path = f"/declaration/constraint/{index}/bound"
            arrays[bound_path] = DenseArray(np.asarray(constraint.bound, np.float64))
            bound = _dense(
                bound_path,
                constraint.bound,
                basis="computational.A",
                role="constraint_bound",
            )
            # `general`: the bound is the Hermitian Theta_k on A.
            rhs_tag = "general"
        else:
            # Definition def:homog (b): a real number, not a 1 x 1 array.
            bound = float(constraint.bound)
            # `homogeneous`: the bound IS the real scalar c_k.
            rhs_tag = "homogeneous"
        constraints.append(
            {
                "operator": {
                    "form": "block_diagonal",
                    "block_kind": "proof_sector",
                    "blocks": block_descriptors,
                    "block_permutation": list(range(len(toy.sector_index_set))),
                },
                "relation": constraint.relation,
                "bound": bound,
                # The DECLARED FORM of the right-hand side, required by the
                # manifest, decided with the bound above.
                "constraint_rhs_tag": rhs_tag,
            }
        )

    accept_statistic: dict[str, dict[str, str]] = {}
    for (c_a, c_b), chat in toy.accept_statistic.items():
        accept_statistic.setdefault(c_a, {})[c_b] = chat

    key_map: dict[str, dict[str, int | None]] = {}
    for (x, v), value in toy.key_map.items():
        key_map.setdefault(x, {})[v] = value

    declaration: dict[str, Any] = {
        "alice_dim": toy.alice_dim,
        "alice_marginal": marginal,
        "source_replacement_license": toy.source_replacement_license,
        "party_partition": _party_partition(toy),
        "sector_index_set": list(toy.sector_index_set),
        "sector_dims": dict(toy.sector_dims),
        # The third component of the one sector map, required by the manifest.
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
        "acceptance_set": _acceptance_set(toy),
        "rounds": rounds,
    }

    manifest: dict[str, Any] = {
        "kind": "operator-bundle",
        # 0.3.0 is the only accepted version (spec/architecture.md 2.9 §6) and
        # every operator is in the sector-block form it requires.
        "schema_version": "0.3.0",
        "mathematical_spec_version": SPEC_VERSION,
        "created_by": f"tests.support.mode_bundles[{toy.toy_id}]",
        "implementation_version": "0.1.0.dev0",
        "assumptions": {
            # contract.tex Section 2.5, transcribed in interface.yaml. The
            # source mode is NOT among them: it is derived from the marginal
            # slot, and a second key carrying it is forbidden.
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
            "declaration": declaration,
            "parameters": dict(DEFAULT_PARAMETERS),
        },
    }
    return manifest, arrays


def build_bundle(toy: ToyDeclaration, *, rounds: int = 1_000_000) -> OperatorBundle:
    """Return ``toy`` as a parsed, format-validated :class:`OperatorBundle`."""
    manifest, arrays = bundle_documents(toy, rounds=rounds)
    return OperatorBundle(manifest=parse_manifest(manifest), arrays=arrays)
