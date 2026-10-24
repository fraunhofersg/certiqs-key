r"""Tests for ``harness/relabel.py``: a claim id renamed everywhere it lives.

MOTIVATION, AND THE ERROR CLASS IT CATCHES. The relabel exists because a claim
id lives outside ``spec/`` (docstrings, ``CLAIM_ROOTS``, the generated closure
table, frozen oracle registries, instances, runs) where ``check_claims`` does
not look, so a missed site fails silently. These tests build a small tree in
``tmp_path`` -- two cores, a submodule, a code package, an oracle registry
with numbers and short codes, history folders and generated files --
and pin what a rename, a re-kind and a move rewrite, what they only print,
what they refuse and what they never touch. The word-boundary tests are the
ones the tool is most likely to get wrong silently (``thm:c1`` inside
``thm:c17``). A last test runs a dry run on the real tree and checks that it
plans edits and writes nothing.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from certiqs_key.domain.claim_closure import CLAIM_ROOTS

REPO_ROOT = Path(__file__).resolve().parents[2]
# The fixture's code package, spelt through a constant: the tree-wide
# test_every_certiqs_key_path_named_in_the_tree_exists follows every literal
# package path of a .py file to a file of this checkout, and the fixture's
# core_a and core_b packages exist only in tmp_path.
PKG = "src/certiqs_key"


def _load_tools() -> tuple[ModuleType, ModuleType]:
    """Return ``harness/relabel.py`` and ``harness/check_claims.py``, loaded by path.

    ``tests/harness/`` is itself a package named ``harness``, so under pytest's
    prepend import mode ``from harness import relabel`` resolves to the test
    package (see test_claim_implements_resolve.py). The real package is placed
    under the name ``harness`` only while the two tool modules load, and the
    import state before the load is restored afterwards.
    """
    if "_harness_relabel" in sys.modules:
        return sys.modules["_harness_relabel"], sys.modules["_harness_relabel_checker"]
    names = ("harness", "harness.check_claims", "harness.relabel")
    saved = {name: sys.modules[name] for name in names if name in sys.modules}
    try:
        for name in names:
            sys.modules.pop(name, None)
        spec = importlib.util.spec_from_file_location(
            "harness", REPO_ROOT / "harness" / "__init__.py",
            submodule_search_locations=[str(REPO_ROOT / "harness")])
        assert spec is not None and spec.loader is not None
        package = importlib.util.module_from_spec(spec)
        sys.modules["harness"] = package
        spec.loader.exec_module(package)
        tool = importlib.import_module("harness.relabel")
        checker = sys.modules["harness.check_claims"]
    finally:
        for name in names:
            sys.modules.pop(name, None)
        sys.modules.update(saved)
    sys.modules["_harness_relabel"] = tool
    sys.modules["_harness_relabel_checker"] = checker
    return tool, checker


relabel, _checker = _load_tools()
load_repo = _checker.load_repo

FILES: dict[str, str] = {
    "refs/index.json": '{"schema_version": "1.0.0", "entries": []}\n',
    "spec/modules.yaml": (
        "cores:\n"
        "  - id: core-a\n"
        "    submodules:\n"
        "      - id: sub-x\n"
        "  - id: core-b\n"
    ),
    "spec/architecture.md": (
        "The main bound core-a/thm:c1 (see also thm:c1) and sub-x/lem:helper.\n"
    ),
    "spec/modules/core-a/module.yaml": (
        "# history: 0.1.0 added thm:c1\n"
        "id: core-a\n"
        "kind: core\n"
        "version: 0.1.0\n"
        "title: Core A\n"
        "depends_on: []\n"
        "submodules: [sub-x]\n"
        "reading_groups:\n"
        "  - title: Basics\n"
        "    start: def:base\n"
        "  - title: Results\n"
        "    start: thm:c1\n"
        "    abstract: Opens with [[thm:c1]].\n"
        "order:\n"
        "  - def:base\n"
        "  - thm:c1\n"
        "  - thm:c17\n"
        "  - rem:note\n"
    ),
    "spec/modules/core-a/claims/def-base.tex": r"""% ---
% id: core-a/def:base
% kind: def
% title: Base object
% summary: >-
%   Defines the base object.
% status: draft
% uses: []
% assumes: []
% refs: []
% provenance: newly-derived
% ---

