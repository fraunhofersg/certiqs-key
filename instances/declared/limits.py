"""How large a protocol document may make the work it asks for.

WHY BOUNDS BEYOND THE READER'S. The reader bounds the TEXT of a document (its
length, depth and node count; :mod:`.reader`), but a few hundred bytes can ask
for far more work than they hold: a product alphabet of five dimensions of
twenty values is 3.2 million labels, a rule table over three such alphabets
is their product, and ``identity: 100000`` is one node naming a matrix of
10^10 entries. A document reaches the engine from an MCP client, whose tool
call must return in seconds (``runs/mcp/server.py``), so such a document is
refused before the work starts -- by the product of the sizes, never by
building it -- with the code ``document_too_large``.

THE BOUNDS sit well above what the four packaged instances use, measured
from their compiled declarations: the largest table is
bbm92's key table, about a thousand rows (decoy's acceptance statistic has
104 entries, its readout alphabets 84 labels); the largest Hilbert-space
dimension is decoy's photon-number space, 31. They are limits of the DOCUMENT
LAYER, never of the engine: a protocol past them can still be built in Python
as an instance.

SIZE BOUNDS AND WORK BOUNDS. Every bound here is a SIZE bound, held for every
document, except the optical WORK bounds below (the photon numbers, the
ports, the input block and the receiver's work), which hold for a CUSTOM
document only. A packaged template (``instances/<id>/protocol.yaml``) is
written in this repository; its parameter table's domains are its bounds, so
that a template loses no range (optical_bb84's table admits a cutoff of 16).
``work_bounds`` in :mod:`.optical` (from ``DocumentSurface.packaged``) applies
them. A
packaged template is not refused at the far end of its domain; its
preparation is estimated with :func:`receiver_work`'s measure and, past a
budget, runs in the background with the expected time stated
(``runs/facade/estimate.py``).
"""

from __future__ import annotations

import math
from collections.abc import Iterator, Mapping
from typing import Any, Final

from instances.declared.errors import DocumentError, DocumentReason, pointer

__all__ = [
    "DIMENSION_KEYS",
    "MAX_ALPHABET_LABELS",
    "MAX_DIMENSION",
    "MAX_INPUT_BLOCK",
    "MAX_INTENSITY",
    "MAX_MODES",
    "MAX_PHOTON_CUTOFF",
    "MAX_PHOTON_NUMBER",
    "MAX_PORTS",
    "MAX_RECEIVER_WORK",
    "MAX_SOURCE_CUTOFF",
    "MAX_SOURCE_LABELS",
    "MAX_TABLE_ROWS",
    "MAX_TABLE_WORK",
    "MAX_TOLERANCES",
    "OPERATOR_BLOCKS",
    "check_dimensions",
    "check_size",
    "photon_blocks",
    "receiver_work",
]

#: The most labels one alphabet may have, after its product or union.
MAX_ALPHABET_LABELS: Final[int] = 4096
#: The most keys one rule table may expand over (the product of its variables).
MAX_TABLE_ROWS: Final[int] = 16_384
#: The most rule tests one table may cost: its keys times its rules.
MAX_TABLE_WORK: Final[int] = 1_000_000
#: The largest Hilbert-space dimension a document may declare.
MAX_DIMENSION: Final[int] = 64

