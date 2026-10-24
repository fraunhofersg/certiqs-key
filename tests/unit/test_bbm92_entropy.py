"""Frozen conditional BBM92 targets at actual two-station optical points.

The protocol coin and generation mass differ from the frozen toy. Only the
per-sifted entropy is compared; no optimizer minimum is inferred.
"""

from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest
from instances.bbm92.surface import default_config, preparation
from instances.common.honest.ideal_pair import IdealPair, honest_provider
from tests.oracles.registry_instances_bbm92 import (
    O_BBM92_B2_SYMMETRIC_ERROR,
    honest_point_bits,
)

from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    build_joint_maps,
    joint_choi_parametrization,
    joint_objective_value,
    joint_statistics,
)
from certiqs_key.runs.pipeline import Preparation


@pytest.mark.parametrize("alpha,expected", O_BBM92_B2_SYMMETRIC_ERROR.frozen_values)
@pytest.mark.parametrize("state", ["ideal", "independent", "honest"])
def test_actual_optical_bell_points_match_conditional_targets(
    alpha: float, expected: float, state: str
):
    config = default_config()
    config = replace(config, device={**config.device, "key_bases": "Z"})
    prepared = preparation(config)
    assert isinstance(prepared, Preparation)
    candidate = prepared.declaration
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
    maps = build_joint_maps(joint_choi_parametrization(declaration))
    point = {
        pair: np.zeros((maps.parametrization.block_dim(pair),) * 2, dtype=np.complex128)
        for pair in maps.joint_sectors
    }
    # Occupation order at each one-photon station is V,H. Simultaneous local
    # reversal preserves each Bell projector, including the Psi-minus sign.
    bell = np.asarray([[1, 0, 0, 1], [1, 0, 0, -1], [0, 1, 1, 0], [0, 1, -1, 0]], float)
    error = 1 / 32
    weights = (
        [1, 0, 0, 0]
        if state == "ideal"
        else [61 / 64, 1 / 64, 1 / 64, 1 / 64]
        if state == "honest"
        else [(1 - error) ** 2, error * (1 - error), error * (1 - error), error**2]
    )
    rho = sum(
        weight * np.outer(vector, vector) / 2
        for weight, vector in zip(weights, bell, strict=True)
    )
    sector = candidate.sectors.labels[
        len(candidate.measured_factors[1].sectors.labels) + 1
    ]
    point[(declaration.alice_sectors[0], sector)] = rho.astype(np.complex128)
    q = joint_statistics(maps, point)
    assert q["gen"] == pytest.approx(7 / 32, abs=1e-14)
    frequencies = honest_provider(
        IdealPair(visibility=Fraction(1) if state == "ideal" else Fraction(15, 16))
    )(candidate)
    assert q == pytest.approx(
        {key: float(value) for key, value in frequencies.items()}, abs=1e-14
    )
    value = joint_objective_value(maps, q, point, alpha)
    target = (
        1.0
        if state == "ideal"
        else honest_point_bits(error, alpha)
        if state == "honest"
        else expected
    )
    assert value / q["gen"] == pytest.approx(target, abs=2e-10)
    if state == "honest":
        assert (
            value / q["gen"] > expected
        )  # Honest point is not the independent-error point.
