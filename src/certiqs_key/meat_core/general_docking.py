"""THE ONE DOCKING MODULE for the general format's wire keys.

``interface.yaml``'s ``general_format_note`` lists the keys the general format
adds to the compiler's emitted ``declaration``, and this module is the only
place in the engine that reads them. Everything below it consumes
:class:`~certiqs_key.meat_core.declaration.general.GeneralDeclaration`, an
engine-local type, so when the wire keys land in ``domain/`` and
``protocol_compiler/`` exactly one function changes:
:func:`dock_general_declaration`.

THE KEYS, AS THE COMPILER EMITS THEM
====================================
:data:`WIRE_KEYS` names each one with what this module needs from it. They are
the compiler's spellings and not this module's (the general-format input rows of
``interface.yaml``: "The keys and their spellings are the compiler's"), and
their ABSENCE IS TODAY'S FORMAT -- one Alice sector, one measured factor, POVM
form, two independent messages, no party-local entry -- which is why a
declaration carrying none of them docks through
:func:`~certiqs_key.meat_core.declaration.general.general_from_accepted` and is
routed to the accepted code path unchanged.

WHY THE ENGINE-LOCAL TYPES EXIST AT ALL
=======================================
``foundations/blocks.py`` and ``domain/families.py`` today offer
``FactorisedSectorMap``, ``SectorFactor``, ``JointBlockOperator`` with its
``alice_sectors`` and ``FactorisedFamily``, all of them in EXACT arithmetic on
tuple matrices -- the admission boundary's substrate. The engine computes in
binary64 numpy arrays, so it needs the same
structures over its own matrix type; the engine-local types under
``meat_core/declaration/general.py`` are that, and they are deliberately a
reading of the shared shapes rather than a second declaration of them: one
``A`` factor and it comes first, at least one ``Q`` factor, one block kind, the
product order with the last factor fastest, and a product identifier joined by
the one declared separator, which this module imports from
``foundations/blocks.py`` rather than spelling again.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import TYPE_CHECKING

import numpy as np

from certiqs_key.domain.manifest import KeyHolder, PartyLabel
from certiqs_key.foundations.blocks import BlockOperator
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.declaration.general import (
    AliceFactor,
    AliceForm,
    GeneralConstraintEntry,
    GeneralDeclaration,
    GeneralRhsTag,
    MeasuredFactor,
    Message,
    SectorAxis,
    Transcript,
    general_from_accepted,
    two_message_transcript,
)
from certiqs_key.meat_core.declaration.general_validation import (
    validate_general_declaration,
)
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.linalg import Matrix

if TYPE_CHECKING:
    from certiqs_key.meat_core.declaration.declaration import (
        AcceptanceSet,
        KeyLengthParameters,
    )
    from certiqs_key.protocol_compiler.declaration import CandidateDeclaration

#: What each general-format wire key supplies, in the compiler's spelling. THE
#: LIST A MERGE READS: every entry names the key, the engine-local slot it
#: fills, and what the engine does with it.
WIRE_KEYS: Mapping[str, str] = {
    "sector_factorisation": (
        "the ordered factor list of (DX1): per factor a system tag A or Q, a "
        "party label and that factor's own sector map (labels with dimensions). "
        "Fills GeneralDeclaration.alice (the factor tagged A, at most one and "
        "first) and .factors (those tagged Q, in the declared order). The "
        "product sector map, the product alphabet and the joint sectors are "
        "DERIVED here and are not read."
    ),
    "alice_form": (
        "`povm` or `ensemble`, which of the two slots of (DX4) is filled. Fills "
        "GeneralDeclaration.alice_form; absent is `povm`."
    ),
    "alice_ensemble": (
        "the block lists N_x^(t) along T, present exactly in ensemble form and "
        "in place of `alice_povm`. Fills GeneralDeclaration.alice_operators, "
        "which the objective reads through lem:choi-factor (iv) at every rank."
    ),
    "alice_povm_blocks": (
        "in the general format, M_x as a BLOCK LIST along T rather than one "
        "array. Fills GeneralDeclaration.alice_operators in POVM form."
    ),
    "alice_marginal_blocks": (
        "in the general format, tau_A as the block list tau_A^(t) of (DX2). "
        "Fills GeneralDeclaration.alice_marginal; its absence is "
        "untrusted-source mode, as today."
    ),
    "bob_povm_factors": (
        "one family of block lists per measured factor, against that factor's "
        "own map and over its own ordered alphabet, plus the product rule. "
        "Fills MeasuredFactor.blocks and .alphabet. NO PRODUCT DATUM IS READ: "
        "the Kronecker block is formed inside the objective."
    ),
    "transcript": (
        "the ordered message list ((pi_m, C_m, a_m))_{m=1..L} of (DX5). Fills "
        "GeneralDeclaration.transcript; L = 2 is the pair `announce_alice`, "
        "`announce_bob`, and the joint announcement function is DERIVED."
    ),
    "constraint_list[].scope": (
        "per entry, the label of the measured factor the entry is scoped to. "
        "Fills GeneralConstraintEntry.scope."
    ),
    "constraint_rhs_tag": (
        "per entry, `homogeneous`, `general` or `party_local`. Fills "
        "GeneralConstraintEntry.rhs_tag; the third value "
        "carries the OPERATOR relation symbols in either source mode."
    ),
    "alice_alphabet": "the ordered general Alice alphabet",
    "acceptance_values": "the ordered acceptance alphabet",
    "key_value_count": "the number of raw key values",
    "accept_statistic": "pairs [transcript tuple, acceptance value]",
    "key_map": "pairs [(Alice letter, product measured letter), raw key]",
}


@dataclass(frozen=True)
class GeneralSlots:
    """The general format's slots, materialised in the engine's own types.

    What a wire reader produces and what :func:`dock_general_declaration`
    consumes. Every field is optional and an absent one takes the degenerate
    reading of the accepted format, which is what makes the two branches of this
    sweep joinable one function at a time.
    """

    alice: AliceFactor | None = None
    alice_marginal: Mapping[str, Matrix] | None = None
    alice_form: AliceForm | None = None
    alice_operators: Mapping[str, Mapping[str, Matrix]] | None = None
    factors: Sequence[MeasuredFactor] | None = None
    transcript: Transcript | None = None
    accept_statistic: Mapping[tuple[str, ...], str] | None = None
    key_map: Mapping[tuple[str, str], int | None] | None = None
    constraint_list: Sequence[GeneralConstraintEntry] | None = None
    alice_alphabet: tuple[str, ...] | None = None
    acceptance_values: tuple[str, ...] | None = None
    key_value_count: int | None = None

    @property
    def is_empty(self) -> bool:
        """Return whether no general-format slot was supplied at all."""
        return all(
            getattr(self, name) is None
            for name in (
                "alice",
                "alice_marginal",
                "alice_form",
                "alice_operators",
                "factors",
                "transcript",
                "accept_statistic",
                "key_map",
                "constraint_list",
                "alice_alphabet",
                "acceptance_values",
                "key_value_count",
            )
        )


def dock_general_declaration(
    declaration: ProtocolDeclaration,
    slots: GeneralSlots | None = None,
    *,
    validate: bool = True,
) -> GeneralDeclaration:
    """Return the general-format declaration of an artefact.

    ``slots`` is what a reader of the general-format wire keys produced;
    ``None`` or an empty :class:`GeneralSlots` is the degenerate reading, and
    then this returns the embedding of ``declaration`` itself -- one Alice
    sector, one measured factor, POVM form, the two announcement maps as the
    ``L = 2`` transcript. A declaration so docked satisfies
    :attr:`GeneralDeclaration.is_degenerate`, so a caller routes it to the
    accepted code path and every number it produces is the number that path
    produced before this module existed.

    Raises:
        DeclarationError: if the supplied slots are not a well-formed general
            declaration (``validate=True``, the default: def:admissible-declaration in
            the general format is decided before anything is computed).
    """
    embedded = general_from_accepted(declaration)
    if slots is None or slots.is_empty:
        return embedded
    if (slots.alice is None) != (slots.alice_marginal is None) and (
        declaration.alice_marginal is not None
    ):
        raise DeclarationError(
            "def:declaration (DX1), (DX2): a declared factor tagged A and the "
            "marginal's block list along T arrive together -- tau_A is a list "
            "of one array per t and the list IS the operator. One without the "
            "other is refused rather than completed here"
        )
    general = GeneralDeclaration(
        alice=slots.alice if slots.alice is not None else embedded.alice,
        alice_marginal=(
            embedded.alice_marginal
            if slots.alice_marginal is None
            else dict(slots.alice_marginal)
        ),
        alice_alphabet=slots.alice_alphabet or embedded.alice_alphabet,
        alice_operators=(
            embedded.alice_operators
            if slots.alice_operators is None
            else {
                letter: dict(blocks) for letter, blocks in slots.alice_operators.items()
            }
        ),
        alice_form=slots.alice_form or embedded.alice_form,
        factors=(embedded.factors if slots.factors is None else tuple(slots.factors)),
        transcript=slots.transcript or embedded.transcript,
        accept_statistic=(
            embedded.accept_statistic
            if slots.accept_statistic is None
            else dict(slots.accept_statistic)
        ),
        key_map=(embedded.key_map if slots.key_map is None else dict(slots.key_map)),
        key_holder=embedded.key_holder,
        acceptance_values=slots.acceptance_values or embedded.acceptance_values,
        key_value_count=(
            embedded.key_value_count
            if slots.key_value_count is None
            else slots.key_value_count
        ),
        acceptance_set=embedded.acceptance_set,
        rounds=embedded.rounds,
        parameters=embedded.parameters,
        sector_block_kind=embedded.sector_block_kind,
        constraint_list=(
            embedded.constraint_list
            if slots.constraint_list is None
            else tuple(slots.constraint_list)
        ),
        constraints_through_a_reductions_chain=(
            embedded.constraints_through_a_reductions_chain
        ),
        attack_set_license=embedded.attack_set_license,
        source_replacement_license=embedded.source_replacement_license,
    )
    if validate:
        validate_general_declaration(general)
    return general


def dock_general_candidate(
    declaration: CandidateDeclaration,
    *,
    acceptance_set: AcceptanceSet,
    rounds: int,
    parameters: KeyLengthParameters,
    reduction_chain_record: Mapping[str, object] | None = None,
) -> GeneralDeclaration:
    """Dock the actual compiler artifact through its shared slot accessors.

    These accessors resolve the dense/block alternatives, missing factor
    labels and the one-factor default scope on the supplier's declared data.
    Exact numbers cross through the existing lossless binary64 boundary.
    """
    from certiqs_key.meat_core.docking import (
        RELATION_TO_CONSUMER,
        _binary64_scalar,
        _consumer_partition,
        _license_record,
        _transported_against_the_list,
        sector_blocks,
        to_complex128,
    )
    from certiqs_key.protocol_compiler.spec import PERP

    d = declaration
    alice_axis = SectorAxis(
        d.alice_sectors.labels,
        dict(zip(d.alice_sectors.labels, d.alice_sectors.dims, strict=True)),
    )
    partition = replace(
        _consumer_partition(d),
        party_of_sector_factors={
            s: tuple(PartyLabel(f.party) for f in d.measured_factors)
            for s in d.sectors.labels
        },
    )
    factors = []
    for i, (label, factor) in enumerate(
        zip(d.measured_factor_labels, d.measured_factors, strict=True)
    ):
        family = None if d.bob_factors is None else d.bob_factors.factors[i]
        alphabet = d.bob_alphabet if family is None else family.alphabet
        factors.append(
            MeasuredFactor(
                label=label,
                party=PartyLabel(factor.party),
                sectors=SectorAxis(
                    factor.sectors.labels,
                    dict(zip(factor.sectors.labels, factor.sectors.dims, strict=True)),
                ),
                alphabet=alphabet,
                blocks={
                    v: sector_blocks(
                        d.bob_povm[v] if family is None else family.member(v),
                        factor.sectors.labels,
                    )
                    for v in alphabet
                },
            )
        )
    entries = []
    for entry in d.constraint_list:
        scope = entry.scope
        if scope is None:
            if len(factors) != 1:
                raise DeclarationError(
                    "an absent constraint scope requires one measured factor"
                )
            scope = factors[0].label
        position = d.measured_factor_position(scope)
        bound: float | Mapping[str, Matrix]
        if isinstance(entry.rhs, Fraction):
            bound = _binary64_scalar(entry.rhs, "constraint scalar")
        elif isinstance(entry.rhs, BlockOperator):
            if entry.rhs.sector_map != d.alice_sectors:
                raise DeclarationError(
                    "general right-hand side carries a different T map"
                )
            bound = sector_blocks(
                entry.rhs, d.alice_sectors.labels, what="general right-hand side"
            )
        else:
            dense = to_complex128(entry.rhs)
            blocks = {}
            remainder = dense.copy()
            offset = 0
            for t, width in zip(
                d.alice_sectors.labels, d.alice_sectors.dims, strict=True
            ):
                blocks[t] = dense[offset : offset + width, offset : offset + width]
                remainder[offset : offset + width, offset : offset + width] = 0
                offset += width
            if np.any(remainder != 0):
                raise DeclarationError(
                    "general right-hand side is not block diagonal along T"
                )
            bound = blocks
        if entry.tag is None:
            raise DeclarationError("constraint has no declared right-hand-side tag")
        entries.append(
            GeneralConstraintEntry(
                scope=scope,
                operator_blocks=sector_blocks(
                    entry.operator, factors[position].sectors.labels
                ),
                relation=RELATION_TO_CONSUMER[entry.relation],
                bound=bound,
                rhs_tag=GeneralRhsTag(entry.tag.value),
            )
        )
    transcript = (
        two_message_transcript(d.announce_alice, d.announce_bob)
        if d.transcript is None
        else Transcript(
            tuple(
                Message(KeyHolder(m.sender), m.alphabet, dict(m.table))
                for m in d.transcript.messages
            )
        )
    )
    marginal = d.marginal_blocks
    result = GeneralDeclaration(
        alice=AliceFactor(partition.party_of_alice_system, alice_axis),
        alice_marginal=None
        if marginal is None
        else sector_blocks(marginal, alice_axis.labels),
        alice_alphabet=d.alice_alphabet,
        alice_operators={
            x: sector_blocks(d.alice_operator(x), alice_axis.labels)
            for x in d.alice_alphabet
        },
        alice_form=AliceForm(d.alice_form.value),
        factors=tuple(factors),
        transcript=transcript,
        accept_statistic={
            kappa: d.acceptance_value(kappa) for kappa in d.announcement_classes()
        },
        key_map={
            pair: None if value == PERP else int(value)
            for pair, value in d.key_map.items()
        },
        key_holder=KeyHolder(d.key_holder.value),
        acceptance_values=d.acceptance_alphabet,
        key_value_count=len(d.key_alphabet),
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
        party_partition=partition,
        sector_block_kind=d.sectors.block_kind.value,
        constraint_list=tuple(entries),
        constraints_through_a_reductions_chain=_transported_against_the_list(
            reduction_chain_record, d.constraint_list
        ),
        attack_set_license=None
        if d.attack_set_license is None
        else {
            "supplier": d.attack_set_license.supplier,
            "statement": d.attack_set_license.statement,
        },
        source_replacement_license=None
        if d.source_replacement_license is None
        else _license_record(d.source_replacement_license),
    )
    validate_general_declaration(result)
    return result
