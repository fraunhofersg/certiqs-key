"""B3 on matched qubit data extracted from the emitted BBM92 stations.

This is deliberately a one-photon-sector comparison.  The production BBM92
declaration also contains vacuum and flag sectors; they are neither deleted
from that declaration nor silently identified with this qubit restriction.
"""

from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest
from instances.bbm92.surface import default_config, preparation
from instances.common.honest.ideal_pair import IdealPair, honest_provider
from tests.oracles.registry_instances_bbm92 import (
    BBM92_SYMMETRIC_ERROR,
    O_BBM92_B3_UNTRUSTED_IS_LARGER,
)

from certiqs_key.domain.manifest import KeyHolder, PartyLabel
from certiqs_key.foundations.exact import identity, matrix, scale, trace
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet, PartyPartition
from certiqs_key.meat_core.declaration.general import (
    AliceFactor,
    AliceForm,
    GeneralDeclaration,
    MeasuredFactor,
    sector_axis,
)
from certiqs_key.meat_core.declaration.general_validation import (
    validate_general_declaration,
)
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    build_joint_maps,
    joint_choi_parametrization,
    joint_objective_value,
    joint_statistics,
    normalise_dropped_set,
)
from certiqs_key.meat_core.objective.joint_gradient import joint_gradient
from certiqs_key.meat_core.objective.joint_rows import check_joint_feasible
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    joint_initial_point,
    run_joint_frank_wolfe,
)
from certiqs_key.solvers.oracles.acceptance import SingletonAcceptanceOracle
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle
from certiqs_key.transmitter.certificate import (
    SourceReplacementCertificate,
    SourceReplacementLicense,
    verify_certificate,
)

ALPHA = 1.5
ERROR = BBM92_SYMMETRIC_ERROR.error_rate
VISIBILITY = 1 - 2 * ERROR
PHOTON_SECTOR = "C:1"
QUBIT_A = "qubit_a"
QUBIT_B = "qubit_b"


def _emitted_bbm92() -> tuple[CandidateDeclaration, GeneralDeclaration]:
    """Compile the actual stations at the frozen B3 error and Z-only keying."""
    config = default_config()
    config = replace(
        config,
        device={
            **config.device,
            "test_fraction": BBM92_SYMMETRIC_ERROR.test_coin,
            "key_bases": "Z",
        },
        model={**config.model, "visibility": VISIBILITY},
        parameters=replace(config.parameters, alpha=ALPHA),
    )
    prepared = preparation(config)
    candidate = prepared.declaration
    frequencies = honest_provider(
        IdealPair(visibility=VISIBILITY)
    )(candidate)
    declaration = dock_general_candidate(
        candidate,
        acceptance_set=AcceptanceSet(
            geometry="singleton",
            frequencies=tuple(
                float(frequencies[value])
                for value in candidate.acceptance_alphabet
            ),
        ),
        rounds=config.rounds,
        parameters=config.parameters,
    )
    return candidate, declaration


def _qubit_factor(factor: MeasuredFactor, sector: str, label: str) -> MeasuredFactor:
    return replace(
        factor,
        sectors=sector_axis([(label, 2)]),
        blocks={
            outcome: {label: factor.blocks[outcome][sector]}
            for outcome in factor.alphabet
        },
    )


