"""The exact-window validation matrix (registry RC8/RC9), and Def. def:tolmap (iv).

Golden replay of groups RP-V and RP-W: ``EXACT_WINDOW_VALIDATION_CASES``,
``REFUSAL_CASES_0_3_0``, ``TOLMAP_IV_PRECEDENCE_CASES``, ``TOLMAP_IV_BAND``,
``TOLMAP_IV_BAND_FIXTURE``, ``TOLMAP_IV_BAND_CLOSED_AT``,
``TOLMAP_IV_BAND_EMPTY_AT_EQUAL_EPS``, ``TOLMAP_IV_BAND_COST``,
``TOLMAP_IV_DERIVATION`` and ``TOLMAP_IV_NO_BEHAVIOUR_CHANGE`` (oracle entries
``O-RP-EXACT-WINDOW-VALIDATION`` and ``O-RP-TOLMAP-IV``), first frozen at
registry 0.3.0 (a registry version is one of
tests/oracles/registry_receiver_povm.py, not of this module).

RP-V -- THE THREE NEW REFUSALS, AND WHAT DECIDES THEM
=====================================================
The refusal rules gained three rows at registry 0.3.0 and lost none
(``interface.yaml`` ``refusals.table``, ``new_at``). Every validation below is
a comparison of declared data against a declared domain or a combinatorial
predicate on the declaration -- Definition ``def:tolmap``'s closing enumeration lists
``m*_t > N`` and ``m*_t <= m_t`` under kind (a) and the conditional presence of
``eps_eig`` and ``eps_6`` under kind (b) -- so **NO NEW THRESHOLD DECIDES ANY OF
THEM**, and none is consulted.

The asymmetry between the two range conditions is load-bearing: ``m*_t > N``
holds ALWAYS, and ``m*_t <= m_t`` only WHERE PREDICATE (X) FAILS. Where (X)
holds no ``m_t`` is required at all and branch 1 takes ``beta(m*_t + 1)``, so a
depth above a supplied-but-unused ``m_t`` is ADMITTED
(``XW-ADMIT-DEPTH-EXCEEDS-UNUSED-TAIL-WINDOW``); where (X) fails the two windows
must compose and it is REFUSED (``XW-REFUSE-DEPTH-EXCEEDS-TAIL-WINDOW``). The
boundary ``m*_t = m_t`` is admitted on both readings, and its middle minimum is
then over the empty index set.

RP-W -- ITEM (iv) DECIDES c ALONE, AND THE BAND IS REFUSED
==========================================================
Registry 0.2.0 left open which of items (iv) and (v) decides the admissibility
of ``c``, and the case is reachable: item (v) admits a route-(ii) ``Gamma`` at
``eps_1`` while item (iv) decides the derived ``c`` at ``eps_2``, so at the
ORDINARY declaration ``eps_1 > eps_2`` the band ``c in [-eps_1, -eps_2)`` is
ADMITTED BY ONE AND REFUSED BY THE OTHER. **Item (iv) wins, and the band is
REFUSED** (Definition ``def:tolmap`` (iv); Remark ``rem:bound-data-band``).

THE REASON STRING IS THIS MODULE'S, AND THE CONTRACT DECLINES TO FIX ONE.
Requirement ``req:tolerance-tests`` states that a failure of item (iv) IS a
refusal under ``fail_closed``, leaves the reason string THE IMPLEMENTER'S TO
NAME, and its lead-in says the contract DELIBERATELY ADDS NONE
(``interface.yaml`` ``refusals.named_without_a_spelling``). So
``REF-TOLMAP-IV-C-REFUSED-NO-SPELLING`` is frozen with ``reason = None`` and
this module's own ``bound_data_not_admissible`` is asserted below AS THIS
MODULE'S SPELLING, not as contract text.

The registry-0.3.0 ruling CHANGES NO BEHAVIOUR for an implementation that
already refused the band, and the test named for that checks exactly it, end
to end, on a request whose derived ``c`` lands in the band's interior.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from receiver_povm_support import (
    TOLERANCE,
    bb84_channel_only_request,
)
from registry_receiver_povm import (
    EXACT_WINDOW_VALIDATION_CASES,
    REFUSAL_CASES_0_3_0,
    TOLERANCE_FIXTURE_0_3_0,
    TOLMAP_IV_BAND,
    TOLMAP_IV_BAND_CLOSED_AT,
    TOLMAP_IV_BAND_COST,
    TOLMAP_IV_BAND_EMPTY_AT_EQUAL_EPS,
    TOLMAP_IV_BAND_FIXTURE,
    TOLMAP_IV_DERIVATION,
    TOLMAP_IV_NO_BEHAVIOUR_CHANGE,
    TOLMAP_IV_PRECEDENCE_CASES,
    rp_oracle,
)

from certiqs_key.receiver import (
    BoundData,
    GramFamily,
    check_bound_data_admissible,
    check_exact_window,
    compile_element_graph,
    construct_receiver,
    port_grams,
    restrict_to_inputs,
    tolerances_from_declaration,
)
from certiqs_key.receiver.numerics import lambda_max
from certiqs_key.receiver.reasons import Refusal, RefusalReason

_SETTING = "t"


def _validate(case: object) -> Refusal | None:
    """Return the first refusal ``validate_request`` would reach, in its order.

    THE ORDER IS THE CONTRACT'S AND NOT A CONVENIENCE: the declared tolerances
    are read first, because these numbers DECIDE the other validations
    (Definition ``def:tolmap``), so a declaration missing a conditionally
    required one refuses before any range is compared. Each frozen case has
    exactly one defect, so the order is checkable without being load-bearing.
    """
    declared = {
        key: value
        for key, value in TOLERANCE_FIXTURE_0_3_0.items()
        if not (key == "eps_eig" and not case.eps_eig_declared)  # type: ignore[attr-defined]
        and not (key == "eps_6" and not case.eps_6_declared)  # type: ignore[attr-defined]
    }
    depths = {} if case.exact_depth is None else {_SETTING: case.exact_depth}  # type: ignore[attr-defined]
    outcome = tolerances_from_declaration(declared, bool(depths))
    if isinstance(outcome, Refusal):
        return outcome
    windows = {} if case.tail_window is None else {_SETTING: case.tail_window}  # type: ignore[attr-defined]
    return check_exact_window(
        case.photon_cutoff,  # type: ignore[attr-defined]
        (_SETTING,),
        {_SETTING: case.predicate_x},  # type: ignore[attr-defined]
        windows,
        depths,
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_exact_window_validation_matrix_is_the_frozen_one() -> None:
    """`inputs.exact_window` and Req. req:exact-window-declaration.

    Ten declarations: the opt-out, four admits including both boundaries, and
    five refusals across the three conditions the two verbatim strings cover.
    """
    assert rp_oracle("O-RP-EXACT-WINDOW-VALIDATION").claims == ("RC8", "RC9")
    assert len(EXACT_WINDOW_VALIDATION_CASES) == 10
    for case in EXACT_WINDOW_VALIDATION_CASES:
        outcome = _validate(case)
        if case.admitted:
            assert outcome is None, case.case_id
            assert case.refusal_reason is None, case.case_id
        else:
            assert outcome is not None, case.case_id
            assert str(outcome.reason) == case.refusal_reason, case.case_id
            assert outcome.detail.strip(), case.case_id
            # A refusal is a RECORD and never an exception.
            assert not isinstance(outcome, BaseException)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_depth_range_condition_is_asymmetric_in_predicate_x() -> None:
    """Def. def:pmcex: m*_t > N always, m*_t <= m_t ONLY where (X) fails.

    The same declaration -- ``N = 1``, ``m_t = 3``, ``m* = 5`` -- is ADMITTED
    where (X) holds and REFUSED where it fails, and nothing but the predicate
    differs. Where (X) holds the window is "UNUSED, NOT AN ERROR"
    (Req. req:window-declaration) and branch 1 has its own remainder; where it
    fails the two windows must compose into ``N < n <= m_t``.
    """
    admitted = check_exact_window(
        1, (_SETTING,), {_SETTING: True}, {_SETTING: 3}, {_SETTING: 5}
    )
    assert admitted is None
    refused = check_exact_window(
        1, (_SETTING,), {_SETTING: False}, {_SETTING: 3}, {_SETTING: 5}
    )
    assert refused is not None
    assert refused.reason is RefusalReason.EXACT_WINDOW_DEPTH_OUTSIDE_DECLARED_RANGE
    # THE BOUNDARY m*_t = m_t IS ADMITTED on both readings.
    for holds in (True, False):
        assert (
            check_exact_window(
                1, (_SETTING,), {_SETTING: holds}, {_SETTING: 3}, {_SETTING: 3}
            )
            is None
        )
    # m*_t > N is STRICT and applies whatever the predicate says.
    for holds in (True, False):
        at_cutoff = check_exact_window(
            1, (_SETTING,), {_SETTING: holds}, {_SETTING: 3}, {_SETTING: 1}
        )
        assert at_cutoff is not None
        assert at_cutoff.reason is (
            RefusalReason.EXACT_WINDOW_DEPTH_OUTSIDE_DECLARED_RANGE
        )
    # AND A SETTING CARRYING NO DEPTH IS NOT AN ERROR: that is the opt-out.
    assert check_exact_window(1, (_SETTING,), {_SETTING: True}, {}, {}) is None


@pytest.mark.contract
@pytest.mark.oracle
def test_the_three_new_refusal_rows_are_produced_with_their_reasons() -> None:
    """Refusal rows 6-8, and the fourth registry-0.3.0 row, which stays unspelled.

    ``REFUSAL_CASES_0_3_0`` has FOUR rows: three carry a verbatim string and the
    fourth -- Def. def:tolmap (iv)'s -- carries ``reason = None``, because the
    contract DELIBERATELY ADDS NONE (Req. req:tolerance-tests).
    """
    rows = {case.case_id: case for case in REFUSAL_CASES_0_3_0}
    assert len(rows) == 4
    verbatim = [case for case in REFUSAL_CASES_0_3_0 if case.reason_is_verbatim]
    assert len(verbatim) == 3
    assert all(case.emits_artifact is False for case in REFUSAL_CASES_0_3_0)
    # The three spelled ones, each produced by the check that states it.
    missing = tolerances_from_declaration(
        {k: v for k, v in TOLERANCE_FIXTURE_0_3_0.items() if k != "eps_eig"}, True
    )
    assert isinstance(missing, Refusal)
    assert str(missing.reason) == rows["REF-EXACT-WINDOW-MISSING-TOLERANCE"].reason
    out_of_range = check_exact_window(
        1, (_SETTING,), {_SETTING: True}, {}, {_SETTING: 1}
    )
    assert out_of_range is not None
    assert (
        str(out_of_range.reason) == rows["REF-EXACT-WINDOW-DEPTH-OUT-OF-RANGE"].reason
    )
    # r_6's reason is replayed in the residual-6 file; here only the spelling.
    assert rows["REF-R6-ABOVE-TOLERANCE"].reason == str(
        RefusalReason.WINDOW_EIGENVALUE_CONSISTENCY_RESIDUAL_ABOVE_TOLERANCE
    )
    # THE FOURTH ROW CARRIES NO REASON, and this module's own key is not
    # promoted into the contract's vocabulary by being used for it.
    unspelled = rows["REF-TOLMAP-IV-C-REFUSED-NO-SPELLING"]
    assert unspelled.reason is None
    assert unspelled.reason_is_verbatim is False


@pytest.mark.contract
@pytest.mark.oracle
def test_def_tolmap_iv_decides_c_alone_and_the_band_is_refused() -> None:
    """Def. def:tolmap (iv): the band c in [-eps_1, -eps_2) is REFUSED.

    Five computed values bracketing the band -- its interior, its closed left
    endpoint, its excluded right endpoint, a value below it where both readings
    agree, and the lossless ``c = 0`` the widening exists for. Item (iv)'s
    verdict is asserted; the LOSING reading's is frozen beside it and is what
    the module must NOT do.
    """
    assert rp_oracle("O-RP-TOLMAP-IV").claims == ("RC9",)
    assert len(TOLMAP_IV_PRECEDENCE_CASES) == 5
    low, high = TOLMAP_IV_BAND
    assert (low, high) == (
        -TOLMAP_IV_BAND_FIXTURE["eps_1"],
        -TOLMAP_IV_BAND_FIXTURE["eps_2"],
    )
    assert TOLMAP_IV_BAND_CLOSED_AT == (True, False)
    for case in TOLMAP_IV_PRECEDENCE_CASES:
        data = BoundData(
            port_count=4,
            gamma=1.0,
            betas=(1.0, 1.0, 1.0, 1.0),
            c=float(case.c),
            ds=(0.5, 0.5, 0.5, 0.5),
        )
        outcome = check_bound_data_admissible(data, float(case.eps_2))
        assert (outcome is None) is case.admitted, case.case_id
        assert case.admitted is case.item_iv_admits, case.case_id
        if outcome is not None:
            # THIS MODULE'S OWN SPELLING, and the contract states none here.
            assert outcome.reason is RefusalReason.BOUND_DATA_NOT_ADMISSIBLE
            assert case.refusal_reason is None, case.case_id
            assert "def:tolmap (iv)" in outcome.detail, case.case_id
        # THE BAND MEMBERSHIP the two readings disagree about.
        in_band = low <= case.c < high
        assert in_band is case.in_band, case.case_id
        if case.in_band:
            assert case.losing_reading_admits is True, case.case_id
            assert case.item_iv_admits is False, case.case_id
        # AND THE LOSING READING IS NOT WHAT THE MODULE DOES: it would admit
        # at eps_1 on the band, and the module refuses there.
        if case.losing_reading_admits and not case.item_iv_admits:
            losing = check_bound_data_admissible(data, float(case.eps_1))
            assert losing is None, case.case_id
            assert outcome is not None, case.case_id
    # AT eps_1 = eps_2 THE BAND IS EMPTY and the question cannot arise, which
    # is the main fixture's own configuration.
    eps_1, eps_2, interval, empty = TOLMAP_IV_BAND_EMPTY_AT_EQUAL_EPS
    assert eps_1 == eps_2
    assert empty is True
    assert interval[0] == interval[1]
    assert TOLERANCE.eps_1 == TOLERANCE.eps_2
    # THE DERIVATION AND ITS COST are frozen; the load-bearing step is (2).
    steps = {row[0]: row[1] for row in TOLMAP_IV_DERIVATION}
    assert "(2)" in steps
    assert "the failure is a refusal" in steps
    cost = dict(TOLMAP_IV_BAND_COST)
    assert cost["the factor between them, (eps_1 / eps_2)^2"] == F(100)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_band_is_refused_end_to_end_and_nothing_else_changes() -> None:
    """Registry 0.3.0: no behaviour changes for an implementation that refused it.

    A route-(ii) declaration whose ``Gamma`` item (v) ADMITS at ``eps_1`` and
    whose derived ``c = -1/200`` lands in the band's interior. The module
    refuses with no artifact, which is what ``fail_closed`` requires under
    EITHER reading of the precedence -- and is why the amendment costs this
    implementation nothing.

    ``TOLMAP_IV_NO_BEHAVIOUR_CHANGE`` lists seven things the ruling does not
    change; every one of them is ``True`` and none is touched here.
    """
    for _what, unchanged in TOLMAP_IV_NO_BEHAVIOUR_CHANGE:
        assert unchanged is True
    seed = bb84_channel_only_request(photon_cutoff=1)
    assert seed.element_graph is not None
    compiled = compile_element_graph(seed.element_graph, len(seed.mode_space))
    # lmax(A_Sigma) = 1 + 1/200 gives c = -1/200, the band's interior.
    scaled = np.asarray(np.sqrt(1.005) * compiled, dtype=np.complex128)
    declared = dict(TOLERANCE_FIXTURE_0_3_0) | {
        "eps_1": TOLMAP_IV_BAND_FIXTURE["eps_1"],
        "eps_2": TOLMAP_IV_BAND_FIXTURE["eps_2"],
    }
    request = replace(
        seed,
        element_graph=None,
        instrument_matrix=scaled,
        numerical_tolerances=declared,
    )
    # ITEM (v) ADMITS: lmax(Gamma^dagger Gamma) = 1.005 <= 1 + eps_1 = 1.01.
    assert lambda_max(scaled.conj().T @ scaled) <= 1.0 + float(declared["eps_1"])
    # THE DERIVED c IS IN THE BAND.
    gamma_inp = restrict_to_inputs(scaled, seed.input_modes.subsystem_order())
    rows = [modes for _, modes in seed.port_map.entries]
    family = GramFamily(seed.port_map.labels, port_grams(gamma_inp, rows))
    a_sigma = sum(family.matrices[1:], family.matrices[0])
    derived_c = 1.0 - lambda_max(a_sigma)
    low, high = TOLMAP_IV_BAND
    assert float(low) <= derived_c < float(high)
    # AND THE MODULE REFUSES, with no artifact and without raising.
    emission = construct_receiver(request)
    assert emission.artifact is None
    assert emission.refusal is not None
    assert emission.refusal.reason is RefusalReason.BOUND_DATA_NOT_ADMISSIBLE
    assert "def:tolmap (iv)" in emission.refusal.detail
    # THE SAME DECLARATION AT eps_1 = eps_2 EMPTIES THE BAND, and then item (v)
    # itself refuses the instrument BEFORE item (iv) is reached -- which is item
    # (v)'s own closing observation, that a declarer wanting one slack
    # regardless of route "declares eps_1 = eps_2, WHICH ALSO EMPTIES
    # Eq. eq:tolmapband". The declaration is refused either way; what the two
    # readings disagree about is the BAND, which is empty there.
    equal = replace(request, numerical_tolerances=dict(TOLERANCE_FIXTURE_0_3_0))
    same = construct_receiver(equal)
    assert same.artifact is None
    assert same.refusal is not None
    assert same.refusal.reason is RefusalReason.INSTRUMENT_MATRIX_NOT_CONTRACTION
    # AND AN UNSCALED DECLARATION IS ADMITTED, so the refusal is about the
    # datum and not about the route.
    clean = construct_receiver(
        replace(seed, element_graph=None, instrument_matrix=compiled)
    )
    assert clean.refusal is None
    assert clean.artifact is not None
