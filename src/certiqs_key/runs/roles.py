"""Each party's role on one run, computed from the run record: the role vector.

WHY THIS EXISTS. "Alice" and "Bob" name the declaration's two parties (the
labels A and B of the party partition, ``meat-core/def:declaration``), and a
party may send, measure, or both: on a prepare-and-measure run A sends and B
measures; on BBM92 (an untrusted source, two stations) A is a measuring
station that also holds the key and draws the test coin. The key-rate report
assumed the prepare-and-measure reading in several places ("Your source" on an
untrusted run, a laboratory premise read as "Your receivers", the source step
saying "emits one signal" where the source delivers one system to each
station). The report has to work for general DV PM and EB protocols. The
smallest set of role predicates that settles every role question is computed
once, in this module, so the report and the guards
(``tests/support/role_guards.py``) read one vector instead of re-deriving
roles in three places, and holds the one map from formal label to name.

PURE AND RECORD-ONLY. :func:`run_roles` reads a run record's payload and
nothing else (no engine call, no new record field), so it reads every record
the report reads (record 0.20.0 to 0.30.0): a field an older record lacks
falls back to what that record carries (``choice_weighting`` before
``choice_weightings``, the announcement tables before ``transcript``), and the
one measured factor of a single-receiver run that records no factorisation is
party B, the declaration's default partition
(``meat_core/declaration/declaration.py``, ``default_party_partition``).

PRESUPPOSITIONS. An assumption's optional ``presupposes`` list (the claim
header field, ``spec/claim-format.md`` section 3, carried by the claim-closure
table) names the roles a run must have for the assumption's text to hold.
:func:`presupposition_holds` evaluates one entry at a row's scope, with the
semantics written beside ``ASSUMPTION_PRESUPPOSITIONS`` in
``harness/check_claims.py``: ``trusted-source`` and ``letters`` at run level;
``sends`` at the row's party where it names one (``emitted_by.party``), else
at some party; ``setting`` at the row's station where it names one
(``emitted_by.station``), else at some station. A role this module does not
know raises: the harness and the run tier then disagree on the vocabulary.

TRIVIALITY. :data:`TRIVIAL_WHEN` is the run-tier registry of guard G1: for a
premise whose every clause holds of any device at some run shape, a predicate saying,
at one row's scope, why the row is trivially satisfied there. An emitter
should not emit such a row; the guard holds the emitters to it. The
registry decides nothing in a run.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

__all__ = [
    "PARTIES",
    "PARTY_NAMES",
    "PRESUPPOSITIONS",
    "ROLE_CONDITIONED_CLAUSES",
    "STATION_MODULES",
    "TRIVIAL_WHEN",
    "PublicChoice",
    "Roles",
    "StationRoles",
    "label_order",
    "not_on_this_run",
    "party_name",
    "presupposition_holds",
    "row_station",
    "run_roles",
    "unmet_presuppositions",
]

#: The declaration's two formal party labels.
PARTIES: Final[tuple[str, str]] = ("A", "B")

#: THE ONE MAP from formal party label to the name the report gives it. "Alice"
#: is party A and "Bob" party B whatever each does in the protocol (the
#: glossary entries "Alice" and "Bob" say so to the reader).
PARTY_NAMES: Final[Mapping[str, str]] = {"A": "Alice", "B": "Bob"}

#: The roles a ``presupposes`` list may name; the same four as
#: ``ASSUMPTION_PRESUPPOSITIONS`` in ``harness/check_claims.py``
#: (``tests/unit/test_roles.py`` compares the two).
PRESUPPOSITIONS: Final[tuple[str, ...]] = (
    "trusted-source", "sends", "setting", "letters",
)


#: The modules that emit their rows per station (``stages.stations[k]``): on
#: a single-receiver run they emit at no station index, and their rows are
#: then the one receiver's (:func:`row_station`).
STATION_MODULES: Final[tuple[str, ...]] = ("receiver", "reductions")


def party_name(party: object) -> str:
    """Return a formal party label's name: ``A`` reads Alice, ``B`` Bob."""
    return PARTY_NAMES.get(str(party), f"party {party}")


