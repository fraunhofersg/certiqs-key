"""The run tier's plausibility check: a bound above what a key can carry is refused.

WHY THIS EXISTS. An overstated key, ``h_low = 3.06`` bits per round on a
one-bit key, must not go uncaught (:mod:`certiqs_key.runs.plausibility`). What is held
here: the ceiling's two factors on hand-derived acceptance sets; that an honest BB84 run
passes and records the check; that a synthetic result whose bound exceeds the ceiling is
refused at ``solve`` under the run tier's code with both numbers in the record;
and that an estimate above the ceiling alone, which an unconverged honest run
can show, is not refused.

AND THE CONTRADICTORY-STATISTICS CHECK: the comparison is EXACT where
the key length is formed from the certified number (its lower end against the
ceiling rounded up, no slack: a bound one ulp above refuses, one at the ceiling
does not), RELATIVE otherwise (a slack of ``2^-10`` of the ceiling, wide
enough that an honest bound at the ceiling with the largest binary64 excess
measured is not refused), the ceiling's upper bound is at least the real
number, and the record stores the objective's split, which decides nothing.
"""

from __future__ import annotations

import math
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from instances.bb84.specification import bb84_specification
from instances.common.honest.depolarized_bell_pair import honest_provider
from tests.support.report_records import refused_record, synthetic_table

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    KeyLengthParameters,
    PolytopeData,
)
from certiqs_key.runs import RunConfig
from certiqs_key.runs import pipeline as pipeline_module
from certiqs_key.runs.errors import RunRefusalReason
from certiqs_key.runs.flow import StageStatus
from certiqs_key.runs.pipeline import SliceRefusal, SliceResult, SliceStage, run_slice
from certiqs_key.runs.plausibility import (
    EXACT,
    RELATIVE,
    RELATIVE_SLACK,
    PlausibilityCheck,
    ceiling_upper,
    key_live_mass,
    objective_split,
    plausibility_check,
)
from certiqs_key.runs.record import record_run
from certiqs_key.runs.report import build_report, report_schema
from certiqs_key.runs.report.explain import VALUE_RANGE_CLAIM
from certiqs_key.solvers.frank_wolfe.general_keyrate import FIRST_ORDER_REASON
from certiqs_key.solvers.types import SearchRequest

QBER = F(1, 50)
PARAMETERS = KeyLengthParameters(
    alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
)

#: The largest excess of a binary64 ``h_lb`` over the certified number at the
#: same points, in units of the ceiling, measured on the reproduction's
#: consistent control ``g1`` at the
#: search's lowest alpha, ``alpha - 1 = 1e-5``: 3.1e-11 against a ceiling of
#: 7.26e-7 (``runs/plausibility.py``, "THE SLACK").
MEASURED_EXCESS = 4.3e-5


# ===========================================================================
#  The ceiling's factors, by hand
# ===========================================================================


def test_the_key_live_mass_of_a_singleton_is_its_key_live_frequencies() -> None:
    acceptance = AcceptanceSet(geometry="singleton", frequencies=(0.25, 0.25, 0.5))
    assert key_live_mass(acceptance, ("a", "b", "c"), ("a", "b")) == 0.5
    assert key_live_mass(acceptance, ("a", "b", "c"), ()) == 0.0


def test_the_key_live_mass_of_a_polytope_is_its_largest_key_live_probability() -> (
    None
):
    # {q in simplex(2): q_a <= 7/10}: the largest q_a is 7/10, the largest q_b 1.
    polytope = PolytopeData(columns=2, rows=((1.0, 0.0),), rhs=(0.7,))
    acceptance = AcceptanceSet(geometry="polytope", polytope=polytope)
    mass = key_live_mass(acceptance, ("a", "b"), ("a",))
    # Rounded UP from the exact optimum, the binary64 0.7 itself.
    assert F(mass) >= F(0.7) and mass == pytest.approx(0.7, abs=1e-15)
    assert key_live_mass(acceptance, ("a", "b"), ("b",)) == 1.0


def _log2_decimal(n: int) -> Decimal:
    """``log2 n`` to the context's digits, by decimal's correctly rounded ``ln``."""
    return Decimal(n).ln() / Decimal(2).ln()


