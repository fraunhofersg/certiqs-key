"""The class stack grouped by the blocks held through boxes, and its reordering.

``meat-core/frank-wolfe/lem:certified-bracket-enclosed`` (b), "the reordering"
and "the stack", and ``meat-core/frank-wolfe/req:certified-evaluation`` (iii)(a):
the rows of a pass class whose element is held through a box are grouped by the
element's whole tuple of boxed blocks, each named by its key and never by its box,
and the group's block of ``C`` is ``(C_beta (x) E^box_beta) U_beta``. CONTRACT
TESTS, each failing where its clause is broken:

* the split form :func:`certified._product` carries: the exact parts' Kronecker
  product, the boxed parts' one, the tuple of the boxed parts' keys and the
  dimensions; none where no part is boxed;
* the reordering ``E_v = R_v (E^ex_v (x) E^box_beta) Sigma_beta(n)`` and the
  stacked rows ``(1 (x) R_v)((E_x (x) E^ex_v) (x) E^box_beta) U_beta``, entry by
  entry on exact matrices, for every placement of the boxed positions;
* the grouping: tuples that share one boxed block but differ in another, or in
  whether another block is boxed, are two groups, whatever their boxes;
* the stack against the exact member: a rank-two box at factor position 0 beside
  an exact block of rank two (``R_v`` and ``Sigma_beta(n)`` both non-trivial),
  shared by two elements, gives the deficit and its gradient the exact member
  gives;
* ``E~ = B~ C`` on random classes: the Gram matrices the class forms from ``C``
  are those of the exact stack, in full and per raw key.

Mutants of :func:`certified._class` these tests kill: keying the groups by the
boxes, per element, or by the first boxed block only; dropping ``U_beta``'s
column permutation or inverting it; dropping ``R_v`` from the placement of
``B~``'s rows; swapping the Kronecker factors of ``C_beta (x) E^box_beta``.
"""

from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction as F
from typing import Any

import pytest

pytest.importorskip("flint")

from certiqs_key.foundations import balls
from certiqs_key.foundations.balls import Ball
from certiqs_key.foundations.exact import Cx, kron, rank_factorisation
from certiqs_key.foundations.reference import FactorEnclosure
from certiqs_key.solvers.frank_wolfe import certified

pytestmark = pytest.mark.contract

ZERO, ONE = F(0), F(1)
TINY = F(1, 2**100)
ALPHA = F(3, 2)


def _cx(x: F | int) -> Cx:
    return Cx(F(x), ZERO)


def _matrix(rows: Any) -> tuple[tuple[Cx, ...], ...]:
    return tuple(tuple(_cx(x) for x in row) for row in rows)


def _key(position: int, letter: str, sector: str = "s") -> tuple[int, str, str]:
    return (position, letter, sector)


def _analyser(angle: float) -> tuple[F, F]:
    """``(cos, sin)`` of ``angle`` as dyadics of ``2^-110``: off the grid."""
    scale = 2**110
    return (
        F(round(math.cos(angle) * scale), scale),
        F(round(math.sin(angle) * scale), scale),
    )


def _boxed_projector(q: tuple[F, F]) -> Any:
    """``q q^T`` through its entrywise enclosure and the box of ``q``: third kind."""
    centre = _matrix([[q[i] * q[j] for j in range(2)] for i in range(2)])
    factor = FactorEnclosure(
        tuple((_cx(e),) for e in q), tuple((TINY,) for _ in q), (ONE,)
    )
    return certified._companion_element(
        centre, ((TINY, TINY), (TINY, TINY)), factor, "P"
    )


def _exact_projector(q: tuple[F, F]) -> Any:
    """Return the same ``q q^T`` read exactly: the boxed one's exact member."""
    return certified._exact_element(
        _matrix([[q[i] * q[j] for j in range(2)] for i in range(2)])
    )


def _rank_two() -> tuple[Any, Any]:
    """Return a rank-two block in dimension 3, boxed (``k = 2``) and exact.

    ``L = [[c, 0], [s, 0], [0, 1]]`` with ``(c, s)`` off the grid, core ``1``:
    the block ``L L^T`` is singular, so no entrywise floor fixes its rank, and
    the factor rule fixes rank 2 through the ``2 x 3`` box of ``L^T``.
    """
    c, s = _analyser(math.pi / 7)
    columns = ((c, ZERO), (s, ZERO), (ZERO, ONE))
    block = _matrix(
        [[sum(columns[i][m] * columns[j][m] for m in range(2)) for j in range(3)]
         for i in range(3)]
    )
    radii = tuple((TINY,) * 3 for _ in range(3))
    factor = FactorEnclosure(
        tuple(tuple(_cx(x) for x in row) for row in columns),
        tuple((TINY, TINY) for _ in range(3)),
        (ONE, ONE),
    )
    boxed = certified._companion_element(block, radii, factor, "L")
    assert boxed.form is not None and isinstance(boxed.form[0], Ball)
    assert boxed.form[0].shape == (2, 3)
    return boxed, certified._exact_element(block)


