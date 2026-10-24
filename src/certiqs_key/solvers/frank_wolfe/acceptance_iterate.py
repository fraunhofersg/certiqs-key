"""The acceptance-side iterate ``q_t``: formed exactly, evaluated in binary64.

Remark ``rem:acc-side`` (alpha) and (beta), and Remarks ``rem:fo-interface``
and ``rem:fo-iterate-checks``. The membership hypothesis of Theorem
``thm:firstorder`` (ii) and (iiib) is on a PRODUCT, and its acceptance factor
``q_t in AcceptSet`` is not measured by anything: it is true BY CONSTRUCTION
when ``q_0`` is an exact rational point of the set and every update is a convex
combination, with exact rational weights, of exact points of the set. A run
that forms ``q_t`` in binary64 instead "has not met the membership hypothesis
and withdraws under (1) with reason ``iterate_not_feasible``" (item (1) is
Requirement ``req:first-order-withdrawal`` (iv)).

ON A CANONICAL BOX THE ITERATE IS NOT STEPPED. There the loop's ``q`` rule
(:mod:`~certiqs_key.solvers.frank_wolfe.q_rule`) forms ``q_t`` as the binary64
closed-form partial minimiser at ``J_t`` made an exact member of the box by
construction, and places it with :meth:`AcceptanceIterate.at` -- condition
(beta) with weight one. The convex-combination machinery below serves the
geometries that keep the vertex step: a general polytope, and a singleton,
where nothing moves.

WHY THIS MODULE EXISTS. On a POLYTOPE a ``q_t`` formed as a binary64 convex
combination would sit outside the set exactly at nearly every gate (24 of 25
measured) while every gate recorded ``acceptance_iterate_exact = True``. The
iterate is kept exact rather than withdrawn on every polytope.

HOW IT IS KEPT EXACT. The iterate carries two views:

* ``exact`` -- the iterate itself, as :class:`~fractions.Fraction` coordinates.
  The start and every vertex come exact from an
  :class:`~certiqs_key.solvers.oracles.acceptance.ExactAcceptanceOracle`, and a
  step ``s`` is a binary64 number, hence an exact dyadic rational, so
  ``(1 - s) q + s v`` formed over the rationals is exactly a convex combination
  of two points of the set;
* ``view`` -- its coordinatewise rounding to the nearest binary64 number. It is
  what the objective, the gradient and the pairings are EVALUATED at, the same
  unbudgeted evaluation arithmetic every other number of the bracket carries
  (Remark ``rem:fo-arithmetic``); it is never combined into the next iterate.

The line search still tries its steps on the binary64 view: which step is TAKEN
is a choice and needs no exactness, and a taken step is re-formed exactly
before anything is evaluated at it.

WHY THE EXACT POINT IS SHORTENED, AND WHY THAT IS SOUND. A step's dyadic
denominator multiplies into the iterate's, so the exact coordinates grow by
about 50 bits per taken step and rational arithmetic on them grows
superlinearly: measured, 2000 steps reach about 227k bits and cost 18.7 s in
the update alone, +19% on a 2000-iteration run. So when a coordinate passes
:data:`SHORTEN_ABOVE_BITS`, :class:`Shortener` looks for a SHORT exact point
next to it -- the exact values of the binary64 view, the sum repaired to
exactly one, and, if that lies an ulp outside a facet, the same point moved a
dyadic fraction ``2^-k`` of the way to the exact interior start -- and adopts
the first candidate the oracle's EXACT membership predicate admits. Condition
(beta) admits it: the adopted point is "a point already established to lie in
acSet", established over the rationals with no window, and the next update is
again a convex combination with exact weights. What this adds is a predicate a
candidate can fail, never one the ITERATE can fail: a rejected candidate is
discarded and the long exact point is kept, still in the set by construction.
The iterate moves by at most ``2^-20`` per coordinate, and every driver
re-evaluates the objective at a changed view.

WHERE EXACTNESS CANNOT BE KEPT, THE RECORD SAYS SO.

* An exact point that no candidate shortens past :data:`EXACT_BITS_CAP` bits
  is given up: the iterate continues in binary64, ``on_island`` is ``False``
  for good, and every gate after it withdraws under ``iterate_not_feasible``
  -- fail-closed and disclosed, never a claim of exactness at an unbounded
  cost.
* An oracle that is not an
  :class:`~certiqs_key.solvers.oracles.acceptance.ExactAcceptanceOracle` (a
  singleton, or a caller's own) gets the binary64 update of
  :func:`combine_frequencies`, which carries a coordinate the vertex leaves
  where it is EXACTLY. So a ``q`` that never moves -- a singleton, where the
  vertex is the point -- stays the declared exact point and keeps the oracle's
  flag, bit for bit as before; the first step that moves any coordinate in
  binary64 sets ``on_island`` to ``False`` for good.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction

from certiqs_key.solvers.oracles.acceptance import (
    AcceptanceOracle,
    ExactAcceptanceOracle,
)

#: An exact point is shortened once a numerator or denominator of it is longer
#: than this. An IMPLEMENTATION CHOICE, deciding no predicate: it only chooses
#: when to look for a shorter member, and a member found is as good as the
#: point it replaces. Above the size of the points the oracle hands out (a
#: shrunk pairwise atom is about 130 bits) so that it fires on growth only.
SHORTEN_ABOVE_BITS = 512

#: An exact point no candidate shortens is given up past this many bits: the
#: run continues in binary64 and withdraws its bracket from there on
#: (fail-closed). At 50 bits a step that is about 1300 steps with every
#: shortening refused, which on a polytope happens only with a set whose
#: every point lies on a facet that the binary64 view keeps missing.
EXACT_BITS_CAP = 1 << 16

#: The fractions of the way to the interior start a candidate is moved, tried
#: in order: none, then ``2^-50``, ``2^-40``, ``2^-30``, ``2^-20``.
_MIXES = (
    Fraction(0),
    Fraction(1, 1 << 50),
    Fraction(1, 1 << 40),
    Fraction(1, 1 << 30),
    Fraction(1, 1 << 20),
)


def exact_bits(values: Iterable[Fraction]) -> int:
    """Return the longest numerator or denominator of ``values``, in bits."""
    return max(
        (
            max(value.numerator.bit_length(), value.denominator.bit_length())
            for value in values
        ),
        default=0,
    )


def short_convex_weights(weights: Sequence[Fraction]) -> tuple[Fraction, ...]:
    """Return short exact weights next to ``weights``: non-negative, summing to 1.

    Each weight is replaced by the exact value of its binary64 rounding and the
    residual of the sum is put on the largest, which it cannot drive negative
    (the residual is a few ulps, the largest weight at least ``1/len``). A
    convex combination of points of the set with these weights is in the set,
    with no predicate at all -- which is how the pairwise rule shortens.
    """
    short = [Fraction(float(weight)) for weight in weights]
    largest = max(range(len(short)), key=lambda index: (short[index], -index))
    short[largest] += 1 - sum(short, Fraction(0))
    if short[largest] < 0:  # pragma: no cover - a residual of a few ulps
        raise ArithmeticError("the weight repair drove the largest weight negative")
    return tuple(short)


@dataclass(frozen=True)
class Shortener:
    """Finds a SHORT exact member of the acceptance set next to a long one.

    ``contains`` is the oracle's exact membership predicate and ``anchor`` the
    exact start, a point of the set positive on the whole acceptance support,
    toward which a candidate an ulp outside a facet is moved.
    """

    values: tuple[str, ...]
    anchor: tuple[Fraction, ...]
    contains: Callable[[Mapping[str, Fraction]], bool]

    def shorten(self, point: Sequence[Fraction]) -> tuple[Fraction, ...] | None:
        """Return a short exact member next to ``point``, or ``None`` if none is.

        ``point`` is in the layout order of ``values``. The candidates are
        :data:`_MIXES` applied to the repaired view; ``None`` means every one
        of them failed the exact predicate, and the caller keeps ``point``.
        """
        # The exact values of the binary64 view, the sum repaired to one (the
        # weight repair of short_convex_weights, applied to coordinates).
        candidate = short_convex_weights(point)
        for mix in _MIXES:
            if mix:
                moved = tuple(
                    value if value == target else value + mix * (target - value)
                    for value, target in zip(candidate, self.anchor, strict=True)
                )
            else:
                moved = candidate
            if all(value >= 0 for value in moved) and self.contains(
                dict(zip(self.values, moved, strict=True))
            ):
                return moved
        return None


def combine_frequencies(
    q: Mapping[str, float], vertex: Mapping[str, float], step: float
) -> dict[str, float]:
    """Return ``(1 - step) q + step s`` on the acceptance block, in binary64.

    A coordinate the vertex leaves where it is stays EXACTLY where it is. The
    mathematics says so -- ``(1 - t) x + t x = x`` -- and machine arithmetic does
    not: forming the combination anyway would move the coordinate by up to an
    ulp for no reason, which on a singleton acceptance set, where the whole
    direction is zero, would perturb every number a run reports. So the
    short-circuit is exactness, not an optimization.

    A binary64 combination that DOES move a coordinate is not on the exact
    island: the line search tries its steps with it, and
    :meth:`AcceptanceIterate.toward` records it as off the island whenever it
    becomes the iterate.
    """
    return {
        chat: (
            value
            if vertex[chat] == value
            else (1.0 - step) * value + step * vertex[chat]
        )
        for chat, value in q.items()
    }


@dataclass(frozen=True)
class AcceptanceVertex:
    """The acceptance oracle's return: its binary64 view and any exact point."""

    view: dict[str, float]
    exact: dict[str, Fraction] | None = None