@pytest.mark.parametrize("count", [1, 2, 3, 4, 255])
@pytest.mark.parametrize("mass", [4.5785000000000004e-07, 0.5, 1.0, 1e-300, 0.7])
def test_the_rigorous_ceiling_is_the_least_machine_number_above_the_real_one(
    count: int, mass: float
) -> None:
    """Held against 60-digit decimal arithmetic, independent of the balls used."""
    pytest.importorskip("flint")
    upper = ceiling_upper(count, mass, rigorous=True)
    with localcontext() as ctx:
        ctx.prec = 60
        real = _log2_decimal(count + 1) * Decimal(mass)
        # At least the real ceiling (the 60-digit value is within a relative
        # 1e-58 of it, far below one ulp) ...
        assert Decimal(upper) >= real * (1 + Decimal("1e-50"))
        # ... and one ulp down is not above it: rounded up once. Where the
        # ceiling is itself a machine number (d_Z + 1 a power of two) the
        # enclosure's radius puts the bound exactly one ulp above it, and
        # one ulp down is the ceiling (to the 60 digits' rounding).
        assert Decimal(math.nextafter(upper, -math.inf)) <= real * (
            1 + Decimal("1e-50")
        )


def test_the_binary64_ceiling_is_rounded_up() -> None:
    nearest = math.log2(3) * 0.5
    upper = ceiling_upper(2, 0.5, rigorous=False)
    assert upper > nearest
    assert upper == math.nextafter(math.nextafter(nearest, math.inf), math.inf)


def _check(
    bound: float | None,
    h_low: float = 1.0,
    *,
    comparison: str = RELATIVE,
    upper: float | None = None,
    mass: float = 0.5,
) -> PlausibilityCheck:
    ceiling = math.log2(3) * mass
    return PlausibilityCheck(
        bound_name="h_cert" if comparison == EXACT else "h_lb",
        bound=bound,
        h_low=h_low,
        key_value_count=2,
        key_live_values=("z",),
        key_live_mass=mass,
        ceiling=ceiling,
        ceiling_upper=ceiling if upper is None else upper,
        comparison=comparison,
    )


def test_the_verdict_compares_the_bound_and_never_an_infinite_estimate() -> None:
    ceiling = math.log2(3) * 0.5
    assert _check(3.0, 3.06).exceeded
    assert not _check(None).compared
    # An infinite estimate is meat-core's own gate (rem:hlow-range).
    assert not _check(3.0, math.inf).compared
    assert not _check(3.0, math.inf).exceeded
    record = _check(3.0, 3.06).as_record()
    assert record["bound"] == 3.0 and record["ceiling"] == ceiling
    assert record["key_alphabet_with_sifting_symbol"] == 3
    assert record["comparison"] == RELATIVE
    with pytest.raises(ValueError, match="comparison"):
        _check(3.0, comparison="absolute")


# ===========================================================================
#  Exact on a certified number, relative otherwise
# ===========================================================================


def test_the_exact_comparison_refuses_one_ulp_above_and_not_at_the_ceiling() -> None:
    """A certified lower end against the ceiling rounded up, with no slack."""
    upper = ceiling_upper(2, 0.5, rigorous=False)
    above = math.nextafter(upper, math.inf)
    below = math.nextafter(upper, -math.inf)
    exact = _check(above, comparison=EXACT, upper=upper)
    assert exact.exceeded and exact.slack == 0.0 and exact.threshold == upper
    assert not _check(upper, comparison=EXACT, upper=upper).exceeded
    assert not _check(below, comparison=EXACT, upper=upper).exceeded
    # The same number in binary64 is within the relative slack, and passes.
    assert not _check(above, comparison=RELATIVE, upper=upper).exceeded


def test_the_relative_slack_is_a_multiple_of_the_ceiling() -> None:
    for mass in (0.5, 4.5785e-07, 1e-12):
        upper = ceiling_upper(2, mass, rigorous=False)
        check = _check(None, upper=upper, mass=mass)
        assert check.relative_slack == RELATIVE_SLACK == 2.0**-10
        assert check.slack == RELATIVE_SLACK * upper
        inside = upper * (1 + RELATIVE_SLACK / 2)
        outside = math.nextafter(upper + RELATIVE_SLACK * upper, math.inf)
        assert not replace(check, bound=inside).exceeded
        assert replace(check, bound=outside).exceeded
    # No absolute slack: at a key-live mass of 1e-12 a bound of 1e-6, half a
    # million ceilings, is refused (the absolute 1e-6 let it pass).
    upper = ceiling_upper(2, 1e-12, rigorous=False)
    assert _check(1e-6, upper=upper, mass=1e-12).exceeded


