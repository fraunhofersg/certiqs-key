"""Contradictory-statistics canaries: a contradiction refuses, a consistent run keys.

WHY THIS EXISTS. An honest table measured on a device against idealised
stations contradicts the declared model, and a searched run must not end
``done`` with a key six times too large; ``test_key_rate_canaries`` runs model
statistics at a fixed alpha and does not cover the case. The cases are bbm92,
ideal pair, transmittances 1/1000, ideal stations, n = 4e10, the alpha search
on; their facade requests are in ``tests/data/contradictory-statistics/`` and
run through the entry point ``runs.facade.worker._run``.

THE CHECK OF ``meat-core/req:unreachable-acceptance-set`` decides them. A run
whose honest statistics are supplied (the ``mt*`` cases and ``g1supplied``,
a facade honest override) is checked: once per run, at the lower end of the
search's domain and before any order is evaluated, the engine bounds the
value with every pair dropped and caps the probability that devices as
declared pass the acceptance test at ``2^-x``; a cap at most
``min_model_pass_probability`` (default one half) refuses the run as a whole.

* ``mt51real`` (Alice's basis split 51/100 in the statistics against 1/2
  declared) and ``mt55`` (11/20) MUST REFUSE with
  ``acceptance_set_unreachable`` at the search's first evaluation, before its
  own solve: their caps are far below one half (measured: x about 9 600 and
  280 000 bits), so the search stops there, chooses nothing and evaluates no
  order. ``mt51real`` at the fixed order ``alpha = 1.25`` refuses too.
* ``mt5005`` (1001/2000, a mismatch inside the acceptance windows) and
  ``g1supplied`` (the model's own law, supplied as a table, the small-mass
  override control) are checked and MUST COMPLETE with a positive key,
  nothing refused.
* ``g1`` (the model's own statistics) and ``g2`` (spdc, the model's own) are
  not checked (their statistics are the engine's model and they declare no
  constraint entry) and MUST COMPLETE with a positive key; ``g2`` completes
  with its bound below the run tier's ceiling.

A REGRESSION SNAPSHOT, NOT AN ORACLE (PRINCIPLES.md 2.3 is not engaged), on
the conventions of ``test_key_rate_canaries.py``: a key is what the engine
computed, held within ``REL_TOL``; a change that moves one updates it here and
says why in its commit. ``slow``: each case runs a full alpha search.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from certiqs_key.runs.alpha_search import UNREACHABLE_EVALUATION_REASON

pytestmark = [pytest.mark.slow, pytest.mark.requires_qics]
pytest.importorskip("qics")

#: The relative tolerance on a recorded key, ``test_key_rate_canaries``'s.
REL_TOL = 0.03

DATA = Path(__file__).resolve().parents[1] / "data" / "contradictory-statistics"

#: The search's first alpha, ``1 + lower_alpha_minus_one`` of every request:
#: alpha_0 of the check.
FIRST_ALPHA = 1.00001

#: The recorded keys of the consistent cases (snapshots).
KEYS: dict[str, int] = {
    # The model's own statistics: 7 878 at a development commit (the
    # reproduction); 6 671 before the companion polish, which recovers the
    # bound on the reference
    # companion the searched points had lost (req:bracket-on-reference (i)).
    "g1": 7878,
    # The same law, supplied as a table: the same key, the check passing.
    "g1supplied": 7878,
    # spdc at transmittance 1/128, the model's own: 15 771 at a development commit.
    "g2": 15707,
    # Alice's split 1001/2000 against 1/2, inside the acceptance windows:
    # 7 466 at a development commit.
    "mt5005": 7669,
}

UNREACHABLE = "acceptance_set_unreachable"


def _request(case: str, *, alpha: float | None = None) -> dict[str, Any]:
    request: dict[str, Any] = json.loads(
        (DATA / f"{case}.json").read_text(encoding="utf-8")
    )
    if alpha is not None:
        request["config"]["alpha"] = alpha
        request["config"]["alpha_search"] = None
    return request


def _run(request: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run one facade request; return the worker's status and the record."""
    from runs.facade import worker

    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        status = worker._run(request, directory, lambda event: None, lambda: None)
        record: dict[str, Any] = json.loads(
            (directory / "record.json").read_text(encoding="utf-8")
        )
    return status, record


