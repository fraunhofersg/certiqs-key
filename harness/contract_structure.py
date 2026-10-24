"""Motivation: one numbering for a contract's PDF, its graphs and its indexes.

A reader meets a claim's number in four places: its heading in the contract
PDF ("Proposition 7.3"), the PDF's contents and bookmarks, the claim index, and
the group graphs with their index `graphs/README.md`. If the PDF and the graphs
numbered differently, "7.3" in one view would name nothing in the other.
Claims are numbered per section on one shared
counter, with sections numbered continuously across parts; this module is the
one place that turns `module.yaml` into that structure, and the assembler
(`harness/assemble_contract.py`) and the graph renderer
(`harness/claim_graph.py`) both read it, so the two views cannot disagree.

The rules (`spec/style.md` sections 4 and 5, `spec/claim-format.md` section 5):

- Part I "Mathematics": the core's reading groups in `order`, each a numbered
  section, without its requirement claims.
- Part II "Engine requirements": the core's requirement claims, in `order`, in
  sections named after the reading group each sits in; no Part II when the
  core has none.
- Each submodule is one further part, titled with its title and introduced by
  its abstract: its mathematics sections, then its requirement sections.
- Sections are numbered continuously across parts; within a section every
  claim, whatever its kind, takes the next number of one counter, so the
  number LaTeX prints is ``<section>.<position>``. That holds because every
  claim file carries exactly one numbered claim environment (check 2 of
  `check_claims`) and nothing else in the document steps the counter: the
  front matter's sections are unnumbered and its restated statements use
  unnumbered environments.

A reading group whose claims are all mathematics or all requirements gives one
section; a group holding both gives two with the same title, and its abstract
introduces the mathematics one. Claims stand where `order` puts them.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from harness.check_claims import Repo, reading_groups
from harness.contract_navigation import group_anchor

MATHEMATICS = "mathematics"
REQUIREMENTS = "requirements"
#: Part titles of the core; a submodule's part carries the submodule's title.
CORE_PART_TITLES = {MATHEMATICS: "Mathematics", REQUIREMENTS: "Engine requirements"}
#: The introduction of Part II (plain text, like every other introduction).
REQUIREMENTS_INTRO = ("What an implementation of this module must do, record or "
                      "refuse; each requirement names the result that motivates it.")


@dataclass(frozen=True)
class Section:
    """One numbered section: a reading group, or its requirement half."""

    number: int                 # continuous across parts
    title: str                  # the reading group's title (plain text)
    module_id: str              # the core or submodule whose group it is
    kind: str                   # MATHEMATICS or REQUIREMENTS
    abstract: str               # its introduction (plain text), "" when none
    claims: tuple[str, ...]     # full claim ids, in order

    @property
    def anchor(self) -> str:
        """Return the section's stable PDF label, from its first claim."""
        return group_anchor(self.claims[0])

    def claim_number(self, claim_id: str) -> str:
        """Return the number LaTeX prints for a claim of the section ("7.3")."""
        return f"{self.number}.{self.claims.index(claim_id) + 1}"


@dataclass(frozen=True)
class Part:
    """One part: the core's mathematics, its requirements, or a submodule."""

    number: int                 # 1-based; LaTeX prints it as a Roman numeral
    title: str
    module_id: str
    intro: str                  # plain text, "" when none
    sections: tuple[Section, ...]


@dataclass(frozen=True)
class ContractSections:
    """A contract's parts and sections, in document order."""

    core: str
    parts: tuple[Part, ...]

    def sections(self) -> list[Section]:
        """Every section, in document order."""
        return [section for part in self.parts for section in part.sections]

    def claims(self) -> list[str]:
        """Every claim id, in document order."""
        return [cid for section in self.sections() for cid in section.claims]

    def section_of(self) -> dict[str, Section]:
        """Map each claim id to its section."""
        return {cid: section for section in self.sections() for cid in section.claims}

    def numbers(self) -> dict[str, str]:
        """Map each claim id to the number LaTeX prints for it."""
        return {cid: section.claim_number(cid) for section in self.sections()
                for cid in section.claims}


def _kind_of(label: str) -> str:
    return label.split(":", 1)[0]


def _module_order(repo: Repo, core: str) -> list[str]:
    """Return the core, then its submodules in declared (else alphabetical) order."""
    declared = repo.modules[core].submodules
    subs = declared or sorted(mid.split("/", 1)[1] for mid in repo.modules
                              if mid.startswith(core + "/"))
    return [core, *(f"{core}/{sub}" for sub in subs if f"{core}/{sub}" in repo.modules)]


def _halves(repo: Repo, module_id: str) -> tuple[
        list[tuple[str, str, list[str]]], list[tuple[str, str, list[str]]]]:
    """Split a module's reading groups into mathematics and requirement halves.

    Each half is a list of (title, abstract, claim ids). The abstract goes to
    the half that holds the group's mathematics, or to its requirement half
    when the group has no mathematics. Raises ``ValueError`` on malformed
    reading groups.
    """
    meta = repo.modules[module_id].meta
    maths: list[tuple[str, str, list[str]]] = []
    reqs: list[tuple[str, str, list[str]]] = []
    starts = {str(group.get("start")): str(group.get("abstract", "") or "")
              for group in meta.get("reading_groups") or [] if isinstance(group, dict)}
    for title, labels in reading_groups(meta):
        abstract = starts.get(labels[0], "") if labels else ""
        ids = [f"{module_id}/{label}" for label in labels]
        mathematics = [cid for cid, label in zip(ids, labels, strict=True)
                       if _kind_of(label) != "req"]
        requirements = [cid for cid, label in zip(ids, labels, strict=True)
                        if _kind_of(label) == "req"]
        if mathematics:
            maths.append((str(title), abstract, mathematics))
        if requirements:
            reqs.append((str(title), "" if mathematics else abstract, requirements))
    return maths, reqs


def contract_sections(repo: Repo, core: str) -> ContractSections:
    """Return the parts, sections and claim order of ``core``'s contract.

    ``repo`` is a loaded repository (``check_claims.load_repo``); its findings
    do not stop the structure from being read. Raises ``KeyError`` when
    ``core`` is not a module and ``ValueError`` when a ``module.yaml`` has
    malformed reading groups.
    """
    parts: list[Part] = []
    numbers = itertools.count(1)

    def add_part(title: str, module_id: str, intro: str,
                 groups: list[tuple[str, str, list[str], str]]) -> None:
        if not groups:
            return
        sections = [Section(next(numbers), group_title, module_id, kind, abstract,
                            tuple(ids))
                    for group_title, abstract, ids, kind in groups]
        parts.append(Part(len(parts) + 1, title, module_id, intro, tuple(sections)))

    for module_id in _module_order(repo, core):
        maths, reqs = _halves(repo, module_id)
        tagged_maths = [(t, a, ids, MATHEMATICS) for t, a, ids in maths]
        tagged_reqs = [(t, a, ids, REQUIREMENTS) for t, a, ids in reqs]
        if module_id == core:
            add_part(CORE_PART_TITLES[MATHEMATICS], core, "", tagged_maths)
            add_part(CORE_PART_TITLES[REQUIREMENTS], core, REQUIREMENTS_INTRO,
                     tagged_reqs)
        else:
            meta = repo.modules[module_id].meta
            add_part(str(meta.get("title", module_id)), module_id,
                     str(meta.get("abstract", "") or ""), tagged_maths + tagged_reqs)
    return ContractSections(core, tuple(parts))
