"""Tests for harness/check_history.py.

Each category has lines it must find and look-alikes it must leave alone
(a citation id with a year, a version, a graph's predecessor, a JSON-Schema
draft, a decorator). The claim notes get their own category; the allow-list
allows, defers (`pending`), and fails on an entry that covers nothing; and the
shipped tree passes `--check`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_tool() -> ModuleType:
    """Return ``harness/check_history.py``, loaded by path.

    ``tests/harness/`` is itself a package named ``harness``, so under pytest's
    prepend import mode ``from harness import check_history`` resolves to the
    test package (see test_relabel.py). The tool imports nothing of the
    harness, so it loads alone under a private name.
    """
    name = "_harness_check_history"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, REPO_ROOT / "harness" / "check_history.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


tool = _load_tool()

#: Synthetic people for the attribution rule: the real list is the maintainers'
#: `harness/history_people.txt`, which a published tree does not carry.
NAMES = ("Zelda", "Quentin")


#: Tests that read the real tree, so they keep the real list.
REAL_PEOPLE = {"test_the_shipped_tree_passes_the_history_check"}


@pytest.fixture(autouse=True)
def _synthetic_people(request: pytest.FixtureRequest,
                      monkeypatch: pytest.MonkeyPatch) -> None:
    if request.node.name in REAL_PEOPLE:
        return
    patterns = dict(tool.PATTERNS)
    patterns["attribution"] = (r"\b(?:" + "|".join(NAMES) + r")\b",
                                *tool.PATTERNS["attribution"][len(tool.PEOPLE) > 0:])
    monkeypatch.setattr(tool, "PATTERNS", patterns)
    monkeypatch.setattr(tool, "_COMPILED", {
        k: tool.re.compile("|".join(f"(?:{alt})" for alt in v))
        for k, v in patterns.items()})
    needles = dict(tool._NEEDLES)
    needles["attribution"] = (*(n.lower() for n in NAMES),
                              *tool._NEEDLES["attribution"][len(tool.PEOPLE):])
    monkeypatch.setattr(tool, "_NEEDLES", needles)


def test_people_file_reader(tmp_path: Path) -> None:
    path = tmp_path / "people.txt"
    path.write_text("# a comment\nZelda\n\nQuentin  # with a note\n", encoding="utf-8")
    assert tool.load_people(path) == ("Zelda", "Quentin")
    assert tool.load_people(tmp_path / "absent.txt") == ()

POSITIVES = [
    ("attribution", "# kept on purpose (Zelda, the sitting)"),
    ("attribution", "Quentin's review asked for this."),
    ("attribution", 'notes: "ACCEPTED 2026, at the sitting"'),
    ("attribution", "# the answer was 'Keep it (Recommended)'"),
    ("dates", "# since 2026-09-26 a declared box gets a row"),
    ("dates", "What moved in (2026-10)"),
    ("dates", "decided on Oct 7, 2026 at the sitting"),
    ("dates", "decided on 7 October 2026"),
    ("dates", "as of 2026 the driver is single"),
    ("predecessor", "It is the successor of the QKD-MEAT engine."),
    ("predecessor", "from qkd_meat.reductions import x"),
    ("predecessor", "The predecessor kept one file per module."),
    ("predecessor", "migrated here at the move"),
    ("predecessor", "the Slice 2 report says so"),
    ("predecessor", "frozen under ROADMAP.md step 2"),
    ("pointers", "see reports/2026-10-06-protocol-document/design.md"),
    ("pointers", "(state/open-items/quality-x.yaml)"),
    ("pointers", "regenerates `state/DASHBOARD.md`"),
    ("pointers", "a note in context/ is evidence"),
    ("pointers", "moved to old/reports/x.md"),
    ("identity", "write to someone@example.com"),
    ("identity", r"C:\Users\someone\Desktop\repo"),
    ("identity", "/home/someone/repo"),
    ("identity", "the copy in Dropbox"),
]

NEGATIVES = [
    "the human operator decides",              # spec/style.md's role word
    r"\cite{arqand2025meat}, Thm. 3",          # a year inside a citation id
    "record schema 0.39.0, format 2",          # versions
    '"$schema": "https://json-schema.org/draft/2020-12/schema"',
    "build/2026-10-07-x/run.json is a path",     # the date is a path component
    "each point is seeded by its predecessor",  # a chain's predecessor
    "predecessors[head].discard(name)",
    "src/certiqs_key/runs/report/build.py",    # report/, not reports/
    "the quantum state/effect pair",
    "@pytest.mark.parametrize('x', [1])",
    "a Bretagnolle-Huber-Carol ball",
    "the value 2026.5 and 20261013",
]


@pytest.mark.parametrize(("category", "line"), POSITIVES)
def test_each_category_finds_its_lines(category: str, line: str) -> None:
    found = tool.scan_text("src/x.py", f"x = 1\n{line}\n")
    assert [(f.category, f.line) for f in found] == [(category, 2)], found


@pytest.mark.parametrize(("category", "line"), POSITIVES)
def test_every_positive_passes_its_prefilter(category: str, line: str) -> None:
    """The substring prefilter is for speed only; it may never hide a match."""
    lowered = line.lower()
    assert any(needle in lowered for needle in tool._NEEDLES[category])


@pytest.mark.parametrize("line", NEGATIVES)
def test_look_alikes_are_not_findings(line: str) -> None:
    assert tool.scan_text("src/x.py", line + "\n") == []


def test_one_line_may_hit_several_categories_once_each() -> None:
    line = "# (Zelda, 2026-09-16; reports/x.md, reports/y.md)"
    found = tool.scan_text("src/x.py", line)
    assert [f.category for f in found] == ["attribution", "dates", "pointers"]


def test_line_numbers_follow_crlf_and_lf_alike() -> None:
    text = "a\r\nb\r\n# Zelda said\r\nc\n# reports/x\n"
    found = tool.scan_text("src/x.py", text)
    assert [(f.line, f.category) for f in found] == [
        (3, "attribution"), (5, "pointers")]
    assert found[0].text == "# Zelda said"


CLAIM = """\
% ---
% id: core-a/thm:x
% title: "A result of 2026-10-10"
% notes: >-
%   A caveat. ACCEPTED 2026-10-10 by Zelda
%   (reports/reviews/core-a/round1.md).
% lean:
% ---

