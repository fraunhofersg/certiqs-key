"""The physics-blind ``LinearOracle`` protocol and its problem data.

spec/architecture.md 7.3: "All SDP linear minimization is behind an internal
``LinearOracle`` protocol. **Physics-blind.** The oracle receives sector-block
Choi data, constraint operators, and a linear cost -- not protocol names, POVM
labels, or squashing metadata."

The problem below is that and nothing more::

    minimize    sum_s <C_s, J_s>
    subject to  J_s >= 0                            for every block s
                the declared COUPLING constraint    (one of two, below)
                sum_s tr[(G_j x H_{k,s}) J_s] bowtie_k  t_j     for each row

The coupling constraint is not optional and is not passed in as data: it is
what binds the blocks into one variable at all, and every declared block is
coupled by it. It comes in exactly TWO forms, which lem:choi-marginal keeps
apart and this protocol keeps apart with it (:class:`Coupling`)::

    input_identity   sum_s tr_{Q_s} J_s = 1_{A_0}    Eq. eq:choi-feas
    unit_trace       sum_s tr J_s       = 1          Eq. eq:choi-feas-un

The second is NOT the first with ``W_tau = 1_A`` substituted. Definition
``def:untrusted-choi`` (b) is explicit: that substitution gives
``sum_s tr_{Q_s} omega_s = 1_A``, an infeasible condition and the operator form
the licence does not supply. Encoding them as two enum members rather than one
formula with a substituted matrix is what makes the mistake unexpressible here.

Constraint ROWS are typed the same way. An operator row (trusted-source mode)
carries a Hermitian ``rhs`` on ``A`` and becomes one real equation per element
of a Hermitian basis of that space, with a matrix slack for an inequality; a
scalar row (untrusted-source mode) carries a real ``rhs`` and is one real
equation with a scalar slack. :func:`row_equations` performs that reduction
once, in the physics-blind language of ``(input operator, target)`` pairs, so
that a backend adapter never has to know which mode produced its data.

Block sizes are ``input_dim * block_dims[s]`` with the INPUT factor first,
which is the ``choi_ordering`` convention of the conventions. In
untrusted-source mode the "input factor" is the ``A`` factor of ``omega_s``
itself, and the same convention (``A`` first, ``subsystem_order``) applies.

An oracle returns an extreme point together with diagnostics and, where the
backend has one, its dual (:class:`OracleDual`). Nothing an oracle reports can
promote a result: "QICS status and gap are not a certificate"
(spec/architecture.md 7.4), and no tier depends on what a solver says about its
own solution. The point serves the search; the dual is a CANDIDATE from which
the feasible side of a bracket is verified in exact arithmetic
(``meat-core/frank-wolfe/req:verified-feasible-side``), whatever the status.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

import numpy as np
import numpy.typing as npt

from certiqs_key.domain.manifest import ConstraintRelation
from certiqs_key.meat_core.errors import MeatError
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.solvers.capabilities.probe import OracleCapabilities


class OracleFailure(MeatError):
    """The linear oracle did not return a usable extreme point.

    Slater or infeasibility reports from a backend are oracle failures, and
    spec/architecture.md 7.4 keeps them distinct from the support-face
    rejections of spec/architecture.md 7.2: a failure here says the subproblem could
    not be
    solved, not that the iterate left its face.

    ``status`` is the solution status the backend reported where the failure
    is a status it does not accept (``None`` for every other failure: a return
    beyond the repair window, a missing or failing spectral backend), and
    ``infeasible`` says whether that status is the backend's verdict that the
    feasible set is EMPTY, which is ``def:admissible-declaration`` (vii)
    failing. The backend that raises decides both, since only it knows what its
    status words mean. A status that is no such verdict asserts no optimality,
    and :attr:`unsolved` names that case: at a portfolio checkpoint the
    bracket is then formed with the multipliers the solves left (``dual``, or
    zero) instead of the run stopping
    (:func:`~certiqs_key.solvers.assessment.assess_candidate`). Neither the
    return nor its status withdraws an iterate (``req:first-order-withdrawal``).
    """

    def __init__(
        self,
        message: str,
        *,
        status: str | None = None,
        infeasible: bool = False,
        dual: OracleDual | None = None,
    ) -> None:
        """Keep the backend's status, its verdict and its dual beside the message."""
        super().__init__(message)
        #: The backend's status word, where a status was the failure.
        self.status = status
        #: Whether that status is the backend's empty-feasible-set verdict.
        self.infeasible = infeasible
        #: The dual the backend returned for the unsolved solve, where it is
        #: finite (frank-wolfe/req:verified-feasible-side (ii): any multipliers
        #: give a bound, whatever the status), else ``None``.
        self.dual = dual

    @property
    def unsolved(self) -> bool:
        """Whether the backend reported a status that is no infeasibility verdict.

        Such a return asserts nothing about the minimum, neither optimality nor
        emptiness: the subproblem was left unsolved at this cost.
        """
        return self.status is not None and not self.infeasible


