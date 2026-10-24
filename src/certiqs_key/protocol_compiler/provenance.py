"""The run's word on where a presented chain came from: ``chain_provenance``.

``req:link-row-provenance``: the compiler omits the row of ``ass:link``
(A-LINK) from its ledger only on Band A, or where the source segment is empty
and EVERY MEASURED FACTOR's receiver segment is the single exact instance link
of a reductions artefact emitted IN THE SAME RUN, docked with the artefact's
declared model or exactly its compression as that factor's physical receiver
family (per factor; at several factors the
joint discharge is ``reductions/thm:emitted-product`` (ii), (iii) with A-MEAS
(iv), ``rem:obligations-discharged``). Whether a chain is such a link CANNOT
BE READ OFF THE SPECIFICATION: its link types and status tags are data a
specification written by hand can carry equally (``def:spec`` (c)). So the
part of the engine that ran the reductions module and docked its artefacts
says so, beside the specification and never inside it, and this record is
that word (the interface's ``chain_provenance`` input row: "it names each
such artefact (module version and link id), per factor").

THE PRECEDENT IS ``meat_core.provenance.CompilerEmission``: a token the run
tier mints, read by one decision and by nothing that forms a number. It is no
proof and no signature; a caller that constructs one asserts what the run
asserts. What the compiler still decides itself, on the presented chain, are
the parts of ``req:link-row-provenance`` (ii) that are data (for every
measured factor one link, status exact, no channel supplied, the identity
outcome correspondence; an empty source segment), and where any of them fails
or the record does not name every factor the row is emitted whatever this
record says (:func:`certiqs_key.protocol_compiler.compile.link_row_discharged`).
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ChainProvenance", "FactorProvenance"]


@dataclass(frozen=True)
class FactorProvenance:
    """The run's word on one measured factor's receiver segment.

    ``factor`` is the measured factor's label (its ``factor_label``, or the
    position default ``f<position>``); ``artifact_version`` the artefact's
    ``mathematical_spec_version`` (``reductions@<version>``) and ``link_id``
    its instance link's id. The compiler compares ``link_id`` with that
    factor's presented link and decides nothing else from this record.
    """

    factor: str
    artifact_version: str
    link_id: str

    def __post_init__(self) -> None:
        """Refuse a token that names no factor, no artefact or no link."""
        if not all(
            str(value).strip()
            for value in (self.factor, self.artifact_version, self.link_id)
        ):
            raise ValueError(
                "a FactorProvenance names the measured factor, the reductions "
                "artefact (its mathematical_spec_version) and its instance "
                "link's id (req:link-row-provenance); got an empty field"
            )


@dataclass(frozen=True)
class ChainProvenance:
    """The run's word that each presented receiver link is an in-run instance link.

    ``req:link-row-provenance`` (ii): each measured factor's receiver segment
    is the instance link of a reductions artefact emitted in the same run,
    docked by that run, and that factor's physical receiver family is that
    artefact's declared model or exactly its compression onto the presented
    physical receiver space; the run passes it only for instances for which
    ``rem:obligations-discharged`` names the claim making the docked family
    that compression (the flat instance,
    ``reductions/wpfss/prop:flat-instance``). One :class:`FactorProvenance`
    per factor the run attests, each factor once.
    """

    factors: tuple[FactorProvenance, ...]

    def __post_init__(self) -> None:
        """Refuse a token that attests nothing or one factor twice."""
        if not self.factors:
            raise ValueError("a ChainProvenance attests at least one measured factor")
        names = [item.factor for item in self.factors]
        if len(set(names)) != len(names):
            raise ValueError(f"a ChainProvenance names a factor twice: {names}")

    def link_of(self, factor: str) -> str | None:
        """Return the attested link id of ``factor``, or ``None`` if not named."""
        return next(
            (item.link_id for item in self.factors if item.factor == factor), None
        )
