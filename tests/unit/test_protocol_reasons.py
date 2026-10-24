"""The ``protocol-compiler`` machine vocabulary: total, unique, and no wider.

The two refusal strings ``contract.tex`` 0.1.3 names verbatim are the
contract's; every other spelling in
:mod:`certiqs_key.protocol_compiler.reasons` is this module's, under the one rule its
docstring states. What these tests hold fixed is the SHAPE of the vocabulary --
that it covers every check the contract obliges a refusal to name, that no two
codes collide, that no code exists for something the contract says is not
decided, and that the three-valued gate vocabulary has exactly three values.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from certiqs_key.protocol_compiler import (
    ASSUMPTION_MACHINE_KEYS,
    CHAIN_REFUSAL_REASONS,
    CHECK_IDS,
    CHECK_REFUSAL_REASONS,
    INHERITED_NEVER_VERIFIED_KEYS,
    NEVER_VERIFIED,
    REFUSAL_REASONS_VERBATIM,
    AssumptionId,
    ConditionOutcome,
    GateVerdict,
    Refusal,
    RefusalReason,
)

pytestmark = pytest.mark.contract


def test_the_seven_verbatim_strings_are_the_contracts_own_spelling() -> None:
    """TWO AT 0.1.4, SEVEN AT 0.3.0, and the two are not withdrawn.

    Section 2.3 (``refusal``) names the five the exact number model adds, in
    the order the contract lists them: "the reasons this contract fixes by
    name, beyond those already named at their sites:
    ``sector_map_mismatch``; ``bob_povm_summation_rounds``,
    ``alice_povm_summation_rounds`` and ``alice_marginal_trace_rounds`` for a
    failure of condition (S) on the respective family;
    ``emitted_value_not_representable`` where the compiler's own exact
    construction of a choice-weighted element does not land on a binary64
    number; ``no_feasibility_witness``; and ``fixed_fraction_requested``."
    """
    spellings = [str(reason) for reason in REFUSAL_REASONS_VERBATIM]
    assert spellings[:2] == ["fixed_fraction_requested", "no_feasibility_witness"]
    assert spellings == [
        "fixed_fraction_requested",
        "no_feasibility_witness",
        "sector_map_mismatch",
        "alice_marginal_trace_rounds",
        "alice_povm_summation_rounds",
        "bob_povm_summation_rounds",
        "emitted_value_not_representable",
    ]


def test_every_reason_string_is_unique() -> None:
    values = [str(reason) for reason in RefusalReason]
    assert len(values) == len(set(values))


def test_the_check_map_is_total_over_v1_to_v8() -> None:
    assert tuple(CHECK_REFUSAL_REASONS) == CHECK_IDS
    assert len(CHECK_REFUSAL_REASONS) == 8


def test_v7_carries_the_contracts_own_reason_and_no_invented_one() -> None:
    """Theorem thm:feasibility (ii) attaches ``no_feasibility_witness`` to V7's refusal.

    So there are SEVEN invented ``V``-spellings and not eight; a
    ``check_v7_failed`` beside the verbatim string would be two names for one
    refusal.
    """
    assert CHECK_REFUSAL_REASONS["V7"] is RefusalReason.NO_FEASIBILITY_WITNESS
    assert not any(str(reason) == "check_v7_failed" for reason in RefusalReason)
    invented_v_codes = [
        str(reason) for reason in RefusalReason if str(reason).startswith("check_v")
    ]
    assert len(invented_v_codes) == 7


def test_the_chain_map_covers_the_nine_decided_conditions_and_not_x1() -> None:
    """Theorem thm:chain-consumption (i): (X1) is NOT DECIDED, so no refusal may name it."""  # noqa: E501
    assert tuple(CHAIN_REFUSAL_REASONS) == (
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "S1",
        "S2",
        "S3",
        "S4",
    )
    assert "X1" not in CHAIN_REFUSAL_REASONS
    assert not any("x1" in str(reason) for reason in RefusalReason)


def test_no_reason_exists_for_sr3() -> None:
    """Theorem thm:certificate-sufficiency (i): (SR3) is decided by no function of the emitted data."""  # noqa: E501
    assert not any(str(reason).endswith("sr3_failed") for reason in RefusalReason)
    # THE TWO CHECKABLE CONDITIONS KEEP A REASON EACH AND THE NAMES ARE
    # THE TRANSMITTER'S: the five certificate conditions are
    # transmitter/def:srcert's and that module's interface spells all five,
    # so gate (G2) reuses them rather than spelling a second set.
    assert RefusalReason.CERTIFICATE_MARGINAL_IDENTITY_FAILS
    assert RefusalReason.CERTIFICATE_SIGNAL_IDENTITY_FAILS


def test_the_gate_vocabulary_has_exactly_three_values_with_the_space() -> None:
    assert [str(verdict) for verdict in GateVerdict] == [
        "passed",
        "failed",
        "passed vacuously",
    ]


def test_the_condition_outcome_vocabulary_has_exactly_four_values() -> None:
    assert [str(outcome) for outcome in ConditionOutcome] == [
        "holds",
        "fails",
        "vacuous",
        "not checked",
    ]
    assert ConditionOutcome.NOT_CHECKED is not ConditionOutcome.HOLDS


def test_a_refusal_is_a_record_and_not_an_exception() -> None:
    """Section 2.2 types ``refusal`` as a RECORD; the two must stay apart."""
    refusal = Refusal(reason=RefusalReason.CHECK_V3_FAILED, detail="a defect")
    assert not isinstance(refusal, BaseException)
    assert refusal.as_machine_record() == {
        "reason": "check_v3_failed",
        "detail": "a defect",
    }
    with pytest.raises(TypeError):
        raise refusal  # type: ignore[misc]


def test_the_assumption_ledger_s_own_rows_and_the_ids_owned_elsewhere() -> None:
    """SEVEN OWN IDS, AND FOUR ASSUMPTIONS ARE ELSEWHERE.

    SHORT IDS AND MACHINE KEYS ARE REPOSITORY-WIDE, so an
    assumption that another module already owns is ASSUMED FROM THERE and not
    restated: A-SEQ, A-ENS and A-SRC are the transmitter's, and A-RECV is
    reductions'.

    A-RHOM'S MACHINE KEY IS ``round_homogeneity_declaration``: ``receiver`` owns
    ``round_homogeneity`` for its A-ROUND, and ``reductions`` owns
    ``round_homogeneity_squashing``.

    THERE IS NO A-BLOCK ROW: the restriction to sector-block-diagonal states is
    the remark ``rem:block-restriction`` (meat-core/thm:reduction, step 1,
    proves it), so there is no key ``block_diagonal_feasible_set`` and no
    ``CONSUMER_OBLIGATIONS``.

    A-SPEC's decided conditions are ``def:well-formed-spec`` and its key is
    ``specification_describes_apparatus``. A-ALICE-MEAS's scope is wherever no
    source-replacement certificate is demanded, ``d_A = 1`` included, and its
    key is ``alice_measurement_as_declared``. There is no A-PRESENT: the exact
    admissibility of the physical family is def:well-formed-spec (iv) and
    req:physical-family-decision, with no key ``presented_receiver_family``.
    """
    assert len(AssumptionId) == 7
    assert len(ASSUMPTION_MACHINE_KEYS) == 7
    assert set(ASSUMPTION_MACHINE_KEYS) == set(AssumptionId)
    assert len(set(ASSUMPTION_MACHINE_KEYS.values())) == 7
    assert ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SPEC] == (
        "specification_describes_apparatus"
    )
    assert "presented_receiver_family" not in ASSUMPTION_MACHINE_KEYS.values()
    assert ASSUMPTION_MACHINE_KEYS[AssumptionId.A_ALICE_MEAS] == (
        "alice_measurement_as_declared"
    )
    assert ASSUMPTION_MACHINE_KEYS[AssumptionId.A_RHOM] == (
        "round_homogeneity_declaration"
    )
    # THE LEDGER'S OWN ORDER, which is the interface's `own_rows` order and not
    # alphabetical: A-IDEAL follows A-ATK, and A-ALICE-MEAS follows
    # A-SPEC.
    assert tuple(AssumptionId)[:2] == (
        AssumptionId.A_SPEC,
        AssumptionId.A_ALICE_MEAS,
    )
    assert tuple(AssumptionId)[-3:] == (
        AssumptionId.A_LINK,
        AssumptionId.A_ATK,
        AssumptionId.A_IDEAL,
    )
    # THE IDS OWNED ELSEWHERE OR ABSENT ARE NOT MEMBERS OF THIS ENUM: a second
    # member would be a second id for one assumption.
    for absent in ("A-SEQ", "A-ENS", "A-RET", "A-RECV", "A-BLOCK", "A-PRESENT"):
        with pytest.raises(ValueError, match="not a valid AssumptionId"):
            AssumptionId(absent)
    # SEVEN OWN, in the ledger's order: A-SPEC, A-ALICE-MEAS, A-RHOM, A-COIN
    # and A-IDEAL carry `verification: never` beside A-LINK and A-ATK
    # (spec/claim-format.md section 3.2).
    assert NEVER_VERIFIED == (
        AssumptionId.A_SPEC,
        AssumptionId.A_ALICE_MEAS,
        AssumptionId.A_RHOM,
        AssumptionId.A_COIN,
        AssumptionId.A_LINK,
        AssumptionId.A_ATK,
        AssumptionId.A_IDEAL,
    )
    # The INHERITED obligations nothing here may decide are named by their
    # machine keys, not as members of this enum, because this module does not
    # own them. FOUR, every inherited
    # row, in the order of INHERITED_KEYS -- the transmitter's A-SEQ, A-ENS
    # and A-SRC and the decoy submodule's A-WCP, each carrying its owner's
    # `never`. Reductions' A-RECV is no row of this module on any route.
    assert INHERITED_NEVER_VERIFIED_KEYS == (
        "sequential_round_model",
        "source_ensemble",
        "source_replacement_license",
        "wcp_source_model",
    )
    assert "block_diagonal_feasible_set" not in ASSUMPTION_MACHINE_KEYS.values()


def test_unconstructed_reasons_are_g3_or_transmitter_owned() -> None:
    """``def:gate-outcome-table`` gives (G3) an EMISSION and not a refusal.

    A (G3) failure is rows
    5 and 6 -- "emission with KLE = false" -- so ``resolve_gates`` records the
    verdict on the report and constructs no refusal, and
    ``gate_g3a_failed`` / ``gate_g3b_failed`` are declared and never built.
    THE TWO NAMES ARE KEPT, for the reason written at the members: they are the
    machine spellings of the gate IDENTITIES, the vocabulary a consumer reads a
    gate report with, and no interface row tables a competing spelling for them
    -- unlike the nine chain spellings, which the interface does table.

    The six source-admission names are constructed by the transmitter and
    converted by value at this boundary. Apart from that explicit supplier
    partition, a third declared-and-unreachable compiler member would be a defect.
    Construction is read off the SOURCE, by the same convention
    ``tests/oracles/test_protocol_compiler_registry_interface.py`` uses: a
    member is constructed where ``RefusalReason.<NAME>`` is written.
    """
    package = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "certiqs_key"
        / "protocol_compiler"
    )
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package.glob("*.py"))
    )
    source_admission = {
        "SOURCE_LINK_KIND_NOT_ADMITTED",
        "LINK_KIND_DEFERRED",
        "SOURCE_LINK_ENTRY_PRESENT",
        "SOURCE_LINK_FAMILY_EXCLUDES_ITS_DESCRIPTOR",
        "SOURCE_LINK_NOT_IN_REGISTRY",
        "SOURCE_LINK_ASSUMPTION_NOT_IN_LEDGER",
        "SOURCE_SEGMENT_NOT_FROM_ADMITTING_MODULE",
    }
    unconstructed = {
        member.name
        for member in RefusalReason
        if f"RefusalReason.{member.name}" not in source
    }
    # Source admission is decided by transmitter and crosses through
    # ``refusal_from_transmitter`` by value, so no compiler-owned static token
    # should be invented for those supplier checks.
    assert unconstructed - source_admission == {
        "GATE_G3A_FAILED",
        "GATE_G3B_FAILED",
    }
    assert unconstructed <= source_admission | {
        "GATE_G3A_FAILED",
        "GATE_G3B_FAILED",
    }
