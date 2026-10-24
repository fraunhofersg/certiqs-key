"""The efficiency normalization: the factor, its refusals, its records, its guards.

``receiver/detector-imperfections/req:efficiency-normalization`` (the factor
and its domain), ``req:normalization-record`` (the record),
``req:loss-before-evaluation`` (the run tier's refusal of a provider that does
not declare the loss applied), ``reductions/wpfss/req:normalized-branch-refusal``
(a normalized receiver read as a branch) and the report's line for a
normalized station. The numbers themselves are in
``tests/golden/test_efficiency_normalization_against_registry.py``.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest
from instances.common.optics import ReceiverParameters, receiver_request
from probe_presence import requires_probe

from certiqs_key.receiver import (
    EfficiencyNormalization,
    NormalizationReason,
    NormalizedPort,
    ReceiverRequest,
    RefusalReason,
    construct_receiver,
    factored_loss,
    normalize_efficiencies,
)
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.runs.errors import RunRefusalReason
from certiqs_key.runs.pipeline import (
    LossAppliedProvider,
    LossAppliedRawProvider,
    factored_loss_applied,
    raw_factored_loss_applied,
)
from certiqs_key.runs.report.setup import _normalization_note

F = Fraction
PORTS = ("H", "V", "D", "A")


def _request(
    efficiencies: tuple[Fraction, ...],
    normalization: Fraction | float | None = None,
    *,
    led: bool = False,
) -> ReceiverRequest:
    parameters = ReceiverParameters(efficiency=efficiencies, photon_cutoff=1)
    probe = None
    if led:
        from instances.common.led import LedProbe

        probe = LedProbe(window=3)
    request = receiver_request(parameters, probe)
    return replace(request, efficiency_normalization=normalization)


@pytest.mark.contract
def test_the_default_factor_stops_short_of_the_largest_efficiency() -> None:
    """req:efficiency-normalization: t = eta_max / (99/100), every port at eta_k / t.

    By hand: ``eta_max = 3/5``, so ``t = (3/5)(100/99) = 300/495 = 20/33``, and
    ``eta_k / t = eta_k * 33/20``: ``3/5 -> 99/100``, ``1/2 -> 33/40``,
    ``3/10 -> 99/200``, ``0 -> 0``.
    """
    efficiencies = (F(3, 5), F(1, 2), F(3, 10), F(0))
    artifact = construct_receiver(_request(efficiencies)).artifact
    assert artifact is not None
    normalization = artifact.efficiency_record.normalization
    assert normalization.factored_loss == F(20, 33)
    assert normalization.applied and normalization.reason is None
    assert not normalization.factor_declared
    assert [(p.label, p.declared, p.compiled) for p in normalization.ports] == [
        ("H", F(3, 5), F(99, 100)),
        ("V", F(1, 2), F(33, 40)),
        ("D", F(3, 10), F(99, 200)),
        ("A", F(0), F(0)),
    ]
    # req:efficiency-record: the rows keep the DECLARED efficiencies.
    detector = {
        row.element.rsplit("eta_", 1)[1]: row.value
        for row in artifact.efficiency_record.rows
        if row.element.startswith("L1 detector layer")
    }
    assert detector == {"H": 0.6, "V": 0.5, "D": 0.3, "A": 0.0}
    assert factored_loss(_request(efficiencies)) == F(20, 33)


@pytest.mark.contract
@pytest.mark.parametrize(
    ("largest", "factor"),
    [
        # Below 99/100: t = eta_max * 100/99, formed exactly, by hand.
        (F(1, 5), F(20, 99)),  # (1/5)(100/99)
        (F(4, 5), F(80, 99)),  # (4/5)(100/99)
        (F(989, 1000), F(989, 990)),  # (989/1000)(100/99) = 989/990 < 1
        (0.5, F(50, 99)),  # a binary64 declaration read as the rational 1/2
        # From 99/100 on: t = 1.
        (F(99, 100), F(1)),
        (F(199, 200), F(1)),
        (F(1), F(1)),
    ],
)
def test_the_default_factor_at_and_around_the_margin(
    largest: Fraction | float, factor: Fraction
) -> None:
    """req:efficiency-normalization: the default on each side of 99/100.

    Below ``99/100`` the default is ``eta_max / (99/100)`` and the largest
    port is compiled at ``99/100`` exactly, recorded as applied with no
    reason; from ``99/100`` on it is ``1``, recorded as NOT applied with the
    reason ``factor_one`` (req:normalization-record: applied exactly where
    ``t < 1``), every port compiled as declared.
    """
    efficiencies = (largest, F(1, 10), F(0), F(1, 10))
    normalization = normalize_efficiencies(
        list(zip(PORTS, efficiencies, strict=True)),
        declared_factor=None,
        source_modes_declared=False,
    )
    assert not isinstance(normalization, str)
    assert normalization.factored_loss == factor
    assert not normalization.factor_declared
    compiled = normalization.ports[0].compiled
    if factor < 1:
        assert normalization.applied and normalization.reason is None
        assert compiled == F(99, 100)
        assert normalization.below_one
        assert normalization.measurement_statement is not None
    else:
        assert not normalization.applied
        assert normalization.reason is NormalizationReason.FACTOR_ONE
        assert all(p.compiled == p.declared for p in normalization.ports)
        assert not normalization.below_one
        assert normalization.measurement_statement is None


@pytest.mark.contract
def test_a_binary64_largest_efficiency_just_below_the_margin_is_normalized() -> None:
    """req:efficiency-normalization: eta_max is the rational the binary64 denotes.

    By hand: the binary64 nearest 0.99 is ``4458563631096791 / 2^52 =
    0.98999999999999999111821580299874767661094665527343750``, below
    ``99/100``, so the default is ``eta_max / (99/100) = (4458563631096791 /
    2^52)(100/99) = 445856363109679100 / (99 * 2^52) < 1``, not one, and the
    port is compiled at ``99/100`` exactly.
    """
    eta = 0.99
    assert F(eta) == F(4458563631096791, 2**52) < F(99, 100)
    normalization = normalize_efficiencies(
        list(zip(PORTS, (eta, F(1, 10), F(0), F(1, 10)), strict=True)),
        declared_factor=None,
        source_modes_declared=False,
    )
    assert not isinstance(normalization, str)
    assert normalization.applied and normalization.below_one
    assert F(eta) < normalization.factored_loss < 1
    assert normalization.factored_loss == F(445856363109679100, 99 * 2**52)
    assert normalization.ports[0].compiled == F(99, 100)


@pytest.mark.contract
def test_the_full_normalization_stays_declarable() -> None:
    """req:efficiency-normalization: a declared t = eta_max is in [eta_max, 1]."""
    efficiencies = (F(3, 5), F(1, 2), F(3, 10), F(0))
    normalization = normalize_efficiencies(
        list(zip(PORTS, efficiencies, strict=True)),
        declared_factor=F(3, 5),
        source_modes_declared=False,
    )
    assert not isinstance(normalization, str)
    assert normalization.factored_loss == F(3, 5)
    assert normalization.factor_declared
    assert [p.compiled for p in normalization.ports] == [
        F(1),
        F(5, 6),
        F(1, 2),
        F(0),
    ]


@pytest.mark.contract
def test_a_declared_factor_between_the_largest_efficiency_and_one_is_used() -> None:
    """req:efficiency-normalization: a declared t in [eta_max, 1] replaces eta_max."""
    artifact = construct_receiver(_request((F(1, 2),) * 4, F(4, 5))).artifact
    assert artifact is not None
    normalization = artifact.efficiency_record.normalization
    assert normalization.factored_loss == F(4, 5)
    assert normalization.factor_declared
    assert {p.compiled for p in normalization.ports} == {F(5, 8)}
    payload = normalization.as_payload()
    assert payload["factored_loss"] == "4/5"
    assert payload["ports"][0] == {
        "port": "H",
        "declared_efficiency": "1/2",
        "compiled_efficiency": "5/8",
    }
    assert "normalized station" in str(payload["measurement"])


@pytest.mark.contract
@pytest.mark.parametrize(
    ("efficiencies", "declared", "led", "reason"),
    [
        ((F(1, 2),) * 4, F(1), False, NormalizationReason.FACTOR_ONE),
        (
            (F(99, 100), F(1, 2), F(0), F(1, 2)),
            None,
            False,
            NormalizationReason.FACTOR_ONE,
        ),
        ((F(1),) * 4, None, False, NormalizationReason.FACTOR_ONE),
        ((F(1, 2),) * 4, None, True, NormalizationReason.SOURCE_MODES_DECLARED),
        ((F(1, 2),) * 4, F(1), True, NormalizationReason.SOURCE_MODES_DECLARED),
        ((F(1),) * 4, None, True, NormalizationReason.SOURCE_MODES_DECLARED),
        ((F(0),) * 4, None, False, NormalizationReason.ALL_EFFICIENCIES_ZERO),
        ((F(0),) * 4, F(1), False, NormalizationReason.ALL_EFFICIENCIES_ZERO),
        ((F(0),) * 4, None, True, NormalizationReason.SOURCE_MODES_DECLARED),
    ],
)
def test_a_request_compiled_at_one_says_why(
    efficiencies: tuple[Fraction, ...],
    declared: Fraction | None,
    led: bool,
    reason: NormalizationReason,
) -> None:
    """req:normalization-record: where not applied, the first reason that holds.

    The order is the claim's: source modes declared, then every efficiency
    zero, then the factor one, declared or by default. So a probe with a
    factor of one, or with every efficiency zero, names the source modes; a
    declared one with every efficiency zero names the zeros.
    """
    normalization = normalize_efficiencies(
        [(label, value) for label, value in zip(PORTS, efficiencies, strict=True)],
        declared_factor=declared,
        source_modes_declared=led,
    )
    assert not isinstance(normalization, str)
    assert not normalization.applied
    assert normalization.reason is reason
    assert normalization.factored_loss == 1
    assert normalization.measurement_statement is None
    assert all(p.compiled == p.declared for p in normalization.ports)


@pytest.mark.contract
@pytest.mark.parametrize(
    ("efficiencies", "declared", "led"),
    [
        ((F(1, 2),) * 4, F(11, 10), False),  # t > 1
        ((F(1, 2),) * 4, F(2, 5), False),  # t < eta_max
        ((F(1, 2),) * 4, F(0), False),  # t = 0
        ((F(1, 2),) * 4, float("nan"), False),  # not a number
        pytest.param(  # t < 1 with a probe
            (F(1, 2),) * 4, F(3, 4), True, marks=requires_probe
        ),
        ((F(0),) * 4, F(1, 2), False),  # t < 1 with every efficiency zero
    ],
)
def test_a_factor_outside_its_domain_is_refused(
    efficiencies: tuple[Fraction, ...], declared: Fraction | float, led: bool
) -> None:
    """req:efficiency-normalization: refused, efficiency_normalization_out_of_range."""
    emission = construct_receiver(_request(efficiencies, declared, led=led))
    assert emission.artifact is None
    assert emission.refusal is not None
    expected = RefusalReason.EFFICIENCY_NORMALIZATION_OUT_OF_RANGE
    assert emission.refusal.reason is expected
    with pytest.raises(HypothesisError):
        factored_loss(_request(efficiencies, declared, led=led))


@pytest.mark.contract
def test_the_range_is_decided_on_the_exact_values_declared() -> None:
    """req:efficiency-normalization: a declared t outside [eta_max, 1] is refused.

    Both sides are the exact rationals declared (foundations/def:binary64):
    the binary64 efficiency 0.8 is 3602879701896397/4503599627370496, which
    exceeds 4/5 by 1/22517998136852480, so a declared t = 4/5 lies below
    eta_max and is refused -- accepting it would compile the port at
    eta/t = 1 + 1/18014398509481984 > 1. The same t beside an exact 4/5, or
    the same binary64 0.8 as t, is in range, and that port compiles at one.
    """
    binary = 0.8
    assert F(binary) == F(3602879701896397, 2**52)
    assert F(binary) - F(4, 5) == F(1, 22517998136852480)
    refused = normalize_efficiencies(
        [("H", binary), ("V", F(1, 2))],
        declared_factor=F(4, 5),
        source_modes_declared=False,
    )
    assert isinstance(refused, str)
    assert "lies outside [eta_max, 1]" in refused
    assert "the binary64 value 0.8 declared" in refused
    exact = normalize_efficiencies(
        [("H", F(4, 5)), ("V", F(1, 2))],
        declared_factor=F(4, 5),
        source_modes_declared=False,
    )
    assert isinstance(exact, EfficiencyNormalization)
    assert exact.factored_loss == F(4, 5)
    assert exact.ports[0].compiled == 1
    same = normalize_efficiencies(
        [("H", binary), ("V", F(1, 2))],
        declared_factor=binary,
        source_modes_declared=False,
    )
    assert isinstance(same, EfficiencyNormalization)
    assert same.factored_loss == F(binary)
    assert same.ports[0].compiled == 1
    assert same.ports[1].compiled == F(1, 2) / F(binary)
    # An exact efficiency gives no binary64 hint.
    plain = normalize_efficiencies(
        [("H", F(4, 5))], declared_factor=F(3, 5), source_modes_declared=False
    )
    assert isinstance(plain, str) and "binary64" not in plain


@pytest.mark.contract
def test_at_one_the_receiver_compiles_what_it_compiled_before() -> None:
    """At t = 1 the validated request IS the declared one, so nothing moves.

    A declared ``t = 1`` and the default at unit efficiency both compile the
    declaration itself: the emitted payloads agree, the efficiency record's
    normalization aside, bit for bit.
    """
    ones = construct_receiver(_request((F(1),) * 4)).artifact
    declared = construct_receiver(_request((F(1),) * 4, F(1))).artifact
    assert ones is not None and declared is not None
    left, right = ones.as_payload(), declared.as_payload()
    left_record = left.pop("efficiency_record")
    right_record = right.pop("efficiency_record")
    assert left == right
    assert left_record["rows"] == right_record["rows"]  # type: ignore[index]


@pytest.mark.contract
@pytest.mark.parametrize("eta", [F(99, 100), F(199, 200), F(1)])
def test_a_default_of_one_compiles_the_declared_receiver(eta: Fraction) -> None:
    """req:normalization-record: a factor of one reads the same, default or declared.

    End to end, with mismatched ports and dark counts at N = 2: from
    ``eta_max = 99/100`` on the default is ``t = 1``
    (req:efficiency-normalization), and the artefact equals the one declared
    at ``t = 1``. Both normalization records say not applied, reason
    ``factor_one``, and differ only in ``factor_declared``, which says who
    chose the one (the regression test of the finding
    receiver/normalization-record-default-one: a default one read applied, a
    declared one not applied).
    """

    def request(normalization: Fraction | None) -> ReceiverRequest:
        parameters = ReceiverParameters(
            efficiency=(eta, F(1, 2), eta, F(1, 2)),
            dark_count=(F(1, 10**4),) * 4,
            photon_cutoff=2,
        )
        return replace(
            receiver_request(parameters), efficiency_normalization=normalization
        )

    default = construct_receiver(request(None)).artifact
    declared = construct_receiver(request(F(1))).artifact
    assert default is not None and declared is not None
    record = default.efficiency_record.normalization
    off = declared.efficiency_record.normalization
    for normalization in (record, off):
        assert normalization.factored_loss == 1
        assert not normalization.applied
        assert normalization.reason is NormalizationReason.FACTOR_ONE
        assert normalization.measurement_statement is None
        assert [p.compiled for p in normalization.ports] == [
            p.declared for p in normalization.ports
        ]
    assert not record.factor_declared and off.factor_declared
    default_payload = record.as_payload()
    declared_payload = off.as_payload()
    assert default_payload.pop("factor_declared") is False
    assert declared_payload.pop("factor_declared") is True
    assert default_payload == declared_payload
    left, right = default.as_payload(), declared.as_payload()
    left_record = left.pop("efficiency_record")
    right_record = right.pop("efficiency_record")
    assert left == right
    assert left_record["rows"] == right_record["rows"]  # type: ignore[index]


@pytest.mark.contract
@pytest.mark.parametrize(
    ("factor", "applied", "reason"),
    [
        (F(1), True, None),  # applied at t = 1
        (F(1, 2), False, NormalizationReason.FACTOR_ONE),  # not applied at t < 1
        (F(1, 2), True, NormalizationReason.FACTOR_ONE),  # a reason where applied
        (F(1), False, None),  # no reason where not applied
    ],
)
def test_a_record_that_contradicts_the_requirement_is_refused(
    factor: Fraction, applied: bool, reason: NormalizationReason | None
) -> None:
    """req:normalization-record: applied exactly where t < 1, a reason where not.

    The record checks itself on construction, so no code path can emit a
    station at ``t = 1`` that says applied, or one at ``t < 1`` that says not.
    """
    port = NormalizedPort("H", F(1, 2), F(1, 2) / factor)
    with pytest.raises(HypothesisError):
        EfficiencyNormalization(
            factored_loss=factor,
            applied=applied,
            reason=reason,
            factor_declared=False,
            ports=(port,),
        )
    for t, ok_applied, ok_reason in (
        (F(1), False, NormalizationReason.FACTOR_ONE),
        (F(1, 2), True, None),
    ):
        EfficiencyNormalization(
            factored_loss=t,
            applied=ok_applied,
            reason=ok_reason,
            factor_declared=False,
            ports=(NormalizedPort("H", F(1, 2), F(1, 2) / t),),
        )


@pytest.mark.contract
@pytest.mark.parametrize(
    ("eta", "reason"),
    [
        (F(1, 2), NormalizationReason.ALL_EFFICIENCIES_ZERO),
        (F(0), NormalizationReason.FACTOR_ONE),
    ],
)
def test_a_reason_the_ports_contradict_is_refused(
    eta: Fraction, reason: NormalizationReason
) -> None:
    """req:normalization-record: the reason order, where the record shows it.

    ``all_efficiencies_zero`` with a declared efficiency above zero, and
    ``factor_one`` where every declared efficiency is zero (whose first
    reason is ``all_efficiencies_zero``), are refused on construction.
    """
    with pytest.raises(HypothesisError):
        EfficiencyNormalization(
            factored_loss=F(1),
            applied=False,
            reason=reason,
            factor_declared=False,
            ports=(NormalizedPort("H", eta, eta),),
        )


@pytest.mark.contract
@pytest.mark.parametrize(
    ("field", "value"),
    [
        # Binary64 rounds each of these into [0, 1]: 1 + 10^-20 to 1.0 and
        # -10^-400 to -0.0, so only an exact comparison sees them outside.
        ("efficiency", F(1) + F(1, 10**20)),
        ("efficiency", F(-1, 10**400)),
        ("dark_count_probability", F(1) + F(1, 10**20)),
        ("efficiency", float("nan")),
        ("efficiency", float("inf")),
    ],
    ids=[
        "eta-hair-above-one",
        "eta-hair-below-zero",
        "p_dc-hair-above-one",
        "nan",
        "inf",
    ],
)
def test_a_detector_layer_value_outside_the_unit_interval_is_refused_not_raised(
    field: str, value: Fraction | float
) -> None:
    """The detector layer's eta_k and p_dc|k lie in [0, 1], decided exactly.

    ``interface.yaml`` ``inputs.detector_layer``. The range is decided on the
    declared rational, not on its binary64
    rounding, so a value a hair outside [0, 1] is refused
    ``port_map_malformed`` before the default factor is formed; a non-finite
    one is refused first.
    """
    request = receiver_request(
        ReceiverParameters(efficiency=(F(1),) * 4, photon_cutoff=1)
    )
    request = replace(
        request,
        detector_layer=tuple(
            replace(port, **{field: value}) for port in request.detector_layer
        ),
    )
    emission = construct_receiver(request)
    assert emission.artifact is None
    assert emission.refusal is not None
    assert emission.refusal.reason is RefusalReason.PORT_MAP_MALFORMED


def test_wrapping_a_provider_declares_the_loss_applied_once() -> None:
    """req:loss-before-evaluation: the run tier's marker, idempotent."""

    def provider(declaration: object) -> dict[str, Fraction]:
        return {}

    wrapped = factored_loss_applied(provider)  # type: ignore[arg-type]
    assert isinstance(wrapped, LossAppliedProvider)
    assert factored_loss_applied(wrapped) is wrapped
    assert wrapped(object()) == {}  # type: ignore[arg-type]
    raw = raw_factored_loss_applied(provider)  # type: ignore[arg-type]
    assert isinstance(raw, LossAppliedRawProvider)
    assert raw_factored_loss_applied(raw) is raw
    assert raw(object()) == {}  # type: ignore[arg-type]


