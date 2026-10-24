"""The 0.3.0 material, from the solver, against the FROZEN Group-6 oracles.

Every expected value here is ``tests/oracles/registry.py``'s, unmodified. The
ten entries of its Group 6 cover what contract 0.3.0 added and the two
implementation-found gaps it closed:

===============================  =========================================
``O-SOURCE-MODE-DERIVED``        the mode is read off the marginal slot
``O-MARGINAL-INADMISSIBLE``      ``tau_A = 0`` is rejected; ``none`` is not 0
``O-MODE-EQUIVALENCE-DA1``       at ``d_A = 1`` the modes are one declaration
``O-UNTRUSTED-CONSERVATIVE``     dropping the marginal never raises ``h_low``
``O-UNTRUSTED-SCALAR-CLASS``     the untrusted licensed class is scalar
``O-CGATE-DEGENERATE``           part (i) degenerates in two cases
``O-SOURCE-LICENSE-GATE``        A-SRC gated fail-closed, vacuous at d_A = 1
``O-PARTY-COMPUTABILITY``        the key holder computes from its own readout
``O-CHOI-BASIS-INVARIANCE``      F-01-01: a singular ``tau_A`` is admissible
``O-GRADIENT-FACE-SPLIT``        F-01-02: the split face rule
===============================  =========================================

TOLERANCE, RECORDED
-------------------
``SOLVER = 1e-8`` absolute for anything a Frank-Wolfe run produced, the same
bar and the same two reasons as ``test_hlow_against_registry.py``: the step cap
at ``1 - 1e-10`` and the oracle's own ``1e-10``. The largest deviation observed
across this file's toys and alpha grid is ``9e-11`` (TOY-9 at ``alpha = 1.05``),
two orders inside the bar. ``EXACT = 1e-13`` is used where two call paths handle
the same numbers and only representation noise separates them.

The bundles for the seven 0.3.0 toys come from ``tests/support/mode_bundles``,
not from the frozen ``dummy_bundles``: that builder was frozen before the
manifest could express an absent marginal, and it refuses these declarations by
name rather than coercing them. Nothing under ``tests/oracles/`` is modified,
imported-and-monkeypatched, or shadowed.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest
from dummy_bundles import build_bundle as build_trusted_bundle
from licensed_form import as_declared_form
from mode_bundles import build_bundle
from registry import (
    ALPHA_GRID,
    O_GRADIENT_FACE_COMPRESSED_VALUES,
    O_UNTRUSTED_CONSERVATIVE_UNTRUSTED_VALUE,
    oracle,
)
from tiers import BRACKET_TIER
from toy_declarations import (
    MODE_TWIN_PAIRS,
    SOURCE_MODE_TOYS,
    TOY9_IOTA_1,
    TOY9_IOTA_2,
    TOY9_J_1,
    TOY9_J_2,
    TOY9_OMEGA,
    ToyDeclaration,
    source_mode,
    toy,
)

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import (
    ProtocolDeclaration,
    RhsTag,
    SourceMode,
)
from certiqs_key.meat_core.declaration.validation import validate_declaration
from certiqs_key.meat_core.errors import DeclarationError, SecurityGateError
from certiqs_key.meat_core.finitekey.keylength import (
    check_key_length_permitted,
    check_source_license,
    key_length_permitted,
    licensed_class_check,
    source_license_required,
)
from certiqs_key.meat_core.objective.branch import (
    branch_operator,
    generate_maps,
    trace_power_pinched,
)
from certiqs_key.meat_core.objective.choi import (
    ChoiIsometryError,
    Coupling,
    choi_parametrization,
)
from certiqs_key.meat_core.objective.linalg import pinch, psd_power, psd_trace_power
from certiqs_key.solvers.oracles.protocol import SectorChoiProblem

SOLVER = 1e-8
EXACT = 1e-13


def declaration_of(toy_id: str):
    """Return the validated declaration of a toy, via its serialized bundle."""
    candidate = toy(toy_id)
    builder = (
        build_bundle
        if candidate in SOURCE_MODE_TOYS
        else build_trusted_bundle  # the frozen builder still owns the 0.2.x toys
    )
    return declaration_from_bundle(builder(candidate))


def joint_problem(declaration: ProtocolDeclaration) -> SectorChoiProblem:
    """Return the zero-cost subproblem the one driver asks the oracle.

    The accepted-format declaration runs as its degenerate general embedding
    (one Alice sector ``t0``), so the program is the per-Alice-sector one in
    trusted-source mode and the single joint one in untrusted-source mode --
    where the Alice system sits INSIDE the joint block, so the input register
    is one-dimensional.
    """
    from certiqs_key.meat_core.declaration.general import general_from_accepted
    from certiqs_key.meat_core.objective.joint import joint_choi_parametrization
    from certiqs_key.solvers.oracles.joint_rows import (
        joint_program_for_alice_sector,
        joint_program_untrusted,
    )

    general = general_from_accepted(declaration)
    parametrization = joint_choi_parametrization(general)
    zero = {
        pair: np.zeros((parametrization.block_dim(pair),) * 2, dtype=np.complex128)
        for pair in parametrization.joint_sectors
    }
    if general.is_trusted_source:
        return joint_program_for_alice_sector(parametrization, "t0", zero)
    return joint_program_untrusted(parametrization, zero)


def solve_toy(toy_id: str, alpha: float):
    """Return the result record of a toy at one Renyi order.

    The toy stands for compiled output, so the run carries the provenance
    token (``req:compiled-declaration-only``); the gates this file tests are
    decided before it and keep their own reasons.
    """
    from tests.support.provenance import COMPILED

    from certiqs_key.solvers.frank_wolfe import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    return solve(
        declaration_of(toy_id), QicsSectorChoiOracle(), alpha=alpha, compiled=COMPILED
    )


# ---------------------------------------------------------------------------
# O-SOURCE-MODE-DERIVED
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_o_source_mode_derived_frozen_verdicts() -> None:
    """O-SOURCE-MODE-DERIVED: the mode is read off ``alice_marginal``, always."""
    entry = oracle("O-SOURCE-MODE-DERIVED")
    assert entry.claims == ("C1",)
    assert entry.value == "derived"

    trusted = (
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
        "TOY-8-T",
        "TOY-9",
    )
    untrusted = ("TOY-1-UN", "TOY-3(m=2)-UN", "TOY-5-UN", "TOY-8-UN", "TOY-10")
    for toy_id in trusted:
        declaration = declaration_of(toy_id)
        assert declaration.source_mode is SourceMode.TRUSTED, toy_id
        assert declaration.is_trusted_source is True, toy_id
        assert source_mode(toy(toy_id)) == "trusted", toy_id
    for toy_id in untrusted:
        declaration = declaration_of(toy_id)
        assert declaration.source_mode is SourceMode.UNTRUSTED, toy_id
        assert declaration.is_trusted_source is False, toy_id
        assert source_mode(toy(toy_id)) == "untrusted", toy_id


@pytest.mark.contract
@pytest.mark.oracle
def test_no_declaration_or_bundle_carries_a_separate_source_mode_field() -> None:
    """Section 2.5: "a second key carrying the mode ... is forbidden"."""
    from dataclasses import fields

    from certiqs_key.domain.manifest import Declaration as ManifestDeclaration
    from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration

    stored = {field.name for field in fields(ProtocolDeclaration)}
    assert "source_mode" not in stored
    assert "source_model" not in stored
    assert isinstance(type(declaration_of("TOY-1")).source_mode, property), (
        "source_mode must be derived, not a settable field"
    )
    assert "source_mode" not in ManifestDeclaration.model_fields
    assert "source_model" not in ManifestDeclaration.model_fields

    # And no bundle declares it under `assumptions` either.
    for toy_id in ("TOY-1", "TOY-8-UN", "TOY-10"):
        candidate = toy(toy_id)
        builder = (
            build_bundle if candidate in SOURCE_MODE_TOYS else build_trusted_bundle
        )
        manifest = builder(candidate).manifest
        assert "source_mode" not in manifest.assumptions
        assert "source_model" not in manifest.assumptions


# ---------------------------------------------------------------------------
# O-MARGINAL-INADMISSIBLE
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_o_marginal_inadmissible_frozen_verdicts() -> None:
    """O-MARGINAL-INADMISSIBLE: four spellings, four frozen verdicts."""
    entry = oracle("O-MARGINAL-INADMISSIBLE")
    assert entry.claims == ("C1", "C8")
    assert entry.value == "reject"

    base = declaration_of("TOY-7")

    # tau_A = 0 -> REJECT, and the message must carry BOTH grounds:
    # def:admissible-declaration (ii) normalization, and the empty feasible set of
    # def:admissible-declaration (vii).
    with pytest.raises(DeclarationError) as raised:
        validate_declaration(
            replace(base, alice_marginal=np.zeros((2, 2), dtype=np.complex128)))
    message = str(raised.value)
    assert "def:admissible-declaration (ii)" in message
    assert "def:admissible-declaration (vii)" in message
    assert "transmitter/rem:source-mode (c)" in message

    # tau_A = none -> ACCEPT, untrusted-source mode.
    untrusted = declaration_of("TOY-8-UN")
    validate_declaration(untrusted)
    assert untrusted.source_mode is SourceMode.UNTRUSTED

    # tau_A = 1_A/d_A -> ACCEPT, and it is a TRUSTED declaration, not a neutral
    # "nothing is known": it fixes the marginal and needs the A-SRC licence.
    maximally_mixed = declaration_of("TOY-7")
    validate_declaration(maximally_mixed)
    assert maximally_mixed.source_mode is SourceMode.TRUSTED
    assert np.allclose(maximally_mixed.trusted_marginal, np.eye(2) / 2.0)
    assert source_license_required(maximally_mixed) is True

    # A singular but nonzero tau_A -> ACCEPT, trusted-source mode.
    singular = declaration_of("TOY-9")
    validate_declaration(singular)
    assert singular.source_mode is SourceMode.TRUSTED
    assert np.linalg.matrix_rank(singular.trusted_marginal) == 2 < singular.alice_dim


# ---------------------------------------------------------------------------
# O-MODE-EQUIVALENCE-DA1
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_o_mode_equivalence_at_alice_dim_one(alpha: float) -> None:
    """O-MODE-EQUIVALENCE-DA1: each untrusted twin reproduces its original."""
    entry = oracle("O-MODE-EQUIVALENCE-DA1")
    assert entry.claims == ("C1", "C8")
    for original, twin in MODE_TWIN_PAIRS:
        assert original.alice_dim == 1 and twin.alice_dim == 1
        first = solve_toy(original.toy_id, alpha)
        second = solve_toy(twin.toy_id, alpha)
        assert second.h_low == pytest.approx(first.h_low, abs=SOLVER), twin.toy_id


@pytest.mark.contract
@pytest.mark.oracle
def test_at_alice_dim_one_the_two_choi_programs_are_the_same_set() -> None:
    """Remark ``rem:modes-da1`` (b4): the coupling constraints coincide.

    ``1_{A_0} = [1]`` at ``d_A = 1``, so ``sum_s tr_{Q_s} J_s = 1_{A_0}`` IS
    ``sum_s tr omega_s = 1``. The two coupling tags stay DISTINCT -- they are
    different conditions in general -- but at ``d_A = 1`` they reduce to the
    same single real equation, which is what makes the twin values identical.
    """
    trusted = declaration_of("TOY-5")
    untrusted = declaration_of("TOY-5-UN")
    p_trusted = choi_parametrization(trusted)
    p_untrusted = choi_parametrization(untrusted)
    assert p_trusted.coupling is Coupling.INPUT_IDENTITY
    assert p_untrusted.coupling is Coupling.UNIT_TRACE
    assert p_trusted.input_dim == p_untrusted.input_dim == 1

    # The subproblems the ONE DRIVER asks.
    problem_t = joint_problem(trusted)
    problem_u = joint_problem(untrusted)
    equations_t = problem_t.coupling_equations()
    equations_u = problem_u.coupling_equations()
    assert len(equations_t) == len(equations_u) == 1
    assert np.allclose(equations_t[0][0], equations_u[0][0], atol=EXACT)
    assert equations_t[0][1] == equations_u[0][1] == 1.0


# ---------------------------------------------------------------------------
# O-UNTRUSTED-CONSERVATIVE
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
@pytest.mark.parametrize(
    ("alpha", "expected"), oracle("O-UNTRUSTED-CONSERVATIVE").frozen_values
)
def test_o_untrusted_conservative_frozen_values(alpha: float, expected: float) -> None:
    """O-UNTRUSTED-CONSERVATIVE: the TOY-8 pair, and the strict gap between them."""
    entry = oracle("O-UNTRUSTED-CONSERVATIVE")
    assert entry.claims == ("C8",)
    assert entry.toy_id == "TOY-8-T"

    trusted = solve_toy("TOY-8-T", alpha)
    untrusted = solve_toy("TOY-8-UN", alpha)
    assert trusted.h_low == pytest.approx(expected, abs=SOLVER)
    assert untrusted.h_low == pytest.approx(
        O_UNTRUSTED_CONSERVATIVE_UNTRUSTED_VALUE, abs=SOLVER
    )
    # Remark transmitter/rem:source-mode (a): dropping the marginal never RAISES h_low,
    # and
    # here it strictly lowers it by the frozen amount.
    assert untrusted.h_low < trusted.h_low
    assert trusted.h_low - untrusted.h_low == pytest.approx(expected, abs=SOLVER)
    assert trusted.assurance is BRACKET_TIER  # certified where installed (P2)


@pytest.mark.contract
@pytest.mark.oracle
def test_every_trusted_feasible_point_is_untrusted_feasible() -> None:
    """The general direction of Remark ``transmitter/rem:source-mode`` (a), on TOY-8.

    The trusted feasible set of TOY-8 is the single point ``tau_A``; it must lie
    in the untrusted one, whose only condition is ``tr omega = 1``.
    """
    from certiqs_key.meat_core.objective.objective import check_feasible

    trusted = declaration_of("TOY-8-T")
    untrusted = declaration_of("TOY-8-UN")
    point = {"s0": np.asarray(trusted.trusted_marginal, dtype=np.complex128)}
    check_feasible(trusted, point)
    check_feasible(untrusted, point)
    # The converse fails: diag(1/2, 1/2) is untrusted-feasible and not trusted.
    other = {"s0": np.diag([0.5, 0.5]).astype(np.complex128)}
    check_feasible(untrusted, other)
    with pytest.raises(DeclarationError, match="trusted marginal"):
        check_feasible(trusted, other)


# ---------------------------------------------------------------------------
# O-UNTRUSTED-SCALAR-CLASS
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_o_untrusted_scalar_class_refuses_the_operator_reading() -> None:
    """O-UNTRUSTED-SCALAR-CLASS: ``Theta_k = c_k 1_A`` is not an equivalent spelling.

    Definition ``def:homog`` (b) types the untrusted right-hand side as a real
    number. Reading the same entry as the operator ``c_k 1_A`` is refused at
    validation, and Remark ``rem:homog`` (a) says why: with the licensed entry
    ``(1_Q, succeq, 1)`` -- whose attack set is EVERY CPTP map, since the
    adjoint of a CPTP map is unital -- the scalar reading is satisfied by every
    state while the operator reading forces ``omega_A >= 1_A``, hence
    ``tr omega >= 2`` at ``d_A = 2``, and empties the feasible set.
    """
    entry = oracle("O-UNTRUSTED-SCALAR-CLASS")
    assert entry.claims == ("C9b", "C17")
    assert entry.toy_id == "TOY-8-UN"

    from certiqs_key.domain.manifest import ConstraintRelation
    from certiqs_key.meat_core.declaration.declaration import ConstraintEntry
    from certiqs_key.meat_core.objective.objective import scalar_constraint_value

    base = declaration_of("TOY-8-UN")
    scalar_entry = ConstraintEntry(
        operator_blocks={"s0": np.eye(1, dtype=np.complex128)},
        relation=ConstraintRelation.SUCCEQ,
        rhs_tag=RhsTag.HOMOGENEOUS,
        bound=1.0,
    )
    licensed = replace(base, constraint_list=(scalar_entry,))
    validate_declaration(licensed)

    # The scalar reading restricts nothing: tr[(1_A x 1_Q) omega] = 1 >= 1.
    point = {"s0": np.diag([0.5, 0.5]).astype(np.complex128)}
    assert scalar_constraint_value(licensed, 0, point) == pytest.approx(1.0, abs=EXACT)

    # The operator reading is refused outright as ill-typed for the mode.
    operator_entry = ConstraintEntry(
        operator_blocks={"s0": np.eye(1, dtype=np.complex128)},
        relation=ConstraintRelation.SUCCEQ,
        rhs_tag=RhsTag.GENERAL,
        bound=np.eye(2, dtype=np.complex128),
    )
    with pytest.raises(DeclarationError) as raised:
        validate_declaration(replace(base, constraint_list=(operator_entry,)))
    assert "rem:homog" in str(raised.value)
    assert "def:homog (b)" in str(raised.value)
    assert "`general` form" in str(raised.value)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
def test_the_licensed_scalar_entry_leaves_toy8_untrusted_unchanged() -> None:
    """Adding ``(1_Q, succeq, 1)`` in untrusted-source mode changes no value."""
    from certiqs_key.domain.manifest import ConstraintRelation
    from certiqs_key.meat_core.declaration.declaration import ConstraintEntry
    from certiqs_key.solvers.frank_wolfe import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    base = declaration_of("TOY-8-UN")
    constrained = replace(
        base,
        constraint_list=(
            ConstraintEntry(
                operator_blocks={"s0": np.eye(1, dtype=np.complex128)},
                relation=ConstraintRelation.SUCCEQ,
                rhs_tag=RhsTag.HOMOGENEOUS,
                bound=1.0,
            ),
        ),
    )
    result = solve(constrained, QicsSectorChoiOracle(), alpha=1.5)
    assert result.h_low == pytest.approx(
        O_UNTRUSTED_CONSERVATIVE_UNTRUSTED_VALUE, abs=SOLVER
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_untrusted_program_is_not_the_trusted_one_with_w_tau_substituted() -> None:
    """Definition ``def:untrusted-choi`` (b): one coupling equation, not ``d_A^2``.

    Substituting ``W_tau = 1_A`` into Eq. ``eq:choi-feas`` would impose the
    OPERATOR condition ``sum_s tr_{Q_s} omega_s = 1_A``, which at ``d_A = 2``
    forces ``tr omega = 2`` and is infeasible. The untrusted coupling is the
    single scalar equation, and the counts are what separate them.
    """
    untrusted = declaration_of("TOY-8-UN")
    parametrization = choi_parametrization(untrusted)
    assert parametrization.coupling is Coupling.UNIT_TRACE
    assert parametrization.input_dim == 2
    # The subproblem the one driver asks: the Alice system sits inside the
    # joint block, so the one scalar equation is on a one-dimensional input.
    problem = joint_problem(untrusted)
    equations = problem.coupling_equations()
    assert len(equations) == 1, "the untrusted coupling is ONE scalar equation"
    assert np.allclose(equations[0][0], np.eye(problem.input_dim), atol=EXACT)
    assert equations[0][1] == 1.0

    # Whereas the trusted twin at the same d_A imposes d_A^2 = 4 of them.
    trusted = declaration_of("TOY-8-T")
    assert len(joint_problem(trusted).coupling_equations()) == 4


# ---------------------------------------------------------------------------
# O-CGATE-DEGENERATE
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_o_cgate_degenerate_frozen_verdicts() -> None:
    """O-CGATE-DEGENERATE as re-frozen: the owner's reading.

    Part (i) is a type check at every d_A. It degenerates in two of the three
    cases -- vacuous in untrusted-source mode, and at d_A = 1 a check that
    rejects only a general tag a producer can avoid -- and a pass there is
    evidence of nothing. TOY-5 and TOY-6 are frozen in both carriages of their
    one entry: the homogeneous form their records declare, and the general
    form the frozen 0.1.0 wire forces.
    """
    entry = oracle("O-CGATE-DEGENERATE")
    assert entry.claims == ("C14", "C17")
    assert entry.toy_id == "TOY-5-UN"
    assert "RE-FROZEN" in entry.revalidation

    # L empty -> key length allowed.
    assert key_length_permitted(declaration_of("TOY-1")) is True

    for toy_id in ("TOY-5", "TOY-6"):
        # d_A = 1, trusted, the HOMOGENEOUS form the record declares: part (i)
        # PASSES and is DEGENERATE, no licence -> hard fail on part (ii).
        declared = as_declared_form(declaration_of(toy_id), toy(toy_id))
        assert declared.alice_dim == 1
        check = licensed_class_check(declared)
        assert check.licensed is True
        assert check.vacuous is True
        assert check.scalars == (0.5,)
        assert "DEGENERATE (Remark rem:cgate)" in check.reason
        assert "prop:trivial-alice-system (iii)" in check.reason
        assert key_length_permitted(declared) is False
        with pytest.raises(SecurityGateError) as raised:
            check_key_length_permitted(declared)
        failing = str(raised.value).split("Failing:")[1]
        assert failing.lstrip().startswith("(ii)")
        assert "attack_set_license" in failing
        assert "DEGENERATE" in failing
        # d_A = 1, trusted, the GENERAL form the frozen wire carries: part (i)
        # FAILS on the tag, no licence -> hard fail on (i) and (ii).
        general = declaration_of(toy_id)
        check = licensed_class_check(general)
        assert check.licensed is False
        assert check.vacuous is False
        assert check.scalars is None
        assert "`general` form" in check.reason
        assert "at any d_A" in check.reason
        assert key_length_permitted(general) is False
        with pytest.raises(SecurityGateError) as raised:
            check_key_length_permitted(general)
        failing = str(raised.value).split("Failing:")[1]
        assert "(i) entries [0] declare the `general` form" in failing
        assert "(ii) the declaration carries no attack_set_license" in failing

    # untrusted, any d_A: part (i) VACUOUS for the other reason.
    declaration = declaration_of("TOY-5-UN")
    check = licensed_class_check(declaration)
    assert check.licensed is True
    assert check.vacuous is True
    assert "untrusted-source mode" in check.reason
    assert "type check" in check.reason
    assert key_length_permitted(declaration) is False
    with pytest.raises(SecurityGateError) as raised:
        check_key_length_permitted(declaration)
    assert "attack_set_license" in str(raised.value)
    assert "VACUOUS" in str(raised.value)

    # trusted, d_A >= 2: a GENUINE restriction, and TOY-7 fails it.
    declaration = declaration_of("TOY-7")
    check = licensed_class_check(declaration)
    assert check.licensed is False
    assert check.vacuous is False
    assert check.scalars is None
    with pytest.raises(SecurityGateError, match="`general` form"):
        check_key_length_permitted(declaration)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
def test_a_vacuous_gate_part_does_not_read_as_a_passed_check() -> None:
    """G3 judgement call (f): the certificate must say so, not just report True.

    "An implementation must not report a passing part (i) as evidence of
    anything in these cases, and must still hard-fail on a missing attestation."
    A boolean cannot carry that, so the certificate carries the vacuity and its
    reason beside it.
    """
    from certiqs_key.solvers.frank_wolfe import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    # TOY-5 in the homogeneous form its record declares (at d_A = 1 the
    # frozen wire's general carriage FAILS part (i), O-CGATE-DEGENERATE), and
    # TOY-5-UN, whose scalar entry crosses the wire as it is declared.
    homogeneous = as_declared_form(declaration_of("TOY-5"), toy("TOY-5"))
    for result in (
        solve(homogeneous, QicsSectorChoiOracle(), alpha=1.5),
        solve_toy("TOY-5-UN", 1.5),
    ):
        gates = result.certificate["security_gates"]
        assert gates["licensed_class_passed"] is True
        assert gates["licensed_class_vacuous"] is True
        assert "rem:cgate" in gates["licensed_class_reason"]
        assert gates["attack_set_license_present"] is False
        assert gates["key_length_permitted"] is False
        assert result.key_length is None
        assert result.as_payload()["optimizer_certificate"]["security_gates"] == dict(
            gates
        )

    genuine = solve_toy("TOY-8-T", 1.5)
    gates = genuine.certificate["security_gates"]
    assert gates["constraint_count"] == 0
    assert gates["source_replacement_license_required"] is True
    assert gates["source_replacement_license_present"] is True
    assert genuine.key_length is not None


# ---------------------------------------------------------------------------
# O-SOURCE-LICENSE-GATE
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_o_source_license_gate_frozen_verdicts() -> None:
    """O-SOURCE-LICENSE-GATE: four frozen cases, including where NOT to demand."""
    entry = oracle("O-SOURCE-LICENSE-GATE")
    assert entry.claims == ("C3", "C14")
    assert entry.toy_id == "TOY-8-T"

    # d_A = 1, tau_A = [1], no licence -> ALLOWED. The licence is vacuous and
    # "must not be demanded" (Remark rem:modes-da1 (b5)).
    for toy_id in ("TOY-1", "TOY-2", "TOY-3(m=2)", "TOY-4a", "TOY-5", "TOY-6"):
        declaration = declaration_of(toy_id)
        assert declaration.is_trusted_source is True
        assert declaration.alice_dim == 1
        assert declaration.source_replacement_license is None
        assert source_license_required(declaration) is False
        check_source_license(declaration)

    # d_A >= 2, tau_A declared, no licence -> HARD FAIL.
    declaration = declaration_of("TOY-7")
    assert source_license_required(declaration) is True
    with pytest.raises(SecurityGateError, match="A-SRC"):
        check_source_license(declaration)
    assert key_length_permitted(declaration) is False

    # d_A >= 2, tau_A declared, licence present -> ALLOWED.
    for toy_id in ("TOY-8-T", "TOY-9"):
        declaration = declaration_of(toy_id)
        assert source_license_required(declaration) is True
        assert declaration.source_replacement_license is not None
        check_source_license(declaration)
        assert key_length_permitted(declaration) is True

    # tau_A = none -> A-SRC NOT ASSERTED; there is no licence to demand.
    for toy_id in ("TOY-1-UN", "TOY-3(m=2)-UN", "TOY-5-UN", "TOY-8-UN", "TOY-10"):
        declaration = declaration_of(toy_id)
        assert declaration.is_trusted_source is False
        assert source_license_required(declaration) is False
        check_source_license(declaration)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_gate_failures_are_independent_and_neither_masks_the_other() -> None:
    """TOY-7 fails A-SRC *in addition to* part (i); both are reported."""
    declaration = declaration_of("TOY-7")
    with pytest.raises(SecurityGateError) as raised:
        check_key_length_permitted(declaration)
    message = str(raised.value)
    assert "(A-SRC)" in message
    assert "`general` form" in message
    assert "attack_set_license" in message

    # Supplying the A-SRC licence leaves the constraint gate closed, and vice
    # versa: the two are independent.
    licensed_source = replace(
        declaration, source_replacement_license={"certificate": "supplied"}
    )
    with pytest.raises(SecurityGateError) as raised:
        check_key_length_permitted(licensed_source)
    assert "(A-SRC)" not in str(raised.value)
    assert "`general` form" in str(raised.value)

    licensed_attack = replace(
        declaration, attack_set_license={"certificate": "supplied"}
    )
    with pytest.raises(SecurityGateError) as raised:
        check_key_length_permitted(licensed_attack)
    assert "(A-SRC)" in str(raised.value)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
def test_the_source_licence_gate_blocks_the_key_length_not_the_value() -> None:
    """A blocked A-SRC gate still reports ``h_low``: numerical use is unrestricted."""
    stripped = replace(
        declaration_of("TOY-8-T"),
        source_replacement_license=None,
    )
    from certiqs_key.solvers.frank_wolfe import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    result = solve(stripped, QicsSectorChoiOracle(), alpha=1.5)
    assert result.key_length is None
    assert "A-SRC" in result.key_length_reason
    assert math.isfinite(result.h_low)
    assert result.h_low == pytest.approx(
        oracle("O-UNTRUSTED-CONSERVATIVE").closed_form(1.5), abs=SOLVER
    )


# ---------------------------------------------------------------------------
# O-PARTY-COMPUTABILITY
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_o_party_computability_frozen_verdicts() -> None:
    """O-PARTY-COMPUTABILITY: on TOY-10, ``h = A`` is admissible, ``h = B`` not."""
    entry = oracle("O-PARTY-COMPUTABILITY")
    assert entry.claims == ("C1", "C14")
    assert entry.toy_id == "TOY-10"

    from certiqs_key.domain.manifest import KeyHolder

    declaration = declaration_of("TOY-10")
    assert declaration.key_holder is KeyHolder.ALICE
    validate_declaration(declaration)
    # r(x0, v_ab) = a factors through pi_A.
    for v in declaration.bob_outcomes:
        assert declaration.readout("A", "x0", v) == ("a0" if v[1] == "0" else "a1")

    # h = B is INADMISSIBLE: pi_B(x0, v00) = pi_B(x0, v10) = b0 while the raw
    # keys differ. The superseded 0.2.x reading would have passed it, because r
    # IS a function of v.
    as_bob = replace(declaration, key_holder=KeyHolder.BOB)
    with pytest.raises(DeclarationError) as raised:
        validate_declaration(as_bob)
    assert "def:admissible-declaration (viii)" in str(raised.value)
    assert "own readout" in str(raised.value)
    assert set(declaration.key_map.values()) == {0, 1}


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_the_embedded_declaration_reproduces_toy1(alpha: float) -> None:
    """TOY-10 is TOY-1's protocol re-declared the 0.3.0 way: same ``h_low``."""
    embedded = solve_toy("TOY-10", alpha)
    original = solve_toy("TOY-1", alpha)
    assert embedded.h_low == pytest.approx(original.h_low, abs=SOLVER)
    assert embedded.h_low == pytest.approx(0.0, abs=SOLVER)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_default_partition_reproduces_the_0_2_x_declarations() -> None:
    """Def. ``def:declaration``: the default partition IS the 0.2.x reading."""
    for toy_id in ("TOY-1", "TOY-5", "TOY-6", "TOY-7"):
        declaration = declaration_of(toy_id)
        assert declaration.party_partition is None
        partition = declaration.partition
        assert partition.is_default is True
        for x in declaration.alice_outcomes:
            for v in declaration.bob_outcomes:
                assert partition.readout_alice[(x, v)] == x
                assert partition.readout_bob[(x, v)] == v
                assert declaration.announcement(x, v) == (
                    declaration.announce_alice[x],
                    declaration.announce_bob[v],
                )


