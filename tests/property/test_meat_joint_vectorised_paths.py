"""The vectorised evaluation paths of the general format against their references.

The statistics
map ``Phi`` of ``eq:K-joint`` is evaluated as one precomputed linear map, not as
a per-term loop. That changes how the number is summed and never which number
it is, so this file compares the two routes on random complex Hermitian PSD
blocks, on the maps of both real two-sided instances (BBM92 and decoy BB84, as
compiled by their default configurations) and on the hand-built multi-factor
declarations of ``tests/support/general_toys.py``.

The same holds for the line search's use of that linearity: the objective
formed from INTERPOLATED endpoint statistics
(``joint_objective_value_at_statistics``) is compared with the direct
``joint_objective_value`` at points along a segment; the precomputed
branch plan (which joint sectors a deficit sum visits) with the per-sector
classification it replaced; and the regrouped ``joint_gradient`` with its
kept reference ``_joint_gradient_reference``.

The agreement asked is rounding-level, relative: ``Phi`` is a sum of
non-negative terms on PSD inputs, so no cancellation can make a relative
comparison meaningless.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import numpy as np
import pytest
from tests.support.general_toys import (
    decoy_like_general,
    maps_of,
    qubit_bb84_general,
    random_choi_point,
    two_factor_general,
)

from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    JointMaps,
    JointSector,
    _joint_statistics_reference,
    build_joint_maps,
    joint_choi_parametrization,
    joint_objective_value,
    joint_objective_value_at_statistics,
    joint_statistics,
    normalise_dropped_set,
)
from certiqs_key.meat_core.objective.joint_gradient import (
    _joint_gradient_reference,
    joint_gradient,
)
from certiqs_key.meat_core.objective.linalg import Matrix, hermitian_part
from certiqs_key.runs.pipeline import Preparation

#: Relative agreement of two summation orders of one real-linear function.
#: NOT A DECLARED TOLERANCE: no predicate of the engine is decided at it.
ROUTE_RTOL = 1e-12


def _instance_maps(module: str, device: dict[str, object] | None = None) -> JointMaps:
    """Return the joint maps of a real instance's default compiled declaration.

    The acceptance frequencies are a placeholder singleton: the maps do not
    read them (``build_joint_maps`` reads the declaration's operators, the
    transcript and the acceptance alphabet only).
    """
    surface = __import__(f"instances.{module}", fromlist=["default_config"])
    config = (
        surface.default_config(device=device) if device else surface.default_config()
    )
    prepared = surface.preparation(config)
    assert isinstance(prepared, Preparation), prepared
    candidate = prepared.declaration
    declaration = dock_general_candidate(
        candidate,
        acceptance_set=AcceptanceSet(
            geometry="singleton",
            frequencies=(1.0, *(0.0 for _ in candidate.acceptance_alphabet[1:])),
        ),
        rounds=config.rounds,
        parameters=config.parameters,
    )
    return build_joint_maps(joint_choi_parametrization(declaration))


MAPS: dict[str, Callable[[], JointMaps]] = {
    "bbm92": lambda: _instance_maps("bbm92.surface"),
    "decoy_bb84": lambda: _instance_maps("decoy_bb84"),
    "toy-two-factor": lambda: maps_of(two_factor_general(party_local=False)),
    "toy-two-factor-party-local": lambda: maps_of(two_factor_general(party_local=True)),
    "toy-decoy-like": lambda: maps_of(decoy_like_general()),
    "toy-decoy-like-ensemble": lambda: maps_of(decoy_like_general(ensemble=True)),
    "toy-qubit-bb84": lambda: maps_of(qubit_bb84_general()),
}

_BUILT: dict[str, JointMaps] = {}


def _maps(name: str) -> JointMaps:
    if name not in _BUILT:
        _BUILT[name] = MAPS[name]()
    return _BUILT[name]


def random_psd_blocks(maps: JointMaps, seed: int) -> dict[JointSector, Matrix]:
    """Return one random complex Hermitian PSD block per joint sector."""
    rng = np.random.default_rng(seed)
    out: dict[JointSector, Matrix] = {}
    for pair in maps.joint_sectors:
        dim = maps.parametrization.block_dim(pair)
        sample = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
        out[pair] = np.asarray(sample @ sample.conj().T, dtype=np.complex128)
    return out


def _assert_close(left: dict[str, float], right: dict[str, float]) -> None:
    assert list(left) == list(right)
    scale = max(abs(value) for value in right.values())
    for chat, value in right.items():
        assert left[chat] == pytest.approx(value, rel=ROUTE_RTOL, abs=1e-15 * scale)


@pytest.mark.parametrize("name", sorted(MAPS))
@pytest.mark.parametrize("seed", (1, 2, 3))
def test_the_statistics_map_equals_the_per_term_loop(name: str, seed: int) -> None:
    """``joint_statistics`` against ``_joint_statistics_reference``."""
    maps = _maps(name)
    blocks = random_psd_blocks(maps, seed)
    _assert_close(
        joint_statistics(maps, blocks), _joint_statistics_reference(maps, blocks)
    )


def test_the_statistics_map_is_read_only_and_cached_per_maps() -> None:
    """The precomputed matrix is immutable and belongs to its own maps."""
    maps = _maps("toy-two-factor")
    layout = maps.statistics_map
    assert maps.statistics_map is layout
    assert not layout.matrix.flags.writeable
    with pytest.raises(ValueError):
        layout.matrix[0, 0] = 1.0
    other = maps_of(two_factor_general(party_local=False))
    assert other.statistics_map is not layout


def test_the_statistics_map_is_exact_on_non_hermitian_blocks() -> None:
    """``Re tr[Gamma J]`` is read for ANY square blocks, as the loop reads it."""
    maps = _maps("toy-decoy-like")
    rng = np.random.default_rng(7)
    blocks = {
        pair: rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
        for pair in maps.joint_sectors
        for dim in (maps.parametrization.block_dim(pair),)
    }
    fast = joint_statistics(maps, blocks)
    slow = _joint_statistics_reference(maps, blocks)
    scale = max(abs(value) for value in slow.values())
    for chat, value in slow.items():
        assert fast[chat] == pytest.approx(value, rel=ROUTE_RTOL, abs=1e-14 * scale)


def test_a_block_of_the_wrong_size_is_refused() -> None:
    """A mis-sized block cannot be silently misaligned in the stacked vector."""
    maps = _maps("toy-two-factor")
    blocks = random_psd_blocks(maps, 4)
    first = maps.joint_sectors[0]
    size = blocks[first].shape[0] + 1
    blocks[first] = np.eye(size, dtype=np.complex128)
    with pytest.raises(ValueError, match="expected"):
        joint_statistics(maps, blocks)


#: Relative agreement of the objective through interpolated and direct
#: statistics: rounding in ``Phi`` passes through the logarithms of the
#: divergence kernel. NOT A DECLARED TOLERANCE.
OBJECTIVE_RTOL = 1e-10


@pytest.mark.parametrize("name", sorted(MAPS))
@pytest.mark.parametrize("step", (0.0, 0.25, 0.618, 1.0))
def test_interpolated_statistics_give_the_direct_objective(
    name: str, step: float
) -> None:
    """``Phi`` is linear along a segment, so both objective routes agree."""
    maps = _maps(name)
    start = random_choi_point(maps.parametrization, 21)
    end = random_choi_point(maps.parametrization, 22)
    middle = {
        pair: hermitian_part(0.5 * start[pair] + 0.5 * end[pair]) for pair in start
    }
    q = joint_statistics(maps, middle)
    point = {
        pair: hermitian_part((1.0 - step) * start[pair] + step * end[pair])
        for pair in start
    }
    phi_start = joint_statistics(maps, start)
    phi_end = joint_statistics(maps, end)
    interpolated = {
        chat: (1.0 - step) * phi_start[chat] + step * phi_end[chat]
        for chat in phi_start
    }
    dropped = (
        normalise_dropped_set(maps, [("match", ("one", "q"))])
        if name == "toy-decoy-like"
        else normalise_dropped_set(maps, [])
    )
    for skip in (True, False):
        direct = joint_objective_value(
            maps, q, point, 1.5, dropped=dropped, skip_key_inert=skip
        )
        through = joint_objective_value_at_statistics(
            maps, q, point, 1.5, interpolated, dropped=dropped, skip_key_inert=skip
        )
        assert through == pytest.approx(direct, rel=OBJECTIVE_RTOL, abs=1e-14)


def test_supplied_statistics_are_the_ones_used() -> None:
    """At the point's own ``Phi`` the two entry points are the same number."""
    maps = _maps("toy-two-factor")
    point = random_choi_point(maps.parametrization, 23)
    q = joint_statistics(maps, point)
    assert joint_objective_value_at_statistics(
        maps, q, point, 1.5, joint_statistics(maps, point)
    ) == joint_objective_value(maps, q, point, 1.5)


