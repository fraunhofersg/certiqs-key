"""Dark counts as a classical outcome channel (registry RC11), vs the registry.

Golden replay of ``DARK_CASES``, ``RMIN_TRAP_CASES``,
``DARK_IMPROVEMENT_CASES`` and ``DARK_COMPOSITION_N2`` (oracle entry
``O-RP-DARK``).

TWO OF THOSE TABLES ARE MARKED AT REGISTRY 0.2.0 AND ARE KEPT DELIBERATELY.
``DARK_CASES`` is ``incomplete`` -- every matrix and every ``r_min`` in it is
still correct, and what it has no field for is the ``rbar``/``delta_dc``/route
triple the artifact now emits -- and ``DARK_IMPROVEMENT_CASES`` is ``reframed``:
all three of its values are correct and are reproduced exactly by
``DS-GENERATED-K2`` and ``DS-GENERATED-K3``, because on the GENERATED route
delta_dc = 0 and r_min <= 1, so rbar = r_min and Eq. eq:darkpmcslack IS
Eq. eq:darkpmc (Remark ``rem:d2slack`` (e)). What is superseded is the FORM, not
a number, so this file keeps replaying both and ``DARK_SLACK_CASES`` -- their
replacement -- is replayed in
``test_receiver_povm_darkslack_against_registry.py``.

THE ``r_min`` TRAP IS WHAT THIS GROUP IS BUILT AROUND. Eq. ``eq:rmin``
minimizes over EVERY non-multiclick column, THE NO-CLICK COLUMN INCLUDED, and
Remark ``rem:rmintrap``'s Eq. ``eq:rmintrapnum`` is the number the shortcut gets
wrong by more than four orders of magnitude -- which is ``TRAP-K4-P100``. The
single-click-only shortcut is computed HERE, in the test, from the emitted
matrix, and is shown to differ; it is not implemented in the module, because the
contract calls it invalid.
"""

from __future__ import annotations

from fractions import Fraction as F

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE, assert_matches, mat_value
from registry_receiver_povm import (
    DARK_CASES,
    DARK_COMPOSITION_N2,
    DARK_IMPROVEMENT_CASES,
    INSTRUMENT_CASES,
    POVM_BLOCK_CASES,
    RMIN_TRAP_CASES,
    is_superseded,
    rp_oracle,
)

from certiqs_key.receiver import (
    DarkCountChannel,
    DarkCountRoute,
    GramFamily,
    check_dark_channel,
    check_dark_count_source,
    coarse_elements,
    compose_blocks,
    element_block,
    improved_bound,
    minimum_multiclick_mass,
    multiclick_mass,
    port_grams,
    product_form,
    raw_alphabet,
    unconditioned_family,
)
from certiqs_key.receiver.reasons import RefusalReason


def _declared(case_id: str) -> DarkCountChannel:
    """Return a frozen channel as a DECLARED matrix, column by column."""
    case = next(c for c in DARK_CASES if c.case_id == case_id)
    columns = {
        frozenset(column): {frozenset(row): float(value) for row, value in entries}
        for column, entries in case.columns
    }
    return DarkCountChannel(case.port_count, DarkCountRoute.DECLARED_MATRIX, columns)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_product_form_reproduces_every_frozen_column() -> None:
    """Eq. eq:darkR at K = 2 and K = 3, in full."""
    assert rp_oracle("O-RP-DARK").claims == ("RC11",)
    for case in DARK_CASES:
        if case.p_dc is None:
            continue
        channel = product_form([float(value) for value in case.p_dc])
        assert channel.route is DarkCountRoute.PER_PORT_PRODUCT_FORM
        for column, entries in case.columns:
            key = frozenset(column)
            for row, value in entries:
                assert channel.entry(frozenset(row), key) == pytest.approx(
                    float(value), abs=TOLERANCE.eps_4
                ), (case.case_id, column, row)
            # (D1): the column sums to one, on the FROZEN entries and on all.
            total = sum(channel.entry(pattern, key) for pattern in channel.patterns())
            assert total == pytest.approx(1.0, abs=TOLERANCE.eps_4), (
                case.case_id,
                column,
            )
        assert check_dark_channel(channel, TOLERANCE) is None, case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_the_multiclick_masses_and_r_min_are_reproduced() -> None:
    """Eq. eq:rmin, with the no-click column BINDING."""
    for case in DARK_CASES:
        channel = (
            product_form([float(value) for value in case.p_dc])
            if case.p_dc is not None
            else _declared(case.case_id)
        )
        for column, expected in case.mc_mass:
            assert multiclick_mass(channel, frozenset(column)) == pytest.approx(
                float(expected), abs=TOLERANCE.eps_4
            ), (case.case_id, column)
        if case.r_min_without_noclick is None:
            continue  # the refused channel emits no r_min
        assert minimum_multiclick_mass(channel) == pytest.approx(
            float(case.r_min), abs=TOLERANCE.eps_4
        ), case.case_id
        # THE TRAP, computed here and not in the module: the single-click-only
        # minimum is LARGER, and the no-click column is where the minimum sits.
        single_click_only = min(
            multiclick_mass(channel, frozenset({port}))
            for port in range(case.port_count)
        )
        assert single_click_only == pytest.approx(
            float(case.r_min_without_noclick), abs=TOLERANCE.eps_4
        ), case.case_id
        assert single_click_only > float(case.r_min)
        assert multiclick_mass(channel, frozenset()) == pytest.approx(
            float(case.r_min), abs=TOLERANCE.eps_4
        ), case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_eq_rmintrapnum_at_k_equals_four() -> None:
    """Remark rem:rmintrap's own numbers -- the test the contract demands."""
    for case_id, ports, probability, no_click, single, r_min, wrong in RMIN_TRAP_CASES:
        channel = product_form([float(probability)] * ports)
        assert multiclick_mass(channel, frozenset()) == pytest.approx(
            float(no_click), abs=1e-12
        ), case_id
        assert multiclick_mass(channel, frozenset({0})) == pytest.approx(
            float(single), abs=1e-12
        ), case_id
        assert minimum_multiclick_mass(channel) == pytest.approx(
            float(r_min), abs=1e-12
        ), case_id
        assert float(wrong) > float(r_min)


