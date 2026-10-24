"""The run's attestation of an in-run receiver artefact: ``receiver_provenance``.

WHY THIS EXISTS. ``reductions/req:recv-row-provenance`` lets the reductions
module omit the row of A-RECV (``reductions/ass:recv``) where the receiver
artefact it read is one the run built itself -- exact, with every weight
evaluated rigorously -- because there both clauses of A-RECV hold by the
receiver's own theorems under its own ledger. Whether the run built the
artefact cannot be read off the artefact, whose version, validation results
and ledger a hand-written one can carry equally; it is established by "the
part of the engine that ran the receiver module and docked its artefact into
the instance", and that is this tier. So this module looks at what the run
itself produced and docked, and mints
:class:`~certiqs_key.reductions.provenance.ReceiverProvenance` only where:

* THE ARTEFACT IS THIS RUN'S (condition (i)). The caller hands the artefact
  :func:`~certiqs_key.receiver.construct.construct_receiver` returned in the
  same run, on the receiver declaration the run holds, as the installed
  receiver module built it (:func:`certiqs_key.runs.pipeline._run_device_prologue`,
  the one caller). A route that hands the run a finished receiver artefact,
  or a reduction call written by hand, has no such artefact and passes no
  attestation.
* IT REACHES THE REDUCTION AS IT WAS EMITTED (condition (i)). The rows handed
  to the reduction are re-docked from the artefact with the receiver's own
  docking (:func:`~certiqs_key.receiver.docking.receiver_artifact_rows`, in the
  block form the rows state) and compared field for field. The photon-number
  blocks below the cutoff, the declaring party's snap record and the
  reference handed beside it are excepted: they are the instance's
  DECLARATION (``foundations/def:declared-data`` (ii)), snapped against the
  receiver's enclosures, a moved block resting on
  ``foundations/ass:snapped-measurement``, and no imported fact
  (``req:recv-row-provenance``, lead-in). Every row the reduction imports --
  the weights with their quantifier domain, the dark-count channel, the
  coarse-graining, the evaluation label, the exact-route record, the version,
  the validation results and the ledger -- must be the artefact's own, or
  nothing is attested.
* THE RUN'S RECORD CARRIES THE ARTEFACT'S OWN LEDGER (condition (iii)). It
  does on every route that docks: the record transcribes the artefact the
  device prologue returns (:func:`certiqs_key.runs.record.receiver_payload`,
  each station's ``receiver``), ledger included, and the route-exact
  manifest lists its rows (:func:`certiqs_key.runs.assumptions.emitted_rows`).

Conditions (ii) and (iv) are data, and the reductions module decides them on
the artefact itself
(:func:`certiqs_key.reductions.emit.receiver_row_omitted_on_provenance`): an
attested artefact with a weight evaluated in floating point, or admitted only
within the receiver tolerances, keeps the row whatever this record says.
"""

from __future__ import annotations

from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
from certiqs_key.receiver.docking import DockingRefusal, receiver_artifact_rows
from certiqs_key.reductions.inputs import ReceiverArtifactRows
from certiqs_key.reductions.provenance import ReceiverProvenance, imported_part

__all__ = ["attest_receiver_provenance"]


def attest_receiver_provenance(
    artifact: ReceiverMeasurementArtifact,
    rows: ReceiverArtifactRows,
) -> ReceiverProvenance | None:
    """Return the run's ``receiver_provenance`` for one docked artefact, or ``None``.

    ``artifact`` is the receiver artefact THIS RUN built, and ``rows`` the rows
    the run hands the reduction for it (docked by the run, or by the
    instance's adapter, which declares its snapped blocks). The conditions are
    the module docstring's: the rows must be the artefact's re-docking in every
    field the reduction imports, the declaration's blocks and their snap
    record excepted; where one differs nothing is attested and the reductions
    module emits the A-RECV row.
    """
    form_is_dark_composed = rows.photon_blocks_form == "dark_composed"
    docked = receiver_artifact_rows(artifact, dark_composed=form_is_dark_composed)
    if isinstance(docked, DockingRefusal):
        return None
    # The declaration's own fields set aside, every other field must be the
    # artefact's re-docking, exactly; the word is bound to those rows.
    if imported_part(docked) != imported_part(rows):
        return None
    return ReceiverProvenance.of(rows)
