"""The general format's declaration: derivations, the degenerate case, refusals.

``def:declaration`` (DX1)-(DX6) and ``def:admissible-declaration``'s general-format
paragraph. Every refusal of
:mod:`certiqs_key.meat_core.declaration.general_validation` has a test here,
because a refusal nobody exercises is a refusal nobody has.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from tests.support.general_toys import (
    BB84_ELEMENTS,
    BB84_LETTERS,
    decoy_like_general,
    qubit_bb84_general,
    two_factor_general,
)

from certiqs_key.domain.manifest import ConstraintRelation, KeyHolder
from certiqs_key.meat_core.declaration.general import (
    SEPARATOR,
    AliceForm,
    GeneralConstraintEntry,
    GeneralRhsTag,
    Message,
    Transcript,
    general_from_accepted,
    sector_axis,
    two_message_transcript,
)
from certiqs_key.meat_core.declaration.general_validation import (
    validate_general_declaration,
)
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.general_docking import WIRE_KEYS, dock_general_declaration


def test_the_two_message_toy_is_the_accepted_format_entry_for_entry() -> None:
    """``def:declaration``: the accepted format is the degenerate case."""
    declaration = qubit_bb84_general()
    assert declaration.is_degenerate
    accepted = declaration.as_accepted()
    assert accepted.alice_dim == 2
    assert accepted.sector_index_set == ("q",)
    assert accepted.alice_outcomes == BB84_LETTERS
    assert accepted.announce_alice == {"z0": "Z", "z1": "Z", "x0": "X", "x1": "X"}
    # The round trip: the embedding of the accepted declaration is this one on
    # every component a derivation reads.
    again = general_from_accepted(accepted)
    assert again.is_degenerate
    assert again.sector_index_set == declaration.sector_index_set
    assert again.bob_outcomes == declaration.bob_outcomes
    for x in BB84_LETTERS:
        assert np.array_equal(
            again.alice_block(x, "t0"), declaration.alice_block(x, "t0")
        )


def test_a_three_message_transcript_is_not_the_accepted_format() -> None:
    """(DX5): the two accepted maps are ``L = 2`` with the second reading nothing."""
    declaration = qubit_bb84_general(messages=3)
    assert not declaration.is_degenerate
    assert declaration.transcript.length == 3
    assert declaration.announcement("z0", "z0") == ("Z", "Z", "keep")
    assert declaration.announcement("z0", "x0") == ("Z", "X", "drop")
    with pytest.raises(TypeError, match="not of the accepted format"):
        declaration.as_accepted()


def test_the_two_message_transcript_recognises_the_accepted_pair() -> None:
    """``two_message_transcript`` builds the degenerate case of ``eq:transcript``."""
    transcript = two_message_transcript({"a": "cA"}, {"b": "cB"})
    assert transcript.is_two_independent_messages
    assert transcript.announcement({KeyHolder.ALICE: "a", KeyHolder.BOB: "b"}) == (
        "cA",
        "cB",
    )


def test_the_product_map_and_alphabet_run_the_last_factor_fastest() -> None:
    """(DX1), ``eq:productmap``, and (DX3)'s product alphabet."""
    declaration = two_factor_general(party_local=False)
    assert declaration.sector_index_set == (f"qA{SEPARATOR}qB",)
    assert declaration.sector_dims[f"qA{SEPARATOR}qB"] == 4
    assert declaration.bob_outcomes[0] == f"z0{SEPARATOR}z0"
    assert declaration.bob_outcomes[1] == f"z0{SEPARATOR}z1"
    assert declaration.split_letter(f"x0{SEPARATOR}z1") == ("x0", "z1")


def test_the_joint_sectors_run_t_slowest() -> None:
    """(DX1): "the pairs ``(t, s)``, ordered with ``t`` slowest"."""
    declaration = decoy_like_general()
    assert declaration.joint_sectors == (
        ("vacuum", "q"),
        ("one", "q"),
        ("flag", "q"),
        ("rank1", "q"),
    )
    assert declaration.joint_block_dim("one", "q") == 4


def test_the_product_block_is_the_kronecker_product_of_the_declared_factors() -> None:
    """(DX3), ``eq:productfamily``: formed in floating point, inside the objective."""
    declaration = two_factor_general(party_local=False)
    letter = f"z0{SEPARATOR}x1"
    sector = f"qA{SEPARATOR}qB"
    expected = np.kron(BB84_ELEMENTS["z0"], BB84_ELEMENTS["x1"])
    assert np.allclose(declaration.bob_block(letter, sector), expected, atol=0.0)


