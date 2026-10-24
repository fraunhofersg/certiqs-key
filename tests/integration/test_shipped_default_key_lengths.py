"""The shipped defaults keep their key lengths.

A REGRESSION SNAPSHOT, NOT AN ORACLE (PRINCIPLES.md 2.3 is not engaged): the
numbers are what the engine computes at each instance's own default
configuration and solver budget.

WHY IT EXISTS. The encoded route carries no positive weight, so a shipped
default does not collapse to key 0 at its own budget (an instance's
certified emission weights, carried by added flag sectors, once did) and its
weights are disclosed. This test keeps that visible: a change that moves a
shipped default's key length fails here and is named.

Slow: decoy_bb84's default solve takes about a quarter of an hour.
"""

from __future__ import annotations

import importlib
import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from certiqs_key.runs.record import record_run

pytestmark = [pytest.mark.slow, pytest.mark.requires_qics]
pytest.importorskip("qics")

#: Per instance: the key length at its own defaults, and whether the run rests
#: on A-SNAP. The first-order bound is formed on the reference companion
#: (meat-core/frank-wolfe/req:bracket-on-reference), which bypasses the
#: emission normaliser; an instance's moved data sectors and instance blocks
#: are evaluated off their snap, so no shipped default rests on A-SNAP. The
#: emitted weight is the enclosed one rounded down (receiver/req:rigorous-
#: weight), with no eps_eig where the exact window binds, so the declaration
#: and the search depend on it; each key is the first-order key of that
#: declaration, and the run certifies at it. Where a companion is admitted,
#: the polish continues the search on it (req:bracket-on-reference (i)), which
#: raised optical_bb84 from 1809 and decoy_bb84 from 9109457.
DEFAULTS: dict[str, tuple[int, bool]] = {
    "optical_bb84": (1810, False),
    "bb84": (1814, False),
    "decoy_bb84": (9127427, False),
    "bbm92": (40193105, False),
}


def _record(name: str) -> dict[str, Any]:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = importlib.import_module(f"instances.{name}.surface")
    config = surface.default_config()
    with tempfile.TemporaryDirectory() as tmp:
        outcome = surface.runner(QicsSectorChoiOracle(), Path(tmp), created_by="t")(
            config, 0
        )
        record: dict[str, Any] = record_run(outcome, config, created_by="t").as_dict()
    return json.loads(json.dumps(record))


@pytest.mark.parametrize("name", sorted(DEFAULTS))
def test_the_shipped_default_key_length_is_unchanged(name: str) -> None:
    key, rests = DEFAULTS[name]
    payload = _record(name)["payload"]
    assert payload["refused"] is False
    assert payload["stages"]["key_rate"]["key_length"] == key
    engaged = {e["short_id"] for e in payload["assumption_manifest"]["assumptions"]}
    assert ("A-SNAP" in engaged) is rests
