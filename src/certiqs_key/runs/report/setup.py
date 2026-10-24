"""The report's "Your QKD setup": the protocol and the devices, read off the record.

WHY THIS EXISTS. A QKD experimentalist or a certification lab reading a key
rate first asks what was modelled: which protocol steps, which source, which
measurement each station makes, with which operators, and what statistics the
honest model expects. This module builds
``sections.setup`` of the report object from the RECORD ONLY.

NOTHING ABSENT IS INVENTED. A step, a field or an operator the record does not
hold is reported as absent, in a sentence, and the section never fails to
build: a missing or malformed field gives ``None`` and a note (records 0.20.0
onwards).

THE SENTENCES HERE are the run tier's plain reading of record fields (the
precedent of :mod:`certiqs_key.runs.report.snaps`): each states what a field
says, never a claim's content. Where a sentence leans on a claim it names the
claim id in ``claims``, and the renderer links it.

THE BASIS OF A PHOTON-NUMBER BLOCK. The receiver emits every block in the
occupation basis of Definition ``def:fock``: the occupation vectors of
``m`` photons over the channel modes (``input_mode_space.channel_labels``),
in ascending lexicographic order
(:func:`certiqs_key.receiver.fock.occupation_vectors`, ``interface.yaml``
``conventions.subsystem_order``), and the record lists them per block in
``receiver.block_dimensions``. With channel modes ``(Z_H, Z_V)`` the
one-photon basis is therefore ``(0, 1), (1, 0)``: first one photon in
``Z_V``, then one photon in ``Z_H``. The labels below are read from those
occupation vectors, never assumed.

THE ONE COMPUTATION: the expected statistics. The
builder otherwise computes no number; these few are sums over the record's
exact honest raw joint distribution, each with the sentence that says how it
was formed, and they qualify nothing the key length rests on.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from fractions import Fraction
from typing import Any, Final

from certiqs_key.runs.report.inputs import (
    analysed_config,
    analysed_words,
    exact_with_decimal,
    pointer_join,
    prepared_inputs,
    resolve_pointer,
    same_number,
    upper_decimal,
)
from certiqs_key.runs.report.model import (
    AcceptanceCategory,
    Detector,
    ExpectedStatistic,
    MatrixEntry,
    OperatorBlock,
    OperatorElement,
    OperatorFamily,
    OpticalElement,
    OutcomeLetter,
    ProtocolStep,
    RoundBlock,
    SetupAcceptance,
    SetupSection,
    SetupSource,
    SetupStation,
)
from certiqs_key.runs.roles import Roles, party_name, run_roles
from certiqs_key.runs.stages import SliceStage

__all__ = [
    "ROUND_COUNTS",
    "ROUND_SENTENCES",
    "ROUTE_WORDS",
    "build_setup",
    "matrix_of",
    "occupation_label",
    "round_block",
    "setup_claims",
]

#: How a station's receiver was given, in words (``runs/record.py``
#: ``RECEIVER_ROUTES``).
ROUTE_WORDS: Final[Mapping[str, str]] = {
    "element-graph": (
        "element graph: the engine compiled the measurement from the declared "
        "optical elements and detectors"
    ),
    "port-grams": (
        "port Grams: the receiver is declared by the Gram matrix of each "
        "detector port, from which the engine builds the measurement"
    ),
    "instrument-matrix": (
        "instrument matrix: the receiver is declared by its transfer matrix "
        "from the input modes to the detector modes"
    ),
    "declared-finite-povm": (
        "declared finite POVM: the measurement operators are declared "
        "directly, with no optical model"
    ),
    "per-station": "per station: each station names its own route",
}

#: The catalogue entries of the receiver's component catalogue
#: (``receiver/catalogue.py``), as a reader names them.
_COMPONENTS: Final[Mapping[str, str]] = {
    "C1": "beamsplitter",
    "C2": "polarising beamsplitter",
    "C3": "wave plate",
    "C4": "circular retarder",
    "C5": "mirror",
    "C6": "phase shifter",
    "C7": "loss element",
    "C8": "polariser",
    "C9": "mode routing",
    "C10": "generic block",
}

#: The protocol document's component names, as a reader names them.
_DOCUMENT_COMPONENTS: Final[Mapping[str, str]] = {
    "beamsplitter": "C1",
    "polarizing_beamsplitter": "C2",
    "half_wave": "C3",
    "quarter_wave": "C3",
    "retarder": "C3",
}

#: Detector parameters of a protocol document, as a reader names them.
_DETECTOR_WORDS: Final[Mapping[str, str]] = {
    "efficiency": "efficiency",
    "dark_count": "dark-click probability per round",
}

#: The claim of the compilation of an element graph.
_COMPILE_CLAIM: Final[str] = "receiver/def:compile"
#: The claim of the Band-A route (a declared finite POVM).
_BAND_A_CLAIM: Final[str] = "protocol-compiler/thm:band-a"
#: The reduction claim a target POVM rests on when the record names no root.
_EMIT_CLAIM: Final[str] = "reductions/thm:emit"
#: The completeness claim of the box acceptance test.
_COMPLETENESS_CLAIM: Final[str] = "statistics/binomial-box/thm:completeness-bound"

_NUMBER_WORDS: Final[tuple[str, ...]] = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten",
)


# --------------------------------------------------------------------------
# Small readers
# --------------------------------------------------------------------------


def _at(record: Mapping[str, Any], pointer: str) -> Any:
    return resolve_pointer(record, pointer, None)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _text(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _fraction(value: Any) -> Fraction | None:
    """Return an exact value of a record number or ``"p/q"`` string, or ``None``."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value.strip())
        except (ValueError, ZeroDivisionError):
            return None
    return None


def _with_decimal(value: Any) -> str:
    """Return a record number as text, an exact ``p/q`` with its decimal."""
    found = _fraction(value)
    if (
        isinstance(value, str) and "/" in value and found is not None
        and found.denominator > 1000
    ):
        return f"{value} (about {float(found):.3g})"
    return _text(value)


def _party_name(party: Any) -> str | None:
    """Return a formal party label's name (:data:`roles.PARTY_NAMES`), or None."""
    return None if party is None else party_name(party)


def _choice_weightings(
    public: Mapping[str, Any],
) -> list[tuple[Mapping[str, Any], str]]:
    """Return every recorded choice weighting with its record pointer.

    Record 0.30.0 lists one entry per weighted factor in
    ``compiled.public.choice_weightings``, each naming its ``factor``; an
    older record carries one ``choice_weighting`` object (with the factor's
    ``party``) or ``null``, read as a list of at most one.
    """
    listed = public.get("choice_weightings")
    if isinstance(listed, list):
        return [
            (item, f"/payload/compiled/public/choice_weightings/{index}")
            for index, item in enumerate(listed) if isinstance(item, Mapping)
        ]
    single = public.get("choice_weighting")
    if isinstance(single, Mapping):
        return [(single, "/payload/compiled/public/choice_weighting")]
    return []


def _weighting_matches(
    weighting: Mapping[str, Any], station: SetupStation, record: Mapping[str, Any]
) -> bool:
    """Whether a recorded weighting was declared at this station's factor.

    A station of a multi-station run by the factor the entry names, against
    the factor ``stages.stations[i].factor`` records; the single receiver of a
    one-station run, which is the one measured factor, always.
    """
    index = station["index"]
    if index is None:
        return True
    factor = weighting.get("factor")
    recorded = _mapping(_at(record, f"/payload/stages/stations/{index}")).get("factor")
    return factor is not None and str(factor) == str(recorded)


def _weighting_station(
    weighting: Mapping[str, Any],
    stations: Sequence[SetupStation],
    record: Mapping[str, Any],
) -> str:
    """Return the station a weighting was declared at, in words."""
    for station in stations:
        if _weighting_matches(weighting, station, record):
            return station["name"]
    factor = weighting.get("factor")
    party = _party_name(weighting.get("party"))
    if party is not None:
        return f"{party}'s station"
    return f"the measured factor {factor}" if factor is not None else "a station"


def combined_words(roles: Roles) -> str:
    """Return what a key-map combination is made of, in words.

    "readouts" at one letter (the letter carries nothing: an untrusted
    source's placeholder); "signal and readouts" where a trusted source's
    letter is the signal sent (SENDS); "letter and readouts" otherwise (a letter
    measured from a delivered system, or drawn as local randomness). Both the
    sifting step and the expected-statistics row read it.
    """
    if not roles.has_letters:
        return "readouts"
    # A signal only where Alice sends (trusted, d_A >= 2).
    return "signal and readouts" if roles.sends(roles.alice_party) else (
        "letter and readouts"
    )


def _station_choices(
    record: Mapping[str, Any], presentation: Any, stations: Sequence[SetupStation]
) -> list[str]:
    """Return a sentence per measuring party's setting-independent public choice.

    Read from A-COIN's ``public_choices`` binding, which lists Alice's
    presentation and every choice-weighted family of a measuring party; the
    presentation is said elsewhere, so it is skipped here.
    """
    families: list[Mapping[str, Any]] = []
    for entry in _sequence(_at(record, "/payload/assumption_manifest/assumptions")):
        if _mapping(entry).get("short_id") != "A-COIN":
            continue
        for binding in _sequence(_mapping(entry).get("bindings")):
            binding = _mapping(binding)
            if binding.get("name") != "public_choices":
                continue
            value = binding.get("value")
            for family in value if isinstance(value, list) else [value]:
                family = _mapping(family)
                if (family and family != _mapping(presentation)
                        and family not in families
                        and len(_sequence(family.get("choices"))) >= 2):
                    families.append(family)
    sentences: list[str] = []
    for family in families:
        party = family.get("party")
        names = [station["name"] for station in stations
                 if party is not None and station["party"] == str(party)]
        if not names and len(stations) == 1:
            names = [stations[0]["name"]]
        where = _joined(names) if names else (
            f"{_party_name(party) or 'a party'}'s station"
        )
        weights = _mapping(family.get("weights"))
        sentences.append(f"At {where}, a public choice is drawn: " + ", ".join(
            f"{choice} with probability {exact_with_decimal(weights.get(choice))}"
            for choice in _sequence(family.get("choices"))
        ) + ".")
    return sentences


#: WHAT A ROUND IS.
#: WHY: mapping the premises to evidence on a time-tagged system needs the
#: definition of a round, before the protocol's steps use it. The block says
#: what a round is in a few sentences, then lists the engaged premises the cut
#: of a detection record into rounds bears on, each with a short gloss of what
#: its own text says (the full text is under "Assumptions you vouch for"); it
#: is not a complete list. No condition of a premise's text is dropped from
#: its gloss: A-SPEC's says that a lost round and a dropped no-click bin are
#: security matters; A-ALPHABET's own text names the security matter through
#: A-SPEC and A-CONFORM, and its gloss says so the same way.
#: Per short id, the gloss;
#: :func:`round_block` keeps those the run's manifest holds, in this order.
_ROUND_PREMISES: Final[tuple[tuple[str, str], ...]] = (
    ("A-SPEC", "each round's recorded outcome is what the declared measurement "
               "gives, so a detection lost from its round or filed in another, or "
               "a no-click bin dropped, is a security matter"),
    ("A-EXACT", "the declared efficiencies and dark-count probabilities are the "
                "true values for the rounds as you cut them"),
    ("A-IDEAL", "exactly one qubit reaches the receiver in each round"),
    ("A-MODES", "no light outside the declared temporal modes (outside a window, "
                "say) reaches a detector"),
    ("A-PORT", "a click probability that depends on the temporal mode "
               "(efficiency mismatch) is declared as mode-dependent loss"),
    ("A-THRESH", "threshold detectors read once per gate, with no dead time, "
                 "afterpulsing or timing jitter"),
    ("A-RHOM", "one declaration covers every round"),
    ("A-ROUND", "the same receiver behaviour in every round and no memory across "
                "rounds, such as dead time or afterpulsing across a boundary"),
    ("A-SEQ", "the declared order of measurements and messages within a round, "
              "and each measuring party completing one round's measurement "
              "before the next round's"),
    ("A-FIXED", "the number of rounds and the acceptance test are fixed before "
                "the run"),
    ("A-ALPHABET", "all n rounds are in the record (the acceptance test is "
                   "evaluated on all n rounds); a measured round missing from it, "
                   "a lost time tag or no-click bin included, leaves the counts "
                   "wrong and is a security matter under [[A-SPEC]] and "
                   "[[A-CONFORM]]"),
)

