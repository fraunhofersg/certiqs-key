"""The general format of the declaration, check by check and string by string.

WHAT THIS FILE IS FOR. ``def:declaration`` has (DX1)--(DX6) and every other
definition of the module has one appended paragraph whose degenerate case is the
plain text entry for entry. Two things have to be
executed for that sentence to mean anything, and both are here:

1. **A candidate of the accepted format is read by the accepted clauses.** Every
   general-format field of
   :class:`~certiqs_key.protocol_compiler.declaration.CandidateDeclaration` is
   optional and its absence is the degenerate value, so
   :attr:`~certiqs_key.protocol_compiler.declaration.CandidateDeclaration.is_general_format`
   is ``False`` for every declaration this repository emits and the whole
   accepted suite is the test of that half.
2. **Each of the seven new refusal strings refuses the object its claim names,
   and nothing else.** One test per string, built BY HAND on a candidate --
   ``def:validator`` is stated on a candidate, and ``thm:validator-soundness``
   (ii)--(iii) are unstatable otherwise -- because no specification this repository
   ships presents a general-format one.

THE OBJECTS ARE BUILT BY HAND AND THAT IS THE POINT. No shipped instance
declares two Alice sectors. So the
records below are shaped as the interface's general-format input rows say.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from certiqs_key.domain.announcements import (
    AnnouncementTranscript,
    Message,
    two_message_transcript,
)
from certiqs_key.domain.constraints import ConstraintEntry, Relation, RhsTag
from certiqs_key.domain.families import (
    AliceForm,
    AliceSlot,
    FactorFamily,
    FactorisedFamily,
)
from certiqs_key.foundations.blocks import (
    BlockKind,
    BlockOperator,
    FactorisedSectorMap,
    JointBlockOperator,
    SectorFactor,
    SectorStructure,
    SystemTag,
)
from certiqs_key.foundations.errors import HypothesisError, MalformedInputError
from certiqs_key.foundations.exact import Cx, identity, matrix, scale
from certiqs_key.protocol_compiler.declaration import (
    CandidateDeclaration,
    build_label_index_map,
)
from certiqs_key.protocol_compiler.feasibility import (
    factor_sector_indices,
    verify_witness,
)
from certiqs_key.protocol_compiler.gates import (
    LICENSED_TAGS,
    CertificateState,
    EmissionOutcome,
    GateInputs,
    licensed_for_the_emitted_mode,
    resolve_gates,
)
from certiqs_key.protocol_compiler.reasons import (
    REFUSAL_REASONS_GENERAL_FORMAT,
    RefusalReason,
)
from certiqs_key.protocol_compiler.spec import Party, default_party_partition
from certiqs_key.protocol_compiler.statistics import (
    joint_distribution,
    phi_distribution,
)
from certiqs_key.protocol_compiler.validation import (
    check_v1,
    check_v2,
    check_v3,
    check_v6,
    check_v7,
    decidability_counts,
)
from certiqs_key.transmitter.reasons import CertificateForm, SourceMode

KIND = BlockKind.PROOF_SECTOR


def _sectors(*entries: tuple[str, int]) -> SectorStructure:
    """Return a sector map over ``(label, dim)`` pairs, in the declared order."""
    return SectorStructure(
        labels=tuple(label for label, _ in entries),
        dims=tuple(dim for _, dim in entries),
        block_kind=KIND,
    )


#: Alice's two sectors, each of dimension one: the smallest shape that is not the
#: degenerate one, and the shape ``d_A > 1`` with every Alice block of dimension
#: one that ``def:homog``'s round-3 correction is about.
ALICE = _sectors(("t0", 1), ("t1", 1))

#: One measured factor with a data sector and a flag sector, which is
#: ``ex:two-party-shape``'s per-factor shape.
MEASURED = _sectors(("d", 2), ("fl", 1))

#: THE MEASURED FACTOR'S OWN LABEL, which is what an entry's scope names. It is
#: NOT the party label: ``reductions`` emits a label per factor and a party label
#: beside it, and a party may hold two factors.
FACTOR = "bob-station"


def _general_declaration(
    *,
    alice_form: AliceForm = AliceForm.POVM,
    trusted: bool = True,
    entries: tuple[ConstraintEntry, ...] = (),
    alice_sectors: SectorStructure = ALICE,
    marginal_blocks: tuple[tuple[tuple[object, ...], ...], ...] | None = None,
    ensemble_blocks: dict[str, tuple[object, ...]] | None = None,
) -> CandidateDeclaration:
    """Return a general-format candidate: two Alice sectors, one measured factor.

    The smallest candidate that is general in (DX1), (DX2) and (DX4) and accepted
    by every check, so that each test below moves ONE datum and reads the refusal
    that datum's claim names.
    """
    factorisation = FactorisedSectorMap(
        factors=(
            SectorFactor(
                party=str(Party.ALICE),
                sectors=alice_sectors,
                system=SystemTag.A,
            ),
            SectorFactor(
                party=str(Party.BOB),
                sectors=MEASURED,
                system=SystemTag.Q,
                label=FACTOR,
            ),
        )
    )
    product = factorisation.flattened_of(SystemTag.Q)
    assert product is not None
    bob = FactorFamily.of(
        str(Party.BOB),
        ("0", "1", "fl"),
        (
            BlockOperator.of(MEASURED, [matrix([[1, 0], [0, 0]]), matrix([[0]])]),
            BlockOperator.of(MEASURED, [matrix([[0, 0], [0, 1]]), matrix([[0]])]),
            BlockOperator.of(MEASURED, [matrix([[0, 0], [0, 0]]), matrix([[1]])]),
        ),
    )
    factors = FactorisedFamily.of(factorisation, [bob])
    half = Fraction(1, 2)
    marginal = (
        BlockOperator.of(
            alice_sectors,
            [matrix([[half]]), matrix([[half]])]
            if marginal_blocks is None
            else list(marginal_blocks),
        )
        if trusted
        else None
    )
    if alice_form is AliceForm.ENSEMBLE:
        blocks = ensemble_blocks or {
            "x0": (matrix([[Fraction(1, 4)]]), matrix([[Fraction(1, 4)]])),
            "x1": (matrix([[Fraction(1, 4)]]), matrix([[Fraction(1, 4)]])),
        }
        slot = AliceSlot.of(
            AliceForm.ENSEMBLE,
            ("x0", "x1"),
            tuple(
                BlockOperator.of(alice_sectors, list(blocks[label]))
                for label in ("x0", "x1")
            ),
        )
    else:
        slot = AliceSlot.of(
            AliceForm.POVM,
            ("x0", "x1"),
            (
                BlockOperator.of(
                    alice_sectors, [matrix([[half]]), matrix([[half]])]
                ),
                BlockOperator.of(
                    alice_sectors, [matrix([[half]]), matrix([[half]])]
                ),
            ),
        )
    x_alphabet = ("x0", "x1")
    v_alphabet = factors.alphabet()
    partition = default_party_partition(x_alphabet, v_alphabet)
    announce_alice = dict.fromkeys(x_alphabet, "ok")
    announce_bob = dict.fromkeys(v_alphabet, "ok")
    classes = (("ok", "ok"),)
    declaration = CandidateDeclaration(
        alice_dim=alice_sectors.total_dim,
        alice_marginal=None,
        sectors=product,
        alice_alphabet=x_alphabet,
        alice_povm={},
        bob_alphabet=v_alphabet,
        bob_povm={},
        partition=partition,
        announce_alice=announce_alice,
        announce_bob=announce_bob,
        alice_announcement_alphabet=("ok",),
        bob_announcement_alphabet=("ok",),
        acceptance_alphabet=("c",),
        accept_statistic=dict.fromkeys(classes, "c"),
        key_map={(x, v): 0 for x in x_alphabet for v in v_alphabet},
        key_alphabet=(0,),
        key_holder=Party.ALICE,
        constraint_list=entries,
        sector_factorisation=factorisation,
        alice_slot=slot,
        alice_marginal_blocks=marginal,
        bob_factors=factors,
    )
    return CandidateDeclaration(
        **{
            **declaration.__dict__,
            "label_index_map": build_label_index_map(
                {
                    "X": x_alphabet,
                    "V": v_alphabet,
                    "S": product.labels,
                    "O_A": partition.alice_readout_alphabet,
                    "O_B": partition.bob_readout_alphabet,
                    "C_A": ("ok",),
                    "C_B": ("ok",),
                    "Chat": ("c",),
                    "Z_perp": ("0", "perp"),
                }
            ),
        }
    )




# ---------------------------------------------------------------------------
#  The degenerate half: a candidate of the accepted format is not general
# ---------------------------------------------------------------------------


def test_a_candidate_of_the_accepted_format_is_not_in_the_general_format() -> None:
    """Every general slot absent, so every check reads its accepted clause.

    The design rule, executed: "the accepted text is the case
    ``|T| = 1``, ``|F| = 1``, POVM form, ``L = 2`` of the following one, ENTRY FOR
    ENTRY". The whole accepted suite is the other half of this test.
    """
    general = _general_declaration()
    accepted = CandidateDeclaration(
        **{
            **general.__dict__,
            "sector_factorisation": None,
            "alice_slot": None,
            "alice_marginal_blocks": None,
            "bob_factors": None,
            "alice_povm": {"x0": identity(1), "x1": identity(1)},
        }
    )
    assert general.is_general_format
    assert not accepted.is_general_format
    assert accepted.alice_form is AliceForm.POVM
    assert accepted.alice_factor is None
    assert accepted.alice_sectors.count == 1


def test_the_general_candidate_passes_every_check_it_should() -> None:
    """The baseline: nothing below refuses the candidate the tests start from."""
    declaration = _general_declaration()
    for check in (check_v1, check_v2, check_v3, check_v6):
        outcome = check(declaration)
        assert outcome.passed, (outcome.check, outcome.refusal)
    outcome, _ = check_v7(declaration)
    assert outcome.passed, outcome.refusal


def test_general_statistics_are_evaluated_per_joint_sector() -> None:
    """The general POVM and product family feed the same exact functional."""
    declaration = _general_declaration()
    blocks = tuple(
        scale(Fraction(1, 4 * dim), identity(dim))
        for dim in declaration.joint_sectors.dims
    )
    state = JointBlockOperator.of(
        declaration.sectors, declaration.alice_sectors, blocks
    )
    expected = {
        (x, v): probability
        for x in declaration.alice_alphabet
        for v, probability in (
            ("0", Fraction(1, 8)),
            ("1", Fraction(1, 8)),
            ("fl", Fraction(1, 4)),
        )
    }
    assert joint_distribution(declaration, state) == expected
    assert joint_distribution(declaration, state.dense()) == expected
    statistics = phi_distribution(declaration, state)
    assert statistics.values == {"c": Fraction(1)}
    assert statistics.total == 1


def test_general_statistics_do_not_form_the_ensemble_denoted_povm() -> None:
    declaration = _general_declaration(alice_form=AliceForm.ENSEMBLE)
    blocks = tuple(
        scale(Fraction(1, 4 * dim), identity(dim))
        for dim in declaration.joint_sectors.dims
    )
    state = JointBlockOperator.of(
        declaration.sectors, declaration.alice_sectors, blocks
    )
    with pytest.raises(HypothesisError, match="formed by no one"):
        joint_distribution(declaration, state)


def test_the_decoy_constructor_source_link_docks_without_a_fock_cutoff() -> None:
    """The infinite-dimensional target is carried as an Alice-side null dim."""
    from decoy_support import tagged_declaration
    from reductions_support import flat_call

    from certiqs_key.domain.chain import Side, SystemDescriptor
    from certiqs_key.protocol_compiler.docking_reductions import (
        dock_source_segment,
        source_chain_segment,
    )
    from certiqs_key.reductions import docking
    from certiqs_key.reductions.emit import reduce
    from certiqs_key.reductions.wpfss import FlatInstanceBuilder

    emitted_links = tagged_declaration().source_segment
    source = source_chain_segment(emitted_links)
    assert len(source) == 1
    assert source[0].source_descriptor.dim is not None
    assert source[0].target_descriptor.dim is None
    assert source[0].target_descriptor.side is Side.ALICE
    assert source[0].channel is None

    reduced = reduce(flat_call(), FlatInstanceBuilder())
    assert reduced.artifact is not None
    physical = SystemDescriptor("B", 4, Side.RECEIVER)
    receiver_chain = docking.reduction_chain(
        reduced.artifact,
        physical,
        sector_block_kind=KIND,
    )
    chain = dock_source_segment(receiver_chain, emitted_links)
    assert chain.source_segment == source

    with pytest.raises(MalformedInputError, match="only an Alice-side"):
        SystemDescriptor("unknown receiver", None, Side.RECEIVER)

    from certiqs_key.domain.manifest import ReductionSystemDescriptor

    carried = ReductionSystemDescriptor(name="A'", dim=None, side="alice")
    assert carried.model_dump(mode="json")["dim"] is None
    with pytest.raises(ValueError, match="only an Alice-side"):
        ReductionSystemDescriptor(name="Q", dim=None, side="receiver")

    from dataclasses import replace

    data_link = replace(emitted_links[0], channel_witness={}, obligation=None)
    with pytest.raises(MalformedInputError, match="data SourceLink"):
        source_chain_segment((data_link,))


# ---------------------------------------------------------------------------
#  The seven new refusal strings, one test each
# ---------------------------------------------------------------------------


def test_the_seven_new_strings_are_the_interfaces_seven() -> None:
    """The partition class is the seven ``interface.yaml`` spells, in its order."""
    assert [str(reason) for reason in REFUSAL_REASONS_GENERAL_FORMAT] == [
        "ensemble_form_in_untrusted_mode",
        "alice_sector_marginal_zero",
        "alice_ensemble_marginal_mismatch",
        "alice_ensemble_sum_rounds",
        "constraint_scope_not_a_factor",
        "ensemble_presentation_without_ensemble_form",
        "general_entry_beside_source_segment",
    ]


def test_an_ensemble_form_beside_nomarg_is_refused_at_v3() -> None:
    """``ensemble_form_in_untrusted_mode``: D(iii)'s general-format clause.

    "An ensemble-form slot beside a marginal slot holding ``nomarg`` is refused
    ... which is a decision on WHICH OF TWO SLOTS IS FILLED, NOT ON A NUMBER."
    """
    declaration = _general_declaration(alice_form=AliceForm.ENSEMBLE, trusted=False)
    outcome = check_v3(declaration)
    assert not outcome.passed
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.ENSEMBLE_FORM_IN_UNTRUSTED_MODE


def test_a_zero_alice_marginal_block_is_refused_at_v2_in_ensemble_form() -> None:
    """``alice_sector_marginal_zero``: ``tau_A^(t) != 0`` per sector.

    A comparison of declared entries with the datum ``0`` (``eq:ensembleform``),
    and it is decided ONLY in ensemble form: the same blocks in POVM form pass V2,
    which the second half of this test asserts.
    """
    zero_second = (matrix([[Fraction(1)]]), matrix([[Fraction(0)]]))
    ensemble = {
        "x0": (matrix([[Fraction(1, 2)]]), matrix([[Fraction(0)]])),
        "x1": (matrix([[Fraction(1, 2)]]), matrix([[Fraction(0)]])),
    }
    declaration = _general_declaration(
        alice_form=AliceForm.ENSEMBLE,
        marginal_blocks=zero_second,
        ensemble_blocks=ensemble,
    )
    outcome = check_v2(declaration)
    assert not outcome.passed
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.ALICE_SECTOR_MARGINAL_ZERO

    povm = _general_declaration(marginal_blocks=zero_second)
    assert check_v2(povm).passed


def test_an_ensemble_sum_that_is_not_tau_a_is_refused_entry_by_entry() -> None:
    """``alice_ensemble_marginal_mismatch``: the identity of ``eq:ensembleform``.

    It stands IN PLACE OF the completeness identity, so the sum is compared with
    the declared ``tau_A`` block and not with ``1_{A_t}``.
    """
    ensemble = {
        "x0": (matrix([[Fraction(1, 4)]]), matrix([[Fraction(1, 4)]])),
        "x1": (matrix([[Fraction(1, 8)]]), matrix([[Fraction(1, 4)]])),
    }
    declaration = _general_declaration(
        alice_form=AliceForm.ENSEMBLE, ensemble_blocks=ensemble
    )
    outcome = check_v3(declaration)
    assert not outcome.passed
    assert outcome.refusal is not None
    assert (
        outcome.refusal.reason is RefusalReason.ALICE_ENSEMBLE_MARGINAL_MISMATCH
    )


def test_an_ensemble_sum_that_rounds_is_refused_although_it_holds() -> None:
    """``alice_ensemble_sum_rounds``: (S) is on the ADDITIONS, not the operands.

    (C) and (S) "are read on DIFFERENT OBJECTS and can disagree" -- (C) on the
    COMPUTED binary64 total and (S) on the additions that formed it. Here
    ``1 + 2^-60`` rounds to ``1`` in binary64, and the declared ``tau_A`` block IS
    that computed total, so the identity holds and (S) fails: the case
    ``thm:pc12`` (ii) exhibits, read on the ensemble form's identity instead of on
    a completeness sum.
    """
    tiny = Fraction(1, 2**60)
    ensemble = {
        "x0": (matrix([[Fraction(1)]]), matrix([[Fraction(1, 4)]])),
        "x1": (matrix([[tiny]]), matrix([[Fraction(1, 4)]])),
    }
    declaration = _general_declaration(
        alice_form=AliceForm.ENSEMBLE,
        marginal_blocks=(matrix([[Fraction(1)]]), matrix([[Fraction(1, 2)]])),
        ensemble_blocks=ensemble,
    )
    outcome = check_v3(declaration)
    assert not outcome.passed
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.ALICE_ENSEMBLE_SUM_ROUNDS


def test_a_scope_that_names_no_measured_factor_is_refused_at_v6() -> None:
    """``constraint_scope_not_a_factor``: a FACTOR label against the factor list.

    Decided and never measured, "as the relation symbol is", and decided BEFORE
    the numerical clauses: an entry whose scope names no factor has no map for its
    operator to be a block list against, which is why V1 compares nothing for it.
    """
    entry = ConstraintEntry(
        operator=BlockOperator.of(MEASURED, [identity(2), identity(1)]),
        relation=Relation.LE,
        rhs=Fraction(1, 8),
        arriving_tag=RhsTag.PARTY_LOCAL,
        scope="Z",
    )
    declaration = _general_declaration(entries=(entry,))
    outcome = check_v6(declaration)
    assert not outcome.passed
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.CONSTRAINT_SCOPE_NOT_A_FACTOR


def test_general_rhs_blocks_reach_v1_and_v6_on_every_alice_sector() -> None:
    """A general RHS carries Alice's map and is checked block by block."""
    rhs = BlockOperator.of(ALICE, [identity(1), identity(1)])
    entry = ConstraintEntry(
        operator=BlockOperator.of(MEASURED, [identity(2), identity(1)]),
        relation=Relation.LE,
        rhs=rhs,
        arriving_tag=RhsTag.GENERAL,
        scope=FACTOR,
    )
    declaration = _general_declaration(entries=(entry,))
    assert entry.tag is RhsTag.GENERAL
    assert check_v1(declaration).passed
    v6 = check_v6(declaration)
    assert v6.passed
    hermiticity = [row for row in v6.predicates if row.predicate == "(H)"]
    assert [row.block for row in hermiticity] == ["t0", "t1"]
    machine_entry = declaration.as_machine_record()["constraint_list"][0]
    assert machine_entry["rhs_kind"] == "block_operator"
    assert len(machine_entry["rhs"]) == 2


