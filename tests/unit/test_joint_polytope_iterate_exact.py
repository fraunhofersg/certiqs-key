"""On a polytope the acceptance iterate is EXACTLY in the set at every gate.

Remark ``rem:acc-side`` (alpha) and (beta) make ``q_t in AcceptSet`` true BY
CONSTRUCTION -- an exact rational start and exact rational convex combinations
of exact points of the set -- and Remark ``req:first-order-withdrawal``
withdraws under ``iterate_not_feasible`` where that was not done. What is
tested, and the defect each test would catch:

* under BOTH step rules, on both drivers, every gate that records
  ``acceptance_iterate_exact = True`` evaluates at the binary64 rounding of an
  exact point that satisfies ``q >= 0``, ``sum q = 1`` and ``B q <= b`` over
  the rationals -- the defect was a binary64 ``q_t`` recorded as exact, and
  the views themselves are shown to leave the set, so the exactness is what
  does the work;
* a moving geometry whose oracle hands out no exact points withdraws every
  gate after ``q`` first moves, with ``iterate_not_feasible``;
* the pairwise active set keeps exact weights that are non-negative and sum
  to one, clamps a step to the exact away weight, and carries its exact point
  as exactly ``sum_i w_i q_i`` through steps and folds;
* THE EXACT NUMBERS STAY SHORT (unshortened they
  grew about 50 bits a step, 227k bits after 2000): over 2000 synthetic steps,
  on both the vanilla iterate and the pairwise active set, no exact number
  passes ``SHORTEN_ABOVE_BITS`` and every point is still an exact member;
  where no short member is admitted the point is given up at
  ``EXACT_BITS_CAP`` and recorded off the island;
* SINGLETON RUNS ARE UNCHANGED, bit for bit: the pairwise rule is pinned
  against the loop at a development commit before the shortening (a
  regression pin, not an oracle; the vanilla rule is pinned in
  ``test_joint_solver_options.py``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from typing import Any

import numpy as np
import pytest
from tests.support.general_toys import (
    decoy_like_general,
    maps_of,
    qubit_bb84_general,
    random_choi_point,
)
from tests.support.platform_pins import (
    DARWIN_ARM64_ACCELERATE,
    WINDOWS_AMD64_OPENBLAS,
    PinTable,
    assert_pinned,
)

import certiqs_key.solvers.frank_wolfe.acceptance_iterate as acceptance_iterate
import certiqs_key.solvers.frank_wolfe.joint_driver as joint_driver
from certiqs_key.meat_core.acceptance.geometry import (
    polytope_contains,
    polytope_minimizer_exact,
    polytope_relative_interior_point_exact,
)
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet, PolytopeData
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.reasons import AssuranceReason
from certiqs_key.solvers.frank_wolfe.acceptance_iterate import (
    SHORTEN_ABOVE_BITS,
    AcceptanceIterate,
    acceptance_vertex,
    exact_bits,
)
from certiqs_key.solvers.frank_wolfe.joint_options import JointFrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_pairwise import (
    ActiveSet,
    shrink_frequencies_exact,
)
from certiqs_key.solvers.oracles.acceptance import (
    AcceptanceOracle,
    ExactAcceptanceOracle,
    SingletonAcceptanceOracle,
)

#: Two polytopes on the two-letter alphabet whose data are not dyadic in
#: decimal: the binary64 roundings of 0.3, 0.7, 0.9 and 0.85 make the binary64
#: convex combinations of the vertices miss ``sum q = 1`` exactly.
POLYTOPES: dict[str, PolytopeData] = {
    "segment": PolytopeData(columns=2, rows=((1.0, 0.0), (-1.0, 0.0)), rhs=(0.7, -0.3)),
    "box": PolytopeData(
        columns=2,
        rows=((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)),
        rhs=(0.9, -0.1, 0.85, -0.15),
    ),
}


def _declaration(name: str) -> GeneralDeclaration:
    return replace(
        decoy_like_general(),
        acceptance_set=AcceptanceSet(geometry="polytope", polytope=POLYTOPES[name]),
    )


def _is_member(point: Sequence[Fraction], data: PolytopeData) -> bool:
    """Return whether ``point`` is in ``{q >= 0, sum q = 1, B q <= b}``, exactly."""
    if any(value < 0 for value in point) or sum(point, Fraction(0)) != 1:
        return False
    return all(
        sum(
            (Fraction(b) * q for b, q in zip(row, point, strict=True)),
            Fraction(0),
        )
        <= Fraction(bound)
        for row, bound in zip(data.rows, data.rhs, strict=True)
    )


class _Recorder:
    """Every acceptance iterate the driver forms, and every ``q`` it evaluates."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, module: Any, name: str) -> None:
        self.iterates: list[AcceptanceIterate] = []
        self.evaluated: list[dict[str, float]] = []
        original_init = AcceptanceIterate.__init__
        original_gradient = getattr(module, name)

        def recording_init(self_: AcceptanceIterate, *args: Any, **kw: Any) -> None:
            original_init(self_, *args, **kw)
            self.iterates.append(self_)

        def recording_gradient(maps: Any, *args: Any, **kw: Any) -> Any:
            q = args[0]
            self.evaluated.append(dict(q))
            return original_gradient(maps, *args, **kw)

        monkeypatch.setattr(AcceptanceIterate, "__init__", recording_init)
        monkeypatch.setattr(module, name, recording_gradient)

    def exact_behind(self, view: Mapping[str, float]) -> dict[str, Fraction]:
        """Return the exact iterate whose rounding ``view`` is, on the island."""
        for iterate in self.iterates:
            if iterate.view == view and iterate.exact is not None:
                assert iterate.on_island
                assert all(
                    float(iterate.exact[chat]) == value for chat, value in view.items()
                )
                return iterate.exact
        raise AssertionError(f"no exact iterate behind the evaluated q {view}")

    def shortest_bits(self, view: Mapping[str, float]) -> int:
        """Return the size of the shortest exact iterate behind ``view``.

        A step forms the long point and shortening then replaces it, often at
        the same view; the driver holds the replacement.
        """
        return min(
            exact_bits(iterate.exact.values())
            for iterate in self.iterates
            if iterate.view == view and iterate.exact is not None
        )


