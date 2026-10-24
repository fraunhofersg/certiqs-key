"""Structural identities of the contracted objective (C1, C2, C5, C6, C7).

spec/architecture.md Section 14.3 asks for "structural identities linking K, T,
P, and G on hand-authored dummy bundles" and "dense versus block objective
equality". Each test below pins one registry entry; the registry carries the
derivation and the entry ID is named in the test.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from reference import (
    branch_entropy,
    branch_operator,
    key_pinch,
    psd_power,
    sector_deficit,
    trace_power_pinched,
)
from registry import oracle
from toy_declarations import (
    TOY1_RETENTION,
    TOY2_DETERMINISTIC,
    TOY3_DEPHASED_3,
    TOY4A_ZERO_GENERATION,
    TOY4C_INFEASIBLE,
    TOY5_CONSTRAINED,
    fully_dephased,
)
from toy_evaluation import branch_values, statistics

ALPHAS = (1.05, 1.25, 1.5, 1.75, 1.9)
WEIGHTS = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)


def _pair(w0: float) -> dict[str, float]:
    return {"s0": w0, "s1": 1.0 - w0}


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
@pytest.mark.parametrize("w0", WEIGHTS)
def test_k_equals_t_plus_p_minus_trace_g(alpha: float, w0: float) -> None:
    """O-K-IDENTITY: K = T + P - tr G, and equals the sector form P + sum_s f_s."""
    entry = oracle("O-K-IDENTITY")
    assert "C5" in entry.claims

    values = branch_values(TOY1_RETENTION, alpha, _pair(w0))["chat0"]

    # The hand-derived closed forms of contract Prop. prop:retention.
    assert values.p == pytest.approx(1.0)
    assert values.trace_g == pytest.approx(1.0)
    assert values.t == pytest.approx(w0 * 2.0 ** (1.0 - alpha) + (1.0 - w0))
    assert values.k == pytest.approx(1.0 + w0 * (2.0 ** (1.0 - alpha) - 1.0))

    # Eq. eq:fK against the sector form Eq. eq:c5-sector (a theorem, not a
    # definition): the two routes to K must agree.
    assert values.k == pytest.approx(values.t + values.p - values.trace_g)
    assert values.k == pytest.approx(values.p + sum(values.deficits.values()))


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
@pytest.mark.parametrize("w0", WEIGHTS)
def test_k_lies_between_zero_and_p(alpha: float, w0: float) -> None:
    """O-K-RANGE: 0 <= K <= P, the bounds Theorem thm:branch-formula proves."""
    assert "C6" in oracle("O-K-RANGE").claims
    for toy in (TOY1_RETENTION, TOY2_DETERMINISTIC, TOY5_CONSTRAINED):
        for values in branch_values(toy, alpha, _pair(w0)).values():
            assert values.k >= -1e-12
            assert values.k <= values.p + 1e-12

    dephased = branch_values(TOY3_DEPHASED_3, alpha, {"s0": 1.0})["chat0"]
    assert 0.0 <= dephased.k <= dephased.p
    assert dephased.k == pytest.approx(3.0 ** (1.0 - alpha))


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_sector_deficits_are_non_positive(alpha: float) -> None:
    """O-DEFICIT-SIGN: f <= 0, and f == 0 exactly on the key-inert pairs."""
    assert oracle("O-DEFICIT-SIGN").claims == ("C6", "C7")

    for w0 in WEIGHTS:
        deficits = branch_values(TOY1_RETENTION, alpha, _pair(w0))["chat0"].deficits
        assert deficits["s0"] == pytest.approx(w0 * (2.0 ** (1.0 - alpha) - 1.0))
        assert deficits["s0"] <= 1e-12
        # C7: the key-inert sector contributes exactly zero for EVERY input.
        assert deficits["s1"] == pytest.approx(0.0, abs=1e-12)
        if w0 > 0.0:
            assert deficits["s0"] < -1e-9  # key-active: strictly negative

        # TOY-2: both pairs key-inert, so both deficits vanish identically.
        both = branch_values(TOY2_DETERMINISTIC, alpha, _pair(w0))["chat0"].deficits
        assert both["s0"] == pytest.approx(0.0, abs=1e-12)
        assert both["s1"] == pytest.approx(0.0, abs=1e-12)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_pinching_monotonicity_and_its_equality_case(alpha: float) -> None:
    """C6, foundations/lem:pinchmono: T <= tr G, with equality iff G is Z-invariant."""
    key_active = branch_operator(
        TOY1_RETENTION.branches["chat0"][0].kraus, np.array([[0.4]])
    )
    labels = TOY1_RETENTION.branches["chat0"][0].row_key_values
    assert trace_power_pinched(key_active, alpha, labels) < float(np.trace(key_active))
    # Not a fixed point of Z, which is the equality condition of the lemma.
    assert not np.allclose(key_pinch(key_active, labels), key_active)

    key_inert = branch_operator(
        TOY1_RETENTION.branches["chat0"][1].kraus, np.array([[0.6]])
    )
    inert_labels = TOY1_RETENTION.branches["chat0"][1].row_key_values
    assert np.allclose(key_pinch(key_inert, inert_labels), key_inert)
    assert trace_power_pinched(key_inert, alpha, inert_labels) == pytest.approx(
        float(np.trace(key_inert))
    )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
@pytest.mark.parametrize("w0", WEIGHTS)
def test_dense_and_block_branch_operators_agree(alpha: float, w0: float) -> None:
    """O-SECTOR-DECOMPOSITION: the dense branch is the direct sum of the blocks."""
    assert "C2" in oracle("O-SECTOR-DECOMPOSITION").claims
    toy = TOY1_RETENTION
    weights = _pair(w0)

    dense = toy.dense_branches["chat0"]
    omega = np.diag([weights[s] for s in toy.sector_index_set])
    dense_operator = branch_operator(dense.kraus, omega)

    # Blockwise: read each sector's rows out of the dense operator and compare
    # against the independently hand-written per-sector branch operator.
    for branch in toy.branches["chat0"]:
        rows = [i for i, s in enumerate(dense.row_sectors) if s == branch.sector]
        block = dense_operator[np.ix_(rows, rows)]
        expected = branch_operator(branch.kraus, np.array([[weights[branch.sector]]]))
        assert np.allclose(block, expected)

    # Off-block entries vanish: that is Lemma lem:branch-maps (iii).
    for i, si in enumerate(dense.row_sectors):
        for j, sj in enumerate(dense.row_sectors):
            if si != sj:
                assert dense_operator[i, j] == pytest.approx(0.0, abs=1e-14)

    # And the scalar the objective actually consumes agrees on both routes.
    dense_t = trace_power_pinched(dense_operator, alpha, dense.row_key_values)
    block_t = sum(
        trace_power_pinched(
            branch_operator(b.kraus, np.array([[weights[b.sector]]])),
            alpha,
            b.row_key_values,
        )
        for b in toy.branches["chat0"]
    )
    assert dense_t == pytest.approx(block_t)


@pytest.mark.contract
@pytest.mark.oracle
def test_key_pinching_cuts_across_sectors() -> None:
    """The pinching and the sector split are different partitions of the rows.

    Recorded with O-SECTOR-DECOMPOSITION: rows ``(v0, s0)`` and ``(v0, s1)``
    carry the same raw-key value and different sectors, so the sector form of
    Eq. eq:c5-sector is a real theorem rather than a relabelling.
    """
    dense = TOY1_RETENTION.dense_branches["chat0"]
    same_key_different_sector = [
        (i, j)
        for i in range(len(dense.row_key_values))
        for j in range(len(dense.row_key_values))
        if dense.row_key_values[i] == dense.row_key_values[j]
        and dense.row_sectors[i] != dense.row_sectors[j]
    ]
    assert same_key_different_sector


@pytest.mark.contract
@pytest.mark.oracle
def test_trace_split_and_statistics_normalization() -> None:
    """O-TRACE-SPLIT: tr G + tr Theta = Phi(chat), and Phi is a distribution."""
    assert oracle("O-TRACE-SPLIT").claims == ("C1", "C2")

    values = branch_values(TOY1_RETENTION, 1.5, _pair(0.3))["chat0"]
    assert values.trace_g == pytest.approx(1.0)
    assert values.p - values.trace_g == pytest.approx(0.0)  # tr Theta = 0

    phi = statistics(TOY4A_ZERO_GENERATION, {"s0": 1.0})
    assert phi["chat0"] == pytest.approx(0.25)
    assert phi["chat1"] == pytest.approx(0.75)
    assert sum(phi.values()) == pytest.approx(1.0)
    # Chat_key empty, so G == 0 (Lemma lem:branch-maps (iv)) and the fail branch carries
    # the whole weight.
    for chat, value in branch_values(TOY4A_ZERO_GENERATION, 1.5, {"s0": 1.0}).items():
        assert value.trace_g == pytest.approx(0.0)
        assert value.p - value.trace_g == pytest.approx(phi[chat])

    unreachable = statistics(TOY4C_INFEASIBLE, {"s0": 1.0})
    assert unreachable["chat0"] == pytest.approx(0.0)
    assert sum(unreachable.values()) == pytest.approx(1.0)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
@pytest.mark.parametrize("m", (2, 3, 4, 5))
def test_branch_entropy_matches_an_independent_renyi_entropy(
    alpha: float, m: int
) -> None:
    """O-BRANCH-ENTROPY: (1/(1-alpha)) log2(K/P) equals H_alpha(Unif(m)) = log2 m."""
    assert oracle("O-BRANCH-ENTROPY").claims == ("C4", "C5")
    toy = fully_dephased(m)
    values = branch_values(toy, alpha, {"s0": 1.0})["chat0"]

    contract_side = branch_entropy(values.k, values.p, alpha)
    independent_side = math.log2(m)  # Renyi entropy of the uniform key
    assert contract_side == pytest.approx(independent_side, abs=1e-9)

    # TOY-1 at w0 = 1: a pure state spread over two key values -> exactly 1 bit.
    one_bit = branch_values(TOY1_RETENTION, alpha, _pair(1.0))["chat0"]
    assert branch_entropy(one_bit.k, one_bit.p, alpha) == pytest.approx(1.0)


@pytest.mark.contract
def test_kernel_convention_is_realised_in_the_matrix_power() -> None:
    """Contract Section 4.1: ``0^p = 0`` on the kernel, which ``t^{1/alpha}`` needs.

    Without an explicit support cutoff a numerically-zero eigenvalue of order
    1e-17 becomes 1e-9 after ``t -> t^{1/alpha}`` and pollutes T at the ninth
    digit. This is the check that the convention is actually applied.
    """
    rank_one = np.outer([1.0, 1.0, 1.0], [1.0, 1.0, 1.0]) / 3.0
    powered = psd_power(rank_one, 1.0 / 1.9)
    eigenvalues = np.linalg.eigvalsh(powered)
    assert float(np.sum(np.abs(eigenvalues[:-1]))) < 1e-14
    assert trace_power_pinched(rank_one, 1.9, (0, 1, 2)) == pytest.approx(
        3.0 ** (1.0 - 1.9), abs=1e-12
    )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHAS)
def test_deficit_is_zero_exactly_on_z_invariant_operators(alpha: float) -> None:
    """Corollary cor:f-nonpos equality case, checked in both directions."""
    invariant = np.diag([0.3, 0.7])
    assert sector_deficit(invariant, alpha, (0, 1)) == pytest.approx(0.0, abs=1e-12)

    coherent = np.array([[0.5, 0.5], [0.5, 0.5]])
    assert sector_deficit(coherent, alpha, (0, 1)) < -1e-9
