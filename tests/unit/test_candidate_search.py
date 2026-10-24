"""Independent coupling/gradient properties and candidate capability regressions."""

from __future__ import annotations

import math
import time
from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest
from tests.support.general_toys import (
    qubit_bb84_general,
    random_choi_point,
    two_factor_general,
)

from certiqs_key.meat_core.acceptance.box import canonical_box
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet, PolytopeData
from certiqs_key.meat_core.objective.joint import joint_objective_value
from certiqs_key.meat_core.objective.linalg import hermitian_part
from certiqs_key.solvers.frank_wolfe.joint_options import JointFrankWolfeOptions
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle
from certiqs_key.solvers.problem import PreparedProblem, prepare_problem
from certiqs_key.solvers.search import entropy as entropy_module
from certiqs_key.solvers.search import stable
from certiqs_key.solvers.search.common import (
    CorrectiveSettings,
    EntropySettings,
    FactorSettings,
    capability_reason,
)
from certiqs_key.solvers.search.corrective import compress, mixture, search_corrective
from certiqs_key.solvers.search.entropy import entropy_initializer, search_entropy
from certiqs_key.solvers.search.factor import FactorLayout, partial_trace, search_factor


def _problem(*, box: bool = False, untrusted: bool = False) -> PreparedProblem:
    declaration = (
        replace(two_factor_general(party_local=False), constraint_list=())
        if untrusted
        else qubit_bb84_general()
    )
    if box:
        declaration = replace(
            declaration,
            acceptance_set=AcceptanceSet(
                geometry="polytope",
                polytope=PolytopeData(
                    columns=2,
                    rows=((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)),
                    rhs=(0.75, 0.75, -0.25, -0.25),
                ),
            ),
        )
    return prepare_problem(
        declaration,
        QicsSectorChoiOracle(),
        options=JointFrankWolfeOptions(oracle="spectral"),
    )


