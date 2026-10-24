"""The outer alpha search wired into the configuration, runner, record and report.

The search is an engine feature of the run tier and an opt-in setting; the
declared alpha stays the default. What is held here, without a
solver:

* the configuration carries ``alpha_search`` only where set, refuses it beside
  a fixed ``alpha`` and refuses settings that are not ones, each with its code;
  a configuration without it keeps the payload, and so the digest, it had;
* :func:`~certiqs_key.runs.alpha_search.searching_runner` runs a configuration
  without the search once, and one with it once per searched alpha, each into
  its own bundle directory, returning the chosen run's own outcome with the
  search attached -- or the first evaluation's where every one refused;
* the record carries the search in the solve stage's ``alpha`` child and
  validates against ``record.schema.json``;
* the report says the order was chosen by the outer search, with the range,
  the number of runs and every evaluation.

The search on a real instance is ``tests/integration/test_runs_alpha_search_bbm92.py``.
"""

from __future__ import annotations

import importlib
import json
import math
from dataclasses import dataclass
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from tests.support.report_records import completed_record, synthetic_table
from tests.unit.test_run_parameters import RUNNER_MODULES

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.alpha_search import (
    AlphaSearchError,
    AlphaSearchSettings,
    searching_runner,
)
from certiqs_key.runs.config import RunConfig, RunConfigError, canonical_json
from certiqs_key.runs.errors import RunInputReason
from certiqs_key.runs.flow import StageChild, StageRecord, StageStatus
from certiqs_key.runs.pipeline import SliceRefusal
from certiqs_key.runs.record import record_run
from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_markdown,
    report_schema,
)
from certiqs_key.runs.stages import SliceStage

pytestmark = pytest.mark.contract

jsonschema = pytest.importorskip("jsonschema")

ROOT = Path(__file__).resolve().parents[2]
SMALL = AlphaSearchSettings(lower=1e-4, upper=0.1, coarse_points=3, refine_steps=1)


def config(**changes: object) -> RunConfig:
    """Return the configuration this file varies from."""
    base = {
        "rounds": 10_000,
        "completeness_budget": F(1, 1_000_000),
        "parameters": KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=7
        ),
        "declared_tolerance": 1e-12,
    }
    return RunConfig(**{**base, **changes})  # type: ignore[arg-type]


# ===========================================================================
#  The configuration
# ===========================================================================


def test_a_configuration_without_the_search_keeps_its_payload_and_digest() -> None:
    """The payload is stated by hand: no ``alpha_search`` key, nothing else new."""
    expected = {
        "rounds": 10_000,
        "completeness_budget": "1/1000000",
        "parameters": {
            "alpha": 1.5,
            "eps_pa": 2.0**-30,
            "eps_ev": 2.0**-30,
            "lambda_ec": 7,
        },
        "model": {},
        "device": {},
        "declared_tolerance": 1e-12,
        "alpha": None,
        "constrained": None,
        "solver": None,
        "endpoint_rule": "exact",
        "tail_evaluation": "sweep",
    }
    plain = config()
    assert plain.alpha_search is None
    assert plain.to_payload() == expected
    assert plain.digest() == sha256(canonical_json(expected).encode()).hexdigest()
    # Setting and removing the search returns the same request.
    assert plain.with_(alpha_search=SMALL).with_(alpha_search=None) == plain


def test_the_search_round_trips_and_is_part_of_the_request() -> None:
    searched = config(alpha_search=SMALL)
    payload = searched.to_payload()
    assert payload["alpha_search"] == {
        "lower_alpha_minus_one": 1e-4,
        "upper_alpha_minus_one": 0.1,
        "coarse_points": 3,
        "refine_steps": 1,
    }
    assert payload["alpha"] is None
    assert RunConfig.from_payload(json.loads(json.dumps(payload))) == searched
    assert searched.digest() != config().digest()


def test_a_searched_configuration_is_a_valid_run_request() -> None:
    """The run-input schema (what the MCP server's agents write) admits it."""
    from instances.bb84.surface import default_config

    path = ROOT / "src" / "certiqs_key" / "runs" / "run-input.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(
        {**schema, "$ref": "#/$defs/run_request"}
    )
    payload = default_config(alpha_search=SMALL).to_payload()
    validator.validate({"instance": "bb84", "config": payload})
    payload["alpha_search"]["lower"] = 1e-4
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({"instance": "bb84", "config": payload})


