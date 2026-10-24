"""Tests for harness/check_claims.py.

Three passing fixture repositories (`good`, `effective` for the computed
status, and `format` for the claim-body commands and the `req` kind), one
failing fixture per check of spec/claim-format.md §6 or a mutation of
`format` for the format checks, and the query modes. The
checker is exercised through its command line, because the exit code and the
`path:line: message` rendering are part of what it promises.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
GOOD = str(FIXTURES / "good")
EFFECTIVE = str(FIXTURES / "effective")
ERROR_LINE = re.compile(r"^\S+:\d+: \S.*$")

# One fixture per check, and the fragment of the message it must produce.
NEGATIVE = [
    ("bad-header", "required field 'provenance' is missing"),
    ("bad-header", "status 'nearly-done' is not one of"),
    ("bad-identity", "does not match the path-derived id"),
    ("bad-proof", "requires a proof environment"),
    ("bad-uses", "does not resolve to a claim"),
    ("bad-leaf", "an assumption may only use definitions"),
    ("bad-cycle", "uses cycle"),
    ("bad-ref", "is an undeclared dependency"),
    ("bad-cite", "without a locator"),
    ("bad-cite", "is not generated from refs/index.json"),
    ("bad-shortid", "is already used by"),
    ("bad-status", "carries a proof sketch"),
    ("bad-pending", "is no longer pending"),
    ("bad-pending", "still has 1 pending reference"),
    ("bad-ex-in-uses", "is an example; an example is never a dependency"),
    ("bad-fact", "a fact is an imported result"),
    ("bad-fact", "a fact may only use definitions"),
    ("bad-sibling", "sibling depends_on cycle"),
    ("bad-sibling", "is not a sibling submodule of core-a nor the id of another"),
]


def check(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the checker from the repository root and capture its output."""
    return subprocess.run(
        [sys.executable, "-m", "harness.check_claims", *args],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )


def test_good_fixture_passes():
    result = check("--repo", GOOD)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok: 7 claim(s) in 3 module(s)" in result.stdout