@pytest.mark.requires_qics
@pytest.mark.parametrize("step_rule", ["vanilla", "pairwise"])
@pytest.mark.parametrize("name", sorted(POLYTOPES))
def test_every_gate_consumes_an_exact_member_of_the_polytope(
    monkeypatch: pytest.MonkeyPatch, step_rule: str, name: str
) -> None:
    """Every gate consumes an exact member, on the general-format driver."""
    from certiqs_key.solvers.frank_wolfe.general_keyrate import _prepare_general
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    oracle = QicsSectorChoiOracle()
    maps, acceptance = _prepare_general(_declaration(name), oracle)
    assert isinstance(acceptance, ExactAcceptanceOracle)
    recorder = _Recorder(monkeypatch, joint_driver, "joint_gradient")
    result = joint_driver.run_joint_frank_wolfe(
        maps,
        oracle,
        acceptance,
        random_choi_point(maps.parametrization, 1),
        1.5,
        JointFrankWolfeOptions(
            max_iterations=25, step_rule=step_rule, oracle="spectral"
        ),
    )
    data = POLYTOPES[name]
    values = list(maps.declaration.acceptance_values)
    assert len(result.gates) == len(recorder.evaluated) == 25
    views_outside = 0
    for gate, view in zip(result.gates, recorder.evaluated, strict=True):
        assert gate.acceptance_iterate_exact
        assert gate.withdrawal != str(AssuranceReason.ITERATE_NOT_FEASIBLE)
        exact = recorder.exact_behind(view)
        assert _is_member([exact[chat] for chat in values], data)
        if not _is_member([Fraction(view[chat]) for chat in values], data):
            views_outside += 1
    # q MOVED, and its binary64 views are not themselves members: a driver
    # that combined the views would have recorded points outside the set.
    assert len({tuple(view.values()) for view in recorder.evaluated}) > 1
    # The recognized box now reconstructs q directly as a short exact member.
    # The non-box segment still exercises views outside the rational set.
    if name == "segment":
        assert views_outside > 0
    assert result.h_lb is not None
    # 25 steps pass the shortening threshold, so the members above include
    # shortened points; none of the exact points the gates stood on is long.
    assert all(
        recorder.shortest_bits(view) <= SHORTEN_ABOVE_BITS
        for view in recorder.evaluated
    )


class _FloatOnly:
    """A polytope oracle with its exact points hidden: binary64 only."""

    def __init__(self, inner: AcceptanceOracle) -> None:
        self.inner = inner

    @property
    def exact_island(self) -> bool:
        return self.inner.exact_island

    def start(self) -> dict[str, float]:
        return self.inner.start()

    def minimize(self, gradient: Mapping[str, float]) -> dict[str, float]:
        return self.inner.minimize(gradient)