\begin{definition}\label{def:base}
A base object is a pair $(x, y)$ with
\begin{equation}\label{eq:base}
  x + y = 1 .
\end{equation}
\end{definition}
""",
    "spec/modules/core-a/claims/thm-c1.tex": r"""% ---
% id: core-a/thm:c1
% kind: thm
% title: Main bound
% summary: >-
%   The main bound on [[def:base]] objects.
% status: draft
% uses: [def:base]
% assumes: []
% refs: []
% provenance: newly-derived
% implements: certiqs_key.core_a.bound:main
% notes: "see thm:c17 for the refinement"
% ---

\begin{theorem}\label{thm:c1}
For every base object of Definition~\ref{def:base},
\begin{equation}\label{eq:c1}
  x \le 1 .
\end{equation}
\end{theorem}
\begin{proof}
By \eqref{eq:base}.
\end{proof}
""",
    "spec/modules/core-a/claims/thm-c17.tex": r"""% ---
% id: core-a/thm:c17
% kind: thm
% title: Refined bound
% summary: >-
%   Sharpens the main bound.
% status: draft
% uses: [thm:c1]
% assumes: []
% refs: []
% provenance: newly-derived
% ---

\begin{theorem}\label{thm:c17}
Theorem~\ref{thm:c1} sharpens: \eqref{eq:c1} holds with $0.125$ slack (C17).
\end{theorem}
\begin{proof}
Apply Theorem~\ref{thm:c1} (\texttt{thm:c1}); this is thm:c17 itself.
\end{proof}
""",
    "spec/modules/core-a/claims/rem-note.tex": r"""% ---
% id: core-a/rem:note
% kind: rem
% title: A note on the bound
% summary: >-
%   Explains [[thm:c1]] and [[core-a/thm:c17]].
% status: draft
% uses: []
% mentions: [thm:c1, thm:c17]
% assumes: []
% refs: []
% provenance: newly-derived
% ---

\begin{remark}\label{rem:note}
A remark on Theorem~\ref{thm:c1} and Theorem~\ref{thm:c17}.
\end{remark}
""",
    "spec/modules/core-a/interface.yaml": (
        "# the bound is thm:c1; see also thm:c17\n"
        "outputs:\n"
        "  - name: bound\n"
        '    locator: "thm:c1 (ii); thm:c17"\n'
        "    claim: core-a/thm:c1\n"
    ),
    "spec/modules/core-a/design.md": (
        "The main bound (`thm:c1`, `core-a/thm:c1`) and `thm:c17`; "
        "the helper `sub-x/lem:helper`.\n"
    ),
    "spec/modules/core-a/contract.tex": "\\label{thm:c1} core-a/thm:c1\n",
    "spec/modules/core-a/graphs/README.md": "core-a/thm:c1 thm:c1\n",
    "spec/module-graph.dot": "core-a/thm:c1\n",
    "spec/modules/core-a/sub-x/module.yaml": (
        "id: sub-x\n"
        "kind: submodule\n"
        "version: 0.1.0\n"
        "title: Sub X\n"
        "depends_on: []\n"
        "order:\n"
        "  - lem:helper\n"
    ),
    "spec/modules/core-a/sub-x/claims/lem-helper.tex": r"""% ---
% id: core-a/sub-x/lem:helper
% kind: lem
% title: Helper
% summary: >-
%   A helper.
% status: draft
% uses: [core-a/thm:c1, core-a/def:base]
% assumes: []
% refs: []
% provenance: newly-derived
% ---

\begin{lemma}\label{lem:helper}
By Theorem~\ref{thm:c1}, the helper holds.
\end{lemma}
\begin{proof}
Immediate from \cref{thm:c1,def:base}.
\end{proof}
""",
    "spec/modules/core-b/module.yaml": (
        "id: core-b\n"
        "kind: core\n"
        "version: 0.1.0\n"
        "title: Core B\n"
        "depends_on: [core-a]\n"
        "order:\n"
        "  - prop:cross\n"
    ),
    "spec/modules/core-b/claims/prop-cross.tex": r"""% ---
% id: core-b/prop:cross
% kind: prop
% title: Cross
% summary: >-
%   Uses the main bound of core A.
% status: draft
% uses: [core-a/thm:c1]
% assumes: []
% refs: []
% provenance: newly-derived
% ---

