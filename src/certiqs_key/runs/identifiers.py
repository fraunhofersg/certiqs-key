"""Presentation labels in, stable IDs out -- once, and injectively.

spec/architecture.md 4.3: "The outcome alphabet uses stable IDs. Labels such as
``H``, ``V``, ``+``, and ``-`` are presentation metadata." The operator-bundle
format takes that literally, because every identifier it carries is also an HDF5
link name: :data:`certiqs_key.domain.identifiers.IDENTIFIER_PATTERN` admits
``[A-Za-z0-9_][A-Za-z0-9_.+-]*`` and nothing else.

The BB84 instance spells its alphabets with the choice first -- ``(Z,0)``,
``(X,1)``, ``(X,0)`` as an announcement -- and parentheses and commas are
outside that character set. So a BB84 declaration cannot travel on the wire
under its own labels, and something has to choose the IDs.

THAT CHOICE IS SOUND, AND THE COMPILER SAYS SO IN ITS OWN WORDS
===============================================================
``instances.bb84.specification``, on the joint alphabet: "A bijection over the
same disjoint union; **labels are metadata and the index is binding** (Section
2.2)." Every table the wire format carries -- the POVMs, the announcements, the
acceptance statistic, the key map, the party partition -- is re-keyed by the same
bijection at the same time, and the DECLARED ORDER of every alphabet is
preserved, so the declaration on the far side is the declaration that was
compiled with different names on its indices.

WHAT WOULD MAKE IT UNSOUND, AND THEREFORE WHAT IS REFUSED
=========================================================
Two labels mapping to one ID. That is not a renaming but a MERGE: two outcomes
would become one column, two POVM elements would claim one dataset, and a table
total on the original alphabet would silently lose a row. :func:`stable_id_map`
decides injectivity exactly and raises rather than disambiguating -- an invented
suffix would be this module choosing which of two outcomes keeps its name.

The sanitization itself is deliberately dull: every character outside the
admitted set becomes ``_``, and a leading character outside ``[A-Za-z0-9_]``
gets one prepended. ``(Z,0)`` becomes ``_Z_0_``, which is legible enough to read
in a manifest and mechanical enough that no reader has to guess at it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from certiqs_key.domain.identifiers import is_identifier
from certiqs_key.runs.errors import SliceAssemblyError

__all__ = ["sanitize", "stable_id_map"]

_ADMITTED = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.+-"
)
_LEADING = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def sanitize(label: str) -> str:
    """Return ``label`` as a stable ID, by the rule in the module docstring."""
    body = "".join(character if character in _ADMITTED else "_" for character in label)
    if not body or body[0] not in _LEADING:
        body = "_" + body
    return body


def stable_id_map(labels: Sequence[str], where: str) -> Mapping[str, str]:
    """Return the label-to-ID bijection for one alphabet, or refuse.

    Raises:
        SliceAssemblyError: if two labels sanitize to one ID, or if a
            sanitized ID is somehow still not an identifier -- either would make
            the re-keyed tables describe a different declaration from the
            compiled one.
    """
    mapping: dict[str, str] = {}
    taken: dict[str, str] = {}
    for label in labels:
        identifier = sanitize(label)
        if not is_identifier(identifier):  # pragma: no cover - sanitize guarantees it
            raise SliceAssemblyError(
                f"{where}: {label!r} does not sanitize to a stable identifier "
                f"({identifier!r})"
            )
        clash = taken.get(identifier)
        if clash is not None:
            raise SliceAssemblyError(
                f"{where}: the labels {clash!r} and {label!r} both sanitize to "
                f"{identifier!r}. Two labels mapping to one ID is a MERGE and "
                "not a renaming; nothing here invents a suffix to tell them "
                "apart, because that would be this module choosing which "
                "outcome keeps its name"
            )
        taken[identifier] = label
        mapping[label] = identifier
    return mapping
