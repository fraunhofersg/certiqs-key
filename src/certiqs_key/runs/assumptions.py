"""The route-exact assumption set of one run, from one reconciled list.

WHY THIS EXISTS. The report lists the route-exact set from one reconciled
list. That set is the closure of the run's actual top-level results, extended
beyond meat-core to the device-side modules and filtered by the route's
emission rules. A test fails when ledger rows and closure disagree. A listing
of one row per emitter and per machine key, read from five ledgers that
nothing compared with the claim graph, would leave a row no claim of the run
rests on (the inherited A-TSM of a route without a squasher) and a premise the
graph names but no ledger emitted both invisible.

THE SHAPE. Two adapters read a finished run, and one pure function reconciles:

* :func:`emitted_rows` -- every ledger row every emitter of the run emitted,
  as :class:`EmittedRow`, with the declared values each row binds;
* :func:`run_claim_roots` -- per module, the top-level results THIS run used,
  chosen by the route (each rule's claim basis is in its helper's docstring);
* :func:`route_exact_assumptions` -- pure, so a test feeds it synthetic rows:
  resolves every row to its short id (fail-closed), takes the union of the
  roots' assumption closures from the shipped claim-closure table,
  deduplicates across emitters, sorts each engaged assumption into
  premises or trusted numerics, lists the closure members a module that ran
  did not emit as not engaged, and records every disagreement.

DISCREPANCIES ARE RECORDED, NOT REFUSED. Listing an extra premise
is the safe direction and refusing a key rate over bookkeeping is not, so a
disagreement goes into :attr:`RouteExactSet.discrepancies` and the report shows
it; ``tests/unit/test_ledger_closure_agree.py`` makes it fatal in CI. An
UNKNOWN machine key, or a short id an emitter gives that the table maps to
another key, stays fatal at runtime (:class:`ClaimClosureError`), as it was in
the record: a row whose owner cannot be read carries no mark.

WHAT THIS MODULE DOES NOT DO. It computes no closure (the table is generated
by ``harness/generate_claim_closure.py`` from ``harness/check_claims.py``'s
graph), authors no assumption text (the snapshot is the table's), and decides
no emission rule (an emitter decides which rows it emits; this module only
reads what it emitted and says where that disagrees with the graph).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

from certiqs_key.domain.claim_closure import (
    ACCEPTANCE_ROOTS,
    COMPANION_ROOTS,
    COMPOSITION_ROOTS,
    CORRECTNESS_ROOTS,
    SECRECY_ROOTS,
    TABLE_NAME,
    VERIFICATIONS,
    ClaimClosureError,
    assumption_info,
    claim_closure,
    closure_table,
    roots_of_module,
)
from certiqs_key.meat_core.reasons import (
    ASSUMPTION_MACHINE_KEYS as MEAT_CORE_KEYS,
)
from certiqs_key.meat_core.reasons import (
    INHERITED_KEYS as MEAT_CORE_INHERITED_KEYS,
)
from certiqs_key.protocol_compiler.compile import public_choice_declared
from certiqs_key.protocol_compiler.declared_premises import band_a_route
from certiqs_key.protocol_compiler.reasons import (
    ASSUMPTION_MACHINE_KEYS as COMPILER_KEYS,
)
from certiqs_key.protocol_compiler.reasons import (
    INHERITED_KEYS as COMPILER_INHERITED_KEYS,
)
from certiqs_key.receiver.reasons import (
    ASSUMPTION_MACHINE_KEYS as RECEIVER_KEYS,
)
from certiqs_key.receiver.reasons import CONDITIONALLY_INVOKED
from certiqs_key.reductions.reasons import (
    ASSUMED_FROM_FOUNDATIONS as REDUCTIONS_FOUNDATIONS_KEYS,
)
from certiqs_key.reductions.reasons import (
    ASSUMPTION_MACHINE_KEYS as REDUCTIONS_KEYS,
)
from certiqs_key.reductions.reasons import SNAPPED_MEASUREMENT_ROW, LinkKind
from certiqs_key.runs.direct_route import (
    EVALUATED_OFF_CONDITION,
    StationEvaluation,
    direct_route,
    resting_names,
)
from certiqs_key.runs.errors import RunError
from certiqs_key.statistics.ledger import LEDGER_IDS as STATISTICS_IDS
from certiqs_key.statistics.ledger import AcceptanceRoute
from certiqs_key.transmitter.decoy.emit import artifact_admits_source_segment
from certiqs_key.transmitter.decoy.reasons import DECOY_ASSUMPTION_MACHINE_KEYS
from certiqs_key.transmitter.reasons import (
    ASSUMPTION_MACHINE_KEYS as TRANSMITTER_KEYS,
)
from certiqs_key.transmitter.reasons import SourceMode

if TYPE_CHECKING:
    from certiqs_key.protocol_compiler.spec import ProtocolSpecification
    from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
    from certiqs_key.reductions.artifact import ProofReductionArtifact
    from certiqs_key.runs.pipeline import SliceResult
    from certiqs_key.runs.wire import WireLabels
    from certiqs_key.transmitter.artifact import TransmitterArtifact

__all__ = [
    "CARRIED_ROWS",
    "COVERING_REFINEMENTS",
    "DISCHARGED_ON_ROUTE",
    "LEDGER_VOCABULARIES",
    "MODULE_ORDER",
    "STATISTICS_ROOTS",
    "AssumptionEntry",
    "Discrepancy",
    "DiscrepancyKind",
    "EmittedRow",
    "NotEngaged",
    "RouteExactSet",
    "Section",
    "attribution_roots",
    "emitted_rows",
    "meat_core_roots",
    "route_exact_assumptions",
    "run_claim_roots",
]


# ---------------------------------------------------------------------------
#  Vocabulary
# ---------------------------------------------------------------------------

#: The modules a run composes, in the order the record lists their ledgers.
#: A module outside this list (a test's) sorts after them, by name.
MODULE_ORDER: Final[tuple[str, ...]] = (
    "protocol-compiler",
    "transmitter",
    "receiver",
    "reductions",
    "statistics",
    "meat-core",
)


class Section(StrEnum):
    """Where an engaged assumption is listed.

    TWO SECTIONS. There is no ``checks`` section for a row whose
    ``verification`` is ``decided`` or ``discharged``: those values are
    refused on every assumption (an engine-decided condition is a definition
    plus a requirement, a discharged one a lemma) and are outside the
    package's vocabulary (``claim_closure.VERIFICATIONS``), so no entry could
    land there. The conditions the engine decides are the
    report's check table (``runs/report/checks.py``), not assumptions.
    """

    #: A premise the user vouches for (``verification`` ``never`` or ``partly``).
    ASSUMPTIONS = "assumptions"
    #: A premise about the engine's own arithmetic (category ``numerical-trust``).
    NUMERICS = "numerics"


class DiscrepancyKind(StrEnum):
    """The disagreements between ledger rows and claim closure this records."""

    #: An engaged premise no root of the run assumes. Still listed among the
    #: assumptions: overstating is the safe direction.
    EMITTED_NOT_IN_CLOSURE = "emitted_not_in_closure"
    #: A closure member that no module which ran can emit: a premise the run
    #: rests on that nothing emitted.
    IN_CLOSURE_NO_EMITTER = "in_closure_no_emitter"
    #: A row a root of the run discharges on this route that an emitter still
    #: emitted (A-LINK on Band A).
    EMITTED_WHERE_DISCHARGED = "emitted_where_discharged"


_NUMERICAL_CATEGORY: Final[str] = "numerical-trust"

#: How a not-engaged row quotes the emission rule of the module that did not
#: emit it: the rule states when the row is emitted, so it is introduced as
#: the rule and followed by the fact that this route does not meet it.
_RULE_PREFIX: Final[str] = "emission rule: "
_RULE_SUFFIX: Final[str] = "; not met on this route"

#: EMISSION RULES THAT NAME A SOURCE, NOT A CONDITION, with the reason a
#: not-engaged row of that module reads instead. The compiler's rule for the
#: transmitter's rows says where they come from ("read off the transmitter
#: artefact's own ledger"), not when they are emitted, so "not met on this
#: route" would read wrong; the row is absent because the transmitter's
#: ledger did not carry it.
_SOURCE_RULE_REASONS: Final[Mapping[str, str]] = MappingProxyType({
    "read off the transmitter artefact's own ledger":
        "not on the transmitter artefact's ledger on this route",
})


def _reductions_vocabulary() -> frozenset[str]:
    """Return the core's ids, foundations' it carries, and reductions-owned ids.

    A removable submodule's rows are carried on the reductions artefact, and
    no tier outside that submodule may spell them (its isolation test), so
    they are read from the table by owner rather than imported.

    Foundations' A-SNAP (``reductions.reasons.ASSUMED_FROM_FOUNDATIONS``) is
    emitted by this ledger under its presence rule: present exactly where the
    emission record names a moved class, or the declaring party's snap record
    a moved block, as resting on it (``reductions/req:emission-record``;
    ``reductions/thm:emit`` (vi)). Because ``reductions/thm:emit`` (vi)
    assumes it, it is in the closure
    of the reductions device roots, so a run that names no resting block lists
    it as not engaged here, as A-SRC is listed where its source segment is
    empty, rather than as a closure member no module can emit.
    """
    owned = {
        short_id
        for short_id, row in closure_table().get("assumptions", {}).items()
        if isinstance(row, Mapping)
        and str(row.get("owner", "")).startswith("reductions/")
    }
    return frozenset(
        {str(member) for member in REDUCTIONS_KEYS}
        | set(REDUCTIONS_FOUNDATIONS_KEYS)
        | owned
    )


#: PER MODULE, EVERY SHORT ID ITS LEDGER CAN EMIT, read from the emitter's own
#: constants (its ``AssumptionId``, its machine-key table, its inherited
#: keys). An id in the vocabulary of a module that ran, in
#: the closure of the run, and not emitted, was excluded by that module's
#: emission rule on this route: it is listed as not engaged, with the rule's
#: text from the table where the interface states one.
LEDGER_VOCABULARIES: Final[Mapping[str, frozenset[str]]] = MappingProxyType({
    "protocol-compiler": frozenset(
        {str(member) for member in COMPILER_KEYS} | set(COMPILER_INHERITED_KEYS)
    ),
    "transmitter": frozenset(
        {str(member) for member in TRANSMITTER_KEYS}
        | {str(member) for member in DECOY_ASSUMPTION_MACHINE_KEYS}
    ),
    "receiver": frozenset(str(member) for member in RECEIVER_KEYS),
    "reductions": _reductions_vocabulary(),
    "statistics": frozenset(STATISTICS_IDS),
    # A-LMO is in no vocabulary: the frank-wolfe submodule's one assumption is
    # superseded and its ledger emits it on no run
    # (meat-core/frank-wolfe/req:verified-feasible-side).
    "meat-core": frozenset(
        {str(member) for member in MEAT_CORE_KEYS} | set(MEAT_CORE_INHERITED_KEYS)
    ),
})

#: ROWS A ROOT OF THE RUN DISCHARGES ON ITS ROUTE: when the root is among the
#: run's roots, the listed ids are not a premise of the run. A row so
#: discharged and not emitted is listed as not engaged with ``discharged_by``;
#: one still emitted is a discrepancy
#: (:attr:`DiscrepancyKind.EMITTED_WHERE_DISCHARGED`) until its emitter omits
#: it. An entry is added only where the claim graph says so: a root whose
#: header still ``assumes`` an id does not discharge it.
#:
#: THREE ROOTS: TWO DISCHARGING A-LINK, ONE A-RECV.
#:
#: A-LINK on Band A by ``protocol-compiler/thm:band-a``,
#: whose header assumes A-IDEAL alone. That theorem's part (v) proves that the Band-A
#: identity link satisfies every clause of A-LINK; ``ass:link``'s lead-in says
#: the same ("On the Band-A identity link, declared directly, every clause
#: holds by exhibition"). The
#: compiler omits its A-LINK row on Band A. A Band-A
#: route with a public choice still reaches A-LINK through
#: ``thm:choice-encoding``, which assumes it; this entry is what removes it
#: there, with ``thm:band-a`` (v) as the reason.
#:
#: A-LINK on an in-run single exact instance link by
#: ``protocol-compiler/req:link-row-provenance`` (ii). The map is keyed on a root and
#: unconditional, so the key is the REQUIREMENT and not ``thm:chain-consumption``, which
#: is a root on every consumed chain, hand-written ones included: the run names the
#: requirement as a root exactly where the compiler omitted the row under (ii)
#: (:func:`run_claim_roots`), and its header assumes nothing, A-LINK least of
#: all. It uses the reductions theorems that prove every clause
#: (``rem:obligations-discharged``), so the not-engaged A-LINK row names it as
#: what discharges the row on that route.
#:
#: A-RECV on an exact, rigorously evaluated receiver artefact the run built,
#: by ``reductions/req:recv-row-provenance``, the precedent above taken over
#: to the supplier row. The key is the REQUIREMENT and not a reductions
#: emission result, which is a root on every supplied artefact, an external
#: one included, and whose header assumes A-RECV: the run names the
#: requirement as a root exactly where every reductions artefact of the run
#: omitted its A-RECV row under it (:func:`run_claim_roots`), and its header
#: assumes nothing, A-RECV least of all. It uses the receiver theorems that
#: prove both clauses there, under the receiver's own ledger, which the run
#: lists, so the not-engaged A-RECV row names it as what discharges the row.
#: A run with one station whose row was omitted and one whose row was not
#: does not name it: the second station's A-RECV is a premise of the run, and
#: it covers the first.
#:
#: A-PRESENT IS NOT IN THIS MAP: its content is clause (iv) of
#: ``protocol-compiler/def:well-formed-spec``, decided on every route
#: (``req:physical-family-decision``), and no claim assumes it.
DISCHARGED_ON_ROUTE: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "protocol-compiler/thm:band-a": ("A-LINK",),
        "protocol-compiler/req:link-row-provenance": ("A-LINK",),
        "reductions/req:recv-row-provenance": ("A-RECV",),
    }
)

#: THE REFINING ASSUMPTIONS THAT COVER THEIR PARENT where they are engaged:
#: the parent is the table's ``refines`` of the member, read there and not
#: here. A parent so covered is in the closure, emitted by no module, and
#: neither listed as not engaged nor a discrepancy, because the user vouches
#: for it in the refining assumption's words.
#:
#: ONE MEMBER, A-WCP. A
#: specification declared by a source model carries A-WCP in A-ENS's place
#: (``transmitter/def:source-spec`` (b)), and A-WCP's last three clauses are
#: A-ENS's for the model's states (``meat-core/lem:product-marginal``'s
#: lead-in), so on a decoy route, where the transmitter emits A-WCP and not
#: A-ENS, the run's A-ENS is A-WCP's. ``refines`` ALONE IS NOT ENOUGH: it
#: says a member narrows its parent, not that it carries every clause of it
#: (A-ALICE-MEAS narrows A-SPEC to one of its parts), so a member is added
#: here only where its statement restates the whole parent.
COVERING_REFINEMENTS: Final[frozenset[str]] = frozenset({"A-WCP"})


# ---------------------------------------------------------------------------
#  Rows
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EmittedRow:
    """One ledger row one emitter of the run emitted.

    ``bindings`` are the emitter's own immutable ``(name, value)`` pairs (the
    receiver's, reductions' and statistics' ``constrains``); they are made
    JSON-ready only in :meth:`RouteExactSet.as_payload`. ``engaged`` is False
    only where the emitter declares the row conditionally invoked and it was
    not invoked on this run; ``condition`` is then the emitter's own statement
    of when it is.
    """

    machine_key: str
    #: The emitting module: ``"meat-core"``, ``"protocol-compiler"``, ...
    emitted_by: str
    #: The station of a per-station receiver or reductions row; ``None`` on the
    #: single-device route and for every other module.
    station: int | None = None
    #: The party (``"A"`` or ``"B"``) of a row its emitter emits once per party
    #: of the declaration -- meat-core's A-LAB (``meat-core/ass:lab``; record
    #: 0.30.0) -- read from the row's own ``party`` binding; ``None`` on every
    #: other row.
    party: str | None = None
    #: The short id as the emitter gave it; ``None`` for a bare-key emitter.
    short_id: str | None = None
    bindings: tuple[tuple[str, object], ...] = ()
    #: The supplier version a reductions A-RECV row was accepted against.
    inherited_from: str | None = None
    engaged: bool = True
    condition: str | None = None


def _conditional_engagement(
    short_id: str, constrains: Sequence[tuple[str, object]]
) -> tuple[bool, str | None]:
    """Whether a receiver row is engaged, from the receiver's own declaration.

    ``receiver.reasons.CONDITIONALLY_INVOKED`` names the one row invoked
    conditionally, A-EIG, "exactly at the settings whose declaration carries an
    exact_window depth (Ass. ass:eig; Def. def:pmcex)"; the row binds
    ``invoked_at``, the list of those settings, so an empty list is a row not
    invoked on this run.
    """
    conditions = {str(member): text for member, text in CONDITIONALLY_INVOKED.items()}
    if short_id not in conditions:
        return True, None
    invoked = dict(constrains).get("invoked_at")
    engaged = bool(invoked) if isinstance(invoked, Sequence) else True
    return engaged, conditions[short_id]


def _receiver_rows(
    artifact: ReceiverMeasurementArtifact, station: int | None
) -> list[EmittedRow]:
    rows = []
    for record in artifact.assumption_ledger:
        short_id = str(record.assumption_id)
        engaged, condition = _conditional_engagement(short_id, record.constrains)
        rows.append(
            EmittedRow(
                machine_key=record.machine_key,
                emitted_by="receiver",
                station=station,
                short_id=short_id,
                bindings=tuple(record.constrains),
                engaged=engaged,
                condition=None if engaged else condition,
            )
        )
    return rows


def _reductions_rows(
    artifact: ProofReductionArtifact,
    station: int | None,
    evaluation: StationEvaluation | None = None,
) -> list[EmittedRow]:
    """Return one reductions artefact's ledger rows, A-SNAP as the run decided it.

    The artefact names its moved blocks and sectors when it is emitted, and
    that naming is provisional (``reductions/req:emission-record``): A-SNAP is
    engaged only for the blocks and sectors the run did NOT evaluate off their
    snap (``foundations/ass:snapped-measurement``; ``meat-core/frank-wolfe/
    req:bracket-on-reference`` (v); :mod:`certiqs_key.runs.direct_route`).
    Where the run names at least one block and every named one was, the row is
    listed as not engaged with that condition; otherwise its binding names
    those that rest, each with its group and cause
    (``foundations/req:snap-reference`` (iii)); where none is named, the row
    stands as emitted.
    """
    rows = []
    for entry in artifact.assumption_ledger:
        bindings = tuple(entry.constrains)
        engaged, condition = True, None
        if (
            entry.assumption_id == SNAPPED_MEASUREMENT_ROW.identifier
            and evaluation is not None
        ):
            remaining = resting_names(evaluation)
            # Disengaged only where the run names some block and every named
            # one was evaluated off its snap: a
            # row whose record names nothing stays engaged as emitted, so the
            # condition below is never cited where it does not hold.
            if evaluation.named and all(
                block.evaluated_off_snap for block in evaluation.named
            ):
                engaged, condition = False, EVALUATED_OFF_CONDITION
            elif remaining:
                bindings = (("resting_blocks", remaining),)
        rows.append(
            EmittedRow(
                machine_key=entry.machine_key,
                emitted_by="reductions",
                station=station,
                short_id=entry.assumption_id,
                bindings=bindings,
                inherited_from=entry.inherited_from,
                engaged=engaged,
                condition=condition,
            )
        )
    return rows


#: THE ENGINE'S BINDINGS THAT SPELL A LABEL, by binding name, with the
#: :class:`~certiqs_key.runs.wire.WireLabels` bijection their ``alphabet``
#: part went through. The engine binds the declaration it read back off the
#: bundle (``meat-core``'s ``declared_values``), and on the wire every label is
#: a stable ID (``runs/identifiers.py``: ``(Z,0)`` travels as ``_Z_0_``,
#: ``gen:Z|X`` as ``gen_Z_X``). The compiler and the transmitter bind the
#: same objects in the declared spelling, and the record's acceptance stage
#: holds the declared outcomes, so the run tier maps the engine's IDs back
#: through the run's own bijection before the rows are joined: one value per
#: name, in the declared spelling.
_WIRE_SPELLED: Final[Mapping[str, str]] = MappingProxyType({
    "alice_povm": "alice_outcome",
    "acceptance_set": "acceptance_value",
})


def _declared_spelling(
    bindings: Sequence[tuple[str, object]], labels: WireLabels
) -> tuple[tuple[str, object], ...]:
    """Return the engine's bindings with every wire ID in its declared spelling.

    Only the ``alphabet`` part of a name in :data:`_WIRE_SPELLED` is touched,
    each letter replaced by the label the run's bijection maps to it. A
    letter the bijection does not reach raises :class:`RunError`: a binding
    the run cannot read back is not one it may record under a declared name.
    So does a value of such a name that is not a tuple of ``(part, value)``
    pairs with exactly one ``alphabet`` part, itself a tuple: the engine
    binds that shape, and any other would pass through unread, wire IDs and
    all (fail closed).
    """
    spelled: list[tuple[str, object]] = []
    for name, value in bindings:
        alphabet = _WIRE_SPELLED.get(str(name))
        if alphabet is not None:
            pairs = _wire_spelled_pairs(str(name), value)
            inverse = {
                wire: label for label, wire in getattr(labels, alphabet).items()
            }
            parts: list[tuple[object, object]] = []
            for part, item in pairs:
                if part == "alphabet" and isinstance(item, tuple):
                    unknown = [letter for letter in item if letter not in inverse]
                    if unknown:
                        raise RunError(
                            f"the engine bound {name} over the letters {unknown}, "
                            f"which the run's {alphabet} bijection does not "
                            "reach; the declared spelling cannot be recovered"
                        )
                    item = tuple(inverse[letter] for letter in item)
                parts.append((part, item))
            value = tuple(parts)
        spelled.append((name, value))
    return tuple(spelled)


def _wire_spelled_pairs(
    name: str, value: object
) -> tuple[tuple[object, object], ...]:
    """Return a label-bearing binding's pairs, or refuse a shape it cannot read.

    The shape :func:`_declared_spelling` maps: a tuple of ``(part, value)``
    pairs, exactly one of them ``alphabet`` with a tuple value.
    """
    if not (
        isinstance(value, tuple)
        and all(isinstance(pair, tuple) and len(pair) == 2 for pair in value)
    ):
        raise RunError(
            f"the engine bound {name} as {value!r}, not a tuple of (part, value) "
            "pairs; the declared spelling cannot be recovered"
        )
    alphabets = [item for part, item in value if part == "alphabet"]
    if len(alphabets) != 1 or not isinstance(alphabets[0], tuple):
        raise RunError(
            f"the engine bound {name} without exactly one alphabet part that is "
            f"a tuple (found {alphabets!r}); the declared spelling cannot be "
            "recovered"
        )
    return tuple((part, item) for part, item in value)


def emitted_rows(result: SliceResult) -> tuple[EmittedRow, ...]:
    """Return every ledger row every emitter of a finished run emitted.

    In the record's order: the compiler's own rows, the transmitter's (which
    reach the run through the compiler's copy of the transmitter artefact's
    ledger, "copied in its order and not re-derived", and are attributed to
    the transmitter that emitted them), the single-device route's reductions
    and receiver artefacts, each station's receiver and reductions artefacts,
    statistics' rows and the engine's keys.

    The compiler and the engine emit bare keys (``short_id`` ``None``); the
    receiver, reductions and statistics emit short ids with their
    ``constrains``. The compiler's, the transmitter's and the engine's
    bindings travel beside their ledgers (``assumption_bindings``, keyed by
    machine key). The engine's are put back
    into the declared spelling first (:data:`_WIRE_SPELLED`).
    """
    rows: list[EmittedRow] = []
    specification = result.specification
    transmitter_keys: tuple[str, ...] = (
        ()
        if specification is None
        else tuple(specification.source.artifact.assumption_ledger)
    )
    transmitter_bindings = (
        {}
        if specification is None
        else dict(specification.source.artifact.assumption_bindings)
    )
    compiler_bindings = dict(result.compilation.assumption_bindings)
    rows.extend(
        EmittedRow(
            machine_key=key,
            emitted_by="protocol-compiler",
            bindings=compiler_bindings.get(key, ()),
        )
        for key in result.compilation.assumption_ledger
        if key not in transmitter_keys
    )
    rows.extend(
        EmittedRow(
            machine_key=key,
            emitted_by="transmitter",
            bindings=transmitter_bindings.get(key, ()),
        )
        for key in transmitter_keys
    )
    decision = direct_route(result)
    if result.reduction_artifact is not None:
        rows.extend(
            _reductions_rows(
                result.reduction_artifact, None, decision.station(None)
            )
        )
    if result.receiver_artifact is not None:
        rows.extend(_receiver_rows(result.receiver_artifact, None))
    for station, emission in enumerate(result.device_artifacts):
        rows.extend(_receiver_rows(emission.receiver, station))
        rows.extend(
            _reductions_rows(emission.reduction, station, decision.station(station))
        )
    rows.extend(
        EmittedRow(
            machine_key=row.machine_key,
            emitted_by="statistics",
            short_id=row.assumption_id,
            bindings=tuple(row.constrains),
        )
        for row in result.acceptance.assumption_ledger
    )
    # ONE ENTRY PER LEDGER ROW, in its order, and not a mapping by key: A-LAB
    # is emitted once per party under one machine key, each row binding its
    # own ``party`` (meat-core/ass:lab). The
    # rows are read off the bindings, so a result whose bindings did not cover
    # its ledger row for row would drop premises; refused here as it is in
    # GeneralKeyRateResult.
    bound_keys = tuple(key for key, _ in result.key_rate.assumption_bindings)
    if bound_keys != tuple(result.key_rate.assumption_ledger):
        raise RunError(
            "the engine's assumption_bindings do not follow its assumption_ledger "
            f"row for row ({list(bound_keys)} against "
            f"{list(result.key_rate.assumption_ledger)}); the manifest would "
            "drop premises"
        )
    rows.extend(
        _engine_row(key, _declared_spelling(bindings, result.labels))
        for key, bindings in result.key_rate.assumption_bindings
    )
    return tuple(rows)


def _engine_row(key: str, bindings: tuple[tuple[str, object], ...]) -> EmittedRow:
    """Return one engine row, naming its party where the row binds one.

    The engine emits A-LAB once per party (``meat_core.reasons.PER_PARTY_ROWS``)
    and binds the party the row is emitted for as ``party`` (the interface's
    ``binds`` for A-LAB); that binding is the row's party here.
    """
    party = next((value for name, value in bindings if name == "party"), None)
    return EmittedRow(
        machine_key=key,
        emitted_by="meat-core",
        party=None if party is None else str(party),
        bindings=bindings,
    )


# ---------------------------------------------------------------------------
#  Roots: the top-level results of this run, per module
# ---------------------------------------------------------------------------

#: The compiler's results on every emitted declaration: the gate outcome table
#: (``thm:gates``), the validator that admitted it (``thm:validator-soundness``),
#: and the three theorems about the emitted slots
#: (``thm:measurements-and-statistics``, ``thm:sifting-and-key``, ``thm:typing``).
_COMPILER_ALWAYS: Final[tuple[str, ...]] = (
    "protocol-compiler/thm:gates",
    "protocol-compiler/thm:validator-soundness",
    "protocol-compiler/thm:measurements-and-statistics",
    "protocol-compiler/thm:sifting-and-key",
    "protocol-compiler/thm:typing",
)
_BAND_A: Final[str] = "protocol-compiler/thm:band-a"
#: The requirement on which the compiler's omission of A-LINK at an in-run
#: single exact instance link rests (req:link-row-provenance (ii)).
_LINK_ROW_PROVENANCE: Final[str] = "protocol-compiler/req:link-row-provenance"
_CHAIN_CONSUMPTION: Final[str] = "protocol-compiler/thm:chain-consumption"
_CHOICE_ENCODING: Final[str] = "protocol-compiler/thm:choice-encoding"

_CERTIFICATE_SUFFICIENCY: Final[str] = "transmitter/thm:certificate-sufficiency"
_SOURCE_REPLACEMENT: Final[str] = "transmitter/fact:sr"
_EMITTED_DECOY: Final[str] = "transmitter/decoy/cor:emitted-decoy"

_EMITTED_UNCONDITIONED: Final[str] = "receiver/cor:emitted-unconditioned"
#: THE REMOVABLE SUBMODULE THAT CONSTRUCTS THE SETTING FAMILY OF A RECEIVER WITH
#: SOURCE MODES, named by its module id alone. Its results are read from the
#: claim-closure table (``roots_of_module``), which carries them only while the
#: submodule is in the tree (``harness/generate_claim_closure.py``,
#: ``REMOVABLE_ROOTS``), so this tier names none of its claims; a root resting
#: on its claims is recognised by its closure (:func:`_rests_on_conditioning`).
_CONDITIONING_SUBMODULE: Final[str] = "receiver/probe-conditioning"

_EMIT: Final[str] = "reductions/thm:emit"
_LICENCE: Final[str] = "reductions/thm:licence"
_FLAT_SUBMODULE: Final[str] = "reductions/wpfss"
_SUPPLIER_ASSUMPTION: Final[str] = "A-RECV"
#: The requirement on which the reductions module's omission of A-RECV at an
#: exact, rigorous in-run receiver artefact rests (req:recv-row-provenance).
_RECV_ROW_PROVENANCE: Final[str] = "reductions/req:recv-row-provenance"

#: The statistics results each acceptance route reports, the roots its
#: ledger's emission rule is the closure of (``statistics/ledger.py``):
#: the constructed box's completeness figure (``binomial-box/thm:completeness-
#: bound``), its honest containment (``binomial-box/thm:honest-containment``)
#: and its acceptance support (``thm:box-oracle`` (i)); a declared singleton's
#: completeness figure (``singleton/thm:singleton-completeness``).
STATISTICS_ROOTS: Final[Mapping[AcceptanceRoute, tuple[str, ...]]] = MappingProxyType({
    AcceptanceRoute.CONSTRUCTED_BOX: (
        "statistics/binomial-box/thm:completeness-bound",
        "statistics/binomial-box/thm:honest-containment",
        *ACCEPTANCE_ROOTS,
    ),
    AcceptanceRoute.DECLARED_SINGLETON: (
        "statistics/singleton/thm:singleton-completeness",
    ),
})


def _compiler_roots(
    specification: ProtocolSpecification, *, link_row_on_provenance: bool = False
) -> tuple[str, ...]:
    """Return the compiler's top-level results for this specification.

    Always :data:`_COMPILER_ALWAYS`. Then ``thm:band-a`` on a Band-A
    specification (``def:banda`` read on the record, by the compiler's own
    :func:`~certiqs_key.protocol_compiler.declared_premises.band_a_route`), else
    ``thm:chain-consumption``, the theorem of a consumed general chain. Then
    ``thm:choice-encoding`` iff a public choice is declared, the theorem that
    a public choice of known bias enters as weights inside the operators.
    Then ``req:link-row-provenance`` where the compiler omitted A-LINK under
    its part (ii) (``link_row_on_provenance``, the compiler's own
    :attr:`~certiqs_key.protocol_compiler.compile.CompilationResult.link_row_omitted_on_provenance`):
    the requirement uses the reductions theorems that prove every clause, so
    naming it puts what the omission rests on into the run's closure.
    """
    roots = list(_COMPILER_ALWAYS)
    roots.append(_BAND_A if band_a_route(specification) else _CHAIN_CONSUMPTION)
    # THE COMPILER'S OWN PREDICATE, the one its A-COIN row is emitted under,
    # and not a copy: a mirror reading the first measured factor only would
    # emit neither A-COIN nor this root for a choice declared at a second
    # station.
    if public_choice_declared(specification):
        roots.append(_CHOICE_ENCODING)
    if link_row_on_provenance:
        roots.append(_LINK_ROW_PROVENANCE)
    return tuple(roots)


def _transmitter_roots(artifact: TransmitterArtifact) -> tuple[str, ...]:
    """Return the transmitter's top-level results for the artefact read.

    A decoy artefact (the decoy submodule's own carrier,
    :func:`~certiqs_key.transmitter.decoy.emit.artifact_admits_source_segment`)
    is ``decoy/cor:emitted-decoy``, "the emitted decoy declaration". Any other
    artefact is the core's emission: ``thm:certificate-sufficiency`` (the
    certificate's checkability and, under retention and sequential rounds,
    source replacement) and ``fact:sr`` (the entanglement-based description of
    a prepare-and-measure source). In
    untrusted mode no certificate is verified; ``thm:certificate-sufficiency``
    then adds only A-SRC to the closure, which the transmitter does not emit
    there and the set lists as not engaged.

    ``fact:sr`` ONLY IN TRUSTED-SOURCE MODE: it describes a source the
    protocol trusts, and in untrusted-source mode no result of the run uses
    it; as a root there it would put A-ENS into the closure, which the
    transmitter does not emit in that mode.
    """
    if artifact_admits_source_segment(artifact):
        return (_EMITTED_DECOY,)
    if artifact.source_mode is not SourceMode.TRUSTED:
        return (_CERTIFICATE_SUFFICIENCY,)
    return (_CERTIFICATE_SUFFICIENCY, _SOURCE_REPLACEMENT)


def _rests_on_conditioning(root: str) -> bool:
    """Return whether a root's closure holds a claim of the conditioning submodule."""
    prefix = _CONDITIONING_SUBMODULE + "/"
    return any(claim.startswith(prefix) for claim in claim_closure(root)["claims"])