def test_an_honest_bound_at_the_ceiling_with_the_measured_excess_passes() -> None:
    """The slack's job: an honest run is never refused.

    An honest exact bound is at most the ceiling. Here it sits AT it, with no
    honest margin, and its binary64 value carries the largest excess measured
    (:data:`MEASURED_EXCESS` of the ceiling), and twenty times that: neither
    is refused. A slack of ``1e-6`` of the ceiling would refuse both.
    """
    for mass in (4.5785000000000004e-07, 0.5):
        upper = ceiling_upper(2, mass, rigorous=False)
        for excess in (MEASURED_EXCESS, 20 * MEASURED_EXCESS):
            check = _check(upper * (1 + excess), upper=upper, mass=mass)
            assert check.compared and not check.exceeded, (mass, excess)


# ===========================================================================
#  The objective's split, by hand
# ===========================================================================


def _namespace(namespace: Any, **changes: Any) -> Any:
    return SimpleNamespace(**{**vars(namespace), **changes})


def test_the_split_reads_the_two_parts_of_the_objective() -> None:
    """``prop:value-range`` (i) at a hand point, ``alpha = 3/2``.

    ``q = (1/2, 1/2)`` on ``(a, b)``, ``a`` key-live; ``P = (1/4, 3/4)``;
    ``K_a = P_a - 1/8 = 1/8``. The penalty is ``3 (1/2 log2 2 + 1/2 log2 2/3)``
    and the entropy term ``1/2 log2(P_a / K_a) / (1/2) = 1``. Their sum is
    ``eq:objective`` at the point: ``1/2 log2 2 + (1/2)/(1/2) log2 4`` on the
    key-live ``a`` and ``3 (1/2 log2 2/3)`` on ``b``.
    """
    rate: Any = SimpleNamespace(
        h_low=0.0,
        alpha=1.5,
        optimized_q={"a": 0.5, "b": 0.5},
        predicted_statistics={"a": 0.25, "b": 0.75},
        block_contributions={"a": {"(0, 0)": -0.125}, "b": {}},
    )
    split = objective_split(rate, ("a",))
    assert split is not None
    penalty = 3 * (0.5 + 0.5 * math.log2(2 / 3))
    assert split["divergence_penalty"] == pytest.approx(penalty, rel=1e-15)
    assert split["entropy_terms"] == pytest.approx(1.0, rel=1e-15)
    objective = 0.5 + 1.0 * 2 + 3 * 0.5 * math.log2(2 / 3)
    assert split["divergence_penalty"] + split["entropy_terms"] == pytest.approx(
        objective, rel=1e-15
    )
    assert split["penalty_share"] == pytest.approx(penalty / objective, rel=1e-15)
    # Nothing finite to split: an infinite estimate, a vanishing statistic.
    assert objective_split(_namespace(rate, h_low=math.inf), ("a",)) is None
    zero = {"a": 0.0, "b": 0.75}
    assert objective_split(_namespace(rate, predicted_statistics=zero), ("a",)) is None


# ===========================================================================
#  The report
# ===========================================================================


def test_the_report_says_at_a_glance_that_the_statistics_contradict_the_model() -> (
    None
):
    """The report says the statistics contradict the model."""
    jsonschema = pytest.importorskip("jsonschema")
    record = refused_record(reason="entropy_bound_above_key_ceiling")
    record["payload"]["stages"]["solve"]["detail"] = "the detail"
    report = build_report(record, table=synthetic_table())
    jsonschema.validate(report, report_schema())
    summary = report["sections"]["summary"]
    (item,) = summary["at_a_glance"]
    assert (item["lead"], item["text"]) == (
        "No key", ": the run was refused at its solve stage, so nothing is certified")
    # Why stands first among the considerations, still in the summary.
    why = summary["considerations"][0]["text"]
    assert why.startswith("The accepted statistics contradict the declared model.")
    assert f"([[{VALUE_RANGE_CLAIM}]])" in why
    assert "no feasible state of the model reproduces any accepted statistic" in why
    assert why.endswith("no warrant for this device.")
    # Any other refusal keeps its plain line, with no such reason.
    other = build_report(refused_record(), table=synthetic_table())["sections"][
        "summary"]
    assert not any("contradict" in line["text"] for line in other["considerations"])


