#!/usr/bin/env python3
r"""Motivation: a claim id renamed in spec/ and missed everywhere else.

Renaming, re-kinding and moving claims is routine editorial work. A claim id does not
live in ``spec/`` alone, where ``check_claims`` validates it: code docstrings,
``CLAIM_ROOTS`` and the generated ``claim_closure.json`` a run record reads,
the frozen oracle registries and their tests, instances and runs all name
claims by id. An id missed outside ``spec/`` fails silently (a docstring that
points at a claim which no longer exists) or only at a distant test.
The cost is one command per rename; the error it prevents is a stale id
outside the checker's reach.

OPERATIONS. A 1:1 rename ``OLD -> NEW`` of full ids (``<module>/<label>`` or
``<module>/<submodule>/<label>``, label ``<kind>:<slug>``): a slug change, a
kind change that keeps the proof obligation (thm/lem/prop/cor among
themselves; def/ass/rem/ex/fact/req among themselves -- ``req``, environment
``requirement``), and a move to another module or submodule. A kind change
across the proof boundary is refused. Splits and merges are not performed:
``--split``/``--merge`` record the entry in the map file and print every
reference site of the old ids for the editor to repair by hand.

WHAT A RENAME REWRITES. In ``spec/``: the claim file's name (and directory, on
a move), its header ``id`` and ``kind``, the claim environment and its
``\label``; the ``order`` entry and any ``reading_groups[].start`` of
``module.yaml`` (on a move the entry leaves the old order, a group anchored on
it re-anchors on its next member, and the entry is appended to the new
module's order); every ``uses``/``mentions``/``pending``/``supersedes`` entry,
a bare label within the owning module and a full id across modules, as
``check_claims`` resolves them; every reference in a claim body -- ``\ref``,
``\eqref``, ``\cref``, ``\Cref``, ``\autoref``, ``\texttt{...}``, ``[[...]]``,
``\xref{full-id}`` and plain occurrences -- where a bare label is rewritten
only inside the contract (the core with its submodules) where it resolves to
the claim, as LaTeX resolves it in the assembled contract; full ids and bare
labels in the owning contract's ``interface.yaml``, ``design.md`` and other
authored files; full ids in every other authored file of ``spec/``. On a move
across contracts a reference that becomes foreign is rewritten from
``\ref{label}`` to ``\xref{new-full-id}`` and a bare header entry to a full
id; a full-id header entry that becomes local turns bare. In ``src/``,
``tests/`` (the frozen oracle registries included), ``instances/`` and
``runs/``: every full id, anywhere, and every bare label inside the code
package of the owning contract (from the ``code:`` field of
``spec/modules.yaml``, the ``src/certiqs_key/<module>`` convention, and the
files named by the contract's ``implements`` fields). Partial ids
``<submodule>/<label>``, which the tree uses in prose, are rewritten like full
ids when the submodule name is unique. Then ``claim_closure.json`` is
regenerated (``python -m harness.generate_claim_closure``).

WHAT IT ONLY PRINTS, for repair by hand: a bare label outside the scope where
it resolves (tests, shared code, another contract's claims, top-level spec
documents); a bare label in a claim header's free text (``notes`` is largely
history); an ambiguous label; a multi-target ``\cref`` that a move makes
foreign; an ``\eqref`` into an equation of a claim moving to another contract;
the kind word before a reference to a re-kinded claim or before a new
``\xref``; a ``uses`` edge a move takes outside ``depends_on``; a reading
group a move empties; a mention of the old claim file name; full ids in
``harness/`` and the top-level documents.

WHAT IT NEVER TOUCHES: ``reports/``, ``state/``, ``context/`` (history, never
rewritten), ``refs/``, ``.git``, ``build/``, ``tmp/``, generated files
(``contract.tex``, ``contract.pdf``, ``graphs/``, ``spec/module-graph.*``),
``HUMAN_SCRATCHPAD.md``, and anything that is not
the id string: numbers and oracle codes such as C5, PC9 or SA3 are never
matched, because a token must be a whole ``<kind>:<slug>`` id with no id
character touching either end (``thm:c1`` never matches inside ``thm:c17``,
``meat-core/def:x`` never inside ``meat-core/def:x-y``).

THE MAP FILE (``--map-out``) is cumulative JSON
``{"renames": {old: new}, "splits": {old: [new, ...]}, "merges": {new: [old,
...]}, "deleted": [...]}`` of full ids, keys sorted, LF. An existing file is
merged: a chain ``a -> b`` then ``b -> c`` collapses to ``a -> c`` and keeps
``b -> c``, so every id that ever existed maps to its current name. It is read
by ``harness/math_diff.py`` and by the frontend demo repository.

Usage:
    python -m harness.relabel OLD_ID NEW_ID [--dry-run] [--map-out PATH]
    python -m harness.relabel --map renames.yaml [--dry-run] [--map-out PATH]
    python -m harness.relabel --split OLD --into NEW1,NEW2 [--dry-run] --map-out PATH
    python -m harness.relabel --merge OLD1,OLD2 --into NEW [--dry-run] --map-out PATH

``--dry-run`` prints every planned edit (file, line, old -> new) and every
site left for repair by hand, and writes nothing. Exit 0 on success; 1 on a
refusal (unknown old id, new id already present, a kind change across the
proof boundary), which writes nothing, or on an error. A failed regeneration
of the closure table (the checker refuses the graph, for instance while it
does not know ``req``) also exits 1, after the relabel itself is written: the
message says so, and ``python -m harness.generate_claim_closure`` finishes it.
``--repo`` defaults to this checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from harness.check_claims import (
    KIND_ENV,
    PROOF_KINDS,
    SLUG_RE,
    Claim,
    Repo,
    allowed_modules,
    discover_modules,
    read_claim,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMAND = "python -m harness.relabel"

# `req` (Requirement: what the implementation must do or refuse) is a kind
# with no proof.
ALL_KIND_ENV: dict[str, str] = {**KIND_ENV, "req": "requirement"}
KIND_WORD: dict[str, str] = {k: env.capitalize() for k, env in ALL_KIND_ENV.items()}

_KINDS = "|".join(sorted(ALL_KIND_ENV, key=len, reverse=True))
_SEG = r"[a-z0-9][a-z0-9-]*"
_LABEL = rf"(?:{_KINDS}):[a-z0-9][a-z0-9-]*"
# A token is maximal: no id character may touch it on either side. This is
# the word-boundary safety: thm:c1 never matches inside thm:c17, and
# meat-core/def:x never inside meat-core/def:x-y or core-b/meat-core/def:x.
BARE_RE = re.compile(rf"(?<![A-Za-z0-9_/.:-])(?P<tok>{_LABEL})(?![A-Za-z0-9_])")
PATH_RE = re.compile(
    rf"(?<![A-Za-z0-9_/.:-])(?P<tok>{_SEG}(?:/{_SEG})?/{_LABEL})(?![A-Za-z0-9_])"
)
LABEL_FULL_RE = re.compile(rf"{_LABEL}")
SEG_RE = re.compile(_SEG)
REF_CMD_RE = re.compile(
    r"\\(?P<cmd>ref|eqref|cref|Cref|autoref)\*?\{(?P<args>[^{}]*)\}")
WIKI_RE = re.compile(r"\[\[(?P<inner>[^\[\]\n]*)\]\]")
KIND_WORD_RE = re.compile(
    r"(?P<word>" + "|".join(sorted(set(KIND_WORD.values()))) + r")s?[~\s]*$"
)
FIELD_RE = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*:")

LIST_FIELDS = frozenset({"uses", "mentions", "pending", "supersedes"})
SCAN_ROOTS = ("spec", "src", "tests", "instances", "runs")
REPORT_ROOTS = ("harness",)
TEXT_SUFFIXES = frozenset({
    ".tex", ".md", ".yaml", ".yml", ".json", ".py", ".pyi", ".toml", ".txt",
    ".csv", ".rst", ".cfg", ".ini",
})
SKIP_DIR_NAMES = frozenset({"__pycache__", "node_modules", "build", "tmp"})
# A fixture repository of the checker's own tests is a separate universe of
# ids (core-a/def:base), never a reference to this tree's claims.
SKIP_PREFIXES = ("tests/harness/fixtures/",)
NEVER_READ = frozenset({"HUMAN_SCRATCHPAD.md"})
MAP_KEYS = ("renames", "splits", "merges", "deleted")


class RelabelError(Exception):
    """A refusal: the requested relabel is not performed and nothing is written."""


# ---------------------------------------------------------------------------
# ids
# ---------------------------------------------------------------------------

def module_of(claim_id: str) -> str:
    """Return the module part of a full claim id."""
    return claim_id.rpartition("/")[0]


def label_of(claim_id: str) -> str:
    """Return the ``<kind>:<slug>`` label of a full claim id."""
    return claim_id.rpartition("/")[2]


def core_of(claim_or_module: str) -> str:
    """Return the core (the contract) of a claim id or module id."""
    return claim_or_module.split("/", 1)[0]


def kind_of(label_or_id: str) -> str:
    """Return the kind of a label or full id."""
    return label_of(label_or_id).split(":", 1)[0]


def file_name(label: str) -> str:
    """Return the claim file name ``<kind>-<slug>.tex`` of a label."""
    kind, _, slug = label.partition(":")
    return f"{kind}-{slug}.tex"


def check_id(claim_id: str) -> None:
    """Refuse a string that is not a full claim id of the claim-file format."""
    module, sep, label = claim_id.rpartition("/")
    segments = module.split("/") if sep else []
    kind, colon, slug = label.partition(":")
    if (not segments or len(segments) > 2
            or not all(SEG_RE.fullmatch(s) for s in segments)
            or not colon or kind not in ALL_KIND_ENV or not SLUG_RE.match(slug)):
        raise RelabelError(
            f"'{claim_id}' is not a full claim id '<module>[/<submodule>]/"
            f"<kind>:<slug>' with kind in {', '.join(ALL_KIND_ENV)}")


def needs_proof(kind: str) -> bool:
    """Return whether a kind carries a proof environment."""
    return kind in PROOF_KINDS


# ---------------------------------------------------------------------------
# the index: claims, contracts and code scopes, read once
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClaimInfo:
    """One claim as the relabel reads it: identity, file, labels, header edges."""

    claim_id: str
    module_id: str
    label: str
    path: Path
    own_labels: frozenset[str]
    uses: tuple[str, ...]
    header_refs: frozenset[str]
    implements: str


@dataclass
class Index:
    """The tree a relabel is planned against, as it stands before the change."""

    root: Path
    repo: Repo
    claims: dict[str, ClaimInfo]
    by_path: dict[str, str]
    contract_labels: dict[tuple[str, str], list[str]]
    unique_subs: dict[str, str]
    code_scopes: dict[str, tuple[str, ...]]
    module_dirs: dict[str, str]

    def rel(self, path: Path) -> str:
        """Return a root-relative posix path."""
        return path.resolve().relative_to(self.root.resolve()).as_posix()

    def scope_contracts(self, rel: str) -> set[str]:
        """Return the contracts whose code package contains ``rel``."""
        return {core for core, prefixes in self.code_scopes.items()
                if any(rel == p or rel.startswith(p + "/") for p in prefixes)}

    def module_path(self, module_id: str) -> Path:
        """Return the directory of a module."""
        return self.repo.modules[module_id].path


def _registry_code_paths(root: Path) -> dict[str, str]:
    """Read the ``code:`` path of each module from ``spec/modules.yaml``."""
    try:
        registry = root / "spec" / "modules.yaml"
        data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    out: dict[str, str] = {}

    def record(module_id: str, value: Any) -> None:
        words = value.split() if isinstance(value, str) else []
        token = words[0].rstrip(",;").rstrip("/") if words else ""
        if token.startswith("src/"):
            out[module_id] = token

    cores = data.get("cores") if isinstance(data, dict) else None
    for core in cores if isinstance(cores, list) else []:
        if not isinstance(core, dict):
            continue
        core_id = str(core.get("id", ""))
        record(core_id, core.get("code"))
        subs = core.get("submodules")
        for sub in subs if isinstance(subs, list) else []:
            if isinstance(sub, dict):
                record(f"{core_id}/{sub.get('id', '')}", sub.get("code"))
    return out


def load_index(root: Path) -> Index:
    """Read modules and claims (``req`` included) with ``check_claims``'s loader."""
    repo = Repo(root=root)
    discover_modules(repo)
    raw: list[Claim] = []
    for module_id in sorted(repo.modules):
        module = repo.modules[module_id]
        claims_dir = module.path / "claims"
        if not claims_dir.is_dir():
            continue
        for path in sorted(claims_dir.glob("*.tex")):
            kind, sep, slug = path.stem.partition("-")
            if not sep or kind not in ALL_KIND_ENV or not SLUG_RE.match(slug):
                continue
            claim = read_claim(repo, module, path)
            if claim is not None:
                raw.append(claim)
    ids = {claim.claim_id for claim in raw}
    owners = {str(c.header.get("short_id", "")).strip(): c.claim_id
              for c in raw if kind_of(c.label) == "ass" and c.header.get("short_id")}

    def resolve(module_id: str, entry: str) -> str | None:
        candidate = entry if "/" in entry else f"{module_id}/{entry}"
        return candidate if candidate in ids else None

    claims: dict[str, ClaimInfo] = {}
    for c in raw:
        uses = tuple(t for t in (resolve(c.module_id, e) for e in c.uses) if t)
        mentions = tuple(t for t in (resolve(c.module_id, e) for e in c.mentions) if t)
        assumed = tuple(owners[s] for s in c.assumes if s in owners)
        claims[c.claim_id] = ClaimInfo(
            claim_id=c.claim_id, module_id=c.module_id, label=c.label, path=c.path,
            own_labels=frozenset(c.own_labels), uses=uses,
            header_refs=frozenset((*uses, *mentions, *assumed)),
            implements=str(c.header.get("implements") or ""),
        )
    root_resolved = root.resolve()
    by_path = {c.path.resolve().relative_to(root_resolved).as_posix(): cid
               for cid, c in claims.items()}
    contract_labels: dict[tuple[str, str], list[str]] = {}
    for cid in sorted(claims):
        contract_labels.setdefault((core_of(cid), label_of(cid)), []).append(cid)
    sub_count: dict[str, list[str]] = {}
    for module_id in repo.modules:
        if "/" in module_id:
            sub_count.setdefault(module_id.split("/")[1], []).append(module_id)
    cores = {m for m in repo.modules if "/" not in m}
    unique_subs = {name: found[0] for name, found in sub_count.items()
                   if len(found) == 1 and name not in cores}
    declared = _registry_code_paths(root)
    scopes: dict[str, list[str]] = {}
    for module_id in sorted(repo.modules):
        found: list[str] = []
        if module_id in declared:
            found.append(declared[module_id])
        else:
            conv = "src/certiqs_key/" + "/".join(
                seg.replace("-", "_") for seg in module_id.split("/"))
            if (root / conv).is_dir():
                found.append(conv)
            elif (root / f"{conv}.py").is_file():
                found.append(f"{conv}.py")
        scopes.setdefault(core_of(module_id), []).extend(found)
    for cid, info in claims.items():
        target = info.implements.partition(":")[0].strip()
        if not target:
            continue
        base = "src/" + target.replace(".", "/")
        if (root / f"{base}.py").is_file():
            scopes.setdefault(core_of(cid), []).append(f"{base}.py")
        elif (root / base).is_dir():
            scopes.setdefault(core_of(cid), []).append(base)
    module_dirs = {module.path.resolve().relative_to(root_resolved).as_posix(): mid
                   for mid, module in repo.modules.items()}
    return Index(
        root=root, repo=repo, claims=claims, by_path=by_path,
        contract_labels=contract_labels, unique_subs=unique_subs,
        code_scopes={core: tuple(sorted(set(p))) for core, p in scopes.items()},
        module_dirs=module_dirs,
    )


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------

