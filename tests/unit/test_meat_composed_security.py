"""Authentication in the key length: the composed parameter, the net key, the gate.

``thm:keylength`` is split into the post-processing model, the secrecy
theorem, the correctness lemma ``lem:ev-correctness`` and
``cor:composed-security``, and the authentication scheme enters the reported
numbers. What the code owes, and what these tests hold it to:

* ``cor:composed-security`` (iii): beside every emitted ``key_length`` the
  engine reports ``security_parameter = eps_PA + eps_EV + 2 eps_auth`` and
  ``net_key_length = key_length - k_auth``, with no clamp, and neither on a run
  that emits no length (the interface's ``outputs`` rows);
* ``req:security-statement-not-vacuous``: the run is refused with the
  unchanged ``security_statement_vacuous`` when
  ``eps_PA + eps_EV + 2 eps_auth >= 1``, the sum formed exactly;
* the ``eps_auth`` and ``k_auth`` parameter rows: ``[0, 1)`` and a
  non-negative integer, both defaulting to 0, and neither entering
  Eq. ``eq:keylength`` -- so NO KEY LENGTH MOVES, which the frozen oracles
  (``tests/oracles/test_key_length.py``,
  ``tests/golden/test_key_length_against_registry.py``) pin unchanged;
* the ledger's emission rule: the seven key-length premises and the inherited
  A-SEQ on every run that reports a key length and on no other.

These are contract tests: each would fail if the claim it names were
implemented otherwise. No number here is an oracle; the key lengths compared
are the code's own at two settings of a parameter the expression does not
read.
"""

from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import yaml
from tests.support.provenance import COMPILED

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core.errors import SecurityStatementVacuousError
from certiqs_key.meat_core.finitekey.keylength import (
    ComposedSecurity,
    check_authentication_parameters,
    check_security_statement,
    composed_security,
    key_length,
    key_length_from_bound,
)
from certiqs_key.meat_core.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    FIRST_ORDER_ROWS,
    INHERITED_KEYS,
    KEY_LENGTH_ROWS,
    AssumptionId,
    RefusalReason,
    assumption_bindings,
    assumption_ledger,
    laboratory_parties,
)
from certiqs_key.solvers.frank_wolfe.general_keyrate import (
    key_length_from_first_order,
)

INTERFACE = Path(__file__).resolve().parents[2] / "spec" / "modules" / "meat-core" / (
    "interface.yaml"
)

#: A point well inside every domain, with a positive length.
BASE = {
    "rounds": 1_000_000,
    "lambda_ec": 200_000,
    "eps_ev": 2.0**-30,
    "eps_pa": 2.0**-30,
    "alpha": 1.5,
}


@pytest.mark.contract
def test_no_key_length_moves_with_the_authentication_parameters() -> None:
    """Neither ``eps_auth`` nor ``k_auth`` enters Eq. ``eq:keylength``.

    ``cor:composed-security`` (iii) composes the scheme's error into the
    security PARAMETER and subtracts its key consumption from the NET key; the
    length of ``thm:keylength`` and of ``cor:keylength-bound`` is the length it
    was. The interface rows say so in terms ("does not enter the key-length
    expression").
    """
    reference = key_length(h_low=0.5, **BASE)
    bounded = key_length_from_bound(h=0.5, **BASE)
    first_order = key_length_from_first_order(h_lb=0.5, **BASE)
    assert reference > 0
    for eps_auth in (0.0, 2.0**-40, 0.25):
        for k_auth in (0, 1, 10**9):
            assert key_length(h_low=0.5, eps_auth=eps_auth, k_auth=k_auth, **BASE) == (
                reference
            )
            assert key_length_from_bound(
                h=0.5, eps_auth=eps_auth, k_auth=k_auth, **BASE
            ) == bounded
            assert key_length_from_first_order(
                h_lb=0.5, eps_auth=eps_auth, k_auth=k_auth, **BASE
            ) == first_order


