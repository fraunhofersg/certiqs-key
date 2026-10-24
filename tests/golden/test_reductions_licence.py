"""Theorem ``thm:licence`` and Eq. ``eq:crosspairing``, against the FROZEN registry.

THE LICENCE IS A THEOREM WITH ONE HYPOTHESIS, AND THE HYPOTHESIS IS RECOMPUTED.
Every case below discharges Eq. ``eq:certificate`` by exact Loewner comparison
on the pull-back rather than trusting the caller's claim, which is what Section
2.5's "NO LICENCE IS EMITTED WITHOUT ITS CERTIFICATE" requires of an
implementation.

The cross-pairing case is frozen AT ITS TIGHT END, where the licensed entry
paired with the other route's channel pulls back to a NEGATIVE operator and
excludes a state that IS reachable under that channel. That is why ``route:
both`` is refused structurally rather than warned about.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from registry_reductions import (
    BLK_GT_V0,
    BLK_GT_V1,
    COMPOSITE_ATTACK_CASE,
    CONSUMER_PIN_0_2_0,
    CONSUMER_PIN_0_3_0,
    CONSUMER_PIN_1_0_0,
    LICENCE_CASES,
    MP_V0,
    MP_V1,
    SOURCE_MODES,
    SUPERSESSIONS,
    TIGHT,
    TOL_ENTRY_FLAG,
    TOL_ENTRY_PROBE_T0,
    WP3_FFSS_V0,
)

from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    diagonal,
    direct_sum,
    equal,
    identity,
    is_positive_semidefinite,
    matmul,
    matrix,
    scale,
    subtract,
    trace,
)
from certiqs_key.reductions.channels import split_blocks
from certiqs_key.reductions.constraints import (
    admissible_set_expression,
    certificate_holds,
    classify_certificate,
    issue_licence,
    theta_typing,
)
from certiqs_key.reductions.reasons import CertificateKind, Relation, SourceMode
from certiqs_key.reductions.validation import (
    resolve_route,
    rule_constraint_channel,
    rule_licence_presence,
    rule_route,
)
from certiqs_key.reductions.wpfss.construction import (
    FSS_INSTANCE_LOCATOR,
    flat_sectors,
    fss_instance_entry,
    fss_target,
    mprime_family,
    transported_cutoff_projectors,
    wp_adjoint,
    wpfss_target,
)

F = Fraction


def m(frozen: object) -> Matrix:
    """Convert a frozen registry matrix into the module's representation."""
    rows = frozen  # type: ignore[assignment]
    return matrix([[Cx(entry[0], entry[1]) for entry in row] for row in rows])  # type: ignore[index,union-attr]


def expectation(operator: Matrix, state: Matrix) -> Fraction:
    """Return ``tr[operator state]`` as an exact rational."""
    value = trace(matmul(operator, state))
    assert value.is_real, value
    return value.re


WP3_PRESERVED = (matrix([[F(2, 3)]]), matrix([[F(1, 3)]]))
WP3_ABOVE = (m(BLK_GT_V0), m(BLK_GT_V1))


WP3_SECTORS = flat_sectors([1], ["v0", "v1"])


#: The entry's discharging claim, as the flat builder supplies it.
DISCHARGED_BY = {"O^ = F^FSS_v0 - (1/4) Pi_flag": FSS_INSTANCE_LOCATOR}


def _fss_entry(mode: SourceMode) -> object:
    return fss_instance_entry(
        _blocks(m(WP3_FFSS_V0)),
        WP3_SECTORS,
        preserved_dim=1,
        alphabet_size=2,
        weight=F(1, 4),
        label="O^ = F^FSS_v0 - (1/4) Pi_flag",
        certified_against="Lambda-FSS",
        mode=mode,
    )


def _blocks(operator: Matrix) -> tuple[Matrix, ...]:
    """Return the operator as the sector-block list of ``WP3_SECTORS``."""
    return tuple(split_blocks(operator, list(WP3_SECTORS.dimensions)))


