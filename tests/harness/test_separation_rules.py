"""Tests for the separation rules of harness/check_claims.py (check 13).

The rules keep apart what a contract asserts, what it points at and what binds
code (spec/claim-format.md sections 4.1, 4.3 and 6; the module docstring of
check_claims says why each exists). They are errors of every run. Each
test breaks one thing in a copy of the `format` fixture, which follows every
rule, and runs the default checker on it.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FORMAT = Path(__file__).resolve().parent / "fixtures" / "format"
CORE_A = "spec/modules/core-a"
CORE_B = "spec/modules/core-b"
BOUND = f"{CORE_A}/claims/thm-bound.tex"
TIGHT = f"{CORE_A}/claims/rem-tight.tex"
RULES = ("statement-ref-kind", "uses-kind", "remark-implements",
         "mention-referenced")
#: A mutation of the fixture copy, breaking one rule.
Mutation = Callable[[Path], None]
FINDING_LINE = re.compile(r"^spec/modules/\S+\.tex:\d+: separation\[([a-z-]+)\]: \S")
CLEAN = "ok: 7 claim(s) in 3 module(s)"


def check(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the checker from the repository root and capture its output."""
    return subprocess.run(
        [sys.executable, "-m", "harness.check_claims", *args],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )


def format_copy(tmp_path: Path) -> Path:
    """Return a scratch copy of the `format` fixture."""
    target = tmp_path / "repo"
    shutil.copytree(FORMAT, target)
    return target


def edit(repo: Path, relative: str, old: str, new: str) -> None:
    """Replace one exact fragment of a fixture file, which must be there."""
    path = repo / relative
    text = path.read_text("utf-8")
    assert old in text, (relative, old)
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def rules_reported(stdout: str) -> list[str]:
    """Return the rule of every finding line, in order."""
    return [match.group(1) for line in stdout.splitlines()
            if (match := FINDING_LINE.match(line))]


def assert_only_separation_errors(result: subprocess.CompletedProcess[str],
                                  rules: list[str]) -> None:
    """Assert the run failed with the given separation findings as its only errors."""
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert sorted(rules_reported(result.stdout)) == sorted(rules), output
    assert f"{len(rules)} error(s) in " in result.stderr, output
    assert "ok:" not in result.stdout, output


# --- one mutation per rule, each an error of the default run -----------------

def point_theorem_at_remark(repo: Path) -> None:
    """Point the theorem's statement at the remark it does not rest on."""
    edit(repo, BOUND, "% assumes: [A-LEAF]\n",
         "% mentions: [rem:tight]\n% assumes: [A-LEAF]\n")
    edit(repo, BOUND, "satisfies $x \\le 1$.\n",
         "satisfies $x \\le 1$ (sharp by Remark~\\ref{rem:tight}).\n")


def xref_requirement_from_proposition(repo: Path) -> None:
    r"""Point another contract's statement at a requirement through \xref."""
    path = f"{CORE_B}/claims/prop-cross.tex"
    edit(repo, path, "% assumes: [A-LEAF]\n",
         "% mentions: [core-a/req:refuse]\n% assumes: [A-LEAF]\n")
    edit(repo, path, "by \\xref{core-a/thm:bound}.\n",
         "by \\xref{core-a/thm:bound}, as \\xref{core-a/req:refuse} enforces.\n")


def definition_uses_requirement(repo: Path) -> None:
    edit(repo, f"{CORE_A}/claims/def-object.tex", "% uses: []\n",
         "% uses: [req:refuse]\n")


def lemma_uses_remark(repo: Path) -> None:
    edit(repo, f"{CORE_A}/sub-x/claims/lem-helper.tex",
         "% uses: [core-a/def:object]\n",
         "% uses: [core-a/def:object, core-a/rem:tight]\n")


def remark_carries_implements(repo: Path) -> None:
    edit(repo, TIGHT, "% lean:\n",
         "% implements: certiqs_key.core:tight_bound\n% lean:\n")


def remark_is_implemented(repo: Path) -> None:
    remark_carries_implements(repo)
    edit(repo, TIGHT, "% status: accepted\n", "% status: implemented\n")


def mention_never_referenced(repo: Path) -> None:
    """Mention a claim linked only from the summary: a link needs no entry."""
    edit(repo, BOUND, "% assumes: [A-LEAF]\n",
         "% mentions: [rem:tight]\n% assumes: [A-LEAF]\n")
    edit(repo, BOUND, "Consumers read the bound as a cap.",
         "Consumers read the bound as a cap, sharp by [[rem:tight]].")


