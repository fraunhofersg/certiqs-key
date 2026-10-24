"""A docked declaration and its reduction chain, written as an operator bundle.

The one place in this slice where numbers become a file. It takes the
:class:`~certiqs_key.meat_core.declaration.declaration.ProtocolDeclaration` that
:func:`certiqs_key.meat_core.docking.dock_declaration` produced, the reduction-chain
record the same compilation emitted, and writes the schema **0.2.0** manifest and
array payload of :mod:`certiqs_key.domain`.

WHAT IS AND IS NOT ADJUSTED HERE
================================
Nothing is adjusted. The matrices written out are the docked ones, entry for
entry, at ``complex128``; the acceptance set is the one
``statistics`` docked; the parameters are the caller's. The only
transformation is the re-keying of :mod:`certiqs_key.runs.identifiers`,
which changes names and never a number, never an order and never a table's
domain.

That is deliberate rather than minimal. The bundle is then read back by
:func:`certiqs_key.domain.read_bundle` and turned into a declaration again by
``meat-core``'s own
:func:`~certiqs_key.meat_core.declaration.bundle.declaration_from_bundle`, which
re-validates everything from its own side (spec/architecture.md 3.6). A writer that
repaired its input would collapse two fail-closed paths into one, which is the same
argument ``certiqs_key.meat_core.docking`` makes about docking rather than trusting.

WHY THE REDUCTION CHAIN TRAVELS AT ALL
======================================
Because spec/architecture.md 6 says it does: the identity link an ideal-qubit protocol
reduces by is "recorded in the bundle as an ``exact`` reduction". Before this
slice the compiler's ``reduction_chain_record`` stayed inside
``protocol-compiler``'s own artifact -- that band authorized no wire extension --
and schema 0.2.0 is the extension §4.4 authorizes. The record is copied across
UNCHANGED except for the same re-keying: this module adds no field the compiler
did not emit, and drops none that it did. (Where a one-factor declaration
carries a route-C weighting, the pipeline hands this module the compiler's
record already read through that weighting, as the compiler's own
multi-factor record is: ``runs.pipeline._chain_record_through_weighting``.)
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from certiqs_key.domain.arrays import ArrayPayload, DenseArray
from certiqs_key.domain.bundle import OperatorBundle, parse_manifest
from certiqs_key.domain.manifest import SCHEMA_VERSION
from certiqs_key.foundations.blocks import BlockKind
from certiqs_key.meat_core.declaration.declaration import (
    ConstraintEntry,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.declaration.validation import (
    MATHEMATICAL_SPEC_VERSION,
    REQUIRED_ASSUMPTIONS,
)
from certiqs_key.runs.errors import SliceAssemblyError
from certiqs_key.runs.identifiers import sanitize, stable_id_map

__all__ = ["WireLabels", "build_bundle", "bundle_documents", "wire_labels"]


@dataclass(frozen=True)
class WireLabels:
    """The label-to-stable-ID bijections of one declaration, one per alphabet.

    Kept as a record rather than applied inline so that a caller can read a
    result keyed by wire IDs back into the compiler's own spelling without
    re-deriving the map -- and so that a test can assert the map is what it looks
    like.
    """

    alice_outcome: Mapping[str, str]
    bob_outcome: Mapping[str, str]
    alice_announcement: Mapping[str, str]
    bob_announcement: Mapping[str, str]
    acceptance_value: Mapping[str, str]
    sector: Mapping[str, str]


def wire_labels(
    declaration: ProtocolDeclaration,
    *,
    alice_announcements: Sequence[str],
    bob_announcements: Sequence[str],
) -> WireLabels:
    """Return the six bijections, in each alphabet's declared order."""
    return WireLabels(
        alice_outcome=stable_id_map(declaration.alice_outcomes, "alice_outcome"),
        bob_outcome=stable_id_map(declaration.bob_outcomes, "bob_outcome"),
        alice_announcement=stable_id_map(alice_announcements, "alice_announcement"),
        bob_announcement=stable_id_map(bob_announcements, "bob_announcement"),
        acceptance_value=stable_id_map(
            declaration.acceptance_values, "acceptance_value"
        ),
        sector=stable_id_map(declaration.sector_index_set, "sector_index_set"),
    )


def _descriptor(
    dataset: str, array: np.ndarray, *, basis: str, subsystem: str, role: str
) -> dict[str, Any]:
    """Return one dense ``complex128`` array descriptor."""
    return {
        "form": "array",
        "dataset": dataset,
        "dtype": "complex128",
        "shape": list(array.shape),
        "basis": basis,
        "subsystem_order": [subsystem],
        "storage": "dense",
        "semantic_role": role,
    }


