"""The map ``Acc_R``, and what travels with it.

Theorems ``thm:box-construction``, ``thm:completeness-bound`` and
``thm:honest-containment``. Definition ``def:construction``: from an admissible input
``(Chat, p^hon, n, ecomp, Chat_con, eps^-, eps^+)`` the map emits the
``polytope`` geometry in CANONICAL BOX FORM with

    q^-(chat) = k^-(chat)/n on Chat_con, 0 off it ,
    q^+(chat) = k^+(chat)/n on Chat_con, 1 off it ,          (eq:boxbounds)

and ``AcceptSet = { q in Delta(Chat) : q^- <= q <= q^+ }`` (eq:accset).

Theorem ``thm:box-construction`` proves the map well defined with exact rational data
(i), its bounds a well-formed canonical box (ii), ``p^hon`` inside what it emits and
therefore non-empty (iii), and the emitted set closed, convex and compact in the
simplex, so that the consuming def:admissible-acceptance-set holds by construction for
EVERY admissible input (iv). Theorem ``thm:completeness-bound`` supplies
``epsilon_star``, and Theorem ``thm:honest-containment`` the two things that make a
failure legible: honest containment, and the rule that every ``infeasibility_report``
originates in an input-domain violation and NEVER in the construction.

FAIL-CLOSED, STRUCTURALLY
=========================
The outputs table: on an input-domain violation the module "names one of the
input-domain violations enumerated in Theorem ``thm:honest-containment`` (iii) and NO
``acceptance_set`` is emitted". That is not a flag on one record here: the two
states are two types, :class:`AcceptanceConstruction` and
:class:`InfeasibleInput`, and the second HAS NO ACCEPTANCE SET TO READ. A
caller cannot reach a box past a report by ignoring a boolean, because there is
no attribute holding one, and a "best-effort" box beside a warning is not
expressible.

THE UNCONSTRAINED COORDINATES KEEP THEIR VACUOUS BOUNDS
=======================================================
Remark ``rem:selector``: off ``Chat_con`` the bounds are ``[0, 1]`` and the rows
are emitted anyway, so that ``m_row = 2|Chat|`` does not depend on ``Chat_con``
and a consumer never has to infer a missing row. The emitted pair is also the
RAW one: the denoted set's coordinate ranges can be strictly tighter -- the
simplex binds where the box does not -- and an implementation that emitted the
tight pair would be emitting a different artifact with the same denotation.
Nothing here tightens.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Sized
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.statistics.bernstein import (
    DEFAULT_BERNSTEIN_PARAMETERS,
    BernsteinParameters,
)
from certiqs_key.statistics.enclosure import (
    DEFAULT_ENCLOSURE_PARAMETERS,
    EnclosureParameters,
)
from certiqs_key.statistics.errors import MalformedInputError
from certiqs_key.statistics.exact import Rational, as_exact_rational
from certiqs_key.statistics.intervals import (
    EnvelopeInterval,
    OutcomeInterval,
    emitted_tails,
)
from certiqs_key.statistics.ledger import (
    ENVELOPE_MODEL_TAG,
    HONEST_MODEL_TAG,
    AcceptanceRoute,
    AssumptionLedgerRow,
    assumption_ledger,
    honest_model_tag,
)
from certiqs_key.statistics.reasons import InfeasibilityReason, InfeasibilityReport
from certiqs_key.statistics.rules import (
    EndpointRule,
    EndpointRuleName,
    TailEvaluation,
    interval_for_rule,
    resolve_rule,
)
from certiqs_key.statistics.taxonomy import (
    PolytopeGeometry,
    acceptance_support,
    canonical_box,
)

__all__ = [
    "ENVELOPE_MODEL_TAG",
    "HONEST_MODEL_TAG",
    "AcceptanceConstruction",
    "AcceptanceRequest",
    "BudgetAllocation",
    "ConstructionResult",
    "EndpointExact",
    "HonestEnvelope",
    "HonestModel",
    "InfeasibleInput",
    "ResolvedRequest",
    "construct",
    "report_completeness",
    "resolve",
    "uniform_allocation",
    "validate_request",
]

#: The two values of the ``honest_model`` tag, :data:`HONEST_MODEL_TAG`
#: (A-HON: a law or a degenerate envelope) and :data:`ENVELOPE_MODEL_TAG`
#: (A-HON-ENV: a non-degenerate envelope), are defined in
#: :mod:`certiqs_key.statistics.ledger`, which binds the tag in its rows, and
#: re-exported here, where the record carries them; :func:`honest_model_tag`
#: is the one place the tag is decided.

_ZERO = Fraction(0)
_ONE = Fraction(1)


@dataclass(frozen=True)
class BudgetAllocation:
    """``(eps^-, eps^+)``, the pair of rational vectors on ``Chat_con``.

    Indexed POSITIONALLY by ``Chat_con`` in its declared order, which is the
    order the request carries it in. The pair is a function on ``Chat_con`` and
    on nothing else: an entry for an outcome outside it would have no interval
    to size and no summand in Eq. ``eq:completeness``.
    """

    lower: tuple[Rational, ...]
    upper: tuple[Rational, ...]


def uniform_allocation(
    constrained: Sequence[str], budget: Fraction
) -> BudgetAllocation:
    """Return the DEFAULT uniform rule ``eps^{+-}(chat) = ecomp / (2 |Chat_con|)``.

    Definition ``def:monotone-rule`` records this rule as monotone, which is the
    hypothesis Theorem ``thm:monotonicity-limits`` (i) needs.

    THE EMPTY SELECTOR IS AN IMPLEMENTATION CHOICE THE CONTRACT LEAVES OPEN, AND
    THIS IS WHERE IT IS DECIDED (``interface.yaml``,
    ``inputs.budget_allocation.empty_selector_note``). At ``Chat_con = {}`` the
    rule's denominator ``2 |Chat_con|`` is zero. The contract admits that input
    -- the inputs table types ``Chat_con`` as ANY subset of ``Chat``, and Theorem
    ``thm:monotonicity-limits`` (vi) works the branch explicitly, where ``epsilon_star``
    is an empty sum -- and the resolution taken here is that THE DIVISION IS PERFORMED
    ONCE PER CONSTRAINED OUTCOME, so on an empty selector it is never performed
    at all: the comprehension below has no item to evaluate, the allocation is
    the pair of empty vectors, and the domain constraint of the inputs table reads
    ``0 <= ecomp``, which holds. No special case is written, because writing one
    would mean choosing a value for a rule with no instance.
    """
    share = 2 * len(constrained)
    entries = tuple(budget / share for _ in constrained)
    return BudgetAllocation(lower=entries, upper=entries)


@dataclass(frozen=True)
class HonestEnvelope:
    """The input ``honest_envelope``: a per-outcome range ``[p^-, p^+]``.

    Assumption A-HON-ENV: on an honest run the conditional law of each round
    given the past lies in this range, outcome by outcome -- the honest channel
    may drift within a run, between runs, or with the past. A set of honest
    statistics enters through its entrywise minimum and maximum. Supplied
    INSTEAD OF a distribution in :attr:`AcceptanceRequest.honest`; a
    distribution is the degenerate envelope ``p^- = p^+``, and an envelope that
    is degenerate at every outcome is read as that distribution.

    Checked, not trusted: :func:`validate_request` refuses an envelope with an
    entry outside ``[0, 1]``, ``p^- > p^+`` somewhere, ``sum p^- > 1`` or
    ``sum p^+ < 1`` (no law would lie in it), or a key set other than ``Chat``,
    with ``honest_envelope_not_admissible``.
    """

    lower: Mapping[str, Rational]
    upper: Mapping[str, Rational]


@dataclass(frozen=True)
class AcceptanceRequest:
    """The eight inputs of the inputs table, as given -- validated, not trusted.

    ``constrained`` and ``allocation`` carry ``None`` for "the declared
    default", which is ``Chat`` for the selector and the uniform rule for the
    allocation. ``None`` is distinct from the empty selector ``()``, which is an
    admissible input in its own right (Theorem ``thm:monotonicity-limits`` (vi)) and not
    a default.

    THE NUMERIC FIELDS ARE ANNOTATED AS EXACT RATIONALS AND CHECKED AS
    ANYTHING. The exact-data half of ``def:conservative-evaluation`` is
    decided at :func:`validate_request` (``binomial-box/req:input-refusal``) by
    :func:`~certiqs_key.statistics.exact.as_exact_rational`, which refuses a
    ``float`` -- an annotation cannot, and the ``inputs_not_rational`` code of
    Theorem ``thm:honest-containment`` (iii) exists precisely because the check is a
    runtime one.
    """

    alphabet: Sequence[str]
    #: A distribution on ``Chat`` (the input ``honest_distribution``) or a
    #: :class:`HonestEnvelope` (the input ``honest_envelope``), never both.
    honest: Mapping[str, Rational] | HonestEnvelope
    rounds: int
    budget: Rational
    constrained: Sequence[str] | None = None
    allocation: BudgetAllocation | None = None
    #: THE TWO REQUEST FIELDS THAT SELECT THE RULE. Rows 7 and 8 of the inputs
    #: table; the defaults are ``exact`` and ``sweep``, the route the frozen
    #: oracles pin. TOGETHER THEY SELECT THE RULE INSTANCE IN FORCE, so a value
    #: outside either enumeration fires the reason code
    #: ``endpoint_rule_unknown`` and no acceptance set is emitted
    #: (``thm:honest-containment`` (iii) violation (11); ``req:input-refusal``;
    #: ``req:rule-in-force``). They are typed as ``str`` and checked as
    #: anything, for the same reason the numeric fields are.
    endpoint_rule: str = EndpointRuleName.EXACT
    tail_evaluation: str = TailEvaluation.SWEEP


@dataclass(frozen=True)
class ResolvedRequest:
    """The eight inputs after validation: exact, ordered, defaults materialized."""

    alphabet: tuple[str, ...]
    #: ``p^hon``, or ``p^-`` under a non-degenerate envelope.
    honest: tuple[Fraction, ...]
    rounds: int
    budget: Fraction
    constrained: tuple[str, ...]
    eps_lower: tuple[Fraction, ...]
    eps_upper: tuple[Fraction, ...]
    endpoint_rule: EndpointRuleName = EndpointRuleName.EXACT
    tail_evaluation: TailEvaluation = TailEvaluation.SWEEP
    #: ``p^+`` under a NON-DEGENERATE envelope; ``None`` for a distribution or
    #: a degenerate envelope, which :func:`resolve` reads as one.
    honest_upper: tuple[Fraction, ...] | None = None


@dataclass(frozen=True)
class HonestModel:
    """The record under the machine key ``honest_model``.

    the outputs table fixes the CONTENTS -- the tag ``iid_honest_rounds`` (A-HON), the
    distribution it was computed under, ``n``, ``Chat_con`` and the allocation,
    in that order -- and adds that "completeness is meaningful only relative to
    this record".
    """

    tag: str
    honest_distribution: tuple[Fraction, ...]
    rounds: int
    constrained_outcomes: tuple[str, ...]
    budget_allocation: BudgetAllocation
    #: THE RULE, THE EVALUATION AND THE EVALUATION PARAMETERS, which
    #: ``binomial-box/req:honest-model-record`` requires the record to carry,
    #: and the parameters are here BECAUSE THEY CHANGE THE NUMBER. Two runs with
    #: the same inputs, the same rule and the same evaluation but a different
    #: window, root exponent or precision may emit different endpoints and
    #: therefore different figures -- all of them admissible, none of them the
    #: same -- so a record naming the rule and not the parameters would not
    #: identify what was computed.
    endpoint_rule: str = str(EndpointRuleName.EXACT)
    tail_evaluation: str = str(TailEvaluation.SWEEP)
    evaluation_parameters: tuple[tuple[str, int], ...] = ()
    #: ``p^+`` of a NON-DEGENERATE envelope, ``None`` otherwise; with it
    #: ``honest_distribution`` holds ``p^-`` and the tag is
    #: :data:`ENVELOPE_MODEL_TAG`.
    honest_upper: tuple[Fraction, ...] | None = None

    def as_machine_record(self) -> dict[str, object]:
        """Return the record under machine keys.

        THE SUB-KEYS ARE AN IMPLEMENTATION CHOICE, DECIDED HERE AND RECORDED
        (``interface.yaml``, ``outputs.honest_model.sub_key_note``). the outputs table
        fixes the record's five items and the value of its tag, and fixes no
        machine key for the four items beside the tag. The keys chosen are the
        INPUT-TABLE MACHINE KEYS of the same four objects --
        ``honest_distribution``, ``rounds``, ``constrained_outcomes`` and
        ``budget_allocation`` (the inputs table) -- because those names are the
        contract's own for exactly these objects, and a second name for one
        object is the only way this decision could acquire proof-relevant
        content.
        """
        record: dict[str, object] = {
            "tag": self.tag,
            "honest_distribution": self.honest_distribution,
            "rounds": self.rounds,
            "constrained_outcomes": self.constrained_outcomes,
            "budget_allocation": (
                self.budget_allocation.lower,
                self.budget_allocation.upper,
            ),
            # The last three. The first two are the input-table
            # machine keys of the same objects, for the reason above; the third
            # is this implementation's name for the parameter list, which no
            # claim and no interface row spells.
            "endpoint_rule": self.endpoint_rule,
            "tail_evaluation": self.tail_evaluation,
            "evaluation_parameters": self.evaluation_parameters,
        }
        if self.honest_upper is not None:
            # A NON-DEGENERATE ENVELOPE: the pair goes under the input-table
            # machine key ``honest_envelope``, and ``honest_distribution`` is
            # emptied because no single law was used. A one-law record has
            # no such key and reads exactly as before.
            record["honest_distribution"] = None
            record["honest_envelope"] = {
                "lower": self.honest_distribution,
                "upper": self.honest_upper,
            }
        return record


@dataclass(frozen=True)
class EndpointExact:
    """One row of the ``endpoint_exact`` diagnostic, per outcome.

    ``prop:bracketed-endpoints`` (ii): whether the emitted endpoint is PROVED
    equal to the exact binomial quantile, per side. PRESENT ONLY UNDER
    ``tail_evaluation = enclosure`` -- absent under ``sweep``, where the
    emitted endpoint IS the exact quantile and the question does not arise, and
    absent under ``endpoint_rule = bernstein``, where no bracket is formed
    (``interface.yaml``, the ``endpoint_exact`` row, whose shape and presence
    rule are that file's).

    IT IS A DIAGNOSTIC. No claim of the contract is stated in terms of it, no
    consumer reads it, and the emitted set is unaffected by whether it is
    emitted. It exists because the enclosure route's one cost is a bounded
    conservatism that is INVISIBLE IN THE EMITTED NUMBERS.
    """

    outcome: str
    lower_decided: bool
    upper_decided: bool


@dataclass(frozen=True)
class AcceptanceConstruction:
    """The outputs of the outputs table on the success branch.

    ``infeasibility_report`` is ``None`` here, which is the row's own domain
    ("``null`` on success"), and it is a fixed field rather than a settable one.
    """

    acceptance_set: PolytopeGeometry
    acceptance_support: tuple[str, ...]
    completeness_certified: Fraction
    honest_model: HonestModel
    #: One record per element of ``Chat`` in the declaration's enumeration,
    #: ``None`` off ``Chat_con``. Diagnostics, licensed by Remark ``rem:guard``
    #: -- the four guard conditions "are decidable exactly ... an implementation
    #: may therefore report which of them holds" -- and by Remark
    #: ``rem:epsstar``. They are not outputs of the outputs table and nothing
    #: downstream is entitled to them.
    intervals: tuple[OutcomeInterval | EnvelopeInterval | None, ...]
    #: Whether ``epsilon_star`` was evaluated exactly. ``False`` means it is an
    #: upward-rounded ``tilde-epsilon`` in the sense of Remark ``rem:epsstar``,
    #: which is a valid bound and is what that remark's reporting rule is for.
    completeness_exact: bool
    #: The ``assumption_ledger`` output row: the rows the interface's
    #: ``emission_rule`` gives the canonical box the construction map emits,
    #: each with the declared values it binds
    #: (:mod:`certiqs_key.statistics.ledger`).
    assumption_ledger: tuple[AssumptionLedgerRow, ...]
    #: The ``endpoint_exact`` diagnostic of the outputs table, one row per
    #: CONSTRAINED outcome: present on ``exact`` + ``enclosure``, as
    #: ``binomial-box/req:endpoint-exact-record`` requires, and ``None`` on
    #: every route that forms no bracket.
    endpoint_exact: tuple[EndpointExact, ...] | None = None
    infeasibility_report: None = None


@dataclass(frozen=True)
class InfeasibleInput:
    """The other branch of the outputs table: a report, and NO acceptance set.

    The four output slots are fixed at ``None`` and cannot be set. Theorem
    ``thm:honest-containment`` (iii): "on any of these the module emits NO
    acceptance_set".
    """

    infeasibility_report: InfeasibilityReport
    acceptance_set: None = None
    acceptance_support: None = None
    completeness_certified: None = None
    honest_model: None = None


#: What :func:`construct` returns. A union rather than one record with optional
#: fields, so that the fail-closed branch has nothing to read.
ConstructionResult = AcceptanceConstruction | InfeasibleInput


def construct(
    request: AcceptanceRequest,
    enclosure_parameters: EnclosureParameters = DEFAULT_ENCLOSURE_PARAMETERS,
    bernstein_parameters: BernsteinParameters = DEFAULT_BERNSTEIN_PARAMETERS,
) -> ConstructionResult:
    """Run the construction map ``Acc_R`` of Definition ``def:construction``.

    Validation first, and on a violation the map is not run at all: Theorem
    ``thm:honest-containment`` (iii) proves the validation predicate of Theorem
    ``thm:geometry-validation`` (iii) holds UNCONDITIONALLY on the output of ``Acc_R``
    over the input domain, FOR EVERY ADMISSIBLE ENDPOINT RULE, so a report that
    originated in the construction would be a defect and not a geometry problem. There
    is therefore no emptiness check on the way out and no branch that could
    produce one.

    NEITHER PARAMETER SET IS A REQUEST INPUT -- the inputs table has eight rows
    and none of them is a parameter -- but the values in force are recorded in
    the emitted ``honest_model``, because they change the number
    (``interface.yaml``, ``outputs.honest_model.why_the_parameters_belong_here``).
    THE RULE IS RESOLVED ONCE, HERE, WITH BOTH SETS, and the object is what
    everything below reads: resolving it twice -- once for the record and once
    for the endpoints -- would be a seam.
    """
    report = validate_request(request)
    if report is not None:
        return InfeasibleInput(report)
    resolved = resolve(request)
    rule = resolve_rule(
        resolved.endpoint_rule,
        resolved.tail_evaluation,
        enclosure_parameters,
        bernstein_parameters,
    )
    intervals = _intervals(resolved, rule)
    lower, upper = _box_bounds(intervals)
    geometry = canonical_box(resolved.alphabet, lower, upper)
    certified, exact = _completeness(resolved, intervals)
    tag = honest_model_tag(resolved.honest_upper)
    return AcceptanceConstruction(
        acceptance_set=geometry,
        acceptance_support=acceptance_support(geometry),
        completeness_certified=report_completeness(certified, resolved.budget),
        honest_model=HonestModel(
            tag=tag,
            honest_distribution=resolved.honest,
            honest_upper=resolved.honest_upper,
            rounds=resolved.rounds,
            constrained_outcomes=resolved.constrained,
            budget_allocation=BudgetAllocation(resolved.eps_lower, resolved.eps_upper),
            endpoint_rule=str(resolved.endpoint_rule),
            tail_evaluation=str(resolved.tail_evaluation),
            evaluation_parameters=rule.recorded_parameters(),
        ),
        intervals=intervals,
        completeness_exact=exact,
        assumption_ledger=assumption_ledger(
            AcceptanceRoute.CONSTRUCTED_BOX,
            alphabet=resolved.alphabet,
            rounds=resolved.rounds,
            honest=resolved.honest,
            honest_upper=resolved.honest_upper,
        ),
        endpoint_exact=_endpoint_exact(resolved, intervals),
    )


def _completeness(
    resolved: ResolvedRequest,
    intervals: tuple[OutcomeInterval | EnvelopeInterval | None, ...],
) -> tuple[Fraction, bool]:
    """Return the completeness figure for the route, and whether it is exact.

    The four rows of ``binomial-box/interface.yaml``'s ``completeness_report``,
    which ``rem:completeness-on-rules`` delegates to that file by name. The
    principle the four rows follow is REPORT THE TIGHTEST FIGURE THE ROUTE CAN
    AFFORD, and every one of them is an upward-rounded bound on the honest
    failure probability:

    * ``exact`` + ``sweep`` -- THE EXACT ``epsilon_star`` of ``rem:epsstar``:
      the two tails at the GUARDED endpoints, already decided in the course of
      finding the quantiles, so the tightest figure is free. This is the
      default report and the one the frozen oracles pin.
    * ``exact`` + ``enclosure`` and ``bernstein`` + ``enclosure`` --
      ``rem:completeness-on-rules`` (b): the UPPER ENCLOSURES at the emitted
      endpoints, each at least the true tail, so the sum is at least
      ``epsilon_star``. The clamp of :func:`report_completeness` is what keeps
      the figure inside the declared output domain.
    * ``bernstein`` + ``sweep`` -- ``rem:completeness-on-rules`` (a): THE
      ALLOCATION SUM. By ``lem:guard`` (ii) each tail at a guarded endpoint is
      at most its allocation, so the sum is at least ``epsilon_star``; it lies
      in ``[0, ecomp]`` by the input domain, so no clamp is needed. The rule
      evaluates no tail to find an endpoint and a sweep afterwards would cost
      the very sweep this rule was chosen to avoid.
    """
    if (
        resolved.endpoint_rule is EndpointRuleName.BERNSTEIN
        and resolved.tail_evaluation is TailEvaluation.SWEEP
    ):
        total = sum(resolved.eps_lower, _ZERO) + sum(resolved.eps_upper, _ZERO)
        return total, False
    if resolved.tail_evaluation is TailEvaluation.ENCLOSURE:
        total = _ZERO
        for interval in intervals:
            if interval is None:
                continue
            below = interval.tail_upper_below
            above = interval.tail_upper_above
            if below is None or above is None:  # pragma: no cover - set together
                raise MalformedInputError(
                    "an enclosure route emitted an interval without its tail "
                    "bounds; the completeness report of interface.yaml needs "
                    "both"
                )
            total = total + below + above
        return total, False
    total = _ZERO
    exact = True
    for interval in intervals:
        if interval is None:
            continue
        below_bound, above_bound = emitted_tails(interval)
        total = total + below_bound.upper + above_bound.upper
        exact = exact and below_bound.exact and above_bound.exact
    return total, exact


def _endpoint_exact(
    resolved: ResolvedRequest,
    intervals: tuple[OutcomeInterval | EnvelopeInterval | None, ...],
) -> tuple[EndpointExact, ...] | None:
    """Return the ``endpoint_exact`` table, or ``None`` where no bracket forms.

    Present only under ``tail_evaluation = enclosure`` AND a rule that forms a
    bracket, which is the exact rule; the Bernstein rule evaluates no tail to
    find an endpoint and there is nothing to report
    (``interface.yaml``, the ``endpoint_exact`` row, ``presence``).

    A ``None`` VERDICT IS REFUSED RATHER THAN COERCED. The row's domain is
    "whether the emitted endpoint is PROVED equal to the exact binomial
    quantile", which is a two-valued question wherever this table is emitted:
    the search decides it, or a convention of ``def:endpoint-rule`` (b) or (c)
    decides it, and both write a boolean. Coercing an absent verdict with
    ``bool`` reported ``False`` at a degenerate honest coordinate, where the
    endpoint is provably the exact quantile; a verdict that is still absent here is a
    defect of this module and is refused as one, not published as a diagnostic.
    """
    if (
        resolved.tail_evaluation is not TailEvaluation.ENCLOSURE
        or resolved.endpoint_rule is not EndpointRuleName.EXACT
    ):
        return None
    rows: list[EndpointExact] = []
    for chat, interval in zip(resolved.alphabet, intervals, strict=True):
        if interval is None:
            continue
        if interval.lower_decided is None or interval.upper_decided is None:
            raise MalformedInputError(  # pragma: no cover - a defect, not an input
                f"the enclosure route emitted no bracket verdict at {chat!r}; "
                "every route that emits endpoint_exact decides it, by the "
                "search or by a convention of def:endpoint-rule"
            )
        rows.append(
            EndpointExact(
                outcome=chat,
                lower_decided=interval.lower_decided,
                upper_decided=interval.upper_decided,
            )
        )
    return tuple(rows)


def report_completeness(certified: Fraction, budget: Fraction) -> Fraction:
    """Return what goes under ``completeness_certified``: ``min{ecomp, tilde}``.

    Remark ``rem:epsstar``, transcribed because it is a REQUIREMENT and not
    advice. ``epsilon_star`` is exactly computable at rational ``p^hon``; an
    implementation that cannot evaluate the tails exactly must round them
    UPWARD (a conservative evaluation, ``def:conservative-evaluation``),
    because "reporting a downward-rounded
    ``epsilon_star`` would claim a completeness the set does not have". Upward
    rounding can carry the figure ABOVE ``ecomp`` -- in the degenerate case
    where every tail meets its allocation exactly and the allocation sums to
    exactly ``ecomp``, any strict over-estimate leaves the declared output
    domain ``[0, ecomp]`` -- and the rule that closes this without weakening
    anything is to report ``min{ecomp, tilde-epsilon}`` for whatever
    upward-rounded ``tilde-epsilon >= epsilon_star`` is available. That is again
    a valid bound, both numbers being at least ``epsilon_star``, which by
    Eq. ``eq:completeness`` is at least the honest failure probability.

    ON THE EXACT ROUTE THE CLAMP NEVER BINDS, and that is a theorem rather than
    an observation: ``epsilon_star <= ecomp`` is part of Eq. ``eq:completeness``.
    It is applied unconditionally anyway, because a rule with two spellings --
    one for each evaluation route -- is a rule with two chances to be wrong.
    """
    return min(budget, certified)


def resolve(request: AcceptanceRequest) -> ResolvedRequest:
    """Return the request with defaults materialized and every number exact.

    Call only on a request :func:`validate_request` has cleared; the conversions
    below assume what that function decides.
    """
    alphabet = tuple(request.alphabet)
    honest_upper: tuple[Fraction, ...] | None = None
    if isinstance(request.honest, HonestEnvelope):
        honest = tuple(_exact(request.honest.lower[chat]) for chat in alphabet)
        upper = tuple(_exact(request.honest.upper[chat]) for chat in alphabet)
        # An envelope degenerate at every outcome IS a distribution (the
        # validation's two sum conditions force it into the simplex) and is
        # recorded as one: A-HON-ENV with p^- = p^+ is A-HON.
        honest_upper = None if upper == honest else upper
    else:
        honest = tuple(_exact(request.honest[chat]) for chat in alphabet)
    budget = _exact(request.budget)
    constrained = (
        alphabet if request.constrained is None else tuple(request.constrained)
    )
    allocation = request.allocation
    if allocation is None:
        allocation = uniform_allocation(constrained, budget)
    return ResolvedRequest(
        alphabet=alphabet,
        honest=honest,
        rounds=request.rounds,
        budget=budget,
        constrained=constrained,
        eps_lower=tuple(_exact(value) for value in allocation.lower),
        eps_upper=tuple(_exact(value) for value in allocation.upper),
        endpoint_rule=EndpointRuleName(request.endpoint_rule),
        tail_evaluation=TailEvaluation(request.tail_evaluation),
        honest_upper=honest_upper,
    )


def _intervals(
    resolved: ResolvedRequest, rule: EndpointRule
) -> tuple[OutcomeInterval | EnvelopeInterval | None, ...]:
    """Return one interval record per element of ``Chat``, ``None`` off ``Chat_con``.

    THE RULE OBJECT IS THE CALLER'S, resolved once in :func:`construct`, so
    that every outcome is evaluated by the same rule with the same parameters:
    an evaluation whose parameters varied between outcomes would lose the
    monotonicity ``prop:rule-bernstein`` (ii) asserts and ``thm:monotonicity-limits``
    (i) and (ii) read.

    UNDER AN ENVELOPE (``def:endpoint-rule``) an
    outcome with ``p^- < p^+`` gets TWO one-sided evaluations: the rule at
    ``p^-`` with the upper allocation zeroed, for ``k^-``, and the rule at
    ``p^+`` with the lower allocation zeroed, for ``k^+``. Zeroing the unused
    side is ``def:endpoint-rule`` (b): that side is answered without a search
    and is never read. An outcome with ``p^- = p^+`` takes the one-law route
    unchanged, which is what keeps every one-law golden bit for bit.
    """
    position = {chat: index for index, chat in enumerate(resolved.constrained)}
    records: list[OutcomeInterval | EnvelopeInterval | None] = []
    for index, chat in enumerate(resolved.alphabet):
        if chat not in position:
            records.append(None)
            continue
        share = position[chat]
        upper = resolved.honest_upper
        if upper is not None and upper[index] != resolved.honest[index]:
            records.append(
                EnvelopeInterval(
                    lower_side=interval_for_rule(
                        resolved.rounds,
                        resolved.honest[index],
                        resolved.eps_lower[share],
                        _ZERO,
                        rule,
                    ),
                    upper_side=interval_for_rule(
                        resolved.rounds,
                        upper[index],
                        _ZERO,
                        resolved.eps_upper[share],
                        rule,
                    ),
                )
            )
            continue
        records.append(
            interval_for_rule(
                resolved.rounds,
                resolved.honest[index],
                resolved.eps_lower[share],
                resolved.eps_upper[share],
                rule,
            )
        )
    return tuple(records)


def _box_bounds(
    intervals: tuple[OutcomeInterval | EnvelopeInterval | None, ...],
) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...]]:
    """Return ``(q^-, q^+)`` of Eq. ``eq:boxbounds``, vacuous bounds included."""
    lower: list[Fraction] = []
    upper: list[Fraction] = []
    for interval in intervals:
        if interval is None:
            # Off Chat_con: the VACUOUS pair, kept rather than omitted so that
            # m_row = 2|Chat| does not depend on Chat_con (Remark rem:selector).
            lower.append(_ZERO)
            upper.append(_ONE)
            continue
        lower.append(interval.box_lower)
        upper.append(interval.box_upper)
    return tuple(lower), tuple(upper)


# ---------------------------------------------------------------------------
#  thm:honest-containment (iii) -- the input-domain check, and the ten codes it
#  may emit.
# ---------------------------------------------------------------------------


def validate_request(request: AcceptanceRequest) -> InfeasibilityReport | None:
    """Return the input-domain violation this request carries, or ``None``.

    THE ORDER OF THE CHECKS IS THE INTERFACE'S, and it is
    ``interface.yaml``'s ``outputs.infeasibility_report.validation_order``
    followed step by step. No claim fixes an order: the outputs table says a
    report "names ONE OF the input-domain violations enumerated in Theorem
    ``thm:honest-containment`` (iii)", so any violated clause is a conforming answer and
    no frozen case violates two. WHAT THE CLAIMS DO FIX, and what the order
    respects, is that every one of them is decided BEFORE anything is
    constructed and that rationality is decided before a comparison of values,
    an inexact datum making every later comparison undecidable in the sense
    ``def:conservative-evaluation`` requires. The nine steps:

    1. ``alphabet_empty``, ``alphabet_not_finite`` -- everything else is
       indexed by ``Chat``. ``alphabet_not_finite`` is decided before
       ``alphabet_empty`` here although the theorem lists them the other way
       round, because ``|Chat| = 0`` cannot be asked of an argument that is not
       a finite enumeration at all;
    2. ``rounds_out_of_range``;
    3. ``selector_not_a_subset``;
    4. ``inputs_not_rational`` -- the type decision, before any comparison;
    5. ``honest_not_a_distribution``, or ``honest_envelope_not_admissible``
       when the honest input is an envelope;
    6. ``budget_out_of_range``;
    7. ``allocation_negative``;
    8. ``allocation_exceeds_budget``;
    9. ``endpoint_rule_unknown`` -- the rule selector, decided last because it
       is the only clause that constrains nothing the other eight read.

    THE SELECTOR IS THIRD. Nothing it can report depends on its position: the two
    halves are independent clauses, and the interface's order is the one a
    conforming implementation follows.

    Two things this deliberately does NOT do. It adds no ELEVENTH code for a
    matched alphabet and round count (``def:matched-alphabet``) -- that
    ``Chat``, its enumeration and ``n`` are the consuming declaration's --
    which "is a relation between artefacts and not a property of an input" and
    is decided at bundle validation as a hard error (``req:matched-alphabet``;
    :mod:`certiqs_key.runs.pipeline`). And it does not turn a malformed
    PRESENTATION of an input into a code: an alphabet with a repeated label
    enumerates no set, so no domain clause can be read against it, and that
    raises
    :class:`~certiqs_key.statistics.errors.MalformedInputError` instead.
    """
    alphabet_report = _alphabet_report(request.alphabet)
    if alphabet_report is not None:
        return alphabet_report
    alphabet = tuple(request.alphabet)
    if not _is_round_count(request.rounds):
        return InfeasibilityReport(
            InfeasibilityReason.ROUNDS_OUT_OF_RANGE,
            f"the inputs table types `rounds` as an int with n >= 1; "
            f"got {request.rounds!r}",
        )
    constrained = (
        alphabet if request.constrained is None else tuple(request.constrained)
    )
    if len(set(constrained)) != len(constrained):
        raise MalformedInputError(
            f"the selector repeats a label: {constrained!r}. Chat_con is a "
            "SUBSET of Chat, and a repeated label enumerates none"
        )
    outside = [chat for chat in constrained if chat not in set(alphabet)]
    if outside:
        return InfeasibilityReport(
            InfeasibilityReason.SELECTOR_NOT_A_SUBSET,
            f"Chat_con carries {outside!r}, which Chat does not: Eq. "
            "eq:boxbounds is a case split over chat IN Chat, and an element "
            "outside it has no box row to occupy and no coordinate to bound",
        )
    rational_report = _rational_report(request)
    if rational_report is not None:
        return rational_report
    honest_report = _honest_report(request, alphabet)
    if honest_report is not None:
        return honest_report
    budget = _exact(request.budget)
    if not _ZERO <= budget < _ONE:
        return InfeasibilityReport(
            InfeasibilityReason.BUDGET_OUT_OF_RANGE,
            f"the inputs table gives ecomp the HALF-OPEN domain [0, 1); got {budget}. "
            "The right end is excluded twice over: the proof of Proposition "
            "prop:rule-exact (vi) uses eps^{+-} < 1 at both end-of-range cases, and "
            "Theorem thm:singleton-completeness (ii) turns on the same half-openness",
        )
    allocation_report = _allocation_report(request, constrained, budget)
    if allocation_report is not None:
        return allocation_report
    return _rule_report(request)


def _rule_report(request: AcceptanceRequest) -> InfeasibilityReport | None:
    """Return the tenth code's violation, or ``None``: step 9 of the order.

    THE PAIR IS NEVER PARTIALLY HONOURED and no route is substituted for
    another: an unknown value of EITHER field names a rule the inputs table
    does not declare, and the request is refused with no acceptance set.
    """
    for field, value, admissible in (
        ("endpoint_rule", request.endpoint_rule, tuple(EndpointRuleName)),
        ("tail_evaluation", request.tail_evaluation, tuple(TailEvaluation)),
    ):
        if value not in {str(item) for item in admissible}:
            return InfeasibilityReport(
                InfeasibilityReason.ENDPOINT_RULE_UNKNOWN,
                f"{field} is {value!r}; the inputs table declares exactly "
                f"{[str(item) for item in admissible]}. The pair "
                "(endpoint_rule, tail_evaluation) selects the endpoint rule in "
                "force, so a value outside either enumeration names a rule "
                "this module does not carry, and thm:honest-containment (iii) "
                "refuses it rather than guessing one",
            )
    return None


def _alphabet_report(alphabet: object) -> InfeasibilityReport | None:
    """Return the alphabet clause's violation, or ``None``."""
    if isinstance(alphabet, str):
        raise MalformedInputError(
            "the acceptance alphabet is a str, which Python presents as a "
            "sequence of its characters; Chat is a set of outcome LABELS and a "
            "str is one label, so no reading of this argument is the intended "
            "one"
        )
    if not isinstance(alphabet, Sequence):
        if isinstance(alphabet, Sized):
            raise MalformedInputError(
                "the acceptance alphabet is finite but carries no fixed "
                "enumeration (the inputs table asks for one, and the conventions "
                "make it the index of every row of B). A set or a mapping is "
                "refused rather than ordered here, because choosing an order "
                "would fix the coordinate order of the emitted artifact"
            )
        return InfeasibilityReport(
            InfeasibilityReason.ALPHABET_NOT_FINITE,
            "Chat was not presented as a finite enumeration. Finiteness is the "
            "one cardinality hypothesis the contract uses: Theorem "
            "thm:geometry-validation (i) applies Heine-Borel on R^Chat, Theorem "
            "thm:completeness-bound aggregates over 2|Chat_con| events by FINITE "
            "subadditivity, and Eq. eq:boxrows sets m_row = 2|Chat|",
        )
    labels = tuple(alphabet)
    if len(set(labels)) != len(labels):
        raise MalformedInputError(
            f"the acceptance alphabet repeats a label: {labels!r}. The inputs "
            "table types Chat as a finite SET with a fixed enumeration, and a "
            "repeated label enumerates no set -- so |Chat|, p^hon in "
            "Delta(Chat) and Chat_con subset Chat are untestable rather than "
            "false, and none of the ten codes applies"
        )
    if not labels:
        return InfeasibilityReport(
            InfeasibilityReason.ALPHABET_EMPTY,
            "|Chat| = 0. Delta(Chat) is then the set of vectors with no "
            "coordinates summing to 1, which is EMPTY, so Eq. eq:accset would "
            "denote the empty set -- closed and convex, hence passing the "
            "consuming def:admissible-acceptance-set while carrying no information at "
            "all",
        )
    return None


def _rational_report(request: AcceptanceRequest) -> InfeasibilityReport | None:
    """Return the inexact datum this request carries, or ``None``.

    The exact-data half of ``def:conservative-evaluation``, refused with
    ``inputs_not_rational`` (``binomial-box/req:input-refusal``).
    """
    values: list[tuple[str, object]] = [("ecomp", request.budget)]
    if isinstance(request.honest, HonestEnvelope):
        for side, entries in (
            ("p^-", request.honest.lower),
            ("p^+", request.honest.upper),
        ):
            if isinstance(entries, Mapping):
                values.extend(
                    (f"{side}({chat!r})", value) for chat, value in entries.items()
                )
    elif isinstance(request.honest, Mapping):
        values.extend(
            (f"p^hon({chat!r})", value) for chat, value in request.honest.items()
        )
    if request.allocation is not None:
        values.extend(
            (f"eps^-[{index}]", value)
            for index, value in enumerate(request.allocation.lower)
        )
        values.extend(
            (f"eps^+[{index}]", value)
            for index, value in enumerate(request.allocation.upper)
        )
    for name, value in values:
        if as_exact_rational(value) is None:
            return InfeasibilityReport(
                InfeasibilityReason.INPUTS_NOT_RATIONAL,
                f"{name} is {value!r}, which is not an exact rational. "
                "A conservative evaluation (statistics/def:conservative-"
                "evaluation) asks for exact rationals, and at "
                "irrational p the tail is irrational, so the comparison of "
                "Definition def:interval against a rational budget is not "
                "decidable by exact arithmetic. A float is refused rather than "
                "converted: 0.1 read as 1/10 is the substitution that "
                "definition rules out, and only the caller knows which "
                "rational was meant",
            )
    return None


def _honest_report(
    request: AcceptanceRequest, alphabet: tuple[str, ...]
) -> InfeasibilityReport | None:
    """Return the ``p^hon`` clause's violation, or ``None``."""
    honest = request.honest
    if isinstance(honest, HonestEnvelope):
        return _envelope_report(honest, alphabet)
    if not isinstance(honest, Mapping):
        raise MalformedInputError(
            "p^hon must be presented as a mapping from outcome label to exact "
            f"rational; got {type(honest).__name__}"
        )
    if set(honest) != set(alphabet):
        return InfeasibilityReport(
            InfeasibilityReason.HONEST_NOT_A_DISTRIBUTION,
            f"p^hon is indexed by {sorted(honest)!r} against Chat = "
            f"{list(alphabet)!r}. the inputs table asks for a vector on Chat, and "
            "the code covers a coordinate outside Chat in as many words",
        )
    values = [_exact(honest[chat]) for chat in alphabet]
    total = sum(values, _ZERO)
    if any(value < _ZERO for value in values) or total != _ONE:
        return InfeasibilityReport(
            InfeasibilityReason.HONEST_NOT_A_DISTRIBUTION,
            f"p^hon is not in Delta(Chat): it sums to {total} and its least "
            f"coordinate is {min(values)}. Theorem thm:completeness-bound's "
            "marginal-law step needs p^hon(chat) to be the success probability "
            "of a Bernoulli indicator, and its event-inclusion step needs "
            "sum_chat N_chat = n",
        )
    return None


def _envelope_report(
    envelope: HonestEnvelope, alphabet: tuple[str, ...]
) -> InfeasibilityReport | None:
    """Return the envelope clause's violation, or ``None``.

    The input domain of ``honest_envelope``: both sides indexed by exactly
    ``Chat``, ``0 <= p^- <= p^+ <= 1`` at every outcome, and
    ``sum p^- <= 1 <= sum p^+`` -- the last pair being exactly the condition for
    SOME law to lie in the envelope (the box-feasibility fact of
    ``thm:geometry-validation`` (iii)), without which A-HON-ENV would describe no honest
    run at all.
    """
    sides: tuple[object, object] = (envelope.lower, envelope.upper)
    if not all(isinstance(side, Mapping) for side in sides):
        raise MalformedInputError(
            "both sides of the honest envelope must be mappings from outcome "
            "label to exact rational"
        )
    for side, entries in (("p^-", envelope.lower), ("p^+", envelope.upper)):
        if set(entries) != set(alphabet):
            return InfeasibilityReport(
                InfeasibilityReason.HONEST_ENVELOPE_NOT_ADMISSIBLE,
                f"{side} is indexed by {sorted(entries)!r} against Chat = "
                f"{list(alphabet)!r}; both sides of the envelope are vectors on "
                "Chat",
            )
    lower = [_exact(envelope.lower[chat]) for chat in alphabet]
    upper = [_exact(envelope.upper[chat]) for chat in alphabet]
    for chat, low, high in zip(alphabet, lower, upper, strict=True):
        if not _ZERO <= low <= high <= _ONE:
            return InfeasibilityReport(
                InfeasibilityReason.HONEST_ENVELOPE_NOT_ADMISSIBLE,
                f"at {chat!r} the envelope is [{low}, {high}], which is not a "
                "sub-interval of [0, 1]: A-HON-ENV bounds a conditional "
                "probability from below by p^- and from above by p^+",
            )
    total_lower = sum(lower, _ZERO)
    total_upper = sum(upper, _ZERO)
    if total_lower > _ONE or total_upper < _ONE:
        return InfeasibilityReport(
            InfeasibilityReason.HONEST_ENVELOPE_NOT_ADMISSIBLE,
            f"sum p^- = {total_lower} and sum p^+ = {total_upper}; no law on Chat "
            "lies in the envelope unless sum p^- <= 1 <= sum p^+, so A-HON-ENV "
            "would describe no honest run",
        )
    return None


def _allocation_report(
    request: AcceptanceRequest, constrained: tuple[str, ...], budget: Fraction
) -> InfeasibilityReport | None:
    """Return the allocation clause's violation, or ``None``.

    The clause has TWO INDEPENDENT HALVES -- componentwise non-negativity and
    the sum bound -- and each is checked on its own. A check of one alone
    accepts a violation of the other: the frozen ``VIOL-allocation-negative``
    case has a negative entry whose SUM is inside the budget, and
    ``VIOL-allocation-exceeds-budget`` has every entry non-negative with a sum
    outside it.
    """
    if request.allocation is None:
        # The default uniform rule is non-negative and sums to at most ecomp by
        # construction: 2 |Chat_con| shares of ecomp / (2 |Chat_con|), and none
        # at all on an empty selector.
        return None
    allocation = request.allocation
    if len(allocation.lower) != len(constrained) or len(allocation.upper) != len(
        constrained
    ):
        raise MalformedInputError(
            f"the allocation carries {len(allocation.lower)} lower and "
            f"{len(allocation.upper)} upper entries against |Chat_con| = "
            f"{len(constrained)}; it is a pair of vectors ON Chat_con, read "
            "positionally against its declared order"
        )
    entries = [_exact(value) for value in (*allocation.lower, *allocation.upper)]
    if any(value < _ZERO for value in entries):
        return InfeasibilityReport(
            InfeasibilityReason.ALLOCATION_NEGATIVE,
            f"the allocation has a negative entry ({min(entries)}). At a "
            "negative budget no k qualifies in Eq. eq:kappaminus at all -- "
            "Pr[N < 0] = 0 is already above it -- so the set whose maximum "
            "kappa^- is defined to be is EMPTY, and Proposition "
            "prop:rule-exact (i), whose "
            "entire content is that k = 0 always belongs, fails",
        )
    total = sum(entries, _ZERO)
    if total > budget:
        return InfeasibilityReport(
            InfeasibilityReason.ALLOCATION_EXCEEDS_BUDGET,
            f"the allocation sums to {total} against ecomp = {budget}. The "
            "chain Pr[freq not in AcceptSet] <= epsilon_star <= ecomp loses "
            "its SECOND inequality, and the failure is silent without this "
            "check: the construction still runs, the box still contains "
            "p^hon, and epsilon_star is still correctly computed -- it is only "
            "the claim epsilon_star <= ecomp that is false, and the consumer "
            "never sees the allocation",
        )
    return None


def _exact(value: object) -> Fraction:
    """Return a validated input as a Fraction; the check has already passed."""
    exact = as_exact_rational(value)
    if exact is None:  # pragma: no cover - validate_request decides this first
        raise MalformedInputError(
            f"{value!r} is not an exact rational; this value should have been "
            "refused by validate_request with the inputs_not_rational code"
        )
    return exact


def _is_round_count(value: object) -> bool:
    """Return whether ``value`` is an ``int`` with ``n >= 1`` (the inputs table).

    ``bool`` is excluded although Python makes it an ``int``: a round count that
    is ``True`` is a type confusion rather than the number one, and a module
    whose entire purpose is to normalize counts by ``n`` should not silently
    read a flag as a round count. A non-integer ``n`` fails the same test, the
    Inputs table typing ``rounds`` as an ``int``.
    """
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1
