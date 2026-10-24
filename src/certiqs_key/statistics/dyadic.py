"""The substrate: dyadic numbers with an explicit binary exponent, rounded.

Remark ``rem:local-evaluation``, "The substrate", states the rule the two
closed-form routes of ``binomial-box`` are built on, and
``binomial-box/interface.yaml`` raises it to a binding convention
(``conventions.the_substrate_rule``):

    "THE PRODUCTS INSIDE THE WINDOW ARE HELD AS DYADIC NUMBERS WITH AN EXPLICIT
    BINARY EXPONENT, rounded in the direction each bound requires -- down for
    the lower, up for the upper -- AND NOT AS EXACT RATIONALS, whose
    denominators would grow with the window ... An exact rational whose
    denominator is a power of the round count is NOT a number model for this
    route."

WHAT A DYADIC IS HERE, AND WHY IT IS STILL A ``Fraction``
========================================================
A dyadic is a :class:`~fractions.Fraction` whose denominator is a power of two,
carried at a bounded number of SIGNIFICANT bits. The explicit binary exponent
the convention asks for is that denominator: a value is ``m / 2^e`` with ``m``
of at most ``bits`` bits, so the representation never grows with the length of
the product that built it, which is the whole of what the rule forbids. Using
the standard-library type rather than a pair of integers keeps one arithmetic
in the module and lets an exact rational and a rounded one be compared without
a conversion; what makes it a substrate rather than an exact rational is that
EVERY OPERATION ROUNDS, in a named direction, through the two functions below.

SIGNIFICANT BITS, NOT ABSOLUTE ONES (see :mod:`certiqs_key.statistics.tails`,
``_shrink``): binomial mass points span
the whole representable range, and an absolute grid would round every one of
them to a bracket whose upper end, carried through a term recursion, grows past
one and bounds nothing.

RIGOROUS AT ANY PRECISION. ``upward=True`` returns a value at or above its
argument and ``upward=False`` one at or below it, always; the precision decides
only how wide the enclosure is, never whether it is one. That is why
``binomial-box/interface.yaml`` can declare the evaluation parameters NOT
thresholds: no value of any of them can make an endpoint less conservative
(``prop:bracketed-endpoints`` (i)).

THIS IS ``tails._shrink`` GENERALISED IN ONE ARGUMENT.
``tails._shrink`` rounds to a fixed 192 bits for the sweep's own internal
enclosure route; :func:`round_dyadic` is the same expression with the precision
passed in, and ``tails`` calls it. THE FROZEN 55 CASES ARE WHAT PINS THAT
IDENTITY: they run the sweep on that route.
"""

from __future__ import annotations

import math
from fractions import Fraction

__all__ = [
    "round_dyadic",
    "round_ratio",
]

_ZERO = Fraction(0)


def _exponent(numerator: int, denominator: int) -> int:
    """Return an integer ``e`` with ``2^e`` strictly above ``|num / den|``.

    From ``|num| < 2^bit_length(num)`` and ``den >= 2^(bit_length(den) - 1)``.
    """
    return numerator.bit_length() - denominator.bit_length() + 1


def round_dyadic(value: Fraction, bits: int, *, upward: bool) -> Fraction:
    """Return ``value`` rounded to ``bits`` significant bits, in one direction.

    ``upward`` returns a dyadic at or above ``value``, otherwise one at or
    below it. Zero is returned unchanged: it is exactly representable and has
    no significand to round.
    """
    if value == _ZERO:
        return value
    shift = bits - _exponent(value.numerator, value.denominator)
    if shift >= 0:
        scale = 1 << shift
        scaled = value * scale
        mantissa = math.ceil(scaled) if upward else math.floor(scaled)
        return Fraction(mantissa, scale)
    scale = 1 << -shift
    scaled = value / scale
    mantissa = math.ceil(scaled) if upward else math.floor(scaled)
    return Fraction(mantissa * scale)


def round_ratio(
    numerator: int, denominator: int, bits: int, *, upward: bool
) -> Fraction:
    """Return ``numerator / denominator`` as a directed dyadic, without a gcd.

    The same value :func:`round_dyadic` would return for
    ``Fraction(numerator, denominator)``, computed from the two integers so
    that the ratios of Eq. ``eq:pmf-ratio`` -- one per term of a window of up
    to a few thousand -- are never normalized into lowest terms on the way.
    ``denominator`` must be positive.
    """
    if denominator <= 0:
        raise ValueError(
            f"a dyadic rounding needs a positive denominator; got {denominator}"
        )
    if numerator == 0:
        return _ZERO
    shift = bits - _exponent(numerator, denominator)
    if shift >= 0:
        scaled_numerator = numerator << shift
        mantissa = (
            -((-scaled_numerator) // denominator)
            if upward
            else scaled_numerator // denominator
        )
        return Fraction(mantissa, 1 << shift)
    scale = 1 << -shift
    divisor = denominator * scale
    mantissa = -((-numerator) // divisor) if upward else numerator // divisor
    return Fraction(mantissa * scale)
