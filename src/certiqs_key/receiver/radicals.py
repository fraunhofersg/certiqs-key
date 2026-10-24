"""Exact arithmetic in ``Q(i)`` adjoined finitely many square roots of rationals.

Requirement ``req:exact-route-decision`` (ii): "the arithmetic represents at
least the field generated over ``Q(i)`` by ``sqrt 2`` and by ``sqrt p`` and
``sqrt(1-p)`` for every declared rational parameter ``p`` in ``[0, 1]``", in
which the engine compiles the instrument matrix and the port Grams EXACTLY and
decides whether every port Gram has entries in ``Q(i)``. This module is that
arithmetic.

THE REPRESENTATION
==================
A field ``Q(i)(sqrt n_1, ..., sqrt n_r)`` with positive integers ``n_j`` is
spanned over ``Q(i)`` by the monomials ``prod_{j in S} sqrt n_j``. They are a
BASIS -- so that "has entries in ``Q(i)``" is the plain test "only the empty
monomial carries a coefficient" -- once the ``n_j`` are replaced by a
**coprime base**: pairwise coprime integers ``b_1, ..., b_m > 1``, none a
perfect square, such that every radicand is a product of powers of them.
Then a product ``prod_{j in S} b_j`` over a non-empty ``S`` is never a perfect
square (the ``b_j`` share no prime and none is a square), so the monomials are
rational multiples of square roots of DISTINCT squarefree integers greater
than one, which are linearly independent over ``Q``, and so over ``Q(i)``:
a relation splits into its real and imaginary parts, each a rational relation
among real square roots. The base is built by gcd refinement, without
factoring any integer.

THE BASE IS FIXED BEFORE ANY NUMBER IS FORMED
=============================================
Refining the base later would change the meaning of numbers already formed,
so a :class:`RadicalField` is built from every radicand its computation will
need (:func:`radicands_of`, which runs the same element formulas with a field
that only records), and a square root it was not built for is NOT
REPRESENTED rather than silently mis-represented.

ANGLES
======
``cos`` and ``sin`` of ``c pi`` lie in ``Q(sqrt 2)`` exactly when ``4c`` is an
integer, and those are the values this arithmetic represents; any other
angle -- a non-zero angle in radians among them -- raises
:class:`NotRepresented`, which the decision of Requirement
``req:exact-route-decision`` (ii) records as its cause.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.exact import Cx
from certiqs_key.receiver.enclosure import (
    DEFAULT_BITS,
    Ball,
    exact_angle,
    sqrt_enclosure,
)
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.numerics import Angle, PiMultiple

__all__ = [
    "NotRepresented",
    "Radical",
    "RadicalField",
    "coprime_base",
]

_ZERO: Final[Fraction] = Fraction(0)


class NotRepresented(Exception):
    """A value the exact arithmetic does not represent.

    Not an error of the declaration: Requirement ``req:exact-route-decision``
    (ii) treats such a declaration as off the exact route and records why.
    """


def coprime_base(values: Iterable[int]) -> tuple[int, ...]:
    """Return a coprime base of positive integers by gcd refinement.

    Every input is a product of powers of the returned integers, which are
    pairwise coprime and greater than one. A pair sharing a factor
    ``g = gcd(a, b) > 1`` is replaced by ``a / g``, ``g`` and ``b / g``; the
    product of the list strictly decreases, so the refinement terminates.
    """
    work = sorted({value for value in values if value > 1})
    changed = True
    while changed:
        changed = False
        for first in range(len(work)):
            for second in range(first + 1, len(work)):
                a, b = work[first], work[second]
                g = math.gcd(a, b)
                if g > 1:
                    rest = [w for k, w in enumerate(work) if k not in (first, second)]
                    work = sorted({w for w in (*rest, a // g, g, b // g) if w > 1})
                    changed = True
                    break
            if changed:
                break
    return tuple(work)


class Radical:
    """An element ``sum_S c_S prod_{j in S} sqrt b_j`` of a :class:`RadicalField`.

    ``terms`` maps the bit mask of ``S`` to the Gaussian-rational coefficient
    ``c_S`` as a ``(re, im)`` pair; zero coefficients are never stored, so the
    empty mapping is zero.
    """

    __slots__ = ("field", "terms")

    field: RadicalField
    terms: dict[int, tuple[Fraction, Fraction]]

    def __init__(
        self, field: RadicalField, terms: Mapping[int, tuple[Fraction, Fraction]]
    ) -> None:
        """Build an element, dropping zero coefficients."""
        self.field = field
        self.terms = {
            mask: (re, im) for mask, (re, im) in terms.items() if re != 0 or im != 0
        }

    def _check(self, other: Radical) -> None:
        if other.field is not self.field:
            raise HypothesisError("two radicals of different fields were combined")

    def __add__(self, other: Radical) -> Radical:
        """Return the sum, coefficient by coefficient."""
        self._check(other)
        terms = dict(self.terms)
        for mask, (re, im) in other.terms.items():
            a, b = terms.get(mask, (_ZERO, _ZERO))
            terms[mask] = (a + re, b + im)
        return Radical(self.field, terms)

    def __neg__(self) -> Radical:
        """Return the additive inverse."""
        return Radical(
            self.field, {mask: (-re, -im) for mask, (re, im) in self.terms.items()}
        )

    def __sub__(self, other: Radical) -> Radical:
        """Return the difference."""
        return self + (-other)

    def __mul__(self, other: Radical) -> Radical:
        """Return the product: ``sqrt b_j sqrt b_j = b_j`` on common factors."""
        self._check(other)
        terms: dict[int, tuple[Fraction, Fraction]] = {}
        for m1, (a, b) in self.terms.items():
            for m2, (c, d) in other.terms.items():
                factor = self.field.common_factor(m1 & m2)
                re = (a * c - b * d) * factor
                im = (a * d + b * c) * factor
                mask = m1 ^ m2
                x, y = terms.get(mask, (_ZERO, _ZERO))
                terms[mask] = (x + re, y + im)
        return Radical(self.field, terms)

    def conjugate(self) -> Radical:
        """Return the complex conjugate: the monomials are real."""
        return Radical(
            self.field, {mask: (re, -im) for mask, (re, im) in self.terms.items()}
        )

    @property
    def is_gaussian_rational(self) -> bool:
        """Whether the element lies in ``Q(i)``: only the empty monomial is used.

        Decisive because the monomials are a basis (module docstring).
        """
        return all(mask == 0 for mask in self.terms)

    def as_cx(self) -> Cx:
        """Return the element as a foundations :class:`Cx`; it must be in ``Q(i)``."""
        if not self.is_gaussian_rational:
            raise HypothesisError("the element is not a Gaussian rational")
        re, im = self.terms.get(0, (_ZERO, _ZERO))
        return Cx(re, im)

    def to_ball(self, bits: int = DEFAULT_BITS) -> tuple[Ball, Fraction]:
        """Return a complex enclosure of the element and its largest leaf radius.

        The element is a finite expression in square roots of integers, so
        Lemma ``lem:enclosure-arithmetic`` (iv) encloses it from
        square-root enclosures of the monomials (Requirement
        ``req:exact-route-decision`` (iii): "where the exact arithmetic of (ii)
        has computed a port Gram, its entries ... may be enclosed from those
        expressions instead"); the empty monomial is exact, so an element of
        ``Q(i)`` is enclosed exactly.
        """
        total = Ball(_ZERO)
        largest = _ZERO
        for mask, (re, im) in self.terms.items():
            coefficient = Ball(re, im)
            if mask == 0:
                total = total + coefficient
                continue
            root = sqrt_enclosure(Fraction(self.field.product(mask)), bits)
            largest = max(largest, root.radius)
            total = total + coefficient * root
        return total, largest


class RadicalField:
    """``Q(i)(sqrt b_1, ..., sqrt b_m)`` over a coprime base fixed at construction.

    Implements the exact arithmetic Requirement ``req:exact-route-decision``
    (ii) asks for: built from every rational whose square root the
    computation takes (``2`` always included), it represents each of them,
    together with ``cos`` and ``sin`` of ``c pi`` for ``4c`` an integer.
    """

    def __init__(self, radicands: Iterable[Fraction]) -> None:
        """Build the coprime base of ``2`` and of every radicand's integer form."""
        integers = {2}
        for value in radicands:
            if value < 0:
                raise NotRepresented(f"the square root of {value} is not real")
            integers.add(value.numerator * value.denominator)
        base = []
        for candidate in coprime_base(integers):
            root = math.isqrt(candidate)
            if root * root != candidate:
                base.append(candidate)
        self.base: tuple[int, ...] = tuple(base)
        self._squares: tuple[int, ...] = tuple(
            b for b in coprime_base(integers) if math.isqrt(b) ** 2 == b
        )
        self._products: dict[int, int] = {}

    # -- the field structure ----------------------------------------------

    def product(self, mask: int) -> int:
        """Return ``prod_{j in mask} b_j``."""
        cached = self._products.get(mask)
        if cached is None:
            cached = 1
            for j, b in enumerate(self.base):
                if mask >> j & 1:
                    cached *= b
            self._products[mask] = cached
        return cached

    def common_factor(self, mask: int) -> Fraction:
        """Return ``prod_{j in mask} b_j``, the rational ``sqrt b_j^2`` products."""
        if mask == 0:
            return Fraction(1)
        return Fraction(self.product(mask))

    def zero(self) -> Radical:
        """Return ``0``."""
        return Radical(self, {})

    def one(self) -> Radical:
        """Return ``1``."""
        return Radical(self, {0: (Fraction(1), _ZERO)})

    def gaussian(self, re: Fraction, im: Fraction = _ZERO) -> Radical:
        """Return the Gaussian rational ``re + i im``."""
        return Radical(self, {0: (re, im)})

    def rational(self, value: Fraction) -> Radical:
        """Return a rational."""
        return self.gaussian(value)

    def sqrt(self, value: Fraction) -> Radical:
        """Return ``sqrt value`` for a rational ``value >= 0`` of the field.

        ``sqrt(a / q) = sqrt(a q) / q``; the integer ``a q`` is factored over
        the coprime base (and the perfect squares the refinement split off),
        even powers leaving the root as rationals.

        Raises:
            NotRepresented: for a negative value, or one whose integer form is
                not a product of the base the field was built for.
        """
        if value < 0:
            raise NotRepresented(f"the square root of {value} is not real")
        if value == 0:
            return self.zero()
        n = value.numerator * value.denominator
        coefficient = Fraction(1, value.denominator)
        mask = 0
        for square in self._squares:
            exponent = 0
            while n % square == 0:
                n //= square
                exponent += 1
            coefficient *= math.isqrt(square) ** exponent
        for j, b in enumerate(self.base):
            exponent = 0
            while n % b == 0:
                n //= b
                exponent += 1
            coefficient *= b ** (exponent // 2)
            if exponent % 2:
                mask |= 1 << j
        root = math.isqrt(n)
        if root * root != n:
            raise NotRepresented(
                f"sqrt({value}) is outside the field this computation was built for"
            )
        coefficient *= root
        return Radical(self, {mask: (coefficient, _ZERO)})

    def cos_sin(self, angle: Angle) -> tuple[Radical, Radical]:
        """Return ``(cos theta, sin theta)`` for ``theta = c pi`` with ``4c`` integral.

        Raises:
            NotRepresented: for a non-zero angle in radians or a multiple of pi
                whose coefficient times four is not an integer.
        """
        value = exact_angle(angle)
        if not isinstance(value, PiMultiple):
            if value == 0:
                return self.one(), self.zero()
            raise NotRepresented(
                f"the angle {value} is given in radians and is not zero; only a "
                f"coefficient of pi reaches the exact route"
            )
        quarter = 4 * value.coefficient
        if quarter.denominator != 1:
            raise NotRepresented(
                f"cos and sin of {value} are not in Q(sqrt 2): its coefficient "
                f"times four is not an integer"
            )
        k = int(quarter) % 8
        half_root = self.sqrt(Fraction(1, 2))
        table: dict[int, tuple[Radical, Radical]] = {
            0: (self.one(), self.zero()),
            1: (half_root, half_root),
            2: (self.zero(), self.one()),
            3: (-half_root, half_root),
            4: (-self.one(), self.zero()),
            5: (-half_root, -half_root),
            6: (self.zero(), -self.one()),
            7: (half_root, -half_root),
        }
        return table[k]

    def is_zero(self, value: Radical) -> bool:
        """Return whether the element is zero: no coefficient is stored."""
        return not value.terms

    def reciprocal(self, value: Radical) -> Radical:
        """Return ``1 / value`` for a non-zero Gaussian rational.

        Raises:
            NotRepresented: for an element outside ``Q(i)``, whose reciprocal
                this computation never needs.
        """
        if not value.is_gaussian_rational:
            raise NotRepresented("the reciprocal of a non-Gaussian-rational element")
        z = value.as_cx()
        squared = z.re * z.re + z.im * z.im
        if squared == 0:
            raise HypothesisError("division by zero in the exact arithmetic")
        return self.gaussian(z.re / squared, -z.im / squared)
