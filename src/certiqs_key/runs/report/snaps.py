"""The report's "Measurement snaps": how every snap of a measurement entered the result.

WHY THIS EXISTS. Every measurement-family snap a run makes is disclosed: a
block the model gives exactly on the lattice is kept, and every other block is
moved by one fidelity-first procedure (``foundations/req:snap-reference``). A
moved block that the key length still reads rests on assumption A-SNAP, and a
user acts on its group, of which there are four, each with its fix. The snaps are
clearly documented and traced in the run output, and this module is the report
half of that: a pure projection of
what the record already holds --

* the instance's per-setting snap records (``payload.snaps.instance`` or each
  station's ``rows_adaptation``, ``measurement_snaps``; ``foundations/
  req:who-snaps``), with the run's decision written on every block;
* the emission normaliser's per-sector records (``payload.snaps.producer`` or
  each station's ``reduction.emission_record``; ``reductions/
  req:emission-record``);
* the run's decision on the direct route (``payload.snaps.reference_companion``;
  ``meat-core/frank-wolfe/req:bracket-on-reference``);
* the two run settings (``payload.config.parameters``) and whether the
  assumption manifest lists A-SNAP.

THE DIRECT ROUTE. Where the run's first-order number is the bound on the
receiver's reference companion, evaluated at the points the search on the
snapped measurement found, every moved block on which the companion carries
your model is EVALUATED OFF ITS SNAP (``foundations/def:evaluated-off-snap``):
the key length reads your receiver model there, the snap only steered the
search, and the block does not rest on A-SNAP. So does the reduction's own
rounding, which the companion bypasses. A kept block is the model itself and
is named as kept, never counted as evaluated off its snap. The record's
``snaps.reference_companion`` is the run's decision, and every reading here
takes it.

FOUR GROUPS (``foundations/req:snap-reference`` (iii)): no usable reference,
reference bracket withdrawn, reference bracket not evaluated, last resort. The
sentences speak in groups and their fixes; the table keeps the cause and its
detailed fix beside the group.

THE RECORDS IT READS. Record 0.29.0's: the block statuses ``kept`` and
``moved`` of 0.28.0, with the strict option keyed ``strict_snaps``. An older
record names its strict option by the old key or made its snaps by a
procedure that no longer exists, and its report carries no measurement-snap
section.

THE PLAIN-WORDS SENTENCES ARE RUN-TIER PROSE, and the exception is deliberate:
the claims state the record, not how a user reads it, and the section is
written "in plain words". Every sentence restates a row of this section; no
number is computed that the record does not hold except counts of its rows and
the largest recorded radius.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any, Final

from certiqs_key.foundations.resting import RestingGroup
from certiqs_key.runs.report.inputs import pointer_join, resolve_pointer
from certiqs_key.runs.report.model import (
    EmissionSnap,
    MeasurementSnaps,
    SnapBlock,
    SnapRow,
)
from certiqs_key.runs.roles import party_name

__all__ = [
    "GROUP_WHY",
    "SNAP_ASSUMPTION",
    "SNAP_RECORD_VERSIONS",
    "measurement_snaps",
    "plain_sentences",
    "resting_sectors",
    "snap_rows",
]

#: The assumption a moved block rests on where the run does not evaluate it
#: off its snap (``foundations/ass:snapped-measurement``).
SNAP_ASSUMPTION: Final[str] = "A-SNAP"

#: The record shapes whose snaps this section reads: record 0.29.0's, made by
#: the procedure that keeps or moves a block, with the renamed strict option,
#: and 0.30.0's to 0.46.0's, whose snaps did not move (0.35.0 adds two causes
#: of the group reference bracket withdrawn and the decision's ``fallback``).
SNAP_RECORD_VERSIONS: Final[tuple[str, ...]] = (
    "0.29.0", "0.30.0", "0.31.0", "0.32.0", "0.33.0", "0.34.0", "0.35.0",
    "0.36.0", "0.37.0", "0.38.0", "0.39.0", "0.40.0", "0.41.0", "0.42.0",
    "0.43.0", "0.44.0", "0.45.0", "0.46.0",
)

def _count_blocks(count: int, noun: str = "block") -> str:
    """Return a count of blocks in agreement: ``1 block``, ``4 blocks`` (n3)."""
    return f"{count} {noun}" + ("" if count == 1 else "s")


def _were(count: int) -> str:
    return "was" if count == 1 else "were"


_KIND_WORDS: Final[Mapping[str, str]] = {
    "exact": "an exact reference (your receiver model, computed exactly)",
    "enclosed": (
        "an enclosed reference (your receiver model, known through rigorous "
        "rational intervals)"
    ),
}

#: The four groups in the order a reader meets them, in plain words.
_GROUP_WORDS: Final[Mapping[str, str]] = {
    str(RestingGroup.NO_USABLE_REFERENCE): "no usable reference",
    str(RestingGroup.REFERENCE_BRACKET_WITHDRAWN): "reference bracket withdrawn",
    str(RestingGroup.REFERENCE_BRACKET_NOT_EVALUATED): (
        "reference bracket not evaluated"
    ),
    str(RestingGroup.LAST_RESORT): "last resort",
}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []


def _text(value: object) -> str | None:
    return None if value is None else str(value)


def _sources(
    payload: Mapping[str, Any],
) -> list[tuple[str | None, Mapping[str, Any], str, Mapping[str, Any] | None, str]]:
    """Return per artefact: station, snap record and reduction, with their pointers.

    The single-device route reads ``snaps.instance`` and ``stages.reduction``;
    a multi-station route reads every ``stages.stations[i]``.
    """
    found: list[
        tuple[str | None, Mapping[str, Any], str, Mapping[str, Any] | None, str]
    ] = []
    stages = payload.get("stages") or {}
    stations = stages.get("stations") if isinstance(stages, Mapping) else None
    if isinstance(stations, list) and stations:
        for index, station in enumerate(stations):
            if not isinstance(station, Mapping):
                continue
            adaptation = station.get("rows_adaptation")
            reduction = station.get("reduction")
            label = station.get("factor")
            found.append(
                (
                    None if label is None else str(label),
                    adaptation if isinstance(adaptation, Mapping) else {},
                    f"/payload/stages/stations/{index}/rows_adaptation",
                    reduction if isinstance(reduction, Mapping) else None,
                    f"/payload/stages/stations/{index}/reduction",
                )
            )
        return found
    snaps = payload.get("snaps")
    instance = snaps.get("instance") if isinstance(snaps, Mapping) else None
    reduction = stages.get("reduction") if isinstance(stages, Mapping) else None
    producer = snaps.get("producer") if isinstance(snaps, Mapping) else None
    if isinstance(reduction, Mapping) and isinstance(producer, Mapping):
        # The single-device route lifts the emission record's blocks into
        # ``snaps.producer``; read them there.
        reduction = {**reduction, "emission_record": producer}
    found.append(
        (
            None,
            instance if isinstance(instance, Mapping) else {},
            "/payload/snaps/instance",
            reduction if isinstance(reduction, Mapping) else None,
            "/payload/stages/reduction",
        )
    )
    return found


def _group_fix(group: str | None, recorded: object) -> str | None:
    """Return the group's fix: the record's, else the foundations wording."""
    if recorded is not None:
        return str(recorded)
    if group is None:
        return None
    try:
        return RestingGroup(group).fix()
    except ValueError:
        return None


def _blocks(
    station: str | None, adaptation: Mapping[str, Any], base: str
) -> list[SnapBlock]:
    """Return one row per block of the instance's snap records.

    Every field is the record's, the run's decision included: a moved block
    names whether it is ``evaluated_off_snap`` and, where it rests on A-SNAP,
    its cause and group (``foundations/req:who-snaps``).
    """
    rows: list[SnapBlock] = []
    for i, snap in enumerate(_list(adaptation.get("measurement_snaps"))):
        if not isinstance(snap, Mapping):
            continue
        for j, block in enumerate(_list(snap.get("blocks"))):
            if not isinstance(block, Mapping):
                continue
            handed = block.get("handed_reference")
            handed = handed if isinstance(handed, Mapping) else None
            off = block.get("evaluated_off_snap") is True
            rests = bool(block.get("rests_on_assumption")) and not off
            group = _text(block.get("group")) if rests else None
            rows.append(
                {
                    "station": station,
                    "setting": _text(snap.get("setting")),
                    "block": str(block.get("block")),
                    "status": str(block.get("status")),
                    "reference_kind": str(block.get("reference_kind")),
                    "handed_kind": (
                        None if handed is None else _text(handed.get("kind"))
                    ),
                    "handed_radius": (
                        None if handed is None else _text(handed.get("largest_radius"))
                    ),
                    "input_radius": (
                        None if handed is None else _text(handed.get("input_radius"))
                    ),
                    "cause": _text(block.get("cause")) if rests else None,
                    "fix": (
                        _text(block.get("receiver_fix") or block.get("fix"))
                        if rests
                        else None
                    ),
                    "group": group,
                    "group_fix": (
                        _group_fix(group, block.get("group_fix")) if rests else None
                    ),
                    "support_not_preserved": bool(block.get("support_not_preserved")),
                    "rests_on_assumption": rests,
                    "evaluated_off_snap": off,
                    "pointer": pointer_join(base, "measurement_snaps", i, "blocks", j),
                }
            )
    return rows


def _emission(
    station: str | None,
    reduction: Mapping[str, Any] | None,
    base: str,
    evaluated: frozenset[int],
    resting: Mapping[int, Mapping[str, Any]],
) -> list[EmissionSnap]:
    """Return the data sectors in which the normaliser moved a class.

    ``evaluated`` names the sectors the run evaluated off their snap, and
    ``resting`` the run's verdict on those that rest on A-SNAP (the
    decision's ``resting_blocks`` of origin ``emission``).
    """
    if reduction is None:
        return []
    record = reduction.get("emission_record")
    if not isinstance(record, Mapping):
        return []
    rows: list[EmissionSnap] = []
    for i, block in enumerate(_list(record.get("blocks"))):
        if not isinstance(block, Mapping):
            continue
        moved = [
            {key: item.get(key) for key in ("class", "step", "support_not_preserved")}
            for item in _list(block.get("classes"))
            if isinstance(item, Mapping) and item.get("status") == "moved"
        ]
        if not moved:
            continue
        index = int(block.get("block_index", i))
        off = index in evaluated or block.get("evaluated_off_snap") is True
        verdict = resting.get(index)
        group = None if off or verdict is None else _text(verdict.get("group"))
        rows.append(
            {
                "station": station,
                "data_sector": index,
                "moved_classes": moved,
                "evaluated_off_snap": off,
                "rests_on_assumption": not off,
                "group": group,
                "group_fix": (
                    None
                    if off or verdict is None
                    else _group_fix(group, verdict.get("group_fix"))
                ),
                "pointer": f"{base}/emission_record/blocks/{i}"
                if station is not None
                else f"/payload/snaps/producer/blocks/{i}",
            }
        )
    return rows


def _where(block: SnapBlock) -> str:
    parts = [block["block"]]
    if block["setting"] not in (None, "off"):
        parts.append(f"setting {block['setting']}")
    if block["station"] is not None:
        parts.append(f"station {block['station']}")
    return ", ".join(parts)


def _largest(values: Sequence[str | None]) -> str | None:
    found = [Fraction(value) for value in values if value is not None]
    if not found or max(found) == 0:
        return None
    return f"{float(max(found)):.1e}"


def _sentences(
    blocks: Sequence[SnapBlock],
    emission: Sequence[EmissionSnap],
    settings: Mapping[str, Any],
    assumption: str | None,
    *,
    direct_route: tuple[str | None, str | None] = (None, None),
) -> list[str]:
    """Return the section's plain-words reading of its rows.

    ``direct_route`` is the run's direct-route status and reason
    (:func:`_decision`).
    """
    out: list[str] = []
    fallback = _fallback_sentence(*direct_route, technical=True)
    if fallback is not None:
        out.append(fallback)
    if blocks:
        out.append(
            f"The engine moved your receiver's measurement onto its numerical "
            f"lattice (a snap) block by block, {_count_blocks(len(blocks))} in all: a "
            "block your model gives exactly on the lattice is kept as it is, and "
            "every other block is moved as little as the rules that keep its "
            "zeros allow."
        )
        on_centres = [block for block in blocks if block["reference_kind"] == "exact"]
        on_data = [block for block in blocks if block["reference_kind"] != "exact"]
        if on_centres:
            out.append(
                f"{_count_blocks(len(on_centres))} {_were(len(on_centres))} "
                "snapped from "
                f"{_KIND_WORDS['exact']}."
            )
        if on_data:
            out.append(
                f"{_count_blocks(len(on_data))} {_were(len(on_data))} snapped from the "
                "receiver's floating-point blocks."
            )
        for kind in ("exact", "enclosed"):
            handed = [block for block in blocks if block["handed_kind"] == kind]
            if not handed:
                continue
            sentence = (
                f"On {_count_blocks(len(handed))} the run handed {_KIND_WORDS[kind]} "
                "beside the snap"
            )
            if kind == "enclosed":
                radius = _largest([block["handed_radius"] for block in handed])
                inputs = _largest([block["input_radius"] for block in handed])
                details = [
                    *([] if radius is None else [f"largest radius {radius}"]),
                    *([] if inputs is None else [f"largest input radius {inputs}"]),
                ]
                if details:
                    sentence += " (" + "; ".join(details) + ")"
            out.append(sentence + ".")
        kept = [block for block in blocks if block["status"] == "kept"]
        if kept:
            out.append(
                f"{_count_blocks(len(kept))} "
                + ("is kept: your model gives it" if len(kept) == 1
                   else "are kept: your model gives them")
                + " exactly on the lattice, so the snap moved nothing there."
            )
        off = [block for block in blocks if block["evaluated_off_snap"]]
        if off:
            one = len(off) == 1
            out.append(
                f"{_count_blocks(len(off), 'moved block')} "
                + ("is evaluated off its snap: on it " if one
                   else "are evaluated off their snap: on them ")
                + "the key length is computed from your receiver model, at the "
                "points the solver found on the moved measurement, so the moving "
                "only steered the search and "
                + ("this block rests" if one else "these blocks rest")
                + " on your receiver model, not on A-SNAP "
                "([[foundations/def:evaluated-off-snap]]; "
                f"{', '.join(_where(block) for block in off)})."
            )
        resting = [block for block in blocks if block["rests_on_assumption"]]
        for group, words in _GROUP_WORDS.items():
            members = [block for block in resting if block["group"] == group]
            if not members:
                continue
            listed = "; ".join(
                f"{_where(block)}: {block['cause']}" for block in members
            )
            fixes = sorted({str(b["group_fix"]) for b in members if b["group_fix"]})
            out.append(
                f"{_count_blocks(len(members))} "
                + ("rests" if len(members) == 1 else "rest")
                + f" on A-SNAP in the group '{words}' "
                f"({listed})"
                + ("." if not fixes else "; what to change: " + " / ".join(fixes) + ".")
            )
        if resting:
            out.append(
                "On a block resting on A-SNAP the key rate is computed as if your "
                "device measured the moved family, which is assumption A-SNAP; "
                "the table gives each block's group, its cause and the detailed "
                "fix."
            )
    if emission and all(row["evaluated_off_snap"] for row in emission):
        out.append(
            "The reduction moved its own emission onto the lattice as well, at "
            + ", ".join(f"data sector {row['data_sector']}" for row in emission)
            + "; the key length does not read that emission: it is evaluated off "
            "its snap, the bound being formed on the emission of your receiver "
            "model itself."
        )
    elif emission:
        moved = ", ".join(
            f"data sector {row['data_sector']}: class(es) "
            + ", ".join(str(item.get("class")) for item in row["moved_classes"])
            + ("" if row["evaluated_off_snap"] else " (rests on A-SNAP)")
            for row in emission
        )
        out.append(
            "The reduction moved its own emission onto the lattice as well, at "
            f"{moved}."
        )
    enclosure = settings.get("reference_enclosure")
    strict = settings.get("strict_snaps")
    out.append(
        "Run settings: enclosed references are "
        + ("used" if enclosure is not False else "not used")
        + ", so the blocks of your model handed beside the snap for the key "
        "length to be computed from are "
        + (
            "only those your model gives exactly"
            if enclosure is False
            else "those known exactly and those known through rigorous intervals"
        )
        + f" (reference_enclosure = {str(enclosure is not False).lower()}); the "
        "strict option is "
        + (
            "on, so a block that would rest on A-SNAP refuses the run"
            if strict
            else "off, so a block that rests on A-SNAP is disclosed, not refused"
        )
        + f" (strict_snaps = {str(bool(strict)).lower()})."
    )
    if assumption is not None:
        out.append(
            "The assumption manifest lists A-SNAP because some block rests on it."
        )
    return out


def _warnings(
    blocks: Sequence[SnapBlock],
    emission: Sequence[EmissionSnap],
    rests: bool,
    assumption: str | None,
) -> list[str]:
    out = [
        f"{_where(block)} was moved by the last resort and is flagged "
        "support_not_preserved: the moved measurement may treat as possible an "
        "outcome your model treats as impossible."
        for block in blocks
        if block["support_not_preserved"]
    ]
    out += [
        f"data sector {row['data_sector']}, class {item.get('class')}, of the "
        "reduction's emission was moved by the last resort and is flagged "
        "support_not_preserved."
        for row in emission
        for item in row["moved_classes"]
        if item.get("support_not_preserved")
    ]
    if rests:
        out.append(
            "The key rate rests on assumption A-SNAP: some moved measurement "
            "block or emission sector is not evaluated off its snap (see "
            "Measurement snaps)."
        )
        if assumption is None:
            out.append(
                "Discrepancy: the record names blocks resting on A-SNAP, but the "
                "assumption manifest does not list A-SNAP; read the manifest of "
                "this run as incomplete."
            )
    return out


# --------------------------------------------------------------------------
# The reader's layer (report 0.10.0)
# --------------------------------------------------------------------------

#: WHY A BLOCK RESTS ON A-SNAP, one clause per group, keyed by the group's
#: name in the record. A group this table does not know (a later record's)
#: is read in its own words, so a new group never breaks the section.
GROUP_WHY: Final[Mapping[str, str]] = {
    str(RestingGroup.NO_USABLE_REFERENCE): (
        "had no reference of your measurement that this run could hand beside "
        "the rounding (none declared, one that failed its checks, an enclosure "
        "the run's settings exclude, or, for the reduction's own rounding, no "
        "claim that carries its exact construction past it), so the key length "
        "could not be computed from your model there"
    ),
    str(RestingGroup.REFERENCE_BRACKET_WITHDRAWN): (
        "had your model (or the reduction's exact construction) carried beside "
        "the rounding, but the key length was computed from the rounded "
        "measurement: the bound formed on your model gave no usable value at "
        "the points the solver found, or its rigorous re-evaluation certified "
        "none of them, or the engine found two enclosures of one of its blocks "
        "inconsistent (a defect of the engine)"
    ),
    str(RestingGroup.REFERENCE_BRACKET_NOT_EVALUATED): (
        "had your model (or the reduction's exact construction) carried beside "
        "the rounding, but no bound was formed on it, so the key length was "
        "computed from the rounded measurement"
    ),
    str(RestingGroup.LAST_RESORT): (
        "could be rounded only by the last resort, which may treat an outcome "
        "your model rules out as possible"
    ),
}

def _group_words(group: str) -> str:
    return _GROUP_WORDS.get(group, group.replace("_", " "))


def _station_names(record: Mapping[str, Any]) -> dict[str | None, str]:
    """Return each station's label read as "<party>'s station"."""
    stations = resolve_pointer(record, "/payload/stages/stations", None)
    names: dict[str | None, str] = {}
    for station in stations if isinstance(stations, list) else ():
        if isinstance(station, Mapping) and station.get("factor") is not None:
            party = station.get("party")
            names[str(station["factor"])] = (
                f"{party_name(party)}'s station"
                if party is not None else str(station["factor"])
            )
    return names