\begin{proposition}\label{prop:cross}
By \xref{core-a/thm:c1} (see \texttt{core-a/thm:c1}), not core-a/thm:c1-extra.
\end{proposition}
\begin{proof}
Direct; the bare thm:c1 is foreign here.
\end{proof}
""",
    f"{PKG}/__init__.py": "",
    f"{PKG}/core_a/__init__.py": (
        '"""Core A: Theorem thm:c1 (C5 of the predecessor) and core-a/thm:c1.\n'
        "\n"
        "The constant 0.125 comes from thm:c17, not from thm:c1-extra.\n"
        '"""\n'
        "BOUND = 0.125\n"
    ),
    f"{PKG}/core_a/bound.py": (
        "def main() -> float:\n"
        '    """Implement core-a/thm:c1 (Eq. eq:c1)."""\n'
        "    return 1.0\n"
    ),
    f"{PKG}/core_b/__init__.py": '"""Reads thm:c1 and core-a/thm:c1."""\n',
    f"{PKG}/domain/claim_closure.py": (
        'CLAIM_ROOTS = ("core-a/thm:c1", "core-a/sub-x/lem:helper")\n'
    ),
    f"{PKG}/domain/claim_closure.json": (
        '{"roots": {"core-a/thm:c1": {"claims": ["core-a/def:base", '
        '"core-a/thm:c1"]}}}\n'
    ),
    "tests/oracles/registry.py": (
        "ORACLES = [\n"
        '    {"id": "O-C1", "claim": "core-a/thm:c1", "code": "C1", "value": 0.5},\n'
        '    {"id": "O-C17", "claim": "core-a/thm:c17", "code": "PC9",'
        ' "value": 1.25e-3},\n'
        '    {"id": "O-X", "claim": "core-a/thm:c1-extra", "label": "thm:c1"},\n'
        "]\n"
    ),
    "tests/harness/fixtures/other/spec/x.md": "core-a/thm:c1\n",
    "instances/demo/README.md": "This instance rests on core-a/thm:c1.\n",
    "runs/demo.py": 'ROOT = "core-a/thm:c1"\n',
    "reports/2026-01-01-history.md": "core-a/thm:c1 was accepted.\n",
    "state/open-items/x.yaml": "claims: [core-a/thm:c1]\n",
    "context/note.md": "core-a/thm:c1\n",
    "harness/tool.py": '"""Example: core-a/thm:c1."""\n',
    "HUMAN_SCRATCHPAD.md": "core-a/thm:c1\n",
}

UNTOUCHABLE = (
    "reports/2026-01-01-history.md", "state/open-items/x.yaml", "context/note.md",
    "harness/tool.py", "HUMAN_SCRATCHPAD.md", "spec/modules/core-a/contract.tex",
    "spec/modules/core-a/graphs/README.md", "spec/module-graph.dot",
    "tests/harness/fixtures/other/spec/x.md",
)


