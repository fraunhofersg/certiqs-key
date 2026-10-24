"""The transmitter's two interfaces against the code's vocabulary.

MOTIVATION, AND THE ERROR CLASS IT CATCHES. The interface files are binding for
the implementation: "the code is written onto these names, not the reverse"
(``artifact_bindings.package_note``). The failure this file makes visible is a
refusal string declared in one artefact and emitted by nothing in the other,
invisible to a suite whose tests compare the interface against the CLAIMS and
never against the enum.

WHAT IS ASSERTED, and the one thing that is deliberately not.

1. EVERY REASON EITHER INTERFACE TABLES IS A MEMBER OF THE OWNING ENUM, and the
   member's value is the tabled string exactly. A frozen spelling that drifted by
   a character would be a refusal a consumer cannot recognise.
2. EVERY MEMBER OF EITHER ENUM IS TABLED, so a string the code can emit and the
   interface does not name cannot exist. This module has no
   ``<family>_<identifier>_failed`` family of its own, unlike the compiler, so the
   inclusion holds in both directions here.
3. THE STRINGS WITH FROZEN SPELLINGS ARE THE ONES THE INTERFACE NAMES AS
   FROZEN (``frozen_spellings``). Those are the spellings a consumer already
   froze.
4. THE ASSUMPTION LEDGER'S EMISSION RULE, as the row states it.

NOT ASSERTED: that every tabled reason is CONSTRUCTED somewhere in the package.
Where a row's reachability needs saying, the row says it (its ``reachable``
field), so a construction check would have to encode that record a second time,
and the record is already written where it belongs, on the rows.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from certiqs_key.transmitter.decoy.reasons import (
    DECOY_ASSUMPTION_MACHINE_KEYS,
    DecoyAssumptionId,
    DecoyRefusalReason,
)
from certiqs_key.transmitter.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    REFUSAL_REASONS_CARRIED_VERBATIM,
    AssumptionId,
    CertificateForm,
    RefusalReason,
    SourceMode,
)

pytestmark = [pytest.mark.contract, pytest.mark.oracle]

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "spec" / "modules" / "transmitter" / "interface.yaml"
DECOY = CORE.parent / "decoy" / "interface.yaml"


def _document(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_the_cores_refusal_table_and_its_enum_are_the_same_vocabulary() -> None:
    """Every tabled string is a member, and every member is tabled."""
    table = {row["reason"] for row in _document(CORE)["refusal_reasons"]["table"]}
    spelled = {str(reason) for reason in RefusalReason}
    assert table == spelled


def test_the_decoys_refusal_table_and_its_enum_are_the_same_vocabulary() -> None:
    """The submodule's four, and the two of the core's it trips most are the core's."""
    reasons = _document(DECOY)["refusal_reasons"]
    table = {row["reason"] for row in reasons["table"]}
    assert table == {str(reason) for reason in DecoyRefusalReason}
    # The two it trips most are listed APART and are the core's strings, not
    # re-spelled here: "the condition is a condition of the ensemble
    # presentation and not of the decoy source".
    borrowed = {
        row["reason"]
        for row in reasons["reasons_of_the_core_this_submodule_trips_most"]
    }
    assert borrowed == {
        str(RefusalReason.FORMED_ENTRY_NOT_DECLARABLE),
        str(RefusalReason.ENSEMBLE_PRESENTATION_NOT_ADMISSIBLE),
    }
    assert borrowed.isdisjoint(table)
    # NO STRING HERE HAS A FROZEN SPELLING.
    assert reasons["frozen_spellings"] == []


def test_the_carried_spellings_are_the_ones_the_interface_names_as_carried() -> None:
    """Three strings that were frozen, and they may not drift."""
    carried = set(_document(CORE)["refusal_reasons"]["frozen_spellings"])
    assert carried == {str(reason) for reason in REFUSAL_REASONS_CARRIED_VERBATIM}
    assert carried == {
        "alice_marginal_trace_rounds",
        "alice_povm_summation_rounds",
        "link_kind_deferred",
    }


def test_the_emission_rule_of_the_ledger_is_the_codes_machine_keys() -> None:
    """The ``assumption_ledger`` output row's ``emission_rule``, by short id.

    THE ROW NAMES SHORT IDS AND THE CODE EMITS MACHINE KEYS, and the declared
    mapping between them is the row's ``ledger_spelling``. What this test pins
    is that the short ids the rule names are exactly the ones the code has a key
    for, so that the mapping is total on them and not a gap.
    """
    rows = _document(CORE)["outputs"]
    ledger = next(row for row in rows if row["name"] == "assumption_ledger")
    rule = ledger["emission_rule"]
    assert rule["always"] == ["A-SEQ"]
    # A-ENS in trusted mode only.
    assert rule["trusted_mode_matrix_declared_ensemble"] == ["A-ENS"]
    assert rule["trusted_mode_d_A_at_least_2"] == ["A-SRC"]
    assert rule["trusted_mode_d_A_equals_1"] == []
    assert rule["untrusted_mode"] == []
    named = (set(rule["always"]) | set(rule["trusted_mode_matrix_declared_ensemble"])
             | set(rule["trusted_mode_d_A_at_least_2"]))
    assert named == {str(member) for member in AssumptionId}
    assert set(ASSUMPTION_MACHINE_KEYS) == set(AssumptionId)


