"""Docking an emitted declaration into the consuming engine, both ends unadjusted.

The two validator sets are kept APART: this
module implements its own V1-V8 from Definition ``def:validator``, and
the consuming engine's own ``validate_declaration`` implements the
consuming engine's def:admissible-declaration independently. NEITHER WAS WRITTEN AGAINST
THE OTHER AND NEITHER IS ADJUSTED FOR THE OTHER HERE. That is the whole value of this
file: it is a cross-check of two implementations of overlapping mathematics
written from two contracts, and a disagreement is a finding rather than a
merge conflict.

WHAT IS SUPPLIED BY THE TEST AND NOT BY THE COMPILER
====================================================
``acceptance_set``, ``rounds`` and the key-length ``parameters`` are built HERE,
in a fixture that says in its own name that they are not this module's. Section
2.2's preamble names the first two as inputs of the consuming engine that are
NOT outputs of this module, and Section 2.4 says this module has no free
numerical parameter at all. ``protocol_compiler.docking.dock_declaration``
requires them as keyword arguments precisely so that a caller cannot forget
whose they are.

THE ASYMMETRY IS ASSERTED, NOT PAPERED OVER
===========================================
Not every refusal of this module has a consumer analogue, and the one that does
not is V7. The consumer's own validation module says so in its docstring: with
a non-empty constraint list, non-emptiness of the feasible set "is a
semidefinite feasibility question; it is decided by the linear oracle at solve
time". This module instead demands a WITNESS (Theorem ``thm:feasibility`` (ii),
Remark ``rem:nosearch``). So a declaration this module refuses at V7 may be
accepted by the consumer's validator and refused later, at a different place,
by a different mechanism -- and :func:`test_v7_has_no_consumer_analogue`
records that rather than hiding it.
"""

from __future__ import annotations

from fractions import Fraction as F

import numpy as np
import pytest
from instances.bb84.specification import bb84_specification
from protocol_blocks import NotBlockDiagonalError, as_blocks

from certiqs_key.domain.constraints import Relation
from certiqs_key.domain.manifest import Constraint as WireConstraint
from certiqs_key.domain.manifest import ConstraintRelation, KeyHolder
from certiqs_key.domain.manifest import Declaration as WireDeclaration
from certiqs_key.foundations.blocks import BlockKind, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import matrix, scale
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    KeyLengthParameters,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.declaration.validation import validate_declaration
from certiqs_key.meat_core.docking import (
    RELATION_TO_CONSUMER,
    dock_declaration,
    sector_blocks,
    to_complex128,
    transported_entry_count,
)
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.protocol_compiler import (
    DECLARATION_SLOT_KEYS,
    CandidateDeclaration,
    compile_specification,
)

#: THE CONSUMER TYPES THIS FILE DOCKS INTO ARE IMPORTED: ``docking`` --
#: ``dock_declaration`` and the conversion it performs -- uses the consumer's
#: ``ProtocolDeclaration``, ``AcceptanceSet``, ``KeyLengthParameters`` and
#: ``validate_declaration``.
#:
#: ``docking.py`` is :mod:`certiqs_key.meat_core.docking`, because imports
#: point downward only (PRINCIPLES.md section 4) and THE CONSUMER READS THE
#: SUPPLIER. What this file tests is the compiler's emission against
#: the consumer's own validator, with neither validator written against the
#: other and neither adjusted for the other here.
#: The block kind every fixture below declares: the shared format's
#: ``proof_sector`` (:class:`~certiqs_key.foundations.blocks.BlockKind`,
#: spec/architecture.md 2.9, a frozen type of the shared format). The contract
#: NAMES the datum and the format FIXES the values, so open choice
#: ``OC-sector-block-kind`` is narrowed within that alphabet and still not
#: decided. ``proof_sector`` is the member these fixtures ARE: their
#: decomposition is "justified by dephasing or SOURCE REPLACEMENT", not photon
#: number (``physical_sector``) and not solver sparsity (``numerical_block``).
#: See :func:`instances.bb84.specification.band_a_block_kind` for the reading.
FIXTURE_BLOCK_KIND = BlockKind.PROOF_SECTOR

_QUTRIT_MAP = SectorStructure(
    labels=("s0", "s1"), dims=(2, 1), block_kind=FIXTURE_BLOCK_KIND
)
_QUBIT_MAP = SectorStructure(labels=("s0",), dims=(2,), block_kind=FIXTURE_BLOCK_KIND)

# THE SKIP MARK IS GONE AND THE OTHER TWO STAY: this file's tests are
# `contract` and `oracle` tests and are run as such now that their subject is
# here. What was deferred was the SUBJECT, not the tier.
pytestmark = [pytest.mark.contract, pytest.mark.oracle]


def _not_this_modules_inputs() -> tuple[AcceptanceSet, int, KeyLengthParameters]:
    """Return the three data the CALLER owns, with their owners named.

    ``acceptance_set``  -- ``statistics-acceptance``. This module emits the
                           acceptance ALPHABET, never the set.
    ``rounds``          -- a run parameter; no module emits it.
    ``parameters``      -- the consuming engine's Section 2.4, not this
                           contract's, whose ``alpha`` row says in as many
                           words that it is "not a parameter of this contract".
    """
    return (
        AcceptanceSet(geometry="singleton", frequencies=(1.0, 0.0, 0.0, 0.0)),
        1_000_000,
        KeyLengthParameters(
            alpha=1.05, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=200_000
        ),
    )