def _matched_pair() -> tuple[
    CandidateDeclaration, GeneralDeclaration, GeneralDeclaration
]:
    """Return the B3 pair, identified letter for letter on qubit blocks."""
    candidate, emitted = _emitted_bbm92()
    station_a = _qubit_factor(emitted.factors[0], PHOTON_SECTOR, QUBIT_A)
    station_b = _qubit_factor(emitted.factors[1], PHOTON_SECTOR, QUBIT_B)
    source_replacement_license = _source_certificate(candidate)
    (source_letter,) = emitted.alice_alphabet

    untrusted_outcomes = tuple(
        f"{a}__{b}" for a in station_a.alphabet for b in station_b.alphabet
    )
    partition = PartyPartition(
        readout_alice={
            (source_letter, f"{a}__{b}"): a
            for a in station_a.alphabet
            for b in station_b.alphabet
        },
        readout_bob={
            (source_letter, f"{a}__{b}"): b
            for a in station_a.alphabet
            for b in station_b.alphabet
        },
        alphabet_alice=station_a.alphabet,
        alphabet_bob=station_b.alphabet,
        party_of_alice_system=PartyLabel.ALICE,
        party_of_sector_factors={
            f"{QUBIT_A}__{QUBIT_B}": (PartyLabel.ALICE, PartyLabel.BOB)
        },
    )
    untrusted = replace(
        emitted,
        factors=(station_a, station_b),
        party_partition=partition,
        sector_block_kind="photon_number",
        constraint_list=(),
        constraints_through_a_reductions_chain=0,
        attack_set_license=None,
    )

    trusted = GeneralDeclaration(
        alice=AliceFactor(
            party=PartyLabel.ALICE, sectors=sector_axis([(QUBIT_A, 2)])
        ),
        alice_marginal={QUBIT_A: 0.5 * np.eye(2, dtype=np.complex128)},
        alice_alphabet=station_a.alphabet,
        alice_operators={
            outcome: {QUBIT_A: station_a.blocks[outcome][QUBIT_A]}
            for outcome in station_a.alphabet
        },
        alice_form=AliceForm.POVM,
        factors=(station_b,),
        transcript=emitted.transcript,
        accept_statistic=emitted.accept_statistic,
        key_map={
            (a, b): emitted.key_map[(source_letter, f"{a}__{b}")]
            for a in station_a.alphabet
            for b in station_b.alphabet
        },
        key_holder=KeyHolder.ALICE,
        acceptance_values=emitted.acceptance_values,
        key_value_count=emitted.key_value_count,
        acceptance_set=emitted.acceptance_set,
        rounds=emitted.rounds,
        parameters=emitted.parameters,
        sector_block_kind="photon_number",
        source_replacement_license=source_replacement_license,
    )
    validate_general_declaration(untrusted)
    validate_general_declaration(trusted)
    assert set(untrusted_outcomes) == set(untrusted.bob_outcomes)
    return candidate, untrusted, trusted


def _source_certificate(candidate: CandidateDeclaration) -> dict[str, object]:
    """Verify a maximally entangled certificate for Alice's emitted qubit POVM."""
    assert candidate.bob_factors is not None
    family = candidate.bob_factors.factors[0]
    sector_index = family.members[0].sector_map.labels.index(PHOTON_SECTOR)
    povm = {
        outcome: family.member(outcome).blocks[sector_index]
        for outcome in family.alphabet
    }
    weights = {
        outcome: trace(element).re / 2 for outcome, element in povm.items()
    }
    states = {
        outcome: (
            scale(Fraction(1, 2), identity(2))
            if weight == 0
            else scale(Fraction(1, 2) / weight, element)
        )
        for (outcome, element), weight in zip(
            povm.items(), weights.values(), strict=True
        )
    }
    phi_plus = matrix(
        (
            (Fraction(1, 2), 0, 0, Fraction(1, 2)),
            (0, 0, 0, 0),
            (0, 0, 0, 0),
            (Fraction(1, 2), 0, 0, Fraction(1, 2)),
        )
    )
    certificate = SourceReplacementCertificate(
        alice_marginal=scale(Fraction(1, 2), identity(2)),
        psi=phi_plus,
        virtual_dim=2,
        virtual_weights=weights,
        virtual_states=states,
    )
    verification = verify_certificate(certificate, family.alphabet, povm)
    assert verification.refusal() is None
    return SourceReplacementLicense.pass_through(
        verification, None, certificate
    ).as_machine_record()


