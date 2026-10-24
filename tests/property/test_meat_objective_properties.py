"""Algebraic and property tests of the objective (spec/architecture.md 14.2).

What is checked here is what the contract PROVES about the objective, on
randomly generated feasible points rather than on the hand-authored ones:

* ``0 <= K_chat <= P_chat`` at every feasible point (Theorem thm:branch-formula, C6);
* ``f_{chat,s} <= 0``, with equality exactly on Z-invariant branch operators
  (Corollary cor:f-nonpos);
* ``K_chat`` concave and the objective jointly convex (C9a, C9b);
* the objective non-negative wherever it is finite (Remark rem:hlow-range);
* the gradient agreeing with a central difference of the objective (C12).

Hypothesis drives the feasible points; every draw is a genuine member of the
feasible set of Eq. eq:feas, built as a mixture over the declared sectors.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

ORACLE_TREE = Path(__file__).resolve().parents[1] / "oracles"
if str(ORACLE_TREE) not in sys.path:
    sys.path.insert(0, str(ORACLE_TREE))

from dummy_bundles import build_bundle  # noqa: E402
from toy_declarations import TOY4B_DIVERGENCE_ONLY, toy  # noqa: E402

from certiqs_key.meat_core.declaration.bundle import (  # noqa: E402
    declaration_from_bundle,
)
from certiqs_key.meat_core.objective.branch import (  # noqa: E402
    evaluate_branches,
    generate_maps,
)
from certiqs_key.meat_core.objective.gradient import state_gradient  # noqa: E402
from certiqs_key.meat_core.objective.objective import (  # noqa: E402
    acceptance_vector,
    check_feasible,
    objective_value,
)

TOYS = ("TOY-1", "TOY-2", "TOY-5", "TOY-6")
MAPS = {
    name: generate_maps(declaration_from_bundle(build_bundle(toy(name))))
    for name in TOYS
}
#: TOY-4b is the one frozen toy with TWO declared acceptance values, so it is
#: the only one on which ``q`` can range over a non-degenerate simplex.
Q_MAPS = {
    "TOY-4b": generate_maps(
        declaration_from_bundle(build_bundle(TOY4B_DIVERGENCE_ONLY))
    ),
}

alphas = st.floats(min_value=1.01, max_value=4.0, allow_nan=False, allow_infinity=False)
shares = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


def point(name: str, raw: list[float]) -> dict[str, np.ndarray]:
    """Return a feasible block-diagonal state from unnormalized sector shares.

    Feasibility includes the DECLARED CONSTRAINT LIST, not only the simplex: on
    the toys that carry one, the entry pins the first sector's weight to at
    least ``1/2``, so the draw is mapped into ``[1/2, 1]`` by
    ``w -> (1 + w_0)/2`` with the remaining mass halved. Every point handed to
    the objective below is therefore a genuine member of Eq. eq:feas, which
    ``check_feasible`` re-asserts.
    """
    sectors = MAPS[name].sectors
    values = list(raw[: len(sectors)]) or [1.0]
    total = sum(values)
    if total <= 0.0:
        values = [1.0] * len(sectors)
        total = float(len(sectors))
    weights = [value / total for value in values]
    if MAPS[name].declaration.constraint_list:
        weights = [0.5 + 0.5 * weights[0], *(0.5 * w for w in weights[1:])]
    return {
        sector: np.array([[weight]], dtype=np.complex128)
        for sector, weight in zip(sectors, weights, strict=True)
    }


@pytest.mark.contract
@settings(max_examples=60, deadline=None)
@given(alpha=alphas, raw=st.lists(shares, min_size=3, max_size=3))
def test_k_lies_between_zero_and_p_at_every_feasible_point(
    alpha: float, raw: list[float]
) -> None:
    """Theorem thm:branch-formula with C6: ``0 <= K <= P``.

    That is what makes h_low >= 0.
    """
    for name in TOYS:
        omega = point(name, raw)
        check_feasible(MAPS[name].declaration, omega, tolerance=1e-9)
        for values in evaluate_branches(MAPS[name], omega, alpha).values():
            assert values.k >= -1e-12
            assert values.k <= values.p + 1e-12


@pytest.mark.contract
@settings(max_examples=60, deadline=None)
@given(alpha=alphas, raw=st.lists(shares, min_size=3, max_size=3))
def test_the_sector_deficits_are_non_positive(alpha: float, raw: list[float]) -> None:
    """Corollary cor:f-nonpos: ``f <= 0``, and ``f = 0`` on key-inert pairs."""
    for name in TOYS:
        maps = MAPS[name]
        omega = point(name, raw)
        for chat, values in evaluate_branches(maps, omega, alpha).items():
            for sector, deficit in values.deficits.items():
                assert deficit <= 1e-12
                if maps.key_inert[(chat, sector)]:
                    assert deficit == pytest.approx(0.0, abs=1e-12)


@pytest.mark.contract
@settings(max_examples=40, deadline=None)
@given(
    alpha=alphas,
    left=st.lists(shares, min_size=3, max_size=3),
    right=st.lists(shares, min_size=3, max_size=3),
    weight=st.floats(min_value=0.05, max_value=0.95),
)
def test_the_objective_is_jointly_convex_and_k_is_concave(
    alpha: float, left: list[float], right: list[float], weight: float
) -> None:
    """Theorem thm:convexity (C9b) resting on Corollary cor:concavity (C9a)."""
    for name in TOYS:
        maps = MAPS[name]
        q = acceptance_vector(maps.declaration)
        first, second = point(name, left), point(name, right)
        middle = {
            sector: weight * first[sector] + (1.0 - weight) * second[sector]
            for sector in first
        }
        mixed = evaluate_branches(maps, middle, alpha)
        ends = (
            evaluate_branches(maps, first, alpha),
            evaluate_branches(maps, second, alpha),
        )
        for chat in mixed:
            chord = weight * ends[0][chat].k + (1.0 - weight) * ends[1][chat].k
            assert mixed[chat].k >= chord - 1e-10  # concave
        value = objective_value(maps, q, middle, alpha)
        upper = weight * objective_value(maps, q, first, alpha) + (
            1.0 - weight
        ) * objective_value(maps, q, second, alpha)
        assert value <= upper + 1e-9  # jointly convex


@pytest.mark.contract
@settings(max_examples=40, deadline=None)
@given(alpha=alphas, raw=st.lists(shares, min_size=3, max_size=3))
def test_the_objective_is_non_negative_wherever_it_is_finite(
    alpha: float, raw: list[float]
) -> None:
    """Remark rem:hlow-range: both parts of the objective are non-negative."""
    for name in TOYS:
        maps = MAPS[name]
        value = objective_value(
            maps, acceptance_vector(maps.declaration), point(name, raw), alpha
        )
        assert value >= -1e-12


@pytest.mark.contract
@settings(max_examples=25, deadline=None)
@given(
    alpha=st.floats(min_value=1.05, max_value=3.0),
    raw=st.lists(st.floats(min_value=0.1, max_value=1.0), min_size=3, max_size=3),
    seed=st.integers(min_value=0, max_value=2**16),
)
def test_the_gradient_agrees_with_a_central_difference(
    alpha: float, raw: list[float], seed: int
) -> None:
    """Corollary cor:full-gradient against the objective it differentiates.

    The gradient formulas are never restated here: the objective is evaluated at
    ``omega +/- eps H`` along a random Hermitian direction and compared with
    ``<grad, H>``. The interior draws keep every block positive definite, which
    is the support-maximality Theorem thm:gradient (ii) requires.
    """
    step = 1e-6
    generator = np.random.default_rng(seed)
    for name in TOYS:
        maps = MAPS[name]
        q = acceptance_vector(maps.declaration)
        omega = point(name, raw)
        gradient = state_gradient(maps, q, omega, alpha)
        for sector in maps.sectors:
            size = omega[sector].shape[0]
            raw_direction = generator.normal(size=(size, size))
            direction = np.asarray(
                0.5 * (raw_direction + raw_direction.T), dtype=np.complex128
            )
            plus = {**omega, sector: omega[sector] + step * direction}
            minus = {**omega, sector: omega[sector] - step * direction}
            difference = (
                objective_value(maps, q, plus, alpha)
                - objective_value(maps, q, minus, alpha)
            ) / (2.0 * step)
            analytic = float(np.real(np.trace(gradient.blocks[sector] @ direction)))
            assert difference == pytest.approx(analytic, rel=1e-4, abs=1e-4)


@pytest.mark.contract
@settings(max_examples=40, deadline=None)
@given(
    q1_left=st.floats(min_value=0.02, max_value=0.98),
    q1_right=st.floats(min_value=0.02, max_value=0.98),
    weight=st.floats(min_value=0.05, max_value=0.95),
    alpha=alphas,
)
def test_the_objective_is_convex_in_q_alone(
    q1_left: float, q1_right: float, weight: float, alpha: float
) -> None:
    """Theorem thm:convexity (C9b), the q-direction of joint convexity.

    ``test_the_objective_is_jointly_convex_and_k_is_concave`` above varies only
    ``omega`` at a fixed (singleton) ``q``. TOY-4b is the one frozen toy with two
    declared acceptance values, so it lets ``q`` range freely over the 2-simplex
    at a FIXED feasible ``omega`` (the toy's single sector is one-dimensional, so
    ``omega`` carries no freedom of its own here), covering the
    ``q``-direction of the claim.

    Both TOY-4b acceptance values are non-key-live (``chat_key`` is empty), so
    this exercises the ``(alpha/(alpha-1)) d(q, P)`` branch of Eq. eq:objective;
    the companion K-branch under a JOINTLY varying ``(q, omega)`` on a key-live
    pair is a separate matter. The driver's ``q`` block takes a genuine
    Frank-Wolfe step, and what is narrowed -- the acceptance-set REPRESENTATIONS a
    declaration may use, against def:admissible-acceptance-set's "any closed convex
    subset" -- is disclosed in the source and in every certificate as
    ``certiqs_key.solvers.frank_wolfe.driver.ACCEPTANCE_GEOMETRY_NARROWING``.
    """
    maps = Q_MAPS["TOY-4b"]
    omega = {"s0": np.array([[1.0]], dtype=np.complex128)}

    def q_of(q1: float) -> dict[str, float]:
        return {"chat0": 1.0 - q1, "chat1": q1}

    mid = weight * q1_left + (1.0 - weight) * q1_right
    value = objective_value(maps, q_of(mid), omega, alpha)
    upper = weight * objective_value(maps, q_of(q1_left), omega, alpha) + (
        1.0 - weight
    ) * objective_value(maps, q_of(q1_right), omega, alpha)
    assert value <= upper + 1e-9