def test_the_zero_predicate_is_decided_per_factor() -> None:
    """``def:joint-sectors``: a product vanishes exactly when a factor does."""
    declaration = two_factor_general(party_local=False)
    sector = f"qA{SEPARATOR}qB"
    zeroed = dataclasses.replace(
        declaration.factors[1],
        blocks={
            v: {
                "qB": (
                    np.zeros((2, 2), dtype=np.complex128)
                    if v == "z1"
                    else block["qB"]
                )
            }
            for v, block in declaration.factors[1].blocks.items()
        },
    )
    declaration = dataclasses.replace(
        declaration, factors=(declaration.factors[0], zeroed)
    )
    assert declaration.bob_block_is_zero(f"z0{SEPARATOR}z1", sector)
    assert not declaration.bob_block_is_zero(f"z0{SEPARATOR}z0", sector)


def test_alice_zero_is_read_off_the_declared_block_in_either_form() -> None:
    """``def:joint-sectors``: the zero predicate is decided on DECLARED data.

    ``lem:ensemble-form`` (iii) -- ``M_x^{(t)} = 0`` iff ``N_x^{(t)} = 0`` -- is
    stated of the POVM a declared ``{N_x}`` DENOTES, whose completion is
    proportional to ``tr N_x`` off ``supp tau_A^{(t)}``. So the two predicates
    agree wherever ``tau_A^{(t)}`` is nonsingular, and on a SINGULAR sector a
    POVM-form ``M_x`` supported off the marginal's support has
    ``tau^{1/2} M_x tau^{1/2} = 0``: the two declarations are then different
    declarations, not two readings of one, and the asymmetry is recorded here
    rather than asserted away. WHAT CANNOT DIFFER IS THE OBJECTIVE, which reads
    Alice's side only through ``N^W_x`` (``lem:choi-factor`` (iii)); the
    predicate difference can only classify a pair as key-ACTIVE, which computes
    a deficit instead of skipping an identically zero one.
    """
    povm = decoy_like_general()
    ensemble = decoy_like_general(ensemble=True)
    for x in BB84_LETTERS:
        for sector in ("vacuum", "one", "flag"):
            assert povm.alice_block_is_zero(x, sector) == ensemble.alice_block_is_zero(
                x, sector
            )
    assert povm.alice_block_is_zero("z1", "flag")
    assert not povm.alice_block_is_zero("z0", "flag")
    # The singular sector, where the two declarations part company.
    assert not povm.alice_block_is_zero("z1", "rank1")
    assert ensemble.alice_block_is_zero("z1", "rank1")


def test_every_toy_is_exactly_admissible() -> None:
    """The exact-admissibility paragraph, decided per factor and per ``t``."""
    for declaration in (
        qubit_bb84_general(),
        qubit_bb84_general(ensemble=True),
        qubit_bb84_general(messages=3),
        decoy_like_general(),
        decoy_like_general(ensemble=True),
        two_factor_general(party_local=True),
        two_factor_general(party_local=False),
    ):
        admission = validate_general_declaration(declaration)
        assert len(admission.per_factor) == len(declaration.factors)
        assert all(admission.alice_rounds_nowhere_per_sector.values())


# ---------------------------------------------------------------------------
#  The refusals, one test each
# ---------------------------------------------------------------------------


def test_a_declaration_with_no_measured_factor_is_refused() -> None:
    """(DX1): "at least one factor is tagged ``Q``"."""
    declaration = dataclasses.replace(qubit_bb84_general(), factors=())
    with pytest.raises(DeclarationError, match=r"\(DX1\)"):
        validate_general_declaration(declaration)


def test_a_factor_label_carrying_the_product_separator_is_refused() -> None:
    """(DX1), (DX3): a product identifier must say which factor supplied what."""
    declaration = two_factor_general(party_local=False)
    broken = dataclasses.replace(
        declaration.factors[0], sectors=sector_axis([(f"q{SEPARATOR}A", 2)])
    )
    broken = dataclasses.replace(
        broken, blocks={v: {f"q{SEPARATOR}A": BB84_ELEMENTS[v]} for v in BB84_LETTERS}
    )
    with pytest.raises(DeclarationError, match="separator"):
        validate_general_declaration(
            dataclasses.replace(declaration, factors=(broken, declaration.factors[1]))
        )


