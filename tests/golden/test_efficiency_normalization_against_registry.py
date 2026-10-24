"""The efficiency normalization against its hand-derived registry.

Golden replay of ``tests/oracles/registry_efficiency_normalization.py``: the
two-photon multiclick block and the exact-window value with and without the
normalization (``rem:normalization-gain``), the pull-back on the one-photon
block (``prop:efficiency-normalization`` (i), (ii)), the honest statistics of
the worked example (``req:loss-before-evaluation``), and the emitted
numbers of a normalized station against those of the station declared
normalized outright (``reductions/wpfss/cor:normalized-flat``,
``req:normalized-link-record``).
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest
from instances.bbm92 import surface as bbm92
from instances.common.optics import ReceiverParameters, receiver_request
from registry_efficiency_normalization import (
    BOTH_DETECT,
    DEFAULT_COMPILED_EFFICIENCY,
    DEFAULT_FACTOR_ONE_FIFTH,
    DEFAULT_FACTOR_THREE_FIFTHS,
    DEFAULT_NORMALIZED_TRANSMITTANCES,
    MULTICLICK_DEFAULT_SCALE,
    MULTICLICK_TWO_PHOTON,
    NEITHER_DETECTS,
    NORMALIZED_TRANSMITTANCES,
    ONE_PHOTON_H_DEFAULT,
    ONE_PHOTON_H_DEVICE,
    ONE_PHOTON_H_FULL,
    WINDOW_DEFAULT,
    WINDOW_FULL,
    WINDOW_UNNORMALIZED,
)

from certiqs_key.receiver import (
    ReceiverMeasurementArtifact,
    ReceiverRequest,
    construct_receiver,
)
from certiqs_key.reductions.channels import ChannelWitness
from certiqs_key.runs.pipeline import Preparation

PORTS = ("H", "V", "D", "A")
F = Fraction
#: Binary64 arithmetic on blocks of entries of order one: far below any
#: difference this file tests and far above the rounding of the compiled
#: product.
ATOL = 1e-12


def _artifact(request: ReceiverRequest) -> ReceiverMeasurementArtifact:
    emission = construct_receiver(request)
    assert emission.artifact is not None, emission.refusal
    return emission.artifact


def _request(
    efficiency: Fraction,
    *,
    cutoff: int,
    window: int | None = None,
    dark: Fraction = Fraction(0),
    normalization: Fraction | None = None,
) -> ReceiverRequest:
    parameters = ReceiverParameters(
        efficiency=(efficiency,) * 4,
        dark_count=(dark,) * 4,
        photon_cutoff=cutoff,
        exact_window=window,
    )
    return replace(
        receiver_request(parameters), efficiency_normalization=normalization
    )


def _block(
    artifact: ReceiverMeasurementArtifact, photons: int, letter: str, *, dark: bool
) -> np.ndarray:
    family = artifact.photon_blocks[0]
    blocks = family.dark_composed if dark else family.blocks
    for n, letters in blocks:
        if n == photons:
            return np.asarray(dict(letters)[letter])
    raise AssertionError(f"no block n = {photons}")


def _matrix(rows: tuple[tuple[Fraction, ...], ...], scale: Fraction) -> np.ndarray:
    return np.asarray([[float(scale * value) for value in row] for row in rows])


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_photon_multiclick_block_scales_with_eta_squared() -> None:
    """rem:normalization-gain on the registry's block, at eta = 1/5.

    At ``t = 1``, at the full normalization ``t = 1/5`` and by default
    (``t = 20/99``, every port at ``99/100``).
    """
    plain = _artifact(_request(F(1, 5), cutoff=2, normalization=F(1)))
    full = _artifact(_request(F(1, 5), cutoff=2, normalization=F(1, 5)))
    default = _artifact(_request(F(1, 5), cutoff=2))
    normalization = default.efficiency_record.normalization
    assert normalization.factored_loss == DEFAULT_FACTOR_ONE_FIFTH
    assert {p.compiled for p in normalization.ports} == {DEFAULT_COMPILED_EFFICIENCY}
    for artifact, scale in (
        (plain, F(1, 25)),
        (full, F(1)),
        (default, MULTICLICK_DEFAULT_SCALE),
    ):
        assert np.allclose(
            _block(artifact, 2, "mc", dark=False),
            _matrix(MULTICLICK_TWO_PHOTON, scale),
            atol=ATOL,
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_exact_window_value_is_the_normalized_stations() -> None:
    """The exact-window value at n = 2, N = 1, at t = 1, t = 1/5 and by default."""
    cases = (
        (F(1), WINDOW_UNNORMALIZED),
        (F(1, 5), WINDOW_FULL),
        (None, WINDOW_DEFAULT),
    )
    for normalization, expected in cases:
        artifact = _artifact(
            _request(F(1, 5), cutoff=1, window=2, normalization=normalization)
        )
        record = artifact.bound_quantifier_domain.per_setting[0].exact_window
        assert record is not None
        (row,) = record.rows
        assert row[0] == 2
        assert row[2] == pytest.approx(float(expected), abs=ATOL)
    # At t = 1 the emitted weight is at most the window value (rem:normalization-gain).
    plain = _artifact(_request(F(1, 5), cutoff=1, window=2, normalization=F(1)))
    assert plain.high_photon_bounds.entries[0].weight <= float(WINDOW_UNNORMALIZED)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_one_photon_block_is_the_pull_back_of_the_normalized_station() -> None:
    """prop:efficiency-normalization (i) on block 1, with the registry's values."""
    device = _artifact(_request(F(3, 5), cutoff=1, normalization=F(1)))
    full = _artifact(_request(F(3, 5), cutoff=1, normalization=F(3, 5)))
    default = _artifact(_request(F(3, 5), cutoff=1))
    assert full.efficiency_record.normalization.factored_loss == F(3, 5)
    assert (
        default.efficiency_record.normalization.factored_loss
        == DEFAULT_FACTOR_THREE_FIFTHS
    )
    # The basis of the one-photon block is (|V>, |H>): ascending occupation order.
    h_device = _block(device, 1, "H", dark=False)
    assert h_device[1, 1].real == pytest.approx(float(ONE_PHOTON_H_DEVICE), abs=ATOL)
    for artifact, expected in (
        (full, ONE_PHOTON_H_FULL),
        (default, ONE_PHOTON_H_DEFAULT),
    ):
        h_normalized = _block(artifact, 1, "H", dark=False)
        assert h_normalized[1, 1].real == pytest.approx(float(expected), abs=ATOL)


