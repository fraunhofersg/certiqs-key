#!/usr/bin/env python3
"""Motivation: a claim link that opens the contract at the claim.

The contracts' named destinations (``claim-<full id>``) are what other
documents link to, a whitepaper above all. GitHub's file view shows a PDF in
an embedded viewer that ignores ``#nameddest``, and a raw file is served as
``application/octet-stream`` with ``nosniff``, so the browser downloads it and
the fragment is lost; GitHub Pages serves ``application/pdf`` and the
browsers' viewers jump to the destination. A Pages deploy from a branch would
serve the whole tree, and the maintainers' tree holds third-party papers
(``refs/papers/``) and internal material (``context/``, ``state/``,
``reports/``) that must never be served; a published tree leaves them out,
and the deny-list holds either way. So this builds the site from an explicit allow-list
(``ALLOW``), and ``.github/workflows/pages.yml`` deploys exactly what it wrote.
Beside the contracts it serves the pages that link into them: the report
examples, the BBM92 study's headline report and the whitepaper's PDF
(``whitepaper/``), whose claim links point at the same site.

The site is versioned: ``latest/`` is the latest ref (main in CI), and every
tag matching the tag pattern gets ``<tag>/``, each with the repository's
layout below it (``<version>/spec/modules/<core>/contract.pdf``), because the
PDFs and the report pages link one another by relative paths. A claim id can
be renamed (``harness.relabel``), so a document citing one release links that
release's folder, which a later rename leaves alone. Every version is read
from git, never from the working tree, so an uncommitted file cannot reach the
site. Each version's ``index.html`` lists the modules and carries a link test:
the same two claims linked with the id raw and percent-encoded, for checking
which form a browser's viewer honours.

``DENY`` repeats, as path prefixes, what must never be served; a path matching
both lists aborts the build, and after writing, every file in the output is
checked against ``ALLOW`` again, so a widened pattern cannot carry a denied
file out unnoticed. Standard library only: the workflow runs it on a bare
runner. ``tests/harness/test_build_pages_site.py`` builds the site from HEAD.

    python -m harness.build_pages_site --out DIR [--latest REF] [--tags PATTERN]
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from urllib.parse import quote

#: What the site serves, as paths with ``*`` matching one path segment.
ALLOW: tuple[str, ...] = (
    "spec/modules/*/contract.pdf",
    "spec/modules/*/digest.pdf",
    "spec/modules/*/graphs/*.svg",
    "spec/modules/*/graphs/*.pdf",
    "spec/module-graph.svg",
    "spec/module-graph.pdf",
    "spec/overview/overview.pdf",
    "runs/report_examples/*/report.html",
    "runs/report_examples/*/record.html",
    "runs/report_examples/*/sweep.html",
    "runs/report_examples/*/points/*.html",
    "runs/bbm92_study/data/headline-report/report.html",
    "runs/bbm92_study/data/headline-report/record.html",
    "whitepaper/*.pdf",
)

#: What must never be served, whatever ``ALLOW`` says.
DENY: tuple[str, ...] = (
    "refs/",
    "context/",
    "state/",
    "reports/",
    "old/",
    ".claude/",
    ".github/",
    "HUMAN_SCRATCHPAD.md",
)

#: The claims of the link test: (core module, full claim id).
LINK_TEST: tuple[tuple[str, str], ...] = (
    ("statistics", "statistics/binomial-box/def:interval"),
    ("meat-core", "meat-core/cor:composed-security"),
)

LATEST = "latest"
INDEX = "index.html"

_ALLOW_RE = [
    re.compile("".join("[^/]+" if part == "*" else re.escape(part)
                       for part in re.split(r"(\*)", pattern)) + r"\Z")
    for pattern in ALLOW
]
_SEGMENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def denied(path: str) -> bool:
    """Return whether ``path`` lies under a ``DENY`` prefix."""
    return any(path == d or path.startswith(d) for d in DENY)


def allowed(path: str) -> bool:
    """Return whether the site serves ``path`` (a repository-relative path)."""
    return not denied(path) and any(r.match(path) for r in _ALLOW_RE)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def versions(repo: Path, latest: str, tags: str) -> list[tuple[str, str]]:
    """Return (folder, ref) per version: ``latest`` first, tags newest first."""
    out = [(LATEST, latest)]
    for tag in _git(repo, "tag", "--list", tags, "--sort=-creatordate").split():
        if tag in (LATEST, INDEX) or not _SEGMENT_RE.match(tag):
            raise SystemExit(f"build_pages_site: tag {tag!r} is not a usable "
                             "folder name")
        out.append((tag, f"refs/tags/{tag}"))
    return out


def served_paths(repo: Path, ref: str) -> list[str]:
    """Return the paths of ``ref``'s tree the site serves, sorted."""
    tree = _git(repo, "ls-tree", "-r", "--name-only", "-z", ref)
    return sorted(p for p in tree.split("\0") if p and allowed(p))


