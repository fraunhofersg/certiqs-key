"""thm:box-oracle (ii)-(iii) -- the exact box minimum and its tight dual witness.

WHAT THIS IS, AND WHAT IT IS NOT
===============================
Theorem ``thm:box-oracle`` splits into an interface obligation of
this module and proven facts about the geometry it emits, and the two bind
differently.

* Part (i) IS an obligation: the outputs table of ``interface.yaml`` carries the row
  ``acceptance_support`` and names ``thm:box-oracle`` (i) in its domain cell. It lives
  in :func:`certiqs_key.statistics.taxonomy.acceptance_support`.
* Parts (ii) and (iii) are PROVEN FACTS ABOUT THE EMITTED GEOMETRY, NOT
  OUTPUTS. Neither ``g``, nor ``min <g, q>``, nor ``(u, v)``, nor ``beta_acc``
  appears in the Inputs or the Outputs table, and Remark ``rem:box-oracle-consumer``
  says so directly: Eq. ``eq:bacc-shape`` is the CONSUMING contract's INPUT
  OBLIGATION, and what thm:box-oracle supplies is that for the representation this
  module emits the minimum is computable in closed form, exactly -- "no dual search and
  no linear-programming solve is needed" -- with the witness available "for
  independent re-verification in exactly the shape that remark's
  instantiation (b) expects".

So this module MAY expose the closed form and MAY omit it; exposing it violates
no claim and omitting it would violate none either. It is exposed here because
the geometry is this module's and the closed form is a property of that
geometry, and because a second, independent route to the same number is worth
having at a boundary the consumer crosses with a linear program.

WHAT IT MAY NOT DO, AND DOES NOT: EMIT A NUMBER AS ``beta_acc``. That quantity
belongs to the consuming contract and is admitted there only through THAT
contract's own admissibility check on ``g + B^T u + v``. Nothing here writes a
``beta_acc``, and nothing here is on a certified path: a consumer that wants one
runs its own check on its own machine numbers, which is what makes the check a
check.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.statistics.taxonomy import PolytopeGeometry, validate_geometry

__all__ = [
    "BoxMinimum",
    "box_minimum",
]

_ZERO = Fraction(0)
_ONE = Fraction(1)


@dataclass(frozen=True)
class BoxMinimum:
    """The exact solution of ``min <g, q>`` over a canonical box, with a witness.

    Every field is exact. ``sorted_order``, ``widths``, ``j_star`` and
    ``fill_increment`` are the greedy data of Eq. ``eq:greedy``; ``lam``,
    ``dual_v`` and ``dual_u`` are the witness of part (iii), in the format of
    the consuming contract's Remark ``rem:acc-side`` (b).
    """

    outcomes: tuple[str, ...]
    #: ``g``, in the DECLARATION's enumeration.
    objective: tuple[Fraction, ...]
    #: The SECOND enumeration of Theorem thm:box-oracle (ii): ``g`` ascending. The
    #: rows of ``B`` are always indexed by the first one (``spec/notation.md``).
    sorted_order: tuple[str, ...]
    #: ``r = 1 - sum q^-``, the residual mass above the floors.
    residual_r: Fraction
    #: ``D_i = q^+(c_i) - q^-(c_i)``, in ``sorted_order``.
    widths: tuple[Fraction, ...]
    #: The least index whose prefix width reaches ``r``, named by outcome.
    j_star: str
    #: ``w = r - sum_{i < j^*} D_i``, the fill increment at the split.
    fill_increment: Fraction
    #: ``q^opt`` of Eq. eq:greedy, in the DECLARATION's enumeration.
    q_opt: tuple[Fraction, ...]
    minimum: Fraction
    #: ``lambda = g(c_{j^*})`` and ``v = -lambda``.
    lam: Fraction
    dual_v: Fraction
    #: ``u = (u^+, u^-)`` in ROW order: the ``m`` caps first, then the ``m``
    #: floors, both in the declaration's enumeration (Eq. eq:boxrows).
    dual_u: tuple[Fraction, ...]
    #: ``g + B^T u + v`` per outcome. ZERO in every coordinate: Eq.
    #: eq:dualfeas holds with EQUALITY, which is why the bound is tight.
    dual_feasibility: tuple[Fraction, ...]
    #: ``-<b, u> - v``. Equals :attr:`minimum`; the witness is tight.
    dual_value: Fraction


def box_minimum(
    geometry: PolytopeGeometry, objective: tuple[Fraction, ...]
) -> BoxMinimum | None:
    """Return ``min <g, q>`` over a canonical box in closed form, or ``None``.

    ``None`` exactly when the geometry's validation predicate fails, and that
    refusal is load-bearing rather than defensive. Theorem ``thm:box-oracle`` (ii) is
    stated for a NON-EMPTY box and takes ``r >= 0`` and the existence of
    ``j^*`` from Theorem ``thm:geometry-validation`` (iii); outside that hypothesis it
    proves nothing, and the fill still returns a number. The frozen
    ``INVALID-box-floors-above-one`` case is the instance: there ``r = -1/5`` is
    NEGATIVE, the rule "the least ``j`` whose prefix width reaches ``r``" is
    satisfied at the first index by ``0 >= -1/5``, and a minimization that skips
    the feasibility test reports a number for a set with no points in it. The
    hypothesis ``0 <= q^- <= q^+`` is equally load-bearing: it is what makes
    every width non-negative and the prefix sums monotone, so that "the least
    index whose prefix reaches ``r``" is the index the exchange argument
    justifies (``ILLFORMED-box-inverted``).

    THE TIE-BREAK IS FREE AND THE VALUE IS NOT. Theorem ``thm:box-oracle`` (ii) fixes
    an enumeration with ``g`` ascending but does not determine it when ``g`` has
    repeated values, so the construction depends on a choice the theorem does
    not make. The sort here is STABLE, which breaks ties by the declaration's
    own enumeration; the frozen ``PMIN-tie-in-g`` case pins that the two
    orderings give DIFFERENT minimizers and the SAME minimum, and the proof's
    own identity is why: ``(g(c_i) - lambda) = 0`` at every tied index, so those
    summands vanish whichever tied index is called ``j^*``.
    """
    if geometry.box_bounds is None:
        return None
    if not validate_geometry(geometry).admissible:
        return None
    lower, upper = geometry.box_bounds
    size = len(geometry.outcomes)
    if len(objective) != size:
        raise ValueError(
            f"the objective has {len(objective)} entries but the geometry has "
            f"{size} outcomes"
        )
    order = sorted(range(size), key=lambda index: objective[index])
    widths = tuple(upper[index] - lower[index] for index in order)
    residual = _ONE - sum(lower, _ZERO)
    split = 0
    prefix = _ZERO
    for position, width in enumerate(widths):
        prefix = prefix + width
        split = position
        if prefix >= residual:
            break
    increment = residual - sum(widths[:split], _ZERO)
    values = list(lower)
    for position, index in enumerate(order):
        if position < split:
            values[index] = upper[index]
        elif position == split:
            values[index] = lower[index] + increment
    q_opt = tuple(values)
    minimum = sum(
        (weight * value for weight, value in zip(objective, q_opt, strict=True)),
        _ZERO,
    )
    lam = objective[order[split]]
    caps = tuple(max(lam - weight, _ZERO) for weight in objective)
    floors = tuple(max(weight - lam, _ZERO) for weight in objective)
    dual_v = -lam
    dual_u = caps + floors
    dual_feasibility = tuple(
        weight + (cap - floor) + dual_v
        for weight, cap, floor in zip(objective, caps, floors, strict=True)
    )
    pairing = sum(
        (
            bound * multiplier
            for bound, multiplier in zip(geometry.rhs, dual_u, strict=True)
        ),
        _ZERO,
    )
    return BoxMinimum(
        outcomes=geometry.outcomes,
        objective=objective,
        sorted_order=tuple(geometry.outcomes[index] for index in order),
        residual_r=residual,
        widths=widths,
        j_star=geometry.outcomes[order[split]],
        fill_increment=increment,
        q_opt=q_opt,
        minimum=minimum,
        lam=lam,
        dual_v=dual_v,
        dual_u=dual_u,
        dual_feasibility=dual_feasibility,
        dual_value=-pairing - dual_v,
    )