def test_general_rhs_wrong_map_and_nonhermitian_block_are_refused() -> None:
    """V1 compares the carried map; V6 decides block Hermiticity exactly."""
    wrong_map = _sectors(("other0", 1), ("other1", 1))
    operator = BlockOperator.of(MEASURED, [identity(2), identity(1)])
    wrong_entry = ConstraintEntry(
        operator=operator,
        relation=Relation.LE,
        rhs=BlockOperator.of(wrong_map, [identity(1), identity(1)]),
        scope=FACTOR,
    )
    assert not check_v1(_general_declaration(entries=(wrong_entry,))).passed

    nonhermitian = ConstraintEntry(
        operator=operator,
        relation=Relation.LE,
        rhs=BlockOperator.of(
            ALICE,
            [matrix([[Cx(Fraction(0), Fraction(1))]]), identity(1)],
        ),
        scope=FACTOR,
    )
    assert not check_v6(_general_declaration(entries=(nonhermitian,))).passed


def test_pc6_counts_current_general_mode_and_form_inventories() -> None:
    """PC6 counts trusted/untrusted and POVM/ensemble branches explicitly."""
    operator = BlockOperator.of(MEASURED, [identity(2), identity(1)])
    general = ConstraintEntry(
        operator=operator,
        relation=Relation.LE,
        rhs=BlockOperator.of(ALICE, [identity(1), identity(1)]),
        scope=FACTOR,
    )
    trusted = decidability_counts(_general_declaration(entries=(general,)))
    assert trusted.v2_v3_v6 == 33
    assert (trusted.summations, trusted.v7) == (5, 13)

    scalar = ConstraintEntry(
        operator=operator, relation=Relation.LE, rhs=Fraction(1), scope=FACTOR
    )
    untrusted = decidability_counts(
        _general_declaration(trusted=False, entries=(scalar,))
    )
    assert (untrusted.v2, untrusted.v2_v3_v6) == (0, 26)
    assert (untrusted.summations, untrusted.v7) == (4, 10)

    ensemble = decidability_counts(
        _general_declaration(alice_form=AliceForm.ENSEMBLE)
    )
    assert ensemble.v2 == 7


