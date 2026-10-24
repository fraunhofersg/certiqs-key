"""The constructions of Sections 4.1-4.8, replayed against the FROZEN registry.

``tests/oracles/registry_reductions.py`` is frozen:
every value was derived by hand from the accepted ``contract.tex`` 0.1.3 before
``src/certiqs_key/reductions/`` existed. These tests recompute each of them with the
implementation and compare exactly -- no tolerance appears anywhere, because the
substrate is exact Gaussian rationals on both sides.

An expected value that turned out to be wrong would be a FINDING reported with
its derivation, never an edit; none was found.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from registry_reductions import (
    BLK_GT_V0,
    BLK_GT_V1,
    BRANCH_MIXTURE,
    CERT_POSITIVITY,
    CERT_SPECTRAL,
    CERT_TWO_SECTOR,
    CHAIN_LADDER,
    ENCODED_CONSTRAINT,
    FLAGS_ENOUGH,
    MIXTURE_CASE,
    MIXTURE_N_J0,
    MIXTURE_N_J1,
    MP_V0,
    MP_V1,
    OBSTRUCTION_CASES,
    P_EQUALS_ONE,
    PI_FLAG_Q,
    PI_GT_B,
    PI_LEQ_B,
    PI_LEQ_Q,
    POSTPROCESSING_CASE,
    PR_OBSTRUCTION,
    PROBE22,
    PROBE22_MPRIME,
    PROBE22_SUM_T0,
    PROBE22_TARGET,
    PROBE22_UNSOUND,
    PROBE22_V,
    RELATION_CASES,
    SUPERSESSIONS,
    TOL2_TARGETPOSCOMP,
    TOL2_TOLERANCE_RECORD,
    TOL_ENTRY_TWO_SECTOR,
    TOP_ELEMENT,
    TRANSFER_ONE_ROUND,
    WEIGHT_FREEDOM,
    WP3,
    WP3_FFSS_V0,
    WP3_FFSS_V1,
    WP3_FWP_V0,
    WP3_FWP_V1,
    WP3_KRAUS,
    WP3_KRAUS_PRIME,
    WP3_M_V0,
    WP3_M_V1,
    WP3_STATISTICS,
)

from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    add,
    adjoint_from_kraus,
    diagonal,
    dimension,
    direct_sum,
    equal,
    identity,
    is_positive_semidefinite,
    matmul,
    matrix,
    scale,
    subtract,
    trace,
    zeros,
)
from certiqs_key.reductions.channels import (
    adjoint_is_unital,
    flag_projector,
    flags_enough_adjoint,
    instrument_adjoint,
    is_povm,
    mixture_adjoint,
    mp_adjoint,
    split_blocks,
)
from certiqs_key.reductions.constraints import (
    certificate_holds,
    classify_certificate,
    probe_expectation_entry,
)
from certiqs_key.reductions.reasons import CertificateKind, Relation, SourceMode
from certiqs_key.reductions.validation import (
    rule_obstructions,
)
from certiqs_key.reductions.wpfss.construction import (
    flat_sectors,
    fss_instance_entry,
    fss_target,
    mprime_family,
    noise_adjoint,
    transported_cutoff_projectors,
    two_sector_entry,
    wp_adjoint,
    wpfss_target,
)
from certiqs_key.reductions.wpfss.validation import (
    rule_total_weight,
)

F = Fraction


def m(frozen: object) -> Matrix:
    """Convert a frozen registry matrix into the module's exact representation.

    The registry writes an entry as the exact pair ``(Fraction, Fraction)``; this
    module writes it as :class:`~certiqs_key.foundations.exact.Cx`. The conversion is
    a change of spelling and loses nothing -- both are exact Gaussian rationals,
    which is the whole point of open implementation choice 1 having been decided
    the way it was.
    """
    rows = frozen  # type: ignore[assignment]
    return matrix([[Cx(entry[0], entry[1]) for entry in row] for row in rows])  # type: ignore[index,union-attr]


def dense(blocks: object) -> Matrix:
    """Return the ``d_Q x d_Q`` array a SECTOR-BLOCK LIST means.

    A constraint entry's ``hat O_k`` is carried as its sector-block list, like
    every other operator on ``Q`` (spec/architecture.md 2.8-2.9). The frozen
    registry values it is compared with here
    are whole-space arrays, and a pull-back through :func:`wp_adjoint` is a
    whole-space computation, so THE TEST forms the direct sum -- the code
    builds none.
    """
    return direct_sum(list(blocks))  # type: ignore[arg-type]


def sector_blocks(operator: Matrix, dims: object) -> tuple[Matrix, ...]:
    """Return an operator as the sector-block list its sector map names."""
    return tuple(split_blocks(operator, list(dims)))  # type: ignore[arg-type]


def expectation(operator: Matrix, state: Matrix) -> Fraction:
    """Return ``tr[operator state]`` as an exact rational."""
    value = trace(matmul(operator, state))
    assert value.is_real, value
    return value.re


WP3_PRESERVED = (matrix([[F(2, 3)]]), matrix([[F(1, 3)]]))
WP3_WEIGHTS = (F(1, 4), F(1, 8))
WP3_ABOVE = (m(BLK_GT_V0), m(BLK_GT_V1))
WP3_PHYSICAL = (m(WP3_M_V0), m(WP3_M_V1))


# ---------------------------------------------------------------------------
#  PR6 / PR1: the targets built from DECLARED data alone
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_wpfss_target_reproduces_the_frozen_multi_bound_target() -> None:
    """Eq. ``eq:WPFSS`` from the preserved blocks and the weights, nothing else."""
    built = wpfss_target(WP3_PRESERVED, WP3_WEIGHTS)
    assert equal(built[0], m(WP3_FWP_V0))
    assert equal(built[1], m(WP3_FWP_V1))
    # No above-cutoff block was needed: the supplier emits none (Section 2.3).
    assert is_povm(list(built))


@pytest.mark.contract
@pytest.mark.oracle
def test_fss_target_reproduces_the_frozen_flag_state_target() -> None:
    """Eq. ``eq:FSS``, the ``p_v == 0`` case."""
    built = fss_target(WP3_PRESERVED)
    assert equal(built[0], m(WP3_FFSS_V0))
    assert equal(built[1], m(WP3_FFSS_V1))
    assert is_povm(list(built))


@pytest.mark.contract
@pytest.mark.oracle
def test_mprime_family_reproduces_the_frozen_rank_one_pvm() -> None:
    """Eq. ``eq:Lwp``'s ``M'_v = (blk M^{>N}_v - p_v 1)/(1 - p)``."""
    built = mprime_family(WP3_ABOVE, WP3_WEIGHTS)
    assert equal(built[0], m(MP_V0))
    assert equal(built[1], m(MP_V1))
    assert is_povm(list(built))
    assert WP3["one_minus_total"] == 1 - sum(WP3_WEIGHTS, start=F(0))


# ---------------------------------------------------------------------------
#  PR1: the adjoint, in closed form and through the frozen Kraus set
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_wp_adjoint_returns_the_frozen_physical_povm() -> None:
    """``Lambda^WP+(F^WP_v) = M_v``, Proposition ``prop:chain`` (i)."""
    mprime = mprime_family(WP3_ABOVE, WP3_WEIGHTS)
    for target, physical in zip(
        (m(WP3_FWP_V0), m(WP3_FWP_V1)), WP3_PHYSICAL, strict=True
    ):
        assert equal(wp_adjoint(target, 1, mprime), physical)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_fss_adjoint_returns_the_same_physical_povm() -> None:
    """The ``p_v == 0`` case: ``M'_v`` replaced by ``blk M^{>N}_v`` (eq:Lfss)."""
    for target, physical in zip(
        (m(WP3_FFSS_V0), m(WP3_FFSS_V1)), WP3_PHYSICAL, strict=True
    ):
        assert equal(wp_adjoint(target, 1, WP3_ABOVE), physical)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_closed_form_agrees_with_the_frozen_kraus_realization() -> None:
    """Eq. ``eq:WPadjoint`` against ``sum_K K+ X K`` on the frozen Kraus set.

    The closed form is what the contract proves and what an artifact path uses;
    the Kraus set exists only because THIS instance makes it rational. Their
    agreement is the check that the closed form is the adjoint of a channel and
    not merely a formula.
    """
    mprime = mprime_family(WP3_ABOVE, WP3_WEIGHTS)
    kraus = tuple(m(operator) for operator in WP3_KRAUS)
    for target in (m(WP3_FWP_V0), m(WP3_FWP_V1), m(PI_LEQ_Q), m(PI_FLAG_Q)):
        assert equal(adjoint_from_kraus(kraus, target), wp_adjoint(target, 1, mprime))
    # Unitality, which is trace preservation read through Eq. eq:pairing.
    assert adjoint_is_unital(adjoint_from_kraus(kraus, identity(3)), 3)
    assert adjoint_is_unital(wp_adjoint(identity(3), 1, mprime), 3)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_transported_cutoff_projectors_are_the_frozen_pullbacks() -> None:
    """Eq. ``eq:transportproj``, under BOTH channels of the frozen instance."""
    pi_leq, pi_flag = transported_cutoff_projectors(1, 2)
    assert equal(pi_leq, m(PI_LEQ_Q))
    assert equal(pi_flag, m(PI_FLAG_Q))
    mprime = mprime_family(WP3_ABOVE, WP3_WEIGHTS)
    assert equal(wp_adjoint(pi_leq, 1, mprime), m(PI_LEQ_B))
    assert equal(wp_adjoint(pi_flag, 1, mprime), m(PI_GT_B))
    assert equal(wp_adjoint(pi_leq, 1, WP3_ABOVE), m(PI_LEQ_B))
    assert equal(wp_adjoint(pi_flag, 1, WP3_ABOVE), m(PI_GT_B))
    # Positive, though NEITHER is a multiple of the identity -- the sentence
    # Section 2.1 uses to admit the default pair on the trivial certificate.
    assert is_positive_semidefinite(m(PI_LEQ_B))
    assert is_positive_semidefinite(m(PI_GT_B))
    assert not equal(m(PI_LEQ_B), scale(F(1), identity(3)))
    assert not equal(m(PI_GT_B), scale(F(1), identity(3)))


