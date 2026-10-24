"""Fixed-length key assembly and its monotonicity (C14, C15).

spec/architecture.md 9 runs these from the first milestone, on the
``estimate`` path: "increasing leakage or decreasing security errors cannot
increase key length" and "final integer key length is rounded downward".

The ``h_low`` inputs are taken from the TOY-3 oracles rather than invented, so
the chain from the contracted objective to the reported integer is closed inside
the registry.
"""

from __future__ import annotations

import math

import pytest
from reference import key_length
from registry import KEY_LENGTH_CASES, oracle
from toy_declarations import fully_dephased
from toy_evaluation import objective_at

ALPHAS_IN_DOMAIN = (1.05, 1.25, 1.5, 1.75, 1.9)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", KEY_LENGTH_CASES, ids=lambda c: c.case_id)
def test_frozen_key_length_cases(case) -> None:  # noqa: ANN001  (a registry record)
    """O-KEY-LENGTH: the four frozen evaluations of Eq. eq:keylength."""
    assert oracle("O-KEY-LENGTH").claims == ("C14",)
    assert case.arithmetic  # every case carries its arithmetic
    assert (
        key_length(
            rounds=case.rounds,
            h_low=case.h_low,
            lambda_ec=case.lambda_ec,
            eps_ev=case.eps_ev,
            eps_pa=case.eps_pa,
            alpha=case.alpha,
            ideal_hash=case.ideal_hash,
        )
        == case.expected
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_key_length_inputs_are_chained_to_the_objective_oracles() -> None:
    """The h_low values fed to KL-1/KL-2 are the TOY-3 oracle values, not guesses."""
    assert objective_at(fully_dephased(2), 1.5, {"s0": 1.0}) == pytest.approx(
        1.0, abs=1e-9
    )
    assert objective_at(fully_dephased(3), 1.5, {"s0": 1.0}) == pytest.approx(
        math.log2(3.0), abs=1e-9
    )
    by_id = {case.case_id: case for case in KEY_LENGTH_CASES}
    assert by_id["KL-1"].h_low == 1.0
    assert by_id["KL-2-floor"].h_low == pytest.approx(math.log2(3.0))


@pytest.mark.contract
@pytest.mark.oracle
def test_integer_key_length_is_rounded_downward() -> None:
    """KL-2: floor(16.8496...) = 16, never 17 (spec/architecture.md 14.4)."""
    unclamped = 10 * math.log2(3.0) + 1.0
    assert unclamped == pytest.approx(16.84962500721156)
    assert (
        key_length(
            rounds=10,
            h_low=math.log2(3.0),
            lambda_ec=0,
            eps_ev=1.0,
            eps_pa=1.0,
            alpha=1.5,
        )
        == 16
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_key_length_is_clamped_at_zero() -> None:
    """KL-3: a negative bracket reports 0 bits, not a negative key length."""
    assert (
        key_length(
            rounds=1,
            h_low=1.0,
            lambda_ec=10,
            eps_ev=2.0**-30,
            eps_pa=2.0**-30,
            alpha=1.5,
        )
        == 0
    )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS_IN_DOMAIN)
def test_key_length_is_non_increasing_in_leakage(alpha: float) -> None:
    """O-KEY-LENGTH-MONOTONE / Proposition prop:monotone (i)."""
    assert oracle("O-KEY-LENGTH-MONOTONE").claims == ("C15",)
    previous = math.inf
    for lambda_ec in (0, 1, 10, 1_000, 100_000, 500_000, 5_000_000):
        value = key_length(
            rounds=1_000_000,
            h_low=1.0,
            lambda_ec=lambda_ec,
            eps_ev=2.0**-30,
            eps_pa=2.0**-30,
            alpha=alpha,
        )
        assert value <= previous
        previous = value
    assert previous == 0


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS_IN_DOMAIN)
def test_key_length_is_non_decreasing_in_each_error_budget(alpha: float) -> None:
    """Proposition prop:monotone (ii) and (iii): a LOOSER budget never costs key."""
    previous = -1
    for exponent in (200, 100, 60, 30, 10, 1, 0):
        value = key_length(
            rounds=1_000_000,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=2.0**-exponent,
            eps_pa=2.0**-30,
            alpha=alpha,
        )
        assert value >= previous
        previous = value

    previous = -1
    for exponent in (200, 100, 60, 30, 10, 1, 0):
        value = key_length(
            rounds=1_000_000,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=2.0**-30,
            eps_pa=2.0**-exponent,
            alpha=alpha,
        )
        assert value >= previous
        previous = value


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS_IN_DOMAIN)
def test_key_length_vanishes_as_the_budgets_go_to_zero(alpha: float) -> None:
    """O-KEY-LENGTH-EPS-TO-ZERO (rubric line R8): l_max -> 0 as eps -> 0+."""
    # The registry entry's explicit threshold: l_max = 0 as soon as
    #   eps_PA <= 2^{-(alpha-1)/alpha * (n h_low - lambda_EC
    #                                   - ceil(log2(1/eps_EV)) + 1)}.
    threshold = (alpha - 1.0) / alpha * (1_000 * 1.0 + 1.0)
    assert (
        key_length(
            rounds=1_000,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=1.0,
            eps_pa=2.0 ** -(threshold + 1.0),
            alpha=alpha,
        )
        == 0
    )
    assert (
        key_length(
            rounds=1_000,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=1.0,
            eps_pa=2.0 ** -(threshold - 5.0),
            alpha=alpha,
        )
        > 0
    )
    # The same, driving eps_EV instead.
    assert (
        key_length(
            rounds=1_000,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=2.0**-1010,
            eps_pa=1.0,
            alpha=alpha,
        )
        == 0
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_key_rate_approaches_h_low_at_large_n() -> None:
    """O-KEY-LENGTH-LARGE-N: |l_max/n - h_low| <= (Delta + 1)/n, with Delta explicit."""
    alpha, eps = 1.5, 2.0**-30
    lambda_ec, h_low = 200_000, 1.0
    delta = lambda_ec + math.ceil(math.log2(1.0 / eps)) + (alpha / (alpha - 1.0)) * 30.0
    assert delta == pytest.approx(200_120.0)

    previous_gap = math.inf
    for rounds in (10**6, 10**7, 10**8, 10**9):
        value = key_length(
            rounds=rounds,
            h_low=h_low,
            lambda_ec=lambda_ec,
            eps_ev=eps,
            eps_pa=eps,
            alpha=alpha,
        )
        gap = abs(value / rounds - h_low)
        assert gap <= (delta + 1.0) / rounds + 1e-15
        assert gap < previous_gap
        previous_gap = gap
        assert value / rounds <= h_low  # approached from below


@pytest.mark.contract
@pytest.mark.oracle
def test_two_universal_hash_costs_exactly_one_bit() -> None:
    """Assumption A-HASH: the merely-two-universal family costs one further bit."""
    common = {
        "rounds": 1_000_000,
        "h_low": 1.0,
        "lambda_ec": 200_000,
        "eps_ev": 2.0**-30,
        "eps_pa": 2.0**-30,
        "alpha": 1.5,
    }
    ideal = key_length(**common, ideal_hash=True)
    merely = key_length(**common, ideal_hash=False)
    assert ideal == 799_881
    assert merely == 799_880
    assert ideal - merely == 1  # the penalty is in the SAFE direction


@pytest.mark.contract
def test_key_length_signature_carries_no_acceptance_probability() -> None:
    """O-KEY-LENGTH-ACCEPTANCE-INDEPENDENT: Pr[Omega_AT] cancels out entirely."""
    import inspect

    entry = oracle("O-KEY-LENGTH-ACCEPTANCE-INDEPENDENT")
    assert entry.claims == ("C3", "C14")
    parameters = set(inspect.signature(key_length).parameters)
    assert parameters == {
        "rounds",
        "h_low",
        "lambda_ec",
        "eps_ev",
        "eps_pa",
        "alpha",
        "ideal_hash",
    }
    for forbidden in ("p_omega", "pr_omega_at", "acceptance_probability"):
        assert forbidden not in parameters


@pytest.mark.contract
@pytest.mark.parametrize("alpha", (0.5, 1.0, 2.0, 2.5))
def test_key_length_rejects_alpha_outside_the_key_length_domain(alpha: float) -> None:
    """req:key-length-alpha-domain: every key-length statement is confined to (1, 2)."""
    with pytest.raises(ValueError, match="req:key-length-alpha-domain"):
        key_length(
            rounds=10,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=0.5,
            eps_pa=0.5,
            alpha=alpha,
        )


@pytest.mark.contract
@pytest.mark.parametrize(
    ("eps_pa", "eps_ev"), ((0.0, 0.5), (0.5, 0.0), (1.5, 0.5), (0.5, 1.5))
)
def test_key_length_rejects_budgets_outside_their_declared_domain(
    eps_pa: float, eps_ev: float
) -> None:
    """Contract Section 2.4: eps_pa and eps_ev lie in (0, 1]."""
    with pytest.raises(ValueError, match="eps_pa and eps_ev"):
        key_length(
            rounds=10,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=eps_ev,
            eps_pa=eps_pa,
            alpha=1.5,
        )
