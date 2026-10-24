"""``req:physical-family-decision``: the presented physical family is decided.

WHAT THIS FILE IS THE TEST HALF OF. There is no A-PRESENT: the exact admissibility of
the physical receiver family as presented is clause (iv) of ``def:well-formed-spec``,
and the compiler decides it on every route, as one block on the physical receiver space,
before any condition of the chain, refusing with ``physical_family_not_admissible`` and
naming the measured factor, the predicate and the index of the first failure (for (S),
the first inexact addition). One test per failure the requirement names, each
a refusal that would not happen were the decision absent, and the control on
which it passes and is recorded.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import pytest
from protocol_blocks import source_part
from tests.unit.test_protocol_general_compile import (
    FACTOR_LETTERS,
    _two_party_specification,
)

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
from certiqs_key.foundations.exact import Matrix, identity, matrix
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
    compile_specification,
    decide_physical_family,
    default_party_partition,
    resolve_povm,
    weighted_family,
)

pytestmark = pytest.mark.contract

HALF = F(1, 2)
ONE_SECTOR = SectorStructure(
    labels=("s0",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
)
Z0 = matrix(((1, 0), (0, 0)))
Z1 = matrix(((0, 0), (0, 1)))
ADMISSIBLE: dict[Label, Matrix] = {"v0": Z0, "v1": Z1}
X_ALPHABET: tuple[Label, ...] = ("x0", "x1")
ALICE = DirectPovm(alphabet=X_ALPHABET, elements={"x0": Z0, "x1": Z1})

#: ``1 - 2**-53`` and ``2**-54`` are binary64 and their sum is not.
_BIG = F(1) - F(1, 2**53)
_SMALL = F(1, 2**54)


def _specification(physical: PovmPresentation) -> ProtocolSpecification:
    """Return a one-sector specification presenting ``physical``.

    The chain is one exact link from a two-dimensional physical system ``B``
    to ``Q`` with an admissible target family ``{Z0, Z1}`` (or, where the
    physical alphabet differs, the physical matrices themselves as one-sector
    blocks), so that every refusal below is the physical decision's: it is
    taken before the chain stage, and the result carries no chain report.
    """
    if isinstance(physical, DirectPovm):
        alphabet = physical.alphabet
        elements = dict(physical.elements)
    else:
        weighted = weighted_family(physical)
        alphabet = weighted.alphabet
        elements = dict(weighted.elements)
    target = (
        {
            label: BlockOperator.of(ONE_SECTOR, (ADMISSIBLE[label],))
            for label in alphabet
        }
        if set(alphabet) == set(ADMISSIBLE)
        else {
            label: BlockOperator.of(ONE_SECTOR, (elements[label],))
            for label in alphabet
        }
    )
    chain = ReductionChain(
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="L1",
                segment=LinkStage.RECEIVER,
                link_type="wpfss",
                source_descriptor=SystemDescriptor(
                    name="B", dim=2, side=Side.RECEIVER
                ),
                target_descriptor=SystemDescriptor(
                    name="Q",
                    dim=2,
                    side=Side.RECEIVER,
                    sectors=(("s0", 2),),
                    sector_block_kind=BlockKind.PROOF_SECTOR,
                ),
                status=LinkStatus.EXACT,
                target_alphabet=alphabet,
                target_povm=target,
            ),
        ),
        outcome_correspondence=dict(zip(alphabet, alphabet, strict=True)),
    )
    announcements = tuple(f"b_{label}" for label in alphabet)
    alice_announcements = ("a0", "a1")
    classes = [(c_a, c_b) for c_a in alice_announcements for c_b in announcements]
    public = PublicPart(
        partition=default_party_partition(X_ALPHABET, alphabet),
        announce_alice=dict(zip(X_ALPHABET, alice_announcements, strict=True)),
        announce_bob=dict(zip(alphabet, announcements, strict=True)),
        alice_announcement_alphabet=alice_announcements,
        bob_announcement_alphabet=announcements,
        sifting=dict.fromkeys(classes, Sifting.PASS),
        key_rule={
            (readout, kappa): index % 2
            for index, readout in enumerate(X_ALPHABET)
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=("g",),
        accept_statistic=dict.fromkeys(classes, "g"),
    )
    return ProtocolSpecification(
        source=source_part(
            alphabet=X_ALPHABET,
            alice_dim=2,
            alice_povm=ALICE,
            transmitted_dim=2,
            signal_weights=dict.fromkeys(X_ALPHABET, HALF),
            signal_states=dict.fromkeys(X_ALPHABET, matrix(((HALF, 0), (0, HALF)))),
        ),
        receiver=ReceiverPart(physical_dim=2, physical_povm=physical),
        public=public,
        sectors=ONE_SECTOR,
        chain=chain,
        constraints=SpecConstraints(),
    )


def _refusal_of(physical: PovmPresentation) -> tuple[str, str]:
    result = compile_specification(_specification(physical))
    assert result.refusal is not None
    # Taken before any condition of the chain: no chain report exists.
    assert result.chain is None
    return str(result.refusal.reason), result.refusal.detail


def test_an_admissible_family_passes_and_the_decision_is_recorded() -> None:
    """The control: the decision is taken, recorded, and refuses nothing."""
    result = compile_specification(
        _specification(DirectPovm(alphabet=("v0", "v1"), elements=ADMISSIBLE))
    )
    assert result.refusal is None, result.refusal
    assert result.gate_report is not None
    taken = result.gate_report.transcript.lookup(
        PredicateSource.COMPILATION_MAP, "f0:{F^ph_w}"
    )
    assert [outcome.predicate for outcome in taken] == ["(H)", "(P)", "(C)", "(S)"]
    assert all(outcome.outcome for outcome in taken)
    # The key of the absent assumption is on no ledger.
    assert "presented_receiver_family" not in result.assumption_ledger


def test_a_non_positive_element_is_refused_naming_factor_predicate_and_index() -> None:
    bad = matrix(((1, 0), (0, -HALF)))
    family = DirectPovm(
        alphabet=("v0", "v1"),
        elements={"v0": bad, "v1": matrix(((0, 0), (0, F(3, 2))))},
    )
    reason, detail = _refusal_of(family)
    assert reason == str(RefusalReason.PHYSICAL_FAMILY_NOT_ADMISSIBLE)
    assert "'f0'" in detail and "(P)" in detail and "element 1" in detail


def test_a_non_hermitian_element_is_refused_at_h() -> None:
    skew = matrix(((HALF, HALF), (0, HALF)))
    family = DirectPovm(
        alphabet=("v0", "v1"),
        elements={"v0": matrix(((HALF, 0), (0, HALF))), "v1": skew},
    )
    reason, detail = _refusal_of(family)
    assert reason == str(RefusalReason.PHYSICAL_FAMILY_NOT_ADMISSIBLE)
    assert "(H)" in detail and "element 2" in detail


def test_a_sum_off_the_identity_is_refused_at_c() -> None:
    family = DirectPovm(
        alphabet=("v0", "v1"),
        elements={"v0": Z0, "v1": matrix(((0, 0), (0, HALF)))},
    )
    reason, detail = _refusal_of(family)
    assert reason == str(RefusalReason.PHYSICAL_FAMILY_NOT_ADMISSIBLE)
    assert "(C)" in detail and "2-dimensional" in detail


def test_a_rounding_sum_is_refused_at_s_with_the_first_inexact_addition() -> None:
    """Exactly the identity, every entry binary64, and the second addition rounds."""
    family = DirectPovm(
        alphabet=("v0", "v1", "v2"),
        elements={
            "v0": matrix(((_BIG, 0), (0, HALF))),
            "v1": matrix(((_SMALL, 0), (0, F(1, 4)))),
            "v2": matrix(((_SMALL, 0), (0, F(1, 4)))),
        },
    )
    reason, detail = _refusal_of(family)
    assert reason == str(RefusalReason.PHYSICAL_FAMILY_NOT_ADMISSIBLE)
    assert "ROUNDS" in detail and "element 2" in detail
    decision = decide_physical_family(
        ReceiverPart(physical_dim=2, physical_povm=family), family, "f0"
    )
    (summation,) = [p for p in decision.predicates if p.predicate == "(S)"]
    assert summation.first_inexact_index == 2


def test_a_choice_weighted_family_whose_own_sum_rounds_is_refused() -> None:
    """Admissible conditional families, representable products, a rounding sum.

    ``t1``'s family is ``{1}`` and ``t0``'s is ``{diag(1 - 2**-53, 0),
    diag(2**-53, 1)}``, each exactly a POVM with a sum that rounds nowhere;
    with ``q = (1/2, 1/2)`` every product is binary64. The weighted family in
    the record's listing, ``t1`` first, adds ``1/2 - 2**-54`` to ``1/2`` at its
    second element, which rounds: (S) on its own declared-order sum fails, the
    one condition decided of the family itself.
    """
    choices = PublicChoices(
        party=Party.BOB,
        choices=("t1", "t0"),
        weights={"t0": HALF, "t1": HALF},
        conditional_alphabets={"t1": ("c",), "t0": ("a", "b")},
        conditional_elements={
            "t1": {"c": identity(2)},
            "t0": {
                "a": matrix(((_BIG, 0), (0, 0))),
                "b": matrix(((F(1, 2**53), 0), (0, 1))),
            },
        },
    )
    resolved = resolve_povm(choices)
    assert resolved.refusal is None  # the products are representable
    reason, detail = _refusal_of(choices)
    assert reason == str(RefusalReason.PHYSICAL_FAMILY_NOT_ADMISSIBLE)
    assert "choice-weighted" in detail and "element 2" in detail
    decision = decide_physical_family(
        ReceiverPart(physical_dim=2, physical_povm=choices), resolved.require(), "f0"
    )
    # Only (S) is decided of the weighted family itself.
    assert [p.predicate for p in decision.predicates] == ["(S)"]


def test_a_further_factor_s_choice_weighted_family_is_decided() -> None:
    """A further factor's choice-weighted family is decided.

    def:well-formed-spec (iv): EACH measured factor's family, conditional
    families included, and not only the first factor's.

    Factor ``b`` of ex:two-party-shape presents a one-choice family whose
    conditional family sums exactly to the identity with no rounding (so (S)
    of the weighted family holds) but fails (P) at "0". Its link supplies no
    channel, so (C4) is not decided and nothing downstream would catch it.
    Without the decision a declaration would be emitted.
    """
    specification = _two_party_specification()
    (second,) = specification.further_receiver_factors
    assert second.chain is not None
    (link,) = second.chain.receiver_segment
    no_channel = replace(link, channel=None, link_type="wpfss")
    choices = PublicChoices(
        party=Party.BOB,
        choices=("t",),
        weights={"t": F(1)},
        conditional_alphabets={"t": FACTOR_LETTERS},
        conditional_elements={
            "t": {
                "0": matrix(((1, 0, 0), (0, -HALF, 0), (0, 0, 0))),
                "1": matrix(((0, 0, 0), (0, F(3, 2), 0), (0, 0, 0))),
                "fl": matrix(((0, 0, 0), (0, 0, 0), (0, 0, 1))),
            }
        },
        joint_labels={(u, "t"): u for u in FACTOR_LETTERS},
    )
    second = replace(
        second,
        physical_povm=choices,
        chain=replace(second.chain, receiver_segment=(no_channel,)),
    )
    result = compile_specification(
        replace(specification, further_receiver_factors=(second,))
    )
    assert result.refusal is not None
    assert result.refusal.reason == RefusalReason.CONDITIONAL_FAMILY_NOT_ADMISSIBLE
    assert "(P)" in result.refusal.detail
    # The refusal names the measured factor beside the party: two factors may
    # carry the same party label.
    factor = second.factor_label if second.factor_label is not None else "f1"
    assert f"measured factor {factor!r}" in result.refusal.detail
    # Taken before any condition of the chain.
    assert result.chain is None
