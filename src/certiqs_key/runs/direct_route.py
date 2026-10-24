"""Which moved blocks a run evaluated off their snap, and which rest on A-SNAP.

WHY THIS EXISTS. ``foundations/def:evaluated-off-snap`` (ii) is a statement
about the RECORD OF THE RUN: a block is evaluated off its snap when no number
the run computes its key length from reads the snapped block. That is known
only after the solve, when ``meat-core/frank-wolfe/req:bracket-on-reference``
has decided whether the bound on the reference companion counts (item (iii))
or the run fell back to the bound on the snapped declaration (item (iv)). The
declaring instance's snap record names its moved blocks, and the reductions'
emission record its data sectors with a moved class, when they are made, and
that naming is PROVISIONAL (``reductions/req:emission-record``; ``thm:emit``
(vi)): this module is where the run decides it, once, and every reader of the
record -- the snap block of the record, the assumption manifest, the report --
reads the decision here.

THE RULE (``req:bracket-on-reference`` (iv), (v); ``foundations/
req:snap-reference`` (iii)). Where the companion's bound counts, every MOVED
block of the snap of each declaring instance whose link the companion
replaces, on which the companion carries the HANDED reference, is evaluated
off its snap, and so is every data sector of each such link's snapped
emission that holds a moved class (the companion bypasses the emission
normaliser and carries none of its data); a KEPT block or sector is named as
kept and is not counted among them. Every other moved block or sector rests
on A-SNAP, with its cause and group:

* a moved instance block on which no reference is handed: the cause its snap
  recorded, in the group ``no usable reference``;
* a moved block on which the reference is handed, and a moved sector of an
  artefact with a companion, at a station whose link the companion
  REPLACES: ``reference bracket withdrawn`` where the bound on the companion
  was withdrawn (cause ``reference_bracket_withdrawn``, or
  ``factor_enclosure_inconsistent`` where the certified evaluation withdrew
  it), ``reference bracket not evaluated`` where it was not evaluated;
* a moved block on which a reference is handed at a station whose link the
  companion does not replace (no companion formed for it): ``reference
  bracket not evaluated``, whatever the status, as without a companion;
* a moved sector of an artefact with no companion: ``no usable reference``
  (cause ``no_reference_companion``);
* a block or sector snapped by the last resort, whatever its cause: the group
  ``last resort``.

THE FALLBACK (``meat-core/frank-wolfe/req:certified-evaluation`` (i);
``req:bracket-on-reference`` (v)). Where the companion's bound counts but the
key length is formed from a number certified on the searched declaration in
its place, no number formed on the companion reaches the key length, so the
blocks the companion carried are NOT evaluated off their snap: they rest in
the group ``reference bracket withdrawn`` with the cause
``companion_not_certified``, and the status stays ``counted``, the run's
first-order number being the companion's. The certified record's
``premises`` and ``resting_blocks`` (item (ix)) are read from the decision for
the declaration the certified number is formed on
(:func:`certified_premises`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

from certiqs_key.foundations.resting import (
    RestingCause,
    RestingGroup,
    resting_fix,
    resting_group,
)
from certiqs_key.foundations.snap import (
    ASSUMPTION_CLAIM,
    ASSUMPTION_ID,
    ASSUMPTION_MACHINE_KEY,
)
from certiqs_key.protocol_compiler.companion import (
    CompiledReferenceCompanion,
    NoCompiledCompanion,
)
from certiqs_key.reductions.companion import ReferenceCompanion
from certiqs_key.solvers.frank_wolfe.certified_record import (
    FACTOR_ENCLOSURE_INCONSISTENT,
    ON_SEARCHED,
)

if TYPE_CHECKING:
    from certiqs_key.reductions.artifact import ProofReductionArtifact
    from certiqs_key.runs.pipeline import SliceResult

__all__ = [
    "EVALUATED_OFF_CONDITION",
    "DirectRoute",
    "RestingBlock",
    "StationEvaluation",
    "annotate_snap_records",
    "certified_premises",
    "direct_route",
    "resting_names",
]

#: The condition a not-engaged A-SNAP row states, where every moved block and
#: data sector the artefact named was evaluated off its snap.
EVALUATED_OFF_CONDITION: Final[str] = (
    "every moved block and data sector the artefact named was evaluated off its "
    "snap: the run's first-order number is the bound on the reference companion "
    "(foundations/def:evaluated-off-snap; "
    "meat-core/frank-wolfe/req:bracket-on-reference (v))"
)

#: The origins a named block carries: the declaring instance's snap, and the
#: reductions' emission normaliser.
INSTANCE_SNAP: Final[str] = "instance_snap"
EMISSION: Final[str] = "emission"


@dataclass(frozen=True)
class RestingBlock:
    """One moved block or data sector, and the run's verdict on it.

    ``cause`` and ``group`` are ``None`` on a block evaluated off its snap,
    which rests on nothing.
    """

    origin: str
    block: str
    group: str | None
    cause: str | None
    evaluated_off_snap: bool
    support_not_preserved: bool = False

    @property
    def fix(self) -> str | None:
        """The fix of the cause, with the device's noise for a last-resort block."""
        if self.cause is None:
            return None
        return resting_fix(
            RestingCause(self.cause), last_resort=self.support_not_preserved
        )

    @property
    def group_fix(self) -> str | None:
        """The fix of the group; the cause's fix details it."""
        if self.group is None:
            return None
        cause = None if self.cause is None else RestingCause(self.cause)
        return RestingGroup(self.group).fix(cause)

    def as_record(self) -> dict[str, Any]:
        """JSON-ready."""
        return {
            "origin": self.origin,
            "block": self.block,
            "group": self.group,
            "cause": self.cause,
            "fix": self.fix,
            "group_fix": self.group_fix,
            "support_not_preserved": self.support_not_preserved,
            "evaluated_off_snap": self.evaluated_off_snap,
        }