@pytest.mark.contract
@pytest.mark.oracle
def test_two_realizing_channels_agree_on_the_carried_span() -> None:
    """The uniqueness clause of Lemma ``lem:statistics``, on the frozen pair."""
    kraus = tuple(m(operator) for operator in WP3_KRAUS)
    kraus_prime = tuple(m(operator) for operator in WP3_KRAUS_PRIME)
    for carried in (m(WP3_FWP_V0), m(WP3_FWP_V1), m(PI_LEQ_Q), m(PI_FLAG_Q)):
        assert equal(
            adjoint_from_kraus(kraus, carried),
            adjoint_from_kraus(kraus_prime, carried),
        )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", RELATION_CASES, ids=lambda case: str(case.case_id))
def test_every_frozen_relation_holds_under_the_module_s_adjoint(case: object) -> None:
    """Every frozen ``RelationCase``'s carried pull-backs, recomputed."""
    mprime = (
        mprime_family(WP3_ABOVE, WP3_WEIGHTS)
        if case.case_id != "WP3-fss"  # type: ignore[attr-defined]
        else WP3_ABOVE
    )
    for (_, target), (_, physical) in zip(
        case.target,
        case.physical,
        strict=True,  # type: ignore[attr-defined]
    ):
        assert equal(wp_adjoint(m(target), 1, mprime), m(physical))
    for _, ohat, pullback in case.carried:  # type: ignore[attr-defined]
        assert equal(wp_adjoint(m(ohat), 1, mprime), m(pullback))


