"""The loop's one ``q`` rule: exact partial minimisation, chosen by geometry alone.

On a canonical
box ``q`` is ``argmin_q f(J, q)`` at every point the loop evaluates and at
every line-search trial; a singleton is untouched; any other polytope keeps
the previous step toward the exact LP vertex. What is tested, and the defect
each test would catch:

* the box solve is OPTIMAL -- against an independent general-purpose solver
  (scipy's SLSQP) on random boxes and random exponents, and against a dense
  grid of the real objective of a declaration at random Choi points;
* the snap makes an EXACT MEMBER of the box from any binary64 view, and the
  driver evaluates only at roundings of such members, with every gate on the
  island;
* the rule is SELECTED BY GEOMETRY ALONE: the code that selects and runs it
  names no protocol, instance or route, the same box under two different
  declarations gets the same rule, and the same declaration with a
  non-box polytope or a singleton gets none;
* a general polytope FALLS BACK to the previous vertex step, and a box run
  never takes that step;
* the objective along a box run never exceeds the previous rule's first step
  (a sanity bound: ``g(J) <= f(J, q)`` for every member ``q``);
* the pairwise rule composes: its atoms are ``J``-only and it certifies;
* the box solve's degenerate branches (every coordinate fixed, uppers that
  cannot hold the mass, lowers that already hold it, the first interval with
  zero lowers, a coordinate clipped at a bound) against hand-derived answers,
  each snapped to an exact member;
* a singleton run, and a general polytope's fallback run, are bit-identical
  to the loop at a development commit (regression pins captured by running
  that commit, not oracles);
* the solver report names the rule that ran (``q_rule``), for the record.
"""

from __future__ import annotations

import io
import math
import random
import tokenize
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from scipy.optimize import minimize
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

import certiqs_key.solvers.frank_wolfe.joint_driver as joint_driver
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet, PolytopeData
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.objective.joint import (
    JointBranchValues,
    joint_objective_value,
)
from certiqs_key.solvers.frank_wolfe import general_keyrate
from certiqs_key.solvers.frank_wolfe.acceptance_iterate import AcceptanceIterate
from certiqs_key.solvers.frank_wolfe.joint_options import JointFrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.q_rule import (
    BoxPartialMinimum,
    box_argmin,
    q_rule_for,
)
from certiqs_key.solvers.oracles.acceptance import SingletonAcceptanceOracle

REPOSITORY = Path(__file__).resolve().parents[2]
ALPHA = 1.5

#: A box on the toys' two acceptance values (match, mismatch) whose minimiser
#: is not the averaged start, so the rule has somewhere to move ``q``.
BOX_LOWER = (0.5, 0.0625)
BOX_UPPER = (0.9375, 0.5)


def _box(lower: tuple[float, ...], upper: tuple[float, ...]) -> PolytopeData:
    """Return the canonical box ``[lower, upper]`` in the rows of eq:boxrows."""
    size = len(lower)
    return PolytopeData(
        columns=size,
        rows=tuple(tuple(float(i == j) for j in range(size)) for i in range(size))
        + tuple(tuple(-float(i == j) for j in range(size)) for i in range(size)),
        rhs=(*upper, *(-v for v in lower)),
        box_bounds=(lower, upper),
    )


def _with(declaration: GeneralDeclaration, data: PolytopeData) -> GeneralDeclaration:
    return replace(
        declaration, acceptance_set=AcceptanceSet(geometry="polytope", polytope=data)
    )


def _branch(p: float, k: float) -> JointBranchValues:
    return JointBranchValues(
        p=p, k=k, deficits={}, dropped_pairs=(), skipped_key_inert=()
    )


def _rule(
    lower: tuple[float, ...], upper: tuple[float, ...], live: tuple[bool, ...]
) -> BoxPartialMinimum:
    return BoxPartialMinimum(
        values=tuple(f"c{i}" for i in range(len(lower))),
        lower=tuple(Fraction(v) for v in lower),
        upper=tuple(Fraction(v) for v in upper),
        live=live,
        alpha=ALPHA,
    )


