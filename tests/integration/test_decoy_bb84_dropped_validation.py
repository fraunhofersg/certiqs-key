"""OT5 on actual prepared decoy declarations, without an optimizer run.

The points below are constructed channels.  Their acceptance singletons are
chosen from their own evaluated statistics, and feasibility is checked after
docking.  They are not assertions about the honest optical model or minima of
the objective.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pytest
from instances.decoy_bb84 import default_config, preparation

from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    JointMaps,
    JointSector,
    build_joint_maps,
    evaluate_joint_branches,
    joint_choi_parametrization,
    joint_deficit,
    joint_objective_value,
    joint_statistics,
    normalise_dropped_set,
    rank_one_deficit,
    rank_one_sector,
)
from certiqs_key.meat_core.objective.joint_gradient import (
    joint_deficit_gradient,
    joint_gradient,
)
from certiqs_key.meat_core.objective.joint_rows import check_joint_feasible
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.runs.pipeline import Preparation
from certiqs_key.solvers.frank_wolfe.joint_driver import coupling_residuals

ALPHAS = (1.05, 1.5, 2.0)
ROUTES = ("encoded", "licensed", "licensed+two-sector")


@dataclass(frozen=True)
class _ActualPoint:
    declaration: GeneralDeclaration
    maps: JointMaps
    q: dict[str, float]
    choi: dict[JointSector, Matrix]
    qubit: str


def _bell_diagonal_choi() -> Matrix:
    vectors = np.asarray(
        [[1, 0, 0, 1], [1, 0, 0, -1], [0, 1, 1, 0], [0, 1, -1, 0]],
        dtype=np.complex128,
    ) / math.sqrt(2)
    weights = (0.5, 0.25, 0.125, 0.125)
    rho = sum(
        weight * np.outer(vector, vector.conj())
        for weight, vector in zip(weights, vectors, strict=True)
    )
    return np.asarray(2 * rho, dtype=np.complex128)


def _actual_point(route: str, *, spread_receiver_weight: bool) -> _ActualPoint:
    """Build the checked point used by the sector tests, with optional spread.

    The spread is used only on the encoded route.  Giving every receiver
    sector positive replacement-channel weight makes the full gradient's
    support hypothesis true.  The qubit-only form is the witness already used
    for the three-route sector identities.
    """
    config = default_config(device={"source_cutoff": 2, "route": route})
    prepared = preparation(config)
    assert isinstance(prepared, Preparation), prepared
    candidate = prepared.declaration

    def dock(frequencies: tuple[float, ...]) -> GeneralDeclaration:
        return dock_general_candidate(
            candidate,
            acceptance_set=AcceptanceSet(geometry="singleton", frequencies=frequencies),
            rounds=config.rounds,
            parameters=config.parameters,
        )

    initial = dock((1.0, *(0.0 for _ in candidate.acceptance_alphabet[1:])))
    maps = build_joint_maps(joint_choi_parametrization(initial))
    qubit = next(sector for sector, dim in initial.sector_dims.items() if dim == 2)
    point = {
        pair: np.zeros((maps.parametrization.block_dim(pair),) * 2, complex)
        for pair in maps.joint_sectors
    }

    if spread_receiver_weight:
        assert route == "encoded"
        receiver_weight = 1.0 / len(initial.sector_dims)
        for alice_sector, sector in maps.joint_sectors:
            alice_dim = initial.alice_dim_of(alice_sector)
            receiver_dim = initial.sector_dims[sector]
            point[alice_sector, sector] = receiver_weight * np.kron(
                np.eye(alice_dim), np.eye(receiver_dim) / receiver_dim
            )
    else:
        receiver_weight = 1.0
        for alice_sector in initial.alice_sectors:
            point[alice_sector, qubit] = np.kron(
                np.eye(initial.alice_dim_of(alice_sector)), np.eye(2) / 2
            )

    point["n1", qubit] = receiver_weight * _bell_diagonal_choi()
    q = joint_statistics(maps, point)
    assert min(q.values()) >= 0.0
    assert sum(q.values()) == pytest.approx(1.0, rel=0.0, abs=2e-14)

    declaration = dock(tuple(q[chat] for chat in initial.acceptance_values))
    assert (
        dict(
            zip(
                declaration.acceptance_values,
                declaration.acceptance_set.frequencies,
                strict=True,
            )
        )
        == q
    )
    support = tuple(chat for chat in declaration.acceptance_values if q[chat] > 0.0)
    maps = build_joint_maps(
        joint_choi_parametrization(declaration), acceptance_support=support
    )
    assert joint_statistics(maps, point) == q
    assert max(coupling_residuals(maps.parametrization, point).values()) < 2e-14
    check_joint_feasible(
        maps.parametrization,
        maps.parametrization.state_from_choi(point),
        tolerance=2e-13,
    )
    return _ActualPoint(declaration, maps, q, point, qubit)


@pytest.fixture(scope="module", params=ROUTES)
def actual_qubit_point(request: pytest.FixtureRequest) -> _ActualPoint:
    return _actual_point(str(request.param), spread_receiver_weight=False)


@pytest.fixture(scope="module")
def actual_gradient_point() -> _ActualPoint:
    return _actual_point("encoded", spread_receiver_weight=True)


def _flag_pair(point: _ActualPoint) -> tuple[str, JointSector]:
    flag = next(
        sector
        for sector in point.declaration.alice_sectors
        if sector.startswith("flag-")
    )
    return "gen", (flag, point.qubit)


@pytest.mark.parametrize("alpha", ALPHAS)
def test_actual_dropped_objective_identities_and_live_pair_bound(
    actual_qubit_point: _ActualPoint, alpha: float
) -> None:
    """``def:dropped`` and ``prop:drop-bound`` on every receiver route."""
    point = actual_qubit_point
    maps, q, choi = point.maps, point.q, point.choi
    base = joint_objective_value(maps, q, choi, alpha)

    empty = normalise_dropped_set(maps, [])
    assert joint_objective_value(maps, q, choi, alpha, dropped=empty) == base

    flag = _flag_pair(point)
    assert maps.key_inert[flag]
    flag_drop = normalise_dropped_set(maps, [flag])
    assert joint_objective_value(maps, q, choi, alpha, dropped=flag_drop) == base

    live = ("gen", ("n1", point.qubit))
    assert not maps.key_inert[live]
    assert joint_deficit(maps, live[0], live[1], choi[live[1]], alpha) < 0.0
    live_drop = normalise_dropped_set(maps, [live])
    base_values = evaluate_joint_branches(maps, choi, alpha)
    dropped_values = evaluate_joint_branches(maps, choi, alpha, dropped=live_drop)
    assert dropped_values["gen"].k > base_values["gen"].k
    assert joint_objective_value(maps, q, choi, alpha, dropped=live_drop) < base


@pytest.mark.parametrize("alpha", ALPHAS)
def test_actual_empty_and_key_inert_drops_are_gradient_identities(
    actual_gradient_point: _ActualPoint, alpha: float
) -> None:
    """The empty and flag drops leave every public gradient component equal."""
    point = actual_gradient_point
    maps, q, choi = point.maps, point.q, point.choi
    empty = normalise_dropped_set(maps, [])
    flag = _flag_pair(point)
    assert maps.key_inert[flag]
    flag_drop = normalise_dropped_set(maps, [flag])

    base = joint_gradient(maps, q, choi, alpha)
    empty_gradient = joint_gradient(maps, q, choi, alpha, dropped=empty)
    flag_gradient = joint_gradient(maps, q, choi, alpha, dropped=flag_drop)

    assert empty_gradient.q == base.q
    assert flag_gradient.q == base.q
    for pair in maps.joint_sectors:
        assert np.array_equal(empty_gradient.blocks[pair], base.blocks[pair])
        assert np.array_equal(flag_gradient.blocks[pair], base.blocks[pair])
    assert empty_gradient.dropped_pieces == ()
    assert flag_gradient.dropped_pieces == (flag,)
    assert flag in base.key_inert_pieces


@pytest.mark.parametrize("alpha", ALPHAS)
def test_actual_rank_one_closed_form_has_the_generic_gradient(
    actual_gradient_point: _ActualPoint, alpha: float
) -> None:
    """Differentiate the public closed deficit along a Hermitian basis."""
    point = actual_gradient_point
    maps, choi = point.maps, point.choi
    pair = ("n0", point.qubit)
    data = rank_one_sector(maps, pair[0])
    assert data is not None
    assert not maps.key_inert[("gen", pair)]

    generic = joint_deficit_gradient(maps, "gen", pair, choi[pair], alpha)
    directions = (
        np.eye(2, dtype=np.complex128),
        np.diag([1.0, -1.0]).astype(np.complex128),
        np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128),
        np.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128),
    )
    step = 2.0**-20
    for direction in directions:
        plus = rank_one_deficit(
            maps, "gen", pair, choi[pair] + step * direction, alpha, data
        )
        minus = rank_one_deficit(
            maps, "gen", pair, choi[pair] - step * direction, alpha, data
        )
        closed_directional_derivative = (plus - minus) / (2 * step)
        generic_directional_derivative = float(np.trace(generic @ direction).real)
        assert closed_directional_derivative == pytest.approx(
            generic_directional_derivative, rel=0.0, abs=2e-10
        )
