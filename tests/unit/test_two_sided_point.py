from __future__ import annotations

import json
from argparse import Namespace
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from runs.two_sided.point import build_config, parser, run_point

from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.record import RunRecord


def _args(tmp_path: Path, *extra: str) -> Namespace:
    return parser().parse_args(
        [
            "--instance", "bbm92", "--route", "licensed", "--loss-db", "10",
            "--rounds", "1000", "--lambda-ec", "0", "--zero-ec-label", "diagnostic",
            "--lambda-ec-purpose", "diagnostic cap; no reconciliation model",
            "--dark-count", "1/1000000", "--source-model", "spdc",
            "--output", str(tmp_path / "point"), *extra,
        ]
    )


def test_bbm_loss_is_total_and_split_symmetrically(tmp_path: Path) -> None:
    _surface, config = build_config(_args(tmp_path))
    assert config.model["alice_transmittance"] == config.model["bob_transmittance"]
    assert abs(float(config.model["alice_transmittance"]) - 10 ** (-0.5)) < 1e-15
    assert config.device["source_model"] == "spdc"
    assert config.solver is not None and config.solver.max_iterations == 2000
    assert config.parameters.lambda_ec == 0
    assert config.endpoint_rule == "bernstein"


def test_bbm92_takes_an_acceptance_map_and_defaults_to_pair_resolved(
    tmp_path: Path,
) -> None:
    _surface, config = build_config(_args(tmp_path))
    assert config.device["acceptance_map"] == "pair-resolved"
    _surface, config = build_config(_args(tmp_path, "--map", "merged-discard"))
    assert config.device["acceptance_map"] == "merged-discard"


def test_zero_ec_requires_a_diagnostic_label(tmp_path: Path) -> None:
    arguments = _args(tmp_path)
    arguments.zero_ec_label = None
    with pytest.raises(ValueError, match="zero-ec-label"):
        build_config(arguments)


def test_mock_runner_writes_one_enriched_record_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    arguments = _args(tmp_path)
    seen = {}

    def builder(
        oracle: object, directory: Path, *, created_by: str
    ) -> Callable[[RunConfig, int], object]:
        seen.update(oracle=oracle, directory=directory, created_by=created_by)
        return lambda config, index: (config, index)

    def recorder(
        outcome: Any, config: RunConfig, *, created_by: str, instance: Any
    ) -> RunRecord:
        assert outcome[0] == config and outcome[1] == 0
        # The point names its instance in the record (record schema 0.20.0).
        assert instance.descriptor.id == "bbm92"
        return RunRecord(
            "run-record", "test", created_by, {"config": "full", "stages": {}}
        )

    written = {}

    def writer(path: Path, record: RunRecord) -> None:
        written.update(path=path, record=record)

    record = run_point(
        arguments, oracle="oracle", runner_builder=builder,
        record_builder=recorder, record_writer=writer,
    )
    assert seen["directory"] == arguments.output / "bundles"
    assert written["path"] == arguments.output / "record.json"
    point = record.payload["two_sided_point"]
    assert isinstance(point, dict)
    assert point["loss_interpretation"].startswith("total symmetric")
    with pytest.raises(FileExistsError):
        run_point(arguments, oracle="oracle", runner_builder=builder)


def test_interruption_retains_request_but_no_completed_record(tmp_path: Path) -> None:
    arguments = _args(tmp_path, "--endpoint-rule", "exact")

    def interrupted(*args: Any, **kwargs: Any) -> Any:
        saved = json.loads((arguments.output / "config.json").read_text())
        assert saved["endpoint_rule"] == "exact"
        assert (arguments.output / "provenance.json").exists()
        raise RuntimeError("interrupted")

    with pytest.raises(RuntimeError, match="interrupted"):
        run_point(arguments, oracle="oracle", runner_builder=interrupted)
    assert not (arguments.output / "record.json").exists()


@pytest.mark.parametrize("loss", ["nan", "inf", "-1"])
def test_invalid_loss_does_not_create_output(tmp_path: Path, loss: str) -> None:
    arguments = _args(tmp_path, "--loss-db", loss)
    with pytest.raises(ValueError, match="finite and non-negative"):
        run_point(arguments, oracle="oracle")
    assert not arguments.output.exists()


def test_a_malformed_set_is_refused(tmp_path: Path) -> None:
    arguments = _args(tmp_path, "--set", "solver.max_iterations=3")
    with pytest.raises(ValueError, match=r"SECTION.KEY=VALUE"):
        build_config(arguments)


def test_alpha_is_declared_or_left_to_the_instance(tmp_path: Path) -> None:
    _surface, config = build_config(_args(tmp_path))
    assert config.alpha is None
    _surface, config = build_config(_args(tmp_path, "--alpha", "1.001"))
    assert config.alpha == 1.001
    with pytest.raises(ValueError, match="alpha"):
        build_config(_args(tmp_path, "--alpha", "1"))