def _entropy_objective(q: np.ndarray, m: np.ndarray) -> float:
    """``sum_c q_c (log2 q_c - m_c)`` with ``0 log 0 = 0``; the solve's objective."""
    total = 0.0
    for value, exponent in zip(q, m, strict=True):
        if value > 0.0:
            total += float(value) * (math.log2(float(value)) - float(exponent))
    return total


# ---------------------------------------------------------------------------
# The box solve is optimal.
# ---------------------------------------------------------------------------


def _random_box(rng: random.Random, size: int) -> tuple[tuple[float, ...], ...]:
    while True:
        lower = tuple(rng.randrange(0, 5) / 32 for _ in range(size))
        upper = tuple(min(1.0, value + rng.randrange(1, 33) / 32) for value in lower)
        if sum(lower) <= 1.0 <= sum(upper):
            return lower, upper


@pytest.mark.parametrize("seed", range(40))
def test_the_box_solve_matches_an_independent_solver(seed: int) -> None:
    rng = random.Random(seed)
    size = rng.randint(2, 6)
    lower, upper = _random_box(rng, size)
    m = np.asarray([rng.uniform(-12.0, 2.0) for _ in range(size)])
    low, high = np.asarray(lower), np.asarray(upper)
    ours = box_argmin(m, low, high)
    assert np.all(ours >= low) and np.all(ours <= high)
    assert float(np.sum(ours)) == pytest.approx(1.0, abs=1e-14)
    best = math.inf
    for start in range(4):
        sample = np.asarray([rng.random() + 1e-3 for _ in range(size)])
        guess = np.clip(sample, low, high)
        found = minimize(
            lambda q: _entropy_objective(np.maximum(q, 0.0), m),
            guess if start else (low + high) / 2.0,
            method="SLSQP",
            bounds=list(zip(lower, upper, strict=True)),
            constraints=[{"type": "eq", "fun": lambda q: float(np.sum(q)) - 1.0}],
            options={"ftol": 1e-14, "maxiter": 500},
        )
        if found.success and abs(float(np.sum(found.x)) - 1.0) < 1e-9:
            best = min(best, _entropy_objective(np.maximum(found.x, 0.0), m))
    assert math.isfinite(best), "the independent solver found no point"
    assert _entropy_objective(ours, m) <= best + 1e-9


def test_a_coordinate_with_no_mass_sits_at_its_lower_bound() -> None:
    """``P = 0`` gives ``d(q, 0) = +inf`` at ``q > 0``: the solve sits at ``l^-``."""
    rule = _rule((0.0, 0.125, 0.0), (1.0, 1.0, 1.0), (True, False, False))
    q = rule.minimise(
        {"c0": _branch(0.5, 0.25), "c1": _branch(0.0, 0.0), "c2": _branch(0.5, 0.5)}
    )
    assert q["c1"] == 0.125
    assert q["c0"] > 0.0 and q["c2"] > 0.0


def _member(
    q: np.ndarray, lower: tuple[float, ...], upper: tuple[float, ...]
) -> dict[str, Fraction]:
    """Snap ``q`` with :meth:`BoxPartialMinimum.exact_member` and check membership."""
    rule = _rule(lower, upper, (False,) * len(lower))
    exact = rule.exact_member({f"c{i}": float(v) for i, v in enumerate(q)})
    assert sum(exact.values(), Fraction(0)) == 1
    for chat, lo, hi in zip(rule.values, rule.lower, rule.upper, strict=True):
        assert lo <= exact[chat] <= hi
    return exact


def test_box_argmin_with_every_coordinate_fixed_returns_the_bounds() -> None:
    """``l = u`` everywhere: nothing is free, the box's one point comes back."""
    q = box_argmin(
        np.asarray([0.0, -5.0]), np.asarray([0.25, 0.75]), np.asarray([0.25, 0.75])
    )
    assert q.tolist() == [0.25, 0.75]
    assert _member(q, (0.25, 0.75), (0.25, 0.75)) == {
        "c0": Fraction(1, 4),
        "c1": Fraction(3, 4),
    }


