"""The lattice-exponent check, the weight ladder and the round-down list: one copy.

WHY THIS FILE EXISTS
====================
spec/architecture.md 2.9: "``foundations/rungs.py`` holds the lattice-exponent
check and the round-down candidate list once, NumPy-free: the candidate list
is what the emission normaliser's last-resort fall-back reads
(``reductions/def:emitnorm`` (3)), and no other module spells one of its
own." Two copies of the candidate list and of the ladder, one in the instance
snap and one in the normaliser, would risk drift. The instance snap does not
round down, so the normaliser is the one reader, and the list lives here so
that a second reader would find it rather than spell it again.

This module is NumPy-free on purpose: it imports the standard library and
:mod:`certiqs_key.foundations.exact` only, which a test keeps true, so that
importing :mod:`certiqs_key.reductions` pulls in no array library.
"""

from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    is_hermitian,
    is_positive_semidefinite,
    lattice_round_matrix,
    on_lattice,
)

__all__ = [
    "MAX_LATTICE_EXPONENT",
    "checked_lattice_exponent",
    "round_down",
    "round_down_candidates",
    "rung_ladder",
]

#: The widest lattice: ``k <= 53`` is half of (D-LAT); above it an integer
#: multiple of ``2^-k`` of modulus one is not a binary64 number.
MAX_LATTICE_EXPONENT: Final[int] = 53


def checked_lattice_exponent(lattice_exponent: int) -> int:
    """Return the lattice exponent ``1 <= k <= 53``, or raise."""
    if isinstance(lattice_exponent, bool) or not isinstance(lattice_exponent, int):
        raise MalformedInputError(
            f"lattice exponent {lattice_exponent!r} is not an integer"
        )
    if not 1 <= lattice_exponent <= MAX_LATTICE_EXPONENT:
        raise MalformedInputError(
            f"lattice exponent {lattice_exponent} is outside "
            f"[1, {MAX_LATTICE_EXPONENT}] (foundations/def:binary64 (iv))"
        )
    return lattice_exponent


def rung_ladder(lattice_exponent: int) -> tuple[Fraction, ...]:
    """Return the weights ``2^-k, 2^-(k-1), ..., 2^-1``, smallest first.

    The ladder ``reductions/def:emitnorm`` (2) and (3) walk at ``k = kappa``
    (step (2) tries ``w = 0`` before it).
    """
    k = checked_lattice_exponent(lattice_exponent)
    return tuple(Fraction(1, 1 << level) for level in range(k, 0, -1))


def _minus_diagonal(m: Matrix, amount: Fraction) -> Matrix:
    shift = Cx(amount, Fraction(0))
    return tuple(
        tuple(entry - shift if i == j else entry for j, entry in enumerate(row))
        for i, row in enumerate(m)
    )


def _scaled(factor: Fraction, m: Matrix) -> Matrix:
    scalar = Cx(factor, Fraction(0))
    return tuple(tuple(scalar * entry for entry in row) for row in m)


def _zero(size: int) -> Matrix:
    zero = Cx(Fraction(0), Fraction(0))
    return tuple(tuple(zero for _ in range(size)) for _ in range(size))


def _is_zero(m: Matrix) -> bool:
    return all(entry.is_zero for row in m for entry in row)


def round_down_candidates(element: Matrix, lattice_exponent: int) -> tuple[Matrix, ...]:
    """Return the fixed candidate list of the round-down step, repeats dropped.

    ``reductions/def:emitnorm`` (3), the fall-back of the last resort: the
    element as it stands; then, for ``r = k, k-1, ..., 1``, the shift
    ``X - 2^-r 1`` and the scaling ``(1 - 2^-r) X``, each rounded part by part
    to the nearest multiple of ``2^-k``, ties to even; finally ``0``. A repeat
    is dropped: it was refused where it first appeared. Ties to even is
    odd-symmetric, so a candidate formed from a Hermitian matrix is Hermitian.
    """
    k = checked_lattice_exponent(lattice_exponent)
    out: list[Matrix] = [element]
    for level in range(k, 0, -1):
        step = Fraction(1, 1 << level)
        out.append(lattice_round_matrix(_minus_diagonal(element, step), k))
        out.append(lattice_round_matrix(_scaled(Fraction(1) - step, element), k))
    out.append(_zero(len(element)))
    unique: list[Matrix] = []
    seen: set[Matrix] = set()
    for candidate in out:
        if candidate not in seen:
            seen.add(candidate)
            unique.append(candidate)
    return tuple(unique)


def round_down(
    element: Matrix,
    lattice_exponent: int,
    *,
    below: Callable[[Matrix], bool],
) -> Matrix:
    """Return the first candidate ``F`` with ``0 <= F <= X`` on the lattice.

    The first matrix of :func:`round_down_candidates` that is Hermitian, a
    lattice value at ``k``, decided positive semidefinite exactly, and for
    which ``below(F)`` -- the caller's exact decision of ``X - F >= 0`` --
    holds (``reductions/def:emitnorm``, Eq. ``eq:rounddown``). The zero matrix
    qualifies without a decision: ``X`` is positive semidefinite, so every
    element receives a candidate and a zero element comes back exactly zero.
    """
    k = checked_lattice_exponent(lattice_exponent)
    for candidate in round_down_candidates(element, k):
        if _is_zero(candidate):
            return candidate
        if not on_lattice(candidate, k) or not is_hermitian(candidate):
            continue
        if not is_positive_semidefinite(candidate):
            continue
        if below(candidate):
            return candidate
    return _zero(len(element))  # pragma: no cover - the list ends with zero
