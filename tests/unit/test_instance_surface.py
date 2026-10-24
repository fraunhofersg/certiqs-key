"""EVERY discovered instance exports the full surface, in the shared types.

The uniformity rule behind it: "nothing in the frontend should be hardcoded to
specific instances ... [they] should all derive fully mechanistically from the
relevant parameters of the instance / run". The test this file is named for is
"a test asserts that every listed package exports the full surface", written over
:func:`instances.discover`, so that adding an instance to the list without a
surface is a failure rather than a silent half-instance.

NOT ONE TEST PER INSTANCE. Every assertion below is parameterised over the
discovered packages and names none of them, which is the same property the
rule asks of a consumer: if this file had to be edited to add an instance, so
would the frontend.
"""

from __future__ import annotations

import inspect
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import pytest
from instances import INSTANCE_PACKAGES, discover

from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.pipeline import Preparation
from certiqs_key.runs.surface import (
    InstanceDescriptor,
    Kind,
    ParameterSpec,
    Preset,
    Quantity,
    Section,
)

pytestmark = pytest.mark.contract

ROOT = Path(__file__).resolve().parents[2]
SURFACES = discover()

#: The names the surface fixes, and the file asserts exactly these.
#: ``preparation`` is the oracle-free preparation: it needs this instance's OWN
#: wiring -- the device requests, the specification provider, the two optional
#: providers -- so a consumer that wants the acceptance alphabet or the snap
#: records before committing to a solve does not rebuild the wiring.
REQUIRED = (
    "DESCRIPTOR",
    "PARAMETERS",
    "PRESETS",
    "default_config",
    "preparation",
    "runner",
)


@pytest.fixture(params=SURFACES, ids=[module.DESCRIPTOR.id for module in SURFACES])
def surface(request: pytest.FixtureRequest) -> ModuleType:
    """One discovered instance's surface module."""
    return request.param  # type: ignore[no-any-return]


def test_discovery_lists_every_package_and_the_packages_exist() -> None:
    """A consumer enumerates instances without naming one."""
    assert INSTANCE_PACKAGES
    assert len(SURFACES) == len(INSTANCE_PACKAGES)
    for name in INSTANCE_PACKAGES:
        assert (ROOT / "instances" / name / "__init__.py").exists()


def test_every_instance_exports_the_full_surface(surface: ModuleType) -> None:
    """The six names, and no instance is excused one of them."""
    for name in REQUIRED:
        assert hasattr(surface, name), (surface.DESCRIPTOR.id, name)


def test_the_descriptor_is_the_shared_type_and_its_readme_exists(
    surface: ModuleType,
) -> None:
    """Three strings and a path a reader can follow."""
    descriptor = surface.DESCRIPTOR
    assert isinstance(descriptor, InstanceDescriptor)
    assert descriptor.id and descriptor.title and descriptor.summary
    assert (ROOT / descriptor.readme).exists(), descriptor.readme


def test_the_descriptor_id_is_the_package_name(surface: ModuleType) -> None:
    """So that a consumer can go from a record back to the package."""
    assert surface.DESCRIPTOR.id in INSTANCE_PACKAGES


def test_the_parameter_table_is_the_shared_type_and_is_well_formed(
    surface: ModuleType,
) -> None:
    """Every field of every spec, in the vocabulary ``runs/`` defines."""
    parameters = surface.PARAMETERS
    assert parameters, surface.DESCRIPTOR.id
    names = [spec.name for spec in parameters]
    assert len(names) == len(set(names)), names
    for spec in parameters:
        assert isinstance(spec, ParameterSpec)
        assert isinstance(spec.section, Section)
        assert isinstance(spec.kind, Kind)
        # THE VOCABULARY IS CLOSED, which is what lets a consumer attach a
        # conversion without knowing the parameter.
        assert isinstance(spec.quantity, Quantity)
        assert spec.meaning, spec.name
        assert isinstance(spec.snapped, bool)


def test_a_per_port_parameter_is_keyed_by_the_port_map_s_labels(
    surface: ModuleType,
) -> None:
    """Not by a fixed count of four: the ports are the receiver's declaration."""
    for spec in surface.PARAMETERS:
        if spec.kind is not Kind.PER_PORT_FRACTION:
            assert spec.per_port_labels == (), spec.name
            continue
        assert spec.per_port_labels, spec.name
        assert set(spec.default) == set(spec.per_port_labels), spec.name


def test_every_default_is_inside_its_own_declared_domain(
    surface: ModuleType,
) -> None:
    """A table whose default its own domain refuses would describe nothing."""
    for spec in surface.PARAMETERS:
        if spec.default is None:
            # An OPTIONAL parameter: absent is not a default standing in for a
            # number, and the instance says so at the site.
            continue
        if spec.kind is Kind.PER_PORT_FRACTION:
            for value in spec.default.values():
                assert spec.domain.admits(value), spec.name
            continue
        assert spec.domain.admits(spec.default), spec.name


def test_the_domain_is_data_and_survives_json(surface: ModuleType) -> None:
    """A consumer shows the admissible values without running the instance."""
    import json

    for spec in surface.PARAMETERS:
        payload = spec.as_payload()
        assert json.loads(json.dumps(payload)) == payload