@pytest.mark.parametrize("trusted", [False, True])
def test_complex_normalization_and_pullback(trusted: bool) -> None:
    """Complex directions, mixed output dimensions and multiple Alice groups."""
    rng = np.random.default_rng(932)
    dims = {("a", "q"): 6, ("a", "r"): 4, ("b", "q"): 3}
    factors = {
        pair: rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
        for pair, dim in dims.items()
    }
    layout = FactorLayout(
        dims,
        {"a": 2, "b": 1},
        trusted=trusted,
        anchor={pair: np.eye(dim, dtype=np.complex128) for pair, dim in dims.items()},
        blend=0,
    )
    x = layout.pack(factors)
    point, cache = layout.forward(x)
    assert max(float(np.max(np.abs(block.imag))) for block in point.values()) > 0.01
    if trusted:
        for alice, dim in (("a", 2), ("b", 1)):
            marginal = sum(
                partial_trace(point[pair], dim, dims[pair] // dim)
                for pair in dims
                if pair[0] == alice
            )
            np.testing.assert_allclose(marginal, np.eye(dim), atol=2e-14)
    else:
        assert sum(
            float(np.trace(block).real) for block in point.values()
        ) == pytest.approx(1.0, abs=2e-15)
        # No accidental per-Alice marginal normalization in untrusted mode.
        assert np.trace(point["b", "q"]).real < 0.5
    costs = {
        pair: hermitian_part(
            rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
        )
        for pair, dim in dims.items()
    }
    pullback = layout.pullback(costs, cache)
    for _ in range(5):
        direction = rng.normal(size=x.size)
        direction /= np.linalg.norm(direction)
        plus, _ = layout.forward(x + 1e-5 * direction)
        minus, _ = layout.forward(x - 1e-5 * direction)
        observed = (
            sum(
                float(np.vdot(costs[pair], plus[pair] - minus[pair]).real)
                for pair in dims
            )
            / 2e-5
        )
        assert float(pullback @ direction) == pytest.approx(observed, abs=2e-9)


def test_source_scaling_and_zero_weight_anchor() -> None:
    pair = ("a", "q")
    anchor = {pair: np.eye(4, dtype=np.complex128) / 2}
    layout = FactorLayout({pair: 4}, {"a": 2}, trusted=True, anchor=anchor, blend=1e-10)
    expected, _ = layout.forward(layout.from_point(anchor))
    scaled, _ = layout.forward(layout.from_point(anchor, {"a": 1e-20}))
    np.testing.assert_allclose(expected[pair], scaled[pair], atol=2e-15)
    frozen = FactorLayout(
        {pair: 4},
        {"a": 2},
        trusted=True,
        anchor=anchor,
        blend=1e-10,
        frozen=frozenset({"a"}),
    )
    actual, cache = frozen.forward(np.zeros(32))
    np.testing.assert_array_equal(actual[pair], anchor[pair])
    np.testing.assert_array_equal(frozen.pullback(anchor, cache), np.zeros(32))
    with pytest.raises(ArithmeticError, match="singular"):
        layout.forward(np.zeros(32))


@pytest.mark.parametrize("untrusted", [False, True])
@pytest.mark.parametrize("box", [False, True])
def test_stable_complex_candidate_gradient(untrusted: bool, box: bool) -> None:
    problem = _problem(box=box, untrusted=untrusted)
    point = random_choi_point(problem.maps.parametrization, 987)
    value, gradient, exact = stable.evaluate(problem, point)
    original = joint_objective_value(
        problem.maps,
        {chat: float(q) for chat, q in exact.items()},
        point,
        problem.alpha,
    )
    assert value == pytest.approx(original, abs=2e-13)
    layout = FactorLayout(
        {pair: block.shape[0] for pair, block in point.items()},
        {
            alice: frame.input_dim
            for alice, frame in problem.maps.parametrization.frames.items()
        },
        trusted=not untrusted,
        anchor=problem.anchor,
        blend=1e-8,
    )
    x = layout.from_point(point)
    actual, cache = layout.forward(x)
    _, gradient, _ = stable.evaluate(problem, actual)
    pullback = layout.pullback(gradient, cache)
    direction = np.random.default_rng(844).normal(size=x.size)
    direction /= np.linalg.norm(direction)
    plus = stable.evaluate(problem, layout.forward(x + 1e-5 * direction)[0])[0]
    minus = stable.evaluate(problem, layout.forward(x - 1e-5 * direction)[0])[0]
    assert float(pullback @ direction) == pytest.approx((plus - minus) / 2e-5, abs=2e-8)
    assert sum(exact.values(), Fraction()) == 1


def test_exact_box_recognition_refuses_almost_coordinate_and_missing_rows() -> None:
    box = PolytopeData(
        columns=2,
        rows=((0.0, -1.0), (1.0, 0.0), (-1.0, 0.0), (0.0, 1.0)),
        rhs=(-0.25, 0.75, -0.25, 0.75),
    )
    assert canonical_box(box) is not None
    assert canonical_box(replace(box, rows=box.rows[:-1], rhs=box.rhs[:-1])) is None
    assert canonical_box(replace(box, rows=((1e-100, -1.0), *box.rows[1:]))) is None
    assert (
        canonical_box(
            replace(box, rows=(*box.rows, box.rows[0]), rhs=(*box.rhs, box.rhs[0]))
        )
        is None
    )
    assert canonical_box(replace(box, rhs=(-0.9, 0.75, -0.25, 0.75))) is None


def test_capabilities_include_singleton_rows_nonbox_and_complex_refusal() -> None:
    singleton = _problem()
    assert capability_reason(singleton, "factor") is None
    assert capability_reason(singleton, "entropy") is None
    assert capability_reason(_problem(box=True), "corrective") is None
    declaration = replace(
        singleton.maps.declaration,
        acceptance_set=AcceptanceSet(
            geometry="polytope",
            polytope=PolytopeData(columns=2, rows=((1.0, -1.0),), rhs=(0.5,)),
        ),
    )
    nonbox = prepare_problem(declaration, QicsSectorChoiOracle())
    assert "canonical box" in str(capability_reason(nonbox, "factor"))
    rows = prepare_problem(
        two_factor_general(party_local=False), QicsSectorChoiOracle()
    )
    assert "additional declared rows" in str(capability_reason(rows, "factor"))
    assert capability_reason(rows, "corrective") is None
    branch_key = next(iter(singleton.maps.branches))
    branch = singleton.maps.branches[branch_key]
    klass = branch.classes[0]
    kraus = klass.kraus.copy()
    kraus[0, 0] += 1e-30j
    branches = dict(singleton.maps.branches)
    branches[branch_key] = replace(
        branch, classes=(replace(klass, kraus=kraus), *branch.classes[1:])
    )
    complex_problem = replace(
        singleton, maps=replace(singleton.maps, branches=branches)
    )
    assert "exactly real" in str(capability_reason(complex_problem, "entropy"))


def test_active_memory_fold_preserves_complex_candidate() -> None:
    rng = np.random.default_rng(301)
    atoms = [
        {
            ("a", "q"): np.asarray(
                rng.normal(size=(3, 3)) + 1j * rng.normal(size=(3, 3)),
                dtype=np.complex128,
            )
        }
        for _ in range(20)
    ]
    weights = rng.random(20)
    weights /= sum(weights)
    expected = mixture(atoms, weights)
    folded, new_weights = compress(atoms, weights, 4, 0.03)
    assert len(folded) <= 4
    np.testing.assert_allclose(
        mixture(folded, new_weights)["a", "q"], expected["a", "q"], atol=3e-16
    )


@pytest.mark.parametrize("method", ["factor", "corrective"])
def test_search_retains_candidate_and_obeys_deadline(method: str) -> None:
    problem = _problem(box=True)
    initial = random_choi_point(problem.maps.parametrization, 931)
    if method == "factor":
        outcome = search_factor(
            problem, initial, settings=FactorSettings(max_iterations=8)
        )
        timed = search_factor(problem, deadline=time.perf_counter() - 1)
    else:
        outcome = search_corrective(
            problem, initial, settings=CorrectiveSettings(max_iterations=3, max_atoms=3)
        )
        timed = search_corrective(problem, deadline=time.perf_counter() - 1)
        assert outcome.diagnostics["max_atoms"] <= 3
    assert timed.termination == "budget_exhausted"
    assert outcome.termination != "numerical_failure", outcome.diagnostics
    assert outcome.search_objective is not None
    assert outcome.search_objective <= stable.evaluate(problem, initial)[0] + 1e-8
    checked, _, q = stable.evaluate(problem, outcome.point)
    assert checked == outcome.search_objective
    assert q == outcome.q_exact


@pytest.mark.parametrize("box", [False, True])
def test_entropy_cone_imposes_accepted_statistics_and_polishes(box: bool) -> None:
    problem = _problem(box=box)
    point, report = entropy_initializer(problem, deadline=time.perf_counter() + 30)
    assert report["cone_status"] in ("optimal", "near_optimal")
    assert np.isfinite(report["alpha1_objective"])
    from certiqs_key.meat_core.objective.joint import joint_statistics

    assert all(
        0.25 - 1e-7 <= p <= 0.75 + 1e-7
        for p in joint_statistics(problem.maps, point).values()
    )
    outcome = search_entropy(
        problem,
        settings=EntropySettings(polish=FactorSettings(max_iterations=3)),
        deadline=time.perf_counter() + 30,
    )
    assert outcome.search_objective is not None, outcome.diagnostics
    assert "alpha1_objective" in outcome.diagnostics


def test_entropy_cone_skips_a_class_no_outcome_pair_realises() -> None:
    """A class with no outcome pair adds no cone and changes nothing.

    The BBM92 encoded route at cutoff 1 holds such classes (a Kraus operator
    with no rows): QICS's QuantKeyDist divided its output dimension by its
    projector count, both zero, and the auto portfolio's entropy stage ended
    "division by zero" on every such run. Its term D(G(J)||Z(G(J))) is zero
    for G = 0, so the cone without it is the same program: the same
    objective, the same number of cones and equalities, the same point.
    """
    problem = _problem()
    key = next(iter(problem.maps.branches))
    branches = dict(problem.maps.branches)
    branch = branches[key]
    width = branch.classes[0].kraus.shape[1]
    empty = replace(
        branch.classes[0],
        pairs=(),
        kraus=np.zeros((0, width), dtype=np.complex128),
        labels=np.zeros(0, dtype=np.int64),
    )
    branches[key] = replace(branch, classes=(*branch.classes, empty))
    padded = replace(problem, maps=replace(problem.maps, branches=branches))
    point, report = entropy_initializer(padded, deadline=time.perf_counter() + 30)
    reference, expected = entropy_initializer(
        problem, deadline=time.perf_counter() + 30
    )
    assert report["cone_status"] in ("optimal", "near_optimal")
    for name in ("alpha1_objective", "cones", "equalities", "variables"):
        assert report[name] == expected[name], name
    assert all(np.array_equal(point[pair], reference[pair]) for pair in reference)


def test_entropy_assembly_memory_limit_is_explicit() -> None:
    outcome = search_entropy(_problem(), settings=EntropySettings(max_assembly_bytes=1))
    assert outcome.termination == "numerical_failure"
    assert "memory budget" in outcome.diagnostics["reason"]


@pytest.mark.parametrize("oversize", ["basis", "projections"])
def test_entropy_preflight_precedes_constructors_and_dense_allocations(
    monkeypatch: pytest.MonkeyPatch, oversize: str
) -> None:
    """A 1 MiB cap refuses the large shape before any cone/basis/projector exists."""
    problem = _problem()
    if oversize == "basis":
        # The former eager d=32 basis alone needed 4,325,376 bytes, while the
        # old width and first-row guards both admitted it under a 1 MiB cap.
        monkeypatch.setattr(
            type(problem.maps.parametrization), "block_dim", lambda *_: 32
        )
    else:
        branch_key = next(iter(problem.maps.branches))
        branches = dict(problem.maps.branches)
        branch = branches[branch_key]
        original = branch.classes[0]
        klass = replace(
            original,
            kraus=np.zeros((512, original.kraus.shape[1]), dtype=np.complex128),
            labels=np.arange(512, dtype=np.int64) % 2,
        )
        branches[branch_key] = replace(branch, classes=(klass, *branch.classes[1:]))
        problem = replace(problem, maps=replace(problem.maps, branches=branches))

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("large allocation ran before memory preflight")

    for constructor in ("PosSemidefinite", "QuantKeyDist", "NonNegOrthant"):
        monkeypatch.setattr(entropy_module.qics.cones, constructor, forbidden)
    monkeypatch.setattr(entropy_module, "_real_basis", forbidden)
    monkeypatch.setattr(entropy_module.np, "diag", forbidden)
    with pytest.raises(MemoryError, match=r"allocation plan.*memory budget"):
        entropy_initializer(
            problem, settings=EntropySettings(max_assembly_bytes=1024 * 1024)
        )


def test_entropy_preflight_refuses_exactly_where_the_initializer_does() -> None:
    # The coordinator skips a stage on the preflight's word, so the two must
    # agree at the boundary: admit at the plan's size, refuse one byte below.
    problem = _problem()
    plan = entropy_module.entropy_preflight(problem)
    assert entropy_module.entropy_preflight(
        problem, EntropySettings(max_assembly_bytes=plan)
    ) == plan
    tight = EntropySettings(max_assembly_bytes=plan - 1)
    with pytest.raises(MemoryError, match="allocation plan"):
        entropy_module.entropy_preflight(problem, tight)
    with pytest.raises(MemoryError, match="allocation plan"):
        entropy_initializer(problem, settings=tight)
    _, report = entropy_initializer(
        problem,
        settings=EntropySettings(max_assembly_bytes=plan),
        deadline=time.perf_counter() + 30,
    )
    assert report["planned_allocation_bytes"] == plan


def test_entropy_basis_is_lazy_and_checks_deadline_between_elements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allocations = []
    original = entropy_module.mat_to_vec

    def counted(matrix: np.ndarray) -> np.ndarray:
        allocations.append(matrix.shape)
        return original(matrix)

    monkeypatch.setattr(entropy_module, "mat_to_vec", counted)
    basis = entropy_module._real_basis(32, deadline=time.perf_counter() + 30)
    assert allocations == []
    assert next(basis).shape == (32**2,)
    assert allocations == [(32, 32)]
    monkeypatch.setattr(entropy_module.time, "perf_counter", lambda: math.inf)
    with pytest.raises(entropy_module.SearchStopped, match="budget_exhausted"):
        next(basis)
    assert allocations == [(32, 32)]


def test_near_one_deficit_matches_hand_derived_equal_superposition() -> None:
    """For |+><+| with key pinching, the deficit is 2**(1-alpha)-1."""
    problem = _problem()
    key = next(iter(problem.maps.branches))
    branch = problem.maps.branches[key]
    klass = replace(
        branch.classes[0],
        kraus=np.eye(2, dtype=np.complex128),
        labels=np.array([0, 1], dtype=np.int64),
    )
    maps = replace(problem.maps, branches={key: replace(branch, classes=(klass,))})
    alpha = 1 + 1e-8
    actual = stable.stable_deficit(
        maps, key[0], key[1], np.full((2, 2), 0.5, dtype=np.complex128), alpha
    )
    assert actual == pytest.approx(math.expm1(-(alpha - 1) * math.log(2)), abs=1e-22)


@pytest.mark.parametrize("method", ["factor", "corrective"])
def test_checkpoint_stop_retains_best_evaluated_candidate(method: str) -> None:
    problem = _problem(box=True)
    initial = random_choi_point(problem.maps.parametrization, 71)
    calls = []

    def stop(point: stable.Point, q: dict[str, Fraction]) -> bool:
        calls.append((point, q))
        return True

    if method == "factor":
        outcome = search_factor(
            problem,
            initial,
            settings=FactorSettings(checkpoint_every=1),
            checkpoint=stop,
        )
    else:
        outcome = search_corrective(
            problem,
            initial,
            settings=CorrectiveSettings(checkpoint_every=1),
            checkpoint=stop,
        )
    assert outcome.termination == "target_met"
    assert len(calls) == 1
    assert stable.evaluate(problem, outcome.point)[0] == outcome.search_objective


def test_corrective_extra_rows_use_declared_oracle() -> None:
    problem = prepare_problem(
        two_factor_general(party_local=False), QicsSectorChoiOracle()
    )
    outcome = search_corrective(problem, settings=CorrectiveSettings(max_iterations=1))
    assert outcome.termination != "unsupported"
    assert outcome.termination != "numerical_failure", outcome.diagnostics
    assert outcome.oracle_calls > 0