def _as_complex(operator: Any) -> np.ndarray:
    """Return one operator as a ``complex128`` array, without altering an entry."""
    return np.asarray(operator, dtype=np.complex128)


def _reduction_chain(
    record: Mapping[str, object], labels: WireLabels
) -> dict[str, Any]:
    """Return the compiler's chain record re-keyed for the wire.

    The compiler's own shape, key for key: two named segments in composition
    order, per link the ten slots
    :func:`certiqs_key.protocol_compiler.compile.chain_record` emits, and the outcome
    correspondence as ordered pairs. Only the OUTCOME LABELS move, and the emitted half
    moves by the same bijection every other table did -- which is what makes the
    wire-format check that the emitted half lands inside the declared Bob alphabet a
    real check rather than a tautology about strings this module just invented.
    """
    correspondence: list[list[str]] = []
    for pair in _sequence(record, "outcome_correspondence"):
        physical, emitted = _pair(pair)
        if emitted not in labels.bob_outcome:
            raise SliceAssemblyError(
                f"the reduction chain maps the physical outcome {physical!r} to "
                f"{emitted!r}, which is not an outcome of the emitted "
                f"declaration {sorted(labels.bob_outcome)}"
            )
        correspondence.append([sanitize(physical), labels.bob_outcome[emitted]])
    return {
        "source_segment": [_link(link) for link in _sequence(record, "source_segment")],
        "receiver_segment": [
            _link(link) for link in _sequence(record, "receiver_segment")
        ],
        "outcome_correspondence": correspondence,
    }


def _link(link: object) -> dict[str, Any]:
    """Return one link record, with its two descriptors."""
    if not isinstance(link, Mapping):
        raise SliceAssemblyError(f"a reduction link is a record; got {link!r}")
    out = dict(link)
    for side in ("source_descriptor", "target_descriptor"):
        descriptor = out.get(side)
        if not isinstance(descriptor, Mapping):
            raise SliceAssemblyError(
                f"a reduction link carries a {side}; got {descriptor!r}"
            )
        sectors = descriptor.get("sectors")
        out[side] = {
            **descriptor,
            "sectors": (
                None
                if sectors is None
                else [
                    [sanitize(str(label)), dimension]
                    for label, dimension in _sectors(sectors)
                ]
            ),
        }
    return out


def _sectors(sectors: object) -> list[tuple[str, int]]:
    """Return a declared sector decomposition as label/dimension pairs."""
    if not isinstance(sectors, Sequence) or isinstance(sectors, str):
        raise SliceAssemblyError(f"a sector decomposition is a list; got {sectors!r}")
    out: list[tuple[str, int]] = []
    for entry in sectors:
        if not isinstance(entry, Sequence) or isinstance(entry, str) or len(entry) != 2:
            raise SliceAssemblyError(
                f"a sector entry is a (label, dimension) pair; got {entry!r}"
            )
        out.append((str(entry[0]), int(entry[1])))
    return out


def _sequence(record: Mapping[str, object], key: str) -> Sequence[Any]:
    """Return one list-valued key of the chain record."""
    value = record.get(key)
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise SliceAssemblyError(
            f"the reduction-chain record's {key!r} is a list; got {value!r}"
        )
    return value


def _pair(pair: object) -> tuple[str, str]:
    """Return one outcome-correspondence entry as a pair of labels."""
    if not isinstance(pair, Sequence) or isinstance(pair, str) or len(pair) != 2:
        raise SliceAssemblyError(
            f"an outcome correspondence entry is a pair; got {pair!r}"
        )
    return str(pair[0]), str(pair[1])


