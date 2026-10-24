"""The run tier's plain-words sentences of the key-rate report, in one place.

WHY THIS EXISTS. The report's first page must be readable by an
experimentalist and mappable to tests by a certification lab. Its summary,
the "About" and "At stake" lines of every assumption
and the one-line reading of every solver diagnostic are run-tier prose; that
prose has exactly one home, this module, so that a reviewer
reads it in one place and a staleness guard can pin
each paraphrase to the claims it leans on (:data:`PARAPHRASES`).

WHAT THE SENTENCES MAY SAY. Each one reads record values, or restates what a
named claim says in fewer words; none adds a guarantee. A sentence that leans
on a claim names it as a ``[[claim id]]`` or ``[[A-...]]`` token, which the
renderer turns into a contract link. Where a claim carries a ``user_statement``
(the closure table's plain reading) the summary quotes it rather than writing
its own; the sentences here only connect record values to it.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from fractions import Fraction
from typing import Any, Final, NamedTuple

from certiqs_key.runs.errors import RunRefusalReason
from certiqs_key.runs.report.inputs import (
    analysed_words,
    exact_with_decimal,
    same_number,
)
from certiqs_key.runs.report.model import (
    AssumptionEntry,
    ClaimRef,
    ConsequenceCounts,
    Deductions,
    DiagnosticRow,
    Emission,
    GlanceItem,
    GuaranteeTerm,
    InputRow,
    MeasurementSnaps,
    ResultSection,
    SetupSection,
    SolverAttempt,
    SummaryItem,
)
from certiqs_key.runs.roles import (
    PARTY_NAMES,
    PublicChoice,
    Roles,
    StationRoles,
    not_on_this_run,
    party_name,
    row_station,
)
from certiqs_key.runs.stages import SliceStage

__all__ = [
    "ABOUT",
    "AT_A_GLANCE_TITLE",
    "AT_STAKE",
    "COMPLETENESS_CLAIM",
    "COMPOSED_CLAIM",
    "CONSEQUENCE_WORDS",
    "COSTS_LEAD",
    "DEVICE_CATEGORIES",
    "DOCUMENT_HINTS",
    "ENGINE_CATEGORIES",
    "FIRSTORDER_CLAIM",
    "FO_ARITHMETIC_CLAIM",
    "IDEALISED_HEADLINE",
    "IDEALISED_HONEST_MODEL",
    "KEYLENGTH_BOUND_CLAIM",
    "KEYLENGTH_CLAIM",
    "LEVERS_LEAD",
    "LEVERS_SNAP",
    "PARAPHRASES",
    "PER_EXECUTION_CLAIM",
    "RETIRED_LABORATORY_KEYS",
    "ROLES_ABSENT_LEAD",
    "STATUS_LEGEND",
    "VOUCH_GROUPS",
    "StatementStatus",
    "ZeroKey",
    "about",
    "at_a_glance",
    "at_stake",
    "binding_words",
    "cap_probability_text",
    "cap_text",
    "consequence",
    "consequence_rows",
    "consequence_words",
    "costs",
    "diagnostic_rows",
    "draft_sentence",
    "epsilon_text",
    "expected_basis",
    "first_sentence",
    "guarantee_terms",
    "idealisation_bears_on_security",
    "idealised",
    "idealised_headline",
    "levers",
    "not_counted",
    "partition_words",
    "pass_cap_sentence",
    "pass_exponent_text",
    "places",
    "refused_numbers",
    "result_sentence",
    "role_notes",
    "roles_absent",
    "roles_box",
    "scope",
    "setup_brief",
    "setup_glance",
    "snap_warning",
    "solve_stop",
    "solver_attempts",
    "statement_status",
    "station_label",
    "statistics_not_run",
    "statistics_refusal",
    "statistics_short",
    "tier_note",
    "vouch_group",
    "zero_key",
    "zero_key_sentence",
]

#: The claims the summary quotes or the appendix reads.
COMPOSED_CLAIM: Final[str] = "meat-core/cor:composed-security"
PER_EXECUTION_CLAIM: Final[str] = "meat-core/rem:repeated-executions"
COMPLETENESS_CLAIM: Final[str] = "meat-core/rem:completeness-scope"
KEYLENGTH_CLAIM: Final[str] = "meat-core/thm:keylength"
#: The constant one bit of the key length and why it is one, not two.
PLUS_ONE_CLAIM: Final[str] = "meat-core/rem:plus2"
FIRSTORDER_CLAIM: Final[str] = "meat-core/frank-wolfe/thm:firstorder"
KEYLENGTH_BOUND_CLAIM: Final[str] = "meat-core/cor:keylength-bound"
FO_ARITHMETIC_CLAIM: Final[str] = "meat-core/frank-wolfe/rem:fo-arithmetic"
#: The one-bit penalty the record deducts for a merely two-universal hash.
HASH_PENALTY_CLAIM: Final[str] = "meat-core/req:hash-penalty"
#: The certified tier's key length and what it still rests on.
CERTIFIED_CLAIM: Final[str] = "meat-core/frank-wolfe/cor:certified-keylength"
CERTIFIED_SCOPE_CLAIM: Final[str] = "meat-core/frank-wolfe/rem:certified-scope"
#: Where a certified number is formed, its fallback and its record.
CERTIFIED_EVALUATION_CLAIM: Final[str] = (
    "meat-core/frank-wolfe/req:certified-evaluation"
)
#: The short id the record's ``certified.premises`` names.
SNAP_PREMISE: Final[str] = "A-SNAP"
#: The claim that owns A-SNAP, which the at-a-glance box names where engaged.
SNAP_CLAIM: Final[str] = "foundations/ass:snapped-measurement"
#: The definition the at-a-glance box names where blocks were evaluated off
#: their snap, and the bound on the reference companion they rest on instead.
OFF_SNAP_CLAIM: Final[str] = "foundations/def:evaluated-off-snap"
REFERENCE_BOUND_CLAIM: Final[str] = "meat-core/frank-wolfe/cor:fo-reference"
#: The claim the run tier's plausibility refusal reads, and its code
#: (``certiqs_key.runs.errors.RunRefusalReason``; ``runs/plausibility.py``).
VALUE_RANGE_CLAIM: Final[str] = "meat-core/prop:value-range"
CONTRADICTION_REFUSAL: Final[str] = str(
    RunRefusalReason.ENTROPY_BOUND_ABOVE_KEY_CEILING
)
#: The check of the acceptance set against the feasible statistics, the
#: proposition its bound reads, the premise it checks, and the core's refusal
#: string (report 0.26.0).
UNREACHABLE_CLAIM: Final[str] = "meat-core/req:unreachable-acceptance-set"
MINIMAL_DIVERGENCE_CLAIM: Final[str] = "meat-core/prop:minimal-divergence"
MODEL_PASS_CLAIM: Final[str] = "meat-core/prop:model-pass-bound"
REACH_PREMISE: Final[str] = "A-REACH"
UNREACHABLE_REFUSAL: Final[str] = "acceptance_set_unreachable"

#: The categories a user vouches for about the devices and the setup, and
#: those about artefacts and the engine.
DEVICE_CATEGORIES: Final[tuple[str, ...]] = (
    "laboratory", "source", "receiver", "channel-and-adversary", "protocol-structure",
    "local-randomness", "post-processing", "honest-model",
)
ENGINE_CATEGORIES: Final[tuple[str, ...]] = ("supplied-artefact", "numerical-trust")

#: "About": the object of an assumption, by category; a
#: receiver premise names its station instead where its emitter does, and a
#: laboratory premise the parties its rows name (:func:`about`).
ABOUT: Final[Mapping[str, str]] = {
    "laboratory": "Your laboratories",
    "source": "Your source",
    "receiver": "Your receivers",
    "channel-and-adversary": "The classical channel and the attacker",
    "protocol-structure": "The protocol's structure",
    "local-randomness": "Your random number generators",
    "post-processing": "Your post-processing",
    # Not "(..., not security)": A-REACH, in this category, affects secrecy
    # (statistics/ass:reach), and its row says "If it fails: security".
    "honest-model": "The honest model (what an honest run is expected to show)",
    "supplied-artefact": "An artefact supplied to the engine",
    "numerical-trust": "The engine's numerics",
}

#: THE PER-PARTY LABORATORY PREMISES OF AN OLDER RECORD (before record 0.30.0,
#: which merged them into A-LAB), by machine key: the
#: formal party whose laboratory each is about, so that an older record's
#: premise reads "Bob's laboratory" and not "Your receivers".
RETIRED_LABORATORY_KEYS: Final[Mapping[str, str]] = {
    "alice_laboratory_sealed": "A",
    "bob_laboratory_sealed": "B",
}

#: "At stake", by the property an assumption ``affects``.
AT_STAKE: Final[Mapping[str, str]] = {
    "secrecy": "secrecy (the key may leak to the attacker)",
    "correctness": "correctness (the two keys may differ)",
    "completeness": "completeness (an honest run may abort more often)",
}

#: What each claim status means, one line each, lowest
#: first as spec/claim-format.md section 6 (check 9) ranks them. Verified is
#: an AI model's review, not a person's.
STATUS_LEGEND: Final[tuple[tuple[str, str], ...]] = (
    ("superseded", "replaced by a newer claim; it no longer counts"),
    ("draft", "not yet through an independent review, or sent back by one, or "
              "substantively amended since"),
    ("verified", "passed an adversarial review by an AI model that saw only the "
                 "written artefacts (the claim files and the references they "
                 "cite), not the author's reasoning; not yet accepted by a person"),
    ("accepted", "passed that review and was then accepted by the project's "
                 "human owner"),
    ("implemented", "accepted, and the code that implements it is accepted"),
    ("effective status",
     "the lowest status over the claim and everything it rests on"),
)

#: A status in words, for the guarantee's review-status line (item 6 of the
#: report v2 last round).
_STATUS_WORDS: Final[Mapping[str, str]] = {
    "superseded": "superseded",
    "draft": "a draft: not yet through an independent review, sent back by one, "
             "or substantively amended since",
    "verified": "reviewed adversarially by an AI model, not yet accepted by a "
                "person",
    # Who reviewed, as the legend says it ("reviewed and accepted" read as
    # stronger than an AI model's review and one owner's acceptance).
    "accepted": "reviewed adversarially by an AI model and accepted by the "
                "project's human owner",
    "implemented": "reviewed adversarially by an AI model and accepted by the "
                   "project's human owner, its code too",
}

#: A claim's own status in words, for one line of the review-status list:
#: what was reviewed and accepted, the statement or the statement and its code.
_CLAIM_STATUS_WORDS: Final[Mapping[str, str]] = {
    **_STATUS_WORDS,
    "accepted": "statement reviewed adversarially by an AI model and accepted by "
                "the project's human owner",
    "implemented": "statement and code reviewed adversarially by an AI model and "
                   "accepted by the project's human owner",
}

#: THE CLAIMS EACH SENTENCE PARAPHRASES, for the staleness guard: when one
#: of these claims' statements changes, re-read the sentence.
PARAPHRASES: Final[Mapping[str, tuple[str, ...]]] = {
    "result_sentence": (
        COMPOSED_CLAIM, KEYLENGTH_CLAIM, FIRSTORDER_CLAIM, FO_ARITHMETIC_CLAIM
    ),
    "levers.lambda_ec": (KEYLENGTH_CLAIM,),
    "levers.alpha": (KEYLENGTH_CLAIM,),
    "levers.step_limit": (FIRSTORDER_CLAIM,),
    "levers.rounds": (KEYLENGTH_CLAIM,),
    "zero_key_sentence": (KEYLENGTH_CLAIM, KEYLENGTH_BOUND_CLAIM, FIRSTORDER_CLAIM),
    "document_hints": (
        "protocol-compiler/def:banda",
        "protocol-compiler/req:band-a-ideal-receiver",
        "protocol-compiler/req:weight-list",
        "protocol-compiler/req:physical-family-decision",
    ),
    "diagnostic.h_low": (FIRSTORDER_CLAIM,),
    "diagnostic.first_order_minus_estimate": (FIRSTORDER_CLAIM,),
    "diagnostic.h_lb": (FIRSTORDER_CLAIM, KEYLENGTH_BOUND_CLAIM),
    "diagnostic.certified": (
        CERTIFIED_CLAIM,
        CERTIFIED_SCOPE_CLAIM,
        FIRSTORDER_CLAIM,
        "foundations/req:tiers",
    ),
    "diagnostic.frank_wolfe_gap": (FIRSTORDER_CLAIM,),
    "diagnostic.solver_status": (FIRSTORDER_CLAIM, KEYLENGTH_BOUND_CLAIM),
    "diagnostic.withdrawals": (FIRSTORDER_CLAIM,),
    "guarantee_terms": (COMPOSED_CLAIM,),
    # The report sweep's run-tier sentences (report 0.33.0 and 0.34.0).
    "large_gap_sentence": (FIRSTORDER_CLAIM, FO_ARITHMETIC_CLAIM),
    "role_notes.seed": ("meat-core/ass:seed", "meat-core/def:postprocessing-model"),
    "_page.COMPOSABLE_AUTH": ("meat-core/ass:auth",),
    "_page.TIER_CLAUSE": (FO_ARITHMETIC_CLAIM, CERTIFIED_CLAIM),
    "_render.EXACT_LEAD": ("receiver/ass:exact",),
    "setup.announcements_order": ("transmitter/ass:seq",),
    "roles_box.untrusted_source": ("meat-core/ass:lab",),
    "at_a_glance": (
        COMPOSED_CLAIM,
        FO_ARITHMETIC_CLAIM,
        SNAP_CLAIM,
        OFF_SNAP_CLAIM,
        REFERENCE_BOUND_CLAIM,
    ),
    "at_a_glance.certified": (CERTIFIED_CLAIM, CERTIFIED_SCOPE_CLAIM),
    "tier_note": (FO_ARITHMETIC_CLAIM, CERTIFIED_CLAIM, CERTIFIED_SCOPE_CLAIM),
    "at_a_glance.contradiction": (VALUE_RANGE_CLAIM,),
    "at_a_glance.unreachable": (
        UNREACHABLE_CLAIM, MINIMAL_DIVERGENCE_CLAIM, MODEL_PASS_CLAIM,
    ),
    "statistics_sentence": (
        UNREACHABLE_CLAIM, MINIMAL_DIVERGENCE_CLAIM, "statistics/ass:reach",
        MODEL_PASS_CLAIM,
    ),
    "result_sentence.certified": (CERTIFIED_CLAIM, CERTIFIED_SCOPE_CLAIM),
    "costs": (KEYLENGTH_CLAIM, HASH_PENALTY_CLAIM, PLUS_ONE_CLAIM),
    "certified_basis": (
        CERTIFIED_EVALUATION_CLAIM, CERTIFIED_SCOPE_CLAIM, SNAP_CLAIM,
        "meat-core/frank-wolfe/req:bracket-on-reference",
    ),
    "binding_words.tau": ("receiver/def:modes",),
    "binding_words.invoked_at": ("receiver/ass:eig",),
    "not_counted.first_order": (FIRSTORDER_CLAIM, FO_ARITHMETIC_CLAIM),
    "setup_brief.untrusted": (
        "meat-core/thm:accumulated-entropy", "meat-core/ass:lab", "receiver/ass:modes",
    ),
    "role_notes.key_register": ("meat-core/ass:keyreg",),
    "role_notes.laboratory": ("meat-core/ass:lab",),
    "roles_box": ("meat-core/def:declaration", "protocol-compiler/ass:coin"),
    "idealised": (
        "receiver/ass:exact", "protocol-compiler/ass:ideal", "transmitter/ass:ens",
        "transmitter/decoy/ass:wcp", "statistics/ass:hon-env",
        "meat-core/rem:completeness-scope",
    ),
    "consequence_words": ("statistics/ass:hon-env",),
    "setup.acceptance_zero": (
        "statistics/binomial-box/def:construction",
        "meat-core/def:postprocessing-model",
        "meat-core/ass:conform",
    ),
    "not_counted.exactness": (
        "receiver/ass:exact", "transmitter/ass:ens", "transmitter/decoy/ass:wcp",
    ),
    "setup.round_block": (
        "protocol-compiler/ass:spec", "receiver/ass:exact",
        "protocol-compiler/ass:ideal", "receiver/ass:modes", "receiver/ass:port",
        "receiver/ass:thresh", "protocol-compiler/ass:rhom", "receiver/ass:round",
        "transmitter/ass:seq", "meat-core/ass:lab", "meat-core/ass:fixed",
        "statistics/ass:alphabet", "meat-core/ass:conform",
    ),
}


def _number(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:.3g}"
    return str(value)


# --------------------------------------------------------------------------
# Assumptions: About and At stake
# --------------------------------------------------------------------------


def _station_words(stations: Sequence[StationRoles]) -> str:
    """Return stations by their party: "Alice's station", "Station 2"."""
    if any(station.index is not None and station.party not in PARTY_NAMES
           for station in stations):
        indices = [str(station.index) for station in stations]
        noun = "Station" if len(indices) == 1 else "Stations"
        return f"{noun} {', '.join(indices)}"
    owners = [f"{party_name(station.party)}'s" for station in stations]
    if len(owners) == 1:
        return f"{owners[0]} station"
    return f"{', '.join(owners[:-1])} and {owners[-1]} stations"


def _located(roles: Roles, emission: Emission) -> StationRoles | None:
    """Return the station an emitting row is at; an unknown index has no party."""
    station = row_station(roles, emission)
    if station is None and emission["station"] is not None:
        return StationRoles(int(emission["station"]), None, "", (), False, None)
    return station


def _laboratory(party: str, roles: Roles) -> str:
    """Return "Alice's laboratory (station alice_station)": a party, its stations.

    A station is named as the setup's Station field names it, by its factor
    label (else its index); the one receiver of a single-receiver run is
    "the receiver".
    """
    stations = roles.stations_of(party)
    indices = [station.factor or str(station.index) for station in stations
               if station.index is not None]
    where = (
        "" if not stations
        else " (the receiver)" if not indices
        else f" (station {indices[0]})" if len(indices) == 1
        else f" (stations {', '.join(indices[:-1])} and {indices[-1]})"
    )
    return f"{party_name(party)}'s laboratory{where}"


def about(
    entry: AssumptionEntry, roles: Roles, category: str | None = None
) -> str:
    """Return the object an assumption is about, in words.

    THE ROW'S SCOPE FIRST, read off its emitting rows through the
    role vector (:mod:`certiqs_key.runs.roles`):

    * a premise emitted once per party (A-LAB, ``meat-core/ass:lab``; record
      0.30.0; or an older record's per-party laboratory premise,
      :data:`RETIRED_LABORATORY_KEYS`) names each party's laboratory and that
      party's stations, "Alice's laboratory (station alice_station)", never "Your
      receivers";
    * a premise every row of which is at a station (:func:`row_station`) is
      named by its stations, "Alice's station", whatever its category;
    * a premise emitted at stations and also for the run names its stations
      only in the categories that did so before (receiver, supplied artefact,
      none), the other run-level object being its category's;
    * a receiver premise of a run with one station names that station.

    Otherwise the category's object (:data:`ABOUT`); ``category`` overrides
    the entry's own where the report groups it elsewhere (an older record's
    source premise on an untrusted run, ``build.py``).
    """
    category = entry["category"] if category is None else category
    parties, stations = scope(entry, roles, category)
    if parties:
        return " and ".join(_laboratory(party, roles) for party in parties)
    if stations:
        return _station_words(stations)
    if category is None:
        return "Uncategorised"
    words = ABOUT.get(category, category)
    if entry["short_id"] == "A-COIN":
        drawn = _choice_places(entry, roles)
        if drawn:
            noun = "choice" if len(drawn) == 1 else "choices"
            return f"{words} (the {noun} drawn {_and(drawn)})"
    return words


def scope(
    entry: AssumptionEntry, roles: Roles, category: str | None = None
) -> tuple[list[str], list[StationRoles]]:
    """Return the parties' laboratories, or the stations, a premise is about.

    The rule :func:`about` words (each party's laboratory for a per-party
    row; the stations for a row every emission of which is at a station, or
    a receiver, supplied-artefact or uncategorised row emitted at stations
    and for the run; the one station for a receiver premise of a
    single-station run); both lists are empty for a premise about no one
    station or laboratory. The per-station checklist of the summary reads it
    too.
    """
    category = entry["category"] if category is None else category
    emissions = entry["emitted_by"]
    named = list(dict.fromkeys(sorted(
        str(emission["party"]) for emission in emissions
        if emission.get("party") is not None
    )))
    retired = RETIRED_LABORATORY_KEYS.get(entry["machine_key"])
    if not named and retired is not None:
        named = [retired]
    if named:
        return named, []
    located = [_located(roles, emission) for emission in emissions]
    found = [station for station in located if station is not None]
    stations = sorted(
        dict.fromkeys(found),
        key=lambda station: (station.index is None, station.index or 0),
    )
    indexed = any(emission["station"] is not None for emission in emissions)
    if stations and (
        len(found) == len(located)
        or (indexed and category in (None, "receiver", "supplied-artefact"))
    ):
        return [], stations
    if category == "receiver" and len(roles.stations) == 1:
        return [], list(roles.stations)
    return [], []


def places(
    entry: AssumptionEntry, roles: Roles, category: str | None = None
) -> list[str]:
    """Return the laboratories and stations a premise applies at, in words.

    The checklist "Where each premise applies": the place :func:`scope` gives, and where
    it gives none, the place the run's roles give the premise: A-COIN at each station
    drawing a choice and at the laboratory of a party drawing one with the
    letter; on a trusted run, the source premises (A-ENS, A-SRC, A-WCP) at
    the laboratory of the party of A, where the trusted source is; A-KEYREG
    at the key holder's laboratory.
    """
    parties, stations = scope(entry, roles, category)
    found = [f"{party_name(party)}'s laboratory" for party in parties]
    found += [station_label(station) for station in stations]
    if found:
        return found
    short_id = entry["short_id"]
    if short_id == "A-COIN":
        for choice in roles.public_choices:
            drawn = _choice_stations(choice, roles)
            for place in (
                [station_label(station) for station in drawn] if drawn
                else [f"{party_name(choice.party)}'s laboratory"]
            ):
                if place not in found:
                    found.append(place)
    elif short_id in _SOURCE_PREMISES and roles.source_trusted is True:
        found.append(f"{party_name(roles.alice_party)}'s laboratory")
    elif short_id == "A-KEYREG" and roles.key_holder is not None:
        found.append(f"{party_name(roles.key_holder)}'s laboratory")
    elif len(roles.stations) == 1 and (
        short_id == "A-RECV"
        or (short_id == "A-LINK" and _receiver_chain_only(entry))
    ):
        # The receiver artefact, and a reduction chain
        # of a receiver segment only, are the one receiver's.
        found.append(station_label(roles.stations[0]))
    return found


def _receiver_chain_only(entry: AssumptionEntry) -> bool:
    """Whether A-LINK's ``reduction_chain`` binding has a receiver segment only."""
    for binding in entry["bindings"]:
        value = binding.get("value")
        if binding["name"] == "reduction_chain" and isinstance(value, Mapping):
            return bool(value.get("receiver_segment")) and not value.get(
                "source_segment")
    return False