# ---------------------------------------------------------------------------
#  PR1: statistics equality on the frozen inputs
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", WP3_STATISTICS, ids=lambda case: str(case.case_id))
def test_statistics_equality_on_every_frozen_input(case: object) -> None:
    """Lemma ``lem:statistics`` (ii) and (iii), on the frozen squashed image."""
    target = {"v0": m(WP3_FWP_V0), "v1": m(WP3_FWP_V1)}
    squashed = diagonal(list(case.squashed_diagonal))  # type: ignore[attr-defined]
    if case.side_operator is None:  # type: ignore[attr-defined]
        for label, value in case.statistics:  # type: ignore[attr-defined]
            assert expectation(target[label], squashed) == value
    if case.rho is not None:  # type: ignore[attr-defined]
        physical = {"v0": WP3_PHYSICAL[0], "v1": WP3_PHYSICAL[1]}
        for label, value in case.statistics:  # type: ignore[attr-defined]
            assert expectation(physical[label], m(case.rho)) == value  # type: ignore[attr-defined]


@pytest.mark.contract
@pytest.mark.oracle
def test_the_one_round_transfer_output_states_agree_with_the_module_s_adjoint() -> None:
    """Theorem ``thm:factorization`` at ``n = 1``: THE SAME output state.

    The physical run measures ``M_v`` on the two branches of ``rho``; the
    squashed run measures ``F^WP_v`` on the corresponding branches of
    ``sigma = (Lambda (x) id)(rho)``. Both are computed here from the frozen
    branch data, and Eq. ``eq:sameoutput`` says they are EQUAL -- not close.
    """
    case = TRANSFER_ONE_ROUND
    mprime = mprime_family(WP3_ABOVE, WP3_WEIGHTS)
    target = {"v0": m(WP3_FWP_V0), "v1": m(WP3_FWP_V1)}
    # rho's two branches: |0><0| on r0, |psi_1><psi_1| = M'_v1 on r1.
    physical_branches = {
        "r0": matrix([[F(1), 0, 0], [0, 0, 0], [0, 0, 0]]),
        "r1": _embed_above(m(MP_V1)),
    }
    squashed_branches = {
        "r0": diagonal([F(1), F(0), F(0)]),
        "r1": diagonal([F(0), F(0), F(1)]),
    }
    for (label, branch), value in case.physical_output:
        physical = expectation(
            {"v0": WP3_PHYSICAL[0], "v1": WP3_PHYSICAL[1]}[label],
            physical_branches[branch],
        )
        assert physical * F(1, 2) == value
    for (label, branch), value in case.squashed_output:
        squashed = expectation(target[label], squashed_branches[branch])
        assert squashed * F(1, 2) == value
    # And the adjoint is what makes the two runs the same run.
    for label in ("v0", "v1"):
        assert equal(
            wp_adjoint(target[label], 1, mprime),
            {"v0": WP3_PHYSICAL[0], "v1": WP3_PHYSICAL[1]}[label],
        )


def _embed_above(block: Matrix) -> Matrix:
    """Embed a 2x2 above-cutoff operator into the 3-dimensional source space."""
    out = [[Cx(F(0), F(0)) for _ in range(3)] for _ in range(3)]
    for i in range(2):
        for j in range(2):
            out[i + 1][j + 1] = block[i][j]
    return tuple(tuple(row) for row in out)


