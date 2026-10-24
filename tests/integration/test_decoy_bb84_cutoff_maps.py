"""Exact cutoff maps between actual prepared and compiled decoy programs.

These are structural D-3 checks, not optimizer comparisons.  The tests construct
the label-independent channel from a lower-cutoff tagged source to a
higher-cutoff one and apply it exactly to every emitted weighted source block.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction

import pytest
from instances.common.wcp import PreparedSource
from instances.decoy_bb84 import default_config, preparation
from tests.support.lowered_templates import decoy_source

from certiqs_key.foundations.exact import (
    Matrix,
    add,
    scale,
    trace_in_row_order,
    zeros,
)
from certiqs_key.runs.pipeline import Preparation
from certiqs_key.transmitter.certificate import SourceReplacementLicense
from certiqs_key.transmitter.decoy import (
    SectorKind,
    TaggedSector,
    TaggedSourceDeclaration,
    WcpLetter,
    emit_decoy_declaration,
    poisson_enclosures,
)
from certiqs_key.transmitter.presentation import EnsemblePresentation


@dataclass(frozen=True)
class _MapLeg:
    """One branch of the direct-sum coarse-to-fine source channel."""

    target: str
    probability: Fraction
    prepared_state: Matrix | None


def _actual_program(
    entropy_cutoff: int, source_cutoff: int
) -> tuple[PreparedSource, Preparation]:
    """Prepare and compile one actual licensed program with all other data fixed."""
    config = default_config(
        device={
            "entropy_cutoff": entropy_cutoff,
            "source_cutoff": source_cutoff,
            "route": "licensed",
        }
    )
    _, source = decoy_source(config)
    outcome = preparation(config)
    assert isinstance(outcome, Preparation), outcome
    return source, outcome


def _actual_source(entropy_cutoff: int, source_cutoff: int) -> PreparedSource:
    config = default_config(
        device={
            "entropy_cutoff": entropy_cutoff,
            "source_cutoff": source_cutoff,
        }
    )
    _, source = decoy_source(config)
    return source


def _sector_by_label(declaration: TaggedSourceDeclaration) -> dict[str, TaggedSector]:
    return {sector.label: sector for sector in declaration.sector_index_set()}


def _letter_for(
    declaration: TaggedSourceDeclaration,
    *,
    polarisation: str,
    intensity: str | None = None,
) -> WcpLetter:
    return next(
        letter
        for letter in declaration.model.alphabet
        if letter.polarisation == polarisation
        and (intensity is None or letter.intensity == intensity)
    )


def _require_compatible_preparation(
    coarse: TaggedSourceDeclaration, fine: TaggedSourceDeclaration
) -> None:
    """Check the exact premises under which the cutoff ordering is available."""
    for field in (
        "polarisations",
        "intensities",
        "alphabet",
        "weights",
        "polarisation_parts",
    ):
        if getattr(coarse.model, field) != getattr(fine.model, field):
            raise ValueError("the source model or prepared label weights changed")
    if (
        fine.entropy_cutoff < coarse.entropy_cutoff
        or fine.source_cutoff < coarse.source_cutoff
    ):
        raise ValueError("the second declaration is not a cutoff extension")
    if (
        fine.entropy_cutoff == coarse.entropy_cutoff
        and fine.source_cutoff == coarse.source_cutoff
    ):
        raise ValueError("at least one cutoff must increase")

    for intensity in coarse.model.intensities:
        for photon_number in range(coarse.source_cutoff + 1):
            key = photon_number, intensity
            if coarse.sector_weights[key] != fine.sector_weights[key]:
                raise ValueError(
                    "a common prepared sector weight changed; the tested source "
                    "map and cutoff ordering do not apply"
                )

        exposed = sum(
            (
                fine.sector_weights[photon_number, intensity]
                for photon_number in range(
                    coarse.source_cutoff + 1, fine.source_cutoff + 1
                )
            ),
            Fraction(),
        )
        if coarse.tail_weight(intensity).value != (
            fine.tail_weight(intensity).value + exposed
        ):
            raise ValueError(
                "the coarse tail is not exactly the fine tail plus newly exposed "
                "prepared weights"
            )

    for (photon_number, intensity), weight in fine.sector_weights.items():
        enclosure = poisson_enclosures(
            fine.model.intensities[intensity], fine.source_cutoff
        ).enclosures[photon_number]
        if not Fraction() <= weight <= enclosure.lower:
            raise ValueError("a prepared weight is outside its directed Poisson bound")


def _prepared_dyad(
    fine: TaggedSourceDeclaration,
    target: TaggedSector,
    *,
    polarisation: str,
    intensity: str | None = None,
) -> Matrix:
    letter = _letter_for(fine, polarisation=polarisation, intensity=intensity)
    return fine.dyad_in(target, letter)


def _coarse_source_map(
    coarse: TaggedSourceDeclaration, fine: TaggedSourceDeclaration
) -> dict[str, tuple[_MapLeg, ...]]:
    """Construct Gamma with Xi_coarse = Xi_fine o Gamma, exactly.

    Common quantum sectors are embedded identically.  A coarse polarisation
    flag is either unchanged or prepares the corresponding fine quantum state.
    A coarse ``(polarisation, intensity)`` tail flag is measured and prepares a
    mixture of newly exposed sectors and the fine tail.  Its branch weights are
    exact rational ratios and sum to one.
    """
    _require_compatible_preparation(coarse, fine)
    fine_sectors = _sector_by_label(fine)
    result: dict[str, tuple[_MapLeg, ...]] = {}

    for source in coarse.sector_index_set():
        if source.kind is SectorKind.QUANTUM:
            target = fine_sectors[source.label]
            assert source.dim == target.dim
            result[source.label] = (_MapLeg(target.label, Fraction(1), None),)
            continue

        if source.kind is SectorKind.POLARISATION_FLAG:
            assert source.photon_number is not None
            assert source.polarisation is not None
            if source.photon_number <= fine.entropy_cutoff:
                target = fine_sectors[f"n{source.photon_number}"]
                prepared = _prepared_dyad(
                    fine, target, polarisation=source.polarisation
                )
                result[source.label] = (_MapLeg(target.label, Fraction(1), prepared),)
            else:
                target = fine_sectors[source.label]
                result[source.label] = (_MapLeg(target.label, Fraction(1), None),)
            continue

        assert source.kind is SectorKind.TAIL_FLAG
        assert source.polarisation is not None
        assert source.intensity is not None
        coarse_tail = coarse.tail_weight(source.intensity).value
        assert coarse_tail > 0
        legs: list[_MapLeg] = []
        for photon_number in range(coarse.source_cutoff + 1, fine.source_cutoff + 1):
            weight = fine.sector_weights[photon_number, source.intensity]
            if weight == 0:
                continue
            target_label = (
                f"n{photon_number}"
                if photon_number <= fine.entropy_cutoff
                else f"flag-n{photon_number}-{source.polarisation}"
            )
            target = fine_sectors[target_label]
            legs.append(
                _MapLeg(
                    target.label,
                    weight / coarse_tail,
                    _prepared_dyad(fine, target, polarisation=source.polarisation),
                )
            )

        fine_tail = fine.tail_weight(source.intensity).value
        if fine_tail:
            target = fine_sectors[f"tail-{source.polarisation}-{source.intensity}"]
            legs.append(
                _MapLeg(
                    target.label,
                    fine_tail / coarse_tail,
                    _prepared_dyad(
                        fine,
                        target,
                        polarisation=source.polarisation,
                        intensity=source.intensity,
                    ),
                )
            )
        assert sum((leg.probability for leg in legs), Fraction()) == 1
        result[source.label] = tuple(legs)

    return result


def _apply_to_presentation(
    source_map: dict[str, tuple[_MapLeg, ...]],
    coarse: EnsemblePresentation,
    fine: EnsemblePresentation,
) -> dict[str, tuple[Matrix, ...]]:
    """Apply the tests' exact direct-sum channel to every weighted source block."""
    fine_dims = dict(
        zip(fine.virtual_sectors.labels, fine.virtual_sectors.dims, strict=True)
    )
    mapped: dict[str, tuple[Matrix, ...]] = {}
    for letter, blocks in coarse.weighted_blocks.items():
        output = {label: zeros(dim) for label, dim in fine_dims.items()}
        for source_label, block in zip(
            coarse.virtual_sectors.labels, blocks, strict=True
        ):
            block_trace = trace_in_row_order(block)
            assert block_trace.value.is_real
            for leg in source_map[source_label]:
                contribution = (
                    scale(leg.probability, block)
                    if leg.prepared_state is None
                    else scale(
                        leg.probability * block_trace.value.re,
                        leg.prepared_state,
                    )
                )
                output[leg.target] = add(output[leg.target], contribution)
        mapped[letter] = tuple(output[label] for label in fine.virtual_sectors.labels)
    return mapped