def test_box_argmin_leaves_the_mass_the_uppers_cannot_hold_to_the_snap() -> None:
    """Hand-derived: ``m = (0, -inf)``, ``u = (1/2, 1)``, ``l = 0``.

    Coordinate 1 has no mass (``m = -inf``) and sits at its lower bound 0; the
    one free coordinate cannot hold the mass 1, so the solve returns it at its
    upper bound, ``q = (1/2, 0)``, summing to 1/2 -- the contract: the rest is
    the caller's exact repair (the value there is ``+inf`` whatever ``q`` is).
    The snap then moves the exact residual 1/2 onto coordinate 1, the one with
    room: ``(1/2, 1/2)``, an exact member.
    """
    q = box_argmin(
        np.asarray([0.0, -np.inf]), np.asarray([0.0, 0.0]), np.asarray([0.5, 1.0])
    )
    assert q.tolist() == [0.5, 0.0]
    assert _member(q, (0.0, 0.0), (0.5, 1.0)) == {
        "c0": Fraction(1, 2),
        "c1": Fraction(1, 2),
    }


def test_box_argmin_with_the_lowers_already_holding_the_mass_returns_them() -> None:
    """Hand-derived: ``l = (1/2, 1/2)`` sums to one, so it is the box's only point.

    And with a fixed third coordinate (``m = -inf`` at ``l = 1/4``) the free
    lowers ``(1/4, 1/2)`` already hold the remaining mass ``3/4``.
    """
    q = box_argmin(
        np.asarray([0.0, 0.0]), np.asarray([0.5, 0.5]), np.asarray([1.0, 1.0])
    )
    assert q.tolist() == [0.5, 0.5]
    assert _member(q, (0.5, 0.5), (1.0, 1.0)) == {
        "c0": Fraction(1, 2),
        "c1": Fraction(1, 2),
    }
    lower = (0.25, 0.5, 0.25)
    q = box_argmin(
        np.asarray([0.0, 3.0, -np.inf]), np.asarray(lower), np.asarray([1.0, 1.0, 1.0])
    )
    assert q.tolist() == [0.25, 0.5, 0.25]
    assert _member(q, lower, (1.0, 1.0, 1.0)) == {
        "c0": Fraction(1, 4),
        "c1": Fraction(1, 2),
        "c2": Fraction(1, 4),
    }


def test_box_argmin_in_the_first_interval_with_zero_lowers() -> None:
    """Hand-derived: ``m = (0, -3)`` on ``[0, 1]^2``.

    Both lowers are 0, so no lower breakpoint exists and the crossing lies in
    the first interval ``(-inf, 0]`` of ``theta``. Free coordinates satisfy
    ``q_c = 2^(m_c + theta)``; ``sum = 1`` gives ``2^theta (1 + 1/8) = 1``, so
    ``q = (8/9, 1/9)``.
    """
    q = box_argmin(
        np.asarray([0.0, -3.0]), np.asarray([0.0, 0.0]), np.asarray([1.0, 1.0])
    )
    assert q[0] == pytest.approx(8 / 9, rel=1e-15)
    assert q[1] == pytest.approx(1 / 9, rel=1e-15)
    exact = _member(q, (0.0, 0.0), (1.0, 1.0))
    assert abs(exact["c0"] - Fraction(8, 9)) < Fraction(1, 2**50)


def test_box_argmin_pins_a_lopsided_coordinate_at_its_bound() -> None:
    """Hand-derived, the same exponents ``(0, -3)`` with a binding bound.

    Unconstrained ``q = (8/9, 1/9)``. With ``u_0 = 3/4 < 8/9`` coordinate 0 is
    clipped to 3/4 and coordinate 1 takes the rest, 1/4 (which is in its
    interval). With ``l_1 = 1/4 > 1/9`` instead, coordinate 1 is clipped up to
    1/4 and coordinate 0 takes 3/4. Both are exact in binary64.
    """
    for lower, upper in (((0.0, 0.0), (0.75, 1.0)), ((0.0, 0.25), (1.0, 1.0))):
        q = box_argmin(np.asarray([0.0, -3.0]), np.asarray(lower), np.asarray(upper))
        assert q.tolist() == [0.75, 0.25]
        assert _member(q, lower, upper) == {"c0": Fraction(3, 4), "c1": Fraction(1, 4)}