@pytest.fixture
def regenerated(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """Record the closure regenerations instead of running the real generator."""
    calls: list[Path] = []

    def fake_regenerate(root: Path) -> tuple[bool, str]:
        calls.append(root)
        return True, "wrote src/certiqs_key/domain/claim_closure.json"

    monkeypatch.setattr(relabel, "regenerate_closure", fake_regenerate)
    return calls


@pytest.fixture
def tree(tmp_path: Path, regenerated: list[Path]) -> Path:
    """Write the fixture tree (LF), with the regeneration recorded, not run."""
    for rel, text in FILES.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    return tmp_path


def read(root: Path, rel: str) -> str:
    """Return a file of the tree as stored."""
    return (root / rel).read_bytes().decode("utf-8")


def snapshot(root: Path) -> dict[str, bytes]:
    """Return every file of the tree with its bytes."""
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def run(root: Path, *args: str) -> int:
    """Run the command line against the fixture tree."""
    return int(relabel.main([*args, "--repo", str(root)]))


# ---------------------------------------------------------------------------
# a simple rename
# ---------------------------------------------------------------------------

def test_simple_rename_rewrites_every_site(tree: Path,
                                           capsys: pytest.CaptureFixture[str]) -> None:
    assert run(tree, "core-a/thm:c1", "core-a/thm:main-bound") == 0
    out = capsys.readouterr().out
    claims = "spec/modules/core-a/claims"
    assert not (tree / claims / "thm-c1.tex").exists()
    moved = read(tree, f"{claims}/thm-main-bound.tex")
    assert "% id: core-a/thm:main-bound\n" in moved
    assert "\\label{thm:main-bound}" in moved
    assert "\\label{eq:c1}" in moved                      # equation labels stay
    assert '% notes: "see thm:c17 for the refinement"\n' in moved   # free text stays
    meta = read(tree, "spec/modules/core-a/module.yaml")
    assert "  - thm:main-bound\n  - thm:c17\n" in meta
    assert "    start: thm:main-bound\n" in meta
    assert "Opens with [[thm:main-bound]]." in meta
    assert "# history: 0.1.0 added thm:c1\n" in meta      # a comment is history
    c17 = read(tree, f"{claims}/thm-c17.tex")
    assert "% uses: [thm:main-bound]\n" in c17
    assert "Theorem~\\ref{thm:main-bound} sharpens" in c17
    assert "(\\texttt{thm:main-bound}); this is thm:c17 itself." in c17
    assert "\\label{thm:c17}" in c17
    note = read(tree, f"{claims}/rem-note.tex")
    assert "% mentions: [thm:main-bound, thm:c17]\n" in note
    assert "Explains [[thm:main-bound]] and [[core-a/thm:c17]]." in note
    helper = read(tree, "spec/modules/core-a/sub-x/claims/lem-helper.tex")
    assert "% uses: [core-a/thm:main-bound, core-a/def:base]\n" in helper
    assert "\\cref{thm:main-bound,def:base}" in helper
    cross = read(tree, "spec/modules/core-b/claims/prop-cross.tex")
    assert "% uses: [core-a/thm:main-bound]\n" in cross
    assert "\\xref{core-a/thm:main-bound}" in cross
    assert "\\texttt{core-a/thm:main-bound}" in cross
    assert "not core-a/thm:c1-extra." in cross
    assert "the bare thm:c1 is foreign here" in cross     # printed, not rewritten
    interface = read(tree, "spec/modules/core-a/interface.yaml")
    assert '"thm:main-bound (ii); thm:c17"' in interface
    assert "claim: core-a/thm:main-bound\n" in interface
    assert "# the bound is thm:main-bound; see also thm:c17\n" in interface
    design = read(tree, "spec/modules/core-a/design.md")
    assert "(`thm:main-bound`, `core-a/thm:main-bound`) and `thm:c17`" in design
    assert "The main bound core-a/thm:main-bound (see also thm:c1)" in read(
        tree, "spec/architecture.md")
    assert "spec/architecture.md:1: bare 'thm:c1'" in out
    assert f"{PKG}/core_b/__init__.py:1: bare 'thm:c1'" in out
    assert "tests/oracles/registry.py:4: bare 'thm:c1'" in out
    assert "bare 'thm:c1' names core-a/thm:c1 of another contract" in out


def test_simple_rename_rewrites_code_registry_and_roots(
        tree: Path, regenerated: list[Path]) -> None:
    assert run(tree, "core-a/thm:c1", "core-a/thm:main-bound") == 0
    code = read(tree, f"{PKG}/core_a/__init__.py")
    assert code == (
        '"""Core A: Theorem thm:main-bound (C5 of the predecessor) and '
        "core-a/thm:main-bound.\n\n"
        "The constant 0.125 comes from thm:c17, not from thm:c1-extra.\n"
        '"""\nBOUND = 0.125\n')
    assert "Implement core-a/thm:main-bound (Eq. eq:c1)" in read(
        tree, f"{PKG}/core_a/bound.py")
    assert read(tree, f"{PKG}/core_b/__init__.py") == (
        '"""Reads thm:c1 and core-a/thm:main-bound."""\n')
    registry = read(tree, "tests/oracles/registry.py")
    assert '"claim": "core-a/thm:main-bound", "code": "C1", "value": 0.5}' in registry
    assert '"claim": "core-a/thm:c17", "code": "PC9", "value": 1.25e-3}' in registry
    assert '"claim": "core-a/thm:c1-extra", "label": "thm:c1"}' in registry
    assert read(tree, f"{PKG}/domain/claim_closure.py") == (
        'CLAIM_ROOTS = ("core-a/thm:main-bound", "core-a/sub-x/lem:helper")\n')
    closure = read(tree, f"{PKG}/domain/claim_closure.json")
    assert "core-a/thm:c1" not in closure
    assert read(tree, "instances/demo/README.md") == (
        "This instance rests on core-a/thm:main-bound.\n")
    assert read(tree, "runs/demo.py") == 'ROOT = "core-a/thm:main-bound"\n'
    assert regenerated == [tree]


def test_history_generated_and_fixture_files_are_untouched(tree: Path) -> None:
    before = snapshot(tree)
    assert run(tree, "core-a/thm:c1", "core-a/thm:main-bound") == 0
    after = snapshot(tree)
    for rel in UNTOUCHABLE:
        assert after[rel] == before[rel], rel


def checker_errors(root: Path) -> list[Any]:
    r"""Return check_claims' findings, less the one the fixture carries on purpose.

    lem-helper's proof keeps a cleveref list, ``\cref{thm:c1,def:base}``, so
    that the relabel's handling of a multi-target reference stays tested; the
    checker refuses ``\cref`` because cleveref is not loaded, which is not what
    these tests are about.
    """
    return [error for error in load_repo(root).errors
            if "\\cref is not available" not in error.message]


def test_rename_keeps_the_checker_green(tree: Path) -> None:
    assert checker_errors(tree) == []
    assert run(tree, "core-a/thm:c1", "core-a/thm:main-bound") == 0
    assert checker_errors(tree) == []


def test_files_stay_lf(tree: Path) -> None:
    assert run(tree, "core-a/thm:c1", "core-a/thm:main-bound") == 0
    for rel, data in snapshot(tree).items():
        assert b"\r\n" not in data, rel


# ---------------------------------------------------------------------------
# word boundaries
# ---------------------------------------------------------------------------

def test_the_longer_label_is_never_matched_by_the_shorter(tree: Path) -> None:
    assert run(tree, "core-a/thm:c1", "core-a/thm:main-bound") == 0
    for rel, data in snapshot(tree).items():
        text = data.decode("utf-8", errors="replace")
        assert "thm:main-bound7" not in text, rel
        assert "thm:main-bound-extra" not in text, rel
    assert "\\label{thm:c17}" in read(tree, "spec/modules/core-a/claims/thm-c17.tex")


def test_renaming_the_longer_label_leaves_the_shorter(tree: Path) -> None:
    before = read(tree, "spec/modules/core-a/claims/thm-c1.tex")
    assert run(tree, "core-a/thm:c17", "core-a/thm:refined") == 0
    # its only mention of thm:c17 is in the header's notes: listed, not rewritten
    assert read(tree, "spec/modules/core-a/claims/thm-c1.tex") == before
    note = read(tree, "spec/modules/core-a/claims/rem-note.tex")
    assert "% mentions: [thm:c1, thm:refined]\n" in note
    assert "Explains [[thm:c1]] and [[core-a/thm:refined]]." in note
    assert "Theorem~\\ref{thm:c1} and Theorem~\\ref{thm:refined}" in note
    registry = read(tree, "tests/oracles/registry.py")
    assert '"claim": "core-a/thm:refined", "code": "PC9", "value": 1.25e-3}' in registry
    assert '"claim": "core-a/thm:c1", "code": "C1"' in registry


def test_tokens_are_maximal() -> None:
    text = ("thm:c1 thm:c17 thm:c1-x core-a/thm:c1 core-a/thm:c1-y "
            "x/core-a/thm:c1 thm:c1.")
    bare = [m.group("tok") for m in relabel.BARE_RE.finditer(text)]
    assert bare == ["thm:c1", "thm:c17", "thm:c1-x", "thm:c1"]
    full = [m.group("tok") for m in relabel.PATH_RE.finditer(text)]
    assert full == ["core-a/thm:c1", "core-a/thm:c1-y", "x/core-a/thm:c1"]


# ---------------------------------------------------------------------------
# kinds
# ---------------------------------------------------------------------------

def test_rekind_remark_to_requirement(tree: Path,
                                     capsys: pytest.CaptureFixture[str]) -> None:
    assert run(tree, "core-a/rem:note", "core-a/req:note") == 0
    out = capsys.readouterr().out
    claims = tree / "spec/modules/core-a/claims"
    assert not (claims / "rem-note.tex").exists()
    text = read(tree, "spec/modules/core-a/claims/req-note.tex")
    assert "% id: core-a/req:note\n% kind: req\n" in text
    assert "\\begin{requirement}\\label{req:note}" in text
    assert "\\end{requirement}" in text
    assert "remark}" not in text
    assert "  - req:note\n" in read(tree, "spec/modules/core-a/module.yaml")
    if "req" not in relabel.KIND_ENV:
        assert "does not know the kind 'req'" in out


def test_kind_word_before_a_reference_is_listed(
        tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(tree, "core-a/thm:c17", "core-a/lem:c17") == 0
    out = capsys.readouterr().out
    note = read(tree, "spec/modules/core-a/claims/rem-note.tex")
    assert "Theorem~\\ref{lem:c17}" in note          # the word is the editor's
    assert "'Theorem' before a reference to core-a/lem:c17, now a lemma" in out
    assert "\\begin{lemma}\\label{lem:c17}" in read(
        tree, "spec/modules/core-a/claims/lem-c17.tex")


def test_kind_change_across_the_proof_boundary_is_refused(
        tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    before = snapshot(tree)
    with pytest.raises(relabel.RelabelError, match="proof boundary"):
        relabel.plan_relabel(tree, {"core-a/thm:c1": "core-a/def:c1"})
    assert run(tree, "core-a/rem:note", "core-a/lem:note") == 1
    assert "proof boundary" in capsys.readouterr().err
    assert snapshot(tree) == before


@pytest.mark.parametrize(("old", "new", "message"), [
    ("core-a/thm:nope", "core-a/thm:x", "unknown old id"),
    ("core-a/thm:c1", "core-a/thm:c17", "already exists"),
    ("core-a/thm:c1", "core-z/thm:c1", "does not exist"),
    ("core-a/thm:c1", "core-a/sub-x/thm:c17", "already used in the contract"),
    ("core-a/thm:c1", "core-a/theorem:c1", "not a full claim id"),
])
def test_refusals(tree: Path, capsys: pytest.CaptureFixture[str], old: str, new: str,
                  message: str) -> None:
    before = snapshot(tree)
    assert run(tree, old, new) == 1
    assert message in capsys.readouterr().err
    assert snapshot(tree) == before


# ---------------------------------------------------------------------------
# a move
# ---------------------------------------------------------------------------

def test_move_to_another_contract(tree: Path,
                                  capsys: pytest.CaptureFixture[str]) -> None:
    assert run(tree, "core-a/thm:c1", "core-b/thm:c1-moved") == 0
    out = capsys.readouterr().out
    assert not (tree / "spec/modules/core-a/claims/thm-c1.tex").exists()
    moved = read(tree, "spec/modules/core-b/claims/thm-c1-moved.tex")
    assert "% id: core-b/thm:c1-moved\n" in moved
    assert "% uses: [core-a/def:base]\n" in moved          # bare -> full id
    assert "Definition~\\xref{core-a/def:base}" in moved    # \ref -> \xref
    assert "\\label{thm:c1-moved}" in moved
    assert "[[core-a/def:base]]" in moved
    c17 = read(tree, "spec/modules/core-a/claims/thm-c17.tex")
    assert "% uses: [core-b/thm:c1-moved]\n" in c17
    assert "Theorem~\\xref{core-b/thm:c1-moved} sharpens" in c17
    assert "(\\texttt{core-b/thm:c1-moved})" in c17
    assert "\\eqref{eq:c1}" in c17                          # printed, not rewritten
    assert "\\eqref{eq:c1} points into core-a/thm:c1" in out
    cross = read(tree, "spec/modules/core-b/claims/prop-cross.tex")
    assert "% uses: [thm:c1-moved]\n" in cross              # full id -> bare
    assert "\\xref{core-b/thm:c1-moved}" in cross
    helper = read(tree, "spec/modules/core-a/sub-x/claims/lem-helper.tex")
    assert "% uses: [core-b/thm:c1-moved, core-a/def:base]\n" in helper
    assert "By Theorem~\\xref{core-b/thm:c1-moved}" in helper
    assert "\\cref{thm:c1,def:base}" in helper
    assert "split the reference and write \\xref by hand" in out
    meta_a = read(tree, "spec/modules/core-a/module.yaml")
    assert "  - def:base\n  - thm:c17\n" in meta_a
    assert "    start: thm:c17\n" in meta_a                 # the group re-anchors
    meta_b = read(tree, "spec/modules/core-b/module.yaml")
    assert meta_b.endswith("order:\n  - prop:cross\n  - thm:c1-moved\n")
    assert "appended at the end of order" in out
    assert "uses core-b/thm:c1-moved: 'core-b' is not in the depends_on" in out
    assert "'Theorem' before the new \\xref{core-b/thm:c1-moved}" in out
    bound = read(tree, f"{PKG}/core_a/bound.py")
    assert bound.count("core-b/thm:c1-moved") == 1
    code = read(tree, f"{PKG}/core_a/__init__.py")
    assert "Theorem core-b/thm:c1-moved (C5" in code         # bare leaves its scope


def test_move_into_a_submodule_of_the_same_contract(
        tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(tree, "core-a/thm:c17", "core-a/sub-x/thm:c17") == 0
    out = capsys.readouterr().out
    moved = read(tree, "spec/modules/core-a/sub-x/claims/thm-c17.tex")
    assert "% uses: [core-a/thm:c1]\n" in moved
    assert "Theorem~\\ref{thm:c1} sharpens" in moved         # same contract: \ref
    note = read(tree, "spec/modules/core-a/claims/rem-note.tex")
    assert "% mentions: [thm:c1, core-a/sub-x/thm:c17]\n" in note
    assert "Theorem~\\ref{thm:c17}" in note
    assert "[[core-a/sub-x/thm:c17]]" in note
    assert "  - lem:helper\n  - thm:c17\n" in read(
        tree, "spec/modules/core-a/sub-x/module.yaml")
    assert "  - thm:c17\n" not in read(tree, "spec/modules/core-a/module.yaml")
    assert "a core claim may not use a submodule claim" not in out


# ---------------------------------------------------------------------------
# dry run, batches, partial ids, the map file
# ---------------------------------------------------------------------------

def test_dry_run_writes_nothing(tree: Path, regenerated: list[Path],
                                capsys: pytest.CaptureFixture[str]) -> None:
    before = snapshot(tree)
    assert run(tree, "core-a/thm:c1", "core-b/thm:c1-moved", "--dry-run",
               "--map-out", str(tree / "map.json")) == 0
    out = capsys.readouterr().out
    assert snapshot(tree) == before
    assert regenerated == []
    assert ("edit  spec/modules/core-a/claims/thm-c17.tex:8: thm:c1 -> "
            "core-b/thm:c1-moved") in out
    assert ("move  spec/modules/core-a/claims/thm-c1.tex -> "
            "spec/modules/core-b/claims/thm-c1-moved.tex") in out
    assert "dry run: nothing written" in out


def test_batch_swap(tree: Path) -> None:
    batch = tree / "batch.yaml"
    batch.write_bytes(b"core-a/thm:c1: core-a/thm:c17\ncore-a/thm:c17: core-a/thm:c1\n")
    assert run(tree, "--map", str(batch)) == 0
    first = read(tree, "spec/modules/core-a/claims/thm-c1.tex")
    second = read(tree, "spec/modules/core-a/claims/thm-c17.tex")
    assert "% id: core-a/thm:c1\n" in first and "Refined bound" in first
    assert "% id: core-a/thm:c17\n" in second and "Main bound" in second
    assert "% uses: [thm:c17]\n" in first
    assert "  - thm:c17\n  - thm:c1\n" in read(tree, "spec/modules/core-a/module.yaml")
    assert checker_errors(tree) == []


def test_partial_ids_follow(tree: Path) -> None:
    assert run(tree, "core-a/sub-x/lem:helper", "core-a/sub-x/lem:aid") == 0
    assert "the helper `sub-x/lem:aid`" in read(tree, "spec/modules/core-a/design.md")
    assert "and sub-x/lem:aid." in read(tree, "spec/architecture.md")
    assert read(tree, f"{PKG}/domain/claim_closure.py") == (
        'CLAIM_ROOTS = ("core-a/thm:c1", "core-a/sub-x/lem:aid")\n')


def test_map_out_merges_chains(tree: Path) -> None:
    out = tree / "reports" / "relabel-map.json"
    assert run(tree, "core-a/thm:c1", "core-a/thm:b", "--map-out", str(out)) == 0
    assert run(tree, "core-a/thm:b", "core-a/thm:c", "--map-out", str(out)) == 0
    data: dict[str, Any] = json.loads(out.read_bytes())
    assert data == {"deleted": [], "merges": {}, "splits": {},
                    "renames": {"core-a/thm:b": "core-a/thm:c",
                                "core-a/thm:c1": "core-a/thm:c"}}
    raw = out.read_bytes()
    assert raw.endswith(b"}\n") and b"\r" not in raw


def test_merge_map_follows_splits_and_merges() -> None:
    first = relabel.merge_map({}, splits={"m/thm:a": ["m/thm:a1", "m/thm:a2"]},
                              merges={"m/lem:ab": ["m/lem:a", "m/lem:b"]})
    second = relabel.merge_map(first, renames={"m/thm:a1": "m/thm:x",
                                               "m/lem:ab": "m/lem:y"})
    assert second["splits"] == {"m/thm:a": ["m/thm:x", "m/thm:a2"]}
    assert second["merges"] == {"m/lem:y": ["m/lem:a", "m/lem:b"]}
    assert second["renames"] == {"m/lem:ab": "m/lem:y", "m/thm:a1": "m/thm:x"}
    back = relabel.merge_map(second, renames={"m/thm:x": "m/thm:a1"})
    assert back["renames"] == {"m/lem:ab": "m/lem:y", "m/thm:x": "m/thm:a1"}


def test_split_records_and_prints_sites(tree: Path,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    before = snapshot(tree)
    target = tree / "map.json"
    assert run(tree, "--split", "core-a/thm:c1",
               "--into", "core-a/thm:c1a,core-a/thm:c1b", "--map-out", str(target)) == 0
    out = capsys.readouterr().out
    after = snapshot(tree)
    assert {rel for rel in after if after[rel] != before.get(rel)} == {"map.json"}
    assert json.loads(target.read_bytes())["splits"] == {
        "core-a/thm:c1": ["core-a/thm:c1a", "core-a/thm:c1b"]}
    assert "spec/modules/core-a/claims/thm-c17.tex:8: uses entry 'thm:c1'" in out
    assert "tests/oracles/registry.py:2: names core-a/thm:c1" in out
    assert "spec/modules/core-a/module.yaml:16: order entry 'thm:c1'" in out


def test_merge_needs_a_map_file(tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(tree, "--merge", "core-a/thm:c1,core-a/thm:c17",
               "--into", "core-a/thm:joint") == 1
    assert "--map-out" in capsys.readouterr().err
    assert run(tree, "--merge", "core-a/thm:c1,core-a/thm:c17",
               "--into", "core-a/thm:joint", "--dry-run") == 0


# ---------------------------------------------------------------------------
# the real tree
# ---------------------------------------------------------------------------

def test_real_tree_dry_run_plans_and_writes_nothing() -> None:
    """A dry run on the checkout plans edits and changes no file it would edit.

    Other agents edit this clone, so ``git status`` cannot be compared; the
    files the plan names are compared by modification time and bytes instead.
    """
    idx = relabel.load_index(REPO_ROOT)
    old = next((r for r in CLAIM_ROOTS if r in idx.claims), sorted(idx.claims)[0])
    new = f"{relabel.module_of(old)}/{relabel.kind_of(old)}:relabel-smoke-test"
    plan = relabel.plan_relabel(REPO_ROOT, {old: new})
    assert plan.edits()
    assert [fp.rel for fp in plan.moves()] == [idx.rel(idx.claims[old].path)]
    watched = [REPO_ROOT / rel for rel in sorted(plan.files)]
    before = {p: (os.stat(p).st_mtime_ns, p.read_bytes()) for p in watched}
    result = subprocess.run(
        [sys.executable, "-m", "harness.relabel", old, new, "--dry-run"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "dry run: nothing written" in result.stdout
    assert f"rename {old} -> {new}" in result.stdout
    assert {p: (os.stat(p).st_mtime_ns, p.read_bytes()) for p in watched} == before
    assert not (idx.claims[old].path.parent
                / relabel.file_name(relabel.label_of(new))).exists()
