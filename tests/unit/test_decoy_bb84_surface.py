"""Public configuration, compilation and serialization at every declared route."""

import json
from fractions import Fraction as F

import pytest
from instances.decoy_bb84 import PARAMETERS, PRESETS, default_config, preparation

from certiqs_key.runs import preparation_record
from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.pipeline import Preparation
from certiqs_key.runs.surface import Preset


@pytest.mark.parametrize("route", ["encoded", "licensed", "licensed+two-sector"])
def test_public_preparation_compiles_each_route_and_records_source(route: str):
    config = default_config(device={"route": route, "source_cutoff": 1})
    outcome = preparation(config)
    assert isinstance(outcome, Preparation), outcome
    record = preparation_record(outcome)
    serialized = json.dumps(record)
    assert "mode_and_intensity" in serialized
    assert "poisson_bounds" in serialized
    assert "decoy.source_category_lattice" in serialized
    assert "wcp_source_model" in serialized
    assert "tagging" in serialized
    assert outcome.raw_joint_distribution is not None
    assert sum(outcome.raw_joint_distribution.values()) == 1


@pytest.mark.parametrize(
    "mode", ["merged-discard", "announcement-resolved", "pair-resolved"]
)
def test_maps_keep_generation_bit_private(mode: str):
    result = preparation(
        default_config(device={"acceptance_map": mode, "source_cutoff": 1})
    )
    assert isinstance(result, Preparation), result
    declaration = result.declaration
    for v in declaration.bob_alphabet:
        assert declaration.announcement("gen-signal-H", v) == declaration.announcement(
            "gen-signal-V", v
        )


def test_float_probability_cells_survive_payload_and_source_records():
    config = default_config(
        declared_tolerance=0.0,
        device={
            "test_signal": 0.1,
            "test_weak": 0.3,
            "test_vacuum": 0.6,
            "source_cutoff": 1,
        },
    )
    restored = RunConfig.from_payload(json.loads(json.dumps(config.to_payload())))
    # No optical tolerance is available at tau=0; use the same public config's
    # recorded source preparation before the receiver's independent refusal.
    from tests.support.lowered_templates import decoy_source

    prepared, source = decoy_source(restored)
    assert sum(source.tagged.model.weights.values()) == 1
    assert json.loads(json.dumps(prepared.input_preparation))
    assert any(
        record.get("admission") == "float_rounding_cells"
        for record in prepared.input_preparation
    )


@pytest.mark.parametrize("preset", PRESETS, ids=lambda p: p.name)
def test_presets_use_the_same_public_surface(preset: Preset):
    config = default_config(
        model=dict(preset.model), device={**dict(preset.device), "source_cutoff": 1}
    )
    outcome = preparation(config)
    assert isinstance(outcome, Preparation), outcome


def test_nonintegral_cutoff_is_not_silently_truncated():
    with pytest.raises(ValueError, match="integer"):
        preparation(default_config(device={"source_cutoff": F(3, 2)}))


def test_parameter_defaults_cover_every_declared_configuration_key():
    config = default_config()
    # The one parameter with no default: the receiver's factored loss, which
    # left unset is the receiver's own default, the largest efficiency divided
    # by 99/100, or 1 from 99/100 on
    # (receiver/detector-imperfections/req:efficiency-normalization).
    unset = {"efficiency_normalization"}
    for section in ("model", "device"):
        names = {p.name for p in PARAMETERS if str(p.section) == section}
        assert set(getattr(config, section)) == names - unset


def test_default_exact_window_tracks_overridden_receiver_cutoff():
    assert default_config(device={"photon_cutoff": 2}).device["exact_window"] == 3


def test_default_endpoint_rule_is_practical_and_overridable():
    assert default_config().endpoint_rule == "bernstein"
    assert default_config(endpoint_rule="exact").endpoint_rule == "exact"


def test_ordinary_numeric_inputs_compile_through_public_surface():
    config = default_config(
        device={
            "test_signal": 0.1,
            "test_weak": 0.3,
            "test_vacuum": 0.6,
            "mu_signal": "4/5",
            "source_cutoff": 1,
        }
    )
    restored = RunConfig.from_payload(json.loads(json.dumps(config.to_payload())))
    outcome = preparation(restored)
    assert isinstance(outcome, Preparation), outcome
    serialized = json.dumps(preparation_record(outcome))
    assert "decoy.source_category_lattice" in serialized
    assert "poisson_bounds" in serialized