def _bb84_declaration() -> CandidateDeclaration:
    """Return the emitted Band-A BB84 declaration."""
    result = compile_specification(
        bb84_specification(F(7, 8), F(1, 8), F(3, 4), F(1, 4))
    )
    assert result.refuses is False
    assert result.declaration is not None
    return result.declaration


#: THE OPTIONAL KEYS OF SCHEMA 0.4.0 OF THE WIRE ``Declaration``, each present
#: ONLY in the general format of ``def:declaration`` (DX1)--(DX6) and each absent
#: from the accepted format. Listed here rather than inline because two tests read
#: the same list and because a reader of a frozen expectation should be able to
#: see WHICH keys are general-format beside the assertion that the rest do not
#: cross.
GENERAL_FORMAT_WIRE_KEYS: frozenset[str] = frozenset(
    {
        "sector_factorisation",
        "alice_form",
        "alice_marginal_blocks",
        "alice_povm_blocks",
        "alice_ensemble",
        "bob_povm_factors",
        "transcript",
        "accept_statistic_general",
    }
)


# ---------------------------------------------------------------------------
#  The shared keys ARE the consumer's declaration minus its two
# ---------------------------------------------------------------------------


def test_the_seventeen_declaration_slots_and_the_two_the_wire_lacks() -> None:
    """Section 2.2's coincidence, checked against the wire format as it stands.

    SEVENTEEN SLOTS: the sector map's third
    component ``sector_block_kind`` and the per-entry ``constraint_rhs_tag``
    are on the wire (Definition ``def:declaration``; Definition ``def:homog``).

    THE WIRE FORMAT CARRIES BOTH, and they sit at the two
    levels the mathematics puts them at: ``sector_block_kind`` is a key of the
    declaration, the sector map being ONE object carried with it, and
    ``constraint_rhs_tag`` is a key of each ENTRY, "emitted WITH EACH ENTRY so
    that the consuming engine's type check has a datum" (Definition
    ``def:homog``). This test fixes exactly that split, so that the tag cannot
    drift up to the declaration and become one tag for a whole list.

    The wire ``Declaration`` has the OPTIONAL general-format keys of schema
    0.4.0 -- ``def:declaration`` (DX1)--(DX6), listed in
    :data:`GENERAL_FORMAT_WIRE_KEYS` above -- and ``sector_factorisation`` is
    inside it. THE SEVENTEEN SLOTS are exactly the wire fields minus
    ``acceptance_set``, ``rounds`` and the general-format keys (including
    ``accept_statistic_general``, the transcript-tuple acceptance map required
    by DX5; the legacy map cannot encode arbitrary transcript lengths), and
    every one of those keys is ABSENT from a declaration of the accepted
    format, which is why both shipped instances' bundles are byte-identical.
    """
    wire_fields = set(WireDeclaration.model_fields)
    entry_fields = set(WireConstraint.model_fields)
    assert len(DECLARATION_SLOT_KEYS) == 17
    assert "sector_block_kind" in wire_fields
    assert "constraint_rhs_tag" in entry_fields
    assert "constraint_rhs_tag" not in wire_fields
    missing = set(DECLARATION_SLOT_KEYS) - wire_fields
    assert missing == {"constraint_rhs_tag"}
    assert wire_fields >= GENERAL_FORMAT_WIRE_KEYS
    assert wire_fields - {
        "acceptance_set",
        "rounds",
        "sector_block_kind",
        *GENERAL_FORMAT_WIRE_KEYS,
    } == (set(DECLARATION_SLOT_KEYS) - missing - {"sector_block_kind"})
    assert {"acceptance_set", "rounds"} <= wire_fields
    # THE ENTRY'S SCOPE IS AT THE ENTRY, as the tag is: (DX6) scopes an ENTRY to
    # one measured factor, so a scope at the declaration would be one scope for a
    # whole list, which is the drift this test exists to prevent.
    assert "scope" in entry_fields
    assert "scope" not in wire_fields


def test_the_six_compiler_only_keys_do_not_cross_the_boundary() -> None:
    """The compiler adds no key to the bundle's ``declaration`` table.

    TRUE OF THE ``declaration`` TABLE, deliberately. The one wire extension is
    the reduction chain, "recorded in the bundle as an ``exact`` reduction",
    and it lives on the manifest's PAYLOAD rather than inside ``declaration``,
    because ``declaration`` is exactly ``meat-core``'s Section 2.1 INPUT table
    and a reduction chain is a ``protocol-compiler`` OUTPUT key; Section 2.1
    typing and the frozen seventeen-field assertion in
    ``tests/oracles/test_protocol_compiler_registry.py`` fix that placement.
    So none of the six compiler-only keys is a key of the wire declaration,
    the seventeen-slot coincidence above holds, and ``meat-core``'s in-memory
    ``ProtocolDeclaration`` gains no field at all.
    """
    from certiqs_key.protocol_compiler import COMPILER_ONLY_KEYS

    wire_fields = set(WireDeclaration.model_fields)
    for key in COMPILER_ONLY_KEYS:
        assert key not in wire_fields, key
    consumer_fields = set(ProtocolDeclaration.__dataclass_fields__)
    for key in COMPILER_ONLY_KEYS:
        assert key not in consumer_fields, key
    assert "reduction_chain" not in wire_fields
    assert "reduction_chain" not in consumer_fields


