"""The run-level parameter table, and A-AUTH's two inputs from configuration to solve.

``runs/surface.py`` ``RUN_PARAMETERS`` describes the configuration's own fields
once for every instance (record schema 0.20.0): the key-rate report's "Your
inputs" reads a meaning, a unit and a domain for ``parameters.eps_auth`` from it as it
reads one for ``model.qber`` from an instance's table. Its names are held to
:meth:`~certiqs_key.runs.config.RunConfig.to_payload` here, so a field added to
the configuration without a row fails.

``eps_auth`` and ``k_auth`` are run inputs, so what is held is that every
instance's runner forwards its configuration's values to ``run_slice``, and
that the record and the configuration's payload carry them.
"""

from __future__ import annotations

import dataclasses
import importlib
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from certiqs_key.runs.config import (
    AdvancedSolverSettings,
    AlphaSearchSettings,
    RunConfig,
    RunConfigError,
    SolverSettings,
)
from certiqs_key.runs.surface import (
    RUN_PARAMETERS,
    InstanceIdentity,
    Kind,
    Section,
)

pytestmark = pytest.mark.contract

#: The instance packages, each with the module whose runner calls ``run_slice``.
#: The four packaged templates run through the document surface's runner.
#: An instance a removable submodule brings is read only where it is
#: present.
RUNNER_MODULES: dict[str, str] = {
    "bb84": "instances.declared.surface",
    "bbm92": "instances.declared.surface",
    "decoy_bb84": "instances.declared.surface",
    "optical_bb84": "instances.declared.surface",
}

#: The keys of ``RunConfig.to_payload`` that are not the configuration's own:
#: the instance's two mappings and the two conversion records.
NOT_RUN_LEVEL = frozenset(
    {"model", "device", "device_name_fields", "input_preparation"}
)


def _payload_names() -> set[str]:
    """Return every run-level name the configuration's payload can carry.

    The ``parameters`` and ``solver`` blocks dotted; the solver's keys are
    its dataclass fields, since its payload writes only the chosen ones, its
    ``advanced`` block's one level deeper (record schema 0.43.0), and
    A-AUTH's two, the two snap parameters (record schema 0.22.0) and the two
    of the statistics check (0.37.0) are declared away from their defaults so
    that the payload writes them, and the opt-in alpha search (0.24.0) is set
    so that it is written.
    """
    from instances.bb84.surface import default_config

    payload = default_config(
        solver=SolverSettings(max_iterations=3),
        alpha_search=AlphaSearchSettings(),
        eps_auth=2.0**-40,
        k_auth=1,
        reference_enclosure=False,
        strict_snaps=True,
        statistics_check="off",
        min_model_pass_probability=Fraction(1, 3),
    ).to_payload()
    names = {key for key in payload if key not in NOT_RUN_LEVEL}
    names -= {"parameters", "solver", "alpha_search"}
    names |= {f"parameters.{key}" for key in payload["parameters"]}
    names |= {f"alpha_search.{key}" for key in payload["alpha_search"]}
    names |= {
        f"solver.{field.name}"
        for field in dataclasses.fields(SolverSettings)
        if field.name != "advanced"
    }
    names |= {
        f"solver.advanced.{field.name}"
        for field in dataclasses.fields(AdvancedSolverSettings)
    }
    return names


def test_the_names_are_the_configuration_s_payload_keys() -> None:
    names = [spec.name for spec in RUN_PARAMETERS]
    assert len(names) == len(set(names))
    assert set(names) == _payload_names()


def test_the_key_length_block_carries_a_auth_s_two_inputs() -> None:
    names = {spec.name for spec in RUN_PARAMETERS if spec.section is Section.KEY_LENGTH}
    assert names == {
        "parameters.alpha",
        "parameters.eps_pa",
        "parameters.eps_ev",
        "parameters.lambda_ec",
        "parameters.eps_auth",
        "parameters.k_auth",
    }


def test_every_row_is_run_level_and_has_a_meaning() -> None:
    for spec in RUN_PARAMETERS:
        assert spec.section in (Section.RUN, Section.KEY_LENGTH, Section.SOLVER)
        assert spec.meaning, spec.name
        assert not spec.snapped, spec.name
        # A default is admitted by its own domain (None: required or solver's own).
        if spec.default is not None:
            assert spec.domain.admits(spec.default), spec.name
        payload = spec.as_payload()
        assert payload["name"] == spec.name
        assert payload["section"] == str(spec.section)


def test_alpha_and_parameters_alpha_are_two_rows() -> None:
    by_name = {spec.name: spec for spec in RUN_PARAMETERS}
    assert by_name["alpha"].section is Section.RUN
    assert by_name["parameters.alpha"].section is Section.KEY_LENGTH


