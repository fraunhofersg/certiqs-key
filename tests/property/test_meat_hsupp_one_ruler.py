"""(H-SUPP) is read with one ruler: rank X at the identity input equals dim W.

``frank-wolfe/rem:fo-one-ruler``. The right side of Eq.
``eq:hsupp-check``, ``dim W_{chat,s} = rank K_{chat,s}``, is read at
``sqrt(support_cutoff)`` on the singular values of the Kraus stack, which is
the ``support_cutoff`` row read on ``K K^dagger``. The left side counts the
eigenvalues of ``X = K (1 (x) J) K^dagger`` at ``support_cutoff``. At the
identity input ``X`` is ``K K^dagger`` itself, the claim's reference,
so the two sides are the same count and (H-SUPP), which holds exactly there by
Eq. ``eq:Wcs-bound``, is also decided to hold. The identity
input is the driver's start point (``joint_initial_point``, a multiple of the
identity per block); what is evaluated is ``X`` at the identity input on
``S_adm (x) H(Q_s)``.

A separate ``branch_support_dim`` row (1e-12 on ``sigma``) would fail this
for BBM92 at photon cutoff 2 and above with ``key_bases = ZX``: lattice
snapping leaves directions with ``sigma`` around 3e-11 relative, which that row
would count and ``rank X`` counts only at a badly conditioned input. The
property is asserted here for every key-active pair of the surveyed instances,
at their defaults and at cutoff 2 (and BBM92 at 3), on the declaration a run
actually solves: the bundle handed to the solver is captured, and no solve is
run.
"""

from __future__ import annotations

import importlib
import math
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import certiqs_key.runs.pipeline as pipeline
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.objective.branch import (
    admissible_isometry,
    aggregate_branch_operator,
    generate_maps,
)
from certiqs_key.meat_core.objective.joint import (
    build_joint_maps,
    joint_choi_parametrization,
)
from certiqs_key.meat_core.objective.joint_gradient import _aggregate
from certiqs_key.meat_core.objective.linalg import (
    FACTOR_SUPPORT_CUTOFF,
    SUPPORT_CUTOFF,
    support_rank,
)
from certiqs_key.meat_core.objective.support import (
    branch_support,
    branch_support_dimension,
)
from certiqs_key.solvers.frank_wolfe.joint_driver import joint_initial_point


class _Captured(Exception):
    """Carries the bundle a run would have solved, instead of solving it."""


def _capture(bundle: Any, oracle: Any, **kwargs: Any) -> Any:
    raise _Captured(bundle)