@pytest.mark.contract
@pytest.mark.oracle
def test_multiclick_absorption_holds_and_a_non_monotone_channel_is_refused() -> None:
    """Theorem thm:dark-counts (iii) and Definition def:darkadm (D2)."""
    for case in DARK_CASES:
        channel = (
            product_form([float(value) for value in case.p_dc])
            if case.p_dc is not None
            else _declared(case.case_id)
        )
        refusal = check_dark_channel(channel, TOLERANCE)
        if case.monotone:
            assert refusal is None, case.case_id
            for column in channel.multiclick_patterns():
                assert multiclick_mass(channel, column) == pytest.approx(
                    1.0, abs=TOLERANCE.eps_4
                ), (case.case_id, column)
        else:
            assert refusal is not None, case.case_id
            assert refusal.reason is RefusalReason.DARK_CONDITION_D2_FAILED
            # The consequence is visible: half the multiclick weight leaks out.
            leaking = multiclick_mass(channel, frozenset({0, 1}))
            assert leaking == pytest.approx(0.5, abs=TOLERANCE.eps_4)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_bound_improves_by_r_min() -> None:
    """Theorem thm:dark-counts (iv), Eq. eq:darkpmc, and r_min (1 - p_mc) >= 0."""
    for case_id, r_min, weight, expected in DARK_IMPROVEMENT_CASES:
        improved = improved_bound(float(r_min), float(weight))
        assert improved == pytest.approx(float(expected), abs=TOLERANCE.eps_2), case_id
        assert improved >= float(weight)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_dark_composition_preserves_the_povm_on_a_block() -> None:
    """Theorem thm:dark-counts (ii) on I-BS's two-photon block with DARK-K2."""
    instrument = next(c for c in INSTRUMENT_CASES if c.case_id == "I-BS")
    gamma_inp = mat_value(instrument.gamma_inp)
    labels = tuple(label for label, _ in instrument.port_map)
    family = unconditioned_family(
        GramFamily(labels, port_grams(gamma_inp, [m for _, m in instrument.port_map]))
    )
    blocks = {
        pattern: element_block(family, pattern, 2)
        for pattern in family_patterns(family.port_count)
    }
    channel = product_form([0.1, 0.2])
    composed = compose_blocks(channel, blocks)
    for pattern, expected in DARK_COMPOSITION_N2:
        value = float(composed[frozenset(pattern)][0, 0].real)
        assert value == pytest.approx(float(expected), abs=TOLERANCE.eps_4), pattern
    # STILL A POVM on the block.
    total = sum(composed.values())
    assert_matches(total, np.eye(1), TOLERANCE.eps_4, "composed completeness")
    # And the BARE blocks are the frozen PB-BS-n2 ones, unchanged by R.
    bare = coarse_elements(family, 2)
    frozen = next(c for c in POVM_BLOCK_CASES if c.case_id == "PB-BS-n2")
    assert_matches(bare["mc"], mat_value(frozen.multiclick), TOLERANCE.eps_4, "bare mc")


def family_patterns(port_count: int) -> tuple[frozenset[int], ...]:
    """Return ``2^[K]`` as the composition needs it."""
    return raw_alphabet(port_count)


@pytest.mark.contract
def test_a_declared_channel_beside_non_zero_dark_counts_is_refused() -> None:
    """Req. req:dark-route-exclusive makes the two routes exclusive.

    The behaviour is the registry-0.1.3 one, and the REASON STRING is the
    contract's: row 1 of the refusal rules spells
    `dark_count_channel_declared_twice`.
    """
    declared = _declared("DARK-K2")
    # Both supplied and the per-port probabilities are non-zero: REFUSED.
    refusal = check_dark_count_source(declared, [F(1, 10), F(1, 5)])
    assert refusal is not None
    assert refusal.reason is RefusalReason.DARK_COUNT_CHANNEL_DECLARED_TWICE
    assert str(refusal.reason) == "dark_count_channel_declared_twice"
    assert "dark_count_channel" in refusal.detail
    assert "detector_layer" in refusal.detail
    # One source only, either way, is admitted.
    assert check_dark_count_source(declared, [0, 0]) is None
    assert check_dark_count_source(None, [F(1, 10), F(1, 5)]) is None


@pytest.mark.contract
def test_the_marked_dark_tables_stay_asserted() -> None:
    """The mark is `incomplete`/`reframed`, so the values stay asserted here."""
    assert is_superseded("DARK_CASES")
    assert is_superseded("DARK_IMPROVEMENT_CASES")
