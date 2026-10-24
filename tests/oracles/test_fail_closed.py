"""Fail-closed labelling and the gates that guard the key-length output.

spec/architecture.md 9: "non-certifying repairs can never produce
``certified``". contract.tex adds two more hard failures that an implementation
must reproduce:

* ``h_low = +inf`` reaching the key-length step: emit NO key-length claim and
  report the declaration/acceptance mismatch (Remark ``rem:hlow-range``);
* a nonempty constraint list combined with a key-length output without BOTH
  membership of the licensed class of the declared source mode AND
  ``attack_set_license`` (Section 2.1 and the "Interface consequence" of
  Section 4.19);
* a declared ``tau_A`` without ``source_replacement_license`` -- new at 0.3.0,
  and subject to the same "Interface consequence" paragraph, with the standing
  exception that at ``d_A = 1`` the licence is vacuous and MUST NOT be
  demanded.

The registry entries are ``O-HLOW-INFINITE``, ``O-CONSTRAINT-GATE``,
``O-CGATE-DEGENERATE``, ``O-SOURCE-LICENSE-GATE`` and
``O-ASSURANCE-ESTIMATE``.
"""

from __future__ import annotations

import math
from dataclasses import replace

import pytest
from reference import divergence_kernel, key_length
from registry import ASSURANCE, ORACLES, is_superseded, oracle
from toy_declarations import (
    ALL_TOYS,
    ALL_TOYS_0_3_0,
    TOY1_RETENTION,
    TOY4C_INFEASIBLE,
    TOY5_CONSTRAINED,
    TOY5_CONSTRAINED_UNTRUSTED,
    TOY6_REMOVABLE,
    TOY7_NON_HOMOGENEOUS,
    TOY8_TRUSTED_MARGINAL,
    TOY8_UNTRUSTED,
    TOY9_SINGULAR_MARGINAL,
    TOY10_EMBEDDED,
    ToyDeclaration,
    source_mode,
)
from toy_evaluation import acceptance_point, objective_at, statistics

ALPHAS = (1.05, 1.25, 1.5, 1.75, 1.9)


# ---------------------------------------------------------------------------
# The gates, expressed exactly as contract.tex Section 2.1 and the "Interface
# consequence" of Section 4.19 state them. These are PREDICATES ON THE
# DECLARATION, not computations, which is why they live here and not in
# `reference.py`.
# ---------------------------------------------------------------------------


def constraint_gate_part_i(toy: ToyDeclaration) -> bool:
    """Part (i): the list lies in the licensed class of the DECLARED source mode.

    Definition ``def:homog``: every entry declared homogeneous, carrying its
    ``c_k``, in trusted-source mode, a real scalar right-hand side in
    untrusted-source mode. A TYPE CHECK AT EVERY ``d_A``: in trusted-source
    mode an entry whose record names no ``c_k`` (the general form) fails it at
    ``d_A = 1`` too. It DEGENERATES in the two cases of Remark ``rem:cgate``
    -- see :func:`constraint_gate_part_i_is_vacuous`.
    """
    if source_mode(toy) == "untrusted":
        # def:homog (b): a TYPE check that a well-formed declaration passes by
        # construction.
        return all(isinstance(entry.bound, float) for entry in toy.constraint_list)
    return all(entry.homogeneous_scalar is not None for entry in toy.constraint_list)


def constraint_gate_part_i_is_vacuous(toy: ToyDeclaration) -> bool:
    """Return whether a passing part (i) is evidence of nothing (Remark rem:cgate).

    In untrusted-source mode part (i) is vacuously true: the entry type is
    scalar by construction. At ``d_A = 1`` it is a type check that rejects
    only a general tag a producer can avoid, every ``1x1`` Hermitian being a
    multiple of ``tau_A``. In both cases the constrained branch rests ENTIRELY
    on the unverifiable attestation (``req:degenerate-gate-report``).
    """
    return source_mode(toy) == "untrusted" or toy.alice_dim == 1