def partition_words(value: Mapping[str, Any], roles: Roles) -> str:
    """Return a ``party_partition`` binding in words.

    ``{"alice_system": "A", "measured_factors": ["A", "B"]}`` reads "system A:
    party A (Alice); measured stations: alice_station (Alice), bob_station
    (Bob)"; a measured factor is named by the run's station at its position
    (its factor label, or "the receiver"), else by its position.
    """
    holder = value.get("alice_system")
    parts: list[str] = []
    if holder is not None:
        parts.append(f"system A: party {holder} ({party_name(holder)})")
    factors = value.get("measured_factors")
    if isinstance(factors, list | tuple) and factors:
        named = []
        for position, party in enumerate(factors):
            station = (roles.stations[position]
                       if len(roles.stations) == len(factors) else None)
            label = (
                f"measured factor {position + 1}" if station is None
                else "the receiver" if station.index is None
                else station.factor or f"station {station.index}"
            )
            named.append(f"{label} ({party_name(party)})")
        parts.append(("measured stations: " if len(named) > 1
                      else "measured station: ") + ", ".join(named))
    return "; ".join(parts) or str(dict(value))


#: The premises about a trusted source, which sits in the laboratory of the
#: party of A (meat-core/ass:lab: the systems handed out of that laboratory).
_SOURCE_PREMISES: Final[tuple[str, ...]] = ("A-ENS", "A-SRC", "A-WCP")


def _and(words: Sequence[str]) -> str:
    if len(words) <= 1:
        return "".join(words)
    return f"{', '.join(words[:-1])} and {words[-1]}"


def station_label(station: StationRoles) -> str:
    """Return "Alice's station (alice_station)", or "Bob's station (the receiver)"."""
    name = _station_words([station])
    if station.index is None:
        return f"{name} (the receiver)"
    return name if station.factor is None else f"{name} ({station.factor})"


def _choice_places(entry: AssumptionEntry, roles: Roles) -> list[str]:
    """Where A-COIN's choices are drawn: "by Alice", "at Bob's station" (R3).

    Read from the role vector's public choices, which come from the record's
    choice weightings (each naming its factor) and the families A-COIN binds.
    """
    del entry
    places: list[str] = []
    for choice in roles.public_choices:
        stations = _choice_stations(choice, roles)
        place = (
            f"at {_station_words(stations)}" if stations
            else f"by {party_name(choice.party)}"
        )
        if place not in places:
            places.append(place)
    return places


def _choice_stations(choice: PublicChoice, roles: Roles) -> list[StationRoles]:
    """Return the stations a public choice is drawn at (none for the letter's)."""
    if not choice.at_station:
        return []
    return [
        station for station in roles.stations
        if (choice.factor is not None and station.factor == choice.factor)
        or (choice.factor is None and station.party == choice.party)
    ] or [station for station in roles.stations if len(roles.stations) == 1]


_PRONOUNS: Final[Mapping[str, str]] = {"A": "her", "B": "his"}


def _holder_record(roles: Roles) -> str | None:
    """Return the key holder's own record in words, or ``None`` (R1, R4).

    A-KEYREG: "its own record (its letters, the detection results of its
    measuring stations, or both, whichever it holds)". The holder holds the
    letters where it holds system A and the declaration has two letters or
    more, and the detection results of each of its stations.
    """
    holder = roles.key_holder
    if holder is None:
        return None
    parts: list[str] = []
    if holder == roles.alice_party and roles.has_letters:
        parts.append(f"{_PRONOUNS.get(holder, 'its')} letters")
    stations = roles.stations_of(holder)
    if stations:
        parts.append("the detection results of "
                     + _and([station_label(station) for station in stations]))
    return _and(parts) or None


def role_notes(entry: AssumptionEntry, roles: Roles) -> list[str]:
    """Return the run-specific lines printed beside a premise (R2, R4).

    "Not on this run: ..." for the role-conditioned clauses of its plain text
    whose condition this run does not meet
    (:data:`certiqs_key.runs.roles.ROLE_CONDITIONED_CLAUSES`), for A-SEED
    that no party is fixed to draw the post-processing seeds, and for
    A-KEYREG which record of the key holder's it reads here.
    """
    notes: list[str] = []
    missing = not_on_this_run(entry["short_id"], roles, entry["emitted_by"])
    if missing:
        notes.append("Not on this run: " + "; ".join(
            f"{clause}, since {reason}" for clause, reason in missing
        ) + ".")
        if entry["short_id"] == "A-LAB":
            # What stays excluded at every laboratory.
            notes.append(
                "Light sent into a laboratory to read out a letter, a setting, a "
                "choice or "
                "a detector state (a Trojan-horse attack, at a receiver as at a "
                "modulator) still violates this premise on this run."
            )
    if entry["short_id"] == "A-SEED":
        # Which party draws the seeds: the analysed
        # post-processing (meat-core/def:postprocessing-model) draws each seed
        # and announces it, and names no party; nor does any premise.
        notes.append(
            "Which party draws each post-processing seed (the error-correction "
            "seed, the error-verification seed and the privacy-amplification "
            "hash) is not fixed by the analysed post-processing: each is drawn "
            "and then announced. As for the seeds, this premise is about the "
            "random number generator of whichever party draws each; [[A-HASH]] "
            "is about the hash families the seeds select from."
        )
    if entry["short_id"] == "A-KEYREG" and roles.key_holder is not None:
        record = _holder_record(roles)
        holder = party_name(roles.key_holder)
        if record is not None:
            notes.append(
                f"On this run {holder} holds the key; "
                f"{_PRONOUNS.get(roles.key_holder, 'its')} own record here is "
                f"{record}."
            )
    return notes


def roles_box(roles: Roles) -> list[str]:
    """Return "Roles on this run": who does what, read off the record (R1).

    Who sends (with a trusted source), each station and its party, who holds
    the key and from which record, where each public choice is drawn, and
    the roles absent from the run (:func:`roles_absent`). Alice and Bob are
    the declaration's parties A and B ([[meat-core/def:declaration]]).
    """
    if not roles.stations and roles.source_mode is None:
        return []
    lines: list[str] = []
    senders = [party for party in ("A", "B") if roles.sends(party)]
    holder_of_a = party_name(roles.alice_party)
    if senders:
        lines.append(_and([party_name(party) for party in senders])
                     + " sends: the trusted source's signals enter the proof.")
    elif roles.source_trusted is False:
        delivered = ("one system to each station" if len(roles.stations) > 1
                     else "its systems to the station")
        line = f"Neither party sends: the untrusted source delivers {delivered}"
        if roles.measures_a(roles.alice_party):
            line += (f", and one to {holder_of_a}, who measures it to obtain "
                     "the round's letter")
        # Where the pump, the timing and the trigger stand (the stage-9
        # experimentalist reader): meat-core/ass:lab counts an untrusted
        # source as outside every laboratory, even one it is in.
        lines.append(
            line + ". The source, its pump, timing and trigger electronics "
            "included, counts as outside every laboratory wherever it stands "
            "([[A-LAB]])."
        )
    elif roles.draws_letter(roles.alice_party):
        lines.append(f"Neither party sends a signal the proof models: "
                     f"{holder_of_a}'s letter is local randomness.")
    if roles.stations:
        lines.append(("Measuring stations: " if len(roles.stations) > 1
                      else "Measuring station: ")
                     + ", ".join(station_label(station)
                                 for station in roles.stations) + ".")
    if roles.key_holder is not None:
        record = _holder_record(roles)
        lines.append(f"Key: {party_name(roles.key_holder)} holds it"
                     + ("" if record is None else f", computed from {record}")
                     + ".")
    if roles.public_choices:
        drawn: list[str] = []
        for choice in roles.public_choices:
            place = _choice_places_of(choice, roles)
            # "Z, X or Y", not "Z or X or Y" (n1).
            values = (" or ".join(choice.choices) if len(choice.choices) < 3
                      else f"{', '.join(choice.choices[:-1])} or {choice.choices[-1]}")
            drawn.append(f"{values}, {place}"
                         + (", weighted by a private setting"
                            if choice.setting_dependent else ""))
        lines.append("Public choices: " + "; ".join(drawn) + ".")
    else:
        lines.append("Public choices: none.")
    return lines


#: The lead of the roles absent from a run (:func:`roles_absent`).
ROLES_ABSENT_LEAD: Final[str] = (
    "Not on this run, so the parts of the premises that apply only with them do "
    "not apply here (each premise says which):"
)


def roles_absent(roles: Roles) -> list[str]:
    """Return the roles a run does not have, one line each (R1).

    A trusted source, a private setting at a station, a second letter: each
    premise's clauses conditioned on one of them do not apply, and each
    premise says which (its role notes).
    """
    if not roles.stations and roles.source_mode is None:
        return []
    missing: list[str] = []
    if roles.source_trusted is False:
        missing.append("A trusted source: the source is untrusted.")
    if roles.stations and not any(station.setting for station in roles.stations):
        missing.append("A private setting: no station has one.")
    if not roles.has_letters:
        only = f" ({roles.letters[0]})" if len(roles.letters) == 1 else ""
        missing.append("A second letter: the declaration has one letter"
                       f"{only}, the per-round value a sender would prepare "
                       "on Alice's side.")
    return missing


def _choice_places_of(choice: PublicChoice, roles: Roles) -> str:
    if not choice.at_station:
        return f"drawn by {party_name(choice.party)} with the letter"
    stations = _choice_stations(choice, roles)
    if not stations:
        return f"drawn by {party_name(choice.party)}"
    return "drawn at " + _station_words(stations)


# --------------------------------------------------------------------------
# Idealised device values
# --------------------------------------------------------------------------

#: THE IDEAL EXTREMES OF THE KNOWN PARAMETER KINDS. WHY: a report on declared
#: ideal devices (efficiency 1, no dark counts, visibility 1) must say near the
#: top that the number covers only such a device. THE RULE: a declared input is
#: at its ideal extreme where its kind, read from the instance's parameter
#: table (the ``quantity`` of the row, else its name, the word itself or a
#: party prefix before it, ``alice_efficiency``), names a device imperfection
#: and every value it holds (each port's, for a per-port value) equals the
#: extreme. Per kind: (label, matches, ideal value).
_IDEAL_KINDS: Final[tuple[tuple[str, tuple[str, ...], str, Fraction], ...]] = (
    ("detection efficiency 1", ("efficiency",), "efficiency", Fraction(1)),
    ("transmittance 1", ("transmittance",), "transmittance", Fraction(1)),
    ("dark-click probability 0", (), "dark_count", Fraction(0)),
    ("visibility 1", (), "visibility", Fraction(1)),
    ("no misalignment", (), "misalignment", Fraction(0)),
    ("QBER 0", (), "qber", Fraction(0)),
    # A record whose PBS leaks are not declared apart declares one
    # extinction (``alice_pbs_extinction``); without this row its report
    # loses its idealised lines. Matched as ``pbs_extinction`` so that another
    # extinction, such as a ratio in dB where 0 is the worst value, is not read
    # as ideal.
    ("polarising beam splitter extinction 0", (), "pbs_extinction",
     Fraction(0)),
    ("polarising beam splitter transmitted leak 0", (), "pbs_leak_transmitted",
     Fraction(0)),
    ("polarising beam splitter reflected leak 0", (), "pbs_leak_reflected",
     Fraction(0)),
    ("no depolarisation", (), "depolarisation", Fraction(0)),
)


#: A PROCESSING SETTING, NOT A DEVICE VALUE: the efficiency normalization
#: (``efficiency_normalization``, ``alice_efficiency_normalization``) has the
#: quantity of a transmittance and a name containing "efficiency", and its
#: value 1 turns factoring off; it says nothing about how ideal a device is.
_NOT_A_DEVICE_VALUE: Final[str] = "efficiency_normalization"


def _exact(value: Any) -> Fraction | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value.strip())
        except (ValueError, ZeroDivisionError):
            return None
    return None


