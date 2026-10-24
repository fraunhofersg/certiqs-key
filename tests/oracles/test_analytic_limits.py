"""Closed-form ``h_low`` values on the toy declarations (C5, C8, C9b, C10).

spec/architecture.md Section 14.3: "Perfectly correlated, deterministic, fully
dephased, and zero-generation toy cases." Each test pins one registry entry.

Two things every test here does. It asserts the hand-derived closed form against
the reference evaluation at the claimed minimizer, and -- where the feasible set
is more than a point -- it confirms on a grid that the claimed minimizer really
is one. The grid is a check on the derivation, never the source of a value.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import pytest
from reference import divergence_kernel
from registry import (
    ALPHA_GRID,
    O_HLOW_DEPHASED_TABLE,
    O_HLOW_NO_AVERAGING_AVERAGED,
    O_HLOW_RETENTION_DROPPED,
    oracle,
)
from toy_declarations import (
    TOY1_RETENTION,
    TOY2_AVERAGED,
    TOY2_DETERMINISTIC,
    TOY4A_ZERO_GENERATION,
    TOY4B_DIVERGENCE_ONLY,
    TOY5_CONSTRAINED,
    TOY6_REMOVABLE,
    fully_dephased,
)
from toy_evaluation import minimum_over_sector_weights, objective_at

ALPHAS = ALPHA_GRID


def _w0_at_least_half(point: Mapping[str, float]) -> bool:
    """Return whether TOY-5 / TOY-6's declared constraint ``w0 >= 1/2`` holds."""
    return point["s0"] >= 0.5 - 1e-12


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
@pytest.mark.parametrize(("m", "expected"), O_HLOW_DEPHASED_TABLE)
def test_fully_dephased_gives_log2_m(alpha: float, m: int, expected: float) -> None:
    """O-HLOW-FULLY-DEPHASED: h_low = log2(m), independent of alpha."""
    entry = oracle("O-HLOW-FULLY-DEPHASED")
    assert entry.claims == ("C5", "C8")
    toy = fully_dephased(m)
    # The feasible set is the single point omega = [1].
    assert objective_at(toy, alpha, {"s0": 1.0}) == pytest.approx(expected, abs=1e-9)
    assert expected == pytest.approx(math.log2(m))


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_deterministic_key_gives_zero(alpha: float) -> None:
    """O-HLOW-DETERMINISTIC: every pair key-inert, so K = P and h_low = 0."""
    assert oracle("O-HLOW-DETERMINISTIC").value == 0.0
    value, at_point = minimum_over_sector_weights(TOY2_DETERMINISTIC, alpha, steps=50)
    assert value == pytest.approx(0.0, abs=1e-12)
    # Zero at EVERY feasible point, not only at the minimizer.
    for w0 in (0.0, 0.25, 0.5, 0.75, 1.0):
        assert objective_at(
            TOY2_DETERMINISTIC, alpha, {"s0": w0, "s1": 1.0 - w0}
        ) == pytest.approx(0.0, abs=1e-12)
    assert set(at_point) == set(TOY2_DETERMINISTIC.sector_index_set)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_zero_generation_with_compatible_acceptance_gives_zero(alpha: float) -> None:
    """O-HLOW-ZERO-GENERATION: no key rounds and no penalty, so h_low = 0."""
    assert oracle("O-HLOW-ZERO-GENERATION").value == 0.0
    assert TOY4A_ZERO_GENERATION.chat_key == ()
    assert objective_at(TOY4A_ZERO_GENERATION, alpha, {"s0": 1.0}) == pytest.approx(
        0.0, abs=1e-12
    )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_retention_dropping_a_constraint_active_sector_costs_one_bit(
    alpha: float,
) -> None:
    """O-HLOW-RETENTION: 0 with the sector retained, exactly 1 bit without it."""
    entry = oracle("O-HLOW-RETENTION")
    assert entry.value == 0.0

    value, at_point = minimum_over_sector_weights(TOY1_RETENTION, alpha, steps=400)
    assert value == pytest.approx(0.0, abs=1e-12)
    assert at_point["s0"] == pytest.approx(0.0, abs=1e-9)  # the claimed argmin

    dropped = objective_at(TOY1_RETENTION, alpha, {"s0": 1.0, "s1": 0.0})
    assert dropped == pytest.approx(O_HLOW_RETENTION_DROPPED)
    assert dropped == pytest.approx(1.0)
    assert dropped > value  # strict, and in the DANGEROUS direction


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_averaging_sectors_costs_one_bit(alpha: float) -> None:
    """O-HLOW-NO-AVERAGING: the averaged declaration reports one bit more."""
    assert oracle("O-HLOW-NO-AVERAGING").value == 0.0

    original, _ = minimum_over_sector_weights(TOY2_DETERMINISTIC, alpha, steps=50)
    averaged = objective_at(TOY2_AVERAGED, alpha, {"sbar": 1.0})

    assert original == pytest.approx(0.0, abs=1e-12)
    assert averaged == pytest.approx(O_HLOW_NO_AVERAGING_AVERAGED)
    assert averaged - original == pytest.approx(1.0)

    # Both declarations really do produce the same statistics on the states the
    # contract's proof compares -- TOY-2 at uniform weights, TOY-2-AVG on its
    # only feasible state -- which is what makes the gap an obstruction.
    from toy_evaluation import statistics

    assert statistics(TOY2_DETERMINISTIC, {"s0": 0.5, "s1": 0.5}) == pytest.approx(
        statistics(TOY2_AVERAGED, {"sbar": 1.0})
    )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    ("alpha", "expected"), oracle("O-HLOW-CONSTRAINED").frozen_values
)
def test_constrained_closed_form(alpha: float, expected: float) -> None:
    """O-HLOW-CONSTRAINED: the alpha-dependent closed form, and its argmin."""
    entry = oracle("O-HLOW-CONSTRAINED")
    assert entry.closed_form is not None
    assert entry.closed_form(alpha) == pytest.approx(expected, rel=1e-12)

    value, at_point = minimum_over_sector_weights(
        TOY5_CONSTRAINED, alpha, steps=400, feasible=_w0_at_least_half
    )
    assert value == pytest.approx(expected, abs=1e-9)
    assert at_point["s0"] == pytest.approx(0.5, abs=1e-9)  # boundary of L

    # h_low(L) >= h_low({}) = 0 (Definition def:hqkd-list).
    unconstrained, _ = minimum_over_sector_weights(TOY1_RETENTION, alpha, steps=400)
    assert value > unconstrained
    assert unconstrained == pytest.approx(0.0, abs=1e-12)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(("alpha", "expected"), oracle("O-HLOW-REMOVAL").frozen_values)