def test_the_ensemble_form_is_refused_in_untrusted_source_mode() -> None:
    """(DX4): the ensemble form "exists in trusted-source mode only"."""
    declaration = dataclasses.replace(
        two_factor_general(party_local=False), alice_form=AliceForm.ENSEMBLE
    )
    with pytest.raises(DeclarationError, match="TRUSTED-source mode only"):
        validate_general_declaration(declaration)


def test_a_vanishing_marginal_block_is_refused_in_ensemble_form() -> None:
    """``eq:ensembleform``: the side condition ``tau_A^{(t)} != 0``."""
    declaration = qubit_bb84_general(ensemble=True)
    declaration = dataclasses.replace(
        declaration,
        alice_marginal={"t0": np.zeros((2, 2), dtype=np.complex128)},
        alice_operators={
            x: {"t0": np.zeros((2, 2), dtype=np.complex128)} for x in BB84_LETTERS
        },
    )
    with pytest.raises(DeclarationError, match="tau_A"):
        validate_general_declaration(declaration)


def test_an_ensemble_sum_that_is_not_the_marginal_is_refused() -> None:
    """``eq:ensembleform``: ``sum_x N_x^{(t)} = tau_A^{(t)}``, decided exactly."""
    declaration = qubit_bb84_general(ensemble=True)
    operators = {x: dict(blocks) for x, blocks in declaration.alice_operators.items()}
    operators["z0"]["t0"] = operators["z0"]["t0"] * 0.5
    with pytest.raises(DeclarationError, match="eq:ensembleform"):
        validate_general_declaration(
            dataclasses.replace(declaration, alice_operators=operators)
        )


def test_an_incomplete_alice_povm_is_refused() -> None:
    """The ``alice_povm_exact`` row, read per Alice sector."""
    declaration = qubit_bb84_general()
    operators = {x: dict(blocks) for x, blocks in declaration.alice_operators.items()}
    operators["x1"]["t0"] = operators["x1"]["t0"] * 0.5
    with pytest.raises(DeclarationError, match="EXACTLY 0"):
        validate_general_declaration(
            dataclasses.replace(declaration, alice_operators=operators)
        )


def test_a_marginal_whose_blocks_do_not_sum_to_one_is_refused() -> None:
    """Admissibility (ii): ``tr tau_A = 1``, accumulated over the blocks in order."""
    declaration = decoy_like_general()
    marginal = dict(declaration.alice_marginal or {})
    marginal["flag"] = marginal["flag"] * 0.5
    with pytest.raises(DeclarationError, match=r"def:admissible-declaration \(ii\)"):
        validate_general_declaration(
            dataclasses.replace(declaration, alice_marginal=marginal)
        )


def test_a_general_entry_is_refused_in_untrusted_source_mode() -> None:
    """Admissibility (vi): a ``general`` ``Theta_k`` does not exist there."""
    declaration = two_factor_general(party_local=False)
    entry = dataclasses.replace(
        declaration.constraint_list[0],
        rhs_tag=GeneralRhsTag.GENERAL,
        bound={"t0": np.eye(1, dtype=np.complex128)},
    )
    with pytest.raises(DeclarationError, match=r"def:admissible-declaration \(vi\)"):
        validate_general_declaration(
            dataclasses.replace(declaration, constraint_list=(entry,))
        )


def test_an_entry_scoped_to_no_declared_factor_is_refused() -> None:
    """(DX6): the scope names one measured factor."""
    declaration = two_factor_general(party_local=True)
    entry = dataclasses.replace(declaration.constraint_list[0], scope="nowhere")
    with pytest.raises(DeclarationError, match="declares the scope"):
        validate_general_declaration(
            dataclasses.replace(declaration, constraint_list=(entry,))
        )


def test_a_party_local_entry_carrying_an_operator_is_refused() -> None:
    """``def:homog``, the party-local form: it carries a real ``c_k``."""
    declaration = two_factor_general(party_local=True)
    entry = GeneralConstraintEntry(
        scope="fB",
        operator_blocks={"qB": np.eye(2, dtype=np.complex128)},
        relation=ConstraintRelation.PRECEQ,
        bound={"t0": np.eye(1, dtype=np.complex128)},
        rhs_tag=GeneralRhsTag.PARTY_LOCAL,
    )
    with pytest.raises(TypeError, match="no scalar c_k"):
        validate_general_declaration(
            dataclasses.replace(declaration, constraint_list=(entry,))
        )


