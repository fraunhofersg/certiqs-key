"""The fixed-length key length, against the FROZEN key-length cases.

``KEY_LENGTH_CASES`` in ``tests/oracles/registry.py`` carries four cases with
their arithmetic written out, and ``O-KEY-LENGTH-*`` carry the monotonicity, the
``eps -> 0`` behaviour, the large-``n`` envelope and the acceptance-probability
independence. Every expected value below is theirs.

These are exact integer comparisons. There is no tolerance to record: the key
length is an integer, the deductions are exact binary quantities on these
budgets, and the only rounding in the chain is the floor the contract itself
prescribes.
"""

from __future__ import annotations

import math

import pytest
from reference import key_length as reference_key_length
from registry import KEY_LENGTH_CASES, KeyLengthCase, oracle

from certiqs_key.meat_core.errors import (
    SecurityGateError,
    SecurityStatementVacuousError,
)
from certiqs_key.meat_core.finitekey.keylength import key_length


#: THE VACUOUS CORNER, and every call below stays out of it or
#: asserts it. The gate ("refuse the corner with a named reason") means that a
#: run with ``eps_PA + eps_EV >= 1`` is refused with
#: ``security_statement_vacuous``: the ``(eps_PA + eps_EV)``-security statement
#: a length would be reported under is empty there, satisfied by every protocol
#: including one that publishes the key.
#:
#: WHAT IT COSTS THIS FILE, DECLARED RATHER THAN ABSORBED. The frozen cases
#: use ``eps = 1`` freely, because at the maximal budgets both
#: deductions vanish and the arithmetic isolates one mechanism at a time -- the
#: floor in ``KL-2-floor``, the clamp in ``FOKL-2-clamped``. That region is
#: refused. THE REGISTRY IS NOT EDITED and THE ARITHMETIC IS NOT CHANGED:
#: every frozen integer inside the corner is still asserted, against the
#: INDEPENDENT reference implementation in ``tests/oracles/reference.py``, which
#: is a transcription of Eq. eq:keylength and carries no gate; what the engine
#: asserts there is the refusal. Every sweep that reaches ``eps = 1`` stops
#: short of the corner AND asserts the refusal at it, so the endpoint is
#: covered rather than dropped.
def at_the_vacuous_corner(case: KeyLengthCase) -> bool:
    """Return whether the corner gate refuses this frozen case."""
    return case.eps_pa + case.eps_ev >= 1.0



@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", KEY_LENGTH_CASES, ids=lambda c: c.case_id)
def test_o_key_length_frozen_cases(case: KeyLengthCase) -> None:
    """O-KEY-LENGTH: the four frozen cases, exactly."""
    entry = oracle("O-KEY-LENGTH")
    assert entry.claims == ("C14",)
    arguments = {
        "rounds": case.rounds,
        "h_low": case.h_low,
        "lambda_ec": case.lambda_ec,
        "eps_ev": case.eps_ev,
        "eps_pa": case.eps_pa,
        "alpha": case.alpha,
        "ideal_hash": case.ideal_hash,
    }
    if at_the_vacuous_corner(case):
        # KL-2-floor: ``eps_EV = eps_PA = 1``, chosen so that "both deductions
        # vanish" and the case pins the DOWNWARD rounding alone. The rounding
        # is unchanged and is still pinned -- the frozen 16 is reproduced from
        # the independent reference, whose floor is the contract's -- and the
        # ENGINE refuses the run under the named reason.
        assert reference_key_length(**arguments) == case.expected
        with pytest.raises(SecurityStatementVacuousError) as refusal:
            key_length(**arguments)
        assert refusal.value.reason == "security_statement_vacuous"
        # AND THE FLOOR IS PINNED WHERE A RUN MAY STILL BE MADE, so that the
        # mechanism the case exists for keeps a live assertion on the ENGINE.
        # n log2 3 is irrational, so the bracket is never an integer and the
        # rounding direction is visible at every budget, not only at eps = 1:
        # at eps_EV = eps_PA = 1/4 the deductions are 2 and 3 * 2 = 6 exactly.
        inside = {**arguments, "eps_ev": 0.25, "eps_pa": 0.25}
        bracket = case.rounds * case.h_low - 2.0 - 6.0 + 1.0
        assert bracket != math.floor(bracket)
        assert key_length(**inside) == math.floor(bracket)
        # UPWARD WOULD BE AN OVERSTATEMENT OF THE KEY BY NEARLY A BIT, which is
        # what the frozen case says of 17 against 16 and holds here of 9
        # against 8.
        assert key_length(**inside) < bracket
        return
    assert key_length(**arguments) == case.expected


