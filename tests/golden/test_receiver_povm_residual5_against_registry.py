"""The fifth residual ``r_5`` and the route rule, against the registry.

Golden replay of ``RESIDUAL5_CASES``, ``RES5_EXPECTATION_CASES``,
``RESIDUAL_ROUTE_PRESENCE``, ``TOLERANCES_UNUSED_ON_ROUTE_I`` and
``RESIDUAL_NORM_0_2_0`` (oracle entry ``O-RP-RES5``), first frozen at registry
0.2.0 (a registry version is one of tests/oracles/registry_receiver_povm.py,
not of this module).

``rho(X) = max{ ||X - X^dagger||, (-lmin((X + X^dagger)/2))_+ }`` in the
SPECTRAL norm, and ``r_5`` is its maximum over EXACTLY the blocks the artifact
emits: every emitted letter ``v``, every ``0 <= n <= N``, and every declared
setting ``t``.

THE THREE THINGS THIS FILE EXISTS TO CATCH:

* ``rho`` is a maximum of TWO defects, and a block failing either is refused.
  ``R5-FAIL-HERMITICITY-DEFECT`` has the first non-zero and the second zero;
  ``R5-FAIL-NEGATIVE-EIGENVALUE`` has it the other way round. A test with only
  one of them would miss half the residual;
* THE DIRECTION IS REFUSE-ONLY. No block is Hermitized, symmetrized, projected
  onto the positive cone, clamped or repaired, and the reason is the
  contract-verbatim ``photon_block_positivity_residual_above_tolerance``;
* THE MAXIMUM INCLUDES ``n = 0``. ``R5-PASS-VACUUM-BLOCK-N0`` is the
  one-dimensional vacuum block, and an implementation that skipped the trivial
  blocks would report a maximum over a smaller set.

AND THE ROUTE RULE: ``r_1`` and ``r_3`` are ABSENT on route (i) -- absent, NOT
zero -- because "emitting 0 would report a check that was not made".
"""

from __future__ import annotations

import numpy as np
import pytest
from probe_presence import with_probe
from receiver_povm_support import (
    TOLERANCE,
    bb84_channel_only_request,
    mat_value,
    probe_receiver_request,
)
from registry_receiver_povm import (
    RES5_EXPECTATION_CASES,
    RESIDUAL5_CASES,
    RESIDUAL_NORM_0_2_0,
    RESIDUAL_ROUTE_PRESENCE,
    TOLERANCES_UNUSED_ON_ROUTE_I,
    rp_oracle,
)

from certiqs_key.receiver import (
    RESIDUAL_NORM,
    Refusal,
    RefusalReason,
    block_positivity_residual,
    check_residuals,
    construct_receiver,
    hermiticity_positivity_defect,
)
from certiqs_key.receiver.numerics import lambda_min, residual_norm


def _block(case_id: str) -> np.ndarray:
    """Return one frozen block as the module's own matrix."""
    case = next(c for c in RESIDUAL5_CASES if c.case_id == case_id)
    return mat_value(case.block)