def _constraint(
    entry: ConstraintEntry,
    index: int,
    ids: WireLabels,
    declaration: ProtocolDeclaration,
    arrays: dict[str, ArrayPayload],
) -> dict[str, Any]:
    """Return one Section 2.1 constraint entry in its wire form.

    THE BOUND'S TYPE IS THE DECLARATION'S AND IS NOT NORMALIZED HERE. Contract
    def:admissible-declaration (vi) fixes it by source mode -- a Hermitian operator on
    ``A`` in trusted-source mode, a real scalar in untrusted-source mode -- and
    ``meat-core``'s Remark ``rem:homog`` (a) exhibits a licensed attack set for
    which reading a scalar entry as ``Theta_k = c_k 1_A`` EMPTIES the feasible
    set. So a scalar is written as a JSON number and an operator as an array,
    exactly as the entry carries it, and neither is converted into the other.

    ``O_k`` crosses in the SAME block-diagonal form as a Bob POVM element,
    because def:admissible-declaration (iii) requires it to be sector-block-diagonal and
    :class:`~certiqs_key.domain.arrays.BlockDiagonalOperator` is how this format
    spells that. The block order is the declaration's own sector order.
    """
    blocks: dict[str, Any] = {}
    for sector, block in entry.operator_blocks.items():
        sector_id = ids.sector[sector]
        path = f"/declaration/constraint_list/{index}/operator/{sector_id}"
        array = _as_complex(block)
        arrays[path] = DenseArray(array)
        blocks[sector_id] = _descriptor(
            path,
            array,
            basis=f"computational.Q.{sector_id}",
            subsystem="Q",
            role="constraint_operator",
        )
    operator = {
        "form": "block_diagonal",
        # THE SHARED FORMAT'S OWN ALPHABET, not a literal: BlockKind is an
        # spec/architecture.md 2.9 frozen type (spec/architecture.md 2.9), so a
        # rename there is a type error here instead of a silent wire drift.
        "block_kind": BlockKind.PROOF_SECTOR.value,
        "blocks": blocks,
        "block_permutation": list(range(len(declaration.sector_index_set))),
    }

    bound: Any
    if entry.is_scalar:
        bound = entry.scalar_bound
    else:
        path = f"/declaration/constraint_list/{index}/bound"
        array = _as_complex(entry.operator_bound)
        arrays[path] = DenseArray(array)
        bound = _descriptor(
            path,
            array,
            basis="computational.A",
            subsystem="A",
            role="constraint_bound",
        )

    return {
        "operator": operator,
        "relation": str(entry.relation),
        "bound": bound,
        # THE DECLARED FORM. Carried
        # from the declaration, never derived from `bound`: the tag is a
        # DECLARED datum and one this writer read off the number it is writing
        # would be a default deciding a security-relevant predicate on nobody's
        # authority (`meat-core`'s own constraint row; `protocol-compiler`
        # Definition `def:homog`).
        "constraint_rhs_tag": str(entry.rhs_tag),
    }


