"""The general format's driver: the per-Alice-sector programs, the dropped name.

``thm:choi``'s product structure (one conic program per Alice sector), the
dropped set as a run option (with ``h_lb_dropped`` reported under its own
name), and the per-stage timing hooks.

THE ORACLE HERE IS A STUB and it is a checking one: it verifies the shape of
every problem it is handed -- the input dimension, the block labels and their
dimensions, the coupling tag, the row count -- and returns the point it was
given, which is a vertex of nothing but is feasible, so the driver's gap is zero
and one iterate contributes. Real conic tests additionally exercise the
backend's status vocabulary and the optimization over the product.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pytest
from tests.support.general_toys import (
    decoy_like_general,
    honest_q,
    maps_of,
    two_factor_general,
)

from certiqs_key.meat_core.objective.joint import (
    JointSector,
    normalise_dropped_set,
)
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    coupling_residuals,
    first_order_bracket,
    joint_initial_point,
    run_joint_frank_wolfe,
)
from certiqs_key.solvers.oracles.acceptance import SingletonAcceptanceOracle
from certiqs_key.solvers.oracles.joint_rows import (
    joint_label,
    joint_program_for_alice_sector,
    joint_program_untrusted,
)
from certiqs_key.solvers.oracles.protocol import (
    Coupling,
    OracleSolution,
    SectorChoiProblem,
)


class _EchoOracle:
    """A stub linear oracle that returns the point it was handed."""

    def __init__(self, point: Mapping[JointSector, Any], *, trusted: bool) -> None:
        self.point = dict(point)
        self.trusted = trusted
        self.problems: list[SectorChoiProblem] = []

    def capabilities(self) -> Any:
        """Return nothing the driver reads; the stub declares no capability."""
        raise NotImplementedError

    def minimize(self, problem: SectorChoiProblem) -> OracleSolution:
        """Return the corresponding blocks of the stored point."""
        self.problems.append(problem)
        if self.trusted:
            alice = next(
                sector
                for sector in {pair[0] for pair in self.point}
                if all(
                    problem.variable_dim(block)
                    == np.asarray(self.point[(sector, block)]).shape[0]
                    for block in problem.blocks
                )
            )
            blocks = {
                block: np.asarray(self.point[(alice, block)])
                for block in problem.blocks
            }
        else:
            blocks = {
                joint_label(pair): np.asarray(block)
                for pair, block in self.point.items()
            }
        return OracleSolution(
            blocks=blocks, objective=0.0, diagnostics={"sol_status": "optimal"}
        )


def test_the_trusted_program_splits_one_per_alice_sector() -> None:
    """``thm:choi``, the general format: ``Feas^J = prod_t Feas^J_t``."""
    maps = maps_of(decoy_like_general())
    parametrization = maps.parametrization
    point = joint_initial_point(parametrization)
    for alice_sector in maps.declaration.alice_sectors:
        problem = joint_program_for_alice_sector(parametrization, alice_sector, point)
        assert problem.coupling is Coupling.INPUT_IDENTITY
        assert problem.input_dim == parametrization.input_dim(alice_sector)
        assert set(problem.blocks) == set(maps.declaration.sector_index_set)
        for sector in problem.blocks:
            assert problem.variable_dim(sector) == parametrization.block_dim(
                (alice_sector, sector)
            )
        assert not problem.rows and not problem.general_rows


def test_the_untrusted_program_is_one_over_every_joint_sector() -> None:
    """``frank-wolfe/rem:fo-general-format`` (2): nothing splits there."""
    declaration = two_factor_general(party_local=True)
    maps = maps_of(declaration)
    parametrization = maps.parametrization
    point = joint_initial_point(parametrization)
    problem = joint_program_untrusted(parametrization, point)
    assert problem.coupling is Coupling.UNIT_TRACE
    assert problem.input_dim == 1
    assert set(problem.blocks) == {
        joint_label(pair) for pair in parametrization.joint_sectors
    }
    # A party_local entry produces a GENERAL row and no affine row: its
    # comparison space is A_t (x) Q_{f^c}, which no product G (x) H_s expresses.
    assert problem.general_rows and not problem.rows
    assert all(row.slack_dim == 2 for row in problem.general_rows)


def test_the_initial_point_meets_the_coupling_of_its_mode() -> None:
    """One residual per Alice sector, trusted; one scalar residual, untrusted."""
    trusted = maps_of(decoy_like_general()).parametrization
    residuals = coupling_residuals(trusted, joint_initial_point(trusted))
    assert set(residuals) == set(trusted.declaration.alice_sectors)
    assert max(residuals.values()) < 1e-12
    untrusted = maps_of(two_factor_general(party_local=False)).parametrization
    assert set(coupling_residuals(untrusted, joint_initial_point(untrusted))) == {"*"}


def test_a_run_with_no_dropped_set_reports_h_lb_and_not_h_lb_dropped() -> None:
    """``cor:fo-dropped``: the two numbers never travel under one name."""
    maps = maps_of(decoy_like_general())
    point = joint_initial_point(maps.parametrization)
    oracle = _EchoOracle(point, trusted=True)
    acceptance = SingletonAcceptanceOracle(honest_q(maps, point))
    result = run_joint_frank_wolfe(
        maps,
        oracle,
        acceptance,
        point,
        1.5,
        FrankWolfeOptions(max_iterations=2),
    )
    assert result.h_lb is not None
    assert result.h_lb_dropped is None
    assert result.dropped_set == ()
    assert result.status == "converged"
    # ONE PROGRAM PER ALICE SECTOR was solved at the iterate.
    assert len(oracle.problems) == len(maps.declaration.alice_sectors)
    # The timing hooks.
    assert set(result.timings.seconds) >= {"gradient", "oracle"}
    assert result.timings.calls["oracle"] >= 1


def test_a_run_with_a_dropped_set_reports_h_lb_dropped_with_d_beside_it() -> None:
    """``def:dropped`` and the ``h_lb_dropped`` output row."""
    maps = maps_of(decoy_like_general())
    point = joint_initial_point(maps.parametrization)
    dropped = [("match", ("one", "q"))]
    oracle = _EchoOracle(point, trusted=True)
    acceptance = SingletonAcceptanceOracle(honest_q(maps, point))
    result = run_joint_frank_wolfe(
        maps,
        oracle,
        acceptance,
        point,
        1.5,
        FrankWolfeOptions(max_iterations=2),
        dropped=dropped,
    )
    assert result.h_lb is None
    assert result.h_lb_dropped is not None
    assert result.dropped_set == (("match", ("one", "q")),)
    # The dropped program's value is no larger than the undropped one's, which
    # is prop:drop-bound (ii) at the same point.
    plain = run_joint_frank_wolfe(
        maps,
        oracle,
        acceptance,
        point,
        1.5,
        FrankWolfeOptions(max_iterations=2),
    )
    assert result.objective <= plain.objective + 1e-12


@pytest.mark.parametrize("alpha", (1.5, 2.0))
def test_the_bracket_at_a_zero_direction_is_the_objective(alpha: float) -> None:
    """``eq:hlb``: the objective plus two pairings, at a vanishing direction.

    With the comparison point equal to the iterate both pairings vanish, so the
    bracket IS the objective at the iterate -- which is the one value
    ``eq:hlb`` takes that a test can state without a backend, and it is what the
    driver's gate records when the oracle returns the point it was given.
    """
    maps = maps_of(decoy_like_general())
    point = joint_initial_point(maps.parametrization)
    q = honest_q(maps, point)
    dropped = normalise_dropped_set(maps, [("match", ("vacuum", "q"))])
    bracket = first_order_bracket(maps, q, point, alpha, q, point, dropped=dropped)
    from certiqs_key.meat_core.objective.joint import joint_objective_value

    assert bracket == pytest.approx(
        joint_objective_value(maps, q, point, alpha, dropped=dropped), abs=1e-12
    )


def test_a_step_the_direct_path_rejects_is_counted_and_not_taken(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The interpolated search chooses; the direct value decides and is counted.

    The interpolated objective is patched to look better at every trial point
    and the direct one never to improve, so every search proposes a step and
    every direct re-evaluation refuses it. A zero gap does not stop the loop
    here because the gap tolerance is set to minus infinity, which is a test
    option and not a stopping rule of the driver.
    """
    import certiqs_key.solvers.frank_wolfe.joint_driver as joint_driver

    monkeypatch.setattr(joint_driver, "joint_objective_value", lambda *a, **k: 1.0)
    monkeypatch.setattr(
        joint_driver, "joint_objective_value_at_statistics", lambda *a, **k: 0.0
    )
    maps = maps_of(decoy_like_general())
    point = joint_initial_point(maps.parametrization)
    iterations = 3
    result = run_joint_frank_wolfe(
        maps,
        _EchoOracle(point, trusted=True),
        SingletonAcceptanceOracle(honest_q(maps, point)),
        point,
        1.5,
        FrankWolfeOptions(max_iterations=iterations, gap_tolerance=-float("inf")),
    )
    assert result.iterations == iterations
    assert result.timings.calls["accepted_point_rejected"] == iterations
    assert result.timings.calls["accepted_point_objective"] == iterations
    assert [gate.objective for gate in result.gates] == [1.0] * iterations
    assert result.objective == 1.0
    assert result.status == "iteration-limit"
