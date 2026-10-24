"""Complex enclosures and their arithmetic, in exact rational arithmetic.

Definition ``def:complex-enclosure`` and Lemma ``lem:enclosure-arithmetic``.
A complex enclosure of a number ``x`` is a Gaussian-rational centre ``x_c``
with a non-negative rational radius ``r``, ``|x - x_c| <= r``; it is exact
where ``r = 0``. :class:`Ball` is that pair, and its operators ARE the rules
of the lemma, item by item:

    (i)   sums, negation, conjugation   (x_c + y_c, r_x + r_y), (-x_c, r_x),
                                        (conj x_c, r_x)
    (ii)  products                      (x_c y_c, |x_c|_1 r_y + r_x |y_c|_1
                                                  + r_x r_y)
    (iii) reciprocals                   (1 / x_c, r_x / (l (l - r_x))), for a
                                        rational l > 0 with l^2 <= |x_c|^2 and
                                        r_x < l
    (v)   Hermitian centres             ((X_c + X_c^dagger)/2, (r + r^T)/2)

with ``|z|_1 = |Re z| + |Im z|``. Item (iv) -- any finite expression -- is
what composing the operators does, so nothing implements it separately.

THE LEAVES
==========
Definition ``def:complex-enclosure`` fixes what an enclosure of a square root,
a cosine or a sine must satisfy and leaves open how it is computed. Here:

* :func:`sqrt_enclosure` -- a SQUARE-ROOT ENCLOSURE of a rational ``p >= 0``:
  a rational centre from an integer square root, exact where ``p`` is the
  square of a rational;
* :func:`angle_enclosure` -- an ANGLE ENCLOSURE of ``theta`` given as a
  rational (a declared value in radians) or as ``c pi``
  (:class:`~certiqs_key.receiver.numerics.PiMultiple`): rational centres for
  ``cos theta`` and ``sin theta`` from a Taylor series evaluated in integer
  fixed point with a rigorous error count, exact where ``theta = c pi`` with
  ``2c`` an integer (``0`` radians included).

NO FLOATING-POINT VALUE ENTERS AN ENCLOSURE (Requirement
``req:exact-route-decision`` (iii)): every number here is an ``int`` or a
:class:`~fractions.Fraction`, and the one constant that is not rational, pi,
enters through rational bounds computed by Machin's formula with a counted
error.

A RADIUS IS ROUNDED UP, NEVER A CENTRE
======================================
Every non-zero radius a rule produces is rounded UP to a dyadic rational of
:data:`RADIUS_BITS` significant bits (:func:`_round_up`). A pair ``(x_c, r')``
with ``r' >= r`` and ``|x - x_c| <= r`` is again a complex enclosure of ``x`` by
Definition ``def:complex-enclosure`` itself, and the rules (i)-(iii) of Lemma
``lem:enclosure-arithmetic`` hold for ANY complex enclosures of their operands,
so every node of an expression still receives a complex enclosure (the
induction of item (iv)). A zero radius is never touched, so an entry that the
lemma makes exact stays exact (item (iv), Theorem ``thm:exact-blocks`` (ii)).
Without it the radii of the probe-conditioned blocks carry denominators of
thousands of bits -- every reciprocal of a determinant, and every sum of terms
with different determinants, multiplies them -- and the construction is
slowed tenfold for no gain: the radius is an upper bound, and a relative
enlargement of ``2^-63`` is invisible beside the margins it is compared with.
Centres are never rounded.

PRECISION
=========
``bits`` sets the radius of a leaf: at most ``2^-bits`` up to a small factor.
Remark ``rem:noise-floor-receiver`` asks that the leaves be small enough that
the radius ``rho`` of every decided matrix lies well below the lattice step,
"which is more than each of them lying below it": the radii are amplified
through permanents, inclusion and exclusion and the fibre sums. The default
:data:`DEFAULT_BITS` is 128, about 88 binary orders below the lattice step
``2^-40`` of spec/architecture.md section 2.9.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction
from functools import lru_cache
from typing import Final

from certiqs_key.foundations.exact import Cx
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.numerics import Angle, PiMultiple

__all__ = [
    "DEFAULT_BITS",
    "Ball",
    "BallMatrix",
    "angle_enclosure",
    "exact_angle",
    "hermitian_centred",
    "pi_bounds",
    "sqrt_enclosure",
]

#: The precision of a leaf enclosure: its radius is at most a small multiple
#: of 2^-DEFAULT_BITS (module docstring, PRECISION).
DEFAULT_BITS: Final[int] = 128

#: The significant bits a non-zero radius is rounded up to (module docstring,
#: A RADIUS IS ROUNDED UP).
RADIUS_BITS: Final[int] = 64

_ZERO: Final[Fraction] = Fraction(0)
_ONE: Final[Fraction] = Fraction(1)


def _round_up(radius: Fraction) -> Fraction:
    """Return a dyadic ``r' >= radius`` of :data:`RADIUS_BITS` significant bits.

    Zero is returned as it is. ``r'`` is the least multiple of ``2^-s`` at or
    above ``radius``, with ``s`` chosen so that ``r'`` has about
    :data:`RADIUS_BITS` significant bits; a radius that already is such a
    dyadic is returned unchanged.
    """
    if radius == 0:
        return radius
    n, d = radius.numerator, radius.denominator
    if d & (d - 1) == 0 and n.bit_length() <= RADIUS_BITS:
        return radius
    shift = RADIUS_BITS - (n.bit_length() - d.bit_length())
    if shift >= 0:
        return Fraction(-((-n << shift) // d), 1 << shift)
    return Fraction(-(-n // (d << -shift)) << -shift)


class Ball:
    """A complex enclosure ``(x_c, r)`` -- Definition ``def:complex-enclosure``.

    Implements ``receiver/def:complex-enclosure``; its operators are the rules
    of ``receiver/lem:enclosure-arithmetic`` (i)-(iii). ``re`` and ``im`` are
    the parts of the Gaussian-rational centre and ``radius`` the non-negative
    rational radius. Immutable by convention (``__slots__``, no setters): every
    operation returns a new ball.
    """

    __slots__ = ("im", "radius", "re")

    re: Fraction
    im: Fraction
    radius: Fraction

    def __init__(
        self, re: Fraction, im: Fraction = _ZERO, radius: Fraction = _ZERO
    ) -> None:
        """Build a ball; the radius must be a non-negative rational."""
        if radius < 0:
            raise HypothesisError(f"a radius is non-negative, got {radius}")
        self.re = re
        self.im = im
        self.radius = radius

    # -- presentation ------------------------------------------------------

    @classmethod
    def exact(cls, value: Fraction | int, im: Fraction | int = 0) -> Ball:
        """Return the exact enclosure of a Gaussian rational."""
        return cls(Fraction(value), Fraction(im), _ZERO)

    @classmethod
    def of_cx(cls, value: Cx) -> Ball:
        """Return the exact enclosure of a foundations :class:`Cx`."""
        return cls(value.re, value.im, _ZERO)

    @property
    def is_exact(self) -> bool:
        """Whether the radius is zero, so that the number IS the centre."""
        return self.radius == 0

    @property
    def is_zero(self) -> bool:
        """Whether the ball is exactly zero: centre and radius both zero."""
        return self.radius == 0 and self.re == 0 and self.im == 0

    @property
    def l1(self) -> Fraction:
        """Return ``|x_c|_1 = |Re x_c| + |Im x_c|``, a rational ``>= |x_c|``."""
        return abs(self.re) + abs(self.im)

    @property
    def centre(self) -> Cx:
        """Return the centre as a foundations :class:`Cx`."""
        return Cx(self.re, self.im)

    def contains(self, value: complex) -> bool:
        """Decide exactly whether a binary64 complex number lies in the ball.

        A finite ``float`` is the dyadic rational it denotes, so the test
        ``|value - x_c|^2 <= r^2`` is decided in rational arithmetic. A test
        utility: no decision about a model is taken on a binary64 number.
        """
        dx = Fraction(value.real) - self.re
        dy = Fraction(value.imag) - self.im
        return dx * dx + dy * dy <= self.radius * self.radius

    def __repr__(self) -> str:
        """Return a short presentation with the radius as a float diagnostic."""
        return (
            f"Ball({float(self.re)!r}, {float(self.im)!r}, "
            f"radius<={float(self.radius):.3e})"
        )

    # -- lem:enclosure-arithmetic (i): sums, negation, conjugation ---------

    def __add__(self, other: Ball) -> Ball:
        """Rule (i): ``(x_c + y_c, r_x + r_y)``, the radius rounded up."""
        return Ball(
            self.re + other.re,
            self.im + other.im,
            _round_up(self.radius + other.radius),
        )

    def __sub__(self, other: Ball) -> Ball:
        """Rules (i) twice: ``x - y = x + (-y)``, the radius rounded up."""
        return Ball(
            self.re - other.re,
            self.im - other.im,
            _round_up(self.radius + other.radius),
        )

    def __neg__(self) -> Ball:
        """Rule (i): ``(-x_c, r_x)``."""
        return Ball(-self.re, -self.im, self.radius)

    def conjugate(self) -> Ball:
        """Rule (i): ``(conj x_c, r_x)``."""
        return Ball(self.re, -self.im, self.radius)

    # -- lem:enclosure-arithmetic (ii): products ---------------------------

    def __mul__(self, other: Ball) -> Ball:
        """Rule (ii): ``(x_c y_c, |x_c|_1 r_y + r_x |y_c|_1 + r_x r_y)``, rounded up."""
        if self.im == 0 and other.im == 0:
            re = self.re * other.re
            im = _ZERO
        else:
            re = self.re * other.re - self.im * other.im
            im = self.re * other.im + self.im * other.re
        if self.radius == 0 and other.radius == 0:
            return Ball(re, im, _ZERO)
        radius = self.l1 * other.radius + self.radius * other.l1
        radius += self.radius * other.radius
        return Ball(re, im, _round_up(radius))

    def scaled(self, factor: Fraction) -> Ball:
        """Rule (ii) with ``y`` the exact rational ``factor``: ``|factor| r_x``."""
        return Ball(
            self.re * factor, self.im * factor, _round_up(abs(factor) * self.radius)
        )

    # -- lem:enclosure-arithmetic (iii): reciprocals -----------------------

    def reciprocal(self, bits: int = DEFAULT_BITS) -> Ball | None:
        """Rule (iii), or ``None`` where no rational ``l`` meets its condition.

        ``l`` is a rational lower bound of ``|x_c|`` with ``l^2 <= |x_c|^2``:
        ``|x_c|`` itself where ``|x_c|^2`` is the square of a rational, and
        otherwise the integer square root of ``|x_c|^2 4^bits`` over
        ``2^bits``. The condition ``r_x < l`` is then DECIDED; where it fails
        the reciprocal receives no enclosure, which is what Lemma
        ``lem:enclosure-arithmetic`` (iv) allows for, and what
        ``detector-imperfections/req:dark-composed-reference`` (iv) records as
        a cause. An exact non-zero ``x`` always receives one, with radius
        zero.
        """
        squared = self.re * self.re + self.im * self.im
        if squared == 0:
            return None
        ell = _sqrt_lower(squared, bits)
        if ell <= 0 or not self.radius < ell:
            return None
        centre_re = self.re / squared
        centre_im = -self.im / squared
        if self.radius == 0:
            return Ball(centre_re, centre_im, _ZERO)
        return Ball(
            centre_re,
            centre_im,
            _round_up(self.radius / (ell * (ell - self.radius))),
        )


#: A matrix of enclosures, row-major: a complex enclosure of a matrix in the
#: sense of Definition def:complex-enclosure, entry by entry.
BallMatrix = list[list[Ball]]


def hermitian_centred(
    matrix: Sequence[Sequence[Ball]],
) -> tuple[tuple[tuple[Cx, ...], ...], tuple[tuple[Fraction, ...], ...]]:
    """Return ``((X_c + X_c^dagger)/2, (r + r^T)/2)`` -- the rule of item (v).

    Implements ``receiver/lem:enclosure-arithmetic`` (v): for a Hermitian
    ``X`` enclosed by ``matrix``, the result is an entrywise enclosure of ``X``
    with a Hermitian Gaussian-rational centre and symmetric radii, exact at
    ``(i, l)`` where both ``r_il`` and ``r_li`` are zero.
    """
    size = len(matrix)
    half = Fraction(1, 2)
    centre: list[tuple[Cx, ...]] = []
    radii: list[tuple[Fraction, ...]] = []
    for i in range(size):
        row_c: list[Cx] = []
        row_r: list[Fraction] = []
        for l in range(size):  # noqa: E741 - the claim's index
            a = matrix[i][l]
            b = matrix[l][i]
            row_c.append(Cx((a.re + b.re) * half, (a.im - b.im) * half))
            row_r.append((a.radius + b.radius) * half)
        centre.append(tuple(row_c))
        radii.append(tuple(row_r))
    return tuple(centre), tuple(radii)


# ---------------------------------------------------------------------------
#  Leaves: square roots
# ---------------------------------------------------------------------------


def _sqrt_lower(value: Fraction, bits: int) -> Fraction:
    """Return a rational ``l`` with ``0 <= l <= sqrt(value)``, exact on squares."""
    p, q = value.numerator, value.denominator
    root_p, root_q = math.isqrt(p), math.isqrt(q)
    if root_p * root_p == p and root_q * root_q == q:
        return Fraction(root_p, root_q)
    # sqrt(p/q) = sqrt(p q) / q, and isqrt(p q 4^bits) / (q 2^bits) is below it.
    return Fraction(math.isqrt((p * q) << (2 * bits)), q << bits)


def sqrt_enclosure(value: Fraction, bits: int = DEFAULT_BITS) -> Ball:
    """Return a square-root enclosure of a rational ``p >= 0``.

    Implements the square-root enclosure of ``receiver/def:complex-enclosure``:
    a complex enclosure of ``sqrt p`` with a rational centre, exact where ``p``
    is the square of a rational. Otherwise, with ``s = isqrt(p q 4^bits)`` for
    ``p = a / q`` in lowest terms, ``s <= sqrt(a q) 2^bits < s + 1``, so the
    centre ``(2s + 1) / (2 q 2^bits)`` lies within ``1 / (2 q 2^bits)`` of
    ``sqrt p = sqrt(a q) / q``, and that is the radius.

    Raises:
        HypothesisError: for a negative ``p``, whose square root is not real.
    """
    if value < 0:
        raise HypothesisError(f"a square-root enclosure needs p >= 0, got {value}")
    a, q = value.numerator, value.denominator
    root_a, root_q = math.isqrt(a), math.isqrt(q)
    if root_a * root_a == a and root_q * root_q == q:
        return Ball(Fraction(root_a, root_q), _ZERO, _ZERO)
    s = math.isqrt((a * q) << (2 * bits))
    scale = q << (bits + 1)
    return Ball(Fraction(2 * s + 1, scale), _ZERO, Fraction(1, scale))


# ---------------------------------------------------------------------------
#  Leaves: pi, cosines and sines
# ---------------------------------------------------------------------------


def _arctan_inverse_fixed(n: int, scale: int) -> tuple[int, int]:
    """Return ``(A, e)`` with ``|arctan(1/n) scale - A| <= e``, in integers.

    The alternating series ``sum (-1)^j / ((2j+1) n^(2j+1))`` evaluated with
    floor divisions. ``power`` approximates ``scale / n^(2j+1)`` with an error
    below two units (each floor adds less than one, and the previous error is
    divided by ``n^2 >= 25``), so each term carries an error below three
    units; the truncation error is below the first omitted term, which is
    below two units once ``power`` has reached zero.
    """
    total = 0
    error = 0
    power = scale // n  # scale / n^(2j+1), floored
    j = 0
    n_squared = n * n
    while power > 0:
        term = power // (2 * j + 1)
        total += -term if j % 2 else term
        error += 3
        power //= n_squared
        j += 1
    return total, error + 3


@lru_cache(maxsize=8)
def pi_bounds(bits: int = DEFAULT_BITS) -> tuple[Fraction, Fraction]:
    """Return rationals ``lo < pi < hi`` with ``hi - lo <= 2^-bits``.

    Machin's formula ``pi = 16 arctan(1/5) - 4 arctan(1/239)``, each arctangent
    evaluated in integer fixed point with a counted error
    (:func:`_arctan_inverse_fixed`).
    """
    guard = 16
    scale = 1 << (bits + guard)
    a5, e5 = _arctan_inverse_fixed(5, scale)
    a239, e239 = _arctan_inverse_fixed(239, scale)
    centre = 16 * a5 - 4 * a239
    error = 16 * e5 + 4 * e239
    lo = Fraction(centre - error, scale)
    hi = Fraction(centre + error, scale)
    if not hi - lo <= Fraction(1, 1 << bits):  # pragma: no cover - by the guard
        raise HypothesisError("the guard bits did not cover the error count")
    return lo, hi


def exact_angle(angle: Angle) -> Fraction | PiMultiple:
    """Return a declared angle as the exact number it denotes.

    A :class:`~certiqs_key.receiver.numerics.PiMultiple` is ``c pi``; any
    other declared value is the rational it denotes (a finite ``float`` is the
    dyadic rational it is; ``foundations/def:binary64`` (iii)).
    """
    if isinstance(angle, PiMultiple):
        return angle
    if isinstance(angle, bool):
        raise HypothesisError("a boolean is not an angle")
    if isinstance(angle, float) and not math.isfinite(angle):
        raise HypothesisError(f"a declared angle is finite, got {angle}")
    return Fraction(angle)


_EXACT_QUARTERS: Final[dict[int, tuple[int, int]]] = {
    # 2c mod 4 -> (cos, sin) at theta = c pi with 2c an integer.
    0: (1, 0),
    1: (0, 1),
    2: (-1, 0),
    3: (0, -1),
}


def _cos_sin_fixed(x: int, prec: int) -> tuple[int, int, int]:
    """Return ``(C, S, e)``: ``|cos(x/2^prec) 2^prec - C| <= e``, same for ``S``.

    ``x / 2^prec`` must satisfy ``|x| <= 4 * 2^prec``. The Taylor terms
    ``t_k = x^k / k!`` are formed in integer fixed point; ``e_k`` bounds the
    accumulated error of ``t_k`` (one unit for each floor division, and the
    previous error scaled by ``|x| / k``), and the loop stops when the next
    term's bound is below one unit, which then bounds the Lagrange remainder
    (every derivative of cos and sin is bounded by one). The loop stops once
    the computed term is at most one unit and the bound on the next term
    (from ``|t_k| + e_k``) is at most one unit; ``e_k`` never falls below the
    three units each step adds, so it cannot itself be the stopping test.
    """
    scale = 1 << prec
    if abs(x) > 4 * scale:
        raise HypothesisError("the fixed-point argument exceeds 4 in modulus")
    term = scale  # t_0 = 1
    term_error = 0
    cos_total, sin_total = scale, 0
    cos_error, sin_error = 0, 0
    k = 0
    magnitude = abs(x)
    while True:
        k += 1
        # t_k = t_{k-1} * x / k, with |error| <= previous * |x| / (scale k) + 2.
        nxt = (term * x) // scale
        nxt = nxt // k if nxt >= 0 else -((-nxt) // k)
        term_error = (term_error * magnitude) // (scale * k) + 3
        term = nxt
        bound = abs(term) + term_error
        if k % 2 == 0:
            sign = -1 if (k // 2) % 2 else 1
            cos_total += sign * term
            cos_error += term_error
        else:
            sign = -1 if ((k - 1) // 2) % 2 else 1
            sin_total += sign * term
            sin_error += term_error
        # The remainder after degree k is at most |x|^(k+1)/(k+1)! <= bound |x|/(k+1).
        tail = (bound * magnitude) // (scale * (k + 1)) + 1
        if abs(term) <= 1 and tail <= 1:
            return cos_total, sin_total, max(cos_error, sin_error) + 2 * tail + 2


def angle_enclosure(angle: Angle, bits: int = DEFAULT_BITS) -> tuple[Ball, Ball]:
    """Return an angle enclosure ``(cos theta, sin theta)``.

    Implements the angle enclosure of ``receiver/def:complex-enclosure``: a
    pair of complex enclosures with rational centres of ``cos theta`` and
    ``sin theta`` for ``theta`` given as a rational (radians) or as ``c pi``,
    both exact where ``theta = c pi`` with ``2c`` an integer (and so at
    ``0`` radians).

    The argument is reduced exactly where it is ``c pi`` (periodicity in
    ``2 pi``, ``c`` into ``(-1, 1]``); a rational argument is used as it is
    (declared angles lie in ``[0, 2 pi)``). The point of evaluation ``x_0``
    is a dyadic rational: ``c`` times a rational point inside the bounds of
    :func:`pi_bounds`, or the rational argument rounded to the fixed-point
    grid. With ``w`` a rational bound on ``|theta - x_0|``, cosine and sine
    being 1-Lipschitz, ``|cos theta - cos x_0| <= w``, and the radius is ``w``
    plus the counted error of the series at ``x_0``.
    """
    value = exact_angle(angle)
    if isinstance(value, PiMultiple):
        c = value.coefficient % 2
        if c > 1:
            c -= 2
        if (2 * c).denominator == 1:
            cos_v, sin_v = _EXACT_QUARTERS[int(2 * c) % 4]
            return Ball.exact(cos_v), Ball.exact(sin_v)
        lo, hi = pi_bounds(bits + 8)
        centre_point = c * (lo + hi) / 2
        spread = abs(c) * (hi - lo) / 2
    else:
        if value == 0:
            return Ball.exact(1), Ball.exact(0)
        centre_point = value
        spread = _ZERO
    prec = bits + 16
    scale = 1 << prec
    x = math.floor(centre_point * scale)
    x0 = Fraction(x, scale)
    width = spread + abs(centre_point - x0)
    if abs(x0) > 4:
        # Declared angles lie in [0, 2 pi); reduce a rational one by a rational
        # multiple of 2 pi with the bounds of pi, the error added to `width`.
        turns = math.floor(x0 / 2 / Fraction(355, 113) + Fraction(1, 2))
        lo, hi = pi_bounds(bits + 8)
        shifted = centre_point - 2 * turns * (lo + hi) / 2
        width = spread + abs(turns) * (hi - lo)
        x = math.floor(shifted * scale)
        x0 = Fraction(x, scale)
        width += abs(shifted - x0)
    cos_i, sin_i, error = _cos_sin_fixed(x, prec)
    radius = Fraction(error, scale) + width
    return Ball(Fraction(cos_i, scale), _ZERO, radius), Ball(
        Fraction(sin_i, scale), _ZERO, radius
    )
