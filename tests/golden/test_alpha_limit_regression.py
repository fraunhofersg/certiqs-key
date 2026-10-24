"""The ``alpha -> 1+`` regression of C16, against the FROZEN limit table.

The design notes of meat-core, section 'Validation against the order-one
limit', call this a regression test and say what it is worth:
"Driving ``alpha -> 1+`` in an implementation of Eq. ``eq:choi-program`` and
comparing against either reference value on the same declaration is a regression
test; disagreement is a defect in the implementation, never a research
question." It does not certify (C13) and it does not validate finite-``alpha``
values.

Two independent numbers are compared for each entry of ``O_ALPHA_LIMIT_TABLE``:

1. the blockwise relative-entropy program of Eq. ``eq:oracle``, evaluated at the
   ``Feas_1`` witness the registry records -- which the registry's own
   derivation identifies as the minimizer;
2. ``h_low(1 + eps)`` from the solver, at a sequence of shrinking ``eps``.

TOLERANCES, RECORDED
--------------------
``1e-12`` for (1) against the frozen ``h_1``: a handful of eigen-decompositions
of matrices of order one.

For (2) the comparison is against the CONVERGENCE, not against a fixed
tolerance, because the limit is approached at first order in ``eps``: the test
requires the error to fall by at least a factor of five per decade of ``eps``
and to reach ``1e-5`` at ``eps = 1e-4``. On TOY-5 the observed error is
``0.0866 * eps``, i.e. exactly first order with the coefficient the registry's
own expansion predicts.
"""

from __future__ import annotations

import itertools
from dataclasses import replace

import numpy as np
import pytest
from dummy_bundles import build_bundle
from mode_bundles import build_bundle as build_mode_bundle
from polytope_toys import polytope_toy
from registry import C16_EXTRA_HYPOTHESES, O_ALPHA_LIMIT_TABLE, oracle
from toy_admission import REFUSED_AT_1_0_0, is_refused
from toy_declarations import toy

from certiqs_key.meat_core.declaration.admission import AdmissionError
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    PolytopeData,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.errors import HypothesisError, UnsupportedDeclarationError
from certiqs_key.meat_core.objective.branch import generate_maps
from certiqs_key.meat_core.objective.limit import (
    check_limit_hypotheses,
    limit_objective,
)

#: The ``Feas_1`` witnesses of ``O_ALPHA_LIMIT_TABLE``, transcribed from its
#: fifth column: "omega = diag(...)" in the sector-weight parametrization.
WITNESSES: dict[str, dict[str, float]] = {
    "TOY-1": {"s0": 0.0, "s1": 1.0},
    "TOY-3(m=2)": {"s0": 1.0},
    "TOY-5": {"s0": 0.5, "s1": 0.5},
}


def declaration_of(toy_id: str) -> ProtocolDeclaration:
    """Return the validated declaration of a frozen toy."""
    return declaration_from_bundle(build_bundle(toy(toy_id)))


def state_of(
    declaration: ProtocolDeclaration, point: dict[str, float]
) -> dict[str, np.ndarray]:
    """Return the block-diagonal state of a sector weighting."""
    return {
        sector: np.array([[point[sector]]], dtype=np.complex128)
        for sector in declaration.sector_index_set
    }


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("row", O_ALPHA_LIMIT_TABLE, ids=lambda row: row[0])
def test_the_limit_program_reproduces_the_frozen_h1(
    row: tuple[str, float, float, float, str],
) -> None:
    """Eq. eq:oracle evaluated at the recorded Feas_1 witness equals ``h_1``."""
    toy_id, h1, limit, p0, _witness_text = row
    # TOY-3(m=3) IS REFUSED AT 1.0.0 by condition (S) -- three declared
    # fl(1/3) entries whose COMPUTED sum is exactly the identity and whose
    # REAL sum is 1 - 2^-54 (tests/support/toy_admission.py). The FROZEN
    # ROW STANDS as mathematics; what is withdrawn is this module's claim
    # to compute it from that declaration, and the refusal is asserted
    # rather than skipped.
    if is_refused(toy_id):
        with pytest.raises(AdmissionError) as raised:
            declaration_of(toy_id)
        assert str(raised.value.reason) == REFUSED_AT_1_0_0[toy_id]
        return
    assert h1 == pytest.approx(limit)
    declaration = declaration_of(toy_id)
    maps = generate_maps(declaration)
    witness = state_of(declaration, WITNESSES[toy_id])
    assert check_limit_hypotheses(maps, witness) == pytest.approx(p0)
    assert limit_objective(maps, witness) == pytest.approx(h1, abs=1e-12)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