@pytest.mark.contract
@pytest.mark.oracle
def test_rho_is_the_maximum_of_its_two_defects_case_by_case() -> None:
    """Eq. eq:rhodef, and Prop. prop:res5 (i) and (ii)."""
    assert rp_oracle("O-RP-RES5").claims == ("RC9",)
    assert RESIDUAL_NORM == RESIDUAL_NORM_0_2_0 == "spectral"
    for case in RESIDUAL5_CASES:
        block = mat_value(case.block)
        skew = residual_norm(block - block.conj().T)
        negativity = max(0.0, -lambda_min(block))
        assert skew == pytest.approx(float(case.hermiticity_defect), abs=1e-12), (
            case.case_id
        )
        assert negativity == pytest.approx(float(case.negativity_defect), abs=1e-12), (
            case.case_id
        )
        assert hermiticity_positivity_defect(block) == pytest.approx(
            float(case.rho), abs=1e-12
        ), case.case_id
        # Prop. prop:res5 (i): rho = 0 iff Hermitian AND positive.
        hermitian = bool(np.allclose(block, block.conj().T, atol=0.0, rtol=0.0))
        assert hermitian is case.hermitian, case.case_id
        assert (float(case.rho) == 0.0) is (hermitian and lambda_min(block) >= 0.0), (
            case.case_id
        )
        # Prop. prop:res5 (ii): on a Hermitian block rho reduces to eq:res2.
        if case.hermitian:
            assert hermiticity_positivity_defect(block) == pytest.approx(
                max(0.0, -lambda_min(block)), abs=1e-12
            ), case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_r_5_refuses_above_its_tolerance_and_repairs_nothing() -> None:
    """Req. req:residual-refusal: refuse-only, with the verbatim reason string."""
    for case in RESIDUAL5_CASES:
        block = mat_value(case.block)
        before = block.copy()
        residual = block_positivity_residual([{"v": block}], TOLERANCE)
        assert residual.residual_id == "r_5"
        assert residual.tolerance == TOLERANCE.eps_5
        assert residual.norm == RESIDUAL_NORM_0_2_0
        assert residual.value == pytest.approx(float(case.rho), abs=1e-12), case.case_id
        assert residual.passes is case.passes, case.case_id
        outcome = check_residuals((residual,))
        if case.passes:
            assert outcome is None, case.case_id
            assert case.refusal_reason is None, case.case_id
        else:
            assert isinstance(outcome, Refusal), case.case_id
            assert str(outcome.reason) == case.refusal_reason, case.case_id
            assert outcome.reason is (
                RefusalReason.PHOTON_BLOCK_POSITIVITY_RESIDUAL_ABOVE_TOLERANCE
            ), case.case_id
        # NOTHING IS REPAIRED: the block the caller handed in is untouched.
        assert np.array_equal(block, before), case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_the_expectation_bounds_of_prop_res5_iii_are_attained() -> None:
    """Prop. prop:res5 (iii), at the vectors the freeze says attain them."""
    vectors = {
        "psi = (1, 0)": np.asarray([1.0, 0.0], dtype=np.complex128),
        "psi = (1, i)/sqrt2": np.asarray([1.0, 1.0j], dtype=np.complex128)
        / np.sqrt(2.0),
        "psi = (0, 1)": np.asarray([0.0, 1.0], dtype=np.complex128),
    }
    for (
        case_id,
        description,
        real,
        imaginary,
        low,
        half,
        tight,
    ) in RES5_EXPECTATION_CASES:
        block = _block(case_id)
        psi = vectors[description]
        value = complex(psi.conj() @ block @ psi)
        assert value.real == pytest.approx(float(real), abs=1e-12), case_id
        assert value.imag == pytest.approx(float(imaginary), abs=1e-12), case_id
        # The two bounds hold ...
        assert value.real >= float(low) - 1e-12, case_id
        assert abs(value.imag) <= float(half) + 1e-12, case_id
        # ... and where the freeze says one is TIGHT, it is an equality.
        if tight == "real":
            assert value.real == pytest.approx(float(low), abs=1e-12), case_id
        elif tight == "imaginary":
            assert abs(value.imag) == pytest.approx(float(half), abs=1e-12), case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_r_5_runs_over_every_emitted_block_including_n_equals_zero() -> None:
    """Def. def:residuals: the maximum is over the blocks the artifact emits.

    The BB84 receiver at ``N = 2`` emits six letters at three photon numbers,
    ``n = 0`` included, and Prop. prop:res5 (iv) makes every one of them exactly
    Hermitian and positive -- so the emitted ``r_5`` is 0 to double precision.
    Re-evaluating ``rho`` over the artifact's OWN ``photon_blocks`` reproduces
    the emitted value, which is what makes the residual a statement about what
    is emitted rather than about a recomputation.
    """
    emission = construct_receiver(bb84_channel_only_request(photon_cutoff=2))
    assert emission.artifact is not None
    artifact = emission.artifact
    rows = [r for r in artifact.validation_results.residuals if r.residual_id == "r_5"]
    assert len(rows) == 1
    seen: list[float] = []
    photon_numbers: set[int] = set()
    for family in artifact.photon_blocks:
        for photons, letters in family.blocks:
            photon_numbers.add(photons)
            for _, block in letters:
                seen.append(hermiticity_positivity_defect(block))
    assert photon_numbers == {0, 1, 2}
    assert rows[0].value == pytest.approx(max(seen), abs=0.0)
    assert rows[0].value <= TOLERANCE.eps_5
    # The n = 0 blocks are one dimensional and ARE in the maximum.
    zero_blocks = [
        block
        for family in artifact.photon_blocks
        for photons, letters in family.blocks
        if photons == 0
        for _, block in letters
    ]
    assert zero_blocks and all(block.shape == (1, 1) for block in zero_blocks)


