"""The route THIS run took, recorded as it is taken and rendered for a reader.

The architecture's conceptual flow is authored once (spec/architecture.md 6),
and the runs/ one is documented so that it is automatically folded in. This
module is that view. It answers a different question from
section 6: not *what may happen*, but *what did happen on this run, and where
did it stop*.

THREE RULES
===========
**It is derived from the composition, never from imports.** Every entry below
is appended by :func:`~certiqs_key.runs.pipeline.run_slice` AS IT RUNS, from
the arguments it was given and the outcomes it got back. Nothing here reads a
module graph, a proof dependency or an import: an allowed edge is not an
executed stage, and a view that confused the two would say a receiver ran on a
run that declared a finite POVM.

**It is one source and not a parallel schema.** The ordered list IS the view;
:func:`mermaid` RENDERS that list and derives nothing of its own, so the
diagram and the record cannot disagree. There is no second flow description,
no per-instance diagram, and no file to maintain by hand.

**A refused stage and an unexecuted one are different.** A stage that ran and
declined carries the refusing module's own machine-readable reason;
the stages after it are ``not_executed``, which says the run stopped rather
than that they passed. A stage that is not on this route at all is ABSENT from
the list rather than present and empty -- the direct finite route has no
receiver construction to report, and a null row would invite a reader to ask
why it did nothing.

WHAT THE VIEW ADDS NOTHING TO. Rendering carries no mathematical authority, no
acceptance status and no verification lifecycle. It is a reading of the record.

THE LIST IS THE PROVENANCE GRAPH
================================
A run flow graph shows how the inputs propagate through different modules and
computations to the final finite size key rate, with the logs filed by stage.
What a list of statuses lacks is the EDGES: which configuration keys and which upstream
artefacts each stage consumed, and what it emitted. Without them a consumer either draws
a chain of statuses -- no propagation -- or hardcodes the pipeline's topology, which is
what the uniformity rule forbids.

So each entry carries :attr:`StageRecord.consumes` and
:attr:`StageRecord.emits`, and THE ORDERED LIST IS THE GRAPH: an edge is an
artefact id appearing in one stage's ``emits`` and a later stage's ``consumes``.
There is no second schema, and the Mermaid text is still rendered from this
same list.

**A PLANNED stage names the KINDS it will consume, not ids.** An id is
``<kind>:<digest prefix>`` of something that has been computed, so a stage that
has not run has none, so a preparation's graph would otherwise have
configuration edges and nothing else. :data:`PLANNED_ARTEFACT_KINDS` is the declared
table a planned entry reports, exactly as :data:`PLANNED_CONFIG_KEYS` is for
configuration, and a test holds it against what a successful run actually
consumed.

**Every edge is recorded from what is PASSED, at the moment it is passed.** Not
inferred from imports, not from the module graph, not from a proof dependency.
The ``consumes`` keys are named PER KEY where the run tier or an instance's
runner hands a stage specific keys, and PER SECTION where it hands a whole
mapping -- an instance's ``model`` and ``device`` mappings are opaque to this
tier by construction, so naming individual keys of them here would be this
tier claiming to know a vocabulary it deliberately does not.

**The digest is this tier's own.** ``sha256`` of the canonical JSON of the
artefact's payload AS THE RECORD SERIALISES IT, by the same canonicalisation
the configuration digest uses. It is NOT the envelope's ``content_hash``, which
is deferred with the artefact store (``spec/future-scope.md`` section 1) and
which a run tier may not fill: a hash field that nothing hashes may not be
given a meaning incompatible with the one it will carry. This one is hashed by
the tier that records it, and says so. The two bundle-shaped artefacts
(``bundle`` and ``docked_declaration``) are digested by :func:`bundle_digest`,
which covers the arrays' bytes as well as the manifest.

THE OBSERVER AND THE LOG
========================
A run takes thirty seconds to fifteen minutes and says nothing until it
returns. :class:`StageEvent` is emitted at the boundaries the pipeline already
has, to a caller's callable that MUST NOT CHANGE THE OUTCOME -- an exception
raised inside an observer propagates as the caller's bug, and is not caught
here -- and one structured line per transition goes to
``logging.getLogger("certiqs_key.runs")``. **No handler is configured by the
library**, and no logging call enters an accepted module: the stage dossier is
this tier's.

PROGRESS INSIDE THE SOLVE. The same observer is told an ``iterate`` event, carrying
``iteration`` and ``gap``, at every Frank-Wolfe iterate of the ``solve`` stage:
:meth:`FlowRecorder.iterate` is the driver's per-iterate hook
(``joint_driver.IterateObserver``), forwarded by
:func:`~certiqs_key.runs.pipeline.run_slice` only when an observer is given.
The same rule holds: it cannot change the outcome. Iterate events are logged
at DEBUG, since a run has thousands of them.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import Any, Final

import numpy as np
import numpy.typing as npt

from certiqs_key.domain.arrays import ArrayPayload, DenseArray
from certiqs_key.domain.bundle import OperatorBundle
from certiqs_key.runs.stages import SliceStage

__all__ = [
    "DEVICE_PROLOGUE",
    "DEVICE_PROLOGUE_KINDS",
    "LOGGER",
    "PLANNED_ARTEFACT_KINDS",
    "PLANNED_CONFIG_KEYS",
    "STAGE_MODULE",
    "STAGE_ORDER",
    "Artefact",
    "ArtefactKind",
    "FlowRecorder",
    "StageChild",
    "StageEvent",
    "StageObserver",
    "StageRecord",
    "StageStatus",
    "artefact_digest",
    "artefact_kind_of",
    "bundle_digest",
    "mermaid",
    "stage_list",
]

#: THE ONE LOGGER OF THIS TIER, and the library configures no handler for it.
#: A library that installed a handler would decide where a caller's output
#: goes; what it may do is emit, which is what this does -- one structured line
#: per stage transition, with the run id, the stage and the status.
LOGGER: Final[logging.Logger] = logging.getLogger("certiqs_key.runs")


class ArtefactKind(StrEnum):
    """What an emitted artefact IS. The vocabulary is fixed, and no more.

    Nine kinds, one per thing a stage of this path produces. A consumer joins
    two stages by an id and reads what it is from here, without knowing which
    module made it.

    ``DOCKED_DECLARATION`` is what the docking stage emits, so that the
    recorded graph shows the honest model and the acceptance set reaching the
    solve.
    """

    RECEIVER_ARTIFACT = "receiver_artifact"
    REDUCTION_CHAIN = "reduction_chain"
    TRANSMITTER_ARTIFACT = "transmitter_artifact"
    DECLARATION = "declaration"
    HONEST_DISTRIBUTION = "honest_distribution"
    ACCEPTANCE_SET = "acceptance_set"
    DOCKED_DECLARATION = "docked_declaration"
    BUNDLE = "bundle"
    KEY_RATE_RESULT = "key_rate_result"


def artefact_digest(payload: Mapping[str, Any] | Sequence[Any]) -> str:
    """Return ``sha256`` of the canonical JSON of one artefact's payload.

    THE RUN TIER'S OWN DIGEST, of the payload AS THE RECORD SERIALISES IT, by
    the canonicalisation :func:`~certiqs_key.runs.config.canonical_json` uses
    for a configuration: sorted keys, no whitespace. Two runs that emitted the
    same artefact get the same id, which is what lets a consumer join a stage
    to the stage that produced what it consumed -- including a CALLER's own
    upstream stages, where the caller supplied the honest distribution.

    ``default=str`` is the fallback for a value a module's payload carries as
    an exact object rather than as JSON -- an exact rational, an enum member --
    and it is deterministic, which is all a digest needs. It is not a licence
    to hash an object graph: what is handed here is what the record writes.

    NEVER HAND IT AN ARRAY. ``str()`` of a large NumPy array TRUNCATES with an
    ellipsis, so an array reaching the ``default=str`` fallback would yield a
    digest that ignores most of its entries while appearing to cover them. An
    operator bundle's arrays are digested by :func:`bundle_digest`, from their
    bytes.
    """
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
    ).hexdigest()


def _array_fingerprint(payload: ArrayPayload) -> dict[str, Any]:
    """Return one array's layout, shape, dtype and the sha256 of its bytes.

    The bytes are read in C order and little-endian, whatever the array's own
    memory layout and byte order, so that two arrays holding the same numbers
    fingerprint the same on every machine; the dtype recorded is the one the
    bytes were read in. ``tobytes`` is the whole array -- nothing here goes
    through ``str()`` (see :func:`artefact_digest`).
    """

    def read(values: npt.NDArray[Any]) -> dict[str, Any]:
        canonical = np.ascontiguousarray(
            values, dtype=values.dtype.newbyteorder("<")
        )
        return {
            "dtype": canonical.dtype.str,
            "shape": list(canonical.shape),
            "sha256": sha256(canonical.tobytes()).hexdigest(),
        }

    if isinstance(payload, DenseArray):
        return {"layout": "dense", "values": read(payload.values)}
    return {
        "layout": "csc",
        "shape": list(payload.shape),
        "data": read(payload.data),
        "indices": read(payload.indices),
        "indptr": read(payload.indptr),
    }


def bundle_digest(bundle: OperatorBundle) -> str:
    """Return the digest of an operator bundle: its manifest AND its arrays.

    An operator bundle is a JSON manifest
    PLUS HDF5 arrays (spec/architecture.md 4.1), and the manifest carries
    ``ArrayDescriptor``s -- dataset, dtype, shape, basis, subsystem order,
    storage -- and not one array entry. Digesting the ``bundle`` and
    ``docked_declaration`` artefacts from the manifest alone would let two
    declarations differing only in the ENTRIES of their operators share
    both ids, and a consumer joining runs by artefact id could merge two runs
    that solved different declarations.

    WHAT IS COVERED: the manifest as :func:`artefact_digest` reads it, and
    for every array of ``bundle.arrays``, keyed by its dataset path, the
    fingerprint :func:`_array_fingerprint` computes -- layout, shape, dtype and
    the sha256 of the numbers' bytes (``DenseArray.values``;
    ``SparseCSCArray``'s ``data``, ``indices``, ``indptr`` and ``shape``). It
    reads the payloads the bundle writer was handed, not a serialisation of an
    object graph.

    WHAT IT IS NOT: the envelope's ``content_hash``, which is deferred with
    the artefact store (spec/future-scope.md section 1) and which this tier
    does not fill. This digest is the run tier's own, like every other one in
    this module.
    """
    return artefact_digest(
        {
            "manifest": bundle.manifest.model_dump(mode="json"),
            "arrays": {
                dataset: _array_fingerprint(payload)
                for dataset, payload in bundle.arrays.items()
            },
        }
    )


@dataclass(frozen=True)
class Artefact:
    """One thing a stage emitted, with its id, its digest and where it is written.

    The ``id`` is ``<kind>:<first twelve of the digest>``: legible in a
    diagram, unique in practice, and derived from the content rather than from
    a counter, so that two runs emitting the same artefact name it the same.
    """

    kind: ArtefactKind
    digest: str
    #: The key of the run record's payload where this artefact is serialised,
    #: as a dotted path. ``None`` where the artefact reaches the record only
    #: through another (the bundle is on disk, and the record names its
    #: directory).
    record_key: str | None = None

    @property
    def identifier(self) -> str:
        """Return ``<kind>:<digest prefix>``."""
        return f"{self.kind}:{self.digest[:12]}"

    def as_record(self) -> dict[str, Any]:
        """Return the JSON-ready form the run record carries."""
        return {
            "id": self.identifier,
            "kind": str(self.kind),
            "digest": self.digest,
            "record_key": self.record_key,
        }


@dataclass(frozen=True)
class StageChild:
    """One step INSIDE a stage, serialised by this tier from what came back.

    The solve stage has children -- bundle validation, the map generation and
    cross-validation, the Frank-Wolfe loop, the key-length assembly, and one
    per candidate alpha where an outer search runs -- WITH NO MODULE CHANGE. So a child
    is a reading of the result record the engine returned, and it carries a
    ``wall_time_s`` only where the run tier measured one at its own boundary: this tier
    does not see the seam between bundle validation and the loop, and a time it did not
    measure would be invented.
    """

    name: str
    status: str
    detail: dict[str, Any] = field(default_factory=dict)
    wall_time_s: float | None = None

    def as_record(self) -> dict[str, Any]:
        """Return the JSON-ready form the run record carries."""
        return {
            "name": self.name,
            "status": self.status,
            "detail": dict(self.detail),
            "wall_time_s": self.wall_time_s,
        }


@dataclass(frozen=True)
class StageEvent:
    """What an observer is told, at a boundary the pipeline already had.

    ``kind`` is ``started`` before a stage runs and ``finished`` or ``refused``
    after it, and ``iterate`` at each Frank-Wolfe iterate inside ``solve``,
    carrying ``iteration`` and ``gap``. ``wall_time_s`` is ``None`` on
    ``started`` and ``iterate`` -- nothing has been measured at that boundary
    -- and the elapsed time on ``finished`` and ``refused``.
    """

    kind: str
    stage: SliceStage
    wall_time_s: float | None = None
    reason: str | None = None
    #: The station's declared factor on a per-station stage of a multi-station
    #: run (:attr:`StageRecord.station`); ``None`` everywhere else.
    station: str | None = None
    #: On an ``iterate`` event: the iteration ``k`` and the Frank-Wolfe gap
    #: formed at it. ``None`` on every other kind.
    iteration: int | None = None
    gap: float | None = None


#: A caller's optional hook. IT MUST NOT CHANGE THE OUTCOME: nothing here reads
#: its return value, and an exception raised inside it propagates as the
#: caller's bug rather than being swallowed into a refusal that did not happen.
type StageObserver = Callable[[StageEvent], None]


class StageStatus(StrEnum):
    """What became of one stage on this run.

    ``EXECUTED`` and ``REFUSED`` are facts about a stage that ran;
    ``NOT_EXECUTED`` is a fact about the RUN -- it stopped earlier -- and is
    the value the item asks to be distinguishable from the other two.
    """

    EXECUTED = "executed"
    REFUSED = "refused"
    NOT_EXECUTED = "not_executed"
    #: The status of every entry a PREPARATION returns: this stage is on
    #: this route and this configuration would run it. It is not a prediction
    #: that it will succeed, and a preparation never reports any other status
    #: for a stage it did not itself run.
    PLANNED = "planned"


#: The stages of the full path, in the order the pipeline runs them. The first
#: three belong to the device prologue and are on the path only where a device
#: was declared; the rest are on every route.
STAGE_ORDER: Final[tuple[SliceStage, ...]] = (
    SliceStage.RECEIVER_CONSTRUCTION,
    SliceStage.RECEIVER_DOCKING,
    SliceStage.REDUCTION,
    SliceStage.COMPILATION,
    SliceStage.HONEST_MODEL,
    SliceStage.ACCEPTANCE_CONSTRUCTION,
    SliceStage.DOCKING,
    SliceStage.BUNDLE_WRITE,
    SliceStage.BUNDLE_READ,
    SliceStage.SOLVE,
)

#: The three stages that exist only where a physical Bob was declared.
DEVICE_PROLOGUE: Final[tuple[SliceStage, ...]] = STAGE_ORDER[:3]

#: WHICH MODULE OWNS EACH STAGE. The run tier owns the order and the record and
#: no mathematics (spec/architecture.md 3.3), so every stage but its own three
#: names the module whose contract decides what happens there. ``runs`` appears
#: for the honest model -- an instance's provider behind ``statistics``'
#: interface, "not proof-critical" (3.4) -- and for the two bundle stages,
#: which are this tier writing and reading the shared format.
STAGE_MODULE: Final[dict[SliceStage, str]] = {
    SliceStage.RECEIVER_CONSTRUCTION: "receiver",
    SliceStage.RECEIVER_DOCKING: "receiver",
    SliceStage.REDUCTION: "reductions",
    SliceStage.COMPILATION: "protocol-compiler",
    SliceStage.HONEST_MODEL: "runs",
    SliceStage.ACCEPTANCE_CONSTRUCTION: "statistics",
    SliceStage.DOCKING: "meat-core",
    SliceStage.BUNDLE_WRITE: "runs",
    SliceStage.BUNDLE_READ: "runs",
    SliceStage.SOLVE: "meat-core",
}


#: WHICH CONFIGURATION KEYS EACH STAGE IS PASSED, as the pipeline passes them.
#:
#: A RUN records what it actually passed, at the moment it passes it; a
#: PREPARATION has not run those stages and reports this table instead, which
#: is the "consumes filled" of a planned entry. The two agree because the
#: pipeline's own ``start`` calls are written from this table -- a test asserts
#: that the executed list and the planned list name the same keys on a
#: successful run, so a stage that started reading a new key and did not say so
#: here fails rather than drifting.
#:
#: ``device`` and ``model`` are named PER SECTION, not per key: both mappings
#: are opaque to this tier by construction, and naming keys inside them would
#: be this tier claiming a vocabulary it deliberately does not have. An
#: instance's runner, which does have it, names them per key where it hands
#: them over.
#:
#: ONE ENTRY NAMES A KEY THIS TIER DOES NOT HAND OVER, and it is here rather
#: than dropped because a reader of the graph wants to know where ``tau`` was
#: spent: ``RECEIVER_DOCKING``'s ``declared_tolerance`` is spent AT that stage
#: BY THE INSTANCE -- its rows adapter closes over the ceiling it was built
#: with and snaps the declared family against it -- while this tier passes the
#: docking stage nothing but the artefact. Every other
#: entry is a key this tier passes at that stage itself.
PLANNED_CONFIG_KEYS: Final[dict[SliceStage, tuple[str, ...]]] = {
    SliceStage.RECEIVER_CONSTRUCTION: ("device",),
    #: Spent by the INSTANCE's rows adapter at this stage; see above.
    SliceStage.RECEIVER_DOCKING: ("declared_tolerance",),
    SliceStage.REDUCTION: ("device",),
    SliceStage.COMPILATION: (),
    SliceStage.HONEST_MODEL: ("model",),
    SliceStage.ACCEPTANCE_CONSTRUCTION: (
        "rounds",
        "completeness_budget",
        "constrained",
        "endpoint_rule",
        "tail_evaluation",
    ),
    SliceStage.DOCKING: ("rounds", "parameters"),
    SliceStage.BUNDLE_WRITE: (),
    SliceStage.BUNDLE_READ: (),
    SliceStage.SOLVE: ("alpha", "parameters", "solver"),
}


#: WHICH UPSTREAM ARTEFACTS EACH STAGE CONSUMES, BY KIND.
#:
#: THE PLANNED GRAPH'S EDGES, and the reason it needs a table of its own.
#: ``consumes_artefacts`` carries artefact IDS, and an id is
#: ``<kind>:<digest prefix>`` of a thing that has been computed -- so a stage
#: that has not run has no ids to name, and without this table the planned
#: list would carry no artefact edges: a preparation's graph would have
#: configuration edges and nothing else.
#: What a planned stage CAN state is the KIND it will consume, which is what
#: this table is.
#:
#: IT DOES NOT WEAKEN THE RULE ABOVE, and the distinction is the whole point: an
#: executed row's ``consumes_artefacts`` is still recorded from what was PASSED
#: at the moment it was passed, never inferred from an import or a proof
#: dependency. This table is a DECLARATION about a route, exactly as
#: :data:`PLANNED_CONFIG_KEYS` is, and it is held against reality the same way
#: -- a test asserts that on a successful run every executed stage's consumed
#: kinds are the ones named here, so a stage that started consuming a new kind
#: and did not say so fails rather than drifting.
#:
#: ``RECEIVER_CONSTRUCTION`` consumes no artefact: it is handed a device
#: request, which is configuration. ``BUNDLE_WRITE`` consumes the compiled
#: declaration as well as the docked one, because this tier passes the
#: announcement alphabets of the first to the writer of the second.
#:
#: TWO OF THE KINDS ARE THE DEVICE PROLOGUE'S and appear only on that route.
#: ``COMPILATION`` consumes a receiver artefact and a reduction chain where a
#: device was declared and NOTHING where a finished specification was supplied,
#: so :meth:`FlowRecorder.planned` drops :data:`DEVICE_PROLOGUE_KINDS` on the
#: direct route rather than promising an edge that cannot exist.
PLANNED_ARTEFACT_KINDS: Final[dict[SliceStage, tuple[ArtefactKind, ...]]] = {
    SliceStage.RECEIVER_CONSTRUCTION: (),
    SliceStage.RECEIVER_DOCKING: (ArtefactKind.RECEIVER_ARTIFACT,),
    SliceStage.REDUCTION: (ArtefactKind.RECEIVER_ARTIFACT,),
    SliceStage.COMPILATION: (
        ArtefactKind.RECEIVER_ARTIFACT,
        ArtefactKind.REDUCTION_CHAIN,
    ),
    SliceStage.HONEST_MODEL: (ArtefactKind.DECLARATION,),
    SliceStage.ACCEPTANCE_CONSTRUCTION: (
        ArtefactKind.HONEST_DISTRIBUTION,
        ArtefactKind.DECLARATION,
    ),
    SliceStage.DOCKING: (ArtefactKind.DECLARATION, ArtefactKind.ACCEPTANCE_SET),
    SliceStage.BUNDLE_WRITE: (
        ArtefactKind.DECLARATION,
        ArtefactKind.DOCKED_DECLARATION,
    ),
    SliceStage.BUNDLE_READ: (ArtefactKind.BUNDLE,),
    SliceStage.SOLVE: (ArtefactKind.BUNDLE,),
}

#: The kinds ONLY the device prologue produces, so the only two entries of
#: :data:`PLANNED_ARTEFACT_KINDS` that depend on the route.
DEVICE_PROLOGUE_KINDS: Final[frozenset[ArtefactKind]] = frozenset(
    {ArtefactKind.RECEIVER_ARTIFACT, ArtefactKind.REDUCTION_CHAIN}
)


def artefact_kind_of(identifier: str) -> ArtefactKind:
    """Return the kind an artefact id names.

    NOT AN INFERENCE. :attr:`Artefact.identifier` IS ``<kind>:<digest
    prefix>``, so the kind is carried in the id and this reads it back; nothing
    here guesses from a stage, a module or an import.

    Raises:
        ValueError: on a string that is not an artefact id, or whose prefix is
            not one of :class:`ArtefactKind`'s members. A silent fallback would
            put an invented kind on a graph edge.
    """
    kind, _, rest = identifier.partition(":")
    if not rest:
        raise ValueError(f"not an artefact id: {identifier!r}")
    return ArtefactKind(kind)


@dataclass(frozen=True)
class StageRecord:
    """One node of the view: a stage, what became of it, and why.

    ``detail`` carries whatever the recording site thought a reader of the
    route needs about THAT stage and nothing more -- the declared route name,
    the number of links a chain carried, the geometry tag an acceptance set
    came back with. It is JSON-ready data the record transcribes and this
    module never interprets.
    """

    stage: SliceStage
    module: str
    status: StageStatus
    #: The refusing module's own machine-readable code, on a refused stage.
    reason: str | None = None
    #: That module's own message, on a refused stage.
    refusal_detail: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    #: the wall time this stage took, measured at this tier's own
    #: boundaries. ``None`` on a stage that did not run.
    wall_time_s: float | None = None
    #: the ``RunConfig`` keys this stage was PASSED, per key where the
    #: run tier hands it specific ones and per section where it hands a whole
    #: mapping.
    consumes_config: tuple[str, ...] = ()
    #: the ids of the upstream artefacts this stage consumed. Every one
    #: of them appears in an earlier stage's :attr:`emits`. EMPTY ON A PLANNED
    #: ENTRY, because an id names a thing that has been computed; what a
    #: planned entry carries instead is :attr:`consumes_artefact_kinds`.
    consumes_artefacts: tuple[str, ...] = ()
    #: the KINDS of the artefacts this stage consumes. On an executed or
    #: refused entry these are read back off the ids above, which carry them;
    #: on a PLANNED entry they are :data:`PLANNED_ARTEFACT_KINDS`, which is
    #: what lets a preparation's graph have artefact edges at all.
    consumes_artefact_kinds: tuple[ArtefactKind, ...] = ()
    #: what this stage produced.
    emits: tuple[Artefact, ...] = ()
    #: the steps inside this stage, where the run tier can read them off
    #: what came back. Empty everywhere but the solve.
    children: tuple[StageChild, ...] = ()
    #: WHICH STATION this stage ran for: the
    #: station's declared factor, :attr:`~certiqs_key.runs.pipeline.Station.factor`,
    #: on each device-prologue stage of a multi-station route, and ``None`` on
    #: every other stage and on every stage of a single-device route. A
    #: reference to the station entry ``payload.stages.stations[i]`` whose
    #: ``factor`` it is -- not a second declaration of the station -- so that
    #: repeated stage names are told apart by what they ran for rather than by
    #: their position in the list.
    station: str | None = None

    def as_record(self) -> dict[str, Any]:
        """Return the JSON-ready form the run record carries."""
        return {
            "stage": str(self.stage),
            "station": self.station,
            "module": self.module,
            "status": str(self.status),
            "reason": self.reason,
            "refusal_detail": self.refusal_detail,
            "detail": dict(self.detail),
            "wall_time_s": self.wall_time_s,
            "consumes": {
                "config": list(self.consumes_config),
                "artefacts": list(self.consumes_artefacts),
                "artefact_kinds": [str(kind) for kind in self.consumes_artefact_kinds],
            },
            "emits": [artefact.as_record() for artefact in self.emits],
            "children": [child.as_record() for child in self.children],
        }


class FlowRecorder:
    """Collects the view while the pipeline runs it.

    THE PIPELINE DRIVES THIS AND NOTHING ELSE DOES. Each stage reports itself
    at the point where it returned, so the list is a transcript rather than a
    reconstruction, and :meth:`finish` fills in what the run never reached.

    A recorder is created knowing ONE thing the stages cannot tell it: whether
    a device prologue is on this route. That is the composition -- the caller
    supplied a device or a finished specification -- and the composition is
    what this tier owns.
    """

    def __init__(
        self,
        *,
        device_prologue: bool,
        stations: Sequence[str] = (),
        observer: StageObserver | None = None,
        run_id: str | None = None,
    ) -> None:
        """Start a transcript for a route with or without the device prologue.

        ``run_id`` is the caller's own -- the configuration digest, where the
        caller has one -- and is carried into every log line so that the lines
        of one run can be collected. This tier does not compute it, because a
        run reaching :func:`~certiqs_key.runs.pipeline.run_slice` without a
        :class:`~certiqs_key.runs.config.RunConfig` has no configuration to
        digest.

        ``stations`` is the declared station factors of a multi-station route,
        in station order, and empty everywhere else. On such a route the
        device prologue's three stages are planned ONCE PER STATION, station
        by station as the prologue runs them, each entry naming its station --
        so the planned list and the ``not_executed`` tail of a refusal cover
        the second station too, instead of counting its stages as seen because
        the first station ran them.
        """
        if stations and not device_prologue:
            raise ValueError("stations are declared only on a device route")
        self._device_prologue = device_prologue
        prologue_stations: tuple[str | None, ...] = tuple(stations) or (None,)
        self._planned: list[tuple[SliceStage, str | None]] = [
            (stage, station)
            for station in (prologue_stations if device_prologue else ())
            for stage in DEVICE_PROLOGUE
        ] + [(stage, None) for stage in STAGE_ORDER if stage not in DEVICE_PROLOGUE]
        self._records: list[StageRecord] = []
        self._observer = observer
        self._run_id = run_id
        self._started: float | None = None
        self._current: SliceStage | None = None
        self._current_station: str | None = None

    def start(
        self,
        stage: SliceStage,
        *,
        config_keys: Sequence[str] = (),
        artefacts: Sequence[str] = (),
        station: str | None = None,
    ) -> None:
        """Record that ``stage`` is about to run, and what it is being passed.

        The edges are recorded HERE, before the stage runs, because that is
        where what is passed is known and where a refusal still leaves them
        readable. A stage that refuses carries the inputs it refused on.
        ``station`` is the station this stage runs for, on a per-station stage
        of a multi-station route (:attr:`StageRecord.station`).
        """
        self._current = stage
        self._current_station = station
        self._pending_config = tuple(config_keys)
        self._pending_artefacts = tuple(artefacts)
        self._started = time.perf_counter()
        self._emit(StageEvent(kind="started", stage=stage, station=station))

    def executed(
        self,
        stage: SliceStage,
        *,
        emits: Sequence[Artefact] = (),
        children: Sequence[StageChild] = (),
        **detail: Any,
    ) -> None:
        """Record that ``stage`` ran and returned, with what it emitted."""
        station = self._station_of(stage)
        elapsed = self._elapsed(stage)
        consumed = self._taken_artefacts(stage)
        self._records.append(
            StageRecord(
                stage=stage,
                module=STAGE_MODULE[stage],
                status=StageStatus.EXECUTED,
                detail=dict(detail),
                wall_time_s=elapsed,
                consumes_config=self._taken_config(stage),
                consumes_artefacts=consumed,
                consumes_artefact_kinds=_kinds(consumed),
                emits=tuple(emits),
                children=tuple(children),
                station=station,
            )
        )
        self._emit(
            StageEvent(
                kind="finished", stage=stage, wall_time_s=elapsed, station=station
            )
        )

    def refused(
        self, stage: SliceStage, reason: str, detail: str, **extra: Any
    ) -> None:
        """Record that ``stage`` declined, in the refusing module's vocabulary."""
        station = self._station_of(stage)
        elapsed = self._elapsed(stage)
        consumed = self._taken_artefacts(stage)
        self._records.append(
            StageRecord(
                stage=stage,
                module=STAGE_MODULE[stage],
                status=StageStatus.REFUSED,
                reason=reason,
                refusal_detail=detail,
                detail=dict(extra),
                wall_time_s=elapsed,
                consumes_config=self._taken_config(stage),
                consumes_artefacts=consumed,
                consumes_artefact_kinds=_kinds(consumed),
                station=station,
            )
        )
        self._emit(
            StageEvent(
                kind="refused",
                stage=stage,
                wall_time_s=elapsed,
                reason=reason,
                station=station,
            )
        )

    def iterate(self, iteration: int, gap: float) -> None:
        """Tell the observer one Frank-Wolfe iterate of the ``solve`` stage.

        The driver's per-iterate hook: ``(k, gap)`` becomes an ``iterate``
        event. Nothing is recorded in the transcript -- the per-iterate gap
        trajectory is on the finished result -- and the event goes to the log
        at DEBUG.
        """
        self._emit(
            StageEvent(
                kind="iterate",
                stage=SliceStage.SOLVE,
                iteration=iteration,
                gap=gap,
            )
        )

    # -- the three halves of the bookkeeping --------------------------------

    _pending_config: tuple[str, ...] = ()
    _pending_artefacts: tuple[str, ...] = ()

    def _station_of(self, stage: SliceStage) -> str | None:
        """Return the station ``stage`` was started for, or ``None``."""
        return self._current_station if self._current is stage else None

    def _taken_config(self, stage: SliceStage) -> tuple[str, ...]:
        """Return and clear the config keys recorded for ``stage``."""
        taken = self._pending_config if self._current is stage else ()
        self._pending_config = ()
        return taken

    def _taken_artefacts(self, stage: SliceStage) -> tuple[str, ...]:
        """Return and clear the artefact ids recorded for ``stage``."""
        taken = self._pending_artefacts if self._current is stage else ()
        self._pending_artefacts = ()
        return taken

    def _elapsed(self, stage: SliceStage) -> float | None:
        """Return the wall time since :meth:`start`, or ``None`` if unmeasured."""
        if self._started is None or self._current is not stage:
            return None
        elapsed = time.perf_counter() - self._started
        self._started = None
        return elapsed

    def _emit(self, event: StageEvent) -> None:
        """Tell the observer and the log, in that order.

        THE OBSERVER IS CALLED FIRST AND ITS EXCEPTION PROPAGATES. Nothing here
        catches it: an observer that raises has a bug, and swallowing it would
        turn a caller's defect into a run that quietly logged less.
        """
        if self._observer is not None:
            self._observer(event)
        LOGGER.log(
            logging.DEBUG if event.kind == "iterate" else logging.INFO,
            "stage %s %s",
            event.stage,
            event.kind,
            # ``stage_module`` AND NOT ``module``: ``LogRecord`` already has a
            # ``module`` attribute (the Python module the call came from), and
            # ``logging`` refuses an ``extra`` that would overwrite one of its
            # own -- correctly, since a field meaning two things is worse than
            # a longer name.
            extra={
                "run_id": self._run_id,
                "stage": str(event.stage),
                "stage_module": STAGE_MODULE[event.stage],
                "event": event.kind,
                "station": event.station,
                "wall_time_s": event.wall_time_s,
                "reason": event.reason,
                "iteration": event.iteration,
                "gap": event.gap,
            },
        )

    def planned(self) -> tuple[StageRecord, ...]:
        """Return the PLANNED list for this route: every stage, in order.

        A preparation returns the same entries with status ``planned``, so that a
        consumer can show the route and the parameter propagation before paying for a
        solve. The stages this recorder already ran keep what they recorded -- a
        preparation DOES run the device prologue and the compilation, and reporting
        those as planned would throw away what actually happened -- and the rest are
        planned.
        """
        seen = {(record.stage, record.station) for record in self._records}
        return tuple(self._records) + tuple(
            StageRecord(
                stage=stage,
                module=STAGE_MODULE[stage],
                status=StageStatus.PLANNED,
                consumes_config=PLANNED_CONFIG_KEYS[stage],
                consumes_artefact_kinds=self._planned_kinds(stage),
                station=station,
            )
            for stage, station in self._planned
            if (stage, station) not in seen
        )

    def _planned_kinds(self, stage: SliceStage) -> tuple[ArtefactKind, ...]:
        """Return the kinds ``stage`` will consume ON THIS ROUTE.

        The two kinds the device prologue produces are dropped where there is
        no prologue: the compilation consumes a receiver artefact and a
        reduction chain on the device route and nothing at all where a finished
        specification was supplied, and a planned edge to a stage that is not
        on this route would be a promise the run cannot keep.
        """
        return tuple(
            kind
            for kind in PLANNED_ARTEFACT_KINDS[stage]
            if self._device_prologue or kind not in DEVICE_PROLOGUE_KINDS
        )

    def finish(self) -> tuple[StageRecord, ...]:
        """Return the view, with every stage the run never reached marked.

        A stage is ``not_executed`` when it is on this route and no record was
        made for it. That is the case a refusal creates and the one the item
        asks to be visible: the run stopped, and the stages after the stop
        neither passed nor failed.
        """
        seen = {(record.stage, record.station) for record in self._records}
        trailing = [
            StageRecord(
                stage=stage,
                module=STAGE_MODULE[stage],
                status=StageStatus.NOT_EXECUTED,
                station=station,
            )
            for stage, station in self._planned
            if (stage, station) not in seen
        ]
        return tuple(self._records) + tuple(trailing)


