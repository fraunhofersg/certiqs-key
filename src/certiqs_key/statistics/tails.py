"""thm:binomial-tails -- the binomial tails, and the incomplete-beta form they equal.

Theorem ``thm:binomial-tails`` proves

    Pr[N >= k] = I_p(k, n - k + 1)  and  Pr[N <= k] = I_{1-p}(n - k, k + 1) ,

with ``I_x(a, b)`` the regularized incomplete beta function of Eq. ``eq:ireg``,
together with the boundary values ``Pr[N >= k] = 1`` for ``k <= 0``,
``Pr[N >= k] = 0`` for ``k > n``, ``Pr[N <= k] = 0`` for ``k < 0`` and
``Pr[N <= k] = 1`` for ``k >= n``. Corollary ``cor:tail-forms`` fixes the two
shapes the rest of the contract uses,

    Pr[N < k] = Pr[N <= k-1]   and   Pr[N > k] = Pr[N >= k+1] ,

and Definition ``def:conservative-evaluation`` allows either route, summing the
probability mass function or evaluating the integral, as long as the evaluation
is conservative; Lemma ``lem:exact-strict-tails`` proves the summed route exact
at rational p and equal to the closed forms. BOTH ROUTES ARE IMPLEMENTED HERE, and
they are independent:
:func:`binomial_cdf` sums, :func:`regularized_incomplete_beta` integrates the
polynomial exactly. Their agreement is Theorem ``thm:binomial-tails`` itself and is what
the thm:binomial-tails tests assert.

TWO EVALUATION PATHS, AND THE ONE DIRECTION A CONSERVATIVE EVALUATION ALLOWS
============================================================================
At rational ``p`` every tail is an exact rational, and where the exact value is
affordable this module computes it: :class:`TailBound` then carries
``exact = True`` and a single number. The exact route is NOT affordable in
general -- ``(1 - 10^-9)^(10^6)``, the value the frozen guard case
``GUARD-fine-alphabet-million-rounds`` turns on, is a rational with roughly
10^7 digits, and the frozen registry deliberately does not write it down -- so
above :data:`EXACT_TAIL_BIT_BUDGET` the tails are computed as RIGOROUS
ENCLOSURES in dyadic arithmetic with directed rounding.

An enclosure is not an approximation of the decision. A comparison against a
budget is made against the enclosure's UPPER bound and only against it
(:func:`within_budget`), which is exactly what ``def:conservative-evaluation``
asks: every tail comparison an endpoint rule makes (for the exact rule, those
of Definition ``def:interval``) "is decided either exactly or against a bound
that rounds the tail upward". An over-estimated tail makes fewer counts
admissible in Eqs. ``eq:kappaminus`` and ``eq:kappaplus``, so ``kappa^-`` can
only fall and ``kappa^+`` can only rise -- the enlargement Proposition
``prop:rule-exact`` (vii) proves an admissible endpoint rule, monotone in the
allocation, and the direction ``binomial-box/lem:widening`` proves safe: it
costs rate, never soundness. The two exact boundary values ``Pr[N < 0] = 0`` and
``Pr[N > n] = 0`` are never enclosed, which is what keeps both sets of Proposition
``prop:rule-exact`` (i) non-empty on either path.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.statistics.dyadic import round_dyadic

__all__ = [
    "BOUNDED_TAIL_PRECISION",
    "EXACT_TAIL_BIT_BUDGET",
    "TailBound",
    "binomial_cdf",
    "binomial_pmf",
    "cumulative_stream",
    "exact_tails_available",
    "lower_tail",
    "regularized_incomplete_beta",
    "upper_tail",
    "within_budget",
]

#: The exact route is taken while ``n * bit_length(denominator of p)`` stays at
#: or below this many bits. The quantity is the size of the common denominator
#: ``b^n`` of every mass point, and it also bounds the work of a full sweep, so
#: one budget guards both. It is a COST threshold and nothing else: neither
#: path may report a tail smaller than the truth, so no claim of the contract
#: depends on where it is set.
EXACT_TAIL_BIT_BUDGET = 4096

#: Significant bits kept by the enclosure route. Every operation rounds its
#: lower bound down and its upper bound up, so the enclosure is rigorous at any
#: precision; the precision only decides how often a comparison is too close to
#: call, and a comparison too close to call is resolved conservatively.
BOUNDED_TAIL_PRECISION = 192

_ZERO = Fraction(0)
_ONE = Fraction(1)


@dataclass(frozen=True)
class TailBound:
    """A rigorous enclosure ``[lower, upper]`` of one tail probability.

    ``exact`` is ``True`` exactly when the two ends coincide AND the common
    value is the tail itself rather than a bracket that happened to close.
    """

    lower: Fraction
    upper: Fraction
    exact: bool

    def __post_init__(self) -> None:
        """Refuse an enclosure that is not one."""
        if self.lower > self.upper:
            raise ValueError(
                f"a tail enclosure must satisfy lower <= upper; got "
                f"[{self.lower}, {self.upper}]"
            )
        if self.exact and self.lower != self.upper:
            raise ValueError(
                "an exact tail enclosure must be a single number; got "
                f"[{self.lower}, {self.upper}]"
            )

    @property
    def value(self) -> Fraction:
        """Return the exact tail; raise when only an enclosure is available."""
        if not self.exact:
            raise ValueError(
                "this tail was evaluated as an enclosure, not exactly; read "
                "`upper` for the bound a conservative evaluation "
                "(statistics/def:conservative-evaluation) decides against, and "
                "`exact` to test which route produced it"
            )
        return self.lower


def within_budget(tail: TailBound, budget: Fraction) -> bool:
    """Return whether ``tail <= budget`` is ESTABLISHED, deciding conservatively.

    The single comparison Definition ``def:interval`` performs, made against the
    enclosure's upper bound alone. On the exact route that is the tail itself,
    so the verdict is the contract's verbatim. On the enclosure route an
    undecided comparison returns ``False``, which is the upward-rounded tail of
    a conservative evaluation (``def:conservative-evaluation``): the count is
    treated as inadmissible, ``kappa^-`` falls, ``kappa^+`` rises, and the
    emitted interval only ever grows.
    """
    return tail.upper <= budget


def _parts(honest: Fraction) -> tuple[int, int, int]:
    """Return ``(a, b, b - a)`` for ``p = a / b`` in lowest terms."""
    return honest.numerator, honest.denominator, honest.denominator - honest.numerator


def exact_tails_available(rounds: int, honest: Fraction) -> bool:
    """Return whether the exact route is taken for this ``(n, p)``.

    Degenerate ``p`` is always exact: Proposition ``prop:rule-exact`` (v) makes
    both tails ``0`` or ``1`` with no arithmetic at all.
    """
    if honest in (_ZERO, _ONE):
        return True
    return rounds * honest.denominator.bit_length() <= EXACT_TAIL_BIT_BUDGET


def binomial_pmf(rounds: int, honest: Fraction, count: int) -> Fraction:
    """Return ``Pr[N = count]`` exactly, for ``N`` binomial ``(n, p)``.

    Unconditionally exact, and unconditionally as expensive as that is: the
    value has denominator ``b^n``. The tail engine below does not call it in a
    loop; it is the direct form, used where a single mass point is wanted and
    by the tests that read the frozen probability-mass tables.
    """
    if count < 0 or count > rounds:
        return _ZERO
    return (
        Fraction(math.comb(rounds, count))
        * honest**count
        * (_ONE - honest) ** (rounds - count)
    )


def cumulative_stream(rounds: int, honest: Fraction) -> Iterator[TailBound]:
    """Yield ``Pr[N <= i]`` for ``i = 0, 1, ..., n``, in one pass.

    One pass is what makes the endpoint search of Definition ``def:interval``
    affordable: ``Pr[N < k]`` and ``Pr[N > k]`` are both read off the same
    running sum, so the two extrema of Eqs. ``eq:kappaminus`` and
    ``eq:kappaplus`` cost one sweep between them rather than one sweep each.
    """
    if honest == _ZERO:
        # N = 0 with probability one (Proposition prop:rule-exact (v)).
        for _ in range(rounds + 1):
            yield TailBound(_ONE, _ONE, exact=True)
        return
    if honest == _ONE:
        # N = n with probability one.
        for index in range(rounds + 1):
            value = _ONE if index == rounds else _ZERO
            yield TailBound(value, value, exact=True)
        return
    if exact_tails_available(rounds, honest):
        yield from _exact_stream(rounds, honest)
        return
    yield from _bounded_stream(rounds, honest)


def _exact_stream(rounds: int, honest: Fraction) -> Iterator[TailBound]:
    """Yield the exact ``Pr[N <= i]``, as integers over the denominator ``b^n``.

    The mass points share the denominator ``b^n``, so the sweep is integer
    arithmetic: with ``term_i = C(n,i) a^i c^{n-i}`` and ``c = b - a``,

        term_{i+1} = term_i * (n - i) * a / ((i + 1) * c) ,

    an exact integer quotient -- ``C(n,i) (n-i) / (i+1) = C(n,i+1)`` is an
    integer and ``c^{n-i}`` has a factor ``c`` to give up.
    """
    numerator, denominator, complement = _parts(honest)
    scale = denominator**rounds
    term = complement**rounds
    total = term
    yield TailBound(Fraction(total, scale), Fraction(total, scale), exact=True)
    for index in range(rounds):
        term = (term * (rounds - index) * numerator) // ((index + 1) * complement)
        total += term
        value = Fraction(total, scale)
        yield TailBound(value, value, exact=True)


def _bounded_stream(rounds: int, honest: Fraction) -> Iterator[TailBound]:
    """Yield rigorous enclosures of ``Pr[N <= i]`` in dyadic arithmetic.

    Same recursion as :func:`_exact_stream`, with every product rounded
    outward and the running sum clamped at one -- a cumulative distribution
    function never exceeds it, so the clamp is a fact and not a repair.
    """
    numerator, _, complement = _parts(honest)
    term_low, term_high = _power(_ONE - honest, rounds)
    total_low, total_high = term_low, term_high
    yield TailBound(total_low, min(total_high, _ONE), exact=False)
    for index in range(rounds):
        ratio = Fraction((rounds - index) * numerator, (index + 1) * complement)
        term_low = _shrink(term_low * _shrink(ratio, upward=False), upward=False)
        term_high = _shrink(term_high * _shrink(ratio, upward=True), upward=True)
        total_low = _shrink(total_low + term_low, upward=False)
        total_high = _shrink(total_high + term_high, upward=True)
        yield TailBound(total_low, min(total_high, _ONE), exact=False)


def binomial_cdf(rounds: int, honest: Fraction, count: int) -> TailBound:
    """Return ``Pr[N <= count]``, with the boundary values of Theorem ``thm:binomial-tails``."""  # noqa: E501
    if count < 0:
        return TailBound(_ZERO, _ZERO, exact=True)
    if count >= rounds:
        return TailBound(_ONE, _ONE, exact=True)
    stream = cumulative_stream(rounds, honest)
    bound = TailBound(_ZERO, _ZERO, exact=True)
    for index, item in enumerate(stream):
        bound = item
        if index == count:
            break
    return bound


def lower_tail(rounds: int, honest: Fraction, count: int) -> TailBound:
    """Return ``Pr[N < count]``, the first form of Eq. ``eq:tails-used``.

    ``Pr[N < 0] = 0`` EXACTLY on both evaluation routes. That value is what
    makes ``k = 0`` admissible in Eq. ``eq:kappaminus`` for every budget, which
    is the whole of Proposition ``prop:rule-exact`` (i) on the lower side, so it
    must not be an enclosure that a conservative comparison could reject.
    """
    if count <= 0:
        return TailBound(_ZERO, _ZERO, exact=True)
    return binomial_cdf(rounds, honest, count - 1)


def upper_tail(rounds: int, honest: Fraction, count: int) -> TailBound:
    """Return ``Pr[N > count]``, the second form of Eq. ``eq:tails-used``.

    ``Pr[N > n] = 0`` EXACTLY, for the mirror reason: it is what makes ``k = n``
    admissible in Eq. ``eq:kappaplus`` for every budget.
    """
    if count >= rounds:
        return TailBound(_ZERO, _ZERO, exact=True)
    if count < 0:
        return TailBound(_ONE, _ONE, exact=True)
    below = binomial_cdf(rounds, honest, count)
    return TailBound(
        max(_ZERO, _ONE - below.upper), _ONE - below.lower, exact=below.exact
    )


def regularized_incomplete_beta(
    argument: Fraction, first: int, second: int
) -> Fraction:
    """Return ``I_x(a, b)`` exactly, for integer ``a, b >= 1`` and rational ``x``.

    Eq. ``eq:ireg`` evaluated as what it is at integer parameters: a polynomial
    integral. Expanding ``(1-t)^{b-1}`` and integrating term by term,

        int_0^x t^{a-1} (1-t)^{b-1} dt
            = sum_{i=0}^{b-1} C(b-1, i) (-1)^i x^{a+i} / (a+i) ,

    and the normalizing integral is ``B(a, b) = (a-1)! (b-1)! / (a+b-1)!``,
    which the proof of Theorem ``thm:binomial-tails`` obtains from ``G(1) = 1`` rather
    than from a table -- so nothing here appeals to a tabulated identity
    either.

    THIS ROUTE SHARES NO STEP WITH :func:`binomial_cdf`. Their agreement is
    Theorem ``thm:binomial-tails``, and it is asserted rather than assumed.
    """
    if first < 1 or second < 1:
        raise ValueError(
            f"Eq. eq:ireg is stated for a, b >= 1; got a = {first}, b = {second}"
        )
    if not _ZERO <= argument <= _ONE:
        raise ValueError(f"Eq. eq:ireg is stated for x in [0, 1]; got x = {argument}")
    integral = sum(
        (
            Fraction((-1) ** index * math.comb(second - 1, index), first + index)
            * argument ** (first + index)
            for index in range(second)
        ),
        _ZERO,
    )
    normalizer = Fraction(
        math.factorial(first - 1) * math.factorial(second - 1),
        math.factorial(first + second - 1),
    )
    return integral / normalizer


# ---------------------------------------------------------------------------
#  Dyadic directed rounding. Rigorous at any precision; see the module
#  docstring for why an enclosure is not an approximation of the decision.
# ---------------------------------------------------------------------------


def _shrink(value: Fraction, *, upward: bool) -> Fraction:
    """Round a non-negative rational to :data:`BOUNDED_TAIL_PRECISION` bits.

    Significant bits, not absolute ones. Binomial mass points span the whole
    representable range -- ``(1-p)^n`` is astronomically small wherever the
    exact route is unaffordable -- and an absolute grid would round every one
    of them to a bracket ``[0, 2^-precision]`` whose upper end, carried through
    the term recursion, grows past one and bounds nothing.

    THE EXPRESSION LIVES IN :mod:`certiqs_key.statistics.dyadic`: the local evaluation
    of ``prop:bracketed-endpoints`` needs the same directed rounding at other
    precisions, and one substrate with a precision argument is one place a
    direction could be inverted instead of two. This route's precision is
    unchanged and the frozen 55 cases are what pins the identity.
    """
    return round_dyadic(value, BOUNDED_TAIL_PRECISION, upward=upward)


def _power(base: Fraction, exponent: int) -> tuple[Fraction, Fraction]:
    """Return a rigorous ``[low, high]`` for ``base ** exponent``, ``base >= 0``."""
    low, high = _ONE, _ONE
    factor_low, factor_high = _shrink(base, upward=False), _shrink(base, upward=True)
    remaining = exponent
    while remaining:
        if remaining & 1:
            low = _shrink(low * factor_low, upward=False)
            high = _shrink(high * factor_high, upward=True)
        remaining >>= 1
        if remaining:
            factor_low = _shrink(factor_low * factor_low, upward=False)
            factor_high = _shrink(factor_high * factor_high, upward=True)
    return low, high