CASES = [
    (point_theorem_at_remark, "statement-ref-kind",
     "the statement references \\ref{rem:tight}, a remark ('core-a/rem:tight'); "
     "the statement of a theorem references no remark, requirement or example"),
    (xref_requirement_from_proposition, "statement-ref-kind",
     "the statement references \\xref{core-a/req:refuse}, a requirement"),
    (definition_uses_requirement, "uses-kind",
     "uses 'core-a/req:refuse', a requirement; a definition rests on no remark"),
    (lemma_uses_remark, "uses-kind",
     "uses 'core-a/rem:tight', a remark; a lemma rests on no remark"),
    (remark_carries_implements, "remark-implements",
     "a remark carries no implements"),
    (mention_never_referenced, "mention-referenced",
     "mentions 'core-a/rem:tight', which the body never references"),
]
CASE_IDS = ["ref-to-remark", "xref-to-requirement", "definition-uses-req",
            "lemma-uses-rem", "remark-implements", "summary-link-only"]


def test_every_rule_has_a_case():
    assert {rule for _mutate, rule, _fragment in CASES} == set(RULES)


@pytest.mark.parametrize(("mutate", "rule", "fragment"), CASES, ids=CASE_IDS)
def test_each_rule_is_an_error_of_the_default_run(tmp_path: Path, mutate: Mutation,
                                                  rule: str, fragment: str):
    repo = format_copy(tmp_path)
    mutate(repo)
    result = check("--repo", str(repo))
    assert_only_separation_errors(result, [rule])
    assert f"separation[{rule}]: {fragment}" in result.stdout, result.stdout


def test_the_clean_fixture_passes():
    result = check("--repo", str(FORMAT))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "separation[" not in result.stdout + result.stderr
    assert CLEAN in result.stdout


def test_an_implemented_remark_is_reported_once(tmp_path: Path):
    """The field and the status are one fix, so one finding names both."""
    repo = format_copy(tmp_path)
    remark_is_implemented(repo)
    result = check("--repo", str(repo))
    assert_only_separation_errors(result, ["remark-implements"])
    assert "its status then tops at 'accepted'" in result.stdout


def test_an_implemented_example_is_reported(tmp_path: Path):
    repo = format_copy(tmp_path)
    (repo / CORE_A / "claims" / "ex-unit.tex").write_text(
        "% ---\n"
        "% id: core-a/ex:unit\n"
        "% kind: ex\n"
        "% title: The unit object\n"
        "% summary: The pair (1, 0) is a base object.\n"
        "% prominence: standard\n"
        "% status: implemented\n"
        "% uses: [def:object]\n"
        "% assumes: []\n"
        "% refs: []\n"
        "% provenance: newly-derived\n"
        "% implements: certiqs_key.core:unit\n"
        "% lean:\n"
        "% ---\n\n"
        "\\begin{example}\\label{ex:unit}\n"
        "The pair $(1, 0)$ satisfies \\eqref{eq:object}.\n"
        "\\end{example}\n", encoding="utf-8", newline="\n")
    edit(repo, f"{CORE_A}/module.yaml", "  - rem:tight\n",
         "  - rem:tight\n  - ex:unit\n")
    result = check("--repo", str(repo))
    assert_only_separation_errors(result, ["remark-implements"])
    assert "separation[remark-implements]: status: an example is never " \
           "'implemented'" in result.stdout, result.stdout


def test_findings_of_several_rules_are_each_an_error(tmp_path: Path):
    repo = format_copy(tmp_path)
    point_theorem_at_remark(repo)
    definition_uses_requirement(repo)
    result = check("--repo", str(repo))
    assert_only_separation_errors(result, ["statement-ref-kind", "uses-kind"])


# --- what each rule leaves alone ----------------------------------------------