@pytest.mark.contract
def test_the_gate_counts_the_authentication_error_twice_and_exactly() -> None:
    """``req:security-statement-not-vacuous``: ``eps_PA + eps_EV + 2 eps_auth >= 1``.

    The refusal code is unchanged, ``security_statement_vacuous``; the gate is
    closed on the refusing side, decided on the exact sum, and at
    ``eps_auth = 0`` it is the two-budget rule.
    """
    corner = {**BASE, "eps_pa": 0.25, "eps_ev": 0.25}
    # 1/4 + 1/4 + 2 * 1/4 = 1: refused at every entry point that takes it.
    for refuse in (
        lambda: check_security_statement(0.25, 0.25, 0.25),
        lambda: key_length(h_low=0.5, eps_auth=0.25, **corner),
        lambda: key_length_from_bound(h=0.5, eps_auth=0.25, **corner),
        lambda: key_length_from_first_order(h_lb=0.5, eps_auth=0.25, **corner),
        lambda: composed_security(
            key_length=1, eps_pa=0.25, eps_ev=0.25, eps_auth=0.25
        ),
    ):
        with pytest.raises(SecurityStatementVacuousError) as refusal:
            refuse()
        assert refusal.value.reason == RefusalReason.SECURITY_STATEMENT_VACUOUS
        assert refusal.value.reason == "security_statement_vacuous"
        assert "eps_auth" in str(refusal.value)
    # ONCE WOULD NOT HAVE REFUSED IT: 1/4 + 1/4 + 1/4 < 1, so the factor 2 of
    # cor:composed-security (iii) is what closes the gate here.
    assert Fraction(0.25) * 3 < 1
    # JUST BELOW, by the smallest step of eps_auth, the run computes; in
    # binary64 the sum would round to exactly 1 and refuse it.
    below = math.nextafter(0.25, 0.0)
    assert 0.5 + 2 * below == 1.0
    assert Fraction(0.5) + 2 * Fraction(below) < 1
    check_security_statement(0.25, 0.25, below)
    assert key_length(h_low=0.5, eps_auth=below, **corner) == key_length(
        h_low=0.5, **corner
    )
    # AT THE DEFAULT IT IS THE TWO-BUDGET RULE: 1/2 + 1/2 refused, 1/2 + 1/4 not.
    with pytest.raises(SecurityStatementVacuousError):
        check_security_statement(0.5, 0.5)
    check_security_statement(0.5, 0.25)
    check_security_statement(0.5, 0.25, 0.0)


@pytest.mark.contract
def test_the_authentication_parameters_keep_their_domains() -> None:
    """``eps_auth`` in ``[0, 1)``, ``k_auth`` a non-negative integer, both default 0."""
    check_authentication_parameters(0.0, 0)
    check_authentication_parameters(math.nextafter(1.0, 0.0), 2**40)
    check_authentication_parameters(0.0, np.int64(3))  # type: ignore[arg-type]
    for eps_auth in (-(2.0**-1074), 1.0, math.inf, math.nan, False, True, "0.1", None):
        with pytest.raises(ValueError, match="eps_auth lies in"):
            check_authentication_parameters(eps_auth, 0)
        with pytest.raises(ValueError, match="eps_auth lies in"):
            key_length(h_low=0.5, eps_auth=eps_auth, **BASE)
        with pytest.raises(ValueError, match="eps_auth lies in"):
            check_security_statement(2.0**-30, 2.0**-30, eps_auth)
    for k_auth in (-1, 1.0, 2.5, True, "3"):
        with pytest.raises(ValueError, match="k_auth is a non-negative integer"):
            check_authentication_parameters(0.0, k_auth)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="k_auth is a non-negative integer"):
            key_length_from_bound(h=0.5, k_auth=k_auth, **BASE)  # type: ignore[arg-type]


