#!/usr/bin/env python3
"""Motivation: shipped files state what is; history drifts back in.

PRINCIPLES.md section 4: status is never mixed with history. A file that
ships (specification, code, tests, tools, documentation) describes the
present design and the reasons for its shape; how it came to be belongs in
commit messages, dated reports and open-item history. History returns as
soon as a comment is written under time pressure: a decision quoted with who
made it and when, a date saying when a rule arrived, a sentence about the
repository this one replaced, a pointer into `reports/` or `state/` (which a
reader of a published tree does not have), a personal email or a local path.
The only other guard, `tests/harness/test_no_predecessor_process_in_the_tree.py`,
reads `src/*.py` for seven document names.

This tool reports, per line of every shipped text file, five kinds of
history (`PATTERNS`):

* ``attribution``: a person named (`PEOPLE`, read from `PEOPLE_FILE`), an
  ``ACCEPTED <date>`` stamp,
  a quoted ``(Recommended)`` answer. "The maintainer" is not matched:
  `spec/style.md` prescribes it as the role word where attribution matters;
* ``dates``: an ISO date or month (``2026-10-13``, ``2026-10``), a
  month-name date (``Oct 2026``), ``since/until/as of <year>``. A year inside
  an identifier (``arqand2025meat``), a version (``0.20.0``) and a date that
  is a path component after a ``/`` (a report folder, which ``pointers``
  reports; a JSON-Schema draft URL) do not match;
* ``predecessor``: the repository this one replaced, its package name, its
  governance documents, its "Slice 2" milestone, migration narration;
* ``pointers``: a path into a tree that does not ship (`reports/`,
  `state/open-items/`, `state/DASHBOARD.md`, `context/`, `old/reports/`);
* ``identity``: an email address, an absolute user path, a sync folder.

Process vocabulary (review rounds, finding codes, batch and phase names) is
left out on purpose: against plain words such as "effort" and "round" it
reads at about 85% precision, and a check that cries wolf trains its readers
to ignore it. The tool decides form, never meaning: whether a hit is history
or a present fact is a reader's call, written into the allow-list.

SCOPE. The tracked files (`git ls-files`; a directory walk when the root is
not a repository) minus what does not ship or is not authored: `reports/`,
`state/`, `context/`, `refs/`, `old/` and `HUMAN_SCRATCHPAD.md` (excluded by
name, never opened); generated files (`GENERATED`: contracts, digests,
graphs, the overview frame and chain, the module map, the report examples,
the claim-closure table, a release's `CITATION.cff`), whose sources are
scanned instead; binaries; and
the tool's own files (`SELF`), which spell out the patterns.

CLAIM NOTES. A line of a claim's `% notes:` header field is reported in its
own category, ``claim-notes``, whatever its pattern (the pattern's category
is kept beside it), because those lines are cleaned by the editorial route
(`harness.math_diff`), not by an ordinary edit.

THE ALLOW-LIST, `harness/history_allow.yaml`, has two lists. Each entry has
a `path` (an `fnmatch` glob, `*` also crossing `/`, or a list of them), a
`category`, a written `reason`, and optionally `match`, a regular expression
the line must contain, so that an entry allows one form (a trailer, a
contact address) without the whole file.

* ``allow``: justified exceptions, permanent (a layout document naming the
  folders, a synthetic fixture, the capture date of a dataset).
* ``pending``: known history waiting for a cleaning pass, listed and counted
  but not failing `--check` unless `--strict`. Its paths name files, so new
  history in any other file fails. The claim notes have no pending entry,
  so a history line in a claim's notes fails `--check`.

A path that covers no finding fails `--check`, so both lists only shrink:
when a pass cleans a file, `--check` says so and its path goes.

Usage:
    python -m harness.check_history [--repo .] [--check] [--strict]
        [--category NAME] [--summary] [--allowed]

Without `--check` it lists the failing and the pending findings (`--allowed`
adds the allowed ones; `--summary` counts them per file) and exits 0; with
it, it prints only what fails and exits 1 on a finding outside the
allow-list, on a pending one under `--strict`, or on an unused path. The
cost is a few seconds per run and one entry, with its reason, per justified
exception; the error it prevents is a published file narrating its history.
"""

