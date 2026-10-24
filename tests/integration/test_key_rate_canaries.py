"""Key-rate canaries: realistic devices, each with a recorded key.

WHY THIS EXISTS. A key-rate regression can send keys to 0, get them refused
or overstate them (decoy N = 2 at half-wave angle 1/7 once reached
h_low = 3.06 bits per round), while a test suite that asserts statuses and
record shapes passes. Each case below is one realistic device, at a small
fixed Frank-Wolfe budget, and asserts that the run is not refused, that its
key is positive, and that the key is within ``REL_TOL`` of the value recorded
here.

THE TIER: every canary also asserts the tier it reaches. They are certified,
with the key the first-order number gives (``frank-wolfe/req:certified-
evaluation``; the certified key equals the first-order one wherever it covers
a run). The receiver's weight is the enclosed one rounded down
(``receiver/req:rigorous-weight``), with no ``eps_eig`` where the exact window
binds (0.499 -> 0.4999...), so the declaration and the fixed-budget search
depend on it.

The three ideal devices at a 1/7 angle are certified on the REFERENCE
COMPANION: the receiver gives the analyser's rank-deficient elements in factor
form (``receiver/detector-imperfections/req:dark-composed-reference`` (vii)),
the reductions and the compiler carry it, and the certified evaluation's
factor rule fixes their ranks, with no premise and the key the first-order
number gives. (Their companion's rank-deficient analyser elements are
otherwise known only as balls, and no entrywise enclosure fixes such a rank,
``rem:certified-scope``.) Each canary asserts the declaration its number is
formed on.

SEVERAL REPLACED FACTORS: the companion's claims are stated for every measured
factor it replaces, both stations of bbm92, any of them known through
enclosures; ``bbm92-noisy-both-angle-1/7`` reads both stations through
enclosures and certifies on the companion.

A REGRESSION SNAPSHOT, NOT AN ORACLE (PRINCIPLES.md 2.3 is not engaged): the
values are what the engine computed, not hand derivations. A change that moves
one deliberately updates the value here, and its commit says why; a change
that moves one by accident fails here. Run these before committing a change to
the snap, reduction or solver code (``pytest --full
tests/integration/test_key_rate_canaries.py``); they are ``slow`` and not in
the edit loop.

The budgets sit where the key has nearly converged at that budget, so that the
tolerance absorbs floating-point noise, not convergence. Every canary runs on
the one path (no certification option, no domination link).
"""

from __future__ import annotations

import importlib
import json
import tempfile
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path
from typing import Any

import pytest

from certiqs_key.runs.config import RunConfig, SolverSettings
from certiqs_key.runs.record import record_run

pytestmark = [pytest.mark.slow, pytest.mark.requires_qics]
pytest.importorskip("qics")

#: The relative tolerance on a recorded key. Each run is deterministic at its
#: fixed budget; the tolerance is for platform floating-point differences, and
#: is far below the effects the hunt found (key 0, refusal, or 6x and more).
REL_TOL = 0.03

PORTS = ("H", "V", "D", "A")

#: The realistic single-port device of the hunt: efficiency 0.9, dark count
#: 1e-6 on every port.
#:
#: DECLARED AT THE FACTORED LOSS ONE
#: (receiver/detector-imperfections/req:efficiency-normalization), as every
#: canary below at an efficiency under one is: their keys were recorded on the
#: device's own station, and at their small fixed budgets a normalized station
#: is not converged -- at the full normalization t = eta_max, at 20
#: iterations optical-N1 gives 1207 and bbm92 at efficiency 4/5 12,077,973 --
#: while at 200 iterations of the auto method the two agree (optical-N1 1491
#: against 1490, bbm92 4/5 32,146,200 against 32,146,194, bbm92 noisy at 1/7
#: 31,362,544 against 31,375,157). The normalized default is the canaries of
#: the worked example and of the encoded-N2 device below.
NOISY: dict[str, Any] = {
    "efficiency": dict.fromkeys(PORTS, F(9, 10)),
    "dark_count": dict.fromkeys(PORTS, F(1, 10**6)),
    "efficiency_normalization": F(1),
}


