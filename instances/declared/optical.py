"""Lowering an optical station: the receiver request, the reduction, the device.

WHY A MODULE OF ITS OWN. An ``optical`` station is the largest
block of a document: modes, ports, detectors, a coarse-graining written as
rules over click patterns, one of the receiver's three input routes
(an element graph of catalogue components C1-C10, port Grams, or an instrument
matrix), and the reduction the station's emission goes through. This module
turns it into exactly the three declarations a physical station hands the run
tier -- :class:`~certiqs_key.receiver.request.ReceiverRequest`, the
reductions' ``ProtocolDeclaration`` and
:class:`~certiqs_key.reductions.inputs.ReductionRequest` -- and the
:class:`~certiqs_key.runs.pipeline.DeviceRequests` that carries them, the
construction ``instances.common.passive_device.passive_device_requests``
makes for the common passive receiver, generalised to any declared optics.

WHAT IT DECIDES: NOTHING ABOUT THE RECEIVER. Whether a beamsplitter's
transmittance is in its domain, whether the graph is well ordered, whether the
coarse-graining is total, whether two input routes were given, whether the
dark-count channel is column-stochastic: each is the receiver's or the
reductions' refusal, returned as data by the run. What is refused here is what
has no meaning as a document: a mode label that names no declared mode (or two
of them), a catalogue entry missing one of its fields, a matrix that is not
square where a square one is the only reading, and -- for a custom document
-- a photon number, a port count or a receiver's work past the document
layer's work bounds (:mod:`.limits`; a packaged template is bounded by its own
parameter domains).

THE CATALOGUE SCALARS. A field written as a JSON
integer is passed as that ``int``; every other scalar as a ``Fraction``. A
document field ``<f>_pi`` is the catalogue's angle ``<f>`` in units of pi: it
is passed as :class:`~certiqs_key.receiver.numerics.PiMultiple` of its value,
which is how the common passive receiver declares its plate angle
(``instances/common/optics.py``), except an integer
literal ``0``, which is passed as ``0``. Records serialise ``0``,
``Fraction(0)`` and a pi multiple differently, so the rule reproduces the
reference declarations byte for byte. The float-valued routes (port
Grams, an instrument matrix, a C10 block) are converted entry by entry to the
receiver's ``complex128``, each inexact entry with a recorded
``numeric_input_conversion``.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Any, cast

import numpy as np

from certiqs_key.foundations import exact
from certiqs_key.foundations.assurance import Assurance
from certiqs_key.foundations.snap import SnapSettings
from certiqs_key.receiver.catalogue import (
    Beamsplitter,
    Component,
    GenericBlock,
    Loss,
    Mirror,
    ModeRouting,
    PhaseShifter,
    Polarizer,
    PolarizingBeamsplitter,
    Retarder,
    Rotator,
)
from certiqs_key.receiver.coarse import CoarseGraining as ReceiverCoarseGraining
from certiqs_key.receiver.dark import DarkCountChannel, DarkCountRoute
from certiqs_key.receiver.grams import GramFamily
from certiqs_key.receiver.graph import Element as GraphElement
from certiqs_key.receiver.graph import ElementGraph
from certiqs_key.receiver.modes import (
    InputModes,
    Mode,
    ModeSpace,
    Polarization,
    PortMap,
)
from certiqs_key.receiver.numerics import PiMultiple
from certiqs_key.receiver.request import DetectorPort, ReceiverRequest
from certiqs_key.receiver.settings import (
    OFF_SETTING,
    ProbeDeclaration,
)
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.inputs import (
    CarriedOperatorRequest,
    ConstraintForm,
    LinkDeclaration,
    ReductionRequest,
    outcome_label,
)
from certiqs_key.reductions.inputs import ProbeDeclaration as ReductionProbe
from certiqs_key.reductions.inputs import ProtocolDeclaration as ReductionDeclaration
from certiqs_key.reductions.reasons import (
    CertificateKind,
    LinkKind,
    LinkStage,
    Relation,
    SourceMode,
)
from certiqs_key.reductions.wpfss import reduce_flat
from certiqs_key.runs.pipeline import (
    CarriedOperatorProvider,
    DeviceRequests,
    Station,
)
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.limits import (
    MAX_INPUT_BLOCK,
    MAX_MODES,
    MAX_PHOTON_CUTOFF,
    MAX_PHOTON_NUMBER,
    MAX_PORTS,
    MAX_RECEIVER_WORK,
    MAX_TOLERANCES,
    check_size,
    photon_blocks,
    receiver_work,
)
from instances.declared.model import (
    BeamsplitterElement,
    ExplicitOperator,
    GenericBlockElement,
    LibraryOperator,
    LossElement,
    MirrorElement,
    ModeRoutingElement,
    Optical,
    ParamRef,
    PhaseShifterElement,
    PolarizerElement,
    PolarizingBeamsplitterElement,
    Reduction,
    RetarderElement,
    RotatorElement,
    WaveplateElement,
)
from instances.declared.rules import Entry, Expansion, Variable, expand_bindings
from instances.declared.values import (
    Environment,
    ParameterAbsentError,
    evaluate_exact,
    matrix,
    number,
    unwrap,
)

__all__ = [
    "KIND_OF_SOURCE",
    "Conversions",
    "LoweredReceiver",
    "device_requests",
    "float_matrix",
    "receiver_request",
]

#: The reductions' source mode of each document source kind: a ``wcp_decoy``
#: source is trusted, as decoy BB84 declares it.
KIND_OF_SOURCE: Mapping[str, SourceMode] = {
    "trusted_ensemble": SourceMode.TRUSTED,
    "wcp_decoy": SourceMode.TRUSTED,
    "untrusted": SourceMode.UNTRUSTED,
}

#: The reductions' relation of each document spelling.
_RELATION: Mapping[str, Relation] = {
    "ge": Relation.GE,
    "le": Relation.LE,
    "eq": Relation.EQ,
}

#: The receiver's six declared tolerances and the two a window brings, at the
#: common passive receiver's 1e-3 (``instances.common.optics``), read from there.
_DEFAULT_TOLERANCES: tuple[str, ...] = (
    "eps_1",
    "eps_2",
    "eps_3",
    "eps_4",
    "eps_5",
    "eps_gap",
)


class Conversions:
    """The ``numeric_input_conversion`` records of one lowering's float routes.

    Port Grams, an instrument matrix and a C10 block are float data of the
    receiver (its numeric substrate is ``complex128``): their exact entries
    are converted here, once, and each entry whose binary64 value differs from
    what was written is recorded with the rule and shape ``runs.inputs``
    records a configuration's conversions in, at site ``document:<pointer>``.
    """

    def __init__(self) -> None:
        """Start with no record."""
        self.records: list[dict[str, Any]] = []

    def entry(self, value: Fraction, site: str) -> float:
        """Return ``value`` as binary64, recording the conversion if inexact."""
        try:
            result = float(value)
        except OverflowError:
            result = math.inf
        if not math.isfinite(result):
            raise DocumentError(
                f"{value} is outside the binary64 range of the receiver's float routes",
                reason=DocumentReason.MATRIX_MALFORMED,
                path=site,
            )
        if Fraction(result) != value:
            self.records.append(
                {
                    "site": f"document:{site}",
                    "rule": "numeric_input_conversion",
                    "input_type": "Fraction",
                    "input_value": str(value),
                    "prepared_value": str(Fraction(result)),
                    "total_displacement": str(Fraction(result) - value),
                }
            )
        return result


def float_matrix(
    node: object, environment: Environment, path: str, conversions: Conversions
) -> np.ndarray:
    """Return a matrix node as the receiver's ``complex128`` array."""
    rows = matrix(node, environment, path)
    out = np.zeros((len(rows), len(rows[0]) if rows else 0), dtype=np.complex128)
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            real = conversions.entry(Fraction(value.re), f"{path}[{i},{j}].re")
            imaginary = conversions.entry(Fraction(value.im), f"{path}[{i},{j}].im")
            out[i, j] = complex(real, imaginary)
    return out