# ---------------------------------------------------------------------------
#  The consumer's INDEPENDENT validator accepts what this module emits
# ---------------------------------------------------------------------------


def test_the_consumers_own_validator_accepts_the_emitted_declaration() -> None:
    acceptance_set, rounds, parameters = _not_this_modules_inputs()
    docked = dock_declaration(
        _bb84_declaration(),
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
    )
    # RAISES ON THE FIRST VIOLATION; a clean return is the whole assertion.
    validate_declaration(docked)


def test_the_chain_records_provenance_crosses() -> None:
    """The transported tail of ``CList``, read off the compiler's own record.

    WHY THE CONSUMER READS A COMPILER-ONLY KEY AT ALL. The count crosses as
    provenance carried into the run record's key-rate payload. Provenance is
    the producer's to state, and the producer states it in
    ``reduction_chain_record``: two segments in ``def:compile``'s
    concatenation order, each link carrying THE COUNT of entries it
    transported. The engine reads that count and derives nothing else from it
    -- no claim of the consuming module reads the datum, it decides no ledger
    row, and no number depends on it.

    BAND A HAS NO CHAIN, so the count is zero.
    """
    result = compile_specification(
        bb84_specification(F(7, 8), F(1, 8), F(3, 4), F(1, 4))
    )
    assert result.declaration is not None
    acceptance_set, rounds, parameters = _not_this_modules_inputs()
    docked = dock_declaration(
        result.declaration,
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
        reduction_chain_record=result.reduction_chain_record,
    )
    # THE RECORD IS PRESENT AND ITS SEGMENTS ARE EMPTY, which req:chain-record-slots is
    # the reason for: a record shape that omitted an empty segment "cannot
    # later distinguish 'no entries' from 'entries not carried'".
    assert result.reduction_chain_record["source_segment"] == []
    assert transported_entry_count(result.reduction_chain_record) == 0
    assert docked.constraints_through_a_reductions_chain == 0

    # THE COUNT IS THE SUM OVER BOTH SEGMENTS, in the order def:compile
    # concatenates them, so it names the trailing entries of CList.
    record = {
        "source_segment": [{"transported_constraints": 1}],
        "receiver_segment": [
            {"transported_constraints": 2},
            {"transported_constraints": 0},
        ],
    }
    assert transported_entry_count(record) == 3
    # THE DECLARATION IT IS DOCKED AGAINST CARRIES THREE ENTRIES, and that is
    # not fixture hygiene but the rule below: a record describing more
    # transported entries than the list it describes HAS is refused, so a
    # fixture pairing three transported entries with an empty list would
    # enshrine the state the guard forbids.
    from certiqs_key.domain.constraints import ConstraintEntry

    entry = ConstraintEntry(
        operator=as_blocks(_QUBIT_MAP, matrix(((1, 0), (0, 0)))),
        relation=Relation.GE,
        rhs=F(1, 4),
    )
    three = CandidateDeclaration(
        **{**result.declaration.__dict__, "constraint_list": (entry, entry, entry)}
    )
    carried = dock_declaration(
        three,
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
        reduction_chain_record=record,
    )
    assert carried.constraints_through_a_reductions_chain == 3
    assert len(carried.constraint_list) == 3

    # A RECORD THAT CONTRADICTS THE LIST IT DESCRIBES IS REFUSED like a
    # malformed one. It is the shape of disagreement sector_map_disagreement
    # is: a supplier record and the artefact it describes saying different
    # things, which this module refuses everywhere rather than reading
    # whichever it happens to hold. It can only arise by pairing two artefacts
    # from different compilations.
    two = CandidateDeclaration(
        **{**result.declaration.__dict__, "constraint_list": (entry, entry)}
    )
    with pytest.raises(MalformedInputError, match="not from one compilation"):
        dock_declaration(
            two,
            acceptance_set=acceptance_set,
            rounds=rounds,
            parameters=parameters,
            reduction_chain_record=record,
        )
    # AND THE BOUNDARY CASE IS ADMITTED: as many transported as the list has,
    # which is the whole-list case every reductions-emitted declaration is in.
    assert (
        dock_declaration(
            three,
            acceptance_set=acceptance_set,
            rounds=rounds,
            parameters=parameters,
            reduction_chain_record={
                "source_segment": [],
                "receiver_segment": [{"transported_constraints": 3}],
            },
        ).constraints_through_a_reductions_chain
        == 3
    )

    # AN ABSENT RECORD IS "NOT ESTABLISHED" AND IS NOT AN ERROR: a hand-built
    # declaration has no producer to have said otherwise, and the row it would
    # otherwise fire names a module that emitted nothing here.
    assert (
        dock_declaration(
            result.declaration,
            acceptance_set=acceptance_set,
            rounds=rounds,
            parameters=parameters,
        ).constraints_through_a_reductions_chain
        == 0
    )

    # AND A RECORD THIS FUNCTION CANNOT READ IS REFUSED RATHER THAN READ AS
    # ZERO. Zero is the answer for "no chain transported anything", and a
    # malformed record must not be able to produce it.
    for broken in (
        {"source_segment": 1},
        {"source_segment": [1]},
        {"source_segment": [{"transported_constraints": -1}]},
        {"source_segment": [{"transported_constraints": "2"}]},
        {"source_segment": [{"transported_constraints": True}]},
        {"source_segment": [{}]},
    ):
        with pytest.raises(MalformedInputError):
            transported_entry_count(broken)


