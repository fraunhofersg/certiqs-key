"""C11 and C12: the oracles this run had to write itself.

The frozen registry deliberately pins neither claim, and a test there asserts
their absence: "an oracle for them would be the implementation written in the
test tree". Both now have an independent check that does not restate the
implementation's formulas.

* **C11 is checked against its own EXACTNESS claim.** Theorem ``thm:choi`` says
  the Choi program is an exact reformulation, not a relaxation. Both forms now
  exist, so the oracle is the identity between them: the bijection ``chi`` and
  its inverse round-trip, the coupling constraint corresponds to
  ``omega_A = tau_A``, the declared constraint list transfers, and the two
  objectives agree to machine precision at the same point.
* **C12 is checked against CENTRAL FINITE DIFFERENCES of the objective it
  differentiates.** The gradient formulas of Eq. ``eq:gradT`` and
  Eq. ``eq:grad-J`` are never re-implemented in the test; the objective is
  evaluated at ``x +/- eps H`` along random Hermitian directions and compared
  with ``<grad, H>``.

TOLERANCES, RECORDED
--------------------
``EXACT = 1e-13`` for the C11 identities: two call paths over the same numbers,
differing only by a congruence with ``W_tau`` and its inverse.

``FD = 1e-5`` relative for the finite-difference comparison at ``eps = 1e-6``.
A central difference has error ``O(eps^2 f''') + O(machine_eps / eps)``, i.e.
about ``1e-12 + 1e-10`` here, but the DIRECTION matrices are random with entries
of order one and the third derivative of ``t -> t^{1/alpha}`` near a small
eigenvalue is large, so the honest bar is a few orders above the ideal one.
Observed deviations are at ``1e-8``; nothing was widened to pass.
"""

from __future__ import annotations

import numpy as np
import pytest
from dummy_bundles import build_bundle
from toy_declarations import toy

from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.errors import DeclarationError, SupportError
from certiqs_key.meat_core.objective.branch import branch_operator, generate_maps
from certiqs_key.meat_core.objective.choi import (
    channel_action,
    check_declared_isometry,
    choi_objective_value,
    choi_parametrization,
    coupling_residual,
)
from certiqs_key.meat_core.objective.gradient import (
    choi_gradient,
    deficit_gradient,
    state_gradient,
    trace_power_gradient,
    z_invariant_face,
)
from certiqs_key.meat_core.objective.linalg import psd_power
from certiqs_key.meat_core.objective.objective import (
    acceptance_vector,
    check_feasible,
    objective_value,
)

EXACT = 1e-13
FD = 1e-5
STEP = 1e-6

#: Structural claims hold on (1, inf); the grid deliberately leaves the
#: key-length window (1, 2) at its last entry (req:key-length-alpha-domain).
ALPHAS = (1.05, 1.5, 1.9, 3.0)

POINTS = {
    "TOY-1": {"s0": 0.4, "s1": 0.6},
    "TOY-5": {"s0": 0.6, "s1": 0.4},
    "TOY-6": {"s0": 0.5, "s1": 0.3, "s2": 0.2},
}


def declaration_of(toy_id: str) -> ProtocolDeclaration:
    """Return the validated declaration of a frozen toy."""
    return declaration_from_bundle(build_bundle(toy(toy_id)))


def state_of(declaration: ProtocolDeclaration, point: dict[str, float]):
    """Return the block-diagonal state of a sector weighting."""
    return {
        sector: np.array([[point[sector]]], dtype=np.complex128)
        for sector in declaration.sector_index_set
    }


def random_hermitian(dimension: int, seed: int) -> np.ndarray:
    """Return a reproducible random Hermitian matrix."""
    generator = np.random.default_rng(seed)
    raw = generator.normal(size=(dimension, dimension)) + 1j * generator.normal(
        size=(dimension, dimension)
    )
    return np.asarray(0.5 * (raw + raw.conj().T), dtype=np.complex128)


# ---------------------------------------------------------------------------
# C11 -- the exactness oracle
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize("toy_id", sorted(POINTS))
def test_c11_chi_is_a_bijection_onto_the_fixed_marginal_set(toy_id: str) -> None:
    """Lemma lem:choi-marginal: chi and its inverse round-trip both ways."""
    declaration = declaration_of(toy_id)
    parametrization = choi_parametrization(declaration)
    omega = state_of(declaration, POINTS[toy_id])
    choi = parametrization.choi_from_state(omega)
    back = parametrization.state_from_choi(choi)
    for sector in declaration.sector_index_set:
        assert np.allclose(back[sector], omega[sector], atol=EXACT, rtol=0.0)
    # tr_Q J = 1_{A_0} is EQUIVALENT to omega_A = tau_A, not merely implied.
    assert coupling_residual(parametrization, choi) < EXACT
    check_feasible(declaration, omega)