# ---------------------------------------------------------------------------
#  PR3 / PR6: certificates and the constraints they discharge
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_cor_fssinstance_entry_and_its_frozen_pullback() -> None:
    """Eq. ``eq:fssentry``: ``O^ = F^FSS_o - p_o Pi_Flag``, ``>=``, ``c = 0``."""
    sectors = flat_sectors([1], ["v0", "v1"])
    entry = fss_instance_entry(
        sector_blocks(m(WP3_FFSS_V0), sectors.dimensions),
        sectors,
        preserved_dim=1,
        alphabet_size=2,
        weight=F(1, 4),
        label="F^FSS_v0 - (1/4) Pi_flag",
        certified_against="Lambda-FSS",
        mode=SourceMode.TRUSTED,
    )
    # THE ENTRY IS ITS SECTOR-BLOCK LIST: one square block per sector, in the
    # sector map's order, and the frozen whole-space value is what the direct
    # sum of that list is.
    assert [dimension(block) for block in entry.operator] == [1, 1, 1]
    operator = dense(entry.operator)
    assert equal(operator, m(CERT_POSITIVITY.ohat))
    pullback = wp_adjoint(operator, 1, WP3_ABOVE)
    assert equal(pullback, m(CERT_POSITIVITY.pullback))
    assert certificate_holds(pullback, entry.relation, entry.constant)
    assert classify_certificate(pullback, entry.relation, entry.constant) is (
        CertificateKind.POSITIVITY
    )
    # The operator on Q is NOT positive; its PULL-BACK is. That is the whole
    # content of Corollary cor:pullback (ii).
    assert not is_positive_semidefinite(operator)
    assert is_positive_semidefinite(pullback)
    # It equals M_v0 - (1/4) Pi_>N, the form cor:fssinstance writes.
    assert equal(pullback, subtract(WP3_PHYSICAL[0], scale(F(1, 4), m(PI_GT_B))))
    # And it is not vacuous: |f_v1><f_v1| is excluded (prop:chain (iii)).
    assert expectation(operator, diagonal([F(0), F(0), F(1)])) == F(-1, 4)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_spectral_certificate_on_the_flag_projector() -> None:
    """Corollary ``cor:pullback`` (iii) with ``a = 0``, ``b = 1``."""
    _, pi_flag = transported_cutoff_projectors(1, 2)
    assert equal(pi_flag, m(CERT_SPECTRAL.ohat))
    pullback = wp_adjoint(pi_flag, 1, mprime_family(WP3_ABOVE, WP3_WEIGHTS))
    assert equal(pullback, m(CERT_SPECTRAL.pullback))
    assert certificate_holds(pullback, Relation.GE, F(0))
    assert certificate_holds(pullback, Relation.LE, F(1))


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_sector_entry_and_the_strictness_witness() -> None:
    """Eq. ``eq:two-sector-entry``: the ``a > 0`` entry is the STRONGER constraint.

    ``CERT_TWO_SECTOR`` is marked ``superseded`` (kind: constant)
    and its replacement is ``TOL_ENTRY_TWO_SECTOR``: the operator, the pull-back and
    the comparison with the ``a = 0`` entry are asserted here exactly as
    0.1.3 states them, while THE FROZEN CONSTANT ``c = 0`` IS
    THE ``eps_op = 0`` CONSTANT ONLY. Remark ``rem:published`` closes: "The
    admissible object is the operator entry eq:two-sector-entry with relation >= and
    c = 0 -- AT A DECLARED eps_op > 0, WITH c = -eta_e INSTEAD, by Corollary
    cor:tolentries (iv)." The ``eps_op > 0`` half is not replayed (there is
    no declared tolerance); this test asserts the scope, so that the 0.1.3
    value cannot be read as unconditional.
    """
    sectors = flat_sectors([1], ["v0", "v1"])
    entry = two_sector_entry(
        sector_blocks(m(WP3_FFSS_V0), sectors.dimensions),
        sectors,
        preserved_dim=1,
        alphabet_size=2,
        below_cutoff_bound=F(2, 3),
        above_cutoff_bound=F(1, 4),
        label="two_sector",
        certified_against="Lambda-FSS",
        mode=SourceMode.UNTRUSTED,
    )
    operator = dense(entry.operator)
    assert equal(operator, m(CERT_TWO_SECTOR.ohat))
    pullback = wp_adjoint(operator, 1, WP3_ABOVE)
    assert equal(pullback, m(CERT_TWO_SECTOR.pullback))
    assert is_positive_semidefinite(pullback)
    # The frozen witness of strictness: sigma = (|q><q| + |f_v1><f_v1|)/2.
    sigma = diagonal([F(1, 2), F(0), F(1, 2)])
    default = fss_instance_entry(
        sector_blocks(m(WP3_FFSS_V0), sectors.dimensions),
        sectors,
        preserved_dim=1,
        alphabet_size=2,
        weight=F(1, 4),
        label="a=0",
        certified_against="Lambda-FSS",
        mode=SourceMode.UNTRUSTED,
    )
    assert expectation(dense(default.operator), sigma) == F(5, 24)
    assert expectation(operator, sigma) == F(-1, 8)

    # THE SCOPE OF THE FROZEN CONSTANT, asserted rather than assumed. The mark
    # names TOL_ENTRY_TWO_SECTOR as the replacement, and that case freezes BOTH
    # constants: 0 at eps_op = 0 and -eta_e = -1/125 at eps_op = 1/100.
    assert entry.constant == F(0)
    assert TOL_ENTRY_TWO_SECTOR.at_zero == ((">=", F(0)),)
    assert TOL_ENTRY_TWO_SECTOR.at_positive == ((">=", F(-1, 125)),)
    assert TOL_ENTRY_TWO_SECTOR.at_zero != TOL_ENTRY_TWO_SECTOR.at_positive
    mark = next(
        record for record in SUPERSESSIONS if record.symbol == "CERT_TWO_SECTOR"
    )
    assert mark.kind == "constant"
    assert mark.still_valid_at_zero_tolerance
    assert mark.replacement == ("TOL_ENTRY_TWO_SECTOR",)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_encoded_constraint_holds_on_every_state_and_the_fss_one_does_not() -> None:
    """Proposition ``prop:chain`` (iii): the two routes' whole difference.

    REWRITTEN AT 0.2.0. ``ENCODED_CONSTRAINT`` is marked ``superseded`` (kind:
    scope) and its replacements are ``TOL2_TARGETPOSCOMP`` and
    ``TOL2_TOLERANCE_RECORD`` -- not entry for entry, BECAUSE THERE IS NO ENTRY.
    Remark ``rem:tolscope``, the ``encoded``-route bullet: ``F^WP_v >= p_v
    Pi_flag`` is what that route encodes INSTEAD OF a ``CList`` entry, "OF THE
    STARRED TARGET THAT REMAINS EXACTLY TRUE; OF THE EMITTED NUMBERS IT HOLDS
    ONLY WITHIN eta_v... AND BECAUSE THE ROUTE EMITS NO CList, NO FIELD OF THE
    ARTIFACT CARRIES THAT RESIDUAL: it is visible only through
    operator_tolerance_record's eta_v and the target_povm row's qualification."

    So the frozen differences below STAND EXACTLY at ``eps_op = 0`` and are
    asserted unchanged; what this test adds is the statement of where the
    residual IS visible above zero, which is the mark's whole content.
    """
    targets = wpfss_target(WP3_PRESERVED, WP3_WEIGHTS)
    _, pi_flag = transported_cutoff_projectors(1, 2)
    for index, (label, expected) in enumerate(ENCODED_CONSTRAINT["wp_differences"]):
        difference = subtract(targets[index], scale(WP3_WEIGHTS[index], pi_flag))
        assert equal(difference, m(expected)), label
        # POSITIVE SEMIDEFINITE ON THE NOSE: it needs no constraint, no licence
        # and no attestation.
        assert is_positive_semidefinite(difference)
    fss = fss_target(WP3_PRESERVED)
    failing = subtract(fss[0], scale(WP3_WEIGHTS[0], pi_flag))
    assert (
        expectation(failing, diagonal([F(0), F(0), F(1)]))
        == (ENCODED_CONSTRAINT["fss_failure_value"])
    )

    # WHERE THE RESIDUAL IS VISIBLE ABOVE eps_op = 0, since no CList entry
    # carries it. The two replacements the mark names are the two places, and
    # both are frozen as DECLARED numbers rather than read off a target.
    mark = next(
        record for record in SUPERSESSIONS if record.symbol == "ENCODED_CONSTRAINT"
    )
    assert mark.kind == "scope"
    assert mark.still_valid_at_zero_tolerance
    assert mark.replacement == ("TOL2_TARGETPOSCOMP", "TOL2_TOLERANCE_RECORD")
    assert TOL2_TARGETPOSCOMP["negative_part"] == F(1, 125)
    assert TOL2_TOLERANCE_RECORD["present"] is True
    assert dict(TOL2_TOLERANCE_RECORD["eta_v"])[("y0", "t0")] == F(1, 125)


