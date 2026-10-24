"""The uniform high-photon multiclick bound (registry RC8), against the registry.

Golden replay of ``BOUND_DATA_CASES`` and ``SLOT_RECORD`` (oracle entry
``O-RP-BOUND``, which the registry-0.2.0 amendment REFRAMES and does not
invalidate: every ``p_mc``, window, tail and residual gap it pins is
unchanged). RC8 is the registry's code for Theorems ``thm:multiclick-bound``
and ``thm:emitted-bound`` (tests/oracles/claim_codes.yaml); a registry version
is one of the frozen record, not of this module.

THE ZERO CASES ARE THE LOAD-BEARING HALF. ``BD-BB84-N1-ZERO`` emits ``p_mc = 0``
and ``BD-BB84-N2`` emits ``1/2`` on the SAME receiver at different cutoffs;
``BD-SINGULAR-N1`` and ``BD-COLLAPSE-SHARP`` emit zero for structural reasons;
``BD-PROBE-ON-N1-M2`` emits zero because the declared window was too short. An
implementation that raised a zero bound would look like an improvement and
would be unsafe, so every one of them is checked as an equality.

TWO REGISTRY-0.1.3 TABLES ARE RETIRED HERE, DELIBERATELY AND ONE BY ONE
=======================================================================
* ``BETA_ZERO_AND_C_SLACK`` is marked ``superseded``: its fourth field is
  "whether predicate (C) fires", and predicate (C) does not exist at registry
  0.2.0 or in this module. REPLACED BY ``COLLAPSE_SLACK_CASES`` and
  ``COLLAPSE_SLACK_COUNTS``, replayed in
  ``test_receiver_povm_branch_against_registry.py``, where the fourth field is
  "eq:collapsehyp holds" -- what the quantity actually decides.
* ``WINDOW_REQUIREMENT_CASES`` is marked ``reframed``: every verdict stands, but
  its fourth row quotes the registry-0.1.3 sentence in which the decoupled-probe
  receiver "fails (X), FAILS (C), and is served by branch 2". REPLACED BY
  ``PMC_BRANCH_CASES`` and ``PMC_X_CLAUSE_CASES``, replayed in the same new
  file; the window-requirement BEHAVIOUR is re-asserted below against
  ``PMC_BRANCH_CASES`` instead, so nothing is dropped.

``BD-PROBE-ON-N1-M3`` is marked ``reframed`` too -- its numbers and its branch
are unchanged, and only the ``derives_from`` prose named (C) -- so it is kept
and its uses are rewritten to name (X) and branch 2.
"""

from __future__ import annotations

from itertools import pairwise

import pytest
from receiver_povm_support import TOLERANCE
from registry_receiver_povm import (
    BOUND_DATA_CASES,
    PMC_BRANCH_CASES,
    SLOT_RECORD,
    is_superseded,
    rp_oracle,
)

from certiqs_key.receiver import (
    BoundData,
    Branch,
    StrengtheningSlot,
    bound_function,
    check_bound_data,
    check_tail_window,
    collapse_slack,
    emitted_weight,
    emitted_weights,
    multiclick_patterns,
    residual_gap,
    setting_bound,
    tail_value,
    underline_beta,
    window_minimum,
)
from certiqs_key.receiver.reasons import RefusalReason


