"""The contract layout, on the `format` fixture.

Motivation: the layout is what a reader sees, and each rule of it
(`spec/style.md` sections 3 to 6, `harness/contract_structure.py`) can silently
regress: a requirement drifting into the mathematics part, a number in the
graph index that is not the number in the PDF, a meta line that drops an edge,
a restated main result that duplicates a label, a free-text interface field
that stops pdflatex. The `format` fixture has one claim of each shape the
layout distinguishes (a main theorem with a lead-in, a remark, an assumption
with a ledger row, a requirement, a technical lemma in a submodule, a claim of
another contract that uses and assumes across the boundary), so each test
reads one rule off the generated TeX, and one test compiles it.
"""

from __future__ import annotations

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


def _load_tools(*names: str) -> list[ModuleType]:
    """Return modules of the real ``harness`` package, loaded by path.

    ``tests/harness/`` is itself a package named ``harness``, so under pytest's
    prepend import mode ``from harness import ...`` resolves to the test
    package (test_relabel.py loads its tool the same way). The real package is
    placed under the name ``harness`` only while the modules load, and the
    import state before the load is restored afterwards.
    """
    cached = [sys.modules.get(f"_layout_{name}") for name in names]
    if all(module is not None for module in cached):
        return [module for module in cached if module is not None]
    prefix = ("harness", "harness.")
    saved = {key: module for key, module in sys.modules.items()
             if key == prefix[0] or key.startswith(prefix[1])}
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
        loaded = [importlib.import_module(f"harness.{name}") for name in names]
    finally:
        stale = [k for k in sys.modules if k == prefix[0] or k.startswith(prefix[1])]
        for key in stale:
            sys.modules.pop(key, None)
        sys.modules.update(saved)
    for name, module in zip(names, loaded, strict=True):
        sys.modules[f"_layout_{name}"] = module
    return loaded


(_claims, _front, _navigation, _render, _structure, _pins) = _load_tools(
    "check_claims", "contract_frontmatter", "contract_navigation", "contract_render",
    "contract_structure", "oracle_pins")
load_repo = _claims.load_repo
restate = _front.restate
UNICODE_TEX, markdown_tex, tex_safe = (_navigation.UNICODE_TEX,
                                       _navigation.markdown_tex, _navigation.tex_safe)
number_displays, split_body = _render.number_displays, _render.split_body
MATHEMATICS, REQUIREMENTS = _structure.MATHEMATICS, _structure.REQUIREMENTS
contract_sections = _structure.contract_sections
oracle_pins, pinned_codes = _pins.oracle_pins, _pins.pinned_codes

FORMAT = Path(__file__).resolve().parent / "fixtures" / "format"
A = "spec/modules/core-a"
HAS_LATEXMK = shutil.which("latexmk") is not None
HAS_GRAPHVIZ = (shutil.which("dot") is not None
                or Path("C:/Program Files/Graphviz/bin/dot.exe").is_file())


def copy(tmp_path: Path) -> Path:
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


