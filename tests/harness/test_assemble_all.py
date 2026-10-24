"""The digest, the overview and ``assemble_contract --all``, on the `format` fixture.

Motivation: ``--all`` is what an author runs after every claim change
(AGENTS.md), so it must rebuild exactly what a change reaches and nothing
else: a rebuild of an untouched file rewrites a tracked output for no reason
(a Graphviz or TeX upgrade would then touch every render), and a missed one
leaves a stale page that looks current. The digest must keep the contract's
numbers, since a reader moves between the two by number. And two builds of the
same sources must give the same PDF bytes, or every run dirties the tree.
Each test reads one of these off a scratch copy of the fixture; the ones that
need latexmk or Graphviz skip without them.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FORMAT = Path(__file__).resolve().parent / "fixtures" / "format"
A = "spec/modules/core-a"
B = "spec/modules/core-b"
HAS_LATEXMK = shutil.which("latexmk") is not None
HAS_GRAPHVIZ = (shutil.which("dot") is not None
                or Path("C:/Program Files/Graphviz/bin/dot.exe").is_file())
NEEDS_BUILD = pytest.mark.skipif(not (HAS_LATEXMK and HAS_GRAPHVIZ),
                                 reason="needs latexmk/Graphviz")


def _load_digest() -> ModuleType:
    """Return ``harness/contract_digest.py`` of the real package, loaded by path.

    ``tests/harness/`` is itself a package named ``harness`` (see
    test_contract_layout.py, which loads its tools the same way).
    """
    if "_all_contract_digest" in sys.modules:
        return sys.modules["_all_contract_digest"]
    saved = {key: module for key, module in sys.modules.items()
             if key == "harness" or key.startswith("harness.")}
    try:
        for key in saved:
            sys.modules.pop(key, None)
        spec = importlib.util.spec_from_file_location(
            "harness", REPO_ROOT / "harness" / "__init__.py",
            submodule_search_locations=[str(REPO_ROOT / "harness")])
        assert spec is not None and spec.loader is not None
        package = importlib.util.module_from_spec(spec)
        sys.modules["harness"] = package
        spec.loader.exec_module(package)
        digest = importlib.import_module("harness.contract_digest")
    finally:
        stale = [k for k in sys.modules if k == "harness" or k.startswith("harness.")]
        for key in stale:
            sys.modules.pop(key, None)
        sys.modules.update(saved)
    sys.modules["_all_contract_digest"] = digest
    return digest


def copy(tmp_path: Path) -> Path:
    """Return a scratch copy of the `format` fixture."""
    target = tmp_path / "repo"
    shutil.copytree(FORMAT, target)
    return target


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the assembler on ``repo`` and capture its output."""
    return subprocess.run(
        [sys.executable, "-m", "harness.assemble_contract", *args, "--repo", str(repo)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def snapshot(repo: Path) -> dict[str, tuple[str, int]]:
    """Map every file of ``repo`` to its hash and modification time."""
    return {path.relative_to(repo).as_posix():
            (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
            for path in sorted(repo.rglob("*")) if path.is_file()}


def edit(repo: Path, relative: str, old: str, new: str) -> None:
    """Replace one exact fragment of a fixture file, which must be there."""
    path = repo / relative
    text = path.read_text("utf-8")
    assert old in text, (relative, old)
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# --- change detection (no TeX needed) --------------------------------------------


def test_all_writes_every_contract_digest_and_the_overview(tmp_path: Path):
    repo = copy(tmp_path)
    result = run(repo, "--all", "--no-pdf")
    assert result.returncode == 0, result.stdout + result.stderr
    for path in (f"{A}/contract.tex", f"{A}/digest.tex", f"{B}/contract.tex",
                 f"{B}/digest.tex", "spec/overview/overview.tex",
                 "spec/overview/chain.tex", "spec/module-graph.dot"):
        assert (repo / path).is_file(), path
    checked = run(repo, "--all", "--check", "--no-pdf")
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_a_second_run_touches_nothing(tmp_path: Path):
    repo = copy(tmp_path)
    assert run(repo, "--all", "--no-pdf").returncode == 0
    before = snapshot(repo)
    again = run(repo, "--all", "--no-pdf")
    assert again.returncode == 0, again.stdout + again.stderr
    assert "core-a: up to date" in again.stdout
    assert "core-b: up to date" in again.stdout
    assert "overview: up to date" in again.stdout
    assert snapshot(repo) == before


def test_a_change_rebuilds_what_it_reaches_and_nothing_else(tmp_path: Path):
    repo = copy(tmp_path)
    assert run(repo, "--all", "--no-pdf").returncode == 0
    before = snapshot(repo)
    edit(repo, f"{B}/claims/prop-cross.tex", "Immediate from", "It is immediate from")
    stale = run(repo, "--all", "--check", "--no-pdf")
    assert stale.returncode == 1
    assert f"{B}/contract.tex differs from its sources" in stale.stderr.replace(
        str(repo).replace("\\", "/") + "/", "")
    assert run(repo, "--all", "--no-pdf").returncode == 0
    after = snapshot(repo)
    changed = sorted(name for name in after if after[name] != before.get(name))
    # the proof is in the contract, not in the digest, the graphs or core-a
    assert changed == [f"{B}/claims/prop-cross.tex", f"{B}/contract.tex"]


def test_a_new_main_result_reaches_the_overview(tmp_path: Path):
    repo = copy(tmp_path)
    assert run(repo, "--all", "--no-pdf").returncode == 0
    chain = (repo / "spec/overview/chain.tex").read_text("utf-8")
    # dependency order: core-a before core-b, whatever the registry's order
    assert chain.index("{Core A}") < chain.index("{Core B}")
    assert (r"\hyperref{../modules/core-a/contract.pdf}{}{claim-core-a/thm:bound}"
            r"{Theorem~1.2 (Bound on the first coordinate)}") in chain
    assert "No claim of this contract is marked as a main result yet." in chain
    edit(repo, f"{B}/claims/prop-cross.tex", "% prominence: standard",
         "% prominence: main")
    assert run(repo, "--all", "--no-pdf").returncode == 0
    chain = (repo / "spec/overview/chain.tex").read_text("utf-8")
    assert r"{claim-core-b/prop:cross}{Proposition~1.1 (The consumer's cap)}" in chain
    # the summary's links point into the contracts
    assert (r"\hyperref{../modules/core-a/contract.pdf}{}{claim-core-a/thm:bound}"
            r"{Theorem~1.2}") in chain


def test_without_an_introduction_the_overview_is_skipped(tmp_path: Path):
    repo = copy(tmp_path)
    (repo / "spec/overview/intro.tex").unlink()
    result = run(repo, "--all", "--no-pdf")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "overview skipped" in result.stderr
    assert not (repo / "spec/overview/chain.tex").exists()


def test_one_module_or_all_but_not_both(tmp_path: Path):
    repo = copy(tmp_path)
    assert run(repo, "core-a", "--all", "--no-pdf").returncode == 2
    assert run(repo, "--no-pdf").returncode == 2


# --- the digest ---------------------------------------------------------------------


def test_the_digest_keeps_the_contracts_numbers(tmp_path: Path):
    repo = copy(tmp_path)
    assert run(repo, "core-a", "--no-pdf").returncode == 0
    digest = (repo / A / "digest.tex").read_text("utf-8")
    assert r"\usepackage{xr-hyper}" in digest
    assert r"\externaldocument[C-]{contract}" in digest
    for label, number in (("def:object", "1.1"), ("thm:bound", "1.2"),
                          ("ass:leaf", "2.1"), ("req:refuse", "3.1")):
        assert f"\\digestlabel{{{label}}}{{{number}}}" in digest, label
    assert (r"\renewcommand*{\RestatedName}{\hyperref{contract.pdf}{}"
            r"{claim-core-a/thm:bound}{Theorem~1.2}}") in digest
    assert r"\section*{3\quad Requirements}" in digest
    # left out: remarks, technical claims, proofs
    assert "rem:tight" not in digest and "lem:helper" not in digest
    assert r"\begin{proof}" not in digest
    # a display keeps the contract's number and gets a local label
    assert (r"\begin{equation*}\tag{\getrefnumber{C-eq:object}}"
            r"\digesteqlabel{eq:object}") in digest
    # the main result keeps its frame
    assert digest.index(r"\begin{mainclaim}") < digest.index(r"{Theorem~1.2}")


def test_a_reference_to_what_the_digest_leaves_out_opens_the_contract():
    digest = _load_digest()
    body = digest.digest_body(
        "By Remark~\\ref{rem:x}, Lemma~\\ref{lem:y} and \\eqref{eq:z}, "
        "\\begin{equation}\\label{eq:w} a = b \\end{equation}", {"lem:y", "eq:w"})
    assert r"Remark~\ref{C-rem:x}" in body
    assert r"Lemma~\ref{lem:y}" in body
    assert r"\eqref{C-eq:z}" in body
    assert r"\tag{\getrefnumber{C-eq:w}}\digesteqlabel{eq:w}" in body
    # a row with its own \tag keeps it, and only it (two are an amsmath error)
    own = digest.digest_body("\\begin{equation}\\label{eq:v} a \\tag{absorbing}"
                             "\\end{equation}", {"eq:v"})
    assert own.count(r"\tag") == 1 and r"\tag{absorbing}" in own
    assert r"\digesteqlabel{eq:v}" in own


def test_every_numbered_display_of_a_digest_claim_is_labelled(tmp_path: Path):
    repo = copy(tmp_path)
    edit(repo, f"{A}/claims/ass-leaf.tex", "has $y \\ge 0$.",
         "has\n\\begin{equation}\n  y \\ge 0 .\n\\end{equation}")
    assert run(repo, "core-a", "--no-pdf").returncode == 0
    contract = (repo / A / "contract.tex").read_text("utf-8")
    assert r"y \ge 0 .\label{eq:auto-ass-leaf-1}" in contract
    digest = (repo / A / "digest.tex").read_text("utf-8")
    assert r"\tag{\getrefnumber{C-eq:auto-ass-leaf-1}}" in digest


# --- builds (latexmk and Graphviz) -------------------------------------------------


@NEEDS_BUILD
def test_the_built_digest_prints_the_contracts_numbers(tmp_path: Path):
    repo = copy(tmp_path)
    result = run(repo, "--all")
    assert result.returncode == 0, result.stdout + result.stderr
    for pdf in (f"{A}/contract.pdf", f"{A}/digest.pdf", f"{B}/digest.pdf",
                "spec/overview/overview.pdf", "spec/module-graph.pdf"):
        assert (repo / pdf).read_bytes().startswith(b"%PDF"), pdf
    leftovers = [p.name for p in (repo / A).iterdir()
                 if p.suffix in (".aux", ".log", ".idx", ".toc", ".fls")]
    assert not leftovers
    if shutil.which("pdftotext") is None:
        return
    text = " ".join(subprocess.run(
        ["pdftotext", str(repo / A / "digest.pdf"), "-"], capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=True).stdout.split())
    for heading in ("Definition 1.1 (Base object)", "(1.1)",
                    "Theorem 1.2 (Bound on the first coordinate)",
                    "Assumption 2.1 [A-LEAF]", "Under Assumption 2.1"):
        assert heading in text, heading
    assert re.search(r"R\s*EQUIREMENT\s+3\.1", text, re.I)
    assert "Remark" not in text and "Lemma 4.1" not in text


@NEEDS_BUILD
def test_two_builds_give_the_same_bytes_and_leave_renders_alone(tmp_path: Path):
    repo = copy(tmp_path)
    assert run(repo, "--all").returncode == 0
    before = snapshot(repo)
    svgs = sorted((repo / A / "graphs").glob("*.svg"))
    assert svgs and all(b"\r\n" not in svg.read_bytes() for svg in svgs)
    # a second --all rebuilds nothing
    again = run(repo, "--all")
    assert again.returncode == 0, again.stdout + again.stderr
    assert snapshot(repo) == before
    # a forced rebuild of one module gives the same PDF bytes, renders untouched
    forced = run(repo, "core-a")
    assert forced.returncode == 0, forced.stdout + forced.stderr
    after = snapshot(repo)
    for name in (f"{A}/contract.pdf", f"{A}/digest.pdf"):
        assert after[name][0] == before[name][0], name
        assert after[name][1] != before[name][1], name        # it was rebuilt
    for svg in svgs:
        name = svg.relative_to(repo).as_posix()
        assert after[name] == before[name], name
