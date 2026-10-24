"""Which engine wrote a run record: the distribution version and the git commit.

WHY THIS EXISTS. A record names the module versions it consumed and the
claim graph its number rests on, but not the code that computed it. A
reviewer reproducing a key rate needs the commit:
``RunConfig.from_payload`` of the record's ``config`` reproduces the run only
on the engine that wrote it. Every record (schema 0.20.0 on) carries it, as
``payload.provenance.engine``.

WHAT IT IS NOT. Not the deferred envelope's ``provenance`` block
(spec/future-scope.md section 1): it sits inside the payload, hashes nothing
and names only the producing code, which a future envelope's block would
contain as a subset. No timestamp, host or path is recorded
(spec/architecture.md 2.6).

Outside a git checkout -- an installed wheel -- ``git_commit`` and
``git_dirty`` are ``null``; the distribution version still says which release
ran.
"""

from __future__ import annotations

import subprocess
from functools import cache
from importlib import metadata
from pathlib import Path
from typing import Any

__all__ = ["DISTRIBUTION", "engine_identity"]

#: The distribution name of this package (``pyproject.toml``).
DISTRIBUTION = "certiqs-key"


def _git(root: Path, *arguments: str) -> str | None:
    """Return a git command's stripped output in ``root``, or ``None``."""
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _checkout_root() -> Path | None:
    """Return the checkout this package is imported from, or ``None``.

    The package lives at ``<root>/src/certiqs_key``; a root is a checkout when
    git names it as its own top level, so a wheel unpacked inside some other
    repository is not mistaken for this one.
    """
    root = Path(__file__).resolve().parents[3]
    top = _git(root, "rev-parse", "--show-toplevel")
    if top is None or Path(top).resolve() != root:
        return None
    return root


@cache
def engine_identity() -> dict[str, Any]:
    """Return ``{distribution_version, git_commit, git_dirty}``, once per process.

    ``git_dirty`` is whether a tracked file differs from the commit at the
    moment it is first asked (``git status --porcelain --untracked-files=no``);
    a run in a dirty tree is reproducible only with that diff, which the record
    cannot carry, so it says so.
    """
    try:
        version: str | None = metadata.version(DISTRIBUTION)
    except metadata.PackageNotFoundError:
        version = None
    root = _checkout_root()
    commit = None if root is None else _git(root, "rev-parse", "HEAD")
    status = (
        None
        if root is None or commit is None
        else _git(root, "status", "--porcelain", "--untracked-files=no")
    )
    return {
        "distribution_version": version,
        "git_commit": commit,
        "git_dirty": None if status is None else bool(status),
    }
