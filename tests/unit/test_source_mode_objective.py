"""Maximal support on the admissible subspace, and the untrusted gradient form.

Two things contract 0.3.0 changed inside the objective layer are checked here,
on hand-authored declarations small enough to reason about:

* **The maximal-support condition is read on ``S_A``, not on ``A (x) Q_s``.**
  Eq. ``eq:Wcs`` builds the maximal branch support ``W_{chat,s}`` from the
  admissible Alice subspace ``S_A`` of Eq. ``eq:SA``, and Eq. ``eq:Wcs-bound``
  records when it is attained: "whenever the Choi block satisfies ``J_s > 0``
  (trusted-source mode), respectively whenever ``omega_s > 0`` on
  ``H(A Q_s)`` (untrusted-source mode); these are the same condition". For a
  SINGULAR ``tau_A`` no feasible ``omega_s`` is ever positive definite on the
  ambient block, so a check written there would refuse every feasible point --
  which is what the 0.2.4-era code did, and what contract Section 2.5 now
  forbids.
* **In untrusted-source mode the STATE form is primary.** Corollary
  ``cor:full-gradient``: the variables are the sector blocks themselves,
  ``chi = id``, and Eq. ``eq:grad-pieces-un`` is Eq. ``eq:grad-pieces`` with
  the ``W_tau`` conjugation deleted. So the Choi-form and state-form gradients
  must be the SAME OBJECT there, not merely equal in value.

The gradient is never re-implemented: it is compared against central
differences of the objective it differentiates, as elsewhere in this suite.
"""

from __future__ import annotations

import numpy as np
import pytest
from mode_bundles import build_bundle
from toy_declarations import ALL_TOYS_0_4_0, toy

from certiqs_key.domain.manifest import KeyHolder
from certiqs_key.meat_core.declaration.admission import AdmissionError
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    KeyLengthParameters,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.declaration.validation import validate_declaration
from certiqs_key.meat_core.errors import DeclarationError, SupportError
from certiqs_key.meat_core.objective.branch import (
    BranchMap,
    ClassBranch,
    aggregate_branch_operator,
    generate_maps,
)
from certiqs_key.meat_core.objective.choi import Coupling, choi_parametrization
from certiqs_key.meat_core.objective.gradient import (
    admissible_isometries,
    attains_the_reference_rank,
    choi_gradient,
    is_support_maximal,
    pullback_trace_power_gradient,
    state_gradient,
    z_invariant_face,
)
from certiqs_key.meat_core.objective.linalg import is_positive_definite, support_rank
from certiqs_key.meat_core.objective.objective import acceptance_vector, objective_value
from certiqs_key.meat_core.objective.support import branch_support_dimension

FD = 1e-5


