#!/usr/bin/env python3
r"""Motivation: a readable contract that nobody maintains by hand.

Splitting a module's mathematics into one file per claim buys a computable
re-review scope (`harness/check_claims.py`), but a reader still needs the
whole argument in one document, in the author's intended order. Maintaining
that document alongside the claim files would mean authoring every statement
twice, and a second copy drifts, so a reader cannot tell which copy is
the contract.
This tool generates it instead. `spec/modules/<id>/contract.tex` is derived,
checked in only so that a reader without the tooling can read it, and
`--check` is what keeps it from drifting.

The PDF next to it, `contract.pdf`, is the human's review copy (generated
after every contract revision and placed where a reviewer finds them; tracked
next to the tex so that every clone and the hosted repository carry the copy
that was reviewed). It is built
here, by the same command that writes the tex, so that the two cannot drift
apart by omission; `--check` also fails when the PDF is missing or older than
the tex. Uncommitted files are compared by modification time; committed,
unmodified files by the time of their last commit, because a checkout writes
files in index order and gives the PDF an earlier timestamp than the tex it
was built from. A digest reads its contract only through `contract.aux`, so
its `contract.tex` input is compared in `aux_view` (labels and what numbers
them): a "Used by" line changed by another module's edit would call digests
stale whose rebuild is byte-identical.

Usage:
    python -m harness.assemble_contract <module-id> [--repo .] [--check] [--no-pdf]
    python -m harness.assemble_contract --all [--repo .] [--check] [--no-pdf]
    (either with [--code-url URL], the base of every code and registry link,
    by default the hosted repository's main branch)

`--check` writes nothing and exits 1 if the tex on disk differs from what
would be generated, or if the PDF is missing or stale. `--no-pdf` skips the
PDF (writing or checking); without a TeX distribution the tool says what to
install rather than pretending the PDF exists.

`--all` is what an author runs after a
claim change: every core module, the module map and the spec-wide overview
(`harness/contract_overview.py`), with only what changed rebuilt. It exists
because a claim edit reaches other contracts (a consumer prints the claim's
title and status) and a hand-picked list of modules to rebuild misses some,
while rebuilding everything rewrote untouched outputs. So a generated text is
written only when its bytes differ from the file on disk; a graph render only
when its `.dot` changed or the render is missing or stale, never because
Graphviz changed; a PDF only when it is not current for its inputs. SVGs are
written with LF (Graphviz on Windows writes CRLF), and latexmk and Graphviz
run with a fixed `SOURCE_DATE_EPOCH` and `FORCE_SOURCE_DATE=1`, so a rebuild of
an unchanged source gives the same bytes and two consecutive runs leave git
status unchanged. Conversely every generated tex sets the PDF's trailer
identifier to a digest of its own text (`with_trailer_id`), so a change of
the tex always changes the PDF's bytes: a preamble macro the body does not
yet use would leave the PDFs byte-identical, git could not record their
rebuild, and the freshness check would call them stale. A module named
alone always rebuilds its two PDFs.

`--all` also regenerates the claim-closure table a run record reads
(`harness/generate_claim_closure.py`; `--check` checks it), because that table
carries every assumption's and every cited claim's plain title, summary and
`user_statement` for the key-rate report: an editorial summary edit that left it stale
would ship a report
quoting text the contract no longer has. It is skipped in a tree that ships
no table (a fixture) and, with a note, while check_claims reports errors.

The layout follows `spec/style.md` sections
3 to 6: the structure (parts, sections, claim numbers) is
`harness/contract_structure.py`, shared with the graphs so that a number in a
graph is the number in the PDF; the preamble, parts, sections, claims and
meta lines are `harness/contract_render.py`; the front and back matter are
`harness/contract_frontmatter.py`; the statements digest is
`harness/contract_digest.py`. This file is the command line and the build: it
joins them, writes the tex, the digest, the graph sources and the module map,
and runs `latexmk` (which also runs bibtex and, for the index of defined
terms, makeindex), the digest right after its contract, whose `.aux` it reads
through xr-hyper, and only then cleans both. The graph index, DOT, SVG and
overview PDF are generated in the same operation; freshness checks prevent
presenting an old graph with a new claim. The authored processing flowchart
stays in design.md, linked from the PDF.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from harness.check_claims import Repo, load_repo
from harness.claim_graph import (
    graph_sources,
    module_map_source,
    render_dot,
    reproducible_env,
)
from harness.contract_digest import render_digest
from harness.contract_frontmatter import back_tex, front_tex
from harness.contract_overview import (
    MODULE_MAP_PDF,
    OVERVIEW_DIR,
    core_order,
    overview_sources,
)
from harness.contract_render import (
    GITHUB,
    AssemblyError,
    Contract,
    body_tex,
    declare_xrefs,
    preamble,
)
from harness.generate_claim_closure import OUTPUT as CLOSURE_TABLE
from harness.generate_claim_closure import regenerate as regenerate_closure

__all__ = ["AssemblyError", "main", "pdf_is_current", "render"]


LATEXMK_MISSING = ("latexmk not found: install a TeX distribution that provides "
                   "latexmk and pdflatex (TeX Live or MiKTeX) so that the review "
                   "PDF is built, or pass --no-pdf and leave the PDF to a machine "
                   "that has one")


def git_output(args: list[str], cwd: Path) -> str | None:
    """Return git's stdout for ``args`` run in ``cwd``, or None if git cannot answer."""
    git = shutil.which("git")
    if git is None:
        return None
    try:
        # UTF-8, not the locale: the tree's sources are UTF-8 (references.bib
        # has accented names), and a file read back through git show must
        # compare equal to the same file read from disk.
        proc = subprocess.run([git, *args], cwd=cwd, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              check=False)
    except OSError:
        return None
    return proc.stdout if proc.returncode == 0 else None