@pytest.mark.requires_qics
@pytest.mark.parametrize("step_rule", ["vanilla", "pairwise"])
def test_a_moving_geometry_without_exact_points_withdraws(step_rule: str) -> None:
    """Where exactness cannot be kept the gate withdraws, never claims it."""
    from certiqs_key.solvers.frank_wolfe.general_keyrate import _prepare_general
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    oracle = QicsSectorChoiOracle()
    maps, acceptance = _prepare_general(_declaration("segment"), oracle)
    hidden = _FloatOnly(acceptance)
    assert not isinstance(hidden, ExactAcceptanceOracle)
    result = joint_driver.run_joint_frank_wolfe(
        maps,
        oracle,
        hidden,
        random_choi_point(maps.parametrization, 1),
        1.5,
        JointFrankWolfeOptions(
            max_iterations=10, step_rule=step_rule, oracle="spectral"
        ),
    )
    flags = [gate.acceptance_iterate_exact for gate in result.gates]
    # The start is the oracle's own point and is on the island until q moves.
    assert flags[0]
    first_off = flags.index(False)
    assert not any(flags[first_off:])
    for gate in result.gates[first_off:]:
        assert gate.withdrawal == str(AssuranceReason.ITERATE_NOT_FEASIBLE)


@pytest.mark.requires_qics
def test_the_accepted_driver_keeps_the_polytope_iterate_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same property for an accepted-format declaration through ``solve``.

    The declaration runs on the joint driver as the degenerate general
    declaration it is, so the recorder watches ``joint_gradient``.
    """
    from mode_bundles import build_bundle
    from polytope_toys import _with_acceptance_set
    from toy_declarations import toy

    from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
    from certiqs_key.solvers.frank_wolfe import solve_bundle
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    declared = _with_acceptance_set(
        toy("TOY-8-T"),
        "TOY-8-T-SEGMENT",
        {
            "geometry": "polytope",
            "m_row": 2,
            "B": ((1.0, 0.0), (-1.0, 0.0)),
            "b": (0.8, -0.3),
        },
        "TOY-8-T on the segment 0.3 <= q(chat0) <= 0.8.",
    )
    bundle = build_bundle(declared)
    data = declaration_from_bundle(bundle).acceptance_set.polytope
    assert data is not None
    recorder = _Recorder(monkeypatch, joint_driver, "joint_gradient")
    result = solve_bundle(
        bundle,
        QicsSectorChoiOracle(),
        options=JointFrankWolfeOptions(max_iterations=15),
    )
    assert result.h_low is not None
    assert recorder.evaluated
    assert all(iterate.on_island for iterate in recorder.iterates)
    assert len({tuple(view.values()) for view in recorder.evaluated}) > 1
    for view in recorder.evaluated:
        exact = recorder.exact_behind(view)
        assert _is_member(list(exact.values()), data)


# ---------------------------------------------------------------------------
# The pairwise active set, exactly.
# ---------------------------------------------------------------------------


def _check_exact(active: ActiveSet) -> None:
    assert active.exact_weights is not None and active.exact_frequencies is not None
    assert all(weight > 0 for weight in active.exact_weights)
    assert sum(active.exact_weights, Fraction(0)) == 1
    assert active.weights.tolist() == [float(w) for w in active.exact_weights]
    columns = len(active.exact_frequencies[0])
    rebuilt = tuple(
        sum(
            (
                weight * row[column]
                for weight, row in zip(
                    active.exact_weights, active.exact_frequencies, strict=True
                )
            ),
            Fraction(0),
        )
        for column in range(columns)
    )
    assert active.exact_point() == rebuilt


def test_the_exact_active_set_keeps_its_weights_and_its_point_exact() -> None:
    rng = np.random.default_rng(7)
    start = (Fraction(1, 3), Fraction(1, 3), Fraction(1, 3))
    vertices = [
        (Fraction(1, 2), Fraction(1, 2), Fraction(0)),
        (Fraction(1, 5), Fraction(3, 5), Fraction(1, 5)),
        (Fraction(0), Fraction(1, 7), Fraction(6, 7)),
    ]
    active = ActiveSet.single(
        np.zeros(1, np.complex128), np.asarray([float(x) for x in start]), start
    )
    _check_exact(active)
    folds = 0
    for step in range(60):
        vertex = vertices[step % 3]
        atom = shrink_frequencies_exact(vertex, start)
        floats = np.asarray([float(x) for x in atom])
        block = rng.normal(size=1).astype(np.complex128)
        before = active.size
        if step % 2 == 0:
            active = active.frank_wolfe(
                block, floats, float(rng.uniform(0.05, 0.9)), atom
            )
        else:
            away = int(rng.integers(active.size))
            assert active.exact_weights is not None
            # Leave a sliver below the fold threshold on the away atom.
            sliver = float(active.exact_weights[away]) * (1 - 1e-14)
            active = active.pairwise(away, block, floats, sliver, atom)
        folds += before + 1 - active.size
        _check_exact(active)
    assert folds > 0


def test_a_pairwise_step_is_clamped_to_the_exact_away_weight() -> None:
    third = Fraction(1, 3)
    start = (third, 1 - third)
    active = ActiveSet.single(
        np.zeros(1, np.complex128), np.asarray([float(x) for x in start]), start
    ).frank_wolfe(
        np.ones(1, np.complex128),
        np.asarray([0.5, 0.5]),
        0.1,
        (Fraction(1, 2), Fraction(1, 2)),
    )
    assert active.exact_weights is not None
    # The binary64 rounding of the away weight may exceed it; a step at the
    # next float up must move exactly the weight there is and no more.
    exact_away = active.exact_weights[0]
    over = np.nextafter(float(exact_away), 2.0)
    assert Fraction(over) > exact_away
    stepped = active.pairwise(
        0,
        np.ones(1, np.complex128),
        np.asarray([0.25, 0.75]),
        float(over),
        (Fraction(1, 4), Fraction(3, 4)),
    )
    _check_exact(stepped)
    assert stepped.size == 2


# ---------------------------------------------------------------------------
# The exact numbers stay short.
# ---------------------------------------------------------------------------


class _ExactPolytope:
    """An exact acceptance oracle over bare polytope data, without a solver."""

    exact_island = True

    def __init__(self, data: PolytopeData, contains: Any = None) -> None:
        self.data = data
        self.values = tuple(f"c{index}" for index in range(data.columns))
        self._contains = contains

    def _named(self, point: Sequence[Fraction]) -> dict[str, Fraction]:
        return dict(zip(self.values, point, strict=True))

    def exact_start(self) -> dict[str, Fraction]:
        point = polytope_relative_interior_point_exact(self.data)
        assert point is not None
        return self._named(point)

    def exact_minimize(self, gradient: Mapping[str, float]) -> dict[str, Fraction]:
        point = polytope_minimizer_exact([gradient[c] for c in self.values], self.data)
        assert point is not None
        return self._named(point)

    def exact_contains(self, point: Mapping[str, Fraction]) -> bool:
        if self._contains is not None:
            return bool(self._contains(point))
        return polytope_contains(self.data, [point[c] for c in self.values])

    def start(self) -> dict[str, float]:
        return {c: float(v) for c, v in self.exact_start().items()}

    def minimize(self, gradient: Mapping[str, float]) -> dict[str, float]:
        return {c: float(v) for c, v in self.exact_minimize(gradient).items()}


def _long_loop(oracle: _ExactPolytope, steps: int) -> list[AcceptanceIterate]:
    """Alternate the two vertices of the segment, with some steps near one.

    The steps near ``1 - 1e-10`` (the driver's cap) drive the iterate to within
    an ulp of a facet, where the binary64 view falls outside the set and a
    short member must come from the move toward the interior start.
    """
    rng = np.random.default_rng(11)
    iterate = AcceptanceIterate.start(oracle)
    seen = [iterate]
    for index in range(steps):
        cost = {"c0": 1.0, "c1": -1.0} if index % 3 else {"c0": -1.0, "c1": 1.0}
        step = 1.0 - 1e-10 if index % 7 == 0 else float(rng.uniform(1e-4, 0.9))
        iterate = iterate.toward(acceptance_vertex(oracle, cost), step)
        seen.append(iterate)
    return seen


def test_the_exact_iterate_stays_short_and_exact_over_a_long_run() -> None:
    oracle = _ExactPolytope(POLYTOPES["segment"])
    assert isinstance(oracle, ExactAcceptanceOracle)
    seen = _long_loop(oracle, 2000)
    for iterate in seen:
        assert iterate.on_island and iterate.exact is not None
        assert exact_bits(iterate.exact.values()) <= SHORTEN_ABOVE_BITS
        assert _is_member(list(iterate.exact.values()), POLYTOPES["segment"])
        assert iterate.view == {c: float(v) for c, v in iterate.exact.items()}


def test_an_exact_iterate_no_member_shortens_is_given_up_off_the_island(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail-closed: past the cap the iterate is binary64 and off the island."""
    monkeypatch.setattr(acceptance_iterate, "EXACT_BITS_CAP", 2048)
    start = _ExactPolytope(POLYTOPES["segment"]).exact_start()
    oracle = _ExactPolytope(
        POLYTOPES["segment"], contains=lambda point: dict(point) == start
    )
    seen = _long_loop(oracle, 200)
    given_up = [index for index, it in enumerate(seen) if not it.on_island]
    assert given_up, "the cap was never reached"
    first = given_up[0]
    assert all(it.exact is not None for it in seen[:first])
    assert max(exact_bits(it.exact.values()) for it in seen[:first]) > 512
    assert all(not it.on_island and it.exact is None for it in seen[first:])


def test_the_pairwise_active_set_stays_short_and_exact_over_a_long_run() -> None:
    data = POLYTOPES["box"]
    oracle = _ExactPolytope(data)
    start = tuple(oracle.exact_start().values())
    shortener = AcceptanceIterate.start(oracle).shortener
    assert shortener is not None
    vertices = [
        tuple(oracle.exact_minimize({"c0": a, "c1": b}).values())
        for a, b in ((1.0, -1.0), (-1.0, 1.0))
    ]
    rng = np.random.default_rng(5)
    active = ActiveSet.single(
        np.zeros(1, np.complex128), np.asarray([float(x) for x in start]), start
    )
    for step in range(2000):
        atom = shrink_frequencies_exact(vertices[step % 2], start)
        floats = np.asarray([float(x) for x in atom])
        block = rng.normal(size=1).astype(np.complex128)
        if step % 3 == 0:
            away = int(rng.integers(active.size))
            assert active.exact_weights is not None
            fraction = float(rng.uniform(0.1, 1.0))
            moved = float(active.exact_weights[away]) * fraction
            active = active.pairwise(away, block, floats, moved, atom)
        else:
            active = active.frank_wolfe(
                block, floats, float(rng.uniform(1e-3, 0.5)), atom
            )
        active = active.bounded(shortener.shorten)
        if step % 50 == 49:
            _check_exact(active)
        assert active.exact_weights is not None
        assert active.exact_frequencies is not None
        assert exact_bits(active.exact_weights) <= SHORTEN_ABOVE_BITS
        assert all(
            exact_bits(row) <= SHORTEN_ABOVE_BITS for row in active.exact_frequencies
        )
        point = active.exact_point()
        assert point is not None and _is_member(point, data)
        assert exact_bits(point) <= SHORTEN_ABOVE_BITS
    _check_exact(active)
    for row in active.exact_frequencies:
        assert _is_member(row, data)


# ---------------------------------------------------------------------------
# Singletons: unchanged, bit for bit.
# ---------------------------------------------------------------------------

#: The pairwise loop at a development commit (before the shortening), 12 iterations from
#: ``random_choi_point(p, 1)`` at alpha 1.5 with the singleton (0.875, 0.125):
#: objective, bracket and gap as hex, and the sha256 of the final iterate's
#: bytes in sorted joint-sector order. A REGRESSION PIN captured by running
#: that commit.
#: KEYED BY PLATFORM (tests/support/platform_pins.py): the values are the
#: Windows machine's, plus the macOS arm64 value where one is recorded. A field
#: a platform has not recorded fails with the values to record.
#: THE BRACKET'S FEASIBLE SIDE is the bound verified from the oracle's dual
#: (frank-wolfe/req:verified-feasible-side), not the pairing with the return;
#: the objective, the gap and the iterate do not depend on it.
PAIRWISE_PINNED: PinTable = {
    WINDOWS_AMD64_OPENBLAS: {
        "decoy/qics": {
            "objective": "0x1.a9bde1dadca7ep+0",
            "bracket": "0x1.a9a4ae6ff0048p+0",
            "gap": "0x1.936c151740280p-12",
            "choi_sha256": (
                "b3b5285f722f48ec1edb6553416425d3f0ac516873311239f6858795c70c3cc7"
            ),
        },
        "decoy/spectral": {
            "objective": "0x1.a9bde9b7f59bap+0",
            "bracket": "0x1.a99a3b73f1f77p+0",
            "gap": "0x1.1dab78338ee00p-11",
            "choi_sha256": (
                "e6a6dbdb71832a95012c287f9df5e6e839138bc44500d55a8f4ff86ffa32e466"
            ),
        },
        "q3/qics": {
            "objective": "0x1.5e8b03a884368p+0",
            "bracket": "0x1.5e25a4d0a769cp+0",
            "gap": "0x1.95a9f03156000p-10",
            "choi_sha256": (
                "4bb25539af2cdb584ef04ae5f16563d8ea7fa5735147b9b7a289f8946c49864e"
            ),
        },
    },
    DARWIN_ARM64_ACCELERATE: {
        "decoy/spectral": {"objective": "0x1.a9bde2193418cp+0"},
        "q3/qics": {"objective": "0x1.5e8af301e2416p+0"},
    },
}

#: The three cases, as (toy, oracle), in the order the test ids number them.
PAIRWISE_PINNED_CASES: tuple[tuple[str, str], ...] = (
    ("decoy", "qics"),
    ("decoy", "spectral"),
    ("q3", "qics"),
)


def _choi_digest(choi: Mapping[Any, Any]) -> str:
    digest = sha256()
    for pair in sorted(choi):
        digest.update(
            np.ascontiguousarray(np.asarray(choi[pair], np.complex128)).tobytes()
        )
    return digest.hexdigest()


@pytest.mark.pins
@pytest.mark.requires_qics
@pytest.mark.parametrize("case", PAIRWISE_PINNED_CASES)
def test_a_singleton_pairwise_run_is_unchanged_bit_for_bit(
    case: tuple[str, str],
) -> None:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    name, oracle_choice = case
    declaration = (
        decoy_like_general() if name == "decoy" else qubit_bb84_general(messages=3)
    )
    maps = maps_of(declaration)
    values = list(maps.declaration.acceptance_values)
    acceptance = SingletonAcceptanceOracle({values[0]: 0.875, values[1]: 0.125})
    result = joint_driver.run_joint_frank_wolfe(
        maps,
        QicsSectorChoiOracle(),
        acceptance,
        random_choi_point(maps.parametrization, 1),
        1.5,
        JointFrankWolfeOptions(
            max_iterations=12, step_rule="pairwise", oracle=oracle_choice
        ),
    )
    assert result.h_lb is not None
    assert_pinned(
        PAIRWISE_PINNED,
        f"{name}/{oracle_choice}",
        {
            "objective": result.objective.hex(),
            "bracket": result.h_lb.hex(),
            "gap": result.gap.hex(),
            "choi_sha256": _choi_digest(result.choi),
        },
        where=(
            "tests/unit/test_joint_polytope_iterate_exact.py, "
            "PAIRWISE_PINNED"
        ),
    )
    # The q of a singleton never moves and every gate keeps the island.
    assert dict(result.q) == {values[0]: 0.875, values[1]: 0.125}
    assert all(gate.acceptance_iterate_exact for gate in result.gates)


def test_the_pairwise_active_set_gives_up_before_far_overshooting_the_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail-closed under pairwise: the carried point never runs far past the cap.

    The cap reads the carried point and the weights as well as the atoms'
    halves: with no member ever shortening, the carried point sum_i w_i q_i
    would run an order of magnitude past a cap on the halves alone before the
    exact side was given up.
    """
    import certiqs_key.solvers.frank_wolfe.joint_pairwise as joint_pairwise

    cap = 5000
    monkeypatch.setattr(joint_pairwise, "EXACT_BITS_CAP", cap)
    data = POLYTOPES["segment"]
    oracle = _ExactPolytope(data)
    start = tuple(oracle.exact_start().values())
    strict = _ExactPolytope(
        data, contains=lambda point: tuple(point.values()) == start
    )
    shortener = AcceptanceIterate.start(strict).shortener
    assert shortener is not None
    vertices = [
        tuple(oracle.exact_minimize({"c0": a, "c1": b}).values())
        for a, b in ((1.0, -1.0), (-1.0, 1.0))
    ]
    rng = np.random.default_rng(3)
    active = ActiveSet.single(
        np.zeros(1, np.complex128), np.asarray([float(x) for x in start]), start
    )
    for step in range(3000):
        atom = shrink_frequencies_exact(vertices[step % 2], start)
        floats = np.asarray([float(x) for x in atom])
        block = rng.normal(size=1).astype(np.complex128)
        before = active
        active = active.frank_wolfe(block, floats, float(rng.uniform(0.2, 0.6)), atom)
        active = active.bounded(shortener.shorten)
        if active.exact_weights is None:
            assert before.exact_q is not None
            assert exact_bits(before.exact_q) <= 2 * cap
            return
    pytest.fail("the exact side was never given up")
