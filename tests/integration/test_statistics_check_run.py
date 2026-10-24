"""The check of the acceptance set against the feasible statistics, on real runs.

WHY THIS EXISTS. ``meat-core/req:unreachable-acceptance-set`` on the path a
run takes: a supplied honest law that no state of the declaration produces
must be refused as a whole, before any order is evaluated, where the cap on
the probability that devices as declared pass the acceptance test is at most
``min_model_pass_probability``, recorded and reported; the same law with the
check off, or with a threshold the cap does not reach, keeps its key and says
what the check found;
a run whose statistics are the engine's own model is not checked and names
A-REACH as the caller's; the model's own law supplied as a table is checked
and never refused for the sign of a rounding, whatever the method, and a
check that forms no bound is solved once per run and reported. The runs are
small (BB84 on a qubit, mostly ``n = 10^6`` at one order) and take seconds
each.

THE CONTRADICTION. The declared basis choices are one half each, so the
sifted-out ("disc") outcome has probability one half under every state the
declaration admits; the supplied law raises it by a fifth and renormalises,
which at ``n = 10^6`` lies outside every accepted window. Measured on this
route at ``alpha_0 = 3/2``: ``b = 0.01576`` bits per round, certified, so
``x = 10^6 (1/3) b``, about 5250, and the cap ``2^-x`` is far below the
default one half, which refuses the run; a threshold of ``2^-10000`` lies
below the cap and refuses nothing. These are measurements, not oracles: the
test asserts the decision and the record's consistency, not the digits.
"""

from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path
from typing import Any

import pytest
from instances.bb84.specification import bb84_specification
from instances.common.honest.depolarized_bell_pair import honest_provider

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.meat_core.finitekey.consistency import NoBoundReason
from certiqs_key.runs.alpha_search import run_searched
from certiqs_key.runs.config import AlphaSearchSettings, RunConfig
from certiqs_key.runs.pipeline import SliceRefusal, SliceResult, SliceStage, run_slice
from certiqs_key.runs.record import record_run
from certiqs_key.runs.report import build_report, report_schema
from certiqs_key.runs.statistics_check import UNREACHABLE_REASON
from certiqs_key.solvers.oracles.protocol import OracleFailure
from certiqs_key.solvers.types import SEARCH_METHODS, SearchRequest

pytestmark = pytest.mark.requires_qics

QBER = F(1, 50)
ROUNDS = 1_000_000
PARAMETERS = KeyLengthParameters(
    alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
)
SCHEMA = (
    Path(__file__).resolve().parents[2]
    / "src" / "certiqs_key" / "runs" / "record.schema.json"
)


def _skewed(declaration: Any) -> dict[str, F]:
    """Return the model's law with the sifted-out outcome raised by a fifth."""
    law = dict(honest_provider(QBER)(declaration))
    raised = {k: v * (F(6, 5) if k == "disc" else 1) for k, v in law.items()}
    total = sum(raised.values())
    return {k: v / total for k, v in raised.items()}


def _run(
    tmp_path: Path,
    *,
    supplied: bool = True,
    honest: Any = _skewed,
    parameters: KeyLengthParameters = PARAMETERS,
    alpha: float = 1.5,
    **options: Any,
) -> SliceResult | SliceRefusal:
    pytest.importorskip("qics")
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    return run_slice(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        honest_provider=honest,
        rounds=ROUNDS,
        completeness_budget=F(1, 1_000_000),
        parameters=parameters,
        oracle=QicsSectorChoiOracle(),
        directory=tmp_path / "bundle",
        created_by="test",
        declared_tolerance=0.0,
        alpha=alpha,
        endpoint_rule="bernstein",
        request=SearchRequest.from_options(None),
        honest_supplied=supplied,
        **options,
    )


def _record(outcome: Any, **config: Any) -> dict[str, Any]:
    jsonschema = pytest.importorskip("jsonschema")
    record = record_run(
        outcome,
        RunConfig(
            rounds=ROUNDS,
            completeness_budget=F(1, 1_000_000),
            parameters=PARAMETERS,
            declared_tolerance=0.0,
            alpha=1.5,
            **config,
        ),
        created_by="test",
    ).as_dict()
    jsonschema.validate(record, json.loads(SCHEMA.read_text(encoding="utf-8")))
    return record


