"""Run B's side of the marking scheme: the marks EXECUTED, not merely present.

``tests/oracles/test_registry_integrity.py`` -- run A's file, frozen -- checks
that every mark is WELL FORMED: that each names a real entry, that each is
earned by a deleted claim, that no entry is both scoped and re-pointed, and that
a re-point lands on live claims. It cannot check that run B DID anything with
them, because it is written before run B exists.

This file is the other half. It asserts what run B owes each mark:

* a SUPERSEDED-BY-SCOPE entry is not asserted by any live test -- the sixteen
  certificate entries are discharged by the deletion of the six test files that
  pinned them, and nothing in the tree may pin them again;
* a RE-POINTED entry keeps its own ``claims`` tuple and is read through
  ``claims_at_1_0_0``, which is what makes the record of the 0.4.0 proof
  survive the move of the claim that owned it;
* the two PENDING-RETIREMENT rows whose files this band deleted are discharged
  by the deletion and stand in the frozen tuple;
* and run A's ``NOT_SUPERSEDED_BY_1_0_0`` row for Group 9 carries run B's dated
  correction beside it, with the three rows that correction marks.

NOTHING HERE EDITS A FROZEN VALUE. Every assertion reads the registry; the
marks are lists beside the entries, and this file is the reader that makes them
consequential.
"""

from __future__ import annotations

import pathlib