@pytest.mark.requires_qics
@pytest.mark.parametrize("seed", range(6))
def test_the_rule_minimises_the_real_objective_at_random_choi_points(seed: int) -> None:
    """Against a dense grid of ``joint_objective_value`` itself."""
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    rng = random.Random(100 + seed)
    lower, upper = _random_box(rng, 2)
    declaration = _with(decoy_like_general(), _box(lower, upper))
    maps, acceptance = general_keyrate._prepare_general(
        declaration, QicsSectorChoiOracle()
    )
    rule = q_rule_for(acceptance, maps, ALPHA)
    assert rule is not None
    point = random_choi_point(maps.parametrization, seed)
    exact, value = rule.exact_at(maps, point, dropped=frozenset(), skip_key_inert=True)
    values = maps.declaration.acceptance_values

    def objective(x: np.ndarray) -> float:
        q = {values[0]: float(x[0]), values[1]: 1.0 - float(x[0])}
        return joint_objective_value(maps, q, point, ALPHA)

    lo = max(lower[0], 1.0 - upper[1])
    hi = min(upper[0], 1.0 - lower[1])
    grid = np.linspace(lo, hi, 2001)
    assert value <= min(objective(np.asarray([x])) for x in grid) + 1e-12
    assert value == pytest.approx(
        joint_objective_value(
            maps, {chat: float(v) for chat, v in exact.items()}, point, ALPHA
        ),
        abs=0.0,
    )


# ---------------------------------------------------------------------------
# The snap: an exact member of the box by construction.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(30))
def test_the_snap_is_an_exact_member_of_the_box(seed: int) -> None:
    rng = random.Random(seed)
    size = rng.randint(2, 6)
    lower, upper = _random_box(rng, size)
    rule = _rule(lower, upper, (False,) * size)
    # A view that is off in every way a binary64 solve can be: outside a bound
    # by a little, and not summing to one.
    raw = [
        rng.uniform(lo - 1e-3, hi + 1e-3) for lo, hi in zip(lower, upper, strict=True)
    ]
    view = {f"c{i}": max(0.0, value) for i, value in enumerate(raw)}
    exact = rule.exact_member(view)
    assert all(isinstance(value, Fraction) for value in exact.values())
    assert sum(exact.values(), Fraction(0)) == 1
    for chat, lo, hi in zip(rule.values, rule.lower, rule.upper, strict=True):
        assert lo <= exact[chat] <= hi


def test_the_snap_leaves_an_exact_member_where_it_is() -> None:
    rule = _rule((0.25, 0.125), (0.75, 0.75), (False, False))
    view = {"c0": 0.625, "c1": 0.375}
    assert rule.exact_member(view) == {"c0": Fraction(5, 8), "c1": Fraction(3, 8)}


def _box_run(
    monkeypatch: pytest.MonkeyPatch,
    options: Any,
    *,
    declaration: GeneralDeclaration | None = None,
    seed: int = 1,
) -> tuple[Any, list[dict[str, Fraction]], list[dict[str, float]]]:
    """Run the box toy from a random coupled start; record exact q and evaluated q."""
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    declaration = declaration or _with(decoy_like_general(), _box(BOX_LOWER, BOX_UPPER))
    maps, acceptance = general_keyrate._prepare_general(
        declaration, QicsSectorChoiOracle()
    )
    members: list[dict[str, Fraction]] = []
    evaluated: list[dict[str, float]] = []
    original_member = BoxPartialMinimum.exact_member
    original_gradient = joint_driver.joint_gradient

    def recording_member(self: BoxPartialMinimum, view: Any) -> dict[str, Fraction]:
        member = original_member(self, view)
        members.append(member)
        return member

    def recording_gradient(maps_: Any, q: Any, *args: Any, **kw: Any) -> Any:
        evaluated.append(dict(q))
        return original_gradient(maps_, q, *args, **kw)

    monkeypatch.setattr(BoxPartialMinimum, "exact_member", recording_member)
    monkeypatch.setattr(joint_driver, "joint_gradient", recording_gradient)
    start = random_choi_point(maps.parametrization, seed)
    result = joint_driver.run_joint_frank_wolfe(
        maps, QicsSectorChoiOracle(), acceptance, start, ALPHA, options
    )
    return result, members, evaluated