def validate(idx: Index, renames: Mapping[str, str]) -> None:
    """Refuse a rename batch that the tree cannot take; return when it can."""
    if not renames:
        raise RelabelError("nothing to rename")
    news = list(renames.values())
    doubled = sorted({n for n in news if news.count(n) > 1})
    if doubled:
        raise RelabelError(f"two old ids are renamed to the same new id '{doubled[0]}'")
    for old, new in renames.items():
        check_id(old)
        check_id(new)
        if old not in idx.claims:
            raise RelabelError(f"unknown old id '{old}': no claim file defines it")
        if old == new:
            raise RelabelError(f"'{old}' is renamed to itself")
        if module_of(new) not in idx.repo.modules:
            raise RelabelError(f"'{new}': module '{module_of(new)}' does not exist "
                               "(a move goes to an existing module or submodule)")
        if new in idx.claims and new not in renames:
            raise RelabelError(f"new id '{new}' already exists")
        old_kind, new_kind = kind_of(old), kind_of(new)
        if needs_proof(old_kind) != needs_proof(new_kind):
            with_proof = ", ".join(sorted(PROOF_KINDS))
            raise RelabelError(
                f"'{old}' -> '{new}': the kind change {old_kind} -> {new_kind} "
                f"crosses the proof boundary ({with_proof} carry a proof, the "
                "other kinds none); that is a rewrite of the claim, not a relabel")
        target = idx.module_path(module_of(new)) / "claims" / file_name(label_of(new))
        moving_away = {idx.claims[o].path.resolve() for o in renames}
        if target.exists() and target.resolve() not in moving_away:
            raise RelabelError(f"'{new}': the file {idx.rel(target)} already exists")
    # A label is unique per assembled contract, or \ref resolves to the wrong claim.
    after: dict[tuple[str, str], list[str]] = {}
    for cid in idx.claims:
        if cid not in renames:
            after.setdefault((core_of(cid), label_of(cid)), []).append(cid)
    for new in news:
        after.setdefault((core_of(new), label_of(new)), []).append(new)
    for new in news:
        clash = [c for c in after[(core_of(new), label_of(new))] if c != new]
        if clash:
            raise RelabelError(
                f"'{new}': its label is already used in the contract "
                f"'{core_of(new)}' by '{clash[0]}'; a bare \\ref would be ambiguous")