@pytest.mark.contract
@pytest.mark.oracle
def test_the_plus_one_constant_is_this_contracts() -> None:
    """Remark rem:plus2: ``+1``, not the source's ``+2``.

    KL-1 with the constant changed would give 799 882. The one-bit difference
    is the announced error-verification acceptance flag, which is what buys
    accepted-state secrecy; an implementation must not silently use ``+2``.
    """
    case = next(c for c in KEY_LENGTH_CASES if c.case_id == "KL-1")
    assert case.expected == 799_881
    bracket = (
        case.rounds * case.h_low
        - case.lambda_ec
        - math.ceil(-math.log2(case.eps_ev))
        - (case.alpha / (case.alpha - 1.0)) * (-math.log2(case.eps_pa))
    )
    assert bracket + 1.0 == float(case.expected)
    assert bracket + 2.0 == float(case.expected + 1)


@pytest.mark.contract
@pytest.mark.oracle
def test_o_key_length_monotone() -> None:
    """O-KEY-LENGTH-MONOTONE: Proposition prop:monotone (i), (ii), (iii)."""
    assert oracle("O-KEY-LENGTH-MONOTONE").claims == ("C15",)
    base = {
        "rounds": 1_000_000,
        "h_low": 1.0,
        "lambda_ec": 200_000,
        "eps_ev": 2.0**-30,
        "eps_pa": 2.0**-30,
        "alpha": 1.5,
    }
    reference = key_length(**base)

    # (i) non-increasing in lambda_EC
    previous = math.inf
    for lambda_ec in (0, 1_000, 200_000, 500_000):
        value = key_length(**{**base, "lambda_ec": lambda_ec})
        assert value <= previous
        previous = value

    # (ii) non-decreasing in eps_EV. THE SWEEP STOPS AT 1/2 AND NOT AT 1: the
    # endpoint eps = 1 is the vacuous corner, where the
    # monotone envelope runs out of security statements rather than out of
    # bits. The endpoint is asserted as a refusal immediately below, so the
    # sweep covers the whole of the domain a run may be made in.
    previous = -1
    for eps_ev in (2.0**-60, 2.0**-30, 2.0**-10, 0.5):
        value = key_length(**{**base, "eps_ev": eps_ev})
        assert value >= previous
        previous = value
    with pytest.raises(SecurityStatementVacuousError):
        key_length(**{**base, "eps_ev": 1.0})

    # (iii) non-decreasing in eps_PA, the same reading of the same endpoint.
    previous = -1
    for eps_pa in (2.0**-60, 2.0**-30, 2.0**-10, 0.5):
        value = key_length(**{**base, "eps_pa": eps_pa})
        assert value >= previous
        previous = value
    with pytest.raises(SecurityStatementVacuousError):
        key_length(**{**base, "eps_pa": 1.0})

    # (iv) unchanged when nothing that enters the formula changes.
    assert key_length(**base) == reference


@pytest.mark.contract
@pytest.mark.oracle
def test_o_key_length_eps_to_zero() -> None:
    """O-KEY-LENGTH-EPS-TO-ZERO: perfect secrecy from finitely many rounds is none."""
    assert oracle("O-KEY-LENGTH-EPS-TO-ZERO").claims == ("C14", "C15")
    # THE OTHER BUDGET IS 1/2 AND NOT 1 IN EACH PAIR: one budget is driven to
    # zero and the other must stay out of the vacuous corner. The
    # entry's content is unaffected -- what it pins is that perfect secrecy
    # from finitely many rounds is no key, which is the DRIVEN budget's doing.
    assert (
        key_length(
            rounds=1000,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=0.5,
            eps_pa=2.0**-400,
            alpha=1.5,
        )
        == 0
    )
    assert (
        key_length(
            rounds=1000,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=2.0**-1050,
            eps_pa=0.5,
            alpha=1.5,
        )
        == 0
    )
    # An eps below 2^-1074 is not a positive float at all and is refused as a
    # domain violation, not silently treated as zero. THE DOMAIN CHECK COMES
    # FIRST AND THE CORNER GATE SECOND: a budget outside (0, 1] is a
    # ValueError and never a security refusal, which is what the pairing of
    # these two assertions says.
    assert 2.0**-2000 == 0.0
    with pytest.raises(ValueError, match=r"eps_ev lies in \(0, 1\]"):
        key_length(
            rounds=1000,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=2.0**-2000,
            eps_pa=0.5,
            alpha=1.5,
        )
    with pytest.raises(ValueError, match=r"eps_ev lies in \(0, 1\]"):
        key_length(
            rounds=1000,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=2.0**-2000,
            eps_pa=1.0,
            alpha=1.5,
        )
    # And an eps so small that 1/eps would overflow to inf still returns a value.
    assert (
        key_length(
            rounds=10**9,
            h_low=1.0,
            lambda_ec=0,
            eps_ev=0.5,
            eps_pa=2.0**-1074,
            alpha=1.5,
        )
        >= 0
    )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("rounds", (10**3, 10**5, 10**7, 10**9))