@pytest.mark.contract
@pytest.mark.parametrize("letter", ["nc", "H", "V", "D", "A", "mc"])
@pytest.mark.parametrize("declared", [None, F(3, 5)], ids=["default", "full"])
def test_dark_counts_act_after_the_factored_loss(
    letter: str, declared: Fraction | None
) -> None:
    """prop:efficiency-normalization (ii): blk_1 M = t blk_1 M' + (1 - t) blk_0 M'.

    On the DARK-COMPOSED family, with a dark count in every port, so that
    ``blk_0 M'`` is not zero: the dark counts act after the loss, and the
    identity holds of every letter of the coarse-grained family, at the
    default ``t = 20/33`` and at the full normalization ``t = 3/5`` declared.
    """
    eta = F(3, 5)
    t = DEFAULT_FACTOR_THREE_FIFTHS if declared is None else declared
    device = _artifact(_request(eta, cutoff=1, dark=F(1, 100), normalization=F(1)))
    normalized = _artifact(
        _request(eta, cutoff=1, dark=F(1, 100), normalization=declared)
    )
    assert normalized.efficiency_record.normalization.factored_loss == t
    expected = float(t) * _block(normalized, 1, letter, dark=True) + float(
        1 - t
    ) * _block(normalized, 0, letter, dark=True)[0, 0] * np.eye(2)
    assert np.allclose(_block(device, 1, letter, dark=True), expected, atol=ATOL)
    assert np.allclose(
        _block(device, 0, letter, dark=True),
        _block(normalized, 0, letter, dark=True),
        atol=ATOL,
    )


