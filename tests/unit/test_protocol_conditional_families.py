"""``def:weighted``'s decision on each conditional family ``{N_{u|t}}_u``.

WHAT THIS FILE IS THE TEST HALF OF. The interface row
``inputs.public_choices`` calls the exact admissibility of each conditional
family DECIDED; ``def:weighted`` states the decision, ``rem:condfamily`` says which way
the implication travels and ``ex:condfamily`` is the witness that it cannot be left to
the emitted family's own five conditions. This file holds the code to those three
claims:

1. ``ex:condfamily`` AS A TEST THAT REFUSES -- the hand-built numbers, with
   both halves asserted: the emitted family passes check V1's map comparison
   and check V3's (H), (P), (C) and (S), and the compilation REFUSES with
   ``conditional_family_not_admissible`` naming (C) at ``t_0``;
2. ONE TEST PER PREDICATE -- (T), (H), (P), (C) and (S) -- each isolated so
   that the refusal names that predicate and the index the ``gate_report`` row
   asks a failed decision for;
3. THE ORDER RULE of ``def:weighted``'s "In which order (S) is read on a
   conditional family", on a presentation whose record listing differs from the
   arriving order, where the two orders give DIFFERENT verdicts;
4. that both shipped instances still compile, with the decision recorded and
   holding for every presentation they declare.

NO REGISTRY IMPORT. The frozen registry's ``EmissionRepresentabilityCase``
carries a ``conditional_family_exactly_admissible`` field, and the golden suite
reads it; what is asserted here are properties of the decision itself, which is
the implementation's side of the same question.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import pytest
from protocol_blocks import source_part

from certiqs_key.domain.chain import (
    ChainLink,
    LinkStage,
    LinkStatus,
    ReductionChain,
    Side,
    SystemDescriptor,
)
from certiqs_key.foundations.blocks import (
    BlockKind,
    BlockOperator,
    Label,
    SectorStructure,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Matrix,
    identity,
    matrix,
    sum_in_declared_order,
)
from certiqs_key.protocol_compiler import (
    DirectPovm,
    Party,
    PovmPresentation,
    PredicateSource,
    ProtocolSpecification,
    PublicChoices,
    PublicPart,
    ReceiverPart,
    RefusalReason,
    Sifting,
    SpecConstraints,
    check_v1,
    check_v3,
    compile_specification,
    conditional_family_order,
    decide_conditional_families,
    decide_every_conditional_family,
    default_party_partition,
    identity_channel,
    is_povm,
    weighted_family,
)

pytestmark = pytest.mark.contract

HALF = F(1, 2)
ONE_SECTOR = SectorStructure(
    labels=("s0",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
)
Z0 = matrix(((1, 0), (0, 0)))
Z1 = matrix(((0, 0), (0, 1)))
V_ALPHABET: tuple[Label, ...] = ("v0", "v1")

#: ``ex:condfamily``'s two conditional families, each a ONE-ELEMENT family over
#: ``U_t = {u_0}``: ``diag(1/2, 3/2)`` and ``diag(3/2, 1/2)``. Every entry is an
#: integer multiple of ``2**-1`` and each weight is ``1/2``, so every product is
#: exactly binary64 and the representability decision passes.
EX_CONDFAMILY: dict[Label, dict[Label, Matrix]] = {
    "t0": {"u0": matrix(((HALF, 0), (0, F(3, 2))))},
    "t1": {"u0": matrix(((F(3, 2), 0), (0, HALF)))},
}

#: The same shape with each conditional family a POVM: the ONE-ELEMENT family
#: ``{1_A}``. The control, so that a refusal below is the decision's and not the
#: fixture's.
ADMISSIBLE_ONE_ELEMENT: dict[Label, dict[Label, Matrix]] = {
    "t0": {"u0": identity(2)},
    "t1": {"u0": identity(2)},
}

#: A three-element conditional family whose exact sum is the identity, whose
#: entries are all binary64, and whose declared-order sum ROUNDS at the second
#: addition in one order and NOWHERE in another. ``1 - 2**-53`` and ``2**-54``
#: are both binary64; ``(1 - 2**-53) + 2**-54 = 1 - 2**-54`` is not.
_BIG = F(1) - F(1, 2**53)
_SMALL = F(1, 2**54)
_ROUNDING: dict[Label, Matrix] = {
    "u0": matrix(((_BIG, 0), (0, HALF))),
    "u1": matrix(((_SMALL, 0), (0, F(1, 4)))),
    "u2": matrix(((_SMALL, 0), (0, F(1, 4)))),
}


def _alice_choices(
    conditional: dict[Label, dict[Label, Matrix]],
) -> PublicChoices:
    """Return a two-value Alice presentation over the given families."""
    return PublicChoices(
        party=Party.ALICE,
        choices=("t0", "t1"),
        weights={"t0": HALF, "t1": HALF},
        conditional_alphabets={
            choice: tuple(outcomes) for choice, outcomes in conditional.items()
        },
        conditional_elements=conditional,
    )


def _specification(
    choices: PublicChoices,
    receiver: PovmPresentation | None = None,
    target_order: tuple[Label, ...] | None = None,
) -> ProtocolSpecification:
    """Return a Band-A specification whose Alice family is ``choices``.

    UNTRUSTED SOURCE MODE AND AN EMPTY ``CList``, so that nothing between the
    specification boundary and the emission can refuse for a reason of its own:
    no certificate is supplied, so gate (G2) is not engaged, and check V7 takes
    its empty-list branch. What is left to refuse is the decision under test.

    ``receiver`` IS THE PHYSICAL PRESENTATION and defaults to the two-element
    direct family; where it is a :class:`PublicChoices` the emitted receiver
    alphabet is what the weighting produces and the Band-A link carries those
    same products as its target, which is what ``def:banda`` makes of a
    choice-weighted receiver family. ``target_order`` permutes the LAST LINK'S
    TARGET ALPHABET without touching the record, which is the one place a
    second order for a receiver presentation could arrive from.
    """
    x_alphabet = tuple(
        label for label in weighted_family(choices).alphabet
    )
    if receiver is None:
        receiver = DirectPovm(alphabet=V_ALPHABET, elements={"v0": Z0, "v1": Z1})
    if isinstance(receiver, DirectPovm):
        v_alphabet = receiver.alphabet
        bob_blocks = {
            label: BlockOperator.of(ONE_SECTOR, (receiver.elements[label],))
            for label in v_alphabet
        }
    else:
        weighted = weighted_family(receiver)
        v_alphabet = weighted.alphabet
        bob_blocks = {
            label: BlockOperator.of(ONE_SECTOR, (weighted.elements[label],))
            for label in v_alphabet
        }
    emitted_order = v_alphabet if target_order is None else target_order
    assert set(emitted_order) == set(v_alphabet)
    descriptor = SystemDescriptor(
        name="Q",
        dim=2,
        side=Side.RECEIVER,
        sectors=(("s0", 2),),
        sector_block_kind=BlockKind.PROOF_SECTOR,
    )
    chain = ReductionChain(
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment=LinkStage.RECEIVER,
                link_type="squashing (identity)",
                source_descriptor=descriptor,
                target_descriptor=descriptor,
                status=LinkStatus.EXACT,
                channel=identity_channel(2),
                transported_constraints=(),
                license_slot=None,
                target_alphabet=emitted_order,
                target_povm=bob_blocks,
            ),
        ),
        outcome_correspondence=dict(zip(v_alphabet, v_alphabet, strict=True)),
    )
    announcements = tuple(f"b_{label}" for label in v_alphabet)
    alice_announcements = tuple(f"a_{index}" for index, _ in enumerate(x_alphabet))
    classes = [(c_a, c_b) for c_a in alice_announcements for c_b in announcements]
    public = PublicPart(
        partition=default_party_partition(x_alphabet, v_alphabet),
        announce_alice=dict(zip(x_alphabet, alice_announcements, strict=True)),
        announce_bob=dict(zip(v_alphabet, announcements, strict=True)),
        alice_announcement_alphabet=alice_announcements,
        bob_announcement_alphabet=announcements,
        sifting=dict.fromkeys(classes, Sifting.PASS),
        key_rule={
            (readout, kappa): index % 2
            for index, readout in enumerate(x_alphabet)
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=("g",),
        accept_statistic=dict.fromkeys(classes, "g"),
    )
    return ProtocolSpecification(
        source=source_part(
            alphabet=x_alphabet,
            alice_dim=2,
            alice_povm=choices,
            transmitted_dim=2,
            signal_weights=dict.fromkeys(x_alphabet, F(1, len(x_alphabet))),
            signal_states=dict.fromkeys(x_alphabet, matrix(((HALF, 0), (0, HALF)))),
        ),
        receiver=ReceiverPart(physical_dim=2, physical_povm=receiver),
        public=public,
        sectors=ONE_SECTOR,
        chain=chain,
        constraints=SpecConstraints(),
    )


# ---------------------------------------------------------------------------
#  1. ex:condfamily, as a test that REFUSES
# ---------------------------------------------------------------------------


def test_ex_condfamily_passes_v1_and_v3_and_is_refused_all_the_same() -> None:
    """``ex:condfamily``: the emitted family is admissible and the presentation is not.

    "Let ``T_pub = {t_0, t_1}`` with ``q = (1/2, 1/2)``, one outcome ``u_0`` per
    choice, and the conditional families ``N_(u0|t0) = diag(1/2, 3/2)``,
    ``N_(u0|t1) = diag(3/2, 1/2)``. The emitted family is
    ``{diag(1/4, 3/4), diag(3/4, 1/4)}``, whose sum is the identity and whose
    members are Hermitian and positive semidefinite, so (H), (P), (C) and (S)
    all hold of it and CHECK V3 PASSES ... NEITHER CONDITIONAL FAMILY IS A
    POVM."

    BOTH HALVES ARE ASSERTED HERE, because the example's force is the
    conjunction: a test that only showed the refusal would not show that the
    refusal is UNREACHABLE from the emitted family, which is the whole reason
    the decision cannot be left to check V3. The control -- the same shape with
    ``{1_A}`` for each conditional family -- compiles, so what refuses below is
    the numbers and not the fixture.
    """
    choices = _alice_choices(EX_CONDFAMILY)
    emitted = weighted_family(choices)
    assert [emitted.elements[label] for label in emitted.alphabet] == [
        matrix(((F(1, 4), 0), (0, F(3, 4)))),
        matrix(((F(3, 4), 0), (0, F(1, 4)))),
    ]

    # THE EMITTED FAMILY IS EXACTLY ADMISSIBLE: (H), (P) and (C) through
    # is_povm, (S) on its own declared-order sum -- two binary64 additions per
    # entry, each exact -- and (T) and the rest through the checks themselves.
    assert is_povm(emitted.ordered(), 2)
    assert sum_in_declared_order(list(emitted.ordered())).rounds_nowhere

    control = compile_specification(
        _specification(_alice_choices(ADMISSIBLE_ONE_ELEMENT))
    )
    assert control.refusal is None
    assert control.declaration is not None
    exhibited = replace(control.declaration, alice_povm=dict(emitted.elements))
    assert check_v1(exhibited).passed, "(T) is V1's, and it passes on this family"
    assert check_v3(exhibited).passed, "V3 decides (H), (P), (C), (S) -- all four hold"

    # AND THE COMPILATION REFUSES, naming (C) at t_0 -- "the FIRST failure, the
    # decision stopping there".
    refused = compile_specification(_specification(choices))
    assert refused.refuses
    assert refused.declaration is None
    assert refused.refusal is not None
    assert (
        refused.refusal.reason is RefusalReason.CONDITIONAL_FAMILY_NOT_ADMISSIBLE
    )
    assert "N_(u|t0)" in refused.refusal.detail
    assert "(C)" in refused.refusal.detail or "completeness" in refused.refusal.detail
    assert str(Party.ALICE) in refused.refusal.detail
    # THE REFUSAL IS TAKEN BEFORE THE CHAIN STAGE RAN, which is fail-closed row
    # 1: no chain report exists beside it, exactly as for the pre-chain
    # representability refusal.
    assert refused.chain is None
    assert refused.key_length_eligible is None

    # AND THE DECISION STOPPED AT THE FIRST FAILURE: t_1's family is just as
    # inadmissible and is not decided at all.
    decision = decide_conditional_families(choices, 2)
    assert decision.refusal is not None
    failing = [entry for entry in decision.predicates if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].key == (
        PredicateSource.COMPILATION_MAP,
        "A:{N_(u|t0)}",
        None,
    )
    assert failing[0].predicate == "(C)"
    assert decision.predicates[-1] is failing[0]
    assert not any("t1" in str(entry.element) for entry in decision.predicates)


def test_the_two_conditional_families_of_ex_condfamily_are_not_povms() -> None:
    """The example's middle paragraph, of the numbers rather than of the record.

    "Their completeness sums are ``diag(1/2, 3/2)`` and ``diag(3/2, 1/2)``, each
    a one-term sum whose single addition ``0 + N_(u0|t)`` is exact, and neither
    is ``1_S``: condition (C) fails for both, of the declared numbers and
    through no rounding, while (T), (H), (P) and (S) hold of both."
    """
    for choice, family in EX_CONDFAMILY.items():
        element = family["u0"]
        verdict = sum_in_declared_order([element])
        assert verdict.rounds_nowhere, choice
        assert verdict.computed_total == element
        assert verdict.computed_total != identity(2)
        assert not is_povm((element,), 2)


# ---------------------------------------------------------------------------
#  2. One test per predicate
# ---------------------------------------------------------------------------


def test_t_is_decided_on_the_one_component_the_record_declares() -> None:
    """(T): the conditional families of one presentation carry ONE map.

    ``def:weighted`` reads (T) as the agreement "of the maps THE CONDITIONAL
    FAMILIES OF ONE PRESENTATION THEMSELVES CARRY". A ``public_choices`` record
    declares one dense array per outcome and no sector map, so the dimension is
    the one component of the four that has a declared subject -- and a
    presentation whose arrays have two shapes is refused under (T) rather than
    reaching the arithmetic with two shapes, which is the refusing reading of
    the three the implementation had to choose between
    (:func:`~certiqs_key.protocol_compiler.weights.decide_conditional_families`).
    """
    mixed = _alice_choices(
        {
            "t0": {"u0": identity(2)},
            "t1": {"u0": identity(3)},
        }
    )
    decision = decide_conditional_families(mixed, 2)
    assert decision.refusal is not None
    assert decision.refusal.reason is RefusalReason.CONDITIONAL_FAMILY_NOT_ADMISSIBLE
    assert "(T)" in decision.refusal.detail
    # ONE DECISION WAS TAKEN AND IT IS (T)'s: the presentation is not decided
    # family by family at all, the shapes not being comparable.
    assert len(decision.predicates) == 1
    assert decision.predicates[0].predicate == "(T)"
    assert decision.predicates[0].element == "A:{N_(u|t)}"
    assert decision.predicates[0].block is None
    # The index is the position of the first disagreeing operator in the
    # record's own listing, 1-based as every index this package computes is.
    assert decision.predicates[0].first_failure_index == 2


def test_completeness_is_compared_with_the_identity_on_the_declared_system() -> None:
    """(C)'s right-hand side is ``1_S`` and not the identity the arrays span.

    A presentation whose
    conditional families agree with one another but live on a space the
    specification does not declare passes (T) -- the maps the families carry DO
    agree -- and is a POVM on nothing the declaration is about. ``def:exact``
    (C) reads ``Sigma = 1_{Q_s}``, the identity on the DECLARED system, and
    ``def:weighted`` asks for "a POVM ON ``S``", so the comparison is against
    ``d_A`` here and against the physical receiver dimension on Bob's side.
    Reading it against the arrays' own dimension would admit this record.

    THE FAILURE IS NAMED (C) AND NOT (T), which is the reading the claims'
    order of predicates gives: (T) is the agreement of the maps the conditional
    families THEMSELVES carry -- the round-2 amendment removed the comparison
    against a map this module holds -- so widening it to reach the declared
    dimension would decide a comparison no claim states, while (C) already
    carries that comparison in its right-hand side.
    """
    elsewhere = _alice_choices(
        {"t0": {"u0": identity(3)}, "t1": {"u0": identity(3)}}
    )
    decision = decide_conditional_families(elsewhere, 2)
    assert decision.refusal is not None
    assert decision.refusal.reason is RefusalReason.CONDITIONAL_FAMILY_NOT_ADMISSIBLE
    failing = [entry for entry in decision.predicates if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].predicate == "(C)"
    assert failing[0].key == (
        PredicateSource.COMPILATION_MAP,
        "A:{N_(u|t0)}",
        None,
    )
    # (T), (H) and (P) were decided first and HELD, which is what makes this a
    # test of (C)'s right-hand side and not of a shape guard.
    assert [entry.predicate for entry in decision.predicates] == [
        "(T)",
        "(H)",
        "(P)",
        "(C)",
    ]
    assert all(entry.outcome for entry in decision.predicates[:3])
    assert "2-dimensional system" in decision.refusal.detail
    # AND THE SAME FAMILY IS ADMITTED WHERE THE DECLARED SYSTEM IS ITS OWN, so
    # the refusal is the comparison and not the arrays.
    assert decide_conditional_families(elsewhere, 3).admitted


def test_h_and_p_are_keyed_per_choice_value_and_carry_the_outcome_index() -> None:
    """(H) then (P), in that order, each naming the element index that failed."""
    not_hermitian = _alice_choices(
        {
            "t0": {"u0": identity(2)},
            "t1": {"u0": matrix(((1, 1), (0, 1)))},
        }
    )
    decision = decide_conditional_families(not_hermitian, 2)
    assert decision.refusal is not None
    assert "not Hermitian" in decision.refusal.detail
    failing = [entry for entry in decision.predicates if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].key == (
        PredicateSource.COMPILATION_MAP,
        "A:{N_(u|t1)}",
        None,
    )
    assert failing[0].predicate == "(H)"
    assert failing[0].first_failure_index == 1

    # (P) IS DECIDED AFTER (H) AND BEFORE (C), so a Hermitian family with a
    # negative eigenvalue is refused under (P) although its completeness sum is
    # wrong too: one failure is named, not a list.
    not_positive = _alice_choices(
        {
            "t0": {"u0": matrix(((2, 0), (0, -1)))},
            "t1": {"u0": identity(2)},
        }
    )
    decision = decide_conditional_families(not_positive, 2)
    assert decision.refusal is not None
    assert "not positive semidefinite" in decision.refusal.detail
    failing = [entry for entry in decision.predicates if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].predicate == "(P)"
    assert failing[0].key == (
        PredicateSource.COMPILATION_MAP,
        "A:{N_(u|t0)}",
        None,
    )


def test_the_per_predicate_decision_and_is_povm_cannot_disagree() -> None:
    """``is_povm`` is the aggregate reading of (H), (P) and (C) of one family.

    The two decide the same numbers and are written twice -- once as a boolean
    for a caller that wants the verdict, once per predicate because the refusal
    owes "the predicate, the block and the index of the first failure". This
    holds them together on four families, so that a change to either is a red.
    """
    families: tuple[tuple[Matrix, ...], ...] = (
        (Z0, Z1),
        (identity(2),),
        (matrix(((HALF, 0), (0, F(3, 2)))),),
        (matrix(((2, 0), (0, -1))), matrix(((-1, 0), (0, 2)))),
    )
    for family in families:
        outcomes = tuple(f"u{index}" for index, _ in enumerate(family))
        record = _alice_choices(
            {
                "t0": dict(zip(outcomes, family, strict=True)),
                "t1": {"u0": identity(2)},
            }
        )
        decision = decide_conditional_families(record, 2)
        t0_holds = not any(
            entry.element == "A:{N_(u|t0)}" and not entry.outcome
            for entry in decision.predicates
        )
        assert t0_holds == is_povm(family, 2), family


def test_s_on_a_conditional_family_is_decided_on_the_additions() -> None:
    """(S): a family whose (C) holds on the computed total and whose sum rounds.

    ``def:exact``: "(S) is on the ADDITIONS, not on the operands, so a family
    every one of whose entries is a binary64 number may still be refused". The
    three declared entries below are binary64 and their exact total is the
    identity; the SECOND addition ``(1 - 2**-53) + 2**-54`` is not, and the
    refusal carries that index under both names the ``gate_report`` row asks
    for.
    """
    record = _alice_choices({"t0": _ROUNDING, "t1": {"u0": identity(2)}})
    decision = decide_conditional_families(record, 2)
    assert decision.refusal is not None
    assert decision.refusal.reason is RefusalReason.CONDITIONAL_FAMILY_NOT_ADMISSIBLE
    assert "ROUNDS" in decision.refusal.detail
    failing = [entry for entry in decision.predicates if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].predicate == "(S)"
    assert failing[0].first_failure_index == 2
    assert failing[0].first_inexact_index == 2
    # (C) WAS DECIDED FIRST AND HELD: the computed total IS the identity, which
    # is the pair def:exact keeps apart and the reason (S) is in the list.
    completeness = [
        entry
        for entry in decision.predicates
        if entry.predicate == "(C)" and entry.element == "A:{N_(u|t0)}"
    ]
    assert len(completeness) == 1
    assert completeness[0].outcome is True


# ---------------------------------------------------------------------------
#  3. The order rule
# ---------------------------------------------------------------------------


def test_the_arriving_declared_order_wins_over_the_records_listing() -> None:
    """``def:weighted``, "In which order (S) is read on a conditional family".

    "Condition (S) on the conditional family ``{N_{u|t}}_u`` is decided in the
    RESTRICTION of that order to the elements the choice value ``t``
    contributes ... Where a declared order arrives with that alphabet the
    compiler takes it, which is the binding rule of Definition ``def:compile``
    and not a new rule of this definition; where none arrives, the choice the
    compiler makes and emits is the record's own listing."

    THE TWO ORDERS DISAGREE ON THIS FAMILY, which is what makes the rule
    testable at all: ``(1 - 2**-53) + 2**-54`` rounds and
    ``2**-54 + 2**-54 + (1 - 2**-53)`` does not. The record lists ``U_t`` in
    the first order and the arriving alphabet in the second, so the
    presentation is REFUSED under the record's listing and ADMITTED under the
    arriving order -- and the arriving order is what the rule takes.
    """
    record = _alice_choices({"t0": _ROUNDING, "t1": {"u0": identity(2)}})
    listed = ("u0", "u1", "u2")
    assert record.conditional_alphabets["t0"] == listed
    assert conditional_family_order(record, "t0") == listed

    # THE ARRIVING ORDER IS ON THE ALPHABET THAT INDEXES THE WEIGHTED FAMILY --
    # X on Alice's side -- and is given as joint labels, which is what the
    # source part declares; the restriction to t_0's elements is what (S) reads.
    arriving = ("(u1,t0)", "(u2,t0)", "(u0,t0)", "(u0,t1)")
    assert conditional_family_order(record, "t0", arriving) == ("u1", "u2", "u0")
    assert conditional_family_order(record, "t1", arriving) == ("u0",)

    assert decide_conditional_families(record, 2).refusal is not None
    assert decide_conditional_families(record, 2, arriving).refusal is None

    # AND NO PRESENTATION IS REFUSED FOR AN ORDER: an arriving order that does
    # not enumerate this presentation's joint labels leaves the record's own
    # listing in force and refuses nothing of its own.
    foreign = ("x0", "x1", "x2", "x3")
    assert conditional_family_order(record, "t0", foreign) == listed


def test_the_compilation_map_gives_alice_the_order_that_arrives_with_x() -> None:
    """``def:spec`` (a): ``X`` arrives ordered with the source part.

    The specification below declares the same rounding family, with the
    transmitter artefact's signal alphabet -- which IS ``X`` with its declared
    order -- listing the joint labels in the order under which (S) holds, while
    the ``public_choices`` record lists ``U_t`` in the order under which it does
    not. The compilation ADMITS it, and the same specification with the two
    orders agreeing on the record's listing refuses: that pair is the wiring,
    and it is the one place the arriving order reaches the decision.

    A RECEIVER PRESENTATION HAS NO SUCH ORDER TO ARRIVE, and that is asserted
    with it: the physical alphabet is what the weighting produces, so the
    record's listing is the free choice and is emitted.
    """
    record = _alice_choices({"t0": _ROUNDING, "t1": {"u0": identity(2)}})
    specification = _specification(record)
    refused = compile_specification(specification)
    assert refused.refuses
    assert refused.refusal is not None
    assert (
        refused.refusal.reason is RefusalReason.CONDITIONAL_FAMILY_NOT_ADMISSIBLE
    )

    reordered = ("(u1,t0)", "(u2,t0)", "(u0,t0)", "(u0,t1)")
    assert set(reordered) == set(specification.source.alphabet)
    artifact = replace(
        specification.source.artifact, signal_alphabet=reordered
    )
    admitted = decide_every_conditional_family(
        replace(
            specification,
            source=replace(specification.source, artifact=artifact),
        )
    )
    assert admitted.refusal is None
    assert admitted.admitted


def test_a_receiver_presentation_is_decided_before_the_chain_reads_its_products() -> (
    None
):
    """Fail-closed row 1, on the side where the products feed the chain.

    ``def:spec`` (b) admits
    a physical receiver family "possibly presented as a choice-weighted
    family", and ``def:compile`` decides each conditional family "wherever one
    is presented, ON EITHER PARTY'S SIDE". The Alice-side tests above cannot
    see that clause: on Bob's side the products are the family (C2) and (C4)
    read and, in Band A, the family (C3) decides, which is why the row runs
    before the chain row at all.

    So the witness is ``ex:condfamily``'s numbers declared as the RECEIVER's
    presentation: the refusal names party ``B``, and ``chain is None`` says the
    compilation stopped before the chain stage -- the observable that separates
    a decision taken at row 1 from one taken after it.
    """
    receiver = PublicChoices(
        party=Party.BOB,
        choices=("t0", "t1"),
        weights={"t0": HALF, "t1": HALF},
        conditional_alphabets={"t0": ("u0",), "t1": ("u0",)},
        conditional_elements=EX_CONDFAMILY,
    )
    refused = compile_specification(
        _specification(_alice_choices(ADMISSIBLE_ONE_ELEMENT), receiver)
    )
    assert refused.refuses
    assert refused.declaration is None
    assert refused.refusal is not None
    assert (
        refused.refusal.reason is RefusalReason.CONDITIONAL_FAMILY_NOT_ADMISSIBLE
    )
    assert f"party {str(Party.BOB)!r}" in refused.refusal.detail
    assert refused.chain is None, (
        "the decision precedes the chain stage, so no chain report exists"
    )
    assert refused.gate_report is None

    # THE RECEIVER'S PRESENTATION IS DECIDED FIRST of the two, which is the
    # order the stages consume them in: its entries open the transcript.
    decision = decide_every_conditional_family(
        _specification(_alice_choices(ADMISSIBLE_ONE_ELEMENT), receiver)
    )
    assert decision.predicates[0].element == "B:{N_(u|t)}"
    assert not any(
        entry.element.startswith("A:") for entry in decision.predicates
    ), "the decision stopped at the first failure, on B's presentation"

    # AND THE CONTROL COMPILES, so the refusal is the receiver's families and
    # not the fixture's shape.
    admissible = PublicChoices(
        party=Party.BOB,
        choices=("t0", "t1"),
        weights={"t0": HALF, "t1": HALF},
        conditional_alphabets={"t0": ("u0",), "t1": ("u0",)},
        conditional_elements=ADMISSIBLE_ONE_ELEMENT,
    )
    control = compile_specification(
        _specification(_alice_choices(ADMISSIBLE_ONE_ELEMENT), admissible)
    )
    assert control.refusal is None
    assert control.declaration is not None


def test_a_receiver_presentations_conditional_s_is_read_in_the_records_listing() -> (
    None
):
    """THE BEHAVIOUR ON BOB'S SIDE, PINNED, and the clause that is open.

    ``def:weighted`` names
    the alphabet a receiver presentation is indexed by with TWO clauses that
    can disagree in Band A: "the physical receiver alphabet ..., which is the
    order the fibre sum of Definition ``def:chaincond`` (C4) is accumulated in
    and, in Band A, is the emitted alphabet's own". In this input shape the
    physical alphabet IS what the weighting produces -- (C4) is accumulated
    over the record's listing -- while the last link's TARGET alphabet is a
    separate declared datum that Band A may list in another order.

    THE CODE FOLLOWS THE FIRST CLAUSE: no order arrives with a receiver
    presentation, so the record's own listing governs and is emitted. The
    witness below is a three-element rounding family whose (S) FAILS in the
    record's listing and HOLDS in the order the last link declares, and the
    compilation REFUSES -- which is the fail-closed direction of the two, and
    is pinned here rather than left to whichever clause a reader takes. Which
    clause governs is for the claim text to settle.
    """
    receiver = PublicChoices(
        party=Party.BOB,
        choices=("t0", "t1"),
        weights={"t0": HALF, "t1": HALF},
        conditional_alphabets={"t0": ("u0", "u1", "u2"), "t1": ("u0",)},
        conditional_elements={"t0": _ROUNDING, "t1": {"u0": identity(2)}},
    )
    # THE TARGET ALPHABET THE LAST LINK DECLARES, permuted into the order in
    # which (S) holds. The record is untouched.
    holds_in = ("(u1,t0)", "(u2,t0)", "(u0,t0)", "(u0,t1)")
    refused = compile_specification(
        _specification(
            _alice_choices(ADMISSIBLE_ONE_ELEMENT), receiver, holds_in
        )
    )
    assert refused.refuses
    assert refused.refusal is not None
    assert (
        refused.refusal.reason is RefusalReason.CONDITIONAL_FAMILY_NOT_ADMISSIBLE
    )
    assert "ROUNDS" in refused.refusal.detail
    # AND THE ORDER IT WAS READ IN IS THE RECORD'S, which the detail names.
    assert "['u0', 'u1', 'u2']" in refused.refusal.detail
    # (S) DOES HOLD IN THE OTHER ORDER, so the pin is a real disagreement
    # between the two clauses and not a property of the numbers.
    assert decide_conditional_families(receiver, 2).refusal is not None
    assert decide_conditional_families(receiver, 2, holds_in).admitted


def test_a_conditional_alphabet_is_finite_non_empty_and_a_set() -> None:
    """``U_t`` is typed like ``T_pub``, and both failures are MALFORMED.

    ``def:weighted`` declares "for each ``t`` a POVM ``{N_{u|t}}_{u in U_t}``". An EMPTY
    ``U_t`` tabulates no family at all -- ``eq:declorder`` has no ``Sigma_{|J|}`` over
    an empty alphabet -- and a REPEATED ``u`` is not an alphabet: (C) and (S)
    would sum one operator twice and the disjoint union would collide. Neither
    is a refusal: they are presentations of an input this module does not type,
    so no clause can be read against them and a reason would have to be
    invented -- the rule ``T_pub``'s own two guards follow.
    """
    with pytest.raises(MalformedInputError, match="empty"):
        _alice_choices({"t0": {}, "t1": {"u0": identity(2)}})
    with pytest.raises(MalformedInputError, match="one outcome repeats"):
        PublicChoices(
            party=Party.ALICE,
            choices=("t0",),
            weights={"t0": F(1)},
            conditional_alphabets={"t0": ("u0", "u0")},
            conditional_elements={"t0": {"u0": identity(2)}},
        )


# ---------------------------------------------------------------------------
#  4. The shipped instances
# ---------------------------------------------------------------------------


def test_both_shipped_instances_declare_admissible_conditional_families() -> None:
    """The decision is taken on every presentation they declare, and holds.

    ``instances/bb84`` declares one on EACH side -- Alice's conjugated
    projectors and the receiver's physical family (``def:spec`` (b)) -- and
    ``instances/optical_bb84`` declares Alice's through a non-trivial chain, its
    receiver family arriving directly. So the two instances between them
    exercise both parties and both presentations of the receiver, and every
    conditional family of both is a POVM: the decision refuses nothing that
    compiles.
    """
    from instances.bb84.specification import bb84_specification

    specification = bb84_specification(HALF, HALF, HALF, HALF)
    decision = decide_every_conditional_family(specification)
    assert decision.admitted
    assert all(entry.outcome for entry in decision.predicates)
    # PER PARTY: one (T) entry for the presentation, then (H), (P), (C), (S)
    # per choice value, keyed by (party, choice value) and carrying no block --
    # the record declares one undecomposed array per outcome and no sector map.
    assert [
        (entry.element, entry.predicate) for entry in decision.predicates
    ] == [
        (f"{party}:{{N_(u|t)}}", "(T)")
        if predicate == "(T)"
        else (f"{party}:{{N_(u|{choice})}}", predicate)
        for party in ("B", "A")
        for choice, predicate in (
            ("", "(T)"),
            *(
                (value, leg)
                for value in ("Z", "X")
                for leg in ("(H)", "(P)", "(C)", "(S)")
            ),
        )
    ]
    assert all(entry.block is None for entry in decision.predicates)

    compiled = compile_specification(specification)
    assert compiled.refusal is None