# ---------------------------------------------------------------------------
#  PR6: the ladder, the weight freedom, and the p = 1 refusal
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_noise_channel_carries_the_fss_target_to_the_wp_target() -> None:
    """Eq. ``eq:L2adjoint``: ``Lambda~+(F^FSS_v) = F^WP_v`` (eq:ladder rung 2)."""
    fss = fss_target(WP3_PRESERVED)
    wp = wpfss_target(WP3_PRESERVED, WP3_WEIGHTS)
    for index, (label, expected_diagonal) in enumerate(
        CHAIN_LADDER["noise_adjoint_check"]
    ):
        recovered = noise_adjoint(fss[index], 1, WP3_WEIGHTS)
        assert equal(recovered, wp[index]), label
        assert equal(recovered, diagonal(list(expected_diagonal)))
    assert tuple(CHAIN_LADDER["mu"]) == WP3_WEIGHTS


@pytest.mark.contract
@pytest.mark.oracle
def test_the_frozen_composition_diagonals_are_self_consistent() -> None:
    """The freeze's own four ``(Lambda^WP, Lambda^FSS)`` diagonal pairs, related.

    THIS CHECKS THE FROZEN VALUES AND NOT THE MODULE: the arithmetic below is
    Eq. ``eq:Lnoise``'s action on a diagonal, written out here, so what it
    decides is that the registry's two columns are consistent with each other.
    The same identity DECIDED THROUGH THE MODULE'S OWN ADJOINTS is
    :func:`test_the_exact_composition_holds_through_the_module_s_own_adjoints`,
    and that one is the test of Proposition ``prop:chain`` (ii).

    The last input carries COHERENCE ACROSS THE CUTOFF, which both sides
    discard; part (ii) says the identity holds for every ``rho`` including
    those, and a diagonal-only fixture could not exhibit it.
    """
    total = sum(WP3_WEIGHTS, start=F(0))
    for label, wp_diagonal, fss_diagonal in CHAIN_LADDER["composition_check"]:
        preserved, flag0, flag1 = wp_diagonal
        flag_total = flag0 + flag1
        recovered = (
            preserved,
            (1 - total) * flag0 + flag_total * WP3_WEIGHTS[0],
            (1 - total) * flag1 + flag_total * WP3_WEIGHTS[1],
        )
        assert recovered == tuple(fss_diagonal), label


