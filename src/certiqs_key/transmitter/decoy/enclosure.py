"""The rational enclosure of the Poisson weights, formed here and nowhere else.

spec/modules/transmitter/decoy/: Lemma ``lem:poisson-enclosure`` and
Requirement ``req:sector-weight-bound``.

WHY IT IS FORMED IN THE MODULE. The obligation (T2) of ``def:tagged-source``,
``0 <= ptilde(n|mu) <= P_mu(n)``, has a right-hand side that is not a declared
number: at a positive binary64 intensity ``P_mu(n) = e^-mu mu^n/n!`` is
transcendental. The requirement has the engine form, from the declared ``mu``
and in exact rational arithmetic, the lower end of the lemma's enclosure and
decide the declared weight against it; it reads no enclosure from a request.
A declarer computes the same lower end with :func:`poisson_enclosures` and
declares at or below it.

THE INDEX IS FIXED BY ONE RULE. The lemma holds at every even ``K >= mu``; the
requirement fixes ``K = K_mu``, the least even ``K >= mu`` with
``t_{K+1} = mu^(K+1)/(K+1)! <= 2^-90``. By part (iv) of the lemma no smaller
admissible index gives a larger lower end, and by part (iii) the two ends
differ by at most ``2^-90 mu^n/n!``. ``K_mu`` is returned with the enclosure,
so that the emitted record can carry it per intensity.

NO FLOATING-POINT NUMBER ENTERS. ``mu`` is an exact rational (a declared
binary64 intensity is a dyadic rational), every ``t_k`` is formed as
``t_{k-1} mu / k``, and the ends are finite sums and products of them.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.errors import MalformedInputError

__all__ = [
    "POISSON_INDEX_THRESHOLD",
    "PoissonEnclosure",
    "PoissonEnclosureTable",
    "poisson_enclosures",
    "poisson_index",
]

#: ``2^-90``: the bound on ``t_{K+1}`` that fixes the summation index ``K_mu``
#: of ``req:sector-weight-bound``.
POISSON_INDEX_THRESHOLD: Final[Fraction] = Fraction(1, 1 << 90)


@dataclass(frozen=True)
class PoissonEnclosure:
    """``[max(0, S_{K+1}) t_n, S_K t_n]``, the enclosure of ``P_mu(n)``.

    ``lem:poisson-enclosure`` (i): ``lower <= P_mu(n) <= upper``. The weight
    obligation of (T2) is decided against :attr:`lower`, which is what makes
    ``ptilde <= P_mu(n)`` follow; :attr:`upper` decides nothing and is carried
    so that a record says what the enclosure was.
    """

    lower: Fraction
    upper: Fraction


@dataclass(frozen=True)
class PoissonEnclosureTable:
    """The enclosures of ``P_mu(n)`` for ``0 <= n <= cutoff`` at one intensity.

    ``index`` is ``K_mu`` of ``req:sector-weight-bound``; ``enclosures[n]`` is
    the enclosure of ``P_mu(n)`` at that index.
    """

    intensity: Fraction
    index: int
    enclosures: tuple[PoissonEnclosure, ...]


def _intensity(mu: object) -> Fraction:
    """Return ``mu`` as a rational, refusing one the lemma is not stated for."""
    if isinstance(mu, bool) or not isinstance(mu, Fraction | int) or mu < 0:
        raise MalformedInputError(
            "lem:poisson-enclosure is stated for a rational intensity mu >= 0; "
            f"this one is {mu!r}"
        )
    return Fraction(mu)


def _cutoff(cutoff: object) -> int:
    """Return ``cutoff``, refusing one that is not a non-negative integer."""
    if isinstance(cutoff, bool) or not isinstance(cutoff, int) or cutoff < 0:
        raise MalformedInputError(
            f"the source cutoff is a non-negative integer; this one is {cutoff!r}"
        )
    return cutoff


def poisson_index(mu: Fraction) -> int:
    """Return ``K_mu``: the least even ``K >= mu`` with ``t_{K+1} <= 2^-90``.

    ``req:sector-weight-bound``. It exists because ``t_k -> 0``
    (``lem:poisson-enclosure`` (iii)). At ``mu = 0`` it is ``0``, where
    ``t_1 = 0``.
    """
    mu = _intensity(mu)
    term = Fraction(1)
    k = 0
    while True:
        following = term * mu / (k + 1)
        if k % 2 == 0 and k >= mu and following <= POISSON_INDEX_THRESHOLD:
            return k
        k += 1
        term = following


def poisson_enclosures(mu: Fraction, cutoff: int) -> PoissonEnclosureTable:
    """Return the enclosures of ``P_mu(n)``, ``n <= cutoff``, at the index ``K_mu``.

    ``lem:poisson-enclosure`` at ``K = K_mu`` (:func:`poisson_index`): with
    ``t_k = mu^k/k!`` and ``S_K = sum_{k <= K} (-1)^k t_k``, the enclosure of
    ``P_mu(n)`` is ``[max(0, S_{K+1}) t_n, S_K t_n]``. Every number is an exact
    rational. At ``mu = 0`` the index is ``0`` and the enclosure is exact:
    ``[1, 1]`` at ``n = 0`` and ``[0, 0]`` above (part (iii)).
    """
    mu = _intensity(mu)
    cutoff = _cutoff(cutoff)
    index = poisson_index(mu)
    term = Fraction(1)
    upper_sum = Fraction(1)
    for k in range(1, index + 1):
        term = term * mu / k
        upper_sum += term if k % 2 == 0 else -term
    following = term * mu / (index + 1)
    lower_sum = max(Fraction(0), upper_sum - following)
    enclosures: list[PoissonEnclosure] = []
    factor = Fraction(1)
    for n in range(cutoff + 1):
        if n:
            factor = factor * mu / n
        enclosures.append(PoissonEnclosure(lower_sum * factor, upper_sum * factor))
    return PoissonEnclosureTable(
        intensity=mu, index=index, enclosures=tuple(enclosures)
    )
