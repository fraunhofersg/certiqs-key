"""``prop:a-neutral`` pointwise: pinching along Alice's sectors never lowers ``K``.

The proposition says: for every state ``omega`` of ``Feas°`` (the feasible set
of the same declaration with Alice's sector split forgotten), the pinched
``omega' = (P_T (x) id)(omega)`` lies in ``Feas``, has the same statistics, a
``K`` per acceptance value no smaller, and an objective no larger. The engine
never holds a state that is not block diagonal along ``T``, since its points
are lists over the joint sectors, so nothing in the engine can violate the
proposition. What it can get wrong is the claim that its sectored
representation is the same program. This file tests both halves, with
the engine's own evaluation on each side:

* the MERGED declaration (one Alice sector, ``A = A_a (+) A_b``, the same
  ``tau_A``, ``M_x`` and constraint entry) is ``Feas°``'s program, where a
  random point is dense across the two sectors;
* its pinching, evaluated on the merged declaration, obeys every relation of
  ``eq:a-neutral``, with a strict increase of ``K`` at some point;
* the pinched point, re-read as a list over the SECTORED declaration's joint
  sectors, gives the same statistics, ``K`` and objective there, and is
  feasible there.

The toy is qubit BB84 on each sector, with the second sector's letters
relabelled so the two sectors disagree about which basis a letter belongs
to. One scalar entry ``tr_Q[(1 (x) O) omega] >= c tau_A`` is declared, with
``c`` read off each random point and rounded down to a dyadic value, so that
membership is a check the point can fail rather than an empty one.

NOT HERE: the paired comparison of the two INFIMA (the audit's "paired
infimum check") needs optimiser runs and is deferred with the other
optimizer-paired comparisons of the two-sided sweep.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest
from tests.support.general_toys import (
    ALPHA_GRID,
    BB84_ELEMENTS,
    qubit_bb84_general,
    random_choi_point,
)

from certiqs_key.domain.manifest import ConstraintRelation, PartyLabel
from certiqs_key.meat_core.declaration.general import (
    AliceFactor,
    GeneralConstraintEntry,
    GeneralDeclaration,
    GeneralRhsTag,
    sector_axis,
)
from certiqs_key.meat_core.declaration.general_validation import (
    validate_general_declaration,
)
from certiqs_key.meat_core.objective.joint import (
    JointMaps,
    JointSector,
    build_joint_maps,
    evaluate_joint_branches,
    joint_choi_parametrization,
    joint_objective_value,
    joint_statistics,
)
from certiqs_key.meat_core.objective.joint_rows import check_joint_feasible
from certiqs_key.meat_core.objective.linalg import Matrix

_ATOL = 1e-12
_SEEDS = (0, 1, 2, 3, 4, 5)
#: The second sector's letter relabelling: Z letters read X elements.
_SWAP = {"z0": "x0", "z1": "x1", "x0": "z0", "x1": "z1"}
_CONSTRAINED = BB84_ELEMENTS["z0"]


def _entry(bound: float) -> GeneralConstraintEntry:
    return GeneralConstraintEntry(
        scope="f0",
        operator_blocks={"q": _CONSTRAINED},
        relation=ConstraintRelation.SUCCEQ,
        bound=bound,
        rhs_tag=GeneralRhsTag.HOMOGENEOUS,
    )


def _declarations(bound: float) -> tuple[GeneralDeclaration, GeneralDeclaration]:
    """Return the SECTORED declaration (``a``, ``b``) and its MERGED twin.

    ``tau_A = 1/4`` on the four-dimensional ``A``, weight 1/2 per sector, so
    both declarations' support frames are ``W = 1/2``, and a Choi point of one
    is a Choi point of the other with the same blocks.
    """
    base = qubit_bb84_general()
    quarter = 0.25 * np.eye(2, dtype=np.complex128)
    sectored = replace(
        base,
        alice=AliceFactor(
            party=PartyLabel.ALICE, sectors=sector_axis([("a", 2), ("b", 2)])
        ),
        alice_marginal={"a": quarter, "b": quarter},
        alice_operators={
            x: {"a": BB84_ELEMENTS[x], "b": BB84_ELEMENTS[_SWAP[x]]}
            for x in base.alice_alphabet
        },
        constraint_list=(_entry(bound),),
    )
    zero = np.zeros((2, 2), dtype=np.complex128)
    merged = replace(
        sectored,
        alice=AliceFactor(party=PartyLabel.ALICE, sectors=sector_axis([("ab", 4)])),
        alice_marginal={"ab": 0.25 * np.eye(4, dtype=np.complex128)},
        alice_operators={
            x: {"ab": np.block([[blocks["a"], zero], [zero, blocks["b"]]])}
            for x, blocks in sectored.alice_operators.items()
        },
    )
    return sectored, merged


def _maps(declaration: GeneralDeclaration) -> JointMaps:
    validate_general_declaration(declaration)
    return build_joint_maps(joint_choi_parametrization(declaration))


def _pinch(block: Matrix) -> Matrix:
    """Return ``(P_T (x) id)`` of a Choi block on ``A (x) Q``, ``A`` index first."""
    alice = np.repeat([0, 0, 1, 1], 2)
    return np.where(alice[:, None] == alice[None, :], block, 0.0)


def _bound_for(point: Matrix) -> float:
    """Return the largest dyadic ``c`` (step 2^-20) the point satisfies."""
    lifted = np.kron(np.eye(4), _CONSTRAINED)
    reduced = np.einsum(
        "aqbq->ab", (lifted @ (0.25 * point)).reshape(4, 2, 4, 2)
    )  # tr_Q[(1 (x) O) omega] with omega = (1/2 (x) 1) J (1/2 (x) 1)
    smallest = float(np.min(np.linalg.eigvalsh(0.5 * (reduced + reduced.conj().T))))
    return math.floor(smallest / 0.25 * 2**20) / 2**20


def _sectored_point(block: Matrix) -> dict[JointSector, Matrix]:
    return {("a", "q"): block[:4, :4], ("b", "q"): block[4:, 4:]}


@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_pinching_along_alice_sectors_obeys_eq_a_neutral(alpha: float) -> None:
    increases = []
    for seed in _SEEDS:
        # The bound only enters feasibility, never the maps, so a point drawn
        # on a placeholder declaration serves for every bound.
        dense = random_choi_point(
            joint_choi_parametrization(_declarations(0.0)[1]), seed
        )[("ab", "q")]
        sectored, merged = _declarations(_bound_for(dense))
        merged_maps, sectored_maps = _maps(merged), _maps(sectored)
        pinched = _pinch(dense)
        assert np.max(np.abs(dense - pinched)) > 1e-2  # the point is dense

        before = {("ab", "q"): dense}
        after = {("ab", "q"): pinched}
        split = _sectored_point(pinched)

        # Membership: Feas° before, Feas after (on the sectored declaration).
        check_joint_feasible(
            merged_maps.parametrization,
            merged_maps.parametrization.state_from_choi(before),
        )
        check_joint_feasible(
            sectored_maps.parametrization,
            sectored_maps.parametrization.state_from_choi(split),
        )

        # Statistics unchanged, and the same on the sectored representation.
        q_before = joint_statistics(merged_maps, before)
        q_after = joint_statistics(merged_maps, after)
        q_split = joint_statistics(sectored_maps, split)
        assert q_after == pytest.approx(q_before, abs=_ATOL)
        assert q_split == pytest.approx(q_before, abs=_ATOL)

        # K no smaller after pinching; equal across the two representations.
        k_before = evaluate_joint_branches(merged_maps, before, alpha)
        k_after = evaluate_joint_branches(merged_maps, after, alpha)
        k_split = evaluate_joint_branches(sectored_maps, split, alpha)
        for chat in merged.acceptance_values:
            assert k_after[chat].k >= k_before[chat].k - _ATOL, chat
            assert k_split[chat].k == pytest.approx(k_after[chat].k, abs=_ATOL)
        increases.append(k_after["match"].k - k_before["match"].k)

        # The objective no larger, at the observed q and at a shifted one.
        for q in (q_before, {"match": 0.4, "mismatch": 0.6}):
            o_before = joint_objective_value(merged_maps, q, before, alpha)
            o_after = joint_objective_value(merged_maps, q, after, alpha)
            o_split = joint_objective_value(sectored_maps, q, split, alpha)
            assert o_after <= o_before + _ATOL
            assert o_split == pytest.approx(o_after, abs=_ATOL)
    # Not vacuous: the coherence between the sectors carries information.
    assert max(increases) > 1e-6