def singular_marginal_declaration() -> ProtocolDeclaration:
    """Return a hand-authored declaration with ``rank tau_A = 1 < 2 = d_A``.

    Small enough to check on paper::

        d_A = 2, tau_A = diag(1, 0)          -- SINGULAR, admissible (2.1)
        one sector s0 of dimension 2
        X = {x0}, M_x0 = 1_A                 -- a valid one-element POVM
        V = {v0, v1}, F_v = 1_{Q_s0} / 2     -- completeness: 1/2 + 1/2 = 1
        trivial announcements, one class, sifting always passes
        r(x0, v) = v, so Z = {0, 1} and the branch is KEY-LIVE
        h = B, since r factors through Bob's own outcome
        AcceptSet = {delta_chat0}

    Every feasible ``omega`` has ``omega_A = tau_A = diag(1, 0)``, hence
    ``omega = |e0><e0| (x) rho`` for a state ``rho`` on ``Q_s0``. No such
    ``omega`` is positive definite on ``A (x) Q_s0``, which is exactly the
    situation the ambient support check got wrong.
    """
    declaration = ProtocolDeclaration(
        alice_dim=2,
        alice_marginal=np.diag([1.0, 0.0]).astype(np.complex128),
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
    validate_declaration(declaration)
    return declaration


def feasible_state(rho: np.ndarray) -> dict[str, np.ndarray]:
    """Return ``|e0><e0| (x) rho``, the feasible point of the fixture above."""
    return {
        "s0": np.asarray(
            np.kron(np.diag([1.0, 0.0]), np.asarray(rho)), dtype=np.complex128
        )
    }


# ---------------------------------------------------------------------------
# Maximal support on the admissible subspace
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_feasible_state_of_a_singular_marginal_is_never_ambient_positive() -> None:
    """Eq. ``eq:SA``: every feasible ``omega`` lives in ``supp tau_A (x) H(Q)``.

    Remark ``rem:modes-da1`` (d) proves it: with
    ``Pi^perp = 1_A - Pi_{supp tau_A}``,
    ``tr[(Pi^perp x 1) omega] = tr[Pi^perp tau_A] = 0`` forces
    ``(Pi^perp x 1) omega = 0`` by positivity. So an ambient positivity check
    would refuse every feasible point of such a declaration.
    """
    declaration = singular_marginal_declaration()
    omega = feasible_state(np.eye(2) / 2.0)
    assert not is_positive_definite(omega["s0"])
    maps = generate_maps(declaration)
    lift = admissible_isometries(maps)["s0"]
    assert lift.shape == (4, 2)
    assert is_support_maximal(omega["s0"], lift) is True


@pytest.mark.contract
def test_the_maximal_support_check_is_basis_independent() -> None:
    """Remark ``rem:basis-invariance`` (a)-(b): congruence by a unitary."""
    declaration = singular_marginal_declaration()
    maps = generate_maps(declaration)
    lift = admissible_isometries(maps)["s0"]
    omega = feasible_state(np.diag([0.7, 0.3]))["s0"]
    rotation = np.kron(np.eye(2, dtype=np.complex128), _hadamard())
    assert is_support_maximal(omega, lift) is True
    assert is_support_maximal(omega, lift @ _hadamard()) is True
    assert is_support_maximal(rotation @ omega @ rotation.conj().T, lift) is True


def _hadamard() -> np.ndarray:
    """Return the 2 x 2 Hadamard, a unitary on the admissible subspace."""
    return np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / np.sqrt(2.0)


@pytest.mark.contract
def test_a_gradient_is_available_at_a_singular_marginal() -> None:
    """C12 on a declaration the 0.2.4-era code refused entirely.

    The gradient is checked against CENTRAL DIFFERENCES along admissible
    directions -- Hermitian directions supported in ``S_A (x) H(Q_s)``, which is
    what Corollary ``cor:full-gradient``'s chain rule is stated for.
    """
    declaration = singular_marginal_declaration()
    maps = generate_maps(declaration)
    q = acceptance_vector(declaration)
    alpha = 1.5
    step = 1e-6
    omega = feasible_state(np.diag([0.6, 0.4]))
    gradient = state_gradient(maps, q, omega, alpha)

    generator = np.random.default_rng(20260829)
    for _ in range(4):
        raw = generator.normal(size=(2, 2))
        inner = 0.5 * (raw + raw.T)
        # supp H <= S_A (x) H(Q_s0), by construction.
        direction = np.asarray(np.kron(np.diag([1.0, 0.0]), inner), dtype=np.complex128)
        plus = {"s0": omega["s0"] + step * direction}
        minus = {"s0": omega["s0"] - step * direction}
        difference = (
            objective_value(maps, q, plus, alpha)
            - objective_value(maps, q, minus, alpha)
        ) / (2.0 * step)
        analytic = float(np.real(np.trace(gradient.blocks["s0"] @ direction)))
        assert difference == pytest.approx(analytic, rel=FD, abs=FD)


@pytest.mark.contract
def test_a_state_singular_on_the_admissible_subspace_is_refused() -> None:
    """Theorem ``thm:gradient`` (ii) still fails closed where it should.

    Widening the check to the admissible subspace did not weaken it: a state
    that is singular THERE has non-maximal branch support, and a direction
    leaving it has an infinite one-sided derivative.

    NEITHER DOES DECIDING ON THE CLAIM'S OWN RULE. Eq. ``eq:hsupp-check`` decides, on
    the AGGREGATE operator over the passing classes; this point fails it at rank 1
    against a reference of 2, so the verdict is unchanged and the refusal names the
    quantities it compared.
    """
    declaration = singular_marginal_declaration()
    maps = generate_maps(declaration)
    q = acceptance_vector(declaration)
    omega = feasible_state(np.diag([1.0, 0.0]))
    lift = admissible_isometries(maps)["s0"]
    assert is_support_maximal(omega["s0"], lift) is False
    # THE REFERENCE IS THE DECLARATION'S AND NOT THE ITERATE'S: dim W_{chat,s}
    # is computed once per pair, from the declaration and W_tau -- ONE NUMBER
    # for the pair, over the passing classes together.
    reference = maps.support_references[("chat0", "s0")]
    branch = maps.branches["chat0"]["s0"]
    assert support_rank(aggregate_branch_operator(branch, omega["s0"])) < reference
    with pytest.raises(SupportError, match="eq:hsupp-check"):
        state_gradient(maps, q, omega, 1.5)


@pytest.mark.contract
def test_h_supp_is_decided_by_the_rank_equality_on_the_aggregate() -> None:
    """``eq:hsupp-check``, both sides computed, with one declared number.

    ``frank-wolfe/rem:fo-one-ruler`` states (H-SUPP) as the RANK EQUALITY
    ``rank X_{chat,s} = dim W_{chat,s}`` and says that both sides are computed:
    the left as the count of eigenvalues of ``X_{chat,s}`` above the
    ``support_cutoff`` row RELATIVE TO THAT BLOCK'S OWN SPECTRAL RADIUS, the
    right as ``rank K_{chat,s}`` of ``eq:Kstack`` at the square root of that
    row (one ruler, no ``branch_support_dim`` row), "computed once per (chat, s) from
    the declaration and W_tau and never from an iterate".

    BOTH SIDES ARE ONE NUMBER FOR THE PAIR. ``lem:fo-face`` defines ``X`` as
    the sum over the passing classes and ``eq:Kstack`` lists their operators
    side by side, so the comparison is made once on the aggregate; comparing
    class by class would ADMIT where the claim refuses, both windows being
    relative.

    NO WIDENING IS EXHIBITED HERE, AND
    THAT IS A FACT ABOUT THE CORPUS RATHER THAN AN OMISSION. Deciding by the
    equality instead of by the sufficient condition ``J_s > 0`` can only differ
    where a state singular on the admissible subspace still attains
    ``dim W_{chat,s}`` -- which needs a class Kraus operator with a KERNEL on
    ``S_adm (x) H(Q_s)``, where ``eq:Kstack-rank``'s inequality is STRICT. NO
    DECLARATION THIS REPOSITORY CARRIES HAS ONE: over every toy that builds a
    declaration, and over this fixture, ``rank K_{chat,s}`` equals the column
    count of the lifted stack exactly, so every class is injective there and
    the two routes agree at every point. That is the structural reason no
    frozen verdict moved, and it is asserted below rather than assumed.
    """
    declaration = singular_marginal_declaration()
    maps = generate_maps(declaration)
    branch = maps.branches["chat0"]["s0"]
    (klass,) = branch.classes
    reference = maps.support_references[("chat0", "s0")]

    # THE REFERENCE IS THE DECLARATION'S: rank K_{chat,s} with K the classes'
    # Kraus operators on the admissible subspace S_A (x) H(Q_s), side by side.
    # tau_A has rank one here, so the admissible subspace is half the ambient
    # block.
    assert reference == 2
    lift = admissible_isometries(maps)["s0"]
    assert branch_support_dimension([klass.kraus @ lift]) == reference
    # AND THE INEQUALITY OF eq:Kstack-rank IS AN EQUALITY ON THIS FIXTURE: the
    # lifted stack has full column rank, which is what leaves the widening
    # unexhibited.
    assert reference == (klass.kraus @ lift).shape[1]

    # A STATE THAT ATTAINS THE MAXIMAL SUPPORT PASSES BOTH ROUTES.
    good = feasible_state(np.diag([0.5, 0.5]))
    assert is_support_maximal(good["s0"], lift) is True
    assert attains_the_reference_rank(
        aggregate_branch_operator(branch, good["s0"]), reference
    )

    # AND A RANK-DEFICIENT ONE FAILS THE EQUALITY, which is the withdrawal
    # gradient_hypothesis_support names.
    bad = feasible_state(np.diag([1.0, 0.0]))
    assert not attains_the_reference_rank(
        aggregate_branch_operator(branch, bad["s0"]), reference
    )
    with pytest.raises(SupportError) as raised:
        state_gradient(maps, acceptance_vector(declaration), bad, 1.5)
    assert raised.value.reason == "gradient_hypothesis_support"

    # THE SUFFICIENT CONDITION IS THE TEST FOR A DIRECT CALLER OF THE
    # PER-CLASS FUNCTION, which cannot form the aggregate and therefore cannot
    # evaluate the claim's rule: it refuses more than the claim does and never
    # less, which is the only direction an API guard may err in.
    with pytest.raises(SupportError):
        pullback_trace_power_gradient(klass, bad["s0"], 1.5, admissible=lift)
    assert pullback_trace_power_gradient(
        klass, bad["s0"], 1.5, admissible=lift, support_established=True
    ).shape == (4, 4)


@pytest.mark.contract
def test_the_kraus_stack_is_side_by_side_and_its_rank_is_the_sum_of_the_ranges() -> (
    None
):
    """``eq:Kstack`` lists the classes SIDE BY SIDE; ``eq:Kstack-rank`` reads its rank.

    ``K_{chat,s}`` maps the DIRECT SUM over ``kappa`` of ``H(A_0 Q_s)`` into
    the one ambient space, so its matrix is the blocks in a ROW and
    ``dim W_{chat,s} = rank K = dim(sum_kappa ran K_kappa V)``. A COLUMN stack
    has the rank of the sum of the blocks' ROW spaces instead -- a different
    number, and one capped by the common column count while ``dim W`` may be as
    large as ``|K_pass(chat)| dim S_adm d_s``.

    THE TWO BLOCKS BELOW HAVE THE SAME ROW SPACE AND ORTHOGONAL RANGES, so the
    two stacks disagree by construction: side by side the rank is 2, the
    dimension of the sum of the ranges, and stacked in a column it is 1. This is
    the guard that keeps the column stack from coming back silently.
    """
    first = np.array([[1.0 + 0j], [0.0 + 0j]])
    second = np.array([[0.0 + 0j], [1.0 + 0j]])
    assert branch_support_dimension([first, second]) == 2
    assert np.linalg.matrix_rank(np.hstack([first, second])) == 2
    assert np.linalg.matrix_rank(np.vstack([first, second])) == 1
    # AND ON ONE BLOCK THE TWO STACKS AGREE, which is why the corpus could not
    # tell them apart while the reference was computed class by class.
    assert branch_support_dimension([first]) == 1


@pytest.mark.contract
def test_the_rank_equality_is_read_against_the_block_the_claim_names() -> None:
    """The left side of ``eq:hsupp-check`` is ``rank X_{chat,s}``, relatively read.

    THE WINDOW IS RELATIVE AND THE SPLIT CHANGES WHAT IT IS RELATIVE TO. A
    class whose branch operator is smaller than the largest by more than
    ``1 / support_cutoff`` contributes nothing to ``rank X_{chat,s}`` while
    attaining its own per-class rank in full, so a per-class comparison admits
    a point the claim's aggregate comparison refuses -- the unsafe side of
    ``rem:fo-danger``. The per-class reading is not the
    stricter one: that is true of the exact
    statement and false of the computed one, and the computed one decides runs.
    """
    small = np.array([[1e-15 + 0j]])
    large = np.array([[1.0 + 0j]])
    assert support_rank(large) == 1
    assert support_rank(small) == 1
    aggregate = np.zeros((2, 2), dtype=np.complex128)
    aggregate[0, 0] = large[0, 0]
    aggregate[1, 1] = small[0, 0]
    # THE CLAIM'S NUMBER, AND IT IS NOT THE SUM OF THE TWO ABOVE.
    assert support_rank(aggregate) == 1
    assert attains_the_reference_rank(aggregate, 2) is False


@pytest.mark.contract
def test_the_z_invariant_face_is_built_over_the_admissible_subspace() -> None:
    """Eq. ``eq:Wcs``: ``W_{chat,s} = K(S_A (x) H(Q_s))``, not ``K(A (x) Q_s)``.

    The face over the admissible subspace is strictly smaller here, and using
    the ambient one would perturb an iterate outside the subspace every feasible
    state lives in.
    """
    declaration = singular_marginal_declaration()
    maps = generate_maps(declaration)
    (klass,) = maps.branches["chat0"]["s0"].classes
    lift = admissible_isometries(maps)["s0"]
    admissible = z_invariant_face(klass, lift)
    ambient = z_invariant_face(klass, None)
    assert np.trace(admissible).real == pytest.approx(4.0)
    assert np.trace(ambient).real == pytest.approx(8.0)
    # And the smaller face sits inside the larger one.
    assert np.allclose(ambient @ admissible, admissible, atol=1e-12)


# ---------------------------------------------------------------------------
# The untrusted-source-mode gradient form
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize("toy_id", ["TOY-10", "TOY-8-UN"])
def test_the_choi_and_state_gradients_coincide_in_untrusted_source_mode(
    toy_id: str,
) -> None:
    """Eq. ``eq:grad-pieces-un``: the pieces lose their ``W_tau`` conjugation.

    ``chi`` is the identity there (Definition ``def:untrusted-choi`` (a)), so the
    Choi-form gradient is not merely equal in value to the state-form one -- it
    is the same matrix, entry for entry.
    """
    declaration = declaration_from_bundle(build_bundle(toy(toy_id)))
    maps = generate_maps(declaration)
    parametrization = choi_parametrization(declaration)
    assert parametrization.coupling is Coupling.UNIT_TRACE
    assert parametrization.is_identity is True
    assert parametrization.iota is None

    q = acceptance_vector(declaration)
    blocks = {
        sector: np.asarray(
            np.eye(declaration.block_dim(sector), dtype=np.complex128)
            / (len(declaration.sector_index_set) * declaration.block_dim(sector)),
            dtype=np.complex128,
        )
        for sector in declaration.sector_index_set
    }
    state = state_gradient(maps, q, blocks, 1.5)
    choi = choi_gradient(maps, parametrization, q, blocks, 1.5)
    for sector in declaration.sector_index_set:
        assert np.allclose(choi.blocks[sector], state.blocks[sector], atol=1e-14)


@pytest.mark.contract
def test_the_untrusted_gradient_agrees_with_central_differences() -> None:
    """C12 in untrusted-source mode, against the objective it differentiates."""
    declaration = declaration_from_bundle(build_bundle(toy("TOY-10")))
    maps = generate_maps(declaration)
    q = acceptance_vector(declaration)
    alpha = 1.5
    step = 1e-6
    omega = {
        "s0": np.array([[0.6]], dtype=np.complex128),
        "s1": np.array([[0.4]], dtype=np.complex128),
    }
    gradient = state_gradient(maps, q, omega, alpha)
    for sector in maps.sectors:
        direction = np.array([[1.0]], dtype=np.complex128)
        plus = {**omega, sector: omega[sector] + step * direction}
        minus = {**omega, sector: omega[sector] - step * direction}
        difference = (
            objective_value(maps, q, plus, alpha)
            - objective_value(maps, q, minus, alpha)
        ) / (2.0 * step)
        analytic = float(np.real(np.trace(gradient.blocks[sector] @ direction)))
        assert difference == pytest.approx(analytic, rel=FD, abs=FD)


@pytest.mark.contract
def test_the_admissible_isometry_is_the_identity_in_untrusted_source_mode() -> None:
    """Eq. ``eq:SA``: ``S_A = H(A)`` when no marginal is declared."""
    declaration = declaration_from_bundle(build_bundle(toy("TOY-8-UN")))
    maps = generate_maps(declaration)
    lift = admissible_isometries(maps)["s0"]
    assert np.allclose(lift, np.eye(declaration.block_dim("s0")))
    assert declaration.admissible_alice_isometry().shape == (2, 2)


# ---------------------------------------------------------------------------
# Sector deletion carries every declared input
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_sector_deletion_carries_the_licence_and_the_party_partition() -> None:
    """A structure-changing operation may not drop a declared input.

    Dropping the A-SRC attestation would close a gate the supplier had opened;
    dropping the party partition would RE-OPEN one, since under the default
    partition an inadmissible key holder can satisfy def:admissible-declaration (viii)
    vacuously.
    """
    from certiqs_key.meat_core.declaration.sectors import (
        delete_sectors,
        find_removal_witness,
    )

    declaration = declaration_from_bundle(build_bundle(toy("TOY-9")))
    assert declaration.source_replacement_license is not None

    # TOY-6 is the registry's removable instance; its partition is the default.
    six = declaration_from_bundle(build_bundle(toy("TOY-6")))
    maps = generate_maps(six)
    witness, _ = find_removal_witness(maps, "s2")
    assert witness is not None
    reduced = delete_sectors(maps, [witness])
    assert reduced.party_partition is None
    assert reduced.source_replacement_license == six.source_replacement_license
    assert set(reduced.sector_index_set) == {"s0", "s1"}

# ---------------------------------------------------------------------------
# (H-SUPP): the two sides are about the same subspace only because the classes
# occupy orthogonal output blocks
# ---------------------------------------------------------------------------


def _synthetic_branch(kraus_by_class: dict[str, np.ndarray]) -> BranchMap:
    """Return a two-class ``BranchMap`` from bare Kraus operators.

    Hand-built rather than compiled, because NO DECLARATION IN THIS TREE HAS A
    BRANCH WITH TWO PASSING CLASSES -- see
    :func:`test_no_declaration_in_this_tree_exercises_a_two_class_branch`. Only
    ``kraus`` is read by the two functions under test; the announcement, the
    pairs and the labels are carried so the dataclass is a real one.
    """
    return BranchMap(
        chat="chat",
        sector="s0",
        classes=tuple(
            ClassBranch(
                announcement=(name, "s0"),
                pairs=(("x0", name),),
                kraus=np.asarray(kraus, dtype=np.complex128),
                labels=np.zeros(np.shape(kraus)[0], dtype=np.int64),
            )
            for name, kraus in kraus_by_class.items()
        ),
    )


#: ``K_A``: the input block of dimension two into ambient coordinates 0 and 1.
_ON_FIRST_BLOCK = np.array(
    [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0], [0.0, 0.0]], dtype=np.complex128
)
#: ``K_B``: the same input block into ambient coordinates 2 and 3 -- a range
#: ORTHOGONAL to ``K_A``'s, which is the configuration ``rem:inert`` grounds.
_ON_SECOND_BLOCK = np.array(
    [[0.0, 0.0], [0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.complex128
)


@pytest.mark.contract
def test_the_aggregate_is_the_ambient_sum_only_for_orthogonal_classes() -> None:
    """THE PROPERTY THAT MAKES Eq. ``eq:hsupp-check``'s TWO SIDES COMPARABLE.

    ``lem:fo-face`` defines ``X_{chat,s} := G^J_{chat,s}(J_s)`` as the SUM over
    the passing classes IN ONE AMBIENT SPACE.
    :func:`aggregate_branch_operator` forms the DIRECT SUM of the per-class
    operators instead, and the two are the same operator up to a relabelling of
    basis vectors ONLY BECAUSE THE CLASSES OCCUPY ORTHOGONAL OUTPUT BLOCKS,
    which ``rem:inert`` grounds. That property was documented at the two sites
    and asserted by no test.

    BOTH DIRECTIONS ARE ASSERTED, and the second is the one that matters.
    Where the orthogonality holds, the two ranks agree. Where it FAILS, the
    direct sum counts a subspace twice and reports a rank the ambient sum does
    not have -- so a rank-deficient pair could meet ``dim W`` spuriously and
    pass (H-SUPP), which is the unsafe direction ``rem:fo-danger`` names. A
    test that asserted only the agreeing case would pass against an
    implementation that had lost the property entirely.
    """
    omega = np.eye(2, dtype=np.complex128) / 2.0

    def ambient_sum(branch: BranchMap) -> np.ndarray:
        """``sum_kappa K_kappa omega K_kappa^dagger``, as lem:fo-face writes it."""
        return sum(
            (klass.kraus @ omega @ klass.kraus.conj().T for klass in branch.classes),
            start=np.zeros((4, 4), dtype=np.complex128),
        )

    orthogonal = _synthetic_branch(
        {"a": _ON_FIRST_BLOCK, "b": _ON_SECOND_BLOCK}
    )
    overlapping = _synthetic_branch(
        {"a": _ON_FIRST_BLOCK, "b": _ON_FIRST_BLOCK}
    )

    def spectrum(operator: np.ndarray) -> list[float]:
        """Return the nonzero eigenvalues, sorted: what the two forms share."""
        values = np.linalg.eigvalsh(operator)
        return sorted(round(float(value), 12) for value in values if value > 1e-12)

    # ORTHOGONAL CLASSES: the direct sum IS lem:fo-face's ambient sum, up to a
    # relabelling of basis vectors -- same nonzero spectrum, same rank. This is
    # the equality Eq. eq:hsupp-check's left side silently relies on.
    assert spectrum(aggregate_branch_operator(orthogonal, omega)) == spectrum(
        ambient_sum(orthogonal)
    )
    assert support_rank(aggregate_branch_operator(orthogonal, omega)) == support_rank(
        ambient_sum(orthogonal)
    )

    # CLASSES SHARING AN OUTPUT BLOCK: the equality FAILS, and it fails in the
    # unsafe direction. The direct sum is formed identically -- it cannot see
    # the overlap -- and reports rank four, while the operator lem:fo-face
    # actually names has rank two. A deficient pair could meet dim W on that
    # overcount, which is what rem:fo-danger puts on the unsafe side.
    assert spectrum(aggregate_branch_operator(overlapping, omega)) != spectrum(
        ambient_sum(overlapping)
    )
    assert support_rank(aggregate_branch_operator(overlapping, omega)) == 4
    assert support_rank(ambient_sum(overlapping)) == 2


@pytest.mark.contract
def test_the_kstack_reference_is_the_span_not_the_sum_of_class_dimensions() -> None:
    """The right side of Eq. ``eq:hsupp-check``, on the same two branches.

    ``eq:Kstack`` lists the operators SIDE BY SIDE, so its rank is the
    dimension of the SPAN of their ranges. With orthogonal classes that span is
    the sum of the per-class dimensions; with classes sharing an output block
    it is strictly smaller, and it is the aggregate side that would have moved
    away from it.
    """
    orthogonal = _synthetic_branch(
        {"a": _ON_FIRST_BLOCK, "b": _ON_SECOND_BLOCK}
    )
    overlapping = _synthetic_branch(
        {"a": _ON_FIRST_BLOCK, "b": _ON_FIRST_BLOCK}
    )
    per_class = [2, 2]

    assert branch_support_dimension(
        [klass.kraus for klass in orthogonal.classes]
    ) == sum(per_class)
    assert branch_support_dimension(
        [klass.kraus for klass in overlapping.classes]
    ) < sum(per_class)


@pytest.mark.contract
def test_no_declaration_in_this_tree_exercises_a_two_class_branch() -> None:
    """WHY THE TWO TESTS ABOVE ARE SYNTHETIC, asserted rather than asserted-in-prose.

    Every non-empty ``(chat, s)`` branch reachable from a declaration in this
    repository has EXACTLY ONE passing class, so the aggregate is that one
    class' operator and the stack is one block: neither construction is
    exercised with more than one class by any run. This
    asserts it rather than repeating it, so that the day a declaration with two
    passing classes arrives -- the run tier's optical prologue is where one may
    first appear -- this test fails and says the synthetic cover is no longer
    the only cover.

    IT IS NOT A CLAIM THAT TWO CLASSES CANNOT OCCUR. ``rem:inert`` describes
    when they do; nothing here forbids it.
    """
    counts: set[int] = set()
    surveyed = 0
    for candidate in ALL_TOYS_0_4_0:
        try:
            declaration = declaration_from_bundle(build_bundle(candidate))
            branches = generate_maps(declaration).branches
        except (AdmissionError, DeclarationError, ValueError):
            # Several toys exist to be REFUSED. They have no branches to count
            # and their refusal is asserted elsewhere in this suite.
            continue
        surveyed += 1
        for by_sector in branches.values():
            for branch in by_sector.values():
                if branch.classes:
                    counts.add(len(branch.classes))
    # Guard the guard: a change that made every toy unbuildable would leave
    # `counts` empty and this test vacuously green.
    assert surveyed >= 10, surveyed
    assert counts == {1}, counts
