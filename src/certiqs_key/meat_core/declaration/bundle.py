"""Read a serialized operator bundle into a :class:`ProtocolDeclaration`.

The bundle format (:mod:`certiqs_key.domain`) is not proof-critical and validates
a bundle only as *data*. This module is the other half: it turns the validated
data into the declaration ``D`` of contract Definition ``def:declaration`` and
then runs the mathematical checks of spec/architecture.md 3.6
(:mod:`certiqs_key.meat_core.declaration.validation`). Everything fails closed; a bundle
that does not validate produces no result at all.

Two conversions are this module's and are stated rather than assumed.

* **The sector map.** The format writes an operator as ONE ARRAY PER SECTOR
  and in no other form (spec/architecture.md 2.9), so sector-block-diagonality holds
  by construction and nothing here verifies it. What this module compares is
  the producer's sector map -- the block identifiers and their ordering --
  against the declared sector index set -- THE ONLY STRUCTURAL FAILURE THE
  REPRESENTATION ADMITS (``def:declaration``, the operator paragraph).
  Its refusal is ``sector_map_disagreement``, decided at no window.
* **Permutations.** A descriptor may declare ``basis_permutation``,
  ``subsystem_permutation`` or ``block_permutation``. The format checks that
  each is a permutation; what a non-identity one *means* is not fixed by the
  accepted contract, so a non-identity permutation is refused rather than
  interpreted.

THE THREE SLOTS
===============
``alice_marginal`` may be absent, and its absence is not a defect: it is the
slot value ``none`` of contract Definition ``def:declaration``, which Remark
``rem:modes-da1`` *defines* to be untrusted-source mode. Nothing is
substituted for it -- neither ``0`` (inadmissible, ``transmitter/rem:source-mode`` (c))
nor
``1_A/d_A`` (a different and STRONGER declaration, Assumption A-SRC). The
source mode is then read off the slot by
:attr:`~certiqs_key.meat_core.declaration.declaration.ProtocolDeclaration.source_mode`,
and no bundle field carries it.

``source_replacement_license`` and ``party_partition`` are likewise optional:
the first absent means no A-SRC attestation was supplied, and the second absent
means the DEFAULT partition, which ``def:declaration`` says reproduces versions
0.2.x verbatim.

THE ACCEPTANCE-SET WIRE KEYS, AND WHY THEY NEED NO SCHEMA CHANGE
================================================================
``meat-core``'s interface fixes exactly one key here, ``acceptance_set``
(the `inputs` table), and the operator-bundle schema types its ``data`` block
as a free-form JSON object precisely because "its taxonomy belongs to
``statistics`` and is deliberately not enumerated here". So carrying
a ``polytope`` geometry needs NO schema version bump: the tag and its data ride
in the slots the format provides, and ``schemas/`` holds nothing more.

Which sub-keys go in that slot is a serialization decision with no
proof-relevant content, and it is taken here rather than left implicit: the
names are the ones the accepted ``statistics`` taxonomy uses
for the same objects -- ``m_row``, ``B``, ``b`` and ``box_bounds`` -- so that
the producer and the consumer spell one taxonomy one way. ``box_bounds`` is the
ORDERED PAIR ``[q^-, q^+]`` of Eq. ``eq:boxset``; a transposed pair is caught by
the ``0 <= q^- <= q^+`` well-formedness check rather than read as a different
box. ``m_row`` is redundant against ``len(B)`` and is required anyway, because
declared data that contradicts itself must be refused rather than silently
reconciled.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from certiqs_key.domain.arrays import (
    ArrayDescriptor,
    ArrayPayload,
    BlockDiagonalOperator,
    DenseArray,
    SparseCSCArray,
    dense_from_csc,
)
from certiqs_key.domain.bundle import OperatorBundle
from certiqs_key.domain.manifest import PartyPartition as ManifestPartyPartition
from certiqs_key.meat_core.acceptance.geometry import GEOMETRY_TAGS, POLYTOPE, SINGLETON
from certiqs_key.meat_core.declaration.admission import check_sector_map
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    ConstraintEntry,
    KeyLengthParameters,
    PartyPartition,
    PolytopeData,
    ProtocolDeclaration,
    RhsTag,
)
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.declaration.validation import (
    validate_declaration,
    validate_manifest_bindings,
)
from certiqs_key.meat_core.errors import DeclarationError, UnsupportedDeclarationError
from certiqs_key.meat_core.objective.linalg import Matrix


def _check_identity_permutation(
    permutation: tuple[int, ...] | None, name: str, where: str
) -> None:
    """Raise unless ``permutation`` is absent or the identity."""
    if permutation is None:
        return
    if tuple(permutation) != tuple(range(len(permutation))):
        raise UnsupportedDeclarationError(
            f"{where}: a non-identity {name} is not interpreted by this "
            "implementation. The bundle format checks that it is a "
            "permutation, but the accepted contract does not fix what it "
            "means, so applying one would be an interface improvisation"
        )


def _materialize(
    descriptor: ArrayDescriptor, arrays: dict[str, ArrayPayload], where: str
) -> Matrix:
    """Return one declared array as a dense complex matrix."""
    _check_identity_permutation(
        descriptor.basis_permutation, "basis_permutation", where
    )
    _check_identity_permutation(
        descriptor.subsystem_permutation, "subsystem_permutation", where
    )
    payload = arrays.get(descriptor.dataset)
    if payload is None:
        raise DeclarationError(
            f"{where}: the manifest declares dataset {descriptor.dataset!r} but "
            "the bundle carries no such array"
        )
    if isinstance(payload, SparseCSCArray):
        if descriptor.index_base is None:
            raise DeclarationError(
                f"{where}: a sparse array without a declared index base"
            )
        values = dense_from_csc(payload, descriptor.index_base)
    elif isinstance(payload, DenseArray):
        values = payload.values
    else:  # pragma: no cover - the payload union has exactly two members
        raise DeclarationError(f"{where}: unknown array payload {type(payload)!r}")
    matrix = np.asarray(values, dtype=np.complex128)
    if matrix.ndim == 1:
        matrix = matrix.reshape(-1, 1)
    if matrix.ndim != 2:
        raise DeclarationError(f"{where}: expected a matrix, got shape {matrix.shape}")
    return matrix


def _blocks_from_operator(
    operator: BlockDiagonalOperator,
    arrays: dict[str, ArrayPayload],
    sector_index_set: tuple[str, ...],
    where: str,
    consumer_kind: str | None,
) -> dict[str, Matrix]:
    """Return the sector blocks of a declared operator, after condition (T).

    CONDITION (T) IS A TYPE RULE, AND THIS IS WHERE IT IS DECIDED.
    A declared operator arrives as ONE ARRAY PER SECTOR plus the sector map, so
    sector-block-diagonality HOLDS BY CONSTRUCTION: "nothing can write an
    off-block entry, NOTHING VERIFIES THAT NONE WAS WRITTEN, and no
    ``d_Q x d_Q`` matrix is assembled in order to be checked"
    (spec/architecture.md 2.9). What a consumer compares
    instead is THE SECTOR MAP -- the block identifiers and their ordering
    against its own -- "and a disagreement is a refusal with a machine-readable
    reason, WHICH IS THE ONLY FAILURE MODE THE REPRESENTATION ADMITS".

    NO FULL-SPACE ARRAY IS OFFERED. A format that offered one would have this
    function split it and refuse a non-block-diagonal one -- the argument being
    that a caller holding a violation must be able to serialize it or
    ``meat-core`` could never detect it. spec/architecture.md 2.9 records that
    the argument is CORRECT IN ITS OWN TERMS and is overturned BY A CHANGE OF
    PREMISE rather than by a refutation: once the producer emits per sector
    there is no off-sector part to discard and no expressible object to catch.
    No ``d_Q x d_Q`` array is materialized in this module.

    NO TOLERANCE REACHES ANY OF THIS, and there is none in this module to
    reach it. The sector-map comparison is a structural check decided by a
    COMPARISON OF DECLARED LABELS (the interface's
    ``fail_closed.how_a_rule_is_decided``), and a disagreement is refused
    outright.

    BOTH PRODUCTION CALL SITES ARE COVERED BY THIS ONE COMPARISON: the
    ``bob_povm`` outcomes and the constraint operators ``hat O_k``, which are
    sector-block diagonal for the same reason and by the same type.
    """
    _check_identity_permutation(operator.block_permutation, "block_permutation", where)
    check_sector_map(
        tuple(operator.blocks),
        sector_index_set,
        where,
        declared_kind=str(operator.block_kind),
        consumer_kind=consumer_kind,
    )
    return {
        sector: _materialize(operator.blocks[sector], arrays, f"{where}[{sector}]")
        for sector in sector_index_set
    }


def _declared_rhs_tag(declared: str, where: str) -> RhsTag:
    """Return the entry's DECLARED right-hand-side form, or refuse.

    Definition ``def:homog`` fixes exactly two forms, ``homogeneous`` and
    ``general``, and the `inputs` table makes part (i) of the two-part security gate a
    "TYPE CHECK ON THE DECLARED TAG". So this reads the datum and does two
    things with a string that is not one of the two: it does NOT map it to a
    nearest member, and it does NOT fall back to ``general`` on the grounds
    that ``general`` is the fail-closed value. A third tag is a declaration
    this module cannot read, and reading it as either of the two would be
    deciding, on nobody's authority, which security-relevant class a producer
    meant to put its entry in.

    Args:
        declared: the wire's ``constraint_rhs_tag``, required and carrying no
            default at any tier.
        where: the entry's path in the payload, for the refusal.

    Raises:
        DeclarationError: on any value outside the two.
    """
    try:
        return RhsTag(declared)
    except ValueError:
        raise DeclarationError(
            f"Definition def:homog: {where} declares constraint_rhs_tag "
            f"{declared!r}, which is neither `homogeneous` nor `general`. The "
            "two tagged forms are the only ones this contract defines, part "
            "(i) of the security gate is a TYPE CHECK ON THE DECLARED TAG, and "
            "a tag this module chose for an entry whose producer declared "
            "something else would decide a security-relevant predicate on "
            "nobody's authority. It is not read off `bound` either"
        ) from None


def declaration_from_bundle(
    bundle: OperatorBundle,
) -> ProtocolDeclaration | GeneralDeclaration:
    """Return the validated declaration a bundle carries.

    Runs, in order: the artefact binding and convention checks of the
    interface's ``artifact_bindings`` and ``conventions``, the array
    conversions above, and the full ``def:admissible-declaration`` /
    ``def:admissible-acceptance-set`` check of :func:`validate_declaration`. Any failure
    raises.

    IT TAKES NO TOLERANCE: this module reads no declared numerical tolerance in
    any form (spec/architecture.md 2.8). Declared data reaches this module
    exactly admissible or the run is refused.

    THE SECTOR MAP IS COMPARED HERE. :func:`_blocks_from_operator` compares the
    producer's sector map with this module's -- the block kind, the block
    identifiers and their ordering -- before any number is read, and a
    disagreement is refused with ``sector_map_disagreement``. Sector-block
    diagonality itself is not checked and cannot be: it holds by construction
    (spec/architecture.md 2.9).
    """
    validate_manifest_bindings(bundle.manifest)
    payload = bundle.manifest.payload
    declared = payload.declaration
    if any(
        getattr(declared, key, None) is not None for key in declared.GENERAL_FORMAT_KEYS
    ) or any(
        entry.constraint_rhs_tag == "party_local" for entry in declared.constraint_list
    ):
        from certiqs_key.meat_core.declaration.general_bundle import (
            general_declaration_from_bundle,
        )

        return general_declaration_from_bundle(bundle)
    arrays = dict(bundle.arrays)

    sector_index_set = tuple(declared.sector_index_set)
    sector_dims = {
        sector: int(declared.sector_dims[sector])
        for sector in sector_index_set
        if sector in declared.sector_dims
    }
    # THE CONSUMER'S OWN BLOCK KIND, read from the declaration the producer
    # emitted. The `inputs` table makes it a component of the
    # sector map, and
    # what this module decides is AGREEMENT across the map and with itself --
    # never which kind is right, which the shared format settles one tier down.
    # The FIRST operator's kind is this declaration's kind, and every other
    # operator is compared against it, so a bundle whose operators disagree
    # among themselves is refused just as one that disagrees with a consumer is.
    kinds = [str(operator.block_kind) for operator in declared.bob_povm.values()]
    kinds += [str(entry.operator.block_kind) for entry in declared.constraint_list]
    sector_block_kind = kinds[0] if kinds else None

    missing = set(sector_index_set) - set(sector_dims)
    if missing:
        raise DeclarationError(
            f"the `inputs` table: sector_dims declares no dimension for "
            f"{sorted(missing)}"
        )

    alice_povm = {
        outcome: _materialize(
            descriptor, arrays, f"payload.declaration.alice_povm[{outcome!r}]"
        )
        for outcome, descriptor in declared.alice_povm.items()
    }
    bob_povm = {
        outcome: _blocks_from_operator(
            operator,
            arrays,
            sector_index_set,
            f"payload.declaration.bob_povm[{outcome!r}]",
            sector_block_kind,
        )
        for outcome, operator in declared.bob_povm.items()
    }

    accept_statistic = {
        (c_a, c_b): value
        for c_a, row in declared.accept_statistic.items()
        for c_b, value in row.items()
    }
    key_map: dict[tuple[str, str], int | None] = {
        (x, v): value for x, row in declared.key_map.items() for v, value in row.items()
    }

    constraints = tuple(
        ConstraintEntry(
            operator_blocks=_blocks_from_operator(
                entry.operator,
                arrays,
                sector_index_set,
                f"payload.declaration.constraint_list[{index}].operator",
                sector_block_kind,
            ),
            relation=entry.relation,
            # THE TAG IS READ FROM THE DATUM, NEVER OFF THE BOUND'S TYPE.
            # Definition def:homog: "the form is part of the datum RATHER THAN
            # A PROPERTY MEASURED OF IT"; the `inputs` table: "Part (i) is
            # a TYPE
            # CHECK ON THE DECLARED TAG and compares no numbers". The wire
            # carries `constraint_rhs_tag` as a required key for exactly this
            # reason, and domain/manifest.py states the rule from the format's
            # side -- it "does not invent one, and IT DOES NOT READ ONE OFF
            # bound, because the tag is a DECLARED datum and a format-supplied
            # one would be a code default deciding a security-relevant
            # predicate ... on nobody's authority".
            #
            # WHAT INFERRING IT WOULD COST. An entry whose producer DECLARED
            # `general` and carries a scalar bound would be read as
            # `homogeneous` and LICENSED for a key length, on an entry
            # def:homog says "is never licensed" -- unsafe. The converse
            # mismatch would be safe. Neither reaches an iterate: each is a
            # type disagreement between the tag and the bound, and
            # `validate_declaration` refuses both.
            rhs_tag=_declared_rhs_tag(
                entry.constraint_rhs_tag,
                f"payload.declaration.constraint_list[{index}]",
            ),
            bound=(
                float(entry.bound)
                if not isinstance(entry.bound, ArrayDescriptor)
                else _materialize(
                    entry.bound,
                    arrays,
                    f"payload.declaration.constraint_list[{index}].bound",
                )
            ),
        )
        for index, entry in enumerate(declared.constraint_list)
    )

    acceptance = _acceptance_set(
        declared.acceptance_set.geometry,
        dict(declared.acceptance_set.data),
        len(payload.alphabets.acceptance_value),
    )
    parameters = KeyLengthParameters(
        alpha=float(payload.parameters.alpha),
        eps_pa=float(payload.parameters.eps_pa),
        eps_ev=float(payload.parameters.eps_ev),
        lambda_ec=int(payload.parameters.lambda_ec),
    )

    declaration = ProtocolDeclaration(
        alice_dim=int(declared.alice_dim),
        # The MARGINAL SLOT. `None` here is the slot value `none` of Definition
        # def:declaration -- untrusted-source mode -- and nothing stands in for
        # it (Remark transmitter/rem:source-mode (c), def:untrusted-choi (b)).
        alice_marginal=(
            None
            if declared.alice_marginal is None
            else _materialize(
                declared.alice_marginal, arrays, "payload.declaration.alice_marginal"
            )
        ),
        sector_index_set=sector_index_set,
        sector_dims=sector_dims,
        sector_block_kind=sector_block_kind,
        alice_povm=alice_povm,
        bob_povm=bob_povm,
        announce_alice=dict(declared.announce_alice),
        announce_bob=dict(declared.announce_bob),
        accept_statistic=accept_statistic,
        key_map=key_map,
        key_holder=declared.key_holder,
        acceptance_values=tuple(payload.alphabets.acceptance_value),
        key_value_count=int(payload.alphabets.key_value_count),
        acceptance_set=acceptance,
        rounds=int(declared.rounds),
        parameters=parameters,
        constraint_list=constraints,
        attack_set_license=(
            dict(declared.attack_set_license)
            if declared.attack_set_license is not None
            else None
        ),
        source_replacement_license=(
            dict(declared.source_replacement_license)
            if declared.source_replacement_license is not None
            else None
        ),
        party_partition=_party_partition(declared.party_partition),
    )
    validate_declaration(declaration)
    return declaration


def _party_partition(declared: ManifestPartyPartition | None) -> PartyPartition | None:
    """Return the declared party partition, or ``None`` for the default one.

    The wire format keys the readout maps as nested ``{x: {v: o}}`` tables, the
    way every binary table in the bundle is keyed; the declaration holds them
    flat on ``X x V``. ``None`` in, ``None`` out: an absent record is the
    DEFAULT partition of contract Definition ``def:declaration``, materialized
    on demand by
    :func:`~certiqs_key.meat_core.declaration.declaration.default_party_partition`
    rather than invented here.
    """
    if declared is None:
        return None
    return PartyPartition(
        readout_alice={
            (x, v): value
            for x, row in declared.readout_alice.items()
            for v, value in row.items()
        },
        readout_bob={
            (x, v): value
            for x, row in declared.readout_bob.items()
            for v, value in row.items()
        },
        alphabet_alice=tuple(declared.alphabet_alice),
        alphabet_bob=tuple(declared.alphabet_bob),
        party_of_alice_system=declared.party_of_alice_system,
        party_of_sector_factors={
            sector: tuple(labels)
            for sector, labels in declared.party_of_sector_factors.items()
        },
    )


def _acceptance_set(
    geometry: str, data: dict[str, Any], outcomes: int
) -> AcceptanceSet:
    """Return the declared acceptance set, refusing an unread geometry.

    ``outcomes`` is ``|Chat|``, which a polytope's rows must match column for
    column. See the module docstring for the wire keys and why the schema did
    not have to change to carry them.
    """
    if geometry == POLYTOPE:
        return AcceptanceSet(geometry=geometry, polytope=_polytope(data, outcomes))
    if geometry != SINGLETON:
        raise UnsupportedDeclarationError(
            f"acceptance-set geometry {geometry!r} is not read by this "
            f"implementation; the tags a declaration may use are "
            f"{list(GEOMETRY_TAGS)}, the two instantiations Remark "
            "rem:acc-side certifies; def:admissible-acceptance-set admits any closed "
            "convex "
            "subset of the probability simplex, and a set fitting neither is "
            "refused at admission, before any solve "
            "(req:acceptance-geometries)"
        )
    frequencies = data.get("frequencies")
    if not isinstance(frequencies, list):
        raise DeclarationError(
            "the 'singleton' acceptance set needs a 'frequencies' list in its "
            "data block"
        )
    return AcceptanceSet(
        geometry=geometry, frequencies=_real_vector(frequencies, "acceptance frequency")
    )


def _real_vector(values: Any, what: str) -> tuple[float, ...]:
    """Return a JSON list of numbers as a tuple of machine numbers."""
    if not isinstance(values, list):
        raise DeclarationError(f"{what} data must be a list of real numbers")
    out: list[float] = []
    for entry in values:
        if not isinstance(entry, int | float) or isinstance(entry, bool):
            raise DeclarationError(f"{what} {entry!r} is not a real number")
        out.append(float(entry))
    return tuple(out)


def _polytope(data: dict[str, Any], outcomes: int) -> PolytopeData:
    """Return the ``polytope`` geometry data of ``statistics/def:taxonomy``.

    Shape only. Whether the data is well formed for the form it claims, and
    whether its denotation is empty, are decided by
    :func:`certiqs_key.meat_core.acceptance.geometry.acceptance_verdict` at declaration
    validation -- in that order, which is the whole content of the frozen
    ``ILLFORMED-box-inverted`` case.
    """
    declared_rows = data.get("B")
    if not isinstance(declared_rows, list):
        raise DeclarationError(
            "the 'polytope' acceptance set needs a 'B' list of rows in its data "
            "block (statistics/def:taxonomy)"
        )
    rows = tuple(_real_vector(row, "a row of B") for row in declared_rows)
    rhs = _real_vector(data.get("b"), "b")
    m_row = data.get("m_row")
    if not isinstance(m_row, int) or isinstance(m_row, bool):
        raise DeclarationError(
            "the 'polytope' acceptance set needs an integer 'm_row' row count"
        )
    if m_row != len(rows):
        raise DeclarationError(
            f"the declared m_row is {m_row} but B carries {len(rows)} rows; a "
            "declaration that contradicts itself is refused, not reconciled"
        )
    bounds = data.get("box_bounds")
    box: tuple[tuple[float, ...], tuple[float, ...]] | None = None
    if bounds is not None:
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise DeclarationError(
                "box_bounds is the ordered pair [q^-, q^+] of Eq. eq:boxset"
            )
        box = (
            _real_vector(bounds[0], "q^- of box_bounds"),
            _real_vector(bounds[1], "q^+ of box_bounds"),
        )
    return PolytopeData(columns=outcomes, rows=rows, rhs=rhs, box_bounds=box)
