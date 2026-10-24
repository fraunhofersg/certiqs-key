"""The ``alpha -> 1+`` consistency target and its two extra hypotheses (C16).

contract.tex Theorem ``thm:oracle`` states the limit
``h_low(alpha) -> h_1``, the blockwise relative-entropy program of
Eq. ``eq:oracle``. It carries TWO hypotheses that Remark ``rem:oracle`` does not
repeat, and both are load-bearing:

  (H1) there is ``p_0 > 0`` with ``q(chat) >= p_0`` for every ``q`` in the
       acceptance set and every ``chat`` in ``Chat_key``;
  (H2) the asymptotic feasible set ``Feas_1 = {omega in Feas : Phi[omega] in
       AcceptSet}`` is nonempty.

They are recorded in ``registry.C16_EXTRA_HYPOTHESES``, discharged per toy by
the witnesses in ``registry.O_ALPHA_LIMIT_TABLE``, and their necessity is shown
by ``O-ALPHA-LIMIT-HYPOTHESIS-FAILS``, where (H2) fails and no finite limit
exists.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pytest
from reference import branch_operator, relative_entropy_to_pinching
from registry import (
    C16_EXTRA_HYPOTHESES,
    O_ALPHA_LIMIT_TABLE,
    oracle,
)
from toy_declarations import (
    TOY1_RETENTION,
    TOY4B_DIVERGENCE_ONLY,
    TOY5_CONSTRAINED,
    fully_dephased,
)
from toy_declarations import (
    toy as toy_by_id,
)
from toy_evaluation import (
    acceptance_point,
    minimum_over_sector_weights,
    objective_at,
    statistics,
)


def _w0_at_least_half(point: Mapping[str, float]) -> bool:
    return point["s0"] >= 0.5 - 1e-12


def _feasible_for(toy_id: str):  # noqa: ANN202  (a predicate or None)
    return _w0_at_least_half if toy_id in {"TOY-5", "TOY-6"} else None


def _h1_objective(toy_id: str, weights: Mapping[str, float]) -> float:
    """Evaluate the right-hand side of Eq. eq:oracle at one feasible point."""
    toy = toy_by_id(toy_id)
    total = 0.0
    for chat in toy.chat_key:
        for branch in toy.branches.get(chat, ()):
            operator = branch_operator(
                branch.kraus, np.array([[weights[branch.sector]]])
            )
            total += relative_entropy_to_pinching(operator, branch.row_key_values)
    return total


@pytest.mark.contract
def test_the_two_extra_hypotheses_are_recorded_verbatim() -> None:
    """Both hypotheses of Theorem thm:oracle are carried with the oracle entry."""
    entry = oracle("O-ALPHA-LIMIT")
    assert entry.claims == ("C16",)
    assert entry.hypotheses == C16_EXTRA_HYPOTHESES
    assert len(C16_EXTRA_HYPOTHESES) == 2
    assert "p_0 > 0" in C16_EXTRA_HYPOTHESES[0]
    assert "Feas_1" in C16_EXTRA_HYPOTHESES[1]
    assert "NONEMPTY" in C16_EXTRA_HYPOTHESES[1]


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    ("toy_id", "h1", "limit", "p0", "witness"), O_ALPHA_LIMIT_TABLE
)
def test_hypotheses_hold_on_every_c16_entry(
    toy_id: str, h1: float, limit: float, p0: float, witness: str
) -> None:
    """(H1) and (H2) are discharged explicitly, with their witnesses."""
    del h1, limit
    toy = toy_by_id(toy_id)

    # (H1): the acceptance set is a singleton here, so p_0 is the smallest mass
    # it puts on a key-live acceptance value.
    q = acceptance_point(toy)
    assert p0 > 0.0
    for chat in toy.chat_key:
        assert q[chat] >= p0

    # (H2): the recorded witness state is feasible AND its statistics are accepted.
    assert witness
    weights = _witness_weights(toy_id)
    predicate = _feasible_for(toy_id)
    assert predicate is None or predicate(weights)
    phi = statistics(toy, weights)
    for chat, mass in q.items():
        assert phi[chat] == pytest.approx(mass)


def _witness_weights(toy_id: str) -> dict[str, float]:
    """Return the Feas_1 witness of O_ALPHA_LIMIT_TABLE, as sector weights."""
    return {
        "TOY-1": {"s0": 0.0, "s1": 1.0},
        "TOY-3(m=2)": {"s0": 1.0},
        "TOY-3(m=3)": {"s0": 1.0},
        "TOY-5": {"s0": 0.5, "s1": 0.5},
    }[toy_id]


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    ("toy_id", "h1", "limit", "p0", "witness"), O_ALPHA_LIMIT_TABLE
)
def test_h1_program_value_matches_the_recorded_limit(
    toy_id: str, h1: float, limit: float, p0: float, witness: str
) -> None:
    """Eq. eq:oracle evaluated directly agrees with the recorded h_1 and limit."""
    del p0, witness
    toy = toy_by_id(toy_id)
    predicate = _feasible_for(toy_id)

    if len(toy.sector_index_set) == 1:
        best = _h1_objective(toy_id, {toy.sector_index_set[0]: 1.0})
    else:
        candidates = [
            _h1_objective(toy_id, point)
            for point in _sector_grid(toy.sector_index_set, 400)
            if predicate is None or predicate(point)
        ]
        best = min(candidates)

    assert best == pytest.approx(h1, abs=1e-9)
    assert h1 == pytest.approx(limit)


def _sector_grid(sectors: tuple[str, ...], steps: int) -> list[dict[str, float]]:
    assert len(sectors) == 2  # the C16 table only carries one- and two-sector toys
    return [
        {sectors[0]: i / steps, sectors[1]: 1.0 - i / steps} for i in range(steps + 1)
    ]


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    ("toy_id", "h1", "limit", "p0", "witness"), O_ALPHA_LIMIT_TABLE
)
def test_h_low_converges_to_the_recorded_limit(
    toy_id: str, h1: float, limit: float, p0: float, witness: str
) -> None:
    """h_low(alpha) -> h_1 as alpha -> 1+, on a decreasing sequence of alphas."""
    del h1, p0, witness
    toy = toy_by_id(toy_id)
    predicate = _feasible_for(toy_id)

    previous_gap = math.inf
    for alpha in (1.1, 1.01, 1.001, 1.0001):
        if len(toy.sector_index_set) == 1:
            value = objective_at(toy, alpha, {toy.sector_index_set[0]: 1.0})
        else:
            value, _ = minimum_over_sector_weights(
                toy, alpha, steps=400, feasible=predicate
            )
        gap = abs(value - limit)
        assert gap <= previous_gap + 1e-9  # monotone approach, no drift
        previous_gap = gap
    assert previous_gap < 1e-4


@pytest.mark.contract
@pytest.mark.oracle
def test_key_inert_sectors_contribute_nothing_to_the_limit() -> None:
    """Eq. eq:oracle sums over key-ACTIVE sectors only; the rest are zero anyway."""
    for weights in ({"s0": 0.0, "s1": 1.0}, {"s0": 0.4, "s1": 0.6}):
        contributions = {}
        for branch in TOY1_RETENTION.branches["chat0"]:
            operator = branch_operator(
                branch.kraus, np.array([[weights[branch.sector]]])
            )
            contributions[branch.sector] = relative_entropy_to_pinching(
                operator, branch.row_key_values
            )
        assert contributions["s1"] == pytest.approx(0.0, abs=1e-12)
        # The hand-derived value for the key-active sector: D(G || Z(G)) = w0.
        assert contributions["s0"] == pytest.approx(weights["s0"], abs=1e-9)


@pytest.mark.contract
@pytest.mark.oracle
def test_fully_dephased_limit_is_log2_m() -> None:
    """Eq. eq:oracle on TOY-3(m): D(|eta><eta| || Z(|eta><eta|)) = log2 m."""
    for m in (2, 3, 4, 5):
        toy = fully_dephased(m)
        branch = toy.branches["chat0"][0]
        operator = branch_operator(branch.kraus, np.array([[1.0]]))
        assert relative_entropy_to_pinching(
            operator, branch.row_key_values
        ) == pytest.approx(math.log2(m), abs=1e-9)


@pytest.mark.contract
@pytest.mark.oracle
def test_constrained_limit_is_the_constraint_boundary() -> None:
    """TOY-5: h_1 = inf over Feas_1 of w0 = 1/2, the declared constraint bound."""
    assert TOY5_CONSTRAINED.constraint_list[0].homogeneous_scalar == 0.5
    values = [
        _h1_objective("TOY-5", {"s0": w, "s1": 1.0 - w}) for w in (0.5, 0.6, 0.75, 1.0)
    ]
    assert values[0] == pytest.approx(0.5, abs=1e-9)
    assert values == sorted(values)  # the C16 objective is w0, increasing


@pytest.mark.contract
@pytest.mark.oracle
def test_hypothesis_h2_is_load_bearing() -> None:
    """O-ALPHA-LIMIT-HYPOTHESIS-FAILS: Feas_1 empty => h_low diverges, no limit."""
    entry = oracle("O-ALPHA-LIMIT-HYPOTHESIS-FAILS")
    assert entry.toy_id == "TOY-4b"

    # (H2) fails: the only reachable statistics vector is not in the acceptance set.
    phi = statistics(TOY4B_DIVERGENCE_ONLY, {"s0": 1.0})
    q = acceptance_point(TOY4B_DIVERGENCE_ONLY)
    assert phi != pytest.approx(q)

    # And h_low really does diverge, so extrapolating a limit would be wrong.
    previous = 0.0
    for alpha in (1.1, 1.01, 1.001, 1.0001):
        value = objective_at(TOY4B_DIVERGENCE_ONLY, alpha, {"s0": 1.0})
        assert value > previous
        previous = value
    assert previous > 1e3