def _dense(entry: object) -> Matrix:
    """Return the ``d_Q x d_Q`` array an entry's sector-block list MEANS.

    An entry's ``hat O_k`` is carried as its block list like every other
    operator on ``Q`` (spec/architecture.md 2.8-2.9); a pull-back through
    :func:`wp_adjoint` and a frozen dense
    comparison are whole-space computations, so THE TEST forms the direct sum.
    """
    return direct_sum(list(entry.operator))  # type: ignore[attr-defined]


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", LICENCE_CASES, ids=lambda case: str(case.case_id))
def test_every_frozen_licence_case_is_typed_and_discharged(case: object) -> None:
    """Definition ``def:licensed`` and Theorem ``thm:licence`` (i)-(ii).

    REWRITTEN AT 0.2.0. ALL THREE FROZEN LICENCE CASES ARE MARKED
    ``superseded``: ``LICENCE_TRUSTED`` and ``LICENCE_UNTRUSTED`` (kind:
    constant, replacement ``TOL_ENTRY_FLAG``) and ``LICENCE_PROBE_IDENTITY``
    (kind: constant and reading, replacements ``TOL_ENTRY_PROBE_T0``,
    ``TOL_ENTRY_PROBE_T1``, ``TOL2-branchprobe-pass``,
    ``TOL2-branchprobe-fail-exact-povm``).

    WHAT IS SUPERSEDED IS THE SCOPE OF THE CONSTANT AND NOT THE TYPING.
    Definition ``def:licensed`` is untouched by the amendment, so every
    assertion below about ``theta_typing``, the source mode and the licence's
    presence STANDS AT EVERY ``eps_op`` and is asserted unchanged. The
    ``(relation, constant)`` pair is now asserted AS THE ``eps_op = 0`` PAIR,
    with the ``eps_op > 0`` one named beside it: at a positive tolerance the
    flag-sector entry carries ``-eta_o`` (``cor:tolentries`` (i)) and the
    probe-expectation entry is replaced by a PAIR at ``q_t -+ delta_t``
    (``cor:tolentries`` (ii)). Nothing here replays them, because there is no
    tolerance to declare.
    """
    mode = SourceMode(case.source_mode)  # type: ignore[attr-defined]
    assert case.source_mode in SOURCE_MODES  # type: ignore[attr-defined]
    typing = theta_typing(mode, case.constant)  # type: ignore[attr-defined]
    if mode is SourceMode.TRUSTED:
        assert "tau_A" in typing
    else:
        assert "real number" in typing
    assert case.licence_present is True  # type: ignore[attr-defined]
    # AT eps_op = 0 everything this module emits is `>=` with c = 0 or `=` with
    # c = q_t. THE SCOPE IS THE POINT: Section 2.3 calls emitting either of
    # these at eps_op > 0 UNSAFE.
    assert (case.relation, case.constant) in {  # type: ignore[attr-defined]
        (">=", F(0)),
        ("=", F(2, 3)),
    }
    mark = next(
        record
        for record in SUPERSESSIONS
        if record.case_id == case.case_id  # type: ignore[attr-defined]
    )
    assert mark.still_valid_at_zero_tolerance
    if case.relation == ">=":  # type: ignore[attr-defined]
        # cor:tolentries (i): the flag-sector entry moves from 0 to -eta_o.
        assert mark.replacement == ("TOL_ENTRY_FLAG",)
        assert TOL_ENTRY_FLAG.at_zero == ((">=", F(0)),)
        assert TOL_ENTRY_FLAG.at_positive == ((">=", F(-1, 125)),)
    else:
        # cor:tolentries (ii): the single equality becomes a two-sided PAIR,
        # and the pair's feasible set CONTAINS the equality's.
        assert "TOL_ENTRY_PROBE_T0" in mark.replacement
        assert TOL_ENTRY_PROBE_T0.at_zero == (("=", F(2, 3)),)
        assert len(TOL_ENTRY_PROBE_T0.at_positive) == 2
        lower = dict(TOL_ENTRY_PROBE_T0.at_positive)[">="]
        upper = dict(TOL_ENTRY_PROBE_T0.at_positive)["<="]
        assert lower < F(2, 3) < upper


@pytest.mark.contract
@pytest.mark.oracle
def test_the_default_licensed_entry_is_certified_in_both_source_modes() -> None:
    """``thm:licence`` (i) and (ii): the SAME entry and the SAME constant."""
    for mode in (SourceMode.TRUSTED, SourceMode.UNTRUSTED):
        entry = _fss_entry(mode)
        pullback = wp_adjoint(_dense(entry), 1, WP3_ABOVE)
        assert certificate_holds(pullback, Relation.GE, F(0))
        assert classify_certificate(pullback, Relation.GE, F(0)) is (
            CertificateKind.POSITIVITY
        )
        licence = issue_licence(  # type: ignore[list-item]
            [entry], mode, "receiver-povm@0.1.3", discharged_by=DISCHARGED_BY
        )
        assert licence is not None
        assert licence.source_mode is mode
        # The record NAMES these things and asserts none of them of a device.
        assert "thm:licence" in licence.theorem
        assert len(licence.hypothesis_per_entry) == 1
        assert "eq:certificate" in licence.hypothesis_per_entry[0]
        # req:licence-record: per entry, the claim that discharges it and the
        # supplier artefact that claim reads, by version.
        (discharge,) = licence.discharge_per_entry
        assert discharge.claim == FSS_INSTANCE_LOCATOR
        assert discharge.supplier_fact is not None
        assert "A-RECV" in discharge.supplier_fact
        assert discharge.supplier_version == "receiver-povm@0.1.3"
        assert licence.discharging_receiver_fact is not None
        assert "A-RECV" in licence.discharging_receiver_fact
        assert licence.receiver_spec_version == "receiver-povm@0.1.3"
        assert "A_CList" in licence.admissible_set