def _write_blobs(repo: Path, ref: str, paths: Sequence[str], dest: Path) -> None:
    """Write each path's blob at ``ref`` below ``dest``, bytes unchanged."""
    request = "".join(f"{ref}:{p}\n" for p in paths).encode()
    stream = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"],
                            input=request, check=True,
                            capture_output=True).stdout
    pos = 0
    for path in paths:
        end = stream.index(b"\n", pos)
        header = stream[pos:end].split()
        if len(header) != 3 or header[1] != b"blob":
            raise SystemExit(f"build_pages_site: {ref}:{path} is not a blob")
        size = int(header[2])
        target = dest / PurePosixPath(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(stream[end + 1:end + 1 + size])
        pos = end + 1 + size + 1


_STYLE = """\
:root { color-scheme: light dark; --fg: #1d1d1f; --bg: #ffffff; --mute: #5f6368;
  --link: #0b57d0; --rule: #d9d9d9; }
@media (prefers-color-scheme: dark) { :root { --fg: #e8eaed; --bg: #1f1f1f;
  --mute: #a0a4a8; --link: #8ab4f8; --rule: #3c4043; } }
body { font: 16px/1.5 system-ui, sans-serif; color: var(--fg);
  background: var(--bg); max-width: 46rem; margin: 2rem auto; padding: 0 16px; }
a { color: var(--link); } h2 { border-bottom: 1px solid var(--rule); }
.mute { color: var(--mute); } code { overflow-wrap: anywhere; }
table { border-collapse: collapse; } td { padding: .15rem .8rem .15rem 0; }
"""


def _page(title: str, body: list[str]) -> str:
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{html.escape(title)}</title>\n<style>\n{_STYLE}</style>\n"
            "</head>\n<body>\n" + "\n".join(body) + "\n</body>\n</html>\n")


def _a(href: str, text: str) -> str:
    return f'<a href="{html.escape(href)}">{html.escape(text)}</a>'