@pytest.mark.requires_qics
@pytest.mark.parametrize("step_rule", ["vanilla", "pairwise"])
def test_every_evaluated_q_is_the_rounding_of_an_exact_member(
    monkeypatch: pytest.MonkeyPatch, step_rule: str
) -> None:
    options = JointFrankWolfeOptions(max_iterations=12, step_rule=step_rule)
    result, members, evaluated = _box_run(monkeypatch, options)
    lower = [Fraction(v) for v in BOX_LOWER]
    upper = [Fraction(v) for v in BOX_UPPER]
    for member in members:
        assert sum(member.values(), Fraction(0)) == 1
        for value, lo, hi in zip(member.values(), lower, upper, strict=True):
            assert lo <= value <= hi
    roundings = [{chat: float(v) for chat, v in member.items()} for member in members]
    assert evaluated
    for q in evaluated:
        assert q in roundings
    assert result.gates
    assert all(gate.acceptance_iterate_exact for gate in result.gates)
    assert result.h_lb is not None


# ---------------------------------------------------------------------------
# Selection by geometry alone.
# ---------------------------------------------------------------------------

#: Names of protocols, instances and routes that must not appear in the code
#: that selects or runs the rule: every instance directory, plus the protocol
#: families and routes this repository knows.
_FORBIDDEN_WORDS = {
    *(
        path.name.lower()
        for path in (REPOSITORY / "instances").iterdir()
        if path.is_dir() and not path.name.startswith("_")
    ),
    "decoy",
    "bb84",
    "bbm92",
    "b92",
    "e91",
    "sixstate",
    "six_state",
    "optical",
    "encoded",
    "licensed",
    "twin",
    "tf_qkd",
}


def _code_tokens(path: Path) -> list[str]:
    """Return the names and string literals of a module, docstrings excluded.

    Comments and docstrings are not logic; every name and every
    other string literal is.
    """
    source = path.read_text(encoding="utf-8")
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    out: list[str] = []
    previous = tokenize.NEWLINE
    for token in tokens:
        if token.type == tokenize.STRING and previous in (
            tokenize.NEWLINE,
            tokenize.NL,
            tokenize.INDENT,
            tokenize.DEDENT,
        ):
            previous = token.type
            continue  # a docstring or a bare string statement
        if token.type in (tokenize.NAME, tokenize.STRING):
            out.append(token.string.lower())
        if token.type not in (tokenize.COMMENT, tokenize.NL):
            previous = token.type
    return out


@pytest.mark.parametrize(
    "module",
    [
        "src/certiqs_key/solvers/frank_wolfe/q_rule.py",
        "src/certiqs_key/solvers/frank_wolfe/joint_driver.py",
        "src/certiqs_key/solvers/frank_wolfe/joint_pairwise.py",
    ],
)
def test_the_rule_names_no_protocol_instance_or_route(module: str) -> None:
    tokens = _code_tokens(REPOSITORY / module)
    assert tokens
    hits = sorted(
        {word for word in _FORBIDDEN_WORDS for token in tokens if word in token}
    )
    assert hits == [], f"{module} names {hits} in its code"


@pytest.mark.requires_qics
def test_the_same_box_gets_the_same_rule_under_different_declarations() -> None:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    data = _box(BOX_LOWER, BOX_UPPER)
    rules = []
    for base in (decoy_like_general(), qubit_bb84_general()):
        maps, acceptance = general_keyrate._prepare_general(
            _with(base, data), QicsSectorChoiOracle()
        )
        rule = q_rule_for(acceptance, maps, ALPHA)
        assert rule is not None
        rules.append(rule)
    assert rules[0] == rules[1]


@pytest.mark.requires_qics
def test_a_non_box_polytope_and_a_singleton_get_no_rule() -> None:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    # A genuinely non-box polytope; row-only boxes now get the same rule.
    tilted = PolytopeData(columns=2, rows=((1.0, -1.0),), rhs=(0.5,))
    for data in (tilted,):
        maps, acceptance = general_keyrate._prepare_general(
            _with(decoy_like_general(), data), QicsSectorChoiOracle()
        )
        assert q_rule_for(acceptance, maps, ALPHA) is None
    maps = maps_of(decoy_like_general())
    singleton = SingletonAcceptanceOracle({"match": 0.875, "mismatch": 0.125})
    assert q_rule_for(singleton, maps, ALPHA) is None