def test_the_alpha_search_rows_default_to_the_settings_own() -> None:
    """The four rows of the opt-in search (0.24.0): an absent key's reading."""
    by_name = {spec.name: spec for spec in RUN_PARAMETERS}
    defaults = AlphaSearchSettings().as_payload()
    for key, value in defaults.items():
        spec = by_name[f"alpha_search.{key}"]
        assert spec.section is Section.RUN, key
        assert spec.default == value, key


def test_the_a_auth_defaults_are_meat_core_s() -> None:
    """``eps_auth`` and ``k_auth`` default to 0, the interface rows' default."""
    by_name = {spec.name: spec for spec in RUN_PARAMETERS}
    assert by_name["parameters.eps_auth"].default == 0.0
    assert by_name["parameters.k_auth"].default == 0
    assert by_name["parameters.eps_auth"].kind is Kind.FLOAT
    assert by_name["parameters.k_auth"].unit == "bit"
    assert not by_name["parameters.eps_auth"].domain.admits(1.0)
    assert by_name["parameters.eps_auth"].domain.admits(0.0)


def test_the_configuration_carries_and_round_trips_a_auth() -> None:
    from instances.bb84.surface import default_config

    config = default_config(eps_auth=2.0**-40, k_auth=256)
    payload = config.to_payload()
    assert payload["parameters"]["eps_auth"] == 2.0**-40
    assert payload["parameters"]["k_auth"] == 256
    assert RunConfig.from_payload(payload) == config
    # At the defaults the configuration's payload omits both, so a
    # configuration from before they existed keeps its payload and digest...
    plain = default_config()
    assert {"eps_auth", "k_auth"}.isdisjoint(plain.to_payload()["parameters"])
    assert RunConfig.from_payload(plain.to_payload()) == plain
    # ...while the record names the zeros it was computed with.
    from certiqs_key.runs.pipeline import SliceRefusal, SliceStage
    from certiqs_key.runs.record import record_run

    refusal = SliceRefusal(stage=SliceStage.COMPILATION, reason="r", detail="d")
    recorded = record_run(refusal, plain, created_by="test").payload["config"]
    assert recorded["parameters"]["eps_auth"] == 0.0
    assert recorded["parameters"]["k_auth"] == 0
    assert recorded["config_digest"] == plain.digest()
    # Declared, they are part of the request: two security statements are
    # two requests.
    assert config.digest() != plain.digest()


def test_an_exact_eps_auth_is_prepared_to_binary64_and_recorded() -> None:
    from instances.bb84.surface import default_config

    config = default_config(eps_auth=Fraction(1, 3))
    assert config.eps_auth == 1 / 3
    assert any(row["site"] == "eps_auth" for row in config.input_preparation)


@pytest.mark.parametrize(
    "changes",
    [{"eps_auth": 1.0}, {"eps_auth": -0.1}, {"k_auth": -1}, {"k_auth": 1.5}],
    ids=["eps-one", "eps-negative", "k-negative", "k-not-integer"],
)
def test_an_authentication_input_outside_its_domain_is_refused(
    changes: dict[str, Any],
) -> None:
    from instances.bb84.surface import default_config

    with pytest.raises(RunConfigError) as caught:
        dataclasses.replace(default_config(), **changes)
    assert caught.value.reason == "authentication_parameter_out_of_domain"


class _Forwarded(Exception):
    """Raised by the stand-in ``run_slice`` with the keywords it was given."""

    def __init__(self, keywords: dict[str, Any]) -> None:
        super().__init__("forwarded")
        self.keywords = keywords


@pytest.mark.parametrize("instance", sorted(RUNNER_MODULES))
def test_every_instance_runner_forwards_a_auth_to_the_solve(
    instance: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No runner drops the two inputs.

    ``run_slice`` defaults both to 0, so a runner that forgot them would solve
    at the defaults while the record said otherwise. The stand-in stops the
    run at that call, before any solve.
    """
    surface = importlib.import_module(f"instances.{instance}.surface")
    caller = importlib.import_module(RUNNER_MODULES[instance])

    def stand_in(*_: Any, **keywords: Any) -> Any:
        raise _Forwarded(keywords)

    monkeypatch.setattr(caller, "run_slice", stand_in)
    config = surface.default_config().with_(eps_auth=2.0**-35, k_auth=128)
    run = surface.runner(object(), tmp_path, created_by="test")
    with pytest.raises(_Forwarded) as caught:
        run(config, 0)
    assert caught.value.keywords["eps_auth"] == 2.0**-35
    assert caught.value.keywords["k_auth"] == 128


def test_an_instance_identity_is_the_descriptor_and_the_table() -> None:
    from instances.bb84.surface import DESCRIPTOR, PARAMETERS

    payload = InstanceIdentity(DESCRIPTOR, tuple(PARAMETERS)).as_payload()
    assert payload["id"] == DESCRIPTOR.id
    assert {"title", "summary", "readme"} <= set(payload)
    assert [row["name"] for row in payload["parameters"]] == [
        spec.name for spec in PARAMETERS
    ]
