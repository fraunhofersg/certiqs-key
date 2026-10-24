"""The enclosed reference against the frozen exact blocks (registry RC5, RC6).

Golden replay of ``FOCK_CASES`` and ``POVM_BLOCK_CASES`` of the receiver
registry, whose values are frozen EXACTLY in ``Q[sqrt2] + i Q[sqrt2]``: the
enclosures the generic pipeline computes in exact rational arithmetic
(``receiver/thm:enclosed-blocks``, ``receiver/lem:fock-permanent``) must
CONTAIN every frozen value, and must be EXACT -- radius zero, centre equal to
the frozen value -- wherever ``receiver/thm:exact-blocks`` says so: Gaussian-
rational inputs and occupation vectors whose factorial product is a square.

Containment of an irrational frozen value ``a + b sqrt2`` is decided with
rational bounds on ``sqrt 2`` far tighter than any radius: the distance from
the centre is convex, so its largest value over the box the bounds give is
attained at a corner, and that corner value is compared with the radius
exactly.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest
from registry_receiver_povm import (
    FOCK_CASES,
    INSTRUMENT_CASES,
    POVM_BLOCK_CASES,
    Alg,
    FockCase,
    Mat,
    POVMBlockCase,
)

from certiqs_key.receiver.enclosure import Ball, sqrt_enclosure
from certiqs_key.receiver.generic import (
    BallField,
    element_blocks,
    fock_block,
    unconditioned_pairs,
)

pytestmark = pytest.mark.oracle

#: Rational bounds on sqrt 2 at 2^-400, for the containment decisions.
_ROOT2_LO = Fraction(math.isqrt(2 << 800), 1 << 400)
_ROOT2_HI = _ROOT2_LO + Fraction(1, 1 << 400)


def _ball(value: Alg, field: BallField) -> Ball:
    """Return an enclosure of ``(a + b sqrt2) + i (c + d sqrt2)`` from leaves."""
    (a, b), (c, d) = value
    root = field.sqrt(Fraction(2))
    real = Ball(a) + Ball(b) * root
    imag = Ball(c) + Ball(d) * root
    return real + Ball(Fraction(0), Fraction(1)) * imag


def _matrix(value: Mat, field: BallField) -> list[list[Ball]]:
    return [[_ball(entry, field) for entry in row] for row in value]


def _is_rational(value: Alg) -> bool:
    (_, b), (_, d) = value
    return b == 0 and d == 0


def _contains(ball: Ball, value: Alg) -> bool:
    """Decide that every point of the sqrt2-box of ``value`` lies in ``ball``."""
    (a, b), (c, d) = value
    if ball.radius == 0:
        return _is_rational(value) and ball.re == a and ball.im == c
    worst = Fraction(0)
    for re_root in (_ROOT2_LO, _ROOT2_HI):
        for im_root in (_ROOT2_LO, _ROOT2_HI):
            dx = a + b * re_root - ball.re
            dy = c + d * im_root - ball.im
            worst = max(worst, dx * dx + dy * dy)
    return worst <= ball.radius * ball.radius


def _square(vector_a: tuple[int, ...], vector_b: tuple[int, ...]) -> bool:
    product = math.prod(math.factorial(m) for m in vector_a) * math.prod(
        math.factorial(m) for m in vector_b
    )
    root = math.isqrt(product)
    return root * root == product


@pytest.mark.parametrize("case", FOCK_CASES, ids=lambda case: case.case_id)
def test_the_permanent_entries_enclose_the_frozen_fock_block(case: FockCase) -> None:
    """``lem:fock-permanent``: ``per X[m|m'] / sqrt(m! m'!)``, enclosed and exact."""
    field = BallField()
    operator = _matrix(case.operator, field)
    block = fock_block(field, operator, case.photon_number)
    basis = case.basis_order
    rational_operator = all(
        _is_rational(entry) for row in case.operator for entry in row
    )
    for i, row in enumerate(case.block):
        for j, value in enumerate(row):
            entry = block[i][j]
            assert _contains(entry, value), (case.case_id, i, j)
            if rational_operator and _square(basis[i], basis[j]):
                # lem:fock-permanent (ii) with lem:enclosure-arithmetic (iv).
                assert entry.is_exact, (case.case_id, i, j)


@pytest.mark.parametrize(
    "case",
    POVM_BLOCK_CASES,
    ids=lambda case: case.case_id,
)
def test_the_enclosed_click_pattern_blocks_contain_the_frozen_ones(
    case: POVMBlockCase,
) -> None:
    """``thm:enclosed-blocks`` (ii) and ``thm:exact-blocks`` (ii) on the frozen POVMs.

    The Grams are the registry's own, enclosed from ``sqrt 2`` leaves where an
    entry is irrational and exactly where it is rational; every frozen block
    entry lies in its enclosure, and with Gaussian-rational Grams the entries
    between occupation vectors with a square factorial product are exact.
    """
    instrument = next(
        c for c in INSTRUMENT_CASES if c.case_id == case.instrument_case_id
    )
    field = BallField()
    labels = tuple(label for label, _ in instrument.grams)
    grams = tuple(_matrix(gram, field) for _, gram in instrument.grams)
    rational_grams = all(
        _is_rational(entry)
        for _, gram in instrument.grams
        for row in gram
        for entry in row
    )
    pairs = unconditioned_pairs(field, grams)
    photons = case.photon_number
    blocks = element_blocks(field, pairs, len(labels), photons)
    basis = case.basis_order
    for pattern_labels, frozen in case.elements:
        pattern = frozenset(labels.index(label) for label in pattern_labels)
        block = blocks[pattern]
        for i, row in enumerate(frozen):
            for j, value in enumerate(row):
                assert _contains(block[i][j], value), (pattern_labels, i, j)
                if rational_grams and _square(basis[i], basis[j]):
                    assert block[i][j].is_exact, (pattern_labels, i, j)


def test_a_square_root_leaf_is_exact_exactly_on_squares() -> None:
    """``def:complex-enclosure``: exact where ``p`` is the square of a rational."""
    assert sqrt_enclosure(Fraction(9, 16)).is_exact
    assert sqrt_enclosure(Fraction(9, 16)).re == Fraction(3, 4)
    assert not sqrt_enclosure(Fraction(1, 2)).is_exact