@pytest.mark.requires_qics
def test_row_only_box_has_identical_rule_and_run() -> None:
    """Exact row recognition makes metadata and row-only boxes interchangeable."""
    from certiqs_key.solvers.frank_wolfe.joint_driver import joint_initial_point
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    box = _box(BOX_LOWER, BOX_UPPER)
    records = []
    rules = []
    for data in (box, replace(box, box_bounds=None)):
        oracle = QicsSectorChoiOracle()
        maps, acceptance = general_keyrate._prepare_general(
            _with(decoy_like_general(), data), oracle
        )
        rules.append(q_rule_for(acceptance, maps, ALPHA))
        result = joint_driver.run_joint_frank_wolfe(
            maps,
            oracle,
            acceptance,
            joint_initial_point(maps.parametrization),
            ALPHA,
            JointFrankWolfeOptions(max_iterations=3, oracle="spectral"),
        )
        records.append((result.h_lb, result.objective, result.q, result.gates))
    assert rules[0] is not None and rules[0] == rules[1]
    assert records[0] == records[1]


# ---------------------------------------------------------------------------
# The fallback, the sanity bound and the pairwise rule.
# ---------------------------------------------------------------------------


@pytest.mark.requires_qics
def test_a_general_polytope_falls_back_to_the_vertex_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The previous rule runs there, and the box path never runs."""
    steps: list[float] = []
    original = AcceptanceIterate.toward

    def counted(self: AcceptanceIterate, vertex: Any, step: float) -> Any:
        steps.append(step)
        return original(self, vertex, step)

    monkeypatch.setattr(AcceptanceIterate, "toward", counted)
    tilted = PolytopeData(columns=2, rows=((1.0, -1.0),), rhs=(0.5,))
    result, members, _ = _box_run(
        monkeypatch,
        JointFrankWolfeOptions(max_iterations=6),
        declaration=_with(decoy_like_general(), tilted),
    )
    assert steps, "the fallback took no vertex step"
    assert members == [], "a general polytope ran the box solve"
    assert all(gate.acceptance_iterate_exact for gate in result.gates)

    steps.clear()
    _box_run(monkeypatch, JointFrankWolfeOptions(max_iterations=6))
    assert steps == [], "a box run took the vertex step"


@pytest.mark.requires_qics
def test_the_objective_never_exceeds_the_previous_rules_first_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``g(J) = min_q f(J, q) <= f(J, q')``: the start and every step start lower.

    The previous rule's one-step run is obtained by withholding the rule
    (``q_rule_for`` returning ``None``), which is what a non-box polytope gets.
    """
    options = JointFrankWolfeOptions(max_iterations=1)
    with monkeypatch.context() as context:
        context.setattr(joint_driver, "q_rule_for", lambda *args: None)
        previous, _, _ = _box_run(context, options)
    ours, _, _ = _box_run(monkeypatch, JointFrankWolfeOptions(max_iterations=10))
    first_step = previous.objective
    assert ours.gates[0].objective <= previous.gates[0].objective
    for gate in ours.gates:
        assert gate.objective <= first_step
    objectives = [gate.objective for gate in ours.gates]
    assert objectives == sorted(objectives, reverse=True)
    assert ours.objective <= first_step


@pytest.mark.requires_qics
def test_pairwise_composes_with_the_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    """Its atoms are J-only, it takes pairwise steps, and it certifies."""
    sizes: list[int] = []
    original = joint_driver._pairwise_iteration

    def watched(*args: Any, **kw: Any) -> Any:
        active = args[2]
        sizes.append(int(active.frequencies.shape[1]))
        return original(*args, **kw)

    monkeypatch.setattr(joint_driver, "_pairwise_iteration", watched)
    options = JointFrankWolfeOptions(max_iterations=30, step_rule="pairwise")
    result, _, _ = _box_run(monkeypatch, options, seed=2)
    assert sizes and set(sizes) == {0}, "the atoms carry a q half"
    report = result.solver_report["pairwise"]
    taken = result.timings.calls.get("accepted_point_objective", 0) - (
        result.timings.calls.get("accepted_point_rejected", 0)
    )
    assert taken > report["fallbacks"], "no pairwise step was ever taken"
    assert result.h_lb is not None
    assert all(gate.acceptance_iterate_exact for gate in result.gates)
    assert result.objective < result.gates[0].objective