def with_trailer_id(tex: str) -> str:
    r"""Return ``tex`` with ``\pdftrailerid`` set to a digest of it, after the class."""
    head, sep, rest = tex.partition("\n\\documentclass")
    if not sep:
        return tex
    line, _, body = rest.partition("\n")
    digest = hashlib.sha256(tex.encode("utf-8")).hexdigest()[:32]
    return f"{head}{sep}{line}\n\\pdftrailerid{{{digest}}}\n{body}"


def pdf_is_current(tex: Path, pdf: Path,
                   view: Callable[[str], str] | None = None) -> tuple[bool, str]:
    """Whether ``pdf`` is at least as new as ``tex``; the reason when it is not.

    Uncommitted or untracked files are compared by modification time. Two
    committed, unmodified files are compared by the time of their last commit,
    because a checkout writes files in index order and gives the PDF an earlier
    timestamp than the tex it was built from. A source committed after its
    output still counts as current when its content is the one it had at the
    output's commit: a source edited and restored leaves an identical build,
    which git cannot record as a newer commit. ``view``, when given, reduces the
    source to the part the
    output reads before that comparison: a reference registered for one
    contract changes ``references.bib`` but not the PDFs that do not cite it,
    whose rebuild is then byte-identical, and a comment-only edit
    of ``spec/macros.tex`` changes no PDF at all.
    """
    if not pdf.is_file():
        return False, "does not exist"
    by_mtime = (pdf.stat().st_mtime >= tex.stat().st_mtime,
                f"is older than {tex.name}")
    names = [tex.name, Path(os.path.relpath(pdf, tex.parent)).as_posix()]
    status = git_output(["status", "--porcelain", "--", *names], tex.parent)
    if status is None or status.strip():
        return by_mtime
    stamps = [git_output(["log", "-1", "--format=%ct", "--", name], tex.parent)
              for name in names]
    if any(stamp is None or not stamp.strip() for stamp in stamps):
        return by_mtime
    tex_commit, pdf_commit = (int(stamp.strip()) for stamp in stamps)  # type: ignore[union-attr]
    if pdf_commit >= tex_commit:
        return True, ""
    built_at = git_output(["log", "-1", "--format=%H", "--", names[1]], tex.parent)
    source_then = (git_output(["show", f"{built_at.strip()}:./{tex.name}"], tex.parent)
                   if built_at else None)
    source_now = tex.read_text(encoding="utf-8")
    if view is not None and source_then is not None:
        source_then, source_now = view(source_then), view(source_now)
    if source_then is not None and source_then == source_now:
        return True, ""
    return False, f"was built from an earlier commit of {tex.name}"


