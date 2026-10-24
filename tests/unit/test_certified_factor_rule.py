"""The certified evaluation's factor rule, its cross-check and the class stack.

``meat-core/frank-wolfe/req:certified-evaluation`` (iii)(a) and (iv) with
``lem:certified-bracket-enclosed`` (b), on factor enclosures injected by hand
(``foundations/def:factor-enclosure``). CONTRACT TESTS, each failing where its clause is
broken:

* (iv)(a) before (iv)(b): the entrywise rule decides first, the factor rule
  only where it leaves the block undecided or fixes no rank;
* (iv)(b): no column is zero, a certified Gram floor not zero with the
  adjoints' box as ``E`` and the core as ``X~``; otherwise nothing is decided;
* (iv)(c): the cross-check, at every block carrying a factor enclosure,
  whichever rule fixes the rank -- a disjoint entry, or one rule deciding zero
  and the other not zero, is ``factor_enclosure_inconsistent``;
* (b) of the lemma: a product of enclosed factors, one or several, is a
  factor form held through the Kronecker product of their boxes; the class stack is
  factorised per tuple of boxed blocks with ``B~`` exact, so Alice's exactly dependent
  rows reduce and two elements sharing one boxed block certify, while two distinct
  blocks with equal boxes stay apart and fail closed at the floor (item 3); an element
  with two boxed blocks stacks as its exact member does. The grouping's own tests,
  the reordering and its mutants are in ``test_certified_shared_boxed_block.py``.
"""

from __future__ import annotations

import math
from fractions import Fraction as F
from typing import Any

import pytest

pytest.importorskip("flint")

from certiqs_key.foundations import balls
from certiqs_key.foundations.balls import Ball
from certiqs_key.foundations.exact import Cx
from certiqs_key.foundations.reference import FactorEnclosure
from certiqs_key.solvers.frank_wolfe import certified
from certiqs_key.solvers.frank_wolfe.certified_record import (
    FACTOR_ENCLOSURE_INCONSISTENT,
    FLOOR_NOT_CERTIFIED,
)

pytestmark = pytest.mark.contract

ZERO, ONE = F(0), F(1)
TINY = F(1, 2**100)


def _cx(x: F | int) -> Cx:
    return Cx(F(x), ZERO)


def _angle() -> tuple[F, F]:
    """``(cos, sin)`` of ``pi/7`` as dyadics of ``2^-110``: an irrational analyser."""
    scale = 2**110
    return (
        F(round(math.cos(math.pi / 7) * scale), scale),
        F(round(math.sin(math.pi / 7) * scale), scale),
    )


def _projector() -> tuple[tuple[tuple[Cx, ...], ...], tuple[tuple[F, ...], ...]]:
    """Return ``q q^T`` exactly, every radius ``2^-100``: rank one, off the grid."""
    q = _angle()
    centre = tuple(tuple(_cx(q[i] * q[j]) for j in range(2)) for i in range(2))
    return centre, ((TINY, TINY), (TINY, TINY))


def _second() -> tuple[F, F]:
    """``(cos, sin)`` of ``pi/5`` as dyadics of ``2^-110``: the other analyser."""
    scale = 2**110
    return (
        F(round(math.cos(math.pi / 5) * scale), scale),
        F(round(math.sin(math.pi / 5) * scale), scale),
    )


def _enclosed_projector(q: tuple[F, F]) -> Any:
    """``q q^T`` through its entrywise enclosure and the box of ``q``: third kind."""
    centre = tuple(tuple(_cx(q[i] * q[j]) for j in range(2)) for i in range(2))
    radii = ((TINY, TINY), (TINY, TINY))
    return certified._companion_element(centre, radii, _column(*q), "P")


def _column(*entries: F, radius: F = TINY, core: F = ONE) -> FactorEnclosure:
    return FactorEnclosure(
        tuple((_cx(e),) for e in entries), tuple((radius,) for _ in entries), (core,)
    )


def _key(position: int, letter: str, sector: str = "s") -> tuple[int, str, str]:
    """Name a block as a block: factor position, the factor's letter, its sector."""
    return (position, letter, sector)


def _product(*parts: Any) -> Any:
    """Return the product of parts that are distinct blocks, named by position."""
    return certified._product(parts, [_key(i, f"b{i}") for i in range(len(parts))])