def test_the_docked_values_are_the_emitted_ones_and_nothing_is_adjusted() -> None:
    declaration = _bb84_declaration()
    acceptance_set, rounds, parameters = _not_this_modules_inputs()
    docked = dock_declaration(
        declaration,
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
    )
    assert docked.alice_dim == declaration.alice_dim
    assert docked.sector_index_set == declaration.sectors.labels
    assert docked.sector_dims == {"s0": 2}
    assert docked.acceptance_values == declaration.acceptance_alphabet
    assert docked.key_value_count == len(declaration.key_alphabet)
    assert docked.key_holder is KeyHolder.ALICE
    assert docked.announce_alice == dict(declaration.announce_alice)
    assert docked.announce_bob == dict(declaration.announce_bob)
    assert docked.accept_statistic == dict(declaration.accept_statistic)
    # perp -> None, which is the consuming format's spelling of the same value.
    for pair, value in declaration.key_map.items():
        assert docked.key_map[pair] == (None if value == "perp" else value)
    assert None in set(docked.key_map.values())

    # The matrices are the emitted ones, converted and not altered.
    assert declaration.alice_marginal is not None
    np.testing.assert_array_equal(
        docked.alice_marginal, to_complex128(declaration.alice_marginal)
    )
    for label in declaration.alice_alphabet:
        np.testing.assert_array_equal(
            docked.alice_povm[label], to_complex128(declaration.alice_povm[label])
        )
    for label in declaration.bob_alphabet:
        # One sector, so the single block IS the operator.
        np.testing.assert_array_equal(
            docked.bob_povm[label]["s0"],
            to_complex128(declaration.bob_povm[label].blocks[0]),
        )
    # The three the caller supplied are the three the caller supplied.
    assert docked.acceptance_set is acceptance_set
    assert docked.rounds == rounds
    assert docked.parameters is parameters


def test_the_partition_crosses_explicitly_and_its_default_flag_is_computed() -> None:
    """Open choice 7: the default partition is spelled EXPLICITLY."""
    acceptance_set, rounds, parameters = _not_this_modules_inputs()
    declaration = _bb84_declaration()
    docked = dock_declaration(
        declaration,
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
    )
    partition = docked.party_partition
    assert partition is not None
    # THE TABLES CROSS, so O_A and O_B need no reconstruction on the far side.
    assert partition.alphabet_alice == declaration.alice_alphabet
    assert partition.alphabet_bob == declaration.bob_alphabet
    assert len(partition.readout_alice) == len(declaration.outcome_pairs())
    assert len(partition.readout_bob) == len(declaration.outcome_pairs())
    # And the flag is COMPUTED from them rather than declared, so it cannot
    # disagree with the tables it summarizes.
    assert partition.is_default is True


def test_the_source_replacement_licence_crosses_as_a_pass_through() -> None:
    acceptance_set, rounds, parameters = _not_this_modules_inputs()
    docked = dock_declaration(
        _bb84_declaration(),
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
    )
    licence = docked.source_replacement_license
    assert licence is not None
    assert licence["sr3_asserted_by_this_module"] is False
    assert licence["sr3_attestation_supplied"] is False
    # THE SHORT ID IS THE TRANSMITTER'S MERGED ONE. A-RET and A-SRC are one
    # assumption for one attestation, merged into A-SRC, and the docking
    # record carries the id the module that owns it declares.
    assert licence["sr3_never_verified_assumption"] == "A-SRC"


# ---------------------------------------------------------------------------
#  The wire round trip
# ---------------------------------------------------------------------------


