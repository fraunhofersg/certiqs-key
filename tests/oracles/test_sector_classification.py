"""Sector classification and its consequences (C7, C10).

The registry records the *verdicts* -- key-active, constraint-active,
state-blind, removable -- as hand-checked golden data, with the check written
out in each toy's ``derivation``. Deciding those predicates from a declaration
is Definition ``def:classes`` and Theorem ``thm:removal``, i.e. solver-side work
under ``src/certiqs_key/meat/``, and no checker for them lives in this tree.

What the tests below pin is what the CONTRACT PROVES about a verdict, which is
the part an implementation can get wrong in a way that changes a key rate:

* key-inert  =>  ``f_{chat,s} == 0`` for every input        (Prop. prop:exact-cancellation)
* key-active =>  ``f_{chat,s} < 0`` for some input          (Def. def:classes (a))
* removable  =>  deleting the sector moves ``h_low`` by 0   (Thm. thm:removal)
* dropping a constraint-active sector  =>  ``h_low`` strictly rises
                                                            (Prop. prop:retention)
* averaging sectors                    =>  ``h_low`` strictly rises
                                                        (Prop. prop:no-averaging)
"""

from __future__ import annotations

import pytest
from registry import ALPHA_GRID, oracle
from toy_declarations import (
    ALL_TOYS,
    TOY1_RETENTION,
    TOY2_AVERAGED,
    TOY2_DETERMINISTIC,
    TOY5_CONSTRAINED,
    TOY6_REMOVABLE,
)
from toy_evaluation import branch_values, minimum_over_sector_weights, objective_at


@pytest.mark.contract
def test_every_sector_carries_exactly_one_class() -> None:
    """Definition def:classes (a)/(b): the two classes partition the sector set."""
    for toy in ALL_TOYS:
        assert set(toy.sector_classes) == set(toy.sector_index_set)
        for sector, klass in toy.sector_classes.items():
            assert klass in {"key-active", "constraint-active"}, (toy.toy_id, sector)
        assert set(toy.state_blind) == set(toy.sector_index_set)
        assert set(toy.removable) == set(toy.sector_index_set)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_constraint_active_sectors_have_identically_vanishing_deficits(
    alpha: float,
) -> None:
    """Proposition prop:exact-cancellation: key-inert sectors contribute zero for EVERY input."""
    for toy in (TOY1_RETENTION, TOY2_DETERMINISTIC, TOY5_CONSTRAINED, TOY6_REMOVABLE):
        sectors = toy.sector_index_set
        for weight in (0.0, 0.3, 0.6, 1.0):
            rest = (1.0 - weight) / max(len(sectors) - 1, 1)
            point = {s: (weight if s == sectors[0] else rest) for s in sectors}
            deficits = branch_values(toy, alpha, point)["chat0"].deficits
            for sector, klass in toy.sector_classes.items():
                if klass == "constraint-active":
                    assert deficits[sector] == pytest.approx(0.0, abs=1e-12), (
                        toy.toy_id,
                        sector,
                    )


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_key_active_sectors_have_a_strictly_negative_deficit_somewhere(
    alpha: float,
) -> None:
    """Definition def:classes (a): a key-active sector carries a real deficit."""
    for toy in (TOY1_RETENTION, TOY2_AVERAGED, TOY5_CONSTRAINED, TOY6_REMOVABLE):
        sectors = toy.sector_index_set
        point = {s: (1.0 if i == 0 else 0.0) for i, s in enumerate(sectors)}
        deficits = branch_values(toy, alpha, point)["chat0"].deficits
        for sector, klass in toy.sector_classes.items():
            if klass == "key-active":
                assert deficits[sector] < -1e-9, (toy.toy_id, sector)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_dropping_a_constraint_active_sector_is_unsound(alpha: float) -> None:
    """Proposition prop:retention (C10b), pinned by O-HLOW-RETENTION."""
    assert oracle("O-HLOW-RETENTION").claims == ("C7", "C10")
    assert TOY1_RETENTION.sector_classes["s1"] == "constraint-active"
    assert TOY1_RETENTION.removable["s1"] is False

    retained, _ = minimum_over_sector_weights(TOY1_RETENTION, alpha, steps=400)
    dropped = objective_at(TOY1_RETENTION, alpha, {"s0": 1.0, "s1": 0.0})
    assert dropped - retained == pytest.approx(1.0)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_averaging_sectors_is_unsound(alpha: float) -> None:
    """Proposition prop:no-averaging (C10c), pinned by O-HLOW-NO-AVERAGING."""
    original, _ = minimum_over_sector_weights(TOY2_DETERMINISTIC, alpha, steps=50)
    averaged = objective_at(TOY2_AVERAGED, alpha, {"sbar": 1.0})
    assert averaged - original == pytest.approx(1.0)
    # The averaged declaration collapses two sectors into one: that is the move
    # the contract forbids, and here it is worth a whole bit.
    assert len(TOY2_AVERAGED.sector_index_set) == 1
    assert len(TOY2_DETERMINISTIC.sector_index_set) == 2


@pytest.mark.contract
@pytest.mark.oracle
def test_removability_verdicts_are_the_hand_checked_ones() -> None:
    """Theorem thm:removal (RM1)-(RM3), as checked in the toys' derivations."""
    # TOY-6's s2 duplicates the key-inert s1: (RM1) matches the response,
    # (RM2) holds because (chat0, s1) is key-inert, (RM3) is 0 = 0. The
    # relation is symmetric, so s1 is removable against s2 on the same three
    # checks -- s1's verdict was corrected False -> True; see the
    # derivation in TOY6_REMOVABLE.derivation. Theorem thm:removal is a
    # ONE-sector statement with targets from SecSet \ {s*}: each of s1, s2 may
    # be deleted alone, and the PAIR may not (that is prop:retention, and the
    # criteria refuse it because s0 is key-active and fails (RM2)).
    assert TOY6_REMOVABLE.removable == {"s0": False, "s1": True, "s2": True}
    # TOY-1 has no removable sector: (RM1) would need (1, 0) = (1/2, 1/2) or
    # (1/2, 1/2) = (1, 0), and neither holds.
    assert TOY1_RETENTION.removable == {"s0": False, "s1": False}
    # A key-active sector is never removable here: (RM2) requires the TARGET
    # pairs to be key-inert, and s0 is not.
    for toy in ALL_TOYS:
        for sector, klass in toy.sector_classes.items():
            if klass == "key-active":
                assert toy.removable[sector] is False, (toy.toy_id, sector)


@pytest.mark.contract
def test_state_blindness_is_not_sufficient_for_removability() -> None:
    """Remark rem:classes: (RM1)-(RM3) need a matching key-inert target too.

    Every sector of every toy here is one-dimensional or carries a scalar POVM
    response, hence state-blind; almost none is removable. Recording the two
    predicates separately is what keeps an implementation from conflating them.
    """
    state_blind_but_not_removable = [
        (toy.toy_id, s)
        for toy in ALL_TOYS
        for s in toy.sector_index_set
        if toy.state_blind[s] and not toy.removable[s]
    ]
    assert state_blind_but_not_removable
    for toy in ALL_TOYS:
        for sector in toy.sector_index_set:
            if toy.removable[sector]:
                assert toy.state_blind[sector], (toy.toy_id, sector)