def _contains(ball: Ball, rows: Any) -> bool:
    return all(
        ball.m[i, j].contains(balls.flint.acb(balls.real(value), 0))
        for i, row in enumerate(rows)
        for j, value in enumerate(row)
    )


# (iv)(b), the factor rule on its own


def test_no_column_decides_zero() -> None:
    assert certified._factor_rule(FactorEnclosure.no_column(2)) == (True, None)


def test_a_certified_gram_decides_not_zero_with_the_adjoints_box() -> None:
    q = _angle()
    with balls.precision(128):
        decided, form = certified._factor_rule(_column(*q, core=F(1, 2)))
        assert decided is False and form is not None
        e, core = form
        assert isinstance(e, Ball) and e.shape == (1, 2)
        assert _contains(e, [[q[0], q[1]]]), "E holds L^dagger"
        assert _contains(core, [[F(1, 2)]]), "X~ is the exact core"


def test_dependent_columns_decide_nothing() -> None:
    q = _angle()
    two = FactorEnclosure(
        ((_cx(q[0]), _cx(q[0])), (_cx(q[1]), _cx(q[1]))),
        ((TINY, TINY), (TINY, TINY)),
        (ONE, ONE),
    )
    assert certified._factor_rule(two) == (None, None)


# (iv): the entrywise rule first, then the factor rule


def test_the_entrywise_rule_decides_first() -> None:
    """A positive definite block keeps the entrywise rule's exact ``E``."""
    centre = ((_cx(1), _cx(0)), (_cx(0), _cx(1)))
    factor = FactorEnclosure(
        ((_cx(1), _cx(0)), (_cx(0), _cx(1))), ((TINY, TINY), (TINY, TINY)), (ONE, ONE)
    )
    with balls.precision(128):
        element = certified._companion_element(
            centre, ((TINY, TINY), (TINY, TINY)), factor, "pd"
        )
    assert element.zero is False and element.form is not None
    assert not isinstance(element.form[0], Ball), "the entrywise rule's exact E"


def test_the_factor_rule_fixes_an_irrational_projector() -> None:
    """The O4 obstruction: no entrywise floor, a rank fixed by the factor."""
    centre, radii = _projector()
    with balls.precision(128):
        entrywise = certified._enclosed_element(centre, radii)
        assert entrywise.zero is False and entrywise.form is None
        element = certified._companion_element(centre, radii, _column(*_angle()), "P")
    assert element.zero is False and element.form is not None
    assert isinstance(element.form[0], Ball) and element.form[0].shape == (1, 2)


def test_no_column_decides_an_undecided_block_zero() -> None:
    zero = ((_cx(0), _cx(0)), (_cx(0), _cx(0)))
    radii = ((TINY, TINY), (TINY, TINY))
    with balls.precision(128):
        assert certified._enclosed_element(zero, radii).zero is None
        element = certified._companion_element(
            zero, radii, FactorEnclosure.no_column(2), "nc"
        )
    assert element.zero is True


def test_a_factor_that_decides_nothing_leaves_the_block_as_it_was() -> None:
    """Two dependent columns: no floor, no conflict, no certified rank."""
    q = _angle()
    centre = tuple(tuple(_cx(2 * q[i] * q[j]) for j in range(2)) for i in range(2))
    two = FactorEnclosure(
        ((_cx(q[0]), _cx(q[0])), (_cx(q[1]), _cx(q[1]))),
        ((TINY, TINY), (TINY, TINY)),
        (ONE, ONE),
    )
    with balls.precision(128):
        element = certified._companion_element(
            centre, ((TINY, TINY), (TINY, TINY)), two, "dependent"
        )
    assert element.zero is False and element.form is None


# (iv)(c): the cross-check, whichever rule fixes the rank


def _inconsistent(centre: Any, radii: Any, factor: FactorEnclosure) -> str:
    with balls.precision(128), pytest.raises(certified._Fail) as caught:
        certified._companion_element(centre, radii, factor, "block")
    assert caught.value.reason == FACTOR_ENCLOSURE_INCONSISTENT
    return str(caught.value)


def test_entrywise_not_zero_and_no_column_are_inconsistent() -> None:
    centre, radii = _projector()
    assert "the factor rule zero" in _inconsistent(
        centre, radii, FactorEnclosure.no_column(2)
    )