def test_a_supplied_law_no_state_produces_is_refused_as_a_whole(
    tmp_path: Path,
) -> None:
    outcome = _run(tmp_path)
    assert isinstance(outcome, SliceRefusal), outcome
    assert outcome.stage is SliceStage.SOLVE and outcome.reason == UNREACHABLE_REASON
    assert "evaluated at no order" in outcome.detail
    check = outcome.statistics_consistency
    assert check is not None and check.scope.checked
    bound = check.bound
    assert bound is not None and bound.bound is not None and bound.bound > 0
    assert bound.alpha_0 == 1.5 and bound.tier == "certified"
    # Item (iv): one decision, before any order: no order was evaluated.
    assert check.cap is not None and check.refused and check.orders == ()
    assert check.cap.exponent == ROUNDS * bound.bound / 3
    record = _record(outcome)
    stage = record["payload"]["stages"]["solve"]
    assert stage["reason"] == UNREACHABLE_REASON and stage["refused_by"] == "meat-core"
    block = record["payload"]["statistics_consistency"]
    assert block["solve"]["stop_cause"] == "gap_target"
    assert block["solve"]["dmin_lower_bound"] > 0
    assert block["min_model_pass_probability"] == "1/2"
    assert block["refused"] is True and block["model_pass_decision"] == "exact"
    # Item (v): x with the tier of b, never above n times the recorded lower
    # bound on D_min (both rounded down from the same exact number).
    assert block["model_pass_exponent_tier"] == "certified"
    assert 1 <= block["model_pass_exponent_bits"] <= (
        block["rounds"] * block["solve"]["dmin_lower_bound"] * (1 + 1e-12)
    )
    assert block["orders"] == []
    report = build_report(record)
    pytest.importorskip("jsonschema").validate(report, report_schema())
    (item,) = report["sections"]["summary"]["at_a_glance"]
    assert item["lead"] == "No key"
    # Why stands first among the considerations, still in the summary, with
    # the cap as a probability in place of a key length (item (v)).
    why = report["sections"]["summary"]["considerations"][0]["text"]
    assert why.startswith("The accepted statistics were checked against your "
                          "declared model: no state it admits")
    assert "pass this acceptance test with probability at most 2^-" in why
    assert ("at most your threshold min_model_pass_probability = 1/2" in why
            and "so the run is refused and reports no key length" in why)
    assert " bits" not in why


#: A threshold far below the cap of the skewed law (2^-x, x about 5250).
TINY_TAU = F(1, 2**10000)


def test_a_threshold_the_cap_does_not_reach_keeps_the_key_and_states_it(
    tmp_path: Path,
) -> None:
    outcome = _run(tmp_path, min_model_pass_probability=TINY_TAU)
    assert isinstance(outcome, SliceResult), outcome
    key = outcome.key_rate.key_length
    assert key is not None and key > 0
    check = outcome.statistics_consistency
    assert check is not None and check.cap is not None and not check.refused
    (order,) = check.orders
    assert order.alpha == 1.5 and order.proven_part is not None
    # (alpha'-1)/alpha' n f = x at alpha' = alpha_0 (item (v)).
    assert order.proven_part / 3 == check.cap.exponent
    record = _record(outcome, min_model_pass_probability=TINY_TAU)
    assert record["payload"]["statistics_consistency"]["refused"] is False
    report = build_report(record)
    pytest.importorskip("jsonschema").validate(report, report_schema())
    texts = [item["text"]
             for item in report["sections"]["summary"]["considerations"]]
    assert any(t.startswith("Devices that behave as your declared model says")
               for t in texts)
    result = report["sections"]["summary"]["result"]
    assert "pass this acceptance test with probability at most 2^-" in result
    assert "so the check does not refuse the run" in result
    assert "penalty" not in result and "share" not in result


