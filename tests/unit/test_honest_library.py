"""The honest-model library: its interface, its refusals and its letter maps.

WHY THIS EXISTS. The five instances' honest models are in
``instances/common/honest`` so that a protocol document can name them. A document is not
the instance whose structure a model was written for, so the library has to (a) refuse a
binding that is not exactly the model's parameters, (b) refuse a structure the model
does not model -- its preconditions -- and (c) read each letter by what it IS, never by
its position. This file holds those three, holds every instance's own context against
its model's preconditions, and holds the attribute maps against the positional zips the
decoy and bbm92 instances make, so that on their structures no number moves.

An instance's context is the one its template's lowering tells the model
(``Lowered.honest_context``).
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F
from itertools import product
from typing import Any

import pytest
from instances.bb84 import surface as bb84_surface
from instances.bbm92 import surface as bbm92_surface
from instances.common.honest import (
    MODELS,
    HonestContext,
    SourceFacts,
    StationFacts,
    build,
)
from instances.common.honest.coherent_pulses import (
    click_distribution,
    raw_distribution,
)
from instances.common.honest.interface import (
    MULTI,
    NONE,
    letter_classes,
    outcome_components,
)
from instances.common.optics import PORTS, RAW_LETTERS
from instances.declared.errors import DocumentError, DocumentReason
from instances.decoy_bb84 import surface as decoy_surface
from instances.optical_bb84 import surface as optical_surface
from tests.support.declared_optical_documents import template_tree
from tests.support.lowered_templates import lowered

from certiqs_key.receiver.coarse import CoarseGraining
from certiqs_key.receiver.modes import InputModes

#: The position the decoy and bbm92 instances read a letter by.
POSITIONAL = ("nc", "H", "V", "D", "A", "mc")


# ---------------------------------------------------------------------------
#  The instances' own contexts
# ---------------------------------------------------------------------------


def _context(instance: str, config: Any = None) -> HonestContext:
    """Return the context the instance's template tells its library model."""
    context = lowered(instance, config)[1].honest_context
    assert context is not None
    return context


def _bb84_context() -> HonestContext:
    return _context("bb84")


def _optical_context(**device: Any) -> HonestContext:
    config = optical_surface.default_config()
    if device:
        config = replace(config, device={**config.device, **device})
    return _context("optical_bb84", config)


@pytest.fixture(scope="module")
def decoy() -> tuple[HonestContext, Any]:
    """Return the decoy instance's context and its prepared declaration."""
    config = decoy_surface.default_config()
    return _context("decoy_bb84", config), decoy_surface.preparation(config)


def _bbm92_context(source_model: str) -> tuple[HonestContext, Any]:
    config = bbm92_surface.default_config()
    config = replace(config, device={**config.device, "source_model": source_model})
    return _context("bbm92", config), config


#: bbm92's source models and the library model each names: the template's
#: ``honest`` switch.
LIBRARY_MODEL = {
    case: block["library"]
    for case, block in template_tree("bbm92")["honest"]["cases"].items()
}


@pytest.fixture(scope="module")
def bbm92() -> tuple[HonestContext, Any]:
    """Return the bbm92 instance's context (SPDC) and its prepared declaration."""
    context, config = _bbm92_context("spdc")
    return context, bbm92_surface.preparation(config)


# ---------------------------------------------------------------------------
#  The interface and the registry
# ---------------------------------------------------------------------------


def test_every_model_has_the_uniform_interface() -> None:
    assert list(MODELS) == [
        "depolarized_bell_pair",
        "single_photon_loss_depolarizing",
        "coherent_pulses",
        "ideal_pair",
        "spdc_pair",
    ]
    for name, model in MODELS.items():
        assert model.name == name
        assert model.parameters and all(isinstance(p, str) for p in model.parameters)
        assert len(set(model.parameters)) == len(model.parameters)
        for method in ("note", "preconditions", "providers"):
            assert callable(getattr(model, method)), (name, method)