def _depolarized_pair() -> np.ndarray:
    """Return the frozen honest Bell-diagonal state, (61,1,1,1)/64."""
    bell = (
        np.asarray((1, 0, 0, 1), np.complex128),
        np.asarray((1, 0, 0, -1), np.complex128),
        np.asarray((0, 1, 1, 0), np.complex128),
        np.asarray((0, 1, -1, 0), np.complex128),
    )
    weights = (61 / 64, 1 / 64, 1 / 64, 1 / 64)
    return sum(
        weight * np.outer(vector, vector.conj()) / 2
        for weight, vector in zip(weights, bell, strict=True)
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_matched_qubit_pair_has_one_objective_and_only_one_extra_condition():
    _, untrusted, trusted = _matched_pair()

    assert "<=" in O_BBM92_B3_UNTRUSTED_IS_LARGER.relation
    assert O_BBM92_B3_UNTRUSTED_IS_LARGER.recorded_not_asserted
    assert untrusted.source_replacement_license is None
    assert trusted.source_replacement_license is not None
    assert trusted.source_replacement_license["sr1_holds"] is True
    assert trusted.source_replacement_license["sr2_holds"] is True
    assert untrusted.alice_marginal is None
    assert np.array_equal(trusted.alice_marginal[QUBIT_A], np.eye(2) / 2)
    assert untrusted.transcript == trusted.transcript
    assert untrusted.accept_statistic == trusted.accept_statistic
    assert untrusted.acceptance_values == trusted.acceptance_values
    assert untrusted.acceptance_set == trusted.acceptance_set
    assert untrusted.parameters.alpha == trusted.parameters.alpha == ALPHA
    assert {"test:H|V", "test:V|H", "test:D|A", "test:A|D"} <= set(
        untrusted.acceptance_values
    )

    maps_u = build_joint_maps(joint_choi_parametrization(untrusted))
    maps_t = build_joint_maps(joint_choi_parametrization(trusted))
    omega = _depolarized_pair()
    state_u = {(untrusted.alice_sectors[0], untrusted.sector_index_set[0]): omega}
    # For tau_A = I/2, chi(J) = J/2; therefore J = 2 omega.
    state_t = {(trusted.alice_sectors[0], trusted.sector_index_set[0]): 2 * omega}
    q_u = joint_statistics(maps_u, state_u)
    q_t = joint_statistics(maps_t, state_t)
    assert q_u == pytest.approx(q_t, abs=2e-15)
    assert q_u == pytest.approx(
        dict(
            zip(
                untrusted.acceptance_values,
                untrusted.acceptance_set.frequencies,
                strict=True,
            )
        ),
        abs=2e-15,
    )
    for agreeing, disagreeing in (
        (("test:H|H", "test:V|V"), ("test:H|V", "test:V|H")),
        (("test:D|D", "test:A|A"), ("test:D|A", "test:A|D")),
    ):
        tested = sum(q_u[value] for value in (*agreeing, *disagreeing))
        errors = sum(q_u[value] for value in disagreeing)
        assert errors / tested == pytest.approx(float(ERROR), abs=2e-15)
    assert sum(q_u.values()) == pytest.approx(1.0, abs=2e-15)
    assert joint_objective_value(maps_u, q_u, state_u, ALPHA) == pytest.approx(
        joint_objective_value(maps_t, q_t, state_t, ALPHA), abs=2e-12
    )

    # The inclusion is strict: this normalized state is allowed without a
    # marginal and fails precisely the trusted I/2 marginal condition.
    biased = np.diag((0.5, 0.5, 0.0, 0.0)).astype(np.complex128)
    check_joint_feasible(maps_u.parametrization, {next(iter(state_u)): biased})
    with pytest.raises(DeclarationError, match="marginal, trusted-source mode"):
        check_joint_feasible(maps_t.parametrization, {next(iter(state_t)): biased})


@pytest.mark.requires_qics
@pytest.mark.contract
@pytest.mark.oracle
def test_real_qics_matched_comparison_reports_both_gaps():
    _, untrusted, trusted = _matched_pair()
    results = []
    for declaration in (untrusted, trusted):
        q = dict(
            zip(
                declaration.acceptance_values,
                declaration.acceptance_set.frequencies,
                strict=True,
            )
        )
        maps = build_joint_maps(
            joint_choi_parametrization(declaration),
            acceptance_support=tuple(value for value, mass in q.items() if mass > 0),
        )
        result = run_joint_frank_wolfe(
            maps,
            QicsSectorChoiOracle(),
            SingletonAcceptanceOracle(q),
            joint_initial_point(maps.parametrization),
            ALPHA,
            FrankWolfeOptions(max_iterations=12),
        )
        assert result.withdrawal is None
        assert result.h_lb is not None
        assert np.isfinite(result.objective)
        assert np.isfinite(result.gap)
        assert result.iterations <= 12
        results.append(result)

    untrusted_result, trusted_result = results
    # A lower bracket for the larger set must not sit above an upper estimate
    # for its trusted subset.  Equality is intentionally not asserted.
    assert untrusted_result.h_lb <= trusted_result.objective + 1e-8
    assert untrusted_result.gap >= 0
    assert trusted_result.gap >= 0


def _random_untrusted_state(
    declaration: GeneralDeclaration, pairs: tuple, rng: np.random.Generator
) -> dict:
    """Return a random full-rank state over the joint sectors, of trace one."""
    blocks = {}
    for pair in pairs:
        dim = declaration.joint_block_dim(*pair)
        g = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
        blocks[pair] = g @ g.conj().T * rng.uniform(0.05, 1.0)
    total = sum(float(np.trace(block).real) for block in blocks.values())
    return {pair: block / total for pair, block in blocks.items()}


@pytest.mark.requires_qics
@pytest.mark.contract
def test_untrusted_dropped_program_bounds_its_own_value():
    """``frank-wolfe/cor:fo-dropped`` in untrusted-source mode, through the driver.

    The emitted BBM92 declaration is in untrusted-source mode (no Alice
    marginal; the coupling is the normalisation). Dropping the key-active
    pair (gen, one photon at each station), the driver runs the dropped
    program: it withdraws nothing, reports the bracket as ``h_lb_dropped``
    and never as ``h_lb``, the dropped gradient agrees with central finite
    differences of ``O^D`` (``meat-core/cor:full-gradient`` read at ``D``), and
    the bracket lies below ``O^D`` at the run's estimate and at random
    feasible points, each a member of the program whose infimum it bounds.
    """
    _, declaration = _emitted_bbm92()
    assert not declaration.is_trusted_source
    assert declaration.alice_marginal is None
    q = dict(
        zip(
            declaration.acceptance_values,
            declaration.acceptance_set.frequencies,
            strict=True,
        )
    )
    maps = build_joint_maps(
        joint_choi_parametrization(declaration),
        acceptance_support=tuple(value for value, mass in q.items() if mass > 0),
    )
    (alice_sector,) = declaration.alice_sectors
    pair = (alice_sector, f"{PHOTON_SECTOR}__{PHOTON_SECTOR}")
    dropped_pair = ("gen", pair)
    assert not maps.key_inert[dropped_pair]
    dropped = normalise_dropped_set(maps, [dropped_pair])

    start = joint_initial_point(maps.parametrization)
    result = run_joint_frank_wolfe(
        maps,
        QicsSectorChoiOracle(),
        SingletonAcceptanceOracle(q),
        start,
        ALPHA,
        FrankWolfeOptions(max_iterations=15),
        dropped=[dropped_pair],
    )
    assert result.withdrawal is None
    assert result.h_lb is None
    assert result.h_lb_dropped is not None
    assert result.dropped_set == (dropped_pair,)
    bound = result.h_lb_dropped

    # The gradient of O^D against central differences, at an interior point
    # between the start and the estimate (full rank, so every direction is
    # admissible both ways), along random Hermitian directions over every
    # block and along a q direction that keeps the support positive.
    point = {key: 0.5 * (start[key] + result.choi[key]) for key in start}
    check_joint_feasible(maps.parametrization, point)
    gradient = joint_gradient(maps, q, point, ALPHA, dropped=dropped)
    assert gradient.dropped_pieces == (dropped_pair,)
    # The undropped gradient differs here, so the check sees the dropped piece.
    undropped = joint_gradient(maps, q, point, ALPHA)
    rng = np.random.default_rng(20261016)
    step = 1e-6
    for _ in range(3):
        direction = {}
        for key, block in point.items():
            g = rng.normal(size=block.shape) + 1j * rng.normal(size=block.shape)
            direction[key] = 0.5 * (g + g.conj().T) * float(np.trace(block).real)
        plus = {key: point[key] + step * direction[key] for key in point}
        minus = {key: point[key] - step * direction[key] for key in point}
        numerical = (
            joint_objective_value(maps, q, plus, ALPHA, dropped=dropped)
            - joint_objective_value(maps, q, minus, ALPHA, dropped=dropped)
        ) / (2 * step)
        analytic = sum(
            float(np.trace(gradient.blocks[key] @ direction[key]).real)
            for key in point
        )
        assert abs(analytic) > 1e-4
        assert analytic == pytest.approx(numerical, rel=1e-5, abs=1e-8)
        other = sum(
            float(np.trace(undropped.blocks[key] @ direction[key]).real)
            for key in point
        )
        assert abs(other - analytic) > 1e-3 * abs(analytic)
    support = maps.acceptance_support
    assert "gen" in support and support[-1] != "gen"
    q_direction = dict.fromkeys(q, 0.0)
    q_direction["gen"], q_direction[support[-1]] = 1.0, -1.0
    q_step = 1e-7
    numerical_q = (
        joint_objective_value(
            maps,
            {v: q[v] + q_step * q_direction[v] for v in q},
            point,
            ALPHA,
            dropped=dropped,
        )
        - joint_objective_value(
            maps,
            {v: q[v] - q_step * q_direction[v] for v in q},
            point,
            ALPHA,
            dropped=dropped,
        )
    ) / (2 * q_step)
    analytic_q = sum(gradient.q[v] * q_direction[v] for v in gradient.q)
    assert analytic_q == pytest.approx(numerical_q, rel=1e-5, abs=1e-8)

    # h_lb_dropped <= O^D at the estimate, which the dropped value never
    # exceeds the undropped one at (prop:drop-bound (ii)) ...
    at_estimate = joint_objective_value(
        maps, result.q, result.choi, ALPHA, dropped=dropped
    )
    assert bound <= at_estimate
    assert at_estimate <= joint_objective_value(maps, result.q, result.choi, ALPHA)
    # ... and at random feasible points of the same program.
    for _ in range(40):
        state = _random_untrusted_state(declaration, maps.joint_sectors, rng)
        check_joint_feasible(maps.parametrization, state)
        assert bound <= joint_objective_value(maps, q, state, ALPHA, dropped=dropped)
