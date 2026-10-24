"""def:endpoint-rule -- what a rule is, the guard, and the three instances.

``binomial-box`` has ONE definition of what an endpoint rule is and ONE CLAIM
PER INSTANCE. ``def:endpoint-rule`` asks of a rule ``R`` that it assign to
every ``(n, p, eps^-, eps^+)`` two integers with

    (a) R^-, R^+ in {0, ..., n} and Pr[N < R^-] <= eps^-, Pr[N > R^+] <= eps^+
    (b) if 0 < p < 1:  R^- = 0 at eps^- = 0  and  R^+ = n at eps^+ = 0
    (c) R^- = R^+ = 0 at p = 0 and R^- = R^+ = n at p = 1, for every eps

and calls the rule MONOTONE IN THE ALLOCATION when ``eps^- -> R^-`` is
non-decreasing and ``eps^+ -> R^+`` non-increasing. Adding a rule is one claim
proving an instance of that definition, one row of the submodule's
``rule_table`` and one value of the core's ``endpoint_rule`` input, and nothing
else anywhere.

(b) AND (c) ARE ENFORCED AT ONE PLACE, AND THIS IS IT.
:meth:`EndpointRule.endpoints` returns the degenerate-mass values at
``p in {0, 1}`` and the zero-budget value on whichever side carries a zero
budget, BEFORE any rule's own evaluation is reached. The conventions are the
old ``SA7`` (iii) and ``SA3`` (v) computations made requirements, so that
``thm:monotonicity-limits`` (iii), (vi) and ``rem:epsstar`` hold for EVERY rule; a rule
that had to re-derive them would be a rule that could get them wrong.

WHAT THE SWEEP'S OWN SHORTCUTS ARE DOING IN ``intervals``.
:func:`~certiqs_key.statistics.intervals.extremal_endpoints` carries the same
two conventions inside itself: they are the proof
of ``thm:monotonicity-limits`` (iii) read as code and are what keeps the ``ecomp = 0``
limit free. They are unreachable through this class and are left where they are
because that function is unit-tested directly, and is on
the route the frozen 55 cases pin -- and because two agreeing statements of a
convention are cheaper to read than one statement and one cross-reference.

THE GUARD IS RULE-INDEPENDENT AND WAS ALREADY WRITTEN THAT WAY.
Eq. ``eq:guard``, ``k^- = min{R^-, floor(np)}`` and ``k^+ = max{R^+, ceil(np)}``,
is :func:`~certiqs_key.statistics.intervals.guarded_endpoints`, which takes two
integers and knows nothing about where they came from. ``lem:guard`` proves its
four properties -- the ordering, the budgets met, the exact cost, the
unconditional ``1/n`` distance from the honest value -- for EVERY admissible
rule, so no second implementation is needed and none is written. It is
re-exported here so that a reader of this module finds it beside the definition
it belongs to.

THE THREE INSTANCES THIS REPOSITORY CARRIES
===========================================
    endpoint_rule  tail_evaluation  the rule                monotone in eps
    exact          sweep            def:interval            YES
    exact          enclosure        prop:bracketed-endpoints NOT CLAIMED
    bernstein      either           prop:rule-bernstein      YES

The third column is ``binomial-box/interface.yaml``'s ``rule_table``, and the
fourth is exactly the hypothesis ``thm:monotonicity-limits`` (i) and (ii) read: ON THE
``exact`` + ``enclosure`` ROW A CONSUMER MAY NOT READ "the set shrinks as the
budget grows" OR the infimum consequence for ``h_low``. Everything else the
table lists is unaffected, monotonicity in the allocation being a hypothesis of
those two clauses alone.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import ClassVar

from certiqs_key.statistics.bernstein import (
    DEFAULT_BERNSTEIN_PARAMETERS,
    BernsteinParameters,
    bernstein_lower_endpoint,
    bernstein_upper_endpoint,
)
from certiqs_key.statistics.enclosure import (
    DEFAULT_ENCLOSURE_PARAMETERS,
    EnclosureParameters,
    bracketed_lower_endpoint,
    bracketed_upper_endpoint,
    lower_tail_upper_bound,
    tail_upper_bound,
)
from certiqs_key.statistics.intervals import (
    OutcomeInterval,
    extremal_endpoints,
    guarded_endpoints,
    interval_record,
)

__all__ = [
    "ENDPOINT_RULES",
    "BernsteinRule",
    "EnclosureExactRule",
    "EndpointRule",
    "EndpointRuleName",
    "RuleEndpoints",
    "SweepExactRule",
    "TailEvaluation",
    "enclosure_rows",
    "guarded_endpoints",
    "interval_for_rule",
    "resolve_rule",
]

_ZERO = Fraction(0)
_ONE = Fraction(1)


class EndpointRuleName(StrEnum):
    """The values of the ``endpoint_rule`` input. There is no third.

    The inputs table of ``interface.yaml`` fixes the domain as a CLOSED
    enumeration -- no claim does, and the closure is what makes the tenth
    reason code ``endpoint_rule_unknown`` decidable.
    """

    #: ``def:interval``, the exact binomial quantile rule. The default.
    EXACT = "exact"
    #: ``prop:rule-bernstein``, the closed-form rule.
    BERNSTEIN = "bernstein"


class TailEvaluation(StrEnum):
    """The values of the ``tail_evaluation`` input. There is no third.

    IT SELECTS HOW A TAIL COMPARISON IS DECIDED AND NEVER WHAT IS DECIDED.
    """

    #: The closed forms of ``cor:tail-forms``, decided exactly by
    #: ``lem:exact-strict-tails``, swept from zero. The default,
    #: and the route the frozen oracles pin.
    SWEEP = "sweep"
    #: The local enclosures of ``prop:bracketed-endpoints``.
    ENCLOSURE = "enclosure"


@dataclass(frozen=True)
class RuleEndpoints:
    """What a rule returns: two integers and what the evaluation knows.

    ``lower`` and ``upper`` are ``R^-`` and ``R^+`` BEFORE the guard. The three
    optional fields are the enclosure route's diagnostics and are ``None`` on
    every other route: ``lower_decided`` and ``upper_decided`` are the bracket
    verdict of ``prop:bracketed-endpoints`` (ii), which the output row
    ``endpoint_exact`` reports, and ``tails_exact`` says whether the endpoints
    were decided against exact tails (the sweep's own meaning, carried).
    """

    lower: int
    upper: int
    tails_exact: bool = True
    lower_decided: bool | None = None
    upper_decided: bool | None = None


def enclosure_rows(
    parameters: EnclosureParameters,
) -> tuple[tuple[str, int], ...]:
    """Return the enclosure evaluation's parameters, under the interface's names.

    ONE PLACE, because they are recorded on every route whose
    ``tail_evaluation`` is ``enclosure`` and not only on the one whose RULE is
    the enclosure evaluation: on ``bernstein`` + ``enclosure`` the endpoints are
    the Bernstein rule's and the reported figure is the sum of the two
    ENCLOSURE upper bounds at the guarded endpoints
    (``binomial-box/interface.yaml``, ``completeness_report``, its fourth row),
    so these numbers decide that figure too.

    EACH NAME IS THE PATH INTO THE SUBMODULE INTERFACE: the block it is
    declared in, a dot, and the row's own name, so that a reader of an emitted
    ``honest_model`` can find the row that sized it. THE BLOCK IS NOT
    DECORATION on the route where both blocks apply: ``the_bernstein_rule`` and
    ``the_enclosure_route`` each declare a ``root_exponent_j`` and a
    ``root_precision_bits``, and on ``bernstein`` + ``enclosure`` the two carry
    DIFFERENT VALUES, so an unqualified union would put two numbers under one
    name.

    The window is ADAPTIVE -- it starts at ``window_start``, doubles until the
    majorant is under ``2^-window_target_bits`` of the window, stops at
    ``window_length_T``, and holds its dyadic products at ``window_precision``
    significant bits -- so the ``window_length_T`` row's single name covers
    FOUR numbers and all four are recorded: a record naming only the cap would
    not identify a run that never reached it.

    ``window_precision`` IS THE ONE FIELD WITH NO ROW OF ITS OWN and is easy to
    miss. It is
    not cosmetic: at n = 60, p = 1/4, ecomp = 1/10 on ``exact`` + ``enclosure``
    the completeness figure moves at 12 bits and THE BOX moves at 6, so two
    runs with the same inputs, rule, evaluation and recorded parameters could
    emit different sets -- which is the one thing the record exists to prevent.
    EVERY FIELD OF THE PARAMETER OBJECT IS RECORDED NOW, and the property test
    ``test_the_record_names_every_parameter_the_figure_depends_on`` asserts
    that against :func:`dataclasses.fields` rather than against a list, so a
    field added later cannot be missed the same way.
    """
    block = "the_enclosure_route"
    return (
        (f"{block}.root_exponent_j", parameters.root_exponent),
        (f"{block}.root_precision_bits", parameters.root_precision),
        (f"{block}.wallis_length_M", parameters.wallis_length),
        (f"{block}.window_length_T", parameters.window_cap),
        (f"{block}.window_start", parameters.window_start),
        (f"{block}.window_target_bits", parameters.window_target_bits),
        (f"{block}.window_precision", parameters.window_precision),
    )


class EndpointRule(ABC):
    """An admissible endpoint rule, ``def:endpoint-rule``.

    A subclass implements :meth:`_raw_endpoints` for ``0 < p < 1`` and a
    positive budget on the side asked for; (b) and (c) are this class's and are
    applied before that method is reached. Every rule of this module is reached
    through :meth:`endpoints` and through nothing else.

    AN INSTANCE CARRIES THE WHOLE ROUTE, not only the rule: the
    ``tail_evaluation`` in force and the enclosure parameters in force, beside
    whatever parameters the rule itself takes. That is what makes
    :meth:`recorded_parameters` able to name every number the emitted figure
    depends on, and what keeps a caller's parameters from changing the reported
    figure without changing the endpoints they were passed to compute.
    """

    #: The value of the ``endpoint_rule`` input this rule answers to.
    name: ClassVar[EndpointRuleName]
    #: The value of ``tail_evaluation`` an instance carries when the caller
    #: names none. For the two exact instances it is the one that selects them;
    #: the Bernstein rule is selected by either, and its default here is the
    #: request's own default.
    default_evaluation: ClassVar[TailEvaluation]
    #: Whether this instance's own proposition proves it monotone in the
    #: allocation, which is the hypothesis ``thm:monotonicity-limits`` (i) and (ii)
    #: read.
    monotone_in_the_allocation: ClassVar[bool]

    def __init__(
        self,
        evaluation: TailEvaluation | None = None,
        enclosure_parameters: EnclosureParameters = DEFAULT_ENCLOSURE_PARAMETERS,
    ) -> None:
        """Fix the route and its parameters for the life of the rule object."""
        self.evaluation = (
            self.default_evaluation if evaluation is None else evaluation
        )
        self.enclosure_parameters = enclosure_parameters

    @abstractmethod
    def _raw_endpoints(
        self,
        rounds: int,
        honest: Fraction,
        eps_lower: Fraction,
        eps_upper: Fraction,
    ) -> RuleEndpoints:
        """Return the rule's own endpoints for ``0 < p < 1``."""

    def own_parameters(self) -> tuple[tuple[str, int], ...]:
        """Return the parameters THE RULE ITSELF takes, and no others.

        Empty for both exact instances: the sweep has none, and the enclosure
        evaluation's are the enclosure parameters, which
        :meth:`recorded_parameters` adds on every enclosure route from one
        place.
        """
        return ()

    def recorded_parameters(self) -> tuple[tuple[str, int], ...]:
        """Return every evaluation parameter in force, for the ``honest_model``.

        ``binomial-box/interface.yaml``, ``evaluation_parameters.recorded_per_run``:
        two runs with the same inputs and different parameters may emit
        different endpoints AND different figures, all of them admissible, so a
        record that did not name the parameters would not identify what was
        computed. THE LIST IS THE UNION of the rule's own parameters and the
        enclosure parameters in force wherever the evaluation is ``enclosure``,
        whichever rule ran.
        """
        rows = self.own_parameters()
        if self.evaluation is TailEvaluation.ENCLOSURE:
            rows = rows + enclosure_rows(self.enclosure_parameters)
        return rows

    def endpoints(
        self,
        rounds: int,
        honest: Fraction,
        eps_lower: Fraction,
        eps_upper: Fraction,
    ) -> RuleEndpoints:
        """Return ``(R^-, R^+)`` with ``def:endpoint-rule`` (b) and (c) applied.

        (c) first, because at ``p in {0, 1}`` the count is deterministic and
        both budgets are unspent whatever they are; then (b) per side, because
        a zero budget buys no constraint on that side and a rule evaluating
        ``ln(1 / 0)`` would be evaluating something the definition already
        answers.

        BOTH CONVENTIONS REPORT A DECIDED BRACKET, and that is not bookkeeping:
        at ``p in {0, 1}`` the emitted endpoint IS the exact quantile --
        ``def:endpoint-rule`` (c) makes it a requirement and
        ``prop:rule-exact`` (v) proves both tails exactly zero -- and at a zero
        budget ``prop:rule-exact`` (ii) proves the same. The diagnostic
        ``endpoint_exact`` says "whether the emitted endpoint is PROVED equal to
        the exact binomial quantile", so on a convention it is ``True``.
        (The degenerate-mass branches must not leave it ``None``: the
        diagnostic would coerce that to ``False``, reporting the opposite of
        what is proved.)
        """
        if honest == _ZERO:
            return RuleEndpoints(
                lower=0,
                upper=0,
                tails_exact=True,
                lower_decided=True,
                upper_decided=True,
            )
        if honest == _ONE:
            return RuleEndpoints(
                lower=rounds,
                upper=rounds,
                tails_exact=True,
                lower_decided=True,
                upper_decided=True,
            )
        raw = self._raw_endpoints(rounds, honest, eps_lower, eps_upper)
        lower = 0 if eps_lower == _ZERO else raw.lower
        upper = rounds if eps_upper == _ZERO else raw.upper
        return RuleEndpoints(
            lower=lower,
            upper=upper,
            tails_exact=raw.tails_exact,
            lower_decided=raw.lower_decided if eps_lower != _ZERO else True,
            upper_decided=raw.upper_decided if eps_upper != _ZERO else True,
        )


class SweepExactRule(EndpointRule):
    """``def:interval`` evaluated by the sweep. THE DEFAULT ROUTE.

    ``prop:rule-exact`` (ii) proves it an admissible endpoint rule, monotone in
    the allocation; its (iii) proves the emitted interval the SMALLEST
    admissible one before the guard wherever every tail is decided exactly, and
    its (vii) admits the comparisons decided against upper bounds on the tails,
    whose interval contains that one and may be wider. The evaluation is
    :func:`~certiqs_key.statistics.intervals.extremal_endpoints`: one pass of
    the running binomial sum decides both quantiles, and the frozen 55 oracle
    cases pin every integer it returns.

    IT TAKES NO PARAMETER OF ITS OWN. The sweep's internal switch to a dyadic
    enclosure above a bit budget is ``tails.EXACT_TAIL_BIT_BUDGET``, which is a
    COST threshold of that module and not an evaluation parameter of a rule:
    neither path may report a tail smaller than the truth, so no claim depends
    on where it is set (``binomial-box/prop:rule-exact`` (vii); design.md,
    "Where the code is").
    """

    name = EndpointRuleName.EXACT
    default_evaluation = TailEvaluation.SWEEP
    monotone_in_the_allocation = True

    def _raw_endpoints(
        self,
        rounds: int,
        honest: Fraction,
        eps_lower: Fraction,
        eps_upper: Fraction,
    ) -> RuleEndpoints:
        lower, upper, exact = extremal_endpoints(rounds, honest, eps_lower, eps_upper)
        return RuleEndpoints(lower=lower, upper=upper, tails_exact=exact)


class EnclosureExactRule(EndpointRule):
    """``def:interval`` evaluated by the local enclosures, ``E1``.

    ``prop:bracketed-endpoints`` (i) proves it an admissible endpoint rule and
    an admissible RELAXATION of the exact rule: the box it emits contains the
    box the sweep emits, and the two coincide wherever the bracket is decided
    (its (ii)). MONOTONICITY IN THE ALLOCATION IS NOT CLAIMED, so
    ``thm:monotonicity-limits`` (i) and (ii) are not available on this route.
    """

    name = EndpointRuleName.EXACT
    default_evaluation = TailEvaluation.ENCLOSURE
    monotone_in_the_allocation = False

    def _raw_endpoints(
        self,
        rounds: int,
        honest: Fraction,
        eps_lower: Fraction,
        eps_upper: Fraction,
    ) -> RuleEndpoints:
        parameters = self.enclosure_parameters
        lower = bracketed_lower_endpoint(rounds, honest, eps_lower, parameters)
        upper = bracketed_upper_endpoint(rounds, honest, eps_upper, parameters)
        return RuleEndpoints(
            lower=lower.index,
            upper=upper.index,
            tails_exact=False,
            lower_decided=lower.decided,
            upper_decided=upper.decided,
        )


class BernsteinRule(EndpointRule):
    """``prop:rule-bernstein``, the closed-form rule. No tail is evaluated.

    Admissible and monotone in the allocation by that proposition's (i) and
    (ii), with an ``n``-monotone ``O(n^-1/2)`` half-width by its (iii), and
    never narrower than the exact rule's raw quantile interval.

    IT IS SELECTED BY EITHER VALUE OF ``tail_evaluation`` because it evaluates
    no tail to find an endpoint; the value it carries still matters, because on
    ``enclosure`` the REPORTED FIGURE is the sum of the two enclosure upper
    bounds at the guarded endpoints and the enclosure parameters are what
    produce it (``completeness_report``, fourth row).
    """

    name = EndpointRuleName.BERNSTEIN
    default_evaluation = TailEvaluation.SWEEP
    monotone_in_the_allocation = True

    def __init__(
        self,
        evaluation: TailEvaluation | None = None,
        enclosure_parameters: EnclosureParameters = DEFAULT_ENCLOSURE_PARAMETERS,
        parameters: BernsteinParameters = DEFAULT_BERNSTEIN_PARAMETERS,
    ) -> None:
        """Fix the route and both parameter sets for the life of the object."""
        super().__init__(evaluation, enclosure_parameters)
        self.parameters = parameters

    def _raw_endpoints(
        self,
        rounds: int,
        honest: Fraction,
        eps_lower: Fraction,
        eps_upper: Fraction,
    ) -> RuleEndpoints:
        lower = (
            0
            if eps_lower == _ZERO
            else bernstein_lower_endpoint(rounds, honest, eps_lower, self.parameters)
        )
        upper = (
            rounds
            if eps_upper == _ZERO
            else bernstein_upper_endpoint(rounds, honest, eps_upper, self.parameters)
        )
        return RuleEndpoints(lower=lower, upper=upper, tails_exact=False)

    def own_parameters(self) -> tuple[tuple[str, int], ...]:
        """Return the two evaluation parameters of the Bernstein rule itself.

        Each name is the path into the submodule interface, as
        :func:`enclosure_rows` explains. ``the_rounding_directions`` is a third
        row of this block and is NOT a parameter: it is a binding rule, and
        there is no value to record. On the ``enclosure`` evaluation
        :meth:`recorded_parameters` adds the enclosure parameters to these,
        because they decide the reported figure.
        """
        block = "the_bernstein_rule"
        return (
            (f"{block}.root_exponent_j", self.parameters.root_exponent),
            (f"{block}.root_precision_bits", self.parameters.root_precision),
        )


#: The ``rule_table`` of ``binomial-box/interface.yaml`` as code: the pair
#: ``(endpoint_rule, tail_evaluation)`` selects the rule instance in force, and
#: a pair this table does not carry is refused with ``endpoint_rule_unknown``
#: and never guessed. THE PAIR IS NEVER PARTIALLY HONOURED and no route is
#: substituted for another.
ENDPOINT_RULES: dict[tuple[EndpointRuleName, TailEvaluation], type[EndpointRule]] = {
    (EndpointRuleName.EXACT, TailEvaluation.SWEEP): SweepExactRule,
    (EndpointRuleName.EXACT, TailEvaluation.ENCLOSURE): EnclosureExactRule,
    (EndpointRuleName.BERNSTEIN, TailEvaluation.SWEEP): BernsteinRule,
    (EndpointRuleName.BERNSTEIN, TailEvaluation.ENCLOSURE): BernsteinRule,
}


def resolve_rule(
    rule: EndpointRuleName,
    evaluation: TailEvaluation,
    enclosure_parameters: EnclosureParameters = DEFAULT_ENCLOSURE_PARAMETERS,
    bernstein_parameters: BernsteinParameters = DEFAULT_BERNSTEIN_PARAMETERS,
) -> EndpointRule:
    """Return the rule instance the request pair selects, WITH ITS PARAMETERS.

    The caller has already decided that both values lie in their enumerations
    -- that is the tenth reason code's job, and it happens before anything is
    constructed (``thm:honest-containment`` (iii)).

    THE PARAMETERS ARE HANDED TO THE INSTANCE HERE AND NOWHERE ELSE, so that
    the numbers that find the endpoints, the numbers that produce the reported
    figure and the numbers the ``honest_model`` records are ONE SET. Resolving
    the rule without them would be a half-connected seam: a caller's parameters
    would move the figure, not move the endpoints they were passed to compute,
    and not be what the record named.
    """
    built = ENDPOINT_RULES[(rule, evaluation)]
    if built is BernsteinRule:
        return BernsteinRule(evaluation, enclosure_parameters, bernstein_parameters)
    return built(evaluation, enclosure_parameters)


def interval_for_rule(
    rounds: int,
    honest: Fraction,
    eps_lower: Fraction,
    eps_upper: Fraction,
    rule: EndpointRule,
) -> OutcomeInterval:
    """Return one outcome's interval record for the route the rule carries.

    The rule returns two integers; everything after that is
    :func:`~certiqs_key.statistics.intervals.interval_record`, which is
    ``lem:guard`` and is rule-independent. ON AN ENCLOSURE EVALUATION the
    record additionally carries an upper bound on each tail AT THE EMITTED
    (guarded) ENDPOINT, which is what the two enclosure rows of
    ``binomial-box/interface.yaml``'s ``completeness_report`` sum -- computed
    at the guarded endpoint and not at the rule's own, because that is where
    ``thm:completeness-bound`` evaluates the tails and the guard can only have moved the
    endpoint outward.

    THE EVALUATION AND ITS PARAMETERS ARE READ OFF THE RULE OBJECT and are not
    passed beside it: one set of numbers, one place they come from.
    """
    endpoints = rule.endpoints(rounds, honest, eps_lower, eps_upper)
    evaluation = rule.evaluation
    route: dict[str, object] = {
        "rule": str(rule.name),
        "evaluation": str(evaluation),
        "lower_decided": endpoints.lower_decided,
        "upper_decided": endpoints.upper_decided,
    }
    if evaluation is TailEvaluation.ENCLOSURE and honest not in (_ZERO, _ONE):
        guarded_low, guarded_high = guarded_endpoints(
            rounds, honest, endpoints.lower, endpoints.upper
        )
        route["tail_upper_below"] = lower_tail_upper_bound(
            rounds, honest, guarded_low, rule.enclosure_parameters
        )
        route["tail_upper_above"] = tail_upper_bound(
            rounds, honest, guarded_high, rule.enclosure_parameters
        )
    elif evaluation is TailEvaluation.ENCLOSURE:
        # A degenerate honest mass spends no budget at all: both tails at the
        # emitted endpoints are exactly zero (prop:rule-exact (v),
        # def:endpoint-rule (c)).
        route["tail_upper_below"] = _ZERO
        route["tail_upper_above"] = _ZERO
    return interval_record(
        rounds,
        honest,
        eps_lower,
        eps_upper,
        endpoints.lower,
        endpoints.upper,
        endpoints.tails_exact,
        **route,
    )
