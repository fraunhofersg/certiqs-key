"""Regressions for C3 review: exact declarations and actual conic returns."""

from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest
from tests.support.general_toys import (
    decoy_like_general,
    honest_q,
    maps_of,
    random_choi_point,
    two_factor_general,
)
from tests.support.provenance import COMPILED

from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.joint import rank_one_sector
from certiqs_key.meat_core.objective.joint_rows import check_joint_feasible
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.solvers.frank_wolfe.driver import FrankWolfeOptions
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    _check_point,
    _oracle_vertex,
    _reports_optimal,
    coupling_residuals,
    joint_initial_point,
    run_joint_frank_wolfe,
)
from certiqs_key.solvers.oracles.acceptance import SingletonAcceptanceOracle
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle


@pytest.mark.parametrize("column", [(1, 2), (1, 1j)])
def test_rank_one_is_an_exact_identity_on_declared_entries(column: tuple[complex, ...]):
    d = decoy_like_general()
    vector = np.asarray(column, np.complex128)
    tau = np.outer(vector, vector.conj()) / 32
    marginal = dict(d.alice_marginal)
    marginal["rank1"] = tau
    # This helper deliberately tests just the shortcut predicate, not global
    # marginal normalization. Every entry of this outer product is exact.
    data = rank_one_sector(maps_of(replace(d, alice_marginal=marginal)), "rank1")
    assert data is not None
    assert np.allclose(data.weight * np.outer(data.vector, data.vector.conj()), tau)
    # A second positive dyadic eigenvalue survives in the actual declarations.
    marginal["rank1"] = np.diag([0.25, 2.0**-100]).astype(np.complex128)
    assert (
        rank_one_sector(maps_of(replace(d, alice_marginal=marginal)), "rank1") is None
    )


def test_review_decimal_example_is_not_exactly_rank_one():
    tau = 0.25 * np.outer([0.6, 0.8], [0.6, 0.8])
    determinant = (
        Fraction(float(tau[0, 0])) * Fraction(float(tau[1, 1]))
        - Fraction(float(tau[0, 1])) ** 2
    )
    assert determinant != 0
    d = decoy_like_general()
    marginal = dict(d.alice_marginal)
    marginal["rank1"] = tau.astype(np.complex128)
    assert (
        rank_one_sector(maps_of(replace(d, alice_marginal=marginal)), "rank1") is None
    )


def test_no_frame_carries_an_unused_inverse():
    frames = maps_of(decoy_like_general(ensemble=True)).parametrization.frames
    assert all(not hasattr(frame, "w_pinv") for frame in frames.values())


def test_sector_activity_unions_alice_sectors_before_checking_constancy():
    from certiqs_key.domain.manifest import KeyHolder, PartyLabel
    from certiqs_key.meat_core.declaration.general import (
        AliceFactor,
        Message,
        Transcript,
        sector_axis,
    )
    from certiqs_key.meat_core.declaration.general_sectors import general_sector_report

    d = decoy_like_general()

    def scalar(x: float) -> Matrix:
        return np.asarray([[x]], np.complex128)

    d = replace(
        d,
        alice=AliceFactor(PartyLabel.ALICE, sector_axis([("a", 1), ("b", 1)])),
        alice_alphabet=("0", "1"),
        alice_marginal={"a": scalar(0.5), "b": scalar(0.5)},
        alice_operators={
            "0": {"a": scalar(1), "b": scalar(0)},
            "1": {"a": scalar(0), "b": scalar(1)},
        },
        transcript=Transcript(
            (Message(KeyHolder.ALICE, ("all",), {("0", ()): "all", ("1", ()): "all"}),)
        ),
        accept_statistic={("all",): "match"},
        acceptance_values=("match",),
        key_map={(x, v): int(x) for x in ("0", "1") for v in d.bob_outcomes},
    )
    maps = maps_of(d)
    assert all(maps.key_inert.values())
    report = general_sector_report(maps)
    assert report.records[0].key_active
    assert not report.records[0].constraint_active


