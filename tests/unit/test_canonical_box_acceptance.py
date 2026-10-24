"""Exact box optimization against independently enumerated vertices and LPs."""

import random
from dataclasses import replace
from fractions import Fraction
from itertools import product

import pytest

from certiqs_key.meat_core.acceptance.box import canonical_box
from certiqs_key.meat_core.acceptance.geometry import (
    acceptance_minimum,
    polytope_support,
)
from certiqs_key.meat_core.declaration.declaration import PolytopeData


def box_data(lower: tuple[float, ...], upper: tuple[float, ...]) -> PolytopeData:
    size = len(lower)
    return PolytopeData(
        columns=size,
        rows=tuple(tuple(float(i == j) for j in range(size)) for i in range(size))
        + tuple(tuple(-float(i == j) for j in range(size)) for i in range(size)),
        rhs=(*upper, *(-v for v in lower)),
        box_bounds=(lower, upper),
    )


def vertices(
    lower: tuple[float, ...], upper: tuple[float, ...]
) -> set[tuple[Fraction, ...]]:
    low, high = tuple(map(Fraction, lower)), tuple(map(Fraction, upper))
    found = set()
    for free in range(len(low)):
        fixed = [i for i in range(len(low)) if i != free]
        for choices in product((False, True), repeat=len(fixed)):
            point = list(low)
            for i, choice in zip(fixed, choices, strict=True):
                point[i] = high[i] if choice else low[i]
            point[free] = 1 - sum(point[i] for i in fixed)
            if low[free] <= point[free] <= high[free]:
                found.add(tuple(point))
    return found


@pytest.mark.parametrize("seed", range(40))
def test_exact_box_matches_vertices_and_generic_simplex(seed: int):
    rng = random.Random(seed)
    size = rng.randint(2, 4)
    lower = tuple(rng.randrange(0, 5) / 16 for _ in range(size))
    upper = tuple(
        value + rng.randrange(0, 17 - int(value * 16)) / 16 for value in lower
    )
    cost = tuple(float(rng.randrange(-4, 5)) for _ in range(size))
    data = box_data(lower, upper)
    box = canonical_box(data)
    assert box is not None
    result = box.minimum(cost)
    points = vertices(lower, upper)
    if not points:
        assert result is None
        return
    assert result is not None
    expected = min(
        sum((Fraction(g) * q for g, q in zip(cost, p, strict=True)), Fraction())
        for p in points
    )
    generic = acceptance_minimum(cost, data)
    assert generic is not None
    assert result.minimum == expected == generic.minimum
    assert result.argmin in points
    assert sum(result.argmin, Fraction()) == 1
    assert all(u >= 0 for u in result.multipliers)
    for j, g in enumerate(cost):
        assert (
            Fraction(g)
            + result.offset
            + sum(
                (
                    Fraction(row[j]) * u
                    for row, u in zip(data.rows, result.multipliers, strict=True)
                ),
                Fraction(),
            )
            == 0
        )
    assert (
        -result.offset
        - sum(
            (
                Fraction(b) * u
                for b, u in zip(data.rhs, result.multipliers, strict=True)
            ),
            Fraction(),
        )
        == expected
    )
    support, start = box.support_and_start()
    assert support == polytope_support(data)
    assert sum(start) == pytest.approx(1.0, abs=1e-15)
    assert all(lo <= q <= hi for lo, q, hi in zip(lower, start, upper, strict=True))
    assert tuple(i for i, q in enumerate(start) if q > 0) == support


def test_only_verified_canonical_rows_select_box_dispatch():
    data = box_data((0.0, 0.0), (1.0, 1.0))
    # Exact signed-coordinate rows establish the box without optional metadata.
    assert canonical_box(replace(data, box_bounds=None)) == canonical_box(data)
    assert canonical_box(replace(data, rows=((2.0, 0.0), *data.rows[1:]))) is None
    assert (
        canonical_box(replace(data, box_bounds=None, rows=((2.0, 0.0), *data.rows[1:])))
        is None
    )
    assert canonical_box(replace(data, box_bounds=((0.75, 0.0), (0.25, 1.0)))) is None


def test_box_exact_support_survives_underflow_and_fixed_simplex_face():
    tiny = float.fromhex("0x0.0000000000001p-1022")
    box = canonical_box(box_data((0.0, 0.0), (tiny, 1.0)))
    assert box is not None
    assert box.support_and_start() == ((0, 1), (0.0, 1.0))
    fixed = canonical_box(box_data((0.25, 0.75), (0.5, 1.0)))
    assert fixed is not None
    result = fixed.minimum((-3.0, 2.0))
    assert result is not None
    assert result.argmin == (Fraction(1, 4), Fraction(3, 4))
