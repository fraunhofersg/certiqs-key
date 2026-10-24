"""The key-rate report's "Measurement snaps" section, on hand-built records.

``runs/report/snaps.py`` (report schema 0.15.0, record 0.28.0): per block
whether it was kept or moved, where its snap started (an exact reference or
the receiver's floating-point blocks), the reference handed beside it (exact;
enclosed, with its largest radius), the run's decision (evaluated off its
snap, or resting on A-SNAP in one of four groups with cause and fix), a
visible warning for ``support_not_preserved``, the enclosure and strict
settings, and A-SNAP when the manifest lists it. The records below are written
by hand in the shape ``instances/common/declare.py`` and ``runs/record.py``
write; nothing is read from a run.

"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from report_records import (
    LAST_RESORT_FIX,
    SNAP_BLOCKS,
    completed_record,
    snap_block,
    snapped_record,
    synthetic_table,
    with_snaps,
)

import certiqs_key.runs.report as report_package
from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_html,
    render_markdown,
)

pytestmark = pytest.mark.contract


def _report(manifest_lists_a_snap: bool = True) -> Any:
    return build_report(
        snapped_record(manifest_lists_a_snap=manifest_lists_a_snap),
        table=synthetic_table(),
    )


def _evaluated_off_report() -> Any:
    """Every moved block evaluated off its snap: nothing rests on A-SNAP."""
    return build_report(
        snapped_record(blocks=SNAP_BLOCKS[:2]), table=synthetic_table()
    )


def _section(report: Any) -> Any:
    section = report["sections"]["protocol"]["measurement_snaps"]
    assert section is not None
    return section


def test_each_status_and_reference_is_said_in_plain_words() -> None:
    section = _section(_report())
    text = " ".join(section["sentences"])
    assert "3 blocks in all" in text
    assert "1 block was snapped from an exact reference" in text
    assert "2 blocks were snapped from the receiver's floating-point blocks" in text
    assert "On 1 block the run handed an exact reference" in text
    assert (
        "On 1 block the run handed an enclosed reference (your receiver model, "
        "known through rigorous rational intervals) beside the snap (largest "
        "radius 1.0e-36; largest input radius 1.0e-38)."
    ) in text
    assert "1 block is kept: your model gives it exactly" in text
    assert "1 moved block is evaluated off its snap: on it" in text
    assert "this block rests on your receiver model" in text
    # The sentences speak in the four groups a user acts on, with the group's
    # fix; the cause is the detail.
    assert (
        "1 block rests on A-SNAP in the group 'last resort' "
        f"(m=2: no_reference); what to change: {LAST_RESORT_FIX}."
    ) in text
    assert "the strict option is off" in text
    assert "enclosed references are used" in text
    assert "The assumption manifest lists A-SNAP" in text


def test_the_rows_carry_status_handed_reference_decision_and_fix() -> None:
    section = _section(_report())
    rows = {row["block"]: row for row in section["blocks"]}
    assert [rows[name]["status"] for name in ("m=0", "m=1", "m=2")] == [
        "kept", "moved", "moved"
    ]
    assert rows["m=1"]["handed_kind"] == "enclosed"
    assert rows["m=1"]["handed_radius"] == "1/1000000000000000000000000000000000000"
    assert rows["m=1"]["evaluated_off_snap"] is True
    assert rows["m=1"]["rests_on_assumption"] is False
    assert rows["m=1"]["cause"] is None and rows["m=1"]["fix"] is None
    # The receiver's fix where it gives one, else the foundations one.
    assert rows["m=2"]["handed_kind"] is None
    assert rows["m=2"]["cause"] == "no_reference"
    assert rows["m=2"]["group"] == "last_resort"
    assert rows["m=2"]["group_fix"] == LAST_RESORT_FIX
    assert rows["m=2"]["fix"] == "declare the loss and dark counts each port has"
    assert rows["m=0"]["pointer"] == (
        "/payload/snaps/instance/measurement_snaps/0/blocks/0"
    )
    assert section["settings"] == {
        "reference_enclosure": True,
        "strict_snaps": False,
    }
    assert section["rests_on_a_snap"] is True
    assert section["evaluated_off_snap"] == 1


def test_a_run_that_evaluates_every_moved_block_off_rests_on_nothing() -> None:
    """A kept block is named as kept, and is not counted as evaluated off."""
    section = _section(_evaluated_off_report())
    assert section["rests_on_a_snap"] is False
    assert section["evaluated_off_snap"] == 1
    assert section["warnings"] == []
    assert "The rounding adds no premise" in " ".join(section["plain"])
    assert "rest on A-SNAP in the group" not in " ".join(section["sentences"])


def test_support_not_preserved_and_a_snap_are_visible_warnings() -> None:
    report = _report()
    section = _section(report)
    assert any("support_not_preserved" in item for item in section["warnings"])
    assert any("A-SNAP" in item for item in section["warnings"])
    assert section["assumption"] == "A-SNAP"
    markdown = render_markdown(report, contract_link=default_contract_link(""))
    # The warning is shown in the summary's "Not counted", before the detail.
    summary = markdown[markdown.index('id="not-counted"'):markdown.index('id="levers"')]
    assert "support_not_preserved" in summary
    assert "Measurement snaps" in markdown
    html = render_html(report, contract_link=default_contract_link(""))
    assert "support_not_preserved" in html


def test_a_snap_is_listed_among_the_user_s_premises_as_a_receiver_premise() -> None:
    """A-SNAP is a premise about the user's device (category ``receiver``).

    The report lists it in the premises the user vouches for, under its
    category, and not among the trusted engine numerics.
    """
    sections = _report()["sections"]
    groups = {
        group["category"]: [
            entry["short_id"]
            for family in group["families"]
            for entry in (family["head"], *family["members"])
        ]
        for group in sections["assumptions"]["groups"]
    }
    assert "A-SNAP" in groups.get("receiver", [])
    assert "A-SNAP" not in [
        entry["short_id"] for entry in sections["numerics"]["entries"]
    ]


def test_the_section_validates_against_the_report_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (Path(report_package.__file__).resolve().parent / "report.schema.json")
        .read_text(encoding="utf-8")
    )
    jsonschema.validate(json.loads(json.dumps(_report())), schema)
    jsonschema.validate(json.loads(json.dumps(_evaluated_off_report())), schema)


def test_a_resting_block_the_manifest_does_not_list_is_a_visible_discrepancy() -> None:
    """A discrepancy between blocks and manifest is a visible warning.

    A record whose blocks rest on A-SNAP while the manifest does not list it
    has ``assumption`` ``None``, and the report names the disagreement as a
    warning.
    """
    section = _section(_report(manifest_lists_a_snap=False))
    assert section["assumption"] is None
    assert section["rests_on_a_snap"] is True
    assert any(
        warning.startswith("Discrepancy") and "does not list A-SNAP" in warning
        for warning in section["warnings"]
    )
    listed = _section(_report())
    assert not any(warning.startswith("Discrepancy") for warning in listed["warnings"])


def test_the_summary_reads_the_run_s_answer() -> None:
    """The facade's report summary says what the report says."""
    from runs.facade.core import report_summary

    snaps = report_summary(_report())["measurement_snaps"]
    assert snaps["rests_on_a_snap"] is True
    assert [row["block"] for row in snaps["resting_blocks"]] == ["m=2"]
    assert snaps["resting_blocks"][0]["group"] == "last_resort"
    off = report_summary(_evaluated_off_report())["measurement_snaps"]
    assert off["rests_on_a_snap"] is False and off["resting_blocks"] == []


def test_the_strict_and_enclosure_settings_are_read_from_the_record() -> None:
    def edit(record: dict[str, Any]) -> None:
        with_snaps(record, [snap_block("m=0")], enclosure=False, strict=True)

    report = build_report(completed_record(edit=edit), table=synthetic_table())
    section = _section(report)
    text = " ".join(section["sentences"])
    assert section["settings"] == {
        "reference_enclosure": False,
        "strict_snaps": True,
    }
    assert "enclosed references are not used" in text
    assert "only those your model gives exactly" in text
    assert "the strict option is on" in text


def test_a_record_of_certified_procedure_snaps_has_no_section() -> None:
    """Record 0.27.0's snaps were made by the certified procedure."""

    def edit(record: dict[str, Any]) -> None:
        with_snaps(record, [dict(block) for block in SNAP_BLOCKS])

    record = completed_record(edit=edit)
    record["schema_version"] = "0.27.0"
    report = build_report(record, table=synthetic_table())
    assert report["sections"]["protocol"]["measurement_snaps"] is None


def test_a_record_without_a_measurement_snap_has_no_section() -> None:
    report = build_report(completed_record(), table=synthetic_table())
    assert report["sections"]["protocol"]["measurement_snaps"] is None
