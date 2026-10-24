"""The key-rate report shows what a protocol document declared (report 0.3.0).

Every premise a document supplies itself -- an explicit constraint entry, an
attack-set licence, a feasibility witness, a declared receiver POVM, a retention
attestation -- is listed in the result section, in the assumption section
under the premise it stands under, and in the facade's ``report_summary``
among the assumptions to vouch for. The texts are the document layer's, carried
in the record; the report copies them.

Also: the protocol section names the document, a 0.20.0 record (no
``protocol_document``) still builds a report, and the sweep report lists the
items once with their points.
"""

from __future__ import annotations

from typing import Any

import pytest
from tests.support.declared_documents import coverage_surface
from tests.support.report_records import completed_record, synthetic_table

from certiqs_key.runs.record import preparation_record
from certiqs_key.runs.report import (
    build_report,
    build_sweep_report,
    default_contract_link,
    render_html,
    render_markdown,
    report_schema,
)

KINDS = {
    "retention_attestation",
    "receiver_povm",
    "constraint_entry",
    "attack_set_license",
    "feasibility_witness",
}


def _document_block() -> dict[str, Any]:
    surface = coverage_surface("explicit_entries_with_licence")
    record = preparation_record(surface.preparation(surface.default_config()))
    block: dict[str, Any] = record["protocol_document"]
    return block


def _record(**changes: Any) -> dict[str, Any]:
    block = _document_block()

    def edit(record: dict[str, Any]) -> None:
        record["payload"]["protocol_document"] = block

    return completed_record(edit=edit, **changes)


def test_every_kind_is_in_the_result_and_the_assumption_sections() -> None:
    report = build_report(_record(), table=synthetic_table())
    result = report["sections"]["result"]["user_declared"]
    assert {item["kind"] for item in result} == KINDS
    assert report["sections"]["assumptions"]["user_declared"] == result
    by_kind = {item["kind"]: item for item in result}
    assert by_kind["receiver_povm"]["assumptions"] == ["A-SPEC", "A-IDEAL"]
    assert by_kind["retention_attestation"]["assumptions"] == ["A-SRC"]
    assert by_kind["attack_set_license"]["assumptions"] == ["A-ATK"]
    assert by_kind["feasibility_witness"]["assumptions"] == []
    for index, item in enumerate(result):
        assert item["pointer"] == f"/payload/protocol_document/user_declared/{index}"
        assert "Declared in the run's protocol document" in item["text"]


def test_the_protocol_section_names_the_document() -> None:
    block = _document_block()
    report = build_report(_record(), table=synthetic_table())
    assert report["sections"]["protocol"]["document"] == {
        "id": "coverage_explicit_entries_with_licence",
        "format_version": "1",
        "packaged": False,
        "digest": block["digest"],
    }


def test_the_report_validates_and_both_renderers_show_the_items() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    report = build_report(_record(), table=synthetic_table())
    jsonschema.validate(report, report_schema())
    markdown = render_markdown(report, contract_link=default_contract_link())
    html = render_html(report, contract_link=default_contract_link())
    for text in (markdown, html):
        assert "Declared in the protocol document, not derived by the engine" in text
        assert "Declared in the protocol document, vouched for by you" in text
        assert "Protocol document" in text
        assert "unit_trace" in text


def test_the_premise_behind_each_item_is_linked() -> None:
    """A-SPEC is in the synthetic table: its owner is indexed for the link."""
    report = build_report(_record(), table=synthetic_table())
    assert report["index"]["assumptions"]["A-SPEC"] == "protocol-compiler/ass:spec"


def test_a_0_21_0_record_without_its_document_key_is_refused() -> None:
    """0.21.0 writes ``protocol_document`` on every record (null off the route)."""
    from certiqs_key.runs.report import ReportInputError

    record = completed_record()
    del record["payload"]["protocol_document"]
    with pytest.raises(ReportInputError) as refused:
        build_report(record, table=synthetic_table())
    assert refused.value.reason == "not_a_run_record"


def test_a_0_20_0_record_still_builds_a_report() -> None:
    """The frontend keeps the reports of the records it has."""
    jsonschema = pytest.importorskip("jsonschema")
    record = completed_record()
    record["schema_version"] = "0.20.0"
    record["payload"].pop("protocol_document", None)
    report = build_report(record, table=synthetic_table())
    jsonschema.validate(report, report_schema())
    assert report["record_schema_version"] == "0.20.0"
    assert report["sections"]["protocol"]["document"] is None
    assert report["sections"]["result"]["user_declared"] == []
    assert report["sections"]["assumptions"]["user_declared"] == []


def test_the_sweep_lists_each_item_once_with_its_points() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    records = [_record(), _record(qber="1/25")]
    sweep = build_sweep_report(records, table=synthetic_table())
    jsonschema.validate(sweep, report_schema())
    items = sweep["common"]["user_declared"]
    assert {item["kind"] for item in items} == KINDS
    assert all(item["points"] == "all" for item in items)
    assert sweep["common"]["assumptions"]["user_declared"] == items


def test_report_summary_puts_every_item_among_the_assumptions_to_vouch_for() -> None:
    from runs.facade.core import report_summary

    summary = report_summary(build_report(_record(), table=synthetic_table()))
    declared = [
        entry
        for entry in summary["assumptions_to_vouch_for"]
        if entry.get("user_declared")
    ]
    assert {entry["kind"] for entry in declared} == KINDS
    assert summary["result"]["user_declared"]
    assert summary["document"]["id"] == "coverage_explicit_entries_with_licence"


def _characterised_record() -> dict[str, Any]:
    """Return a completed record carrying a port-Gram document's block (m4 (b))."""
    from tests.support.declared_optical_documents import (
        coverage_surface as optical_coverage,
    )

    surface = optical_coverage("port_grams")
    block = preparation_record(surface.preparation(surface.default_config()))[
        "protocol_document"
    ]

    def edit(record: dict[str, Any]) -> None:
        record["payload"]["protocol_document"] = block

    return completed_record(edit=edit)


def test_a_declared_characterisation_is_reported_under_a_trust() -> None:
    """A declared characterisation is shown like a POVM."""
    jsonschema = pytest.importorskip("jsonschema")
    from runs.facade.core import report_summary

    report = build_report(_characterised_record(), table=synthetic_table())
    jsonschema.validate(report, report_schema())
    (item,) = report["sections"]["result"]["user_declared"]
    assert item["kind"] == "receiver_characterisation"
    assert item["assumptions"] == ["A-TRUST"]
    assert report["sections"]["assumptions"]["user_declared"] == [item]
    markdown = render_markdown(report, contract_link=default_contract_link())
    declared = markdown[markdown.index("vouched for by you") :]
    assert "A-TRUST" in declared and "port Grams" in declared
    summary = report_summary(report)
    vouched = [
        entry
        for entry in summary["assumptions_to_vouch_for"]
        if entry.get("user_declared")
    ]
    assert [entry["kind"] for entry in vouched] == ["receiver_characterisation"]