import pytest
from registry import (
    CERTIFICATE_SUPERSESSION_LINE,
    MATHEMATICAL_SPEC_VERSION_0_5_0,
    MATHEMATICAL_SPEC_VERSION_1_0_0,
    NORM_CHANGE_SUPERSEDED_1_0_0,
    NOT_SUPERSEDED_BY_1_0_0,
    NOT_SUPERSEDED_CORRECTION_1_0_0,
    PENDING_RETIREMENT_AT_RUN_B,
    PENDING_ROWS_SUPERSEDED_BY_SCOPE_1_0_0,
    REPOINT_AT_RUN_B_1_0_0,
    SUPERSEDED_BY_1_0_0,
    SUPERSEDED_BY_SCOPE_1_0_0,
    claims_at_1_0_0,
    oracle,
    pending_row_superseded,
    repointing,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: The meat-core test files a reader of this suite may find an entry id in.
#: An explicit list and not a glob: the tree also holds the sibling modules'
#: suites, which are other bands' artifacts and none of this file's business.
SCANNED = tuple(
    path
    for path in sorted((REPO_ROOT / "tests").rglob("test_*.py"))
    if not any(
        foreign in path.name
        for foreign in (
            "proof_reductions",
            "protocol_compiler",
            "receiver_povm",
            "statistics_acceptance",
            "reductions_",
        )
    )
)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_sixteen_scope_marks_are_acknowledged_wherever_they_are_named() -> None:
    """A superseded-by-scope entry is retired, and retirement is not a comment.

    ``CERTIFICATE_SUPERSESSION_LINE`` states the ground once for the group:
    "NO RUN OF THIS MODULE COMPUTES ANY QUANTITY THEY FREEZE. The values are
    not withdrawn as mathematics ... what is withdrawn is THE MODULE'S CLAIM TO
    COMPUTE THEM."

    SO THE RULE IS ABOUT ACKNOWLEDGEMENT AND NOT ABOUT SILENCE, which is the
    form run A's own hand-off invariant takes and the reason this test does not
    simply ban the ids. Two of the sixteen are still legitimately NAMED by live
    files -- ``O-ASSURANCE-CERTIFIED-GATE`` because it is the unique registry
    entry naming ``certified`` as a value, which is a fact about the
    REGISTRY'S SHAPE and not about any computation, and ``O-OPTOL-HCERT-NO-CLAIM``
    because a run-B test asserts that it IS superseded. What is forbidden is
    naming one WITHOUT acknowledging the mark, because that is indistinguishable
    from asserting the withdrawn claim.

    THE SIXTEEN ARE OTHERWISE DISCHARGED BY DELETION: the six certificate test
    files that pinned them are gone, so no live file replays a certificate
    value at all.
    """
    assert len(SUPERSEDED_BY_SCOPE_1_0_0) == 16
    assert "meat-core 1.0.0" in CERTIFICATE_SUPERSESSION_LINE

    scoped = {name for name, _ in SUPERSEDED_BY_SCOPE_1_0_0}
    acknowledgements = (
        "SUPERSEDED_BY_SCOPE_1_0_0",
        "is_superseded_by_scope",
        "SUPERSEDED_BY_0_5_0",
        "superseded",
    )
    offenders: list[tuple[str, str]] = []
    for path in SCANNED:
        source = path.read_text(encoding="utf-8")
        if any(word in source for word in acknowledgements):
            continue
        for name in scoped:
            if f'"{name}"' in source or f"'{name}'" in source:
                offenders.append((path.name, name))
    assert offenders == [], offenders

    # AND THE FILES THAT REPLAYED THEIR VALUES ARE GONE, which is the executed
    # form of the mark rather than a statement about it.
    for relative in (
        "tests/oracles/test_certificate.py",
        "tests/golden/test_certificate_against_registry.py",
        "tests/unit/test_certificate_acceptance_side.py",
        "tests/unit/test_certificate_budget.py",
        "tests/unit/test_certificate_exact_arithmetic.py",
        "tests/unit/test_certificate_substrate.py",
    ):
        assert not (REPO_ROOT / relative).exists(), relative


@pytest.mark.contract
@pytest.mark.oracle
def test_the_six_repoints_are_read_through_the_repointing_table() -> None:
    """A re-point moves the CLAIM and leaves the entry's own tuple alone.

    "Run B changes the ``claims`` tuple and NOTHING ELSE: no value, no
    derivation and no verdict of any of these moves." The frozen tuple is what
    records which claim the 0.4.0 proof was written under, so the new tuple is
    carried BESIDE it and read through :func:`claims_at_1_0_0`.
    """
    assert len(REPOINT_AT_RUN_B_1_0_0) == 6
    for name, old_claims, new_claims, _ in REPOINT_AT_RUN_B_1_0_0:
        entry = oracle(name)
        # The entry itself is untouched -- byte-immutability.
        assert entry.claims == old_claims, name
        # And the live reading is the new tuple.
        assert claims_at_1_0_0(entry) == new_claims, name
        assert repointing(name) == new_claims, name
        assert "C19" not in new_claims and "C13" not in new_claims, name

    # ALL SIX MOVE FOR ONE REASON, and it is worth asserting rather than
    # trusting: the acceptance-side linear minimization was inside C19 and is
    # inside C22, where Remark rem:acc-side records that its acceptance half
    # is DISCHARGED, not assumed.
    assert all("C22" in new for _, _, new, _ in REPOINT_AT_RUN_B_1_0_0)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_deleted_pending_rows_are_marked_and_not_removed() -> None:
    """The two-instance freeze forbids a deletion inside a frozen file.

    Even of an inventory row: a row that is GONE cannot be read as having been
    disposed of deliberately, and the whole point of the hand-off invariant is
    that every pair is work someone accounted for. So the rows stand and the
    disposal is recorded beside them.
    """
    assert len(PENDING_ROWS_SUPERSEDED_BY_SCOPE_1_0_0) == 2
    pending = set(PENDING_RETIREMENT_AT_RUN_B)
    for relative, name, ground in PENDING_ROWS_SUPERSEDED_BY_SCOPE_1_0_0:
        assert (relative, name) in pending, relative
        assert pending_row_superseded(relative, name)
        assert not (REPO_ROOT / relative).exists(), relative
        assert len(ground) > 60, relative


@pytest.mark.contract
@pytest.mark.oracle
def test_run_a_s_group_9_row_carries_run_b_s_dated_correction() -> None:
    """The F-2 correction, BESIDE run A's row and never in place of it.

    Run A wrote that "EVERY GROUP 9 FAMILY IS BLOCK-DIAGONAL WITH 1x1 BLOCKS,
    WHERE THE TWO NORMS COINCIDE" and concluded that "no frozen defect value
    moves". THE PREMISE IS FALSE FOR THREE FAMILIES and the conclusion fails for
    one number. Run A's sentence stands -- a mark that erased the sentence it
    corrects would take with it the record of what was believed -- and the
    correction stands next to it.
    """
    rows = dict(NOT_SUPERSEDED_BY_1_0_0)
    key = "OPTOL_FAMILIES and the (H)/(P)/(C) admission cases of Group 9"
    assert key in rows
    # RUN A'S TEXT IS INTACT, which is what makes this a correction.
    assert "WHERE THE TWO NORMS COINCIDE" in rows[key]
    assert "no frozen defect value moves" in rows[key]

    # AND THE CORRECTION says run A is not rewritten and states the derivation.
    assert "Run A's text is not rewritten" in NOT_SUPERSEDED_CORRECTION_1_0_0
    assert "FALSE PREMISE" in NOT_SUPERSEDED_CORRECTION_1_0_0
    assert "eq:normconv" in NOT_SUPERSEDED_CORRECTION_1_0_0

    # THREE ROWS, and the one whose VERDICT moves is named as such.
    assert len(NORM_CHANGE_SUPERSEDED_1_0_0) == 3
    subjects = {subject for subject, _ in NORM_CHANGE_SUPERSEDED_1_0_0}
    assert subjects == {
        "OPTOL_FAMILIES: OPTOL-2D-COMP.delta_cpl",
        "OPTOL_ADMISSION_CASES: AD-2DC-below",
        "OPTOL_REPORT_CASES: REPORT-2DCOMP-boundary",
    }
    grounds = dict(NORM_CHANGE_SUPERSEDED_1_0_0)
    assert "ADMITTING direction" in grounds["OPTOL_ADMISSION_CASES: AD-2DC-below"]
    # The registry's own sentence is what makes the third row a supersession by
    # the contract's norm choice rather than by anything this run decided.
    assert (
        "componentwise maximum"
        in (grounds["OPTOL_REPORT_CASES: REPORT-2DCOMP-boundary"])
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_no_entry_is_marked_twice_across_the_four_lists() -> None:
    """The dispositions are exclusive: an entry is retired, or kept, or neither.

    Run A's own integrity file asserts this for its two lists. Run B adds two
    more, and the same rule has to hold across all four or a reader cannot tell
    what happened to an entry.
    """
    scoped = {name for name, _ in SUPERSEDED_BY_SCOPE_1_0_0}
    repointed = {name for name, _, _, _ in REPOINT_AT_RUN_B_1_0_0}
    norm_changed = {subject for subject, _ in NORM_CHANGE_SUPERSEDED_1_0_0}
    pending = {name for _, name, _ in PENDING_ROWS_SUPERSEDED_BY_SCOPE_1_0_0}

    assert not (scoped & repointed)
    # The norm-change marks name TABLE ROWS (family and case ids), not oracle
    # entries, so they cannot collide with either list -- and that is asserted
    # rather than assumed, because a subject naming both would be ambiguous.
    assert not (norm_changed & (scoped | repointed))
    # The pending rows name an ORACLE ENTRY that is already scoped, which is
    # consistent: the entry is retired and the file that pinned it is gone.
    assert pending <= scoped


@pytest.mark.contract
@pytest.mark.oracle
def test_the_spec_string_moved_and_no_meat_core_file_still_declares_0_5_0() -> None:
    """``SPEC_VERSION_0_5_0``, executed rather than merely satisfied by drift.

    Run A marked the string ``meat-core@0.5.0`` superseded: "IT NAMES A
    CONTRACT THAT IS NO LONGER THE ACCEPTED ONE. contract.tex Section 2.5 fixes
    ``artifact_bindings.mathematical_spec_version`` as the string
    ``meat-core@<contract_version>`` OF THE ACCEPTED CONTRACT, and 0.5.0 was
    superseded at the 1.0.0 G3, so every artifact declaring it is one a 1.0.0
    consumer must refuse."

    THE MARK IS THE STRING AND NOT AN IDENTIFIER, for the reason the 0.5.0 band
    gave when it marked the 0.4.0 string: "the tree holds more than one place
    that pins it independently, and marking the VALUE catches all of them and
    shrinks by itself as each is retyped". This asserts that the shrinking
    finished.

    NO NUMBER IN ANY BUNDLE CHANGES, and the registry says why: "by Theorem
    thm:optol (i) every toy in this registry is exactly admissible ... and
    carries the 0.5.0 reading verbatim. WHAT IS INVALIDATED IS THE ONE STRING."
    """
    from certiqs_key.meat_core.declaration.validation import MATHEMATICAL_SPEC_VERSION

    # THE PIN IS AN ACCEPTED VERSION OF module.yaml, and this expectation is
    # edited BY HAND when it moves (a frozen non-numerical
    # expectation an accepted claim moves is edited by hand and listed
    # old -> new). ``MATHEMATICAL_SPEC_VERSION_1_0_0`` is the FROZEN
    # registry's constant and stays what it is -- it names the 1.0.0 contract --
    # so what is asserted here is that the code's pin is the accepted version
    # and has LEFT the one the registry froze. The registry's own re-pin, a new
    # ``Supersession`` marking the string ``meat-core@1.0.0``, is the oracle
    # author's and is owed by the C3 item; it is not this batch's to write, the
    # frozen registries being read and never edited by an implementer.
    assert MATHEMATICAL_SPEC_VERSION == "meat-core@1.28.0"
    assert MATHEMATICAL_SPEC_VERSION != MATHEMATICAL_SPEC_VERSION_1_0_0
    assert MATHEMATICAL_SPEC_VERSION_1_0_0 == "meat-core@1.0.0"

    pin = next(
        record for record in SUPERSEDED_BY_1_0_0 if record.name == "SPEC_VERSION_0_5_0"
    )
    assert pin.scan_pattern == MATHEMATICAL_SPEC_VERSION_0_5_0 == "meat-core@0.5.0"
    assert pin.replacement == ("MATHEMATICAL_SPEC_VERSION_1_0_0",)

    # AND NO meat-core FILE STILL DECLARES IT. The sibling modules' suites are
    # other bands' artifacts and are deliberately outside this scan, exactly as
    # they are outside run A's own hand-off invariant.
    #
    # THE SHARED-FORMAT FILES THAT NAME THE STRING ARE NOT OFFENDERS, which is
    # worth saying rather than filtering silently. They belong to the ``domain``
    # tier, and what they use the string for is an EXAMPLE OF THE SHAPE
    # ``<module-id>@<version>`` -- ``test_domain_manifest.py`` in particular
    # uses it in a list of MALFORMED variants to check that the format refuses
    # them. None is an artefact binding of this module, and none is this batch's
    # to edit: ``domain`` is outside the meat-core move's write set.
    #
    # THE NAMES ARE ``test_domain_manifest.py`` and
    # ``test_domain_bundle_roundtrip.py``.
    FORMAT_EXAMPLES = {
        "test_domain_manifest.py",
        "test_domain_bundle_roundtrip.py",
    }
    offenders = [
        path.name
        for path in SCANNED
        if path.name not in FORMAT_EXAMPLES
        and pin.scan_pattern in path.read_text(encoding="utf-8")
        and "SUPERSEDED_BY_1_0_0" not in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], offenders
