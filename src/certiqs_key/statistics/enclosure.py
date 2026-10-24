"""E1 -- the exact rule's LOCAL evaluation, in log space, at about log2(n) cost.

``lem:pmf-enclosure``, ``lem:tail-majorant`` and ``prop:bracketed-endpoints``,
with the search procedure ``binomial-box/interface.yaml`` fixes
(``search_procedure``). This is the route selected by
``tail_evaluation = enclosure``, and it is an ADMISSIBLE RELAXATION of the
exact binomial quantile rule: every emitted box CONTAINS the box the sweep
emits, and the two coincide wherever the bracket is decided.

WHAT IS ENCLOSED, AND WHERE
===========================
``lem:tail-majorant`` (iii) writes the upper tail as one mass point times a
rational:

    Pr[N > k] = pmf(k+1) (A_T + theta B_T),   0 <= theta <= 1,

with ``A_T`` the window of ``T`` terms and ``B_T`` the geometric majorant of
the rest, both computable from ``n``, ``p``, ``k`` and ``T`` alone
(Eq. ``eq:window-rationals``). The mass point is never formed: its LOGARITHM is
enclosed by ``lem:pmf-enclosure``, the two rationals are held as directed
dyadics (:mod:`certiqs_key.statistics.dyadic`), and the comparison against the
budget happens in log space against ``ln eps``. That is the substrate rule of
``rem:local-evaluation`` and of
``binomial-box/interface.yaml``'s ``conventions.the_substrate_rule``: no
intermediate ever has the magnitude of a mass point, of a power of the honest
mass or of a binomial coefficient.

THE VERDICT, AND WHICH SIDE OF IT MOVES AN ENDPOINT
===================================================
``prop:bracketed-endpoints`` calls an index CERTIFIED ADMISSIBLE when the upper
bound proves ``Pr[N > k] <= eps``, CERTIFIED INADMISSIBLE when the lower bound
proves the opposite, and UNDECIDED otherwise. ONLY THE UPPER BOUND EVER MOVES
AN EMITTED ENDPOINT. The lower bound enters the bracket verdict of that
proposition's (ii) -- the diagnostic ``endpoint_exact`` -- and the conservatism
report of its (iii), and nothing else; an implementation that let a lower
enclosure narrow an interval would have inverted the one direction a
conservative evaluation has (``def:conservative-evaluation``;
``binomial-box/interface.yaml``,
``conventions.exact_arithmetic_here``).

THE SEARCH IS THE INTERFACE'S AND IS PART OF THE RULE
=====================================================
``prop:bracketed-endpoints`` defines the evaluation as the rule whose endpoint
"a fixed search procedure that ``interface.yaml`` records" returns: until the
procedure is fixed there is no function of ``(n, p, eps)`` and the proposition
has no subject. The procedure is the bisection of ``search_procedure``: hi
starts at ``n``, where the predicate holds unconditionally, lo at the
fictitious index ``-1``, an UNDECIDED index counts as NOT certified, and the
lower side is the same procedure on the mirror ``N' = n - N`` of
``lem:tail-majorant`` (v). NO SEED IS USED: the Bernstein endpoint is offered
as an optional start, and a seed is part of the procedure and therefore part of
the rule, so taking one would change what the frozen oracles pin for a constant
factor.

ONE ADDITION THE INTERFACE'S WINDOW POLICY DOES NOT COVER, AND WHY IT IS
NEEDED. ``lem:tail-majorant`` (ii) requires ``r_{k+T+1} < 1``, and below the
mode no window shorter than about ``np - k`` terms achieves it -- a bisection
step near the middle of the range would build a window of hundreds of millions
of terms at the ``n`` this route exists for. At such an index the window is not
built at all: the tail is bounded BELOW by the single mass point at the first
index where the ratio drops under one, which is one term of the same sum, and
that suffices to certify INADMISSIBILITY there. No upper bound is claimed, so
the index is never certified admissible and no emitted endpoint can rest on the
short cut; what it costs is that a genuinely admissible index below the mode --
reachable only at a tail budget above one half -- is passed over, which is
conservative and therefore admissible.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from functools import lru_cache

from certiqs_key.statistics.dyadic import round_dyadic, round_ratio
from certiqs_key.statistics.logs import (
    LogBounds,
    exp_upper,
    log_bounds,
    log_factorial_bounds,
)

__all__ = [
    "DEFAULT_ENCLOSURE_PARAMETERS",
    "BracketedEndpoint",
    "EnclosureParameters",
    "Verdict",
    "bracketed_lower_endpoint",
    "bracketed_upper_endpoint",
    "certify_upper",
    "conservatism_bound",
    "first_decreasing_index",
    "log_pmf_bounds",
    "lower_tail_upper_bound",
    "mass_ratio",
    "tail_upper_bound",
    "upper_tail_log_bounds",
]

_ZERO = Fraction(0)
_ONE = Fraction(1)


@dataclass(frozen=True)
class EnclosureParameters:
    """The evaluation parameters of the enclosure route, as settled here.

    ``binomial-box/interface.yaml``, ``evaluation_parameters.the_enclosure_route``
    proposes each of these and marks it ``proposal: true``; the values here are
    what this implementation settled on. NONE OF THEM CAN MAKE AN
    ENDPOINT LESS CONSERVATIVE -- every bound entering a decision is used in
    the one direction a conservative evaluation
    (``def:conservative-evaluation``) licenses -- which is why they are evaluation
    parameters and not thresholds (``declared_thresholds`` is empty
    deliberately).

    They are NOT request inputs: the inputs table has eight rows and none of
    them is a parameter. They are recorded per run in the emitted
    ``honest_model``.
    """

    #: ``j``, with ``m = 2^j`` root steps per logarithm (``lem:log-enclosure``).
    #: 64 RATHER THAN THE PROPOSED 48, AND THE REASON IS MEASURED. A single
    #: logarithm's slack is multiplied by about ``3n`` in
    #: ``lem:pmf-enclosure``, so it is the one parameter whose contribution
    #: GROWS WITH ``n``, while the Wallis constant's does not. At
    #: ``n = 10^9`` both settle the bracket and cost the same wall time (the
    #: window dominates), but the enclosure is 2.9e-4 nats wide at 48 against
    #: 1.8e-4 at 64, and the difference is entirely the logarithm term: at 64
    #: it is under 1e-17 and the width is the Wallis constant alone, at every
    #: ``n``. At 32 the bracket does not close at all (6.9 nats). Taking 64
    #: therefore removes the only ``n``-dependent term for no measured cost;
    #: the proposal's own sizing, against a single logarithm, is what the
    #: binary-exponent split in :mod:`certiqs_key.statistics.logs` made
    #: insufficient to reason from.
    root_exponent: int = 64
    #: ``s``, the precision of each integer-square-root step.
    root_precision: int = 128
    #: ``M``, the number of Wallis factors. 4096 rather than the proposed 65536:
    #: the constant enters ``lem:pmf-enclosure`` with coefficient 3/2, so this
    #: contributes ``3/(4M) = 1.8e-4`` nats, under 0.1 counts at every per-count
    #: decay this engine sees.
    wallis_length: int = 4096
    #: The first window length tried, then doubled.
    window_start: int = 32
    #: The largest window built. At the cap the bracket is formed from whatever
    #: relative slack the window has reached.
    window_cap: int = 4096
    #: The window stops when ``B_T / A_T <= 2^-window_target_bits``.
    window_target_bits: int = 24
    #: The significand kept by the window's dyadic products.
    window_precision: int = 128


#: The values in force unless a caller says otherwise.
DEFAULT_ENCLOSURE_PARAMETERS = EnclosureParameters()


class Verdict(StrEnum):
    """The three verdicts of ``prop:bracketed-endpoints`` on one index."""

    #: The upper bound proves the tail is within the budget.
    CERTIFIED_ADMISSIBLE = "certified_admissible"
    #: The lower bound proves it is not.
    CERTIFIED_INADMISSIBLE = "certified_inadmissible"
    #: Neither bound decides. Counted as NOT certified by the search.
    UNDECIDED = "undecided"


@dataclass(frozen=True)
class BracketedEndpoint:
    """One bracketed endpoint, with what ``prop:bracketed-endpoints`` (ii) says.

    ``decided`` is the bracket verdict: ``True`` when the emitted index is
    PROVED equal to the exact binomial quantile -- either because it is ``0``,
    or because the index below it is certified inadmissible. It is the
    diagnostic ``endpoint_exact`` of ``interface.yaml`` and no claim of the
    contract is stated in terms of it.

    ``tail_upper`` is a rational upper bound on the tail AT the emitted index,
    which the enclosure routes' completeness report sums
    (``binomial-box/interface.yaml``, ``completeness_report``); ``None`` where
    the tail is exactly zero.
    """

    index: int
    decided: bool
    tail_upper: Fraction | None


def mass_ratio(rounds: int, honest: Fraction, index: int) -> Fraction:
    """Return ``r_index`` of Eq. ``eq:pmf-ratio``, exactly.

    ``r_j = (n - j) p / ((j + 1) (1 - p))`` for ``0 <= j <= n - 1``, and
    ``r_n = 0`` by the lemma's convention.
    """
    if index >= rounds:
        return _ZERO
    numerator, denominator = honest.numerator, honest.denominator
    return Fraction(
        (rounds - index) * numerator, (index + 1) * (denominator - numerator)
    )


def first_decreasing_index(rounds: int, honest: Fraction) -> int:
    """Return the least ``j`` with ``r_j < 1``; the ratios decrease strictly.

    ``r_j < 1`` is ``(n - j) a < (j + 1) (b - a)`` for ``p = a / b``, i.e.
    ``j > (n a + a - b) / b``, so the least such ``j`` is the floor of that
    plus one, clamped into ``{0, ..., n}``.
    """
    numerator, denominator = honest.numerator, honest.denominator
    threshold = (rounds * numerator + numerator - denominator) // denominator + 1
    return max(0, min(rounds, threshold))


@lru_cache(maxsize=8192)
def log_pmf_bounds(
    rounds: int, honest: Fraction, index: int, parameters: EnclosureParameters
) -> LogBounds:
    """Return rationals enclosing ``ln Pr[N = index]``, ``lem:pmf-enclosure``.

    Eq. ``eq:pmf-enclosure``: each term of
    ``F(n) - F(j) - F(n-j) + j ln p + (n-j) ln(1-p)`` is replaced by the bound
    in the direction its sign requires, ``F`` from
    ``lem:stirling-enclosure`` (iii) and the two logarithms from
    ``lem:log-enclosure``.
    """
    if not 0 <= index <= rounds:
        raise ValueError(f"a mass point needs 0 <= j <= n; got j = {index}")
    if honest in (_ZERO, _ONE):
        raise ValueError("lem:pmf-enclosure is stated for 0 < p < 1")
    exponent, precision = parameters.root_exponent, parameters.root_precision
    wallis = parameters.wallis_length
    total = log_factorial_bounds(rounds, exponent, precision, wallis)
    left = log_factorial_bounds(index, exponent, precision, wallis)
    right = log_factorial_bounds(rounds - index, exponent, precision, wallis)
    log_p = log_bounds(honest, exponent, precision)
    log_q = log_bounds(_ONE - honest, exponent, precision)
    lower = (
        total.lower
        - left.upper
        - right.upper
        + index * log_p.lower
        + (rounds - index) * log_q.lower
    )
    upper = (
        total.upper
        - left.lower
        - right.lower
        + index * log_p.upper
        + (rounds - index) * log_q.upper
    )
    return LogBounds(
        round_dyadic(lower, precision, upward=False),
        round_dyadic(upper, precision, upward=True),
    )


def _window(
    rounds: int, honest: Fraction, index: int, parameters: EnclosureParameters
) -> tuple[Fraction, Fraction]:
    """Return ``(A_T, A_T + B_T)`` as directed dyadics, Eq. ``eq:window-rationals``.

    The first value is a LOWER bound on ``A_T`` and the second an UPPER bound
    on ``A_T + B_T``, so that Eq. ``eq:tail-log`` holds with them in place of
    the exact rationals. The window grows from ``window_start`` by doubling
    until the majorant is below ``2^-window_target_bits`` of the window, until
    it reaches the end of the range -- where the tail is exact and the majorant
    is zero -- or until ``window_cap``.
    """
    bits = parameters.window_precision
    target = 1 << parameters.window_target_bits
    max_terms = rounds - index
    start = first_decreasing_index(rounds, honest)
    minimum = max(1, start - index - 1)
    next_check = max(minimum, parameters.window_start)
    window_low = window_high = _ONE
    term_low = term_high = _ONE
    length = 1
    while True:
        if length >= max_terms:
            # The window reached the end of the range: the tail is the window.
            return window_low, window_high
        ratio_numerator = (rounds - index - length) * honest.numerator
        ratio_denominator = (index + length + 1) * (
            honest.denominator - honest.numerator
        )
        ratio_low = round_ratio(
            ratio_numerator, ratio_denominator, bits, upward=False
        )
        ratio_high = round_ratio(
            ratio_numerator, ratio_denominator, bits, upward=True
        )
        term_low = round_dyadic(term_low * ratio_low, bits, upward=False)
        term_high = round_dyadic(term_high * ratio_high, bits, upward=True)
        if length >= next_check or length >= parameters.window_cap:
            tail_ratio = mass_ratio(rounds, honest, index + length + 1)
            if tail_ratio < _ONE:
                majorant = round_dyadic(
                    term_high / (_ONE - tail_ratio), bits, upward=True
                )
                if majorant * target <= window_low or length >= parameters.window_cap:
                    return window_low, round_dyadic(
                        window_high + majorant, bits, upward=True
                    )
            next_check = max(2 * length, length + 1)
        window_low = round_dyadic(window_low + term_low, bits, upward=False)
        window_high = round_dyadic(window_high + term_high, bits, upward=True)
        length += 1


@lru_cache(maxsize=8192)
def upper_tail_log_bounds(
    rounds: int, honest: Fraction, index: int, parameters: EnclosureParameters
) -> LogBounds | None:
    """Return rationals enclosing ``ln Pr[N > index]``, or ``None`` if it is 0.

    ``None`` is the exact boundary value ``Pr[N > n] = 0`` of ``thm:binomial-tails``,
    which is what makes ``k = n`` certified for every budget and the search
    total. Below the mode the window is not built; see the module docstring.
    """
    if index >= rounds:
        return None
    if index < 0:
        return LogBounds(_ZERO, _ZERO)
    start = first_decreasing_index(rounds, honest)
    if start - index - 1 > parameters.window_cap:
        # One term of the tail bounds it from below; no upper bound is claimed,
        # and ln 1 = 0 is the trivial one, which certifies nothing.
        witness = log_pmf_bounds(rounds, honest, min(start, rounds), parameters)
        return LogBounds(witness.lower, _ZERO)
    point = log_pmf_bounds(rounds, honest, index + 1, parameters)
    window_low, window_high = _window(rounds, honest, index, parameters)
    exponent, precision = parameters.root_exponent, parameters.root_precision
    return LogBounds(
        point.lower + log_bounds(window_low, exponent, precision).lower,
        point.upper + log_bounds(window_high, exponent, precision).upper,
    )


def certify_upper(
    rounds: int,
    honest: Fraction,
    index: int,
    budget: Fraction,
    parameters: EnclosureParameters,
) -> Verdict:
    """Return the verdict of ``prop:bracketed-endpoints`` on one index.

    ``C^+(k)`` is ``U(k) <= lambda^-`` for a rational ``lambda^- <= ln eps``,
    and ``D^+(k)`` is ``Lambda(k) > lambda^+`` for a rational
    ``lambda^+ >= ln eps``; an index that is neither is undecided.
    """
    enclosure = upper_tail_log_bounds(rounds, honest, index, parameters)
    if enclosure is None:
        return Verdict.CERTIFIED_ADMISSIBLE
    if budget <= _ZERO:
        # Pr[N > k] > 0 for every k < n at 0 < p < 1, so no index below n is
        # admissible at a zero budget; def:endpoint-rule (b) returns n without
        # a search and this branch is the fail-closed answer for a caller that
        # asks anyway.
        return Verdict.CERTIFIED_INADMISSIBLE
    exponent, precision = parameters.root_exponent, parameters.root_precision
    log_budget = log_bounds(budget, exponent, precision)
    if enclosure.upper <= log_budget.lower:
        return Verdict.CERTIFIED_ADMISSIBLE
    if enclosure.lower > log_budget.upper:
        return Verdict.CERTIFIED_INADMISSIBLE
    return Verdict.UNDECIDED


def tail_upper_bound(
    rounds: int,
    honest: Fraction,
    index: int,
    parameters: EnclosureParameters,
) -> Fraction:
    """Return a rational at or above ``Pr[N > index]``, for the report.

    The upper enclosure of the same object the endpoint decision used, taken
    out of log space by :func:`~certiqs_key.statistics.logs.exp_upper`. It
    enters ``completeness_certified`` on the two enclosure rows of
    ``binomial-box/interface.yaml``'s ``completeness_report`` and NO emitted
    endpoint.
    """
    enclosure = upper_tail_log_bounds(rounds, honest, index, parameters)
    if enclosure is None:
        return _ZERO
    return min(
        _ONE,
        exp_upper(
            enclosure.upper, parameters.root_exponent, parameters.root_precision
        ),
    )


def bracketed_upper_endpoint(
    rounds: int,
    honest: Fraction,
    budget: Fraction,
    parameters: EnclosureParameters = DEFAULT_ENCLOSURE_PARAMETERS,
) -> BracketedEndpoint:
    """Return the bracketed UPPER endpoint of ``prop:bracketed-endpoints``.

    The bisection ``binomial-box/interface.yaml`` fixes: ``hi = n``, where
    ``C^+`` holds unconditionally, ``lo = -1``, an undecided index counted as
    not certified, ``hi`` returned. About ``log2(n + 1)`` evaluations, and the
    search cannot fail -- which is why the enclosure route adds no reason code
    to the core's ten.
    """
    low, high = -1, rounds
    while high - low > 1:
        middle = (low + high) // 2
        verdict = certify_upper(rounds, honest, middle, budget, parameters)
        if verdict is Verdict.CERTIFIED_ADMISSIBLE:
            high = middle
        else:
            low = middle
    decided = high == 0 or (
        certify_upper(rounds, honest, high - 1, budget, parameters)
        is Verdict.CERTIFIED_INADMISSIBLE
    )
    return BracketedEndpoint(
        index=high,
        decided=decided,
        tail_upper=tail_upper_bound(rounds, honest, high, parameters),
    )


def bracketed_lower_endpoint(
    rounds: int,
    honest: Fraction,
    budget: Fraction,
    parameters: EnclosureParameters = DEFAULT_ENCLOSURE_PARAMETERS,
) -> BracketedEndpoint:
    """Return the bracketed LOWER endpoint, through the mirror of (v).

    ``N' = n - N`` is binomial ``(n, 1 - p)`` and ``Pr[N < k] = Pr[N' > n - k]``
    (``lem:tail-majorant`` (v)), so the lower side is the upper-side procedure
    applied to ``N'`` and the returned index subtracted from ``n``.
    """
    mirrored = bracketed_upper_endpoint(rounds, _ONE - honest, budget, parameters)
    return BracketedEndpoint(
        index=rounds - mirrored.index,
        decided=mirrored.decided,
        tail_upper=mirrored.tail_upper,
    )


def lower_tail_upper_bound(
    rounds: int,
    honest: Fraction,
    index: int,
    parameters: EnclosureParameters,
) -> Fraction:
    """Return a rational at or above ``Pr[N < index]``, through the mirror."""
    if index <= 0:
        return _ZERO
    return tail_upper_bound(rounds, _ONE - honest, rounds - index, parameters)


def conservatism_bound(
    rounds: int,
    honest: Fraction,
    certified_inadmissible_index: int,
    slack: Fraction,
    parameters: EnclosureParameters,
) -> Fraction | None:
    """Return the count bound of Eq. ``eq:bracket-conservatism``, or ``None``.

    ``1 + w / (-ln r)`` with ``r`` the ratio at
    ``certified_inadmissible_index + 2``, which ``rem:local-evaluation`` names
    as the valid substitute for ``r_{kappa+1}`` when only a
    certified-inadmissible index is in hand. ``None`` where the hypothesis
    ``r < 1`` fails, the vacuous case ``prop:bracketed-endpoints`` (iii) states.
    """
    ratio = mass_ratio(rounds, honest, certified_inadmissible_index + 2)
    if ratio >= _ONE or ratio <= _ZERO:
        return None
    decay = log_bounds(ratio, parameters.root_exponent, parameters.root_precision)
    if decay.upper >= _ZERO:  # pragma: no cover - r < 1 gives ln r < 0
        return None
    return 1 + slack / (-decay.upper)
