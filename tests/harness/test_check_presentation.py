"""Tests for harness/check_presentation.py (run by every ``check_claims``).

Motivation: the presentation rules exist so that the contracts stay readable
(spec/claim-format.md marks each one). Each test breaks one rule in a copy of
the conforming ``format`` fixture and asserts that ``check_claims`` reports
exactly that rule and exits 1. A rule that never fired would check nothing; one
that fired for another rule's defect would send the writer to the wrong place.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FORMAT = Path(__file__).resolve().parent / "fixtures" / "format"
A = "spec/modules/core-a"
REM = f"{A}/claims/rem-tight.tex"
LONG = ("The bound of the theorem on the first coordinate is attained at the "
        "object whose second coordinate vanishes, and at no other object of the "
        "family, which a reader checks by inserting the defining identity and "
        "comparing both sides term by term, with nothing left over on either "
        "side and nothing assumed beyond the hypothesis that the theorem itself "
        "states.")


def check(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the checker from the repository root and capture its output."""
    return subprocess.run([sys.executable, "-m", "harness.check_claims", *args],
                          cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=False)


def edit(repo: Path, relative: str, old: str, new: str) -> None:
    """Replace one exact fragment of a fixture file, which must be there."""
    path = repo / relative
    text = path.read_text("utf-8")
    assert old in text, (relative, old)
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def rules_reported(stdout: str) -> set[str]:
    """Return the rule ids of the findings a run printed."""
    return set(re.findall(r"^\S+:\d+: presentation\[([a-z-]+)\]:", stdout, re.M))


# (rule, file, old fragment, new fragment): each breaks one rule only.
CASES = [
    ("prominence-missing", REM, "% prominence: standard\n", ""),
    ("summary-missing", REM,
     "% summary: The bound of [[thm:bound]] is attained at y = 0.\n", ""),
    ("summary-sentences", REM, "is attained at y = 0.",
     "is attained. It is attained at y = 0. Nothing else is claimed."),
    ("summary-length", REM,
     "% summary: The bound of [[thm:bound]] is attained at y = 0.",
     f"% summary: {LONG}"),
    ("title-length", REM, "title: Sharpness of the bound",
     "title: Sharpness of the bound on the first coordinate of each base object"
     " declared"),
    ("title-code", REM, "title: Sharpness of the bound", "title: 'C5: sharpness'"),
    ("title-short-id", f"{A}/claims/ass-leaf.tex",
     "title: Nonnegative second coordinate", "title: 'A-LEAF: nonnegative'"),
    ("title-plain", REM, "title: Sharpness of the bound",
     "title: \"Sharpness of the R\\\\'enyi bound\""),
    ("lead-in", f"{A}/claims/thm-bound.tex", "in one line.\n",
     "in one line:\n\\begin{equation}x = 1 - y .\\end{equation}\n"),
    ("after-statement", REM, "\\end{remark}\n", "\\end{remark}\n\nA trailing aside.\n"),
    ("statement-markup", REM, "} is attained", "} is \\textbf{attained}"),
    ("statement-code", REM, "is attained at $y = 0$.",
     "is attained at $y = 0$, as interface.yaml records."),
    ("texttt-claim-id", REM, "Theorem~\\ref{thm:bound}",
     "Theorem~\\ref{thm:bound} (\\texttt{core-a/thm:bound})"),
    ("foreign-ref", "spec/modules/core-b/claims/prop-cross.tex",
     "by \\xref{core-a/thm:bound}.", "by Theorem~\\ref{thm:bound}."),
    ("iface-outside-req", REM, "} is attained", "} is attained (\\iface{attained})"),
    ("term-gloss", f"{A}/claims/def-object.tex",
     "\\term[a pair of reals whose coordinates sum to one]{base object}",
     "\\term{base object}"),
    ("term-link", "spec/modules/core-b/claims/prop-cross.tex",
     "Every \\tref{base object} satisfies", "Every base object satisfies"),
    ("order", f"{A}/module.yaml",
     "  - thm:bound\n  - rem:tight\n  - ass:leaf\n",
     "  - rem:tight\n  - ass:leaf\n  - thm:bound\n"),
]


