"""The entropy stage at a small key-round mass (solvers/search/entropy.py).

The regime of small per-round probabilities:
bbm92 with an SPDC source of 0.05 mean pairs per round, transmittances 1/10
and 6/1000, efficiencies 3/5 and 1/5, dark counts 1e-6, photon cutoff 1, the
encoded route, n = 2e11, alpha 1.05, so that a round is a key round with
probability about 1.8e-6. There the entropy stage of the auto portfolio ended
"division by zero" in about 0.3 s on every run and its budget share went to
the other stages: the encoded route holds transcript classes no outcome pair
realises, and QICS's QuantKeyDist cannot be built on an empty Kraus operator.
The explicit entropy method runs that stage alone; with such classes left out
of the cone it solves and hands its point to the polish.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest
from instances import surface_of

from certiqs_key.runs.config import SolverSettings
from certiqs_key.runs.record import record_run

pytestmark = [pytest.mark.slow, pytest.mark.requires_qics]

PORTS = ("H", "V", "D", "A")


def test_the_entropy_stage_solves_at_a_small_key_round_mass(tmp_path: Path) -> None:
    pytest.importorskip("qics")
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = surface_of("bbm92")
    base = surface.default_config()
    dark = Fraction(1, 10**6)
    config = base.with_(
        model={
            **base.model,
            "alice_transmittance": Fraction(1, 10),
            "bob_transmittance": Fraction(6, 1000),
            "mean_pairs": Fraction(1, 20),
        },
        device={
            **base.device,
            "source_model": "spdc",
            "alice_efficiency": dict.fromkeys(PORTS, Fraction(3, 5)),
            "bob_efficiency": dict.fromkeys(PORTS, Fraction(1, 5)),
            "alice_dark_count": dict.fromkeys(PORTS, dark),
            "bob_dark_count": dict.fromkeys(PORTS, dark),
        },
        rounds=200_000_000_000,
        alpha=1.05,
        solver=SolverSettings.from_choices(method="entropy", budget_seconds=90),
    )
    runner = surface.runner(QicsSectorChoiOracle(), tmp_path, created_by="test")
    record = record_run(runner(config, 0), config, created_by="test").as_dict()
    payload = record.get("payload", record)
    key_rate = payload["stages"]["key_rate"]
    # The regime: the estimate is of the order of the key-round mass.
    assert 0 < key_rate["h_low"] < 1e-5
    (attempt,) = key_rate["search_report"]["attempts"]
    assert attempt["method"] == "entropy"
    diagnostics = attempt["diagnostics"]
    assert "division by zero" not in str(diagnostics.get("reason"))
    assert attempt["termination"] != "numerical_failure", diagnostics
    assert diagnostics["cone_status"] in ("optimal", "near_optimal")
    assert "polish" in diagnostics
