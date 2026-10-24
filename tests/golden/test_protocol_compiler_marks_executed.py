"""The protocol-compiler marks EXECUTED, not merely present.

The analogue of ``tests/golden/test_registry_marks_executed.py``, which does
this for ``meat-core``. ``tests/oracles/test_protocol_compiler_registry.py`` is
run A's file and checks that every mark is WELL FORMED -- that each names a real
entry or tuple, that no entry is both scoped and re-pointed, that a re-point
lands on live claims. It cannot check that anything was DONE with them, because
it is written before the source runs exist.

This file is the other half, and F-S2-pc-08 is why it exists. The Stage 2
implementation-verifier found that "there is no protocol-compiler analogue of
tests/golden/test_registry_marks_executed.py, so nothing makes the eight
SUPERSEDED_BY_SCOPE_0_3_0 marks or REPOINT_AT_RUN_B_0_3_0 consequential --
WHICH IS HOW F-S2-pc-05 SURVIVED": a live test was still asserting the ledger's
superseded ten-row reading, under a mark that says it is eleven, and nothing
noticed.

What each mark owes:

* a SUPERSEDED-BY-SCOPE row is not asserted in its superseded reading by any
  live test -- the reading is retired, though the frozen VALUE stands and is
  never edited;
* a RE-POINTED entry keeps its own ``claims`` tuple, the re-point being recorded
  BESIDE it;
* and the four fail-closed rows 0.3.0 added are DRIVEN by a case somewhere, not
  merely spelled in an enum -- the coverage-theatre failure the verifier named.

NOTHING HERE EDITS A FROZEN VALUE. Every assertion reads the registry or the
tree; the marks are lists beside the entries, and this file is the reader that
makes them consequential.
"""

from __future__ import annotations

import pathlib

import pytest
from registry_instances_bb84 import bb84_pc_oracle
from registry_protocol_compiler import (
    NOT_MARKED_AT_0_3_0,
    REPOINT_AT_RUN_B_0_3_0,
    RESTORED_AT_0_3_0,
    SCOPE_SUPERSESSION_LINE_0_3_0,
    SUPERSEDED_BY_SCOPE_0_3_0,
    pc_oracle,
)
from registry_transmitter import transmitter_pc_oracle

pytestmark = [pytest.mark.contract, pytest.mark.oracle]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: The protocol-compiler test files a reader may find a mark's subject in. An
#: explicit filter and not a glob: the tree also holds the sibling modules'
#: suites, which are other bands' artifacts and none of this file's business.
SCANNED = (
    tuple(
        path
        for path in sorted((REPO_ROOT / "tests").rglob("test_*protocol_compiler*.py"))
    )
    + tuple(sorted((REPO_ROOT / "tests" / "unit").glob("test_protocol_*.py")))
    + tuple(sorted((REPO_ROOT / "tests" / "property").glob("test_protocol_*.py")))
)


def test_the_scanned_set_is_not_empty_and_holds_the_files_it_claims_to() -> None:
    """A scan that matched nothing would make every assertion below vacuous."""
    names = {path.name for path in SCANNED}
    assert "test_protocol_compiler_against_registry.py" in names
    assert "test_protocol_compiler_registry.py" in names
    assert "test_protocol_emission.py" in names
    assert "test_protocol_compiler_group_pc_m.py" in names
    assert len(SCANNED) >= 8


def test_the_supersession_line_names_its_blob_and_meaning() -> None:
    """A mark whose ground is unstated cannot be audited later."""
    assert "superseded BY SCOPE" in SCOPE_SUPERSESSION_LINE_0_3_0
    assert "f1441567" in SCOPE_SUPERSESSION_LINE_0_3_0
    # AND IT SAYS WHAT SUPERSESSION BY SCOPE MEANS, which is the thing a reader
    # must not get wrong: "The value is NOT withdrawn as wrong: it is a correct
    # reading of a superseded text whose SUBJECT 0.3.0 removed."
    assert "NOT withdrawn as wrong" in SCOPE_SUPERSESSION_LINE_0_3_0
    assert len(SUPERSEDED_BY_SCOPE_0_3_0) == 8


