"""The packaged templates' lowered objects, for tests of what an instance builds.

WHY A SUPPORT MODULE. The instances bb84, optical_bb84, decoy_bb84 and bbm92
are protocol documents (``instances/<id>/protocol.yaml``). Tests of
what an instance builds -- its device requests, its specification provider, its
public part, its source preparation, its configuration reader -- assert against
what the template LOWERS to: the station's
:class:`~certiqs_key.runs.pipeline. DeviceRequests`, the specification
provider, the expanded rule tables, the prepared source. This module is the one
place a test reaches the document surface's reader,
:meth:`~instances.declared.DocumentSurface._read`, which returns the
configuration as a run reads it and the lowering.

Nothing here builds a second wiring: every object comes from the template's
own lowering at a configuration the instance's ``default_config`` builds.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Any

from instances import surface_of
from instances.common.optics import PORTS, ReceiverParameters
from instances.common.wcp import PreparedSource, prepare_source
from instances.declared import DocumentSurface
from instances.declared.lowering import Lowered
from tests.support.declared_optical_documents import (
    custom_from,
    template_surface,
    template_tree,
)

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.protocol_compiler import ProtocolSpecification
from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.inputs import NumericInput
from certiqs_key.runs.pipeline import SliceOutcome
from certiqs_key.runs.pipeline import run_slice as _run_slice
from certiqs_key.transmitter.certificate import RetentionAttestation
from certiqs_key.transmitter.decoy import FlagFamily

if TYPE_CHECKING:  # pragma: no cover - typing only
    from certiqs_key.solvers.frank_wolfe import FrankWolfeOptions
    from certiqs_key.solvers.oracles.protocol import LinearOracle
    from certiqs_key.solvers.types import SearchRequest

__all__ = [
    "ACCEPTANCE_MAPS",
    "ANNOUNCEMENT_RESOLVED",
    "ENCODED",
    "LICENSED",
    "LICENSED_TWO_SECTOR",
    "MERGED_DISCARD",
    "OPTICAL_ACCEPTANCE_ALPHABETS",
    "PAIR_RESOLVED",
    "ROUTES",
    "choice_options",
    "decoy_source",
    "lowered",
    "optical_config",
    "optical_lowered",
    "optical_run_slice",
    "qubit_run_slice",
    "wcp_source",
]

#: The reduction routes, by the templates' ``route`` domain.
ENCODED = "encoded"
LICENSED = "licensed"
LICENSED_TWO_SECTOR = "licensed+two-sector"
#: The acceptance maps, by the templates' ``acceptance_map`` domain.
MERGED_DISCARD = "merged-discard"
ANNOUNCEMENT_RESOLVED = "announcement-resolved"
PAIR_RESOLVED = "pair-resolved"


def choice_options(instance: str, name: str) -> tuple[str, ...]:
    """Return a choice parameter's values, in the template's declared order."""
    (row,) = (spec for spec in surface_of(instance).PARAMETERS if spec.name == name)
    assert row.domain is not None, name
    return tuple(option for option, _meaning in row.domain.options)


ROUTES: tuple[str, ...] = choice_options("optical_bb84", "route")
ACCEPTANCE_MAPS: tuple[str, ...] = choice_options("optical_bb84", "acceptance_map")
assert set(ROUTES) == {ENCODED, LICENSED, LICENSED_TWO_SECTOR}
assert set(ACCEPTANCE_MAPS) == {MERGED_DISCARD, ANNOUNCEMENT_RESOLVED, PAIR_RESOLVED}

_ALICE_ANNOUNCEMENTS = ("Z", "(X,0)", "(X,1)")
_BOB_RESOLVED = ("Z", "(X,0)", "(X,1)", "nc", "mc")

#: Optical BB84's acceptance alphabet ``Chat`` under each acceptance map, in its
#: declared order, WRITTEN OUT as the independent
#: expectation a run's declaration is compared against (the merged arm's is
#: the qubit instance's four letters; a pair letter is ``"<c_A>|<c_B>"``,
#: Alice major).
OPTICAL_ACCEPTANCE_ALPHABETS: Mapping[str, tuple[str, ...]] = {
    MERGED_DISCARD: ("gen", "ok", "err", "disc"),
    ANNOUNCEMENT_RESOLVED: ("gen", "ok", "err", "mis", "nc", "mc"),
    PAIR_RESOLVED: tuple(
        f"{c_a}|{c_b}" for c_a in _ALICE_ANNOUNCEMENTS for c_b in _BOB_RESOLVED
    ),
}


def lowered(
    instance: str | DocumentSurface, config: RunConfig | None = None
) -> tuple[RunConfig, Lowered]:
    """Return a configuration as a run reads it, and the template's lowering of it.

    ``config`` defaults to the instance's ``default_config()``.
    """
    surface = template_surface(instance) if isinstance(instance, str) else instance
    configured, lowering = surface._read(
        surface.default_config() if config is None else config
    )
    return configured, lowering


def _per_port(values: tuple[Fraction, ...]) -> dict[str, Fraction]:
    """Return a per-detector tuple keyed by the port labels, in the port map's order."""
    return {label: value for (label, _mode), value in zip(PORTS, values, strict=True)}