def latexmk(tex: Path) -> str | None:
    """Compile ``tex`` in its directory with the fixed build date; an error or None."""
    run = [str(shutil.which("latexmk")), "-pdf", "-cd", "-interaction=nonstopmode",
           "-halt-on-error", "-silent", tex.name]
    proc = subprocess.run(run, cwd=tex.parent, capture_output=True, text=True,
                          check=False, env=reproducible_env())
    if proc.returncode == 0:
        return None
    log = tex.with_suffix(".log")
    tail = proc.stdout.strip().splitlines()[-15:]
    return (f"latexmk failed on {tex.as_posix()} (exit {proc.returncode}); "
            f"see {log.as_posix()}\n" + "\n".join(tail))


def build_pdfs(texs: list[Path]) -> str | None:
    """Compile ``texs`` in order, then clean their auxiliary files.

    A digest reads its contract's ``.aux`` through xr-hyper, so the contract
    is compiled first and nothing is cleaned until both are built. On a
    failure the files stay, the log included, for the reader of the error.
    """
    if shutil.which("latexmk") is None:
        return LATEXMK_MISSING
    for tex in texs:
        error = latexmk(tex)
        if error is not None:
            return error
    for tex in texs:
        subprocess.run([str(shutil.which("latexmk")), "-c", "-cd", "-silent", tex.name],
                       cwd=tex.parent, capture_output=True, text=True, check=False)
    return None


def write_changed(sources: dict[Path, str]) -> set[Path]:
    """Write the sources whose bytes differ from the file on disk; return those.

    An unchanged file is not touched, so its modification time, and with it
    every freshness judgement that reads it, stays as it was.
    """
    changed: set[Path] = set()
    for path, content in sources.items():
        data = content.encode("utf-8")
        if path.is_file() and path.read_bytes() == data:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        changed.add(path)
    return changed


def renders_of(dot: Path) -> list[Path]:
    """Return a graph's renders: its SVG, and a PDF where one is used."""
    outputs = [dot.with_suffix(".svg")]
    if dot.stem in ("overview", "module-graph"):
        outputs.append(dot.with_suffix(".pdf"))
    return outputs


def render_graphs(dots: list[Path], changed: set[Path]) -> list[Path]:
    """Render the graphs whose ``.dot`` changed or whose render is missing or stale.

    A render whose ``.dot`` is byte-identical to the file on disk and current
    is left alone, so a Graphviz upgrade never rewrites an untouched view.
    """
    rendered: list[Path] = []
    for dot in dots:
        for output in renders_of(dot):
            if dot in changed or not pdf_is_current(dot, output)[0]:
                render_dot(dot, output)
                rendered.append(output)
    return rendered


def stale_graphs(dots: list[Path]) -> list[str]:
    """Say which renders are missing or older than their ``.dot``."""
    found = []
    for dot in dots:
        for output in renders_of(dot):
            current, reason = pdf_is_current(dot, output)
            if not current:
                found.append(f"{output.as_posix()} ({reason}); rebuild graphs")
    return found


CITE = re.compile(r"\\(?:no)?cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}")
BIB_ENTRY = re.compile(r"^@\w+\{\s*([^,\s]+)\s*,", re.M)