def _square(array: np.ndarray, what: str, path: str) -> np.ndarray:
    if array.ndim != 2 or array.shape[0] != array.shape[1] or array.shape[0] == 0:
        raise DocumentError(
            f"{what} is a square matrix; this one has shape {array.shape}",
            reason=DocumentReason.MATRIX_MALFORMED,
            path=path,
        )
    return array


@dataclass(frozen=True)
class LoweredReceiver:
    """One optical station's receiver request and what the lowering reads of it.

    ``outcomes`` is the station's emitted alphabet ``V = Y x T`` as the
    reductions spell it (``outcome_label``), in the declared order (``t``
    slowest, ``y`` fastest), each entry carrying ``letter`` with the
    coarse-graining letter's attributes and ``setting``: what a rule over the
    station's outcomes reads.
    """

    request: ReceiverRequest
    letters: tuple[str, ...]
    settings: tuple[str, ...]
    class_weights: Mapping[str, Fraction]
    outcomes: tuple[Entry, ...]
    coarse: Expansion
    space: ModeSpace
    conversions: list[dict[str, Any]] = field(default_factory=list)
    #: Each optional field read as absent: ``{path, parameter, read_as}``.
    absent: list[dict[str, str]] = field(default_factory=list)
    #: What the station declares as numbers rather than catalogue physics:
    #: ``(what, path)`` (A-TRUST).
    characterisation: list[tuple[str, str]] = field(default_factory=list)