@dataclass(frozen=True)
class StationRoles:
    """One measured factor (a station) and what happens there."""

    #: The index into ``stages.stations``; ``None`` for the one receiver of a
    #: single-receiver run, whose rows are emitted without a station.
    index: int | None
    #: The measured factor's label, where the record names it.
    factor: str | None
    #: The formal party label of the station.
    party: str
    #: The station's setting alphabet: its probe alphabet and the settings of
    #: a choice weighting declared at it, in record order, each once.
    settings: tuple[str, ...]
    #: Whether a public choice is applied at the station: a choice weighting
    #: declared at it, or a choice-weighted family of its party.
    choice_applied: bool
    #: The formal label of the party whose readout records the station's
    #: setting, where a choice weighting at the station shows it (A-COIN
    #: (ii): "a party whose readout records the setting component").
    setting_recorded_by: str | None

    @property
    def setting(self) -> bool:
        """SETTING(f): a private per-round setting with two or more values."""
        return len(self.settings) >= 2


@dataclass(frozen=True)
class PublicChoice:
    """One public choice of the run: who draws it, where, over which values."""

    #: The formal label of the party that draws it.
    party: str
    #: ``True`` where it is drawn at a station of that party (a choice
    #: weighting at a measured factor, or a measuring party's choice-weighted
    #: family), ``False`` for Alice's presentation, drawn with her letter.
    at_station: bool
    #: The measured factor of a choice weighting; ``None`` otherwise.
    factor: str | None
    #: The values of the choice, in record order.
    choices: tuple[str, ...]
    #: Whether its probabilities depend on a private setting of two or more
    #: values (A-COIN (ii)).
    setting_dependent: bool


@dataclass(frozen=True)
class Roles:
    """The role vector of one run."""

    #: ``compiled.source.source_mode`` (``trusted``, ``untrusted``), or None.
    source_mode: str | None
    #: SOURCE_TRUSTED; ``None`` where the record does not say.
    source_trusted: bool | None
    #: The formal party label of the letter system ``A``.
    alice_party: str
    #: ``d_A``, where recorded.
    alice_dim: int | None
    #: The letter alphabet ``X``.
    letters: tuple[str, ...]
    #: The transmitted system's dimension, where recorded.
    transmitted_dim: int | None
    #: The key holder's formal label, where recorded.
    key_holder: str | None
    #: The measured factors, in record order.
    stations: tuple[StationRoles, ...]
    #: The parties that draw a public choice of two or more values.
    choosers: frozenset[str]
    #: The senders of the public messages, in transcript order.
    message_senders: tuple[str, ...]
    #: Every public choice, in record order (the roles box, A-COIN's About).
    public_choices: tuple[PublicChoice, ...] = ()
    #: In an acceptance value written with a bar, whose announcement stands
    #: before the bar and whose after it, where every label of the record
    #: that shows it agrees (:func:`label_order`); ``None`` otherwise.
    label_order: tuple[str, str] | None = None
    #: Whether detector-response modes are declared (an assumption of
    #: :data:`RESPONSE_MODE_ASSUMPTIONS` engaged); ``None`` where the record
    #: carries no assumption manifest.
    response_modes: bool | None = None

    @property
    def has_letters(self) -> bool:
        """LETTERS: the letter alphabet has two or more letters."""
        return len(self.letters) >= 2

    def sends(self, party: str) -> bool:
        """SENDS(P): P holds A, the source is trusted and d_A >= 2."""
        return (party == self.alice_party and self.source_trusted is True
                and (self.alice_dim or 0) >= 2)

    def measures_a(self, party: str) -> bool:
        """MEASURES_A(P): P holds A, d_A >= 2 and the source is untrusted."""
        return (party == self.alice_party and self.source_trusted is False
                and (self.alice_dim or 0) >= 2)

    def draws_letter(self, party: str) -> bool:
        """DRAWS_LETTER(P): P holds A, d_A = 1 and |X| >= 2."""
        return party == self.alice_party and self.alice_dim == 1 and self.has_letters

    def stations_of(self, party: str) -> tuple[StationRoles, ...]:
        """STATIONS(P): the stations of party P."""
        return tuple(station for station in self.stations if station.party == party)

    def chooses(self, party: str) -> bool:
        """CHOOSES(P): P draws a public choice of two or more values."""
        return party in self.choosers

    def holds_key(self, party: str) -> bool:
        """HOLDS_KEY(P)."""
        return self.key_holder == party

    def has_lab(self, party: str) -> bool:
        """HAS_LAB(P): P has any role (derived)."""
        return (self.sends(party) or self.measures_a(party)
                or self.draws_letter(party) or self.chooses(party)
                or self.holds_key(party) or bool(self.stations_of(party))
                or party in self.message_senders)

    def station(self, index: int | None) -> StationRoles | None:
        """Return the station a row's ``emitted_by.station`` names.

        ``None`` names the one receiver of a single-receiver run, and no
        station where the run has several.
        """
        if index is None:
            return self.stations[0] if len(self.stations) == 1 else None
        return next(
            (station for station in self.stations if station.index == index), None
        )