from __future__ import annotations

import argparse
import bisect
import fnmatch
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CATEGORIES = ("attribution", "dates", "predecessor", "pointers", "identity")
CLAIM_NOTES = "claim-notes"
UNUSED = "allow-list"
LISTS = ("allow", "pending")

ALLOW_FILE = "harness/history_allow.yaml"

#: The people a shipped file must not name, one per line in `PEOPLE_FILE`
#: beside this tool (`#` starts a comment). The list names people, so it is
#: kept with the maintainers' tree and does not ship with a published one; a
#: tree without the file checks no names. A surname that is also a
#: mathematician's (an inequality's name) is left out of the file.
PEOPLE_FILE = Path(__file__).with_name("history_people.txt")


def load_people(path: Path = PEOPLE_FILE) -> tuple[str, ...]:
    """Return the names of `path`, or none where the file is absent."""
    if not path.is_file():
        return ()
    lines = path.read_text(encoding="utf-8").splitlines()
    return tuple(s for s in (line.split("#", 1)[0].strip() for line in lines) if s)


PEOPLE = load_people()

_MONTH = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|"
          r"July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
          r"Dec(?:ember)?)")
_YEAR = r"20[2-3]\d"

#: One regular expression per alternative; `(?i:...)` marks the
#: case-insensitive ones. None spans a line break: whitespace is `[ \t]`.
PATTERNS: dict[str, tuple[str, ...]] = {
    "attribution": (
        *((r"\b(?:" + "|".join(map(re.escape, PEOPLE)) + r")\b",) if PEOPLE else ()),
        r"\bACCEPTED[ \t]+(?:on[ \t]+)?" + _YEAR,
        r"\(Recommended\)",
    ),
    "dates": (
        r"(?<![\w./])" + _YEAR + r"-[01]\d(?:-[0-3]\d)?(?![\d.])",
        r"\b" + _MONTH + r"\.?[ \t]+(?:\d{1,2},?[ \t]+)?" + _YEAR + r"\b",
        r"\b\d{1,2}[ \t]+" + _MONTH + r"\.?[ \t]+" + _YEAR + r"\b",
        r"(?i:\b(?:since|until|as[ \t]+of)[ \t]+)" + _YEAR + r"\b",
    ),
    "predecessor": (
        r"QKD-MEAT",
        r"\bqkd_meat\b",
        r"(?i:\bthe predecessor\b)",
        r"(?i:\bmigrat(?:e|ed|es|ing|ion)\b)",
        r"(?i:\bslice[-_ ]?2\b)",
        r"\b(?:ROADMAP\.md|STATUS\.yaml|REVIEW\.md|OPEN_ITEMS\.md|"
        r"AGENT_WORKFLOW\.md|ARCHITECTURE_SPEC\.md)",
    ),
    "pointers": (
        r"(?<![\w./-])reports/",
        r"(?<![\w./-])state/(?:open-items|DASHBOARD)",
        r"(?<![\w./-])context/",
        r"(?<![\w./-])old/reports",
    ),
    "identity": (
        r"[\w.+-]@[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|de|sg|edu|io|ai)\b",
        r"(?i:\b[A-Z]:[\\/]+Users[\\/])",
        r"(?<![\w.])/(?:home|Users)/\w",
        r"\b(?:Dropbox|OneDrive)\b",
    ),
}

_COMPILED = {
    category: re.compile("|".join(f"(?:{alt})" for alt in alternatives))
    for category, alternatives in PATTERNS.items()
}

#: For speed only: a category's expression runs on a file only when the
#: lowercased file contains one of these substrings, each implied by a match
#: (a regular-expression search over the whole tree takes seconds, a
#: substring test milliseconds). `tests/harness/test_check_history.py` holds
#: that every positive example passes its prefilter.
_NEEDLES: dict[str, tuple[str, ...]] = {
    "attribution": (*(p.lower() for p in PEOPLE), "accepted", "(recommended)"),
    "dates": ("202", "203"),
    "predecessor": ("qkd-meat", "qkd_meat", "predecessor", "migrat", "slice",
                    "roadmap.md", "status.yaml", "review.md", "open_items.md",
                    "agent_workflow.md", "architecture_spec.md"),
    "pointers": ("reports/", "state/", "context/", "old/reports"),
    "identity": ("@", "users", "/home/", "dropbox", "onedrive"),
}