@pytest.mark.contract
def test_an_undeclared_provider_is_refused_where_a_station_is_normalized(
    tmp_path: object,
) -> None:
    """req:loss-before-evaluation: refused before the provider runs."""
    from pathlib import Path

    from instances.bbm92 import surface

    from certiqs_key.runs.pipeline import SliceRefusal

    base = surface.default_config()
    config = base.with_(
        device={**base.device, "bob_efficiency": dict.fromkeys(PORTS, F(1, 2))}
    )
    called: list[object] = []

    def provider(declaration: object) -> dict[str, Fraction]:
        called.append(declaration)
        return {}

    runner = surface.runner(
        None,  # type: ignore[arg-type]
        Path(str(tmp_path)),
        created_by="t",
        honest_provider=provider,
        honest_model_note={"model": "test", "overridden": True},
    )
    outcome = runner(config, 0)
    assert isinstance(outcome, SliceRefusal)
    assert outcome.reason == RunRefusalReason.FACTORED_LOSS_NOT_APPLIED
    assert str(outcome.stage) == "honest_model"
    assert "bob_station: t = 50/99" in outcome.detail  # (1/2)(100/99)
    assert not called


def test_the_report_names_the_factor_and_the_efficiencies() -> None:
    """The report's line for a normalized station, and none at the default of one.

    By hand: at ``eta = 3/5`` the default is ``t = 20/33`` and every port is
    compiled at ``99/100``.
    """
    artifact = construct_receiver(_request((F(3, 5),) * 4)).artifact
    assert artifact is not None
    note = _normalization_note(artifact.efficiency_record.normalization.as_payload())
    assert note is not None
    assert "factor 20/33" in note
    assert "H 3/5 -> 99/100" in note
    ones = construct_receiver(_request((F(1),) * 4)).artifact
    assert ones is not None
    default = ones.efficiency_record.normalization.as_payload()
    assert _normalization_note(default) is None
    off = construct_receiver(_request((F(3, 5),) * 4, F(1))).artifact
    assert off is not None
    assert "off (factor 1 declared)" in str(
        _normalization_note(off.efficiency_record.normalization.as_payload())
    )
    # A default one below unit efficiency (eta_max = 99/100) is not declared,
    # so it prints nothing either.
    near = construct_receiver(_request((F(99, 100),) * 4)).artifact
    assert near is not None
    near_payload = near.efficiency_record.normalization.as_payload()
    assert near_payload["reason"] == "factor_one"
    assert _normalization_note(near_payload) is None