@pytest.mark.parametrize(("rule", "file", "old", "new"), CASES,
                         ids=[case[0] for case in CASES])
def test_each_rule_fires_alone(
    tmp_path: Path, rule: str, file: str, old: str, new: str,
):
    repo = tmp_path / "repo"
    shutil.copytree(FORMAT, repo)
    edit(repo, file, old, new)
    result = check("--repo", str(repo))
    assert result.returncode == 1, result.stdout + result.stderr
    assert rules_reported(result.stdout) == {rule}, result.stdout
    assert "presentation finding(s)" in result.stderr


def test_every_rule_has_a_case():
    script = ("from harness.check_presentation import RULES\n"
              "print(' '.join(RULES))\n")
    result = subprocess.run([sys.executable, "-c", script], cwd=REPO_ROOT,
                            capture_output=True, text=True, check=True)
    assert set(result.stdout.split()) == {case[0] for case in CASES}


def test_the_summary_counts_every_rule(tmp_path: Path):
    repo = tmp_path / "repo"
    shutil.copytree(FORMAT, repo)
    edit(repo, REM, "\\end{remark}\n", "\\end{remark}\n\nA trailing aside.\n")
    result = check("--repo", str(repo))
    rows = dict(re.findall(r"^  ([a-z-]+)\s+(\d+)\s+\d+", result.stdout, re.M))
    assert rows["after-statement"] == "1"
    assert rows["total"] == "1"
    assert rows["order"] == "0"
    assert len(rows) == len(CASES) + 1


def test_the_first_assumption_and_requirement_start_reading_groups(tmp_path: Path):
    repo = tmp_path / "repo"
    shutil.copytree(FORMAT, repo)
    edit(repo, f"{A}/module.yaml",
         "  - title: Assumptions\n    start: ass:leaf\n"
         "    abstract: The one hypothesis of the bound.\n", "")
    result = check("--repo", str(repo))
    assert "the first assumption 'ass:leaf' does not start a reading group" \
        in result.stdout
    assert rules_reported(result.stdout) == {"order"}


def test_foreign_and_ambiguous_refs(tmp_path: Path):
    """The seven wrong refs of the tree: a label that two contracts define."""
    repo = tmp_path / "repo"
    shutil.copytree(FORMAT, repo)
    cross = "spec/modules/core-b/claims/prop-cross.tex"
    edit(repo, cross, "\\begin{proposition}\\label{prop:cross}",
         "\\begin{proposition}\\label{prop:cross}\nSee \\eqref{eq:object}, and\n"
         "\\begin{equation}\\label{eq:object} x \\le 1 \\end{equation}")
    edit(repo, cross, "uses: [core-a/thm:bound]",
         "uses: [core-a/thm:bound, core-a/def:object]")
    result = check("--repo", str(repo))
    # The claim defines eq:object itself: its own label wins, nothing to report.
    assert result.returncode == 0, result.stdout + result.stderr
    # A remark of core-a that declares both twins cannot tell them apart.
    edit(repo, REM, "uses: [thm:bound]", "uses: [thm:bound, def:object]\n"
         "% mentions: [core-b/prop:cross]")
    edit(repo, REM, "is attained at $y = 0$.",
         "is attained at $y = 0$ in \\eqref{eq:object}.")
    result = check("--repo", str(repo))
    assert ("\\ref{eq:object} is ambiguous: it resolves to core-a/def:object in "
            "this contract, while the declared core-b/prop:cross") in result.stdout
    # Without its own label, the proposition's \eqref names another contract.
    edit(repo, cross, "\\begin{equation}\\label{eq:object}",
         "\\begin{equation}\\label{eq:local}")
    result = check("--repo", str(repo))
    assert ("\\ref{eq:object} names a label of core-a/def:object in another "
            "contract") in result.stdout
    assert "is ambiguous" not in result.stdout
    assert result.returncode == 1


