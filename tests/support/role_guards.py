"""Guards G1-G7 of the PM/EB roles, as functions over one run record.

WHY THIS EXISTS. The key-rate report of BBM92 (an entanglement-based run, an
untrusted source, two stations, no probe) must not show source premises, "Bob's"
private setting at Alice's station or a laboratory premise read as both
stations, as it would if premise texts, emission rules and the report
presupposed prepare-and-measure roles; the engine serves general DV PM and EB
protocols. The guards make that class of error visible on any run; each
function here is one guard, returning the
violations it finds (an empty list passes). The role vector they read is
:mod:`certiqs_key.runs.roles`, computed from the record alone.

THE GUARDS (G6 lives elsewhere):

* G1 no engaged premise is structurally trivial (``roles.TRIVIAL_WHEN``);
* G2 an untrusted run engages no source premise and renders no source group;
* G3 a station premise names no party but its station's, and no singular
  role noun;
* G4 every engaged premise's ``presupposes`` holds at its rows' scopes (the
  run-tier half; the claim half is ``check_claims``' role-word check);
* G5 on a key-length run, each party with a role has exactly one engaged
  laboratory row (A-LAB) bound to it;
* G6 A-COIN over every factor: ``tests/unit/test_pm_eb_coin_and_lab_premises.py`` (a
  public choice declared only at the second station engages A-COIN);
* G7 the roots follow the source mode: untrusted, ``transmitter/fact:sr`` is
  no root and A-ENS is not engaged; trusted, the two go together.

Who runs them: ``tests/unit/test_role_guards.py`` over every committed report
example, ``tests/integration/test_role_guards_fresh.py`` over fresh runs of the
same examples with the current engine.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from certiqs_key.domain.claim_closure import closure_table
from certiqs_key.runs.report import (
    build_report,
    default_contract_link,
    render_html,
    render_markdown,
)
from certiqs_key.runs.report.model import AssumptionEntry, KeyRateReport, group_entries
from certiqs_key.runs.roles import (
    PARTIES,
    PARTY_NAMES,
    TRIVIAL_WHEN,
    Roles,
    row_station,
    run_roles,
    unmet_presuppositions,
)

__all__ = [
    "GUARDS",
    "SINGULAR_ROLE_NOUNS",
    "Checked",
    "checked",
    "g1_no_trivial_premise",
    "g2_untrusted_has_no_source",
    "g3_station_names_its_own_party",
    "g4_presuppositions_hold",
    "g5_one_laboratory_per_party",
    "g7_roots_follow_the_mode",
    "violations",
]

#: Phrases that name one party's role in a text emitted at every station,
#: wrong wherever there are two stations.
SINGULAR_ROLE_NOUNS: tuple[str, ...] = (
    "the measuring party's",
    "the instance's declared party's",
)
_PARTY_WORD = re.compile(r"\b(" + "|".join(PARTY_NAMES.values()) + r")\b")
#: The roles whose presence a source premise presupposes (G2).
_SOURCE_ROLES = frozenset({"sends", "trusted-source"})


@dataclass(frozen=True)
class Checked:
    """One record with its report, both renderings and its role vector."""

    record: Mapping[str, Any]
    report: KeyRateReport
    markdown: str
    html: str
    roles: Roles
    table: Mapping[str, Any]

    @property
    def manifest(self) -> Mapping[str, Any]:
        """Return the record's assumption manifest (``{}`` where it has none)."""
        found = self.record["payload"].get("assumption_manifest")
        return found if isinstance(found, Mapping) else {}

    @property
    def engaged(self) -> list[Mapping[str, Any]]:
        """Return the record's engaged assumptions (premises and numerics)."""
        return [entry for entry in self.manifest.get("assumptions") or ()
                if isinstance(entry, Mapping)]

    @property
    def entries(self) -> list[AssumptionEntry]:
        """Return the report's engaged entries: premises, then numerics."""
        sections = self.report["sections"]
        return [*group_entries(sections["assumptions"]["groups"]),
                *sections["numerics"]["entries"]]


def checked(
    record: Mapping[str, Any], table: Mapping[str, Any] | None = None
) -> Checked:
    """Return a record ready for the guards; ``table`` defaults to the shipped one."""
    shipped = closure_table() if table is None else table
    report = build_report(record, table=table)
    link = default_contract_link()
    return Checked(
        record=record,
        report=report,
        markdown=render_markdown(report, contract_link=link),
        html=render_html(report, contract_link=link),
        roles=run_roles(record["payload"]),
        table=shipped,
    )


