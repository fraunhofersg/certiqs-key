"""Library model ``spdc_pair``: rational threshold statistics of polarization SPDC.

ONE MODEL for bbm92 and a protocol document, with the raw
``X x V`` table. The Gram preparation keeps its
recorded site ``instances.bbm92.spdc.port_grams``: it names a snap in every
bbm92 record, and a record of the same declaration must not change.

The source is two equal-phase two-mode squeezed vacua, A_H--B_H and
A_V--B_V, each with mean photon number n. The mean emitted pair number is
2n. The no-click determinant reduces to a rational 2x2 determinant; see
``pair_models.md`` beside this module for the newly-derived reduction and its
conventions.

LETTERS BY ATTRIBUTE. The raw table does not zip Alice's factor alphabet with
``product(RAW_LETTERS, ("gen", "test"))``; it reads
each factor label's ``(letter, setting, choice)`` through the engine's own
spelling functions (:func:`~instances.common.honest.interface.
outcome_components`), each factor's station by its label, each arm by its
station's party, and the coin weight of a choice from the station's declared
choice weighting -- never from the names ``gen`` and ``test``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Any, ClassVar, cast

import numpy as np

from certiqs_key.foundations.blocks import PRODUCT_LABEL_SEPARATOR
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    add,
    identity,
    matmul,
    scale,
    subtract,
    zeros,
)
from certiqs_key.foundations.snap import snap_family_exact
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
from certiqs_key.reductions.inputs import outcome_label
from certiqs_key.runs.pipeline import (
    DeviceEmission,
    HonestProvider,
    RawJointProvider,
    factored_loss_applied,
    raw_factored_loss_applied,
)
from instances.common.honest.ideal_pair import PAIR_NOTE, pair_preconditions
from instances.common.honest.interface import (
    HonestContext,
    StationFacts,
    letter_classes,
    outcome_components,
    precondition,
)
from instances.common.honest.tables import aggregate

__all__ = [
    "MODEL",
    "SpdcModel",
    "SpdcPair",
    "click_distribution",
    "coarse_distribution",
    "no_click_probability",
    "prepare_station_grams",
]


@dataclass(frozen=True)
class SpdcModel:
    """Equal-squeezing SPDC with independent arm attenuation."""

    mean_pairs: Fraction = Fraction(1, 32)
    alice_transmittance: Fraction = Fraction(1)
    bob_transmittance: Fraction = Fraction(1)

    def __post_init__(self) -> None:
        """Validate source brightness and arm probabilities."""
        for name in ("mean_pairs", "alice_transmittance", "bob_transmittance"):
            if not isinstance(getattr(self, name), Fraction):
                raise ValueError(f"{name} must be an exact rational model parameter")
        if self.mean_pairs < 0:
            raise ValueError("SPDC mean_pairs must be nonnegative")
        for value in (self.alice_transmittance, self.bob_transmittance):
            if not 0 <= value <= 1:
                raise ValueError("SPDC arm transmittance lies in [0, 1]")


def no_click_probability(
    a: Matrix, b: Matrix, mean_per_polarization: Fraction
) -> Fraction:
    """Return the exact vacuum probability for local detected Gram sums A,B."""
    bt = tuple(tuple(b[j][i] for j in range(2)) for i in range(2))
    denominator = add(
        identity(2),
        scale(mean_per_polarization, subtract(add(a, bt), matmul(a, bt))),
    )
    determinant = (
        denominator[0][0] * denominator[1][1] - denominator[0][1] * denominator[1][0]
    )
    if determinant.im != 0 or determinant.re < 1:
        raise ValueError("SPDC no-click determinant is not a real number at least one")
    return 1 / determinant.re


def prepare_station_grams(
    artifact: ReceiverMeasurementArtifact,
    *,
    tolerance: float,
    lattice_exponent: int = 40,
) -> tuple[tuple[Matrix, ...], dict[str, Any]]:
    """Declare a physical two-mode optical Gram family for the honest model.

    Four detected ports plus their loss completion form a POVM on the input
    polarization space. The shared preparation supplies exact positivity and
    completeness. This changes only the declared honest channel model; no
    key-rate continuity statement is made about its measured displacement.
    """
    if (
        len(artifact.input_mode_space.channel_labels) != 2
        or artifact.input_mode_space.source_labels
    ):
        raise ValueError("the SPDC model needs two channel modes and no probe modes")
    grams = [np.asarray(value, dtype=np.complex128) for _, value in artifact.port_grams]
    if len(grams) != 4 or any(gram.shape != (2, 2) for gram in grams):
        raise ValueError("the SPDC station must carry four two-mode port Grams")
    completion = np.eye(2, dtype=np.complex128) - sum(
        grams, np.zeros((2, 2), dtype=np.complex128)
    )
    prepared, records = snap_family_exact(
        [*grams, completion],
        tolerance=tolerance,
        lattice_exponent=lattice_exponent,
        site="instances.bbm92.spdc.port_grams",
    )
    return tuple(
        tuple(
            tuple(Cx(Fraction(float(z.real)), Fraction(float(z.imag))) for z in row)
            for row in gram
        )
        for gram in prepared[:-1]
    ), {
        "site": "instances.bbm92.spdc.port_grams",
        "declared_tolerance": tolerance,
        "lattice_exponent": lattice_exponent,
        "port_order": [label for label, _ in artifact.port_grams],
        "snaps": [record.as_record() for record in records],
        "meaning": "honest optical model declaration; no key-rate continuity claim",
    }


def click_distribution(
    alice_grams: Sequence[Matrix],
    bob_grams: Sequence[Matrix],
    model: SpdcModel,
    *,
    alice_dark: Sequence[Fraction],
    bob_dark: Sequence[Fraction],
) -> dict[tuple[int, int], Fraction]:
    """Return all 16x16 threshold-pattern probabilities, exactly.

    Bit k means port k clicked. Efficiencies are already in the port Grams;
    arm attenuation multiplies their local sums once. Independent per-port
    dark counts multiply no-click probabilities before inclusion-exclusion.
    """
    if len(alice_grams) != 4 or len(bob_grams) != 4:
        raise ValueError("each station needs four port Grams")
    dark = tuple(alice_dark) + tuple(bob_dark)
    if len(dark) != 8 or any(not 0 <= value <= 1 for value in dark):
        raise ValueError("eight independent dark-count probabilities are required")
    local_sums = []
    for grams, transmittance in (
        (alice_grams, model.alice_transmittance),
        (bob_grams, model.bob_transmittance),
    ):
        sums = []
        for mask in range(16):
            block = zeros(2)
            for i, gram in enumerate(grams):
                if mask & (1 << i):
                    block = add(block, gram)
            sums.append(scale(transmittance, block))
        local_sums.append(sums)
    vacuum = {}
    for mask in range(256):
        probability = no_click_probability(
            local_sums[0][mask & 15], local_sums[1][mask >> 4], model.mean_pairs / 2
        )
        for i, value in enumerate(dark):
            if mask & (1 << i):
                probability *= 1 - value
        vacuum[mask] = probability
    result = {}
    for clicks in range(256):
        nonclicks = 255 ^ clicks
        subset = clicks
        probability = Fraction(0)
        while True:
            probability += (-1 if subset.bit_count() % 2 else 1) * vacuum[
                nonclicks | subset
            ]
            if subset == 0:
                break
            subset = (subset - 1) & clicks
        if probability < 0:
            raise ValueError("exact SPDC pattern probability is negative")
        result[(clicks & 15, clicks >> 4)] = probability
    if sum(result.values(), Fraction(0)) != 1:
        raise AssertionError("SPDC inclusion-exclusion lost normalization")
    return result


def coarse_distribution(
    patterns: Mapping[tuple[int, int], Fraction],
    alice: ReceiverMeasurementArtifact,
    bob: ReceiverMeasurementArtifact,
) -> dict[tuple[str, str], Fraction]:
    """Apply each station's emitted coarse-graining to the exact pattern table."""
    maps = []
    for artifact in (alice, bob):
        ports = {label: i for i, (label, _) in enumerate(artifact.port_grams)}
        maps.append(
            {
                sum(1 << ports[label] for label in pattern): outcome
                for outcome, fibre in artifact.outcome_alphabet.fibres
                for pattern in fibre
            }
        )
    out = {
        pair: Fraction(0)
        for pair in product(
            dict.fromkeys(maps[0].values()), dict.fromkeys(maps[1].values())
        )
    }
    for (left, right), probability in patterns.items():
        out[(maps[0][left], maps[1][right])] += probability
    return out


