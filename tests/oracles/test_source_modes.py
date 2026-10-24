"""The 0.3.0 material: source modes, party partition, singular marginal, faces.

Everything checked here entered the contract at ``contract_version`` 0.3.0, or
is one of the two implementation-found gaps that 0.3.0 closes:

* the two SOURCE MODES (Remark ``rem:modes-da1``), their equivalence at
  ``d_A = 1``, and the conservative direction of dropping the marginal;
* the untrusted licensed class (Definition ``def:homog`` (b)) and why the
  operator form is not merely unlicensed but infeasible;
* the PARTY PARTITION and Assumption ``def:admissible-declaration`` (viii)'s widening;
* F-01-01, the declared basis of the Choi input register ``A_0`` for a
  singular ``tau_A`` (Remark ``rem:basis-invariance``);
* F-01-02, the SPLIT face rule of Theorem ``thm:gradient`` (i).

Registry entries: ``O-SOURCE-MODE-DERIVED``, ``O-MARGINAL-INADMISSIBLE``,
``O-MODE-EQUIVALENCE-DA1``, ``O-UNTRUSTED-CONSERVATIVE``,
``O-UNTRUSTED-SCALAR-CLASS``, ``O-PARTY-COMPUTABILITY``,
``O-CHOI-BASIS-INVARIANCE``, ``O-GRADIENT-FACE-SPLIT``. The two gate entries,
``O-CGATE-DEGENERATE`` and ``O-SOURCE-LICENSE-GATE``, live in
``test_fail_closed.py`` beside the gate predicate they constrain.

Nothing here imports from ``src/``: the toy declarations are hand-authored
literals and :mod:`reference` is the naive evaluator.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from reference import psd_power, trace_power_pinched
from registry import (
    ALPHA_GRID,
    O_GRADIENT_FACE_COMPRESSED_VALUES,
    O_UNTRUSTED_CONSERVATIVE_UNTRUSTED_VALUE,
    oracle,
)
from toy_declarations import (
    ALL_TOYS_0_3_0,
    MODE_TWIN_PAIRS,
    TOY1_RETENTION,
    TOY5_CONSTRAINED,
    TOY5_CONSTRAINED_UNTRUSTED,
    TOY7_NON_HOMOGENEOUS,
    TOY8_TRUSTED_MARGINAL,
    TOY8_UNTRUSTED,
    TOY9_IOTA_1,
    TOY9_IOTA_2,
    TOY9_J_1,
    TOY9_J_2,
    TOY9_OMEGA,
    TOY9_SINGULAR_MARGINAL,
    TOY10_EMBEDDED,
    ToyDeclaration,
    party_partition_of,
    source_mode,
)
from toy_evaluation import (
    branch_values,
    minimum_over_sector_weights,
    objective_from_blocks,
    statistics_from_blocks,
)

ALPHAS = ALPHA_GRID


def _toy5_feasible(point: dict[str, float]) -> bool:
    """Return whether ``point`` satisfies the declared entry ``w0 >= 1/2``."""
    return point["s0"] >= 0.5 - 1e-12


FEASIBILITY = {
    "TOY-5": _toy5_feasible,
    "TOY-5-UN": _toy5_feasible,
}


# ---------------------------------------------------------------------------
# O-SOURCE-MODE-DERIVED and O-MARGINAL-INADMISSIBLE
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_source_mode_is_derived_from_the_marginal_slot() -> None:
    """O-SOURCE-MODE-DERIVED: contract Section 2.5's source_model convention."""
    entry = oracle("O-SOURCE-MODE-DERIVED")
    assert entry.claims == ("C1",)
    assert entry.value == "derived"

    expected = {
        "TOY-1-UN": "untrusted",
        "TOY-3(m=2)-UN": "untrusted",
        "TOY-5-UN": "untrusted",
        "TOY-8-UN": "untrusted",
        "TOY-10": "untrusted",
    }
    for toy in ALL_TOYS_0_3_0:
        mode = source_mode(toy)
        assert mode == expected.get(toy.toy_id, "trusted"), toy.toy_id
        # The mode IS the slot value, read off it and nothing else.
        assert (mode == "untrusted") == (toy.alice_marginal is None), toy.toy_id


