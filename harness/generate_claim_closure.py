#!/usr/bin/env python3
"""Motivation: a key rate that cannot name the claim graph it rests on.

PRINCIPLES.md section 2.1 asks that every result carry "a machine-generated
manifest of the assumption IDs, module versions and claim graph it rests on",
and spec/architecture.md 4.4 names "the claim ids of the theorem and its
transitive ``uses`` closure". The claim files live in ``spec/``, which the
installed package does not contain, so a record written from a wheel could not
name them without a table shipped as package data; this generates it.

This writes ``src/certiqs_key/domain/claim_closure.json``: for every root the
table covers (``certiqs_key.domain.claim_closure.ALL_ROOTS``: the claim roots a
key-rate result may name, the three properties a key length rests on, the
device modules' emission results and the completeness results; and, while a
removable submodule is in the tree, its emission results, ``REMOVABLE_ROOTS``
below), the root and
its transitive ``uses`` closure, and every assumption short id those claims
declare with the assumption claim that owns it; beside them, every module's
version from its ``module.yaml``. The graph is ``harness/check_claims.py``'s,
loaded once and walked with its own ``uses_closure`` and
``assumption_closure`` (the helper ``--assumptions`` prints from, shared so the
two walks cannot drift): no second parser, and the table
lists what ``check_claims --assumptions <root>`` prints. ``--check`` exits 1
when the checked-in table differs from what the claim files give, and names
the top-level blocks that differ, which is how a claim edit, a module version
bump or a new root reaches the record: the error it prevents is a manifest
naming a stale closure, or a version that is no longer the accepted one.

Beside the roots it writes every assumption's owner, its ledger
``machine_key`` (read from the owner's interface.yaml, as the assembler reads
it) and its ``verification`` header field (spec/claim-format.md section 3.2):
the run record marks a manifest row never verified by that field, keyed by
machine key, instead of hand lists that could disagree.

THE KEY-RATE REPORT QUOTES ASSUMPTION TEXT AND LINKS CLAIMS; A RUN-TIER COPY
OF THAT TEXT WOULD DRIFT FROM THE HEADERS. So each assumption also carries its plain
title, summary,
``user_statement``, ``category``, ``affects``, ``refines``, header and
effective status, the generated verification sentence, its contract anchor
and every interface's ``assumption_ledger.emission_rule`` for it (display
only), and a ``claims`` block carries the same plain text for every root,
limitation (``LIMITATION_CLAIMS``), cited claim (``CITED_CLAIMS``),
assumption owner and every claim a carried text links to. Every ``[[...]]``
link in a carried text is written as its full target, so a renderer needs no
knowledge of the contract it came from. A consequence worth knowing: an edit
of a carried summary or ``user_statement`` makes the table stale, which
is why ``python -m harness.assemble_contract --all`` also runs this generator.

A claim of any kind but a
definition may carry a ``user_statement``, the plain reading of a result for
a user who is not a proof expert, and the report presents its security
statement through it; so every entry of the ``claims`` block carries its
``user_statement`` beside its summary (``null`` where it has none), its links
resolved like a summary's.

Each assumption also carries its
``presupposes`` list (empty where the header has none): the roles a run must
have for the assumption's text to hold, which a run-tier guard reads to refuse
a run that engages a premise its roles do not satisfy. The guard is the run
tier's; the table only carries the field, so the guard needs no copy of the
headers.

It refuses to write, and says why, when the claim graph has check_claims
errors (a closure computed over a malformed graph would be a wrong manifest
rather than a missing one), when a declared root, limitation or cited claim is
not a claim, when a link in a carried text does not resolve, when two
assumptions share a machine key, or when an interface's emission rule has a
shape it cannot read, or when an assumption's ``verification`` lies outside
the package's vocabulary (``claim_closure.VERIFICATIONS``, which the shipped
accessors enforce at run time).

Usage:
    python -m harness.generate_claim_closure            # write the table
    python -m harness.generate_claim_closure --check    # exit 1 if it is stale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import yaml

from certiqs_key.domain.claim_closure import (
    ALL_ROOTS,
    CITED_CLAIMS,
    LIMITATION_CLAIMS,
    TABLE_NAME,
    VERIFICATIONS,
)
from harness.check_claims import (
    ASSUMPTION_CATEGORIES,
    Repo,
    assumption_closure,
    contract_of,
    effective_status,
    link_target,
    load_repo,
    uses_closure,
)
from harness.contract_navigation import (
    KIND_WORD,
    LINK_RE,
    SHORT_ID_LINK_RE,
    claim_anchor,
    plain_title,
)
from harness.contract_render import VERIFICATION_SENTENCES, ledger_machine_key

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = Path("src") / "certiqs_key" / "domain" / TABLE_NAME
COMMAND = "python -m harness.generate_claim_closure"

#: THE EMISSION RESULTS OF A REMOVABLE SUBMODULE, carried only while the
#: submodule is in the tree. A submodule declared removable must stay so
#: (the public tree may be exported without it), so no shipped tier below it
#: names its claims (each has an isolation test, such as
#: tests/unit/test_receiver_probe_isolation.py) and
#: ``certiqs_key.domain.claim_closure.DEVICE_ROOTS`` leaves them out; the
#: harness may name them, and a tree without the submodule drops them here.
#: A submodule's entry may name a claim of another module that goes with it:
#: ``reductions/wpfss/cor:route-conditioned``, the weight route read through
#: the probe-conditioned receiver, is the one claim outside the receiver that
#: uses probe conditioning, and the export removes it with the submodule.
REMOVABLE_ROOTS: dict[str, tuple[str, ...]] = {
    "receiver/probe-conditioning": (
        "receiver/probe-conditioning/cor:emitted-conditioned",
        "reductions/wpfss/cor:route-conditioned",
    ),
}


def root_closure(repo: Repo, root: str) -> dict[str, Any]:
    """Return a root's claim ids and its assumption short ids with their owners.

    The claims are the root and ``uses_closure(root)``; the assumptions are
    ``assumption_closure(root)``, the one walk ``check_claims --assumptions``
    prints, each short id mapped to the assumption claim that owns it.
    """
    claims = [root, *uses_closure(repo, root)]
    assumptions: dict[str, str] = {}
    for short_id, declarers in assumption_closure(repo, root).items():
        owner = repo.assumptions.get(short_id)
        if owner is None:
            raise ValueError(
                f"{declarers[0]} assumes {short_id!r}, which names no assumption"
            )
        assumptions[short_id] = owner.claim_id
    return {"claims": claims, "assumptions": assumptions}


def _interfaces(repo: Repo) -> dict[str, Any]:
    """Return every module's parsed interface.yaml (``None`` where it has none)."""
    found: dict[str, Any] = {}
    for module_id in sorted(repo.modules):
        path = repo.root / "spec" / "modules" / module_id / "interface.yaml"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        found[module_id] = yaml.safe_load(text) if text else None
    return found


