"""Optical stations, the decoy source, transcripts and several stations.

THE EQUIVALENCE. Three whole documents -- the
packaged templates ``instances/{optical_bb84,decoy_bb84,bbm92}/protocol.yaml``
read as packaged -- lower to the SAME objects the library builds
by hand: each station's receiver request, reductions' protocol declaration,
reduction request and station identity are
``instances.common.passive_device.passive_device_requests`` at the station's
receiver parameters (with the instances' own identity strings), and the decoy
source's tagged declaration and preparation record are
``instances.common.wcp.prepare_source``'s in decoy BB84's shape.

THE COVERAGE DOCUMENTS. Each custom document exercises one
lowering no instance uses -- the port-Gram and instrument-matrix routes, a
quarter-wave plate with the catalogue's C4-C10, a declared dark-count matrix,
``tau`` modes, an explicit carried operator, a probe, three stations, a
two-intensity WCP source, a three-message transcript, a two-station Band A --
and the test asserts only that a MODULE decides it: a preparation, a module's
refusal as data, a wrapped module refusal with its own reason, or a module's
own ``MalformedInputError``. Never an exception of the lowering.

Also here: what the lowering itself refuses (a mode that names no mode, a
catalogue entry missing a field, a photon number past the bounds, the WCP
preparation's wrapped call sites), the recorded conversions of the float
routes, and ``certified_against`` read off the first-pass artefact.
"""

from __future__ import annotations

import copy
import traceback
from dataclasses import replace
from fractions import Fraction as F
from typing import Any

import pytest
from instances.common.declare import snap_settings
from instances.common.honest import MODELS, HonestContext
from instances.common.optics import PORTS, ReceiverParameters
from instances.common.passive_device import passive_device_requests
from instances.common.sources import bb84_qubit_source_part
from instances.declared import DocumentError, DocumentReason
from probe_presence import PROBE_PRESENT, requires_probe
from tests.support.declared_optical_documents import (
    COVERAGE,
    COVERAGE_CONFIG,
    coverage_surface,
    custom_from,
    instrument_matrix,
    port_grams,
    template_surface,
)
from tests.support.lowered_templates import wcp_source

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.receiver.numerics import PiMultiple
from certiqs_key.reductions.reasons import SourceMode
from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.pipeline import (
    DeviceRequests,
    MultiDeviceRequests,
    Preparation,
    SliceRefusal,
    Station,
)
from certiqs_key.transmitter.decoy import emit_decoy_declaration

#: The identity strings the instances' stations declare, as the Python
#: instances wrote them and the templates write them.
DECLARED_BY = {
    "optical_bb84": "instances.optical_bb84.declare",
    "decoy_bb84": "instances.decoy_bb84.declare",
}

#: Per instance: the defaults, and non-default configurations that move every
#: switch, each preset, and asymmetric, noisy and lossy devices.
NOISY = {"H": F(1, 10**6), "V": F(2, 10**6), "D": F(1, 10**6), "A": F(3, 10**6)}
LOSSY = {"H": F(9, 10), "V": F(4, 5), "D": F(9, 10), "A": F(9, 10)}
ROUTES = ("encoded", "licensed", "licensed+two-sector")
MAPS = ("merged-discard", "announcement-resolved", "pair-resolved")


def _optical_grid() -> list[tuple[str, dict[str, Any]]]:
    device = dict(template_surface("optical_bb84").default_config().device)
    grid: list[tuple[str, dict[str, Any]]] = [("defaults", {})]
    grid += [
        (
            f"{route}-{name}",
            {"device": {**device, "route": route, "acceptance_map": name}},
        )
        for route in ROUTES
        for name in MAPS
    ]
    grid += [
        (
            "noisy-lossy-cutoff-2",
            {
                "model": {"qber": F(1, 50), "transmittance": F(1, 2)},
                "device": {
                    **device,
                    "route": "licensed+two-sector",
                    "photon_cutoff": 2,
                    "exact_window": 3,
                    "dark_count": NOISY,
                    "efficiency": LOSSY,
                },
            },
        ),
        (
            "plate-extinction-no-window",
            {
                "device": {
                    "route": "licensed",
                    "acceptance_map": "merged-discard",
                    "half_wave_angle": F(1, 7),
                    "pbs_leak_transmitted": F(1, 100),
                    "pbs_leak_reflected": F(1, 100),
                    "basis_split": F(2, 3),
                }
            },
        ),
    ]
    return grid


def _decoy_grid() -> list[tuple[str, dict[str, Any]]]:
    grid: list[tuple[str, dict[str, Any]]] = [("defaults", {})]
    grid += [
        (f"{route}-{name}", {"device": {"route": route, "acceptance_map": name}})
        for route in ROUTES
        for name in MAPS
    ]
    grid += [
        (f"preset-{preset.name}", {"device": dict(preset.device)})
        for preset in template_surface("decoy_bb84").PRESETS
        if preset.device
    ]
    grid += [
        (
            "noisy-misaligned-thirds",
            {
                "model": {"transmittance": F(1, 3), "misalignment": F(1, 20)},
                "device": {
                    "route": "licensed+two-sector",
                    "gamma": F(1, 3),
                    "test_signal": F(1, 3),
                    "test_weak": F(1, 3),
                    "test_vacuum": F(1, 3),
                    "source_cutoff": 4,
                    "dark_count": NOISY,
                },
            },
        ),
        ("cutoff-2", {"device": {"photon_cutoff": 2, "efficiency": LOSSY}}),
    ]
    return grid


def _bbm92_grid() -> list[tuple[str, dict[str, Any]]]:
    config = template_surface("bbm92").default_config()
    device, model = dict(config.device), dict(config.model)
    grid: list[tuple[str, dict[str, Any]]] = [("defaults", {})]
    index = 0
    for source in ("ideal_pair", "spdc"):
        for bases in ("ZX", "Z"):
            for route in ROUTES:
                name = MAPS[index % 3]
                index += 1
                changes: dict[str, Any] = {
                    "source_model": source,
                    "key_bases": bases,
                    "route": route,
                    "acceptance_map": name,
                    "test_fraction": F(1, 7) if index % 2 else F(1, 8),
                }
                if route != "encoded":
                    changes["party_local_view"] = (
                        "licensed_scalar" if index % 2 else "operator"
                    )
                else:
                    # A dark count only on the encoded route: on a licensed one
                    # the factor assembly is refused in both (the domination
                    # link).
                    changes["bob_dark_count"] = NOISY
                grid.append(
                    (
                        f"{source}-{bases}-{route}-{name}",
                        {
                            "model": {
                                **model,
                                "mean_pairs": F(1, 20),
                                "bob_transmittance": F(1, 3),
                            },
                            "device": {
                                **device,
                                **changes,
                                "bob_basis_split": F(1, 3),
                            },
                        },
                    )
                )
    return grid


GRID: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "optical_bb84": _optical_grid(),
    "decoy_bb84": _decoy_grid(),
    "bbm92": _bbm92_grid(),
}

CASES = [
    (name, label, overrides) for name, grid in GRID.items() for label, overrides in grid
]
IDS = [f"{name}-{label}" for name, label, _ in CASES]


def _strip(value: Any) -> Any:
    """Drop every ``wall_time_s``, at any depth: the wall clock is not compared."""
    if isinstance(value, dict):
        return {k: _strip(v) for k, v in value.items() if k != "wall_time_s"}
    if isinstance(value, list):
        return [_strip(item) for item in value]
    return value


def _requests(device: DeviceRequests) -> tuple[Any, ...]:
    """Return a station's declarations, without the closures (adapter, providers)."""
    return (
        device.receiver_request,
        device.reduction_declaration,
        device.reduction_request,
        device.reduction_entry,
        device.station,
        device.carried_operator_provider is None,
    )


def _config(name: str, overrides: dict[str, Any]) -> tuple[Any, RunConfig]:
    document = template_surface(name)
    return document, document.default_config(**copy.deepcopy(overrides))


