"""lem:log-enclosure and lem:stirling-enclosure: logarithms without a library.

Two lemmas of ``binomial-box`` and one inverse the interface needs, all of them
self-contained down to :func:`math.isqrt`. ``binomial-box/interface.yaml``
raises that to a binding convention
(``conventions.no_transcendental_dependency``): "NO LOGARITHM, EXPONENTIAL OR
SPECIAL FUNCTION OF ANY LIBRARY IS CALLED ON ANY PATH OF THIS SUBMODULE, and no
claim of it rests on one."

lem:log-enclosure -- THE ROOT BOUNDS
===================================
    m (1 - x^(-1/m))  <=  ln x  <=  m (x^(1/m) - 1)          (eq:log-root-bounds)

and, for rationals ``0 < l <= x^(1/m) <= u``,

    m (1 - 1/l)  <=  ln x  <=  m (u - 1)                 (eq:log-rational-bounds)

with ``l`` and ``u`` computed by ``j`` integer square roots at ``m = 2^j``
through

    isqrt(c d 4^s) / (d 2^s)  <=  sqrt(c/d)  <  (isqrt(c d 4^s) + 1) / (d 2^s)
                                                             (eq:isqrt-bounds)

THE WIDTH IS COMPUTABLE AT ANY PRESCRIBED VALUE, THE CALLER CHOOSING THE
PRECISIONS. ``lem:log-enclosure`` states the enclosure computable at any
prescribed width; both bounds are valid at every precision, so the width is
tightness and never soundness. :func:`log_bounds` therefore RETURNS THE WIDTH IT
ACHIEVED rather than assuming one, which is what
``binomial-box/interface.yaml`` asks of a conforming implementation
(``evaluation_parameters``, ``root_precision_bits``, its caveat).

ONE DEPARTURE FROM THE LEMMA'S ITERATION, AND IT IS A NARROWING. The proof
takes ``l_{i+1}`` from the lower bound of eq:isqrt-bounds applied to ``l_i``;
this file additionally ROUNDS ``l_{i+1}`` DOWN and ``u_{i+1}`` UP to
``precision`` significant bits after each step. A lower bound rounded down is a
lower bound, so the enclosure stays valid; what it buys is that the denominator
stays at ``2^precision`` instead of growing by ``2^s`` per step, which at
``j = 64`` is the difference between integers of a few hundred bits and
integers of several thousand.

lem:stirling-enclosure -- ROBBINS' BOUNDS AND WALLIS'S CONSTANT
===============================================================
    (m + 1/2) ln m - m + C + 1/(12m+1)  <  ln m!
                                        <  (m + 1/2) ln m - m + C + 1/(12m)

with ``C = ln(2 pi) / 2`` enclosed through the Wallis partial product
``P_M`` of eq:wallis-partial, ``4 P_M < 2 pi < 4 P_M (1 + 1/(2M))``.

SMALL FACTORIALS ARE NOT TAKEN THROUGH ROBBINS AT ALL. The gap between the two
Robbins bounds is ``1/(12m(12m+1))``, which is ``1/156`` at ``m = 1`` -- a
hundredth of a nat, enough to leave a bracket undecided at a small ``n`` where
the per-count decay is of order one. For ``m`` at or below
:data:`SMALL_FACTORIAL_MAX` the lemma's own alternative is used: the integer
``m!`` is held exactly and its logarithm is enclosed by the root bounds
(``lem:pmf-enclosure``, the parenthesis on ``F^-`` and ``F^+``), and
``F(0) = 0`` exactly.

THE INVERSE, AND WHY IT IS HERE
===============================
``binomial-box/interface.yaml``'s ``completeness_report`` asks the enclosure
routes to report "the two UPPER enclosures of the tails at the emitted
endpoints", and adds that "each upper enclosure is the same object the endpoint
decision used, so no new machinery and no second pass is needed". THE ENDPOINT
DECISION IS MADE IN LOG SPACE and a completeness figure is a number, so
something must turn a rational upper bound on ``ln tail`` into a rational upper
bound on ``tail``. :func:`exp_upper` is that step and it is NOT a new
dependency: it searches for a dyadic ``y`` whose LOWER root bound is at least
the given ``u``, and ``ln y >= log_bounds(y).lower >= u`` gives ``y >= e^u``.
The search is monotone, deterministic and bounded; it touches no emitted
endpoint, only the reported figure.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache

from certiqs_key.statistics.dyadic import round_dyadic

__all__ = [
    "SMALL_FACTORIAL_MAX",
    "LogBounds",
    "exp_upper",
    "isqrt_bounds",
    "log_bounds",
    "log_factorial_bounds",
    "root_bounds",
    "two_pi_bounds",
    "wallis_partial_product",
]

_ZERO = Fraction(0)
_ONE = Fraction(1)

#: The largest ``m`` whose ``ln m!`` is enclosed from the EXACT integer ``m!``
#: rather than through Robbins' bounds. Chosen so that the Robbins gap
#: ``1/(12m(12m+1))`` above it is below ``1.1e-7`` -- three orders of magnitude
#: under the Wallis contribution -- while ``m!`` stays an integer of a few
#: thousand bits, whose root bounds cost one large :func:`math.isqrt` and then
#: nothing (the first rounding brings it to ``precision`` bits).
SMALL_FACTORIAL_MAX = 256


@dataclass(frozen=True)
class LogBounds:
    """A rational enclosure ``lower <= ln x <= upper``, with the width achieved.

    ``width`` is ``upper - lower`` as an exact rational and is the quantity
    ``binomial-box/interface.yaml`` requires a conforming implementation to
    carry rather than assume (see the module docstring).
    """

    lower: Fraction
    upper: Fraction

    def __post_init__(self) -> None:
        """Refuse an enclosure that is not one."""
        if self.lower > self.upper:
            raise ValueError(
                f"a log enclosure must satisfy lower <= upper; got "
                f"[{self.lower}, {self.upper}]"
            )

    @property
    def width(self) -> Fraction:
        """Return the width the evaluation actually achieved."""
        return self.upper - self.lower


def isqrt_bounds(value: Fraction, precision: int) -> tuple[Fraction, Fraction]:
    """Return rationals bracketing ``sqrt(value)``, Eq. ``eq:isqrt-bounds``.

    For ``value = c/d > 0``, ``sqrt(value) = sqrt(c d 4^s) / (d 2^s)`` and the
    definition of :func:`math.isqrt` gives
    ``isqrt(N) <= sqrt(N) < isqrt(N) + 1``; the two bounds differ by
    ``1 / (d 2^s) <= 2^-s``.
    """
    if value < _ZERO:
        raise ValueError(f"a square root needs a non-negative argument; got {value}")
    if value == _ZERO:
        return _ZERO, _ZERO
    numerator, denominator = value.numerator, value.denominator
    scale = denominator << precision
    root = math.isqrt(numerator * denominator << (2 * precision))
    return Fraction(root, scale), Fraction(root + 1, scale)


def grid_up(value: Fraction, precision: int) -> int:
    """Return the least integer ``a`` with ``a / 2^precision >= value``."""
    return math.ceil(value * (1 << precision))


def grid_down(value: Fraction, precision: int) -> int:
    """Return the greatest integer ``a`` with ``a / 2^precision <= value``."""
    return math.floor(value * (1 << precision))


def grid_sqrt_up(mantissa: int, precision: int) -> int:
    """Return ``ceil(sqrt(mantissa / 2^s) * 2^s)``, on the grid ``2^-s Z``.

    ``sqrt(a / 2^s) * 2^s = sqrt(a * 2^s)``, so the ceiling is one integer
    square root and a test for a perfect square.
    """
    scaled = mantissa << precision
    root = math.isqrt(scaled)
    return root if root * root == scaled else root + 1


def grid_sqrt_down(mantissa: int, precision: int) -> int:
    """Return ``floor(sqrt(mantissa / 2^s) * 2^s)``, on the grid ``2^-s Z``."""
    return math.isqrt(mantissa << precision)


def root_bounds(
    value: Fraction, exponent: int, precision: int
) -> tuple[Fraction, Fraction]:
    """Return ``l <= value^(1/2^exponent) <= u`` for ``1 <= value <= 2``.

    The iteration of ``lem:log-enclosure``, run ENTIRELY ON THE FIXED DYADIC
    GRID ``2^-s Z``: the argument is snapped outward onto the grid once, and
    each of the ``j`` steps is one integer square root of a grid mantissa,
    rounded down for the lower chain and up for the upper.

    THE GRID IS WHAT MAKES THE RULE MONOTONE, and it is not a performance
    choice. Eq. ``eq:isqrt-bounds`` applied to a rational ``c/d`` has excess
    ``1/(d 2^s)``, WHICH DEPENDS ON THE DENOMINATOR, so the bare bound is not a
    monotone function of its argument: at ``s = 0`` and ``j = 1`` the budgets
    ``eps = 1/2`` and ``eps = 4/9`` give ``L = 2`` and ``L = 3/2``, the larger
    budget producing the larger ``L`` and hence the WIDER interval, which is
    exactly the inversion ``prop:rule-bernstein`` (ii) forbids. On the grid the
    denominator is the same for every argument, each step is
    ``a -> ceil(sqrt(a 2^s))`` or ``a -> isqrt(a 2^s)`` -- both non-decreasing
    in ``a`` -- and the snapping onto the grid is non-decreasing too, so the
    composite is monotone.

    THE RANGE IS THE CALLER'S OBLIGATION. :func:`log_bounds` splits off the
    binary exponent first, so every argument reaching here lies in ``[1, 2]``,
    where a grid of ``2^-s`` resolves the value and the lower chain cannot
    collapse onto zero.
    """
    if not _ONE <= value <= 2:
        raise ValueError(
            f"the root iteration is run on the normalized range [1, 2]; got "
            f"{value}. log_bounds splits off the binary exponent first"
        )
    lower = grid_down(value, precision)
    upper = grid_up(value, precision)
    for _ in range(exponent):
        lower = grid_sqrt_down(lower, precision)
        upper = grid_sqrt_up(upper, precision)
    scale = 1 << precision
    return Fraction(lower, scale), Fraction(upper, scale)


def _binary_exponent(value: Fraction) -> int:
    """Return the integer ``e`` with ``2^e <= value < 2^(e+1)``, for ``value > 0``."""
    guess = value.numerator.bit_length() - value.denominator.bit_length()
    while _power_of_two(guess) > value:
        guess -= 1
    while _power_of_two(guess + 1) <= value:
        guess += 1
    return guess


@lru_cache(maxsize=16)
def _log_two(exponent: int, precision: int) -> LogBounds:
    """Return the enclosure of ``ln 2``, the one argument taken undecomposed.

    Every other logarithm is ``e ln 2 + ln x'`` with ``x'`` in ``[1, 2)``, so
    this one cannot be, and it is the base of the decomposition rather than a
    special case of it. ``2`` is on the grid exactly and the chain from it
    stays inside ``[1, 2]``.
    """
    return _raw_log_bounds(Fraction(2), exponent, precision)


def _raw_log_bounds(value: Fraction, exponent: int, precision: int) -> LogBounds:
    """Return the root-bound enclosure of ``ln value`` for ``1 <= value <= 2``."""
    lower_root, upper_root = root_bounds(value, exponent, precision)
    scale = 1 << exponent
    lower = Fraction(
        grid_down(scale * (_ONE - _ONE / lower_root), precision), 1 << precision
    )
    upper = Fraction(
        grid_up(scale * (upper_root - _ONE), precision), 1 << precision
    )
    return LogBounds(lower, upper)


@lru_cache(maxsize=4096)
def log_bounds(value: Fraction, exponent: int, precision: int) -> LogBounds:
    """Return ``lower <= ln value <= upper``, Eq. ``eq:log-rational-bounds``.

    ``m (1 - 1/l) <= ln x <= m (u - 1)`` at ``m = 2^exponent``, with the
    argument split first: ``x = 2^e x'`` with ``x'`` in ``[1, 2)``, so that
    ``ln x = e ln 2 + ln x'`` and the root iteration runs where the grid of
    :func:`root_bounds` resolves it. THE SPLIT IS EXACT -- ``e`` is an integer
    and ``2^e`` a grid point -- and it is what makes the enclosure tight at
    every magnitude: without it a large ``x`` carries a slack of order
    ``(ln x)^2 / 2m``, which ``lem:pmf-enclosure`` then multiplies by ``3n``.

    IT IS ALSO MONOTONE, which is what ``prop:rule-bernstein`` (ii) needs of
    the evaluation. Inside one binary exponent both ends are monotone because
    the grid chain is; across a boundary the value just below
    ``2^(e+1)`` is bounded by the value just above it, because the chain's own
    enclosure of ``ln 2`` is exactly what the exponent term adds -- for the
    upper end, ``e L_up + chain_up(x') <= e L_up + chain_up(2) = (e+1) L_up``.
    """
    if value <= _ZERO:
        raise ValueError(f"a logarithm needs a positive argument; got {value}")
    if value == _ONE:
        # ln 1 = 0 exactly; eq:log-root-bounds has equality on both sides here
        # and the root iteration would spend j square roots to say so.
        return LogBounds(_ZERO, _ZERO)
    binary = _binary_exponent(value)
    mantissa = value / _power_of_two(binary)
    inner = _raw_log_bounds(mantissa, exponent, precision)
    if binary == 0:
        return inner
    two = _log_two(exponent, precision)
    # The exponent is exact, so each end takes the bound of ln 2 that its own
    # sign makes conservative.
    if binary > 0:
        return LogBounds(
            binary * two.lower + inner.lower, binary * two.upper + inner.upper
        )
    return LogBounds(
        binary * two.upper + inner.lower, binary * two.lower + inner.upper
    )


def _range_product(low: int, high: int) -> int:
    """Return the product of the integers in ``[low, high)``, by binary split.

    A plain left-to-right product of ``2M`` factors costs ``O(M^2)`` word
    operations because the accumulator grows; splitting the range keeps the
    operands of comparable size, which is what makes the Wallis product of
    :data:`wallis_partial_product` affordable at ``M`` in the thousands.
    """
    if low >= high:
        return 1
    if high - low == 1:
        return low
    middle = (low + high) // 2
    return _range_product(low, middle) * _range_product(middle, high)


@lru_cache(maxsize=8)
def wallis_partial_product(length: int) -> Fraction:
    """Return ``P_M`` of Eq. ``eq:wallis-partial``, EXACTLY.

    ``prod_{k=1}^{M} (2k)^2 / ((2k-1)(2k+1))``, assembled as one integer
    numerator over one integer denominator. ``binomial-box/interface.yaml``
    proposes accumulating it as a dyadic with directed rounding at every
    factor; an exact product with ONE directed rounding at the end (in
    :func:`two_pi_bounds`) is strictly tighter and, with the binary split
    above, cheaper. Cached because it depends on no input: it is a constant of
    the arithmetic and not of the request.
    """
    if length < 1:
        raise ValueError(f"Eq. eq:wallis-partial is stated for M >= 1; got {length}")
    evens = _range_product(1, length + 1) << length  # prod_{k=1}^{M} 2k = 2^M M!
    lower_odds = _odd_product(1, length)  # 1, 3, ..., 2M-1
    upper_odds = _odd_product(2, length + 1)  # 3, 5, ..., 2M+1
    return Fraction(evens * evens, lower_odds * upper_odds)


def _odd_product(first_index: int, last_index: int) -> int:
    """Return ``prod_{k=first_index}^{last_index} (2k - 1)``, by binary split."""
    if first_index > last_index:
        return 1
    if first_index == last_index:
        return 2 * first_index - 1
    middle = (first_index + last_index) // 2
    return _odd_product(first_index, middle) * _odd_product(middle + 1, last_index)


@lru_cache(maxsize=8)
def two_pi_bounds(length: int, exponent: int, precision: int) -> LogBounds:
    """Return rationals enclosing ``ln(2 pi)``, Eq. ``eq:wallis-bounds``.

    ``4 P_M < 2 pi < 4 P_M (1 + 1/(2M))``, then :func:`log_bounds` on the two
    rationals in the direction each end needs. Cached with its parameters for
    the same reason :func:`wallis_partial_product` is.
    """
    partial = wallis_partial_product(length)
    below = 4 * partial
    above = below * (1 + Fraction(1, 2 * length))
    return LogBounds(
        log_bounds(below, exponent, precision).lower,
        log_bounds(above, exponent, precision).upper,
    )


@lru_cache(maxsize=4096)
def log_factorial_bounds(
    value: int, exponent: int, precision: int, wallis_length: int
) -> LogBounds:
    """Return rationals enclosing ``ln value!``, ``lem:stirling-enclosure`` (iii).

    ``F(0) = F(1) = 0`` exactly. Up to :data:`SMALL_FACTORIAL_MAX` the integer
    ``value!`` is held exactly and :func:`log_bounds` encloses its logarithm,
    which is tighter than Robbins' bounds and is the alternative
    ``lem:pmf-enclosure`` names. Above it, Eq. ``eq:lnfact-enclosure``:
    ``(m + 1/2) lambda^mp - m + c^mp / 2`` plus the two Robbins remainders,
    each term taken in the direction its sign requires.
    """
    if value < 0:
        raise ValueError(f"a factorial needs a non-negative argument; got {value}")
    if value <= 1:
        return LogBounds(_ZERO, _ZERO)
    if value <= SMALL_FACTORIAL_MAX:
        return log_bounds(Fraction(math.factorial(value)), exponent, precision)
    log_value = log_bounds(Fraction(value), exponent, precision)
    constant = two_pi_bounds(wallis_length, exponent, precision)
    half = Fraction(2 * value + 1, 2)
    lower = (
        half * log_value.lower
        - value
        + constant.lower / 2
        + Fraction(1, 12 * value + 1)
    )
    upper = (
        half * log_value.upper - value + constant.upper / 2 + Fraction(1, 12 * value)
    )
    return LogBounds(
        round_dyadic(lower, precision, upward=False),
        round_dyadic(upper, precision, upward=True),
    )


#: A tail below ``2^-EXP_FLOOR_EXPONENT`` is reported as ``2^-EXP_FLOOR_EXPONENT``
#: by :func:`exp_upper`. That is an UPPER bound, so the reported completeness
#: figure stays admissible; what it buys is that the denominators of the
#: reported figure stay bounded when a guarded endpoint sits so far in the tail
#: that the true probability has no useful decimal at all.
EXP_FLOOR_EXPONENT = 4096


def exp_upper(
    value: Fraction, exponent: int, precision: int, mantissa_bits: int = 16
) -> Fraction:
    """Return a dyadic at or above ``e^value``, using :func:`log_bounds` only.

    ``ln y >= log_bounds(y).lower``, so any ``y`` with
    ``log_bounds(y).lower >= value`` satisfies ``y >= e^value``. The search is
    a power-of-two bracket followed by a bisection on ``mantissa_bits`` bits of
    significand, both monotone and both bounded; see the module docstring for
    why the inverse is needed at all and what it is not used for.
    """
    binary_log = log_bounds(Fraction(2), exponent, precision)
    guess = (
        math.ceil(value / binary_log.lower)
        if value >= _ZERO
        else math.ceil(value / binary_log.upper)
    )
    guess = max(guess, -EXP_FLOOR_EXPONENT)
    while log_bounds(_power_of_two(guess), exponent, precision).lower < value:
        guess += 1
    if guess <= -EXP_FLOOR_EXPONENT:
        return Fraction(1, 1 << EXP_FLOOR_EXPONENT)
    # Refine inside [2^(guess-1), 2^guess]: the smallest mantissa that still
    # certifies. `high` always certifies, `low` never does.
    scale = 1 << mantissa_bits
    low, high = scale // 2, scale
    while high - low > 1:
        middle = (low + high) // 2
        candidate = Fraction(middle, scale) * _power_of_two(guess)
        if log_bounds(candidate, exponent, precision).lower >= value:
            high = middle
        else:
            low = middle
    return Fraction(high, scale) * _power_of_two(guess)


def _power_of_two(exponent: int) -> Fraction:
    """Return ``2 ** exponent`` as a Fraction, for either sign of the exponent."""
    if exponent >= 0:
        return Fraction(1 << exponent)
    return Fraction(1, 1 << -exponent)