def test_models_cover_every_document_instance() -> None:
    """bb84, optical, decoy and bbm92 (both source models) run library models.

    An instance written in Python with its own model is excluded from the
    document's coverage and is not asked for here.
    """
    modules = {type(model).__module__: name for name, model in MODELS.items()}
    for surface, expected in (
        (bb84_surface, "depolarized_bell_pair"),
        (optical_surface, "single_photon_loss_depolarizing"),
        (decoy_surface, "coherent_pulses"),
    ):
        assert modules[surface.DEFAULT_HONEST_MODEL_NOTE["module"]] == expected
    choices = next(
        spec for spec in bbm92_surface.PARAMETERS if spec.name == "source_model"
    ).domain
    assert set(LIBRARY_MODEL) == {name for name, _ in choices.options}
    assert set(LIBRARY_MODEL.values()) <= set(MODELS)


def test_the_notes_keep_each_instances_keys() -> None:
    assert bb84_surface.DEFAULT_HONEST_MODEL_NOTE == {
        "instance": "bb84",
        "model": (
            "depolarizing qubit channel, evaluated exactly on the emitted declaration"
        ),
        "module": "instances.common.honest.depolarized_bell_pair",
        "overridden": False,
    }
    for surface in (optical_surface, decoy_surface):
        note = surface.DEFAULT_HONEST_MODEL_NOTE
        assert set(note) == {"instance", "model", "module", "overridden"}
        assert note["instance"] == surface.DESCRIPTOR.id
    context, _ = _bbm92_context("ideal_pair")
    for name, model in (("ideal_pair", "ideal_pair"), ("spdc_pair", "spdc")):
        note = MODELS[name].note({}, context)
        assert note["model"] == model
        assert set(note) == {"model", "source_trusted", "model_derivation", "status"}


# ---------------------------------------------------------------------------
#  Binding refusals
# ---------------------------------------------------------------------------


def test_an_unknown_model_is_refused() -> None:
    with pytest.raises(DocumentError) as caught:
        build("werner", {"qber": F(0)}, _bb84_context())
    assert caught.value.reason is DocumentReason.LIBRARY_MODEL_UNKNOWN


@pytest.mark.parametrize(
    "bind",
    [{}, {"qber": F(0), "transmittance": F(1)}, {"QBER": F(0)}],
    ids=["missing", "extra", "misspelt"],
)
def test_a_binding_that_is_not_exactly_the_parameters_is_refused(
    bind: dict[str, F],
) -> None:
    with pytest.raises(DocumentError) as caught:
        build("depolarized_bell_pair", bind, _bb84_context())
    assert caught.value.reason is DocumentReason.LIBRARY_MODEL_BINDING_INVALID


def test_a_good_binding_builds_the_instances_own_providers() -> None:
    built = build("depolarized_bell_pair", {"qber": F(1, 20)}, _bb84_context())
    assert built.raw is not None
    assert built.note == bb84_surface.DEFAULT_HONEST_MODEL_NOTE


# ---------------------------------------------------------------------------
#  Preconditions: every instance's structure passes, a mismatched one is refused
# ---------------------------------------------------------------------------


def test_every_instance_context_satisfies_its_models_preconditions(
    decoy: tuple[HonestContext, Any], bbm92: tuple[HonestContext, Any]
) -> None:
    MODELS["depolarized_bell_pair"].preconditions(_bb84_context())
    MODELS["single_photon_loss_depolarizing"].preconditions(_optical_context())
    MODELS["coherent_pulses"].preconditions(decoy[0])
    MODELS["spdc_pair"].preconditions(bbm92[0])
    MODELS["ideal_pair"].preconditions(_bbm92_context("ideal_pair")[0])


def test_the_contexts_tell_the_declarations_truth(
    decoy: tuple[HonestContext, Any], bbm92: tuple[HonestContext, Any]
) -> None:
    """``d_A``, the source alphabet and the station ids are the compiled ones."""
    for context, prepared in (decoy, bbm92):
        declaration = prepared.declaration
        assert context.source is not None
        assert context.source.alice_dim in (None, declaration.alice_dim)
        assert context.source.alphabet == declaration.alice_alphabet
    assert tuple(s.id for s in bbm92[0].stations) == (
        bbm92[1].declaration.measured_factor_labels
    )