@pytest.mark.parametrize("row", O_ALPHA_LIMIT_TABLE, ids=lambda row: row[0])
def test_h_low_converges_to_the_limit_program(
    row: tuple[str, float, float, float, str],
) -> None:
    """O-ALPHA-LIMIT: h_low(alpha) -> h_1 as alpha -> 1+, at first order."""
    from certiqs_key.solvers.frank_wolfe import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    assert oracle("O-ALPHA-LIMIT").claims == ("C16",)
    toy_id, h1, _limit, _p0, _witness = row
    # TOY-3(m=3) IS REFUSED AT 1.0.0 by condition (S) -- three declared
    # fl(1/3) entries whose COMPUTED sum is exactly the identity and whose
    # REAL sum is 1 - 2^-54 (tests/support/toy_admission.py). The FROZEN
    # ROW STANDS as mathematics; what is withdrawn is this module's claim
    # to compute it from that declaration, and the refusal is asserted
    # rather than skipped.
    if is_refused(toy_id):
        with pytest.raises(AdmissionError) as raised:
            declaration_of(toy_id)
        assert str(raised.value.reason) == REFUSED_AT_1_0_0[toy_id]
        return
    declaration = declaration_of(toy_id)
    solver = QicsSectorChoiOracle()

    errors = []
    for epsilon in (1e-2, 1e-3, 1e-4):
        value = solve(declaration, solver, alpha=1.0 + epsilon).h_low
        errors.append(abs(value - h1))
    assert errors[-1] < 1e-5
    for previous, current in itertools.pairwise(errors):
        # First-order convergence: a decade in eps buys at least a factor five,
        # with a floor at 1e-8 for the toys whose h_low is alpha-INDEPENDENT --
        # there the error is already solver noise and has nothing left to
        # converge.
        assert current <= max(previous / 5.0, 1e-8)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_extra_hypotheses_are_enforced_not_assumed() -> None:
    """O-ALPHA-LIMIT-HYPOTHESIS-FAILS: an unreachable acceptance set is refused."""
    entry = oracle("O-ALPHA-LIMIT-HYPOTHESIS-FAILS")
    assert entry.toy_id == "TOY-4b"
    assert len(C16_EXTRA_HYPOTHESES) == 2

    declaration = declaration_of("TOY-4b")
    maps = generate_maps(declaration)
    witness = {"s0": np.array([[1.0]], dtype=np.complex128)}
    with pytest.raises(HypothesisError, match="H2"):
        check_limit_hypotheses(maps, witness)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
def test_the_refused_declaration_really_does_diverge() -> None:
    """On TOY-4b, h_low(alpha) grows without bound as alpha -> 1+.

    Which is why refusing the comparison is the conforming behaviour rather
    than a missing feature: there is no finite value to converge to.
    """
    from certiqs_key.solvers.frank_wolfe import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    declaration = declaration_of("TOY-4b")
    solver = QicsSectorChoiOracle()
    values = [
        solve(declaration, solver, alpha=1.0 + epsilon).h_low
        for epsilon in (1e-1, 1e-2, 1e-3)
    ]
    assert values[0] < values[1] < values[2]
    assert values[-1] > 200.0


@pytest.mark.contract
def test_a_key_inert_branch_contributes_nothing_to_the_limit() -> None:
    """Proposition prop:exact-cancellation inside Eq. eq:oracle.

    A Z-invariant branch gives zero.
    """
    declaration = declaration_of("TOY-2")
    maps = generate_maps(declaration)
    for share in (0.0, 0.25, 0.5, 1.0):
        witness = state_of(declaration, {"s0": share, "s1": 1.0 - share})
        assert limit_objective(maps, witness) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.contract