def _data(case_id: str) -> BoundData:
    """Return the frozen bound-data tuple as the module's own record."""
    case = next(c for c in BOUND_DATA_CASES if c.case_id == case_id)
    return BoundData(
        port_count=case.port_count,
        gamma=float(case.gamma),
        betas=tuple(float(value) for value in case.betas),
        c=float(case.c),
        ds=tuple(float(value) for value in case.ds),
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_bound_datum_is_admissible_and_beta_is_reproduced() -> None:
    """Eq. eq:bounddata and Eq. eq:beta, with the convention 0^0 = 1."""
    assert rp_oracle("O-RP-BOUND").claims == ("RC8",)
    for case in BOUND_DATA_CASES:
        data = _data(case.case_id)
        check_bound_data(data)
        for photons, expected in case.beta_values:
            assert bound_function(data, photons) == pytest.approx(
                float(expected), abs=TOLERANCE.eps_2
            ), (case.case_id, photons)
        # Theorem thm:multiclick-bound's closing sentence: beta <= 1 everywhere.
        for photons in range(6):
            assert bound_function(data, photons) <= 1.0 + TOLERANCE.eps_2


@pytest.mark.contract
@pytest.mark.oracle
def test_p_mc_is_the_value_the_declared_branch_produces() -> None:
    """Definition def:pmc Eq. eq:pmcdef, both branches."""
    for case in BOUND_DATA_CASES:
        data = _data(case.case_id)
        cutoff = case.photon_cutoff
        if case.branch == "1":
            assert case.predicate == "X"
            record = setting_bound(
                case.case_id, data, cutoff, True, TOLERANCE, case.window
            )
            assert record.branch is Branch.COLLAPSE, case.case_id
            # Branch 1 EXACTLY where (X) holds, and the record reports the
            # branch rather than "which predicate" (`one_predicate_note`).
            assert record.predicate_x is True, case.case_id
        elif case.branch == "2":
            assert case.window is not None
            record = setting_bound(
                case.case_id, data, cutoff, False, TOLERANCE, case.window
            )
            assert record.branch is Branch.WINDOW_AND_TAIL, case.case_id
            assert record.predicate_x is False, case.case_id
            assert record.window_minimum == pytest.approx(
                float(case.window_minimum or 0), abs=TOLERANCE.eps_2
            ), case.case_id
            assert record.tail == pytest.approx(
                float(case.tail or 0), abs=TOLERANCE.eps_2
            ), case.case_id
            assert record.residual_gap == pytest.approx(
                float(case.residual_gap or 0), abs=TOLERANCE.eps_gap
            ), case.case_id
        else:
            # `lemma-only`: the case exists to freeze Lemma lem:windowtail (iv)'s
            # hypothesis, not a selector outcome. Definition def:pmc would take
            # branch 1 there through (X), and both routes give the same value.
            assert case.branch == "lemma-only"
            assert case.window is not None
            record = setting_bound(case.case_id, data, cutoff, True, TOLERANCE)
            assert record.branch is Branch.COLLAPSE
        assert record.weight == pytest.approx(float(case.p_mc), abs=TOLERANCE.eps_2), (
            case.case_id
        )
        # Proposition prop:slotvalid: p_mc in [0, 1].
        assert -TOLERANCE.eps_2 <= record.weight <= 1.0 + TOLERANCE.eps_2


@pytest.mark.contract
@pytest.mark.oracle
def test_the_window_tail_and_residual_gap_of_lemma_windowtail() -> None:
    """Eq. eq:windowtail and Eq. eq:resgap, with the closed form at m = N + 1."""
    for case in BOUND_DATA_CASES:
        if case.window is None:
            continue
        data = _data(case.case_id)
        cutoff, window = case.photon_cutoff, case.window
        assert window_minimum(data, cutoff, window) == pytest.approx(
            float(case.window_minimum or 0), abs=TOLERANCE.eps_2
        ), case.case_id
        assert tail_value(data, window) == pytest.approx(
            float(case.tail or 0), abs=TOLERANCE.eps_2
        ), case.case_id
        assert residual_gap(data, cutoff, window) == pytest.approx(
            float(case.residual_gap or 0), abs=TOLERANCE.eps_gap
        ), case.case_id
        if window == cutoff + 1:
            # Lemma lem:windowtail (ii): g_{N,N+1} = (K-1) gamma c^{N+1}.
            closed = (data.port_count - 1) * data.gamma * data.c ** (cutoff + 1)
            assert residual_gap(data, cutoff, window) == pytest.approx(
                closed, abs=TOLERANCE.eps_gap
            ), case.case_id


@pytest.mark.contract
def test_the_window_bound_is_monotone_in_the_window() -> None:
    """Lemma lem:windowtail (ii): underline-beta is non-decreasing in m."""
    for case_id in ("BD-PROBE-ON-N1-M2", "BD-COLLAPSE-FAILS-M3"):
        case = next(c for c in BOUND_DATA_CASES if c.case_id == case_id)
        data = _data(case_id)
        cutoff = case.photon_cutoff
        values = [
            underline_beta(data, cutoff, window)
            for window in range(cutoff + 1, cutoff + 6)
        ]
        for earlier, later in pairwise(values):
            assert later >= earlier - TOLERANCE.eps_2, case_id


@pytest.mark.contract
def test_the_superseded_bound_tables_carry_their_mark() -> None:
    """The two tables are superseded by a recorded mark, not silently absent.

    ``BETA_ZERO_AND_C_SLACK`` and ``WINDOW_REQUIREMENT_CASES`` are marked in
    ``SUPERSEDED_BY_0_2_0`` and are not asserted by this file; their
    replacements are replayed in
    ``tests/golden/test_receiver_povm_branch_against_registry.py``. This test
    fails if either mark is ever removed from the freeze without this file being
    revisited.
    """
    assert is_superseded("BETA_ZERO_AND_C_SLACK")
    assert is_superseded("WINDOW_REQUIREMENT_CASES")
    # O-RP-BOUND itself is marked `reframed`: its numbers stand and this file
    # keeps replaying them.
    assert is_superseded("O-RP-BOUND")


@pytest.mark.contract
def test_the_collapse_slack_is_a_diagnostic_and_no_predicate_consumes_it() -> None:
    """Remark rem:noslack: no computed predicate selects branch 1.

    The quantity survives as a diagnostic -- ``sigma = -beta(0) <= 0`` at every
    frozen case -- and nothing consults it. The per-case values are replayed
    against ``COLLAPSE_SLACK_CASES`` in the branch file; what is checked here is
    the identity and the sign, on every frozen tuple, and that
    :class:`SettingBound` carries no predicate-(C) field to consume it with.
    """
    for case in BOUND_DATA_CASES:
        data = _data(case.case_id)
        assert collapse_slack(data) == pytest.approx(
            -bound_function(data, 0), abs=TOLERANCE.eps_2
        ), case.case_id
        assert bound_function(data, 0) >= -TOLERANCE.eps_2, case.case_id
        assert collapse_slack(data) <= TOLERANCE.eps_2, case.case_id
    record = setting_bound("on", _data("BD-PROBE-ON-N1-M3"), 1, False, TOLERANCE, 3)
    assert record.predicate_x is False
    assert record.branch is Branch.WINDOW_AND_TAIL
    fields = {f.name for f in type(record).__dataclass_fields__.values()}
    assert "predicate_c" not in fields
    assert "predicate_c_slack" not in fields
    assert "selecting_predicate" not in fields


@pytest.mark.contract
@pytest.mark.oracle
def test_the_window_requirement_is_decidable_from_the_declaration() -> None:
    """Remark rem:windowdecidable, Requirement req:window-declaration, three outcomes.

    Read from ``PMC_BRANCH_CASES`` (which replaces the superseded
    ``WINDOW_REQUIREMENT_CASES``): a window is required at exactly the
    settings where (X) FAILS, which is the rule stated without the (C)
    clause the registry-0.1.3 table's fourth row quoted.
    """
    cutoff = 1
    for index, (_, predicate_x, _, _, required) in enumerate(PMC_BRANCH_CASES):
        setting = f"t{index}"
        assert required is (not predicate_x)
        # Missing where needed -> REFUSED; missing where not needed -> fine.
        refusal = check_tail_window(cutoff, (setting,), {setting: predicate_x}, {})
        if required:
            assert refusal is not None and refusal.reason is (
                RefusalReason.TAIL_WINDOW_MISSING
            )
        else:
            assert refusal is None
        # Supplied where not needed: UNUSED, NOT AN ERROR.
        assert (
            check_tail_window(cutoff, (setting,), {setting: predicate_x}, {setting: 3})
            is None
        )
        # m_t <= N: refused either way.
        too_small = check_tail_window(
            cutoff, (setting,), {setting: predicate_x}, {setting: cutoff}
        )
        assert too_small is not None
        assert too_small.reason is RefusalReason.TAIL_WINDOW_NOT_ABOVE_CUTOFF


@pytest.mark.contract
@pytest.mark.oracle
def test_the_version_one_strengthening_slot() -> None:
    """Definition def:slot and Proposition prop:slotvalid, PER SETTING.

    The slot carries one weight per entry AND SETTING (def:slot), so each
    entry below is written with its per-setting weights; the one-setting
    entries are the (O_i, p_i). The frozen SLOT_RECORD is not touched.
    """
    record = dict(SLOT_RECORD)
    assert record["entry_count"] == "1"
    slot = StrengtheningSlot(((multiclick_patterns(4), (("off", 0.5),)),))
    assert len(slot.entries) == 1
    assert slot.entries[0][0] == multiclick_patterns(4)
    assert slot.is_valid() is True
    assert slot.uniform_weights() == (0.5,)
    # The two spec/architecture.md 5.4 failure conditions.
    assert (
        StrengtheningSlot(((multiclick_patterns(4), (("off", -0.1),)),)).is_valid()
        is False
    )
    assert (
        StrengtheningSlot(
            (
                ((frozenset({0, 1}),), (("off", 0.7),)),
                ((frozenset({0, 1, 2}),), (("off", 0.7),)),
            )
        ).is_valid()
        is False
    )
    # PER SETTING (prop:slotvalid): p_i^(t) >= 0 and sum_i p_i^(t) <= 1 at
    # EVERY setting, and the uniform weight is the minimum over T. A slot
    # valid at one setting and not at the other is not valid.
    two = StrengtheningSlot(
        ((multiclick_patterns(4), (("off", 0.5), ("on", 0.75))),)
    )
    assert two.is_valid() is True
    assert two.uniform_weights() == (0.5,)
    assert (
        StrengtheningSlot(
            ((multiclick_patterns(4), (("off", 0.5), ("on", -0.25))),)
        ).is_valid()
        is False
    )
    # Entries indexed by different setting sets are no slot of def:slot.
    assert (
        StrengtheningSlot(
            (
                ((frozenset({0, 1}),), (("off", 0.25), ("on", 0.25))),
                ((frozenset({0, 2}),), (("off", 0.25),)),
            )
        ).is_valid()
        is False
    )


@pytest.mark.contract
def test_p_mc_is_the_minimum_over_the_probe_alphabet() -> None:
    """Definition def:pmc: p_mc = min over t in T of p_mc^{(t)}."""
    off_case = next(c for c in BOUND_DATA_CASES if c.case_id == "BD-PROBE-OFF-N1")
    on_case = next(c for c in BOUND_DATA_CASES if c.case_id == "BD-PROBE-ON-N1-M3")
    off = setting_bound("off", _data(off_case.case_id), 1, True, TOLERANCE)
    on = setting_bound(
        "on", _data(on_case.case_id), 1, False, TOLERANCE, on_case.window
    )
    # The two frozen per-setting values, on one receiver at two settings.
    assert off.weight == pytest.approx(float(off_case.p_mc), abs=TOLERANCE.eps_2)
    assert on.weight == pytest.approx(float(on_case.p_mc), abs=TOLERANCE.eps_2)
    # The emitted value is the MINIMUM over T, which here is the probe-off one:
    # the receiver is worse at the setting that is easier to bound.
    assert emitted_weight((off, on)) == pytest.approx(
        min(off.weight, on.weight), abs=TOLERANCE.eps_2
    )
    assert emitted_weight((off, on)) == pytest.approx(
        float(off_case.p_mc), abs=TOLERANCE.eps_2
    )
    assert off.weight < on.weight
    # THE PER-SETTING WEIGHTS ARE THE GUARANTEED CONTENT
    # (thm:emitted-bound eq:pmcsetting), read off the same records and not
    # re-evaluated, and the uniform weight is their minimum (eq:pmcstatement).
    assert emitted_weights((off, on)) == (("off", off.weight), ("on", on.weight))
    assert emitted_weight((off, on)) == min(
        weight for _, weight in emitted_weights((off, on))
    )