@dataclass(frozen=True)
class StationEvaluation:
    """One reductions artefact's moved blocks: which were evaluated off their snap."""

    #: The station's index in ``stages.stations``; ``None`` on the
    #: single-device route.
    station: int | None
    #: The measured factor's label, where the declaration names one.
    factor: str | None
    #: The moved instance-snap blocks (``m=<m>, t=<setting>``) evaluated off
    #: their snap.
    instance_blocks: frozenset[str]
    #: The data sectors with a moved class evaluated off their snap.
    emission_sectors: frozenset[int]
    #: The instance-snap blocks the snap kept, named as kept and in neither
    #: list (``foundations/req:who-snaps``).
    kept_blocks: tuple[str, ...]
    #: Every moved block and data sector, with the verdict.
    named: tuple[RestingBlock, ...]

    @property
    def resting(self) -> tuple[RestingBlock, ...]:
        """The blocks that rest on A-SNAP after the run's decision."""
        return tuple(block for block in self.named if not block.evaluated_off_snap)

    def verdict(self, origin: str, block: str) -> RestingBlock | None:
        """Return the verdict on one named block or sector, or ``None``."""
        for item in self.named:
            if item.origin == origin and item.block == block:
                return item
        return None

    def as_record(self) -> dict[str, Any]:
        """JSON-ready."""
        return {
            "station": self.station,
            "factor": self.factor,
            "evaluated_off_snap": sorted(self.instance_blocks),
            "emission_evaluated_off_snap": sorted(self.emission_sectors),
            "kept_blocks": list(self.kept_blocks),
            "named": [block.as_record() for block in self.named],
            "resting": [block.as_record() for block in self.resting],
        }


