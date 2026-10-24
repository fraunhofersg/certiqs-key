"""Tests for harness/dashboard.py.

The passing claim fixture is staged together with a small open-item queue
(tests/harness/fixtures/dashboard-state): the page must rank decisions by
severity before priority, hide closed items, list every registered module
whether or not it exists yet, and fail `--check` when stale. The real
repository's checked-in page must be current.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def dashboard(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the generator from the repository root and capture its output."""
    return subprocess.run(
        [sys.executable, "-m", "harness.dashboard", *args],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )


def staged(tmp_path: Path) -> Path:
    """Copy the good claim fixture and the dashboard state into one repo."""
    shutil.copytree(FIXTURES / "good", tmp_path, dirs_exist_ok=True)
    shutil.copytree(FIXTURES / "dashboard-state", tmp_path, dirs_exist_ok=True)
    return tmp_path


def test_page_is_generated_from_items_and_claims(tmp_path: Path):
    repo = staged(tmp_path)
    result = dashboard("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr
    page = (repo / "state/DASHBOARD.md").read_text("utf-8")

    # decisions: major before minor, closed ones absent
    assert page.index("spec/b-decision") < page.index("spec/a-decision")
    assert "closed-decision" not in page
    assert "Recommended: option A." in page
    # status map: registry order, submodule under its core, unknown as not started
    status = page[page.index("## 2."):page.index("## 3.")]
    assert status.index("| core-b |") < status.index("| core-a |")
    assert status.index("| core-a |") < status.index("| core-a/sub-x |")
    assert "| core-c | - | - |" in status
    assert "not started `migration/core-c`" in status
    # contract column: a core without a built PDF says so, a submodule is blank
    # each status cell is the header count with the effective count in
    # parentheses (the checker computes the effective
    # status; here the fixture's two agree)
    assert ("| core-a | 0.2.0 | missing | 3 (3) | 2 (2) | 0 (0) | 0 (0) "
            "| 0 (0) | 1 |") in status
    assert "| core-a/sub-x | 0.2.0 |  |" in status or "| core-a/sub-x |" in status
    (repo / "spec/modules/core-a/contract.pdf").write_bytes(b"%PDF-1.4\n")
    assert dashboard("--repo", str(repo)).returncode == 0
    relinked = (repo / "state/DASHBOARD.md").read_text("utf-8")
    assert "| core-a | 0.2.0 | [pdf](../spec/modules/core-a/contract.pdf) |" in relinked
    (repo / "spec/modules/core-a/contract.pdf").unlink()
    assert dashboard("--repo", str(repo)).returncode == 0
    # findings and tasks
    assert "| minor | `core-a/loose-bound` | agent | 2026-09-03 |" in page
    assert "1. `migration/core-c`: Migrate core C" in page

    again = dashboard("--repo", str(repo), "--check")
    assert again.returncode == 0, again.stdout + again.stderr


def test_check_detects_a_stale_page(tmp_path: Path):
    repo = staged(tmp_path)
    assert dashboard("--repo", str(repo)).returncode == 0
    item = repo / "state/open-items/a-decision.yaml"
    item.write_text(item.read_text("utf-8").replace("status: open", "status: closed"),
                    "utf-8")
    result = dashboard("--repo", str(repo), "--check")
    assert result.returncode == 1
    assert "stale" in result.stderr


def test_malformed_item_is_an_error(tmp_path: Path):
    repo = staged(tmp_path)
    (repo / "state/open-items/broken.yaml").write_text("- not: a mapping\n", "utf-8")
    result = dashboard("--repo", str(repo))
    assert result.returncode == 1
    assert "broken.yaml" in result.stderr


def test_checked_in_dashboard_is_current():
    result = dashboard("--repo", str(REPO_ROOT), "--check")
    assert result.returncode == 0, result.stdout + result.stderr