def test_a_presentation_beside_a_povm_form_declaration_is_refused_at_g2() -> None:
    """``ensemble_presentation_without_ensemble_form``: (G2) by form.

    "A presentation is admitted ONLY BESIDE AN ENSEMBLE-FORM DECLARATION, nothing
    tying the declared ``{M_x}`` to it", which is the transmitter's own rule for a
    POVM-form consumer -- so this string names an EXISTING refusal. Beside an
    ensemble-form declaration the same inputs emit.
    """
    common = {
        "validator_passed": True,
        "emitted_mode": SourceMode.TRUSTED,
        "alice_dim": 2,
        "certificate": CertificateState.PRESENT_PASSING,
        "has_constraint_entries": False,
        "list_licensed": True,
        "license_present": False,
        "certificate_form": CertificateForm.ENSEMBLE_PRESENTATION,
    }
    refused = resolve_gates(GateInputs(**common, alice_form=AliceForm.POVM))
    assert refused.outcome is EmissionOutcome.REFUSAL
    assert refused.refusal is not None
    assert (
        refused.refusal.reason
        is RefusalReason.ENSEMBLE_PRESENTATION_WITHOUT_ENSEMBLE_FORM
    )
    admitted = resolve_gates(GateInputs(**common, alice_form=AliceForm.ENSEMBLE))
    assert admitted.outcome is EmissionOutcome.EMISSION


