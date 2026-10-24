"""An exact rational simplex, for the acceptance-set linear program.

Contract Remark ``rem:acc-side`` states Eq. ``eq:bacc-def`` as an INPUT
OBLIGATION rather than an algorithm -- "whether it is computable is a property
of the declared representation" -- so nothing here is claimed to be part of the
contract's mathematics. What this module is, is the machinery that lets the
implementation MEET that obligation for the declared ``polytope``
representation, and it produces two things at once:

* the primal minimizer of a linear cost over ``{q >= 0, sum q = 1, B q <= b}``,
  which is what the Frank-Wolfe driver's acceptance-side direction needs;
* the simplex multipliers, which -- after the sign identification worked out in
  :mod:`certiqs_key.meat_core.acceptance.geometry` -- are exactly the ``(u, v)`` pair
  Remark ``rem:acc-side`` (b) asks for.

NOTHING HERE IS TRUSTED BY THE CERTIFICATE
==========================================
The certified acceptance-side bound never rests on this solver being right.
``frank-wolfe/rem:acc-side`` (b) certifies a number by the COMPONENTWISE test
``g + B^T u + v >= 0``, and that test is applied to whatever this module
returns, in exact arithmetic, by
:func:`certiqs_key.meat_core.acceptance.bacc.beta_acc_polytope`. A wrong or merely
suboptimal witness therefore costs tightness or fails closed; it cannot make an
unsound bound certified. The frozen registry entry ``O-POLYTOPE-ACC-MINIMUM``
says the same thing from the other side: "nothing here licenses feeding a
self-computed minimum to the certificate WITHOUT the admissibility check".

WHY EXACT RATIONALS
===================
Two reasons, and only the second is about the certificate. Emptiness of a
declared acceptance set is a DECISION -- an empty set satisfies Definition
def:admissible-acceptance-set, makes Eq. ``eq:bacc-def`` vacuous, and must be refused
rather than answered -- and a floating-point feasibility test decides it wrongly near
the boundary. And a witness assembled from rounded arithmetic would fail the
componentwise test for no better reason than rounding. :class:`fractions.
Fraction` is exact and needs no optional substrate, so the ESTIMATE path keeps
working without any interval-arithmetic extra.

THE PIVOT RULE IS BLAND'S
=========================
Degenerate vertices are the normal case here, not the exception: a canonical box
whose floors already carry the whole normalization has an argmin face that is a
single point reached with zero residual mass (the frozen case
``PMIN-box-support-superset``), and a tied cost vector has an argmin face with
several vertices (``PMIN-box-tie``). Bland's rule terminates on both without a
perturbation, an anti-cycling clock or a tolerance.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

_ZERO = Fraction(0)
_ONE = Fraction(1)


class LinearProgramStatus(StrEnum):
    """How a linear program ended."""

    #: An optimal basis was reached.
    OPTIMAL = "optimal"
    #: The constraint system has no solution: phase one ended above zero.
    INFEASIBLE = "infeasible"
    #: The objective decreases without bound along a feasible ray.
    UNBOUNDED = "unbounded"
    #: An artificial variable could not be driven out of the basis, so the row
    #: set is linearly dependent and no basis of the original columns exists.
    DEGENERATE = "degenerate"


@dataclass(frozen=True)
class LinearProgramResult:
    """The outcome of ``min <c, x>`` over ``{A x = d, x >= 0}``, exactly."""

    status: LinearProgramStatus
    #: The optimal ``x``, empty unless the status is ``optimal``.
    primal: tuple[Fraction, ...] = ()
    #: ``<c, x>`` at that point.
    objective: Fraction | None = None
    #: The simplex multipliers ``y`` of the ORIGINAL row system, satisfying
    #: ``A^T y <= c`` and ``<d, y> = <c, x>``. ``None`` when no basis of the
    #: original columns was reached.
    dual: tuple[Fraction, ...] | None = None


def solve_standard_form(
    matrix: Sequence[Sequence[Fraction]],
    rhs: Sequence[Fraction],
    cost: Sequence[Fraction],
) -> LinearProgramResult:
    """Return the exact optimum of ``min <cost, x>`` over ``A x = rhs, x >= 0``.

    Two phases. Phase one drives a full set of artificial variables to zero and
    decides feasibility; phase two optimizes over the columns of ``A`` alone.
    The multipliers are read off the final basis rather than off the tableau, so
    the row sign normalization phase one needs leaves no trace in them.

    Raises:
        ValueError: if the shapes disagree. A caller that builds the system from
            declared data has already checked them; this is the last guard.
    """
    rows = len(rhs)
    columns = len(cost)
    if any(len(row) != columns for row in matrix) or len(matrix) != rows:
        raise ValueError(
            f"the constraint matrix must be {rows} x {columns} to match the "
            "right-hand side and the cost vector"
        )
    body = [[Fraction(value) for value in row] for row in matrix]
    targets = [Fraction(value) for value in rhs]
    for index in range(rows):
        # Phase one needs a non-negative right-hand side to start from the
        # artificial basis. Negating a row is an invertible row operation: it
        # changes neither the feasible set nor which column sets are bases, so
        # the multipliers extracted at the end are those of the ORIGINAL rows.
        if targets[index] < _ZERO:
            body[index] = [-value for value in body[index]]
            targets[index] = -targets[index]

    width = columns + rows
    tableau = [
        [
            *body[index],
            *(_ONE if position == index else _ZERO for position in range(rows)),
            targets[index],
        ]
        for index in range(rows)
    ]
    basis = [columns + index for index in range(rows)]

    phase_one = [*(_ZERO for _ in range(columns)), *(_ONE for _ in range(rows))]
    _optimize(tableau, basis, phase_one, tuple(range(width)))
    residual = _ZERO
    for index in range(rows):
        if basis[index] >= columns:
            residual = residual + tableau[index][width]
    if residual > _ZERO:
        return LinearProgramResult(LinearProgramStatus.INFEASIBLE)

    for index in range(rows):
        if basis[index] < columns:
            continue
        for column in range(columns):
            if tableau[index][column] != _ZERO:
                _pivot(tableau, basis, index, column)
                break
    if any(entry >= columns for entry in basis):
        # Only reachable when the row system is linearly dependent, which the
        # acceptance-set program never is: its slack columns are an identity
        # block on every row but the normalization, and that row is the only one
        # with a nonzero entry in no slack column.
        return LinearProgramResult(LinearProgramStatus.DEGENERATE)

    phase_two = [*cost, *(_ZERO for _ in range(rows))]
    if not _optimize(tableau, basis, phase_two, tuple(range(columns))):
        return LinearProgramResult(LinearProgramStatus.UNBOUNDED)

    primal = [_ZERO] * columns
    for index in range(rows):
        primal[basis[index]] = tableau[index][width]
    objective = _ZERO
    for column in range(columns):
        objective = objective + cost[column] * primal[column]
    return LinearProgramResult(
        LinearProgramStatus.OPTIMAL,
        tuple(primal),
        objective,
        _multipliers(matrix, cost, basis),
    )


def _optimize(
    tableau: list[list[Fraction]],
    basis: list[int],
    cost: Sequence[Fraction],
    allowed: Sequence[int],
) -> bool:
    """Pivot to optimality under Bland's rule; return ``False`` if unbounded.

    ``allowed`` must be ASCENDING: Bland's rule is "the least eligible index",
    and it is what rules out cycling on the degenerate vertices this program
    produces routinely.
    """
    width = len(cost)
    while True:
        entering = _entering_column(tableau, basis, cost, allowed)
        if entering is None:
            return True
        leaving: int | None = None
        best: Fraction | None = None
        for row in range(len(basis)):
            coefficient = tableau[row][entering]
            if coefficient <= _ZERO:
                continue
            ratio = tableau[row][width] / coefficient
            if best is None or ratio < best:
                best, leaving = ratio, row
            elif ratio == best and leaving is not None and basis[row] < basis[leaving]:
                leaving = row
        if leaving is None:
            return False
        _pivot(tableau, basis, leaving, entering)


def _entering_column(
    tableau: Sequence[Sequence[Fraction]],
    basis: Sequence[int],
    cost: Sequence[Fraction],
    allowed: Sequence[int],
) -> int | None:
    """Return the least allowed column of negative reduced cost, or ``None``."""
    multipliers = [cost[column] for column in basis]
    for column in allowed:
        if column in basis:
            continue
        reduced = cost[column]
        for row, factor in enumerate(multipliers):
            if factor != _ZERO:
                reduced = reduced - factor * tableau[row][column]
        if reduced < _ZERO:
            return column
    return None


def _pivot(
    tableau: list[list[Fraction]], basis: list[int], row: int, column: int
) -> None:
    """Make ``column`` basic in ``row`` by exact Gauss-Jordan elimination."""
    divisor = tableau[row][column]
    scaled = [value / divisor for value in tableau[row]]
    tableau[row] = scaled
    for index, other in enumerate(tableau):
        if index == row:
            continue
        factor = other[column]
        if factor != _ZERO:
            tableau[index] = [
                value - factor * pivot
                for value, pivot in zip(other, scaled, strict=True)
            ]
    basis[row] = column


def _multipliers(
    matrix: Sequence[Sequence[Fraction]],
    cost: Sequence[Fraction],
    basis: Sequence[int],
) -> tuple[Fraction, ...] | None:
    """Return ``y`` with ``B^T y = c_B``, on the ORIGINAL (unnegated) rows.

    At an optimal basis this ``y`` satisfies ``A^T y <= c`` -- that is what
    "no column has negative reduced cost" says -- and ``<rhs, y>`` equals the
    primal optimum, which is strong duality. Both facts are re-established
    downstream rather than assumed: the acceptance witness is checked
    componentwise in exact arithmetic before any certified number is built from
    it.
    """
    size = len(basis)
    system = [
        [matrix[row][basis[position]] for row in range(size)] + [cost[basis[position]]]
        for position in range(size)
    ]
    return _solve_exactly(system, size)


def _solve_exactly(
    system: list[list[Fraction]], size: int
) -> tuple[Fraction, ...] | None:
    """Return the solution of an augmented square system, or ``None`` if singular."""
    for column in range(size):
        pivot_row = next(
            (row for row in range(column, size) if system[row][column] != _ZERO), None
        )
        if pivot_row is None:  # pragma: no cover - a basis matrix is invertible
            return None
        system[column], system[pivot_row] = system[pivot_row], system[column]
        divisor = system[column][column]
        system[column] = [value / divisor for value in system[column]]
        for row in range(size):
            if row == column:
                continue
            factor = system[row][column]
            if factor != _ZERO:
                system[row] = [
                    value - factor * pivot
                    for value, pivot in zip(system[row], system[column], strict=True)
                ]
    return tuple(system[row][size] for row in range(size))