def _example(
    transmittances: tuple[Fraction, Fraction],
    efficiencies: tuple[Fraction, Fraction],
    factors: tuple[Fraction, Fraction] | None = None,
) -> Preparation:
    base = bbm92.default_config()
    declared = (
        {}
        if factors is None
        else {
            "alice_efficiency_normalization": factors[0],
            "bob_efficiency_normalization": factors[1],
        }
    )
    config = base.with_(
        model={
            **base.model,
            "alice_transmittance": transmittances[0],
            "bob_transmittance": transmittances[1],
            "visibility": F(47, 50),
        },
        device={
            **base.device,
            "alice_efficiency": dict.fromkeys(PORTS, efficiencies[0]),
            "bob_efficiency": dict.fromkeys(PORTS, efficiencies[1]),
            **declared,
        },
    )
    prepared = bbm92.preparation(config)
    assert isinstance(prepared, Preparation), prepared
    return prepared


def _letters(label: str) -> tuple[str, str]:
    """Return the two stations' letters of a bbm92 raw label ``(a,c)__b``."""
    alice, bob = label.split("__")
    return alice.strip("()").split(",")[0], bob


@pytest.mark.contract
@pytest.mark.oracle
def test_the_honest_law_is_the_devices_under_the_normalization() -> None:
    """req:loss-before-evaluation on the worked example, exactly.

    At the full normalization ``t = (3/5, 1/5)``, declared, the normalized
    receivers are ideal stations, so the declaration is the one of the
    efficiency-one device at transmittances (3/50, 1/5000); the honest model
    applies each station's factored loss to its arm, and the two laws agree
    as rationals, with the registry's detection probabilities. By default
    (``t = (20/33, 20/99)``) the normalized stations are at ``99/100``, whose
    blocks are binary64 evaluations, so the default's law is the same law to
    that rounding (and equals the stations declared at ``99/100`` exactly:
    ``test_a_normalized_station_emits_the_declared_normalized_stations_numbers``).
    """
    full = _example((F(1, 10), F(1, 1000)), (F(3, 5), F(1, 5)), (F(3, 5), F(1, 5)))
    reference = _example(NORMALIZED_TRANSMITTANCES, (F(1), F(1)))
    default = _example((F(1, 10), F(1, 1000)), (F(3, 5), F(1, 5)))
    assert full.raw_joint_distribution is not None
    assert full.raw_joint_distribution == reference.raw_joint_distribution
    assert default.raw_joint_distribution is not None
    assert default.raw_joint_distribution.keys() == full.raw_joint_distribution.keys()
    clicks = {"H", "V", "D", "A"}
    for law, exact in (
        (full.raw_joint_distribution, True),
        (default.raw_joint_distribution, False),
    ):
        both = sum(
            (p for (_, v), p in law.items() if {*_letters(v)} <= clicks),
            start=F(0),
        )
        neither = sum(
            (p for (_, v), p in law.items() if _letters(v) == ("nc", "nc")),
            start=F(0),
        )
        if exact:
            assert both == BOTH_DETECT
            assert neither == NEITHER_DETECTS
        else:
            assert abs(both - BOTH_DETECT) < ATOL
            assert abs(neither - NEITHER_DETECTS) < ATOL
            assert max(
                abs(p - full.raw_joint_distribution[k]) for k, p in law.items()
            ) < ATOL