def test_sample_module_passes():
    result = check("--repo", str(REPO_ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok:" in result.stdout


@pytest.mark.parametrize(("fixture", "fragment"), NEGATIVE)
def test_negative_fixture_is_caught(fixture: str, fragment: str):
    result = check("--repo", str(FIXTURES / fixture))
    assert result.returncode == 1
    assert fragment in result.stdout, result.stdout


@pytest.mark.parametrize("fixture", sorted({name for name, _ in NEGATIVE}))
def test_every_error_is_rendered_as_path_line_message(fixture: str):
    result = check("--repo", str(FIXTURES / fixture))
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines
    for line in lines:
        assert ERROR_LINE.match(line), line


def test_dependents_is_the_re_review_scope():
    result = check("--repo", GOOD, "--dependents", "core-a/def:base")
    assert result.returncode == 0, result.stdout + result.stderr
    listed = {line.split()[0] for line in result.stdout.splitlines()
              if line.startswith("  ")}
    assert listed == {"core-a/ass:leaf", "core-a/fact:ext", "core-a/thm:main",
                      "core-a/rem:aside", "core-a/sub-x/lem:helper",
                      "core-b/prop:cross"}


def test_a_declared_sibling_dependency_is_allowed_and_walked():
    # good-sibling: core-a/sub-y declares depends_on [sub-x] and its corollary
    # uses sub-x/lem:helper (a submodule's composition may use the
    # instance a sibling builds). Without the
    # declaration the same edge is refused (the module fence of check 3).
    sibling = str(FIXTURES / "good-sibling")
    result = check("--repo", sibling)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok: 8 claim(s) in 4 module(s)" in result.stdout
    walked = check("--repo", sibling, "--dependents", "core-a/sub-x/lem:helper")
    assert "  core-a/sub-y/cor:sib" in walked.stdout


def test_an_undeclared_sibling_use_is_refused(tmp_path: Path):
    import shutil

    repo = tmp_path / "repo"
    shutil.copytree(FIXTURES / "good-sibling", repo)
    meta = repo / "spec/modules/core-a/sub-y/module.yaml"
    meta.write_text(meta.read_text("utf-8").replace("depends_on: [sub-x]",
                                                     "depends_on: []"), "utf-8")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "crosses into a module not in depends_on" in result.stdout


def test_a_mention_is_not_a_dependency():
    # good/core-a/rem:aside mentions core-b/prop:cross; it must not appear as
    # a dependent of it, and the mention must not count as a cross-module use.
    result = check("--repo", GOOD, "--dependents", "core-b/prop:cross")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "dependents of core-b/prop:cross (0)" in result.stdout
    assert "mentioned by, not a dependency (1):" in result.stdout
    assert "  core-a/rem:aside" in result.stdout


def test_dependents_of_an_assumption_are_the_claims_that_declare_it():
    # thm:main and fact:ext declare A-LEAF; rem:aside uses thm:main.
    result = check("--repo", GOOD, "--dependents", "core-a/ass:leaf")
    assert result.returncode == 0, result.stdout + result.stderr
    listed = {line.split()[0] for line in result.stdout.splitlines()
              if line.startswith("  ")}
    assert {"core-a/thm:main", "core-a/fact:ext", "core-a/rem:aside"} <= listed


def test_dependents_of_the_sample_definition_reach_the_theorem():
    result = check("--repo", str(REPO_ROOT), "--dependents", "meat-core/def:homog")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "meat-core/thm:constrained-accumulation" in result.stdout


def test_dependents_of_an_unknown_claim_fails():
    result = check("--repo", GOOD, "--dependents", "core-a/thm:nonexistent")
    assert result.returncode == 1
    assert "is not a claim id" in result.stderr


def test_assumption_closure_is_transitive():
    result = check("--repo", GOOD, "--assumptions", "core-a/rem:aside")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "A-LEAF" in result.stdout
    assert "core-a/thm:main" in result.stdout


def test_status_table_counts_every_module():
    result = check("--repo", GOOD, "--status")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "core-a" in result.stdout
    assert "core-a/sub-x" in result.stdout
    assert "pending" in result.stdout.splitlines()[0]
    rows = [line for line in result.stdout.splitlines() if line.startswith("TOTAL")]
    assert rows and rows[0].split()[-1] == "7"
    assert rows[0].split()[-2] == "1"       # rem:aside's one pending label


# The effective status (computed by the checker). The fixture `effective` carries
# one accepted claim per case: thm:cond uses a draft definition, cor:chain sits
# behind it, prop:assumed declares a verified assumption, core-b/prop:foreign
# declares that same assumption across a module fence, rem:talks only mentions
# the draft, and rem:retired still uses a superseded definition.


def test_an_accepted_claim_may_use_a_draft_one():
    # The rule this replaces made a substantive amendment of one accepted claim
    # cascade through its dependent closure as status edits.
    result = check("--repo", EFFECTIVE)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok: 10 claim(s) in 2 module(s)" in result.stdout


def test_effective_status_is_the_minimum_over_the_uses_closure():
    result = check("--repo", EFFECTIVE, "--effective", "core-a/thm:cond")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "header status:    accepted" in result.stdout
    assert "effective status: draft" in result.stdout
    assert "bound by (1):" in result.stdout
    assert "core-a/def:fresh  [draft]" in result.stdout


def test_effective_status_runs_the_whole_chain():
    # cor:chain is implemented and uses the accepted thm:cond, which uses the
    # draft def:fresh: the minimum is taken over the transitive closure.
    result = check("--repo", EFFECTIVE, "--effective", "core-a/cor:chain")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "header status:    implemented" in result.stdout
    assert "effective status: draft" in result.stdout
    assert "core-a/def:fresh  [draft]" in result.stdout


def test_an_assumes_declaration_binds_the_effective_status():
    result = check("--repo", EFFECTIVE, "--effective", "core-a/prop:assumed")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "effective status: verified" in result.stdout
    assert "core-a/ass:shaky  [verified]" in result.stdout


def test_an_assumes_short_id_binds_across_a_module_fence():
    # A short id is unique repository-wide and resolves to its assumption
    # wherever it lives; the declaration is a dependency all the same.
    result = check("--repo", EFFECTIVE, "--effective", "core-b/prop:foreign")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "effective status: verified" in result.stdout
    assert "core-a/ass:shaky  [verified]" in result.stdout


def test_a_mention_does_not_bind_the_effective_status():
    result = check("--repo", EFFECTIVE, "--effective", "core-a/rem:talks")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "effective status: accepted" in result.stdout
    assert "core-a/def:fresh" not in result.stdout
    assert "core-a/rem:talks  [accepted] (itself)" in result.stdout


def test_a_superseded_dependency_ranks_below_draft():
    result = check("--repo", EFFECTIVE, "--effective", "core-a/rem:retired")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "header status:    accepted" in result.stdout
    assert "effective status: superseded" in result.stdout
    assert "core-a/def:old  [superseded]" in result.stdout


def test_effective_of_an_unknown_claim_fails():
    result = check("--repo", EFFECTIVE, "--effective", "core-a/thm:nonexistent")
    assert result.returncode == 1
    assert "is not a claim id" in result.stderr


def test_status_table_carries_the_effective_counts_beside_the_header_counts():
    result = check("--repo", EFFECTIVE, "--status")
    assert result.returncode == 0, result.stdout + result.stderr
    rows = {line.split()[0]: line.split(maxsplit=1)[1]
            for line in result.stdout.splitlines() if line and not line[0].isspace()}
    # core-a: 1 draft, 1 verified, 5 accepted, 1 implemented, 1 superseded by
    # header; effectively 3 draft, 2 verified, 2 accepted, 0 implemented,
    # 2 superseded.
    assert rows["core-a"].split() == ["1", "(3)", "1", "(2)", "5", "(2)",
                                      "1", "(0)", "1", "(2)", "0", "9"]
    assert rows["core-b"].split() == ["0", "(0)", "0", "(1)", "1", "(0)",
                                      "0", "(0)", "0", "(0)", "0", "1"]
    assert "header count (effective count)" in result.stdout


def test_graph_is_written_as_dot(tmp_path: Path):
    target = tmp_path / "claims.dot"
    result = check("--repo", GOOD, "--graph", str(target))
    assert result.returncode == 0, result.stdout + result.stderr
    dot = target.read_text(encoding="utf-8")
    assert dot.startswith("digraph claims {")
    assert '"core-a/thm:main" -> "core-a/def:base";' in dot
    assert 'core-a/def:base<BR/>Base object<BR/>verified' in dot
    assert ('"core-a/thm:main" -> "core-a/ass:leaf" '
            '[style=dashed, color="#a35f13", tooltip="assumes"]') in dot
    assert '"core-a/rem:aside" -> "core-b/prop:cross"' not in dot


def test_focused_graph_follows_external_prerequisites_and_assumptions(tmp_path: Path):
    import shutil

    repo = tmp_path / "repo"
    shutil.copytree(FIXTURES / "good", repo)
    helper = repo / "spec/modules/core-a/sub-x/claims/lem-helper.tex"
    helper.write_text(helper.read_text("utf-8").replace(
        "uses: [core-a/def:base]", "uses: [core-a/def:base, core-a/thm:main]"), "utf-8")
    target = tmp_path / "focus.dot"
    result = check("--repo", str(repo), "--focus", "core-a/sub-x/lem:helper",
                   "--graph", str(target))
    assert result.returncode == 0, result.stdout + result.stderr
    dot = target.read_text("utf-8")
    assert '"core-a/sub-x/lem:helper" -> "core-a/thm:main"' in dot
    assert '"core-a/thm:main" -> "core-a/ass:leaf"' in dot
    assert '"core-a/ass:leaf" -> "core-a/def:base"' in dot
    assert "BOUNDARY" not in dot
    assert "core-a/rem:aside" not in dot


def test_module_graph_marks_external_boundary_without_expanding_it(tmp_path: Path):
    target = tmp_path / "module.dot"
    result = check("--repo", GOOD, "--module", "core-b", "--graph", str(target))
    assert result.returncode == 0, result.stdout + result.stderr
    dot = target.read_text("utf-8")
    assert '"core-b/prop:cross" -> "core-a/def:base"' in dot
    assert "BOUNDARY: further prerequisites omitted" in dot
    assert "Base object" in dot
    assert "core-a/thm:main" not in dot


def test_unknown_graph_focus_is_reported(tmp_path: Path):
    result = check("--repo", GOOD, "--focus", "core-a/missing",
                   "--graph", str(tmp_path / "no.dot"))
    assert result.returncode == 1
    assert "is not a claim id" in result.stderr
    assert not (tmp_path / "no.dot").exists()


@pytest.mark.parametrize(("groups", "error"), [
    ("[{title: Missing, start: 'def:absent'}]", "is not in order"),
    ("[{title: First, start: 'def:base'}, {title: Again, start: 'def:base'}]",
     "unique and follow order"),
    ("[{title: Later, start: 'thm:main'}]", "first claim"),
    ("[{title: '', start: 'def:base'}]", "nonempty text"),
])
def test_reading_group_boundaries_are_checked(
    tmp_path: Path, groups: str, error: str,
):
    import shutil

    shutil.copytree(FIXTURES / "good", tmp_path, dirs_exist_ok=True)
    meta = tmp_path / "spec/modules/core-a/module.yaml"
    meta.write_text(meta.read_text("utf-8") + f"\nreading_groups: {groups}\n", "utf-8")
    result = check("--repo", str(tmp_path))
    assert result.returncode == 1
    assert error in result.stdout


def test_module_filter_narrows_the_scope():
    result = check("--repo", GOOD, "--module", "core-b")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "under core-b" in result.stdout


def test_unknown_module_filter_fails():
    result = check("--repo", GOOD, "--module", "core-z")
    assert result.returncode == 1
    assert "is not a module" in result.stderr


def test_unknown_repo_fails():
    result = check("--repo", str(FIXTURES / "does-not-exist"))
    assert result.returncode == 1
    assert "is not a directory" in result.stderr


# --- the claim format (checks 10-12, always on) -----
#
# `format` is a repository that follows the whole format: a requirement, the
# prominence field, \xref into another contract, [[...]] links in summaries
# and abstracts, \term, \iface and \repodoc. Each test below breaks one thing
# in a copy of it.

FORMAT = FIXTURES / "format"
CORE_A = "spec/modules/core-a"


def format_copy(tmp_path: Path) -> Path:
    """Return a scratch copy of the `format` fixture."""
    import shutil

    target = tmp_path / "repo"
    shutil.copytree(FORMAT, target)
    return target


def edit(repo: Path, relative: str, old: str, new: str) -> None:
    """Replace one exact fragment of a fixture file, which must be there."""
    path = repo / relative
    text = path.read_text("utf-8")
    assert old in text, (relative, old)
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def test_format_fixture_passes_every_check():
    result = check("--repo", str(FORMAT))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok: 7 claim(s) in 3 module(s)" in result.stdout
    assert "presentation[" not in result.stdout


def test_the_presentation_flag_is_gone():
    result = check("--repo", str(FORMAT), "--presentation")
    assert result.returncode == 2
    assert "unrecognized arguments: --presentation" in result.stderr


def test_a_requirement_carries_no_proof(tmp_path: Path):
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/claims/req-refuse.tex", "\\end{requirement}\n",
         "\\end{requirement}\n\n\\begin{proof}\nNone.\n\\end{proof}\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "kind 'req' must carry no proof environment" in result.stdout


def test_a_requirement_needs_its_environment(tmp_path: Path):
    repo = format_copy(tmp_path)
    path = f"{CORE_A}/claims/req-refuse.tex"
    edit(repo, path, "\\begin{requirement}", "\\begin{remark}")
    edit(repo, path, "\\end{requirement}", "\\end{remark}")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "environment 'remark' does not match kind 'req'" in result.stdout


@pytest.mark.parametrize(("file", "old", "new", "fragment"), [
    ("claims/thm-bound.tex", "prominence: main", "prominence: headline",
     "prominence 'headline' is not one of main, standard, technical"),
    ("claims/rem-tight.tex", "prominence: standard", "prominence: main",
     "a remark or an example is never a main result"),
])
def test_prominence_vocabulary(tmp_path: Path, file: str, old: str, new: str,
                               fragment: str):
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/{file}", old, new)
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert fragment in result.stdout


VERIFICATION_CASES = [
    ("claims/ass-leaf.tex", "% verification: never\n", "",
     "an assumption requires a verification (never, partly;"),
    ("claims/ass-leaf.tex", "% verification: never\n", "% verification: maybe\n",
     "verification 'maybe' is not one of never, partly"),
    ("claims/thm-bound.tex", "% lean:\n", "% verification: never\n% lean:\n",
     "verification is for assumptions only"),
    ("claims/ass-leaf.tex", "% verification: never\n", "% verification: decided\n",
     "verification 'decided' is refused on an assumption, which is an unchecked "
     "premise: a condition the engine decides is a definition plus a requirement"),
    ("claims/ass-leaf.tex", "% verification: never\n",
     "% verification: discharged\n",
     "verification 'discharged' is refused on an assumption, which is an unchecked "
     "premise: a condition a theorem discharges is a lemma"),
]


@pytest.mark.parametrize(("file", "old", "new", "fragment"), VERIFICATION_CASES,
                         ids=["missing", "unknown", "not-an-assumption", "decided",
                              "discharged"])
def test_an_assumption_states_whether_the_engine_verifies_it(
    tmp_path: Path, file: str, old: str, new: str, fragment: str,
):
    """Whether a run rests on an assumption unverified has one home.

    spec/claim-format.md section 3.2 makes the header field the one source,
    required on every assumption and refused on every other kind. An
    assumption is an unchecked premise, so `decided` and `discharged` are
    refused on it (such a condition is a definition plus a requirement, or a
    lemma).
    """
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/{file}", old, new)
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert fragment in result.stdout, result.stdout


def test_prominence_is_required(tmp_path: Path):
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/claims/rem-tight.tex", "% prominence: standard\n", "")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "presentation[prominence-missing]" in result.stdout


# These presentation rules fail the default run.
PROMOTED_CASES = [
    ("claims/rem-tight.tex", "% lean:\n", "% lean:\n% origin: 'an older repository'\n",
     "header: unknown field 'origin'"),
    ("claims/rem-tight.tex", "\\begin{remark}",
     "\\begin{remark}[Sharpness of the bound]",
     "\\begin{remark} carries a bracketed title"),
    ("claims/rem-tight.tex", "at y = 0.",
     "at y = 0 in units of \N{PLANCK CONSTANT OVER TWO PI}.",
     "summary carries U+210F, outside the mapped Unicode set"),
    ("module.yaml", "The one hypothesis of the bound.",
     "The one hypothesis of the bound \N{PLANCK CONSTANT OVER TWO PI}.",
     "reading_groups abstract carries U+210F"),
]


@pytest.mark.parametrize(("file", "old", "new", "fragment"), PROMOTED_CASES,
                         ids=["origin", "env-title", "summary-unicode",
                              "abstract-unicode"])
def test_the_promoted_presentation_rules_fail_the_default_run(
    tmp_path: Path, file: str, old: str, new: str, fragment: str,
):
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/{file}", old, new)
    result = check("--repo", str(repo))
    assert result.returncode == 1, result.stdout
    assert fragment in result.stdout, result.stdout
    assert "presentation[" not in result.stdout


XREF_CASES = [
    ("\\xref{core-a/thm:missing}", "names no claim"),
    ("\\xref{thm:bound}", "needs a full claim id"),
    ("\\xref{core-a/def:object}", "is not declared: list it in uses or mentions"),
]


@pytest.mark.parametrize(("replacement", "fragment"), XREF_CASES)
def test_a_wrong_xref_is_refused(tmp_path: Path, replacement: str, fragment: str):
    repo = format_copy(tmp_path)
    edit(repo, "spec/modules/core-b/claims/prop-cross.tex",
         "by \\xref{core-a/thm:bound}.", f"by {replacement}.")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert fragment in result.stdout, result.stdout
    assert "prop-cross.tex:18:" in result.stdout      # the line of the \xref


TREF_CASES = [
    ("\\tref{base object}", None),
    ("\\tref[base object]{base objects}", None),
    ("\\tref{cap}", "no \\term of any contract defines"),
]


@pytest.mark.parametrize(("use", "fragment"), TREF_CASES)
def test_a_term_link_must_resolve(tmp_path: Path, use: str, fragment: str | None):
    repo = format_copy(tmp_path)
    edit(repo, "spec/modules/core-b/claims/prop-cross.tex",
         "Every \\tref{base object} satisfies", f"Every {use} satisfies")
    result = check("--repo", str(repo))
    if fragment is None:
        assert result.returncode == 0, result.stdout
    else:
        assert result.returncode == 1
        assert fragment in result.stdout, result.stdout
        assert "prop-cross.tex:18:" in result.stdout


def test_an_xref_into_its_own_contract_is_refused(tmp_path: Path):
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/claims/rem-tight.tex", "Theorem~\\ref{thm:bound}",
         "\\xref{core-a/thm:bound}")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "names a claim of this contract; refer to it as Theorem~\\ref{thm:bound}" \
        in result.stdout


def test_an_xref_may_name_an_assumption_through_its_short_id(tmp_path: Path):
    repo = format_copy(tmp_path)
    edit(repo, "spec/modules/core-b/claims/prop-cross.tex",
         "Immediate from", "Under \\xref{core-a/ass:leaf}, immediate from")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(("file", "old", "new", "fragment"), [
    (f"{CORE_A}/claims/rem-tight.tex", "[[thm:bound]]", "[[thm:gone]]",
     "summary link [[thm:gone]] names no claim"),
    (f"{CORE_A}/claims/thm-bound.tex", "[[def:object]]", "[[core-b/def:object]]",
     "summary link [[core-b/def:object]] names no claim"),
    ("spec/modules/core-b/claims/prop-cross.tex", "[[A-LEAF]]", "[[A-NONE]]",
     "summary link [[A-NONE]] names no assumption short id"),
    (f"{CORE_A}/module.yaml", "[[core-b/prop:cross]]", "[[prop:cross]]",
     "abstract link [[prop:cross]] names no claim"),
    (f"{CORE_A}/module.yaml", "which is\n      [[thm:bound]]", "which is [[thm:none]]",
     "reading_groups abstract link [[thm:none]] names no claim"),
    (f"{CORE_A}/sub-x/module.yaml", "[[core-a/def:object]]", "[[core-b/def:object]]",
     "abstract link [[core-b/def:object]] names no claim"),
])
def test_a_link_that_resolves_to_nothing_is_refused(
    tmp_path: Path, file: str, old: str, new: str, fragment: str,
):
    repo = format_copy(tmp_path)
    edit(repo, file, old, new)
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert fragment in result.stdout, result.stdout


def test_a_bare_link_is_read_in_its_contract(tmp_path: Path):
    r"""A submodule's field reaches a core claim by its label, as a \ref does."""
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/sub-x/module.yaml", "[[core-a/def:object]]",
         "[[def:object]]")
    edit(repo, f"{CORE_A}/sub-x/claims/lem-helper.tex", "when y ≤ 1.",
         "when y ≤ 1, a step towards [[thm:bound]].")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr
    # but not into another contract
    edit(repo, "spec/modules/core-b/module.yaml", "[[core-a/thm:bound]]",
         "[[thm:bound]]")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "abstract link [[thm:bound]] names no claim" in result.stdout


