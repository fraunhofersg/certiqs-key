"""A closed-form ``LinearOracle`` for the subproblems that are SPECTRAPLEXES.

``rem:fo-reachability`` says the module "prescribes no optimizer and does not
require one". Where the feasible set of a subproblem is a spectraplex the
linear minimum has a closed form, and this backend returns its minimiser
instead of an interior-point solve, for the search to step toward.

WHICH SUBPROBLEMS ARE SPECTRAPLEXES
===================================
A :class:`~certiqs_key.solvers.oracles.protocol.SectorChoiProblem` with NO
declared rows (neither affine nor general) whose coupling is ONE scalar
equation ``sum_b tr J_b = 1``::

    { (J_b)_b : J_b >= 0,  sum_b tr J_b = 1 }

That is the ``unit_trace`` coupling of untrusted-source mode (every joint
sector in one program, ``joint_program_untrusted``) and the ``input_identity``
coupling at input dimension one, where ``sum_b tr_{Q_b} J_b = 1_{A_0}`` IS the
scalar equation (``rem:modes-da1`` (b4)'s coincidence; the trusted-source
Alice sectors of dimension one, ``joint_program_for_alice_sector``). Its
extreme points are the rank-one projectors ``v v^dagger`` with ``||v|| = 1``
placed on ONE block, so

    min  sum_b <C_b, J_b>  =  min_b  lambda_min(C_b),

attained at the unit eigenvector of the smallest eigenvalue of the block that
carries it. Every other subproblem -- an input dimension above one under
``input_identity``, or any declared row -- is NOT a spectraplex and this
backend REFUSES it (:class:`~certiqs_key.solvers.oracles.protocol.OracleFailure`)
rather than returning something: spec/architecture.md 7.3, no silent fallback.
Which subproblem goes to which backend is decided structurally by the driver
before the loop (``joint_options.oracle_assignment`` in
:mod:`certiqs_key.solvers.frank_wolfe`) and recorded; the refusal here is
the second lock on the same door.

WHAT IT RETURNS AND WHAT IT RECORDS
===================================
It reports ``sol_status = "optimal"``, a diagnostic like every status, and the
ZERO DUAL: on a spectraplex (a one-dimensional coupling and no rows)
``frank-wolfe/req:verified-feasible-side`` (ii) takes ``Y = 0``, and
``lem:feasible-side-dual`` (iii) makes the verified bound
``min_b lambda_min(C_b)`` itself, so nothing is lost. No bracket reads the
returned vector. The EIGEN-RESIDUAL ``||C v - lambda v||_2`` of the returned
vector and the gap between the consumed value ``<C, v v^dagger>`` and ``lambda``
are recorded per call as evidence about the search's step; neither enters a
number.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from certiqs_key.meat_core.objective.linalg import Matrix, hermitian_part
from certiqs_key.solvers.capabilities.probe import Capability, OracleCapabilities
from certiqs_key.solvers.oracles.protocol import (
    Coupling,
    OracleFailure,
    OracleSolution,
    SectorChoiProblem,
    zero_dual,
)

#: The name and version this backend declares and every call records. The
#: version moves when what it computes moves.
SPECTRAL_BACKEND = "spectral"
SPECTRAL_VERSION = "1"


def is_spectraplex(problem: SectorChoiProblem) -> bool:
    """Return whether a subproblem's feasible set is a spectraplex.

    Structural only: no declared row of either kind, and a coupling that is one
    scalar equation -- ``unit_trace``, or ``input_identity`` at input dimension
    one. Nothing numerical is read.
    """
    if problem.rows or problem.general_rows:
        return False
    return problem.coupling is Coupling.UNIT_TRACE or problem.input_dim == 1


class SpectralSectorChoiOracle:
    """The closed-form ``LinearOracle``, for spectraplex subproblems only."""

    def capabilities(self) -> OracleCapabilities:
        """Return what this backend declares (spec/architecture.md 7.3).

        No row capability: a spectraplex subproblem has no declared rows, and a
        problem with one is refused. The coupling is not a row; it is the
        normalisation the closed form is stated on.
        """
        return OracleCapabilities(
            name="spectral-sector-choi",
            version=SPECTRAL_VERSION,
            capabilities=frozenset(
                {
                    Capability.COMPLEX_HERMITIAN_PSD,
                    Capability.DIRECT_SUM_SECTORS,
                    Capability.CHOI_FORM,
                }
            ),
            max_sector_dim=None,
        )

    def minimize(self, problem: SectorChoiProblem) -> OracleSolution:
        """Return ``v v^dagger`` on the block of the smallest eigenvalue.

        Ties between blocks go to the first block in the problem's order and
        within a block to the eigensolver's first eigenvector, so the return is
        deterministic.

        Raises:
            OracleFailure: if the problem is not a spectraplex, or a cost block
                is not finite. Never a substitute return.
        """
        if not is_spectraplex(problem):
            raise OracleFailure(
                "the spectral oracle was handed a subproblem that is not a "
                "spectraplex (declared rows, or an input dimension above one "
                "under the operator coupling); its closed form does not apply "
                "and nothing is returned. spec/architecture.md 7.3: no silent "
                "fallback"
            )
        best: tuple[float, str, Matrix, Matrix] | None = None
        for block in problem.blocks:
            cost = hermitian_part(np.asarray(problem.cost[block], np.complex128))
            if not np.all(np.isfinite(cost)):
                raise OracleFailure(f"the cost on block {block!r} is not finite")
            values, vectors = np.linalg.eigh(cost)
            smallest = float(values[0])
            if best is None or smallest < best[0]:
                best = (smallest, block, vectors[:, 0], cost)
        if best is None:
            raise OracleFailure("the spectral oracle was handed no block")
        value, chosen, vector, cost = best
        vector = np.asarray(vector, dtype=np.complex128)
        vector = vector / np.linalg.norm(vector)
        out: dict[str, Matrix] = {}
        for block in problem.blocks:
            dim = problem.variable_dim(block)
            out[block] = np.zeros((dim, dim), dtype=np.complex128)
        out[chosen] = np.asarray(np.outer(vector, vector.conj()), dtype=np.complex128)
        consumed_cost = np.asarray(problem.cost[chosen], dtype=np.complex128)
        objective = float(np.real(np.trace(consumed_cost @ out[chosen])))
        residual = float(np.linalg.norm(cost @ vector - value * vector))
        diagnostics: dict[str, Any] = {
            "backend": SPECTRAL_BACKEND,
            "version": SPECTRAL_VERSION,
            "sol_status": "optimal",
            "block": chosen,
            "min_eigenvalue": value,
            "eigen_residual": residual,
            "consumed_minus_eigenvalue": objective - value,
            "note": (
                "closed-form minimum over a spectraplex; the residual is "
                "evidence and discharges nothing (frank-wolfe/rem:fo-arithmetic)"
            ),
        }
        return OracleSolution(
            blocks=out,
            objective=objective,
            diagnostics=diagnostics,
            dual=zero_dual(problem),
        )


__all__ = [
    "SPECTRAL_BACKEND",
    "SPECTRAL_VERSION",
    "SpectralSectorChoiOracle",
    "is_spectraplex",
]
