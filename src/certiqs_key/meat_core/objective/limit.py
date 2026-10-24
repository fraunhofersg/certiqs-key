"""The ``alpha -> 1+`` validation oracle of C16 (Theorem ``thm:oracle``).

contract.tex Eq. ``eq:oracle``::

    lim_{alpha -> 1+} h_low(alpha)
        = inf_{omega in Feas_1} sum_{chat in Chat_key} sum_{s in S_K(chat)}
          D( G_{chat,s}(omega_s) || Z(G_{chat,s}(omega_s)) )

a blockwise relative-entropy program. Remark ``rem:oracle`` fixes its status:
"Driving ``alpha -> 1+`` in an implementation of Eq. ``eq:choi-program`` and
comparing against either reference value on the same declaration is a
regression test; disagreement is a defect in the implementation, never a
research question. ... The oracle validates consistency of the ``alpha -> 1+``
limit; it does not certify (C13) and it does not validate finite-``alpha``
objective values."

**The two hypotheses are load-bearing and are enforced.** Theorem
``thm:oracle`` assumes (H1) a uniform floor ``p_0 > 0`` on ``q(chat)`` over the
whole acceptance set for every key-live ``chat``, and (H2) that the asymptotic
feasible set ``Feas_1 = {omega in Feas : Phi[omega] in AcceptSet}`` is nonempty.
Where they fail, the conforming behaviour is to REFUSE the comparison, not to
report a limit anyway: on a declaration whose acceptance set is unreachable,
``h_low(alpha)`` diverges as ``alpha -> 1+`` and no finite value is approached.
This module raises :class:`~certiqs_key.meat_core.errors.HypothesisError` there. Both
quantifiers run over the DECLARED SET on either geometry a declaration may
carry, so a set that is not a point is decided rather than refused; see
:func:`check_limit_hypotheses`, which records why that choice was made.

The relative entropy is finite wherever it is evaluated, and the contract says
why (thm:oracle): a vector in the kernel of ``Z(sigma)`` satisfies
``sigma^{1/2} Z_j |w> = 0`` for every ``j`` and therefore lies in the kernel of
``sigma``, so ``supp sigma`` is contained in ``supp Z(sigma)``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import numpy.typing as npt

from certiqs_key.meat_core import thresholds
from certiqs_key.meat_core.acceptance.geometry import (
    acceptance_floors,
    acceptance_verdict,
    polytope_of,
    singleton_frequencies,
)
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.errors import HypothesisError, UnsupportedDeclarationError
from certiqs_key.meat_core.objective.branch import (
    GeneratedMaps,
    branch_operator,
    statistics,
)
from certiqs_key.meat_core.objective.linalg import Matrix, pinch, support_spectrum

#: Absolute tolerance for membership of ``Phi[omega]`` in the declared
#: acceptance set, i.e. for hypothesis (H2) of Theorem ``thm:oracle``. It is
#: the tolerance this module has always applied to (H2) on a singleton, and the
#: polytope widening reuses it rather than choosing a second one.
#:
#: IT IS THE ``limit_membership`` ROW OF CONTRACT SECTION 2.6, READ FROM THE
#: DECLARED TABLE AND NOT WRITTEN HERE. `declared_thresholds` retires
#: that row into Group
#: C conditionally -- "an implementation that does not run the oracle carries
#: neither, and ONE THAT DOES DECLARES IT AS A GROUP B NUMBER, the object it
#: decides being one the module computed" -- and this module IS the oracle, so
#: the row is live and this constant is what carries it. Going through
#: :mod:`certiqs_key.meat_core.thresholds` is what puts it under the one-to-one
#: carrying rule and into ``tolerance_report``; a bare number here would be a
#: window this module chose, reported nowhere, on a predicate the contract
#: names.
ACCEPTANCE_TOLERANCE = thresholds.declared(thresholds.LIMIT_MEMBERSHIP)


def _log2_operator(operator: Matrix) -> Matrix:
    """Return ``log2`` on the support of a PSD operator, ``0`` on its kernel."""
    values, vectors = support_spectrum(operator)
    logs = np.where(values > 0.0, np.log2(np.where(values > 0.0, values, 1.0)), 0.0)
    return np.asarray((vectors * logs) @ vectors.conj().T, dtype=np.complex128)


def relative_entropy_to_pinching(
    operator: Matrix, labels: npt.NDArray[np.int64]
) -> float:
    """Return ``D(X || Z(X))`` in bits, the summand of Eq. ``eq:oracle``."""
    if operator.size == 0:
        return 0.0
    pinched = pinch(operator, labels)
    difference = _log2_operator(operator) - _log2_operator(pinched)
    return float(np.real(np.trace(operator @ difference)))


def limit_objective(maps: GeneratedMaps, omega: Mapping[str, Matrix]) -> float:
    """Return the right-hand side of Eq. ``eq:oracle`` at one state.

    The sum runs over the key-live acceptance values and every declared sector.
    Restricting it to the key-active sectors would give the same number --
    Proposition ``prop:exact-cancellation`` makes a key-inert branch operator
    ``Z``-block
    diagonal, so its relative entropy to its own pinching is zero -- and the
    unrestricted sum is the identity, so that is what is computed.
    """
    total = 0.0
    for chat in maps.chat_key:
        for sector in maps.sectors:
            branch = maps.branches[chat][sector]
            for klass in branch.classes:
                operator = branch_operator(klass, np.asarray(omega[sector]))
                total += relative_entropy_to_pinching(operator, klass.labels)
    return total


def _membership_defect(
    declaration: ProtocolDeclaration, predicted: Mapping[str, float]
) -> str | None:
    """Return why ``Phi[omega]`` is outside the declared acceptance set, or ``None``.

    Hypothesis (H2) asks whether ``Phi[omega]`` is a member of ``AcceptSet``,
    and what membership MEANS is fixed by the declared representation, read as
    data: a singleton denotes ``{q*}``, a polytope denotes
    ``{q >= 0, sum q = 1, B q <= b}`` -- all three conditions together, the same
    denotation :func:`~certiqs_key.meat_core.acceptance.geometry.polytope_is_nonempty`
    decides emptiness against. The comparison is numerical on both, at the one
    :data:`ACCEPTANCE_TOLERANCE` this module has always used for (H2).

    TWO SHAPE FACTS ARE PRECONDITIONS HERE, and both are established by the
    caller rather than re-checked, because a shape defect is not a failure of
    (H2) and must not be reported as one: every row of ``B`` has one entry per
    acceptance value, which
    :func:`~certiqs_key.meat_core.acceptance.geometry.acceptance_verdict` decides as
    well-formedness; and the column count matches the acceptance alphabet,
    which :func:`~certiqs_key.meat_core.acceptance.geometry.acceptance_floors` decides
    by returning ``None`` when it does not.
    """
    data = polytope_of(declaration.acceptance_set)
    if data is None:
        for chat, mass in singleton_frequencies(declaration).items():
            if abs(predicted[chat] - mass) > ACCEPTANCE_TOLERANCE:
                return (
                    f"Phi[omega] leaves the acceptance set at {chat!r} "
                    f"({predicted[chat]!r} against the declared {mass!r})"
                )
        return None
    values = declaration.acceptance_values
    point = [predicted[chat] for chat in values]
    for chat, mass in zip(values, point, strict=True):
        if mass < -ACCEPTANCE_TOLERANCE:
            return (
                f"Phi[omega] is negative at {chat!r} ({mass!r}), so it is not "
                "in the probability simplex the acceptance set lies in"
            )
    total = math.fsum(point)
    if abs(total - 1.0) > ACCEPTANCE_TOLERANCE:
        return (
            f"Phi[omega] sums to {total!r} rather than 1, so it is not in the "
            "probability simplex the acceptance set lies in"
        )
    for index, row in enumerate(data.rows):
        value = math.fsum(
            coefficient * mass for coefficient, mass in zip(row, point, strict=True)
        )
        if value > data.rhs[index] + ACCEPTANCE_TOLERANCE:
            return (
                f"Phi[omega] violates row {index} of the declared B q <= b "
                f"({value!r} against {data.rhs[index]!r})"
            )
    return None


def check_limit_hypotheses(maps: GeneratedMaps, witness: Mapping[str, Matrix]) -> float:
    """Raise unless Theorem ``thm:oracle``'s hypotheses hold; return ``p_0``.

    ``witness`` discharges (H2) by exhibiting a member of ``Feas_1``: it must be
    feasible and its statistics must lie in the acceptance set. Nonemptiness of
    ``Feas_1`` is a semidefinite feasibility question in general, so this
    module asks for the witness rather than searching for one -- and refuses
    when it does not check out.

    BOTH HYPOTHESES ARE DECIDED OVER THE WHOLE DECLARED SET, which is where
    Theorem ``thm:oracle`` states them: (H1) is the minimum of ``q(chat)`` over
    ``AcceptSet``, one exact linear program per coordinate
    (:func:`~certiqs_key.meat_core.acceptance.geometry.acceptance_floors`), and (H2) is
    a membership test in it. On a ``singleton`` both reduce to the declared
    vector and every frozen ``p_0`` of ``O_ALPHA_LIMIT_TABLE`` is unmoved: the
    minimum over a one-point set is that point.

    THE ROAD NOT TAKEN, recorded where the choice is made. The conforming
    alternative was to refuse a non-singleton declaration with a typed error and
    record the residual as a disclosed narrowing; the contract settles the
    hypotheses but not which of the two an implementation offers. It was
    declined on two counts. That narrowing would be disclosed in every
    result, so it would put a limitation of a REGRESSION ORACLE into the
    channel that discloses limitations of the RESULT. And Remark
    ``rem:oracle`` makes this oracle the independent check on an implementation
    of Eq. ``eq:choi-program``; withdrawing it on a newer acceptance geometry is
    the opposite of what it is for. The cost of the road taken is one linear
    program per acceptance value on machinery the acceptance oracle already
    trusts, and it decides nothing: the minimum, the membership and the
    tolerance are all fixed by the contract, by the declared representation, or
    by this module's existing (H2) constant.

    Raises:
        HypothesisError: if (H1) or (H2) fails at the supplied point.
        UnsupportedDeclarationError: if the declared acceptance set is one this
            implementation does not read, is ill formed, or is empty -- all
            three refused at declaration validation, so reaching one here means
            a declaration was built in memory and never checked -- or if it
            admits no floor at all, which no declaration parsed from a bundle
            can do. Refusing typed is the fail-closed answer in either case.
    """
    declaration = maps.declaration
    verdict = acceptance_verdict(declaration)
    if not verdict.admissible:
        raise UnsupportedDeclarationError(verdict.detail)
    # (H1)'s floors are computed first because they establish the shape
    # agreement (H2)'s membership test reads the declared rows under; the
    # (H1) VERDICT is still taken last, in the contract's own order.
    floors = acceptance_floors(declaration)
    if floors is None:
        raise UnsupportedDeclarationError(
            "no floor on q(chat) over the declared acceptance set could be "
            "computed, so Theorem thm:oracle hypothesis (H1) cannot be decided "
            "and the alpha -> 1+ comparison is refused rather than run on an "
            "undecided hypothesis"
        )
    # (H2) first: it is the hypothesis that fails on a declaration whose
    # acceptance set is unreachable, which is the case the contract singles out.
    predicted = statistics(maps, witness)
    defect = _membership_defect(declaration, predicted)
    if defect is not None:
        raise HypothesisError(
            "Theorem thm:oracle hypothesis (H2) is not discharged: the "
            f"supplied state is not in Feas_1, because {defect}. Where Feas_1 "
            "is EMPTY the conforming behaviour is to refuse the alpha -> 1+ "
            "comparison: h_low(alpha) then diverges instead of converging"
        )
    if not maps.chat_key:
        raise HypothesisError(
            "Theorem thm:oracle's limit is a sum over Chat_key, which is empty "
            "for this declaration: there is no key-live acceptance value, so "
            "the blockwise relative-entropy program is trivially zero and the "
            "comparison carries no information"
        )
    floor = min(floors[chat] for chat in maps.chat_key)
    if floor <= 0.0:
        raise HypothesisError(
            "Theorem thm:oracle hypothesis (H1) fails: the acceptance set does "
            "not put a uniform positive floor p_0 on q(chat) for every key-live "
            f"chat (the smallest floor over the declared set is {floor!r})"
        )
    return floor