def test_the_shared_keys_round_trip_through_the_wire_declaration() -> None:
    """The frozen manifest model, exercised on the emitted key vocabulary.

    The marker's own declaration in ``pyproject.toml`` reads
    "contract: ... NEVER SKIP, XFAIL OR WEAKEN ONE", and this module's
    ``pytestmark`` is ``[contract, oracle]``.

    THE HAND-BUILT PAYLOAD SPELLS EACH ``bob_povm`` element as a
    ``block_diagonal`` operator, because
    :data:`~certiqs_key.foundations.blocks.OperatorRef` does not express a
    FULL-SPACE array. Each ``bob_povm`` element
    is one array per sector -- this instance has the single sector ``s0`` of dimension
    2, so exactly one block, carrying
    the same ``[2, 2]`` array on the same basis. Section 2.5
    (``operator_form``): "an operator on Q IS A LIST OF SECTOR BLOCKS together
    with the map that names them", and at ``|S| = 1`` that list is the whole
    operator, not a truncation of it. THE KEY VOCABULARY is what this test
    exists to pin.
    """
    declaration = _bb84_declaration()
    payload: dict[str, object] = {
        "alice_dim": declaration.alice_dim,
        "alice_marginal": {
            "form": "array",
            "dataset": "/declaration/alice_marginal",
            "dtype": "complex128",
            "shape": [2, 2],
            "basis": "computational.A",
            "subsystem_order": ["A"],
            "storage": "dense",
            "semantic_role": "alice_marginal",
        },
        "source_replacement_license": {"sr3_asserted_by_this_module": False},
        "party_partition": {
            "readout_alice": {
                x: dict.fromkeys(declaration.bob_alphabet, x)
                for x in declaration.alice_alphabet
            },
            "readout_bob": {
                x: {v: v for v in declaration.bob_alphabet}
                for x in declaration.alice_alphabet
            },
            "alphabet_alice": list(declaration.alice_alphabet),
            "alphabet_bob": list(declaration.bob_alphabet),
            "party_of_alice_system": "A",
            "party_of_sector_factors": {"s0": ["B"]},
        },
        "sector_index_set": list(declaration.sectors.labels),
        "sector_dims": {"s0": 2},
        # The third component of the one sector map, required by the manifest;
        # the kind here is `proof_sector`.
        "sector_block_kind": "proof_sector",
        "alice_povm": {
            label: {
                "form": "array",
                "dataset": f"/declaration/alice_povm/{index}",
                "dtype": "complex128",
                "shape": [2, 2],
                "basis": "computational.A",
                "subsystem_order": ["A"],
                "storage": "dense",
                "semantic_role": "alice_povm_element",
            }
            for index, label in enumerate(declaration.alice_alphabet)
        },
        # ONE ARRAY PER SECTOR BLOCK, which is the only form `OperatorRef`
        # expresses. Band A has the single sector `s0`
        # of dimension 2, so the list has one entry.
        "bob_povm": {
            label: {
                "form": "block_diagonal",
                # THE SHARED FORMAT'S OWN ALPHABET, taken from `BlockKind`
                # rather than written as a literal, so that a rename there is a
                # failure here instead of a silent wire drift -- the same rule
                # the run tier's wire record follows.
                "block_kind": BlockKind.PROOF_SECTOR.value,
                "blocks": {
                    "s0": {
                        "form": "array",
                        "dataset": f"/declaration/bob_povm/{index}/s0",
                        "dtype": "complex128",
                        "shape": [2, 2],
                        "basis": "computational.Q.s0",
                        "subsystem_order": ["Q"],
                        "storage": "dense",
                        "semantic_role": "bob_povm_element",
                    }
                },
                "block_permutation": [0],
            }
            for index, label in enumerate(declaration.bob_alphabet)
        },
        "announce_alice": dict(declaration.announce_alice),
        "announce_bob": dict(declaration.announce_bob),
        "accept_statistic": {
            c_a: {
                c_b: declaration.accept_statistic[(c_a, c_b)]
                for c_b in declaration.bob_announcement_alphabet
            }
            for c_a in declaration.alice_announcement_alphabet
        },
        "key_map": {
            x: {
                v: (
                    None
                    if declaration.key_map[(x, v)] == "perp"
                    else declaration.key_map[(x, v)]
                )
                for v in declaration.bob_alphabet
            }
            for x in declaration.alice_alphabet
        },
        "key_holder": "A",
        "constraint_list": [],
        "attack_set_license": None,
        "acceptance_set": {"geometry": "singleton", "data": {}, "arrays": {}},
        "rounds": 1_000_000,
    }
    model = WireDeclaration.model_validate(payload)
    again = WireDeclaration.model_validate(model.model_dump())
    assert again == model
    assert again.alice_dim == declaration.alice_dim
    assert set(again.alice_povm) == set(declaration.alice_alphabet)
    assert set(again.bob_povm) == set(declaration.bob_alphabet)
    assert again.key_holder is KeyHolder.ALICE
    # The two the contract names as NOT this module's are supplied by the test.
    assert again.rounds == 1_000_000
    assert again.acceptance_set.geometry == "singleton"

    # AND THE BLOCK SPLIT SURVIVES THE ROUND TRIP, which is what F-S2-pc-09
    # asked for: every Bob element crosses as a per-sector list keyed by the
    # declaration's own sector identifiers, against the declaration's own block
    # kind. That is the three-component sector map the consumer compares.
    assert again.sector_block_kind == BlockKind.PROOF_SECTOR.value
    assert again.sector_index_set == declaration.sectors.labels
    for label in declaration.bob_alphabet:
        operator = again.bob_povm[label]
        assert operator.form == "block_diagonal"
        # THE WIRE SPELLING AND THE IN-MEMORY SPELLING ARE ONE ENUM:
        # ``domain.arrays`` imports the kind from ``foundations.blocks`` rather
        # than declaring a second, so this is an identity, not a comparison
        # by value.
        assert operator.block_kind is BlockKind.PROOF_SECTOR
        assert tuple(operator.blocks) == declaration.sectors.labels
        assert operator.blocks["s0"].shape == (2, 2)