@dataclass(frozen=True)
class DirectRoute:
    """The run's decision on the direct route (``req:bracket-on-reference``)."""

    #: ``counted`` (the bound on the companion counts), ``withdrawn`` (no
    #: evaluated point contributed, or the certified evaluation found a
    #: block's enclosures inconsistent, item (iv)), ``not_evaluated`` (the
    #: companion was not admitted or a dropped program ran), ``not_compiled``
    #: (no companion was compiled) or ``absent`` (no reduction stage).
    status: str
    reason: str | None
    stations: tuple[StationEvaluation, ...]
    #: Whether the key length is formed in the fallback of
    #: ``req:certified-evaluation`` (i): counted, but from a number certified
    #: on the searched declaration, so the carried blocks rest on A-SNAP.
    fallback: bool = False

    @property
    def counted(self) -> bool:
        """Whether the run's first-order number is the bound on the companion."""
        return self.status == "counted"

    @property
    def evaluated_off_snap_count(self) -> int:
        """The number of moved instance-snap blocks evaluated off their snap."""
        return sum(len(station.instance_blocks) for station in self.stations)

    @property
    def rests_on_a_snap(self) -> bool:
        """Whether some moved block or sector still rests on A-SNAP."""
        return any(station.resting for station in self.stations)

    def station(self, index: int | None) -> StationEvaluation | None:
        """Return the evaluation of one station (``None``: the single device)."""
        for item in self.stations:
            if item.station == index:
                return item
        return None

    def as_record(self) -> dict[str, Any]:
        """JSON-ready: ``payload.snaps.reference_companion``."""
        evaluated = [
            {"station": station.station, "factor": station.factor, "block": block}
            for station in self.stations
            for block in sorted(station.instance_blocks)
        ]
        return {
            "status": self.status,
            "reason": self.reason,
            "fallback": self.fallback,
            "evaluated_off_snap": evaluated,
            "evaluated_off_snap_count": self.evaluated_off_snap_count,
            "emission_evaluated_off_snap": [
                {
                    "station": station.station,
                    "factor": station.factor,
                    "data_sectors": sorted(station.emission_sectors),
                }
                for station in self.stations
                if station.emission_sectors
            ],
            "kept_blocks": [
                {"station": station.station, "factor": station.factor, "block": block}
                for station in self.stations
                for block in station.kept_blocks
            ],
            "resting_blocks": [
                {"station": station.station, "factor": station.factor,
                 **block.as_record()}
                for station in self.stations
                for block in station.resting
            ],
            "rests_on_a_snap": self.rests_on_a_snap,
            "stations": [station.as_record() for station in self.stations],
        }


@dataclass(frozen=True)
class _SnapBlock:
    """One block of an instance's measurement snap, as its record names it."""

    name: str
    moved: bool
    handed: bool
    cause: str | None
    support_not_preserved: bool


def _snap_blocks(adaptation: Mapping[str, Any] | None) -> list[_SnapBlock]:
    """Return every block of an instance's measurement snaps, read from its record.

    ``foundations/req:who-snaps``: per block its status, whether the reference
    is handed beside it and, where none is, its cause. Read structurally: a
    rows adapter that snaps no measurement family (the qubit slice) records
    none, and the run then names no instance block.
    """
    if adaptation is None:
        return []
    snaps = adaptation.get("measurement_snaps")
    if not isinstance(snaps, Sequence) or isinstance(snaps, str):
        return []
    out: list[_SnapBlock] = []
    for snap in snaps:
        if not isinstance(snap, Mapping):
            continue
        setting = snap.get("setting")
        for block in snap.get("blocks") or ():
            if not isinstance(block, Mapping):
                continue
            out.append(
                _SnapBlock(
                    name=f"{block.get('block')}, t={setting}",
                    moved=block.get("status") == "moved",
                    handed=block.get("handed_reference") is not None,
                    cause=(
                        None if block.get("cause") is None else str(block["cause"])
                    ),
                    support_not_preserved=bool(block.get("support_not_preserved")),
                )
            )
    return out


def _stations(
    result: SliceResult,
) -> list[tuple[int | None, ProofReductionArtifact, Mapping[str, Any] | None]]:
    if getattr(result, "device_artifacts", ()):
        return [
            (index, emission.reduction, emission.rows_adaptation)
            for index, emission in enumerate(result.device_artifacts)
        ]
    artifact = getattr(result, "reduction_artifact", None)
    if artifact is not None:
        return [(None, artifact, getattr(result, "rows_adaptation", None))]
    return []


