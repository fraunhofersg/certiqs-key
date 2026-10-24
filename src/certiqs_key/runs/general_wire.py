"""Serialize general declarations without materializing product operators.

Factor order, transcript order and acceptance columns travel unchanged. Only
labels are re-keyed; array entries are never prepared or repaired at this tier.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import product
from typing import Any

import numpy as np

from certiqs_key.domain.arrays import ArrayPayload, DenseArray
from certiqs_key.domain.bundle import OperatorBundle, parse_manifest
from certiqs_key.domain.manifest import SCHEMA_VERSION_FACTORISED, KeyHolder
from certiqs_key.foundations.blocks import PRODUCT_LABEL_SEPARATOR, BlockOperator
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.declaration.general_validation import (
    validate_general_transcript_tables,
)
from certiqs_key.meat_core.declaration.validation import (
    MATHEMATICAL_SPEC_VERSION,
    REQUIRED_ASSUMPTIONS,
)
from certiqs_key.runs.errors import SliceAssemblyError
from certiqs_key.runs.identifiers import sanitize, stable_id_map
from certiqs_key.runs.wire import (
    WireLabels,
    _acceptance_set,
    _as_complex,
    _descriptor,
    _implementation_version,
    _link,
    _pair,
    _reduction_chain,
    _sequence,
)


def _factor_reduction_chain(
    record: Mapping[str, object],
    *,
    scopes: Mapping[str, str],
    letters: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    """Re-key every local factor chain without inventing a product gamma."""
    rows = _sequence(record, "receiver_factor_segments")
    if len(rows) != len(letters):
        raise SliceAssemblyError(
            "the factor reduction-chain record carries one receiver row per "
            f"measured factor: got {len(rows)} for {len(letters)} factors"
        )
    converted = []
    for index, item in enumerate(rows):
        if not isinstance(item, Mapping):
            raise SliceAssemblyError(
                f"receiver factor segment {index} is a record; got {item!r}"
            )
        label = str(item.get("factor_label"))
        if label not in scopes:
            raise SliceAssemblyError(
                f"receiver factor segment {index} names {label!r}, outside "
                f"{list(scopes)}"
            )
        correspondence = []
        for pair in _sequence(item, "outcome_correspondence"):
            physical, emitted = _pair(pair)
            if emitted not in letters[index]:
                raise SliceAssemblyError(
                    f"factor {label!r} maps {physical!r} to {emitted!r}, outside "
                    f"its local alphabet {list(letters[index])}"
                )
            correspondence.append([sanitize(physical), letters[index][emitted]])
        converted.append(
            {
                "factor_label": scopes[label],
                "party": str(item.get("party")),
                "receiver_segment": [
                    _link(link) for link in _sequence(item, "receiver_segment")
                ],
                "outcome_correspondence": correspondence,
            }
        )
    return {
        "source_segment": [_link(link) for link in _sequence(record, "source_segment")],
        "receiver_factor_segments": converted,
    }


def _constraint_rhs(
    rhs: object,
    *,
    alice_labels: Sequence[str],
    alice_dims: Mapping[str, int],
) -> np.ndarray[Any, np.dtype[np.complex128]]:
    """Materialize one exact Alice block list only at the dense wire boundary."""
    if isinstance(rhs, BlockOperator):
        return _as_complex(rhs.dense())
    if not isinstance(rhs, Mapping):
        return _as_complex(rhs)
    total = sum(alice_dims[label] for label in alice_labels)
    dense = np.zeros((total, total), dtype=np.complex128)
    offset = 0
    for label in alice_labels:
        size = alice_dims[label]
        dense[offset : offset + size, offset : offset + size] = _as_complex(rhs[label])
        offset += size
    return dense


def general_bundle_documents(
    declaration: GeneralDeclaration,
    *,
    alice_announcements: Sequence[str],
    bob_announcements: Sequence[str],
    reduction_chain: Mapping[str, object] | None,
    created_by: str,
) -> tuple[dict[str, Any], dict[str, ArrayPayload], WireLabels]:
    """Return manifest, factor arrays and reversible label maps."""
    d = declaration
    validate_general_transcript_tables(d)
    xs = stable_id_map(d.alice_alphabet, "alice_outcome")
    ats = stable_id_map(d.alice.sectors.labels, "alice_sector")
    scopes = stable_id_map(tuple(f.label for f in d.factors), "factor")
    sectors = [stable_id_map(f.sectors.labels, "factor_sector") for f in d.factors]
    letters = [stable_id_map(f.alphabet, "factor_outcome") for f in d.factors]

    def joined(maps: list[Mapping[str, str]]) -> dict[str, str]:
        return {
            PRODUCT_LABEL_SEPARATOR.join(parts): PRODUCT_LABEL_SEPARATOR.join(
                m[p] for m, p in zip(maps, parts, strict=True)
            )
            for parts in product(*(tuple(m) for m in maps))
        }

    vs, ss = joined(letters), joined(sectors)
    chats = stable_id_map(d.acceptance_values, "acceptance_value")
    ids = WireLabels(
        xs,
        vs,
        stable_id_map(alice_announcements, "alice_announcement"),
        stable_id_map(bob_announcements, "bob_announcement"),
        chats,
        ss,
    )
    arrays: dict[str, ArrayPayload] = {}

    def blocks(
        values: Mapping[str, Any],
        names: Mapping[str, str],
        path: str,
        subsystem: str,
        basis: str,
        role: str,
    ) -> dict[str, Any]:
        refs: dict[str, Any] = {}
        for label, identifier in names.items():
            dataset = f"{path}/{identifier}"
            array = _as_complex(values[label])
            arrays[dataset] = DenseArray(array)
            refs[identifier] = _descriptor(
                dataset,
                array,
                basis=f"computational.{basis}.{identifier}",
                subsystem=subsystem,
                role=role,
            )
        return {
            "form": "block_diagonal",
            "block_kind": d.sector_block_kind,
            "blocks": refs,
            "block_permutation": list(range(len(names))),
        }

    partition = d.party_partition
    ras = (
        xs
        if partition is None
        else stable_id_map(partition.alphabet_alice, "readout_alice")
    )
    rbs = (
        vs
        if partition is None
        else stable_id_map(partition.alphabet_bob, "readout_bob")
    )
    message_ids = [stable_id_map(m.alphabet, "message") for m in d.transcript.messages]
    transcript = []
    for index, message in enumerate(d.transcript.messages):
        readouts = ras if message.sender is KeyHolder.ALICE else rbs
        transcript.append(
            {
                "sender": str(message.sender),
                "alphabet": list(message_ids[index].values()),
                "table": [
                    [
                        readouts[r],
                        [message_ids[j][p] for j, p in enumerate(prefix)],
                        message_ids[index][v],
                    ]
                    for r in readouts
                    for prefix in product(
                        *(m.alphabet for m in d.transcript.messages[:index])
                    )
                    for v in (message.table[r, prefix],)
                ],
            }
        )

    def readout_table(
        values: Mapping[tuple[str, str], str], names: Mapping[str, str]
    ) -> dict[str, Any]:
        table: dict[str, Any] = {}
        for (x, v), result in values.items():
            table.setdefault(xs[x], {})[vs[v]] = names[result]
        return table

    partition_wire = (
        None
        if partition is None
        else {
            "readout_alice": readout_table(partition.readout_alice, ras),
            "readout_bob": readout_table(partition.readout_bob, rbs),
            "alphabet_alice": list(ras.values()),
            "alphabet_bob": list(rbs.values()),
            "party_of_alice_system": str(partition.party_of_alice_system),
            "party_of_sector_factors": {
                ss[s]: [str(p) for p in parties]
                for s, parties in partition.party_of_sector_factors.items()
            },
        }
    )
    factorisation = [
        {
            "system": "A",
            "party": str(d.alice.party),
            "sectors": [[ats[t], d.alice.sectors.dims[t]] for t in ats],
        }
    ]
    families = []
    for i, factor in enumerate(d.factors):
        factorisation.append(
            {
                "system": "Q",
                "party": str(factor.party),
                "label": scopes[factor.label],
                "sectors": [
                    [sectors[i][s], factor.sectors.dims[s]] for s in sectors[i]
                ],
            }
        )
        families.append(
            {
                "party": str(factor.party),
                "alphabet": list(letters[i].values()),
                "members": {
                    letters[i][v]: blocks(
                        factor.blocks[v],
                        sectors[i],
                        f"/declaration/factors/{i}/{letters[i][v]}",
                        "Q",
                        f"Q.{i}",
                        "bob_povm_element",
                    )
                    for v in factor.alphabet
                },
            }
        )
    constraints = []
    for i, entry in enumerate(d.constraint_list):
        f_index = next(j for j, f in enumerate(d.factors) if f.label == entry.scope)
        bound: Any = entry.bound
        if isinstance(entry.bound, (Mapping, BlockOperator)):
            array = _constraint_rhs(
                entry.bound,
                alice_labels=tuple(ats),
                alice_dims=d.alice.sectors.dims,
            )
            dataset = f"/declaration/constraints/{i}/bound"
            arrays[dataset] = DenseArray(array)
            bound = _descriptor(
                dataset,
                array,
                basis="computational.A",
                subsystem="A",
                role="constraint_bound",
            )
        constraints.append(
            {
                "scope": scopes[entry.scope],
                "relation": str(entry.relation),
                "constraint_rhs_tag": str(entry.rhs_tag),
                "bound": bound,
                "operator": blocks(
                    entry.operator_blocks,
                    sectors[f_index],
                    f"/declaration/constraints/{i}/operator",
                    "Q",
                    f"Q.{f_index}",
                    "constraint_operator",
                ),
            }
        )
    key_map: dict[str, Any] = {}
    for (x, v), key in d.key_map.items():
        key_map.setdefault(xs[x], {})[vs[v]] = key
    family_key = (
        "alice_ensemble" if str(d.alice_form) == "ensemble" else "alice_povm_blocks"
    )
    wire: dict[str, Any] = {
        "alice_dim": d.alice_dim,
        "alice_form": str(d.alice_form),
        "alice_marginal_blocks": None
        if d.alice_marginal is None
        else blocks(
            d.alice_marginal,
            ats,
            "/declaration/alice_marginal",
            "A",
            "A",
            "alice_marginal",
        ),
        family_key: {
            xs[x]: blocks(
                d.alice_operators[x],
                ats,
                f"/declaration/alice_operators/{xs[x]}",
                "A",
                "A",
                "alice_povm_element",
            )
            for x in xs
        },
        "sector_factorisation": factorisation,
        "bob_povm_factors": families,
        "sector_index_set": list(ss.values()),
        "sector_dims": {ss[s]: dim for s, dim in d.sector_dims.items()},
        "sector_block_kind": d.sector_block_kind,
        "transcript": transcript,
        "announce_alice": {},
        "announce_bob": {},
        "accept_statistic": {},
        "accept_statistic_general": [
            [[message_ids[i][v] for i, v in enumerate(k)], chats[d.accept_statistic[k]]]
            for k in product(*(m.alphabet for m in d.transcript.messages))
        ],
        "key_map": key_map,
        "key_holder": str(d.key_holder),
        "party_partition": partition_wire,
        "constraint_list": constraints,
        "attack_set_license": None
        if d.attack_set_license is None
        else dict(d.attack_set_license),
        # The transmitter's own JSON record, passed through (runs.wire).
        "source_replacement_license": None
        if d.source_replacement_license is None
        else dict(d.source_replacement_license),
        "acceptance_set": _acceptance_set(d),
        "rounds": d.rounds,
    }
    manifest = {
        "kind": "operator-bundle",
        "schema_version": SCHEMA_VERSION_FACTORISED,
        "mathematical_spec_version": MATHEMATICAL_SPEC_VERSION,
        "created_by": created_by,
        "implementation_version": _implementation_version(),
        "assumptions": dict(REQUIRED_ASSUMPTIONS),
        "warnings": [],
        "payload": {
            "alphabets": {
                "alice_outcome": list(xs.values()),
                "bob_outcome": list(vs.values()),
                "alice_announcement": [],
                "bob_announcement": [],
                "acceptance_value": list(chats.values()),
                "key_value_count": d.key_value_count,
            },
            "declaration": wire,
            "reduction_chain": None
            if reduction_chain is None
            else _factor_reduction_chain(
                reduction_chain, scopes=scopes, letters=letters
            )
            if "receiver_factor_segments" in reduction_chain
            else _reduction_chain(reduction_chain, ids),
            "parameters": {
                "alpha": d.parameters.alpha,
                "eps_pa": d.parameters.eps_pa,
                "eps_ev": d.parameters.eps_ev,
                "lambda_ec": d.parameters.lambda_ec,
            },
        },
    }
    return manifest, arrays, ids


def build_general_bundle(
    declaration: GeneralDeclaration,
    *,
    alice_announcements: Sequence[str],
    bob_announcements: Sequence[str],
    reduction_chain: Mapping[str, object] | None,
    created_by: str,
) -> tuple[OperatorBundle, WireLabels]:
    """Build the same checked bundle used by the ordinary pipeline."""
    manifest, arrays, labels = general_bundle_documents(
        declaration,
        alice_announcements=alice_announcements,
        bob_announcements=bob_announcements,
        reduction_chain=reduction_chain,
        created_by=created_by,
    )
    return OperatorBundle(manifest=parse_manifest(manifest), arrays=arrays), labels