def _photons(block: SnapBlock) -> str:
    label = block["block"]
    found = label.removeprefix("m=")
    if found.isdigit():
        count = int(found)
        words = (
            "0 photons (vacuum)" if count == 0
            else "1 photon" if count == 1 else f"{count} photons"
        )
    else:
        words = label
    if block["setting"] not in (None, "off"):
        words += f", setting {block['setting']}"
    return words


def _status(block: SnapBlock) -> str:
    if block["status"] == "kept":
        return "kept exactly: the rounding moved nothing"
    if block["evaluated_off_snap"]:
        return (
            "rounded, and evaluated off its snap: the key length is computed "
            "from your model here, so the rounding only steered the search"
        )
    if block["rests_on_assumption"]:
        return "rounded" + (
            "" if block["group"] is None else f" ({_group_words(block['group'])})"
        )
    return block["status"].replace("_", " ")


def snap_rows(
    blocks: Sequence[SnapBlock], names: Mapping[str | None, str]
) -> list[SnapRow]:
    """Return one readable row per snap block."""
    return [
        {
            "station": None if block["station"] is None
            else names.get(block["station"], block["station"]),
            "photons": _photons(block),
            "status": _status(block),
            "rests_on_assumption": block["rests_on_assumption"],
            "evaluated_off_snap": block["evaluated_off_snap"],
            "group": None if block["group"] is None or not block["rests_on_assumption"]
            else _group_words(block["group"]),
            "fix": block["group_fix"] if block["rests_on_assumption"] else None,
            "pointer": block["pointer"],
        }
        for block in blocks
    ]