def test_the_ledger_scope_mark_is_executed_and_no_live_test_reads_ten() -> None:
    """The mark F-S2-pc-05 was hiding behind, made consequential.

    The row reads: "LEDGER_ROWS and the assumption count | the ledger read as
    TEN rows | ELEVEN AT 0.3.0. A-BLOCK (`block_diagonal_feasible_set`) was
    added at the round-9 revision of 0.2.0 and this registry was never authored
    against 0.2.0 ... THE FOUR-MEMBER NEVER-VERIFIED SET IS UNCHANGED and
    A-BLOCK is not in it."

    Two things follow: the code
    carries eleven rows, and no live test asserts the superseded ten-row
    reading of ``ASSUMPTION_MACHINE_KEYS``.
    """
    from certiqs_key.protocol_compiler import (
        ASSUMPTION_MACHINE_KEYS,
        INHERITED_NEVER_VERIFIED_KEYS,
        NEVER_VERIFIED,
        AssumptionId,
    )

    row = next(
        entry
        for entry in SUPERSEDED_BY_SCOPE_0_3_0
        if entry[0].startswith("LEDGER_ROWS")
    )
    assert "TEN rows" in row[1]
    assert "ELEVEN AT 0.3.0" in row[2]

    # THE CODE HAS SEVEN OWN IDS, NOT ELEVEN: four of the frozen rows are
    # other modules'. THE SCOPE MARK THIS TEST
    # EXECUTES IS UNCHANGED -- reading the frozen ten-row ledger as
    # COMPLETE is what is superseded -- and
    # the count it is measured against is the code's current one. A-BLOCK is
    # not a member: it is a remark, rem:block-restriction
    # (meat-core/thm:reduction, step 1, proves it), and A-PRESENT is part of
    # def:well-formed-spec (iv). The mark is still executed: what it supersedes
    # is reading the frozen ten-row ledger as complete, and that reading is
    # superseded -- the row it added left by a later decision, not by
    # the frozen reading becoming right.
    assert len(AssumptionId) == 7
    assert len(ASSUMPTION_MACHINE_KEYS) == 7
    assert "A-BLOCK" not in {str(member) for member in AssumptionId}
    assert "A-PRESENT" not in {str(member) for member in AssumptionId}
    # The four that left are present in the modules that own them, and
    # the run manifest assembles the closure from their artefacts
    # (spec/architecture.md 4.4).
    # AND THE NEVER-VERIFIED SET IS UNCHANGED, which the mark says explicitly.
    # SEVEN OWN AND FOUR INHERITED: A-RET is the transmitter's A-SRC, so it is
    # no member of this module's enum and is named by machine key instead.
    # The frozen pair (A-LINK, A-LIC as A-ATK) gained A-SPEC, A-RHOM, A-COIN,
    # A-IDEAL and A-ALICE-MEAS; of the inherited pair (A-RET as A-SRC,
    # A-RECV), A-RECV is no row of this module on any route (it is the
    # reductions artefact's own, reductions/req:recv-row-provenance), and the
    # inherited set gained A-ENS, A-SEQ and the decoy's A-WCP. What this mark
    # executes is unchanged: the frozen reading is superseded, and A-BLOCK,
    # discharged, is in neither set.
    assert len(NEVER_VERIFIED) == 7
    assert len(INHERITED_NEVER_VERIFIED_KEYS) == 4
    assert "A-BLOCK" not in {str(member) for member in NEVER_VERIFIED}

    # AND NO LIVE TEST ASSERTS THE SUPERSEDED READING. The pattern below is the
    # exact assertion that survived the band and that the verifier caught. THIS
    # FILE IS EXCLUDED FROM ITS OWN SCAN, and that is not a loophole: the rule
    # the meat-core analogue states is about ACKNOWLEDGEMENT and not silence --
    # naming a superseded reading in order to assert that it is superseded is
    # the opposite of asserting it.
    superseded_reading = "len(ASSUMPTION_MACHINE_KEYS) == len(" + "LEDGER_ROWS) == 10"
    offenders = [
        path.name
        for path in SCANNED
        if path.name != pathlib.Path(__file__).name
        and superseded_reading in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], offenders


