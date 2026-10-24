#!/usr/bin/env python3
"""Motivation: published run records may come from an earlier tree than the release.

A run record names the commit it ran at, and the study behind the
whitepaper's numbers takes about ten hours. Rerunning it at the release
commit just to change that name costs a day; reusing records from an earlier
tree (a rehearsal export) is sound only if the code that computed them is the
code that is published. A plain diff of the two trees cannot say so: a
release edits comments, docstrings and messages throughout, and the diff of
those buries the one change that could move a number.

This tool compares two trees (directories) under `--paths` (default `src`,
`instances`, `runs`) and lists what a reader must still look at: every
Python file whose code differs once comments and docstrings are set aside
(the comparison is of the parsed syntax tree), every other file that differs
(a protocol document's default or a JSON table can move a number as much as
code can), and every file present on one side only. Python files that differ
only in comments and docstrings are counted, not listed. It decides nothing:
whether a listed change can move a recorded number is the reader's call, and
one that can means the affected runs are rerun.

Exit status: 0 when nothing is listed, 1 otherwise.
"""
from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable
from pathlib import Path

PATHS = ("src", "instances", "runs")
SKIP_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache"}
DOCUMENTED = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _files(root: Path, paths: Iterable[str],
           exclude: Iterable[str]) -> dict[str, Path]:
    """Map each file under ``root``'s ``paths``, named relative to it, to its path."""
    out: dict[str, Path] = {}
    excluded = tuple(e.rstrip("/") + "/" for e in exclude)
    for top in paths:
        base = root / top
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            skipped = SKIP_PARTS & set(path.parts) or path.suffix == ".pyc"
            if not path.is_file() or skipped:
                continue
            name = path.relative_to(root).as_posix()
            if not name.startswith(excluded):
                out[name] = path
    return out


def code_of(source: bytes) -> str:
    """Return the syntax tree of ``source`` without docstrings, as text.

    Comments never reach the tree.
    """
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, DOCUMENTED):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree)


def compare(old: Path, new: Path, paths: Iterable[str] = PATHS,
            exclude: Iterable[str] = ()) -> tuple[dict[str, list[str]], int]:
    """Return what differs between ``old`` and ``new``, and the comment-only count."""
    paths, exclude = list(paths), list(exclude)
    a, b = _files(old, paths, exclude), _files(new, paths, exclude)
    found: dict[str, list[str]] = {"code": [], "other": []}
    comment_only = 0
    for name in sorted(a.keys() & b.keys()):
        x, y = a[name].read_bytes(), b[name].read_bytes()
        if x == y:
            continue
        if name.endswith(".py"):
            try:
                same = code_of(x) == code_of(y)
            except SyntaxError:
                same = False
            if same:
                comment_only += 1
                continue
            found["code"].append(name)
        else:
            found["other"].append(name)
    found["old only"] = sorted(a.keys() - b.keys())
    found["new only"] = sorted(b.keys() - a.keys())
    return found, comment_only


def main(argv: list[str] | None = None) -> int:
    """List what differs; return 1 when anything is listed."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("old", type=Path, help="the tree the records ran at")
    parser.add_argument("new", type=Path, help="the tree to be published")
    parser.add_argument("--paths", nargs="+", default=list(PATHS),
                        help="the directories compared (default: %(default)s)")
    parser.add_argument("--exclude", action="append", default=[],
                        help="a directory left out, such as the records themselves")
    args = parser.parse_args(argv)
    found, comment_only = compare(args.old, args.new, args.paths, args.exclude)
    for kind, names in found.items():
        for name in names:
            print(f"{kind}: {name}")
    listed = sum(len(names) for names in found.values())
    print(f"{comment_only} Python file(s) differ only in comments and docstrings; "
          f"{listed} file(s) listed to read")
    return 1 if listed else 0


if __name__ == "__main__":
    sys.exit(main())
