"""B4 on emitted passive stations: swap factors, parties, coin and key holder."""

from dataclasses import replace
from fractions import Fraction
from itertools import product

import numpy as np
import pytest
from instances.bbm92.surface import default_config, preparation

from certiqs_key.domain.announcements import AnnouncementTranscript
from certiqs_key.foundations.blocks import PRODUCT_LABEL_SEPARATOR
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.meat_core.objective.joint import (
    build_joint_maps,
    joint_choi_parametrization,
    joint_objective_value,
    joint_statistics,
)
from certiqs_key.protocol_compiler import Party
from certiqs_key.protocol_compiler.compile import compile_specification
from certiqs_key.runs.pipeline import Preparation


def exchanged(prepared: Preparation):
    spec = prepared.specification
    old = prepared.declaration
    assert old.bob_factors is not None
    left, right = old.bob_factors.factors
    labels = {
        PRODUCT_LABEL_SEPARATOR.join((a, b)): PRODUCT_LABEL_SEPARATOR.join((b, a))
        for a, b in product(left.alphabet, right.alphabet)
    }
    public = spec.public
    partition = public.partition
    assert partition is not None and public.transcript is not None
    swapped_partition = replace(
        partition,
        alice_readout={
            (x, labels[v]): value for (x, v), value in partition.bob_readout.items()
        },
        bob_readout={
            (x, labels[v]): value for (x, v), value in partition.alice_readout.items()
        },
        alice_readout_alphabet=partition.bob_readout_alphabet,
        bob_readout_alphabet=partition.alice_readout_alphabet,
        alice_system_party=Party.BOB,
        sector_factor_parties=((Party.ALICE,), (Party.BOB,)),
    )
    public = replace(
        public,
        partition=swapped_partition,
        holder=Party.BOB,
        transcript=AnnouncementTranscript(
            messages=tuple(
                replace(message, sender="B" if message.sender == "A" else "A")
                for message in public.transcript.messages
            )
        ),
    )
    first, second = spec.receiver_parts
    changed = replace(
        spec,
        receiver=replace(second, party=Party.ALICE),
        further_receiver_factors=(replace(first, party=Party.BOB),),
        chain=second.chain,
        public=public,
    )
    compiled = compile_specification(changed)
    assert compiled.refusal is None, compiled.refusal
    assert compiled.declaration is not None
    return compiled.declaration, labels


@pytest.mark.parametrize("alpha", [1.05, 1.5, 2.0])
def test_identical_actual_stations_preserve_maps_and_objective_under_holder_swap(
    alpha: float,
):
    config = default_config()
    prepared = preparation(config)
    assert isinstance(prepared, Preparation)
    original = prepared.declaration
    swapped, labels = exchanged(prepared)
    assert original.key_holder == Party.ALICE and swapped.key_holder == Party.BOB
    assert swapped.measured_factor_labels == tuple(
        reversed(original.measured_factor_labels)
    )
    for x, v in original.outcome_pairs():
        assert swapped.announcement(x, labels[v]) == original.announcement(x, v)
        assert swapped.key_map[(x, labels[v])] == original.key_map[(x, v)]
    assert original.bob_factors is not None and swapped.bob_factors is not None
    # Both are real compiled declarations. The first station's coin physically
    # moves to the second factor; this is not a second solve of the same data.
    assert swapped.bob_factors.factors == tuple(
        replace(factor, party="A" if factor.party == "B" else "B")
        for factor in reversed(original.bob_factors.factors)
    )
    assert len(original.bob_factors.factors[0].alphabet) == 12
    assert len(swapped.bob_factors.factors[0].alphabet) == 6
    maps = []
    for candidate in (original, swapped):
        d = dock_general_candidate(
            candidate,
            acceptance_set=AcceptanceSet(
                geometry="singleton",
                frequencies=tuple(
                    1.0 if value == "gen" else 0.0
                    for value in candidate.acceptance_alphabet
                ),
            ),
            rounds=config.rounds,
            parameters=config.parameters,
        )
        maps.append(build_joint_maps(joint_choi_parametrization(d)))
    d, reverse = (m.declaration for m in maps)
    rng = np.random.default_rng(3404)
    point, image = {}, {}
    total = 0.0
    for pair in d.joint_sectors:
        sa, sb = d.split_sector(pair[1])
        da, db = d.factors[0].sectors.dims[sa], d.factors[1].sectors.dims[sb]
        value = rng.normal(size=(da * db, da * db)) + 1j * rng.normal(
            size=(da * db, da * db)
        )
        rho = value @ value.conj().T
        point[pair] = rho
        total += float(np.trace(rho).real)
        target = next(
            k for k in reverse.joint_sectors if reverse.split_sector(k[1]) == (sb, sa)
        )
        image[target] = (
            rho.reshape(da, db, da, db).transpose(1, 0, 3, 2).reshape(db * da, db * da)
        )
    point = {k: value / total for k, value in point.items()}
    image = {k: value / total for k, value in image.items()}
    q = joint_statistics(maps[0], point)
    assert joint_statistics(maps[1], image) == pytest.approx(q, abs=2e-14)
    assert joint_objective_value(maps[0], q, point, alpha) == pytest.approx(
        joint_objective_value(maps[1], q, image, alpha), abs=2e-12
    )


def test_unequal_actual_station_devices_make_the_exchange_nontrivial():
    config = default_config()
    config = replace(
        config, device={**config.device, "bob_basis_split": Fraction(3, 8)}
    )
    prepared = preparation(config)
    assert isinstance(prepared, Preparation)
    swapped, _ = exchanged(prepared)
    original = prepared.declaration
    assert original.bob_factors is not None and swapped.bob_factors is not None
    assert swapped.bob_factors.factors[0] == replace(
        original.bob_factors.factors[1], party="A"
    )
    # Compare the physical (pre-coin) receiver data, so coin placement cannot
    # alone make this negative control pass.
    assert (
        prepared.specification.receiver_parts[0].physical_povm
        != prepared.specification.receiver_parts[1].physical_povm
    )
    assert original.as_machine_record() != swapped.as_machine_record()
