"""The rows Lemma D reads: exact data, and the oracle's own layout.

CONTRACT TESTS of ``meat-core/frank-wolfe/req:verified-feasible-side`` (i)
and ``lem:feasible-side-dual`` (ii)(a), (b). Each test here fails on a mutant
of the clause it pins.

* EXACT DATA. ``Theta_k = c_k tau`` and ``D = O - c_k
  1`` are formed exactly from the declaration, never as the binary64 products
  the oracle is handed. The declaration is chosen so that those products
  round (``tau = diag(3/8, 5/8)``, ``c_k = 0.1``), which no other test
  declaration does.
* THE LAYOUT. The residual ``R_s = G_s - Y (x) 1 -
  sum_r sigma_r L*_r(Lambda_r)`` must be ``G_s - sum_i m_i A_i``, the oracle
  boundary's own equations weighted by the same multipliers: ``Y (x) 1`` with
  the input factor first, ``(W~^dagger Lambda W~) (x) O^{up(s)}``, and the
  party-local ``L*`` with the scoped factor placed between the others
  (scoped and right both 2, so the arrangement matters), in untrusted- and in
  trusted-source mode through ``W~ (x) 1``. The residuals are captured where
  the evaluator hands them to the eigenvalue bound.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from typing import Any

import numpy as np
import pytest
from tests.support.general_toys import qubit_bb84_general, two_factor_general

from certiqs_key.domain.manifest import ConstraintRelation
from certiqs_key.meat_core.declaration.general import (
    AliceFactor,
    GeneralConstraintEntry,
    GeneralDeclaration,
    GeneralRhsTag,
    PartyLabel,
)
from certiqs_key.meat_core.objective.joint import joint_choi_parametrization
from certiqs_key.solvers.frank_wolfe import verified
from certiqs_key.solvers.frank_wolfe.verified import GroupSolve, _group_bound
from certiqs_key.solvers.oracles.joint_rows import (
    joint_program_for_alice_sector,
    joint_program_untrusted,
)
from certiqs_key.solvers.oracles.protocol import (
    OracleDual,
    dual_from_equations,
    row_equations,
)

pytestmark = pytest.mark.contract

#: A diagonal marginal whose square roots and products with 0.1 round.
TAU = np.diag([0.375, 0.625]).astype(np.complex128)


def _qubit_with(entry: GeneralConstraintEntry) -> GeneralDeclaration:
    return replace(
        qubit_bb84_general(), alice_marginal={"t0": TAU}, constraint_list=(entry,)
    )


def _capture(monkeypatch: pytest.MonkeyPatch) -> list[np.ndarray]:
    """Record every matrix the evaluator hands the eigenvalue bound."""
    captured: list[np.ndarray] = []

    def capture(matrix: verified.DyadicMatrix, **_: Any) -> Fraction:
        captured.append(matrix.to_complex())
        return Fraction(0)

    monkeypatch.setattr(verified, "least_eigenvalue_bound", capture)
    return captured


# ---------------------------------------------------------------------------
#  The rows from exact data
# ---------------------------------------------------------------------------


def test_theta_is_the_exact_product_c_k_tau() -> None:
    entry = GeneralConstraintEntry(
        scope="f0",
        operator_blocks={"q": np.diag([0.75, 0.25]).astype(np.complex128)},
        relation=ConstraintRelation.PRECEQ,
        bound=0.1,
        rhs_tag=GeneralRhsTag.HOMOGENEOUS,
    )
    parametrization = joint_choi_parametrization(_qubit_with(entry))
    # The binary64 product the oracle is handed rounds here.
    assert Fraction(0.1 * 0.375) != Fraction(0.1) * Fraction(0.375)
    (row,) = verified._groups(parametrization)["t0"].lifted
    assert isinstance(row.theta, verified.DyadicMatrix)
    for i, t in enumerate((0.375, 0.625)):
        assert row.theta.entry(i, i) == (Fraction(0.1) * Fraction(t), Fraction(0))
    assert row.theta.entry(0, 1) == (Fraction(0), Fraction(0))


def test_the_party_local_deviation_is_formed_exactly() -> None:
    entry = GeneralConstraintEntry(
        scope="f0",
        operator_blocks={"q": np.diag([0.75, 0.25]).astype(np.complex128)},
        relation=ConstraintRelation.PRECEQ,
        bound=0.1,
        rhs_tag=GeneralRhsTag.PARTY_LOCAL,
    )
    parametrization = joint_choi_parametrization(_qubit_with(entry))
    # The binary64 difference the oracle is handed rounds here.
    assert Fraction(0.75 - 0.1) != Fraction(0.75) - Fraction(0.1)
    (row,) = verified._groups(parametrization)["t0"].party_local
    ((deviation, _),) = row.blocks.values()
    for i, o in enumerate((0.75, 0.25)):
        assert deviation.entry(i, i) == (Fraction(o) - Fraction(0.1), Fraction(0))


# ---------------------------------------------------------------------------
#  The layout of the multiplier terms is the oracle's
# ---------------------------------------------------------------------------


def test_the_coupling_and_lifted_row_residual_is_the_oracles_encoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``Y (x) 1`` and ``(W~^dagger Lambda W~) (x) O`` against ``G - sum m_i A_i``."""
    operator = np.array([[0.75, 0.125 - 0.25j], [0.125 + 0.25j, 0.25]])
    entry = GeneralConstraintEntry(
        scope="f0",
        operator_blocks={"q": operator},
        relation=ConstraintRelation.EQ,
        bound=0.1,
        rhs_tag=GeneralRhsTag.HOMOGENEOUS,
    )
    parametrization = joint_choi_parametrization(_qubit_with(entry))
    rng = np.random.default_rng(3)
    gradient = {}
    for pair in parametrization.joint_sectors:
        size = parametrization.block_dim(pair)
        sample = rng.normal(size=(size, size)) + 1j * rng.normal(size=(size, size))
        gradient[pair] = (sample + sample.conj().T) / 2
    problem = joint_program_for_alice_sector(parametrization, "t0", gradient)
    coupling = list(problem.coupling_equations())
    rows = [list(row_equations(row, problem.input_dim)) for row in problem.rows]
    weights = rng.normal(size=len(coupling) + sum(len(eqs) for eqs in rows))
    dual = dual_from_equations(problem, weights)
    captured = _capture(monkeypatch)
    group = verified._groups(parametrization)["t0"]
    _group_bound(group, gradient, GroupSolve(problem, dual), "t0")
    assert len(captured) == len(group.pairs)
    for (label, pair), residual in zip(group.pairs.items(), captured, strict=True):
        dim = problem.block_dims[label]
        expected = np.array(gradient[pair], dtype=np.complex128)
        for weight, (element, _) in zip(
            weights[: len(coupling)], coupling, strict=True
        ):
            expected -= weight * np.kron(element, np.eye(dim))
        offset = len(coupling)
        for row, equations in zip(problem.rows, rows, strict=True):
            for weight, (element, _) in zip(
                weights[offset : offset + len(equations)], equations, strict=True
            ):
                expected -= weight * np.kron(element, row.blocks[label])
            offset += len(equations)
        assert np.allclose(residual, expected, atol=1e-9), label