def _loop_classification(
    maps: JointMaps, chat: str, dropped: frozenset[tuple[str, JointSector]], skip: bool
) -> tuple[tuple[JointSector, ...], ...]:
    """Return the classification evaluate_joint_branch made inline before."""
    evaluated, dropped_pairs, skipped = [], [], []
    for pair in maps.joint_sectors:
        if chat in maps.chat_key and (chat, pair) in dropped:
            dropped_pairs.append(pair)
        elif skip and maps.key_inert[(chat, pair)]:
            skipped.append(pair)
        else:
            evaluated.append(pair)
    return tuple(evaluated), tuple(dropped_pairs), tuple(skipped)


def _dropped_for(maps: JointMaps, name: str) -> frozenset[tuple[str, JointSector]]:
    if name == "toy-decoy-like":
        return normalise_dropped_set(
            maps, [("match", ("one", "q")), ("match", ("flag", "q"))]
        )
    return normalise_dropped_set(maps, [])


@pytest.mark.parametrize("name", sorted(MAPS))
@pytest.mark.parametrize("skip", (True, False))
def test_the_branch_plan_is_the_loop_classification(name: str, skip: bool) -> None:
    """Only the sectors that contribute are visited, in the declared order."""
    maps = _maps(name)
    dropped = _dropped_for(maps, name)
    for chat in maps.declaration.acceptance_values:
        plan = maps.branch_plan(chat, dropped, skip)
        assert (
            plan.evaluated,
            plan.dropped_pairs,
            plan.skipped_key_inert,
        ) == _loop_classification(maps, chat, dropped, skip)
        assert maps.branch_plan(chat, dropped, skip) is plan
    needed = set(maps.deficit_pairs(dropped, skip))
    assert needed == {
        pair
        for chat in maps.declaration.acceptance_values
        for pair in _loop_classification(maps, chat, dropped, skip)[0]
    }
    point = random_choi_point(maps.parametrization, 31)
    q = joint_statistics(maps, point)
    phi = joint_statistics(maps, point)
    only_needed = {pair: point[pair] for pair in maps.deficit_pairs(dropped, skip)}
    assert joint_objective_value_at_statistics(
        maps, q, only_needed, 1.5, phi, dropped=dropped, skip_key_inert=skip
    ) == joint_objective_value(
        maps, q, point, 1.5, dropped=dropped, skip_key_inert=skip
    )