@pytest.mark.contract
@pytest.mark.parametrize("toy_id", sorted(POINTS))
@pytest.mark.parametrize("alpha", ALPHAS)
def test_c11_the_choi_program_is_exact_not_a_relaxation(
    toy_id: str, alpha: float
) -> None:
    """Theorem thm:choi: the two forms agree at corresponding points."""
    declaration = declaration_of(toy_id)
    maps = generate_maps(declaration)
    parametrization = choi_parametrization(declaration)
    q = acceptance_vector(declaration)
    omega = state_of(declaration, POINTS[toy_id])
    choi = parametrization.choi_from_state(omega)
    assert choi_objective_value(maps, parametrization, q, choi, alpha) == pytest.approx(
        objective_value(maps, q, omega, alpha), abs=EXACT
    )


@pytest.mark.contract
def test_c11_ordering_convention_is_the_declared_one() -> None:
    """Remark rem:ordering: input factor first, transpose in the declared basis.

    The reading is checked on a Choi block whose channel is known by hand. With
    ``tau_A = 1_2/2``, the Choi block ``J = 1_2`` on ``A_0 x Q_s`` with
    ``d_s = 1`` is the trace map, so ``E(rho) = tr rho``: the ordering
    convention would fail this if the factors were transposed.
    """
    declaration = declaration_of("TOY-7")
    parametrization = choi_parametrization(declaration)
    choi = parametrization.choi_from_state(
        {"s0": np.asarray(declaration.alice_marginal, dtype=np.complex128)}
    )
    assert np.allclose(choi["s0"], np.eye(2), atol=EXACT)
    for rho in (
        np.eye(2, dtype=np.complex128) / 2.0,
        np.diag([1.0, 0.0]).astype(np.complex128),
        np.array([[0.5, 0.25], [0.25, 0.5]], dtype=np.complex128),
    ):
        action = channel_action(parametrization, "s0", choi["s0"], rho)
        assert action.shape == (1, 1)
        assert action[0, 0] == pytest.approx(np.trace(rho), abs=EXACT)


@pytest.mark.contract
def test_c11_accepts_a_singular_trusted_marginal_and_records_its_basis() -> None:
    """A singular ``tau_A`` is admissible input.

    Section 2.1 admits it and Section 2.5 says in so many words that an
    implementation "must NOT refuse a singular ``tau_A`` on the ground that the
    contract names no canonical basis, because the contract deliberately names
    none". What it must do instead is pick any orthonormal basis of
    ``supp tau_A`` and RECORD it. Both halves are checked here: the
    parametrization is built, ``iota`` satisfies Eq. ``eq:iota``, and
    ``records_input_basis`` is on precisely because ``rank tau_A < d_A``.
    """
    from dataclasses import replace

    declaration = replace(
        declaration_of("TOY-7"),
        alice_marginal=np.diag([1.0, 0.0]).astype(np.complex128),
    )
    parametrization = choi_parametrization(declaration)
    assert parametrization.input_dim == 1
    assert parametrization.records_input_basis is True

    iota = parametrization.iota
    assert iota is not None and iota.shape == (2, 1)
    check_declared_isometry(iota, declaration.trusted_marginal, 2)
    # W_tau W_tau^dagger = tau_A, Eq. eq:Wtau, is what the parametrization rests
    # on and is exact for a singular marginal too.
    assert np.allclose(
        parametrization.w_tau @ parametrization.w_tau.conj().T,
        declaration.trusted_marginal,
        atol=EXACT,
    )


@pytest.mark.contract
def test_c11_refuses_an_iota_that_is_not_a_basis_of_the_support() -> None:
    """Eq. ``eq:iota`` is the whole of what may be demanded of a declared basis.

    "ANY orthonormal basis of ``supp tau_A`` may be declared" -- and no other.
    An isometry onto the WRONG one-dimensional subspace is not an admissible
    choice, and accepting it would parametrize a different set of states.
    """
    from dataclasses import replace

    declaration = replace(
        declaration_of("TOY-7"),
        alice_marginal=np.diag([1.0, 0.0]).astype(np.complex128),
    )
    wrong = np.array([[0.0], [1.0]], dtype=np.complex128)
    with pytest.raises(DeclarationError, match="eq:iota"):
        choi_parametrization(declaration, iota=wrong)