# ---------------------------------------------------------------------------
# the plan
# ---------------------------------------------------------------------------

@dataclass(frozen=True, order=True)
class Change:
    """One text replacement: ``text[start:end]`` becomes ``new``."""

    start: int
    end: int
    new: str
    old: str
    line: int


@dataclass(frozen=True, order=True)
class Note:
    """A site left for repair by hand (or, for a split/merge, a reference site)."""

    path: str
    line: int
    message: str

    def render(self) -> str:
        """Return ``path:line: message``."""
        return f"{self.path}:{self.line}: {self.message}"


@dataclass
class FilePlan:
    """The planned edits of one file, against its bytes as read."""

    path: Path
    rel: str
    text: str
    new_path: Path | None = None
    changes: list[Change] = field(default_factory=list)

    def line_at(self, offset: int) -> int:
        """Return the 1-based line of a character offset."""
        return self.text.count("\n", 0, offset) + 1

    def new_text(self) -> str:
        """Return the text with every change applied."""
        out: list[str] = []
        position = 0
        for change in sorted(set(self.changes)):
            if change.start < position:
                raise RelabelError(f"{self.rel}: overlapping edits at line "
                                   f"{change.line} (a relabel bug; nothing written)")
            out.append(self.text[position:change.start])
            out.append(change.new)
            position = change.end
        out.append(self.text[position:])
        return "".join(out)


@dataclass
class Plan:
    """Everything a relabel would do, computed before anything is written."""

    root: Path
    renames: dict[str, str]
    files: dict[str, FilePlan]
    notes: list[Note]

    def edits(self) -> list[tuple[FilePlan, Change]]:
        """Return every change, by file and position."""
        return [(self.files[rel], change) for rel in sorted(self.files)
                for change in sorted(set(self.files[rel].changes))]

    def moves(self) -> list[FilePlan]:
        """Return the files that change path."""
        return [self.files[r] for r in sorted(self.files)
                if self.files[r].new_path is not None]


def iter_files(root: Path) -> Iterator[tuple[Path, str, bool]]:
    """Yield ``(path, rel, report_only)`` for every file a relabel reads.

    ``spec/``, ``src/``, ``tests/``, ``instances/`` and ``runs/`` are
    rewritten; ``harness/`` and the top-level documents are only reported.
    """
    tops = [(r, False) for r in SCAN_ROOTS] + [(r, True) for r in REPORT_ROOTS]
    for top, report_only in tops:
        base = root / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(
                d for d in dirnames
                if not d.startswith(".") and d not in SKIP_DIR_NAMES
                and not d.endswith(".egg-info"))
            for name in sorted(filenames):
                path = Path(dirpath) / name
                rel = path.relative_to(root).as_posix()
                if (path.suffix in TEXT_SUFFIXES and not is_generated(rel)
                        and not rel.startswith(SKIP_PREFIXES)):
                    yield path, rel, report_only
    for path in sorted(root.glob("*.md")):
        if path.name not in NEVER_READ:
            yield path, path.name, True


def is_generated(rel: str) -> bool:
    """Return whether a spec path is generated by the assembler or the graphs."""
    parts = rel.split("/")
    if parts[0] != "spec":
        return False
    if len(parts) == 2 and parts[1].startswith("module-graph."):
        return True
    return len(parts) > 2 and parts[1] == "modules" and (
        "graphs" in parts[2:-1] or parts[-1].startswith("contract."))


def read_text(path: Path) -> str | None:
    """Return a file's text exactly as stored (no newline translation), or None."""
    data = path.read_bytes()
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def header_fields(text: str) -> tuple[list[tuple[int, int, str]], int]:
    """Return the ``(start, end, field)`` spans of header lines and the body offset.

    A header line belongs to the last top-level key opened above it, so a
    folded ``summary`` or a block list belongs to its field.
    """
    spans: list[tuple[int, int, str]] = []
    offset = 0
    state = "before"
    current = ""
    for line in text.split("\n"):
        start, end = offset, offset + len(line)
        offset = end + 1
        stripped = line.strip()
        if state == "before":
            if not stripped:
                continue
            if stripped != "% ---":
                return [], 0
            state = "header"
            continue
        if stripped == "% ---":
            return spans, min(offset, len(text))
        content = line.lstrip()[1:] if line.lstrip().startswith("%") else line
        content = content[1:] if content.startswith(" ") else content
        match = FIELD_RE.match(content)
        if match and not content.startswith((" ", "\t")):
            current = match.group("key")
        spans.append((start, end, current))
    return [], 0