@dataclass(frozen=True)
class AffineRow:
    """One affine condition on the Choi blocks, in either of its two types.

    ``blocks[s]`` is the operator ``H_{k,s}`` on block ``s``; ``relation`` is
    the declared relation.

    ``rhs`` carries the TYPE. A Hermitian matrix is an OPERATOR row -- the
    trusted-source-mode entry of contract Eq. ``eq:choi-feas``, compared on
    ``A`` -- and ``congruence``, when given, is applied to the left-hand side
    before the comparison, carrying the ``W_tau`` conjugation without the oracle
    having to know what ``W_tau`` is. A real number is a SCALAR row -- the
    untrusted-source-mode entry of Eq. ``eq:choi-feas-un``, a comparison of real
    numbers (Definition ``def:homog`` (b)) -- and no congruence is admissible
    there, because there is no operator to conjugate.
    """

    blocks: Mapping[str, Matrix]
    relation: ConstraintRelation
    rhs: Matrix | float
    congruence: Matrix | None = None

    @property
    def is_scalar(self) -> bool:
        """Return whether this is a scalar row (untrusted-source mode)."""
        return not isinstance(self.rhs, np.ndarray)

    @property
    def slack_dim(self) -> int:
        """Return the dimension of the slack an inequality of this row needs."""
        return 1 if self.is_scalar else int(np.asarray(self.rhs).shape[0])


@dataclass(frozen=True)
class GeneralOperatorRow:
    """One row whose coefficient is a FULL operator per block, not ``G (x) H_s``.

    NEW WITH THE GENERAL FORMAT, and it exists because ``eq:partylocal-entry``
    compares an operator on "the systems of ``omega`` other than ``Q_{f_k}``"
    -- ``A`` and the other measured factors -- so its conjugated Choi row
    (``thm:choi``, the general format) entangles the Choi input register with
    the other factors' blocks. No product ``G (x) H_s`` can express that, which
    is the whole reason for a second row type; a caller with a row of the
    product shape uses :class:`AffineRow` and this type sees no traffic.

    ``coefficients[i][block]`` is the operator ``C`` of the ``i``-th REAL
    equation ``sum_block tr[C J_block] bowtie targets[i]``, one per element of a
    Hermitian basis of the comparison space; ``slack_dim`` is the dimension of
    that space, which an inequality needs a positive semidefinite slack on. A
    block absent from one equation's mapping contributes nothing to it, which is
    how a party-local row at one ``s_{f^c}`` names only the blocks whose other
    factors match.

    AN EMPTY TUPLE OF THESE IS TODAY'S PROBLEM, ROW FOR ROW: nothing in the
    accepted format builds one, so no existing subproblem changes.
    """

    coefficients: tuple[Mapping[str, Matrix], ...]
    targets: tuple[float, ...]
    relation: ConstraintRelation
    slack_dim: int
    #: What this row is, for a diagnostic and for the record. Never read as
    #: data by a backend.
    label: str = ""