# ---------------------------------------------------------------------------
#  The two validator sets, and the one place they do not overlap
# ---------------------------------------------------------------------------


def test_the_two_validators_agree_on_a_frozen_refusal_with_an_analogue() -> None:
    """V2's zero marginal: both sides refuse, independently and for their own reason."""
    declaration = _bb84_declaration()
    broken = CandidateDeclaration(
        **{**declaration.__dict__, "alice_marginal": matrix(((0, 0), (0, 0)))}
    )
    from certiqs_key.protocol_compiler import validate

    result = validate(broken)
    assert "V2" in result.refusing_checks

    acceptance_set, rounds, parameters = _not_this_modules_inputs()
    docked = dock_declaration(
        broken,
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
    )
    with pytest.raises(DeclarationError):
        validate_declaration(docked)


def test_the_two_validators_agree_on_an_incomplete_povm() -> None:
    """V3's completeness half, refused independently at both ends."""
    declaration = _bb84_declaration()
    first = declaration.alice_alphabet[0]
    broken = CandidateDeclaration(
        **{
            **declaration.__dict__,
            "alice_povm": {
                **declaration.alice_povm,
                first: scale(F(1, 2), declaration.alice_povm[first]),
            },
        }
    )
    from certiqs_key.protocol_compiler import validate

    assert "V3" in validate(broken).refusing_checks

    acceptance_set, rounds, parameters = _not_this_modules_inputs()
    docked = dock_declaration(
        broken,
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
    )
    with pytest.raises(DeclarationError):
        validate_declaration(docked)


def test_v7_has_no_consumer_analogue_and_the_asymmetry_is_recorded() -> None:
    """The one refusal of this module with nothing to agree with.

    Theorem ``thm:validator-soundness`` (iii): V7 is one-sided and refuses a WELL-FORMED
    declaration. The consuming engine does not check D(vii) at validation time
    at all -- with a non-empty list it defers non-emptiness to the linear
    oracle at solve time -- so there is nothing on the far side to agree or
    disagree with, and the two ends fail closed at DIFFERENT PLACES BY DESIGN.
    """
    declaration = _bb84_declaration()
    from certiqs_key.domain.constraints import ConstraintEntry
    from certiqs_key.protocol_compiler import validate

    # A non-empty list whose feasible set is non-empty and does NOT contain the
    # default candidate: this module refuses at V7, with no witness supplied.
    unreachable = CandidateDeclaration(
        **{
            **declaration.__dict__,
            "constraint_list": (
                ConstraintEntry(
                    operator=as_blocks(_QUBIT_MAP, matrix(((1, 0), (0, 0)))),
                    relation=Relation.GE,
                    # `homogeneous` with c_k = 1: the LICENSED form, whose
                    # right-hand side the compiler CONSTRUCTS as c_k tau_A
                    # (Definition def:homog (a)).
                    rhs=F(1),
                ),
            ),
        }
    )
    result = validate(unreachable)
    assert "V7" in result.refusing_checks
    assert result.feasibility.refusal is not None
    assert str(result.feasibility.refusal.reason) == "no_feasibility_witness"

    # THE CONSUMER'S VALIDATOR DOES NOT REFUSE IT, and that is not a
    # disagreement about the mathematics: it is a different division of labour.
    acceptance_set, rounds, parameters = _not_this_modules_inputs()
    docked = dock_declaration(
        unreachable,
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
    )
    validate_declaration(docked)


# ---------------------------------------------------------------------------
#  The conversion site
# ---------------------------------------------------------------------------


def test_the_conversion_is_exact_where_the_rational_is_dyadic() -> None:
    dyadic = matrix(((F(3, 4), 0), (0, F(1, 4))))
    converted = to_complex128(dyadic)
    assert converted.dtype == np.complex128
    np.testing.assert_array_equal(
        converted, np.array([[0.75 + 0j, 0j], [0j, 0.25 + 0j]], dtype=np.complex128)
    )


def test_the_conversion_carries_an_imaginary_part_and_warns_about_nothing() -> None:
    """``filterwarnings = error`` is repo-wide; the target dtype is complex."""
    from instances.bb84.specification import P_Y0

    converted = to_complex128(P_Y0)
    assert converted.dtype == np.complex128
    assert converted[0][1] == -0.5j
    assert converted[1][0] == 0.5j


def test_a_non_dyadic_rational_is_refused_at_the_boundary_and_never_rounded() -> None:
    """``no_snapping`` at the one site a number leaves the exact substrate.

    Asserting the OPPOSITE behaviour -- that ``2/3`` is emitted as the nearest
    binary64 -- would rest on the argument that "a rounding at this boundary
    cannot flip a verdict this module reached", and that argument fails on
    both legs. Definition ``def:exact`` opens with the premise that "Declared
    operator data arrives as binary64 numbers, and a binary64 number is a
    dyadic rational: IT IS THE NUMBER IT DENOTES AND THERE IS NO EXACT OBJECT
    BEHIND IT of which it is an approximation", so ``2/3`` is not a datum this
    contract types at all. And Section 2.5 (``no_snapping``): "AN EMITTED MATRIX
    ENTRY THAT THIS MODULE WAS HANDED IS THE ENTRY IT WAS HANDED ... this module
    therefore NEVER SNAPS, IN EITHER OF THE TWO SENSES SECTION 3.8
    DISTINGUISHES." Rounding here is the second sense.

    Nor would the rounding have been harmless: the CONSUMER decides (H), (P),
    (C) and (S) at exactly zero on precisely the numbers it receives, so a
    silent rounding hands it data this module decided nothing about.
    """
    non_dyadic = matrix(((F(2, 3), 0), (0, F(1, 3))))
    with pytest.raises(MalformedInputError, match="not a binary64 number"):
        to_complex128(non_dyadic)
    # AND THE REFUSAL NAMES WHICH OBJECT, so a caller is not left to search.
    with pytest.raises(MalformedInputError, match="the declared marginal tau_A"):
        to_complex128(non_dyadic, what="the declared marginal tau_A")
    # THE DYADIC NEIGHBOUR IS EMITTED UNCHANGED, which is the other half of the
    # rule: ``float`` is the IDENTITY on a number already on the lattice, so
    # what crosses is the number this module decided on.
    dyadic = matrix(((F(3, 4), 0), (0, F(1, 4))))
    emitted = to_complex128(dyadic)
    assert F(emitted[0][0].real) == F(3, 4)
    assert F(emitted[1][1].real) == F(1, 4)


def test_the_relation_map_is_total_and_injective() -> None:
    assert set(RELATION_TO_CONSUMER) == set(Relation)
    assert len(set(RELATION_TO_CONSUMER.values())) == 3
    assert set(RELATION_TO_CONSUMER.values()) == set(ConstraintRelation)


