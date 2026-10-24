r"""Tests for harness/math_diff.py.

Every test builds a small git repository in `tmp_path` -- a macro file and one
module `m` with a definition, a lemma with a proof and a remark -- commits it,
changes it, and runs the tool's command line as a subprocess (as the other
tests here do: `tests/harness/` is itself a package named `harness`, so the
tool cannot be imported from inside it). The cases are the ones the tool
promises: presentation-only rewrites compare equal (exit 0), a changed formula
in a statement or a changed proof step fails (exit 1) with the segment named,
a rename or a split declared in the map compares equal, non-normative
segments are reported without failing, a status change is flagged,
`--worktree` reads the disk, and `--json` parses. One smoke test runs
`HEAD HEAD` on the real tree.

Every fixture change goes through `edit`, which refuses a pattern that is not
in the text: a replacement that silently matched nothing would turn an
"equal after normalisation" test into a comparison of identical files.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

MACROS = r"""% PART A
\newcommand{\Hs}[1]{\mathcal{H}(#1)}
\newcommand{\kout}{k_{\mathrm{out}}}
\DeclareMathOperator{\Tr}{Tr}
"""

DEF_SPACE = r"""% ---
% id: m/def:space
% kind: def
% title: "Spaces"
% summary: >-
%   Fixes the spaces.
% status: accepted
% uses: []
% assumes: []
% refs: []
% provenance: newly-derived
% ---

\begin{definition}[Spaces]\label{def:space}
For a system $A$ write $\Hs{A}$ for its Hilbert space.
The output length is $\kout\in\mathbb{N}$.
\end{definition}
"""

LEM_BOUND = r"""% ---
% id: m/lem:bound
% kind: lem
% title: "The bound"
% summary: >-
%   Bounds the output length.
% status: accepted
% uses: [def:space]
% assumes: []
% refs: []
% provenance: newly-derived
% ---

Throughout, $n$ is the number of rounds.

\begin{lemma}[The bound]\label{lem:bound}
For every $n\ge1$ and every state $\rho$ on $\Hs{A}$,
\begin{equation}\label{eq:bound}
  \kout\le n\,\Tr[\rho].
\end{equation}
\end{lemma}

\begin{proof}
By Definition~\ref{def:space}, $\kout$ counts output bits, and
\begin{equation*}
  \kout = \sum_{i=1}^{n} x_i \le n\cdot 1 = n\,\Tr[\rho],
\end{equation*}
because each $x_i\le1$ and $\Tr[\rho]=1$.
\end{proof}
"""

REM_NOTE = r"""% ---
% id: m/rem:note
% kind: rem
% title: "A note"
% status: accepted
% uses: [lem:bound]
% assumes: []
% refs: []
% provenance: newly-derived
% ---

\begin{remark}[A note]\label{rem:note}
Lemma~\ref{lem:bound} is tight: equality holds in \eqref{eq:bound} when every
round succeeds, and at half the rounds the bound is $\frac{1}{2}n$.
\end{remark}
"""

#: The remark's sentence, as a lemma's trailing text would carry it.
REM_SENTENCE = (r"Lemma~\ref{lem:bound} is tight: equality holds in \eqref{eq:bound}"
                " when every\nround succeeds, and at half the rounds the bound is"
                r" $\frac{1}{2}n$.")

CLAIMS = "spec/modules/m/claims"
BASE_FILES = {
    "spec/macros.tex": MACROS,
    "spec/modules/m/module.yaml": "id: m\nkind: core\n",
    f"{CLAIMS}/def-space.tex": DEF_SPACE,
    f"{CLAIMS}/lem-bound.tex": LEM_BOUND,
    f"{CLAIMS}/rem-note.tex": REM_NOTE,
}


def edit(text: str, *pairs: tuple[str, str]) -> str:
    """Apply replacements, refusing any whose pattern is not in the text."""
    for old, new in pairs:
        assert old in text, f"fixture pattern not found: {old!r}"
        text = text.replace(old, new)
    return text


def git(repo: Path, *args: str) -> str:
    """Run git in the fixture repository with a fixed identity."""
    result = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=math-diff-test",
         "-c", "user.email=math-diff-test@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", *args],
        capture_output=True, text=True, check=True)
    return result.stdout.strip()


def write(repo: Path, rel: str, text: str) -> None:
    """Write a fixture file with LF line ends."""
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def commit(repo: Path, message: str = "step") -> str:
    """Commit everything in the fixture repository and return the sha."""
    git(repo, "add", "--all")
    git(repo, "commit", "-q", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def write_map(tmp_path: Path, data: dict[str, Any]) -> str:
    """Write a claim map and return its path."""
    path = tmp_path / "map.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Build a fixture repository with the base files committed."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    for rel, text in BASE_FILES.items():
        write(root, rel, text)
    commit(root, "base")
    return root


Runner = Callable[..., tuple[int, str]]


@pytest.fixture
def run() -> Runner:
    """Run the tool's command line; return its exit code and stdout."""
    def runner(repo: Path, *args: str) -> tuple[int, str]:
        result = subprocess.run(
            [sys.executable, "-m", "harness.math_diff", *args, "--repo", str(repo)],
            cwd=REPO_ROOT, capture_output=True, encoding="utf-8", check=False)
        if result.returncode not in (0, 1):     # a usage error or a crash
            return result.returncode, result.stdout + result.stderr
        return result.returncode, result.stdout

    return runner


def run_json(run: Runner, repo: Path, *args: str) -> tuple[int, dict[str, Any]]:
    """Run with ``--json`` and parse the output."""
    code, out = run(repo, *args, "--json")
    return code, json.loads(out)


def claim_entry(data: dict[str, Any], claim_id: str) -> dict[str, Any]:
    """Return the report entry whose old or new ids include ``claim_id``."""
    return next(c for c in data["claims"] if claim_id in c["old"] + c["new"])


def segments(entry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index a report entry's segments by name."""
    return {s["segment"]: s for s in entry["segments"]}


def change(repo: Path, rel: str, text: str) -> str:
    """Write one changed file, commit it, and return the base it changed."""
    base = git(repo, "rev-parse", "HEAD")
    write(repo, rel, text)
    commit(repo)
    return base


def test_identical_revisions_exit_zero_with_an_empty_report(repo: Path, run: Runner):
    code, out = run(repo, "HEAD", "HEAD")
    assert code == 0, out
    assert "No differences after normalisation." in out
    assert "## Claims" not in out
    code, data = run_json(run, repo, "HEAD", "HEAD")
    assert code == 0
    assert data["claims"] == []
    assert data["counts"]["old_claims"] == 3


def test_presentation_only_changes_compare_equal(repo: Path, run: Runner):
    """Whitespace, comments, labels, titles, emphasis, spacing, displays, refs."""
    base = git(repo, "rev-parse", "HEAD")
    write(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND,
        ("Throughout, $n$ is the number of rounds.",
         "Throughout,   $n$ is the number\nof rounds. % a comment"),
        ("[The bound]", "[Output-length bound]"),
        (r"For every $n\ge1$ and every state $\rho$",
         r"For \emph{every} $n\ge1$ and every state~$\rho$"),
        ("\\begin{equation}\\label{eq:bound}\n  \\kout\\le n\\,\\Tr[\\rho].\n"
         "\\end{equation}",
         "\\begin{align}\\label{eq:bound}\n  \\kout &\\le n\\;"
         "\\Tr\\left[\\rho\\right].\n\\end{align}"),
        (r"By Definition~\ref{def:space}", r"By \Cref{def:space}"),
        ("\\begin{equation*}\n  \\kout = \\sum_{i=1}^{n} x_i \\le n\\cdot 1"
         " = n\\,\\Tr[\\rho],\n\\end{equation*}",
         "\\begin{align*}\n  \\kout &= \\sum_{i=1}^{n} x_i \\\\\n"
         "        &\\le n\\cdot 1 = n\\,\\Tr\\bigl[\\rho\\bigr],\n"
         "\\end{align*}"),
    ))
    write(repo, f"{CLAIMS}/rem-note.tex", edit(
        REM_NOTE,
        (r"Lemma~\ref{lem:bound}", r"\xref{m/lem:bound}"),
        (r"\frac{1}{2}", r"\dfrac{1}{2}"),
        ("[A note]", "[A remark]"),
        ("round succeeds", r"\tref[round]{round} succeeds"),
    ))
    write(repo, f"{CLAIMS}/def-space.tex", edit(
        DEF_SPACE,
        (r"\label{def:space}", r"\label{def:space}% the label stays"),
        (r"$\kout\in\mathbb{N}$", r"$ \kout \in \mathbb{N} $"),
        ("The output length", r"The \term[how many bits come out]{output length}"),
    ))
    commit(repo, "presentation")
    code, data = run_json(run, repo, base, "HEAD")
    assert code == 0, json.dumps(data, indent=1)
    assert data["counts"]["statements_differ"] == 0
    assert data["counts"]["proofs_differ"] == 0
    assert data["counts"]["other_segments_differ"] == 0


def test_a_bare_or_broken_texttt_id_reads_as_the_reference_it_names(
        repo: Path, run: Runner):
    r"""``\texttt{def:\allowbreak space}`` and ``\ref{def:space}`` compare equal."""
    write(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND,
        (r"By Definition~\ref{def:space}", r"By \texttt{def:\allowbreak space}")))
    base = commit(repo, "texttt")
    write(repo, f"{CLAIMS}/lem-bound.tex", LEM_BOUND)
    commit(repo, "ref")
    code, out = run(repo, base, "HEAD")
    assert code == 0, out
    write(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND, (r"By Definition~\ref{def:space}", r"By Lemma~\ref{lem:bound}")))
    commit(repo, "another claim")
    code, out = run(repo, base, "HEAD")
    assert code == 1, out