#: The sentences that say what a round is, before the protocol's steps.
ROUND_SENTENCES: Final[tuple[str, ...]] = (
    "A round is one use of the protocol as declared, recording its own outcomes.",
    "How a time-tagged system cuts its detection record into rounds (time bins, "
    "coincidence windows, how the stations synchronise) is yours to choose, and "
    "your declaration must describe it.",
)

#: The sentence that every round counts, said where A-SPEC or A-ALPHABET is
#: engaged (their texts are its basis).
ROUND_COUNTS: Final[str] = (
    "Every one of the n rounds counts: where your measurement has a no-click "
    "outcome, a time bin in which nothing clicks is a round with that outcome, "
    "not one to drop."
)


def _engaged_ids(record: Mapping[str, Any]) -> set[str]:
    """Return the short ids of the run's engaged premises (its manifest)."""
    return {
        str(_mapping(entry).get("short_id"))
        for entry in _sequence(_at(record, "/payload/assumption_manifest/assumptions"))
    }


def round_block(engaged: Collection[str], trusted: bool | None) -> RoundBlock:
    """Return what a round is and the engaged premises the cut bears on.

    A-LAB's gloss names the timing and synchronisation clause, and the clock
    or trigger line of an untrusted source only on an untrusted run.
    """
    glosses = [(short_id, gloss) for short_id, gloss in _ROUND_PREMISES
               if short_id in engaged]
    if "A-LAB" in engaged:
        lab = ("no timing or synchronisation signal reveals a party's records, and "
               "only the declared inputs influence a measurement")
        if trusted is False:
            lab += ", not a clock or trigger line from the untrusted source"
        position = next(
            (index for index, (short_id, _) in enumerate(glosses)
             if short_id == "A-FIXED"), len(glosses),
        )
        glosses.insert(position, ("A-LAB", lab))
    sentences = list(ROUND_SENTENCES)
    if {"A-SPEC", "A-ALPHABET"} & set(engaged):
        sentences.append(ROUND_COUNTS)
    return {
        "text": " ".join(sentences),
        "premises": [{"short_id": short_id, "gloss": gloss}
                     for short_id, gloss in glosses],
    }


def _joined(items: Iterable[Any], last: str = "and") -> str:
    words = [str(item) for item in items]
    if len(words) <= 1:
        return "".join(words)
    return f"{', '.join(words[:-1])} {last} {words[-1]}"


# --------------------------------------------------------------------------
# Matrices
# --------------------------------------------------------------------------


