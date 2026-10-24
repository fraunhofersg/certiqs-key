"""The refusal rules as a key vocabulary, at the registry-0.3.0 amendment.

Golden replay of ``REFUSAL_REASONS_VERBATIM_0_3_0``,
``REFUSAL_REASONS_ADDED_AT_0_3_0``, ``TIER_FALLBACK_REASON_VERBATIM``,
``REASON_VOCABULARY_0_3_0``, ``REASON_EMITS_ARTIFACT_0_3_0``,
``REASON_VOCABULARY_RECEIVER_0_1_2``, ``RETIRED_FROM_THE_CODE_RECEIVER_0_1_2``,
``REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0``, ``CONVENTION_KEYS_0_3_0`` and
``MATHEMATICAL_SPEC_VERSION_0_3_0`` (oracle entry ``O-RP-REASONS``).

WHAT THE REFUSAL TABLE IS FOR, in the words the frozen registry records
(tests/oracles/registry_receiver_povm.py; a registry version is the
contract version the registry froze): the rules are gathered
together with the reason string they emit "because AN IMPLEMENTER BINDS THE
STRING, NOT THE PROSE". EIGHT strings are contract text at registry 0.3.0 --
the five of registry 0.2.0 unchanged and three the exact window adds -- and a
ninth is named beside them and is a TIER FALLBACK, named "only so the two kinds
of machine-readable reason are not confused". ``interface.yaml`` ``refusals``
carries the same eight and the dropped ninth (``tier_fallback``).

THE ONE INVARIANT THIS FILE IS FOR: an implementation that emitted a further
string under one of these conditions, or REUSED ONE OF THE NINE for a condition
the table does not name, would be reporting something the contract does not
state. Both halves are asserted -- the eight are spelled exactly, and no other
condition in the module emits one of the nine.

THE NINTH STRING IS NOT THE MODULE'S. The tier fallback has no spelling in
``RefusalReason``: the ``certified`` rung that reached
``receiver_grams_not_enclosed`` is not part of the design (PRINCIPLES.md
section 10). The frozen nine are NOT rewritten for it -- they record
the frozen contract -- and what the code is compared against is
``REASON_VOCABULARY_RECEIVER_0_1_2``, with
``RETIRED_FROM_THE_CODE_RECEIVER_0_1_2`` naming what the code does not spell.

THE REGISTRY-0.2.0 OBJECTS ARE SUPERSEDED, ONE BY ONE, and the
mark is a recorded act: ``REFUSAL_REASONS_VERBATIM_0_2_0``,
``REASON_VOCABULARY_0_2_0``, ``REASON_EMITS_ARTIFACT``,
``REFUSALS_NAMED_WITHOUT_A_SPELLING`` and ``MATHEMATICAL_SPEC_VERSION_0_2_0``
are all marked in ``SUPERSEDED_BY_0_3_0`` -- each as an ENUMERATION the
amendment widens, not as a value it changes -- and the last test below asserts
that the marks are still there.

The per-condition replays live in ``test_receiver_povm_refusals_against_registry
.py``; what is checked here is the VOCABULARY, its two kinds, and the artifact
version the amendment binds.
"""

from __future__ import annotations

import pytest
from registry_receiver_povm import (
    CONVENTION_KEYS_0_3_0,
    MATHEMATICAL_SPEC_VERSION_0_3_0,
    MATHEMATICAL_SPEC_VERSION_RECEIVER_0_1_2,
    REASON_EMITS_ARTIFACT_0_3_0,
    REASON_VOCABULARY_0_3_0,
    REASON_VOCABULARY_RECEIVER_0_1_2,
    REFUSAL_REASONS_ADDED_AT_0_3_0,
    REFUSAL_REASONS_VERBATIM_0_3_0,
    REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0,
    RETIRED_FROM_THE_CODE_RECEIVER_0_1_2,
    TIER_FALLBACK_REASON_VERBATIM,
    is_superseded_0_3_0,
    rp_oracle,
)

