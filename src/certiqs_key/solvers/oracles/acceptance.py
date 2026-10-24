"""The acceptance-set linear oracle for the frequency vector ``q``.

spec/architecture.md 7.2: the outer frequency vector ``q`` is optimised jointly
over ``Q_acc``, never by the Choi oracle, and "its linear minimisation, which
every bracket pairs with, is a **separate acceptance-set linear oracle**". (How
``q`` MOVES is the loop's geometry-keyed rule,
:mod:`certiqs_key.solvers.frank_wolfe.q_rule`; this oracle is what the bracket
consumes under every rule.) spec/architecture.md 7.4
repeats it from the other side: the ``q``-frequency LMO is "out of scope
entirely" for QICS.

Two geometries are read, the two the accepted ``statistics``
taxonomy defines (Definition ``def:taxonomy``) and the two contract
Remark ``rem:acc-side`` certifies:

* ``singleton`` -- the acceptance set is one declared frequency vector, the
  outer infimum of Eq. ``eq:hlow-def`` is an evaluation, and the ``q`` block of
  the Frank-Wolfe direction is identically zero;
* ``polytope`` -- ``{q in simplex(Chat) : B q <= b}``, where the outer infimum
  is a genuine linear program and the ``q`` block of the direction is not zero.
  It is solved exactly, over the rationals
  (:mod:`certiqs_key.meat_core.acceptance.simplex`).

Every other tag is refused upstream, in
:mod:`certiqs_key.meat_core.declaration.validation`, and never reaches this module. What
that leaves out of def:admissible-acceptance-set's "any closed convex subset" is
DISCLOSED rather than implicit: the refusal's own message states it
(:func:`~certiqs_key.meat_core.acceptance.geometry.acceptance_verdict`).

AN EMPTY ACCEPTANCE SET NEVER REACHES AN ORACLE
===============================================
It is refused at declaration validation, and refused again by the solve entry
point for a declaration built in memory, where the conforming answer is
``h_low = +inf`` with no key-length claim rather than an exception (Remark
``rem:hlow-range``). So the oracles below may assume a non-empty set, and
:func:`acceptance_oracle` says so by raising rather than by returning something
that would have to be checked again later.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol, runtime_checkable

from certiqs_key.meat_core.acceptance.geometry import (
    POLYTOPE,
    acceptance_contains_exact,
    acceptance_minimizer,
    acceptance_minimizer_exact,
    acceptance_start,
    acceptance_start_exact,
    acceptance_verdict,
)
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.errors import UnsupportedDeclarationError


@runtime_checkable
class AcceptanceOracle(Protocol):
    """The linear minimization oracle over the declared acceptance set."""

    def start(self) -> dict[str, float]:
        """Return a member of the acceptance set to start from."""
        ...

    @property
    def exact_island(self) -> bool:
        """Return whether ``q_t`` was formed on the exact island."""
        ...

    def minimize(self, gradient: Mapping[str, float]) -> dict[str, float]:
        """Return a minimizer of the linear cost over the acceptance set."""
        ...


@runtime_checkable
class ExactAcceptanceOracle(AcceptanceOracle, Protocol):
    """An acceptance oracle that also hands out its points as EXACT rationals.

    Remark ``rem:acc-side`` (alpha) and (beta): ``q_t`` is in the acceptance set
    BY CONSTRUCTION when it starts at an exact rational point of the set and
    every update is a convex combination, with exact rational weights, of
    exact points of the set. A driver meets that on a moving geometry only if
    the oracle gives it those exact points: ``start`` and ``minimize`` return
    their binary64 roundings, which need not lie in the set, and serve as the
    views the objective is EVALUATED at.

    A MOVING GEOMETRY WHOSE ORACLE IS NOT ONE OF THESE cannot keep ``q_t`` on
    the island, and the driver then records ``acceptance_iterate_exact =
    False`` from the first step that moves ``q`` (withdrawal under
    ``iterate_not_feasible``, Remark ``rem:fo-interface``).
    """

    def exact_start(self) -> dict[str, Fraction]:
        """Return the start of :meth:`start` as exact rationals."""
        ...

    def exact_minimize(self, gradient: Mapping[str, float]) -> dict[str, Fraction]:
        """Return the minimizer of :meth:`minimize` as exact rationals."""
        ...

    def exact_contains(self, point: Mapping[str, Fraction]) -> bool:
        """Return whether an exact point is in the acceptance set, decided exactly.

        What lets a driver SHORTEN a long exact iterate: a short exact point
        this predicate admits is a point established to lie in the set, and
        Remark ``rem:acc-side`` (beta) admits any such point into the next
        convex combination (:mod:`~certiqs_key.solvers.frank_wolfe.
        acceptance_iterate`).
        """
        ...


@dataclass(frozen=True)
class SingletonAcceptanceOracle:
    """The acceptance oracle of a declared singleton acceptance set.

    Its linear minimization is the identity: the feasible set has one point, so
    the Frank-Wolfe direction in the ``q`` block is identically zero and
    contributes nothing to the gap. The driver does not special-case that -- it
    takes the direction it is given, and a zero one moves nothing.
    """

    frequencies: Mapping[str, float]

    #: THE ACCEPTANCE FACTOR OF THE MEMBERSHIP, RECORDED AND NOT MEASURED.
    #: Remark ``rem:acc-side``: the acceptance half of Eq. ``eq:lmo`` is
    #: DISCHARGED rather than assumed, by conditions (alpha) and (beta) that
    #: make ``q_t in AcceptSet`` true BY CONSTRUCTION on the exact island of
    #: the conventions. the `outputs` table asks the
    #: per-iterate record to carry the
    #: boolean as "A RECORDED PROPERTY, NEVER A MEASUREMENT", which is what
    #: this is: the geometry either constructs its iterate on the island or it
    #: does not, and no residual is taken of it.
    #:
    #: "THE ACCEPTANCE FACTOR ADDS NO FOURTH EXPOSURE: it is not measured at
    #: all -- it is exact by construction on the island -- so the count is
    #: THREE because the three are the J-side checks, and the product's other
    #: factor is established in a way that has no residual to expose."
    exact_island: bool = True

    def start(self) -> dict[str, float]:
        """Return the single accepted frequency vector."""
        return dict(self.frequencies)

    def minimize(self, gradient: Mapping[str, float]) -> dict[str, float]:
        """Return the single accepted frequency vector, whatever the cost."""
        del gradient
        return dict(self.frequencies)


@dataclass(frozen=True)
class PolytopeAcceptanceOracle:
    """The acceptance oracle of a declared polytope acceptance set.

    ``minimize`` is the exact linear program ``min <g, q>`` over
    ``{q >= 0, sum q = 1, B q <= b}``, whose answer is a VERTEX. ``start`` is
    deliberately not a vertex: Corollary ``cor:full-gradient`` is stated at a
    point with ``q(chat) > 0``, so a run starting at a vertex would ask for a
    gradient whose ``q``-derivative is ``-inf`` at the first coordinate the
    vertex sets to zero. The start is the average of one maximizer per
    coordinate, which lies in the set by convexity and is strictly positive on
    exactly the minimal acceptance support; the driver's step cap keeps it that
    way for the rest of the run.
    """

    declaration: ProtocolDeclaration

    #: TRUE BECAUSE THIS ORACLE IS AN :class:`ExactAcceptanceOracle`. The
    #: polytope is the geometry on which a binary64 convex combination leaves
    #: the set, so the flag is true only of a ``q_t`` a driver formed from
    #: :meth:`exact_start` and :meth:`exact_minimize` in exact arithmetic
    #: (:mod:`certiqs_key.solvers.frank_wolfe.acceptance_iterate`), and the
    #: per-gate record is the driver's, not this constant.
    #:
    #: THE ACCEPTANCE FACTOR OF THE MEMBERSHIP, RECORDED AND NOT MEASURED.
    #: Remark ``rem:acc-side``: the acceptance half of Eq. ``eq:lmo`` is
    #: DISCHARGED rather than assumed, by conditions (alpha) and (beta) that
    #: make ``q_t in AcceptSet`` true BY CONSTRUCTION on the exact island of
    #: the conventions. the `outputs` table asks the
    #: per-iterate record to carry the
    #: boolean as "A RECORDED PROPERTY, NEVER A MEASUREMENT", which is what
    #: this is: the geometry either constructs its iterate on the island or it
    #: does not, and no residual is taken of it.
    #:
    #: "THE ACCEPTANCE FACTOR ADDS NO FOURTH EXPOSURE: it is not measured at
    #: all -- it is exact by construction on the island -- so the count is
    #: THREE because the three are the J-side checks, and the product's other
    #: factor is established in a way that has no residual to expose."
    exact_island: bool = True

    def start(self) -> dict[str, float]:
        """Return a member of the acceptance set positive wherever it can be."""
        return acceptance_start(self.declaration)

    def minimize(self, gradient: Mapping[str, float]) -> dict[str, float]:
        """Return an exact minimizer of the linear cost over the polytope."""
        return acceptance_minimizer(self.declaration, gradient)

    def exact_start(self) -> dict[str, Fraction]:
        """Return the start as exact rationals: Remark ``rem:acc-side`` (alpha)."""
        return acceptance_start_exact(self.declaration)

    def exact_minimize(self, gradient: Mapping[str, float]) -> dict[str, Fraction]:
        """Return the vertex as exact rationals: Remark ``rem:acc-side`` (beta)."""
        return acceptance_minimizer_exact(self.declaration, gradient)

    def exact_contains(self, point: Mapping[str, Fraction]) -> bool:
        """Return whether an exact point is in the polytope, decided exactly."""
        return acceptance_contains_exact(self.declaration, point)


def acceptance_oracle(declaration: ProtocolDeclaration) -> AcceptanceOracle:
    """Return the acceptance oracle a declaration asks for.

    Raises:
        UnsupportedDeclarationError: if the declared geometry is not one this
            module reads, or if its set is ill-formed or empty. All three are
            refused at declaration validation, so reaching one here means a
            declaration was built in memory and never checked; refusing is the
            fail-closed answer and the caller decides how to report it.
    """
    verdict = acceptance_verdict(declaration)
    if not verdict.admissible:
        raise UnsupportedDeclarationError(verdict.detail)
    if declaration.acceptance_set.geometry == POLYTOPE:
        return PolytopeAcceptanceOracle(declaration=declaration)
    return SingletonAcceptanceOracle(
        frequencies=dict(
            zip(
                declaration.acceptance_values,
                declaration.acceptance_set.frequencies,
                strict=True,
            )
        )
    )