#: The same device at both stations of bbm92.
NOISY_PAIR: dict[str, Any] = {
    f"{station}_{key}": value
    for station in ("alice", "bob")
    for key, value in NOISY.items()
}


def _cutoff(photons: int) -> dict[str, F]:
    """Return the receiver's photon cutoff ``N`` with its exact window ``N + 1``."""
    return {"photon_cutoff": F(photons), "exact_window": F(photons + 1)}


@dataclass(frozen=True)
class Canary:
    instance: str
    #: Device keys that override the instance's default device.
    device: dict[str, Any]
    #: The Frank-Wolfe iteration budget.
    iterations: int
    #: The recorded key length at that budget.
    key: int
    #: The tier the run reaches (``certified`` or ``first-order``).
    tier: str = "certified"
    #: The declaration the certified number is formed on (record 0.35.0):
    #: ``reference_companion``, or ``searched`` where the run has no counted
    #: companion or its number is certified in the fallback.
    declaration: str = "reference_companion"


CANARIES: dict[str, Canary] = {
    # Encoded route, positive weight (once 1490 -> 0). 1482 from the search's
    # points alone; the companion polish (frank-wolfe/req:bracket-on-reference
    # (i)) continues the 20-iteration search on the companion.
    "optical-N1-noisy-encoded": Canary("optical_bb84", {**NOISY}, 20, 1489),
    "optical-N2-noisy-licensed": Canary(
        "optical_bb84", {**_cutoff(2), **NOISY, "route": "licensed"}, 20, 1482
    ),
    # Decoy (once loss 5.19M -> 0). The blocks are snapped by the
    # fidelity-first rows.
    "decoy-N2-noisy-encoded": Canary(
        "decoy_bb84", {**_cutoff(2), **NOISY}, 40, 8957180
    ),
    # Round-down-and-place once overstated this key (40,482,456 at N = 1).
    # The receiver's weight is the rigorous one (the exact window without
    # eps_eig at both stations: 0.5). Certified on the companion, through the
    # receiver's factor form (req:certified-evaluation (iv)(b)); the key equals
    # the first-order one. 6404026 from the search's points alone, before the
    # companion polish.
    "decoy-N1-ideal-angle-1/7": Canary(
        "decoy_bb84", {"half_wave_angle": F(1, 7)}, 40, 7530049, "certified"
    ),
    # bbm92 (peer case once 27,962,546 -> 0 encoded; refused with
    # constraint_channel_mismatch licensed). The receiver's weight is the
    # rigorous one (Alice's exact window without eps_eig: 0.5).
    "bbm92-efficiency-4/5-encoded": Canary(
        "bbm92",
        {
            "bob_efficiency": dict.fromkeys(PORTS, F(4, 5)),
            "bob_efficiency_normalization": F(1),
        },
        20,
        32137178,
    ),
    # No domination link is emitted, so the licensed route's flag entries are
    # not corrected for a carried weight. The feasible side of every bracket
    # is the bound verified from the oracle's dual
    # (frank-wolfe/req:verified-feasible-side), not the pairing with its
    # return, and the receiver's weight is the rigorous one, so the
    # declaration and the 20-iteration search depend on it.
    "bbm92-efficiency-4/5-licensed": Canary(
        "bbm92",
        {
            "bob_efficiency": dict.fromkeys(PORTS, F(4, 5)),
            "bob_efficiency_normalization": F(1),
            "route": "licensed",
        },
        20,
        32137719,
    ),
    # spdc (once overstated, 1.03M -> 31.5M). The receiver's weight is the
    # rigorous one at both stations (0.5). The search is not converged at 200
    # iterations: at 600 the floating-point weight gives 1047411 and the
    # rigorous one 1049304, the larger weight the larger key. Certified on the
    # companion, through the receiver's factor form; the key equals the
    # first-order one.
    "bbm92-spdc-angle-1/7-at-bob": Canary(
        "bbm92",
        {"source_model": "spdc", "bob_half_wave_angle": F(1, 7)},
        200,
        996781,
        "certified",
    ),
    # Both stations read through enclosures of positive radius: realistic
    # detectors at both, both analysers at angle 1/7
    # (meat-core/prop:reference-companion and
    # frank-wolfe/lem:certified-bracket-enclosed): the certifier reads both
    # stations, so the number is certified on the companion without the
    # fallback and its A-SNAP premise.
    "bbm92-noisy-both-angle-1/7": Canary(
        "bbm92",
        {
            **NOISY_PAIR,
            "alice_half_wave_angle": F(1, 7),
            "bob_half_wave_angle": F(1, 7),
        },
        20,
        30579480,
        "certified",
    ),
    # Round-down-and-place once refused this run. The receiver's weight is the
    # rigorous one (+-5e-16 where the analytic remainder binds), which moves
    # the 20-iteration search. Certified on the companion, through the
    # receiver's factor form; the key equals the first-order one.
    "optical-N2-ideal-angle-1/7": Canary(
        "optical_bb84",
        {**_cutoff(2), "half_wave_angle": F(1, 7)},
        20,
        1321,
        "certified",
    ),
    # No domination link, so the Eq. 27 entry stays in force, and the run needs
    # a larger budget: the key is unchanged at 140 and 200 iterations. The
    # Eq. 27 entry is formed on the reference companion, which needs its a to
    # hold of the receiver model as well; the instance's a is therefore 6/2^40
    # (the reference's floor) rather than 7/2^40 (the snapped block's), a
    # weaker entry on both declarations. At 2000 iterations the key is
    # 5905463; at 100 it was 5376396 from the search's points alone, before
    # the companion polish continued the search on the companion.
    "decoy-N1-noisy-licensed+two-sector": Canary(
        "decoy_bb84", {**NOISY, "route": "licensed+two-sector"}, 100, 5984616
    ),
}


