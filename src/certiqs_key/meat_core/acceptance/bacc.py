"""``beta_acc``: the acceptance half of Eq. ``eq:lmo``, discharged not assumed.

THE CLAIM. Remark ``rem:acc-side`` records that the acceptance half of
Eq. ``eq:lmo`` is DISCHARGED, not assumed, and Eq. ``eq:bacc-def`` is what
discharges it. (The feasible half is bounded from the oracle's dual,
``frank-wolfe/req:verified-feasible-side``.) The bound and its witness belong
to ``rem:acc-side``, which owns them.

THE ARITHMETIC. The remark says how: the acceptance-side minimization is
solved EXACTLY OVER THE RATIONALS in geometry (b), on the exact island of the
conventions, where the acceptance data are exact rationals and are "the single
exception to the binary64 number model". So the type is
:class:`fractions.Fraction`, from the standard library, and no optional
dependency is needed. No interval-arithmetic assumption is involved
(PRINCIPLES.md section 10).

NOTHING HERE ROUNDS: both functions return an
EXACT rational, and :func:`float_below` is the one place a rational becomes a
machine number, downward, where a caller needs one.

TWO GEOMETRIES, AND A DECLARATION FITTING NEITHER IS REFUSED. Remark
``rem:acc-side`` (a) is the singleton, where "the minimum is the single
evaluation, attained at ``v_t = q^*``"; (b) is the polytope. A declaration
whose acceptance set fits neither is refused at admission, before any solve,
and no first-order bound is formed for it (``req:acceptance-geometries``).

OPEN IMPLEMENTATION CHOICE OC-8, NARROWED AND NOT DECIDED. The remark admits
TWO routes for the acceptance half -- a point attaining the minimum, or a
certified bound satisfying Eq. ``eq:bacc-def`` -- and leaves to an
implementation "whether it computes the vertex or the bound on a geometry where
both are available". The Frank-Wolfe driver computes THE VERTEX, through the
acceptance oracle, in both geometries; these functions are the OTHER route, and
they are kept because the frozen registry pins them. A run
that takes this route RECORDS WHICH OF THE TWO IT USED, which is what the
remark requires of either.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from fractions import Fraction


def float_below(value: Fraction) -> float:
    """Return the largest binary64 at or below the exact rational ``value``.

    THE ONE PLACE A RATIONAL BECOMES A MACHINE NUMBER, and it rounds DOWNWARD
    because every consumer of ``beta_acc`` adds it to a lower bound: rounding up
    could raise a bound above the quantity it bounds, which is the unsafe
    direction.

    ``float(value)`` rounds to NEAREST, so it may land above; one step towards
    ``-inf`` corrects it, and the step is taken only when it is needed, so an
    exactly representable value is returned exactly.
    """
    nearest = float(value)
    if Fraction(nearest) > value:
        return math.nextafter(nearest, -math.inf)
    return nearest


def beta_acc_singleton(
    surrogate: Mapping[str, float],
    frequencies: Mapping[str, float],
    support: Sequence[str],
) -> Fraction:
    """Return ``beta_acc`` for a SINGLETON acceptance set, Remark ``rem:acc-side`` (a).

    "Any downward-rounded evaluation of ``sum_chat g(chat) q*(chat)``". The sum
    is over the acceptance support only, which is where ``q*`` has all its mass
    and where the surrogate ``g`` is defined. It is returned EXACTLY; the
    downward rounding happens once, at the site that needs a machine number,
    where the sign convention is unambiguous.
    """
    total = Fraction(0)
    for chat in support:
        total = total + Fraction(surrogate[chat]) * Fraction(frequencies[chat])
    return total


def beta_acc_polytope(
    surrogate: Sequence[float],
    rows: Sequence[Sequence[float]],
    bounds: Sequence[float],
    multipliers: Sequence[float],
    offset: float,
) -> Fraction | None:
    """Return ``beta_acc`` for a POLYTOPE acceptance set, Remark ``rem:acc-side`` (b).

    For ``AcceptSet = {q >= 0, sum q = 1, B q <= b}`` and any ``u >= 0``,
    ``v in R`` with ``g + B^T u + v >= 0`` componentwise::

        min_{q'} <g, q'> >= -<b, u> - v .

    The admissibility condition is a componentwise sign check on an exactly
    represented vector; there is no reason to skip it and no way for it to be
    expensive. ``None`` is returned when it fails -- the recipe's number is then
    NOT A BOUND, and would exceed the true minimum, which is the direction that
    matters.

    ``B`` has one column per element of the ACCEPTANCE SUPPORT, not per element
    of ``Chat``: every ``q`` in ``AcceptSet`` is supported there, so coordinates
    outside it carry no mass and are omitted.

    WHAT THIS IS NOT. It is not a reading of a backend's DUAL OBJECTIVE, which
    Requirement ``req:primal-pairing`` forbids by name: an interior-point return is
    only approximately dual-feasible and the corrected bound carries a term of
    UNKNOWN SIGN. Here the multipliers are given and their admissibility is
    CHECKED exactly, which is what makes the inequality hold rather than
    approximately hold.
    """
    if any(len(row) != len(surrogate) for row in rows):
        raise ValueError(
            "each row of B must have one column per acceptance-support element"
        )
    if len(bounds) != len(rows) or len(multipliers) != len(rows):
        raise ValueError("b and u must have one entry per row of B")
    zero = Fraction(0)
    if any(Fraction(value) < zero for value in multipliers):
        return None
    shifted_offset = Fraction(offset)
    for column, coefficient in enumerate(surrogate):
        total = Fraction(coefficient) + shifted_offset
        for row_index, row in enumerate(rows):
            total = total + Fraction(row[column]) * Fraction(multipliers[row_index])
        if total < zero:
            return None
    result = -shifted_offset
    for row_index, bound in enumerate(bounds):
        result = result - Fraction(bound) * Fraction(multipliers[row_index])
    return result