def resting_sectors(emission: Sequence[EmissionSnap]) -> list[int]:
    """Return the data sectors of the reduction's emission that rest on A-SNAP.

    A sector rests where it holds a moved class the run did not evaluate off
    its snap (``reductions/req:emission-record``).
    """
    return [row["data_sector"] for row in emission if row["rests_on_assumption"]]


#: Why the bound on the receiver model was not used, per reason the record
#: gives, in plain words (``meat-core/frank-wolfe/req:bracket-on-reference``
#: (iv); ``meat-core/req:companion-admission`` (i)). A reason this table does
#: not know is named as the record spells it.
_FALLBACK_WHY: Final[Mapping[str, str]] = {
    "reference_bracket_withdrawn": (
        "the engine formed the bound on it at the points the solver found, but "
        "no point gave a usable bound there"
    ),
    "factor_enclosure_inconsistent": (
        "the engine formed the bound on it, but its rigorous re-evaluation found "
        "the two enclosures it holds of one block inconsistent, which is a "
        "defect of the engine to report and not of your model, so the bound on "
        "your model was withdrawn"
    ),
    "dropped_set_not_covered": (
        "the run evaluates a dropped program, and no claim states that bound "
        "on your receiver model"
    ),
    "companion_joint_sectors_differ": (
        "its joint sectors differ from those of the rounded measurement"
    ),
    "companion_measured_family_shape": (
        "its measurement does not have the shape of the rounded one, so it was "
        "not admitted"
    ),
    "companion_constraint_list": (
        "its constraint list does not match the rounded one, so it was not "
        "admitted"
    ),
    "companion_entry_not_hermitian_binary64": (
        "one of its constraint entries is not a Hermitian binary64 operator, so "
        "it was not admitted"
    ),
}