def _receiver(values: dict[str, object], prefix: str = "") -> ReceiverParameters:
    """Return one station's receiver parameters, read from a run's values.

    As the Python instances read them (``parameters_from_config``,
    ``station_parameters``): the per-port rows in the port map's order, the
    cutoff an integer, an absent window no window.
    """

    def ports(name: str) -> tuple[F, ...]:
        mapping = values[f"{prefix}{name}"]
        assert isinstance(mapping, dict)
        return tuple(F(mapping[label]) for label, _modes in PORTS)

    window = values.get(f"{prefix}exact_window")
    return ReceiverParameters(
        basis_split=F(values[f"{prefix}basis_split"]),  # type: ignore[arg-type]
        half_wave_angle=F(values[f"{prefix}half_wave_angle"]),  # type: ignore[arg-type]
        pbs_leak_transmitted=F(values[f"{prefix}pbs_leak_transmitted"]),  # type: ignore[arg-type]
        pbs_leak_reflected=F(values[f"{prefix}pbs_leak_reflected"]),  # type: ignore[arg-type]
        efficiency=ports("efficiency"),
        dark_count=ports("dark_count"),
        photon_cutoff=int(values[f"{prefix}photon_cutoff"]),  # type: ignore[call-overload]
        exact_window=None if window is None else int(window),  # type: ignore[call-overload]
    )


def _reference_requests(name: str, config: RunConfig) -> tuple[DeviceRequests, ...]:
    """Return the stations' requests the library builds by hand at ``config``.

    ``passive_device_requests`` at each station's receiver parameters, the
    run's tolerance, route and snap settings, with the instances' identity
    strings.
    """
    document = template_surface(name)
    configured, _lowered = document._read(config)
    values = document.resolve(config)
    common: dict[str, Any] = {
        "declared_tolerance": configured.declared_tolerance,
        "route": str(values["route"]),
        "snap": snap_settings(configured),
    }
    if name != "bbm92":
        return (
            passive_device_requests(
                _receiver(values), declared_by=DECLARED_BY[name], **common
            ),
        )
    stations = []
    for label, party in (("alice_station", "A"), ("bob_station", "B")):
        request = passive_device_requests(
            _receiver(values, label.removesuffix("station")),
            source_mode=SourceMode.UNTRUSTED,
            declared_by=f"instances.bbm92.{label}",
            **common,
        )
        stations.append(
            replace(
                request,
                reduction_declaration=replace(
                    request.reduction_declaration, party_label=party
                ),
                station=Station(factor=label, party=party),
            )
        )
    return tuple(stations)


# ===========================================================================
#  1. The lowered objects are the library's
# ===========================================================================


@pytest.mark.parametrize(
    "overrides",
    [overrides for _, overrides in GRID["optical_bb84"]],
    ids=[label for label, _ in GRID["optical_bb84"]],
)
def test_the_optical_station_lowers_to_the_library_requests(
    overrides: dict[str, Any],
) -> None:
    document, ours = _config("optical_bb84", overrides)
    configured, lowered = document._read(ours)
    assert isinstance(lowered.device, DeviceRequests)
    (expected,) = _reference_requests("optical_bb84", ours)
    assert _requests(lowered.device) == _requests(expected)
    assert lowered.specification_provider is not None
    assert lowered.route() == {
        "device": lowered.device,
        "specification_provider": lowered.specification_provider,
    }
    # The source is the qubit instance's hand-built part, through the transmitter.
    preparation = document.preparation(ours)
    assert isinstance(preparation, Preparation)
    assert preparation.specification.source == bb84_qubit_source_part(F(1, 2), F(1, 2))
    del configured


@pytest.mark.parametrize(
    "overrides",
    [overrides for _, overrides in GRID["decoy_bb84"]],
    ids=[label for label, _ in GRID["decoy_bb84"]],
)
def test_the_decoy_source_and_station_lower_to_the_library_objects(
    overrides: dict[str, Any],
) -> None:
    document, ours = _config("decoy_bb84", overrides)
    configured, lowered = document._read(ours)
    values = document.resolve(ours)
    source = wcp_source(
        intensities={
            name: values[f"mu_{name}"]  # type: ignore[misc]
            for name in ("signal", "weak", "vacuum")
        },
        test_intensity_probabilities=[
            values[f"test_{name}"]  # type: ignore[misc]
            for name in ("signal", "weak", "vacuum")
        ],
        gamma=values["gamma"],  # type: ignore[arg-type]
        entropy_cutoff=int(values["entropy_cutoff"]),  # type: ignore[call-overload]
        source_cutoff=int(values["source_cutoff"]),  # type: ignore[call-overload]
        tolerance=configured.declared_tolerance,
    )
    # The WCP preparation record is appended where decoy appends its own.
    assert configured.input_preparation[-1] == source.record
    assert lowered.wcp_source is not None
    assert lowered.wcp_source.tagged == source.tagged
    assert isinstance(lowered.device, DeviceRequests)
    (expected,) = _reference_requests("decoy_bb84", ours)
    assert _requests(lowered.device) == _requests(expected)
    preparation = document.preparation(ours)
    assert isinstance(preparation, Preparation)
    part = preparation.specification.source
    emitted = emit_decoy_declaration(source.tagged).require()
    assert part.artifact == emitted.as_transmitter_artifact()
    assert part.source_links == emitted.source_segment


@pytest.mark.parametrize(
    "overrides",
    [overrides for _, overrides in GRID["bbm92"]],
    ids=[label for label, _ in GRID["bbm92"]],
)
def test_the_two_stations_lower_to_the_library_requests(
    overrides: dict[str, Any],
) -> None:
    document, ours = _config("bbm92", overrides)
    _configured, lowered = document._read(ours)
    expected = _reference_requests("bbm92", ours)
    assert isinstance(lowered.device, MultiDeviceRequests)
    assert [_requests(d) for d in lowered.device.devices] == [
        _requests(d) for d in expected
    ]
    assert lowered.route() == {"device": lowered.device}


def test_a_refused_factor_assembly_is_coded() -> None:
    """The wrapped call site of ``assemble_factor_emissions``.

    Whether the reductions assemble this device is theirs to decide; where they
    refuse, the document refuses with the reductions' own reason in
    ``module_reason`` (not a builtin ``ValueError``: the equivalence gate's
    named difference).
    """
    defaults = dict(template_surface("bbm92").default_config().device)
    overrides = {
        "model": {
            **dict(template_surface("bbm92").default_config().model),
            "mean_pairs": F(1, 20),
        },
        "device": {
            **defaults,
            "source_model": "spdc",
            "route": "licensed",
            "alice_dark_count": {"H": F(1, 10**5), "V": 0, "D": 0, "A": 0},
        },
    }
    document, ours = _config("bbm92", overrides)
    try:
        outcome = document.preparation(ours)
    except DocumentError as refused:
        assert refused.reason is DocumentReason.FACTOR_ASSEMBLY_REFUSED
        assert refused.module_reason
        return
    assert isinstance(outcome, Preparation)


def test_the_expansions_are_recorded_for_every_table() -> None:
    outcome = template_surface("bbm92").preparation(
        template_surface("bbm92").default_config()
    )
    assert outcome.protocol_document is not None
    expansion = outcome.protocol_document["expansion"]
    assert set(expansion) == {
        "alice_station.coarse_graining",
        "bob_station.coarse_graining",
        "alice_station.setting_of",
        "message_m1",
        "message_m2",
        "sifting",
        "key",
        "acceptance",
    }
    coarse = expansion["alice_station.coarse_graining"]
    assert coarse["variables"] == ["pattern"]
    assert coarse["rows"][0] == ["{}", "nc", 0]
    assert ["{H,V}", "mc", 2] in coarse["rows"]
    assert outcome.protocol_document["unmatched"]["message_m2"] == []


# ===========================================================================
#  2. The coverage documents
# ===========================================================================

