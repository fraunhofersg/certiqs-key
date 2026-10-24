"""What every part of the lowering shares: the records, the helpers, the state.

The lowering (:mod:`instances.declared.lowering`) is one class built up in
layers, one module per block of the document: this module's
:class:`_LoweringBase` holds one lowering's state and the helpers every layer
calls; :mod:`.source`, :mod:`.stations`, :mod:`.public`, :mod:`.constraints`,
:mod:`.honest` and :mod:`.providers` each add the methods of one block, each
on the layer before it.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from certiqs_key.domain.constraints import (
    AttackSetLicense,
)
from certiqs_key.foundations import exact
from certiqs_key.foundations.blocks import (
    PRODUCT_LABEL_SEPARATOR,
    BlockKind,
    SectorStructure,
)
from certiqs_key.foundations.snap import SnapSettings
from certiqs_key.protocol_compiler.chain import (
    ReductionChain,
)
from certiqs_key.protocol_compiler.spec import (
    ProtocolSpecification,
    PublicPart,
    ReceiverPart,
    SourcePart,
)
from certiqs_key.protocol_compiler.weights import (
    ChoiceWeighting,
)
from certiqs_key.runs.pipeline import (
    DeviceRequests,
    HonestProvider,
    MultiDeviceRequests,
    RawJointProvider,
    SpecificationProvider,
)
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.limits import MAX_ALPHABET_LABELS, check_size
from instances.declared.model import (
    ProtocolDocument,
    Sectors,
    Station,
)
from instances.declared.optical import (
    LoweredReceiver,
)
from instances.declared.rules import Entry, Expansion, Variable, build_alphabet, expand
from instances.declared.values import Environment, matrix, number

if TYPE_CHECKING:  # pragma: no cover - typing only
    from certiqs_key.runs.pipeline import ChannelInterfaceProvider
    from instances.common.honest import HonestContext
    from instances.common.wcp import PreparedSource
    from instances.declared.wcp import LoweredWcp


#: The premise each user-declared kind stands under.
#: The attack-set licence's premise is A-ATK
#: (``protocol_compiler/reasons.py``).
#: A declared receiver POVM names the premises the Band-A route ENGAGES:
#: A-SPEC and A-IDEAL, which the compiler emits on Band A
#: (``compile.py``, "if band_a: ... A_IDEAL"); A-TRUST is emitted only off
#: Band A, so naming it would link a premise the report does not carry.
ASSUMPTION_OF_KIND: Mapping[str, tuple[str, ...]] = {
    "constraint_entry": ("A-ATK",),
    "attack_set_license": ("A-ATK",),
    "feasibility_witness": (),
    "receiver_povm": ("A-SPEC", "A-IDEAL"),
    "retention_attestation": ("A-SRC",),
    # An optical station whose measurement is declared as numbers rather than
    # derived from catalogue optics: the optical route engages A-TRUST
    # (receiver/construct.py), the premise that the declared characterisation
    # is the device's.
    "receiver_characterisation": ("A-TRUST",),
}

#: The common opening of every user-declared item's text. It names
#: no author: a shipped template's declarations are recorded too, since the
#: user who runs it takes responsibility for them.
_DECLARED = (
    "Declared in the run's protocol document (your own or a shipped template), "
    "not derived by the engine; you vouch for it."
)

#: The sector block kind of every emitted target: the reductions' map is a
#: proof sector map (the Python optical instance's ``SECTOR_BLOCK_KIND``).
_KIND = BlockKind.PROOF_SECTOR


@dataclass(frozen=True)
class UserDeclared:
    """One premise the document supplies itself, flagged in the key-rate report."""

    kind: str
    path: str
    label: str
    text: str

    def as_record(self) -> dict[str, Any]:
        """Return the item as the record carries it."""
        return {
            "kind": self.kind,
            "path": self.path,
            "label": self.label,
            "text": self.text,
            "assumptions": list(ASSUMPTION_OF_KIND[self.kind]),
        }


@dataclass
class Lowered:
    """One configuration's lowering: what ``prepare`` and ``run_slice`` are given.

    Exactly one route is filled: ``specification`` on Band A; ``device`` with
    ``specification_provider`` for one optical station; ``device`` as a
    :class:`~certiqs_key.runs.pipeline.MultiDeviceRequests` (which carries
    its own provider and channel interface) for several. ``input_preparation``
    holds the records the lowering adds to the configuration's: the
    ``wcp_decoy`` source's preparation record, and the conversions of the
    receiver's float routes.
    """

    specification: ProtocolSpecification | None
    honest: HonestProvider
    raw: RawJointProvider | None
    #: The honest-model note, live: a library model may extend it at run time.
    note: dict[str, Any]
    channel_interface: ChannelInterfaceProvider | None
    expansions: dict[str, Expansion] = field(default_factory=dict)
    user_declared: list[UserDeclared] = field(default_factory=list)
    device: DeviceRequests | MultiDeviceRequests | None = None
    specification_provider: SpecificationProvider | None = None
    input_preparation: list[Mapping[str, Any]] = field(default_factory=list)
    #: Each optional field the configuration left absent: ``{path, parameter,
    #: read_as}`` (an ``exact_window`` that is a parameter the configuration
    #: does not carry).
    absent: list[dict[str, str]] = field(default_factory=list)
    #: The lowered public part (``S_pub``), as the specification carries it:
    #: built before the run on every route, so that it can be read without the
    #: artefacts an optical station's specification waits for (the tests of
    #: what an instance's public part declares read it).
    public: PublicPart | None = None
    #: A ``wcp_decoy`` source's preparation (the library's
    #: :class:`~instances.common.wcp.PreparedSource`): the tagged declaration
    #: before emission, its record and its letters; ``None`` for every other
    #: source. Read by the tests of the prepared source.
    wcp_source: PreparedSource | None = None
    #: The structure the honest library model is told, or
    #: ``None`` where the honest statistics are given as data (a table or an
    #: envelope). Read by the tests of the library models.
    honest_context: HonestContext | None = None

    def route(self) -> dict[str, Any]:
        """Return the route's keyword arguments of ``prepare`` and ``run_slice``."""
        if self.specification is not None:
            return {"specification": self.specification}
        if isinstance(self.device, MultiDeviceRequests):
            return {"device": self.device}
        return {
            "device": self.device,
            "specification_provider": self.specification_provider,
        }

    def record(
        self,
        *,
        document_id: str,
        packaged: bool,
        digest: str,
        canonical: Mapping[str, Any],
        conversions: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Return the ``protocol_document`` block of the run record."""
        return {
            "format_version": "1",
            "id": document_id,
            "packaged": packaged,
            "digest": digest,
            "canonical": dict(canonical),
            "conversions": [dict(item) for item in conversions],
            "expansion": {
                name: expansion.as_record()
                for name, expansion in self.expansions.items()
            },
            "unmatched": {
                name: [list(key) for key in expansion.unmatched]
                for name, expansion in self.expansions.items()
            },
            # EVERY DOCUMENT'S, A PACKAGED TEMPLATE'S TOO (the user still takes
            # responsibility for these when using the key rates): bb84's
            # declared POVM and decoy_bb84's retention attestation are premises
            # the engine did not derive, which the report asks the user to
            # vouch for.
            "user_declared": [item.as_record() for item in self.user_declared],
            "absent": [dict(item) for item in self.absent],
        }


def _topology(detail: str, path: str) -> DocumentError:
    """Refuse a combination the run tier has no route for."""
    return DocumentError(detail, reason=DocumentReason.UNSUPPORTED_TOPOLOGY, path=path)


def _fraction(node: object, environment: Environment, path: str) -> Fraction:
    return Fraction(number(node, environment, path))


def _ordered[T](mapping: Mapping[str, T], order: Sequence[str]) -> dict[str, T]:
    """Return ``mapping`` in the alphabet's order, any other key after, as written.

    A reordering only: the modules read these mappings by key, and a key the
    alphabet lacks is kept for the module to refuse.
    """
    ordered = {key: mapping[key] for key in order if key in mapping}
    ordered.update({key: value for key, value in mapping.items() if key not in ordered})
    return ordered


def _sectors(node: Sectors, path: str) -> SectorStructure:
    try:
        kind = BlockKind(node.block_kind)
    except ValueError:
        raise DocumentError(
            f"{node.block_kind!r} is not a block kind "
            f"({[str(member) for member in BlockKind]})",
            reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
            path=path + pointer("block_kind"),
        ) from None
    return SectorStructure(
        labels=tuple(node.labels), dims=tuple(node.dims), block_kind=kind
    )


def _split(
    key: str,
    left: Sequence[str],
    right: Sequence[str],
    path: str,
    what: str,
) -> tuple[str, str]:
    """Return the ``(a, b)`` a key ``"a|b"`` names, split where both are declared.

    A label may itself contain ``|``, so the key is split at the one place
    that gives a declared ``a`` and a declared ``b``.
    """
    splits = [
        (key[:index], key[index + 1 :]) for index, char in enumerate(key) if char == "|"
    ]
    found = [(a, b) for a, b in splits if a in left and b in right]
    if len(found) != 1:
        raise DocumentError(
            f"a {what} key is 'a|b' with both parts declared; {key!r} splits into "
            f"{len(found)} such pairs",
            reason=DocumentReason.DOCUMENT_SCHEMA_VIOLATION,
            path=path,
        )
    return found[0]


@dataclass(frozen=True)
class _Source:
    """The lowered source: its part, its alphabet's entries and what a model reads."""

    part: SourcePart
    entries: tuple[Entry, ...]
    alice_dim: int | None
    kind: str
    wcp: LoweredWcp | None = None

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(entry.label for entry in self.entries)


@dataclass(frozen=True)
class _Outcomes:
    """A station's outcomes as the public part reads them, with its identity."""

    id: str
    party: str
    entries: tuple[Entry, ...]


@dataclass(frozen=True)
class _BandA:
    """One Band-A station, lowered."""

    station: Station
    receiver: ReceiverPart
    outcomes: tuple[Entry, ...]
    sectors: SectorStructure
    chain: ReductionChain
    elements: Mapping[str, exact.Matrix]


@dataclass(frozen=True)
class _Optical:
    """One optical station, lowered: its receiver, its requests, its weighting."""

    station: Station
    receiver: LoweredReceiver
    device: DeviceRequests
    weighting: ChoiceWeighting | None
    #: The station's outcomes as the public part reads them: the emitted ``V``,
    #: or the weighted family's labels where a choice weighting is declared.
    entries: tuple[Entry, ...]


@dataclass(frozen=True)
class _Constraints:
    """The constraints block, its switches resolved, read once per lowering."""

    docked: bool
    view: str | None
    view_path: str
    entries: Sequence[Any]
    entries_path: str
    licence: AttackSetLicense | None
    witness: object
    witness_path: str


def _weighted_entry(outcome: Entry, label: str, choice: str) -> Entry:
    """Return one label of a choice-weighted family: ``v``'s components and the choice.

    The choice is the component ``choice``. A Band-A station
    declared by a choice family already gives its outcomes a ``choice`` (the
    basis), which a rule reads; there the weighting's choice is
    ``weighted_choice`` instead, so that neither shadows the other.
    """
    components = {
        name: value for name, value in outcome.components.items() if name != "label"
    }
    name = "weighted_choice" if "choice" in components else "choice"
    return Entry.of(label, {**components, name: choice})


def _joint(stations: Sequence[_Outcomes], path: str) -> tuple[Entry, ...]:
    """Return the joint outcome alphabet of several stations, in the product order.

    A joint label is the stations' labels joined by the product separator, the
    spelling the compiler gives a product of measured factors; its components
    are each station's label under the station's id and each station's
    components under ``<id>.<component>``, so a rule reads ``v.bob`` or
    ``v.bob.letter``.
    """
    check_size(
        math.prod(len(station.entries) for station in stations),
        MAX_ALPHABET_LABELS,
        "the joint outcome alphabet's size",
        path,
    )
    joint: list[Entry] = []
    for combination in itertools.product(*(station.entries for station in stations)):
        components: dict[str, str] = {}
        for station, entry in zip(stations, combination, strict=True):
            components[station.id] = entry.label
            for name, value in entry.components.items():
                if name != "label":
                    components[f"{station.id}.{name}"] = value
        joint.append(
            Entry.of(
                PRODUCT_LABEL_SEPARATOR.join(entry.label for entry in combination),
                components,
            )
        )
    return tuple(joint)


class _LoweringBase:
    """The state of one lowering: the document, the configuration's values."""

    def __init__(
        self,
        model: ProtocolDocument,
        environment: Environment,
        *,
        record_label: str,
        document_id: str,
        declared_tolerance: float,
        model_section: Mapping[str, Any] | None = None,
        work_bounds: bool = True,
        snap: SnapSettings | None = None,
    ) -> None:
        self.model = model
        self.env = environment
        self.record_label = record_label
        self.document_id = document_id
        self.declared_tolerance = declared_tolerance
        #: Whether the work bounds of :mod:`.limits` hold (a custom document).
        self.work_bounds = work_bounds
        self.model_section = dict(model_section or {})
        #: The run's snap parameters (``snap_settings`` of the configuration),
        #: which every optical station's snap and reduction request carry, as
        #: the Python instances' do.
        self.snap = snap or SnapSettings()
        self.named = model.alphabets
        self.expansions: dict[str, Expansion] = {}
        self.user_declared: list[UserDeclared] = []
        self.input_preparation: list[Mapping[str, Any]] = []
        self.absent: list[dict[str, str]] = []
        self.multi = len(model.stations) > 1

    # -- helpers ---------------------------------------------------------------

    def matrix(self, node: object, path: str) -> exact.Matrix:
        return matrix(node, self.env, path)

    def alphabet(self, node: object, path: str) -> tuple[Entry, ...]:
        return build_alphabet(node, self.named, path)  # type: ignore[arg-type]

    def expand(
        self, name: str, rules: object, variables: Sequence[Variable], path: str
    ) -> Expansion:
        expansion = expand(name, rules, variables, path=path, environment=self.env)
        self.expansions[name] = expansion
        return expansion

    def flag(self, kind: str, path: str, label: str, text: str) -> None:
        self.user_declared.append(UserDeclared(kind, path, label, text))

    def table_name(self, station: Station, table: str) -> str:
        """Return a station table's name in the record: per station where several."""
        return f"{station.id}.{table}" if self.multi else table
