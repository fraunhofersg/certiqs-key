"""Soundness clauses of the certified tier's enclosures, each pinned against a mutant.

Each test pins one clause that a mutant of the code would otherwise survive in
every other tier:

- ``foundations/cor:least-eigenvalue-over-enclosure`` (ii): rho counts every
  entry of the radius matrix, the off-diagonal ones twice;
- the Weyl radius ``e`` of ``foundations/balls.spectral``, on which every
  error term of ``lem:matrix-function-perturbation`` rests;
- ``lem:matrix-function-perturbation`` (i): the ``sqrt(n)`` of the trace
  bound;
- ``meat-core/frank-wolfe/req:certified-evaluation`` (iv): a block whose
  floor ``l_K - rho_K`` is exactly zero has no certified rank;
- ``req:certified-evaluation`` (v)(b): an element whose rank is undecided
  enters the statistics operator as its enclosure.

Each passes on the code and fails on its mutant.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, ClassVar

import pytest

pytest.importorskip("flint")

from certiqs_key.foundations import balls
from certiqs_key.foundations.balls import Ball
from certiqs_key.foundations.dyadic import enclosure_eigenvalue_bounds
from certiqs_key.foundations.exact import Cx

ZERO, ONE, HALF = Fraction(0), Fraction(1), Fraction(1, 2)


def _cx(x: Fraction | int) -> Cx:
    return Cx(Fraction(x), ZERO)


# cor:least-eigenvalue-over-enclosure (ii): rho^2 >= the sum over ALL (i, l)
# of r_il^2


def test_rho_counts_every_entry_of_a_symmetric_radius_matrix() -> None:
    """X = -J (every entry -1) is a member of the box |X_il| <= 1 around C = 0.

    Its least eigenvalue is -n, so the bound must lie at or below it; counting each
    off-diagonal radius once gives rho = sqrt 3 at n = 2 and a bound above -2.
    """
    centre = [[_cx(0), _cx(0)], [_cx(0), _cx(0)]]
    radii = [[ONE, ONE], [ONE, ONE]]
    low, high = enclosure_eigenvalue_bounds(centre, radii)
    assert low <= -2
    assert high >= 2
    centre3 = [[_cx(0)] * 3 for _ in range(3)]
    low3, high3 = enclosure_eigenvalue_bounds(centre3, [[ONE] * 3 for _ in range(3)])
    assert low3 <= -3 and high3 >= 3


# lem:matrix-function-perturbation and spectral(): the Weyl radius e at a
# corner of the box


@pytest.mark.parametrize("n", [2, 3, 4])
def test_the_spectral_enclosure_holds_at_the_corners_of_the_box(n: int) -> None:
    """1 + r J and 1 - r J are Hermitian members at two corners.

    Their extreme eigenvalues are 1 +- n r.
    """
    r = Fraction(1, 4)
    centre = [[_cx(1 if i == j else 0) for j in range(n)] for i in range(n)]
    box = Ball.enclosure(centre, [[r] * n for _ in range(n)])
    with balls.precision(128):
        sp = balls.spectral(box)
        lo, hi = balls._exact(sp.lo.lower()), balls._exact(sp.hi.upper())
    assert hi >= 1 + n * r
    assert lo <= 1 - n * r
    assert balls.least_eigenvalue(box) <= 1 - n * r


# lem:matrix-function-perturbation (i):
# |tr f(P) - tr f(Q)| <= sqrt(n) L ||P - Q||_F


@pytest.mark.parametrize("s", [Fraction(2), Fraction(1, 2), Fraction(3, 2)])
def test_the_trace_power_carries_the_sqrt_n_of_the_trace_bound(s: Fraction) -> None:
    """(1 + r) 1 is a member of the diagonal-radius box around 1.

    Its trace power is n (1 + r)^s.
    """
    n, r = 4, Fraction(1, 10)
    centre = [[_cx(1 if i == j else 0) for j in range(n)] for i in range(n)]
    radii = [[r if i == j else ZERO for j in range(n)] for i in range(n)]
    with balls.precision(128):
        sp = balls.spectral(Ball.enclosure(centre, radii))
        trace = balls.trace_power(sp, balls.real(s), "trace")
        lo, hi = balls._exact(trace.lower()), balls._exact(trace.upper())
        member_hi = n * balls.real(1 + r) ** balls.real(s)
        member_lo = n * balls.real(1 - r) ** balls.real(s)
        assert hi >= balls.upper(member_hi)
        assert lo <= balls._exact(member_lo.lower())


# req:certified-evaluation (iv): a block whose floor is exactly zero has no
# certified rank


def test_a_block_whose_floor_is_exactly_zero_has_no_certified_rank() -> None:
    """C = 1 (2 x 2) with every radius 1/2 contains a rank-one member.

    Its entries are +1/2 and -1/2.

    l_K = 1 and rho_K = 1 exactly, so l_K - rho_K = 0: not positive, and the corollary
    fixes no rank. A rule reading >= 0 would declare rank 2 for a box containing a
    singular member.
    """
    from certiqs_key.solvers.frank_wolfe.certified import _enclosed_element

    centre = ((_cx(1), _cx(0)), (_cx(0), _cx(1)))
    element = _enclosed_element(centre, ((HALF, HALF), (HALF, HALF)))
    assert element.zero is False
    assert element.form is None
    assert element.cause is not None and "floor" in element.cause


# req:certified-evaluation (v)(b): an undecided element enters the statistics
# as its enclosure


def test_an_undecided_element_enters_the_statistics_operator_as_its_enclosure() -> None:
    from certiqs_key.solvers.frank_wolfe.certified import (
        _announcement_classes,
        _Element,
        _Model,
        _statistics_operators,
    )

    class _Declaration:
        alice_alphabet = ("a",)
        bob_outcomes = ("b",)
        accept_statistic: ClassVar[dict[tuple[str, ...], str]] = {("k",): "c"}

        @staticmethod
        def announcement(x: str, v: str) -> tuple[str, ...]:
            return ("k",)

    class _Maps:
        declaration = _Declaration()
        joint_sectors = (("t", "s"),)
        acceptance_support = ("c",)
        chat_key = ()

    # A duck-typed stand-in for JointMaps: only the fields the two functions read.
    maps: Any = _Maps()
    model = _Model(maps, ("c",), ())
    alice = {("a", "t"): _Element(Ball.of([[_cx(1)]]), False)}
    bob = {("b", "s"): _Element(Ball.enclosure([[_cx(0)]], [[HALF]]), None)}
    _statistics_operators(model, alice, bob, _announcement_classes(maps))
    gamma = model.gamma.get(("c", ("t", "s")))
    assert gamma is not None, "the undecided element was dropped from Gamma"
    entry = gamma.m[0, 0].real
    assert balls._exact(entry.lower()) <= -HALF
    assert balls.upper(entry) >= HALF