#: The reasons under which the lowering surfaces a MODULE's refusal.
_WRAPPED = {
    DocumentReason.SOURCE_REFUSED,
    DocumentReason.FACTOR_ASSEMBLY_REFUSED,
    DocumentReason.CHOICE_WEIGHTING_REFUSED,
}


@pytest.mark.parametrize("name", sorted(COVERAGE))
def test_the_engine_decides_every_coverage_document(name: str) -> None:
    """Accepted, or refused by a module -- never an exception of the lowering."""
    surface = coverage_surface(name)
    try:
        outcome = surface.preparation(
            surface.default_config(**copy.deepcopy(COVERAGE_CONFIG.get(name, {})))
        )
    except DocumentError as refusal:
        assert refusal.reason in _WRAPPED, refusal
        assert refusal.module_reason
        return
    except MalformedInputError as failure:
        origin = traceback.extract_tb(failure.__traceback__)[-1].filename
        assert "certiqs_key" in origin and "instances" not in origin, origin
        return
    assert isinstance(outcome, Preparation | SliceRefusal)
    assert outcome.protocol_document is not None
    if isinstance(outcome, SliceRefusal):
        assert outcome.reason


#: What the engine decides of each coverage document today, recorded so that a
#: change is seen.
_DECIDED = {
    "port_grams": Preparation,
    "instrument_matrix": Preparation,
    "catalogue_c3_to_c10": Preparation,
    "dark_count_matrix": Preparation,
    "tau_modes": Preparation,
    "three_stations": Preparation,
    "wcp_two_intensities": Preparation,
    "three_message_transcript": Preparation,
    # Two declared qubit stations on the Band-A route: refused, the route
    # admitting one measured factor (req:band-a-ideal-receiver (i)).
    "two_station_band_a": SliceRefusal,
    "band_a_choice_weighting": Preparation,
    "explicit_carried_operator": SliceRefusal,
    # A document declaring a probe, where the probe-conditioning submodule is.
    **({"generic_probe": Preparation} if PROBE_PRESENT else {}),
}


@pytest.mark.parametrize("name", sorted(_DECIDED))
def test_each_coverage_document_is_decided_as_recorded(name: str) -> None:
    surface = coverage_surface(name)
    outcome = surface.preparation(
        surface.default_config(**copy.deepcopy(COVERAGE_CONFIG.get(name, {})))
    )
    assert isinstance(outcome, _DECIDED[name]), outcome


def test_a_two_station_band_a_document_is_lowered_and_then_refused() -> None:
    """A two-station lowering, and the compiler's refusal of two Band-A factors.

    The document is lowered straight to ``further_receiver_factors``, one
    factor per station. Both stations are declared qubit measurements behind
    the identity link, so the specification is on the Band-A route, which
    admits exactly one measured factor (protocol-compiler/
    req:band-a-ideal-receiver (i)); the compiler refuses it.
    """
    surface = coverage_surface("two_station_band_a")
    config = surface.default_config()
    _configured, lowered = surface._read(config)
    specification = lowered.specification
    assert specification is not None
    assert len(specification.further_receiver_factors) == 1
    assert specification.receiver.factor_label == "alice_station"
    assert specification.further_receiver_factors[0].factor_label == "bob_station"
    outcome = surface.preparation(config)
    assert isinstance(outcome, SliceRefusal)
    assert outcome.stage == "compilation"
    assert outcome.reason == "band_a_outside_ideal_receiver"
    assert "clause (i)" in outcome.detail


def test_the_explicit_carried_operator_is_certified_against_the_first_pass() -> None:
    """``certified_against`` is the artefact's own channel."""
    surface = coverage_surface("explicit_carried_operator")
    config = surface.default_config(**COVERAGE_CONFIG["explicit_carried_operator"])
    _configured, lowered = surface._read(config)
    assert isinstance(lowered.device, DeviceRequests)
    provider = lowered.device.carried_operator_provider
    assert provider is not None
    licensed = template_surface("optical_bb84").preparation(
        template_surface("optical_bb84").default_config(device={"route": "licensed"})
    )
    assert isinstance(licensed, Preparation)
    artifact = licensed.reduction_artifact
    assert artifact is not None
    (request,) = provider(artifact)
    assert request.certified_against == artifact.squashing_channel.identity
    assert request.label == "zero"


def test_the_float_routes_record_their_conversions() -> None:
    surface = coverage_surface("instrument_matrix")
    configured, _lowered = surface._read(surface.default_config())
    records = [
        record
        for record in configured.input_preparation
        if str(record.get("site", "")).startswith("document:/stations/0/measurement")
    ]
    assert records
    assert {record["rule"] for record in records} == {"numeric_input_conversion"}
    assert all(F(record["total_displacement"]) != 0 for record in records)


def test_the_catalogue_scalars_keep_the_written_form() -> None:
    """A JSON integer stays an ``int``; a ``_pi`` field is a pi multiple (1.6)."""
    _configured, lowered = template_surface("optical_bb84")._read(
        template_surface("optical_bb84").default_config()
    )
    assert isinstance(lowered.device, DeviceRequests)
    graph = lowered.device.receiver_request.element_graph
    assert graph is not None
    splitter = graph.element("bs").component
    assert type(splitter.phase) is int and splitter.phase == 0  # type: ignore[attr-defined]
    assert type(splitter.loss_1) is int  # type: ignore[attr-defined]
    assert splitter.transmittance == F(1, 2)  # type: ignore[attr-defined]
    plate = graph.element("hwp").component
    assert plate.angle == PiMultiple(F(1, 8))  # type: ignore[attr-defined]


# ===========================================================================
#  3. What the lowering itself refuses
# ===========================================================================


def _refused(fixture: str, edit: Any) -> DocumentError:
    surface = custom_from(fixture, edit, "refused")
    with pytest.raises(DocumentError) as refused:
        surface.preparation(surface.default_config())
    return refused.value


def test_a_mode_reference_names_a_declared_mode() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["stations"][0]["measurement"]["channel_modes"] = ["Z_H", "Q_V"]

    error = _refused("optical_bb84", edit)
    assert error.reason is DocumentReason.RULE_REFERENCE_UNKNOWN
    assert error.path == "/stations/0/measurement/channel_modes/1"


def test_a_catalogue_entry_declares_every_field() -> None:
    def edit(tree: dict[str, Any]) -> None:
        del tree["stations"][0]["measurement"]["elements"][0]["params"]["loss_2"]

    error = _refused("optical_bb84", edit)
    assert error.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION
    assert error.path == "/stations/0/measurement/elements/0/params/loss_2"


def test_a_photon_number_past_the_bounds_is_refused_before_the_work() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["stations"][0]["measurement"]["photon_cutoff"] = 31

    error = _refused("optical_bb84", edit)
    assert error.reason is DocumentReason.DOCUMENT_TOO_LARGE


@requires_probe
def test_a_probe_block_past_the_bounds_is_refused() -> None:
    def edit(tree: dict[str, Any]) -> None:
        measurement = tree["stations"][0]["measurement"]
        measurement["source_modes"] = ["X_H", "X_V"]
        measurement["probe"] = {
            "settings": [
                {"label": "off", "mean_photons": [0, 0], "class_weight": 1},
            ],
            "tail_window": {"off": 30},
        }

    error = _refused("optical_bb84", edit)
    assert error.reason is DocumentReason.DOCUMENT_TOO_LARGE


@pytest.mark.parametrize(
    "edit",
    [
        lambda tree: tree["source"].update(entropy_cutoff=3),
        lambda tree: tree["source"]["test"]["intensity_probabilities"].pop("weak"),
        lambda tree: tree["source"]["intensities"][1].update(mu="-1/5"),
    ],
    ids=["entropy-cutoff", "missing-test-probability", "negative-intensity"],
)
def test_the_wcp_preparation_s_raises_are_coded(edit: Any) -> None:
    """``prepare_source``'s builtin raises, where called."""
    error = _refused("decoy_bb84", edit)
    assert error.reason is DocumentReason.WCP_SOURCE_INVALID


