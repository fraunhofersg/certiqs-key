"""D-1 on the engine: the qubit target scaled by the single-photon weight.

``O-DECOY-D1-QUBIT-LIMIT`` freezes D-1 against a closed form, and
``test_decoy_bb84_registry_integrity.py`` recomputes that closed form. Neither
runs the engine, which is the gap in the coverage of D1. This file runs it:
the general-format objective of ``meat-core``
(``build_joint_maps``, ``joint_objective_value``) on a declaration of the
entry's instance, ``DECOY-IDEAL-TWO-SECTOR``, at its noiseless honest point,
against

* the frozen tail-corrected values on the frozen grid (the entry's
  observable), with the vacuum and tail-flag deficits zero and the one-photon
  deficit ``(1 - 2^{1-alpha}) g_1``, which is the mechanism the entry states;
* the tail-free comparison source, where the value is ``w (1 - gamma) = 1/8``
  at every alpha (T1 scaled);
* the entry's discriminating check: with the tail, the value at
  ``alpha = 1.05`` is NOT ``1/8``.

WHY A HAND-BUILT DECLARATION AND NOT ``instances/decoy_bb84``. The entry says
it: that instance has three intensities and a passive four-detector receiver
where D-1 is stated on one intensity and an ideal threshold pair, and a
tail-free source with weight on ``n = 1`` is not a weak-coherent-pulse
declaration at all (the entry's step 2). So the declaration below is the
instance's shape written out: one intensity, four polarisations, a coin
``gamma = 1/2`` with generation in Z only and Bob measuring Z, an ideal
receiver (a vacuum sector that never clicks and a qubit sector that always
does), acceptance convention A (``gen`` is a sifted generation round), direct
reconciliation. Every declared number is dyadic, as the toys of
``tests/support/general_toys.py`` require. It is declared in ENSEMBLE form,
because the flag sectors' conditional letter weights (2/3, 1/3) are not
dyadic while the joint weights ``N_x`` are.
"""

from __future__ import annotations

import numpy as np
import pytest
from tests.oracles.registry_instances_decoy_bb84 import (
    DECOY_IDEAL_TWO_SECTOR,
    O_DECOY_D1_QUBIT_LIMIT,
    sector_deficit_factor,
    sifted,
)
from tests.support.general_toys import ALPHA_GRID