def _assert_shared_program_is_fixed(coarse: Preparation, fine: Preparation) -> None:
    """Check the source map is the only change in the two compiled programs."""
    assert coarse.raw_joint_distribution == fine.raw_joint_distribution
    left = coarse.declaration
    right = fine.declaration
    for field in (
        "alice_alphabet",
        "bob_alphabet",
        "bob_povm",
        "sectors",
        "partition",
        "announce_alice",
        "announce_bob",
        "alice_announcement_alphabet",
        "bob_announcement_alphabet",
        "acceptance_alphabet",
        "accept_statistic",
        "key_map",
        "key_alphabet",
        "key_holder",
        "constraint_list",
        "attack_set_license",
        "transcript",
        "accept_statistic_general",
    ):
        assert getattr(left, field) == getattr(right, field), field
    assert left.measured_factors == right.measured_factors
    assert left.bob_factors is not None
    assert right.bob_factors is not None
    assert left.bob_factors.factors == right.bob_factors.factors
    assert left.constraint_list
    assert left.attack_set_license is not None


def _compiled_presentation(outcome: Preparation) -> EnsemblePresentation:
    licence = outcome.declaration.source_replacement_license
    assert isinstance(licence, SourceReplacementLicense)
    assert licence.presentation is not None
    return licence.presentation