def test_o_key_length_large_n_envelope(rounds: int) -> None:
    """O-KEY-LENGTH-LARGE-N: |l/n - h_low| <= (Delta + 1)/n, with Delta explicit."""
    assert oracle("O-KEY-LENGTH-LARGE-N").claims == ("C14",)
    alpha, eps = 1.5, 2.0**-30
    lambda_ec, h_low = 200_000, 1.0
    delta = lambda_ec + 30 + (alpha / (alpha - 1.0)) * 30
    assert delta == pytest.approx(200_120.0)
    value = key_length(
        rounds=rounds,
        h_low=h_low,
        lambda_ec=lambda_ec,
        eps_ev=eps,
        eps_pa=eps,
        alpha=alpha,
    )
    if rounds * h_low - delta >= 0.0:
        assert abs(value / rounds - h_low) <= (delta + 1.0) / rounds
    else:
        assert value == 0


@pytest.mark.contract
@pytest.mark.oracle
def test_o_key_length_takes_no_acceptance_probability() -> None:
    """O-KEY-LENGTH-ACCEPTANCE-INDEPENDENT: the parameter does not exist here."""
    entry = oracle("O-KEY-LENGTH-ACCEPTANCE-INDEPENDENT")
    assert entry.claims == ("C3", "C14")
    import inspect

    parameters = set(inspect.signature(key_length).parameters)
    # PLUS eps_auth
    # and k_auth, A-AUTH's parameters, which the function validates and which
    # enter its corner gate (eps_auth) but not the expression
    # (cor:composed-security (iii); the interface's parameter rows). The
    # oracle's subject, no acceptance-probability argument, is unchanged.
    assert parameters == {
        "rounds",
        "h_low",
        "lambda_ec",
        "eps_ev",
        "eps_pa",
        "alpha",
        "ideal_hash",
        "eps_auth",
        "k_auth",
    }
    for forbidden in ("acceptance_probability", "pr_omega_at", "p_omega"):
        assert forbidden not in parameters


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_universal_hash_penalty_is_one_bit_in_the_safe_direction() -> None:
    """Assumption A-HASH: a merely two-universal family costs one bit."""
    case = next(c for c in KEY_LENGTH_CASES if c.case_id == "KL-4-two-universal-hash")
    arguments = {
        "rounds": case.rounds,
        "h_low": case.h_low,
        "lambda_ec": case.lambda_ec,
        "eps_ev": case.eps_ev,
        "eps_pa": case.eps_pa,
        "alpha": case.alpha,
    }
    ideal = key_length(**arguments, ideal_hash=True)
    merely = key_length(**arguments, ideal_hash=False)
    assert merely == case.expected
    assert ideal - merely == 1


@pytest.mark.contract
def test_alpha_outside_the_key_length_domain_is_refused() -> None:
    """req:key-length-alpha-domain: a KEY-LENGTH statement lives in (1, 2) only."""
    # THE BUDGETS SUM BELOW ONE: 1/2 and
    # 1/2 would sum to exactly 1, which is inside the refused corner (the predicate
    # is `>= 1`, because a security statement at exactly 1 is as empty as one
    # above it). The alpha domain is what this test is about, so the budgets are moved
    # rather than the assertion.
    arguments = {
        "rounds": 1_000_000,
        "h_low": 1.0,
        "lambda_ec": 0,
        "eps_ev": 0.25,
        "eps_pa": 0.25,
    }
    assert key_length(**arguments, alpha=1.9) > 0
    for alpha in (1.0, 2.0, 2.5, 10.0):
        with pytest.raises(SecurityGateError, match="req:key-length-alpha-domain"):
            key_length(**arguments, alpha=alpha)
    # AND THE CORNER GATE IS DECIDED BEFORE THE ALPHA GATE, which is the
    # ORDER THE INTERFACE TABLE FIXES: `security_statement_not_vacuous` is
    # order 7 and `alpha_in_the_profile_domain` is order 8. At a point inside
    # the corner AND outside (1, 2) the corner refusal is the one a caller
    # gets, through every door: the same pair of rules gives one answer
    # whichever entry point is used.
    with pytest.raises(SecurityStatementVacuousError):
        key_length(**{**arguments, "eps_ev": 0.5, "eps_pa": 0.5}, alpha=2.5)