@pytest.mark.contract
@pytest.mark.oracle
def test_the_licence_technique_names_the_accepted_consumer_pin() -> None:
    """``sec:openitems`` at 1.0.0: the consumer pin is the accepted ``meat-core`` 1.0.0.

    ``technique`` is item (e) of Remark ``rem:notlicensed`` -- a licence is "not
    automatically compatible with a postselection-based reduction", so the
    artifact "NAMES THE TECHNIQUE THE LICENCE WAS ISSUED FOR" -- and the
    technique it names is the squashed round model of Definition
    ``def:roundmodel``, quoted throughout from ``meat-core`` 1.0.0.
    ``sec:openitems``: "THE CONSUMER PIN IS THE ACCEPTED 1.0.0 ... ``meat-core``
    1.0.0 SUPERSEDES 0.5.0."

    IT IS ONE OF THE TWO HARD-CODED VERSION STRINGS EACH AMENDMENT MOVES IN THE
    PACKAGE. The other, ``mathematical_spec_version``, is asserted against the
    spec-version constant in four places. BOTH SUPERSEDED PINS ARE ASSERTED
    ABSENT, so a regression to either leaves the suite red.
    """
    entry = _fss_entry(SourceMode.UNTRUSTED)
    licence = issue_licence(  # type: ignore[list-item]
        [entry],
        SourceMode.UNTRUSTED,
        "receiver-povm@0.1.3",
        discharged_by=DISCHARGED_BY,
    )
    assert licence is not None
    assert CONSUMER_PIN_1_0_0 in licence.technique
    assert CONSUMER_PIN_0_3_0 not in licence.technique
    assert CONSUMER_PIN_0_2_0 not in licence.technique
    assert licence.as_machine_record()["technique"] == licence.technique


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_admissible_sets_differ_by_the_output_system_they_name() -> None:
    """Eqs. ``eq:attset`` and ``eq:attsetun``, quoted in the consumer's spelling.

    The untrusted form LIFTS the constraint operator to the larger supplied
    system, ``1_A (x) O^_k (x) 1_E''``, "because in this mode ``A_j`` is an
    OUTPUT of the attack channel".
    """
    trusted = admissible_set_expression(
        [_fss_entry(SourceMode.TRUSTED)],
        SourceMode.TRUSTED,  # type: ignore[list-item]
    )
    untrusted = admissible_set_expression(
        [_fss_entry(SourceMode.UNTRUSTED)],
        SourceMode.UNTRUSTED,  # type: ignore[list-item]
    )
    assert "A_CList(E', Q E'')" in trusted
    assert "eq:attset)" in trusted
    assert "A_CList(E', A Q E'')" in untrusted
    assert "1_A (x)" in untrusted
    assert "eq:attsetun" in untrusted


@pytest.mark.contract
@pytest.mark.oracle
def test_a_composite_attack_lands_in_the_set_as_an_operator_inequality() -> None:
    """``thm:licence`` (i) on the frozen measure-and-prepare attack.

    ``A^sq+(O^ (x) 1) = sum_e tr[(Lambda^FSS+(O^) (x) 1) rho_e] |e><e|``, which is
    ``diag(5/8, 0)`` -- NOT a multiple of ``1_E'``. The conclusion is a genuine
    OPERATOR inequality, which is what Eq. ``eq:attset`` asks for and what a
    scalar-only implementation would get wrong.
    """
    entry = _fss_entry(SourceMode.TRUSTED)
    pullback = wp_adjoint(_dense(entry), 1, WP3_ABOVE)
    branches = {
        "e0": _embed_above(m(MP_V0)),
        "e1": _embed_above(m(MP_V1)),
    }
    result = diagonal(
        [expectation(pullback, branches["e0"]), expectation(pullback, branches["e1"])]
    )
    assert equal(result, m(COMPOSITE_ATTACK_CASE["result"]))
    assert is_positive_semidefinite(
        subtract(result, scale(COMPOSITE_ATTACK_CASE["constant"], identity(2)))
    )
    assert COMPOSITE_ATTACK_CASE["in_set"] is True
    # NOT a multiple of the identity.
    assert not equal(result, scale(result[0][0].re, identity(2)))
    # Cross-check against the TARGET side at E' = C with rho = |psi_0><psi_0|:
    # Lambda^FSS(|psi_0><psi_0|) has flag distribution (7/8, 1/8).
    squashed = diagonal([F(0), F(7, 8), F(1, 8)])
    assert expectation(_dense(entry), squashed) == F(5, 8)


