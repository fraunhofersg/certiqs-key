"""The check of the acceptance set against the feasible statistics.

``meat-core/req:unreachable-acceptance-set``, the core's part: which runs are
checked, the cap on the pass probability of devices as declared and the
refusal of item (iv), the proven floor of item (iii) at each order the run
evaluates, and the record of item (v). The once-per-run solve of items (i)
and (ii) is the solver submodule's
(:mod:`certiqs_key.solvers.frank_wolfe.minimal_divergence`), which returns a
:class:`DivergenceBound`; the run tier (:mod:`certiqs_key.runs.statistics_check`)
holds that bound for the run, decides the cap once, before any order is
evaluated, and records each order's diagnostic.

WHAT A POSITIVE BOUND PROVES. With every pair dropped the objective is
``alpha/(alpha-1)`` times the divergence between an accepted distribution and
the statistics of a feasible state (``prop:minimal-divergence`` (i)), so a
lower bound ``b`` on that value at one order ``alpha_0`` gives
``D_min >= (alpha_0-1)/alpha_0 b``. By ``prop:model-pass-bound`` (ii), devices
the declaration admits, run so that each round's acceptance value given the
earlier ones follows the statistics of a feasible state, then pass the
acceptance test with probability at most ``2^(-x)``,
``x = n (alpha_0-1)/alpha_0 b``: the cap, proven where ``b`` is certified.

THE REFUSAL IS ON THE CAP (item (iv)). A run whose cap is at most ``tau``,
the run option ``min_model_pass_probability`` (default one half), is refused
as a whole: its own model expects it to abort. ``x >= log2(1/tau)`` is decided
exactly where ``tau = 2^(-k)`` (``x >= k``), and otherwise against a rigorous
enclosure of ``log2(1/tau)`` (:func:`~certiqs_key.foundations.balls.log2_enclosure`),
an undecided comparison refusing, since a refusal only withholds a key. The
decision carries the tier of ``b``. A positive bound alone refuses nothing: a
``b`` at rounding level gives a cap near one, so no rounding floor on ``b`` is
needed.

EXACT ARITHMETIC. ``b`` is an exact rational (the certified number) or a
binary64 number (the first-order number), both exact rationals; ``alpha_0`` is
a binary64 number and ``n`` an integer, so ``x`` is exact and the decision is
made on it. The record carries ``x`` and each order's ``n f`` rounded toward
``-inf`` (:func:`float_down`), so that ``2^(-x)`` at the recorded ``x`` stays an
upper bound, and carries the refusal as decided on the exact ``x``.

THE SIGN OF THE SOLVE'S ESTIMATE DECIDES NOTHING (item (ii)). ``O_0`` is no
estimate of the run: ``b`` is formed whatever its sign, and a negative ``O_0``
is recorded as a diagnostic (``estimate_negative``).

NOTHING HERE READS A KEY LENGTH, AND NO NUMBER OF THE RUN READS THESE ENTRIES
(item (v)). The refusal only withholds a key.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction
from typing import Any

from certiqs_key.foundations.dyadic import float_down

__all__ = [
    "DEFAULT_MIN_MODEL_PASS_PROBABILITY",
    "DEFAULT_STATISTICS_CHECK",
    "STATISTICS_CHECK_BUDGET_SHARE",
    "STATISTICS_CHECK_OPTIONS",
    "UNCHECKED_PREMISE",
    "Alpha0Rule",
    "CapDecision",
    "CheckScope",
    "DivergenceBound",
    "NoBoundReason",
    "NoCapReason",
    "OrderDiagnostic",
    "PassCap",
    "StatisticsConsistency",
    "StopCause",
    "UncheckedReason",
    "check_min_model_pass_probability",
    "check_scope",
    "decide_pass_cap",
    "dmin_lower_bound",
    "model_pass_exponent",
    "order_diagnostic",
    "proven_floor",
]

#: The run option ``statistics_check`` (item (i)'s opening paragraph):
#: ``on`` by default, ``off`` opts a run out and is recorded.
STATISTICS_CHECK_OPTIONS: tuple[str, ...] = ("on", "off")
DEFAULT_STATISTICS_CHECK = "on"
#: The run option ``min_model_pass_probability``, ``tau`` of item (iv), an
#: exact rational in ``(0, 1]``; default one half, exactly.
DEFAULT_MIN_MODEL_PASS_PROBABILITY = Fraction(1, 2)
#: The premise an unchecked run names as the caller's to vouch for.
UNCHECKED_PREMISE = "A-REACH"
#: ``statistics_check_budget_share`` (meat-core interface, fixed by that file):
#: the share of the wall budget of one evaluation of the run that the check's
#: solve gets as its own wall budget (item (i)). ``b`` is a lower bound at any
#: effort, so the share bears on how tight the cap is and on wall time, never
#: on soundness; a constant, not a run option.
STATISTICS_CHECK_BUDGET_SHARE = Fraction(1, 4)


class Alpha0Rule(StrEnum):
    """Which rule of item (i) fixed ``alpha_0``."""

    #: The run's fixed order.
    FIXED_ORDER = "fixed_order"
    #: The lowest order the run's order search evaluates, which the search
    #: fixes before it evaluates any and evaluates none below.
    LOWEST_EVALUATED_ORDER = "lowest_evaluated_order"
    #: The lower end of the domain the order search declares.
    DOMAIN_LOWER_END = "domain_lower_end"


class UncheckedReason(StrEnum):
    """Why a run is not checked (the requirement's opening paragraph)."""

    #: Its honest statistics are the engine's own model of the declared
    #: devices and its declaration carries no constraint entry the caller
    #: declared.
    OUT_OF_SCOPE = "out_of_scope"
    #: It is in scope and sets ``statistics_check`` to ``off``.
    OPTED_OUT = "opted_out"


class NoBoundReason(StrEnum):
    """Why the solve formed no bound ``b`` (item (ii)); the run proceeds.

    The sign of the solve's estimate is none of them: ``b`` is formed
    whatever it is, a negative estimate being recorded as a diagnostic.
    """

    #: ``alpha_0`` is not in ``(1, infinity)``, where the program is evaluated
    #: (``req:objective-alpha-domain``): the solve is refused and does not run.
    ALPHA_OUTSIDE_OBJECTIVE_DOMAIN = "alpha_0_outside_objective_domain"
    #: The first-order number of the dropped program is withdrawn (no iterate
    #: contributed; the solver's withdrawal reason is recorded beside it).
    FIRST_ORDER_WITHDRAWN = "first_order_withdrawn"
    #: The solve did not complete: the linear oracle left a step unsolved or
    #: failed without a status, or the assessment of a point failed
    #: numerically (``stop_cause`` and ``detail`` say which).
    SOLVE_NOT_COMPLETED = "solve_not_completed"


class StopCause(StrEnum):
    """Item (v)'s stop cause, as the solver reports it, in three common names.

    Item (v) records "the cause it stopped on, as the solver reports it (such
    as the gap target, the iteration cap or the budget)": these three are the
    names given to the solver's statuses that mean them; every other status
    (a stagnated iterate, a withdrawn hypothesis, an oracle failure, ...) is
    recorded as the solver states it.
    """

    GAP_TARGET = "gap_target"
    ITERATION_CAP = "iteration_cap"
    BUDGET = "budget"


@dataclass(frozen=True)
class CheckScope:
    """Whether a run is checked and, where not, why (the opening paragraph).

    ``honest_supplied``: the acceptance set is built from an honest law or
    envelope the caller gave as numbers. ``caller_constraint_entries``: how
    many constraint entries of the declaration the caller declared (not the
    compiler or a reduction).
    """

    checked: bool
    unchecked_reason: UncheckedReason | None
    option: str
    honest_supplied: bool
    caller_constraint_entries: int

    def as_record(self) -> dict[str, Any]:
        """Return the scope entries of ``statistics_consistency``."""
        return {
            "checked": self.checked,
            "unchecked_reason": (
                None if self.unchecked_reason is None else str(self.unchecked_reason)
            ),
            "unchecked_premise": None if self.checked else UNCHECKED_PREMISE,
            "statistics_check": self.option,
            "honest_statistics_supplied": self.honest_supplied,
            "caller_constraint_entries": self.caller_constraint_entries,
        }


def check_scope(
    *, honest_supplied: bool, caller_constraint_entries: int, option: str
) -> CheckScope:
    """Decide whether a run is checked (``req:unreachable-acceptance-set``).

    A run is checked when its honest statistics are supplied as numbers or its
    declaration carries a constraint entry the caller declared, unless it sets
    ``statistics_check`` to ``off``. A run outside that scope is
    ``out_of_scope`` whatever the option says, since it would not be checked
    with the option on either.
    """
    if option not in STATISTICS_CHECK_OPTIONS:
        raise ValueError(
            f"statistics_check is {option!r}; admitted: "
            f"{list(STATISTICS_CHECK_OPTIONS)}"
        )
    if caller_constraint_entries < 0:
        raise ValueError("caller_constraint_entries is a count")
    in_scope = honest_supplied or caller_constraint_entries > 0
    reason = (
        UncheckedReason.OUT_OF_SCOPE
        if not in_scope
        else UncheckedReason.OPTED_OUT
        if option == "off"
        else None
    )
    return CheckScope(
        checked=reason is None,
        unchecked_reason=reason,
        option=option,
        honest_supplied=honest_supplied,
        caller_constraint_entries=caller_constraint_entries,
    )


@dataclass(frozen=True)
class DivergenceBound:
    """What the once-per-run solve formed: items (i), (ii) and (v)'s solve entries.

    ``bound`` is ``b``: the certified number where a point is certified, the
    first-order number otherwise, ``None`` where no bound was formed
    (``no_bound_reason`` then says why). ``estimate`` is ``O_0``, the dropped
    objective at the returned point, where the solve returned one. The solve
    runs on the declaration the run searches (item (ii)), whatever declaration
    the key length is formed on.
    """

    alpha_0: float
    bound: Fraction | None
    #: ``certified`` or ``first-order`` (foundations/def:tiers), with ``bound``.
    tier: str | None
    no_bound_reason: NoBoundReason | None = None
    #: Where the solve ran: :data:`STATISTICS_CHECK_BUDGET_SHARE` and the wall
    #: budget it gave the solve (``None`` where the evaluation has no wall
    #: budget, the run's iteration cap and gap target alone bounding it).
    budget_share: Fraction | None = None
    budget_seconds: float | None = None
    #: Where the solve ran: item (v)'s cause where it is one of
    #: :class:`StopCause`, otherwise the solver's own status.
    stop_cause: str | None = None
    solver_status: str | None = None
    termination: str | None = None
    estimate: float | None = None
    #: Whether the returned point is established in the relaxed set.
    estimate_relaxed_member: bool | None = None
    first_order: float | None = None
    #: The solver's withdrawal reason where the first-order number is withdrawn.
    withdrawal: str | None = None
    #: The certified evaluation's record (frank-wolfe ``certified_evaluation``),
    #: or ``None`` where it did not run.
    certification: Mapping[str, Any] | None = None
    iterations: int | None = None
    seconds: float = 0.0
    detail: str | None = None
    declaration: str = "searched"

    def __post_init__(self) -> None:
        """Hold a bound and its reason apart: exactly one is present."""
        if (self.bound is None) == (self.no_bound_reason is None):
            raise ValueError("a bound is formed, or the reason none was is recorded")
        if (self.bound is None) != (self.tier is None):
            raise ValueError("a bound carries its tier, and only a bound does")

    @property
    def formed(self) -> bool:
        """Whether ``b`` was formed."""
        return self.bound is not None

    @property
    def estimate_negative(self) -> bool | None:
        """Whether ``O_0`` is negative: a diagnostic, refusing nothing (item (ii))."""
        if self.estimate is None or math.isnan(self.estimate):
            return None
        return self.estimate < 0

    def as_record(self) -> dict[str, Any]:
        """Return the solve entries of ``statistics_consistency`` (item (v))."""
        bound = self.bound
        lower = None if bound is None else dmin_lower_bound(bound, self.alpha_0)
        return {
            "declaration": self.declaration,
            "alpha_0": self.alpha_0,
            "bound": None if bound is None else float_down(bound),
            "bound_tier": self.tier,
            "dmin_lower_bound": None if lower is None else float_down(lower),
            "no_bound_reason": (
                None if self.no_bound_reason is None else str(self.no_bound_reason)
            ),
            "detail": self.detail,
            "stop_cause": self.stop_cause,
            "solver_status": self.solver_status,
            "termination": self.termination,
            "budget_share": (
                None if self.budget_share is None else str(self.budget_share)
            ),
            "budget_seconds": self.budget_seconds,
            "estimate": _finite(self.estimate),
            "estimate_negative": self.estimate_negative,
            "estimate_relaxed_member": self.estimate_relaxed_member,
            "gap": (
                None
                if bound is None or self.estimate is None
                or not math.isfinite(self.estimate)
                else float(Fraction(self.estimate) - bound)
            ),
            "first_order_number": self.first_order,
            "withdrawal": self.withdrawal,
            "certified_evaluation": (
                None if self.certification is None else dict(self.certification)
            ),
            "iterations": self.iterations,
            "seconds": self.seconds,
        }


def _finite(value: float | None) -> float | str | None:
    """Return a number for JSON: ``"inf"`` for an infinite one, as ``h_low``."""
    if value is None:
        return None
    return value if math.isfinite(value) else "inf"


def _order_factor(alpha: float) -> Fraction:
    """Return ``alpha/(alpha-1)`` exactly, for ``alpha`` in ``(1, infinity)``."""
    exact = Fraction(alpha)
    if not exact > 1:
        raise ValueError(f"the order {alpha!r} is not in (1, infinity)")
    return exact / (exact - 1)


def dmin_lower_bound(bound: Fraction, alpha_0: float) -> Fraction:
    """Return ``(alpha_0-1)/alpha_0 b``, a lower bound on ``D_min``.

    ``prop:minimal-divergence`` (iv), eq:dmin-bracket's lower inequality.
    """
    return bound / _order_factor(alpha_0)


def proven_floor(alpha: float, alpha_0: float, bound: Fraction) -> Fraction:
    """Return ``f(alpha')`` of item (iii), exactly, in bits per round.

    ``alpha'/(alpha'-1) (alpha_0-1)/alpha_0 b`` where ``b > 0``, ``0`` where
    ``b <= 0``: by ``prop:minimal-divergence`` (ii) and (iv) it is at most
    ``alpha'/(alpha'-1) D_min``, which is at most ``h_low`` at ``alpha'``.
    """
    if bound <= 0:
        return Fraction(0)
    return _order_factor(alpha) * dmin_lower_bound(bound, alpha_0)


def model_pass_exponent(
    rounds: int, alpha_0: float, bound: Fraction
) -> Fraction | None:
    """Return the exponent ``x = n (alpha_0-1)/alpha_0 b`` in bits, exactly.

    ``meat-core/prop:model-pass-bound`` (ii) and
    ``meat-core/req:unreachable-acceptance-set`` (iv): where ``b > 0``, devices
    the declaration admits, run so that each round's acceptance value given
    the earlier ones follows the statistics of a feasible state, pass the
    acceptance test with probability at most ``2^(-x)``. ``None`` where
    ``b <= 0``: there is no cap (item (iv)). The record carries
    ``x`` rounded toward ``-inf``, so that the cap it shows stays an upper
    bound.
    """
    if isinstance(rounds, bool) or rounds < 1:
        raise ValueError(f"the number of rounds {rounds!r} is not a positive integer")
    if bound <= 0:
        return None
    return rounds * dmin_lower_bound(bound, alpha_0)


def check_min_model_pass_probability(tau: object) -> Fraction:
    """Return ``tau`` where it is an exact rational in ``(0, 1]``, else refuse it."""
    if isinstance(tau, bool) or not isinstance(tau, (Fraction, int)):
        raise ValueError(
            f"min_model_pass_probability is {tau!r}; it is an exact rational "
            "in (0, 1]"
        )
    tau = Fraction(tau)
    if not 0 < tau <= 1:
        raise ValueError(f"min_model_pass_probability {tau} is not in (0, 1]")
    return tau


class CapDecision(StrEnum):
    """How item (iv) decided ``x >= log2(1/tau)``."""

    #: ``tau = 2^(-k)``: ``x`` compared with the integer ``k``.
    EXACT = "exact"
    #: Any other ``tau``: ``x`` outside a rigorous enclosure of ``log2(1/tau)``.
    ENCLOSURE = "enclosure"
    #: ``x`` inside the enclosure: undecided, and refused.
    UNDECIDED = "undecided"


class NoCapReason(StrEnum):
    """Why a checked run has no cap (item (iv)); nothing is refused."""

    #: ``b <= 0``: no mismatch is proven.
    BOUND_NOT_POSITIVE = "bound_not_positive"
    #: No bound was formed (the solve's ``no_bound_reason`` says why).
    NO_BOUND_FORMED = "no_bound_formed"


def _power_of_two_exponent(tau: Fraction) -> int | None:
    """Return ``k`` where ``tau = 2^(-k)`` for an integer ``k >= 0``, else ``None``."""
    if tau.numerator != 1:
        return None
    k = tau.denominator.bit_length() - 1
    return k if tau.denominator == 1 << k else None


@dataclass(frozen=True)
class PassCap:
    """Item (iv)'s cap and decision: ``x`` exact, ``tau``, and the refusal.

    ``exponent`` is ``x = n (alpha_0-1)/alpha_0 b``: devices as declared pass
    the acceptance test with probability at most ``2^(-x)``
    (``prop:model-pass-bound`` (ii)), with the tier of ``b``. ``refused`` is
    decided on the exact ``x``.
    """

    exponent: Fraction
    tier: str
    tau: Fraction
    decision: CapDecision
    refused: bool


def decide_pass_cap(
    *, rounds: int, alpha_0: float, bound: Fraction, tier: str, tau: Fraction
) -> PassCap | None:
    """Item (iv): the cap ``2^(-x)`` and whether it refuses the run.

    ``None`` where ``b <= 0``: there is no cap, and nothing is refused. Where
    ``tau = 2^(-k)`` the run is refused exactly when ``x >= k``; otherwise
    against an enclosure ``[lo, hi]`` of ``log2(1/tau)``: refused where
    ``x >= hi``, not where ``x < lo``, and refused, undecided, in between.
    """
    tau = check_min_model_pass_probability(tau)
    exponent = model_pass_exponent(rounds, alpha_0, bound)
    if exponent is None:
        return None
    k = _power_of_two_exponent(tau)
    if k is not None:
        return PassCap(exponent, tier, tau, CapDecision.EXACT, exponent >= k)
    # Imported here: the optional arithmetic library loads only where a
    # threshold that is not a power of two is compared.
    from certiqs_key.foundations.balls import log2_enclosure

    lo, hi = log2_enclosure(1 / tau)
    if exponent >= hi:
        return PassCap(exponent, tier, tau, CapDecision.ENCLOSURE, True)
    if exponent < lo:
        return PassCap(exponent, tier, tau, CapDecision.ENCLOSURE, False)
    return PassCap(exponent, tier, tau, CapDecision.UNDECIDED, True)


@dataclass(frozen=True)
class OrderDiagnostic:
    """One order the run evaluated: ``n f(alpha')`` of item (v), a diagnostic.

    ``proven_part`` is ``n f(alpha')`` (``None`` where no bound was formed).
    It refuses nothing and the report does not show it; it satisfies
    ``(alpha'-1)/alpha' n f(alpha') = x`` where ``b > 0``.
    """

    alpha: float
    proven_part: Fraction | None

    def as_record(self) -> dict[str, Any]:
        """Return the per-order entry of ``statistics_consistency``."""
        return {
            "alpha": self.alpha,
            "proven_part_bits": (
                None if self.proven_part is None else float_down(self.proven_part)
            ),
        }


def order_diagnostic(
    *, alpha: float, bound: DivergenceBound | None, rounds: int
) -> OrderDiagnostic:
    """Return item (v)'s diagnostic at the order ``alpha`` the run evaluates."""
    if bound is None or bound.bound is None:
        return OrderDiagnostic(alpha=alpha, proven_part=None)
    floor = proven_floor(alpha, bound.alpha_0, bound.bound)
    return OrderDiagnostic(alpha=alpha, proven_part=rounds * floor)


@dataclass(frozen=True)
class StatisticsConsistency:
    """The run's ``statistics_consistency`` record (item (v)), as one value.

    ``bound`` is ``None`` on a run that is not checked, or one that ended
    before the solve; ``cap`` is item (iv)'s, ``None`` where there is none;
    ``alpha_0_rule`` which rule of item (i) fixed ``alpha_0``; ``orders`` holds
    every order the run evaluated, in order (none on a run refused under
    item (iv), which evaluates none).
    """

    scope: CheckScope
    tau: Fraction
    rounds: int
    bound: DivergenceBound | None = None
    cap: PassCap | None = None
    orders: tuple[OrderDiagnostic, ...] = field(default=())
    alpha_0_rule: Alpha0Rule | None = None

    @property
    def refused(self) -> bool:
        """Whether item (iv) refused the run, as decided on the exact ``x``."""
        return self.cap is not None and self.cap.refused

    @property
    def no_cap_reason(self) -> NoCapReason | None:
        """Why a checked run whose solve ran has no cap; ``None`` otherwise."""
        if not self.scope.checked or self.bound is None or self.cap is not None:
            return None
        if self.bound.bound is None:
            return NoCapReason.NO_BOUND_FORMED
        return NoCapReason.BOUND_NOT_POSITIVE

    def as_record(self) -> dict[str, Any]:
        """Return ``payload.statistics_consistency``.

        ``model_pass_exponent_bits`` is ``x`` rounded toward ``-inf`` and
        ``model_pass_exponent_tier`` the tier of ``b``; ``model_pass_decision``
        how item (iv) decided; ``refused`` its decision on the exact ``x``;
        ``no_cap_reason`` why there is no cap, where the solve ran and formed
        none.
        """
        cap = self.cap
        no_cap = self.no_cap_reason
        return {
            **self.scope.as_record(),
            "min_model_pass_probability": str(self.tau),
            "rounds": self.rounds,
            "alpha_0_rule": (
                None if self.alpha_0_rule is None else str(self.alpha_0_rule)
            ),
            "solve": None if self.bound is None else self.bound.as_record(),
            "model_pass_exponent_bits": (
                None if cap is None else float_down(cap.exponent)
            ),
            "model_pass_exponent_tier": None if cap is None else cap.tier,
            "model_pass_decision": None if cap is None else str(cap.decision),
            "no_cap_reason": None if no_cap is None else str(no_cap),
            "refused": self.refused,
            "orders": [order.as_record() for order in self.orders],
        }