def test_a_refused_choice_weighting_is_coded() -> None:
    """A weighting that is not stochastic: the compiler's refusal, wrapped."""

    def edit(tree: dict[str, Any]) -> None:
        tree["stations"][0]["choice_weighting"]["matrix"]["off|test"] = "1/4"

    error = _refused("bbm92", edit)
    assert error.reason is DocumentReason.CHOICE_WEIGHTING_REFUSED
    assert error.module_reason == "choice_weight_not_stochastic"


def test_a_channel_interface_that_does_not_describe_the_stations_is_refused() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["channel_interface"] = {"variant": "mode_intensity"}

    error = _refused("optical_bb84", edit)
    assert error.reason is DocumentReason.UNSUPPORTED_TOPOLOGY
    assert error.path == "/channel_interface/variant"


def test_party_local_view_on_one_station_is_refused() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["constraints"] = {"party_local_view": "operator"}

    error = _refused("optical_bb84", edit)
    assert error.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION


def test_explicit_entries_join_the_docked_licence() -> None:
    """One licence record, naming the reductions and the user."""

    def edit(tree: dict[str, Any]) -> None:
        tree["constraints"] = {
            "attack_set_license": {"statement": "My lab's attack set."},
            "feasibility_witness": "auto",
        }

    surface = custom_from("optical_bb84", edit, "joined")
    outcome = surface.preparation(
        surface.default_config(device={"route": "licensed", "dark_count": NOISY})
    )
    assert isinstance(outcome, Preparation)
    licence = outcome.specification.constraints.attack_set_license
    assert licence is not None
    assert licence.supplier.startswith("reductions ")
    assert licence.supplier.endswith("+ user-declared:joined")
    assert licence.statement.endswith("Declared by the user: My lab's attack set.")
    assert outcome.protocol_document is not None
    assert [item["kind"] for item in outcome.protocol_document["user_declared"]] == [
        "attack_set_license"
    ]


def test_an_undocked_station_carries_only_the_user_s_constraints() -> None:
    """``docked: false`` on a licensed route: the reductions' entries stay out."""

    def edit(tree: dict[str, Any]) -> None:
        tree["constraints"] = {"docked": False, "feasibility_witness": "none"}

    surface = custom_from("optical_bb84", edit, "undocked")
    outcome = surface.preparation(
        surface.default_config(device={"route": "licensed", "dark_count": NOISY})
    )
    assert isinstance(outcome, Preparation)
    constraints = outcome.specification.constraints
    assert constraints.entries == ()
    assert constraints.attack_set_license is None
    assert constraints.feasibility_witness is None
    docked = template_surface("optical_bb84").preparation(
        template_surface("optical_bb84").default_config(
            device={"route": "licensed", "dark_count": NOISY}
        )
    )
    assert isinstance(docked, Preparation)
    assert docked.specification.constraints.entries


def test_a_one_message_transcript_leaves_bob_s_default_alphabet_empty() -> None:
    """Bob sends nothing, so his default alphabet is empty.

    The compiler's declaration refuses an empty announcement alphabet by type
    (D(i)): a ``MalformedInputError`` raised inside ``certiqs_key``.
    """

    def edit(tree: dict[str, Any]) -> None:
        tree["public"]["transcript"]["messages"] = tree["public"]["transcript"][
            "messages"
        ][:1]
        tree["public"]["sifting"] = [{"value": "fail"}]
        tree["public"]["acceptance"] = {"map": [{"value": "all"}]}
        tree["honest"] = {
            "acceptance_table": {"all": 1},
            "source": "one value, for the test only",
        }
        tree["channel_interface"] = {"variant": "none"}

    surface = custom_from("decoy_bb84", edit, "one_message")
    _configured, lowered = surface._read(surface.default_config())
    assert lowered.specification is None  # the optical route: a provider
    with pytest.raises(MalformedInputError) as refused:
        surface.preparation(surface.default_config())
    assert "C_B is finite and NON-EMPTY" in str(refused.value)
    origin = traceback.extract_tb(refused.value.__traceback__)[-1].filename
    assert "certiqs_key" in origin and "instances" not in origin


def test_a_declared_announcement_alphabet_is_used_as_written() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["public"]["announcement_alphabets"] = {
            "A": ["gen-Z", "test-signal-H"],
            "B": ["Z", "X"],
        }

    surface = custom_from("decoy_bb84", edit, "alphabets")
    outcome = surface.preparation(surface.default_config())
    assert isinstance(outcome, Preparation | SliceRefusal)
    if isinstance(outcome, SliceRefusal) and outcome.compilation is not None:
        assert outcome.reason


def test_the_transcript_message_ids_are_names_of_their_own() -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["public"]["transcript"]["messages"][1]["id"] = "r"

    with pytest.raises(DocumentError) as refused:
        custom_from("decoy_bb84", edit, "bad_id")
    assert refused.value.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION


def test_the_station_identity_is_carried_on_several_stations_only() -> None:
    _configured, single = template_surface("optical_bb84")._read(
        template_surface("optical_bb84").default_config()
    )
    assert isinstance(single.device, DeviceRequests)
    assert single.device.station is None
    assert single.device.reduction_declaration.party_label is None
    _configured, several = template_surface("bbm92")._read(
        template_surface("bbm92").default_config()
    )
    assert isinstance(several.device, MultiDeviceRequests)
    assert [
        (d.station.factor, d.station.party, d.reduction_declaration.party_label)
        for d in several.device.devices
        if d.station is not None
    ] == [("alice_station", "A", "A"), ("bob_station", "B", "B")]


def test_the_honest_note_is_the_library_model_s() -> None:
    """The note a run records, the library model's, as the instances recorded it.

    bbm92's Python instance laid two extra keys over it, a named difference.
    """
    for name, model in (
        ("optical_bb84", "single_photon_loss_depolarizing"),
        ("decoy_bb84", "coherent_pulses"),
    ):
        document = template_surface(name)
        expected = MODELS[model].note({}, HonestContext(instance=name, stations=()))
        assert expected == document.DEFAULT_HONEST_MODEL_NOTE


def test_a_configuration_refusal_is_the_run_tier_s() -> None:
    """A value outside its domain: the run tier's own refusal, the same code.

    The code is the one the Python instances raised (``outside_domain``).
    """
    from certiqs_key.runs.errors import RunInputReason, RunInputValueError

    for name, device in (
        ("optical_bb84", {"basis_split": F(3, 2)}),
        ("decoy_bb84", {"gamma": F(0)}),
    ):
        document = template_surface(name)
        defaults = dict(document.default_config().device)
        overrides = {"device": {**defaults, **device}}
        with pytest.raises(Exception) as refused:
            document.preparation(document.default_config(**copy.deepcopy(overrides)))
        assert (type(refused.value), getattr(refused.value, "reason", None)) == (
            RunInputValueError,
            RunInputReason.OUTSIDE_DOMAIN,
        ), name


def test_the_document_records_its_identity_strings() -> None:
    """The packaged templates write the instances' strings into the record."""
    configured, lowered = template_surface("decoy_bb84")._read(
        template_surface("decoy_bb84").default_config()
    )
    assert configured.input_preparation[-1]["instance"] == "instances.decoy_bb84.source"
    assert isinstance(lowered.device, DeviceRequests)
    assert lowered.note["instance"] == "decoy_bb84"


# ===========================================================================
#  4. Bounds, bare parameters and refusals
# ===========================================================================


def _station(tree: dict[str, Any]) -> dict[str, Any]:
    measurement: dict[str, Any] = tree["stations"][0]["measurement"]
    return measurement


def _unchanged(tree: dict[str, Any]) -> None:
    del tree