def _row(alice: Any, element: Any, key: int) -> certified._Row:
    """Return the row of a pair ``(x, v)``, ``E_x = alice``, core ``X_x = 1``."""
    assert element.form is not None
    e, core = element.form
    one = Ball.of([[_cx(1)]])
    return certified._Row(alice, e, one.kron(core), key, element.split)


def _choi(n: int) -> Ball:
    """``2 1 + H``, ``H`` the Hilbert matrix: positive definite, no symmetry.

    No permutation of the coordinates but the identity leaves it fixed, so a
    stack whose columns or rows are placed in a wrong order changes the deficit.
    """
    return Ball.of(
        [
            [_cx((2 if i == j else 0) + F(1, i + j + 1)) for j in range(n)]
            for i in range(n)
        ]
    )


def _agree(
    boxed: certified._Class | None, exact: certified._Class | None, n: int
) -> None:
    """Assert the deficits and gradients at one Choi block, boxed and exact, overlap."""
    assert boxed is not None and exact is not None
    choi, alpha = _choi(n), balls.real(ALPHA)
    value_box, gradient_box = certified._deficit([boxed], choi, alpha, "box")
    value_exact, gradient_exact = certified._deficit([exact], choi, alpha, "exact")
    assert value_box.overlaps(value_exact)
    for i in range(n):
        for j in range(n):
            assert gradient_box.m[i, j].overlaps(gradient_exact.m[i, j]), (i, j)


# The split form


def test_the_split_form_of_an_exact_block_beside_a_boxed_one() -> None:
    q = _analyser(math.pi / 7)
    exact = certified._exact_element(_matrix([[2, 1, 0], [1, 1, 0], [0, 0, 0]]))
    with balls.precision(128):
        boxed = _boxed_projector(q)
        element = certified._product([exact, boxed], [_key(0, "x"), _key(1, "b")])
    assert exact.form is not None and boxed.form is not None
    split = element.split
    assert split is not None
    assert split.exact == exact.form[0], "E^ex: the exact part's E"
    assert split.box is boxed.form[0], "E^box: the boxed part's box itself"
    assert split.blocks == (_key(1, "b"),), "beta: the boxed part's key alone"
    assert split.boxed == (False, True)
    assert split.rows == (2, 1) and split.columns == (3, 2)


def test_the_split_form_of_two_boxed_blocks_and_of_none() -> None:
    q, p = _analyser(math.pi / 7), _analyser(math.pi / 5)
    exact = certified._exact_element(_matrix([[1, 0], [0, 1]]))
    with balls.precision(128):
        both = certified._product(
            [_boxed_projector(q), _boxed_projector(p)], [_key(0, "a"), _key(1, "b")]
        )
        none = certified._product([exact, exact], [_key(0, "a"), _key(1, "b")])
    assert both.split is not None
    assert both.split.exact == ((_cx(1),),), "no exact part: [[1]]"
    assert both.split.box.shape == (1, 4)
    assert both.split.blocks == (_key(0, "a"), _key(1, "b")), "factor order"
    assert none.split is None and none.form is not None
    assert not isinstance(none.form[0], Ball)


def test_the_tuple_names_the_blocks_and_not_their_boxes() -> None:
    """One block's element under two keys: equal boxes, two distinct tuples."""
    one = certified._exact_element(((_cx(1),),))
    with balls.precision(128):
        boxed = _boxed_projector(_analyser(math.pi / 7))
        first = certified._product([one, boxed], [_key(0, "a"), _key(1, "b")])
        second = certified._product([one, boxed], [_key(0, "a"), _key(1, "c")])
    assert first.split is not None and second.split is not None
    assert first.split.box.shape == second.split.box.shape
    assert first.split.blocks != second.split.blocks


def test_a_product_needs_one_key_per_part() -> None:
    one = certified._exact_element(((_cx(1),),))
    with pytest.raises(
        certified._Fail, match=r"^boxed_form_inconsistent: .*block keys"
    ):
        certified._product([one, one], [_key(0, "a")])


# The reordering, exactly


