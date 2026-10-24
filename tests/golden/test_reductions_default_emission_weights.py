"""What the emission normaliser does to each shipped instance at its defaults.

``reductions/def:emitnorm`` (1)--(3) and ``reductions/req:emission-record``,
read at every instance under ``instances/`` whose default preparation forms a
reductions artefact (``bb84`` and ``bbm92`` form none; ``declared`` has no
default preparation). Every number is derived by hand below and never read
from the code under test.

This file pins which classes are kept and how the moved ones are snapped by
``def:emitnorm``'s fidelity-first snap. No emission weight is computed, so
none is pinned.

* ``optical_bb84`` and ``decoy_bb84``: every class of the handed datum has
  denominators within ``2^-40`` at ``kappa = 40``, so every class is KEPT
  (step (1)) and nothing is moved.

An instance that moves classes has its hand derivation and its case in its
own test file where it goes with a removable submodule.
"""

from __future__ import annotations

import importlib
from fractions import Fraction as F
from typing import Any

import pytest

#: Hand-derived above: per data sector, the moved classes with their step,
#: their ``w`` and their hosts.
EXPECTED_MOVED: dict[str, dict[int, tuple[tuple[str, F, tuple[str, ...]], ...]]] = {
    "optical_bb84": {},
    "decoy_bb84": {},
}


def moved_and_statuses(
    name: str,
) -> tuple[dict[int, tuple[tuple[str, F, tuple[str, ...]], ...]], dict[Any, Any]]:
    """Return an instance's moved classes per data sector, and its block statuses.

    ``def:emitnorm`` (1), (2) at the defaults; ``req:emission-record``. The
    record's last-resort sectors are asserted empty on the way.
    """
    surface = importlib.import_module(f"instances.{name}.surface")
    outcome = surface.preparation(surface.default_config())
    artifact = outcome.reduction_artifact
    assert artifact is not None
    record = artifact.emission_record
    moved = {
        block.block_index: tuple(
            (str(snap.step), snap.mixing_weight, snap.hosts) for snap in block.moved
        )
        for block in record.blocks
    }
    assert record.last_resort_sectors == frozenset()
    adaptation = outcome.rows_adaptation
    assert adaptation is not None
    statuses = {
        (snap["setting"], block["block"]): (
            block["status"],
            block["handed_reference_kind"],
        )
        for station in adaptation.get("stations") or [adaptation]
        for snap in station["measurement_snaps"]
        for block in snap["blocks"]
    }
    return {k: v for k, v in moved.items() if v}, statuses


@pytest.mark.contract
@pytest.mark.parametrize("name", sorted(EXPECTED_MOVED))
def test_the_default_preparation_keeps_or_moves_its_classes(name: str) -> None:
    """``def:emitnorm`` (1), (2) at the defaults; ``req:emission-record``."""
    moved, statuses = moved_and_statuses(name)
    assert moved == EXPECTED_MOVED[name]
    assert {status for status, _ in statuses.values()} == {"kept"}