def optical_config(
    parameters: ReceiverParameters | None = None,
    *,
    route: str = ENCODED,
    acceptance_map: str = MERGED_DISCARD,
    declared_tolerance: float = 1e-12,
    model: Mapping[str, Any] | None = None,
) -> RunConfig:
    """Return optical BB84's configuration for a receiver, route and acceptance map.

    The device section is the receiver's parameters as the template's table
    names them (the per-port rows keyed by the port labels); an absent
    ``exact_window`` is left absent, so that the receiver declares none.
    """
    receiver = parameters if parameters is not None else ReceiverParameters()
    device: dict[str, Any] = {
        "basis_split": receiver.basis_split,
        "half_wave_angle": receiver.half_wave_angle,
        "pbs_leak_transmitted": receiver.pbs_leak_transmitted,
        "pbs_leak_reflected": receiver.pbs_leak_reflected,
        "efficiency": _per_port(receiver.efficiency),
        "dark_count": _per_port(receiver.dark_count),
        "photon_cutoff": receiver.photon_cutoff,
        "route": route,
        "acceptance_map": acceptance_map,
    }
    if receiver.exact_window is not None:
        device["exact_window"] = receiver.exact_window
    overrides: dict[str, Any] = {
        "device": device,
        "declared_tolerance": declared_tolerance,
    }
    if model is not None:
        overrides["model"] = dict(model)
    return surface_of("optical_bb84").default_config(**overrides)


def _alice_weights(alice_z: Fraction, alice_x: Fraction) -> Any:
    def edit(tree: dict[str, Any]) -> None:
        source = tree["source"]
        source["weights"] = {
            "(Z,0)": str(alice_z / 2),
            "(Z,1)": str(alice_z / 2),
            "(X,0)": str(alice_x / 2),
            "(X,1)": str(alice_x / 2),
        }
        source["alice"]["choice_family"]["weights"] = {
            "Z": str(alice_z),
            "X": str(alice_x),
        }

    return edit


def optical_lowered(
    parameters: ReceiverParameters | None = None,
    *,
    route: str = ENCODED,
    acceptance_map: str = MERGED_DISCARD,
    declared_tolerance: float = 1e-12,
    alice_z: Fraction = Fraction(1, 2),
    alice_x: Fraction = Fraction(1, 2),
    model: Mapping[str, Any] | None = None,
) -> Lowered:
    """Return optical BB84's lowering: one station's requests and its provider.

    Alice's basis weights are fixed in the template's source at ``1/2``; other
    weights lower a custom document that differs from the template in exactly
    the source's weights and Alice's choice weights.
    """
    config = optical_config(
        parameters,
        route=route,
        acceptance_map=acceptance_map,
        declared_tolerance=declared_tolerance,
        model=model,
    )
    surface: DocumentSurface | str = "optical_bb84"
    if (alice_z, alice_x) != (Fraction(1, 2), Fraction(1, 2)):
        surface = custom_from(
            "optical_bb84", _alice_weights(alice_z, alice_x), "optical_alice_weights"
        )
        config = surface.default_config(
            model=dict(config.model),
            device=dict(config.device),
            declared_tolerance=declared_tolerance,
        )
    return lowered(surface, config)[1]


def qubit_run_slice(
    specification: ProtocolSpecification,
    *,
    qber: Fraction,
    rounds: int,
    completeness_budget: Fraction,
    parameters: KeyLengthParameters,
    oracle: LinearOracle,
    directory: Path,
    declared_tolerance: float,
    alpha: float | None = None,
    options: FrankWolfeOptions | None = None,
    request: SearchRequest | None = None,
    constrained: tuple[str, ...] | None = None,
) -> SliceOutcome:
    """Run the flow once on ``specification`` with bb84's honest model at ``qber``.

    The run tier's :func:`~certiqs_key.runs.pipeline.run_slice` with the library model
    the bb84 template names
    (:mod:`instances.common.honest.depolarized_bell_pair`), every other
    argument forwarded unchanged, and the same ``created_by``.
    """
    from instances.common.honest.depolarized_bell_pair import honest_provider

    return _run_slice(
        specification,
        honest_provider=honest_provider(qber),
        rounds=rounds,
        completeness_budget=completeness_budget,
        parameters=parameters,
        oracle=oracle,
        directory=directory,
        declared_tolerance=declared_tolerance,
        created_by=f"instances.bb84[Q={qber}, n={rounds}]",
        alpha=alpha,
        options=options,
        request=request,
        constrained=constrained,
    )


