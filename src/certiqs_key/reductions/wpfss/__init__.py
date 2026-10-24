"""``wpfss``: the flag-state squasher with certified weights.

ONE SQUASHER, AND IT IS A SUBMODULE. An ideal qubit protocol never needs it,
and both corpus notes squash with the plain flag-state squasher plus
constraints, so it is not the last squasher the core will host. What it owns:
the weight-preserving and flag-state targets, the weight route of
``def:weight-route`` and ``prop:route``, the six fail-closed rows about the
dark-count matrix and the routed weights, and the FLAT reduction instance --
the emission with no branches, ``prop:flat-instance`` and ``cor:emitted-flat``.

The entry point is :func:`reduce_flat`.
"""

from __future__ import annotations

from certiqs_key.reductions.wpfss.api import (
    FLAT_ROWS,
    FlatInstanceBuilder,
    reduce_flat,
)

__all__ = ["FLAT_ROWS", "FlatInstanceBuilder", "reduce_flat"]
