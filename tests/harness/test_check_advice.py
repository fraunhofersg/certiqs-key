"""Tests for harness/check_advice.py, run through `check_claims --advice`.

The editorial heuristics are advice, so that they present no productivity tax:
printed only on demand, never in the default run,
never changing the exit code, with no waiver list. These tests pin exactly
that, and that each heuristic fires on a copy of the `format` fixture broken
for it. The live tree is checked for the shape of the report only, never for
its counts.
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
BOUND = f"{CORE_A}/claims/thm-bound.tex"
OBJECT = f"{CORE_A}/claims/def-object.tex"
HELPER = f"{CORE_A}/sub-x/claims/lem-helper.tex"
ADVICE_LINE = re.compile(r"^spec/modules/\S+\.tex:\d+: advice\[([a-z-]+)\]: \S")
CLOSING = "advice only: nothing here blocks"
Mutation = Callable[[Path], None]


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


def advice_rules(stdout: str) -> set[str]:
    """Return the rules of the advice lines."""
    return {match.group(1) for line in stdout.splitlines()
            if (match := ADVICE_LINE.match(line))}


# --- one mutation per heuristic ----------------------------------------------

def long_statement(repo: Path) -> None:
    edit(repo, BOUND, "satisfies $x \\le 1$.\n",
         "satisfies $x \\le 1$." + " Indeed." * 401 + "\n")


def long_lead_in(repo: Path) -> None:
    edit(repo, BOUND, "identity in one line.\n",
         "identity in one line." + " It is short." * 51 + "\n")


def definition_only_mentioned(repo: Path) -> None:
    """Mention the definition the theorem's statement and proof reference."""
    edit(repo, BOUND, "% uses: [def:object, ass:leaf]\n",
         "% uses: [ass:leaf]\n% mentions: [def:object]\n")


def assumption_only_mentioned(repo: Path) -> None:
    """Name, in a proof, an assumption the header neither assumes nor uses."""
    edit(repo, HELPER, "% assumes: []\n",
         "% mentions: [core-a/ass:leaf]\n% assumes: []\n")
    edit(repo, HELPER, "By \\eqref{eq:object}.\n",
         "By \\eqref{eq:object}, whether or not Assumption~\\ref{ass:leaf} holds.\n")


def headed_paragraph(repo: Path) -> None:
    edit(repo, OBJECT, "as in \\cite", "\\emph{Scope.} The pair is real, as in \\cite")


def general_format(repo: Path) -> None:
    edit(repo, OBJECT, "as in \\cite", "in the general format, as in \\cite")


def inventory(repo: Path) -> None:
    edit(repo, BOUND, "By \\eqref{eq:object}, ",
         "By " + "\\eqref{eq:object}, " * 6)


CASES = [
    (long_statement, {"long-statement"}),
    (long_lead_in, {"long-lead-in"}),
    (definition_only_mentioned, {"statement-ref-mention", "proof-ref-mention"}),
    (assumption_only_mentioned, {"proof-ref-mention"}),
    (headed_paragraph, {"statement-heading"}),
    (general_format, {"general-format-track"}),
    (inventory, {"inventory-sentence"}),
]
CASE_IDS = ["long-statement", "long-lead-in", "mention-only-definition",
            "mention-only-assumption", "statement-heading", "general-format",
            "inventory-sentence"]


@pytest.mark.parametrize(("mutate", "rules"), CASES, ids=CASE_IDS)
def test_each_heuristic_fires_under_advice_and_exits_0(
    tmp_path: Path, mutate: Mutation, rules: set[str],
):
    repo = format_copy(tmp_path)
    mutate(repo)
    result = check("--repo", str(repo), "--advice")
    assert result.returncode == 0, result.stdout + result.stderr
    assert advice_rules(result.stdout) == rules, result.stdout
    assert CLOSING in result.stdout
    assert "ok: 7 claim(s) in 3 module(s)" in result.stdout


@pytest.mark.parametrize(("mutate", "rules"), CASES, ids=CASE_IDS)
def test_the_default_run_prints_no_advice(tmp_path: Path, mutate: Mutation,
                                          rules: set[str]):
    repo = format_copy(tmp_path)
    mutate(repo)
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "advice[" not in result.stdout + result.stderr
    assert CLOSING not in result.stdout


def test_a_missed_premise_is_named_as_one(tmp_path: Path):
    repo = format_copy(tmp_path)
    assumption_only_mentioned(repo)
    result = check("--repo", str(repo), "--advice")
    assert ("advice[proof-ref-mention]: possible missed premise: the proof "
            "references \\ref{ass:leaf}, an assumption ('core-a/ass:leaf', A-LEAF)"
            in result.stdout), result.stdout
    assert "1 name an assumption the header does not declare" in result.stdout


def test_the_clean_fixture_has_no_advice():
    result = check("--repo", str(FORMAT), "--advice")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "advice[" not in result.stdout
    assert CLOSING in result.stdout


def test_advice_leaves_a_failing_exit_code_as_it_was(tmp_path: Path):
    """Advice never sets the exit code, in either direction."""
    repo = format_copy(tmp_path)
    long_statement(repo)
    edit(repo, BOUND, "% uses: [def:object, ass:leaf]\n", "% uses: [ass:leaf]\n")
    default = check("--repo", str(repo))
    with_advice = check("--repo", str(repo), "--advice")
    assert default.returncode == 1, default.stdout + default.stderr
    assert with_advice.returncode == 1
    assert "advice[long-statement]" in with_advice.stdout


def test_rule_narrows_the_report(tmp_path: Path):
    repo = format_copy(tmp_path)
    long_statement(repo)
    long_lead_in(repo)
    result = check("--repo", str(repo), "--advice", "--rule", "long-lead-in")
    assert result.returncode == 0, result.stdout + result.stderr
    assert advice_rules(result.stdout) == {"long-lead-in"}, result.stdout


@pytest.mark.parametrize("args", [("--rule", "long-lead-in"),
                                  ("--advice", "--rule", "no-such-rule")])
def test_a_misused_rule_flag_is_a_usage_error(args: tuple[str, ...]):
    result = check("--repo", str(FORMAT), *args)
    assert result.returncode == 1
    assert result.stderr.startswith("error: --rule")


def test_the_default_run_never_imports_the_advice_module():
    probe = ("import sys; from harness.check_claims import main; "
             "code = main(['--repo', sys.argv[1]]); "
             "print(code, 'harness.check_advice' in sys.modules)")
    run = subprocess.run([sys.executable, "-c", probe, str(FORMAT)], cwd=REPO_ROOT,
                         capture_output=True, text=True, check=True)
    assert run.stdout.splitlines()[-1] == "0 False", run.stdout


def test_the_advice_module_reads_no_waiver_or_baseline_file():
    """Nothing a hit could be acknowledged in: the module opens no file."""
    source = (REPO_ROOT / "harness" / "check_advice.py").read_text("utf-8")
    code = source.split('"""', 2)[2]          # the code, past the module docstring
    for needle in ("open(", "read_text", "read_bytes", "import json", "import yaml"):
        assert needle not in code, needle


def test_the_live_tree_report_is_well_formed():
    """Shape only: counts fall as editorial passes land."""
    default = check()
    result = check("--advice")
    assert result.returncode == default.returncode
    assert "advice[" not in default.stdout
    lines = [line for line in result.stdout.splitlines() if "advice[" in line]
    assert all(ADVICE_LINE.match(line) for line in lines), lines[:5]
    assert CLOSING in result.stdout
