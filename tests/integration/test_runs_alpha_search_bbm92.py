"""The outer alpha search on a real bbm92 run (certiqs_key.runs.alpha_search).

A small search (three grid points, two refinements) on the ideal device. It
checks the run-tier adapter end to end: every evaluation is a real run at its
own alpha, the chosen record is the run at the chosen alpha, and the search
beats the worst grid point.

The second test is the opt-in setting through the instance's own runner
(``RunConfig.alpha_search``, record schema 0.24.0): the record of the chosen
run says ``searched: true`` in the solve stage's ``alpha`` child with every
evaluation, its key rate is at the chosen alpha, and the report renders it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from instances import surface_of

from certiqs_key.runs.alpha_search import (
    AlphaSearchSettings,
    run_tier_evaluator,
    search_alpha,
)
from certiqs_key.runs.config import SolverSettings
from certiqs_key.runs.record import record_run
from certiqs_key.runs.surface import InstanceIdentity

pytestmark = [pytest.mark.slow, pytest.mark.requires_qics]


def test_the_search_runs_each_alpha_and_keeps_the_best(tmp_path: Path) -> None:
    pytest.importorskip("qics")
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = surface_of("bbm92")
    config = surface.default_config(
        solver=SolverSettings(method="auto", budget_seconds=120)
    )
    runner = surface.runner(QicsSectorChoiOracle(), tmp_path, created_by="test")
    settings = AlphaSearchSettings(
        lower=1e-4, upper=0.1, coarse_points=3, refine_steps=2
    )
    result = search_alpha(
        run_tier_evaluator(config, runner, created_by="test"), settings
    )
    assert len(result.evaluations) == 5
    assert result.chosen is not None
    keys = [e.point.key_length for e in result.evaluations]
    assert all(k is not None and k > 0 for k in keys)
    assert result.chosen.point.key_length == max(k for k in keys if k is not None)
    record = result.chosen.point.run.as_dict()
    payload = record.get("payload", record)
    assert payload["stages"]["key_rate"]["alpha"] == pytest.approx(result.alpha)


def test_the_opt_in_setting_records_the_search_and_the_report_renders_it(
    tmp_path: Path,
) -> None:
    pytest.importorskip("qics")
    from certiqs_key.runs.report import (
        build_report,
        default_contract_link,
        render_markdown,
    )
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = surface_of("bbm92")
    settings = AlphaSearchSettings(
        lower=1e-4, upper=0.1, coarse_points=3, refine_steps=1
    )
    config = surface.default_config(
        solver=SolverSettings(method="auto", budget_seconds=120),
        alpha_search=settings,
    )
    runner = surface.runner(QicsSectorChoiOracle(), tmp_path, created_by="test")
    outcome = runner(config, 0)
    assert not outcome.refuses
    identity = InstanceIdentity(surface.DESCRIPTOR, tuple(surface.PARAMETERS))
    record = record_run(outcome, config, created_by="test", instance=identity)
    payload = record.as_dict()["payload"]
    assert payload["config"]["alpha_search"] == settings.as_payload()
    (solve,) = [
        stage for stage in payload["composition_flow"]["stages"]
        if stage["stage"] == "solve"
    ]
    (alpha,) = [child for child in solve["children"] if child["name"] == "alpha"]
    detail = alpha["detail"]
    assert detail["searched"] is True
    assert len(detail["evaluations"]) == 4
    assert {e["phase"] for e in detail["evaluations"]} == {"coarse", "refine"}
    assert detail["chosen_alpha"] is not None
    assert payload["stages"]["key_rate"]["alpha"] == detail["chosen_alpha"]
    chosen = max(
        (e for e in detail["evaluations"] if e["score"] is not None),
        key=lambda e: e["score"],
    )
    assert chosen["alpha"] == detail["chosen_alpha"]
    assert payload["stages"]["key_rate"]["key_length"] == chosen["key_length"]
    # Each evaluation wrote its own bundle.
    assert sorted(p.name for p in (tmp_path / "run-0000").iterdir()) == [
        f"alpha-{k:02d}" for k in range(4)
    ]

    report = build_report(record.as_dict())
    used = report["sections"]["result"]["alpha"]
    assert used["chosen_by"] == "outer-search"
    assert used["runs"] == 4
    assert used["value"] == detail["chosen_alpha"]
    text = render_markdown(report, contract_link=default_contract_link())
    assert "the outer alpha search" in text
    assert "Alpha search" in text
