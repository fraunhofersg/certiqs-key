"""Property tests of the general format, on random points of the coupling set.

What is checked, each with the claim it is the content of:

* ``prop:drop-bound`` (i)-(iv): the chain ``0 <= K <= K^D <= K^D' <= P``, the
  objective's monotonicity in the dropped set, non-negativity at a normalised
  point, the identity at ``D = empty``, and the identity when every dropped pair
  is key-inert;
* ``lem:joint-sectors`` (iii) as plan item **P3**: skipping the key-inert pairs
  and computing their identically zero deficits give THE SAME VALUE, objective
  and gradient;
* ``lem:choi-factor`` (iii), (iv): an ensemble-form declaration and the
  POVM-form declaration it denotes give the same objective and gradient;
* ``eq:partylocal-entry`` read twice -- as an operator on the other systems and
  as the real equations the oracle consumes -- agree.
"""

from __future__ import annotations

import numpy as np
import pytest
from tests.support.general_toys import (
    ALPHA_GRID,
    decoy_like_general,
    honest_q,
    maps_of,
    qubit_bb84_general,
    random_choi_point,
    two_factor_general,
)

from certiqs_key.meat_core.objective.joint import (
    evaluate_joint_branches,
    joint_objective_value,
    joint_statistics,
    normalise_dropped_set,
)
from certiqs_key.meat_core.objective.joint_gradient import joint_gradient
from certiqs_key.meat_core.objective.joint_rows import party_local_value
from certiqs_key.solvers.oracles.joint_rows import (
    joint_label,
    joint_program_untrusted,
)

SEEDS = (11, 12, 13)

#: The agreement two arithmetic routes to one real number reach here. NOT A
#: DECLARED TOLERANCE: no declaration is admitted by it and no predicate of the
#: engine is decided at it.
ROUTE_ATOL = 1e-10


@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize("seed", SEEDS)
def test_the_dropped_program_is_a_bound_in_the_safe_direction(
    alpha: float, seed: int
) -> None:
    """``prop:drop-bound`` (i), (ii), (iii): pointwise, and monotone in ``D``."""
    maps = maps_of(decoy_like_general())
    choi = random_choi_point(maps.parametrization, seed)
    q = honest_q(maps, choi)
    small = normalise_dropped_set(maps, [("match", ("one", "q"))])
    large = normalise_dropped_set(
        maps, [("match", ("one", "q")), ("match", ("vacuum", "q"))]
    )
    undropped = evaluate_joint_branches(maps, choi, alpha)
    dropped = evaluate_joint_branches(maps, choi, alpha, dropped=small)
    more = evaluate_joint_branches(maps, choi, alpha, dropped=large)
    for chat in maps.chat_key:
        assert undropped[chat].k >= 0.0
        assert undropped[chat].k <= dropped[chat].k + ROUTE_ATOL
        assert dropped[chat].k <= more[chat].k + ROUTE_ATOL
        assert more[chat].k <= undropped[chat].p + ROUTE_ATOL
    base = joint_objective_value(maps, q, choi, alpha)
    one = joint_objective_value(maps, q, choi, alpha, dropped=small)
    two = joint_objective_value(maps, q, choi, alpha, dropped=large)
    assert two <= one + ROUTE_ATOL
    assert one <= base + ROUTE_ATOL
    assert two >= 0.0


@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_dropping_nothing_and_dropping_a_key_inert_pair_are_identities(
    alpha: float,
) -> None:
    """``def:dropped`` at ``D = empty`` and ``prop:drop-bound`` (iv)."""
    maps = maps_of(decoy_like_general())
    choi = random_choi_point(maps.parametrization, 14)
    q = honest_q(maps, choi)
    base = joint_objective_value(maps, q, choi, alpha)
    empty = joint_objective_value(
        maps, q, choi, alpha, dropped=normalise_dropped_set(maps, [])
    )
    assert empty == base
    inert = normalise_dropped_set(maps, [("match", ("flag", "q"))])
    assert maps.key_inert[("match", ("flag", "q"))]
    assert joint_objective_value(maps, q, choi, alpha, dropped=inert) == base


def test_a_dropped_pair_keeps_its_statistics_weight() -> None:
    """``def:dropped``, "What is not changed": ``Phi`` is untouched."""
    maps = maps_of(decoy_like_general())
    choi = random_choi_point(maps.parametrization, 15)
    dropped = normalise_dropped_set(maps, [("match", ("one", "q"))])
    values = evaluate_joint_branches(maps, choi, 1.5, dropped=dropped)
    assert values["match"].p == pytest.approx(
        joint_statistics(maps, choi)["match"], abs=0.0
    )
    assert values["match"].dropped_pairs == (("one", "q"),)