#: The direct route's reason as :func:`_route_reading` gives it where the
#: bound on the companion counted and the key length is formed in the
#: fallback of ``meat-core/frank-wolfe/req:certified-evaluation`` (i).
COMPANION_NOT_CERTIFIED: Final[str] = "companion_not_certified"


def _route_reading(
    payload: Mapping[str, Any], status: str | None, reason: str | None
) -> tuple[str | None, str | None]:
    """Return the status and reason the fallback sentence reads (record 0.35.0).

    A withdrawn bracket whose record names a cause (``factor_enclosure_
    inconsistent``, ``req:bracket-on-reference`` (iv)) is read by its cause;
    a counted bracket whose decision is the certified evaluation's fallback
    reads as ``counted`` with the reason :data:`COMPANION_NOT_CERTIFIED`.
    """
    snaps = payload.get("snaps")
    decision = snaps.get("reference_companion") if isinstance(snaps, Mapping) else None
    if status == "counted" and isinstance(decision, Mapping) and decision.get(
        "fallback"
    ):
        return status, COMPANION_NOT_CERTIFIED
    stages = payload.get("stages") or {}
    bracket = (stages.get("key_rate") or {}).get("reference_bracket")
    cause = bracket.get("cause") if isinstance(bracket, Mapping) else None
    if status == "withdrawn" and cause is not None:
        return status, str(cause)
    return status, reason


