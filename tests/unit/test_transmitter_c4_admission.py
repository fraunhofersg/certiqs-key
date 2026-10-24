"""C4 opens the admitting-module route without weakening source provenance."""

from dataclasses import fields, replace
from fractions import Fraction
from typing import Any, cast

from decoy_support import declaration_input

from certiqs_key.transmitter.artifact import (
    TransmitterArtifact,
    source_segment_from_admitting_module,
)
from certiqs_key.transmitter.decoy import emit_decoy_declaration
from certiqs_key.transmitter.links import SourceLinkKind


def test_tagged_source_emits_its_link_and_model_assumption() -> None:
    source = emit_decoy_declaration(declaration_input()).require()
    artifact = source.as_transmitter_artifact()
    assert artifact.source_segment == source.source_segment
    assert artifact.alice_ensemble_operators
    assert not artifact.alice_povm
    assert artifact.assumption_ledger == (
        "wcp_source_model", "sequential_round_model", "source_replacement_license"
    )
    assert artifact.as_machine_record()["source_segment"]
    assert source_segment_from_admitting_module(artifact)

    generic = cast(Any, TransmitterArtifact)(
        **{
            field.name: getattr(artifact, field.name)
            for field in fields(artifact)
        }
    )
    assert not source_segment_from_admitting_module(generic)

    wrong_kind = replace(
        artifact,
        source_segment=(
            replace(
                artifact.source_segment[0],
                kind=SourceLinkKind.SOURCE_MAP,
                obligation=replace(
                    artifact.source_segment[0].obligation,
                    kind=SourceLinkKind.SOURCE_MAP,
                ),
            ),
        ),
    )
    assert not source_segment_from_admitting_module(wrong_kind)


def test_vacuum_only_decoy_is_admitted_without_source_attestation() -> None:
    declaration = declaration_input(entropy_cutoff=0, source_cutoff=0)
    model = replace(
        declaration.model,
        intensities={mu: Fraction(0) for mu in declaration.model.intensities},
    )
    declaration = replace(
        declaration, model=model,
        sector_weights={(0, mu): Fraction(1) for mu in model.intensities},
    )
    artifact = emit_decoy_declaration(declaration).require().as_transmitter_artifact()
    assert artifact.alice_dim == 1
    assert artifact.alice_marginal is not None
    assert artifact.source_replacement_license is None
    assert artifact.assumption_ledger == ("wcp_source_model", "sequential_round_model")