@pytest.mark.contract
@pytest.mark.oracle
def test_which_residuals_exist_on_which_route_absent_never_zero() -> None:
    """Def. def:residuals, "Which residuals exist on which route"."""
    frozen = {
        route: (present, absent) for route, present, absent in RESIDUAL_ROUTE_PRESENCE
    }
    assert set(frozen) == {"port_grams", "instrument_matrix", "element_graph"}

    def _ids(request: object) -> set[str]:
        emission = construct_receiver(request)  # type: ignore[arg-type]
        assert emission.artifact is not None
        return {r.residual_id for r in emission.artifact.validation_results.residuals}

    # Route (iii) and route (ii): all five exist.
    for build in (bb84_channel_only_request, *with_probe(probe_receiver_request)):
        route = (
            "element_graph"
            if build is bb84_channel_only_request
            else "instrument_matrix"
        )
        present, absent = frozen[route]
        emitted = _ids(build())
        assert set(present) <= emitted, route
        assert emitted & set(absent) == set(), route
        assert emitted == {"r_1", "r_2", "r_3", "r_4", "r_5"}, route

    # Route (i): r_1 and r_3 are ABSENT -- not present with the value zero.
    present, absent = frozen["port_grams"]
    emitted = _ids(_route_one_request())
    assert set(present) <= emitted
    assert emitted & set(absent) == set()
    assert emitted == {"r_2", "r_4", "r_5"}
    assert set(absent) == {"r_1", "r_3"}


@pytest.mark.contract
def test_the_unused_tolerances_are_still_required_on_route_i() -> None:
    """The inputs table: "an unused tolerance is unused, not an error"."""
    from dataclasses import replace as dc_replace

    assert TOLERANCES_UNUSED_ON_ROUTE_I == ("eps_1", "eps_3")
    request = _route_one_request()
    for missing in TOLERANCES_UNUSED_ON_ROUTE_I:
        declared = {
            key: value
            for key, value in request.numerical_tolerances.items()
            if key != missing
        }
        emission = construct_receiver(
            dc_replace(request, numerical_tolerances=declared)
        )
        assert emission.artifact is None, missing
        assert emission.refusal is not None
        assert emission.refusal.reason is RefusalReason.NUMERICAL_TOLERANCE_MISSING
    # And with all six declared the route-(i) request emits.
    assert construct_receiver(request).artifact is not None


def _route_one_request() -> object:
    """Return a route-(i) request: the BB84 Grams, declared directly."""
    from dataclasses import replace as dc_replace

    from certiqs_key.receiver import GramFamily, port_grams, restrict_to_inputs
    from certiqs_key.receiver.graph import compile_element_graph

    seed = bb84_channel_only_request(photon_cutoff=1)
    assert seed.element_graph is not None
    gamma = compile_element_graph(seed.element_graph, len(seed.mode_space))
    gamma_inp = restrict_to_inputs(gamma, seed.input_modes.subsystem_order())
    rows = [modes for _, modes in seed.port_map.entries]
    family = GramFamily(seed.port_map.labels, port_grams(gamma_inp, rows))
    return dc_replace(seed, element_graph=None, port_grams=family)


@pytest.mark.contract
def test_the_frozen_r5_values_are_not_a_second_norm_reading() -> None:
    """The norm is named: rho is a determinate number under it.

    The registry-0.1.3 device of freezing a failing residual under BOTH natural
    readings is gone, because Def. def:residuals names the spectral norm. Under
    the OTHER reading -- the squared Frobenius one the registry carried at
    0.1.3 -- the Hermiticity case would give a DIFFERENT number, so the frozen
    value pins the norm and not merely the verdict.
    """
    block = _block("R5-FAIL-HERMITICITY-DEFECT")
    skew = block - block.conj().T
    spectral = residual_norm(skew)
    frobenius_squared = float(np.sum(np.abs(skew) ** 2))
    assert spectral == pytest.approx(0.25, abs=1e-12)
    assert frobenius_squared == pytest.approx(0.125, abs=1e-12)
    assert spectral != pytest.approx(frobenius_squared, abs=1e-3)
