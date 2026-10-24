"""The lambda_EC estimate (certiqs_key.runs.error_correction) on the bbm92 instance.

The estimate is generic over the declaration; bbm92 pins it against the
closed form it must reduce to there. With a Werner state of visibility v the
error on every passing round is (1 - v)/2 in each key basis, independent of the
announcement class, so H(R | O_B, K) = p_pass * h2((1 - v)/2).
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest
from instances import surface_of

from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.error_correction import (
    DEFAULT_F_EC,
    LambdaEcEstimateError,
    estimate_lambda_ec,
    with_estimated_lambda_ec,
)
from certiqs_key.runs.pipeline import Preparation


def _h2(q: float) -> float:
    return 0.0 if q in (0.0, 1.0) else -q * math.log2(q) - (1 - q) * math.log2(1 - q)


def _prepared(visibility: Fraction) -> tuple[RunConfig, Preparation]:
    surface = surface_of("bbm92")
    base = surface.default_config()
    model = dict(base.model)
    model["visibility"] = visibility
    model["alice_transmittance"] = Fraction(1, 2)
    model["bob_transmittance"] = Fraction(1, 2)
    config = base.with_(model=model)
    preparation = surface.preparation(config)
    assert isinstance(preparation, Preparation)
    return config, preparation


def test_a_perfect_source_leaks_nothing() -> None:
    config, preparation = _prepared(Fraction(1))
    updated, estimate = with_estimated_lambda_ec(config, preparation)
    assert estimate.lambda_ec == 0
    assert updated.parameters.lambda_ec == 0


def test_the_estimate_reduces_to_the_symmetric_closed_form() -> None:
    config, preparation = _prepared(Fraction(9, 10))
    updated, estimate = with_estimated_lambda_ec(config, preparation)
    # gen fraction 7/8, coincidence (1/2)^2, matched basis 1/2.
    assert estimate.p_pass == pytest.approx(7 / 64, abs=1e-15)
    closed = DEFAULT_F_EC * config.rounds * estimate.p_pass * _h2(0.05)
    assert estimate.lambda_ec == math.ceil(closed)
    assert updated.parameters.lambda_ec == estimate.lambda_ec
    assert updated.parameters.alpha == config.parameters.alpha
    assert estimate.as_payload()["f_ec_source"].startswith("kamin2025renyi")


def test_inputs_that_are_not_ones_are_refused() -> None:
    config, preparation = _prepared(Fraction(9, 10))
    raw = preparation.raw_joint_distribution
    assert raw is not None
    with pytest.raises(LambdaEcEstimateError):
        estimate_lambda_ec(preparation.declaration, raw, rounds=config.rounds, f_ec=0.9)
    with pytest.raises(LambdaEcEstimateError):
        halved = {pair: p / 2 for pair, p in raw.items()}
        estimate_lambda_ec(preparation.declaration, halved, rounds=config.rounds)
    with pytest.raises(LambdaEcEstimateError):
        estimate_lambda_ec(preparation.declaration, raw, rounds=0)
