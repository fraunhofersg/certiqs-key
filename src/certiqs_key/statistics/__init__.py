"""``statistics``: the forward construction of the acceptance set.

Implements ``spec/modules/statistics/``, whose machine-facing half is the two
``interface.yaml`` files beside the claims. Given an honest per-round
distribution ``p^hon`` on the declared acceptance alphabet, a round count ``n``
and a completeness budget ``ecomp``, the module constructs a closed convex
``AcceptSet`` inside the probability simplex together with an exact completeness
statement about the honest run.

THE DIRECTION IS FORWARDS, AND THAT IS THE POINT. The acceptance set is a
protocol parameter fixed BEFORE the run: the consumer's ``h_low`` is an infimum
over it and the key length is conditioned on the accept event. No set is
inferred from observed counts, and observed counts appear nowhere in this
package. A pipeline that fitted the acceptance set to the data it then accepted
would be assuming what it is meant to test.

THIS MODULE MAKES NO SECURITY CLAIM. the claim files say so in as
many words: soundness of any key length rests entirely on ``meat-core``, nothing
established here is used in that argument, and the honest-channel assumptions
A-HON and A-HON-ENV are consumed only by completeness statements. What can fail here is
USABILITY -- an honest run aborting more often than advertised -- and the
package is built so that a failure is legible rather than silent.

Layout, one module per claim group:

    exact          def:conservative-evaluation's input half at the boundary,
                   and the exact-rational verdict
    reasons        thm:honest-containment (iii): the ELEVEN input-domain violation codes
    taxonomy       thm:geometry-validation, thm:box-oracle (i): the two tags and the
                   support
    tails          thm:binomial-tails: the binomial tails and the incomplete-beta form
    dyadic         rem:local-evaluation, "The substrate": directed rounding
    logs           lem:log-enclosure, lem:stirling-enclosure, and their inverse
    enclosure      lem:pmf-enclosure, lem:tail-majorant,
                   prop:bracketed-endpoints: the local evaluation (E1)
    bernstein      lem:bernstein-tail, prop:rule-bernstein: the closed-form rule
    rules          def:endpoint-rule: what a rule is, the guard eq:guard for any
                   rule, and the three instances this repository carries
    intervals      def:interval, prop:rule-exact, lem:guard: one outcome
    construction   def:construction, thm:box-construction, thm:completeness-bound,
                   thm:honest-containment: the map Acc_R
    minimization   thm:box-oracle (ii)-(iii): the closed-form box minimum and witness
    singleton      singleton/thm:singleton-completeness: singleton completeness

THIS PACKAGE IMPORTS ``certiqs_key.domain`` AND NOTHING ELSE OF THIS
REPOSITORY, and at the time of writing it imports nothing from it either: its
own mathematics is a finite alphabet, integer counts, exact rationals and
integer square roots. THE DOCKING ADAPTER IS THE CONSUMER'S: the code that
fills ``meat-core``'s ``PolytopeData`` from this module's geometry is
``certiqs_key.meat_core.docking_statistics`` (``interface.yaml``,
``artifact_bindings.docking``), so that the supplier does not depend on its
consumer. The rounding direction is named where it happens there: ``q^-`` down
and ``q^+`` up.
"""

from __future__ import annotations