def _alpha_child(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Return the solve stage's ``alpha`` child: its status and its detail."""
    (solve,) = (
        stage
        for stage in payload["composition_flow"]["stages"]
        if stage["stage"] == "solve"
    )
    (child,) = (child for child in solve["children"] if child["name"] == "alpha")
    return child["status"], child["detail"]


def _checked(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the run's check, asserting it ran on the supplied law."""
    check: dict[str, Any] = payload["statistics_consistency"]
    assert check["checked"] is True and check["honest_statistics_supplied"] is True
    assert check["min_model_pass_probability"] == "1/2"
    return check


@pytest.mark.parametrize("case", ["mt51real", "mt55"])
def test_a_contradiction_refuses_the_searched_run_as_a_whole(case: str) -> None:
    status, record = _run(_request(case))
    payload = record["payload"]
    assert status["state"] == "refused", status
    assert status["refusal"]["reason"] == UNREACHABLE
    assert payload["config"]["alpha_search"] is not None
    assert payload["refused"] is True
    solve = payload["stages"]["solve"]
    assert solve["reason"] == UNREACHABLE and solve["refused_by"] == "meat-core"
    assert "refused as a whole" in solve["detail"]
    check = _checked(payload)
    # One solve, at the lower end of the search's domain, proving the mismatch.
    assert check["solve"]["alpha_0"] == FIRST_ALPHA
    assert check["solve"]["bound"] > 0 and check["solve"]["dmin_lower_bound"] > 0
    assert check["solve"]["bound_tier"] in ("certified", "first-order")
    # Item (iv): the cap is at most one half, decided before any order, so
    # the search stops at its first evaluation and no order is evaluated.
    assert check["refused"] is True and check["model_pass_decision"] == "exact"
    assert check["model_pass_exponent_bits"] >= 1
    assert check["orders"] == []
    assert solve.get("plausibility") is None
    child_status, search = _alpha_child(payload)
    assert child_status == UNREACHABLE and search["chosen_alpha"] is None
    assert search["contradiction_alpha"] is None
    assert [e["alpha"] for e in search["evaluations"]] == [FIRST_ALPHA]
    assert search["evaluations"][0]["reason"] == UNREACHABLE_EVALUATION_REASON


def test_a_contradiction_at_the_order_the_old_guard_passed_refuses() -> None:
    status, record = _run(_request("mt51real", alpha=1.25))
    payload = record["payload"]
    assert status["state"] == "refused", status
    assert status["refusal"]["reason"] == UNREACHABLE
    check = _checked(payload)
    # A fixed order is its own alpha_0.
    assert check["solve"]["alpha_0"] == 1.25
    assert check["refused"] is True and check["orders"] == []


def _completes(case: str) -> dict[str, Any]:
    status, record = _run(_request(case))
    payload: dict[str, Any] = record["payload"]
    assert status["state"] == "done", status
    assert payload["refused"] is False
    key = payload["stages"]["key_rate"]["key_length"]
    assert key is not None and key > 0, key
    assert key == pytest.approx(KEYS[case], rel=REL_TOL), (
        f"{case}: key {key}, recorded {KEYS[case]}; a deliberate change updates "
        "the recorded value and says why in its commit"
    )
    child_status, search = _alpha_child(payload)
    assert child_status == "chosen" and search["contradiction_alpha"] is None
    return payload


@pytest.mark.parametrize("case", ["mt5005", "g1supplied"])
def test_consistent_supplied_statistics_are_checked_and_keep_their_key(
    case: str,
) -> None:
    payload = _completes(case)
    check = _checked(payload)
    assert check["solve"]["alpha_0"] == FIRST_ALPHA
    assert check["refused"] is False and check["orders"]
    # Where a cap was formed it is above one half: x below one bit.
    if check["model_pass_exponent_bits"] is not None:
        assert check["model_pass_exponent_bits"] < 1


@pytest.mark.parametrize("case", ["g1", "g2"])
def test_the_models_own_statistics_are_not_checked_and_key(case: str) -> None:
    payload = _completes(case)
    check = payload["statistics_consistency"]
    assert check["checked"] is False and check["unchecked_reason"] == "out_of_scope"
    assert check["unchecked_premise"] == "A-REACH" and check["solve"] is None
    (solve,) = (
        stage
        for stage in payload["composition_flow"]["stages"]
        if stage["stage"] == "solve"
    )
    plausibility = solve["detail"]["plausibility"]
    assert plausibility["compared"] is True and plausibility["exceeded"] is False
    assert plausibility["bound"] < plausibility["ceiling"]
    if case == "g2":
        # The reproduction: h_lb at most 0.46 of the ceiling.
        assert plausibility["bound"] <= 0.5 * plausibility["ceiling"]
