r"""The receiver's rigorous multiclick weight (``receiver/req:rigorous-weight``).

CONTRACT TESTS of ``receiver/thm:enclosed-weight`` as the engine emits it,
against values derived BY HAND from the claims' formulas (``def:pmcex``,
``eq:beta``), not regenerated from code:

* The ideal passive BB84 receiver at ``N = 1`` with the exact window
  ``m* = 2`` (the bbm92 instance's default station; ``component-catalogue/
  ex:bb84exact``): ``B = A_Sigma = 1`` and ``B_k = A_{[K]\\k}`` with least
  eigenvalue ``1/2``, so ``gamma = beta_k = 1``, ``c = 0``, ``d_k = 1/2``;
  ``beta(2) = 1 - 4 (1/2)^2 = 0``, ``beta(3) = 1 - 4 (1/2)^3 = 1/2``; the
  exact window ``beta*(2) = 1/2`` (ex:bb84exact), so ``l(2) = 1/2`` and the
  weight (predicate (X) holds) is ``min{l(2), beta(3)} = 1/2``. The
  floating-point weight subtracts ``eps_eig = 1e-3`` (0.499); the rigorous
  one subtracts nothing, so it lies within the enclosures' width of 1/2.
* The noisy receiver of the optical canary (efficiency 9/10 on every port,
  ``N = 1``, ``m* = 2``): ``c = 1 - 9/10``, ``d_k = 1 - 9/20``, so
  ``beta(3) = 1 + 3 (1/10)^3 - 4 (11/20)^3 = 27/80``; ``beta(2) < 0`` and
  ``beta*(2) > 27/80``, so the weight is ``27/80``.

In both the emitted weight is at most the exact value (the rounding is
downward and the enclosures conservative), within ``1e-14`` of it, and the
artifact records the rigorous evaluation per setting with A-EIG invoked
nowhere. A declaration with no enclosure falls back to the floating-point
weight with the reason ``port_grams_not_enclosed``.
"""

from __future__ import annotations

import importlib
from dataclasses import replace
from fractions import Fraction
from typing import Any

import pytest

from certiqs_key.receiver import construct as construct_module
from certiqs_key.receiver.construct import construct_receiver
from certiqs_key.receiver.rigorous import PORT_GRAMS_NOT_ENCLOSED

pytestmark = pytest.mark.contract

PORTS = ("H", "V", "D", "A")


def _requests(instance: str, device: dict[str, Any]) -> list[Any]:
    surface = importlib.import_module(f"instances.{instance}.surface")
    base = surface.default_config()
    return list(surface.receiver_requests(base.with_(device={**base.device, **device})))


def _settings(request: Any) -> list[Any]:
    emission = construct_receiver(request)
    assert emission.artifact is not None, emission.refusal
    return list(emission.artifact.bound_quantifier_domain.per_setting)


def test_the_ideal_receiver_reaches_its_exact_window_without_eps_eig() -> None:
    record = _settings(_requests("bbm92", {})[0])[0]
    assert record.evaluation == "rigorous" and record.fallback_reason is None
    assert record.assumption_eig_invoked is False
    exact = Fraction(1, 2)
    assert Fraction(record.weight) <= exact
    assert exact - Fraction(record.weight) < Fraction(1, 10**14)
    assert record.floating_point_weight is not None
    assert record.floating_point_weight < 0.4991  # 1/2 - eps_eig, under A-EIG
    window = record.enclosed["window_bounds"]
    assert [entry["photons"] for entry in window] == [2]
    assert Fraction(window[0]["bound"]) <= exact
    assert exact - Fraction(window[0]["bound"]) < Fraction(1, 10**14)


def test_the_noisy_receiver_reaches_its_analytic_remainder() -> None:
    noisy = {
        "efficiency": dict.fromkeys(PORTS, Fraction(9, 10)),
        "dark_count": dict.fromkeys(PORTS, Fraction(1, 10**6)),
    }
    # Declared at the factored loss one: the analytic remainder 27/80 is the
    # device's at efficiency 9/10 (the normalized station's, efficiency one,
    # is the ideal receiver's window, the test above).
    request = replace(
        _requests("optical_bb84", noisy)[0], efficiency_normalization=Fraction(1)
    )
    record = _settings(request)[0]
    exact = Fraction(27, 80)
    assert record.evaluation == "rigorous"
    assert Fraction(record.weight) <= exact
    assert exact - Fraction(record.weight) < Fraction(1, 10**14)
    assert Fraction(record.enclosed["enclosed_weight"]) <= exact
    # The floating-point weight differs by rounding only where the window
    # does not bind: the rigorous one is within it.
    assert record.weight >= record.floating_point_weight - 1e-15


def test_the_artifact_label_and_the_ledger_follow_the_settings() -> None:
    emission = construct_receiver(_requests("bbm92", {})[0])
    artifact = emission.artifact
    assert artifact is not None
    assert artifact.bound_evaluation == "rigorous"
    eig = next(
        row
        for row in artifact.assumption_ledger
        if dict(row.constrains).get("invoked_at") is not None
    )
    assert dict(eig.constrains)["invoked_at"] == []
    slot = artifact.high_photon_bounds.entries[0]
    assert slot.weight == min(weight for _, weight in slot.per_setting)


def test_without_an_enclosure_the_floating_point_weight_stays(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _requests("bbm92", {})[0]
    monkeypatch.setattr(
        construct_module,
        "rigorous_weights",
        lambda validated: {
            setting.label: PORT_GRAMS_NOT_ENCLOSED
            for setting in validated.request.probe_declaration.settings
        },
    )
    emission = construct_receiver(request)
    artifact = emission.artifact
    assert artifact is not None and artifact.bound_evaluation == "floating_point"
    record = artifact.bound_quantifier_domain.per_setting[0]
    assert record.evaluation == "floating_point"
    assert record.fallback_reason == PORT_GRAMS_NOT_ENCLOSED
    assert record.assumption_eig_invoked is True
    assert record.weight < 0.4991
