"""Build the key-rate report of one run record, and the report of a sweep.

WHY THIS EXISTS. Every key-rate run yields a key-rate report: everything
needed to qualify the key rate, so that a question a QKD security evaluation
asks of a claimed key rate can be answered from it.

A PURE PROJECTION OF THE RECORD. The builder computes no number: it reads
``key_length``, ``net_key_length``, ``security_parameter`` and the rest from
the record (the record is the authority). Assumption text is the record's
snapshot; the text of every other claim it links (statement claims,
limitations, the per-execution claims, the claims of the checks) is the
shipped closure table's (:mod:`certiqs_key.domain.claim_closure`). Run-tier
prose is limited to the three zero-default flags below; every other sentence
in a report is a claim's own plain-text field. The setup section
(:mod:`certiqs_key.runs.report.setup`) is the one exception on both
counts: its sentences are the run tier's reading of record fields, and its
expected statistics are sums over the record's exact honest distribution,
each saying how it was formed; none of them enters the key length.

WHAT IT REFUSES. The record shapes of
:data:`SUPPORTED_RECORD_SCHEMA_VERSIONS` are read; any other raises
:class:`ReportInputError` with ``reason = record_schema_version`` (no
conversion of old records, PRINCIPLES.md section 9: re-run the configuration at
``/payload/config``). Several shapes are read so that the reports of
records already written keep building. A sweep of records of
different instances raises ``mixed_instances``.

NO SUM OF ε. Neither report adds ε over executions or over sweep points. The
security parameter bounds one execution; the per-execution note cites
``meat-core/rem:repeated-executions`` and ``meat-core/cor:separate-executions``,
which say what holds for several executions and under which premise. A sweep
point carries its own parameter and nothing aggregates them.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Collection, Iterable, Mapping, Sequence
from typing import Any, Final, Literal

from certiqs_key.domain.claim_closure import (
    COMPOSITION_ROOTS,
    CORRECTNESS_ROOTS,
    SECRECY_ROOTS,
    ClaimClosureError,
    closure_table,
)
from certiqs_key.runs.errors import RunError
from certiqs_key.runs.report import explain
from certiqs_key.runs.report.checks import CHECKS, stage_index
from certiqs_key.runs.report.glossary import categories, see_claims
from certiqs_key.runs.report.inputs import (
    INPUT_POINTERS,
    build_facts,
    build_inputs,
    input_row_name,
    preparation_moves,
    resolve_pointer,
)
from certiqs_key.runs.report.model import (
    AlphaBound,
    AlphaEvaluationRow,
    AlphaSearchDetail,
    AlphaUsed,
    AssumptionEntry,
    AssumptionsSection,
    Binding,
    CategoryGroup,
    Check,
    ChecksSection,
    ClaimRef,
    CommonPart,
    Completeness,
    ConsequenceCounts,
    ContractAnchor,
    Deductions,
    Discrepancy,
    DocumentInfo,
    Emission,
    Family,
    Flag,
    Guarantee,
    InputRow,
    InstanceInfo,
    KeyRateReport,
    NoPositiveKey,
    NotEngaged,
    NumericsSection,
    Outcome,
    Points,
    Preparation,
    ProtocolSection,
    ProvenanceSection,
    Refusal,
    ReportIndex,
    ResultSection,
    SetupSection,
    StatisticsCheck,
    Summary,
    SweepPoint,
    SweepReport,
    UserDeclared,
    WhereRow,
    group_entries,
)
from certiqs_key.runs.report.setup import (
    build_setup,
    setup_claims,
    zero_count_outcomes,
)
from certiqs_key.runs.report.snaps import measurement_snaps, resting_sectors
from certiqs_key.runs.roles import Roles, party_name, run_roles
from certiqs_key.runs.stages import SliceStage

__all__ = [
    "CLAIM_MENTION_RE",
    "FLAG_SPECS",
    "PER_EXECUTION_CLAIMS",
    "REFUSED_DECLARED_BELOW",
    "REFUSED_NOT_LISTED",
    "REPORT_SCHEMA_VERSION",
    "SUPPORTED_RECORD_SCHEMA_VERSION",
    "SUPPORTED_RECORD_SCHEMA_VERSIONS",
    "SWEEP_ALL_REFUSED",
    "ReportInputError",
    "build_report",
    "build_sweep_report",
    "record_id",
    "resolve_claim_mention",
]

#: The report object's own shape version; bumped when ``report.schema.json``
#: is, which describes every field of the report and of the sweep report.
REPORT_SCHEMA_VERSION: Final[str] = "0.36.0"
#: The record schema version this builder is written against, the newest of
#: :data:`SUPPORTED_RECORD_SCHEMA_VERSIONS`. A constant of its own and not an
#: import of ``runs/record.py``'s ``RECORD_SCHEMA_VERSION``, so that the next
#: bump of the record cannot pass through the builder unread:
#: ``tests/unit/test_report_build.py`` holds the two equal.
SUPPORTED_RECORD_SCHEMA_VERSION: Final[str] = "0.46.0"

#: EVERY RECORD SHAPE THIS BUILDER READS. A field that a record of an older
#: shape lacks is read as absent, and the report says so or omits the section
#: that reads it (no document and nothing user-declared, no measurement
#: snaps, no alpha search, no acceptance intervals, no statistics check, no
#: certified tier); a field an older shape names under another key or in
#: another form is read in that form; its assumption manifest is listed as
#: the record lists it.
SUPPORTED_RECORD_SCHEMA_VERSIONS: Final[tuple[str, ...]] = (
    "0.20.0",
    "0.21.0",
    "0.22.0",
    "0.23.0",
    "0.24.0",
    "0.25.0",
    "0.26.0",
    "0.27.0",
    "0.28.0",
    "0.29.0",
    "0.30.0",
    "0.31.0",
    "0.32.0",
    "0.33.0",
    "0.34.0",
    "0.35.0",
    "0.36.0",
    "0.37.0",
    "0.38.0",
    "0.39.0",
    "0.40.0",
    "0.41.0",
    "0.42.0",
    "0.43.0",
    "0.44.0",
    "0.45.0",
    SUPPORTED_RECORD_SCHEMA_VERSION,
)

#: THE TRUSTED ENGINE NUMERICS: the premises about the engine's own
#: arithmetic, the entries of this category (in the record's snapshot or the
#: closure table; derived, not listed by id). They
#: appear there and only there, never in the vouch list (an assumption is about the
#: environment, never the evaluated object's behaviour).
NUMERICAL_CATEGORY: Final[str] = "numerical-trust"

#: The claims that say what one execution's security parameter covers and
#: when several executions' parameters add. Cited by id, quoted by summary.
PER_EXECUTION_CLAIMS: Final[tuple[str, ...]] = (
    "meat-core/rem:repeated-executions",
    "meat-core/cor:separate-executions",
)

#: The claim that fixes how the completeness figure is reported.
COMPLETENESS_CLAIM: Final[str] = "statistics/binomial-box/req:completeness-report"

#: cor:composed-security (iii) charges ε_auth twice.
AUTH_FACTOR: Final[int] = 2

#: THE ZERO-DEFAULT FLAGS (zero is kept, and the report flags it: raised
#: whenever the parameter is zero). ``(id, parameter, text, ids)``. The
#: three texts, with :data:`REFUSED_NOT_LISTED` and :data:`SWEEP_ALL_REFUSED`,
#: are the only run-tier sentences of a report. Each flag qualifies a number
#: that exists only beside a key length (the length, its security parameter,
#: the net key; ``cor:composed-security`` (iii)), so a record without a key
#: length raises none: a refused one and a completed one whose outcome is
#: ``no-key-length`` alike. Such a record lists none of the flags'
#: assumptions in the vouch list, so a flag would cite premises the report does not
#: carry.
FLAG_SPECS: Final[tuple[tuple[str, str, str, tuple[str, ...]], ...]] = (
    (
        "lambda_ec_zero",
        "lambda_ec",
        "No error-correction leakage counted (λ_EC = 0). A run that sends an "
        "error-correction transcript must declare its length; with λ_EC = 0 the "
        "key length is too long for it.",
        ("A-KEYREG", "A-CONFORM"),
    ),
    (
        "eps_auth_zero",
        "eps_auth",
        "No authentication error counted (ε_auth = 0). This holds only where "
        "the classical channel is itself authenticated, with no keyed scheme "
        "and no pre-shared key; a keyed scheme's error, a reused key's distance "
        "δ included, must be declared.",
        ("A-AUTH",),
    ),
    (
        "k_auth_zero",
        "k_auth",
        "No authentication key consumption counted (k_auth = 0); the net key "
        "equals the key length.",
        ("A-AUTH",),
    ),
)

#: WHY THE VOUCH LIST AND THE ENGINE NUMERICS ARE EMPTY ON A REFUSED
#: RECORD: a refused run reached no result, so no claim was named and no
#: assumption engaged. The renderers fill in the refusing stage and its
#: module's reason code from the record's ``refusal``.
REFUSED_NOT_LISTED: Final[str] = (
    "No assumption of the run is listed because the run was refused at stage "
    "{stage} ({reason}) before any result named a claim."
)

#: Said after :data:`REFUSED_NOT_LISTED` where the protocol document declared
#: premises of its own, which the section still lists beneath it.
REFUSED_DECLARED_BELOW: Final[str] = (
    "The premises your protocol document declared are listed below."
)

#: The same for a sweep none of whose points completed.
SWEEP_ALL_REFUSED: Final[str] = (
    "No assumption is listed because every point was refused before any "
    "result named a claim."
)

#: How a flag's parameter is written in its text.
_FLAG_SYMBOLS: Final[Mapping[str, str]] = {
    "lambda_ec": "λ_EC", "eps_auth": "ε_auth", "k_auth": "k_auth",
}

_LINK_RE: Final = re.compile(r"\[\[([^\[\]]+)\]\]")
_SHORT_ID_RE: Final = re.compile(r"^A-[A-Z0-9-]+$")
#: ``<module>[/<submodule>...]/<kind>:<label>``, the claim ids of spec/.
_CLAIM_ID_RE: Final = re.compile(
    r"[a-z0-9][a-z0-9-]*(/[a-z0-9][a-z0-9-]*)*/[a-z]+:[A-Za-z0-9][A-Za-z0-9._-]*"
)
_MISSING: Final = object()

type Placement = Literal["assumptions", "numerics", "checks"]

_STAGES: Final[frozenset[str]] = frozenset(str(stage) for stage in SliceStage)


class ReportInputError(RunError):
    """A record the report cannot be built from, with a machine-readable reason.

    ``reason`` is one of ``not_a_run_record``, ``record_schema_version``,
    ``mixed_instances``, ``no_records``, ``labels_mismatch`` and (the CLI's)
    ``unreadable_record``; a consumer words the code and does not parse the
    message.
    """

    def __init__(self, reason: str, detail: str) -> None:
        """Store the reason beside the message."""
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


class _Table:
    """The closure table a report reads claim text from: shipped, or a test's."""

    def __init__(self, table: Mapping[str, Any]) -> None:
        self.claims: Mapping[str, Any] = table.get("claims") or {}
        self.assumptions: Mapping[str, Any] = table.get("assumptions") or {}
        self.order: tuple[str, ...] = tuple(table.get("category_order") or ())
        self.limitations: tuple[str, ...] = tuple(table.get("limitations") or ())
        #: Every module and submodule path the claim graph registers.
        self.modules: tuple[str, ...] = tuple(table.get("module_versions") or ())
        #: Each root's closure: the assumptions it rests on, by short id.
        self.roots: Mapping[str, Any] = table.get("roots") or {}

    def beneath(self, claim_ids: Iterable[str]) -> set[str] | None:
        """Return the short ids of the premises beneath the claims, or ``None``.

        The union of their closures' assumptions as the table states them;
        ``None`` where the table states no closure for one of them.
        """
        found: set[str] = set()
        for claim_id in claim_ids:
            closure = self.roots.get(claim_id)
            if not isinstance(closure, Mapping):
                return None
            found |= set(closure.get("assumptions") or ())
        return found

    def find(self, claim_id: str) -> ClaimRef | None:
        entry = self.claims.get(claim_id)
        if not isinstance(entry, Mapping):
            return None
        return _claim_ref(claim_id, entry)

    def claim(self, claim_id: str) -> ClaimRef:
        found = self.find(claim_id)
        if found is None:
            raise ClaimClosureError(
                f"the closure table carries no claim {claim_id!r}, which the "
                "key-rate report cites; regenerate it with "
                "python -m harness.generate_claim_closure"
            )
        return found

    def owner(self, short_id: str) -> str | None:
        entry = self.assumptions.get(short_id)
        return str(entry["owner"]) if isinstance(entry, Mapping) else None

    def category(self, short_id: str) -> str | None:
        entry = self.assumptions.get(short_id)
        found = entry.get("category") if isinstance(entry, Mapping) else None
        return None if found is None else str(found)


def _contract_of(claim_id: str) -> ContractAnchor:
    """Return the contract anchor of a claim: its core module's PDF.

    DERIVED FROM THE ID, NEVER COPIED. A link a renderer writes into an
    ``href`` is built here from a claim id of the house form (a submodule's
    claims live in its core module's PDF, ``harness/contract_navigation.py``),
    so no string carried in a record can reach a link target; an id of
    another form refuses the record.
    """
    if not _CLAIM_ID_RE.fullmatch(claim_id):
        raise ReportInputError("not_a_run_record", f"{claim_id!r} is not a claim id")
    core = claim_id.split("/", 1)[0]
    return {"pdf": f"spec/modules/{core}/contract.pdf", "anchor": f"claim-{claim_id}"}


def _claim_ref(claim_id: str, entry: Mapping[str, Any]) -> ClaimRef:
    return {
        "id": claim_id,
        "kind": str(entry.get("kind", "")),
        "kind_word": str(entry.get("kind_word", "")),
        "title": str(entry.get("title", "")),
        "summary": str(entry.get("summary", "")),
        "user_statement": (
            entry["user_statement"]
            if isinstance(entry.get("user_statement"), str) else None
        ),
        "status": str(entry.get("status", "")),
        "effective_status": str(entry.get("effective_status", "")),
        "contract": _contract_of(claim_id),
    }


def record_id(record: Mapping[str, Any]) -> str:
    """Return the sha256 of the record's canonical JSON (sorted keys, no spaces)."""
    text = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _check_record(record: object) -> Mapping[str, Any]:
    """Return the record if this builder reads it; raise otherwise."""
    if (
        not isinstance(record, Mapping)
        or record.get("kind") != "run-record"
        or not isinstance(record.get("payload"), Mapping)
    ):
        raise ReportInputError(
            "not_a_run_record", "the input is not a run record (kind run-record)"
        )
    version = record.get("schema_version")
    if version not in SUPPORTED_RECORD_SCHEMA_VERSIONS:
        raise ReportInputError(
            "record_schema_version",
            f"the record has schema {version!r}; this report reads "
            f"{', '.join(SUPPORTED_RECORD_SCHEMA_VERSIONS)} only. Re-run its "
            "configuration (/payload/config) to obtain a current record",
        )
    canonical = _canonical_record(record)
    _check_shape(canonical["payload"], str(version))
    return canonical


def _canonical_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return the record as its ``record.json`` reads back: keys sorted.

    WHY. A record held in memory (the job worker's) keeps its mappings in
    insertion order; the same record read from ``record.json``, which the
    writer emits with sorted keys, has them sorted. Every place in the report
    that walks a record mapping (the setup's operators, a binding's value,
    an input's domain, ...) would follow that order, so the two reports
    differed (tests/integration/test_run_facade.py). Reading the record once
    in its canonical form makes the report independent of key insertion
    everywhere at once; an explicit order the record carries (an alphabet, a
    letter list) still wins where a section reads one.
    """
    try:
        canonical: dict[str, Any] = json.loads(json.dumps(record, sort_keys=True))
    except (TypeError, ValueError) as exc:
        raise ReportInputError(
            "not_a_run_record", f"the record is not plain JSON data: {exc}"
        ) from exc
    return canonical


def _check_shape(payload: Mapping[str, Any], version: str) -> None:
    """Refuse a truncated or malformed record before anything reads it.

    The blocks the report reads must have the types the record writes: a
    ``config`` with its ``parameters``, the ``stages`` and, where present,
    the ``assumption_manifest`` with lists of objects, each assumption entry
    naming its short id and owner. A record that fails this is not a run
    record the report can read (``not_a_run_record``), never a traceback.
    """

    def refuse(what: str) -> ReportInputError:
        return ReportInputError("not_a_run_record", f"the record is malformed: {what}")

    config = payload.get("config")
    if not isinstance(config, Mapping):
        raise refuse("payload.config is missing or not an object")
    if not isinstance(config.get("parameters"), Mapping):
        raise refuse("payload.config.parameters is missing or not an object")
    if not isinstance(payload.get("stages", {}), Mapping):
        raise refuse("payload.stages is not an object")
    if version != "0.20.0" and "protocol_document" not in payload:
        # 0.21.0 writes the key on every record, null off the document route.
        raise refuse("payload.protocol_document is missing (record 0.21.0)")
    document = payload.get("protocol_document")
    if document is not None:
        if not isinstance(document, Mapping):
            raise refuse("payload.protocol_document is not an object")
        items = document.get("user_declared", [])
        if not isinstance(items, list) or not all(
            isinstance(item, Mapping)
            and isinstance(item.get("assumptions", []), list)
            for item in items
        ):
            raise refuse("protocol_document.user_declared is not a list of objects")
    manifest = payload.get("assumption_manifest")
    if manifest is None:
        return
    if not isinstance(manifest, Mapping):
        raise refuse("payload.assumption_manifest is not an object")
    for block in ("assumptions", "not_engaged", "discrepancies"):
        items = manifest.get(block, [])
        if not isinstance(items, list) or not all(
            isinstance(item, Mapping) for item in items
        ):
            raise refuse(f"assumption_manifest.{block} is not a list of objects")
    for entry in manifest.get("assumptions", []):
        if not isinstance(entry.get("short_id"), str) or not isinstance(
            entry.get("owner"), str
        ):
            raise refuse("an assumption entry lacks its short_id or owner")
        bindings = entry.get("bindings", [])
        if not isinstance(bindings, list) or not all(
            (isinstance(item, Mapping) and isinstance(item.get("name"), str))
            or (isinstance(item, list) and len(item) == 2 and isinstance(item[0], str))
            for item in bindings
        ):
            raise refuse(f"the bindings of {entry['short_id']} are malformed")


# --------------------------------------------------------------------------
# Assumption entries (R3, R4, R5's decided rows)
# --------------------------------------------------------------------------


def _emitter_label(raw: Any) -> str:
    if isinstance(raw, Mapping):
        module = str(raw.get("module", ""))
        station = raw.get("station")
        party = raw.get("party")
        label = module if station is None else f"{module}@station{station}"
        return label if party is None else f"{label}@party{party}"
    return str(raw)


def _emission(raw: Any, machine_key: str) -> Emission:
    if isinstance(raw, Mapping):
        station = raw.get("station")
        party = raw.get("party")
        return {
            "module": str(raw.get("module", "")),
            "station": None if station is None else int(station),
            "party": None if party is None else str(party),
            "machine_key": str(raw.get("machine_key", machine_key)),
            "inherited_from": raw.get("inherited_from"),
        }
    return {
        "module": str(raw),
        "station": None,
        "party": None,
        "machine_key": machine_key,
        "inherited_from": None,
    }


def _binding(
    raw: Any, record: Mapping[str, Any], row_pointers: Mapping[str, str]
) -> Binding:
    """Normalise one recorded binding and give it a pointer where one resolves."""
    if isinstance(raw, Mapping):
        source: Mapping[str, Any] = raw
    elif isinstance(raw, Sequence) and not isinstance(raw, str) and len(raw) == 2:
        source = {"name": raw[0], "value": raw[1]}
    else:
        raise ReportInputError(
            "not_a_run_record", f"a binding of the record is malformed: {raw!r}"
        )
    emitted = source.get("emitted_by") or []
    if not isinstance(emitted, list):
        emitted = [emitted]
    binding: Binding = {
        "name": str(source["name"]),
        "emitted_by": sorted({_emitter_label(item) for item in emitted}),
    }
    if "value" in source:
        binding["value"] = source["value"]
    if "input" in source:
        binding["input"] = str(source["input"])
    name = binding.get("input", binding["name"])
    row = input_row_name(name, row_pointers)
    for pointer in (
        source.get("pointer"),
        None if row is None else row_pointers[row],
        INPUT_POINTERS.get(name),
    ):
        if pointer and resolve_pointer(record, pointer, _MISSING) is not _MISSING:
            binding["pointer"] = str(pointer)
            break
    return binding


def _entry(
    raw: Mapping[str, Any],
    record: Mapping[str, Any],
    row_pointers: Mapping[str, str],
) -> AssumptionEntry:
    """Return the report's form of one record entry (the snapshot, copied)."""
    short_id = str(raw["short_id"])
    owner_id = str(raw.get("owner", ""))
    machine_key = str(raw.get("machine_key", ""))
    owner = _claim_ref(owner_id, {"kind": "ass", "kind_word": "Assumption", **raw})
    affects = raw.get("affects")
    emitted = raw.get("emitted_by") or []
    return {
        "short_id": short_id,
        "owner": owner,
        "machine_key": machine_key,
        "category": raw.get("category"),
        "affects": None if affects is None else [str(item) for item in affects],
        "refines": raw.get("refines"),
        "verification": str(raw.get("verification", "")),
        "verification_sentence": str(raw.get("verification_sentence", "")),
        "user_statement": raw.get("user_statement"),
        "bindings": [
            _binding(item, record, row_pointers) for item in raw.get("bindings") or ()
        ],
        "emitted_by": [
            _emission(item, machine_key)
            for item in (emitted if isinstance(emitted, list) else [emitted])
        ],
        # Filled once the stations are known (build_report).
        "about": "",
        "role_notes": [],
        "current_text": None,
        "at_stake": explain.at_stake(
            None if affects is None else [str(item) for item in affects], short_id
        ),
    }


def _placement(entry: AssumptionEntry, table: _Table) -> Placement:
    """Return the section an entry belongs in.

    The placement rule is applied here
    and not read from the record's ``section`` field, so that the two content
    rules the report owes hold whatever the record says: a decided or
    discharged row is a check, never a premise; an entry of category
    ``numerical-trust`` (in the record or the table) is a trusted engine
    numeric and appears nowhere else.
    """
    if entry["verification"] in ("decided", "discharged"):
        return "checks"
    if NUMERICAL_CATEGORY in (entry["category"], table.category(entry["short_id"])):
        return "numerics"
    return "assumptions"


def _group_category(entry: AssumptionEntry, trusted: bool | None) -> str | None:
    """Return the category an entry is grouped under: its own, with two readings.

    NO SOURCE GROUP UNLESS THE SOURCE IS TRUSTED: on an untrusted run
    nothing is "your source", and the current engine engages no source premise there
    (guard G2, ``tests/unit/test_role_guards.py``); an older record's source
    premise of such a run (A-ENS, A-ALICE-MEAS, the sender's laboratory
    premise) is grouped with the protocol's structure. An older record's
    per-party laboratory premise (:data:`explain.RETIRED_LABORATORY_KEYS`) is
    grouped with the laboratories, as A-LAB is.
    """
    if entry["machine_key"] in explain.RETIRED_LABORATORY_KEYS:
        return "laboratory"
    if entry["category"] == "source" and trusted is False:
        return "protocol-structure"
    return entry["category"]


def _groups(
    entries: Sequence[AssumptionEntry], order: Sequence[str],
    trusted: bool | None = None,
) -> list[CategoryGroup]:
    """Group entries by category (table order) and by ``refines`` family.

    A member sits under the topmost of its ``refines`` ancestors that is
    present; a member whose head is absent stands alone. The family sits in
    its head's category as :func:`_group_category` reads it with the run's
    source trust (``trusted``). Ids are sorted inside each level.
    """
    by_id = {entry["short_id"]: entry for entry in entries}

    def top(short_id: str) -> str:
        seen = {short_id}
        current = short_id
        while True:
            parent = by_id[current]["refines"]
            if parent is None or parent not in by_id or parent in seen:
                return current
            seen.add(parent)
            current = parent

    members: dict[str, list[AssumptionEntry]] = {}
    for short_id in sorted(by_id):
        head = top(short_id)
        members.setdefault(head, [])
        if head != short_id:
            members[head].append(by_id[short_id])

    categories: dict[str | None, list[Family]] = {}
    for head in sorted(members):
        entry = by_id[head]
        categories.setdefault(_group_category(entry, trusted), []).append(
            {"head": entry, "members": members[head]}
        )
    known = [category for category in order if category in categories]
    extra = sorted(
        category for category in categories
        if category is not None and category not in order
    )
    ordered: list[str | None] = [*known, *extra]
    if None in categories:
        ordered.append(None)
    return [
        {"category": category, "families": categories[category]}
        for category in ordered
    ]


def _not_engaged(raw: Any) -> NotEngaged:
    item: NotEngaged = {
        "short_id": str(raw.get("short_id", "")),
        "module": str(raw.get("module", "")),
        "reason": str(raw.get("reason", "")),
    }
    if raw.get("discharged_by") is not None:
        item["discharged_by"] = str(raw["discharged_by"])
    return item


def _discrepancy(raw: Any) -> Discrepancy:
    return {
        "short_id": str(raw.get("short_id", "")),
        "kind": str(raw.get("kind", "")),
        "emitted_by": raw.get("emitted_by"),
        "detail": raw.get("detail"),
    }


# --------------------------------------------------------------------------
# R1 result
# --------------------------------------------------------------------------


def _refusal(payload: Mapping[str, Any]) -> Refusal | None:
    if not payload.get("refused"):
        return None
    for stage, entry in (payload.get("stages") or {}).items():
        if isinstance(entry, Mapping) and entry.get("refused") is True:
            refusal: Refusal = {
                "stage": str(stage),
                "reason": entry.get("reason"),
                "detail": entry.get("detail"),
                "rule": entry.get("rule"),
            }
            # The bound a solve-stage refusal formed (the run tier's
            # plausibility block, also on acceptance_set_unreachable).
            found = entry.get("plausibility")
            if isinstance(found, Mapping):
                refusal["plausibility"] = {
                    name: found.get(name) for name in ("bound_name", "bound", "h_low")
                }
            return refusal
    return {"stage": "", "reason": None, "detail": None, "rule": None}


def _flags(parameters: Mapping[str, Any]) -> list[Flag]:
    """Raise a flag for each parameter at zero, and for one the record lacks.

    A zero raises the flag's text. An absent parameter raises the same flag
    with ``value: null`` and the text "... not recorded.", which claims
    nothing about the value the run used.
    """
    flags: list[Flag] = []
    for flag_id, parameter, text, ids in FLAG_SPECS:
        if parameters.get(parameter) is None:
            wording, value = f"{_FLAG_SYMBOLS[parameter]} not recorded.", None
        elif parameters[parameter] == 0:
            wording, value = text, parameters[parameter]
        else:
            continue
        flags.append(
            {
                "id": flag_id,
                "parameter": f"parameters.{parameter}",
                "value": value,
                "text": wording,
                "assumptions": list(ids),
            }
        )
    return flags


def _user_declared(payload: Mapping[str, Any]) -> list[UserDeclared]:
    """Return the protocol document's user-declared premises, as the record holds them.

    Copied, never worded here: each item's ``text`` is the document layer's
    sentence in the record. Empty off the document route and on a 0.20.0
    record, which has no ``protocol_document``.
    """
    document = payload.get("protocol_document")
    if not isinstance(document, Mapping):
        return []
    return [
        {
            "kind": str(item.get("kind", "")),
            "path": str(item.get("path", "")),
            "label": str(item.get("label", "")),
            "text": str(item.get("text", "")),
            "assumptions": [str(short_id) for short_id in item.get("assumptions", [])],
            "pointer": f"/payload/protocol_document/user_declared/{index}",
        }
        for index, item in enumerate(document.get("user_declared") or ())
    ]


def _document(payload: Mapping[str, Any]) -> DocumentInfo | None:
    document = payload.get("protocol_document")
    if not isinstance(document, Mapping):
        return None
    return {
        "id": str(document.get("id", "")),
        "format_version": str(document.get("format_version", "")),
        "packaged": bool(document.get("packaged", False)),
        "digest": str(document.get("digest", "")),
    }


def _outcome(payload: Mapping[str, Any]) -> Outcome:
    if payload.get("refused"):
        return "refused"
    key_rate = (payload.get("stages") or {}).get("key_rate") or {}
    return "key-length" if key_rate.get("key_length") is not None else "no-key-length"


#: The statuses at which a claim counts as accepted.
ACCEPTED_STATUSES: Final[frozenset[str]] = frozenset({"accepted", "implemented"})


def _route_below_accepted(
    payload: Mapping[str, Any], table: _Table, shown: Sequence[str]
) -> list[ClaimRef]:
    """Return the manifest's route theorems below accepted, not shown elsewhere.

    The review-status paragraph names the security statements and the key
    length's roots; the device and route premises reach the key length
    through the route theorems of the assumption manifest's ``roots``. Those
    are named only where their effective status is below accepted
    (``tests/unit/test_report_page.py``).
    """
    manifest = payload.get("assumption_manifest") or {}
    found = manifest.get("roots") or {}
    route = dict.fromkeys(
        str(claim) for claims in found.values() for claim in claims
        if str(claim) not in shown
    )
    refs = [table.find(claim) for claim in route]
    return [ref for ref in refs if ref is not None
            and ref["effective_status"] not in ACCEPTED_STATUSES]


def _route_all_accepted(
    payload: Mapping[str, Any], table: _Table, shown: Sequence[str]
) -> bool:
    """Whether the manifest names route theorems and every one is accepted.

    True only where each root outside ``shown`` is in the closure table at an
    accepted effective status, so the review-status paragraph can say so; a
    root the table does not carry
    leaves it unsaid.
    """
    manifest = payload.get("assumption_manifest") or {}
    found = manifest.get("roots") or {}
    route = [str(claim) for claims in found.values() for claim in claims
             if str(claim) not in shown]
    refs = [table.find(claim) for claim in route]
    return bool(refs) and all(
        ref is not None and ref["effective_status"] in ACCEPTED_STATUSES
        for ref in refs
    )


def _result(
    record: Mapping[str, Any], table: _Table, outcome: Outcome
) -> ResultSection:
    payload = record["payload"]
    config = payload.get("config") or {}
    parameters = config.get("parameters") or {}
    stages = payload.get("stages") or {}
    key_rate = stages.get("key_rate") or {}
    acceptance = stages.get("acceptance_construction")

    roots = [str(root) for root in key_rate.get("claim_roots") or ()]
    if outcome == "key-length":
        roots += [*COMPOSITION_ROOTS, *SECRECY_ROOTS, *CORRECTNESS_ROOTS]
    completeness: Completeness | None = None
    if isinstance(acceptance, Mapping) and not acceptance.get("refused"):
        completeness = {
            "eps_star": acceptance.get("completeness_certified"),
            "claim": table.claim(COMPLETENESS_CLAIM),
        }
    rounds = key_rate.get("rounds", config.get("rounds"))
    certified = key_rate.get("certified")
    on_tier = key_rate.get("reported_tier") == "certified" and isinstance(
        certified, Mapping
    )
    certified_on = (
        str(certified["declaration"])
        if on_tier and isinstance(certified, Mapping) and certified.get("declaration")
        else None
    )
    return {
        "outcome": outcome,
        "refusal": _refusal(payload),
        "key_length": key_rate.get("key_length"),
        "net_key_length": key_rate.get("net_key_length"),
        "rate_per_round": key_rate.get("rate_per_round"),
        "rounds": rounds,
        "alpha": _alpha_used(payload),
        "reported_tier": key_rate.get("reported_tier"),
        "certified_on": certified_on,
        # The fallback of req:certified-evaluation (i): the companion's bound
        # counted, and the number was certified on the searched declaration.
        "certified_fallback": (
            certified_on == "searched"
            and isinstance(certified, Mapping)
            and "companion_points" in certified
            and (key_rate.get("reference_bracket") or {}).get("status") == "counted"
        ),
        "certified_premises": (
            [str(item) for item in certified.get("premises") or ()]
            if on_tier and isinstance(certified, Mapping)
            else []
        ),
        "key_length_reason": key_rate.get("key_length_reason"),
        "key_length_reason_code": key_rate.get("key_length_reason_code"),
        "reason_text": key_rate.get("reason_text"),
        "security_parameter": {
            "value": key_rate.get("security_parameter"),
            "terms": {
                name: parameters.get(name) for name in ("eps_pa", "eps_ev", "eps_auth")
            },
            "auth_factor": AUTH_FACTOR,
        },
        "completeness": completeness,
        "statement_claims": [table.claim(root) for root in dict.fromkeys(roots)],
        "route_claims_below_accepted": _route_below_accepted(payload, table, roots),
        "route_claims_accepted": _route_all_accepted(payload, table, roots),
        "per_execution": [table.claim(claim) for claim in PER_EXECUTION_CLAIMS],
        "not_counted": _flags(parameters) if outcome == "key-length" else [],
        "user_declared": _user_declared(payload),
        "limitations": [table.claim(claim) for claim in table.limitations],
        "statistics_check": _statistics_check(payload),
        "deductions": _deductions(key_rate),
    }


def _deductions(key_rate: Mapping[str, Any]) -> Deductions | None:
    """Return the record's deductions term by term, or ``None`` without a key length.

    Read, never computed: ``key_rate.deductions`` as
    ``meat_core.finitekey.result`` writes it (``meat-core/thm:keylength``).
    """
    found = key_rate.get("deductions")
    if key_rate.get("key_length") is None or not isinstance(found, Mapping):
        return None

    def term(name: str) -> float | None:
        value = found.get(name)
        return (float(value) if isinstance(value, int | float)
                and not isinstance(value, bool) else None)

    return {
        "error_correction": term("error_correction_lambda_ec"),
        "error_verification": term("error_verification"),
        "privacy_amplification": term("privacy_amplification"),
        "added_back": term("accepted_state_flag_bonus"),
        "hash_penalty": term("two_universal_hash_penalty"),
        "pointer": "/payload/stages/key_rate/deductions",
    }


def _statistics_check(payload: Mapping[str, Any]) -> StatisticsCheck | None:
    """Return the check of the acceptance set against the feasible statistics.

    From the record's ``statistics_consistency`` in its 0.46.0 shape
    (``meat-core/req:unreachable-acceptance-set`` (iv), (v)): the bound, the
    cap's exponent ``x`` with its tier and decision, ``tau`` and whether the
    run was refused. ``None`` on a record that carries none, and on one
    before 0.46.0, whose check refused by the share of the key length that
    the requirement no longer has: its report says nothing of the check. The
    per-order diagnostic ``n f`` is not read: the report does not show it.
    """
    block = payload.get("statistics_consistency")
    if not isinstance(block, Mapping) or "min_model_pass_probability" not in block:
        return None
    solve = block.get("solve") if isinstance(block.get("solve"), Mapping) else None
    return {
        "checked": bool(block.get("checked")),
        "unchecked_reason": block.get("unchecked_reason"),
        "bound": None if solve is None else solve.get("bound"),
        "bound_tier": None if solve is None else solve.get("bound_tier"),
        "alpha_0": None if solve is None else solve.get("alpha_0"),
        "no_bound_reason": None if solve is None else solve.get("no_bound_reason"),
        "model_pass_exponent_bits": block.get("model_pass_exponent_bits"),
        "model_pass_exponent_tier": block.get("model_pass_exponent_tier"),
        "model_pass_decision": block.get("model_pass_decision"),
        "min_model_pass_probability": block.get("min_model_pass_probability"),
        "no_cap_reason": block.get("no_cap_reason"),
        "refused": bool(block.get("refused")),
        "companion_admitted": (
            (((payload.get("stages") or {}).get("key_rate") or {})
             .get("reference_bracket") or {}).get("status")
            in ("counted", "withdrawn")
        ),
        "pointer": "/payload/statistics_consistency",
    }


# --------------------------------------------------------------------------
# R2 protocol, R4 diagnostics, R5 checks, R6 provenance
# --------------------------------------------------------------------------


def _instance(payload: Mapping[str, Any]) -> InstanceInfo | None:
    instance = payload.get("instance")
    if not isinstance(instance, Mapping) or "id" not in instance:
        return None
    return {
        "id": str(instance["id"]),
        "title": str(instance.get("title", "")),
        "summary": str(instance.get("summary", "")),
        "readme": str(instance.get("readme", "")),
    }


def _protocol(
    record: Mapping[str, Any],
    inputs: list[InputRow],
    entries: Sequence[AssumptionEntry],
) -> ProtocolSection:
    payload = record["payload"]
    tag = next(
        (
            binding.get("value")
            for entry in entries
            for binding in entry["bindings"]
            if binding["name"] == "honest_model" and "value" in binding
        ),
        None,
    )
    snaps = payload.get("snaps") if isinstance(payload.get("snaps"), Mapping) else None
    config = payload.get("config") or {}
    # The instance's input preparations are recorded under the snaps (the
    # document route writes none under the configuration), and the record's
    # extrema cover the measurement blocks alone: a moved input family is
    # folded in so that the table does not say nothing moved
    # (inputs.preparation_moves).
    prepared = resolve_pointer(record, "/payload/snaps/instance/input_preparation",
                               None)
    moves = preparation_moves(record)
    preparation: Preparation = {
        "input_preparation_pointer": (
            "/payload/config/input_preparation"
            if "input_preparation" in config
            else "/payload/snaps/instance/input_preparation"
            if isinstance(prepared, list) and prepared
            else None
        ),
        "snaps_pointer": None if snaps is None else "/payload/snaps",
        "declared_tolerance": config.get("declared_tolerance"),
        # The record's fields as it states them, beside the moves of its
        # input families under their own names.
        "snap_max_defect": None if snaps is None else snaps.get("snap_max_defect"),
        "snap_max_displacement": (
            None if snaps is None else snaps.get("snap_max_displacement")
        ),
    }
    if moves:
        defects = [move["normalization_defect"] for move in moves
                   if move["normalization_defect"] is not None]
        preparation["input_max_displacement"] = max(
            move["displacement"] for move in moves)
        preparation["input_normalization_defect"] = max(defects) if defects else None
    return {
        "measurement_snaps": measurement_snaps(
            record, [entry["short_id"] for entry in entries]
        ),
        "instance": _instance(payload),
        "document": _document(payload),
        "facts": build_facts(record),
        "inputs": inputs,
        "honest_model": {"note": payload.get("honest_model_note"), "tag": tag},
        "preparation": preparation,
    }


def _alpha_search_child(
    payload: Mapping[str, Any],
) -> tuple[str, Mapping[str, Any]] | None:
    """Return the searched ``alpha`` child's detail and its pointer, or ``None``.

    The outer alpha search (record 0.24.0) is recorded in one place: the
    solve stage's ``alpha`` child in ``composition_flow``, with
    ``searched: true``.
    """
    flow = payload.get("composition_flow")
    stages = flow.get("stages") if isinstance(flow, Mapping) else None
    for i, stage in enumerate(stages if isinstance(stages, list) else ()):
        if not isinstance(stage, Mapping) or stage.get("stage") != "solve":
            continue
        for j, child in enumerate(stage.get("children") or ()):
            if not isinstance(child, Mapping) or child.get("name") != "alpha":
                continue
            detail = child.get("detail")
            if isinstance(detail, Mapping) and detail.get("searched") is True:
                return (
                    f"/payload/composition_flow/stages/{i}/children/{j}/detail",
                    detail,
                )
    return None


def _alpha_used(payload: Mapping[str, Any]) -> AlphaUsed:
    """Return the Renyi order of the key length and what chose it (report 0.6.0)."""
    config = payload.get("config") or {}
    key_rate = (payload.get("stages") or {}).get("key_rate") or {}
    found = _alpha_search_child(payload)
    has_rate = key_rate.get("alpha") is not None
    pointer = "/payload/stages/key_rate/alpha" if has_rate else None
    if found is not None:
        where, detail = found
        settings = detail.get("settings") or {}
        lower = settings.get("lower_alpha_minus_one")
        upper = settings.get("upper_alpha_minus_one")
        evaluations = detail.get("evaluations")
        no_key = _no_positive_key(detail)
        return {
            "value": key_rate.get("alpha") if has_rate else detail.get("chosen_alpha"),
            "chosen_by": "outer-search",
            "searched_range": (
                None
                if lower is None or upper is None
                else [1.0 + float(lower), 1.0 + float(upper)]
            ),
            "runs": len(evaluations) if isinstance(evaluations, list) else None,
            "pointer": pointer or f"{where}/chosen_alpha",
            "no_positive_key": None if no_key is None else no_key["reason"],
        }
    configured = config.get("alpha")
    declared = (config.get("parameters") or {}).get("alpha")
    return {
        "value": (
            key_rate.get("alpha")
            if has_rate
            else configured if configured is not None else declared
        ),
        "chosen_by": "declaration" if configured is None else "configuration",
        "searched_range": None,
        "runs": None,
        "pointer": pointer
        or ("/payload/config/parameters/alpha" if configured is None
            else "/payload/config/alpha"),
        "no_positive_key": None,
    }


def _alpha_bound(found: Any) -> AlphaBound | None:
    """Return one of the no-key outcome's bounds, or ``None``."""
    if not isinstance(found, Mapping):
        return None
    alpha, h_lb = found.get("alpha"), found.get("h_lb")
    if alpha is None or h_lb is None:
        return None
    return {"alpha": float(alpha), "h_lb": float(h_lb)}


def _no_positive_key(detail: Mapping[str, Any]) -> NoPositiveKey | None:
    """Return the search's no-positive-key outcome (record 0.40.0), or ``None``."""
    found = detail.get("no_positive_key")
    if not isinstance(found, Mapping) or found.get("reported_alpha") is None:
        return None
    h_low = found.get("h_low")
    return {
        "reported_alpha": float(found["reported_alpha"]),
        "h_low": None if h_low is None else float(h_low),
        "largest_h_lb": _alpha_bound(found.get("largest_h_lb")),
        "largest_h_lb_searched": _alpha_bound(found.get("largest_h_lb_searched")),
        "reason": str(found.get("reason") or ""),
    }


def _alpha_search(payload: Mapping[str, Any]) -> AlphaSearchDetail | None:
    """Return the outer alpha search with every evaluation, or ``None``."""
    found = _alpha_search_child(payload)
    if found is None:
        return None
    where, detail = found
    rows: list[AlphaEvaluationRow] = [
        {
            "alpha": float(item["alpha"]),
            "phase": str(item.get("phase", "")),
            "key_length": item.get("key_length"),
            "h_lb": item.get("h_lb"),
            "score": item.get("score"),
            "reason": item.get("reason"),
            "seconds": float(item.get("seconds") or 0.0),
            "set_aside": (
                None if item.get("set_aside") is None else str(item["set_aside"])
            ),
        }
        for item in detail.get("evaluations") or ()
        if isinstance(item, Mapping) and item.get("alpha") is not None
    ]
    return {
        "pointer": where,
        "rule": detail.get("rule"),
        "reads": detail.get("reads"),
        "settings": dict(detail.get("settings") or {}),
        "chosen_alpha": detail.get("chosen_alpha"),
        "evaluations": rows,
        "refinement_stopped": (
            None if detail.get("refinement_stopped") is None
            else str(detail["refinement_stopped"])
        ),
        "no_positive_key": _no_positive_key(detail),
    }


#: The diagnostics, in the order shown. ``h_cert`` is the record's
#: ``certified.certified_bound`` (record 0.33.0), shown before h_lb: on a run
#: reported at the certified tier it is the number the key length is computed
#: from (foundations/req:tiers).
_DIAGNOSTICS: Final[tuple[str, ...]] = (
    "h_low",
    "h_low_dropped",
    "h_cert",
    "h_lb",
    "h_lb_dropped",
    "first_order_minus_estimate",
    "first_order_clamped",
    "estimate_point_relaxed_member",
    "frank_wolfe_gap",
    "solver_status",
    "iterations",
)


def _diagnostics(payload: Mapping[str, Any]) -> dict[str, Any]:
    key_rate = (payload.get("stages") or {}).get("key_rate") or {}
    fields = dict(key_rate)
    certified = key_rate.get("certified")
    if isinstance(certified, Mapping) and certified.get("certified_bound") is not None:
        fields["h_cert"] = certified["certified_bound"]
    found = {name: fields[name] for name in _DIAGNOSTICS if name in fields}
    gates = key_rate.get("per_iterate")
    if isinstance(gates, list):
        withdrawals = Counter(
            str(gate["withdrawal"])
            for gate in gates
            if isinstance(gate, Mapping) and gate.get("withdrawal") is not None
        )
        found["withdrawals"] = dict(sorted(withdrawals.items()))
    return found


def _checks(record: Mapping[str, Any], table: _Table) -> list[Check]:
    """Evaluate the check table on a completed or refused record.

    On a refused record the check that owns the refusal code reads
    ``refused``. A check before it -- or, when no check owns the code,
    before the refusing stage -- reads ``not-applicable`` where its own
    evaluation on the record says so and ``passed`` otherwise; every other
    check reads ``not-reached``. A refusing stage the record does not name,
    or names outside the stage vocabulary, places nothing: every check that
    does not own the code reads ``not-reached``.
    """
    refusal = _refusal(record["payload"])
    position: int | None = None
    if refusal is not None and refusal["reason"] is not None:
        position = next(
            (
                index for index, spec in enumerate(CHECKS)
                if refusal["reason"] in spec.reasons
            ),
            None,
        )
    known_stage = refusal is not None and refusal["stage"] in _STAGES
    checks: list[Check] = []
    for index, spec in enumerate(CHECKS):
        claims = [table.claim(claim) for claim in spec.claims]
        outcome, value, pointer = spec.evaluate(record)
        check: Check = {
            "id": spec.id, "title": spec.title, "claims": claims,
            "outcome": outcome, "value": value, "pointer": pointer,
        }
        if refusal is not None:
            if position is not None:
                before = index < position
            elif known_stage:
                before = stage_index(spec.stage) < stage_index(refusal["stage"])
            else:
                before = False
            check["value"], check["pointer"] = None, None
            if position == index:
                check["outcome"] = "refused"
                check["value"] = {"stage": refusal["stage"],
                                  "reason": refusal["reason"]}
                check["pointer"] = f"/payload/stages/{refusal['stage']}"
            elif before:
                # A check its own evaluation finds unreached (a receiver route
                # on a record refused at compilation) is not passed.
                check["outcome"] = (
                    outcome if outcome in ("not-applicable", "not-reached")
                    else "passed"
                )
            else:
                check["outcome"] = "not-reached"
        checks.append(check)
    return checks


def _provenance(
    record: Mapping[str, Any], report_id: str, statement: Sequence[ClaimRef]
) -> ProvenanceSection:
    payload = record["payload"]
    config = payload.get("config") or {}
    key_rate = (payload.get("stages") or {}).get("key_rate") or {}
    manifest = payload.get("assumption_manifest") or {}
    provenance = payload.get("provenance")
    engine = provenance.get("engine") if isinstance(provenance, Mapping) else None
    pointers = {
        name: f"/payload/stages/key_rate/{name}"
        for name in ("solver_request", "search_report", "joint_solver")
        if name in key_rate
    }
    artefacts = [
        {
            "stage": stage.get("stage"),
            "station": stage.get("station"),
            "kind": emit.get("kind"),
            "id": emit.get("id"),
            "digest": emit.get("digest"),
        }
        for stage in (payload.get("composition_flow") or {}).get("stages") or ()
        if isinstance(stage, Mapping)
        for emit in stage.get("emits") or ()
        if isinstance(emit, Mapping)
    ]
    return {
        "engine": dict(engine) if isinstance(engine, Mapping) else None,
        "created_by": str(record.get("created_by", "")),
        "config_digest": config.get("config_digest"),
        "record_schema_version": str(record["schema_version"]),
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "report_id": report_id,
        "module_versions": {
            "contracts": dict(payload.get("contracts") or {}),
            "assumption_manifest": dict(manifest.get("module_versions") or {}),
        },
        "claim_status": [
            {
                "id": claim["id"],
                "status": claim["status"],
                "effective_status": claim["effective_status"],
            }
            for claim in statement
        ],
        "solver": {
            "config": config.get("solver"),
            "solver_options": key_rate.get("solver_options"),
            "pointers": pointers,
        },
        "tolerances": {
            "declared_tolerance": config.get("declared_tolerance"),
            "optimizer": key_rate.get("tolerances"),
            "group_b_worst_pointer": (
                "/payload/stages/key_rate/group_b_worst"
                if "group_b_worst" in key_rate
                else None
            ),
        },
        "platform": key_rate.get("backend"),
        "artefacts": artefacts,
        "final_iterate": (
            dict(payload["final_iterate"])
            if isinstance(payload.get("final_iterate"), Mapping)
            else None
        ),
        "reproduce": {"config_pointer": "/payload/config"},
    }


# --------------------------------------------------------------------------
# The index of linked claims
# --------------------------------------------------------------------------


def _index(
    table: _Table,
    claims: Iterable[ClaimRef],
    entries: Sequence[AssumptionEntry],
    premises: Iterable[str] = (),
) -> ReportIndex:
    """Return every claim the report shows or links, and every linked id's owner.

    The ``[[...]]`` targets of carried text are resolved through the table;
    a target the table does not carry (a record snapshot older than the
    installed table) is left out and renders as plain text.
    """
    found: dict[str, ClaimRef] = {}
    owners: dict[str, str] = {}
    pending: list[str] = []

    def add(claim: ClaimRef) -> None:
        if claim["id"] not in found:
            found[claim["id"]] = claim
            pending.append(claim["summary"])
            if claim["user_statement"]:
                pending.append(claim["user_statement"])

    for claim in claims:
        add(claim)
    for entry in entries:
        owners[entry["short_id"]] = entry["owner"]["id"]
        add(entry["owner"])
        if entry["user_statement"]:
            pending.append(entry["user_statement"])
    # The premises a user-declared item stands under, and the closure members
    # the run lists as not engaged (a discharged A-LINK or A-RECV among them),
    # linked whether or not the run engaged them, so the report can name the
    # claim behind each.
    for short_id in premises:
        owner = owners.get(short_id) or table.owner(short_id)
        if owner is None:
            continue
        owners[short_id] = owner
        linked = found.get(owner) or table.find(owner)
        if linked is not None:
            add(linked)
    while pending:
        for target in _LINK_RE.findall(pending.pop()):
            target = target.strip()
            if _SHORT_ID_RE.match(target):
                owner = owners.get(target) or table.owner(target)
                if owner is None:
                    continue
                owners[target] = owner
                target = owner
            linked = found.get(target) or table.find(target)
            if linked is not None:
                add(linked)
    return {
        "claims": {key: found[key] for key in sorted(found)},
        "assumptions": {key: owners[key] for key in sorted(owners)},
    }


#: A CLAIM ID AS CARRIED TEXT WRITES IT (report 0.8.0): the
#: full id (``statistics/req:matched-alphabet``), one relative to a module
#: (``wpfss/cor:flat-companion``) or the bare ``kind:label`` of the
#: text's own module (``ass:keyreg``). The kinds are those of
#: ``spec/claim-format.md``.
CLAIM_MENTION_RE: Final = re.compile(
    r"(?<![\w/.:\-])((?:[a-z0-9][a-z0-9-]*/)*"
    r"(?:ass|req|thm|cor|def|lem|rem|prop|ex|fact):[A-Za-z0-9][A-Za-z0-9._-]*)"
)


def resolve_claim_mention(
    token: str, ids: Iterable[str], module: str | None = None
) -> str | None:
    """Return the claim id a mention in carried text names, or ``None``.

    The id itself; else the one id ending in ``/<token>`` (a module-relative
    or bare mention), within ``module`` where the text's own module is known
    and over all ``ids`` otherwise. An ambiguous or unknown mention resolves
    to nothing and stays plain text.
    """
    token = token.rstrip(".")
    known = list(ids)
    if token in known:
        return token
    candidates = [
        claim for claim in known
        if claim.endswith("/" + token)
        and (module is None or "/" in token or claim.startswith(module + "/"))
    ]
    return candidates[0] if len(candidates) == 1 else None


def _carried_texts(protocol: ProtocolSection) -> list[str]:
    """Return the run-tier texts that may name claims: meanings and snap causes."""
    texts = [str(row["meaning"]) for row in protocol["inputs"] if row["meaning"]]
    snaps = protocol["measurement_snaps"]
    if snaps is not None:
        texts += [*snaps["sentences"], *snaps["warnings"]]
        texts += [
            str(block[name]) for block in snaps["blocks"]
            for name in ("cause", "fix", "group_fix") if block[name]
        ]
    return texts


def _mentioned(table: _Table, texts: Iterable[str]) -> list[ClaimRef]:
    """Return the claims the texts name by id that the table carries."""
    found: list[ClaimRef] = []
    for text in texts:
        for match in CLAIM_MENTION_RE.finditer(text):
            claim_id = resolve_claim_mention(match.group(1), table.claims)
            linked = None if claim_id is None else table.find(claim_id)
            if linked is not None:
                found.append(linked)
    return found


def _known_ids(record: Mapping[str, Any], table: _Table) -> set[str]:
    """Return every claim id the report can know exists.

    The closure table's, and every claim in the closures the record's
    assumption manifest lists (``claim_closure``): ids taken from the claim
    graph, never guessed from a module name.
    """
    known = set(table.claims)
    manifest = record["payload"].get("assumption_manifest") or {}
    closure = manifest.get("claim_closure") if isinstance(manifest, Mapping) else None
    for item in (closure.values() if isinstance(closure, Mapping) else ()):
        if isinstance(item, Mapping):
            known.update(str(claim) for claim in item.get("claims") or ())
    return {claim for claim in known if _CLAIM_ID_RE.fullmatch(claim)}


def _strings(value: Any) -> list[str]:
    """Return every string inside a JSON value."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return []


def _scoped(value: Any) -> list[tuple[str, str]]:
    """Return ``(module, text)`` for every row that names the module of its text.

    A not-engaged row's reason is its module's emission rule, whose bare
    ``kind:label`` ids are that module's own (``thm:emit`` in reductions').
    """
    if isinstance(value, Mapping):
        module, reason = value.get("module"), value.get("reason")
        found = (
            [(module, reason)]
            if isinstance(module, str) and isinstance(reason, str) else []
        )
        return found + [pair for item in value.values() for pair in _scoped(item)]
    if isinstance(value, list):
        return [pair for item in value for pair in _scoped(item)]
    return []


def _mentions(
    document: Any, known: set[str], table: _Table, indexed: Collection[str]
) -> dict[str, ContractAnchor]:
    """Return the claim ids the report's text names that the table lacks.

    Keyed as written; a mention resolves when it is a known id or ends one
    uniquely (:func:`resolve_claim_mention`), or when it names its module and
    that module path ends exactly one registered module's (a submodule's
    claim such as ``wpfss/cor:flat-companion``, which no closure
    lists). A bare ``kind:label`` resolves through a known id or one such
    module-qualified mention on the page on the page, or, in a row
    that names its module (a not-engaged reason), as that module's claim,
    keyed then by ``<module>/<id as written>``. Nothing else becomes a link.

    The report package cannot read spec/, so it cannot see that a claim so
    built exists: it builds one only on a registered module path whose
    contract PDF the closure table already cites, and
    the examples test, which reads spec/, checks the claim files behind the
    committed examples' links.
    """
    found: dict[str, ContractAnchor] = {}
    pdfs = {_contract_of(claim)["pdf"] for claim in table.claims
            if _CLAIM_ID_RE.fullmatch(claim)}

    def registered(prefix: str, local: str) -> str | None:
        modules = [module for module in table.modules
                   if module == prefix or module.endswith("/" + prefix)]
        guess = f"{modules[0]}/{local}" if len(modules) == 1 else ""
        if _CLAIM_ID_RE.fullmatch(guess) and _contract_of(guess)["pdf"] in pdfs:
            return guess
        return None

    texts = _strings(document)
    tokens = [match.group(1).rstrip(".") for text in texts
              for match in CLAIM_MENTION_RE.finditer(text)]
    qualified = set(known)
    for token in tokens:
        if "/" in token and resolve_claim_mention(token, known) is None:
            guess = registered(*token.rpartition("/")[::2])
            if guess is not None:
                qualified.add(guess)
    # What the report's own index links already needs no mention; a claim the
    # closure table carries but the index does not still does.
    for token in tokens:
        if token in found or resolve_claim_mention(token, indexed):
            continue
        claim_id = resolve_claim_mention(token, qualified)
        if claim_id is not None:
            found[token] = _contract_of(claim_id)
    for module, text in _scoped(document):
        for match in CLAIM_MENTION_RE.finditer(text):
            token = match.group(1).rstrip(".")
            if "/" in token or token in found or resolve_claim_mention(
                token, indexed, module
            ):
                continue
            guess = resolve_claim_mention(token, known, module) or registered(
                module, token
            )
            if guess is not None:
                # Keyed by the text's module and the id as written, which is
                # what the renderer looks up for a row of that module.
                found[f"{module}/{token}"] = _contract_of(guess)
    return dict(sorted(found.items()))


def _found(table: _Table, claim_ids: Iterable[str]) -> list[ClaimRef]:
    """Return the claims of ``claim_ids`` the table carries, skipping the rest."""
    return [
        claim for claim in (table.find(claim_id) for claim_id in claim_ids)
        if claim is not None
    ]


# --------------------------------------------------------------------------
# The summary (report 0.9.0; explain.py holds every sentence)
# --------------------------------------------------------------------------


def _describe(entries: Sequence[AssumptionEntry], roles: Roles) -> None:
    """Fill in what each entry is about, from the run's role vector."""
    for entry in entries:
        entry["about"] = explain.about(
            entry, roles, _group_category(entry, roles.source_trusted)
        )
        entry["role_notes"] = explain.role_notes(entry, roles)
        entry["bindings"] = _readable_bindings(entry["bindings"], roles)


def _readable_bindings(bindings: Sequence[Binding], roles: Roles) -> list[Binding]:
    """Return a premise's bindings with the party ones in words.

    A reader meets A-LAB's bindings as a flat list (party: A,
    source_mode, party_partition, party: B). A ``party`` binding reads
    "laboratory: Alice's (party A)" and comes first, one per party; a
    ``party_partition`` binding reads "system A: party A (Alice); measured
    stations: alice_station (Alice), bob_station (Bob)", its measured
    factors matched to the run's stations in order. Other bindings are
    unchanged and keep their order.
    """
    first: list[Binding] = []
    rest: list[Binding] = []
    for binding in bindings:
        value = binding.get("value")
        if binding["name"] == "party" and isinstance(value, str):
            first.append({**binding, "name": "laboratory",
                          "value": f"{party_name(value)}'s (party {value})"})
            continue
        if binding["name"] == "party_partition" and isinstance(value, Mapping):
            rest.append({**binding, "value": explain.partition_words(value, roles)})
            continue
        rest.append(binding)
    return [*first, *rest]


def _line_about(entry: AssumptionEntry) -> str:
    """Return a summary line's own About, or "" where it is its category's.

    A line restates no About its group's heading already says, also where
    the heading words it differently (glossary.yaml "The channel and the
    attacker" for ABOUT's "The classical channel and the attacker"): only an
    About read off the row's scope (a station, a laboratory) is said.
    """
    category = entry["category"]
    words = None if category is None else explain.ABOUT.get(category)
    if words is not None and entry["about"] == words:
        return ""
    if words is not None and entry["about"].startswith(words + " (") and (
        entry["about"].endswith(")")
    ):
        # "Your random number generators (the choice drawn at ...)": the
        # heading says the first half (A-COIN).
        return entry["about"][len(words) + 2:-1]
    return entry["about"]


def _consequences(
    vouch: Mapping[str, Sequence[Family]], internal: Sequence[str],
    engaged: Mapping[str, AssumptionEntry],
) -> ConsequenceCounts:
    """Return the one-line count of the premises by consequence (item 3).

    Every premise of the run by its own ``affects``
    (:func:`explain.consequence`), refinements and the premises about
    artefacts and the engine's numerics included; those of the last that can
    break security are named.
    """
    counts = {"security": 0, "completeness": 0}
    for families in vouch.values():
        for family in families:
            for entry in (family["head"], *family["members"]):
                counts[explain.consequence(entry["affects"])] += 1
    engine: list[str] = []
    for short_id in internal:
        found = engaged.get(short_id)
        effect = explain.consequence(None if found is None else found["affects"])
        counts[effect] += 1
        if effect == "security":
            engine.append(short_id)
    return {"security": counts["security"], "engine": engine,
            "completeness": counts["completeness"]}


def _where(entries: Sequence[AssumptionEntry], roles: Roles) -> list[WhereRow]:
    """Return "Where each premise applies".

    The certification lab's checklist: per party laboratory, then per
    station, every premise of the run (What you vouch for and the premises
    about artefacts and the engine) that applies there
    (:func:`explain.places`), then those tied to no one station or
    laboratory. A premise about two places is listed under both.
    """
    rows_by_place: dict[str, list[str]] = {}
    for party in ("A", "B"):
        rows_by_place[f"{party_name(party)}'s laboratory"] = []
    for station in roles.stations:
        rows_by_place[explain.station_label(station)] = []
    elsewhere: list[str] = []
    for entry in entries:
        named = explain.places(
            entry, roles, _group_category(entry, roles.source_trusted)
        )
        for place in named:
            found = rows_by_place.setdefault(place, [])
            if entry["short_id"] not in found:
                found.append(entry["short_id"])
        if not named:
            elsewhere.append(entry["short_id"])
    rows: list[WhereRow] = [
        {"place": place, "premises": sorted(found)}
        for place, found in rows_by_place.items() if found
    ]
    if elsewhere and rows:
        rows.append({"place": "About the protocol as a whole (both parties' "
                              "equipment and software)",
                     "premises": sorted(elsewhere)})
    return rows


def _entropy(
    result: ResultSection, numerics: NumericsSection
) -> tuple[str, float] | None:
    """Return the per-round number the key length is computed from, with its symbol.

    h_cert on a run reported at the certified tier, h_lb on a first-order
    one (the record's diagnostics); ``None`` on any other run or where the
    record holds no such number.
    """
    tier = result["reported_tier"]
    symbol = {"certified": "h_cert", "first-order": "h_lb"}.get(str(tier))
    if symbol is None:
        return None
    value = numerics["diagnostics"].get(symbol)
    try:
        return None if value is None else (symbol, float(value))
    except (TypeError, ValueError):
        return None


def _supplied_law(protocol: ProtocolSection) -> bool:
    """Return whether a distribution was supplied in place of the honest model."""
    note = protocol["honest_model"]["note"]
    return isinstance(note, Mapping) and note.get("overridden") is True


def _summary(
    result: ResultSection,
    setup: SetupSection,
    protocol: ProtocolSection,
    assumptions: AssumptionsSection,
    numerics: NumericsSection,
    table: _Table,
    roles: Roles,
) -> Summary:
    """Return the report's first page."""
    premises = group_entries(assumptions["groups"])
    vouch: dict[str, list[Family]] = {}
    # The three groups the summary shows (explain.VOUCH_GROUPS), every premise
    # of the run in one, those about artefacts and the engine included.
    shown: dict[str, list[Family]] = {key: [] for key, _, _ in explain.VOUCH_GROUPS}
    internal: list[str] = []
    headings = categories()
    # The device categories first ("which to test first"); the
    # source only where it is trusted (an untrusted run has
    # no source group, _group_category).
    first = ("receiver", "source") if setup["source"] is None or (
        setup["source"]["trusted"] is not False
    ) else ("receiver",)
    ordered = sorted(
        assumptions["groups"],
        key=lambda group: (group["category"] not in first,
                           first.index(group["category"])
                           if group["category"] in first else 0),
    )
    for category_group in ordered:
        category = category_group["category"]
        for family in category_group["families"]:
            shown[explain.vouch_group(category)].append(family)
            if category in explain.ENGINE_CATEGORIES:
                internal += [family["head"]["short_id"],
                             *(member["short_id"] for member in family["members"])]
                continue
            # Grouped by category, the station named in each line's About
            # one line per refines-family.
            found = headings.get(str(category))
            heading = found.heading if found is not None else (
                category or "Uncategorised"
            )
            vouch.setdefault(heading, []).append(family)
    internal += [entry["short_id"] for entry in numerics["entries"]]
    shown["engine"] += [{"head": entry, "members": []}
                        for entry in numerics["entries"]]
    engaged = {
        entry["short_id"]: entry for entry in [*premises, *numerics["entries"]]
    }
    key = result["outcome"] == "key-length"
    completeness = result["completeness"]
    guarantee: Guarantee | None = None
    if key:
        guarantee = {
            "claim": _known(table, explain.COMPOSED_CLAIM),
            "terms": explain.guarantee_terms(result),
            "per_execution": _known(table, explain.PER_EXECUTION_CLAIM),
            "completeness": _known(table, explain.COMPLETENESS_CLAIM),
            "eps_star": None if completeness is None else completeness["eps_star"],
            "outside": _outside(engaged, table, result),
        }
    instance = protocol["instance"]
    snaps = protocol["measurement_snaps"]
    snap_entry = engaged.get("A-SNAP")
    # A run with a key and a security-bearing idealisation opens At a glance
    # with one short fragment saying so (a refused run opens with its refusal;
    # an idealised honest model alone bears on completeness only); the line
    # that says what is idealised closes the considerations.
    headline = key and explain.idealisation_bears_on_security(
        protocol["inputs"], set(engaged), roles
    )
    acceptance = setup["acceptance"]
    ideal = explain.idealised(
        protocol["inputs"], set(engaged), roles, after_headline=headline,
        zero_outcomes=0 if acceptance is None
        else len(zero_count_outcomes(acceptance["categories"])),
    )
    # A completed run whose key length is 0: its cause as the record states
    # it, which the box, the result and the levers say (M1).
    zero = explain.zero_key(result, numerics["diagnostics"], _entropy(result, numerics))
    box, considerations = explain.at_a_glance(
        result,
        sum(1 + len(family["members"]) for found in vouch.values()
            for family in found) + len(internal),
        None if snap_entry is None or snaps is None
        or not snaps["rests_on_a_snap"]
        else str(snap_entry["owner"]["effective_status"]),
        0 if snaps is None else snaps["evaluated_off_snap"],
        0 if snaps is None else sum(
            1 for block in snaps["blocks"] if block["status"] != "kept"
        ),
        supplied_law=_supplied_law(protocol),
        idealised_devices=bool(headline),
        k_auth=next((row["value"] for row in protocol["inputs"]
                     if row["name"] == "parameters.k_auth"), None),
        zero=zero,
        lambda_ec=next((row["value"] for row in protocol["inputs"]
                        if row["name"] == "parameters.lambda_ec"), None),
        diagnostics=numerics["diagnostics"],
        engine_premises=internal,
    )
    k_auth = next((row["value"] for row in protocol["inputs"]
                   if row["name"] == "parameters.k_auth"), None)
    # The setup in one fragment, after the idealised one, where a key came out.
    described = explain.setup_glance(
        setup, None if instance is None else dict(instance)
    ) if key else None
    if described is not None:
        box.insert(0, described)
    # A run that gives no key leads its box with that (M1), before the
    # idealised headline and the setup.
    lead = [item for item in box if item["lead"].startswith("No key")]
    return {
        "at_a_glance": [
            *lead,
            *([explain.idealised_headline()] if headline else []),
            *(item for item in box if item not in lead),
        ],
        # A snap warning (a moved block whose support is not preserved, a
        # discrepancy) and what is idealised close the considerations, so that
        # nothing the snaps' appendix part warns of leaves the summary.
        "considerations": [
            *considerations,
            *(explain.snap_warning(warning)
              for warning in ([] if snaps is None else snaps["warnings"])
              if not warning.startswith("The key rate rests on assumption A-SNAP")),
            *([] if ideal is None else [ideal]),
        ],
        "result": explain.result_sentence(
            result, None if setup["source"] is None else setup["source"]["trusted"],
            zero=zero, document=protocol["document"] is not None,
        ),
        "costs": explain.costs(result, k_auth, _entropy(result, numerics)),
        "guarantee": guarantee,
        "setup_brief": explain.setup_brief(
            setup, protocol["inputs"], None if instance is None else dict(instance)
        ),
        "roles": explain.roles_box(roles),
        "roles_absent": explain.roles_absent(roles),
        "vouch": [
            {"about": heading,
             "entries": [{"short_id": family["head"]["short_id"],
                          "title": family["head"]["owner"]["title"],
                          "consequence": explain.consequence(
                              family["head"]["affects"]),
                          "about": _line_about(family["head"]),
                          "refinements": [member["short_id"]
                                          for member in family["members"]],
                          "refinement_consequences": [
                              explain.consequence(member["affects"])
                              for member in family["members"]],
                          "summary": _one_liner(family["head"], table)}
                         for family in shown[key]]}
            for key, heading, _ in explain.VOUCH_GROUPS if shown[key]
        ],
        "where": _where([*premises, *numerics["entries"]], roles),
        "consequences": _consequences(vouch, internal, engaged),
        "internal": internal,
        "internal_consequences": [
            explain.consequence(engaged[short_id]["affects"])
            if short_id in engaged else "security"
            for short_id in internal
        ],
        "not_counted": explain.not_counted(
            result,
            [dict(claim) for claim in result["limitations"]] if key else [],
            engaged,
            protocol["measurement_snaps"],
        ),
        "levers": explain.levers(result, protocol["inputs"],
                                 protocol["measurement_snaps"], zero) if key else [],
        "tier_note": explain.tier_note(
            result, 0 if snaps is None else snaps["evaluated_off_snap"]
        ),
        "drafts": sorted(
            short_id for short_id, entry in engaged.items()
            if entry["owner"]["effective_status"] == "draft"
        ),
        "stale": sorted(
            short_id for short_id, entry in engaged.items()
            if entry["current_text"] is not None
        ),
    }


def _current_text(entry: AssumptionEntry, table: _Table) -> str | None:
    """Return the table's text of a premise where the record froze another.

    The record carries the assumption text of the engine that made the run;
    the closure table is this engine's. Where the two differ (whitespace
    aside) the report shows both.
    """
    current = table.assumptions.get(entry["short_id"])
    if not isinstance(current, Mapping):
        return None
    now = current.get("user_statement") or current.get("summary")
    then = entry["user_statement"] or entry["owner"]["summary"]
    if not isinstance(now, str) or not now.strip():
        return None
    return None if " ".join(now.split()) == " ".join(str(then).split()) else now


def _outside(
    engaged: Mapping[str, AssumptionEntry], table: _Table, result: ResultSection
) -> list[str] | None:
    """Return the run's premises not beneath the claims of the review status.

    The security statement and the key-length theorem, with the claims this
    run forms its key length through: a premise outside their closures (a
    receiver's, a reduction's, the statistics') enters through the run's own
    route. ``None`` where the table states no closure for one of them.
    """
    claims = [explain.COMPOSED_CLAIM, explain.KEYLENGTH_CLAIM,
              *(claim["id"] for claim in result["statement_claims"])]
    beneath = table.beneath(dict.fromkeys(claims))
    return None if beneath is None else sorted(set(engaged) - beneath)


def _current_reading(entry: AssumptionEntry, table: _Table) -> None:
    """Read a premise with the current contract where the record froze another.

    WHY: the note on premise texts an older engine froze says the current
    text is the one to vouch for, so the report must read the premise by it.
    What its failure puts at stake is the stricter of the record's ``affects``
    and the current contract's (their union; the current one alone where
    the record states none); a premise whose frozen text
    differs (``current_text``) takes the current summary as well, where the
    frozen reading is its ``user_statement`` and so stays shown as the earlier
    wording. A premise the table does not carry keeps the record's reading.
    """
    current = table.assumptions.get(entry["short_id"])
    if not isinstance(current, Mapping):
        return
    now = current.get("affects")
    then = entry["affects"]
    if isinstance(now, list):
        merged = sorted({*(then or ()), *(str(item) for item in now)})
        if then is None or merged != sorted(then):
            entry["affects"] = merged
            entry["at_stake"] = explain.at_stake(merged, entry["short_id"])
    summary = current.get("summary")
    if (entry["current_text"] is not None and entry["user_statement"]
            and isinstance(summary, str) and summary.strip()):
        entry["owner"] = {**entry["owner"], "summary": summary}


def _one_liner(entry: AssumptionEntry, table: _Table) -> str:
    """Return a premise's one-liner for What you vouch for: the current one.

    The first sentence of its current contract's summary where the record
    froze an earlier text; marked as the earlier text where the table has no
    current one to give.
    """
    summary = entry["owner"]["summary"]
    if entry["current_text"] is not None:
        current = table.assumptions.get(entry["short_id"])
        found = current.get("summary") if isinstance(current, Mapping) else None
        if isinstance(found, str) and found.strip():
            summary = found
        else:
            return "(earlier text) " + explain.first_sentence(summary)
    return explain.first_sentence(summary)


def _known(table: _Table, claim_id: str) -> str | None:
    return claim_id if table.find(claim_id) is not None else None


# --------------------------------------------------------------------------
# The run report
# --------------------------------------------------------------------------


def _row_pointers(record: Mapping[str, Any]) -> dict[str, str]:
    return {row["name"]: row["pointer"] for row in build_inputs(record, {})}


def _bound_by(
    entries: Sequence[AssumptionEntry], row_names: Iterable[str]
) -> dict[str, list[str]]:
    names = list(row_names)
    bound: dict[str, list[str]] = {}
    for entry in entries:
        for binding in entry["bindings"]:
            row = input_row_name(binding.get("input", binding["name"]), names)
            if row is not None:
                bound.setdefault(row, []).append(entry["short_id"])
    return bound


#: The quantities of a station's declared component values, which A-EXACT
#: says are the device's true values ("each efficiency, dark-count
#: probability, probe mean photon number and other component parameter");
#: a photon cutoff, an exact window and an efficiency normalization are
#: analysis choices, not values of the device.
_EXACT_QUANTITIES: Final[frozenset[str]] = frozenset(
    {"efficiency", "probability", "angle_pi", "mean_photon_number"}
)


#: The parts of a protocol document's station measurement whose parameters
#: are values of the receiver's components: its detectors, its optical
#: elements, its port Grams or instrument matrix, its dark-count channel,
#: and a probe's mean photon numbers (A-EXACT's "probe mean photon number").
_COMPONENT_PARTS: Final[frozenset[str]] = frozenset({
    "detectors", "elements", "port_grams", "instrument_matrix",
    "dark_count_channel",
})


#: An identifier in a document expression.
_IDENTIFIER: Final = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _component_parameters(record: Mapping[str, Any]) -> set[str]:
    """Return the parameters a protocol document declares receiver components with.

    Read off the record's canonical document: every ``{"param": name}`` and
    every identifier of an ``{"expr": ...}`` under a station measurement's
    component parts (:data:`_COMPONENT_PARTS`), or under its ``probe`` on a
    path that names a mean photon number. Empty off the document route.
    """
    document = (record.get("payload") or {}).get("protocol_document")
    canonical = document.get("canonical") if isinstance(document, Mapping) else None
    stations = canonical.get("stations") if isinstance(canonical, Mapping) else None
    found: set[str] = set()

    def walk(value: Any, path: tuple[str, ...]) -> None:
        if isinstance(value, Mapping):
            component = bool(path) and (
                path[0] in _COMPONENT_PARTS
                or (path[0] == "probe" and any("mean" in part for part in path))
            )
            name = value.get("param")
            if isinstance(name, str) and component:
                found.add(name)
            # An expression ("1 - pbs_leak_reflected") names its parameters
            # as identifiers; a name that is no input row matches none.
            expression = value.get("expr")
            if isinstance(expression, str) and component:
                found.update(_IDENTIFIER.findall(expression))
            for key, item in value.items():
                walk(item, (*path, str(key)))
        elif isinstance(value, list):
            for item in value:
                walk(item, path)

    for station in stations if isinstance(stations, list) else ():
        if isinstance(station, Mapping):
            walk(station.get("measurement"), ())
    return found


def _per_port_parameters(record: Mapping[str, Any]) -> set[str]:
    """Return the instance parameters declared per detector port."""
    instance = (record.get("payload") or {}).get("instance")
    specs = instance.get("parameters") if isinstance(instance, Mapping) else None
    return {
        str(spec["name"]) for spec in specs if isinstance(spec, Mapping)
        and spec.get("name") and spec.get("per_port_labels")
    } if isinstance(specs, list) else set()


def _exact_inputs(
    inputs: list[InputRow], engaged: Collection[str], record: Mapping[str, Any]
) -> list[InputRow]:
    """Name A-EXACT beside each declared receiver component value it covers.

    WHY: the inputs table's Premises column showed a dash beside every
    efficiency and dark count, though A-EXACT is the premise a reader vouches
    for there (the stage-9 experimentalist reader). Only where the run
    engages A-EXACT, on a device row of a component quantity that the record
    ties to a receiver: the instance's parameter table names its station; a
    protocol document declares a station's detector, element or probe with
    it (:func:`_component_parameters`); or it is declared per detector port.
    The inference is the report's, kept apart from the record's bindings in
    ``covered_by``; a value the record does not tie to a receiver keeps no
    entry, and the table's lead says what A-EXACT asks of every one.
    """
    if "A-EXACT" not in engaged:
        return inputs
    component = _component_parameters(record) | _per_port_parameters(record)
    for row in inputs:
        bare = row["name"].split(".", 1)[-1]
        if (row["section"] == "device" and row["quantity"] in _EXACT_QUANTITIES
                and (row["station"] is not None or bare in component)
                and "A-EXACT" not in row["bound_by"]):
            row["covered_by"] = sorted({*row["covered_by"], "A-EXACT"})
    return inputs


def build_report(
    record: Mapping[str, Any], *, table: Mapping[str, Any] | None = None
) -> KeyRateReport:
    """Return the key-rate report of one run record.

    ``table`` is the closure table the claim text is read from: the shipped
    one (:func:`~certiqs_key.domain.claim_closure.closure_table`) by default,
    a fixture's in a test. Raises :class:`ReportInputError` for a record this
    builder does not read and
    :class:`~certiqs_key.domain.claim_closure.ClaimClosureError` when the
    table lacks a claim the report cites (a stale table, a packaging defect).
    """
    record = _check_record(record)
    claims = _Table(closure_table() if table is None else table)
    payload = record["payload"]
    outcome = _outcome(payload)
    manifest = payload.get("assumption_manifest") or {}
    roles = run_roles(payload)

    row_pointers = _row_pointers(record)
    entries = [
        _entry(raw, record, row_pointers)
        for raw in manifest.get("assumptions") or ()
        if isinstance(raw, Mapping)
    ]
    for entry in entries:
        entry["current_text"] = _current_text(entry, claims)
        _current_reading(entry, claims)
    placed: dict[Placement, list[AssumptionEntry]] = {
        "assumptions": [], "numerics": [], "checks": [],
    }
    for entry in sorted(entries, key=lambda item: item["short_id"]):
        placed[_placement(entry, claims)].append(entry)

    inputs = _exact_inputs(build_inputs(record, _bound_by(entries, row_pointers)),
                           {entry["short_id"] for entry in entries}, record)
    not_engaged_all = [
        _not_engaged(raw) for raw in manifest.get("not_engaged") or ()
        if isinstance(raw, Mapping)
    ]
    report_id = record_id(record)
    result = _result(record, claims, outcome)
    checks: ChecksSection = {
        "checks": _checks(record, claims),
        "decided_rows": placed["checks"],
        "discharged_on_route": [
            item for item in not_engaged_all if "discharged_by" in item
        ],
    }
    assumptions: AssumptionsSection = {
        "groups": _groups(
            placed["assumptions"], claims.order, roles.source_trusted
        ),
        "not_engaged": [
            item for item in not_engaged_all if "discharged_by" not in item
        ],
        "discrepancies": [
            _discrepancy(raw) for raw in manifest.get("discrepancies") or ()
            if isinstance(raw, Mapping)
        ],
        # THE SAME ITEMS AS THE RESULT'S, here under the premises they stand under:
        # the route-exact manifest adds no user
        # premise of its own, so a premise the document supplied would
        # otherwise appear in the result section alone.
        "user_declared": result["user_declared"],
    }
    diagnostics = _diagnostics(payload)
    key_rate = (payload.get("stages") or {}).get("key_rate") or {}
    numerics: NumericsSection = {
        "entries": placed["numerics"],
        "diagnostics": diagnostics,
        "explained": explain.diagnostic_rows(
            diagnostics, reported_tier=result["reported_tier"]
        ),
        "solver_attempts": explain.solver_attempts(
            key_rate.get("search_report") if isinstance(key_rate, Mapping) else None
        ),
        "solve_stop": explain.solve_stop(
            key_rate.get("search_report") if isinstance(key_rate, Mapping) else None,
            diagnostics,
        ),
        "alpha_search": _alpha_search(payload),
    }
    setup = build_setup(record, known=lambda claim: claims.find(claim) is not None)
    _describe(entries, roles)
    if result["alpha"]["chosen_by"] == "outer-search":
        for row in inputs:
            if row["name"] == "parameters.alpha":
                row["not_used"] = "not used: alpha was searched"
    # The setting asks for the check of the statistics; where it did not run,
    # the row says so beside "on" (m1).
    not_run = explain.statistics_not_run(result)
    for row in inputs:
        if row["name"] == "parameters.statistics_check" and not_run is not None:
            row["not_used"] = not_run
    protocol = _protocol(record, inputs, entries)
    if setup["expected"]:
        note = protocol["honest_model"]["note"]
        model = note.get("model") if isinstance(note, Mapping) else None
        setup["expected_basis"] = explain.expected_basis(
            inputs, None if model is None else str(model), _supplied_law(protocol),
            detectors=any(station["detectors"] for station in setup["stations"]),
        )
    summary = _summary(result, setup, protocol, assumptions, numerics, claims, roles)
    shown = [
        *result["statement_claims"],
        *result["per_execution"],
        *result["limitations"],
        *([result["completeness"]["claim"]] if result["completeness"] else []),
        *(claim for check in checks["checks"] for claim in check["claims"]),
        *(claims.claim(claim) for claim in setup_claims(setup)),
        *_mentioned(claims, _carried_texts(protocol)),
        *_found(claims, [
            explain.COMPOSED_CLAIM, explain.PER_EXECUTION_CLAIM,
            explain.COMPLETENESS_CLAIM, explain.KEYLENGTH_CLAIM,
            explain.FIRSTORDER_CLAIM, explain.KEYLENGTH_BOUND_CLAIM,
            *see_claims(),
        ]),
        # Every claim the summary's and the setup's own sentences link, so
        # that each reads by its title wherever the closure table carries it.
        *_found(claims, [
            target.strip() for text in _strings([summary, setup])
            for target in _LINK_RE.findall(text)
            if _CLAIM_ID_RE.fullmatch(target.strip())
        ]),
    ]
    report: KeyRateReport = {
        "kind": "key-rate-report",
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "record_schema_version": str(record["schema_version"]),
        "id": report_id,
        "sections": {
            "summary": summary,
            "result": result,
            "setup": setup,
            "protocol": protocol,
            "assumptions": assumptions,
            "numerics": numerics,
            "checks": checks,
            "provenance": _provenance(record, report_id, result["statement_claims"]),
        },
        "index": _index(
            claims,
            shown,
            entries,
            [
                *(
                    short_id
                    for item in result["user_declared"]
                    for short_id in item["assumptions"]
                ),
                *(item["short_id"] for item in not_engaged_all),
            ],
        ),
    }
    report["index"]["mentions"] = _mentions(
        [report["sections"], report["index"]["claims"]],
        _known_ids(record, claims), claims, report["index"]["claims"],
    )
    _titled(report["index"], claims)
    return report


def _titled(index: ReportIndex, table: _Table) -> None:
    """Index every mentioned claim the closure table carries, so it reads by title.

    A mention is resolved with its module's scope (:func:`_mentions`); where
    the table carries the claim it names, the index gains that claim and the
    renderer links the mention as ``Kind "Title"`` rather than by its id. The
    mention stays as the fallback for a token the index cannot resolve alone.
    """
    for anchor in (index.get("mentions") or {}).values():
        claim_id = anchor["anchor"].removeprefix("claim-")
        found = None if claim_id in index["claims"] else table.find(claim_id)
        if found is not None:
            index["claims"][claim_id] = found
    index["claims"] = {key: index["claims"][key] for key in sorted(index["claims"])}


# --------------------------------------------------------------------------
# The sweep report
# --------------------------------------------------------------------------


def _all_entries(report: KeyRateReport) -> list[AssumptionEntry]:
    sections = report["sections"]
    return [
        *group_entries(sections["assumptions"]["groups"]),
        *sections["numerics"]["entries"],
        *sections["checks"]["decided_rows"],
    ]


def _fact(report: KeyRateReport, name: str) -> Any:
    for fact in report["sections"]["protocol"]["facts"]:
        if fact["name"] == name:
            return fact["value"]
    return None


def _route(report: KeyRateReport) -> tuple[str, frozenset[str]]:
    """Return a completed point's route signature and its engaged ids."""
    engaged = frozenset(entry["short_id"] for entry in _all_entries(report))
    signature = {
        "engaged": sorted(engaged),
        "receiver_route": _fact(report, "receiver_route"),
        "receiver_construction_route": _fact(report, "receiver_construction_route"),
        "reduction_route": _fact(report, "reduction_route"),
    }
    digest = hashlib.sha256(_canonical(signature).encode("utf-8")).hexdigest()
    return digest, engaged


def _merge_bindings(entries: Sequence[AssumptionEntry]) -> list[Binding]:
    """Return the union of the points' bindings, one that differs marked ``varies``.

    Names in order of first appearance. A binding whose value (or named
    input) differs between the points, or that some point lacks, is written
    once with ``varies: true`` and no value.
    """
    merged: list[Binding] = []
    names = list(dict.fromkeys(
        binding["name"] for entry in entries for binding in entry["bindings"]
    ))
    for name in names:
        found = [
            next((item for item in entry["bindings"] if item["name"] == name), None)
            for entry in entries
        ]
        values = {
            "\0missing" if item is None
            else _canonical(item.get("value", item.get("input")))
            for item in found
        }
        first = next(item for item in found if item is not None)
        if len(values) == 1:
            merged.append(first)
            continue
        varied: Binding = {
            "name": name,
            "varies": True,
            "emitted_by": sorted({
                label for item in found if item is not None
                for label in item["emitted_by"]
            }),
        }
        if "input" in first:
            varied["input"] = first["input"]
        if "pointer" in first:
            varied["pointer"] = first["pointer"]
        merged.append(varied)
    return merged


def _points_of(indices: Sequence[int], completed: Sequence[int]) -> Points:
    """Return ``"all"`` when every completed point holds a row, else its points."""
    return "all" if list(indices) == list(completed) else list(indices)


def _union_entries(
    per_point: Mapping[int, Sequence[AssumptionEntry]],
) -> list[AssumptionEntry]:
    """Return every entry some completed point carries, marked with its points.

    The text is the first carrying point's (one table, one text); the
    bindings are merged over the carrying points.
    """
    completed = sorted(per_point)
    carriers: dict[str, list[tuple[int, AssumptionEntry]]] = {}
    for index in completed:
        for carried in per_point[index]:
            carriers.setdefault(carried["short_id"], []).append((index, carried))
    result: list[AssumptionEntry] = []
    for short_id in sorted(carriers):
        versions = carriers[short_id]
        entry: AssumptionEntry = {
            **versions[0][1],
            "bindings": _merge_bindings([version for _, version in versions]),
            "points": _points_of([index for index, _ in versions], completed),
        }
        result.append(entry)
    return result


def _union_rows(
    per_point: Mapping[int, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    """Return every row some completed point carries, once, with its points."""
    completed = sorted(per_point)
    rows: dict[str, tuple[Mapping[str, Any], list[int]]] = {}
    for index in completed:
        for item in per_point[index]:
            key = _canonical(item)
            if key not in rows:
                rows[key] = (item, [])
            rows[key][1].append(index)
    return [
        {**item, "points": _points_of(indices, completed)}
        for item, indices in rows.values()
    ]


def _union_flags(per_point: Mapping[int, Sequence[Flag]]) -> list[Flag]:
    """Return every flag some completed point raises, marked with its points.

    In :data:`FLAG_SPECS` order; the text is the first raising point's. The
    UNION and not the intersection, as for every other row of the common part:
    a point without a key length
    raises no flag (:func:`_result`), and a flag one completed point raises
    still qualifies that point's number.
    """
    completed = sorted(per_point)
    raised: dict[str, tuple[Flag, list[int]]] = {}
    for index in completed:
        for flag in per_point[index]:
            if flag["id"] not in raised:
                raised[flag["id"]] = (flag, [])
            raised[flag["id"]][1].append(index)
    order = [flag_id for flag_id, _, _, _ in FLAG_SPECS]
    return [
        {**raised[flag_id][0],
         "points": _points_of(raised[flag_id][1], completed)}
        for flag_id in order
        if flag_id in raised
    ]


def _union_declared(
    reports: Sequence[KeyRateReport], completed: Mapping[int, KeyRateReport]
) -> list[UserDeclared]:
    """Return every user-declared item some completed point carries, with its points.

    The pointer is the first carrying point's; the points say where it holds.
    """
    order = sorted(completed)
    found: dict[str, tuple[UserDeclared, list[int]]] = {}
    for index in order:
        for item in reports[index]["sections"]["result"]["user_declared"]:
            key = _canonical({k: v for k, v in item.items() if k != "pointer"})
            if key not in found:
                found[key] = (item, [])
            found[key][1].append(index)
    return [
        {**item, "points": _points_of(indices, order)}
        for item, indices in found.values()
    ]


def _sweep_checks(reports: Sequence[KeyRateReport]) -> list[Check]:
    """Return each check once: its outcome, or ``varies`` with every point's."""
    result: list[Check] = []
    for index, check in enumerate(reports[0]["sections"]["checks"]["checks"]):
        others = [report["sections"]["checks"]["checks"][index] for report in reports]
        merged: Check = {**check}
        if len({_canonical(other["value"]) for other in others}) > 1:
            merged["value"] = None
            merged["value_varies"] = True
        outcomes = [other["outcome"] for other in others]
        if len(set(outcomes)) > 1:
            merged["outcome"] = "varies"
            merged["point_outcomes"] = [
                outcome for outcome in outcomes if outcome != "varies"
            ]
            merged["pointer"] = None
        result.append(merged)
    return result


def _sweep_trusted(reports: Sequence[KeyRateReport]) -> bool | None:
    """Return the points' source trust where every point records the same one."""
    found = {
        None if report["sections"]["setup"]["source"] is None
        else report["sections"]["setup"]["source"]["trusted"]
        for report in reports
    }
    return next(iter(found)) if len(found) == 1 else None


def _snap_status(report: KeyRateReport) -> tuple[bool | None, int, int]:
    """Return whether a point rests on A-SNAP, on how many blocks and sectors.

    The blocks are its stations'; the sectors are the reduction's emission's.
    """
    snaps = report["sections"]["protocol"]["measurement_snaps"]
    if snaps is None:
        return None, 0, 0
    resting = sum(1 for row in snaps["rows"] if row["rests_on_assumption"])
    return (snaps["rests_on_a_snap"], resting,
            len(resting_sectors(snaps["emission"])))


def _instance_key(record: Mapping[str, Any]) -> str | None:
    instance = record["payload"].get("instance")
    return str(instance["id"]) if isinstance(instance, Mapping) else None


def build_sweep_report(
    records: Sequence[Mapping[str, Any]],
    *,
    labels: Sequence[str] | None = None,
    table: Mapping[str, Any] | None = None,
) -> SweepReport:
    """Return the report of a sweep: what is shown once, what varies, the points.

    Every record must be a current run record of one instance
    (``mixed_instances`` otherwise). The varying inputs are inferred by
    comparing every point's input rows; ``labels`` (for instance a
    caller's run ids) name the points.

    THE PREMISES ARE THE UNION over the completed points, never their
    intersection: an evaluator reading the sweep must be told of every
    premise any point rests on. Each entry (and each row not engaged,
    discharged or in disagreement, and each not-counted flag) carries
    ``points``: ``"all"`` when every completed point carries it, else the
    point indices. A point's own ``flags`` are those it raises that not every
    completed point does. A check whose outcome differs reads ``varies`` with
    ``point_outcomes``.

    A refused point is listed with its refusal and no route. The common
    route is the signature most completed points share (ties to the lowest
    index); a point on another route is flagged with the ids it adds and
    lacks. No field adds ε over points.
    """
    records = [_check_record(record) for record in records]
    if not records:
        raise ReportInputError("no_records", "a sweep report needs at least one record")
    if labels is not None and len(labels) != len(records):
        raise ReportInputError(
            "labels_mismatch",
            f"{len(labels)} labels for {len(records)} records",
        )
    instances = sorted({str(_instance_key(record)) for record in records})
    if len(instances) > 1:
        raise ReportInputError(
            "mixed_instances",
            f"the records belong to different instances: {', '.join(instances)}",
        )
    resolved = closure_table() if table is None else table
    reports = [build_report(record, table=resolved) for record in records]

    rows = [
        {row["name"]: row for row in report["sections"]["protocol"]["inputs"]}
        for report in reports
    ]
    names = list(dict.fromkeys(name for found in rows for name in found))
    varying = [
        name for name in names
        if len({
            _canonical(found[name]["value"]) if name in found else "\0missing"
            for found in rows
        }) > 1
    ]
    first = reports[0]["sections"]
    completed = {
        index: report for index, report in enumerate(reports)
        if report["sections"]["result"]["outcome"] != "refused"
    }
    order = _Table(resolved).order

    def union_rows(section: str, block: str) -> list[Any]:
        sections: dict[int, Mapping[str, Any]] = {
            index: report["sections"] for index, report in completed.items()
        }
        return _union_rows({
            index: found[section][block] for index, found in sections.items()
        })

    provenance: dict[str, Any] = {}
    fields: list[Mapping[str, Any]] = [
        report["sections"]["provenance"] for report in reports
    ]
    for name in ("engine", "module_versions", "solver", "platform", "created_by"):
        if len({_canonical(found[name]) for found in fields}) == 1:
            provenance[name] = fields[0][name]

    not_counted = _union_flags({
        index: report["sections"]["result"]["not_counted"]
        for index, report in completed.items()
    })
    shown_point = min(completed) if completed else None
    keyed = [
        index for index in sorted(completed)
        if reports[index]["sections"]["result"]["outcome"] == "key-length"
    ]
    common_part: CommonPart = {
        "setup": (
            None if shown_point is None
            else reports[shown_point]["sections"]["setup"]
        ),
        "setup_point": shown_point,
        "guarantee": (
            None if not keyed
            else reports[keyed[0]]["sections"]["summary"]["guarantee"]
        ),
        "instance": first["protocol"]["instance"],
        "inputs": [
            rows[0][name] for name in names
            if name not in varying and name in rows[0]
        ],
        "not_counted": not_counted,
        "user_declared": _union_declared(reports, completed),
        "limitations": first["result"]["limitations"],
        "per_execution": first["result"]["per_execution"],
        "assumptions": {
            "groups": _groups(
                _union_entries({
                    index: group_entries(report["sections"]["assumptions"]["groups"])
                    for index, report in completed.items()
                }),
                order,
                _sweep_trusted(list(completed.values())),
            ),
            "not_engaged": union_rows("assumptions", "not_engaged"),
            "discrepancies": union_rows("assumptions", "discrepancies"),
            "user_declared": _union_declared(reports, completed),
        },
        "numerics": {
            "entries": _union_entries({
                index: report["sections"]["numerics"]["entries"]
                for index, report in completed.items()
            }),
            "diagnostics": {},
            "explained": [],
            "solver_attempts": [],
            "solve_stop": None,
            "alpha_search": None,
        },
        "checks": _sweep_checks(reports),
        "discharged_on_route": union_rows("checks", "discharged_on_route"),
        "decided_rows": _union_entries({
            index: report["sections"]["checks"]["decided_rows"]
            for index, report in completed.items()
        }),
        "provenance": provenance,
    }

    routes = {
        index: _route(report)
        for index, report in enumerate(reports)
        if report["sections"]["result"]["outcome"] != "refused"
    }
    counts = Counter(signature for signature, _ in routes.values())
    common_signature: str | None = None
    common_ids: frozenset[str] = frozenset()
    if counts:
        top = max(counts.values())
        for index in sorted(routes):
            signature, engaged = routes[index]
            if counts[signature] == top:
                common_signature, common_ids = signature, engaged
                break

    common_flags = {flag["id"] for flag in not_counted if flag.get("points") == "all"}
    points: list[SweepPoint] = []
    for index, (record, report) in enumerate(zip(records, reports, strict=True)):
        result = report["sections"]["result"]
        route = routes.get(index)
        point_signature = None if route is None else route[0]
        point_ids = frozenset() if route is None else route[1]
        security = result["security_parameter"]["value"]
        points.append(
            {
                "index": index,
                "label": None if labels is None else str(labels[index]),
                "record_id": record_id(record),
                "values": {
                    name: rows[index][name]["value"] if name in rows[index] else None
                    for name in varying
                },
                "outcome": result["outcome"],
                "key_length": result["key_length"],
                "net_key_length": result["net_key_length"],
                "rate_per_round": result["rate_per_round"],
                "reported_tier": result["reported_tier"],
                "security_parameter": security,
                "refusal": result["refusal"],
                "route_signature": point_signature,
                "route_differs": (
                    route is not None and point_signature != common_signature
                ),
                "route_delta": {
                    "added": [] if route is None else sorted(point_ids - common_ids),
                    "removed": [] if route is None else sorted(common_ids - point_ids),
                },
                "flags": sorted(
                    flag["id"] for flag in result["not_counted"]
                    if flag["id"] not in common_flags
                ),
                "rests_on_a_snap": _snap_status(report)[0],
                "resting_blocks": _snap_status(report)[1],
                "resting_sectors": _snap_status(report)[2],
            }
        )

    index_claims: dict[str, ClaimRef] = {}
    index_owners: dict[str, str] = {}
    index_mentions: dict[str, ContractAnchor] = {}
    for report in reports:
        index_claims.update(report["index"]["claims"])
        index_owners.update(report["index"]["assumptions"])
        index_mentions.update(report["index"].get("mentions") or {})
    digest = hashlib.sha256(
        "\n".join(point["record_id"] for point in points).encode("utf-8")
    ).hexdigest()
    return {
        "kind": "key-rate-sweep-report",
        "report_schema_version": REPORT_SCHEMA_VERSION,
        # The points' record schema; several, comma-separated, where a sweep
        # mixes the two shapes this builder reads.
        "record_schema_version": ", ".join(
            sorted({str(record["schema_version"]) for record in records})
        ),
        "id": digest,
        "common": common_part,
        "varying": varying,
        "points": points,
        "index": {
            "claims": {key: index_claims[key] for key in sorted(index_claims)},
            "assumptions": {key: index_owners[key] for key in sorted(index_owners)},
            "mentions": {key: index_mentions[key] for key in sorted(index_mentions)},
        },
    }
