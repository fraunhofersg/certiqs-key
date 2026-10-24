"""The bracket reads the verified feasible side, never the oracle's return or status.

CONTRACT TESTS of ``meat-core/frank-wolfe/req:verified-feasible-side`` and
the amended ``req:first-order-withdrawal`` through the one gate every search
uses (:func:`~certiqs_key.solvers.assessment.assess_candidate`):

* a CORRUPTED return -- the backend's point scaled so that its pairing is too
  low, or too high -- moves the diagnostic ``oracle_pairing`` (and the
  search's gap) and leaves the bracket bit for bit where it was;
* a status that asserts no optimality withdraws nothing and changes no
  number;
* the bracket is ``value + fl_down(b^F_t) - <G, J_t> + <g, v_t - q_t>``,
  ``b^F_t`` rounded toward ``-inf`` (item (v)), with its record (item (vi)).
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from typing import Any

import numpy as np
import pytest
from tests.support.general_toys import decoy_like_general, honest_q, maps_of

from certiqs_key.foundations.dyadic import float_down
from certiqs_key.meat_core.objective.linalg import as_matrix
from certiqs_key.solvers.assessment import CandidateAssessment, assess_candidate
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_driver import joint_initial_point
from certiqs_key.solvers.oracles.acceptance import SingletonAcceptanceOracle
from certiqs_key.solvers.oracles.protocol import OracleSolution, SectorChoiProblem
from certiqs_key.solvers.problem import prepared_from_maps

pytestmark = [pytest.mark.contract, pytest.mark.requires_qics]


class _Tampered:
    """QICS, with the returned point scaled and/or the status replaced.

    The dual of the very solve is passed through untouched, as a backend that
    returned a poor point beside its dual would.
    """

    def __init__(self, *, factor: float = 1.0, status: str | None = None) -> None:
        from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

        self.inner = QicsSectorChoiOracle()
        self.factor = factor
        self.status = status

    def capabilities(self) -> Any:
        return self.inner.capabilities()

    def minimize(self, problem: SectorChoiProblem) -> OracleSolution:
        solution = self.inner.minimize(problem)
        diagnostics = dict(solution.diagnostics)
        if self.status is not None:
            diagnostics["sol_status"] = self.status
        return replace(
            solution,
            blocks={
                label: self.factor * block for label, block in solution.blocks.items()
            },
            diagnostics=diagnostics,
        )


def _assess(oracle: Any) -> CandidateAssessment:
    pytest.importorskip("qics")
    maps = maps_of(decoy_like_general())
    point = joint_initial_point(maps.parametrization)
    problem = prepared_from_maps(
        maps,
        oracle,
        SingletonAcceptanceOracle(honest_q(maps, point)),
        1.5,
        FrankWolfeOptions(max_iterations=1),
    )
    return assess_candidate(problem, point)


@pytest.mark.parametrize("factor", [0.999, 1.001])
def test_a_corrupted_return_moves_the_diagnostic_and_not_the_bracket(
    factor: float,
) -> None:
    honest = _assess(_Tampered())
    corrupted = _assess(_Tampered(factor=factor))
    assert honest.contributes and corrupted.contributes
    assert corrupted.gate.linearization == honest.gate.linearization
    assert corrupted.gate.feasible_side_bound == honest.gate.feasible_side_bound
    assert honest.gate.oracle_pairing is not None
    assert corrupted.gate.oracle_pairing is not None
    assert corrupted.gate.oracle_pairing != honest.gate.oracle_pairing
    assert corrupted.gap != honest.gap
    # Under A-LMO the bracket WAS the pairing: it would have moved with it.
    shift = corrupted.gate.oracle_pairing - honest.gate.oracle_pairing
    assert abs(shift) > 1e-6


def test_a_status_that_asserts_no_optimality_withdraws_nothing() -> None:
    """``req:first-order-withdrawal``: no return and no status removes an iterate."""
    honest = _assess(_Tampered())
    nearly = _assess(_Tampered(status="near_optimal"))
    assert nearly.contributes
    assert nearly.gate.withdrawal is None
    assert nearly.gate.oracle_status == "near_optimal"
    assert nearly.gate.oracle_optimal is False
    assert nearly.gate.linearization == honest.gate.linearization


def test_the_bracket_is_the_verified_side_rounded_down_with_its_record() -> None:
    assessment = _assess(_Tampered())
    gate = assessment.gate
    side = assessment.feasible_side
    assert side is not None and assessment.gradient is not None
    assert gate.feasible_side_bound == float_down(side.bound)
    assert Fraction(gate.feasible_side_bound) <= side.bound
    direction = gate.feasible_side_bound
    for pair, block in assessment.gradient.blocks.items():
        direction -= float(np.real(np.trace(block @ as_matrix(assessment.point[pair]))))
    # The singleton acceptance set: v = q, so the acceptance side adds nothing.
    assert gate.linearization == gate.objective + direction
    assert set(gate.feasible_side_multipliers) == {
        pair[0] for pair in assessment.gradient.blocks
    }
    assert gate.dual_gap is not None and gate.oracle_pairing is not None
    assert gate.dual_gap == float(Fraction(gate.oracle_pairing) - side.bound)
    assert gate.frame_deduction == float(side.frame_deduction)
