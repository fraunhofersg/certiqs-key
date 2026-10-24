"""``h_low`` from the solver, against the FROZEN analytic-limit oracles.

Every expected value is ``tests/oracles/registry.py``'s, unmodified. These are
the end-to-end checks that "the solver returns the expected
value on the dummy bundle, agrees with the oracles inside recorded
tolerances, and reports ``estimate``".

TOLERANCE, RECORDED
-------------------
``SOLVER = 1e-8`` absolute, for every value produced by a Frank-Wolfe run. Two
things sit between the closed form and the returned number, and both are
bounded well below it:

* the Frank-Wolfe step is capped at ``1 - 1e-10`` so that an iterate never lands
  ON the boundary of the PSD cone, where the next gradient would not exist
  (Theorem ``thm:gradient`` (ii)). At a vertex minimizer this leaves a residual
  of order ``1e-10`` times the local slope;
* the linear oracle solves each subproblem to ``1e-10``, so its returned vertex
  is feasible and optimal to about that.

The largest deviation observed across the toys and the alpha grid is ``2e-9``
(TOY-6 at ``alpha = 1.05``, three sectors). ``1e-8`` leaves a factor of five and
is still two orders of magnitude tighter than any difference the oracles are
meant to detect -- the smallest of which is a whole bit.
"""

from __future__ import annotations

import math

import pytest
from dummy_bundles import build_bundle
from registry import ALPHA_GRID, O_HLOW_DEPHASED_TABLE, oracle
from toy_admission import REFUSED_AT_1_0_0, is_refused
from toy_declarations import toy

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core.declaration.admission import AdmissionError
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.solvers.frank_wolfe import solve
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

SOLVER = 1e-8

pytestmark = pytest.mark.requires_qics


def run(toy_id: str, alpha: float):
    """Return the ``KeyRateResult`` of a frozen toy at one Renyi order."""
    declaration = declaration_from_bundle(build_bundle(toy(toy_id)))
    return solve(declaration, QicsSectorChoiOracle(), alpha=alpha)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize(("count", "expected"), O_HLOW_DEPHASED_TABLE)
