"""def:interval, prop:rule-exact, lem:guard -- one outcome, and the guard.

Definition ``def:interval`` fixes the extremal endpoints

    kappa^-(chat) = max { k in {0..n} : Pr[N < k] <= eps^-(chat) }  (eq:kappaminus)
    kappa^+(chat) = min { k in {0..n} : Pr[N > k] <= eps^+(chat) }  (eq:kappaplus)

and then the EMITTED endpoints, after the honest-containment guard,

    k^-(chat) = min{ kappa^-(chat), floor(n p) }                          (eq:guard)
    k^+(chat) = max{ kappa^+(chat), ceil(n p) } .

Proposition ``prop:rule-exact`` proves the endpoints exist and are unique (i), that the
EMITTED endpoints meet their budgets (ii), that enlarging the interval is always
admissible and shrinking it beyond ``[kappa^-, kappa^+]`` is not (iii), that the
endpoints are computable from the closed forms (iv), that a degenerate honest
mass gives ``[0, 0]`` respectively ``[n, n]`` with both budgets unspent (v), and
the exact cost of the guard, in counts and in distance from the honest value
(vi).

WHY THE GUARD IS NOT OPTIONAL, AND WHAT IT COSTS
================================================
Remark ``rem:guard``: what the guard buys is unconditional -- ``p^hon(chat)``
lies in ``[k^-/n, k^+/n]`` for EVERY admissible budget and EVERY admissible
allocation, including allocations so lopsided that the raw quantile interval
excludes the honest value. Theorems ``thm:box-construction`` (iii) and
``thm:honest-containment`` rest on exactly that, and without it both would carry a side
condition on how large ``ecomp`` may be.

What it costs has two different and equally correct answers and this module
reports both, because reporting only the second overstates the guarantee.
Against the RAW quantile interval the cost is Eq. ``eq:guard-cost`` and is NOT
bounded by one count. Against the HONEST VALUE the emitted endpoint sits within
``1/n`` of ``p`` on whichever side the guard acts, unconditionally
(Eq. ``eq:guard-from-p``).

THE FOUR VERDICTS ARE READ OFF THE COST; THE EQUIVALENCE IS THE EXACT ROUTE'S
============================================================================
Eqs. ``eq:guard-lo0``, ``eq:guard-lo1``, ``eq:guard-up0`` and ``eq:guard-up1``
are stated as comparisons of an allocated budget against a value of the count
distribution function, and Proposition ``prop:rule-exact`` (vi) proves each one
EQUIVALENT to a statement about the enlargement of Eq. ``eq:guard-cost`` -- ``lo0`` to a
lower enlargement of ``0``, ``lo1`` to one of at most ``1``, and symmetrically
above. This module evaluates the enlargement side, which needs no further tail
evaluation.

ON THE EXACT ROUTE the two sides are the same predicate. That equivalence is
stated for the contract's ``kappa^{+-}``, and on the exact route this module's
``kappa^{+-}`` ARE the contract's, so each verdict is the contract's equation
verbatim.

ON THE ENCLOSURE ROUTE of :mod:`certiqs_key.statistics.tails` they are not the
same predicate, and the claim is narrowed here rather than repaired. A tail
comparison too close to call is resolved conservatively, so this module's
``kappa^-`` can fall below and its ``kappa^+`` rise above the contract's, and
the enlargement measured below is then the one the EMITTED interval has over
those conservative endpoints -- not the one the contract's raw quantile
interval has. The four verdicts therefore describe the emitted interval, and
the budget-side equations can disagree with them. A worked instance: at
``n = 8`` and ``p = (3^399 + 1) / 3^400``, with ``eps^-`` set exactly equal to
``Pr[N < 3]``, the contract's ``kappa^- = 3`` while this module returns
``2 = floor(np)``; ``guard_lo0_holds`` comes back ``True`` although
``eq:guard-lo0`` evaluated at the exact tails is false.

NOTHING DOWNSTREAM TURNS ON THAT. The four fields are diagnostics and are not
outputs of the outputs table -- nothing downstream is entitled to them -- and the
EMITTED endpoints are unaffected: on either route they are enlarged only in the
direction Proposition ``prop:rule-exact`` (iii) licenses. Reading a verdict
off the tails instead would inherit the enclosure's conservatism for no gain,
and would still not be the contract's predicate, whose ``kappa^{+-}`` are
unavailable on that route by construction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.statistics.tails import (
    TailBound,
    cumulative_stream,
    lower_tail,
    upper_tail,
    within_budget,
)

__all__ = [
    "EnvelopeInterval",
    "OutcomeInterval",
    "emitted_tails",
    "extremal_endpoints",
    "guarded_endpoints",
    "interval_record",
    "outcome_interval",
]

_ZERO = Fraction(0)
_ONE = Fraction(1)


@dataclass(frozen=True)
class OutcomeInterval:
    """One outcome's count interval, before and after the guard.

    Every field is a quantity Proposition ``prop:rule-exact`` names. The two
    ``distance_*`` fields are the two sides of Eq. ``eq:guard-from-p``. The
    four ``guard_*`` verdicts are the four iff conditions of part (vi) where
    ``tails_exact`` is ``True``; where it is ``False`` they describe the
    EMITTED interval rather than the raw quantile interval, and may differ from the
    budget-side equations (module docstring).
    """

    rounds: int
    honest: Fraction
    eps_lower: Fraction
    eps_upper: Fraction
    #: The extremal endpoints of Eqs. eq:kappaminus and eq:kappaplus.
    kappa_lower: int
    kappa_upper: int
    #: The emitted endpoints of Eq. eq:guard.
    k_lower: int
    k_upper: int
    floor_np: int
    ceil_np: int
    #: Eq. eq:guard-cost: kappa^- - k^- and k^+ - kappa^+, in counts.
    lower_enlargement: int
    upper_enlargement: int
    guard_lo0_holds: bool
    guard_lo1_holds: bool
    guard_up0_holds: bool
    guard_up1_holds: bool
    #: Eq. eq:guard-from-p: p - k^-/n and k^+/n - p.
    distance_below_p: Fraction
    distance_above_p: Fraction
    #: Whether the endpoints were decided against exact tails. ``False`` means
    #: the endpoints were decided conservatively
    #: (``def:conservative-evaluation``): by
    #: the sweep's own dyadic route, by the local enclosures of
    #: ``prop:bracketed-endpoints``, or by the closed form of
    #: ``prop:rule-bernstein``, which evaluates no tail at all.
    tails_exact: bool
    #: THE ROUTE THIS RECORD WAS BUILT ON: the values of
    #: the two request fields ``endpoint_rule`` and ``tail_evaluation`` the
    #: inputs table carries. ``kappa_lower`` and ``kappa_upper`` are then the
    #: RULE'S OWN endpoints ``R^-`` and ``R^+`` before the guard, which are the
    #: exact quantiles only where the rule is the exact one.
    rule: str = "exact"
    evaluation: str = "sweep"
    #: The bracket verdict of ``prop:bracketed-endpoints`` (ii) per side, which
    #: the output row ``endpoint_exact`` reports: whether the emitted endpoint
    #: is PROVED equal to the exact binomial quantile.
    #:
    #: ``True`` WHEREVER A CONVENTION DECIDES IT, ON EVERY ROUTE. The two
    #: conventions of ``def:endpoint-rule`` -- a degenerate honest mass (c) and
    #: a zero budget (b) -- are applied in ``rules.EndpointRule.endpoints``,
    #: which sits above every rule's own evaluation, and both are cases where
    #: the emitted endpoint IS the exact quantile (``prop:rule-exact`` (ii),
    #: (v)). So the SWEEP route, which forms no bracket, still carries ``True``
    #: at those two and ``None`` elsewhere. ``None`` means only "this route's
    #: evaluation formed no bracket and no convention answered", and it is NOT
    #: a promise about which route is running.
    #:
    #: WHAT IS PUBLISHED IS GATED ELSEWHERE: ``construction._endpoint_exact``
    #: emits the table only under ``tail_evaluation = enclosure`` with the
    #: exact rule, so a verdict set here on another route reaches no output.
    #:
    #: A DIAGNOSTIC: no claim is stated in terms of it and the emitted set is
    #: unaffected by whether it is recorded.
    lower_decided: bool | None = None
    upper_decided: bool | None = None
    #: Rational upper bounds on the two tails AT THE EMITTED (guarded)
    #: endpoints, ``Pr[N < k^-]`` and ``Pr[N > k^+]``, where the route computed
    #: them; ``None`` elsewhere. They are what the two enclosure rows of
    #: ``binomial-box/interface.yaml``'s ``completeness_report`` sum.
    tail_upper_below: Fraction | None = None
    tail_upper_above: Fraction | None = None

    @property
    def box_lower(self) -> Fraction:
        """Return ``q^-(chat) = k^-(chat) / n`` (Eq. ``eq:boxbounds``)."""
        return Fraction(self.k_lower, self.rounds)

    @property
    def box_upper(self) -> Fraction:
        """Return ``q^+(chat) = k^+(chat) / n`` (Eq. ``eq:boxbounds``)."""
        return Fraction(self.k_upper, self.rounds)


@dataclass(frozen=True)
class EnvelopeInterval:
    """One outcome's interval under a NON-DEGENERATE honest envelope.

    ``def:endpoint-rule`` with an envelope ``[p^-, p^+]``: the lower endpoint is
    the rule at ``p^-`` guarded by ``floor(n p^-)``, the upper endpoint the rule
    at ``p^+`` guarded by ``ceil(n p^+)``. The two sides are therefore two
    one-sided records at two different success probabilities, and this record
    pairs them rather than inventing a single ``honest`` value that neither
    side was evaluated at. ``lower_side`` is evaluated at ``p^-`` with its upper
    allocation set to zero, ``upper_side`` at ``p^+`` with its lower allocation
    set to zero: ``def:endpoint-rule`` (b) answers the unused side without a
    search, and only the used side of each is read.

    A coordinate whose envelope is degenerate (``p^- = p^+``) is NOT recorded
    here: it takes the plain :class:`OutcomeInterval` route, which is what
    keeps the one-law case bit for bit the plain route's.
    """

    lower_side: OutcomeInterval
    upper_side: OutcomeInterval

    @property
    def rounds(self) -> int:
        """Return ``n``."""
        return self.lower_side.rounds

    @property
    def honest_lower(self) -> Fraction:
        """Return ``p^-``."""
        return self.lower_side.honest

    @property
    def honest_upper(self) -> Fraction:
        """Return ``p^+``."""
        return self.upper_side.honest

    @property
    def k_lower(self) -> int:
        """Return ``k^- = min{R^-(n, p^-), floor(n p^-)}``."""
        return self.lower_side.k_lower

    @property
    def k_upper(self) -> int:
        """Return ``k^+ = max{R^+(n, p^+), ceil(n p^+)}``."""
        return self.upper_side.k_upper

    @property
    def box_lower(self) -> Fraction:
        """Return ``q^-(chat) = k^-(chat) / n`` (Eq. ``eq:boxbounds``)."""
        return Fraction(self.k_lower, self.rounds)

    @property
    def box_upper(self) -> Fraction:
        """Return ``q^+(chat) = k^+(chat) / n`` (Eq. ``eq:boxbounds``)."""
        return Fraction(self.k_upper, self.rounds)

    @property
    def tails_exact(self) -> bool:
        """Return whether both used sides were decided against exact tails."""
        return self.lower_side.tails_exact and self.upper_side.tails_exact

    @property
    def lower_decided(self) -> bool | None:
        """Return the lower side's bracket verdict."""
        return self.lower_side.lower_decided

    @property
    def upper_decided(self) -> bool | None:
        """Return the upper side's bracket verdict."""
        return self.upper_side.upper_decided

    @property
    def tail_upper_below(self) -> Fraction | None:
        """Return the enclosure's bound on ``Pr[Bin(n, p^-) < k^-]``."""
        return self.lower_side.tail_upper_below

    @property
    def tail_upper_above(self) -> Fraction | None:
        """Return the enclosure's bound on ``Pr[Bin(n, p^+) > k^+]``."""
        return self.upper_side.tail_upper_above