def test_an_absent_key_of_the_block_reads_its_default() -> None:
    assert AlphaSearchSettings.from_payload({}) == AlphaSearchSettings()
    assert AlphaSearchSettings.from_payload({"coarse_points": 4}) == (
        AlphaSearchSettings(coarse_points=4)
    )


def test_alpha_and_a_search_together_are_refused() -> None:
    with pytest.raises(RunConfigError) as caught:
        config(alpha=1.01, alpha_search=SMALL)
    assert caught.value.reason is RunInputReason.ALPHA_AND_ALPHA_SEARCH_BOTH_SET
    with pytest.raises(RunConfigError):
        config(alpha_search=SMALL).with_(alpha=1.01)


@pytest.mark.parametrize(
    "payload",
    [
        {"lower_alpha_minus_one": 0.0},
        {"lower_alpha_minus_one": 0.2, "upper_alpha_minus_one": 0.1},
        {"upper_alpha_minus_one": 1.0},
        {"coarse_points": 1},
        {"coarse_points": 2.5},
        {"refine_steps": -1},
        {"refine_steps": True},
        {"lower_alpha_minus_one": "1e-4"},
        {"lower": 1e-4},
    ],
)
def test_a_search_setting_that_is_not_one_is_refused_with_its_code(
    payload: dict[str, Any],
) -> None:
    with pytest.raises(AlphaSearchError) as caught:
        AlphaSearchSettings.from_payload(payload)
    assert caught.value.reason is RunInputReason.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN
    assert isinstance(caught.value, ValueError)


def test_a_search_that_is_not_settings_is_refused() -> None:
    with pytest.raises(RunConfigError) as caught:
        config(alpha_search={"coarse_points": 3})
    assert caught.value.reason is RunInputReason.ALPHA_SEARCH_SETTING_OUT_OF_DOMAIN


# ===========================================================================
#  The runner
# ===========================================================================


@dataclass(frozen=True)
class _Ran:
    """A stand-in completed outcome: what the search reads and attaches to."""

    key_rate: Any
    bundle: Path
    stages: tuple[StageRecord, ...] = ()
    alpha_search: Any = None


def _solve(
    *children: StageChild, status: StageStatus = StageStatus.EXECUTED
) -> StageRecord:
    return StageRecord(
        stage=SliceStage.SOLVE, module="meat-core", status=status, children=children
    )


def _peaked(calls: list[tuple[float, Path]], at: float = 3e-3) -> Any:
    """Return a one-alpha run whose key length peaks at ``alpha - 1 = at``."""

    def run_at(point: RunConfig, bundle: Path) -> _Ran:
        assert point.alpha_search is None and point.alpha is not None
        calls.append((point.alpha, bundle))
        t = math.log(point.alpha - 1.0) - math.log(at)
        key_length = int(1e6 - 1e5 * t * t)
        rate = SimpleNamespace(
            key_length=key_length, h_lb=0.4, h_low=0.4, reference_bracket=None,
            rounds=point.rounds,
            alpha=point.alpha,
            key_length_reason_code="first_order_reported",
        )
        child = StageChild(
            name="alpha", status="chosen",
            detail={"alpha": point.alpha, "key_length": key_length, "searched": False},
        )
        return _Ran(key_rate=rate, bundle=bundle, stages=(_solve(child),))

    return run_at


def test_without_the_search_the_runner_runs_once_where_it_always_did(
    tmp_path: Path,
) -> None:
    calls: list[tuple[float, Path]] = []
    run = searching_runner(_peaked(calls), tmp_path)
    outcome = run(config(alpha=1.01), 3)
    assert calls == [(1.01, tmp_path / "run-0003")]
    assert outcome.alpha_search is None


