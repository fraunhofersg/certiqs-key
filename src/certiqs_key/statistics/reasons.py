"""thm:honest-containment (iii) -- the ELEVEN input-domain violation codes, and nothing else.

Theorem ``thm:honest-containment`` (iii) enumerates the violations of this
module's input domain that are decidable from its own inputs, and the
enumeration IS the vocabulary: the codes below are that theorem's, verbatim and
in its order. They are "the negation, clause by clause, of the domain
constraints tabulated in the inputs table of ``interface.yaml``".

``endpoint_rule_unknown`` IS THE REQUEST'S SELECTOR. It fires on a value of
``endpoint_rule`` or ``tail_evaluation`` outside the enumeration the inputs
table declares, AND THE PAIR IS READ AS ONE SELECTOR: ``prop:bracketed-endpoints``
makes ``(exact, enclosure)`` one endpoint rule, so an unknown value of either
field names a rule the inputs table does not declare. That reading is
``thm:honest-containment`` (iii) violation (11), "the requested endpoint rule, or
the requested evaluation", and ``req:input-refusal``.

EXACTLY ONE CLAUSE OF THE INPUT DOMAIN CARRIES NO CODE, and the codes must not be
read as covering it: that ``Chat``, its enumeration and ``n`` are those of the
SAME declaration the consumer solves, a matched alphabet and round count
(``def:matched-alphabet``). The match "is a relation between artefacts and not
a property of an input", and it is decided at bundle validation as a hard
error (``req:matched-alphabet``; spec/architecture.md 3.6). An implementation
that adds a code for it has invented vocabulary; one that silently
accepts a mismatched alphabet emits a set on the wrong coordinate space.

THIS IS NOT ``AcceptanceDefect``, AND NOT ``GeometryDefect``. The consuming
module's ``certiqs_key.meat_core.acceptance.geometry.AcceptanceDefect`` says what is
wrong with a DECLARED acceptance set at ITS boundary
(``unsupported-geometry`` / ``ill-formed`` / ``empty``), and
:class:`certiqs_key.statistics.taxonomy.GeometryDefect` says the same about a
geometry a profile declares to this module. Neither is a statement about this
module's INPUTS, which is what the codes below are about, and Theorem
``thm:honest-containment`` (iii) is exactly the claim that keeps them apart: the
validation predicate holds UNCONDITIONALLY on the output of the construction map, so
every report this module emits originates in an input-domain violation and NEVER in
the construction. An implementation that can reach one of these codes from a
validated input has a defect, not a geometry problem.
"""  # noqa: E501

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "REASON_CODES",
    "REASON_CODES_BEFORE_T9",
    "InfeasibilityReason",
    "InfeasibilityReport",
]


class InfeasibilityReason(StrEnum):
    """The eleven codes of Theorem ``thm:honest-containment`` (iii), verbatim and in its order."""  # noqa: E501

    #: |Chat| = 0.
    ALPHABET_EMPTY = "alphabet_empty"
    #: |Chat| not finite.
    ALPHABET_NOT_FINITE = "alphabet_not_finite"
    #: n < 1.
    ROUNDS_OUT_OF_RANGE = "rounds_out_of_range"
    #: p^hon not in Delta(Chat), including a coordinate outside Chat.
    HONEST_NOT_A_DISTRIBUTION = "honest_not_a_distribution"
    #: the honest envelope (p^-, p^+) is not admissible: an entry outside
    #: [0, 1], p^- > p^+ at some outcome, sum p^- > 1, sum p^+ < 1, or a
    #: coordinate outside Chat. The point form keeps honest_not_a_distribution.
    HONEST_ENVELOPE_NOT_ADMISSIBLE = "honest_envelope_not_admissible"
    #: ecomp not in [0, 1).
    BUDGET_OUT_OF_RANGE = "budget_out_of_range"
    #: some eps^{+-}(chat) < 0.
    ALLOCATION_NEGATIVE = "allocation_negative"
    #: sum over Chat_con of (eps^-(chat) + eps^+(chat)) > ecomp.
    ALLOCATION_EXCEEDS_BUDGET = "allocation_exceeds_budget"
    #: Chat_con not a subset of Chat.
    SELECTOR_NOT_A_SUBSET = "selector_not_a_subset"
    #: some coordinate of p^hon, or ecomp, or some eps^{+-}(chat) is not an
    #: exact rational, violating Definition def:conservative-evaluation.
    INPUTS_NOT_RATIONAL = "inputs_not_rational"
    #: the value of endpoint_rule, or of tail_evaluation, is none of the rules
    #: the inputs table declares. It goes with the two request
    #: fields; the module docstring says why the pair is one selector.
    ENDPOINT_RULE_UNKNOWN = "endpoint_rule_unknown"


#: The codes in the theorem's own order, as a tuple. The whole vocabulary.
REASON_CODES: tuple[InfeasibilityReason, ...] = tuple(InfeasibilityReason)

#: The first NINE codes, in order, kept as their own name because the
#: frozen oracle registry pins exactly those and the tenth has no frozen case.
#: A reader comparing the two tuples reads the difference off them rather than
#: off a count in prose.
REASON_CODES_BEFORE_T9: tuple[InfeasibilityReason, ...] = tuple(
    code
    for code in InfeasibilityReason
    if code
    not in (
        InfeasibilityReason.ENDPOINT_RULE_UNKNOWN,
        InfeasibilityReason.HONEST_ENVELOPE_NOT_ADMISSIBLE,
    )
)


@dataclass(frozen=True)
class InfeasibilityReport:
    """The record under the machine key ``infeasibility_report``.

    ``reason`` is the machine-readable code and is the load-bearing field;
    ``detail`` names the offending input in prose, for a human reading a
    refusal. The outputs table: a report is emitted INSTEAD OF an acceptance set,
    never beside one.
    """

    reason: InfeasibilityReason
    detail: str

    def as_machine_record(self) -> dict[str, object]:
        """Return the report as a machine record."""
        return {"reason": str(self.reason), "detail": self.detail}