def test_a_label_is_unique_in_its_contract_not_across_contracts(tmp_path: Path):
    repo = format_copy(tmp_path)
    # The submodule belongs to core-a's contract: a second eq:object clashes.
    edit(repo, f"{CORE_A}/sub-x/claims/lem-helper.tex", "$x \\ge 0$.\n",
         "$x \\ge 0$.\n\\begin{equation}\\label{eq:object}x \\ge 0\\end{equation}\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert ("\\label{eq:object} is already defined by 'core-a/def:object' in the "
            "contract of core-a") in result.stdout
    # The same label in another contract is a different label.
    repo = format_copy(tmp_path / "other")
    edit(repo, "spec/modules/core-b/claims/prop-cross.tex", "$x \\le 1$, by",
         "\\begin{equation}\\label{eq:object}x \\le 1\\end{equation} by")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


def test_cref_is_refused_because_cleveref_is_not_loaded(tmp_path: Path):
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/claims/rem-tight.tex", "Theorem~\\ref{thm:bound}",
         "\\cref{thm:bound}")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "\\cref is not available (cleveref is not loaded)" in result.stdout


@pytest.mark.parametrize(("file", "old", "new", "fragment"), [
    ("claims/thm-bound.tex", "satisfies $x \\le 1$", "satisfies \\term{the cap}",
     "\\term{the cap} marks a defined phrase and belongs inside a definition"),
    ("claims/def-object.tex", "\\begin{definition}",
     "A lead-in naming a \\term{pair}.\n\n\\begin{definition}",
     "\\term{pair} marks a defined phrase and belongs inside a definition"),
])
def test_term_belongs_inside_a_definition(tmp_path: Path, file: str, old: str,
                                          new: str, fragment: str):
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/{file}", old, new)
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert fragment in result.stdout, result.stdout