from certiqs_key.receiver import (
    MATHEMATICAL_SPEC_VERSION,
    OUTPUT_KEYS,
    REASON_VOCABULARY,
    Assurance,
    RefusalReason,
    resolve_assurance,
)
from certiqs_key.receiver.reasons import REFUSAL_REASONS_ADDED_AT_0_3_0 as ADDED
from certiqs_key.receiver.reasons import REFUSAL_REASONS_ADDED_AT_0_7_0

#: The delta the frozen 0.3.0 registry does not carry: receiver 0.7.0 spells
#: ONE further refusal after the eight, the efficiency normalization's
#: (detector-imperfections/req:efficiency-normalization).
ADDED_AT_0_7_0: tuple[str, ...] = ("efficiency_normalization_out_of_range",)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_eight_refusal_reasons_are_spelled_character_for_character() -> None:
    """The refusal table at registry 0.3.0, in its own row order."""
    assert rp_oracle("O-RP-REASONS").kind == "fail-closed"
    assert len(REFUSAL_REASONS_VERBATIM_0_3_0) == 8
    # THE MODULE'S EIGHT, in order: the whole of the module's vocabulary, the
    # tier fallback not being a `RefusalReason`.
    refusals = REASON_VOCABULARY
    assert (
        tuple(str(reason) for reason in refusals)
        == REFUSAL_REASONS_VERBATIM_0_3_0 + ADDED_AT_0_7_0
    )
    assert tuple(str(r) for r in REFUSAL_REASONS_ADDED_AT_0_7_0) == ADDED_AT_0_7_0
    # Each is a member of the enum under its own name, so a caller cannot
    # reach one by a near-miss spelling.
    for spelling in REFUSAL_REASONS_VERBATIM_0_3_0:
        assert RefusalReason(spelling) in refusals
    # THE DELTA IS THREE ADDED AND NONE REMOVED (registry 0.3.0; the
    # interface's `refusals.table` rows with `new_at: "0.3.0"`).
    assert tuple(str(reason) for reason in ADDED) == REFUSAL_REASONS_ADDED_AT_0_3_0
    assert set(ADDED) < set(refusals)
    assert len(REFUSAL_REASONS_ADDED_AT_0_3_0) == 3


