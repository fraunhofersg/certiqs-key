"""One run's check of the acceptance set against the feasible statistics.

``meat-core/req:unreachable-acceptance-set``, the run tier's part. The core
states the scope, the cap and its decision, the floor and the record
(:mod:`certiqs_key.meat_core.finitekey.consistency`); the solver submodule
runs the solve (:mod:`certiqs_key.solvers.frank_wolfe.minimal_divergence`).
What only the run tier can do is here:

* WHICH RUNS ARE CHECKED. Where the honest statistics and the constraint
  entries came from is known to the caller that composed the run, not to the
  engine; an instance's runner says so (``honest_supplied``,
  ``caller_constraint_entries`` of :func:`~certiqs_key.runs.pipeline.run_slice`).
* ONCE PER RUN. A run at one order solves at that order; a run whose order
  the outer alpha search chooses solves once, at the lowest order the search
  evaluates, which it fixes before it evaluates any (the first point of its
  coarse grid), or the lower end of its domain where that is lower
  (``alpha_0``, :func:`~certiqs_key.runs.alpha_search.alpha_zero`, the rule
  recorded as ``alpha_0_rule``), before its first evaluation, and every
  evaluation reads that one bound (:func:`searched_run`). Every evaluation of
  a search is an ordinary run from scratch, so the bound is held here for the
  search, keyed by the digests of the compiled declaration and of the
  acceptance set it was formed on: an evaluation whose declaration or
  acceptance set differs is an error, never a silent reuse.
* THE CAP, DECIDED ONCE, BEFORE ANY ORDER IS EVALUATED (item (iv)). The cap
  ``2^(-x)`` is one number per run, so the refusal is per run: where it is at
  most ``tau`` (``min_model_pass_probability``) the evaluation that formed the
  bound is refused at its solve stage with ``acceptance_set_unreachable``
  before its own solve, and the run is refused as a whole; a search stops
  there (``runs/alpha_search.py``).
* EACH ORDER'S DIAGNOSTIC (item (v)): ``n f(alpha')`` at every order the run
  evaluates, recorded and read by nothing.

WHERE IT SITS IN A RUN'S ORDER. The solve and the cap come first, before any
order is evaluated: row 10 of meat-core's ``fail_closed`` table. A run the
cap refuses is evaluated at no order, so neither the solve's own refusals nor
the strict option of ``foundations/req:snap-reference`` (iv) nor the run
tier's plausibility check (``runs/plausibility.py``) is reached.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from fractions import Fraction

from certiqs_key.foundations.dyadic import float_down
from certiqs_key.meat_core.finitekey.consistency import (
    Alpha0Rule,
    CapDecision,
    CheckScope,
    DivergenceBound,
    OrderDiagnostic,
    PassCap,
    StatisticsConsistency,
    check_min_model_pass_probability,
    check_scope,
    decide_pass_cap,
    order_diagnostic,
)
from certiqs_key.meat_core.reasons import RefusalReason

__all__ = [
    "UNREACHABLE_REASON",
    "RunCheck",
    "honest_supplied_from_note",
    "refusal_detail",
    "run_check",
    "searched_run",
]

#: The core's refusal string.
UNREACHABLE_REASON = str(RefusalReason.ACCEPTANCE_SET_UNREACHABLE)


@dataclass
class RunCheck:
    """One run's check: its scope, its bound and cap formed once, each order noted.

    ``alpha_0`` is fixed before any order is evaluated: on a searched run
    :func:`~certiqs_key.runs.alpha_search.alpha_zero`, the lowest order the
    search evaluates or the lower end of its domain where that is lower
    (``searched`` true); the run's fixed order otherwise (set by its one
    evaluation). ``alpha_0_rule`` records which rule of item (i) fixed it.
    """

    alpha_0: float | None = None
    searched: bool = False
    alpha_0_rule: Alpha0Rule | None = None
    scope: CheckScope | None = None
    tau: Fraction | None = None
    rounds: int | None = None
    bound: DivergenceBound | None = None
    #: Item (iv)'s cap and decision, formed with the bound; ``None`` where
    #: there is none.
    cap: PassCap | None = None
    #: The digests of the compiled declaration and the acceptance set the
    #: bound was formed on.
    formed_on: tuple[str, str] | None = None
    orders: list[OrderDiagnostic] = field(default_factory=list)

    @property
    def refused(self) -> bool:
        """Whether item (iv) refuses the run (decided on the exact ``x``)."""
        return self.cap is not None and self.cap.refused

    def begin(
        self,
        *,
        honest_supplied: bool,
        caller_constraint_entries: int,
        option: str,
        tau: Fraction,
        rounds: int,
        alpha: float,
    ) -> CheckScope:
        """Set the run's scope at its first evaluation; check it at every later one."""
        scope = check_scope(
            honest_supplied=honest_supplied,
            caller_constraint_entries=caller_constraint_entries,
            option=option,
        )
        tau = check_min_model_pass_probability(tau)
        if self.scope is None:
            self.scope, self.tau, self.rounds = scope, tau, rounds
            if self.alpha_0 is None:
                self.alpha_0 = alpha
                self.alpha_0_rule = Alpha0Rule.FIXED_ORDER
        elif (self.scope, self.tau, self.rounds) != (scope, tau, rounds):
            raise RuntimeError(
                "meat-core/req:unreachable-acceptance-set: one run's evaluations "
                "differ in whether the run is checked, in tau or in n"
            )
        return scope

    def ensure_bound(
        self, formed_on: tuple[str, str], solve: Callable[[float], DivergenceBound]
    ) -> DivergenceBound:
        """Return the run's bound, solving once and deciding the cap (items (i)-(iv)).

        ``formed_on`` are the digests of the compiled declaration and of the
        acceptance set of the evaluation asking; the bound is reused only for
        the same two. What the solve returns is kept whether or not it formed
        a bound: where none was formed, the reason is the run's outcome of the
        check, read by every later evaluation and not solved again. The solve
        returns that reason rather than raising it
        (:func:`~certiqs_key.solvers.frank_wolfe.minimal_divergence.bound_minimal_divergence`);
        what it raises concerns the run and keeps nothing here.
        """
        if self.bound is None:
            assert self.alpha_0 is not None
            assert self.rounds is not None and self.tau is not None
            bound = solve(self.alpha_0)
            self.bound = bound
            self.formed_on = formed_on
            if bound.bound is not None and bound.tier is not None:
                self.cap = decide_pass_cap(
                    rounds=self.rounds,
                    alpha_0=bound.alpha_0,
                    bound=bound.bound,
                    tier=bound.tier,
                    tau=self.tau,
                )
        elif self.formed_on != formed_on:
            raise RuntimeError(
                "meat-core/req:unreachable-acceptance-set: an evaluation of this "
                "run has another declaration or acceptance set than the one its "
                "bound was formed on, so the bound formed once is not this "
                "evaluation's"
            )
        return self.bound

    def note_order(self, alpha: float) -> None:
        """Record item (v)'s diagnostic ``n f`` at an order the run evaluates."""
        if self.scope is None or not self.scope.checked or self.rounds is None:
            return
        self.orders.append(
            order_diagnostic(alpha=alpha, bound=self.bound, rounds=self.rounds)
        )

    def record(self) -> StatisticsConsistency | None:
        """Return the run's ``statistics_consistency``; ``None`` before it began."""
        if self.scope is None or self.tau is None or self.rounds is None:
            return None
        return StatisticsConsistency(
            scope=self.scope,
            tau=self.tau,
            rounds=self.rounds,
            bound=self.bound,
            cap=self.cap,
            orders=tuple(self.orders),
            alpha_0_rule=self.alpha_0_rule,
        )


