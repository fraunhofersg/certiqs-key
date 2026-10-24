"""The declared acceptance-set geometries, read as data.

``meat-core`` defines NO geometry vocabulary of its own. The `inputs` table
types ``acceptance_set`` as "a closed convex subset of the probability simplex
on Chat" (def:admissible-acceptance-set) and enumerates no geometries; the taxonomy is
owned by ``statistics``, whose accepted taxonomy fixes exactly two
tags in its Definition ``def:taxonomy``:

* ``singleton`` -- data ``q*``, denoting ``{q*}``;
* ``polytope`` -- data ``(m_row, B, b)``, denoting
  ``{q in simplex(Chat) : B q <= b}``, with the CANONICAL BOX as a recorded
  sub-form rather than a third tag.

They are in one-to-one correspondence with the two instantiations of contract
Remark ``rem:acc-side``, which is what makes both certifiable here: (a) is an
evaluation, (b) is the dual bound ``-<b, u> - v``. A declaration whose set fits
neither is REFUSED AT ADMISSION, before any solve, and no first-order bound is
formed for it (``req:acceptance-geometries``): a tag outside the taxonomy is
refused rather than guessed.

THE EMPTY SET IS THE HAZARD, AND IT IS NOT A TAG ERROR
======================================================
The empty set is closed, convex and a subset of the simplex, so it satisfies
def:admissible-acceptance-set. Then Eq. ``eq:bacc-def`` is VACUOUS -- a minimum over the
empty set is ``+inf``, so every real number is a valid ``beta_acc``, including
numbers that make ``h_cert`` as large as one likes -- and the componentwise
admissibility test of Remark ``rem:acc-side`` (b) is no defence, because it is a
condition on ``g``, ``B`` and ``v`` alone and says nothing about whether any
``q`` satisfies ``B q <= b``. The conforming behaviour is fixed by
Remark ``rem:hlow-range``: ``h_low = +inf``, propagated and never clamped, with
NO key-length claim. The same rule binds every route to a key length, the
first-order one included: ``cor:keylength-bound`` (b) emits no positive length
from a value that is not finite.

So emptiness is DECIDED here, exactly, over the rationals, and it is decided
AFTER well-formedness and never by the same test. The order is the content of
the frozen case ``ILLFORMED-box-inverted``: an inverted canonical box PASSES the
closed-form emptiness test ``sum q^- <= 1 <= sum q^+`` while denoting the empty
set, so a path that runs that test without first checking ``0 <= q^- <= q^+``
admits data that is not a geometry at all -- and then computes with NEGATIVE
widths.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from certiqs_key.meat_core.acceptance.simplex import (
    LinearProgramStatus,
    solve_standard_form,
)
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    PolytopeData,
    ProtocolDeclaration,
)

#: The two tags of ``statistics/def:taxonomy``,
#: read here as data. "There is no third tag; a consumer presented with any
#: other tag refuses rather than guessing."
SINGLETON = "singleton"
POLYTOPE = "polytope"
GEOMETRY_TAGS: tuple[str, ...] = (SINGLETON, POLYTOPE)

_ZERO = Fraction(0)
_ONE = Fraction(1)


class AcceptanceDefect(StrEnum):
    """Why a declared acceptance set cannot be used, if it cannot.

    A vocabulary of DEFECTS, deliberately separate from the assurance-reason
    vocabulary of :mod:`certiqs_key.meat_core.reasons`: this enum says what is
    wrong with a DECLARATION, and that module says what a RESULT RECORD calls
    it. Mapping one onto the other in code (``_ACCEPTANCE_DEFECT_REASONS`` in
    :mod:`certiqs_key.solvers.frank_wolfe.keyrate`) keeps the two from drifting
    into a single implicit vocabulary.
    """

    #: The tag is outside the taxonomy the two instantiations of Remark
    #: ``rem:acc-side`` cover.
    UNSUPPORTED_GEOMETRY = "unsupported-geometry"
    #: The data is not well formed for the form it claims -- checked FIRST, so
    #: that an inverted canonical box is refused as data rather than reasoned
    #: about as a set.
    ILL_FORMED = "ill-formed"
    #: Well-formed data whose denotation is empty.
    EMPTY = "empty"


@dataclass(frozen=True)
class AcceptanceVerdict:
    """What a declared acceptance set is, and what is wrong with it if anything."""

    defect: AcceptanceDefect | None
    #: A one-sentence statement naming the failed check, for the error a caller
    #: raises or the machine-readable reason it reports.
    detail: str = ""

    @property
    def admissible(self) -> bool:
        """Return whether the declared set may be used."""
        return self.defect is None


@dataclass(frozen=True)
class AcceptanceMinimum:
    """The exact solution of ``min <g, q>`` over a declared polytope.

    All four fields are exact rationals. ``multipliers`` and ``offset`` are the
    ``(u, v)`` of Remark ``rem:acc-side`` (b): ``u >= 0`` with one entry per row
    of ``B`` in the declared row order, ``v`` unrestricted in sign, satisfying
    ``g + B^T u + v >= 0`` componentwise, and ``-<b, u> - v == minimum`` at an
    optimal basis (strong duality). None of that is ASSUMED downstream: the
    caller re-checks the componentwise condition in exact arithmetic on
    the machine numbers it actually uses.
    """

    minimum: Fraction
    argmin: tuple[Fraction, ...]
    multipliers: tuple[Fraction, ...]
    offset: Fraction


@dataclass(frozen=True)
class AcceptanceWitness:
    """A machine-number ``(u, v)`` for Remark ``rem:acc-side`` (b), and its bound.

    The multipliers are the exact optimal ones rounded TOWARDS ZERO, which keeps
    ``u >= 0``; the offset is then raised to the smallest machine number that
    makes ``g + B^T u + v >= 0`` hold EXACTLY on those rounded multipliers.
    Raising ``v`` lowers ``-<b, u> - v``, so the repair is conservative, and it
    costs about one unit in the last place of the bound.
    """

    multipliers: tuple[float, ...]
    offset: float
    #: ``-<b, u> - v``, exactly, on the MACHINE ``u`` and ``v`` above.
    bound: Fraction


# ---------------------------------------------------------------------------
#  Well-formedness, then emptiness. In that order, never the other.
# ---------------------------------------------------------------------------


def polytope_defect(data: PolytopeData) -> str | None:
    """Return the first well-formedness check the data fails, or ``None``.

    Well-formedness is a property of the DATA against the form it claims, and it
    is decided before any set-theoretic question. Three groups of checks:

    * shape -- every row has one entry per element of ``Chat``, ``b`` has one
      entry per row, and every entry is a finite machine number, because a
      non-finite entry is not a rational and no exact decision can be made
      about it;
    * canonical box, when ``box_bounds`` is present -- ``0 <= q^- <= q^+``
      componentwise, the condition Theorem ``thm:geometry-validation`` (iii) of the
      geometry contract is stated under and which the frozen ``ILLFORMED-box-inverted``
      case violates while passing the closed-form emptiness test;
    * agreement -- the declared rows ARE the canonical box rows of that pair
      (Eq. ``eq:boxrows``: row ``i`` is ``+e_i`` at ``q^+(c_i)``, row ``m + i``
      is ``-e_i`` at ``-q^-(c_i)``). Declared data that contradicts itself is a
      defect whichever half is wrong, and this module cannot decide which.
    """
    if data.columns < 1:
        return "the acceptance alphabet is empty, so no polytope is declared on it"
    for index, row in enumerate(data.rows):
        if len(row) != data.columns:
            return (
                f"row {index} of B has {len(row)} columns, but the acceptance "
                f"alphabet has {data.columns}"
            )
        if any(not math.isfinite(value) for value in row):
            return f"row {index} of B carries a value that is not a real number"
    if len(data.rhs) != data.m_row:
        return (
            f"b has {len(data.rhs)} entries but B has {data.m_row} rows; they "
            "are read positionally against each other"
        )
    if any(not math.isfinite(value) for value in data.rhs):
        return "b carries a value that is not a real number"
    if data.box_bounds is None:
        return None
    lower, upper = data.box_bounds
    if len(lower) != data.columns or len(upper) != data.columns:
        return (
            "box_bounds must carry one (q^-, q^+) pair per element of the "
            f"acceptance alphabet, which has {data.columns}"
        )
    if any(not math.isfinite(value) for value in (*lower, *upper)):
        return "box_bounds carries a value that is not a real number"
    for index in range(data.columns):
        if not 0.0 <= lower[index] <= upper[index]:
            return (
                "a canonical box requires 0 <= q^- <= q^+ componentwise; at "
                f"column {index} the declared pair is "
                f"({lower[index]!r}, {upper[index]!r}), so this data is not a "
                "canonical box and no box-shaped reasoning applies to it"
            )
    return _box_rows_defect(data, lower, upper)


def _box_rows_defect(
    data: PolytopeData, lower: Sequence[float], upper: Sequence[float]
) -> str | None:
    """Return why the rows are not the canonical box rows of the pair, or ``None``."""
    size = data.columns
    if data.m_row != 2 * size:
        return (
            f"a canonical box on {size} outcomes has m_row = {2 * size} rows "
            f"(Eq. eq:boxrows), but {data.m_row} are declared"
        )
    for index in range(size):
        cap = data.rows[index]
        floor = data.rows[size + index]
        expected_cap = tuple(1.0 if k == index else 0.0 for k in range(size))
        expected_floor = tuple(-1.0 if k == index else 0.0 for k in range(size))
        if tuple(cap) != expected_cap or data.rhs[index] != upper[index]:
            return (
                f"row {index} is not the canonical cap row of column {index} "
                "(Eq. eq:boxrows: +e_i^T q <= q^+(c_i))"
            )
        if tuple(floor) != expected_floor or data.rhs[size + index] != -lower[index]:
            return (
                f"row {size + index} is not the canonical floor row of column "
                f"{index} (Eq. eq:boxrows: -e_i^T q <= -q^-(c_i))"
            )
    return None


def polytope_contains(data: PolytopeData, point: Sequence[Fraction]) -> bool:
    """Return whether ``point`` is in ``{q >= 0, sum q = 1, B q <= b}``, exactly.

    All three conditions over the rationals, the declared ``B`` and ``b`` read
    as the exact values of their binary64 entries. No tolerance: a point on a
    facet is a member and a point an ulp outside is not.
    """
    if len(point) != data.columns:
        return False
    if any(value < _ZERO for value in point) or sum(point, _ZERO) != _ONE:
        return False
    for row, bound in zip(data.rows, data.rhs, strict=True):
        total = _ZERO
        for coefficient, value in zip(row, point, strict=True):
            if coefficient != 0.0 and value != _ZERO:
                total += Fraction(coefficient) * value
        if total > Fraction(bound):
            return False
    return True


def acceptance_contains_exact(
    declaration: ProtocolDeclaration, point: Mapping[str, Fraction]
) -> bool:
    """Return whether an exact point is in the declared acceptance set.

    Singleton: equality with the declared vector. Polytope:
    :func:`polytope_contains`.
    """
    values = declaration.acceptance_values
    if set(point) != set(values):
        return False
    data = polytope_of(declaration.acceptance_set)
    if data is None:
        return all(
            point[chat] == Fraction(value)
            for chat, value in singleton_frequencies(declaration).items()
        )
    return polytope_contains(data, [point[chat] for chat in values])


def polytope_is_nonempty(data: PolytopeData) -> bool:
    """Return whether the declared polytope has a point, decided exactly.

    The validation predicate of ``statistics`` Definition
    ``def:taxonomy`` verbatim: rational feasibility of
    ``{q >= 0, sum q = 1, B q <= b}``, ALL THREE conditions together. The middle
    one is what the frozen ``INFEAS-rows-contradict-simplex`` case exists for --
    its single row is satisfiable in the non-negative orthant and empty on the
    simplex -- and no closed form is used anywhere here, so the box-shaped test
    that the inverted box passes is never consulted.
    """
    result = solve_standard_form(*_standard_form(data, (_ZERO,) * data.columns))
    return result.status is not LinearProgramStatus.INFEASIBLE


def acceptance_verdict(declaration: ProtocolDeclaration) -> AcceptanceVerdict:
    """Return what is wrong with a declaration's acceptance set, if anything.

    ``req:acceptance-set-admission``: an acceptance set is admitted only when
    the engine decides, exactly on the declared data, that it is an admissible
    acceptance set (``def:admissible-acceptance-set``) -- a geometry tag every
    well-formed datum of which denotes a closed convex subset of the simplex,
    and data well formed for that tag. This decides the tag and a polytope's
    data; a singleton's vector is decided by
    :func:`certiqs_key.meat_core.declaration.validation.validate_acceptance_set`,
    the requirement's ``implements``, which calls this.

    The tag is checked for both geometries. For a ``polytope`` the data is then
    checked for well-formedness and its denotation for emptiness, in that order.

    A ``singleton`` stops at the tag, and the asymmetry is deliberate: its
    validation predicate is a statement about a declared VECTOR -- non-negative,
    summing to one -- which
    :func:`certiqs_key.meat_core.declaration.validation.validate_declaration`
    checks at the boundary, EXACTLY, as it decides every other declared identity
    of def:admissible-declaration. A polytope's emptiness is visible nowhere in its data
    and has to be decided, which is why it is decided here.
    """
    acceptance = declaration.acceptance_set
    if acceptance.geometry not in GEOMETRY_TAGS:
        return AcceptanceVerdict(
            AcceptanceDefect.UNSUPPORTED_GEOMETRY,
            f"acceptance-set geometry {acceptance.geometry!r} is not read by "
            "this implementation. def:admissible-acceptance-set admits any closed "
            "convex "
            "subset of the probability simplex; the tags a declaration may use "
            f"are {list(GEOMETRY_TAGS)}, the two instantiations contract "
            "Remark rem:acc-side certifies. A set fitting neither is refused at "
            "admission, before any solve, and no first-order bound is formed "
            "for it (req:acceptance-geometries); inventing a "
            "tag here would decide something no accepted contract states",
        )
    if acceptance.geometry == SINGLETON:
        return AcceptanceVerdict(None)
    data = acceptance.polytope
    if data is None:
        return AcceptanceVerdict(
            AcceptanceDefect.ILL_FORMED,
            "the 'polytope' geometry carries no (m_row, B, b) data",
        )
    defect = polytope_defect(data)
    if defect is not None:
        return AcceptanceVerdict(
            AcceptanceDefect.ILL_FORMED,
            f"the declared 'polytope' acceptance set is not well formed: {defect}",
        )
    if not polytope_is_nonempty(data):
        return AcceptanceVerdict(
            AcceptanceDefect.EMPTY,
            "the declared 'polytope' acceptance set is well formed and its "
            "denotation {q >= 0, sum q = 1, B q <= b} is EMPTY. An empty set "
            "satisfies def:admissible-acceptance-set and makes Eq. eq:bacc-def "
            "vacuous, so "
            "no beta_acc is derivable from it and no certificate may be "
            "emitted; the conforming h_low is +inf with no key-length claim "
            "(Remark rem:hlow-range, Requirement req:infinite-value)",
        )
    return AcceptanceVerdict(None)


# ---------------------------------------------------------------------------
#  The linear minimization, and the witness that certifies it.
# ---------------------------------------------------------------------------


def acceptance_minimum(
    surrogate: Sequence[float], data: PolytopeData
) -> AcceptanceMinimum | None:
    """Return the exact ``min <g, q>`` over the declared polytope, with a witness.

    The right-hand side of Eq. ``eq:bacc-def`` for instantiation (b). ``None``
    when the set is empty or no basis was reached -- the caller fails closed
    rather than substituting a number, because every inadmissible alternative is
    locally reasonable and wrong: ``-inf`` writes a value the contract does not
    define, the minimum over the whole simplex answers about a LARGER set, and
    repairing the rows changes a declaration nobody accepted.
    """
    if len(surrogate) != data.columns:
        raise ValueError(
            f"the surrogate has {len(surrogate)} entries but the polytope has "
            f"{data.columns} columns"
        )
    if any(not math.isfinite(value) for value in surrogate):
        return None
    cost = tuple(Fraction(value) for value in surrogate)
    result = solve_standard_form(*_standard_form(data, cost))
    if result.status is not LinearProgramStatus.OPTIMAL:
        return None
    if result.dual is None or result.objective is None:  # pragma: no cover
        return None
    return AcceptanceMinimum(
        minimum=result.objective,
        argmin=result.primal[: data.columns],
        # The sign identification of Remark rem:acc-side (b) against the dual of
        # min <c,x> s.t. Ax = d, x >= 0: with row 0 the normalization and rows
        # 1..m_row the declared inequalities, u = -y_{1..m} (non-negative
        # because those rows carry a slack column) and v = -y_0 (unrestricted,
        # the normalization being an equality). Then the dual constraint on a q
        # column reads g + B^T u + v >= 0 and the dual objective is
        # -<b, u> - v, which are the remark's two displayed formulas.
        multipliers=tuple(-value for value in result.dual[1:]),
        offset=-result.dual[0],
    )


def acceptance_witness(
    surrogate: Sequence[float], data: PolytopeData
) -> AcceptanceWitness | None:
    """Return a MACHINE-NUMBER ``(u, v)`` admissible for Remark ``rem:acc-side`` (b).

    The exact optimal multipliers are not machine numbers in general, and
    rounding them would break the componentwise condition exactly where it is
    tight -- which for a canonical box is every coordinate at once. So the
    multipliers are rounded towards zero, which preserves ``u >= 0``, and then
    ``v`` is recomputed as the smallest machine number for which
    ``g + B^T u + v >= 0`` holds EXACTLY on the rounded multipliers.

    The result is admissible by construction. It is verified again anyway, by
    :func:`certiqs_key.meat_core.acceptance.bacc.beta_acc_polytope`, because
    that componentwise test is what certifies a number and a construction bug
    must not be able to walk around it.
    """
    optimum = acceptance_minimum(surrogate, data)
    if optimum is None:
        return None
    multipliers: list[float] = []
    for value in optimum.multipliers:
        rounded = float_below(value if value > _ZERO else _ZERO)
        if rounded is None or not math.isfinite(rounded):
            return None
        multipliers.append(rounded)
    exact_u = tuple(Fraction(value) for value in multipliers)
    shortfall: Fraction | None = None
    for column in range(data.columns):
        total = Fraction(surrogate[column])
        for index, row in enumerate(data.rows):
            total = total + Fraction(row[column]) * exact_u[index]
        if shortfall is None or total < shortfall:
            shortfall = total
    if shortfall is None:  # pragma: no cover - columns >= 1 after well-formedness
        return None
    offset = float_above(-shortfall)
    if offset is None or not math.isfinite(offset):
        return None
    bound = -Fraction(offset)
    for index, value in enumerate(exact_u):
        bound = bound - Fraction(data.rhs[index]) * value
    return AcceptanceWitness(tuple(multipliers), offset, bound)


def polytope_minimizer(
    surrogate: Sequence[float], data: PolytopeData
) -> tuple[float, ...] | None:
    """Return a minimizer of ``<g, q>`` over the polytope, as machine numbers.

    The Frank-Wolfe vertex. A minimizer is a VERTEX of the acceptance set, so
    ties leave the value unique and the point not: the frozen ``PMIN-box-tie``
    case records both endpoints of a segment argmin and notes that "a test that
    asserts the ARGMIN rather than the VALUE pins the sort's stability, which no
    contract fixes". Nothing downstream reads which endpoint comes back.
    """
    point = polytope_minimizer_exact(surrogate, data)
    if point is None:
        return None
    return tuple(float(value) for value in point)


def polytope_minimizer_exact(
    surrogate: Sequence[float], data: PolytopeData
) -> tuple[Fraction, ...] | None:
    """Return the Frank-Wolfe vertex of :func:`polytope_minimizer`, EXACTLY.

    Remark ``rem:acc-side`` (beta): the acceptance-side update moves toward "a
    vertex computed exactly over the rationals", and a driver that forms
    ``q_t`` on the exact island needs that vertex itself, not its binary64
    rounding, which need not lie in the set. :func:`polytope_minimizer` is this
    point rounded to the nearest machine numbers, coordinate by coordinate.
    """
    optimum = acceptance_minimum(surrogate, data)
    if optimum is None:
        return None
    return optimum.argmin


def polytope_coordinate_maximizers(
    data: PolytopeData,
) -> tuple[tuple[Fraction, ...], ...] | None:
    """Return one maximizer of each coordinate over the polytope, exactly."""
    points: list[tuple[Fraction, ...]] = []
    for index in range(data.columns):
        cost = tuple(
            -_ONE if column == index else _ZERO for column in range(data.columns)
        )
        result = solve_standard_form(*_standard_form(data, cost))
        if result.status is not LinearProgramStatus.OPTIMAL:
            return None
        points.append(result.primal[: data.columns])
    return tuple(points)


def polytope_support_and_start(
    data: PolytopeData,
) -> tuple[tuple[int, ...], tuple[float, ...]] | None:
    """Compute exact support and the usual averaged start from one LP batch.

    This is solve-local reuse of the same coordinate maximizers used separately
    by ``polytope_support`` and ``polytope_relative_interior_point``. Support is
    decided on the exact rational maxima, never on the rounded starting point.
    The average uses the same order and float conversion as the existing start.
    """
    prepared = polytope_support_and_exact_start(data)
    if prepared is None:
        return None
    support, start = prepared
    return support, tuple(float(value) for value in start)


def polytope_support_and_exact_start(
    data: PolytopeData,
) -> tuple[tuple[int, ...], tuple[Fraction, ...]] | None:
    """Return :func:`polytope_support_and_start` with the start kept EXACT.

    Remark ``rem:acc-side`` (alpha): the acceptance-side iterate starts at an
    exact rational point of the set. The average of the coordinate maximizers
    is one, and its binary64 rounding in general is not (a division by the
    column count is not dyadic), so a driver forming ``q_t`` on the exact
    island starts here and evaluates at the rounding.
    """
    maximizers = polytope_coordinate_maximizers(data)
    if maximizers is None:
        return None
    support = tuple(
        index for index, point in enumerate(maximizers) if point[index] > _ZERO
    )
    return support, _average(maximizers, data.columns)


def _average(
    maximizers: Sequence[Sequence[Fraction]], columns: int
) -> tuple[Fraction, ...]:
    """Return the exact average of the coordinate maximizers, coordinatewise."""
    size = Fraction(columns)
    return tuple(
        sum((point[column] for point in maximizers), _ZERO) / size
        for column in range(columns)
    )


def polytope_coordinate_minima(data: PolytopeData) -> tuple[Fraction, ...] | None:
    """Return ``min_q q(c)`` over the polytope for every coordinate, exactly.

    One linear program per coordinate on the same standard form
    :func:`polytope_coordinate_maximizers` uses, with the opposite sign of cost.
    ``None`` when any of them reaches no optimal basis -- the empty set, or data
    a caller built in memory and never validated -- so that the caller fails
    closed instead of substituting a number for a minimum that does not exist.

    THE DECLARED ``q^-`` IS NOT THIS NUMBER, even for a canonical box, which is
    why the box record is not consulted here: the box of ``TOY-8-T-POLY``
    declares ``q^- = (1/4, 1/8)`` while the minima over its denotation are
    ``(1/4, 1/4)``, because the normalization ``sum q = 1`` cuts the box down to
    a segment. Reading a floor off ``box_bounds`` would answer about a larger
    set than the one declared.
    """
    minima: list[Fraction] = []
    for index in range(data.columns):
        cost = tuple(
            _ONE if column == index else _ZERO for column in range(data.columns)
        )
        result = solve_standard_form(*_standard_form(data, cost))
        if result.status is not LinearProgramStatus.OPTIMAL:
            return None
        if result.objective is None:  # pragma: no cover - optimal carries a value
            return None
        minima.append(result.objective)
    return tuple(minima)


def polytope_support(data: PolytopeData) -> tuple[int, ...]:
    """Return the MINIMAL acceptance support of the polytope, as column indices.

    Eq. ``eq:chacc-def`` (Definition ``def:first-order-setting``): the
    acceptance support ``Chat_acc`` is the union of the supports of every ``q``
    in ``AcceptSet``. That union is exactly ``{c : max_q q(c) > 0}``, one linear
    program per coordinate, and it is the choice taken here because it is the
    smallest set the certificate has to carry.

    Returning a superset would be conforming too -- the frozen
    ``PMIN-box-support-superset`` case is built to say so, and to say that both
    choices give the same minimum -- but a smaller ``Chat_acc`` means fewer
    hypotheses to certify, not more.
    """
    maximizers = polytope_coordinate_maximizers(data)
    if maximizers is None:  # pragma: no cover - an empty set is refused upstream
        return ()
    return tuple(
        index for index, point in enumerate(maximizers) if point[index] > _ZERO
    )


def polytope_relative_interior_point(data: PolytopeData) -> tuple[float, ...] | None:
    """Return a point of the polytope, positive on every coordinate that can be.

    The average of one maximizer per coordinate. It lies in the set by
    convexity, and for each coordinate whose maximum over the set is positive
    the average is positive too, because every point of the set is
    non-negative -- so the returned point is strictly positive exactly on the
    minimal acceptance support.

    That property is what the Frank-Wolfe start needs and a vertex would not
    give: Corollary ``cor:full-gradient`` is stated at a point with
    ``q(chat) > 0``, so starting at a vertex would ask for a gradient where the
    ``q``-derivative is ``-inf``. Steps are capped strictly below one
    thereafter, so a coordinate that starts positive stays positive.
    """
    point = polytope_relative_interior_point_exact(data)
    if point is None:
        return None
    return tuple(float(value) for value in point)


def polytope_relative_interior_point_exact(
    data: PolytopeData,
) -> tuple[Fraction, ...] | None:
    """Return the point of :func:`polytope_relative_interior_point`, EXACTLY.

    It is a member of the set by convexity; its binary64 rounding need not be
    (Remark ``rem:acc-side`` (alpha)).
    """
    maximizers = polytope_coordinate_maximizers(data)
    if maximizers is None:
        return None
    return _average(maximizers, data.columns)


# ---------------------------------------------------------------------------
#  Declaration-level helpers.
# ---------------------------------------------------------------------------


def singleton_frequencies(declaration: ProtocolDeclaration) -> dict[str, float]:
    """Return the ``q*`` of a ``singleton`` acceptance set, keyed by ``chat``."""
    return dict(
        zip(
            declaration.acceptance_values,
            declaration.acceptance_set.frequencies,
            strict=True,
        )
    )


def polytope_of(acceptance: AcceptanceSet) -> PolytopeData | None:
    """Return the polytope data of a ``polytope`` acceptance set, or ``None``."""
    if acceptance.geometry != POLYTOPE:
        return None
    return acceptance.polytope


def minimal_acceptance_support(declaration: ProtocolDeclaration) -> tuple[str, ...]:
    """Return the acceptance support ``Chat_acc`` of Eq. ``eq:chacc-def``.

    Singleton: the support of the one declared vector. Polytope: the coordinates
    whose maximum over the set is positive. Both are the union of the supports
    of the members, which is what the definition calls the minimal choice.
    """
    values = declaration.acceptance_values
    data = polytope_of(declaration.acceptance_set)
    if data is None:
        frequencies = singleton_frequencies(declaration)
        return tuple(chat for chat in values if frequencies[chat] > 0.0)
    return tuple(values[index] for index in polytope_support(data))


def acceptance_floors(declaration: ProtocolDeclaration) -> dict[str, float] | None:
    """Return a floor on ``q(chat)`` over the WHOLE acceptance set, per ``chat``.

    The quantity Theorem ``thm:oracle`` hypothesis (H1) is stated over: "there
    is ``p_0 > 0`` with ``q(chat) >= p_0`` for every ``q`` in ``AcceptSet`` and
    every ``chat`` in ``Chat_key``". Singleton: the set is one point, so the
    declared vector IS the minimum and the two readings coincide -- which is why
    the singleton-only implementation this widens was never a different rule,
    only the special case. Polytope: one linear program per coordinate.

    Each polytope floor is rounded DOWNWARD, the sound direction: what is
    returned must satisfy ``q(chat) >= floor`` for every member of the set, and
    rounding upward could claim a floor no member meets. A smaller floor is a
    weaker (H1) and never an unsound one.

    ``None`` when no floor is derivable -- an empty or unreachable polytope, or
    a column count that disagrees with the acceptance alphabet. The caller fails
    closed with its own typed refusal rather than seeing an untyped exception
    from a mismatched zip; a declaration parsed from a bundle cannot reach the
    second case, whose ``columns`` is taken from the alphabet itself.
    """
    values = declaration.acceptance_values
    data = polytope_of(declaration.acceptance_set)
    if data is None:
        return singleton_frequencies(declaration)
    minima = polytope_coordinate_minima(data)
    if minima is None or len(minima) != len(values):
        return None
    floors: dict[str, float] = {}
    for chat, value in zip(values, minima, strict=True):
        rounded = float_below(value)
        if rounded is None:  # pragma: no cover - declared data is bounded
            return None
        floors[chat] = rounded
    return floors


def acceptance_start(declaration: ProtocolDeclaration) -> dict[str, float]:
    """Return a member of the declared acceptance set to start a run from."""
    data = polytope_of(declaration.acceptance_set)
    if data is None:
        return singleton_frequencies(declaration)
    point = polytope_relative_interior_point(data)
    if point is None:  # pragma: no cover - an empty set is refused upstream
        raise ValueError(
            "the declared polytope acceptance set has no point to start from; "
            "an empty acceptance set is refused before an oracle is built"
        )
    return dict(zip(declaration.acceptance_values, point, strict=True))


def acceptance_start_exact(declaration: ProtocolDeclaration) -> dict[str, Fraction]:
    """Return the start of :func:`acceptance_start` as exact rationals.

    Singleton: the declared vector, whose binary64 entries are exact dyadic
    rationals. Polytope: the exact average of the coordinate maximizers, of
    which :func:`acceptance_start` is the rounding.
    """
    data = polytope_of(declaration.acceptance_set)
    if data is None:
        return {
            chat: Fraction(value)
            for chat, value in singleton_frequencies(declaration).items()
        }
    point = polytope_relative_interior_point_exact(data)
    if point is None:  # pragma: no cover - an empty set is refused upstream
        raise ValueError(
            "the declared polytope acceptance set has no point to start from; "
            "an empty acceptance set is refused before an oracle is built"
        )
    return dict(zip(declaration.acceptance_values, point, strict=True))


def acceptance_minimizer_exact(
    declaration: ProtocolDeclaration, surrogate: Mapping[str, float]
) -> dict[str, Fraction]:
    """Return the minimizer of :func:`acceptance_minimizer` as exact rationals."""
    values = declaration.acceptance_values
    data = polytope_of(declaration.acceptance_set)
    if data is None:
        return {
            chat: Fraction(value)
            for chat, value in singleton_frequencies(declaration).items()
        }
    point = polytope_minimizer_exact([surrogate[chat] for chat in values], data)
    if point is None:
        raise ValueError(
            "no minimizer of the declared polytope acceptance set was reached; "
            "an empty or ill-formed acceptance set is refused before an oracle "
            "is built, and a non-finite cost is a defect upstream"
        )
    return dict(zip(values, point, strict=True))


def acceptance_minimizer(
    declaration: ProtocolDeclaration, surrogate: Mapping[str, float]
) -> dict[str, float]:
    """Return a minimizer of the linear cost ``surrogate`` over the acceptance set."""
    values = declaration.acceptance_values
    data = polytope_of(declaration.acceptance_set)
    if data is None:
        return singleton_frequencies(declaration)
    point = polytope_minimizer([surrogate[chat] for chat in values], data)
    if point is None:
        raise ValueError(
            "no minimizer of the declared polytope acceptance set was reached; "
            "an empty or ill-formed acceptance set is refused before an oracle "
            "is built, and a non-finite cost is a defect upstream"
        )
    return dict(zip(values, point, strict=True))


# ---------------------------------------------------------------------------
#  Internals.
# ---------------------------------------------------------------------------


def _standard_form(
    data: PolytopeData, cost: Sequence[Fraction]
) -> tuple[list[list[Fraction]], list[Fraction], list[Fraction]]:
    """Return ``min <c, x>`` over ``{A x = d, x >= 0}`` for the declared polytope.

    The variables are ``(q, s)`` with one slack per declared row, so that the
    denotation ``{q >= 0, sum q = 1, B q <= b}`` becomes an equality system.
    Row ``0`` is the normalization and rows ``1..m_row`` are the declared
    inequalities, in the declared order -- which is the order the multipliers
    come back in and therefore the order of ``u``.
    """
    size = data.columns
    rows_count = data.m_row
    matrix: list[list[Fraction]] = [
        [*(_ONE for _ in range(size)), *(_ZERO for _ in range(rows_count))]
    ]
    rhs: list[Fraction] = [_ONE]
    for index, row in enumerate(data.rows):
        matrix.append(
            [
                *(Fraction(value) for value in row),
                *(
                    _ONE if position == index else _ZERO
                    for position in range(rows_count)
                ),
            ]
        )
        rhs.append(Fraction(data.rhs[index]))
    return matrix, rhs, [*cost, *(_ZERO for _ in range(rows_count))]


def float_below(value: Fraction) -> float | None:
    """Return the largest machine number provably ``<= value``, or ``None``.

    ``None`` where no machine number stands for the rational at all, which is
    the overflow case; the caller then has no witness and fails closed.

    PUBLIC because this pair is the repository's one direction-bearing
    rounding from an exact rational to a machine number, and the statistics
    docking adapter (``meat_core/docking_statistics.py``) shares it rather than
    carrying a third copy, so it needs a public name at the boundary that uses
    it.

    NO INTERVAL-ARITHMETIC EXTRA IS INVOLVED, and this package must run
    WITHOUT any such extra: the acceptance-set linear minimization is on the
    ESTIMATE path too, where no estimate-tier output depends on an
    optional extra. The direction is checked in exact arithmetic.
    """
    try:
        candidate = float(value)
    except OverflowError:  # pragma: no cover - declared data is bounded
        return None
    while candidate > -math.inf and Fraction(candidate) > value:
        candidate = math.nextafter(candidate, -math.inf)
    return candidate


def float_above(value: Fraction) -> float | None:
    """Return the smallest machine number provably ``>= value``, or ``None``."""
    try:
        candidate = float(value)
    except OverflowError:  # pragma: no cover - declared data is bounded
        return None
    while candidate < math.inf and Fraction(candidate) < value:
        candidate = math.nextafter(candidate, math.inf)
    return candidate