def test_a_general_entry_beside_a_non_empty_source_segment_is_refused() -> None:
    """``general_entry_beside_source_segment``: the licensed-only rule.

    It REFUSES A CASE THE ACCEPTED FORMAT ADMITS, which without the rule would
    be emitted with the flag false, and the refusal is strictly the more
    conservative outcome; beside an EMPTY segment the same list is admitted.
    The detail names no claim that does not exist
    (not the transmitter/ass:nosrc).
    """
    from certiqs_key.protocol_compiler.chain import check_licensed_only

    general = ConstraintEntry(
        operator=BlockOperator.of(MEASURED, [identity(2), identity(1)]),
        relation=Relation.LE,
        rhs=identity(2),
    )
    scalar = ConstraintEntry(
        operator=BlockOperator.of(MEASURED, [identity(2), identity(1)]),
        relation=Relation.LE,
        rhs=Fraction(1, 2),
    )
    refusal = check_licensed_only(
        (scalar, general), source_segment_is_non_empty=True
    )
    assert refusal is not None
    assert refusal.reason is RefusalReason.GENERAL_ENTRY_BESIDE_SOURCE_SEGMENT
    assert "entry 2" in refusal.detail
    assert "ass:nosrc" not in refusal.detail
    assert (
        check_licensed_only((scalar, general), source_segment_is_non_empty=False)
        is None
    )