def cited_entries(bib: str, texs: list[Path]) -> str:
    """Return the entries of ``bib`` that ``texs`` cite, in key order."""
    keys = {key.strip() for tex in texs
            for group in CITE.findall(tex.read_text(encoding="utf-8"))
            for key in group.split(",")}
    starts = [(m.start(), m.group(1)) for m in BIB_ENTRY.finditer(bib)]
    ends = [start for start, _ in starts[1:]] + [len(bib)]
    entries = {key: bib[start:end].strip()
               for (start, key), end in zip(starts, ends, strict=True)}
    return "\n".join(entries[key] for key in sorted(keys) if key in entries)


TEX_COMMENT = re.compile(r"[ \t]*(?<!\\)%[^\n]*\n?")


def without_comments(tex: str) -> str:
    r"""Return TeX source without its comments, which never reach a build.

    A comment-only edit of spec/macros.tex rebuilds every PDF byte-identically,
    which git cannot record as a newer commit, so the freshness check called
    those PDFs stale. A ``%`` ends the line for TeX, newline
    included, and the blanks before it go with it (an indented continuation
    line of a comment counts); an escaped ``\%`` is text and
    stays.
    """
    return TEX_COMMENT.sub("", tex)


MACRO_DEFINITION = re.compile(
    r"\\(?:(?:new|renew|provide)command\*?\s*\{?\\([A-Za-z]+)"
    r"|DeclareMathOperator\*?\s*\{?\\([A-Za-z]+)"
    r"|def\s*\\([A-Za-z]+)|let\s*\\([A-Za-z]+))")
CONTROL_WORD = re.compile(r"\\([A-Za-z]+)")


def used_macros(macros: str, texs: list[Path]) -> str:
    r"""Return ``macros`` reduced to the definitions ``texs`` can reach.

    A definition of spec/macros.tex reaches a build only where a control word
    of the build's sources names it, directly or through another reached
    definition. An edit of a macro no contract uses (the shared notation
    renaming a symbol of another module) rebuilds the other PDFs
    byte-identically, which git cannot record as a newer commit, so the
    freshness check called them stale. The text before the first definition
    is kept whole; comments are dropped as in ``without_comments``, and so are
    blank lines, which the preamble that reads the file ignores (removing a
    block of comments otherwise left its blank lines as a difference).
    """
    text = "".join(line for line in without_comments(macros).splitlines(keepends=True)
                   if line.strip())
    found = [(match.start(), next(name for name in match.groups() if name))
             for match in MACRO_DEFINITION.finditer(text)]
    if not found:
        return text
    ends = [start for start, _ in found[1:]] + [len(text)]
    definitions = [(name, text[start:end])
                   for (start, name), end in zip(found, ends, strict=True)]
    bodies: dict[str, list[str]] = {}
    for name, body in definitions:
        bodies.setdefault(name, []).append(body)
    pending = {word for tex in texs
               for word in CONTROL_WORD.findall(tex.read_text(encoding="utf-8"))}
    used: set[str] = set()
    while pending:
        word = pending.pop()
        if word in used or word not in bodies:
            continue
        used.add(word)
        for body in bodies[word]:
            pending.update(CONTROL_WORD.findall(body))
    kept = "".join(body for name, body in definitions if name in used)
    return text[:found[0][0]] + kept


TRAILER_ID = re.compile(r"\\pdftrailerid\{[^}]*\}\n?")
#: What fixes a label's entry in a contract's ``.aux``: the label itself, and
#: everything that steps a counter or a hyperref anchor before it.
AUX_TOKEN = re.compile(
    r"\\(?:label|tag\*?)\{[^}]*\}"
    r"|\\begin\{(?:enumerate|itemize|description)\}(?:\[[^\]]*\])?"
    r"|\\(?:begin|end)\{[^}]*\}"
    r"|\\item(?:\[[^\]]*\])?(?![A-Za-z])"
    r"|\\(?:setcounter|addtocounter|numberwithin)\{[^}]*\}\{[^}]*\}"
    r"|\\(?:refstepcounter|stepcounter)\{[^}]*\}"
    r"|\\(?:part|chapter|section|subsection|subsubsection|paragraph|subparagraph)"
    r"\*?(?![A-Za-z])"
    r"|\\(?:appendix|phantomsection|claimanchor|footnote|caption|nonumber|notag)"
    r"(?![A-Za-z])")