def _fallback_sentence(
    status: str | None, reason: str | None, *, technical: bool
) -> str | None:
    """Return the sentence of a run whose bound on the receiver model was not used.

    ``None`` unless the direct route's status is ``withdrawn`` or
    ``not_evaluated``, or the key length is formed in the certified
    evaluation's fallback (``counted`` with :data:`COMPANION_NOT_CERTIFIED`):
    a user whose receiver model was carried beside the snap learns that the
    key length was not computed from it, and why. ``technical`` adds the
    record's status and reason strings.
    """
    if status == "counted" and reason == COMPANION_NOT_CERTIFIED:
        sentence = (
            "Your receiver model was carried beside the rounded measurement and "
            "the first-order bound was formed on it, but its rigorous "
            "re-evaluation certified none of the solver's final points, so the "
            "certified key length is computed from the rounded measurement "
            "instead and the blocks your model carried rest on A-SNAP; the "
            "first-order bound on your model is recorded beside it, and no number "
            "is formed from the two together "
            "([[meat-core/frank-wolfe/req:certified-evaluation]])"
        )
        if technical:
            sentence += (
                " (direct route counted, the certified number formed on the "
                "searched declaration in the fallback, cause "
                f"{COMPANION_NOT_CERTIFIED})"
            )
        return sentence + "."
    if status not in ("withdrawn", "not_evaluated"):
        return None
    why = (
        "the record gives no reason"
        if reason is None
        else _FALLBACK_WHY.get(reason, f"the record gives the reason {reason}")
    )
    sentence = (
        "Your receiver model was carried beside the rounded measurement, but the "
        f"key length is not computed from it: {why}. The key length is computed "
        "from the rounded measurement instead, and its moved blocks rest on "
        "A-SNAP"
    )
    if technical:
        formed = (
            "was formed and withdrawn" if status == "withdrawn" else "was not formed"
        )
        sentence += (
            f" (direct route {status}: the bound on the reference companion "
            f"{formed}" + ("" if reason is None else f", reason {reason}") + ")"
        )
    return sentence + "."