@pytest.mark.contract
@pytest.mark.oracle
def test_no_declaration_carries_a_separate_source_mode_field() -> None:
    """A second key holding the mode would be a second source of truth."""
    forbidden = {"source_mode", "source_model", "mode", "trusted"}
    fields = set(ToyDeclaration.__dataclass_fields__)
    assert fields & forbidden == set()


@pytest.mark.contract
@pytest.mark.oracle
def test_a_zero_marginal_is_inadmissible_on_both_grounds() -> None:
    """O-MARGINAL-INADMISSIBLE: transmitter/rem:source-mode (c), twice over."""
    entry = oracle("O-MARGINAL-INADMISSIBLE")
    assert entry.kind == "fail-closed"
    assert entry.value == "reject"

    zero = np.zeros((2, 2))
    # Ground (1): def:admissible-declaration (ii) asks for a normalized state.
    assert float(np.trace(zero)) != pytest.approx(1.0)

    # Ground (2), independent of normalization: for omega >= 0 on A x Q,
    # omega_A = 0 forces tr omega = tr omega_A = 0 and hence omega = 0, so the
    # feasible set is empty against def:admissible-declaration (vii). Checked on the
    # general fact that a PSD matrix of zero trace is zero.
    rng = np.random.default_rng(20260829)
    for _ in range(16):
        root = rng.normal(size=(4, 4))
        psd = root @ root.T
        scaled = psd / float(np.trace(psd))
        assert float(np.trace(scaled)) == pytest.approx(1.0)
        # ... and the only PSD matrix whose trace vanishes is the zero matrix.
        eigenvalues = np.linalg.eigvalsh(psd)
        assert (eigenvalues >= -1e-12).all()
        assert (np.abs(eigenvalues).sum() > 0.0) == (float(np.trace(psd)) > 0.0)

    # The absent marginal has its own spelling and is NOT the zero matrix.
    assert TOY8_UNTRUSTED.alice_marginal is None
    assert TOY8_TRUSTED_MARGINAL.alice_marginal is not None


@pytest.mark.contract
@pytest.mark.oracle
def test_the_maximally_mixed_marginal_is_a_trusted_declaration() -> None:
    """A-SRC: tau_A = 1_A/d_A is not a neutral 'nothing is known about A'."""
    assert source_mode(TOY7_NON_HOMOGENEOUS) == "trusted"
    assert np.allclose(TOY7_NON_HOMOGENEOUS.alice_marginal, np.eye(2) / 2.0)
    # It EXCLUDES every source that sends anything else: at d_A = 2 with a
    # one-dimensional Q the marginal condition pins omega outright.
    assert TOY7_NON_HOMOGENEOUS.sector_dims == {"s0": 1}


# ---------------------------------------------------------------------------
# O-MODE-EQUIVALENCE-DA1
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_the_two_modes_agree_at_alice_dim_one(alpha: float) -> None:
    """O-MODE-EQUIVALENCE-DA1: the twins reproduce their originals exactly."""
    entry = oracle("O-MODE-EQUIVALENCE-DA1")
    assert entry.kind == "structural-identity"

    for original, twin in MODE_TWIN_PAIRS:
        assert original.alice_dim == 1 and twin.alice_dim == 1
        assert source_mode(original) == "trusted"
        assert source_mode(twin) == "untrusted"
        feasible = FEASIBILITY.get(original.toy_id)
        left, at_left = minimum_over_sector_weights(
            original, alpha, steps=400, feasible=feasible
        )
        right, at_right = minimum_over_sector_weights(
            twin, alpha, steps=400, feasible=FEASIBILITY.get(twin.toy_id)
        )
        # Not "close": the same declaration, hence the same number.
        assert left == right, (original.toy_id, alpha, left, right)
        assert at_left == at_right