# ---------------------------------------------------------------------------
# O-CHOI-BASIS-INVARIANCE
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
@pytest.mark.parametrize(
    ("alpha", "expected"), oracle("O-CHOI-BASIS-INVARIANCE").frozen_values
)
def test_o_choi_basis_invariance_frozen_value(alpha: float, expected: float) -> None:
    """O-CHOI-BASIS-INVARIANCE: TOY-9's ``h_low``, from the singular marginal."""
    entry = oracle("O-CHOI-BASIS-INVARIANCE")
    assert entry.claims == ("C11",)
    assert entry.toy_id == "TOY-9"
    result = solve_toy("TOY-9", alpha)
    assert result.h_low == pytest.approx(expected, abs=SOLVER)
    assert result.assurance is BRACKET_TIER  # certified where installed (P2)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_second_declared_basis_is_refused_and_the_invariance_stands() -> None:
    """Remark ``rem:basis-invariance``, and what 1.0.0's exactness row does to it.

    RE-POINTED, AND ONLY ONE OF THE TWO STATEMENTS MOVES. The frozen entry
    ``O-CHOI-BASIS-INVARIANCE`` says two things: that ``h_low``, ``key_length``
    and ``sector_report`` do not depend on which admissible frame is used, and
    that the two hand-authored coordinate matrices ``J_1`` and ``J_2`` are
    DIFFERENT while the state is the same. Run A marked the entry NOT
    superseded, and the mathematics is indeed untouched -- it is a statement
    about real numbers.

    WHAT MOVES IS WHICH FRAMES THIS MODULE WILL CONSUME. Section 2.6's
    ``choi_isometry`` row declares the window "exactly 0, entrywise, as
    binary64 data; NO DECLARED NUMBER", and names what makes that reachable:
    "BOTH CONSTRUCTIONS OF SECTION 4.13 MEET IT BY ``{0, 1}`` ARITHMETIC;
    anything else is refused with ``choi_isometry_inexact``." ``iota_1`` is a
    ``{0, 1}`` frame and passes. ``iota_2`` is the Hadamard frame, whose
    ``1/sqrt 2`` entries give ``iota^dagger iota - 1`` a worst entry of
    ``2.22e-16`` -- admitted by the 0.5.0 ``1e-10`` window, refused now.

    THE INVARIANCE IS STILL ASSERTED, on the frame that survives: the state the
    first parametrization carries is the frozen ``TOY9_OMEGA`` and its
    coordinates are the frozen ``J_1``. What can no longer be asserted THROUGH
    THIS MODULE is the comparison against ``J_2``, and the frozen matrices
    stand as the record of it.
    """
    declaration = declaration_of("TOY-9")

    # THE {0, 1} FRAME PASSES, and carries the frozen coordinates.
    first = choi_parametrization(declaration, iota=TOY9_IOTA_1.astype(np.complex128))
    omega = {"s0": TOY9_OMEGA.astype(np.complex128)}
    assert np.allclose(first.choi_from_state(omega)["s0"], TOY9_J_1, atol=EXACT)

    # THE HADAMARD FRAME IS REFUSED, with the contract's own reason string, and
    # the defect that refuses it is asserted rather than described.
    hadamard = TOY9_IOTA_2.astype(np.complex128)
    residual = hadamard.conj().T @ hadamard - np.eye(hadamard.shape[1])
    assert 0.0 < float(np.max(np.abs(residual))) < 1e-10
    with pytest.raises(ChoiIsometryError) as raised:
        choi_parametrization(declaration, iota=hadamard)
    assert str(raised.value.reason) == "choi_isometry_inexact"
    assert "{0, 1} ARITHMETIC" in str(raised.value)

    # AND THE FROZEN MATRICES ARE STILL DIFFERENT, which is the entry's own
    # second statement and is a fact about the numbers rather than about this
    # module: the state is basis-independent, the coordinates are not.
    assert not np.allclose(np.asarray(TOY9_J_1), np.asarray(TOY9_J_2), atol=EXACT)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