def version_index(folder: str, paths: Sequence[str]) -> str:
    """Return the ``index.html`` of one version, linking only served paths."""
    have = set(paths)
    cores = sorted({p.split("/")[2] for p in paths
                    if p.startswith("spec/modules/") and p.endswith("/contract.pdf")})
    body = [f"<h1>CERTIQS-KEY contracts: {html.escape(folder)}</h1>",
            "<p class=\"mute\">One contract and one statements digest per core "
            "module; a submodule's claims are in its core's contract. Link a "
            "claim as <code>spec/modules/&lt;core&gt;/contract.pdf#nameddest="
            "claim-&lt;full claim id&gt;</code>.</p>"]
    documents = [(p, "whitepaper") for p in paths
                 if p.startswith("whitepaper/") and p.endswith(".pdf")]
    documents += [(p, "the BBM92 study's headline key-rate report") for p in (
        "runs/bbm92_study/data/headline-report/report.html",) if p in have]
    if documents:
        body.append("<h2>Whitepaper</h2>")
        body.append("<ul>" + "".join(
            f"<li>{_a(p, text)}</li>" for p, text in documents) + "</ul>")
    body += ["<h2>Modules</h2>", "<table>"]
    for core in cores:
        base = f"spec/modules/{core}/"
        cells = [_a(base + "contract.pdf", core)]
        for name, text in (("digest.pdf", "digest"),
                           ("graphs/overview.svg", "section matrix"),
                           ("graphs/claims.svg", "claim graph")):
            if base + name in have:
                cells.append(_a(base + name, text))
        body.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    body.append("</table>")
    overview = [(p, text) for p, text in (
        ("spec/overview/overview.pdf", "main results in dependency order"),
        ("spec/module-graph.svg", "module map")) if p in have]
    if overview:
        body.append("<h2>Overview</h2>")
        body.append("<ul>" + "".join(
            f"<li>{_a(p, text)}</li>" for p, text in overview) + "</ul>")
    reports = [p for p in paths if p.startswith("runs/report_examples/")
               and p.count("/") == 3 and p.endswith(("/report.html", "/sweep.html"))]
    if reports:
        body.append("<h2>Key-rate report examples</h2>")
        body.append("<ul>" + "".join(
            f"<li>{_a(p, p.split('/')[2])}</li>" for p in reports) + "</ul>")
    tests = [(core, cid) for core, cid in LINK_TEST
             if f"spec/modules/{core}/contract.pdf" in have]
    if tests:
        body.append("<h2>Link test</h2>")
        body.append("<p class=\"mute\">Each claim twice: the id as written, and "
                    "percent-encoded. Both should open the contract at the "
                    "claim.</p>")
        body.append("<ul>")
        for core, cid in tests:
            pdf = f"spec/modules/{core}/contract.pdf#nameddest=claim-"
            body.append(f"<li><code>{html.escape(cid)}</code>: "
                        f"{_a(pdf + cid, 'raw')}, "
                        f"{_a(pdf + quote(cid, safe=''), 'encoded')}</li>")
        body.append("</ul>")
    body.append(f"<p class=\"mute\">{_a('../' + INDEX, 'All versions')}</p>")
    return _page(f"CERTIQS-KEY contracts {folder}", body)


def root_index(folders: Sequence[str]) -> str:
    """Return the site's root ``index.html``, listing the versions."""
    items = []
    for folder in folders:
        note = " (the main branch)" if folder == LATEST else ""
        items.append(f"<li>{_a(folder + '/' + INDEX, folder)}{note}</li>")
    return _page("CERTIQS-KEY", [
        "<h1>CERTIQS-KEY</h1>",
        "<p>The whitepaper, the contract and digest PDFs and the key-rate "
        "reports, per release. A document citing one release links that "
        "release's folder.</p>",
        "<ul>" + "".join(items) + "</ul>"])


def build(repo: Path, out: Path, latest: str, tags: str) -> dict[str, list[str]]:
    """Build the site into ``out`` (absent or empty); return paths per version."""
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"build_pages_site: {out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    built: dict[str, list[str]] = {}
    for folder, ref in versions(repo, latest, tags):
        paths = served_paths(repo, ref)
        bad = [p for p in paths if denied(p)]
        if bad:
            raise SystemExit(f"build_pages_site: denied paths matched: {bad}")
        dest = out / folder
        _write_blobs(repo, ref, paths, dest)
        (dest / INDEX).write_text(version_index(folder, paths), encoding="utf-8",
                                  newline="\n")
        built[folder] = paths
    (out / INDEX).write_text(root_index(list(built)), encoding="utf-8",
                             newline="\n")
    stray = [p for p in out.rglob("*") if p.is_file()
             and not _is_site_file(p.relative_to(out).as_posix(), built)]
    if stray:
        raise SystemExit(f"build_pages_site: files outside the allow-list: {stray}")
    return built


def _is_site_file(rel: str, built: dict[str, list[str]]) -> bool:
    if rel == INDEX:
        return True
    folder, _, path = rel.partition("/")
    return folder in built and (path == INDEX or allowed(path))


def main(argv: Sequence[str] | None = None) -> int:
    """Build the site; print one line per version."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True,
                        help="output folder, absent or empty")
    parser.add_argument("--latest", default="origin/main",
                        help="the ref served as latest/ (default origin/main)")
    parser.add_argument("--tags", default="v*",
                        help="tags served as versions (default v*)")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    built = build(args.repo, args.out, args.latest, args.tags)
    for folder, paths in built.items():
        print(f"{folder}: {len(paths)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