# ---------------------------------------------------------------------------
#  (G3)(a): the party-local form is a third LICENSED form, in either mode
# ---------------------------------------------------------------------------


def test_the_licensed_class_has_three_forms_and_general_is_not_one() -> None:
    """``def:eligible`` (G3)(a): a type check on the tag, comparing no numbers."""
    assert {RhsTag.HOMOGENEOUS, RhsTag.PARTY_LOCAL} == LICENSED_TAGS
    operator = BlockOperator.of(MEASURED, [identity(2), identity(1)])
    tagged = ConstraintEntry(
        operator=operator,
        relation=Relation.LE,
        rhs=Fraction(1, 8),
        arriving_tag=RhsTag.PARTY_LOCAL,
        scope=FACTOR,
    )
    untagged = ConstraintEntry(
        operator=operator, relation=Relation.LE, rhs=Fraction(1, 8)
    )
    general = ConstraintEntry(
        operator=operator, relation=Relation.LE, rhs=identity(2)
    )
    for marginal in (None, identity(1)):
        assert licensed_for_the_emitted_mode(marginal, (tagged,))
        assert licensed_for_the_emitted_mode(marginal, (untagged,))
        assert not licensed_for_the_emitted_mode(marginal, (general,))


def test_a_party_local_tag_is_the_arriving_field_and_never_inferred() -> None:
    """``def:homog``: "an entry arriving WITHOUT the tag is never read party-locally".

    The two entries below carry THE SAME DATUM, a real scalar, and differ only in
    the arriving field -- which is the one exception to the read-off-the-datum
    rule and is why V6 compares the field against the type instead.
    """
    operator = BlockOperator.of(MEASURED, [identity(2), identity(1)])
    untagged = ConstraintEntry(
        operator=operator, relation=Relation.LE, rhs=Fraction(1, 8)
    )
    tagged = ConstraintEntry(
        operator=operator,
        relation=Relation.LE,
        rhs=Fraction(1, 8),
        arriving_tag=RhsTag.PARTY_LOCAL,
    )
    assert untagged.tag is RhsTag.HOMOGENEOUS
    assert not untagged.is_party_local
    assert tagged.tag is RhsTag.PARTY_LOCAL
    assert tagged.is_party_local


def test_a_party_local_tag_beside_a_matrix_is_refused_by_the_tag_comparison() -> None:
    """V6: "refuses a ``party_local`` tag beside a matrix right-hand side"."""
    entry = ConstraintEntry(
        operator=BlockOperator.of(MEASURED, [identity(2), identity(1)]),
        relation=Relation.LE,
        rhs=BlockOperator.of(ALICE, [identity(1), identity(1)]),
        arriving_tag=RhsTag.PARTY_LOCAL,
        scope=FACTOR,
    )
    outcome = check_v6(_general_declaration(entries=(entry,)))
    assert not outcome.passed
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.CHECK_V6_FAILED


def test_a_party_local_entry_at_preceq_in_untrusted_mode_is_admitted() -> None:
    """The relation symbol is read by form, on the ``ex:two-party-shape`` shape.

    An untrusted-source declaration with a ``party_local`` entry declared at
    ``preceq``: D(vi) and V6 read the relation symbol BY FORM, so the entry is
    admitted. Under a mode-only reading it would be refused.
    """
    entry = ConstraintEntry(
        operator=BlockOperator.of(MEASURED, [matrix([[0, 0], [0, 0]]), identity(1)]),
        relation=Relation.LE,
        rhs=Fraction(1, 8),
        arriving_tag=RhsTag.PARTY_LOCAL,
        scope=FACTOR,
    )
    declaration = _general_declaration(trusted=False, entries=(entry,))
    assert check_v6(declaration).passed


# ---------------------------------------------------------------------------
#  (DX1), (DX3): the derived orders, and the per-factor readings
# ---------------------------------------------------------------------------