@pytest.mark.contract
@pytest.mark.oracle
def test_the_tier_fallback_string_is_spelled_by_no_path() -> None:
    """The tier fallback; Theorem thm:exact-and-evaluated (iii) and (v).

    THE OPT-IN ROUTE DOES NOT SOFTEN THE TIER RULE. Theorem
    thm:exact-and-evaluated (v): item (iii) COVERS BOTH evaluations -- no path
    in this module produces a label stronger than the floating-point label, SO
    NO ARTIFACT RESTING ON Assumption ass:eig CAN CLAIM MORE.

    The code does not spell the ninth string at all. The frozen side is
    untouched; the nine and their emits-an-artifact flags record the
    frozen contract, and the code is read against
    ``REASON_VOCABULARY_RECEIVER_0_1_2`` and
    ``RETIRED_FROM_THE_CODE_RECEIVER_0_1_2``.
    """
    emits = dict(REASON_EMITS_ARTIFACT_0_3_0)
    assert len(emits) == 9
    assert emits[TIER_FALLBACK_REASON_VERBATIM] is True
    # THE ONE OF THE NINE THAT EMITS AN ARTIFACT IS THE ONE THE CODE LACKS: it is not a
    # member of the enum under any name, so no path
    # can construct it and no near-miss spelling reaches it.
    assert RETIRED_FROM_THE_CODE_RECEIVER_0_1_2 == (TIER_FALLBACK_REASON_VERBATIM,)
    spelled = {str(reason) for reason in RefusalReason}
    for retired in RETIRED_FROM_THE_CODE_RECEIVER_0_1_2:
        assert retired not in spelled, retired
        with pytest.raises(ValueError, match="not a valid RefusalReason"):
            RefusalReason(retired)
    # Every string the module does spell of the contract's own refuses with NO
    # artifact.
    assert len(REASON_VOCABULARY) == 8 + len(ADDED_AT_0_7_0)
    assert all(
        emits[str(reason)] is False
        for reason in REASON_VOCABULARY
        if str(reason) not in ADDED_AT_0_7_0
    )
    # THE FALLBACK IS UNREACHABLE: the
    # `certified` request that would trigger it names a tier PRINCIPLES.md
    # section 10 does not have, so `Assurance` has no such member. What holds is the
    # rule the vocabulary row states -- every request is answered `estimate`,
    # with no fallback reason, on every rung the ladder still has.
    for tier in Assurance:
        assert resolve_assurance(tier) == (Assurance.ESTIMATE, None)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_module_vocabulary_is_the_eight_and_nothing_else_reuses_one() -> None:
    """The refusal rules: no further string, and no re-use of one of the nine.

    The module's vocabulary is compared against
    ``REASON_VOCABULARY_RECEIVER_0_1_2``, the eight the code carries. The
    frozen nine stay the reference for the closing half, so a module spelling
    that collided with the dropped string would still fail here.
    """
    assert (
        tuple(str(r) for r in REASON_VOCABULARY)
        == REASON_VOCABULARY_RECEIVER_0_1_2 + ADDED_AT_0_7_0
    )
    assert len(REASON_VOCABULARY_RECEIVER_0_1_2) == 8
    assert len(set(REASON_VOCABULARY_0_3_0)) == 9
    # THE CLOSING HALF OF THE INVARIANT: every OTHER member of the enum is this
    # module's own spelling, and none collides with a contract key.
    ours = [reason for reason in RefusalReason if reason not in set(REASON_VOCABULARY)]
    assert ours, "the module names conditions the contract leaves unspelled"
    for reason in ours:
        assert str(reason) not in REASON_VOCABULARY_0_3_0
    # THE ONE REFUSAL THE CONTRACT DECLINES TO SPELL stays in `ours`:
    # Req. req:tolerance-tests states that a failure of Def. def:tolmap (iv) IS
    # a refusal, and its lead-in adds no string: "fixing a contract-verbatim key
    # here would settle an interface detail that no claim of this contract
    # consumes".
    assert RefusalReason.BOUND_DATA_NOT_ADMISSIBLE in ours
    # And the six contract keys are used for exactly one condition each: no two
    # enum members share a spelling.
    spellings = [str(reason) for reason in RefusalReason]
    assert len(spellings) == len(set(spellings))


@pytest.mark.contract
@pytest.mark.oracle
def test_the_seven_unspelled_conditions_are_recorded_without_a_key() -> None:
    """The unspelled refusals: the identity is contract, the spelling is code's.

    SIX AT REGISTRY 0.2.0 AND SEVEN AT REGISTRY 0.3.0. The seventh was not in
    the registry-0.2.0 enumeration: Req. req:tolerance-tests states the refusal
    for Def. def:tolmap (iv) and declines its string (``interface.yaml``
    ``refusals.named_without_a_spelling``).
    """
    assert len(REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0) == 7
    for condition, site in REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0:
        assert condition.strip() and site.strip()
        # None of the seven is given a contract key by the registry, and none of
        # this module's keys for them is in the contract's vocabulary.
        assert condition not in REASON_VOCABULARY_0_3_0
    assert "def:tolmap (iv)" in REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0[-1][1]


