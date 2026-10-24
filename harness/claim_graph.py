"""Motivation: expose the declared argument without a hand-maintained graph.

The old DOT export omitted assumes edges and human titles. This renderer uses
the checked claim model for uses/assumes edges, a compact group overview, and
group neighbourhoods. External boundary nodes remain visible; mentions never
become proof edges. Graphviz supplies layout, SVG and PDF, with no browser app.
The assembler writes/checks these views with the contract, preventing stale
navigation. This does not verify the completeness or correctness of a proof.
The reading index renders co-located summaries with a local non-normative
label so readers can follow an argument without a separately maintained guide;
their `[[label]]` links become Markdown links into the contract PDFs, resolved
by the checker's own resolver so that the index and the PDF name one target.
The groups are the contract's sections as `contract_structure.py` numbers
them, so a number in a graph or in the
index is the number the PDF prints; the contract does not print the section
matrix and links `overview.svg` instead.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import textwrap
from collections.abc import Collection
from html import escape
from pathlib import Path
from urllib.parse import quote

from harness.check_claims import (
    STATUS_COLOUR,
    Repo,
    in_scope,
    link_resolver,
    load_repo,
    load_yaml_mapping,
)
from harness.contract_navigation import (
    claim_anchor,
    group_slug,
    markdown_plain,
    plain_title,
)
from harness.contract_structure import contract_sections


def dependencies(repo: Repo, claim_id: str) -> list[tuple[str, str]]:
    """Return declared uses and assumes, preserving their different meanings."""
    claim = repo.claims[claim_id]
    edges = [(target, "uses") for target in claim.resolved_uses]
    edges += [(repo.assumptions[sid].claim_id, "assumes")
              for sid in claim.assumes if sid in repo.assumptions]
    return sorted(set(edges))


def prerequisite_closure(repo: Repo, claim_id: str) -> set[str]:
    """Walk prerequisites, including assumptions and their defining objects."""
    found: set[str] = set()
    todo = [claim_id]
    while todo:
        current = todo.pop()
        if current in found:
            continue
        found.add(current)
        todo.extend(target for target, _ in dependencies(repo, current))
    return found


def quoted(text: str) -> str:
    """Quote arbitrary metadata for DOT, including quotes and backslashes."""
    return json.dumps(text, ensure_ascii=False)


def wrapped(text: str, width: int = 38) -> str:
    """Wrap labels so full titles remain readable rather than being truncated."""
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def graph_header(title: str) -> list[str]:
    """Start a vector graph with its edge meaning visible in the image itself."""
    legend = (title + "\nArrow: claim -> prerequisite. Solid: uses; dashed: assumes."
              "\nDeclared dependencies, not a proof check. Mentions excluded.")
    return ["digraph claims {", "  rankdir=LR;",
            f"  graph [label={quoted(legend)}, labelloc=t, fontsize=13, "
            'fontname="Arial", bgcolor="white", pad=0.25, nodesep=0.3];',
            '  node [shape=box, style="rounded,filled", fontname="Arial", '
            'fontsize=11, margin="0.13,0.09"];',
            '  edge [color="#526777", arrowsize=0.65];']


def claim_dot(repo: Repo, selected: set[str], directory: Path,
              title: str) -> str:
    """Render selected claims and one-hop boundary nodes without hiding edges."""
    boundary = {target for cid in selected for target, _ in dependencies(repo, cid)
                if target not in selected}
    lines = graph_header(title)
    for module_id in sorted({repo.claims[cid].module_id
                             for cid in selected | boundary}):
        lines += [f"  subgraph {quoted('cluster_' + module_id)} {{",
                  f"    label={quoted(module_id)}; color=\"#cbd5df\";"]
        for cid in sorted(selected | boundary):
            claim = repo.claims[cid]
            if claim.module_id != module_id:
                continue
            suffix = ("\nBOUNDARY: further prerequisites omitted"
                      if cid in boundary else "")
            pending = (f"\n{len(claim.pending)} pending reference(s)"
                       if claim.pending else "")
            title_text = plain_title(str(claim.header.get("title", claim.label)))
            label = (cid + "\n" + wrapped(title_text)
                     + "\n" + claim.status + pending + suffix)
            relative = Path(os.path.relpath(claim.path, directory)).as_posix()
            url = quote(relative, safe="/.")
            core_dir = repo.modules[claim.module_id.split("/")[0]].path
            pdf_path = Path(os.path.relpath(
                core_dir / "contract.pdf", directory)).as_posix()
            pdf_url = quote(pdf_path, safe="/.") + "#nameddest=" + claim_anchor(cid)
            html_label = escape(label).replace("\n", "<BR/>")
            html_label = ('<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">'
                          f'<TR><TD COLSPAN="2">{html_label}</TD></TR>'
                          f'<TR><TD HREF="{escape(url)}" TARGET="_top">'
                          '<FONT COLOR="#164b87" POINT-SIZE="10">TeX source</FONT></TD>'
                          f'<TD HREF="{escape(pdf_url)}" TARGET="_top">'
                          '<FONT COLOR="#164b87" POINT-SIZE="10">Rendered PDF</FONT>'
                          '</TD></TR></TABLE>')
            style = "rounded,filled,dashed" if cid in boundary else "rounded,filled"
            colour = STATUS_COLOUR.get(claim.status, '#ffffff')
            lines.append(f"    {quoted(cid)} [label=<{html_label}>, "
                         f"fillcolor={quoted(colour)}, "
                         f"style={quoted(style)}, URL={quoted(url)}, target=\"_top\"];")
        lines.append("  }")
    for cid in sorted(selected):
        for target, kind in dependencies(repo, cid):
            attrs = ' [style=dashed, color="#a35f13", tooltip="assumes"]' \
                if kind == "assumes" else ""
            lines.append(f"  {quoted(cid)} -> {quoted(target)}{attrs};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def module_groups(repo: Repo, module_id: str) -> list[tuple[str, str, list[str]]]:
    """Return the contract's sections as graph groups, numbered as in the PDF.

    One group per section of ``contract_structure.contract_sections``: its
    file stem ``group-NN-<slug>`` (NN the section number), its heading
    ``"NN Title"`` (a submodule's sections prefixed by the submodule's title,
    which the PDF shows as the part) and its claim ids.
    """
    result: list[tuple[str, str, list[str]]] = []
    for section in contract_sections(repo, module_id).sections():
        title = section.title
        if section.module_id != module_id:
            title = f"{repo.modules[section.module_id].meta['title']}: {title}"
        result.append((f"group-{section.number:02}-{group_slug(title)}",
                       f"{section.number} {title}", list(section.claims)))
    return result


def overview_dot(repo: Repo, module_id: str,
                 groups: list[tuple[str, str, list[str]]]) -> str:
    """Collapse claims into reading groups; retain edge kinds and external modules."""
    owner = {cid: stem for stem, _, ids in groups for cid in ids}
    edges: set[tuple[str, str, str]] = set()
    external: set[str] = set()
    for cid, source in owner.items():
        for target, kind in dependencies(repo, cid):
            dest = owner.get(target, "external:" + repo.claims[target].module_id)
            if dest.startswith("external:"):
                external.add(dest)
            if source != dest:
                edges.add((source, dest, kind))
    lines = graph_header(module_id + ": reading-group overview")
    lines += ['  graph [ranksep=0.6];', '  node [fillcolor="#edf3f8"];']
    for stem, title, ids in groups:
        label = wrapped(title, 28) + f"\n{len(ids)} claims"
        lines.append(f"  {quoted(stem)} [label={quoted(label)}, "
                     f"URL={quoted(stem + '.svg')}, target=\"_top\"];")
    for dest in sorted(external):
        label = quoted(dest.removeprefix('external:'))
        lines.append(f"  {quoted(dest)} [label={label}, "
                     'style="rounded,dashed", fillcolor="white"];')
    for source, dest, kind in sorted(edges):
        style = 'style=dashed, color="#a35f13"' if kind == "assumes" else 'style=solid'
        lines.append(f"  {quoted(source)} -> {quoted(dest)} [{style}];")
    lines += ["}"]
    return "\n".join(lines) + "\n"


def graph_sources(root: Path, module_id: str,
                  repo: Repo | None = None) -> dict[Path, str]:
    """Generate DOT and a linked reading index; no graph content is authored twice.

    ``[[...]]`` links in summaries and abstracts become Markdown links into
    the contract PDFs. ``repo`` spares a second load when the caller has one.
    """
    if repo is None:
        repo = load_repo(root)

    def prose(text: str, mid: str) -> str:
        return markdown_plain(text, link_resolver(repo, mid), module_id)
    directory = root / "spec" / "modules" / module_id / "graphs"
    groups = module_groups(repo, module_id)
    sources: dict[Path, str] = {}
    sources[directory / "overview.dot"] = overview_matrix(repo, module_id, groups)
    sources[directory / "groups.dot"] = overview_dot(repo, module_id, groups)
    selected = {cid for _, _, ids in groups for cid in ids}
    sources[directory / "claims.dot"] = claim_dot(
        repo, selected, directory, module_id + ": all local claims")
    lines = [f"# {repo.modules[module_id].meta['title']}: graphs and navigation", "",
             "GENERATED by `python -m harness.assemble_contract " + module_id
             + "`. Do not edit this index or the graphs.", "",
             "[Contract PDF](../contract.pdf) · "
             "[Viewing instructions](../../../../harness/contract-reading.md)", ""]
    # The link names a heading, so it is written only where that heading
    # exists: a design.md without a main-logic section (foundations') would
    # otherwise get a link that resolves to nothing.
    design = directory.parent / "design.md"
    if design.is_file() and re.search(
        r"^## The module's main logic\s*$",
        design.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    ):
        lines += ["[Explanatory flowchart in design.md]"
                  "(../design.md#the-modules-main-logic) "
                  "(authored, non-normative; different from dependency graphs).", ""]
    lines += ["## Module summary", "",
              "Summaries explain purpose and content. They are non-normative; "
              "the claim statements, proofs and declared assumptions remain "
              "authoritative.", ""]
    abstract = repo.modules[module_id].meta.get("abstract")
    if abstract:
        lines += ["**Non-normative summary.** " + prose(str(abstract), module_id), ""]
    lines += ["## Start here", "",
              "Open [overview.svg](overview.svg) in a browser; click a group to open "
              "its detailed graph. The matrix keeps dense dependencies legible in "
              "print. SVG is zoomable and needs no server or extension. "
              "Repository previews may require **Raw** or downloading first.", "",
              "The [standalone overview PDF](overview.pdf) shows the same matrix. "
              "Group numbers are the section numbers of the contract PDF, and a "
              "claim's number there is its section's number followed by its place "
              "in the section; E marks external modules. "
              "Rows depend on columns: U = uses, A = assumes, UA = both. Blank = no "
              "declared edge between groups; internal edges are omitted. "
              "The [full group arrow graph](groups.svg) shows the same cross-group "
              "relationships; grouping can introduce cycles.", "",
              "Arrows point **from a claim to its prerequisite**. Solid = `uses`; "
              "dashed amber = `assumes`. Mentions are excluded. Node labels include "
              "the current status; colour is only a redundant aid. Dashed boundary "
              "boxes name external prerequisites whose own edges are omitted. "
              "Each claim offers **TeX source** and **Rendered PDF** links; the latter "
              "opens its claim in the owning core's contract (viewer support for PDF "
              "named destinations varies). Pending references are "
              "counted, never invented as resolved edges. These views do not prove "
              "that the declarations are complete or correct.", "",
              "[All local claims, with boundary nodes](claims.svg) · "
              "[DOT source](claims.dot)", "", "## Sections and claim index", ""]
    structure = contract_sections(repo, module_id)
    for part in structure.parts:
        lines += [f"## Part {roman(part.number)}: {part.title}", ""]
        if part.intro:
            lines += ["**Non-normative summary.** " + prose(part.intro, part.module_id),
                      ""]
        for section in part.sections:
            stem, title, ids = groups[section.number - 1]
            sources[directory / f"{stem}.dot"] = claim_dot(repo, set(ids), directory,
                                                           title)
            lines += [f"### {section.number} {section.title}", "",
                      f"[Dependency view]({stem}.svg)", ""]
            if section.abstract:
                lines += ["**Non-normative summary.** "
                          + prose(section.abstract, section.module_id), ""]
            for cid in ids:
                claim = repo.claims[cid]
                label = plain_title(str(claim.header.get("title", claim.label)))
                label = label.replace("|", r"\|")
                path = Path(os.path.relpath(claim.path, directory)).as_posix()
                number = section.claim_number(cid)
                lines.append(f"- {number} [`{cid}`]({path}): {label} "
                             f"([PDF](../contract.pdf#nameddest={claim_anchor(cid)}))")
                if claim.header.get("summary"):
                    lines += ["", "  **Non-normative summary.** "
                              + prose(str(claim.header["summary"]), claim.module_id),
                              ""]
            lines.append("")
    sources[directory / "README.md"] = "\n".join(lines).rstrip() + "\n"
    return sources


def roman(number: int) -> str:
    """Write a part number as LaTeX prints it (I, II, III, IV, ...)."""
    numerals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
                (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"),
                (4, "IV"), (1, "I")]
    out = ""
    for value, numeral in numerals:
        while number >= value:
            out += numeral
            number -= value
    return out


def overview_data(repo: Repo, groups: list[tuple[str, str, list[str]]]) -> tuple[
        list[tuple[str, str]], dict[str, str], dict[tuple[str, str], set[str]]]:
    """Project claim edges onto the sections: the matrix's rows, columns and cells."""
    owner = {cid: stem for stem, _, ids in groups for cid in ids}
    external = sorted({repo.claims[target].module_id for cid in owner
                       for target, _ in dependencies(repo, cid) if target not in owner})
    columns = [(stem, title) for stem, title, _ in groups]
    columns += [("external:" + mid, mid + " (external)") for mid in external]
    numbers = {stem: title.split(" ", 1)[0] for stem, title, _ in groups}
    numbers.update({"external:" + mid: f"E{i}"
                    for i, mid in enumerate(external, start=1)})
    edges: dict[tuple[str, str], set[str]] = {}
    for cid, source in owner.items():
        for target, kind in dependencies(repo, cid):
            dest = owner.get(target, "external:" + repo.claims[target].module_id)
            if source != dest:
                edges.setdefault((source, dest), set()).add(kind)
    return columns, numbers, edges