# ---------------------------------------------------------------------------
# A singleton is bit-identical to the loop before this change.
# ---------------------------------------------------------------------------

#: The loop at a development commit, captured by running it: the decoy toy from
#: ``random_choi_point(p, 3)`` at alpha 1.5 with the singleton
#: (0.875, 0.125), the spectral oracle, 15 iterations; the objective, bracket
#: and gap as hex, and the sha256 of the final iterate's bytes in sorted
#: joint-sector order. A REGRESSION PIN, not an oracle.
#: KEYED BY PLATFORM (tests/support/platform_pins.py): the values are the
#: Windows machine's, plus the macOS arm64 value where one is recorded. A field
#: a platform has not recorded fails with the values to record.
#: THE BRACKET'S FEASIBLE SIDE is the bound verified from the oracle's dual
#: (frank-wolfe/req:verified-feasible-side), not the pairing with the return;
#: the objective, the gap and the iterate do not depend on it.
PINNED_SINGLETON: PinTable = {
    WINDOWS_AMD64_OPENBLAS: {
        "vanilla": {
            "objective": "0x1.a9be4ae8e58cap+0",
            "bracket": "0x1.a941e25211313p+0",
            "gap": "0x1.f29c8293b6b00p-10",
            "choi_sha256": (
                "6d59269b7872ed76e646a0ad6ba79b3bc2f751c6d546566aeeea8cbe4b023595"
            ),
        },
        "pairwise": {
            "objective": "0x1.a9bddff59f152p+0",
            "bracket": "0x1.a9aba6b445061p+0",
            "gap": "0x1.6821f9bf75200p-12",
            "choi_sha256": (
                "c57d5d3d2d08d0ef0305b435bed35d7fcfea474f34ce7a7420c4a1b48ff6862f"
            ),
        },
    },
    DARWIN_ARM64_ACCELERATE: {
        "vanilla": {"objective": "0x1.a9be4ae8a186dp+0"},
        "pairwise": {"objective": "0x1.a9bdde76c5de0p+0"},
    },
}


def _choi_digest(choi: Any) -> str:
    digest = sha256()
    for pair in sorted(choi):
        digest.update(
            np.ascontiguousarray(np.asarray(choi[pair], np.complex128)).tobytes()
        )
    return digest.hexdigest()


def _singleton_run(step_rule: str) -> Any:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    maps = maps_of(decoy_like_general())
    start = random_choi_point(maps.parametrization, 3)
    acceptance = SingletonAcceptanceOracle({"match": 0.875, "mismatch": 0.125})
    options = JointFrankWolfeOptions(
        max_iterations=15, oracle="spectral", step_rule=step_rule
    )
    return joint_driver.run_joint_frank_wolfe(
        maps, QicsSectorChoiOracle(), acceptance, start, ALPHA, options
    )


@pytest.mark.pins
@pytest.mark.requires_qics
@pytest.mark.parametrize("step_rule", ["vanilla", "pairwise"])
def test_a_singleton_run_matches_its_pin_bit_for_bit(step_rule: str) -> None:
    result = _singleton_run(step_rule)
    assert result.h_lb is not None
    assert_pinned(
        PINNED_SINGLETON,
        step_rule,
        {
            "objective": result.objective.hex(),
            "bracket": result.h_lb.hex(),
            "gap": result.gap.hex(),
            "choi_sha256": _choi_digest(result.choi),
        },
        where="tests/unit/test_exact_q_rule.py, PINNED_SINGLETON",
    )
    assert result.q == {"match": 0.875, "mismatch": 0.125}


# ---------------------------------------------------------------------------
# A general polytope's fallback is bit-identical to the plain vertex-step loop.
# ---------------------------------------------------------------------------