@pytest.mark.contract
@pytest.mark.oracle
def test_a_smaller_weight_family_gives_a_cleaner_target() -> None:
    """Remark ``rem:weightfree`` with Eq. ``eq:weightmono``, frozen numbers."""
    smaller = tuple(value for _, value in WEIGHT_FREEDOM["smaller_weights"])
    built = wpfss_target(WP3_PRESERVED, smaller)
    for index, (label, expected) in enumerate(WEIGHT_FREEDOM["smaller_target"]):
        assert equal(built[index], diagonal(list(expected))), label
    # Psi+ carries the smaller-weight target back to the larger-weight one.
    larger = wpfss_target(WP3_PRESERVED, WP3_WEIGHTS)
    lam = WEIGHT_FREEDOM["lambda_coefficient"]
    nu = WEIGHT_FREEDOM["nu_diagonal"]
    for index in range(2):
        flag = [built[index][1][1].re, built[index][2][2].re]
        trace_nu = sum((nu[k] * flag[k] for k in range(2)), start=F(0))
        recovered = diagonal(
            [
                built[index][0][0].re,
                lam * flag[0] + trace_nu,
                lam * flag[1] + trace_nu,
            ]
        )
        assert equal(recovered, larger[index])


@pytest.mark.contract
@pytest.mark.oracle
def test_the_total_weight_one_declaration_is_refused_not_constructed() -> None:
    """Lemma ``lem:ple1`` and Remark ``rem:peqone``: ``p = 1`` is a refusal."""
    weights = tuple(value for _, value in P_EQUALS_ONE["weights"])
    assert sum(weights, start=F(0)) == P_EQUALS_ONE["total"] == 1
    refusal = rule_total_weight(weights)
    assert refusal is not None
    assert str(refusal.reason) == P_EQUALS_ONE["refusal_reason"]
    # And the recovery rem:peqone names IS admitted: lower one weight.
    smaller = tuple(value for _, value in P_EQUALS_ONE["smaller_admissible"])
    assert rule_total_weight(smaller) is None


# ---------------------------------------------------------------------------
#  PR4: the calculus
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_post_processing_by_a_column_stochastic_matrix_acts_on_both_sides() -> None:
    """Lemma ``lem:linear`` (i), with the frozen post-processed pair."""
    weights = {
        (row, column): value for row, column, value in POSTPROCESSING_CASE["matrix"]
    }
    targets = wpfss_target(WP3_PRESERVED, WP3_WEIGHTS)
    combined_target = add(
        scale(weights[("u0", "v0")], targets[0]),
        scale(weights[("u0", "v1")], targets[1]),
    )
    assert equal(combined_target, diagonal(list(POSTPROCESSING_CASE["pf_u0_diagonal"])))
    combined_physical = add(
        scale(weights[("u0", "v0")], WP3_PHYSICAL[0]),
        scale(weights[("u0", "v1")], WP3_PHYSICAL[1]),
    )
    assert equal(combined_physical, m(POSTPROCESSING_CASE["pm_u0"]))
    # AND THE ADJOINT REPRODUCES IT.
    mprime = mprime_family(WP3_ABOVE, WP3_WEIGHTS)
    assert equal(wp_adjoint(combined_target, 1, mprime), combined_physical)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_private_setting_enters_as_a_weight_inside_the_povm_elements() -> None:
    """Lemma ``lem:linear`` (ii) on PROBE22, and the target it builds."""
    joint = {
        outcome: (preserved, above) for outcome, preserved, above in PROBE22["joint"]
    }
    order = list(PROBE22_V)
    preserved = tuple(matrix([[joint[v][0]]]) for v in order)
    weights = tuple(value for _, value in PROBE22["weights"])
    built = wpfss_target(preserved, weights)
    for index, (outcome, expected_preserved, expected_flag) in enumerate(
        PROBE22_TARGET
    ):
        assert outcome == order[index]
        expected = diagonal([expected_preserved, *expected_flag])
        assert equal(built[index], expected)
    assert is_povm(list(built))
    assert dimension(built[0]) == PROBE22["target_dim"]
    # The certified weights are the frozen ones and p < 1.
    assert sum(weights, start=F(0)) == PROBE22["total_weight"]
    assert rule_total_weight(weights) is None


