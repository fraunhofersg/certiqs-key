"""``poisson_enclosures`` encloses the Poisson weights over a document's whole domain.

WHY THIS TEST EXISTS. The function is ``transmitter/decoy/lem:poisson-enclosure``
at the index ``K_mu`` of ``req:sector-weight-bound``
(:mod:`certiqs_key.transmitter.decoy.enclosure`): the emission forms with it the
enclosure against which it decides the weight inequality (T2) of a tagged WCP
source, and the instance preparation declares each weight at or below its lower
end. The decoy template reaches it at its three default intensities and its
source cutoff; a ``wcp_decoy`` document widens its input to every ``mu`` and
``source_cutoff``
the document layer admits -- ``mu <= MAX_INTENSITY`` (10) and ``source_cutoff
<= MAX_SOURCE_CUTOFF`` (100) of :mod:`instances.declared.limits` -- so it is
held, over exactly that domain, against an independent evaluation of ``exp(-mu)
mu^n / n!`` in 80-digit ``decimal`` arithmetic: for every ``n <= cutoff``,
``lower <= P <= upper``.

The independent value carries a relative error far below ``10^-70``, while
the enclosure's own gap is ``2^-90`` relative at most, so the comparison
allows a relative slack of ``10^-70`` on each side and nothing more.
``mu`` is drawn both as a rational with a small denominator and as a binary64
number, which is what the ``wcp_decoy`` lowering passes
(``Fraction(float(exact_input(mu)))``).
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction

from hypothesis import given, settings
from hypothesis import strategies as st
from instances.declared.limits import MAX_INTENSITY, MAX_SOURCE_CUTOFF

from certiqs_key.transmitter.decoy import (
    POISSON_INDEX_THRESHOLD,
    poisson_enclosures,
    poisson_index,
)

_SLACK = Decimal("1e-70")

_RATIONAL_MU = st.builds(
    Fraction,
    st.integers(min_value=0, max_value=10_000),
    st.integers(min_value=1, max_value=1_000),
).filter(lambda mu: mu <= MAX_INTENSITY)
_BINARY64_MU = st.floats(
    min_value=0.0, max_value=float(MAX_INTENSITY), allow_nan=False, allow_infinity=False
).map(Fraction)
_CUTOFF = st.integers(min_value=0, max_value=MAX_SOURCE_CUTOFF)


def _poisson(mu: Fraction, n: int) -> Decimal:
    """Return ``exp(-mu) mu^n / n!`` at 80 significant digits."""
    with localcontext() as context:
        context.prec = 80
        value = Decimal(mu.numerator) / Decimal(mu.denominator)
        term = (-value).exp()
        for k in range(1, n + 1):
            term = term * value / k
        return term


def _holds(mu: Fraction, cutoff: int) -> None:
    enclosures = poisson_enclosures(mu, cutoff).enclosures
    assert len(enclosures) == cutoff + 1
    with localcontext() as context:
        context.prec = 90
        for n, enclosure in enumerate(enclosures):
            target = _poisson(mu, n)
            lower = Decimal(enclosure.lower.numerator) / Decimal(
                enclosure.lower.denominator
            )
            upper = Decimal(enclosure.upper.numerator) / Decimal(
                enclosure.upper.denominator
            )
            assert 0 <= enclosure.lower <= enclosure.upper, (mu, n)
            assert lower <= target * (1 + _SLACK), (mu, n, lower, target)
            assert target * (1 - _SLACK) <= upper, (mu, n, target, upper)


@settings(max_examples=60, deadline=None)
@given(mu=_RATIONAL_MU, cutoff=_CUTOFF)
def test_the_enclosure_holds_at_rational_intensities(mu: Fraction, cutoff: int) -> None:
    _holds(mu, cutoff)


@settings(max_examples=60, deadline=None)
@given(mu=_BINARY64_MU, cutoff=_CUTOFF)
def test_the_enclosure_holds_at_binary64_intensities(mu: Fraction, cutoff: int) -> None:
    _holds(mu, cutoff)


def test_the_enclosure_is_exact_at_zero_and_holds_at_the_ends() -> None:
    """At ``mu = 0`` the law is exact, zeros included; the domain's corners hold."""
    exact = poisson_enclosures(Fraction(0), 3)
    assert exact.index == 0
    assert [(e.lower, e.upper) for e in exact.enclosures] == [
        (1, 1),
        (0, 0),
        (0, 0),
        (0, 0),
    ]
    _holds(Fraction(MAX_INTENSITY), MAX_SOURCE_CUTOFF)
    _holds(Fraction(1, 10**6), MAX_SOURCE_CUTOFF)
    _holds(Fraction(1, 10**6), 0)


def _term(mu: Fraction, k: int) -> Fraction:
    """Return ``t_k = mu^k / k!``, formed here independently of the module."""
    value = Fraction(1)
    for j in range(1, k + 1):
        value = value * mu / j
    return value


def _partial_sum(mu: Fraction, upto: int) -> Fraction:
    """Return ``S_K = sum_{k <= K} (-1)^k t_k`` of ``eq:expsum``."""
    return sum(((-1) ** k * _term(mu, k) for k in range(upto + 1)), Fraction(0))


def _admissible(mu: Fraction, index: int) -> bool:
    """Whether ``K`` meets the rule's three conditions: even, ``>= mu``, small tail."""
    return (
        index % 2 == 0
        and index >= mu
        and _term(mu, index + 1) <= POISSON_INDEX_THRESHOLD
    )


@settings(max_examples=60, deadline=None)
@given(mu=_BINARY64_MU)
def test_the_rules_index_is_the_least_admissible_one(mu: Fraction) -> None:
    """``req:sector-weight-bound``: ``K_mu`` is the least admissible index.

    The least even ``K >= mu`` with ``t_{K+1} <= 2^-90``, and the enclosure is
    formed at it. Every even index below it fails one of the conditions, it
    meets all three, and the returned ends are ``max(0, S_{K+1}) t_n`` and
    ``S_K t_n`` at that index, re-formed here from the partial sums.
    """
    index = poisson_index(mu)
    assert _admissible(mu, index)
    for smaller in range(0, index, 2):
        assert not _admissible(mu, smaller), (mu, smaller)
    table = poisson_enclosures(mu, 3)
    assert table.index == index
    upper = _partial_sum(mu, index)
    lower = max(Fraction(0), _partial_sum(mu, index + 1))
    for n, enclosure in enumerate(table.enclosures):
        assert enclosure.lower == lower * _term(mu, n)
        assert enclosure.upper == upper * _term(mu, n)


@settings(max_examples=40, deadline=None)
@given(mu=_RATIONAL_MU.filter(lambda mu: mu <= 4))
def test_the_ends_are_monotone_over_the_admissible_even_indices(
    mu: Fraction,
) -> None:
    """``lem:poisson-enclosure`` (iv): the ends are monotone in ``K``.

    Over even ``K >= mu`` the lower end does not decrease and the upper end does
    not increase, so no smaller admissible index gives a larger lower end than
    the rule's.
    """
    start = int(mu) + (int(mu) % 2)
    if start < mu:
        start += 2
    lowers = []
    uppers = []
    for index in range(start, start + 12, 2):
        lowers.append(max(Fraction(0), _partial_sum(mu, index + 1)))
        uppers.append(_partial_sum(mu, index))
    assert lowers == sorted(lowers)
    assert uppers == sorted(uppers, reverse=True)
