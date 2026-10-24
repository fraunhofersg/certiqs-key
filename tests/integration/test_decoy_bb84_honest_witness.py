"""A finite source/flag channel matching the actual nonvacuum honest table.

Restricted to ideal detectors, zero misalignment and N_ent=N_src=N_rec=1.
The residual tail carries all discarded Poisson mass, including downward
rounding. Every raw probability, state constraint and actual Bernstein
acceptance bound is checked. This is a numerical witness, not an exact
certificate or an optimized key rate. See the actual-sector witness report.
At these ideal parameters licensed+two-sector equals licensed: no Eq. 27 row is
emitted, so three route entry points cover two distinct constraint systems.
"""

from decimal import Decimal, localcontext
from fractions import Fraction as F

import numpy as np
import pytest
from instances.decoy_bb84 import default_config, preparation

from certiqs_key.meat_core.docking_statistics import acceptance_set_record
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    build_joint_maps,
    joint_choi_parametrization,
    joint_statistics,
)
from certiqs_key.meat_core.objective.joint_rows import check_joint_feasible
from certiqs_key.runs.pipeline import Preparation
from certiqs_key.solvers.frank_wolfe.joint_driver import coupling_residuals
from certiqs_key.statistics import AcceptanceConstruction, AcceptanceRequest, construct


