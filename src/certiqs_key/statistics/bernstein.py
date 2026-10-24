"""prop:rule-bernstein -- the closed-form endpoint rule, n-monotone by design.

``lem:bernstein-tail`` proves, for ``N`` binomial ``(n, p)`` and
``v = n p (1 - p)``,

    Pr[N - np >= t] <= exp(-t^2 / (2 (v + t/3)))                (eq:bernstein)

and the same bound for the lower deviation, so that both tails are at most
``e^-L`` for every

    t >= t(L) = L/3 + sqrt((L/3)^2 + 2 v L) .                 (eq:bernstein-t)

``prop:rule-bernstein`` turns that into an endpoint rule, evaluated in exact
rational arithmetic with integer square roots and nothing else:

    R^- = max{0, floor(np - t^-)},   R^+ = min{n, ceil(np + t^+)}
                                                     (eq:bernstein-endpoints)

WHY IT IS CARRIED AT ALL. It is THE n-MONOTONE ALTERNATIVE. The exact rule's
emitted interval is not monotone in ``n`` (``thm:monotonicity-limits`` (v), with an
explicit ``n = 2`` against ``n = 3`` counterexample), which a consumer sweeping ``n``
sees as noise; this rule's half-width is strictly decreasing in ``n`` and is
``O(n^-1/2)`` (its (iii)). What it costs is a wider box: it is never narrower
than the exact rule's raw quantile interval, the quantiles being the extremal
admissible indices.

EVERY ROUNDING WIDENS, AND THAT IS A BINDING RULE AND NOT A PARAMETER
=====================================================================
``binomial-box/interface.yaml``, ``evaluation_parameters.the_bernstein_rule.
the_rounding_directions``: the budget term ``L`` is rounded UP, the deviation
``t`` is rounded UP, and the endpoints take a floor below and a ceiling above.
A larger ``L`` gives a larger ``t`` gives a wider interval, which is the one
direction a conservative evaluation (``def:conservative-evaluation``;
``binomial-box/lem:widening``) licenses. The monotonicity of the proposition's
(ii) requires in addition that the roundings be MONOTONE FUNCTIONS OF THEIR
ARGUMENTS at fixed parameters, AND A BARE INTEGER-SQUARE-ROOT BOUND IS NOT ONE:
the excess of Eq. ``eq:isqrt-bounds`` on ``c/d`` is ``1/(d 2^s)``, which
depends on the denominator, so at ``s = 0`` and ``j = 1`` the budgets
``eps = 1/2`` and ``eps = 4/9`` give ``L = 2`` and ``L = 3/2`` -- the LARGER budget
producing the LARGER deviation and the WIDER interval. EVERY ROUNDING ON THIS ROUTE IS
THEREFORE THE ONE ``prop:rule-bernstein`` (ii) PROVES MONOTONE: the argument of each
square root is first rounded up onto the fixed dyadic grid ``2^-s Z`` and the root is
the upper bound of Eq. ``eq:isqrt-bounds`` at that grid point with ``d = 2^s``
fixed, at every step of ``lem:log-enclosure``'s iteration on ``1/eps`` itself
and for the root of Eq. ``eq:bernstein-endpoint-t``; ``L`` and ``t`` are then
the least multiples of ``2^-s`` at or above the values so obtained. The
budget term is not taken from
:func:`certiqs_key.statistics.logs.log_bounds`, which splits ``1/eps`` at its
binary exponent first (``ln x = e ln 2 + ln x'``) -- an evaluation no claim
states. The parameters are fixed per run and recorded in the
emitted ``honest_model``, and an implementation that varied them with the
allocation would lose the monotonicity ``thm:monotonicity-limits`` (i) and (ii)
read.

NO TAIL IS EVALUATED TO FIND AN ENDPOINT on this route, which is why
``tail_evaluation`` governs only the completeness report here
(``binomial-box/interface.yaml``, ``completeness_report``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.statistics.logs import grid_up

__all__ = [
    "DEFAULT_BERNSTEIN_PARAMETERS",
    "BernsteinParameters",
    "bernstein_deviation",
    "bernstein_lower_endpoint",
    "bernstein_upper_endpoint",
    "budget_term",
    "grid_root_up",
]

_ZERO = Fraction(0)
_ONE = Fraction(1)


@dataclass(frozen=True)
class BernsteinParameters:
    """``j`` and ``s`` of ``prop:rule-bernstein``, as settled here.

    ``binomial-box/interface.yaml``,
    ``evaluation_parameters.the_bernstein_rule`` proposes both and marks them
    ``proposal: true``; BOTH PROPOSALS ARE TAKEN AS THEY STAND. The deviation
    enters under a square root, so a relative error of ``2^-20`` in the budget
    term moves the half-width by about half that -- far below one count at any
    ``n`` this engine runs at -- and this is the cheap route, which does not
    need the enclosure route's precision.
    """

    #: ``j``, with ``m = 2^j`` root steps in the enclosure of ``ln(1/eps)``.
    root_exponent: int = 32
    #: ``s``, the precision of each integer-square-root step, including the one
    #: that rounds the deviation upward.
    root_precision: int = 64


#: The values in force unless a caller says otherwise.
DEFAULT_BERNSTEIN_PARAMETERS = BernsteinParameters()


def grid_root_up(value: Fraction, precision: int) -> Fraction:
    """Return the upper root bound ``prop:rule-bernstein`` (ii) evaluates.

    The argument ``y`` is first rounded up onto the grid,
    ``c = ceil(y 2^s)`` with the denominator ``d = 2^s`` fixed, and the upper
    bound of Eq. ``eq:isqrt-bounds`` is taken at ``c/d``:

        u = (isqrt(c d 4^s) + 1) / (d 2^s)  >  sqrt(c/d)  >=  sqrt(y) .

    For the fixed ``d``, ``u`` is non-decreasing in the integer ``c`` because
    ``isqrt`` is, and ``c`` is non-decreasing in ``y``: the composite is a
    non-decreasing map of ``y``, which is the whole of what (ii) asks of a
    rounding. ``u`` lies on the finer grid ``2^-2s Z``; a caller that iterates
    rounds it up onto ``2^-s Z`` again at its next step.
    """
    if value < _ZERO:
        raise ValueError(f"a square root needs a non-negative argument; got {value}")
    scale = 1 << precision
    numerator = grid_up(value, precision)
    return Fraction(math.isqrt(numerator * scale * scale * scale) + 1, scale * scale)


def budget_term(budget: Fraction, parameters: BernsteinParameters) -> Fraction:
    """Return the ``L`` of ``prop:rule-bernstein``, an upper bound on ``ln(1/budget)``.

    The upper bound ``m (u - 1)`` of Eq. ``eq:log-rational-bounds`` at
    ``m = 2^j``, with ``u`` the upper root enclosure of
    ``lem:log-enclosure``'s iteration started at ``u_0 = 1/eps`` and run ``j``
    times, each step :func:`grid_root_up` -- the evaluation (ii) proves
    monotone -- and ``L`` the least multiple of ``2^-s`` at or above
    ``m (u - 1)``. ``L >= ln(1/eps)`` gives ``e^-L <= eps``, which is the
    direction the tail bound needs; a larger ``L`` widens the interval and is
    always admissible.

    THE ITERATION RUNS ON ``1/eps`` ITSELF, as the proposition defines it, and
    not on a mantissa split off at the binary exponent: the split is a
    different evaluation, monotone across a binary boundary only by an
    argument no claim makes.
    """
    if not _ZERO < budget < _ONE:
        raise ValueError(
            f"the budget term is formed for 0 < eps < 1; got {budget}. The "
            "zero budget is def:endpoint-rule (b) and is returned without an "
            "evaluation"
        )
    precision = parameters.root_precision
    root = _ONE / budget
    for _ in range(parameters.root_exponent):
        root = grid_root_up(root, precision)
    scale = 1 << parameters.root_exponent
    return Fraction(grid_up(scale * (root - _ONE), precision), 1 << precision)


def bernstein_deviation(
    variance: Fraction, term: Fraction, parameters: BernsteinParameters
) -> Fraction:
    """Return a rational ``t >= t(L)`` of Eq. ``eq:bernstein-t``, rounded UP.

    ``L/3 + sqrt((L/3)^2 + 2 v L)``, the positive root of
    ``t^2 - (2L/3) t - 2 v L = 0``, with the square root rounded "the same
    way" as the roots of ``L`` (``prop:rule-bernstein`` (ii)): the radicand
    rounded up onto the grid ``2^-s Z`` and the root the upper bound of
    Eq. ``eq:isqrt-bounds`` there (:func:`grid_root_up`), and ``t`` the least
    multiple of ``2^-s`` at or above ``L/3`` plus that root.

    THE GRID IS WHAT MAKES THE RULE MONOTONE IN THE ALLOCATION. A bare
    Eq. ``eq:isqrt-bounds`` on a rational has an excess that depends on the
    argument's DENOMINATOR, so it is not a monotone function of its argument
    and a larger budget could produce a wider interval -- the inversion
    ``prop:rule-bernstein`` (ii) forbids.
    On the grid every step is a non-decreasing map and the composite
    ``eps -> 1/eps -> L -> radicand -> t -> R^+`` is monotone.
    """
    precision = parameters.root_precision
    third = term / 3
    radicand = third * third + 2 * variance * term
    root = grid_root_up(radicand, precision)
    return Fraction(grid_up(third + root, precision), 1 << precision)


def _deviation(
    rounds: int, honest: Fraction, budget: Fraction, parameters: BernsteinParameters
) -> Fraction:
    variance = rounds * honest * (_ONE - honest)
    return bernstein_deviation(variance, budget_term(budget, parameters), parameters)


def bernstein_upper_endpoint(
    rounds: int,
    honest: Fraction,
    budget: Fraction,
    parameters: BernsteinParameters = DEFAULT_BERNSTEIN_PARAMETERS,
) -> int:
    """Return ``R^+`` of Eq. ``eq:bernstein-endpoints``, clipped into the range.

    ``min{n, ceil(np + t^+)}``. The zero-budget and degenerate-mass conventions
    of ``def:endpoint-rule`` (b) and (c) are applied by
    :mod:`certiqs_key.statistics.rules`, at the one place every rule passes
    through, and are not repeated here.
    """
    deviation = _deviation(rounds, honest, budget, parameters)
    return min(rounds, math.ceil(rounds * honest + deviation))


def bernstein_lower_endpoint(
    rounds: int,
    honest: Fraction,
    budget: Fraction,
    parameters: BernsteinParameters = DEFAULT_BERNSTEIN_PARAMETERS,
) -> int:
    """Return ``R^-`` of Eq. ``eq:bernstein-endpoints``, clipped into the range.

    ``max{0, floor(np - t^-)}``.
    """
    deviation = _deviation(rounds, honest, budget, parameters)
    return max(0, math.floor(rounds * honest - deviation))
