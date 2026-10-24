"""Production preparation of both independently emitted BBM92 stations."""

from dataclasses import replace
from fractions import Fraction

import pytest
from instances.bbm92.surface import default_config, preparation

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.runs.pipeline import Preparation


@pytest.mark.parametrize("route", ["encoded", "licensed", "licensed+two-sector"])
def test_routes_prepare_both_station_licences(route: str):
    config = default_config()
    config = replace(config, device={**config.device, "route": route})
    result = preparation(config)
    assert isinstance(result, Preparation), result
    assert len(result.device_artifacts) == 2
    assert result.raw_joint_distribution is not None
    assert sum(result.raw_joint_distribution.values(), Fraction()) == 1
    constraints = result.specification.constraints
    if route != "encoded":
        assert constraints.entries
        assert {entry.scope for entry in constraints.entries} == {
            "alice_station",
            "bob_station",
        }
        assert constraints.attack_set_license is not None
        assert constraints.feasibility_witness is not None


def test_spdc_surface_uses_all_photon_statistics():
    config = default_config()
    config = replace(config, device={**config.device, "source_model": "spdc"})
    result = preparation(config)
    assert isinstance(result, Preparation), result
    table = result.raw_joint_distribution
    assert table is not None
    assert sum(table.values(), Fraction()) == 1
    assert min(table.values()) >= 0
    assert result.channel_interface is not None
    assert result.channel_interface.source_model == "spdc"


def _raw(**changes: object) -> dict[tuple[str, str], Fraction]:
    config = default_config()
    model = {k: v for k, v in changes.items() if k in config.model}
    device = {k: v for k, v in changes.items() if k not in config.model}
    config = replace(
        config,
        model={**config.model, **model},
        device={**config.device, **device},
    )
    result = preparation(config)
    assert isinstance(result, Preparation), result
    assert result.raw_joint_distribution is not None
    return dict(result.raw_joint_distribution)


def test_each_source_number_moves_the_data_under_its_own_model_only():
    """The evidence behind ``applies_when`` on visibility and mean_pairs."""
    ideal = _raw(source_model="ideal_pair")
    assert _raw(source_model="ideal_pair", visibility=Fraction(9, 10)) != ideal
    assert _raw(source_model="ideal_pair", mean_pairs=Fraction(1, 4)) == ideal
    spdc = _raw(source_model="spdc")
    assert _raw(source_model="spdc", mean_pairs=Fraction(1, 4)) != spdc
    assert _raw(source_model="spdc", visibility=Fraction(9, 10)) == spdc


def test_the_party_local_view_matters_on_the_licensed_routes_only():
    """The evidence behind ``applies_when`` on party_local_view."""

    def entries(route: str, view: str) -> object:
        config = default_config()
        config = replace(
            config,
            device={**config.device, "route": route, "party_local_view": view},
        )
        result = preparation(config)
        assert isinstance(result, Preparation), result
        return result.specification.constraints.entries

    assert entries("encoded", "operator") == ()
    with pytest.raises(MalformedInputError, match="licensed_scalar"):
        entries("encoded", "licensed_scalar")
    for route in ("licensed", "licensed+two-sector"):
        assert entries(route, "operator") != entries(route, "licensed_scalar")


def test_each_station_window_defaults_from_its_cutoff():
    config = default_config()
    device = {**config.device, "alice_photon_cutoff": 3}
    del device["alice_exact_window"]
    configured = default_config(device=device)
    assert configured.device["alice_exact_window"] == 4
    assert configured.device["bob_exact_window"] == 2
    explicit = default_config(device={**device, "alice_exact_window": None})
    assert explicit.device.get("alice_exact_window") is None


def test_probe_free_station_labels_carry_no_probe_component():
    """Both stations declare ``T = {off}``, so no emitted label spells ``,off``.

    The probe setting is an add-on (reductions.inputs.outcome_label): the
    stations' target alphabets are their detection letters, Alice's weighted
    labels are ``(y,f)`` and the joint readouts ``(y,f)__y'``.
    """
    from certiqs_key.runs.record import preparation_record

    result = preparation(default_config())
    assert isinstance(result, Preparation), result
    payload = preparation_record(result)
    public = payload["compiled"]["public"]
    text = repr(public)
    assert ",off" not in text
    readouts = public["label_index_map"]
    assert readouts is not None
    (weighting,) = public["choice_weightings"]
    assert weighting["setting_map"]["H"] == "off"
    assert ["(H,gen)", "H", "gen"] in weighting["support"]
    assert "(H,gen)__V" in repr(public["key_map"])


def test_the_test_coin_is_recorded_with_its_letters():
    """``compiled.public.choice_weightings`` names the factor, letters and weights.

    One entry per weighted factor, naming the factor and no party.
    """
    from certiqs_key.runs.record import preparation_record

    result = preparation(default_config())
    assert isinstance(result, Preparation), result
    (weighting,) = preparation_record(result)["compiled"]["public"]["choice_weightings"]
    assert "party" not in weighting
    assert weighting["factor"] == "alice_station"
    assert weighting["setting_alphabet"] == ["off"]
    assert weighting["choice_alphabet"] == ["gen", "test"]
    # The default coin, 1/8, is exact on the 12-bit lattice the preparation
    # snaps it to, so the recorded matrix is the declared one.
    assert weighting["matrix"] == {"off|gen": "7/8", "off|test": "1/8"}
    assert [row[2] for row in weighting["support"]] == ["gen", "test"] * (
        len(weighting["source_alphabet"])
    )