def _emission_of(
    emissions: tuple[DeviceEmission, ...], station: StationFacts, position: int
) -> DeviceEmission:
    """Return the emission of ``station``: by its declared factor, else its position.

    The positional fallback applies only to an emission that declares no
    station at all (``DeviceEmission.station is None``); every multi-station
    run declares one per request, and then the factor label decides.
    """
    for emission in emissions:
        if emission.station is not None and emission.station.factor == station.id:
            return emission
    return emissions[position]


class SpdcPair:
    """The library entry ``spdc_pair``: SPDC pairs into two passive stations.

    PRECONDITIONS: those of ``ideal_pair``; a canonical
    coarse-graining on both stations; a choice weighting on exactly one
    station, with one setting. Two more, because the Gram preparation and the
    click law are written for them and would otherwise fail inside a run: each
    station has four detector ports and declares no source (probe) modes.

    The stations' port Grams exist only once the device stage has run, so the
    exact pattern table is computed when the specification provider hands the
    emissions to the context (:meth:`HonestContext.set_emissions`), at the
    point bbm92 computed it, and the Gram preparation record is added to the
    live note there.
    """

    name: ClassVar[str] = "spdc_pair"
    parameters: ClassVar[tuple[str, ...]] = (
        "mean_pairs",
        "alice_transmittance",
        "bob_transmittance",
    )

    def note(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> dict[str, Any]:
        """Return bbm92's note shape for this model."""
        return {"model": "spdc", **PAIR_NOTE}

    def preconditions(self, context: HonestContext) -> None:
        """Refuse anything but SPDC pairs into two canonical passive stations."""
        pair_preconditions(self.name, context)
        for station in context.stations:
            assert station.request is not None
            precondition(
                self.name,
                len(station.port_labels) == 4,
                f"station {station.id!r}: the click law is written for four "
                f"detector ports; got {len(station.port_labels)}",
            )
            precondition(
                self.name,
                not station.request.input_modes.source,
                f"station {station.id!r}: the Gram preparation has no term for a "
                "probe, so the station must declare no source modes",
            )
            precondition(
                self.name,
                letter_classes(station) is not None,
                f"station {station.id!r}: its letters are read by attribute, so "
                "the coarse-graining must be canonical: the empty pattern to one "
                "letter, each single port to a letter of its own, every "
                "multi-port pattern to one further letter",
            )
        weighted = [s for s in context.stations if s.choice_weighting is not None]
        precondition(
            self.name,
            len(weighted) == 1
            and len(weighted[0].choice_weighting.setting_alphabet) == 1,  # type: ignore[union-attr]
            "the test coin is one station's choice, so exactly one station must "
            "declare a choice weighting, with one setting",
        )

    def providers(
        self, bound: Mapping[str, Fraction | str], context: HonestContext
    ) -> tuple[HonestProvider, RawJointProvider | None]:
        """Return the raw table over both factors and its aggregation."""
        model = SpdcModel(
            cast(Fraction, bound["mean_pairs"]),
            cast(Fraction, bound["alice_transmittance"]),
            cast(Fraction, bound["bob_transmittance"]),
        )
        alice = next(s for s in context.stations if s.party == "A")
        bob = next(s for s in context.stations if s.party == "B")
        state: dict[str, Mapping[tuple[str, str], Fraction]] = {}

        def dark(station: StationFacts) -> tuple[Fraction, ...]:
            assert station.request is not None
            return tuple(
                cast(Fraction, port.dark_count_probability)
                for port in station.request.detector_layer
            )

        def prepare(emissions: tuple[DeviceEmission, ...]) -> None:
            first = _emission_of(emissions, alice, context.stations.index(alice))
            second = _emission_of(emissions, bob, context.stations.index(bob))
            a, ar = prepare_station_grams(
                first.receiver, tolerance=context.declared_tolerance
            )
            b, br = prepare_station_grams(
                second.receiver, tolerance=context.declared_tolerance
            )
            # receiver/detector-imperfections/req:loss-before-evaluation: the
            # emitted Grams are the NORMALIZED station's where a receiver was
            # compiled at t < 1. The pure-loss channel in front pulls each
            # no-click element F(1 - A'_J) back to F(1 - t A'_J)
            # (lem:pure-loss-lift), so the device's law is the click law at the
            # Grams times t -- which is the arm attenuation times t, the law
            # multiplying each local sum by the arm transmittance once. Each
            # station with the t of its own record.
            device = SpdcModel(
                model.mean_pairs,
                model.alice_transmittance * _factored_loss(first),
                model.bob_transmittance * _factored_loss(second),
            )
            state["coarse"] = coarse_distribution(
                click_distribution(
                    a, b, device, alice_dark=dark(alice), bob_dark=dark(bob)
                ),
                first.receiver,
                second.receiver,
            )
            if context.note is not None:
                context.note["gram_preparation"] = [ar, br]

        context.on_emissions(prepare)

        def raw(
            declaration: CandidateDeclaration,
        ) -> Mapping[tuple[str, str], Fraction]:
            assert declaration.bob_factors is not None
            stations = [
                context.station(label) for label in declaration.measured_factor_labels
            ]
            components = [outcome_components(station) for station in stations]
            coarse = state["coarse"]
            result: dict[tuple[str, str], Fraction] = {}
            for x in declaration.alice_alphabet:
                for labels in product(
                    *(family.alphabet for family in declaration.bob_factors.factors)
                ):
                    letters: dict[str, str] = {}
                    weight: Fraction | None = None
                    for station, component, label in zip(
                        stations, components, labels, strict=True
                    ):
                        letter, setting, choice = component[label]
                        letters[station.party] = letter
                        weighting = station.choice_weighting
                        if weighting is not None and choice is not None:
                            v = outcome_label((letter, setting), station.settings)
                            coin = weighting.weight(weighting.setting_of[v], choice)
                            weight = coin if weight is None else weight * coin
                    probability = coarse[(letters["A"], letters["B"])]
                    result[(x, PRODUCT_LABEL_SEPARATOR.join(labels))] = (
                        probability if weight is None else probability * weight
                    )
            return result

        return factored_loss_applied(aggregate(raw)), raw_factored_loss_applied(raw)


def _factored_loss(emission: DeviceEmission) -> Fraction:
    """Return the factored loss ``t`` of one station's receiver artefact."""
    return emission.receiver.efficiency_record.normalization.factored_loss


#: The one instance of this model the registry holds.
MODEL = SpdcPair()
