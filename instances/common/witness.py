"""The library's feasibility witnesses, picked by topology.

WHY WITNESSES ARE LIBRARY AND NOT FLAGGED. Theorem ``thm:feasibility`` (i)
proves the compiler's own default witness feasible only for an empty
constraint list; a docked reduction brings entries, and the compiler then asks
to be SHOWN a feasible state ("I WAS NOT SHOWN A FEASIBLE STATE, never THERE IS
NONE", ``rem:completeness``). The three instances that dock showed one each,
and a document with ``feasibility_witness: auto`` gets the one its topology
calls for. The compiler verifies every witness, so a library witness is the
instances' own construction and no premise of the user's.

- :func:`below_cutoff` -- one optical station without source links:
  ``tau_A (x) 1_{<=N}/d_{<=N}``, the optical BB84 instance's
  (:func:`instances.common.passive_device.below_cutoff_witness`).
- :func:`vacuum_output` -- one station behind a source with links (a
  ``wcp_decoy`` source): the replacement channel that outputs vacuum, the
  decoy BB84 instance's.
- :func:`factor_uniform_below_cutoff` -- two stations with a factor emission:
  the uniform state on the product of the stations' photon-number blocks
  below their cutoffs, bbm92's.

The instance templates use these. Where a topology's preconditions do not
hold, each returns ``None``: the specification then carries no witness and the
compiler decides with its own default.
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from itertools import product

from certiqs_key.foundations.blocks import (
    BlockOperator,
    JointBlockOperator,
    SectorStructure,
)
from certiqs_key.foundations.exact import Matrix, identity, scale, zeros
from certiqs_key.protocol_compiler.spec import SourcePart
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.factors import FactorEmission
from instances.common.passive_device import below_cutoff_witness

__all__ = ["below_cutoff", "factor_uniform_below_cutoff", "vacuum_output"]


def below_cutoff(
    source: SourcePart, sectors: SectorStructure, preserved: int
) -> JointBlockOperator | None:
    """Return ``omega* = tau_A (x) 1_{<=N}/d_{<=N}`` on the emitted sector map.

    ``tau_A`` is the source artefact's declared marginal; an untrusted source
    with ``d_A = 1`` declares none, and its marginal is the number one.
    """
    marginal: Matrix | None = source.marginal
    if marginal is None:
        if source.alice_dim != 1:
            return None
        marginal = identity(1)
    return below_cutoff_witness(
        marginal, sectors, alice_dim=source.alice_dim, preserved=preserved
    )


def vacuum_output(
    source: SourcePart, sectors: SectorStructure
) -> JointBlockOperator | None:
    """Return the vacuum-output witness of a source with links (decoy BB84's).

    A replacement channel outputting vacuum is feasible for every source
    sector: each certified receiver constraint holds on physical vacuum. The
    compiler verifies this witness, never infers its feasibility.
    """
    marginal = source.marginal_blocks
    if marginal is None:
        # The d_A = 1 vacuum artefact has no required A-SRC licence; its one
        # declared marginal matrix is already the sole sector block.
        if source.alice_sectors.count != 1 or source.marginal is None:
            return None
        marginal = BlockOperator.of(source.alice_sectors, [source.marginal])
    if not sectors.dims or sectors.dims[0] != 1:
        return None
    return JointBlockOperator.of(
        sectors,
        source.alice_sectors,
        [
            tau if index == 0 else zeros(len(tau) * dim, len(tau) * dim)
            for tau in marginal.blocks
            for index, dim in enumerate(sectors.dims)
        ],
    )


def factor_uniform_below_cutoff(
    emission: FactorEmission, reductions: Sequence[ProofReductionArtifact]
) -> JointBlockOperator | None:
    """Return bbm92's witness: uniform on the stations' blocks below the cutoffs.

    A two-factor construction: with three or more stations a
    document's witness is ``none`` or explicit. The source is untrusted with
    ``d_A = 1``, so Alice's leg is the number one.
    """
    maps = emission.sector_map.factors
    if len(maps) != 2 or len(reductions) != 2:
        return None
    physical_counts = tuple(
        reduction.source_descriptor.channel_grading.cutoff + 1
        for reduction in reductions
    )
    normalization = (
        reductions[0].source_descriptor.channel_grading.preserved_dimension
        * reductions[1].source_descriptor.channel_grading.preserved_dimension
    )
    return JointBlockOperator.of(
        emission.family.flattened(),
        1,
        tuple(
            scale(Fraction(1, normalization), identity(da * db))
            if ia < physical_counts[0] and ib < physical_counts[1]
            else zeros(da * db)
            for (ia, da), (ib, db) in product(
                enumerate(maps[0].sectors.dims),
                enumerate(maps[1].sectors.dims),
            )
        ),
    )