# ---------------------------------------------------------------------------
# C12 -- the finite-difference oracle
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize("toy_id", sorted(POINTS))
@pytest.mark.parametrize("alpha", ALPHAS)
def test_c12_state_gradient_matches_central_differences(
    toy_id: str, alpha: float
) -> None:
    """Corollary cor:full-gradient, state form, against the objective itself."""
    declaration = declaration_of(toy_id)
    maps = generate_maps(declaration)
    q = acceptance_vector(declaration)
    omega = state_of(declaration, POINTS[toy_id])
    gradient = state_gradient(maps, q, omega, alpha)
    for index, sector in enumerate(declaration.sector_index_set):
        direction = random_hermitian(omega[sector].shape[0], seed=17 + index)
        plus = {**omega, sector: omega[sector] + STEP * direction}
        minus = {**omega, sector: omega[sector] - STEP * direction}
        difference = (
            objective_value(maps, q, plus, alpha)
            - objective_value(maps, q, minus, alpha)
        ) / (2.0 * STEP)
        analytic = float(np.real(np.trace(gradient.blocks[sector] @ direction)))
        assert difference == pytest.approx(analytic, rel=FD, abs=FD), (
            toy_id,
            alpha,
            sector,
        )


@pytest.mark.contract
@pytest.mark.parametrize("toy_id", sorted(POINTS))
@pytest.mark.parametrize("alpha", ALPHAS)
def test_c12_choi_gradient_matches_central_differences(
    toy_id: str, alpha: float
) -> None:
    """Eq. eq:grad-J, against the Choi-form objective."""
    declaration = declaration_of(toy_id)
    maps = generate_maps(declaration)
    parametrization = choi_parametrization(declaration)
    q = acceptance_vector(declaration)
    choi = parametrization.choi_from_state(state_of(declaration, POINTS[toy_id]))
    gradient = choi_gradient(maps, parametrization, q, choi, alpha)
    for index, sector in enumerate(declaration.sector_index_set):
        direction = random_hermitian(choi[sector].shape[0], seed=31 + index)
        plus = {**choi, sector: choi[sector] + STEP * direction}
        minus = {**choi, sector: choi[sector] - STEP * direction}
        difference = (
            choi_objective_value(maps, parametrization, q, plus, alpha)
            - choi_objective_value(maps, parametrization, q, minus, alpha)
        ) / (2.0 * STEP)
        analytic = float(np.real(np.trace(gradient.blocks[sector] @ direction)))
        assert difference == pytest.approx(analytic, rel=FD, abs=FD), (
            toy_id,
            alpha,
            sector,
        )


@pytest.mark.contract
@pytest.mark.parametrize("alpha", ALPHAS)
def test_c12_q_gradient_matches_central_differences(alpha: float) -> None:
    """Eq. eq:grad-q, the frequency block.

    Differentiated in the AMBIENT ``q`` coordinates, which is what
    Corollary ``cor:full-gradient`` states; the simplex constraint is the
    feasible set's, not the derivative's.
    """
    declaration = declaration_of("TOY-4b")  # two acceptance values, both positive
    maps = generate_maps(declaration)
    omega = {"s0": np.array([[1.0]], dtype=np.complex128)}
    q = acceptance_vector(declaration)
    gradient = state_gradient(maps, q, omega, alpha)
    for chat in declaration.acceptance_values:
        plus = {**q, chat: q[chat] + STEP}
        minus = {**q, chat: q[chat] - STEP}
        difference = (
            objective_value(maps, plus, omega, alpha)
            - objective_value(maps, minus, omega, alpha)
        ) / (2.0 * STEP)
        assert difference == pytest.approx(gradient.q[chat], rel=FD, abs=FD)


@pytest.mark.contract
@pytest.mark.parametrize("alpha", ALPHAS)
def test_c12_key_inert_sectors_have_an_identically_zero_deficit_gradient(
    alpha: float,
) -> None:
    """Proposition prop:exact-cancellation at the gradient level.

    f == 0 implies grad f == 0.
    """
    declaration = declaration_of("TOY-1")
    maps = generate_maps(declaration)
    omega = state_of(declaration, {"s0": 0.5, "s1": 0.5})
    inert = deficit_gradient(maps, "chat0", "s1", omega["s1"], alpha)
    assert np.allclose(inert, 0.0, atol=1e-12)
    active = deficit_gradient(maps, "chat0", "s0", omega["s0"], alpha)
    assert not np.allclose(active, 0.0, atol=1e-9)