@pytest.mark.parametrize("alpha", [1.05, 1.5, 2.0])
def test_rank_deficient_ensemble_and_denoted_povm_agree(alpha: float):
    from tests.support.general_toys import qubit_bb84_general

    from certiqs_key.meat_core.declaration.general import AliceForm
    from certiqs_key.meat_core.objective.joint import joint_objective_value

    d = qubit_bb84_general()
    t = d.alice_sectors[0]
    tau = np.diag([1.0, 0.0]).astype(np.complex128)
    povm = replace(
        d,
        alice_marginal={t: tau},
        alice_operators={
            x: {t: np.eye(2, dtype=np.complex128) / 4} for x in d.alice_alphabet
        },
    )
    ensemble = replace(
        povm,
        alice_form=AliceForm.ENSEMBLE,
        alice_operators={x: {t: tau / 4} for x in d.alice_alphabet},
    )
    p, e = maps_of(povm), maps_of(ensemble)
    jp, je = (
        joint_initial_point(p.parametrization),
        joint_initial_point(e.parametrization),
    )
    q = {"match": 0.5, "mismatch": 0.5}
    assert joint_objective_value(p, q, jp, alpha) == pytest.approx(
        joint_objective_value(e, q, je, alpha), abs=1e-12
    )


@pytest.mark.parametrize(
    "diagnostics", [{}, {"status": "optimal"}, {"sol_status": "pdopt"}]
)
def test_optimal_vocabulary_stays_closed(diagnostics: dict[str, str]):
    assert not _reports_optimal(diagnostics)


@pytest.mark.requires_qics
def test_real_backend_contributes_a_bracket():
    maps = maps_of(decoy_like_general())
    start = joint_initial_point(maps.parametrization)
    result = run_joint_frank_wolfe(
        maps,
        QicsSectorChoiOracle(),
        SingletonAcceptanceOracle(honest_q(maps, start)),
        start,
        1.5,
        FrankWolfeOptions(max_iterations=1),
    )
    assert all(d["sol_status"] == "optimal" for d in result.oracle_diagnostics)
    assert result.h_lb is not None
    assert result.withdrawal is None


@pytest.mark.requires_qics
@pytest.mark.parametrize("trusted", [True, False])
def test_real_vertex_minimizes_product_and_satisfies_rows(trusted: bool):
    maps = maps_of(
        decoy_like_general() if trusted else two_factor_general(party_local=True)
    )
    p = maps.parametrization
    rng = np.random.default_rng(67)
    cost = {}
    for pair in p.joint_sectors:
        a = rng.normal(size=(p.block_dim(pair), p.block_dim(pair)))
        cost[pair] = (a + a.T).astype(np.complex128)
    diagnostics = []
    vertex, optimal = _oracle_vertex(maps, QicsSectorChoiOracle(), cost, diagnostics)
    assert optimal
    assert (
        max(coupling_residuals(p, vertex).values())
        < FrankWolfeOptions().iterate_coupling
    )
    check_joint_feasible(p, p.state_from_choi(vertex))
    value = sum(float(np.trace(cost[k] @ vertex[k]).real) for k in cost)
    assert value == pytest.approx(
        sum(float(d["primal_objective"]) for d in diagnostics), abs=1e-7
    )
    for seed in range(20):
        point = random_choi_point(p, seed)
        if not trusted:
            # The random coupling set need not satisfy the party-local row.
            try:
                check_joint_feasible(p, p.state_from_choi(point))
            except DeclarationError:
                continue
        assert (
            value <= sum(float(np.trace(cost[k] @ point[k]).real) for k in cost) + 1e-7
        )


@pytest.mark.requires_qics
def test_production_general_result_has_bound_length_and_frame_records():
    from certiqs_key.solvers.frank_wolfe.keyrate import solve

    d = replace(decoy_like_general(), source_replacement_license={"supplier": "test"})
    # Stands for compiled output (req:compiled-declaration-only).
    result = solve(
        d,
        QicsSectorChoiOracle(),
        options=FrankWolfeOptions(max_iterations=1),
        compiled=COMPILED,
    )
    assert result.h_lb is not None
    assert result.key_length is not None
    payload = result.as_payload()
    # Certified by default where the evaluation certifies a point
    # (frank-wolfe/req:certified-evaluation (vi)).
    assert payload["reported_tier"] in ("first-order", "certified")
    assert set(payload["optimizer_certificate"]["choi_input_basis"]) == set(
        d.alice_sectors
    )
    assert payload["assumption_ledger"]
    assert payload["mathematical_spec_version"] == "meat-core@1.28.0"
    assert payload["optimizer_certificate"]["accumulation_rule"]