def test_the_instances_defaults_and_presets_are_within_the_work_bound() -> None:
    """A CUSTOM copy of each template is bounded and admits its defaults, presets."""
    for name in ("optical_bb84", "decoy_bb84", "bbm92"):
        document = custom_from(name, _unchanged, f"bounded_{name}")
        assert not document.packaged
        configs = [document.default_config()]
        configs += [
            document.default_config(
                model=dict(document.default_config().model),
                device={**dict(document.default_config().device), **preset.device},
            )
            for preset in document.PRESETS
        ]
        for config in configs:
            document._read(config)


@pytest.mark.parametrize(
    ("device", "what"),
    [
        ({"photon_cutoff": 8, "exact_window": 9}, "the photon cutoff"),
        ({"photon_cutoff": 1, "exact_window": 10}, "the receiver's work"),
        ({"photon_cutoff": 7, "exact_window": 8}, None),
        ({"photon_cutoff": 1, "exact_window": 9}, None),
    ],
    ids=["cutoff-8", "window-10", "cutoff-7-admitted", "window-9-admitted"],
)
def test_the_work_bound_admits_and_refuses_as_measured(
    device: dict[str, Any], what: str | None
) -> None:
    """Design limits: cutoff 7, and 3^K sum dim^2 <= 40,000."""
    document = custom_from("optical_bb84", _unchanged, "bounded")
    config = document.default_config(device=device)
    if what is None:
        document._read(config)
        return
    with pytest.raises(DocumentError) as refused:
        document._read(config)
    assert refused.value.reason is DocumentReason.DOCUMENT_TOO_LARGE
    assert what in refused.value.detail


@pytest.mark.parametrize(
    ("name", "device"),
    [
        ("optical_bb84", {"photon_cutoff": 8, "exact_window": 9}),
        ("optical_bb84", {"photon_cutoff": 16, "exact_window": 17}),
        ("optical_bb84", {"photon_cutoff": 1, "exact_window": 17}),
        ("decoy_bb84", {"photon_cutoff": 1, "exact_window": 30}),
        ("bbm92", {"alice_photon_cutoff": 8, "alice_exact_window": 9}),
    ],
    ids=[
        "optical-cutoff-8",
        "optical-cutoff-16",
        "optical-window-17",
        "decoy-window-30",
        "bbm92-cutoff-8",
    ],
)
def test_a_packaged_template_is_bounded_by_its_own_domains(
    name: str, device: dict[str, Any]
) -> None:
    """The work bound applies to custom documents only.

    A packaged template admits every value its parameter table admits, as its
    Python instance did, and lowers there to the library's own requests
    (optical; cheap, nothing is solved); a custom copy of it is refused
    ``document_too_large`` at the same values, before any work starts.
    """
    packaged = template_surface(name)
    overrides = {
        "model": dict(packaged.default_config().model),
        "device": {**dict(packaged.default_config().device), **device},
    }
    config = packaged.default_config(**copy.deepcopy(overrides))
    configured, lowered = packaged._read(config)
    if name == "optical_bb84":
        assert isinstance(lowered.device, DeviceRequests)
        (expected,) = _reference_requests(name, config)
        assert _requests(lowered.device) == _requests(expected)
    del configured
    custom = custom_from(name, _unchanged, f"bounded_{name}")
    with pytest.raises(DocumentError) as refused:
        custom._read(custom.default_config(**copy.deepcopy(overrides)))
    assert refused.value.reason is DocumentReason.DOCUMENT_TOO_LARGE


def _ports(count: int, window: int) -> Any:
    def edit(tree: dict[str, Any]) -> None:
        labels = [f"P{i}" for i in range(count)]
        measurement = _station(tree)
        measurement["modes"] = [
            {"path": "Z", "polarization": "H"},
            {"path": "Z", "polarization": "V"},
            *({"path": f"p{i:02d}", "polarization": "H"} for i in range(count)),
        ]
        measurement["route"] = "port_grams"
        measurement["elements"] = []
        measurement["edges"] = []
        measurement["port_grams"] = {
            label: {
                "matrix": [[f"2/{count}", 0], [0, 0]]
                if i % 2 == 0
                else [[0, 0], [0, f"2/{count}"]]
            }
            for i, label in enumerate(labels)
        }
        measurement["ports"] = [
            {"label": label, "modes": [f"p{i:02d}_H"]} for i, label in enumerate(labels)
        ]
        measurement["detectors"] = [
            {"port": label, "efficiency": 1, "dark_count": 0} for label in labels
        ]
        measurement["coarse_graining"] = {
            "letters": [
                {"label": "nc"},
                *(
                    {"label": label, "class": "Z" if i % 4 < 2 else "X", "bit": i % 2}
                    for i, label in enumerate(labels)
                ),
                {"label": "mc"},
            ],
            "map": [
                {"when": {"count": "0"}, "value": "nc"},
                {"when": {"count": "1"}, "value": "{port}"},
                {"value": "mc"},
            ],
        }
        measurement["photon_cutoff"] = 1
        measurement["exact_window"] = window

    return edit


@pytest.mark.parametrize(
    ("count", "window", "refused"),
    [(9, 2, True), (8, 2, True), (8, 1, False), (6, 3, False), (6, 4, True)],
)
def test_the_port_count_and_the_work_bound(
    count: int, window: int, refused: bool
) -> None:
    surface = custom_from("optical_bb84", _ports(count, window), "ports")
    config = surface.default_config()
    if not refused:
        surface._read(config)
        return
    with pytest.raises(DocumentError) as error:
        surface._read(config)
    assert error.value.reason is DocumentReason.DOCUMENT_TOO_LARGE


@pytest.mark.parametrize(
    "edit",
    [
        lambda tree: tree["source"].update(lattice_exponent=0),
        lambda tree: tree["source"].update(lattice_exponent=54),
        lambda tree: tree["snap"].update(lattice_exponent=0),
        lambda tree: tree["stations"][0]["reduction"]["cases"]["encoded"].update(
            lattice_exponent=0
        ),
    ],
    ids=["wcp-0", "wcp-54", "snap-0", "reduction-0"],
)
def test_every_lattice_exponent_is_bounded_by_the_schema(edit: Any) -> None:
    """1 <= k <= 53, refused at load, before any snap runs."""
    with pytest.raises(DocumentError) as refused:
        custom_from("decoy_bb84", edit, "lattice")
    assert refused.value.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION


def test_an_absent_window_parameter_is_no_window_and_is_recorded() -> None:
    """A bare ``{param}`` the configuration lacks; recorded."""
    document = template_surface("optical_bb84")
    outcome = document.preparation(document.default_config(device={"route": "encoded"}))
    assert isinstance(outcome, Preparation)
    assert outcome.protocol_document is not None
    assert outcome.protocol_document["absent"] == [
        {
            "path": "/stations/0/measurement/exact_window",
            "parameter": "exact_window",
            "read_as": "no exact window",
        }
    ]
    assert outcome.receiver_artifact is not None
    defaults = document.preparation(document.default_config())
    assert defaults.protocol_document is not None
    assert defaults.protocol_document["absent"] == []


def test_a_window_expression_over_an_absent_parameter_is_refused() -> None:
    """Only a bare ``{param}`` may be absent; an expression is not."""

    def edit(tree: dict[str, Any]) -> None:
        _station(tree)["exact_window"] = {"expr": "exact_window + 1"}

    surface = custom_from("optical_bb84", edit, "window_expr")
    with pytest.raises(DocumentError) as refused:
        surface.preparation(surface.default_config(device={"route": "encoded"}))
    assert refused.value.reason is DocumentReason.UNKNOWN_PARAMETER_REFERENCE
    assert refused.value.path == "/stations/0/measurement/exact_window"


def test_the_accepted_receiver_versions_are_not_a_document_s_to_widen() -> None:
    """Assumption A-RECV stays fixed."""

    def edit(tree: dict[str, Any]) -> None:
        tree["stations"][0]["reduction"]["cases"]["encoded"][
            "accepted_receiver_versions"
        ] = ["receiver@0.9.0", "receiver@9.9.9"]

    error = _refused("optical_bb84", edit)
    assert error.reason is DocumentReason.DOCUMENT_SCHEMA_VIOLATION
    assert error.path.endswith("/accepted_receiver_versions")