def test_the_limit_oracle_meets_a_polytope_declaration_without_an_untyped_error() -> (
    None
):
    """Theorem thm:oracle's hypotheses are stated over the WHOLE acceptance set.

    "(H1) a uniform floor p_0 > 0 on q(chat) over the whole acceptance set" and
    "(H2) Feas_1 = {omega in Feas : Phi[omega] in AcceptSet}" -- both quantify
    over ``AcceptSet``, not over one declared vector. A declaration may carry
    a set that is not a point, and this oracle is a consumer of the acceptance
    set: ``acceptance_vector`` zips the acceptance alphabet against
    ``frequencies``, which is EMPTY for a polytope, so ``strict=True`` would
    raise a bare ``ValueError`` before either hypothesis was
    examined.

    THE FIRST ASSERTION DECIDES NOTHING THE CONTRACT LEAVES OPEN. Two answers
    are conforming -- decide (H1) and (H2) over the declared set, or refuse the
    comparison with the typed error this module documents -- and either raises
    one of the two types below. What is excluded is the third: an untyped
    exception from a zip, where every other refusal in this module names its
    check. The SECOND assertion pins the answer this implementation gives,
    having taken the first road (``check_limit_hypotheses`` records why).

    On TOY-8-T-POLY the refusal is the truthful answer either way, and the
    declaration is worth using precisely because it is: its feasible set is the
    single point ``omega = tau_A`` with ``Phi[omega] = (7/8, 1/8)``, while the
    declared box caps ``q(chat0)`` at ``3/4``. So ``Feas_1`` is EMPTY, (H2)
    genuinely fails, and ``h_low`` carries the ``alpha/(alpha-1)`` prefactor
    that diverges as ``alpha -> 1+`` -- exactly the situation thm:oracle
    excludes by hypothesis. A run reaching a finite limit here would be the
    defect.
    """
    declaration = declaration_from_bundle(build_mode_bundle(polytope_toy()))
    assert declaration.acceptance_set.geometry == "polytope"
    maps = generate_maps(declaration)
    # TOY-8-T-POLY's feasible set is the single point omega = tau_A.
    witness = {"s0": np.diag([0.875 + 0.0j, 0.125 + 0.0j])}
    with pytest.raises((HypothesisError, UnsupportedDeclarationError)) as raised:
        check_limit_hypotheses(maps, witness)
    # It names the hypothesis that fails on this declaration, not the geometry:
    # the set is read, and what is wrong with it is that nothing feasible meets
    # it.
    assert "H2" in str(raised.value)


@pytest.mark.contract
def test_the_hypotheses_are_decided_over_a_polytope_that_is_reachable() -> None:
    """(H1) and (H2) on a declared set that is not a point, and both answer.

    The companion to the refusal above: there the polytope is unreachable and
    the conforming answer is to refuse, so nothing exercises the widened
    hypotheses in the direction where they HOLD. Here TOY-5's acceptance set --
    the single vector ``q* = (1)`` -- is re-declared as the canonical box
    ``q^- = q^+ = 1`` on the same one-element alphabet. The denotation
    ``{q >= 0, sum q = 1, q <= 1, -q <= -1}`` is the same one point, so both
    hypotheses must give TOY-5's own frozen answers through a different route:
    (H2) holds at the frozen ``Feas_1`` witness, and (H1)'s floor is the
    minimum over the set, which is that point's mass.

    The tag and not the data selects the route (``O-POLYTOPE-SINGLETON-
    AGREEMENT``), so this really does go through the linear program, and the
    frozen ``p_0`` is what it has to come back with.
    """
    row = next(entry for entry in O_ALPHA_LIMIT_TABLE if entry[0] == "TOY-5")
    _toy_id, h1, _limit, p0, _witness_text = row
    declaration = replace(
        declaration_of("TOY-5"),
        acceptance_set=AcceptanceSet(
            geometry="polytope",
            polytope=PolytopeData(
                columns=1,
                rows=((1.0,), (-1.0,)),
                rhs=(1.0, -1.0),
                box_bounds=((1.0,), (1.0,)),
            ),
        ),
    )
    maps = generate_maps(declaration)
    witness = state_of(declaration, WITNESSES["TOY-5"])
    assert check_limit_hypotheses(maps, witness) == pytest.approx(p0)
    assert limit_objective(maps, witness) == pytest.approx(h1, abs=1e-12)


@pytest.mark.contract
def test_a_polytope_whose_columns_do_not_match_the_alphabet_fails_closed() -> None:
    """The shape defect no declared bundle can carry, refused typed anyway.

    ``bundle._polytope`` takes ``columns`` from the acceptance alphabet, so a
    declaration parsed from an operator bundle cannot disagree with itself
    here. One built in memory can, and the answer must still be a typed refusal
    rather than the untyped exception a mismatched zip would raise -- which is
    the whole species of failure.
    """
    declaration = replace(
        declaration_of("TOY-4b"),
        acceptance_set=AcceptanceSet(
            geometry="polytope",
            polytope=PolytopeData(columns=1, rows=((1.0,),), rhs=(1.0,)),
        ),
    )
    maps = generate_maps(declaration)
    witness = {"s0": np.array([[1.0]], dtype=np.complex128)}
    with pytest.raises(UnsupportedDeclarationError, match="H1"):
        check_limit_hypotheses(maps, witness)