def extremal_endpoints(
    rounds: int, honest: Fraction, eps_lower: Fraction, eps_upper: Fraction
) -> tuple[int, int, bool]:
    """Return ``(kappa^-, kappa^+, tails_exact)`` of Definition ``def:interval``.

    ONE SWEEP DECIDES BOTH, and the shape of the sweep is what Lemma
    ``lem:guard`` (ii) proves about the two tails: ``k -> Pr[N < k]`` is
    non-decreasing and ``k -> Pr[N > k]`` non-increasing, so with
    ``S_i = Pr[N <= i]``

    * ``k >= 1`` is admissible in Eq. ``eq:kappaminus`` iff ``S_{k-1} <=
      eps^-``, an admissibility that is downward closed, so ``kappa^-`` is the
      first index at which the running sum leaves the budget;
    * ``k`` is admissible in Eq. ``eq:kappaplus`` iff ``S_k >= 1 - eps^+``, an
      admissibility that is upward closed, so ``kappa^+`` is the first index at
      which the running sum reaches that level.

    Neither extremum is searched for by bisection and neither is approached
    iteratively: they are the extrema of a finite set of integers, and there is
    nothing to converge to (Proposition ``prop:rule-exact`` (i), (iv)). Where
    the running sum is an enclosure (above the bit budget of
    :mod:`~certiqs_key.statistics.tails`), each comparison is decided against
    the bound on the tail that rounds it upward, and the indices returned are
    Proposition ``prop:rule-exact`` (vii)'s ``tilde-kappa``, with ``tails_exact``
    false: ``tilde-kappa^- <= kappa^-`` and ``tilde-kappa^+ >= kappa^+``.

    THREE SHORTCUTS, EACH ONE A THEOREM RATHER THAN AN OPTIMIZATION.

    * ``p = 0`` gives ``[0, 0]`` and ``p = 1`` gives ``[n, n]``, which is
      Proposition ``prop:rule-exact`` (v) verbatim -- and the sweep would agree, at the
      cost of ``n`` steps on a distribution with one mass point.
    * ``eps^- = 0`` with ``0 < p < 1`` forces ``kappa^- = 0``, because
      ``Pr[N < k] >= Pr[N = 0] = (1-p)^n > 0`` for every ``k >= 1``;
    * ``eps^+ = 0`` with ``0 < p < 1`` forces ``kappa^+ = n``, because
      ``Pr[N > k] >= Pr[N = n] = p^n > 0`` for every ``k <= n - 1``.

    The last two are the proof of Theorem ``thm:monotonicity-limits`` (iii) read as
    code, and they are what keeps the ``ecomp = 0`` limit -- where the sweep would run
    to ``n`` on every outcome and return the whole range anyway -- free.
    """
    if honest == _ZERO:
        return 0, 0, True
    if honest == _ONE:
        return rounds, rounds, True
    kappa_lower: int | None = 0 if eps_lower == _ZERO else None
    kappa_upper: int | None = rounds if eps_upper == _ZERO else None
    if kappa_lower is not None and kappa_upper is not None:
        return kappa_lower, kappa_upper, True
    exact = True
    threshold = _ONE - eps_upper
    for index, cumulative in enumerate(cumulative_stream(rounds, honest)):
        exact = exact and cumulative.exact
        if kappa_lower is None and not within_budget(cumulative, eps_lower):
            # The first index whose running sum leaves the lower budget: no
            # k > index is admissible, and k = index is.
            kappa_lower = index
        if kappa_upper is None and cumulative.lower >= threshold:
            # Pr[N > index] <= 1 - S_index <= eps^+, established against the
            # enclosure's upper bound on the tail (a conservative evaluation,
            # def:conservative-evaluation).
            kappa_upper = index
        if kappa_lower is not None and kappa_upper is not None:
            break
    if kappa_lower is None:
        # Unreachable on the input domain -- eps^- <= ecomp < 1 while
        # S_n = 1 -- but a sweep that ended without a verdict must not fall
        # through to a guessed endpoint.
        kappa_lower = rounds
    if kappa_upper is None:
        # Pr[N > n] = 0 exactly (Theorem thm:binomial-tails's boundary values), so k = n
        # is admissible for every budget and the minimum is at most n.
        kappa_upper = rounds
    return min(kappa_lower, rounds), min(kappa_upper, rounds), exact