@pytest.mark.parametrize(
    ("name", "what"),
    [
        ("port_grams", "port Grams"),
        ("instrument_matrix", "an instrument matrix"),
        ("catalogue_c3_to_c10", "the generic block (C10) 'block'"),
        ("dark_count_matrix", "a dark-count channel"),
    ],
)
def test_a_declared_characterisation_is_flagged_under_a_trust(
    name: str, what: str
) -> None:
    """One item per such station."""
    surface = coverage_surface(name)
    outcome = surface.preparation(surface.default_config())
    assert outcome.protocol_document is not None
    items = [
        item
        for item in outcome.protocol_document["user_declared"]
        if item["kind"] == "receiver_characterisation"
    ]
    assert len(items) == 1
    (item,) = items
    assert item["assumptions"] == ["A-TRUST"]
    assert item["path"] == "/stations/0/measurement"
    assert what in item["text"]
    assert "exactly your device's" in item["text"]


def test_catalogue_optics_are_not_a_declared_characterisation() -> None:
    """A template's catalogue optics are derived physics, never flagged A-TRUST."""
    for name in ("optical_bb84", "decoy_bb84", "bbm92"):
        document = template_surface(name)
        outcome = document.preparation(document.default_config())
        assert outcome.protocol_document is not None
        kinds = {item["kind"] for item in outcome.protocol_document["user_declared"]}
        assert "receiver_characterisation" not in kinds, name


#: What each packaged template declares itself at its defaults: bb84's Band-A
#: POVM and decoy_bb84's retention attestation. Whoever runs a shipped
#: template vouches for them as for a custom document's (the user still takes
#: responsibility for these if using the key rates).
PACKAGED_DECLARES: dict[str, list[tuple[str, list[str]]]] = {
    "bb84": [("receiver_povm", ["A-SPEC", "A-IDEAL"])],
    "optical_bb84": [],
    "decoy_bb84": [("retention_attestation", ["A-SRC"])],
    "bbm92": [],
}


@pytest.mark.parametrize("name", sorted(PACKAGED_DECLARES))
def test_a_packaged_template_records_what_it_declares(name: str) -> None:
    """The record carries every item the lowering flagged, packaged or not."""
    from tests.support.declared_equivalence import config_grid, copied

    document = template_surface(name)
    assert document.packaged
    outcome = document.preparation(document.default_config())
    assert outcome.protocol_document is not None
    items = outcome.protocol_document["user_declared"]
    assert [(item["kind"], item["assumptions"]) for item in items] == (
        PACKAGED_DECLARES[name]
    )
    for item in items:
        assert "Declared in the run's protocol document" in item["text"]
    lowered_points = 0
    for label, overrides in config_grid(document):
        try:
            config = document.default_config(**copied(copy.deepcopy(overrides)))
            _configured, lowered = document._read(config)
        except Exception:
            continue
        lowered_points += 1
        record = lowered.record(
            document_id=name,
            packaged=True,
            digest=document.digest,
            canonical=document.canonical,
            conversions=document.conversions,
        )
        assert record["user_declared"] == [
            item.as_record() for item in lowered.user_declared
        ], label
    assert lowered_points


def test_the_factor_projection_readouts_are_bounded() -> None:
    """X x V of the factor projection, before it is built."""
    letters = [f"x{i}" for i in range(256)]
    share = "1/256"

    def edit(tree: dict[str, Any]) -> None:
        tree["source"] = {
            "kind": "untrusted",
            "alphabet": {"enum": letters},
            "transmitted_dim": 1,
            "weights": dict.fromkeys(letters, share),
            "states": {letter: {"identity": 1} for letter in letters},
            "alice_dim": 1,
            "alice_povm": {
                letter: {"scale": {"factor": share, "of": {"identity": 1}}}
                for letter in letters
            },
        }

    error = _refused("bbm92", edit)
    assert error.reason is DocumentReason.DOCUMENT_TOO_LARGE
    assert error.path == "/public/partition"


@pytest.mark.parametrize(
    ("template", "reason"),
    [
        ("{round}-{intensity}", DocumentReason.DOCUMENT_SCHEMA_VIOLATION),
        ("{intensity}-{polarisation}", DocumentReason.DOCUMENT_SCHEMA_VIOLATION),
        ("{round}-{oops}-{polarisation}", DocumentReason.RULE_REFERENCE_UNKNOWN),
    ],
)
def test_a_letter_label_that_cannot_name_its_letters_is_refused_at_load(
    template: str, reason: DocumentReason
) -> None:
    def edit(tree: dict[str, Any]) -> None:
        tree["source"]["letter_label"] = template

    with pytest.raises(DocumentError) as refused:
        custom_from("decoy_bb84", edit, "letters")
    assert refused.value.reason is reason
    assert refused.value.path == "/source/letter_label"


# -- refusal parity  -------------------------------------------


def _decision(surface: Any, overrides: dict[str, Any]) -> tuple[str, str]:
    """Return how a surface decides a configuration: its outcome or its refusal."""
    try:
        outcome = surface.preparation(
            surface.default_config(**copy.deepcopy(overrides))
        )
    except Exception as failure:
        return (type(failure).__name__, str(getattr(failure, "reason", "")))
    if isinstance(outcome, SliceRefusal):
        return ("SliceRefusal", f"{outcome.stage}:{outcome.reason}")
    return ("Preparation", "")


#: How the Python instances decided each configuration below: the exception type and
#: code, or the refusing stage and reason. The decoy entropy cutoff was a builtin
#: ``ValueError`` from ``prepare_source``, which the document codes
#: ``wcp_source_invalid``.
_PYTHON_DECISIONS = {
    "optical-domain": ("RunInputValueError", "outside_domain"),
    "optical-model-domain": ("RunInputValueError", "outside_domain"),
    "optical-receiver": (
        "SliceRefusal",
        "receiver_construction:graph_condition_e1_failed",
    ),
    "optical-per-port": ("RunInputKeyError", "port_labels_mismatch"),
    "decoy-domain": ("RunInputValueError", "outside_domain"),
    "decoy-normalization": ("RunInputValueError", "normalization_exceeds_tolerance"),
    "decoy-entropy-cutoff": ("ValueError", ""),
    "bbm92-domain": ("RunInputValueError", "outside_domain"),
    "bbm92-choice": ("RunInputValueError", "outside_domain"),
}


@pytest.mark.parametrize(
    ("label", "name", "overrides"),
    [
        ("optical-domain", "optical_bb84", {"device": {"basis_split": F(3, 2)}}),
        ("optical-model-domain", "optical_bb84", {"model": {"qber": F(1, 2)}}),
        ("optical-receiver", "optical_bb84", {"device": {"half_wave_angle": F(1)}}),
        (
            "optical-per-port",
            "optical_bb84",
            {"device": {"dark_count": {"H": F(1, 2)}}},
        ),
        ("decoy-domain", "decoy_bb84", {"device": {"gamma": F(0)}}),
        (
            "decoy-normalization",
            "decoy_bb84",
            {"device": {"test_signal": F(1, 2), "test_weak": F(1, 2)}},
        ),
        (
            "decoy-entropy-cutoff",
            "decoy_bb84",
            {"device": {"entropy_cutoff": 2, "source_cutoff": 1}},
        ),
        ("bbm92-domain", "bbm92", {"device": {"test_fraction": F(1)}}),
        ("bbm92-choice", "bbm92", {"device": {"key_bases": "XZ"}}),
    ],
)
def test_a_refusal_is_the_python_instance_s(
    label: str, name: str, overrides: dict[str, Any]
) -> None:
    """The same configuration is refused alike: type and code, or stage and reason.

    For optical and bbm92 a caller's section replaces the base, so the base
    device is laid under each edit; decoy merges.
    """
    if name != "decoy_bb84":
        base = template_surface(name).default_config()
        overrides = {
            "model": {**dict(base.model), **overrides.get("model", {})},
            "device": {**dict(base.device), **overrides.get("device", {})},
        }
    ours = _decision(template_surface(name), overrides)
    theirs = _PYTHON_DECISIONS[label]
    if ours[0] == "DocumentError":
        # The decoy entropy cutoff: prepare_source's builtin ValueError is the
        # document's wcp_source_invalid.
        assert theirs[0] == "ValueError" and ours[1] == "wcp_source_invalid"
        return
    assert ours != ("Preparation", ""), ours
    assert ours == theirs