def _at_extreme(value: Any, ideal: Fraction) -> bool:
    values = list(value.values()) if isinstance(value, Mapping) else [value]
    found = [_exact(item) for item in values]
    return bool(found) and all(item == ideal for item in found)


def idealised(
    inputs: Sequence[InputRow], engaged: Collection[str], roles: Roles,
    *, after_headline: bool = False, zero_outcomes: int = 0,
) -> SummaryItem | None:
    """Return the at-a-glance line on idealised values, or ``None``.

    The line opens with :data:`IDEALISED_HEADLINE`; with ``after_headline``
    (a run whose box opens with :func:`idealised_headline`) it opens with
    "What is idealised:" instead.

    Every idealisation that bears on security
    first, then the honest model's:

    * an engaged A-IDEAL (the Band-A route's ideal qubit receiver, which no
      real optical receiver meets);
    * an engaged A-ENS whose trusted source emits a qubit (a transmitted
      system of dimension two): exactly the declared qubit states;
    * a declared intensity exactly 0 under an engaged A-WCP (the vacuum
      decoy);
    * device values (section ``device``) at their ideal extreme
      (:data:`_IDEAL_KINDS`), which A-EXACT holds exact where it is a premise
      of the run;
    * honest-model values (section ``model``) at their ideal extreme, which
      bear only on completeness: the completeness figure no longer bounds
      how often a device that does not show them aborts.

    Where the acceptance test admits a count of exactly 0 in some outcomes
    (``zero_outcomes``, the setup's rule), the honest model's sentence says
    so plainly: one round with such an outcome aborts the run (A-CONFORM (i);
    the setup's acceptance test says the same per outcome).

    Nothing is shown when the run declares no such value. A run whose only
    idealisation is the honest model's is not called an idealised example:
    its line opens with :data:`IDEALISED_HONEST_MODEL`, since that bears on
    completeness only (and ``after_headline`` does not apply to it).
    """
    security, model = _idealisations(inputs, engaged, roles, zero_outcomes)
    if not security:
        if model is None:
            return None
        return {"text": f"{IDEALISED_HONEST_MODEL} {model}", "pointer": None,
                "anchor": "inputs"}
    if after_headline:
        first, *rest = security
        lines = [f"What is idealised: {first[0].lower()}{first[1:]}", *rest]
    else:
        lines = [IDEALISED_HEADLINE, *security]
    if model is not None:
        lines.append(model)
    return {"text": " ".join(lines), "pointer": None, "anchor": "inputs"}


def idealisation_bears_on_security(
    inputs: Sequence[InputRow], engaged: Collection[str], roles: Roles
) -> bool:
    """Whether :func:`idealised` names an idealisation that bears on security.

    A-IDEAL, a qubit A-ENS, a zero intensity under A-WCP or device values at
    their ideal extreme; the honest model's alone bears on completeness only.
    Only such a run opens At a glance with :func:`idealised_headline`.
    """
    return bool(_idealisations(inputs, engaged, roles)[0])


def _idealisations(
    inputs: Sequence[InputRow], engaged: Collection[str], roles: Roles,
    zero_outcomes: int = 0,
) -> tuple[list[str], str | None]:
    """Return the security-bearing idealisation sentences and the honest model's."""
    device: list[str] = []
    model: list[str] = []
    intensities: list[str] = []
    for row in inputs:
        if row["section"] not in ("device", "model") or row["value"] is None:
            continue
        name = row["name"].rsplit(".", 1)[-1]
        if name.endswith(_NOT_A_DEVICE_VALUE):
            continue
        value = row["value"] if row["prepared"] is None else row["prepared"]
        if (row["section"] == "device" and row["quantity"] == "mean_photon_number"
                and "A-WCP" in engaged and _at_extreme(value, Fraction(0))):
            intensities.append(f"{name} = 0")
            continue
        for label, quantities, word, ideal in _IDEAL_KINDS:
            kind = (row["quantity"] in quantities) if quantities else False
            named = name == word or name.endswith(f"_{word}")
            if (kind or named) and _at_extreme(value, ideal):
                found = device if row["section"] == "device" else model
                if label not in found:
                    found.append(label)
                break
    security: list[str] = []
    if "A-IDEAL" in engaged:
        security.append(
            "The run's receiver is the ideal qubit receiver of the Band-A route "
            "([[A-IDEAL]]): no real optical receiver meets this premise, so the "
            "key length covers no real receiver."
        )
    if "A-ENS" in engaged and roles.transmitted_dim == 2:
        security.append(
            "The run's trusted source emits exactly the declared qubit states, one "
            "per round ([[A-ENS]])."
        )
    if intensities:
        security.append(
            "The run's decoy source emits exactly the declared intensities, "
            f"among them {', '.join(intensities)} ([[A-WCP]])."
        )
    if device:
        exact = " ([[A-EXACT]])" if "A-EXACT" in engaged else ""
        security.append(
            "The run's device values are at their ideal extreme "
            f"({', '.join(device)}): the key length covers only a device with "
            f"exactly these values{exact}."
        )
    honest = None
    if model:
        # The reader of decoy_bb84 took "possibly on almost every run" for
        # an understatement: where the test admits exactly 0 counts in some
        # outcomes, what one such round does is said plainly.
        zero = (
            "The acceptance test built from it admits a count of exactly 0 in "
            + ("one outcome, so a single round with it" if zero_outcomes == 1
               else f"{zero_outcomes} outcomes, so a single round with one of them")
            + " makes the run abort ([[A-CONFORM]]; see Acceptance test). "
        ) if zero_outcomes else ""
        honest = (
            f"The run's honest model is at its ideal extreme ({', '.join(model)}): the "
            "acceptance test is built for statistics a real device may not show. "
            + zero
            + "For such a device the completeness figure \u03b5* no longer bounds "
            "how often it aborts"
            + ("" if zero_outcomes else ", possibly on almost every run")
            + "; security is unaffected."
        )
    return security, honest


#: THE FIRST LINE OF AT A GLANCE ON A RUN WITH A SECURITY-BEARING
#: IDEALISATION (:func:`idealisation_bears_on_security`). WHY: the reader who
#: stops after one line must learn that the number is for an idealised
#: example; :func:`idealised`'s line, which says what is idealised and what
#: that means, closes the box (build.py places both).
IDEALISED_HEADLINE: Final[str] = "Idealised example, not a characterised device."

#: THE OPENING OF THE LINE ON A RUN WHOSE ONLY IDEALISATION IS THE HONEST
#: MODEL'S: the key length still covers the declared devices, so the run is
#: not called an idealised example.
IDEALISED_HONEST_MODEL: Final[str] = (
    "Idealised honest model, bearing on completeness only."
)


def idealised_headline() -> GlanceItem:
    """Return the opening at-a-glance fragment of a run :func:`idealised` names.

    :data:`IDEALISED_HEADLINE` as a fragment, its key part in bold.
    """
    return {"lead": "Idealised example", "text": ", not a characterised device",
            "anchor": "inputs"}


# --------------------------------------------------------------------------
# Consequence of a premise's failure
# --------------------------------------------------------------------------

#: A premise's consequence in words, by what its ``affects`` puts at stake
#: :func:`consequence_words`.
CONSEQUENCE_WORDS: Final[Mapping[str, str]] = {
    "secrecy": "security (the key may leak)",
    "correctness": "security (the two keys may differ)",
    "both": "security (the key may leak, or the two keys may differ)",
    "completeness": "only how often an honest run aborts, never security",
}


def consequence_words(short_id: str, affects: Sequence[str] | None) -> str:
    """Return "If it fails: ..." in words, naming only what is at stake.

    Secrecy alone reads "the key may leak", correctness alone "the two keys
    may differ", both or none (the safe reading) both; a completeness-only
    premise reads "only how often an honest run aborts". A premise with words
    of its own in :data:`CONSEQUENCE_WORDS` is read in them; none has any
    now (A-REACH, which had, affects secrecy as well since its failure was
    shown to let a key length grow with the mismatch:
    ``meat-core/prop:minimal-divergence``).
    """
    found = set(affects or ())
    if consequence(affects) == "completeness":
        # A premise with words of its own (CONSEQUENCE_WORDS) is read in them.
        return CONSEQUENCE_WORDS.get(short_id, CONSEQUENCE_WORDS["completeness"])
    secrecy, correctness = "secrecy" in found, "correctness" in found
    if secrecy and not correctness:
        return CONSEQUENCE_WORDS["secrecy"]
    if correctness and not secrecy:
        return CONSEQUENCE_WORDS["correctness"]
    return CONSEQUENCE_WORDS["both"]


def consequence(affects: Sequence[str] | None) -> str:
    """Return ``security`` or ``completeness``: what a premise's failure affects.

    From its ``affects`` (the claim header): ``completeness`` where that is
    all it affects, ``security`` where secrecy or correctness is at stake, or
    where the record does not say (the safe reading).
    """
    found = set(affects or ())
    return "completeness" if found == {"completeness"} else "security"


def consequence_rows(counts: ConsequenceCounts) -> list[tuple[str, str]]:
    """Return the premises counted by consequence, one table row each.

    Every premise whose ``affects`` puts secrecy or correctness at stake can
    break security, the premises about supplied artefacts and the engine's
    numerics among them (``engine``, those of them that can, named); the rest
    affect only completeness.
    """
    security, engine = counts["security"], counts["engine"]
    rows = [("Can break security if they fail", str(security))]
    if engine:
        rows.append(("of them, about artefacts supplied to the engine and its "
                     "numerics", f"{len(engine)}: {', '.join(engine)}"))
    rows.append(("Affect only completeness: how often an honest run aborts, or "
                 "whether it yields a key", str(counts["completeness"])))
    rows.append(("All premises of this run", str(security + counts["completeness"])))
    return rows


#: "What you vouch for" in three groups, each by the premises' categories:
#: (key, heading, categories). A category no group names joins the first.
VOUCH_GROUPS: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
    ("devices", "Your devices and setup", ()),
    ("procedure", "How the run is carried out",
     ("protocol-structure", "post-processing")),
    ("engine", "Artefacts and the engine", ENGINE_CATEGORIES),
)


def vouch_group(category: str | None) -> str:
    """Return the key of the "What you vouch for" group a category falls in."""
    for key, _, found in VOUCH_GROUPS:
        if category in found:
            return key
    return VOUCH_GROUPS[0][0]


_SENTENCE_END: Final = re.compile(r"(?<=[a-z0-9)\]])\.\s+(?=[A-Z\[])")


def first_sentence(text: str) -> str:
    """Return a claim summary's first sentence: the result in plain words.

    A summary gives the result, then its consequence or role
    (spec/claim-format.md section 3.1); the first sentence is the existing
    one-liner What you vouch for shows.
    """
    found = _SENTENCE_END.search(text)
    return text if found is None else text[:found.start()] + "."


class StatementStatus(NamedTuple):
    """The review status of the security statement: a lead, a list, a tail."""

    #: The main message: the lowest status over the claims and the claim
    #: graph beneath them.
    lead: str
    #: One line per claim: its id as a ``[[...]]`` token, its role, its status.
    items: list[str]
    #: Where the device and route premises' statuses are.
    tail: str

    def text(self) -> str:
        """Return the three parts as one string (for search and tests)."""
        return " ".join([self.lead, *self.items, self.tail])


def statement_status(
    claims: Sequence[ClaimRef], formed: Sequence[ClaimRef] = (),
    route: Sequence[ClaimRef] = (), outside: Sequence[str] | None = None,
    sweep: bool = False, route_accepted: bool = False,
) -> StatementStatus | None:
    """Return the review status of the security statement (item 6).

    The lowest effective status over the statements (``claims``) and the
    claims this run forms its key length through (``formed``, the run's
    key-length roots) leads: the claim graph they rest on. Then each of them
    with its own status, one line each. That closure holds no device or
    route premise, which reaches the key length through the run's own roots,
    so the tail says so and points to the premises' own statuses. The route
    theorems those premises reach it through (``route``, the manifest's
    roots below accepted) are named where any is below accepted; where none
    is and every root was found in the closure table (``route_accepted``),
    the tail says that every one is accepted.
    """
    if not claims:
        return None
    subject = "sweep" if sweep else "run"
    ladder = ("superseded", "draft", "verified", "accepted", "implemented")

    def words(claim: ClaimRef) -> str:
        return _CLAIM_STATUS_WORDS.get(claim["status"], claim["status"])

    shown = {claim["id"] for claim in claims}
    roots = [claim for claim in formed if claim["id"] not in shown]
    lowest = min(
        (claim["effective_status"] for claim in [*claims, *roots]),
        key=lambda status: ladder.index(status) if status in ladder else -1,
    )
    lead = (
        "Review status: the lowest status of the claims below, with everything "
        f"they rest on in the claim graph, is: {_STATUS_WORDS.get(lowest, lowest)}."
    )
    items = [
        *(f"[[{claim['id']}]], the security statement: {words(claim)}."
          for claim in claims),
        *(f"[[{claim['id']}]], on this run: {words(claim)}." for claim in roots),
    ]
    if outside:
        # Named: the premises outside the closure of the claims listed, so
        # that no premise of the run is said to be outside wrongly.
        text = (
            ("The premise " if len(outside) == 1 else "The premises ")
            + _and([f"[[{short_id}]]" for short_id in outside])
            + (" is" if len(outside) == 1 else " are")
            + " not beneath the claims above in the claim graph: "
            + ("it enters" if len(outside) == 1 else "they enter")
            + " through this " + subject + "'s own route, and each carries its "
            "own review "
            "status under Assumptions you vouch for."
        )
    elif outside is not None:
        text = f"Every premise of this {subject} is beneath the claims above."
    else:
        text = (
            "The closure table does not state which of this "
            + subject + "'s premises lie beneath these claims; each carries "
            "its own review status under Assumptions you vouch for."
        )
    if route:
        below = min(
            (claim["effective_status"] for claim in route),
            key=lambda status: ladder.index(status) if status in ladder else -1,
        )
        text += (
            " Of the route theorems they reach it through, "
            + _and([f"[[{claim['id']}]]" for claim in route])
            + (" rests" if len(route) == 1 else " rest")
            + " on the claim graph at the lowest status: "
            + _STATUS_WORDS.get(below, below)
            + "; every other one is accepted with everything it rests on."
        )
    elif route_accepted and outside:
        # The route theorems' status is
        # printed from the run's own manifest roots, not only guarded by a
        # test over the shipped examples.
        text += (
            " Every route theorem they reach it through (the roots of this "
            + subject + "'s assumption manifest) is accepted with everything "
            "it rests on."
        )
    return StatementStatus(lead, items, text)


#: "At stake" words of a premise whose own text says more precisely what a
#: failure means, keyed by short id. A-REACH's completeness: an honest run
#: may abort more often, and on a checked run a proven mismatch withholds the
#: key length where it reaches its share (its user statement;
#: ``meat-core/req:unreachable-acceptance-set``). Its secrecy reads in the
#: generic words.
_AT_STAKE_OF: Final[Mapping[str, Mapping[str, str]]] = {
    "A-REACH": {"completeness": "completeness (an honest run may abort more "
                                "often, and a checked run whose mismatch is "
                                "proven may report no key length)"},
}


def at_stake(affects: Sequence[str] | None, short_id: str = "") -> list[str]:
    """Return what an assumption puts at stake, in words."""
    own = _AT_STAKE_OF.get(short_id, {})
    return [own.get(item, AT_STAKE.get(item, item)) for item in affects or ()]


def emitted_stations(emissions: Sequence[Emission]) -> list[int]:
    """Return the stations an entry was emitted at, sorted."""
    return sorted({
        emission["station"] for emission in emissions
        if emission["station"] is not None
    })


# --------------------------------------------------------------------------
# The summary
# --------------------------------------------------------------------------


#: The title of the box at the top of the summary.
AT_A_GLANCE_TITLE: Final[str] = "At a glance"


def epsilon_text(value: float | None) -> str:
    """Return an ε as ``1.86e-09``, a power of two also as ``(2^-29)`` (L14)."""
    if value is None:
        return "\u2014"
    text = f"{value:.3g}"
    if value > 0:
        mantissa, exponent = math.frexp(value)
        if mantissa == 0.5:
            text += f" (2^{exponent - 1})"
    return text


class ZeroKey(NamedTuple):
    """Why a completed run's key length is 0, as its record states it (M1).

    Read off the record and never inferred beyond it: ``symbol`` and
    ``bound`` are the number the key length is computed from (h_cert or
    h_lb), ``rounds`` is n, and the record's deductions term by term:
    ``lambda_ec`` (taken to grow with n: the record does not say it was
    declared as a fixed bit count, and an estimate from the honest model,
    runs/error_correction.py, is linear in n), ``verification``, the
    finite-size term ``amplification``, ``hash_penalty`` and the constant bit
    ``added_back``; ``stopped_at_limit`` whether the solver stopped at its step
    limit, with its ``steps`` and its Frank-Wolfe ``gap``; ``estimate`` the
    solver's estimate of h_low, which is not a bound.
    """

    symbol: str
    bound: float
    rounds: int | None
    lambda_ec: float | None
    verification: float
    amplification: float
    hash_penalty: float
    added_back: float
    stopped_at_limit: bool
    steps: int | None
    gap: float | None
    estimate: float | None

    @property
    def fixed(self) -> float | None:
        """The deductions that do not grow with n, less the constant bit."""
        if self.lambda_ec is None:
            return None
        return (self.verification + self.amplification + self.hash_penalty
                - self.added_back)

    @property
    def deducted(self) -> float | None:
        """Every bit the key length deducts, less the constant bit."""
        fixed = self.fixed
        return None if fixed is None or self.lambda_ec is None else (
            fixed + self.lambda_ec)

    def shortfall(self) -> float | None:
        """Return how far the bound per round is from leaving a key, or ``None``.

        Below 0, its distance from 0 (the clamp); above 0, how far it falls
        short, per round, of the bits deducted plus the one whole bit a key
        needs.
        """
        if self.bound <= 0:
            return -self.bound
        if self.rounds and self.deducted is not None:
            short = (self.deducted + 1) / self.rounds - self.bound
            return short if short > 0 else None
        return None

    def limited(self) -> bool:
        """Whether the solver stopped at its step limit, its gap above the shortfall."""
        short = self.shortfall()
        return (self.stopped_at_limit and self.gap is not None
                and short is not None and self.gap > short)