def test_the_report_reads_a_0_39_0_normalization() -> None:
    """A normalization of record schema 0.39.0 renders as it did.

    0.39.0 recorded a declared one as ``declared_one`` (not applied) and a
    default one as applied at ``t = 1`` with no reason; the report still reads
    those records (``SUPPORTED_RECORD_SCHEMA_VERSIONS``), the first as the
    off line and the second as nothing.
    """
    ports = [
        {"port": label, "declared_efficiency": "3/5", "compiled_efficiency": "3/5"}
        for label in PORTS
    ]
    declared_one = {
        "factored_loss": "1",
        "factor_declared": True,
        "applied": False,
        "reason": "declared_one",
        "ports": ports,
        "measurement": None,
    }
    assert _normalization_note(declared_one) == (
        "Efficiency normalization: off (factor 1 declared); the detectors are "
        "analysed at their declared efficiencies."
    )
    default_one = {
        **declared_one,
        "factor_declared": False,
        "applied": True,
        "reason": None,
        "ports": [{**port, "declared_efficiency": "99/100"} for port in ports],
    }
    assert _normalization_note(default_one) is None


@pytest.mark.contract
@pytest.mark.parametrize(
    ("instance", "device"),
    [
        ("optical_bb84", {"efficiency_normalization": F(1, 2)}),
        ("decoy_bb84", {"efficiency_normalization": F(1, 2)}),
        ("bbm92", {"bob_efficiency_normalization": F(1, 2)}),
        ("bbm92", {"source_model": "spdc", "bob_efficiency_normalization": F(1, 2)}),
    ],
)
def test_an_out_of_range_factor_is_the_receivers_refusal_whatever_the_model(
    instance: str, device: dict[str, object]
) -> None:
    """req:efficiency-normalization: refused with its reason, never raised.

    At efficiency one a declared ``t = 1/2`` lies below ``eta_max``. Every
    honest model reads its stations' ``t`` only when the run calls it, after
    the receiver has decided the factor, so the refusal is the receiver's on
    every instance and model.
    """
    import importlib

    from certiqs_key.runs.pipeline import SliceRefusal

    surface = importlib.import_module(f"instances.{instance}.surface")
    base = surface.default_config()
    outcome = surface.preparation(base.with_(device={**base.device, **device}))
    assert isinstance(outcome, SliceRefusal)
    assert str(outcome.stage) == "receiver_construction"
    assert outcome.reason == "efficiency_normalization_out_of_range"


