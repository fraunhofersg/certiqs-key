"""No shipped file points a reader at a process document or a path this tree lacks.

MOTIVATION, AND THE ERROR CLASS IT CATCHES. A sentence about another
repository's package, with only its package name rewritten to ``certiqs_key``,
reads as a FALSE STATEMENT ABOUT THIS TREE -- "``src/certiqs_key/reductions/``
did not exist at the time of writing" (of a package that does), "the
``LIFT_LADDER`` of this package's ``domain.snap``" (of a module that does not
exist here). A comment citing a governance document this tree does not have
(``GONE`` below; this tree's process is PRINCIPLES.md section 6) sends a reader
to a file that is not here. Both kinds were found in shipped code by an
implementation review. The check is a GREP WITH A NAMED ALLOW-LIST, so that a
deliberate reference to such a document, in a sentence that says whose it is,
is written down rather than caught.

WHAT IT DOES NOT CHECK. Prose describing an earlier construction is not the
subject. What it checks is a POINTER: a path or a document name a reader of
THIS repository would follow.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

#: Governance documents this tree does not have; its process is PRINCIPLES.md
#: section 6.
GONE = (
    "ROADMAP.md",
    "STATUS.yaml",
    "REVIEW.md",
    "OPEN_ITEMS.md",
    "AGENT_WORKFLOW.md",
    "ARCHITECTURE_SPEC.md",
    "docs/mathematical-contracts",
)

#: Files that may name one of the above BECAUSE THEY ARE THE FROZEN RECORD OF
#: A RUN IN THAT REPOSITORY (PRINCIPLES.md section 2.3: a registry "moves with
#: its module and is never regenerated"), each naming the repository the run
#: was made in where the sentence is about it.
FROZEN = ("tests/oracles/",)

#: THE ALLOW-LIST, AND IT IS A RATCHET THAT ONLY SHRINKS. It is empty: every
#: shipped tree is clean and stays so; a NEW entry here would be a regression
#: and is the thing this list makes visible.
NOT_YET_SWEPT: tuple[str, ...] = ()
_ALLOWED = FROZEN + NOT_YET_SWEPT


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _shipped(base: str) -> list[Path]:
    return [
        path
        for path in sorted((ROOT / base).rglob("*.py"))
        if not any(_rel(path).startswith(part) for part in _ALLOWED)
    ]


#: The tier PRINCIPLES.md section 10 drops: "not the tier name, not the enum
#: member, not the witness apparatus". A shipped file may say what the
#: PREDECESSOR had, in a sentence that says whose it was; it may not describe a
#: certified path of THIS tree, which has none. Added at the implementation
#: review, round 2 (F-19): domain/assurance.py (now foundations/assurance.py)
#: carried two module constants
#: saying that "the certified path is what supplies a lower bound", which
#: spec/architecture.md 2.8 gives to `first-order`.
DROPPED_TIER = ("the certified path", "certificate post-processing")


@pytest.mark.parametrize("phrase", DROPPED_TIER)
def test_no_shipped_file_describes_the_dropped_tier_as_a_live_path(
    phrase: str,
) -> None:
    offenders = [
        _rel(path)
        for path in _shipped("src")
        if phrase in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], (phrase, offenders)


@pytest.mark.parametrize("token", GONE)
def test_no_source_file_points_at_a_predecessor_process_document(token: str) -> None:
    offenders = [
        _rel(path)
        for path in _shipped("src")
        if token in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], (token, offenders)


def test_the_allow_list_is_named_and_every_entry_of_it_is_still_needed() -> None:
    """A ratchet that only shrinks: an entry that has become unnecessary goes.

    The list is small on purpose. If a sweep has cleaned one of these trees,
    this test says so and the entry is deleted rather than kept out of habit.
    """
    for allowed in NOT_YET_SWEPT:
        assert (ROOT / allowed).is_dir(), allowed
        still_needed = any(
            token in path.read_text(encoding="utf-8")
            for path in sorted((ROOT / allowed).rglob("*.py"))
            for token in GONE
        )
        assert still_needed, f"{allowed} is clean: drop it from NOT_YET_SWEPT"


def test_every_certiqs_key_path_named_in_the_tree_exists() -> None:
    """A path a reader can follow, or none at all.

    Both halves of the tree are scanned, the frozen registries included: a
    frozen value that names a file of THIS repository is either right or is
    evidence of nothing, and a frozen value naming a file of the repository its
    run was made in keeps that repository's spelling.
    """
    pattern = re.compile(r"src/certiqs_key/[A-Za-z0-9_/]+\.py")
    for base in ("src", "tests", "harness"):
        for path in sorted((ROOT / base).rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                assert (ROOT / match.group(0)).exists(), (
                    str(path.relative_to(ROOT)),
                    match.group(0),
                )