Body text naming reports/x.md.
"""


def test_claim_notes_are_their_own_category_with_the_pattern_kept() -> None:
    found = tool.scan_text("spec/modules/core-a/claims/thm-x.tex", CLAIM)
    by_line = [(f.line, f.category, f.kind) for f in found]
    assert by_line == [
        (3, "dates", "dates"),                       # the title is not notes
        (5, "claim-notes", "attribution"),
        (5, "claim-notes", "dates"),
        (6, "claim-notes", "pointers"),              # a continuation line
        (10, "pointers", "pointers"),                # the body is not notes
    ]


def test_a_submodule_claim_is_a_claim_file() -> None:
    rel = "spec/modules/receiver/detector-imperfections/claims/rem-x.tex"
    assert {f.category for f in tool.scan_text(rel, CLAIM)} >= {"claim-notes"}


def test_notes_outside_a_claim_file_are_ordinary_lines() -> None:
    found = tool.scan_text("spec/notation.md", CLAIM)
    assert "claim-notes" not in {f.category for f in found}


@pytest.mark.parametrize("rel", [
    "reports/2026-10-10-x/README.md",
    "state/open-items/x.yaml",
    "context/notes.md",
    "refs/index.json",
    "old/reports/x.md",
    "HUMAN_SCRATCHPAD.md",
    "spec/modules/meat-core/contract.tex",
    "spec/modules/meat-core/digest.tex",
    "spec/modules/meat-core/graphs/README.md",
    "spec/overview/chain.tex",
    "spec/module-graph.dot",
    "runs/report_examples/bb84/report.html",
    "src/certiqs_key/domain/claim_closure.json",
    "CITATION.cff",
    "spec/modules/meat-core/contract.pdf",
    "tests/data/b6-last-python-run/x.json.gz",
    "harness/check_history.py",
    "harness/history_allow.yaml",
])
def test_out_of_scope_paths(rel: str) -> None:
    assert not tool.in_scope(rel)


@pytest.mark.parametrize("rel", [
    "README.md", "AGENTS.md", ".gitignore", "pyproject.toml",
    "spec/overview/intro.tex", "spec/modules/meat-core/claims/thm-x.tex",
    "spec/modules/meat-core/design.md", "src/certiqs_key/runs/report/build.py",
    "tests/unit/test_x.py", "instances/bb84/README.md", "runs/x/README.md",
    ".claude/agents/drafter.md", "harness/export_citation.cff",
])
def test_in_scope_paths(rel: str) -> None:
    assert tool.in_scope(rel)


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def _tree(tmp_path: Path, allow: str | None = None) -> Path:
    _write(tmp_path, "src/a.py", "# Zelda chose this\nx = 1\n")
    _write(tmp_path, "docs/b.md", "See reports/x.md.\nDecided-by: Zelda\n")
    _write(tmp_path, "reports/r.md", "Zelda, 2026-10-10, reports/x.md\n")
    _write(tmp_path, "HUMAN_SCRATCHPAD.md", "Zelda 2026-10-10\n")
    if allow is not None:
        _write(tmp_path, tool.ALLOW_FILE, allow)
    return tmp_path


def test_the_tree_walk_skips_what_does_not_ship(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    found, scanned = tool.scan(root)
    assert scanned == 2
    assert sorted({f.path for f in found}) == ["docs/b.md", "src/a.py"]


def test_check_fails_without_an_allow_list_and_listing_does_not(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    root = _tree(tmp_path)
    assert tool.main(["--repo", str(root)]) == 0
    assert "src/a.py:1: [attribution] 'Zelda'" in capsys.readouterr().out
    assert tool.main(["--repo", str(root), "--check"]) == 1


ALLOW = """\
allow:
  - path: docs/b.md
    category: attribution
    match: 'Decided-by: Zelda'
    reason: the trailer convention