def source_replacement_gate(toy: ToyDeclaration) -> bool:
    """Return whether ``toy`` clears the A-SRC gate of Section 4.19.

    "A declared ``tau_A`` without ``source_replacement_license`` (Assumption
    A-SRC) must hard-fail before any key-length output, and at ``d_A = 1`` the
    licence is vacuous and must not be demanded."
    """
    if source_mode(toy) == "untrusted":
        return True  # A-SRC is NOT ASSERTED; there is nothing to license
    if toy.alice_dim == 1:
        return True  # VACUOUS (rem:modes-da1 (b5)); demanding it is wrong
    return toy.source_replacement_license is not None


def key_length_permitted(toy: ToyDeclaration) -> bool:
    """Return whether ``toy`` may be combined with a key-length output.

    contract.tex Section 2.1, ``constraint_list`` row: "a key-length output may
    be combined with m >= 1 only if (i) the list lies in the licensed class of
    the declared source mode ... AND (ii) attack_set_license is present.
    Hard-fail otherwise (fail-closed); numerical use outside the security chain
    is unrestricted." Section 4.19 extends the same discipline to the marginal.
    """
    if not source_replacement_gate(toy):
        return False
    if not toy.constraint_list:
        return True
    return constraint_gate_part_i(toy) and toy.attack_set_license is not None


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_h_low_is_plus_infinity_when_acceptance_is_unreachable(alpha: float) -> None:
    """O-HLOW-INFINITE: TOY-4c has no absolutely continuous accepted vector."""
    entry = oracle("O-HLOW-INFINITE")
    assert entry.value == math.inf
    assert entry.kind == "fail-closed"

    phi = statistics(TOY4C_INFEASIBLE, {"s0": 1.0})
    q = acceptance_point(TOY4C_INFEASIBLE)
    assert phi["chat0"] == pytest.approx(0.0)
    assert q["chat0"] > 0.0  # q is not absolutely continuous w.r.t. Phi[omega]

    value = objective_at(TOY4C_INFEASIBLE, alpha, {"s0": 1.0})
    assert value == math.inf
    assert not math.isnan(value)  # +inf, never NaN and never clamped


