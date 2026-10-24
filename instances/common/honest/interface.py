"""What a library honest model is told, and what it must check before it is used.

WHY A CONTEXT AND NOT A DECLARATION. A provider of ``p_honest`` is handed the
compiled declaration and nothing else (``runs.pipeline.HonestProvider``), and
for a qubit model that is enough. A physical model is not: the coherent-pulse
model needs the station's element graph and detectors, the SPDC model the
stations' port Grams, which exist only once the device stage has run. The
protocol document (``instances/declared/``) needs these models without an
instance's wiring, so the facts a model may read
are named here, once, as :class:`HonestContext`: the source, every station's
receiver request, and the device emissions when the run has made them.

WHY PRECONDITIONS. A model that read the declaration BY POSITION (zipping the
emitted letters with a fixed ``("nc", "H", "V", "D", "A", "mc")``, or Alice's
factor alphabet with ``product(RAW_LETTERS, ("gen", "test"))``) would be safe
inside one instance, whose declaration the model's author also wrote. A document that
reorders or renames the coarse-graining would have its honest statistics
mis-attributed without a word. So every model states the structure it models
as :meth:`LibraryModel.preconditions`, checked against the context before any
provider is built, and refused as
:attr:`~instances.declared.errors.DocumentReason.LIBRARY_MODEL_BINDING_INVALID`.

WHY LETTERS ARE READ BY ATTRIBUTE. :func:`letter_classes` decides what each
letter of a station's coarse-graining IS -- no click, one named port, or
several -- from the expanded map itself, never from its spelling, and
:func:`outcome_components` recovers ``(letter, setting, choice)`` of every
emitted label through the engine's own spelling functions
(``reductions.inputs.outcome_label``, ``protocol_compiler.weights.
setting_joint_label``) rather than by parsing it. The models index their
per-port probabilities through these two maps.

Nothing here is proof-critical: an honest model is the simulator side of
spec/architecture.md 4.3, and no proof of secrecy reads it. A wrong one is not
harmless, though: its law may be one no state of the declaration produces
(statistics/ass:reach, A-REACH), and then part of a key length formed against
it is a penalty for that mismatch rather than secrecy
(meat-core/prop:minimal-divergence). The engine's own models are built to
match the declared Alice marginal, and no claim proves their law reached; a
run they feed is checked against the feasible statistics only where the caller
declared a constraint entry (meat-core/req:unreachable-acceptance-set).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, ClassVar, Literal, Protocol

from certiqs_key.protocol_compiler.weights import (
    ChoiceWeighting,
    setting_joint_label,
)
from certiqs_key.receiver.povm import raw_alphabet
from certiqs_key.receiver.request import ReceiverRequest, factored_loss
from certiqs_key.reductions.inputs import outcome_label
from certiqs_key.runs.pipeline import (
    DeviceEmission,
    DeviceRequests,
    HonestProvider,
    RawJointProvider,
)
from certiqs_key.transmitter.decoy import WcpModel
from instances.declared.errors import DocumentError, DocumentReason

__all__ = [
    "MULTI",
    "NONE",
    "HonestContext",
    "LetterClass",
    "LibraryModel",
    "SourceFacts",
    "StationFacts",
    "channel_mode_labels",
    "letter_classes",
    "outcome_components",
    "precondition",
    "station_from_device",
]

#: The two letter classes that are not a port: the empty pattern, and every
#: pattern with two or more ports.
NONE: Literal["none"] = "none"
MULTI: Literal["multi"] = "multi"

#: What one letter of a canonical coarse-graining is: ``("none", None)``,
#: ``("port", label)`` or ``("multi", None)``.
type LetterClass = tuple[str, str | None]

type StationKind = Literal["declared_povm", "optical"]
type SourceKind = Literal["trusted", "untrusted", "wcp_decoy"]


@dataclass(frozen=True)
class SourceFacts:
    """What a model may read about the source: its kind, ``d_A``, its alphabet.

    ``wcp`` is the declared weak-coherent model of a ``wcp_decoy`` source and
    ``None`` otherwise. ``alice_dim`` is ``None`` where ``d_A`` is not a
    declared number but the dimension of the register the transmitter emits
    (a ``wcp_decoy`` source's tagged register), which no model reads.
    """

    kind: SourceKind
    alice_dim: int | None
    alphabet: tuple[str, ...] = ()
    wcp: WcpModel | None = None


@dataclass(frozen=True)
class StationFacts:
    """What a model may read about one station.

    A ``declared_povm`` station carries its ``dimension``; an ``optical`` one
    carries its whole :class:`~certiqs_key.receiver.request.ReceiverRequest`,
    the object the device stage is given, so the model reads the mode space,
    ports, detectors, probe settings, cutoff, coarse-graining and element graph
    the receiver itself reads. ``choice_weighting`` is the station's declared
    choice weighting (bbm92's test coin), where it has one.
    """

    id: str
    party: str
    kind: StationKind
    dimension: int | None = None
    request: ReceiverRequest | None = None
    choice_weighting: ChoiceWeighting | None = None

    @property
    def photon_cutoff(self) -> int | None:
        """Return the station's photon cutoff ``N``; ``None`` off the optical route."""
        return None if self.request is None else self.request.photon_cutoff

    @property
    def port_labels(self) -> tuple[str, ...]:
        """Return the detector port labels, in the port map's declared order."""
        return () if self.request is None else self.request.port_map.labels

    @property
    def settings(self) -> tuple[str, ...]:
        """Return the probe settings ``T`` of the station's receiver."""
        if self.request is None:
            return ()
        return self.request.probe_declaration.labels

    @property
    def factored_loss(self) -> Fraction:
        """Return the factored loss ``t`` the station's receiver is compiled at.

        ``receiver/detector-imperfections/req:loss-before-evaluation``: where
        ``t < 1`` the emitted measurement is the NORMALIZED station's, and a
        model that evaluates it on a state standing for this station's input
        applies the pure-loss channel of transmittance ``t`` to that input
        first. Read through the receiver's own
        :func:`~certiqs_key.receiver.request.factored_loss`, the decision the
        device stage makes on the same request, so the two cannot disagree.
        ``1`` off the optical route, where no receiver is compiled.

        READ IT INSIDE A PROVIDER, never while building one. A declared factor
        outside ``[eta_max, 1]`` raises ``HypothesisError`` here; the run calls
        a provider only after the device stage has refused such a factor with
        ``efficiency_normalization_out_of_range``
        (``req:efficiency-normalization``), so a model that reads ``t`` when it
        is called gives that refusal on every instance, and one that read it
        while the document is lowered would raise instead.
        """
        if self.request is None:
            return Fraction(1)
        return factored_loss(self.request)


def station_from_device(
    device: DeviceRequests,
    *,
    id: str | None = None,
    party: str | None = None,
    choice_weighting: ChoiceWeighting | None = None,
) -> StationFacts:
    """Return the facts of an optical station from the requests a run is given.

    Read from the SAME :class:`~certiqs_key.runs.pipeline.DeviceRequests` the
    device stage runs on, so the model and the receiver cannot be told two
    different devices. ``id`` and ``party`` default to the request's declared
    station, and a single-station run without one is Bob's ``"bob"``.
    """
    station = device.station
    return StationFacts(
        id=id if id is not None else ("bob" if station is None else station.factor),
        party=party
        if party is not None
        else ("B" if station is None else station.party),
        kind="optical",
        request=device.receiver_request,
        choice_weighting=choice_weighting,
    )


@dataclass
class HonestContext:
    """Everything a library model may read, filled as the run's stages run.

    ``instance`` is the record label the note carries. ``declared_tolerance``
    is the run's ``tau``, which a model that declares data of its own (the SPDC
    model's port Grams) spends exactly as an instance would. ``note`` is the
    live honest-model note a model may extend once it has run (the SPDC
    model's Gram preparation record). ``emissions`` is set by the
    specification provider through :meth:`set_emissions` when the device stage
    has run; a model that needs them registers with :meth:`on_emissions`.
    """

    instance: str
    stations: tuple[StationFacts, ...]
    source: SourceFacts | None = None
    declared_tolerance: float = 0.0
    note: dict[str, Any] | None = None
    emissions: tuple[DeviceEmission, ...] | None = None
    _listeners: list[Callable[[tuple[DeviceEmission, ...]], None]] = field(
        default_factory=list, init=False, repr=False
    )

    def station(self, station_id: str) -> StationFacts:
        """Return the station whose id is ``station_id``."""
        for station in self.stations:
            if station.id == station_id:
                return station
        raise KeyError(f"no station {station_id!r} in {[s.id for s in self.stations]}")

    def on_emissions(
        self, listener: Callable[[tuple[DeviceEmission, ...]], None]
    ) -> None:
        """Run ``listener`` when the device emissions are set."""
        self._listeners.append(listener)

    def set_emissions(self, emissions: tuple[DeviceEmission, ...]) -> None:
        """Record the device emissions and run every registered listener, in order."""
        self.emissions = emissions
        for listener in self._listeners:
            listener(emissions)


class LibraryModel(Protocol):
    """The uniform interface of a library honest model.

    ``parameters`` are the names a document's ``bind`` must give, exactly.
    ``preconditions`` refuses a context whose structure the model does not
    model; ``providers`` returns the acceptance-alphabet provider and the raw
    ``X x V`` provider (``None`` where the model has none). ``note`` is the
    honest-model note a record carries for this model, with ``instance`` taken
    from the context.
    """

    name: ClassVar[str]
    parameters: ClassVar[tuple[str, ...]]

    def note(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> dict[str, Any]:
        """Return the honest-model note of this model."""
        ...

    def preconditions(self, context: HonestContext) -> None:
        """Refuse a context whose structure this model does not model."""
        ...

    def providers(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> tuple[HonestProvider, RawJointProvider | None]:
        """Return the honest and raw providers at these parameters."""
        ...


def precondition(model: str, holds: bool, detail: str) -> None:
    """Refuse with ``library_model_binding_invalid`` unless ``holds``."""
    if not holds:
        raise DocumentError(
            f"the honest model {model!r} does not model this protocol: {detail}",
            reason=DocumentReason.LIBRARY_MODEL_BINDING_INVALID,
            path="/honest",
        )


def channel_mode_labels(station: StationFacts) -> tuple[str, str] | None:
    """Return the ``(H, V)`` channel mode labels of one path, or ``None``.

    ``None`` unless the station's channel modes are exactly two, on one path,
    with the polarizations ``H`` and ``V``: the encoding every library optical
    model assumes, read from the declared modes rather than from their labels.
    """
    if station.request is None:
        return None
    space = station.request.mode_space
    modes = [space.modes[index] for index in station.request.input_modes.channel]
    if len(modes) != 2 or modes[0].path != modes[1].path:
        return None
    by_polarization = {str(mode.polarization): mode.label for mode in modes}
    if set(by_polarization) != {"H", "V"}:
        return None
    return by_polarization["H"], by_polarization["V"]


def letter_classes(station: StationFacts) -> dict[str, LetterClass] | None:
    """Return what each coarse-graining letter is, or ``None`` if not canonical.

    CANONICAL means the expanded map sends the empty pattern to one
    letter, each single-port pattern to a letter of its own, and every pattern
    with two or more ports to one further letter. It is decided on the
    expansion -- the receiver's ``assignment`` over all ``2^K`` patterns -- and
    never on the letters' names: a document is free to call its letters
    anything, and a model reads which port a letter is from the map.
    """
    if station.request is None:
        return None
    coarse = station.request.outcome_coarse_graining
    ports = station.port_labels
    if coarse.port_count != len(ports):
        return None
    classes: dict[str, LetterClass] = {}
    for pattern in raw_alphabet(coarse.port_count):
        letter = coarse.assignment.get(pattern)
        if letter is None:
            return None
        if not pattern:
            kind: LetterClass = (NONE, None)
        elif len(pattern) == 1:
            kind = ("port", ports[next(iter(pattern))])
        else:
            kind = (MULTI, None)
        if classes.setdefault(letter, kind) != kind:
            return None
    if len(set(classes.values())) != len(classes) or set(classes) != set(
        coarse.alphabet
    ):
        return None
    return classes


def outcome_components(
    station: StationFacts,
) -> dict[str, tuple[str, str, str | None]]:
    """Return ``{emitted label: (letter, setting, choice)}`` of one station.

    The labels are SPELT by the engine's own functions and never parsed:
    ``outcome_label`` joins a letter and a probe setting into the station's
    ``V``, and where the station declares a choice weighting,
    ``setting_joint_label`` joins each ``v`` with each choice of positive
    weight -- the support ``setting_weighted_family`` emits. ``choice`` is
    ``None`` on a station without a weighting.
    """
    if station.request is None:
        return {}
    settings = station.settings
    letters = station.request.outcome_coarse_graining.alphabet
    plain = {
        outcome_label((letter, setting), settings): (letter, setting)
        for letter in letters
        for setting in settings
    }
    weighting = station.choice_weighting
    if weighting is None:
        return {
            label: (letter, setting, None) for label, (letter, setting) in plain.items()
        }
    out: dict[str, tuple[str, str, str | None]] = {}
    for v, (letter, setting) in plain.items():
        for choice in weighting.choice_alphabet:
            if weighting.weight(weighting.setting_of[v], choice) > 0:
                out[setting_joint_label(v, choice)] = (letter, setting, choice)
    return out