class Coupling(StrEnum):
    """Which coupling constraint binds the blocks (lem:choi-marginal).

    Mirrors :class:`certiqs_key.meat_core.objective.choi.Coupling` at the oracle
    boundary, where the enum is physics-blind: it says which equations to build,
    not what they mean. The two are not two spellings of one condition; see the
    module docstring.
    """

    #: ``sum_s tr_{Q_s} J_s = 1_{A_0}`` -- Eq. ``eq:choi-feas``.
    INPUT_IDENTITY = "input_identity"
    #: ``sum_s tr J_s = 1`` -- Eq. ``eq:choi-feas-un``.
    UNIT_TRACE = "unit_trace"


@dataclass(frozen=True)
class SectorChoiProblem:
    """The Frank-Wolfe linear subproblem, in sector-Choi form.

    Physics-blind: matrices, dimensions, relations and one coupling tag.
    """

    input_dim: int
    block_dims: Mapping[str, int]
    cost: Mapping[str, Matrix]
    rows: Sequence[AffineRow] = ()
    coupling: Coupling = Coupling.INPUT_IDENTITY
    #: The general-format rows of ``eq:partylocal-entry``, conjugated as
    #: ``thm:choi``'s general format writes them. EMPTY IS TODAY'S PROBLEM: no
    #: declaration of the accepted format produces one.
    general_rows: Sequence[GeneralOperatorRow] = ()

    @property
    def blocks(self) -> tuple[str, ...]:
        """Return the block labels in a deterministic order."""
        return tuple(self.block_dims)

    def variable_dim(self, block: str) -> int:
        """Return the matrix dimension of one Choi block."""
        return self.input_dim * self.block_dims[block]

    def coupling_equations(self) -> tuple[tuple[Matrix, float], ...]:
        """Return the coupling constraint as ``(input operator, target)`` pairs.

        Each pair ``(G, t)`` stands for the real equation
        ``sum_s tr[(G x 1_{Q_s}) J_s] = t``:

        * ``input_identity`` -- one pair per element ``E`` of a Hermitian basis
          of the input space, with ``t = tr E``. Together they say
          ``sum_s tr_{Q_s} J_s = 1_{A_0}``, ``d_{A_0}^2`` real equations;
        * ``unit_trace`` -- the single pair ``(1_{input}, 1)``, i.e.
          ``sum_s tr J_s = 1``, ONE real equation.

        The counts differ, which is the point: a run in untrusted-source mode
        that produced ``d_A^2`` coupling equations would be imposing the
        operator condition Definition ``def:untrusted-choi`` (b) rejects.
        """
        if self.coupling is Coupling.UNIT_TRACE:
            identity = np.eye(self.input_dim, dtype=np.complex128)
            return ((identity, 1.0),)
        return tuple(
            (element, float(np.real(np.trace(element))))
            for element in hermitian_basis(self.input_dim)
        )


def row_equations(row: AffineRow, input_dim: int) -> tuple[tuple[Matrix, float], ...]:
    """Return one constraint row as ``(input operator, target)`` pairs.

    Each pair ``(G, t)`` stands for the real relation
    ``sum_s tr[(G x H_{k,s}) J_s] bowtie_k t``, with the row's own slack
    supplying the inequality.

    OPERATOR row: ``G = C^dagger E C`` and ``t = tr[E R]`` for ``E`` over a
    Hermitian basis of the right-hand side space and ``C`` the declared
    congruence, since ``tr[E C L C^dagger] = tr[(C^dagger E C) L]``. That is
    Eq. ``eq:choi-feas``'s ``W_tau ( ... ) W_tau^dagger bowtie_k Theta_k``,
    read against a basis.

    SCALAR row: the single pair ``(1_{input}, c_k)``, which is
    ``tr[(1_A x O_k) omega] bowtie_k c_k`` of Eq. ``eq:choi-feas-un``. The
    left-hand side is the FULL trace, over the input factor as well: in
    untrusted-source mode ``A`` is an output of Eve's channel, so Lemma
    ``lem:range`` (i) transports only the trace identity and there is no
    operator-valued analogue to compare on ``A``.
    """
    if row.is_scalar:
        if row.congruence is not None:
            raise OracleFailure(
                "a scalar row has no operator side to conjugate; a congruence "
                "on it would be the W_tau substitution Definition "
                "def:untrusted-choi (b) rejects"
            )
        identity = np.eye(input_dim, dtype=np.complex128)
        return ((identity, float(row.rhs)),)
    rhs = np.asarray(row.rhs, dtype=np.complex128)
    congruence = (
        np.eye(input_dim, dtype=np.complex128)
        if row.congruence is None
        else np.asarray(row.congruence, dtype=np.complex128)
    )
    return tuple(
        (
            np.asarray(congruence.conj().T @ element @ congruence, np.complex128),
            float(np.real(np.trace(element @ rhs))),
        )
        for element in hermitian_basis(int(rhs.shape[0]))
    )


