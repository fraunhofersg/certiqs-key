"""``claim_codes.yaml`` against the registries it translates and the claims it names.

WHY THIS FILE EXISTS. The frozen registries pin claims by oracle codes
and are never edited (PRINCIPLES.md section 2.3); ``claim_codes.yaml`` is the one
table that says which claims of this repository a code means, and the interface
tests read their mappings out of it. Two drifts would go unseen without the checks
below: a claim renamed or deleted while the table still names it (the interface
tests look only at their own module's rows), and a code a registry pins that the
table does not translate (a pin nobody can follow to a claim).

WHAT IS DELIBERATELY NOT ASSERTED. That every listed registry file still exists,
and that an id of a submodule whose directory is gone still resolves: a removable
submodule is deleted with its own registry and tests, and the rest of the suite
must stay green after that deletion. The stale row goes with the next edit of the
table.
"""

from __future__ import annotations

import dataclasses
import importlib
import re
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import claim_codes
import pytest

pytestmark = pytest.mark.oracle

ROOT = Path(__file__).resolve().parents[2]
MODULES = ROOT / "spec" / "modules"
HERE = Path(__file__).resolve().parent

#: The code families of the oracle's five contracts.
FAMILIES = frozenset({"C", "PC", "PR", "RC", "SA"})

#: The fields and keys through which a registry pins a claim.
PIN_FIELDS = frozenset({"claims", "supports"})

#: A full claim id: ``<module>/<label>`` or ``<module>/<submodule>/<label>``.
FULL_ID = re.compile(r"^[a-z0-9-]+(/[a-z0-9-]+)?/[a-z]+:[A-Za-z0-9-]+$")


def _registry_files() -> list[Path]:
    return sorted(HERE.glob("registry*.py"))


def _claim_ids() -> set[str]:
    """Return every claim id declared in a claim file, read from its header."""
    ids: set[str] = set()
    for path in MODULES.rglob("claims/*.tex"):
        match = re.search(
            r"^% id: (?P<id>\S+)$", path.read_text(encoding="utf-8"), re.MULTILINE
        )
        assert match is not None, path
        ids.add(match["id"])
    return ids


def _named_ids() -> Iterator[tuple[str, str]]:
    """Yield every claim id the table names, with where it names it."""
    document = claim_codes.document()
    for code, ids in document["codes"].items():
        for claim in ids:
            yield f"codes.{code}", claim
    for code, entry in document["unresolved"].items():
        for claim in entry["candidates"]:
            yield f"unresolved.{code}", claim
    for claim in document["titles"]:
        yield "titles", claim


def _is_code(value: object) -> bool:
    if not isinstance(value, str) or claim_codes.CODE.match(value) is None:
        return False
    return claim_codes.family(value) in FAMILIES


def _pins(module: ModuleType) -> set[str]:
    """Return every string a registry module pins through a ``claims``/``supports``.

    A walk over the module's data: dataclass instances, tuples, lists, sets and
    dicts, collecting the values of the pin fields and keys. Read at run time
    rather than from the source, because some pins are names (``claims=CLAIM_IDS``)
    and some are computed (``ALL_CLAIMS[3:]``).
    """
    found: set[str] = set()
    seen: set[int] = set()
    stack: list[object] = [
        value for name, value in vars(module).items() if not name.startswith("__")
    ]

    def collect(value: object) -> None:
        if isinstance(value, str):
            found.add(value)
        elif isinstance(value, tuple | list | set | frozenset):
            for item in value:
                collect(item)

    while stack:
        value = stack.pop()
        if id(value) in seen or isinstance(value, str | bytes | ModuleType | type):
            continue
        seen.add(id(value))
        if dataclasses.is_dataclass(value):
            for field in dataclasses.fields(value):
                item = getattr(value, field.name)
                if field.name in PIN_FIELDS:
                    collect(item)
                else:
                    stack.append(item)
        elif isinstance(value, dict):
            for key, item in value.items():
                if key in PIN_FIELDS:
                    collect(item)
                else:
                    stack.append(item)
        elif isinstance(value, tuple | list | set | frozenset):
            stack.extend(value)
    return found