def _float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if math.isfinite(value) else None


def zero_key(
    result: ResultSection,
    diagnostics: Mapping[str, Any],
    entropy: tuple[str, float] | None,
) -> ZeroKey | None:
    """Return why a completed run's key length is 0, or ``None`` where it is not.

    ``entropy`` is the number the key length is computed from with its
    symbol (h_cert on a certified run, h_lb on a first-order one). ``None``
    on a refusal, a run with no key length or a positive one, and where the
    outer alpha search already says no alpha gave a key.
    """
    if (result["refusal"] is not None or result["key_length"] != 0
            or result["alpha"].get("no_positive_key") or entropy is None):
        return None
    found = result["deductions"]

    def term(name: str) -> float:
        value = None if found is None else found[name]  # type: ignore[literal-required]
        return 0.0 if value is None else float(value)

    steps = diagnostics.get("iterations")
    return ZeroKey(
        symbol=entropy[0],
        bound=entropy[1],
        rounds=result["rounds"],
        lambda_ec=None if found is None else term("error_correction"),
        verification=term("error_verification"),
        amplification=term("privacy_amplification"),
        hash_penalty=term("hash_penalty"),
        added_back=term("added_back"),
        stopped_at_limit=diagnostics.get("solver_status") == "iteration-limit",
        steps=steps if isinstance(steps, int) and not isinstance(steps, bool) else None,
        gap=_float(diagnostics.get("frank_wolfe_gap")),
        estimate=_float(diagnostics.get("h_low")),
    )


def _per_round(cause: ZeroKey) -> tuple[str, float] | None:
    """Return the positive number per round n multiplies, with its words.

    The bound where positive. Where it is not, max{0, h} is 0 at every n
    ([[meat-core/cor:keylength-bound]]), so more rounds alone give no key:
    only where the solver stopped at its step limit short of a positive bound
    (:meth:`ZeroKey.limited`) is the solver's estimate of h_low used, named
    as an estimate, and the lever then says it is conditional on more steps.
    """
    if cause.bound > 0:
        return f"n·{cause.symbol}", cause.bound
    if cause.limited() and cause.estimate is not None and cause.estimate > 0:
        return "n times the solver's estimate of h_low", cause.estimate
    return None


def _deducted_for(cause: ZeroKey) -> str:
    """Name what the deducted bits pay for, the hash penalty where it is counted."""
    return ("error correction, error verification, privacy amplification and "
            "the hash penalty" if cause.hash_penalty else
            "error correction, error verification and privacy amplification")


def zero_key_sentence(cause: ZeroKey) -> str:
    """Return the cause of a key length of 0 the record states, in plain words.

    The bound below 0 and clamped; or n times it below the bits the key
    length deducts; or above them by less than the whole bit a key needs, so
    that the sum rounds down to 0 ([[meat-core/thm:keylength]],
    [[meat-core/cor:keylength-bound]]); where the solver stopped at its step
    limit with a Frank-Wolfe gap larger than that shortfall, that too, and
    the estimate of h_low where positive, called an estimate and never a key
    ([[meat-core/frank-wolfe/thm:firstorder]]).
    """
    deducted = cause.deducted
    if cause.bound <= 0:
        text = (
            f"The bound the key length is computed from, {cause.symbol} = "
            f"{cause.bound:.3g} bits per round, is not positive, so the "
            f"accumulated entropy is clamped at 0 ([[{KEYLENGTH_BOUND_CLAIM}]])."
        )
    elif cause.rounds and deducted is not None and (
        cause.rounds * cause.bound < deducted
    ):
        text = (
            f"The accumulated entropy n·{cause.symbol} ≈ "
            f"{_bits(cause.rounds * cause.bound)} bits is less than the "
            f"{_bits(deducted)} bits the key length deducts for "
            + _deducted_for(cause) + ", less "
            f"the constant bit ([[{KEYLENGTH_CLAIM}]])."
        )
    elif cause.rounds and deducted is not None:
        text = (
            f"The accumulated entropy n·{cause.symbol} ≈ "
            f"{_bits(cause.rounds * cause.bound)} bits, less the "
            f"{_bits(deducted)} bits the key length deducts for "
            + _deducted_for(cause) + " (the "
            "constant bit added back), leaves less than one bit, which rounds "
            f"down to 0 ([[{KEYLENGTH_CLAIM}]])."
        )
    else:
        text = (
            f"The key length computed from {cause.symbol} = {cause.bound:.3g} "
            f"bits per round rounds down to 0 ([[{KEYLENGTH_CLAIM}]])."
        )
    if cause.limited():
        assert cause.gap is not None
        text += (
            " The solver stopped at its step limit"
            + ("" if cause.steps is None else f" of {cause.steps:,} steps")
            + f" with a Frank-Wolfe gap of {cause.gap:.3g} bits per round, larger "
            + (f"than |{cause.symbol}| = {-cause.bound:.3g}" if cause.bound <= 0
               else "than the shortfall per round")
        )
        if cause.estimate is not None and cause.estimate > 0:
            text += (
                f", while its estimate of h_low is {cause.estimate:.3g} bits per "
                "round, positive. The estimate is not a bound and gives no key "
                f"([[{FIRSTORDER_CLAIM}]])."
            )
        else:
            text += f" ([[{FIRSTORDER_CLAIM}]])."
    return text


#: WHAT A PROTOCOL-DOCUMENT USER CAN CHANGE, by the refusal code of a module
#: that refuses what a document declared. The module's own detail is written
#: for its own callers and may name modules and reductions a document cannot
#: express; each hint says what the document itself can change, read off the
#: claim that refuses and the format guide (instances/declared/README.md). Said
#: only on a run lowered from a protocol document; a code with no entry adds
#: nothing.
DOCUMENT_HINTS: Final[Mapping[str, str]] = {
    "band_a_outside_ideal_receiver": (
        "In a protocol document, declared_povm stations with the identity "
        "link put the run on the Band-A route ([[protocol-compiler/def:banda]]) "
        "wherever the source carries no source segment and the emitted sector "
        "set is a single sector, and that route admits exactly one measured "
        "station: one declared_povm station on a receiver system of dimension "
        "two (and, with a trusted source, a transmitted system of dimension "
        "two), its family projective as declared "
        "([[protocol-compiler/req:band-a-ideal-receiver]]). Declare any other "
        "receiver, and each station of a protocol in which both parties "
        "measure, as an optical station (kind: optical); see "
        "instances/declared/README.md."
    ),
    "choice_weights_not_normalized": (
        "In a protocol document, the weights of a choice family must be "
        "positive and sum to exactly 1, and their running sum, in the order "
        "the choices are listed, must be exact in binary64 "
        "([[protocol-compiler/req:weight-list]]): declare weights that are, "
        "such as fractions whose denominators are powers of two."
    ),
    "physical_family_not_admissible": (
        "In a protocol document, the elements of each declared_povm station "
        "must be Hermitian and positive semidefinite and sum to the identity "
        "exactly, with the running sum, in the order the outcomes are listed, "
        "exact in binary64 "
        "([[protocol-compiler/req:physical-family-decision]]); the detail names "
        "the condition that fails and the first element at fault."
    ),
}


#: Why the check of the statistics did not run, in a few words for the
#: inputs table (m1), by the record's ``unchecked_reason``.
_NOT_RUN_WORDS: Final[Mapping[str, str]] = {
    "out_of_scope": "the statistics are your honest model's predictions and you "
                    "declared no constraint entry",
    "opted_out": "switched off",
}


def statistics_not_run(result: ResultSection) -> str | None:
    """Return "not run: <reason>" where the check of the statistics did not run.

    The record's ``statistics_check`` setting says only that the check was
    asked for; it did not run on a run its scope excludes (the record's
    ``unchecked_reason``) or one refused before the solve, where it runs.
    ``None`` where it ran, or the record does not say.
    """
    check = result["statistics_check"]
    if check is not None and not check["checked"]:
        reason = str(check["unchecked_reason"])
        return f"not run: {_NOT_RUN_WORDS.get(reason, reason)}"
    refusal = result["refusal"]
    if refusal is not None and refusal["stage"] != "solve" and (
        check is None or (check["bound"] is None
                          and check["no_bound_reason"] is None
                          and not check["refused"])
    ):
        return (f"not run: the run was refused at its {refusal['stage'] or 'unknown'}"
                " stage, before the solve")
    return None


def at_a_glance(
    result: ResultSection,
    premises: int,
    snap_status: str | None,
    evaluated_off: int = 0,
    moved_blocks: int = 0,
    supplied_law: bool = False,
    k_auth: Any = None,
    idealised_devices: bool = False,
    zero: ZeroKey | None = None,
    lambda_ec: Any = None,
    diagnostics: Mapping[str, Any] | None = None,
    engine_premises: Sequence[str] = (),
) -> tuple[list[GlanceItem], list[SummaryItem]]:
    """Return the box at the top of the summary and the considerations beneath it.

    THE BOX holds terse fragments, each with its key part in bold (``lead``)
    and a link to its section: the key length, the key rate, ε, the premises
    the run record lists (``premises``, counted over What you vouch for; the
    guarantee states them, [[meat-core/cor:composed-security]]), and that
    the calculation is model-based (the acceptance test is built around the
    honest model's predictions, or around a distribution supplied in its
    place, ``supplied_law``). A refused run's box says only that no key was
    output and at which stage.

    THE CONSIDERATIONS ("Key rate considerations", right after the box) hold
    each nuance in one plain sentence with its link, so that none vanishes
    from the summary: the check of the statistics; the measurement blocks
    the run evaluated off their snap (``evaluated_off`` of the
    ``moved_blocks``; [[foundations/def:evaluated-off-snap]],
    [[meat-core/frank-wolfe/cor:fo-reference]]); A-SNAP with its effective
    status where the run rests on it (``snap_status``); the tier the key
    length is reported at, a first-order one with the arithmetic no premise
    covers ([[meat-core/frank-wolfe/rem:fo-arithmetic]]); a refusal's
    explanation. No grade is given beyond what those claims say; the
    qualifiers and claims stand in the section each line links. A completed
    run whose key length is 0 (``zero``, :func:`zero_key`) opens the box with
    "No key at these settings" in place of the key length and its rate, and
    its cause as the record states it opens the considerations. A declared
    λ_EC of 0 (``lambda_ec``) is said in the box beside the free
    authentication: Not counted says the key length is then too long for a
    run that sends an error-correction transcript. A search the step limit
    stopped with the solver's estimate of h_low well above the bound
    (``diagnostics``: a relative gap of at least :data:`LARGE_GAP`) is said
    among the considerations: stopping early makes the bound looser, not
    invalid ([[meat-core/frank-wolfe/thm:firstorder]]).
    """
    refusal = result["refusal"]
    if refusal is not None:
        stage = refusal["stage"] or "unknown"
        box: list[GlanceItem] = [{
            "lead": "No key",
            "text": f": the run was refused at its {stage} stage, so nothing is "
                    "certified",
            "anchor": "result",
        }]
        if refusal["reason"] == UNREACHABLE_REFUSAL:
            # The core's refusal (meat-core/req:unreachable-acceptance-set (iv)).
            return box, [{
                "text": statistics_refusal(result),
                "pointer": None, "anchor": "result",
            }]
        if refusal["reason"] == CONTRADICTION_REFUSAL:
            # The run tier's plausibility refusal (runs/plausibility.py), in
            # plain words: a proved contradiction between the statistics and
            # the model.
            return box, [{
                "text": "The accepted statistics contradict the declared model. "
                        "Each entropy term of the program is at most "
                        "log₂(d_Z + 1) bits per key-live round, while its "
                        "divergence penalty has no ceiling "
                        f"([[{VALUE_RANGE_CLAIM}]]); the run's entropy bound lies "
                        "above what the entropy terms can carry, so no feasible "
                        "state of the model reproduces any accepted statistic, "
                        "and a key computed from that bound would have no warrant "
                        "for this device.",
                "pointer": None, "anchor": "result",
            }]
        return box, []
    if result["key_length"] is None:
        return [{
            "lead": "No key length",
            "text": ": the run completed but reports none, so nothing is certified",
            "anchor": "result",
        }], []
    rounds = result["rounds"]
    epsilon = result["security_parameter"]["value"]
    rate = result["rate_per_round"]
    alpha = result["alpha"]
    # Where the outer alpha search found no alpha with a key (record 0.40.0)
    # the box opens with that, in place of a key length of 0 and its rate.
    if alpha.get("no_positive_key"):
        box = [{
            "lead": "No key",
            "text": ": no \u03b1 the search evaluated gives a positive key length"
                    + ("" if rounds is None
                       else f" from n = {_number(rounds)} rounds")
                    + "; the figures shown are at \u03b1 = "
                    + ("?" if alpha["value"] is None
                       else f"{alpha['value']:.6g}")
                    + ", where the estimate h_low was largest, and the key "
                    "length there is 0",
            "anchor": "result",
        }]
        rate = None
    elif zero is not None:
        # A key length of 0 is no key: said first, and the rate of 0 with it.
        box = [{
            "lead": "No key at these settings",
            "text": ": the key length is \u2113 = 0 bits"
                    + ("" if rounds is None else f" from n = {_number(rounds)} rounds"),
            "anchor": "result",
        }]
        rate = None
    else:
        box = [{
            "lead": f"Key length \u2113 = {_number(result['key_length'])} bits",
            "text": "" if rounds is None else f" from n = {_number(rounds)} rounds",
            "anchor": "result",
        }]
    if rate is not None and rounds is not None:
        box.append({
            "lead": f"Key rate \u2113/n = {rate:.3g} bits per round",
            "text": ", every round counted",
            "anchor": "result",
        })
    terms = result["security_parameter"]["terms"]
    if epsilon is not None:
        # The target the chosen budgets set: ε = ε_PA + ε_EV + 2ε_auth.
        # Each term as it enters ε = ε_PA + ε_EV + 2ε_auth.
        chosen = [f"{symbol} = {factor * float(terms[name]):.3g}"
                  for name, symbol, factor in (("eps_pa", "ε_PA", 1),
                                               ("eps_ev", "ε_EV", 1),
                                               ("eps_auth", "2ε_auth", 2))
                  if isinstance(terms.get(name), int | float)
                  and (name != "eps_auth" or terms[name])]
        box.append({
            "lead": f"Security parameter \u03b5 = {epsilon_text(epsilon)}",
            "text": ", the target you set"
                    + (f" ({', '.join(chosen)})" if chosen else ""),
            "anchor": "guarantee",
        })
    if terms.get("eps_auth") == 0 and _exact(k_auth) == 0:
        # A-AUTH with nothing counted: an idealisation like the device ones.
        box.append({
            "lead": "Free authentication",
            "text": ": the run assumes an authenticated classical channel at no "
                    "cost (\u03b5_auth = 0, k_auth = 0), an idealisation"
                    + (" like the device values" if idealised_devices else ""),
            "anchor": "not-counted",
        })
    if _exact(lambda_ec) == 0 and zero is None:
        # The headline beside lambda_EC = 0 would read as a real code's key
        # length; Not counted's flag says the same in full.
        box.append({
            "lead": "No error-correction cost counted",
            "text": ": \u03bb_EC = 0 as declared, so for a run that sends an "
                    "error-correction transcript this key length is too long",
            "anchor": "not-counted",
        })
    box += [{
        "lead": "One premise" if premises == 1 else f"{premises} premises",
        # Sufficiency, as the guarantee states it: a failed premise voids the
        # guarantee without by itself making the key insecure. A first-order
        # run also needs its computed h_lb <= h_low, which no premise covers
        # (cor:composed-security), so the line names it there.
        "text": " for you to vouch for: the key length and \u03b5 are guaranteed "
                + ("when it holds" if premises == 1 else "when all of them hold")
                + (" and the computed h_lb lies below h_low, which no premise "
                   "covers" if result["reported_tier"] == "first-order" else ""),
        "anchor": "vouch",
    }, {
        "lead": "Model-based",
        "text": ": no measured data analysed; the acceptance test is built around "
                + ("a distribution supplied with the run in place of the "
                   "instance's honest model"
                   if supplied_law else "your honest model's predictions"),
        "anchor": "setup-acceptance",
    }]
    considerations: list[SummaryItem] = []
    if zero is not None:
        considerations.append({
            "text": "No key at these settings. " + zero_key_sentence(zero),
            "pointer": None, "anchor": "levers",
        })
    check = statistics_short(result)
    if check:
        considerations.append({"text": check, "pointer": None, "anchor": "result"})
    gap = (large_gap_sentence(diagnostics or {}, result["reported_tier"])
           if zero is None else None)
    if gap is not None:
        considerations.append({"text": gap, "pointer": None, "anchor": "diagnostics"})
    if evaluated_off and evaluated_off < moved_blocks:
        considerations.append({
            "text": f"On {evaluated_off} of the {moved_blocks} moved measurement "
                    "blocks the key length is computed from your receiver model; "
                    "on the other moved blocks it reads the rounded measurement.",
            "pointer": None, "anchor": "measurement-snaps",
        })
    elif evaluated_off:
        blocks = ("the one moved measurement block" if evaluated_off == 1
                  else f"all {evaluated_off} moved measurement blocks")
        considerations.append({
            "text": f"On {blocks} the key length is computed from your receiver "
                    "model, not from its rounded form, so "
                    + ("that block does" if evaluated_off == 1
                       else "those blocks do")
                    + " not rest on [[A-SNAP]].",
            "pointer": None, "anchor": "measurement-snaps",
        })
    if snap_status is not None:
        considerations.append({
            "text": "Some moved measurement blocks rest on [[A-SNAP]] (effective "
                    f"status {snap_status}): the key length reads the rounded "
                    "measurement there.",
            "pointer": None, "anchor": "measurement-snaps",
        })
    if result["reported_tier"] == "first-order":
        considerations.append({
            "text": "The key length is a first-order number: its bound is computed "
                    "in floating point with no bound on its numerical error, "
                    "which no premise "
                    "covers.",
            "pointer": None, "anchor": "how-computed",
        })
    if result["reported_tier"] == "certified":
        on = result["certified_on"]
        considerations.append({
            # "No premise about numerics" stood beside a count row naming
            # A-LINK and A-RECV under "artefacts ... and its numerics": the
            # certified evaluation adds none; the run's
            # own premises stay (meat-core/frank-wolfe/cor:certified-keylength).
            "text": "The key length is certified: its bound was formed again with "
                    "every arithmetic step exact or rigorously enclosed, so the "
                    "certified evaluation adds no premise about numerics; the "
                    "premises the run lists remain"
                    + ("" if not engine_premises else
                       ", " + _and([f"[[{short_id}]]" for short_id in engine_premises])
                       + (", about artefacts and the engine,"
                          if len(engine_premises) > 1
                          else ", about an artefact or the engine,")
                       + " among them")
                    + (", though on the rounded measurement the solver searched "
                       "rather than on your receiver model"
                       if on is not None and result["certified_fallback"] else "")
                    + ("; it rests on [[A-SNAP]] for some moved measurement blocks"
                       if SNAP_PREMISE in result["certified_premises"] else "")
                    + ".",
            "pointer": None, "anchor": "how-computed",
        })
    return box, considerations


