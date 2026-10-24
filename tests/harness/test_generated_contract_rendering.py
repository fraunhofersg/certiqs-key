"""Three rendering defects of the generated contract files, held closed.

Motivation: they appear in the tracked generated files, where nothing else
checks them:

* H-1: ``graphs/README.md`` linked ``../design.md#the-modules-main-logic``
  whenever a ``design.md`` existed, and foundations' has no such heading;
* H-2: an interface row with ``symbol: null`` printed "None" in the
  Interface table;
* H-3: a claim a Notation Meaning cell names ("meat-core Def.
  `def:declaration`") printed as typewriter text instead of a link.

The tests read the tracked files, which ``assemble_contract --all --check``
holds current, so they need no import of ``harness`` (``tests/harness`` is
itself a package of that name).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULES = ROOT / "spec" / "modules"


def test_no_interface_table_prints_none_for_a_null_symbol() -> None:
    """H-2: ``symbol: null`` renders as no symbol."""
    offenders = [
        str(path.relative_to(ROOT))
        for path in sorted(MODULES.glob("*/contract.tex"))
        if "\\newline None &" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_every_design_flowchart_link_lands_on_a_heading() -> None:
    """H-1: a graphs index links the main-logic section only where it exists."""
    for index in sorted(MODULES.rglob("graphs/README.md")):
        text = index.read_text(encoding="utf-8")
        if "../design.md#the-modules-main-logic" not in text:
            continue
        design = index.parent.parent / "design.md"
        assert design.is_file(), index
        assert re.search(
            r"^## The module's main logic\s*$",
            design.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        ), index


def test_a_claim_named_in_a_meaning_cell_is_a_link() -> None:
    """H-3: inside its own contract the claim is a reference, elsewhere a link."""
    meat = (MODULES / "meat-core" / "contract.tex").read_text(encoding="utf-8")
    assert "the tuple of \\mref{Def.}{def:declaration}" in meat
    compiler = (MODULES / "protocol-compiler" / "contract.tex").read_text(
        encoding="utf-8"
    )
    assert (
        "the tuple of \\extref{../meat-core/contract.pdf}{meat-core/def:declaration}"
        in compiler
    )
    assert "meat-core Def. \\texttt{def:declaration}" not in compiler