def test_a_changed_formula_in_a_statement_fails_and_names_the_segment(
        repo: Path, run: Runner):
    base = change(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND, (r"For every $n\ge1$", r"For every $n\ge2$")))
    code, out = run(repo, base, "HEAD")
    assert code == 1
    assert "### `m/lem:bound`" in out
    assert "statement: **differs (fails)**" in out
    assert "- math: " in out
    code, data = run_json(run, repo, base, "HEAD")
    statement = segments(claim_entry(data, "m/lem:bound"))["statement"]
    assert statement["fails"] is True
    assert [(op["old"], op["new"], op["kind"]) for op in statement["ops"]] == [
        ("1", "2", "math")]
    assert data["counts"]["statements_differ"] == 1
    assert data["counts"]["proofs_differ"] == 0


def test_a_changed_proof_step_fails(repo: Path, run: Runner):
    base = change(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND, (r"because each $x_i\le1$", r"because each $x_i\le2$")))
    code, data = run_json(run, repo, base, "HEAD")
    assert code == 1
    proof = segments(claim_entry(data, "m/lem:bound"))["proof"]
    assert proof["fails"] is True
    assert (data["counts"]["statements_differ"], data["counts"]["proofs_differ"]) \
        == (0, 1)


def rename_bound(repo: Path) -> str:
    """Rename m/lem:bound to m/lem:main-bound everywhere; return the base."""
    base = git(repo, "rev-parse", "HEAD")
    (repo / CLAIMS / "lem-bound.tex").unlink()
    write(repo, f"{CLAIMS}/lem-main-bound.tex", edit(
        LEM_BOUND,
        ("m/lem:bound", "m/lem:main-bound"),
        (r"\label{lem:bound}", r"\label{lem:main-bound}"),
    ))
    write(repo, f"{CLAIMS}/rem-note.tex", edit(
        REM_NOTE,
        ("uses: [lem:bound]", "uses: [lem:main-bound]"),
        (r"\ref{lem:bound}", r"\ref{lem:main-bound}"),
    ))
    commit(repo, "rename")
    return base