def _conditioned_roots(roots: Sequence[str], what: str) -> tuple[str, ...]:
    """Return ``roots`` that rest on the conditioning submodule, or refuse.

    Raises:
        RunError: if none does: the table carries no result for a receiver
            with source modes, because the submodule is not in this tree.
    """
    found = tuple(root for root in roots if _rests_on_conditioning(root))
    if not found:
        raise RunError(
            f"a receiver with source modes ran, and the claim-closure table "
            f"carries no {what} for it: the {_CONDITIONING_SUBMODULE} submodule "
            "is not in this tree (the receiver refuses such a declaration as "
            "probe_conditioning_submodule_absent)"
        )
    return found


def _receiver_root(artifact: ReceiverMeasurementArtifact) -> tuple[str, ...]:
    """Return the receiver's emission corollary for one artefact.

    ``cor:emitted-unconditioned`` for an instrument with ``Inp_S`` empty; for
    one with ``Inp_S`` non-empty (a probe declared), the emission result of
    the submodule that constructs its setting family, read from the table
    (``roots_of_module``): the instance is selected by whether ``Inp_S`` is
    empty, so a run names one closure, not the union. ``Inp_S`` is the
    artefact's ``input_mode_space.source_labels``.
    """
    if artifact.input_mode_space.source_labels:
        return _conditioned_roots(
            roots_of_module(_CONDITIONING_SUBMODULE), "receiver emission result"
        )
    return (_EMITTED_UNCONDITIONED,)


