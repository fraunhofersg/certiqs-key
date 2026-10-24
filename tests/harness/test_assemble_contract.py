"""Tests for harness/assemble_contract.py.

A round trip on a module of the live tree (transmitter), the
title injection and submodule part of the passing fixture, and the staleness
check that keeps the generated contract from drifting from its claim files.
The layout itself (parts, numbering, meta lines, front and back matter) is
tested on fixtures in test_contract_layout.py.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
HAS_LATEXMK = shutil.which("latexmk") is not None
HAS_GRAPHVIZ = (shutil.which("dot") is not None
                or Path("C:/Program Files/Graphviz/bin/dot.exe").is_file())


def assemble(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the assembler from the repository root and capture its output.

    Every test passes ``--no-pdf`` unless it is about the PDF, so the suite
    does not depend on a TeX distribution.
    """
    if "--no-pdf" not in args and "--pdf-test" not in args:
        args = (*args, "--no-pdf")
    args = tuple(a for a in args if a != "--pdf-test")
    return subprocess.run(
        [sys.executable, "-m", "harness.assemble_contract", *args],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )


def staged(tmp_path: Path, source: Path, module_id: str) -> Path:
    """Copy one module into a scratch repository and return that repo root."""
    target = tmp_path / "spec" / "modules" / module_id
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    return tmp_path


def module_order(module_dir: Path) -> list[str]:
    """Return the `order` list of a module.yaml (tests never freeze a claim list)."""
    import yaml
    meta = yaml.safe_load((module_dir / "module.yaml").read_text("utf-8"))
    return list(meta["order"])


def module_title_and_version(module_dir: Path) -> tuple[str, str]:
    """Return (title, version) of a module.yaml.

    READ AND NEVER FROZEN, for the reason the claim list beside it is not
    frozen either: this test is about the ASSEMBLER, and a literal title here
    goes red whenever a module is accepted at a new version. What it asserts is
    that the assembler injects the module's OWN title and version, which is
    checkable without knowing either.
    """
    import yaml
    meta = yaml.safe_load((module_dir / "module.yaml").read_text("utf-8"))
    return str(meta["title"]), str(meta["version"])


def first_reading_group(module_dir: Path) -> tuple[str, str]:
    """Return (start label, title) of the first reading group.

    The assembler's default single group is titled "Claims" and starts at the
    first claim of the order.
    """
    import yaml
    meta = yaml.safe_load((module_dir / "module.yaml").read_text("utf-8"))
    groups = meta.get("reading_groups") or []
    if groups:
        return groups[0]["start"], groups[0]["title"]
    return meta["order"][0], "Claims"


SMOKE = "transmitter"


def test_sample_module_round_trip(tmp_path: Path):
    repo = staged(tmp_path, REPO_ROOT / f"spec/modules/{SMOKE}", SMOKE)
    result = assemble(SMOKE, "--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr

    contract = (repo / f"spec/modules/{SMOKE}/contract.tex").read_text("utf-8")
    assert contract.startswith("% GENERATED FILE -- DO NOT EDIT.")
    title, version = module_title_and_version(REPO_ROOT / f"spec/modules/{SMOKE}")
    assert f"{{\\LARGE\\bfseries {title}}}" in contract
    assert f"{{\\large Contract, version {version}}}" in contract
    # no date, else --check would rot overnight
    assert "\\today" not in contract and "\\maketitle" not in contract
    assert "\\bibliographystyle{plain}" in contract
    assert "\\bibliography{../../../refs/references}" in contract
    assert contract.rstrip().endswith("\\end{document}")

    # module.yaml: order is honoured (read from the file, so the test does not
    # freeze the module's claim list)
    order = module_order(REPO_ROOT / f"spec/modules/{SMOKE}")
    positions = [contract.index(f"\\label{{{label}}}") for label in order]
    assert positions == sorted(positions)
    assert "\n% ---\n" not in contract      # the header fence never ships
    assert "% id:" not in contract
    assert "\\begin{proof}" in contract
    assert "\\tableofcontents" in contract
    assert "\\section*{Claim index}" in contract
    assert "\\part{Mathematics}" in contract
    first = order[0]
    assert (f"\\claimbookmark{{{SMOKE}/{first}}}" in contract)
    first_start, first_title = first_reading_group(REPO_ROOT / f"spec/modules/{SMOKE}")
    assert f"\\section{{{first_title}}}\\label{{group-{SMOKE}/{first_start}}}" \
        in contract

    again = assemble(SMOKE, "--repo", str(repo), "--check")
    assert again.returncode == 0, again.stdout + again.stderr
    assert "up to date" in again.stdout


def test_check_detects_a_stale_contract(tmp_path: Path):
    repo = staged(tmp_path, REPO_ROOT / f"spec/modules/{SMOKE}", SMOKE)
    assert assemble(SMOKE, "--repo", str(repo)).returncode == 0

    first = module_order(REPO_ROOT / f"spec/modules/{SMOKE}")[0]
    claim = repo / f"spec/modules/{SMOKE}/claims/{first.replace(':', '-', 1)}.tex"
    claim.write_text(claim.read_text("utf-8") + "\n% a later edit\n", "utf-8")
    result = assemble(SMOKE, "--repo", str(repo), "--check")
    assert result.returncode == 1
    assert "stale" in result.stderr


def test_check_without_a_contract_is_stale(tmp_path: Path):
    repo = staged(tmp_path, REPO_ROOT / f"spec/modules/{SMOKE}", SMOKE)
    # the sample module ships its generated contract; the staged copy must not
    (repo / f"spec/modules/{SMOKE}/contract.tex").unlink()
    result = assemble(SMOKE, "--repo", str(repo), "--check")
    assert result.returncode == 1
    assert "does not exist" in result.stderr


def test_title_is_injected_and_submodules_get_a_part(tmp_path: Path):
    repo = staged(tmp_path, FIXTURES / "good/spec/modules/core-a", "core-a")
    result = assemble("core-a", "--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr

    contract = (repo / "spec/modules/core-a/contract.tex").read_text("utf-8")
    # thm-main.tex writes a bare \begin{theorem}; the header title fills it in.
    assert "\\begin{theorem}[Main bound]\\label{thm:main}" in contract
    assert "\\begin{definition}[Base object]" in contract
    assert "\\part{Sub X}" in contract
    assert contract.index("\\part{Sub X}") < contract.index("\\label{lem:helper}")
    assert contract.index("\\label{rem:aside}") < contract.index("\\part{Sub X}")


def test_unknown_module_fails(tmp_path: Path):
    result = assemble("core-z", "--repo", str(tmp_path))
    assert result.returncode == 1
    assert "no module.yaml" in result.stderr


# --- the review PDF (built after every revision) ----------


def test_check_reports_a_missing_pdf(tmp_path: Path):
    repo = staged(tmp_path, FIXTURES / "good/spec/modules/core-a", "core-a")
    assert assemble("core-a", "--repo", str(repo), "--no-pdf").returncode == 0
    without = assemble("core-a", "--repo", str(repo), "--check", "--no-pdf")
    assert without.returncode == 0, without.stdout + without.stderr
    result = assemble("core-a", "--repo", str(repo), "--check", "--pdf-test")
    assert result.returncode == 1
    assert "contract.pdf does not exist" in result.stderr


def test_check_reports_a_pdf_older_than_the_tex(tmp_path: Path):
    repo = staged(tmp_path, FIXTURES / "good/spec/modules/core-a", "core-a")
    assert assemble("core-a", "--repo", str(repo), "--no-pdf").returncode == 0
    module = repo / "spec/modules/core-a"
    (module / "contract.pdf").write_bytes(b"%PDF-1.4\n")
    stale_by = time.time() - 60
    os.utime(module / "contract.pdf", (stale_by, stale_by))
    result = assemble("core-a", "--repo", str(repo), "--check", "--pdf-test")
    assert result.returncode == 1
    assert "older than contract.tex" in result.stderr
    # a PDF at least as new as the tex passes (no git repository here: mtime)
    # Rendered graphs are also required now; isolate this timestamp test from
    # the renderer using stand-ins. The integration test builds real outputs.
    for dot in (module / "graphs").glob("*.dot"):
        dot.with_suffix(".svg").write_text("<svg/>", "utf-8")
    (module / "graphs/overview.pdf").write_bytes(b"%PDF-1.4\n")
    (repo / "spec/macros.tex").write_text("% test input", "utf-8")
    (repo / "refs").mkdir()
    (repo / "refs/references.bib").write_text("% test input", "utf-8")
    (module / "digest.pdf").write_bytes(b"%PDF-1.4\n")
    fresh = time.time() + 1
    os.utime(module / "contract.pdf", (fresh, fresh))
    os.utime(module / "digest.pdf", (fresh, fresh))
    result = assemble("core-a", "--repo", str(repo), "--check", "--pdf-test")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "up to date: spec/modules/core-a/contract.pdf" in result.stdout.replace(
        str(repo).replace("\\", "/") + "/", "")


@pytest.mark.skipif(not (HAS_LATEXMK and HAS_GRAPHVIZ), reason="needs latexmk/Graphviz")
def test_pdf_is_built_with_the_tex(tmp_path: Path):
    """The PDF is built and cleaned, and it prints the numbers the graphs print.

    ``contract_structure`` computes each claim's number for the graphs and the
    indexes; LaTeX computes it again for the heading. Every heading of the
    built PDF is compared with the computed number, so the two cannot drift.
    """
    repo = staged(tmp_path, REPO_ROOT / f"spec/modules/{SMOKE}", SMOKE)
    # the sample's contract inputs ../../macros and the bibliography by path
    shutil.copy(REPO_ROOT / "spec/macros.tex", repo / "spec/macros.tex")
    (repo / "refs").mkdir()
    shutil.copy(REPO_ROOT / "refs/references.bib", repo / "refs/references.bib")
    result = assemble(SMOKE, "--repo", str(repo), "--pdf-test")
    assert result.returncode == 0, result.stdout + result.stderr
    pdf = repo / f"spec/modules/{SMOKE}/contract.pdf"
    assert pdf.is_file() and pdf.read_bytes().startswith(b"%PDF")
    assert not (repo / f"spec/modules/{SMOKE}/contract.aux").exists()  # cleaned
    if shutil.which("pdftotext"):
        import re

        text = " ".join(subprocess.run(
            ["pdftotext", str(pdf), "-"], capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=True).stdout.split())
        probe = ("import sys, json; from pathlib import Path; "
                 "from harness.check_claims import load_repo; "
                 "from harness.contract_structure import contract_sections; "
                 "repo = load_repo(Path(sys.argv[1])); "
                 "print(json.dumps(contract_sections(repo, sys.argv[2]).numbers()))")
        numbers = json.loads(subprocess.run(
            [sys.executable, "-c", probe, str(repo), SMOKE], cwd=REPO_ROOT,
            capture_output=True, text=True, check=True).stdout)
        words = {"thm": "Theorem", "lem": "Lemma", "prop": "Proposition",
                 "cor": "Corollary", "def": "Definition", "ass": "Assumption",
                 "rem": "Remark", "ex": "Example", "fact": "Fact",
                 "req": "Requirement"}
        for claim_id, number in numbers.items():
            word = words[claim_id.rsplit("/", 1)[1].split(":")[0]]
            heading = re.escape(word) + r"\s+" + re.escape(number) + r"\s+[(\[]"
            assert re.search(heading, text), (claim_id, number)
    again = assemble(SMOKE, "--repo", str(repo), "--check", "--pdf-test")
    assert again.returncode == 0, again.stdout + again.stderr


def test_missing_latexmk_says_what_to_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repo = staged(tmp_path, FIXTURES / "good/spec/modules/core-a", "core-a")
    monkeypatch.setenv("PATH", str(tmp_path))   # no latexmk on this PATH
    result = assemble("core-a", "--repo", str(repo), "--pdf-test")
    assert result.returncode == 1
    assert "latexmk not found" in result.stderr
    assert (repo / "spec/modules/core-a/contract.tex").is_file()   # tex written first


def test_edge_only_change_invalidates_graphs_without_changing_claim_body(
    tmp_path: Path,
):
    """A header-only dependency repair must not leave a displayed edge stale.

    The edge shows twice: in the graphs and in
    the claim's meta line; both views follow the header.
    """
    repo = staged(tmp_path, FIXTURES / "good/spec/modules/core-a", "core-a")
    assert assemble("core-a", "--repo", str(repo)).returncode == 0
    tex = repo / "spec/modules/core-a/contract.tex"
    dot = repo / "spec/modules/core-a/graphs/claims.dot"
    original, original_dot = tex.read_text("utf-8"), dot.read_text("utf-8")
    claim = repo / "spec/modules/core-a/claims/thm-main.tex"
    claim.write_text(claim.read_text("utf-8").replace("assumes: [A-LEAF]",
                                                     "assumes: []"), "utf-8")
    result = assemble("core-a", "--repo", str(repo), "--check")
    assert result.returncode == 1
    assert "differs from its sources" in result.stderr
    assert tex.read_text("utf-8") == original            # --check writes nothing
    assert assemble("core-a", "--repo", str(repo)).returncode == 0
    assert dot.read_text("utf-8") != original_dot
    meta = tex.read_text("utf-8").split("% claim core-a/thm:main", 1)[1]
    meta = meta.split("\\claimmeta{", 1)[1].split("\\begin{proof}", 1)[0]
    assert "Assumes" not in meta
    assert "Assumes" in original.split("% claim core-a/thm:main", 1)[1].split(
        "\\begin{proof}", 1)[0]


def test_group_anchor_controls_contents_and_graph_membership(tmp_path: Path):
    repo = staged(tmp_path, FIXTURES / "good/spec/modules/core-a", "core-a")
    meta = repo / "spec/modules/core-a/module.yaml"
    meta.write_text(meta.read_text("utf-8") + "\nreading_groups:\n"
                    "  - {title: Objects, start: 'def:base'}\n"
                    "  - {title: Results, start: 'thm:main'}\n", "utf-8")
    result = assemble("core-a", "--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr
    directory = repo / "spec/modules/core-a"
    tex = (directory / "contract.tex").read_text("utf-8")
    assert tex.index("\\section{Objects}") < tex.index("\\label{def:base}")
    assert tex.index("\\section{Results}") < tex.index("\\label{thm:main}")
    assert tex.count("\\label{def:base}") == 1
    index = (directory / "graphs/README.md").read_text("utf-8")
    assert "### 1 Objects" in index and "### 2 Results" in index
    assert "#nameddest=claim-core-a/thm:main" in index
    assert (directory / "graphs/group-01-objects.dot").is_file()
    assert (directory / "graphs/group-02-results.dot").is_file()
    assert r"\label{group-core-a/thm:main}" in tex
    # the dependency matrix left the PDF; it stays in graphs/
    assert "Rows depend on columns" not in tex
    assert (directory / "graphs/overview.dot").is_file()
    # Obsolete generated group views must not look current after regrouping.
    obsolete = directory / "graphs/group-04.dot"
    obsolete.write_text("old generated group", "utf-8")
    result = assemble("core-a", "--repo", str(repo), "--check")
    assert result.returncode == 1 and "obsolete generated" in result.stderr
    assert assemble("core-a", "--repo", str(repo)).returncode == 0
    assert not obsolete.exists()
    # Renaming changes the descriptive suffix and must remove both old views.
    old_dot = directory / "graphs/group-02-results.dot"
    old_svg = old_dot.with_suffix(".svg")
    old_svg.write_text("<svg/>", "utf-8")
    meta.write_text(meta.read_text("utf-8").replace(
        "title: Results", "title: Main results"), "utf-8")
    assert assemble("core-a", "--repo", str(repo)).returncode == 0
    assert not old_dot.exists() and not old_svg.exists()
    assert (directory / "graphs/group-02-main-results.dot").is_file()


def test_claim_graph_links_raw_and_rendered_claims_across_module_boundaries(
    tmp_path: Path,
):
    repo = staged(tmp_path, FIXTURES / "good/spec/modules/core-a", "core-a")
    staged(tmp_path, FIXTURES / "good/spec/modules/core-b", "core-b")
    result = assemble("core-b", "--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr
    dot = (repo / "spec/modules/core-b/graphs/claims.dot").read_text("utf-8")
    assert "TeX source" in dot and "Rendered PDF" in dot
    assert '../../core-a/contract.pdf#nameddest=claim-core-a/def:base' in dot
    assert '../../core-a/claims/def-base.tex' in dot
    assert '../contract.pdf#nameddest=claim-core-b/' in dot


def test_module_map_comes_from_registry_and_dashes_modules_not_on_disk(tmp_path: Path):
    repo = staged(tmp_path, FIXTURES / "good/spec/modules/core-a", "core-a")
    (repo / "spec/modules.yaml").write_text(
        "cores:\n  - id: core-a\n    title: Core A\n    depends_on: [future]\n"
        "  - id: future\n    title: Future module\n    depends_on: []\n", "utf-8")
    assert assemble("core-a", "--repo", str(repo)).returncode == 0
    dot = (repo / "spec/module-graph.dot").read_text("utf-8")
    assert '"core-a" -> "future"' in dot
    assert 'style="rounded,dashed"' in dot
    assert "allowed imports, not execution order" in dot
    assert "modules/core-a/graphs/README.md" in dot


def test_navigation_titles_keep_math_without_exposing_tex_commands(tmp_path: Path):
    repo = staged(tmp_path, FIXTURES / "good/spec/modules/core-a", "core-a")
    claim = repo / "spec/modules/core-a/claims/def-base.tex"
    claim.write_text(claim.read_text("utf-8").replace(
        "title: Base object", r"title: '\emph{Base} object $x_1$'"), "utf-8")
    result = assemble("core-a", "--repo", str(repo))
    assert result.returncode == 0, result.stdout + result.stderr
    directory = repo / "spec/modules/core-a"
    tex = (directory / "contract.tex").read_text("utf-8")
    assert (r"\claimbookmark{core-a/def:base}{Definition}{def:base}"
            r"{Base object x\_1}") in tex
    assert r"\emph{Base} object $x_1$\newline" in tex          # the claim index
    dot = (directory / "graphs/claims.dot").read_text("utf-8")
    assert "Base object x_1" in dot and "emph" not in dot
    # The header title is the claim's only title: the heading prints it as TeX.
    assert r"\begin{definition}[\emph{Base} object $x_1$]\label{def:base}" in tex


@pytest.mark.skipif(not (HAS_LATEXMK and HAS_GRAPHVIZ), reason="needs latexmk/Graphviz")
def test_missing_graph_and_changed_shared_macro_make_review_copy_stale(tmp_path: Path):
    """The review bundle includes SVGs; the PDF consumes shared macros too."""
    repo = staged(tmp_path, REPO_ROOT / f"spec/modules/{SMOKE}", SMOKE)
    shutil.copy(REPO_ROOT / "spec/macros.tex", repo / "spec/macros.tex")
    (repo / "refs").mkdir()
    shutil.copy(REPO_ROOT / "refs/references.bib", repo / "refs/references.bib")
    assert assemble(SMOKE, "--repo", str(repo), "--pdf-test").returncode == 0
    svg = repo / f"spec/modules/{SMOKE}/graphs/overview.svg"
    content = svg.read_bytes()
    svg.unlink()
    result = assemble(SMOKE, "--repo", str(repo), "--check", "--pdf-test")
    assert result.returncode == 1 and "overview.svg" in result.stderr
    svg.write_bytes(content)
    macro = repo / "spec/macros.tex"
    future = time.time() + 3
    os.utime(macro, (future, future))
    result = assemble(SMOKE, "--repo", str(repo), "--check", "--pdf-test")
    assert result.returncode == 1 and "macros.tex" in result.stderr



# --- the claim-body commands (spec/claim-format.md section 4) -----------------


def staged_format(tmp_path: Path) -> Path:
    """Copy the whole `format` fixture: two contracts that cite each other."""
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURES / "format", repo)
    return repo


def test_claim_body_commands_and_links_render(tmp_path: Path):
    repo = staged_format(tmp_path)
    for core in ("core-a", "core-b"):
        result = assemble(core, "--repo", str(repo))
        assert result.returncode == 0, result.stdout + result.stderr
    a = (repo / "spec/modules/core-a/contract.tex").read_text("utf-8")
    b = (repo / "spec/modules/core-b/contract.tex").read_text("utf-8")
    # the requirement environment on the shared counter; no cleveref
    assert r"\newtheorem{requirement}[theorem]{Requirement}" in a
    assert r"\begin{requirement}[Refusal of an object with a negative coordinate]" in a
    assert "cleveref" not in a
    # one \DeclareXref per cited claim of another contract, from bodies and links
    assert (r"\DeclareXref{core-a/thm:bound}{Theorem}{Bound on the first "
            r"coordinate}{../core-a/contract.pdf}") in b
    assert b.count(r"\DeclareXref{") == 1
    assert (r"\DeclareXref{core-b/prop:cross}{Proposition}{The consumer's cap}"
            r"{../core-b/contract.pdf}") in a
    assert r"by \xref{core-a/thm:bound}." in b
    # [[...]]: local claims as "Kind number", short ids as themselves, foreign
    # claims as \xref; the mapped Unicode set as TeX
    assert r"\hyperlink{claim-core-a/thm:bound}{Theorem~\ref*{thm:bound}}" in a
    assert r"\hyperlink{claim-core-a/ass:leaf}{A-LEAF}" in a
    assert r"consumes as \xref{core-b/prop:cross}." in a
    assert (r"under \hyperref{../core-a/contract.pdf}{}{claim-core-a/ass:leaf}"
            r"{A-LEAF}") in b
    assert r"so x \ensuremath{\le} 1." in a
    # \repodoc becomes a relative link that shows the path
    assert (r"\href{../../../docs/guide.md\#usage}{\nolinkurl{docs/guide.md}"
            r"\texttt{\#usage}}") in b
    # the graph index renders the same links in Markdown
    index = (repo / "spec/modules/core-b/graphs/README.md").read_text("utf-8")
    assert ("[Theorem \N{LEFT DOUBLE QUOTATION MARK}Bound on the first coordinate"
            "\N{RIGHT DOUBLE QUOTATION MARK}](../../core-a/contract.pdf"
            "#nameddest=claim-core-a/thm:bound)") in index
    assert "[A\\-LEAF](../../core-a/contract.pdf#nameddest=claim-core-a/ass:leaf)" \
        in index
    local = (repo / "spec/modules/core-a/graphs/README.md").read_text("utf-8")
    assert "(../contract.pdf#nameddest=claim-core-a/thm:bound)" in local
    again = assemble("core-b", "--repo", str(repo), "--check")
    assert again.returncode == 0, again.stdout + again.stderr


def link_actions(pdf: Path) -> tuple[set[str], int]:
    """Return a PDF's URI link targets and its number of GoToR actions."""
    import re
    import zlib

    data = pdf.read_bytes()
    chunks = [data]
    for match in re.finditer(rb"stream\r?\n", data):
        end = data.find(b"endstream", match.end())
        try:
            chunks.append(zlib.decompress(data[match.end():end]))
        except zlib.error:
            continue
    uris: set[str] = set()
    gotor = 0
    for chunk in chunks:
        uris.update(match.group(1).decode()
                    for match in re.finditer(rb"/S\s*/URI\s*/URI\s*\(([^)]*)\)", chunk))
        gotor += len(re.findall(rb"/S\s*/GoToR", chunk))
    return uris, gotor


@pytest.mark.skipif(not (HAS_LATEXMK and HAS_GRAPHVIZ), reason="needs latexmk/Graphviz")
def test_an_xref_links_into_the_other_contract_at_the_claim(tmp_path: Path):
    """A link into another PDF is a relative URI to the stable named destination.

    Browser viewers (Edge, Chrome) ignore a GoToR action, hyperref's default
    for a link into another PDF; a relative URI opens the file at the claim.
    """
    repo = staged_format(tmp_path)          # it carries macros.tex and the .bib
    result = assemble("core-b", "--repo", str(repo), "--pdf-test")
    assert result.returncode == 0, result.stdout + result.stderr
    for pdf in ("contract.pdf", "digest.pdf"):
        uris, gotor = link_actions(repo / "spec/modules/core-b" / pdf)
        assert gotor == 0, pdf
    uris, _ = link_actions(repo / "spec/modules/core-b/contract.pdf")
    assert "../core-a/contract.pdf#nameddest=claim-core-a/thm:bound" in uris
    assert "../core-a/contract.pdf#nameddest=claim-core-a/ass:leaf" in uris
    assert "digest.pdf" in uris


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_a_source_restored_after_its_build_keeps_the_build_current(tmp_path: Path):
    """Commit times alone do not call a restored source's SVG stale.

    A source edited and restored in later commits leaves a build that is still
    exact but can never be committed again, since its bytes do not change. An
    output is current when the source is the one it had at the output's commit;
    a genuinely changed source stays stale.
    """
    def pdf_is_current(source: Path, output: Path) -> tuple[bool]:
        probe = ("import sys; from pathlib import Path; "
                 "from harness.assemble_contract import pdf_is_current as f; "
                 "print(f(Path(sys.argv[1]), Path(sys.argv[2]))[0])")
        run = subprocess.run([sys.executable, "-c", probe, str(source), str(output)],
                             cwd=REPO_ROOT, capture_output=True, text=True, check=True)
        return (run.stdout.strip() == "True",)

    def commit(*args: str, when: str) -> None:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
        subprocess.run(["git", *args], cwd=tmp_path, check=True,
                       capture_output=True, env=env)

    def put(path: Path, body: str) -> None:
        path.write_bytes(body.encode("utf-8") + bytes([10]))

    source, output = tmp_path / "g.dot", tmp_path / "g.svg"
    commit("init", "-q", when="2026-01-01T00:00:00")
    put(source, "digraph { a }")
    put(output, "<svg/>")
    commit("add", "g.dot", "g.svg", when="2026-01-01T00:00:00")
    commit("commit", "-q", "-m", "build", when="2026-01-01T00:00:00")
    for body, when in (("digraph { b }", "2026-01-02T00:00:00"),
                       ("digraph { a }", "2026-01-03T00:00:00")):
        put(source, body)
        commit("commit", "-q", "-am", "edit", when=when)
    assert pdf_is_current(source, output)[0]
    put(source, "digraph { c }")
    commit("commit", "-q", "-am", "change", when="2026-01-04T00:00:00")
    assert not pdf_is_current(source, output)[0]


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_a_reference_no_contract_cites_keeps_its_pdfs_current(tmp_path: Path):
    """Registering one reference does not make every PDF stale.

    A PDF reads only the entries of references.bib its tex cites, so a new
    entry elsewhere rebuilds it byte-identically and git cannot record the
    rebuild. The entries compared carry accented names, which git's output
    must decode as the UTF-8 the file is. A changed cited entry stays stale.
    """
    def stale(pdf: Path, *inputs: Path) -> bool:
        probe = ("import sys; from pathlib import Path; "
                 "from harness.assemble_contract import stale_pdf as f; "
                 "print(f(Path(sys.argv[1]), [Path(a) for a in sys.argv[2:]]))")
        run = subprocess.run([sys.executable, "-c", probe, str(pdf),
                              *map(str, inputs)], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True)
        return run.stdout.strip() != "None"

    def commit(*args: str, when: str) -> None:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
        subprocess.run(["git", *args], cwd=tmp_path, check=True,
                       capture_output=True, env=env)

    def put(path: Path, body: str) -> None:
        path.write_bytes(body.encode("utf-8") + bytes([10]))

    cited = "@article{cited,\n  author = {N. Lütkenhaus},\n  year = {2020}\n}\n"
    tex, bib, pdf = tmp_path / "c.tex", tmp_path / "references.bib", tmp_path / "c.pdf"
    commit("init", "-q", when="2026-01-01T00:00:00")
    put(tex, r"See \cite[Thm.~1]{cited}.")
    put(bib, cited)
    put(pdf, "%PDF")
    commit("add", "c.tex", "references.bib", "c.pdf", when="2026-01-01T00:00:00")
    commit("commit", "-q", "-m", "build", when="2026-01-01T00:00:00")
    put(bib, cited + "\n@misc{other,\n  author = {J. Müller}\n}\n")
    commit("commit", "-q", "-am", "register", when="2026-01-02T00:00:00")
    assert not stale(pdf, tex, bib)
    put(bib, cited.replace("2020", "2021"))
    commit("commit", "-q", "-am", "correct", when="2026-01-03T00:00:00")
    assert stale(pdf, tex, bib)


def test_a_comment_only_edit_of_a_tex_input_keeps_its_pdf_current(tmp_path: Path):
    """A comment-only edit of spec/macros.tex does not make PDFs stale.

    The rebuild is byte-identical, so git cannot record it; a comment never
    reaches the build. A changed macro stays stale, and an escaped percent
    sign is text, not a comment.
    """
    def stale(pdf: Path, *inputs: Path) -> bool:
        probe = ("import sys; from pathlib import Path; "
                 "from harness.assemble_contract import stale_pdf as f; "
                 "print(f(Path(sys.argv[1]), [Path(a) for a in sys.argv[2:]]))")
        run = subprocess.run([sys.executable, "-c", probe, str(pdf),
                              *map(str, inputs)], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True)
        return run.stdout.strip() != "None"

    def commit(*args: str, when: str) -> None:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
        subprocess.run(["git", *args], cwd=tmp_path, check=True,
                       capture_output=True, env=env)

    def put(path: Path, body: str) -> None:
        path.write_bytes(body.encode("utf-8"))

    macros = ("% The macros.\n\\newcommand{\\rate}{r} % the rate\n"
              "\\newcommand{\\pct}{5\\%}\n")
    tex, pdf = tmp_path / "macros.tex", tmp_path / "c.pdf"
    commit("init", "-q", when="2026-01-01T00:00:00")
    put(tex, macros)
    put(pdf, "%PDF")
    commit("add", "macros.tex", "c.pdf", when="2026-01-01T00:00:00")
    commit("commit", "-q", "-m", "build", when="2026-01-01T00:00:00")
    put(tex, macros.replace("% The macros.", "% The macros, current state.")
        .replace("% the rate", "% the key rate"))
    commit("commit", "-q", "-am", "comments", when="2026-01-02T00:00:00")
    assert not stale(pdf, tex)
    put(tex, macros.replace("5\\%", "6\\%"))
    commit("commit", "-q", "-am", "percent", when="2026-01-03T00:00:00")
    assert stale(pdf, tex)


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_a_macro_edit_stales_only_the_pdfs_whose_sources_reach_it(tmp_path: Path):
    """spec/macros.tex is compared by the definitions a PDF's other texs reach.

    A definition no source of the build names (directly, or through another
    definition it names) rebuilds the PDF byte-identically, so an edit of it
    leaves the PDF current; git could not record the rebuild. An edit of a
    definition the contract names, or of one reached only through another
    definition's body, makes it stale. A comment of macros.tex, even one on
    a reached definition's line or naming a reached macro, reaches nothing.
    """
    def stale(pdf: Path, *inputs: Path) -> bool:
        probe = ("import sys; from pathlib import Path; "
                 "from harness.assemble_contract import stale_pdf as f; "
                 "print(f(Path(sys.argv[1]), [Path(a) for a in sys.argv[2:]]))")
        run = subprocess.run([sys.executable, "-c", probe, str(pdf),
                              *map(str, inputs)], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True)
        return run.stdout.strip() != "None"

    def used(macros: str, *texs: Path) -> str:
        probe = ("import sys; from pathlib import Path; "
                 "from harness.assemble_contract import used_macros as f; "
                 "sys.stdout.write(f(sys.stdin.read(), "
                 "[Path(a) for a in sys.argv[1:]]))")
        return subprocess.run([sys.executable, "-c", probe, *map(str, texs)],
                              input=macros, cwd=REPO_ROOT, capture_output=True,
                              text=True, check=True).stdout

    def commit(*args: str, when: str) -> None:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
        subprocess.run(["git", *args], cwd=tmp_path, check=True,
                       capture_output=True, env=env)

    def put(path: Path, body: str) -> None:
        path.write_bytes(body.encode("utf-8"))

    macros = ("% The shared macros.\n\\usepackage{amsmath}\n"
              "\\newcommand{\\rate}{r} % the rate, unlike \\other\n"
              "\\newcommand{\\keyrate}{\\rate_{\\mathrm{key}}}\n"
              "\\DeclareMathOperator{\\Tr}{Tr}\n"
              "\\newcommand{\\other}{o}\n")
    body = "The rate is $\\keyrate$ and $\\Tr\\rho$.\n"
    shared, tex = tmp_path / "macros.tex", tmp_path / "c.tex"
    pdf = tmp_path / "c.pdf"
    put(tex, body)
    view = used(macros, tex)
    assert "\\usepackage{amsmath}" in view
    for reached in ("\\rate}", "\\keyrate}", "\\Tr}"):
        assert reached in view, reached
    for unreached in ("\\other}", "\\other\n", "%"):
        assert unreached not in view, unreached
    spaced = macros.replace("\n\\newcommand{\\other}", "\n\n\n\\newcommand{\\other}")
    assert used(spaced, tex) == view   # the preamble ignores blank lines

    commit("init", "-q", when="2026-01-01T00:00:00")
    put(shared, macros)
    put(pdf, "%PDF")
    commit("add", "macros.tex", "c.tex", "c.pdf", when="2026-01-01T00:00:00")
    commit("commit", "-q", "-m", "build", when="2026-01-01T00:00:00")
    edits = (
        ("\\newcommand{\\other}{o}", "\\newcommand{\\other}{p}", False),
        ("% The shared macros.", "% The shared macros, renamed.", False),
        ("% the rate", "% the secret-key rate", False),
        ("\\newcommand{\\rate}{r}", "\\newcommand{\\rate}{R}", True),
        ("{\\rate_{\\mathrm{key}}}", "{\\rate_{\\mathrm{sec}}}", True),
        ("{Tr}", "{tr}", True),
    )
    for day, (old, new, expected) in enumerate(edits, start=2):
        put(shared, macros.replace(old, new))
        commit("commit", "-q", "-am", old, when=f"2026-01-{day:02d}T00:00:00")
        assert stale(pdf, tex, shared) is expected, (old, new)


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_a_meta_line_edit_of_a_contract_leaves_its_digest_current(tmp_path: Path):
    """A meta-line-only change of contract.tex does not make digests stale.

    A claim of another module gaining or losing an edge changes only the
    "Used by" or "Assumed by" line of a contract (and its trailer id). The
    contract PDF is then stale, but the digest reads its contract only through
    contract.aux, labels with their numbers and anchors, so its rebuild is
    byte-identical and git cannot record it. A new label in a claim the
    digest leaves out still makes the digest stale: it can renumber.
    """
    def stale(pdf: Path, *inputs: Path) -> bool:
        probe = ("import sys; from pathlib import Path; "
                 "from types import SimpleNamespace; "
                 "from harness.assemble_contract import Unit; "
                 "unit = SimpleNamespace(tex=Path(sys.argv[1]), "
                 "digest=Path(sys.argv[2])); "
                 "print(Unit.stale_pdf(unit, Path(sys.argv[3]), "
                 "[Path(a) for a in sys.argv[4:]]))")
        run = subprocess.run([sys.executable, "-c", probe, str(contract), str(digest),
                              str(pdf), *map(str, inputs)], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True)
        return run.stdout.strip() != "None"

    def commit(*args: str, when: str) -> None:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
        subprocess.run(["git", *args], cwd=tmp_path, check=True,
                       capture_output=True, env=env)

    def put(path: Path, body: str) -> None:
        path.write_bytes(body.encode("utf-8"))

    meta = "\\claimmeta{\\metalabel{Assumed by}\\mref{Thm.}{thm:bound}}\n"
    tex = ("\\documentclass{article}\n\\pdftrailerid{0001}\n\\begin{document}\n"
           "\\section{Results}\n"
           "\\begin{theorem}\\label{thm:bound}\nEvery $x \\le 1$.\n\\end{theorem}\n"
           + meta +
           "\\begin{remark}\\label{rem:tight}\nSharp.\n\\end{remark}\n"
           "\\end{document}\n")
    contract, digest = tmp_path / "contract.tex", tmp_path / "digest.tex"
    contract_pdf, digest_pdf = tmp_path / "contract.pdf", tmp_path / "digest.pdf"
    commit("init", "-q", when="2026-01-01T00:00:00")
    put(contract, tex)
    put(digest, "\\documentclass{article}\n\\externaldocument[C-]{contract}\n")
    put(contract_pdf, "%PDF")
    put(digest_pdf, "%PDF")
    commit("add", ".", when="2026-01-01T00:00:00")
    commit("commit", "-q", "-m", "build", when="2026-01-01T00:00:00")
    put(contract, tex.replace("0001", "0002").replace(
        meta, meta.replace("}}\n", "}, \\extref{../m/contract.pdf}{m/thm:new}}\n")))
    commit("commit", "-q", "-am", "meta line", when="2026-01-02T00:00:00")
    assert stale(contract_pdf, contract)
    assert not stale(digest_pdf, digest, contract)
    put(contract, tex.replace("Sharp.\n", "Sharp:\n\\begin{equation}\\label{eq:new}"
                              "x\\end{equation}\n"))
    commit("commit", "-q", "-am", "a new display", when="2026-01-03T00:00:00")
    assert stale(digest_pdf, digest, contract)


def test_a_change_of_the_tex_changes_the_pdf_trailer_identifier():
    """A preamble macro no body uses leaves every PDF byte-identical.

    Git cannot record a rebuild that changes no byte, so the freshness check
    would call those PDFs stale; the trailer identifier is a digest of the tex.
    """
    def with_trailer_id(tex: str) -> str:
        probe = ("import sys; "
                 "from harness.assemble_contract import with_trailer_id as f; "
                 "sys.stdout.write(f(sys.stdin.read()))")
        return subprocess.run([sys.executable, "-c", probe], input=tex, cwd=REPO_ROOT,
                              capture_output=True, text=True, check=True).stdout

    one = with_trailer_id("% head\n\\documentclass{article}\n\\newcommand{\\a}{a}\n")
    two = with_trailer_id("% head\n\\documentclass{article}\n\\newcommand{\\b}{b}\n")
    assert one.splitlines()[2].startswith("\\pdftrailerid{")
    assert one.splitlines()[2] != two.splitlines()[2]
    assert with_trailer_id("no class here\n") == "no class here\n"