def test_entrywise_zero_and_a_certified_gram_are_inconsistent() -> None:
    zero = ((_cx(0), _cx(0)), (_cx(0), _cx(0)))
    nothing = ((ZERO, ZERO), (ZERO, ZERO))
    assert "decides it zero" in _inconsistent(zero, nothing, _column(*_angle()))


def test_a_disjoint_entry_is_inconsistent_where_the_entrywise_rule_decides() -> None:
    """The identity, decided by the entrywise rule, against members diag(1, 0)."""
    centre = ((_cx(1), _cx(0)), (_cx(0), _cx(1)))
    radii = ((TINY, TINY), (TINY, TINY))
    assert "disjoint at entry (1, 1)" in _inconsistent(
        centre, radii, _column(ONE, ZERO, radius=ZERO)
    )


def test_overlapping_enclosures_are_consistent() -> None:
    """``q q^T``'s members overlap its entrywise enclosure: no raise."""
    centre, radii = _projector()
    with balls.precision(128):
        certified._companion_element(centre, radii, _column(*_angle()), "P")


def test_a_gap_between_one_and_two_radii_is_disjoint() -> None:
    """Disjoint means farther than the radius, not than some multiple of it.

    Entrywise ``diag(1, 0)`` with radius ``1/4`` on entry ``(0, 0)``; the one
    member ``diag(11/8, 0)`` (column ``(1, 0)`` exactly, core ``11/8``) lies
    ``3/8``, one and a half radii, from it: inconsistent.
    """
    centre = ((_cx(1), _cx(0)), (_cx(0), _cx(0)))
    radii = ((F(1, 4), ZERO), (ZERO, ZERO))
    factor = _column(ONE, ZERO, radius=ZERO, core=F(11, 8))
    assert "disjoint at entry (0, 0)" in _inconsistent(centre, radii, factor)
    # At 5/4, one radius away, the two touch and are consistent.
    with balls.precision(128):
        certified._companion_element(
            centre, radii, _column(ONE, ZERO, radius=ZERO, core=F(5, 4)), "touch"
        )


# lem:certified-bracket-enclosed (b): products and the class stack


def test_a_product_of_enclosed_factors_is_a_factor_form() -> None:
    """One or two blocks of the third kind: ``E`` in the Kronecker box, rank fixed.

    ``q q^T`` read through the box of ``q``: beside an exact block the
    product's ``E`` is a ``1 x 4`` box, and so it is for two such blocks (both
    stations enclosed, the second at ``p``), containing ``(q (x) p)^T``, the
    first factor the slower, with core ``1``.
    """
    q, p = _angle(), _second()
    with balls.precision(128):
        enclosed = _enclosed_projector(q)
        exact = certified._exact_element(((_cx(1), _cx(0)), (_cx(0), _cx(0))))
        mixed = _product(exact, enclosed)
        twice = _product(enclosed, _enclosed_projector(p))
        assert mixed.form is not None and isinstance(mixed.form[0], Ball)
        assert mixed.form[0].shape == (1, 4)
        assert twice.zero is False and twice.form is not None
        e, core = twice.form
        assert isinstance(e, Ball) and e.shape == (1, 4)
        assert _contains(e, [[q[i] * p[j] for i in range(2) for j in range(2)]])
        assert not _contains(e, [[p[i] * q[j] for i in range(2) for j in range(2)]])
        assert _contains(core, [[ONE]])


def _box() -> Ball:
    q = _angle()
    return Ball.enclosure(((_cx(q[0]),), (_cx(q[1]),)), ((TINY,), (TINY,))).adjoint


def _alone(box: Ball, block: tuple[int, str, str]) -> certified._Split:
    """Return the split form of an element that is the boxed block ``block``."""
    k, n = box.shape
    return certified._Split(((_cx(1),),), box, (block,), (True,), (k,), (n,))


def _row(
    alice: int, bob: Ball, key: int, block: tuple[int, str, str]
) -> certified._Row:
    return certified._Row(
        ((_cx(alice),),), bob, Ball.of([[_cx(1)]]), key, _alone(bob, block)
    )


