"""The key-rate report's glossary, read from ``glossary.yaml`` (package data).

WHY THIS EXISTS. Terms a reader cannot look up stop a reader; the definitions live once,
as data beside this module, and the renderer prints those that occur on its page. The
same file carries the intros of the assumption groups.
This module only loads and indexes the file; ``glossary.yaml``'s header says
what a text may claim.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from functools import cache
from importlib import resources
from typing import Any, Final

import yaml

__all__ = [
    "GLOSSARY_NAME",
    "Category",
    "Term",
    "categories",
    "see_claims",
    "term_anchor",
    "terms",
]

#: The package-data file beside this module.
GLOSSARY_NAME: Final[str] = "glossary.yaml"

#: A ``see`` that is a claim id rather than a document anchor.
_CLAIM_ID: Final = re.compile(r"^[a-z0-9-]+(/[a-z0-9-]+)*/[a-z]+:[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class Term:
    """One glossary entry: its name, the labels that name it, its text, a pointer."""

    term: str
    aliases: tuple[str, ...]
    text: str
    see: str | None
    #: A term of optical receivers only (``optical: true``): left out of the
    #: glossary of a run whose stations are all declared finite POVMs, where
    #: it occurs only in a claim's title or a not-applicable check.
    optical: bool = False

    @property
    def anchor(self) -> str:
        """Return the entry's anchor in the page."""
        return term_anchor(self.term)

    @property
    def see_claim(self) -> str | None:
        """Return ``see`` where it is a claim id."""
        return self.see if self.see and _CLAIM_ID.match(self.see) else None


@dataclass(frozen=True)
class Category:
    """An assumption category's readable heading and its evidence intro.

    ``where_listed`` pairs a short id with the intro that replaces ``intro``
    on the page of a record whose premises list that id (``glossary.yaml``'s
    header says why): an older record that lists A-EVE-DIM keeps the intro it
    was written with.
    """

    heading: str
    intro: str
    where_listed: tuple[tuple[str, str], ...] = ()

    def intro_for(self, listed: Collection[str]) -> str:
        """Return the intro for a page whose premises are ``listed``."""
        for short_id, intro in self.where_listed:
            if short_id in listed:
                return intro
        return self.intro


#: Greek and other symbols of a term, spelled out so that anchors stay ASCII
#: and distinct ("ε* (completeness)" is not "completeness").
_SPELLED: Final[Mapping[str, str]] = {
    "ε": "eps", "\u03b1": "alpha", "λ": "lambda",
    "\u2113": "ell", "τ": "tau", "*": "-star",
}


def term_anchor(term: str) -> str:
    """Return ``g-`` and the term reduced to ASCII letters, digits and dashes."""
    spelled = "".join(_SPELLED.get(char, char) for char in term.lower())
    slug = re.sub(r"[^a-z0-9]+", "-", spelled).strip("-")
    return "g-" + (slug or "term")


@cache
def _data() -> Mapping[str, Any]:
    text = (
        resources.files("certiqs_key.runs.report")
        .joinpath(GLOSSARY_NAME)
        .read_text(encoding="utf-8")
    )
    data = yaml.safe_load(text)
    if not isinstance(data, Mapping):
        raise ValueError(f"{GLOSSARY_NAME} holds no mapping")
    return data


@cache
def terms() -> tuple[Term, ...]:
    """Return every glossary entry, in file order."""
    return tuple(
        Term(
            term=str(item["term"]),
            aliases=tuple(str(alias) for alias in item.get("aliases") or ()),
            text=" ".join(str(item["text"]).split()),
            see=None if item.get("see") is None else str(item["see"]),
            optical=bool(item.get("optical", False)),
        )
        for item in _data().get("terms") or ()
    )


@cache
def categories() -> Mapping[str, Category]:
    """Return the heading and intro of every assumption category."""
    return {
        str(name): Category(
            str(item["heading"]),
            " ".join(str(item["intro"]).split()),
            tuple(
                (str(short_id), " ".join(str(intro).split()))
                for short_id, intro in (item.get("intro_where_listed") or {}).items()
            ),
        )
        for name, item in (_data().get("categories") or {}).items()
    }


def see_claims() -> list[str]:
    """Return every claim id a glossary entry points at, once."""
    return list(dict.fromkeys(
        term.see_claim for term in terms() if term.see_claim is not None
    ))