def test_a_rename_declared_in_the_map_compares_equal(repo: Path, run: Runner,
                                                     tmp_path: Path):
    base = rename_bound(repo)
    mapping = write_map(tmp_path, {"renames": {"m/lem:bound": "m/lem:main-bound"}})
    code, data = run_json(run, repo, base, "HEAD", "--map", mapping)
    assert code == 0, json.dumps(data, indent=1)
    entry = claim_entry(data, "m/lem:main-bound")
    assert (entry["relation"], entry["old"], entry["new"]) == (
        "renamed", ["m/lem:bound"], ["m/lem:main-bound"])
    assert entry["segments"] == [] and entry["headers"] == []
    assert data["counts"]["renamed"] == 1
    assert "m/rem:note" not in json.dumps(data["claims"])   # its refs followed


def test_a_rename_without_the_map_fails(repo: Path, run: Runner):
    base = rename_bound(repo)
    code, out = run(repo, base, "HEAD")
    assert code == 1
    assert "removed without a map entry, unaccounted (fails)" in out
    assert "added without a map entry, unaccounted (fails)" in out


def test_a_split_whose_concatenation_is_equal_compares_equal(
        repo: Path, run: Runner, tmp_path: Path):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, f"{CLAIMS}/def-space.tex", edit(
        DEF_SPACE, ("\nThe output length is $\\kout\\in\\mathbb{N}$.", "")))
    write(repo, f"{CLAIMS}/def-output.tex", edit(
        DEF_SPACE,
        ("m/def:space", "m/def:output"),
        (r"\label{def:space}", r"\label{def:output}"),
        ("Fixes the spaces.", "Fixes the output length."),
        ("For a system $A$ write $\\Hs{A}$ for its Hilbert space.\n", ""),
    ))
    write(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND, (r"Definition~\ref{def:space}", r"Definition~\ref{def:output}")))
    commit(repo, "split")
    mapping = write_map(tmp_path, {
        "splits": {"m/def:space": ["m/def:space", "m/def:output"]}})
    code, data = run_json(run, repo, base, "HEAD", "--map", mapping)
    assert code == 0, json.dumps(data, indent=1)
    entry = claim_entry(data, "m/def:output")
    assert entry["relation"] == "split"
    assert entry["new"] == ["m/def:space", "m/def:output"]
    found = segments(entry)
    assert "statement" not in found
    assert found["summary"]["fails"] is False     # two summaries now, reported
    code, _out = run(repo, base, "HEAD")          # without the map: unaccounted
    assert code == 1