def aux_view(tex: str) -> str:
    r"""Return the part of a contract's tex that its digest reads, through the ``.aux``.

    The digest takes from ``contract.aux`` (xr-hyper) each label's number and
    link anchor, never its page or its text. Those are fixed by the preamble
    (counter setup, theorem styles) and, in the body, by the ordered sequence
    of labels, sectioning commands, environment openings and closings (claims,
    displays, lists with their label format) and the other commands that step
    a counter or an anchor (``\item``, ``\tag``, ``\phantomsection`` and the
    ``\claimanchor`` that wraps it, ``\footnote``, ``\caption``,
    ``\setcounter``). This keeps the preamble, without the trailer id (a
    digest of the whole tex), and that sequence of the body. A meta line
    ("Used by", "Assumed by") holds none of it: a consumer elsewhere gaining
    or losing a claim changes only meta lines of other contracts, and the freshness
    check would call their
    digests stale although a rebuild is byte-identical. A
    deliberate over-approximation: a remark gaining a list also counts,
    since hyperref's item anchors are numbered through the document.
    """
    text = without_comments(tex)
    head, begin, body = text.partition("\\begin{document}")
    tokens = "\n".join(match.group() for match in AUX_TOKEN.finditer(body))
    return TRAILER_ID.sub("", head) + begin + "\n" + tokens


def stale_pdf(pdf: Path, inputs: list[Path],
              views: dict[Path, Callable[[str], str]] | None = None) -> str | None:
    """Say why ``pdf`` is not current for ``inputs`` (its tex first), or None.

    A ``.tex`` input is compared without comments, ``spec/macros.tex`` by the
    definitions the other texs reach (``used_macros``; without other texs,
    like any tex) and a ``.bib`` input by
    the entries the texs cite, unless ``views`` names another view for it (a
    digest's ``contract.tex``: ``aux_view``).
    """
    texs = [source for source in inputs if source.suffix == ".tex"]
    others = [source for source in texs if source.name != "macros.tex"]
    for source in inputs:
        if not source.is_file():
            return f"{pdf.as_posix()}: missing input {source.as_posix()}"
        view: Callable[[str], str] | None = (
            (views or {}).get(source)
            or ((lambda text: cited_entries(text, texs)) if source.suffix == ".bib"
                else (lambda text: used_macros(text, others))
                if source.name == "macros.tex" and others
                else without_comments if source.suffix == ".tex" else None))
        current, reason = pdf_is_current(source, pdf, view)
        if not current:
            return f"{pdf.as_posix()} {reason}"
    return None


