"""The frozen registry, the claim files, interface.yaml and the code agree.

ONE TEST PER ABSENT ONE. An earlier arrangement bound this
registry to a single interface transcription
and to a ``contract.tex`` pinned by content hash; neither document exists here
and neither will. Thirteen such tests are absent and the header of
``test_protocol_compiler_registry.py`` lists all thirteen with its reason for
each. SIX ARE RE-ESTABLISHABLE against THIS repository's artefacts -- the 45
claim files under spec/modules/protocol-compiler/claims/ and the interface.yaml
beside them -- and they are here, under the name the removed one had wherever
the subject is unchanged.

WHAT EACH CATCHES: a claim id, a ledger row, a machine key, a refusal string, a
convention or a recorded parameter that exists on one side of the boundary and
not on the other. The reductions move made the same call for the same reason
and its file says so in the same words
(``test_reductions_registry_interface.py``).

WHAT IS DIFFERENT HERE, AND IT IS THE POINT OF THE BATCH. The frozen registry
was authored against a contract whose PC10, PC11 and PC12 are no longer this
module's, and whose assumption ledger had eleven rows where this module now
owns seven. THE REGISTRY IS NOT EDITED. Every test below states the mapping
explicitly -- which frozen label resolves in which module's claim files, which
ledger row is inherited from which supplier -- so that a reader can see where
each went rather than infer it from a silence.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import claim_codes
import pytest
import registry_instances_bb84 as bb84
import registry_protocol_compiler as core
import registry_transmitter as transmitter
import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "spec" / "modules" / "protocol-compiler"
CLAIMS = SPEC / "claims"
INTERFACE = SPEC / "interface.yaml"

#: The twelve oracle claim labels, and where each one's mathematics is
#: in THIS repository. PC1-PC9 are the compiler's own claim files; PC10 and
#: PC11 belong to ``transmitter``; PC12 is ``instances/bb84/`` and is not a
#: claim at all. All three are read from
#: ``claim_codes.yaml``, the one table where the oracle codes meet this
#: repository's claim ids.
WHERE_EACH_LABEL_WENT: dict[str, tuple[str, ...]] = claim_codes.labels(
    "PC", "protocol-compiler"
)
RETIRED_TO_THE_TRANSMITTER = tuple(claim_codes.labels("PC", "transmitter"))
MOVED_TO_THE_INSTANCE = claim_codes.no_claim("PC")


def _interface() -> dict[str, Any]:
    with INTERFACE.open(encoding="utf-8") as handle:
        document: dict[str, Any] = yaml.safe_load(handle)
    return document


def _claim_ids() -> set[str]:
    """Return every claim id declared under this module, from the files."""
    ids: set[str] = set()
    for path in sorted(CLAIMS.glob("*.tex")):
        match = re.search(
            r"^% id: protocol-compiler/(?P<id>\S+)$",
            path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        assert match is not None, path.name
        ids.add(match.group("id"))
    return ids


@pytest.mark.contract
@pytest.mark.oracle
def test_every_oracle_claim_id_resolves_in_the_module_that_owns_it() -> None:
    """Traceability, re-established across the three modules the labels went to.

    THE ABSENT TEST read a ``claims:`` block of an earlier
    interface.yaml. There is no such block here: a claim is a FILE, and the id
    is in its header. So the mapping is stated above and checked here -- every
    label a frozen entry names resolves either to claim files of this module,
    or to the module the label was retired to, or to the instance.
    """
    named = {claim for entry in core.PC_ORACLES for claim in entry.claims}
    named |= {
        claim for entry in transmitter.TRANSMITTER_PC_ORACLES for claim in entry.claims
    }
    named |= {claim for entry in bb84.BB84_PC_ORACLES for claim in entry.claims}
    assert named <= set(WHERE_EACH_LABEL_WENT) | set(RETIRED_TO_THE_TRANSMITTER) | set(
        MOVED_TO_THE_INSTANCE
    )

    present = _claim_ids()
    for label, claim_ids in WHERE_EACH_LABEL_WENT.items():
        for claim_id in claim_ids:
            assert claim_id in present, (label, claim_id)

    # PC10 and PC11 resolve in the TRANSMITTER's claim files and in none of
    # this module's.
    transmitter_claims = ROOT / "spec" / "modules" / "transmitter" / "claims"
    for claim_id in (
        "def:srcert",
        "thm:certificate-sufficiency",
        "fact:sr",
        "cor:noncanonical",
    ):
        slug = claim_id.replace(":", "-").lower()
        assert (transmitter_claims / f"{slug}.tex").is_file(), claim_id
        assert claim_id not in present, claim_id

    # PC12 is not a claim of any module; it is the instance.
    assert (ROOT / "instances" / "bb84" / "specification.py").is_file()
    assert "def:bb84spec" not in present
    assert "thm:pc12" not in present


@pytest.mark.contract
@pytest.mark.oracle
def test_the_interface_carries_the_ledger_the_registry_froze() -> None:
    """Nine own rows and five inherited, against the frozen ten (and A-WCP).

    THE FROZEN TEN ARE NOT EDITED. Four of them are other modules' assumptions
    now and appear under ``inherited_rows``; one --
    A-RHOM -- keeps its statement and takes a new machine key, because keys are
    repository-wide and ``receiver`` owns ``round_homogeneity``; one -- A-LIC --
    is A-ATK, the two ids being one file under
    the engine's id, same key. A-BLOCK is the
    eleventh row the frozen ledger never had and the registry's own scope mark
    says so.

    A-SPEC is split. Its
    decided conditions became ``def:well-formed-spec``; A-PRESENT and
    A-ALICE-MEAS are own rows the frozen ledger never had; A-SPEC keeps its
    statement's remaining clauses and takes the key
    ``specification_describes_apparatus``. The frozen row is not edited: the
    key rename is read through ``renamed``, as A-RHOM's is.

    A-ALICE-MEAS's key became
    ``alice_measurement_as_declared`` (was ``alice_measurement_untrusted``)
    when its scope widened to ``d_A = 1``. It is not a frozen row.

    the frozen row A-BLOCK
    (``block_diagonal_feasible_set``) is RETIRED, the restriction it named
    being the remark ``rem:block-restriction`` that meat-core/thm:reduction,
    step 1, proves. The frozen row is not edited; it is read through
    ``retired_here``.

    A-PRESENT, an
    own row the frozen ledger never had, is RETIRED into
    ``def:well-formed-spec`` (iv) and ``req:physical-family-decision``; its key
    ``presented_receiver_family`` is no row of the interface.
    """
    document = _interface()
    ledger = document["assumption_ledger"]
    own = {row["id"]: row["machine_key"] for row in ledger["own_rows"]}
    inherited = {row["id"]: row["machine_key"] for row in ledger["inherited_rows"]}
    assert set(own) == {
        "A-SPEC",
        "A-ALICE-MEAS",
        "A-RHOM",
        "A-COIN",
        "A-LINK",
        "A-ATK",  # A-LIC before the two ids merged
        "A-IDEAL",
    }
    assert own["A-RHOM"] == "round_homogeneity_declaration"
    assert own["A-SPEC"] == "specification_describes_apparatus"
    assert "presented_receiver_family" not in own.values()
    assert own["A-ALICE-MEAS"] == "alice_measurement_as_declared"

    renamed = {"A-RHOM", "A-SPEC"}
    retired = {"A-SEQ": "A-SEQ", "A-ENS": "A-ENS", "A-RET": "A-SRC"}
    merged = {"A-LIC": "A-ATK"}  # one file under the engine's id, same key
    # A-BLOCK: rem:block-restriction since B5b; no row. A-RECV: the reductions
    # artefact's own row, emitted or omitted there
    # (reductions/req:recv-row-provenance); this module emits none on any route
    # (assumption_ledger.a_recv_not_emitted_note).
    retired_here = {"A-BLOCK", "A-RECV"}
    for row in core.LEDGER_ROWS:
        if row.assumption_id in retired_here:
            assert row.assumption_id not in own and row.assumption_id not in inherited
            continue
        if row.assumption_id in merged:
            assert own[merged[row.assumption_id]] == row.machine_key, row.assumption_id
            continue
        if row.assumption_id in retired:
            here = retired[row.assumption_id]
            assert here in inherited, row.assumption_id
            assert inherited[here] == row.machine_key, row.assumption_id
            continue
        assert row.assumption_id in own, row.assumption_id
        if row.assumption_id not in renamed:
            assert own[row.assumption_id] == row.machine_key, row.assumption_id

    # And the interface's never-verified list agrees with the frozen one.
    # FROZEN UNION
    # ADDED. Added to the own list: A-SPEC, A-RHOM, A-COIN
    # and A-IDEAL; to the inherited list: A-SEQ and A-ENS (frozen rows read as
    # decided in 0.3.0) and the decoy submodule's A-WCP (a row the frozen
    # ledger predates, which the interface now declares). The frozen ten and
    # their four never-verified rows are not edited. A-SPEC's split part
    # A-ALICE-MEAS joins the own list; A-PRESENT, retired, is in neither.
    # A-RECV, a frozen never-verified row, left the inherited list: it is no
    # row of this module's ledger, and stays never verified in reductions,
    # its owner (reductions/ass:recv).
    never = document["never_verified"]
    frozen_never = {row.assumption_id for row in core.LEDGER_ROWS if row.never_verified}
    assert set(never["own"]) == {"A-LINK", "A-ATK"} | {
        "A-SPEC", "A-ALICE-MEAS", "A-RHOM", "A-COIN", "A-IDEAL"
    }
    assert set(never["inherited"]) == {"A-SRC"} | {
        "A-SEQ", "A-ENS", "A-WCP"
    }
    assert inherited["A-WCP"] == "wcp_source_model"
    assert "consumer_obligation" not in never
    assert {"A-LINK", "A-LIC", "A-RECV", "A-RET"} == frozen_never


@pytest.mark.contract
@pytest.mark.oracle
def test_the_interface_key_vocabulary_is_the_frozen_one_plus_what_moved() -> None:
    """Every frozen machine key is in the interface, or moved with its object.

    THE ABSENT TEST asserted the frozen tuples as subsets of the interface's
    key tables. Four input keys are the transmitter's now and one is retired
    , so the subset is stated of the rest and the five are named --
    which is what makes this a supersession of a TABLE and not of a vocabulary.
    """
    document = _interface()
    inputs = [row["name"] for row in document["inputs"]]
    outputs = [row["name"] for row in document["outputs"]]
    retired = [row["name"] for row in document["retired_input_rows"]]

    moved_to_the_transmitter = {
        "alice_system",
        "alice_povm_spec",
        "source_replacement_certificate",
    }
    assert moved_to_the_transmitter <= set(core.INPUT_KEYS)
    assert retired == ["source_mode_request"]
    assert "source_mode_request" in core.INPUT_KEYS
    carried = [
        name
        for name in core.INPUT_KEYS
        if name not in moved_to_the_transmitter and name not in retired
    ]
    assert set(carried) <= set(inputs)
    # The frozen registry is NOT regenerated: what moved is
    # this expectation, and it moved because interface.yaml gained NINE
    # GENERAL-FORMAT INPUT ROWS, each present ONLY in the general format and each
    # absent spelling today's format (the block headed "THE GENERAL FORMAT'S INPUT
    # ROWS"; def:spec (a')-(e')). Old -> new: the three names below -> the same
    # three plus these nine. Nothing was removed and no frozen row moved.
    #
    # one more input row, `chain_provenance`, the run's record beside
    # the specification that req:link-row-provenance reads for A-LINK's
    # presence rule. Old -> new: the set below plus that one name.
    assert set(inputs) - set(carried) == {
        "chain_provenance",
        "target_povm",
        "transmitter_artifact",
        "choice_weighting",
        "alice_sector_factor",
        "alice_form",
        "alice_ensemble",
        "receiver_parts",
        "reduction_chain.receiver_segments",
        "reduction_chain.source_segment",
        "public_structure.transcript",
        "constraint_entries.scope_and_tag",
        "feasibility_witness.joint",
    }

    # EVERY FROZEN OUTPUT KEY SURVIVES, and the additions are named.
    # interface.yaml gained EIGHT GENERAL-FORMAT OUTPUT ROWS (the block headed
    # "THE GENERAL FORMAT'S OUTPUT ROWS"), each emitted ONLY in the general format
    # and each absent spelling today's format. Old -> new: the five names above ->
    # the same five plus these eight. Two of the eight are DOTTED, naming a second
    # SHAPE of a key the frozen tuple already has rather than a new key
    # (`alice_marginal.blocks`, `bob_povm.per_factor`), and one names a second tag
    # VALUE (`constraint_rhs_tag.party_local`); they are listed here because this
    # test reads row NAMES, and the code emits them as the sibling keys
    # `alice_marginal_blocks`, `alice_povm_blocks` and `bob_povm_factors` for the
    # reason the shared format records at Declaration.alice_marginal_blocks.
    #
    # one more output row, `assumption_bindings`, the declared values
    # each ledger row binds, beside `assumption_ledger`. Old -> new: the set
    # below plus that one name. No frozen key is touched.
    #
    # one more output row, `reference_companion`, the compiled reference
    # companion beside the declaration
    # (protocol-compiler/req:reference-companion-compiled), which the code
    # forms now (certiqs_key.protocol_compiler.companion). Old -> new: the set
    # below plus that one name. No frozen key is touched.
    assert set(core.OUTPUT_KEYS) <= set(outputs)
    assert set(outputs) - set(core.OUTPUT_KEYS) == {
        "sector_block_kind",
        "constraint_rhs_tag",
        "choice_weighting_record",
        "assumption_ledger",
        "assumption_bindings",
        "mathematical_spec_version",
        "sector_factorisation",
        "alice_form",
        "alice_ensemble",
        "alice_marginal.blocks",
        "bob_povm.per_factor",
        "transcript",
        "constraint_scope",
        "constraint_rhs_tag.party_local",
        "reference_companion",
    }
    # The declaration's own slots are a subset of the outputs, as they were.
    assert set(core.DECLARATION_SLOT_KEYS) <= set(outputs)
    assert set(core.NOT_OUTPUTS).isdisjoint(outputs)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_verbatim_refusal_strings_are_the_frozen_ones() -> None:
    """The frozen spellings and every other class of ``refusal_reasons``.

    THE FROZEN TUPLE IS TWO STRINGS -- the registry was authored at 0.1.4,
    where the contract named two -- and its own scope mark records the five
    that arrived with the exact number model. Both halves are asserted here,
    against the interface rather than against a second contract document.

    THE CLASS KEYS ARE NAMED BY WHAT THEIR STRINGS REFUSE: `frozen_spellings`,
    `setting_dependent_weighting`,
    `conditional_family`, `physical_family`, `band_a_route`,
    `source_identity_at_da1`, `general_format` and `source_mode_rule`.
    `weight_list` is new with
    req:weight-list's `choice_weights_not_normalized`. Every string is
    unchanged but that one.
    """
    document = _interface()
    reasons = document["refusal_reasons"]
    carried = set(reasons["frozen_spellings"])
    weight_list = set(reasons["weight_list"])
    new = set(reasons["setting_dependent_weighting"])
    mine = set(reasons["this_files_own_spelling"])
    # def:weighted's own spelling and not this file's -- which is why it is
    # its own class beside `this_files_own_spelling` rather than inside it.
    conditional = set(reasons["conditional_family"])
    # req:physical-family-decision's one string (a new class beside the
    # conditional one).
    physical = set(reasons["physical_family"])
    # The declared-data parts of premises, each its requirement's one string:
    # req:band-a-ideal-receiver and req:band-a-identity-link (the Band-A
    # route's two), and req:da1-source-identity.
    band_a = set(reasons["band_a_route"])
    source_identity = set(reasons["source_identity_at_da1"])
    # Seven strings, each spelled by a CLAIM of this module -- def:compile,
    # def:validator, thm:gates and def:chaincond -- and not by this file.
    general_format = set(reasons["general_format"]["strings"])
    # The source-mode half of reductions/def:chain's admission rule, separate
    # from the general format's seven and from the transmitter's reused
    # reasons.
    source_mode = set(reasons["source_mode_rule"]["strings"])

    assert {str(reason) for reason in core.REFUSAL_REASONS_VERBATIM} <= carried
    assert len(carried) == 7
    assert weight_list == {"choice_weights_not_normalized"}
    assert new == {"choice_weight_depends_on_outcome", "choice_weight_not_stochastic"}
    assert mine == {"chain_interface_condition_failed"}
    assert conditional == {"conditional_family_not_admissible"}
    assert physical == {"physical_family_not_admissible"}
    from certiqs_key.protocol_compiler import REFUSAL_REASONS_PHYSICAL_FAMILY

    assert physical == {str(reason) for reason in REFUSAL_REASONS_PHYSICAL_FAMILY}
    from certiqs_key.protocol_compiler import (
        REFUSAL_REASONS_BAND_A_ROUTE,
        REFUSAL_REASONS_SOURCE_IDENTITY_AT_DA1,
    )

    assert band_a == {"band_a_outside_ideal_receiver", "band_a_link_not_identity"}
    assert band_a == {str(reason) for reason in REFUSAL_REASONS_BAND_A_ROUTE}
    assert source_identity == {"da1_source_identity_failed"}
    assert source_identity == {
        str(reason) for reason in REFUSAL_REASONS_SOURCE_IDENTITY_AT_DA1
    }
    assert source_mode == {"source_segment_in_untrusted_mode"}
    assert general_format == {
        "ensemble_form_in_untrusted_mode",
        "alice_sector_marginal_zero",
        "alice_ensemble_marginal_mismatch",
        "alice_ensemble_sum_rounds",
        "constraint_scope_not_a_factor",
        "ensemble_presentation_without_ensemble_form",
        "general_entry_beside_source_segment",
    }

    # EVERY STRING THE TABLE ROWS NAME IS IN ONE OF THOSE CLASSES, and the ones the
    # transmitter owns are listed apart rather than mixed in.
    tabled = {row["reason"] for row in reasons["table"]}
    assert tabled == (
        carried
        | weight_list
        | new
        | mine
        | conditional
        | physical
        | band_a
        | source_identity
        | general_format
        | source_mode
    )
    elsewhere = reasons["reasons_that_belong_to_another_module"]
    owners = {row["owner"] for row in elsewhere}
    assert owners == {"transmitter"}


@pytest.mark.contract
@pytest.mark.oracle
def test_alpha_and_purifier_dim_are_recorded_and_are_not_parameters() -> None:
    """Two rows, both recorded for the consumer and depended on by no claim.

    The frozen registry says the module "declares NO per-result assurance
    label" and no free numerical parameter; the interface says the same of
    these two and marks both ``fixed_here``, which is the honest statement that
    no claim of this module states either row.
    """
    document = _interface()
    parameters = document["parameters"]
    assert parameters["free_numerical_parameters"] == "none"
    rows = {row["name"]: row for row in parameters["rows"]}
    assert set(rows) == {"alpha", "purifier_dim"}
    for row in rows.values():
        assert "fixed_here" in row
        assert "NO CLAIM" in row["fixed_here"].upper()
    assert rows["alpha"]["domain"] == "(1, 2)"
    # AND NO TOLERANCE, IN EITHER DIRECTION.
    assert "NONE" in parameters["tolerances"].upper()


@pytest.mark.contract
@pytest.mark.oracle
def test_the_conventions_are_named_and_the_dropped_tier_is_in_none_of_them() -> None:
    """The conventions block, re-established against this interface.

    THE ABSENT TEST counted eleven bullets of an earlier contract. The
    count is not a fact about this repository -- interface.yaml carries the
    seventeen conventions with their notes as separate keys -- so what is
    asserted is what is actually promised: every convention the
    frozen registry's derivations lean on is present BY NAME, and the dropped
    ``certified`` tier is in none of them (PRINCIPLES.md section 10).
    """
    document = _interface()
    conventions = document["conventions"]
    for name in (
        "number_model",
        "exact_decisions",
        "summation_order",
        "operator_form",
        "no_snapping",
        "decide_never_infer",
        "fail_closed",
        "source_model",
        "subsystem_order",
        "test_statistics_model",
        "chain_order",
        "conjugation_basis",
    ):
        assert name in conventions, name
    rendered = yaml.safe_dump(conventions)
    assert "certified" not in rendered


@pytest.mark.contract
@pytest.mark.oracle
def test_every_reason_the_interface_fixes_is_one_the_code_can_emit() -> None:
    """The ``refusal`` output row: "the reason vocabulary is refusal_reasons".

    NOTHING ELSE HELD THIS TOGETHER. ``chain_interface_condition_failed`` -- the
    ONE spelling interface.yaml fixes on its own -- was declared in
    ``RefusalReason`` and emitted by nothing, while the code refused a chain
    with nine finer strings the interface's vocabulary does not contain. The
    six re-established interface tests beside this one compare the interface
    against the CLAIMS and never against the enum, so the disagreement was
    invisible to the suite.

    WHAT IS ASSERTED, and the one thing that is deliberately NOT.

    1. EVERY REASON THE INTERFACE FIXES IS A MEMBER OF THE ENUM, and every one
       of them is CONSTRUCTED somewhere in the package -- read off the source,
       so that a declared-and-dead member is a failure and not a comment.
    2. NO RETIRED SPELLING SURVIVES, in either the enum or the table.
    3. WHAT THE INTERFACE DOES NOT TABLE IS EXACTLY THIS MODULE'S OWN
       ``<family>_<identifier>_failed`` SPELLINGS, plus the transmitter's five.
       That split is the reasons module's own rule and the interface's: the
       claims "fix the naming OBLIGATION and the IDENTITY of the named check
       and NOT a spelling" for V1-V8 and (G1)-(G3), so those strings are the
       implementation's and the interface tables only what it FIXES. Asserting
       the reverse inclusion would demand that the interface spell them, which
       is the decision neither file took.
    """
    import re

    from certiqs_key.protocol_compiler.reasons import (
        RETIRED_CHAIN_REFUSAL_REASONS,
        RefusalReason,
        refusal_from_transmitter,
    )
    from certiqs_key.transmitter.reasons import Refusal as TransmitterRefusal
    from certiqs_key.transmitter.reasons import RefusalReason as TransmitterReason

    reasons = _interface()["refusal_reasons"]
    tabled = {row["reason"] for row in reasons["table"]}
    spelled = {str(reason) for reason in RefusalReason}
    package = ROOT / "src" / "certiqs_key" / "protocol_compiler"
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package.glob("*.py"))
    )

    # (1) fixed by the interface -> a member, and constructed by name.
    for reason in sorted(tabled):
        member = RefusalReason(reason)
        assert f"RefusalReason.{member.name}" in source, reason

    # (2) the nine retired spellings are in neither.
    for retired in RETIRED_CHAIN_REFUSAL_REASONS:
        assert retired not in spelled, retired
        assert retired not in tabled, retired
    assert "chain_interface_condition_failed" in tabled

    # (3) what the interface does not table is this module's own scheme, plus
    # the five the transmitter owns.
    borrowed: set[str] = set()
    for row in reasons["reasons_that_belong_to_another_module"]:
        borrowed.update(row.get("strings", []))
        if "reason" in row:
            borrowed.add(row["reason"])
    source_admission = {
        "source_link_kind_not_admitted",
        "link_kind_deferred",
        "source_link_entry_present",
        "source_link_family_excludes_its_descriptor",
        "source_link_not_in_registry",
        "source_link_assumption_not_in_ledger",
        "source_segment_not_from_admitting_module",
    }
    # These are transmitter-owned checks, dynamically converted at the
    # compiler boundary. Exercise that real path instead of requiring dummy
    # ``RefusalReason.NAME`` tokens in compiler source.
    for reason in source_admission:
        supplier = TransmitterRefusal(TransmitterReason(reason), "supplier detail")
        carried = refusal_from_transmitter(supplier)
        assert str(carried.reason) == reason
        assert carried.detail == supplier.detail
    borrowed |= source_admission
    own_scheme = re.compile(r"^(check_v[1-8]|gate_g(1|2|3a|3b))_failed$")
    for reason in sorted(spelled - tabled - borrowed):
        assert own_scheme.match(reason), reason


@pytest.mark.contract
@pytest.mark.oracle
def test_what_the_gate_report_row_emits_is_what_its_row_discloses() -> None:
    """The outputs table is BINDING; a row not implemented in full says so.

    ``outputs.gate_report`` asks for two things, a verdict per
    gate with the degeneration record AND "per exact predicate of Definition
    def:exact that the compiler decided ... THE OUTCOME, KEYED BY (source,
    element, block)" with the first-failure indices, and the second half is
    now recorded --
    :class:`~certiqs_key.protocol_compiler.transcript.PredicateTranscript`,
    emitted under ``predicates``. What the row still discloses is the RESIDUE,
    and the test's subject moves with it: not "the gap is disclosed" but "the
    two artefacts say the same thing".

    THE TEST HAS TWO HALVES AND NEEDS BOTH, which is why it is one test and
    not two. The row must carry the disclosure of what is NOT recorded, and
    the emitted record must be the thing the disclosure describes -- exactly
    ``{"gates", "predicates"}``. Move one artefact and this test fails until
    the other moves with it, which is the point: nothing else holds the two against each
    other.

    EACH ASSERTION BELOW CARRIES THE REASON IT MOVED, hand-edited and never
    regenerated from the code it tests (PRINCIPLES.md section 2.3). What the
    transcript covers and what it does not is
    ``tests/unit/test_protocol_compiler_transcript.py``, which reads the
    enumeration out of the same row; this test holds the ROW against the
    RECORD and asserts nothing about the transcript's contents.
    """
    from fractions import Fraction

    from instances.bb84.specification import bb84_specification

    from certiqs_key.protocol_compiler import compile_specification

    row = next(
        entry
        for entry in _interface()["outputs"]
        if entry["name"] == "gate_report"
    )
    status = row["implementation_status"]
    # The residue this row once disclosed was the conditional families'
    # admissibility, which the code now DECIDES -- so the disclosure must not
    # name that item, and naming it would point a reader at a gap that
    # is closed. What it must still state are the two limits on what the
    # enumeration names; the row states them without naming a closed open
    # item.
    assert "protocol-compiler-conditional-family-admissibility" not in status, (
        "the disclosure does not name a residue the code no longer has"
    )
    assert "enumeration-overreaches-the-module" not in status, (
        "and it names no closed open item"
    )
    assert "transmitter-owned ensemble conditions remain with the transmitter" in (
        status
    ), "it still states the first limit on the enumeration"
    assert "one exact equality decision" in status, (
        "and the second"
    )
    assert "protocol-compiler-gate-report-transcript" not in status, (
        "and it does not name the item the transcript batch closed"
    )
    # UNCHANGED, and it is the half that was never about the gap: the row
    # states the CONTENT, and a row that deleted its enumeration once the code
    # recorded it would leave the record describing nothing.
    assert "recorded_predicates" in row, (
        "the row still states the content the record carries; a row that "
        "deleted the content would be a scope change and not a disclosure"
    )

    half = Fraction(1, 2)
    record = compile_specification(
        bb84_specification(half, half, half, half)
    ).as_machine_record()["gate_report"]
    assert isinstance(record, dict)
    # MOVED WITH THE CODE, hand-edited: the transcript is emitted BESIDE the
    # verdicts under one new key, `predicates`. A third key, or the loss of
    # either of these two, is a change to what this row emits and must move
    # `implementation_status` with it.
    assert set(record) == {"gates", "predicates"}, (
        "the emitted gate report changed shape: re-read "
        "outputs.gate_report.implementation_status and the open items it "
        "names against it, and move them with this assertion"
    )
    # AND THE SECOND HALF IS NOT EMPTY ON THE ONE INSTANCE IN THE TREE. This
    # is the assertion the old two-key shape could not make: a `predicates`
    # key carrying `[]` would satisfy the shape above and describe neither
    # state, which is exactly the half-implemented record the open item's
    # closing condition rules out.
    predicates = record["predicates"]
    assert isinstance(predicates, list)
    assert predicates, (
        "the transcript of a compiled BB84 declaration records at least one "
        "decision; an empty one would mean the deciders stopped filling it"
    )