def contract_ref(claim_id: str) -> dict[str, str]:
    """Return where a claim is shown: its core's contract PDF and its anchor.

    A submodule's claims live in its core's contract, so the PDF is the
    core's; the anchor is the stable named destination of the assembler.
    """
    return {
        "pdf": f"spec/modules/{contract_of(claim_id)}/contract.pdf",
        "anchor": claim_anchor(claim_id),
    }


def plain_text(repo: Repo, module_id: str, text: Any, links: set[str]) -> str | None:
    """Return a header text with its whitespace collapsed and its links made full.

    Every ``[[...]]`` is rewritten as ``[[A-...]]`` or ``[[<full claim id>]]``,
    resolved as the contract renderers resolve it (``check_claims.link_target``,
    the field's own module first); the claim it names is added to ``links``.
    ``None`` for an absent field. A link that does not resolve is refused.
    """
    if text is None:
        return None
    collapsed = " ".join(str(text).split())

    def full(match: re.Match[str]) -> str:
        written = match.group(1).strip()
        target = link_target(repo, module_id, written)
        if target is None:
            raise ValueError(
                f"{module_id}: the link [[{written}]] in a carried text resolves "
                "to no claim"
            )
        links.add(target.claim_id)
        if SHORT_ID_LINK_RE.match(written):
            return f"[[{written}]]"
        return f"[[{target.claim_id}]]"

    return LINK_RE.sub(full, collapsed)


