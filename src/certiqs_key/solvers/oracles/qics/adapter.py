"""The initial ``LinearOracle``: the sector-Choi encoding on QICS.

spec/architecture.md 7.4. QICS hosts a linear conic program over a product of
``PosSemidefinite(..., iscomplex=True)`` cones plus affine rows, and this
adapter maps the Frank-Wolfe subproblem of
:mod:`certiqs_key.solvers.oracles.protocol` into that form::

    variables   J_s  (one PSD block per declared sector, input factor first)
                S_k  (one slack per declared INEQUALITY row: a PSD block for an
                      operator row, a non-negative scalar for a scalar row)
    equalities  the declared COUPLING equations
                the declared ROW equations, minus/plus their slack
    objective   sum_s <C_s, J_s>

Both the coupling and the rows arrive already reduced to real
``(input operator, target)`` pairs by
:meth:`~certiqs_key.solvers.oracles.protocol.SectorChoiProblem.coupling_equations`
and :func:`~certiqs_key.solvers.oracles.protocol.row_equations`, so this adapter
never has to know which source mode produced them. What it does see is the
COUNT: ``d_{A_0}^2`` coupling equations for ``sum_s tr_{Q_s} J_s = 1_{A_0}``
(contract Eq. ``eq:choi-feas``) against exactly one for
``sum_s tr J_s = 1`` (Eq. ``eq:choi-feas-un``).

Three things this adapter does NOT do, each named as out of scope by
spec/architecture.md 7.4:

* it does not touch QICS's built-in quantum, Renyi-entropy or key-distance
  cones -- they are not ``K`` evaluators and must not be wired into the
  objective path;
* it does not solve the ``q``-frequency subproblem, which uses the separate
  acceptance-set oracle of :mod:`certiqs_key.solvers.oracles.acceptance`;
* it does not certify anything. "QICS status and gap are not a certificate.
  They may appear in the result record's diagnostics. THEY CANNOT RAISE THE
  REPORTED TIER: solver status and duality gap are diagnostics, never evidence
  (spec/architecture.md 2.5).

The import of ``qics`` is deliberately inside the methods. QICS is an optional
extra (pyproject.toml, the ``oracle-qics`` extra) precisely so that the
capability probe of
spec/architecture.md 7.3 is testable in an environment without it, and an
absent extra must produce a ``CapabilityError``
(:mod:`certiqs_key.solvers.capabilities.probe`) with installation instructions
rather than an ``ImportError`` from the middle of a solve.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import numpy.typing as npt

from certiqs_key.domain.manifest import ConstraintRelation
from certiqs_key.meat_core import thresholds
from certiqs_key.meat_core.objective.linalg import Matrix, hermitian_part
from certiqs_key.solvers.capabilities.probe import (
    QICS_INSTALL_HINT,
    Capability,
    CapabilityError,
    OracleCapabilities,
    qics_available,
    qics_version,
)
from certiqs_key.solvers.oracles.protocol import (
    OracleDual,
    OracleFailure,
    OracleSolution,
    SectorChoiProblem,
    dual_from_equations,
    hermitian_basis,
    row_equations,
)

#: Solution statuses this adapter accepts as an extreme point. ``near_optimal``
#: is accepted and RECORDED as such: it is a diagnostic like any other, and on
#: the estimate path a near-optimal linear minimizer is a usable Frank-Wolfe
#: direction, not a certificate (spec/architecture.md 2.5, spec/architecture.md 7.4).
ACCEPTED_STATUSES = ("optimal", "near_optimal")

#: The statuses that are QICS's verdict that the PRIMAL feasible set is empty,
#: which is def:admissible-declaration (vii) failing: raised with
#: ``infeasible=True``, so that every caller stops on them. ``near_pinfeas`` is
#: counted with ``pinfeas`` on the side of stopping. Every other status this
#: adapter does not accept (``unknown``, ``dinfeas``, ``illposed``, ...) is
#: raised as unsolved (:attr:`OracleFailure.unsolved`): it asserts neither a
#: minimum nor emptiness.
INFEASIBILITY_STATUSES = ("pinfeas", "near_pinfeas")

#: How far below zero a returned block's spectrum may sit before the solution is
#: rejected outright. An interior-point solver returns a point feasible to its
#: own tolerance, so a small negative eigenvalue is expected; it is clipped to
#: the PSD cone and the repair is RECORDED (spec/architecture.md 2.5), never
#: absorbed silently.
PSD_REPAIR_TOLERANCE = thresholds.declared(thresholds.ORACLE_REPAIR_WINDOW)


class QicsSectorChoiOracle:
    """A :class:`~certiqs_key.solvers.oracles.protocol.LinearOracle` backed by QICS."""

    def __init__(self, *, tol_gap: float = 1e-10, tol_feas: float = 1e-10) -> None:
        """Create the oracle, refusing at once if the optional extra is absent."""
        if not qics_available():
            raise CapabilityError(
                "the QICS linear oracle is not installed. "
                f"Install it with: {QICS_INSTALL_HINT}"
            )
        self.tol_gap = tol_gap
        self.tol_feas = tol_feas

    def capabilities(self) -> OracleCapabilities:
        """Return what this oracle declares (spec/architecture.md 7.3)."""
        return OracleCapabilities(
            name="qics-sector-choi",
            version=qics_version() or "unknown",
            capabilities=frozenset(
                {
                    Capability.COMPLEX_HERMITIAN_PSD,
                    Capability.DIRECT_SUM_SECTORS,
                    Capability.CHOI_FORM,
                    Capability.EQUALITY_ROWS,
                    Capability.INEQUALITY_ROWS,
                }
            ),
            max_sector_dim=None,
        )

    def minimize(self, problem: SectorChoiProblem) -> OracleSolution:
        """Return a minimizer of the linear cost over the declared feasible set.

        Raises:
            OracleFailure: if the backend reports primal infeasibility -- which
                is def:admissible-declaration (vii) failing, an empty feasible set ``W``
                -- or any status outside :data:`ACCEPTED_STATUSES`.
        """
        import qics
        from qics.vectorize import mat_to_vec, vec_to_mat

        blocks = problem.blocks
        cones: list[Any] = [
            qics.cones.PosSemidefinite(problem.variable_dim(block), iscomplex=True)
            for block in blocks
        ]
        slack_rows = [
            row for row in problem.rows if row.relation is not ConstraintRelation.EQ
        ]
        for row in slack_rows:
            # An operator row needs a PSD slack on the right-hand side space; a
            # scalar row (untrusted-source mode) needs a single non-negative
            # number, which is the order of the reals def:admissible-declaration (vi)
            # asks for.
            cones.append(
                qics.cones.NonNegOrthant(1)
                if row.is_scalar
                else qics.cones.PosSemidefinite(row.slack_dim, iscomplex=True)
            )
        # THE GENERAL-FORMAT ROWS (eq:partylocal-entry, conjugated by
        # W_t (x) 1): an operator relation on A_0 (x) Q_{f^c}, so an inequality
        # needs a PSD slack of THAT space's dimension. Empty on every
        # accepted-format problem, so nothing below this line runs on one.
        general_slack_rows = [
            row
            for row in problem.general_rows
            if row.relation is not ConstraintRelation.EQ
        ]
        for general_row in general_slack_rows:
            cones.append(
                qics.cones.PosSemidefinite(general_row.slack_dim, iscomplex=True)
            )
        dims = [int(cone.dim[0]) for cone in cones]
        offsets = np.cumsum([0, *dims])
        width = int(offsets[-1])

        cost = np.zeros((width, 1))
        for index, block in enumerate(blocks):
            cost[offsets[index] : offsets[index + 1], 0] = mat_to_vec(
                np.ascontiguousarray(
                    hermitian_part(np.asarray(problem.cost[block], np.complex128))
                )
            ).ravel()

        rows: list[npt.NDArray[np.float64]] = []
        targets: list[float] = []

        def block_coefficients(
            input_operator: Matrix, sector_operators: Mapping[str, Matrix] | None
        ) -> npt.NDArray[np.float64]:
            """Return the cost vector of ``sum_s tr[(G x H_s) J_s]``."""
            coefficients = np.zeros(width)
            for index, block in enumerate(blocks):
                sector_operator = (
                    np.eye(problem.block_dims[block], dtype=np.complex128)
                    if sector_operators is None
                    else np.asarray(sector_operators[block], dtype=np.complex128)
                )
                lifted = np.asarray(
                    np.kron(input_operator, sector_operator), dtype=np.complex128
                )
                coefficients[offsets[index] : offsets[index + 1]] = mat_to_vec(
                    np.ascontiguousarray(hermitian_part(lifted))
                ).ravel()
            return coefficients

        # The COUPLING constraint, in whichever of its two forms the problem
        # declares (contract Eqs. eq:choi-feas / eq:choi-feas-un).
        for element, target in problem.coupling_equations():
            rows.append(block_coefficients(element, None))
            targets.append(target)

        slack_index = len(blocks)
        for entry in problem.rows:
            equations = row_equations(entry, problem.input_dim)
            basis = (
                (np.ones((1, 1), dtype=np.complex128),)
                if entry.is_scalar
                else hermitian_basis(entry.slack_dim)
            )
            for (input_operator, target), element in zip(equations, basis, strict=True):
                coefficients = block_coefficients(input_operator, entry.blocks)
                if entry.relation is not ConstraintRelation.EQ:
                    sign = -1.0 if entry.relation is ConstraintRelation.SUCCEQ else 1.0
                    start, stop = offsets[slack_index], offsets[slack_index + 1]
                    coefficients[start:stop] = sign * (
                        np.ones(1)
                        if entry.is_scalar
                        else mat_to_vec(np.ascontiguousarray(element)).ravel()
                    )
                rows.append(coefficients)
                targets.append(target)
            if entry.relation is not ConstraintRelation.EQ:
                slack_index += 1

        def full_block_coefficients(
            per_block: Mapping[str, Matrix],
        ) -> npt.NDArray[np.float64]:
            """Return the cost vector of ``sum_block tr[C_block J_block]``.

            The general row's coefficient is one operator per Choi block, not a
            product ``G (x) H_s``, so it is vectorised as it stands. A block the
            row does not name contributes nothing to that equation.
            """
            coefficients = np.zeros(width)
            for index, block in enumerate(blocks):
                operator = per_block.get(block)
                if operator is None:
                    continue
                coefficients[offsets[index] : offsets[index + 1]] = mat_to_vec(
                    np.ascontiguousarray(
                        hermitian_part(np.asarray(operator, dtype=np.complex128))
                    )
                ).ravel()
            return coefficients

        for general_entry in problem.general_rows:
            basis = hermitian_basis(general_entry.slack_dim)
            for (per_block, target), element in zip(
                zip(
                    general_entry.coefficients, general_entry.targets, strict=True
                ),
                basis,
                strict=True,
            ):
                coefficients = full_block_coefficients(per_block)
                relation = general_entry.relation
                if relation is not ConstraintRelation.EQ:
                    sign = -1.0 if relation is ConstraintRelation.SUCCEQ else 1.0
                    start, stop = offsets[slack_index], offsets[slack_index + 1]
                    coefficients[start:stop] = sign * mat_to_vec(
                        np.ascontiguousarray(element)
                    ).ravel()
                rows.append(coefficients)
                targets.append(target)
            if general_entry.relation is not ConstraintRelation.EQ:
                slack_index += 1

        model = qics.Model(
            c=cost,
            A=np.asarray(rows, dtype=np.float64),
            b=np.asarray(targets, dtype=np.float64).reshape(-1, 1),
            cones=cones,
        )
        solver = qics.Solver(
            model, verbose=0, tol_gap=self.tol_gap, tol_feas=self.tol_feas
        )
        info = solver.solve()
        status = str(info["sol_status"])
        dual = _dual_of(problem, info)
        if status not in ACCEPTED_STATUSES:
            raise OracleFailure(
                f"the linear oracle returned status {status!r} "
                f"(exit {info['exit_status']!r}). A 'pinfeas' status means the "
                "declared feasible set W is empty, which is def:admissible-declaration "
                "(vii) failing; any other status is a backend failure. Either "
                "way no extreme point is returned for this subproblem",
                status=status,
                infeasible=status in INFEASIBILITY_STATUSES,
                dual=None if status in INFEASIBILITY_STATUSES else dual,
            )

        solution = np.asarray(info["x_opt"])
        repairs: list[dict[str, Any]] = []
        out: dict[str, Matrix] = {}
        for index, block in enumerate(blocks):
            matrix = hermitian_part(
                np.asarray(
                    vec_to_mat(
                        solution[offsets[index] : offsets[index + 1]], iscomplex=True
                    ),
                    dtype=np.complex128,
                )
            )
            values, vectors = np.linalg.eigh(matrix)
            smallest = float(np.min(values)) if values.size else 0.0
            if smallest < -PSD_REPAIR_TOLERANCE:
                raise OracleFailure(
                    f"the oracle returned a block on {block!r} with minimum "
                    f"eigenvalue {smallest:.3e}, beyond the repair tolerance "
                    f"{PSD_REPAIR_TOLERANCE:.1e}"
                )
            if smallest < 0.0:
                matrix = np.asarray(
                    (vectors * np.clip(values, 0.0, None)) @ vectors.conj().T,
                    dtype=np.complex128,
                )
                repairs.append(
                    {
                        "kind": "psd-projection-of-oracle-return",
                        "block": block,
                        "min_eigenvalue": smallest,
                        "note": (
                            "an interior-point return is feasible to the "
                            "solver's own tolerance; the negative part is "
                            "projected away and recorded "
                            "(spec/architecture.md 2.5)"
                        ),
                    }
                )
            out[block] = matrix

        diagnostics: dict[str, Any] = {
            "backend": "qics",
            "version": qics_version(),
            "sol_status": status,
            "exit_status": str(info["exit_status"]),
            "num_iter": int(info["num_iter"]),
            "primal_objective": float(info["p_obj"]),
            "dual_objective": float(info["d_obj"]),
            "opt_gap": float(info["opt_gap"]),
            "primal_feasibility": float(info["p_feas"]),
            "dual_feasibility": float(info["d_feas"]),
            "repairs": repairs,
            "note": (
                "diagnostics only: status and duality gap are not a "
                "certificate (spec/architecture.md 7.4)"
            ),
        }
        objective = sum(
            float(
                np.real(
                    np.trace(
                        np.asarray(problem.cost[block], np.complex128) @ out[block]
                    )
                )
            )
            for block in blocks
        )
        return OracleSolution(
            blocks=out, objective=objective, diagnostics=diagnostics, dual=dual
        )


def _dual_of(problem: SectorChoiProblem, info: Mapping[str, Any]) -> OracleDual | None:
    """Return the dual of the very solve, in :class:`OracleDual`'s encoding.

    QICS solves ``min c^T x`` subject to ``b - A x = 0`` and ``h - G x in K``
    with ``G = -1`` and ``h = 0``, and its dual is ``z = c + A^T y in K*`` with
    objective ``-b^T y`` (the ``qics.Model`` docstring), so the textbook
    multiplier of equation ``i`` is ``-y_i``. ``y_opt`` is unscaled by QICS and
    in the order the equations were built here: the coupling equations, each
    row's, then each general row's -- the order
    :func:`~certiqs_key.solvers.oracles.protocol.dual_from_equations` reads.
    ``None`` where QICS returned none, or a non-finite one: the bound is then
    formed with zero multipliers (``req:verified-feasible-side`` (ii)).
    """
    y = info.get("y_opt")
    if y is None:
        return None
    multipliers = -np.asarray(y, dtype=np.float64).ravel()
    if not np.all(np.isfinite(multipliers)):
        return None
    return dual_from_equations(problem, multipliers)
