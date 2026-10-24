"""Lowering a protocol document to the modules' constructors, for one configuration.

WHY A LOWERING AND NOT A SECOND RULE ENGINE. A document says what a protocol
IS; the engine decides whether it is admissible. This module turns the
configuration-dependent blocks of a document -- the source, the stations, the
public part, the constraints, the honest model and the channel interface --
into exactly the arguments the modules' public constructors take
(``SourceSpecification`` for :func:`~certiqs_key.transmitter.artifact.
emit_artifact`, a ``TaggedSourceDeclaration`` for ``emit_decoy_declaration``,
``ReceiverRequest`` and the reductions' requests, ``PublicChoices``,
``ReceiverPart``, ``PublicPart`` with or without a transcript,
``SpecConstraints``, the honest-model library's providers), and hands them
over. It decides nothing about the protocol: a weight that does not sum to one,
a POVM that is not complete, a key map that is not total is the transmitter's
or the compiler's refusal, returned as data.

TWO ROUTES, AS THE RUN TIER HAS THEM. Band A -- every station a
``declared_povm`` -- builds the specification directly. Optical stations
build each station's :class:`~certiqs_key.runs.pipeline.DeviceRequests`
(:mod:`.optical`) and a SPECIFICATION PROVIDER over the emitted artefacts:
one station's is the construction the optical and decoy BB84
templates use, several stations' the one the bbm92 template uses, with the
factor docking of ``reductions.factors``. The rule tables are expanded
BEFORE the run, over the outcome alphabets the reductions will emit, so a
refused run still records them; each provider checks that the emitted
alphabet is the predicted one.

WHAT IT DOES REFUSE, as :class:`~instances.declared.errors.DocumentError`:
what has no meaning as a document (a rule value that cannot be rendered, a
block label that names no sector, a mode label that names no mode), a
transmitter refusal surfaced as ``source_refused`` with the transmitter's own
reason in ``module_reason`` (``require()`` is never called),
explicit constraint entries without an explicit licence, the
wrapped call sites (``wcp_source_invalid``,
``factor_assembly_refused``, ``choice_weighting_refused``), and a topology
the run tier has no route for (``unsupported_topology``: a channel interface
that does not describe the stations, a library witness of a shape the
document does not have).

WHAT IT RECORDS. Every expanded rule table, the keys no rule matched, and every
premise the document itself supplies (``user_declared``: explicit constraint
entries, licences and witnesses, a hand-declared receiver POVM, the source's
retention attestation). The record block is
:meth:`Lowered.record`, which the run tier carries into the run record as
``payload.protocol_document`` (record schema 0.21.0). A PACKAGED template's
record lists its items as a custom document's does (bb84's declared POVM,
decoy_bb84's retention attestation): whoever runs a shipped template vouches
for them.

THE PACKAGE. One lowering is one object, :class:`.providers._Lowering`, built
up in layers, one module per block of the document, each on the one before:
:mod:`.base` (the records :class:`Lowered` and :class:`UserDeclared`, the
shared helpers and the lowering's state), :mod:`.source`, :mod:`.stations`,
:mod:`.public`, :mod:`.constraints`, :mod:`.honest` (with the one wrapped call
site of the honest library) and :mod:`.providers` (the two drivers, Band A and
optical). This module holds :func:`lower`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from certiqs_key.foundations.snap import SnapSettings
from instances.declared.lowering.base import (
    ASSUMPTION_OF_KIND,
    Lowered,
    UserDeclared,
)
from instances.declared.lowering.providers import _Lowering
from instances.declared.model import DeclaredPovm, ProtocolDocument
from instances.declared.values import Environment

__all__ = [
    "ASSUMPTION_OF_KIND",
    "Lowered",
    "UserDeclared",
    "lower",
]


def lower(
    model: ProtocolDocument,
    environment: Environment,
    *,
    record_label: str,
    document_id: str,
    declared_tolerance: float,
    model_section: Mapping[str, Any] | None = None,
    work_bounds: bool = True,
    snap: SnapSettings | None = None,
) -> Lowered:
    """Lower a document at one configuration's values.

    ``model_section`` is the configuration's model section, which a bipartite
    channel interface records as its source parameters (bbm92's).
    ``snap`` is the run's snap parameters
    (``instances.common.declare.snap_settings``; their defaults where none).
    ``work_bounds`` is ``False`` for a packaged template, which its own
    parameter domains bound instead of the work bounds of :mod:`.limits`.
    """
    lowering = _Lowering(
        model,
        environment,
        record_label=record_label,
        document_id=document_id,
        declared_tolerance=declared_tolerance,
        model_section=model_section or {},
        work_bounds=work_bounds,
        snap=snap,
    )
    if all(isinstance(s.measurement, DeclaredPovm) for s in model.stations):
        return lowering.band_a()
    return lowering.optical()