def test_summary_and_lead_in_changes_are_reported_but_pass(repo: Path, run: Runner):
    base = change(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND,
        ("Bounds the output length.", "Bounds the output by the rounds."),
        ("$n$ is the number of rounds", "$n$ counts the rounds"),
    ))
    code, out = run(repo, base, "HEAD")
    assert code == 0, out
    assert "summary: differs (reported, does not fail)" in out
    assert "lead-in: differs (reported, does not fail)" in out
    code, data = run_json(run, repo, base, "HEAD")
    found = segments(claim_entry(data, "m/lem:bound"))
    assert {name: s["fails"] for name, s in found.items()} == {
        "summary": False, "lead-in": False}


def test_a_status_change_is_flagged(repo: Path, run: Runner):
    base = change(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND, ("status: accepted", "status: verified")))
    code, out = run(repo, base, "HEAD")
    assert code == 0, out
    flags = out.split("## Flags", 1)[1].split("##", 1)[0]
    assert "status changed: `m/lem:bound`: accepted -> verified" in flags
    assert "**(status change)**" in out


#: An assumption carrying the four assumption fields, added on top of the base
#: commit by the tests that need it (the base fixture has no assumption).
ASS_ROUNDS = r"""% ---
% id: m/ass:rounds
% kind: ass
% title: "Independent rounds"
% summary: >-
%   The rounds are independent.
% status: accepted
% uses: []
% assumes: []
% refs: []
% provenance: newly-derived
% short_id: A-ROUNDS
% verification: never
% category: protocol-structure
% affects: [secrecy]
% user_statement: >-
%   Applies to every run. Each round uses fresh devices.
% ---

\begin{assumption}[Independent rounds]\label{ass:rounds}
The $n$ rounds are independent.
\end{assumption}
"""