# ===========================================================================
#  On a run
# ===========================================================================


def _config() -> RunConfig:
    return RunConfig(
        rounds=2_000,
        completeness_budget=F(1, 1_000_000),
        parameters=PARAMETERS,
        declared_tolerance=0.0,
        model={"qber": QBER},
    )


def _run(tmp_path: Path, certified: str = "on") -> SliceResult | SliceRefusal:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    return run_slice(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        honest_provider=honest_provider(QBER),
        rounds=2_000,
        completeness_budget=F(1, 1_000_000),
        parameters=PARAMETERS,
        oracle=QicsSectorChoiOracle(),
        directory=tmp_path / "bundle",
        created_by="test",
        declared_tolerance=0.0,
        alpha=1.5,
        request=replace(
            SearchRequest.from_options(None), certified_evaluation=certified
        ),
    )


def _inflated(**changes: Any) -> Any:
    """Wrap the real solve and replace fields of what it returns."""
    real = pipeline_module.solve_bundle

    def solve(*args: Any, **kwargs: Any) -> Any:
        return replace(real(*args, **kwargs), **changes)

    return solve


def _certified_bound(value: float) -> Any:
    """Wrap the real solve and set the certified number's recorded lower end."""
    real = pipeline_module.solve_bundle

    def solve(*args: Any, **kwargs: Any) -> Any:
        result = real(*args, **kwargs)
        assert result.reported_tier is Assurance.CERTIFIED, result.certified
        return replace(
            result, certified={**result.certified, "certified_bound": value}
        )

    return solve


@pytest.mark.requires_qics
def test_an_honest_run_passes_and_its_solve_stage_records_the_check(
    tmp_path: Path,
) -> None:
    pytest.importorskip("qics")
    outcome = _run(tmp_path)
    assert isinstance(outcome, SliceResult), outcome
    rate = outcome.key_rate
    check = plausibility_check(outcome.reread, rate)
    assert check.compared and not check.exceeded
    assert check.key_value_count == outcome.reread.key_value_count
    assert check.ceiling == math.log2(check.key_value_count + 1) * check.key_live_mass
    assert check.ceiling <= check.ceiling_upper
    assert 0.0 < check.key_live_mass <= 1.0
    # Certified, so compared exactly, on the certified number's lower end.
    assert rate.reported_tier is Assurance.CERTIFIED
    assert rate.certified is not None
    assert check.comparison == EXACT and check.bound_name == "h_cert"
    assert check.bound == rate.certified["certified_bound"]
    assert check.first_order_bound == rate.h_lb
    solve = next(r for r in outcome.stages if r.stage is SliceStage.SOLVE)
    recorded = solve.detail["plausibility"]
    assert recorded["exceeded"] is False and recorded["comparison"] == EXACT
    assert recorded["bound"] == rate.certified["certified_bound"]
    assert recorded["slack"] == 0.0
    # The split decides nothing; its parts add up to the estimate.
    split = recorded["objective_split"]
    assert split is not None
    total = split["divergence_penalty"] + split["entropy_terms"]
    assert total == pytest.approx(rate.h_low, rel=1e-9)
    assert 0.0 <= split["penalty_share"] <= 1.0


@pytest.mark.requires_qics
def test_an_honest_first_order_run_is_compared_relative_and_passes(
    tmp_path: Path,
) -> None:
    pytest.importorskip("qics")
    outcome = _run(tmp_path, certified="off")
    assert isinstance(outcome, SliceResult), outcome
    assert outcome.key_rate.reported_tier is Assurance.FIRST_ORDER
    solve = next(r for r in outcome.stages if r.stage is SliceStage.SOLVE)
    recorded = solve.detail["plausibility"]
    assert recorded["comparison"] == RELATIVE and recorded["bound_name"] == "h_lb"
    assert recorded["bound"] == outcome.key_rate.h_lb
    assert recorded["relative_slack"] == RELATIVE_SLACK
    assert recorded["slack"] == RELATIVE_SLACK * recorded["ceiling_upper"]
    assert recorded["exceeded"] is False