def _record(
    canary: Canary, certified_evaluation: str | None = None
) -> dict[str, Any]:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = importlib.import_module(f"instances.{canary.instance}.surface")
    base: RunConfig = surface.default_config()
    config = base.with_(
        device={**base.device, **canary.device},
        solver=SolverSettings.from_choices(
            max_iterations=canary.iterations, certified_evaluation=certified_evaluation
        ),
    )
    with tempfile.TemporaryDirectory() as tmp:
        outcome = surface.runner(QicsSectorChoiOracle(), Path(tmp), created_by="t")(
            config, 0
        )
        record: dict[str, Any] = record_run(outcome, config, created_by="t").as_dict()
    loaded: dict[str, Any] = json.loads(json.dumps(record))
    return loaded


@pytest.mark.parametrize("name", list(CANARIES))
def test_the_canary_keeps_its_key(name: str) -> None:
    canary = CANARIES[name]
    payload = _record(canary)["payload"]
    assert payload["refused"] is False, payload.get("reason")
    key = payload["stages"]["key_rate"]["key_length"]
    assert key is not None and key > 0, key
    assert key == pytest.approx(canary.key, rel=REL_TOL), (
        f"{name}: key {key}, recorded {canary.key}; a deliberate change updates "
        "the recorded value and says why in its commit"
    )
    key_rate = payload["stages"]["key_rate"]
    certified = key_rate["certified"]
    assert key_rate["reported_tier"] == canary.tier, certified["reasons"]
    if canary.tier == "certified":
        # The certified key equals the first-order one (the tightness gate).
        assert certified["status"] == "certified"
        assert key == certified["first_order_key_length"]
        assert certified["declaration"] == canary.declaration
        # No canary runs the fallback: no premise at the snap, no second run.
        assert certified["premises"] == [] and "companion_points" not in certified
    else:
        assert certified["status"] == "not_certified"
        assert all(
            point["reasons"] == ["rank_not_certified"] for point in certified["points"]
        )


