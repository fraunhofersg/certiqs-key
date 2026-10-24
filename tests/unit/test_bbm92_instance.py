"""The BBM92 physical declaration and exact ideal-pair statistics.

The stations' device requests and the two-station specification provider are the bbm92
template's lowering: the stations at the template's defaults, cutoff 1 with the exact
window at 2.
"""

from fractions import Fraction as F
from typing import Any

import pytest
from instances.bbm92.surface import default_config
from instances.common.honest.ideal_pair import (
    IdealPair,
    honest_provider,
    ideal_pair_block,
)
from tests.support.lowered_templates import lowered

from certiqs_key.foundations.exact import is_positive_semidefinite, trace
from certiqs_key.protocol_compiler.compile import compile_specification
from certiqs_key.receiver.construct import construct_receiver
from certiqs_key.reductions.inputs import ReductionCall
from certiqs_key.runs.pipeline import (
    AdapterRefusal,
    DeviceEmission,
    MultiDeviceRequests,
    MultiSpecificationProvider,
)


def _lowered_device(**device: Any) -> MultiDeviceRequests:
    """Return the template's two stations and provider at the default device."""
    config = default_config()
    config = config.with_(device={**config.device, **device})
    lowering = lowered("bbm92", config)[1].device
    assert isinstance(lowering, MultiDeviceRequests)
    return lowering


def specification_provider(**device: Any) -> MultiSpecificationProvider:
    """Return the two-station specification provider at one device section."""
    return _lowered_device(**device).specification_provider


@pytest.fixture(scope="module")
def station_artifacts() -> tuple[DeviceEmission, ...]:
    stations = _lowered_device().devices
    assert all(
        request.receiver_request.photon_cutoff == 1
        and dict(request.receiver_request.exact_window) == {"off": 2}
        for request in stations
    )
    artifacts = []
    for request in stations:
        receiver = construct_receiver(request.receiver_request)
        assert receiver.refusal is None
        assert receiver.artifact is not None
        assert request.rows_adapter is not None
        adapted = request.rows_adapter(receiver.artifact)
        assert not isinstance(adapted, AdapterRefusal)
        call = ReductionCall(
            adapted.rows, request.reduction_declaration, request.reduction_request
        )
        reduction = request.reduction_entry(call)
        assert reduction.refusal is None
        assert reduction.artifact is not None
        artifacts.append(
            DeviceEmission(
                receiver=receiver.artifact,
                reduction=reduction.artifact,
                call=call,
                rows_adaptation=adapted.report,
                upstream=(),
                station=request.station,
            )
        )
    return tuple(artifacts)


@pytest.mark.parametrize(
    "eta_a,eta_b,v",
    [(F(1), F(1), F(1)), (F(1, 2), F(1, 4), F(3, 4)), (F(0), F(1), F(1))],
)
def test_ideal_pair_erasure_components_are_normalized_and_positive(
    eta_a: F, eta_b: F, v: F
):
    block = ideal_pair_block(3, 3, IdealPair(eta_a, eta_b, v))
    assert trace(block).re == 1
    assert is_positive_semidefinite(block)
    assert block[0][0].re == (1 - eta_a) * (1 - eta_b)
    assert sum(block[i][i].re for i in (3, 6)) == eta_a * (1 - eta_b)
    assert sum(block[i][i].re for i in (1, 2)) == (1 - eta_a) * eta_b
    assert sum(block[i][i].re for i in (4, 5, 7, 8)) == eta_a * eta_b


def test_two_optical_stations_compile_with_local_readouts(
    station_artifacts: tuple[DeviceEmission, ...],
):
    specification = specification_provider(test_fraction=F(1, 8))(station_artifacts)
    compiled = compile_specification(specification)
    assert compiled.refusal is None, compiled.refusal
    declaration = compiled.declaration
    assert declaration is not None
    assert declaration.alice_dim == 1
    assert declaration.alice_marginal is None
    assert len(declaration.measured_factors) == 2
    assert (
        declaration.partition.alice_readout_alphabet
        != declaration.partition.bob_readout_alphabet
    )


def test_spdc_uses_the_actual_station_grams(
    station_artifacts: tuple[DeviceEmission, ...],
):
    from instances.common.honest.spdc_pair import (
        SpdcModel,
        click_distribution,
        coarse_distribution,
        prepare_station_grams,
    )

    left, right = station_artifacts[0].receiver, station_artifacts[1].receiver
    a, a_record = prepare_station_grams(left, tolerance=1e-12)
    b, b_record = prepare_station_grams(right, tolerance=1e-12)
    patterns = click_distribution(
        a, b, SpdcModel(), alice_dark=(F(0),) * 4, bob_dark=(F(0),) * 4
    )
    coarse = coarse_distribution(patterns, left, right)
    assert sum(coarse.values(), F(0)) == 1
    assert coarse[("nc", "nc")] == 1 / (1 + F(1, 64)) ** 2
    assert a_record["snaps"] and b_record["snaps"]


@pytest.mark.parametrize("bases,expected", [(("Z",), F(7, 32)), (("Z", "X"), F(7, 16))])
def test_actual_ideal_pair_generation_mass(
    station_artifacts: tuple[DeviceEmission, ...], bases: tuple[str, ...], expected: F
):
    compiled = compile_specification(
        specification_provider(key_bases="".join(bases))(station_artifacts)
    )
    assert compiled.declaration is not None
    frequencies = honest_provider(IdealPair())(compiled.declaration)
    assert frequencies["gen"] == expected
    assert sum(frequencies.values(), F(0)) == 1