def plain_sentences(
    blocks: Sequence[SnapBlock],
    displacement: Any,
    emission: Sequence[EmissionSnap] = (),
    *,
    direct_route: tuple[str | None, str | None] = (None, None),
    first_order: bool = False,
) -> list[str]:
    """Return the three to five sentences a reader meets first.

    Built from the rows, keyed by group (:data:`GROUP_WHY`), never by run:
    what a snap is, what rests on A-SNAP (your stations' blocks, clause (i),
    and the reduction's emission, clause (ii)), why (one clause per group),
    and the fix the record names. The displacement is named for what it is and
    said not to bound the key length (``meat-core/rem:declared-measurement``).
    ``direct_route`` is the run's direct-route status and reason: on a
    fallback (``withdrawn``, ``not_evaluated``) one sentence says that the
    bound on the receiver model was not used and why
    (``meat-core/frank-wolfe/req:bracket-on-reference`` (iv)). On a
    ``first_order`` run the blocks evaluated off their snap add that the bound
    is evaluated at the centres of the model's rigorous intervals
    (``meat-core/frank-wolfe/rem:fo-arithmetic``).
    """
    out = [
        "Before solving, the engine rounds each station's measurement operators "
        "onto a fine numerical grid (a snap), so that its exact checks can run."
    ]
    if (
        isinstance(displacement, int | float) and not isinstance(displacement, bool)
        and displacement > 0
    ):
        out[0] += (
            f" The largest entry moved, over your stations' rounding and the "
            f"reduction's together, is {float(displacement):.1e}. How far an "
            "entry moves does not bound how far the key length can move "
            "([[meat-core/rem:declared-measurement]])."
        )
    moved = [block for block in blocks if block["status"] != "kept"]
    kept = len(blocks) - len(moved)
    resting = [block for block in blocks if block["rests_on_assumption"]]
    off = [block for block in blocks if block["evaluated_off_snap"]]
    sectors = resting_sectors(emission)
    fallback = _fallback_sentence(*direct_route, technical=False)
    if fallback is not None:
        out.append(fallback)
    if kept:
        out.append(
            f"{kept} of the {len(blocks)} blocks of your stations are kept: your "
            "model gives them exactly on the grid, so the rounding moved nothing "
            "there."
        )
    if off:
        share = (
            f"all {len(moved)}" if len(off) == len(moved)
            else f"{len(off)} of the {len(moved)}"
        )
        out.append(
            f"On {share} moved blocks of your stations the key length is computed "
            "from your receiver model, at the points the solver found on the "
            "rounded measurement: those blocks are evaluated off their snap and "
            "rest on your receiver model, not on [[A-SNAP]] "
            "([[foundations/def:evaluated-off-snap]])"
            + ("; on this first-order run, where your model is known only "
               "through rigorous intervals, the bound is evaluated at their "
               "centres ([[meat-core/frank-wolfe/rem:fo-arithmetic]])."
               if first_order else ".")
        )
    if resting:
        share = (
            f"all {len(moved)}" if len(resting) == len(moved)
            else f"{len(resting)} of the {len(moved)}"
        )
        out.append(
            f"On {share} moved blocks of your stations the analysis does not "
            "account for the rounding, so there the key length holds for the "
            "rounded measurement, and you vouch that your device measures it "
            "([[A-SNAP]])."
        )
        groups = list(dict.fromkeys(
            str(block["group"]) for block in resting if block["group"] is not None
        ))
        clauses = []
        for group in groups:
            count = sum(1 for block in resting if block["group"] == group)
            why = GROUP_WHY.get(
                group,
                ("rests" if count == 1 else "rest")
                + f" on A-SNAP ({_group_words(group)})",
            )
            clauses.append(f"{_count_blocks(count)} {why}")
        if clauses:
            out.append("Why: " + "; ".join(clauses) + ".")
    if sectors:
        out.append(
            "The reduction's own rounding of what it emits rests on [[A-SNAP]] at "
            f"data sector(s) {', '.join(str(sector) for sector in sectors)}: there "
            "you vouch that what the run concludes from the emission holds of the "
            "rounded emission."
        )
    if resting:
        fixes = list(dict.fromkeys(
            str(block["group_fix"]) for block in resting if block["group_fix"]
        ))
        if fixes:
            out.append("What to change: " + ". Or: ".join(
                fix[:1].upper() + fix[1:] for fix in fixes
            ) + ".")
    elif blocks and not sectors:
        # Said so that a reader knows this section asks nothing of them (the
        # stage-9 experimentalist reader could not tell whether to skip it).
        out.append(
            "The rounding adds no premise: the key length does not rest on A-SNAP, "
            "so nothing in this section asks anything of you."
        )
    return out