def bundle_documents(
    declaration: ProtocolDeclaration,
    *,
    alice_announcements: Sequence[str],
    bob_announcements: Sequence[str],
    reduction_chain: Mapping[str, object] | None,
    created_by: str,
    labels: WireLabels | None = None,
) -> tuple[dict[str, Any], dict[str, ArrayPayload], WireLabels]:
    """Return ``(manifest, arrays, labels)`` for one docked declaration."""
    ids = (
        wire_labels(
            declaration,
            alice_announcements=alice_announcements,
            bob_announcements=bob_announcements,
        )
        if labels is None
        else labels
    )
    arrays: dict[str, ArrayPayload] = {}

    marginal: dict[str, Any] | None = None
    if declaration.alice_marginal is not None:
        array = _as_complex(declaration.alice_marginal)
        arrays["/declaration/alice_marginal"] = DenseArray(array)
        marginal = _descriptor(
            "/declaration/alice_marginal",
            array,
            basis="computational.A",
            subsystem="A",
            role="alice_marginal",
        )

    alice_povm: dict[str, Any] = {}
    for label, element in declaration.alice_povm.items():
        identifier = ids.alice_outcome[label]
        path = f"/declaration/alice_povm/{identifier}"
        array = _as_complex(element)
        arrays[path] = DenseArray(array)
        alice_povm[identifier] = _descriptor(
            path,
            array,
            basis="computational.A",
            subsystem="A",
            role="alice_povm_element",
        )

    bob_povm: dict[str, Any] = {}
    for label, blocks in declaration.bob_povm.items():
        identifier = ids.bob_outcome[label]
        descriptors: dict[str, Any] = {}
        for sector, block in blocks.items():
            sector_id = ids.sector[sector]
            path = f"/declaration/bob_povm/{identifier}/{sector_id}"
            array = _as_complex(block)
            arrays[path] = DenseArray(array)
            descriptors[sector_id] = _descriptor(
                path,
                array,
                basis=f"computational.Q.{sector_id}",
                subsystem="Q",
                role="bob_povm_element",
            )
        bob_povm[identifier] = {
            "form": "block_diagonal",
            "block_kind": BlockKind.PROOF_SECTOR.value,
            "blocks": descriptors,
            "block_permutation": list(range(len(declaration.sector_index_set))),
        }

    constraint_list = [
        _constraint(entry, index, ids, declaration, arrays)
        for index, entry in enumerate(declaration.constraint_list)
    ]

    accept_statistic: dict[str, dict[str, str]] = {}
    for (c_a, c_b), chat in declaration.accept_statistic.items():
        row = accept_statistic.setdefault(ids.alice_announcement[c_a], {})
        row[ids.bob_announcement[c_b]] = ids.acceptance_value[chat]

    key_map: dict[str, dict[str, int | None]] = {}
    for (x, v), value in declaration.key_map.items():
        key_map.setdefault(ids.alice_outcome[x], {})[ids.bob_outcome[v]] = value

    partition = declaration.party_partition
    party_partition: dict[str, Any] | None = None
    if partition is not None:
        # The readout alphabets O_A and O_B coincide with X and V only under
        # the DEFAULT partition, which is the one an ideal-qubit BB84
        # declaration carries and the only one this slice re-keys. A
        # declaration whose readouts range over some third alphabet would need
        # two more bijections, and inventing them here would silently rename a
        # readout into an outcome.
        if (
            tuple(partition.alphabet_alice) != declaration.alice_outcomes
            or tuple(partition.alphabet_bob) != declaration.bob_outcomes
        ):
            raise SliceAssemblyError(
                "this slice re-keys a declaration whose readout alphabets O_A "
                "and O_B are X and V -- the default party partition of "
                "meat-core Definition def:declaration. This one declares "
                f"O_A = {list(partition.alphabet_alice)} and "
                f"O_B = {list(partition.alphabet_bob)}"
            )
        readout_alice: dict[str, dict[str, str]] = {}
        for (x_a, v_a), readout in partition.readout_alice.items():
            row_a = readout_alice.setdefault(ids.alice_outcome[x_a], {})
            row_a[ids.bob_outcome[v_a]] = ids.alice_outcome[readout]
        readout_bob: dict[str, dict[str, str]] = {}
        for (x_b, v_b), readout in partition.readout_bob.items():
            row_b = readout_bob.setdefault(ids.alice_outcome[x_b], {})
            row_b[ids.bob_outcome[v_b]] = ids.bob_outcome[readout]
        party_partition = {
            "readout_alice": readout_alice,
            "readout_bob": readout_bob,
            "alphabet_alice": [
                ids.alice_outcome[label] for label in partition.alphabet_alice
            ],
            "alphabet_bob": [
                ids.bob_outcome[label] for label in partition.alphabet_bob
            ],
            "party_of_alice_system": str(partition.party_of_alice_system),
            "party_of_sector_factors": {
                ids.sector[sector]: [str(party) for party in parties]
                for sector, parties in partition.party_of_sector_factors.items()
            },
        }

    wire_declaration: dict[str, Any] = {
        "alice_dim": declaration.alice_dim,
        "alice_marginal": marginal,
        # THE LICENCE IS SERIALIZED BY ITS OWNER AND PASSED THROUGH. The
        # transmitter emits it as JSON (SourceReplacementLicense
        # .as_machine_record: exact matrices through
        # foundations.exact.serialize_matrix, weights as "p/q"), so this
        # writer copies the record and converts nothing.
        "source_replacement_license": (
            None
            if declaration.source_replacement_license is None
            else dict(declaration.source_replacement_license)
        ),
        "party_partition": party_partition,
        "sector_index_set": [ids.sector[s] for s in declaration.sector_index_set],
        "sector_dims": {
            ids.sector[s]: dimension for s, dimension in declaration.sector_dims.items()
        },
        # THE THIRD COMPONENT OF THE ONE SECTOR MAP, carried and never
        # supplied. It is the docked declaration's own datum: the compiler read
        # it off the specification the instance declared, and this writer
        # transcribes it. Where the declaration carries none the manifest model
        # refuses the bundle at the boundary, which is where the
        # producer that omitted it is still identifiable -- inventing a kind
        # here would be this tier deciding what somebody else's identifiers
        # mean (`protocol-compiler` Section 2.5, `decide_never_infer`).
        "sector_block_kind": declaration.sector_block_kind,
        "alice_povm": alice_povm,
        "bob_povm": bob_povm,
        "announce_alice": {
            ids.alice_outcome[x]: ids.alice_announcement[c]
            for x, c in declaration.announce_alice.items()
        },
        "announce_bob": {
            ids.bob_outcome[v]: ids.bob_announcement[c]
            for v, c in declaration.announce_bob.items()
        },
        "accept_statistic": accept_statistic,
        "key_map": key_map,
        "key_holder": str(declaration.key_holder),
        "constraint_list": constraint_list,
        "attack_set_license": (
            None
            if declaration.attack_set_license is None
            else dict(declaration.attack_set_license)
        ),
        "acceptance_set": _acceptance_set(declaration),
        "rounds": declaration.rounds,
    }

    manifest: dict[str, Any] = {
        "kind": "operator-bundle",
        "schema_version": SCHEMA_VERSION,
        "mathematical_spec_version": MATHEMATICAL_SPEC_VERSION,
        "created_by": created_by,
        "implementation_version": _implementation_version(),
        # contract Section 2.5, and the values meat-core's own validator
        # requires. Read from that module rather than restated, so that a
        # convention cannot be declared here and enforced differently there.
        "assumptions": dict(REQUIRED_ASSUMPTIONS),
        "warnings": [],
        "payload": {
            "alphabets": {
                "alice_outcome": [
                    ids.alice_outcome[x] for x in declaration.alice_outcomes
                ],
                "bob_outcome": [ids.bob_outcome[v] for v in declaration.bob_outcomes],
                "alice_announcement": [
                    ids.alice_announcement[c] for c in alice_announcements
                ],
                "bob_announcement": [
                    ids.bob_announcement[c] for c in bob_announcements
                ],
                "acceptance_value": [
                    ids.acceptance_value[c] for c in declaration.acceptance_values
                ],
                "key_value_count": declaration.key_value_count,
            },
            "declaration": wire_declaration,
            # NOT one of `declaration`'s keys: that model is exactly
            # meat-core's Section 2.1 INPUT table, and a reduction chain is a
            # protocol-compiler OUTPUT key. spec/architecture.md 4.1 lists
            # `reduction_chain` among the ProofInstance contents without
            # prescribing nesting, so it does not decide this either way; the
            # format's own docstring records what does.
            "reduction_chain": (
                None
                if reduction_chain is None
                else _reduction_chain(reduction_chain, ids)
            ),
            "parameters": {
                "alpha": declaration.parameters.alpha,
                "eps_pa": declaration.parameters.eps_pa,
                "eps_ev": declaration.parameters.eps_ev,
                "lambda_ec": declaration.parameters.lambda_ec,
            },
        },
    }
    return manifest, arrays, ids