from certiqs_key.domain.manifest import KeyHolder, PartyLabel
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    KeyLengthParameters,
)
from certiqs_key.meat_core.declaration.general import (
    AliceFactor,
    AliceForm,
    GeneralDeclaration,
    MeasuredFactor,
    Message,
    Transcript,
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
from certiqs_key.meat_core.objective.linalg import Matrix

_ATOL = 1e-12

#: Alice's letters: the coin (``g`` generation, ``t`` test) and the
#: polarisation. Generation sends Z only; test sends all four.
_PROBABILITY = {
    "gz0": 0.25,
    "gz1": 0.25,
    "tz0": 0.125,
    "tz1": 0.125,
    "tx0": 0.125,
    "tx1": 0.125,
}
_POLARISATION = {x: x[1:] for x in _PROBABILITY}
_BIT = {"z0": 0, "z1": 1, "x0": 0, "x1": 1}
#: The polarisation projectors, WRITTEN OUT so that every entry is dyadic: a
#: projector formed from ``2**-0.5`` is off the lattice by one unit in the last
#: place, and the ensemble sum would then be refused as inexact.
_PROJECTOR: dict[str, Matrix] = {
    "z0": np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128),
    "z1": np.asarray([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128),
    "x0": np.asarray([[0.5, 0.5], [0.5, 0.5]], dtype=np.complex128),
    "x1": np.asarray([[0.5, -0.5], [-0.5, 0.5]], dtype=np.complex128),
}
_FLAGS = tuple(f"f{a}" for a in ("z0", "z1", "x0", "x1"))
_BOB_LETTERS = ("z0", "z1", "nc")


def _d1_declaration(*, tail: bool) -> GeneralDeclaration:
    """Return ``DECOY-IDEAL-TWO-SECTOR`` or its tail-free comparison source.

    With the tail: ``p~(0) = 1/2``, ``p~(1) = 1/4``, ``w~ = 1/4`` split over the
    four polarisation flags by the letters' weights. Tail-free: ``(3/4, 1/4)``
    on ``n <= 1`` and no flag, the entry's comparison source.
    """
    vacuum_weight = 0.5 if tail else 0.75
    one_weight = 0.25
    tail_weight = 0.25 if tail else 0.0
    alice_sectors: list[tuple[str, int]] = [("vacuum", 1), ("one", 2)]
    if tail:
        alice_sectors += [(flag, 1) for flag in _FLAGS]
    operators: dict[str, dict[str, Matrix]] = {}
    for x, p in _PROBABILITY.items():
        blocks: dict[str, Matrix] = {
            "vacuum": np.asarray([[vacuum_weight * p]], dtype=np.complex128),
            "one": one_weight * p * _PROJECTOR[_POLARISATION[x]],
        }
        if tail:
            for flag in _FLAGS:
                weight = tail_weight * p if flag == f"f{_POLARISATION[x]}" else 0.0
                blocks[flag] = np.asarray([[weight]], dtype=np.complex128)
        operators[x] = blocks
    # tau_A^{(t)} = sum_x N_x^{(t)}, exactly (every summand is dyadic).
    marginal = {
        label: sum(
            (operators[x][label] for x in _PROBABILITY),
            np.zeros((dim, dim), dtype=np.complex128),
        )
        for label, dim in alice_sectors
    }
    zero_1 = np.zeros((1, 1), dtype=np.complex128)
    zero_2 = np.zeros((2, 2), dtype=np.complex128)
    bob = MeasuredFactor(
        label="f0",
        party=PartyLabel.BOB,
        sectors=sector_axis([("v0", 1), ("q", 2)]),
        alphabet=_BOB_LETTERS,
        blocks={
            "z0": {"v0": zero_1, "q": _PROJECTOR["z0"]},
            "z1": {"v0": zero_1, "q": _PROJECTOR["z1"]},
            "nc": {"v0": np.ones((1, 1), dtype=np.complex128), "q": zero_2},
        },
    )
    transcript = Transcript(
        messages=(
            Message(
                sender=KeyHolder.ALICE,
                alphabet=("g", "t"),
                table={(x, ()): x[0] for x in _PROBABILITY},
            ),
            Message(
                sender=KeyHolder.BOB,
                alphabet=("click", "nc"),
                table={
                    (v, (first,)): "nc" if v == "nc" else "click"
                    for v in _BOB_LETTERS
                    for first in ("g", "t")
                },
            ),
        )
    )
    statistic = {
        (first, second): "gen" if (first, second) == ("g", "click") else "other"
        for first in ("g", "t")
        for second in ("click", "nc")
    }
    key = {
        (x, v): (_BIT[_POLARISATION[x]] if x.startswith("g") and v != "nc" else None)
        for x in _PROBABILITY
        for v in _BOB_LETTERS
    }
    return GeneralDeclaration(
        alice=AliceFactor(party=PartyLabel.ALICE, sectors=sector_axis(alice_sectors)),
        alice_marginal=marginal,
        alice_alphabet=tuple(_PROBABILITY),
        alice_operators=operators,
        alice_form=AliceForm.ENSEMBLE,
        factors=(bob,),
        transcript=transcript,
        accept_statistic=statistic,
        key_map=key,
        key_holder=KeyHolder.ALICE,
        acceptance_values=("gen", "other"),
        key_value_count=2,
        acceptance_set=AcceptanceSet(geometry="singleton", frequencies=(0.25, 0.75)),
        rounds=1000,
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=1e-10, eps_ev=1e-10, lambda_ec=0
        ),
        sector_block_kind="photon_number",
    )