def _party_local_at_the_first_factor(operator: np.ndarray) -> GeneralConstraintEntry:
    """Scoped at the FIRST of two factors: scoped = right = 2."""
    return GeneralConstraintEntry(
        scope="fA",
        operator_blocks={"qA": operator},
        relation=ConstraintRelation.EQ,
        bound=0.25,
        rhs_tag=GeneralRhsTag.PARTY_LOCAL,
    )


def _expected_party_local(problem: Any, weights: Any, label: str) -> np.ndarray:
    """``-sum_i m_i C_i`` over the general rows' coefficients on one block."""
    total = 0
    for row, row_weights in zip(problem.general_rows, weights, strict=True):
        for weight, coefficient in zip(row_weights, row.coefficients, strict=True):
            if label in coefficient:
                total = total - weight * coefficient[label]
    return np.asarray(total, dtype=np.complex128)


def test_the_untrusted_party_local_residual_is_the_oracles_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = _party_local_at_the_first_factor(np.array([[0.75, 0.25j], [-0.25j, 0.125]]))
    declaration = replace(
        two_factor_general(party_local=True), constraint_list=(entry,)
    )
    parametrization = joint_choi_parametrization(declaration)
    assert not declaration.is_trusted_source
    gradient = {
        pair: np.zeros((parametrization.block_dim(pair),) * 2, dtype=np.complex128)
        for pair in parametrization.joint_sectors
    }
    problem = joint_program_untrusted(parametrization, gradient)
    rng = np.random.default_rng(5)
    weights = tuple(
        rng.normal(size=len(row.coefficients)) for row in problem.general_rows
    )
    captured = _capture(monkeypatch)
    group = verified._groups(parametrization)["*"]
    dual = OracleDual(coupling=0.0, rows=(), general_rows=weights)
    _group_bound(group, gradient, GroupSolve(problem, dual), "*")
    assert len(captured) == len(group.pairs)
    for label, residual in zip(group.pairs, captured, strict=True):
        expected = _expected_party_local(problem, weights, label)
        assert np.allclose(residual, expected, atol=1e-9), label


def test_the_trusted_party_local_residual_is_the_oracles_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Through ``W~ (x) 1``, with ``W~`` the rounded root of a diagonal marginal."""
    base = two_factor_general(party_local=True)
    rng = np.random.default_rng(11)
    sample = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    entry = _party_local_at_the_first_factor(
        np.round((sample + sample.conj().T) / 2, 3)
    )
    declaration = replace(
        base,
        alice=AliceFactor(
            party=PartyLabel.ALICE,
            sectors=replace(base.alice.sectors, labels=("t0",), dims={"t0": 2}),
        ),
        alice_marginal={"t0": TAU},
        alice_operators={"*": {"t0": np.eye(2, dtype=np.complex128)}},
        constraint_list=(entry,),
    )
    assert declaration.is_trusted_source
    parametrization = joint_choi_parametrization(declaration)
    gradient = {
        pair: np.zeros((parametrization.block_dim(pair),) * 2, dtype=np.complex128)
        for pair in parametrization.joint_sectors
    }
    problem = joint_program_for_alice_sector(parametrization, "t0", gradient)
    weights = tuple(
        rng.normal(size=len(row.coefficients)) for row in problem.general_rows
    )
    dual = OracleDual(
        coupling=np.zeros((problem.input_dim,) * 2, dtype=np.complex128),
        rows=(),
        general_rows=weights,
    )
    group = verified._groups(parametrization)["t0"]
    # The frame is rounded, so the evaluator charges it rather than zeroing the
    # rows: the multipliers do enter the residual.
    assert group.frame_error is not None and group.frame_error > 0
    captured = _capture(monkeypatch)
    _group_bound(group, gradient, GroupSolve(problem, dual), "t0")
    assert len(captured) == len(group.pairs)
    for label, residual in zip(group.pairs, captured, strict=True):
        expected = _expected_party_local(problem, weights, label)
        assert np.allclose(residual, expected, atol=1e-9), label