def assemble(repo: Path, core: str, *args: str) -> str:
    """Assemble ``core`` without a PDF and return its contract.tex."""
    result = subprocess.run(
        [sys.executable, "-m", "harness.assemble_contract", core, "--repo", str(repo),
         "--no-pdf", *args], cwd=REPO_ROOT, capture_output=True, text=True,
        check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return (repo / "spec" / "modules" / core / "contract.tex").read_text("utf-8")


def claim_block(tex: str, claim_id: str) -> str:
    """Return one claim's emitted block, up to the next claim or section."""
    block = tex.split(f"% claim {claim_id}\n", 1)[1]
    return re.split(r"\n% claim |\n\\section|\n\\clearpage", block, maxsplit=1)[0]


def meta_of(tex: str, claim_id: str) -> str:
    """Return the argument of one claim's meta line (braces matched)."""
    block = claim_block(tex, claim_id)
    start = block.index("\\claimmeta{") + len("\\claimmeta{")
    depth = 1
    for position in range(start, len(block)):
        if block[position] == "{" and block[position - 1] != "\\":
            depth += 1
        elif block[position] == "}" and block[position - 1] != "\\":
            depth -= 1
            if depth == 0:
                return block[start:position]
    raise AssertionError(f"unbalanced meta line of {claim_id}")


# --- the structure ------------------------------------------------------------------


def test_parts_sections_and_numbers():
    structure = contract_sections(load_repo(FORMAT), "core-a")
    parts = [(part.title, [(s.number, s.title, s.kind) for s in part.sections])
             for part in structure.parts]
    assert parts == [
        ("Mathematics", [(1, "Objects and the bound", MATHEMATICS),
                         (2, "Assumptions", MATHEMATICS)]),
        ("Engine requirements", [(3, "Requirements", REQUIREMENTS)]),
        ("Sub X", [(4, "The helper", MATHEMATICS)]),
    ]
    assert structure.numbers() == {
        "core-a/def:object": "1.1", "core-a/thm:bound": "1.2",
        "core-a/rem:tight": "1.3", "core-a/ass:leaf": "2.1",
        "core-a/req:refuse": "3.1", "core-a/sub-x/lem:helper": "4.1"}


def test_a_requirement_in_a_mixed_group_goes_to_part_two(tmp_path: Path):
    """A group holding both kinds gives two sections of the same title."""
    repo = copy(tmp_path)
    edit(repo, f"{A}/module.yaml", "  - title: Requirements\n    start: req:refuse\n"
         "    abstract: What the implementation refuses.\n", "")
    structure = contract_sections(load_repo(repo), "core-a")
    sections = [(s.number, s.title, s.kind, s.claims, s.abstract)
                for s in structure.sections()]
    assert sections[1] == (2, "Assumptions", MATHEMATICS, ("core-a/ass:leaf",),
                           "The one hypothesis of the bound.")
    assert sections[2] == (3, "Assumptions", REQUIREMENTS, ("core-a/req:refuse",), "")
    tex = assemble(repo, "core-a")
    assert tex.index(r"\part{Engine requirements}") < tex.index(r"\label{req:refuse}")


def test_no_part_two_without_requirements(tmp_path: Path):
    tex = assemble(copy(tmp_path), "core-b")
    assert r"\part{Mathematics}" in tex
    assert r"\part{Engine requirements}" not in tex


def test_the_graph_index_prints_the_numbers_the_pdf_prints(tmp_path: Path):
    repo = copy(tmp_path)
    tex = assemble(repo, "core-a")
    index = (repo / A / "graphs" / "README.md").read_text("utf-8")
    assert "## Part II: Engine requirements" in index
    assert "### 3 Requirements" in index
    assert "- 1.2 [`core-a/thm:bound`]" in index
    assert "- 4.1 [`core-a/sub-x/lem:helper`]" in index
    assert (repo / A / "graphs" / "group-03-requirements.dot").is_file()
    assert (repo / A / "graphs" / "group-04-sub-x-the-helper.dot").is_file()
    assert "4 Sub X: The helper" in (repo / A / "graphs" / "overview.dot").read_text(
        "utf-8")
    # the PDF's sections carry the same order and anchors
    assert tex.index(r"\section{Requirements}\label{group-core-a/req:refuse}") \
        < tex.index(r"\part{Sub X}")


# --- one claim ----------------------------------------------------------------------


def test_a_claim_reads_summary_bookmark_leadin_statement_meta_proof(tmp_path: Path):
    tex = assemble(copy(tmp_path), "core-a")
    block = claim_block(tex, "core-a/thm:bound")
    order = [r"\claimsummary{core-a/thm:bound}{The first coordinate",
             r"\claimbookmark{core-a/thm:bound}{Theorem}{thm:bound}"
             r"{Bound on the first coordinate}",
             "\\claimleadin{%\nThe bound is the reason",
             r"\begin{mainclaim}",
             r"\begin{theorem}[Bound on the first coordinate]\label{thm:bound}",
             r"\end{mainclaim}", r"\claimmeta{", r"\begin{proof}"]
    positions = [block.index(piece) for piece in order]
    assert positions == sorted(positions)
    # the summary's [[...]] link and mapped Unicode, rendered
    assert (r"(\hyperlink{claim-core-a/def:object}{Definition~\ref*{def:object}})"
            in block)
    technical = claim_block(tex, "core-a/sub-x/lem:helper")
    assert r"\begin{technicalclaim}" in technical
    assert "mainclaim" not in claim_block(tex, "core-a/rem:tight")
    assumption = claim_block(tex, "core-a/ass:leaf")
    assert assumption.index(r"\SetShortId{A-LEAF}") < assumption.index(
        r"\begin{assumption}[Nonnegative second coordinate]")


def test_the_meta_lines(tmp_path: Path):
    repo = copy(tmp_path)
    # a module of the real tree, since test_no_predecessor_process_in_the_tree
    # holds every certiqs_key path named in tests to exist
    edit(repo, f"{A}/claims/req-refuse.tex", "% lean:",
         "% implements: certiqs_key.transmitter.certificate:verify_certificate\n"
         "% lean:")
    tex = assemble(repo, "core-a")
    items = meta_of(tex, "core-a/thm:bound").split("\n\\metasep ")
    assert items == [
        r"\metalabel{Uses}\mref{Def.}{def:object}, \mref{Ass.}{ass:leaf}",
        r"\metalabel{Assumes}\aref{A-LEAF}{ass:leaf}",
        r"\metalabel{Used by}\mref{Rem.}{rem:tight}, "
        r"\extref{../core-b/contract.pdf}{core-b/prop:cross}",
        "newly derived",
        "accepted",
        r"\metalabel{Oracles}\coderef{" + _render.GITHUB
        + r"tests/oracles/registry_core_a.py}{registry_core_a.py}",
    ]
    assumption = meta_of(tex, "core-a/ass:leaf")
    assert (r"\metalabel{Assumed by}\mref{Thm.}{thm:bound}, "
            r"\extref{../core-b/contract.pdf}{core-b/prop:cross}") in assumption
    assert r"\metalabel{Machine key}\iface{leaf_nonnegative}" in assumption
    assert assumption.index("Assumed by") < assumption.index("Machine key") \
        < assumption.index("Used by")
    requirement = meta_of(tex, "core-a/req:refuse").split("\n\\metasep ")
    assert requirement == [
        r"\metalabel{Motivated by}\mref{Thm.}{thm:bound}", "accepted",
        r"\metalabel{Code}\coderef{" + _render.GITHUB
        + r"src/certiqs_key/transmitter/certificate.py}"
        r"{certiqs_key.transmitter.certificate:verify_certificate}"]
    assert r"published in \cite[{Def. 1}]{alpha2020work}" in meta_of(
        tex, "core-a/def:object")
    # a claim of the submodule is internal: numbered, not a link to a PDF
    assert r"\mref{Lem.}{lem:helper}" in meta_of(tex, "core-a/def:object")


def test_the_code_links_take_another_base(tmp_path: Path):
    """``--code-url`` moves every code and registry link, a public copy's need."""
    repo = copy(tmp_path)
    edit(repo, f"{A}/claims/req-refuse.tex", "% lean:",
         "% implements: certiqs_key.transmitter.certificate:verify_certificate\n"
         "% lean:")
    tex = assemble(repo, "core-a", "--code-url", "https://example.org/tree/")
    assert "github.com" not in tex
    assert (r"\coderef{https://example.org/tree/src/certiqs_key/transmitter/"
            r"certificate.py}") in meta_of(tex, "core-a/req:refuse")
    assert (r"\coderef{https://example.org/tree/tests/oracles/registry_core_a.py}"
            in meta_of(tex, "core-a/thm:bound"))


def test_a_machine_key_written_as_prose_keeps_its_spaces(tmp_path: Path):
    repo = copy(tmp_path)
    edit(repo, f"{A}/interface.yaml", "machine_key: leaf_nonnegative",
         'machine_key: "leaf_nonnegative, y_sign"')
    tex = assemble(repo, "core-a")
    assert (r"\metalabel{Machine key}\texttt{leaf\_nonnegative, y\_sign}"
            in meta_of(tex, "core-a/ass:leaf"))


def test_the_effective_status_is_shown_when_lower(tmp_path: Path):
    repo = copy(tmp_path)
    edit(repo, f"{A}/claims/def-object.tex", "% status: accepted", "% status: draft")
    tex = assemble(repo, "core-a")
    assert "\n\\metasep accepted (effective: draft)" in meta_of(tex, "core-a/thm:bound")


def test_text_after_the_proof_is_printed_not_dropped(tmp_path: Path):
    repo = copy(tmp_path)
    edit(repo, f"{A}/claims/thm-bound.tex", "\\end{proof}\n",
         "\\end{proof}\n\nA trailing aside.\n")
    edit(repo, f"{A}/claims/rem-tight.tex", "\\end{remark}\n",
         "\\end{remark}\n\nAnother aside.\n")
    tex = assemble(repo, "core-a")
    theorem = claim_block(tex, "core-a/thm:bound")
    assert theorem.index(r"\end{proof}") < theorem.index("A trailing aside.")
    remark = claim_block(tex, "core-a/rem:tight")
    assert remark.index(r"\claimmeta{") < remark.index("Another aside.")


def test_a_section_lists_its_foreign_imports_once(tmp_path: Path):
    tex = assemble(copy(tmp_path), "core-b")
    assert tex.count(r"\sectionimports{") == 1
    assert (r"\sectionimports{\extref{../core-a/contract.pdf}{core-a/thm:bound}}"
            in tex)
    assert "Imports" not in assemble(copy(tmp_path / "a"), "core-a").split(
        r"\part{Mathematics}", 1)[1].split(r"\part{Sub X}", 1)[0].replace(
        r"\metalabel{Imports}", "")


# --- front matter -------------------------------------------------------------------


def test_the_front_matter_order(tmp_path: Path):
    tex = assemble(copy(tmp_path), "core-a")
    front = tex.split(r"\begin{document}", 1)[1].split(r"\part{Mathematics}", 1)[0]
    order = [r"{\LARGE\bfseries Core A}", r"{\large Contract, version 0.1.0}",
             r"\begin{overview}", "is non-normative", r"\href{graphs/overview.svg}",
             r"\tableofcontents", r"\section*{Main results}",
             r"\section*{Assumptions at a glance}"]
    positions = [front.index(piece) for piece in order]
    assert positions == sorted(positions)
    assert "Rows depend on columns" not in tex          # the matrix left the PDF


def test_a_main_result_is_listed_with_its_summary(tmp_path: Path):
    tex = assemble(copy(tmp_path), "core-a")
    main = tex.split(r"\section*{Main results}", 1)[1].split(r"\section*{", 1)[0]
    assert (r"\hyperref[thm:bound]{\textbf{Theorem~\ref*{thm:bound}}}\enspace "
            r"Bound on the first coordinate") in main
    assert "Consumers read the bound as a cap." in main      # the summary
    assert r"\claimmeta{\metalabel{Rests on}\aref{A-LEAF}{ass:leaf}}" in main
    assert r"\begin{restatedclaim}" not in main and r"\label" not in main
    assert r"\section*{Main results}" not in assemble(copy(tmp_path / "b"), "core-b")


def test_terms_are_defined_linked_and_tabulated(tmp_path: Path):
    repo = copy(tmp_path)
    own = assemble(repo, "core-a")
    assert (r"\termdef{term-base-object}{base object}"
            in claim_block(own, "core-a/def:object"))
    assert (r"Every \termref{term-base-object}{base object}"
            in claim_block(own, "core-a/ass:leaf"))
    terms = own.split(r"\section*{Terms}", 1)[1].split(r"\end{xltabular}", 1)[0]
    assert (r"\termref{term-base-object}{base object} & a pair of reals whose "
            r"coordinates sum to one & \mref{Definition}{def:object}\\") in terms
    # the first use in a section introduction links, the second does not
    intro = own.split(r"\section{Objects and the bound}", 1)[1].split("\n\n", 1)[0]
    assert r"Defines the \termref{term-base-object}{base object} and" in intro
    foreign = assemble(repo, "core-b")
    assert (r"Every \exttermref{../core-a/contract.pdf}{term-base-object}{base object}"
            in claim_block(foreign, "core-b/prop:cross"))
    table = foreign.split(r"\section*{Terms}", 1)[1].split(r"\end{xltabular}", 1)[0]
    assert r"\extref{../core-a/contract.pdf}{core-a/def:object}" in table


def test_the_assumptions_at_a_glance(tmp_path: Path):
    repo = copy(tmp_path)
    own = assemble(repo, "core-a")
    assert (r"\aref{A-LEAF}{ass:leaf} & source & Nonnegative second coordinate & "
            r"\mref{Assumption}{ass:leaf} & \mref{Thm.}{thm:bound}\\") in own
    assert "Assumption & Category & Title & Stated as" in own
    foreign = assemble(repo, "core-b")
    assert (r"\extaref{../core-a/contract.pdf}{core-a/ass:leaf}{A-LEAF} & source & "
            r"Nonnegative second coordinate & "
            r"\extref{../core-a/contract.pdf}{core-a/ass:leaf} & "
            r"\mref{Prop.}{prop:cross}\\") in foreign


LEAF = f"{A}/claims/ass-leaf.tex"
#: The required assumption fields as the fixture's A-LEAF carries them.
LEAF_CATEGORY = "% category: source\n"
LEAF_AFFECTS = "% affects: [secrecy]\n"
LEAF_READING = ("% user_statement: Every pair you declare has a nonnegative second "
                "coordinate.\n")


def add_assumption(repo: Path, slug: str, short_id: str, extra: str = "",
                   category: str = "numerical-trust") -> None:
    """Add a second assumption to core-a, assumed by the theorem."""
    (repo / A / "claims" / f"ass-{slug}.tex").write_text(
        "% ---\n"
        f"% id: core-a/ass:{slug}\n% kind: ass\n% title: Bounded pairs {slug}\n"
        "% summary: The first coordinate of every pair is at most one.\n"
        "% prominence: standard\n% status: accepted\n% uses: []\n% assumes: []\n"
        "% refs: []\n% provenance: newly-derived\n"
        f"% short_id: {short_id}\n% verification: never\n"
        f"% category: {category}\n% affects: [completeness]\n"
        "% user_statement: Every pair you declare has x ≤ 1.\n" + extra
        + "% lean:\n% ---\n\n"
        f"\\begin{{assumption}}\\label{{ass:{slug}}}\n"
        "Every pair $(x, y)$ has $x \\le 1$.\n\\end{assumption}\n",
        encoding="utf-8", newline="\n")
    edit(repo, f"{A}/module.yaml", "  - ass:leaf\n", f"  - ass:leaf\n  - ass:{slug}\n")
    edit(repo, f"{A}/claims/thm-bound.tex", "% assumes: [A-LEAF",
         f"% assumes: [A-LEAF, {short_id}")


def test_an_assumption_shows_category_affects_and_refines(tmp_path: Path):
    repo = copy(tmp_path)
    edit(repo, LEAF, LEAF_CATEGORY + LEAF_AFFECTS,
         "% category: channel-and-adversary\n% affects: [secrecy, correctness]\n")
    add_assumption(repo, "twin", "A-TWIN", "% refines: A-LEAF\n")
    tex = assemble(repo, "core-a")
    leaf = meta_of(tex, "core-a/ass:leaf").split("\n\\metasep ")
    assert leaf[:4] == [r"\metalabel{Uses}\mref{Def.}{def:object}",
                        r"\metalabel{Category}channel and adversary",
                        r"\metalabel{Affects}secrecy, correctness",
                        r"\metalabel{Assumed by}\mref{Thm.}{thm:bound}, "
                        r"\extref{../core-b/contract.pdf}{core-b/prop:cross}"]
    twin = meta_of(tex, "core-a/ass:twin").split("\n\\metasep ")
    assert twin[:3] == [r"\metalabel{Category}numerical trust",
                        r"\metalabel{Affects}completeness",
                        r"\metalabel{Refines}\aref{A-LEAF}{ass:leaf}"]


def test_the_verification_sentence_is_generated_from_the_field(tmp_path: Path):
    """Every assumption gets it, then its reading, before the meta line.

    Every assumption carries
    `category` and a `verification` of never or partly, so the sentence is
    generated for each and no body writes it by hand.
    """
    repo = copy(tmp_path)
    edit(repo, LEAF, LEAF_READING, "% user_statement: Every pair you declare has "
         "y ≥ 0; otherwise see [[thm:bound]].\n")
    tex = assemble(repo, "core-a")
    block = claim_block(tex, "core-a/ass:leaf")
    sentence = (r"\claimverification{The engine does not verify this assumption; "
                r"a run that rests on it records it as unverified.}")
    reading = (r"\claimreading{Every pair you declare has y \ensuremath{\ge} 0; "
               r"otherwise see \hyperlink{claim-core-a/thm:bound}"
               r"{Theorem~\ref*{thm:bound}}.}")
    order = [r"\end{assumption}", sentence, reading, r"\claimmeta{"]
    positions = [block.index(piece) for piece in order]
    assert positions == sorted(positions)
    # the other value an assumption may carry, from the one table
    edit(repo, LEAF, "% verification: never\n", "% verification: partly\n")
    assert ("decides part of this assumption; the rest is attested."
            in claim_block(assemble(repo, "core-a"), "core-a/ass:leaf"))


def test_a_result_with_a_user_statement_gets_the_reading_paragraph(tmp_path: Path):
    """A result's plain reading prints as an assumption's does.

    The key-rate report shows a user the reading of its security statement,
    so the contract prints it beside the statement it reads, after the
    framed statement and before the meta line; no verification sentence,
    which is an assumption's alone. A claim without one gets no paragraph.
    """
    repo = copy(tmp_path)
    edit(repo, f"{A}/claims/thm-bound.tex", "% lean:\n",
         "% user_statement: Your first coordinate is at most one while "
         "[[A-LEAF]] holds; see [[rem:tight]].\n% lean:\n")
    tex = assemble(repo, "core-a")
    block = claim_block(tex, "core-a/thm:bound")
    reading = (r"\claimreading{Your first coordinate is at most one while "
               r"\hyperlink{claim-core-a/ass:leaf}{A-LEAF} holds; see "
               r"\hyperlink{claim-core-a/rem:tight}{Remark~\ref*{rem:tight}}.}")
    order = [r"\end{mainclaim}", reading, r"\claimmeta{", r"\begin{proof}"]
    positions = [block.index(piece) for piece in order]
    assert positions == sorted(positions)
    assert r"\claimverification" not in block
    assert r"\claimreading" not in claim_block(tex, "core-a/rem:tight")


def test_the_assumption_table_groups_by_category(tmp_path: Path):
    repo = copy(tmp_path)
    edit(repo, LEAF, LEAF_CATEGORY, "% category: post-processing\n")
    add_assumption(repo, "twin", "A-TWIN", category="source")
    add_assumption(repo, "zero", "A-AAA", category="receiver")
    table = assemble(repo, "core-a").split(r"\section*{Assumptions at a glance}",
                                           1)[1].split(r"\end{xltabular}", 1)[0]
    rows = [line.split(" & ")[:2] for line in table.split("\n")
            if line.startswith(r"\aref")]
    assert rows == [[r"\aref{A-TWIN}{ass:twin}", "source"],
                    [r"\aref{A-AAA}{ass:zero}", "receiver"],
                    [r"\aref{A-LEAF}{ass:leaf}", "post processing"]]


def test_the_notation_table_holds_the_macros_used(tmp_path: Path):
    repo = copy(tmp_path)
    assert r"\section*{Notation}" not in assemble(repo, "core-a")
    edit(repo, f"{A}/claims/def-object.tex", "of reals with",
         "of reals in $\\Obj$ with")
    tex = assemble(repo, "core-a")
    notation = tex.split(r"\section*{Notation}", 1)[1].split(r"\end{xltabular}", 1)[0]
    assert (r"$\Obj$ & The set of base objects, pairs $(x, y)$ with "
            r"\texttt{x + y = 1}\\") in notation
    assert "Unused" not in notation


# --- back matter --------------------------------------------------------------------


def test_the_back_matter(tmp_path: Path):
    repo = copy(tmp_path)
    tex = assemble(repo, "core-a")
    back = tex.split(r"\section*{Interface}", 1)[1]
    assert (r"\iface{base_object}\newline (x, y) & always & "
            r"\mref{Def.}{def:object}\\") in back
    assert (r"\iface{second_coordinate_sign}\newline y \textgreater{}= 0 & "
            r"whenever the bound is wanted & \mref{Ass.}{ass:leaf}, "
            r"\mref{Thm.}{thm:bound}\\") in back
    assert r"\subsection*{Outputs: Core A}" in back
    assert (r"\mref{Theorem}{thm:bound} & Bound on the first coordinate\newline"
            r"{\footnotesize\color{metaGrey}\claimid{core-a/thm:bound}} & "
            r"\pageref{thm:bound}\\") in back
    order = [r"\section*{Claim index}", r"\printindex", r"\bibliography{"]
    positions = [back.index(piece) for piece in order]
    assert positions == sorted(positions)
    # core-b defines no term and has no interface file
    other = assemble(repo, "core-b")
    assert r"\printindex" not in other and r"\section*{Interface}" not in other


def test_the_preamble(tmp_path: Path):
    tex = assemble(copy(tmp_path), "core-a")
    preamble = tex.split(r"\begin{document}", 1)[0]
    assert r"\newtheorem{theorem}{Theorem}[section]" in preamble
    for kind in ("lemma", "definition", "assumption", "remark", "requirement"):
        assert re.search(r"\\newtheorem\{" + kind + r"\}\[theorem\]", preamble), kind
    assert r"\numberwithin{equation}{section}" in preamble
    assert "cleveref" not in preamble and "UseFramedRule" not in preamble
    declared = set(re.findall(r"\\DeclareUnicodeCharacter\{([0-9A-F]{4})\}", preamble))
    assert declared == {f"{ord(char):04X}" for char in UNICODE_TEX}


# --- the text transformations ---------------------------------------------------------


def test_restating_tags_displays_with_their_numbers():
    statement = ("\\begin{theorem}[T]\\label{thm:t}\nA \\term{thing} holds:\n"
                 "\\begin{equation}\\label{eq:a} x = 1 \\end{equation}\n"
                 "\\begin{align} y &= 2 \\\\ z &= 3 \\notag \\\\ w &= 4 % c\n"
                 "\\end{align}\n\\end{theorem}")
    numbered = number_displays(statement, "thm-t")
    assert numbered.count(r"\label{eq:auto-thm-t-") == 2
    assert r"y &= 2\label{eq:auto-thm-t-1} \\ z &= 3 \notag \\" in numbered
    assert r"w &= 4\label{eq:auto-thm-t-2} % c" in numbered   # before the comment
    content = numbered.split("]", 1)[1].rsplit("\\end{theorem}", 1)[0]
    copy_ = restate(content)
    assert r"\label" not in copy_ and r"\notag" not in copy_
    assert r"\begin{equation*}\tag{\ref*{eq:a}} x = 1 \end{equation*}" in copy_
    assert r"\tag{\ref*{eq:auto-thm-t-1}}" in copy_
    assert r"\begin{align*}" in copy_ and r"\end{align*}" in copy_
    assert r"\emph{thing}" in copy_ and r"\term" not in copy_
    glossed = restate(r"A \term[a gloss]{thing} and a \tref[thing]{things}.")
    assert glossed == r"A \emph{thing} and a things."


def test_a_body_is_cut_at_its_environment_and_proof():
    body = ("% a comment \\begin{lemma}\nLead $x$.\n\n\\begin{lemma}\\label{lem:x}\n"
            "S.\n\\end{lemma}\nBetween.\n\\begin{proof}\nP.\n\\end{proof}\nAfter.\n")
    parts = split_body(body)
    assert parts.lead.strip().endswith("Lead $x$.")
    assert parts.statement.startswith("\\begin{lemma}\\label{lem:x}")
    assert parts.statement.endswith("\\end{lemma}")
    assert parts.between.strip() == "Between."
    assert parts.proof.startswith("\\begin{proof}")
    assert parts.trailing.strip() == "After."


def test_free_text_never_stops_pdflatex():
    assert tex_safe("a_b <c> & \N{CIRCLED PLUS} \N{GREEK SMALL LETTER ALPHA}") == (
        r"a\_b \textless{}c\textgreater{} \& \ensuremath{\oplus} \ensuremath{\alpha}")
    assert tex_safe("\N{PLANCK CONSTANT OVER TWO PI}") == r"\textsf{[U+210F]}"
    assert markdown_tex("the *virtual* ensemble with `N_x` and $\\rho$") == (
        r"the \emph{virtual} ensemble with \texttt{N\_x} and $\rho$")


# --- the oracle pins ----------------------------------------------------------------


def test_pins_are_read_from_literals_strings_and_named_constants():
    source = ('IDS = ("PC9", "PC11")\n'
              'A = Entry(claims=("C5", "C6"), supports=["SA3"])\n'
              'B = {"claims": "PR3", "kind": "x"}\n'
              'C = Entry(claims=IDS)\n'
              'D = Entry(name="C7")\n')
    assert pinned_codes(source) == {"PC9", "PC11", "C5", "C6", "SA3", "PR3"}


def test_a_code_no_registry_pins_is_not_an_oracle():
    pins = oracle_pins(FORMAT)
    assert [(pin.code, pin.registries) for pin in pins["core-a/thm:bound"]] == [
        ("C1", ("tests/oracles/registry_core_a.py",))]
    assert "core-a/def:object" not in pins           # C2: mapped, pinned by none
    assert oracle_pins(FORMAT / "spec") == {}         # no table, no pins


# --- the PDF ------------------------------------------------------------------------


@pytest.mark.skipif(not (HAS_LATEXMK and HAS_GRAPHVIZ), reason="needs latexmk/Graphviz")
def test_the_layout_compiles_with_its_numbers(tmp_path: Path):
    repo = copy(tmp_path)
    edit(repo, f"{A}/claims/def-object.tex", "of reals with",
         "of reals in $\\Obj$ with")
    # an assumption: the generated sentence and the reading compile too
    edit(repo, LEAF, LEAF_CATEGORY, "% category: channel-and-adversary\n")
    edit(repo, LEAF, LEAF_READING, "% user_statement: Every pair you declare has "
         "y ≥ 0; see [[thm:bound]].\n")
    result = subprocess.run(
        [sys.executable, "-m", "harness.assemble_contract", "core-a", "--repo",
         str(repo)], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    if shutil.which("pdftotext") is None:
        return
    text = " ".join(subprocess.run(
        ["pdftotext", str(repo / A / "contract.pdf"), "-"], capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=True).stdout.split())
    for heading in ("Definition 1.1 (Base object)",
                    "Theorem 1.2 (Bound on the first coordinate)",
                    "Assumption 2.1 [A-LEAF] (Nonnegative second coordinate)",
                    "Lemma 4.1 (Nonnegativity of the first coordinate)",
                    "Main results", "Assumptions at a glance", "Notation",
                    "Index of defined terms", "Terms",
                    "Theorem 1.2 Bound on the first coordinate",
                    "The engine does not verify this assumption",
                    "Reading: Every pair you declare has y",
                    "Category channel and adversary"):
        assert heading in text, heading
    assert re.search(r"R\s*EQUIREMENT\s+3\.1", text, re.I), text[:2000]