def _embed_above(block: Matrix) -> Matrix:
    """Embed a 2x2 above-cutoff operator into the 3-dimensional source space."""
    out = [[Cx(F(0), F(0)) for _ in range(3)] for _ in range(3)]
    for i in range(2):
        for j in range(2):
            out[i + 1][j + 1] = block[i][j]
    return tuple(tuple(row) for row in out)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_cross_channel_pairing_is_negative_at_the_tight_end() -> None:
    """Eq. ``eq:crosspairing`` on the frozen TIGHT instance, and why `both` fails.

    Certified WITH EQUALITY at ``o`` -- ``blk M^{>N}_o = p_o 1`` -- which is
    exactly the configuration Remark ``rem:tworoutes`` names. The entry's
    certificate holds tightly on ITS OWN channel and FAILS on the other one, and
    the state it then excludes is REACHABLE under that other channel.
    """
    preserved = tuple(matrix([[value]]) for _, value in TIGHT["preserved"])
    above = tuple(matrix([[value]]) for _, value in TIGHT["above_cutoff"])
    weights = tuple(value for _, value in TIGHT["weights"])
    assert sum(weights, start=F(0)) == TIGHT["total_weight"]
    mprime = mprime_family(above, weights)
    for index, (_, expected) in enumerate(TIGHT["mprime"]):
        assert equal(mprime[index], matrix([[expected]]))
    fss = fss_target(preserved)
    _, pi_flag = transported_cutoff_projectors(1, 2)
    ohat = subtract(fss[0], scale(weights[0], pi_flag))
    assert (ohat[1][1].re, ohat[2][2].re) == tuple(TIGHT["ohat_flag_block"])
    # Its OWN channel: Lambda^FSS, whose flag term uses blk M^{>N}_v.
    own = wp_adjoint(ohat, 1, above)
    assert own[1][1].re == TIGHT["pairing_with_own_channel"] == F(0)
    assert is_positive_semidefinite(own)
    assert certificate_holds(own, Relation.GE, F(0))
    # The OTHER route's channel: Lambda^WP, whose flag term uses M'_v.
    other = wp_adjoint(ohat, 1, mprime)
    assert other[1][1].re == TIGHT["pairing_with_other_channel"] == F(-1, 5)
    assert not is_positive_semidefinite(other)
    assert not certificate_holds(other, Relation.GE, F(0))
    # And it excludes a state REACHABLE under Lambda^WP.
    reachable = diagonal([F(0), *TIGHT["reachable_flag_state"]])
    assert expectation(ohat, reachable) < 0
    # The two ways to reach the failure, with their two reasons.
    assert set(TIGHT["refusal_reasons"]) == {
        "route_not_single_valued",
        "constraint_channel_mismatch",
    }


@pytest.mark.contract
@pytest.mark.oracle
def test_route_both_is_refused_and_the_two_values_resolve() -> None:
    """Section 2.1's ``route`` row: EXACTLY ONE VALUE PER REQUEST."""
    assert rule_route("encoded") is None
    assert rule_route("licensed") is None
    refusal = rule_route("both")
    assert refusal is not None
    assert str(refusal.reason) == "route_not_single_valued"
    assert resolve_route("both") is None
    assert resolve_route("encoded") is not None


@pytest.mark.contract
@pytest.mark.oracle
def test_an_entry_certified_against_another_channel_is_refused() -> None:
    """Section 4.14: certified against THE CHANNEL WITNESS OF ITS OWN LINK."""
    entry = _fss_entry(SourceMode.UNTRUSTED)
    assert rule_constraint_channel([entry], "Lambda-FSS") is None  # type: ignore[list-item]
    refusal = rule_constraint_channel([entry], "Lambda-WP")  # type: ignore[list-item]
    assert refusal is not None
    assert str(refusal.reason) == "constraint_channel_mismatch"


