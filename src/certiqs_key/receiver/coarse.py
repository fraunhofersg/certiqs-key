"""The declared coarse-graining onto the emitted outcome alphabet.

Definition ``def:coarse`` and Theorem ``thm:coarse-graining``:

    F_v = sum over the fibre cg^{-1}(v) of M_S ,   cg : 2^[K] -> V surjective.

THE ALPHABET IS DECLARED, NEVER HARDCODED
=========================================
Requirement ``req:declared-alphabet``: the optical profile's six-outcome alphabet
at ``K = 4`` is ONE INSTANCE and not the definition, and a receiver that fixed
six outcomes over four detectors internally would make the outcome alphabet an
implementation detail of the receiver rather than a declared property of the
protocol. ``V`` and ``cg`` are DATA-FLOW inputs supplied at run time by the
protocol declaration (``interface.yaml`` ``data_flow_inputs``). Nothing in this
file constructs an alphabet; it validates and applies a declared one.

WHICH ``V`` THIS BINDS. ``interface.yaml``
``data_flow_inputs.emitted_outcome_alphabet`` names a collision: the joint
outcome alphabet ``V`` of spec/notation.md (section 3.3) also carries the
per-round classical choices, the probe setting among them, whereas this ``V`` is
the RECEIVER's own per-round alphabet, which carries the click pattern and not
the probe setting. An implementer binding this key binds the receiver alphabet,
not the declaration's, and this module so binds it.

THE ID ASSIGNMENT AND THE EMITTED ORDER
=======================================
``interface.yaml`` ``outputs.outcome_alphabet.order_and_ids_note`` leaves open
which particular stable IDs are assigned, and whether the emitted order is the
declared order of ``V`` or is derived from an ordering of ``2^[K]`` through
``cg``. No theorem distinguishes two choices: Theorem ``thm:coarse-graining``
indexes by the LETTER and sums over a FIBRE, which is a set.

**THE DECISION, taken in :class:`CoarseGraining`:** the emitted order is the
DECLARED order of ``V``, and the stable ID of a letter is its position in that
declared order, counted from zero. Two reasons. First, ``V`` arrives as data
from the protocol declaration, which already presents it as an ordered
alphabet; deriving a second order here from an ordering of ``2^[K]`` would make
the emitted index depend on a convention this module chose, which is the exact
failure Requirement ``req:declared-alphabet`` names for the alphabet itself. Second,
the outputs table calls the labels presentation metadata
(``outputs.outcome_alphabet``), so the ID must not be derived from a label --
and a position in the declared list is the one stable identifier that is not.

COARSENING IS LOSSY IN ONE DIRECTION ONLY
=========================================
Theorem ``thm:coarse-graining`` (ii): per-outcome-set lower bounds ADD, and if
the fibre STRICTLY CONTAINS the bounded outcome set the bound still holds,
because the remaining elements of the fibre are positive and are added. Theorem
``thm:coarse-graining`` (iii): a bound on a coarse outcome says NOTHING about
its fibres. That asymmetry is why Definition ``def:slot`` indexes the
strengthening slot by OUTCOME SETS and not by emitted letters, and it is why
nothing in this file pushes a bound downward.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from certiqs_key.receiver.numerics import Matrix
from certiqs_key.receiver.povm import NoClickFamily, element_block, raw_alphabet
from certiqs_key.receiver.reasons import Refusal, RefusalReason

__all__ = [
    "CoarseGraining",
    "check_coarse_graining",
    "coarse_block",
    "coarse_blocks",
    "fibre_bound",
]


@dataclass(frozen=True)
class CoarseGraining:
    """A declared surjection ``cg : 2^[K] -> V`` with its emitted alphabet.

    ``alphabet`` is the declared emitted alphabet IN ITS DECLARED ORDER, and
    ``assignment`` maps every raw click pattern to one of its letters. The
    stable ID of a letter is its index in ``alphabet``; the letter itself is
    presentation metadata (``interface.yaml`` ``outputs.outcome_alphabet``).
    """

    port_count: int
    alphabet: tuple[str, ...]
    assignment: Mapping[frozenset[int], str]

    def identifier(self, letter: str) -> int:
        """Return the stable ID of an emitted letter: its declared position."""
        return self.alphabet.index(letter)

    def fibre(self, letter: str) -> tuple[frozenset[int], ...]:
        """Return ``cg^{-1}(v)``, the raw patterns the letter aggregates."""
        return tuple(
            pattern
            for pattern in raw_alphabet(self.port_count)
            if self.assignment.get(pattern) == letter
        )


def check_coarse_graining(coarse: CoarseGraining) -> Refusal | None:
    """Return a refusal if ``cg`` is not a total surjection onto ``V``.

    Definition ``def:coarse`` requires both, and the proof of Theorem
    ``thm:coarse-graining`` (i) uses exactly one hypothesis: that the fibres PARTITION
    ``2^[K]``, which is what "``cg`` is a total map" means.
    """
    patterns = raw_alphabet(coarse.port_count)
    missing = [pattern for pattern in patterns if pattern not in coarse.assignment]
    if missing:
        return Refusal(
            RefusalReason.COARSE_GRAINING_NOT_TOTAL,
            f"cg assigns no letter to {len(missing)} of the {len(patterns)} raw "
            f"click patterns, the first being {sorted(missing[0])}; Definition "
            f"def:coarse declares a TOTAL map on 2^[K]",
        )
    unknown = {
        letter for letter in coarse.assignment.values() if letter not in coarse.alphabet
    }
    if unknown:
        return Refusal(
            RefusalReason.COARSE_GRAINING_NOT_TOTAL,
            f"cg maps a pattern to {sorted(unknown)!r}, which is not a letter of "
            f"the declared emitted alphabet",
        )
    hit = set(coarse.assignment.values())
    unreached = [letter for letter in coarse.alphabet if letter not in hit]
    if unreached:
        return Refusal(
            RefusalReason.COARSE_GRAINING_NOT_SURJECTIVE,
            f"no click pattern maps to the declared letter(s) {unreached!r}; "
            f"Definition def:coarse requires cg to be SURJECTIVE onto V",
        )
    if len(set(coarse.alphabet)) != len(coarse.alphabet):
        return Refusal(
            RefusalReason.COARSE_GRAINING_NOT_SURJECTIVE,
            "the declared emitted alphabet repeats a letter, so its stable IDs "
            "would not identify a letter",
        )
    return None


def coarse_block(
    family: NoClickFamily, coarse: CoarseGraining, letter: str, photons: int
) -> Matrix:
    """Return ``blk F_v^{(=n)}`` -- Eq. ``eq:coarse`` on one photon block.

    Theorem ``thm:coarse-graining`` (i): "the block of a finite sum is the sum of the
    blocks".
    """
    size = family.block_dimension(photons)
    total = np.zeros((size, size), dtype=np.complex128)
    for pattern in coarse.fibre(letter):
        total = total + element_block(family, pattern, photons)
    return np.asarray(total, dtype=np.complex128)


def coarse_blocks(
    family: NoClickFamily, coarse: CoarseGraining, photons: int
) -> dict[str, Matrix]:
    """Return every emitted block at one photon number, keyed by letter."""
    return {
        letter: coarse_block(family, coarse, letter, photons)
        for letter in coarse.alphabet
    }


def fibre_bound(
    coarse: CoarseGraining,
    letter: str,
    bounded: Sequence[tuple[Iterable[int], float]],
) -> float:
    """Return the bound Theorem ``thm:coarse-graining`` (ii) gives the emitted letter.

    "Bounds add": if every ``S`` in an outcome set ``O`` satisfies
    ``blk M_S^{(>N)} >= p_S`` then their sum satisfies the sum of the ``p_S``,
    and if ``cg^{-1}(v)`` CONTAINS ``O`` the bound still holds for ``F_v``,
    because the remaining elements of the fibre are positive and are added
    (the proof of (ii)).

    A bounded outcome set that is not inside the fibre contributes nothing:
    the theorem is a statement about a sum over a subset of the fibre, and
    Theorem ``thm:coarse-graining`` (iii) forbids the other direction.
    """
    fibre = set(coarse.fibre(letter))
    return sum(weight for pattern, weight in bounded if frozenset(pattern) in fibre)