@pytest.mark.contract
@pytest.mark.parametrize("alpha", ALPHAS)
def test_c12_grad_t_is_scale_invariant(alpha: float) -> None:
    """``T`` is homogeneous of degree one, so ``grad T`` is of degree zero.

    The identity the implementation relies on to evaluate the gradient at
    ``X / tr X`` and stay in range no matter how lightly a sector is weighted.
    """
    declaration = declaration_of("TOY-1")
    maps = generate_maps(declaration)
    branch = maps.branches["chat0"]["s0"].classes[0]
    base = branch_operator(branch, np.array([[0.5]], dtype=np.complex128))
    face = z_invariant_face(branch)
    # grad T is stated at a positive definite argument; perturb onto the face.
    perturbed = 0.9 * base + 0.1 * (np.trace(base).real / 2.0) * face
    reference = trace_power_gradient(perturbed, alpha, branch.labels)
    for scale in (1e-9, 1e-3, 1.0, 1e3):
        scaled = trace_power_gradient(scale * perturbed, alpha, branch.labels)
        assert np.allclose(scaled, reference, atol=1e-9, rtol=0.0)


@pytest.mark.contract
def test_c12_refuses_a_gradient_at_a_non_maximal_support() -> None:
    """Theorem thm:gradient (ii): support-enlarging directions fail closed."""
    declaration = declaration_of("TOY-1")
    maps = generate_maps(declaration)
    singular = np.array([[0.0]], dtype=np.complex128)
    with pytest.raises(SupportError, match="thm:gradient"):
        deficit_gradient(maps, "chat0", "s0", singular, 1.5)
    # A rank-deficient branch operator is likewise refused by the operator-level
    # formula, which Theorem thm:gradient states at X > 0.
    branch = maps.branches["chat0"]["s0"].classes[0]
    rank_one = branch_operator(branch, np.array([[0.5]], dtype=np.complex128))
    assert np.linalg.matrix_rank(rank_one) == 1
    with pytest.raises(SupportError, match="thm:gradient"):
        trace_power_gradient(rank_one, 1.5, branch.labels)


@pytest.mark.contract
@pytest.mark.parametrize("alpha", ALPHAS)
def test_c12_the_explicit_perturbation_is_recorded_and_converges(
    alpha: float,
) -> None:
    """The alternative route of Theorem thm:gradient (ii), and its accounting.

    A positive perturbation makes the gradient available at a singular iterate,
    converges to the exact face-compressed value as it shrinks, and is RECORDED
    in the result rather than folded into it (spec/architecture.md 2.5).

    The rate is worth seeing: it is close to ``delta`` near ``alpha = 1`` and
    decays to roughly ``delta^{1/alpha}`` as ``alpha`` grows, so at
    ``alpha = 3`` a perturbation of ``1e-6`` still leaves a relative error of a
    few parts in a thousand. That is exactly why the perturbation route needs a
    quantitative error term before it can support a bound, and supplying one is
    the open claim C13. The default path of this implementation is the exact
    face compression, which needs no such term.
    """
    declaration = declaration_of("TOY-1")
    maps = generate_maps(declaration)
    q = acceptance_vector(declaration)
    omega = state_of(declaration, {"s0": 0.5, "s1": 0.5})
    exact = state_gradient(maps, q, omega, alpha)
    assert exact.perturbations == {}
    scale = float(np.max(np.abs(exact.blocks["s0"])))

    previous = None
    for delta in (1e-2, 1e-3, 1e-4, 1e-5, 1e-6):
        perturbed = state_gradient(maps, q, omega, alpha, perturbation=delta)
        assert perturbed.perturbations[("chat0", "s0")] == delta
        error = float(np.max(np.abs(perturbed.blocks["s0"] - exact.blocks["s0"])))
        if previous is not None:
            assert error < previous
        previous = error
    assert previous is not None and previous < 1e-2 * scale


@pytest.mark.contract
def test_the_pinching_moves_weight_out_of_the_support() -> None:
    """Why ``Y = Z(X^p)`` must be formed on the ambient space.

    The subtlety the gradient module is written around: for a branch operator of
    rank one spread over two raw-key values, ``Z(X^p)`` has rank two. Compressing
    it to ``supp X`` would compute a different number, so Theorem
    ``thm:gradient`` (i)'s compression subspace must be ``Z``-INVARIANT.
    """
    declaration = declaration_of("TOY-1")
    maps = generate_maps(declaration)
    branch = maps.branches["chat0"]["s0"].classes[0]
    operator = branch_operator(branch, np.array([[0.7]], dtype=np.complex128))
    assert np.linalg.matrix_rank(operator) == 1
    from certiqs_key.meat_core.objective.linalg import pinch

    pinched = pinch(psd_power(operator, 1.0 / 1.5), branch.labels)
    assert np.linalg.matrix_rank(pinched) == 2
    face = z_invariant_face(branch)
    assert np.trace(face).real == pytest.approx(2.0)
