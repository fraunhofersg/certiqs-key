"""The cross-check of a block's two enclosures, where the other tests do not reach.

``meat-core/frank-wolfe/req:certified-evaluation`` (iv)(c): a block's two
enclosures are inconsistent where the enclosure of ``L W L^dagger`` and the
block's entrywise enclosure are disjoint AT SOME ENTRY. The cross-check runs
WHEREVER the compilation carries a factor enclosure, WHICHEVER rule fixes the
block's rank, and also where neither does. In ``test_certified_factor_rule.py``
every disjoint entry is a diagonal one that differs in modulus, and the
disjointness is reached only where some rule decides. These cases cover the
rest:

* an off-diagonal entry that differs from the entrywise one in phase alone
  (the transpose of the block, as a missing conjugation in a carrier would
  give);
* a factor enclosure whose columns are dependent, so that the factor rule
  decides nothing, and whose members are disjoint from the entrywise
  enclosure.
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction as F

import pytest

pytest.importorskip("flint")

from certiqs_key.foundations import balls
from certiqs_key.foundations.exact import Cx, Matrix
from certiqs_key.foundations.reference import FactorEnclosure
from certiqs_key.solvers.frank_wolfe import certified
from certiqs_key.solvers.frank_wolfe.certified_record import (
    FACTOR_ENCLOSURE_INCONSISTENT,
)

pytestmark = pytest.mark.contract

ZERO = F(0)
TINY = F(1, 2**100)
HALF = F(1, 2)


def _inconsistent(
    centre: Matrix, radii: Sequence[Sequence[F]], factor: FactorEnclosure
) -> str:
    with balls.precision(128), pytest.raises(certified._Fail) as caught:
        certified._companion_element(centre, radii, factor, "block")
    assert caught.value.reason == FACTOR_ENCLOSURE_INCONSISTENT
    return str(caught.value)


def test_a_phase_only_off_diagonal_disagreement_is_inconsistent() -> None:
    """Members ``c c^dagger / 2``, ``c = (1, i)``; the entrywise block its transpose.

    ``L W L^dagger = [[1/2, -i/2], [i/2, 1/2]]`` exactly (radius 0), the
    entrywise centre ``[[1/2, i/2], [-i/2, 1/2]]`` with radius ``2^-100``:
    every entry has the same modulus, the diagonal agrees, and entry (0, 1)
    lies at distance 1 from the disc. Both rules decide the block not zero.
    """
    factor = FactorEnclosure(
        ((Cx(F(1), ZERO),), (Cx(ZERO, F(1)),)), ((ZERO,), (ZERO,)), (HALF,)
    )
    centre = (
        (Cx(HALF, ZERO), Cx(ZERO, HALF)),
        (Cx(ZERO, -HALF), Cx(HALF, ZERO)),
    )
    radii = ((TINY, TINY), (TINY, TINY))
    assert "disjoint at entry (0, 1)" in _inconsistent(centre, radii, factor)


def test_a_factor_that_decides_nothing_is_still_cross_checked() -> None:
    """Two equal columns ``(1, 0)``: no Gram floor, members ``diag(2, 0)``.

    The entrywise enclosure is ``diag(1, 0)`` with radius ``2^-100``; the
    factor rule decides nothing (dependent columns), the entrywise rule fixes
    no rank, and entry (0, 0) is disjoint: inconsistent all the same.
    """
    one = Cx(F(1), ZERO)
    nil = Cx(ZERO, ZERO)
    factor = FactorEnclosure(
        ((one, one), (nil, nil)), ((ZERO, ZERO), (ZERO, ZERO)), (F(1), F(1))
    )
    assert certified._factor_rule(factor) == (None, None)
    centre = ((one, nil), (nil, nil))
    radii = ((TINY, TINY), (TINY, TINY))
    assert "disjoint at entry (0, 0)" in _inconsistent(centre, radii, factor)
