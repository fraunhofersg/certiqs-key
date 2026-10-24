"""The spectral enclosure's ends are the EXACT extremes of its midpoints.

``foundations/cor:least-eigenvalue-over-enclosure`` (i) gives every eigenvalue
of every member in ``[lmin(diag lam) - e, lmax(diag lam) + e]``, the exact
extremes of ``lam``, and the :class:`~certiqs_key.foundations.balls.Spectral`
docstring promises that interval. ``lo`` feeds the floor that certifies a
compression is the support and the constants of
``foundations/lem:matrix-function-perturbation`` (i) and (iii)(b).

Choosing the ends with ``key=float`` would let two exact midpoints that round
to one binary64 number tie, and ``min``/``max`` would return the first of
them. For the order ``(1/2 + 2^-60, 1/2)`` that puts ``lo`` at ``1/2 + 2^-60``,
above the least eigenvalue ``1/2`` (and ``hi = 1/2`` below ``1/2 + 2^-60`` for
the other order). Both cases are tested.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

pytest.importorskip("flint")
from certiqs_key.foundations import balls
from certiqs_key.foundations.exact import Cx

pytestmark = pytest.mark.contract


def _cx(value: Fraction) -> Cx:
    return Cx(value, Fraction(0))


@pytest.mark.parametrize("first_larger", [True, False])
def test_the_spectral_interval_holds_the_exact_extremes_at_binary64_ties(
    first_larger: bool,
) -> None:
    small, large = Fraction(1, 2), Fraction(1, 2) + Fraction(1, 2**60)
    assert float(small) == float(large)  # the two tie under key=float
    diagonal = (large, small) if first_larger else (small, large)
    zero = _cx(Fraction(0))
    with balls.precision(128):
        sp = balls.spectral(
            balls.Ball.of([[_cx(diagonal[0]), zero], [zero, _cx(diagonal[1])]])
        )
        lowest = -balls.upper(-sp.lo)
        highest = balls.upper(sp.hi)
    # Every member's spectrum (here the exact matrix's: {1/2, 1/2 + 2^-60})
    # lies in [lo, hi].
    assert lowest <= small
    assert highest >= large
