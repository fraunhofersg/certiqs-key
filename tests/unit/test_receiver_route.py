"""The record names how the run's receiver was given: one test per route.

``stages.receiver_construction.receiver_route`` (record schema 0.20.0) is
derived at record time from the artefact's presences, which the receiver's
interface fixes (``receiver/def:compile``'s three input routes; the outputs
table's ``receiver_construction`` presence rule; ``req:residual-emission``):
the element graph carries a construction, the instrument matrix the residuals
``r_1`` and ``r_3`` without one, the port Grams neither; a run with no receiver
artefact took Band A's declared finite POVM. The key-rate report's
``receiver-route`` check reads it ("the report's checks section must
record it"). Each expectation below is the route the REQUEST declared, read off
the request and never off the function under test.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from types import SimpleNamespace

import pytest
from probe_presence import with_probe
from receiver_povm_support import (
    bb84_channel_only_request,
    probe_free_matrix_request,
    probe_receiver_request,
)

from certiqs_key.receiver import GramFamily, ReceiverRequest, construct_receiver
from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
from certiqs_key.receiver.request import InputRoute
from certiqs_key.runs.record import RECEIVER_ROUTES, receiver_route

pytestmark = pytest.mark.contract

#: The route-(ii) receivers: the probe-free one in every tree, the probe
#: receiver where the removable probe-conditioning submodule is present.
MATRIX_REQUESTS = (probe_free_matrix_request, *with_probe(probe_receiver_request))


def _artifact(request: ReceiverRequest) -> ReceiverMeasurementArtifact:
    emission = construct_receiver(request)
    assert emission.refusal is None, emission.refusal
    assert emission.artifact is not None
    return emission.artifact


def _single(artifact: ReceiverMeasurementArtifact | None) -> SimpleNamespace:
    """Return a finished single-device run, as far as the route reads it."""
    return SimpleNamespace(receiver_artifact=artifact, device_artifacts=())


def _stations(*artifacts: ReceiverMeasurementArtifact) -> SimpleNamespace:
    """Return a two-station run: no single receiver, one per station."""
    return SimpleNamespace(
        receiver_artifact=None,
        device_artifacts=tuple(SimpleNamespace(receiver=a) for a in artifacts),
    )


def _port_grams_request(build: Callable[[], ReceiverRequest]) -> ReceiverRequest:
    """Return a route-(ii) receiver with its Grams supplied directly (route (i))."""
    supplied = _artifact(build())
    family = GramFamily(
        tuple(label for label, _ in supplied.port_grams),
        tuple(matrix for _, matrix in supplied.port_grams),
    )
    return replace(build(), instrument_matrix=None, port_grams=family)


def test_the_requests_declare_the_three_routes() -> None:
    """The fixtures are what their names say: each declares one route."""
    assert bb84_channel_only_request().element_graph is not None
    for build in MATRIX_REQUESTS:
        assert build().instrument_matrix is not None
        request = _port_grams_request(build)
        assert request.port_grams is not None
        assert request.instrument_matrix is None and request.element_graph is None
    assert {str(route) for route in InputRoute} == {
        "port_grams", "instrument_matrix", "element_graph",
    }


def test_an_element_graph_is_recorded_as_one() -> None:
    artifact = _artifact(bb84_channel_only_request())
    assert receiver_route(_single(artifact)) == "element-graph"


def test_an_instrument_matrix_is_recorded_as_one() -> None:
    for build in MATRIX_REQUESTS:
        artifact = _artifact(build())
        assert receiver_route(_single(artifact)) == "instrument-matrix"


def test_port_grams_are_recorded_as_such() -> None:
    for build in MATRIX_REQUESTS:
        artifact = _artifact(_port_grams_request(build))
        assert receiver_route(_single(artifact)) == "port-grams"


def test_no_receiver_artefact_is_band_a_s_declared_povm() -> None:
    assert receiver_route(_single(None)) == "declared-finite-povm"


def test_stations_on_one_route_name_it_and_on_two_say_per_station() -> None:
    graph = _artifact(bb84_channel_only_request())
    assert receiver_route(_stations(graph, graph)) == "element-graph"
    for build in MATRIX_REQUESTS:
        matrix = _artifact(build())
        assert receiver_route(_stations(graph, matrix)) == "per-station"


def test_the_closed_list_is_the_schema_s() -> None:
    import json
    from pathlib import Path

    schema = json.loads(
        (Path(__file__).resolve().parents[2] / "src" / "certiqs_key" / "runs"
         / "record.schema.json").read_text(encoding="utf-8")
    )
    stages = schema["$defs"]["payload"]["properties"]["stages"]["properties"]
    declared = stages["receiver_construction"]["properties"]["receiver_route"]["enum"]
    assert tuple(declared) == RECEIVER_ROUTES
    station = stages["stations"]["items"]["properties"]["receiver_route"]["enum"]
    per_run_only = {"declared-finite-povm", "per-station"}
    assert set(station) == set(RECEIVER_ROUTES) - per_run_only


@pytest.mark.parametrize(
    ("route", "expected"),
    [("band-a", "declared-finite-povm"), ("decoy", "element-graph"),
     ("untrusted-two-station", "element-graph")],
)
def test_a_preparation_record_carries_the_route(route: str, expected: str) -> None:
    """The preparation's receiver surface carries the same key as a run's."""
    from tests.support.route_fixtures import preparation

    from certiqs_key.runs.record import preparation_record

    prepared, _config = preparation(route)
    surface = preparation_record(prepared)["receiver_construction"]
    assert surface["receiver_route"] == expected