@pytest.mark.parametrize("name", sorted(MAPS))
@pytest.mark.parametrize("alpha", (1.05, 1.5))
def test_the_restructured_gradient_equals_the_reference(
    name: str, alpha: float
) -> None:
    """``joint_gradient`` against ``_joint_gradient_reference``, to rounding."""
    maps = _maps(name)
    dropped = _dropped_for(maps, name)
    point = random_choi_point(maps.parametrization, 41)
    other = random_choi_point(maps.parametrization, 42)
    q = joint_statistics(
        maps, {pair: 0.5 * point[pair] + 0.5 * other[pair] for pair in point}
    )
    # (H-POS) is asked on the acceptance support; the real instances declare
    # values no operator reaches, which a run leaves out of it the same way.
    maps = replace(
        maps, acceptance_support=tuple(chat for chat, value in q.items() if value > 0)
    )
    for skip in (True, False):
        fast = joint_gradient(
            maps, q, point, alpha, dropped=dropped, skip_key_inert=skip
        )
        slow = _joint_gradient_reference(
            maps, q, point, alpha, dropped=dropped, skip_key_inert=skip
        )
        assert fast.q == slow.q
        assert fast.dropped_pieces == slow.dropped_pieces
        assert fast.key_inert_pieces == slow.key_inert_pieces
        assert dict(fast.perturbations) == dict(slow.perturbations)
        assert list(fast.blocks) == list(slow.blocks)
        scale = max(float(np.max(np.abs(block))) for block in slow.blocks.values())
        for pair, block in slow.blocks.items():
            np.testing.assert_allclose(
                fast.blocks[pair], block, rtol=OBJECTIVE_RTOL, atol=1e-13 * scale
            )