def _reductions_roots(
    artifact: ProofReductionArtifact, *, probe_conditioned: bool = False
) -> tuple[str, ...]:
    """Return the reductions results for one emitted artefact.

    WHICH CONSTRUCTION EMITTED IT. A row the artefact carries whose
    assumption the table gives an owner in a reductions SUBMODULE
    (``reductions/<sub>/...``) names that submodule, whose instance carries
    rows of its own. Otherwise a squashing link of kind ``wpfss`` or
    ``fss`` is the flat instance (``reductions/wpfss``). Otherwise it is the
    core's emission alone.

    WHICH OF THE SUBMODULE'S RESULTS. Its roots in the table
    (:func:`~certiqs_key.domain.claim_closure.roots_of_module`, so that this
    tier names no claim of a removable submodule), those that rest on a
    supplied receiver artefact -- whose closure holds A-RECV,
    ``reductions/ass:recv``, "the receiver artefact accepted" -- when the
    artefact read one, and the others when it read none, such as
    ``wpfss/cor:emitted-flat`` (an optical receiver's family without
    branches) or a submodule's result for its model without a supplier. When
    no submodule root fits, the core's ``thm:emit``, the exact emission of any
    reduction instance.

    WHETHER IT READ ONE is :func:`_reads_a_supplier_artefact`: its A-RECV row
    names a supplier version, or the row is absent because
    ``req:recv-row-provenance`` omitted it, which the artefact records with the
    receiver artefact's version (``receiver_row_omitted_on_provenance``). The
    omitted row changes no root: the results the artefact rests on are those
    of a supplied artefact either way, and A-RECV in their closure is
    discharged by that requirement, which :func:`run_claim_roots` names beside
    them (:data:`DISCHARGED_ON_ROUTE`).

    WHERE THE RECEIVER WAS CONDITIONED ON A PROBE (``probe_conditioned``: a
    receiver artefact of the run has source modes). A root that rests on the
    conditioning submodule's claims is named exactly then, of whichever
    submodule it is a root, and never on a probe-free run. The weight route
    read through the probe-conditioned receiver, a ``wpfss`` result removed
    with that submodule, which names the receiver claims behind the
    conditioned family, is named then on every supplied run, whichever
    submodule emitted the artefact, and its absence from the table is a
    refusal (:func:`_conditioned_roots`). Each is selected by the same
    supplier rule as the others, since it rests on the supplied receiver
    artefact. The flag is the run's, not the station's: on a run with
    stations conditioned and stations not, a probe-free station's reduction
    also names the conditioned roots, which over-names the closure and
    never under-names it.

    ``thm:licence`` is added whenever the artefact carries an attack-set
    licence: it is the theorem of that licence.
    """
    supplied = _reads_a_supplier_artefact(artifact)
    owners = {
        str(assumption_info(entry.assumption_id)["owner"])
        for entry in artifact.assumption_ledger
    }
    submodules = sorted(
        {
            "/".join(owner.split("/")[:2])
            for owner in owners
            if owner.startswith("reductions/") and owner.count("/") >= 2
        }
    )
    if not submodules and any(
        link.kind in (LinkKind.WPFSS, LinkKind.FSS)
        for link in artifact.reduction_chain.links
    ):
        submodules = [_FLAT_SUBMODULE]
    # The direct route's results are named only where the companion's bound
    # counted (run_claim_roots), never by membership of a submodule.
    companion = {root for roots in COMPANION_ROOTS.values() for root in roots}
    candidates = [
        root
        for submodule in submodules
        for root in roots_of_module(submodule)
        if root not in companion
        and (probe_conditioned or not _rests_on_conditioning(root))
    ]
    if probe_conditioned and supplied:
        candidates.extend(
            _conditioned_roots(
                roots_of_module(_FLAT_SUBMODULE), "weight-route result"
            )
        )
    roots = [
        root
        for root in dict.fromkeys(candidates)
        if (_SUPPLIER_ASSUMPTION in claim_closure(root)["assumptions"]) == supplied
    ]
    if not roots:
        roots = [_EMIT]
    if artifact.attack_set_license is not None:
        roots.append(_LICENCE)
    return tuple(roots)