@pytest.mark.contract
@pytest.mark.parametrize(("coarse_cutoff", "fine_cutoff"), [(0, 1), (1, 2)])
def test_actual_entropy_cutoff_extension_has_an_exact_source_map(
    coarse_cutoff: int, fine_cutoff: int
) -> None:
    coarse_source, coarse_program = _actual_program(coarse_cutoff, 2)
    fine_source, fine_program = _actual_program(fine_cutoff, 2)
    _assert_shared_program_is_fixed(coarse_program, fine_program)

    source_map = _coarse_source_map(coarse_source.tagged, fine_source.tagged)
    coarse_presentation = _compiled_presentation(coarse_program)
    fine_presentation = _compiled_presentation(fine_program)
    assert (
        coarse_presentation
        == emit_decoy_declaration(coarse_source.tagged).require().presentation
    )
    assert (
        fine_presentation
        == emit_decoy_declaration(fine_source.tagged).require().presentation
    )
    assert _apply_to_presentation(
        source_map, coarse_presentation, fine_presentation
    ) == dict(fine_presentation.weighted_blocks)


@pytest.mark.contract
@pytest.mark.parametrize(("coarse_cutoff", "fine_cutoff"), [(1, 2), (2, 3)])
def test_actual_source_cutoff_extension_splits_each_tail_exactly(
    coarse_cutoff: int, fine_cutoff: int
) -> None:
    coarse_source, coarse_program = _actual_program(1, coarse_cutoff)
    fine_source, fine_program = _actual_program(1, fine_cutoff)
    _assert_shared_program_is_fixed(coarse_program, fine_program)

    source_map = _coarse_source_map(coarse_source.tagged, fine_source.tagged)
    coarse_presentation = _compiled_presentation(coarse_program)
    fine_presentation = _compiled_presentation(fine_program)
    assert _apply_to_presentation(
        source_map, coarse_presentation, fine_presentation
    ) == dict(fine_presentation.weighted_blocks)

    # The non-vacuum coarse tails really split: this is not an identity-only test.
    assert len(source_map["tail-H-signal"]) == 2
    assert len(source_map["tail-H-weak"]) == 2


@pytest.mark.contract
def test_cutoff_ordering_is_not_asserted_after_a_common_weight_changes() -> None:
    coarse_source = _actual_source(1, 1)
    fine_source = _actual_source(1, 2)
    changed_weights = dict(fine_source.tagged.sector_weights)
    changed_weights[0, "signal"] -= Fraction(1, 1 << 24)
    changed = replace(fine_source.tagged, sector_weights=changed_weights)

    # The altered declaration remains independently admissible under the same
    # directed Poisson bounds.  It is simply not the cutoff extension above.
    assert emit_decoy_declaration(changed).refusal is None
    with pytest.raises(ValueError, match="common prepared sector weight changed"):
        _coarse_source_map(coarse_source.tagged, changed)