@pytest.mark.contract
def test_the_composed_parameter_and_the_net_key() -> None:
    """``cor:composed-security`` (iii): the parameter and the net key ``l - k_auth``.

    At the defaults the parameter is ``eps_PA + eps_EV`` -- the parameter of
    (ii), numerically of (i) -- and the net key IS the key length. The net key
    is not clamped: a run that consumed more pre-shared key than it produced
    reports a negative number, which is the report that it yields no net key.
    """
    length = key_length(h_low=0.5, **BASE)
    plain = composed_security(key_length=length, eps_pa=2.0**-30, eps_ev=2.0**-30)
    assert plain == ComposedSecurity(security_parameter=2.0**-29, net_key_length=length)

    charged = composed_security(
        key_length=length,
        eps_pa=2.0**-30,
        eps_ev=2.0**-30,
        eps_auth=2.0**-40,
        k_auth=1_000,
    )
    assert Fraction(charged.security_parameter) == (
        Fraction(2.0**-30) + Fraction(2.0**-30) + 2 * Fraction(2.0**-40)
    )
    assert charged.net_key_length == length - 1_000

    # NO CLAMP, and zero is reported as zero.
    assert composed_security(
        key_length=10, eps_pa=0.25, eps_ev=0.25, k_auth=100
    ).net_key_length == -90
    assert composed_security(
        key_length=100, eps_pa=0.25, eps_ev=0.25, k_auth=100
    ).net_key_length == 0
    assert composed_security(key_length=0, eps_pa=0.25, eps_ev=0.25).net_key_length == 0


@pytest.mark.contract
def test_the_composed_parameter_is_never_rounded_down() -> None:
    """A bound on a distinguishing advantage is reported at or above its value.

    At non-dyadic sums binary64 addition rounds to nearest and may land below
    the exact sum; the reported parameter is the smallest machine number at or
    above it. ``0.1 + 0.2`` is the textbook case where the nearest lies above
    and nothing moves; ``0.1 + 0.7`` rounds down in binary64.
    """
    for eps_pa, eps_ev, eps_auth in (
        (0.1, 0.2, 0.0),
        (0.1, 0.7, 0.0),
        (0.1, 0.2, 0.3),
        (2.0**-30, 3.0 * 2.0**-31, 0.1),
    ):
        exact = Fraction(eps_pa) + Fraction(eps_ev) + 2 * Fraction(eps_auth)
        reported = composed_security(
            key_length=1, eps_pa=eps_pa, eps_ev=eps_ev, eps_auth=eps_auth
        ).security_parameter
        assert Fraction(reported) >= exact
        assert Fraction(math.nextafter(reported, 0.0)) < exact
    assert Fraction(0.1 + 0.7) < Fraction(0.1) + Fraction(0.7)