def test_the_decoy_ledger_rule_puts_a_wcp_in_the_place_of_a_ens() -> None:
    """``ass:wcp``'s place in the ledger, and the two it never emits."""
    rows = _document(DECOY)["outputs"]
    ledger = next(row for row in rows if row["name"] == "assumption_ledger")
    rule = ledger["emission_rule"]
    assert rule["always"] == ["A-WCP", "A-SEQ"]
    assert rule["conditional"] == {"A-SRC": "trusted-source mode at d_A >= 2"}
    assert rule["never"] == ["A-ENS"]
    assert set(DECOY_ASSUMPTION_MACHINE_KEYS) == set(DecoyAssumptionId)
    assert str(DecoyAssumptionId.A_WCP) == "A-WCP"


def test_the_soundness_registry_of_the_interface_is_the_registry_the_code_emits() -> (
    None
):
    """The ``soundness_registry`` output row's table, entry by entry.

    The registry is CLOSED and "adding one is a claim batch, not a
    configuration", so the interface's table and the module constant are two
    spellings of one datum and a drift between them is a defect.
    """
    from certiqs_key.transmitter.links import (
        DECLARED_KINDS_WITHOUT_A_SOUNDNESS_CLAIM,
        SOUNDNESS_REGISTRY,
    )

    rows = _document(CORE)["outputs"]
    registry = next(row for row in rows if row["name"] == "soundness_registry")
    admitted = [
        entry for entry in registry["table"] if entry["soundness_claim"] is not None
    ]
    assert len(admitted) == len(SOUNDNESS_REGISTRY)
    for tabled, emitted in zip(admitted, SOUNDNESS_REGISTRY, strict=True):
        assert tabled["kind"] == str(emitted.kind)
        assert tabled["soundness_claim"] == emitted.soundness_claim
        assert tuple(tabled["assumptions"]) == emitted.assumptions
    declared_only = [
        entry["kind"]
        for entry in registry["table"]
        if entry["soundness_claim"] is None
    ]
    assert declared_only == [
        str(kind) for kind in DECLARED_KINDS_WITHOUT_A_SOUNDNESS_CLAIM
    ]


def test_the_three_declared_forms_are_the_ones_the_licence_row_names() -> None:
    """The three declared forms the licence record may name.

    The ``source_replacement_license`` row: ``pure``, ``block`` or
    ``ensemble_presentation``, "because which conditions were decided depends
    on it".
    """
    text = CORE.read_text(encoding="utf-8")
    for form in CertificateForm:
        assert f"`{form.value}`" in text or f"``{form.value}``" in text or (
            form.value in text
        )
    assert {str(form) for form in CertificateForm} == {
        "pure",
        "block",
        "ensemble_presentation",
    }


def test_the_emitted_wire_keys_are_the_output_table() -> None:
    """The record and the outputs table may not disagree SILENTLY.

    Every key on the wire has an ``outputs`` row and every row a key. The
    degenerate record (one sector, pure form, empty segment) carries the
    table's names minus the rows the interface lists in
    ``artifact_bindings.rows_whose_key_the_degenerate_record_omits``; an
    ensemble presentation's record carries every row's key. A key added
    without a row fails here, and so does a row written without a key.

    The four keys ``alice_marginal_slot_filled``, ``certificate_form``,
    ``alice_ensemble_operators`` and ``virtual_ensemble_weighted_members``
    have rows, and the interface has no pending list.
    """
    from fractions import Fraction

    from certiqs_key.foundations.blocks import BlockKind, SectorStructure
    from certiqs_key.foundations.exact import matrix
    from certiqs_key.transmitter.artifact import SourceSpecification, emit_artifact
    from certiqs_key.transmitter.presentation import EnsemblePresentation

    document = _document(CORE)
    bindings = document["artifact_bindings"]
    tabled = {row["name"] for row in document["outputs"]}
    omitted = set(bindings["rows_whose_key_the_degenerate_record_omits"])
    assert omitted <= tabled

    degenerate = emit_artifact(
        SourceSpecification(
            signal_alphabet=("x0",),
            transmitted_dim=1,
            signal_weights={"x0": Fraction(1)},
            signal_states={"x0": matrix(((1,),))},
            alice_dim=1,
            alice_povm={"x0": matrix(((1,),))},
        )
    ).require()
    assert degenerate.is_degenerate_presentation
    assert set(degenerate.as_machine_record()) == tabled - omitted

    sectors = SectorStructure(
        labels=("A",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
    )
    half = Fraction(1, 2)
    presented = emit_artifact(
        SourceSpecification(
            signal_alphabet=("x0", "x1"),
            transmitted_dim=2,
            signal_weights={"x0": half, "x1": half},
            signal_states={
                "x0": matrix(((1, 0), (0, 0))),
                "x1": matrix(((0, 0), (0, 1))),
            },
            source_mode_request=SourceMode.TRUSTED,
            ensemble_presentation=EnsemblePresentation(
                virtual_sectors=sectors,
                weighted_blocks={
                    "x0": (matrix(((half, 0), (0, 0))),),
                    "x1": (matrix(((0, 0), (0, half))),),
                },
            ),
        )
    ).require()
    # EVERY ROW'S KEY APPEARS on a presentation, so the table carries no name
    # nothing emits.
    assert set(presented.as_machine_record()) == tabled


def test_the_kind_vocabulary_of_the_interface_is_the_codes() -> None:
    """The ``source_segment`` row's ``kind_vocabulary`` and its two subsets."""
    from certiqs_key.transmitter.links import SourceLinkKind

    rows = _document(CORE)["inputs"]
    segment = next(row for row in rows if row["name"] == "source_segment")
    assert set(segment["kind_vocabulary"]) == {str(kind) for kind in SourceLinkKind}
    assert segment["kinds_with_a_soundness_claim"] == ["tagging"]
    assert segment["kinds_declared_and_refused"] == ["source-map"]
    added = _document(DECOY)["link_kind"]["adds"]
    assert added == ["tagging"]