class _Reader:
    """The values of one station, with the paths refusals name.

    ``work_bounds`` says whether the work bounds of :mod:`.limits` hold: they
    do for a custom document and not for a packaged template.
    """

    def __init__(
        self, environment: Environment, path: str, *, work_bounds: bool
    ) -> None:
        self.env = environment
        self.path = path
        self.work_bounds = work_bounds

    def at(self, *parts: str | int) -> str:
        return self.path + pointer(*parts)

    def scalar(self, node: object, path: str) -> int | Fraction:
        """Return a catalogue scalar: a JSON integer as ``int``, else exact."""
        return number(node, self.env, path)

    def angle(self, node: object, path: str) -> int | PiMultiple:
        """Return a ``_pi`` field: a pi multiple, an integer literal 0 as 0."""
        resolved, where = unwrap(node, self.env, path)
        if (
            isinstance(resolved, int)
            and not isinstance(resolved, bool)
            and not resolved
        ):
            return 0
        return PiMultiple(Fraction(number(resolved, self.env, where)))

    def integer(self, node: object, path: str) -> int:
        value = Fraction(number(node, self.env, path))
        if value.denominator != 1:
            raise DocumentError(
                f"an integer is required here; the value is {value}",
                reason=DocumentReason.EXPRESSION_NOT_INTEGRAL,
                path=path,
            )
        return int(value)

    def photons(self, node: object, path: str) -> int:
        value = self.integer(node, path)
        if self.work_bounds:
            check_size(value, MAX_PHOTON_NUMBER, "a declared photon number", path)
        return value


def _required(params: object, name: str, component: str, path: str) -> object:
    value = getattr(params, name)
    if value is None:
        raise DocumentError(
            f"the {component} entry declares {name}; it has no default",
            reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
            path=path + pointer("params", name),
        )
    return value


def _component(
    element: object, read: _Reader, path: str, conversions: Conversions
) -> Component:
    """Return a catalogue entry from a document element."""

    def need(name: str) -> object:
        return _required(element.params, name, element.component, path)  # type: ignore[attr-defined]

    def at(name: str) -> str:
        return path + pointer("params", name)

    if isinstance(element, BeamsplitterElement):
        return Beamsplitter(
            transmittance=read.scalar(need("transmittance"), at("transmittance")),
            phase=read.angle(need("phase_pi"), at("phase_pi")),
            loss_1=read.scalar(need("loss_1"), at("loss_1")),
            loss_2=read.scalar(need("loss_2"), at("loss_2")),
        )
    if isinstance(element, PolarizingBeamsplitterElement):
        return PolarizingBeamsplitter(
            transmittance_h=read.scalar(need("transmittance_h"), at("transmittance_h")),
            transmittance_v=read.scalar(need("transmittance_v"), at("transmittance_v")),
            phase_h=read.angle(need("phase_h_pi"), at("phase_h_pi")),
            phase_v=read.angle(need("phase_v_pi"), at("phase_v_pi")),
            loss_1=read.scalar(need("loss_1"), at("loss_1")),
            loss_2=read.scalar(need("loss_2"), at("loss_2")),
        )
    if isinstance(element, RetarderElement):
        return Retarder(
            read.angle(need("retardance_pi"), at("retardance_pi")),
            read.angle(need("angle_pi"), at("angle_pi")),
            read.scalar(need("loss"), at("loss")),
        )
    if isinstance(element, WaveplateElement):
        preset = (
            Retarder.half_wave
            if element.component == "half_wave"
            else Retarder.quarter_wave
        )
        return preset(
            read.angle(need("angle_pi"), at("angle_pi")),
            loss=read.scalar(need("loss"), at("loss")),
        )
    if isinstance(element, RotatorElement):
        return Rotator(read.angle(need("rotation_angle_pi"), at("rotation_angle_pi")))
    if isinstance(element, MirrorElement):
        mirror = Mirror(
            reflectivity_h=read.scalar(need("reflectivity_h"), at("reflectivity_h")),
            reflectivity_v=read.scalar(need("reflectivity_v"), at("reflectivity_v")),
            phase_h=read.angle(need("phase_h_pi"), at("phase_h_pi")),
            phase_v=read.angle(need("phase_v_pi"), at("phase_v_pi")),
        )
        flip = element.params.handedness_flip
        return mirror if flip is None else replace(mirror, handedness_flip=flip)
    if isinstance(element, PhaseShifterElement):
        phases = cast(list[object], need("phases_pi"))
        return PhaseShifter(
            tuple(
                read.angle(node, at("phases_pi") + pointer(index))
                for index, node in enumerate(phases)
            )
        )
    if isinstance(element, LossElement):
        efficiencies = cast(list[object], need("efficiencies"))
        return Loss(
            tuple(
                read.scalar(node, at("efficiencies") + pointer(index))
                for index, node in enumerate(efficiencies)
            )
        )
    if isinstance(element, PolarizerElement):
        return Polarizer(
            angle=read.angle(need("angle_pi"), at("angle_pi")),
            pass_transmittance=read.scalar(
                need("pass_transmittance"), at("pass_transmittance")
            ),
            leak_transmittance=read.scalar(
                need("leak_transmittance"), at("leak_transmittance")
            ),
        )
    if isinstance(element, ModeRoutingElement):
        return ModeRouting(tuple(cast(list[int], need("permutation"))))
    assert isinstance(element, GenericBlockElement)
    block = float_matrix(need("block"), read.env, at("block"), conversions)
    return GenericBlock(_square(block, "a C10 block", at("block")))