def emission_rules(repo: Repo, interfaces: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Return ``{short id: {module: rule}}`` from every ``emission_rule`` mapping.

    Read from ``assumption_ledger.emission_rule`` of each interface, in either
    of the two shapes the tree writes: short id to its rule (meat-core,
    frank-wolfe, statistics), or a condition to the short ids it emits
    (protocol-compiler). A short id that names no assumption is skipped (a
    superseded row an interface still lists); a shape outside these two, a list
    item that is no short id among them, is refused rather than guessed.
    Display text only: nothing parses it.
    """
    rules: dict[str, dict[str, str]] = {}

    def add(short_id: str, module_id: str, rule: str) -> None:
        if short_id not in repo.assumptions:
            return
        text = " ".join(rule.split())
        held = rules.setdefault(short_id, {})
        held[module_id] = f"{held[module_id]}; {text}" if module_id in held else text

    for module_id, document in interfaces.items():
        ledger = (document.get("assumption_ledger")
                  if isinstance(document, dict) else None)
        mapping = ledger.get("emission_rule") if isinstance(ledger, dict) else None
        if mapping is None:
            continue
        if not isinstance(mapping, dict):
            raise ValueError(
                f"{module_id}: assumption_ledger.emission_rule is not a mapping"
            )
        for key, value in mapping.items():
            if SHORT_ID_LINK_RE.match(str(key)) and isinstance(value, str):
                add(str(key), module_id, value)
            elif isinstance(value, list) and all(
                isinstance(v, str) and SHORT_ID_LINK_RE.match(v) for v in value
            ):
                for short_id in value:
                    add(short_id, module_id, str(key))
            else:
                raise ValueError(
                    f"{module_id}: assumption_ledger.emission_rule[{key!r}] is "
                    "neither a short id's rule nor a condition's list of short ids"
                )
    return rules


def _list_or_none(value: Any) -> list[str] | None:
    """Return a header list as strings, ``None`` where the field is absent."""
    if value is None:
        return None
    return [str(item) for item in value] if isinstance(value, list) else [str(value)]


def assumption_table(
    repo: Repo, links: set[str] | None = None
) -> dict[str, dict[str, Any]]:
    """Return every assumption's owner, key, mark, text, anchor and emission rules.

    Claims its texts link to are added to ``links``. Two assumptions sharing
    one machine key are refused: one key must carry one mark.
    """
    links = set() if links is None else links
    interfaces = _interfaces(repo)
    emission = emission_rules(repo, interfaces)
    table: dict[str, dict[str, Any]] = {}
    owners_of_key: dict[str, str] = {}
    for short_id, owner in sorted(repo.assumptions.items()):
        header = owner.header
        key = ledger_machine_key(interfaces.get(owner.module_id), short_id)
        if key is not None:
            if key in owners_of_key:
                raise ValueError(
                    f"the machine key {key!r} names two assumptions, "
                    f"{owners_of_key[key]} and {short_id}"
                )
            owners_of_key[key] = short_id
        verification = str(header.get("verification"))
        if verification not in VERIFICATIONS:
            # The package refuses a table carrying any other value at run
            # time (claim_closure.VERIFICATIONS; `decided` and `discharged`
            # left with record schema 0.20.0), so none is written.
            raise ValueError(
                f"{short_id} has verification {verification!r}; an assumption "
                f"carries one of {sorted(VERIFICATIONS)}"
            )
        refines = header.get("refines")
        table[short_id] = {
            "owner": owner.claim_id,
            "machine_key": key,
            "verification": verification,
            "verification_sentence": VERIFICATION_SENTENCES.get(verification),
            "title": plain_title(str(header.get("title", owner.label))),
            "summary": plain_text(repo, owner.module_id, header.get("summary"), links),
            "user_statement": plain_text(
                repo, owner.module_id, header.get("user_statement"), links
            ),
            "category": None if header.get("category") is None
            else str(header["category"]),
            "presupposes": _list_or_none(header.get("presupposes")) or [],
            "affects": _list_or_none(header.get("affects")),
            "refines": None if refines is None else str(refines),
            "status": owner.status,
            "effective_status": effective_status(repo, owner.claim_id)[0],
            "contract": contract_ref(owner.claim_id),
            "emission": dict(sorted(emission.get(short_id, {}).items())),
        }
    return table


def claim_entry(repo: Repo, claim_id: str, links: set[str]) -> dict[str, Any]:
    """Return one claim's kind, plain title, summary and reading, statuses, anchor.

    The reading is the claim's ``user_statement``, ``None`` where it has none.
    """
    claim = repo.claims[claim_id]
    return {
        "kind": claim.kind,
        "kind_word": KIND_WORD.get(claim.kind, claim.kind),
        "title": plain_title(str(claim.header.get("title", claim.label))),
        "summary": plain_text(repo, claim.module_id, claim.header.get("summary"),
                              links),
        "user_statement": plain_text(
            repo, claim.module_id, claim.header.get("user_statement"), links
        ),
        "status": claim.status,
        "effective_status": effective_status(repo, claim_id)[0],
        "contract": contract_ref(claim_id),
    }


def claim_table(repo: Repo, seeds: Iterable[str], links: set[str]) -> dict[str, Any]:
    """Return the ``claims`` block: the seeds and every claim a carried text links.

    A worklist: a carried summary's link adds its target, whose own summary is
    carried in turn, so every target a renderer meets is in the block.
    """
    table: dict[str, Any] = {}
    pending = sorted(set(seeds) | links)
    while pending:
        claim_id = pending.pop()
        if claim_id in table:
            continue
        found: set[str] = set()
        table[claim_id] = claim_entry(repo, claim_id, found)
        pending.extend(sorted(found - set(table)))
    return dict(sorted(table.items()))


def default_roots(repo: Repo) -> tuple[str, ...]:
    """Return ``ALL_ROOTS`` and the roots of every removable submodule present."""
    present = [root for module_id, roots in REMOVABLE_ROOTS.items()
               if module_id in repo.modules for root in roots]
    return tuple(sorted({*ALL_ROOTS, *present}))


def build_table(
    repo: Repo,
    *,
    roots: Sequence[str] | None = None,
    limitations: Sequence[str] = LIMITATION_CLAIMS,
    cited: Sequence[str] = CITED_CLAIMS,
) -> dict[str, Any]:
    """Return the table for ``repo``: versions, assumptions, claims and roots.

    ``roots`` defaults to :func:`default_roots`, ``limitations`` and ``cited``
    to the declarations of ``certiqs_key.domain.claim_closure``; a fixture
    passes its own. Each must name claims: a declared id that is not one is
    refused, by kind.
    """
    roots = default_roots(repo) if roots is None else roots
    for what, ids in (("claim roots", roots), ("limitation claims", limitations),
                      ("cited claims", cited)):
        missing = [claim_id for claim_id in ids if claim_id not in repo.claims]
        if missing:
            raise ValueError(f"{what} that are not claims: {', '.join(missing)}")
    links: set[str] = set()
    assumptions = assumption_table(repo, links)
    owners = [row["owner"] for row in assumptions.values()]
    return {
        "assumptions": assumptions,
        "category_order": list(ASSUMPTION_CATEGORIES),
        "claims": claim_table(repo, [*roots, *limitations, *cited, *owners], links),
        "generated_by": COMMAND,
        "limitations": list(limitations),
        "module_versions": {
            module_id: str(repo.modules[module_id].meta["version"])
            for module_id in sorted(repo.modules)
        },
        "roots": {root: root_closure(repo, root) for root in sorted(roots)},
    }


def render(table: dict[str, Any]) -> str:
    """Return the table as the deterministic text that is checked in."""
    return json.dumps(table, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def stale_blocks(current: str | None, table: dict[str, Any]) -> list[str]:
    """Return the top-level blocks of ``table`` that ``current`` lacks or differs in."""
    try:
        old = json.loads(current) if current is not None else {}
    except json.JSONDecodeError:
        old = {}
    if not isinstance(old, dict):
        old = {}
    return sorted(key for key in set(old) | set(table)
                  if old.get(key) != table.get(key))


def regenerate(root: Path, repo: Repo, check: bool) -> tuple[bool, list[str]]:
    """Write the table, or check it; return whether all is well and what to say.

    The one routine of ``main`` and of ``assemble_contract --all``. A graph
    with check_claims errors writes nothing.
    """
    if repo.errors:
        lines = [error.render() for error in sorted(repo.errors)]
        lines.append(f"{len(repo.errors)} check_claims error(s); no table written")
        return False, lines
    try:
        table = build_table(repo)
    except ValueError as exc:
        return False, [f"error: {exc}; no table written"]
    text = render(table)
    target = root / OUTPUT
    current = target.read_bytes().decode("utf-8") if target.exists() else None
    if check:
        if current != text:
            blocks = ", ".join(stale_blocks(current, table)) or "formatting only"
            return False, [f"{OUTPUT.as_posix()} is stale; run {COMMAND}",
                           f"differing blocks: {blocks}"]
        return True, [f"ok: {OUTPUT.as_posix()} is current"]
    if current == text:
        return True, [f"{OUTPUT.as_posix()} is up to date"]
    target.write_bytes(text.encode("utf-8"))
    return True, [f"wrote {OUTPUT.as_posix()}"]


def main(argv: list[str] | None = None) -> int:
    """Write the table, or with ``--check`` report whether it is current."""
    parser = argparse.ArgumentParser(prog=COMMAND, description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=str(REPO_ROOT),
                        help="repository root (default: this checkout)")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the checked-in table is stale")
    args = parser.parse_args(argv)
    root = Path(args.repo)
    ok, lines = regenerate(root, load_repo(root), args.check)
    for line in lines:
        print(line, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