class Unit:
    """One core module's generated files: contract, digest, graphs."""

    def __init__(self, root: Path, repo: Repo, core: str, *,
                 code_url: str = GITHUB) -> None:
        """Render every generated text of the module (nothing is written)."""
        self.root, self.core = root, core
        directory = root / "spec" / "modules" / core
        if not (directory / "module.yaml").is_file():
            raise AssemblyError(f"spec/modules/{core}/module.yaml: no module.yaml")
        contract = Contract(root, repo, core, code_url=code_url)
        self.tex = directory / "contract.tex"
        self.digest = directory / "digest.tex"
        self.sources = {self.tex: with_trailer_id(render_contract(contract)),
                        self.digest: with_trailer_id(render_digest(contract)),
                        **graph_sources(root, core, repo)}
        graph_dir = directory / "graphs"
        expected = {p.name for p in self.sources if p.parent == graph_dir}
        expected |= {p.with_suffix(".svg").name for p in self.sources
                     if p.parent == graph_dir and p.suffix == ".dot"}
        # A removed group must not leave an obsolete, apparently current view.
        self.obsolete = [p for p in graph_dir.glob("group-*")
                         if re.fullmatch(r"group-\d+(?:-[a-z0-9-]+)?\.(dot|svg)",
                                         p.name) and p.name not in expected]

    @property
    def dots(self) -> list[Path]:
        """The module's graph sources."""
        return [path for path in self.sources if path.suffix == ".dot"]

    def pdf_inputs(self) -> dict[Path, list[Path]]:
        """Each PDF with the files it is built from, its own tex first."""
        shared = [self.root / "spec" / "macros.tex",
                  self.root / "refs" / "references.bib"]
        return {self.tex.with_suffix(".pdf"): [self.tex, *shared],
                self.digest.with_suffix(".pdf"): [self.digest, self.tex, *shared]}

    def stale_pdf(self, pdf: Path, inputs: list[Path]) -> str | None:
        """Say why one of the module's PDFs is not current, or None.

        The digest reads its contract only through the ``.aux``, so its
        ``contract.tex`` input is compared in ``aux_view``.
        """
        views: dict[Path, Callable[[str], str]] | None = (
            {self.tex: aux_view} if pdf == self.digest.with_suffix(".pdf") else None)
        return stale_pdf(pdf, inputs, views)

    def stale(self, no_pdf: bool) -> list[str]:
        """Say what is stale: a generated text, an obsolete view, a render, a PDF."""
        found = [f"obsolete generated group view {path.as_posix()}; rebuild"
                 for path in self.obsolete]
        for path, content in self.sources.items():
            if not path.is_file():
                found.append(f"{path.as_posix()} does not exist")
            elif path.read_text(encoding="utf-8") != content:
                found.append(f"{path.as_posix()} differs from its sources")
        if not no_pdf and not found:
            for pdf, inputs in self.pdf_inputs().items():
                reason = self.stale_pdf(pdf, inputs)
                if reason:
                    found.append(reason + "; run the assembler without --check to "
                                 "rebuild it")
            found += stale_graphs(self.dots)
        return found

    def build(self, no_pdf: bool, force: bool) -> tuple[list[str], str | None]:
        """Write what changed and rebuild what is not current; say what was done.

        ``force`` rebuilds the two PDFs even when they are current (a single
        module asked for by name). Returns the paths written and an error.
        """
        changed = write_changed(self.sources)
        for path in self.obsolete:
            path.unlink()
        done = [path.as_posix() for path in sorted(changed)]
        if no_pdf:
            return done, None
        try:
            done += [path.as_posix() for path in render_graphs(self.dots, changed)]
        except (ValueError, OSError) as exc:
            return done, str(exc)
        pdfs = self.pdf_inputs()
        if (force or self.tex in changed or self.digest in changed
                or any(self.stale_pdf(pdf, inputs) for pdf, inputs in pdfs.items())):
            error = build_pdfs([self.tex, self.digest])
            if error is not None:
                return done, error
            done += [pdf.as_posix() for pdf in pdfs]
        return done, None


def render(root: Path, module_id: str, repo: Repo | None = None, *,
           code_url: str = GITHUB) -> str:
    """Render the whole contract of one core module as TeX."""
    if not (root / "spec" / "modules" / module_id / "module.yaml").is_file():
        raise AssemblyError(f"spec/modules/{module_id}/module.yaml: no module.yaml")
    if repo is None:
        repo = load_repo(root)
    return render_contract(Contract(root, repo, module_id, code_url=code_url))


def render_contract(contract: Contract) -> str:
    """Join the preamble, the front matter, the parts and the back matter."""
    meta = contract.repo.modules[contract.core].meta
    title = str(meta.get("title", contract.core))
    version = str(meta.get("version", "0.0.0"))
    return (preamble(f"{title} -- contract {version}")
            + declare_xrefs(contract.repo, contract.core)
            + front_tex(contract) + body_tex(contract) + back_tex(contract))