#: A relative gap at or above which a search stopped at its step limit is
#: named in the summary: one percent of the estimate.
LARGE_GAP: Final[float] = 0.01


def large_gap_sentence(
    diagnostics: Mapping[str, Any], tier: str | None = None
) -> str | None:
    """Return the sentence on a step-limited search with a large gap, or ``None``.

    Where the solver stopped at its step limit and its estimate of h_low
    lies at least :data:`LARGE_GAP` (relative) above its first-order bound
    h_lb: more steps may raise the bound and so lengthen the key. On a
    certified run (``tier``) stopping early does not invalidate the key
    length: it makes the bound looser, not invalid
    ([[meat-core/frank-wolfe/thm:firstorder]]). On a first-order run nothing
    more is said than that the guarantee's first-order clause still applies:
    there the computed h_lb is not proved to lie below h_low
    ([[meat-core/frank-wolfe/rem:fo-arithmetic]]). The estimate claims no
    bound, so nothing is said of how much the key would grow.
    """
    if diagnostics.get("solver_status") != "iteration-limit":
        return None
    h_low = _float(diagnostics.get("h_low"))
    h_lb = _float(diagnostics.get("h_lb"))
    if h_low is None or h_lb is None or h_low == 0:
        return None
    relative = (h_low - h_lb) / abs(h_low)
    if relative < LARGE_GAP:
        return None
    steps = diagnostics.get("iterations")
    after = (f" after {steps} steps" if isinstance(steps, int)
             and not isinstance(steps, bool) else "")
    text = (
        f"The solver stopped at its step limit{after} with its estimate of h_low "
        f"above its first-order bound h_lb by a relative gap of {relative:.3g} "
        "((h_low - h_lb) / |h_low|): more steps may raise the bound and lengthen "
        "the key."
    )
    if tier == "certified":
        text += (" Stopping early does not invalidate the key length: it makes "
                 f"the bound looser, not invalid ([[{FIRSTORDER_CLAIM}]]).")
    elif tier == "first-order":
        text += (" The guarantee's first-order clause still applies: the computed "
                 f"h_lb is not proved to lie below h_low ([[{FO_ARITHMETIC_CLAIM}]]).")
    return text


def snap_warning(warning: str) -> SummaryItem:
    """Return a measurement-snap warning as a line of the considerations."""
    return {"text": warning, "pointer": None, "anchor": "measurement-snaps"}


def setup_glance(
    setup: SetupSection, instance: Mapping[str, Any] | None
) -> GlanceItem | None:
    """Return the at-a-glance fragment of the setup, read from the record.

    The protocol (the instance's title), the loss per arm (the honest model's
    transmittances in decibels), the detectors' efficiency, and the expected
    QBER of the honest statistics where the setup's expected statistics hold
    it (as defined there: among the key rounds of the honest raw joint
    distribution, the probability that the key bit differs from the bit the
    other party most likely holds). A part the record does not hold is left
    out; ``None`` without a protocol.
    """
    if not instance:
        return None
    parts: list[str] = []
    source = setup["source"]
    losses = [(name, value) for name, value in
              ({} if source is None else source["honest_parameters"]).items()
              if "transmittance" in name]
    decibels = []
    for _, value in losses:
        found = _exact(value)
        if found is not None and 0 < found <= 1:
            decibels.append(10 * math.log10(1 / float(found)))
    if decibels and len(decibels) == len(losses):
        each = "per arm" if len(decibels) > 1 else "in the channel"
        if max(decibels) - min(decibels) < 1e-9:
            parts.append("no loss" if decibels[0] == 0
                         else f"{decibels[0]:.3g} dB loss {each}")
        else:
            parts.append(f"{min(decibels):.3g} to {max(decibels):.3g} dB loss "
                         f"{each}")
    efficiencies = [found for station in setup["stations"]
                    for detector in station["detectors"]
                    if (found := _exact(detector["parameters"].get("efficiency")))
                    is not None]
    if efficiencies:
        low, high = min(efficiencies), max(efficiencies)
        parts.append(f"detector efficiency {float(low):.4g}" if low == high else
                     f"detector efficiency {float(low):.4g} to {float(high):.4g}")
    qbers = [item["value"] for item in setup["expected"]
             if item["name"].startswith("Expected QBER") and item["value"] is not None]
    if qbers:
        low_q, high_q = min(qbers), max(qbers)
        parts.append(f"expected QBER {low_q:.3g}" if f"{low_q:.3g}" == f"{high_q:.3g}"
                     else f"expected QBER {low_q:.3g} to {high_q:.3g}")
    return {
        "lead": str(instance.get("title") or instance.get("id")),
        "text": "" if not parts else ", " + ", ".join(parts),
        "anchor": "setup",
    }


def tier_note(result: ResultSection, evaluated_off: int = 0) -> str:
    """Return the tier's full sentence, said under "How the number was computed".

    The Key rate considerations hold its short form (:func:`at_a_glance`).
    On a first-order run, the arithmetic no premise covers
    ([[meat-core/frank-wolfe/rem:fo-arithmetic]]) and, where some block was
    evaluated off its snap (``evaluated_off``), that the bound is evaluated at
    the centres of the model's rigorous intervals; on a certified run, the
    re-formed bound and the declaration it is formed on
    (:func:`certified_basis`). Empty where the run reports no key length or
    names no such tier.
    """
    if result["refusal"] is not None or result["key_length"] is None:
        return ""
    if result["reported_tier"] == "first-order":
        return (
            "The key length is computed from the first-order bound in floating "
            "point with no bound on its numerical error, which no premise covers: "
            "it is not a key "
            "length from verified numerics, the first-order tier being weaker "
            "than a verified numerical certificate"
            + (", and where your model is known only through rigorous intervals "
               "the bound is evaluated at their centres" if evaluated_off else "")
            + f" ([[{FO_ARITHMETIC_CLAIM}]])."
        )
    if result["reported_tier"] == "certified":
        return (
            "The key length is certified: the first-order bound was formed again "
            "at the solver's final points from the data of the declaration it is "
            "formed on, every arithmetic step exact or rigorously enclosed, so no "
            "premise about how a number was computed is added; the premises of "
            f"the run remain ([[{CERTIFIED_CLAIM}]], [[{CERTIFIED_SCOPE_CLAIM}]])."
            + certified_basis(result)
        )
    return ""


def refused_numbers(result: ResultSection) -> str:
    """Return what a refused run computed, for How the number was computed.

    No key length was reported. A run refused before the solve formed no
    bound; one refused at the solve may have: the plausibility block's bound
    and estimate (``stages.solve.plausibility``) and the check of the
    statistics' bound on the mismatch (``statistics_consistency``), each
    named where the record holds it.
    """
    refusal = result["refusal"]
    assert refusal is not None
    stage = refusal["stage"]
    order = [str(member) for member in SliceStage]
    if stage in order and stage != str(SliceStage.SOLVE):
        return (f"The run was refused at its {stage} stage, before the solve, so "
                "no key length was reported and no bound was formed. The table "
                "holds what the record states.")
    text = (f"The run was refused at its {stage or 'unknown'} stage, so no key "
            "length was reported.")
    held: list[str] = []
    found = refusal.get("plausibility") or {}
    bound, h_low = _float(found.get("bound")), _float(found.get("h_low"))
    if bound is not None:
        held.append(f"the bound the solve formed, {found.get('bound_name') or 'h'} "
                    f"= {bound:.6g} bits per round"
                    + ("" if h_low is None else
                       f", beside the solver's estimate h_low = {h_low:.6g}"))
    check = result["statistics_check"]
    if check is not None and check["bound"] is not None:
        held.append(f"the check's {check['bound_tier'] or ''} lower bound on the "
                    f"mismatch of the accepted statistics, {check['bound']:.3g}"
                    .replace("  ", " "))
    if stage == str(SliceStage.SOLVE):
        text += (" The record holds " + _and(held) + "." if held
                 else " The record holds no bound.")
    return text + " The table holds what the record states."


def pass_exponent_text(exponent: float) -> str:
    """Return the exponent ``x`` of a cap ``2^-x`` for display, rounded DOWN.

    The cap shown must stay an upper bound on the pass probability, so the
    exponent is never rounded up: from 100000 on, its integer part; below,
    six significant digits toward zero, written positionally (so that the
    HTML sets it as a power).
    """
    if not exponent > 0 or not math.isfinite(exponent):
        raise ValueError(
            f"a pass cap's exponent {exponent!r} is not positive and finite"
        )
    exact = Fraction(exponent)
    if exact >= 100_000:
        return str(math.floor(exact))
    scale = Fraction(10) ** (5 - math.floor(math.log10(exponent)))
    floored = Fraction(math.floor(exact * scale)) / scale
    return _positional(floored)


def _positional(value: Fraction) -> str:
    """Return a terminating decimal fraction written out exactly, no trailing zeros."""
    whole, rest = divmod(value.numerator, value.denominator)
    if rest == 0:
        return str(whole)
    digits = ""
    while rest:
        rest *= 10
        digit, rest = divmod(rest, value.denominator)
        digits += str(digit)
    return f"{whole}.{digits}"


#: The relative and absolute margin taken off ``x log10(2)`` before the
#: decimal of a cap is formed: far above binary64's rounding of that product
#: and of ``10^(1-frac)``, so that the decimal shown is at least the cap.
_DECIMAL_MARGIN: Final[float] = 1e-12


def cap_probability_text(exponent: str) -> str:
    """Return a decimal at least ``2^-x`` for a displayed ``x``, rounded UPWARD.

    Three significant digits; below 0.001, as a mantissa times ``10^-e``.
    Where ``x`` is an integer ``k`` (up to :data:`_EXACT_POWER_LIMIT`), ``2^-k``
    is formed exactly and rounded up (``0.5``, ``0.25``). Otherwise
    ``x log10(2)`` is formed in binary64 and lowered by a margin far above its
    rounding error before the decimal is rounded up, so the value shown is
    never below the cap.
    """
    x = Fraction(exponent)
    if x <= 0:
        return "1"
    if x.denominator == 1 and x <= _EXACT_POWER_LIMIT:
        return _decimal_up(Fraction(1, 2 ** int(x)))
    t = float(x) * math.log10(2.0)
    t_low = t - (abs(t) * _DECIMAL_MARGIN + _DECIMAL_MARGIN)
    if t_low <= 0:
        return "1"
    e = math.floor(t_low)
    mantissa = 10.0 ** (1.0 - (t_low - e)) * (1.0 + _DECIMAL_MARGIN)
    hundredths = math.ceil(mantissa * 100)
    power = e + 1
    if hundredths >= 1000:
        hundredths, power = 100, power - 1
    if power <= 0:
        return "1"
    if power <= 3:
        return _positional(Fraction(hundredths, 100) / 10**power)
    return f"{hundredths // 100}.{hundredths % 100:02d} \u00d7 10^-{power}"


#: The largest integer exponent whose power of two is rounded exactly.
_EXACT_POWER_LIMIT: Final[int] = 10**6


def _decimal_up(value: Fraction) -> str:
    """Return an exact ``value`` in ``(0, 1]`` rounded UP to three digits."""
    if value >= 1:
        return "1"
    power = max(1, math.floor(value.denominator.bit_length() * 0.30103) - 2)
    while value * 10**power >= 10:
        power -= 1
    while value * 10**power < 1:
        power += 1
    hundredths = math.ceil(value * 10**power * 100)
    if hundredths >= 1000:
        hundredths, power = 100, power - 1
    if power <= 3:
        return _positional(Fraction(hundredths, 100) / 10**power)
    return f"{hundredths // 100}.{hundredths % 100:02d} \u00d7 10^-{power}"


def cap_text(exponent: float) -> str:
    """Return the cap as a probability: ``2^-x ≈ d``, both rounded upward."""
    shown = pass_exponent_text(exponent)
    return f"2^-{shown} ≈ {cap_probability_text(shown)}"


#: How item (iv) decided, where it refused, in the report's words.
_REFUSAL_DECISION_WORDS: Final[Mapping[str, str]] = {
    "exact": "decided on the exact value, so a displayed value a little above "
             "the threshold is the upward rounding",
    "enclosure": "decided on the exact value against a rigorous enclosure of "
                 "the threshold, so a displayed value a little above it is the "
                 "upward rounding",
    "undecided": "the exact value lies too close to the threshold for the "
                 "comparison to be decided either way, and an undecided "
                 "comparison refuses",
}


def pass_cap_sentence(result: ResultSection) -> str:
    """Return the cap on how often devices as declared pass the test, or ``""``.

    ``meat-core/req:unreachable-acceptance-set`` (iv), (v) and
    ``meat-core/prop:model-pass-bound`` (ii): where the record carries ``x``
    (``b > 0``), devices the declaration the run searches admits, run so
    that each round's acceptance value given the earlier ones follows the
    statistics of a feasible state, pass with probability at most ``2^-x``.
    The cap is shown as a probability (``2^-x`` and a decimal, both rounded
    upward), with the tier of ``b``, ``tau`` and whether the run was refused,
    as the record carries that decision; never as bits. The reading of a
    real pass is graded by the cap and never a proof, and does not apply to
    an acceptance set built from the run's own frequencies (the claim's
    ``user_statement``). Empty where there is none.
    """
    check = result["statistics_check"]
    exponent = None if check is None else check["model_pass_exponent_bits"]
    if check is None or exponent is None or not exponent > 0:
        return ""
    tier = check["model_pass_exponent_tier"] or check["bound_tier"]
    tau = check["min_model_pass_probability"]
    if check["refused"] and check["model_pass_decision"] == "undecided":
        verdict = (
            " This is not shown to exceed your threshold "
            f"min_model_pass_probability = {tau} "
            f"({_REFUSAL_DECISION_WORDS['undecided']}), so the run is refused "
            "and reports no key length."
        )
    elif check["refused"]:
        decision = _REFUSAL_DECISION_WORDS.get(
            str(check["model_pass_decision"]), "decided on the exact value"
        )
        verdict = (
            f" This is at most your threshold min_model_pass_probability = {tau} "
            f"({decision}), so the run is refused and reports no key length."
        )
    else:
        verdict = (
            f" This is above your threshold min_model_pass_probability = {tau}, "
            "so the check does not refuse the run."
        )
    searched = (
        " (in the rounded form the solver searched; the run also evaluated a "
        "refined form of your receiver model, the reference companion, and "
        "this cap is not shown to hold for it)"
        if check["companion_admitted"]
        else ""
    )
    return (
        f" Devices that behave as your declared model says{searched} pass this "
        "acceptance test with probability at most "
        f"{cap_text(exponent)} (both rounded upward; {tier} bound; "
        f"[[{MODEL_PASS_CLAIM}]]), where in every round the acceptance value, "
        "given the earlier rounds, follows the statistics of a state the model "
        "admits." + verdict + " This is about the model, not your real "
        "devices: if they pass a test fixed before the run, that is evidence "
        "against the model only at the level of this cap, the stronger the "
        "smaller the cap, and not a proof. An acceptance set built from the "
        "same run's frequencies passes by construction, so no such reading "
        "applies to it."
    )