class Planner:
    """Computes the edits and the manual-repair sites of one relabel batch.

    Every reference is resolved against the tree as it stands, and its new
    text is computed from the batch: ``new_id(target)`` seen from the new
    home of the referencing claim. That one rule covers a rename, a move and
    the references a moved claim itself makes to its old neighbours.
    ``report`` names ids whose sites are only listed (a split or a merge).
    """

    def __init__(self, idx: Index, renames: Mapping[str, str],
                 report: Iterable[str] = ()) -> None:
        """Prepare a plan for ``renames`` (and ``report`` ids to list only)."""
        self.idx = idx
        self.m = dict(renames)
        self.report = set(report)
        self.targets = set(self.m) | self.report
        self.old_labels = {label_of(t) for t in self.targets}
        self.movers = {o for o, n in self.m.items() if module_of(o) != module_of(n)}
        self.cross = {o for o, n in self.m.items() if core_of(o) != core_of(n)}
        self.cross_eq: dict[tuple[str, str], str] = {
            (core_of(o), lab): o for o in self.cross
            for lab in idx.claims[o].own_labels if lab != label_of(o)}
        self.renamed_files = {
            file_name(label_of(o)): o for o, n in self.m.items()
            if file_name(label_of(o)) != file_name(label_of(n))}
        self.files: dict[str, FilePlan] = {}
        self.notes: set[Note] = set()

    # -- helpers -----------------------------------------------------------

    def new_id(self, claim_id: str) -> str:
        """Return a claim's id after the batch."""
        return self.m.get(claim_id, claim_id)

    def change(self, fp: FilePlan, start: int, end: int, new: str) -> None:
        """Record one replacement unless it changes nothing."""
        old = fp.text[start:end]
        if new != old:
            fp.changes.append(Change(start, end, new, old, fp.line_at(start)))

    def note(self, fp: FilePlan, offset: int, message: str) -> None:
        """Record a manual-repair site."""
        self.notes.add(Note(fp.rel, fp.line_at(offset), message))

    def partial_form(self, claim_id: str) -> str:
        """Return ``<submodule>/<label>`` where the submodule name is unique."""
        module = module_of(claim_id)
        if "/" in module:
            sub = module.split("/")[1]
            if self.idx.unique_subs.get(sub) == module:
                return f"{sub}/{label_of(claim_id)}"
        return claim_id

    def resolve_path(self, token: str) -> tuple[str | None, bool]:
        """Resolve a ``module/label`` or ``submodule/label`` token; flag partials."""
        module, _, label = token.rpartition("/")
        if module in self.idx.repo.modules or token in self.targets:
            return token, False
        if "/" not in module and module in self.idx.unique_subs:
            return f"{self.idx.unique_subs[module]}/{label}", True
        return None, False

    def tokens(self, pattern: re.Pattern[str], fp: FilePlan, lo: int,
               hi: int) -> Iterator[tuple[int, int, str]]:
        """Yield ``(start, end, token)``, a trailing hyphen dropped."""
        for match in pattern.finditer(fp.text, lo, hi):
            token = match.group("tok").rstrip("-")
            yield match.start("tok"), match.start("tok") + len(token), token

    def scan_paths(self, fp: FilePlan, lo: int, hi: int,
                   report_only: bool = False) -> None:
        """Rewrite full and partial ids of renamed claims (or report them)."""
        for start, end, token in self.tokens(PATH_RE, fp, lo, hi):
            target, partial = self.resolve_path(token)
            if target is None or target not in self.targets:
                continue
            if target in self.report or report_only:
                self.note(fp, start, f"names {target}"
                          + (f" (now {self.m[target]})" if target in self.m else ""))
                continue
            new = self.m[target]
            self.change(fp, start, end, self.partial_form(new) if partial else new)

    def report_possible(self, fp: FilePlan, start: int, token: str,
                        where: str) -> None:
        """List a bare label that may name a target but is not rewritten here."""
        named = sorted(t for t in self.targets if label_of(t) == token)
        if named:
            self.note(fp, start, f"bare '{token}' {where}, not rewritten; "
                      f"if it names {' or '.join(named)}, write "
                      + " or ".join(self.m.get(t, t) for t in named))

    def new_bare(self, target: str, home_contract: str) -> str:
        """Return a target's new text seen from ``home_contract``: bare if local."""
        new = self.new_id(target)
        return label_of(new) if core_of(new) == home_contract else new

    # -- zones -------------------------------------------------------------

    def run(self) -> Plan:
        """Scan every file and return the plan."""
        forced = {self.idx.rel(self.idx.claims[o].path) for o in self.m}
        for old, new in self.m.items():
            for module_id in {module_of(old), module_of(new)}:
                meta = self.idx.module_path(module_id) / "module.yaml"
                forced.add(self.idx.rel(meta))
        needles = (self.old_labels | set(self.renamed_files)
                   | {lab for (_, lab) in self.cross_eq})
        for path, rel, report_only in iter_files(self.idx.root):
            text = read_text(path)
            if text is None or (rel not in forced
                                and not any(n in text for n in needles)):
                continue
            fp = FilePlan(path=path, rel=rel, text=text)
            self.dispatch(fp, report_only)
            self.scan_file_names(fp)
            if fp.changes:
                self.files[rel] = fp
        for old, new in self.m.items():
            info = self.idx.claims[old]
            rel = self.idx.rel(info.path)
            fp = self.files.get(rel) or FilePlan(
                info.path, rel, read_text(info.path) or "")
            target = (self.idx.module_path(module_of(new)) / "claims"
                      / file_name(label_of(new)))
            if target.resolve() != info.path.resolve():
                fp.new_path = target
            self.files[rel] = fp
        self.check_fences()
        self.kind_notes()
        return Plan(self.idx.root, dict(self.m), self.files, sorted(self.notes))

    def dispatch(self, fp: FilePlan, report_only: bool) -> None:
        """Route a file to the rules of its zone."""
        rel = fp.rel
        if report_only:
            self.scan_paths(fp, 0, len(fp.text), report_only=True)
        elif rel in self.idx.by_path:
            self.process_claim(fp, self.idx.claims[self.idx.by_path[rel]])
        elif rel.startswith("spec/modules/") and rel.endswith("/module.yaml"):
            module_id = self.idx.module_dirs.get(rel.rpartition("/")[0])
            self.process_module_yaml(fp, module_id)
        elif rel.startswith("spec/modules/") and len(rel.split("/")) > 3:
            self.process_contract_doc(fp)
        elif rel.startswith("spec/"):
            self.scan_paths(fp, 0, len(fp.text))
            for start, _end, token in self.tokens(BARE_RE, fp, 0, len(fp.text)):
                self.report_possible(fp, start, token,
                                     "in a document outside the contracts")
        else:
            self.process_code(fp)

    def scan_file_names(self, fp: FilePlan) -> None:
        """List mentions of a claim file whose name the batch changes."""
        for name, old in self.renamed_files.items():
            pattern = re.compile(r"(?<![A-Za-z0-9_.-])" + re.escape(name)
                                 + r"(?![A-Za-z0-9_])")
            for match in pattern.finditer(fp.text):
                self.note(fp, match.start(), f"names the claim file {name}, which "
                          f"becomes {file_name(label_of(self.m[old]))}")

    # -- claim files ---------------------------------------------------------

    def process_claim(self, fp: FilePlan, x: ClaimInfo) -> None:
        """Rewrite one claim file: header fields, body references, environment."""
        spans, body = header_fields(fp.text)
        for start, end, name in spans:
            if name in LIST_FIELDS:
                self.header_entries(fp, x, start, end, name)
            elif name == "kind":
                self.header_kind(fp, x, start, end)
            else:
                self.scan_paths(fp, start, end)
                self.header_text(fp, x, start, end)
        self.body(fp, x, body)
        if x.claim_id in self.m and kind_of(x.claim_id) != kind_of(self.m[x.claim_id]):
            self.environment(fp, x, body)

    def header_kind(self, fp: FilePlan, x: ClaimInfo, start: int, end: int) -> None:
        """Rewrite the header ``kind`` of a re-kinded claim."""
        if x.claim_id not in self.m:
            return
        match = re.search(r"kind\s*:\s*(?P<k>[a-z]+)", fp.text[start:end])
        if match:
            self.change(fp, start + match.start("k"), start + match.end("k"),
                        kind_of(self.m[x.claim_id]))

    def header_entries(self, fp: FilePlan, x: ClaimInfo, start: int, end: int,
                       name: str) -> None:
        """Rewrite ``uses``-style entries: bare within a module, full id across."""
        home_new = module_of(self.new_id(x.claim_id))
        moved = x.claim_id in self.movers
        found = [(s, e, t, False) for s, e, t in self.tokens(PATH_RE, fp, start, end)]
        found += [(s, e, t, True) for s, e, t in self.tokens(BARE_RE, fp, start, end)]
        for s, e, token, bare in found:
            target = f"{x.module_id}/{token}" if bare else token
            if target not in self.idx.claims and target not in self.targets:
                continue
            if target in self.report:
                self.note(fp, s, f"{name} entry '{token}' names {target}")
                continue
            if target not in self.m and not moved:
                continue
            new = self.new_id(target)
            local = module_of(new) == home_new
            if bare:
                text = label_of(new) if local else new
            else:
                shifted = moved or module_of(new) != module_of(target)
                text = label_of(new) if local and shifted else new
            self.change(fp, s, e, text)

    def header_text(self, fp: FilePlan, x: ClaimInfo, start: int, end: int) -> None:
        """Header free text: rewrite ``[[label]]``; list other bare labels."""
        wiki = [(m.start("inner"), m.end("inner"))
                for m in WIKI_RE.finditer(fp.text, start, end)]
        for s, e, token in self.tokens(BARE_RE, fp, start, end):
            target, foreign, cands = self.resolve_in_claim(x, token)
            if target is None:
                self.unresolved(fp, x, s, token, foreign, cands)
            elif any(a <= s and e <= b for a, b in wiki):
                self.rewrite_claim_token(fp, x, s, e, target)
            elif target in self.targets or (
                    x.claim_id in self.cross and target != x.claim_id):
                new = self.new_bare(target, core_of(self.new_id(x.claim_id)))
                if new != token:
                    self.note(fp, s, f"bare '{token}' in the header's free text "
                              f"names {target}; not rewritten (write {new} if the "
                              "text is current)")

    def resolve_in_claim(self, x: ClaimInfo,
                         token: str) -> tuple[str | None, str | None, list[str]]:
        """Resolve a bare label written in claim ``x``, as the contract does.

        Returns ``(target, foreign, candidates)``: ``target`` the claim it
        names within ``x``'s contract (itself included), ``foreign`` a claim of
        another contract that ``x``'s header names with that label, and the
        contract's candidates when there are several.
        """
        if token == x.label:
            return x.claim_id, None, [x.claim_id]
        cands = self.idx.contract_labels.get((core_of(x.claim_id), token), [])
        header = [h for h in x.header_refs if label_of(h) == token]
        other = header[0] if len(header) == 1 and header[0] not in cands else None
        if len(cands) == 1:
            return cands[0], other, cands
        if len(header) == 1 and header[0] in cands:
            return header[0], None, cands
        return None, other, cands

    def unresolved(self, fp: FilePlan, x: ClaimInfo, start: int, token: str,
                   foreign: str | None, cands: list[str]) -> None:
        """List a bare label in a claim that may name a target it cannot reach."""
        if foreign is not None and foreign in self.targets:
            xref = f"\\xref{{{self.new_id(foreign)}}}"
            self.note(fp, start, f"bare '{token}' names {foreign} of another "
                      f"contract; not rewritten, write {xref}")
        elif len(cands) > 1 and self.targets & set(cands):
            self.note(fp, start, f"bare '{token}' is ambiguous in "
                      f"{core_of(x.claim_id)} ({', '.join(cands)}); not rewritten")
        elif not cands and foreign is None:
            self.report_possible(fp, start, token,
                                 "resolves in no claim of this contract")

    def rewrite_claim_token(self, fp: FilePlan, x: ClaimInfo, start: int, end: int,
                            target: str) -> None:
        r"""Rewrite a resolved bare label outside a ``\ref``: bare if still local."""
        if target in self.report:
            self.note(fp, start, f"'{fp.text[start:end]}' names {target}")
            return
        if target in self.m or x.claim_id in self.cross:
            self.change(fp, start, end,
                        self.new_bare(target, core_of(self.new_id(x.claim_id))))

    def body(self, fp: FilePlan, x: ClaimInfo, lo: int) -> None:
        """Rewrite the references of a claim body."""
        hi = len(fp.text)
        self.scan_paths(fp, lo, hi)
        consumed: list[tuple[int, int]] = []
        for cmd in REF_CMD_RE.finditer(fp.text, lo, hi):
            consumed.append((cmd.start("args"), cmd.end("args")))
            self.ref_command(fp, x, cmd)
        for s, e, token in self.tokens(BARE_RE, fp, lo, hi):
            if any(a <= s and e <= b for a, b in consumed):
                continue
            target, foreign, cands = self.resolve_in_claim(x, token)
            if target is None:
                self.unresolved(fp, x, s, token, foreign, cands)
                continue
            if foreign is not None and {foreign, target} & self.targets:
                self.note(fp, s, f"bare '{token}' resolves to {target} in this "
                          f"contract although the header names {foreign}")
            self.rewrite_claim_token(fp, x, s, e, target)

    def ref_command(self, fp: FilePlan, x: ClaimInfo, cmd: re.Match[str]) -> None:
        r"""Rewrite one ``\ref``-family command; a now-foreign target gets ``\xref``."""
        args_at = cmd.start("args")
        parts: list[tuple[int, int, str]] = []
        offset = 0
        for piece in cmd.group("args").split(","):
            stripped = piece.strip()
            if stripped:
                s = args_at + offset + piece.index(stripped)
                parts.append((s, s + len(stripped), stripped))
            offset += len(piece) + 1
        home_new = core_of(self.new_id(x.claim_id))
        for s, e, token in parts:
            if not LABEL_FULL_RE.fullmatch(token):
                self.equation_ref(fp, x, cmd, token)
                continue
            target, foreign, cands = self.resolve_in_claim(x, token)
            if target is None:
                self.unresolved(fp, x, s, token, foreign, cands)
                continue
            if target in self.report:
                self.note(fp, s, f"\\{cmd.group('cmd')}{{{token}}} names {target}")
                continue
            if target not in self.m and x.claim_id not in self.cross:
                continue
            new = self.new_id(target)
            if core_of(new) == home_new:
                self.change(fp, s, e, label_of(new))
                self.kind_word(fp, cmd.start(), target, new)
            elif len(parts) == 1:
                self.change(fp, cmd.start(), cmd.end(), f"\\xref{{{new}}}")
                before = fp.text[max(0, cmd.start() - 24):cmd.start()]
                word = KIND_WORD_RE.search(before)
                if word:
                    self.note(fp, cmd.start(), f"'{word.group('word')}' before the new "
                              f"\\xref{{{new}}}, which renders the kind itself")
            else:
                self.note(fp, s, f"\\{cmd.group('cmd')}{{{cmd.group('args')}}}: "
                          f"'{token}' becomes {new} in another contract; split the "
                          "reference and write \\xref by hand")

    def kind_word(self, fp: FilePlan, at: int, old: str, new: str) -> None:
        """List a kind word before a reference to a re-kinded claim."""
        if kind_of(old) == kind_of(new):
            return
        word = KIND_WORD_RE.search(fp.text[max(0, at - 24):at])
        if word and word.group("word") != KIND_WORD[kind_of(new)]:
            self.note(fp, at, f"'{word.group('word')}' before a reference to {new}, "
                      f"now a {ALL_KIND_ENV[kind_of(new)]}")

    def equation_ref(self, fp: FilePlan, x: ClaimInfo, cmd: re.Match[str],
                     token: str) -> None:
        """List an equation reference that a move across contracts breaks."""
        text = f"\\{cmd.group('cmd')}{{{token}}}"
        if x.claim_id in self.cross and token not in x.own_labels:
            owners = [c for c in self.idx.claims.values()
                      if core_of(c.claim_id) == core_of(x.claim_id)
                      and token in c.own_labels and c.claim_id != x.claim_id]
            if owners and core_of(self.new_id(owners[0].claim_id)) != core_of(
                    self.new_id(x.claim_id)):
                self.note(fp, cmd.start(), f"{text} points into {owners[0].claim_id}, "
                          "which the moved claim leaves behind; repair by hand")
        owner = self.cross_eq.get((core_of(x.claim_id), token))
        if owner is not None and owner != x.claim_id and core_of(
                self.new_id(owner)) != core_of(self.new_id(x.claim_id)):
            self.note(fp, cmd.start(), f"{text} points into {owner}, which moves to "
                      f"{module_of(self.m[owner])}; repair by hand")

    def environment(self, fp: FilePlan, x: ClaimInfo, lo: int) -> None:
        """Rename the claim environment of a re-kinded claim."""
        old_env = ALL_KIND_ENV[kind_of(x.claim_id)]
        new_env = ALL_KIND_ENV[kind_of(self.m[x.claim_id])]
        begin = fp.text.find(f"\\begin{{{old_env}}}", lo)
        if begin == -1:
            self.note(fp, lo, f"no \\begin{{{old_env}}} found; rename the environment "
                      "by hand")
            return
        name_at = begin + len("\\begin{")
        self.change(fp, name_at, name_at + len(old_env), new_env)
        end = fp.text.find(f"\\end{{{old_env}}}", begin)
        if end == -1:
            self.note(fp, begin, f"no \\end{{{old_env}}} found; close it by hand")
            return
        name_at = end + len("\\end{")
        self.change(fp, name_at, name_at + len(old_env), new_env)

    # -- module.yaml ---------------------------------------------------------

    def process_module_yaml(self, fp: FilePlan, module_id: str | None) -> None:
        """Rewrite ``order`` and ``reading_groups[].start``; append moved claims."""
        self.scan_paths(fp, 0, len(fp.text))
        if module_id is None:
            return
        structural = self.order_and_starts(fp, module_id)
        wiki = [(m.start("inner"), m.end("inner")) for m in WIKI_RE.finditer(fp.text)]
        for s, e, token in self.tokens(BARE_RE, fp, 0, len(fp.text)):
            if any(a <= s < b for a, b in structural):
                continue
            if any(a <= s and e <= b for a, b in wiki):
                self.contract_token(fp, s, e, token, module_id)
                continue
            cands = self.idx.contract_labels.get((core_of(module_id), token), [])
            named = [c for c in cands if c in self.targets]
            if named:
                self.note(fp, s, f"bare '{token}' in module.yaml prose or a comment "
                          f"names {named[0]}; not rewritten")

    def order_and_starts(self, fp: FilePlan, module_id: str) -> list[tuple[int, int]]:
        """Apply the batch to one module's order and group anchors."""
        lines: list[tuple[int, str]] = []
        offset = 0
        for line in fp.text.split("\n"):
            lines.append((offset, line))
            offset += len(line) + 1
        newline = "\r\n" if "\r\n" in fp.text else "\n"
        item_re = re.compile(r"^(?P<pre>\s*-\s*)(?P<q>[\"']?)(?P<tok>[^\s#\"']+)(?P=q)")
        start_re = re.compile(
            r"^(?P<pre>\s*(?:-\s+)?start\s*:\s*)(?P<q>[\"']?)(?P<tok>[^\s#\"']+)(?P=q)")
        # (line start, token start, token end, token, the "  - " prefix)
        items: list[tuple[int, int, int, str, str]] = []
        in_order = False
        flow_at = -1
        for start, line in lines:
            body = line.rstrip("\r")
            if re.match(r"^order\s*:", body):
                rest = body.split(":", 1)[1].split("#", 1)[0].strip()
                in_order = not rest
                flow_at = start if rest else -1
                continue
            if in_order:
                match = item_re.match(body)
                if match:
                    items.append((start, start + match.start("tok"),
                                  start + match.end("tok"), match.group("tok"),
                                  match.group("pre")))
                elif body.strip() and not body.lstrip().startswith("#"):
                    in_order = False
        structural = [(s, e) for _, s, e, _, _ in items]
        order = [token for *_, token, _ in items]
        moved_out = {lab for lab in order
                     if f"{module_id}/{lab}" in self.m
                     and module_of(self.m[f"{module_id}/{lab}"]) != module_id}
        incoming = [label_of(n) for o, n in self.m.items()
                    if module_of(n) == module_id and module_of(o) != module_id]
        if flow_at >= 0:
            if moved_out or incoming or any(f"{module_id}/{lab}" in self.m
                                            for lab in order):
                self.note(fp, flow_at, "order is a flow list; apply the relabel to it "
                          "by hand")
            return structural
        for line_start, s, e, token, _pre in items:
            old = f"{module_id}/{token}"
            if old in self.report:
                self.note(fp, s, f"order entry '{token}' names {old}")
            elif token in moved_out:
                line_end = fp.text.find("\n", line_start)
                stop = len(fp.text) if line_end == -1 else line_end + 1
                self.change(fp, line_start, stop, "")
            elif old in self.m:
                self.change(fp, s, e, label_of(self.m[old]))
        starts: list[tuple[int, int, str]] = []
        for start, line in lines:
            match = start_re.match(line.rstrip("\r"))
            if match:
                starts.append((start + match.start("tok"), start + match.end("tok"),
                               match.group("tok")))
        structural += [(s, e) for s, e, _ in starts]
        anchors = {token for _, _, token in starts}
        for s, e, token in starts:
            old = f"{module_id}/{token}"
            if old in self.report:
                self.note(fp, s, f"reading-group start '{token}' names {old}")
            elif token in moved_out:
                successor = self.successor(module_id, order, token, anchors, moved_out)
                if successor is None:
                    self.note(fp, s, f"reading group anchored on '{token}' is left "
                              "empty by the move; remove or re-anchor it by hand")
                else:
                    self.change(fp, s, e, successor)
            elif old in self.m:
                self.change(fp, s, e, label_of(self.m[old]))
        if incoming:
            if not items:
                self.note(fp, 0, f"no block order list to append {', '.join(incoming)} "
                          "to; add them by hand")
            else:
                last_start, *_, pre = items[-1]
                line_end = fp.text.find("\n", last_start)
                at = len(fp.text) if line_end == -1 else line_end + 1
                lead = "" if line_end != -1 else newline
                added = lead + "".join(f"{pre}{lab}{newline}" for lab in incoming)
                fp.changes.append(Change(at, at, added, "", fp.line_at(at)))
                self.note(fp, at, f"moved claim(s) {', '.join(incoming)} appended at "
                          "the end of order; place them where they belong")
        return structural

    def successor(self, module_id: str, order: Sequence[str], token: str,
                  anchors: set[str], moved_out: set[str]) -> str | None:
        """Return the next staying member of the group anchored on ``token``."""
        for later in order[order.index(token) + 1:]:
            if later in anchors:
                return None
            if later not in moved_out:
                return label_of(self.new_id(f"{module_id}/{later}"))
        return None

    # -- other files of a contract, and code ----------------------------------

    def contract_token(self, fp: FilePlan, s: int, e: int, token: str,
                       module_id: str | None) -> None:
        """Rewrite a bare label in an authored file of one contract."""
        core = fp.rel.split("/")[2]
        cands = self.idx.contract_labels.get((core, token), [])
        if len(cands) > 1 and module_id is not None:
            nearest = [c for c in cands if module_of(c) == module_id]
            cands = nearest if len(nearest) == 1 else cands
        if len(cands) == 1:
            target = cands[0]
            if target in self.report:
                self.note(fp, s, f"'{token}' names {target}")
            elif target in self.m:
                self.change(fp, s, e, self.new_bare(target, core))
        elif not cands:
            self.report_possible(fp, s, token, f"resolves in no claim of {core}")
        elif self.targets & set(cands):
            self.note(fp, s, f"bare '{token}' is ambiguous in {core} "
                      f"({', '.join(cands)}); not rewritten")

    def process_contract_doc(self, fp: FilePlan) -> None:
        """Rewrite interface.yaml, design.md and other authored contract files."""
        self.scan_paths(fp, 0, len(fp.text))
        directory = fp.rel.rpartition("/")[0]
        module_id = None
        while directory.count("/") >= 2:
            module_id = self.idx.module_dirs.get(directory)
            if module_id is not None:
                break
            directory = directory.rpartition("/")[0]
        for s, e, token in self.tokens(BARE_RE, fp, 0, len(fp.text)):
            self.contract_token(fp, s, e, token, module_id)

    def process_code(self, fp: FilePlan) -> None:
        """Rewrite code, tests, instances and runs: bare labels only in scope."""
        self.scan_paths(fp, 0, len(fp.text))
        scope = self.idx.scope_contracts(fp.rel)
        for s, e, token in self.tokens(BARE_RE, fp, 0, len(fp.text)):
            cands = sorted({c for core in scope
                            for c in self.idx.contract_labels.get((core, token), [])})
            if len(cands) == 1:
                target = cands[0]
                if target in self.report:
                    self.note(fp, s, f"'{token}' names {target}")
                elif target in self.m:
                    new = self.new_id(target)
                    local = core_of(new) in scope
                    self.change(fp, s, e, label_of(new) if local else new)
            elif not cands:
                where = ("outside the code package of its contract" if scope
                         else "outside any contract's code package")
                self.report_possible(fp, s, token, where)
            elif self.targets & set(cands):
                self.note(fp, s, f"bare '{token}' is ambiguous here "
                          f"({', '.join(cands)}); not rewritten")

    # -- whole-graph checks ----------------------------------------------------

    def check_fences(self) -> None:
        """List ``uses`` edges that a move takes outside ``depends_on``."""
        for x in self.idx.claims.values():
            for target in x.uses:
                if x.claim_id not in self.movers and target not in self.movers:
                    continue
                home = module_of(self.new_id(x.claim_id))
                there = module_of(self.new_id(target))
                if home == there:
                    continue
                path = self.idx.rel(x.path)
                allowed = allowed_modules(self.idx.repo, self.idx.repo.modules[home])
                if there.startswith(home + "/"):
                    problem = "a core claim may not use a submodule claim"
                elif there not in allowed:
                    problem = f"'{there}' is not in the depends_on of '{home}'"
                else:
                    continue
                self.notes.add(Note(path, 1, f"after the move "
                                    f"{self.new_id(x.claim_id)} uses "
                                    f"{self.new_id(target)}: {problem}"))

    def kind_notes(self) -> None:
        """List what a kind change leaves to the editor."""
        for old, new in self.m.items():
            before, after = kind_of(old), kind_of(new)
            if before == after:
                continue
            path = self.idx.rel(self.idx.claims[old].path)
            if before == "ass":
                self.notes.add(Note(path, 1, f"{new} is no longer an assumption: "
                               "remove its short_id and repoint the assumes entries "
                               f"naming it (check_claims --dependents {old})"))
            if after == "ass":
                self.notes.add(Note(path, 1, f"{new} is an assumption now: it needs "
                               "a short_id"))
            if after not in KIND_ENV:
                self.notes.add(Note(path, 1, f"check_claims does not know the kind "
                               f"'{after}'"))