def test_the_search_runs_each_alpha_in_its_own_directory_and_keeps_the_best(
    tmp_path: Path,
) -> None:
    calls: list[tuple[float, Path]] = []
    run = searching_runner(_peaked(calls), tmp_path)
    outcome: Any = run(config(alpha_search=SMALL), 0)
    # Three grid points and one refinement, each its own run and directory.
    assert len(calls) == 4
    assert [bundle for _, bundle in calls] == [
        tmp_path / "run-0000" / f"alpha-{k:02d}" for k in range(4)
    ]
    search = outcome.alpha_search
    assert search is not None and search.chosen is not None
    lengths = {alpha: e.point.key_length for alpha, e in
               ((e.alpha, e) for e in search.evaluations)}
    best = max(lengths, key=lambda a: lengths[a] or -1)
    # The outcome returned is the chosen run's own.
    assert search.alpha == best == outcome.key_rate.alpha
    assert outcome.bundle == dict(calls)[best]
    # The others' runs are not carried.
    assert all(e.point.run is None for e in search.evaluations)
    (solve,) = outcome.stages
    (child,) = solve.children
    assert child.status == "chosen"
    assert child.detail["searched"] is True
    assert child.detail["chosen_alpha"] == best
    assert child.detail["alpha"] == best
    assert [e["alpha"] for e in child.detail["evaluations"]] == [a for a, _ in calls]
    assert child.detail["settings"] == SMALL.as_payload()


def test_a_search_in_which_every_alpha_refused_returns_the_first_refusal(
    tmp_path: Path,
) -> None:
    seen: list[Path] = []

    def refuse(point: RunConfig, bundle: Path) -> SliceRefusal:
        seen.append(bundle)
        return SliceRefusal(
            stage=SliceStage.SOLVE,
            reason="negative_objective",
            detail=f"at alpha {point.alpha}",
            stages=(_solve(status=StageStatus.REFUSED),),
        )

    outcome = searching_runner(refuse, tmp_path)(config(alpha_search=SMALL), 0)
    assert isinstance(outcome, SliceRefusal)
    # No grid point scored, so no refinement ran.
    assert len(seen) == SMALL.coarse_points
    assert outcome.detail == f"at alpha {1.0 + SMALL.lower}"
    assert outcome.alpha_search is not None and outcome.alpha_search.chosen is None
    (solve,) = outcome.stages
    (child,) = solve.children
    assert child.name == "alpha" and child.status == "none_chosen"
    assert child.detail["chosen_alpha"] is None
    assert {e["reason"] for e in child.detail["evaluations"]} == {
        "solve: negative_objective"
    }