def _rows(entry: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = entry.get("emitted_by") or []
    return [row for row in (rows if isinstance(rows, list) else [rows])
            if isinstance(row, Mapping)]


def _at_row(binding: Mapping[str, Any], row: Mapping[str, Any]) -> bool:
    """Whether a binding was emitted by this row (its module, station and party)."""
    emitters = binding.get("emitted_by") or []
    return any(
        isinstance(emitter, Mapping)
        and emitter.get("module") == row.get("module")
        and emitter.get("station") == row.get("station")
        and emitter.get("party") == row.get("party")
        for emitter in (emitters if isinstance(emitters, list) else [emitters])
    )


def _presupposes(entry: Mapping[str, Any], table: Mapping[str, Any]) -> list[str]:
    """Return a premise's ``presupposes``: the record's snapshot, else the table's."""
    if "presupposes" in entry:
        return [str(role) for role in entry.get("presupposes") or ()]
    found = (table.get("assumptions") or {}).get(str(entry.get("short_id")))
    return [str(role) for role in (found or {}).get("presupposes") or ()]


# --------------------------------------------------------------------------
# The guards
# --------------------------------------------------------------------------


def g1_no_trivial_premise(c: Checked) -> list[str]:
    """G1: no engaged premise is trivially satisfied at any row of it.

    Each row of a premise of ``roles.TRIVIAL_WHEN`` is judged at its scope
    with the bindings that row emitted; a row trivially satisfied there is a
    premise an emitter should not have emitted on this run.
    """
    found: list[str] = []
    for entry in c.engaged:
        short_id = str(entry.get("short_id"))
        trivial = TRIVIAL_WHEN.get(short_id)
        if trivial is None:
            continue
        bindings = [binding for binding in entry.get("bindings") or ()
                    if isinstance(binding, Mapping)]
        for row in _rows(entry) or [{}]:
            here = [binding for binding in bindings if not row or _at_row(binding, row)]
            station = row.get("station")
            reason = trivial(
                here, c.roles, station if isinstance(station, int) else None
            )
            if reason is not None:
                found.append(f"{short_id} emitted by {dict(row)}: {reason}")
    return found


def g2_untrusted_has_no_source(c: Checked) -> list[str]:
    """G2: on an untrusted run nothing is "your source".

    No engaged premise has category ``source`` or presupposes a sender or a
    trusted source, and neither rendering has a source category heading nor
    the summary a "Your source" group.
    """
    if c.roles.source_trusted is not False:
        return []
    found: list[str] = []
    for entry in c.engaged:
        short_id = str(entry.get("short_id"))
        if entry.get("category") == "source":
            found.append(f"{short_id} has category source")
        presupposed = _SOURCE_ROLES & set(_presupposes(entry, c.table))
        if presupposed:
            found.append(f"{short_id} presupposes {sorted(presupposed)}")
    for name, text in (("markdown", c.markdown), ("html", c.html)):
        if 'id="category-source"' in text:
            found.append(f"the {name} page has a source category heading")
    for group in c.report["sections"]["summary"]["vouch"]:
        if group["about"] == "Your source":
            found.append("the summary has a 'Your source' group")
    return found


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                yield item


#: Both parties named together ("inaccessible to Alice and Bob") name
#: no one party's role, so G3 reads past the phrase.
_BOTH_PARTIES = re.compile(r"\b(?:Alice|Bob)\s+(?:and|or)\s+(?:Alice|Bob)\b")


def _wrong_words(text: str, allowed: set[str]) -> list[str]:
    words = [match for match in _PARTY_WORD.findall(_BOTH_PARTIES.sub("", text))
             if match not in allowed]
    lowered = text.lower()
    return [*words, *(noun for noun in SINGULAR_ROLE_NOUNS if noun in lowered)]


def g3_station_names_its_own_party(c: Checked) -> list[str]:
    """G3: a station premise names no other party and no singular role noun.

    A premise every row of which is at a station (``roles.row_station``) has
    a title, summary, user statement and current text naming only the
    parties of its stations; a binding every emitter of which is at a station
    names only those stations' parties in its name and string values. Both
    parties named together ("Alice and Bob") name no one party's role and
    pass. Neither uses a phrase of :data:`SINGULAR_ROLE_NOUNS`.
    """
    found: list[str] = []
    by_id = {str(entry.get("short_id")): entry for entry in c.engaged}
    for entry in c.entries:
        rows = entry["emitted_by"]
        stations = [row_station(c.roles, row) for row in rows]
        if rows and all(station is not None for station in stations):
            allowed = {PARTY_NAMES.get(station.party, station.party)
                       for station in stations if station is not None}
            owner = entry["owner"]
            for field, text in (("title", owner["title"]),
                                ("summary", owner["summary"]),
                                ("user statement", entry["user_statement"]),
                                ("current text", entry["current_text"])):
                wrong = _wrong_words(text or "", allowed)
                if wrong:
                    found.append(f"{entry['short_id']} {field} names {wrong}")
        raw = by_id.get(entry["short_id"], {})
        for binding in raw.get("bindings") or ():
            emitters = [emitter for emitter in binding.get("emitted_by") or ()
                        if isinstance(emitter, Mapping)]
            at = [row_station(c.roles, emitter) for emitter in emitters]
            if not emitters or any(station is None for station in at):
                continue
            allowed = {PARTY_NAMES.get(station.party, station.party)
                       for station in at if station is not None}
            for text in (str(binding.get("name", "")),
                         *_strings(binding.get("value"))):
                wrong = _wrong_words(text, allowed)
                if wrong:
                    found.append(
                        f"{entry['short_id']} binding {binding.get('name')!r} "
                        f"names {wrong}"
                    )
    return found


def g4_presuppositions_hold(c: Checked) -> list[str]:
    """G4 (run-tier half): each engaged premise's roles hold at its rows' scopes."""
    found: list[str] = []
    for entry in c.engaged:
        for role, scope in unmet_presuppositions(
            _presupposes(entry, c.table), c.roles, _rows(entry)
        ):
            found.append(f"{entry.get('short_id')} presupposes {role} at {scope}")
    return found


def g5_one_laboratory_per_party(c: Checked) -> list[str]:
    """G5: on a key-length run each party with a role has one A-LAB row, bound to it."""
    if c.report["sections"]["result"]["outcome"] != "key-length":
        return []
    lab = next((entry for entry in c.engaged if entry.get("short_id") == "A-LAB"),
               None)
    found: list[str] = []
    for party in PARTIES:
        if not c.roles.has_lab(party):
            continue
        rows = [row for row in _rows(lab or {}) if row.get("party") == party]
        bound = [
            binding for binding in (lab or {}).get("bindings") or ()
            if binding.get("name") == "party" and binding.get("value") == party
            and any(_at_row(binding, row) for row in rows)
        ]
        if len(rows) != 1 or len(bound) != 1:
            found.append(
                f"party {party} has {len(rows)} engaged A-LAB row(s) and "
                f"{len(bound)} party binding(s); exactly one of each is expected"
            )
    return found


#: The root that names A-ENS in trusted-source mode (transmitter/fact:sr).
SOURCE_REPLACEMENT_ROOT = "transmitter/fact:sr"


def g7_roots_follow_the_mode(c: Checked) -> list[str]:
    """G7: ``transmitter/fact:sr`` and A-ENS follow the source mode.

    Untrusted: neither is there (``meat-core/thm:accumulated-entropy`` uses
    none of the trusted-mode assumptions in that mode). Trusted: the root is
    named exactly where A-ENS is engaged, and one source-model premise is
    (A-ENS for a declared ensemble, A-WCP for the decoy source model, whose
    run names ``transmitter/decoy/cor:emitted-decoy`` instead).
    """
    roots = {
        str(root) for found in (c.manifest.get("roots") or {}).values()
        for root in found or ()
    }
    engaged = {str(entry.get("short_id")) for entry in c.engaged}
    sr, ens = SOURCE_REPLACEMENT_ROOT in roots, "A-ENS" in engaged
    found: list[str] = []
    if c.roles.source_trusted is False:
        if sr:
            found.append(f"untrusted run names {SOURCE_REPLACEMENT_ROOT} as a root")
        if ens:
            found.append("untrusted run engages A-ENS")
    elif c.roles.source_trusted is True and roots:
        if sr != ens:
            found.append(
                f"trusted run: {SOURCE_REPLACEMENT_ROOT} root {sr}, A-ENS engaged {ens}"
            )
        if not ens and "A-WCP" not in engaged:
            found.append("trusted run engages no source-model premise (A-ENS, A-WCP)")
    return found


#: Every guard of this module, by its number.
GUARDS: Mapping[str, Callable[[Checked], list[str]]] = {
    "G1": g1_no_trivial_premise,
    "G2": g2_untrusted_has_no_source,
    "G3": g3_station_names_its_own_party,
    "G4": g4_presuppositions_hold,
    "G5": g5_one_laboratory_per_party,
    "G7": g7_roots_follow_the_mode,
}


def violations(c: Checked) -> dict[str, list[str]]:
    """Return every guard's violations, only the guards that found some."""
    return {name: found for name, guard in GUARDS.items() if (found := guard(c))}
