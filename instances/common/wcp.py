"""The tagged weak-coherent-pulse source: its preparation.

WHAT IS HERE. The library half of a ``wcp_decoy`` source: the
preparation that turns ordinary inputs -- a test coin, test-intensity
probabilities, intensities, which polarisations a generation and a test round
send -- into the transmitter's ``TaggedSourceDeclaration`` and its
serialisable preparation record. A
protocol document's ``wcp_decoy`` block (:mod:`instances.declared.wcp`) reads
its values and calls :func:`prepare_source`; the decoy BB84 template
(``instances/decoy_bb84/protocol.yaml``) is such a document.

WHAT IT PREPARES. The decoy BB84 template's shape (three intensities,
generation at the signal in H and V, tests at every intensity in four
polarisations), generalised for documents. Each sector weight is the lower end
of the Poisson enclosure the transmitter forms itself
(:func:`certiqs_key.transmitter.decoy.poisson_enclosures`,
``transmitter/decoy/req:sector-weight-bound``), rounded down onto the lattice,
so the prepared weight passes the engine's own comparison. The signal dyads are
not prepared here: the emission forms them from the polarisation parts
(``transmitter/decoy/req:signal-dyads``).

WHY NOTHING IS ROUNDED IN THE FORMED ENTRIES. No emitted matrix is repaired.
Category masses are declared on the lattice (24 bits for decoy BB84), then
split equally between the polarisations a round sends. Poisson weights are
rounded downward on the same lattice. Thus every weighted dyad has a bounded
denominator and every partial sum lies in [0, 1]: the formed entries and
accumulations are binary64 numbers without rounding.

WHAT IT REFUSES. :class:`WcpSourceError`, a ``ValueError``, with the input it
refuses in ``field``: cutoffs out of order, not one test probability per
intensity, a lattice that would change the categories' positive support, a
negative intensity. A document's lowering re-raises it as its coded
``wcp_source_invalid``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.runs.errors import RunInputReason, RunInputValueError
from certiqs_key.runs.inputs import (
    NumericInput,
    exact_input,
    prepare_bound,
    prepare_probabilities,
)
from certiqs_key.transmitter.certificate import RetentionAttestation
from certiqs_key.transmitter.decoy import (
    FlagFamily,
    RoundType,
    TaggedSourceDeclaration,
    WcpLetter,
    WcpModel,
    poisson_enclosures,
)

__all__ = [
    "PreparedLetter",
    "PreparedSource",
    "WcpSourceError",
    "check_cutoffs",
    "prepare_source",
]


class WcpSourceError(ValueError):
    """A WCP source's preparation refused; ``field`` names the refused input.

    ``field`` is a JSON-pointer suffix relative to the source (``""`` the
    source as a whole, ``"/intensities"``, ``"/entropy_cutoff"``), so that a
    document's lowering can point at the block it came from.
    """

    def __init__(self, message: str, *, field: str = "") -> None:
        """Carry ``message`` as a ``ValueError`` does, and the refused ``field``."""
        super().__init__(message)
        self.field = field


def check_cutoffs(entropy_cutoff: int, source_cutoff: int) -> None:
    """Refuse an entropy cutoff outside ``[0, min(2, source_cutoff)]``."""
    if not 0 <= entropy_cutoff <= min(2, source_cutoff):
        raise WcpSourceError(
            "require 0 <= entropy_cutoff <= min(2, source_cutoff)",
            field="/entropy_cutoff",
        )


@dataclass(frozen=True)
class PreparedLetter:
    """One emitted letter: its label and the fields its label was rendered from.

    ``fields`` are ``round`` (``gen`` or ``test``), ``intensity`` and
    ``polarisation``.
    """

    label: str
    fields: Mapping[str, str]


@dataclass(frozen=True)
class PreparedSource:
    """The exact transmitter input, its serialisable record, and its letters."""

    tagged: TaggedSourceDeclaration
    record: Mapping[str, Any]
    letters: tuple[PreparedLetter, ...]


def prepare_source(
    *,
    polarisations: Mapping[str, str],
    intensities: Mapping[str, NumericInput],
    test_probabilities: Sequence[NumericInput],
    coin: NumericInput,
    generation_intensity: str,
    generation_polarisations: Sequence[str],
    test_polarisations: Sequence[str],
    entropy_cutoff: int,
    source_cutoff: int,
    lattice_exponent: int,
    flag_family: FlagFamily,
    attestation: RetentionAttestation | None,
    letter_label: Callable[[Mapping[str, str]], str],
    tolerance: float,
    site: str,
    instance: str,
) -> PreparedSource:
    """Prepare ordinary inputs before handing exact data to the transmitter.

    ``polarisations`` maps each polarisation's label to its part, in order;
    ``intensities`` each intensity's name to its written ``mu``, in order, and
    ``test_probabilities`` gives one test probability per intensity in that
    order. ``coin`` is the test probability ``gamma``. A category is
    generation, at ``generation_intensity`` in ``generation_polarisations``,
    or tests at one intensity in ``test_polarisations``; splitting only after
    snapping preserves the uniform bit/basis law. All positive category support
    is preserved or preparation refuses. ``letter_label`` renders a letter's
    label from its fields; ``site`` prefixes every preparation record's site
    and ``instance`` is the record's ``instance`` string.

    The sequence, step for step: the coin, the test intensities and the
    categories with ``prepare_probabilities`` (sites ``<site>.test_coin``,
    ``.test_intensities``, ``.source_category_lattice``); each ``mu`` read as
    ``Fraction(float(exact_input(mu)))``, the binary64 value its declaration
    denotes; the Poisson enclosures, with ``prepare_bound`` (sites
    ``<site>.poisson.<intensity>.<n>``); ``WcpModel`` and
    ``TaggedSourceDeclaration``.
    """
    names = tuple(intensities)
    if not names or len(names) != len(test_probabilities):
        raise WcpSourceError("one test probability is required per intensity")
    check_cutoffs(entropy_cutoff, source_cutoff)
    prepared_coin = prepare_probabilities(
        (coin, 1 - exact_input(coin)),
        tolerance=tolerance,
        lattice_exponent=lattice_exponent,
        site=f"{site}.test_coin",
    )
    tests = prepare_probabilities(
        test_probabilities,
        tolerance=tolerance,
        lattice_exponent=lattice_exponent,
        site=f"{site}.test_intensities",
    )
    # The category vector is formed from two prepared vectors as exact
    # products, so it is a probability vector the instance prepares before
    # declaring it: foundations/req:declared-tolerance, second paragraph,
    # decides it by the input preparation's rule. Its inputs are exact
    # (closed-point cells) and its exact defect is 0, and the snap runs at the
    # same guard as before; the record carries the cells and the admission
    # ground. It is snapped onto the lattice even when already binary64,
    # because the module docstring's no-rounding argument needs the masses
    # there.
    original = (
        prepared_coin.values[1],
        *(prepared_coin.values[0] * p for p in tests.values),
    )
    try:
        categories = prepare_probabilities(
            original,
            tolerance=tolerance,
            lattice_exponent=lattice_exponent,
            site=f"{site}.source_category_lattice",
            preserve_exact=False,
        )
    except RunInputValueError as error:
        if error.reason is RunInputReason.POSITIVE_SUPPORT_LOST:
            raise WcpSourceError(
                "source category lattice would change positive support"
            ) from error
        raise
    declared_mu = {
        name: Fraction(float(exact_input(mu))) for name, mu in intensities.items()
    }
    if any(mu < 0 for mu in declared_mu.values()):
        raise WcpSourceError("intensities must be nonnegative", field="/intensities")
    labels = tuple(polarisations)
    letters: list[WcpLetter] = []
    weights: dict[str, Fraction] = {}
    prepared_letters: list[PreparedLetter] = []
    for index, mass in enumerate(categories.values):
        if not mass:
            continue
        generation = index == 0
        intensity = generation_intensity if generation else names[index - 1]
        sent = tuple(generation_polarisations if generation else test_polarisations)
        if not sent:
            # A category with mass and no polarisation sends no letter; the
            # weights then miss its mass, which the emission decides.
            continue
        round_name = str(RoundType.GEN if generation else RoundType.TEST)
        for polarisation in sent:
            fields = {
                "round": round_name,
                "intensity": intensity,
                "polarisation": polarisation,
            }
            label = letter_label(fields)
            letters.append(
                WcpLetter(
                    label,
                    polarisation,
                    intensity,
                    RoundType.GEN if generation else RoundType.TEST,
                )
            )
            weights[label] = mass / len(sent)
            prepared_letters.append(PreparedLetter(label, fields))
    model = WcpModel(
        labels,
        declared_mu,
        tuple(letters),
        weights,
        dict(polarisations),
    )
    sector_weights: dict[tuple[int, str], Fraction] = {}
    bounds = []
    for name, mu in declared_mu.items():
        try:
            enclosed = poisson_enclosures(mu, source_cutoff)
        except MalformedInputError as failure:
            raise WcpSourceError(str(failure), field="/intensities") from failure
        for n, enclosure in enumerate(enclosed.enclosures):
            weight, record = prepare_bound(
                enclosure.lower,
                direction="lower",
                lattice_exponent=lattice_exponent,
                site=f"{site}.poisson.{name}.{n}",
            )
            sector_weights[n, name] = weight
            bounds.append(
                {
                    **record,
                    "enclosure_lower": str(enclosure.lower),
                    "enclosure_upper": str(enclosure.upper),
                }
            )
    tagged = TaggedSourceDeclaration(
        model,
        entropy_cutoff,
        source_cutoff,
        sector_weights,
        flag_family=flag_family,
        retention_attestation=attestation,
    )
    record = {
        "instance": instance,
        "lattice_exponent": lattice_exponent,
        "coin": prepared_coin.record,
        "test_intensities": tests.record,
        "categories": categories.record,
        "intensities": {
            name: {
                "input": str(exact_input(intensities[name])),
                "prepared": str(mu),
                "displacement": str(mu - exact_input(intensities[name])),
            }
            for name, mu in declared_mu.items()
        },
        "poisson_bounds": bounds,
    }
    return PreparedSource(tagged, record, tuple(prepared_letters))
