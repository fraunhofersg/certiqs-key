"""C7 and C10: the sector classification, and the operations that are refused.

contract Remark ``rem:classes`` allows exactly two structure-changing
operations, and this module tests both of them plus the absence of the others:

    (i)  evaluate the objective over key-active sectors only -- an identity;
    (ii) delete a sector whose (RM1)-(RM3) hypotheses are CHECKED;
    (iii) nothing else.

Dropping a constraint-active sector and merging sectors are the two unsound
moves, and the way they are prevented is that no function performs them. The
last test in this file states that as a property of the module surface.
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
from certiqs_key.meat_core.declaration.sectors import (  # noqa: E402
    RemovalTarget,
    RemovalWitness,
    SectorClass,
    build_sector_report,
    classify_sector,
    delete_sectors,
    find_removal_witness,
    is_state_blind,
    verify_removal_witness,
)
from certiqs_key.meat_core.errors import SectorOperationError  # noqa: E402
from certiqs_key.meat_core.objective.branch import (  # noqa: E402
    evaluate_branches,
    generate_maps,
)

ALPHAS = (1.05, 1.5, 1.9)


def declaration_of(toy_id: str) -> ProtocolDeclaration:
    """Return the validated declaration of a frozen toy."""
    return declaration_from_bundle(build_bundle(toy(toy_id)))


@pytest.mark.contract
def test_the_classification_matches_the_frozen_toys() -> None:
    """Definition def:classes (a)-(c), against every toy's hand-checked verdict."""
    for declared in admitted(ALL_TOYS):
        declaration = declaration_of(declared.toy_id)
        maps = generate_maps(declaration)
        for sector in declaration.sector_index_set:
            assert (
                str(classify_sector(maps, sector)) == declared.sector_classes[sector]
            ), (declared.toy_id, sector)
            assert (
                is_state_blind(declaration, sector) is declared.state_blind[sector]
            ), (declared.toy_id, sector)


@pytest.mark.contract
@pytest.mark.parametrize("alpha", ALPHAS)
def test_restricting_the_sum_to_key_active_sectors_is_an_identity(
    alpha: float,
) -> None:
    """Prop. prop:exact-cancellation / Definition def:keyactive: EQUAL, not a bound.

    The implementation sums the deficits over ALL sectors precisely because the
    restriction is an identity; this checks the identity rather than trusting
    the predicate that would justify the shortcut.
    """
    for toy_id in ("TOY-1", "TOY-2", "TOY-5", "TOY-6"):
        declaration = declaration_of(toy_id)
        maps = generate_maps(declaration)
        sectors = declaration.sector_index_set
        for share in (0.0, 0.3, 0.7, 1.0):
            rest = (1.0 - share) / max(len(sectors) - 1, 1)
            omega = {
                s: np.array([[share if s == sectors[0] else rest]], dtype=np.complex128)
                for s in sectors
            }
            values = evaluate_branches(maps, omega, alpha)["chat0"]
            active = maps.key_active_sectors("chat0")
            restricted = values.p + sum(values.deficits[s] for s in active)
            assert restricted == pytest.approx(values.k, abs=1e-12)
            for sector in sectors:
                if sector not in active:
                    assert values.deficits[sector] == pytest.approx(0.0, abs=1e-12)


@pytest.mark.contract
def test_the_removable_sector_of_toy6_carries_a_verified_witness() -> None:
    """Theorem thm:removal on TOY-6's s2, the registry's removable sector."""
    maps = generate_maps(declaration_of("TOY-6"))
    report = build_sector_report(maps)
    record = report.record("s2")
    assert record.removable is True
    assert record.removal_witness is not None
    assert [t.sector for t in record.removal_witness.targets] == ["s1"]
    verify_removal_witness(maps, record.removal_witness)
    assert record.sector_class is SectorClass.CONSTRAINT_ACTIVE