def statistics_refusal(result: ResultSection) -> str:
    """Return a run refused under item (iv), in the considerations' words."""
    return (
        "The accepted statistics were checked against your declared model: no "
        "state it admits has per-round statistics that the acceptance test "
        f"accepts ([[{UNREACHABLE_CLAIM}]], [[{MINIMAL_DIVERGENCE_CLAIM}]])."
        + pass_cap_sentence(result)
    )


#: Why a run is not checked, in words.
_UNCHECKED_WORDS: Final[Mapping[str, str]] = {
    "out_of_scope": "its statistics are your honest model's predictions for your "
                    "declared devices and you declared no constraint entry",
    "opted_out": "you switched the check off (statistics_check off)",
}


def statistics_short(result: ResultSection) -> str:
    """Return the at-a-glance form of :func:`statistics_sentence`, or ``""``.

    One plain sentence: whether the statistics were checked and what was
    found; the claims, the bound's tier and the threshold are in the result
    paragraph, which says :func:`statistics_sentence` in full.
    """
    check = result["statistics_check"]
    if check is None:
        return ""
    if not check["checked"]:
        return (
            "The accepted statistics were not checked against your declared "
            "model, so that a state your declared devices admit can produce them "
            f"([[{REACH_PREMISE}]]) is yours to vouch for."
        )
    exponent = check["model_pass_exponent_bits"]
    if check["bound"] is None:
        return (
            "The accepted statistics were checked against your declared model, "
            "but no bound on a mismatch was formed, so there is no cap on how "
            "often devices as declared pass the test."
        )
    if exponent is None or not exponent > 0:
        return (
            "The accepted statistics were checked against your declared model, "
            "and no mismatch is proven."
        )
    return (
        "Devices that behave as your declared model says pass the acceptance "
        f"test with probability at most {cap_text(exponent)} (rounded upward), "
        "above your threshold of "
        f"{check['min_model_pass_probability']}."
    )


def statistics_sentence(result: ResultSection) -> str:
    """Return what the check of the statistics found, beside a key length (0.26.0).

    ``meat-core/req:unreachable-acceptance-set`` (v): beside each key length
    the report shows the cap on the probability that devices as declared pass
    the acceptance test (:func:`pass_cap_sentence`), or that there is none and
    why (no mismatch proven, or no bound formed and the reason); on a run that
    is not checked, why not, with A-REACH named as the caller's to vouch for.
    It shows no number of bits and no share. Empty on an older record.
    """
    check = result["statistics_check"]
    if check is None:
        return ""
    claim = f"[[{UNREACHABLE_CLAIM}]]"
    if not check["checked"]:
        why = _UNCHECKED_WORDS.get(
            str(check["unchecked_reason"]), str(check["unchecked_reason"])
        )
        return (
            "The accepted statistics were not checked against your declared "
            f"model ({why}; {claim}): that a state your declared devices admit "
            f"can produce them, [[{REACH_PREMISE}]], is yours to vouch for."
        )
    if check["bound"] is None:
        return (
            "The accepted statistics were checked against your declared model, "
            "but no bound on their mismatch was formed ("
            + str(check["no_bound_reason"] or "no reason recorded")
            + f"; {claim}), so a mismatch is neither proven nor ruled out, there "
            "is no cap on how often devices as declared pass the test, and the "
            "check refuses nothing."
        )
    # Whether a mismatch is proven is the bound's sign.
    if check["bound"] <= 0 or check["model_pass_exponent_bits"] is None:
        return (
            "The accepted statistics were checked against your declared model "
            f"({claim}): no mismatch is proven (the {check['bound_tier']} lower "
            "bound on it is not positive), so there is no cap on how often "
            "devices as declared pass the test, and the check refuses nothing."
        )
    return (
        "The accepted statistics were checked against your declared model "
        f"({claim}, [[{MINIMAL_DIVERGENCE_CLAIM}]]): no state your declared "
        "devices admit has per-round statistics the test accepts "
        f"({check['bound_tier']} bound)." + pass_cap_sentence(result)
    )


def certified_basis(result: ResultSection) -> str:
    """Return which declaration a certified number is formed on, and its premise.

    ``meat-core/frank-wolfe/req:certified-evaluation`` (i), (vi), (ix), from
    the record (report 0.22.0): on the reference companion, built from the
    receiver model on every block its intervals were handed for (and from the
    rounded measurement on any other, which the premise then names); in the
    FALLBACK, the rounded measurement the solver searched,
    the bound on the receiver model having certified none of the points it was
    formed at (the search's and the polish's,
    ``meat-core/frank-wolfe/req:bracket-on-reference`` (i)),
    recorded beside it and combined with nothing; otherwise the declaration
    the solver searched. A-SNAP is named where the record's ``premises``
    names it. Empty on an older record, which names no declaration.
    """
    on = result["certified_on"]
    if on is None:
        return ""
    if result["certified_fallback"]:
        text = (
            " It is formed on the rounded measurement the solver searched, not on "
            "your receiver model: the rigorous re-evaluation on your model "
            "certified none of the points it was re-evaluated at, so it was made "
            "once more on the rounded measurement; the first-order bound on your "
            "model "
            "is recorded beside it and no number is formed from the two together "
            f"([[{CERTIFIED_EVALUATION_CLAIM}]])"
        )
    elif on == "reference_companion":
        text = (
            " It is formed on the reference companion: the declaration built "
            "from your receiver model, through the model's rigorous intervals, "
            "on every block the run handed those intervals for"
        )
    else:
        text = " It is formed on the declaration the solver searched"
    if SNAP_PREMISE in result["certified_premises"]:
        text += (
            "; it rests on [[A-SNAP]] for the moved measurement blocks the record "
            "lists there"
        )
    return text + "."


#: What one round sends, by whether the source is trusted: the per-round
#: rate is then also a rate per signal (setup.py's source step says the same).
PER_ROUND_WORDS: Final[Mapping[bool, str]] = {
    True: "each round sends one signal, so this is also the rate per signal sent",
    False: "in each round the untrusted source delivers one system to each "
           "station",
}


def result_sentence(
    result: ResultSection, trusted_source: bool | None = None,
    *, zero: ZeroKey | None = None, document: bool = False,
) -> str:
    """Return the summary's result paragraph, values woven in.

    The rate is defined where it is first given: the key length over every
    round of the run, the rounds that give no raw key bit included, and, by
    the source mode (``trusted_source``), what one round sends. What consumes
    key, the authentication's pre-shared key included, is :func:`costs`. A
    key length of 0 (``zero``) is said as no key, with its cause; a refusal
    of a run lowered from a protocol document (``document``) ends with what
    the document can change (:data:`DOCUMENT_HINTS`).
    """
    refusal = result["refusal"]
    rounds = result["rounds"]
    if refusal is not None:
        text = (
            f"The run was refused at its {refusal['stage'] or 'unknown'} stage"
            + ("" if refusal["reason"] is None else f" ({refusal['reason']})")
            + ", so no key length was computed and nothing is certified."
        )
        if refusal["detail"]:
            text += f" Why: {refusal['detail']}"
            text += "" if str(refusal["detail"]).endswith(".") else "."
        if refusal["rule"]:
            text += f" What the engine requires: {refusal['rule']}"
            text += "" if str(refusal["rule"]).endswith(".") else "."
        hint = DOCUMENT_HINTS.get(str(refusal["reason"])) if document else None
        if hint is not None:
            text += " " + hint
        return text
    if result["key_length"] is None:
        reason = result["reason_text"] or result["key_length_reason"] or ""
        return (
            "The run completed but reports no key length"
            + ("" if rounds is None else f" for n = {_number(rounds)} rounds")
            + (f": {reason}" if reason else ".")
        )
    rate = result["rate_per_round"]
    security = result["security_parameter"]
    no_key = result["alpha"].get("no_positive_key")
    if no_key:
        # The outer alpha search found no alpha with a key (record 0.40.0):
        # said first, before any figure of the one run shown.
        text = (
            "No key: the protocol outputs no key"
            + ("" if rounds is None else f" from n = {_number(rounds)} rounds")
            + ". " + no_key
            + ("" if no_key.endswith(".") else ".")
            + " The figures shown are those of the alpha with the largest "
            f"estimate h_low (\u03b1 = {result['alpha']['value']:.6g}), whose key "
            "length is 0; h_low is an estimate, never a key."
        )
        check = statistics_sentence(result)
        return text + (" " + check if check else "")
    if zero is not None:
        # A key of 0 bits is no key: no "outputs a key", no rate and no ε of
        # a key, and the cause the record states said first.
        text = (
            "No key at these settings: "
            + (f"from n = {_number(rounds)} rounds " if rounds is not None else "")
            + "the key length is \u2113 = 0 bits. " + zero_key_sentence(zero)
        )
    else:
        text = _key_sentence(result, rounds, rate, security, trusted_source)
    check = statistics_sentence(result)
    if check:
        text += " " + check
    return text + _tier_sentence(result)


def _key_sentence(
    result: ResultSection, rounds: int | None, rate: float | None,
    security: Mapping[str, Any], trusted_source: bool | None,
) -> str:
    """Return the key length, its rate and its ε, as the result first says them."""
    text = (
        (f"From n = {_number(rounds)} rounds the protocol" if rounds is not None
         else "The protocol")
        + f", unless it aborts, outputs a key of \u2113 = "
        f"{_number(result['key_length'])} bits"
        + ("" if rate is None else (
            f": a key rate of {rate:.3g} bits per round, \u2113 divided by all n "
            "rounds, the rounds that give no raw key bit included"
            # "Every round" already says what one round is on an untrusted
            # run; a trusted source's round is also one signal sent.
            + ("" if trusted_source is not True
               else f" ({PER_ROUND_WORDS[trusted_source]})")
        ))
        + "."
    )
    if security["value"] is not None:
        text += (
            f" Its security parameter is ε = {security['value']:.3g}."
        )
    return text


def _tier_sentence(result: ResultSection) -> str:
    """Return what the key length rests on, by its reported tier, or ``""``."""
    text = ""
    if result["reported_tier"] == "first-order":
        text += (
            " The key length rests on the solver's first-order bound h_lb, a "
            "lower bound on h_low, the attacker's worst-case uncertainty per "
            "round about the raw key; it does not rest on the solver's estimate "
            "of h_low. The bound's proof is exact, and the minima it uses are "
            "bounded from below in exact arithmetic, not taken from the solver. "
            "Its objective and gradient, though, are computed in floating point "
            "with no bound on their numerical error, so the computed h_lb is not "
            "proved to lie below h_low ([[" + FIRSTORDER_CLAIM + "]], [["
            + FO_ARITHMETIC_CLAIM + "]])."
        )
    if result["reported_tier"] == "certified":
        # Three short sentences in place of one (the stage-9 readers' "long
        # certified sentences"); nothing is dropped.
        text += (
            " The key length rests on a certified lower bound, h_cert, on the "
            "attacker's worst-case uncertainty per round about the raw key. "
            "h_cert is the solver's first-order bound formed again at its final "
            "points, from the data of the declaration it is formed on, with "
            "every arithmetic step exact or rigorously enclosed. It lies below "
            "that declaration's value by the claims alone, and the key length "
            "is computed from it exactly ([[" + CERTIFIED_CLAIM
            + "]], [[" + CERTIFIED_SCOPE_CLAIM + "]])."
            + certified_basis(result)
        )
    return text


def _bits(value: float) -> str:
    """Return a number of bits: whole where it is (to rounding), else one decimal."""
    if abs(value - round(value)) < 1e-6:
        return f"{round(value):,}"
    return f"{value:,.1f}"


def _deduction_lines(found: Deductions) -> list[str]:
    """Return the record's post-processing deductions, one line each."""
    lines: list[str] = []
    if found["error_correction"] is not None:
        lines.append(f"Less {_bits(found['error_correction'])} bits that error "
                     "correction reveals (λ_EC, as declared).")
    if found["error_verification"] is not None:
        lines.append(f"Less a {_bits(found['error_verification'])}-bit hash for "
                     "error verification (⌈log₂(1/ε_EV)⌉).")
    if found["privacy_amplification"] is not None:
        lines.append(f"Less {_bits(found['privacy_amplification'])} bits that "
                     "privacy amplification costs for a finite key "
                     "(\u03b1/(\u03b1\u22121)·log₂(1/ε_PA)).")
    penalty = found["hash_penalty"]
    if penalty:
        lines.append(f"Less a further {_bits(penalty)} bit(s), since the "
                     "privacy-amplification family is only two-universal, not "
                     f"ideal ([[{HASH_PENALTY_CLAIM}]]).")
    added = found["added_back"]
    if added:
        lines.append(
            ("Plus one bit" if added == 1 else f"Plus {_bits(added)} bits")
            + ", a constant of the bound: its source's derivation adds two, and "
            "one of them pays for announcing whether error verification passed "
            f"([[{PLUS_ONE_CLAIM}]])."
        )
    return lines


#: The lead of the costs list (:func:`costs`), with the theorem it reads.
COSTS_LEAD: Final[str] = (
    f"From the accumulated entropy to the key you gain ([[{KEYLENGTH_CLAIM}]]):"
)


def costs(
    result: ResultSection, k_auth: Any = None,
    entropy: tuple[str, float] | None = None,
) -> list[str]:
    """Return what consumes key and what remains, one line each, or ``[]``.

    The list adds up (``meat-core/thm:keylength``, Eq. ``eq:keylength``):
    the accumulated entropy n·h, ``entropy`` being the number the key length
    is computed from with its symbol (h_lb, or h_cert on a certified run);
    less the record's deductions, term by term, each named before its symbol
    (the lambda_EC bits of error correction, the verification hash, the
    finite-size term of privacy amplification, ``meat-core/req:hash-penalty``
    where the hash is only two-universal); plus the bound's constant one bit
    (``meat-core/rem:plus2``); rounded down to the key length; then the
    pre-shared key the authentication consumes (``k_auth``, the declared
    input) and the net key the record states. Read, never computed, but for
    the product n·h.
    """
    found: Deductions | None = result["deductions"]
    key_length = result["key_length"]
    if key_length is None:
        return []
    rounds = result["rounds"]
    lines: list[str] = []
    total: float | None = None
    if entropy is not None and rounds is not None:
        symbol, value = entropy
        total = rounds * max(value, 0.0)
        # A lower bound on the entropy, not the entropy; a first-order h_lb is
        # the computed number, not proved to lie below h_low, so it is not
        # called a bound on the entropy.
        first_order = symbol == "h_lb"
        lines.append(
            ("The accumulated entropy as the computed first-order bound "
             "gives it, n·h_lb"
             if first_order else
             f"The accumulated entropy, bounded below by n·{symbol}")
            + f" \u2248 {_bits(total)} bits ("
            + ("not proved to lie below n·h_low; " if first_order else "")
            + f"n = {_number(rounds)} rounds, "
            f"{symbol} = {value:.6g} bits per round"
            + (", clamped at 0" if value < 0 else "") + ")."
        )
    # A record before the deductions gives the key length and the net key only.
    lines += [] if found is None else _deduction_lines(found)
    if total is not None and found is not None:
        total -= sum(found[name] or 0.0 for name in (
            "error_correction", "error_verification", "privacy_amplification",
            "hash_penalty"))
        total += found["added_back"] or 0.0
    # The key length is max(0, floor(...)): clamped where the sum is negative.
    clamped = key_length == 0 and total is not None and math.floor(total) < 0
    lines.append(
        "Rounded down to a whole bit"
        + (" and clamped at 0" if clamped else "")
        + f", the key length is \u2113 = {_number(key_length)} bits."
    )
    if k_auth is not None:
        lines.append(f"Authentication consumes k_auth = {_number(k_auth)} bits of "
                     "pre-shared key per run (declared); an aborted run may "
                     "consume as many.")
    net = result["net_key_length"]
    if net is not None:
        lines.append(f"You gain \u2113 \u2212 k_auth = {_number(net)} bits.")
    return lines


def guarantee_terms(result: ResultSection) -> list[GuaranteeTerm]:
    """Return the ε table beneath the guarantee: ε and its three terms."""
    security = result["security_parameter"]
    terms = security["terms"]

    def value(name: str) -> float | None:
        found = terms.get(name)
        return float(found) if isinstance(found, int | float) else None

    return [
        {"symbol": "ε", "value": security["value"],
         "meaning": "the run's security parameter, ε_PA + ε_EV + 2ε_auth"},
        {"symbol": "ε_PA", "value": value("eps_pa"),
         "meaning": "secrecy error: how far the key may be from uniformly random "
                    "and independent of the attacker"},
        {"symbol": "ε_EV", "value": value("eps_ev"),
         "meaning": "a bound on the chance that both parties accept with "
                    "different keys"},
        {"symbol": "ε_auth", "value": value("eps_auth"),
         "meaning": "authentication error, counted twice in ε, including, for a "
                    "key from an earlier run, its distance from an ideal key"},
    ]


_ROUTE_SHORT: Final[Mapping[str, str]] = {
    "element-graph": "an optical element graph",
    "port-grams": "declared port Grams",
    "instrument-matrix": "a declared instrument matrix",
    "declared-finite-povm": "a declared POVM",
}


def _input(inputs: Sequence[InputRow], *names: str) -> Any:
    for row in inputs:
        if row["name"] in names:
            return row["value"]
    return None


def _analysed_text(inputs: Sequence[InputRow], name: str) -> str | None:
    """Return the value the run analysed, with the requested one where it differs.

    A preparation may replace a requested value (``device.test_fraction`` 1/10
    becomes 205/2048 on a 2^-11 grid); the report states the prepared value,
    the one the key length rests on, and the request beside it.
    """
    row = next((row for row in inputs if row["name"] == name), None)
    if row is None or row["value"] is None:
        return None
    prepared = row["prepared"]
    if prepared is None or same_number(prepared, row["value"]):
        return exact_with_decimal(row["value"] if prepared is None else prepared)
    return analysed_words(prepared, row["value"])