@pytest.mark.parametrize("instance", sorted(RUNNER_MODULES))
def test_every_instance_runner_runs_the_search(
    instance: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every instance gets the feature through its own runner, not only bbm92.

    The stand-in ``run_slice`` refuses at once, so the search spends only its
    grid; what is held is that each grid point reached ``run_slice`` at its
    own alpha and in its own bundle directory.
    """
    surface = importlib.import_module(f"instances.{instance}.surface")
    caller = importlib.import_module(RUNNER_MODULES[instance])
    seen: list[tuple[float | None, Path]] = []

    def stand_in(*_: Any, **keywords: Any) -> SliceRefusal:
        seen.append((keywords["alpha"], keywords["directory"]))
        return SliceRefusal(stage=SliceStage.COMPILATION, reason="r", detail="d")

    monkeypatch.setattr(caller, "run_slice", stand_in)
    run = surface.runner(object(), tmp_path, created_by="test")
    outcome = run(surface.default_config(alpha_search=SMALL), 2)
    # search_alpha evaluates each grid point at twelve significant digits.
    assert [alpha for alpha, _ in seen] == [
        float(f"{alpha:.12g}") for alpha in SMALL.coarse_grid()
    ]
    assert [path for _, path in seen] == [
        tmp_path / "run-0002" / f"alpha-{k:02d}" for k in range(SMALL.coarse_points)
    ]
    assert outcome.alpha_search is not None
    assert len(outcome.alpha_search.evaluations) == SMALL.coarse_points


# ===========================================================================
#  The record
# ===========================================================================


def _record_schema() -> dict[str, Any]:
    path = ROOT / "src" / "certiqs_key" / "runs" / "record.schema.json"
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def test_a_searched_refusal_records_the_search_and_validates(tmp_path: Path) -> None:
    def refuse(point: RunConfig, bundle: Path) -> SliceRefusal:
        return SliceRefusal(
            stage=SliceStage.COMPILATION,
            reason="specification_malformed",
            detail="d",
            stages=(_solve(status=StageStatus.NOT_EXECUTED),),
        )

    searched = config(alpha_search=SMALL, model={"qber": F(1, 50)})
    outcome = searching_runner(refuse, tmp_path)(searched, 0)
    record = record_run(outcome, searched, created_by="test").as_dict()
    jsonschema.validate(record, _record_schema())
    payload = record["payload"]
    assert payload["config"]["alpha_search"] == SMALL.as_payload()
    assert payload["config"]["alpha"] is None
    assert payload["config"]["config_digest"] == searched.digest()
    (solve,) = payload["composition_flow"]["stages"]
    (child,) = solve["children"]
    assert child["detail"]["searched"] is True
    assert len(child["detail"]["evaluations"]) == SMALL.coarse_points


def test_a_record_without_the_search_writes_no_alpha_search_key() -> None:
    refusal = SliceRefusal(stage=SliceStage.COMPILATION, reason="r", detail="d")
    record = record_run(refusal, config(), created_by="test").as_dict()
    assert "alpha_search" not in record["payload"]["config"]


# ===========================================================================
#  The report
# ===========================================================================


def _searched_record() -> dict[str, Any]:
    """Return a hand-written completed record whose alpha the outer search chose."""
    evaluations = [
        {"alpha": 1.0001, "phase": "coarse", "key_length": 100, "h_lb": 0.5,
         "score": 100.0, "reason": "first_order_reported", "seconds": 1.0},
        {"alpha": 1.01, "phase": "coarse", "key_length": 300, "h_lb": 0.6,
         "score": 300.0, "reason": "first_order_reported", "seconds": 1.5},
        {"alpha": 1.1, "phase": "coarse", "key_length": None, "h_lb": None,
         "score": None, "reason": "solve: negative_objective", "seconds": 0.5},
        {"alpha": 1.03, "phase": "refine", "key_length": 250, "h_lb": 0.58,
         "score": 250.0, "reason": "first_order_reported", "seconds": 1.2},
    ]

    def edit(record: dict[str, Any]) -> None:
        payload = record["payload"]
        payload["config"]["alpha"] = None
        payload["config"]["alpha_search"] = {
            "lower_alpha_minus_one": 1e-4, "upper_alpha_minus_one": 0.1,
            "coarse_points": 3, "refine_steps": 1,
        }
        payload["stages"]["key_rate"]["alpha"] = 1.01
        payload["composition_flow"]["stages"][0]["children"] = [{
            "name": "alpha", "status": "chosen", "wall_time_s": None,
            "detail": {
                "alpha": 1.01, "searched": True, "rule": "the rule",
                "reads": "the honest model",
                "settings": payload["config"]["alpha_search"],
                "chosen_alpha": 1.01, "evaluations": evaluations,
            },
        }]

    return completed_record(edit=edit)


def test_the_report_says_the_outer_search_chose_alpha() -> None:
    built = build_report(_searched_record(), table=synthetic_table())
    jsonschema.validate(built, report_schema())
    assert built["sections"]["result"]["alpha"] == {
        "value": 1.01,
        "chosen_by": "outer-search",
        "searched_range": [1.0001, 1.1],
        "runs": 4,
        "pointer": "/payload/stages/key_rate/alpha",
        "no_positive_key": None,
    }
    search = built["sections"]["numerics"]["alpha_search"]
    assert search is not None
    assert search["pointer"] == "/payload/composition_flow/stages/0/children/0/detail"
    assert search["chosen_alpha"] == 1.01
    assert [row["alpha"] for row in search["evaluations"]] == [1.0001, 1.01, 1.1, 1.03]
    names = {row["name"] for row in built["sections"]["protocol"]["inputs"]}
    assert {"alpha_search.coarse_points", "alpha_search.refine_steps"} <= names
    text = render_markdown(built, contract_link=default_contract_link())
    assert "the outer alpha search" in text
    assert "Alpha search" in text
    assert "solve: negative\\_objective" in text or "solve: negative_objective" in text


def test_a_report_at_one_alpha_names_the_declaration_or_the_configuration() -> None:
    built = build_report(completed_record(), table=synthetic_table())
    alpha = built["sections"]["result"]["alpha"]
    # The synthetic record fixes config.alpha = 1.5.
    assert alpha["chosen_by"] == "configuration"
    assert alpha["value"] == 1.5
    assert alpha["runs"] is None and alpha["searched_range"] is None
    assert built["sections"]["numerics"]["alpha_search"] is None

    def declared(record: dict[str, Any]) -> None:
        record["payload"]["config"]["alpha"] = None

    alpha = build_report(completed_record(edit=declared), table=synthetic_table())[
        "sections"
    ]["result"]["alpha"]
    assert alpha["chosen_by"] == "declaration"