def test_a_pointer_in_the_lead_in_or_the_proof_is_not_a_statement_reference(
    tmp_path: Path,
):
    repo = format_copy(tmp_path)
    edit(repo, BOUND, "% assumes: [A-LEAF]\n",
         "% mentions: [rem:tight, req:refuse]\n% assumes: [A-LEAF]\n")
    edit(repo, BOUND, "in one line.\n",
         "in one line; Remark~\\ref{rem:tight} shows it is sharp.\n")
    edit(repo, BOUND, "$x = 1 - y \\le 1$.\n",
         "$x = 1 - y \\le 1$; Requirement~\\ref{req:refuse} enforces $y \\ge 0$.\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "separation[" not in result.stdout


def test_a_remark_statement_may_point_and_a_remark_may_use_a_requirement(
    tmp_path: Path,
):
    repo = format_copy(tmp_path)
    edit(repo, TIGHT, "% uses: [thm:bound]\n", "% uses: [thm:bound, req:refuse]\n")
    edit(repo, TIGHT, "is attained at $y = 0$.\n",
         "is attained at $y = 0$, which Requirement~\\ref{req:refuse} admits.\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "separation[" not in result.stdout


def test_a_mention_referenced_through_an_equation_or_an_xref_counts(tmp_path: Path):
    repo = format_copy(tmp_path)
    # the lemma reaches the definition only through its equation label
    edit(repo, f"{CORE_A}/sub-x/claims/lem-helper.tex",
         "% uses: [core-a/def:object]\n",
         "% uses: []\n% mentions: [core-a/def:object]\n")
    edit(repo, f"{CORE_A}/sub-x/claims/lem-helper.tex",
         "of Definition~\\ref{def:object} ", "")
    path = f"{CORE_B}/claims/prop-cross.tex"
    edit(repo, path, "% assumes: [A-LEAF]\n",
         "% mentions: [core-a/def:object]\n% assumes: [A-LEAF]\n")
    edit(repo, path, "The consumer reads one coordinate;",
         "The consumer reads one coordinate of \\xref{core-a/def:object};")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "separation[" not in result.stdout


def test_the_module_filter_narrows_the_errors(tmp_path: Path):
    repo = format_copy(tmp_path)
    xref_requirement_from_proposition(repo)
    narrowed = check("--repo", str(repo), "--module", "core-a")
    assert narrowed.returncode == 0, narrowed.stdout + narrowed.stderr
    assert "separation[" not in narrowed.stdout
    wide = check("--repo", str(repo), "--module", "core-b")
    assert_only_separation_errors(wide, ["statement-ref-kind"])


# --- the finding records ------------------------------------------------------

def checker_output(script: str, *args: str) -> list[str]:
    """Return the lines a script over ``check_claims`` prints.

    Run in a subprocess, as every test here runs the checker: the tests
    package shadows ``harness`` on the import path of an in-process import.
    """
    result = subprocess.run([sys.executable, "-c", script, *args], cwd=REPO_ROOT,
                            capture_output=True, text=True, check=True)
    return result.stdout.splitlines()


def test_each_finding_is_an_error_record_naming_its_rule(tmp_path: Path):
    """``load_repo`` files a separation finding among the errors, its rule set."""
    repo = format_copy(tmp_path)
    point_theorem_at_remark(repo)
    definition_uses_requirement(repo)
    lemma_uses_remark(repo)
    remark_carries_implements(repo)
    # a second unreferenced mention, in a file the mutations above leave alone
    edit(repo, f"{CORE_B}/claims/prop-cross.tex", "% assumes: [A-LEAF]\n",
         "% mentions: [core-a/req:refuse]\n% assumes: [A-LEAF]\n")
    script = (
        "import sys\nfrom pathlib import Path\n"
        "from harness import check_claims\n"
        "repo = check_claims.load_repo(Path(sys.argv[1]))\n"
        "for error in sorted(repo.errors):\n"
        "    prefix = 'separation[' + error.rule + ']: '\n"
        "    print(error.rule or '-', error.message.startswith(prefix))\n")
    lines = checker_output(script, str(repo))
    rules = sorted(line.split()[0] for line in lines)
    assert rules == ["mention-referenced", "remark-implements",
                     "statement-ref-kind", "uses-kind", "uses-kind"], lines
    assert all(line.split()[1] == "True" for line in lines), lines


def test_the_rule_names_are_the_four_rules():
    names = checker_output("from harness import check_claims\n"
                           "for name in check_claims.SEPARATION_RULES:\n"
                           "    print(name)\n")
    assert tuple(names) == RULES


# --- the live tree --------------------------------------------------------------

def test_the_real_tree_carries_no_separation_finding():
    """The real tree stays clean under every rule."""
    result = check()
    findings = [line for line in result.stdout.splitlines() if "separation[" in line]
    assert findings == [], "\n".join(findings)
