"""Public information and coherent-click limits from independent formulas.

The public part is the decoy template's lowered one, at a source of two
non-default intensities.
"""

from decimal import Decimal, localcontext
from fractions import Fraction as F

import pytest
from instances.common.honest.coherent_pulses import click_distribution
from instances.common.optics import ReceiverParameters
from instances.decoy_bb84.surface import default_config
from tests.oracles.registry_instances_decoy_bb84 import DECOY_TOY
from tests.support.lowered_templates import choice_options, lowered


@pytest.mark.parametrize("mode", choice_options("decoy_bb84", "acceptance_map"))
def test_generation_announces_no_bit_and_only_sifted_clicks_generate(mode: str):
    config = default_config(
        device={
            "mu_signal": 0.5,
            "mu_weak": 0.1,
            "gamma": 0.25,
            "acceptance_map": mode,
        }
    )
    public = lowered("decoy_bb84", config)[1].public
    assert public is not None
    assert public.transcript is not None
    first, second = public.transcript.messages
    assert first.table["gen-signal-H", ()] == first.table["gen-signal-V", ()] == "gen-Z"
    assert second.table["H", ("gen-Z",)] == second.table["V", ("gen-Z",)] == "Z"
    assert second.table["H", ("test-weak-H",)] == "H"
    assert second.table["V", ("test-weak-H",)] == "V"
    passing = [k for k, v in public.sifting.items() if str(v) == "pass"]
    assert passing == [("gen-Z", "Z")]


def test_vacuum_is_polarisation_independent_and_has_exact_dark_pattern_law():
    d = F(1, 64)
    parameters = ReceiverParameters(dark_count=(d,) * 4)
    distributions = [
        click_distribution(
            parameters,
            intensity=F(0),
            polarisation=p,
            transmittance=F(1),
            misalignment=F(0),
        )
        for p in ("H", "V", "plus", "minus")
    ]
    assert all(value == distributions[0] for value in distributions)
    distribution = distributions[0]
    assert distribution["nc"] == (1 - d) ** 4
    assert distribution["H"] == d * (1 - d) ** 3
    assert sum(distribution.values()) == 1


def test_frozen_toy_total_click_target_in_single_port_limit():
    # The registry explicitly distinguishes its threshold-pair toy from the
    # real passive receiver. Closing the X arm and using only H's detector
    # reproduces this component formula, without relabelling the toy as ours.
    toy = DECOY_TOY
    parameters = ReceiverParameters(
        basis_split=F(1),
        efficiency=(toy.efficiency,) * 4,
        dark_count=(toy.dark_count, F(0), F(0), F(0)),
    )
    clicks = click_distribution(
        parameters,
        intensity=toy.intensity,
        polarisation="H",
        transmittance=F(1),
        misalignment=F(0),
    )
    assert float((1 - toy.test_coin) * (1 - clicks["nc"])) == pytest.approx(
        toy.sifted_generation_total, abs=1e-15
    )


def test_coherent_single_clicks_follow_independent_port_law():
    parameters = ReceiverParameters()
    clicks = click_distribution(
        parameters,
        intensity=F(1, 2),
        polarisation="H",
        transmittance=F(1),
        misalignment=F(0),
    )
    with localcontext() as ctx:
        ctx.prec = 60
        # Ideal H input reaches H with fraction 1/2, D/A with 1/4 each.
        expected_h = (1 - (-Decimal(1) / 4).exp()) * (-Decimal(1) / 4).exp()
    assert float(clicks["H"]) == pytest.approx(float(expected_h), abs=2e-16)
    assert clicks["V"] == 0
    assert sum(clicks.values()) == 1
