"""The trusted frame and root of ``tau_A`` keep every positive eigenvalue.

``meat-core/lem:choi-marginal``, Eqs. ``eq:iota`` and ``eq:WWtau``. The
frame is built by the lemma's construction (b) when ``tau_A`` is diagonal bit
for bit and by construction (a) otherwise, and the root clamps only negative
eigenvalues: no eigenvalue is dropped for being small against the spectral
radius, as a ``support_cutoff`` window would.
"""

from __future__ import annotations

import numpy as np
import pytest

from certiqs_key.domain.manifest import KeyHolder
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    KeyLengthParameters,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.declaration.general import general_from_accepted
from certiqs_key.meat_core.objective.joint import (
    joint_choi_parametrization,
    marginal_frame,
    marginal_root,
)

#: 2^-50: far below SUPPORT_CUTOFF (1e-12) times the spectral radius 1 - 2^-50.
EPS = 2.0**-50


def _declaration(tau: np.ndarray) -> ProtocolDeclaration:
    """Return a one-sector, one-letter qubit declaration with marginal ``tau``.

    Only the frame is read from it here, so the rest is the smallest
    well-formed declaration: M_x0 = 1_A, F_v = 1/2 on one qubit sector.
    """
    return ProtocolDeclaration(
        alice_dim=2,
        alice_marginal=np.asarray(tau, dtype=np.complex128),
        sector_index_set=("s0",),
        sector_dims={"s0": 2},
        alice_povm={"x0": np.eye(2, dtype=np.complex128)},
        bob_povm={
            "v0": {"s0": 0.5 * np.eye(2, dtype=np.complex128)},
            "v1": {"s0": 0.5 * np.eye(2, dtype=np.complex128)},
        },
        announce_alice={"x0": "cA0"},
        announce_bob={"v0": "cB0", "v1": "cB0"},
        accept_statistic={("cA0", "cB0"): "chat0"},
        key_map={("x0", "v0"): 0, ("x0", "v1"): 1},
        key_holder=KeyHolder.BOB,
        acceptance_values=("chat0",),
        key_value_count=2,
        acceptance_set=AcceptanceSet(geometry="singleton", frequencies=(1.0,)),
        rounds=1_000,
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        source_replacement_license={"certificate": "hand-authored fixture"},
    )


@pytest.mark.contract
def test_the_trusted_frame_keeps_a_tiny_positive_eigenvalue_of_tau_a() -> None:
    """lem:choi-marginal eq:iota: Pi_iota tau_A = tau_A exactly, no window.

    On the frame builder (not ``support_isometry``) for ``tau_A``. tau_A =
    diag(1 - 2^-50, 2^-50) is diagonal with both entries non-zero, so
    construction (b) keeps both indices: iota = 1, and Pi_iota tau = tau is
    an identity of {0, 1} arithmetic. The root is diag(sqrt(t_i)), whose
    square has a positive (1, 1) entry.
    """
    tau = np.diag([1 - EPS, EPS]).astype(complex)
    frame = marginal_frame(tau, full=False)
    iota = frame.iota
    assert iota.shape == (2, 2)
    assert np.array_equal(iota.conj().T @ iota, np.eye(2))
    assert np.array_equal(iota @ iota.conj().T @ tau, tau)
    root = marginal_root(tau)
    assert (root @ root)[1, 1].real > 0
    # eq:WWtau up to the rounding of the root alone, far inside EPS.
    w = frame.root @ iota
    assert np.max(np.abs(w @ w.conj().T - tau)) < EPS / 16


@pytest.mark.contract
def test_the_production_frame_keeps_the_tiny_eigenvalue() -> None:
    """The frame joint_choi_parametrization builds, POVM form, trusted mode."""
    tau = np.diag([1 - EPS, EPS]).astype(complex)
    general = general_from_accepted(_declaration(tau))
    frame = joint_choi_parametrization(general).frames["t0"]
    assert frame.input_dim == 2
    assert not frame.is_full_frame
    assert np.array_equal(frame.iota @ frame.iota.conj().T @ tau, tau)
    assert np.max(np.abs(frame.w @ frame.w.conj().T - tau)) < EPS / 16


@pytest.mark.contract
def test_construction_b_drops_exactly_the_zero_diagonal_entries() -> None:
    """(b): the coordinate injection onto {i : t_i != 0}, increasing order.

    tau = diag(0, 1/4, 3/4): index 0 is the datum 0 and is dropped, so
    iota = [e1, e2] and d_{A_0} = 2 = rank tau.
    """
    tau = np.diag([0.0, 0.25, 0.75]).astype(complex)
    frame = marginal_frame(tau, full=False)
    assert not frame.full
    assert np.array_equal(frame.iota, np.eye(3)[:, [1, 2]])
    assert np.array_equal(frame.iota @ frame.iota.conj().T @ tau, tau)
    # The root of a diagonal tau is formed entry by entry: sqrt(1/4) = 1/2.
    assert frame.root[1, 1] == 0.5


@pytest.mark.contract
def test_a_non_diagonal_marginal_gets_the_full_frame_and_an_uncut_root() -> None:
    """(a) when tau is not diagonal bit for bit, with no rank decided.

    tau = [[1/2, 1/2 - d], [1/2 - d, 1/2]] with d = 2^-46 has eigenvalues
    1 - d and d (on |+> and |->); d / (1 - d) is far below the 1e-12 cutoff,
    which dropped it and left W W^dagger - tau of size d / 2 off the
    diagonal. With no cutoff the residue is the rounding of the root only.
    """
    d = 2.0**-46
    tau = np.array([[0.5, 0.5 - d], [0.5 - d, 0.5]], dtype=complex)
    frame = marginal_frame(tau, full=False)
    assert frame.full
    assert np.array_equal(frame.iota, np.eye(2))
    w = frame.root @ frame.iota
    assert np.max(np.abs(w @ w.conj().T - tau)) < d / 16
    general = general_from_accepted(_declaration(tau))
    production = joint_choi_parametrization(general).frames["t0"]
    assert production.is_full_frame and production.input_dim == 2
    assert np.max(np.abs(production.w @ production.w.conj().T - tau)) < d / 16


@pytest.mark.contract
def test_the_ensemble_form_frame_is_always_full() -> None:
    """lem:choi-factor (iv): the ensemble form reads the full frame.

    Even for a diagonal singular tau, where (b) would have been tight.
    """
    tau = np.diag([1.0, 0.0]).astype(complex)
    frame = marginal_frame(tau, full=True)
    assert frame.full
    assert np.array_equal(frame.iota, np.eye(2))


def test_a_nearly_diagonal_marginal_is_not_diagonal() -> None:
    """def:classes (c): the bit-level test, at no window."""
    tau = np.array([[1 - EPS, 2.0**-1074], [2.0**-1074, EPS]], dtype=complex)
    assert marginal_frame(tau, full=False).full
    diagonal = _declaration(np.diag([1.0, 0.0]))
    assert not joint_choi_parametrization(
        general_from_accepted(diagonal)
    ).frames["t0"].is_full_frame