def _unevaluated_cause(
    status: str, cause: str | None, *, replaced: bool
) -> RestingCause:
    """Return the cause of a moved block the companion's bound did not cover.

    ``req:bracket-on-reference`` (iv): a withdrawn bracket names in the group
    reference bracket withdrawn only the blocks of a station whose link the
    companion replaces (``replaced``). A station it does not replace, because
    no companion was formed for it, is named as without a companion: its
    bracket was not evaluated (``foundations/req:snap-reference`` (iii)(c)),
    whatever became of the other station's.
    """
    if status == "withdrawn" and replaced:
        if cause == FACTOR_ENCLOSURE_INCONSISTENT:
            return RestingCause.FACTOR_ENCLOSURE_INCONSISTENT
        return RestingCause.REFERENCE_BRACKET_WITHDRAWN
    return RestingCause.REFERENCE_BRACKET_NOT_EVALUATED


def _certified_on_searched(key_rate: object) -> bool:
    """Whether the key length is formed from a number certified on ``D``, the searched.

    Read off the certified record (``req:certified-evaluation`` (ix)): status
    ``certified`` -- the key length is formed from the certified number -- on
    the declaration ``searched``. Beside a counted companion bound that is the
    fallback of item (i).
    """
    certified = getattr(key_rate, "certified", None)
    return (
        isinstance(certified, Mapping)
        and certified.get("status") == "certified"
        and certified.get("declaration") == ON_SEARCHED
    )


def _verdict(
    origin: str,
    block: str,
    cause: RestingCause | None,
    *,
    support_not_preserved: bool,
) -> RestingBlock:
    """Return the verdict: evaluated off its snap where ``cause`` is ``None``."""
    group = resting_group(cause, last_resort=support_not_preserved)
    return RestingBlock(
        origin=origin,
        block=block,
        group=None if group is None else str(group),
        cause=None if cause is None else str(cause),
        evaluated_off_snap=cause is None,
        support_not_preserved=support_not_preserved,
    )


def direct_route(
    result: SliceResult, *, certified_on_searched: bool | None = None
) -> DirectRoute:
    """Return the run's decision: what is evaluated off its snap, what still rests.

    Implements the run-record half of ``meat-core/frank-wolfe/
    req:bracket-on-reference`` (v) and (iv) with ``foundations/
    def:evaluated-off-snap`` (ii) and the groups of ``foundations/
    req:snap-reference`` (iii); see the module docstring.

    ``certified_on_searched`` says whether the number the decision is taken
    for is formed on the searched declaration; by default the number the
    run's key length is formed from (:func:`_certified_on_searched`).
    :func:`certified_premises` passes the certified number's declaration.
    """
    stations = _stations(result)
    # Read structurally: a result composed by hand (a test's, a caller's that
    # predates the direct route) carries neither, and reads as a run with no
    # companion.
    bracket: Mapping[str, Any] | None = getattr(
        result.key_rate, "reference_bracket", None
    )
    compiled = getattr(result, "reference_companion", None)
    cause: str | None = None
    if not stations:
        status, reason = "absent", None
    elif isinstance(compiled, NoCompiledCompanion) or compiled is None:
        status = "not_compiled"
        reason = None if compiled is None else str(compiled.reason)
    elif bracket is None:
        status, reason = "not_evaluated", None
    else:
        status = str(bracket.get("status"))
        reason = None if bracket.get("reason") is None else str(bracket["reason"])
        cause = None if bracket.get("cause") is None else str(bracket["cause"])
    counted = status == "counted" and isinstance(compiled, CompiledReferenceCompanion)
    if certified_on_searched is None:
        certified_on_searched = _certified_on_searched(result.key_rate)
    fallback = counted and certified_on_searched
    factors = (
        {}
        if not isinstance(compiled, CompiledReferenceCompanion)
        else {factor.position: factor for factor in compiled.factors}
    )
    declaration = getattr(result, "declaration", None)
    labels: tuple[str, ...] = (
        () if declaration is None else tuple(declaration.measured_factor_labels)
    )
    evaluations: list[StationEvaluation] = []
    for position, (station, artifact, adaptation) in enumerate(stations):
        companion = artifact.reference_companion
        formed = isinstance(companion, ReferenceCompanion)
        replaced = position in factors and formed
        carries = counted and replaced
        carried: frozenset[str] = (
            frozenset(block.name for block in companion.handed_blocks)
            if carries and isinstance(companion, ReferenceCompanion)
            else frozenset()
        )
        named: list[RestingBlock] = []
        kept: list[str] = []
        for block in _snap_blocks(adaptation):
            if not block.moved:
                kept.append(block.name)
                continue
            verdict: RestingCause | None
            if not block.handed:
                verdict = (
                    RestingCause(block.cause)
                    if block.cause is not None
                    else RestingCause.NO_REFERENCE
                )
            elif block.name in carried:
                verdict = RestingCause.COMPANION_NOT_CERTIFIED if fallback else None
            else:
                verdict = _unevaluated_cause(status, cause, replaced=replaced)
            named.append(
                _verdict(
                    INSTANCE_SNAP,
                    block.name,
                    verdict,
                    support_not_preserved=block.support_not_preserved,
                )
            )
        last_resort = artifact.emission_record.last_resort_sectors
        evaluated_sectors: set[int] = set()
        for index, _ in artifact.emission_record.moved_sectors:
            if carries and fallback:
                sector_cause: RestingCause | None = RestingCause.COMPANION_NOT_CERTIFIED
            elif carries:
                sector_cause = None
                evaluated_sectors.add(index)
            elif not formed:
                sector_cause = RestingCause.NO_REFERENCE_COMPANION
            else:
                sector_cause = _unevaluated_cause(status, cause, replaced=replaced)
            named.append(
                _verdict(
                    EMISSION,
                    f"data sector {index}",
                    sector_cause,
                    support_not_preserved=index in last_resort,
                )
            )
        evaluations.append(
            StationEvaluation(
                station=station,
                factor=labels[position] if position < len(labels) else None,
                instance_blocks=frozenset(
                    item.block
                    for item in named
                    if item.origin == INSTANCE_SNAP and item.evaluated_off_snap
                ),
                emission_sectors=frozenset(evaluated_sectors),
                kept_blocks=tuple(kept),
                named=tuple(named),
            )
        )
    return DirectRoute(
        status=status, reason=reason, stations=tuple(evaluations), fallback=fallback
    )