@pytest.mark.contract
@pytest.mark.oracle
def test_the_operator_form_transplant_fails_where_the_expectation_form_holds() -> None:
    """Remark ``rem:unsound``, with the frozen reachable state and projector."""
    joint = {
        outcome: (preserved, above) for outcome, preserved, above in PROBE22["joint"]
    }
    order = list(PROBE22_V)
    preserved = tuple(matrix([[joint[v][0]]]) for v in order)
    weights = tuple(value for _, value in PROBE22["weights"])
    built = wpfss_target(preserved, weights)
    dims = [1] + [1] * len(order)
    entry = probe_expectation_entry(
        [
            sector_blocks(built[index], dims)
            for index, v in enumerate(order)
            if v[1] == "t0"
        ],
        F(2, 3),
        label="sum_y F_(y,t0)",
        certified_against="Lambda-WP",
        mode=SourceMode.UNTRUSTED,
    )
    operator = dense(entry.operator)
    assert equal(operator, diagonal(list(PROBE22_SUM_T0)))
    # The preserved entry IS q_t0; the flag entries are NOT.
    assert operator[0][0].re == PROBE22_UNSOUND["target_identity_would_be"]
    assert any(operator[i][i].re != F(2, 3) for i in range(1, 5))
    # The PULL-BACK is q_t0 1_B exactly: the identity certificate.
    mprime = tuple(diagonal(list(dict(PROBE22_MPRIME)[v])) for v in order)
    pullback = wp_adjoint(operator, 1, mprime)
    assert equal(pullback, scale(F(2, 3), identity(3)))
    assert classify_certificate(pullback, Relation.EQ, F(2, 3)) is (
        CertificateKind.IDENTITY
    )
    # And the operator form fails on the frozen reachable flag state.
    reachable = tuple(PROBE22_UNSOUND["reachable_state"])
    witness = order.index(("y1", "t0"))
    lhs = operator[witness + 1][witness + 1].re * reachable[witness]
    assert lhs == PROBE22_UNSOUND["operator_form_lhs"]
    assert F(2, 3) * reachable[witness] == PROBE22_UNSOUND["operator_form_rhs"]
    assert lhs != PROBE22_UNSOUND["operator_form_rhs"]
    # While the EXPECTATION form holds on the same state.
    flag_expectation = sum(
        (operator[k + 1][k + 1].re * reachable[k] for k in range(len(order))),
        start=F(0),
    )
    assert flag_expectation == F(2, 3)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    "case", OBSTRUCTION_CASES, ids=lambda case: str(case["case_id"])
)
def test_both_obstruction_legs_decide_the_frozen_instances(case: object) -> None:
    """Lemma ``lem:obstructions``, each leg with a refusing and a passing case."""
    identifier = case["case_id"]  # type: ignore[index]
    if identifier == "obstruction-i-refuse":
        # The reverse relation F^FSS <= F^WP, refused by the norm leg.
        preserved = (matrix([[F(1, 2)]]), matrix([[F(1, 2)]]))
        weights = (F(1, 2), F(0))
        fss = fss_target(preserved)
        wp = wpfss_target(preserved, weights)
        refusal = rule_obstructions(list(fss), list(wp))
        assert refusal is not None
        assert str(refusal.reason) == case["refusal_reason"]  # type: ignore[index]
    elif identifier == "obstruction-i-pass":
        targets = wpfss_target(WP3_PRESERVED, WP3_WEIGHTS)
        assert rule_obstructions(list(WP3_PHYSICAL), list(targets)) is None
    else:
        physical = [diagonal([F(1), F(0)]), diagonal([F(0), F(1)])]
        target = [scale(F(1, 2), identity(2)), scale(F(1, 2), identity(2))]
        refusal = rule_obstructions(physical, target)
        assert refusal is not None
        assert str(refusal.reason) == case["refusal_reason"]  # type: ignore[index]


# ---------------------------------------------------------------------------
#  PR5: the branching rule and the flag PVM
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_flag_pvm_is_a_top_element() -> None:
    """Lemma ``lem:top``: EVERY POVM squashes to the flag PVM."""
    physical = [m(element) for _, element in TOP_ELEMENT["physical"]]
    target = [m(element) for _, element in TOP_ELEMENT["target"]]
    for index, element in enumerate(target):
        assert equal(mp_adjoint(element, physical), physical[index])
    for label, expected in TOP_ELEMENT["channel_action"]:
        state = {
            "|0><0|": diagonal([F(1), F(0)]),
            "|1><1|": diagonal([F(0), F(1)]),
            "|+><+|": matrix([[F(1, 2), F(1, 2)], [F(1, 2), F(1, 2)]]),
        }[label]
        distribution = tuple(expectation(element, state) for element in physical)
        assert distribution == tuple(expected)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_convex_mixture_with_a_known_weight() -> None:
    """Corollary ``cor:instances`` (i), and the branch-weight constraint."""
    weight = BRANCH_MIXTURE["q"]
    g_povm = [m(element) for _, element in BRANCH_MIXTURE["g_povm"]]
    r_povm = [m(element) for _, element in BRANCH_MIXTURE["r_povm"]]
    physical = [m(element) for _, element in BRANCH_MIXTURE["physical"]]
    target = [m(element) for _, element in BRANCH_MIXTURE["target"]]
    for index in range(2):
        rebuilt = add(scale(1 - weight, g_povm[index]), scale(weight, r_povm[index]))
        assert equal(rebuilt, physical[index])
    # Lambda+(F_v) = I_1+(Lambda_G+(G_v)) + I_2+(Lmp+(|v><v|)) = M_v.
    for index, element in enumerate(target):
        characterized = tuple(tuple(element[i][j] for j in range(2)) for i in range(2))
        flag = tuple(tuple(element[i + 2][j + 2] for j in range(2)) for i in range(2))
        rebuilt = add(
            scale(1 - weight, characterized),
            scale(weight, mp_adjoint(flag, r_povm)),
        )
        assert equal(rebuilt, physical[index])
    # The branch weights are multiples of the identity HERE, so the SCALAR
    # constraint is produced; the operator form is the one worth imposing.
    assert dict(BRANCH_MIXTURE["branch_weight_scalar_form"]) == {
        "Pi_1": 1 - weight,
        "Pi_flag": weight,
    }