@pytest.mark.requires_qics
def test_a_certified_number_one_ulp_above_the_ceiling_refuses_and_at_it_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact comparison on a run: h_cert, not h_lb, and no slack."""
    pytest.importorskip("qics")
    honest = _run(tmp_path / "honest")
    assert isinstance(honest, SliceResult)
    check = plausibility_check(honest.reread, honest.key_rate)
    upper = check.ceiling_upper
    assert upper == ceiling_upper(
        check.key_value_count, check.key_live_mass, rigorous=True
    )

    monkeypatch.setattr(pipeline_module, "solve_bundle", _certified_bound(upper))
    at = _run(tmp_path / "at")
    assert isinstance(at, SliceResult), at

    above = math.nextafter(upper, math.inf)
    monkeypatch.setattr(pipeline_module, "solve_bundle", _certified_bound(above))
    refused = _run(tmp_path / "above")
    assert isinstance(refused, SliceRefusal)
    assert refused.reason == RunRefusalReason.ENTROPY_BOUND_ABOVE_KEY_CEILING
    assert refused.plausibility is not None
    assert refused.plausibility["comparison"] == EXACT
    assert refused.plausibility["bound_name"] == "h_cert"
    assert refused.plausibility["bound"] == above
    # The first-order number stayed where it was, below the ceiling.
    assert refused.plausibility["first_order_bound"] < upper
    assert "contradict the declared model" in refused.detail
    assert "compared exactly" in refused.detail


@pytest.mark.requires_qics
def test_a_bound_above_the_ceiling_is_refused_with_both_numbers_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hunt's overstated key, on a synthetic result: h_lb 3.0 on one bit."""
    pytest.importorskip("qics")
    monkeypatch.setattr(
        pipeline_module, "solve_bundle", _inflated(h_lb=3.0, h_low=3.06)
    )
    outcome = _run(tmp_path, certified="off")
    assert isinstance(outcome, SliceRefusal)
    assert outcome.stage is SliceStage.SOLVE
    assert outcome.reason == RunRefusalReason.ENTROPY_BOUND_ABOVE_KEY_CEILING
    assert outcome.reason == "entropy_bound_above_key_ceiling"
    assert outcome.plausibility is not None
    assert outcome.plausibility["bound"] == 3.0
    assert outcome.plausibility["h_low"] == 3.06
    assert outcome.plausibility["ceiling"] < 3.0
    assert outcome.plausibility["exceeded"] is True
    assert outcome.plausibility["comparison"] == RELATIVE
    assert outcome.detail.startswith(
        "the accepted statistics contradict the declared model: no feasible "
        "state of it reproduces any accepted statistic, so a key has no "
        "warrant for this device."
    )

    payload = record_run(outcome, _config(), created_by="test").payload
    assert payload["refused"] is True
    stage = payload["stages"]["solve"]
    assert stage["reason"] == "entropy_bound_above_key_ceiling"
    assert stage["refused_by"] == "runs"
    assert stage["plausibility"]["bound"] == 3.0
    assert stage["plausibility"]["ceiling"] == outcome.plausibility["ceiling"]
    assert "3.0" in stage["detail"]
    solve = next(
        entry
        for entry in payload["composition_flow"]["stages"]
        if entry["stage"] == "solve"
    )
    assert solve["status"] == str(StageStatus.REFUSED)
    assert solve["detail"]["refused_by"] == "runs"
    assert solve["detail"]["plausibility"]["exceeded"] is True


@pytest.mark.requires_qics
def test_an_estimate_above_the_ceiling_alone_is_not_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The estimate bounds h_low from ABOVE; an unconverged run may show this."""
    pytest.importorskip("qics")
    monkeypatch.setattr(pipeline_module, "solve_bundle", _inflated(h_low=3.06))
    outcome = _run(tmp_path, certified="off")
    assert isinstance(outcome, SliceResult), outcome


@pytest.mark.requires_qics
def test_a_run_not_reported_certified_is_compared_on_its_first_order_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A certified number beside a first-order report is not what is compared."""
    pytest.importorskip("qics")
    monkeypatch.setattr(
        pipeline_module,
        "solve_bundle",
        _inflated(
            reported_tier=Assurance.FIRST_ORDER,
            key_length_reason_code=FIRST_ORDER_REASON,
            h_lb=3.0,
        ),
    )
    outcome = _run(tmp_path)
    assert isinstance(outcome, SliceRefusal)
    assert outcome.plausibility is not None
    assert outcome.plausibility["comparison"] == RELATIVE
    assert outcome.plausibility["bound_name"] == "h_lb"
    assert outcome.plausibility["bound"] == 3.0