def _form_row(alice: Any, element: Any, core: Ball, key: int) -> certified._Row:
    """Return the row of a pair from an element :func:`certified._product` forms."""
    assert element.form is not None
    e, bob_core = element.form
    return certified._Row(alice, e, core.kron(bob_core), key, element.split)


def test_alices_dependent_rows_reduce_per_boxed_tuple() -> None:
    """Alice's sector of dimension 1: two letters, both ``E_x = [1]``, one Bob ``v``.

    The stack is ``[E_v; E_v]``, of rank 1; per tuple ``S_beta = [1; 1] =
    B_beta C_beta`` exactly, so ``C = C_beta (x) E_v = E_v``, one row, and the
    floor of ``N`` is certified. With ``B~ = 1`` ``C`` would keep both rows and
    ``N`` would be singular.
    """
    box = _box()
    with balls.precision(128):
        klass = certified._class(
            [_row(1, box, 0, _key(0, "v")), _row(1, box, 1, _key(0, "v"))]
        )
        assert klass is not None and klass.c.shape == (1, 2)
        choi = Ball.of([[_cx(1), _cx(0)], [_cx(0), _cx(1)]])
        value, _ = certified._deficit([klass], choi, balls.real(F(3, 2)), "test")
    assert value is not None


def test_two_distinct_blocks_with_equal_boxes_fail_closed() -> None:
    """Two blocks, ``v`` and ``w``, with one box object: two groups, the floor fails.

    ``req:certified-evaluation`` (iii)(a): "two distinct blocks with equal
    boxes are distinct entries of the tuples". The two blocks are named by
    distinct keys and handed the very same box, so a grouping by the boxes
    would merge them and certify. Grouped by the blocks, ``C`` keeps a row
    per block; the rows are dependent at the member where the two blocks'
    ``E_*`` agree, through an irrational relation no exact factorisation
    sees, so ``N`` is singular there and the point fails closed with
    ``floor_not_certified`` (prototype pitfall 5.3 item 3).
    """
    box = _box()
    with balls.precision(128):
        klass = certified._class(
            [_row(1, box, 0, _key(0, "v")), _row(1, box, 1, _key(0, "w"))]
        )
        assert klass is not None and klass.c.shape == (2, 2)
        choi = Ball.of([[_cx(1), _cx(0)], [_cx(0), _cx(1)]])
        with pytest.raises(certified._Fail) as caught:
            certified._deficit([klass], choi, balls.real(F(3, 2)), "test")
    assert caught.value.reason == FLOOR_NOT_CERTIFIED


def test_two_elements_sharing_one_boxed_block_certify() -> None:
    """Two Bob elements ``(a, b)`` and ``(a', b)``, ``b`` boxed and shared: one group.

    The case at issue (a dark count makes every block of station A at the
    vacuum a non-zero ``1 x 1`` scalar, ``E_a = E_a' = [1]``): both elements
    are ``[1] (x) E_b``, of the one tuple ``((1, b, s),)``. Grouped by that
    tuple, ``S_beta = [1; 1]`` has rank 1 exactly, ``C`` has the one row
    ``E_b`` and the floor of ``N`` is certified; per element (``C`` with the
    rows ``E_b`` twice) it fails, as two distinct blocks do.
    """
    q = _angle()
    centre = tuple(tuple(_cx(q[i] * q[j]) for j in range(2)) for i in range(2))
    one = certified._exact_element(((_cx(1),),))
    with balls.precision(128):
        b = certified._companion_element(
            centre, ((TINY, TINY), (TINY, TINY)), _column(*q), "b"
        )
        shared = _key(1, "b")
        first = certified._product([one, b], [_key(0, "a"), shared])
        second = certified._product([one, b], [_key(0, "a'"), shared])
        assert first.split is not None and second.split is not None
        assert first.split.blocks == second.split.blocks == (shared,)
        core = Ball.of([[_cx(1)]])
        klass = certified._class(
            [
                _form_row(((_cx(1),),), first, core, 0),
                _form_row(((_cx(1),),), second, core, 1),
            ]
        )
        assert klass is not None and klass.c.shape == (1, 2)
        choi = Ball.of([[_cx(1), _cx(0)], [_cx(0), _cx(1)]])
        value, _ = certified._deficit([klass], choi, balls.real(F(3, 2)), "test")
    assert value is not None