def _modes(
    measurement: Optical, path: str
) -> tuple[ModeSpace, Callable[[str, str], int]]:
    """Return the declared mode space and the reader of a mode reference.

    A mode is referred to by its label ``<path>_<polarization>``. Two modes
    differing in ``tau`` alone share a label (the receiver's single-value rule
    for ``tau`` is the receiver's to decide), so a reference to such a label
    names no one mode and is refused where it is made.
    """
    check_size(len(measurement.modes), MAX_MODES, "the number of modes", path)
    space = ModeSpace.declare(
        Mode(mode.path, Polarization(mode.polarization), mode.tau)
        for mode in measurement.modes
    )
    positions: dict[str, list[int]] = {}
    for position, mode in enumerate(space.modes):
        positions.setdefault(mode.label, []).append(position)

    def index(label: str, where: str) -> int:
        found = positions.get(label, [])
        if len(found) != 1:
            raise DocumentError(
                f"{label!r} names {len(found)} declared modes; a mode is named by "
                f"its label <path>_<polarization> ({sorted(positions)})",
                reason=DocumentReason.RULE_REFERENCE_UNKNOWN,
                path=where,
            )
        return found[0]

    return space, index


def _pattern_name(fired: Sequence[str]) -> str:
    """Return a click pattern's key in the expansion record: ``{H,V}``."""
    return "{" + ",".join(fired) + "}"


def _coarse_graining(
    measurement: Optical,
    labels: tuple[str, ...],
    environment: Environment,
    path: str,
    table: str,
    *,
    work_bounds: bool,
) -> tuple[ReceiverCoarseGraining, Expansion, dict[str, dict[str, str]]]:
    """Expand the coarse-graining rules over the ``2^K`` click patterns.

    Each pattern binds three variables: ``count``, the number of
    ports that fired; ``port``, the port's label where exactly one fired (and
    nothing otherwise, so a condition on it does not match); and ``fired``,
    whose label is ``{H,V}`` and whose component per port label is ``1`` or
    ``0``. The patterns run in the receiver's own bitmask order, the order
    the common passive receiver's map is written in.
    """
    count = len(labels)
    if work_bounds:
        check_size(count, MAX_PORTS, "the number of detector ports", path + "/ports")
    where = path + "/coarse_graining"
    letters = measurement.coarse_graining.letters
    attributes = {
        letter["label"]: {key: value for key, value in letter.items() if key != "label"}
        for letter in letters
    }
    keys: list[tuple[tuple[str, ...], dict[str, Entry]]] = []
    for mask in range(1 << count):
        fired = tuple(index for index in range(count) if mask & (1 << index))
        name = _pattern_name([labels[index] for index in fired])
        keys.append(
            (
                (name,),
                {
                    "count": Entry.of(str(len(fired))),
                    "port": Entry.of(labels[fired[0]])
                    if len(fired) == 1
                    else Entry.absent(),
                    "fired": Entry.of(
                        name,
                        {
                            label: "1" if index in fired else "0"
                            for index, label in enumerate(labels)
                        },
                    ),
                },
            )
        )
    variables = [
        Variable("count", tuple(Entry.of(str(n)) for n in range(count + 1))),
        Variable("port", tuple(Entry.of(label) for label in labels)),
        Variable(
            "fired",
            (Entry.of("", dict.fromkeys(labels, "0")),),
        ),
    ]
    expansion = expand_bindings(
        table,
        measurement.coarse_graining.map,
        variables,
        keys,
        path=where + "/map",
        environment=environment,
        key_names=("pattern",),
    )
    by_name = {row.key[0]: row.value for row in expansion.rows}
    assignment: dict[frozenset[int], str] = {}
    for mask in range(1 << count):
        fired = tuple(index for index in range(count) if mask & (1 << index))
        name = _pattern_name([labels[index] for index in fired])
        if name in by_name:
            assignment[frozenset(fired)] = str(by_name[name])
    coarse = ReceiverCoarseGraining(
        port_count=count,
        alphabet=tuple(letter["label"] for letter in letters),
        assignment=assignment,
    )
    return coarse, expansion, attributes