def test_h_low_does_not_depend_on_the_declared_basis_but_is_recorded() -> None:
    """The two obligations of Section 2.5, both discharged.

    ``h_low`` does not depend on the declared basis, and the frame a run used is
    recorded -- and ABSENT wherever the contract says it should be.

    THE ONE DRIVER takes no declared basis. The one-factor loop took a declared
    ``iota`` and re-solved in it; the one driver builds its frame by the
    declared construction (``lem:choi-factor``: the support frame in POVM
    form) and takes none. So the invariance is asserted where it lives, on the
    solved point: the state the run returned, written in the declared frame
    ``TOY9_IOTA_1`` and in the default one, has ONE objective value, and it is
    the run's ``h_low``. The frozen matrices and values are unchanged.
    """
    from certiqs_key.meat_core.declaration.general import general_from_accepted
    from certiqs_key.meat_core.objective.choi import choi_objective_value
    from certiqs_key.meat_core.objective.joint import joint_choi_parametrization
    from certiqs_key.solvers.frank_wolfe import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    declaration = declaration_of("TOY-9")
    result = solve(declaration, QicsSectorChoiOracle(), alpha=1.5)
    assert result.final_iterate is not None
    states = joint_choi_parametrization(
        general_from_accepted(declaration)
    ).state_from_choi(result.final_iterate)
    omega = {pair[1]: block for pair, block in states.items()}
    maps = generate_maps(declaration)
    q = dict(result.optimized_q)
    values = []
    for iota in (TOY9_IOTA_1.astype(np.complex128), None):
        frame = choi_parametrization(declaration, iota=iota)
        values.append(
            choi_objective_value(maps, frame, q, frame.choi_from_state(omega), 1.5)
        )
    assert values[0] == pytest.approx(values[1], abs=SOLVER)
    assert values[0] == pytest.approx(result.h_low, abs=SOLVER)

    # THE FRAME THE RUN USED IS RECORDED, per Alice sector, and it is a frame
    # of supp tau_A: an isometry C^2 -> C^3 whose range carries tau_A.
    (record,) = result.certificate["choi_input_basis"].values()
    assert record["alice_dim"] == 3 and record["input_dim"] == 2
    iota_used = np.asarray(record["real"]) + 1j * np.asarray(record["imag"])
    assert np.allclose(iota_used.conj().T @ iota_used, np.eye(2), atol=EXACT)
    tau = np.asarray(declaration.trusted_marginal, dtype=np.complex128)
    projector = iota_used @ iota_used.conj().T
    assert np.allclose(projector @ tau @ projector, tau, atol=EXACT)
    assert "choi_input_basis" in result.as_payload()["optimizer_certificate"]

    # WIDENED AT 1.0.0, AND THE WIDENING IS A REFUSAL TO DECIDE SOMETHING:
    # NO RUN COMPUTES rank tau_A, so the field is recorded on every
    # trusted-source-mode run and names the construction; it is ABSENT on
    # exactly the runs with no Choi input register at all, the untrusted-source
    # ones (Definition def:untrusted-choi (a)).
    for toy_id in ("TOY-1", "TOY-7", "TOY-8-T"):
        certificate = solve_toy(toy_id, 1.5).certificate
        assert "choi_input_basis" in certificate, toy_id
        assert "constraint_row_form" in certificate, toy_id
    for toy_id in ("TOY-8-UN",):
        certificate = solve_toy(toy_id, 1.5).certificate
        assert "choi_input_basis" not in certificate, toy_id
        assert "constraint_row_form" not in certificate, toy_id


