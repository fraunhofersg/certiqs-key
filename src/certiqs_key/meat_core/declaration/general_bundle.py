"""Read schema 0.4 general operator bundles without forming product data."""

from __future__ import annotations

from typing import Any

import numpy as np

from certiqs_key.domain.arrays import ArrayDescriptor, BlockDiagonalOperator
from certiqs_key.domain.bundle import OperatorBundle
from certiqs_key.domain.manifest import KeyHolder, PartyLabel
from certiqs_key.foundations.blocks import (
    IMPLICIT_ALICE_SECTOR_LABEL,
    SystemTag,
    default_factor_label,
)
from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
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
    two_message_transcript,
)
from certiqs_key.meat_core.declaration.general_validation import (
    validate_general_declaration,
)
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.linalg import Matrix


def general_declaration_from_bundle(bundle: OperatorBundle) -> GeneralDeclaration:
    """Materialize each declared factor and Alice block, then decide admissibility.

    Admissibility is ``def:admissible-declaration``, decided by
    :func:`~certiqs_key.meat_core.declaration.general_validation.validate_general_declaration`.
    """
    from certiqs_key.meat_core.declaration.bundle import (
        _acceptance_set,
        _blocks_from_operator,
        _materialize,
        _party_partition,
    )

    payload = bundle.manifest.payload
    d = payload.declaration
    arrays = dict(bundle.arrays)
    kind = d.sector_block_kind
    factors = d.sector_factorisation or ()
    retained = [f for f in factors if f.system is SystemTag.A]
    measured = [f for f in factors if f.system is SystemTag.Q]
    partition = _party_partition(d.party_partition)
    alice_axis = (
        SectorAxis(tuple(s for s, _ in retained[0].sectors), dict(retained[0].sectors))
        if retained
        else SectorAxis(
            (IMPLICIT_ALICE_SECTOR_LABEL,), {IMPLICIT_ALICE_SECTOR_LABEL: d.alice_dim}
        )
    )
    alice_party = (
        PartyLabel(retained[0].party)
        if retained
        else PartyLabel.ALICE
        if partition is None
        else partition.party_of_alice_system
    )

    def blocks(
        operator: BlockDiagonalOperator, axis: SectorAxis, where: str
    ) -> dict[str, Matrix]:
        return _blocks_from_operator(operator, arrays, axis.labels, where, kind)

    def dense_alice(descriptor: ArrayDescriptor, where: str) -> dict[str, Matrix]:
        matrix = _materialize(descriptor, arrays, where)
        if matrix.shape != (d.alice_dim, d.alice_dim):
            raise DeclarationError(f"{where}: wrong Alice operator dimension")
        out = {}
        remainder = matrix.copy()
        offset = 0
        for t in alice_axis.labels:
            width = alice_axis.dims[t]
            out[t] = matrix[offset : offset + width, offset : offset + width]
            remainder[offset : offset + width, offset : offset + width] = 0
            offset += width
        if np.any(remainder != 0):
            raise DeclarationError(
                f"{where}: not block diagonal along declared Alice sectors"
            )
        return out

    marginal = (
        blocks(d.alice_marginal_blocks, alice_axis, "alice_marginal_blocks")
        if d.alice_marginal_blocks is not None
        else None
        if d.alice_marginal is None
        else dense_alice(d.alice_marginal, "alice_marginal")
    )
    form = AliceForm.POVM if d.alice_form is None else AliceForm(d.alice_form.value)
    operators = d.alice_ensemble if form is AliceForm.ENSEMBLE else d.alice_povm_blocks
    alice_operators = (
        {
            x: blocks(operator, alice_axis, f"alice[{x}]")
            for x, operator in operators.items()
        }
        if operators is not None
        else {
            x: dense_alice(descriptor, f"alice_povm[{x}]")
            for x, descriptor in d.alice_povm.items()
        }
    )
    output_factors = []
    if d.bob_povm_factors is not None:
        if len(measured) != len(d.bob_povm_factors):
            raise DeclarationError(
                "one family is required per declared measured factor"
            )
        for i, (factor, family) in enumerate(
            zip(measured, d.bob_povm_factors, strict=True)
        ):
            axis = SectorAxis(tuple(s for s, _ in factor.sectors), dict(factor.sectors))
            if factor.party != family.party:
                raise DeclarationError(
                    "factor family party differs from sector factor party"
                )
            output_factors.append(
                MeasuredFactor(
                    label=factor.label or default_factor_label(i),
                    party=PartyLabel(factor.party),
                    sectors=axis,
                    alphabet=family.alphabet,
                    blocks={
                        v: blocks(family.members[v], axis, f"factor[{i}][{v}]")
                        for v in family.alphabet
                    },
                )
            )
    else:
        if len(measured) > 1:
            raise DeclarationError(
                "multiple measured factors require per-factor families"
            )
        axis = SectorAxis(d.sector_index_set, dict(d.sector_dims))
        output_factors.append(
            MeasuredFactor(
                label=(measured[0].label or default_factor_label(0))
                if measured
                else default_factor_label(0),
                party=PartyLabel(measured[0].party) if measured else PartyLabel.BOB,
                sectors=axis,
                alphabet=payload.alphabets.bob_outcome,
                blocks={
                    v: blocks(d.bob_povm[v], axis, f"bob_povm[{v}]")
                    for v in payload.alphabets.bob_outcome
                },
            )
        )
    transcript = (
        two_message_transcript(d.announce_alice, d.announce_bob)
        if d.transcript is None
        else Transcript(
            tuple(
                Message(
                    KeyHolder(m.sender.value),
                    m.alphabet,
                    {(readout, earlier): value for readout, earlier, value in m.table},
                )
                for m in d.transcript
            )
        )
    )
    # The schema owns the additive field and the mutual-exclusion rule.
    general_statistics: Any = getattr(d, "accept_statistic_general", None)
    if d.transcript is not None and general_statistics is None:
        raise DeclarationError("a transcript requires its tuple-keyed acceptance map")
    statistic = (
        dict(general_statistics)
        if general_statistics is not None
        else {
            (a, b): value
            for a, row in d.accept_statistic.items()
            for b, value in row.items()
        }
    )
    entries = []
    labels = [f.label for f in output_factors]
    for i, entry in enumerate(d.constraint_list):
        scope = entry.scope
        if scope is None:
            if len(output_factors) != 1:
                raise DeclarationError("absent constraint scope requires one factor")
            scope = labels[0]
        if scope not in labels:
            raise DeclarationError("constraint scope names no measured factor")
        factor_axis = output_factors[labels.index(scope)].sectors
        entries.append(
            GeneralConstraintEntry(
                scope=scope,
                operator_blocks=blocks(entry.operator, factor_axis, f"constraint[{i}]"),
                relation=entry.relation,
                rhs_tag=GeneralRhsTag(entry.constraint_rhs_tag),
                bound=dense_alice(entry.bound, f"bound[{i}]")
                if isinstance(entry.bound, ArrayDescriptor)
                else float(entry.bound),
            )
        )
    result = GeneralDeclaration(
        alice=AliceFactor(alice_party, alice_axis),
        alice_marginal=marginal,
        alice_alphabet=payload.alphabets.alice_outcome,
        alice_operators=alice_operators,
        alice_form=form,
        factors=tuple(output_factors),
        transcript=transcript,
        accept_statistic=statistic,
        key_map={
            (x, v): value for x, row in d.key_map.items() for v, value in row.items()
        },
        key_holder=d.key_holder,
        acceptance_values=payload.alphabets.acceptance_value,
        key_value_count=payload.alphabets.key_value_count,
        acceptance_set=_acceptance_set(
            d.acceptance_set.geometry,
            dict(d.acceptance_set.data),
            len(payload.alphabets.acceptance_value),
        ),
        rounds=d.rounds,
        parameters=KeyLengthParameters(
            alpha=payload.parameters.alpha,
            eps_pa=payload.parameters.eps_pa,
            eps_ev=payload.parameters.eps_ev,
            lambda_ec=payload.parameters.lambda_ec,
        ),
        party_partition=partition,
        sector_block_kind=kind,
        constraint_list=tuple(entries),
        attack_set_license=d.attack_set_license,
        source_replacement_license=d.source_replacement_license,
    )
    if (
        result.alice_dim != d.alice_dim
        or result.sector_index_set != d.sector_index_set
        or dict(result.sector_dims) != d.sector_dims
    ):
        raise DeclarationError(
            "general factor map disagrees with declared dimensions or order"
        )
    if result.bob_outcomes != payload.alphabets.bob_outcome:
        raise DeclarationError(
            "product alphabet disagrees with declared measured alphabet"
        )
    validate_general_declaration(result)
    return result
