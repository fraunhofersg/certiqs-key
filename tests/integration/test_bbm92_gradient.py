"""Actual BBM92 disk declaration: exact-zero rows and supported gradients."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from instances.bbm92.surface import default_config, preparation
from instances.common.honest.ideal_pair import IdealPair, honest_provider

from certiqs_key.domain.bundle import read_bundle, write_bundle
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    build_joint_maps,
    joint_choi_parametrization,
    joint_objective_value,
)
from certiqs_key.meat_core.objective.joint_gradient import joint_gradient
from certiqs_key.runs.general_wire import build_general_bundle
from certiqs_key.runs.pipeline import Preparation
from certiqs_key.solvers.frank_wolfe.joint_driver import joint_initial_point


def test_bbm92_disk_maps_zero_rows_and_supported_direction(tmp_path: Path):
    config = default_config()
    prepared = preparation(config)
    assert isinstance(prepared, Preparation)
    candidate = prepared.declaration
    frequencies = honest_provider(IdealPair())(candidate)
    declaration = dock_general_candidate(
        candidate,
        acceptance_set=AcceptanceSet(
            geometry="singleton",
            frequencies=tuple(
                float(frequencies[c]) for c in candidate.acceptance_alphabet
            ),
        ),
        rounds=config.rounds,
        parameters=config.parameters,
    )
    bundle, _ = build_general_bundle(
        declaration,
        alice_announcements=(),
        bob_announcements=(),
        reduction_chain=prepared.compilation.reduction_chain_record,
        created_by="bbm92-gradient-test",
    )
    write_bundle(tmp_path / "bundle", bundle)
    reread = declaration_from_bundle(read_bundle(tmp_path / "bundle"))
    assert isinstance(reread, GeneralDeclaration)
    q = dict(
        zip(reread.acceptance_values, reread.acceptance_set.frequencies, strict=True)
    )
    maps = build_joint_maps(
        joint_choi_parametrization(reread),
        acceptance_support=tuple(c for c, v in q.items() if v > 0),
    )
    point = joint_initial_point(maps.parametrization)
    assert any(
        klass.kraus.size == 0
        for branch in maps.branches.values()
        for klass in branch.classes
    )
    # An independent full-space reference appends exactly zero rows. Their
    # labels are immaterial, since pinching and trace powers leave them zero.
    full = replace(
        maps,
        branches={
            key: replace(
                branch,
                classes=tuple(
                    replace(
                        klass,
                        kraus=np.vstack(
                            (klass.kraus, np.zeros((1, klass.kraus.shape[1])))
                        ),
                        labels=np.append(klass.labels, 0),
                    )
                    for klass in branch.classes
                ),
            )
            for key, branch in maps.branches.items()
        },
    )
    alpha = 1.5
    assert joint_objective_value(maps, q, point, alpha) == pytest.approx(
        joint_objective_value(full, q, point, alpha), abs=1e-12
    )
    gradient = joint_gradient(maps, q, point, alpha)
    pair = next(p for p in maps.joint_sectors if maps.parametrization.block_dim(p) == 4)
    direction = np.diag([1.0, -1.0, 0.0, 0.0]).astype(np.complex128)
    step = 1e-7
    plus = {**point, pair: point[pair] + step * direction}
    minus = {**point, pair: point[pair] - step * direction}
    assert np.linalg.eigvalsh(minus[pair]).min() > 0
    numerical = (
        joint_objective_value(maps, q, plus, alpha)
        - joint_objective_value(maps, q, minus, alpha)
    ) / (2 * step)
    analytic = float(np.trace(gradient.blocks[pair] @ direction).real)
    assert abs(analytic) > 1e-4
    assert analytic == pytest.approx(numerical, abs=2e-7)