def _dark_channel(
    node: object, port_count: int, environment: Environment, path: str
) -> DarkCountChannel:
    """Return a declared ``R`` on ``2^[K]`` (``DarkCountRoute.DECLARED_MATRIX``).

    Rows and columns run over the patterns in the receiver's own order (by
    the number of ports fired, then lexicographically); only the non-zero
    entries are held, as the receiver stores a channel. Whether ``R`` is
    column-stochastic and multiclick-absorbing is the receiver's check.
    """
    rows = matrix(node, environment, path)
    patterns = DarkCountChannel(
        port_count, DarkCountRoute.DECLARED_MATRIX, {}
    ).patterns()
    size = len(patterns)
    if len(rows) != size or any(len(row) != size for row in rows):
        raise DocumentError(
            f"a dark-count channel on {port_count} ports is a {size} x {size} "
            f"matrix over the click patterns; this one is {len(rows)} x "
            f"{len(rows[0]) if rows else 0}",
            reason=DocumentReason.MATRIX_MALFORMED,
            path=path,
        )
    columns: dict[frozenset[int], dict[frozenset[int], Fraction]] = {}
    for j, column in enumerate(patterns):
        entries: dict[frozenset[int], Fraction] = {}
        for i, row in enumerate(patterns):
            value = rows[i][j]
            if value.im != 0:
                raise DocumentError(
                    "a dark-count channel's entries are real probabilities",
                    reason=DocumentReason.MATRIX_MALFORMED,
                    path=path + f"/matrix/{i}/{j}",
                )
            if value.re != 0:
                entries[row] = Fraction(value.re)
        columns[column] = entries
    return DarkCountChannel(port_count, DarkCountRoute.DECLARED_MATRIX, columns)


def receiver_request(
    measurement: Optical,
    environment: Environment,
    path: str,
    *,
    table: str = "coarse_graining",
    work_bounds: bool = True,
) -> LoweredReceiver:
    """Return the station's :class:`ReceiverRequest`.

    ``work_bounds`` is ``False`` for a packaged template only: its photon
    numbers, ports and receiver work are then bounded by its own parameter
    domains, not by :mod:`.limits`.
    """
    read = _Reader(environment, path, work_bounds=work_bounds)
    where = path + "/measurement"
    conversions = Conversions()
    space, index = _modes(measurement, where)
    channel = tuple(
        index(label, where + pointer("channel_modes", i))
        for i, label in enumerate(measurement.channel_modes)
    )
    source = tuple(
        index(label, where + pointer("source_modes", i))
        for i, label in enumerate(measurement.source_modes)
    )
    ports = PortMap(
        tuple(
            (
                port.label,
                tuple(
                    index(mode, where + pointer("ports", p, "modes", m))
                    for m, mode in enumerate(port.modes)
                ),
            )
            for p, port in enumerate(measurement.ports)
        )
    )
    detectors = tuple(
        DetectorPort(
            detector.port,
            read.scalar(
                detector.efficiency, where + pointer("detectors", d, "efficiency")
            ),
            read.scalar(
                detector.dark_count, where + pointer("detectors", d, "dark_count")
            ),
        )
        for d, detector in enumerate(measurement.detectors)
    )
    labels = tuple(port.label for port in measurement.ports)
    coarse, expansion, attributes = _coarse_graining(
        measurement, labels, environment, where, table, work_bounds=work_bounds
    )
    cutoff = read.photons(measurement.photon_cutoff, where + "/photon_cutoff")
    exact_window: dict[str, int] = {}
    tail_window: dict[str, int] = {}
    absent: list[dict[str, str]] = []
    if measurement.exact_window is not None:
        window, window_path = unwrap(
            measurement.exact_window, environment, where + "/exact_window"
        )
        if isinstance(window, ParamRef) and window.port is None:
            # THE ONE FIELD THAT MAY READ AN ABSENT PARAMETER, and only as a
            # bare ``{param: name}``: a window that IS a parameter the
            # configuration does not carry is no window. An expression over an
            # absent parameter is refused as every other one is.
            # The absence is recorded.
            try:
                exact_window[OFF_SETTING] = read.photons(window, window_path)
            except ParameterAbsentError:
                absent.append(
                    {
                        "path": window_path,
                        "parameter": window.param,
                        "read_as": "no exact window",
                    }
                )
        else:
            exact_window[OFF_SETTING] = read.photons(window, window_path)
    declaration = ProbeDeclaration.probe_free()
    settings: tuple[str, ...] = (OFF_SETTING,)
    weights: dict[str, Fraction] = {OFF_SETTING: Fraction(1)}
    if work_bounds:
        _check_work(
            len(labels),
            len(channel) + len(source),
            cutoff,
            max([0, cutoff, *exact_window.values(), *tail_window.values()]),
            where,
        )
    tolerances = _tolerances(measurement, environment, where, bool(exact_window))
    graph: ElementGraph | None = None
    if measurement.route == "element_graph" or measurement.elements:
        graph = ElementGraph(
            tuple(
                GraphElement(
                    element.name,
                    _component(
                        element, read, where + pointer("elements", e), conversions
                    ),
                    tuple(
                        index(mode, where + pointer("elements", e, "support", m))
                        for m, mode in enumerate(element.support)
                    ),
                )
                for e, element in enumerate(measurement.elements)
            ),
            tuple((a, b) for a, b in measurement.edges),
        )
    grams: GramFamily | None = None
    if measurement.port_grams is not None:
        grams = _gram_family(measurement, labels, environment, where, conversions)
    instrument: np.ndarray | None = None
    if measurement.instrument_matrix is not None:
        instrument = float_matrix(
            measurement.instrument_matrix,
            environment,
            where + "/instrument_matrix",
            conversions,
        )
    dark = (
        None
        if measurement.dark_count_channel is None
        else _dark_channel(
            measurement.dark_count_channel,
            len(labels),
            environment,
            where + "/dark_count_channel",
        )
    )
    request = ReceiverRequest(
        mode_space=space,
        input_modes=InputModes(channel=channel, source=source),
        port_map=ports,
        detector_layer=detectors,
        probe_declaration=declaration,
        photon_cutoff=cutoff,
        exact_window=exact_window,
        numerical_tolerances=tolerances,
        outcome_coarse_graining=coarse,
        requested_assurance=Assurance.ESTIMATE,
        port_grams=grams,
        instrument_matrix=instrument,
        element_graph=graph,
        dark_count_channel=dark,
        tail_window=tail_window,
        # receiver/detector-imperfections/req:efficiency-normalization: absent
        # leaves the factored loss to the receiver's default; the receiver
        # decides the declared value's domain and refuses one outside it.
        efficiency_normalization=_efficiency_normalization(
            measurement, environment, read, where
        ),
    )
    letters = coarse.alphabet
    outcomes = tuple(
        Entry.of(
            outcome_label((letter, setting), settings),
            {**attributes.get(letter, {}), "letter": letter, "setting": setting},
        )
        for setting in settings
        for letter in letters
    )
    return LoweredReceiver(
        request=request,
        letters=letters,
        settings=settings,
        class_weights=weights,
        outcomes=outcomes,
        coarse=expansion,
        space=space,
        conversions=conversions.records,
        absent=absent,
        characterisation=_characterisation(measurement, where),
    )


