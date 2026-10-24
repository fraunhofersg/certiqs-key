"""Tests for harness/build_pages_site.py.

The site must hold the contracts and digests of every core module and nothing
outside the allow-list: the denied areas (third-party papers, internal notes,
open items, reports) are refused even where a pattern would match them, and a
site built from HEAD contains only allowed files and indexes whose links
resolve inside it.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from urllib.parse import unquote

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_tool() -> ModuleType:
    """Return ``harness/build_pages_site.py``, loaded by path.

    ``tests/harness/`` is itself a package named ``harness`` (see
    test_check_history.py); the tool imports nothing of the harness.
    """
    name = "_harness_build_pages_site"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, REPO_ROOT / "harness" / "build_pages_site.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


tool = _load_tool()


@pytest.mark.parametrize("path", [
    "spec/modules/meat-core/contract.pdf",
    "spec/modules/statistics/digest.pdf",
    "spec/modules/receiver/graphs/overview.svg",
    "spec/modules/receiver/graphs/overview.pdf",
    "spec/module-graph.svg",
    "spec/overview/overview.pdf",
    "runs/report_examples/bb84/report.html",
    "runs/report_examples/bb84/record.html",
    "runs/report_examples/sweep-bb84/sweep.html",
    "runs/report_examples/sweep-bb84/points/0000.record.html",
    "runs/bbm92_study/data/headline-report/report.html",
    "whitepaper/certiqs-key-whitepaper.pdf",
])
def test_allowed(path: str) -> None:
    assert tool.allowed(path)


@pytest.mark.parametrize("path", [
    "refs/papers/tupkary2026decoy.pdf",
    "context/notes/contract.pdf",
    "state/DASHBOARD.md",
    "reports/2026-10-13-x/contract.pdf",
    "HUMAN_SCRATCHPAD.md",
    "spec/modules/meat-core/design.md",
    "spec/modules/meat-core/graphs/README.md",
    "spec/modules/meat-core/graphs/claims.dot",
    "spec/modules/meat-core/contract.tex",
    "spec/modules/reductions/wpfss/contract.pdf",
    "runs/report_examples/bb84/record.json",
    "runs/report_examples/bb84/report.md",
    "src/certiqs_key/domain/claim_closure.json",
])
def test_refused(path: str) -> None:
    assert not tool.allowed(path)


def test_deny_wins_over_allow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tool, "_ALLOW_RE", [re.compile(r".*\Z")])
    assert tool.allowed("spec/macros.tex")
    for path in ("refs/papers/a.pdf", "context/a.pdf", "state/a.yaml",
                 "reports/a.pdf", "HUMAN_SCRATCHPAD.md", ".claude/a.md"):
        assert not tool.allowed(path)


def _cores() -> set[str]:
    listing = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-tree", "--name-only", "HEAD:spec/modules/"],
        check=True, capture_output=True, text=True).stdout.split()
    return {c for c in listing
            if (REPO_ROOT / "spec" / "modules" / c / "module.yaml").is_file()}


def test_site_from_head(tmp_path: Path) -> None:
    out = tmp_path / "site"
    built = tool.build(REPO_ROOT, out, "HEAD", "no-such-tag-*")
    assert list(built) == [tool.LATEST]
    paths = built[tool.LATEST]
    for core in _cores():
        for name in ("contract.pdf", "digest.pdf"):
            assert f"spec/modules/{core}/{name}" in paths
    files = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
    assert files == ({"index.html", "latest/index.html"}
                     | {f"latest/{p}" for p in paths})
    for index in (out / "index.html", out / "latest" / "index.html"):
        for href in re.findall(r'href="([^"]+)"', index.read_text(encoding="utf-8")):
            target = (index.parent / unquote(href.split("#")[0])).resolve()
            assert target.is_file(), f"{index.name}: {href}"
