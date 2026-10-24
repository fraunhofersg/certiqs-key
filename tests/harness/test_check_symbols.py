r"""Tests for harness/check_symbols.py.

Three fixture repositories under `fixtures/symbols/` -- a clean one, one whose
claim uses a macro nothing defines, and one whose part-A expansion has drifted
from the catalogue -- plus two runs over the real `spec/modules`. The tool is
exercised through its command line, because the exit code and the
`path:line: message` rendering are what it promises.

The clean fixture is not only a green case: it carries the three parsing rules
the tool depends on (the positional Macro/Rendered pairing of a section 3 table,
the inline `\name ($rendering$)` rule of section 3.9, and a macro whose
expansion reaches the catalogue's rendering only through another macro's
grouping braces), so a regression in any of them turns it red.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "symbols"
GOOD = str(FIXTURES / "good")
UNDEFINED = str(FIXTURES / "undefined")
MISMATCH = str(FIXTURES / "mismatch")
ERROR_LINE = re.compile(r"^\S+:\d+: \S.*$")


def check(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the checker from the repository root and capture its output."""
    return subprocess.run(
        [sys.executable, "-m", "harness.check_symbols", *args],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )


def findings(result: subprocess.CompletedProcess[str]) -> list[str]:
    """Return the `path:line: message` lines of a run."""
    return [line for line in result.stdout.splitlines() if ERROR_LINE.match(line)]


def test_good_fixture_passes():
    result = check("--repo", GOOD)
    assert result.returncode == 0, result.stdout + result.stderr
    assert findings(result) == []
    assert "ok: every macro used" in result.stdout
    assert "5 in part A" in result.stdout


def test_good_fixture_records_every_catalogue_rule():
    """The clean fixture's five part-A macros are all matched, none left over."""
    result = check("--repo", GOOD)
    assert "5 macro(s) recorded by spec/notation.md" in result.stdout
    assert "0 catalogue row(s) not comparable" in result.stdout
    assert "no catalogue row" not in result.stdout


def test_undefined_macro_is_reported():
    result = check("--repo", UNDEFINED)
    assert result.returncode == 1
    reported = findings(result)
    assert len(reported) == 1, result.stdout
    assert "def-base.tex:12" in reported[0]
    assert r"undefined macro \Nosuch (1 occurrence)" in reported[0]


def test_a_macro_named_only_in_a_comment_is_not_a_use():
    r"""`\Nevermentioned` sits in a LaTeX comment of the clean fixture's claim."""
    result = check("--repo", GOOD)
    assert "Nevermentioned" not in result.stdout


def test_expansion_mismatch_is_reported():
    result = check("--repo", MISMATCH)
    assert result.returncode == 1
    reported = findings(result)
    assert len(reported) == 1, result.stdout
    assert reported[0].startswith("spec/macros.tex:12: catalogue:")
    assert r"\Qsys expands to 'Q^{\prime}'" in reported[0]
    assert "records 'Q'" in reported[0]


def test_module_filter_selects_the_claims_reported():
    """The undefined fixture's second module is clean, so the filter decides."""
    assert check("--repo", UNDEFINED, "--module", "m").returncode == 1
    clean = check("--repo", UNDEFINED, "--module", "n")
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert "1 claim file(s) under n" in clean.stdout


def test_unknown_module_is_an_error():
    result = check("--repo", UNDEFINED, "--module", "nope")
    assert result.returncode == 1
    assert "is not a module" in result.stderr


def test_unused_is_informational_and_never_fails():
    result = check("--repo", GOOD, "--unused")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "unused in part A (catalogued notation): 1" in result.stdout
    assert "unused in part B (module-local): 1" in result.stdout
    assert r"\Spare" in result.stdout


def test_missing_repo_is_an_error():
    result = check("--repo", str(FIXTURES / "does-not-exist"))
    assert result.returncode == 1
    assert "is not a directory" in result.stderr