def overview_matrix(repo: Repo, module_id: str,
                    groups: list[tuple[str, str, list[str]]]) -> str:
    """Keep a dense group graph readable on paper without dropping cross edges."""
    columns, numbers, edges = overview_data(repo, groups)
    table = ['<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5">',
             '<TR><TD ALIGN="LEFT"><B>Group / prerequisite column</B></TD>']
    table += [f'<TD><B>{number}</B></TD>' for number in numbers.values()]
    table += ['</TR>']
    for stem, title in columns:
        label = (numbers[stem] + " " if stem.startswith("external:") else "") + title
        label = escape(wrapped(label, 34)).replace("\n", '<BR/>')
        href = (f' HREF="{stem}.svg" TARGET="_top"'
                if not stem.startswith("external:") else "")
        table.append(f'<TR><TD ALIGN="LEFT"{href}>{label}</TD>')
        for dest, _ in columns:
            kinds = edges.get((stem, dest), set())
            cell = (("U" if "uses" in kinds else "")
                    + ("A" if "assumes" in kinds else ""))
            if stem.startswith("external:") or stem == dest:
                cell, colour = "-", "#eeeeee"
            else:
                colour = "#fff0d6" if "assumes" in kinds else "#edf3f8"
            table.append(f'<TD BGCOLOR="{colour}">{cell or " "}</TD>')
        table.append('</TR>')
    table.append('</TABLE>')
    legend = (module_id + ": reading-group dependencies\nRows depend on columns. "
              "U = uses; A = assumes; UA = both.\n"
              "Numbers match PDF contents; E = external module.\n"
              "Blank: no cross-group edge. Grey: internal or external detail omitted.")
    return ("digraph overview {\n  graph [pad=0.1, fontname=\"Arial\", fontsize=11, "
            f"labelloc=t, label={quoted(legend)}];\n"
            "  node [shape=plain, fontname=\"Arial\", fontsize=11];\n"
            "  overview [label=<" + "".join(table) + ">];\n}\n")