@pytest.mark.contract
@pytest.mark.requires_qics
@pytest.mark.parametrize("alpha", [1.05, 1.5, 2.0])
def test_a_singular_non_diagonal_marginal_runs_on_the_full_frame(alpha: float) -> None:
    """lem:choi-marginal (a): TOY-9 rotated off the diagonal, same ``h_low``.

    TOY-9 conjugated by the Hadamard ``H`` on ``span{e0, e1}`` (``e2`` fixed):
    ``tau_A = H diag(3/4, 1/4, 0) H = [[1/2, 1/4, 0], [1/4, 1/2, 0], [0, 0, 0]]``
    (diagonal ``(3/4 + 1/4)/2``, off-diagonal ``(3/4 - 1/4)/2``), still of rank
    2, and ``M_x0 = H |e0><e0| H = [[1/2, 1/2, 0], [1/2, 1/2, 0], [0, 0, 0]]``,
    ``M_x1 = 1_A - M_x0``. All entries are dyadic. ``tr[M_x0 tau_A] =
    (1/2)(1/2 + 1/4 + 1/4 + 1/2) = 3/4`` and ``tr[M_x1 tau_A] = 1/4``, so
    TOY-9's derivation holds unchanged: ``Phi`` is ``(3/4, 1/4)`` at every
    feasible point and ``h_low = (alpha/(alpha-1)) (1/2) log2 3``.

    ``tau_A`` is not diagonal bit for bit, so the production frame is
    construction (a), the full frame, with ``d_{A_0} = d_A = 3`` although
    ``rank tau_A = 2``: no rank is decided, and ``thm:choi`` maps the Choi
    feasible set onto the state one, so the value is the same.
    """
    from certiqs_key.solvers.frank_wolfe import solve
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    tau = np.array(
        [[0.5, 0.25, 0.0], [0.25, 0.5, 0.0], [0.0, 0.0, 0.0]], dtype=np.complex128
    )
    m_x0 = np.array(
        [[0.5, 0.5, 0.0], [0.5, 0.5, 0.0], [0.0, 0.0, 0.0]], dtype=np.complex128
    )
    rotated = replace(
        declaration_of("TOY-9"),
        alice_marginal=tau,
        alice_povm={"x0": m_x0, "x1": np.eye(3, dtype=np.complex128) - m_x0},
    )
    validate_declaration(rotated)
    result = solve(rotated, QicsSectorChoiOracle(), alpha=alpha)
    (record,) = result.certificate["choi_input_basis"].values()
    assert record["frame"] == "full"
    assert record["alice_dim"] == 3 and record["input_dim"] == 3
    expected = (alpha / (alpha - 1.0)) * 0.5 * math.log2(3.0)
    assert result.h_low == pytest.approx(expected, abs=SOLVER)
    # A non-diagonal marginal's frame is not enclosed by the certified
    # evaluation (out of scope, fails closed with its reason),
    # so the run stays at the first-order tier.
    assert result.assurance is Assurance.FIRST_ORDER
    assert all(
        point["reasons"] == ["frame_not_enclosed"]
        for point in result.certified["points"]
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_no_iota_may_be_declared_in_untrusted_source_mode() -> None:
    """Definition ``def:untrusted-choi`` (a).

    There is no ``A_0`` to declare a basis of.
    """
    with pytest.raises(DeclarationError, match="def:untrusted-choi"):
        choi_parametrization(
            declaration_of("TOY-8-UN"), iota=np.eye(2, dtype=np.complex128)
        )


# ---------------------------------------------------------------------------
# O-GRADIENT-FACE-SPLIT
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    ("alpha", "expected"), oracle("O-GRADIENT-FACE-SPLIT").frozen_values
)
def test_o_gradient_face_split_ambient_value(alpha: float, expected: float) -> None:
    """O-GRADIENT-FACE-SPLIT: the implementation computes the AMBIENT ``T``.

    TOY-1's sector ``s0`` at ``w0 = 1`` is the contract's own rank-one witness:
    ``|eta> = (1, 1)/sqrt2`` spread over two raw-key values, so ``Z(X^p)`` has
    rank two while ``X`` has rank one. Rule (b) of Theorem ``thm:gradient`` (i)
    keeps ``Y`` ambient and gives ``2^{1-alpha}``; the discarded "compress
    everything to ``supp X``" rule gives ``2^{-alpha}``.
    """
    entry = oracle("O-GRADIENT-FACE-SPLIT")
    assert entry.claims == ("C6", "C12")
    assert entry.toy_id == "TOY-1"

    maps = generate_maps(declaration_of("TOY-1"))
    (klass,) = maps.branches["chat0"]["s0"].classes
    operator = branch_operator(klass, np.array([[1.0]], dtype=np.complex128))
    ambient = trace_power_pinched(operator, alpha, klass.labels)
    assert ambient == pytest.approx(expected, abs=EXACT)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(("alpha", "wrong"), O_GRADIENT_FACE_COMPRESSED_VALUES)
