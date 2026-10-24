"""Hard errors of the ``statistics`` module.

MOST FAILURES HERE ARE NOT ERRORS. The outputs table of ``interface.yaml`` types
``infeasibility_report`` as "a record or ``null``" and Theorem
``thm:honest-containment`` (iii) enumerates the eleven machine-readable codes it may
carry, so an inadmissible INPUT is reported as data --
:class:`certiqs_key.statistics.reasons.InfeasibilityReport` beside a construction that
emitted no acceptance set -- and not raised. The exceptions below are for the two things
that are not input-domain violations:

* an argument that is not a well-formed presentation of an input at all, so
  that no domain clause can be tested against it (:class:`MalformedInputError`);
* a question this module declines to answer rather than deciding something the
  accepted contract states no closed form for (:class:`UndecidedGeometryError`).

Refusing is the fail-closed alternative to improvising, and it is deliberately
distinguishable from the eleven codes: a caller must not be able to turn a
refusal into a report code, or a report code into a TWELFTH one.
"""

from __future__ import annotations

__all__ = [
    "HypothesisError",
    "MalformedInputError",
    "StatisticsError",
    "UndecidedGeometryError",
]


class StatisticsError(Exception):
    """Base class for every ``statistics`` failure."""


class MalformedInputError(StatisticsError):
    """An argument is not a presentation of an input the inputs table types.

    NOT an input-domain violation, and deliberately not one of the eleven codes
    of Theorem ``thm:honest-containment`` (iii). Those eleven are "the negation,
    clause by clause, of the domain constraints tabulated in the inputs table",
    and a clause can only be negated by data the clause can be read against. An
    acceptance alphabet presented with a repeated label is the case this exists
    for: the inputs table types ``Chat`` as a finite SET with a fixed
    enumeration, and a repeated label means the argument enumerates no set, so
    ``|Chat|``, ``p^hon in Delta(Chat)`` and ``Chat_con subset Chat`` are all
    untestable rather than false. Adding a TWELFTH code for it would invent
    vocabulary the contract does not carry.
    """


class HypothesisError(StatisticsError):
    """A stated hypothesis of the theorem being evaluated does not hold.

    Theorem ``thm:singleton-completeness`` is stated for a ``singleton`` geometry with
    ``q^*`` in the simplex and for an honest law on the same alphabet; outside those
    hypotheses its formulas still evaluate and prove nothing. Distinct from an
    ``infeasibility_report``: the eleven codes of Theorem
    ``thm:honest-containment`` (iii) are violations of the CONSTRUCTION MAP'S
    input domain, and thm:singleton-completeness is not on the construction
    path -- it is what a profile that DECLARES a singleton must record.
    """


class UndecidedGeometryError(StatisticsError):
    """A declared geometry's validation predicate is not decided by this module.

    Definition ``def:taxonomy`` gives the ``polytope`` tag the predicate
    "rational feasibility of ``{q >= 0, sum q = 1, B q <= b}``", which is a
    linear program rather than a closed form. Theorem ``thm:geometry-validation`` (iii)
    supplies the closed form for the CANONICAL BOX, which is the only ``polytope`` the
    construction map of Definition ``def:construction`` ever emits. A declared
    general polytope is therefore refused here and decided where the consumer
    already decides it exactly
    (``certiqs_key.meat_core.acceptance.geometry.polytope_is_nonempty``).
    """