def test_claim_body_commands_are_allowed_and_cleveref_is_not(tmp_path: Path):
    r"""The preamble defines \xref, \term, \iface and \repodoc; it loads no cleveref."""
    import shutil

    repo = tmp_path / "repo"
    shutil.copytree(FIXTURES / "good", repo)
    claim = repo / "spec/modules/m/claims/def-base.tex"
    text = claim.read_text("utf-8")
    body = ("\n\\xref{n/def:base} \\term{a phrase} \\iface{a_key} "
            "\\repodoc{docs/a.md}\n\\begin{requirement}x\\end{requirement}\n")
    claim.write_text(text + body, encoding="utf-8", newline="\n")
    result = check("--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr
    claim.write_text(text + "\n\\cref{def:base}\n", encoding="utf-8", newline="\n")
    result = check("--repo", str(repo))
    assert result.returncode == 1
    assert r"undefined macro \cref" in result.stdout


MEANING = "| Hilbert space of the system label $A$ |"
MEANING_CASES = [
    # (new Meaning cell, the finding's fragment or None when the cell is plain)
    ("| **The** Hilbert space of $A$ |", "carries strong emphasis"),
    ("| The __Hilbert__ space of $A$ |", "carries strong emphasis"),
    ("| Hilbert space of $A$ (\N{SECTION SIGN}3.1) |", "carries a section pointer"),
    ("| Hilbert space of $A$, as in m Eq. `eq:space` |",
     "names `eq:space`, which is no claim name"),
    ("| Hilbert space of $A$, as in `m/def:base` |",
     "names `m/def:base`, which is no claim name"),
    ("| Hilbert space of $A$, as in m Def. `def:gone` |",
     "names `def:gone`, which is no claim name"),
    ("| Hilbert space of $A$, as in m Def. `def:base` |", None),
    ("| Hilbert space of $A$, as in `m` `def:base` |", None),
    ("| Hilbert space of $A$ with *emphasis* and $x^{**}$ |", None),
]


def test_a_meaning_cell_is_plain_and_names_claims_that_resolve(tmp_path: Path):
    r"""Check (d): what the contract's notation table would misprint.

    "**The** test-statistics map" printed bold in meat-core's contract, a
    "(\N{SECTION SIGN}3.11 b)" named a section the PDF does not hold, and
    `eq:feas` or a bare `foundations/req:declared-tolerance` printed as
    typewriter text instead of a link.
    """
    import shutil

    for index, (cell, fragment) in enumerate(MEANING_CASES):
        repo = tmp_path / f"repo-{index}"
        shutil.copytree(FIXTURES / "good", repo)
        notation = repo / "spec/notation.md"
        text = notation.read_text("utf-8")
        assert MEANING in text
        notation.write_text(text.replace(MEANING, cell, 1), encoding="utf-8",
                            newline="\n")
        result = subprocess.run(
            [sys.executable, "-m", "harness.check_symbols", "--repo", str(repo)],
            cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8",
            check=False)
        if fragment is None:
            assert result.returncode == 0, (cell, result.stdout + result.stderr)
        else:
            assert result.returncode == 1, cell
            lines = findings(result)
            assert len(lines) == 1 and fragment in lines[0], (cell, result.stdout)
            assert lines[0].startswith("spec/notation.md:"), lines[0]


def test_real_tree_has_no_undefined_macro():
    """Check (a) over the repository: every symbol a claim writes is defined."""
    result = check()
    undefined = [line for line in findings(result) if "undefined macro" in line]
    assert undefined == [], "\n".join(undefined)


def test_real_tree_is_clean():
    r"""Check (b) over the repository: part A is what the catalogue records.

    spec/macros.tex defines \innerp with \left/\right delimiters, and
    spec/notation.md section 3.8 records it with them. The macro keeps its
    delimiters: they auto-size, and dropping them would change how every
    contract renders \innerp over tall arguments. THE CATALOGUE CELL copies
    the expansion verbatim, which is what part A requires of it.
    """
    result = check()
    assert result.returncode == 0, result.stdout + result.stderr