#: Trees that do not ship: history, working notes, pinned references.
EXCLUDED_DIRS = ("reports/", "state/", "context/", "refs/", "old/", ".git/")

#: Excluded by name and never opened (AGENTS.md: agents never read it).
EXCLUDED_FILES = ("HUMAN_SCRATCHPAD.md",)

#: Generated from sources this tool scans; their generators' `--check` keeps
#: them current, so a hit there is a hit in a source.
GENERATED = (
    "spec/modules/*/contract.tex",
    "spec/modules/*/digest.tex",
    "spec/modules/*/graphs/*",
    "spec/overview/chain.tex",
    "spec/overview/overview.tex",
    "spec/module-graph.*",
    "runs/report_examples/*",
    "src/certiqs_key/domain/claim_closure.json",
    # A release's citation file, rendered by the export from
    # harness/export_citation.cff; its date-released is the release's date.
    "CITATION.cff",
)

#: This tool's own files, which spell out the patterns they look for.
SELF = (
    "harness/check_history.py",
    ALLOW_FILE,
    "harness/history_people.txt",
    "tests/harness/test_check_history.py",
)

BINARY_SUFFIXES = (
    ".pdf", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".gz", ".npz", ".npy",
    ".zip", ".pyc", ".ico",
)

#: A claim file: its `% ---` header carries the `notes` field.
_CLAIM_FILE = re.compile(r"^spec/modules/.+/claims/[^/]+\.tex$")
_HEADER_FIELD = re.compile(r"^%\s?([A-Za-z_][\w-]*):")
_LINE_BREAK = re.compile(r"\r\n|[\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029]")


@dataclass(frozen=True)
class Finding:
    """One line of a shipped file that matches a category.

    ``kind`` is the pattern's category; ``category`` equals it except on a
    claim's `notes` lines, where it is ``claim-notes``.
    """

    path: str
    line: int
    category: str
    kind: str
    match: str
    text: str

    def render(self) -> str:
        """Render the finding as `path:line: [category] 'match': text`."""
        text = self.text.strip()
        if len(text) > 160:
            text = text[:157] + "..."
        label = self.category if self.category == self.kind else (
            f"{self.category}/{self.kind}")
        return f"{self.path}:{self.line}: [{label}] {self.match!r}: {text}"


@dataclass
class AllowEntry:
    """One entry of the allow-list, `allow` or `pending`, with one or more paths."""

    section: str
    paths: tuple[str, ...]
    category: str
    reason: str
    match: re.Pattern[str] | None = None
    used: Counter[str] = field(default_factory=Counter)

    def covers(self, finding: Finding) -> str | None:
        """Return the path glob of this entry that covers the finding, if any."""
        if self.category != finding.category:
            return None
        if self.match is not None and self.match.search(finding.text) is None:
            return None
        return next((glob for glob in self.paths
                     if fnmatch.fnmatchcase(finding.path, glob)), None)

    def unused(self) -> list[str]:
        """Return the path globs of this entry that covered no finding."""
        return [glob for glob in self.paths if not self.used[glob]]


@dataclass
class Result:
    """The findings of one run, split by what `--check` does with them."""

    failing: list[Finding] = field(default_factory=list)
    pending: list[Finding] = field(default_factory=list)
    allowed: list[Finding] = field(default_factory=list)
    unused: list[tuple[AllowEntry, str]] = field(default_factory=list)
    files: int = 0


def _matches(rel: str, globs: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(rel, glob) for glob in globs)


def in_scope(rel: str) -> bool:
    """Whether a repository-relative POSIX path is a shipped, authored text file."""
    if rel.startswith(EXCLUDED_DIRS) or rel in EXCLUDED_FILES:
        return False
    if rel in SELF or _matches(rel, GENERATED):
        return False
    return not rel.lower().endswith(BINARY_SUFFIXES)