def _efficiency_normalization(
    measurement: Optical,
    environment: Environment,
    read: _Reader,
    where: str,
) -> int | Fraction | None:
    """Return the station's declared factored loss, or ``None`` for the default.

    ``receiver/detector-imperfections/req:efficiency-normalization``. Like the
    exact window, a bare ``{param: name}`` may read a parameter the
    configuration does not carry: a factor that IS a parameter left unset is
    no declaration, and the receiver's default (the largest efficiency
    divided by 99/100, or 1 from 99/100 on) applies. Unlike the window's, the
    absence is NOT listed under ``absent``: leaving the factor unset is the
    ordinary case, and what the receiver did with it is recorded in its
    efficiency record (``req:normalization-record``). Any other node is read
    as a number.
    """
    node = measurement.efficiency_normalization
    if node is None:
        return None
    path = where + "/efficiency_normalization"
    value, value_path = unwrap(node, environment, path)
    if isinstance(value, ParamRef) and value.port is None:
        try:
            return read.scalar(value, value_path)
        except ParameterAbsentError:
            return None
    return read.scalar(value, value_path)


def _characterisation(measurement: Optical, where: str) -> list[tuple[str, str]]:
    """Return what of the station is a declared characterisation, with its path.

    The catalogue entries C1-C9 are physics the receiver derives the
    measurement from; port Grams, an instrument matrix, a C10 block and a
    declared dark-count channel are numbers the engine takes AS the device's
    (Assumption A-TRUST). Each is a premise of the user's.
    """
    found: list[tuple[str, str]] = []
    if measurement.port_grams is not None:
        found.append(("port Grams", where + "/port_grams"))
    if measurement.instrument_matrix is not None:
        found.append(("an instrument matrix", where + "/instrument_matrix"))
    for index, element in enumerate(measurement.elements):
        if isinstance(element, GenericBlockElement):
            found.append(
                (
                    f"the generic block (C10) {element.name!r}",
                    where + pointer("elements", index),
                )
            )
    if measurement.dark_count_channel is not None:
        found.append(("a dark-count channel", where + "/dark_count_channel"))
    return found