def with_assumption(repo: Path) -> None:
    """Commit the assumption fixture on top of the base files."""
    write(repo, f"{CLAIMS}/ass-rounds.tex", ASS_ROUNDS)
    commit(repo, "assumption")


def test_assumption_header_fields_are_reported_and_do_not_fail(
        repo: Path, run: Runner):
    """`category`, `affects` and `refines` are header changes."""
    with_assumption(repo)
    base = change(repo, f"{CLAIMS}/ass-rounds.tex", edit(
        ASS_ROUNDS,
        ("category: protocol-structure", "category: source"),
        ("affects: [secrecy]", "affects: [secrecy, correctness]\n% refines: A-SPEC"),
    ))
    code, out = run(repo, base, "HEAD")
    assert code == 0, out
    for name in ("category", "affects", "refines"):
        assert f"- `{name}`: " in out
    code, data = run_json(run, repo, base, "HEAD")
    entry = claim_entry(data, "m/ass:rounds")
    assert entry["fails"] is False and entry["segments"] == []
    headers = {h["field"]: h for h in entry["headers"]}
    assert set(headers) == {"category", "affects", "refines"}
    assert (headers["category"]["old"], headers["category"]["new"]) == (
        "protocol-structure", "source")
    assert (headers["affects"]["added"], headers["affects"]["removed"]) == (
        ["correctness"], [])
    assert (headers["refines"]["old"], headers["refines"]["new"]) == (None, "A-SPEC")
    # `affects` is compared as a set: reordering it is no change.
    base = change(repo, f"{CLAIMS}/ass-rounds.tex", edit(
        ASS_ROUNDS,
        ("category: protocol-structure", "category: source"),
        ("affects: [secrecy]", "affects: [correctness, secrecy]\n% refines: A-SPEC"),
    ))
    code, data = run_json(run, repo, base, "HEAD")
    assert code == 0
    assert data["counts"]["header_changes"] == 0
    assert not any("m/ass:rounds" in c["old"] + c["new"] for c in data["claims"])


def test_a_user_statement_change_alone_is_reported_and_exits_zero(
        repo: Path, run: Runner):
    """A non-normative `user_statement` is a segment that never fails."""
    with_assumption(repo)
    base = change(repo, f"{CLAIMS}/ass-rounds.tex", edit(
        ASS_ROUNDS, ("uses fresh devices", "reuses no device state")))
    code, out = run(repo, base, "HEAD")
    assert code == 0, out
    assert "user_statement: differs (reported, does not fail)" in out
    code, data = run_json(run, repo, base, "HEAD")
    found = segments(claim_entry(data, "m/ass:rounds"))
    assert {name: s["fails"] for name, s in found.items()} == {
        "user_statement": False}
    assert data["counts"]["statements_differ"] == 0


def test_worktree_mode_reads_the_files_on_disk(repo: Path, run: Runner):
    code, _out = run(repo, "HEAD", "--worktree")
    assert code == 0
    write(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND, (r"\kout\le n", r"\kout\ge n")))
    code, out = run(repo, "HEAD", "--worktree")
    assert code == 1
    assert "-> worktree" in out
    assert "statement: **differs (fails)**" in out


def test_json_output_parses_with_the_documented_keys(repo: Path, run: Runner):
    code, data = run_json(run, repo, "HEAD", "HEAD")
    assert code == data["exit_code"] == 0
    assert {"old", "new", "map", "module", "counts", "flags", "map_problems",
            "claims"} <= set(data)


def test_a_renamed_macro_compares_equal(repo: Path, run: Runner):
    base = git(repo, "rev-parse", "HEAD")
    write(repo, "spec/macros.tex", edit(MACROS, (r"\kout", r"\klen")))
    for name, text in (("def-space.tex", DEF_SPACE), ("lem-bound.tex", LEM_BOUND)):
        write(repo, f"{CLAIMS}/{name}", edit(text, (r"\kout", r"\klen")))
    commit(repo, "macro rename")
    code, out = run(repo, base, "HEAD")
    assert code == 0, out