def test_exact_rows_take_one_factorisation_as_before() -> None:
    """No enclosed ``E_v``: ``B~ C`` is the stack's one exact rank factorisation."""
    exact = ((_cx(1), _cx(0)),)
    with balls.precision(128):
        klass = certified._class(
            [
                certified._Row(((_cx(1),),), exact, Ball.of([[_cx(1)]]), 0),
                certified._Row(((_cx(1),),), exact, Ball.of([[_cx(1)]]), 1),
            ]
        )
    assert klass is not None and klass.c.shape == (1, 2)


def test_a_row_carries_its_split_form_exactly_where_e_v_is_a_box() -> None:
    """``_Row`` refuses a boxed ``E_v`` with no tuple, and a tuple on an exact one."""
    box = _box()
    with pytest.raises(
        certified._Fail, match=r"^boxed_form_inconsistent: .*split form"
    ):
        certified._Row(((_cx(1),),), box, Ball.of([[_cx(1)]]), 0)
    with pytest.raises(
        certified._Fail, match=r"^boxed_form_inconsistent: .*split form"
    ):
        certified._Row(
            ((_cx(1),),), ((_cx(1), _cx(0)),), Ball.of([[_cx(1)]]), 0,
            _alone(box, _key(0, "v")),
        )


def test_a_compiled_factor_refuses_a_factor_enclosure_of_another_shape() -> None:
    """The compiled factor: one enclosure per sector, of the block's dimension."""
    from certiqs_key.protocol_compiler.companion import CompanionFactor

    centre = ((_cx(1), _cx(0)), (_cx(0), _cx(0)))
    radii = ((ZERO, ZERO), (ZERO, ZERO))

    def compiled(enclosures: dict[str, Any]) -> CompanionFactor:
        return CompanionFactor(
            position=0,
            label="B",
            alphabet=("v",),
            sector_labels=("s",),
            sector_dims=(2,),
            centres={"v": (centre,)},
            radii={"v": (radii,)},
            record={},
            factor_enclosures=enclosures,
        )

    assert compiled({"v": (FactorEnclosure.no_column(2),)}).factor_enclosures
    with pytest.raises(ValueError, match="dimension"):
        compiled({"v": (FactorEnclosure.no_column(3),)})
    with pytest.raises(ValueError, match="one per sector"):
        compiled({"v": ()})
    with pytest.raises(ValueError, match="one per sector"):
        compiled({"w": (None,)})


def test_the_per_tuple_stack_agrees_with_the_exact_one() -> None:
    """The per-tuple ``E~ = B~ C`` places ``B_beta (x) 1``: same deficit as exact.

    Alice's sector of dimension 2 with ``E_x1 = (1, 0)``, ``E_x2 = (0, 1)``
    (so ``S_beta`` has rank 2), one Bob element with ``E_v`` of two rows in a
    space of three, raw keys 0 and 1. Read exactly the class takes one exact
    rank factorisation; read through a box of radius 0 it takes the
    per-tuple one. Both give the branch operators of the same stack, so the
    two deficits at one Choi block overlap; a ``B~`` whose columns are placed
    in the other Kronecker order, ``1 (x) B_beta``, would not.
    """
    e_v = ((_cx(1), _cx(0), _cx(0)), (_cx(0), _cx(1), _cx(0)))
    box = Ball.of(e_v)
    core = Ball.of([[_cx(1), _cx(0)], [_cx(0), _cx(2)]])
    a1, a2 = ((_cx(1), _cx(0)),), ((_cx(0), _cx(1)),)
    n = 6
    choi = Ball.of(
        [
            [_cx(2) if i == j else _cx(F(1, 4)) if abs(i - j) == 1 else _cx(0)
             for j in range(n)]
            for i in range(n)
        ]
    )
    alpha = balls.real(F(3, 2))
    with balls.precision(128):
        def rows(bob: Any) -> list[certified._Row]:
            split = _alone(bob, _key(0, "v")) if isinstance(bob, Ball) else None
            return [
                certified._Row(a1, bob, core, 0, split),
                certified._Row(a2, bob, core, 1, split),
            ]

        exact = certified._class(rows(e_v))
        enclosed = certified._class(rows(box))
        assert exact is not None and enclosed is not None
        value_exact, _ = certified._deficit([exact], choi, alpha, "exact")
        value_box, _ = certified._deficit([enclosed], choi, alpha, "box")
    assert value_exact.overlaps(value_box)


