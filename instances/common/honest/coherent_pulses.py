"""Library model ``coherent_pulses``: physical clicks of weak coherent pulses.

THE DECOY MODEL, generalised only as far as data allows: the click
law reads a station's declared element graph, mode space, ports and detectors
(its :class:`~certiqs_key.receiver.request.ReceiverRequest`) in place of
``common.optics.element_graph(parameters)`` and ``mode_space()``, and each
letter's Jones vector from its polarisation's declared ``part``. For the decoy
instance these are the same objects, so its numbers do not move.

THE MODEL. The optical graph supplies the passive transfer amplitudes. A fixed
real polarization rotation models misalignment. Independent Poisson arrivals
and dark counts give per-port no-click probabilities (1-d_k) exp(-eta_k mu_k).
Exponentials and pattern products use Decimal precision 60. This is the honest
model, not a proof-critical enclosure or a bound on an implementation error.

LETTERS BY ATTRIBUTE. The raw table does not zip the emitted letters with a
fixed ``("nc", "H", "V", "D", "A", "mc")``; it asks the
station's coarse-graining which letter is the empty pattern, which is a single
port and which is every multi-port pattern
(:func:`~instances.common.honest.interface.letter_classes`), so a document
that orders or names its letters otherwise is attributed correctly or refused.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any, ClassVar, cast

import numpy as np

from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.protocol_compiler.spec import PublicPart
from certiqs_key.receiver.graph import ElementGraph, compile_element_graph
from certiqs_key.receiver.modes import ModeSpace
from certiqs_key.runs.pipeline import (
    HonestProvider,
    RawJointProvider,
    factored_loss_applied,
    raw_factored_loss_applied,
)
from certiqs_key.transmitter.decoy import WcpModel
from instances.common.honest.interface import (
    MULTI,
    NONE,
    HonestContext,
    StationFacts,
    channel_mode_labels,
    letter_classes,
    outcome_components,
    precondition,
)
from instances.common.honest.tables import aggregate
from instances.common.optics import PORTS, ReceiverParameters, element_graph, mode_space

__all__ = [
    "JONES",
    "MODEL",
    "CoherentPulses",
    "acceptance_distribution",
    "click_distribution",
    "port_clicks",
    "raw_distribution",
]

#: The real Jones vector ``(h, v)`` of each polarisation ``part`` the WCP
#: model declares (``WcpModel.polarisation_parts``).
JONES: Mapping[str, tuple[float, float]] = {
    "H": (1.0, 0.0),
    "V": (0.0, 1.0),
    "+": (math.sqrt(0.5), math.sqrt(0.5)),
    "-": (math.sqrt(0.5), -math.sqrt(0.5)),
}

#: The decoy instance's polarisation names, and the part each one is.
_PART_OF_NAME: Mapping[str, str] = {"H": "H", "V": "V", "plus": "+", "minus": "-"}


def port_clicks(
    graph: ElementGraph,
    space: ModeSpace,
    ports: Sequence[tuple[str, tuple[int, ...]]],
    efficiency: Sequence[Fraction],
    dark_count: Sequence[Fraction],
    channel: tuple[int, int],
    *,
    intensity: Fraction,
    jones: tuple[float, float],
    transmittance: Fraction,
    misalignment: Fraction,
) -> tuple[Fraction, dict[str, Fraction], Fraction]:
    """Return ``(no click, {port: exactly that port}, two or more)``, summing to one.

    ``channel`` is the pair of mode indices ``(H, V)`` the pulse enters on, and
    ``ports`` the port map's ``(label, mode indices)`` in declared order, with
    one efficiency and one dark-count probability per port.
    """
    if (
        intensity < 0
        or not 0 <= transmittance <= 1
        or not 0 <= misalignment <= Fraction(1, 2)
    ):
        raise ValueError("invalid coherent channel parameters")
    h, v = jones
    c, s = math.sqrt(1 - float(misalignment)), math.sqrt(float(misalignment))
    vector = np.zeros(len(space.modes), dtype=complex)
    vector[channel[0]], vector[channel[1]] = c * h - s * v, s * h + c * v
    output = compile_element_graph(graph, len(space.modes)) @ vector
    with localcontext() as context:
        context.prec = 60
        scale = Decimal(intensity.numerator) / Decimal(intensity.denominator)
        scale *= Decimal(transmittance.numerator) / Decimal(transmittance.denominator)
        no_click = []
        for (_, modes), eta, dark in zip(ports, efficiency, dark_count, strict=True):
            power = Decimal(0)
            for index, mode in enumerate(modes):
                amplitude = output[mode]
                term = (
                    Decimal(float(amplitude.real)) ** 2
                    + Decimal(float(amplitude.imag)) ** 2
                )
                power = term if index == 0 else power + term
            efficiency_k = Decimal(eta.numerator) / Decimal(eta.denominator)
            dc = Decimal(dark.numerator) / Decimal(dark.denominator)
            no_click.append(Fraction((1 - dc) * (-efficiency_k * scale * power).exp()))
        vacuum = Fraction(math.prod(no_click))
        singles: dict[str, Fraction] = {}
        for index, (label, _) in enumerate(ports):
            value = (1 - no_click[index]) * math.prod(
                q for j, q in enumerate(no_click) if j != index
            )
            singles[label] = Fraction(value)
        # The complement includes every pattern with at least two clicks;
        # Exact rational subtraction keeps the evaluated model normalized.
        multi = 1 - sum((vacuum, *singles.values()), Fraction())
        if multi < 0:
            raise ArithmeticError("coherent probability evaluation lost positivity")
        return vacuum, singles, multi


def click_distribution(
    parameters: ReceiverParameters,
    *,
    intensity: Fraction,
    polarisation: str,
    transmittance: Fraction,
    misalignment: Fraction,
) -> dict[str, Fraction]:
    """Return nc, four single clicks and mc on the common passive receiver.

    The decoy instance's own form, kept for its tests: the receiver is
    :mod:`instances.common.optics`'s, and ``polarisation`` is one of its names
    ``H``, ``V``, ``plus``, ``minus``.
    """
    space = mode_space()
    at = {mode.label: i for i, mode in enumerate(space.modes)}
    vacuum, singles, multi = port_clicks(
        element_graph(parameters),
        space,
        tuple((label, tuple(at[m] for m in modes)) for label, modes in PORTS),
        parameters.efficiency,
        parameters.dark_count,
        (at["Z_H"], at["Z_V"]),
        intensity=intensity,
        jones=JONES[_PART_OF_NAME[polarisation]],
        transmittance=transmittance,
        misalignment=misalignment,
    )
    return {"nc": vacuum, **singles, "mc": multi}


def raw_distribution(
    model: WcpModel,
    station: StationFacts,
    emitted: tuple[str, ...],
    *,
    transmittance: Fraction,
    misalignment: Fraction,
) -> dict[tuple[str, str], Fraction]:
    """Evaluate the physical model for every declared source letter.

    Each emitted label is read as ``(letter, setting, choice)`` and each
    letter as no click, one port or several, by attribute; the preconditions
    of :class:`CoherentPulses` guarantee both maps exist.
    """
    request = station.request
    classes = letter_classes(station)
    channel = channel_mode_labels(station)
    precondition(
        CoherentPulses.name,
        request is not None
        and request.element_graph is not None
        and classes is not None
        and channel is not None,
        "the station is not an element-graph receiver with H/V channel modes "
        "and a canonical coarse-graining",
    )
    assert request is not None and classes is not None and channel is not None
    components = outcome_components(station)
    labels = [mode.label for mode in request.mode_space.modes]
    detectors = request.detector_layer
    result = {}
    for letter in model.alphabet:
        vacuum, singles, multi = port_clicks(
            cast(ElementGraph, request.element_graph),
            request.mode_space,
            request.port_map.entries,
            tuple(cast(Fraction, port.efficiency) for port in detectors),
            tuple(cast(Fraction, port.dark_count_probability) for port in detectors),
            (labels.index(channel[0]), labels.index(channel[1])),
            intensity=model.intensities[letter.intensity],
            jones=JONES[model.polarisation_parts[letter.polarisation]],
            transmittance=transmittance,
            misalignment=misalignment,
        )
        for v in emitted:
            kind, port = classes[components[v][0]]
            probability = (
                vacuum
                if kind == NONE
                else multi
                if kind == MULTI
                else singles[cast(str, port)]
            )
            result[letter.label, v] = model.weights[letter.label] * probability
    return result


def acceptance_distribution(
    public: PublicPart,
    raw: dict[tuple[str, str], Fraction],
) -> dict[str, Fraction]:
    """Push the honest raw table through exactly the declared transcript."""
    assert public.transcript is not None and public.accept_statistic_general is not None
    result = dict.fromkeys(public.acceptance_alphabet, Fraction())
    first, second = public.transcript.messages
    for (x, v), probability in raw.items():
        a = first.table[x, ()]
        b = second.table[v, (a,)]
        result[public.accept_statistic_general[a, b]] += probability
    return result


class CoherentPulses:
    """The library entry: a WCP decoy source into one passive optical station.

    PRECONDITIONS: a ``wcp_decoy`` source whose every
    polarisation's part is one of ``H``, ``V``, ``+``, ``-``; one optical
    station whose channel modes are the ``H`` and ``V`` modes of one path, with
    a canonical coarse-graining. Two more, because the click law has no term
    for them and would otherwise be silently wrong: the station declares no
    probe (source) modes, and no choice weighting.
    """

    name: ClassVar[str] = "coherent_pulses"
    parameters: ClassVar[tuple[str, ...]] = ("transmittance", "misalignment")

    def note(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> dict[str, Any]:
        """Return decoy BB84's note, with ``instance`` from the context."""
        return {
            "instance": context.instance,
            "module": __name__,
            "model": (
                "coherent port clicks with optical loss and polarization rotation; "
                "Decimal precision 60"
            ),
            "overridden": False,
        }

    def preconditions(self, context: HonestContext) -> None:
        """Refuse anything but WCP pulses into one canonical H/V passive station."""
        source = context.source
        wcp = None if source is None else source.wcp
        precondition(
            self.name,
            source is not None and source.kind == "wcp_decoy" and wcp is not None,
            "it models weak coherent pulses, so it needs a wcp_decoy source",
        )
        assert wcp is not None
        parts = {pol: wcp.polarisation_parts.get(pol) for pol in wcp.polarisations}
        precondition(
            self.name,
            all(part in JONES for part in parts.values()),
            f"every polarisation's part must be one of {sorted(JONES)}; got {parts}",
        )
        precondition(
            self.name,
            len(context.stations) == 1 and context.stations[0].kind == "optical",
            "it models one receiver, so it needs exactly one optical station",
        )
        station = context.stations[0]
        assert station.request is not None
        precondition(
            self.name,
            station.request.element_graph is not None,
            "the click law propagates the pulse through the station's element "
            "graph, so the receiver must be declared by one (not by port Grams "
            "or an instrument matrix)",
        )
        precondition(
            self.name,
            channel_mode_labels(station) is not None,
            "the pulse's polarization is written into the H and V modes of one "
            "path, so the station's channel modes must be exactly those two",
        )
        precondition(
            self.name,
            not station.request.input_modes.source,
            "the click law has no term for a probe, so the station must declare "
            "no source modes",
        )
        precondition(
            self.name,
            station.choice_weighting is None,
            "the click law has no term for a choice coin, so the station must "
            "declare no choice weighting",
        )
        precondition(
            self.name,
            letter_classes(station) is not None,
            "its letters are read by attribute, so the coarse-graining must be "
            "canonical: the empty pattern to one letter, each single port to a "
            "letter of its own, every multi-port pattern to one further letter",
        )

    def providers(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> tuple[HonestProvider, RawJointProvider | None]:
        """Return the raw table over the declared letters and its aggregation."""
        assert context.source is not None and context.source.wcp is not None
        wcp = context.source.wcp
        station = context.stations[0]
        transmittance = cast(Fraction, bound["transmittance"])
        misalignment = cast(Fraction, bound["misalignment"])

        def raw(declaration: CandidateDeclaration) -> dict[tuple[str, str], Fraction]:
            return raw_distribution(
                wcp,
                station,
                declaration.bob_alphabet,
                transmittance=transmittance,
                misalignment=misalignment,
            )

        # receiver/detector-imperfections/req:loss-before-evaluation holds
        # without a factor here: the click law reads the DECLARED device --
        # the station's element graph and its declared detector efficiencies
        # -- and never the emitted (possibly normalized) measurement, so its
        # law is the device's whatever factored loss the receiver carries.
        return factored_loss_applied(aggregate(raw)), raw_factored_loss_applied(raw)


#: The one instance of this model the registry holds.
MODEL = CoherentPulses()
