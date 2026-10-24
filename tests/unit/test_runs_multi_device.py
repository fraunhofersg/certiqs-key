"""The run tier retains every station before asking the instance to compose.

A multi-station request declares which measured factor each
station is (``DeviceRequests.station``) and the run tier holds that against
the compiled declaration, so these tests compose a real two-factor
declaration -- BBM92's two stations -- rather than a one-factor one built
from the first station alone.
"""

import json
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest
from instances.bbm92.surface import default_config
from tests.support.lowered_templates import lowered

from certiqs_key.protocol_compiler.spec import ProtocolSpecification
from certiqs_key.runs.errors import SliceAssemblyError
from certiqs_key.runs.pipeline import (
    DeviceEmission,
    DeviceRequests,
    MultiDeviceRequests,
    MultiSpecificationProvider,
    Preparation,
    SliceRefusal,
    SliceStage,
    Station,
    prepare,
)
from certiqs_key.runs.record import preparation_record, record_run


def _lowered() -> MultiDeviceRequests:
    """BBM92's two stations and provider: the template's lowering at its defaults.

    Both stations at cutoff 1 with the exact window at 2, at the instance's
    declared tolerance.
    """
    device = lowered("bbm92", default_config())[1].device
    assert isinstance(device, MultiDeviceRequests)
    return device


def _stations() -> tuple[DeviceRequests, DeviceRequests]:
    alice, bob = _lowered().devices
    for station in (alice, bob):
        assert station.receiver_request.photon_cutoff == 1
        assert dict(station.receiver_request.exact_window) == {"off": 2}
    return alice, bob


def _compose(seen: list[DeviceEmission]) -> MultiSpecificationProvider:
    provider = _lowered().specification_provider

    def compose(emissions: tuple[DeviceEmission, ...]) -> ProtocolSpecification:
        seen.extend(emissions)
        return provider(emissions)

    return compose


def test_both_station_emissions_reach_provider_and_preparation_record() -> None:
    seen: list[DeviceEmission] = []
    result = prepare(
        default_config(), device=MultiDeviceRequests(_stations(), _compose(seen))
    )
    assert isinstance(result, Preparation)
    assert len(seen) == 2
    assert result.device_artifacts == tuple(seen)
    assert seen[0].receiver is not seen[1].receiver
    record = preparation_record(result)
    assert len(record["stations"]) == 2
    for item in record["stations"]:
        assert item["receiver"]["mathematical_spec_version"]
        assert item["reduction"]["assumption_ledger"]
        assert item["rows_adaptation"]


def test_each_station_names_its_declared_factor_and_party() -> None:
    """runs/station-party: the record states the pairing; nobody infers it."""
    result = prepare(
        default_config(), device=MultiDeviceRequests(_stations(), _compose([]))
    )
    assert isinstance(result, Preparation)
    declaration = result.declaration
    declared = {
        label: factor.party
        for label, factor in zip(
            declaration.measured_factor_labels,
            declaration.measured_factors,
            strict=True,
        )
    }
    stations = preparation_record(result)["stations"]
    assert {item["factor"]: item["party"] for item in stations} == declared
    assert [item["factor"] for item in stations] == ["alice_station", "bob_station"]
    assert [item["party"] for item in stations] == ["A", "B"]


@pytest.mark.parametrize(
    ("station", "match"),
    [
        (Station(factor="alice_station", party="B"), "scopes that factor"),
        (Station(factor="carol_station", party="A"), "measured factors"),
    ],
)
def test_a_station_the_declaration_disagrees_with_is_a_composition_error(
    station: Station, match: str
) -> None:
    alice, bob = _stations()
    device = MultiDeviceRequests((replace(alice, station=station), bob), _compose([]))
    with pytest.raises(SliceAssemblyError, match=match):
        prepare(default_config(), device=device)


def test_a_multi_station_request_names_every_station_once() -> None:
    alice, bob = _stations()
    with pytest.raises(SliceAssemblyError, match="declares which"):
        MultiDeviceRequests((replace(alice, station=None), bob), _compose([]))
    with pytest.raises(SliceAssemblyError, match="each measured factor"):
        MultiDeviceRequests((replace(alice, station=bob.station), bob), _compose([]))


def test_the_single_device_route_refuses_a_station_identity() -> None:
    alice, _bob = _stations()

    def unexpected(*_: object) -> ProtocolSpecification:
        pytest.fail("the station must be refused before anything runs")

    with pytest.raises(SliceAssemblyError, match="single-device route"):
        prepare(default_config(), device=alice, specification_provider=unexpected)


def test_refused_second_station_keeps_first_station(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import certiqs_key.runs.pipeline as pipeline

    config = default_config()
    original = pipeline._run_device_prologue
    calls = 0

    def prologue(*args: object, **kwargs: object) -> DeviceEmission | SliceRefusal:
        nonlocal calls
        calls += 1
        if calls == 2:
            return SliceRefusal(
                stage=SliceStage.REDUCTION,
                reason="test_supplier_refusal",
                detail="Second station declined.",
            )
        return original(*args, **kwargs)  # type: ignore[arg-type]

    def unexpected(_: tuple[DeviceEmission, ...]) -> ProtocolSpecification:
        pytest.fail("composition must wait until both stations emit")

    monkeypatch.setattr(pipeline, "_run_device_prologue", prologue)
    result = prepare(config, device=MultiDeviceRequests(_stations(), unexpected))
    assert isinstance(result, SliceRefusal)
    assert len(result.device_artifacts) == 1
    assert len(preparation_record(result)["stations"]) == 1
    # THE SECOND STATION'S PROLOGUE IS NOT "SEEN" because the first ran it:
    # its three stages are listed, by station, as not executed.
    tail = [
        (str(stage.stage), stage.station, str(stage.status))
        for stage in result.stages
        if stage.station == "bob_station"
    ]
    assert tail == [
        ("receiver_construction", "bob_station", "not_executed"),
        ("receiver_docking", "bob_station", "not_executed"),
        ("reduction", "bob_station", "not_executed"),
    ]
    record = record_run(result, config, created_by="test").as_dict()
    assert len(record["payload"]["stages"]["stations"]) == 1
    schema = Path(pipeline.__file__).with_name("record.schema.json")
    jsonschema.validate(record, json.loads(schema.read_text(encoding="utf-8")))