def _refused(name: str, context: HonestContext) -> str:
    with pytest.raises(DocumentError) as caught:
        MODELS[name].preconditions(context)
    assert caught.value.reason is DocumentReason.LIBRARY_MODEL_BINDING_INVALID
    return caught.value.detail


def test_a_model_is_refused_on_another_instances_structure(
    decoy: tuple[HonestContext, Any], bbm92: tuple[HonestContext, Any]
) -> None:
    optical = _optical_context()
    assert "declared_povm" in _refused("depolarized_bell_pair", optical)
    assert "optical station" in _refused(
        "single_photon_loss_depolarizing", _bb84_context()
    )
    assert "wcp_decoy" in _refused("coherent_pulses", optical)
    assert "untrusted" in _refused("ideal_pair", decoy[0])
    assert "untrusted" in _refused("spdc_pair", optical)


def test_a_cutoff_below_one_is_refused() -> None:
    """The template's lowering runs the model's preconditions on its context.

    So the refusal comes from building the context at cutoff 0 (the Python
    instance built the context first and the test asked the model after).
    """
    with pytest.raises(DocumentError) as caught:
        _optical_context(photon_cutoff=F(0))
    assert caught.value.reason is DocumentReason.LIBRARY_MODEL_BINDING_INVALID
    assert "at least 1" in caught.value.detail


def _with_station(context: HonestContext, index: int, **changes: Any) -> HonestContext:
    stations = list(context.stations)
    stations[index] = replace(stations[index], **changes)
    return replace(context, stations=tuple(stations))


def _with_request(context: HonestContext, index: int, **changes: Any) -> HonestContext:
    request = context.stations[index].request
    assert request is not None
    return _with_station(context, index, request=replace(request, **changes))


def test_channel_modes_that_are_not_h_and_v_of_one_path_are_refused(
    decoy: tuple[HonestContext, Any],
) -> None:
    context = decoy[0]
    request = context.stations[0].request
    assert request is not None
    at = {mode.label: i for i, mode in enumerate(request.mode_space.modes)}
    two_paths = _with_request(
        context, 0, input_modes=InputModes(channel=(at["Z_H"], at["X_V"]))
    )
    assert "H and V modes of one path" in _refused("coherent_pulses", two_paths)


def _reordered(coarse: CoarseGraining, names: dict[str, str]) -> CoarseGraining:
    """Rename every letter and reverse the declared order: the same map."""
    return CoarseGraining(
        port_count=coarse.port_count,
        alphabet=tuple(names[letter] for letter in reversed(coarse.alphabet)),
        assignment={pattern: names[v] for pattern, v in coarse.assignment.items()},
    )


def test_a_non_canonical_coarse_graining_is_refused(
    decoy: tuple[HonestContext, Any], bbm92: tuple[HonestContext, Any]
) -> None:
    request = decoy[0].stations[0].request
    assert request is not None
    coarse = request.outcome_coarse_graining
    # H and V clicks merged into one letter: not a letter per port.
    merged = CoarseGraining(
        port_count=coarse.port_count,
        alphabet=tuple(v for v in coarse.alphabet if v != "V"),
        assignment={p: ("H" if v == "V" else v) for p, v in coarse.assignment.items()},
    )
    context = _with_request(decoy[0], 0, outcome_coarse_graining=merged)
    assert "canonical" in _refused("coherent_pulses", context)
    spdc = _with_request(bbm92[0], 1, outcome_coarse_graining=merged)
    assert "canonical" in _refused("spdc_pair", spdc)


def test_the_pair_models_refuse_a_wrong_choice_weighting_or_party_order(
    bbm92: tuple[HonestContext, Any],
) -> None:
    context = bbm92[0]
    no_coin = _with_station(context, 0, choice_weighting=None)
    assert "choice weighting" in _refused("spdc_pair", no_coin)
    swapped = replace(context, stations=context.stations[::-1])
    assert "A and then B" in _refused("ideal_pair", swapped)
    assert "A and then B" in _refused("spdc_pair", swapped)