@pytest.mark.contract
def test_the_key_length_premises_are_emitted_exactly_with_a_key_length() -> None:
    """The interface's ``emission_rule``: "on every run that reports a key length".

    The own premises, in the ledger's order after A-HASH, and the
    inherited A-SEQ after A-RHOM -- and none of them on a run that reports
    neither a length nor a first-order bound, whether or not a length was
    wanted. Two of them, A-SEED and A-LAB
    (``FIRST_ORDER_ROWS``), are emitted with a reported first-order bound too,
    which rests on them through ``lem:product-marginal``; the rule reads "on
    every run that reports a key length or a first-order bound". The inherited
    A-SEQ follows the same rule. A-KEYREG and A-HASH are key-length rows only,
    and the inherited A-RHOM follows A-SEQ's rule: ``lem:estimate``, the one
    root of a run that reports neither a bound nor a length, rests on no
    assumption. A-LAB-ALICE and A-LAB-BOB are one premise, A-LAB, whose own
    rule ("once per party ...")
    emits it at both parties with a length and, without one, in trusted-source
    mode at the party of A only; its rows are checked in the next test.
    """
    document = yaml.safe_load(INTERFACE.read_text(encoding="utf-8"))
    rules = document["assumption_ledger"]["emission_rule"]
    on_a_key_length = {
        short_id
        for short_id, rule in rules.items()
        if str(rule).startswith("on every run that reports a key length")
    }
    assert str(rules["A-LAB"]).startswith("once per party of the declaration")
    assert {str(member) for member in KEY_LENGTH_ROWS} - {"A-LAB"} | {
        "A-SEQ", "A-RHOM"
    } == on_a_key_length
    assert INHERITED_KEYS["A-SEQ"] == "sequential_round_model"
    premises = [ASSUMPTION_MACHINE_KEYS[member] for member in KEY_LENGTH_ROWS]
    assert premises == [
        "key_register",
        "pa_hash_family",
        "post_processing_seeds",
        "parameters_fixed_before_run",
        "post_processing_as_analysed",
        "classical_channel_authenticated",
        "laboratory_sealed",
    ]
    # meat-core/ass:eve-dim is superseded: no rule emits it.
    assert "A-EVE-DIM" not in rules

    with_bound = {
        short_id
        for short_id, rule in rules.items()
        if str(rule).endswith("or a first-order bound")
        and short_id in {str(member) for member in KEY_LENGTH_ROWS}
    }
    assert {str(member) for member in FIRST_ORDER_ROWS} - {"A-LAB"} == with_bound
    bound_premises = [ASSUMPTION_MACHINE_KEYS[member] for member in FIRST_ORDER_ROWS]
    assert bound_premises == [
        "post_processing_seeds",
        "laboratory_sealed",
    ]

    def ledger(*, reported: bool, bound: bool = True) -> tuple[str, ...]:
        return assumption_ledger(
            trusted_source=True,
            alice_dim=2,
            alice_party="A",
            constraint_entries=0,
            key_length_wanted=True,
            key_length_reported=reported,
            first_order=bound,
        )

    with_length, without = ledger(reported=True), ledger(reported=False)
    # A-SEQ and A-RHOM are emitted with the bound too.
    assert set(with_length) - set(without) == set(premises) - set(bound_premises)
    # A-LAB once per party: twice with a length, once at the party of A
    # without one (trusted-source mode here).
    assert with_length.count("laboratory_sealed") == 2
    assert without.count("laboratory_sealed") == 1
    assert "sequential_round_model" in without
    assert "round_homogeneity_declaration" in without
    assert set(without) <= set(with_length)
    # A bound and no length: the two first, in the ledger's order.
    assert list(without[: len(bound_premises)]) == bound_premises
    # Neither: no row at all (lem:estimate rests on no assumption).
    assert ledger(reported=False, bound=False) == ()
    lab = premises.index("laboratory_sealed")
    expanded = [*premises[: lab + 1], "laboratory_sealed", *premises[lab + 1 :]]
    assert list(with_length[: len(expanded)]) == expanded
    assert with_length.index("sequential_round_model") == (
        with_length.index("round_homogeneity_declaration") + 1
    )
    # Every row once, but A-LAB, which is one row per party.
    assert len(set(with_length)) == len(with_length) - 1


@pytest.mark.contract
@pytest.mark.parametrize("alice_party", ["A", "B"])
def test_the_laboratory_premise_is_emitted_once_per_party(alice_party: str) -> None:
    """A-LAB's ``emission_rule`` (meat-core/ass:lab).

    "Once per party of the declaration, its row naming the party: on a run
    that reports a key length, at both parties, unconditionally; on a run
    that reports a first-order bound and no key length, in trusted-source mode
    only and only at the party to which the party partition assigns A, and in
    untrusted-source mode not at all". The party is the row's ``party``
    binding, which the run tier reads as the row's party.
    """
    key = ASSUMPTION_MACHINE_KEYS[AssumptionId.A_LAB]

    def rows(*, trusted: bool, reported: bool, bound: bool) -> list[str | None]:
        ledger = assumption_ledger(
            trusted_source=trusted,
            alice_dim=2,
            alice_party=alice_party,
            constraint_entries=0,
            key_length_wanted=True,
            key_length_reported=reported,
            first_order=bound,
        )
        parties = laboratory_parties(
            trusted_source=trusted,
            alice_party=alice_party,
            key_length_reported=reported,
            first_order=bound,
        )
        declared = {"source_mode": "x", "party_partition": "x"}
        lab_only = tuple(item for item in ledger if item == key)
        bindings = assumption_bindings(lab_only, declared, parties=parties)
        return [dict(pairs).get("party") for _, pairs in bindings]  # type: ignore[misc]

    for trusted in (True, False):
        # A key length: both parties, A then B, in either mode.
        assert rows(trusted=trusted, reported=True, bound=True) == ["A", "B"]
        # Neither a bound nor a length: none.
        assert rows(trusted=trusted, reported=False, bound=False) == []
    # A first-order bound alone: trusted, at the party of A only ...
    assert rows(trusted=True, reported=False, bound=True) == [alice_party]
    # ... untrusted, none.
    assert rows(trusted=False, reported=False, bound=True) == []
    with pytest.raises(ValueError, match="parties"):
        assumption_bindings((key, key), {"source_mode": "x", "party_partition": "x"},
                            parties=("A",))