def _kinds(identifiers: Sequence[str]) -> tuple[ArtefactKind, ...]:
    """Return the kinds of ``identifiers``, in their order and with duplicates.

    Duplicates are KEPT: a stage handed two artefacts of one kind consumed two
    things, and collapsing them would make the graph say it consumed one.
    """
    return tuple(artefact_kind_of(identifier) for identifier in identifiers)


def stage_list(outcome: Any) -> tuple[StageRecord, ...]:
    """Return the view an outcome carries.

    A thin reader, because the view is built where it happens: the outcome
    carries what the pipeline recorded, and this function exists so that the
    record module names one entry point rather than reaching for an attribute.
    """
    stages: Sequence[StageRecord] = getattr(outcome, "stages", ())
    return tuple(stages)


def mermaid(stages: Sequence[StageRecord]) -> str:
    """Render the view as Mermaid flowchart text.

    ONE SOURCE. Every node and every edge below comes from ``stages`` and from
    nothing else, so a diagram that disagreed with the record would be a
    defect in this function rather than two descriptions drifting apart. The
    status is carried in the node's own label, because a colour class would put
    the one thing a reader needs where a plain-text reader cannot see it.

    The text is deliberately plain: ``flowchart TD`` and one node per stage,
    linked in the order the stages ran. The viewing guide
    (``harness/contract-reading.md``) is where a reader learns to preview it,
    and it is the same guide the module flowcharts use.
    """
    if not stages:
        return "flowchart TD\n    empty[\"no stage ran\"]\n"
    lines = ["flowchart TD"]
    marks = {
        StageStatus.EXECUTED: "ok",
        StageStatus.REFUSED: "REFUSED",
        StageStatus.NOT_EXECUTED: "not executed",
        StageStatus.PLANNED: "planned",
    }
    for index, record in enumerate(stages):
        # A PER-STATION STAGE NAMES ITS STATION in the node, so the two
        # stations' prologues read as two and not as one stage run twice.
        name = (
            str(record.stage)
            if record.station is None
            else f"{record.stage} [{record.station}]"
        )
        label = f"{name} ({record.module}) -- {marks[record.status]}"
        if record.reason is not None:
            label = f"{label}: {record.reason}"
        lines.append(f'    s{index}["{_label(label)}"]')
    for index in range(len(stages) - 1):
        lines.append(f"    s{index} --> s{index + 1}")
    return "\n".join(lines) + "\n"


def _label(text: str) -> str:
    """Return a node label safe inside Mermaid's double-quoted form.

    A LABEL CARRIES A REFUSING MODULE'S OWN REASON CODE, verbatim, and this
    tier neither owns that vocabulary nor may edit it -- so a reason containing
    a quotation mark would close the label early and produce text no renderer
    accepts (latent today, because every reason code in the tree is an
    identifier). ``#quot;`` is Mermaid's own entity for the
    character, so the reason still READS as what the module wrote.

    Newlines go the same way and for the same reason: the text is one line per
    node, and a reason with a line break in it would be a second node's worth
    of syntax.
    """
    return text.replace('"', "#quot;").replace("\n", " ")