def _acceptance_set(
    declaration: ProtocolDeclaration | GeneralDeclaration,
) -> dict[str, Any]:
    """Return the declared acceptance set in its wire form.

    The sub-keys of ``data`` are ``statistics``'s own for the same
    objects, which is the serialization ``certiqs_key.meat_core.declaration.bundle``
    documents and reads. Nothing here is re-keyed, and that is the point: the
    set is carried POSITIONALLY, one column of ``B`` per acceptance value in the
    alphabet's declared order, so a renaming of the acceptance values cannot
    touch it and cannot permute it.
    """
    acceptance = declaration.acceptance_set
    if acceptance.polytope is None:
        return {
            "geometry": acceptance.geometry,
            "data": {"frequencies": list(acceptance.frequencies)},
            "arrays": {},
        }
    polytope = acceptance.polytope
    data: dict[str, Any] = {
        "m_row": polytope.m_row,
        "B": [list(row) for row in polytope.rows],
        "b": list(polytope.rhs),
    }
    if polytope.box_bounds is not None:
        lower, upper = polytope.box_bounds
        data["box_bounds"] = [list(lower), list(upper)]
    return {"geometry": acceptance.geometry, "data": data, "arrays": {}}


def _implementation_version() -> str:
    """Return the distribution version this bundle was written by.

    READ FROM THE INSTALLED DISTRIBUTION METADATA and not from a module
    constant: ``pyproject.toml`` is the "single source of dependency
    truth" (spec/architecture.md 8) and a second spelling in the package would
    be a version pinned twice. A checkout that is not installed has no
    metadata, which is not a reason to refuse a bundle and not a number to
    invent either, so the manifest says so in the one place it appears.
    """
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("certiqs-key")
    except PackageNotFoundError:  # pragma: no cover - an uninstalled checkout
        return "unknown (certiqs-key is not installed in this environment)"


def build_bundle(
    declaration: ProtocolDeclaration,
    *,
    alice_announcements: Sequence[str],
    bob_announcements: Sequence[str],
    reduction_chain: Mapping[str, object] | None,
    created_by: str,
) -> tuple[OperatorBundle, WireLabels]:
    """Return ``declaration`` as a parsed, format-validated operator bundle."""
    manifest, arrays, labels = bundle_documents(
        declaration,
        alice_announcements=alice_announcements,
        bob_announcements=bob_announcements,
        reduction_chain=reduction_chain,
        created_by=created_by,
    )
    return OperatorBundle(manifest=parse_manifest(manifest), arrays=arrays), labels