def _reads_a_supplier_artefact(artifact: ProofReductionArtifact) -> bool:
    """Whether a reductions artefact rests on a supplied receiver artefact.

    Its A-RECV row names the supplier version it was accepted against
    (``inherited_from``), or ``req:recv-row-provenance`` omitted that row and
    the artefact records the receiver artefact's version in its
    ``receiver_row_omitted_on_provenance``.
    """
    if artifact.receiver_row_omitted_on_provenance:
        return True
    return any(
        entry.assumption_id == _SUPPLIER_ASSUMPTION and entry.inherited_from is not None
        for entry in artifact.assumption_ledger
    )


def meat_core_roots(
    claim_roots: Sequence[str], *, key_length_reported: bool
) -> tuple[str, ...]:
    """Return the engine's top-level results for one key-rate result.

    The result's own roots, and on a reported length the three properties a
    key length rests on.

    ``claim_roots`` is what the key-rate result names in its certificate
    (``cor:keylength-bound`` with the first-order root on an emitted length,
    ``lem:estimate`` with the first-order root on a bound whose length was
    withheld, ``lem:estimate`` alone otherwise; ``solvers.frank_wolfe.
    general_keyrate.result_claim_roots``). A reported key length is secret
    (``thm:keylength``), correct (``lem:ev-correctness``) and composes with the
    authentication scheme into the security statement the record carries
    (``cor:composed-security`` (iii): ``security_parameter`` and
    ``net_key_length`` are emitted exactly when the length is).
    """
    roots = list(dict.fromkeys(str(root) for root in claim_roots))
    if key_length_reported:
        for root in (*SECRECY_ROOTS, *CORRECTNESS_ROOTS, *COMPOSITION_ROOTS):
            if root not in roots:
                roots.append(root)
    return tuple(roots)