# ===========================================================================
#  The raw law is an evaluation too (req:loss-before-evaluation)
# ===========================================================================


def _bbm92_at(bob_efficiency: Fraction) -> object:
    from instances.bbm92 import surface

    base = surface.default_config()
    return base.with_(
        device={**base.device, "bob_efficiency": dict.fromkeys(PORTS, bob_efficiency)}
    )


@pytest.mark.contract
def test_an_undeclared_raw_provider_is_refused_where_a_station_is_normalized() -> None:
    """req:loss-before-evaluation: the raw X x V law is refused before it runs.

    The raw provider feeds lambda_EC and the record's raw table, so ``prepare``
    refuses an unmarked one at ``honest_model`` wherever a station's ``t`` is
    below one, and calls neither it nor anything after it. The library's own
    raw provider is marked and passes; at ``t = 1`` an unmarked one passes.
    """
    from tests.support.lowered_templates import lowered

    from certiqs_key.runs.pipeline import Preparation, SliceRefusal, prepare

    called: list[object] = []

    def raw(declaration: object) -> dict[tuple[str, str], Fraction]:
        called.append(declaration)
        return {}

    configured, lowering = lowered("bbm92", _bbm92_at(F(1, 2)))  # type: ignore[arg-type]
    assert isinstance(lowering.raw, LossAppliedRawProvider)
    outcome = prepare(
        configured,
        **lowering.route(),
        raw_joint_provider=raw,  # type: ignore[arg-type]
        channel_interface_provider=lowering.channel_interface,
    )
    assert isinstance(outcome, SliceRefusal)
    assert outcome.reason == RunRefusalReason.FACTORED_LOSS_NOT_APPLIED
    assert str(outcome.stage) == "honest_model"
    assert "bob_station: t = 50/99" in outcome.detail  # (1/2)(100/99)
    assert "raw joint provider" in outcome.detail
    assert not called

    configured, lowering = lowered("bbm92", _bbm92_at(F(1, 2)))  # type: ignore[arg-type]
    marked = prepare(
        configured,
        **lowering.route(),
        raw_joint_provider=lowering.raw,
        channel_interface_provider=lowering.channel_interface,
    )
    assert isinstance(marked, Preparation), marked
    assert marked.raw_joint_distribution

    configured, lowering = lowered("bbm92", _bbm92_at(F(1)))  # type: ignore[arg-type]
    plain = prepare(
        configured,
        **lowering.route(),
        raw_joint_provider=raw,  # type: ignore[arg-type]
        channel_interface_provider=lowering.channel_interface,
    )
    assert isinstance(plain, Preparation), plain
    assert called