def test_sentences_are_counted_with_abbreviations_and_numbers():
    script = (
        "from harness.check_presentation import sentence_count as n\n"
        "cases = [\n"
        "  ('One sentence without a stop', 1),\n"
        "  ('The rate, cf. Eq. 3, is 0.5 bits. It is tight.', 2),\n"
        "  ('A bound (Thm. 2) holds, e.g. for alpha. So does its limit!', 2),\n"
        "  ('First. Second. Third.', 3),\n"
        "  ('It ends with a quotation: \"done.\" Then more.', 2),\n"
        "  ('The value of x. is odd', 1),\n"
        "]\n"
        "print(all(n(text) == want for text, want in cases),\n"
        "      [n(text) for text, _ in cases])\n")
    result = subprocess.run([sys.executable, "-c", script], cwd=REPO_ROOT,
                            capture_output=True, text=True, check=True)
    assert result.stdout.startswith("True"), result.stdout


PLAIN_TITLES = [
    # (authored title, plain title, TeX the flattening cannot render)
    (r"Exact evaluation of $\varepsilon^{\star}$ and its report",
     "Exact evaluation of \N{GREEK SMALL LETTER EPSILON}^* and its report", []),
    (r"Demanded only at $d_A\ge2$",
     "Demanded only at d_A\N{GREATER-THAN OR EQUAL TO}2", []),
    (r"The minimum defining $r_{\min}$ and $\log x$",
     "The minimum defining r_min and log x", []),
    (r"A rate $\mathrm{fl}(x)\,\le\,1$", "A rate fl(x) \N{LESS-THAN OR EQUAL TO} 1",
     []),
    ("Sandwiched R\N{LATIN SMALL LETTER E WITH ACUTE}nyi divergence",
     "Sandwiched R\N{LATIN SMALL LETTER E WITH ACUTE}nyi divergence", []),
    (r"Sandwiched R\'enyi divergence", r"Sandwiched R\'enyi divergence", [r"\'"]),
    (r"The role of $\Chatcon$", "The role of Chatcon", [r"\Chatcon"]),
    (r"\emph{Base} object", "Base object", [r"\emph"]),
]


def test_plain_titles_render_the_mapped_macros_and_name_the_rest():
    r"""The flattening behind bookmarks and graph labels (rule title-plain).

    "R\'enyi" read "R\textbackslash{}'enyi" in the foundations bookmarks,
    and "Chatcon", "varepsilon ^star" and "d_Age 2" in the statistics and
    transmitter graph indexes.
    """
    script = (
        "import json, sys\n"
        "from harness.contract_navigation import plain_title, "
        "unrenderable_title_tex\n"
        "titles = json.loads(sys.stdin.read())\n"
        "print(json.dumps([[plain_title(t), unrenderable_title_tex(t)] "
        "for t in titles]))\n")
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=REPO_ROOT, capture_output=True,
        text=True, encoding="utf-8", check=True,
        input=json.dumps([title for title, _plain, _bad in PLAIN_TITLES]))
    got = json.loads(result.stdout)
    assert got == [[plain, bad] for _title, plain, bad in PLAIN_TITLES]


def test_a_title_may_use_mapped_macros_in_its_mathematics(tmp_path: Path):
    repo = tmp_path / "repo"
    shutil.copytree(FORMAT, repo)
    edit(repo, REM, "title: Sharpness of the bound",
         r"title: 'Sharpness of the bound at $y\ge0$ and $\varepsilon\to0$'")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_real_tree_carries_no_presentation_finding():
    """The real tree stays green under every rule."""
    result = check()
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr
    assert "presentation[" not in result.stdout