def module_map_source(root: Path, building: str | Collection[str] | None = None,
                      ) -> dict[Path, str]:
    """Show core module relationships from the registry, including future modules.

    ``building`` names the core or cores whose graph index this run writes: a
    node links its module's index when that exists or is being written, so
    the map is the same whether it is rendered before the indexes or after.
    """
    built = {building} if isinstance(building, str) else set(building or ())
    registry = root / "spec" / "modules.yaml"
    if not registry.is_file():
        return {}
    cores = load_yaml_mapping(registry.read_text(encoding="utf-8")).get("cores", [])
    lines = ["digraph modules {", "  rankdir=LR;",
             '  graph [fontname="Arial", fontsize=14, labelloc=t, pad=0.3, '
             'label="Core module map\\nArrow: module -> declared dependency '
             '(allowed imports, not execution order or individual proof edges).\\n'
             'Dashed boxes: no local claim bundle. '
             'Submodules: see each module graph index."];',
             '  node [shape=box, style="rounded,filled", fillcolor="#edf3f8", '
             'fontname="Arial", fontsize=12, margin=0.2];',
             '  edge [color="#526777"];']
    for core in cores:
        mid = str(core["id"])
        present = (root / "spec" / "modules" / mid / "module.yaml").is_file()
        label = mid + "\n" + str(core.get("title", mid))
        attrs = "" if present else ', style="rounded,dashed", fillcolor="white"'
        has_index = (root / "spec/modules" / mid / "graphs/README.md").is_file()
        link = (f"modules/{mid}/graphs/README.md" if has_index or mid in built
                else f"modules/{mid}/module.yaml" if present else "modules.yaml")
        lines.append(f"  {quoted(mid)} [label={quoted(label)}, "
                     f"URL={quoted(link)}, target=\"_top\"{attrs}];")
        for dep in core.get("depends_on", []):
            lines.append(f"  {quoted(mid)} -> {quoted(str(dep))};")
    lines += ["}"]
    return {root / "spec" / "module-graph.dot": "\n".join(lines) + "\n"}