@pytest.mark.contract
@pytest.mark.oracle
def test_flags_are_enough_on_the_zero_weight_block() -> None:
    """Corollary ``cor:flagsenough``: one target covers two different devices."""
    source = [m(element) for _, element in FLAGS_ENOUGH["source_povm"]]
    target = [m(element) for _, element in FLAGS_ENOUGH["target_povm"]]
    second = [m(element) for _, element in FLAGS_ENOUGH["second_source_povm"]]
    for family in (source, second):
        for index, element in enumerate(target):
            assert equal(flags_enough_adjoint(element, family, 2), family[index])
    # What it costs: the information in the B_0 block is gone.
    state = diagonal([F(1), F(0), F(0), F(0)])
    assert tuple(expectation(element, state) for element in source) == tuple(
        FLAGS_ENOUGH["distinguishability_before"]
    )
    assert tuple(expectation(element, state) for element in target) == tuple(
        FLAGS_ENOUGH["distinguishability_after"]
    )


# ---------------------------------------------------------------------------
#  PR8: the register-conditioned mixture
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_register_conditioned_mixture_with_a_non_projective_register() -> None:
    """Theorem ``thm:mixture`` on the frozen two-branch instance."""
    register = [m(MIXTURE_N_J0), m(MIXTURE_N_J1)]
    assert is_povm(register)
    # NON-PROJECTIVE: decision 6 removes the projectivity hypothesis.
    assert not equal(matmul(register[0], register[0]), register[0])
    branch = {
        (mode, outcome): m(element)
        for mode, outcome, element in MIXTURE_CASE["branch_povms"]
    }
    physical = [m(element) for _, element in MIXTURE_CASE["physical"]]
    target = [m(element) for _, element in MIXTURE_CASE["target"]]
    for index, outcome in enumerate(("v0", "v1")):
        blocks = [
            tuple(tuple(target[index][i][j] for j in range(2)) for i in range(2)),
            tuple(
                tuple(target[index][i + 2][j + 2] for j in range(2)) for i in range(2)
            ),
        ]
        adjoints = [
            blocks[0],
            mp_adjoint(blocks[1], [branch[("j1", "v0")], branch[("j1", "v1")]]),
        ]
        rebuilt = mixture_adjoint(target[index], [2, 2], adjoints, register)
        assert equal(rebuilt, physical[index]), outcome
    # The branch weights are transported AS OPERATORS, not as numbers.
    for label, expected in MIXTURE_CASE["branch_weight_pullbacks"]:
        mode = 0 if label == "Pi_j0" else 1
        assert equal(instrument_adjoint(identity(2), register[mode]), m(expected)), (
            label
        )
        assert not equal(m(expected), scale(m(expected)[0][0].re, identity(4)))
    assert MIXTURE_CASE["branch_weight_is_a_constraint"] is False


# ---------------------------------------------------------------------------
#  PR10: the obstruction, frozen with its numbers
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_event_bound_obstruction_data_are_admissible() -> None:
    """Proposition ``prop:obstruction``: the POVM, the event, the witness."""
    elements = {label: m(element) for label, element in PR_OBSTRUCTION.povm}
    assert is_povm(list(elements.values()))
    event = zeros(2)
    for label in PR_OBSTRUCTION.event:
        event = add(event, elements[label])
    assert trace(event).re == PR_OBSTRUCTION.event_sum_trace
    # p_* is the smaller root of x^2 - (trace)x + (det); the RATIONAL witness
    # 1/8 has an exact PSD certificate, and the proof uses only p_* > 0.
    shifted = subtract(event, scale(PR_OBSTRUCTION.rational_witness, identity(2)))
    assert is_positive_semidefinite(shifted)
    assert trace(shifted).re == PR_OBSTRUCTION.witness_shift_trace
    assert PR_OBSTRUCTION.rational_witness > 0
    # Two DISTINCT rank-one projections drive the contradiction.
    assert not equal(elements["1"], elements["2"])


@pytest.mark.contract
def test_the_flag_projector_is_the_basis_projector_of_the_declared_order() -> None:
    """The flag index of ``v`` IS its position in the declared order of ``V``."""
    for index in range(3):
        projector = flag_projector(3, index)
        assert projector[index][index].re == 1
        assert trace(projector).re == 1


@pytest.mark.contract
@pytest.mark.oracle
def test_the_exact_composition_holds_through_the_module_s_own_adjoints() -> None:
    """Proposition ``prop:chain`` (ii): ``Lambda^FSS+ = Lambda^WP+ o Lambda~+`` in CODE.

    The adjoint of a composition reverses the order, so the flag-noise adjoint
    is applied first and the WPFSS adjoint second; the result must equal the
    FSS adjoint on every carried operator and on the identity (unitality).
    """
    mprime = mprime_family(WP3_ABOVE, WP3_WEIGHTS)
    fss = fss_target(WP3_PRESERVED)
    pi_leq, pi_flag = transported_cutoff_projectors(1, 2)
    for x in (fss[0], fss[1], pi_leq, pi_flag, identity(3)):
        composed = wp_adjoint(noise_adjoint(x, 1, WP3_WEIGHTS), 1, mprime)
        assert equal(composed, wp_adjoint(x, 1, WP3_ABOVE))