#: Three factors' (rows, columns) and every non-empty placement of the boxes.
DIMS = ((2, 3), (1, 2), (3, 2))
MASKS = [m for m in itertools.product((False, True), repeat=3) if any(m)]


def _factors() -> list[tuple[tuple[Cx, ...], ...]]:
    """Three integer matrices whose entries are all distinct."""
    counter = itertools.count(1)
    return [
        _matrix([[next(counter) for _ in range(n)] for _ in range(p)]) for p, n in DIMS
    ]


def _mask_id(mask: tuple[bool, ...]) -> str:
    return "".join("B" if held else "x" for held in mask)


def _kron_all(parts: Any) -> Any:
    out: Any = ((_cx(1),),)
    for part in parts:
        out = kron(out, part)
    return out


@pytest.mark.parametrize("boxed", MASKS, ids=_mask_id)
def test_the_reordering_of_an_element(boxed: tuple[bool, ...]) -> None:
    """``E_v[iv, cv] = (E^ex (x) E^box)[R_v^T iv, Sigma(n) cv]``, entry by entry."""
    parts = _factors()
    e_v = _kron_all(parts)
    e_ex = _kron_all(p for p, held in zip(parts, boxed, strict=True) if not held)
    e_box = _kron_all(p for p, held in zip(parts, boxed, strict=True) if held)
    product = kron(e_ex, e_box)
    rows, columns = [p for p, _ in DIMS], [n for _, n in DIMS]
    k = math.prod(p for p, held in zip(rows, boxed, strict=True) if held)
    n_box = math.prod(n for n, held in zip(columns, boxed, strict=True) if held)
    seen = set()
    for iv in range(math.prod(rows)):
        i_ex, i_box = certified._radix_split(iv, rows, boxed)
        seen.add((i_ex, i_box))
        for cv in range(math.prod(columns)):
            c_ex, c_box = certified._radix_split(cv, columns, boxed)
            assert e_v[iv][cv] == product[i_ex * k + i_box][c_ex * n_box + c_box]
    assert len(seen) == math.prod(rows), "R_v is a permutation"


@pytest.mark.parametrize("boxed", MASKS, ids=_mask_id)
def test_the_stacked_rows_of_a_pair(boxed: tuple[bool, ...]) -> None:
    """``E_x (x) E_v = (1 (x) R_v)((E_x (x) E^ex) (x) E^box) U_beta``, exactly.

    Alice's ``E_x`` of two rows on a space of two; :func:`certified._columns`
    gives ``U_beta = 1_a (x) Sigma_beta(n)`` as the column order of
    ``(E_x (x) E^ex) (x) E^box``.
    """
    parts = _factors()
    e_x = _matrix([[1, 2], [3, 5]])
    target = kron(e_x, _kron_all(parts))
    e_ex = _kron_all(p for p, held in zip(parts, boxed, strict=True) if not held)
    e_box = _kron_all(p for p, held in zip(parts, boxed, strict=True) if held)
    raw = kron(kron(e_x, e_ex), e_box)
    rows, columns = tuple(p for p, _ in DIMS), tuple(n for _, n in DIMS)
    split = certified._Split(e_ex, Ball.of(e_box), (), boxed, rows, columns)
    order = certified._columns(split, len(raw[0]))
    assert sorted(order) == list(range(len(raw[0]))), "U_beta is a permutation"
    k, height = len(e_box), len(e_ex)
    for ix in range(len(e_x)):
        for iv in range(math.prod(rows)):
            i_ex, i_box = certified._radix_split(iv, rows, boxed)
            source = raw[(ix * height + i_ex) * k + i_box]
            assert tuple(source[c] for c in order) == target[ix * math.prod(rows) + iv]


# The grouping


def test_tuples_sharing_one_boxed_block_but_not_another_are_two_groups() -> None:
    """``(a, b)`` and ``(a, c)``, every block boxed, ``b`` and ``c`` with equal boxes.

    The tuples share the block ``a`` and differ in ``b`` against ``c``, so the
    class has two groups and ``C`` two rows, whatever the boxes: here ``b`` and
    ``c`` are read through one box object. A grouping by the shared block alone,
    or by the boxes, would leave one group and one row.
    """
    q = _analyser(math.pi / 7)
    one = ((_cx(1),),)
    with balls.precision(128):
        a, shared_box = _boxed_projector(q), _boxed_projector(_analyser(math.pi / 5))
        first = certified._product([a, shared_box], [_key(0, "a"), _key(1, "b")])
        second = certified._product([a, shared_box], [_key(0, "a"), _key(1, "c")])
        klass = certified._class([_row(one, first, 0), _row(one, second, 1)])
    assert klass is not None and klass.c.shape == (2, 4)