#: The efficiency normalization's worked example:
#: passive bbm92 stations at efficiencies 3/5 and 1/5, arm transmittances 1/10
#: and 1/1000, visibility 47/50, n = 1.9e11, lambda_EC estimated at f_EC 1.1.
#: Analysed as declared it gave key 0 (at a development commit); under the efficiency
#: normalization (receiver/detector-imperfections/req:efficiency-normalization,
#: on by default) it keeps a key. Recorded at the default factors 20/33
#: (Alice, eta_max 3/5) and 20/99 (Bob, eta_max 1/5), alpha 1.0005, 200
#: iterations of the auto method (about 37 s); at the full normalization
#: t = eta_max it gave 494,332, and there the full search at 600 s per alpha
#: gave 538,717.
OPEN_ITEM_EXAMPLE_KEY = 494486


def _open_item_payload(device_extra: dict[str, Any]) -> dict[str, Any]:
    """Run the worked example with ``device_extra`` and return its payload."""
    from certiqs_key.runs.error_correction import with_estimated_lambda_ec
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = importlib.import_module("instances.bbm92.surface")
    base: RunConfig = surface.default_config()
    config = base.with_(
        rounds=190_000_000_000,
        model={
            **base.model,
            "alice_transmittance": F(1, 10),
            "bob_transmittance": F(1, 1000),
            "visibility": F(47, 50),
        },
        device={
            **base.device,
            "alice_efficiency": dict.fromkeys(PORTS, F(3, 5)),
            "bob_efficiency": dict.fromkeys(PORTS, F(1, 5)),
            **device_extra,
        },
        solver=SolverSettings(method="auto", max_iterations=200),
        alpha=1.0005,
    )
    config, _ = with_estimated_lambda_ec(config, surface.preparation(config), f_ec=1.1)
    with tempfile.TemporaryDirectory() as tmp:
        outcome = surface.runner(QicsSectorChoiOracle(), Path(tmp), created_by="t")(
            config, 0
        )
        record = record_run(outcome, config, created_by="t").as_dict()
    payload: dict[str, Any] = json.loads(json.dumps(record))["payload"]
    return payload


def test_the_open_item_example_keeps_a_key_under_the_normalization() -> None:
    payload = _open_item_payload({})
    assert payload["refused"] is False, payload.get("reason")
    factors = [
        station["receiver"]["efficiency_record"]["normalization"]
        for station in payload["stages"]["stations"]
    ]
    assert all(normalization["applied"] is True for normalization in factors)
    # The default factor eta_max / (99/100): (3/5)(100/99) and (1/5)(100/99).
    assert [normalization["factored_loss"] for normalization in factors] == [
        "20/33",
        "20/99",
    ]
    key_rate = payload["stages"]["key_rate"]
    assert key_rate["key_length"] == pytest.approx(OPEN_ITEM_EXAMPLE_KEY, rel=REL_TOL)
    assert key_rate["reported_tier"] == "certified"


#: The bbm92 study's headline device at photon cutoff 2 on the encoded route:
#: passive stations at efficiency 4/5 and dark count 1e-7 on every port, exact
#: window 3, 10 dB in total (each arm at the binary64 10^-1/2, read exactly as
#: 5696652996790543/2^54), visibility 49/50 (QBER 1 %), 1.6e7 rounds, the
#: declared lambda_EC, alpha 1.05, 200 iterations of the auto method. At the
#: full normalization t = eta_max it gives key 0: the two-photon block on which
#: the normalized station's elements are singular is lifted by the snap and the
#: lifted directions are counted by the support check
#: (receiver/detector-imperfections/rem:normalization-scope). At the default
#: factor 80/99 it certifies a key. Recorded at the default, about 18 s.
ENCODED_N2_KEY = 333709