def test_the_discarded_compression_differs_and_errs_unsafely(
    alpha: float, wrong: float
) -> None:
    """The two rules disagree by exactly a factor of two, in the unsafe direction.

    A smaller ``T`` gives a smaller ``K``; the kernel ``d(u, v)`` is
    non-increasing in ``v`` (Lemma ``foundations/lem:kernel``), so a smaller ``K`` gives
    a LARGER objective, a larger ``h_low`` and a larger key. That is why the
    contract calls the split rule "the rule an implementation must realize"
    rather than one of two acceptable conventions.
    """
    maps = generate_maps(declaration_of("TOY-1"))
    (klass,) = maps.branches["chat0"]["s0"].classes
    operator = branch_operator(klass, np.array([[1.0]], dtype=np.complex128))

    ambient = trace_power_pinched(operator, alpha, klass.labels)
    # The discarded rule, re-derived here rather than taken from the code: the
    # WHOLE computation compressed to supp X = C|eta>.
    values, vectors = np.linalg.eigh(operator)
    eta = vectors[:, int(np.argmax(values))]
    pinched = pinch(psd_power(operator, 1.0 / alpha), klass.labels)
    compressed = float(np.real(eta.conj() @ pinched @ eta)) ** alpha

    assert compressed == pytest.approx(wrong, abs=EXACT)
    assert ambient == pytest.approx(2.0 * compressed, abs=EXACT)
    assert compressed < ambient


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_full_compression_agrees_only_on_a_z_invariant_face(alpha: float) -> None:
    """The licensing condition of Theorem ``thm:gradient`` (i), both directions.

    TOY-1's sector ``s1`` has its whole range inside one ``Z``-eigenspace, so
    ``supp X`` IS ``Z``-invariant and full compression is licensed and agrees.
    Sector ``s0``'s is not, and it does not.
    """
    maps = generate_maps(declaration_of("TOY-1"))
    for sector, agrees in (("s1", True), ("s0", False)):
        (klass,) = maps.branches["chat0"][sector].classes
        operator = branch_operator(klass, np.array([[1.0]], dtype=np.complex128))
        ambient = trace_power_pinched(operator, alpha, klass.labels)
        values, vectors = np.linalg.eigh(operator)
        keep = vectors[:, values > 1e-12 * float(np.max(values))]
        inner = keep.conj().T @ operator @ keep
        # Compressing EVERYTHING to supp X: powers and pinching taken inside.
        labels_inside = np.zeros(inner.shape[0], dtype=np.int64)
        fully_compressed = psd_trace_power(
            pinch(psd_power(inner, 1.0 / alpha), labels_inside), alpha
        )
        if agrees:
            assert fully_compressed == pytest.approx(ambient, abs=EXACT)
        else:
            assert abs(fully_compressed - ambient) > 1e-3


