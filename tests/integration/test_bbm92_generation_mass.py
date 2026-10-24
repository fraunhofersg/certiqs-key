"""B-5 on the actual compiled BBM92 instance: the generation mass is ``1 - gamma``.

``O-BBM92-B5-COIN-MASS`` freezes the identity on the toy: the test coin enters
only through the weights inside the POVM elements (``def:weighted``, A-TSM),
so the summed mass of every generation-branch letter is ``1 - gamma`` at EVERY
feasible state, while the sifted letter ``gen`` alone moves with the state.
The existing BBM92 tests check ``gen`` at the honest point and total
normalisation; neither is the state-independent sum, which is what this file
checks.

The states are random points of the untrusted coupling set (trace one), which
contains the feasible set, so a property "at every feasible state" is tested
on a superset. Binary64 throughout; the tolerance is rounding, not modelling.

``merged-discard`` is not tested and cannot be: it pools the generation
failures with the test discards into one value ``disc``, so the generation
branch is not a union of its acceptance values there. The test below asserts
that pooling, so a change to that map fails here rather than passing silently.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from instances.bbm92.surface import default_config, preparation
from tests.support.general_toys import random_choi_point

from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    JointMaps,
    build_joint_maps,
    joint_choi_parametrization,
    joint_statistics,
)
from certiqs_key.runs.pipeline import Preparation

_SEEDS = (0, 1, 2, 3)


def _maps(acceptance_map: str, test_fraction: Fraction) -> JointMaps:
    config = default_config()
    config = config.with_(
        device={
            **config.device,
            "acceptance_map": acceptance_map,
            "test_fraction": test_fraction,
        }
    )
    prepared = preparation(config)
    assert isinstance(prepared, Preparation), prepared
    candidate = prepared.declaration
    # The maps do not read the acceptance frequencies; any singleton serves.
    declaration = dock_general_candidate(
        candidate,
        acceptance_set=AcceptanceSet(
            geometry="singleton",
            frequencies=tuple(
                1.0 if x == "gen" else 0.0 for x in candidate.acceptance_alphabet
            ),
        ),
        rounds=config.rounds,
        parameters=config.parameters,
    )
    assert not declaration.is_trusted_source
    return build_joint_maps(joint_choi_parametrization(declaration))


def _generation_values(maps: JointMaps) -> list[str]:
    """Return the acceptance values of the generation branch.

    ``instances/bbm92/device.acceptance_label``: sifted generation is ``gen``
    and an unsifted generation transcript keeps its announcement,
    ``gen:<class>|<second>``, under both resolved maps.
    """
    return [
        value
        for value in maps.declaration.acceptance_values
        if value == "gen" or value.startswith("gen:")
    ]


@pytest.mark.parametrize("test_fraction", [Fraction(1, 8), Fraction(1, 4)])
@pytest.mark.parametrize("acceptance_map", ["pair-resolved", "announcement-resolved"])
def test_generation_branch_mass_is_one_minus_gamma_at_every_state(
    acceptance_map: str, test_fraction: Fraction
) -> None:
    maps = _maps(acceptance_map, test_fraction)
    generation = _generation_values(maps)
    assert "gen" in generation and len(generation) > 1
    sifted = []
    for seed in _SEEDS:
        point = random_choi_point(maps.parametrization, seed)
        q = joint_statistics(maps, point)
        assert sum(q.values()) == pytest.approx(1.0, abs=1e-12)
        assert sum(q[value] for value in generation) == pytest.approx(
            float(1 - test_fraction), abs=1e-12
        )
        sifted.append(q["gen"])
    # The split inside the branch is state dependent: pinning ``gen`` alone
    # would be pinning a state, not the declaration.
    assert max(sifted) - min(sifted) > 1e-3


def test_merged_discard_pools_generation_failures_with_test_discards() -> None:
    maps = _maps("merged-discard", Fraction(1, 8))
    values = maps.declaration.acceptance_values
    assert "disc" in values
    assert _generation_values(maps) == ["gen"]
