"""Stable identifiers used throughout the operator-bundle format.

Outcome, announcement, acceptance-value and sector identifiers are *stable
IDs*. Presentation labels such as ``H``, ``V``, ``+`` and ``-`` are metadata of
a parallel presentation document keyed by these IDs (spec/architecture.md 4.3:
"labels such as ``H``, ``V``, ``+``, ``-`` are presentation metadata"); they
are never identifiers, and this format does not carry them.

The character set is restricted for a mechanical reason, not an aesthetic one:
every identifier is also an HDF5 link name inside ``arrays.h5``. The empty
string, ``/``, ``.``, ``..`` and leading whitespace are not addressable there,
so a bundle that used them could be written and never read back.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence

from certiqs_key.domain._base import BundleValidationError

#: A stable identifier: an HDF5-safe, non-empty, path-component-free name.
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.+-]*$")

#: An absolute dataset path inside ``arrays.h5``, e.g. ``/declaration/tau_A``.
DATASET_PATH_PATTERN = re.compile(r"^(?:/[A-Za-z0-9_][A-Za-z0-9_.+-]*)+$")


def is_identifier(value: str) -> bool:
    """Report whether ``value`` is a well-formed stable identifier."""
    return bool(IDENTIFIER_PATTERN.fullmatch(value))


def is_dataset_path(value: str) -> bool:
    """Report whether ``value`` is a well-formed absolute dataset path."""
    return bool(DATASET_PATH_PATTERN.fullmatch(value))


def check_identifier(value: str, where: str) -> None:
    """Raise unless ``value`` is a well-formed stable identifier."""
    if not is_identifier(value):
        raise BundleValidationError(
            f"{where}: {value!r} is not a stable identifier; identifiers must "
            f"match {IDENTIFIER_PATTERN.pattern} (they are HDF5 link names)"
        )


def check_alphabet(values: Sequence[str], where: str) -> None:
    """Raise unless ``values`` is a non-empty, duplicate-free ID sequence."""
    if not values:
        raise BundleValidationError(f"{where}: alphabet is empty")
    for value in values:
        check_identifier(value, where)
    counts = Counter(values)
    duplicates = sorted(value for value, count in counts.items() if count > 1)
    if duplicates:
        raise BundleValidationError(
            f"{where}: duplicate identifiers {duplicates}; an alphabet is a set "
            "listed in canonical order, so every entry must be distinct"
        )


def check_total_over(
    table: dict[str, object], alphabet: Sequence[str], where: str
) -> None:
    """Raise unless ``table`` is keyed by exactly ``alphabet``."""
    expected = set(alphabet)
    actual = set(table)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise BundleValidationError(
            f"{where}: not total over its declared alphabet; missing keys {missing}"
        )
    if extra:
        raise BundleValidationError(
            f"{where}: keys {extra} are not in the declared alphabet"
        )
