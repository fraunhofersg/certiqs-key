"""OT2/3/4 on the actual prepared source and supplier receiver artifacts.

These are channel point evaluations, not honest-model or optimizer minima.
The acceptance singleton is explicitly chosen from the evaluated channel,
and all state constraints are checked before calling the pair feasible.
The ideal licensed+two-sector route emits no extra Eq. 27 row and equals licensed;
the three entry points exercise two distinct constraint systems.
"""

import math

import numpy as np
import pytest
from instances.decoy_bb84 import default_config, preparation

from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    build_joint_maps,
    joint_choi_parametrization,
    joint_deficit,
    joint_statistics,
    rank_one_deficit,
    rank_one_sector,
)
from certiqs_key.meat_core.objective.joint_rows import check_joint_feasible
from certiqs_key.runs.pipeline import Preparation
from certiqs_key.solvers.frank_wolfe.joint_driver import coupling_residuals


@pytest.mark.parametrize("route", ["encoded", "licensed", "licensed+two-sector"])
@pytest.mark.parametrize("alpha", [1.05, 1.5, 2.0])
def test_actual_source_flag_rank_one_and_bell_sector_identities(
    route: str, alpha: float
):
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

    # Only used to form the maps; replaced by the actual point's frequencies
    # below, before any claim of acceptance-set membership.
    initial = dock((1.0, *(0.0 for _ in candidate.acceptance_alphabet[1:])))
    maps = build_joint_maps(joint_choi_parametrization(initial))
    qubit = next(s for s, dim in initial.sector_dims.items() if dim == 2)
    point = {
        pair: np.zeros((maps.parametrization.block_dim(pair),) * 2, complex)
        for pair in maps.joint_sectors
    }
    for t in initial.alice_sectors:
        # Replacement channel into the physical one-photon maximally mixed
        # state. It satisfies each receiver constraint as explicitly checked.
        point[t, qubit] = np.kron(np.eye(initial.alice_dim_of(t)), np.eye(2) / 2)
    bell_vectors = np.asarray(
        [[1, 0, 0, 1], [1, 0, 0, -1], [0, 1, 1, 0], [0, 1, -1, 0]], complex
    ) / math.sqrt(2)
    lambdas = (0.5, 0.25, 0.125, 0.125)
    rho = sum(
        p * np.outer(v, v.conj()) for p, v in zip(lambdas, bell_vectors, strict=True)
    )
    point["n1", qubit] = 2 * rho  # trace-preserving Bell-diagonal qubit channel
    q = joint_statistics(maps, point)
    assert min(q.values()) >= 0
    assert sum(q.values()) == pytest.approx(1, rel=0, abs=2e-14)
    declaration = dock(tuple(q[c] for c in initial.acceptance_values))
    maps = build_joint_maps(joint_choi_parametrization(declaration))
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
    assert joint_statistics(maps, point) == q
    assert max(coupling_residuals(maps.parametrization, point).values()) < 2e-14
    states = maps.parametrization.state_from_choi(point)
    check_joint_feasible(maps.parametrization, states, tolerance=2e-13)
    assert bool(declaration.constraint_list) == (route != "encoded")

    # OT2: every carried polarization/tail flag has a fixed generation bit
    # or contributes no generation. Evaluate the generic matrix route too.
    flags = [t for t in declaration.alice_sectors if t.startswith(("flag-", "tail-"))]
    assert any(t.startswith("flag-") for t in flags)
    assert any(t.startswith("tail-") for t in flags)
    for t in ("n0", *flags):
        data = rank_one_sector(maps, t)
        assert data is not None
        pair = (t, qubit)
        state = states[pair]
        sigma = state.reshape(1, 2, 1, 2)[0, :, 0, :]
        assert np.allclose(
            state, np.kron(np.outer(data.vector, data.vector.conj()), sigma)
        )
        generic = joint_deficit(maps, "gen", pair, point[pair], alpha)
        closed = rank_one_deficit(maps, "gen", pair, point[pair], alpha, data)
        assert generic == pytest.approx(closed, rel=0, abs=2e-14)
        if t in flags:
            assert generic == pytest.approx(0, rel=0, abs=2e-14)

    # OT4 uses the *actual declared* generation weight on n1 and the
    # supplier's Bob Z-arm probability, not a frozen toy click probability.
    pair = ("n1", qubit)
    g = float(np.real(np.trace(maps.statistics_operator["gen", pair] @ point[pair])))
    assert g > 0
    n_h = declaration.alice_block("gen-signal-H", "n1")
    n_v = declaration.alice_block("gen-signal-V", "n1")
    gen_weight = float(np.trace(n_h + n_v).real)
    assert np.allclose(n_h, np.diag([gen_weight / 2, 0]), atol=0, rtol=0)
    assert np.allclose(n_v, np.diag([0, gen_weight / 2]), atol=0, rtol=0)
    _, h, v, _, _, _ = declaration.bob_outcomes
    z_sum = declaration.bob_block(h, qubit) + declaration.bob_block(v, qubit)
    z_probability = float(np.trace(z_sum).real) / 2
    assert np.allclose(z_sum, z_probability * np.eye(2), atol=0, rtol=0)
    assert g == pytest.approx(gen_weight * z_probability, rel=0, abs=2e-15)
    power_sum = sum(
        (lambdas[i] ** (1 / alpha) + lambdas[i + 1] ** (1 / alpha)) ** alpha
        for i in (0, 2)
    )
    expected = g * (2 ** (1 - alpha) * power_sum - 1)
    assert joint_deficit(maps, "gen", pair, point[pair], alpha) == pytest.approx(
        expected, rel=0, abs=3e-13
    )