@pytest.mark.contract
@pytest.mark.requires_qics
def test_a_run_reports_the_composed_outputs_beside_its_length() -> None:
    """End to end: the one driver emits the two outputs and the premises.

    The same declaration run at the defaults and at ``eps_auth = 2^-40``,
    ``k_auth = 256``: the length is identical, the net key is the length less
    256, the parameter grows by ``2^-39``, and the ledger carries the
    key-length premises on both. A run that withholds its length carries
    neither output and none of the premises.
    """
    from dataclasses import replace

    from tests.support.general_toys import decoy_like_general

    from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
    from certiqs_key.solvers.frank_wolfe.keyrate import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    licensed = replace(
        decoy_like_general(), source_replacement_license={"supplier": "test"}
    )
    options = FrankWolfeOptions(max_iterations=1)
    # The declaration stands for compiled output and this tests the
    # mathematics of the composed outputs, so it passes the token
    # (req:compiled-declaration-only).
    plain = solve(licensed, QicsSectorChoiOracle(), options=options, compiled=COMPILED)
    charged = solve(
        licensed,
        QicsSectorChoiOracle(),
        options=options,
        eps_auth=2.0**-40,
        k_auth=256,
        compiled=COMPILED,
    )
    assert plain.key_length is not None
    assert charged.key_length == plain.key_length
    assert plain.net_key_length == plain.key_length
    assert charged.net_key_length == plain.key_length - 256
    eps_pa, eps_ev = licensed.parameters.eps_pa, licensed.parameters.eps_ev
    assert plain.security_parameter is not None
    assert Fraction(plain.security_parameter) >= Fraction(eps_pa) + Fraction(eps_ev)
    assert charged.security_parameter is not None
    assert Fraction(charged.security_parameter) >= (
        Fraction(eps_pa) + Fraction(eps_ev) + 2 * Fraction(2.0**-40)
    )
    premises = {ASSUMPTION_MACHINE_KEYS[member] for member in KEY_LENGTH_ROWS}
    for result in (plain, charged):
        assert premises | {"sequential_round_model"} <= set(result.assumption_ledger)
        assert {"A-AUTH", "A-SEQ"} <= set(result.assumption_ids)
        assert "A-EVE-DIM" not in result.assumption_ids
        # A-LAB once per party (meat-core/ass:lab): two rows, one id.
        assert result.assumption_ledger.count("laboratory_sealed") == 2
        assert result.assumption_ids.count("A-LAB") == 1
        assert len(set(result.assumption_ids)) == len(result.assumption_ids)
        assert [k for k, _ in result.assumption_bindings] == list(
            result.assumption_ledger
        )
        assert [
            dict(pairs)["party"]
            for key, pairs in result.assumption_bindings
            if key == "laboratory_sealed"
        ] == ["A", "B"]

    # WITHHELD: the A-SRC gate closes without its attestation, so the run
    # reports the estimate only, and nothing composed travels with it.
    withheld = solve(
        decoy_like_general(),
        QicsSectorChoiOracle(),
        options=options,
        k_auth=256,
        compiled=COMPILED,
    )
    assert withheld.key_length is None
    assert withheld.security_parameter is None
    assert withheld.net_key_length is None
    # A bound still reported carries FIRST_ORDER_ROWS, and no
    # other key-length premise.
    carried = (
        {ASSUMPTION_MACHINE_KEYS[member] for member in FIRST_ORDER_ROWS}
        if withheld.assurance in (Assurance.FIRST_ORDER, Assurance.CERTIFIED)
        else set()
    )
    assert premises & set(withheld.assumption_ledger) == carried
    assert ("sequential_round_model" in withheld.assumption_ledger) is bool(carried)