def test_brace_only_differences_are_noted_not_failed(repo: Path, run: Runner):
    base = change(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND, (r"\sum_{i=1}^{n}", r"\sum_{i=1}^n")))
    code, data = run_json(run, repo, base, "HEAD")
    assert code == 0
    proof = segments(claim_entry(data, "m/lem:bound"))["proof"]
    assert (proof["brace_only"], proof["fails"]) == (True, False)


def test_a_sentence_moved_out_of_a_lead_in_is_reported_as_moved(
        repo: Path, run: Runner):
    base = change(repo, f"{CLAIMS}/lem-bound.tex", edit(
        LEM_BOUND,
        ("Throughout, $n$ is the number of rounds.\n\n", ""),
        ("\\label{lem:bound}\n",
         "\\label{lem:bound}\nThroughout, $n$ is the number of rounds.\n"),
    ))
    code, data = run_json(run, repo, base, "HEAD")
    assert code == 1                    # the statement did change
    moved = claim_entry(data, "m/lem:bound")["moved_out"]
    assert [(m["from_segment"], m["to"], m["to_segment"]) for m in moved] == [
        ("lead-in", "m/lem:bound", "statement")]


def test_a_deleted_claim_fails_whether_or_not_the_map_declares_it(
        repo: Path, run: Runner, tmp_path: Path):
    """Deleting a claim is never editorial: exit 1 either way, reported apart.

    Undeclared, the deletion is unaccounted; declared under `deleted`, it is
    reported as "deleted (declared in map)" with its sentence traced to where
    it moved -- the declaration changes the report, not the exit code.
    """
    assert REM_SENTENCE in REM_NOTE
    base = git(repo, "rev-parse", "HEAD")
    (repo / CLAIMS / "rem-note.tex").unlink()
    write(repo, f"{CLAIMS}/lem-bound.tex", LEM_BOUND + "\n" + REM_SENTENCE + "\n")
    commit(repo, "delete")
    code, data = run_json(run, repo, base, "HEAD")
    assert code == 1
    assert claim_entry(data, "m/rem:note")["relation"] == "removed"
    assert any("removed without a map entry, unaccounted (fails)" in flag
               for flag in data["flags"])
    assert not any("declared in map" in flag for flag in data["flags"])
    mapping = write_map(tmp_path, {"deleted": ["m/rem:note"]})
    code, data = run_json(run, repo, base, "HEAD", "--map", mapping)
    assert code == 1, json.dumps(data, indent=1)
    entry = claim_entry(data, "m/rem:note")
    assert (entry["relation"], entry["fails"]) == ("deleted", True)
    assert "deleted (declared in map) (fails): `m/rem:note`" in data["flags"]
    assert not any("unaccounted" in flag for flag in data["flags"])
    assert data["counts"]["deleted"] == 1 and data["counts"]["removed"] == 0
    moved = entry["moved_out"]
    assert [(m["to"], m["to_segment"]) for m in moved] == [("m/lem:bound", "trailing")]


def test_module_filter_and_usage_errors(repo: Path, run: Runner, tmp_path: Path):
    assert run(repo, "HEAD", "HEAD", "--module", "m")[0] == 0
    assert run(repo, "HEAD", "HEAD", "--module", "nope")[0] == 2
    assert run(repo, "HEAD")[0] == 2                      # neither NEW nor --worktree
    assert run(repo, "no-such-revision", "HEAD")[0] == 2
    code, out = run(repo, "HEAD", "HEAD", "--map", str(tmp_path / "absent.json"))
    assert code == 0
    assert "not found; an empty map is used" in out


def test_head_against_head_on_the_real_tree_is_empty_and_quick(run: Runner):
    start = time.perf_counter()
    code, out = run(REPO_ROOT, "HEAD", "HEAD")
    elapsed = time.perf_counter() - start
    assert code == 0, out
    assert "No differences after normalisation." in out
    assert elapsed < 60, f"math_diff HEAD HEAD took {elapsed:.1f} s"
