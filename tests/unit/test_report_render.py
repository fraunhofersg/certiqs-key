"""The Markdown and HTML renderings of a key-rate report.

Escaping of ``<``, ``&``, ``|`` and
Unicode; every claim link ends ``#nameddest=claim-<id>``; the HTML has no
``<script>`` and no external ``src`` or ``href`` but the contract links; the
not-counted flags come first; the output is deterministic.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

import pytest
from tests.support.report_records import (
    completed_record,
    estimate_record,
    refused_record,
    synthetic_table,
)

from certiqs_key.runs.report import (
    build_report,
    build_sweep_report,
    default_contract_link,
    render_html,
    render_markdown,
    render_sweep_html,
    render_sweep_markdown,
)
from certiqs_key.runs.report._render import SECTION_TITLES
from certiqs_key.runs.report.model import KeyRateReport, SweepPoint

NASTY = "a <b> & c | d * e _ f [g] `h` ε_auth δ λ_EC ≥ 2"


def built(record: dict[str, Any] | None = None) -> KeyRateReport:
    return build_report(record or completed_record(), table=synthetic_table())


def nasty_record() -> dict[str, Any]:
    def edit(record: dict[str, Any]) -> None:
        for entry in record["payload"]["assumption_manifest"]["assumptions"]:
            if entry["short_id"] == "A-AUTH":
                entry["user_statement"] = NASTY

    return completed_record(edit=edit)


def md(report: KeyRateReport, base: str = "") -> str:
    return render_markdown(report, contract_link=default_contract_link(base))


def html(report: KeyRateReport, base: str = "") -> str:
    return render_html(report, contract_link=default_contract_link(base))


class Links(HTMLParser):
    """Collect every ``href`` and ``src`` and every tag of an HTML document."""

    def __init__(self) -> None:
        """Start with nothing collected."""
        super().__init__()
        self.hrefs: list[str] = []
        self.srcs: list[str] = []
        self.tags: list[str] = []
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        for name, value in attrs:
            if name == "href" and value is not None:
                self.hrefs.append(value)
            if name == "src" and value is not None:
                self.srcs.append(value)
            if name == "id" and value is not None:
                self.ids.append(value)


def parse(document: str) -> Links:
    links = Links()
    links.feed(document)
    return links


def test_markdown_escapes_markup_and_keeps_unicode() -> None:
    text = md(built(nasty_record()))
    assert NASTY not in text
    assert ("a &lt;b> &amp; c \\| d \\* e \\_ f \\[g\\] \\`h\\` ε_auth δ λ_EC ≥ 2"
            in text)


def test_html_escapes_markup_and_keeps_unicode() -> None:
    text = html(built(nasty_record()))
    # A symbol's subscript is set as one in HTML, so it is not taken for
    # LaTeX that did not render.
    assert ("a &lt;b&gt; &amp; c | d * e _ f [g] `h` ε<sub>auth</sub> δ "
            "λ<sub>EC</sub> ≥ 2") in text
    assert "<b>" not in text


def test_a_pipe_in_a_value_does_not_break_a_markdown_table() -> None:
    def edit(record: dict[str, Any]) -> None:
        record["payload"]["config"]["model"]["qber"] = "1|50"

    text = md(built(completed_record(edit=edit)))
    row = next(line for line in text.splitlines() if "`model.qber`" in line)
    assert "1\\|50" in row
    assert row.count(" | ") == 4  # five cells


@pytest.mark.parametrize("render", [md, html], ids=["markdown", "html"])
def test_every_claim_link_ends_with_the_claim_s_named_destination(render: Any) -> None:
    report = built()
    text = render(report)
    targets = (
        re.findall(r"\]\(([^)]*)\)", text) if render is md else parse(text).hrefs
    )
    external = [target for target in targets if not target.startswith("#")]
    assert external
    for target in external:
        found = re.fullmatch(r"spec/modules/[^/]+/contract\.pdf#nameddest=claim-(.+)",
                             target)
        assert found, target
        assert found.group(1) in report["index"]["claims"]


def test_the_contract_base_prefixes_every_contract_link() -> None:
    text = html(built(), base="https://engine.example/contracts/")
    external = [href for href in parse(text).hrefs if not href.startswith("#")]
    assert external
    assert all(href.startswith("https://engine.example/contracts/spec/modules/")
               for href in external)


def test_html_is_self_contained_and_inert() -> None:
    for report in (built(), built(refused_record()), built(estimate_record())):
        text = html(report)
        links = parse(text)
        assert "script" not in links.tags
        assert "<script" not in text.lower()
        assert links.srcs == []
        assert "link" not in links.tags and "img" not in links.tags
        assert "@import" not in text and "url(" not in text
        for href in links.hrefs:
            assert href.startswith("#") or "#nameddest=claim-" in href, href


def test_every_in_page_link_has_its_anchor() -> None:
    links = parse(html(built()))
    for href in links.hrefs:
        if href.startswith("#"):
            assert href[1:] in links.ids, href


def test_the_not_counted_flags_lead_the_summary_s_not_counted_list() -> None:
    text = md(built())
    start = text.index('id="not-counted"')
    end = text.index('id="levers"')
    assert text.index('id="summary"') < start < end < text.index('id="setup"')
    order = [text.index(words, start) for words in (
        "No error-correction leakage counted", "No authentication error counted",
        "No authentication key consumption counted",
    )]
    assert order == sorted(order)
    assert order[-1] < end
    # The engine rows of the result table sit in the appendix.
    assert text.index('id="appendix"') < text.index("| outcome |")


def test_sections_appear_in_order_with_fixed_headings() -> None:
    expected = [title for key, title in SECTION_TITLES.items() if key != "snaps"]
    found_md = re.findall(r"^## (?:<a id=\"[^\"]+\"></a>)?(.+)$", md(built()), re.M)
    assert found_md == ["Contents", *expected]
    found_html = re.findall(r"<h2[^>]*>([^<]+)</h2>", html(built()))
    assert found_html == ["Contents", *expected]


def test_a_lmo_is_shown_once_among_the_engine_s_premises() -> None:
    text = md(built())
    engine = text.index('id="premises-engine"')
    appendix = text.index('id="appendix"')
    found = [match.start() for match in re.finditer(r"A-LMO: ", text)]
    assert len(found) == 1
    assert engine < found[0] < appendix


def test_carried_links_are_resolved() -> None:
    text = md(built())
    # rem:repeated-executions' summary links cor:separate-executions and A-SEPARATE.
    assert ('[Corollary "Security parameters of separate executions add"]'
            "(spec/modules/meat-core/contract.pdf#nameddest="
            "claim-meat-core/cor:separate-executions)") in text
    assert ("[A-SEPARATE](spec/modules/meat-core/contract.pdf#nameddest="
            "claim-meat-core/ass:separate-executions)") in text
    # An assumption present in the report links to its entry.
    assert "[A-KEYREG](#A-KEYREG)" in text
    assert "[[" not in text


def test_rendering_is_deterministic() -> None:
    first, second = built(), built()
    assert md(first) == md(second)
    assert html(first) == html(second)


def test_the_sweep_renders_the_points_with_their_links() -> None:
    records = [completed_record(qber=q) for q in ("1/50", "1/25")] + [refused_record()]
    sweep = build_sweep_report(records, table=synthetic_table())

    def point_link(point: SweepPoint) -> str:
        return f"points/{point['index']:04d}.html"

    link = default_contract_link()
    text = render_sweep_markdown(sweep, contract_link=link, point_link=point_link)
    assert "| Point | Label | model.qber |" in text
    assert "](points/0002.html)" in text
    # Codes are shown as code.
    assert "security_statement_vacuous" not in text.replace(
        "`security_statement_vacuous`", "")
    assert "`security_statement_vacuous`" in text
    page = render_sweep_html(sweep, contract_link=link, point_link=point_link)
    hrefs = parse(page).hrefs
    assert "points/0001.html" in hrefs
    assert "<script" not in page.lower()
    for href in hrefs:
        assert (href.startswith(("#", "points/")) or "#nameddest=claim-" in href), href
    assert render_sweep_html(sweep, contract_link=link, point_link=point_link) == page


def test_a_snapshot_pdf_string_cannot_reach_an_href() -> None:
    def edit(record: dict[str, Any]) -> None:
        for entry in record["payload"]["assumption_manifest"]["assumptions"]:
            entry["contract"] = {"pdf": "javascript:alert(1)", "anchor": "x"}

    report = built(completed_record(edit=edit))
    page = html(report)
    assert "javascript:" not in page
    assert all(not href.lower().startswith("javascript")
               for href in parse(page).hrefs)
    assert "javascript:" not in md(report)


def test_markdown_neutralises_block_starts_and_empty_identifiers() -> None:
    def edit(record: dict[str, Any]) -> None:
        for entry in record["payload"]["assumption_manifest"]["assumptions"]:
            if entry["short_id"] == "A-AUTH":
                entry["user_statement"] = "# not a heading"
            if entry["short_id"] == "A-KEYREG":
                entry["user_statement"] = "1. not a list"
            if entry["short_id"] == "A-CONFORM":
                entry["user_statement"] = "> not a quote"
            if entry["short_id"] == "A-SEQ":
                entry["machine_key"] = ""

    text = md(built(completed_record(edit=edit)))
    lines = text.splitlines()
    assert r"\# not a heading" in lines
    assert r"1\. not a list" in lines
    assert r"\> not a quote" in lines
    assert "# not a heading" not in lines
    assert "``" not in text
    assert "| Machine key | — |" in text


def test_a_sweep_shows_where_each_row_holds_and_varying_checks() -> None:
    def without_eig(record: dict[str, Any]) -> None:
        manifest = record["payload"]["assumption_manifest"]
        manifest["assumptions"] = [
            entry for entry in manifest["assumptions"] if entry["short_id"] != "A-EIG"
        ]
        record["payload"]["stages"]["key_rate"]["security_gates"][
            "key_length_permitted"
        ] = False

    records = [completed_record(), completed_record(qber="1/25", edit=without_eig),
               completed_record(qber="3/50")]
    sweep = build_sweep_report(records, table=synthetic_table())
    text = render_sweep_markdown(
        sweep, contract_link=default_contract_link(),
        point_link=lambda point: f"points/{point['index']:04d}.md",
    )
    eig = text.index("A-EIG: ")
    assert "| Points | points 0, 2 |" in text[eig:]
    assert "| Points | all points |" in text
    assert "varies: 0: passed; 1: failed; 2: passed" in text
    assert "Discharged on the route" in text


# ===========================================================================
#  Empty sections, and what "all" means on a sweep
# ===========================================================================


def test_a_refused_record_says_why_r3_and_r4_are_empty() -> None:
    """One sentence under each heading, and no flag beside no length."""
    report = built(refused_record(eps_pa=0.5, eps_ev=0.5))
    assert report["sections"]["result"]["not_counted"] == []
    sentence = (
        "No assumption of the run is listed because the run was refused at "
        "stage solve (security_statement_vacuous) before any result named a "
        "claim."
    )
    text = md(report)
    assumptions = text.index('id="assumptions"')
    appendix = text.index('id="appendix"')
    assert text.count(sentence) == 1
    assert assumptions < text.index(sentence) < appendix
    assert "counted (" not in text
    assert "The run was refused at its solve stage" in text
    page = html(report)
    assert page.count("No assumption of the run is listed because the run was "
                      "refused") == 1
    # A completed record carries no such sentence.
    assert "No assumption of the run is listed" not in md(built())


def test_a_sweep_with_a_refused_point_says_all_completed_points() -> None:
    """``"all"`` is every COMPLETED point, and the sweep says so."""
    records = [completed_record(), refused_record(), completed_record(qber="1/25")]
    sweep = build_sweep_report(records, table=synthetic_table())
    text = render_sweep_markdown(
        sweep, contract_link=default_contract_link(),
        point_link=lambda point: f"points/{point['index']:04d}.md",
    )
    assert "all completed points" in text
    assert "Points: all points." not in text
    # The flags carry their points (Markdown escapes the brackets).
    assert re.search(r"\\?\[all completed points\\?\]", text)
    complete = build_sweep_report(records[::2], table=synthetic_table())
    other = render_sweep_markdown(
        complete, contract_link=default_contract_link(),
        point_link=lambda point: f"points/{point['index']:04d}.md",
    )
    assert "all completed points" not in other
    assert re.search(r"\\?\[all points\\?\]", other)


def test_a_sweep_none_of_whose_points_completed_says_so() -> None:
    sweep = build_sweep_report([refused_record(), refused_record(qber="1/25")],
                               table=synthetic_table())
    text = render_sweep_markdown(
        sweep, contract_link=default_contract_link(),
        point_link=lambda point: f"points/{point['index']:04d}.md",
    )
    assert text.count(
        "No assumption is listed because every point was refused before any "
        "result named a claim."
    ) == 1  # the engine numerics are in the assumptions
    assert "No point output a key, so no security guarantee applies." in text
    assert "No point completed, so no setup is shown." in text