def test_a_key_that_its_holder_cannot_compute_is_refused() -> None:
    """Admissibility (viii), ``eq:partycomp``, for a transcript protocol."""
    declaration = qubit_bb84_general()
    key = dict(declaration.key_map)
    key[("z0", "z0")] = 1
    key[("z0", "z1")] = 0
    with pytest.raises(DeclarationError, match="eq:partycomp"):
        validate_general_declaration(dataclasses.replace(declaration, key_map=key))


def test_sifting_that_is_not_announcement_determined_is_refused() -> None:
    """``def:admissible-declaration`` (v): ``r = perp`` exactly when the class fails."""
    declaration = qubit_bb84_general()
    key = dict(declaration.key_map)
    key[("z0", "z0")] = None
    with pytest.raises(DeclarationError, match=r"def:admissible-declaration \(v\)"):
        validate_general_declaration(dataclasses.replace(declaration, key_map=key))


def test_a_transcript_table_that_is_not_total_is_refused() -> None:
    """Admissibility (i): all maps total, including every message table."""
    declaration = qubit_bb84_general()
    first, second = declaration.transcript.messages
    partial = Message(
        sender=second.sender,
        alphabet=second.alphabet,
        table={
            key: value
            for key, value in second.table.items()
            if key[0] != "x1"
        },
    )
    with pytest.raises(DeclarationError, match="not total"):
        validate_general_declaration(
            dataclasses.replace(
                declaration, transcript=Transcript(messages=(first, partial))
            )
        )


# ---------------------------------------------------------------------------
#  The docking module
# ---------------------------------------------------------------------------


def test_docking_without_general_slots_returns_the_degenerate_embedding() -> None:
    """The absence of every general-format key IS today's format."""
    accepted = qubit_bb84_general().as_accepted()
    docked = dock_general_declaration(accepted)
    assert docked.is_degenerate
    assert docked.as_accepted().sector_index_set == accepted.sector_index_set


def test_docking_general_slots_validates_them() -> None:
    """A supplied slot is admitted before anything is computed from it."""
    accepted = qubit_bb84_general().as_accepted()
    general = decoy_like_general()
    from certiqs_key.meat_core.general_docking import GeneralSlots

    docked = dock_general_declaration(
        accepted,
        GeneralSlots(
            alice=general.alice,
            alice_marginal=general.alice_marginal,
            alice_operators=general.alice_operators,
        ),
    )
    assert docked.alice_sectors == ("vacuum", "one", "flag", "rank1")
    assert not docked.is_degenerate


def test_the_wire_keys_are_named_for_the_merge() -> None:
    """Every key the general format adds is listed with what it fills."""
    assert set(WIRE_KEYS) == {
        "sector_factorisation",
        "alice_form",
        "alice_ensemble",
        "alice_povm_blocks",
        "alice_marginal_blocks",
        "bob_povm_factors",
        "transcript",
        "constraint_list[].scope",
        "constraint_rhs_tag",
        "alice_alphabet",
        "acceptance_values",
        "key_value_count",
        "accept_statistic",
        "key_map",
    }
    assert all(WIRE_KEYS.values())


# ---------------------------------------------------------------------------
#  def:classes in the general format
# ---------------------------------------------------------------------------


def test_removable_is_off_for_every_sector_on_both_grounds() -> None:
    """``def:classes``, the general format, and the two grounds it names."""
    from tests.support.general_toys import maps_of

    from certiqs_key.meat_core.declaration.general_sectors import (
        RemovableRefusal,
        general_sector_report,
        removable_refusals,
    )

    tagged = two_factor_general(party_local=True)
    assert set(removable_refusals(tagged)) == {
        RemovableRefusal.PARTY_LOCAL_ENTRY,
        RemovableRefusal.SEVERAL_MEASURED_FACTORS,
    }
    scalar = two_factor_general(party_local=False)
    assert removable_refusals(scalar) == (
        RemovableRefusal.SEVERAL_MEASURED_FACTORS,
    )
    report = general_sector_report(maps_of(tagged))
    assert all(not record.removable for record in report.records)
    assert report.joint_pairs["sifted"]
    # A declaration with several Alice sectors and ONE factor carries neither
    # ground, and the flag is still off because no witness is exhibited here.
    decoy = general_sector_report(maps_of(decoy_like_general()))
    assert all(not record.removable for record in decoy.records)
    assert decoy.removable_refused_because == ()


def test_state_blindness_is_decided_per_factor_at_no_window() -> None:
    """``def:classes`` (c): a block only NEARLY scalar is not state-blind."""
    from certiqs_key.meat_core.declaration.general_sectors import is_state_blind

    declaration = decoy_like_general()
    assert not is_state_blind(declaration, "q")
