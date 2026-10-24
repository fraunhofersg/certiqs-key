"""The engine-level targets of the two frozen instance registries.

``registry_instances_decoy_bb84.py`` OT1 to OT4 and
``registry_instances_bbm92.py`` B-6 are stated of the MATHEMATICS -- "OT1, OT2
and OT3 are state independent, hence exact tests at any feasible point"
(``05-validation.md`` 5.3) -- so the ones that need no instance are tested here,
on the hand-built toys of :mod:`tests.support.general_toys`. THE REGISTRIES ARE
READ AND NEVER EDITED: every closed form below is imported from one of them.

Which entry each test is: OT1 the vacuum sector's one bit, OT2 the flag
sectors' identically zero deficit, OT3 the factorisation of a rank-one Alice
sector, OT4 the single-photon Bell-diagonal closed form, plus the ensemble-form
/ POVM-form equality of ``lem:choi-factor`` (iii), (iv) on the qubit BB84
declaration where ``tau_A`` is a multiple of the identity, and B-6's containment
direction on a toy two-factor declaration.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from tests.oracles.registry_instances_decoy_bb84 import (
    OT3_FOIL_MARGINAL,
    OT3_FOIL_STATE,
    OT3_WITNESS_MARGINAL,
    OT3_WITNESS_STATE,
    bell_diagonal_bits,
    sector_deficit_factor,
)
from tests.support.general_toys import (
    ALPHA_GRID,
    decoy_like_general,
    honest_q,
    maps_of,
    projector,
    qubit_bb84_general,
    random_choi_point,
    two_factor_general,
)

from certiqs_key.meat_core.objective.joint import (
    joint_deficit,
    joint_objective_value,
    joint_statistics,
    rank_one_deficit,
    rank_one_sector,
)
from certiqs_key.meat_core.objective.joint_gradient import joint_gradient
from certiqs_key.meat_core.objective.joint_rows import (
    check_joint_feasible,
    entry_trace_value,
    party_local_value,
)

#: How closely a computed deficit must match a closed form. Both sides are
#: binary64 evaluations of the same real number through different arithmetic --
#: a matrix power and eigendecomposition on one side, a scalar formula on the
#: other -- so the comparison is at the accumulated rounding of the matrix
#: route and not at zero. IT IS NOT A DECLARED TOLERANCE AND DECIDES NOTHING
#: ABOUT ANY DECLARATION.
CLOSED_FORM_ATOL = 1e-12


def _as_array(rows: tuple[tuple[object, ...], ...]) -> np.ndarray:
    """Return an exact rational registry matrix as binary64 data."""
    return np.asarray(
        [[complex(float(entry)) for entry in row] for row in rows],
        dtype=np.complex128,
    )


@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize("seed", (1, 2))
def test_ot1_the_vacuum_sector_carries_one_bit(alpha: float, seed: int) -> None:
    """OT1: one bit per sifted round, at every alpha and every output state.

    The vacuum sector's marginal is rank one and the key is a uniform bit inside
    every pass class, so ``lem:rank-one-sector`` (iii), (iv) give
    ``eta = 1 - 2^{1-alpha}`` and the deficit
    ``f = -eta * P_{(t,s)}`` -- which is
    ``registry_instances_decoy_bb84.sector_deficit_factor`` times the pair's
    pass weight. The pair's ``K/P`` is then ``2^{(1-alpha) * 1}``: one bit.
    """
    maps = maps_of(decoy_like_general())
    choi = random_choi_point(maps.parametrization, seed)
    pair = ("vacuum", "q")
    block = choi[pair]
    deficit = joint_deficit(maps, "match", pair, block, alpha)
    pass_weight = float(
        np.real(np.trace(maps.statistics_operator[("match", pair)] @ block))
    )
    expected = -sector_deficit_factor(alpha, (0.5, 0.5)) * pass_weight
    assert deficit == pytest.approx(expected, abs=CLOSED_FORM_ATOL)
    # The bits the pair carries, read off K/P as thm:branch-formula does.
    ratio = (pass_weight + deficit) / pass_weight
    assert math.log2(ratio) / (1.0 - alpha) == pytest.approx(
        1.0, abs=CLOSED_FORM_ATOL
    )


@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_ot2_a_flag_sector_has_deficit_identically_zero(alpha: float) -> None:
    """OT2: a flag sector's deficit vanishes for EVERY input.

    The key is constant where ``mu_x > 0``, so ``eta_kappa = 0``
    (``lem:rank-one-sector`` (iv)) and the pair is key-inert
    (``def:joint-sectors``), which ``lem:joint-sectors`` (iii) turns into
    ``f == 0`` on the whole subcone.
    """
    maps = maps_of(decoy_like_general())
    pair = ("flag", "q")
    assert maps.key_inert[("match", pair)]
    for seed in (3, 4):
        choi = random_choi_point(maps.parametrization, seed)
        assert joint_deficit(maps, "match", pair, choi[pair], alpha) == pytest.approx(
            0.0, abs=CLOSED_FORM_ATOL
        )


def test_ot3_a_rank_one_alice_sector_factorises_at_every_feasible_point() -> None:
    """OT3, on the registry's own witness and foil.

    ``lem:rank-one-sector`` (i): every positive block whose ``A``-marginal is
    ``p |v><v|`` is ``|v><v| (x) sigma``. The WITNESS is such a pair and the
    factorisation is exhibited; the FOIL has a rank-TWO marginal and a positive
    non-product block, which is why one row of the pair is not evidence.
    """
    witness_marginal = _as_array(OT3_WITNESS_MARGINAL)
    witness_state = _as_array(OT3_WITNESS_STATE)
    values, vectors = np.linalg.eigh(witness_marginal)
    order = np.argsort(-values)
    assert float(values[order[1]]) == 0.0
    vector = np.asarray(vectors[:, order[0]], dtype=np.complex128)
    lift = np.kron(vector.conj().reshape(1, -1), np.eye(2, dtype=np.complex128))
    sigma = lift @ witness_state @ lift.conj().T
    assert np.allclose(
        np.kron(projector(vector), sigma), witness_state, atol=0.0
    )
    foil_marginal = _as_array(OT3_FOIL_MARGINAL)
    foil_state = _as_array(OT3_FOIL_STATE)
    foil_values = np.linalg.eigvalsh(foil_marginal)
    assert float(np.min(foil_values)) > 0.0
    foil_vector = np.asarray([1.0, 0.0], dtype=np.complex128)
    foil_lift = np.kron(
        foil_vector.conj().reshape(1, -1), np.eye(2, dtype=np.complex128)
    )
    foil_sigma = foil_lift @ foil_state @ foil_lift.conj().T
    assert not np.allclose(np.kron(projector(foil_vector), foil_sigma), foil_state)


@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize("seed", (5, 6))
def test_ot3_the_engine_reads_a_rank_one_sector_as_a_product(
    alpha: float, seed: int
) -> None:
    """OT3 in the engine: the closed form agrees with the general matrix route.

    The engine's rank-one reading (``lem:rank-one-sector`` (i), (iii)) is
    exercised against the deficit computed from the branch operators, which
    reads no rank at all. Agreement is the factorisation: the closed form is an
    identity only if every feasible block of that sector is
    ``|v><v| (x) sigma_s``.
    """
    maps = maps_of(decoy_like_general())
    choi = random_choi_point(maps.parametrization, seed)
    for sector in ("vacuum", "rank1"):
        data = rank_one_sector(maps, sector)
        assert data is not None
        pair = (sector, "q")
        closed = rank_one_deficit(maps, "match", pair, choi[pair], alpha, data)
        general = joint_deficit(maps, "match", pair, choi[pair], alpha)
        assert closed == pytest.approx(general, abs=CLOSED_FORM_ATOL)
    assert rank_one_sector(maps, "one") is None


@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_ot4_the_one_photon_sector_at_a_bell_diagonal_point(alpha: float) -> None:
    """OT4: ``h_1 = 1 - log2 S / (alpha - 1)`` at a Bell-diagonal block.

    ``S = sum_i (lambda_{i0}^{1/alpha} + lambda_{i1}^{1/alpha})^alpha``, which
    ``registry_instances_decoy_bb84.bell_diagonal_bits`` evaluates, and the
    identity that makes it the sector's bits is ``T / tr G = 2^{(1-alpha) h}``.
    The point is the Bell-diagonal state of the frozen weights, placed on the
    single-photon Alice sector and lifted to the Choi block of that sector's
    frame.
    """
    lambdas = (13.0 / 16.0, 1.0 / 16.0, 1.0 / 16.0, 1.0 / 16.0)
    maps = maps_of(decoy_like_general())
    pair = ("one", "q")
    root = math.sqrt(0.5)
    bell = {
        0: np.asarray([root, 0.0, 0.0, root], dtype=np.complex128),
        1: np.asarray([root, 0.0, 0.0, -root], dtype=np.complex128),
        2: np.asarray([0.0, root, root, 0.0], dtype=np.complex128),
        3: np.asarray([0.0, root, -root, 0.0], dtype=np.complex128),
    }
    state = sum(
        weight * projector(bell[index]) for index, weight in enumerate(lambdas)
    )
    # The Choi block of this state: chi(J) = (W (x) 1) J (W^dagger (x) 1) with
    # W = sqrt(tau^(one)) = sqrt(1/8) 1, and the sector's weight is tr tau = 1/4,
    # so omega = (1/4) state and J = omega / (1/8) = 2 state.
    choi_block = np.asarray(2.0 * state, dtype=np.complex128)
    branch = maps.branches[("match", pair)]
    t_total = 0.0
    trace_total = 0.0
    from certiqs_key.meat_core.objective.branch import trace_power_pinched

    for klass in branch.classes:
        operator = klass.kraus @ choi_block @ klass.kraus.conj().T
        t_total += trace_power_pinched(operator, alpha, klass.labels)
        trace_total += float(np.real(np.trace(operator)))
    bits = math.log2(t_total / trace_total) / (1.0 - alpha)
    assert bits == pytest.approx(
        bell_diagonal_bits(lambdas, alpha), abs=CLOSED_FORM_ATOL
    )


@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize("seed", (7, 8))
def test_the_ensemble_form_and_the_povm_form_it_denotes_agree(
    alpha: float, seed: int
) -> None:
    """``lem:choi-factor`` (iii), (iv) and ``lem:ensemble-form`` (ii).

    On the qubit BB84 declaration ``tau_A = 1/2`` is a multiple of the identity,
    so the support frame and the full frame coincide, ``N_x = M_x / 2`` is
    exactly representable, and the two declarations denote each other on the
    lattice. The objective and the gradient then agree at the same point, up to
    the rounding of ``sqrt(1/2)`` that the POVM route performs and the ensemble
    route does not -- which is one of the reasons the ensemble form exists.
    """
    povm = maps_of(qubit_bb84_general())
    ensemble = maps_of(qubit_bb84_general(ensemble=True))
    choi = random_choi_point(povm.parametrization, seed)
    q = honest_q(povm, choi)
    assert joint_statistics(ensemble, choi) == pytest.approx(
        joint_statistics(povm, choi), abs=CLOSED_FORM_ATOL
    )
    assert joint_objective_value(ensemble, q, choi, alpha) == pytest.approx(
        joint_objective_value(povm, q, choi, alpha), abs=CLOSED_FORM_ATOL
    )
    left = joint_gradient(povm, q, choi, alpha)
    right = joint_gradient(ensemble, q, choi, alpha)
    for pair in povm.joint_sectors:
        assert np.allclose(left.blocks[pair], right.blocks[pair], atol=1e-10)


def test_b6_the_party_local_reading_is_contained_in_the_scalar_one() -> None:
    """B-6's containment direction, on a toy two-factor declaration.

    ``def:homog``, the party-local form: a tagged entry "implies, in either
    mode, the untagged reading of the same entry, which is obtained from it by
    the partial trace over the other measured factors, and it is in general not
    implied by it". Both halves are exercised: a point satisfying the tagged row
    satisfies the untagged one, and a WITNESS satisfies the untagged row while
    failing the tagged one -- which is why the tagged feasible set is contained
    and the containment is strict.
    """
    tagged = two_factor_general(party_local=True)
    scalar = two_factor_general(party_local=False)
    tagged_maps = maps_of(tagged)
    sector = tagged.sector_index_set[0]
    pair = ("t0", sector)
    # THE WITNESS: the two stations correlated, |0><0| on the first factor
    # against a state the second factor's row reads at its bound.
    witness = 0.5 * np.kron(projector((1.0, 0.0)), projector((1.0, 0.0)))
    witness = witness + 0.5 * np.kron(
        projector((0.0, 1.0)), projector((0.0, 1.0))
    )
    state = {pair: np.asarray(witness, dtype=np.complex128)}
    scalar_value = entry_trace_value(scalar, 0, state)
    assert scalar_value == pytest.approx(0.25, abs=CLOSED_FORM_ATOL)
    check_joint_feasible(maps_of(scalar).parametrization, state)
    rows = party_local_value(tagged, 0, state)
    worst = max(
        float(np.max(np.linalg.eigvalsh(value))) for value in rows.values()
    )
    assert worst > 1e-9
    with pytest.raises(Exception, match="party_local"):
        check_joint_feasible(tagged_maps.parametrization, state)
    # And the other direction: a point satisfying the tagged row satisfies the
    # untagged one, the untagged value being the trace of the tagged one.
    balanced = {
        pair: np.asarray(
            np.kron(
                projector((1.0, 0.0)),
                0.5 * np.eye(2, dtype=np.complex128),
            )
            * 0.5
            + np.kron(
                projector((0.0, 1.0)),
                0.5 * np.eye(2, dtype=np.complex128),
            )
            * 0.5,
            dtype=np.complex128,
        )
    }
    for value in party_local_value(tagged, 0, balanced).values():
        assert float(np.max(np.linalg.eigvalsh(value))) <= 1e-12
    assert entry_trace_value(scalar, 0, balanced) <= 0.25 + 1e-12