def test_off_opts_the_run_out_and_names_the_premise(tmp_path: Path) -> None:
    outcome = _run(tmp_path, statistics_check="off")
    assert isinstance(outcome, SliceResult), outcome
    check = outcome.statistics_consistency
    assert check is not None and not check.scope.checked
    assert check.bound is None and not check.orders
    record = _record(outcome, statistics_check="off")
    block = record["payload"]["statistics_consistency"]
    assert block["unchecked_reason"] == "opted_out"
    assert block["unchecked_premise"] == "A-REACH"
    report = build_report(record)
    texts = [item["text"]
             for item in report["sections"]["summary"]["considerations"]]
    assert any("a state your declared devices admit can produce them "
               "([[A-REACH]]) is yours to vouch for" in t for t in texts)


def test_the_engines_own_law_is_out_of_scope_and_solves_nothing_more(
    tmp_path: Path,
) -> None:
    outcome = _run(tmp_path, supplied=False, honest=honest_provider(QBER))
    assert isinstance(outcome, SliceResult), outcome
    check = outcome.statistics_consistency
    assert check is not None and check.scope.unchecked_reason is not None
    assert str(check.scope.unchecked_reason) == "out_of_scope"
    assert check.bound is None


def test_an_order_with_key_length_zero_records_its_diagnostic(
    tmp_path: Path,
) -> None:
    """Item (v): n f at every order the run evaluates, a key length 0 included.

    lambda_ec takes every bit, so the run reports the key length 0; the bound
    is positive (the skewed law), and with a threshold below the cap nothing
    is refused: the order records n f > 0 and nothing reads it.
    """
    outcome = _run(
        tmp_path,
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=10**6
        ),
        min_model_pass_probability=TINY_TAU,
    )
    assert isinstance(outcome, SliceResult), outcome
    assert outcome.key_rate.key_length == 0
    check = outcome.statistics_consistency
    assert check is not None and check.bound is not None
    assert check.bound.bound is not None and check.bound.bound > 0
    (order,) = check.orders
    assert order.proven_part is not None and order.proven_part > 0
    assert not check.refused


def test_an_order_outside_the_key_length_domain_records_its_diagnostic(
    tmp_path: Path,
) -> None:
    # req:key-length-alpha-domain withholds the key length at alpha = 5/2; the
    # order is still evaluated, and its n f recorded.
    outcome = _run(tmp_path, alpha=2.5, min_model_pass_probability=TINY_TAU)
    assert isinstance(outcome, SliceResult), outcome
    assert outcome.key_rate.key_length is None
    check = outcome.statistics_consistency
    assert check is not None and check.bound is not None
    assert check.bound.bound is not None and check.bound.bound > 0
    (order,) = check.orders
    assert order.alpha == 2.5 and order.proven_part is not None
    assert not check.refused


def _searched(tmp_path: Path, *, skew: F, check: str) -> SliceResult | SliceRefusal:
    """Run an outer alpha search over the skewed law, the check on or off."""
    pytest.importorskip("qics")
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    def law(declaration: Any) -> dict[str, F]:
        base = dict(honest_provider(QBER)(declaration))
        raised = {k: v * (skew if k == "disc" else 1) for k, v in base.items()}
        total = sum(raised.values())
        return {k: v / total for k, v in raised.items()}

    def run_one(config: RunConfig, index: int) -> SliceResult | SliceRefusal:
        return run_slice(
            bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
            honest_provider=law,
            rounds=ROUNDS,
            completeness_budget=F(1, 1_000_000),
            parameters=PARAMETERS,
            oracle=QicsSectorChoiOracle(),
            directory=tmp_path / f"{check}-{index}",
            created_by="test",
            declared_tolerance=0.0,
            alpha=config.alpha,
            endpoint_rule="bernstein",
            request=SearchRequest.from_options(None),
            honest_supplied=True,
            statistics_check=check,
        )

    config = RunConfig(
        rounds=ROUNDS,
        completeness_budget=F(1, 1_000_000),
        parameters=PARAMETERS,
        declared_tolerance=0.0,
        alpha_search=AlphaSearchSettings(
            lower=1e-3, upper=0.9, coarse_points=4, refine_steps=0
        ),
    )
    return run_searched(config, run_one)