def test_the_product_sector_order_runs_the_last_factor_fastest() -> None:
    """(DX1): the digits of the product position, last factor fastest."""
    assert factor_sector_indices((2, 3), 0) == (0, 0)
    assert factor_sector_indices((2, 3), 1) == (0, 1)
    assert factor_sector_indices((2, 3), 3) == (1, 0)
    assert factor_sector_indices((3,), 2) == (2,)


def test_v1_compares_alices_declared_data_against_the_a_factors_map() -> None:
    """Without it a wrong Alice block kind would pass every check.

    "It is decided HERE AND NOWHERE ELSE, and without it a candidate whose Alice
    block list carried a different block kind, a different identifier list or a
    different order would pass every check and violate D(i)."
    """
    permuted = _sectors(("t1", 1), ("t0", 1))
    declaration = _general_declaration()
    slot = declaration.alice_slot
    assert slot is not None
    wrong = AliceSlot.of(
        AliceForm.POVM,
        slot.alphabet,
        tuple(
            BlockOperator.of(permuted, list(member.blocks)) for member in slot.members
        ),
    )
    moved = CandidateDeclaration(**{**declaration.__dict__, "alice_slot": wrong})
    outcome = check_v1(moved)
    assert not outcome.passed
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.SECTOR_MAP_MISMATCH


def test_v1_refuses_an_emitted_alphabet_that_is_not_the_derived_product() -> None:
    """(DX3): the product alphabet is DERIVED and is not a second choice."""
    declaration = _general_declaration()
    moved = CandidateDeclaration(
        **{**declaration.__dict__, "bob_alphabet": ("fl", "0", "1")}
    )
    outcome = check_v1(moved)
    assert not outcome.passed
    assert "product order" in str(outcome.refusal)


# ---------------------------------------------------------------------------
#  ``eq:feas-general``: per joint sector, and the party-local rows
# ---------------------------------------------------------------------------


def test_the_default_candidate_is_verified_per_joint_sector() -> None:
    """``eq:witness-general`` lies in ``Feas`` at an empty list (``thm:feasibility`` (i))."""  # noqa: E501
    declaration = _general_declaration()
    from certiqs_key.protocol_compiler.feasibility import default_witness

    candidate = default_witness(declaration)
    assert candidate.alice_sectors.count == 2
    assert len(candidate.blocks) == 2 * declaration.sectors.count
    verification = verify_witness(declaration, candidate)
    assert verification.passes, verification.failing_legs()


def test_a_party_local_entry_is_verified_ROW_BY_ROW_and_not_by_its_trace() -> None:
    """``ex:two-party-shape``'s own point, at one measured factor.

    The party-local reading is an operator relation per ``(t, s_{f^c})`` and the
    untagged reading is its trace: a state that satisfies the trace and violates
    one row is refused with the tag and admitted without it, which is
    ``def:homog``'s "the tag never weakens an entry".
    """
    flag = BlockOperator.of(MEASURED, [matrix([[0, 0], [0, 0]]), identity(1)])
    tagged = ConstraintEntry(
        operator=flag,
        relation=Relation.LE,
        rhs=Fraction(1, 8),
        arriving_tag=RhsTag.PARTY_LOCAL,
        scope=FACTOR,
    )
    untagged = ConstraintEntry(operator=flag, relation=Relation.LE, rhs=Fraction(1, 8))
    declaration = _general_declaration(trusted=False, entries=(tagged,))
    sectors = declaration.sectors
    # ALL OF THE FLAG WEIGHT ON ALICE'S FIRST SECTOR, and that sector carries 1/8
    # of the state. The UNTAGGED reading is the total flag weight, 1/8, which meets
    # the bound; the party-local ROW at t0 is 1/8 - (1/8)(1/8) > 0, which does not.
    # That is "it allows all of Bob's flag weight to sit where Alice's factor is in
    # one fixed state" (ex:two-party-shape), and "the tag never weakens an entry"
    # (def:homog) is the other side of it.
    blocks = []
    for alice in range(2):
        for position, dim in enumerate(sectors.dims):
            weight = Fraction(0)
            if alice == 0 and sectors.labels[position] == "fl":
                weight = Fraction(1, 8)
            elif alice == 1 and sectors.labels[position] == "d":
                weight = Fraction(7, 8)
            blocks.append(scale(weight, scale(Fraction(1, dim), identity(dim))))
    state = JointBlockOperator.of(sectors, declaration.alice_sectors, blocks)
    assert verify_witness(declaration, state).trace_one
    tagged_verdict = verify_witness(declaration, state)
    untagged_verdict = verify_witness(
        CandidateDeclaration(
            **{**declaration.__dict__, "constraint_list": (untagged,)}
        ),
        state,
    )
    assert not tagged_verdict.constraints
    assert untagged_verdict.constraints


# ---------------------------------------------------------------------------
#  (DX5): the transcript, and the degenerate two-message reading
# ---------------------------------------------------------------------------


def test_the_two_message_transcript_is_the_accepted_announcement_pair() -> None:
    """(DX5): the two maps ``a_A``, ``a_B`` ARE the transcript with ``L = 2``."""
    transcript = two_message_transcript(
        ("ok", "fl"),
        ("ok", "fl"),
        {"x0": "ok", "x1": "fl"},
        {"v0": "ok", "v1": "fl"},
        ("x0", "x1"),
        ("v0", "v1"),
    )
    assert transcript.length == 2
    assert transcript.senders == ("A", "B")
    assert transcript.joint_alphabet() == (
        ("ok", "ok"),
        ("ok", "fl"),
        ("fl", "ok"),
        ("fl", "fl"),
    )
    readout = {"A": "x1", "B": "v0"}
    assert transcript.joint_announcement(lambda party: readout[party]) == ("fl", "ok")