def test_tuples_sharing_one_block_and_differing_in_another_certify_as_exact() -> None:
    """``(a, b)`` and ``(a, c)`` with ``b``, ``c`` at different analysers: as exact."""
    q, p, r = (_analyser(math.pi / d) for d in (7, 5, 3))
    one = ((_cx(1),),)
    keys = {"a": _key(0, "a"), "b": _key(1, "b"), "c": _key(1, "c")}
    with balls.precision(128):

        def klass(read: Any) -> Any:
            first = certified._product([read(q), read(p)], [keys["a"], keys["b"]])
            second = certified._product([read(q), read(r)], [keys["a"], keys["c"]])
            return certified._class([_row(one, first, 0), _row(one, second, 1)])

        boxed = klass(_boxed_projector)
        assert boxed is not None and boxed.c.shape == (2, 4)
        _agree(boxed, klass(_exact_projector), 4)


def test_a_block_boxed_in_one_element_and_exact_in_another_parts_the_groups() -> None:
    """``(a, b)`` with both boxed and ``(a, x)`` with ``x`` exact: two tuples.

    ``((0, a), (1, b))`` against ``((0, a),)``: the elements share the boxed
    block ``a`` and differ in whether their other block is boxed, so they are
    two groups, ``C`` stacking ``C_beta (x) E^box_beta`` for each; the deficit
    is the exact member's.
    """
    q, p, r = (_analyser(math.pi / d) for d in (7, 5, 3))
    one = ((_cx(1),),)
    with balls.precision(128):

        def klass(read: Any) -> Any:
            first = certified._product([read(q), read(p)], [_key(0, "a"), _key(1, "b")])
            second = certified._product(
                [read(q), _exact_projector(r)], [_key(0, "a"), _key(1, "x")]
            )
            if read is _boxed_projector:
                assert first.split is not None and second.split is not None
                assert first.split.blocks == (_key(0, "a"), _key(1, "b"))
                assert second.split.blocks == (_key(0, "a"),)
            return certified._class([_row(one, first, 0), _row(one, second, 1)])

        boxed = klass(_boxed_projector)
        assert boxed is not None and boxed.c.shape == (2, 4)
        _agree(boxed, klass(_exact_projector), 4)


def test_one_tuple_at_two_placements_is_refused() -> None:
    """A tuple whose rows disagree on the boxed positions is a defect, not a group."""
    box = Ball.of(_matrix([[1, 0]]))
    block = _key(0, "a")
    left = certified._Split(((_cx(1),),), box, (block,), (True, False), (1, 1), (2, 1))
    right = certified._Split(((_cx(1),),), box, (block,), (False, True), (1, 1), (1, 2))
    one, core = ((_cx(1),),), Ball.of([[_cx(1)]])
    with balls.precision(128), pytest.raises(
        certified._Fail, match=r"^boxed_form_inconsistent: .*two positions"
    ):
        certified._class(
            [
                certified._Row(one, box, core, 0, left),
                certified._Row(one, box, core, 1, right),
            ]
        )


# The stack against the exact member


def test_a_rank_two_box_at_position_zero_shared_by_two_stacks_as_exact() -> None:
    """``R_v`` and ``Sigma_beta(n)`` both non-trivial, one shared boxed block.

    The block ``L L^T`` (dimension 3, rank 2, :func:`_rank_two`) at factor
    position 0, boxed with ``k = 2``, times ``diag(1, 2)`` (``v``: ``p = (2, 2)``,
    ``n = (3, 2)``) and times ``diag(0, 1)`` (``w``: ``p = (2, 1)``). Both
    elements have the tuple of the one block, so they are one group; Alice's
    ``E_x1 = (1, 0)``, ``E_x2 = (0, 1)`` with raw keys 0 and 1. The deficit and
    its gradient at a Choi block of dimension 12 with no symmetry are those of
    the exact member, which a stack without ``U_beta``'s permutation or
    without ``R_v`` in ``B~`` does not give.
    """
    v = certified._exact_element(_matrix([[1, 0], [0, 2]]))
    w = certified._exact_element(_matrix([[0, 0], [0, 1]]))
    alice = [_matrix([[1, 0]]), _matrix([[0, 1]])]
    with balls.precision(128):
        boxed, exact = _rank_two()

        def klass(block: Any) -> Any:
            rows = []
            for letter, part in (("v", v), ("w", w)):
                element = certified._product(
                    [block, part], [_key(0, "L"), _key(1, letter)]
                )
                rows.extend(_row(e_x, element, key) for key, e_x in enumerate(alice))
            return certified._class(rows)

        by_box = klass(boxed)
        # S_beta: E_x (x) E^ex over v's two rows and w's one, which lies in their
        # span: rank 4, so C has 4 k = 8 rows (per element it would have 12).
        assert by_box is not None and by_box.c.shape == (8, 12)
        _agree(by_box, klass(exact), 12)