def tracked_files(root: Path) -> list[str]:
    """Return the tracked files, or every file below `root` outside git."""
    if (root / ".git").exists():
        try:
            out = subprocess.run(
                ["git", "ls-files", "-z"], cwd=root, capture_output=True,
                check=True,
            ).stdout
            return sorted(p for p in out.decode("utf-8").split("\0") if p)
        except (OSError, subprocess.CalledProcessError):
            pass
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )


def shipped_files(root: Path) -> list[str]:
    """Return the files this tool scans, as repository-relative POSIX paths."""
    return [rel for rel in tracked_files(root) if in_scope(rel)]


def claim_notes_lines(rel: str, lines: list[str]) -> set[int]:
    """1-based numbers of the lines that hold a claim's `notes` header field."""
    if not _CLAIM_FILE.match(rel) or not lines or lines[0].strip() != "% ---":
        return set()
    notes: set[int] = set()
    current = None
    for number, line in enumerate(lines[1:], start=2):
        if line.strip() == "% ---":
            break
        field_match = _HEADER_FIELD.match(line)
        if field_match:
            current = field_match.group(1)
        if current == "notes":
            notes.add(number)
    return notes


def scan_text(rel: str, text: str) -> list[Finding]:
    """Every (line, category) hit of one file; a claim's notes in their own category."""
    lines = text.splitlines()
    notes = claim_notes_lines(rel, lines)
    # Offsets of the line starts, as `splitlines` splits: the whole text is
    # searched once per category and each hit mapped back to its line.
    starts = [0] + [m.end() for m in _LINE_BREAK.finditer(text)]
    lowered = text.lower()
    found: dict[tuple[int, str], Finding] = {}
    for kind, pattern in _COMPILED.items():
        if not any(needle in lowered for needle in _NEEDLES[kind]):
            continue
        for hit in pattern.finditer(text):
            number = bisect.bisect_right(starts, hit.start())
            if (number, kind) in found:
                continue
            category = CLAIM_NOTES if number in notes else kind
            found[number, kind] = Finding(
                rel, number, category, kind, hit.group(0), lines[number - 1])
    order = {kind: index for index, kind in enumerate(CATEGORIES)}
    return sorted(found.values(), key=lambda f: (f.line, order[f.kind]))


def scan(root: Path, files: list[str] | None = None) -> tuple[list[Finding], int]:
    """Scan the shipped files under `root`; returns the findings and the file count."""
    rels = shipped_files(root) if files is None else files
    found: list[Finding] = []
    scanned = 0
    for rel in rels:
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        scanned += 1
        found.extend(scan_text(rel, text))
    return found, scanned


