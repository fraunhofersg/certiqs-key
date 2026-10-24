"""Solve-local LP reuse must preserve the legacy exact support and start."""

import subprocess
import sys
from dataclasses import replace
from fractions import Fraction

import pytest
from tests.support.general_toys import decoy_like_general

from certiqs_key.meat_core.acceptance import geometry
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet, PolytopeData
from certiqs_key.solvers import problem
from certiqs_key.solvers.frank_wolfe import general_keyrate, joint_driver
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle


def test_reused_support_stays_exact_when_start_rounds_to_zero():
    tiny = float.fromhex("0x0.0000000000001p-1022")
    data = PolytopeData(columns=2, rows=((1.0, 0.0),), rhs=(tiny,))
    prepared = geometry.polytope_support_and_start(data)
    assert prepared is not None
    support, start = prepared
    assert support == geometry.polytope_support(data) == (0, 1)
    assert start == geometry.polytope_relative_interior_point(data)
    assert start[0] == 0.0  # Exact support must not be inferred from this float.


@pytest.mark.requires_qics
def test_general_solve_reuses_maximizers_and_keeps_optimizer_result(
    monkeypatch: pytest.MonkeyPatch,
):
    original = geometry.polytope_coordinate_maximizers
    calls = []

    def counted(data: PolytopeData) -> tuple[tuple[Fraction, ...], ...] | None:
        calls.append(data)
        return original(data)

    monkeypatch.setattr(geometry, "polytope_coordinate_maximizers", counted)
    data = PolytopeData(columns=2, rows=((1.0, 0.0), (-1.0, 0.0)), rhs=(0.75, -0.25))
    declaration = replace(
        decoy_like_general(),
        acceptance_set=AcceptanceSet(
            geometry="polytope",
            polytope=data,
        ),
    )
    oracle = QicsSectorChoiOracle()
    options = FrankWolfeOptions(max_iterations=2)

    def legacy(data: PolytopeData) -> tuple[tuple[int, ...], tuple[Fraction, ...]]:
        support = geometry.polytope_support(data)
        start = geometry.polytope_relative_interior_point_exact(data)
        assert start is not None
        return support, start

    with monkeypatch.context() as context:
        context.setattr(problem, "polytope_support_and_exact_start", legacy)
        baseline = general_keyrate.solve_general_declaration(
            declaration, oracle, options=options
        )
    assert len(calls) == 2
    calls.clear()
    reused = general_keyrate.solve_general_declaration(
        declaration, oracle, options=options
    )
    assert len(calls) == 1
    assert reused.status == baseline.status
    assert reused.withdrawal == baseline.withdrawal
    assert reused.objective == pytest.approx(baseline.objective, abs=1e-13)
    assert reused.gap == pytest.approx(baseline.gap, abs=1e-13)
    assert reused.h_lb == pytest.approx(baseline.h_lb, abs=1e-13)
    assert reused.q == pytest.approx(baseline.q, abs=1e-13)
    calls.clear()
    general_keyrate.solve_general_declaration(declaration, oracle, options=options)
    assert len(calls) == 1  # A new solve computes its own batch; no global cache.


@pytest.mark.requires_qics
def test_canonical_box_dispatch_preserves_unique_extrema_solve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.unit.test_canonical_box_acceptance import box_data

    data = box_data((0.25, 0.25), (0.75, 0.75))
    declaration = replace(
        decoy_like_general(),
        acceptance_set=AcceptanceSet(geometry="polytope", polytope=data),
    )
    options = FrankWolfeOptions(max_iterations=2)
    # WHAT IS COMPARED IS THE LP DISPATCH, so the q rule is held at the
    # previous vertex step on both sides. A declared box gets
    # exact partial minimisation in q and a generic polytope does not
    # (joint_driver, q_rule), so the two runs would otherwise differ by design.
    monkeypatch.setattr(joint_driver, "q_rule_for", lambda *args: None)
    with monkeypatch.context() as context:
        context.setattr(problem, "canonical_box", lambda data: None)
        generic = general_keyrate.solve_general_declaration(
            declaration, QicsSectorChoiOracle(), options=options
        )

    def no_generic_maximizers(data: PolytopeData) -> None:
        raise AssertionError("canonical box dispatched to generic coordinate LPs")

    monkeypatch.setattr(
        problem, "polytope_support_and_exact_start", no_generic_maximizers
    )
    specialized = general_keyrate.solve_general_declaration(
        declaration, QicsSectorChoiOracle(), options=options
    )
    assert specialized.status == generic.status
    assert specialized.withdrawal == generic.withdrawal
    assert specialized.objective == pytest.approx(generic.objective, abs=1e-13)
    assert specialized.gap == pytest.approx(generic.gap, abs=1e-13)
    assert specialized.h_lb == pytest.approx(generic.h_lb, abs=1e-13)
    assert specialized.q == pytest.approx(generic.q, abs=1e-13)


@pytest.mark.parametrize("first_module", ["types", "problem", "assessment", "solve"])
def test_generic_solver_modules_import_first_in_a_fresh_process(
    first_module: str,
) -> None:
    code = (
        f"import certiqs_key.solvers.{first_module}; "
        "import certiqs_key.solvers.frank_wolfe as fw; "
        "assert all(getattr(fw, name) is not None for name in fw.__all__)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr
