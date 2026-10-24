"""Convenient inputs retain normalization, bound direction and provenance."""

from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from certiqs_key.foundations.exact import is_binary64
from certiqs_key.runs.inputs import (
    NumericInput,
    exact_input,
    prepare_bound,
    prepare_probabilities,
)


@pytest.mark.parametrize(
    "values",
    [
        [Fraction(1, 3), Fraction(2, 3), 0],
        [Decimal("0.1"), Decimal("0.9"), 0],
        ["1/3", "2/3", "0"],
        [0.1, 0.9, 0],
    ],
)
def test_prepared_probabilities_are_exact_and_record_the_original(
    values: list[NumericInput],
) -> None:
    result = prepare_probabilities(
        values, tolerance=1e-12, lattice_exponent=40, site="weights"
    )
    assert sum(result.values) == 1
    assert result.values[-1] == 0
    partial = Fraction()
    for value in result.values:
        partial += value
        assert is_binary64(value)
        assert is_binary64(partial)
    before = tuple(map(exact_input, values))
    assert tuple(map(Fraction, result.record["input_values"])) == before
    assert tuple(map(Fraction, result.record["total_displacement"])) == tuple(
        after - old for old, after in zip(before, result.values, strict=True)
    )


def test_existing_fine_dyadic_declaration_is_unchanged() -> None:
    values = [Fraction(1, 2**50), 1 - Fraction(1, 2**50)]
    result = prepare_probabilities(
        values, tolerance=0.0, lattice_exponent=40, site="weights"
    )
    assert result.values == tuple(values)
    assert result.record["snaps"] == []


def test_bad_normalization_is_not_hidden_by_conversion() -> None:
    with pytest.raises(ValueError, match="normalization"):
        prepare_probabilities(
            [Fraction(1, 2), Fraction(1, 2) + Fraction(1, 2**100)],
            tolerance=0.0,
            lattice_exponent=40,
            site="weights",
        )


@pytest.mark.parametrize("value", ["0.1", Decimal("0.1234"), Fraction(1, 3), 0.9])
def test_prepared_bounds_have_the_required_direction(value: NumericInput) -> None:
    original = exact_input(value)
    lower, lo = prepare_bound(value, direction="lower", lattice_exponent=40, site="p")
    upper, hi = prepare_bound(value, direction="upper", lattice_exponent=40, site="p")
    assert lower <= original <= upper
    assert upper - lower <= Fraction(1, 2**40)
    assert Fraction(lo["total_displacement"]) == lower - original
    assert Fraction(hi["total_displacement"]) == upper - original


@pytest.mark.parametrize("value", [True, "nan", float("inf"), Decimal("NaN")])
def test_non_numeric_or_nonfinite_values_are_refused(value: NumericInput) -> None:
    with pytest.raises((TypeError, ValueError)):
        exact_input(value)


def test_bb84_public_preparation_accepts_fractional_weights_and_records_them() -> None:
    from instances.bb84.surface import default_config, preparation

    from certiqs_key.runs.config import RunConfig
    from certiqs_key.runs.record import preparation_record

    config = default_config(
        model={"qber": Decimal("0.02")},
        device={"alice_z": "1/3", "alice_x": "2/3", "bob_z": 0.5, "bob_x": 0.5},
        declared_tolerance=0,
    )
    assert RunConfig.from_payload(config.to_payload()) == config
    outcome = preparation(config)
    assert not outcome.refuses
    record = preparation_record(outcome)
    conversions = record["rows_adaptation"]["input_preparation"]
    weights = next(row for row in conversions if row["rule"] == "shared_family_snap")
    assert weights["input_values"] == ["1/3", "2/3"]
    assert sum(map(Fraction, weights["prepared_values"])) == 1
    assert any(Fraction(value) != 0 for value in weights["total_displacement"])


def test_default_prepared_configuration_keeps_its_historical_payload() -> None:
    from instances.bb84.surface import default_config

    config = default_config()
    assert "input_preparation" not in config.to_payload()


def test_float_rounding_cells_allow_decimal_probabilities_at_zero_tau() -> None:
    result = prepare_probabilities(
        [0.1, 0.9, 0.0], tolerance=0.0, lattice_exponent=40, site="weights"
    )
    assert result.record["admission"] == "float_rounding_cells"
    assert result.record["declared_tolerance"] == 0.0
    assert Fraction(result.record["normalization_defect"]) == Fraction(1, 2**55)
    assert sum(result.values) == 1
    assert result.values[0] > 0 and result.values[1] > 0 and result.values[2] == 0


@pytest.mark.parametrize("kind", [Fraction, Decimal, str])
def test_exact_input_mismatch_gets_no_representation_allowance(kind: type) -> None:
    with pytest.raises(ValueError, match="normalization"):
        prepare_probabilities(
            [kind("0.1"), kind("0.90000000000000001")],
            tolerance=0.0,
            lattice_exponent=40,
            site="weights",
        )


def test_rounding_cell_power_of_two_asymmetry_and_nearest_even_endpoints() -> None:
    import math

    from certiqs_key.runs.inputs import _float_cell

    lo, hi, closed = _float_cell(0.5)
    assert lo == Fraction(1, 2) - Fraction(1, 2**55)
    assert hi == Fraction(1, 2) + Fraction(1, 2**54)
    assert closed
    admitted = prepare_probabilities(
        [0.5, 1 - lo], tolerance=0.0, lattice_exponent=40, site="weights"
    )
    assert admitted.record["admission"] == "float_rounding_cells"
    odd = math.nextafter(0.5, math.inf)
    odd_lo, _, odd_closed = _float_cell(odd)
    assert not odd_closed
    with pytest.raises(ValueError, match="normalization"):
        prepare_probabilities(
            [odd, 1 - odd_lo], tolerance=0.0, lattice_exponent=40, site="weights"
        )


def test_subnormal_cells_are_exact_and_support_is_not_silently_removed() -> None:
    import math

    from certiqs_key.runs.inputs import _float_cell

    tiny = math.nextafter(0.0, 1.0)
    lo, hi, closed = _float_cell(tiny)
    assert (lo, hi, closed) == (Fraction(1, 2**1075), Fraction(3, 2**1075), False)
    assert _float_cell(-0.0) == (0, 0, True)
    with pytest.raises(ValueError, match="positive support"):
        prepare_probabilities(
            [tiny, 1.0], tolerance=0.0, lattice_exponent=40, site="weights"
        )


def test_many_exact_tenths_use_recorded_snap_guard_without_core_tolerance() -> None:
    result = prepare_probabilities(
        [Fraction(1, 10)] * 10,
        tolerance=0.0,
        lattice_exponent=40,
        site="weights",
    )
    assert result.record["normalization_defect"] == "0"
    assert result.record["declared_tolerance"] == 0.0
    assert sum(result.values) == 1
    assert all(value > 0 for value in result.values)


def test_float_origin_survives_config_round_trip_and_public_preparation() -> None:
    import json

    from instances.bb84.surface import default_config, preparation

    from certiqs_key.runs.config import RunConfig
    from certiqs_key.runs.record import preparation_record

    config = default_config(
        device={"alice_z": 0.1, "alice_x": 0.9, "bob_z": 0.1, "bob_x": 0.9}
    )
    restored = RunConfig.from_payload(json.loads(json.dumps(config.to_payload())))
    assert restored == config
    outcome = preparation(restored)
    assert not outcome.refuses
    rows = preparation_record(outcome)["rows_adaptation"]["input_preparation"]
    weights = [row for row in rows if row["rule"] == "shared_family_snap"]
    assert len(weights) == 2
    assert all(row["admission"] == "float_rounding_cells" for row in weights)
    assert all(row["declared_tolerance"] == 0.0 for row in weights)


def test_replacing_device_does_not_lend_old_float_allowance_to_exact_fractions() -> (
    None
):
    from instances.bb84.surface import default_config, preparation

    original = default_config(
        device={"alice_z": 0.1, "alice_x": 0.9, "bob_z": 0.5, "bob_x": 0.5}
    )
    exact = original.with_(device=dict(original.device))
    assert not any(row["site"].startswith("device.") for row in exact.input_preparation)
    with pytest.raises(ValueError, match="normalization"):
        preparation(exact)
    fresh_floats = exact.with_(
        device={"alice_z": 0.1, "alice_x": 0.9, "bob_z": 0.5, "bob_x": 0.5}
    )
    assert not preparation(fresh_floats).refuses


def test_numeric_looking_device_name_is_not_parsed_and_round_trips() -> None:
    from instances.bb84.surface import default_config

    from certiqs_key.runs.config import RunConfig

    config = RunConfig.from_inputs(
        **{
            field: getattr(default_config(), field)
            for field in default_config().__dataclass_fields__
        },
    ).with_(device={"route": "123"})
    restored = RunConfig.from_payload(config.to_payload())
    assert restored.device == {"route": "123"}
    assert isinstance(restored.device["route"], str)


def test_run_record_config_preserves_input_conversion_evidence() -> None:
    from instances.bb84.surface import default_config

    from certiqs_key.runs.record import _config_payload

    config = default_config(model={"qber": Decimal("0.02")})
    assert _config_payload(config)["input_preparation"] == list(
        config.input_preparation
    )
    assert "input_preparation" not in _config_payload(default_config())


def test_optical_public_surface_uses_schema_for_numbers_and_choice_names() -> None:
    from instances.optical_bb84.surface import default_config, preparation

    from certiqs_key.runs.record import preparation_record

    device = dict(default_config().device)
    device["basis_split"] = Decimal("0.1")
    device["half_wave_angle"] = "1/8"
    device["efficiency"] = dict.fromkeys(device["efficiency"], "0.9")
    config = default_config(device=device)
    outcome = preparation(config)
    assert not outcome.refuses
    rows = preparation_record(outcome)["rows_adaptation"]["input_preparation"]
    assert any(row["site"] == "device.basis_split" for row in rows)
    assert any(row["site"].startswith("device.efficiency.") for row in rows)
    bad = dict(device, route="123")
    named = default_config(device=bad)
    assert named.device["route"] == "123"
    assert isinstance(named.device["route"], str)


def test_json_numeric_float_inputs_retain_their_origin() -> None:
    from instances.bb84.surface import default_config, preparation

    from certiqs_key.runs.config import RunConfig

    payload = default_config().to_payload()
    payload["device"] = {"alice_z": 0.1, "alice_x": 0.9, "bob_z": 0.5, "bob_x": 0.5}
    payload["model"] = {"qber": 0.02}
    loaded = RunConfig.from_payload(payload)
    assert any(row["input_type"] == "float" for row in loaded.input_preparation)
    assert not preparation(loaded).refuses


def test_runner_uses_the_same_prepared_weights_as_preparation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from instances.bb84 import surface

    from certiqs_key.runs.record import preparation_record

    config = surface.default_config(
        device={"alice_z": 0.1, "alice_x": 0.9, "bob_z": 0.5, "bob_x": 0.5}
    )
    expected = surface.preparation(config)
    received = {}

    def capture(*args: Any, **kwargs: Any) -> Any:
        received.update(kwargs)
        # Compilation is exercised by preparation above; this spy verifies
        # runner wiring without substituting a numerical solver oracle.
        return expected

    # The bb84 runner is its document surface's, so the spy replaces the
    # run_slice that module calls.
    import instances.declared.surface as document_surface

    monkeypatch.setattr(document_surface, "run_slice", capture)
    outcome = surface.runner(object(), tmp_path, created_by="test")(config, 0)
    assert received["declared_tolerance"] == 0.0
    assert received["run_id"]
    rows = preparation_record(outcome)["rows_adaptation"]["input_preparation"]
    assert any(row.get("admission") == "float_rounding_cells" for row in rows)