@pytest.mark.contract
@pytest.mark.oracle
def test_the_licence_presence_rule_is_an_iff_with_two_reasons() -> None:
    """Section 2.3 and Definition ``def:link``: present EXACTLY WHEN non-empty."""
    entry = _fss_entry(SourceMode.TRUSTED)
    assert rule_licence_presence([entry], licence_present=True) is None  # type: ignore[list-item]
    assert rule_licence_presence([], licence_present=False) is None
    missing = rule_licence_presence([entry], licence_present=False)  # type: ignore[list-item]
    assert missing is not None
    assert str(missing.reason) == "licence_missing"
    spurious = rule_licence_presence([], licence_present=True)
    assert spurious is not None
    assert str(spurious.reason) == "licence_without_constraints"
    # And a licence is never built for an empty list in the first place.
    assert (
        issue_licence(
            [], SourceMode.TRUSTED, "receiver-povm@0.1.3", discharged_by={}
        )
        is None
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_encoded_route_needs_no_licence_and_the_licensed_route_does() -> None:
    """The whole difference between the two routes, on one instance."""
    encoded = wpfss_target(WP3_PRESERVED, (F(1, 4), F(1, 8)))
    _, pi_flag = transported_cutoff_projectors(1, 2)
    # Under F^WP the device fact is an operator inequality ON Q: it needs no
    # constraint, no licence and no attestation.
    assert is_positive_semidefinite(subtract(encoded[0], scale(F(1, 4), pi_flag)))
    assert rule_licence_presence([], licence_present=False) is None
    # Under F^FSS the same fact is only a pull-back constraint.
    licensed = fss_target(WP3_PRESERVED)
    ohat = subtract(licensed[0], scale(F(1, 4), pi_flag))
    assert not is_positive_semidefinite(ohat)
    assert is_positive_semidefinite(wp_adjoint(ohat, 1, WP3_ABOVE))
    entry = _fss_entry(SourceMode.TRUSTED)
    assert rule_licence_presence([entry], licence_present=False) is not None  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# req:licence-record: the record is emitted only when every entry has its
# certificate and what discharges it
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_no_licence_where_an_entry_has_no_discharging_claim() -> None:
    """An entry missing from ``discharged_by`` gets no licence at all.

    ``issue_licence`` returns ``None``, and the presence row then refuses the
    non-empty list ``licence_missing``: no record is emitted that names
    nothing for an entry.
    """
    entry = _fss_entry(SourceMode.TRUSTED)
    assert (
        issue_licence(  # type: ignore[list-item]
            [entry], SourceMode.TRUSTED, "receiver-povm@0.1.3", discharged_by={}
        )
        is None
    )
    refusal = rule_licence_presence([entry], licence_present=False)  # type: ignore[list-item]
    assert refusal is not None
    assert str(refusal.reason) == "licence_missing"


@pytest.mark.contract
def test_a_licence_with_unequal_per_entry_lists_is_refused() -> None:
    """One certificate and one discharge per entry, or the record is malformed."""
    from certiqs_key.reductions.constraints import AttackSetLicence, EntryDischarge
    from certiqs_key.reductions.errors import MalformedInputError

    with pytest.raises(MalformedInputError, match="req:licence-record"):
        AttackSetLicence(
            theorem="Theorem thm:licence (PR11)",
            hypothesis_per_entry=("eq:certificate for O", "eq:certificate for P"),
            discharge_per_entry=(EntryDischarge(entry="O", claim="cor:entries (i)"),),
            discharging_receiver_fact=None,
            receiver_spec_version=None,
            source_mode=SourceMode.TRUSTED,
            admissible_set="A_CList(...)",
        )


@pytest.mark.contract
def test_a_supplier_fact_without_its_version_is_refused() -> None:
    """A discharge that reads a supplier fact names its artefact by version."""
    from certiqs_key.reductions.constraints import RECEIVER_FACT, EntryDischarge
    from certiqs_key.reductions.errors import MalformedInputError

    with pytest.raises(MalformedInputError, match="by version"):
        EntryDischarge(
            entry="O", claim="wpfss/cor:fssinstance", supplier_fact=RECEIVER_FACT
        )
    with pytest.raises(MalformedInputError, match="by version"):
        EntryDischarge(
            entry="O", claim="wpfss/cor:fssinstance", supplier_version="receiver@0.9.0"
        )
    both = EntryDischarge(
        entry="O",
        claim="wpfss/cor:fssinstance",
        supplier_fact=RECEIVER_FACT,
        supplier_version="receiver@0.9.0",
    )
    assert both.as_machine_record()["supplier_version"] == "receiver@0.9.0"