def test_every_applies_when_resolves_inside_its_own_table(
    surface: ModuleType,
) -> None:
    """A condition names another parameter of this table, with values it admits.

    The instance also runs this check at import; asserting it here keeps the
    guarantee from depending on every instance remembering the call.
    """
    from certiqs_key.runs.surface import check_applicability

    check_applicability(surface.PARAMETERS, surface.DESCRIPTOR.id)
    table = {spec.name: spec for spec in surface.PARAMETERS}
    for spec in surface.PARAMETERS:
        payload = spec.as_payload()["applies_when"]
        if spec.applies_when is None:
            assert payload is None, spec.name
            continue
        assert set(payload) <= set(table) - {spec.name}, spec.name
        for name, values in spec.applies_when:
            assert all(table[name].domain.admits(value) for value in values), (
                spec.name,
                name,
            )


def test_presets_are_the_shared_type_and_may_be_empty(surface: ModuleType) -> None:
    """Optional, and an instance with none exports ``()`` not a placeholder."""
    presets = surface.PRESETS
    assert isinstance(presets, tuple)
    known = {spec.name for spec in surface.PARAMETERS}
    for preset in presets:
        assert isinstance(preset, Preset)
        assert preset.name
        assert set(preset.model) | set(preset.device) <= known, preset.name


def test_the_default_config_is_runnable_and_declares_its_tolerance(
    surface: ModuleType,
) -> None:
    """Every required field is filled and ``tau`` is DECLARED, never defaulted."""
    config = surface.default_config()
    assert isinstance(config, RunConfig)
    assert config.rounds > 0
    assert isinstance(config.declared_tolerance, float)
    assert 0.0 <= config.declared_tolerance < 1.0
    # And the sections carry the table's own keys, with admissible values.
    #
    # THE RULE IS "DECLARED, AND ADMISSIBLE", NOT "EXACTLY THE ROWS THAT CARRY A
    # DEFAULT": set equality against the rows whose `default` is not None would be a
    # statement about HOW a `default_config` happens to be built rather than about what
    # it owes a caller. An instance may fill an OPTIONAL row -- one whose table default
    # is absent because absent is a legal declaration -- when leaving it out would hand
    # back a configuration that runs and returns nothing; the optical instance fills
    # `exact_window` at `N + 1` for exactly that reason. What a caller is owed is that
    # every key is a parameter THIS TABLE DECLARES, that nothing with a default is
    # missing, and that every value its own domain ADMITS.
    for section, mapping in (
        (Section.MODEL, config.model),
        (Section.DEVICE, config.device),
    ):
        rows = {
            spec.name: spec
            for spec in surface.PARAMETERS
            if spec.section is section
        }
        with_defaults = {
            name for name, spec in rows.items() if spec.default is not None
        }
        assert with_defaults <= set(mapping), (surface.DESCRIPTOR.id, section)
        assert set(mapping) <= set(rows), (surface.DESCRIPTOR.id, section)
        for name, value in mapping.items():
            spec = rows[name]
            if spec.kind is Kind.PER_PORT_FRACTION:
                for item in value.values():
                    assert spec.domain.admits(item), (name, item)
            else:
                assert spec.domain.admits(value), (name, value)


def test_the_default_config_survives_this_instance_s_own_reader(
    surface: ModuleType,
) -> None:
    """The default config goes through the instance's own reader.

    It is what keeps the parameter table and the instance's own reader from
    drifting apart: a ``default_config()`` its own runner refuses (a table
    that declares a parameter as one rational PER PORT against a reader that
    accepts only a scalar) would raise before anything else happened. Every
    other test here is about the table or about the configuration OBJECT, and
    the integration suites build the receiver's parameters directly.

    IT GOES THROUGH ``preparation`` AND NOT ``runner``, which is the whole path
    up to but not including the solve: the key check, the instance's reader,
    the device prologue where there is one, and the compilation. That is every
    stage that can refuse a configuration, and it needs no oracle -- so this
    assertion is default-tier on both instances and names neither.
    """
    outcome = surface.preparation(surface.default_config())
    assert isinstance(outcome, Preparation), outcome
    # ... and the preparation is about THIS configuration: the acceptance
    # alphabet is the compiled declaration's own.
    assert outcome.acceptance_alphabet
    assert outcome.declaration is not None


def test_a_station_scope_names_a_station_the_instance_declares(
    surface: ModuleType,
) -> None:
    """runs/parameter-station-scope, over every instance and naming none.

    ``ParameterSpec.station`` is a REFERENCE to a station the instance's own
    requests declare, so it is held against what a preparation of the default
    configuration actually emitted: every scoped parameter names one of those
    stations, a single-station instance scopes nothing, a multi-station
    instance scopes at least one parameter to each of its stations, and the
    payload a consumer reads carries the same value.
    """
    outcome = surface.preparation(surface.default_config())
    assert isinstance(outcome, Preparation), outcome
    stations = {
        emission.station.factor
        for emission in outcome.device_artifacts
        if emission.station is not None
    }
    scoped = {spec.station for spec in surface.PARAMETERS} - {None}
    for spec in surface.PARAMETERS:
        assert spec.as_payload()["station"] == spec.station, spec.name
    assert scoped <= stations, (surface.DESCRIPTOR.id, scoped, stations)
    if len(outcome.device_artifacts) > 1:
        assert scoped == stations, (surface.DESCRIPTOR.id, scoped, stations)
    else:
        assert not scoped, (surface.DESCRIPTOR.id, scoped)


