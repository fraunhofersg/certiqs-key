"""The corrective search on a declaration with constraint rows (licensed route).

Under method auto on the BBM92 licensed route (FSS constraint rows) at
cutoff 2 and 3, both corrective stages could end in numerical_failure and give
no key. Two causes would be possible, both in the search's own arithmetic,
none in a claim (every candidate is certified by solvers/assessment.py):

* with constraint rows the anchor is the QICS zero-cost vertex; an SLSQP
  trial that puts zero weight on it keeps it only through
  ``CorrectiveSettings.blend``, and at 1e-10 a kept key-active pair fell
  below H-SUPP^D's 1e-12 relative rank cutoff (``frank-wolfe/cor:fo-dropped``).
  A series starts at 1e-10 and moves to 1e-6 after such a refusal
  (``search/common.py`` SUPPORT_FALLBACK_BLEND, ``solve.py`` THE BLEND);
* the search's own oracle call returns QICS ``near_optimal`` and the search
  takes the atom, while the assessor's calls stay strict.

The toy anchor's eigenvalues are large (about 0.17), so the first test mixes
it toward a vertex until its smallest eigenvalue is about 5e-3, as the BBM92
anchor's is at cutoff 2 (5.77e-3): there 1e-10 fails and the fallback passes.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import pytest
from tests.support.general_toys import two_factor_general

from certiqs_key.meat_core.errors import MeatError
from certiqs_key.solvers.frank_wolfe.joint_driver import _oracle_vertex
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle
from certiqs_key.solvers.problem import PreparedProblem, prepare_problem
from certiqs_key.solvers.search import corrective as corrective_module
from certiqs_key.solvers.search import stable
from certiqs_key.solvers.search.common import (
    SUPPORT_FALLBACK_BLEND,
    CorrectiveSettings,
)
from certiqs_key.solvers.search.corrective import mixture, search_corrective

pytestmark = pytest.mark.requires_qics


def _rows_problem() -> PreparedProblem:
    problem = prepare_problem(
        two_factor_general(party_local=False), QicsSectorChoiOracle()
    )
    assert problem.maps.declaration.constraint_list
    return problem


def _vertex(problem: PreparedProblem) -> dict[Any, Any]:
    """Return a rank-deficient extreme point of the constrained feasible set."""
    rng = np.random.default_rng(0)
    cost = {}
    for pair, block in problem.anchor.items():
        m = rng.normal(size=block.shape) + 1j * rng.normal(size=block.shape)
        cost[pair] = (m + m.conj().T) / 2
    vertex, optimal = _oracle_vertex(
        problem.maps,
        problem.oracle,
        cost,
        [],
        problem.rows,
        assignment=problem.assignment,
        spectral=problem.spectral,
    )
    assert optimal
    assert min(np.linalg.matrix_rank(b, tol=1e-9) < b.shape[0] for b in vertex.values())
    return vertex


def test_a_mixture_with_zero_anchor_weight_keeps_full_rank() -> None:
    problem = _rows_problem()
    vertex = _vertex(problem)
    anchor = {p: 0.97 * vertex[p] + 0.03 * problem.anchor[p] for p in vertex}
    smallest = min(float(np.linalg.eigvalsh(b)[0]) for b in anchor.values())
    assert 1e-3 < smallest < 1e-2  # the BBM92 anchor's scale at cutoff 2
    small = replace(problem, anchor=anchor)

    def evaluate(blend: float) -> None:
        atom = {p: (1 - blend) * vertex[p] + blend * anchor[p] for p in vertex}
        # An SLSQP trial with zero weight on atom 0, the anchor itself.
        stable.evaluate(small, mixture([anchor, atom], np.array([0.0, 1.0])))

    evaluate(SUPPORT_FALLBACK_BLEND)
    # The default a series starts at refuses here, which is what moves a
    # series to the fallback (solve.py, THE BLEND).
    assert CorrectiveSettings().blend == 1e-10
    with pytest.raises(MeatError, match="H-SUPP"):
        evaluate(CorrectiveSettings().blend)


def test_a_near_optimal_search_atom_is_taken(monkeypatch: Any) -> None:
    problem = _rows_problem()
    real = corrective_module._oracle_vertex

    def near(*args: Any, **kwargs: Any) -> Any:
        calls = args[3]
        vertex, _ = real(*args, **kwargs)
        for call in calls:
            call["sol_status"] = "near_optimal"
        return vertex, False

    monkeypatch.setattr(corrective_module, "_oracle_vertex", near)
    outcome = search_corrective(problem, settings=CorrectiveSettings(max_iterations=1))
    assert outcome.termination != "numerical_failure", outcome.diagnostics
    assert outcome.iterations == 1


def test_an_unsolved_search_atom_is_still_refused(monkeypatch: Any) -> None:
    problem = _rows_problem()
    real = corrective_module._oracle_vertex

    def unknown(*args: Any, **kwargs: Any) -> Any:
        calls = args[3]
        vertex, _ = real(*args, **kwargs)
        for call in calls:
            call["sol_status"] = "unknown"
        return vertex, False

    monkeypatch.setattr(corrective_module, "_oracle_vertex", unknown)
    outcome = search_corrective(problem, settings=CorrectiveSettings(max_iterations=1))
    assert outcome.termination == "numerical_failure"
    assert "did not report optimality" in outcome.diagnostics["message"]


def test_the_support_margin_shows_the_thinning_direction() -> None:
    """The diagnostic reads what H-SUPP^D tests, against 1e-12."""
    problem = _rows_problem()
    vertex = _vertex(problem)
    anchor = {p: 0.97 * vertex[p] + 0.03 * problem.anchor[p] for p in vertex}
    small = replace(problem, anchor=anchor)

    def margin(blend: float) -> dict[str, Any]:
        atom = {p: (1 - blend) * vertex[p] + blend * anchor[p] for p in vertex}
        point = mixture([anchor, atom], np.array([0.0, 1.0]))
        found = stable.support_margin(small, point)
        assert found is not None
        return found

    assert stable.support_margin(problem, problem.anchor)["margin_factor"] > 1e6
    held, refused = margin(SUPPORT_FALLBACK_BLEND), margin(1e-10)
    assert held["cutoff"] == refused["cutoff"] == 1e-12
    assert held["margin_factor"] > 1 > refused["margin_factor"]
    thinnest = "smallest_relative_eigenvalue"
    assert held[thinnest] > refused[thinnest]