def test_the_vocabulary_scope_mark_is_executed_at_thirteen_and_twenty_three() -> None:
    """The key-count mark: twelve/twenty-one at 0.1.4, thirteen/twenty-three now.

    The mark adds that "NO EXISTING KEY IS REMOVED OR RENAMED, so every name in
    every tuple is still a machine key of this module; what is superseded is the
    COUNT and the POSITION of the insertions" -- so the frozen tuples are
    asserted to be SUBSETS of the implemented ones, never equal to them.
    """
    from registry_protocol_compiler import COMPILER_ONLY_KEYS as FROZEN_COMPILER_ONLY
    from registry_protocol_compiler import DECLARATION_SLOT_KEYS as FROZEN_SLOTS
    from registry_protocol_compiler import INPUT_KEYS as FROZEN_INPUTS
    from registry_protocol_compiler import OUTPUT_KEYS as FROZEN_OUTPUTS

    from certiqs_key.protocol_compiler import (
        COMPILER_ONLY_KEYS,
        DECLARATION_SLOT_KEYS,
        INPUT_KEYS,
        OUTPUT_KEYS,
    )

    row = next(
        entry
        for entry in SUPERSEDED_BY_SCOPE_0_3_0
        if entry[0].startswith("INPUT_KEYS")
    )
    assert "THIRTEEN/TWENTY-THREE AT 0.3.0" in row[2]
    assert "NO EXISTING KEY IS REMOVED OR RENAMED" in row[2]

    # ELEVEN INPUT KEYS, NOT THIRTEEN. Three of the frozen ones
    # became ONE `transmitter_artifact` row, one -- `source_mode_request`
    # -- is retired and one is new (`choice_weighting`,
    # route C). THE SCOPE MARK IS UNCHANGED.
    assert len(INPUT_KEYS) == 11
    assert len(OUTPUT_KEYS) == 23
    assert len(DECLARATION_SLOT_KEYS) == 17
    assert len(COMPILER_ONLY_KEYS) == 6
    # EVERY FROZEN NAME SURVIVES, which is what the mark asserts and what makes
    # this a supersession of a COUNT rather than of a vocabulary.
    # THE FOUR FROZEN INPUT NAMES THAT DID NOT SURVIVE, AND WHERE
    # EACH WENT. This is the one place the vocabulary mark's "NO EXISTING
    # KEY IS REMOVED OR RENAMED" stops holding of THIS repository, and
    # it stops holding because the OBJECTS moved modules rather than
    # because a name was dropped: `alice_system`, `alice_povm_spec` and
    # `source_replacement_certificate` are read off the transmitter
    # artefact under the transmitter's own key names, and
    # `source_mode_request` is an input of THAT module (a request
    # is not an emission). THE FROZEN TUPLE
    # IS NOT EDITED.
    MOVED_TO_THE_TRANSMITTER = {
        "alice_system",
        "alice_povm_spec",
        "source_replacement_certificate",
        "source_mode_request",
    }
    assert set(FROZEN_INPUTS) >= MOVED_TO_THE_TRANSMITTER
    assert set(FROZEN_INPUTS) - MOVED_TO_THE_TRANSMITTER <= set(INPUT_KEYS)
    assert "transmitter_artifact" in INPUT_KEYS
    assert "choice_weighting" in INPUT_KEYS
    assert set(FROZEN_OUTPUTS) <= set(OUTPUT_KEYS)
    assert set(FROZEN_SLOTS) <= set(DECLARATION_SLOT_KEYS)
    assert set(FROZEN_COMPILER_ONLY) == set(COMPILER_ONLY_KEYS)


def test_the_refusal_vocabulary_scope_mark_is_executed_at_seven() -> None:
    """The refusal-vocabulary mark: two strings at 0.1.4, seven at 0.3.0.

    "BOTH EXISTING STRINGS REMAIN CORRECT AND ARE NOT WITHDRAWN; what is
    superseded is the completeness of the tuple." The mark names the five that
    arrive, so they are checked BY NAME and not by count alone -- a count would
    pass on any five strings.
    """
    from certiqs_key.protocol_compiler import REFUSAL_REASONS_VERBATIM

    row = next(
        entry
        for entry in SUPERSEDED_BY_SCOPE_0_3_0
        if entry[0] == "REFUSAL_REASONS_VERBATIM"
    )
    assert "SEVEN AT 0.3.0" in row[2]
    assert "BOTH EXISTING STRINGS REMAIN CORRECT AND ARE NOT WITHDRAWN" in row[2]

    spellings = tuple(str(reason) for reason in REFUSAL_REASONS_VERBATIM)
    assert len(spellings) == 7
    for name in (
        "sector_map_mismatch",
        "alice_marginal_trace_rounds",
        "alice_povm_summation_rounds",
        "bob_povm_summation_rounds",
        "emitted_value_not_representable",
    ):
        assert name in row[2], name
        assert name in spellings, name


