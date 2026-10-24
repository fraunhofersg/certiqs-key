"""Keep the reading layer present, plain and distinct from the mathematics.

Motivation: optional schema fields must not let newly maintained claims silently
lose their explanations. Coverage follows the current tree, without frozen
counts; rendering tests prevent prose from becoming TeX/Markdown instructions
or disappearing from one of the generated reading views. No test judges meaning.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
GOOD = Path(__file__).parent / "fixtures/good"


def run_tool(tool: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Exercise the public CLI without shadowing it with tests/harness."""
    return subprocess.run([sys.executable, "-m", "harness." + tool, *args],
                          cwd=ROOT, capture_output=True, text=True, check=False)


def assemble(root: Path, *args: str) -> int:
    result = run_tool("assemble_contract", "core-a", "--repo", str(root),
                      "--no-pdf", *args)
    if result.returncode:
        assert "stale:" in result.stderr, result.stdout + result.stderr
    return result.returncode


@pytest.fixture
def summary_repo(tmp_path: Path) -> Path:
    """Use the passing fixture; a test that needs absent metadata drops it."""
    shutil.copytree(GOOD, tmp_path, dirs_exist_ok=True)
    return tmp_path


def drop_claim_metadata(root: Path) -> None:
    """Remove every claim's summary and prominence, as a legacy claim lacks them."""
    for path in (root / "spec").rglob("*.tex"):
        text = path.read_text("utf-8")
        kept = [line for line in text.split("\n")
                if not line.startswith(("% summary:", "% prominence:"))]
        path.write_text("\n".join(kept), encoding="utf-8", newline="\n")


def set_metadata(root: Path, level: str, value: Any) -> None:
    """Set a single summary field without changing its mathematical source."""
    if level == "claim":
        path = root / "spec/modules/core-a/claims/def-base.tex"
        text = path.read_text("utf-8")
        # This fixture uses scalar single-line summaries; replace an earlier
        # value when exercising freshness rather than creating duplicate keys.
        text = "\n".join(line for line in text.split("\n")
                         if not line.startswith("% summary:"))
        field = yaml.safe_dump({"summary": value}, allow_unicode=True)
        commented = "".join("% " + line + "\n" for line in field.splitlines())
        path.write_text(text.replace("% status:", commented + "% status:", 1),
                        encoding="utf-8", newline="\n")
    else:
        mid = "core-a/sub-x" if level == "submodule" else "core-a"
        path = root / "spec/modules" / mid / "module.yaml"
        meta = yaml.safe_load(path.read_text("utf-8"))
        if level == "group":
            # The first assumption starts a group of its own (the order rule).
            meta["reading_groups"] = [
                {"title": "Foundations", "start": "def:base", "abstract": value},
                {"title": "Assumptions", "start": "ass:leaf"}]
        else:
            meta["abstract"] = value
        path.write_text(yaml.safe_dump(meta, sort_keys=False),
                        encoding="utf-8", newline="\n")


@pytest.mark.parametrize("level", ["module", "submodule", "group", "claim"])
@pytest.mark.parametrize("value", [None, 42, [], "", "  ", r"Use \alpha", "$x$"])
def test_invalid_explanation_is_reported(
    summary_repo: Path, level: str, value: Any,
):
    set_metadata(summary_repo, level, value)
    result = run_tool("check_claims", "--repo", str(summary_repo))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "plain text" in result.stdout
    assert ("summary" if level == "claim" else "abstract") in result.stdout


def test_absent_fields_keep_legacy_group_and_claims(summary_repo: Path):
    # check_claims requires both fields of every claim; the assembler still
    # renders a claim without them.
    drop_claim_metadata(summary_repo)
    result = run_tool("check_claims", "--repo", str(summary_repo))
    assert result.returncode == 1
    rules = set(re.findall(r"presentation\[([a-z-]+)\]", result.stdout))
    assert rules == {"summary-missing", "prominence-missing"}, result.stdout
    assert assemble(summary_repo) == 0
    tex = (summary_repo / "spec/modules/core-a/contract.tex").read_text("utf-8")
    assert r"\section{Claims}" in tex
    assert r"\textbf{Non-normative summary}" not in tex
    assert r"\claimanchor{core-a/def:base}" in tex        # no summary, same anchor


def test_group_abstract_does_not_relax_other_group_keys(summary_repo: Path):
    set_metadata(summary_repo, "group", "Explains the foundation.")
    path = summary_repo / "spec/modules/core-a/module.yaml"
    meta = yaml.safe_load(path.read_text("utf-8"))
    meta["reading_groups"][0]["claims"] = ["def:base"]
    path.write_text(yaml.safe_dump(meta), encoding="utf-8", newline="\n")
    result = run_tool("check_claims", "--repo", str(summary_repo))
    assert result.returncode == 1
    assert "entries need title and start" in result.stdout