# -- hostile documents  ----------------------------------------


def _m(tree: dict[str, Any], index: int = 0) -> dict[str, Any]:
    measurement: dict[str, Any] = tree["stations"][index]["measurement"]
    return measurement


def _encoded(tree: dict[str, Any]) -> dict[str, Any]:
    case: dict[str, Any] = tree["stations"][0]["reduction"]["cases"]["encoded"]
    return case


def _window_expression(tree: dict[str, Any]) -> None:
    """Write the window as an expression, with no derived default to fill it."""
    _m(tree).update(exact_window={"expr": "exact_window + 1"})
    tree["run_defaults"].pop("derived")
    tree["run_defaults"].pop("derived_timing")


def _element(name: str, component: str, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "component": component,
        "support": ["Zr_H", "Zr_V"],
        "params": params,
    }


#: Hostile edits: (fixture, id, edit, expected). The expectation is a coded
#: ``DocumentError`` (``doc:<reason>``), a module's refusal as data
#: (``refused:<stage>:<reason>``), a ``MalformedInputError`` raised inside
#: ``certiqs_key`` (``malformed``), or a preparation. Never a builtin.
HOSTILE: list[tuple[str, str, Any, str]] = [
    (
        "optical_bb84",
        "cutoff-negative",
        lambda t: _m(t).update(photon_cutoff=-1),
        "doc:library_model_binding_invalid",
    ),
    (
        "optical_bb84",
        "cutoff-past-bound",
        lambda t: _m(t).update(photon_cutoff=8),
        "doc:document_too_large",
    ),
    (
        "optical_bb84",
        "window-expression-absent",
        _window_expression,
        "doc:unknown_parameter_reference",
    ),
    (
        "optical_bb84",
        "no-ports",
        lambda t: _m(t).update(ports=[], detectors=[]),
        "doc:station_reference_unknown",
    ),
    ("optical_bb84", "ports-past-bound", _ports(9, 2), "doc:document_too_large"),
    (
        "optical_bb84",
        "detector-unknown-port",
        lambda t: _m(t)["detectors"][0].update(port="Q"),
        "refused:receiver_construction:port_map_malformed",
    ),
    (
        "optical_bb84",
        "fewer-detectors",
        lambda t: _m(t)["detectors"].pop(),
        "refused:receiver_construction:port_map_malformed",
    ),
    (
        "optical_bb84",
        "support-short",
        lambda t: _m(t)["elements"][0].update(support=["Z_H", "Z_V"]),
        "refused:receiver_construction:graph_condition_e1_failed",
    ),
    (
        "optical_bb84",
        "edge-unknown",
        lambda t: _m(t)["edges"].append(["bs", "x"]),
        "refused:receiver_construction:graph_condition_e1_failed",
    ),
    (
        "optical_bb84",
        "edge-cycle",
        lambda t: _m(t)["edges"].append(["pbs_x", "bs"]),
        "refused:receiver_construction:graph_condition_e2_failed",
    ),
    (
        "optical_bb84",
        "mode-unknown",
        lambda t: _m(t).update(channel_modes=["Z_H", "Q_V"]),
        "doc:rule_reference_unknown",
    ),
    (
        "optical_bb84",
        "field-missing",
        lambda t: _m(t)["elements"][0]["params"].pop("loss_2"),
        "doc:document_schema_violation",
    ),
    (
        "optical_bb84",
        "grams-3x3",
        lambda t: (port_grams(t), _m(t)["port_grams"].update(H={"identity": 3})),
        "doc:matrix_malformed",
    ),
    (
        "optical_bb84",
        "grams-missing-port",
        lambda t: (port_grams(t), _m(t)["port_grams"].pop("A")),
        "refused:receiver_construction:port_grams_not_admissible",
    ),
    (
        "optical_bb84",
        "two-routes",
        lambda t: (port_grams(t), _m(t).update(route="element_graph")),
        "refused:receiver_construction:input_routes_not_exactly_one",
    ),
    (
        "optical_bb84",
        "instrument-2x2",
        lambda t: (
            instrument_matrix(t),
            _m(t).update(instrument_matrix={"identity": 2}),
        ),
        "refused:receiver_construction:instrument_matrix_not_contraction",
    ),
    (
        "optical_bb84",
        "dark-wrong-size",
        lambda t: _m(t).update(dark_count_channel={"identity": 4}),
        "doc:matrix_malformed",
    ),
    (
        "optical_bb84",
        "dark-twice",
        lambda t: (
            _m(t).update(dark_count_channel={"identity": 16}),
            _m(t)["detectors"][0].update(dark_count="1/10"),
        ),
        "refused:receiver_construction:dark_count_channel_declared_twice",
    ),
    (
        "optical_bb84",
        "probe-weights-bad",
        lambda t: _m(t).update(
            source_modes=["X_H", "X_V"],
            probe={
                "settings": [
                    {"label": "off", "mean_photons": [0, 0], "class_weight": "1/2"}
                ]
            },
        ),
        "refused:reduction:probe_weights_ill_formed",
    ),
    (
        "optical_bb84",
        "probe-past-bound",
        lambda t: _m(t).update(
            source_modes=["X_H", "X_V"],
            probe={
                "settings": [
                    {"label": "off", "mean_photons": [0, 0], "class_weight": 1}
                ],
                "tail_window": {"off": 30},
            },
        ),
        "doc:document_too_large",
    ),
    (
        "optical_bb84",
        "tolerances-missing",
        lambda t: _m(t).update(tolerances={"eps_1": "1e-3"}),
        "refused:receiver_construction:numerical_tolerance_missing",
    ),
    (
        "optical_bb84",
        "tolerances-negative",
        lambda t: _m(t).update(
            tolerances=dict.fromkeys(
                ("eps_1", "eps_2", "eps_3", "eps_4", "eps_5", "eps_gap"), "-1"
            )
        ),
        "refused:receiver_construction:tolerance_outside_declared_domain",
    ),
    (
        "optical_bb84",
        "coarse-not-total",
        lambda t: _m(t)["coarse_graining"].update(
            map=[{"when": {"count": "0"}, "value": "nc"}]
        ),
        "refused:receiver_construction:coarse_graining_not_total",
    ),
    (
        "optical_bb84",
        "coarse-unknown-letter",
        lambda t: _m(t)["coarse_graining"].update(map=[{"value": "zz"}]),
        "refused:receiver_construction:coarse_graining_not_total",
    ),
    (
        "optical_bb84",
        "tau-mixed",
        lambda t: _m(t)["modes"][0].update(tau=1),
        "refused:receiver_construction:mode_space_tau_not_single_valued",
    ),
    (
        "optical_bb84",
        "links-deferred",
        lambda t: _encoded(t).update(links=[{"kind": "pinching"}]),
        "refused:reduction:chain_ill_formed",
    ),
    (
        "optical_bb84",
        "links-empty",
        lambda t: _encoded(t).update(links=[]),
        "refused:reduction:chain_ill_formed",
    ),
    (
        "optical_bb84",
        "route-both",
        lambda t: _encoded(t).update(route="both"),
        "doc:document_schema_violation",
    ),
    (
        "optical_bb84",
        "lattice-0",
        lambda t: _encoded(t).update(lattice_exponent=0),
        "doc:document_schema_violation",
    ),
    (
        "optical_bb84",
        "versions-widened",
        lambda t: _encoded(t).update(accepted_receiver_versions=[]),
        "doc:document_schema_violation",
    ),
    (
        "optical_bb84",
        "c10-nonsquare",
        lambda t: _m(t)["elements"].append(
            _element(
                "g", "generic_block", {"block": {"matrix": [[1, 0, 0], [0, 1, 0]]}}
            )
        ),
        "doc:matrix_malformed",
    ),
    (
        "optical_bb84",
        "c10-not-contraction",
        lambda t: _m(t)["elements"].append(
            _element("g", "generic_block", {"block": {"matrix": [[2, 0], [0, 2]]}})
        ),
        "refused:receiver_construction:graph_condition_e1_failed",
    ),
    (
        "optical_bb84",
        "splitter-out-of-domain",
        lambda t: _m(t)["elements"][0]["params"].update(transmittance="3/2"),
        "refused:receiver_construction:graph_condition_e1_failed",
    ),
    (
        "optical_bb84",
        "routing-not-a-permutation",
        lambda t: _m(t)["elements"].append(
            _element("r", "mode_routing", {"permutation": [0, 0]})
        ),
        "refused:receiver_construction:graph_condition_e1_failed",
    ),
    (
        "optical_bb84",
        "phases-wrong-length",
        lambda t: _m(t)["elements"].append(
            _element("p", "phase_shifter", {"phases_pi": [0]})
        ),
        "refused:receiver_construction:graph_condition_e1_failed",
    ),
    (
        "optical_bb84",
        "honest-model-mismatch",
        lambda t: t.update(
            honest={
                "library": "coherent_pulses",
                "bind": {"transmittance": 1, "misalignment": 0},
            }
        ),
        "doc:library_model_binding_invalid",
    ),
    (
        "optical_bb84",
        "witness-wrong-shape",
        lambda t: t.update(
            constraints={"feasibility_witness": {"blocks": [{"identity": 2}]}}
        ),
        "malformed",
    ),
    (
        "optical_bb84",
        "entry-unknown-sector",
        lambda t: t.update(
            constraints={
                "entries": [
                    {
                        "label": "e",
                        "operator": {"blocks": {"s9": {"identity": 1}}},
                        "relation": "ge",
                        "rhs": 0,
                    }
                ],
                "attack_set_license": {"statement": "x"},
            }
        ),
        "doc:document_schema_violation",
    ),
    (
        "decoy_bb84",
        "flag-family-split",
        lambda t: t["source"].update(flag_family="split_by_intensity"),
        "doc:source_refused",
    ),
    (
        "decoy_bb84",
        "intensity-unknown",
        lambda t: t["source"]["generation"].update(intensity="nowhere"),
        "malformed",
    ),
    # Two labels for one vector of D: transmitter/decoy/req:signal-dyads makes
    # distinctness a condition of a quantum sector above the vacuum, so the
    # emission refuses it (quantum_sector_outside_construction) at the
    # template's N_ent >= 1, which the declared surface reports as a source
    # refusal.
    (
        "decoy_bb84",
        "polarisation-part-twice",
        lambda t: t["source"]["polarisations"][1].update(part="H"),
        "doc:source_refused",
    ),
    (
        "decoy_bb84",
        "letter-label-collision",
        lambda t: t["source"].update(letter_label="{round}-{polarisation}"),
        "malformed",
    ),
    (
        "decoy_bb84",
        "intensity-past-bound",
        lambda t: t["source"]["intensities"][0].update(mu=11),
        "doc:document_too_large",
    ),
    (
        "decoy_bb84",
        "lattice-0",
        lambda t: t["source"].update(lattice_exponent=0),
        "doc:document_schema_violation",
    ),
    (
        "decoy_bb84",
        "entropy-cutoff-3",
        lambda t: t["source"].update(entropy_cutoff=3),
        "doc:wcp_source_invalid",
    ),
    (
        "decoy_bb84",
        "derived-alphabet-empty",
        lambda t: t["public"]["transcript"]["messages"][0].update(
            table=[{"when": {"r.round": "nope"}, "value": "x"}]
        ),
        "malformed",
    ),
    (
        "decoy_bb84",
        "channel-bipartite",
        lambda t: t.update(channel_interface={"variant": "bipartite"}),
        "doc:unsupported_topology",
    ),
    (
        "bbm92",
        "weighting-not-stochastic",
        lambda t: t["stations"][0]["choice_weighting"]["matrix"].update(
            {"off|test": "1/4"}
        ),
        "doc:choice_weighting_refused",
    ),
    (
        "bbm92",
        "weighting-key-bad",
        lambda t: t["stations"][0]["choice_weighting"]["matrix"].update({"x|y": 1}),
        "doc:document_schema_violation",
    ),
    (
        "bbm92",
        "source-povm-incomplete",
        lambda t: t["source"].update(
            alphabet={"enum": ["x0", "x1"]},
            weights={"x0": "1/2", "x1": "1/2"},
            states={"x0": {"identity": 1}, "x1": {"identity": 1}},
            alice_povm={"x0": {"identity": 1}, "x1": {"identity": 1}},
        ),
        "doc:source_refused",
    ),
    (
        "bbm92",
        "channel-single-photon",
        lambda t: t.update(channel_interface={"variant": "single_photon"}),
        "doc:unsupported_topology",
    ),
    (
        "bbm92",
        "pair-model-one-station",
        lambda t: t.update(
            honest={
                "library": "ideal_pair",
                "station": "bob_station",
                "bind": {
                    "alice_transmittance": 1,
                    "bob_transmittance": 1,
                    "visibility": 1,
                },
            }
        ),
        "doc:library_model_binding_invalid",
    ),
]