def setup_brief(
    setup: SetupSection, inputs: Sequence[InputRow], instance: Mapping[str, Any] | None
) -> list[str]:
    """Return "Your setup in brief": one short sentence per part."""
    lines: list[str] = []
    source = setup["source"]
    if instance:
        line = f"Protocol: {instance.get('title') or instance.get('id')}"
        if source is not None and source["trusted"] is False:
            # The proof uses no model of what the source
            # delivers, but A-LAB and A-MODES exclude what else may reach a
            # station from it (meat-core/thm:accumulated-entropy's mapping of
            # physical attacks rests on A-LAB at both parties).
            line += (
                ", with an untrusted source (the proof uses no model of the "
                "source: whatever it delivers into the stations' declared input "
                "modes is treated as prepared by the attacker; that nothing else "
                "from it reaches a station, such as a clock or trigger line, pump "
                "light or light in an undeclared mode, is part of [[A-LAB]] and "
                "[[A-MODES]] under What you vouch for)"
            )
        elif source is not None and source["trusted"] is True:
            line += ", with a trusted source"
        lines.append(line + ".")
    if source is not None:
        mode = source["mode"] or "mode not recorded"
        trust = {True: "trusted", False: "untrusted"}.get(source["trusted"])  # type: ignore[arg-type]
        model = source["honest_model"]
        # A model whose own name says it is an honest one (a document's
        # "honest acceptance table ...") is not prefixed again (m10).
        lines.append(
            f"Source: {mode}"
            + ("" if trust is None or trust == mode else f" ({trust})")
            + ("" if model is None
               else f"; {model}" if str(model).lower().startswith("honest ")
               else f"; honest model {model}")
            + "."
        )
        channel = _channel(source["honest_parameters"])
        if channel:
            lines.append("Channel: " + channel + ".")
    for station in setup["stations"]:
        parts = [_ROUTE_SHORT.get(station["route"] or "", "a receiver")]
        if station["elements"]:
            parts.append(f"{len(station['elements'])} optical elements")
        if station["detectors"]:
            parts.append(f"{len(station['detectors'])} detectors"
                         + _detector_words(station["detectors"]))
        if station["photon_cutoff"] is not None:
            parts.append(f"photon cutoff N = {station['photon_cutoff']}")
        lines.append(f"{station['name'].capitalize()}: " + ", ".join(parts) + ".")
    rounds = _input(inputs, "rounds")
    fraction = _analysed_text(inputs, "device.test_fraction")
    bases = _input(inputs, "device.key_bases")
    run = [] if rounds is None else [f"n = {_number(rounds)} rounds"]
    if fraction is not None:
        run.append(f"test fraction {fraction}")
    if bases is not None:
        run.append(f"key bases {bases}")
    if run:
        lines.append("Run: " + ", ".join(run) + ".")
    return lines


#: The detector parameters the brief summarises, as the setup names them
#: (setup.py's ``_DETECTOR_WORDS``), and how the brief says them.
_DETECTOR_BRIEF: Final[tuple[tuple[str, str], ...]] = (
    ("efficiency", "detection efficiency"),
    ("dark-click probability per round", "dark-click probability per round"),
)


def _detector_words(detectors: Sequence[Mapping[str, Any]]) -> str:
    """Return a station's detector efficiency and dark counts in short, or ``""``.

    `` (detection efficiency 0.8, dark-click probability per round 1e-06)``;
    a range where the detectors differ. The table under the station has
    each detector's own values.
    """
    words: list[str] = []
    for name, label in _DETECTOR_BRIEF:
        values = [found for detector in detectors
                  if (found := _exact(detector["parameters"].get(name))) is not None]
        if not values:
            continue
        low, high = min(values), max(values)
        words.append(f"{label} {float(low):.4g}" if low == high
                     else f"{label} {float(low):.4g} to {float(high):.4g}")
    return f" ({', '.join(words)})" if words else ""


_ARM_OWNERS: Final[tuple[tuple[str, str], ...]] = (
    ("alice_", "Alice's"), ("bob_", "Bob's"),
)


def _loss(value: Any) -> str:
    """Return a transmittance with its loss in decibels: ``0.5 (3.01 dB loss)``."""
    found = _exact(value)
    if found is None or not 0 < found <= 1:
        return str(value)
    decibels = 10 * math.log10(1 / float(found))
    return (f"{float(found):.4g} ("
            + ("no loss" if found == 1 else f"{decibels:.3g} dB loss") + ")")


def _channel(parameters: Mapping[str, Any]) -> str:
    """Return the honest model's transmittances in words, arms by party."""
    parts: list[str] = []
    for name, value in parameters.items():
        if "transmittance" not in name:
            continue
        owner = next((words for prefix, words in _ARM_OWNERS
                      if name.startswith(prefix)), None)
        if owner is None:
            parts.append(f"transmittance {_loss(value)}")
        elif not any("arm transmittance" in part for part in parts):
            parts.append(f"{owner} arm transmittance {_loss(value)}")
        else:
            parts.append(f"{owner} {_loss(value)}")
    return ", ".join(parts)


#: The limitations whose reading the guarantee already quotes (E5: the
#: completeness paragraph appeared three times on one page).
QUOTED_LIMITATIONS: Final[tuple[str, ...]] = (COMPLETENESS_CLAIM, PER_EXECUTION_CLAIM)

#: A parameter's name in words where its readable label does not serve
#: (``model.qber`` reads "Qber"), by the last segment of its name.
_PARAMETER_WORDS: Final[Mapping[str, str]] = {"qber": "QBER"}


def _parameter_words(row: InputRow) -> str:
    """Return an input's readable label inside a sentence.

    A possessive first word ("Alice's transmittance") and an acronym stay as
    they are; an ordinary capitalised first word is lowered ("visibility").
    """
    name = row["name"].rsplit(".", 1)[-1]
    if name in _PARAMETER_WORDS:
        return _PARAMETER_WORDS[name]
    label = row["label"] or name
    first = label.split(" ", 1)[0]
    if first.endswith("'s") or not label[1:2].islower():
        return label
    return label[:1].lower() + label[1:]


def _ideal_label(row: InputRow) -> str | None:
    """Return the ideal extreme a row's value is at (:data:`_IDEAL_KINDS`), or None."""
    name = row["name"].rsplit(".", 1)[-1]
    value = row["value"] if row["prepared"] is None else row["prepared"]
    for label, quantities, word, ideal in _IDEAL_KINDS:
        kind = (row["quantity"] in quantities) if quantities else False
        named = name == word or name.endswith(f"_{word}")
        if (kind or named) and _at_extreme(value, ideal):
            return label
    return None


def expected_basis(
    inputs: Sequence[InputRow], model: str | None, supplied_law: bool,
    detectors: bool = False,
) -> str:
    """Return which model the expected statistics come from, one sentence.

    Mechanical, from the record only (no physics of a model is written here):
    a distribution supplied in place of the honest model (``supplied_law``)
    is as the caller declared it; otherwise the honest model the record names
    (``honest_model_note.model``) and the parameters it was evaluated with,
    read from the inputs of section ``model``: those not at an ideal extreme
    by name and value, then those at one by that extreme, as the declared
    stations record them (``detectors``: their detector efficiencies, dark
    counts and settings). A parameter the inputs mark as having no effect is
    left out. Empty where the record names no honest model. With a supplied
    distribution the record does not say where its raw joint distribution, the
    statistics' source, came from, so the sentence says only that the two need
    not agree.
    """
    if supplied_law:
        return (
            "These statistics come from the record's honest raw joint "
            "distribution; the acceptance test is built around a distribution "
            "supplied with the run in place of the instance's honest model, so "
            "the two need not agree."
        )
    if not model:
        return ""
    named = model if model.replace("_", "").replace("-", "").isalnum() else f'"{model}"'
    shown: list[str] = []
    ideal: list[str] = []
    for row in inputs:
        if row["section"] != "model" or row["value"] is None or row["not_used"]:
            continue
        at = _ideal_label(row)
        if at is not None:
            if at not in ideal:
                ideal.append(at)
            continue
        value = _analysed_text(inputs, row["name"])
        if value is not None:
            shown.append(f"{_parameter_words(row)} {value}")
    text = f"These statistics are expected from the honest model {named}"
    extremes = f"at their ideal values ({', '.join(ideal)})"
    if shown:
        text += f", evaluated with {_and(shown)}"
        if ideal:
            text += f" and its other parameters {extremes}"
    elif ideal:
        text += f", evaluated with its parameters {extremes}"
    return text + (
        ", as your declared stations record them (with their detector "
        "efficiencies, dark counts and settings; see the stations above)."
        if detectors else
        ", as your declared stations record them (see the stations above)."
    )


#: THE LEAD OF "Choices that could lengthen the key". WHY: "What would change
#: the number" read as a list of everything that moves the key length; these
#: are the run's own settings, and the reader must learn that the device
#: values move it too.
LEVERS_LEAD: Final[str] = (
    "These are run settings that change \u2113 without changing your devices or "
    "the security statement. Your device values change it too; a sweep over them "
    "shows how."
)

#: The lead where a measurement-snap fix is listed: that fix changes which
#: premises the key length rests on as well as its length.
LEVERS_SNAP: Final[str] = (
    "The settings below other than a measurement-snap fix change \u2113 without "
    "changing your devices or the security statement; a measurement-snap fix "
    "changes which premises the key length rests on (A-SNAP) as well. Your device "
    "values change \u2113 too; a sweep over them shows how."
)


def not_counted(
    result: ResultSection,
    limitations: Sequence[Mapping[str, Any]],
    engaged: Mapping[str, AssumptionEntry],
    snaps: MeasurementSnaps | None,
) -> list[SummaryItem]:
    """Return what the key length does not count, one plain sentence each.

    First what a lab asks first: that a measured value's
    error bar is not covered (A-EXACT or A-IDEAL, A-ENS, A-WCP, where the run
    rests on them), and on a
    first-order run that the bound's numerical error is unbounded. Then the
    zero-default flags with their own texts; each limitation's summary (the
    claim's own text) with its link, except those the guarantee quotes,
    which one line points to (E5); and the snap's warnings.
    """
    items: list[SummaryItem] = []
    # Every exactness premise the run engages, the receiver's (A-EXACT, or on
    # the Band-A route A-IDEAL's ideal qubit measurement) and the source's
    # (A-ENS states, A-WCP intensities).
    exact = [short_id for short_id in ("A-EXACT", "A-IDEAL", "A-ENS", "A-WCP")
             if short_id in engaged]
    if exact:
        items.append({
            "text": "A measured value with an error bar is not covered: the result "
                    "applies to the exact declared values ("
                    + ", ".join(f"[[{short_id}]]" for short_id in exact) + ").",
            "pointer": None, "anchor": None,
        })
    if result["reported_tier"] == "first-order":
        items.append({
            "text": "The first-order bound's objective and gradient are "
                    "computed in floating point with no bound on their numerical "
                    "error "
                    f"([[{FO_ARITHMETIC_CLAIM}]]).",
            "pointer": None, "anchor": "how-computed",
        })
    items += [
        {"text": flag["text"] + " (" + ", ".join(
            f"[[{short_id}]]" for short_id in flag["assumptions"]) + ")",
         "pointer": None, "anchor": None}
        for flag in result["not_counted"]
    ]
    quoted = [claim for claim in limitations if claim["id"] in QUOTED_LIMITATIONS]
    for claim in limitations:
        if claim["id"] not in QUOTED_LIMITATIONS:
            items.append({"text": f"{claim['summary']} ([[{claim['id']}]])",
                          "pointer": None, "anchor": None})
    if quoted:
        items.append({
            "text": "What ε covers per execution, and what the completeness figure "
                    "does and does not bound, are not repeated here.",
            "pointer": None, "anchor": "guarantee",
        })
    if snaps is not None:
        tail = " ([[A-SNAP]])" if snaps["rests_on_a_snap"] else ""
        shown = snaps["warnings"] or (
            snaps["sentences"][:1] if snaps["rests_on_a_snap"] else []
        )
        for warning in shown:
            items.append({"text": warning + tail, "pointer": None, "anchor": None})
    return items


def levers(
    result: ResultSection,
    inputs: Sequence[InputRow],
    snaps: MeasurementSnaps | None,
    zero: ZeroKey | None = None,
) -> list[SummaryItem]:
    """Return the run-level levers the record names.

    On a key length of 0 (``zero``) also the solver's step limit, where the
    search stopped there with a gap larger than the shortfall, and the rounds
    n, where n times the per-round number is below the bits the key length
    deducts (:func:`zero_key_levers`).
    """
    items: list[SummaryItem] = zero_key_levers(zero, inputs) if zero else []
    if snaps is not None:
        fixes = list(dict.fromkeys(
            str(block["group_fix"]) for block in snaps["blocks"]
            if block["rests_on_assumption"] and block["group_fix"]
        ))
        for fix in fixes:
            items.append({
                "text": "Measurement snap: blocks rest on [[A-SNAP]]; the record "
                        f"names this fix: {fix}.",
                "pointer": None, "anchor": None,
            })
    lambda_ec = _input(inputs, "parameters.lambda_ec")
    if (
        isinstance(lambda_ec, int | float) and not isinstance(lambda_ec, bool)
        and lambda_ec > 0
    ):
        items.append({
            "text": f"Error correction: λ_EC = {_number(lambda_ec)} bits is deducted "
                    "from the key in full, so a code that leaks fewer bits (declared "
                    "as a smaller λ_EC) lengthens the key by as many bits "
                    f"([[{KEYLENGTH_CLAIM}]]).",
            "pointer": "/payload/config/parameters/lambda_ec", "anchor": None,
        })
    alpha = result["alpha"]
    if alpha.get("no_positive_key") and alpha["value"] is not None:
        span = alpha["searched_range"]
        items.append({
            "text": "Rényi order: no \u03b1 the search on the honest model "
                    "evaluated"
                    + ("" if span is None else
                       f" over [{span[0]:.6g}, {span[1]:.6g}]")
                    + " gives a key, so none was chosen; the figures shown are "
                    f"at \u03b1 = {alpha['value']:.6g}, where the estimate h_low "
                    f"was largest ([[{KEYLENGTH_CLAIM}]]).",
            "pointer": alpha["pointer"], "anchor": None,
        })
    elif alpha["chosen_by"] == "outer-search" and alpha["value"] is not None:
        span = alpha["searched_range"]
        items.append({
            "text": f"Rényi order: \u03b1 = {alpha['value']:.6g} was chosen by a "
                    "search on the honest model before the run"
                    + ("" if span is None else
                       f" over [{span[0]:.6g}, {span[1]:.6g}]")
                    + "; \u03b1 changes only the key's length, never its secrecy, "
                    "and a different search range may find a different key length "
                    f"([[{KEYLENGTH_CLAIM}]]).",
            "pointer": alpha["pointer"], "anchor": None,
        })
    elif alpha["value"] is not None:
        items.append({
            "text": "Rényi order: the key length was computed at \u03b1 = "
                    f"{alpha['value']:.6g}; any \u03b1 in (1, 2) fixed before the "
                    "run is valid and changes only the key's length, so the opt-in "
                    "\u03b1 search may find a longer key "
                    f"([[{KEYLENGTH_CLAIM}]]).",
            "pointer": alpha["pointer"], "anchor": None,
        })
    return items


def zero_key_levers(zero: ZeroKey, inputs: Sequence[InputRow]) -> list[SummaryItem]:
    """Return the step limit and the rounds as levers on a key length of 0.

    The step limit where the solver stopped there with a Frank-Wolfe gap
    larger than the bound's shortfall: more steps may close the gap
    ([[meat-core/frank-wolfe/thm:firstorder]]). The rounds where the
    per-round number exceeds λ_EC/n (λ_EC taken to grow with n) and n times
    it does not exceed the deductions by a whole bit, so that the deductions
    that do not grow with n (the hash, the finite-size term, the hash
    penalty) are what leave no key ([[meat-core/thm:keylength]]). The
    per-round number is the bound; where the bound is not positive, max{0, h}
    is 0 at every n, so the lever is given only where more steps may make it
    positive, said as conditional on them, with the solver's estimate of
    h_low, named as an estimate.
    """
    items: list[SummaryItem] = []
    if zero.limited():
        assert zero.gap is not None
        limit = _input(inputs, "solver.max_iterations")
        items.append({
            "text": "Solver step limit: the search stopped at its limit"
                    + ("" if zero.steps is None else f" of {zero.steps:,} steps")
                    + f" with a Frank-Wolfe gap of {zero.gap:.3g} bits per round, "
                    "larger than "
                    + (f"|{zero.symbol}| = {-zero.bound:.3g}" if zero.bound <= 0
                       else f"the shortfall of {zero.symbol} per round")
                    + "; more steps (solver.max_iterations) may close the gap "
                    f"and give a positive key length ([[{FIRSTORDER_CLAIM}]]).",
            "pointer": (None if limit is None
                        else "/payload/config/solver/max_iterations"),
            "anchor": None,
        })
    per_round = _per_round(zero)
    deducted, fixed, lambda_ec = zero.deducted, zero.fixed, zero.lambda_ec
    if (per_round is not None and zero.rounds and deducted is not None
            and fixed is not None and lambda_ec is not None):
        words, value = per_round
        rounds = zero.rounds
        # λ_EC grows with n (an estimate is n times a rate), so more rounds
        # help only where the per-round number exceeds λ_EC/n and it is the
        # n-independent part that leaves no key.
        if value > lambda_ec / rounds and rounds * value < deducted + 1:
            parts = [f"the verification hash ({_bits(zero.verification)} bits)",
                     "the finite-size term of privacy amplification "
                     f"({_bits(zero.amplification)} bits)"]
            if zero.hash_penalty:
                penalty = zero.hash_penalty
                parts.append(f"the hash penalty ({_bits(penalty)} bit"
                             + (")" if penalty == 1 else "s)"))
            items.append({
                "text": "Rounds n: "
                        + ("" if zero.bound > 0 else
                           f"if more steps make {zero.symbol} positive, the "
                           "rounds matter too: ")
                        + f"at n = {_number(rounds)}, {words} is "
                        f"\u2248 {_bits(rounds * value)} bits"
                        + ("" if words.startswith("n·") else
                           " (the estimate is not a bound)")
                        + f", short of the {_bits(deducted + 1)} bits a one-bit "
                        f"key needs: the {_bits(deducted)} bits the key length "
                        f"deducts and one more. Of these deductions, "
                        f"{_bits(fixed)} bits do not grow with n: "
                        f"{_and(parts)}, less the constant bit"
                        + ("" if not lambda_ec else
                           f"; λ_EC = {_bits(lambda_ec)} bits is taken to grow "
                           "with n, as an estimate from the honest model does, "
                           f"and {value:.3g} bits per round exceeds λ_EC/n = "
                           f"{lambda_ec / rounds:.3g}")
                        + ". So more rounds may leave a key "
                        f"([[{KEYLENGTH_CLAIM}]]).",
                "pointer": "/payload/config/rounds", "anchor": None,
            })
    return items