def test_iterate_gate_checks_party_local_rows_beyond_scalar_coupling():
    from certiqs_key.meat_core.errors import SupportError

    scalar = maps_of(two_factor_general(party_local=False)).parametrization
    local = maps_of(two_factor_general(party_local=True)).parametrization
    bell = np.zeros((4, 4), dtype=np.complex128)
    bell[0, 0] = bell[3, 3] = bell[0, 3] = bell[3, 0] = 0.5
    point = {scalar.joint_sectors[0]: bell}
    _check_point(scalar, point, FrankWolfeOptions(), "initial")
    with pytest.raises(SupportError, match="constraint-row residual"):
        _check_point(local, point, FrankWolfeOptions(), "initial")


@pytest.mark.requires_qics
def test_dropped_production_result_keeps_bound_name_and_program():
    from certiqs_key.solvers.frank_wolfe.general_keyrate import solve_general

    d = replace(decoy_like_general(), source_replacement_license={"supplier": "test"})
    pair = maps_of(d).parametrization.joint_sectors[0]
    result = solve_general(
        d,
        QicsSectorChoiOracle(),
        options=FrankWolfeOptions(max_iterations=1),
        dropped=(("match", pair),),
        compiled=COMPILED,
    )
    assert result.h_lb is None
    assert result.h_lb_dropped is not None
    assert result.key_length is not None
    payload = result.as_payload()
    assert "h_lb" not in payload
    assert "h_low" not in payload
    assert payload["h_low_dropped"] == result.h_low
    assert payload["h_lb_dropped"] == result.h_lb_dropped
    assert payload["dropped_set"]
    assert (
        "meat-core/frank-wolfe/cor:fo-dropped"
        in payload["optimizer_certificate"]["claim_roots"]
    )


@pytest.mark.requires_qics
def test_general_missing_source_attestation_withholds_only_key_length():
    from certiqs_key.solvers.frank_wolfe.keyrate import solve

    result = solve(
        decoy_like_general(),
        QicsSectorChoiOracle(),
        options=FrankWolfeOptions(max_iterations=1),
    )
    assert result.h_lb is not None
    assert result.key_length is None
    assert str(result.reported_tier) == "estimate"


@pytest.mark.requires_qics
def test_compiled_two_party_artifact_docks_with_party_readouts():
    from tests.unit.test_protocol_general_compile import _two_party_specification

    from certiqs_key.meat_core.declaration.declaration import (
        AcceptanceSet,
        KeyLengthParameters,
    )
    from certiqs_key.meat_core.general_docking import dock_general_candidate
    from certiqs_key.protocol_compiler.compile import compile_specification
    from certiqs_key.solvers.frank_wolfe.keyrate import solve

    compiled = compile_specification(_two_party_specification())
    assert compiled.declaration is not None
    source = compiled.declaration
    count = len(source.acceptance_alphabet)
    d = dock_general_candidate(
        source,
        acceptance_set=AcceptanceSet(
            geometry="singleton",
            frequencies=tuple(Fraction(1, count) for _ in range(count)),
        ),
        rounds=1000,
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=1e-10, eps_ev=1e-10, lambda_ec=0
        ),
    )
    assert d.party_partition is not None
    assert not d.party_partition.is_default
    for x, v in source.outcome_pairs():
        assert d.announcement(x, v) == source.announcement(x, v)
    result = solve(
        d, QicsSectorChoiOracle(), options=FrankWolfeOptions(max_iterations=1)
    )
    assert result.as_payload()["sector_report"]


