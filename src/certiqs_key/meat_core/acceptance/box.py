"""Exact canonical-box LP implementation for general solves only.

Newly-derived implementation argument, not a new accepted claim: for
l <= q <= u and sum(q)=1, start at l and allocate the remaining mass in
nondecreasing cost order. If a more expensive coordinate has allocated mass
while a cheaper coordinate has remaining capacity, transferring the lesser
of these amounts cannot increase cost. Repeating yields this greedy point.

An independent exact dual check accompanies the construction. Let theta be
the last filled cost (the minimum cost if no mass was needed). For the
canonical rows (+I,-I), take upper multipliers max(theta-g,0), lower
multipliers max(g-theta,0), and offset -theta. They are nonnegative and
satisfy g + B^T multipliers + offset = 0. Complementary slackness follows
from the fill order, so the dual value equals the primal cost exactly.

Metadata whose actual rows pass the existing canonical-box predicate, or an
exact list containing one upper and one lower unit-coordinate row per column,
selects this algorithm. Other polytopes use the unchanged rational simplex.
No tolerance, floating rank decision, or altered acceptance set is involved.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.meat_core.acceptance.geometry import AcceptanceMinimum, polytope_defect
from certiqs_key.meat_core.declaration.declaration import PolytopeData


@dataclass(frozen=True)
class CanonicalBox:
    """Exact bounds of an already validated canonical box intersected with simplex."""

    lower: tuple[Fraction, ...]
    upper: tuple[Fraction, ...]

    def minimum(self, surrogate: Sequence[float]) -> AcceptanceMinimum | None:
        """Return an exact primal/dual optimum, or None for an empty box."""
        if len(surrogate) != len(self.lower):
            raise ValueError("box cost and declared coordinates disagree")
        if any(not math.isfinite(value) for value in surrogate):
            return None
        cost = tuple(Fraction(value) for value in surrogate)
        remaining = 1 - sum(self.lower, Fraction())
        capacity = sum(self.upper, Fraction()) - sum(self.lower, Fraction())
        if remaining < 0 or remaining > capacity:
            return None
        point = list(self.lower)
        threshold = min(cost)
        for index in sorted(range(len(cost)), key=lambda i: (cost[i], i)):
            if remaining == 0:
                break
            moved = min(remaining, self.upper[index] - self.lower[index])
            point[index] += moved
            remaining -= moved
            if moved > 0:
                threshold = cost[index]
        if remaining != 0:
            raise AssertionError("exact box allocation did not exhaust its residual")
        upper_dual = tuple(max(threshold - value, Fraction()) for value in cost)
        lower_dual = tuple(max(value - threshold, Fraction()) for value in cost)
        objective = sum((g * q for g, q in zip(cost, point, strict=True)), Fraction())
        dual = threshold - sum(
            (u * b for u, b in zip(upper_dual, self.upper, strict=True)), Fraction()
        )
        dual += sum(
            (u * b for u, b in zip(lower_dual, self.lower, strict=True)), Fraction()
        )
        if dual != objective:
            raise AssertionError("exact box primal and dual objectives disagree")
        return AcceptanceMinimum(
            objective, tuple(point), (*upper_dual, *lower_dual), -threshold
        )

    def support_and_start(self) -> tuple[tuple[int, ...], tuple[float, ...]] | None:
        """Use exact coordinate maximizers for support and their averaged start."""
        prepared = self.support_and_exact_start()
        if prepared is None:
            return None
        support, start = prepared
        return support, tuple(float(value) for value in start)

    def support_and_exact_start(
        self,
    ) -> tuple[tuple[int, ...], tuple[Fraction, ...]] | None:
        """Return :meth:`support_and_start` with the averaged start kept exact.

        Remark ``rem:acc-side`` (alpha): the acceptance-side iterate starts at
        an exact rational point of the set, which the average is and its
        binary64 rounding in general is not.
        """
        size = len(self.lower)
        points = []
        for index in range(size):
            result = self.minimum(
                tuple(-1.0 if i == index else 0.0 for i in range(size))
            )
            if result is None:
                return None
            points.append(result.argmin)
        support = tuple(i for i, point in enumerate(points) if point[i] > 0)
        start = tuple(
            sum((p[i] for p in points), Fraction()) / size for i in range(size)
        )
        return support, start


def canonical_box(data: PolytopeData) -> CanonicalBox | None:
    """Recognize exact signed-coordinate boxes, with or without box metadata.

    The row-only case requires exactly one row of each sign per coordinate.
    No numerical geometry inference or removal of redundant rows is performed.
    ``minimum`` supplies a dual in canonical (+I,-I) order, not input row order;
    consumers of a declared-row witness continue to use the rational LP.
    """
    if polytope_defect(data) is not None:
        return None
    if data.box_bounds is not None:
        lower, upper = data.box_bounds
        return CanonicalBox(
            tuple(Fraction(v) for v in lower), tuple(Fraction(v) for v in upper)
        )
    bounds: dict[tuple[int, int], Fraction] = {}
    for row, rhs in zip(data.rows, data.rhs, strict=True):
        nonzero = [(i, Fraction(v)) for i, v in enumerate(row) if v != 0]
        if len(nonzero) != 1:
            return None
        index, coefficient = nonzero[0]
        if coefficient not in (-1, 1):
            return None
        key = (index, int(coefficient))
        if key in bounds:
            return None
        bounds[key] = Fraction(rhs) * coefficient
    if len(bounds) != 2 * data.columns:
        return None
    lows = tuple(bounds[i, -1] for i in range(data.columns))
    highs = tuple(bounds[i, 1] for i in range(data.columns))
    if any(not 0 <= low <= high for low, high in zip(lows, highs, strict=True)):
        return None
    return CanonicalBox(lows, highs)