def certified_premises(result: SliceResult) -> dict[str, Any] | None:
    """Return ``premises`` and ``resting_blocks`` of the run's certified record.

    ``meat-core/frank-wolfe/req:certified-evaluation`` (ix): the short id of
    A-SNAP wherever a moved block or class of the declaration the certified
    number is formed on rests on it (``foundations/req:snap-reference`` (iii)),
    and those blocks as the run's record names them. The declaration is the
    record's ``declaration``: on the searched one every moved block or class
    rests, the companion's carried blocks with the cause
    ``companion_not_certified`` where its bound counts (the fallback); on a
    companion, the moved blocks it carries snapped and those of every snap it
    does not replace. ``None`` where the run has no certified record.
    """
    certified = getattr(result.key_rate, "certified", None)
    if not isinstance(certified, Mapping):
        return None
    on_searched = certified.get("declaration") == ON_SEARCHED
    decision = direct_route(result, certified_on_searched=on_searched)
    resting = decision.as_record()["resting_blocks"]
    return {
        "premises": [ASSUMPTION_ID] if resting else [],
        "resting_blocks": resting,
    }


def resting_names(evaluation: StationEvaluation) -> tuple[str, ...]:
    """Return the A-SNAP row's ``resting_blocks`` binding after the decision.

    ``<origin>: <block> (<group>: <cause>)``, restricted to what still rests.
    """
    return tuple(
        f"{block.origin}: {block.block} ({block.group}: {block.cause})"
        for block in evaluation.resting
    )