@pytest.mark.contract
@pytest.mark.oracle
def test_the_artifact_binds_the_accepted_amendment_version() -> None:
    """The artifact-binding convention and the `mathematical_spec_version` output."""
    from certiqs_key.receiver.artifact import ACCEPTED_CONTRACT_VERSION

    # The accepted contract is an accepted version of
    # spec/modules/receiver/module.yaml, the one the code implements, and the
    # emitted pin is `receiver@` followed by it; both
    # literals are written by hand when the pin moves, never regenerated from
    # the code under test. The frozen registry's two constants are NOT
    # rewritten: MATHEMATICAL_SPEC_VERSION_0_3_0 records what the 0.3.0 freeze
    # bound and MATHEMATICAL_SPEC_VERSION_RECEIVER_0_1_2 what the 0.1.2 bound;
    # the code's pin is neither.
    assert ACCEPTED_CONTRACT_VERSION == "0.9.0"
    assert MATHEMATICAL_SPEC_VERSION == "receiver@0.9.0"
    assert MATHEMATICAL_SPEC_VERSION_RECEIVER_0_1_2 == "receiver@0.1.2"
    assert MATHEMATICAL_SPEC_VERSION != MATHEMATICAL_SPEC_VERSION_RECEIVER_0_1_2
    assert MATHEMATICAL_SPEC_VERSION_0_3_0 == "receiver-povm@0.3.0"
    assert MATHEMATICAL_SPEC_VERSION != MATHEMATICAL_SPEC_VERSION_0_3_0
    # "an artifact may not claim a draft version", and it may not claim a
    # version of the frozen module id either.
    assert "draft" not in MATHEMATICAL_SPEC_VERSION
    assert MATHEMATICAL_SPEC_VERSION not in (
        "receiver-povm@0.1.3",
        "receiver-povm@0.2.0",
        "receiver-povm@0.3.0",
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_seventeen_conventions_and_the_fifteen_output_keys() -> None:
    """The registry-0.3.0 conventions keep their bullets, and the outputs gain no key.

    ``delta_from_0_2_0``: the seventeen convention bullets are THE SAME
    SEVENTEEN, of which exactly two change text, and the fifteen output keys are
    the same fifteen, of which three change what they CONTAIN. The input surface
    is where the registry-0.3.0 amendment adds -- one key, ``exact_window``.
    """
    assert len(CONVENTION_KEYS_0_3_0) == 17
    assert CONVENTION_KEYS_0_3_0.index("numerical_tolerance_assignment") == (
        CONVENTION_KEYS_0_3_0.index("numerics") + 1
    )
    assert CONVENTION_KEYS_0_3_0.index("fail_closed") == (
        CONVENTION_KEYS_0_3_0.index("numerical_tolerance_assignment") + 1
    )
    assert len(OUTPUT_KEYS) == 15
    assert "dark_count_channel" in OUTPUT_KEYS
    assert "validation_results" in OUTPUT_KEYS
    assert "bound_quantifier_domain" in OUTPUT_KEYS


@pytest.mark.contract
def test_the_superseded_vocabulary_objects_carry_their_mark() -> None:
    """The supersession is a recorded mark, not a silent deletion.

    Every registry-0.2.0 enumeration is marked in
    ``SUPERSEDED_BY_0_3_0`` -- as an ENUMERATION the amendment widens, never as
    a value it changes -- and is not asserted above. This test fails if a
    mark is removed from the freeze without this file being revisited.
    """
    for name in (
        "REFUSAL_REASONS_VERBATIM_0_2_0",
        "REASON_VOCABULARY_0_2_0",
        "REASON_EMITS_ARTIFACT",
        "REFUSALS_NAMED_WITHOUT_A_SPELLING",
        "MATHEMATICAL_SPEC_VERSION_0_2_0",
    ):
        assert is_superseded_0_3_0(name), name
    # The tier-fallback string is NOT marked: it is byte-identical across all
    # three versions of the frozen contract, and the registry records
    # that. Its absence from THE CODE is a different fact, and it
    # is recorded by RETIRED_FROM_THE_CODE_RECEIVER_0_1_2, not by a
    # superseded mark.
    assert not is_superseded_0_3_0("TIER_FALLBACK_REASON_VERBATIM")
    assert RETIRED_FROM_THE_CODE_RECEIVER_0_1_2 == (TIER_FALLBACK_REASON_VERBATIM,)
