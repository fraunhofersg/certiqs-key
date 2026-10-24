#!/usr/bin/env python3
"""Motivation: a human entry point that nobody maintains by hand.

PRINCIPLES.md section 3 gives the human two to five hours a week and one
entry point, `state/DASHBOARD.md`: decisions waiting on the maintainer, ranked; the
module and claim status map; open findings by severity. A page
maintained by hand drifts, so the human reads a status that is no longer
true and agents stop trusting the page. This tool generates the page from the two
sources that are already
kept current for other reasons: the open-item files in `state/open-items/`
(one per item, the single queue) and the claim files as `check_claims`
reads them. Nothing on the page is typed twice, and `--check` fails when the
checked-in page is stale, so a commit that changes an item without
regenerating the page is caught.

Usage:
    python -m harness.dashboard [--repo .] [--check]

The page is deterministic: no timestamps, no ages, so `--check` does not
rot overnight (the same rule as the assembled contracts).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from harness.check_claims import (
    STATUSES,
    Repo,
    effective_counts,
    effective_status_map,
    load_repo,
    status_counts,
)

SEVERITY_RANK = {"blocking": 0, "major": 1, "minor": 2, "info": 3}
OPEN = ("open", "in-progress")


@dataclass
class Item:
    """One open item, as read from its YAML file."""

    path: str
    data: dict[str, Any]

    def get(self, key: str, default: str = "") -> str:
        """Return a field as a string, or ``default`` when absent."""
        value = self.data.get(key)
        return default if value is None else str(value)

    @property
    def is_open(self) -> bool:
        """Whether the item still waits on someone."""
        return self.get("status") in OPEN

    @property
    def rank(self) -> tuple[int, int, str]:
        """Sort key: severity, then priority, then id."""
        severity = SEVERITY_RANK.get(self.get("severity"), 9)
        try:
            priority = int(self.get("priority", "9"))
        except ValueError:
            priority = 9
        return severity, priority, self.get("id")


def load_items(root: Path) -> list[Item]:
    """Read every ``state/open-items/*.yaml``; a malformed one is an error."""
    items: list[Item] = []
    for path in sorted((root / "state" / "open-items").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "id" not in data:
            raise ValueError(f"{path.as_posix()}: not an open item (no id)")
        items.append(Item(path.relative_to(root).as_posix(), data))
    return items


def load_registry(root: Path) -> list[str]:
    """Return the core module ids in the order ``spec/modules.yaml`` lists them."""
    path = root / "spec" / "modules.yaml"
    if not path.is_file():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cores = data.get("cores", []) if isinstance(data, dict) else []
    return [str(core["id"]) for core in cores
            if isinstance(core, dict) and "id" in core]


def one_line(text: str) -> str:
    """Collapse a multi-line brief into a single table-safe line."""
    return " ".join(text.split()).replace("|", "\\|")


def render_decisions(items: list[Item]) -> list[str]:
    """Section 1: decisions waiting on the human, ranked, with their briefs."""
    waiting = sorted((i for i in items if i.is_open and i.data.get("needs_human")),
                     key=lambda i: i.rank)
    lines = ["## 1. Decisions waiting on the maintainer", ""]
    if not waiting:
        lines += ["No open item in this tree waits on a human decision.", ""]
        return lines
    lines += ["| # | Item | Severity | In one line |", "| --- | --- | --- | --- |"]
    for number, item in enumerate(waiting, start=1):
        lines.append(f"| {number} | `{item.get('id')}` | {item.get('severity')} | "
                     f"{one_line(item.get('title'))} |")
    lines.append("")
    for number, item in enumerate(waiting, start=1):
        lines += [f"**{number}. `{item.get('id')}`** ({item.path})", "",
                  one_line(item.get("brief")), ""]
        links = item.data.get("links") or []
        if links:
            lines += ["Links: " + ", ".join(f"`{link}`" for link in links), ""]
    return lines


def module_note(module_id: str, items: list[Item]) -> str:
    """Return the note column: the open items that name the module."""
    naming = [i for i in items if i.is_open and i.get("module") == module_id]
    if not naming:
        return ""
    return ", ".join(f"`{i.get('id')}`" for i in sorted(naming, key=lambda i: i.rank))


def contract_link(root: Path, module_id: str) -> str:
    """Return the link to a core's review PDF from ``state/``, or empty.

    A submodule's claims are inside its core's contract, so only cores link;
    the PDF is the assembler's review copy (generated after every
    revision and placed where a reviewer finds it).
    """
    if "/" in module_id:
        return ""
    pdf = root / "spec" / "modules" / module_id / "contract.pdf"
    if not pdf.is_file():
        return "missing"
    links = [f"[pdf](../{pdf.relative_to(root).as_posix()})"]
    graphs = pdf.parent / "graphs" / "README.md"
    if graphs.is_file():
        links.append(f"[graphs](../{graphs.relative_to(root).as_posix()})")
    design = pdf.parent / "design.md"
    if design.is_file():
        links.append(f"[design](../{design.relative_to(root).as_posix()})")
    return " · ".join(links)


def render_status(root: Path, repo: Repo, registry: list[str],
                  items: list[Item]) -> list[str]:
    """Section 2: the module and claim status map.

    Each status cell is the header count with the effective count in
    parentheses: the header status is a claim's local judgement, the effective
    status the minimum over its uses/assumes closure. A
    module's batch is accepted when its effective counts say so, which is what
    a reader of this map wants to see beside the headers.
    """
    effective = effective_status_map(repo)
    lines = ["## 2. Status map", "",
             "| Module | Version | Contract | " + " | ".join(STATUSES)
             + " | pending | Note |",
             "| --- | --- | --- | " + " | ".join("---" for _ in STATUSES)
             + " | --- | --- |"]
    present = sorted(repo.modules)
    ordered = [m for m in registry if m in present] + [
        m for m in present if "/" not in m and m not in registry]
    rows: list[str] = []
    for core in ordered:
        for module_id in [core, *[m for m in present if m.startswith(f"{core}/")]]:
            module = repo.modules[module_id]
            counts, pending = status_counts(repo, module_id)
            eff = effective_counts(repo, module_id, effective)
            rows.append(f"| {module_id} | {module.meta.get('version', '')} | "
                        f"{contract_link(root, module_id)} | "
                        + " | ".join(f"{counts[s]} ({eff[s]})" for s in STATUSES)
                        + f" | {pending} | {module_note(module_id, items)} |")
    for module_id in registry:
        if module_id not in present:
            note = " ".join(
                filter(None, ["not started", module_note(module_id, items)]))
            rows.append(f"| {module_id} | - | - | " + " | ".join("-" for _ in STATUSES)
                        + f" | - | {note} |")
    lines += rows
    lines += ["", "[Core module map](../spec/module-graph.svg) · "
              "[Inputs-to-key-rate flow]"
              "(../spec/architecture.md#6-protocol-compilation-and-meat-flow) · "
              "[How to read contracts and view graphs]"
              "(../harness/contract-reading.md). "
              "The contract column links the PDF, generated graph index and authored "
              "design flowchart. Rebuild together with "
              "`python -m harness.assemble_contract <id>`. "
              "Counts are `python -m harness.check_claims --status`: each cell is "
              "the header count (the local judgement of each claim) with the "
              "effective count in parentheses (the minimum over each claim's "
              "uses/assumes closure; "
              "`python -m harness.check_claims --effective <claim-id>` names the "
              "claims that bind one).", ""]
    return lines


def render_findings(items: list[Item]) -> list[str]:
    """Section 3: open findings and defects by severity."""
    found = sorted((i for i in items if i.is_open
                    and i.get("kind") in {"finding", "defect"}), key=lambda i: i.rank)
    lines = ["## 3. Open findings and defects by severity", ""]
    if not found:
        lines += ["No open finding is recorded in this tree.", ""]
        return lines
    lines += ["| Severity | Item | Owner | Opened | In one line |",
              "| --- | --- | --- | --- | --- |"]
    for item in found:
        lines.append(f"| {item.get('severity')} | `{item.get('id')}` | "
                     f"{item.get('owner')} | {item.get('opened')} | "
                     f"{one_line(item.get('title'))} |")
    lines.append("")
    return lines


def render_tasks(items: list[Item]) -> list[str]:
    """Section 4: open tasks in priority order."""
    tasks = sorted((i for i in items if i.is_open and i.get("kind") == "task"
                    and not i.data.get("needs_human")), key=lambda i: i.rank)
    lines = ["## 4. Tasks in order", ""]
    if not tasks:
        lines += ["No open task is recorded in this tree.", ""]
    for number, item in enumerate(tasks, start=1):
        status = " (in progress)" if item.get("status") == "in-progress" else ""
        lines.append(f"{number}. `{item.get('id')}`{status}: "
                     f"{one_line(item.get('title'))}")
    if tasks:
        lines.append("")
    lines += ["An effort's plan and status with its context is its umbrella "
              "item in `state/open-items/`; history is git.", ""]
    return lines


def render(root: Path) -> str:
    """Render the whole dashboard."""
    repo = load_repo(root)
    items = load_items(root)
    registry = load_registry(root)
    lines = ["# Dashboard", "",
             "GENERATED by `python -m harness.dashboard` from `state/open-items/` "
             "and the claim files; do not edit. Regenerate after changing an open "
             "item or a claim's status; `--check` fails when this page is stale. "
             "Past decisions: `git log --grep \"^Decided-by:\"`.", ""]
    if repo.errors:
        lines += [f"**check_claims reports {len(repo.errors)} error(s)**; run it "
                  "before trusting the status map.", ""]
    lines += render_decisions(items)
    lines += render_status(root, repo, registry, items)
    lines += render_findings(items)
    lines += render_tasks(items)
    return "\n".join(lines).rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write or check ``state/DASHBOARD.md``."""
    parser = argparse.ArgumentParser(
        prog="python -m harness.dashboard",
        description="Generate state/DASHBOARD.md from open items and claim files.")
    parser.add_argument("--repo", default=".", help="repository root (default: .)")
    parser.add_argument("--check", action="store_true",
                        help="write nothing; exit 1 if DASHBOARD.md is stale")
    args = parser.parse_args(argv)
    root = Path(args.repo)
    target = root / "state" / "DASHBOARD.md"
    try:
        rendered = render(root)
    except (ValueError, yaml.YAMLError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != rendered:
            print(f"stale: {target.as_posix()} differs from what would be generated",
                  file=sys.stderr)
            return 1
        print(f"up to date: {target.as_posix()}")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"wrote {target.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