def run_claim_roots(result: SliceResult) -> dict[str, tuple[str, ...]]:
    """Return, per module that ran, the top-level results this run used.

    A module that did not run has no key. Per-station modules (receiver,
    reductions) list the union over their stations, in station order. Each
    rule is a helper here, with its claim basis in its docstring:
    :func:`_compiler_roots`, :func:`_transmitter_roots`,
    :func:`_receiver_root`, :func:`_reductions_roots`,
    :data:`STATISTICS_ROOTS` (a run's acceptance set is always the
    construction map's box, :func:`certiqs_key.statistics.construct`) and
    :func:`meat_core_roots`.

    ``reductions/req:recv-row-provenance`` is named where EVERY reductions
    artefact of the run omitted its A-RECV row under it (each records the
    omission in ``receiver_row_omitted_on_provenance``): the requirement uses
    the receiver theorems that prove both clauses of A-RECV there, so naming
    it puts what the omission rests on into the run's closure, and it
    discharges A-RECV (:data:`DISCHARGED_ON_ROUTE`). Where one station's row
    was emitted, that station's A-RECV is a premise of the run, and the
    requirement is not named.
    """
    specification = result.specification
    if specification is None:
        raise RunError(
            "run_claim_roots reads the compiled specification for the compiler's "
            "Band-A and public-choice rules, and this result carries none"
        )
    roots: dict[str, tuple[str, ...]] = {
        "protocol-compiler": _compiler_roots(
            specification,
            link_row_on_provenance=result.compilation.link_row_omitted_on_provenance,
        ),
        "transmitter": _transmitter_roots(specification.source.artifact),
    }
    receivers = [
        *([] if result.receiver_artifact is None else [result.receiver_artifact]),
        *(emission.receiver for emission in result.device_artifacts),
    ]
    if receivers:
        roots["receiver"] = tuple(
            dict.fromkeys(
                root for artifact in receivers for root in _receiver_root(artifact)
            )
        )
    probe_conditioned = any(
        artifact.input_mode_space.source_labels for artifact in receivers
    )
    reductions = [
        *([] if result.reduction_artifact is None else [result.reduction_artifact]),
        *(emission.reduction for emission in result.device_artifacts),
    ]
    if reductions:
        # THE DIRECT ROUTE'S RESULTS, where the run's first-order number is the
        # bound on the reference companion: the companion of the reduction
        # instance and (H-REF) for the flat instance (COMPANION_ROOTS).
        companion = (
            COMPANION_ROOTS["reductions"] if direct_route(result).counted else ()
        )
        recv_row_omitted = all(
            artifact.receiver_row_omitted_on_provenance for artifact in reductions
        )
        roots["reductions"] = tuple(
            dict.fromkeys(
                (
                    *(
                        root
                        for artifact in reductions
                        for root in _reductions_roots(
                            artifact, probe_conditioned=probe_conditioned
                        )
                    ),
                    *companion,
                    *((_RECV_ROW_PROVENANCE,) if recv_row_omitted else ()),
                )
            )
        )
    roots["statistics"] = STATISTICS_ROOTS[AcceptanceRoute.CONSTRUCTED_BOX]
    roots["meat-core"] = meat_core_roots(
        [str(root) for root in result.key_rate.certificate["claim_roots"]],
        key_length_reported=result.key_rate.key_length is not None,
    )
    return roots