def _first_order(payload: Mapping[str, Any]) -> bool:
    """Whether the run's key length is reported at the first-order tier."""
    stages = payload.get("stages")
    key_rate = stages.get("key_rate") if isinstance(stages, Mapping) else None
    return isinstance(key_rate, Mapping) and key_rate.get("reported_tier") == (
        "first-order"
    )


def measurement_snaps(
    record: Mapping[str, Any], engaged: Sequence[str]
) -> MeasurementSnaps | None:
    """Return the report's measurement-snap section, or ``None`` where none was made.

    ``engaged`` is the short ids of the assumption manifest's entries. A record
    whose shape is not one of :data:`SNAP_RECORD_VERSIONS` gets ``None``.
    """
    if str(record.get("schema_version")) not in SNAP_RECORD_VERSIONS:
        return None
    payload = record["payload"]
    blocks: list[SnapBlock] = []
    emission: list[EmissionSnap] = []
    status, reason, sectors, resting = _decision(payload)
    reading = _route_reading(payload, status, reason)
    for station, adaptation, base, reduction, reduction_base in _sources(payload):
        blocks += _blocks(station, adaptation, base)
        emission += _emission(
            station,
            reduction,
            reduction_base,
            sectors.get(station, frozenset()),
            resting.get(station, {}),
        )
    if not blocks and not emission:
        return None
    parameters = resolve_pointer(record, "/payload/config/parameters", {})
    settings = {
        name: parameters.get(name) if isinstance(parameters, Mapping) else None
        for name in ("reference_enclosure", "strict_snaps")
    }
    assumption = SNAP_ASSUMPTION if SNAP_ASSUMPTION in engaged else None
    rests = any(block["rests_on_assumption"] for block in blocks) or bool(
        resting_sectors(emission)
    )
    return {
        "settings": settings,
        "sentences": _sentences(
            blocks, emission, settings, assumption, direct_route=reading
        ),
        "warnings": _warnings(blocks, emission, rests, assumption),
        "blocks": blocks,
        "emission": emission,
        "rests_on_a_snap": rests,
        "assumption": assumption,
        "plain": plain_sentences(
            blocks,
            resolve_pointer(record, "/payload/snaps/snap_max_displacement", None),
            emission,
            direct_route=reading,
            first_order=_first_order(payload),
        ),
        "rows": snap_rows(blocks, _station_names(record)),
        "direct_route": status,
        "evaluated_off_snap": sum(1 for block in blocks if block["evaluated_off_snap"]),
    }