def guarded_endpoints(
    rounds: int, honest: Fraction, kappa_lower: int, kappa_upper: int
) -> tuple[int, int]:
    """Return ``(k^-, k^+)`` of Eq. ``eq:guard``, FOR ANY ADMISSIBLE RULE.

    ``k^- = min{R^-, floor(np)}`` and ``k^+ = max{R^+, ceil(np)}``. The two
    arguments are the rule's own endpoints and this function knows nothing
    about where they came from, which is what ``def:endpoint-rule``'s
    Eq. ``eq:guard`` asks of the guard and what makes ``lem:guard`` (i)-(iv)
    hold for every rule rather than for the exact one alone. The parameter
    names are the exact rule's because on the
    default route they ARE the quantiles.
    """
    return (
        min(kappa_lower, math.floor(rounds * honest)),
        max(kappa_upper, math.ceil(rounds * honest)),
    )


def interval_record(
    rounds: int,
    honest: Fraction,
    eps_lower: Fraction,
    eps_upper: Fraction,
    kappa_lower: int,
    kappa_upper: int,
    tails_exact: bool,
    **route: object,
) -> OutcomeInterval:
    """Return the interval record for endpoints A RULE HAS ALREADY RETURNED.

    Everything after the rule: the guard Eq. ``eq:guard``, the cost identities
    Eq. ``eq:guard-cost``, the two distances of Eq. ``eq:guard-from-p`` and the
    four verdicts. IT IS RULE-INDEPENDENT, which is ``lem:guard``, so both
    :func:`outcome_interval` and the rule-aware builder of
    :mod:`certiqs_key.statistics.rules` go through it and the emitted record of
    the default route is the same expression.

    ``route`` carries the optional fields of :class:`OutcomeInterval` that
    depend on which rule ran; it is empty on the default route.
    """
    k_lower, k_upper = guarded_endpoints(rounds, honest, kappa_lower, kappa_upper)
    floor_np = math.floor(rounds * honest)
    ceil_np = math.ceil(rounds * honest)
    lower_enlargement = max(0, kappa_lower - floor_np)
    upper_enlargement = max(0, ceil_np - kappa_upper)
    return OutcomeInterval(
        rounds=rounds,
        honest=honest,
        eps_lower=eps_lower,
        eps_upper=eps_upper,
        kappa_lower=kappa_lower,
        kappa_upper=kappa_upper,
        k_lower=k_lower,
        k_upper=k_upper,
        floor_np=floor_np,
        ceil_np=ceil_np,
        lower_enlargement=lower_enlargement,
        upper_enlargement=upper_enlargement,
        # The four iff conditions of prop:rule-exact (vi), read off the enlargement.
        # The contract's equations exactly where `exact` is True; where it is
        # False these are verdicts about the EMITTED interval (module
        # docstring), and are diagnostics either way.
        guard_lo0_holds=lower_enlargement == 0,
        guard_lo1_holds=lower_enlargement <= 1,
        guard_up0_holds=upper_enlargement == 0,
        guard_up1_holds=upper_enlargement <= 1,
        distance_below_p=honest - Fraction(k_lower, rounds),
        distance_above_p=Fraction(k_upper, rounds) - honest,
        tails_exact=tails_exact,
        **route,  # type: ignore[arg-type]
    )