#: THE ROWS A MODULE EMITS FOR A PREMISE ANOTHER MODULE'S RESULT RESTS ON:
#: ``{emitting module: {short id: (carrying modules, ...)}}``. Such a row is
#: attributed to the roots of the carrying modules as well as to the
#: emitter's own (:func:`attribution_roots`), because no result of the
#: emitter spends it.
#:
#: THE COMPILER'S ONE PASS-THROUGH ROW. The compiler's own results do not
#: rest on it: ``thm:typing``, ``thm:sifting-and-key`` and
#: ``thm:measurements-and-statistics`` assume ``ass:spec`` alone. The compiler
#: still emits the row, because it is the module that holds the declaration
#: it describes:
#:
#: * ``A-ALICE-MEAS``, Alice's declared measurement, where no
#:   source-replacement certificate is demanded. ``meat-core/thm:keylength``
#:   assumes it (with ``cor:keylength-bound`` and ``cor:composed-security``),
#:   and the engine has no row of its own for it (the meat-core interface's
#:   ``a_link_note`` and ``a_spec_note``), so it is attributed to meat-core.
#:   On a run that reports no key length no result rests on it, and the row
#:   is then outside the run's closure: recorded as
#:   ``emitted_not_in_closure``, the safe direction.
#:
#: A-RECV IS NO LONGER AMONG THEM: the compiler emits no row of it on any
#: route (its interface's ``assumption_ledger.a_recv_not_emitted_note``), and
#: the row is the reductions artefact's own, attributed to that module's
#: roots.
CARRIED_ROWS: Final[Mapping[str, Mapping[str, tuple[str, ...]]]] = MappingProxyType(
    {
        "protocol-compiler": MappingProxyType(
            {
                "A-ALICE-MEAS": ("meat-core",),
            }
        ),
    }
)


def attribution_roots(
    module: str,
    short_id: str,
    roots: Mapping[str, Sequence[str]],
    *,
    carried: Mapping[str, Mapping[str, Sequence[str]]] = CARRIED_ROWS,
) -> tuple[str, ...]:
    """Return the roots a module's row for ``short_id`` is attributed to.

    The module's own roots in ``roots`` (:func:`run_claim_roots`), and, for a
    row the module emits for another module's result (:data:`CARRIED_ROWS`),
    the carrying modules' roots of the same run after them. A row lies where
    it should when its assumption is in the closure of one of these roots;
    the whole run's closure (:func:`route_exact_assumptions`) is their union
    over every module and does not depend on the attribution.
    """
    carriers = carried.get(module, {}).get(short_id, ())
    return tuple(
        dict.fromkeys(
            (
                *(str(root) for root in roots.get(module, ())),
                *(
                    str(root)
                    for carrier in carriers
                    for root in roots.get(carrier, ())
                ),
            )
        )
    )


# ---------------------------------------------------------------------------
#  The reconciled set
# ---------------------------------------------------------------------------


#: One emitter of a row: ``(module, station, party)``. ``station`` names a
#: per-station row's station, ``party`` a per-party row's party (record
#: 0.30.0); each is ``None`` elsewhere.
type Emitter = tuple[str, int | None, str | None]


def _emitter_payload(emitter: Emitter) -> dict[str, Any]:
    """Return one emitter in the record's form."""
    module, station, party = emitter
    return {"module": module, "station": station, "party": party}