#: The fallback at the same development commit: the decoy toy with the
#: box-free tilted polytope ``q_match - q_mismatch <= 1/2`` (on the simplex), from
#: ``random_choi_point(p, 3)`` at alpha 1.5, the spectral oracle, 15
#: iterations; objective, bracket, gap and the final ``q`` as hex, and the
#: sha256 of the final iterate's bytes as in :data:`PINNED_SINGLETON`.
#: CAPTURED from an export of that commit, never from the working tree. A
#: REGRESSION PIN, not an oracle.
#: KEYED BY PLATFORM (tests/support/platform_pins.py): the values are the
#: Windows machine's, plus the macOS arm64 value where one is recorded. A field
#: a platform has not recorded fails with the values to record.
#: THE BRACKET'S FEASIBLE SIDE is the bound verified from the oracle's dual
#: (frank-wolfe/req:verified-feasible-side), not the pairing with the return;
#: the objective, the gap and the iterate do not depend on it.
PINNED_FALLBACK: PinTable = {
    WINDOWS_AMD64_OPENBLAS: {
        "vanilla": {
            "objective": "0x1.5344b3fb23d27p-3",
            "bracket": "0x1.335097b965612p-3",
            "gap": "0x1.7e96cdf070380p-6",
            "choi_sha256": (
                "12b65f6ccefbf54425a5b67ea4ba15ebe730a2f38afd7c064802c078c0be604b"
            ),
            "q_match": "0x1.eae532fe71a3bp-2",
            "q_mismatch": "0x1.0a8d6680c72e3p-1",
        },
        "pairwise": {
            "objective": "0x1.52874ac954d92p-3",
            "bracket": "0x1.3399ea00352fep-3",
            "gap": "0x1.beb6bc42d6f80p-6",
            "choi_sha256": (
                "a3f24acc09ecb210be137785f57d892b62e7a1d085a3431a217089cb094ce1b2"
            ),
            "q_match": "0x1.eb101765cf99dp-2",
            "q_mismatch": "0x1.0a77f44d18331p-1",
        },
    },
}


@pytest.mark.pins
@pytest.mark.requires_qics
@pytest.mark.parametrize("step_rule", ["vanilla", "pairwise"])
def test_a_polytope_fallback_run_matches_its_pin_bit_for_bit(step_rule: str) -> None:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    tilted = PolytopeData(columns=2, rows=((1.0, -1.0),), rhs=(0.5,))
    maps, acceptance = general_keyrate._prepare_general(
        _with(decoy_like_general(), tilted), QicsSectorChoiOracle()
    )
    assert q_rule_for(acceptance, maps, ALPHA) is None
    start = random_choi_point(maps.parametrization, 3)
    options = JointFrankWolfeOptions(
        max_iterations=15, oracle="spectral", step_rule=step_rule
    )
    result = joint_driver.run_joint_frank_wolfe(
        maps, QicsSectorChoiOracle(), acceptance, start, ALPHA, options
    )
    assert result.h_lb is not None
    assert_pinned(
        PINNED_FALLBACK,
        step_rule,
        {
            "objective": result.objective.hex(),
            "bracket": result.h_lb.hex(),
            "gap": result.gap.hex(),
            "choi_sha256": _choi_digest(result.choi),
            "q_match": result.q["match"].hex(),
            "q_mismatch": result.q["mismatch"].hex(),
        },
        where="tests/unit/test_exact_q_rule.py, PINNED_FALLBACK",
    )
    assert all(gate.acceptance_iterate_exact for gate in result.gates)
    assert result.solver_report["q_rule"] == "vertex-step"


# ---------------------------------------------------------------------------
# The record says which q rule ran.
# ---------------------------------------------------------------------------


@pytest.mark.requires_qics
def test_the_solver_report_names_the_q_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    """A box run reports ``box-partial-minimum``; a singleton ``vertex-step``."""
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    box, _, _ = _box_run(monkeypatch, JointFrankWolfeOptions(max_iterations=2))
    assert box.solver_report["q_rule"] == "box-partial-minimum"
    maps = maps_of(decoy_like_general())
    singleton = joint_driver.run_joint_frank_wolfe(
        maps,
        QicsSectorChoiOracle(),
        SingletonAcceptanceOracle({"match": 0.875, "mismatch": 0.125}),
        random_choi_point(maps.parametrization, 3),
        ALPHA,
        JointFrankWolfeOptions(max_iterations=2),
    )
    assert singleton.solver_report["q_rule"] == "vertex-step"