@pytest.mark.contract
@pytest.mark.oracle
def test_infinite_h_low_yields_no_key_length_claim() -> None:
    """O-HLOW-INFINITE: the fail-closed branch refuses, it does not return a number."""
    with pytest.raises(ValueError, match="rem:hlow-range"):
        key_length(
            rounds=1_000_000,
            h_low=math.inf,
            lambda_ec=0,
            eps_ev=2.0**-30,
            eps_pa=2.0**-30,
            alpha=1.5,
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_extended_kernel_is_what_produces_the_infinity() -> None:
    """O-KERNEL-CONVENTIONS: the lsc extension of foundations/lem:kernel, frozen."""
    assert oracle("O-KERNEL-CONVENTIONS").claims == ("C9b",)
    assert divergence_kernel(0.0, 0.0) == 0.0
    assert divergence_kernel(0.0, 0.5) == 0.0
    assert divergence_kernel(0.5, 0.0) == math.inf
    assert divergence_kernel(0.5, 0.5) == 0.0
    assert divergence_kernel(0.5, 0.25) == pytest.approx(0.5)
    # A single term may be negative; only the full KL sum is non-negative.
    assert divergence_kernel(0.25, 0.5) == pytest.approx(-0.25)
    assert divergence_kernel(0.25, 0.5) + divergence_kernel(0.75, 0.5) > 0.0
    # Non-increasing in v, which is what Theorem thm:convexity uses on K.
    values = [divergence_kernel(0.5, v) for v in (0.1, 0.25, 0.5, 0.9, 1.0)]
    assert values == sorted(values, reverse=True)


@pytest.mark.contract
@pytest.mark.parametrize("u", (0.0, 0.5))
def test_the_kernel_rejects_arguments_outside_its_domain(u: float) -> None:
    """Lemma foundations/lem:kernel is stated on the non-negative quadrant only."""
    with pytest.raises(ValueError, match="non-negative quadrant"):
        divergence_kernel(u, -0.1)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_part_constraint_gate_verdicts() -> None:
    """O-CONSTRAINT-GATE: the four frozen verdicts, and both parts are needed."""
    entry = oracle("O-CONSTRAINT-GATE")
    assert entry.claims == ("C14", "C17")

    assert key_length_permitted(TOY1_RETENTION) is True  # L empty

    # Part (ii) fails: homogeneous, but no supplier attestation.
    assert TOY5_CONSTRAINED.constraint_list[0].homogeneous_scalar == 0.5
    assert TOY5_CONSTRAINED.attack_set_license is None
    assert key_length_permitted(TOY5_CONSTRAINED) is False
    assert key_length_permitted(TOY6_REMOVABLE) is False

    # Part (i) fails: Theta = diag(1, 1/2) is not any multiple of tau_A = I/2.
    assert TOY7_NON_HOMOGENEOUS.constraint_list[0].homogeneous_scalar is None
    assert key_length_permitted(TOY7_NON_HOMOGENEOUS) is False


@pytest.mark.contract
@pytest.mark.oracle
def test_both_parts_of_the_gate_are_independently_load_bearing() -> None:
    """Neither homogeneity alone nor a licence alone opens the gate."""
    from dataclasses import replace

    licensed = replace(
        TOY5_CONSTRAINED,
        attack_set_license={"certificate": "supplied by proof-reductions"},
    )
    assert key_length_permitted(licensed) is True  # (i) and (ii) both hold

    licensed_but_inhomogeneous = replace(
        TOY7_NON_HOMOGENEOUS,
        attack_set_license={"certificate": "supplied by proof-reductions"},
    )
    assert key_length_permitted(licensed_but_inhomogeneous) is False


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_a_blocked_gate_still_permits_the_numerical_value(alpha: float) -> None:
    """Numerical use outside the security chain is unrestricted (Section 2.1)."""
    assert key_length_permitted(TOY7_NON_HOMOGENEOUS) is False
    assert objective_at(TOY7_NON_HOMOGENEOUS, alpha, {"s0": 1.0}) == pytest.approx(
        0.0, abs=1e-12
    )

    assert key_length_permitted(TOY5_CONSTRAINED) is False
    constrained = objective_at(TOY5_CONSTRAINED, alpha, {"s0": 0.5, "s1": 0.5})
    assert constrained > 0.0
    assert math.isfinite(constrained)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_constrained_value_is_the_one_the_gate_protects() -> None:
    """The gate exists because h_low(L) >= h_low({}) -- a tightening bought by A-ATK."""
    for alpha in ALPHAS:
        unconstrained = objective_at(TOY1_RETENTION, alpha, {"s0": 0.0, "s1": 1.0})
        constrained = objective_at(TOY5_CONSTRAINED, alpha, {"s0": 0.5, "s1": 0.5})
        assert constrained > unconstrained
    # Feeding the tighter value to Eq. eq:keylength without the licence is what
    # would overstate the key; the gate is what forbids it.
    assert key_length_permitted(TOY5_CONSTRAINED) is False


@pytest.mark.contract
@pytest.mark.oracle
def test_every_registry_entry_is_estimate_tier() -> None:
    """O-ASSURANCE-ESTIMATE: no entry claims the certified tier for itself.

    RE-DERIVED AT contract_version 0.4.0. Through 0.3.0 the reason was that C13
    was ``open`` and no code path could label anything ``certified``. C13 is now
    CLOSED and the label is reachable, so that reason is spent -- but the
    conclusion is not, and its replacement is stronger: a result is labelled
    ``certified`` only by the runtime checks of contract Section 4.18, and
    reading an oracle table is none of them (Remark rem:cert-interface;
    spec/architecture.md 2.5). Every entry's ``assurance`` is therefore
    still ``estimate``.

    Exactly ONE entry names ``certified`` as the value it PINS --
    ``O-ASSURANCE-CERTIFIED-GATE``, whose whole subject is when the label may be
    emitted -- and naming it is not claiming it: that entry's own ``assurance``
    is ``estimate`` like every other. The exception is enumerated by ID here so
    a second one is a defect this test catches.

    REWRITTEN AT contract_version 0.5.0, and the rewrite is what the mark
    requires rather than a tidy-up. ``O-ASSURANCE-CERTIFIED-GATE`` is
    ``superseded`` in ``SUPERSEDED_BY_0_5_0``: its subject is the BICONDITIONAL
    "certified EXACTLY WHEN the requested assurance was certified and all four
    check groups of Section 4.18 passed", and Theorem ``thm:optol`` (iii)
    falsifies it -- on the tolerance branch the four groups may all pass and the
    label is forced OFF anyway. What this test still asserts of that entry is
    only what remains true of it: its own evidential tier, and that it is the
    unique entry naming the label as a value. Its REPLACEMENT for the
    biconditional is ``O-OPTOL-ASSURANCE-FORCED-ESTIMATE``, asserted in
    ``tests/golden/test_operator_tolerance_against_registry.py``, and the mark
    is read here rather than recited so that retiring it would break this test.
    """
    entry = oracle("O-ASSURANCE-ESTIMATE")
    assert entry.claims == ("C13",)
    assert entry.value == "estimate"
    assert ASSURANCE == "estimate"
    for record in ORACLES:
        assert record.assurance == "estimate", record.oracle_id
    naming_certified = {
        record.oracle_id for record in ORACLES if record.value == "certified"
    }
    assert naming_certified == {"O-ASSURANCE-CERTIFIED-GATE"}
    gate = oracle("O-ASSURANCE-CERTIFIED-GATE")
    assert gate.kind == "fail-closed"
    assert gate.assurance == "estimate"
    # THE MARK, read from the registry: the biconditional this entry states is
    # superseded at 0.5.0, and its replacement forces the label off on a branch
    # where every check passes. Nothing below asserts the "exactly when".
    assert is_superseded("O-ASSURANCE-CERTIFIED-GATE")
    assert oracle("O-OPTOL-ASSURANCE-FORCED-ESTIMATE").assurance == "estimate"
    # And no entry silently promotes itself by naming a different tier.
    assert {record.assurance for record in ORACLES} == {"estimate"}


@pytest.mark.contract
@pytest.mark.oracle
def test_the_mechanical_half_of_the_gate_degenerates() -> None:
    """O-CGATE-DEGENERATE: Remark rem:cgate, and the G3 (f) instruction."""
    entry = oracle("O-CGATE-DEGENERATE")
    assert entry.claims == ("C14", "C17")
    assert entry.kind == "fail-closed"

    # Trusted mode with d_A >= 2: part (i) is a GENUINE restriction and TOY-7
    # fails it -- Theta_1 = diag(1, 1/2) is no multiple of tau_A = I/2.
    assert constraint_gate_part_i_is_vacuous(TOY7_NON_HOMOGENEOUS) is False
    assert constraint_gate_part_i(TOY7_NON_HOMOGENEOUS) is False

    # d_A = 1: the toys declare the homogeneous form (c_1 = 1/2), so part (i)
    # passes -- degenerately, a pass being evidence of nothing.
    for toy in (TOY5_CONSTRAINED, TOY6_REMOVABLE):
        assert toy.alice_dim == 1
        assert toy.constraint_list[0].homogeneous_scalar == 0.5
        assert constraint_gate_part_i_is_vacuous(toy) is True
        assert constraint_gate_part_i(toy) is True
        # THE SAME ENTRY IN THE GENERAL FORM, Theta_1 = [1/2], FAILS part (i):
        # a type check at every d_A (O-CGATE-DEGENERATE as re-frozen, the
        # owner's reading of def:homog).
        general = replace(
            toy,
            constraint_list=tuple(
                replace(entry, homogeneous_scalar=None)
                for entry in toy.constraint_list
            ),
        )
        assert constraint_gate_part_i(general) is False
        assert key_length_permitted(general) is False

    # Untrusted mode: vacuously true for the other reason -- a type check.
    assert source_mode(TOY5_CONSTRAINED_UNTRUSTED) == "untrusted"
    assert constraint_gate_part_i_is_vacuous(TOY5_CONSTRAINED_UNTRUSTED) is True
    assert constraint_gate_part_i(TOY5_CONSTRAINED_UNTRUSTED) is True

    # ... and in EVERY vacuous case the gate still hard-fails on the missing
    # attestation. A passing part (i) is evidence of nothing.
    for toy in (TOY5_CONSTRAINED, TOY6_REMOVABLE, TOY5_CONSTRAINED_UNTRUSTED):
        assert toy.attack_set_license is None
        assert key_length_permitted(toy) is False


@pytest.mark.contract
@pytest.mark.oracle
def test_the_source_replacement_licence_gate() -> None:
    """O-SOURCE-LICENSE-GATE: Section 4.19's second fail-closed discipline."""
    entry = oracle("O-SOURCE-LICENSE-GATE")
    assert entry.claims == ("C3", "C14")
    assert entry.kind == "fail-closed"

    # d_A >= 2 with a declared tau_A and no licence: HARD FAIL, before any
    # constraint question is even reached.
    assert TOY7_NON_HOMOGENEOUS.alice_dim == 2
    assert TOY7_NON_HOMOGENEOUS.source_replacement_license is None
    assert source_replacement_gate(TOY7_NON_HOMOGENEOUS) is False
    assert key_length_permitted(TOY7_NON_HOMOGENEOUS) is False

    # With the licence supplied it clears A-SRC and fails on part (i) alone --
    # the two failures are independent and neither masks the other.
    from dataclasses import replace

    with_licence = replace(
        TOY7_NON_HOMOGENEOUS,
        source_replacement_license={"certificate": "supplied by proof-reductions"},
    )
    assert source_replacement_gate(with_licence) is True
    assert constraint_gate_part_i(with_licence) is False
    assert key_length_permitted(with_licence) is False

    # d_A >= 2 with the licence present: allowed.
    for toy in (TOY8_TRUSTED_MARGINAL, TOY9_SINGULAR_MARGINAL):
        assert toy.source_replacement_license is not None
        assert source_replacement_gate(toy) is True
        assert key_length_permitted(toy) is True

    # d_A = 1: the licence is VACUOUS and must not be demanded. None of the
    # frozen d_A = 1 toys carries one, and all of them clear the gate.
    for toy in ALL_TOYS_0_3_0:
        if toy.alice_dim == 1 and source_mode(toy) == "trusted":
            assert toy.source_replacement_license is None, toy.toy_id
            assert source_replacement_gate(toy) is True, toy.toy_id

    # Untrusted mode: A-SRC is NOT ASSERTED, so there is nothing to demand.
    for toy in (TOY8_UNTRUSTED, TOY10_EMBEDDED):
        assert source_mode(toy) == "untrusted"
        assert toy.source_replacement_license is None
        assert source_replacement_gate(toy) is True


@pytest.mark.contract
def test_no_toy_declares_a_certified_assurance_or_a_draft_spec_version() -> None:
    """Contract Section 2.5: no artifact may claim a draft contract version."""
    from dummy_bundles import SPEC_VERSION

    assert SPEC_VERSION == "meat-core@1.28.0"
    assert "-draft" not in SPEC_VERSION
    assert ALL_TOYS  # the serializable subset is unchanged at 0.3.0
    for toy in ALL_TOYS_0_3_0:
        assert "certified" not in toy.summary.lower()