def _check_work(ports: int, inputs: int, cutoff: int, deepest: int, where: str) -> None:
    """Refuse a station whose receiver would cost past the bounds (:mod:`.limits`).

    Checked before the request is built, from the integers alone: the cutoff,
    the largest photon-number block, and the receiver's work ``3^K * sum_{n <=
    m} dim(n)^2``.
    """
    check_size(cutoff, MAX_PHOTON_CUTOFF, "the photon cutoff", where + "/photon_cutoff")
    if not inputs:
        return
    check_size(
        photon_blocks(inputs, deepest)[-1],
        MAX_INPUT_BLOCK,
        "the largest photon-number block on the input modes",
        where,
    )
    check_size(
        receiver_work(ports, inputs, deepest),
        MAX_RECEIVER_WORK,
        "the receiver's work, 3^ports times the sum of the squared photon-number "
        "block dimensions up to the deepest window,",
        where,
    )


def _gram_family(
    measurement: Optical,
    labels: tuple[str, ...],
    environment: Environment,
    where: str,
    conversions: Conversions,
) -> GramFamily:
    """Return the declared port Grams, in port-map order, then any other key."""
    declared = measurement.port_grams or {}
    order = [label for label in labels if label in declared]
    order += [label for label in declared if label not in order]
    matrices = tuple(
        _square(
            float_matrix(
                declared[label],
                environment,
                where + pointer("port_grams", label),
                conversions,
            ),
            "a port Gram",
            where + pointer("port_grams", label),
        )
        for label in order
    )
    if len({m.shape for m in matrices}) > 1:
        raise DocumentError(
            "the port Grams act on one space, |Inp| x |Inp|; their shapes "
            f"{sorted({m.shape for m in matrices})} differ",
            reason=DocumentReason.MATRIX_MALFORMED,
            path=where + "/port_grams",
        )
    return GramFamily(tuple(order), matrices)


def _tolerances(
    measurement: Optical, environment: Environment, where: str, window: bool
) -> dict[str, float]:
    """Return the declared tolerances, the common receiver's where none are written.

    ``eps_6`` and ``eps_eig`` are added at their declared default exactly where
    a window is declared and not written, as the common passive receiver adds
    them (``instances.common.optics.receiver_request``): the receiver requires
    them with a window and refuses them without one.
    """
    from instances.common.optics import (
        DECLARED_EXACT_WINDOW_TOLERANCES,
        DECLARED_TOLERANCES,
    )

    if measurement.tolerances is None:
        tolerances = {name: DECLARED_TOLERANCES[name] for name in _DEFAULT_TOLERANCES}
    else:
        check_size(
            len(measurement.tolerances),
            MAX_TOLERANCES,
            "the number of tolerances",
            where + "/tolerances",
        )
        tolerances = {}
        for name, node in measurement.tolerances.items():
            path = where + pointer("tolerances", name)
            written = evaluate_exact(node, environment, path)
            try:
                tolerances[name] = float(written)
            except OverflowError:
                raise DocumentError(
                    f"{node!r} is outside the binary64 range",
                    reason=DocumentReason.EXPRESSION_INVALID,
                    path=path,
                ) from None
    if window:
        for name, value in DECLARED_EXACT_WINDOW_TOLERANCES.items():
            tolerances.setdefault(name, value)
    return tolerances


# ---------------------------------------------------------------------------
#  The reduction
# ---------------------------------------------------------------------------