pending:
  - path: [src/a.py]
    category: attribution
    reason: an attribution to clean
  - path: docs/*.md
    category: pointers
    reason: a pointer to clean
"""


def test_allow_and_pending_keep_check_green_and_strict_fails_on_pending(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    root = _tree(tmp_path, ALLOW)
    assert tool.main(["--repo", str(root), "--check"]) == 0
    out = capsys.readouterr().out
    assert "failing: 0 (none); pending: 2" in out
    assert "allowed: 1" in out
    assert "(pending)" not in out                    # --check prints what fails
    assert tool.main(["--repo", str(root)]) == 0
    assert "(pending) src/a.py:1: [attribution]" in capsys.readouterr().out
    assert tool.main(["--repo", str(root), "--check", "--strict"]) == 1
    assert "src/a.py:1: [attribution]" in capsys.readouterr().out


def test_match_limits_an_allow_entry_to_one_form(tmp_path: Path) -> None:
    root = _tree(tmp_path, ALLOW)
    _write(root, "docs/b.md", "See reports/x.md.\nDecided-by: Zelda\nZelda said so\n")
    result = tool.run(root)
    assert [(f.path, f.line) for f in result.failing] == [("docs/b.md", 3)]


def test_a_path_that_covers_nothing_fails_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    stale = ALLOW + ("  - path: [src/a.py, src/clean.py]\n"
                     "    category: dates\n"
                     "    reason: cleaned since\n")
    root = _tree(tmp_path, stale)
    assert tool.main(["--repo", str(root), "--check"]) == 1
    out = capsys.readouterr().out
    assert "pending path src/a.py (dates) matches nothing" in out
    assert "pending path src/clean.py (dates) matches nothing" in out


def test_the_claim_notes_entry_defers_only_the_notes(tmp_path: Path) -> None:
    allow = ("pending:\n"
             "  - path: spec/modules/*/claims/*.tex\n"
             "    category: claim-notes\n"
             "    reason: the claim-notes pass\n")
    root = tmp_path
    _write(root, tool.ALLOW_FILE, allow)
    _write(root, "spec/modules/core-a/claims/thm-x.tex", CLAIM)
    result = tool.run(root)
    assert {f.category for f in result.pending} == {"claim-notes"}
    assert sorted(f.line for f in result.failing) == [3, 10]


@pytest.mark.parametrize(("text", "message"), [
    ("allow:\n  - path: a\n    category: dates\n", "'reason' is required"),
    ("allow:\n  - path: a\n    category: process\n    reason: r\n",
     "unknown category"),
    ("allow:\n  - category: dates\n    reason: r\n", "'path' must be"),
    ("allow:\n  - path: a\n    category: dates\n    reason: r\n    max: 3\n",
     "unknown field"),
    ("baseline: []\n", "expected a mapping with the lists"),
])
def test_a_malformed_allow_list_is_an_error(
    tmp_path: Path, text: str, message: str,
) -> None:
    path = tmp_path / "allow.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        tool.load_allow_list(path)


def test_the_shipped_tree_passes_the_history_check(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """New history in a shipped file, or an allow-list path that covers nothing.

    A red here names the file and line. Either state the line as a present
    fact, or, for a justified exception, add an `allow` entry with its reason
    to harness/history_allow.yaml; when a cleaning pass empties a `pending`
    path, drop the path.
    """
    code = tool.main(["--repo", str(REPO_ROOT), "--check"])
    assert code == 0, capsys.readouterr().out