def find_dot() -> str:
    """Find Graphviz on PATH or in its standard Windows installation."""
    found = shutil.which("dot")
    if found:
        return found
    candidate = Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) \
        / "Graphviz" / "bin" / "dot.exe"
    if candidate.is_file():
        return str(candidate)
    raise ValueError("Graphviz dot not found; install Graphviz and put dot on PATH. "
                     "--no-pdf writes only TeX, DOT and the reading index.")


#: The build date of every generated PDF (2025-09-28 00:00 UTC), fixed so that
#: a rebuild of unchanged sources gives the same bytes (pdfTeX and cairo read
#: it; FORCE_SOURCE_DATE makes pdfTeX use it for the document dates too).
BUILD_EPOCH = "1759017600"


def reproducible_env() -> dict[str, str]:
    """Return the environment for latexmk and Graphviz: the fixed build date."""
    return {**os.environ, "SOURCE_DATE_EPOCH": BUILD_EPOCH, "FORCE_SOURCE_DATE": "1"}


def render_dot(source: Path, target: Path) -> None:
    """Render with Graphviz; the output extension selects SVG or PDF.

    An SVG is written with LF line ends (Graphviz on Windows writes CRLF,
    which the repository's text files never carry).
    """
    result = subprocess.run([find_dot(), "-T" + target.suffix[1:], str(source),
                             "-o", str(target)], capture_output=True, text=True,
                            encoding="utf-8", check=False, env=reproducible_env())
    if result.returncode:
        raise ValueError(f"Graphviz failed on {source}: {result.stderr.strip()}")
    if target.suffix == ".svg":
        data = target.read_bytes()
        if b"\r\n" in data:
            target.write_bytes(data.replace(b"\r\n", b"\n"))


def export_graph(repo: Repo, target: Path, wanted: str | None,
                 focus: str | None = None) -> None:
    """Export a module neighbourhood or a full focused prerequisite closure."""
    if focus is not None and focus not in repo.claims:
        raise ValueError(f"--focus '{focus}' is not a claim id")
    selected = prerequisite_closure(repo, focus) if focus else {
        cid for cid, claim in repo.claims.items() if in_scope(claim.module_id, wanted)}
    title = f"Prerequisites of {focus}" if focus else (wanted or "All claims")
    if target.suffix not in {".dot", ".svg", ".pdf"}:
        raise ValueError("--graph output must end in .dot, .svg or .pdf")
    source = target if target.suffix == ".dot" else target.with_suffix(".dot")
    source.write_text(claim_dot(repo, selected, target.parent, title), encoding="utf-8")
    if target != source:
        render_dot(source, target)