# ---------------------------------------------------------------------------
#  Letters by attribute
# ---------------------------------------------------------------------------


def _positional_name(kind: tuple[str, str | None]) -> str:
    return {NONE: "nc", MULTI: "mc"}.get(kind[0]) or str(kind[1])


def test_decoy_attribute_maps_reproduce_the_positional_zip(
    decoy: tuple[HonestContext, Any],
) -> None:
    station = decoy[0].stations[0]
    emitted = decoy[1].declaration.bob_alphabet
    classes = letter_classes(station)
    components = outcome_components(station)
    assert classes is not None
    by_attribute = {v: _positional_name(classes[components[v][0]]) for v in emitted}
    assert by_attribute == dict(zip(emitted, POSITIONAL, strict=True))
    assert all(components[v][1:] == ("off", None) for v in emitted)


def test_bbm92_attribute_maps_reproduce_the_positional_zips(
    bbm92: tuple[HonestContext, Any],
) -> None:
    declaration = bbm92[1].declaration
    assert declaration.bob_factors is not None
    first, second = declaration.bob_factors.factors
    alice, bob = (
        bbm92[0].station(label) for label in declaration.measured_factor_labels
    )
    alice_components, bob_components = (
        outcome_components(alice),
        outcome_components(bob),
    )
    assert {
        v: (alice_components[v][0], alice_components[v][2]) for v in first.alphabet
    } == dict(zip(first.alphabet, product(RAW_LETTERS, ("gen", "test")), strict=True))
    assert {v: bob_components[v][0] for v in second.alphabet} == dict(
        zip(second.alphabet, RAW_LETTERS, strict=True)
    )
    # The coin weight of a choice is the declared matrix entry, not a name.
    weighting = alice.choice_weighting
    assert weighting is not None
    gamma = F(str(bbm92_surface.default_config().device["test_fraction"]))
    assert weighting.weight("off", "test") + weighting.weight("off", "gen") == 1
    assert abs(weighting.weight("off", "test") - gamma) < F(1, 1 << 11)


def test_letters_are_read_by_the_map_and_not_by_their_names_or_order(
    decoy: tuple[HonestContext, Any],
) -> None:
    """Renamed, reversed letters give each port the same probability."""
    context = decoy[0]
    station = context.stations[0]
    request = station.request
    assert request is not None and context.source is not None
    wcp = context.source.wcp
    assert wcp is not None
    names = {v: f"y{i}" for i, v in enumerate(request.outcome_coarse_graining.alphabet)}
    renamed = replace(
        station,
        request=replace(
            request,
            outcome_coarse_graining=_reordered(request.outcome_coarse_graining, names),
        ),
    )
    classes = letter_classes(renamed)
    assert classes is not None
    assert classes == {
        names[v]: kind for v, kind in (letter_classes(station) or {}).items()
    }
    bind = {"transmittance": F(1, 2), "misalignment": F(1, 100)}
    original = raw_distribution(wcp, station, POSITIONAL, **bind)
    moved = raw_distribution(
        wcp, renamed, tuple(names[v] for v in reversed(POSITIONAL)), **bind
    )
    assert moved == {(x, names[v]): p for (x, v), p in original.items()}