# ---------------------------------------------------------------------------
# Every 0.3.0 toy runs end to end
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.requires_qics
@pytest.mark.parametrize("candidate", SOURCE_MODE_TOYS, ids=lambda t: t.toy_id)
def test_every_source_mode_toy_solves_and_reports_estimate(
    candidate: ToyDeclaration,
) -> None:
    """The exit condition, on the seven 0.3.0 declarations."""
    result = solve_toy(candidate.toy_id, 1.5)
    assert math.isfinite(result.h_low)
    assert result.h_low >= -SOLVER
    # Certified where the ball arithmetic is installed (P2) and the run is
    # reported at that tier; a toy whose key-length gate is closed (TOY-5-UN,
    # no attack-set licence) reports the estimate, and its achieved tier is
    # first-order (the frank-wolfe interface's optimizer_certificate row).
    assert result.assurance is (
        BRACKET_TIER if result.key_length is not None else Assurance.FIRST_ORDER
    )
    assert result.mathematical_spec_version == "meat-core@1.28.0"
    payload = result.as_payload()
    # The achieved tier is a reading of the bound's presence; the record
    # names why (the acceptance-set narrowing that travelled here as
    # `scope_narrowings` is stated where a third tag is
    # refused).
    assert payload["optimizer_certificate"]["assurance_reason"] == (
        "first_order_reported"
    )
