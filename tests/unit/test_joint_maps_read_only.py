"""Every array the joint caches read refuses an in-place write.

``JointMaps.statistics_map`` and ``JointMaps.branch_plan`` are built once from
the arrays held in the maps' read-only mappings, and so are the frames of the
parametrization. A mapping refuses a rebinding, but an element written into
one of its arrays after first use left the cached statistics map stale (open
item meat-core/joint-cache-arrays-and-pickling, demonstrated on the two-factor
toy). Each array is now built with ``write=False``; this walks every array the
mappings and frames hold, on a one-factor, a decoy-like ensemble and a
two-factor declaration, and checks that a write raises.
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import pytest
from tests.support.general_toys import (
    decoy_like_general,
    maps_of,
    qubit_bb84_general,
    two_factor_general,
)

from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.objective.joint import JointMaps

DECLARATIONS = {
    "qubit_bb84": lambda: qubit_bb84_general(),
    "decoy_like_ensemble": lambda: decoy_like_general(ensemble=True),
    "two_factor": lambda: two_factor_general(party_local=True),
}


def _arrays(maps: JointMaps) -> Iterator[tuple[str, np.ndarray]]:
    for key, operator in maps.statistics_operator.items():
        yield f"statistics_operator{key}", operator
    for key, branch in maps.branches.items():
        for klass in branch.classes:
            yield f"branches{key}.kraus", klass.kraus
            yield f"branches{key}.labels", klass.labels
    for sector, frame in maps.parametrization.frames.items():
        yield f"frames[{sector}].w", frame.w
        yield f"frames[{sector}].iota", frame.iota
        yield f"frames[{sector}].gram", frame.gram


@pytest.mark.parametrize("name", sorted(DECLARATIONS))
def test_every_array_in_the_joint_maps_is_read_only(name: str) -> None:
    declaration: GeneralDeclaration = DECLARATIONS[name]()
    maps = maps_of(declaration)
    found = list(_arrays(maps))
    assert any(label.startswith("branches") for label, _ in found)
    for label, array in found:
        assert not array.flags.writeable, label
        if array.size:
            with pytest.raises(ValueError, match="read-only"):
                array.flat[0] = array.flat[0]


def test_the_cached_statistics_map_cannot_be_made_stale() -> None:
    maps = maps_of(two_factor_general(party_local=True))
    before = maps.statistics_map.matrix.copy()
    key = next(iter(maps.statistics_operator))
    with pytest.raises(ValueError, match="read-only"):
        maps.statistics_operator[key][0, 0] += 1.0
    assert np.array_equal(maps.statistics_map.matrix, before)
