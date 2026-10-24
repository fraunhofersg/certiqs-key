"""The pointwise quantities, against the FROZEN oracle registry.

Every expected value here comes from ``tests/oracles/registry.py``, which was
written before any solver existed and may not be modified.
These tests compare ``src/certiqs_key/meat/objective`` against it.

TOLERANCES, AND WHY EACH IS WHAT IT IS
--------------------------------------
``abs=1e-12`` for identities that hold exactly in exact arithmetic and are
evaluated by a handful of floating-point operations on numbers of order one:
``K = T + P - tr G``, the sector form, the deficit signs, the trace split. The
only rounding is in ``eigh`` and the two powers, at the level of a few units in
the last place.

``abs=1e-9`` where a matrix power with exponent ``1/alpha`` sits between the
input and the compared number and the operator is only a few dimensions wide:
the branch entropy and the closed-form objective values. The support cutoff
lives three orders of magnitude below that (``1e-12`` relative), so a genuine
error cannot hide under it.

No tolerance here is wider than ``1e-9``, and none was widened to make a test
pass: the largest observed deviation on these toys is at the level of ``1e-13``.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from dummy_bundles import build_bundle
from registry import (
    ALPHA_GRID,
    O_HLOW_DEPHASED_TABLE,
    oracle,
)
from toy_admission import REFUSED_AT_1_0_0, admitted, is_refused
from toy_declarations import ALL_TOYS, ToyDeclaration, toy

from certiqs_key.meat_core.declaration.admission import AdmissionError
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.objective.branch import (
    branch_operator,
    dense_branch,
    evaluate_branches,
    generate_maps,
    is_key_inert,
    key_live_values,
    statistics,
    trace_power_pinched,
)
from certiqs_key.meat_core.objective.objective import acceptance_vector, objective_value

EXACT = 1e-12
POWERED = 1e-9


def declaration_of(toy_id: str) -> ProtocolDeclaration:
    """Return the validated declaration of a frozen toy, through its bundle."""
    return declaration_from_bundle(build_bundle(toy(toy_id)))


def weights(
    declaration: ProtocolDeclaration, values: dict[str, float]
) -> dict[str, np.ndarray]:
    """Return the block-diagonal state of a one-dimensional sector weighting."""
    return {
        sector: np.array([[values[sector]]], dtype=np.complex128)
        for sector in declaration.sector_index_set
    }


def mixed_state(
    declaration: ProtocolDeclaration, share: dict[str, float]
) -> dict[str, np.ndarray]:
    """Return the feasible state ``omega_s = share_s * tau_A x 1_{Q_s}/d_s``.

    Feasible for any Alice dimension: the sector blocks are PSD and
    ``tr_Q omega = sum_s share_s tau_A = tau_A`` when the shares sum to one
    (Eq. ``eq:feas``).
    """
    return {
        sector: np.asarray(
            share[sector]
            * np.kron(
                np.asarray(declaration.alice_marginal, dtype=np.complex128),
                np.eye(declaration.sector_dims[sector], dtype=np.complex128)
                / declaration.sector_dims[sector],
            ),
            dtype=np.complex128,
        )
        for sector in declaration.sector_index_set
    }


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize("w0", (0.0, 0.25, 0.5, 0.75, 1.0))
def test_o_k_identity_and_sector_form(alpha: float, w0: float) -> None:
    """O-K-IDENTITY: K = T + P - tr G, and Eq. eq:c5-sector as a THEOREM."""
    entry = oracle("O-K-IDENTITY")
    assert entry.claims == ("C5",)
    declaration = declaration_of("TOY-1")
    maps = generate_maps(declaration)
    values = evaluate_branches(
        maps, weights(declaration, {"s0": w0, "s1": 1.0 - w0}), alpha
    )["chat0"]
    assert values.p == pytest.approx(1.0, abs=EXACT)
    assert values.trace_g == pytest.approx(1.0, abs=EXACT)
    assert values.t == pytest.approx(w0 * 2.0 ** (1.0 - alpha) + (1.0 - w0), abs=EXACT)
    assert values.k == pytest.approx(1.0 + w0 * (2.0 ** (1.0 - alpha) - 1.0), abs=EXACT)
    assert values.k == pytest.approx(values.t + values.p - values.trace_g, abs=EXACT)
    assert values.k == pytest.approx(values.k_from_sector_form, abs=EXACT)
    assert values.deficits["s0"] == pytest.approx(
        w0 * (2.0 ** (1.0 - alpha) - 1.0), abs=EXACT
    )
    assert values.deficits["s1"] == pytest.approx(0.0, abs=EXACT)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_k_range(alpha: float) -> None:
    """O-K-RANGE: 0 <= K <= P at every feasible point.

    Theorem thm:branch-formula, C6.
    """
    assert oracle("O-K-RANGE").claims == ("C5", "C6")
    for toy_id in ("TOY-1", "TOY-2", "TOY-5", "TOY-6"):
        declaration = declaration_of(toy_id)
        maps = generate_maps(declaration)
        sectors = declaration.sector_index_set
        for share in (0.0, 0.3, 0.6, 1.0):
            rest = (1.0 - share) / max(len(sectors) - 1, 1)
            point = {s: (share if s == sectors[0] else rest) for s in sectors}
            for values in evaluate_branches(
                maps, weights(declaration, point), alpha
            ).values():
                assert values.k >= -EXACT
                assert values.k <= values.p + EXACT


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_deficit_sign(alpha: float) -> None:
    """O-DEFICIT-SIGN: f <= 0 always, and == 0 exactly on key-inert pairs."""
    assert oracle("O-DEFICIT-SIGN").claims == ("C6", "C7")
    expectations = {
        "TOY-1": {"s0": "negative", "s1": "zero"},
        "TOY-2": {"s0": "zero", "s1": "zero"},
    }
    for toy_id, expected in expectations.items():
        declaration = declaration_of(toy_id)
        maps = generate_maps(declaration)
        point = weights(declaration, {"s0": 0.5, "s1": 0.5})
        deficits = evaluate_branches(maps, point, alpha)["chat0"].deficits
        for sector, kind in expected.items():
            assert deficits[sector] <= EXACT
            if kind == "zero":
                assert deficits[sector] == pytest.approx(0.0, abs=EXACT)
                assert is_key_inert(declaration, "chat0", sector)
            else:
                assert deficits[sector] < -1e-3
                assert not is_key_inert(declaration, "chat0", sector)
    # TOY-3: f = m^{1-alpha} - 1 on the single key-active sector.
    declaration = declaration_of("TOY-3(m=2)")
    maps = generate_maps(declaration)
    deficits = evaluate_branches(
        maps, {"s0": np.array([[1.0]], dtype=np.complex128)}, alpha
    )["chat0"].deficits
    assert deficits["s0"] == pytest.approx(2.0 ** (1.0 - alpha) - 1.0, abs=EXACT)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize("toy_id", ("TOY-1", "TOY-2", "TOY-6"))
def test_o_sector_decomposition(alpha: float, toy_id: str) -> None:
    """O-SECTOR-DECOMPOSITION: the dense branch equals the direct sum of sectors.

    Lemma ``lem:branch-maps`` (iii), checked between two INDEPENDENTLY assembled
    objects:
    the dense Kraus operator on all of ``A x Q`` and the per-sector ones. The
    check is not trivial, because the key pinching groups rows by raw-key value,
    a partition that CUTS ACROSS the sectors.
    """
    assert oracle("O-SECTOR-DECOMPOSITION").claims == ("C2", "C5")
    declaration = declaration_of(toy_id)
    maps = generate_maps(declaration)
    sectors = declaration.sector_index_set
    assert declaration.alice_dim == 1  # the dense picture below is written for d_A = 1
    share = {
        s: (0.5 if i == 0 else 0.5 / (len(sectors) - 1)) for i, s in enumerate(sectors)
    }
    blocks = weights(declaration, share)
    dense_state = np.diag(np.array([share[s] for s in sectors], dtype=np.complex128))

    dense = dense_branch(maps, "chat0")
    dense_t = sum(
        trace_power_pinched(branch_operator(klass, dense_state), alpha, klass.labels)
        for klass in dense.classes
    )
    block_t = evaluate_branches(maps, blocks, alpha)["chat0"].t
    assert dense_t == pytest.approx(block_t, abs=POWERED)


@pytest.mark.contract
@pytest.mark.oracle
def test_o_trace_split() -> None:
    """O-TRACE-SPLIT: tr G + tr Theta = Phi(chat), and Phi sums to one."""
    assert oracle("O-TRACE-SPLIT").claims == ("C1", "C2")
    declaration = declaration_of("TOY-1")
    maps = generate_maps(declaration)
    values = evaluate_branches(maps, weights(declaration, {"s0": 0.5, "s1": 0.5}), 1.5)[
        "chat0"
    ]
    assert values.p == pytest.approx(1.0, abs=EXACT)
    assert values.trace_g == pytest.approx(1.0, abs=EXACT)
    assert values.p - values.trace_g == pytest.approx(0.0, abs=EXACT)

    for toy_id, expected in (
        ("TOY-4a", (0.25, 0.75)),
        ("TOY-4c", (0.0, 1.0)),
    ):
        declaration = declaration_of(toy_id)
        maps = generate_maps(declaration)
        point = {"s0": np.array([[1.0]], dtype=np.complex128)}
        phi = statistics(maps, point)
        assert phi["chat0"] == pytest.approx(expected[0], abs=EXACT)
        assert phi["chat1"] == pytest.approx(expected[1], abs=EXACT)
        assert sum(phi.values()) == pytest.approx(1.0, abs=EXACT)
        # Chat_key is empty, so every branch map is zero (Lemma lem:branch-maps (iv)).
        assert key_live_values(declaration) == ()
        for values in evaluate_branches(maps, point, 1.5).values():
            assert values.trace_g == pytest.approx(0.0, abs=EXACT)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize(("count", "expected"), O_HLOW_DEPHASED_TABLE)
def test_o_branch_entropy_and_fully_dephased(
    alpha: float, count: int, expected: float
) -> None:
    """O-BRANCH-ENTROPY and O-HLOW-FULLY-DEPHASED on the TOY-3 family."""
    assert oracle("O-BRANCH-ENTROPY").claims == ("C4", "C5")
    assert oracle("O-HLOW-FULLY-DEPHASED").value == 1.0
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
            declaration_of(f"TOY-3(m={count})")
        assert str(raised.value.reason) == REFUSED_AT_1_0_0[f"TOY-3(m={count})"]
        return
    declaration = declaration_of(f"TOY-3(m={count})")
    maps = generate_maps(declaration)
    point = {"s0": np.array([[1.0]], dtype=np.complex128)}
    values = evaluate_branches(maps, point, alpha)["chat0"]
    assert values.k == pytest.approx(float(count) ** (1.0 - alpha), abs=POWERED)
    # The independent value: the Renyi entropy of the uniform distribution on
    # m raw-key values, with a trivial conditioning system.
    entropy = math.log2(values.k / values.p) / (1.0 - alpha)
    assert entropy == pytest.approx(math.log2(count), abs=POWERED)
    assert objective_value(
        maps, acceptance_vector(declaration), point, alpha
    ) == pytest.approx(expected, abs=POWERED)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_kernel_conventions_reach_the_objective(alpha: float) -> None:
    """O-KERNEL-CONVENTIONS: d(u, 0) = +inf is what makes h_low infinite."""
    assert oracle("O-KERNEL-CONVENTIONS").claims == ("C9b",)
    declaration = declaration_of("TOY-4c")
    maps = generate_maps(declaration)
    value = objective_value(
        maps,
        acceptance_vector(declaration),
        {"s0": np.array([[1.0]], dtype=np.complex128)},
        alpha,
    )
    assert math.isinf(value)
    assert not math.isnan(value)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_hlow_divergence_only(alpha: float) -> None:
    """O-HLOW-DIVERGENCE-ONLY: the penalty really is the KL divergence."""
    entry = oracle("O-HLOW-DIVERGENCE-ONLY")
    declaration = declaration_of("TOY-4b")
    maps = generate_maps(declaration)
    value = objective_value(
        maps,
        acceptance_vector(declaration),
        {"s0": np.array([[1.0]], dtype=np.complex128)},
        alpha,
    )
    assert entry.closed_form is not None
    assert value == pytest.approx(entry.closed_form(alpha), abs=POWERED)
    # The number would differ under a Renyi divergence D_alpha.
    assert value == pytest.approx(
        (alpha / (alpha - 1.0)) * (1.0 - 0.5 * math.log2(3.0)), abs=POWERED
    )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_convexity_along_the_toy1_family(alpha: float) -> None:
    """O-CONVEXITY: K is concave (affine here) and the objective strictly convex."""
    assert oracle("O-CONVEXITY").claims == ("C9a", "C9b")
    declaration = declaration_of("TOY-1")
    maps = generate_maps(declaration)
    grid = [i / 20.0 for i in range(21)]
    ks = []
    objectives = []
    for w0 in grid:
        point = weights(declaration, {"s0": w0, "s1": 1.0 - w0})
        ks.append(evaluate_branches(maps, point, alpha)["chat0"].k)
        objectives.append(
            objective_value(maps, acceptance_vector(declaration), point, alpha)
        )
    for index in range(1, len(grid) - 1):
        midpoint = 0.5 * (ks[index - 1] + ks[index + 1])
        assert ks[index] >= midpoint - EXACT  # concave (affine)
        chord = 0.5 * (objectives[index - 1] + objectives[index + 1])
        assert objectives[index] <= chord + EXACT  # convex
    assert objectives[-1] > objectives[0]  # strictly increasing in w0


@pytest.mark.contract
@pytest.mark.oracle
def test_every_toy_reproduces_its_declared_statistics() -> None:
    """Phi computed from the POVMs equals the statistics each toy records.

    The toys record ``Phi`` per sector as hand-checked data; this module derives
    it from the declaration through Eq. ``eq:Phimap`` (Theorem ``thm:protocol-channel``
    (iii)). Agreement is the C1 check that the generated statistics map is the
    contract's.
    """
    # admitted(): TOY-3(m=3) is refused at 1.0.0 (condition (S); see
    # tests/support/toy_admission.py), and the refusal is asserted by
    # test_o_branch_entropy_and_fully_dephased above rather than skipped here.
    for declared in admitted(ALL_TOYS):
        declaration = declaration_of(declared.toy_id)
        maps = generate_maps(declaration)
        sectors = declaration.sector_index_set
        share = {s: 1.0 / len(sectors) for s in sectors}
        phi = statistics(maps, mixed_state(declaration, share))
        for chat, per_sector in declared.statistics.items():
            expected = sum(
                value * share[sector] for sector, value in per_sector.items()
            )
            assert phi[chat] == pytest.approx(expected, abs=EXACT), (
                declared.toy_id,
                chat,
            )


@pytest.mark.contract
def test_the_toys_this_module_reads_are_the_frozen_ones() -> None:
    """Guard against silent drift in what the golden tests are reading.

    THE FROZEN LIST IS UNCHANGED -- ``ALL_TOYS`` still holds twelve records,
    ``TOY-3(m=3)`` among them, and nothing frozen is edited. What this test
    reads is the list the golden tests SOLVE, which is the frozen list less the
    declarations 1.0.0 refuses at admission.
    """
    assert len({declared.toy_id for declared in ALL_TOYS}) == 12
    assert "TOY-3(m=3)" in {declared.toy_id for declared in ALL_TOYS}
    assert {declared.toy_id for declared in admitted(ALL_TOYS)} == {
        "TOY-1",
        "TOY-2",
        "TOY-2-AVG",
        "TOY-3(m=2)",
        "TOY-3(m=4)",
        "TOY-4a",
        "TOY-4b",
        "TOY-4c",
        "TOY-5",
        "TOY-6",
        "TOY-7",
    }
    assert isinstance(toy("TOY-1"), ToyDeclaration)