def test_two_boxed_blocks_stack_as_their_exact_member() -> None:
    """An element whose blocks at both stations are only boxed: same deficit as exact.

    ``E_v = (q (x) p)^T``, one row in a space of four, from two blocks of the
    third kind at different analysers; Alice's sector of dimension 2 with
    ``E_x1 = (1, 0)``, ``E_x2 = (0, 1)``, raw keys 0 and 1. Read through the
    Kronecker product of the two boxes the class takes the per-tuple
    factorisation; read exactly, the one exact rank factorisation. The two
    deficits at one Choi block overlap; a box formed in the other Kronecker
    order, ``(p (x) q)^T``, would not.
    """
    q, p = _angle(), _second()
    with balls.precision(128):
        element = _product(_enclosed_projector(q), _enclosed_projector(p))
        assert element.form is not None
        box, core = element.form
        assert isinstance(box, Ball)
        exact = ((tuple(_cx(q[i] * p[j]) for i in range(2) for j in range(2))),)
        a1, a2 = ((_cx(1), _cx(0)),), ((_cx(0), _cx(1)),)
        n = 8
        choi = Ball.of(
            [
                [_cx(2) if i == j else _cx(F(1, 4)) if abs(i - j) == 1 else _cx(0)
                 for j in range(n)]
                for i in range(n)
            ]
        )
        alpha = balls.real(F(3, 2))

        def rows(bob: Any) -> list[certified._Row]:
            split = element.split if isinstance(bob, Ball) else None
            return [
                certified._Row(a1, bob, core, 0, split),
                certified._Row(a2, bob, core, 1, split),
            ]

        by_box = certified._class(rows(box))
        by_exact = certified._class(rows(exact))
        assert by_box is not None and by_exact is not None
        value_box, _ = certified._deficit([by_box], choi, alpha, "box")
        value_exact, _ = certified._deficit([by_exact], choi, alpha, "exact")
    assert value_box.overlaps(value_exact)