def binding_words(name: str, value: Any) -> str | None:
    """Return a binding's value in words where its name alone misleads (L11, L12).

    ``tau`` is the reserved temporal or spectral index of the mode labels
    (``receiver/def:modes``), not the declared tolerance; ``invoked_at`` lists
    the receiver settings whose declaration carries an exact-window depth
    (``receiver/ass:eig``); what rests on the premise there is the setting's
    exact-window multi-click weight (``receiver/def:pmcex``). ``off`` is the
    probe setting with no probe light (``receiver/def:probe``), which a reader
    took for "the exact window is off".
    """
    if name == "tau" and not isinstance(value, bool) and isinstance(value, int):
        return (
            f"{value}, the temporal or spectral index of every mode label "
            "(reserved: a single value, with no temporal meaning; "
            "not the declared tolerance)"
        )
    if name == "invoked_at" and isinstance(value, list):
        if not value:
            return (
                "no receiver setting: no setting declared an exact window, so "
                "this premise is not drawn on"
            )
        named = "; ".join(
            "'off', the setting with no probe light (the only one of a receiver "
            "without a probe), not a switch of the exact window"
            if str(item) == "off" else f"'{item}', a receiver setting by name"
            for item in value
        )
        where, whose = (
            ("At this setting", "the setting's") if len(value) == 1
            else ("At these settings", "each setting's")
        )
        return (
            f"{named}. {where} the declared exact window was used, so {whose} "
            "multi-click weight rests on this premise"
        )
    if name == "public_choices":
        return _public_choice_words(value)
    return None


def _weight_words(value: Any) -> str:
    """Return a choice weight decimal first, its exact fraction beside where needed."""
    try:
        found = Fraction(str(value).strip())
    except (ValueError, ZeroDivisionError):
        return str(value)
    decimal = f"{float(found):.6g}"
    return decimal if Fraction(decimal) == found else f"{decimal} ({found})"


def _public_choice_words(value: Any) -> str | None:
    """Return A-COIN's public choices one per party: "Alice: Z 0.5, X 0.25".

    The record writes each choice as a mapping of its party, its choices in
    declared order and its weights by choice; flattened into one list the
    choices of two parties would run together.
    Anything of another shape is left to the generic words.
    """
    items = [value] if isinstance(value, Mapping) else value
    if not isinstance(items, list) or not items:
        return None
    parts: list[str] = []
    for item in items:
        if not isinstance(item, Mapping):
            return None
        weights = item.get("weights")
        choices = item.get("choices")
        if not isinstance(weights, Mapping) or not isinstance(choices, list):
            return None
        order = [str(choice) for choice in choices]
        order += [str(key) for key in weights if str(key) not in order]
        party = item.get("party")
        who = party_name(str(party)) if party is not None else "a party"
        parts.append(f"{who}: " + ", ".join(
            f"{choice} {_weight_words(weights[choice])}" if choice in weights
            else choice
            for choice in order
        ))
    return "; ".join(parts)


def draft_sentence(drafts: Sequence[str]) -> str | None:
    """Return the sentence that names the run's premises still in draft."""
    if not drafts:
        return None
    return (
        "Premises of this run whose effective status is still draft, so not yet "
        "through an independent review: "
        + ", ".join(f"[[{short_id}]]" for short_id in drafts) + "."
    )


# --------------------------------------------------------------------------
# Diagnostics
# --------------------------------------------------------------------------

_DIAGNOSTIC_TEXT: Final[Mapping[str, tuple[str, str]]] = {
    "h_low": (
        "Estimate of h_low",
        "The objective at the point the solver returned: an estimate of the "
        "worst-case entropy per round. It claims no bound and is not used for "
        "the key length; the point is feasible only within a window, so the "
        f"estimate need not lie above h_low ([[{FIRSTORDER_CLAIM}]]).",
    ),
    "h_low_dropped": (
        "Estimate of h_low with a dropped set",
        "The same estimate where the run gave up the entropy deficits of a "
        "dropped set (every variable, statistic and constraint kept); not used "
        "for the key length.",
    ),
    "h_lb": (
        "First-order lower bound h_lb",
        "The first-order lower bound on h_low that the key length uses, through "
        "max{0, h_lb}: the best bound over the steps that passed the first-order "
        "checks. It is proved in exact arithmetic, its linear minimisations "
        "bounded exactly, and computed in floating point, so a computed h_lb can "
        "exceed h_low "
        f"([[{FIRSTORDER_CLAIM}]], [[{KEYLENGTH_BOUND_CLAIM}]]).",
    ),
    "h_lb_dropped": (
        "First-order lower bound with a dropped set",
        "The first-order lower bound where the run gave up the entropy deficits "
        "of a dropped set (every variable, statistic and constraint kept); it "
        "bounds the dropped value, which lies below h_low, and replaces h_lb in "
        "the key length on such a run.",
    ),
    "first_order_minus_estimate": (
        "Bound minus estimate",
        "h_lb minus the estimate of h_low, recorded with its sign as a "
        "diagnostic that asserts nothing. A negative value is how far the bound "
        "lies below the estimate, a rough indication of what a longer solve "
        "might gain. A positive value is evidence about the arithmetic or the "
        "relaxation, not by itself of an unsound bound.",
    ),
    "first_order_clamped": (
        "Bound clamped at zero",
        "Whether h_lb was negative, so that the key length used 0 in its place.",
    ),
    "estimate_point_relaxed_member": (
        "Estimate's point checked",
        "Whether the Choi factor of the estimate's point passed the three "
        "feasibility checks (the acceptance-side factor is not part of this "
        "check); it changes no bound, tier or length.",
    ),
    "frank_wolfe_gap": (
        "Frank-Wolfe gap",
        "The Frank-Wolfe gap of one step: the objective there minus that step's "
        "tangent-plane bound. On an fw run it is the last step whose gradient "
        "was formed; on a candidate search, the best contributing step. It is a "
        "convergence diagnostic, and no key length uses it. It reads the point "
        "the solver returned, which nothing verifies, so it is no proven bound.",
    ),
    "solver_status": (
        "How the solver's search stopped",
        "How the search for a good point stopped (on an fw run the loop's own "
        "stop; on a candidate search the search's termination), not whether the "
        "bound holds. How the search stopped does not enter h_lb, and any lower "
        "bound on h_low may stand in the key length "
        f"([[{KEYLENGTH_BOUND_CLAIM}]]); so it can cost key length. Whether h_lb "
        "is a lower bound rests on the first-order checks, which run in floating "
        "point, and on exact arithmetic the engine does not have "
        f"([[{FIRSTORDER_CLAIM}]]).",
    ),
    "iterations": (
        "Steps",
        "The number of steps the solve counted: Frank-Wolfe iterations on an fw "
        "run, candidate assessments on a candidate search.",
    ),
    "withdrawals": (
        "Withdrawn steps",
        "Steps whose first-order bound was withdrawn because a hypothesis failed "
        "or was not established, by reason; a withdrawn step contributes no "
        "bound "
        f"([[{FIRSTORDER_CLAIM}]]).",
    ),
}


#: THE READINGS THAT CHANGE ON A RUN REPORTED AT THE CERTIFIED TIER: the key length is
#: computed from the certified number h_cert
#: (``meat-core/frank-wolfe/cor:certified-keylength``), and h_lb is recorded beside it
#: (``foundations/req:tiers``: "a number at a weaker tier is recorded beside it").
#: ``h_cert`` is the record's ``certified.certified_bound``.
_CERTIFIED_DIAGNOSTIC_TEXT: Final[Mapping[str, tuple[str, str]]] = {
    "h_cert": (
        "Certified lower bound h_cert",
        "The certified lower bound, from which the key length is computed, "
        "exactly, through max{0, h_cert}: the first-order bound formed again at "
        "the solver's final points from the data of the declaration it is "
        "formed on, every arithmetic step exact or rigorously enclosed, so it "
        "lies below that declaration's value by the claims alone "
        f"([[{CERTIFIED_CLAIM}]], [[{CERTIFIED_SCOPE_CLAIM}]]).",
    ),
    "h_lb": (
        "First-order lower bound h_lb",
        "The first-order lower bound on h_low, recorded beside the certified "
        "bound h_cert, from which this run's key length is computed: the best "
        "bound over the steps that passed the first-order checks. It is proved "
        "in exact arithmetic, its linear minimisations bounded exactly, and "
        "computed in floating point, so a computed h_lb can exceed h_low "
        f"([[{FIRSTORDER_CLAIM}]], [[{CERTIFIED_CLAIM}]]).",
    ),
    "h_lb_dropped": (
        "First-order lower bound with a dropped set",
        "The first-order lower bound where the run gave up the entropy deficits "
        "of a dropped set (every variable, statistic and constraint kept); it "
        "bounds the dropped value, which lies below h_low, and is recorded "
        "beside the certified bound h_cert, from which this run's key length is "
        "computed.",
    ),
    "first_order_clamped": (
        "Bound clamped at zero",
        "Whether h_cert was negative, so that the key length used 0 in its place.",
    ),
}

#: ``h_cert`` on a run NOT reported at the certified tier (a point certified,
#: the tier withheld or the key length withheld by a gate): recorded, unused.
_RECORDED_CERTIFIED_TEXT: Final[tuple[str, str]] = (
    "Certified lower bound h_cert (recorded)",
    "The first-order bound formed again at the solver's final points from the "
    "data of the declaration it is formed on, every arithmetic step exact or "
    "rigorously enclosed. This run "
    "is not reported at the certified tier, so it is recorded only and no key "
    "length is computed from it; the reasons of the run's certified evaluation, "
    "or its key-length reason where a gate withheld the length, say why "
    f"([[{CERTIFIED_CLAIM}]]).",
)

#: Where a diagnostic that is not a field of the key-rate stage is read.
_DIAGNOSTIC_POINTER: Final[Mapping[str, str]] = {"h_cert": "certified/certified_bound"}


def diagnostic_rows(
    diagnostics: Mapping[str, Any],
    pointer: str = "/payload/stages/key_rate",
    reported_tier: str | None = None,
) -> list[DiagnosticRow]:
    """Return every diagnostic with its readable name and its one-line reading.

    ``reported_tier`` chooses the readings of h_cert, h_lb and the clamp on a
    run reported at the certified tier (:data:`_CERTIFIED_DIAGNOSTIC_TEXT`).
    """
    certified = reported_tier == "certified"
    rows: list[DiagnosticRow] = []
    for name, value in diagnostics.items():
        label, text = (
            _CERTIFIED_DIAGNOSTIC_TEXT[name]
            if certified and name in _CERTIFIED_DIAGNOSTIC_TEXT
            else _RECORDED_CERTIFIED_TEXT
            if name == "h_cert"
            else _DIAGNOSTIC_TEXT.get(name, (name, ""))
        )
        rows.append({
            "name": name,
            "label": label,
            "value": value,
            "explanation": text or None,
            "pointer": None if name == "withdrawals"
            else f"{pointer}/{_DIAGNOSTIC_POINTER.get(name, name)}",
        })
    return rows


def solver_attempts(search_report: Any) -> list[SolverAttempt]:
    """Return how each attempt of the candidate search stopped."""
    if not isinstance(search_report, Mapping):
        return []
    attempts: list[SolverAttempt] = []
    for item in search_report.get("attempts") or ():
        if not isinstance(item, Mapping):
            continue
        seconds = item.get("seconds")
        bound = item.get("assessed_bound_after")
        iterations = item.get("iterations")
        stop_reason = item.get("stop_reason")
        resumed = item.get("resumed")
        attempts.append({
            "method": str(item.get("method", "")),
            "termination": str(item.get("termination", "")),
            "iterations": iterations if isinstance(iterations, int) else None,
            "seconds": float(seconds) if isinstance(seconds, int | float) else None,
            "bound_after": float(bound) if isinstance(bound, int | float) else None,
            "stop_reason": None if stop_reason is None else str(stop_reason),
            "resumed": resumed if isinstance(resumed, bool) else None,
        })
    return attempts


def _finite_number(value: Any) -> float | None:
    """Return a finite JSON number as a float, or ``None``."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if math.isfinite(value) else None


def solve_stop(search_report: Any, diagnostics: Mapping[str, Any]) -> str | None:
    """Return how the candidate search stopped as a whole, in one paragraph.

    The record's ``termination`` is the search's last word, which is the last
    attempt's unless the gap target was met or the budget's deadline passed:
    a run that closed its bracket can read ``numerical_failure`` from a late
    probe, and one that an iteration cap ended with most of its budget unspent
    reads ``budget_exhausted``. This reads the whole report instead: whether
    the gap target was met, the relative gap the bracket closed to, how each
    attempt ended, the time used of the budget, and an iteration cap that
    ended a stage. A diagnostic: nothing here enters a bound or a key length.
    """
    if not isinstance(search_report, Mapping):
        return None
    attempts = [item for item in search_report.get("attempts") or ()
                if isinstance(item, Mapping)]
    termination = str(search_report.get("termination") or "")
    target = _finite_number(search_report.get("gap_target"))
    met = termination == "target_met" or any(
        item.get("termination") == "target_met" for item in attempts)
    target_text = "" if target is None else f" ({target:.3g})"
    parts = [
        f"The search met its gap target{target_text}." if met
        else f"The search did not meet its gap target{target_text}."
    ]
    relabelled = termination == "relative_gap_met"
    if relabelled:
        # The search's own bracket, on the declaration it searched; the
        # reported h_lb can be the reference companion's, formed after the
        # search, so the two relative gaps can differ by orders of magnitude.
        level = _finite_number(search_report.get("converged_relative_gap"))
        own = _finite_number(search_report.get("relative_gap"))
        parts.append(
            "It converged all the same: its last stage stopped making progress "
            "with the search's own bracket, on the declaration it searched, "
            "closed to "
            + ("" if own is None else f"a relative gap of {own:.3g}, ")
            + "within "
            + ("its relative tolerance" if level is None else f"{level:.3g}")
            + " of the value it brackets, which an absolute target does not "
            "see when the value itself is small."
        )
    h_low = _finite_number(diagnostics.get("h_low"))
    h_lb = _finite_number(diagnostics.get("h_lb"))
    if h_low is not None and h_lb is not None and h_low != 0:
        parts.append(
            ("The reported bracket (h_low against the h_lb the run reports) "
             "closed to a relative gap of " if relabelled
             else "Its bracket closed to a relative gap of ")
            + f"{(h_low - h_lb) / abs(h_low):.3g} ((h_low - h_lb) / |h_low|)."
        )
    if attempts:
        ended = Counter(str(item.get("termination", "")) for item in attempts)
        listing = ", ".join(f"{count} {name}" for name, count in ended.items())
        last = attempts[-1]
        why = last.get("stop_reason")
        parts.append(
            f"Its {len(attempts)} attempt{'s' if len(attempts) != 1 else ''} "
            f"ended {listing}; the last ({last.get('method', '')}) ended "
            f"{last.get('termination', '')}"
            + ("" if why is None else f", its probe series stopped by {why}")
            + "."
        )
    budget = _finite_number(search_report.get("budget_seconds"))
    spent = [_finite_number(item.get("seconds")) for item in attempts]
    if budget is not None and spent and all(value is not None for value in spent):
        used = sum(value for value in spent if value is not None)
        parts.append(
            f"It used {used:.3g} s of its {budget:.3g} s time limit"
            + (", stopping well before the limit."
               if not met and used < budget / 2 else ".")
        )
    cap = search_report.get("max_iterations")
    capped_methods = search_report.get("max_iterations_caps") or ()
    if isinstance(cap, int) and not isinstance(cap, bool):
        capped = sorted({
            str(item.get("method")) for item in attempts
            if item.get("method") in capped_methods and item.get("iterations") == cap
        })
        if capped:
            parts.append(
                f"The iteration cap (max_iterations = {cap}) ended the "
                f"{', '.join(capped)} stage{'s' if len(capped) > 1 else ''}."
            )
    parts.append(
        f"The record's termination field reads {termination or 'nothing'}."
    )
    return " ".join(parts)