def overview_step(root: Path, repo: Repo, check: bool, no_pdf: bool,
                  map_changed: bool) -> tuple[list[str], list[str]]:
    """Check or build the spec-wide overview; return (done or stale, errors)."""
    directory = root / OVERVIEW_DIR
    intro = directory / "intro.tex"
    if not intro.is_file():
        return [], [] if check else [f"note: no {intro.as_posix()}; overview skipped"]
    tex = directory / "overview.tex"
    sources = overview_sources(root, repo)
    sources[tex] = with_trailer_id(sources[tex])
    pdf = tex.with_suffix(".pdf")
    inputs = [tex, directory / "chain.tex", intro, root / "spec" / "macros.tex"]
    if (root / "spec" / "modules.yaml").is_file():     # the module map is drawn
        inputs.append(root / MODULE_MAP_PDF)
    if check:
        found = [f"{path.as_posix()} differs from its sources" for path, content
                 in sources.items()
                 if not path.is_file() or path.read_text(encoding="utf-8") != content]
        if not no_pdf and not found:
            reason = stale_pdf(pdf, inputs)
            found += [reason] if reason else []
        return found, []
    changed = write_changed(sources)
    done = [path.as_posix() for path in sorted(changed)]
    if no_pdf:
        return done, []
    if changed or map_changed or stale_pdf(pdf, inputs):
        error = build_pdfs([tex])
        if error is not None:
            return done, [error]
        done.append(pdf.as_posix())
    return done, []


def closure_step(root: Path, repo: Repo, check: bool) -> tuple[list[str], list[str]]:
    """Check or regenerate the claim-closure table; return (done or stale, errors).

    Skipped where the tree ships no table (a fixture), and with a note while
    the claim graph has check_claims errors, on which the generator writes
    nothing.
    """
    if not (root / CLOSURE_TABLE).is_file():
        return [], []
    if repo.errors:
        return [], [f"note: {CLOSURE_TABLE.as_posix()} not regenerated: "
                    f"{len(repo.errors)} check_claims error(s)"]
    ok, lines = regenerate_closure(root, repo, check)
    if check:
        return ([] if ok else [" ".join(lines)]), []
    return (lines if ok else []), ([] if ok else [" ".join(lines)])