@dataclass(frozen=True)
class AcceptanceIterate:
    """``q_t``: the binary64 view evaluated at, the exact point, and the record.

    ``on_island`` is Remark ``rem:fo-returned-point``'s record for the
    acceptance factor, "a recorded property, never a measurement": whether
    ``q_t`` was formed under (alpha) and (beta) of Remark ``rem:acc-side``.
    ``shortener`` is present exactly when the oracle can decide membership
    exactly, and bounds the size of ``exact``.
    """

    view: dict[str, float]
    exact: dict[str, Fraction] | None
    on_island: bool
    shortener: Shortener | None = field(default=None, compare=False, repr=False)

    @classmethod
    def start(cls, oracle: AcceptanceOracle) -> AcceptanceIterate:
        """Return ``q_0``: exact when the oracle can say it exactly.

        (alpha): an exact rational point of the set. For an exact oracle the
        view is the rounding of the exact start, which is what ``start()``
        returns; for any other oracle the start is what ``start()`` returns,
        and the flag is the oracle's own.
        """
        if isinstance(oracle, ExactAcceptanceOracle):
            exact = oracle.exact_start()
            shortener = Shortener(
                tuple(exact), tuple(exact.values()), oracle.exact_contains
            )
            return cls(_rounded(exact), exact, oracle.exact_island, shortener)
        return cls(oracle.start(), None, oracle.exact_island)

    def at(self, exact: Mapping[str, Fraction]) -> AcceptanceIterate:
        """Return the iterate at an exact point formed by the caller.

        The caller vouches for (beta); the record and the shortener carry over.
        """
        point = dict(exact)
        return AcceptanceIterate(_rounded(point), point, self.on_island, self.shortener)

    def toward(self, vertex: AcceptanceVertex, step: float) -> AcceptanceIterate:
        """Return ``(1 - step) q_t + step v``: exact when both ends are exact.

        (beta): with ``s = Fraction(step)`` -- exact, ``step`` being a binary64
        number -- the rational combination is a convex combination of two
        exact points of the set, so it is one too. A coordinate on which the
        two ends agree is carried as it is, in both views. The result is
        shortened when it has grown (the module docstring).

        Without an exact pair the binary64 combination is formed, and the flag
        survives only if no coordinate moved: the iterate is then the same
        point as before, which the induction already placed in the set.
        """
        if self.exact is not None and vertex.exact is not None:
            weight = Fraction(step)
            exact: dict[str, Fraction] = {}
            view: dict[str, float] = {}
            for chat, value in self.exact.items():
                target = vertex.exact[chat]
                if target == value:
                    exact[chat] = value
                    view[chat] = self.view[chat]
                else:
                    moved = value + weight * (target - value)
                    exact[chat] = moved
                    view[chat] = float(moved)
            return AcceptanceIterate(
                view, exact, self.on_island, self.shortener
            ).bounded()
        combined = combine_frequencies(self.view, vertex.view, step)
        return AcceptanceIterate(
            combined, None, self.on_island and combined == self.view
        )

    def bounded(self) -> AcceptanceIterate:
        """Return this iterate with its exact point kept short, or given up.

        Below :data:`SHORTEN_ABOVE_BITS` it is returned as it is. Above, the
        first short member the :class:`Shortener` finds replaces it. If none
        is found the long point is kept, until it passes
        :data:`EXACT_BITS_CAP`, where it is given up: binary64 from here on,
        off the island (the module docstring).
        """
        if self.exact is None or self.shortener is None:
            return self
        bits = exact_bits(self.exact.values())
        if bits <= SHORTEN_ABOVE_BITS:
            return self
        values = self.shortener.values
        short = self.shortener.shorten([self.exact[chat] for chat in values])
        if short is not None:
            return self.at(dict(zip(values, short, strict=True)))
        if bits > EXACT_BITS_CAP:
            return AcceptanceIterate(self.view, None, False)
        return self


def acceptance_vertex(
    oracle: AcceptanceOracle, cost: Mapping[str, float]
) -> AcceptanceVertex:
    """Return the oracle's minimizer of ``cost``: exact when it can say it exactly.

    ONE linear program either way: an exact oracle's view is the rounding of
    its exact vertex, which is what ``minimize`` would have returned.
    """
    if isinstance(oracle, ExactAcceptanceOracle):
        exact = oracle.exact_minimize(cost)
        return AcceptanceVertex(_rounded(exact), exact)
    return AcceptanceVertex(oracle.minimize(cost))


def _rounded(exact: Mapping[str, Fraction]) -> dict[str, float]:
    """Return the nearest binary64 number to each coordinate."""
    return {chat: float(value) for chat, value in exact.items()}


__all__ = [
    "EXACT_BITS_CAP",
    "SHORTEN_ABOVE_BITS",
    "AcceptanceIterate",
    "AcceptanceVertex",
    "Shortener",
    "acceptance_vertex",
    "combine_frequencies",
    "exact_bits",
    "short_convex_weights",
]