@pytest.mark.contract
def test_a_normalized_station_emits_the_declared_normalized_stations_numbers() -> None:
    """cor:normalized-flat; req:normalized-link-record: only the link record differs.

    The device at efficiencies (3/5, 1/5), compiled by default at
    ``t = (20/33, 20/99)``, and the stations declared at ``99/100`` it
    normalizes to, at the arm transmittances of registry item 4. Every
    emitted number of each station's reduction artefact is the same; the
    device's link carries the pure-loss channel in front, with its factor
    under ``factored_loss``, the receiver's measurement as its source family,
    its pull-backs through the loss and the composite's reachable set.
    """
    device = _example((F(1, 10), F(1, 1000)), (F(3, 5), F(1, 5)))
    reference = _example(
        DEFAULT_NORMALIZED_TRANSMITTANCES,
        (DEFAULT_COMPILED_EFFICIENCY, DEFAULT_COMPILED_EFFICIENCY),
    )
    assert device.raw_joint_distribution == reference.raw_joint_distribution
    for station, emission, normal, t in zip(
        ("alice", "bob"),
        device.device_artifacts,
        reference.device_artifacts,
        (DEFAULT_FACTOR_THREE_FIFTHS, DEFAULT_FACTOR_ONE_FIFTH),
        strict=True,
    ):
        ours, theirs = emission.reduction, normal.reduction
        assert ours.target_povm == theirs.target_povm, station
        assert ours.wpfss_data == theirs.wpfss_data, station
        assert ours.constraint_list == theirs.constraint_list, station
        assert ours.transported_operators == theirs.transported_operators, station
        assert ours.attack_set_license == theirs.attack_set_license, station
        (link,) = ours.reduction_chain.links
        (plain,) = theirs.reduction_chain.links
        witness: ChannelWitness = link.channel_witness
        assert witness.identity == plain.channel_witness.identity
        assert plain.channel_witness.precomposed_with is None
        assert witness.precomposed_with is not None
        record = witness.as_machine_record()
        loss = record["precomposed_with"]
        assert isinstance(loss, dict)
        assert loss["factored_loss"] == str(t)
        assert "factored_loss" not in plain.channel_witness.as_machine_record()
        assert all(
            pullback == f"Lambda^loss_t^dagger({original})"
            for pullback, original in zip(
                link.carried_operator_pair[1],
                plain.carried_operator_pair[1],
                strict=True,
            )
        )
        assert link.carried_operator_pair[0] == plain.carried_operator_pair[0]
        assert "RECEIVER'S measurement" in link.source_family.description
        assert "Lambda o Lambda^loss_t" in link.reachable_set_statement
        assert ours.squashing_channel == witness


#: Mismatched per-port efficiencies, so that the normalized station's ports
#: differ (at the default ``t = 20/33``: 99/100, 33/40, 99/100 and 33/50), and
#: a dark count in every port, so that the dark counts act after the loss on
#: every letter.
MISMATCHED = {"H": F(3, 5), "V": F(1, 2), "D": F(3, 5), "A": F(2, 5)}
NOISE = dict.fromkeys(PORTS, F(1, 10**4))
#: Each library model that evaluates the emitted measurement, on the instance
#: that ships it: its model and device parameters, and the device parameters
#: that declare every station at ``t = 1``.
LIBRARY_CASES: dict[
    str, tuple[str, dict[str, object], dict[str, object], dict[str, object]]
] = {
    "spdc_pair": (
        "bbm92",
        {"alice_transmittance": F(1, 10), "bob_transmittance": F(1, 100)},
        {
            "source_model": "spdc",
            "alice_efficiency": MISMATCHED,
            "bob_efficiency": dict.fromkeys(PORTS, F(1, 5)),
            "alice_dark_count": NOISE,
            "bob_dark_count": NOISE,
        },
        {"alice_efficiency_normalization": F(1), "bob_efficiency_normalization": F(1)},
    ),
    "single_photon_loss_depolarizing": (
        "optical_bb84",
        {"qber": F(3, 100), "transmittance": F(1, 10)},
        {"efficiency": MISMATCHED, "dark_count": NOISE},
        {"efficiency_normalization": F(1)},
    ),
}


def _prepared(
    instance: str, model: dict[str, object], device: dict[str, object]
) -> Preparation:
    import importlib

    surface = importlib.import_module(f"instances.{instance}.surface")
    base = surface.default_config()
    prepared = surface.preparation(
        base.with_(model={**base.model, **model}, device={**base.device, **device})
    )
    assert isinstance(prepared, Preparation), prepared
    return prepared


