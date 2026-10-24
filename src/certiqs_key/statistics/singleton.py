"""singleton/thm:singleton-completeness -- singleton completeness, both degenerate routes.

Theorem ``thm:singleton-completeness`` is about a geometry THE CONSTRUCTION MAP
NEVER EMITS (Remark ``rem:singleton-honest``). The tag is in the taxonomy
because a consumer's currently implemented acceptance oracle reads exactly that
geometry and because the consuming contract certifies its acceptance-side
minimum; what thm:singleton-completeness supplies is the completeness figure a profile
that DECLARES one must record.

Eq. ``eq:singleton-acc``, with the convention ``0^0 = 1``:

    Pr[freq = q^*] = n! / prod_chat (n q^*(chat))!
                     * prod_chat p^hon(chat)^{n q^*(chat)}

when every ``n q^*(chat)`` is a non-negative integer, and ``0`` otherwise.

THE DEGENERATE CASE IS NOT AN EDGE CASE, AND ``ecomp = 1`` IS NOT A SUBSTITUTE
==============================================================================
Theorem ``thm:singleton-completeness`` (ii): the accept probability is ``0`` if and only
if either ``n q^*`` has a non-integer coordinate or ``q^*`` is not absolutely continuous
with respect to ``p^hon``. The two routes are INDEPENDENT -- the second can fail
with perfectly integral counts and a positive multinomial coefficient -- and in
either case the admissible-budget interval is ``[1, 1)``, which is EMPTY. No
``ecomp`` in ``[0, 1)`` is admissible, and a profile declaring such a geometry
"must record that fact rather than a budget of ``1``, which is outside the
declared domain of ``ecomp``". :attr:`SingletonCompleteness.least_admissible_budget`
is therefore ``None`` and never ``1``.

Remark ``rem:singleton-honest`` adds that this is reached "at most round
counts": for a fixed ``q^*``, ``n q^*`` has a non-integer coordinate for all but
a sparse set of ``n``.
"""  # noqa: E501

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.statistics.construction import HonestEnvelope
from certiqs_key.statistics.errors import HypothesisError
from certiqs_key.statistics.taxonomy import SingletonGeometry, validate_geometry

__all__ = [
    "SingletonCompleteness",
    "singleton_completeness",
]

_ZERO = Fraction(0)
_ONE = Fraction(1)


@dataclass(frozen=True)
class SingletonCompleteness:
    """The exact completeness figure of a DECLARED ``singleton`` geometry."""

    outcomes: tuple[str, ...]
    honest: tuple[Fraction, ...]
    rounds: int
    q_star: tuple[Fraction, ...]
    #: Whether every ``n q^*(chat)`` is a non-negative integer.
    counts_are_integral: bool
    #: ``(n q^*(chat))_chat`` when integral, else ``None``.
    counts: tuple[int, ...] | None
    #: Whether ``q^* << p^hon``: ``q^*(chat) > 0`` implies ``p^hon(chat) > 0``.
    absolutely_continuous: bool
    #: ``n! / prod (n q^*)!`` when the counts are integral, else ``None``.
    multinomial_coefficient: int | None
    #: Eq. eq:singleton-acc.
    accept_probability: Fraction
    #: Eq. eq:singleton-budget, or ``None`` when NO admissible budget exists.
    least_admissible_budget: Fraction | None

    @property
    def admissible_budget_exists(self) -> bool:
        """Return whether any ``ecomp`` in ``[0, 1)`` is admissible at all."""
        return self.least_admissible_budget is not None