from certiqs_key.statistics.bernstein import (
    DEFAULT_BERNSTEIN_PARAMETERS,
    BernsteinParameters,
    bernstein_lower_endpoint,
    bernstein_upper_endpoint,
)
from certiqs_key.statistics.construction import (
    ENVELOPE_MODEL_TAG,
    HONEST_MODEL_TAG,
    AcceptanceConstruction,
    AcceptanceRequest,
    BudgetAllocation,
    ConstructionResult,
    EndpointExact,
    HonestEnvelope,
    HonestModel,
    InfeasibleInput,
    ResolvedRequest,
    construct,
    report_completeness,
    resolve,
    uniform_allocation,
    validate_request,
)
from certiqs_key.statistics.enclosure import (
    DEFAULT_ENCLOSURE_PARAMETERS,
    BracketedEndpoint,
    EnclosureParameters,
    Verdict,
    bracketed_lower_endpoint,
    bracketed_upper_endpoint,
    certify_upper,
)
from certiqs_key.statistics.errors import (
    HypothesisError,
    MalformedInputError,
    StatisticsError,
    UndecidedGeometryError,
)
from certiqs_key.statistics.exact import Rational, as_exact_rational
from certiqs_key.statistics.intervals import (
    EnvelopeInterval,
    OutcomeInterval,
    emitted_tails,
    extremal_endpoints,
    guarded_endpoints,
    outcome_interval,
)
from certiqs_key.statistics.ledger import (
    EMISSION_BY_ROUTE,
    AcceptanceRoute,
    AssumptionLedgerRow,
    assumption_ledger,
    honest_model_tag,
)
from certiqs_key.statistics.minimization import BoxMinimum, box_minimum
from certiqs_key.statistics.reasons import (
    REASON_CODES,
    REASON_CODES_BEFORE_T9,
    InfeasibilityReason,
    InfeasibilityReport,
)
from certiqs_key.statistics.rules import (
    ENDPOINT_RULES,
    BernsteinRule,
    EnclosureExactRule,
    EndpointRule,
    EndpointRuleName,
    RuleEndpoints,
    SweepExactRule,
    TailEvaluation,
    interval_for_rule,
    resolve_rule,
)
from certiqs_key.statistics.singleton import (
    SingletonCompleteness,
    singleton_completeness,
)
from certiqs_key.statistics.tails import (
    TailBound,
    binomial_cdf,
    binomial_pmf,
    lower_tail,
    regularized_incomplete_beta,
    upper_tail,
    within_budget,
)
from certiqs_key.statistics.taxonomy import (
    GeometryDefect,
    GeometryTag,
    GeometryVerdict,
    PolytopeGeometry,
    SingletonGeometry,
    acceptance_support,
    box_witness_point,
    canonical_box,
    validate_geometry,
)

__all__ = [
    "DEFAULT_BERNSTEIN_PARAMETERS",
    "DEFAULT_ENCLOSURE_PARAMETERS",
    "EMISSION_BY_ROUTE",
    "ENDPOINT_RULES",
    "ENVELOPE_MODEL_TAG",
    "HONEST_MODEL_TAG",
    "REASON_CODES",
    "REASON_CODES_BEFORE_T9",
    "AcceptanceConstruction",
    "AcceptanceRequest",
    "AcceptanceRoute",
    "AssumptionLedgerRow",
    "BernsteinParameters",
    "BernsteinRule",
    "BoxMinimum",
    "BracketedEndpoint",
    "BudgetAllocation",
    "ConstructionResult",
    "EnclosureExactRule",
    "EnclosureParameters",
    "EndpointExact",
    "EndpointRule",
    "EndpointRuleName",
    "EnvelopeInterval",
    "GeometryDefect",
    "GeometryTag",
    "GeometryVerdict",
    "HonestEnvelope",
    "HonestModel",
    "HypothesisError",
    "InfeasibilityReason",
    "InfeasibilityReport",
    "InfeasibleInput",
    "MalformedInputError",
    "OutcomeInterval",
    "PolytopeGeometry",
    "Rational",
    "ResolvedRequest",
    "RuleEndpoints",
    "SingletonCompleteness",
    "SingletonGeometry",
    "StatisticsError",
    "SweepExactRule",
    "TailBound",
    "TailEvaluation",
    "UndecidedGeometryError",
    "Verdict",
    "acceptance_support",
    "as_exact_rational",
    "assumption_ledger",
    "bernstein_lower_endpoint",
    "bernstein_upper_endpoint",
    "binomial_cdf",
    "binomial_pmf",
    "box_minimum",
    "box_witness_point",
    "bracketed_lower_endpoint",
    "bracketed_upper_endpoint",
    "canonical_box",
    "certify_upper",
    "construct",
    "emitted_tails",
    "extremal_endpoints",
    "guarded_endpoints",
    "honest_model_tag",
    "interval_for_rule",
    "lower_tail",
    "outcome_interval",
    "regularized_incomplete_beta",
    "report_completeness",
    "resolve",
    "resolve_rule",
    "singleton_completeness",
    "uniform_allocation",
    "upper_tail",
    "validate_geometry",
    "validate_request",
    "within_budget",
]