#: THE OPTICAL BOUNDS. A
#: station's work is not its size: the receiver's inclusion-exclusion runs over
#: the ``3^K`` pairs of nested click patterns, each at every photon-number
#: block up to the deepest declared window, and the exact arithmetic of the
#: reductions and the honest models grows steeply with the photon cutoff.
#: Measured on the optical_bb84 document (one preparation):
#:
#: - cutoff N with window N + 1 at K = 4 ports: N = 6 0.9 s, 7 2.1 s, 8 9.7 s,
#:   9 63 s, 10 638 s;
#: - window 9 at cutoff 1: 0.9 s;
#: - port-Gram documents at N = 1, window 2: K = 4 0.1 s, 8 1.1 s, 10 10.9 s.
#:
#: So three bounds hold together, each checked before any work starts and
#: refused ``document_too_large``. They admit every default and preset of the
#: four packaged instances (cutoff 1, window 2, four ports), and less than
#: their parameter tables do: optical_bb84's table admits a cutoff of 16 and
#: decoy_bb84's windows up to 30, which a CUSTOM document is refused above the
#: bounds below; a packaged template is not held to them (above). A protocol
#: past them can still be built in Python as an instance.
#:
#: The largest photon cutoff ``N`` of a station.
MAX_PHOTON_CUTOFF: Final[int] = 7
#: The largest photon number any window may name (a cheap first check; the
#: work bound below decides).
MAX_PHOTON_NUMBER: Final[int] = 30
#: The receiver's work, ``3^K * sum_{n <= m} dim(n)^2`` with ``K`` detector
#: ports, ``m`` the deepest photon number (cutoff or window) and ``dim(n) =
#: C(n + k - 1, k - 1)`` the photon-number block on ``k`` input modes. 40,000
#: admits, on two input modes, windows up to 9 at four ports (31,185), 3 at
#: six ports, 1 at eight; the instances' defaults cost 1,134.
MAX_RECEIVER_WORK: Final[int] = 40_000
#: The largest dimension of one photon-number block on a station's input modes,
#: ``C(n + k - 1, k - 1)``: a probe's extra input modes make it grow fastest.
MAX_INPUT_BLOCK: Final[int] = 64
#: The most detector ports one station may declare: the coarse-graining is a
#: table over the ``2^K`` click patterns and the receiver's work grows as
#: ``3^K`` (a work bound).
MAX_PORTS: Final[int] = 8
#: The most optical modes one station may declare (a size bound).
MAX_MODES: Final[int] = 32
#: The most numerical tolerances a station may declare (the receiver reads
#: eight).
MAX_TOLERANCES: Final[int] = 16
#: A ``wcp_decoy`` source: the largest source cutoff (decoy_bb84's table admits
#: 100), the largest intensity (its table admits 10, and the Poisson
#: enclosure's series grows with ``mu``), and the most intensities and
#: polarisations. ``tests/property/test_declared_poisson_enclosures.py`` holds
#: the enclosure over exactly this domain, so these hold for every document,
#: packaged or not: they equal decoy_bb84's own domains.
MAX_SOURCE_CUTOFF: Final[int] = 100
MAX_INTENSITY: Final[int] = 10
MAX_SOURCE_LABELS: Final[int] = 16

#: The model's fields that declare a Hilbert-space dimension (an ``int``), or a
#: list of them (``dims`` of a sector declaration).
DIMENSION_KEYS: Final[frozenset[str]] = frozenset(
    {"alice_dim", "transmitted_dim", "virtual_dim", "dimension", "identity", "dims"}
)


#: The top-level blocks that declare operators and their spaces.
OPERATOR_BLOCKS: Final[tuple[str, ...]] = (
    "source",
    "stations",
    "constraints",
    "honest",
)


def photon_blocks(inputs: int, deepest: int) -> list[int]:
    """Return ``dim(n) = C(n + k - 1, k - 1)`` for ``n = 0..deepest`` on ``k`` modes."""
    if inputs <= 0:
        return []
    return [math.comb(n + inputs - 1, inputs - 1) for n in range(max(deepest, 0) + 1)]


def receiver_work(ports: int, inputs: int, deepest: int) -> int:
    """Return the receiver's work, ``3^K * sum_{n <= m} dim(n)^2`` (above).

    The one measure of :data:`MAX_RECEIVER_WORK`, also read by the facade's
    cost estimate (``runs/facade/estimate.py``), which applies it to every
    instance's configuration, packaged or not.
    """
    work: int = 3**ports * sum(
        block * block for block in photon_blocks(inputs, deepest)
    )
    return work


def check_size(count: int, limit: int, what: str, path: str) -> None:
    """Refuse ``what`` at ``path`` when ``count`` exceeds ``limit``."""
    if count > limit:
        raise DocumentError(
            f"{what} would be {count}; a protocol document allows at most {limit}",
            reason=DocumentReason.DOCUMENT_TOO_LARGE,
            path=path,
        )


def check_dimensions(tree: Mapping[str, Any]) -> None:
    """Refuse a declared dimension above :data:`MAX_DIMENSION`, before any is used.

    Every field named in :data:`DIMENSION_KEYS` whose value is an integer (or
    a list of integers) is a dimension, in the blocks that hold operators
    (:data:`OPERATOR_BLOCKS`). Alphabets and rules are not read, so a product
    dimension that happens to be called ``dims`` is a label set, not a size.
    """
    for block in OPERATOR_BLOCKS:
        if block in tree:
            for value, path in _dimensions(tree[block], pointer(block)):
                check_size(value, MAX_DIMENSION, "a Hilbert-space dimension", path)


def _dimensions(node: object, path: str) -> Iterator[tuple[int, str]]:
    if isinstance(node, dict):
        for key, item in node.items():
            where = path + pointer(key)
            if key in DIMENSION_KEYS:
                if isinstance(item, int) and not isinstance(item, bool):
                    yield item, where
                    continue
                if isinstance(item, list) and all(
                    isinstance(x, int) and not isinstance(x, bool) for x in item
                ):
                    yield from (
                        (x, where + pointer(index)) for index, x in enumerate(item)
                    )
                    continue
            yield from _dimensions(item, where)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from _dimensions(item, path + pointer(index))