def singleton_completeness(
    geometry: SingletonGeometry,
    honest: tuple[Fraction, ...] | HonestEnvelope,
    rounds: int,
) -> SingletonCompleteness:
    """Return the exact accept probability and least budget of ``thm:singleton-completeness``.

    The hypotheses of Theorem ``thm:singleton-completeness`` are checked rather than
    assumed: A-HON with law ``p^hon`` on ``Chat``, and a ``singleton`` geometry whose
    validation predicate holds. Outside them the formulas still evaluate and
    prove nothing, so this raises
    :class:`~certiqs_key.statistics.errors.HypothesisError` instead.

    The counting is the proof's own: ``freq = q^*`` holds exactly when
    ``N_chat = n q^*(chat)`` for every ``chat`` (Definition ``def:freq``), which
    is IMPOSSIBLE -- not improbable -- unless every ``n q^*(chat)`` is a
    non-negative integer; each string with those counts has probability
    ``prod_chat p^hon(chat)^{n_chat}`` under A-HON, and the number of such
    strings is the multinomial coefficient.
    """  # noqa: E501
    if rounds < 1:
        raise HypothesisError(
            "Theorem thm:singleton-completeness is stated for n >= 1 rounds; "
            f"got n = {rounds}"
        )
    if isinstance(honest, HonestEnvelope):
        honest = _degenerate_law(geometry, honest)
    size = len(geometry.outcomes)
    if len(honest) != size:
        raise HypothesisError(
            f"p^hon carries {len(honest)} coordinates against |Chat| = {size}"
        )
    if any(value < _ZERO for value in honest) or sum(honest, _ZERO) != _ONE:
        raise HypothesisError(
            "Assumption A-HON gives the honest rounds a LAW on Chat; the "
            "argument is not a probability vector"
        )
    verdict = validate_geometry(geometry)
    if not verdict.admissible:
        raise HypothesisError(
            "Theorem thm:singleton-completeness is stated for a singleton geometry "
            f"with q^* in the simplex, and this one is inadmissible: {verdict.detail}"
        )
    scaled = tuple(rounds * value for value in geometry.frequencies)
    integral = all(value.denominator == 1 for value in scaled)
    counts = tuple(int(value) for value in scaled) if integral else None
    absolutely_continuous = all(
        law > _ZERO
        for target, law in zip(geometry.frequencies, honest, strict=True)
        if target > _ZERO
    )
    coefficient: int | None = None
    probability = _ZERO
    if counts is not None:
        coefficient = math.factorial(rounds)
        for count in counts:
            coefficient //= math.factorial(count)
        weight = _ONE
        for law, count in zip(honest, counts, strict=True):
            # The convention 0^0 = 1 of Eq. eq:singleton-acc is Python's own,
            # and it is load-bearing: without it the weight of a point mass
            # against its own outcome is undefined on a case whose answer is 1.
            weight = weight * law**count
        probability = Fraction(coefficient) * weight
    return SingletonCompleteness(
        outcomes=geometry.outcomes,
        honest=honest,
        rounds=rounds,
        q_star=geometry.frequencies,
        counts_are_integral=integral,
        counts=counts,
        absolutely_continuous=absolutely_continuous,
        multinomial_coefficient=coefficient,
        accept_probability=probability,
        # Eq. eq:singleton-budget. The admissible budgets are the interval
        # [1 - Pr, 1), which is non-empty iff Pr > 0; at Pr = 0 it is [1, 1)
        # and there is NO admissible budget -- not a budget of 1.
        least_admissible_budget=(_ONE - probability) if probability > _ZERO else None,
    )


def _degenerate_law(
    geometry: SingletonGeometry, envelope: HonestEnvelope
) -> tuple[Fraction, ...]:
    """Return the law of a DEGENERATE envelope, or refuse a non-degenerate one.

    ``rem:singleton-honest``: the singleton takes the
    point form of the honest input only, because ``thm:singleton-completeness``'s accept
    probability is a multinomial mass under one i.i.d. law (A-HON). A degenerate
    envelope IS that law (``lem:hon-degenerate``); a non-degenerate one is
    refused with ``honest_envelope_not_degenerate`` and is not reduced to one of
    its laws, which would certify a figure for a channel the caller did not
    declare (``interface.yaml``, ``submodules_today.singleton.honest_input``).
    """
    try:
        lower = tuple(Fraction(envelope.lower[chat]) for chat in geometry.outcomes)
        upper = tuple(Fraction(envelope.upper[chat]) for chat in geometry.outcomes)
    except (KeyError, TypeError) as error:
        raise HypothesisError(
            "the honest envelope is not a pair of rational vectors on Chat"
        ) from error
    if lower != upper:
        raise HypothesisError(
            "honest_envelope_not_degenerate: Theorem thm:singleton-completeness is "
            "stated under A-HON for one law, and this envelope is not degenerate"
        )
    return lower