@pytest.mark.slow
def test_turning_the_check_on_reports_no_key_the_unchecked_search_refuses(
    tmp_path: Path,
) -> None:
    """The check refuses the run before any order; unchecked, a contradiction does.

    "disc" raised by 6/100: at alpha = 1.001 the bound exceeds the run tier's
    ceiling (a proved contradiction, which refuses the unchecked search as a
    whole). Checked, the cap refuses the run at the search's first
    evaluation, before its own solve: no order is evaluated, so no
    plausibility check runs, and the search stops there.
    """
    unchecked = _searched(tmp_path, skew=F(106, 100), check="off")
    assert isinstance(unchecked, SliceRefusal)
    assert unchecked.reason == "entropy_bound_above_key_ceiling"
    checked = _searched(tmp_path, skew=F(106, 100), check="on")
    assert isinstance(checked, SliceRefusal), checked.key_rate.key_length
    assert checked.reason == UNREACHABLE_REASON
    assert checked.plausibility is None
    search = checked.alpha_search
    assert search is not None and search.contradiction is None
    assert search.chosen is None and len(search.evaluations) == 1
    check = checked.statistics_consistency
    assert check is not None and check.refused and check.orders == ()


# ===========================================================================
#  Item (ii): the check's solve refuses nothing
# ===========================================================================


@pytest.mark.parametrize("alpha", [1.5, 1.0 + 1e-5])
def test_a_reachable_supplied_table_is_checked_and_not_refused(
    tmp_path: Path, alpha: float
) -> None:
    """The model's own law, supplied as the honest table, under method auto.

    The law is reachable, so the penalty-only program's value is exactly 0
    and the sign of a computed objective is a matter of the last bit times
    alpha_0 / (alpha_0 - 1). At n = 10^9 the check's portfolio meets points
    a few ulps below 0 (measured: -1.2e-15 at alpha = 3/2, -2.4e-11 at
    1 + 1e-5), where a per-point refusal would refuse the run with
    ``negative_objective``; item (ii) says the bound is formed whatever the
    sign of the estimate, and a negative estimate refuses nothing. On a
    reachable table that bound is not positive, so there is no cap. The
    budget is a cap: the solves stop at their own target or stagnation well
    before it.
    """
    pytest.importorskip("qics")
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    outcome = run_slice(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        honest_provider=honest_provider(QBER),
        rounds=10**9,
        completeness_budget=F(1, 1_000_000),
        parameters=PARAMETERS,
        oracle=QicsSectorChoiOracle(),
        directory=tmp_path / "bundle",
        created_by="test",
        declared_tolerance=0.0,
        alpha=alpha,
        endpoint_rule="bernstein",
        request=SearchRequest(method="auto", budget_seconds=10.0),
        honest_supplied=True,
    )
    assert isinstance(outcome, SliceResult), (outcome.reason, outcome.detail)
    key = outcome.key_rate.key_length
    assert key is not None and key > 0
    check = outcome.statistics_consistency
    assert check is not None and check.scope.checked
    assert check.bound is not None
    assert check.bound.no_bound_reason is None and check.bound.bound is not None
    assert check.bound.bound <= 0
    assert check.cap is None and not check.refused and len(check.orders) == 1


class _FailingOnce:
    """The QICS oracle, whose first solve raises an oracle failure without a status.

    The first solve of a checked run is the check's: it comes before the
    run's own solve (row 10 of meat-core's fail_closed table).
    """

    def __init__(self) -> None:
        from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

        self.inner = QicsSectorChoiOracle()
        self.failed = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)

    def minimize(self, problem: Any) -> Any:
        if not self.failed:
            self.failed = True
            raise OracleFailure("the backend raised (a fake, for this test)")
        return self.inner.minimize(problem)