# ---------------------------------------------------------------------------
# planning, applying, the map file
# ---------------------------------------------------------------------------

def plan_relabel(root: Path, renames: Mapping[str, str]) -> Plan:
    """Validate a rename batch and return its plan; ``RelabelError`` on refusal."""
    idx = load_index(root)
    validate(idx, renames)
    return Planner(idx, renames).run()


def apply_plan(plan: Plan) -> list[str]:
    """Write a plan (LF preserved: bytes as read); return the paths written."""
    written: list[str] = []
    rendered = {rel: fp.new_text() for rel, fp in plan.files.items()}
    for rel, fp in sorted(plan.files.items()):
        if fp.new_path is None and fp.changes:
            fp.path.write_bytes(rendered[rel].encode("utf-8"))
            written.append(rel)
    moves = plan.moves()
    for fp in moves:
        fp.path.unlink()
    for fp in moves:
        assert fp.new_path is not None
        fp.new_path.parent.mkdir(parents=True, exist_ok=True)
        fp.new_path.write_bytes(rendered[fp.rel].encode("utf-8"))
        written.append(fp.new_path.resolve().relative_to(plan.root.resolve()).as_posix())
    return written


def regenerate_closure(root: Path) -> tuple[bool, str]:
    """Regenerate ``claim_closure.json`` in a fresh process (it imports CLAIM_ROOTS)."""
    if not (root / "harness" / "generate_claim_closure.py").is_file():
        return True, "no harness/generate_claim_closure.py here; nothing regenerated"
    result = subprocess.run(
        [sys.executable, "-m", "harness.generate_claim_closure", "--repo", str(root)],
        cwd=root, capture_output=True, text=True, check=False)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def read_rename_file(path: Path) -> dict[str, str]:
    """Read a YAML or JSON batch: a mapping, or a list of pairs, of full ids."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RelabelError(f"cannot read {path}: {exc}") from exc
    pairs: list[tuple[Any, Any]] = []
    if isinstance(data, dict):
        pairs = list(data.items())
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, list | tuple) and len(item) == 2:
                pairs.append((item[0], item[1]))
            elif isinstance(item, dict) and set(item) in ({"old", "new"},
                                                          {"from", "to"}):
                keys = ("old", "new") if "old" in item else ("from", "to")
                pairs.append((item[keys[0]], item[keys[1]]))
            elif isinstance(item, dict) and len(item) == 1:
                pairs.append(next(iter(item.items())))
            elif isinstance(item, str) and "->" in item:
                old, _, new = item.partition("->")
                pairs.append((old.strip(), new.strip()))
            else:
                raise RelabelError(f"{path}: cannot read the entry {item!r}")
    else:
        raise RelabelError(f"{path}: expected a mapping or a list of old -> new ids")
    out: dict[str, str] = {}
    for old, new in pairs:
        if not isinstance(old, str) or not isinstance(new, str):
            raise RelabelError(f"{path}: ids must be strings ({old!r} -> {new!r})")
        if old in out:
            raise RelabelError(f"{path}: '{old}' is renamed twice")
        out[old] = new
    return out


def merge_map(existing: Mapping[str, Any], renames: Mapping[str, str] | None = None,
              splits: Mapping[str, Sequence[str]] | None = None,
              merges: Mapping[str, Sequence[str]] | None = None) -> dict[str, Any]:
    """Merge new entries into a cumulative map; a rename chain collapses.

    ``a -> b`` then ``b -> c`` gives ``a -> c`` and ``b -> c``; a split's
    pieces and a merge's result follow later renames too.
    """
    for key in existing:
        if key not in MAP_KEYS:
            raise RelabelError(f"map file: unknown key '{key}'")
    out_renames = {str(k): str(v)
                   for k, v in dict(existing.get("renames") or {}).items()}
    out_splits = {str(k): [str(i) for i in v]
                  for k, v in dict(existing.get("splits") or {}).items()}
    out_merges = {str(k): [str(i) for i in v]
                  for k, v in dict(existing.get("merges") or {}).items()}
    deleted = sorted({str(i) for i in existing.get("deleted") or []})
    for old, new in (splits or {}).items():
        out_splits[old] = list(new)
    for new, olds in (merges or {}).items():
        out_merges[new] = list(olds)
    for old, new in (renames or {}).items():
        for key, value in list(out_renames.items()):
            if value == old:
                out_renames[key] = new
        out_renames[old] = new
        for key, pieces in out_splits.items():
            out_splits[key] = [new if piece == old else piece for piece in pieces]
        if old in out_merges:
            out_merges[new] = out_merges.pop(old)
    out_renames = {k: v for k, v in out_renames.items() if k != v}
    return {"deleted": deleted, "merges": dict(sorted(out_merges.items())),
            "renames": dict(sorted(out_renames.items())),
            "splits": dict(sorted(out_splits.items()))}


def update_map_file(path: Path, **entries: Any) -> None:
    """Merge entries into the map file at ``path`` and write it (sorted, LF)."""
    existing: Any = {}
    if path.exists():
        try:
            existing = json.loads(path.read_bytes().decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RelabelError(f"cannot read the map file {path}: {exc}") from exc
        if not isinstance(existing, dict):
            raise RelabelError(f"the map file {path} is not a JSON object")
    merged = merge_map(existing, **entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(merged, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_bytes(text.encode("utf-8"))


# ---------------------------------------------------------------------------
# the command line
# ---------------------------------------------------------------------------

def _shown(text: str) -> str:
    """Return a one-line rendering of an edited span."""
    flat = text.replace("\r", "").strip("\n")
    return flat.replace("\n", " | ") if flat else "(nothing)"


def print_plan(plan: Plan, dry_run: bool) -> None:
    """Print the plan: every edit on a dry run, a summary otherwise; then notes."""
    for old, new in sorted(plan.renames.items()):
        print(f"rename {old} -> {new}")
    edits = plan.edits()
    touched = {fp.rel for fp, _ in edits} | {fp.rel for fp in plan.moves()}
    for fp in plan.moves():
        assert fp.new_path is not None
        target = fp.new_path.resolve().relative_to(plan.root.resolve()).as_posix()
        print(f"move  {fp.rel} -> {target}")
    if dry_run:
        for fp, change in edits:
            print(f"edit  {fp.rel}:{change.line}: {_shown(change.old)} -> "
                  f"{_shown(change.new)}")
    verb = "planned" if dry_run else "applied"
    print(f"{len(edits)} edit(s) {verb} in {len(touched)} file(s), "
          f"{len(plan.moves())} file move(s)")
    print_notes(plan.notes, "left for repair by hand")


def print_notes(notes: Sequence[Note], what: str) -> None:
    """Print manual-repair sites (or reference sites)."""
    print(f"{len(notes)} site(s) {what}" + (":" if notes else ""))
    for note in notes:
        print(f"  {note.render()}")


def split_list(value: str) -> list[str]:
    """Split a comma-separated id list."""
    return [part.strip() for part in value.split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog=COMMAND,
        description="Rename, re-kind or move claims across spec/, src/, tests/, "
                    "instances/ and runs/; record splits and merges.")
    parser.add_argument("old", nargs="?", help="old full claim id")
    parser.add_argument("new", nargs="?", help="new full claim id")
    parser.add_argument("--map", dest="map_file", metavar="RENAMES.YAML",
                        help="a batch: a YAML/JSON mapping (or list of pairs) "
                             "old full id -> new full id, applied together")
    parser.add_argument("--split", metavar="OLD", help="record a split of OLD")
    parser.add_argument("--merge", metavar="OLD1,OLD2", help="record a merge")
    parser.add_argument("--into", metavar="IDS",
                        help="with --split: NEW1,NEW2,...; with --merge: NEW")
    parser.add_argument("--dry-run", action="store_true",
                        help="print every planned edit and write nothing")
    parser.add_argument("--map-out", metavar="PATH",
                        help="cumulative relabel map (JSON) to merge the entries into")
    parser.add_argument("--repo", default=str(REPO_ROOT),
                        help="repository root (default: this checkout)")
    return parser


def run_split_merge(args: argparse.Namespace, root: Path) -> int:
    """Record a split or a merge in the map file and print its reference sites."""
    if not args.into:
        raise RelabelError("--split and --merge need --into")
    if args.split:
        olds, news = [args.split.strip()], split_list(args.into)
        if len(news) < 2:
            raise RelabelError("--split OLD --into NEW1,NEW2: at least two new ids")
        entry: dict[str, Any] = {"splits": {olds[0]: news}}
    else:
        olds, news = split_list(args.merge), split_list(args.into)
        if len(olds) < 2 or len(news) != 1:
            raise RelabelError("--merge OLD1,OLD2 --into NEW: two or more old ids, "
                               "one new id")
        entry = {"merges": {news[0]: olds}}
    for claim_id in [*olds, *news]:
        check_id(claim_id)
    if not args.map_out and not args.dry_run:
        raise RelabelError("a split or merge is recorded in the map file: pass "
                           "--map-out PATH (or --dry-run to list the sites only)")
    idx = load_index(root)
    for claim_id in olds:
        if claim_id not in idx.claims:
            print(f"note: {claim_id} is not a claim of this tree; sites are found "
                  "by its id and label only")
    notes = Planner(idx, {}, report=olds).run().notes
    print_notes(notes, f"reference {' and '.join(olds)}; repair them by hand")
    if args.dry_run:
        print(f"dry run: nothing recorded ({json.dumps(entry, sort_keys=True)})")
        return 0
    update_map_file(Path(args.map_out), **entry)
    print(f"recorded in {args.map_out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run one relabel; return the exit code."""
    args = build_parser().parse_args(argv)
    root = Path(args.repo)
    modes = [bool(args.old or args.new), bool(args.map_file), bool(args.split),
             bool(args.merge)]
    try:
        if sum(modes) != 1:
            raise RelabelError("give OLD NEW, or --map FILE, or --split/--merge "
                               "with --into (exactly one)")
        if not (root / "spec" / "modules").is_dir():
            raise RelabelError(f"--repo {root}: no spec/modules here")
        if args.split or args.merge:
            return run_split_merge(args, root)
        if args.map_file:
            renames = read_rename_file(Path(args.map_file))
        else:
            if not (args.old and args.new):
                raise RelabelError("give both OLD and NEW")
            renames = {args.old: args.new}
        plan = plan_relabel(root, renames)
        print_plan(plan, args.dry_run)
        if args.dry_run:
            print("dry run: nothing written")
            return 0
        apply_plan(plan)
        if args.map_out:
            update_map_file(Path(args.map_out), renames=plan.renames)
            print(f"recorded in {args.map_out}")
        ok, output = regenerate_closure(root)
        if not ok:
            print(f"the relabel is applied, but claim_closure.json was not "
                  f"regenerated:\n{output}\nrepair and run python -m "
                  "harness.generate_claim_closure", file=sys.stderr)
            return 1
        print(f"claim closure: {output.splitlines()[-1] if output else 'regenerated'}")
        print("next: python -m harness.check_claims")
        return 0
    except RelabelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