@pytest.mark.contract
@pytest.mark.parametrize(
    ("instance", "device"),
    [
        ("optical_bb84", {"efficiency": dict.fromkeys(PORTS, F(1, 2))}),
        ("decoy_bb84", {"efficiency": dict.fromkeys(PORTS, F(1, 2))}),
        ("bbm92", {"bob_efficiency": dict.fromkeys(PORTS, F(1, 2))}),
        (
            "bbm92",
            {"source_model": "spdc", "bob_efficiency": dict.fromkeys(PORTS, F(1, 2))},
        ),
    ],
)
def test_every_library_model_declares_both_of_its_laws(
    instance: str, device: dict[str, object]
) -> None:
    """req:loss-before-evaluation: the honest and raw providers both carry the mark.

    Each shipped optical instance, its stations at a factored loss below one,
    lowers to providers that survive the lowering's guard marked, so its
    preparation runs to its raw law rather than refusing.
    """
    import importlib

    from tests.support.lowered_templates import lowered

    from certiqs_key.runs.pipeline import Preparation

    surface = importlib.import_module(f"instances.{instance}.surface")
    base = surface.default_config()
    config = base.with_(device={**base.device, **device})
    _, lowering = lowered(instance, config)
    assert isinstance(lowering.honest, LossAppliedProvider)
    assert isinstance(lowering.raw, LossAppliedRawProvider)
    assert isinstance(surface.preparation(config), Preparation)


