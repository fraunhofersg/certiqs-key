"""C1 and C2: what a declaration generates, checked against the definitions.

Theorem ``thm:protocol-channel`` and Lemma ``lem:branch-maps``. The objects are
built from the
declaration by ``certiqs_key.meat_core.objective.branch``; the toys carry the same
objects written out BY HAND in ``tests/oracles/toy_declarations.py``, so the
Kraus operators can be compared against literal matrices rather than against a
second generation of the same recipe.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ORACLE_TREE = Path(__file__).resolve().parents[1] / "oracles"
if str(ORACLE_TREE) not in sys.path:
    sys.path.insert(0, str(ORACLE_TREE))
SUPPORT_TREE = Path(__file__).resolve().parents[1] / "support"
if str(SUPPORT_TREE) not in sys.path:
    sys.path.insert(0, str(SUPPORT_TREE))

from dummy_bundles import build_bundle  # noqa: E402
from toy_admission import admitted  # noqa: E402
from toy_declarations import ALL_TOYS, toy  # noqa: E402

from certiqs_key.meat_core.declaration.bundle import (  # noqa: E402
    declaration_from_bundle,
)
from certiqs_key.meat_core.declaration.declaration import (  # noqa: E402
    ProtocolDeclaration,
)
from certiqs_key.meat_core.objective.branch import (  # noqa: E402
    effective_outcomes,
    evaluate_branches,
    generate_maps,
    is_key_inert,
    key_live_values,
    sifting_map,
    statistics,
)

ALPHAS = (1.05, 1.5, 1.9)


def declaration_of(toy_id: str) -> ProtocolDeclaration:
    """Return the validated declaration of a frozen toy."""
    return declaration_from_bundle(build_bundle(toy(toy_id)))


@pytest.mark.contract
def test_the_generated_kraus_operators_are_the_hand_written_ones() -> None:
    """Eq. eq:kraus, against the literal matrices the toys carry."""
    for declared in admitted(ALL_TOYS):
        maps = generate_maps(declaration_of(declared.toy_id))
        for chat, branches in declared.branches.items():
            for hand in branches:
                generated = maps.branches[chat][hand.sector]
                assert len(generated.classes) == len(hand.kraus)
                for klass, expected in zip(generated.classes, hand.kraus, strict=True):
                    assert klass.kraus.shape == expected.shape
                    assert np.allclose(klass.kraus, expected, atol=1e-12)
                    assert tuple(klass.labels) == hand.row_key_values


@pytest.mark.contract
def test_the_sifting_map_is_announcement_determined() -> None:
    """def:admissible-declaration (v): pass or fail is a function of the class."""
    declaration = declaration_of("TOY-1")
    assert sifting_map(declaration) == {("cA0", "cB0"): True}
    assert key_live_values(declaration) == ("chat0",)

    zero = declaration_of("TOY-4a")
    assert sifting_map(zero) == {("cA0", "cB0"): False, ("cA0", "cB1"): False}
    assert key_live_values(zero) == ()


@pytest.mark.contract
def test_a_branch_with_no_pass_class_is_zero() -> None:
    """Lemma lem:branch-maps (iv): ``chat`` outside ``Chat_key`` has ``G_chat = 0``."""
    maps = generate_maps(declaration_of("TOY-4a"))
    for chat in ("chat0", "chat1"):
        for sector in maps.sectors:
            assert maps.branches[chat][sector].is_zero


@pytest.mark.contract
@pytest.mark.parametrize("alpha", ALPHAS)
def test_the_trace_identity_of_lemma_c2(alpha: float) -> None:
    """Eq. eq:traces: ``tr G + tr Theta = Phi(chat)``, and ``Phi`` normalizes.

    ``tr Theta`` is not stored anywhere; it is ``P - tr G``, so the identity is
    checked by computing ``tr G`` two independent ways -- from the branch
    operators, and from the pass-only statistics operator.
    """
    for toy_id in ("TOY-1", "TOY-2", "TOY-4a", "TOY-5", "TOY-6"):
        declaration = declaration_of(toy_id)
        maps = generate_maps(declaration)
        sectors = declaration.sector_index_set
        omega = {
            s: np.array([[1.0 / len(sectors)]], dtype=np.complex128) for s in sectors
        }
        phi = statistics(maps, omega)
        assert sum(phi.values()) == pytest.approx(1.0, abs=1e-12)
        values = evaluate_branches(maps, omega, alpha)
        for chat in declaration.acceptance_values:
            direct = sum(
                float(
                    np.real(np.trace(maps.pass_operator[chat][sector] @ omega[sector]))
                )
                for sector in sectors
            )
            assert values[chat].trace_g == pytest.approx(direct, abs=1e-12)
            assert values[chat].p - values[chat].trace_g >= -1e-12


@pytest.mark.contract
def test_the_effective_outcome_set_and_the_key_inert_predicate() -> None:
    """Definition def:keyinert, decided on the declaration alone."""
    declaration = declaration_of("TOY-1")
    kappa = ("cA0", "cB0")
    assert effective_outcomes(declaration, kappa, "s0") == (
        ("x0", "v0"),
        ("x0", "v1"),
    )
    # On s1 the outcome v1 has F = 0, so the effective set is a singleton and r
    # is constant on it.
    assert effective_outcomes(declaration, kappa, "s1") == (("x0", "v0"),)
    assert not is_key_inert(declaration, "chat0", "s0")
    assert is_key_inert(declaration, "chat0", "s1")


@pytest.mark.contract
def test_key_inertness_is_decided_exactly_not_by_a_tolerance() -> None:
    """The predicate is a property of the DECLARATION, so dust counts as nonzero.

    Treating a numerically tiny POVM block as nonzero enlarges the effective
    outcome set, which can only make ``r`` harder to be constant -- i.e. can
    only classify the sector as key-active. That is the conservative direction.
    """
    from dataclasses import replace

    declaration = declaration_of("TOY-1")
    perturbed = replace(
        declaration,
        bob_povm={
            "v0": {
                "s0": np.array([[0.5]], dtype=np.complex128),
                "s1": np.array([[1.0 - 1e-18]], dtype=np.complex128),
            },
            "v1": {
                "s0": np.array([[0.5]], dtype=np.complex128),
                "s1": np.array([[1e-18]], dtype=np.complex128),
            },
        },
    )
    assert effective_outcomes(perturbed, ("cA0", "cB0"), "s1") == (
        ("x0", "v0"),
        ("x0", "v1"),
    )
    assert not is_key_inert(perturbed, "chat0", "s1")


@pytest.mark.contract
@pytest.mark.parametrize("alpha", ALPHAS)
def test_an_acceptance_value_with_no_branch_gives_the_same_objective_either_way(
    alpha: float,
) -> None:
    """Why an unrealized announcement class cannot matter.

    ``varsigma`` is not determined by the declaration on a class no outcome pair
    realises. It cannot matter: a branch with no Kraus term has ``G = 0``, hence
    ``K = P``, and the key-live term ``d(q,P) + d(q,K)/(alpha-1)`` then equals
    the non-key-live term ``(alpha/(alpha-1)) d(q,P)`` exactly. Checked here on
    numbers rather than argued.
    """
    from certiqs_key.meat_core.objective.objective import objective_from_branches

    declaration = declaration_of("TOY-4a")
    maps = generate_maps(declaration)
    omega = {"s0": np.array([[1.0]], dtype=np.complex128)}
    q = {"chat0": 0.3, "chat1": 0.7}
    values = evaluate_branches(maps, omega, alpha)
    for chat in ("chat0", "chat1"):
        assert values[chat].k == pytest.approx(values[chat].p, abs=1e-12)
    treated_as_dead = objective_from_branches(
        alpha=alpha, q=q, values=values, chat_key=()
    )
    treated_as_live = objective_from_branches(
        alpha=alpha, q=q, values=values, chat_key=("chat0", "chat1")
    )
    assert treated_as_dead == pytest.approx(treated_as_live, abs=1e-12)


@pytest.mark.contract
def test_the_state_embedding_interleaves_rather_than_slices() -> None:
    """The A-first ordering of Section 2.5, written out.

    In ``A x Q`` the index of ``(a, q)`` is ``a d_Q + q``, so a sector block is
    an interleaved selection and not a contiguous slice as soon as ``d_A > 1``.
    Getting this wrong would silently scramble a multi-dimensional Alice.
    """
    from dataclasses import replace

    from certiqs_key.meat_core.objective.branch import embed_state, sector_indices

    declaration = replace(
        declaration_of("TOY-1"),
        alice_dim=2,
        alice_marginal=np.eye(2, dtype=np.complex128) / 2.0,
        alice_povm={"x0": np.eye(2, dtype=np.complex128)},
    )
    assert list(sector_indices(declaration, "s0")) == [0, 2]
    assert list(sector_indices(declaration, "s1")) == [1, 3]
    blocks = {
        "s0": np.diag([0.3, 0.2]).astype(np.complex128),
        "s1": np.diag([0.2, 0.3]).astype(np.complex128),
    }
    dense = embed_state(declaration, blocks)
    assert dense.shape == (4, 4)
    assert np.allclose(np.diag(dense).real, [0.3, 0.2, 0.2, 0.3])
    assert np.trace(dense).real == pytest.approx(1.0)


@pytest.mark.contract
def test_a_feasible_state_passes_the_feasible_set_check() -> None:
    """Eq. eq:feas, including the declared constraint list."""
    from certiqs_key.meat_core.errors import DeclarationError
    from certiqs_key.meat_core.objective.objective import check_feasible

    declaration = declaration_of("TOY-5")
    check_feasible(
        declaration,
        {
            "s0": np.array([[0.5]], dtype=np.complex128),
            "s1": np.array([[0.5]], dtype=np.complex128),
        },
    )
    # The constraint w0 >= 1/2 is part of the feasible set, and a violation is a
    # hard error rather than a penalty.
    with pytest.raises(DeclarationError, match="constraint 0"):
        check_feasible(
            declaration,
            {
                "s0": np.array([[0.25]], dtype=np.complex128),
                "s1": np.array([[0.75]], dtype=np.complex128),
            },
        )
    # tr omega = 1 is checked EXPLICITLY and unconditionally: Eq. eq:feas
    # writes it out rather than deriving it, because in untrusted-source mode
    # it is the only unconditional constraint the feasible set carries.
    with pytest.raises(DeclarationError, match="tr omega"):
        check_feasible(
            declaration,
            {
                "s0": np.array([[0.5]], dtype=np.complex128),
                "s1": np.array([[0.9]], dtype=np.complex128),
            },
        )
    # And so is the trusted marginal, on a NORMALIZED state so that the trace
    # condition cannot stand in for it. TOY-5 has d_A = 1, so a normalized
    # block-diagonal state always has omega_A = tau_A = [1]; the marginal row of
    # Eq. eq:feas-modes is exercised on a d_A = 2 declaration instead.
    two_dimensional = declaration_of("TOY-7")
    check_feasible(
        two_dimensional,
        {"s0": np.diag([0.5, 0.5]).astype(np.complex128)},
    )
    with pytest.raises(DeclarationError, match="trusted marginal"):
        check_feasible(
            two_dimensional,
            {"s0": np.diag([0.75, 0.25]).astype(np.complex128)},
        )
