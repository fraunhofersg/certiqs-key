"""harness/generate_bibliography.py: corporate authors of standards stay whole."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[2] / "harness" / "generate_bibliography.py"
_SPEC = importlib.util.spec_from_file_location("generate_bibliography", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
generate_bibliography = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(generate_bibliography)


def _author(entry: dict[str, object]) -> str:
    return dict(generate_bibliography._fields(entry))["author"]


def test_standard_authors_are_braced() -> None:
    entry = {"ref_id": "s", "type": "standard",
             "authors": ["ISO/IEC JTC 1/SC 27"]}
    assert _author(entry) == "{ISO/IEC JTC 1/SC 27}"


def test_personal_authors_are_not_braced() -> None:
    entry = {"ref_id": "p", "type": "arxiv",
             "authors": ["Amir Arqand", "Ernest Y.-Z. Tan"]}
    assert _author(entry) == "Amir Arqand and Ernest Y.-Z. Tan"