def test_a_term_is_defined_once_per_contract(tmp_path: Path):
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/claims/def-object.tex", "as in \\cite",
         "a \\term{Base  Object} again, as in \\cite")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert ("\\term{Base  Object} is already defined by this claim in the "
            "contract of core-a") in result.stdout


@pytest.mark.parametrize(("argument", "fragment"), [
    ("docs/missing.md", "names no file of the repository"),
    ("reports/old.md", "points into reports/, which a contract never cites"),
    ("docs/../refs/index.json", "must be a repository-relative path"),
    ("docs/guide.md#a b", "has an anchor with characters outside"),
])
def test_a_repodoc_must_name_a_citable_file(tmp_path: Path, argument: str,
                                            fragment: str):
    repo = format_copy(tmp_path)
    (repo / "reports").mkdir()
    (repo / "reports/old.md").write_text("history\n", "utf-8")
    edit(repo, "spec/modules/core-b/claims/prop-cross.tex",
         "\\repodoc{docs/guide.md#usage}", f"\\repodoc{{{argument}}}")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert fragment in result.stdout, result.stdout


def test_the_assumption_closure_is_one_walk_for_the_query_and_the_table():
    """`--assumptions` and the claim-closure table share `assumption_closure`."""
    script = (
        "from pathlib import Path\n"
        "from certiqs_key.domain.claim_closure import CLAIM_ROOTS\n"
        "from harness.check_claims import load_repo, assumption_closure\n"
        "from harness.generate_claim_closure import root_closure\n"
        "repo = load_repo(Path('.'))\n"
        "for root in CLAIM_ROOTS:\n"
        "    table = root_closure(repo, root)['assumptions']\n"
        "    walk = assumption_closure(repo, root)\n"
        "    assert list(table) == list(walk), root\n"
        "    assert all(table[s] == repo.assumptions[s].claim_id for s in walk)\n"
        "print('same', len(CLAIM_ROOTS))\n")
    result = subprocess.run([sys.executable, "-c", script], cwd=REPO_ROOT,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith("same")


# --- the assumption header fields -------------

LEAF = f"{CORE_A}/claims/ass-leaf.tex"
BOUND = f"{CORE_A}/claims/thm-bound.tex"
CROSS = "spec/modules/core-b/claims/prop-cross.tex"
#: The required assumption fields as the `format` fixture's A-LEAF carries them.
LEAF_HEADER = ("% category: source\n"
               "% affects: [secrecy]\n"
               "% user_statement: Every pair you declare has a nonnegative second "
               "coordinate.\n")
LEAF_FIELDS = ("% category: channel-and-adversary\n"
               "% affects: [secrecy, correctness]\n"
               "% user_statement: >-\n"
               "%   Every pair you declare has a nonnegative second coordinate; see\n"
               "%   [[thm:bound]].\n")
TWIN_FIELDS = ("% category: numerical-trust\n"
               "% affects: [completeness]\n"
               "% user_statement: Every pair you declare has a first coordinate of "
               "at most one.\n")


def set_field(repo: Path, relative: str, line: str) -> None:
    """Set one header field of a fixture claim: replace its line, else add it."""
    name = line[2:].split(":", 1)[0]
    path = repo / relative
    text = path.read_text("utf-8")
    pattern = re.compile(rf"^% {re.escape(name)}:.*\n", re.MULTILINE)
    if pattern.search(text):
        text = pattern.sub(lambda _match: line, text, count=1)
    else:
        assert "% lean:\n" in text, relative
        text = text.replace("% lean:\n", line + "% lean:\n", 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def add_assumption(repo: Path, slug: str, short_id: str, extra: str = "", *,
                   fields: str = TWIN_FIELDS, mentions: str = "",
                   statement: str = "Every pair $(x, y)$ has $x \\le 1$.",
                   declared: bool = True) -> None:
    """Add a second assumption to core-a, after ass:leaf in its order.

    It carries the required fields (``fields``) and, when ``declared``,
    thm:bound declares it, so that it is used.
    """
    (repo / CORE_A / "claims" / f"ass-{slug}.tex").write_text(
        "% ---\n"
        f"% id: core-a/ass:{slug}\n"
        "% kind: ass\n"
        f"% title: Bounded first coordinate {slug}\n"
        "% summary: The first coordinate of every pair is at most one.\n"
        "% prominence: standard\n"
        "% status: accepted\n"
        "% uses: []\n"
        + (f"% mentions: [{mentions}]\n" if mentions else "") +
        "% assumes: []\n"
        "% refs: []\n"
        "% provenance: newly-derived\n"
        f"% short_id: {short_id}\n"
        "% verification: never\n"
        + fields + extra +
        "% lean:\n"
        "% ---\n\n"
        f"\\begin{{assumption}}\\label{{ass:{slug}}}\n"
        f"{statement}\n"
        "\\end{assumption}\n", encoding="utf-8", newline="\n")
    edit(repo, f"{CORE_A}/module.yaml", "  - ass:leaf\n",
         f"  - ass:leaf\n  - ass:{slug}\n")
    if declared:
        edit(repo, BOUND, "% assumes: [A-LEAF", f"% assumes: [A-LEAF, {short_id}")


def test_the_assumption_fields_are_accepted_on_an_assumption(tmp_path: Path):
    repo = format_copy(tmp_path)
    edit(repo, LEAF, LEAF_HEADER, LEAF_FIELDS)
    add_assumption(repo, "twin", "A-TWIN", "% refines: A-LEAF\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


ASSUMPTION_FIELD_CASES = [
    ("% category: weather\n", "category 'weather' is not one of source, receiver"),
    ("% category: round-structure\n", "category 'round-structure' is not one of"),
    ("% category: supplied-reduction\n", "category 'supplied-reduction' is not one of"),
    ("% affects: []\n", "affects must be a non-empty list"),
    ("% affects: secrecy\n", "affects must be a non-empty list"),
    ("% affects: [secrecy, liveness]\n", "affects 'liveness' is not one of secrecy, "
     "correctness, completeness"),
    ("% affects: [secrecy, secrecy]\n", "affects lists 'secrecy' twice"),
    ("% refines: leaf\n", "refines 'leaf' is not an assumption short id"),
    ("% refines: A-NONE\n", "refines: 'A-NONE' names no assumption"),
    ("% refines: A-LEAF\n", "refines: A-LEAF refines itself"),
    ("% user_statement: The pair is $(x, y)$.\n",
     "user_statement must be plain text (no backslash or dollar sign)"),
    ("% user_statement: The pair obeys \\le.\n",
     "user_statement must be plain text (no backslash or dollar sign)"),
    ("% user_statement: The pair is in units of \N{PLANCK CONSTANT OVER TWO PI}.\n",
     "user_statement carries U+210F, outside the mapped Unicode set"),
    ("% user_statement: " + "word " * 181 + "\n",
     "user_statement has 904 characters as rendered (at most 900)"),
    ("% user_statement: As [[thm:gone]] says.\n",
     "user_statement link [[thm:gone]] names no claim"),
]


@pytest.mark.parametrize(("field", "fragment"), ASSUMPTION_FIELD_CASES,
                         ids=["category", "category-retired-round",
                              "category-retired-reduction", "affects-empty",
                              "affects-scalar",
                              "affects-unknown", "affects-repeat", "refines-form",
                              "refines-unknown", "refines-self", "reading-dollar",
                              "reading-backslash", "reading-unicode",
                              "reading-length", "reading-link"])
def test_a_wrong_assumption_field_is_refused(tmp_path: Path, field: str,
                                             fragment: str):
    """category, affects, refines and user_statement feed the key-rate report.

    A value outside the vocabulary, a family that names nothing or itself, or
    a reading with TeX in it would surface as a broken report instead.
    """
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, field)
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert fragment in result.stdout, result.stdout


@pytest.mark.parametrize("category", ["protocol-structure", "supplied-artefact"])
def test_the_renamed_categories_are_accepted(tmp_path: Path, category: str):
    """The assumption categories under their current names.

    `round-structure` became `protocol-structure` (A-SPEC and A-FIXED describe
    the protocol as a whole) and `supplied-reduction` became
    `supplied-artefact` (A-RECV is a receiver artefact, not a reduction).
    """
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, f"% category: {category}\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_definition_assumes_nothing(tmp_path: Path):
    """A definition asserts nothing that could be false (spec/style.md section 2).

    Eighteen definitions declared premises, and four assumptions reached
    themselves through one (A-DECL through meat-core's def:declaration); the
    premise belongs on the claims that consume it.
    """
    repo = format_copy(tmp_path)
    edit(repo, f"{CORE_A}/claims/def-object.tex", "% assumes: []\n",
         "% assumes: [A-LEAF]\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "def-object.tex" in result.stdout
    assert "leaves: a definition's assumes list must be empty" in result.stdout, \
        result.stdout


def test_a_refines_cycle_is_refused(tmp_path: Path):
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, "% refines: A-TWIN\n")
    add_assumption(repo, "twin", "A-TWIN", "% refines: A-LEAF\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "refines: cycle A-LEAF -> A-TWIN -> A-LEAF" in result.stdout, result.stdout
    assert "refines: cycle A-TWIN -> A-LEAF -> A-TWIN" in result.stdout


@pytest.mark.parametrize("field", ["category: source", "affects: [secrecy]",
                                   "refines: A-LEAF", "presupposes: [sends]"])
def test_the_assumption_fields_are_refused_on_other_kinds(tmp_path: Path, field: str):
    repo = format_copy(tmp_path)
    edit(repo, BOUND, "% lean:\n", f"% {field}\n% lean:\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    name = field.split(":", 1)[0]
    assert f"header: {name} is for assumptions only" in result.stdout, result.stdout


# --- the roles an assumption's text presupposes

def test_the_laboratory_category_is_accepted(tmp_path: Path):
    """A party's laboratory and its boundary: a category of its own, after receiver."""
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, "% category: laboratory\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


PRESUPPOSES_CASES = [
    ("% presupposes: [sender]\n",
     "presupposes 'sender' is not one of trusted-source, sends, setting, letters"),
    ("% presupposes: setting\n", "presupposes must be a list drawn from"),
    ("% presupposes: [setting, setting]\n", "presupposes lists 'setting' twice"),
]


@pytest.mark.parametrize(("field", "fragment"), PRESUPPOSES_CASES,
                         ids=["unknown", "scalar", "repeat"])
def test_a_wrong_presupposes_is_refused(tmp_path: Path, field: str, fragment: str):
    """A run-tier guard reads these values; one outside the vocabulary is refused."""
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, field)
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert fragment in result.stdout, result.stdout


def test_a_valid_presupposes_is_accepted(tmp_path: Path):
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, "% presupposes: [trusted-source, sends, setting, letters]\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


#: A user_statement naming the sender's laser, unconditioned.
LASER = "% user_statement: Her laser fixes every pair you declare.\n"


def test_a_role_word_without_presupposes_is_refused(tmp_path: Path):
    """A role word such as "her laser" on a run with no sender is refused.

    The finding stands at the field's line and names the field, the
    sentence, the role word and both remedies.
    """
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, LASER)
    result = check("--repo", str(repo))
    assert result.returncode == 1
    found = [line for line in result.stdout.splitlines() if "presupposes:" in line]
    assert len(found) == 1, result.stdout
    line = found[0]
    assert line.startswith(f"{LEAF}:16: presupposes: the user_statement sentence "
                           "\"Her laser fixes every pair you declare.\" uses the "
                           "sender word 'laser' unconditioned"), line
    assert "declare presupposes: [sends or trusted-source]" in line, line
    assert "or condition the sentence (where, if, when" in line, line


@pytest.mark.parametrize("role", ["sends", "trusted-source"])
def test_a_role_word_with_a_satisfying_presupposes_passes(tmp_path: Path, role: str):
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, LASER)
    set_field(repo, LEAF, f"% presupposes: [{role}]\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_presupposes_of_another_group_does_not_satisfy(tmp_path: Path):
    """A private setting says nothing about a sender."""
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, LASER)
    set_field(repo, LEAF, "% presupposes: [setting]\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "uses the sender word 'laser'" in result.stdout, result.stdout


@pytest.mark.parametrize("sentence", [
    "Where you declare a pair, her laser fixes it.",
    "If you declare a pair, her laser fixes it.",
    "Her laser fixes a pair when you declare one.",
    "Her laser fixes every pair, unless you declare none.",
    "A pair whose value her laser fixes is declared.",
    "With a trusted source, her laser fixes every pair.",
    "In trusted-source mode her laser fixes every pair.",
])
def test_a_conditioned_role_word_passes(tmp_path: Path, sentence: str):
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, f"% user_statement: {sentence}\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_condition_reaches_only_its_own_sentence(tmp_path: Path):
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, "% user_statement: Her laser fixes every pair. Where you "
                          "declare one, it is nonnegative.\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert "sentence \"Her laser fixes every pair.\"" in result.stdout, result.stdout


def test_the_title_is_one_sentence_under_the_rule(tmp_path: Path):
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, "% title: Pairs fixed by Bob's private setting\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert (f"{LEAF}:4: presupposes: the title sentence \"Pairs fixed by Bob's "
            "private setting\" uses the setting word 'private setting'"
            in result.stdout), result.stdout
    assert "declare presupposes: [setting]" in result.stdout
    set_field(repo, LEAF, "% presupposes: [setting]\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("text", [
    "The implementation sends no message beyond the model's.",
    "Each detector emits no light that depends on its outcome.",
    "The probe settings of your receiver are fixed before the run.",
    "This holds in a prepare-and-measure setup as declared.",
])
def test_the_words_left_out_of_the_role_lists_pass(tmp_path: Path, text: str):
    """The words left out of ``ROLE_WORDS`` name no party's role.

    Public messages, a device's emissions, the receiver's probe declaration
    and the protocol class.
    """
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, f"% user_statement: {text}\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_role_rule_reads_assumptions_only(tmp_path: Path):
    repo = format_copy(tmp_path)
    edit(repo, BOUND, "% lean:\n",
         "% user_statement: Her laser fixes every pair you declare.\n% lean:\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


# --- a user_statement on other kinds ----------

COROLLARY = f"{CORE_A}/claims/cor-twice.tex"


def add_corollary(repo: Path) -> None:
    """Add a corollary of thm:bound to core-a, after rem:tight in its order."""
    (repo / COROLLARY).write_text(
        "% ---\n"
        "% id: core-a/cor:twice\n"
        "% kind: cor\n"
        "% title: Bound on twice the first coordinate\n"
        "% summary: Twice the first coordinate is at most two.\n"
        "% prominence: standard\n"
        "% status: accepted\n"
        "% uses: [thm:bound]\n"
        "% assumes: [A-LEAF]\n"
        "% refs: []\n"
        "% provenance: newly-derived\n"
        "% lean:\n"
        "% ---\n\n"
        "\\begin{corollary}\\label{cor:twice}\n"
        "Every base object has $2x \\le 2$.\n"
        "\\end{corollary}\n\n"
        "\\begin{proof}\nDouble Theorem~\\ref{thm:bound}.\n\\end{proof}\n",
        encoding="utf-8", newline="\n")
    edit(repo, f"{CORE_A}/module.yaml", "  - rem:tight\n",
         "  - rem:tight\n  - cor:twice\n")


#: A claim of each kind but an assumption and a definition, in the fixture.
READING_TARGETS = {
    "thm": BOUND,
    "cor": COROLLARY,
    "lem": f"{CORE_A}/sub-x/claims/lem-helper.tex",
    "prop": CROSS,
    "rem": f"{CORE_A}/claims/rem-tight.tex",
    "req": f"{CORE_A}/claims/req-refuse.tex",
}


@pytest.mark.parametrize("kind", sorted(READING_TARGETS))
def test_a_user_statement_is_accepted_on_a_result_remark_or_requirement(
    tmp_path: Path, kind: str
):
    """The key-rate report reads its security statement through these readings.

    A plain reading for a user who is not a proof expert lives with the claim
    it reads, so a result may carry one; it is optional there, and its links
    resolve like a summary's.
    """
    repo = format_copy(tmp_path)
    add_corollary(repo)
    set_field(repo, READING_TARGETS[kind],
              "% user_statement: >-\n"
              "%   Your first coordinate never exceeds one, as long as\n"
              "%   [[A-LEAF]] holds; [[core-a/thm:bound]] is the statement.\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_user_statement_is_refused_on_a_definition(tmp_path: Path):
    """A definition asserts nothing a user relies on, so it has no reading."""
    repo = format_copy(tmp_path)
    set_field(repo, f"{CORE_A}/claims/def-object.tex",
              "% user_statement: A base object is a pair.\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert ("header: a definition carries no user_statement" in result.stdout), \
        result.stdout


@pytest.mark.parametrize(("field", "fragment"), [
    ("% user_statement: The bound is $x \\le 1$.\n",
     "user_statement must be plain text (no backslash or dollar sign)"),
    ("% user_statement: " + "word " * 181 + "\n",
     "user_statement has 904 characters as rendered (at most 900)"),
    ("% user_statement: As [[thm:gone]] says.\n",
     "user_statement link [[thm:gone]] names no claim"),
], ids=["reading-dollar", "reading-length", "reading-link"])
def test_a_result_user_statement_obeys_the_rules_of_an_assumption_one(
    tmp_path: Path, field: str, fragment: str
):
    """The plain-text rules and the length limit hold wherever a reading stands."""
    repo = format_copy(tmp_path)
    set_field(repo, BOUND, field)
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert fragment in result.stdout, result.stdout


# --- the checks on assumption fields ---------


@pytest.mark.parametrize("name", ["category", "affects", "user_statement"])
def test_the_assumption_fields_are_required(tmp_path: Path, name: str):
    """B8-1: the key-rate report is built from these three fields.

    An assumption without them would render a blank row. `refines` is
    optional, and the clean fixture carries none.
    """
    repo = format_copy(tmp_path)
    line = next(text for text in LEAF_HEADER.splitlines(keepends=True)
                if text.startswith(f"% {name}:"))
    edit(repo, LEAF, line, "")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert (f"ass-leaf.tex:1: header: an assumption requires {name} "
            "(spec/claim-format.md section 3)") in result.stdout, result.stdout


BODY_CASES = [
    ("statement", "has $y \\ge 0$.",
     "has $y \\ge 0$, as Theorem~\\ref{thm:bound} and \\xref{core-b/prop:cross} need."),
    ("lead-in", "\\begin{assumption}",
     "Theorem~\\ref{thm:bound} and \\xref{core-b/prop:cross} rest on this.\n\n"
     "\\begin{assumption}"),
]


@pytest.mark.parametrize(("where", "old", "new"), BODY_CASES,
                         ids=[case[0] for case in BODY_CASES])
def test_an_assumption_body_references_only_definitions(
    tmp_path: Path, where: str, old: str, new: str,
):
    """B8-2: the condition is checkable without its consumers (decision 4).

    Assumptions listed their consumers and pointed at theorems (26 references
    in five assumptions), so editing a consumer changed what the assumption
    appeared to say. The lead-in is covered as well as the statement.
    """
    repo = format_copy(tmp_path)
    clean = check("--repo", str(repo))
    assert "assumption body:" not in clean.stdout
    edit(repo, LEAF, "% assumes: []\n",
         "% mentions: [thm:bound, core-b/prop:cross]\n% assumes: []\n")
    edit(repo, LEAF, old, new)
    result = check("--repo", str(repo))
    assert result.returncode == 1, where
    assert ("assumption body: references \\ref{thm:bound}, a theorem "
            "('core-a/thm:bound'); an assumption's body references only "
            "definitions and the assumption it refines") in result.stdout, result.stdout
    assert ("assumption body: references \\xref{core-b/prop:cross}, a proposition "
            "('core-b/prop:cross')") in result.stdout, result.stdout
    assert "def:object" not in result.stdout     # a definition is always allowed


@pytest.mark.parametrize("refines", [True, False], ids=["parent", "sibling"])
def test_an_assumption_body_may_reference_only_the_assumption_it_refines(
    tmp_path: Path, refines: bool,
):
    repo = format_copy(tmp_path)
    add_assumption(repo, "twin", "A-TWIN",
                   "% refines: A-LEAF\n" if refines else "", mentions="ass:leaf",
                   statement="Every pair of Assumption~\\ref{ass:leaf} has $x \\le 1$.")
    result = check("--repo", str(repo))
    message = ("assumption body: references \\ref{ass:leaf}, an assumption "
               "('core-a/ass:leaf')")
    if refines:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode == 1
        assert message in result.stdout, result.stdout


def affects_findings(repo: Path, roots: dict[str, list[str]]) -> list[str]:
    """Return what ``check_affects`` reports on ``repo`` for the given roots."""
    script = (
        "import json, sys\nfrom pathlib import Path\n"
        "from harness import check_claims\n"
        "repo = check_claims.load_repo(Path(sys.argv[1]))\n"
        "before = len(repo.errors)\n"
        "check_claims.check_affects(repo, json.loads(sys.argv[2]))\n"
        "for error in repo.errors[before:]:\n"
        "    print(error.render())\n")
    result = subprocess.run(
        [sys.executable, "-c", script, str(repo), json.dumps(roots)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.splitlines()


AFFECTS_CASES = [
    # (affects of A-LEAF, roots, the finding or None); A-LEAF is in the
    # assumption closures of core-a/thm:bound and core-b/prop:cross.
    ("[secrecy]", {"secrecy": ["core-a/thm:bound"]}, None),
    ("[correctness, completeness]", {"secrecy": ["core-a/thm:bound"]},
     "affects: A-LEAF is in the assumption closure of the secrecy root "
     "'core-a/thm:bound', so its failure puts secrecy at stake; affects lists "
     "completeness, correctness"),
    ("[secrecy]", {"correctness": ["core-b/prop:cross"]},
     "affects: A-LEAF is in the assumption closure of the correctness root "
     "'core-b/prop:cross', so its failure puts correctness at stake; affects "
     "lists secrecy"),
    ("[correctness]", {"composition": ["core-a/thm:bound"]}, None),
    ("[completeness]", {"composition": ["core-a/thm:bound"]},
     "affects: A-LEAF is in the assumption closure of the composition root "
     "'core-a/thm:bound', so its failure puts secrecy or correctness at stake; "
     "affects lists completeness"),
    ("[completeness]", {"secrecy": ["core-a/def:object"],
                        "correctness": ["core-a/sub-x/lem:helper"],
                        "composition": ["core-a/req:refuse"]}, None),
    ("[secrecy]", {"secrecy": ["core-a/thm:gone"]},
     "src/certiqs_key/domain/claim_closure.py:1: affects: the secrecy root "
     "'core-a/thm:gone' of certiqs_key.domain.claim_closure names no claim"),
    ("[secrecy]", {"secrecy": ["meat-core/thm:keylength"]}, None),
]


@pytest.mark.parametrize(("affects", "roots", "finding"), AFFECTS_CASES,
                         ids=["secrecy-listed", "secrecy-missing",
                              "correctness-missing", "composition-one-of-two",
                              "completeness-only-in-composition",
                              "outside-every-closure", "root-renamed",
                              "root-module-absent"])
def test_affects_agrees_with_the_claim_graph(
    tmp_path: Path, affects: str, roots: dict[str, list[str]], finding: str | None,
):
    """B8-3: where the claim graph says what is at stake, affects says so too.

    `affects` is hand-written; a disagreement would print a wrong "at stake"
    line in every report. Only that direction is checked (a device premise
    reaches the key length through the run's route, not through claim edges),
    and a root that names no claim in a module of the tree is an error rather
    than a check silently switched off.
    """
    repo = format_copy(tmp_path)
    set_field(repo, LEAF, f"% affects: {affects}\n")
    findings = affects_findings(repo, roots)
    if finding is None:
        assert findings == []
    else:
        assert len(findings) == 1, findings
        assert finding in findings[0], findings


def test_the_affects_roots_are_the_run_records_roots():
    """One declaration of the three roots, read by the run record and the check."""
    script = (
        "from certiqs_key.domain import claim_closure as c\n"
        "from harness.check_claims import affects_roots\n"
        "assert affects_roots() == {'secrecy': c.SECRECY_ROOTS, "
        "'correctness': c.CORRECTNESS_ROOTS, 'composition': c.COMPOSITION_ROOTS}\n"
        "print('same')\n")
    result = subprocess.run([sys.executable, "-c", script], cwd=REPO_ROOT,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


def test_an_unused_assumption_is_refused(tmp_path: Path):
    """B8-5: an undeclared assumption is in no closure and no report.

    It would still read as a premise in the contract. A `uses` edge to it does
    not count: the closure walks `assumes`.
    """
    repo = format_copy(tmp_path)
    assert "unused assumption" not in check("--repo", str(repo)).stdout
    edit(repo, BOUND, "% assumes: [A-LEAF]\n", "% assumes: []\n")
    edit(repo, CROSS, "% assumes: [A-LEAF]\n", "% assumes: []\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert ("ass-leaf.tex:12: unused assumption: no claim declares A-LEAF in "
            "assumes, and no used assumption refines it") in result.stdout, \
        result.stdout


def test_a_superseded_assumption_may_be_unused(tmp_path: Path):
    """A superseded assumption belongs in no closure."""
    repo = format_copy(tmp_path)
    edit(repo, BOUND, "% assumes: [A-LEAF]\n", "% assumes: []\n")
    edit(repo, CROSS, "% assumes: [A-LEAF]\n", "% assumes: []\n")
    edit(repo, LEAF, "% status: accepted\n", "% status: superseded\n")
    assert "unused assumption" not in check("--repo", str(repo)).stdout


@pytest.mark.parametrize("declared", [True, False], ids=["member-used",
                                                          "member-unused"])
def test_a_family_parent_is_used_through_a_used_member(tmp_path: Path,
                                                       declared: bool):
    repo = format_copy(tmp_path)
    add_assumption(repo, "twin", "A-TWIN", "% refines: A-LEAF\n", declared=declared)
    edit(repo, CROSS, "% assumes: [A-LEAF]\n", "% assumes: []\n")
    if declared:
        edit(repo, BOUND, "% assumes: [A-LEAF, A-TWIN]\n", "% assumes: [A-TWIN]\n")
    else:
        edit(repo, BOUND, "% assumes: [A-LEAF]\n", "% assumes: []\n")
    stdout = check("--repo", str(repo)).stdout
    unused = sorted(re.findall(r"no claim declares (A-[A-Z]+)", stdout))
    assert unused == ([] if declared else ["A-LEAF", "A-TWIN"]), stdout


@pytest.mark.parametrize("flag", ["--dependents", "--effective", "--assumptions"])
def test_a_query_accepts_an_assumption_short_id(flag: str):
    by_id = check("--repo", GOOD, flag, "core-a/ass:leaf")
    by_short = check("--repo", GOOD, flag, "A-LEAF")
    assert by_short.returncode == 0, by_short.stdout + by_short.stderr
    assert by_short.stdout == by_id.stdout
    assert "core-a/ass:leaf" in by_short.stdout


def test_a_query_with_an_unknown_short_id_fails():
    result = check("--repo", GOOD, "--dependents", "A-NONE")
    assert result.returncode == 1
    assert "'A-NONE' is not a claim id or an assumption short id" in result.stderr