def outcome_interval(
    rounds: int, honest: Fraction, eps_lower: Fraction, eps_upper: Fraction
) -> OutcomeInterval:
    """Return one outcome's full interval record on THE DEFAULT ROUTE.

    ``endpoint_rule = exact`` and ``tail_evaluation = sweep``: the exact
    binomial quantile rule of ``def:interval`` evaluated by the sweep. The
    rule-aware entry point is
    :func:`certiqs_key.statistics.rules.interval_for_rule`, which reaches this
    same record through :func:`interval_record`.
    """
    kappa_lower, kappa_upper, exact = extremal_endpoints(
        rounds, honest, eps_lower, eps_upper
    )
    return interval_record(
        rounds, honest, eps_lower, eps_upper, kappa_lower, kappa_upper, exact
    )


def emitted_tails(
    interval: OutcomeInterval | EnvelopeInterval,
) -> tuple[TailBound, TailBound]:
    """Return the two tails of Eq. ``eq:budget-met``, at the EMITTED endpoints.

    ``Pr[N < k^-]`` and ``Pr[N > k^+]`` -- the two summands Eq.
    ``eq:completeness`` adds for this outcome. AT THE EMITTED ENDPOINTS, not at
    ``kappa^{+-}`` and not at the allocation: Remark ``rem:epsstar`` turns on
    that distinction, the integrality of ``k^{+-}`` and the guard both leaving
    budget unspent. Under an envelope the lower tail is the binomial's at
    ``p^-`` and the upper tail the binomial's at ``p^+`` (``thm:completeness-bound``
    with ``lem:envelope-dominance``).
    """
    if isinstance(interval, EnvelopeInterval):
        return (
            lower_tail(interval.rounds, interval.honest_lower, interval.k_lower),
            upper_tail(interval.rounds, interval.honest_upper, interval.k_upper),
        )
    return (
        lower_tail(interval.rounds, interval.honest, interval.k_lower),
        upper_tail(interval.rounds, interval.honest, interval.k_upper),
    )