@pytest.mark.contract
@pytest.mark.oracle
def test_the_twin_values_are_the_frozen_ones() -> None:
    """The pairs pin 0, 1 and the alpha-dependent constrained form."""
    for alpha in ALPHAS:
        zero, _ = minimum_over_sector_weights(MODE_TWIN_PAIRS[0][1], alpha, steps=200)
        assert zero == pytest.approx(0.0, abs=1e-12)

        one, _ = minimum_over_sector_weights(MODE_TWIN_PAIRS[1][1], alpha, steps=200)
        assert one == pytest.approx(1.0, rel=1e-12)

        constrained, _ = minimum_over_sector_weights(
            TOY5_CONSTRAINED_UNTRUSTED, alpha, steps=400, feasible=_toy5_feasible
        )
        assert constrained == pytest.approx(
            oracle("O-HLOW-CONSTRAINED").closed_form(alpha), rel=1e-9
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_untrusted_twin_retypes_the_constraint_right_hand_side() -> None:
    """def:homog (b): the entry is a SCALAR there, an operator in trusted mode."""
    trusted = TOY5_CONSTRAINED.constraint_list[0]
    untrusted = TOY5_CONSTRAINED_UNTRUSTED.constraint_list[0]

    assert isinstance(trusted.bound, np.ndarray)
    assert trusted.bound.shape == (1, 1)
    assert isinstance(untrusted.bound, float)

    # Different TYPES, and at d_A = 1 the same number, hence the same set --
    # Remark rem:modes-da1 (b3).
    assert float(trusted.bound[0, 0]) == untrusted.bound
    assert trusted.homogeneous_scalar == untrusted.homogeneous_scalar == 0.5
    assert trusted.relation == untrusted.relation == "succeq"
    assert np.allclose(trusted.operator_blocks["s0"], untrusted.operator_blocks["s0"])


# ---------------------------------------------------------------------------
# O-UNTRUSTED-CONSERVATIVE
# ---------------------------------------------------------------------------


def _toy8_untrusted_infimum(alpha: float, *, steps: int = 4000) -> float:
    """Grid the one parameter TOY-8-UN's objective depends on.

    The objective sees ``omega`` only through ``diag(omega) = (p, 1-p)``, every
    PSD normalized ``omega`` has such a diagonal, and every such pair is
    realized by ``diag(p, 1-p)``. So this grid covers the feasible set; it is a
    check on a hand-derived infimum, not a solver.
    """
    best = math.inf
    for index in range(steps + 1):
        share = index / steps
        blocks = {"s0": np.diag([share, 1.0 - share])}
        best = min(best, objective_from_blocks(TOY8_UNTRUSTED, alpha, blocks))
    return best


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_dropping_the_marginal_strictly_lowers_h_low_on_toy8(alpha: float) -> None:
    """O-UNTRUSTED-CONSERVATIVE: the frozen gap, and its direction."""
    entry = oracle("O-UNTRUSTED-CONSERVATIVE")
    assert entry.claims == ("C8",)
    expected = dict(entry.frozen_values)[alpha]

    # Trusted mode: omega_A = tau_A pins omega, so the feasible set is a point.
    phi = statistics_from_blocks(
        TOY8_TRUSTED_MARGINAL, {"s0": TOY8_TRUSTED_MARGINAL.alice_marginal}
    )
    assert phi == pytest.approx({"chat0": 0.875, "chat1": 0.125})
    trusted = objective_from_blocks(
        TOY8_TRUSTED_MARGINAL, alpha, {"s0": TOY8_TRUSTED_MARGINAL.alice_marginal}
    )
    assert trusted == pytest.approx(expected, rel=1e-12)
    assert trusted == pytest.approx(
        (alpha / (alpha - 1.0)) * (2.0 - 0.5 * math.log2(7.0)), rel=1e-12
    )

    # Untrusted mode: the accepted vector becomes reachable and the value is 0.
    untrusted = _toy8_untrusted_infimum(alpha)
    assert untrusted == pytest.approx(
        O_UNTRUSTED_CONSERVATIVE_UNTRUSTED_VALUE, abs=1e-9
    )

    # The direction of Remark transmitter/rem:source-mode (a), strictly.
    assert untrusted < trusted
    assert trusted - untrusted == pytest.approx(expected, rel=1e-8)


@pytest.mark.contract
@pytest.mark.oracle
def test_every_trusted_feasible_point_of_toy8_is_untrusted_feasible() -> None:
    """transmitter/rem:source-mode (a): the untrusted feasible set is the larger one."""
    omega = TOY8_TRUSTED_MARGINAL.alice_marginal
    assert float(np.trace(omega)) == pytest.approx(1.0)  # the untrusted condition
    assert (np.linalg.eigvalsh(omega) >= -1e-12).all()
    # And the untrusted set is strictly larger: diag(1/2, 1/2) is in it and is
    # not the declared marginal.
    assert not np.allclose(omega, np.diag([0.5, 0.5]))


# ---------------------------------------------------------------------------
# O-UNTRUSTED-SCALAR-CLASS
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_operator_reading_of_a_scalar_entry_empties_the_feasible_set() -> None:
    """O-UNTRUSTED-SCALAR-CLASS: rem:homog (a)'s witness, re-derived here."""
    entry = oracle("O-UNTRUSTED-SCALAR-CLASS")
    assert entry.kind == "fail-closed"
    assert entry.claims == ("C9b", "C17")

    identity_q = np.array([[1.0]])  # O = 1_Q on TOY-8-UN's single sector
    bound = 1.0  # c = 1
    # 1_A x O on A x Q_s0, with A first (contract subsystem_order A, Q).
    lifted = np.kron(np.eye(TOY8_UNTRUSTED.alice_dim), identity_q)

    # SCALAR reading (licensed): tr[(1_A x O) omega] = tr omega = 1 >= c.
    for share in (0.0, 0.25, 0.5, 1.0):
        omega = np.diag([share, 1.0 - share])
        value = float(np.real(np.trace(lifted @ omega)))
        assert value == pytest.approx(1.0)
        assert value >= bound - 1e-15

    # OPERATOR reading (unlicensed): tr_Q[(1_A x O) omega] = omega_A >= 1_A.
    # At d_A = 2 that forces tr omega_A >= 2, contradicting tr omega = 1.
    for share in (0.0, 0.25, 0.5, 1.0):
        omega_a = np.diag([share, 1.0 - share])
        residual = omega_a - np.eye(2) * bound
        assert np.linalg.eigvalsh(residual).min() < 0.0
    # No normalized state can satisfy it: the trace of the residual is
    # 1 - d_A = -1 < 0, so the residual is never PSD.
    assert 1.0 - 2.0 * bound < 0.0


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_the_licensed_scalar_entry_changes_nothing_on_toy8_untrusted(
    alpha: float,
) -> None:
    """The licensed attack set is everything, and so the entry restricts nothing."""
    # The entry (O = 1_Q, >=, c = 1) is satisfied by every feasible state, so
    # the infimum is the unconstrained one.
    assert _toy8_untrusted_infimum(alpha, steps=1000) == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# O-PARTY-COMPUTABILITY
# ---------------------------------------------------------------------------


def _factors_through_readout(toy: ToyDeclaration, holder: str) -> bool:
    """Return whether ``r`` factors through ``pi_holder`` and the announcements.

    Assumption ``def:admissible-declaration`` (viii), Eq. ``eq:partycomp``: there must
    be a total ``r_h`` with ``r(x, v) = r_h(pi_h(x, v), a(x, v))``. Equivalently, any
    two outcome pairs with the same holder readout AND the same announcements carry
    the same raw-key value.
    """
    partition = party_partition_of(toy)
    readout = partition.readout_alice if holder == "A" else partition.readout_bob
    seen: dict[tuple[str, str, str], int | None] = {}
    for pair, value in toy.key_map.items():
        announcement = (
            toy.announce_alice[partition.readout_alice[pair]],
            toy.announce_bob[partition.readout_bob[pair]],
        )
        signature = (readout[pair], *announcement)
        if signature in seen and seen[signature] != value:
            return False
        seen[signature] = value
    return True


@pytest.mark.contract
@pytest.mark.oracle
def test_the_party_partition_decides_which_key_holder_is_admissible() -> None:
    """O-PARTY-COMPUTABILITY: Admissibility (viii) on TOY-10, both verdicts."""
    entry = oracle("O-PARTY-COMPUTABILITY")
    assert entry.claims == ("C1", "C14")
    assert entry.toy_id == "TOY-10"

    assert TOY10_EMBEDDED.key_holder == "A"
    assert _factors_through_readout(TOY10_EMBEDDED, "A") is True
    assert _factors_through_readout(TOY10_EMBEDDED, "B") is False

    # The exact witness pair: same Bob readout, different raw key.
    partition = party_partition_of(TOY10_EMBEDDED)
    assert partition.is_default is False
    assert partition.readout_bob[("x0", "v00")] == partition.readout_bob[("x0", "v10")]
    assert (
        TOY10_EMBEDDED.key_map[("x0", "v00")] != TOY10_EMBEDDED.key_map[("x0", "v10")]
    )

    # ... and under the SUPERSEDED 0.2.x reading -- r a function of v alone --
    # h = B would have passed, which is the vacuity the widening removes.
    by_outcome: dict[str, int | None] = {}
    vacuously_ok = True
    for (_, v), value in TOY10_EMBEDDED.key_map.items():
        if v in by_outcome and by_outcome[v] != value:
            vacuously_ok = False
        by_outcome[v] = value
    assert vacuously_ok is True


@pytest.mark.contract
@pytest.mark.oracle
def test_the_default_partition_reproduces_the_0_2_x_declarations() -> None:
    """def:declaration: the default partition "reproduces versions 0.2.x verbatim"."""
    partition = party_partition_of(TOY1_RETENTION)
    assert partition.is_default is True
    for x in TOY1_RETENTION.alice_povm:
        for v in TOY1_RETENTION.bob_povm:
            assert partition.readout_alice[(x, v)] == x
            assert partition.readout_bob[(x, v)] == v
    assert partition.party_of_alice_system == "A"
    assert set(partition.party_of_sector_factors) == set(
        TOY1_RETENTION.sector_index_set
    )
    # Every frozen 0.2.4-era toy carries the default and no other.
    assert _factors_through_readout(TOY1_RETENTION, "B") is True


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_the_embedded_declaration_reproduces_toy1(alpha: float) -> None:
    """TOY-10 is TOY-1's protocol declared the 0.3.0 way; the value must agree."""
    value, at = minimum_over_sector_weights(TOY10_EMBEDDED, alpha, steps=400)
    assert value == pytest.approx(0.0, abs=1e-12)
    assert at["s0"] == pytest.approx(0.0)

    # And dropping the constraint-active sector still costs exactly one bit
    # (Proposition prop:retention), through a four-outcome, untrusted-mode,
    # party-partitioned declaration.
    dropped = branch_values(TOY10_EMBEDDED, alpha, {"s0": 1.0, "s1": 0.0})["chat0"]
    assert dropped.k == pytest.approx(2.0 ** (1.0 - alpha))
    assert math.log2(1.0 / dropped.k) / (alpha - 1.0) == pytest.approx(1.0)

    # The key-inert sector still cancels exactly (C7).
    inert = branch_values(TOY10_EMBEDDED, alpha, {"s0": 0.0, "s1": 1.0})["chat0"]
    assert inert.deficits["s1"] == pytest.approx(0.0, abs=1e-14)


# ---------------------------------------------------------------------------
# O-CHOI-BASIS-INVARIANCE  (closure of F-01-01)
# ---------------------------------------------------------------------------


def _moore_penrose_of_full_column_rank(matrix: np.ndarray) -> np.ndarray:
    """Return ``(W^dagger W)^{-1} W^dagger`` for a full-column-rank ``W``."""
    return np.linalg.inv(matrix.T @ matrix) @ matrix.T


@pytest.mark.contract
@pytest.mark.oracle
def test_a_singular_trusted_marginal_is_admissible() -> None:
    """O-CHOI-BASIS-INVARIANCE: contract Section 2.1 admits it explicitly."""
    entry = oracle("O-CHOI-BASIS-INVARIANCE")
    assert entry.claims == ("C11",)

    tau = TOY9_SINGULAR_MARGINAL.alice_marginal
    assert float(np.trace(tau)) == pytest.approx(1.0)  # def:admissible-declaration (ii)
    assert (np.linalg.eigvalsh(tau) >= -1e-14).all()
    rank = int(np.linalg.matrix_rank(tau, tol=1e-12))
    assert rank == 2 < TOY9_SINGULAR_MARGINAL.alice_dim == 3
    # The condition that makes choi_input_basis a REQUIRED output field.
    assert rank < TOY9_SINGULAR_MARGINAL.alice_dim


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_h_low_on_toy9_is_the_frozen_closed_form(alpha: float) -> None:
    """The value, and its independence of the feasible point chosen."""
    entry = oracle("O-CHOI-BASIS-INVARIANCE")
    expected = dict(entry.frozen_values)[alpha]
    tau = TOY9_SINGULAR_MARGINAL.alice_marginal

    for omega in (np.kron(tau, np.eye(2) / 2.0), TOY9_OMEGA):
        phi = statistics_from_blocks(TOY9_SINGULAR_MARGINAL, {"s0": omega})
        assert phi == pytest.approx({"chat0": 0.75, "chat1": 0.25})
        value = objective_from_blocks(TOY9_SINGULAR_MARGINAL, alpha, {"s0": omega})
        assert value == pytest.approx(expected, rel=1e-12)
        assert value == pytest.approx(
            (alpha / (alpha - 1.0)) * 0.5 * math.log2(3.0), rel=1e-12
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_both_declared_bases_are_admissible_and_give_the_same_state() -> None:
    """Remark rem:basis-invariance, on the two frozen isometries."""
    tau = TOY9_SINGULAR_MARGINAL.alice_marginal
    root = np.diag(np.sqrt(np.diag(tau)))
    support_projector = np.diag([1.0, 1.0, 0.0])
    identity_q = np.eye(2)

    coordinates = []
    for iota, frozen in ((TOY9_IOTA_1, TOY9_J_1), (TOY9_IOTA_2, TOY9_J_2)):
        # Eq. eq:iota: an isometry onto supp(tau_A).
        assert np.allclose(iota.T @ iota, np.eye(2))
        assert np.allclose(iota @ iota.T, support_projector)

        w_tau = root @ iota  # Eq. eq:Wtau
        assert np.allclose(w_tau @ w_tau.T, tau)
        pseudo = _moore_penrose_of_full_column_rank(w_tau)
        assert np.allclose(pseudo @ w_tau, np.eye(2))

        choi = np.kron(pseudo, identity_q) @ TOY9_OMEGA @ np.kron(pseudo, identity_q).T
        assert np.allclose(choi, frozen), "the frozen coordinates are the derived ones"

        # The coupling constraint of Eq. eq:choi-feas.
        partial = np.trace(choi.reshape(2, 2, 2, 2), axis1=1, axis2=3)
        assert np.allclose(partial, np.eye(2))

        # ... and chi carries it back to the same state (Lemma lem:choi-marginal).
        back = np.kron(w_tau, identity_q) @ choi @ np.kron(w_tau, identity_q).T
        assert np.allclose(back, TOY9_OMEGA)
        coordinates.append(choi)

    # The coordinates DIFFER while the state and the value do not: that is the
    # whole content, and the reason choi_input_basis must be recorded.
    assert not np.allclose(coordinates[0], coordinates[1])
    hadamard = np.array([[1.0, 1.0], [1.0, -1.0]]) / math.sqrt(2.0)
    assert np.allclose(
        np.kron(hadamard.T, identity_q)
        @ coordinates[0]
        @ np.kron(hadamard, identity_q),
        coordinates[1],
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_toy9_is_the_only_declaration_needing_a_recorded_choi_basis() -> None:
    """choi_input_basis is required exactly when rank(tau_A) < d_A."""
    needing = set()
    for toy in ALL_TOYS_0_3_0:
        if toy.alice_marginal is None:
            continue  # untrusted mode: there is no Choi input register at all
        rank = int(np.linalg.matrix_rank(toy.alice_marginal, tol=1e-12))
        if rank < toy.alice_dim:
            needing.add(toy.toy_id)
    assert needing == {"TOY-9"}


# ---------------------------------------------------------------------------
# O-GRADIENT-FACE-SPLIT  (closure of F-01-02)
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_the_ambient_and_compressed_trace_powers_differ(alpha: float) -> None:
    """O-GRADIENT-FACE-SPLIT: thm:gradient (i)'s rank-one witness, re-derived."""
    entry = oracle("O-GRADIENT-FACE-SPLIT")
    assert entry.claims == ("C6", "C12")
    correct = dict(entry.frozen_values)[alpha]
    wrong = dict(O_GRADIENT_FACE_COMPRESSED_VALUES)[alpha]

    # |eta> = (|j,u> + |j',u'>)/sqrt2 with j /= j': rank one, spread over two
    # raw-key values, so supp X is NOT Z-invariant.
    eta = np.array([1.0, 1.0]) / math.sqrt(2.0)
    branch = np.outer(eta, eta)
    row_key_values = (0, 1)

    # AMBIENT, the contract's rule: Z(X^p) is formed on the branch space.
    ambient = trace_power_pinched(branch, alpha, row_key_values)
    assert ambient == pytest.approx(correct, rel=1e-12)
    assert ambient == pytest.approx(2.0 ** (1.0 - alpha), rel=1e-12)

    # COMPRESSED TO supp X, the rule the 0.2.4 statement literally said and
    # 0.2.5/0.3.0 discard: a 1x1 computation inside C|eta>.
    powered = psd_power(branch, 1.0 / alpha)
    pinched = powered * (np.array(row_key_values)[:, None] == row_key_values)
    compressed = float(eta @ pinched @ eta) ** alpha
    assert compressed == pytest.approx(wrong, rel=1e-12)
    assert compressed == pytest.approx(2.0**-alpha, rel=1e-12)

    # Exactly a factor of two, at every alpha.
    assert ambient / compressed == pytest.approx(2.0, rel=1e-12)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_the_discarded_compression_errs_in_the_unsafe_direction(alpha: float) -> None:
    """A smaller T gives a smaller K, a larger h_low and a larger key length."""
    correct = dict(oracle("O-GRADIENT-FACE-SPLIT").frozen_values)[alpha]
    wrong = dict(O_GRADIENT_FACE_COMPRESSED_VALUES)[alpha]
    assert wrong < correct

    # On TOY-1 at w0 = 1 the witness IS the branch operator, so K = T and the
    # objective is (1/(alpha-1)) log2(1/K).
    values = branch_values(TOY1_RETENTION, alpha, {"s0": 1.0, "s1": 0.0})["chat0"]
    assert values.k == pytest.approx(correct, rel=1e-12)

    honest = math.log2(1.0 / correct) / (alpha - 1.0)
    overstated = math.log2(1.0 / wrong) / (alpha - 1.0)
    assert overstated > honest
    # And the overstatement is exactly one bit per round here.
    assert overstated - honest == pytest.approx(1.0 / (alpha - 1.0), rel=1e-12)


@pytest.mark.contract
@pytest.mark.oracle
def test_a_z_invariant_face_is_where_the_two_rules_agree() -> None:
    """thm:gradient (i): full compression is licensed on a Z-invariant S'."""
    # TOY-1's key-INERT sector s1: its branch operator is supported in a single
    # R-eigenspace, which is Z-invariant, so compressing changes nothing.
    branch = np.diag([1.0, 0.0])
    row_key_values = (0, 1)
    for alpha in ALPHAS:
        ambient = trace_power_pinched(branch, alpha, row_key_values)
        assert ambient == pytest.approx(float(np.trace(branch)))
        vector = np.array([1.0, 0.0])
        powered = psd_power(branch, 1.0 / alpha)
        pinched = powered * (np.array(row_key_values)[:, None] == row_key_values)
        compressed = float(vector @ pinched @ vector) ** alpha
        assert compressed == pytest.approx(ambient, rel=1e-12)
