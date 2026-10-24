"""In the fallback the key length is the fallback's certified number's alone.

``meat-core/frank-wolfe/req:certified-evaluation`` (vi): in the fallback "no
number is formed from the two together: the key length is that of the
fallback's certified number alone, whether the companion's first-order number
gives a larger key length or a smaller one". In the fallback tests elsewhere
the two key lengths are equal, so a key length taken as the larger of the two
would pass them. Here the fallback's certified number is lowered by 1/20 bit
per round, standing in for a searched declaration that certifies less than the
companion's first-order bound, and the key length must follow it down.

The run is the ideal optical device at angle 1/7 (N = 2, 20 iterations) with
the factor form taken away, as in
``tests/integration/test_certified_evaluation_reads_the_companion.py``.
"""

from __future__ import annotations

import dataclasses
import importlib
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("flint")


def test_the_fallback_key_length_is_the_certified_numbers_alone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("qics")
    from certiqs_key.meat_core.finitekey.keylength import certified_key_length
    from certiqs_key.runs.config import SolverSettings
    from certiqs_key.runs.record import record_run
    from certiqs_key.solvers.frank_wolfe import certified, general_keyrate
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    real_evaluate = certified.evaluate
    # The solve's own binding is patched below; the real function is the
    # module's that defines it.
    real_length = certified_key_length
    lengths: list[tuple[Fraction, int]] = []

    def evaluate(maps: Any, *args: Any, **kwargs: Any) -> Any:
        result = real_evaluate(maps, *args, **kwargs)
        if kwargs.get("companion") is None and result.certified_bound is not None:
            lowered = result.certified_bound - Fraction(1, 20)
            return dataclasses.replace(result, certified_bound=lowered)
        return result

    def length(**kwargs: Any) -> Any:
        found = real_length(**kwargs)
        lengths.append((kwargs["h"], found[0]))
        return found

    monkeypatch.setattr(certified, "_carried", lambda *_: None)
    monkeypatch.setattr(certified, "evaluate", evaluate)
    monkeypatch.setattr(general_keyrate, "certified_key_length", length)
    surface = importlib.import_module("instances.optical_bb84.surface")
    base = surface.default_config()
    config = base.with_(
        device={
            **base.device,
            "photon_cutoff": Fraction(2),
            "exact_window": Fraction(3),
            "half_wave_angle": Fraction(1, 7),
        },
        solver=SolverSettings(method="fw", max_iterations=20),
    )
    with tempfile.TemporaryDirectory() as scratch:
        runner = surface.runner(QicsSectorChoiOracle(), Path(scratch), created_by="t")
        record = record_run(runner(config, 0), config, created_by="t").as_dict()
    key_rate = record["payload"]["stages"]["key_rate"]
    certified_record = key_rate["certified"]
    assert key_rate["reported_tier"] == "certified"
    assert certified_record["declaration"] == "searched"
    assert "companion_points" in certified_record
    ((_, fallback_length),) = lengths
    first_order_length = certified_record["first_order_key_length"]
    assert fallback_length < first_order_length, "the case needs a smaller length"
    assert key_rate["key_length"] == fallback_length
