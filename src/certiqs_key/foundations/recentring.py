"""Recentring an entrywise enclosure at zero: ``foundations/lem:recentred-enclosure``.

WHY THIS EXISTS. A reference known through an entrywise enclosure says, at an
entry whose disc contains ``0``, nothing about whether the entry is zero. A
family evaluated at its centres would then carry there a number of the order
of the radius that the model may not have, and a support decision taken on the
evaluation (the key-inert pairs and the rank comparison behind (H-SUPP)) could
see support the model lacks. The direct route
(``meat-core/frank-wolfe/req:bracket-on-reference``) evaluates the first-order
bound on such centres, so ``reductions/req:reference-companion`` (i) recentres
every handed block before the construction and the companion's datum after it.

WHAT IS HERE. One record and two pure functions on exact data, no float
anywhere and NO ARRAY LIBRARY: :mod:`certiqs_key.reductions` reads them, and
importing that package loads no NumPy (``tests/golden/
test_reductions_docking.py``). That is why the record is not
:class:`certiqs_key.foundations.reference.Enclosure`, whose module sits beside
the snap, which loads NumPy; :meth:`EntrywiseEnclosure.of` reads one.

* :func:`hermitian_enclosure` is part (iv): any pair ``(C~, r~)`` enclosing a
  Hermitian matrix is replaced by ``((C~ + C~^dagger)/2, (r~ + r~^T)/2)``,
  which encloses it too and has a Hermitian centre and symmetric radii;
* :func:`recentred_enclosure` is part (i): every entry whose disc contains
  ``0`` (``Re^2 + Im^2 <= r^2``, a comparison of rationals) gets centre ``0``
  and radius ``r + |Re C| + |Im C|``; every other entry is unchanged.

The second returns the number of entries it changed, which the companion's
record carries (``req:reference-companion`` (v)).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import ZERO, Cx, Matrix
from certiqs_key.foundations.reference import FactorEnclosure

__all__ = [
    "EntrywiseEnclosure",
    "Radii",
    "hermitian_enclosure",
    "recentred_enclosure",
]

#: Rational radii, one per entry, as rows.
Radii = tuple[tuple[Fraction, ...], ...]


class _Enclosed(Protocol):
    """Any record with a centre and radii (``foundations/def:exact-reference``)."""

    @property
    def centre(self) -> Matrix:
        """The centre, entries in ``Q(i)``."""
        ...

    @property
    def radii(self) -> Radii:
        """The radii, non-negative rationals."""
        ...


@dataclass(frozen=True)
class EntrywiseEnclosure:
    """An entrywise enclosure ``(C, r)``: ``|X_il - C_il| <= r_il`` for every entry.

    ``foundations/def:exact-reference``'s enclosure as data: a centre with
    entries in ``Q(i)`` and non-negative rational radii. That it encloses the
    model is the constructing module's claim, never decided here. ``factor``
    is the factor enclosure carried on the same block, if any
    (``foundations/def:factor-enclosure``), handed with it unaltered; the
    recentring below leaves it behind, its box enclosing the block itself.
    """

    centre: Matrix
    radii: Radii
    factor: FactorEnclosure | None = None

    def __post_init__(self) -> None:
        """Refuse a ragged presentation."""
        size = len(self.centre)
        if len(self.radii) != size or any(
            len(row) != size for row in (*self.centre, *self.radii)
        ):
            raise MalformedInputError("an enclosure is a square centre with its radii")

    @classmethod
    def of(cls, enclosure: _Enclosed) -> EntrywiseEnclosure:
        """Read any enclosure record with a centre and radii, and its factor."""
        return cls(
            enclosure.centre, enclosure.radii, getattr(enclosure, "factor", None)
        )

    @property
    def largest_radius(self) -> Fraction:
        """The largest single radius."""
        return max((r for row in self.radii for r in row), default=Fraction(0))

    @property
    def is_exact(self) -> bool:
        """Whether every radius is zero."""
        return all(r == 0 for row in self.radii for r in row)


def hermitian_enclosure(centre: Matrix, radii: Radii) -> EntrywiseEnclosure:
    """Return part (iv) of ``foundations/lem:recentred-enclosure``.

    ``(centre, radii)`` encloses a Hermitian matrix ``X`` entrywise; the
    returned enclosure has the averaged centre ``(C + C^dagger)/2`` and the
    averaged radii ``(r + r^T)/2``, so it encloses ``X`` with a Hermitian centre
    and symmetric radii, and it equals the input where the input already has
    both (the lemma's last sentence).
    """
    size = len(centre)
    if len(radii) != size or any(len(row) != size for row in (*centre, *radii)):
        raise MalformedInputError("an enclosure is a square centre with its radii")
    half = Fraction(1, 2)
    averaged = tuple(
        tuple(
            centre[i][j]
            if centre[i][j] == centre[j][i].conjugate()
            else Cx(
                (centre[i][j].re + centre[j][i].re) * half,
                (centre[i][j].im - centre[j][i].im) * half,
            )
            for j in range(size)
        )
        for i in range(size)
    )
    symmetric = tuple(
        tuple(
            radii[i][j] if radii[i][j] == radii[j][i]
            else (radii[i][j] + radii[j][i]) * half
            for j in range(size)
        )
        for i in range(size)
    )
    return EntrywiseEnclosure(averaged, symmetric)


def recentred_enclosure(
    enclosure: EntrywiseEnclosure,
) -> tuple[EntrywiseEnclosure, int]:
    """Return part (i) of ``foundations/lem:recentred-enclosure``, with a count.

    The set ``Z`` of entries whose enclosure contains ``0`` is decided by
    ``(Re C)^2 + (Im C)^2 <= r^2``; on ``Z`` the centre is set to ``0`` and the
    radius widened by ``|Re C| + |Im C|`` (at most ``(1 + sqrt 2) r``, part
    (ii)), off ``Z`` nothing changes. A structurally zero entry (centre and
    radius ``0``) lies in ``Z`` and stays as it is, so an exact enclosure is
    returned unchanged (part (iii)). The count is the number of entries whose
    centre was not already ``0`` and was set to ``0``.
    """
    changed = 0
    centre_rows: list[tuple[Cx, ...]] = []
    radius_rows: list[tuple[Fraction, ...]] = []
    for row, radius_row in zip(enclosure.centre, enclosure.radii, strict=True):
        centres: list[Cx] = []
        radii: list[Fraction] = []
        for entry, radius in zip(row, radius_row, strict=True):
            if entry.squared_modulus <= radius * radius and not entry.is_zero:
                centres.append(ZERO)
                radii.append(radius + abs(entry.re) + abs(entry.im))
                changed += 1
            else:
                centres.append(entry)
                radii.append(radius)
        centre_rows.append(tuple(centres))
        radius_rows.append(tuple(radii))
    if not changed:
        return enclosure, 0
    return EntrywiseEnclosure(tuple(centre_rows), tuple(radius_rows)), changed
