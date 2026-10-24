"""A factor enclosure and the rank it fixes, decided exactly.

``foundations/def:factor-enclosure`` (:class:`FactorEnclosure`, carried beside
a block's entrywise enclosure) and ``foundations/cor:rank-over-factor-
enclosure`` (:func:`fixes_rank`, :func:`gram_radius`): (i) no column is the
zero member; (ii) a Gram floor fixes the rank at every member; (iii) the
rational choice of ``G = L_c^dagger L_c`` and ``rho``. CONTRACT TESTS, each
failing where its clause is broken, the numbers derived by hand below.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Cx
from certiqs_key.foundations.reference import (
    Enclosure,
    FactorEnclosure,
    fixes_rank,
    gram_radius,
)

pytestmark = pytest.mark.contract

ZERO = F(0)


def _cx(re: F | int, im: F | int = 0) -> Cx:
    return Cx(F(re), F(im))


def _column(*entries: Cx, radius: F) -> FactorEnclosure:
    """Return a one-column factor enclosure with every radius ``radius``, core 1."""
    return FactorEnclosure(
        tuple((entry,) for entry in entries),
        tuple((radius,) for _ in entries),
        (F(1),),
    )


# def:factor-enclosure: the triple, decided as req:snap-reference (i) says


def test_a_factor_enclosure_is_d_by_k_with_exact_entries() -> None:
    with pytest.raises(MalformedInputError, match="d x k"):
        FactorEnclosure(((_cx(1),),), ((ZERO,),), (F(1), F(2)))
    with pytest.raises(MalformedInputError, match="Cx"):
        FactorEnclosure(((1,),), ((ZERO,),), (F(1),))  # type: ignore[arg-type]
    with pytest.raises(MalformedInputError, match="Fraction"):
        FactorEnclosure(((_cx(1),),), ((0.5,),), (F(1),))  # type: ignore[arg-type]
    with pytest.raises(MalformedInputError, match="d >= 1"):
        FactorEnclosure((), (), ())


def test_the_declarers_decisions_on_radii_and_core() -> None:
    """req:snap-reference (i): radii non-negative, core positive; else not carried."""
    good = _column(_cx(1), radius=F(1, 8))
    assert good.failures() == ()
    negative = FactorEnclosure(((_cx(1),),), ((F(-1, 8),),), (F(1),))
    assert negative.failures() == ("factor_radius_negative",)
    flat = FactorEnclosure(((_cx(1),),), ((ZERO,),), (ZERO,))
    assert flat.failures() == ("factor_core_not_positive",)


def test_an_enclosure_carries_a_factor_of_its_own_dimension() -> None:
    centre = ((_cx(1), _cx(0)), (_cx(0), _cx(0)))
    radii = ((ZERO, ZERO), (ZERO, ZERO))
    carried = Enclosure(centre, radii, _column(_cx(1), _cx(0), radius=ZERO))
    assert carried.as_record()["factor"] == {
        "centre": [["1+0i"], ["0+0i"]],
        "radii": [["0"], ["0"]],
        "core": ["1"],
    }
    assert "factor" not in Enclosure(centre, radii).as_record()
    with pytest.raises(MalformedInputError, match="dimension"):
        Enclosure(centre, radii, _column(_cx(1), radius=ZERO))


# cor:rank-over-factor-enclosure (i): no column


def test_no_column_is_the_zero_member_and_fixes_no_rank_of_its_own() -> None:
    empty = FactorEnclosure.no_column(3)
    assert (empty.dimension, empty.columns) == (3, 0)
    assert not fixes_rank(empty)


# cor:rank-over-factor-enclosure (iii): eq:gram-radius by hand


def test_the_gram_radius_is_eq_gram_radius() -> None:
    """``L_c = (1, i)^T``, ``t = (1/4, 1/8)``: ``a = (1, 1)``.

    ``s_11 = (1 * 1/4 + 1/4 * 1 + 1/16) + (1 * 1/8 + 1/8 * 1 + 1/64)
    = 9/16 + 17/64 = 53/64``; so ``rho`` is the least grid rational at least
    ``53/64``, within ``2^-64`` relative of it.
    """
    factor = FactorEnclosure(
        ((_cx(1),), (_cx(0, 1),)), ((F(1, 4),), (F(1, 8),)), (F(1),)
    )
    rho = gram_radius(factor)
    assert rho >= F(53, 64)
    assert rho - F(53, 64) <= F(53, 64) * F(1, 2**63)


def test_two_columns_take_every_cross_term() -> None:
    """``L_c = [[1, 0], [0, 1]]``, every ``t = 1/10``: ``a = 1`` on the diagonal.

    ``s_ml = sum_i (a_im t + t a_il + t^2)``: ``s_11 = s_22 = (2/10 + 1/100) +
    1/100 = 22/100``, ``s_12 = s_21 = (1/10 + 1/100) + (1/10 + 1/100) =
    22/100``; ``sum s^2 = 4 (22/100)^2``, so ``rho >= 44/100``.
    """
    t = F(1, 10)
    factor = FactorEnclosure(
        ((_cx(1), _cx(0)), (_cx(0), _cx(1))), ((t, t), (t, t)), (F(1), F(1))
    )
    assert gram_radius(factor) >= F(44, 100)
    assert gram_radius(factor) - F(44, 100) <= F(1, 2**60)
    # G = 1, so 1 - rho > 0: the rank 2 is fixed at every member.
    assert fixes_rank(factor)


# cor:rank-over-factor-enclosure (ii): the floor, decided exactly


def test_a_gram_floor_fixes_the_rank_of_a_column_away_from_zero() -> None:
    """``L_c = (1, 0)``, ``t = (1/3, 0)``: ``s = 2/3 + 1/9 = 7/9 < 1 = G``."""
    factor = FactorEnclosure(((_cx(1),), (_cx(0),)), ((F(1, 3),), (ZERO,)), (F(1),))
    assert fixes_rank(factor)


@pytest.mark.parametrize("radius", [F(1), F(2), F(1, 2), F(9, 20)])
def test_no_floor_where_the_bound_does_not_clear_g(radius: F) -> None:
    """``L_c = (1, 0)``, ``t = (r, 0)``: ``s = 2r + r^2``, at least ``1`` here.

    At ``r >= 1`` the box contains the zero factor, a member of rank 0; at
    ``r = 1/2`` and ``9/20`` every factor has rank 1 but the bound of (iii),
    ``2r + r^2 >= 1``, does not clear ``G = 1``, and no rank is claimed.
    """
    factor = FactorEnclosure(((_cx(1),), (_cx(0),)), ((radius,), (ZERO,)), (F(1),))
    assert not fixes_rank(factor)


def test_a_box_holding_a_rank_deficient_factor_fixes_no_rank() -> None:
    """``L_c = [[1, 1], [0, e]]``, ``t_22 = e``: the box holds ``[[1, 1], [0, 0]]``.

    That factor has rank 1 of 2, so no floor may be established, however small
    ``e``.
    """
    for e in (F(1, 2), F(1, 1000), F(1, 2**80)):
        factor = FactorEnclosure(
            ((_cx(1), _cx(1)), (_cx(0), _cx(e))),
            ((ZERO, ZERO), (ZERO, e)),
            (F(1), F(1)),
        )
        assert not fixes_rank(factor)


def test_more_columns_than_rows_fix_no_rank() -> None:
    """``k > d``: every factor's ``L^dagger L`` is singular (``k <= d`` in (ii))."""
    factor = FactorEnclosure(
        ((_cx(1), _cx(0), _cx(0)), (_cx(0), _cx(1), _cx(0))),
        ((ZERO,) * 3, (ZERO,) * 3),
        (F(1),) * 3,
    )
    assert not fixes_rank(factor)


def test_an_exact_rank_one_column_at_an_irrational_angle_is_fixed() -> None:
    """The ideal analyser's case: a column ``(cos, sin)`` known to 2^-120.

    ``(cos 1/7 pi, sin 1/7 pi)`` rounded to dyadics of 2^-120 with that radius:
    ``G`` is within 2^-118 of 1 and ``rho`` of order 2^-119, so the rank is 1.
    """
    import math

    scale = 2**120
    c = F(round(math.cos(math.pi / 7) * scale), scale)
    s = F(round(math.sin(math.pi / 7) * scale), scale)
    r = F(1, 2**52)  # the binary64 rounding of cos and sin bounds the error
    factor = FactorEnclosure(((_cx(c),), (_cx(s),)), ((r,), (r,)), (F(1, 2),))
    assert fixes_rank(factor)