@dataclass(frozen=True)
class OracleDual:
    """The multipliers of one solve, BACKEND-NEUTRAL, in the textbook sign.

    ``meat-core/frank-wolfe/req:verified-feasible-side`` (ii) reads ``Y`` and
    every ``Lambda_r`` off "the dual the backend returned for that same solve,
    as the operators that the multipliers of the coupling condition and of row
    ``r`` represent in the encoding the oracle used". This is that encoding,
    stated once, so that every backend fills the same fields:

    * ``coupling``: ``Y``, a ``d x d`` Hermitian array under the
      ``input_identity`` coupling, or the scalar ``y`` under ``unit_trace``;
    * ``rows``: one entry per ``problem.rows``, in order: the Hermitian
      operator on the row's right-hand-side space (``slack_dim``) for an
      operator row, the scalar for a scalar row;
    * ``general_rows``: one weight vector per ``problem.general_rows``, in
      order, one weight per real equation, i.e. per element of
      :func:`hermitian_basis` of the row's ``slack_dim``.

    The sign is the Lagrangian's: the residual is ``C - Y (x) 1 - sum_r
    L*_r(Lambda_r)`` with no sign repair applied, so an inequality row's
    multiplier is positive semidefinite for ``succeq`` and negative
    semidefinite for ``preceq`` when the dual is feasible. NOTHING IS ASSUMED OF
    IT: Lemma ``lem:feasible-side-dual`` (i) holds for any multipliers, and the
    evaluator repairs the signs exactly. A backend that returns no dual leaves
    :attr:`OracleSolution.dual` ``None``, and the bound is then formed with
    zero multipliers.
    """

    coupling: Matrix | float
    rows: tuple[Matrix | float, ...] = ()
    general_rows: tuple[npt.NDArray[np.float64], ...] = ()

    def is_finite(self) -> bool:
        """Return whether every multiplier is a finite number."""
        values = [np.asarray(self.coupling)]
        values += [np.asarray(row) for row in self.rows]
        values += [np.asarray(weights) for weights in self.general_rows]
        return all(bool(np.all(np.isfinite(value))) for value in values)


def zero_dual(problem: SectorChoiProblem) -> OracleDual:
    """Return the zero multipliers of a subproblem, in :class:`OracleDual`'s shape."""
    coupling: Matrix | float = (
        0.0
        if problem.coupling is Coupling.UNIT_TRACE
        else np.zeros((problem.input_dim, problem.input_dim), dtype=np.complex128)
    )
    return OracleDual(
        coupling=coupling,
        rows=tuple(
            0.0
            if row.is_scalar
            else np.zeros((row.slack_dim, row.slack_dim), dtype=np.complex128)
            for row in problem.rows
        ),
        general_rows=tuple(
            np.zeros(len(row.coefficients)) for row in problem.general_rows
        ),
    )