def test_general_docking_reads_supplier_rhs_blocks_without_changing_values():
    from tests.unit.test_protocol_general_format import (
        ALICE,
        FACTOR,
        MEASURED,
        _general_declaration,
    )

    from certiqs_key.domain.constraints import ConstraintEntry, Relation, RhsTag
    from certiqs_key.foundations.blocks import BlockOperator
    from certiqs_key.foundations.exact import identity, scale
    from certiqs_key.meat_core.declaration.declaration import (
        AcceptanceSet,
        KeyLengthParameters,
    )
    from certiqs_key.meat_core.general_docking import dock_general_candidate

    rhs = BlockOperator.of(ALICE, [identity(1), scale(Fraction(1, 2), identity(1))])
    entry = ConstraintEntry(
        operator=BlockOperator.of(MEASURED, [identity(2), identity(1)]),
        relation=Relation.LE,
        rhs=rhs,
        arriving_tag=RhsTag.GENERAL,
        scope=FACTOR,
    )
    candidate = _general_declaration(entries=(entry,))
    arguments = {
        "acceptance_set": AcceptanceSet(geometry="singleton", frequencies=(1.0,)),
        "rounds": 100,
        "parameters": KeyLengthParameters(
            alpha=1.05,
            eps_pa=1e-10,
            eps_ev=1e-10,
            lambda_ec=0,
        ),
    }
    block = dock_general_candidate(candidate, **arguments)
    dense = dock_general_candidate(
        replace(candidate, constraint_list=(replace(entry, rhs=rhs.dense()),)),
        **arguments,
    )
    for t in ALICE.labels:
        np.testing.assert_array_equal(
            block.constraint_list[0].bound[t], dense.constraint_list[0].bound[t]
        )


def test_product_factor_labels_are_looked_up_without_parsing_delimiters():
    from certiqs_key.meat_core.declaration.general import sector_axis

    original = two_factor_general(party_local=False)
    factors = []
    for factor in original.factors:
        letters = {v: f"_{v}_" for v in factor.alphabet}
        sectors = {s: f"_{s}_" for s in factor.sectors.labels}
        factors.append(
            replace(
                factor,
                alphabet=tuple(letters.values()),
                sectors=sector_axis(
                    tuple(
                        (sectors[s], factor.sectors.dims[s])
                        for s in factor.sectors.labels
                    )
                ),
                blocks={
                    letters[v]: {sectors[s]: block for s, block in blocks.items()}
                    for v, blocks in factor.blocks.items()
                },
            )
        )
    renamed = replace(original, factors=tuple(factors))
    for before, after in zip(original.bob_outcomes, renamed.bob_outcomes, strict=True):
        for bs, ass in zip(
            original.sector_index_set, renamed.sector_index_set, strict=True
        ):
            np.testing.assert_array_equal(
                original.bob_block(before, bs), renamed.bob_block(after, ass)
            )
    assert renamed.split_letter(renamed.bob_outcomes[0]) == tuple(
        f.alphabet[0] for f in factors
    )


def test_joint_reference_embeds_transcripts_and_rejects_missing_support():
    from certiqs_key.meat_core.objective.gradient import attains_the_reference_rank
    from certiqs_key.meat_core.objective.joint import (
        JointClassBranch,
        _joint_support_reference,
    )
    from certiqs_key.meat_core.objective.joint_gradient import _aggregate
    from certiqs_key.meat_core.objective.support import branch_support_dimension

    first = JointClassBranch(
        ("a",),
        (("x", "v0"), ("x", "v1")),
        np.eye(2, dtype=np.complex128) / 2,
        np.array([0, 1]),
    )
    second = replace(first, transcript=("b",))
    classes = (first, second)
    reference = _joint_support_reference(classes)
    assert reference == 4
    deficient = _aggregate(classes, np.diag([1.0, 0.0]).astype(np.complex128))
    assert not attains_the_reference_rank(deficient, reference)
    incorrect_shared_output = branch_support_dimension([first.kraus, second.kraus])
    assert incorrect_shared_output == 2
    assert attains_the_reference_rank(deficient, incorrect_shared_output)
    # The existing one GLOBAL relative SVD threshold still applies. A sum of
    # separately thresholded class ranks would incorrectly return four here.
    tiny = replace(second, kraus=second.kraus * 2.0**-100)
    assert _joint_support_reference((first, tiny)) == 2