@dataclass(frozen=True)
class AssumptionEntry:
    """One engaged assumption of the run, once, with every emitter listed."""

    short_id: str
    section: Section
    #: The table's entry for the assumption: machine key, owner, text,
    #: category, verification, status and contract anchor (the snapshot).
    snapshot: Mapping[str, Any]
    #: ``(module, station, party, machine_key, inherited_from)`` per engaged
    #: row; ``party`` only on a per-party row (record 0.30.0).
    emitted_by: tuple[tuple[str, int | None, str | None, str, str | None], ...]
    #: ``(name, value, emitters)``, identical pairs from several emitters
    #: collapsed into one with all of them listed, in first-seen order; an
    #: emitter is ``(module, station, party)``.
    bindings: tuple[tuple[str, object, tuple[Emitter, ...]], ...]

    def as_payload(self) -> dict[str, Any]:
        """Return the record form (``AssumptionEntry``)."""
        snapshot = dict(self.snapshot)
        snapshot.pop("emission", None)
        return {
            "short_id": self.short_id,
            "section": str(self.section),
            **_json_value(snapshot),
            "emitted_by": [
                {
                    "module": module,
                    "station": station,
                    "party": party,
                    "machine_key": key,
                    "inherited_from": inherited,
                }
                for module, station, party, key, inherited in self.emitted_by
            ],
            "bindings": [
                {
                    "name": name,
                    "value": _json_value(value),
                    "emitted_by": [_emitter_payload(item) for item in emitters],
                }
                for name, value, emitters in self.bindings
            ],
        }


@dataclass(frozen=True)
class NotEngaged:
    """A closure member a module that ran did not emit on this route."""

    short_id: str
    module: str
    reason: str
    discharged_by: str | None = None

    def as_payload(self) -> dict[str, Any]:
        """Return the record form: ``discharged_by`` only where it applies."""
        payload: dict[str, Any] = {
            "short_id": self.short_id,
            "module": self.module,
            "reason": self.reason,
        }
        if self.discharged_by is not None:
            payload["discharged_by"] = self.discharged_by
        return payload


@dataclass(frozen=True)
class Discrepancy:
    """One disagreement between the emitted rows and the claim closure."""

    short_id: str
    kind: DiscrepancyKind
    #: ``(module, station, party)`` of every emitter of the id; empty when none.
    emitted_by: tuple[Emitter, ...]
    detail: str

    def as_payload(self) -> dict[str, Any]:
        """Return the record form."""
        return {
            "short_id": self.short_id,
            "kind": str(self.kind),
            "emitted_by": [_emitter_payload(item) for item in self.emitted_by],
            "detail": self.detail,
        }


@dataclass(frozen=True)
class RouteExactSet:
    """The reconciled assumption set of one run."""

    roots: Mapping[str, tuple[str, ...]]
    #: Per root of the run, its ``claims`` and ``assumptions`` as the table has them.
    claim_closure: Mapping[str, Mapping[str, Any]]
    entries: tuple[AssumptionEntry, ...]
    not_engaged: tuple[NotEngaged, ...]
    discrepancies: tuple[Discrepancy, ...]

    def section(self, section: Section) -> tuple[str, ...]:
        """Return the short ids listed in one section, sorted."""
        return tuple(
            entry.short_id for entry in self.entries if entry.section is section
        )

    def kinds(self, kind: DiscrepancyKind) -> tuple[str, ...]:
        """Return the short ids of one kind of discrepancy, sorted."""
        return tuple(item.short_id for item in self.discrepancies if item.kind is kind)

    def as_payload(self) -> dict[str, Any]:
        """Return the record's ``assumption_manifest`` blocks this set owns.

        ``module_versions`` and ``reported_tier`` are the record's.
        """
        return {
            "roots": {module: list(roots) for module, roots in self.roots.items()},
            "claim_closure": {
                root: {
                    "claims": list(entry["claims"]),
                    "assumptions": dict(entry["assumptions"]),
                }
                for root, entry in self.claim_closure.items()
            },
            "assumptions": [entry.as_payload() for entry in self.entries],
            "not_engaged": [item.as_payload() for item in self.not_engaged],
            "discrepancies": [item.as_payload() for item in self.discrepancies],
        }


def _json_value(value: object) -> Any:
    """Return an emitter's binding value as JSON data.

    Exact rationals become ``"p/q"`` and enums their value, as the record
    writes them. A sequence of ``(name, value)`` pairs with distinct string
    names -- the immutable stand-in for a mapping that statistics' laws and
    envelopes use -- becomes an object, in its order; every other
    sequence a list.
    """
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, StrEnum):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        pairs = all(
            isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str)
            for item in value
        )
        if value and pairs and len({item[0] for item in value}) == len(value):
            return {item[0]: _json_value(item[1]) for item in value}
        return [_json_value(item) for item in value]
    return value


def _canonical(value: object) -> str:
    return json.dumps(_json_value(value), sort_keys=True, separators=(",", ":"))


def _module_rank(module: str) -> tuple[int, str]:
    if module in MODULE_ORDER:
        return MODULE_ORDER.index(module), module
    return len(MODULE_ORDER), module


def _table_parts(
    table: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any], dict[str, str]]:
    """Return the table's assumptions, roots and ``{machine key: short id}``.

    Fail-closed as the shipped accessors are: a table without either block, an
    assumption without a machine key, a key two assumptions share, or a
    ``verification`` outside :data:`~certiqs_key.domain.claim_closure.VERIFICATIONS`
    raises :class:`ClaimClosureError`.
    """
    assumptions = table.get("assumptions")
    roots = table.get("roots")
    if not isinstance(assumptions, Mapping) or not assumptions:
        raise ClaimClosureError(f"{TABLE_NAME} carries no assumptions")
    if not isinstance(roots, Mapping):
        raise ClaimClosureError(f"{TABLE_NAME} carries no roots")
    index: dict[str, str] = {}
    for short_id, row in assumptions.items():
        key = row.get("machine_key") if isinstance(row, Mapping) else None
        if not isinstance(key, str) or not key:
            raise ClaimClosureError(
                f"{TABLE_NAME} gives the assumption {short_id} no machine key"
            )
        if key in index:
            raise ClaimClosureError(
                f"the machine key {key!r} names two assumptions in {TABLE_NAME}"
            )
        if row.get("verification") not in VERIFICATIONS:
            raise ClaimClosureError(
                f"{TABLE_NAME} gives the assumption {short_id} the verification "
                f"{row.get('verification')!r}, which is not one of "
                f"{sorted(VERIFICATIONS)}; regenerate it with python -m "
                "harness.generate_claim_closure"
            )
        index[key] = str(short_id)
    return assumptions, roots, index


def _resolve(row: EmittedRow, index: Mapping[str, str]) -> str:
    """Return the row's short id: the table's for its key, checked against its own."""
    short_id = index.get(row.machine_key)
    if short_id is None:
        raise ClaimClosureError(
            f"the machine key {row.machine_key!r} emitted by {row.emitted_by} names "
            f"no assumption in {TABLE_NAME}; regenerate the table with python -m "
            "harness.generate_claim_closure, or give the row its owner's key"
        )
    if row.short_id is not None and row.short_id != short_id:
        raise ClaimClosureError(
            f"{row.emitted_by} emits the machine key {row.machine_key!r} as "
            f"{row.short_id}, but {TABLE_NAME} gives that key to {short_id}"
        )
    return short_id


def _section(entry: Mapping[str, Any]) -> Section:
    """Sort one assumption by its header fields.

    Category ``numerical-trust`` to numerics, every other to the premises.
    Read from the table and nowhere else.
    """
    if entry.get("category") == _NUMERICAL_CATEGORY:
        return Section.NUMERICS
    return Section.ASSUMPTIONS


def _merge_bindings(
    rows: Iterable[EmittedRow],
) -> tuple[tuple[str, object, tuple[Emitter, ...]], ...]:
    merged: dict[tuple[str, str], tuple[str, object, list[Emitter]]] = {}
    for row in rows:
        for name, value in row.bindings:
            slot = (str(name), _canonical(value))
            if slot not in merged:
                merged[slot] = (str(name), value, [])
            emitter = (row.emitted_by, row.station, row.party)
            if emitter not in merged[slot][2]:
                merged[slot][2].append(emitter)
    return tuple(
        (name, value, tuple(emitters)) for name, value, emitters in merged.values()
    )