def _with_complex_hermitian_operators(maps: JointMaps, seed: int) -> JointMaps:
    """Return ``maps`` with every ``Gamma`` a random complex Hermitian PSD matrix.

    Every statistics operator the shipped maps carry is real symmetric, so
    ``Gamma == Gamma^T`` and a stacked map built WITHOUT the transpose of
    ``tr[G J] = sum_ij G_ij J_ji`` would agree with the loop exactly. Complex
    Hermitian operators are not symmetric, which is what makes the transpose
    visible to a test. ``replace`` gives a new instance with empty caches.
    """
    rng = np.random.default_rng(seed)
    operators: dict[tuple[str, JointSector], Matrix] = {}
    for key, operator in maps.statistics_operator.items():
        dim = operator.shape[0]
        sample = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
        operators[key] = np.asarray(sample @ sample.conj().T, dtype=np.complex128)
    return replace(maps, statistics_operator=operators)


@pytest.mark.parametrize("name", ["toy-decoy-like", "toy-two-factor", "bbm92"])
def test_the_vectorised_paths_hold_on_complex_hermitian_operators(name: str) -> None:
    """Statistics and gradient against the loops where ``Gamma != Gamma^T``."""
    maps = _with_complex_hermitian_operators(_maps(name), 51)
    asymmetry = max(
        float(np.max(np.abs(operator - operator.T)))
        for operator in maps.statistics_operator.values()
    )
    assert asymmetry > 0.1
    blocks = random_psd_blocks(maps, 52)
    _assert_close(
        joint_statistics(maps, blocks), _joint_statistics_reference(maps, blocks)
    )
    point = random_choi_point(maps.parametrization, 53)
    q = joint_statistics(maps, point)
    maps = replace(
        maps, acceptance_support=tuple(chat for chat, value in q.items() if value > 0)
    )
    dropped = _dropped_for(maps, name)
    fast = joint_gradient(maps, q, point, 1.5, dropped=dropped)
    slow = _joint_gradient_reference(maps, q, point, 1.5, dropped=dropped)
    assert fast.q == pytest.approx(slow.q, rel=OBJECTIVE_RTOL)
    scale = max(float(np.max(np.abs(block))) for block in slow.blocks.values())
    for pair, block in slow.blocks.items():
        np.testing.assert_allclose(
            fast.blocks[pair], block, rtol=OBJECTIVE_RTOL, atol=1e-13 * scale
        )


@pytest.mark.parametrize("name", ["toy-decoy-like", "toy-two-factor", "bbm92"])
def test_the_inputs_of_the_caches_are_read_only(name: str) -> None:
    """An in-place write to a cached input raises instead of going stale.

    ``JointMaps.statistics_map`` reads ``statistics_operator`` and the frames,
    ``JointMaps.branch_plan`` reads ``key_inert``, and the declaration's cached
    sector tables read each factor's ``SectorAxis.dims``.
    """
    maps = _maps(name)
    key = next(iter(maps.statistics_operator))
    with pytest.raises(TypeError):
        maps.statistics_operator[key] = maps.statistics_operator[key]  # type: ignore[index]
    with pytest.raises(TypeError):
        maps.key_inert[key] = True  # type: ignore[index]
    frames = maps.parametrization.frames
    alice = next(iter(frames))
    with pytest.raises(TypeError):
        frames[alice] = frames[alice]  # type: ignore[index]
    for factor in maps.declaration.factors:
        label = factor.sectors.labels[0]
        with pytest.raises(TypeError):
            factor.sectors.dims[label] = 99  # type: ignore[index]
    axis = maps.declaration.alice.sectors
    with pytest.raises(TypeError):
        axis.dims[axis.labels[0]] = 99  # type: ignore[index]