def test_a_message_that_reads_an_earlier_one_is_expressible_and_total() -> None:
    """``ex:transcript``'s shape: Bob's message depends on Alice's earlier one.

    "With two maps ``a_A`` on ``O_A`` and ``a_B`` on ``O_B``, Bob's announcement
    is a function of ``v`` alone and CANNOT DEPEND ON THE ROUND TYPE"; here the
    dependence is in the SIGNATURE, and party computability holds by it.
    """
    first = Message(
        sender="A",
        alphabet=("test", "gen"),
        table={("x_test", ()): "test", ("x_gen", ()): "gen"},
    )
    second = Message(
        sender="B",
        alphabet=("0", "click"),
        table={
            (readout, (kappa,)): ("0" if kappa == "test" else "click")
            for readout in ("v0",)
            for kappa in ("test", "gen")
        },
    )
    transcript = AnnouncementTranscript(messages=(first, second))
    assert transcript.missing_cell({"A": ("x_test", "x_gen"), "B": ("v0",)}) is None
    readout = {"A": "x_test", "B": "v0"}
    assert transcript.joint_announcement(lambda p: readout[p]) == ("test", "0")
    readout = {"A": "x_gen", "B": "v0"}
    assert transcript.joint_announcement(lambda p: readout[p]) == ("gen", "click")


def test_an_untabulated_transcript_cell_is_located_and_never_defaulted() -> None:
    """V1's totality clause has a datum: the first missing cell, in order."""
    message = Message(sender="A", alphabet=("ok",), table={("x0", ()): "ok"})
    transcript = AnnouncementTranscript(messages=(message,))
    assert transcript.missing_cell({"A": ("x0", "x1")}) == (0, "x1", ())
    with pytest.raises(Exception, match="not tabulated"):
        transcript.joint_announcement(lambda _: "x1")


def test_no_lifted_operator_is_formed_where_a_scoped_entry_is_verified() -> None:
    """THE LIFTED OPERATOR IS FORMED BY NO ONE, and this is what would catch it.

    The interface's ``constraint_entries.scope_and_tag`` row: "IT NEVER FORMS THE
    LIFTED OPERATOR ``1 (x) O_k (x) 1`` as a datum, AT ANY STEP, V7'S LEGS
    INCLUDED: a constraint value is computed by contracting a joint block against
    ``O_k``'s block on its own tensor factor". A Kronecker product IS how a lift is
    built, so the test is that none is taken while a scoped entry's rows are
    verified: :func:`~certiqs_key.foundations.exact.kron` is replaced by a function that
    fails, and the verification runs to a verdict anyway.

    THE DEFAULT CANDIDATE IS BUILT BEFORE THE PATCH, deliberately: ``omega^*`` of
    ``eq:witness-general`` is ``tau_A^(t) (x) 1_{Q_s}/d_Q``, which IS a Kronecker
    product and is licensed to be one -- it is a candidate the compiler exhibits on
    one joint block, not a lifted constraint operator. What this test pins is the
    VERIFICATION path, which is where the row's sentence bites.
    """
    from certiqs_key.protocol_compiler import feasibility

    flag = BlockOperator.of(MEASURED, [matrix([[0, 0], [0, 0]]), identity(1)])
    entry = ConstraintEntry(
        operator=flag,
        relation=Relation.LE,
        rhs=Fraction(1, 8),
        arriving_tag=RhsTag.PARTY_LOCAL,
        scope=FACTOR,
    )
    declaration = _general_declaration(trusted=False, entries=(entry,))
    candidate = feasibility.default_witness(declaration)

    def refuse(*_: object) -> None:
        raise AssertionError(
            "a Kronecker product was formed while a scoped entry was verified; "
            "the lifted operator 1 (x) O_k (x) 1 is formed by no one, V7's legs "
            "included (def:declaration (DX6); thm:feasibility (ii), the general format)"
        )

    original = feasibility.kron
    feasibility.kron = refuse  # type: ignore[assignment]
    try:
        verdict = feasibility.verify_witness(declaration, candidate)
    finally:
        feasibility.kron = original  # type: ignore[assignment]
    assert verdict.trace_one


def test_a_scope_is_a_factor_label_and_never_a_party_label() -> None:
    """Two measured factors of ONE party are told apart, which a party cannot do.

    ``reductions``' factor emission declares a LABEL per factor and carries the
    party beside it, and two factors may share a party -- two stations of one
    party. A scope compared against party labels would admit an entry scoped to
    either of them and refuse neither, which is the direction
    ``constraint_scope_not_a_factor`` exists to close; so the comparison is
    against the factor labels, and the party label of a factor is NOT one of them.
    """
    declaration = _general_declaration()
    assert declaration.measured_factor_labels == (FACTOR,)
    assert declaration.measured_factor(FACTOR) is not None
    # The PARTY label of the same factor names no factor.
    assert declaration.measured_factor(str(Party.BOB)) is None

    second = _sectors(("u", 1),)
    two_stations = FactorisedSectorMap(
        factors=(
            SectorFactor(
                party=str(Party.BOB),
                sectors=MEASURED,
                system=SystemTag.Q,
                label="left",
            ),
            SectorFactor(
                party=str(Party.BOB),
                sectors=second,
                system=SystemTag.Q,
                label="right",
            ),
        )
    )
    assert two_stations.labels_of(SystemTag.Q) == ("left", "right")