# E~ = B~ C on random classes


def _diag(values: Any) -> Ball:
    n = len(values)
    return Ball.of(
        _matrix([[values[i] if i == j else 0 for j in range(n)] for i in range(n)])
    )


def _full_row_rank(rng: random.Random, p: int, n: int) -> Any:
    """Return a random integer ``p x n`` matrix of full row rank."""
    while True:
        e = _matrix([[rng.randint(-3, 3) for _ in range(n)] for _ in range(p)])
        if len(rank_factorisation(e)[1]) == p:
            return e


def _gram(rows: Any, weights: Any) -> Any:
    """Return ``E^dagger D E`` of real rows ``E`` and diagonal weights ``D``."""
    width = len(rows[0])
    return [
        [
            sum(
                (w * r[c].re * r[d].re for r, w in zip(rows, weights, strict=True)),
                F(0),
            )
            for d in range(width)
        ]
        for c in range(width)
    ]


def _equal(ball: Ball, exact: Any) -> bool:
    """Return whether each entry of ``ball`` holds ``exact``'s, radius below 1e-20."""
    n = len(exact)
    return all(
        ball.m[i, j].overlaps(balls.flint.acb(balls.real(exact[i][j]), 0))
        and float(ball.m[i, j].rad()) < 1e-20
        for i in range(n)
        for j in range(n)
    )


@pytest.mark.parametrize("seed", range(40))
def test_the_class_stack_is_b_tilde_c_on_random_classes(seed: int) -> None:
    """``lem:certified-bracket-enclosed`` (b), the stack: ``E~ = B~ C``.

    Random classes over two or three factors, each block exact or boxed (a box
    of radius 0 around an integer matrix of full row rank, so the member is
    exact), blocks shared between elements and Alice's factors repeated. With
    ``D`` the cores, ``C^dagger G C = E~^dagger D E~`` and, per raw key ``j``,
    ``(R_j F_j R_G C)^dagger (R_j F_j R_G C) = E~_j^dagger D_j E~_j``.
    """
    rng = random.Random(seed)
    m, a = rng.choice([2, 3]), rng.randint(1, 3)
    blocks: dict[Any, Any] = {}
    for j in range(m):
        n = rng.randint(1, 3)
        for letter in "uvw"[: rng.randint(1, 3)]:
            p = rng.randint(1, n)
            e = _full_row_rank(rng, p, n)
            factor = Ball.of(e) if rng.random() < 0.6 else e
            form = (factor, _diag([rng.randint(1, 4) for _ in range(p)]))
            element = certified._Element(Ball.of(_matrix([[0]])), False, form)
            blocks[(j, letter, "s")] = (e, element)
    alice = [
        _full_row_rank(rng, rng.randint(1, a), a) for _ in range(rng.randint(1, 3))
    ]
    alice += alice[:1]
    rows, stack, weights, labels = [], [], [], []
    with balls.precision(128):
        for _ in range(rng.randint(2, 6)):
            keys = [rng.choice([k for k in blocks if k[0] == j]) for j in range(m)]
            element = certified._product([blocks[k][1] for k in keys], keys)
            e_v = _kron_all(blocks[k][0] for k in keys)
            e_x, key = rng.choice(alice), rng.randint(0, 1)
            d = [rng.randint(1, 9) for _ in range(len(e_x) * len(e_v))]
            assert element.form is not None
            rows.append(
                certified._Row(e_x, element.form[0], _diag(d), key, element.split)
            )
            block = kron(e_x, e_v)
            stack += block
            weights += d
            labels += [key] * len(block)
        klass = certified._class(rows)
        assert klass is not None
        c = klass.c
        assert _equal(c.adjoint @ klass.gram @ c, _gram(stack, weights))
        pinched = iter(klass.labels)
        for key in sorted(set(labels)):
            f_j, r_j = next(pinched)
            mine = [i for i, label in enumerate(labels) if label == key]
            inner = r_j @ f_j @ klass.root @ c
            expected = _gram([stack[i] for i in mine], [weights[i] for i in mine])
            assert _equal(inner.adjoint @ inner, expected)