def dual_from_equations(
    problem: SectorChoiProblem, multipliers: npt.ArrayLike
) -> OracleDual:
    """Return the :class:`OracleDual` of one multiplier per real equation.

    ``multipliers`` are in the order a backend that encodes the subproblem by
    :meth:`SectorChoiProblem.coupling_equations`, :func:`row_equations` and
    the general rows' coefficients builds its equations -- the coupling
    equations, then each row's in ``problem.rows`` order, then each general
    row's in ``problem.general_rows`` order -- and in the TEXTBOOK sign, the
    Lagrangian ``<C, J> - sum_i m_i (<A_i, J> - t_i)``. Each operator is
    assembled in binary64 against the same basis the equations were built
    from; the evaluator takes the exact Hermitian part of what is returned as
    its datum, so the ``1/sqrt(2)`` of the basis needs no exactness.

    Raises:
        OracleFailure: the count is not the number of equations.
    """
    values = np.asarray(multipliers, dtype=np.float64).ravel()
    index = 0

    def take(count: int) -> npt.NDArray[np.float64]:
        nonlocal index
        part = values[index : index + count]
        index += count
        return part

    coupling_basis = problem.coupling_equations()
    part = take(len(coupling_basis))
    coupling: Matrix | float = (
        float(part[0])
        if problem.coupling is Coupling.UNIT_TRACE
        else _combination(part, [element for element, _ in coupling_basis])
    )
    rows: list[Matrix | float] = []
    for row in problem.rows:
        if row.is_scalar:
            rows.append(float(take(1)[0]))
        else:
            basis = hermitian_basis(row.slack_dim)
            rows.append(_combination(take(len(basis)), basis))
    general = tuple(
        np.array(take(len(row.coefficients))) for row in problem.general_rows
    )
    if index != values.size:
        raise OracleFailure(
            f"the backend returned {values.size} multipliers for {index} equations"
        )
    return OracleDual(coupling=coupling, rows=tuple(rows), general_rows=general)


def _combination(weights: npt.NDArray[np.float64], basis: Sequence[Matrix]) -> Matrix:
    """Return ``sum_i w_i E_i`` in binary64."""
    total = np.zeros_like(np.asarray(basis[0], dtype=np.complex128))
    for weight, element in zip(weights, basis, strict=True):
        total = total + float(weight) * np.asarray(element, dtype=np.complex128)
    return np.asarray(total, dtype=np.complex128)


@dataclass(frozen=True)
class OracleSolution:
    """An extreme point of the subproblem, plus diagnostics and the dual.

    ``diagnostics`` carries the backend's own report -- status, gap, residuals,
    iteration count. Diagnostics only (spec/architecture.md 7.4). ``dual`` is
    the backend's dual for this solve (:class:`OracleDual`), or ``None`` where
    the backend returned none; it is a CANDIDATE, which the feasible-side bound
    verifies exactly and never trusts.
    """

    blocks: Mapping[str, Matrix]
    objective: float
    diagnostics: Mapping[str, Any] = field(default_factory=dict)
    dual: OracleDual | None = None


@runtime_checkable
class LinearOracle(Protocol):
    """The linear minimization oracle the Frank-Wolfe driver queries."""

    def capabilities(self) -> OracleCapabilities:
        """Return what this oracle declares it supports."""
        ...

    def minimize(self, problem: SectorChoiProblem) -> OracleSolution:
        """Return a minimizer of the linear cost over the feasible set."""
        ...


def hermitian_basis(dimension: int) -> tuple[Matrix, ...]:
    """Return an orthogonal basis of the Hermitian matrices of a dimension.

    Used to turn a Hermitian matrix EQUATION into the smallest set of
    independent real equations, ``d^2`` of them: the diagonal units and the
    real and imaginary off-diagonal pairs. Vectorizing the equation instead
    would produce ``2 d^2`` rows, half of them trivial or duplicated, and a
    rank-deficient constraint matrix is a needless hazard for an interior-point
    backend.
    """
    basis: list[Matrix] = []
    for index in range(dimension):
        element = np.zeros((dimension, dimension), dtype=np.complex128)
        element[index, index] = 1.0
        basis.append(element)
    root = 1.0 / np.sqrt(2.0)
    for row in range(dimension):
        for column in range(row + 1, dimension):
            symmetric = np.zeros((dimension, dimension), dtype=np.complex128)
            symmetric[row, column] = root
            symmetric[column, row] = root
            basis.append(symmetric)
            antisymmetric = np.zeros((dimension, dimension), dtype=np.complex128)
            antisymmetric[row, column] = 1j * root
            antisymmetric[column, row] = -1j * root
            basis.append(antisymmetric)
    return tuple(basis)