def test_dropping_a_pair_that_is_not_key_live_is_refused() -> None:
    """``def:dropped``: ``D`` is a subset of ``Chat_key x (T x S)``."""
    maps = maps_of(decoy_like_general())
    with pytest.raises(Exception, match="key-live"):
        normalise_dropped_set(maps, [("mismatch", ("one", "q"))])
    with pytest.raises(Exception, match="declared joint sector"):
        normalise_dropped_set(maps, [("match", ("nowhere", "q"))])


@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize("seed", SEEDS)
def test_skipping_key_inert_pairs_changes_no_value(alpha: float, seed: int) -> None:
    """Plan item **P3**, which is ``lem:joint-sectors`` (iii) as an identity.

    The default skips a key-inert pair's deficit; ``skip_key_inert=False``
    computes it. The two paths must agree, and they agree at the accumulated
    rounding of the matrix route rather than exactly, which is why the accepted
    format's path is left computing the identity: there the last bits are frozen
    numbers.
    """
    maps = maps_of(decoy_like_general())
    choi = random_choi_point(maps.parametrization, seed)
    q = honest_q(maps, choi)
    skipped = joint_objective_value(maps, q, choi, alpha)
    computed = joint_objective_value(maps, q, choi, alpha, skip_key_inert=False)
    assert skipped == pytest.approx(computed, abs=ROUTE_ATOL)
    left = joint_gradient(maps, q, choi, alpha)
    right = joint_gradient(maps, q, choi, alpha, skip_key_inert=False)
    for pair in maps.joint_sectors:
        assert np.allclose(left.blocks[pair], right.blocks[pair], atol=ROUTE_ATOL)
    # The gradient omits a key-inert pair's piece on BOTH paths -- there the
    # restriction is thm:gradient (ii)'s and not a choice -- so what the flag
    # moves is the K values the prefactors read, and they agree.
    assert left.key_inert_pieces == right.key_inert_pieces


@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize("seed", SEEDS)
def test_the_two_forms_of_alices_slot_agree_on_random_points(
    alpha: float, seed: int
) -> None:
    """``lem:choi-factor`` (iii), (iv) on the qubit declaration."""
    povm = maps_of(qubit_bb84_general())
    ensemble = maps_of(qubit_bb84_general(ensemble=True))
    choi = random_choi_point(povm.parametrization, seed)
    q = honest_q(povm, choi)
    assert joint_objective_value(ensemble, q, choi, alpha) == pytest.approx(
        joint_objective_value(povm, q, choi, alpha), abs=ROUTE_ATOL
    )
    left = joint_gradient(povm, q, choi, alpha)
    right = joint_gradient(ensemble, q, choi, alpha)
    assert left.q == pytest.approx(right.q, abs=ROUTE_ATOL)
    for pair in povm.joint_sectors:
        assert np.allclose(left.blocks[pair], right.blocks[pair], atol=ROUTE_ATOL)


@pytest.mark.parametrize("seed", SEEDS)
def test_the_oracles_party_local_equations_are_the_operator_row(seed: int) -> None:
    """``thm:choi``'s general format: the two readings of ``eq:partylocal-entry``.

    The engine reads the row as an operator on ``A_t`` and the other measured
    factors; the oracle consumes one real equation per Hermitian basis element of
    that space. Pairing the equations' coefficients against the point must return
    the operator's own components, or the backend is solving a different program
    from the one the feasibility check decides.
    """
    declaration = two_factor_general(party_local=True)
    maps = maps_of(declaration)
    parametrization = maps.parametrization
    choi = random_choi_point(parametrization, seed)
    program = joint_program_untrusted(parametrization, choi)
    assert program.general_rows
    from certiqs_key.solvers.oracles.protocol import hermitian_basis

    operator_rows = party_local_value(declaration, 0, choi)
    labelled = {joint_label(pair): choi[pair] for pair in parametrization.joint_sectors}
    for row in program.general_rows:
        alice_sector, _, other = row.label.partition("@")[2].partition("|")
        expected = operator_rows[(alice_sector, other)]
        basis = hermitian_basis(row.slack_dim)
        for per_block, element in zip(row.coefficients, basis, strict=True):
            value = sum(
                float(np.real(np.trace(np.asarray(coefficient) @ labelled[block])))
                for block, coefficient in per_block.items()
            )
            assert value == pytest.approx(
                float(np.real(np.trace(element @ expected))), abs=ROUTE_ATOL
            )