def optical_run_slice(
    *,
    qber: Fraction,
    transmittance: Fraction,
    receiver: ReceiverParameters,
    rounds: int,
    completeness_budget: Fraction,
    parameters: KeyLengthParameters,
    oracle: LinearOracle,
    directory: Path,
    alice_z: Fraction = Fraction(1, 2),
    alice_x: Fraction = Fraction(1, 2),
    declared_tolerance: float,
    alpha: float | None = None,
    options: FrankWolfeOptions | None = None,
    request: SearchRequest | None = None,
    constrained: tuple[str, ...] | None = None,
    route: str = ENCODED,
    acceptance_map: str = MERGED_DISCARD,
) -> SliceOutcome:
    """Run the flow once for optical BB84, its device and model the template's.

    The honest provider, the device requests and the specification provider
    are the template's lowering at ``qber``, ``transmittance``, the receiver,
    the route and the acceptance map (:func:`optical_lowered`); every other
    argument is forwarded unchanged, and ``created_by`` names the route and the
    acceptance map.
    """
    lowering = optical_lowered(
        receiver,
        route=route,
        acceptance_map=acceptance_map,
        declared_tolerance=declared_tolerance,
        alice_z=alice_z,
        alice_x=alice_x,
        model={"qber": qber, "transmittance": transmittance},
    )
    assert lowering.specification_provider is not None
    return _run_slice(
        honest_provider=lowering.honest,
        device=lowering.device,
        specification_provider=lowering.specification_provider,
        rounds=rounds,
        completeness_budget=completeness_budget,
        parameters=parameters,
        oracle=oracle,
        directory=directory,
        declared_tolerance=declared_tolerance,
        created_by=(
            f"instances.optical_bb84[Q={qber}, eta={transmittance}, "
            f"N={receiver.photon_cutoff}, "
            f"m*={receiver.exact_window}, route={route}, "
            f"acceptance={acceptance_map}, n={rounds}]"
        ),
        alpha=alpha,
        options=options,
        request=request,
        constrained=constrained,
    )


def decoy_source(config: RunConfig | None = None) -> tuple[RunConfig, PreparedSource]:
    """Return decoy BB84's configuration as a run reads it, and its prepared source.

    The source is the template's ``wcp_decoy`` block lowered at ``config``
    (default: the instance's ``default_config()``): the tagged declaration
    before emission and its preparation record, which the configuration's
    ``input_preparation`` also carries.
    """
    configured, lowering = lowered("decoy_bb84", config)
    assert lowering.wcp_source is not None
    return configured, lowering.wcp_source


def wcp_source(
    *,
    intensities: Mapping[str, NumericInput],
    test_intensity_probabilities: list[NumericInput],
    gamma: NumericInput,
    entropy_cutoff: int = 1,
    source_cutoff: int = 6,
    tolerance: float = 1e-10,
) -> PreparedSource:
    """Prepare a tagged WCP source in decoy BB84's shape, at any intensities.

    The library's :func:`instances.common.wcp.prepare_source` with everything
    but the intensities and probabilities read off the decoy template's source
    block: its polarisations and parts, which polarisations a generation and a
    test round send, its lattice, letter labels, record site and label, and
    retention attestation. The first intensity is the signal, at which
    generation rounds are sent.
    """
    source = template_tree("decoy_bb84")["source"]
    attestation = source["retention_attestation"]
    template = source.get("letter_label", "{round}-{intensity}-{polarisation}")
    return prepare_source(
        polarisations={
            entry["label"]: entry["part"] for entry in source["polarisations"]
        },
        intensities=dict(intensities),
        test_probabilities=list(test_intensity_probabilities),
        coin=gamma,
        generation_intensity=next(iter(intensities)),
        generation_polarisations=tuple(source["generation"]["polarisations"]),
        test_polarisations=tuple(source["test"]["polarisations"]),
        entropy_cutoff=entropy_cutoff,
        source_cutoff=source_cutoff,
        lattice_exponent=int(source["lattice_exponent"]),
        flag_family=FlagFamily(source.get("flag_family", "shared")),
        attestation=RetentionAttestation(
            attestation["attested_by"], attestation["statement"]
        ),
        letter_label=lambda fields: template.format_map(dict(fields)),
        tolerance=tolerance,
        site=source["record_site"],
        instance=source["record_label"],
    )
