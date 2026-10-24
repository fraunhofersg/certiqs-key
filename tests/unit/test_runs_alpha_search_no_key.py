"""The outer alpha search where no alpha gives a key (runs/alpha_search.py).

Module docstring, "NO ALPHA GIVES A KEY": where some evaluation formed a bound
and none reported a positive key length, the search chooses no alpha; the
run reported is the evaluation with the largest ``h_low``, the largest
``h_lb`` (and, where the reported bound is the reference companion's, the
largest bound on the searched declaration) is a diagnostic, and a sentence
says why the key is 0. One positive key length anywhere keeps the choice as
it was. The numbers are hand-written; the shape is that of the small
key-round-mass regime, where the companion's bound is negative while the searched
declaration's is close to h_low, and the best unclamped score sits at the top
of the grid.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from tests.support.report_records import completed_record, synthetic_table

import certiqs_key.runs as runs_package
from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.alpha_search import (
    NO_POSITIVE_KEY_RULE,
    AlphaPoint,
    AlphaSearchSettings,
    search_alpha,
    searching_runner,
)
from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.flow import StageChild, StageRecord, StageStatus
from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_markdown,
    report_schema,
)
from certiqs_key.runs.stages import SliceStage

jsonschema = pytest.importorskip("jsonschema")

#: Three grid points, no refinement: the evaluations are exactly these.
GRID = AlphaSearchSettings(lower=1e-3, upper=0.1, coarse_points=3, refine_steps=0)

#: Per grid alpha: (key length, reported h_lb, h_low, searched h_lb, score).
#: The best score is at the top of the grid (1.1); the largest h_low at 1.01.
ZERO: dict[float, tuple[int, float, float, float, float]] = {
    1.001: (0, -3e-6, 2.0e-6, 1.9e-6, -500.0),
    1.01: (0, -2e-6, 3.0e-6, 2.9e-6, -300.0),
    1.1: (0, -1e-6, 1.0e-6, 0.9e-6, -100.0),
}


def _at(table: dict[float, tuple[int, float, float, float, float]]) -> Any:
    def evaluate(alpha: float) -> AlphaPoint:
        (key,) = [k for k in table if math.isclose(k, alpha, rel_tol=1e-9)]
        key_length, h_lb, h_low, searched, score = table[key]
        return AlphaPoint(
            score=score,
            key_length=key_length,
            h_lb=h_lb,
            h_low=h_low,
            h_lb_searched=searched,
            reason="certified_reported",
        )

    return evaluate


def test_every_score_zero_gives_the_no_key_outcome() -> None:
    result = search_alpha(_at(ZERO), GRID)
    assert [round(e.alpha, 9) for e in result.evaluations] == [1.001, 1.01, 1.1]
    # No alpha is chosen, and the top of the grid (the best score) is not
    # what the run reports: the largest h_low is.
    assert result.chosen is None and result.alpha is None
    assert result.contradiction is None
    reported = result.no_positive_key
    assert reported is not None and reported.alpha == pytest.approx(1.01)
    payload = result.as_payload()
    json.dumps(payload)
    assert payload["chosen_alpha"] is None
    assert payload["no_positive_key_rule"] == NO_POSITIVE_KEY_RULE
    no_key = payload["no_positive_key"]
    assert no_key["reported_alpha"] == pytest.approx(1.01)
    assert no_key["h_low"] == 3.0e-6
    assert no_key["largest_h_lb"]["h_lb"] == -1e-6
    assert no_key["largest_h_lb"]["alpha"] == pytest.approx(1.1)
    assert no_key["largest_h_lb_searched"]["h_lb"] == 2.9e-6
    assert no_key["largest_h_lb_searched"]["alpha"] == pytest.approx(1.01)
    reason = no_key["reason"]
    assert reason.startswith(
        "No alpha the search evaluated gives a positive key length: each of the "
        "3 evaluations that formed a bound reported 0"
    )
    assert "n times the bound the key length is computed from" in reason
    assert "closest is alpha = 1.1, where n h_lb falls 100 bits short" in reason
    assert "the bound reaches 2.9e-06" in reason
    assert "at most -1e-06" in reason
    schema = json.loads(
        (Path(runs_package.__file__).resolve().parent / "record.schema.json")
        .read_text(encoding="utf-8")
    )
    jsonschema.validate(
        payload, {"$ref": "#/$defs/alpha_search", "$defs": schema["$defs"]}
    )


def test_one_positive_score_keeps_the_choice() -> None:
    table = dict(ZERO)
    table[1.1] = (5, 2e-6, 2.5e-6, 2.4e-6, 5.0)
    result = search_alpha(_at(table), GRID)
    assert result.no_positive_key is None
    assert result.chosen is not None and result.alpha == pytest.approx(1.1)
    payload = result.as_payload()
    assert payload["chosen_alpha"] == pytest.approx(1.1)
    assert payload["no_positive_key"] is None


def test_without_h_low_the_highest_score_is_reported() -> None:
    def evaluate(alpha: float) -> AlphaPoint:
        return AlphaPoint(score=-alpha, key_length=0, h_lb=-0.1)

    result = search_alpha(evaluate, GRID)
    assert result.chosen is None
    assert result.no_positive_key is not None
    assert result.no_positive_key.alpha == pytest.approx(1.001)
    no_key = result.as_payload()["no_positive_key"]
    assert no_key["h_low"] is None and no_key["largest_h_lb_searched"] is None
    # No searched bound above the reported one: no sentence about the companion.
    assert "reference companion" not in no_key["reason"]


# ---------------------------------------------------------------------------
#  Through the runner: the run returned is the largest h_low's
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Ran:
    key_rate: Any
    bundle: Path
    stages: tuple[StageRecord, ...] = ()
    alpha_search: Any = None


def test_the_runner_returns_the_largest_estimate_with_the_no_key_status(
    tmp_path: Path,
) -> None:
    def run_at(point: RunConfig, bundle: Path) -> _Ran:
        assert point.alpha is not None
        (key,) = [k for k in ZERO if math.isclose(k, point.alpha, rel_tol=1e-9)]
        _, h_lb, h_low, searched, _ = ZERO[key]
        rate = SimpleNamespace(
            key_length=0, h_lb=h_lb, h_low=h_low,
            reference_bracket={"counted": True, "snapped": {"h_lb": searched}},
            rounds=point.rounds, alpha=point.alpha,
            key_length_reason_code="certified_reported",
        )
        child = StageChild(
            name="alpha", status="chosen",
            detail={"alpha": point.alpha, "key_length": 0, "searched": False},
        )
        solve = StageRecord(
            stage=SliceStage.SOLVE, module="meat-core",
            status=StageStatus.EXECUTED, children=(child,),
        )
        return _Ran(key_rate=rate, bundle=bundle, stages=(solve,))

    config = RunConfig(
        rounds=10_000,
        completeness_budget=Fraction(1, 1_000_000),
        declared_tolerance=1e-12,
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=7
        ),
        alpha_search=GRID,
    )
    outcome: Any = searching_runner(run_at, tmp_path)(config, 0)
    assert outcome.key_rate.alpha == pytest.approx(1.01)
    assert outcome.bundle == tmp_path / "run-0000" / "alpha-01"
    search = outcome.alpha_search
    assert search.chosen is None and search.no_positive_key is not None
    (solve,) = outcome.stages
    (child,) = solve.children
    assert child.status == "no_positive_key"
    assert child.detail["chosen_alpha"] is None
    assert child.detail["no_positive_key"]["reported_alpha"] == pytest.approx(1.01)
    # The searched declaration's bound comes from the run's reference bracket.
    assert child.detail["no_positive_key"]["largest_h_lb_searched"]["h_lb"] == 2.9e-6


# ---------------------------------------------------------------------------
#  The report says it plainly
# ---------------------------------------------------------------------------

REASON = (
    "No alpha the search evaluated gives a positive key length: each of the 3 "
    "evaluations that formed a bound reported 0, n times the bound the key "
    "length is computed from not covering the deductions (error correction, "
    "the verification hash and privacy amplification); by the search's "
    "ranking, which reads the first-order h_lb, the closest is alpha = 1.1, "
    "where n h_lb falls 100 bits short."
)


def _no_key_record() -> dict[str, Any]:
    evaluations = [
        {"alpha": alpha, "phase": "coarse", "key_length": 0, "h_lb": h_lb,
         "score": score, "reason": "certified_reported", "seconds": 1.0,
         "h_low": h_low, "relative_gap": None, "set_aside": None}
        for alpha, (_, h_lb, h_low, _, score) in ZERO.items()
    ]

    def edit(record: dict[str, Any]) -> None:
        payload = record["payload"]
        payload["config"]["alpha"] = None
        payload["config"]["alpha_search"] = GRID.as_payload()
        payload["stages"]["key_rate"]["alpha"] = 1.01
        payload["stages"]["key_rate"]["h_low"] = 3.0e-6
        payload["composition_flow"]["stages"][0]["children"] = [{
            "name": "alpha", "status": "no_positive_key", "wall_time_s": None,
            "detail": {
                "alpha": 1.01, "searched": True, "rule": "the rule",
                "reads": "the honest model", "settings": GRID.as_payload(),
                "chosen_alpha": None, "evaluations": evaluations,
                "no_positive_key": {
                    "reported_alpha": 1.01,
                    "h_low": 3.0e-6,
                    "largest_h_lb": {"alpha": 1.1, "h_lb": -1e-6},
                    "largest_h_lb_searched": {"alpha": 1.01, "h_lb": 2.9e-6},
                    "reason": REASON,
                },
                "no_positive_key_rule": NO_POSITIVE_KEY_RULE,
            },
        }]

    return completed_record(key_length=0, net_key_length=0, edit=edit)


def test_the_report_says_no_alpha_gives_a_key() -> None:
    built = build_report(_no_key_record(), table=synthetic_table())
    jsonschema.validate(built, report_schema())
    alpha = built["sections"]["result"]["alpha"]
    assert alpha["value"] == 1.01 and alpha["no_positive_key"] == REASON
    search = built["sections"]["numerics"]["alpha_search"]
    assert search is not None and search["chosen_alpha"] is None
    assert search["no_positive_key"] == {
        "reported_alpha": 1.01,
        "h_low": 3.0e-6,
        "largest_h_lb": {"alpha": 1.1, "h_lb": -1e-6},
        "largest_h_lb_searched": {"alpha": 1.01, "h_lb": 2.9e-6},
        "reason": REASON,
    }
    summary = built["sections"]["summary"]["result"]
    assert summary.startswith(
        "No key: the protocol outputs no key from n = 1,000,000,000 rounds. "
        + REASON
    )
    assert "(\u03b1 = 1.01), whose key length is 0" in summary
    assert "h_low is an estimate, never a key" in summary
    text = render_markdown(built, contract_link=default_contract_link())
    assert "No key: the protocol outputs no key" in text
    # The box opens with the no-key line, not with a key length of 0.
    glance = built["sections"]["summary"]["at_a_glance"]
    # After the setup line, in place of a key length of 0 and its rate.
    (no_key,) = [item for item in glance if item["lead"] == "No key"]
    assert glance.index(no_key) <= 1
    assert no_key["text"].startswith(
        ": no \u03b1 the search evaluated gives a positive key length "
        "from n = 1,000,000,000 rounds; the figures shown are at \u03b1 = 1.01"
    )
    assert not any(item["lead"].startswith(("Key length", "Key rate"))
                   for item in glance)
    assert "no alpha the outer search evaluated gives a key" in text
    assert "gives a key, so none was chosen" in text
    assert "none: no alpha gives a positive key length" in text
    assert "3e-06 at alpha 1.01" in text
    assert "-1e-06 at alpha 1.1" in text
    assert "2.9e-06 at alpha 1.01" in text


def test_the_no_key_result_keeps_the_statistics_check() -> None:
    """The no-key paragraph ends with what the check of the statistics found."""
    record = _no_key_record()
    record["payload"]["statistics_consistency"] = {
        "checked": False, "unchecked_reason": "opted_out",
        "refused": False, "min_model_pass_probability": "1/2", "orders": [],
    }
    built = build_report(record, table=synthetic_table())
    summary = built["sections"]["summary"]["result"]
    assert summary.startswith("No key: the protocol outputs no key")
    assert summary.endswith(
        "is yours to vouch for."
    ), summary
    assert "The accepted statistics were not checked against your declared " \
        "model (you switched the check off (statistics_check off)" in summary