@pytest.mark.parametrize("route", ["encoded", "licensed", "licensed+two-sector"])
@pytest.mark.parametrize("transmission", [F(1, 10), F(1, 100)])
def test_finite_channel_matches_every_honest_raw_probability_and_constraint(
    route: str, transmission: F
) -> None:
    config = default_config(
        model={"transmittance": transmission, "misalignment": 0},
        device={"source_cutoff": 1, "route": route, "acceptance_map": "pair-resolved"},
    )
    prepared = preparation(config)
    assert isinstance(prepared, Preparation), prepared
    candidate = prepared.declaration
    raw = prepared.raw_joint_distribution
    assert raw is not None
    honest = dict.fromkeys(candidate.acceptance_alphabet, F())
    for (x, v), p in raw.items():
        honest[candidate.acceptance_value(candidate.announcement(x, v))] += p
    acceptance = construct(
        AcceptanceRequest(
            alphabet=candidate.acceptance_alphabet,
            honest=honest,
            rounds=config.rounds,
            budget=config.completeness_budget,
            endpoint_rule=config.endpoint_rule,
        )
    )
    assert isinstance(acceptance, AcceptanceConstruction), acceptance
    declaration = dock_general_candidate(
        candidate,
        acceptance_set=acceptance_set_record(acceptance.acceptance_set),
        rounds=config.rounds,
        parameters=config.parameters,
    )
    maps = build_joint_maps(joint_choi_parametrization(declaration))
    sectors = declaration.sector_dims
    vacuum = next(iter(sectors))
    qubit = next(s for s, dim in sectors.items() if dim == 2)
    flag_sectors = [s for s in sectors if s not in (vacuum, qubit)]
    assert sectors[vacuum] == 1 and len(flag_sectors) == 6
    flag_response = np.asarray(
        [
            [declaration.bob_block(v, s).item().real for s in flag_sectors]
            for v in declaration.bob_outcomes
        ]
    )
    if route == "encoded":
        c = flag_response[-1, 0]
        assert 0 <= c <= 0.5
        expected_response = (1 - c) * np.eye(6)
        expected_response[-1, :] += c
        assert np.array_equal(flag_response, expected_response)
    else:
        assert np.array_equal(flag_response, np.eye(6))
    point = {
        pair: np.zeros((maps.parametrization.block_dim(pair),) * 2, complex)
        for pair in maps.joint_sectors
    }
    point["n0", vacuum] = np.ones((1, 1), complex)
    t = float(transmission)
    # The source's (H,V) basis and receiver's one-photon Fock basis have
    # opposite orders. This explicit isometry is checked by the raw table.
    swap = np.array([[0, 1], [1, 0]], complex)
    omega = np.array([0, 1, 1, 0], complex)
    point["n1", vacuum] = (1 - t) * np.eye(2, dtype=complex)
    point["n1", qubit] = t * np.outer(omega, omega.conj())
    assert prepared.channel_interface is not None
    intensities = prepared.channel_interface.intensities
    for tail in declaration.alice_sectors:
        if tail in ("n0", "n1"):
            continue
        assert tail.startswith("tail-") and declaration.alice_dim_of(tail) == 1
        carried = [
            x
            for x in declaration.alice_alphabet
            if declaration.alice_block(x, tail).item().real > 0
        ]
        x = carried[0]
        px = sum(raw[x, v] for v in declaration.bob_outcomes)
        weight0 = F(float(declaration.alice_block(x, "n0").item().real)) / px
        n1 = declaration.alice_block(x, "n1")
        weight1 = F(float(np.trace(n1).real)) / px
        weight_tail = F(float(declaration.alice_block(x, tail).item().real)) / px
        assert weight0 + weight1 + weight_tail == 1
        rho = swap @ (n1 / float(px * weight1)) @ swap
        assert np.trace(rho) == pytest.approx(1, rel=0, abs=2e-14)
        powers = np.asarray(
            [
                np.trace(declaration.bob_block(v, qubit) @ rho).real
                for v in declaration.bob_outcomes
            ]
        )
        assert powers[0] == powers[-1] == 0 and sum(powers) == 1
        assert max(powers) <= 0.5
        mu = intensities[x.split("-")[1]]
        with localcontext() as ctx:
            ctx.prec = 70
            lam = Decimal((mu * transmission).numerator) / Decimal(
                (mu * transmission).denominator
            )
            p0 = (-lam).exp()
            p1 = lam * p0
            singles = [p0 * ((lam * Decimal(float(a))).exp() - 1) for a in powers[1:-1]]
            high = np.asarray(
                [
                    0.0,
                    *(
                        float(p - p1 * Decimal(float(a)))
                        for p, a in zip(singles, powers[1:-1], strict=True)
                    ),
                    float(1 - p0 - sum(singles)),
                ]
            )
        # Invert the actual supplier's flag response. Encoded WPFSS columns
        # are not deterministic outcomes; licensed FSS columns are.
        flags = np.linalg.solve(flag_response, high)
        assert min(flags) >= -2e-15
        assert sum(flags) == pytest.approx(float(1 - p0 - p1), rel=0, abs=2e-15)
        residual0 = float(p0) - float(weight0) - float(weight1) * (1 - t)
        residual1 = float(p1) - float(weight1) * t
        assert residual0 >= 0 and residual1 >= 0
        scale = float(weight_tail)
        point[tail, vacuum] = np.array([[residual0 / scale]], complex)
        point[tail, qubit] = (residual1 / scale) * rho
        for s, p in zip(flag_sectors, flags, strict=True):
            point[tail, s] = np.array([[p / scale]], complex)
        # Tail sharing really is compatible with every carried source letter.
        for other in carried:
            other_px = sum(raw[other, v] for v in declaration.bob_outcomes)
            assert all(
                raw[other, v] / other_px == raw[x, v] / px
                for v in declaration.bob_outcomes
            )

    assert max(coupling_residuals(maps.parametrization, point).values()) < 2e-12
    states = maps.parametrization.state_from_choi(point)
    check_joint_feasible(maps.parametrization, states, tolerance=2e-12)
    assert bool(declaration.constraint_list) == (route != "encoded")
    for (x, v), expected in raw.items():
        formed = sum(
            np.trace(
                np.kron(declaration.alice_block(x, a), declaration.bob_block(v, b))
                @ point[a, b]
            ).real
            for a, b in maps.joint_sectors
        )
        assert formed == pytest.approx(float(expected), rel=0, abs=2e-14)
    q = joint_statistics(maps, point)
    assert sum(q.values()) == pytest.approx(1, rel=0, abs=2e-13)
    assert min(q.values()) >= -2e-15
    polytope = declaration.acceptance_set.polytope
    assert polytope is not None
    vector = np.array([q[c] for c in declaration.acceptance_values])
    assert np.all(
        np.asarray(polytope.rows) @ vector <= np.asarray(polytope.rhs) + 2e-13
    )
    for c, expected in honest.items():
        assert q[c] == pytest.approx(float(expected), rel=0, abs=2e-14)