def test_the_four_new_fail_closed_rows_are_driven_and_not_only_spelled() -> None:
    """The coverage-theatre finding, closed. F-S2-pc-08.

    "For those four rows that assertion is COVERAGE THEATRE: it pins the
    spelling of an enum and WOULD PASS WITH EVERY ONE OF THEIR REFUSAL PATHS
    DELETED." So each of the four must be reachable from a real compilation or
    a real decision, and this test drives all four.
    """
    from dataclasses import replace
    from fractions import Fraction as F

    from instances.bb84.specification import band_a_block_kind, bb84_specification

    from certiqs_key.domain.constraints import ConstraintEntry, Relation
    from certiqs_key.foundations.blocks import BlockOperator, SectorStructure
    from certiqs_key.foundations.exact import identity, matrix, scale
    from certiqs_key.protocol_compiler import (
        Party,
        PublicChoices,
        compile_specification,
        resolve_povm,
    )
    from certiqs_key.protocol_compiler.validation import check_v1, check_v2, check_v3

    driven: set[str] = set()

    # (1) alice_povm_summation_rounds -- the decimal-literal family, presented
    # directly. Through Alice's public-choice record req:weight-list refuses
    # its weight list first, with choice_weights_not_normalized
    # (S-ALICE-DECIMAL-LITERALS); with no record the compiler reads the
    # artefact's own matrices and V3's (S) leg refuses them
    # (S-ALICE-DECIMAL-LITERALS-DIRECT).
    decimal_spec = bb84_specification(
        F(8106479329266893, 2**53), F(3602879701896397, 2**55), F(1, 2), F(1, 2)
    )
    weight_list = compile_specification(decimal_spec)
    assert weight_list.refusal is not None
    assert str(weight_list.refusal.reason) == "choice_weights_not_normalized"
    decimal = compile_specification(
        replace(decimal_spec, source=replace(decimal_spec.source, alice_choices=None))
    )
    assert decimal.refusal is not None
    driven.add(str(decimal.refusal.reason))

    balanced = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert balanced.declaration is not None
    declaration = balanced.declaration

    # (2) bob_povm_summation_rounds -- the SAME defect, on the per-block sum.
    # fl(0.9) and fl(0.1) again: the computed per-block total is exactly 1_{Q_s}
    # so (C) passes, and the third addition rounds so (S) fails. Weighting Bob's
    # four projectors reproduces Alice's accumulation on the other side.
    nine, one = F(8106479329266893, 2**53), F(3602879701896397, 2**55)
    half = F(1, 2)
    bob = {
        "(Z,0)": BlockOperator.of(declaration.sectors, [matrix(((nine, 0), (0, 0)))]),
        "(Z,1)": BlockOperator.of(declaration.sectors, [matrix(((0, 0), (0, nine)))]),
        "(X,0)": BlockOperator.of(
            declaration.sectors,
            [matrix(((one * half, one * half), (one * half, one * half)))],
        ),
        "(X,1)": BlockOperator.of(
            declaration.sectors,
            [matrix(((one * half, -one * half), (-one * half, one * half)))],
        ),
    }
    rounded = replace(declaration, bob_povm=bob)
    outcome = check_v3(rounded)
    assert outcome.refusal is not None
    driven.add(str(outcome.refusal.reason))

    # (3) alice_marginal_trace_rounds -- (S) on the TRACE, accumulated over the
    # row index in increasing order. The fixture is a qutrit marginal whose
    # trace is EXACTLY one and whose SECOND row addition is not: with
    # a = 1 - 2**-53 and b = 2**-54, a + b = (2**54 - 1) * 2**-54 has an odd
    # 54-bit numerator and is not binary64, while a + b + b = 1 exactly. So the
    # equality holds and (S) fails, which is the configuration this row exists
    # for -- the trace being "read as an IDENTITY OF REAL NUMBERS exactly as a
    # completeness sum is" (Definition def:exact). A two-by-two marginal cannot
    # exhibit it: if x + y is exactly 1 then that addition is exact.
    a = 1 - F(1, 2**53)
    b = F(1, 2**54)
    marginal = replace(
        declaration,
        alice_dim=3,
        alice_marginal=matrix(((a, 0, 0), (0, b, 0), (0, 0, b))),
    )
    trace_outcome = check_v2(marginal)
    assert trace_outcome.refusal is not None
    assert "row 2" in trace_outcome.refusal.detail
    driven.add(str(trace_outcome.refusal.reason))

    # (4) emitted_value_not_representable -- def:weighted's emission decision,
    #     taken ON the resolution path.
    a = F(2**52 + 1, 2**53)
    b = F(2**52 - 1, 2**53)
    conditional = {
        "u0": matrix(((a, 0), (0, b))),
        "u1": matrix(((b, 0), (0, a))),
    }
    resolution = resolve_povm(
        PublicChoices(
            party=Party.ALICE,
            choices=("t0", "t1"),
            weights={"t0": a, "t1": b},
            conditional_alphabets={"t0": ("u0", "u1"), "t1": ("u0", "u1")},
            conditional_elements={"t0": conditional, "t1": conditional},
        )
    )
    assert resolution.refusal is not None
    driven.add(str(resolution.refusal.reason))

    assert driven == {
        "alice_povm_summation_rounds",
        "bob_povm_summation_rounds",
        "alice_marginal_trace_rounds",
        "emitted_value_not_representable",
    }

    # AND THE FIFTH 0.3.0 ROW, `sector_map_mismatch`, which the verifier found
    # already driven -- asserted here so the set stays complete if it moves.
    other = SectorStructure(labels=("s9",), dims=(2,), block_kind=band_a_block_kind())
    mismatched = replace(
        declaration,
        constraint_list=(
            ConstraintEntry(
                operator=BlockOperator.of(other, [scale(F(1, 2), identity(2))]),
                relation=Relation.LE,
                rhs=F(1),
            ),
        ),
    )
    v1 = check_v1(mismatched)
    assert v1.refusal is not None
    assert str(v1.refusal.reason) == "sector_map_mismatch"