@pytest.mark.contract
def test_a_key_active_sector_is_never_removable() -> None:
    """(RM2) requires the TARGET pairs to be key-inert, so s0 is no target."""
    for toy_id in ("TOY-1", "TOY-5", "TOY-6", "TOY-2-AVG"):
        declaration = declaration_of(toy_id)
        maps = generate_maps(declaration)
        for sector in declaration.sector_index_set:
            if classify_sector(maps, sector) is SectorClass.KEY_ACTIVE:
                witness, note = find_removal_witness(maps, sector)
                assert witness is None, (toy_id, sector)
                assert note


@pytest.mark.contract
def test_the_retention_sector_of_toy1_has_no_witness() -> None:
    """Proposition prop:retention: TOY-1's s1 may not be dropped.

    (RM1) would need ``(1, 0)`` to be a convex combination of responses of
    key-inert target sectors, and TOY-1 has none other than s1 itself.
    """
    maps = generate_maps(declaration_of("TOY-1"))
    report = build_sector_report(maps)
    for sector in ("s0", "s1"):
        assert report.record(sector).removable is False
    assert report.record("s1").sector_class is SectorClass.CONSTRAINT_ACTIVE


@pytest.mark.contract
def test_a_witness_that_fails_a_criterion_is_refused() -> None:
    """Every removal must be justified by the CHECKED hypotheses."""
    maps = generate_maps(declaration_of("TOY-6"))
    one = np.ones((1, 1), dtype=np.complex128)

    # (RM2): s0 is key-active, so it is not an admissible target.
    with pytest.raises(SectorOperationError, match="RM2"):
        verify_removal_witness(
            maps,
            RemovalWitness("s2", (RemovalTarget("s0", one, 1.0),)),
        )
    # (RM1): the weights must sum to one, and the response must match.
    with pytest.raises(SectorOperationError, match="sum_i mu_i = 1"):
        verify_removal_witness(
            maps,
            RemovalWitness("s2", (RemovalTarget("s1", one, 0.5),)),
        )
    with pytest.raises(SectorOperationError, match="mu_i >= 0"):
        verify_removal_witness(
            maps,
            RemovalWitness(
                "s2",
                (RemovalTarget("s1", one, 2.0), RemovalTarget("s1", one, -1.0)),
            ),
        )
    # A target must be another sector.
    with pytest.raises(SectorOperationError, match="other than the removed one"):
        verify_removal_witness(
            maps,
            RemovalWitness("s2", (RemovalTarget("s2", one, 1.0),)),
        )
    # And there must be one at all.
    with pytest.raises(SectorOperationError, match="at least one target"):
        verify_removal_witness(maps, RemovalWitness("s2", ()))


@pytest.mark.contract
def test_deleting_a_witnessed_sector_needs_the_witness_to_survive() -> None:
    """The theorem moves the removed weight ONTO its targets."""
    maps = generate_maps(declaration_of("TOY-6"))
    one = np.ones((1, 1), dtype=np.complex128)
    both = [
        RemovalWitness("s2", (RemovalTarget("s1", one, 1.0),)),
        RemovalWitness("s1", (RemovalTarget("s2", one, 1.0),)),
    ]
    with pytest.raises(SectorOperationError, match="itself being deleted"):
        delete_sectors(maps, both)
    reduced = delete_sectors(maps, both[:1])
    assert reduced.sector_index_set == ("s0", "s1")
    assert set(reduced.bob_povm["v0"]) == {"s0", "s1"}
    assert set(reduced.constraint_list[0].operator_blocks) == {"s0", "s1"}


