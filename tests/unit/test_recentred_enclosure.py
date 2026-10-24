"""``foundations/lem:recentred-enclosure``: recentring an enclosure at zero.

The direct route evaluates its first-order bound at the centres of the handed
reference (``meat-core/frank-wolfe/req:bracket-on-reference``), and
``reductions/req:reference-companion`` (i) recentres every handed block, and
the companion's datum, by this lemma. Each test reads one part of it; the
validity of an enclosure is read by ``foundations/def:exact-reference``'s own
decisions (:meth:`certiqs_key.foundations.reference.Enclosure.failures`).
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.foundations.exact import Cx
from certiqs_key.foundations.recentring import (
    EntrywiseEnclosure,
    hermitian_enclosure,
    recentred_enclosure,
)
from certiqs_key.foundations.reference import Enclosure

pytestmark = pytest.mark.contract


def _cx(re: F | int, im: F | int = 0) -> Cx:
    return Cx(F(re), F(im))


def _valid(enclosure: EntrywiseEnclosure) -> bool:
    """Hermitian centre, symmetric non-negative radii (def:exact-reference)."""
    return Enclosure(enclosure.centre, enclosure.radii).failures() == ()


def test_an_entry_whose_disc_holds_zero_gets_centre_zero_and_a_wider_radius() -> None:
    """Part (i): Z is decided on rationals; on Z the centre is 0, r + |Re| + |Im|."""
    tiny = F(1, 10**30)
    enclosure = EntrywiseEnclosure(
        ((_cx(1), _cx(tiny, tiny)), (_cx(tiny, -tiny), _cx(F(1, 2)))),
        ((F(0), 2 * tiny), (2 * tiny, F(0))),
    )
    recentred, changed = recentred_enclosure(enclosure)
    assert changed == 2
    assert recentred.centre[0][1].is_zero and recentred.centre[1][0].is_zero
    # r' = r + |Re C| + |Im C| on Z, nothing changed off it.
    assert recentred.radii[0][1] == 4 * tiny == recentred.radii[1][0]
    assert recentred.centre[0][0] == _cx(1) and recentred.radii[0][0] == 0
    # (i): Hermitian centre, symmetric non-negative radii; (ii): the widening
    # stays within (1 + sqrt 2) r, here 2r <= 2.415 r.
    assert _valid(recentred)
    assert recentred.radii[0][1] <= F(2415, 1000) * enclosure.radii[0][1]


def test_an_entry_outside_its_disc_and_an_exact_enclosure_are_left_alone() -> None:
    """Parts (ii), (iii): a centre beyond its radius stays; exact stays exact."""
    enclosure = EntrywiseEnclosure(
        ((_cx(1), _cx(F(1, 3))), (_cx(F(1, 3)), _cx(1))),
        ((F(0), F(1, 10)), (F(1, 10), F(0))),
    )
    recentred, changed = recentred_enclosure(enclosure)
    assert changed == 0 and recentred is enclosure
    exact = EntrywiseEnclosure.of(
        Enclosure.exact(((_cx(1), _cx(0)), (_cx(0), _cx(0))))
    )
    again, count = recentred_enclosure(exact)
    assert count == 0 and again.is_exact
    # A structurally zero entry (centre and radius 0) is in Z and unchanged.
    assert again.centre[1][1].is_zero and again.radii[1][1] == 0


def test_a_non_hermitian_pair_is_averaged_into_an_enclosure() -> None:
    """Part (iv): ((C + C^dagger)/2, (r + r^T)/2) encloses the Hermitian X."""
    centre = ((_cx(1), _cx(F(1, 4), F(1, 8))), (_cx(F(1, 4), F(-1, 4)), _cx(2)))
    radii = ((F(0), F(1, 16)), (F(3, 16), F(0)))
    averaged = hermitian_enclosure(centre, radii)
    assert _valid(averaged)
    assert averaged.centre[0][1] == _cx(F(1, 4), F(3, 16))
    assert averaged.radii[0][1] == F(1, 8) == averaged.radii[1][0]
    # X = [[1, x], [conj x, 2]] with |x - C_01| <= 1/16 and |conj x - C_10| <= 3/16:
    # x = 1/4 + i/8 is one; the averaged disc contains it.
    x = _cx(F(1, 4), F(1, 8))
    gap = x - averaged.centre[0][1]
    assert gap.squared_modulus <= averaged.radii[0][1] ** 2
    # Already Hermitian with symmetric radii: returned equal.
    same = hermitian_enclosure(averaged.centre, averaged.radii)
    assert same == averaged