def test_the_encoded_n2_device_keeps_its_key_by_default() -> None:
    """The default factor stops short of eta_max, and the device keeps its key.

    ``req:efficiency-normalization``: at ``eta_max = 4/5`` the default is
    ``(4/5)(100/99) = 80/99`` at both stations.
    """
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = importlib.import_module("instances.bbm92.surface")
    base: RunConfig = surface.default_config()
    arm = F(5696652996790543, 2**54)
    config = base.with_(
        rounds=16_000_000,
        model={
            **base.model,
            "alice_transmittance": arm,
            "bob_transmittance": arm,
            "visibility": F(49, 50),
        },
        device={
            **base.device,
            **{
                f"{station}_{key}": value
                for station in ("alice", "bob")
                for key, value in (
                    ("efficiency", dict.fromkeys(PORTS, F(4, 5))),
                    ("dark_count", dict.fromkeys(PORTS, F(1, 10**7))),
                    ("photon_cutoff", F(2)),
                    ("exact_window", F(3)),
                )
            },
            "route": "encoded",
        },
        solver=SolverSettings(method="auto", max_iterations=200),
        alpha=1.05,
    )
    with tempfile.TemporaryDirectory() as tmp:
        outcome = surface.runner(QicsSectorChoiOracle(), Path(tmp), created_by="t")(
            config, 0
        )
        record = record_run(outcome, config, created_by="t").as_dict()
    payload: dict[str, Any] = json.loads(json.dumps(record))["payload"]
    assert payload["refused"] is False, payload.get("reason")
    for station in payload["stages"]["stations"]:
        normalization = station["receiver"]["efficiency_record"]["normalization"]
        assert normalization["applied"] is True
        assert normalization["factored_loss"] == "80/99"
    key_rate = payload["stages"]["key_rate"]
    key = key_rate["key_length"]
    assert key is not None and key > 0, key_rate["key_length_reason"]
    assert key == pytest.approx(ENCODED_N2_KEY, rel=REL_TOL)
    assert key_rate["reported_tier"] == "certified"


#: The worked example with dark counts 1e-7 on every port at photon cutoff
#: 2 (exact window 3): it gives key 0 at t = 1 and at the full normalization
#: t = eta_max (the latter by rem:normalization-scope's engine handling), and
#: the default factors 20/33 and 20/99 certify a key. Recorded at the default,
#: about 25 s.
OPEN_ITEM_DARK_N2_KEY = 485029


def test_the_open_item_example_with_dark_counts_keeps_a_key_by_default() -> None:
    dark = dict.fromkeys(PORTS, F(1, 10**7))
    payload = _open_item_payload(
        {
            "alice_dark_count": dark,
            "bob_dark_count": dark,
            "alice_photon_cutoff": F(2),
            "bob_photon_cutoff": F(2),
            "alice_exact_window": F(3),
            "bob_exact_window": F(3),
        }
    )
    assert payload["refused"] is False, payload.get("reason")
    assert [
        station["receiver"]["efficiency_record"]["normalization"]["factored_loss"]
        for station in payload["stages"]["stations"]
    ] == ["20/33", "20/99"]
    key_rate = payload["stages"]["key_rate"]
    assert key_rate["key_length"] == pytest.approx(OPEN_ITEM_DARK_N2_KEY, rel=REL_TOL)
    assert key_rate["reported_tier"] == "certified"


def test_the_open_item_example_has_no_key_analysed_as_declared() -> None:
    """The worked example's regression: at t = 1 on both stations the key is zero.

    The same run with each station's ``efficiency_normalization`` declared 1,
    so both receivers are compiled at their declared efficiencies: the
    example keeps no key, which is what the normalization exists to change
    (``rem:normalization-gain``).
    """
    payload = _open_item_payload(
        {"alice_efficiency_normalization": F(1), "bob_efficiency_normalization": F(1)}
    )
    assert payload["refused"] is False, payload.get("reason")
    for station in payload["stages"]["stations"]:
        normalization = station["receiver"]["efficiency_record"]["normalization"]
        assert normalization["applied"] is False
        assert normalization["factored_loss"] == "1"
    assert payload["stages"]["key_rate"]["key_length"] == 0


