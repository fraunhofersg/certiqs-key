"""Links of the key-rate report: record excerpts, claim ids, repository paths, λ_EC.

Report 0.8.0 (report v2, design sections 7 and 9): every record pointer the
rendered report shows links to its excerpt, and every excerpt anchor exists;
a claim id in carried text links its contract where the report's index
resolves it, and stays plain otherwise; a repository path links through
``--repo-base`` and only then; a λ_EC estimate beside the record is shown
under the λ_EC input; Markdown writes numbers without backslashes.
"""

from __future__ import annotations

import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from tests.support.report_records import completed_record, synthetic_table

from certiqs_key.runs.report import (
    build_report,
    cited_repo_paths,
    default_contract_link,
    render_html,
    render_markdown,
)
from certiqs_key.runs.report.__main__ import lambda_ec_path, main
from certiqs_key.runs.report._render import excerpt_anchor
from certiqs_key.runs.report.build import resolve_claim_mention
from certiqs_key.runs.report.render_markdown import escape_markdown

ROOT = Path(__file__).resolve().parents[2]
BBM92 = ROOT / "runs" / "report_examples" / "bbm92" / "record.json.gz"
_LINK = re.compile(r"\[[^\]]*\]\(([^)]*)\)")


class _Html(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name == "href" and value is not None:
                self.hrefs.append(value)
            if name == "id" and value is not None:
                self.ids.add(value)


def parsed(text: str) -> _Html:
    parser = _Html()
    parser.feed(text)
    return parser


# --------------------------------------------------------------------------
# Record excerpts
# --------------------------------------------------------------------------


def test_excerpt_anchors_are_injective_and_safe() -> None:
    pointers = ["/payload/a_b", "/payload/a/b", "/payload/a.b", "/payload/a~1b",
                "/payload/a b", "/payload/gen:X|A"]
    anchors = [excerpt_anchor(pointer) for pointer in pointers]
    assert len(set(anchors)) == len(anchors)
    for anchor in anchors:
        assert re.fullmatch(r"p-[A-Za-z0-9_.~-]+", anchor), anchor


@pytest.mark.parametrize("form", ["md", "html"])
def test_every_pointer_of_the_bbm92_report_has_its_excerpt(
    tmp_path: Path, form: str
) -> None:
    out = tmp_path / f"report.{form}"
    assert main([str(BBM92), "--format", form, "--out", str(out)]) == 0
    report = out.read_text(encoding="utf-8")
    excerpts = (tmp_path / f"record.{form}").read_text(encoding="utf-8")
    if form == "html":
        targets = [href for href in parsed(report).hrefs
                   if href.startswith("record.html#")]
        anchors = parsed(excerpts).ids
    else:
        targets = [href for href in _LINK.findall(report)
                   if href.startswith("record.md#")]
        anchors = set(re.findall(r'<a id="([^"]+)"></a>', excerpts))
    assert targets
    missing = {target for target in targets if target.split("#", 1)[1] not in anchors}
    assert missing == set()
    if form == "md":
        # Every pointer the report shows is a link: none is left as text.
        assert "/payload" not in _LINK.sub("", report)
    # The excerpts link back to the report.
    assert f"report.{form}" in excerpts


def test_the_excerpts_can_be_turned_off_and_stdout_has_none(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "report.md"
    assert main([str(BBM92), "--out", str(out), "--no-excerpts"]) == 0
    assert not (tmp_path / "record.md").exists()
    assert "record.md#" not in out.read_text(encoding="utf-8")
    assert main([str(BBM92)]) == 0
    assert "record.md#" not in capsys.readouterr().out


def test_a_sweep_writes_excerpts_beside_each_point(tmp_path: Path) -> None:
    records = tmp_path / "records"
    records.mkdir()
    shutil.copy(BBM92, records / "run-0000.json.gz")
    shutil.copy(BBM92, records / "run-0001.json.gz")
    out = tmp_path / "out"
    assert main([str(records), "--format", "html", "--out", str(out)]) == 0
    for index in ("0000", "0001"):
        point = (out / "points" / f"{index}.html").read_text(encoding="utf-8")
        excerpts = (out / "points" / f"{index}.record.html").read_text(encoding="utf-8")
        targets = [href for href in parsed(point).hrefs
                   if href.startswith(f"{index}.record.html#")]
        assert targets
        ids = parsed(excerpts).ids
        assert all(target.split("#", 1)[1] in ids for target in targets)


# --------------------------------------------------------------------------
# Claim ids in carried text
# --------------------------------------------------------------------------


def test_a_claim_mention_resolves_full_relative_or_bare_when_unambiguous() -> None:
    ids = ["meat-core/ass:keyreg", "reductions/domination/req:domination-route",
           "statistics/req:matched-alphabet", "a/thm:x", "b/thm:x"]
    assert resolve_claim_mention("statistics/req:matched-alphabet", ids) == (
        "statistics/req:matched-alphabet")
    assert resolve_claim_mention("domination/req:domination-route", ids) == (
        "reductions/domination/req:domination-route")
    assert resolve_claim_mention("ass:keyreg", ids) == "meat-core/ass:keyreg"
    assert resolve_claim_mention("ass:keyreg.", ids) == "meat-core/ass:keyreg"
    assert resolve_claim_mention("ass:keyreg", ids, module="statistics") is None
    assert resolve_claim_mention("thm:x", ids) is None
    assert resolve_claim_mention("thm:x", ids, module="a") == "a/thm:x"
    assert resolve_claim_mention("meat-core/ass:nothing", ids) is None


def _meaning_record(meaning: str) -> dict[str, Any]:
    def edit(record: dict[str, Any]) -> None:
        record["payload"]["instance"]["parameters"][0]["meaning"] = meaning

    return completed_record(edit=edit)


def test_claim_ids_in_an_input_meaning_become_contract_links() -> None:
    meaning = (
        "Bound by meat-core/cor:keylength-bound, by frank-wolfe/thm:firstorder (ii) "
        "and rem:repeated-executions; not by meat-core/ass:nothing."
    )
    report = build_report(_meaning_record(meaning), table=synthetic_table())
    for claim in ("meat-core/cor:keylength-bound",
                  "meat-core/frank-wolfe/thm:firstorder",
                  "meat-core/rem:repeated-executions"):
        assert claim in report["index"]["claims"]
    text = render_markdown(report, contract_link=default_contract_link())
    row = next(line for line in text.splitlines() if "`model.qber`" in line)
    assert "#nameddest=claim-meat-core/cor:keylength-bound)" in row
    assert "#nameddest=claim-meat-core/frank-wolfe/thm:firstorder) (ii)" in row
    assert "#nameddest=claim-meat-core/rem:repeated-executions)" in row
    assert "not by meat-core/ass:nothing." in row


# --------------------------------------------------------------------------
# Repository paths
# --------------------------------------------------------------------------


def test_repository_paths_link_only_through_a_repo_base() -> None:
    report = build_report(
        _meaning_record("See spec/architecture.md 2.8."), table=synthetic_table()
    )
    link = default_contract_link("https://repo.example/blob/abc/")
    plain = render_markdown(report, contract_link=link)
    assert "](https://repo.example/blob/abc/instances/" not in plain
    base = "https://repo.example/blob/abc/"
    for render in (render_markdown, render_html):
        text = render(report, contract_link=link, repo_base=base)
        assert f"{base}instances/bb84/README.md" in text
        assert f"{base}spec/architecture.md" in text
        assert cited_repo_paths(text, base) == [
            "instances/bb84/README.md", "spec/architecture.md",
        ]


# --------------------------------------------------------------------------
# λ_EC origin
# --------------------------------------------------------------------------


ESTIMATE = {
    "conditional_entropy_bits_per_round": 0.25,
    "f_ec": 1.1,
    "f_ec_source": "kamin2025renyi, Sec. VII, Eq. (123)",
    "formula": "lambda_EC = ceil(f_EC * n * H(R | O_nonholder, K))",
    "key_holder": "A",
    "lambda_ec": 275,
    "p_pass": 0.5,
    "rounds": 1000,
}


def _write(path: Path, record: dict[str, Any]) -> Path:
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def test_the_lambda_ec_side_file_is_found_beside_the_record(tmp_path: Path) -> None:
    assert lambda_ec_path(tmp_path / "record.json.gz") == (
        tmp_path / "record.lambda-ec.json")
    assert lambda_ec_path(tmp_path / "run-0001.json") == (
        tmp_path / "run-0001.lambda-ec.json")


def test_lambda_ec_shows_how_it_was_chosen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from certiqs_key.runs.report import build as build_module

    monkeypatch.setattr(build_module, "closure_table", synthetic_table)
    record = _write(tmp_path / "record.json", completed_record(lambda_ec=275))
    out = tmp_path / "report.md"
    assert main([str(record), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "How λ_EC was chosen: declared by you" in text

    (tmp_path / "record.lambda-ec.json").write_text(json.dumps(ESTIMATE),
                                                    encoding="utf-8")
    assert main([str(record), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "estimated from the honest model ([how](#lambda-ec-origin))" in text
    assert '<a id="lambda-ec-origin"></a>How λ_EC was chosen' in text
    # f_EC links its glossary definition; its source links the registered paper.
    assert "| [f_EC](#g-f-ec), the error-correction inefficiency | 1.1 |" in text
    # The registered source links its paper (refs/index.json: arXiv 2504.12248v2).
    assert ("[kamin2025renyi](https://arxiv.org/abs/2504.12248v2), Sec. VII, "
            "Eq. (123)") in text
    assert "λ_EC differs" not in text

    other = dict(ESTIMATE, lambda_ec=999)
    (tmp_path / "record.lambda-ec.json").write_text(json.dumps(other),
                                                    encoding="utf-8")
    assert main([str(record), "--out", str(out)]) == 0
    assert "λ_EC differs" in out.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Markdown numbers
# --------------------------------------------------------------------------


def test_markdown_writes_numbers_without_backslashes() -> None:
    assert escape_markdown("0.057") == "0.057"
    assert escape_markdown("-0.2") == "-0.2"
    assert escape_markdown("1e-12") == "1e-12"
    assert escape_markdown("100,000,000") == "100,000,000"
    # What would open a block where it starts a line is still escaped ...
    assert escape_markdown("1. a list") == "1\\. a list"
    assert escape_markdown("- a list") == "\\- a list"
    assert escape_markdown("# a heading") == "\\# a heading"
    assert escape_markdown("---") == "\\---"
    # ... but never inside a table cell, which cannot open one.
    assert escape_markdown("1. a cell", line_start=False) == "1. a cell"


def test_a_table_cell_holds_a_plain_number() -> None:
    report = build_report(completed_record(), table=synthetic_table())
    text = render_markdown(report, contract_link=default_contract_link())
    row = next(line for line in text.splitlines()
               if line.startswith("| security parameter"))
    assert row.startswith("| security parameter | 1.862645149230957e-09 |")
    assert not re.search(r"\d\\\.\d|\\-\d", text)


def test_a_directory_s_lambda_ec_side_files_are_not_read_as_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from certiqs_key.runs.report import build as build_module

    monkeypatch.setattr(build_module, "closure_table", synthetic_table)
    records = tmp_path / "records"
    records.mkdir()
    _write(records / "run-0000.json", completed_record(lambda_ec=275))
    (records / "run-0000.lambda-ec.json").write_text(json.dumps(ESTIMATE),
                                                     encoding="utf-8")
    out = tmp_path / "out"
    assert main([str(records), "--out", str(out)]) == 0
    point = (out / "points" / "0000.md").read_text(encoding="utf-8")
    assert r"How λ_EC was chosen" in point
