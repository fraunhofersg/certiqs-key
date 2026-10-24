#!/usr/bin/env python3
"""Generate refs/references.bib from refs/index.json.

`refs/index.json` is the only citable universe (PRINCIPLES.md §8).
Contracts cite ref-ids from it, so the BibTeX file a contract compiles against
is a *derived* artifact, not something an author maintains. Regenerating it is
the only supported way to change it.

Usage:
    python harness/generate_bibliography.py            # write references/references.bib
    python harness/generate_bibliography.py --check    # exit 1 if the file is stale

The output is deterministic: entries are sorted by BibTeX key so that
regenerating without an index change produces a byte-identical file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "refs" / "index.json"
OUTPUT_PATH = REPO_ROOT / "refs" / "references.bib"

HEADER = """\
%% GENERATED FILE -- DO NOT EDIT.
%%
%% Produced by harness/generate_bibliography.py from refs/index.json,
%% which is the only citable universe (PRINCIPLES.md section 3).
%%
%% To add a citable work: register it in refs/index.json (refs/README.md),
%% then regenerate this file. Editing this file directly does not make a
%% work citable and will be overwritten.
"""


def _escape(value: str) -> str:
    """Protect BibTeX-significant characters in a field value."""
    return value.replace("{", r"\{").replace("}", r"\}")


def _entry_type(entry: dict[str, Any]) -> str:
    """Choose a BibTeX entry type from the index record."""
    declared = (entry.get("type") or "").lower()
    if declared == "book":
        return "book"
    if declared == "thesis":
        return "phdthesis"
    if entry.get("journal_ref"):
        return "article"
    if declared == "arxiv" or entry.get("arxiv_id"):
        return "misc"
    return "misc"


def _fields(entry: dict[str, Any]) -> list[tuple[str, str]]:
    """Build the ordered field list for one entry."""
    fields: list[tuple[str, str]] = []

    authors = entry.get("authors") or []
    if (entry.get("type") or "").lower() == "standard":
        # A standard's authors are bodies ("ISO/IEC JTC 1/SC 27"); braced, so
        # BibTeX and biber do not split them into given name and surname.
        authors = ["{" + author + "}" for author in authors]
    if authors:
        fields.append(("author", " and ".join(authors)))

    if entry.get("title"):
        fields.append(("title", "{" + _escape(entry["title"]) + "}"))

    if entry.get("year") is not None:
        fields.append(("year", str(entry["year"])))

    if entry.get("journal_ref"):
        fields.append(("journal", _escape(entry["journal_ref"])))

    if entry.get("publisher"):
        fields.append(("publisher", _escape(entry["publisher"])))

    if entry.get("school"):
        fields.append(("school", _escape(entry["school"])))

    if entry.get("edition"):
        fields.append(("edition", _escape(str(entry["edition"]))))

    arxiv_id = entry.get("arxiv_id")
    if arxiv_id:
        version = entry.get("arxiv_version") or ""
        fields.append(("eprint", f"{arxiv_id}{version}"))
        fields.append(("archivePrefix", "arXiv"))

    if entry.get("doi"):
        fields.append(("doi", entry["doi"]))

    if entry.get("isbn"):
        fields.append(("isbn", entry["isbn"]))

    # Record non-redistributable works explicitly: they are citable but no PDF
    # is stored, and a reader needs to know why the file is absent.
    if entry.get("access") and entry.get("file") is None:
        fields.append(
            ("note", _escape(f"Not redistributable; access: {entry['access']}"))
        )

    return fields


def render(index: dict[str, Any]) -> str:
    """Render the whole BibTeX file from a parsed index."""
    entries = index.get("entries", [])
    chunks = [HEADER]

    for entry in sorted(entries, key=lambda e: e.get("bibtex_key") or e["ref_id"]):
        key = entry.get("bibtex_key") or entry["ref_id"]
        fields = _fields(entry)
        body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields)
        chunks.append(f"@{_entry_type(entry)}{{{key},\n{body}\n}}\n")

    return "\n".join(chunks)


def main() -> int:
    """Regenerate references.bib, or check it against refs/index.json."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 if references.bib is missing or stale",
    )
    args = parser.parse_args()

    if not INDEX_PATH.exists():
        print(f"error: {INDEX_PATH} not found", file=sys.stderr)
        return 1

    with INDEX_PATH.open(encoding="utf-8") as handle:
        index = json.load(handle)

    rendered = render(index)

    if args.check:
        if not OUTPUT_PATH.exists():
            print(
                f"stale: {OUTPUT_PATH} does not exist; "
                "run harness/generate_bibliography.py",
                file=sys.stderr,
            )
            return 1
        current = OUTPUT_PATH.read_text(encoding="utf-8")
        if current != rendered:
            print(
                f"stale: {OUTPUT_PATH} differs from refs/index.json",
                file=sys.stderr,
            )
            return 1
        print(f"up to date: {OUTPUT_PATH.relative_to(REPO_ROOT)}")
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    count = len(index.get("entries", []))
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} ({count} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