def _hostile_outcome(fixture: str, edit: Any) -> str:
    try:
        surface = custom_from(fixture, edit, "hostile")
        outcome = surface.preparation(surface.default_config())
    except DocumentError as refusal:
        return f"doc:{refusal.reason}"
    except MalformedInputError as failure:
        origin = traceback.extract_tb(failure.__traceback__)[-1].filename
        assert "certiqs_key" in origin and "instances" not in origin, origin
        return "malformed"
    if isinstance(outcome, SliceRefusal):
        return f"refused:{outcome.stage}:{outcome.reason}"
    return "prepared"


#: The hostile documents that declare a probe need the probe-conditioning
#: submodule, whose document field goes with it.
_HOSTILE_HERE = [
    row for row in HOSTILE if PROBE_PRESENT or not row[1].startswith("probe-")
]


@pytest.mark.parametrize(
    ("fixture", "edit", "expected"),
    [(fixture, edit, expected) for fixture, _, edit, expected in _HOSTILE_HERE],
    ids=[f"{fixture}-{name}" for fixture, name, _, _ in _HOSTILE_HERE],
)
def test_a_hostile_document_is_decided_with_a_code(
    fixture: str, edit: Any, expected: str
) -> None:
    """Never a builtin: a coded refusal, a module refusal, or a module type error."""
    assert _hostile_outcome(fixture, edit) == expected


def test_the_run_s_snap_settings_reach_every_station() -> None:
    """The snap run parameters reach snap and reduction.

    The instances hand ``snap_settings(config)`` to their rows adapter and
    their reduction request (``passive_device_requests``); the lowering does
    the same, from the same configuration fields
    (``foundations/req:snap-reference`` (i), (iv)).
    """
    overrides = {"reference_enclosure": False, "strict_snaps": True}
    document = template_surface("optical_bb84")
    config = document.default_config(**overrides)
    _configured, lowered = document._read(config)
    assert isinstance(lowered.device, DeviceRequests)
    request = lowered.device.reduction_request
    assert request.reference_enclosure is False
    assert request.strict_snaps is True
    (expected,) = _reference_requests("optical_bb84", config)
    assert _requests(lowered.device) == _requests(expected)
    _configured, several = template_surface("bbm92")._read(
        template_surface("bbm92").default_config(**overrides)
    )
    assert isinstance(several.device, MultiDeviceRequests)
    assert {
        device.reduction_request.strict_snaps
        for device in several.device.devices
    } == {True}
