"""The run's word on where a receiver artefact came from: ``receiver_provenance``.

``req:recv-row-provenance``: the engine omits the row of ``ass:recv``
(A-RECV) from the emitted ledger only where every supplier artefact the
reduction instance read is a receiver artefact that the part of the engine
that ran this module obtained IN THE SAME RUN, by running the receiver module
as installed on the receiver declaration the run holds, handed on as it was
emitted (i), whose declared version is the installed module's and which
passes the supplier refusals (ii), whose own assumption ledger the run's
record carries (iii), and which records a model admissible exactly and the
``rigorous`` evaluation label (iv). Whether the run built the artefact CANNOT
BE READ OFF THE ARTEFACT: its version, validation results and ledger are data
an artefact written by hand can carry equally. So the part of the engine that
ran the receiver and docked its artefact says so, beside the artefact and
never inside it, and this record is that word (the interface's
``receiver_provenance`` input row: "it names each artifact by its
`module_version`").

THE WORD IS BOUND TO THE ROWS IT ATTESTS, not to the version alone. The
version is the installed receiver's on every artefact the run builds, so a
token naming only it would license any other exact, rigorous rows at that
version. The record therefore holds the rows the run attested with the
declaration's own fields set aside (:func:`imported_part`: the blocks below
the cutoff, the snap record and the handed reference, which are the
instance's declaration and no imported fact), and it names the rows it is
read with only where their imported part is exactly those.

THE PRECEDENT IS ``protocol_compiler.provenance.ChainProvenance``: a token the
run tier mints
(:func:`certiqs_key.runs.receiver_provenance.attest_receiver_provenance`),
read by one decision, the presence rule of A-RECV, and by nothing that forms a
number. It is no proof and no signature; a caller that constructs one asserts
what the run asserts. What this module still decides itself, on the artefact,
are the parts of ``req:recv-row-provenance`` that are data, (ii) and (iv)
(:func:`certiqs_key.reductions.emit.receiver_row_omitted_on_provenance`), and
where any of them fails, or the record does not name the rows read, the row
is emitted whatever this record says.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from certiqs_key.reductions.inputs import ReceiverArtifactRows

__all__ = ["ReceiverProvenance", "imported_part"]


def imported_part(rows: ReceiverArtifactRows) -> ReceiverArtifactRows:
    """Return ``rows`` with the declaration's own fields set aside.

    The photon-number blocks below the cutoff, the declaring party's snap
    record and the reference handed beside it are the instance's declaration
    (``foundations/def:declared-data`` (ii); ``req:recv-row-provenance``,
    lead-in), so they are emptied; every other field is the receiver
    artefact's, as docked.
    """
    return replace(rows, photon_blocks={}, instance_snap=None, handed_reference=None)


@dataclass(frozen=True)
class ReceiverProvenance:
    """The run's word that the receiver rows read are those of an artefact it built.

    ``req:recv-row-provenance`` (i) and (iii): the artefact is the installed
    receiver module's output in the same run, on the receiver declaration the
    run holds, handed to this module as it was emitted, and the run's record
    carries its own assumption ledger. ``attested`` is the imported part of the
    rows the run handed on (:func:`imported_part`); ``artifact_version`` is
    their declared version (the artefact's ``mathematical_spec_version``,
    ``receiver@<version>``), read off them. A reduction instance reads ONE
    receiver artefact
    (:attr:`~certiqs_key.reductions.inputs.ReductionCall.artifact_rows`), so
    the record names one; a run with several stations passes one per
    station's reduction.
    """

    attested: ReceiverArtifactRows

    def __post_init__(self) -> None:
        """Refuse a token that names no artefact."""
        if not str(self.artifact_version).strip():
            raise ValueError(
                "a ReceiverProvenance names the receiver artefact by its "
                "mathematical_spec_version (req:recv-row-provenance); got an "
                "empty version"
            )

    @classmethod
    def of(cls, rows: ReceiverArtifactRows) -> ReceiverProvenance:
        """Return the run's word on ``rows``, bound to their imported part."""
        return cls(imported_part(rows))

    @property
    def artifact_version(self) -> str:
        """The declared version of the attested artefact."""
        return self.attested.mathematical_spec_version

    def names(self, rows: ReceiverArtifactRows) -> bool:
        """Whether this record attests ``rows``: their imported part, exactly."""
        return imported_part(rows) == self.attested
