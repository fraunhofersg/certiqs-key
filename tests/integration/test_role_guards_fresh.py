"""Guards G1-G7 of the PM/EB roles over fresh runs of the report examples.

WHY THIS EXISTS. The committed report examples are regenerated at a commit,
so a guard over them reads whatever engine wrote them
(``tests/unit/test_role_guards.py``). Here each example's configurations are
run again with the CURRENT engine (the same instance, document and solver
budget as ``runs/report_examples/generate.py``, nothing written) and every
resulting record must pass the guards of ``tests/support/role_guards.py``
(no trivial premise, no source premise on an
untrusted run, station premises naming their own party, presuppositions
met, one laboratory row per party, roots that follow the source mode). An
emitter change that brings back a prepare-and-measure reading on an
entanglement-based run fails here before the examples are regenerated.

COST. A fresh run of an example takes 2 to 9 seconds (on a development
machine; the examples' solver budget is five Frank-Wolfe iterations): bb84 and
bbm92, one prepare-and-measure and one entanglement-based run, and
document-bbm92_choice_at_bob, which keeps G6 (a public choice at the second
station alone) on a real run, are in the default tier; the other examples are
marked ``slow``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from runs.report_examples.generate import CREATED_BY, EXAMPLES, Example
from tests.support.role_guards import checked, violations

pytestmark = pytest.mark.requires_qics

#: The examples run in the default tier; the rest are ``slow``.
DEFAULT_TIER = frozenset({"bb84", "bbm92", "document-bbm92_choice_at_bob"})


def _fresh_records(example: Example, scratch: Path) -> list[dict[str, Any]]:
    """Run one example's configurations with the current engine; write nothing."""
    from instances import surface_of

    from certiqs_key.runs.surface import InstanceIdentity
    from certiqs_key.runs.sweep import sweep
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = (
        surface_of(example.instance) if example.document is None
        else example.document()
    )
    identity = InstanceIdentity(surface.DESCRIPTOR, tuple(surface.PARAMETERS))
    runner = surface.runner(QicsSectorChoiOracle(), scratch, created_by=CREATED_BY)
    swept = sweep(example.configs(surface), runner, created_by=CREATED_BY,
                  instance=identity)
    return [point.record.as_dict() for point in swept]


@pytest.mark.parametrize(
    "example",
    [
        pytest.param(example, id=example.name,
                     marks=() if example.name in DEFAULT_TIER else pytest.mark.slow)
        for example in EXAMPLES
    ],
)
def test_a_fresh_run_passes_the_guards(example: Example, tmp_path: Path) -> None:
    for index, record in enumerate(_fresh_records(example, tmp_path)):
        found = violations(checked(record))
        assert found == {}, f"{example.name} point {index}: {found}"