# ===========================================================================
#  A model told a subset of the stations (req:loss-before-evaluation)
# ===========================================================================


def _station(
    station_id: str,
    efficiencies: tuple[Fraction, ...] | None,
    normalization: Fraction | None = None,
) -> object:
    from instances.common.honest import StationFacts

    if efficiencies is None:
        return StationFacts(
            id=station_id, party="B", kind="declared_povm", dimension=2
        )
    return StationFacts(
        id=station_id,
        party="B",
        kind="optical",
        request=_request(efficiencies, normalization),
    )


@pytest.mark.contract
def test_a_subset_covers_the_run_only_where_every_other_station_is_at_one() -> None:
    """The lowering keeps a subset model's mark only where the rest are at t = 1."""
    from instances.declared.lowering.honest import _covers_every_normalized_station

    told = _station("a", (F(3, 5),) * 4)
    normalized = _station("b", (F(1, 2),) * 4)
    declared_one = _station("b", (F(1, 2),) * 4, F(1))
    at_one = _station("b", (F(1),) * 4)
    refused = _station("b", (F(1, 2),) * 4, F(2, 5))
    povm = _station("b", None)
    for other, covered in (
        (normalized, False),
        (declared_one, True),
        (at_one, True),
        (refused, False),
        (povm, True),
    ):
        stations = (told, other)
        assert _covers_every_normalized_station(stations, (told,)) is covered  # type: ignore[arg-type]
        assert _covers_every_normalized_station(stations, stations) is True  # type: ignore[arg-type]


