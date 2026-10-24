"""The polish on the reference companion and the five points certified there.

WHY THIS EXISTS. ``meat-core/frank-wolfe/req:bracket-on-reference`` (i): after
the search on the snapped declaration ``D``, a short search on the reference
companion's own program (the POLISH) starts at the first set's point with the
largest bracket on ``D``, its acceptance-side component that point's exact
one, and the points it keeps are evaluated beside the search's; it runs within
the share ``reference_polish_share`` (1/10) of the evaluation's wall budget, set
aside before the search; it does not run from a start whose ``q`` was not
formed on the exact island; it refuses nothing on the sign of its values
(``req:negative-estimate-refused`` binds the run's search alone); a failed
polish keeps what it assessed and leaves the first set's bracket.
``req:certified-evaluation`` (i): on a companion, at most five points of the
two sets together are certified, those that contribute with the largest
brackets there, a point in both counted once, ties by the order the search and
then the polish consumed them.

Without the polish, on BBM92 with an SPDC source, dark counts of 1e-6 to 1e-4
and a key-round probability near 2e-6 per round, the bound on the companion
at the search's points was about -5e-3 against 1.1e-6 on ``D`` and the key 0:
the canaries below, in the full tier, hold the key positive there.

Every expectation is written from the requirements, not read off a run.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from certiqs_key.solvers.frank_wolfe.reference import (
    CERTIFIED_POINTS,
    REFERENCE_POLISH_SHARE,
    START_NOT_EXACT,
    EvaluatedPoint,
    KeptPoint,
    PointSet,
    ReferenceBracket,
    ReferenceCandidates,
    ReferenceStatus,
    polish_on_reference,
)

PORTS = ("H", "V", "D", "A")
NOISY = {
    "efficiency": dict.fromkeys(PORTS, F(9, 10)),
    "dark_count": dict.fromkeys(PORTS, F(1, 10**6)),
    "efficiency_normalization": F(1),
}


# ===========================================================================
#  Unit: the start rule, the kept points and the certified selection
# ===========================================================================


def _assessment(
    bracket: float | None, *, q: F = F(1, 2), block: float = 1.0, exact: bool = True
) -> Any:
    """Return a stand-in for a CandidateAssessment: a point (q, J), its bracket."""
    return SimpleNamespace(
        bracket=bracket,
        point={("A", "x"): np.array([[block]], dtype=np.complex128)},
        q_iterate=SimpleNamespace(
            exact={"c": q} if exact else None, view={"c": float(q)}, on_island=exact
        ),
        gate=SimpleNamespace(iteration=1),
    )


@pytest.mark.contract
def test_a_polish_from_an_inexact_start_does_not_run_and_says_why() -> None:
    """req:bracket-on-reference (i): no exact q at the start, no polish, set empty.

    Nothing of the companion is touched: the record names the reason, the
    share and the start, and keeps no point.
    """
    start = KeptPoint(_assessment(1e-6, exact=False), ("best",), 3)
    outcome = polish_on_reference(
        None,  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
        1.05,
        SimpleNamespace(max_iterations=200),  # type: ignore[arg-type]
        start,
        budget_seconds=12.0,
    )
    record = outcome.record
    assert outcome.kept == ()
    assert record.ran is False and record.reason == START_NOT_EXACT
    assert record.points_assessed == 0 and record.stop_cause is None
    assert record.share == REFERENCE_POLISH_SHARE == F(1, 10)
    assert record.start_index == 0 and record.budget_seconds == 12.0
    assert record.as_record()["share"] == "1/10"


@pytest.mark.contract
def test_each_set_keeps_its_four_best_and_its_last_with_their_order() -> None:
    """Item (i): at most four contributing points by bracket, ties to the earlier."""
    keeper = ReferenceCandidates()
    brackets = [0.1, None, 0.3, 0.3, 0.2, 0.05, 0.4, -1.0]
    for value in brackets:
        keeper.observe(_assessment(value))  # type: ignore[arg-type]
    kept = keeper.points()
    # Best: 0.4 (7th), 0.3 (3rd), 0.3 (4th), 0.2 (5th); last: -1.0 (8th).
    assert [k.sequence for k in kept] == [7, 3, 4, 5, 8]
    assert [k.roles for k in kept] == [("best",)] * 4 + [("last",)]
    assert keeper.seen == len(brackets)


def _evaluated(
    point_set: PointSet, sequence: int, bracket: float | None, **point: Any
) -> EvaluatedPoint:
    candidate = _assessment(bracket, **point)
    reference = None if bracket is None else candidate
    return EvaluatedPoint(point_set, sequence, candidate, reference)


@pytest.mark.contract
def test_the_certified_points_are_the_five_best_of_the_union_each_once() -> None:
    """req:certified-evaluation (i): five of the two sets, by bracket on the companion.

    Seven points contribute, one of the polish's being the search's best point
    again (the polish consumes its start first: counted once, as the
    search's); a point that does not contribute is never selected; equal
    brackets go to the earlier-consumed point, the search's before the
    polish's.
    """
    search = [
        _evaluated(PointSet.SEARCH, 1, 0.5, block=1.0),
        _evaluated(PointSet.SEARCH, 2, 0.2, block=2.0),
        _evaluated(PointSet.SEARCH, 3, 0.2, block=3.0),
        _evaluated(PointSet.SEARCH, 4, None, block=4.0),  # withdrawn there
        _evaluated(PointSet.SEARCH, 5, -0.1, block=5.0),
    ]
    polish = [
        _evaluated(PointSet.POLISH, 6, 0.5, block=1.0),  # the start, again
        _evaluated(PointSet.POLISH, 7, 0.9, block=7.0),
        _evaluated(PointSet.POLISH, 8, 0.2, block=8.0),
    ]
    bracket = ReferenceBracket(
        ReferenceStatus.COUNTED, None, 0.9, evaluations=(*search, *polish)
    )
    chosen = bracket.certification_points()
    assert len(chosen) == CERTIFIED_POINTS == 5
    assert [(e.point_set, e.sequence) for e in chosen] == [
        (PointSet.POLISH, 7),  # 0.9
        (PointSet.SEARCH, 1),  # 0.5, the start as the search consumed it
        (PointSet.SEARCH, 2),  # 0.2, earliest of three
        (PointSet.SEARCH, 3),  # 0.2
        (PointSet.POLISH, 8),  # 0.2, the polish's after the search's
    ]


@pytest.mark.contract
def test_a_point_is_the_same_point_only_with_the_same_q_and_choi_blocks() -> None:
    """The same Choi blocks with another exact q are two points, both selectable."""
    bracket = ReferenceBracket(
        ReferenceStatus.COUNTED,
        None,
        0.5,
        evaluations=(
            _evaluated(PointSet.SEARCH, 1, 0.5, q=F(1, 2)),
            _evaluated(PointSet.POLISH, 2, 0.5, q=F(1, 3)),
        ),
    )
    assert [e.sequence for e in bracket.certification_points()] == [1, 2]


# ===========================================================================
#  Integration: a companion run (optical BB84, noisy two-photon device)
# ===========================================================================


def _config(**solver: Any) -> Any:
    from instances.optical_bb84 import surface

    from certiqs_key.runs.config import SolverSettings

    # fw by name: these tests pin iteration-bounded points and counts.
    base = surface.default_config(
        solver=SolverSettings(**{"method": "fw", **solver})
    )
    return base.with_(
        device={
            **base.device,
            "photon_cutoff": F(2),
            "exact_window": F(3),
            **NOISY,
        }
    )


def _run(config: Any) -> dict[str, Any]:
    from instances.optical_bb84 import surface

    from certiqs_key.runs.record import record_run
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    with tempfile.TemporaryDirectory() as tmp:
        outcome = surface.runner(QicsSectorChoiOracle(), Path(tmp), created_by="t")(
            config, 0
        )
        record = record_run(outcome, config, created_by="t").as_dict()
    found: dict[str, Any] = json.loads(json.dumps(record))
    return found


def _rate(record: dict[str, Any]) -> dict[str, Any]:
    rate: dict[str, Any] = record["payload"]["stages"]["key_rate"]
    return rate


@pytest.mark.requires_qics
@pytest.mark.contract
def test_the_polish_s_points_are_evaluated_beside_the_search_s() -> None:
    """Item (i), (iii), (vi): the polish runs, its points count, the record says so.

    The run's first-order number is the largest bracket on the companion over
    the points of both sets; each point names its set; the polish's record
    names its start, share, method, cap, points and stop cause. With no wall
    budget (an explicit FW run of 20 iterations) the cap alone bounds it.
    """
    pytest.importorskip("qics")
    record = _run(_config(max_iterations=20))
    rate = _rate(record)
    bracket = rate["reference_bracket"]
    assert bracket["status"] == "counted"
    polish = bracket["polish"]
    assert polish["ran"] is True and polish["reason"] is None
    assert polish["start_index"] == 0 and polish["share"] == "1/10"
    assert polish["budget_seconds"] is None  # no wall budget: the cap alone
    assert polish["method"] == "corrective" and polish["iteration_cap"] == 20
    assert polish["points_assessed"] >= 1
    assert polish["stop_cause"] in ("stagnated", "iteration_cap")
    sets = [point["set"] for point in bracket["points"]]
    assert "polish" in sets and "search" in sets
    polish_points = [p for p in bracket["points"] if p["set"] == "polish"]
    assert all(p["bracket_snapped"] is None for p in polish_points)
    assert 1 <= len(polish_points) <= 5
    brackets = [
        p["bracket_reference"]
        for p in bracket["points"]
        if p["bracket_reference"] is not None
    ]
    assert bracket["h_lb_reference"] == max(brackets) == rate["h_lb"]
    assert len(rate["certified"]["points"]) <= 5


@pytest.mark.requires_qics
@pytest.mark.contract
def test_the_polish_s_share_is_set_aside_before_the_search_and_only_then(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Item (i): 1/10 of the evaluation's wall budget is set aside where admitted.

    With the companion admitted, the search on D runs with 9/10 of the
    budget and the polish is given 1/10; where the companion is not admitted
    nothing is set aside and nothing is polished.
    """
    pytest.importorskip("qics")
    from certiqs_key.meat_core.declaration.companion import (
        CompanionNotAdmitted,
        NotAdmittedReason,
    )
    from certiqs_key.solvers.frank_wolfe import general_keyrate

    config = _config(method="auto", budget_seconds=4.0)
    admitted = _rate(_run(config))
    assert admitted["search_report"]["budget_seconds"] == pytest.approx(3.6)
    polish = admitted["reference_bracket"]["polish"]
    assert polish["budget_seconds"] == pytest.approx(0.4)
    assert polish["seconds"] <= 0.4 + 1.0  # the share, plus one assessment's overrun

    def refused(declaration: Any, companion: Any) -> Any:
        return CompanionNotAdmitted(NotAdmittedReason.CONSTRAINT_LIST, "test")

    monkeypatch.setattr(general_keyrate, "admit_reference_companion", refused)
    alone = _rate(_run(config))
    assert alone["search_report"]["budget_seconds"] == pytest.approx(4.0)
    assert alone["reference_bracket"]["status"] == "not_evaluated"
    assert alone["reference_bracket"]["polish"] is None


@pytest.mark.requires_qics
@pytest.mark.contract
def test_the_polish_refuses_nothing_on_a_negative_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """req:negative-estimate-refused binds the run's search alone.

    Every objective value the polish assesses is made negative; the run is
    not refused, the polish runs to its own stop, and its points are kept.
    """
    pytest.importorskip("qics")
    from certiqs_key.solvers.frank_wolfe import reference

    original = reference.assess_candidate

    def negative(*args: Any, **kwargs: Any) -> Any:
        found = original(*args, **kwargs)
        return replace(found, gate=replace(found.gate, objective=-1e-3))

    monkeypatch.setattr(reference, "assess_candidate", negative)
    record = _run(_config(max_iterations=20))
    assert not record["payload"].get("refused")
    rate = _rate(record)
    assert rate["key_length"] is not None and rate["key_length"] > 0
    bracket = rate["reference_bracket"]
    assert bracket["polish"]["ran"] is True
    polish_points = [p for p in bracket["points"] if p["set"] == "polish"]
    assert polish_points and all(
        p["objective_reference"] == -1e-3 for p in polish_points
    )


@pytest.mark.requires_qics
@pytest.mark.contract
def test_a_failed_polish_leaves_the_first_set_s_bracket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Item (i): a polish that fails keeps what it assessed (here nothing).

    The polish's first assessment raises; its stop cause names the failure,
    it keeps no point, and the companion's bracket is the first set's.
    """
    pytest.importorskip("qics")
    from certiqs_key.solvers.frank_wolfe import reference

    def failing(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("a failing assessment (test)")

    monkeypatch.setattr(reference, "assess_candidate", failing)
    record = _run(_config(max_iterations=20))
    bracket = _rate(record)["reference_bracket"]
    assert bracket["status"] == "counted"
    polish = bracket["polish"]
    assert polish["ran"] is True and polish["stop_cause"] == "assessment_failure"
    assert "failing assessment" in polish["detail"]
    assert polish["points_assessed"] == 0
    assert {p["set"] for p in bracket["points"]} == {"search"}
    assert bracket["h_lb_reference"] == max(
        p["bracket_reference"]
        for p in bracket["points"]
        if p["bracket_reference"] is not None
    )


@pytest.mark.requires_qics
@pytest.mark.contract
def test_the_fw_polish_starts_from_the_start_point_s_exact_q(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Item (i), the FW path: no corrective search, so FW from the start's q.

    The corrective search is made unsupported; the polish runs the
    Frank-Wolfe driver, handed the start point's acceptance-side iterate
    (start_q) exactly as the search consumed it, and its points contribute
    on the companion (gate of (ii), no perturbation).
    """
    pytest.importorskip("qics")
    from certiqs_key.solvers.frank_wolfe import joint_driver
    from certiqs_key.solvers.search import common

    monkeypatch.setattr(common, "capability_reason", lambda *args: "forced")
    seen: list[Any] = []
    original = joint_driver.run_joint_frank_wolfe

    def spy(*args: Any, **kwargs: Any) -> Any:
        seen.append((args[3], kwargs.get("start_q")))
        return original(*args, **kwargs)

    monkeypatch.setattr(joint_driver, "run_joint_frank_wolfe", spy)
    record = _run(_config(max_iterations=20))
    bracket = _rate(record)["reference_bracket"]
    polish = bracket["polish"]
    assert polish["ran"] is True and polish["method"] == "fw"
    # The search on D runs FW too (explicit fw): the polish's call is the one
    # handed a start_q, and only one is.
    seeded = [(start, q) for start, q in seen if q is not None]
    assert len(seeded) == 1
    _, start_q = seeded[0]
    assert start_q.on_island and start_q.exact is not None
    first = bracket["points"][0]
    assert first["set"] == "search" and polish["start_index"] == 0
    polish_points = [p for p in bracket["points"] if p["set"] == "polish"]
    assert polish_points
    assert all(p["withdrawal_reference"] is None for p in polish_points)


@pytest.mark.requires_qics
@pytest.mark.contract
def test_a_polish_cut_at_its_third_assessment_keeps_the_two_before(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Item (i): "a polish that fails ... keeps ... the points it assessed".

    The rotated device (angle 1/7, cutoff 2) at 20 FW iterations, on which the
    polish assesses three points; the third raises. The first two are kept
    and evaluated beside the search's.
    """
    pytest.importorskip("qics")
    from certiqs_key.solvers.frank_wolfe import reference

    original = reference.assess_candidate
    calls = [0]

    def third_fails(*args: Any, **kwargs: Any) -> Any:
        calls[0] += 1
        if calls[0] == 3:
            raise ValueError("the third assessment fails (test)")
        return original(*args, **kwargs)

    monkeypatch.setattr(reference, "assess_candidate", third_fails)
    config = _config(max_iterations=20)
    config = config.with_(device={**config.device, "half_wave_angle": F(1, 7)})
    bracket = _rate(_run(config))["reference_bracket"]
    polish = bracket["polish"]
    assert calls[0] == 3
    assert polish["points_assessed"] == 2
    assert polish["stop_cause"] == "assessment_failure"
    assert "third assessment" in polish["detail"]
    kept = [p for p in bracket["points"] if p["set"] == "polish"]
    assert 1 <= len(kept) <= 2


@pytest.mark.requires_qics
@pytest.mark.contract
def test_a_warm_start_and_a_perturbation_do_not_reach_the_polish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Items (i), (ii): the polish drops the run's warm start and perturbation.

    The settings handed to the companion's evaluation carry a warm start (a
    run's seed) and a gradient perturbation. A warm start beside the polish's
    own start would be refused at its preparation, and a perturbation would
    withdraw every polish point (gradient_perturbation_applied); the polish
    runs, and its points contribute.
    """
    pytest.importorskip("qics")
    from certiqs_key.solvers.frank_wolfe import general_keyrate, reference
    from certiqs_key.solvers.frank_wolfe.joint_options import (
        JointFrankWolfeOptions,
        WarmStart,
    )

    original = reference.bracket_on_reference

    def seeded(*args: Any, **kwargs: Any) -> Any:
        settings = args[5]
        assert isinstance(settings, JointFrankWolfeOptions)
        settings = replace(
            settings,
            gradient_perturbation=1e-9,
            warm_start=WarmStart({}, "untrusted", 0),
        )
        return original(*args[:5], settings, *args[6:], **kwargs)

    monkeypatch.setattr(general_keyrate, "bracket_on_reference", seeded)
    bracket = _rate(_run(_config(max_iterations=20)))["reference_bracket"]
    polish = bracket["polish"]
    assert polish["ran"] is True and polish["stop_cause"] != "preparation_failure"
    kept = [p for p in bracket["points"] if p["set"] == "polish"]
    assert kept and all(p["withdrawal_reference"] is None for p in kept)


@pytest.mark.requires_qics
@pytest.mark.contract
def test_each_certified_point_names_its_set_and_order() -> None:
    """req:certified-evaluation (i), (ix): the record says which set and when.

    On the rotated device the polish's point is the best and is certified:
    the certified record names it polish, with a sequence after every search
    point's.
    """
    pytest.importorskip("qics")
    config = _config(max_iterations=20)
    config = config.with_(device={**config.device, "half_wave_angle": F(1, 7)})
    rate = _rate(_run(config))
    certified = rate["certified"]
    assert certified["declaration"] == "reference_companion"
    points = certified["points"]
    assert points and all(p["set"] in ("search", "polish") for p in points)
    assert all(isinstance(p["sequence"], int) for p in points)
    search = [p["sequence"] for p in points if p["set"] == "search"]
    polish = [p["sequence"] for p in points if p["set"] == "polish"]
    assert polish and all(s < q for s in search for q in polish)
    assert len({p["sequence"] for p in points}) == len(points)


# ===========================================================================
#  Canaries: the regime the polish was made for (full tier)
# ===========================================================================

#: The probe regime of solvers/stagnation-at-small-per-round-probabilities:
#: BBM92, SPDC source, 0.05 pairs per round, transmittance 1/10 and 6/1000,
#: efficiencies 3/5 and 1/5 (normalized by the receiver's default), photon
#: cutoff 1, encoded route, n = 2e11, alpha = 1.05, method auto (120 s).
#: Without the polish each gave the key length 0.
#: The least share of the bound on D the bound on D^ref must reach: at dark
#: counts 1e-6 and 1e-8 the polish recovers D's bound (measured to about
#: 1e-7 relative); at 1e-4 the search on D itself is slow (its bound below
#: half its estimate) and the polish recovers about 0.8 of it.
CANARY_FRACTION = {"1/1000000": 0.99, "1/100000000": 0.99, "1/10000": 0.5}


def _canary_config(dark: str) -> Any:
    from instances import surface_of

    from certiqs_key.runs.config import SolverSettings

    surface = surface_of("bbm92")
    base = surface.default_config(
        solver=SolverSettings(method="auto", budget_seconds=120)
    )
    device = {
        **base.device,
        "source_model": "spdc",
        "route": "encoded",
        "alice_efficiency": dict.fromkeys(PORTS, F(3, 5)),
        "bob_efficiency": dict.fromkeys(PORTS, F(1, 5)),
        "alice_dark_count": dict.fromkeys(PORTS, F(dark)),
        "bob_dark_count": dict.fromkeys(PORTS, F(dark)),
    }
    model = {
        **base.model,
        "mean_pairs": F(1, 20),
        "alice_transmittance": F(1, 10),
        "bob_transmittance": F(6, 1000),
    }
    return base.with_(device=device, model=model, rounds=200_000_000_000).with_(
        alpha=1.05
    )


@pytest.mark.slow
@pytest.mark.requires_qics
@pytest.mark.parametrize("dark", sorted(CANARY_FRACTION))
def test_the_small_probability_regime_keeps_a_positive_key(dark: str) -> None:
    """The probe regime: a positive certified key, the bound on D^ref near D's.

    The polish ran within its share and the key is certified on the companion.
    """
    pytest.importorskip("qics")
    from instances import surface_of

    from certiqs_key.runs.record import record_run
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    config = _canary_config(dark)
    surface = surface_of("bbm92")
    with tempfile.TemporaryDirectory() as tmp:
        outcome = surface.runner(QicsSectorChoiOracle(), Path(tmp), created_by="t")(
            config, 0
        )
        record = record_run(outcome, config, created_by="t").as_dict()
    rate = record["payload"]["stages"]["key_rate"]
    bracket = rate["reference_bracket"]
    assert rate["key_length"] is not None and rate["key_length"] > 0
    assert rate["reported_tier"] == "certified"
    assert rate["certified"]["declaration"] == "reference_companion"
    snapped = bracket["snapped"]["h_lb"]
    assert snapped > 0
    assert bracket["h_lb_reference"] >= CANARY_FRACTION[dark] * snapped
    polish = bracket["polish"]
    assert polish["ran"] is True and polish["budget_seconds"] == pytest.approx(12.0)
    assert polish["seconds"] <= polish["budget_seconds"] + 2.0