def test_every_id_the_table_names_is_a_claim_file() -> None:
    """Each id of ``codes``, ``unresolved`` and ``titles`` is a claim of the tree.

    Read from the claim files' headers, so a rename that ``harness/relabel.py``
    did not carry here, or a claim deleted under the table, is a failure. An id
    whose SUBMODULE directory is absent is passed over: that is a removed
    submodule (see the module docstring), never a core, because a core is not
    removable.
    """
    known = _claim_ids()
    for where, claim in _named_ids():
        assert FULL_ID.match(claim), (where, claim, "not a full id")
        if claim in known:
            continue
        parts = claim.split("/")
        assert (MODULES / parts[0]).is_dir(), (where, claim, "no such core")
        if len(parts) == 3 and not (MODULES / parts[0] / parts[1]).is_dir():
            continue
        raise AssertionError((where, claim, "no claim file declares this id"))


def test_every_code_a_registry_pins_is_in_the_table() -> None:
    """Every oracle code in a ``claims`` or ``supports`` field is translated.

    Either to claims (``codes``), or to no claim with the ground (``no_claim``),
    or as an open question with candidates and evidence (``unresolved``). The
    walk must find codes of all five families, or it is the walk that broke.
    """
    document = claim_codes.document()
    translated = (
        set(document["codes"]) | set(document["no_claim"]) | set(document["unresolved"])
    )
    pinned: dict[str, str] = {}
    for path in _registry_files():
        for value in _pins(importlib.import_module(path.stem)):
            if _is_code(value):
                pinned.setdefault(value, path.name)
    assert {claim_codes.family(code) for code in pinned} == FAMILIES
    missing = sorted(set(pinned) - translated, key=claim_codes.natural_key)
    assert not missing, [(code, pinned[code]) for code in missing]


def test_the_sections_are_disjoint_and_complete_in_themselves() -> None:
    """A code has one disposition, and each disposition says what it rests on."""
    document = claim_codes.document()
    assert set(document) == {"registries", "codes", "no_claim", "unresolved", "titles"}
    sections = {name: document[name] for name in ("codes", "no_claim", "unresolved")}
    seen: dict[str, str] = {}
    for name, table in sections.items():
        assert list(table) == sorted(table, key=claim_codes.natural_key), name
        for code in table:
            assert _is_code(code), (name, code)
            assert code not in seen, (code, seen.get(code), name)
            seen[code] = name
    for code, ids in document["codes"].items():
        assert ids, code
        assert len(set(ids)) == len(ids), code
    for code, ground in document["no_claim"].items():
        assert isinstance(ground, str), code
        assert ground.strip(), code
    for code, entry in document["unresolved"].items():
        assert set(entry) == {"candidates", "evidence"}, code
        assert entry["candidates"], code
        assert entry["evidence"].strip(), code
    titles = document["titles"]
    assert list(titles) == sorted(titles)
    for claim, code in titles.items():
        assert _is_code(code), (claim, code)


def test_every_registry_file_is_listed_with_what_it_moves_with() -> None:
    """A registry file present here has a row, and its owner exists.

    An owner is a core (a directory of ``spec/modules`` with a ``module.yaml``)
    or, for an instance's registry, the instance's directory; a registry pinning
    claims of two cores lists both.
    """
    registries = claim_codes.document()["registries"]
    assert list(registries) == sorted(registries)
    for path in _registry_files():
        key = path.relative_to(ROOT).as_posix()
        assert key in registries, key
        owner = registries[key]
        owners = [owner] if isinstance(owner, str) else owner
        assert owners, key
        for name in owners:
            if name.startswith("instances/"):
                assert (ROOT / name).is_dir(), (key, name)
            else:
                assert (MODULES / name / "module.yaml").is_file(), (key, name)
