"""Analytic passive-click limits for the literature comparison, not figure oracles.

Newly derived for the literature comparison of the decoy sweep. These
test the honest public surface and reconciliation bookkeeping only: they
assert no optimized key-rate ordering against a different protocol.
"""

import math
from fractions import Fraction as F

import pytest
from instances.decoy_bb84 import default_config, preparation

from certiqs_key.runs.pipeline import Preparation


def _h2(p: float) -> float:
    return 0.0 if p in (0.0, 1.0) else -p * math.log2(p) - (1 - p) * math.log2(1 - p)


@pytest.mark.parametrize("transmission", [F(1, 10), F(1, 100)])
@pytest.mark.parametrize("z_split", [F(4, 5), F(1, 5)])
def test_both_printed_split_conventions_obey_passive_single_click_law(
    transmission: F, z_split: F
) -> None:
    e = math.sin(0.03) ** 2
    outcome = preparation(
        default_config(
            model={"transmittance": transmission, "misalignment": e},
            device={
                "gamma": F(1, 5),
                "mu_signal": F(4, 5),
                "mu_weak": F(1, 5),
                "mu_vacuum": F(1, 100),
                "test_signal": F(1, 3),
                "test_weak": F(1, 3),
                "test_vacuum": F(1, 3),
                "basis_split": z_split,
                "source_cutoff": 1,
            },
        )
    )
    assert isinstance(outcome, Preparation), outcome
    raw = outcome.raw_joint_distribution
    assert raw is not None
    _, h, v, _, _, _ = outcome.declaration.bob_alphabet
    generation_mass = sum(p for (x, _), p in raw.items() if x.startswith("gen-"))
    table = {
        (0, 0): raw["gen-signal-H", h] / generation_mass,
        (0, 1): raw["gen-signal-H", v] / generation_mass,
        (1, 0): raw["gen-signal-V", h] / generation_mass,
        (1, 1): raw["gen-signal-V", v] / generation_mass,
    }
    lam = 0.8 * float(transmission)
    r = float(z_split)
    correct = math.exp(-lam) * math.expm1(lam * r * (1 - e))
    wrong = math.exp(-lam) * math.expm1(lam * r * e)
    for bits, p in table.items():
        assert float(p) == pytest.approx(
            (correct if bits[0] == bits[1] else wrong) / 2,
            rel=2e-12,
            abs=2e-15,
        )
    sifted = float(sum(table.values()))
    joint = {bits: float(p) / sifted for bits, p in table.items()}
    conditional_entropy = -sum(
        p * math.log2(p / sum(joint[a, b] for a in (0, 1)))
        for (_, b), p in joint.items()
        if p
    )
    assert conditional_entropy == pytest.approx(
        _h2(wrong / (correct + wrong)), abs=2e-13
    )


def test_vacuum_generation_clicks_need_one_bit_of_reconciliation() -> None:
    outcome = preparation(
        default_config(
            device={
                "mu_signal": 0,
                "mu_weak": 0,
                "mu_vacuum": 0,
                "dark_count": dict.fromkeys(("H", "V", "D", "A"), F(1, 64)),
            }
        )
    )
    assert isinstance(outcome, Preparation), outcome
    raw = outcome.raw_joint_distribution
    assert raw is not None
    _, h, v, _, _, _ = outcome.declaration.bob_alphabet
    for bob in (h, v):
        assert raw["gen-signal-H", bob] == raw["gen-signal-V", bob] > 0
    # Each Bob-conditioned Alice bit is exactly uniform: H(A|B,G)=1.
    # Factor 1.1 therefore exceeds the one-bit-per-sifted-round entropy
    # target. This is an EC-model sanity check, not a solver-rate assertion.
    p_sift = sum(raw[x, b] for x in ("gen-signal-H", "gen-signal-V") for b in (h, v))
    assert F(11, 10) * p_sift > p_sift