@pytest.mark.contract
@pytest.mark.parametrize("name", sorted(LIBRARY_CASES))
def test_every_library_model_applies_each_stations_factored_loss(name: str) -> None:
    """req:loss-before-evaluation: the default's law is the device's (t = 1's).

    Mismatched efficiencies and dark counts; two stations at their own t for
    the pair. The two declarations are two binary64 evaluations of one POVM
    (prop:efficiency-normalization (i)), so the laws agree to that rounding.
    """
    instance, model, device, off = LIBRARY_CASES[name]
    default = _prepared(instance, model, device)
    for emission in default.device_artifacts or ():
        assert emission.receiver.efficiency_record.normalization.below_one
    if default.receiver_artifact is not None:
        assert default.receiver_artifact.efficiency_record.normalization.below_one
    normalized = default.raw_joint_distribution
    declared = _prepared(instance, model, {**device, **off}).raw_joint_distribution
    assert normalized is not None and declared is not None
    assert normalized.keys() == declared.keys()
    assert max(abs(normalized[k] - declared[k]) for k in normalized) < ATOL


@pytest.mark.contract
def test_the_reference_companion_carries_the_loss_in_front() -> None:
    """req:normalized-link-record (companion); cor:normalized-flat (iv)."""
    device = _example((F(1, 10), F(1, 1000)), (F(3, 5), F(1, 5)))
    reference = _example(
        DEFAULT_NORMALIZED_TRANSMITTANCES,
        (DEFAULT_COMPILED_EFFICIENCY, DEFAULT_COMPILED_EFFICIENCY),
    )
    for emission, normal, t in zip(
        device.device_artifacts,
        reference.device_artifacts,
        (DEFAULT_FACTOR_THREE_FIFTHS, DEFAULT_FACTOR_ONE_FIFTH),
        strict=True,
    ):
        ours = emission.reduction.reference_companion
        theirs = normal.reduction.reference_companion
        assert ours is not None and theirs is not None
        mine, plain = ours.as_record(), theirs.as_record()
        loss = mine.pop("precomposed_with")
        assert "precomposed_with" not in plain
        assert loss["factored_loss"] == str(t)
        assert mine == plain  # same target, entries, digest, channel identity


@pytest.mark.contract
def test_the_full_normalization_emits_the_efficiency_one_stations_numbers() -> None:
    """cor:normalized-flat at a DECLARED t = eta_max: the ideal stations' numbers.

    The device at efficiencies (3/5, 1/5) declared at ``t = (3/5, 1/5)``
    normalizes to stations at efficiency one; every emitted number of each
    station's reduction artefact and reference companion is theirs, the link
    and the companion carrying the loss in front with its factor.
    """
    device = _example((F(1, 10), F(1, 1000)), (F(3, 5), F(1, 5)), (F(3, 5), F(1, 5)))
    reference = _example(NORMALIZED_TRANSMITTANCES, (F(1), F(1)))
    for station, emission, normal, t in zip(
        ("alice", "bob"),
        device.device_artifacts,
        reference.device_artifacts,
        (F(3, 5), F(1, 5)),
        strict=True,
    ):
        ours, theirs = emission.reduction, normal.reduction
        assert ours.target_povm == theirs.target_povm, station
        assert ours.wpfss_data == theirs.wpfss_data, station
        assert ours.constraint_list == theirs.constraint_list, station
        assert ours.transported_operators == theirs.transported_operators, station
        (link,) = ours.reduction_chain.links
        loss = link.channel_witness.as_machine_record()["precomposed_with"]
        assert isinstance(loss, dict)
        assert loss["factored_loss"] == str(t)
        assert ours.reference_companion is not None
        assert theirs.reference_companion is not None
        mine = ours.reference_companion.as_record()
        plain = theirs.reference_companion.as_record()
        assert mine.pop("precomposed_with")["factored_loss"] == str(t)
        assert mine == plain