def route_exact_assumptions(
    roots: Mapping[str, Sequence[str]],
    rows: Sequence[EmittedRow],
    *,
    vocabularies: Mapping[str, frozenset[str]] = LEDGER_VOCABULARIES,
    table: Mapping[str, Any] | None = None,
    discharges: Mapping[str, Sequence[str]] = DISCHARGED_ON_ROUTE,
    covering: frozenset[str] = COVERING_REFINEMENTS,
) -> RouteExactSet:
    """Return the run's route-exact assumption set.

    1. RESOLVE every row to its short id through the table's machine keys;
       an unknown key, or a given short id the table maps to another key,
       raises :class:`ClaimClosureError`.
    2. CLOSURE ``C``: the union of the assumption closures of every root of
       the run. A root the table lacks raises :class:`ClaimClosureError`.
    3. ENGAGED ``E``: the ids of the rows emitted engaged.
    4. PARTITION ``E``: category ``numerical-trust`` to numerics, the rest to
       assumptions.
    5. DISCREPANCIES: an id in ``E`` but not ``C``
       (``emitted_not_in_closure``); a member of ``C`` not in ``E`` that no
       module which ran can emit (``in_closure_no_emitter``); a row a root
       discharges on this route that was emitted all the same
       (``emitted_where_discharged``).
    6. NOT ENGAGED: a member of ``C`` not in ``E`` in the vocabulary of a
       module that ran, once per such module, with the module's emission rule
       from the table quoted as "emission rule: <rule>; not met on this route"
       (or "not emitted on this route" where it states none); with ``discharged_by``
       where a root discharges it; and every row emitted not engaged, with
       its emitter's condition. A member of ``C`` that an engaged member of
       ``covering`` refines (the table's ``refines``) is covered by it and is
       neither listed nor a discrepancy (:data:`COVERING_REFINEMENTS`).
    7. DEDUPLICATE: one entry per id, every engaged emitter listed, bindings
       merged.

    A module ran when it has roots or emitted a row.
    """
    source = closure_table() if table is None else table
    assumptions, root_table, index = _table_parts(source)

    resolved = [(row, _resolve(row, index)) for row in rows]

    run_roots = {
        module: tuple(dict.fromkeys(str(root) for root in module_roots))
        for module, module_roots in roots.items()
    }
    closure: dict[str, Mapping[str, Any]] = {}
    for module_roots in run_roots.values():
        for root in module_roots:
            if root not in root_table:
                raise ClaimClosureError(
                    f"{TABLE_NAME} carries no closure for the claim root {root!r}; "
                    "regenerate it with python -m harness.generate_claim_closure"
                )
            closure[root] = root_table[root]
    in_closure: dict[str, list[str]] = {}
    for root, entry in closure.items():
        for short_id in entry["assumptions"]:
            in_closure.setdefault(str(short_id), []).append(root)

    ran = sorted(
        {module for module, module_roots in run_roots.items() if module_roots}
        | {row.emitted_by for row in rows},
        key=_module_rank,
    )
    engaged_rows: dict[str, list[EmittedRow]] = {}
    unengaged_rows: dict[str, list[EmittedRow]] = {}
    for row, short_id in resolved:
        target = engaged_rows if row.engaged else unengaged_rows
        target.setdefault(short_id, []).append(row)

    discharged_by: dict[str, str] = {}
    for root in closure:
        for short_id in discharges.get(root, ()):
            discharged_by.setdefault(str(short_id), root)

    # The parent, by the table's `refines`, of an engaged
    # covering refinement is covered by it.
    covered = {
        str(parent)
        for short_id in engaged_rows
        if short_id in covering
        and isinstance(parent := assumptions[short_id].get("refines"), str)
        and parent
    }

    def emitters(short_id: str) -> tuple[Emitter, ...]:
        found = [*engaged_rows.get(short_id, ()), *unengaged_rows.get(short_id, ())]
        return tuple(
            dict.fromkeys((row.emitted_by, row.station, row.party) for row in found)
        )

    entries: list[AssumptionEntry] = []
    discrepancies: list[Discrepancy] = []
    for short_id in sorted(engaged_rows):
        snapshot = assumptions[short_id]
        section = _section(snapshot)
        found = engaged_rows[short_id]
        entries.append(
            AssumptionEntry(
                short_id=short_id,
                section=section,
                snapshot=json.loads(json.dumps(snapshot)),
                emitted_by=tuple(
                    dict.fromkeys(
                        (
                            row.emitted_by,
                            row.station,
                            row.party,
                            row.machine_key,
                            row.inherited_from,
                        )
                        for row in found
                    )
                ),
                bindings=_merge_bindings(found),
            )
        )
        if short_id not in in_closure:
            discrepancies.append(
                Discrepancy(
                    short_id=short_id,
                    kind=DiscrepancyKind.EMITTED_NOT_IN_CLOSURE,
                    emitted_by=emitters(short_id),
                    detail=(
                        "emitted engaged, but in the assumption closure of no root "
                        "of this run; listed all the same (overstating is the "
                        "safe direction)"
                    ),
                )
            )
        if short_id in discharged_by:
            discrepancies.append(
                Discrepancy(
                    short_id=short_id,
                    kind=DiscrepancyKind.EMITTED_WHERE_DISCHARGED,
                    emitted_by=emitters(short_id),
                    detail=(
                        f"discharged on this route by {discharged_by[short_id]}, "
                        "but emitted all the same"
                    ),
                )
            )

    not_engaged: list[NotEngaged] = []
    for short_id in sorted(set(in_closure) - set(engaged_rows) - covered):
        holders = [module for module in ran if short_id in vocabularies.get(module, ())]
        if not holders:
            discrepancies.append(
                Discrepancy(
                    short_id=short_id,
                    kind=DiscrepancyKind.IN_CLOSURE_NO_EMITTER,
                    emitted_by=emitters(short_id),
                    detail=(
                        "in the assumption closure of "
                        f"{', '.join(sorted(in_closure[short_id]))}, but no module "
                        "that ran can emit it"
                    ),
                )
            )
            continue
        emission = assumptions.get(short_id, {}).get("emission") or {}
        conditions = {
            row.emitted_by: row.condition
            for row in unengaged_rows.get(short_id, ())
            if row.condition
        }
        for module in holders:
            if short_id in discharged_by:
                reason = f"discharged on this route by {discharged_by[short_id]}"
            elif module in conditions:
                reason = str(conditions[module])
            elif emission.get(module):
                # The rule says when the row IS emitted; quoted bare it would read
                # as the condition of its absence. A rule that names where the
                # row comes from has its own reason.
                rule = str(emission[module])
                reason = _SOURCE_RULE_REASONS.get(
                    rule, f"{_RULE_PREFIX}{rule}{_RULE_SUFFIX}"
                )
            else:
                reason = "not emitted on this route"
            not_engaged.append(
                NotEngaged(
                    short_id=short_id,
                    module=module,
                    reason=reason,
                    discharged_by=discharged_by.get(short_id),
                )
            )
    listed = {(item.short_id, item.module) for item in not_engaged}
    for short_id in sorted(set(unengaged_rows) - set(engaged_rows)):
        for row in unengaged_rows[short_id]:
            if (short_id, row.emitted_by) in listed:
                continue
            listed.add((short_id, row.emitted_by))
            not_engaged.append(
                NotEngaged(
                    short_id=short_id,
                    module=row.emitted_by,
                    reason=row.condition or "emitted, and not invoked on this run",
                )
            )

    not_engaged.sort(key=lambda item: (item.short_id, _module_rank(item.module)))
    discrepancies.sort(key=lambda item: (item.short_id, str(item.kind)))
    return RouteExactSet(
        roots=MappingProxyType(dict(run_roots)),
        claim_closure=MappingProxyType(
            {root: json.loads(json.dumps(entry)) for root, entry in closure.items()}
        ),
        entries=tuple(entries),
        not_engaged=tuple(not_engaged),
        discrepancies=tuple(discrepancies),
    )
