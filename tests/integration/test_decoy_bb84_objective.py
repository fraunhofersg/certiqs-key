"""The frozen D-2/OT1 vacuum identity on the actual compiled instance.

This checks the objective at a named feasible point, not an optimized key rate.
The oracle identity is one bit per sifted generation round at every alpha;
the frozen registry's separate threshold-pair click numbers are not reused as
predictions for this passive four-detector apparatus.
"""

import pytest
from instances.decoy_bb84 import default_config, preparation

from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    build_joint_maps,
    joint_choi_parametrization,
    joint_objective_value,
    joint_statistics,
)
from certiqs_key.runs.pipeline import Preparation
from certiqs_key.solvers.frank_wolfe.joint_driver import joint_initial_point


@pytest.mark.parametrize("alpha", [1.05, 1.5, 2.0])
def test_compiled_vacuum_objective_is_one_bit_per_sifted_generation(alpha: float):
    config = default_config(device={"mu_signal": 0, "mu_weak": 0, "mu_vacuum": 0})
    prepared = preparation(config)
    assert isinstance(prepared, Preparation), prepared
    candidate = prepared.declaration
    # Maps do not read these placeholder acceptance frequencies; q below is
    # the directly evaluated distribution of the stated uniform Choi point.
    declaration = dock_general_candidate(
        candidate,
        acceptance_set=AcceptanceSet(
            geometry="singleton",
            frequencies=(
                1.0,
                *(0.0 for _ in candidate.acceptance_alphabet[1:]),
            ),
        ),
        rounds=config.rounds,
        parameters=config.parameters,
    )
    maps = build_joint_maps(joint_choi_parametrization(declaration))
    point = joint_initial_point(maps.parametrization)
    q = joint_statistics(maps, point)
    assert q["gen"] > 0
    assert joint_objective_value(maps, q, point, alpha) == pytest.approx(
        q["gen"], abs=2e-13
    )