def _noiseless_point(maps: JointMaps) -> dict[JointSector, Matrix]:
    """Return the honest Choi point: an identity channel on every sector.

    Full frame (ensemble form), so the coupling is ``tr_Q J_t = 1``: the vacuum
    reaches Bob's vacuum, the one-photon sector is the unnormalised maximally
    entangled block, and each flag sector delivers one photon in its own
    polarisation, which an ideal receiver detects with the matching bit.
    """
    point: dict[JointSector, Matrix] = {
        pair: np.zeros((maps.parametrization.block_dim(pair),) * 2, dtype=np.complex128)
        for pair in maps.joint_sectors
    }
    point[("vacuum", "v0")] = np.ones((1, 1), dtype=np.complex128)
    omega = np.asarray([1.0, 0.0, 0.0, 1.0], dtype=np.complex128)
    point[("one", "q")] = np.outer(omega, omega.conj())
    for flag in _FLAGS:
        if (flag, "q") in point:
            point[(flag, "q")] = _PROJECTOR[flag[1:]]
    return point


def _maps(*, tail: bool) -> JointMaps:
    return build_joint_maps(joint_choi_parametrization(_d1_declaration(tail=tail)))


@pytest.mark.parametrize("tail", [True, False])
def test_the_declaration_is_exactly_admissible(tail: bool) -> None:
    validate_general_declaration(_d1_declaration(tail=tail))


def test_the_declaration_reproduces_the_frozen_sifted_masses() -> None:
    maps = _maps(tail=True)
    q = joint_statistics(maps, _noiseless_point(maps))
    assert q["gen"] == pytest.approx(
        float(DECOY_IDEAL_TWO_SECTOR.sifted_generation_total), abs=_ATOL
    )
    assert sum(q.values()) == pytest.approx(1.0, abs=_ATOL)


@pytest.mark.parametrize("alpha,expected", O_DECOY_D1_QUBIT_LIMIT.frozen_values)
def test_the_engine_reproduces_the_frozen_tail_corrected_values(
    alpha: float, expected: float
) -> None:
    maps = _maps(tail=True)
    point = _noiseless_point(maps)
    q = joint_statistics(maps, point)
    assert joint_objective_value(maps, q, point, alpha) == pytest.approx(
        expected, abs=_ATOL
    )
    # The mechanism the entry states: the vacuum never clicks and a flag's key
    # is constant, so the only deficit is the one-photon sector's.
    deficits = evaluate_joint_branches(maps, point, alpha, skip_key_inert=False)[
        "gen"
    ].deficits
    g_1 = sifted(DECOY_IDEAL_TWO_SECTOR, "one-photon")
    for pair, value in deficits.items():
        target = (
            -sector_deficit_factor(alpha, (0.5, 0.5)) * g_1
            if pair == ("one", "q")
            else 0.0
        )
        assert value == pytest.approx(target, abs=_ATOL), pair


@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_the_tail_free_source_is_the_qubit_target_scaled(alpha: float) -> None:
    maps = _maps(tail=False)
    point = _noiseless_point(maps)
    q = joint_statistics(maps, point)
    assert q["gen"] == pytest.approx(float(O_DECOY_D1_QUBIT_LIMIT.value), abs=_ATOL)
    assert joint_objective_value(maps, q, point, alpha) == pytest.approx(
        float(O_DECOY_D1_QUBIT_LIMIT.value), abs=_ATOL
    )


def test_with_the_tail_the_value_is_not_the_scaled_target() -> None:
    maps = _maps(tail=True)
    point = _noiseless_point(maps)
    q = joint_statistics(maps, point)
    value = joint_objective_value(maps, q, point, 1.05)
    assert abs(value - float(O_DECOY_D1_QUBIT_LIMIT.value)) > 1e-4
