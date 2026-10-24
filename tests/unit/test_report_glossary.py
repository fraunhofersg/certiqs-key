"""The key-rate report's glossary (report 0.9.0).

WHY THESE TESTS EXIST. A term a reader cannot look up stops a reader. The
checks: every glossary text is plain and short,
every ``see`` resolves to a claim file or a heading of ``spec/notation.md``,
every anchor is distinct, the page prints only the terms it uses, the HTML
links the first label naming a term, and every label, table header and
result-row name the renderer emits for the committed examples is plain
English (:data:`PLAIN`) or names a glossary term.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import pytest
from runs.report_examples.generate import EXAMPLES, read_record, record_paths
from tests.support.report_records import assumption, completed_record, synthetic_table

from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_html,
    render_markdown,
)
from certiqs_key.runs.report._page import _plain, write_report
from certiqs_key.runs.report._render import Rich, Writer
from certiqs_key.runs.report.build import SUPPORTED_RECORD_SCHEMA_VERSION
from certiqs_key.runs.report.glossary import categories, term_anchor, terms

ROOT = Path(__file__).resolve().parents[2]

#: LABELS THAT ARE PLAIN ENGLISH, or record field names the appendix shows
#: verbatim beside their values (provenance, route, preparation): a reader
#: needs no definition of either.
PLAIN: frozenset[str] = frozenset({
    "Alpha search", "Assumption", "Attempt", "Block", "Bound after", "Category",
    "Cause", "Cause (detail)", "Check", "Claim", "Claims", "Click patterns",
    "Collects modes", "Declared", "Diagnostic", "Digest", "Discharged by",
    "Document", "Element", "Fact", "Field", "Fix (detail)", "Flags", "Group",
    "How it is computed", "How it stopped", "Input", "Instance", "Key length",
    "Kind", "Label", "Letter", "Link", "Meaning", "Method", "Module", "Outcome",
    "Parameter", "Party", "Phase", "Port", "Premises", "Preparation",
    "Provenance", "Reason", "Record", "Refines", "Result", "Score", "Seconds",
    "Signals", "Stage", "Statement", "Station", "Statistic", "Status", "Steps",
    "Steps (iterations)", "Summary", "Trusted", "Unit", "Value",
    "Value on this run", "Verification", "Versions", "What it bounds",
    "What it is", "What it means", "What to change", "Points", "Data sector",
    "Estimate", "Setting", "Operator", "Allowed frequency", "Allowed count",
    "Why it stopped", "Resumed", "Set aside", "refinement stopped",
    "authentication factor", "outcome", "rate per round", "reason", "reason text",
    "refused at stage", "rounds", "rule", "runs", "reads", "record", "settings",
    "detail", "summary", "title", "id", "readme", "tag", "note", "digest",
    "packaged", "format_version", "config", "config_digest", "contracts",
    "created_by", "engine", "final_iterate", "platform", "report_id",
    "record_schema_version", "report_schema_version", "reproduce", "pointers",
    "optimizer", "solver_options", "assumption_manifest",
    "input_preparation_pointer", "snaps_pointer", "snap_max_defect",
    "snap_max_displacement", "group_b_worst_pointer", "reference_enclosure",
    "strict_snaps", "Bound clamped at zero (first_order_clamped)",
    "Estimate's point checked (estimate_point_relaxed_member)",
    "Run setting", "chosen alpha", "Station 0", "Station 1", "Fix",
    "Rests on A-SNAP?", "Where", "About", "At stake", "If it fails", "Count",
    "Premises of this run", "Input route",
})

_NOTATION = ROOT / "spec" / "notation.md"


class _Labels(Writer):
    """Record every table header, and the names of pair and diagnostic rows."""

    def __init__(self) -> None:
        self.labels: set[str] = set()

    def heading(self, level: int, text: str, anchor: str | None = None) -> None:
        del level, text, anchor

    def paragraph(self, rich: Rich) -> None:
        del rich

    def bullets(self, items: Sequence[Rich]) -> None:
        del items

    def numbered(self, items: Sequence[Rich]) -> None:
        del items

    def table(
        self, header: Sequence[str | Rich], rows: Sequence[Sequence[Rich]]
    ) -> None:
        heads = [cell if isinstance(cell, str) else _plain(cell) for cell in header]
        self.labels.update(heads)
        if (len(heads) == 2 and heads[1] == "Value") or heads[0] == "Diagnostic":
            self.labels.update(_plain(row[0]) for row in rows)

    def matrix(
        self, caption: str, rows: Sequence[str], columns: Sequence[str],
        cells: Sequence[Sequence[str]],
    ) -> None:
        del caption, rows, columns, cells

    def notice(self, title: str, items: Sequence[Rich]) -> None:
        del title, items

    def details(self, summary: str, body: Callable[[], None], *, open_: bool) -> None:
        del summary, open_
        body()

    def text(self) -> str:
        return ""


def _slug(heading: str) -> str:
    text = heading.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s", "-", text)


def _claim_file(claim_id: str) -> Path:
    path, _, label = claim_id.rpartition("/")
    kind, _, name = label.partition(":")
    return ROOT / "spec" / "modules" / path / "claims" / f"{kind}-{name}.tex"


def test_every_text_is_short_and_every_term_has_aliases() -> None:
    assert terms()
    for term in terms():
        assert 0 < len(term.text) <= 400, term.term
        assert term.aliases, term.term
        assert "\n" not in term.text


def test_every_see_resolves() -> None:
    headings = {
        _slug(line.lstrip("#"))
        for line in _NOTATION.read_text(encoding="utf-8").splitlines()
        if line.startswith("#")
    }
    for term in terms():
        if term.see is None:
            continue
        if term.see_claim is not None:
            assert _claim_file(term.see_claim).is_file(), (term.term, term.see)
        else:
            path, _, anchor = term.see.partition("#")
            assert path == "spec/notation.md" and anchor in headings, term.see


def test_anchors_are_distinct_and_aliases_unambiguous() -> None:
    anchors = [term.anchor for term in terms()]
    assert len(set(anchors)) == len(anchors)
    assert term_anchor("ε* (completeness)") != term_anchor("completeness")
    aliases = [alias for term in terms() for alias in term.aliases]
    assert len(set(aliases)) == len(aliases)


def test_every_category_has_a_heading_and_an_evidence_intro() -> None:
    found = categories()
    assert set(found) >= {
        "source", "receiver", "channel-and-adversary", "protocol-structure",
        "local-randomness", "post-processing", "honest-model",
        "supplied-artefact", "numerical-trust",
    }
    for category in found.values():
        assert category.heading and "Evidence" in category.intro
        for _, intro in category.where_listed:
            assert "Evidence" in intro


#: The sentence a record whose premises list no A-EVE-DIM is told
#: (meat-core/cor:composed-security reaches an attacker of any memory through
#: lem:memory-lift and lem:honest-attacks).
UNLIMITED_MEMORY = "No premise limits the size of the attacker's memory"


def _attacker_intro(text: str) -> str:
    start = text.index('id="category-channel-and-adversary"')
    return text[start:].split("\n\n", 2)[1]


def _with_eve_dim(record: dict[str, Any]) -> None:
    record["schema_version"] = "0.40.0"
    record["payload"]["assumption_manifest"]["assumptions"].append(assumption(
        "A-EVE-DIM", "meat-core/ass:eve-dim", "adversary_registers_finite",
        category="channel-and-adversary",
        title="The adversary's registers are finite-dimensional",
        user_statement="The analysis makes no claim about an attacker whose "
                       "memory cannot be described by a finite-dimensional system.",
        affects=["secrecy"],
    ))


def test_an_older_record_listing_a_eve_dim_is_not_told_memory_is_unlimited() -> None:
    record = completed_record(edit=_with_eve_dim)
    assert any(entry["short_id"] == "A-EVE-DIM"
               for entry in record["payload"]["assumption_manifest"]["assumptions"])
    text = render_markdown(build_report(record, table=synthetic_table()),
                           contract_link=default_contract_link())
    assert "A-EVE-DIM" in text
    assert UNLIMITED_MEMORY not in text
    (older,) = [intro for short_id, intro in
                categories()["channel-and-adversary"].where_listed
                if short_id == "A-EVE-DIM"]
    assert _attacker_intro(text) == older


def test_a_current_record_says_memory_is_unlimited() -> None:
    record = completed_record()
    assert record["schema_version"] == SUPPORTED_RECORD_SCHEMA_VERSION
    assert all(entry["short_id"] != "A-EVE-DIM"
               for entry in record["payload"]["assumption_manifest"]["assumptions"])
    text = render_markdown(build_report(record, table=synthetic_table()),
                           contract_link=default_contract_link())
    assert UNLIMITED_MEMORY in _attacker_intro(text)
    assert "memory of any size" in text and "A-EVE-DIM" not in text


def _covered(label: str, aliases: Sequence[str]) -> bool:
    return any(
        re.search(r"(?<![\w])" + re.escape(alias) + r"(?![\w])", label)
        for alias in aliases
    )


@pytest.mark.parametrize(
    "example", [example for example in EXAMPLES if example.kind == "run"],
    ids=lambda example: example.name,
)
def test_every_label_is_plain_or_in_the_glossary(example: object) -> None:
    aliases = [alias for term in terms() for alias in term.aliases]
    for path in record_paths(example):  # type: ignore[arg-type]
        writer = _Labels()
        write_report(writer, build_report(read_record(path)), default_contract_link())
        missing = sorted(
            label for label in writer.labels
            if label not in PLAIN and not _covered(label, aliases)
        )
        assert missing == [], missing


def _bbm92() -> dict[str, object]:
    (example,) = [example for example in EXAMPLES if example.name == "bbm92"]
    (path,) = record_paths(example)
    return read_record(path)


def test_the_page_prints_only_the_terms_it_uses_alphabetically() -> None:
    report = build_report(_bbm92())  # type: ignore[arg-type]
    text = render_markdown(report, contract_link=default_contract_link())
    glossary = text[text.index('id="glossary"'):]
    printed = re.findall(r'<a id="(g-[a-z0-9-]+)"></a>([^:]+):', glossary)
    names = [name for _, name in printed]
    assert names == sorted(names, key=str.lower)
    by_anchor = {term.anchor: term for term in terms()}
    # The honest model's parameters the source table names are defined too,
    # from the instance's parameter table.
    assert {anchor for anchor, _ in printed
            if not anchor.startswith("g-param-")} <= set(by_anchor)
    params = dict(printed)
    assert params["g-param-model-visibility"] == "visibility"
    visibility = glossary[glossary.index('id="g-param-model-visibility"'):]
    assert visibility.split("\n", 1)[0].endswith(
        "Visibility v of the entangled pair: matched-basis bits disagree with "
        "probability (1 - v)/2. The instance's parameter `model.visibility` "
        "(Visibility); its value on this run is under "
        "[Your inputs](#input-model.visibility).")
    assert "g-h-lb" in dict(printed)
    # A term no label or sentence uses is left out.
    assert "g-choi" not in dict(printed) or "Choi" in text.replace(glossary, "")


def test_html_links_the_first_label_naming_a_term_and_the_anchor_exists() -> None:
    report = build_report(_bbm92())  # type: ignore[arg-type]
    page = render_html(report, contract_link=default_contract_link())
    links = re.findall(r'href="#(g-[a-z0-9-]+)"', page)
    assert links
    assert len(links) == len(set(links))
    for anchor in links:
        assert f'id="{anchor}"' in page
    markdown = render_markdown(report, contract_link=default_contract_link())
    # Markdown links no label to the glossary; only a parameter the source
    # table names by its key links its definition, in both formats.
    assert set(re.findall(r"\]\(#(g-[a-z0-9-]+)\)", markdown)) == {
        "g-param-model-alice-transmittance", "g-param-model-bob-transmittance",
        "g-param-model-mean-pairs", "g-param-model-visibility",
    }