def test_the_six_group_pc_m_tuples_are_read_by_a_live_test() -> None:
    """The other half of F-S2-pc-08: "frozen evidence that nothing reads".

    Run A derived every value in these six tuples twice, by independent routes,
    and no test imported any of them. This asserts that a live file now does --
    by NAME, so that deleting the reader is a failure here rather than a silent
    return to frozen-and-unread.
    """
    reader = REPO_ROOT / "tests" / "golden" / "test_protocol_compiler_group_pc_m.py"
    assert reader.exists()
    source = reader.read_text(encoding="utf-8")
    for name in (
        "SUMMATION_CASES",
        "RHS_TAG_CASES",
        "CERTIFICATE_OPERATOR_CASES",
        "SECTOR_MAP_COMPARISON_CASES",
        "EMISSION_REPRESENTABILITY_CASES",
        "DECLARED_ORDER_CASES",
    ):
        assert f"    {name},\n" in source, name
        # And it is READ, not merely imported: each name is used again below
        # its import, in a parametrize or a lookup.
        assert source.count(name) >= 2, name


def test_the_eight_repoints_keep_their_own_claim_tuples() -> None:
    """A re-point records a MOVE beside an entry and changes nothing in it.

    "RUN B RE-POINTS THESE AND CHANGES NOTHING ELSE ABOUT THEM; none is
    superseded and none is re-derived." So every re-pointed entry still resolves
    and still carries the claim tuple it was frozen with.
    """
    assert len(REPOINT_AT_RUN_B_0_3_0) == 8
    # THE ENTRY IS LOOKED UP ACROSS THE THREE HALVES OF THE PARTITION.
    # Two of the eight -- O-PC-CERTIFICATE and O-PC-SR-BOUNDARY -- pin PC10 and
    # PC11, which are `transmitter` claims, and one pins the
    # BB84 instance. NOT ONE BYTE OF ANY OF THEM MOVED; what moved is which
    # file holds it.
    def _any_half(oracle_id: str) -> object:
        for accessor in (pc_oracle, transmitter_pc_oracle, bb84_pc_oracle):
            try:
                return accessor(oracle_id)
            except KeyError:
                continue
        raise AssertionError(f"no half of the registry has {oracle_id!r}")

    for name, ground in REPOINT_AT_RUN_B_0_3_0:
        entry = _any_half(name)
        assert entry.oracle_id == name  # type: ignore[attr-defined]
        assert entry.claims, name  # type: ignore[attr-defined]
        # The ground says what moved, and it is prose of substance rather than
        # a marker word.
        assert len(ground) > 80, name


def test_no_entry_or_subject_is_marked_twice_across_the_lists() -> None:
    """The dispositions are exclusive: scoped, or re-pointed, or restored."""
    scoped = {holder for holder, _, _ in SUPERSEDED_BY_SCOPE_0_3_0}
    repointed = {name for name, _ in REPOINT_AT_RUN_B_0_3_0}
    restored = {subject for subject, _ in RESTORED_AT_0_3_0}
    not_marked = {subject for subject, _ in NOT_MARKED_AT_0_3_0}

    assert not (scoped & repointed)
    assert not (scoped & restored)
    assert not (repointed & restored)
    # AND THE DELIBERATELY-UNMARKED LIST IS DISJOINT FROM ALL THREE, which is
    # what makes it an audit trail rather than a duplicate.
    assert not (not_marked & (scoped | repointed | restored))
    assert len(NOT_MARKED_AT_0_3_0) == 5
    assert len(RESTORED_AT_0_3_0) == 4