def test_a_products_factor_form_reproduces_the_product() -> None:
    """``E^dagger X E`` of a product contains ``kron`` of its parts, in their order.

    Two exact parts of rank 2 with cores that are no multiples of the
    identity, and a third-kind part beside one of them: each product's form
    must give back the tensor product in the order of its parts, the first
    the slower, which a form with the cores' (or the factors') Kronecker
    order swapped does not.
    """
    a = ((F(2), F(1)), (F(1), F(1)))
    b = ((F(3), F(1)), (F(1), F(2)))
    q = _angle()
    projector = tuple(tuple(q[i] * q[j] for j in range(2)) for i in range(2))

    def exact(m: Any) -> Any:
        return certified._exact_element(tuple(tuple(_cx(x) for x in row) for row in m))

    with balls.precision(128):
        exact_a, exact_b = exact(a), exact(b)
        enclosed = _enclosed_projector(q)
        cases = [
            ([exact_a, exact_b], a, b),
            ([exact_b, exact_a], b, a),
            ([exact_a, enclosed], a, projector),
            ([enclosed, exact_b], projector, b),
        ]
        for parts, left, right in cases:
            element = _product(*parts)
            assert element.form is not None
            e, core = element.form
            box = e if isinstance(e, Ball) else Ball.of(e)
            product = [
                [left[i // 2][j // 2] * right[i % 2][j % 2] for j in range(4)]
                for i in range(4)
            ]
            assert _contains(box.adjoint @ core @ box, product)


#: A wide box radius, so that a box built from centres alone would miss members.
WIDE = F(1, 64)


def _boxed(q: tuple[F, F]) -> Any:
    """``q q^T``, entrywise radius 1/8, read through the box of ``q`` of radius 1/64."""
    centre = tuple(tuple(_cx(q[i] * q[j]) for j in range(2)) for i in range(2))
    radii = ((F(1, 8), F(1, 8)), (F(1, 8), F(1, 8)))
    factor = FactorEnclosure(
        tuple((_cx(e),) for e in q), tuple((WIDE,) for _ in q), (ONE,)
    )
    return certified._companion_element(centre, radii, factor, "P")


def test_the_kronecker_box_of_two_boxes_holds_every_member() -> None:
    """``req:certified-evaluation`` (iii): ``E`` in the Kronecker box at EVERY member.

    Not only at the centres' product: at the four corners ``q* (x) p*`` of two
    boxes of radius 1/64. A box formed from the centres alone misses them.
    """
    q, p = _angle(), _second()
    with balls.precision(128):
        element = _product(_boxed(q), _boxed(p))
        assert element.form is not None
        e, _ = element.form
        assert isinstance(e, Ball) and e.shape == (1, 4)
        for sq in (-1, 1):
            for sp in (-1, 1):
                q_star = (q[0] + sq * WIDE, q[1] - sq * WIDE)
                p_star = (p[0] - sp * WIDE, p[1] + sp * WIDE)
                row = [q_star[i] * p_star[j] for i in range(2) for j in range(2)]
                assert _contains(e, [row]), (sq, sp)


def test_a_shared_box_of_rank_one_times_rank_two_stacks_as_its_exact_member() -> None:
    """A product box with ``k_v = 2``, its boxed block shared by two class elements.

    ``lem:certified-bracket-enclosed`` (b), the stack: the elements ``v`` and
    ``w`` are the boxed ``q q^T`` times ``diag(1, 2, 0)`` and times
    ``diag(0, 0, 1)``, so ``E_v`` is a ``2 x 6`` box and ``E_w`` a ``1 x 6``
    one sharing the boxed factor. Their class's deficit overlaps the one
    formed with the exact member.
    """
    q = _angle()
    centre = tuple(tuple(_cx(q[i] * q[j]) for j in range(2)) for i in range(2))

    def diag(*d: int) -> Any:
        return certified._exact_element(
            tuple(tuple(_cx(d[i] if i == j else 0) for j in range(3)) for i in range(3))
        )

    b, b_prime = diag(1, 2, 0), diag(0, 0, 1)
    alice = [((_cx(1), _cx(0)),), ((_cx(0), _cx(1)),)]
    n = 12
    choi = Ball.of(
        [
            [
                _cx(3) if i == j else _cx(F(1, 4)) if abs(i - j) in (1, 5) else _cx(0)
                for j in range(n)
            ]
            for i in range(n)
        ]
    )
    alpha = balls.real(F(3, 2))
    with balls.precision(128):
        boxed_a = certified._companion_element(
            centre, ((TINY, TINY), (TINY, TINY)), _column(*q), "a"
        )
        exact_a = certified._exact_element(centre)

        def rows(a: Any) -> list[certified._Row]:
            out = []
            for letter, part in (("v", b), ("w", b_prime)):
                element = certified._product([a, part], [_key(0, "a"), _key(1, letter)])
                for key, e_x in enumerate(alice):
                    out.append(_form_row(e_x, element, Ball.of([[_cx(1)]]), key))
            return out

        boxed = rows(boxed_a)
        assert isinstance(boxed[0].bob, Ball) and boxed[0].bob.shape == (2, 6)
        tuples = {row.split.blocks for row in boxed if row.split is not None}
        assert tuples == {(_key(0, "a"),)}, "v and w share the one group of block a"
        by_box = certified._class(boxed)
        by_exact = certified._class(rows(exact_a))
        assert by_box is not None and by_exact is not None
        value_box, _ = certified._deficit([by_box], choi, alpha, "box")
        value_exact, _ = certified._deficit([by_exact], choi, alpha, "exact")
    assert value_box.overlaps(value_exact)


def test_a_block_decided_zero_decides_its_element_whatever_its_partner() -> None:
    """A block zero for every member makes its element zero: nothing asked of others.

    ``lem:certified-bracket-enclosed``: a block decided zero beside an
    undecided one makes the element zero, in either order
    (``req:certified-evaluation`` (iv), the waiver).
    """
    zero = ((Cx(F(0), F(0)),),)
    with balls.precision(128):
        decided = certified._enclosed_element(zero, ((F(0),),))
        undecided = certified._enclosed_element(zero, ((F(1, 2**100),),))
        assert undecided.zero is None
        assert _product(decided, undecided).zero is True
        assert _product(undecided, decided).zero is True