def test_a_check_left_without_a_bound_is_solved_once_and_the_search_proceeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Items (i), (ii) on an outer alpha search whose check forms no bound.

    The check's solve meets an oracle failure without a status: it is
    recorded as ``solve_not_completed``, the run proceeds to its key, and the
    search's later evaluations read the recorded outcome rather than solving
    again (one solve per run). The report says no bound was formed and why.
    """
    pytest.importorskip("qics")
    from certiqs_key.runs import pipeline

    solves: list[float] = []
    original = pipeline.bound_minimal_divergence_of_bundle

    def counted(*args: Any, alpha_0: float, **kwargs: Any) -> Any:
        solves.append(alpha_0)
        return original(*args, alpha_0=alpha_0, **kwargs)

    monkeypatch.setattr(pipeline, "bound_minimal_divergence_of_bundle", counted)
    oracle = _FailingOnce()

    def run_one(config: RunConfig, index: int) -> SliceResult | SliceRefusal:
        return run_slice(
            bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
            honest_provider=honest_provider(QBER),
            rounds=ROUNDS,
            completeness_budget=F(1, 1_000_000),
            parameters=PARAMETERS,
            oracle=oracle,
            directory=tmp_path / f"run-{index}",
            created_by="test",
            declared_tolerance=0.0,
            alpha=config.alpha,
            endpoint_rule="bernstein",
            request=SearchRequest(method="auto", budget_seconds=10.0),
            honest_supplied=True,
        )

    config = RunConfig(
        rounds=ROUNDS,
        completeness_budget=F(1, 1_000_000),
        parameters=PARAMETERS,
        declared_tolerance=0.0,
        alpha_search=AlphaSearchSettings(
            lower=0.05, upper=0.5, coarse_points=3, refine_steps=0
        ),
    )
    outcome = run_searched(config, run_one)
    assert isinstance(outcome, SliceResult), (outcome.reason, outcome.detail)
    assert outcome.key_rate.key_length is not None
    assert outcome.key_rate.key_length > 0
    assert oracle.failed and len(solves) == 1
    search = outcome.alpha_search
    assert search is not None and len(search.evaluations) == 3
    check = outcome.statistics_consistency
    assert check is not None and check.scope.checked
    bound = check.bound
    assert bound is not None and bound.bound is None
    assert bound.no_bound_reason is NoBoundReason.SOLVE_NOT_COMPLETED
    assert bound.stop_cause == "oracle_failure"
    assert bound.detail is not None and "failed without a status" in bound.detail
    assert len(check.orders) == 3 and check.cap is None and not check.refused
    record = record_run(outcome, config, created_by="test").as_dict()
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(record, json.loads(SCHEMA.read_text(encoding="utf-8")))
    solve = record["payload"]["statistics_consistency"]["solve"]
    assert solve["no_bound_reason"] == "solve_not_completed"
    assert solve["stop_cause"] == "oracle_failure"
    assert "failed without a status" in solve["detail"]
    report = build_report(record)
    jsonschema.validate(report, report_schema())
    # The considerations say it in one plain line; the result paragraph
    # names the reason.
    texts = [item["text"] for item in report["sections"]["summary"]["considerations"]]
    assert any("but no bound on a mismatch was formed, so there is no cap"
               in text for text in texts)
    assert ("no bound on their mismatch was formed (solve_not_completed;"
            in report["sections"]["summary"]["result"])


def _model_law_bundle(tmp_path: Path, rounds: int) -> Any:
    """Return the bundle of a run whose supplied table is the model's own law."""
    pytest.importorskip("qics")
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    outcome = run_slice(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        honest_provider=honest_provider(QBER),
        rounds=rounds,
        completeness_budget=F(1, 1_000_000),
        parameters=PARAMETERS,
        oracle=QicsSectorChoiOracle(),
        directory=tmp_path / f"bundle-{rounds}",
        created_by="test",
        declared_tolerance=0.0,
        alpha=1.5,
        endpoint_rule="bernstein",
        request=SearchRequest(method="auto", budget_seconds=10.0),
        honest_supplied=True,
        statistics_check="off",
    )
    assert isinstance(outcome, SliceResult), (outcome.reason, outcome.detail)
    return outcome.bundle