def _scalar(value: Any) -> str | float | None:
    """Return one real part as the report carries it: exact string or binary64."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return value
    if isinstance(value, str):
        return value.strip()
    return None


def _entry(value: Any) -> MatrixEntry | None:
    if isinstance(value, list) and len(value) == 2:
        real, imaginary = _scalar(value[0]), _scalar(value[1])
        if real is None or imaginary is None:
            return None
        return [real, imaginary]
    real = _scalar(value)
    if real is None:
        return None
    return [real, "0" if isinstance(real, str) else 0.0]


def matrix_of(value: Any) -> list[list[MatrixEntry]] | None:
    """Return a record matrix as rows of ``[re, im]`` entries, or ``None``.

    Reads the forms the record writes: rows of ``[re, im]`` pairs (exact
    strings or binary64), rows of plain reals (a protocol document's), a
    ``{"matrix": rows}`` wrapper and ``{"identity": d}``. Anything else is not
    a matrix and gives ``None``.
    """
    if isinstance(value, Mapping):
        if "matrix" in value:
            return matrix_of(value["matrix"])
        size = value.get("identity")
        if isinstance(size, int) and not isinstance(size, bool) and 0 < size <= 64:
            return [
                [["1" if row == column else "0", "0"] for column in range(size)]
                for row in range(size)
            ]
        return None
    if not isinstance(value, list) or not value:
        return None
    rows: list[list[MatrixEntry]] = []
    for raw in value:
        if not isinstance(raw, list) or not raw:
            return None
        row = [_entry(item) for item in raw]
        if any(item is None for item in row):
            return None
        rows.append([item for item in row if item is not None])
    if len({len(row) for row in rows}) != 1:
        return None
    return rows


def _is_exact(elements: Iterable[OperatorElement]) -> bool:
    return all(
        isinstance(part, str)
        for element in elements
        for row in element["matrix"]
        for entry in row
        for part in entry
    )


def _block(
    title: str,
    basis: list[str],
    elements: list[OperatorElement],
    pointer: str | None,
    *,
    basis_note: str | None = None,
    column_basis: list[str] | None = None,
) -> OperatorBlock:
    return {
        "title": title,
        "basis": basis,
        "column_basis": column_basis,
        "basis_note": basis_note,
        "elements": elements,
        "exact": _is_exact(elements),
        "pointer": pointer,
    }


def _numbered(size: int) -> list[str]:
    return [f"basis state {index}" for index in range(1, size + 1)]


# --------------------------------------------------------------------------
# Photon-number bases
# --------------------------------------------------------------------------


def _count(number: int) -> str:
    return _NUMBER_WORDS[number] if 0 <= number < len(_NUMBER_WORDS) else str(number)


def occupation_label(vector: Sequence[int], modes: Sequence[str]) -> str:
    """Return a basis state of a photon-number block in words.

    ``vector`` is an occupation vector over ``modes`` (the channel modes, in
    the order the receiver indexes them): ``(0, 1)`` over ``(Z_H, Z_V)`` is
    "one photon in mode Z_V", the vacuum is "vacuum".
    """
    parts = [
        (int(count), str(mode))
        for count, mode in zip(vector, modes, strict=False)
        if int(count) > 0
    ]
    if not parts:
        return "vacuum"
    if len(parts) == 1:
        count, mode = parts[0]
        noun = "photon" if count == 1 else "photons"
        return f"{_count(count)} {noun} in mode {mode}"
    return ", ".join(f"{_count(count)} in mode {mode}" for count, mode in parts)


def _photon_bases(
    dimensions: Any, modes: Sequence[str]
) -> dict[int, tuple[list[str], str]]:
    """Return per photon number the basis labels and the note saying where from."""
    bases: dict[int, tuple[list[str], str]] = {}
    mode_list = ", ".join(modes)
    for row in _sequence(dimensions):
        if not isinstance(row, Mapping):
            continue
        photons = row.get("photons")
        vectors = row.get("occupation_vectors")
        if not isinstance(photons, int) or not isinstance(vectors, list):
            continue
        labels = [
            occupation_label(vector, modes)
            for vector in vectors
            if isinstance(vector, list)
        ]
        written = "; ".join(
            f"{index}. {label} {tuple(vector)}"
            for index, (label, vector) in enumerate(
                zip(labels, vectors, strict=False), start=1
            )
        )
        bases[photons] = (
            labels,
            f"Basis in the record's order, occupation numbers over the channel "
            f"modes ({mode_list}): {written}.",
        )
    return bases


def _sector_basis(
    sector: str, size: int, bases: Mapping[int, tuple[list[str], str]]
) -> tuple[str, list[str], str | None]:
    """Return a sector's title, basis labels and basis note.

    A target or declared sector ``C:m`` (or ``("C", "m")``) is the channel's
    ``m``-photon block, on the photon-number basis; ``C:<letter>`` is the
    one-dimensional flag of an outcome (``reductions`` ``eq:WPFSS``).
    """
    _, _, label = sector.partition(":")
    if label.isdigit():
        photons = int(label)
        found = bases.get(photons)
        noun = "photon" if photons == 1 else "photons"
        title = f"{photons} {noun}"
        if found is not None and len(found[0]) == size:
            return title, found[0], found[1]
        return title, _numbered(size), None
    if label and size == 1:
        return f"flag {label}", [f"flag {label}"], None
    return f"sector {sector}", _numbered(size), None


# --------------------------------------------------------------------------
# The protocol document: what a station declared
# --------------------------------------------------------------------------


def _resolve(node: Any, config: Mapping[str, Any]) -> Any:
    """Return a protocol-document value: a ``{"param"}`` read from the config."""
    if isinstance(node, Mapping):
        if "param" in node:
            name = str(node["param"])
            device = _mapping(config.get("device"))
            model = _mapping(config.get("model"))
            value = device.get(name, model.get(name))
            port = node.get("port")
            if port is not None and isinstance(value, Mapping):
                return value.get(str(port))
            return value
        if "expr" in node:
            return str(node["expr"])
    return node


def _document_station(
    record: Mapping[str, Any], label: str | None, party: str | None
) -> Mapping[str, Any]:
    stations = _sequence(_at(record, "/payload/protocol_document/canonical/stations"))
    for station in stations:
        if (
            isinstance(station, Mapping) and label is not None
            and station.get("id") == label
        ):
            return station
    matching = [
        station for station in stations
        if isinstance(station, Mapping) and station.get("party") == party
    ]
    return matching[0] if len(matching) == 1 else {}


def _document_letters(station: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    measurement = _mapping(station.get("measurement"))
    letters = _sequence(_mapping(measurement.get("coarse_graining")).get("letters"))
    return {
        str(letter["label"]): letter
        for letter in letters
        if isinstance(letter, Mapping) and "label" in letter
    }


def _document_patterns(
    record: Mapping[str, Any], station_id: str | None
) -> dict[str, list[list[str]]]:
    """Return the click patterns per letter from the document's expansion rows."""
    expansion = _mapping(_at(record, "/payload/protocol_document/expansion"))
    keys = [f"{station_id}.coarse_graining"] if station_id else []
    keys.append("coarse_graining")
    for key in keys:
        rows = _sequence(_mapping(expansion.get(key)).get("rows"))
        if not rows:
            continue
        patterns: dict[str, list[list[str]]] = {}
        for row in rows:
            if not isinstance(row, list) or len(row) < 2:
                continue
            raw = str(row[0]).strip()
            ports = [
                part.strip() for part in raw.strip("{}").split(",") if part.strip()
            ]
            patterns.setdefault(str(row[1]), []).append(ports)
        return patterns
    return {}


# --------------------------------------------------------------------------
# Stations
# --------------------------------------------------------------------------


def _letter_meaning(patterns: list[list[str]] | None, letter: Mapping[str, Any]) -> str:
    if patterns is None:
        meaning = "an outcome of the declared measurement"
    elif patterns == [[]]:
        meaning = "no detector clicked"
    elif len(patterns) == 1 and len(patterns[0]) == 1:
        meaning = f"only detector {patterns[0][0]} clicked"
    elif patterns and all(len(pattern) >= 2 for pattern in patterns):
        meaning = (
            f"more than one detector clicked (any of {len(patterns)} click "
            "patterns)"
        )
    else:
        meaning = "the click patterns " + "; ".join(
            "+".join(pattern) or "none" for pattern in patterns
        )
    basis, bit = letter.get("basis"), letter.get("bit")
    if basis is not None and bit is not None:
        meaning += f"; basis {basis}, bit {bit}"
    return meaning


def _outcomes(
    coarse: Any,
    document_letters: Mapping[str, Mapping[str, Any]],
    document_patterns: Mapping[str, list[list[str]]],
    fallback: Sequence[str],
) -> list[OutcomeLetter]:
    rows: list[tuple[str, list[list[str]] | None]] = []
    for item in _sequence(coarse):
        if not isinstance(item, Mapping) or "letter" not in item:
            continue
        fibre = [
            [str(port) for port in pattern]
            for pattern in _sequence(item.get("fibre"))
            if isinstance(pattern, list)
        ]
        rows.append((str(item["letter"]), fibre))
    if not rows and document_patterns:
        # In the document's letter order, then any letter it does not list.
        order = [
            *(letter for letter in document_letters if letter in document_patterns),
            *(letter for letter in document_patterns if letter not in document_letters),
        ]
        rows = [(letter, list(document_patterns[letter])) for letter in order]
    if not rows:
        rows = [(str(letter), None) for letter in fallback]
    return [
        {
            "letter": letter,
            "meaning": _letter_meaning(patterns, document_letters.get(letter, {})),
            "patterns": patterns,
        }
        for letter, patterns in rows
    ]


def _pi_angle(value: Any) -> str | None:
    found = _fraction(value)
    if found is None:
        return None
    if found == 0:
        return "0°"
    numerator = "π" if found.numerator == 1 else f"{found.numerator}π"
    text = numerator if found.denominator == 1 else f"{numerator}/{found.denominator}"
    return f"{text} = {float(found * 180):g}°"


def _coefficient(value: Any) -> Any:
    return value.get("pi_coefficient") if isinstance(value, Mapping) else value


def _split(value: Any) -> str:
    found = _fraction(value)
    if found is None or not 0 <= found <= 1:
        return f"transmittance {_text(value)}"
    left, right = float(found * 100), float((1 - found) * 100)
    return f"transmittance {_text(value)} ({left:g}:{right:g})"


def _element_words(catalogue: str | None, parameters: Mapping[str, Any]) -> str:
    """Return an element's parameters in words, by its catalogue entry."""
    zero = {"0", "0.0"}
    extras = [
        f"{name.replace('_', ' ')} {_text(parameters[name])}"
        for name in ("loss", "loss_1", "loss_2", "phase", "phase_h", "phase_v")
        if name in parameters and _text(parameters[name]) not in zero
    ]
    if catalogue == "C1":
        words = _split(parameters.get("transmittance"))
    elif catalogue == "C2":
        through, crossed = (
            _fraction(parameters.get("transmittance_h")),
            _fraction(parameters.get("transmittance_v")),
        )
        if through == 1 and crossed == 0:
            words = "transmits H and reflects V"
        else:
            words = (
                f"transmits H with probability "
                f"{_text(parameters.get('transmittance_h'))} and V with probability "
                f"{_text(parameters.get('transmittance_v'))}"
            )
    elif catalogue == "C3":
        retardance = _fraction(_coefficient(parameters.get("retardance")))
        kind = (
            "half-wave plate" if retardance == 1
            else "quarter-wave plate" if retardance == Fraction(1, 2)
            else f"retardance {_text(_coefficient(parameters.get('retardance')))}·π"
        )
        angle = _pi_angle(_coefficient(parameters.get("angle")))
        words = kind if angle is None else f"{kind} at angle {angle}"
    else:
        words = ", ".join(
            f"{name} = {_text(_coefficient(value))}"
            for name, value in parameters.items()
        )
        extras = []
    return "; ".join([words, *extras]) if words else "; ".join(extras)


def _paths(catalogue: str, parameters: Mapping[str, Any], modes: Sequence[str]) -> str:
    """Return where a two-path element sends light, read off its support.

    A beamsplitter or polarising beamsplitter acts on ``(p1H, p1V, p2H,
    p2V)``; its transmittance is the probability of staying in path p1
    (``receiver/catalogue.py`` C1 and C2, Eq. ``eq:bs``). This explains
    the mode names Zr_V, Xr_V.
    """
    if catalogue not in ("C1", "C2") or len(modes) != 4:
        return ""
    first, second = (mode.rsplit("_", 1)[0] for mode in (modes[0], modes[2]))
    if first == second:
        return ""
    first_loss, second_loss = (
        _fraction(parameters.get("loss_1", 0)), _fraction(parameters.get("loss_2", 0))
    )
    if first_loss is None or second_loss is None:
        return ""
    # With a declared loss a photon is also lost at an output.
    lossy = bool(first_loss or second_loss)
    losses = (
        f"; output {first} then loses a fraction {_text(parameters.get('loss_1', 0))} "
        f"and output {second} a fraction {_text(parameters.get('loss_2', 0))}"
        if lossy else ""
    )
    if catalogue == "C1":
        found = _fraction(parameters.get("transmittance"))
        if found is None:
            return ""
        value = _text(parameters.get("transmittance"))
        if lossy:
            return (
                f"a photon from path {first} goes towards path {first} with "
                f"probability {value} and towards path {second} with probability "
                f"1 \u2212 {value}{losses}"
            )
        return (
            f"a photon from path {first} stays in path {first} with probability "
            f"{value} and otherwise moves to path {second}"
        )
    through, crossed = (
        _fraction(parameters.get("transmittance_h")),
        _fraction(parameters.get("transmittance_v")),
    )
    if through == 1 and crossed == 0:
        return (
            f"H {'goes towards' if lossy else 'stays in'} path {first}, V is "
            f"reflected {'towards' if lossy else 'into'} path {second}{losses}"
        )
    return ""


def _arm(modes: Sequence[str]) -> str:
    paths = list(dict.fromkeys(mode.rsplit("_", 1)[0] for mode in modes if "_" in mode))
    if len(paths) == 1:
        return f"in the {paths[0]} arm (modes {', '.join(modes)})"
    return f"on modes {', '.join(modes)}"


def _elements(raw: Any, document: Mapping[str, Any]) -> list[OpticalElement]:
    found: list[OpticalElement] = []
    items = _sequence(raw)
    from_document = False
    if not items:
        items = _sequence(_mapping(document.get("measurement")).get("elements"))
        from_document = True
    for item in items:
        if not isinstance(item, Mapping):
            continue
        if from_document:
            catalogue = _DOCUMENT_COMPONENTS.get(str(item.get("component")))
            parameters = _mapping(item.get("params"))
        else:
            catalogue = item.get("catalogue_id", item.get("entry_id"))
            parameters = _mapping(item.get("parameters"))
        modes = [str(mode) for mode in _sequence(item.get("support"))]
        component = None if catalogue is None else _COMPONENTS.get(str(catalogue))
        words = _element_words(
            None if catalogue is None else str(catalogue), parameters
        )
        location = _arm(modes) if modes else ""
        routes = _paths(str(catalogue), parameters, modes)
        if routes:
            words = f"{words} ({routes})" if words else routes
        # A wave plate's words name its kind (half-wave plate, ...) already.
        kind = None if catalogue == "C3" and words else (
            component or str(item.get("component", ""))
        )
        description = ", ".join(part for part in (kind, words, location) if part)
        found.append({
            "name": str(item.get("name", "")),
            "component": component,
            "description": description,
            "modes": modes,
        })
    return found


def _port_modes(raw: Any, document: Mapping[str, Any]) -> dict[str, list[str]]:
    ports: dict[str, list[str]] = {}
    for item in _sequence(raw):
        if isinstance(item, Mapping) and "port" in item:
            ports[str(item["port"])] = [
                str(mode) for mode in _sequence(item.get("modes"))
            ]
    if ports:
        return ports
    for item in _sequence(_mapping(document.get("measurement")).get("ports")):
        if isinstance(item, Mapping) and "label" in item:
            ports[str(item["label"])] = [
                str(mode) for mode in _sequence(item.get("modes"))
            ]
    return ports


def _detectors(
    ports: Mapping[str, list[str]],
    document: Mapping[str, Any],
    efficiency_record: Any,
    config: Mapping[str, Any],
) -> list[Detector]:
    declared: dict[str, dict[str, Any]] = {}
    for item in _sequence(_mapping(document.get("measurement")).get("detectors")):
        if not isinstance(item, Mapping) or "port" not in item:
            continue
        values: dict[str, Any] = {}
        for key, node in item.items():
            if key == "port":
                continue
            value = _resolve(node, config)
            if value is not None:
                word = _DETECTOR_WORDS.get(str(key), str(key).replace("_", " "))
                values[word] = value
        declared[str(item["port"])] = values
    efficiencies: dict[str, Any] = {}
    # Record 0.38.0 makes the record an object of its rows and the
    # normalization; an older record's is the list of rows itself.
    rows = (
        _mapping(efficiency_record).get("rows")
        if isinstance(efficiency_record, Mapping)
        else efficiency_record
    )
    for row in _sequence(rows):
        if not isinstance(row, Mapping):
            continue
        element = str(row.get("element", ""))
        match = re.fullmatch(r"L1 detector layer, parameter eta_(.+)", element)
        if match is not None:
            # ``value`` from record schema 0.42.0, ``transmittance`` before.
            efficiencies[match.group(1)] = row.get("value", row.get("transmittance"))
    names = list(dict.fromkeys([*ports, *declared, *efficiencies]))
    detectors: list[Detector] = []
    for port in names:
        parameters = dict(declared.get(port, {}))
        if "efficiency" not in parameters and port in efficiencies:
            parameters["efficiency"] = efficiencies[port]
        detectors.append({
            "port": port,
            "modes": ports.get(port),
            "parameters": parameters,
        })
    return detectors


def _normalization_note(normalization: Any) -> str | None:
    """Return the station's efficiency-normalization line, or ``None``.

    ``receiver/detector-imperfections/req:normalization-record``, in words:
    where the receiver was compiled at its normalized station (factored loss
    below one), the factor and every efficiency declared beside the one
    compiled; where the request declared the factor one (``factor_declared``
    with the reason ``factor_one``, or a record before 0.40.0's
    ``declared_one``) and some detector is below one, that the efficiencies
    stay in the receiver. Nothing where the factor is one by default (largest
    efficiency at least 99/100), with source modes, or with every efficiency
    zero: the analysed receiver is then the declared one and there is nothing
    to say.
    """
    record = _mapping(normalization)
    factor = _fraction(record.get("factored_loss"))
    ports = [_mapping(item) for item in _sequence(record.get("ports"))]
    if factor is None:
        return None
    if factor < 1:
        pairs = ", ".join(
            f"{port.get('port')} {port.get('declared_efficiency')} -> "
            f"{port.get('compiled_efficiency')}"
            for port in ports
        )
        return (
            f"Efficiency normalization: factor {factor}; detector efficiencies "
            f"declared -> analysed: {pairs}. The common factor is moved in front "
            "of the receiver as loss that the channel, and so the adversary, is "
            "given; the observed statistics are unchanged, and the expected "
            "statistics are computed for your receiver with the loss applied "
            "([[receiver/detector-imperfections/prop:efficiency-normalization]])."
        )
    declared_below_one = any(
        (value := _fraction(port.get("declared_efficiency"))) is not None
        and value < 1
        for port in ports
    )
    declared_one = record.get("factor_declared") is True and record.get(
        "reason"
    ) in ("factor_one", "declared_one")
    if declared_one and declared_below_one:
        return (
            "Efficiency normalization: off (factor 1 declared); the detectors are "
            "analysed at their declared efficiencies."
        )
    return None


def _letter_blocks(
    raw_blocks: Any,
    bases: Mapping[int, tuple[list[str], str]],
    setting: str | None,
    pointer: str,
) -> list[OperatorBlock]:
    """Return one block per photon number of ``[{photons, elements}]``."""
    blocks: list[OperatorBlock] = []
    for index, row in enumerate(_sequence(raw_blocks)):
        if not isinstance(row, Mapping):
            continue
        photons = row.get("photons")
        elements: list[OperatorElement] = []
        for item in _sequence(row.get("elements")):
            if not isinstance(item, Mapping):
                continue
            matrix = matrix_of(item.get("block"))
            if matrix is not None:
                elements.append({"outcome": str(item.get("letter", "")),
                                 "matrix": matrix})
        if not elements:
            continue
        size = len(elements[0]["matrix"])
        found = bases.get(photons) if isinstance(photons, int) else None
        basis, note = (
            (found[0], found[1]) if found is not None and len(found[0]) == size
            else (_numbered(size), None)
        )
        noun = "photon" if photons == 1 else "photons"
        blocks.append(_block(
            f"{photons} {noun}" if setting is None
            else f"setting {setting}, {photons} {noun}", basis, elements,
            pointer_join(pointer, index), basis_note=note,
        ))
    return blocks


def _sector_family(
    members: Mapping[str, Any],
    sectors: Sequence[str],
    bases: Mapping[int, tuple[list[str], str]],
    pointer: str,
    keyed: bool,
) -> list[OperatorBlock]:
    """Return one block per sector of a sector-block POVM.

    ``members`` maps an outcome to its sector blocks: a list in the order of
    ``sectors`` (a target POVM) or, ``keyed``, a mapping by sector name (a
    declared factor).
    """
    names = list(sectors)
    if keyed and not names:
        names = list(dict.fromkeys(
            str(sector) for blocks in members.values() if isinstance(blocks, Mapping)
            for sector in blocks
        ))
    if not keyed and not names:
        longest = max((len(_sequence(raw)) for raw in members.values()), default=0)
        names = [f"sector {position + 1}" for position in range(longest)]
    blocks: list[OperatorBlock] = []
    for position, sector in enumerate(names):
        elements: list[OperatorElement] = []
        for outcome, raw in members.items():
            if keyed:
                matrix = matrix_of(_mapping(raw).get(sector))
            else:
                parts = _sequence(raw)
                matrix = matrix_of(parts[position]) if position < len(parts) else None
            if matrix is not None:
                elements.append({"outcome": str(outcome), "matrix": matrix})
        if not elements:
            continue
        size = len(elements[0]["matrix"])
        title, basis, note = _sector_basis(sector, size, bases)
        blocks.append(_block(title, basis, elements, pointer, basis_note=note))
    return blocks


def _target_family(
    reduction: Mapping[str, Any],
    bases: Mapping[int, tuple[list[str], str]],
    pointer: str,
    claims: list[str],
) -> OperatorFamily | None:
    target = reduction.get("target_povm")
    if not isinstance(target, Mapping) or not target:
        return None
    # The outcomes in the station's alphabet order where the record gives one.
    order = [
        str(letter) for letter in _sequence(
            _mapping(reduction.get("outcome_correspondence")).get("alphabet"))
    ]
    target = {
        **{letter: target[letter] for letter in order if letter in target},
        **{letter: value for letter, value in target.items() if letter not in order},
    }
    descriptor = _mapping(reduction.get("target_descriptor"))
    sectors = [
        ":".join(str(part) for part in sector) if isinstance(sector, list)
        else str(sector)
        for sector in _sequence(descriptor.get("sectors"))
    ]
    blocks = _sector_family(
        target, sectors, bases, pointer_join(pointer, "target_povm"), keyed=False
    )
    if not blocks:
        return None
    return {
        "kind": "target-povm",
        "title": "Squashed target POVM",
        "text": (
            "The finite-dimensional model the security proof works with: the "
            "reduction maps the receiver's measurement onto it, and proves that "
            "analysing it is enough. One block per photon number up to the "
            "cutoff, then one flag per outcome."
        ),
        "claims": claims,
        "blocks": blocks,
        "pointer": pointer_join(pointer, "target_povm"),
    }


def _gram_family(
    raw: Any, labels: Sequence[str], pointer: str, declared: bool
) -> OperatorFamily | None:
    elements: list[OperatorElement] = []
    for item in _sequence(raw):
        if not isinstance(item, Mapping):
            continue
        matrix = matrix_of(item.get("gram"))
        if matrix is not None:
            elements.append({"outcome": str(item.get("port", "")), "matrix": matrix})
    if not elements:
        return None
    size = len(elements[0]["matrix"])
    basis = list(labels) if len(labels) == size else _numbered(size)
    return {
        "kind": "port-grams",
        "title": "Port Grams" + (" as declared" if declared else ""),
        "text": (
            "The Gram matrix of each detector port over the input modes: the "
            "probability amplitude structure with which a photon in each input "
            "mode reaches that port."
        ),
        "claims": [],
        "blocks": [_block("input modes", basis, elements, pointer,
                          basis_note="Rows and columns are the input modes in "
                                     "the receiver's order.")],
        "pointer": pointer,
    }


def _document_matrices(
    station: Mapping[str, Any], channel: Sequence[str], pointer: str
) -> list[OperatorFamily]:
    """Return what a protocol document declared of a receiver: Grams or a matrix."""
    measurement = _mapping(station.get("measurement"))
    families: list[OperatorFamily] = []
    grams = measurement.get("port_grams")
    if isinstance(grams, Mapping) and grams:
        elements: list[OperatorElement] = [
            {"outcome": str(port), "matrix": matrix}
            for port, raw in grams.items()
            if (matrix := matrix_of(raw)) is not None
        ]
        if elements:
            size = len(elements[0]["matrix"])
            basis = list(channel) if len(channel) == size else _numbered(size)
            families.append({
                "kind": "port-grams",
                "title": "Port Grams as declared in the protocol document",
                "text": (
                    "The Gram matrix of each detector port over the channel "
                    "modes, as the document declares it; the engine builds the "
                    "receiver from these numbers."
                ),
                "claims": [],
                "blocks": [_block("channel modes", basis, elements,
                                  pointer_join(pointer, "measurement", "port_grams"))],
                "pointer": pointer_join(pointer, "measurement", "port_grams"),
            })
    instrument = matrix_of(measurement.get("instrument_matrix"))
    if instrument is not None:
        modes = [
            f"{item.get('path')}_{item.get('polarization')}"
            if isinstance(item, Mapping) and "path" in item else str(item)
            for item in _sequence(measurement.get("modes"))
        ]
        rows, columns = len(instrument), len(instrument[0])
        families.append({
            "kind": "instrument-matrix",
            "title": "Instrument matrix as declared in the protocol document",
            "text": (
                "The transfer matrix from the input modes (columns) to the "
                "receiver's modes (rows), as the document declares it."
            ),
            "claims": [],
            "blocks": [_block(
                "input modes to receiver modes",
                modes if len(modes) == rows else _numbered(rows),
                [{"outcome": "instrument", "matrix": instrument}],
                pointer_join(pointer, "measurement", "instrument_matrix"),
                column_basis=list(channel) if len(channel) == columns
                else _numbered(columns),
            )],
            "pointer": pointer_join(pointer, "measurement", "instrument_matrix"),
        })
    return families


def _document_pointer(record: Mapping[str, Any], station: Mapping[str, Any]) -> str:
    stations = _sequence(_at(record, "/payload/protocol_document/canonical/stations"))
    for index, item in enumerate(stations):
        if item is station:
            return f"/payload/protocol_document/canonical/stations/{index}"
    return "/payload/protocol_document/canonical/stations"


def _exact_window(domain: Mapping[str, Any]) -> Any:
    depths = {
        _mapping(item.get("exact_window")).get("depth")
        for item in _sequence(domain.get("per_setting"))
        if isinstance(item, Mapping)
    }
    depths.discard(None)
    if len(depths) == 1:
        return depths.pop()
    return sorted(depths, key=str) or None


def _station(
    record: Mapping[str, Any],
    raw: Mapping[str, Any],
    index: int,
    reduction_claims: list[str],
) -> SetupStation:
    """Return one station of a multi-station run (``stages.stations[i]``)."""
    config = analysed_config(record)
    pointer = f"/payload/stages/stations/{index}"
    receiver = _mapping(raw.get("receiver"))
    label = None if raw.get("factor") is None else str(raw.get("factor"))
    party = None if raw.get("party") is None else str(raw.get("party"))
    document = _document_station(record, label, party)
    route = raw.get("receiver_route")
    modes = _mapping(receiver.get("input_mode_space"))
    channel = [str(mode) for mode in _sequence(modes.get("channel_labels"))]
    inputs = [str(mode) for mode in _sequence(modes.get("input_labels"))] or channel
    bases = _photon_bases(receiver.get("block_dimensions"), channel)
    construction = _mapping(receiver.get("receiver_construction"))
    domain = _mapping(receiver.get("bound_quantifier_domain"))
    families: list[OperatorFamily] = []
    notes: list[str] = []
    claims: list[str] = []
    settings = _sequence(_mapping(receiver.get("photon_blocks")).get("settings"))
    # A receiver without a probe has one setting, off (receiver/def:probe):
    # said once, not in every title.
    only_off = [
        str(item.get("setting")) for item in settings if isinstance(item, Mapping)
    ] == ["off"]
    if only_off:
        notes.append(
            "This station has no probe: its one setting is off, the probe "
            "setting with no probe light ([[receiver/def:probe]]), so the "
            "measurement below is the station's only one."
        )
    for position, setting in enumerate(settings):
        if not isinstance(setting, Mapping):
            continue
        name = str(setting.get("setting", position))
        where = pointer_join(pointer, "receiver", "photon_blocks", "settings", position)
        # The setting's own label (None without a probe); not ``label``, the
        # station's factor label, which this loop once overwrote (stations of
        # BBM92 came out with label None).
        setting_label = None if only_off else name
        at = "" if only_off else f" at setting {name}"
        bare = _letter_blocks(setting.get("blocks"), bases, setting_label,
                              pointer_join(where, "blocks"))
        if bare:
            families.append({
                "kind": "photon-blocks",
                "title": "POVM per photon number" if only_off
                else f"POVM at setting {name}, per photon number",
                "text": (
                    "One operator per outcome on each photon-number block of "
                    "the channel modes, before dark counts: the measurement the "
                    "receiver applies to a pulse of that many photons."
                ),
                "claims": [_COMPILE_CLAIM] if route == "element-graph" else [],
                "blocks": bare,
                "pointer": pointer_join(where, "blocks"),
            })
        composed = _letter_blocks(setting.get("dark_composed"), bases, setting_label,
                                  pointer_join(where, "dark_composed"))
        if composed:
            families.append({
                "kind": "dark-composed",
                "title": f"POVM{at} with dark counts",
                "text": (
                    "The same blocks with the detectors' dark counts composed "
                    "in: what a pulse of that many photons produces including "
                    "dark clicks."
                ),
                "claims": [],
                "blocks": composed,
                "pointer": pointer_join(where, "dark_composed"),
            })
    if not settings:
        notes.append("The record holds no photon-number blocks for this station.")
    if route == "port-grams":
        family = _gram_family(receiver.get("port_grams"), inputs,
                              pointer_join(pointer, "receiver", "port_grams"),
                              declared=True)
        if family is not None:
            families.append(family)
    if document:
        families.extend(
            family for family in _document_matrices(
                document, channel, _document_pointer(record, document)
            )
            if not (route == "port-grams" and family["kind"] == "port-grams")
        )
    reduction = _mapping(raw.get("reduction"))
    target = _target_family(reduction, bases, pointer_join(pointer, "reduction"),
                            reduction_claims)
    if target is not None:
        families.append(target)
    else:
        notes.append("The record holds no squashed target POVM for this station.")
    if route == "element-graph":
        claims.append(_COMPILE_CLAIM)
    note = _mode_note(construction.get("elements"), record)
    if note:
        notes.append(note)
    normalization = _normalization_note(
        _mapping(receiver.get("efficiency_record")).get("normalization")
    )
    if normalization:
        notes.append(normalization)
    letters = _document_letters(document)
    outcome_alphabet = _mapping(receiver.get("outcome_alphabet"))
    return {
        "index": index,
        "label": label,
        "party": party,
        "name": _station_name(party, label),
        "route": None if route is None else str(route),
        "route_text": _route_text(route),
        "channel_modes": channel,
        "outcomes": _outcomes(
            outcome_alphabet.get("coarse_graining"), letters,
            _document_patterns(record, _station_id(document)),
            [str(item.get("label"))
             for item in _sequence(outcome_alphabet.get("letters"))
             if isinstance(item, Mapping)],
        ),
        "elements": _elements(construction.get("elements"), document),
        "edges": _edges(construction.get("edges")),
        "detectors": _detectors(
            _port_modes(construction.get("port_map"), document), document,
            receiver.get("efficiency_record"), config,
        ),
        "photon_cutoff": (
            domain.get("photon_cutoff")
            if isinstance(domain.get("photon_cutoff"), int) else None
        ),
        "exact_window": _exact_window(domain),
        "families": families,
        "notes": notes,
        "claims": claims,
        "pointer": pointer,
    }


#: What a mode name is.
_MODE_LABEL: Final = re.compile(r"^(?P<path>.+)_(?P<polarisation>[HV])$")


def _mode_note(elements: Any, record: Mapping[str, Any]) -> str:
    """Return what a mode name is, with an example from the station's elements.

    The example is the last ``path_H`` or ``path_V`` label an element acts on;
    without one, no note (the labels are then not of that form).
    """
    labels = [
        str(mode)
        for item in _sequence(elements) if isinstance(item, Mapping)
        for mode in _sequence(item.get("support"))
    ]
    found = [match for label in labels if (match := _MODE_LABEL.match(label))]
    if not found:
        return ""
    example = found[-1]
    return (
        "Mode names are the instance's labels, a path and a polarisation: "
        f"{example.group(0)} is {example.group('polarisation')}-polarised light "
        f"in path {example.group('path')}." + _readme(record)
    )


def _readme(record: Mapping[str, Any]) -> str:
    readme = _at(record, "/payload/instance/readme")
    if isinstance(readme, str) and readme:
        return f" The instance's own description is in {readme}."
    return ""


def _station_id(document: Mapping[str, Any]) -> str | None:
    return None if not document else str(document.get("id"))


def _edges(raw: Any) -> list[list[str]]:
    return [
        [str(part) for part in edge] for edge in _sequence(raw)
        if isinstance(edge, list)
    ]


def _station_name(party: str | None, label: str | None) -> str:
    name = _party_name(party)
    if name is not None:
        return f"{name}'s station"
    return label or "the receiver"


def _route_text(route: Any) -> str:
    if route is None:
        return "The record names no receiver route."
    return ROUTE_WORDS.get(str(route), str(route))


def _in_declared_order(labels: Iterable[str], order: Sequence[Any]) -> list[str]:
    """Return labels in a declared order, any the order lacks after it as found.

    WHY: a record written with sorted keys holds a mapping by outcome or
    signal in label order, (X,0) before (Z,0); the compiled alphabets keep
    the order the document declared.
    """
    found = list(labels)
    rank = {str(label): position for position, label in enumerate(order)}
    return sorted(found, key=lambda label: (rank.get(label, len(rank)),
                                            found.index(label)))


def _readout_order(record: Mapping[str, Any], party: str | None) -> list[Any]:
    """Return a party's readout alphabet in declared order, or ``[]``."""
    if party not in ("A", "B"):
        return []
    partition = _mapping(_at(record, "/payload/compiled/public/party_partition"))
    key = "alice_readout_alphabet" if party == "A" else "bob_readout_alphabet"
    return list(_sequence(partition.get(key)))


def _declared_family(
    declared: Any, pointer: str, order: Sequence[Any] = ()
) -> list[OperatorFamily]:
    """Return the declared finite POVM of the Band-A route, one family per factor.

    ``order`` is the declared order of the outcomes (the readout alphabet).
    """
    if not isinstance(declared, Mapping):
        return []
    factors = declared.get("factors")
    parts: list[tuple[str, Mapping[str, Any], str]] = []
    if isinstance(factors, list):
        for index, factor in enumerate(factors):
            if isinstance(factor, Mapping):
                name = _party_name(factor.get("party")) or str(factor.get("label"))
                parts.append((
                    f"Declared POVM of {name}",
                    _mapping(factor.get("members")),
                    pointer_join(pointer, "factors", index, "members"),
                ))
    else:
        parts.append(("Declared POVM", declared, pointer))
    families: list[OperatorFamily] = []
    for title, members, where in parts:
        members = {label: members[label]
                   for label in _in_declared_order(map(str, members), order)}
        blocks = _sector_family(members, [], {}, where, keyed=True)
        if blocks:
            families.append({
                "kind": "declared-povm",
                "title": title,
                "text": (
                    "The measurement operators as declared, one per outcome, "
                    "per sector; the record names no basis for these systems, "
                    "so basis states are numbered in the record's order."
                ),
                "claims": [_BAND_A_CLAIM],
                "blocks": blocks,
                "pointer": where,
            })
    return families


def _single_receiver(
    record: Mapping[str, Any], reduction_claims: list[str]
) -> SetupStation | None:
    """Return the one receiver of a single-receiver run (``receiver_construction``)."""
    construction = _at(record, "/payload/stages/receiver_construction")
    if not isinstance(construction, Mapping):
        return None
    config = analysed_config(record)
    pointer = "/payload/stages/receiver_construction"
    route = construction.get("receiver_route")
    document = _document_station(record, None, "B")
    # The receiver's party is the document's; a record without a document
    # does not name it, and none is assumed.
    party = None if document.get("party") is None else str(document.get("party"))
    port_map = construction.get("port_map")
    channel = [
        str(mode) for mode in _sequence(_mapping(port_map).get("channel_labels"))
    ] or [
        str(mode) for mode in _sequence(
            _mapping(document.get("measurement")).get("channel_modes"))
    ]
    readouts = _readout_order(record, party)
    families = _declared_family(construction.get("declared_povm"),
                                pointer_join(pointer, "declared_povm"), readouts)
    if document:
        families.extend(_document_matrices(document, channel,
                                           _document_pointer(record, document)))
    notes: list[str] = []
    note = _mode_note(construction.get("elements"), record)
    if note:
        notes.append(note)
    normalization = _normalization_note(construction.get("efficiency_normalization"))
    if normalization:
        notes.append(normalization)
    if route != "declared-finite-povm":
        notes.append(
            "On this route the record keeps the receiver's construction (its "
            "modes, port labels, block dimensions and residuals) but not its "
            "POVM operators or the squashed target POVM; the run computed them "
            "and handed them to the reduction without writing them."
        )
    sectors = _sequence(_at(record, "/payload/stages/reduction/target_sectors"))
    if sectors:
        labels = [
            ":".join(str(part) for part in _sequence(_mapping(item).get("label")))
            for item in sectors
        ]
        notes.append(
            "The squashed target POVM the proof works with has the sectors "
            + ", ".join(labels) + " (the reduction stage's target sectors)."
        )
    measurement = _mapping(document.get("measurement"))
    cutoff = construction.get("photon_cutoff")
    if not isinstance(cutoff, int):
        resolved = _fraction(_resolve(measurement.get("photon_cutoff"), config))
        cutoff = None if resolved is None else int(resolved)
    window = _resolve(measurement.get("exact_window"), config)
    letters = _document_letters(document)
    fallback = _in_declared_order((
        str(label) for label in _mapping(construction.get("declared_povm"))
        if label != "factors"
    ), readouts)
    claims = [_COMPILE_CLAIM] if route == "element-graph" else []
    return {
        "index": None,
        "label": None if not document else str(document.get("id")),
        "party": party,
        "name": _station_name(party, None),
        "route": None if route is None else str(route),
        "route_text": _route_text(route),
        "channel_modes": channel,
        "outcomes": _outcomes(
            None, letters,
            _document_patterns(record, _station_id(document)),
            fallback,
        ),
        "elements": _elements(construction.get("elements"), document),
        "edges": _edges(construction.get("edges")),
        "detectors": _detectors(
            _port_modes(None, document), document, None, config,
        ) if document else [],
        "photon_cutoff": cutoff,
        "exact_window": window,
        "families": families,
        "notes": notes,
        "claims": claims,
        "pointer": pointer,
    }


# --------------------------------------------------------------------------
# Source
# --------------------------------------------------------------------------


def _complex(entry: MatrixEntry) -> complex | None:
    """Return a ``[re, im]`` matrix entry as a complex number, or ``None``."""
    try:
        return complex(*(float(Fraction(part)) if isinstance(part, str)
                         else float(part) for part in entry))
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def _conjugates(
    operators: Sequence[OperatorElement], states: Sequence[OperatorElement]
) -> bool:
    """Whether each operator is its signal state's conjugate, weighted, one complex.

    Each operator a positive multiple of its signal state's complex
    conjugate, and some entry complex. Read off the two as the record holds
    them, never assumed: the sentence that says so is written only where it
    holds (to 1e-9 of the largest entry) and every operator's signal has a
    declared state.
    """
    by_label = {state["outcome"]: state["matrix"] for state in states}
    # The sentence speaks of all the operators, so each must have its state.
    if any(element["outcome"] not in by_label for element in operators):
        return False
    pairs = [(element["matrix"], by_label[element["outcome"]])
             for element in operators]
    complex_entry = False
    for operator, state in pairs:
        if len(operator) != len(state):
            return False
        found = [[_complex(entry) for entry in row] for row in operator]
        wanted = [[_complex(entry) for entry in row] for row in state]
        flat = [value for row in found for value in row]
        target = [value for row in wanted for value in row]
        if len(flat) != len(target) or None in flat or None in target:
            return False
        values = [value for value in flat if value is not None]
        conjugate = [value.conjugate() for value in target if value is not None]
        complex_entry = complex_entry or any(value.imag != 0 for value in values)
        trace = sum(conjugate[index * (len(state) + 1)].real
                    for index in range(len(state)))
        if trace <= 0:
            return False
        scale = sum(values[index * (len(state) + 1)].real
                    for index in range(len(state))) / trace
        largest = max(abs(value) for value in values) or 1.0
        if scale <= 0 or any(abs(value - scale * other) > 1e-9 * largest
                             for value, other in zip(values, conjugate, strict=True)):
            return False
    return complex_entry and bool(pairs)


def _source(record: Mapping[str, Any], roles: Roles) -> SetupSource | None:
    """Return the source part of the setup, read with the run's roles.

    WITH AN UNTRUSTED SOURCE AND ONE LETTER (BBM92's encoding) the
    declaration's letter is a placeholder the source does not emit: no signal row, and
    the text says so. The source-replacement block is shown only where the proof uses
    it, with a trusted source and d_A > 1.
    """
    source = _at(record, "/payload/compiled/source")
    note = _mapping(_at(record, "/payload/honest_model_note"))
    if not isinstance(source, Mapping) and not note:
        return None
    source = _mapping(source)
    mode = source.get("source_mode")
    trusted = note.get("source_trusted")
    if not isinstance(trusted, bool):
        trusted = None if mode is None else mode == "trusted"
    model = note.get("model")
    if trusted is False:
        text = (
            "The security analysis does not trust the source. Its model"
            + ("" if model is None else f" ({model})")
            + " only predicts the statistics an honest run is expected to show; "
            "those set the acceptance test, and nothing in the key length's "
            "security rests on the model being right."
        )
    elif trusted is True:
        text = (
            "The source is trusted: the analysis uses the declared ensemble of "
            "signals below, prepared with the weights shown."
        )
    else:
        text = "The record does not say whether the source is trusted."
    weights = _mapping(source.get("virtual_ensemble_weights"))
    signals = [
        {"label": str(label), "weight": weights.get(str(label))}
        for label in _sequence(source.get("signal_alphabet"))
    ]
    holder = party_name(roles.alice_party)
    if trusted is False and len(signals) == 1:
        text += (
            " The declaration's letter is the one placeholder "
            f"{signals[0]['label']}: {holder} draws no letter, and the data of a "
            "round are the stations' readouts."
        )
        signals = []
    families: list[OperatorFamily] = []
    replacement: OperatorFamily | None = None
    elements: list[OperatorElement] = []
    dimension = source.get("alice_dim")
    povm = _sequence(source.get("alice_povm"))
    if trusted is True and isinstance(dimension, int) and dimension > 1 and povm:
        elements = [
            {"outcome": str(signals[index]["label"]) if index < len(signals)
             else str(index),
             "matrix": matrix}
            for index, raw in enumerate(povm)
            if (matrix := matrix_of(raw)) is not None
        ]
        blocks = [_block(f"{holder}'s system", _numbered(dimension), elements,
                         "/payload/compiled/source/alice_povm")] if elements else []
        marginal = matrix_of(source.get("alice_marginal"))
        if marginal is not None:
            blocks.append(_block(
                f"{holder}'s reduced state", _numbered(dimension),
                [{"outcome": "reduced state", "matrix": marginal}],
                "/payload/compiled/source/alice_marginal",
            ))
        if blocks:
            replacement = {
                "kind": "source",
                "title": f"{holder}'s measurement in the source-replacement picture",
                "text": (
                    f"The trusted source as the proof sees it: {holder} holds one "
                    "half of an entangled state and measures it; each outcome "
                    "selects the signal sent. The record names no basis for "
                    f"{holder}'s system, so basis states are numbered."
                ),
                "claims": [],
                "blocks": blocks,
                "pointer": "/payload/compiled/source",
            }
            families.append(replacement)
    states = _mapping(_at(record, "/payload/protocol_document/canonical/source/states"))
    # In the source's declared signal order, not the record's sorted keys (n2).
    declared: list[OperatorElement] = [
        {"outcome": label, "matrix": matrix}
        for label in _in_declared_order(
            map(str, states), _sequence(source.get("signal_alphabet")))
        if (matrix := matrix_of(states[label])) is not None and len(matrix) > 1
    ]
    if replacement is not None and _conjugates(elements, declared):
        # A reader checking an operator against its signal state finds the
        # imaginary parts with opposite signs and reads a sign error (m7).
        replacement["text"] = (replacement["text"] or "") + (
            f" {holder}'s operators here are the weighted complex conjugates of "
            "the signal states below: where an entry is complex, its imaginary "
            "part has the opposite sign to the signal state's."
        )
    if trusted is True and declared:
        families.append({
            "kind": "source",
            "title": "Signal states as declared in the protocol document",
            "text": "The state the source prepares for each signal.",
            "claims": [],
            "blocks": [_block(
                "transmitted system", _numbered(len(declared[0]["matrix"])),
                declared, "/payload/protocol_document/canonical/source/states",
            )],
            "pointer": "/payload/protocol_document/canonical/source/states",
        })
    # The values the run analysed: a parameter a preparation replaced reads
    # as its prepared value (inputs.analysed_config).
    model_parameters = _mapping(analysed_config(record).get("model"))
    return {
        "mode": None if mode is None else str(mode),
        "trusted": trusted,
        "text": text,
        "honest_model": None if model is None else str(model),
        "honest_parameters": dict(model_parameters),
        "derivation": (
            None if note.get("model_derivation") is None
            else str(note.get("model_derivation"))
        ),
        "status": None if note.get("status") is None else str(note.get("status")),
        "signals": signals,
        "families": families,
        "pointer": (
            "/payload/compiled/source" if source
            else "/payload/honest_model_note"
        ),
    }


# --------------------------------------------------------------------------
# Protocol steps
# --------------------------------------------------------------------------


def _alphabet(values: Iterable[Any]) -> str:
    return ", ".join(str(value) for value in values)


def _announcements(public: Mapping[str, Any]) -> tuple[str, str | None] | None:
    transcript = [item for item in _sequence(public.get("transcript"))
                  if isinstance(item, Mapping)]
    if transcript:
        parts = []
        for position, message in enumerate(transcript):
            sender = _party_name(message.get("sender")) or "a party"
            order = "first" if position == 0 else "then"
            parts.append(
                f"{order} {sender} announces one of "
                f"{_alphabet(_sequence(message.get('alphabet')))}"
            )
        text = "; ".join(parts) + "."
        return text[0].upper() + text[1:], "/payload/compiled/public/transcript"
    alice = _sequence(public.get("announce_alice"))
    bob = _sequence(public.get("announce_bob"))
    if alice or bob:
        parts = []
        for name, table in ((party_name("A"), alice), (party_name("B"), bob)):
            if table:
                values = dict.fromkeys(
                    str(row[1]) for row in table
                    if isinstance(row, list) and len(row) == 2
                )
                parts.append(f"{name} announces one of {_alphabet(values)}")
        return "; ".join(parts) + ".", "/payload/compiled/public/announce_alice"
    return None


def _refusing_stage(record: Mapping[str, Any]) -> str | None:
    """Return the stage a refused record names as refusing, else ``None``."""
    if not _at(record, "/payload/refused"):
        return None
    for stage, entry in _mapping(_at(record, "/payload/stages")).items():
        if isinstance(entry, Mapping) and entry.get("refused") is True:
            return str(stage)
    return None


#: The path's stages in order (runs/stages.py), which tells whether a refused
#: run stopped before a step's stage.
_STAGE_ORDER: Final[tuple[str, ...]] = tuple(str(stage) for stage in SliceStage)


def _missing_step(record: Mapping[str, Any], stage: SliceStage) -> str:
    """Return what a protocol step the record does not hold says.

    A run refused at or before the step's stage never reached it, which is
    said as such: "the record holds no public choice" would read as a fact
    about the protocol. Otherwise
    the record merely does not hold the step (a refused record keeps its
    refusing stage alone).
    """
    refused = _refusing_stage(record)
    if refused in _STAGE_ORDER and (
        _STAGE_ORDER.index(refused) <= _STAGE_ORDER.index(str(stage))
    ):
        return (f"Not reached: the run was refused at its {refused} stage, "
                "before this step.")
    return "The record does not hold this step."


def _protocol(
    record: Mapping[str, Any], stations: Sequence[SetupStation], roles: Roles
) -> list[ProtocolStep]:
    config = _mapping(_at(record, "/payload/config"))
    public = _mapping(_at(record, "/payload/compiled/public"))
    source = _mapping(_at(record, "/payload/compiled/source"))
    absent = "The record does not hold this step."
    # A step of the compiled specification (source, measurement, choices,
    # announcements, key map) on a record that holds none.
    uncompiled = _missing_step(record, SliceStage.COMPILATION)
    steps: list[ProtocolStep] = []

    rounds = config.get("rounds")
    if rounds is None:
        steps.append({"title": "Rounds", "text": absent, "pointer": None})
    else:
        # What a round is stands before the steps (SetupSection.round).
        count = f"{rounds:,}" if isinstance(rounds, int) else str(rounds)
        steps.append({"title": "Rounds",
                      "text": f"The protocol runs n = {count} rounds.",
                      "pointer": "/payload/config/rounds"})

    mode = source.get("source_mode")
    signals = _sequence(source.get("signal_alphabet"))
    if mode is None:
        steps.append({"title": "Source", "text": uncompiled, "pointer": None})
    elif roles.source_trusted is False:
        # EB-AWARE: an untrusted source
        # delivers systems; it emits no declared signal.
        letter_holder = party_name(roles.alice_party)
        delivered = (
            "one system to each station" if len(stations) > 1
            else "one system to the station" if stations else "its systems"
        )
        text = f"In every round the untrusted source delivers {delivered}"
        if roles.measures_a(roles.alice_party):
            text += (
                f", and one to {letter_holder}, who measures it to obtain the round's "
                f"letter, one of {len(signals)} ({_alphabet(signals)})"
            )
        steps.append({"title": "Source", "text": text + "; see Source below.",
                      "pointer": "/payload/compiled/source"})
    else:
        text = (
            f"In every round the {mode} source emits one signal"
            + (f" of {len(signals)} ({_alphabet(signals)})" if len(signals) > 1 else "")
            + "; see Source below."
        )
        steps.append({"title": "Source", "text": text,
                      "pointer": "/payload/compiled/source"})

    if stations:
        who = _joined(
            f"{station['name']} ({station['route'] or 'route not recorded'})"
            for station in stations
        )
        steps.append({
            "title": "Measurement",
            "text": f"Each round is measured at {who}; see the stations below.",
            "pointer": (
                "/payload/stages/stations" if stations[0]["index"] is not None
                else "/payload/stages/receiver_construction"
            ),
        })
    else:
        steps.append({"title": "Measurement", "text": uncompiled, "pointer": None})

    weightings = _choice_weightings(public)
    choices = source.get("public_choices")
    test_fraction = _analysed_test_fraction(record, config)
    # Alice's presentation choice, said beside every weighted choice too
    # (a run may have both, and A-COIN covers both).
    presented: str | None = None
    if isinstance(choices, Mapping):
        weights = _mapping(choices.get("weights"))
        presented = (
            f"{_party_name(choices.get('party')) or 'a party'} draws a public "
            "choice: " + ", ".join(
                f"{choice} with probability {exact_with_decimal(weights.get(choice))}"
                for choice in _sequence(choices.get("choices"))
            ) + "."
        )
    # A measuring party's setting-independent choice, which A-COIN binds
    # beside Alice's (bb84's Bob draws Z or X).
    measured = _station_choices(record, choices, stations)
    said = [*([] if presented is None else [presented]), *measured]
    if weightings:
        # EVERY WEIGHTED FACTOR (record 0.30.0),
        # named by its station. Who draws the choice is not said as such:
        # A-COIN (ii) says a party whose readout records the setting draws a
        # setting-dependent one, so where the setting has two or more values
        # the sentence names whose readout records it, where the role vector
        # knows (roles.StationRoles.setting_recorded_by), else the station only.
        parts = []
        for weighting, pointer in weightings:
            matrix = _mapping(weighting.get("matrix"))
            where = _weighting_station(weighting, stations, record)
            settings = _sequence(weighting.get("setting_alphabet"))
            if len(settings) > 1:
                by_setting: dict[str, list[str]] = {}
                for key, value in matrix.items():
                    setting, _, choice = str(key).partition("|")
                    by_setting.setdefault(setting, []).append(
                        f"{choice} with probability {exact_with_decimal(value)}"
                    )
                sentence = (
                    f"At {where}, a public choice is drawn whose probabilities "
                    "depend on the station's private setting: " + "; ".join(
                        f"at setting {setting}, {', '.join(items)}"
                        for setting, items in by_setting.items()
                    ) + "."
                )
                recorder = next((
                    station.setting_recorded_by for station in roles.stations
                    if station.setting_recorded_by is not None and (
                        station.factor is None
                        or station.factor == str(weighting.get("factor"))
                    )
                ), None)
                if recorder is not None:
                    sentence += (
                        f" {party_name(recorder)}'s readout records the setting."
                    )
            else:
                sentence = f"At {where}, a public choice is drawn: " + ", ".join(
                    f"{str(key).split('|', 1)[-1]} with probability "
                    f"{exact_with_decimal(value)}"
                    for key, value in matrix.items()
                ) + "."
            parts.append((sentence, pointer))
        text = " ".join([*said, *(sentence for sentence, _ in parts)])
        if test_fraction is not None:
            text += f" The test fraction is {test_fraction}."
        steps.append({
            "title": "Public choice (test coin)" if not said
            else "Public choices (and the test coin)",
            "text": text, "pointer": parts[0][1],
        })
    elif said:
        steps.append({
            "title": "Public choice" if len(said) == 1 else "Public choices",
            "text": " ".join(said),
            "pointer": "/payload/compiled/source/public_choices"
            if presented is not None else None,
        })
    elif _at(record, "/payload/compiled") is None:
        # No compiled specification: what the protocol declares is unknown
        # here, so nothing is said of it.
        steps.append({"title": "Public choice", "text": uncompiled, "pointer": None})
    else:
        steps.append({"title": "Public choice", "text": (
            "The record holds no public choice (no test coin and no basis choice "
            "announced separately)."
        ), "pointer": None})

    announced = _announcements(public)
    if announced is not None and (_sequence(public.get("announce_alice"))
                                  or _sequence(public.get("announce_bob"))):
        # When a basis becomes public: the record's
        # announcement tables compute each announcement from the announcing
        # party's own readout, and A-SEQ (a premise of every run) puts every
        # measurement of a round before its public messages.
        announced = (
            announced[0] + " Each announcement is computed from the announcing "
            "party's own readout (the record's announcement tables), and "
            "[[A-SEQ]] states the order within a round: every party's "
            "measurement, then the round's public messages. So the analysis "
            "assumes that no announcement, a basis included, comes before a "
            "measurement of its round; you vouch for this under [[A-SEQ]].",
            announced[1],
        )
    steps.append(
        {"title": "Announcements", "text": announced[0], "pointer": announced[1]}
        if announced is not None
        else {"title": "Announcements", "text": uncompiled, "pointer": None}
    )

    key_map = [row for row in _sequence(public.get("key_map"))
               if isinstance(row, list) and len(row) == 2]
    holder = _party_name(public.get("key_holder"))
    if key_map:
        keyed = sum(1 for row in key_map if row[1] != "perp")
        bases = _mapping(config.get("device")).get("key_bases")
        # "Signal" only where the letter carries one: combined_words.
        combined = combined_words(roles)
        text = (
            f"A round gives a raw key bit when its announcements pass sifting: "
            f"{keyed} of the {len(key_map)} combinations of {combined} "
            f"map to a key bit, the rest are discarded. "
            + ("" if holder is None else f"{holder} holds the key")
            + (
                "" if public.get("key_alphabet") is None
                else " over the alphabet "
                + _alphabet(_sequence(public.get("key_alphabet")))
            )
            + "."
            + ("" if bases is None else f" Key bases: {bases}.")
        )
        steps.append({"title": "Sifting and key map", "text": text,
                      "pointer": "/payload/compiled/public/key_map"})
    else:
        steps.append({"title": "Sifting and key map", "text": uncompiled,
                      "pointer": None})

    # The step points at the Acceptance test part, which a record without the
    # acceptance construction does not have.
    acceptance = _at(record, "/payload/stages/acceptance_construction")
    steps.append({
        "title": "Acceptance test",
        "text": "The parties estimate the acceptance statistics on the whole run "
                "and abort unless they pass; see Acceptance test below."
        if acceptance is not None
        else _missing_step(record, SliceStage.ACCEPTANCE_CONSTRUCTION),
        "pointer": "/payload/stages/acceptance_construction"
        if acceptance is not None else None,
    })

    parameters = _mapping(config.get("parameters"))
    deductions = _mapping(_at(record, "/payload/stages/key_rate/deductions"))
    lambda_ec = parameters.get("lambda_ec")
    deducted = _at(record, "/payload/stages/key_rate/key_length") is not None
    steps.append({
        "title": "Error correction",
        "text": absent if lambda_ec is None else (
            f"One-way error correction; its transcript leaks λ_EC = {lambda_ec} bits"
            # Only a key length deducts it; a refused record has none.
            + (", which the key length deducts." if deducted else ".")
        ),
        "pointer": (
            None if lambda_ec is None
            else "/payload/config/parameters/lambda_ec"
        ),
    })
    verification = deductions.get("error_verification")
    eps_ev = parameters.get("eps_ev")
    if verification is None and eps_ev is None:
        steps.append({"title": "Error verification", "text": absent, "pointer": None})
    else:
        text = "The parties compare a hash of the corrected keys"
        if eps_ev is not None:
            text += f" (failure probability ε_EV = {_text(eps_ev)})"
        if verification is not None:
            text += f"; the key length deducts {_text(verification)} bits for it"
        steps.append({
            "title": "Error verification",
            "text": text + ".",
            "pointer": (
                "/payload/stages/key_rate/deductions/error_verification"
                if verification is not None else "/payload/config/parameters/eps_ev"
            ),
        })
    key_length = _at(record, "/payload/stages/key_rate/key_length")
    eps_pa = parameters.get("eps_pa")
    steps.append({
        "title": "Privacy amplification",
        "text": (
            "The record holds no key length, so no privacy amplification is "
            "stated." if key_length is None else
            "A two-universal hash shortens the corrected key to \u2113 = "
            f"{key_length:,} "
            "bits" + ("" if eps_pa is None else
                      f", secret except with probability ε_PA = {_text(eps_pa)}")
            + "."
        ),
        "pointer": (
            None if key_length is None
            else "/payload/stages/key_rate/key_length"
        ),
    })
    return steps


# --------------------------------------------------------------------------
# Acceptance test and expected statistics
# --------------------------------------------------------------------------


def _failure_words(certified: Any, budget: Any) -> str:
    """Return the chance an honest run fails the test, the quantity before ε*.

    The decimal is rounded up, so that "at most" stays true; the exact
    figure is the table's. The budget reads decimal first.
    """
    if certified is None:
        return ""
    shown = upper_decimal(certified)
    if shown is None:
        bound = f"ε* = {_with_decimal(certified)}"
    else:
        decimal, exact = shown
        bound = (f"{decimal} (ε*" + ("" if exact else ", rounded up; its exact "
                                    "value is in the table below") + ")")
    return (
        f"An honest run fails it with probability at most {bound}"
        + ("" if budget is None
           else f", within your completeness budget of {exact_with_decimal(budget)} "
           "(the completeness parameter ε_comp you allow)")
        + "."
    )


def _acceptance(
    record: Mapping[str, Any], claims: list[str], roles: Roles
) -> SetupAcceptance | None:
    stage = _at(record, "/payload/stages/acceptance_construction")
    if not isinstance(stage, Mapping):
        return None
    outcomes = [str(item) for item in _sequence(stage.get("outcomes"))]
    if not outcomes:
        outcomes = [str(item) for item in _sequence(
            _at(record, "/payload/compiled/public/acceptance_alphabet"))]
    support = stage.get("support")
    budget = _at(record, "/payload/config/completeness_budget")
    certified = stage.get("completeness_certified")
    rows = len(outcomes) if outcomes else None
    text = (
        f"The run records one acceptance value per round, from {len(outcomes)} "
        "outcomes, and accepts only if the observed frequency of every outcome "
        "lies in the box of intervals built around the honest model's "
        "probabilities"
        + ("" if stage.get("endpoint_rule") is None
           else f" (endpoint rule {stage.get('endpoint_rule')})")
        + ". "
        + _failure_words(certified, budget)
    ).strip()
    if stage.get("refused"):
        text = "The acceptance construction was refused; see the checks."
    honest = _mapping(stage.get("honest_distribution"))
    probabilities: list[dict[str, Any]] = []
    for outcome in outcomes:
        value = _fraction(honest.get(outcome))
        if value is not None:
            probabilities.append({"outcome": outcome, "probability": float(value)})
    rounds = _at(record, "/payload/config/rounds")
    categories = _acceptance_categories(
        stage.get("box"), outcomes, probabilities,
        rounds if isinstance(rounds, int) and not isinstance(rounds, bool) else None,
    )
    if categories and not stage.get("refused"):
        text += (
            " The table of acceptance categories below gives, for each outcome, "
            "the honest model's probability and the interval its observed "
            "frequency must lie in, ends included, and the counts that interval "
            "admits out of the rounds of the run: a run whose count of any "
            "outcome falls outside its range is not accepted "
            "([[statistics/binomial-box/def:construction]])."
        )
        text += _zero_count_words(categories)
    elif probabilities and not stage.get("refused"):
        text += (
            " The record does not list the intervals themselves: it holds each "
            "outcome's honest probability (below), the endpoint rule and the "
            "completeness budget; with the round count n, which outcomes are "
            "constrained and how the budget is split, the engine builds them "
            "from these ([[statistics/binomial-box/def:construction]])."
        )
    if roles.label_order is not None and not stage.get("refused"):
        # The label convention is the document's, not the
        # transcript order (roles.label_order).
        first, second = (party_name(party) for party in roles.label_order)
        text += (
            f" In an acceptance value written with a bar, {first}'s announcement "
            f"stands before the bar and {second}'s after it."
        )
    return {
        "rows": rows,
        "outcomes": outcomes,
        "support": len(support) if isinstance(support, list) else None,
        "endpoint_rule": None if stage.get("endpoint_rule") is None
        else str(stage.get("endpoint_rule")),
        "geometry": (
            None if stage.get("geometry") is None
            else str(stage.get("geometry"))
        ),
        "completeness_budget": budget,
        "completeness_certified": None if certified is None else str(certified),
        "text": text,
        "claims": claims,
        "pointer": "/payload/stages/acceptance_construction",
        "honest": probabilities,
        "categories": categories,
    }


def zero_count_outcomes(categories: Sequence[AcceptanceCategory]) -> list[str]:
    """Return the acceptance outcomes whose allowed count is exactly 0.

    The rule of :func:`_zero_count_words`: an upper count endpoint of 0, or
    where the record gives no round count, an upper frequency of 0.
    """
    return [
        str(row["outcome"]) for row in categories
        if (row["count_max"] == 0 if row["count_max"] is not None
            else Fraction(row["upper"]) == 0)
    ]


def _zero_count_words(categories: Sequence[AcceptanceCategory]) -> str:
    """Return the sentence on outcomes whose allowed count is exactly 0, or "".

    WHY: a reader skimming the table misses that an outcome admitting no
    count makes one such round fail the test. An outcome admits no count when
    its upper count endpoint is 0 (``floor(n q^+) = 0``), or, where the
    record gives no round count, when ``q^+`` is 0. One such round puts the
    outcome's frequency outside its interval, so the acceptance test fails and
    both parties abort (statistics/binomial-box/def:construction,
    meat-core/def:postprocessing-model), as A-CONFORM (i) requires of the
    implementation, which the sentence links: the closure table carries the
    premise, not the definition (``PARAPHRASES['setup.acceptance_zero']``).
    """
    zero = [
        row for row in categories
        if (row["count_max"] == 0 if row["count_max"] is not None
            else Fraction(row["upper"]) == 0)
    ]
    if not zero:
        return ""
    if len(zero) == 1:
        return (
            f" One outcome, {zero[0]['outcome']}, admits a count of exactly 0: a "
            "single round with it fails the acceptance test, and your "
            "implementation must abort the run ([[A-CONFORM]])."
        )
    return (
        f" {len(zero)} of the {len(categories)} outcomes admit a count of exactly "
        "0: a single round with any of them fails the acceptance test, and your "
        "implementation must abort the run ([[A-CONFORM]])."
    )


def _acceptance_categories(
    box: Any,
    outcomes: Sequence[str],
    probabilities: Sequence[Mapping[str, Any]],
    rounds: int | None,
) -> list[AcceptanceCategory]:
    """Return one row per outcome of the record's acceptance box, in order.

    The box is ``[q^-, q^+]`` per outcome (record 0.36.0); an accepted run's
    frequency ``k / n`` of each outcome lies in it, ends included, so the
    counts it admits are ``ceil(n q^-)`` to ``floor(n q^+)``, computed
    exactly. Empty where the record carries no box.
    """
    if not isinstance(box, Mapping):
        return []
    honest = {str(row["outcome"]): row["probability"] for row in probabilities}
    rows: list[AcceptanceCategory] = []
    for outcome in outcomes:
        entry = box.get(outcome)
        if not isinstance(entry, Mapping):
            continue
        lower = _fraction(entry.get("lower"))
        upper = _fraction(entry.get("upper"))
        if lower is None or upper is None:
            continue
        count_min = count_max = None
        if rounds is not None:
            count_min = math.ceil(lower * rounds)
            count_max = math.floor(upper * rounds)
        rows.append({
            "outcome": outcome,
            "probability": honest.get(outcome),
            "lower": str(lower),
            "upper": str(upper),
            "count_min": count_min,
            "count_max": count_max,
            "rounds": rounds,
        })
    return rows


def _analysed_test_fraction(
    record: Mapping[str, Any], config: Mapping[str, Any]
) -> str | None:
    """Return the test fraction the run analysed, the requested one beside it.

    The record's configuration holds the requested ``device.test_fraction``;
    where a preparation replaced it (:func:`prepared_inputs`) the run analysed
    the prepared value, which is what is said, with the request where the two
    differ.
    """
    requested = _mapping(config.get("device")).get("test_fraction")
    if requested is None:
        return None
    prepared = prepared_inputs(record).get("test_fraction")
    if prepared is None or same_number(prepared[0], requested):
        return exact_with_decimal(requested if prepared is None else prepared[0])
    return analysed_words(prepared[0], requested)


def _readout_map(rows: Any) -> dict[tuple[str, str], str]:
    found: dict[tuple[str, str], str] = {}
    for row in _sequence(rows):
        if (
            isinstance(row, list) and len(row) == 2 and isinstance(row[0], list)
            and len(row[0]) == 2
        ):
            found[(str(row[0][0]), str(row[0][1]))] = str(row[1])
    return found


def _holder_announcements(
    public: Mapping[str, Any], holder: str
) -> dict[str, str] | None:
    """Return the key holder's announcement per readout, or ``None``."""
    table = _sequence(public.get("announce_alice" if holder == "A" else "announce_bob"))
    found = {
        str(row[0]): str(row[1]) for row in table
        if isinstance(row, list) and len(row) == 2
    }
    if found:
        return found
    for message in _sequence(public.get("transcript")):
        if not isinstance(message, Mapping) or message.get("sender") != holder:
            continue
        mapping: dict[str, set[str]] = {}
        for row in _sequence(message.get("table")):
            if isinstance(row, list) and len(row) == 3 and row[1] == []:
                mapping.setdefault(str(row[0]), set()).add(str(row[2]))
        if mapping and all(len(values) == 1 for values in mapping.values()):
            return {readout: next(iter(values)) for readout, values in mapping.items()}
    return None


def _letter_of(
    readout: str, letters: set[str], support: Mapping[str, str]
) -> str | None:
    if readout in letters:
        return readout
    return support.get(readout)


def _expected(
    record: Mapping[str, Any], stations: Sequence[SetupStation], roles: Roles
) -> tuple[list[ExpectedStatistic], list[str]]:
    """Return the honest model's expected statistics and what could not be formed."""
    pointer = "/payload/stages/acceptance_construction/raw_joint_distribution"
    raw = _at(record, pointer)
    public = _mapping(_at(record, "/payload/compiled/public"))
    if not isinstance(raw, Mapping) or not raw:
        return [], ["The record holds no honest raw joint distribution, so no "
                    "expected statistic is given."]
    joint: dict[str, Fraction] = {}
    for key, value in raw.items():
        found = _fraction(value)
        if found is None:
            return [], ["The honest raw joint distribution is not exact, so no "
                        "expected statistic is given."]
        joint[str(key)] = found
    key_map = _readout_map(public.get("key_map"))
    partition = _mapping(public.get("party_partition"))
    alice = _readout_map(partition.get("alice_readout"))
    bob = _readout_map(partition.get("bob_readout"))
    statistics: list[ExpectedStatistic] = []
    notes: list[str] = []

    def probability(outcome: tuple[str, str]) -> Fraction:
        return joint.get(f"{outcome[0]}|{outcome[1]}", Fraction(0))

    keyed = {outcome: bit for outcome, bit in key_map.items() if bit != "perp"}
    if key_map:
        total = sum((probability(outcome) for outcome in keyed), Fraction(0))
        statistics.append({
            "name": "Probability that a round gives a raw key bit",
            "value": float(total),
            "how": (
                "The sum of the honest raw joint distribution over every "
                f"combination of {combined_words(roles)} the compiled key map "
                "sends to a key bit."
            ),
            "pointer": pointer,
        })
        holder = str(public.get("key_holder", ""))
        other = bob if holder == "A" else alice
        mine = alice if holder == "A" else bob
        announcements = _holder_announcements(public, holder)
        groups: dict[str, list[tuple[str, str]]] = {}
        for outcome in keyed:
            readout = mine.get(outcome)
            label = (
                None if announcements is None or readout is None
                else announcements.get(readout)
            )
            groups.setdefault(label or "all key rounds", []).append(outcome)
        if other and groups:
            holder_name = _party_name(holder) or "the key holder"
            for label, outcomes in groups.items():
                mass = sum((probability(outcome) for outcome in outcomes), Fraction(0))
                if mass == 0:
                    continue
                by_view: dict[str, dict[str, Fraction]] = {}
                for outcome in outcomes:
                    view = other.get(outcome)
                    if view is None:
                        break
                    bits = by_view.setdefault(view, {})
                    bit = keyed[outcome]
                    bits[bit] = bits.get(bit, Fraction(0)) + probability(outcome)
                else:
                    error = sum(
                        (sum(bits.values(), Fraction(0)) - max(bits.values())
                         for bits in by_view.values()),
                        Fraction(0),
                    )
                    name = (
                        "Expected QBER" if label == "all key rounds"
                        else f"Expected QBER, key rounds {holder_name} announces "
                        f"{label}"
                    )
                    statistics.append({
                        "name": name,
                        "value": float(error / mass),
                        "how": (
                            "Among these key rounds of the honest raw joint "
                            f"distribution, the probability that {holder_name}'s key "
                            "bit differs from the bit the other party most likely "
                            "holds given their own readout."
                        ),
                        "pointer": pointer,
                    })
                    continue
                notes.append(f"No QBER for {label}: a key round's readout of the "
                             "other party is not in the record's party partition.")
        elif not other:
            notes.append("The record's party partition is absent, so no QBER is given.")
    else:
        notes.append("The record holds no compiled key map, so neither the key-round "
                     "probability nor the QBER is given.")

    weighted = _choice_weightings(public)
    for station in stations:
        # The support of the weighting declared at THIS station's factor, the
        # only one whose emitted letters its readouts carry.
        weighting = next(
            (item for item, _ in weighted
             if _weighting_matches(item, station, record)),
            {},
        )
        support = {
            str(row[0]): str(row[1]) for row in _sequence(weighting.get("support"))
            if isinstance(row, list) and len(row) >= 2
        }
        party = station["party"]
        readouts = alice if party == "A" else bob if party == "B" else {}
        silent = {
            outcome["letter"] for outcome in station["outcomes"]
            if outcome["patterns"] == [[]]
        }
        letters = {outcome["letter"] for outcome in station["outcomes"]}
        if not readouts or not silent:
            continue
        mass = Fraction(0)
        complete = True
        for outcome, readout in readouts.items():
            letter = _letter_of(readout, letters, support)
            if letter is None:
                complete = False
                break
            if letter not in silent:
                mass += probability(outcome)
        if not complete:
            notes.append(f"No detection probability for {station['name']}: its "
                         "readouts do not map onto its outcome letters.")
            continue
        statistics.append({
            "name": f"Detection probability at {station['name']}",
            "value": float(mass),
            "how": (
                "The honest probability that at least one detector of the station "
                "clicks: the sum of the raw joint distribution over every readout "
                f"whose letter is not {_joined(sorted(silent), 'or')}."
            ),
            "pointer": pointer,
        })
    return statistics, notes


# --------------------------------------------------------------------------
# The section
# --------------------------------------------------------------------------


def _roots(record: Mapping[str, Any], module: str) -> list[str]:
    roots = _mapping(_at(record, "/payload/assumption_manifest/roots")).get(module)
    return [str(root) for root in _sequence(roots)]


def build_setup(
    record: Mapping[str, Any], known: Callable[[str], bool] | None = None
) -> SetupSection:
    """Return ``sections.setup`` of the report of ``record``.

    ``known`` says whether the report can link a claim id (the closure table
    carries it); a claim it does not know is left out of the ``claims`` lists.
    """
    def linked(ids: Iterable[str]) -> list[str]:
        return [claim for claim in dict.fromkeys(ids) if known is None or known(claim)]

    reduction_claims = linked([*_roots(record, "reductions"), _EMIT_CLAIM])[:1]
    stations: list[SetupStation] = []
    raw_stations = _at(record, "/payload/stages/stations")
    station_notes: list[str] = []
    if isinstance(raw_stations, list) and raw_stations:
        for index, raw in enumerate(raw_stations):
            if isinstance(raw, Mapping):
                stations.append(_station(record, raw, index, reduction_claims))
    else:
        single = _single_receiver(record, reduction_claims)
        if single is not None:
            stations.append(single)
        else:
            station_notes.append("The record holds no receiver stage, so no "
                                 "station is described.")
    for station in stations:
        for family in station["families"]:
            family["claims"] = linked(family["claims"])
        station["claims"] = linked(station["claims"])
    roles = run_roles(_mapping(record.get("payload")))
    acceptance = _acceptance(
        record,
        linked([*(root for root in _roots(record, "statistics")
                  if root.endswith(":completeness-bound")), _COMPLETENESS_CLAIM])[:1],
        roles,
    )
    expected, expected_notes = _expected(record, stations, roles)
    source = _source(record, roles)
    source_notes = [] if source is not None else [
        "The record holds no compiled source, so the source is not described."
    ]
    rounds = _at(record, "/payload/config/rounds")
    return {
        "round": None if rounds is None else round_block(
            _engaged_ids(record), roles.source_trusted
        ),
        "protocol": _protocol(record, stations, roles),
        "source": source,
        "stations": stations,
        "acceptance": acceptance,
        "expected": expected,
        # Said by build.py, which reads the inputs (explain.expected_basis).
        "expected_basis": "",
        "source_notes": source_notes,
        "station_notes": station_notes,
        "expected_notes": expected_notes,
    }


def setup_claims(setup: SetupSection) -> list[str]:
    """Return every claim id the setup section cites, once, in order."""
    found: list[str] = []
    for station in setup["stations"]:
        found.extend(station["claims"])
        for family in station["families"]:
            found.extend(family["claims"])
    source = setup["source"]
    if source is not None:
        for family in source["families"]:
            found.extend(family["claims"])
    acceptance = setup["acceptance"]
    if acceptance is not None:
        found.extend(acceptance["claims"])
    return list(dict.fromkeys(found))