def test_removing_a_removable_sector_changes_nothing(
    alpha: float, expected: float
) -> None:
    """O-HLOW-REMOVAL: deleting the (RM1)-(RM3) sector leaves h_low untouched."""
    assert oracle("O-HLOW-REMOVAL").claims == ("C10",)
    assert TOY6_REMOVABLE.removable["s2"] is True

    with_s2, at_point = minimum_over_sector_weights(
        TOY6_REMOVABLE, alpha, steps=120, feasible=_w0_at_least_half
    )
    without_s2, _ = minimum_over_sector_weights(
        TOY5_CONSTRAINED, alpha, steps=400, feasible=_w0_at_least_half
    )

    assert with_s2 == pytest.approx(expected, abs=1e-9)
    assert without_s2 == pytest.approx(expected, abs=1e-9)
    assert with_s2 == pytest.approx(without_s2, abs=1e-9)
    assert at_point["s0"] == pytest.approx(0.5, abs=1e-8)
    # The shared value is not zero -- an equality at zero would prove nothing.
    assert expected > 0.4


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    ("alpha", "expected"), oracle("O-HLOW-DIVERGENCE-ONLY").frozen_values
)
def test_divergence_only_closed_form(alpha: float, expected: float) -> None:
    """O-HLOW-DIVERGENCE-ONLY: the pure KL penalty, and it really is KL."""
    entry = oracle("O-HLOW-DIVERGENCE-ONLY")
    assert entry.closed_form is not None
    assert entry.closed_form(alpha) == pytest.approx(expected, rel=1e-12)
    assert objective_at(TOY4B_DIVERGENCE_ONLY, alpha, {"s0": 1.0}) == pytest.approx(
        expected
    )

    # The divergence is the base-2 KL divergence sfD of Definition foundations/def:kl,
    # and not a Renyi divergence. Recomputed here from
    # the kernel, independently of the closed form.
    kl = divergence_kernel(0.5, 0.25) + divergence_kernel(0.5, 0.75)
    assert kl == pytest.approx(1.0 - 0.5 * math.log2(3.0))
    assert expected == pytest.approx((alpha / (alpha - 1.0)) * kl)


@pytest.mark.contract
@pytest.mark.oracle
def test_h_low_is_non_negative_everywhere_in_the_registry() -> None:
    """Remark rem:hlow-range: h_low >= 0, from K <= P and the non-negative KL term."""
    toys = (
        TOY1_RETENTION,
        TOY2_DETERMINISTIC,
        TOY5_CONSTRAINED,
        fully_dephased(3),
        TOY4A_ZERO_GENERATION,
        TOY4B_DIVERGENCE_ONLY,
    )
    for alpha in ALPHAS:
        for toy in toys:
            for point in _points(toy):
                assert objective_at(toy, alpha, point) >= -1e-12


def _points(toy: object) -> list[dict[str, float]]:
    sectors = toy.sector_index_set  # type: ignore[attr-defined]
    if len(sectors) == 1:
        return [{sectors[0]: 1.0}]
    return [
        dict(zip(sectors, (w, 1.0 - w), strict=True))
        for w in (0.0, 0.25, 0.5, 0.75, 1.0)
    ]


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_entropy_part_respects_the_contract_ceiling(alpha: float) -> None:
    """Remark rem:hlow-range: the entropy part is at most log2 of the key support."""
    for m in (2, 3, 4, 5):
        toy = fully_dephased(m)
        value = objective_at(toy, alpha, {"s0": 1.0})
        assert value <= math.log2(toy.key_value_count + 1) + 1e-9
        assert value == pytest.approx(math.log2(m), abs=1e-9)