def test_the_default_config_digests_and_round_trips(surface: ModuleType) -> None:
    """The configuration every instance offers first digests and round-trips.

    A default a caller cannot key a cache on, submit as JSON or compare with
    another is not usable as a starting point, and per-port mappings are
    values that can break it.
    """
    import json

    declared = surface.default_config()
    assert len(declared.digest()) == 64
    assert RunConfig.from_payload(declared.to_payload()) == declared
    assert json.loads(json.dumps(declared.to_payload())) == declared.to_payload()


def test_a_per_port_parameter_takes_a_mapping_and_not_a_scalar(
    surface: ModuleType,
) -> None:
    """ONE SHAPE, and the key check and the reader agree about which.

    ``check_keys`` and the instance's reader agree on the shape. The shape is the
    kind's, stated once on ``Kind.PER_PORT_FRACTION``, and a consumer derives it from
    the table rather than discovering it.
    """
    from certiqs_key.runs.surface import check_keys

    for spec in surface.PARAMETERS:
        if spec.kind is not Kind.PER_PORT_FRACTION:
            continue
        section = spec.section
        # The declared default is the admissible shape ...
        check_keys(
            section,
            {spec.name: dict(spec.default)},
            surface.PARAMETERS,
            surface.DESCRIPTOR.id,
        )
        # ... and a scalar is not.
        with pytest.raises(ValueError, match=spec.name):
            check_keys(
                section,
                {spec.name: Fraction(1)},
                surface.PARAMETERS,
                surface.DESCRIPTOR.id,
            )
        # A mapping keyed by anything but the port labels is refused too, and
        # the message names the labels the receiver declared.
        with pytest.raises(KeyError, match=spec.name):
            check_keys(
                section,
                {spec.name: {"not-a-port": Fraction(1)}},
                surface.PARAMETERS,
                surface.DESCRIPTOR.id,
            )


def test_the_default_config_takes_overrides(surface: ModuleType) -> None:
    """A caller varies one field without rebuilding the rest."""
    config = surface.default_config(rounds=4_321)
    assert config.rounds == 4_321


def test_every_preset_builds_a_configuration_its_own_instance_accepts(
    surface: ModuleType,
) -> None:
    """A preset that its instance refuses would be a fixture of nothing."""
    from certiqs_key.runs.surface import check_keys

    for preset in surface.PRESETS:
        config = surface.default_config(
            model={**surface.default_config().model, **dict(preset.model)},
            device={**surface.default_config().device, **dict(preset.device)},
        )
        check_keys(
            Section.MODEL, config.model, surface.PARAMETERS, surface.DESCRIPTOR.id
        )
        check_keys(
            Section.DEVICE, config.device, surface.PARAMETERS, surface.DESCRIPTOR.id
        )


def test_the_runner_takes_the_same_arguments_on_every_instance(
    surface: ModuleType,
) -> None:
    """One signature, so a caller drives a new instance with no code of its own.

    The oracle is REQUIRED and has no default, here as on ``run_slice``: the
    capability probe that decides whether an oracle can serve a declaration is
    ``meat-core``'s gate, which refuses an oracle that cannot, and an instance
    that defaulted one would be choosing a backend.
    """
    signature = inspect.signature(surface.runner)
    assert list(signature.parameters) == [
        "oracle",
        "directory",
        "created_by",
        "observer",
        "honest_provider",
        "honest_model_note",
    ], surface.DESCRIPTOR.id
    assert signature.parameters["oracle"].default is inspect.Parameter.empty
    assert signature.parameters["directory"].default is inspect.Parameter.empty
    for optional in ("observer", "honest_provider", "honest_model_note"):
        assert signature.parameters[optional].default is None


def test_an_unknown_key_is_refused_by_the_instance_s_own_check(
    surface: ModuleType,
) -> None:
    """The check READS the table, so the table cannot drift from the instance."""
    from certiqs_key.runs.surface import check_keys

    with pytest.raises(KeyError, match="whatever"):
        check_keys(
            Section.MODEL,
            {"whatever": Fraction(1, 2)},
            surface.PARAMETERS,
            surface.DESCRIPTOR.id,
        )


def test_a_value_outside_its_domain_is_refused_by_the_same_check(
    surface: ModuleType,
) -> None:
    """The domain is decided, not merely displayed."""
    from certiqs_key.runs.surface import check_keys

    spec = next(
        spec
        for spec in surface.PARAMETERS
        if spec.kind is Kind.FRACTION and spec.domain.form == "interval"
    )
    with pytest.raises(ValueError, match=spec.name):
        check_keys(
            spec.section, {spec.name: Fraction(-1)}, surface.PARAMETERS, "test"
        )