def device_requests(
    receiver: LoweredReceiver,
    reduction: Reduction,
    environment: Environment,
    path: str,
    *,
    source_mode: SourceMode,
    declared_by: str,
    declared_tolerance: float,
    station: Station | None,
    snap: SnapSettings,
) -> DeviceRequests:
    """Return the station's three declarations, its adapter and its provider.

    The construction ``passive_device_requests`` makes, generalised: the
    reductions' protocol declaration is DERIVED from the measurement (its
    letters, settings, class weights and cutoff), and ``party_label`` and the
    station identity are set on a multi-station document only. The carried
    operators are asked for on a second pass over the first-pass artefact:
    the library's ``two_sector_floor`` (``passive_device.two_sector_provider``) and each
    explicit request, certified against that artefact's squashing channel --
    never against a channel the document names.
    """
    from instances.common.declare import rows_adapter
    from instances.common.passive_device import ACCEPTED_RECEIVER_VERSIONS

    if list(reduction.accepted_receiver_versions) != list(ACCEPTED_RECEIVER_VERSIONS):
        # THE DECLARED SET IS ASSUMPTION A-RECV (reductions/validation.py):
        # widening it is a premise about which receiver contract a run trusts,
        # not a protocol fact, so a document does not move it.
        raise DocumentError(
            "accepted_receiver_versions is the receiver contract version a run "
            f"is written against, {list(ACCEPTED_RECEIVER_VERSIONS)}, and only "
            "that (Assumption A-RECV)",
            reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
            path=path + "/accepted_receiver_versions",
        )
    links, links_path = unwrap(reduction.links, environment, path + "/links")
    declarations = tuple(
        LinkDeclaration(
            stage=LinkStage.RECEIVER,
            kind=LinkKind(link.kind),
            **(
                {}
                if link.requested_status is None
                else {"requested_status": link.requested_status}
            ),
        )
        for link in links
    )
    del links_path
    route, _ = unwrap(reduction.route, environment, path + "/route")
    carried, carried_path = unwrap(
        reduction.carried_operators, environment, path + "/carried_operators"
    )
    optional: dict[str, Any] = {}
    if route is not None:
        optional["route"] = route
    if reduction.squash_before_post_processing is not None:
        optional["squash_before_post_processing"] = (
            reduction.squash_before_post_processing
        )
    if reduction.declared_sector_order is not None:
        optional["declared_sector_order"] = tuple(reduction.declared_sector_order)
    if reduction.declared_occupation_basis_order is not None:
        optional["declared_occupation_basis_order"] = tuple(
            tuple(order) for order in reduction.declared_occupation_basis_order
        )
    if reduction.declared_relations:
        optional["declared_relations"] = tuple(
            (
                tuple(
                    matrix(
                        node, environment, path + pointer("declared_relations", r, 0, m)
                    )
                    for m, node in enumerate(physical)
                ),
                tuple(
                    matrix(
                        node, environment, path + pointer("declared_relations", r, 1, m)
                    )
                    for m, node in enumerate(target)
                ),
            )
            for r, (physical, target) in enumerate(reduction.declared_relations)
        )
    request = ReductionRequest(
        link_declarations=declarations,
        accepted_receiver_versions=tuple(reduction.accepted_receiver_versions),
        requested_assurance="estimate",
        lattice_exponent=reduction.lattice_exponent,
        # THE RUN'S SNAP PARAMETERS, as the instances pass them
        # (``passive_device_requests``): run parameters of the configuration,
        # never of the document.
        strict_snaps=snap.strict,
        reference_enclosure=snap.reference_enclosure,
        **optional,
    )
    settings = receiver.settings
    declaration = ReductionDeclaration(
        probe_declaration=ReductionProbe(
            settings=settings, weights=dict(receiver.class_weights)
        ),
        detection_alphabet=receiver.letters,
        photon_cutoff=receiver.request.photon_cutoff,
        source_mode=source_mode,
        joint_alphabet=tuple(
            (letter, setting) for setting in settings for letter in receiver.letters
        ),
        **({} if station is None else {"party_label": station.party}),
    )
    return DeviceRequests(
        receiver_request=receiver.request,
        reduction_declaration=declaration,
        reduction_entry=reduce_flat,
        reduction_request=request,
        reference_enclosure=snap.reference_enclosure,
        rows_adapter=rows_adapter(
            tolerance=declared_tolerance,
            lattice_exponent=reduction.lattice_exponent,
            settings=snap,
            declared_by=declared_by,
        ),
        carried_operator_provider=_carried(carried, environment, carried_path),
        station=station,
    )


def _carried(
    carried: Sequence[LibraryOperator | ExplicitOperator],
    environment: Environment,
    path: str,
) -> CarriedOperatorProvider | None:
    """Return the second-pass provider of the declared carried operators, or none."""
    from instances.common.passive_device import two_sector_provider

    if not carried:
        return None
    parts: list[
        Callable[[ProofReductionArtifact], tuple[CarriedOperatorRequest, ...]]
    ] = []
    explicit: list[tuple[ExplicitOperator, exact.Matrix, Fraction]] = []
    for index, node in enumerate(carried):
        if isinstance(node, LibraryOperator):
            parts.append(two_sector_provider())
            continue
        where = path + pointer(index)
        explicit.append(
            (
                node,
                matrix(node.operator, environment, where + "/operator"),
                Fraction(number(node.constant, environment, where + "/constant")),
            )
        )

    def requested(
        artifact: ProofReductionArtifact,
    ) -> tuple[CarriedOperatorRequest, ...]:
        return tuple(
            CarriedOperatorRequest(
                label=node.label,
                operator=operator,
                relation=_RELATION[node.relation],
                constant=constant,
                certificate_kind=CertificateKind(node.certificate_kind),
                # THE FIRST-PASS ARTEFACT'S OWN CHANNEL: a request
                # certified against any other is the reductions' refusal, and
                # the document has no way to name one.
                certified_against=artifact.squashing_channel.identity,
                form=ConstraintForm(node.form),
            )
            for node, operator, constant in explicit
        )

    if explicit:
        parts.append(requested)
    if len(parts) == 1:
        return parts[0]

    def provider(
        artifact: ProofReductionArtifact,
    ) -> tuple[CarriedOperatorRequest, ...]:
        return tuple(request for part in parts for request in part(artifact))

    return provider
