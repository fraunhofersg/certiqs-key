"""A completed two-station record: every record_key resolves, and the final iterate.

runs/record-station-scope and runs/final-iterate-helper, on real runs of the
two instances that exercise them: BBM92 (two stations, the general format,
which carries a final iterate) and BB84 (no device, the one-factor format,
which carries none). The solves run three Frank-Wolfe iterations; nothing
here reads a key rate.
"""

from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from tests.support.manifest_spelling import assert_bindings_in_declared_spelling

from certiqs_key.runs.config import RunConfig, SolverSettings
from certiqs_key.runs.flow import artefact_digest
from certiqs_key.runs.iterate_file import ITERATE_FILE_NAME, attach_final_iterate
from certiqs_key.runs.pipeline import SliceResult
from certiqs_key.runs.record import RunRecord, jsonable, record_run

pytestmark = pytest.mark.requires_qics

SCHEMA = json.loads(
    (
        Path(__file__).resolve().parents[2]
        / "src/certiqs_key/runs/record.schema.json"
    ).read_text(encoding="utf-8")
)
_STEP = re.compile(r"^(?P<key>[^\[\]]+)(?:\[(?P<index>\d+)\])?$")


def _run(instance: str, directory: Path) -> tuple[SliceResult, RunConfig]:
    import importlib

    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = importlib.import_module(f"instances.{instance}.surface")
    config = surface.default_config().with_(
        solver=SolverSettings(method="fw", max_iterations=3)
    )
    outcome = surface.runner(QicsSectorChoiOracle(), directory, created_by="test")(
        config, 0
    )
    assert isinstance(outcome, SliceResult), outcome
    return outcome, config


@pytest.fixture(scope="module")
def two_station(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[SliceResult, RunConfig, RunRecord]:
    outcome, config = _run("bbm92", tmp_path_factory.mktemp("bbm92"))
    return outcome, config, record_run(outcome, config, created_by="test")


def _resolve(document: dict[str, Any], key: str) -> Any:
    """Follow a dotted ``record_key`` with ``[i]`` list steps; KeyError if absent."""
    node: Any = document
    for step in key.split("."):
        match = _STEP.match(step)
        assert match is not None, (key, step)
        node = node[match["key"]]
        if match["index"] is not None:
            node = node[int(match["index"])]
    return node


def test_every_record_key_of_a_two_station_record_resolves(
    two_station: tuple[SliceResult, RunConfig, RunRecord],
) -> None:
    outcome, _config, record = two_station
    document = record.as_dict()
    jsonschema.validate(document, SCHEMA)
    stages = document["payload"]["composition_flow"]["stages"]
    keys = [
        artefact["record_key"]
        for stage in stages
        for artefact in stage["emits"]
        if artefact["record_key"] is not None
    ]
    assert keys
    for key in keys:
        assert _resolve(document, key) is not None, key
    # AND EACH STATION KEY HOLDS THAT STATION'S ARTEFACT, not merely a value:
    # the digest the stage emitted is the digest of what the key holds.
    for stage in stages:
        for artefact in stage["emits"]:
            key = artefact["record_key"]
            if key is None or ".stations[" not in key:
                continue
            index = int(key.split("[", 1)[1].split("]", 1)[0])
            station = document["payload"]["stages"]["stations"][index]
            assert station["factor"] == stage["station"], key
            emission = outcome.device_artifacts[index]
            payload = (
                emission.receiver.as_payload()
                if key.endswith(".receiver")
                else emission.reduction.as_machine_record()
            )
            assert artefact["digest"] == artefact_digest(payload), key
            assert _resolve(document, key) == jsonable(payload), key


def test_the_two_station_record_binds_each_name_once_in_the_declared_spelling(
    two_station: tuple[SliceResult, RunConfig, RunRecord],
) -> None:
    """Each name is bound once, in the declared spelling, on BBM92.

    The acceptance values ``gen:Z|X`` and the like travel as ``gen_Z_X``; the
    engine's A-FIXED and A-CONFORM bind the acceptance alphabet the record's
    acceptance stage holds, and every entry binds each name once.
    """
    _outcome, _config, record = two_station
    document = record.as_dict()
    assert_bindings_in_declared_spelling(document)
    outcomes = document["payload"]["stages"]["acceptance_construction"]["outcomes"]
    assert any(":" in outcome or "|" in outcome for outcome in outcomes)
    bound = [
        binding["value"]["alphabet"]
        for entry in document["payload"]["assumption_manifest"]["assumptions"]
        for binding in entry["bindings"]
        if binding["name"] == "acceptance_set"
    ]
    assert bound and all(alphabet == outcomes for alphabet in bound)


def test_the_per_station_stages_name_their_station(
    two_station: tuple[SliceResult, RunConfig, RunRecord],
) -> None:
    _outcome, _config, record = two_station
    flow = record.payload["composition_flow"]
    named = [(stage["stage"], stage["station"]) for stage in flow["stages"]]
    prologue = [
        (stage, station)
        for station in ("alice_station", "bob_station")
        for stage in ("receiver_construction", "receiver_docking", "reduction")
    ]
    assert named[:6] == prologue
    assert all(station is None for _stage, station in named[6:])
    assert "reduction [bob_station] (reductions) -- ok" in flow["mermaid"]
    # Each station names
    # how its receiver was given; both of BBM92's are element graphs, so the
    # run's route is that one.
    stations = record.payload["stages"]["stations"]
    assert [entry["receiver_route"] for entry in stations] == [
        "element-graph", "element-graph"
    ]
    assert (
        record.payload["stages"]["receiver_construction"]["receiver_route"]
        == "element-graph"
    )


def test_a_general_run_gets_its_final_iterate_file_and_key(
    two_station: tuple[SliceResult, RunConfig, RunRecord],
    tmp_path: Path,
) -> None:
    outcome, config, record = two_station
    attached = attach_final_iterate(record, outcome, config, tmp_path)
    file = tmp_path / ITERATE_FILE_NAME
    assert file.exists()
    assert attached.payload["final_iterate"] == {
        "file": ITERATE_FILE_NAME,
        "sha256": sha256(file.read_bytes()).hexdigest(),
    }
    assert "final_iterate" not in record.payload  # the input is not mutated
    jsonschema.validate(attached.as_dict(), SCHEMA)
    with pytest.raises(FileExistsError):
        attach_final_iterate(record, outcome, config, tmp_path)


def test_an_accepted_format_run_gets_its_final_iterate_too(tmp_path: Path) -> None:
    """One driver: a bb84 run is a completed run like any other.

    It writes the general record, and its final iterate seeds a warm start
    like every other run's.
    """
    outcome, config = _run("bb84", tmp_path / "bundles")
    record = record_run(outcome, config, created_by="test")
    attached = attach_final_iterate(record, outcome, config, tmp_path)
    file = tmp_path / ITERATE_FILE_NAME
    assert file.exists()
    assert attached.payload["final_iterate"] == {
        "file": ITERATE_FILE_NAME,
        "sha256": sha256(file.read_bytes()).hexdigest(),
    }
    jsonschema.validate(attached.as_dict(), SCHEMA)
