"""Toy declarations carrying a NON-SINGLETON acceptance set.

``tests/oracles/toy_declarations.py`` is FROZEN and every
declaration in it carries a ``singleton`` geometry. The polytope acceptance
oracle needs a declaration whose acceptance set is not a point -- otherwise the ``q``
block of the Frank-Wolfe direction is identically zero and the joint
optimization is never exercised end to end -- so the toys live here, outside the
frozen tree.

THEY ARE ADDITIONS AND NOT EDITS, deliberately. ``ALL_TOYS``, ``ALL_TOYS_0_3_0``
and ``ALL_TOYS_0_4_0`` are untouched, so the frozen arithmetic identity in
``tests/oracles/test_registry_integrity.py::
test_the_certificate_toys_are_registered_and_new`` -- ``len(ALL_TOYS_0_4_0) ==
len(ALL_TOYS) + 7 + len(CERTIFICATE_TOYS)`` -- still holds, and no frozen
consumer sees a declaration it did not see before.

TOY-8-T-POLY, and why it is built from TOY-8-T
==============================================
TOY-8-T is the toy whose FEASIBLE SET IS A SINGLE POINT: ``d_A = 2`` with the
trusted marginal ``tau_A = diag(7/8, 1/8)`` on a one-dimensional ``Q``, so
Eq. ``eq:feas`` forces ``omega = tau_A`` and ``Phi[omega] = (7/8, 1/8)`` is
fixed. Everything the objective can still move is therefore in ``q``, which is
exactly the block this band adds -- a run on it that lands on the right answer
lands there through the acceptance oracle and through nothing else.

Its acceptance set here is the canonical box

    ``q^- = (1/4, 1/8)`` , ``q^+ = (3/4, 3/4)`` ,

whose denotation on the 2-simplex is the segment
``{(a, 1 - a) : 1/4 <= a <= 3/4}``. The objective
``(alpha/(alpha-1)) D(q || (7/8, 1/8))`` decreases in ``a`` towards ``7/8``, so
the infimum is at the box cap ``a = 3/4`` -- a point INSIDE no facet of the
simplex and strictly positive in both coordinates, so Corollary
``cor:full-gradient``'s hypotheses hold along the whole run and the certificate
can be requested at the end of it. In closed form, at any ``alpha``:

    ``h_low = (alpha/(alpha-1)) [ (3/4) log2(6/7) + 1/4 ]`` ,

which at ``alpha = 3/2`` is ``0.2496170519929917...``.

The start the oracle picks is the average of the two coordinate maximizers,
``((3/4, 1/4) + (1/4, 3/4))/2 = (1/2, 1/2)``, so the run has to MOVE ``q`` to
reach the answer and a driver that ignored the acceptance direction would stop
at ``(1/2, 1/2)`` with a visibly larger ``h_low``.
"""

from __future__ import annotations

import math
from dataclasses import replace

from toy_declarations import ToyDeclaration, toy

#: ``(q^-, q^+)`` of the canonical box, and the ``(B, b)`` rows Eq.
#: ``eq:boxrows`` spells them out as: row ``i`` is ``+e_i`` at ``q^+(c_i)``, row
#: ``m + i`` is ``-e_i`` at ``-q^-(c_i)``.
BOX_LOWER: tuple[float, ...] = (0.25, 0.125)
BOX_UPPER: tuple[float, ...] = (0.75, 0.75)

POLYTOPE_ACCEPTANCE_SET: dict[str, object] = {
    "geometry": "polytope",
    "m_row": 4,
    "B": ((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)),
    "b": (BOX_UPPER[0], BOX_UPPER[1], -BOX_LOWER[0], -BOX_LOWER[1]),
    "box_bounds": (BOX_LOWER, BOX_UPPER),
}

#: The same box written WITHOUT its ``box_bounds`` record. Identical denotation,
#: identical rows; what differs is only that a consumer cannot tell it is a box.
#: contract Remark ``rem:acc-side`` (b) asks for exact ``B`` and ``b`` and
#: nothing more, and ``statistics-acceptance`` calls the box a sub-form rather
#: than a tag, so the two must give the same answer -- which is what makes this
#: pair worth having.
GENERAL_ACCEPTANCE_SET: dict[str, object] = {
    key: value for key, value in POLYTOPE_ACCEPTANCE_SET.items() if key != "box_bounds"
}


def _with_acceptance_set(
    base: ToyDeclaration, toy_id: str, acceptance: dict[str, object], summary: str
) -> ToyDeclaration:
    """Return ``base`` with a different declared acceptance set."""
    return replace(
        base,
        toy_id=toy_id,
        acceptance_set=dict(acceptance),
        summary=summary,
        derivation=base.derivation
        + f"""
ACCEPTANCE SET REPLACED, for the polytope acceptance-oracle band. The feasible
set is unchanged and is still the single point omega = tau_A, so
Phi[omega] = (7/8, 1/8) is fixed and the whole of the remaining optimization is
in q. The declared set is the canonical box q^- = {BOX_LOWER}, q^+ = {BOX_UPPER},
i.e. the segment {{(a, 1-a) : 1/4 <= a <= 3/4}} of the 2-simplex.

  D((a, 1-a) || (7/8, 1/8)) = a log2(a/(7/8)) + (1-a) log2((1-a)/(1/8))

is decreasing in a on (0, 7/8), so the infimum over the segment is at a = 3/4:

  h_low = (alpha/(alpha-1)) [ (3/4) log2(6/7) + 1/4 ] ,

which is {POLYTOPE_H_LOW_AT_ALPHA_1_5!r} at alpha = 3/2. Both coordinates of the
minimizer are strictly positive, so the gradient hypotheses of Corollary
cor:full-gradient hold there and a certificate may be requested.
""",
    )


#: ``h_low`` of the polytope toy at ``alpha = 3/2``, in closed form. Derived
#: from the declaration by hand (see the module docstring), not read off a run.
POLYTOPE_H_LOW_AT_ALPHA_1_5: float = 3.0 * (
    0.75 * math.log2(6.0 / 7.0) + 0.25 * math.log2(2.0)
)

#: The minimizer that value is attained at.
POLYTOPE_ARGMIN: dict[str, float] = {"chat0": 0.75, "chat1": 0.25}

#: The start the polytope oracle picks: the average of the two coordinate
#: maximizers ``(3/4, 1/4)`` and ``(1/4, 3/4)``.
POLYTOPE_START: dict[str, float] = {"chat0": 0.5, "chat1": 0.5}


def polytope_toy() -> ToyDeclaration:
    """Return TOY-8-T with a canonical-box acceptance set."""
    return _with_acceptance_set(
        toy("TOY-8-T"),
        "TOY-8-T-POLY",
        POLYTOPE_ACCEPTANCE_SET,
        "TOY-8-T with a canonical-box polytope acceptance set on the segment "
        "1/4 <= q(chat0) <= 3/4. The feasible set is still one point, so the "
        "whole optimization is in q and h_low is attained at the box cap.",
    )


def general_polytope_toy() -> ToyDeclaration:
    """Return the same set declared WITHOUT its canonical-box record."""
    return _with_acceptance_set(
        toy("TOY-8-T"),
        "TOY-8-T-POLY-GENERAL",
        GENERAL_ACCEPTANCE_SET,
        "TOY-8-T-POLY with box_bounds omitted: the same (B, b), the same "
        "denotation, and nothing telling a consumer it is a box.",
    )