def test_the_raw_table_is_the_click_law_of_each_port() -> None:
    """Through the station's own request, the common receiver's click law.

    NEAR-CIRCULAR BY CONSTRUCTION: both sides run :func:`port_clicks`, so
    this pins only that the request path and the ``ReceiverParameters`` path
    feed it the same graph, ports and detectors. That the law itself
    is the decoy instance's rests on the golden and oracle tests.
    """
    context = _optical_context()
    station = context.stations[0]
    assert station.request is not None
    from instances.common.honest.coherent_pulses import JONES, port_clicks
    from instances.common.optics import ReceiverParameters

    request = station.request
    labels = [mode.label for mode in request.mode_space.modes]
    vacuum, singles, multi = port_clicks(
        request.element_graph,  # type: ignore[arg-type]
        request.mode_space,
        request.port_map.entries,
        tuple(F(p.efficiency) for p in request.detector_layer),
        tuple(F(p.dark_count_probability) for p in request.detector_layer),
        (labels.index("Z_H"), labels.index("Z_V")),
        intensity=F(1, 2),
        jones=JONES["+"],
        transmittance=F(1),
        misalignment=F(0),
    )
    expected = click_distribution(
        ReceiverParameters(),
        intensity=F(1, 2),
        polarisation="plus",
        transmittance=F(1),
        misalignment=F(0),
    )
    assert {"nc": vacuum, **singles, "mc": multi} == expected
    assert list(singles) == [label for label, _ in PORTS]


def test_station_facts_read_the_receiver_request() -> None:
    station = _optical_context().stations[0]
    assert isinstance(station, StationFacts)
    assert station.port_labels == tuple(label for label, _ in PORTS)
    assert station.settings == ("off",)
    assert (
        station.photon_cutoff
        == optical_surface.default_config().device["photon_cutoff"]
    )
    assert SourceFacts(kind="trusted", alice_dim=2).wcp is None


def test_a_multi_mode_port_sums_its_modes_power() -> None:
    """Merging two ports into one two-mode port keeps the no-click law.

    A port watching several modes has power ``sum |alpha_m|^2``, so with equal
    efficiencies and no dark counts its no-click probability
    ``exp(-eta mu sum |alpha_m|^2)`` is the product of the two single-mode
    ports' -- to the 60-digit evaluation, not bit for bit.
    """
    from instances.common.honest.coherent_pulses import JONES, port_clicks
    from instances.common.optics import ReceiverParameters, element_graph, mode_space

    parameters = ReceiverParameters()
    space = mode_space()
    at = {mode.label: i for i, mode in enumerate(space.modes)}
    ports = tuple((label, tuple(at[m] for m in modes)) for label, modes in PORTS)
    eta = (F(9, 10),) * 4
    dark = (F(0),) * 4
    kwargs: dict[str, Any] = {
        "intensity": F(1, 2),
        "jones": JONES["+"],
        "transmittance": F(1),
        "misalignment": F(0),
    }
    channel = (at["Z_H"], at["Z_V"])
    graph = element_graph(parameters)
    vacuum, singles, _ = port_clicks(graph, space, ports, eta, dark, channel, **kwargs)
    merged_ports = (("HV", ports[0][1] + ports[1][1]), *ports[2:])
    merged, merged_singles, _ = port_clicks(
        graph, space, merged_ports, eta[:3], dark[:3], channel, **kwargs
    )
    # No click anywhere: the two-mode port's factor is the product of the two.
    assert abs(merged - vacuum) < F(1, 10**50)
    # The ports it does not touch keep their odds of firing alone.
    assert abs(merged_singles["D"] / merged - singles["D"] / vacuum) < F(1, 10**50)


def test_build_wires_the_live_note_for_spdc(bbm92: tuple[HonestContext, Any]) -> None:
    """A document's SPDC model records its Gram preparation in the run's note.

    The SPDC model writes ``gram_preparation`` into ``context.note`` once the
    stations' Grams exist; ``build`` must hand that same dict back as the note
    the caller passes to the run, or a document run would lack the snap record
    of the Grams it declared.
    """
    context, _ = _bbm92_context("spdc")
    prepared = bbm92[1]
    model = bbm92_surface.default_config().model
    bind = {name: model[name] for name in MODELS["spdc_pair"].parameters}
    built = build("spdc_pair", bind, context)
    assert built.note is context.note
    assert "gram_preparation" not in built.note
    context.set_emissions(prepared.device_artifacts)
    assert len(built.note["gram_preparation"]) == 2
    assert built.raw is not None
    table = built.raw(prepared.declaration)
    assert table == prepared.raw_joint_distribution
    assert sum(table.values()) == 1