def row_station(roles: Roles, emitter: Mapping[str, Any]) -> StationRoles | None:
    """Return the station one emitting row is at, or ``None`` for a wider row.

    A row naming ``station`` k is at the station of index k; a row of a
    module of :data:`STATION_MODULES` that names none is at the one receiver
    of a single-receiver run. Any other row is at run or party level.
    """
    station = emitter.get("station")
    if isinstance(station, int):
        return roles.station(station)
    if emitter.get("party") is None and str(emitter.get("module")) in STATION_MODULES:
        return roles.station(None)
    return None


# --------------------------------------------------------------------------
# Reading the record
# --------------------------------------------------------------------------


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []


def _unique(values: Iterable[Any]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values))


def _weightings(public: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Every recorded choice weighting (record 0.30.0's list, or the older one)."""
    listed = public.get("choice_weightings")
    if isinstance(listed, list):
        return [item for item in listed if isinstance(item, Mapping)]
    single = public.get("choice_weighting")
    return [single] if isinstance(single, Mapping) else []


def _readout_party(
    weighting: Mapping[str, Any], partition: Mapping[str, Any]
) -> str | None:
    """Return the party whose readout records a weighting's setting, or None.

    The weighting's ``support`` lists ``(readout letter, station letter,
    choice)``; the readout records the setting where every readout letter of
    the support comes from one station letter's setting (through
    ``setting_map``) and all of them are letters of one party's readout
    alphabet (``party_partition``: ``alice_*`` is party A's, ``bob_*`` B's),
    and of exactly one party's.
    """
    support = [row for row in _sequence(weighting.get("support"))
               if isinstance(row, list | tuple) and len(row) == 3]
    setting_map = _mapping(weighting.get("setting_map"))
    if not support or not setting_map:
        return None
    settings: dict[str, set[str]] = {}
    for readout, letter, _choice in support:
        if str(letter) not in setting_map:
            return None
        settings.setdefault(str(readout), set()).add(str(setting_map[str(letter)]))
    if any(len(found) != 1 for found in settings.values()):
        return None
    readouts = set(settings)
    matching = [
        party for party, key in (("A", "alice_readout_alphabet"),
                                 ("B", "bob_readout_alphabet"))
        if (alphabet := {str(item) for item in _sequence(partition.get(key))})
        and readouts <= alphabet
    ]
    # Exactly one party's readout alphabet must hold every support letter: two
    # parties with identically named letters leave the recorder unknown, and the report
    # then names the station only.
    return matching[0] if len(matching) == 1 else None


def _measured_factors(public: Mapping[str, Any]) -> list[tuple[str | None, str]]:
    """Return the measured factors ``(label, party)`` of ``sector_factorisation``."""
    found: dict[str | None, str] = {}
    for item in _sequence(public.get("sector_factorisation")):
        item = _mapping(item)
        if item.get("system", "Q") != "Q" or item.get("party") is None:
            continue
        label = None if item.get("label") is None else str(item["label"])
        found.setdefault(label, str(item["party"]))
    return list(found.items())


def _probe_alphabet(receiver: Mapping[str, Any]) -> list[Any]:
    domain = _mapping(receiver.get("bound_quantifier_domain"))
    alphabet = _sequence(domain.get("probe_alphabet")) or _sequence(
        receiver.get("probe_alphabet")
    )
    if alphabet:
        return alphabet
    return [
        _mapping(item).get("setting")
        for item in _sequence(_mapping(receiver.get("photon_blocks")).get("settings"))
        if _mapping(item).get("setting") is not None
    ]


def _choice_parties(
    source: Mapping[str, Any], manifest: Mapping[str, Any]
) -> list[tuple[str, tuple[str, ...], bool]]:
    """``(party, choices, at a station)`` of every setting-free public choice.

    Alice's presentation in ``compiled.source.public_choices`` (drawn with
    the letter, at no station), and every other family A-COIN binds
    (``public_choices``): a measuring party's choice-weighted family, applied
    at that party's stations.
    """
    presentation = _mapping(source.get("public_choices"))
    found: list[tuple[str, tuple[str, ...], bool]] = []
    families: list[tuple[Mapping[str, Any], bool]] = (
        [(presentation, False)] if presentation else []
    )
    for entry in _sequence(manifest.get("assumptions")):
        for binding in _sequence(_mapping(entry).get("bindings")):
            binding = _mapping(binding)
            if binding.get("name") != "public_choices":
                continue
            value = binding.get("value")
            for family in value if isinstance(value, list) else [value]:
                family = _mapping(family)
                if family and family != presentation:
                    families.append((family, True))
    for family, at_station in families:
        if family.get("party") is not None:
            found.append((
                str(family["party"]),
                _unique(_sequence(family.get("choices"))),
                at_station,
            ))
    return found


def _announced(public: Mapping[str, Any]) -> dict[str, set[str]]:
    """Return each party's announcement values (the transcript, else the tables)."""
    found: dict[str, set[str]] = {}
    for message in _sequence(public.get("transcript")):
        message = _mapping(message)
        if message.get("sender") is not None:
            found.setdefault(str(message["sender"]), set()).update(
                str(value) for value in _sequence(message.get("alphabet"))
            )
    if not found:
        for party, key in (("A", "alice_announcement_alphabet"),
                           ("B", "bob_announcement_alphabet")):
            values = {str(value) for value in _sequence(public.get(key))}
            if values:
                found[party] = values
    return found


def _without_kind(text: str) -> str:
    """Return ``Z`` for ``gen:Z``: a value without its round-kind prefix."""
    return text.split(":", 1)[1] if ":" in text else text


def label_order(public: Mapping[str, Any]) -> tuple[str, str] | None:
    """Return whose announcement an acceptance value writes before and after its bar.

    WHY: the label convention is the protocol
    document's, not the transcript order (a run may send Bob's message
    first and write Alice's letter first; the bbm92 document with Bob's coin
    writes Bob's message first). Each part of every label with one bar is
    matched to the one party whose announcement values hold it, as written,
    else without a round-kind prefix (``test:(Z,0)`` is Alice's ``(Z,0)``).
    The order is returned only where every label that decides it agrees and
    at least one does.
    """
    announced = _announced(public)
    if len(announced) != 2:
        return None
    bare = {party: {_without_kind(value) for value in values}
            for party, values in announced.items()}

    def owner(part: str) -> str | None:
        found = [party for party, values in announced.items() if part in values]
        if not found:
            found = [party for party, values in bare.items()
                     if _without_kind(part) in values]
        return found[0] if len(found) == 1 else None

    orders: set[tuple[str, str]] = set()
    for label in _sequence(public.get("acceptance_alphabet")):
        parts = str(label).split("|")
        if len(parts) != 2:
            continue
        first, second = owner(parts[0]), owner(parts[1])
        if first is not None and second is not None and first != second:
            orders.add((first, second))
    return next(iter(orders)) if len(orders) == 1 else None


def run_roles(payload: Mapping[str, Any]) -> Roles:
    """Return the role vector of the run whose record payload this is."""
    compiled = _mapping(payload.get("compiled"))
    source = _mapping(compiled.get("source"))
    public = _mapping(compiled.get("public"))
    partition = _mapping(public.get("party_partition"))
    stages = _mapping(payload.get("stages"))
    manifest = _mapping(payload.get("assumption_manifest"))
    note = _mapping(payload.get("honest_model_note"))

    mode = source.get("source_mode")
    trusted = note.get("source_trusted")
    if not isinstance(trusted, bool):
        trusted = None if mode is None else mode == "trusted"
    alice_party = str(partition.get("alice_system_party") or "A")
    dimension = source.get("alice_dim")
    transmitted = source.get("virtual_transmitted_system")
    weightings = _weightings(public)
    factor_party = dict(_measured_factors(public))
    choices = _choice_parties(source, manifest)

    def station_roles(
        index: int | None, factor: str | None, party: str,
        probe: Sequence[Any], only: bool,
    ) -> StationRoles:
        here = [
            weighting for weighting in weightings
            if only or (
                str(weighting["factor"]) == factor
                if weighting.get("factor") is not None
                else str(weighting.get("party")) == party
            )
        ]
        settings = _unique([
            *probe,
            *(value for weighting in here
              for value in _sequence(weighting.get("setting_alphabet"))),
        ])
        recorded = {_readout_party(weighting, partition) for weighting in here}
        return StationRoles(
            index=index,
            factor=factor,
            party=party,
            settings=settings,
            choice_applied=bool(here) or any(
                chooser == party and len(values) >= 2 and at_station
                for chooser, values, at_station in choices
            ),
            setting_recorded_by=(
                next(iter(recorded)) if len(recorded) == 1 and None not in recorded
                else None
            ),
        )

    stations: list[StationRoles] = []
    listed = [_mapping(item) for item in _sequence(stages.get("stations"))]
    if listed:
        for position, raw in enumerate(listed):
            factor = None if raw.get("factor") is None else str(raw["factor"])
            party = raw.get("party") or factor_party.get(factor) or "B"
            index = raw.get("index")
            stations.append(station_roles(
                index if isinstance(index, int) else position, factor, str(party),
                _probe_alphabet(_mapping(raw.get("receiver"))), only=False,
            ))
    else:
        factors = _measured_factors(public)
        construction = _mapping(stages.get("receiver_construction"))
        if not factors and (construction or public):
            factors = [(None, "B")]
        single = len(factors) == 1
        for factor, party in factors:
            stations.append(station_roles(
                None, factor, party,
                _probe_alphabet(construction) if single else [], only=single,
            ))

    choosers = {party for party, values, _ in choices if len(values) >= 2}
    drawn = [
        PublicChoice(party, at_station, None, values, False)
        for party, values, at_station in choices if len(values) >= 2
    ]
    for weighting in weightings:
        if len(_unique(_sequence(weighting.get("choice_alphabet")))) < 2:
            continue
        factor = weighting.get("factor")
        party = weighting.get("party") if factor is None else (
            factor_party.get(str(factor)) or next(
                (station.party for station in stations
                 if station.factor == str(factor)), None,
            )
        )
        if party is None and len(stations) == 1:
            party = stations[0].party
        if party is not None:
            choosers.add(str(party))
            drawn.append(PublicChoice(
                str(party), True, None if factor is None else str(factor),
                _unique(_sequence(weighting.get("choice_alphabet"))),
                len(_unique(_sequence(weighting.get("setting_alphabet")))) >= 2,
            ))

    transcript = [_mapping(item) for item in _sequence(public.get("transcript"))]
    senders = [str(item["sender"]) for item in transcript if item.get("sender")]
    if not senders:
        senders = [party for party, key in (("A", "announce_alice"),
                                            ("B", "announce_bob"))
                   if _sequence(public.get(key))]
    holder = public.get("key_holder")
    return Roles(
        source_mode=None if mode is None else str(mode),
        source_trusted=trusted,
        alice_party=alice_party,
        alice_dim=dimension if isinstance(dimension, int) else None,
        letters=_unique(_sequence(source.get("signal_alphabet"))),
        transmitted_dim=transmitted if isinstance(transmitted, int) else None,
        key_holder=None if holder is None else str(holder),
        stations=tuple(stations),
        choosers=frozenset(choosers),
        message_senders=tuple(senders),
        public_choices=tuple(drawn),
        label_order=label_order(public),
        response_modes=(
            None if not _sequence(manifest.get("assumptions"))
            else any(_mapping(entry).get("short_id") in RESPONSE_MODE_ASSUMPTIONS
                     for entry in _sequence(manifest.get("assumptions")))
        ),
    )


# --------------------------------------------------------------------------
# Presuppositions (the claim header field)
# --------------------------------------------------------------------------


def presupposition_holds(
    role: str, roles: Roles, *, party: str | None = None,
    station: int | None = None,
) -> bool:
    """Whether a ``presupposes`` entry holds of the run at one row's scope.

    The semantics are those written beside ``ASSUMPTION_PRESUPPOSITIONS`` in
    ``harness/check_claims.py``: ``trusted-source`` and ``letters`` at run
    level; ``sends`` at ``party`` where given, else at some party; ``setting``
    at ``station`` where given, else at some station. ``station`` is the
    row's ``emitted_by.station``, an index into ``stages.stations``.
    """
    if role == "trusted-source":
        return roles.source_trusted is True
    if role == "letters":
        return roles.has_letters
    if role == "sends":
        if party is not None:
            return roles.sends(party)
        return any(roles.sends(each) for each in PARTIES)
    if role == "setting":
        if station is not None:
            found = roles.station(station)
            return found is not None and found.setting
        return any(each.setting for each in roles.stations)
    raise ValueError(
        f"unknown presupposition {role!r}; harness/check_claims.py's "
        f"ASSUMPTION_PRESUPPOSITIONS and runs/roles.py's PRESUPPOSITIONS disagree"
    )


def unmet_presuppositions(
    presupposes: Iterable[str],
    roles: Roles,
    emitted_by: Iterable[Mapping[str, Any]],
) -> list[tuple[str, str]]:
    """Return ``(role, scope)`` for every entry unmet at some row of a premise.

    Each emitting row is a scope (its ``party`` and ``station``); a premise
    with no emitting row is evaluated at run level. ``scope`` reads
    ``run``, ``party A`` or ``station 0``.
    """
    rows = [dict(row) for row in emitted_by] or [{}]
    unmet: list[tuple[str, str]] = []
    for role in presupposes:
        for row in rows:
            party = row.get("party")
            station = row.get("station")
            if not presupposition_holds(
                role, roles,
                party=None if party is None else str(party),
                station=station if isinstance(station, int) else None,
            ):
                scope = (
                    f"party {party}" if party is not None
                    else f"station {station}" if station is not None else "run"
                )
                if (role, scope) not in unmet:
                    unmet.append((role, scope))
    return unmet


# --------------------------------------------------------------------------
# Triviality (guard G1)
# --------------------------------------------------------------------------

#: A row's bindings (the record's or the report's form: ``name``, ``value``).
type Bindings = Sequence[Mapping[str, Any]]
#: ``(bindings at the row, roles, the row's station)`` -> why it is trivial.
type Trivial = Callable[[Bindings, Roles, int | None], str | None]


def _values(bindings: Bindings, name: str) -> list[Any]:
    return [binding.get("value") for binding in bindings if binding.get("name") == name]


def _probe(bindings: Bindings, roles: Roles, station: int | None) -> str | None:
    """A-PROBE: one setting at the station (``q_* = 1``), so every clause holds."""
    weights = [binding for binding in bindings
               if str(binding.get("name", "")).startswith("q_")]
    if weights:
        return None if len(weights) >= 2 else "the station declares one setting"
    found = roles.station(station)
    if found is not None and not found.setting:
        return "the station declares one setting"
    return None


def _ensemble(bindings: Bindings, roles: Roles, station: int | None) -> str | None:
    """A-ENS: unused with an untrusted source; vacuous at one letter in dimension 1."""
    del station
    if roles.source_trusted is False:
        return "the source is untrusted"
    for value in _values(bindings, "source_ensemble"):
        value = _mapping(value)
        if (len(_sequence(value.get("signal_alphabet"))) == 1
                and value.get("transmitted_dim") == 1):
            return "one letter in a one-dimensional transmitted system"
    return None


def _alice_measurement(
    bindings: Bindings, roles: Roles, station: int | None
) -> str | None:
    """A-ALICE-MEAS: at one letter {M_x} is the identity on A."""
    del bindings, station
    return None if roles.has_letters else "the letter alphabet has one letter"


def _specification(bindings: Bindings, roles: Roles, station: int | None) -> str | None:
    """A-SPEC's ``alice_povm`` clause: bound at one letter, it holds of any device."""
    del station
    if _values(bindings, "alice_povm") and not roles.has_letters:
        return "its alice_povm clause is bound at one letter"
    return None


def _test_statistics(
    bindings: Bindings, roles: Roles, station: int | None
) -> str | None:
    """A-TSM: no setting and no public choice at the station."""
    del bindings
    found = roles.station(station)
    targets = [found] if found is not None else list(roles.stations)
    if targets and all(not each.setting and not each.choice_applied
                       for each in targets):
        return "no setting and no public choice at the station"
    return None


def _coin(bindings: Bindings, roles: Roles, station: int | None) -> str | None:
    """A-COIN: every public choice has one value."""
    del roles, station
    sizes: list[int] = []
    for value in _values(bindings, "choice_weighting"):
        for item in value if isinstance(value, list) else [value]:
            sizes.append(len(_sequence(_mapping(item).get("choice_alphabet"))))
    for value in _values(bindings, "public_choices"):
        for item in value if isinstance(value, list) else [value]:
            sizes.append(len(_sequence(_mapping(item).get("choices"))))
    if sizes and all(size <= 1 for size in sizes):
        return "every public choice has one value"
    return None


def _vacuum(bindings: Bindings, roles: Roles, station: int | None) -> str | None:
    """A-VAC: no undeclared input mode."""
    del roles, station
    values = _values(bindings, "undeclared_input_modes")
    if values and all(not _sequence(value) for value in values):
        return "no undeclared input mode"
    return None


def _eigenvalues(bindings: Bindings, roles: Roles, station: int | None) -> str | None:
    """A-EIG: invoked at no setting."""
    del roles, station
    values = _values(bindings, "invoked_at")
    if values and all(not _sequence(value) for value in values):
        return "invoked at no setting"
    return None


#: GUARD G1's REGISTRY: per short id, why a row of that
#: premise is trivially satisfied at its scope, or ``None``. Each predicate
#: restates the emission rule the premise's emitter states in its interface
#: (``emission_rule``) or the clause that is vacuous at that run shape.
TRIVIAL_WHEN: Final[Mapping[str, Trivial]] = {
    "A-PROBE": _probe,
    "A-ENS": _ensemble,
    "A-ALICE-MEAS": _alice_measurement,
    "A-SPEC": _specification,
    "A-TSM": _test_statistics,
    "A-COIN": _coin,
    "A-VAC": _vacuum,
    "A-EIG": _eigenvalues,
}


# --------------------------------------------------------------------------
# Role-conditioned clauses
# --------------------------------------------------------------------------

#: WHAT EACH CONDITION MEANS, and why a clause conditioned on it is not on
#: this run where it fails. ``setting`` is read at the premise's stations
#: where its rows are at stations (:func:`row_station`), else at any station.
_CONDITION_REASONS: Final[Mapping[str, str]] = {
    "trusted-source": "the source is untrusted",
    "lab-source": "the source is untrusted and counts as outside every laboratory",
    "setting": "no station it is about has a private setting",
    "alice-measures": "the declaration has one letter",
    "setting-choice": "no choice on this run is weighted by a setting",
    "letters": "the declaration has one letter, a placeholder",
    "response-modes": "no detector-response mode is declared",
}

#: The assumptions whose presence in a record's assumption manifest says that
#: detector-response modes are declared, the condition of A-ROUND-SQ's clause
#: about them. They are a removable submodule's; a tree without it has none,
#: and the clause is then off every run with a manifest.
RESPONSE_MODE_ASSUMPTIONS: Final[frozenset[str]] = frozenset()

#: THE ROLE-CONDITIONED CLAUSES OF THE PREMISES' PLAIN TEXTS. WHY: the sender,
#: trusted-source and probe clauses of the premises are conditional ("where the
#: party sends with a trusted source", "where it has one"), and a reader should
#: not have to check each condition against the setup. Per short id,
#: the clauses of its ``user_statement`` written under a role condition, each
#: with the condition (:data:`_CONDITION_REASONS`); :func:`not_on_this_run`
#: names those whose condition fails, and the report prints them beside the
#: premise ("Not on this run: ..."). Read off the user statements of the
#: claim-closure table; it marks a clause, it never removes or
#: rewrites one, and a premise not listed has no such clause (or one whose
#: condition the record cannot decide, such as A-ENS's pair source in the
#: laboratory). When a listed premise's user statement changes, re-read its
#: row. A CONDITION THE RECORD DOES NOT DECIDE HOLDS: nothing is marked off a
#: run whose record does not say. A-LAB is narrowed to the clauses about a
#: trusted source in the party's laboratory (Trojan-horse light into a station
#: stays excluded at every laboratory, as the user statement says), A-VAC is
#: not listed (whether the station's own equipment emits light is a hardware
#: fact the declaration it polices cannot show), and A-COIN's mention of
#: Alice's letter and A-ROUND-SQ's clause about detector-response modes are
#: listed.
ROLE_CONDITIONED_CLAUSES: Final[Mapping[str, tuple[tuple[str, str], ...]]] = {
    "A-LAB": (("lab-source", "the clauses about a trusted source in the party's "
                             "laboratory (the signals it emits, light seeding or "
                             "recalibrating its laser)"),),
    "A-SEQ": (("trusted-source",
               "the trusted source preparing and sending each round's signal"),),
    "A-RHOM": (("trusted-source",
                "the same source in every round, and the source's memory"),),
    "A-SEED": (("trusted-source",
                "the randomness of a trusted source and its prepared states"),),
    "A-SPEC": (("alice-measures",
                "Alice's declared measurement of two or more letters"),),
    "A-COIN": (("setting-choice",
                "a choice whose probabilities depend on a station's private "
                "setting"),
               ("letters", "its mention of Alice's letter")),
    "A-TSM": (("setting", "its probe setting"),),
    "A-TRUST": (("setting", "the probe states"),),
    "A-EXACT": (("setting", "the probe mean photon numbers"),),
    "A-NOSEL": (("setting", "the probe settings"),),
    "A-ROUND": (("setting", "the probe settings"),),
    "A-ROUND-SQ": (("response-modes", "the same response in each declared "
                                      "detector-response mode"),),
}


def _condition_holds(
    condition: str, roles: Roles, stations: Sequence[StationRoles]
) -> bool:
    if condition in ("trusted-source", "lab-source"):
        # Trusted-source mode at the party of A, whatever d_A (ass:lab: the
        # systems handed out of a laboratory); unknown holds.
        return roles.source_trusted is not False
    if condition == "setting":
        present = stations or roles.stations
        return not present or any(station.setting for station in present)
    if condition == "letters":
        return roles.has_letters or not roles.letters
    if condition == "response-modes":
        return roles.response_modes is not False
    if condition == "alice-measures":
        return roles.has_letters and (
            roles.source_trusted is not True or roles.alice_dim == 1
        )
    if condition == "setting-choice":
        return any(choice.setting_dependent for choice in roles.public_choices)
    raise ValueError(f"unknown role condition {condition!r}")


def not_on_this_run(
    short_id: str, roles: Roles, emitted_by: Iterable[Mapping[str, Any]]
) -> list[tuple[str, str]]:
    """Return ``(clause, reason)`` for each role-conditioned clause not on this run.

    A premise every row of which is at a station reads ``setting`` at those
    stations; any other premise at every station of the run.
    """
    rows = list(emitted_by)
    located = [row_station(roles, row) for row in rows]
    stations = (
        [station for station in located if station is not None]
        if rows and all(station is not None for station in located) else []
    )
    return [
        (clause, _reason(condition, roles))
        for condition, clause in ROLE_CONDITIONED_CLAUSES.get(short_id, ())
        if not _condition_holds(condition, roles, stations)
    ]


def _reason(condition: str, roles: Roles) -> str:
    """Return why a condition fails on this run (:data:`_CONDITION_REASONS`)."""
    if condition == "alice-measures" and roles.has_letters:
        return ("a trusted source with A of dimension two or more demands a "
                "source-replacement certificate instead")
    return _CONDITION_REASONS[condition]