def _completed_receiver_fix(
    receiver_fix: object, verdict: RestingBlock
) -> str | None:
    """Return a block's receiver fix as the run's decision completes it.

    ``receiver/detector-imperfections/req:snap-fix``: the receiver states the
    fix of its own causes at the snap; the run completes the fix of a handed
    block once its search has decided whether the block rests. A block
    evaluated off its snap rests on nothing and is named with no fix, whether
    or not the last resort snapped it. A block resting for a cause of the
    run's (reference bracket withdrawn or not evaluated) is named with the fix
    ``foundations/req:snap-reference`` (iii) names for that cause and, where
    the last resort snapped it, the receiver's noise fix beside it.
    """
    if verdict.evaluated_off_snap or verdict.cause is None:
        return None
    text = receiver_fix if isinstance(receiver_fix, str) and receiver_fix else None
    cause = RestingCause(verdict.cause)
    if cause not in _RUN_CAUSES:
        return text
    return cause.fix if text is None else f"{cause.fix}; {text}"


#: The causes the run decides after its search, not the declarer at the snap.
_RUN_CAUSES: Final[frozenset[RestingCause]] = frozenset(
    {
        RestingCause.REFERENCE_BRACKET_WITHDRAWN,
        RestingCause.FACTOR_ENCLOSURE_INCONSISTENT,
        RestingCause.COMPANION_NOT_CERTIFIED,
        RestingCause.REFERENCE_BRACKET_NOT_EVALUATED,
    }
)


def annotate_snap_records(
    adaptation: Mapping[str, Any] | None, evaluation: StationEvaluation | None
) -> Mapping[str, Any] | None:
    """Return an instance's snap record with the run's decision on every block.

    ``foundations/req:who-snaps``: "the record of the run names every moved
    block of the snap that is evaluated off its snap, and every moved block
    that rests on A-SNAP, with its cause, group and fix; a kept block is named
    as kept and in neither list". Each block of every ``measurement_snaps``
    record gains ``evaluated_off_snap`` (``false`` on a kept block), and a
    moved block the run decided on carries that decision's
    ``rests_on_assumption``, cause, group and fixes; each snap's
    ``resting_blocks`` and ``assumption`` follow. Without an evaluation (no
    reduction stage) nothing is evaluated off its snap and the snap's own
    record stands.
    """
    if adaptation is None:
        return None
    out = dict(adaptation)
    snaps = out.get("measurement_snaps")
    if not isinstance(snaps, Sequence) or isinstance(snaps, str):
        return out
    annotated = []
    for snap in snaps:
        if not isinstance(snap, Mapping):
            annotated.append(snap)
            continue
        setting = snap.get("setting")
        blocks = []
        for block in snap.get("blocks") or ():
            if not isinstance(block, Mapping):
                blocks.append(block)
                continue
            name = f"{block.get('block')}, t={setting}"
            verdict = (
                None if evaluation is None else evaluation.verdict(INSTANCE_SNAP, name)
            )
            entry = {**block, "evaluated_off_snap": bool(
                verdict is not None and verdict.evaluated_off_snap
            )}
            if verdict is not None:
                entry.update(
                    {
                        "rests_on_assumption": not verdict.evaluated_off_snap,
                        "cause": verdict.cause,
                        "group": verdict.group,
                        "fix": verdict.fix,
                        "group_fix": verdict.group_fix,
                        "receiver_fix": _completed_receiver_fix(
                            block.get("receiver_fix"), verdict
                        ),
                    }
                )
            blocks.append(entry)
        resting = [
            str(block.get("block"))
            for block in blocks
            if isinstance(block, Mapping) and block.get("rests_on_assumption")
        ]
        fixes = {
            str(block.get("block")): block["receiver_fix"]
            for block in blocks
            if isinstance(block, Mapping) and block.get("receiver_fix") is not None
        }
        annotated.append(
            {
                **snap,
                "blocks": blocks,
                **({} if "receiver_fixes" not in snap else {"receiver_fixes": fixes}),
                "resting_blocks": resting,
                "assumption": (
                    None
                    if not resting
                    else {
                        "id": ASSUMPTION_ID,
                        "machine_key": ASSUMPTION_MACHINE_KEY,
                        "claim": ASSUMPTION_CLAIM,
                        "site": snap.get("site"),
                        "setting": setting,
                        "blocks": resting,
                    }
                ),
            }
        )
    out["measurement_snaps"] = annotated
    return out
