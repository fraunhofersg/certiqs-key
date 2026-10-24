"""Item (vii) of the certified evaluation as the run tier decides it.

``frank-wolfe/req:certified-evaluation`` (vii): a run is not reported at the
certified tier where (a) A-EIG is invoked (``receiver/req:eig-ledger-row``) or
(b) a floating-point receiver weight enters a routed weight
(``receiver/req:evaluation-label``). The run tier decides both in
``runs/pipeline.py`` :func:`~certiqs_key.runs.pipeline.certification_withheld`.

These tests call ``certification_withheld`` directly, so deleting either
reason fails the suite (a test that handed the string ``withheld`` to
``evaluate`` would not notice). The solver's half of (vii), the tier and the length on a
withheld evaluation, is ``tests/integration/test_key_rate_pipeline.py::
test_a_withheld_certification_keeps_the_first_order_number``.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import pytest

from certiqs_key.receiver import construct as construct_module
from certiqs_key.receiver.construct import construct_receiver
from certiqs_key.receiver.rigorous import PORT_GRAMS_NOT_ENCLOSED
from certiqs_key.runs.pipeline import certification_withheld

pytestmark = pytest.mark.contract


def _request() -> Any:
    surface = importlib.import_module("instances.bbm92.surface")
    return next(iter(surface.receiver_requests(surface.default_config())))


def test_a_floating_point_receiver_withholds_the_tier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rigorous = construct_receiver(_request()).artifact
    assert rigorous is not None and rigorous.bound_evaluation == "rigorous"
    monkeypatch.setattr(
        construct_module,
        "rigorous_weights",
        lambda validated: {
            setting.label: PORT_GRAMS_NOT_ENCLOSED
            for setting in validated.request.probe_declaration.settings
        },
    )
    floating = construct_receiver(_request()).artifact
    assert floating is not None and floating.bound_evaluation == "floating_point"

    def prepared(*receivers: Any, single: Any = None) -> Any:
        return SimpleNamespace(
            device_artifacts=tuple(SimpleNamespace(receiver=r) for r in receivers),
            receiver_artifact=single,
        )

    both = ("numerical_trust_premise", "receiver_weight_floating_point")
    assert certification_withheld(prepared(single=rigorous)) == ()
    assert certification_withheld(prepared(rigorous, rigorous)) == ()
    # bbm92's station declares an exact window: A-EIG is invoked at it (a),
    # and its slot carries the floating-point weight (b).
    assert certification_withheld(prepared(single=floating)) == both
    assert certification_withheld(prepared(rigorous, floating)) == both