@pytest.mark.parametrize("rounds", [10**4, 10**8])
def test_the_checks_solve_returns_under_every_method_on_a_reachable_table(
    tmp_path: Path, rounds: int
) -> None:
    """Item (ii) under every method, at two block sizes and two orders.

    The model's own law is reachable, so the penalty-only value is 0 and the
    sign of every computed objective is rounding's. Whatever it is, the
    check's solve returns a bound with its tier (item (ii): formed whatever
    the sign of its estimate), not positive on a reachable table, or a
    withdrawn first-order number; never an exception and never a solve left
    incomplete.
    """
    from certiqs_key.solvers.frank_wolfe.keyrate import (
        bound_minimal_divergence_of_bundle,
    )
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    bundle = _model_law_bundle(tmp_path, rounds)
    for method in SEARCH_METHODS:
        for alpha_0 in (1.05, 1.5):
            bound = bound_minimal_divergence_of_bundle(
                bundle,
                QicsSectorChoiOracle(),
                alpha_0=alpha_0,
                request=SearchRequest(method=method, budget_seconds=5.0),
            )
            where = (method, alpha_0, bound.no_bound_reason, bound.detail)
            assert bound.alpha_0 == alpha_0, where
            assert bound.no_bound_reason is not NoBoundReason.SOLVE_NOT_COMPLETED, where
            if bound.bound is None:
                assert (
                    bound.no_bound_reason is NoBoundReason.FIRST_ORDER_WITHDRAWN
                ), where
            else:
                assert bound.bound <= 0, where


def test_a_searched_auto_run_with_a_reachable_table_completes_and_solves_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The canary's table under an outer alpha search, method auto, n = 10^9."""
    pytest.importorskip("qics")
    from certiqs_key.runs import pipeline
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    solves: list[float] = []
    original = pipeline.bound_minimal_divergence_of_bundle

    def counted(*args: Any, alpha_0: float, **kwargs: Any) -> Any:
        solves.append(alpha_0)
        return original(*args, alpha_0=alpha_0, **kwargs)

    monkeypatch.setattr(pipeline, "bound_minimal_divergence_of_bundle", counted)

    def run_one(config: RunConfig, index: int) -> SliceResult | SliceRefusal:
        return run_slice(
            bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
            honest_provider=honest_provider(QBER),
            rounds=10**9,
            completeness_budget=F(1, 1_000_000),
            parameters=PARAMETERS,
            oracle=QicsSectorChoiOracle(),
            directory=tmp_path / f"run-{index}",
            created_by="test",
            declared_tolerance=0.0,
            alpha=config.alpha,
            endpoint_rule="bernstein",
            request=SearchRequest(method="auto", budget_seconds=10.0),
            honest_supplied=True,
        )

    config = RunConfig(
        rounds=10**9,
        completeness_budget=F(1, 1_000_000),
        parameters=PARAMETERS,
        declared_tolerance=0.0,
        alpha_search=AlphaSearchSettings(coarse_points=3, refine_steps=0),
    )
    outcome = run_searched(config, run_one)
    assert isinstance(outcome, SliceResult), (outcome.reason, outcome.detail)
    assert outcome.key_rate.key_length is not None
    assert outcome.key_rate.key_length > 0
    assert len(solves) == 1
    check = outcome.statistics_consistency
    assert check is not None and check.scope.checked and check.bound is not None
    assert len(check.orders) == 3 and not check.refused


def test_a_vacuous_security_statement_met_by_the_check_is_the_runs_refusal(
    tmp_path: Path,
) -> None:
    """The check's own boundary passes on the run's preparation error.

    eps_pa + eps_ev >= 1 leaves no security statement to make
    (meat-core/req:security-statement-not-vacuous). The check's solve meets it
    first, in the preparation it shares with the run's own solve, and the run
    is refused at the solve stage under the engine's code, as the run's own
    solve would refuse it; the check forms nothing.
    """
    outcome = _run(
        tmp_path,
        honest=honest_provider(QBER),
        parameters=KeyLengthParameters(
            alpha=1.5, eps_pa=0.5, eps_ev=0.5, lambda_ec=0
        ),
    )
    assert isinstance(outcome, SliceRefusal), outcome
    assert outcome.stage is SliceStage.SOLVE
    assert outcome.reason == "security_statement_vacuous"
    check = outcome.statistics_consistency
    assert check is not None and check.scope.checked
    assert check.bound is None