class _OneStation:
    """A single-station library model that applies the loss of its own station."""

    name = "one_station_for_the_test"
    parameters: tuple[str, ...] = ()

    def note(self, bound: object, context: object) -> dict[str, object]:
        return {"model": self.name}

    def preconditions(self, context: object) -> None:
        assert len(context.stations) == 1  # type: ignore[attr-defined]

    def providers(self, bound: object, context: object) -> tuple[object, object]:
        from instances.common.honest.tables import aggregate

        def raw(declaration: object) -> dict[tuple[str, str], Fraction]:
            return {}

        return (
            factored_loss_applied(aggregate(raw)),  # type: ignore[arg-type]
            raw_factored_loss_applied(raw),  # type: ignore[arg-type]
        )


@pytest.mark.contract
@pytest.mark.parametrize(("bob", "marked"), [(F(1, 2), False), (F(1), True)])
def test_a_model_told_one_station_is_marked_only_where_the_other_is_at_one(
    monkeypatch: pytest.MonkeyPatch, bob: Fraction, marked: bool
) -> None:
    """req:loss-before-evaluation: an unseen station's loss is never declared applied.

    A document names a one-station model for Alice's station of bbm92's two.
    Where Bob's receiver is compiled at ``t < 1`` the model has not applied
    his loss, so the lowering does not keep its mark and the run refuses
    ``factored_loss_not_applied``; where Bob is at ``t = 1`` the mark stands.
    """
    from instances.common import honest as library
    from tests.support.declared_optical_documents import custom_from

    from certiqs_key.runs.pipeline import Preparation, SliceRefusal, prepare

    monkeypatch.setitem(library.MODELS, _OneStation.name, _OneStation())  # type: ignore[arg-type]

    def edit(tree: dict[str, object]) -> None:
        tree["honest"] = {
            "library": _OneStation.name,
            "station": "alice_station",
            "bind": {},
        }

    surface = custom_from("bbm92", edit, "one_station_honest")
    base = surface.default_config()
    config = base.with_(
        device={
            **base.device,
            "alice_efficiency": dict.fromkeys(PORTS, F(3, 5)),
            "bob_efficiency": dict.fromkeys(PORTS, bob),
        }
    )
    configured, lowering = surface._read(config)
    assert isinstance(lowering.honest, LossAppliedProvider) is marked
    assert isinstance(lowering.raw, LossAppliedRawProvider) is marked
    outcome = prepare(
        configured,
        **lowering.route(),
        raw_joint_provider=lowering.raw,
        channel_interface_provider=lowering.channel_interface,
    )
    if marked:
        assert isinstance(outcome, Preparation), outcome
    else:
        assert isinstance(outcome, SliceRefusal)
        assert outcome.reason == RunRefusalReason.FACTORED_LOSS_NOT_APPLIED
        assert "bob_station: t = 50/99" in outcome.detail  # (1/2)(100/99)
