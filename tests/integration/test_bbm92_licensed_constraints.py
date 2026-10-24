"""Actual BBM92 supplier scopes and licensed scalar/operator separation."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from instances.bbm92.surface import default_config, preparation
from instances.common.honest.ideal_pair import IdealPair, honest_provider
from tests.support.declared_optical_documents import template_tree

from certiqs_key.domain.bundle import read_bundle, write_bundle
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    build_joint_maps,
    joint_choi_parametrization,
)
from certiqs_key.meat_core.objective.joint_rows import check_joint_feasible
from certiqs_key.runs.general_wire import build_general_bundle
from certiqs_key.runs.pipeline import Preparation
from certiqs_key.solvers.frank_wolfe.joint_driver import _oracle_vertex
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle


def prepared_declaration(route: str, view: str):
    config = default_config()
    config = replace(
        config, device={**config.device, "route": route, "party_local_view": view}
    )
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
    return prepared, declaration


@pytest.mark.parametrize("route", ["licensed", "licensed+two-sector"])
@pytest.mark.parametrize("view", ["operator", "licensed_scalar"])
def test_actual_licensed_scopes_survive_disk(route: str, view: str, tmp_path: Path):
    prepared, declaration = prepared_declaration(route, view)
    entries = declaration.constraint_list
    assert len(entries) >= 4
    # The factor labels are the template's station ids.
    factor_labels = tuple(
        station["id"] for station in template_tree("bbm92")["stations"]
    )
    assert factor_labels == ("alice_station", "bob_station")
    assert all(entry.scope in factor_labels for entry in entries)
    assert sum(entry.is_party_local for entry in entries) == (
        len(entries) // 2 if view == "operator" else 0
    )
    bundle, _ = build_general_bundle(
        declaration,
        alice_announcements=(),
        bob_announcements=(),
        reduction_chain=prepared.compilation.reduction_chain_record,
        created_by="bbm92-licensed-test",
    )
    write_bundle(tmp_path / "bundle", bundle)
    reread = declaration_from_bundle(read_bundle(tmp_path / "bundle"))
    assert [(e.scope, e.is_party_local) for e in reread.constraint_list] == [
        (e.scope, e.is_party_local) for e in entries
    ]


@pytest.mark.requires_qics
def test_actual_licensed_scalar_view_has_strict_lmo_gap():
    _, local = prepared_declaration("licensed", "operator")
    _, scalar = prepared_declaration("licensed", "licensed_scalar")
    maps = [build_joint_maps(joint_choi_parametrization(d)) for d in (local, scalar)]
    p = maps[0].parametrization
    a, b = local.factors

    def pair(ai: int, bi: int) -> tuple[str, str]:
        return next(
            pair
            for pair in local.joint_sectors
            if local.split_sector(pair[1])
            == (a.sectors.labels[ai], b.sectors.labels[bi])
        )

    # These indices are the actual supplier's declared order: vacuum, photon,
    # nc, H, V, D, A, mc. No engine or instance retags a constraint.
    h_vac, mc_vac, mc_photon = pair(3, 0), pair(7, 0), pair(7, 1)
    witness = {
        key: np.zeros((p.block_dim(key), p.block_dim(key)), np.complex128)
        for key in p.joint_sectors
    }
    witness[h_vac][0, 0] = 0.5
    witness[mc_photon][1, 1] = 0.5
    check_joint_feasible(maps[1].parametrization, witness)
    with pytest.raises(DeclarationError, match="party_local"):
        check_joint_feasible(p, witness)

    cost = {key: np.zeros_like(block) for key, block in witness.items()}
    cost[h_vac][0, 0] = -1
    cost[mc_vac][0, 0] = 2
    values = []
    for item in maps:
        diagnostics = []
        vertex, optimal = _oracle_vertex(
            item, QicsSectorChoiOracle(), cost, diagnostics
        )
        assert optimal
        check_joint_feasible(item.parametrization, vertex)
        values.append(sum(float(np.trace(cost[k] @ vertex[k]).real) for k in cost))
    assert values[0] == pytest.approx(0, abs=1e-7)
    # Scalar optimum is -(1-w), where the supplier's mc weight is w.
    w = -float(local.constraint_list[0].operator_blocks[a.sectors.labels[3]][0, 0].real)
    assert values[1] == pytest.approx(-(1 - w), abs=1e-7)
    # The mc weight is the receiver's enclosed one, 1/2 rounded down
    # (receiver/req:rigorous-weight), so the gap 1 - w is 1/2 and a little.
    assert 1 - w > 0.5
    assert values[0] - values[1] == pytest.approx(1 - w, abs=1e-6)