def _solved_declaration(
    instance: str,
    cutoff: int | None,
    directory: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> ProtocolDeclaration | GeneralDeclaration:
    """Return the declaration a default run of ``instance`` hands the solver."""
    surface = importlib.import_module(f"instances.{instance}.surface")
    config = surface.default_config()
    if cutoff is not None:
        device = dict(config.device)
        if instance == "bbm92":
            for station in ("alice", "bob"):
                device[f"{station}_photon_cutoff"] = cutoff
                device[f"{station}_exact_window"] = cutoff + 1
        else:
            device["photon_cutoff"] = Fraction(cutoff)
            device["exact_window"] = Fraction(cutoff + 1)
        config = surface.default_config(device=device)
    monkeypatch.setattr(pipeline, "solve_bundle", _capture)
    with pytest.raises(_Captured) as captured:
        surface.runner(object(), directory, created_by="one-ruler property")(
            config, 0
        )
    return declaration_from_bundle(captured.value.args[0])


def _mismatches(
    declaration: ProtocolDeclaration | GeneralDeclaration,
) -> tuple[int, int, list[tuple[str, str, int, int]]]:
    """Return the key-active pair count, their band total, and every mismatch."""
    bad: list[tuple[str, str, int, int]] = []
    active = 0
    band = 0
    if isinstance(declaration, GeneralDeclaration):
        maps = build_joint_maps(joint_choi_parametrization(declaration))
        start = joint_initial_point(maps.parametrization)
        for (chat, pair), inert in maps.key_inert.items():
            if inert:
                continue
            active += 1
            band += maps.support_bands[(chat, pair)]
            classes = maps.branches[(chat, pair)].classes
            rank = support_rank(_aggregate(classes, start[pair]))
            reference = maps.support_references[(chat, pair)]
            if rank != reference:
                bad.append((chat, str(pair), rank, reference))
        return active, band, bad
    one = generate_maps(declaration)
    for (chat, sector), inert in one.key_inert.items():
        if inert:
            continue
        active += 1
        band += one.support_bands[(chat, sector)]
        # THE IDENTITY INPUT on S_adm (x) H(Q_s), omega_s = lift lift^dagger,
        # at which X is the lifted K K^dagger -- the reference of the amended
        # claim. Not the one-factor driver's start point, which is the oracle's
        # analytic centre.
        lift = admissible_isometry(declaration, sector)
        operator = aggregate_branch_operator(
            one.branches[chat][sector], lift @ lift.conj().T
        )
        rank = support_rank(operator)
        reference = one.support_references[(chat, sector)]
        if rank != reference:
            bad.append((chat, sector, rank, reference))
    return active, band, bad


_CASES = [
    pytest.param("bbm92", None, id="bbm92-default"),
    pytest.param("bbm92", 2, id="bbm92-N2"),
    pytest.param("bbm92", 3, id="bbm92-N3", marks=pytest.mark.slow),
    pytest.param("optical_bb84", None, id="optical_bb84-default"),
    pytest.param("optical_bb84", 2, id="optical_bb84-N2"),
    pytest.param("decoy_bb84", None, id="decoy_bb84-default"),
    pytest.param("decoy_bb84", 2, id="decoy_bb84-N2"),
]


@pytest.mark.parametrize(("instance", "cutoff"), _CASES)
def test_rank_x_at_the_identity_input_equals_dim_w_on_every_key_active_pair(
    instance: str,
    cutoff: int | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """At the identity input the two sides agree.

    BBM92 at cutoff 2 and 3 (``key_bases = ZX`` by default) is where the
    snapped directions sit, so the band there is asserted non-empty: the
    property is exercised on the case that failed, not only on clean data.
    Everywhere else the band is asserted EMPTY on every key-active pair, which
    is the exact ground for the old and new rules coinciding at every iterate
    there, so that no number those configurations issue moves.
    """
    declaration = _solved_declaration(instance, cutoff, tmp_path, monkeypatch)
    active, band, bad = _mismatches(declaration)
    assert active > 0
    assert bad == []
    if instance == "bbm92" and cutoff is not None:
        assert band > 0
    else:
        assert band == 0


def test_the_reference_and_the_band_are_read_with_the_support_cutoff_row() -> None:
    """``dim W`` at ``sqrt(support_cutoff)``, the band between the two windows.

    A stack with singular values ``1``, ``1e-3``, ``3e-11`` (the order of the
    snapped direction the item found) and ``1e-14``: the reference counts two,
    the band holds the one at ``3e-11``, and ``1e-14`` is in neither. And the
    reference is exactly the ``support_cutoff`` count of ``K K^dagger``.
    """
    assert math.sqrt(SUPPORT_CUTOFF) == FACTOR_SUPPORT_CUTOFF
    values = np.array([1.0, 1e-3, 3e-11, 1e-14])
    stack = np.diag(values).astype(np.complex128)
    support = branch_support([stack])
    assert support.dimension == 2
    assert support.band == 1
    assert branch_support_dimension([stack]) == 2
    assert support_rank(stack @ stack.conj().T) == support.dimension
    # Relative, so a uniformly small stack is not a degenerate one.
    assert branch_support([stack * 2.0**-60]) == support
    # Split across two classes side by side, the reading is of the one stack.
    first = np.diag([1.0, 0.0, 3e-11, 0.0]).astype(np.complex128)
    second = np.diag([0.0, 1e-3, 0.0, 1e-14]).astype(np.complex128)
    assert branch_support([first, second]) == support
    # An empty or vanishing stack spans nothing and has no band.
    assert branch_support([]).dimension == 0
    assert branch_support([np.zeros((2, 2), dtype=np.complex128)]).band == 0