def _decision(
    payload: Mapping[str, Any],
) -> tuple[
    str | None,
    str | None,
    dict[str | None, frozenset[int]],
    dict[str | None, dict[int, Mapping[str, Any]]],
]:
    """Return the run's direct-route decision as the section reads it.

    The status and its reason; per station (its factor label on a
    multi-station route, ``None`` on the single-device one) the emission's data
    sectors evaluated off their snap, and the run's verdict on each sector
    that rests on A-SNAP.
    """
    snaps = payload.get("snaps")
    decision = snaps.get("reference_companion") if isinstance(snaps, Mapping) else None
    if not isinstance(decision, Mapping):
        return None, None, {}, {}

    def key(item: Mapping[str, Any]) -> str | None:
        return None if item.get("station") is None else _text(item.get("factor"))

    sectors = {
        key(item): frozenset(int(sector) for sector in _list(item.get("data_sectors")))
        for item in _list(decision.get("emission_evaluated_off_snap"))
        if isinstance(item, Mapping)
    }
    resting: dict[str | None, dict[int, Mapping[str, Any]]] = {}
    for item in _list(decision.get("resting_blocks")):
        if not isinstance(item, Mapping) or item.get("origin") != "emission":
            continue
        name = str(item.get("block"))
        index = name.removeprefix("data sector ").strip()
        if index.isdigit():
            resting.setdefault(key(item), {})[int(index)] = item
    return (
        _text(decision.get("status")),
        _text(decision.get("reason")),
        sectors,
        resting,
    )