def test_strict_refuses_a_run_that_does_not_certify(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A run that certifies on neither declaration (not even the fallback).

    The ideal device certifies, so every Gram of a pass class is
    refused here: ``support_not_established`` on the companion and, in the
    fallback, on the searched declaration.
    """
    from certiqs_key.foundations import balls

    def refused(*_: Any, **__: Any) -> Any:
        raise balls.NotCertified("forced by the test")

    monkeypatch.setattr(balls, "cholesky_upper", refused)
    payload = _record(CANARIES["optical-N2-ideal-angle-1/7"], "strict")["payload"]
    solve = payload["stages"]["solve"]
    assert payload["refused"] is True and solve["refused"] is True
    assert solve["reason"] == "certification_refused"
    assert "support_not_established" in solve["detail"]
    assert "per point on the reference companion" in solve["detail"]
    assert payload["config"]["solver"]["advanced"]["certified_evaluation"] == "strict"


def test_without_the_ball_arithmetic_the_run_stays_first_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from certiqs_key.foundations import balls

    monkeypatch.setattr(balls, "AVAILABLE", False)
    payload = _record(CANARIES["optical-N1-noisy-encoded"])["payload"]
    key_rate = payload["stages"]["key_rate"]
    assert key_rate["reported_tier"] == "first-order"
    assert key_rate["key_length"] == CANARIES["optical-N1-noisy-encoded"].key
    reasons = key_rate["certified"]["reasons"]
    assert reasons == ["not_certified", "certifier_unavailable"]


@pytest.mark.parametrize("name", ["optical-N1-noisy-encoded", "decoy-N2-noisy-encoded"])
def test_the_engine_gradient_lies_in_the_certified_enclosure_on_a_canary(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Plan section 3 rule 6, on canary points: the two evaluations agree.

    At every point the certified evaluation formed, the engine's binary64
    gradient (the companion's assessment where the bound counts on it) lies
    within ``1e-9`` of the largest entry, plus twice the radius, of the
    certified enclosure (measured at most ``1.8e-12``).
    """
    from certiqs_key.solvers.frank_wolfe import general_keyrate

    seen: list[tuple[Any, Any, Any]] = []
    original = general_keyrate._certify

    def spy(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        seen.append((args[1], args[2], result))
        return result

    monkeypatch.setattr(general_keyrate, "_certify", spy)
    _record(CANARIES[name])
    ((run, reference, result),) = seen
    assessments = (
        [item.reference for item in reference.certification_points()]
        if reference is not None
        else [kept.assessment for kept in run.reference_candidates]
    )
    assert result.status == "certified"
    for assessment, point in zip(assessments, result.points, strict=True):
        engine = assessment.gradient
        scale = max(abs(float(x.mid())) for x in point.gradient_q.values())
        for chat, ball in point.gradient_q.items():
            gap = abs(engine.q[chat] - float(ball.mid()))
            assert gap <= 1e-9 * scale + 2 * float(ball.rad())
        def mids(ball: Any) -> list[list[complex]]:
            n = ball.shape[0]
            return [[complex(float(ball.m[i, j].real.mid()),
                             float(ball.m[i, j].imag.mid())) for j in range(n)]
                    for i in range(n)]

        centres = {pair: mids(ball) for pair, ball in point.gradient_blocks.items()}
        biggest = max(abs(z) for rows in centres.values() for row in rows for z in row)
        for pair, rows in centres.items():
            radius = point.gradient_blocks[pair].radius()
            for i, row in enumerate(rows):
                for j, centre in enumerate(row):
                    gap = abs(engine.blocks[pair][i, j] - centre)
                    assert gap <= 1e-9 * biggest + 2 * radius