_CURRENT: ContextVar[RunCheck | None] = ContextVar("statistics_check_run", default=None)


@contextmanager
def searched_run(
    alpha_0: float, rule: Alpha0Rule = Alpha0Rule.LOWEST_EVALUATED_ORDER
) -> Iterator[RunCheck]:
    """Hold one check for every evaluation of an outer alpha search.

    ``alpha_0`` is :func:`~certiqs_key.runs.alpha_search.alpha_zero`: the
    lowest order the search evaluates, or the lower end of its declared
    domain where that is lower, so every order it evaluates is at least
    ``alpha_0`` (item (i)); ``rule`` says which. Every
    :func:`~certiqs_key.runs.pipeline.run_slice` called inside reads this
    check through :func:`run_check` rather than starting its own.
    """
    check = RunCheck(alpha_0=alpha_0, searched=True, alpha_0_rule=rule)
    token = _CURRENT.set(check)
    try:
        yield check
    finally:
        _CURRENT.reset(token)


def run_check() -> RunCheck:
    """Return the search's check where a search holds one, else a run's own."""
    current = _CURRENT.get()
    return RunCheck() if current is None else current


def honest_supplied_from_note(note: Mapping[str, object] | None) -> bool:
    """Read whether an honest law was supplied off a run's honest-model note.

    The fallback where the caller does not say: a note marked ``overridden``
    (a facade or MCP honest table, an injected provider) or ``supplied``
    stands for a law the caller gave in place of the engine's model.
    """
    if note is None:
        return False
    return bool(note.get("overridden")) or bool(note.get("supplied"))


#: How the comparison was decided, in the refusal's words.
_DECISION_WORDS: dict[CapDecision, str] = {
    CapDecision.EXACT: "decided exactly",
    CapDecision.ENCLOSURE: "decided against a rigorous enclosure of log2(1/tau)",
    CapDecision.UNDECIDED: (
        "undecided, x lying within the enclosure of log2(1/tau), and refused "
        "because a refusal only withholds a key"
    ),
}


def refusal_detail(cap: PassCap, bound: DivergenceBound) -> str:
    """Return the detail of a run refused under item (iv), in one sentence.

    An undecided comparison is not said to put the cap at most ``tau``: it
    only fails to show the cap above it.
    """
    verdict = (
        "which is not shown to exceed"
        if cap.decision is CapDecision.UNDECIDED
        else "which is at most"
    )
    return (
        "meat-core/req:unreachable-acceptance-set (iv): no feasible state of the "
        "declaration has its per-round statistics in the acceptance set (a "
        f"{bound.tier} lower bound {float(bound.bound or 0):.6g} on the value "
        f"with every pair dropped at alpha_0 = {bound.alpha_0!r}), so devices "
        "behaving as the declaration says pass the acceptance test with "
        f"probability at most 2^-x, x = {float_down(cap.exponent)!r} (rounded "
        "down) "
        f"(meat-core/prop:model-pass-bound (ii), {cap.tier} tier), {verdict} "
        f"min_model_pass_probability = {cap.tau} "
        f"({_DECISION_WORDS[cap.decision]}); the run is refused as a whole and "
        "evaluated at no order"
    )
