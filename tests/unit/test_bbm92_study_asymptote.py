"""The ideal-device asymptote of the BBM92 study (runs.bbm92_study.asymptote).

The closed form is newly derived for the study and drawn as the ``n -> infinity``
reference of the ideal-detector curves; these tests pin it at hand-computed
points and tie its test fraction to the instance's default.
"""

from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

import pytest
import yaml
from runs.bbm92_study.asymptote import (
    TEST_FRACTION,
    binary_entropy,
    ideal_rate,
    ideal_rate_per_coincidence,
)

PROTOCOL = Path(__file__).resolve().parents[2] / "instances/bbm92/protocol.yaml"


def test_binary_entropy_at_its_landmarks() -> None:
    assert binary_entropy(0.0) == 0.0 == binary_entropy(1.0)
    assert binary_entropy(0.5) == pytest.approx(1.0)
    assert binary_entropy(0.01) == pytest.approx(0.080793136, abs=1e-9)


def test_rate_per_coincidence_by_hand() -> None:
    """(1 - 1/8) * 1/2 * (1 - 2.1 h(0.01)) = 0.363266..."""
    expected = 7 / 16 * (1 - 2.1 * 0.080793136)
    assert ideal_rate_per_coincidence(0.01, 1.1) == pytest.approx(expected, abs=1e-8)
    assert ideal_rate_per_coincidence(0.0, 1.1) == pytest.approx(7 / 16)


def test_rate_scales_with_both_arms_transmittance() -> None:
    at_zero = ideal_rate(0.0, 0.01, 1.1)
    assert ideal_rate(10.0, 0.01, 1.1) == pytest.approx(at_zero / 10)
    assert ideal_rate(30.0, 0.01, 1.1) == pytest.approx(at_zero / 1000)


def test_rate_is_floored_at_zero_past_the_threshold() -> None:
    threshold = 0.10228282
    assert ideal_rate_per_coincidence(threshold - 1e-6, 1.1) > 0
    assert ideal_rate_per_coincidence(threshold + 1e-6, 1.1) == 0.0
    assert math.isclose(2.1 * binary_entropy(threshold), 1.0, abs_tol=1e-6)


def test_test_fraction_is_the_instance_default() -> None:
    document = yaml.safe_load(PROTOCOL.read_text(encoding="utf-8"))
    (declared,) = [
        p for p in document["parameters"]["table"] if p.get("name") == "test_fraction"
    ]
    assert Fraction(str(declared["default"])) == TEST_FRACTION
