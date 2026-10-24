"""Structural validation of an operator bundle -- and where it stops.

THE VALIDATION BOUNDARY
=======================

This module carries no claims: ``spec/modules.yaml`` files ``domain`` under
``shared``, the tier of spec/architecture.md 3.3 that "states no mathematics
and carries no claims". It checks that a bundle is **well-formed and
self-consistent as data**, and it deliberately checks nothing that requires
linear algebra or mathematics.

What is checked here
--------------------
* every declared array exists in ``arrays.h5``, exactly once, and no dataset in
  ``arrays.h5`` is unreferenced;
* declared ``dtype``, ``shape`` and ``storage`` match the bytes on disk;
* array shapes match the declared dimensions: operators on ``A`` are
  ``alice_dim`` square, operators on ``Q`` are ``sum(sector_dims)`` square, and
  a sector block is ``sector_dims[s]`` square;
* ``sum(sector_dims) == d_Q``, and ``sector_dims`` is keyed by exactly
  ``sector_index_set``;
* matrices declared square are square;
* every function table is **total** over its declared alphabet, on both
  arguments where it has two, and lands inside its declared codomain;
* ``key_holder`` is in ``{A, B}``; ``alpha`` lies in ``(1, 2)``; ``eps_pa`` and
  ``eps_ev`` lie in ``(0, 1]``; ``lambda_ec`` is a non-negative integer;
  ``rounds >= 1`` (enforced by the manifest models);
* CSC ``indices``/``indptr`` are in range, correctly sized and canonically
  ordered, and ``index_base`` is declared rather than assumed;
* the word "block" carries its kind (spec/architecture.md 2.3), and a
  decomposition indexed by ``sector_index_set`` is a ``proof_sector`` one;
* one space carries one basis label -- a pure string-equality check, not a
  change-of-basis argument;
* where a ``declaration.sector_factorisation`` is present (schema 0.4.0), that
  it refines the
  keys it factorises rather than replacing them: the ``Q`` side flattens to
  ``sector_index_set`` with ``sector_dims`` in that order, the ``A`` side's
  dimensions sum to ``alice_dim``, and the product's own rules -- one block kind,
  at most one ``A`` factor, an ``A`` factor first -- are
  :class:`~certiqs_key.foundations.blocks.FactorisedSectorMap`'s refusals, reached by
  building that type rather than respelled here;
* where a ``reduction_chain`` is present (schema 0.2.0), its shape: link ids
  unique, each link filed under the segment it names, every declared sector
  decomposition summing to the system it decomposes, the last receiver link's
  target agreeing with the declared ``sector_index_set`` and ``sector_dims``,
  the physical half of ``outcome_correspondence`` a stable identifier, and its
  emitted half landing inside the declared Bob alphabet. That is
  spec/architecture.md 3.6's first bullet -- "outcome alphabets, bases,
  subsystem order, and dimensions agree across the compiled maps, the reduction,
  and the statistics" -- at the part of it that is decidable as data.

What is deliberately NOT checked here
-------------------------------------
Positivity of the POVM elements, POVM completeness (that the elements sum to
the identity), Hermiticity, block-diagonality of the Bob POVM elements,
tau_A-homogeneity of the constraint list, convexity or closedness of the
acceptance set, announcement-determined sifting and
holder-computability of the key map (``meat-core`` def:admissible-declaration (v) and
(viii)), the soundness of an ``attack_set_license``, whether a declared
reduction link is a sound reduction at all, and every cross-artifact
agreement that is not decidable from the manifest alone.

All of that is ``meat-core`` bundle validation (spec/architecture.md 3.6),
where "a failure is a hard error, never a warning and never a repair".

The reason for the line is not tidiness. Those checks decide whether a security
proof applies, so they are proof-relevant behaviour; encoding one here would
put it in a module that has no contract, no gates, no verifier rounds and no
tier invariant to hold it.

ONE THING THIS FORMAT DELIBERATELY CANNOT EXPRESS: a
``bob_povm`` element or a constraint operator that is not sector-block-diagonal.
A format able to express the violation would let ``meat-core`` see and reject
it, and spec/architecture.md 2.9 overturns that by a change of premise: an operator IS
its list of
sector blocks, a producer constructs one array per sector, so nothing can write
an off-sector entry and there is no violation of that kind left to see. What a
consumer compares instead is the SECTOR MAP, and a disagreement about what the
sectors are is the failure that can actually arise.

Failures here are hard errors naming the offending key. Nothing warns, repairs
or defaults (spec/architecture.md 2.5, 3.6).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from itertools import product

import numpy as np

from certiqs_key.domain._base import BundleValidationError
from certiqs_key.domain.arrays import (
    ArrayDescriptor,
    ArrayPayload,
    BlockDiagonalOperator,
    DenseArray,
    Dtype,
    SemanticRole,
    SparseCSCArray,
    Storage,
)
from certiqs_key.domain.identifiers import (
    check_alphabet,
    check_identifier,
    check_total_over,
)
from certiqs_key.domain.manifest import (
    Declaration,
    FactorReductionChain,
    MessageRecord,
    OperatorBundleManifest,
    PartyPartition,
    ReductionChain,
    ReductionSegment,
    ReductionSystemDescriptor,
    SectorFactorRecord,
)
from certiqs_key.foundations.blocks import (
    PRODUCT_LABEL_SEPARATOR,
    BlockKind,
    FactorisedSectorMap,
    SectorFactor,
    SectorStructure,
    SystemTag,
    default_factor_label,
)
from certiqs_key.foundations.errors import MalformedInputError

_NUMPY_DTYPE = {Dtype.FLOAT64: np.float64, Dtype.COMPLEX128: np.complex128}

#: Dtype kinds the CSC *index* arrays may have -- ``indices`` and ``indptr``
#: only. Value payloads (``data``, and the ``real``/``imag`` halves of a
#: complex array) are float or complex and are checked against their declared
#: dtype instead.
_INDEX_KINDS = frozenset("iu")


def collect_descriptors(
    manifest: OperatorBundleManifest,
) -> dict[str, tuple[ArrayDescriptor, str]]:
    """Map every dataset path in ``manifest`` to its descriptor and key path.

    Raises:
        BundleValidationError: if two descriptors claim the same dataset path,
            or if one claims a path nested inside another's. Nesting is not a
            near-miss of the duplicate rule but the same defect: each array is
            written as an HDF5 *group* holding its own datasets, so a path
            inside another path is a group inside another array. Depending only
            on which descriptor happens to be written first, that either
            corrupts the outer array's group membership or makes ``h5py``
            refuse to create the group at all -- and the second case escapes as
            a raw library error rather than a bundle error.
    """
    found: dict[str, tuple[ArrayDescriptor, str]] = {}

    def add(descriptor: ArrayDescriptor, where: str) -> None:
        previous = found.get(descriptor.dataset)
        if previous is not None:
            raise BundleValidationError(
                f"{where}: dataset {descriptor.dataset!r} is already claimed by "
                f"{previous[1]}; every array has its own dataset"
            )
        found[descriptor.dataset] = (descriptor, where)

    def add_operator(operator: BlockDiagonalOperator, where: str) -> None:
        # An operator is its list of sector blocks and nothing else
        # (spec/architecture.md 2.9), so there is one form to walk.
        for block_id, block in operator.blocks.items():
            add(block, f"{where}.blocks[{block_id!r}]")

    declaration = manifest.payload.declaration
    if declaration.alice_marginal is not None:
        add(declaration.alice_marginal, "payload.declaration.alice_marginal")
    if declaration.alice_marginal_blocks is not None:
        add_operator(
            declaration.alice_marginal_blocks,
            "payload.declaration.alice_marginal_blocks",
        )
    for outcome, element in declaration.alice_povm.items():
        add(element, f"payload.declaration.alice_povm[{outcome!r}]")
    for field_name in ("alice_povm_blocks", "alice_ensemble"):
        operators = getattr(declaration, field_name)
        if operators is not None:
            for outcome, operator in operators.items():
                add_operator(
                    operator,
                    f"payload.declaration.{field_name}[{outcome!r}]",
                )
    for outcome, operator in declaration.bob_povm.items():
        add_operator(operator, f"payload.declaration.bob_povm[{outcome!r}]")
    if declaration.bob_povm_factors is not None:
        for factor_index, family in enumerate(declaration.bob_povm_factors):
            for outcome, operator in family.members.items():
                add_operator(
                    operator,
                    "payload.declaration.bob_povm_factors"
                    f"[{factor_index}].members[{outcome!r}]",
                )
    for index, constraint in enumerate(declaration.constraint_list):
        base = f"payload.declaration.constraint_list[{index}]"
        add_operator(constraint.operator, f"{base}.operator")
        # A scalar bound (untrusted-source mode) is a JSON number, not an
        # array: there is no dataset to claim.
        if isinstance(constraint.bound, ArrayDescriptor):
            add(constraint.bound, f"{base}.bound")
    for name, array in declaration.acceptance_set.arrays.items():
        add(array, f"payload.declaration.acceptance_set.arrays[{name!r}]")
    _check_no_nested_dataset_paths(found)
    return found


def _check_no_nested_dataset_paths(
    found: Mapping[str, tuple[ArrayDescriptor, str]],
) -> None:
    """Raise if one dataset path lies inside another, in either order.

    The check walks each path's own ancestors rather than comparing sorted
    neighbours, so the result does not depend on the order the descriptors were
    collected in. Sorting is not enough: ``+``, ``-`` and ``.`` are legal in an
    identifier and all sort before ``/``, so a sibling can fall between a path
    and its own child.
    """
    for path, (_, where) in found.items():
        parts = path.split("/")
        for depth in range(2, len(parts)):
            ancestor = "/".join(parts[:depth])
            outer = found.get(ancestor)
            if outer is not None:
                raise BundleValidationError(
                    f"{where}: dataset {path!r} is nested inside {ancestor!r}, "
                    f"claimed by {outer[1]}; every array is its own HDF5 group "
                    "and no array may live inside another"
                )


def validate_manifest(manifest: OperatorBundleManifest) -> None:
    """Check the manifest against itself, without reading ``arrays.h5``.

    Raises:
        BundleValidationError: on the first inconsistency, naming its key.
    """
    payload = manifest.payload
    alphabets = payload.alphabets
    declaration = payload.declaration

    for name in (
        "alice_outcome",
        "acceptance_value",
    ):
        check_alphabet(getattr(alphabets, name), f"payload.alphabets.{name}")
    if declaration.sector_factorisation is None:
        check_alphabet(alphabets.bob_outcome, "payload.alphabets.bob_outcome")
        check_alphabet(
            declaration.sector_index_set,
            "payload.declaration.sector_index_set",
        )
    else:
        _check_distinct_labels(
            alphabets.bob_outcome, "payload.alphabets.bob_outcome"
        )
        _check_distinct_labels(
            declaration.sector_index_set,
            "payload.declaration.sector_index_set",
        )
    if declaration.transcript is None:
        check_alphabet(
            alphabets.alice_announcement,
            "payload.alphabets.alice_announcement",
        )
        check_alphabet(
            alphabets.bob_announcement,
            "payload.alphabets.bob_announcement",
        )
    else:
        if alphabets.alice_announcement or alphabets.bob_announcement:
            raise BundleValidationError(
                "payload.alphabets carries the accepted two-message announcement "
                "alphabets beside declaration.transcript; message alphabets have "
                "one source, the transcript"
            )
        for index, message in enumerate(declaration.transcript):
            check_alphabet(
                message.alphabet,
                f"payload.declaration.transcript[{index}].alphabet",
            )

    check_total_over(
        dict(declaration.sector_dims),
        declaration.sector_index_set,
        "payload.declaration.sector_dims",
    )
    bob_dim = sum(declaration.sector_dims[s] for s in declaration.sector_index_set)

    bases: dict[str, tuple[str, str]] = {}
    alice_dim = declaration.alice_dim

    # The MARGINAL SLOT of contract Definition ``def:declaration``. Absent (or
    # explicit ``null``) is the value ``none``, which Remark ``rem:source-mode``
    # defines to be untrusted-source mode; there is nothing to shape-check then,
    # and nothing that could stand in for it -- ``tau_A = 0`` is inadmissible
    # (``rem:source-mode`` (c)) and is rejected by ``meat-core``'s own
    # def:admissible-declaration (ii) check, not here.
    if declaration.alice_marginal is not None:
        _check_matrix(
            declaration.alice_marginal,
            "payload.declaration.alice_marginal",
            alice_dim,
            SemanticRole.ALICE_MARGINAL,
            "A",
            bases,
        )

    if declaration.alice_povm:
        check_total_over(
            dict(declaration.alice_povm),
            alphabets.alice_outcome,
            "payload.declaration.alice_povm",
        )
        for outcome, element in declaration.alice_povm.items():
            _check_matrix(
                element,
                f"payload.declaration.alice_povm[{outcome!r}]",
                alice_dim,
                SemanticRole.ALICE_POVM_ELEMENT,
                "A",
                bases,
            )
    else:
        alice_blocks = (
            declaration.alice_ensemble
            if declaration.alice_ensemble is not None
            else declaration.alice_povm_blocks
        )
        assert alice_blocks is not None
        check_total_over(
            dict(alice_blocks),
            alphabets.alice_outcome,
            "payload.declaration.alice measurement blocks",
        )

    if declaration.bob_povm_factors is None:
        check_total_over(
            dict(declaration.bob_povm),
            alphabets.bob_outcome,
            "payload.declaration.bob_povm",
        )
        for outcome, operator in declaration.bob_povm.items():
            _check_bob_operator(
                operator,
                f"payload.declaration.bob_povm[{outcome!r}]",
                declaration.sector_index_set,
                declaration.sector_dims,
                SemanticRole.BOB_POVM_ELEMENT,
                bases,
            )
    else:
        _check_factor_families(
            declaration,
            alphabets.bob_outcome,
            bases,
            "payload.declaration.bob_povm_factors",
        )

    # def:admissible-declaration (viii): each party announces a function of its OWN
    # READOUT, so the announcement tables are keyed by the readout alphabets
    # O_A and O_B of the declared party partition. Under the DEFAULT partition
    # (pi_A(x, v) = x, pi_B(x, v) = v) those are X and V, which is the 0.2.x
    # signature verbatim.
    partition = declaration.party_partition
    readout_alice_alphabet = (
        alphabets.alice_outcome if partition is None else partition.alphabet_alice
    )
    readout_bob_alphabet = (
        alphabets.bob_outcome if partition is None else partition.alphabet_bob
    )
    if partition is not None:
        _check_party_partition(
            partition,
            alphabets.alice_outcome,
            alphabets.bob_outcome,
            declaration.sector_index_set,
            "payload.declaration.party_partition",
        )
    if declaration.transcript is None:
        _check_function_table(
            declaration.announce_alice,
            readout_alice_alphabet,
            alphabets.alice_announcement,
            "payload.declaration.announce_alice",
        )
        _check_function_table(
            declaration.announce_bob,
            readout_bob_alphabet,
            alphabets.bob_announcement,
            "payload.declaration.announce_bob",
        )
        _check_binary_table(
            declaration.accept_statistic,
            alphabets.alice_announcement,
            alphabets.bob_announcement,
            alphabets.acceptance_value,
            "payload.declaration.accept_statistic",
        )
    else:
        if declaration.announce_alice or declaration.announce_bob:
            raise BundleValidationError(
                "payload.declaration carries announce_alice or announce_bob "
                "beside transcript; the transcript is the one announcement slot"
            )
        _check_transcript(
            declaration.transcript,
            readout_alice_alphabet,
            readout_bob_alphabet,
            "payload.declaration.transcript",
        )
        _check_general_accept_statistic(
            declaration.accept_statistic_general or (),
            tuple(message.alphabet for message in declaration.transcript),
            alphabets.acceptance_value,
            "payload.declaration.accept_statistic_general",
        )
    _check_key_map(
        declaration.key_map,
        alphabets.alice_outcome,
        alphabets.bob_outcome,
        alphabets.key_value_count,
        "payload.declaration.key_map",
    )

    for index, constraint in enumerate(declaration.constraint_list):
        base = f"payload.declaration.constraint_list[{index}]"
        entry_sectors = declaration.sector_index_set
        entry_dims: Mapping[str, int] = declaration.sector_dims
        entry_space = "Q"
        if constraint.scope is not None:
            if declaration.sector_factorisation is None:
                raise BundleValidationError(
                    f"{base}.scope: names {constraint.scope!r}, but the bundle "
                    "declares no measured-factor list"
                )
            measured = tuple(
                factor
                for factor in declaration.sector_factorisation
                if factor.system is SystemTag.Q
            )
            labels = tuple(
                factor.label or f"f{position}"
                for position, factor in enumerate(measured)
            )
            if constraint.scope not in labels:
                raise BundleValidationError(
                    f"{base}.scope: {constraint.scope!r} names no measured "
                    f"factor in {list(labels)}"
                )
            factor_position = labels.index(constraint.scope)
            factor = measured[factor_position]
            entry_sectors = tuple(label for label, _ in factor.sectors)
            entry_dims = dict(factor.sectors)
            entry_space = f"Q.factor[{factor_position}]"
        _check_bob_operator(
            constraint.operator,
            f"{base}.operator",
            entry_sectors,
            entry_dims,
            SemanticRole.CONSTRAINT_OPERATOR,
            bases,
            space_prefix=entry_space,
        )
        # Theta_k is typed by the declared source mode (def:admissible-declaration
        # (vi)): a Hermitian operator on A, or a real scalar c_k. Only the
        # operator spelling has a shape to check here; WHICH spelling this
        # declaration is entitled to is a mathematical question and belongs to
        # meat-core, not to the format.
        if isinstance(constraint.bound, ArrayDescriptor):
            _check_matrix(
                constraint.bound,
                f"{base}.bound",
                alice_dim,
                SemanticRole.CONSTRAINT_BOUND,
                "A",
                bases,
            )
        elif not math.isfinite(constraint.bound):
            raise BundleValidationError(
                f"{base}.bound: a scalar bound is a real number c_k; "
                f"{constraint.bound!r} is not finite"
            )

    license_record = declaration.attack_set_license
    if license_record is not None and not license_record:
        raise BundleValidationError(
            "payload.declaration.attack_set_license: present but empty; a "
            "license names a supplier certificate, and an empty record names "
            "nothing. Omit it (null) to leave the constrained branch disabled"
        )
    source_record = declaration.source_replacement_license
    if source_record is not None and not source_record:
        raise BundleValidationError(
            "payload.declaration.source_replacement_license: present but "
            "empty; the A-SRC attestation names a supplier certificate, and an "
            "empty record names nothing. Omit it (null) -- the sound "
            "declaration without it is untrusted-source mode"
        )

    for name, array in declaration.acceptance_set.arrays.items():
        where = f"payload.declaration.acceptance_set.arrays[{name!r}]"
        if array.semantic_role is not SemanticRole.ACCEPTANCE_SET_DATUM:
            raise BundleValidationError(
                f"{where}: semantic_role is {array.semantic_role.value!r}, "
                f"expected {SemanticRole.ACCEPTANCE_SET_DATUM.value!r}"
            )

    # THE KEY IS A DECLARATION SLOT, not a payload one (def:declaration (DX1);
    # spec/architecture.md 4.1).
    if declaration.sector_factorisation is not None:
        _check_sector_factorisation(
            declaration.sector_factorisation,
            declaration=declaration,
            where="payload.declaration.sector_factorisation",
        )

    if payload.reduction_chain is not None:
        if isinstance(payload.reduction_chain, FactorReductionChain):
            _check_factor_reduction_chain(
                payload.reduction_chain,
                declaration=declaration,
                where="payload.reduction_chain",
            )
        else:
            _check_reduction_chain(
                payload.reduction_chain,
                sector_index_set=declaration.sector_index_set,
                sector_dims=declaration.sector_dims,
                bob_dim=bob_dim,
                bob_outcome=alphabets.bob_outcome,
                where="payload.reduction_chain",
            )


def validate_bundle(
    manifest: OperatorBundleManifest, arrays: Mapping[str, ArrayPayload]
) -> None:
    """Validate the manifest and the arrays it points at, together.

    Raises:
        BundleValidationError: on the first inconsistency, naming its key.
    """
    validate_manifest(manifest)
    descriptors = collect_descriptors(manifest)

    missing = sorted(set(descriptors) - set(arrays))
    if missing:
        raise BundleValidationError(
            f"arrays.h5 is missing datasets declared in manifest.json: {missing}"
        )
    unreferenced = sorted(set(arrays) - set(descriptors))
    if unreferenced:
        raise BundleValidationError(
            f"arrays.h5 holds datasets no descriptor claims: {unreferenced}; "
            "an unreferenced array has no declared meaning"
        )

    for dataset, (descriptor, where) in descriptors.items():
        _check_payload(descriptor, arrays[dataset], where)


def _check_matrix(
    descriptor: ArrayDescriptor,
    where: str,
    dimension: int,
    role: SemanticRole,
    space: str,
    bases: dict[str, tuple[str, str]],
) -> None:
    """Check one square operator descriptor against a declared dimension."""
    if descriptor.semantic_role is not role:
        raise BundleValidationError(
            f"{where}: semantic_role is {descriptor.semantic_role.value!r}, "
            f"expected {role.value!r}"
        )
    if len(descriptor.shape) != 2 or descriptor.shape[0] != descriptor.shape[1]:
        raise BundleValidationError(
            f"{where}: shape {list(descriptor.shape)} is not square, but "
            f"{role.value!r} is an operator"
        )
    if descriptor.shape[0] != dimension:
        raise BundleValidationError(
            f"{where}: shape {list(descriptor.shape)} does not match the "
            f"declared dimension {dimension} of space {space!r}"
        )
    _register_basis(descriptor.basis, where, space, bases)


def _register_basis(
    basis: str, where: str, space: str, bases: dict[str, tuple[str, str]]
) -> None:
    """Require one basis label per space, by string equality only."""
    previous = bases.get(space)
    if previous is None:
        bases[space] = (basis, where)
    elif previous[0] != basis:
        raise BundleValidationError(
            f"{where}: basis {basis!r} on space {space!r} disagrees with "
            f"{previous[0]!r} declared at {previous[1]}; one space carries one "
            "basis label"
        )


def _check_bob_operator(
    operator: BlockDiagonalOperator,
    where: str,
    sector_index_set: tuple[str, ...],
    sector_dims: Mapping[str, int],
    role: SemanticRole,
    bases: dict[str, tuple[str, str]],
    *,
    space_prefix: str = "Q",
) -> None:
    """Check an operator on Bob's system: its sector map, then its blocks.

    There is one form (spec/architecture.md 2.9). The full-space branch this
    function used
    to open with -- one ``d_Q x d_Q`` matrix, checked against ``bob_dim`` --
    went with the union, and with it the only place in this module that would
    have materialized a full-space shape.
    """
    if operator.block_kind is not BlockKind.PROOF_SECTOR:
        raise BundleValidationError(
            f"{where}: block_kind is {operator.block_kind.value!r}, but a "
            "decomposition indexed by sector_index_set is a "
            f"{BlockKind.PROOF_SECTOR.value!r} one (spec/architecture.md 2.3)"
        )
    check_total_over(dict(operator.blocks), sector_index_set, f"{where}.blocks")
    for sector, block in operator.blocks.items():
        _check_matrix(
            block,
            f"{where}.blocks[{sector!r}]",
            sector_dims[sector],
            role,
            f"{space_prefix}[{sector}]",
            bases,
        )


def _check_party_partition(
    partition: PartyPartition,
    alice_outcome: tuple[str, ...],
    bob_outcome: tuple[str, ...],
    sector_index_set: tuple[str, ...],
    where: str,
) -> None:
    """Check the party partition ``P`` of contract Def. ``def:declaration``.

    Part (a), the readout maps, is checked as data: both are TOTAL on
    ``X x V`` and land in their declared alphabets, which is what makes
    "a function of its own readout" (def:admissible-declaration (viii)) a statement
    about a table rather than an aspiration. Part (b) is checked for coverage
    only -- one entry per declared sector, at least one labelled factor each --
    because it carries a ``protocol-compiler`` obligation that ``meat-core``
    never verifies.
    """
    check_alphabet(partition.alphabet_alice, f"{where}.alphabet_alice")
    check_alphabet(partition.alphabet_bob, f"{where}.alphabet_bob")
    _check_binary_table(
        partition.readout_alice,
        alice_outcome,
        bob_outcome,
        partition.alphabet_alice,
        f"{where}.readout_alice",
    )
    _check_binary_table(
        partition.readout_bob,
        alice_outcome,
        bob_outcome,
        partition.alphabet_bob,
        f"{where}.readout_bob",
    )
    check_total_over(
        dict(partition.party_of_sector_factors),
        sector_index_set,
        f"{where}.party_of_sector_factors",
    )
    for sector, labels in partition.party_of_sector_factors.items():
        if not labels:
            raise BundleValidationError(
                f"{where}.party_of_sector_factors[{sector!r}]: a declared "
                "tensor factorization of H(Q_s) has at least one factor, and "
                "each factor carries a party label"
            )


def _check_sector_factorisation(
    factorisation: tuple[SectorFactorRecord, ...],
    *,
    declaration: Declaration,
    where: str,
) -> None:
    """Check a declared factorisation against the keys it refines (2.9).

    THE PRODUCT RULES ARE NOT RESPELLED HERE. One block kind, at most one ``A``
    factor and an ``A`` factor first are
    :class:`~certiqs_key.foundations.blocks.FactorisedSectorMap`'s own refusals, so
    this function BUILDS that type from the records and lets it refuse; a second
    spelling of a rule is a second rule as soon as one of them is edited. What
    is checked here is the part only the manifest knows: that the ``Q`` side
    flattens to the declaration's own ``sector_index_set`` and ``sector_dims``,
    in that order, and that the ``A`` side's dimensions sum to ``alice_dim``.
    Neither key is superseded by the factorisation -- it says how the same map
    factorises -- so a disagreement is a refusal and never a reconciliation.

    Building the type needs the ONE block kind the factors carry, which is the
    declaration's ``sector_block_kind``. That key is a free string elsewhere in
    this format, deliberately ("this format carries the declared string and
    decides nothing about what it MEANS"); a FACTORISED declaration is the one
    place it must name a member of the shared vocabulary, because the one-kind
    rule it rests on is stated over that vocabulary. A 0.3.0 bundle is untouched
    by this: it declares no factorisation.
    """
    declared_kind = _block_kind_of(declaration.sector_block_kind, where)
    factors: list[SectorFactor] = []
    for index, record in enumerate(factorisation):
        labels = tuple(label for label, _ in record.sectors)
        check_alphabet(labels, f"{where}[{index}].sectors")
        factors.append(
            SectorFactor(
                party=record.party,
                sectors=SectorStructure(
                    labels=labels,
                    dims=tuple(dim for _, dim in record.sectors),
                    block_kind=declared_kind,
                ),
                system=record.system,
                # ABSENT IS THE POSITION DEFAULT and is filled by the shared type,
                # not here: one home for one rule, as with the product's refusals.
                label=record.label or "",
            )
        )
    try:
        product = FactorisedSectorMap(factors=tuple(factors))
    except MalformedInputError as error:
        raise BundleValidationError(f"{where}: {error}") from error

    declared = tuple(
        (sector, declaration.sector_dims[sector])
        for sector in declaration.sector_index_set
    )
    measured = product.flattened_of(SystemTag.Q)
    if measured is None or measured.entries != declared:
        found = "no Q factor at all" if measured is None else list(measured.entries)
        raise BundleValidationError(
            f"{where}: the Q side of the product flattens to {found}, not to "
            f"the declaration's {list(declared)}, in that order; the "
            "factorisation says how the DECLARED map factorises and does not "
            "replace it"
        )
    retained = product.flattened_of(SystemTag.A)
    if retained is not None and retained.total_dim != declaration.alice_dim:
        raise BundleValidationError(
            f"{where}: the A side's dimensions sum to {retained.total_dim}, not "
            f"to the declared alice_dim {declaration.alice_dim}; a "
            "decomposition that does not decompose its own system is refused "
            "rather than reconciled"
        )
    _check_retained_party(
        product.factors_of(SystemTag.A),
        partition=declaration.party_partition,
        where=where,
    )


def _check_retained_party(
    retained: tuple[SectorFactor, ...],
    *,
    partition: PartyPartition | None,
    where: str,
) -> None:
    """Refuse an ``A`` factor scoped to a party other than ``A``'s holder.

    The declaration says WHO HOLDS ``A`` in one place already --
    ``party_partition.party_of_alice_system`` -- and the ``A`` factor of the
    factorisation says it in another. Two keys for one fact is exactly the
    "second source of truth" this format refuses elsewhere, so where both are
    present they are compared and a disagreement is a hard error. Where the
    partition is ABSENT nothing is compared: absence spells the DEFAULT
    partition, and the default's reading of a factorised map is not something
    this format may settle on the producer's behalf.

    ``party_of_sector_factors`` is NOT read here. It labels the tensor factors
    INSIDE each ``H(Q_s)``; a factor of this product is a factor of the sector
    map. The key's own comment says why the two are not cross-checked.
    """
    if partition is None or not retained:
        return
    (factor,) = retained
    declared = partition.party_of_alice_system.value
    if factor.party != declared:
        raise BundleValidationError(
            f"{where}: the {SystemTag.A.value!r} factor is scoped to party "
            f"{factor.party!r}, but the declared party partition gives A to "
            f"party {declared!r} (party_of_alice_system). Who holds the "
            "retained system is one fact, and this format carries no second "
            "answer to it"
        )


def _block_kind_of(declared: str, where: str) -> BlockKind:
    """Return the declared block kind as a member, or refuse the document."""
    try:
        return BlockKind(declared)
    except ValueError as error:
        raise BundleValidationError(
            f"{where}: the declaration's sector_block_kind {declared!r} is not "
            f"one of {[kind.value for kind in BlockKind]}, and a factorised "
            "sector map is read against the one block kind its factors carry "
            "(spec/architecture.md 2.9). Nothing here maps it onto a nearest "
            "member"
        ) from error


def _check_reduction_chain(
    chain: ReductionChain,
    *,
    sector_index_set: tuple[str, ...],
    sector_dims: Mapping[str, int],
    bob_dim: int,
    bob_outcome: tuple[str, ...],
    where: str,
) -> None:
    """Check a declared reduction chain as data (spec/architecture.md 3.6).

    Every failure below is a hard error naming its key, never a warning and
    never a repair. What is checked is the part of 3.6's first bullet that a
    manifest decides on its own: the chain's own internal consistency, and the
    agreement of its last receiver link with the declaration built from it.
    Whether the link is a SOUND reduction is not asked here and is not this
    format's to ask -- exactly as with ``acceptance_set``.

    The status vocabulary, a non-empty ``receiver_segment`` and positive
    descriptor dimensions are enforced by the model itself, at parse time; they
    are named in the module docstring alongside these because they are part of
    the same check and a reader should not have to find out where each half
    lives.
    """
    seen: dict[str, str] = {}
    for segment, links in (
        (ReductionSegment.SOURCE, chain.source_segment),
        (ReductionSegment.RECEIVER, chain.receiver_segment),
    ):
        for index, link in enumerate(links):
            slot = f"{where}.{segment.value}_segment[{index}]"
            if link.segment is not segment:
                raise BundleValidationError(
                    f"{slot}: the link declares segment "
                    f"{link.segment.value!r} but is filed under "
                    f"{segment.value!r}; composition order is data and a link "
                    "filed in the wrong segment silently reorders the chain"
                )
            previous = seen.get(link.link_id)
            if previous is not None:
                raise BundleValidationError(
                    f"{slot}: link_id {link.link_id!r} is already used by "
                    f"{previous}; a link id names one link"
                )
            seen[link.link_id] = slot
            _check_reduction_descriptor(
                link.source_descriptor, f"{slot}.source_descriptor"
            )
            _check_reduction_descriptor(
                link.target_descriptor, f"{slot}.target_descriptor"
            )

    last = chain.receiver_segment[-1]
    target = last.target_descriptor
    slot = f"{where}.receiver_segment[{len(chain.receiver_segment) - 1}]"
    if target.dim != bob_dim:
        raise BundleValidationError(
            f"{slot}.target_descriptor: dim {target.dim} does not match the "
            f"declared receiver dimension {bob_dim} = sum(sector_dims); the "
            "emitted receiver system IS the last link's target"
        )
    if target.sectors is not None:
        declared = tuple((s, sector_dims[s]) for s in sector_index_set)
        if tuple(target.sectors) != declared:
            raise BundleValidationError(
                f"{slot}.target_descriptor: the declared sector decomposition "
                f"{list(target.sectors)} does not match the declaration's "
                f"{list(declared)}, in that order"
            )

    emitted = set(bob_outcome)
    physical: set[str] = set()
    for index, (source, image) in enumerate(chain.outcome_correspondence):
        slot = f"{where}.outcome_correspondence[{index}]"
        # THE PHYSICAL HALF IS AN IDENTIFIER TOO, and it has to be checked here
        # rather than left to a type annotation. The emitted half is checked by
        # membership in the declared Bob alphabet, which `check_alphabet`
        # already put through the identifier pattern; the physical half is in
        # NO declared alphabet -- V^ph is the reduction's own input alphabet and
        # this format does not carry it -- so nothing else would ever look at
        # it. The published schema types both halves as `$defs/identifier`, and
        # a reader looser than its own schema would accept bundles the schema
        # rejects.
        check_identifier(source, f"{slot} (physical outcome)")
        if source in physical:
            raise BundleValidationError(
                f"{slot}: the physical outcome {source!r} already has an image; "
                "the correspondence is a function on the physical alphabet"
            )
        physical.add(source)
        if image not in emitted:
            raise BundleValidationError(
                f"{slot}: the emitted outcome {image!r} is not in the declared "
                f"Bob alphabet {sorted(emitted)}"
            )


def _check_factor_reduction_chain(
    chain: FactorReductionChain,
    *,
    declaration: Declaration,
    where: str,
) -> None:
    """Check each receiver segment against its corresponding measured factor."""
    factorisation = declaration.sector_factorisation
    families = declaration.bob_povm_factors
    if factorisation is None or families is None:
        raise BundleValidationError(
            f"{where}: a factor reduction chain requires the declaration's "
            "sector_factorisation and bob_povm_factors"
        )
    measured = tuple(factor for factor in factorisation if factor.system is SystemTag.Q)
    rows = chain.receiver_factor_segments
    if len(rows) != len(measured) or len(rows) != len(families):
        raise BundleValidationError(
            f"{where}.receiver_factor_segments: carries {len(rows)} rows for "
            f"{len(measured)} measured sector factors and {len(families)} families"
        )
    for index, (row, factor, family) in enumerate(
        zip(rows, measured, families, strict=True)
    ):
        slot = f"{where}.receiver_factor_segments[{index}]"
        expected_label = (
            factor.label if factor.label is not None else default_factor_label(index)
        )
        if row.factor_label != expected_label:
            raise BundleValidationError(
                f"{slot}.factor_label: {row.factor_label!r} does not match the "
                f"corresponding measured factor label {expected_label!r}"
            )
        if row.party != factor.party or row.party != family.party:
            raise BundleValidationError(
                f"{slot}.party: {row.party!r} does not match the corresponding "
                f"sector factor/family parties {factor.party!r}/{family.party!r}"
            )
        local = ReductionChain(
            source_segment=chain.source_segment if index == 0 else (),
            receiver_segment=row.receiver_segment,
            outcome_correspondence=row.outcome_correspondence,
        )
        local_dims = dict(factor.sectors)
        _check_reduction_chain(
            local,
            sector_index_set=tuple(local_dims),
            sector_dims=local_dims,
            bob_dim=sum(local_dims.values()),
            bob_outcome=family.alphabet,
            where=slot,
        )


def _check_reduction_descriptor(
    descriptor: ReductionSystemDescriptor, where: str
) -> None:
    """Check one system descriptor's declared decomposition against its dimension."""
    if descriptor.sectors is None:
        return
    labels = tuple(label for label, _ in descriptor.sectors)
    check_alphabet(labels, f"{where}.sectors")
    total = sum(dim for _, dim in descriptor.sectors)
    if total != descriptor.dim:
        raise BundleValidationError(
            f"{where}: the declared sector dimensions sum to {total}, not to "
            f"the system dimension {descriptor.dim}; a decomposition that does "
            "not decompose its own system is refused rather than reconciled"
        )


def _check_function_table(
    table: Mapping[str, str],
    domain: tuple[str, ...],
    codomain: tuple[str, ...],
    where: str,
) -> None:
    """Check a one-argument function table for totality and codomain."""
    check_total_over(dict(table), domain, where)
    allowed = set(codomain)
    for key, value in table.items():
        if value not in allowed:
            raise BundleValidationError(
                f"{where}[{key!r}]: value {value!r} is not in the declared "
                f"codomain {sorted(allowed)}"
            )


def _check_distinct_labels(labels: tuple[str, ...], where: str) -> None:
    """Check a derived product alphabet without treating its join as an ID.

    The components are stable identifiers and are checked at their factor;
    their product spelling contains the declared separator by construction.
    """
    if not labels:
        raise BundleValidationError(f"{where}: an alphabet is non-empty")
    if len(set(labels)) != len(labels):
        raise BundleValidationError(f"{where}: labels are not pairwise distinct")


def _check_general_accept_statistic(
    table: tuple[tuple[tuple[str, ...], str], ...],
    alphabets: tuple[tuple[str, ...], ...],
    codomain: tuple[str, ...],
    where: str,
) -> None:
    """Check ``phi`` on the derived transcript product alphabet."""
    expected = tuple(product(*alphabets))
    found: dict[tuple[str, ...], str] = {}
    allowed = set(codomain)
    for index, (key, value) in enumerate(table):
        if key in found:
            raise BundleValidationError(
                f"{where}[{index}]: transcript class {key!r} is repeated"
            )
        if len(key) != len(alphabets):
            raise BundleValidationError(
                f"{where}[{index}]: transcript class {key!r} has {len(key)} "
                f"components, not the declared message count {len(alphabets)}"
            )
        if value not in allowed:
            raise BundleValidationError(
                f"{where}[{index}]: value {value!r} is outside the declared "
                f"codomain {sorted(allowed)}"
            )
        found[key] = value
    if tuple(found) != expected:
        raise BundleValidationError(
            f"{where}: keys are {list(found)}, not the derived transcript "
            f"alphabet {list(expected)} in its declared product order"
        )


def _check_transcript(
    messages: tuple[MessageRecord, ...],
    alice_readouts: tuple[str, ...],
    bob_readouts: tuple[str, ...],
    where: str,
) -> None:
    """Check each message table over its sender and earlier messages."""
    prefixes: tuple[tuple[str, ...], ...] = ((),)
    for index, message in enumerate(messages):
        sender = message.sender
        alphabet = message.alphabet
        table = message.table
        readouts = alice_readouts if str(sender) == "A" else bob_readouts
        expected = tuple(
            (readout, prefix) for readout in readouts for prefix in prefixes
        )
        found: dict[tuple[str, tuple[str, ...]], str] = {}
        allowed = set(alphabet)
        for cell_index, (readout, prefix, value) in enumerate(table):
            cell = (readout, prefix)
            if cell in found:
                raise BundleValidationError(
                    f"{where}[{index}].table[{cell_index}]: cell {cell!r} is repeated"
                )
            if value not in allowed:
                raise BundleValidationError(
                    f"{where}[{index}].table[{cell_index}]: value {value!r} is "
                    f"outside the message alphabet {sorted(allowed)}"
                )
            found[cell] = value
        if tuple(found) != expected:
            raise BundleValidationError(
                f"{where}[{index}].table: cells are {list(found)}, not the "
                f"declared signature {list(expected)} in its product order"
            )
        prefixes = tuple((*prefix, value) for prefix in prefixes for value in alphabet)


def _check_factor_families(
    declaration: Declaration,
    bob_outcome: tuple[str, ...],
    bases: dict[str, tuple[str, str]],
    where: str,
) -> None:
    """Check per-factor families and their derived product alphabet."""
    assert declaration.bob_povm_factors is not None
    assert declaration.sector_factorisation is not None
    q_factors = tuple(
        factor
        for factor in declaration.sector_factorisation
        if factor.system is SystemTag.Q
    )
    families = declaration.bob_povm_factors
    if len(families) != len(q_factors):
        raise BundleValidationError(
            f"{where}: carries {len(families)} families for {len(q_factors)} "
            "declared measured factors"
        )
    for index, (family, factor) in enumerate(zip(families, q_factors, strict=True)):
        check_alphabet(family.alphabet, f"{where}[{index}].alphabet")
        check_total_over(
            dict(family.members), family.alphabet, f"{where}[{index}].members"
        )
        sectors = tuple(label for label, _ in factor.sectors)
        dims = dict(factor.sectors)
        for outcome, operator in family.members.items():
            _check_bob_operator(
                operator,
                f"{where}[{index}].members[{outcome!r}]",
                sectors,
                dims,
                SemanticRole.BOB_POVM_ELEMENT,
                bases,
                space_prefix=f"Q.factor[{index}]",
            )
    expected = tuple(
        PRODUCT_LABEL_SEPARATOR.join(letters)
        for letters in product(*(family.alphabet for family in families))
    )
    if bob_outcome != expected:
        raise BundleValidationError(
            f"payload.alphabets.bob_outcome is {list(bob_outcome)}, not the "
            f"derived factor product {list(expected)}"
        )


def _check_binary_table(
    table: Mapping[str, Mapping[str, str]],
    first: tuple[str, ...],
    second: tuple[str, ...],
    codomain: tuple[str, ...],
    where: str,
) -> None:
    """Check a two-argument function table for totality and codomain."""
    check_total_over(dict(table), first, where)
    for key, row in table.items():
        _check_function_table(row, second, codomain, f"{where}[{key!r}]")


def _check_key_map(
    table: Mapping[str, Mapping[str, int | None]],
    first: tuple[str, ...],
    second: tuple[str, ...],
    key_value_count: int,
    where: str,
) -> None:
    """Check the raw-key map for totality and key-alphabet range.

    ``None`` encodes the discard symbol of the ``meat-core`` Section 2.1 key alphabet
    ``Z = {0, ..., d_Z - 1}`` disjoint-union ``{perp}``. That the discard
    pattern is announcement-determined is def:admissible-declaration (v) and belongs to
    ``meat-core``; it is not checked here.
    """
    check_total_over(dict(table), first, where)
    for key, row in table.items():
        row_where = f"{where}[{key!r}]"
        check_total_over(dict(row), second, row_where)
        for inner, value in row.items():
            if value is None:
                continue
            if not 0 <= value < key_value_count:
                raise BundleValidationError(
                    f"{row_where}[{inner!r}]: key value {value} is outside "
                    f"{{0, ..., {key_value_count - 1}}}; use null for the "
                    "discard symbol"
                )


def _check_payload(
    descriptor: ArrayDescriptor, payload: ArrayPayload, where: str
) -> None:
    """Check one array's bytes against what its descriptor declares."""
    expected_dtype = np.dtype(_NUMPY_DTYPE[descriptor.dtype])
    if descriptor.storage is Storage.DENSE:
        if not isinstance(payload, DenseArray):
            raise BundleValidationError(
                f"{where}: storage is 'dense' but the payload is CSC"
            )
        if payload.values.dtype != expected_dtype:
            raise BundleValidationError(
                f"{where}: dtype on disk is {payload.values.dtype}, declared "
                f"{descriptor.dtype.value}"
            )
        if tuple(payload.values.shape) != tuple(descriptor.shape):
            raise BundleValidationError(
                f"{where}: shape on disk is {list(payload.values.shape)}, "
                f"declared {list(descriptor.shape)}"
            )
        return

    if not isinstance(payload, SparseCSCArray):
        raise BundleValidationError(
            f"{where}: storage is 'sparse_csc' but the payload is dense"
        )
    if payload.data.dtype != expected_dtype:
        raise BundleValidationError(
            f"{where}: dtype on disk is {payload.data.dtype}, declared "
            f"{descriptor.dtype.value}"
        )
    if payload.shape != tuple(descriptor.shape):
        raise BundleValidationError(
            f"{where}: CSC shape on disk is {list(payload.shape)}, declared "
            f"{list(descriptor.shape)}"
        )
    _check_csc(payload, descriptor, where)


def _check_csc(
    payload: SparseCSCArray, descriptor: ArrayDescriptor, where: str
) -> None:
    """Check that a CSC payload is canonical and in range."""
    if descriptor.index_base is None:  # pragma: no cover - the model guarantees it
        raise BundleValidationError(f"{where}: sparse_csc without an index_base")
    base = descriptor.index_base
    rows, cols = payload.shape
    # Dimensionality and index dtype are checked here as well as on the read
    # path, so that both ends of the round trip accept the same set. A payload
    # this function passes and the reader then refuses is a defect either way,
    # but it is a worse one at write time: it produces a file.
    for name, component in (
        ("data", payload.data),
        ("indices", payload.indices),
        ("indptr", payload.indptr),
    ):
        if component.ndim != 1:
            raise BundleValidationError(
                f"{where}: CSC {name!r} is {component.ndim}-D, expected 1-D; "
                "canonical CSC stores three flat arrays"
            )
    for name, component in (("indices", payload.indices), ("indptr", payload.indptr)):
        if component.dtype.kind not in _INDEX_KINDS:
            raise BundleValidationError(
                f"{where}: CSC {name!r} has dtype {component.dtype}, expected an "
                "integer dtype; a float index would be truncated on the way to "
                "disk, and nothing here repairs silently"
            )
    if payload.indices.shape != payload.data.shape:
        raise BundleValidationError(
            f"{where}: indices has {payload.indices.size} entries but data has "
            f"{payload.data.size}"
        )
    if payload.indptr.size != cols + 1:
        raise BundleValidationError(
            f"{where}: indptr has {payload.indptr.size} entries, expected "
            f"{cols + 1} for {cols} columns"
        )
    indptr = payload.indptr.astype(np.int64) - base
    if int(indptr[0]) != 0:
        raise BundleValidationError(
            f"{where}: indptr[0] is {int(payload.indptr[0])}, expected the "
            f"declared index_base {base}"
        )
    if int(indptr[-1]) != payload.data.size:
        raise BundleValidationError(
            f"{where}: indptr[-1] is {int(payload.indptr[-1])}, expected "
            f"{base} + nnz = {base + payload.data.size}"
        )
    if bool(np.any(np.diff(indptr) < 0)):
        raise BundleValidationError(f"{where}: indptr is not non-decreasing")
    indices = payload.indices.astype(np.int64) - base
    if payload.data.size and (int(indices.min()) < 0 or int(indices.max()) >= rows):
        raise BundleValidationError(
            f"{where}: a row index is outside [{base}, {base + rows}) for a "
            f"{rows}-row array"
        )
    for column in range(cols):
        start, stop = int(indptr[column]), int(indptr[column + 1])
        column_indices = indices[start:stop]
        if column_indices.size > 1 and bool(np.any(np.diff(column_indices) <= 0)):
            raise BundleValidationError(
                f"{where}: column {column} row indices are not strictly "
                "increasing; canonical CSC has sorted, duplicate-free columns"
            )