def test_both_views_render_all_levels_without_changing_graph(summary_repo: Path):
    # The groups exist before and after, so only the new prose differs.
    set_metadata(summary_repo, "group", "Explains the foundation.")
    assert assemble(summary_repo) == 0
    directory = summary_repo / "spec/modules/core-a/graphs"
    before = {p.name: p.read_text("utf-8") for p in directory.glob("*.dot")}
    set_metadata(summary_repo, "module", "Module purpose & scope: 50%.")
    set_metadata(summary_repo, "submodule", "Submodule purpose with {detail}.")
    set_metadata(summary_repo, "group", "Group purpose with a_b.")
    set_metadata(summary_repo, "claim", "Claim purpose with <tag> and [link](target).")
    assert run_tool("check_claims", "--repo", str(summary_repo)).returncode == 0
    assert assemble(summary_repo) == 0
    after = {p.name: p.read_text("utf-8") for p in directory.glob("*.dot")}
    assert after == before

    tex = (directory.parent / "contract.tex").read_text("utf-8")
    # One legend in the front matter labels them all; no box per paragraph.
    assert r"\textbf{Non-normative summary}" not in tex
    assert tex.count("is non-normative") == 1
    assert (tex.index(r"\begin{overview}")
            < tex.index(r"Module purpose \& scope: 50\%.")
            < tex.index(r"\end{overview}"))
    assert (tex.index(r"\part{Sub X}")
            < tex.index(r"\sectionintro{Submodule purpose with \{detail\}.}"))
    assert (tex.index(r"\section{Foundations}")
            < tex.index(r"\sectionintro{Group purpose with a\_b.}"))
    assert (tex.index(r"\claimsummary{core-a/def:base}{Claim purpose with")
            < tex.index(r"\begin{definition}"))
    index = (directory / "README.md").read_text("utf-8")
    # The module, the submodule, the group, and each of the six claims of
    # core-a and sub-x, every claim carrying a summary.
    assert index.count("**Non-normative summary.**") == 3 + 6
    assert "Module purpose & scope: 50%\\." in index
    assert r"Submodule purpose with \{detail\}\." in index
    assert r"Group purpose with a\_b\." in index
    assert r"Claim purpose with \<tag\> and \[link\]\(target\)\." in index
    assert "[PDF](../contract.pdf#nameddest=claim-core-a/def:base)" in index


def test_markdown_summary_remains_literal(summary_repo: Path):
    set_metadata(summary_repo, "claim", "*emphasis* `code` # title | ~word~")
    assert assemble(summary_repo) == 0
    index = (summary_repo / "spec/modules/core-a/graphs/README.md").read_text("utf-8")
    assert r"\*emphasis\* \`code\` \# title \| \~word\~" in index


@pytest.mark.parametrize("level", ["module", "submodule", "group", "claim"])
def test_summary_edit_stales_generated_views(summary_repo: Path, level: str):
    set_metadata(summary_repo, level, "Original explanation.")
    assert assemble(summary_repo) == 0
    assert assemble(summary_repo, "--check") == 0
    set_metadata(summary_repo, level, "Revised explanation.")
    assert assemble(summary_repo, "--check") == 1
    assert assemble(summary_repo) == 0
    assert assemble(summary_repo, "--check") == 0


def test_maintained_tree_has_explanations_at_every_required_level():
    """Catch missing coverage without freezing the number or identity of claims."""
    for path in (ROOT / "spec/modules").rglob("module.yaml"):
        meta = yaml.safe_load(path.read_text("utf-8"))
        assert meta.get("abstract"), path
        assert "one_line" not in meta, path
        assert meta.get("reading_groups"), path
        for group in meta["reading_groups"]:
            assert group.get("abstract"), (path, group["title"])
        for claim in (path.parent / "claims").glob("*.tex"):
            if not claim.name.startswith("rem-"):
                header = claim.read_text("utf-8").split("% ---")[1]
                meta = yaml.safe_load("\n".join(
                    line.removeprefix("% ") for line in header.splitlines()))
                assert meta.get("summary"), claim


def test_mapped_text_sets_angle_brackets_and_bar_as_text_symbols():
    """A summary's "<" printed as an inverted exclamation mark in OT1 text mode.

    Run in a subprocess from the repository root, as ``run_tool`` runs the
    CLIs: ``tests/harness`` is itself a package named ``harness``, and an
    in-process import resolved to it when this test ran alone (P7
    integration, H-4).
    """
    probe = (
        "import sys; from harness.contract_navigation import tex_mapped; "
        "sys.stdout.buffer.write("
        "tex_mapped(chr(0x3b5) + ' < 1 | x > 0').encode('utf-8'))"
    )
    result = subprocess.run([sys.executable, "-c", probe], cwd=ROOT,
                            capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert result.stdout.decode("utf-8") == (
        r"\ensuremath{\varepsilon} \textless{} 1 \textbar{} x \textgreater{} 0")