def assemble_all(root: Path, check: bool, no_pdf: bool,
                 code_url: str = GITHUB) -> int:
    """Check or rebuild every core module, its digest, the module map and the overview.

    Only what changed is written or rebuilt: a generated text whose bytes
    differ from the file on disk, a render or PDF that is missing or older
    than an input.
    """
    try:
        repo = load_repo(root)
        cores = core_order(root, repo)
        units = [Unit(root, repo, core, code_url=code_url) for core in cores]
        map_sources = module_map_source(root, building=cores)
    except (AssemblyError, ValueError, OSError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not no_pdf and not check and shutil.which("latexmk") is None:
        print(f"error: {LATEXMK_MISSING}", file=sys.stderr)
        return 1
    stale: list[str] = []
    errors: list[str] = []
    map_changed = False
    for unit in units:
        if check:
            stale += unit.stale(no_pdf)
            continue
        done, error = unit.build(no_pdf, force=False)
        print(f"{unit.core}: " + (", ".join(done) if done else "up to date"))
        if error:
            errors.append(error)
    map_dots = [path for path in map_sources if path.suffix == ".dot"]
    if check:
        stale += [f"{path.as_posix()} differs from its sources"
                  for path, content in map_sources.items()
                  if not path.is_file() or path.read_text(encoding="utf-8") != content]
        if not no_pdf:
            stale += stale_graphs(map_dots)
    else:
        changed = write_changed(map_sources)
        map_changed = bool(changed)
        if not no_pdf:
            try:
                map_changed |= bool(render_graphs(map_dots, changed))
            except (ValueError, OSError) as exc:
                errors.append(str(exc))
    found, overview_errors = overview_step(root, repo, check, no_pdf, map_changed)
    errors += overview_errors
    closure, closure_errors = closure_step(root, repo, check)
    if check:
        stale += found + closure
        for note in closure_errors:
            print(note, file=sys.stderr)
        for line in stale:
            print(f"stale: {line}", file=sys.stderr)
        if not stale:
            unchecked = " (claim closure not checked)" if closure_errors else ""
            print(f"up to date: {len(units)} contracts, their digests and the "
                  f"overview{unchecked}")
        return 1 if stale else 0
    errors += closure_errors
    print("overview: " + (", ".join(found) if found else "up to date"))
    if closure:
        print("claim closure: " + "; ".join(closure))
    for error in errors:
        print(("" if error.startswith("note:") else "error: ") + error,
              file=sys.stderr)
    return 1 if any(not error.startswith("note:") for error in errors) else 0


def assemble_one(root: Path, core: str, check: bool, no_pdf: bool,
                 code_url: str = GITHUB) -> int:
    """Check or build one core module: its contract, digest, graphs and module map."""
    try:
        repo = load_repo(root)
        unit = Unit(root, repo, core, code_url=code_url)
        map_sources = module_map_source(root, building=core)
    except (AssemblyError, ValueError, OSError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if check:
        stale = unit.stale(no_pdf)
        stale += [f"{path.as_posix()} differs from its sources"
                  for path, content in map_sources.items()
                  if not path.is_file() or path.read_text(encoding="utf-8") != content]
        for line in stale:
            print(f"stale: {line}", file=sys.stderr)
        if stale:
            return 1
        print(f"up to date: {unit.tex.as_posix()}")
        if not no_pdf:
            print(f"up to date: {unit.tex.with_suffix('.pdf').as_posix()}")
        return 0
    if not no_pdf and shutil.which("latexmk") is None:
        write_changed({**unit.sources, **map_sources})
        print(f"error: {LATEXMK_MISSING}", file=sys.stderr)
        return 1
    _, error = unit.build(no_pdf, force=True)
    changed = write_changed(map_sources)
    if not no_pdf and error is None:
        try:
            render_graphs([path for path in map_sources if path.suffix == ".dot"],
                          changed)
        except (ValueError, OSError) as exc:
            error = str(exc)
    print(f"wrote {unit.tex.as_posix()}")
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if not no_pdf:
        print(f"wrote {unit.tex.with_suffix('.pdf').as_posix()}")
        print(f"wrote {unit.digest.with_suffix('.pdf').as_posix()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Write or check one module's contract, digest and graphs, or all of them."""
    parser = argparse.ArgumentParser(
        prog="python -m harness.assemble_contract",
        description="Assemble a module's claim files into contract.tex and its "
                    "statements digest, and build the review PDFs next to them; "
                    "--all does it for every core module and the overview.")
    parser.add_argument("module_id", nargs="?",
                        help="the core module id, e.g. meat-core")
    parser.add_argument("--all", action="store_true",
                        help="every core module, then the module map and the "
                             "overview; only what changed is rebuilt")
    parser.add_argument("--repo", default=".", help="repository root (default: .)")
    parser.add_argument("--check", action="store_true",
                        help="write nothing; exit 1 if a generated file or PDF is "
                             "stale")
    parser.add_argument("--no-pdf", action="store_true",
                        help="skip the PDFs and graph renders (neither built nor "
                             "checked)")
    parser.add_argument("--code-url", default=GITHUB,
                        help="the base of every code and registry link "
                             f"(default: {GITHUB})")
    args = parser.parse_args(argv)
    if bool(args.all) == bool(args.module_id):
        parser.error("name one module id, or pass --all")
    root = Path(args.repo)
    if args.all:
        return assemble_all(root, args.check, args.no_pdf, args.code_url)
    return assemble_one(root, args.module_id, args.check, args.no_pdf, args.code_url)


if __name__ == "__main__":
    raise SystemExit(main())