def test_sector_blocks_re_keys_a_block_list_and_no_longer_splits_anything() -> None:
    """THE OPERATOR IS ALREADY ITS BLOCKS, so there is nothing left to refuse.

    At 0.1.4 this function sliced a ``d_Q x d_Q`` array along the sector
    decomposition and re-checked that the off-diagonal blocks it discarded were
    zero. Both the slice and the re-check are superseded by scope at 0.3.0:
    Section 2.5 (``operator_form``), "Sector-block-diagonality HOLDS BY
    CONSTRUCTION; nothing verifies that the off-sector entries are zero,
    BECAUSE NOTHING CAN WRITE THEM."

    The refusal the 0.1.4 test exercised has moved UPSTREAM OF THE MODULE
    ENTIRELY: an operator with a crossing entry has no block list at all, which
    the fixture adaptor asserts and which is a stronger statement than the
    refusal it replaces.
    """
    crossing = matrix(((F(1, 2), 0, F(1, 2)), (0, 0, 0), (F(1, 2), 0, F(1, 2))))
    with pytest.raises(NotBlockDiagonalError):
        as_blocks(_QUTRIT_MAP, crossing)
    block_diagonal = matrix(((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    blocks = sector_blocks(as_blocks(_QUTRIT_MAP, block_diagonal), ("s0", "s1"))
    assert set(blocks) == {"s0", "s1"}
    assert blocks["s0"].shape == (2, 2)
    assert blocks["s1"].shape == (1, 1)


def test_docking_is_not_reachable_from_either_package_surface() -> None:
    """Neither package re-exports it, and the file has moved to the consumer.

    The rule is the same on both sides. It is not
    on the compiler's surface; it is not on the engine's
    because importing it from ``__init__`` would put the compiler's exact
    Gaussian-rational substrate on the import path of a package whose own
    mathematics is binary64 linear algebra.
    """
    import certiqs_key.meat_core as engine
    import certiqs_key.protocol_compiler as package

    assert not hasattr(package, "dock_declaration")
    assert not hasattr(package, "to_complex128")
    assert "docking" not in package.__all__
    assert not hasattr(engine, "dock_declaration")
    assert not hasattr(engine, "to_complex128")
    assert "docking" not in engine.__all__


# ---------------------------------------------------------------------------
#  The two 0.3.0 keys at the boundary
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_tag_crosses_and_is_read_off_the_datum_never_off_a_field() -> None:
    """Definition ``def:homog``: the consumer's type check gets its datum.

    ``constraint_rhs_tag`` is "a key of THIS module, emitted with each entry so
    that the consuming engine's type check has a datum", and it is READ OFF THE
    DATUM: a scalar right-hand side spells ``homogeneous``, a Hermitian matrix
    spells ``general``. The consumer's own row requires it and supplies no
    default, so the two ends carry the same object for the same reason.
    """
    from certiqs_key.domain.constraints import ConstraintEntry, RhsTag
    from certiqs_key.meat_core.declaration.declaration import RhsTag as ConsumerRhsTag
    from certiqs_key.meat_core.docking import CONSUMER_RHS_TAG

    # ``RhsTag`` has the THIRD form of ``def:homog``, ``party_local``, which
    # the consuming engine's own vocabulary does not carry. So the crossing map
    # is asserted as it is: every tag the CONSUMER knows crosses, and the
    # compiler's vocabulary is the wider of the two by exactly that member:
    # the consumer's set is the compiler's minus ``party_local``.
    assert set(CONSUMER_RHS_TAG) == set(RhsTag) - {RhsTag.PARTY_LOCAL}
    assert set(CONSUMER_RHS_TAG.values()) == set(ConsumerRhsTag)

    declaration = _bb84_declaration()
    scalar_entry = ConstraintEntry(
        operator=as_blocks(_QUBIT_MAP, matrix(((1, 0), (0, 0)))),
        relation=Relation.GE,
        rhs=F(1, 4),
    )
    matrix_entry = ConstraintEntry(
        operator=as_blocks(_QUBIT_MAP, matrix(((1, 0), (0, 0)))),
        relation=Relation.GE,
        rhs=scale(F(1, 4), matrix(((1, 0), (0, 1)))),
    )
    assert scalar_entry.tag is RhsTag.HOMOGENEOUS
    assert matrix_entry.tag is RhsTag.GENERAL

    acceptance_set, rounds, parameters = _not_this_modules_inputs()
    for entry, expected in (
        (scalar_entry, ConsumerRhsTag.HOMOGENEOUS),
        (matrix_entry, ConsumerRhsTag.GENERAL),
    ):
        docked = dock_declaration(
            CandidateDeclaration(
                **{**declaration.__dict__, "constraint_list": (entry,)}
            ),
            acceptance_set=acceptance_set,
            rounds=rounds,
            parameters=parameters,
        )
        assert docked.constraint_list[0].rhs_tag is expected


@pytest.mark.contract
def test_all_three_components_of_the_sector_map_cross_the_boundary() -> None:
    """Definition ``def:declaration``: all three, not two of them.

    "ALL THREE of its components are machine keys of the emitted artifact ...
    so that a consumer comparing sector maps can compare ALL THREE AND NOT TWO
    OF THEM." The consuming declaration has its ``sector_block_kind`` slot, so
    what this test pins is the crossing.

    THE VALUE IS THE SHARED FORMAT'S, NOT A SPELLING OF THIS MODULE'S: the
    vocabulary is :class:`~certiqs_key.foundations.blocks.BlockKind`
    (spec/architecture.md 2.9, a frozen type of the shared format), and what
    goes on the wire is that enum's value.
    """
    from certiqs_key.foundations.blocks import BlockKind

    ConsumerDeclaration = ProtocolDeclaration

    consumer_fields = set(ConsumerDeclaration.__dataclass_fields__)
    assert {"sector_index_set", "sector_dims", "sector_block_kind"} <= consumer_fields

    declaration = _bb84_declaration()
    assert declaration.sectors.block_kind is BlockKind.PROOF_SECTOR

    acceptance_set, rounds, parameters = _not_this_modules_inputs()
    docked = dock_declaration(
        declaration,
        acceptance_set=acceptance_set,
        rounds=rounds,
        parameters=parameters,
    )
    assert docked.sector_block_kind == BlockKind.PROOF_SECTOR.value
    assert docked.sector_index_set == declaration.sectors.labels

    # AND THE SAME VALUE IS IN THE EMITTED MACHINE RECORD, as the enum's value
    # and not its repr -- a record a consumer reads must carry the wire string.
    record = declaration.as_machine_record()
    assert record["sector_block_kind"] == BlockKind.PROOF_SECTOR.value
    assert record["sector_block_kind"] == "proof_sector"


@pytest.mark.contract
def test_no_block_kind_outside_the_frozen_enum_is_admitted() -> None:
    """A value outside ``BlockKind`` is refused, never mapped to a member.

    The contract NAMES the datum and the shared format FIXES the values
    (spec/architecture.md 2.9; conversions between the two spellings are
    EXPLICIT AND CHECKED). A CONSUMER DECIDES AND NEVER INFERS is what makes
    the refusal the only admissible answer: a kind this module chose would be
    it deciding what somebody else's identifiers mean.

    THERE IS NO CONVERSION HELPER: THE REFUSAL IS IN THE TYPE.
    ``certiqs_key.foundations.blocks.SectorStructure`` refuses a value
    outside the enum in its own ``__post_init__`` and supplies none. So
    there is one constructor check, and this asserts
    both halves of it: every member is admitted, and nothing else is.
    """
    from certiqs_key.foundations.blocks import BlockKind
    from certiqs_key.foundations.errors import MalformedInputError

    for member in BlockKind:
        structure = SectorStructure(labels=("s0",), dims=(2,), block_kind=member)
        assert structure.block_kind is member

    for rejected in ("whole-space", "", "PROOF_SECTOR", None, 3, object()):
        with pytest.raises(MalformedInputError):
            SectorStructure(labels=("s0",), dims=(2,), block_kind=rejected)  # type: ignore[arg-type]