def test_a_factor_that_declares_no_label_takes_its_position_default() -> None:
    """``f<position>``, 0-based on its own side, which is reductions' own default.

    So a declaration built from that emission and one built by hand name the same
    factor the same way, and today's single-factor declaration -- which declares no
    factor list at all -- has the scope ``f0``, which is "with one measured factor
    the scope is that factor" (DX6).
    """
    plain = FactorisedSectorMap(
        factors=(
            SectorFactor(party="A", sectors=ALICE, system=SystemTag.A),
            SectorFactor(party="B", sectors=MEASURED, system=SystemTag.Q),
        )
    )
    # THE POSITION IS THE ONE ON ITS OWN SIDE: the A factor is f0 of the A side and
    # the Q factor is f0 of the Q side, which is the side a scope is compared
    # against.
    assert plain.labels_of(SystemTag.A) == ("f0",)
    assert plain.labels_of(SystemTag.Q) == ("f0",)
    declaration = _general_declaration()
    accepted = CandidateDeclaration(
        **{
            **declaration.__dict__,
            "sector_factorisation": None,
            "alice_slot": None,
            "alice_marginal_blocks": None,
            "bob_factors": None,
            "alice_povm": {"x0": identity(2), "x1": identity(2)},
        }
    )
    assert accepted.measured_factor_labels == ("f0",)


def test_a_repeated_factor_label_is_refused_rather_than_disambiguated() -> None:
    """A scope that named two factors could not be refused, so the list is refused."""
    clash = FactorisedSectorMap(
        factors=(
            SectorFactor(
                party="B", sectors=MEASURED, system=SystemTag.Q, label="same"
            ),
            SectorFactor(
                party="C",
                sectors=_sectors(("u", 1)),
                system=SystemTag.Q,
                label="same",
            ),
        )
    )
    with pytest.raises(Exception, match="repeated"):
        clash.labels_of(SystemTag.Q)


# ---------------------------------------------------------------------------
#  THE DOCKING POINT: real `reduce_factors` output, not a hand-built record
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_real_factor_emission_docks_and_its_labels_and_scopes_survive() -> None:
    """``reductions``' own emission, through the ONE docking function.

    The records in this file are hand-built because ``def:validator`` is stated on
    a candidate; THIS ONE IS NOT. It runs
    :func:`certiqs_key.reductions.factors.reduce_factors` on a pair of flat
    instances and docks the emission with
    :func:`~certiqs_key.protocol_compiler.docking_reductions.factorised_slots`, so
    that what the compiler's checks read is the producer's output and not this
    file's idea of it.

    WHAT IT PINS, and each is a seam the merge could have moved. The factor
    LABELS reach the declaration and are what a scope is compared against -- one
    caller-named (``left``), one at the position default (``f1``) -- so the party
    labels, which are ``Alice`` and ``Bob`` here, name no factor. Every emitted
    entry is scoped to a declared factor and arrives tagged ``party_local``, and V6
    admits it in untrusted-source mode BY FORM. And V1's four-component comparison
    runs factor by factor against the emitted maps.
    """
    from reductions_support import flat_call

    from certiqs_key.protocol_compiler.docking_reductions import factorised_slots
    from certiqs_key.reductions.factors import FactorCall, reduce_factors
    from certiqs_key.reductions.wpfss import FlatInstanceBuilder

    kind = "proof_sector"
    second_letters = ("z_empty", "z_1", "z_2", "z_mc")
    outcome = reduce_factors(
        [
            FactorCall(
                call=flat_call(party="Alice", route="licensed"),
                builder=FlatInstanceBuilder(),
                sector_block_kind=kind,
                factor_label="left",
            ),
            FactorCall(
                call=flat_call(
                    party="Bob", letters=second_letters, route="licensed"
                ),
                builder=FlatInstanceBuilder(),
                sector_block_kind=kind,
            ),
        ]
    )
    assert outcome.refusal is None
    emission = outcome.emission
    assert emission is not None
    slots = factorised_slots(emission, sector_block_kind=kind)

    assert slots.sector_factorisation.labels_of(SystemTag.Q) == ("left", "f1")
    assert emission.parties == ("Alice", "Bob")
    assert slots.constraint_entries
    assert {entry.scope for entry in slots.constraint_entries} == {"left", "f1"}
    assert all(
        entry.tag is RhsTag.PARTY_LOCAL for entry in slots.constraint_entries
    )
    assert slots.attack_set_license is not None
    assert "left:" in slots.attack_set_license.statement
    assert "f1:" in slots.attack_set_license.statement

    x_alphabet = ("x0",)
    v_alphabet = slots.bob_alphabet
    partition = default_party_partition(x_alphabet, v_alphabet)
    declaration = CandidateDeclaration(
        alice_dim=1,
        alice_marginal=None,
        sectors=slots.sectors,
        alice_alphabet=x_alphabet,
        alice_povm={"x0": identity(1)},
        bob_alphabet=v_alphabet,
        bob_povm={},
        partition=partition,
        announce_alice=dict.fromkeys(x_alphabet, "ok"),
        announce_bob=dict.fromkeys(v_alphabet, "ok"),
        alice_announcement_alphabet=("ok",),
        bob_announcement_alphabet=("ok",),
        acceptance_alphabet=("c",),
        accept_statistic={("ok", "ok"): "c"},
        key_map={(x, v): 0 for x in x_alphabet for v in v_alphabet},
        key_alphabet=(0,),
        key_holder=Party.ALICE,
        constraint_list=slots.constraint_entries,
        sector_factorisation=slots.sector_factorisation,
        bob_factors=slots.bob_factors,
    )
    assert declaration.is_general_format
    assert declaration.measured_factor_labels == ("left", "f1")
    # THE PARTY LABELS NAME NO FACTOR, which is the whole point of the label.
    assert declaration.measured_factor("Alice") is None
    assert declaration.measured_factor("Bob") is None
    for check in (check_v1, check_v3, check_v6):
        verdict = check(declaration)
        assert verdict.passed, (verdict.check, verdict.refusal)
