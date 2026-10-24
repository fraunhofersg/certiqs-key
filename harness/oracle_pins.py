r"""Motivation: a reader of a claim cannot see which frozen oracle tests it.

The frozen oracle registries under `tests/oracles/` pin claims by
oracle codes (C5, PC11, SA3), never by this repository's ids, because a
frozen registry is never edited (PRINCIPLES.md section 2.3).
`tests/oracles/claim_codes.yaml` is the one table that translates them. A
reader of the contract PDF, or a reviewer asking whether a numerical oracle
exercises a statement, would otherwise have to open that table and then grep
the registries. The meta line links, under each claim, the registry files that
pin it; this module
computes, per claim, the codes mapped to it and the registries pinning each.
The PDF prints the registry files only: the codes are the registries'
vocabulary, which the contracts do not carry.

It reads the YAML and the registry files as text, because `tests/` is not an
importable package for `harness/`. A registry pins a claim through a `claims`
or `supports` field or key (`tests/oracles/test_claim_codes.py`, which walks the
imported registries, is the authority on that); here the value of such a field
is read from the source: a bracketed literal, a single quoted string, or the
name of a constant whose bracketed literal the same file assigns. That
reading finds exactly the pins the imported walk
finds. A pin computed in a way the text does not show (an expression other
than a name) is missed, never invented; `test_claim_codes.py` still guarantees
the table covers it.

Only codes of the `codes` section count (a code with no claim, or an
unresolved one, pins no claim), and a code is listed only when at least one
registry pins it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

#: Where the table lives, relative to the repository root.
CLAIM_CODES = Path("tests") / "oracles" / "claim_codes.yaml"
#: An oracle code: a family of capitals, a number, an optional sub-letter.
CODE_RE = re.compile(r"^(?P<family>[A-Z]+)(?P<number>[0-9]+)(?P<suffix>[a-z]?)$")
#: The start of a pinning value: ``claims=``, ``supports=``, ``"claims":``.
PIN_RE = re.compile(r"""(?:\b(?:claims|supports)\s*=\s*"""
                    r"""|["'](?:claims|supports)["']\s*:\s*)""")
QUOTED_RE = re.compile(r"""["']([A-Za-z0-9]+)["']""")
NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CLOSERS = {"(": ")", "[": "]", "{": "}"}


@dataclass(frozen=True)
class OraclePin:
    """One oracle code mapped to a claim, with the registries pinning it."""

    code: str
    registries: tuple[str, ...]     # repository-relative paths, sorted


def natural_key(code: str) -> tuple[str, int, str]:
    """Order codes by family, then number, then suffix: C9b before C10."""
    match = CODE_RE.match(code)
    if match is None:
        return code, 0, ""
    return match["family"], int(match["number"]), match["suffix"]


def _bracketed(text: str, index: int) -> str | None:
    """Return the bracketed literal starting at ``index`` (after spaces), if any."""
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text) or text[index] not in CLOSERS:
        return None
    depth = 0
    for position in range(index, len(text)):
        if text[position] in CLOSERS:
            depth += 1
        elif text[position] in CLOSERS.values():
            depth -= 1
            if depth == 0:
                return text[index:position + 1]
    return None


def _assigned(text: str, name: str) -> str | None:
    """Return the bracketed literal a module-level ``name = ...`` assigns, if any."""
    match = re.search(r"^" + re.escape(name) + r"\s*(?::[^=\n]*)?=\s*", text, re.M)
    return None if match is None else _bracketed(text, match.end())


def pinned_codes(text: str) -> set[str]:
    """Return every code a registry source pins through ``claims``/``supports``."""
    found: set[str] = set()
    for match in PIN_RE.finditer(text):
        value = _bracketed(text, match.end())
        if value is None:
            rest = text[match.end():]
            quoted = QUOTED_RE.match(rest)
            if quoted is not None:
                value = quoted.group(0)
            else:
                name = NAME_RE.match(rest)
                value = _assigned(text, name.group(0)) if name else None
        if value is not None:
            found.update(code for code in QUOTED_RE.findall(value)
                         if CODE_RE.match(code))
    return found


def _load(root: Path) -> dict[str, Any]:
    path = root / CLAIM_CODES
    if not path.is_file():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def oracle_pins(root: Path) -> dict[str, tuple[OraclePin, ...]]:
    """Return, per full claim id, the codes mapped to it that a registry pins.

    Codes are in natural order, each with the registry files that pin it. A
    repository without ``tests/oracles/claim_codes.yaml`` has no pins.
    """
    document = _load(root)
    codes = document.get("codes") or {}
    registries = document.get("registries") or {}
    pinning: dict[str, set[str]] = {}
    for relative in sorted(str(name) for name in registries):
        path = root / relative
        if not path.is_file():
            continue
        for code in pinned_codes(path.read_text(encoding="utf-8")):
            pinning.setdefault(code, set()).add(relative)
    per_claim: dict[str, list[OraclePin]] = {}
    for code in sorted(codes, key=lambda item: natural_key(str(item))):
        files = pinning.get(str(code))
        if not files:
            continue
        for claim_id in codes[code] or []:
            per_claim.setdefault(str(claim_id), []).append(
                OraclePin(str(code), tuple(sorted(files))))
    return {claim_id: tuple(pins) for claim_id, pins in per_claim.items()}