def load_allow_list(path: Path) -> list[AllowEntry]:
    """Read both lists; every entry needs a path, a known category and a reason."""
    if not path.is_file():
        return []
    data: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or set(data) - set(LISTS):
        raise ValueError(f"{path.name}: expected a mapping with the lists "
                         f"{', '.join(LISTS)} only")
    entries: list[AllowEntry] = []
    for name in LISTS:
        raw = data.get(name) or []
        if not isinstance(raw, list):
            raise ValueError(f"{path.name}: '{name}' is not a list")
        for index, item in enumerate(raw):
            where = f"{path.name} {name} entry {index + 1}"
            if not isinstance(item, dict):
                raise ValueError(f"{where}: not a mapping")
            unknown = set(item) - {"path", "category", "reason", "match"}
            if unknown:
                raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}")
            for key in ("category", "reason"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    raise ValueError(f"{where}: '{key}' is required")
            paths = item.get("path")
            if isinstance(paths, str):
                paths = [paths]
            if (not isinstance(paths, list) or not paths
                    or not all(isinstance(p, str) and p.strip() for p in paths)):
                raise ValueError(f"{where}: 'path' must be a glob or a list of globs")
            if item["category"] not in (*CATEGORIES, CLAIM_NOTES):
                raise ValueError(f"{where}: unknown category '{item['category']}'")
            match = item.get("match")
            if match is not None and not isinstance(match, str):
                raise ValueError(f"{where}: 'match' must be a string")
            entries.append(AllowEntry(
                name, tuple(paths), item["category"], item["reason"],
                re.compile(match) if match else None))
    return entries


def classify(findings: list[Finding], entries: list[AllowEntry]) -> Result:
    """Split findings into failing, pending and allowed; `allow` entries first."""
    ordered = sorted(entries, key=lambda e: LISTS.index(e.section))
    result = Result()
    for finding in findings:
        for entry in ordered:
            glob = entry.covers(finding)
            if glob is not None:
                entry.used[glob] += 1
                bucket = result.allowed if entry.section == "allow" else result.pending
                bucket.append(finding)
                break
        else:
            result.failing.append(finding)
    result.unused = [(entry, glob) for entry in entries for glob in entry.unused()]
    return result


def run(root: Path, allow_file: Path | None = None) -> Result:
    """Scan `root` and classify its findings against its allow-list."""
    findings, scanned = scan(root)
    entries = load_allow_list(allow_file or root / ALLOW_FILE)
    result = classify(findings, entries)
    result.files = scanned
    return result


def counts(findings: list[Finding]) -> str:
    """Count findings per category, as `name n, ...`, or `none`."""
    tally = Counter(f.category for f in findings)
    order = (*CATEGORIES, CLAIM_NOTES)
    return ", ".join(f"{name} {tally[name]}" for name in order if tally[name]) or "none"


def build_parser() -> argparse.ArgumentParser:
    """Build the command line."""
    parser = argparse.ArgumentParser(
        prog="python -m harness.check_history",
        description="List history (attribution, dates, predecessor, pointers, "
                    "identity) in the shipped files.")
    parser.add_argument("--repo", default=".", help="repository root")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 on a finding outside the allow-list or an "
                             "unused allow-list entry")
    parser.add_argument("--strict", action="store_true",
                        help="pending findings fail too")
    parser.add_argument("--category", choices=(*CATEGORIES, CLAIM_NOTES),
                        help="list only this category")
    parser.add_argument("--summary", action="store_true",
                        help="counts per file instead of lines")
    parser.add_argument("--allowed", action="store_true",
                        help="also list the findings the allow list covers")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Scan the shipped files, print the findings and return the exit code."""
    args = build_parser().parse_args(argv)
    root = Path(args.repo)
    if not root.is_dir():
        print(f"error: --repo {args.repo} is not a directory", file=sys.stderr)
        return 1
    try:
        result = run(root)
    except (ValueError, re.error, yaml.YAMLError) as error:
        print(f"error: {ALLOW_FILE}: {error}", file=sys.stderr)
        return 1
    if args.strict:
        result.failing.extend(result.pending)
        result.pending = []

    def chosen(findings: list[Finding]) -> list[Finding]:
        return [f for f in findings
                if args.category is None or f.category == args.category]

    sections = [("", chosen(result.failing))]
    if not args.check:
        sections.append(("pending", chosen(result.pending)))
    if args.allowed:
        sections.append(("allowed", chosen(result.allowed)))
    for title, findings in sections:
        if args.summary and findings:
            print(f"{title or 'failing'} findings by file:")
            per_file = Counter(f.path for f in findings)
            for path, count in sorted(per_file.items(), key=lambda kv: (-kv[1], kv[0])):
                print(f"  {count:5d}  {path}")
            continue
        for finding in findings:
            print((f"({title}) " if title else "") + finding.render())
    for entry, glob in result.unused:
        print(f"{ALLOW_FILE}: [{UNUSED}] {entry.section} path {glob} "
              f"({entry.category}) matches nothing: drop it")

    print(f"{result.files} shipped file(s) scanned. "
          f"failing: {len(result.failing)} ({counts(result.failing)}); "
          f"pending: {len(result.pending)} ({counts(result.pending)}); "
          f"allowed: {len(result.allowed)}; "
          f"unused allow-list entries: {len(result.unused)}")
    if args.check and (result.failing or result.unused):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
