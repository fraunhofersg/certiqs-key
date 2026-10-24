"""The run's attestation of an in-run reductions chain: ``chain_provenance``.

WHY THIS EXISTS. ``protocol-compiler/req:link-row-provenance`` lets the
compiler omit the row of A-LINK (``ass:link``) where the one receiver segment
is the single exact instance link of a reductions artefact emitted IN THE SAME
RUN and the presented physical family is that artefact's declared model or
exactly its compression -- because there the reductions module's own theorems
prove every clause (``protocol-compiler/rem:obligations-discharged``). Whether
a chain is such a link cannot be read off the specification, whose link fields
a hand-written one can carry equally; it is established by "the part of the
engine that ran the reductions module and docked its artefact", and that is
this tier. So this module looks at what the run itself produced and docked,
and mints :class:`~certiqs_key.protocol_compiler.provenance.ChainProvenance`
only where:

* EVERY MEASURED FACTOR, each with the artefact this run emitted for it
  (per factor: at several factors the
  joint discharge is ``reductions/thm:emitted-product`` (ii), (iii), with
  A-MEAS (iv) for the product apparatus). A factor without an artefact of
  this run, or failing any condition below, attests nothing for the whole
  specification, and the compiler emits the row.
* A FLAT-INSTANCE ARTEFACT. ``rem:obligations-discharged`` names the claim
  that makes the docked block the compression of the declared model for the
  flat instance alone (``reductions/wpfss/prop:flat-instance``); a branching
  artefact docks the same reading of its flat branch and no claim shows
  it to be a compression, so its routes keep the row. Read as the run's
  reductions roots read it (:mod:`certiqs_key.runs.assumptions`): an artefact
  carrying a row owned by a reductions submodule is that submodule's, and
  this tier names no claim of a removable submodule.
* THE ARTEFACT'S CHAIN IS ITS INSTANCE LINK ALONE, and the presented receiver
  segment IS that link as the reductions docking writes it: the segment is
  re-docked from the artefact with the presented descriptors and compared
  link for link (frozen ``ChainLink`` equality). A domination link after the
  instance link makes the artefact's chain two links long and passes none.
* THE PRESENTED PHYSICAL FAMILY IS THE READ-OFF, exactly: presented directly,
  on the preserved dimension, element for element the artefact's
  :func:`~certiqs_key.reductions.docking.physical_family`.

Everything else of ``req:link-row-provenance`` (ii) that is data -- the status,
the channel slot, the identity outcome correspondence, the empty source
segment -- the compiler decides on the presented chain itself, and it emits the
row where any of them fails whatever this record says.
"""

from __future__ import annotations

from collections.abc import Mapping

from certiqs_key.domain.claim_closure import assumption_info
from certiqs_key.foundations.blocks import default_factor_label
from certiqs_key.foundations.exact import equal
from certiqs_key.protocol_compiler import (
    ChainProvenance,
    DirectPovm,
    ProtocolSpecification,
    ReceiverPart,
    ReductionChain,
)
from certiqs_key.protocol_compiler.provenance import FactorProvenance
from certiqs_key.reductions import docking
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.reasons import LinkKind

__all__ = ["attest_chain_provenance", "is_flat_instance"]

#: The squashing link kinds of the flat instance (``reductions/wpfss``).
_FLAT_KINDS = frozenset({LinkKind.WPFSS, LinkKind.FSS})


def is_flat_instance(artifact: ProofReductionArtifact) -> bool:
    """Whether an artefact is the flat instance's: no submodule row, a flat link.

    A row the artefact carries whose assumption the closure table gives an
    owner in a reductions SUBMODULE (``reductions/<sub>/...``) other than the
    flat instance's own names that submodule (a branching instance carries
    its own rows); otherwise the artefact is the flat instance's exactly when its
    chain's links are squashing links of kind ``wpfss`` or ``fss``.
    """
    for entry in artifact.assumption_ledger:
        owner = str(assumption_info(entry.assumption_id)["owner"])
        if (
            owner.startswith("reductions/")
            and owner.count("/") >= 2
            and not owner.startswith("reductions/wpfss/")
        ):
            return False
    links = artifact.reduction_chain.links
    return bool(links) and all(link.kind in _FLAT_KINDS for link in links)


def attest_chain_provenance(
    specification: ProtocolSpecification,
    artifacts: Mapping[str, ProofReductionArtifact],
) -> ChainProvenance | None:
    """Return the run's ``chain_provenance`` for a specification, or ``None``.

    ``artifacts`` are the reductions artefacts THIS RUN emitted and docked into
    ``specification``, keyed by the measured factor each became (a factor's
    ``factor_label``, or the position default ``f<position>``); empty on a
    route that supplied a finished specification. The conditions are the
    module docstring's, decided factor by factor; where one fails for any
    factor nothing is attested and the compiler emits the A-LINK row.
    """
    factors: list[FactorProvenance] = []
    for position, part in enumerate(specification.receiver_parts):
        label = (
            part.factor_label
            if part.factor_label is not None
            else default_factor_label(position)
        )
        artifact = artifacts.get(label)
        if artifact is None:
            return None
        chain = specification.chain if position == 0 else part.chain
        attested = _attest_factor(part, chain, artifact, label)
        if attested is None:
            return None
        factors.append(attested)
    return ChainProvenance(factors=tuple(factors)) if factors else None


def _attest_factor(
    part: ReceiverPart,
    chain: object,
    artifact: ProofReductionArtifact,
    label: str,
) -> FactorProvenance | None:
    """Return the run's word on one factor's segment, or ``None`` where it fails."""
    if not is_flat_instance(artifact) or len(artifact.reduction_chain.links) != 1:
        return None
    if not isinstance(chain, ReductionChain) or len(chain.receiver_segment) != 1:
        return None
    presented = chain.receiver_segment[0]
    kind = presented.target_descriptor.sector_block_kind
    if kind is None:
        return None
    docked = docking.reduction_chain(
        artifact,
        presented.source_descriptor,
        presented.target_descriptor.name,
        sector_block_kind=kind,
    )
    if docked.receiver_segment != chain.receiver_segment:
        return None
    preserved = artifact.source_descriptor.channel_grading.preserved_dimension
    if part.physical_dim != preserved:
        return None
    family = part.physical_povm
    if not isinstance(family, DirectPovm):
        return None
    expected = docking.physical_family(artifact, preserved)
    if set(family.alphabet) != set(expected) or len(family.alphabet) != len(expected):
        return None
    if not all(equal(family.elements[letter], expected[letter]) for letter in expected):
        return None
    return FactorProvenance(
        factor=label,
        artifact_version=artifact.mathematical_spec_version,
        link_id=presented.link_id,
    )