@pytest.mark.contract
def test_the_duplicate_key_inert_sector_of_toy6_also_carries_a_witness() -> None:
    """The mirror image of s2's witness.

    Recording ``removable`` for TOY-6 as ``{s0: False, s1: False, s2: True}``
    would reject s1 because "s2 is itself the sector we would be trying to
    justify against". That is an argument about removing s1 AND s2 together.
    Theorem ``thm:removal`` is stated for ONE sector ``s*`` with targets drawn
    from the other sectors, and for ``s* = s1`` the sector s2 satisfies every
    hypothesis:

        s1 is state-blind (one-dimensional);
        (RM1)  c_{v,s1} = (1, 0) = 1 * tr[F^{(s2)}_v chi] = (1, 0);
        (RM2)  (chat0, s2) is key-inert -- its effective outcome set is the
               singleton {(x0, v0)};
        (RM3)  o_{1,s1} = 0 = 1 * tr[O_1^{(s2)} chi] = 0.

    So this implementation reports s1 as removable, and the report is SOUND:
    deleting s1 leaves ``w0 + w2 = 1`` with ``w0 >= 1/2``, the same range of the
    only variable the objective depends on, hence the same infimum -- which the
    next test verifies numerically.

    This verdict is confirmed against the theorem and against the registry's
    own naive evaluator, and the registry field agrees. The assertion below pins
    the field so that a silent revert would fail here.
    """
    maps = generate_maps(declaration_of("TOY-6"))
    report = build_sector_report(maps)
    record = report.record("s1")
    assert record.removable is True
    assert record.removal_witness is not None
    assert [t.sector for t in record.removal_witness.targets] == ["s2"]
    verify_removal_witness(maps, record.removal_witness)
    assert toy("TOY-6").removable["s1"] is True  # the registry, corrected to agree


@pytest.mark.contract
@pytest.mark.parametrize("alpha", ALPHAS)
def test_deleting_either_duplicate_leaves_the_objective_alone(alpha: float) -> None:
    """The mathematical content of ``removable``: the value does not move.

    Theorem ``thm:removal``'s conclusion is about the INFIMUM, and on TOY-6 the
    objective depends on the sector weights only through ``w0``, whose feasible
    range ``[1/2, 1]`` is unchanged by deleting either of the two duplicate
    key-inert sectors. Checked pointwise here at the boundary optimum; the
    end-to-end version is in the golden tests.
    """
    from certiqs_key.meat_core.objective.objective import (
        acceptance_vector,
        objective_value,
    )

    maps = generate_maps(declaration_of("TOY-6"))
    one = np.ones((1, 1), dtype=np.complex128)
    full = objective_value(
        maps,
        acceptance_vector(maps.declaration),
        {
            "s0": np.array([[0.5]], dtype=np.complex128),
            "s1": np.array([[0.3]], dtype=np.complex128),
            "s2": np.array([[0.2]], dtype=np.complex128),
        },
        alpha,
    )
    for removed, kept in (("s2", "s1"), ("s1", "s2")):
        reduced = delete_sectors(
            maps, [RemovalWitness(removed, (RemovalTarget(kept, one, 1.0),))]
        )
        reduced_maps = generate_maps(reduced)
        value = objective_value(
            reduced_maps,
            acceptance_vector(reduced),
            {
                "s0": np.array([[0.5]], dtype=np.complex128),
                kept: np.array([[0.5]], dtype=np.complex128),
            },
            alpha,
        )
        assert value == pytest.approx(full, abs=1e-12)


@pytest.mark.contract
def test_the_module_offers_no_way_to_merge_or_average_sectors() -> None:
    """Remark rem:classes (iii): nothing else. Enforced by absence.

    Proposition ``prop:no-averaging`` prices merging at one bit in the
    dangerous direction, and the durable protection is that no function
    performs it: the public surface of the sector module contains exactly one
    structure-changing operation, and it demands a checked witness.
    """
    import certiqs_key.meat_core.declaration.sectors as module

    surface = {name for name in dir(module) if not name.startswith("_")}
    for forbidden in ("merge", "average", "coarse_grain", "collapse", "prune"):
        assert not any(forbidden in name.lower() for name in surface), forbidden
    changing = {name for name in surface if name.startswith("delete")}
    assert changing == {"delete_sectors"}


@pytest.mark.contract
def test_the_sector_report_is_serializable_data() -> None:
    """The ``sector_report`` output of Section 2.2 carries no operators."""
    import json

    maps = generate_maps(declaration_of("TOY-6"))
    payload = build_sector_report(maps).as_payload()
    json.dumps(payload)
    assert {row["sector"] for row in payload} == {"s0", "s1", "s2"}
    for row in payload:
        assert set(row) == {
            "sector",
            "class",
            "state_blind",
            "removable",
            "key_inert",
            "removal_targets",
            "removal_note",
        }
        assert row["removal_note"]