def test_o_hlow_fully_dephased(alpha: float, count: int, expected: float) -> None:
    """O-HLOW-FULLY-DEPHASED: h_low = log2(m) exactly, at every alpha."""
    entry = oracle("O-HLOW-FULLY-DEPHASED")
    assert entry.claims == ("C5", "C8")
    # TOY-3(m=3) IS REFUSED AT 1.0.0 and the refusal is recorded in
    # tests/support/toy_admission.py with its arithmetic: three declared
    # entries fl(1/3) whose COMPUTED declared-order sum is exactly 1.0 and
    # whose REAL sum is 1 - 2^-54, so condition (S) of Definition
    # def:optol refuses it at every tau_num. The frozen VALUE below is
    # unchanged as mathematics -- it is a statement about the real number
    # 1/3 -- and what 1.0.0 withdraws is this module's claim to compute it
    # FROM THIS DECLARATION.
    if is_refused(f"TOY-3(m={count})"):
        with pytest.raises(AdmissionError) as raised:
            run(f"TOY-3(m={count})", alpha)
        assert str(raised.value.reason) == REFUSED_AT_1_0_0[f"TOY-3(m={count})"]
        return
    result = run(f"TOY-3(m={count})", alpha)
    assert result.h_low == pytest.approx(expected, abs=SOLVER)
    # The run carries no compiled token, so its key length is withheld and it
    # reports the estimate; the achieved tier is first-order whatever the
    # certified evaluation found, the certified tier being achieved only where
    # the run is reported at it (the frank-wolfe interface's
    # optimizer_certificate row).
    assert result.assurance is Assurance.FIRST_ORDER


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_hlow_deterministic(alpha: float) -> None:
    """O-HLOW-DETERMINISTIC: a deterministic raw key gives exactly zero."""
    entry = oracle("O-HLOW-DETERMINISTIC")
    assert entry.value == 0.0
    result = run("TOY-2", alpha)
    assert result.h_low == pytest.approx(0.0, abs=SOLVER)
    # Zero is the CORRECT answer: a small positive number would overstate the key.
    assert result.h_low >= 0.0


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_hlow_zero_generation(alpha: float) -> None:
    """O-HLOW-ZERO-GENERATION: no key rounds and no penalty gives zero."""
    assert oracle("O-HLOW-ZERO-GENERATION").value == 0.0
    result = run("TOY-4a", alpha)
    assert result.h_low == pytest.approx(0.0, abs=SOLVER)
    # NO BLOCK CONTRIBUTES. The record lists the
    # key-ACTIVE joint pairs only -- a key-inert pair's deficit is exactly zero
    # (lem:joint-sectors (iii)) and is skipped, not formed -- and with no key
    # rounds there is none, so every deficit there is, is zero.
    contributions = result.block_contributions["chat0"]
    assert all(value == 0.0 for value in contributions.values())
    assert not result.sector_report["joint_pairs"].get("chat0")


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_hlow_retention_costs_exactly_one_bit(alpha: float) -> None:
    """O-HLOW-RETENTION: dropping a constraint-active sector costs one bit.

    The dangerous direction, priced. The solver keeps every declared sector and
    returns ``0``; the declaration that has already lost the constraint-active
    sector returns ``1``. There is no code path that performs the drop -- it is
    exhibited here by handing the solver a DIFFERENT declaration, which is what
    an engine that pruned the sector would effectively be solving.
    """
    assert oracle("O-HLOW-RETENTION").value == 0.0
    retained = run("TOY-1", alpha)
    assert retained.h_low == pytest.approx(0.0, abs=SOLVER)

    dropped = run("TOY-2-AVG", alpha)  # TOY-1's key-active sector alone
    assert dropped.h_low == pytest.approx(1.0, abs=SOLVER)
    assert dropped.h_low - retained.h_low == pytest.approx(1.0, abs=SOLVER)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_hlow_no_averaging_costs_exactly_one_bit(alpha: float) -> None:
    """O-HLOW-NO-AVERAGING: merging two sectors overstates the key by a bit."""
    assert oracle("O-HLOW-NO-AVERAGING").value == 0.0
    original = run("TOY-2", alpha)
    averaged = run("TOY-2-AVG", alpha)
    assert original.h_low == pytest.approx(0.0, abs=SOLVER)
    assert averaged.h_low == pytest.approx(1.0, abs=SOLVER)
    assert averaged.h_low - original.h_low == pytest.approx(1.0, abs=SOLVER)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_hlow_constrained_closed_form(alpha: float) -> None:
    """O-HLOW-CONSTRAINED: the alpha-dependent closed form on TOY-5."""
    entry = oracle("O-HLOW-CONSTRAINED")
    assert entry.claims == ("C8", "C9b", "C17")
    assert entry.closed_form is not None
    expected = dict(entry.frozen_values)[alpha]
    result = run("TOY-5", alpha)
    assert result.h_low == pytest.approx(expected, abs=SOLVER)
    assert result.h_low == pytest.approx(entry.closed_form(alpha), abs=SOLVER)
    # h_low(L) >= h_low({}): the constrained inner set is smaller.
    assert result.h_low > run("TOY-1", alpha).h_low


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_hlow_removal_leaves_the_value_alone(alpha: float) -> None:
    """O-HLOW-REMOVAL: TOY-6 and TOY-5 share a NON-ZERO value."""
    entry = oracle("O-HLOW-REMOVAL")
    assert entry.claims == ("C10",)
    expected = dict(entry.frozen_values)[alpha]
    with_extra = run("TOY-6", alpha)
    without = run("TOY-5", alpha)
    assert with_extra.h_low == pytest.approx(expected, abs=SOLVER)
    assert without.h_low == pytest.approx(expected, abs=SOLVER)
    assert with_extra.h_low == pytest.approx(without.h_low, abs=SOLVER)
    assert expected > 0.4  # an equality at zero would pass for almost any bug


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_hlow_divergence_only(alpha: float) -> None:
    """O-HLOW-DIVERGENCE-ONLY: finite, positive, and divergent as alpha -> 1+."""
    entry = oracle("O-HLOW-DIVERGENCE-ONLY")
    assert entry.closed_form is not None
    result = run("TOY-4b", alpha)
    assert result.h_low == pytest.approx(entry.closed_form(alpha), abs=SOLVER)
    assert math.isfinite(result.h_low)
    assert result.h_low > 0.0


@pytest.mark.contract
@pytest.mark.oracle
def test_h_low_is_never_negative_across_the_registry() -> None:
    """Remark rem:hlow-range: the objective is non-negative wherever it is finite."""
    for toy_id in (
        "TOY-1",
        "TOY-2",
        "TOY-2-AVG",
        "TOY-3(m=2)",
        "TOY-4a",
        "TOY-4b",
        "TOY-5",
        "TOY-6",
        "TOY-7",
    ):
        for alpha in (1.05, 1.9):
            assert run(toy_id, alpha).h_low >= -SOLVER
