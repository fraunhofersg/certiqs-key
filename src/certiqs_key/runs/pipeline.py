"""One slice, end to end: a specification in, a typed outcome out.

spec/architecture.md 6's flow, in one function and in one order:

    compile  ->  honest distribution  ->  acceptance set  ->  dock
             ->  write bundle  ->  read bundle  ->  validate  ->  solve

and, for a slice whose Bob is a physical device rather than a declared qubit
POVM, spec/architecture.md 6's two device stages in front of it:

    construct receiver  ->  dock its rows  ->  reduce  ->  build specification

Every stage belongs to a module with an accepted contract; this one belongs to
none, and computes nothing of its own. It is a caller, and it is deliberately
thin: the value of the slice is that a wrong number afterwards has one candidate
cause, so anything clever here would defeat its purpose.

THE DEVICE PROLOGUE IS OPTIONAL, AND ITS PARTS ARRIVE AS DATA
============================================================
A caller supplies EITHER a finished ``specification`` -- the qubit route, where
the receiver is a declared qubit POVM and there is no device to construct -- OR a
:class:`DeviceRequests` together with a :data:`SpecificationProvider`. Exactly
one; supplying both or neither is a :class:`SliceAssemblyError`, because this
tier may not decide which one was meant.

What crosses is DATA and one callable, and the split is the same one
:data:`HonestProvider` draws. The three requests are the instance's own
declarations -- which optics, which cutoff, which link -- and this module never
reads inside them. The callable is the instance's too: assembling a
``ProtocolSpecification`` needs the source part, the public part and the sector
structure, all of which are a protocol's identity, and
spec/architecture.md 3.3 keeps protocol identity out of this tier. What is owned HERE is
only the ORDER: construct before dock, dock before reduce, reduce before compile.

WHAT MAKES THIS PROTOCOL-AGNOSTIC, AND WHY IT HAS TO BE
=======================================================
Exactly one stage of that path is protocol-specific: the honest distribution.
Everything else consumes a compiled declaration and does not care what protocol
produced it. So the channel model arrives as a :data:`HonestProvider` supplied by
the instance, and this module never learns what a ``qber`` is.

That is the PRINCIPLES.md section 4 tier boundary in one argument. The alternative --
importing one instance's model here -- is what welded the first version of this file to
BB84, and it would have made the second slice a copy of the first rather than a second
caller of it.

EVERY REFUSAL IS AN OUTCOME, NOT AN EXCEPTION AND NOT A DEFAULT
==============================================================
Three of the four modules on that path can conformingly decline to answer, and
each declines in its own vocabulary:

``protocol-compiler``
    a :class:`~certiqs_key.protocol_compiler.CompilationResult` carrying a refusal and
    NO declaration. "A refusal emits *no* declaration", so there is nothing partial to
    hand on and nothing here tries.
``statistics``
    an :class:`~certiqs_key.statistics.InfeasibleInput` carrying one of the nine
    input-domain codes and NO acceptance set. It is a union rather than a record
    with optional fields precisely so that the fail-closed branch has nothing to
    read, and this module reads nothing.
``meat-core``
    a :class:`~certiqs_key.solvers.frank_wolfe.general_keyrate.GeneralKeyRateResult`
    with ``key_length = None`` and a ``key_length_reason`` naming the gate that
    closed -- an ``h_low`` of ``+inf``, a security gate, the ``alpha in (1, 2)``
    confinement, or a declaration not known to be the compiler's emission
    (``declaration_not_compiled``, ``req:compiled-declaration-only``; this
    tier passes the token whenever the bundle read back is the bundle
    written, so a run of it sees that one only on a round-trip defect, which
    its ``bundle_read`` stage records). That is a RESULT and not a refusal of the run,
    so it is carried on :class:`SliceResult` exactly as the engine emitted it.
``receiver``
    a :class:`~certiqs_key.receiver.construct.ReceiverEmission` carrying a
    ``Refusal`` and NO artifact, or -- one stage later -- a
    :class:`~certiqs_key.receiver.docking.DockingRefusal` from the adapter that
    fills the squasher's rows.
``reductions``
    a :class:`~certiqs_key.reductions.artifact.ReductionOutcome` whose ``emitted``
    is false, carrying that module's own reason, the rule that decided it, and a
    verification report which is present on BOTH branches.
``runs`` itself
    once, after the solve: the plausibility check
    (:mod:`certiqs_key.runs.plausibility`) refuses a result whose entropy
    bound exceeds what any key could carry, at the ``solve`` stage, under the
    run tier's own code ``entropy_bound_above_key_ceiling``
    (:class:`~certiqs_key.runs.errors.RunRefusalReason`), with the bound and
    the ceiling on the refusal.

All of them arrive at the caller as data. Nothing is retried with a different
argument, nothing is clamped, and no default is substituted for a missing datum.

THE ROWS ADAPTER IS THE CALLER'S, AND IT IS NOT A REPAIR THIS TIER PERFORMS
==========================================================================
``receiver`` evaluates in floating point (Definition ``def:evaluation-model``, Theorem
``thm:exact-and-evaluated`` (ii): "this contract asserts NO BOUND ON THE DIFFERENCE"),
while ``reductions`` decides its validity conditions EXACTLY. Neither module
bridges that, and neither may: ``reductions`` Section 4.13 is explicit that
a declared tolerance "is A LICENCE TO ACCEPT A DECLARATION AND NEVER A REPAIR",
and ``meat-core`` Section 4.23 repeats it for its own.

So an instance whose receiver is float-evaluated may supply a
:data:`RowsAdapter`, which turns the emitted artefact into the rows of the
family it DECLARES: it docks the artefact itself, in the block form it
declares (the instances' adapter docks the dark-composed blocks and snaps them
against the receiver's reference, ``foundations/req:who-snaps``).
That is a caller's act on a caller's declaration -- ``receiver``'s
Assumption A-TRUST already makes the declared receiver the device by hypothesis
and never verifies it -- and this module neither performs it, defines it, nor
supplies one. What this module does is run it at the one place it can go, carry
its refusal as an outcome, and put its report in the run record so that a run
which declared something says so.

THE ACCEPTANCE ALPHABET IS THE DECLARATION'S, AND IS CHECKED
============================================================
``statistics`` builds an acceptance set only on a matched alphabet and round
count (``statistics/def:matched-alphabet``): the alphabet, its enumeration and
``n`` are the consuming declaration's, and ``statistics/req:matched-alphabet``
routes that cross-artifact relation to bundle validation as a hard error rather
than to one of its reason codes. So the request built here is built FROM the
emitted declaration -- its acceptance alphabet in its declared order, the same
``n`` -- and the returned geometry's outcome order is compared against it before
anything is docked (:func:`_require_matched_alphabet`). A disagreement is
:class:`SliceAssemblyError`: a defect in one of the two modules, not a refusal
by either.

WHAT IS NOT HERE
================
No alpha search. ``meat-core`` deliberately contains none -- Eq. ``eq:keylength``
holds at every ``alpha`` in ``(1, 2)`` and choosing one is a caller's business --
and spec/architecture.md 6 draws the "outer alpha search within the active
profile domain" between the configuration and the run, in the run tier.
That search is :mod:`certiqs_key.runs.alpha_search`, opted into by
:attr:`RunConfig.alpha_search <certiqs_key.runs.config.RunConfig.alpha_search>`
and wired into every instance's runner by
:func:`~certiqs_key.runs.alpha_search.searching_runner`: it calls this
function once per candidate alpha and attaches the search to the chosen
outcome. :func:`run_slice` itself still takes one ``alpha`` or the declared
default, runs once, and reports. A harness that wants a grid runs this
function once per point.

No oracle default either. The linear oracle is a REQUIRED argument, because the
capability probe that decides whether the oracle can serve the declaration is
``meat-core``'s gate, which refuses an oracle that cannot (spec/architecture.md
3.3, 7.3), and quietly constructing a particular backend here would decide
something this module does not own.

And no tolerance default -- and no tolerance FORWARDED, because there is
nothing left to forward it to. ``declared_tolerance`` is the instance's ``tau``
and spec/architecture.md 2.8 puts it in exactly one place: it is "the ceiling on
the pre-snap defect an instance may repair", and "modules receive no tolerance
to reason with". So this tier reads it off the run configuration, hands it to
the INSTANCE's snap -- the only caller entitled to it -- records it, and hands
it to nobody else.

THIS TIER PASSES NO TOLERANCE, NOT EVEN ``0.0``. The engine's
tolerance apparatus does not exist:
:func:`~certiqs_key.meat_core.declaration.bundle.declaration_from_bundle` and
:func:`~certiqs_key.solvers.frank_wolfe.solve_bundle` take no tolerance at all,
``reductions`` carries ``lattice_exponent`` where a tolerance row would be --
a SET of representable values and not a distance -- and
``protocol-compiler`` has no such row either. A constant here spelling a zero
nobody is passed would be this tier declaring something on a module's behalf.
``meat-core``'s ``prop:optol-nobound`` is why no consumer-side tolerance could
buy anything.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Any

from certiqs_key.domain.bundle import (
    OperatorBundle,
    read_bundle,
    write_bundle,
)
from certiqs_key.foundations.blocks import default_factor_label
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import (
    KeyLengthParameters,
    ProtocolDeclaration,
)
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.docking import compiler_emission, dock_declaration
from certiqs_key.meat_core.docking_statistics import acceptance_set_record
from certiqs_key.meat_core.errors import (
    CertificationRefusedError,
    SecurityStatementVacuousError,
)
from certiqs_key.meat_core.general_docking import dock_general_candidate
from certiqs_key.protocol_compiler import (
    CandidateDeclaration,
    CompilationResult,
    ProtocolSpecification,
    PublicChoices,
    compile_specification,
)
from certiqs_key.protocol_compiler.companion import (
    CompiledReferenceCompanion,
    NoCompiledCompanion,
    compile_reference_companion,
)
from certiqs_key.protocol_compiler.compile import FactorWeighting
from certiqs_key.protocol_compiler.weights import setting_joint_label
from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
from certiqs_key.receiver.construct import construct_receiver
from certiqs_key.receiver.docking import DockingRefusal, receiver_artifact_rows
from certiqs_key.receiver.reasons import AssumptionId as ReceiverAssumption
from certiqs_key.receiver.request import ReceiverRequest
from certiqs_key.reductions.artifact import (
    ProofReductionArtifact,
    ReductionOutcome,
    VerificationReport,
)
from certiqs_key.reductions.inputs import (
    CarriedOperatorRequest,
    ReceiverArtifactRows,
    ReductionCall,
    ReductionRequest,
)
from certiqs_key.reductions.inputs import ProtocolDeclaration as ReductionDeclaration
from certiqs_key.runs.chain_provenance import attest_chain_provenance
from certiqs_key.runs.channel import (
    BipartiteChannelInterface,
    ChannelInterface,
    ModeIntensityChannelInterface,
    OpticalChannelArm,
    SourceChannelInterface,
    mode_role,
)
from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.direct_route import DirectRoute, direct_route
from certiqs_key.runs.errors import RunRefusalReason, SliceAssemblyError
from certiqs_key.runs.flow import (
    Artefact,
    ArtefactKind,
    FlowRecorder,
    StageChild,
    StageObserver,
    StageRecord,
    artefact_digest,
    bundle_digest,
)
from certiqs_key.runs.general_wire import build_general_bundle
from certiqs_key.runs.plausibility import plausibility_check
from certiqs_key.runs.receiver_provenance import attest_receiver_provenance
from certiqs_key.runs.stages import SliceStage
from certiqs_key.runs.statistics_check import (
    UNREACHABLE_REASON,
    RunCheck,
    honest_supplied_from_note,
    refusal_detail,
    run_check,
)
from certiqs_key.runs.wire import WireLabels, build_bundle
from certiqs_key.solvers.frank_wolfe import (
    FrankWolfeOptions,
    NegativeObjectiveError,
    solve_bundle,
)
from certiqs_key.solvers.frank_wolfe.general_keyrate import GeneralKeyRateResult
from certiqs_key.solvers.frank_wolfe.joint_options import WarmStartRefused
from certiqs_key.solvers.frank_wolfe.keyrate import bound_minimal_divergence_of_bundle
from certiqs_key.solvers.oracles.protocol import LinearOracle
from certiqs_key.solvers.types import SearchRequest
from certiqs_key.statistics import (
    AcceptanceConstruction,
    AcceptanceRequest,
    HonestEnvelope,
    InfeasibilityReport,
    InfeasibleInput,
    construct,
)
from certiqs_key.statistics.rules import EndpointRuleName, TailEvaluation

if TYPE_CHECKING:
    from certiqs_key.meat_core.finitekey.consistency import StatisticsConsistency
    from certiqs_key.runs.alpha_search import AlphaSearchResult

__all__ = [
    "AdaptedRows",
    "AdapterRefusal",
    "ChannelInterfaceProvider",
    "DeviceEmission",
    "DeviceRequests",
    "HonestProvider",
    "LossAppliedProvider",
    "LossAppliedRawProvider",
    "MultiDeviceRequests",
    "MultiSpecificationProvider",
    "Preparation",
    "PreparationOutcome",
    "RawJointProvider",
    "RowsAdapter",
    "SliceOutcome",
    "SliceRefusal",
    "SliceResult",
    "SliceStage",
    "SpecificationProvider",
    # RE-EXPORTED DELIBERATELY: an instance's runner takes an observer and
    # imports it from here, beside ``run_slice`` which consumes it. mypy's
    # ``no_implicit_reexport`` is what makes the difference between a name this
    # module offers and one it merely imported, and this one is offered.
    "StageObserver",
    "StageRecord",
    "Station",
    "factored_loss_applied",
    "prepare",
    "raw_factored_loss_applied",
    "run_slice",
]

#: An instance's honest channel model, as this tier sees it: a declaration in, a
#: distribution on that declaration's acceptance alphabet out. Its own model
#: parameters -- ``qber`` for the BB84 depolarizing model -- are closed over by
#: the instance that builds it and are invisible here, which is what keeps
#: channel-model vocabulary out of the orchestration tier (PRINCIPLES.md section 4).
#:
#: The requirement that travels with any such provider is not this tier's to
#: enforce and not optional: it emits JOINT PER-OUTCOME probabilities on the
#: declared acceptance alphabet, never a sifted QBER, because Assumption A-TSM
#: binds the ``output_state`` test-statistics model.
#:
#: A provider may instead return a ``statistics`` :class:`HonestEnvelope` --
#: a per-outcome range ``[p^-, p^+]`` under Assumption A-HON-ENV, for an honest
#: channel that drifts -- and this tier forwards it to ``statistics`` as the
#: input ``honest_envelope`` without reading it.
type HonestProvider = Callable[
    [CandidateDeclaration], Mapping[str, Fraction] | HonestEnvelope
]


@dataclass(frozen=True)
class LossAppliedProvider:
    """An honest provider that DECLARES its law the device's under a factored loss.

    ``receiver/detector-imperfections/req:loss-before-evaluation``: where a
    station's receiver was compiled at its normalized station, factored loss
    ``t < 1``, every evaluation of its emitted measurement that stands for the
    receiver's statistics -- the honest law among them -- is made on
    ``Lambda^loss_t(rho)``, each station with its own ``t``, and a consumer
    that cannot apply the loss refuses with ``factored_loss_not_applied``.

    A provider is a bare callable and this tier cannot see what it
    evaluates, so the provider SAYS SO by being wrapped here: a library honest
    model applies each station's loss to the state it hands the declaration
    (or reads the device's own declared parameters and never the emitted
    measurement), and a declared table is the device's statistics as given.
    :func:`run_slice` refuses an unwrapped provider at the ``honest_model``
    stage wherever some station's ``t`` is below one, BEFORE calling it,
    rather than let a law of a more efficient receiver set the acceptance
    set. Where every ``t`` is one the wrapper changes nothing. The raw
    ``X x V`` provider carries a marker of its own,
    :class:`LossAppliedRawProvider`, checked by :func:`prepare`.
    """

    provider: HonestProvider

    def __call__(
        self, declaration: CandidateDeclaration
    ) -> Mapping[str, Fraction] | HonestEnvelope:
        """Return the wrapped provider's law, unchanged."""
        return self.provider(declaration)


def factored_loss_applied(provider: HonestProvider) -> HonestProvider:
    """Return ``provider`` declared to apply every station's factored loss.

    See :class:`LossAppliedProvider`; wrapping twice is wrapping once.
    """
    if isinstance(provider, LossAppliedProvider):
        return provider
    return LossAppliedProvider(provider)


@dataclass(frozen=True)
class AdapterRefusal:
    """A caller's rows adapter declined, in the caller's own vocabulary.

    Deliberately a bare pair of strings. The reason is the ADAPTER'S -- this tier
    owns no refusal vocabulary and invents none -- and the envelope is the same
    one :class:`SliceRefusal` uses to carry a module's code.
    """

    reason: str
    detail: str


@dataclass(frozen=True)
class AdaptedRows:
    """What a rows adapter returns when it does not decline.

    ``report`` is whatever the adapter wants recorded about what it did -- a
    lattice, a displacement, which blocks it touched. It is JSON-ready data that
    this package never interprets and :mod:`certiqs_key.runs.record` transcribes.
    """

    rows: ReceiverArtifactRows
    report: Mapping[str, object] = field(default_factory=dict)


#: A caller's hook between ``receiver``'s emitted artefact and the family it
#: DECLARES to ``reductions``. See the module docstring: the platform
#: performs no repair, and an adapter is a declaration rather than one. It is
#: handed the ARTEFACT, not docked rows, because what it declares is read off
#: more than the rows carry -- the dark-composed blocks and the reference the
#: receiver offers for them (``receiver/detector-imperfections/
#: req:dark-composed-reference``) -- and it docks the artefact itself, in the
#: form it declares (``reductions/wpfss`` input ``photon_blocks_form``).
type RowsAdapter = Callable[
    [ReceiverMeasurementArtifact], AdaptedRows | AdapterRefusal
]


#: THE INSTANCE'S REDUCTION ENTRY POINT, as this tier sees it: the declared
#: inputs in, an outcome out. It is an ARGUMENT and not an import, for the
#: reason the honest provider and the specification provider are: WHICH
#: reduction instance a device declares -- the flat one, a branching one, a
#: register-conditioned one -- is a statement about the device, and
#: ``reductions`` types it as an instance builder chosen at the call
#: (``def:reduction-instance``). A branching model is a REMOVABLE submodule's
#: and the choice an entry point, so what this tier passes through unread is a
#: callable. What is owned HERE is only the order.
type ReductionEntry = Callable[[ReductionCall], ReductionOutcome]


#: A caller's hook that reads a BASELINE reduction artifact and returns the
#: carried operators to ask for on a second pass. See
#: :attr:`DeviceRequests.carried_operator_provider`. Returning ``()`` is the
#: same as declaring no provider: the baseline emission is the emission.
type CarriedOperatorProvider = Callable[
    [ProofReductionArtifact], tuple[CarriedOperatorRequest, ...]
]


@dataclass(frozen=True)
class Station:
    """WHICH MEASURED FACTOR A STATION EMITS, AND FOR WHICH PARTY.

    THE ONE HOME OF A STATION'S IDENTITY. The instance
    declares it on :attr:`DeviceRequests.station`; the run record copies it
    onto ``payload.stages.stations[i]``, each per-station stage of
    ``composition_flow`` names it (:attr:`~certiqs_key.runs.flow.StageRecord.station`),
    and an instance's per-station parameters name it
    (:attr:`~certiqs_key.runs.surface.ParameterSpec.station`). The last two
    carry :attr:`factor` and nothing else: they are references to this record,
    not second declarations of it.

    ``factor`` IS THE KEY AND ``party`` IS NOT, for the reason the compiled
    declaration gives: "a party may hold TWO measured factors -- two stations
    of one party" (``CandidateDeclaration.measured_factor``), so a party label
    does not identify a station and a reference by party would be ambiguous in
    exactly the case a second station of one party creates. ``factor`` is the
    label of the measured factor this station's receiver becomes in the
    declaration (``sector_factorisation``'s per-factor label); ``party`` is the
    party that factor is scoped to. Both are the declaration's own strings.

    DECLARED, AND CHECKED AGAINST THE DECLARATION. Pairing station ``i`` with
    the ``i``-th measured factor by position would be an inference the record
    does not state. :func:`_prepare` holds every
    station against the compiled declaration's measured factors -- each
    station names one, with that factor's party, and every measured factor is
    named by exactly one station -- and a disagreement is a
    :class:`SliceAssemblyError`, as a disagreement about the channel
    interface's modes is.
    """

    factor: str
    party: str

    def __post_init__(self) -> None:
        """Refuse an empty label: an empty reference names nothing."""
        if not self.factor or not self.party:
            raise SliceAssemblyError(
                f"a station names a non-empty factor and party; got {self!r}"
            )

    def as_payload(self) -> dict[str, str]:
        """Return the JSON form the run record carries."""
        return {"factor": self.factor, "party": self.party}


@dataclass(frozen=True)
class DeviceRequests:
    """The three declarations a physical Bob needs, plus the caller's adapter.

    Every field is the INSTANCE's own and is passed through unread. They are
    grouped into one record rather than spread over four arguments of
    :func:`run_slice` because they are selected together and travel together --
    the same reason :class:`~certiqs_key.runs.config.RunConfig` exists.
    """

    #: ``receiver`` Section 2.1: the fourteen input keys.
    receiver_request: ReceiverRequest
    #: ``reductions`` Section 2.1 group 2, aliased on import because
    #: ``meat-core`` has a ``ProtocolDeclaration`` of its own and they are
    #: different objects of different contracts.
    reduction_declaration: ReductionDeclaration
    #: ``reductions`` Section 2.1 group 3, carrying ``lattice_exponent``.
    reduction_request: ReductionRequest
    #: The instance's reduction entry point. See :data:`ReductionEntry`: it has
    #: NO DEFAULT, because a default would be this tier choosing which
    #: reduction instance a device declares.
    reduction_entry: ReductionEntry
    #: Optional. ``None`` hands the emitted rows on untouched.
    rows_adapter: RowsAdapter | None = None
    #: THE RUN OPTION ``reference_enclosure`` (``foundations/req:snap-reference``
    #: (i)), the instance's as its snap settings carry it. Read here for one
    #: thing only: the receiver is constructed with ``exact_reference_only``
    #: exactly where the run declares enclosed references not used
    #: (``receiver/detector-imperfections/req:dark-composed-reference`` (vi)).
    #: Every other run is offered the enclosed reference too, which the
    #: instance hands beside its snap and the first-order bound reads
    #: (``foundations/def:evaluated-off-snap`` (i);
    #: ``meat-core/frank-wolfe/req:bracket-on-reference``).
    reference_enclosure: bool = True
    #: Optional. Builds ``carried_operators`` from a BASELINE reduction, which
    #: makes the reduction stage run TWICE. ``None`` runs it once.
    #:
    #: WHY THIS SEAM EXISTS AND WHY IT IS HERE. Some of ``reductions``'
    #: carried operators are written in terms of the emission they are about:
    #: Eq. ``eq:two-sector-entry``'s operator is ``F^FSS_e - a Pi_{<=N} - b Pi_Flag``,
    #: built from the EMITTED target element and certified against the emitted
    #: squashing channel's identity, and a caller cannot construct either before
    #: the emission exists. The module's own test suite drives it exactly this
    #: way -- reduce once, read the artifact, rebuild the request, reduce again.
    #:
    #: It is a field of this record rather than of the instance because a second
    #: pass is an ORDERING fact, and order is what this tier owns
    #: (spec/architecture.md 3.3: "runs -- composition, order, record").
    #: WHICH entries are asked for stays the instance's: this tier calls the
    #: provider and never looks inside what it returns. The receiver is
    #: constructed once and the rows adapted once; only the reduction repeats,
    #: on the same rows, so the two passes differ in exactly the requested
    #: operators and in nothing else.
    carried_operator_provider: CarriedOperatorProvider | None = None
    #: WHICH MEASURED FACTOR THIS DEVICE IS, on a multi-station route. See
    #: :class:`Station`. REQUIRED of every station of a
    #: :class:`MultiDeviceRequests` and REFUSED on the single-device route,
    #: where there is one receiver and nothing to tell apart: a field that
    #: meant something on one route and was ignored on the other would be
    #: two meanings for one key.
    station: Station | None = None
    #: WHETHER THE SPECIFICATION THE INSTANCE WILL BUILD APPLIES A PUBLIC CHOICE
    #: AT THIS DEVICE'S MEASURED FACTOR (a ``choice_weighting`` or a
    #: choice-weighted physical family there), handed to the reduction as
    #: ``ReductionCall.public_choice_applied``: A-TSM's emission rule reads it
    #: (reductions ``interface.yaml``). The
    #: instance says so because the specification is built only after the
    #: reduction; ``None`` ("not told") keeps the A-TSM row, the safe default.
    #: :func:`_check_public_choice_told` holds a ``False`` to the specification.
    public_choice_at_station: bool | None = None


#: Builds the compiler's specification once both artifacts exist. The instance's,
#: because a specification carries a protocol's identity: its source part, its
#: announcements, its acceptance statistic.
type SpecificationProvider = Callable[
    [ReceiverMeasurementArtifact, ProofReductionArtifact], ProtocolSpecification
]


@dataclass(frozen=True)
class DeviceEmission:
    """One station's emitted artifacts and the prepared call that produced them."""

    receiver: ReceiverMeasurementArtifact
    reduction: ProofReductionArtifact
    call: ReductionCall
    rows_adaptation: Mapping[str, object] | None
    upstream: tuple[str, ...]
    #: The station's declared identity, carried from
    #: :attr:`DeviceRequests.station` so that the record reads it off the
    #: emission it transcribes. ``None`` on the single-device route.
    station: Station | None = None


type MultiSpecificationProvider = Callable[
    [tuple[DeviceEmission, ...]], ProtocolSpecification
]


@dataclass(frozen=True)
class MultiDeviceRequests:
    """Ordered stations, composed only after all station artifacts exist."""

    devices: tuple[DeviceRequests, ...]
    specification_provider: MultiSpecificationProvider
    channel_interface_provider: Callable[
        [tuple[DeviceEmission, ...]], SourceChannelInterface
    ] | None = None

    def __post_init__(self) -> None:
        """Require a nonempty station order, each station named once."""
        if not self.devices:
            raise SliceAssemblyError("a multi-device request needs a station")
        factors = [
            None if device.station is None else device.station.factor
            for device in self.devices
        ]
        if None in factors:
            raise SliceAssemblyError(
                "every station of a multi-device request declares which "
                "measured factor it is (DeviceRequests.station); a consumer "
                "would otherwise pair stations with factors by position"
            )
        if len(set(factors)) != len(factors):
            raise SliceAssemblyError(
                f"the stations name the factors {factors}; each measured "
                "factor is one station"
            )


@dataclass(frozen=True)
class SliceRefusal:
    """A module on the path conformingly declined, and said why.

    ``reason`` is the refusing module's own machine-readable code -- a
    ``protocol-compiler`` refusal reason, or one of ``statistics``'s
    nine input-domain codes -- never a code this module invented. ``detail`` is
    that module's own message. THE ONE EXCEPTION is the run tier's own check
    of a result (:class:`~certiqs_key.runs.errors.RunRefusalReason`, record
    schema 0.25.0): the plausibility check refuses at ``solve`` under its own
    code, and :attr:`plausibility` carries its numbers.
    """

    stage: SliceStage
    reason: str
    detail: str
    #: The compilation that produced this, where one ran. Present on an
    #: acceptance refusal too: the declaration exists there, and a caller
    #: diagnosing an infeasible request needs the alphabet it was built on.
    compilation: CompilationResult | None = None
    #: ``statistics``'s own report, on its branch.
    infeasibility: InfeasibilityReport | None = None
    #: The receiver artifact, where one was built before the refusal. Present on
    #: a docking or reduction refusal, which is where it is wanted.
    receiver_artifact: ReceiverMeasurementArtifact | None = None
    #: ``reductions``' verification report, which that module emits on
    #: BOTH branches and which names every row it decided.
    verification_report: VerificationReport | None = None
    #: The rule ``reductions`` refused under, beside its reason.
    rule: str | None = None
    #: THE COMPOSITION-FLOW VIEW of this run, up to and including the stage
    #: that declined, with every stage after it marked ``not_executed``. See
    #: :mod:`certiqs_key.runs.flow`: it is recorded AS THE PATH IS TAKEN and is
    #: never reconstructed from what a refusal happens to carry.
    stages: tuple[StageRecord, ...] = ()
    #: Stations already emitted before this refusal, in preparation order.
    device_artifacts: tuple[DeviceEmission, ...] = ()
    #: THE PROTOCOL DOCUMENT this run was lowered from (record schema 0.21.0),
    #: or ``None`` where a Python instance or a hand-composed caller ran it.
    #: Uninterpreted here: the document layer (``instances/declared``) writes
    #: it through :func:`~certiqs_key.runs.inputs.attach_protocol_document`
    #: and the record carries it as ``payload.protocol_document``.
    protocol_document: Mapping[str, Any] | None = None
    #: THE OUTER ALPHA SEARCH that chose this run (record schema 0.24.0), or
    #: ``None`` for a run at one alpha. Attached by the run tier's search
    #: (:func:`certiqs_key.runs.alpha_search.attach_alpha_search`), never by
    #: :func:`run_slice`, which runs one alpha; the record reads it through
    #: the solve stage's ``alpha`` child, which the same call fills.
    alpha_search: AlphaSearchResult | None = None
    #: THE PLAUSIBILITY CHECK that refused this run (record schema 0.25.0),
    #: :meth:`~certiqs_key.runs.plausibility.PlausibilityCheck.as_record`: the
    #: bound, the ceiling and its two factors, beside the estimate. ``None``
    #: on every other refusal: an ``acceptance_set_unreachable`` refusal is
    #: decided before any order is evaluated (record schema 0.46.0), so no
    #: plausibility check runs there.
    plausibility: Mapping[str, Any] | None = None
    #: THE CHECK OF THE ACCEPTANCE SET AGAINST THE FEASIBLE STATISTICS
    #: (``meat-core/req:unreachable-acceptance-set``; record schema 0.37.0):
    #: whether the run is checked and why not, and on a checked run the bound,
    #: the cap and its decision, and each order's diagnostic. Set by
    #: :func:`run_slice` on every outcome it returns; on a searched run the
    #: search sets the whole run's.
    statistics_consistency: StatisticsConsistency | None = None

    @property
    def refuses(self) -> bool:
        """Whether this outcome is a refusal. Always true; see :class:`SliceResult`."""
        return True


@dataclass(frozen=True)
class SliceResult:
    """One completed run, with every intermediate record it passed through.

    The records are carried rather than recomputed so that a caller can see what
    each stage produced without re-running it -- and so that a test asserting a
    number can assert the record it came from in the same breath.
    """

    compilation: CompilationResult
    declaration: CandidateDeclaration
    #: What the honest provider returned: a distribution, or an envelope.
    honest_distribution: Mapping[str, Fraction] | HonestEnvelope
    acceptance: AcceptanceConstruction
    docked: ProtocolDeclaration | GeneralDeclaration
    bundle_directory: Path
    bundle: OperatorBundle
    #: The declaration as ``meat-core`` read it back off the disk. Distinct from
    #: :attr:`docked` in representation and equal to it in content, which is what
    #: the round trip is for.
    reread: ProtocolDeclaration | GeneralDeclaration
    labels: WireLabels
    key_rate: GeneralKeyRateResult
    #: ``tau`` as the run DECLARED it. No module was told it and no module has
    #: a row for it; it is carried so that the record can say what ceiling the
    #: instance's snap was allowed to spend. REQUIRED, with no default, for the
    #: reason it is required everywhere: a defaulted ceiling on repair decides a
    #: security-relevant act on nobody's authority (spec/architecture.md 2.8).
    declared_tolerance: float
    #: THE COMPOSITION-FLOW VIEW of this run: every stage of the route it took,
    #: in order, recorded as it was taken (:mod:`certiqs_key.runs.flow`).
    stages: tuple[StageRecord, ...] = ()
    #: HOW ``A'`` ENTERED THE RECEIVER, where the instance declared it.
    channel_interface: SourceChannelInterface | None = None
    #: The honest per-round distribution over the raw outcome pairs ``X x V``,
    #: where the instance's honest model computes it.
    raw_joint_distribution: Mapping[tuple[str, str], Fraction] | None = None
    #: WHICH HONEST MODEL PRODUCED THE DISTRIBUTION, verbatim and
    #: uninterpreted. spec/architecture.md 3.2: "a profile states which honest
    #: model its eps_comp was computed under". Where a caller injects a
    #: provider -- a table, a digital twin -- no function of the emitted data
    #: can say what it was, so the caller says it and the record carries it.
    honest_model_note: Mapping[str, Any] | None = None
    #: The specification this run compiled. Carried for the same reason every
    #: other intermediate record is -- so that a caller can see what each stage
    #: was given without re-running it -- and read by the record for the
    #: transmitter's consumed version, which no other artefact on this path
    #: carries.
    specification: ProtocolSpecification | None = None
    #: The device prologue's two artifacts, absent on the route that supplies a
    #: finished specification. Carried rather than recomputed, for the reason
    #: every other record here is.
    receiver_artifact: ReceiverMeasurementArtifact | None = None
    reduction_artifact: ProofReductionArtifact | None = None
    #: What the caller's rows adapter reported about what it declared. ``None``
    #: where no adapter ran. THE INSTANCE'S SNAP RECORD lives here: it is the
    #: one place on this path where declared device data is moved, and
    #: spec/architecture.md 2.8 requires every snap to reach the run
    #: record with its pre-snap defect and its displacement.
    rows_adaptation: Mapping[str, object] | None = None
    #: The forwarded budget: the Frank-Wolfe budget this run was driven at, or
    #: ``None`` for the declared default. Recorded beside the gap it explains, so that a
    #: record reporting ``iteration-limit`` says what the limit was.
    solver_options: FrankWolfeOptions | None = None
    solver_request: SearchRequest | None = None
    device_artifacts: tuple[DeviceEmission, ...] = ()
    #: THE PROTOCOL DOCUMENT this run was lowered from (record schema 0.21.0),
    #: or ``None`` where a Python instance or a hand-composed caller ran it.
    #: Uninterpreted here: the document layer (``instances/declared``) writes
    #: it through :func:`~certiqs_key.runs.inputs.attach_protocol_document`
    #: and the record carries it as ``payload.protocol_document``.
    protocol_document: Mapping[str, Any] | None = None
    #: THE OUTER ALPHA SEARCH that chose this run (record schema 0.24.0), or
    #: ``None`` for a run at one alpha. Attached by the run tier's search
    #: (:func:`certiqs_key.runs.alpha_search.attach_alpha_search`), never by
    #: :func:`run_slice`, which runs one alpha; the record reads it through
    #: the solve stage's ``alpha`` child, which the same call fills.
    alpha_search: AlphaSearchResult | None = None
    #: The compiled reference companion the solve evaluated the first-order
    #: bound on, or the record of why none was compiled (see
    #: :attr:`Preparation.reference_companion`); the key-rate result's
    #: ``reference_bracket`` says whether that bound counted.
    reference_companion: CompiledReferenceCompanion | NoCompiledCompanion | None = None
    #: The check of the acceptance set against the feasible statistics; see
    #: :attr:`SliceRefusal.statistics_consistency`.
    statistics_consistency: StatisticsConsistency | None = None

    @property
    def refuses(self) -> bool:
        """Whether this outcome refused. Always false; cf. :class:`SliceRefusal`."""
        return False


#: What :func:`run_slice` returns. A union rather than one record with optional
#: fields, so that a refusal has nothing to read -- the same shape
#: ``statistics`` chose for the same reason.
SliceOutcome = SliceResult | SliceRefusal


#: An instance's honest model over the RAW OUTCOME PAIRS, as this tier sees it.
#: A declaration in, the per-round distribution on ``X x V`` out, as exact
#: rationals and before any coarse-graining to the acceptance alphabet.
#:
#: WHY IT IS A SECOND PROVIDER AND NOT A WIDENING OF THE FIRST. What the
#: acceptance construction consumes is the distribution on the DECLARED
#: ACCEPTANCE ALPHABET, and that is what :data:`HonestProvider` emits and what
#: statistics/def:matched-alphabet binds; the raw table is a different object
#: over a different index set, wanted by a caller that needs an
#: error-correction estimate, a conditional entropy or a per-outcome view, none
#: of which the acceptance alphabet can express (the compiler declares only the
#: holder's raw key map).
#: Making one provider return both would make the proof-critical one carry a
#: payload nothing on the proof path reads.
#:
#: IT IS OPTIONAL, AND ``None`` IS AN HONEST ANSWER. An instance whose honest
#: model computes only the coarse distribution supplies none, and
#: :attr:`Preparation.raw_joint_distribution` is ``None`` rather than a table
#: this tier reconstructed -- which it could not: coarse-graining is not
#: invertible.
type RawJointProvider = Callable[
    [CandidateDeclaration], Mapping[tuple[str, str], Fraction]
]


@dataclass(frozen=True)
class LossAppliedRawProvider:
    """A raw ``X x V`` provider DECLARING its law the device's under a factored loss.

    ``receiver/detector-imperfections/req:loss-before-evaluation`` binds every
    evaluation of a receiver's emitted measurement that stands for the
    receiver's statistics, and the raw law is one: the error-correction
    estimate (:mod:`certiqs_key.runs.error_correction`) and the record's raw
    table are formed from it. So it carries the marker of
    :class:`LossAppliedProvider` on its own, and :func:`prepare` refuses an
    unwrapped raw provider with ``factored_loss_not_applied`` wherever some
    station's ``t`` is below one, BEFORE calling it. Where every ``t`` is one
    the wrapper changes nothing.
    """

    provider: RawJointProvider

    def __call__(
        self, declaration: CandidateDeclaration
    ) -> Mapping[tuple[str, str], Fraction]:
        """Return the wrapped provider's law, unchanged."""
        return self.provider(declaration)


def raw_factored_loss_applied(provider: RawJointProvider) -> RawJointProvider:
    """Return the raw ``provider`` declared to apply every station's factored loss.

    See :class:`LossAppliedRawProvider`; wrapping twice is wrapping once.
    """
    if isinstance(provider, LossAppliedRawProvider):
        return provider
    return LossAppliedRawProvider(provider)


#: An instance's declaration of HOW THE TRANSMITTED SYSTEM ENTERS ITS RECEIVER,
#: as this tier sees it: the receiver artefact where one was built, or
#: ``None`` on the route that declares a finite POVM, and the interface out.
#:
#: IT IS A PROVIDER AND NOT A CONSTANT, for the same reason the honest model is
#: one: the encoding of an instance with a compiled receiver depends on THAT
#: receiver's declared mode space and Fock basis order, which exist only once
#: the receiver has been constructed. An instance with a declared finite POVM
#: ignores the argument and returns the identity on ``A'``.
type ChannelInterfaceProvider = Callable[
    [ReceiverMeasurementArtifact | None], SourceChannelInterface
]


@dataclass(frozen=True)
class Preparation:
    """Everything a run produces BEFORE the honest model and the solve.

    The snap records, the compiled declaration's public part and acceptance
    alphabet, the receiver construction and artefact and the reduction record
    are all available in seconds and need no oracle, and would be reachable
    only by paying for a full solve. A caller building an honest-statistics table needs
    the acceptance alphabet BEFORE the run.

    IT SHARES ITS CODE PATH WITH :func:`run_slice` AND IS NOT A SECOND ONE.
    Both call :func:`_prepare`, which is the device prologue and the
    compilation and nothing else; ``run_slice`` is that, then the honest model,
    the acceptance set, the docking, the bundle and the solve. So the two
    cannot drift about what a route does, which is the whole reason the
    preparation is not a second function that "does the same thing".

    NO ORACLE ARGUMENT, because no solve happens. The oracle stays a REQUIRED
    argument of :func:`run_slice` (spec/architecture.md 3.3), and a preparation
    that took one would be asking for a capability probe it never runs.
    """

    specification: ProtocolSpecification
    compilation: CompilationResult
    declaration: CandidateDeclaration
    #: The declared acceptance alphabet, in its declared order. The datum a
    #: caller wanted the preparation for.
    acceptance_alphabet: tuple[str, ...]
    #: The device prologue's two artefacts, ``None`` on the route that supplies
    #: a finished specification. The key is present and null rather than
    #: absent, so that one shape serves every instance.
    receiver_artifact: ReceiverMeasurementArtifact | None = None
    reduction_artifact: ProofReductionArtifact | None = None
    #: THE INSTANCE'S SNAP RECORDS, as the rows adapter reported them: what it
    #: declared, how far it moved and under what ceiling. ``None`` where no
    #: adapter ran.
    rows_adaptation: Mapping[str, object] | None = None
    #: The honest per-round distribution over the raw outcome pairs ``X x V``,
    #: exactly, where the instance's honest model computes it. See
    #: :data:`RawJointProvider` for why it is not the acceptance distribution
    #: and why ``None`` is an honest answer.
    raw_joint_distribution: Mapping[tuple[str, str], Fraction] | None = None
    #: HOW ``A'`` ENTERS THE RECEIVER, where the instance declares it.
    #: ``None`` only where no provider was supplied; an instance that HAS no
    #: channel modes says so inside the interface rather than by omitting it.
    channel_interface: SourceChannelInterface | None = None
    #: The PLANNED stage list for this configuration: the same entries a run
    #: records, with status ``planned``.
    stages: tuple[StageRecord, ...] = ()
    #: The compiled declaration as an artefact of the provenance graph:
    #: its id is what the honest, acceptance and docking stages consume.
    declaration_artefact: Artefact | None = None
    device_artifacts: tuple[DeviceEmission, ...] = ()
    #: THE PROTOCOL DOCUMENT this run was lowered from (record schema 0.21.0),
    #: or ``None`` where a Python instance or a hand-composed caller ran it.
    #: Uninterpreted here: the document layer (``instances/declared``) writes
    #: it through :func:`~certiqs_key.runs.inputs.attach_protocol_document`
    #: and the record carries it as ``payload.protocol_document``.
    protocol_document: Mapping[str, Any] | None = None
    #: THE COMPILED REFERENCE COMPANION beside the declaration
    #: (``protocol-compiler/req:reference-companion-compiled``), or the record
    #: of why none was compiled; ``None`` on a route with no reduction stage.
    #: Evaluation-only, with no run of its own: no bundle is written from it,
    #: and the solve forms the first-order bound on it, at the search's points
    #: and its polish's (``frank-wolfe/req:bracket-on-reference``).
    reference_companion: CompiledReferenceCompanion | NoCompiledCompanion | None = None

    @property
    def refuses(self) -> bool:
        """Whether this outcome refused. Always false; cf. :class:`SliceRefusal`."""
        return False


#: What :func:`prepare` returns.
PreparationOutcome = Preparation | SliceRefusal



def run_slice(
    specification: ProtocolSpecification | None = None,
    *,
    honest_provider: HonestProvider,
    rounds: int,
    completeness_budget: Fraction,
    parameters: KeyLengthParameters,
    oracle: LinearOracle,
    directory: Path,
    created_by: str,
    device: DeviceRequests | MultiDeviceRequests | None = None,
    specification_provider: SpecificationProvider | None = None,
    raw_joint_provider: RawJointProvider | None = None,
    channel_interface_provider: ChannelInterfaceProvider | None = None,
    declared_tolerance: float,
    alpha: float | None = None,
    options: FrankWolfeOptions | None = None,
    request: SearchRequest | None = None,
    endpoint_rule: str = str(EndpointRuleName.EXACT),
    tail_evaluation: str = str(TailEvaluation.SWEEP),
    observer: StageObserver | None = None,
    run_id: str | None = None,
    honest_model_note: Mapping[str, Any] | None = None,
    constrained: tuple[str, ...] | None = None,
    eps_auth: float = 0.0,
    k_auth: int = 0,
    honest_supplied: bool | None = None,
    caller_constraint_entries: int = 0,
    statistics_check: str = "on",
    min_model_pass_probability: Fraction = Fraction(1, 2),
) -> SliceOutcome:
    """Run the path once and return what came out of it.

    Args:
        specification: the protocol, as ``protocol-compiler`` types it. Supply
            this OR the ``device`` / ``specification_provider`` pair, never both
            and never neither.
        honest_provider: the instance's honest channel model, already carrying
            its own model parameters. See :data:`HonestProvider`; an
            instance's honest model is, for example, the library's
            ``depolarized_bell_pair`` (``instances/common/honest/``).
        rounds: ``n``, total channel uses. The same ``n`` reaches the acceptance
            construction and the declaration, from this one argument, because
            ``statistics/req:matched-alphabet`` requires them to agree.
        completeness_budget: ``eps_comp``, in ``[0, 1)``. It buys COMPLETENESS
            and never soundness: ``statistics`` makes no security
            claim, and no key length below depends on this number.
        parameters: ``meat-core``'s Section 2.4 block. Not this slice's to
            choose and not defaulted here.
        oracle: the linear oracle the Frank-Wolfe driver minimizes over. See the
            module docstring for why there is no default.
        directory: where the bundle is written. It must not already hold one:
            :func:`~certiqs_key.domain.write_bundle` never overwrites.
        created_by: what produced the bundle. Never an absolute machine path,
            timestamp or run ID (spec/architecture.md 2.6).
        device: the physical receiver's three declarations and the caller's
            optional rows adapter. See :class:`DeviceRequests`.
        specification_provider: builds the specification from the two artifacts
            the device prologue produced. See :data:`SpecificationProvider`.
        declared_tolerance: ``tau``, the instance's ONE declared numerical
            tolerance (spec/architecture.md 2.8), read off
            :attr:`~certiqs_key.runs.config.RunConfig.declared_tolerance`.
            REQUIRED, keyword-only, no default: a run that does not declare it
            cannot be assembled here either. It is the CEILING ON THE PRE-SNAP
            DEFECT the instance's own snap may repair, and NO MODULE IS TOLD A
            TOLERANCE AT ALL -- not this number and not a zero standing in for
            it. This tier records the
            declared number and hands it to nobody but the instance that
            declared it.
        alpha: the Renyi order to solve at, defaulting to the declared one.
        observer: a caller's optional hook, called at the boundaries this
            function already has, and inside the ``solve`` stage at
            every Frank-Wolfe iterate with an ``iterate`` event carrying
            ``(iteration, gap)``. IT MUST NOT CHANGE THE OUTCOME: nothing reads its
            return value, and an exception raised inside it propagates as the
            caller's bug.
        run_id: the id every log line of this run carries. The caller's own --
            the configuration digest, where the caller has one -- because a run
            reaching this function without a ``RunConfig`` has no configuration
            to digest and this tier will not invent an id for it.
        honest_model_note: what the record says about WHICH honest model
            produced the distribution, carried VERBATIM.
            spec/architecture.md 3.2 requires that "a profile states which
            honest model its eps_comp was computed under", and an injected
            provider makes that unanswerable from the code alone.
        endpoint_rule: ``statistics``' ``endpoint_rule`` request field,
            forwarded unchanged. ``exact`` is that module's own default and the
            parity route; ``bernstein`` is the closed-form rule. A value the
            module does not admit is ITS refusal, and
            :class:`~certiqs_key.runs.config.RunConfig` refuses one earlier for
            the reason its own check states.
        tail_evaluation: the same, for the evaluation of the exact rule's
            tail: ``sweep`` (the running sum, the parity route) or
            ``enclosure`` (the local Stirling and geometric route that large
            ``n`` needs).
        options: the Frank-Wolfe budget, forwarded to
            :func:`~certiqs_key.solvers.frank_wolfe.solve_bundle` unchanged.
            ``None`` takes that function's declared default. It is wiring the caller
            owns, exactly like ``oracle``, and it is recorded beside the gap and the
            iteration count it explains.
        constrained: which acceptance outcomes the acceptance set constrains,
            defaulting to all of them. ``None`` is the declared default and is
            distinct from ``()``, which is an admissible selector in its own
            right.
        eps_auth, k_auth: A-AUTH's two run inputs
            (:attr:`~certiqs_key.runs.config.RunConfig.eps_auth` and
            ``k_auth``), forwarded to
            :func:`~certiqs_key.solvers.frank_wolfe.solve_bundle` unchanged.
            The defaults are meat-core's own (0); an instance's runner passes
            its configuration's. A budget with ``eps_pa + eps_ev + 2 eps_auth
            >= 1`` is a ``solve``-stage refusal with the engine's own reason,
            ``security_statement_vacuous``.

        honest_supplied, caller_constraint_entries, statistics_check,
            min_model_pass_probability: the check of the acceptance set against the
            feasible statistics (``meat-core/req:unreachable-acceptance-set``;
            :mod:`certiqs_key.runs.statistics_check`). The run is checked
            where its honest statistics were supplied as numbers (an
            honest table or envelope the caller gave, not the engine's model
            of the declared devices) or its declaration carries a constraint
            entry the caller declared, unless ``statistics_check`` is
            ``off``; ``honest_supplied`` ``None`` reads the honest-model
            note's ``overridden``. ``min_model_pass_probability`` is
            ``tau``. The instance's runner knows where both came from and
            says so. A checked run solves the penalty-only program once,
            before its solve, and is refused as a whole, evaluated at no
            order, where the cap on the pass probability of devices as
            declared is at most ``tau`` (item (iv)).

    Returns:
        A :class:`SliceResult`, or a :class:`SliceRefusal` naming the stage that
        declined and the refusing module's own reason.

    Raises:
        SliceAssemblyError: if neither or both of the two specification routes
            are supplied; if ``declared_tolerance`` is not a ``float`` in
            ``[0, 1)``; or if the acceptance construction and the emitted
            declaration disagree about the acceptance alphabet. No module may
            decide any of the three, so none is a refusal by one. The
            ``reductions`` declares no tolerance, so there is no ``eps_op``
            cross-check.
        Exception: whatever ``honest_provider`` raises when its model does not
            apply to the emitted declaration. Nothing is caught here: a provider
            that cannot model a declaration has produced no distribution, and
            substituting one would be this tier inventing a number.
    """
    # THE RUN'S STATISTICS CHECK (meat-core/req:unreachable-acceptance-set):
    # the search's where one holds it, the run's own otherwise. Its scope is
    # decided first, so that every outcome below records whether the run is
    # checked and why not.
    check = run_check()
    check.begin(
        honest_supplied=(
            honest_supplied_from_note(honest_model_note)
            if honest_supplied is None
            else honest_supplied
        ),
        caller_constraint_entries=caller_constraint_entries,
        option=statistics_check,
        tau=min_model_pass_probability,
        rounds=rounds,
        alpha=parameters.alpha if alpha is None else alpha,
    )
    outcome = _run_slice(
        specification=specification,
        honest_provider=honest_provider,
        rounds=rounds,
        completeness_budget=completeness_budget,
        parameters=parameters,
        oracle=oracle,
        directory=directory,
        created_by=created_by,
        device=device,
        specification_provider=specification_provider,
        raw_joint_provider=raw_joint_provider,
        channel_interface_provider=channel_interface_provider,
        declared_tolerance=declared_tolerance,
        alpha=alpha,
        options=options,
        request=request,
        endpoint_rule=endpoint_rule,
        tail_evaluation=tail_evaluation,
        observer=observer,
        run_id=run_id,
        honest_model_note=honest_model_note,
        constrained=constrained,
        eps_auth=eps_auth,
        k_auth=k_auth,
        check=check,
    )
    return replace(outcome, statistics_consistency=check.record())


def _run_slice(
    specification: ProtocolSpecification | None = None,
    *,
    honest_provider: HonestProvider,
    rounds: int,
    completeness_budget: Fraction,
    parameters: KeyLengthParameters,
    oracle: LinearOracle,
    directory: Path,
    created_by: str,
    device: DeviceRequests | MultiDeviceRequests | None = None,
    specification_provider: SpecificationProvider | None = None,
    raw_joint_provider: RawJointProvider | None = None,
    channel_interface_provider: ChannelInterfaceProvider | None = None,
    declared_tolerance: float,
    alpha: float | None = None,
    options: FrankWolfeOptions | None = None,
    request: SearchRequest | None = None,
    endpoint_rule: str = str(EndpointRuleName.EXACT),
    tail_evaluation: str = str(TailEvaluation.SWEEP),
    observer: StageObserver | None = None,
    run_id: str | None = None,
    honest_model_note: Mapping[str, Any] | None = None,
    constrained: tuple[str, ...] | None = None,
    eps_auth: float = 0.0,
    k_auth: int = 0,
    check: RunCheck,
) -> SliceOutcome:
    """Run the body of :func:`run_slice`, whose docstring reads its arguments.

    ``check`` is the run's statistics check, its scope already decided.
    """
    # THE DECLARED tau IS DECIDED HERE TOO, AND NOT ONLY ON RunConfig. A caller
    # may reach this function without ever building one -- every instance's own
    # ``run_slice`` does -- and spec/architecture.md 2.8 puts the rule
    # on the RUN and not on one of its representations: "tau itself has no
    # default and no fallback: a run whose configuration does not declare it is
    # refused". The domain is the repo-wide ``[0, 1)`` of that section, whose
    # upper limit is derived there; the type is binary64 because "a declared
    # value IS its binary64 datum". Nothing is coerced and nothing substituted.
    _check_declared_tolerance(declared_tolerance)

    # THE VIEW IS RECORDED AS THE PATH IS TAKEN, and the one thing the stages
    # cannot tell it is the COMPOSITION: whether a device prologue is on this
    # route at all. That is what this tier owns.
    flow = FlowRecorder(
        device_prologue=device is not None,
        stations=_station_factors(device),
        observer=observer,
        run_id=run_id,
    )

    # THE SHARED HALF, AND IT IS THE SAME CALL :func:`prepare` MAKES.
    prepared = _prepare(
        specification,
        device=device,
        specification_provider=specification_provider,
        raw_joint_provider=raw_joint_provider,
        channel_interface_provider=channel_interface_provider,
        flow=flow,
    )
    if isinstance(prepared, SliceRefusal):
        return prepared
    specification = prepared.specification
    compilation = prepared.compilation
    declaration = prepared.declaration
    receiver_artifact = prepared.receiver_artifact
    reduction_artifact = prepared.reduction_artifact
    rows_adaptation = prepared.rows_adaptation

    declaration_artefact = prepared.declaration_artefact
    assert declaration_artefact is not None  # _prepare always builds one
    flow.start(
        SliceStage.HONEST_MODEL,
        artefacts=[declaration_artefact.identifier],
        config_keys=["model"],
    )
    # receiver/detector-imperfections/req:loss-before-evaluation, decided
    # before the provider is called: see LossAppliedProvider.
    normalized = _normalized_stations(
        prepared.device_artifacts, prepared.receiver_artifact
    )
    if normalized and not isinstance(honest_provider, LossAppliedProvider):
        reason = str(RunRefusalReason.FACTORED_LOSS_NOT_APPLIED)
        detail = _loss_not_applied_detail(
            normalized, "honest provider", "factored_loss_applied"
        )
        flow.refused(SliceStage.HONEST_MODEL, reason, detail)
        return SliceRefusal(
            stage=SliceStage.HONEST_MODEL,
            reason=reason,
            detail=detail,
            compilation=compilation,
            receiver_artifact=receiver_artifact,
            stages=flow.finish(),
            device_artifacts=prepared.device_artifacts,
        )
    honest = honest_provider(declaration)
    honest_artefact = Artefact(
        kind=ArtefactKind.HONEST_DISTRIBUTION,
        # THE CALLER'S OWN DISTRIBUTION IS AN ARTEFACT TOO, and its
        # digest is recorded where the honest stage CONSUMED it, so that a
        # caller's own upstream stages -- a channel simulator, a table -- can
        # join to this run by digest without this tier knowing anything about
        # them.
        digest=artefact_digest(_honest_payload(honest)),
        record_key=(
            "payload.stages.acceptance_construction.honest_envelope"
            if isinstance(honest, HonestEnvelope)
            else "payload.stages.acceptance_construction.honest_distribution"
        ),
    )
    flow.executed(
        SliceStage.HONEST_MODEL,
        emits=[honest_artefact],
        outcomes=len(honest.lower if isinstance(honest, HonestEnvelope) else honest),
        overridden=honest_model_note is not None
        and bool(honest_model_note.get("overridden")),
    )
    alphabet = declaration.acceptance_alphabet
    flow.start(
        SliceStage.ACCEPTANCE_CONSTRUCTION,
        artefacts=[honest_artefact.identifier, declaration_artefact.identifier],
        config_keys=[
            "rounds",
            "completeness_budget",
            "constrained",
            "endpoint_rule",
            "tail_evaluation",
        ],
    )
    construction = construct(
        AcceptanceRequest(
            alphabet=alphabet,
            honest=honest,
            rounds=rounds,
            budget=completeness_budget,
            constrained=constrained,
            # THE TWO REQUEST FIELDS, FORWARDED AND NOT DECIDED. They are
            # ``statistics``' own (its ``endpoint_rule`` and ``tail_evaluation``
            # input rows), and this tier neither
            # reads them nor defaults them: ``RunConfig`` carries the caller's
            # choice with that module's own default, and the module records
            # both in the ``honest_model`` record it emits, where completeness
            # is read relative to them.
            endpoint_rule=endpoint_rule,
            tail_evaluation=tail_evaluation,
        )
    )
    if isinstance(construction, InfeasibleInput):
        report = construction.infeasibility_report
        flow.refused(
            SliceStage.ACCEPTANCE_CONSTRUCTION, str(report.reason), report.detail
        )
        return SliceRefusal(
            stage=SliceStage.ACCEPTANCE_CONSTRUCTION,
            reason=str(report.reason),
            detail=report.detail,
            compilation=compilation,
            infeasibility=report,
            stages=flow.finish(),
            device_artifacts=prepared.device_artifacts,
        )
    _require_matched_alphabet(construction.acceptance_set.outcomes, alphabet)

    acceptance_record = acceptance_set_record(construction.acceptance_set)
    acceptance_artefact = Artefact(
        kind=ArtefactKind.ACCEPTANCE_SET,
        digest=artefact_digest(
            {
                "geometry": acceptance_record.geometry,
                "outcomes": list(construction.acceptance_set.outcomes),
                "support": list(construction.acceptance_support),
            }
        ),
        record_key="payload.stages.acceptance_construction",
    )
    flow.executed(
        SliceStage.ACCEPTANCE_CONSTRUCTION,
        emits=[acceptance_artefact],
        geometry=type(construction.acceptance_set).__name__,
        completeness_exact=construction.completeness_exact,
    )

    flow.start(
        SliceStage.DOCKING,
        artefacts=[declaration_artefact.identifier, acceptance_artefact.identifier],
        config_keys=["rounds", "parameters"],
    )
    docked: ProtocolDeclaration | GeneralDeclaration
    if declaration.is_general_format:
        docked = dock_general_candidate(
            declaration, acceptance_set=acceptance_record, rounds=rounds,
            parameters=parameters,
            reduction_chain_record=compilation.reduction_chain_record,
        )
    else:
        docked = dock_declaration(
            declaration, acceptance_set=acceptance_record, rounds=rounds,
            parameters=parameters,
        )
    # THE DOCKED DECLARATION IS SERIALISED INSIDE THIS STAGE'S WINDOW. The
    # docking stage emits an artefact, so the recorded graph has an edge from
    # the honest model and the acceptance set through to the solve and the
    # parameter trace is unbroken. An artefact must be serialisable for its
    # digest to exist, so serialising it IS part of emitting it, and
    # ``bundle_write`` measures the WRITE, which is what it is named for:
    # ``docking``'s ``wall_time_s`` includes building the bundle documents and
    # ``bundle_write``'s does not. Both are measured at this tier's own boundaries and
    # neither is invented.
    bundle_writer = (
        build_general_bundle if isinstance(docked, GeneralDeclaration) else build_bundle
    )
    bundle, labels = bundle_writer(
        docked,  # type: ignore[arg-type]
        alice_announcements=declaration.alice_announcement_alphabet,
        bob_announcements=declaration.bob_announcement_alphabet,
        reduction_chain=_chain_record_through_weighting(
            compilation.reduction_chain_record, compilation.choice_weightings
        ),
        created_by=created_by,
    )
    docking_artefact = Artefact(
        kind=ArtefactKind.DOCKED_DECLARATION,
        # THE SAME DIGEST AS THE BUNDLE ARTEFACT'S, of the same bundle; the
        # KINDS keep the two ids apart, so a consumer joining ``docking`` to
        # ``bundle_write`` reads an edge and not one node twice.
        #
        # WHAT IT COVERS: the bundle's manifest AND every array's numbers.
        # An operator bundle is a JSON manifest PLUS HDF5 arrays
        # (spec/architecture.md 4.1), and the manifest carries
        # ``ArrayDescriptor``s and not one array entry, so a digest of the
        # manifest alone would give two declarations differing only in the
        # ENTRIES of their operators the same id.
        # :func:`~certiqs_key.runs.flow.bundle_digest` adds each array's layout, shape,
        # dtype and the sha256 of its bytes, so this id is the docked declaration as
        # written down, envelope and operators.
        digest=bundle_digest(bundle),
        # IT REACHES THE RECORD THROUGH THE BUNDLE. There is no
        # ``stages.docking`` key carrying the declaration -- what a reader gets
        # is the bundle directory -- and naming a key that does not exist would
        # be worse than naming none.
        record_key=None,
    )
    flow.executed(
        SliceStage.DOCKING,
        emits=[docking_artefact],
        rounds=rounds,
        constraint_entries=len(docked.constraint_list),
    )
    flow.start(
        SliceStage.BUNDLE_WRITE,
        artefacts=[declaration_artefact.identifier, docking_artefact.identifier],
    )
    write_bundle(directory, bundle)
    bundle_artefact = Artefact(
        kind=ArtefactKind.BUNDLE,
        # Manifest and arrays; see the docking artefact above.
        digest=bundle_digest(bundle),
        # THE BUNDLE IS ON DISK AND THE RECORD NAMES ITS DIRECTORY. The record
        # does not carry the manifest, so the key below is where a reader finds
        # the bundle rather than where the bytes are.
        record_key="payload.stages.bundle",
    )
    flow.executed(
        SliceStage.BUNDLE_WRITE,
        emits=[bundle_artefact],
        directory=directory.name,
        schema_version=bundle.manifest.schema_version,
    )
    # READ BACK, not reused. What is solved is what is on the disk, so a datum
    # this slice failed to serialize shows up as a wrong answer rather than as a
    # bundle nobody consumed.
    reread_bundle = read_bundle(directory)
    # NOTHING BELOW IS TOLD A TOLERANCE, AND THERE IS NO ZERO TO PASS EITHER.
    # `declaration_from_bundle` and `solve_bundle` take no tolerance argument
    # (the module docstring's "THIS TIER PASSES NO TOLERANCE"). The run's own tau is the
    # ceiling on the INSTANCE's snap; it was spent before this line by whoever declared
    # data, and widening what the engine admits with it would be the one thing
    # spec/architecture.md 2.8 forbids outright: "a tolerance never widens what
    # a security predicate admits".
    flow.start(SliceStage.BUNDLE_READ, artefacts=[bundle_artefact.identifier])
    # THE ROUND TRIP IS CHECKED, because the provenance token below vouches for
    # what is solved. The bundle read back
    # must be the bundle written, manifest and every array's numbers
    # (:func:`~certiqs_key.runs.flow.bundle_digest`); where it is not, the read
    # stage emits the bundle it actually read, under its own digest, and records
    # ``round_trip_identical`` False.
    round_trip_identical = bundle_digest(reread_bundle) == bundle_artefact.digest
    read_artefact = (
        bundle_artefact
        if round_trip_identical
        else Artefact(
            kind=ArtefactKind.BUNDLE,
            digest=bundle_digest(reread_bundle),
            record_key="payload.stages.bundle",
        )
    )
    flow.executed(
        SliceStage.BUNDLE_READ,
        emits=[read_artefact],
        schema_version=reread_bundle.manifest.schema_version,
        round_trip_identical=round_trip_identical,
    )
    reread = declaration_from_bundle(reread_bundle)
    # THE PROVENANCE TOKEN TRAVELS IN MEMORY, BESIDE THE BUNDLE AND NOT IN IT
    # (meat-core/req:compiled-declaration-only). The bundle written and read back above
    # is the docked form of the declaration this slice's compilation emitted, and
    # nothing on the disk says so: the wire format is unchanged. So the token is minted
    # from that emitted declaration here and handed to the solve with the reread
    # bundle -- ONLY WHERE THE ROUND TRIP WAS IDENTICAL. A bundle that changed
    # on the disk is not known to be the compiler's emission, so it gets no
    # token and the engine WITHHOLDS the key length with its own reason
    # (``declaration_not_compiled``), as on any other declaration from
    # elsewhere: a withholding, not a refusal, with every number reported and
    # the read stage's ``round_trip_identical`` saying why. The run tier
    # invents no reason code for it.
    compiled = compiler_emission(declaration) if round_trip_identical else None
    flow.start(
        SliceStage.SOLVE,
        artefacts=[read_artefact.identifier],
        config_keys=["alpha", "parameters", "solver"],
    )
    # THE ORDER THIS EVALUATION IS AT, as the solve reads it.
    order = parameters.alpha if alpha is None else alpha

    def refused_at_solve(reason: str, detail: str) -> SliceRefusal:
        """Record the solve stage's refusal under the engine's own code.

        An order the run evaluates: the check notes its diagnostic
        (req:unreachable-acceptance-set (v)).
        """
        flow.refused(SliceStage.SOLVE, reason, detail)
        check.note_order(order)
        return SliceRefusal(
            stage=SliceStage.SOLVE,
            reason=reason,
            detail=detail,
            compilation=compilation,
            receiver_artifact=receiver_artifact,
            stages=flow.finish(),
            device_artifacts=prepared.device_artifacts,
        )

    # THE CHECK'S SOLVE, ONCE PER RUN AND BEFORE ANY ORDER IS EVALUATED
    # (meat-core/req:unreachable-acceptance-set (i), (ii); row 10 of the
    # fail_closed table): on the declaration this run searches, the one read
    # back, and with its acceptance set, at alpha_0 with this evaluation's
    # search request. A search forms it at its first evaluation and every
    # later one reads it, a bound or the reason none was formed alike
    # (runs/statistics_check.py).
    # ITS OWN EXCEPTION BOUNDARY, apart from the run's solve below, so that
    # nothing the check raises is filed as the run's own refusal. It refuses
    # nothing itself: an unsolved or failed oracle step and a numerical
    # failure of its search come back as the reason no bound was formed, and
    # a negative estimate is a diagnostic beside a bound formed all the same
    # (solvers/frank_wolfe/minimal_divergence.py). Its wall budget is a share
    # of this evaluation's (meat-core STATISTICS_CHECK_BUDGET_SHARE). What it raises
    # concerns the run: a vacuous security statement, which the run's own
    # preparation raises the same and which is refused here as the run's,
    # under the engine's code; an inadmissible declaration or an
    # infeasibility verdict, which propagate as they do from the run's solve.
    if check.scope is not None and check.scope.checked:
        try:
            check.ensure_bound(
                (declaration_artefact.digest, acceptance_artefact.digest),
                lambda alpha_0: bound_minimal_divergence_of_bundle(
                    reread_bundle,
                    oracle,
                    alpha_0=alpha_0,
                    options=options,
                    request=request,
                    eps_auth=eps_auth,
                ),
            )
        except SecurityStatementVacuousError as vacuous:
            return refused_at_solve(str(vacuous.reason), str(vacuous))
        # THE CAP AND THE REFUSAL (item (iv)), decided with the bound and once
        # per run: where the cap on the pass probability of devices as
        # declared is at most tau, the run is refused as a whole here, before
        # this evaluation's own solve, and evaluated at no order.
        if check.refused:
            assert check.cap is not None and check.bound is not None
            detail = refusal_detail(check.cap, check.bound)
            flow.refused(
                SliceStage.SOLVE, UNREACHABLE_REASON, detail, refused_by="meat-core"
            )
            return SliceRefusal(
                stage=SliceStage.SOLVE,
                reason=UNREACHABLE_REASON,
                detail=detail,
                compilation=compilation,
                receiver_artifact=receiver_artifact,
                stages=flow.finish(),
                device_artifacts=prepared.device_artifacts,
            )
    try:
        key_rate = solve_bundle(
            reread_bundle,
            oracle,
            alpha=alpha,
            options=options,
            request=request,
            # THE PER-ITERATE HOOK, forwarded only where a caller listens: it
            # becomes the observer's `iterate` events and changes nothing.
            observer=flow.iterate if observer is not None else None,
            compiled=compiled,
            eps_auth=eps_auth,
            k_auth=k_auth,
            # THE REFERENCE COMPANION, evaluation-only and in memory, never in
            # the bundle (protocol-compiler/req:reference-companion-compiled
            # (iv)): the solve admits it beside the declaration it read back,
            # sets aside the polish's share of the budget, and after the search
            # forms the first-order bound on it at the search's points and the
            # polish's (frank-wolfe/req:bracket-on-reference).
            companion=(
                prepared.reference_companion
                if isinstance(prepared.reference_companion, CompiledReferenceCompanion)
                else None
            ),
            certification_withheld=certification_withheld(prepared),
            # foundations/req:snap-reference (iv): a strict_snaps run forms no
            # certified number on the snapped declaration in place of the
            # companion's (frank-wolfe/req:certified-evaluation (i)).
            strict_snaps=_declares_strict(device),
        )
    except (SecurityStatementVacuousError, CertificationRefusedError) as vacuous:
        # THE CORNER GATE (meat-core/req:security-statement-not-vacuous), with
        # A-AUTH's eps_auth in it since the run tier threads that input (record
        # schema 0.20.0): a budget eps_pa + eps_ev + 2 eps_auth >= 1 leaves no
        # security statement to make. The engine refuses before any number is
        # computed; this tier records the refusal under the engine's own code,
        # as it records a negative objective, rather than passing a traceback
        # to a sweep.
        return refused_at_solve(str(vacuous.reason), str(vacuous))
    except NegativeObjectiveError as negative:
        # THE HARD ERROR STAYS IN THE SOLVER AND THIS TIER TURNS IT INTO DATA.
        # The solver is right to raise:
        # the `h_low` output row forbids clamping, "zero cannot stand in for
        # it", and a bare return of 0.0 would report a plausible number in
        # place of a detected inconsistency. But a CALLER SWEEPING A PARAMETER
        # AXIS INTO THE NO-KEY REGION is not diagnosing an inconsistency, it is
        # walking off the edge of the region where a key exists, and a
        # traceback with no reason code to file it under would turn a sweep of
        # thirty points into twenty results and ten crashes.
        #
        # The value is never clamped and never reaches a key length; this tier
        # RECORDS the refusal instead of propagating the exception, exactly as
        # it already does for the compiler's, reductions' and statistics'
        # refusals. THE REASON CODE IS THE SOLVER'S OWN
        # (`RefusalReason.NEGATIVE_OBJECTIVE`, spelled `negative_objective`)
        # and is not invented here, which is what this tier's SliceRefusal
        # requires: "never a code this module invented". It is the run's own
        # solve's: the check's solve has its own boundary above.
        return refused_at_solve(str(negative.reason), str(negative))
    except WarmStartRefused as refused:
        # A WARM START WHOSE SEED DOES NOT LIVE IN THIS POINT'S FEASIBLE SET,
        # refused by the solver with its own code (warm_start_*), recorded as
        # the refusal of this stage for the reason the negative objective is:
        # a chained loss sweep walking into a mismatched seed is a result to
        # file, not a traceback. Nothing is projected or clamped.
        return refused_at_solve(refused.reason, str(refused))
    plausibility = plausibility_check(reread, key_rate)
    result = SliceResult(
        compilation=compilation,
        declaration=declaration,
        honest_distribution=honest,
        acceptance=construction,
        docked=docked,
        bundle_directory=directory,
        bundle=reread_bundle,
        reread=reread,
        labels=labels,
        key_rate=key_rate,
        receiver_artifact=receiver_artifact,
        reduction_artifact=reduction_artifact,
        rows_adaptation=rows_adaptation,
        declared_tolerance=declared_tolerance,
        stages=flow.finish(),
        specification=specification,
        channel_interface=prepared.channel_interface,
        raw_joint_distribution=prepared.raw_joint_distribution,
        honest_model_note=honest_model_note,
        solver_options=options,
        solver_request=request,
        device_artifacts=prepared.device_artifacts,
        reference_companion=prepared.reference_companion,
    )
    # THE STRICT OPTION AFTER THE SEARCH (foundations/req:snap-reference (iv)):
    # "the run, after its search and before any key length is reported, where
    # a moved block is not evaluated off its snap". Whether a block rests is
    # decided only now (runs/direct_route.py), so this is the last place the
    # run can refuse instead of reporting a key length that rests on A-SNAP;
    # the snap and the emission refused earlier wherever the resting was
    # already certain. Recorded under the run tier's own code, like the
    # plausibility check, at the solve stage.
    if _declares_strict(device):
        decision = direct_route(result)
        if decision.rests_on_a_snap:
            # No key length at this order, for another requirement's reason
            # (foundations/req:snap-reference (iv)); an order the run
            # evaluated, whose diagnostic the check notes.
            check.note_order(order)
            reason = str(RunRefusalReason.STRICT_SNAPS)
            detail = _strict_detail(decision)
            flow.refused(SliceStage.SOLVE, reason, detail, refused_by="runs")
            return SliceRefusal(
                stage=SliceStage.SOLVE,
                reason=reason,
                detail=detail,
                compilation=compilation,
                receiver_artifact=receiver_artifact,
                stages=flow.finish(),
                device_artifacts=prepared.device_artifacts,
            )
    # THE ORDER'S DIAGNOSTIC (meat-core/req:unreachable-acceptance-set (v)):
    # n f at the order this evaluation formed its key length at, recorded and
    # read by nothing. The refusal of item (iv) was decided before the solve.
    check.note_order(key_rate.alpha)
    # THE PLAUSIBILITY CHECK, the run tier's own and last: the bound the key length is
    # computed from, held against log2(d_Z + 1) times the largest key-live
    # probability over the acceptance set (meat-core/prop:value-range (ii)).
    # A bound above it says the declared model contradicts every accepted
    # statistic -- an overstated key, such as h_low = 3.06 bits per round on a
    # one-bit key. The run tier refuses it
    # under its own code, at this stage, with both numbers; the module that
    # owns the stage computed the number and is not the one refusing, which
    # the stage detail says (``refused_by``). See :mod:`certiqs_key.runs.
    # plausibility` for the derivation, for why the bound and not the
    # estimate is compared, and for the two comparisons: exact on a certified
    # number, relative to the ceiling otherwise. A searched run that meets this
    # refusal at any alpha is refused as a whole by the search
    # (runs/alpha_search.py).
    if plausibility.exceeded:
        reason = str(RunRefusalReason.ENTROPY_BOUND_ABOVE_KEY_CEILING)
        flow.refused(
            SliceStage.SOLVE,
            reason,
            plausibility.detail(),
            refused_by="runs",
            plausibility=plausibility.as_record(),
        )
        return SliceRefusal(
            stage=SliceStage.SOLVE,
            reason=reason,
            detail=plausibility.detail(),
            compilation=compilation,
            receiver_artifact=receiver_artifact,
            stages=flow.finish(),
            device_artifacts=prepared.device_artifacts,
            plausibility=plausibility.as_record(),
        )
    flow.executed(
        SliceStage.SOLVE,
        emits=[
            Artefact(
                kind=ArtefactKind.KEY_RATE_RESULT,
                digest=artefact_digest(key_rate.as_payload()),
                record_key="payload.stages.key_rate",
            )
        ],
        children=_solve_children(key_rate),
        reported_tier=str(key_rate.reported_tier),
        key_length=key_rate.key_length,
        key_length_reason=key_rate.key_length_reason,
        plausibility=plausibility.as_record(),
    )
    return replace(result, stages=flow.finish())


def _declares_strict(device: DeviceRequests | MultiDeviceRequests | None) -> bool:
    """Whether the run declares the strict option, as its reduction requests do.

    The run option ``strict_snaps`` reaches every station's reduction
    request (``reductions``' core input of that name); a run with no device
    snaps no measurement and has nothing to refuse.
    """
    if device is None:
        return False
    devices = device.devices if isinstance(device, MultiDeviceRequests) else (device,)
    return any(item.reduction_request.strict_snaps for item in devices)


def _strict_detail(decision: DirectRoute) -> str:
    """Name every block the strict option refuses, with its group, cause and fix."""
    names = "; ".join(
        (
            f"{block.origin} {block.block}"
            + ("" if station.factor is None else f" of factor {station.factor!r}")
            + f": group {block.group}, cause {block.cause}, fix: {block.fix}"
        )
        for station in decision.stations
        for block in station.resting
    )
    return (
        "the strict option refuses: after the search these moved blocks are not "
        f"evaluated off their snap (direct route {decision.status}), so a key "
        f"length would rest on A-SNAP (foundations/ass:snapped-measurement): "
        f"{names} (foundations/req:snap-reference (iv))"
    )


def _artifacts_by_factor(
    specification: ProtocolSpecification,
    device: DeviceRequests | MultiDeviceRequests | None,
    emissions: Sequence[DeviceEmission],
    single: ProofReductionArtifact | None,
) -> dict[str, ProofReductionArtifact]:
    """Return the reductions artefacts this run emitted, keyed by measured factor.

    A station's by the factor its :class:`Station` names; the single device's
    as the specification's one (first) measured factor. Empty where the run
    ran no prologue.
    """
    if isinstance(device, MultiDeviceRequests):
        return {
            station.station.factor: emission.reduction
            for station, emission in zip(device.devices, emissions, strict=True)
            if station.station is not None
        }
    if device is None or single is None:
        return {}
    first = specification.receiver
    return {
        first.factor_label
        if first.factor_label is not None
        else default_factor_label(0): single
    }


def _check_public_choice_told(
    specification: ProtocolSpecification, devices: Sequence[DeviceRequests]
) -> None:
    """Refuse a device that told its reduction "no public choice" falsely.

    A-TSM's row at a station without a private setting is omitted only where
    the reduction was told that no public choice is applied at its factor
    (:attr:`DeviceRequests.public_choice_at_station` ``False``). An instance says so
    before its specification exists, so the specification it then builds is held to it
    here: a weighting or a choice-weighted physical family at a factor whose device said
    ``False`` would leave A-TSM unemitted where it is engaged, the unsafe direction.
    A station is every measured factor whose label its :class:`Station`
    names, matched by list so that a repeated label is checked at each of its
    factors; a station naming no factor
    is held to every factor, and a single device to the specification's
    first (one) measured factor.
    """
    labelled = [
        (
            part.factor_label
            if part.factor_label is not None
            else default_factor_label(position),
            part,
        )
        for position, part in enumerate(specification.receiver_parts)
    ]
    for index, device in enumerate(devices):
        if device.public_choice_at_station is not False:
            continue
        if device.station is None:
            found = list(specification.receiver_parts[:1])
        else:
            found = [
                part for label, part in labelled if label == device.station.factor
            ] or list(specification.receiver_parts)
        if any(
            part.choice_weighting is not None
            or isinstance(part.physical_povm, PublicChoices)
            for part in found
        ):
            raise SliceAssemblyError(
                f"station {index} told its reduction that no public choice is "
                "applied at its measured factor, but the specification applies "
                "one there; A-TSM would be omitted where it is engaged"
            )


def _chain_record_through_weighting(
    record: Mapping[str, object] | None,
    weightings: Sequence[FactorWeighting],
) -> Mapping[str, object] | None:
    """Return the compiler's chain record read through its route-C weighting.

    ``rem:relabel`` records a declared ``choice_weighting`` BESIDE the
    chain, and the compiler keeps its one-factor ``reduction_chain_record``
    byte-for-byte what it was; only its multi-factor record carries the
    expansion (``_factor_chain_record``). The bundle's Bob alphabet is the
    weighted support in both cases, so a one-factor correspondence is read
    through the weighting here, before the wire checks that every emitted
    label lands in that alphabet: each pair ``(physical, v)`` becomes one pair
    ``(setting_joint_label(physical, f), (v, f))`` per support member, the
    multi-factor record's own spelling. Without this, every single-station
    route-C declaration (a lit probe station on route C) fails at the
    bundle write. No number is read from the
    correspondence: meat-core counts the transported constraints only.
    """
    if (
        record is None
        or not weightings
        or "receiver_factor_segments" in record
    ):
        return record
    # A one-factor record carries one factor, so at most one weighting.
    if len(weightings) != 1:
        raise SliceAssemblyError(
            "a one-factor chain record beside weightings at "
            f"{len(weightings)} factors; the compiler records a multi-factor "
            "chain as receiver_factor_segments"
        )
    weighting = weightings[0].family
    correspondence = record.get("outcome_correspondence")
    if not isinstance(correspondence, list):
        raise SliceAssemblyError(
            "the compiler's one-factor chain record carries its outcome "
            f"correspondence as a list of pairs; got {correspondence!r}"
        )
    expanded: list[list[str]] = []
    for pair in correspondence:
        physical, emitted = pair
        for member in weighting.members_of_outcome(emitted):
            choice = weighting.pairs[member][1]
            expanded.append(
                [str(setting_joint_label(physical, choice)), str(member)]
            )
    return {**record, "outcome_correspondence": expanded}


def _solve_children(
    key_rate: GeneralKeyRateResult,
) -> tuple[StageChild, ...]:
    """Return the steps inside the solve, READ OFF what the engine returned.

    They are serialized BY THE RUN TIER from the result record it gets back,
    with NO MODULE CHANGE: a reading of fields the result already carries,
    grouped under four names. Nothing is computed and nothing is asked of ``meat-core``.

    WALL TIMES ONLY WHERE THIS TIER MEASURED ONE, which is nowhere inside the
    solve: ``solve_bundle`` is one call and this tier does not see the seam
    between bundle validation and the loop. A time it did not measure would be
    invented, so every child below carries ``None``.

    THE ALPHA CHILD, AND WHY THERE IS ONE. A candidate per alpha is wanted
    where an OUTER SEARCH runs. :func:`run_slice` runs one alpha
    (spec/architecture.md 6's rule), so
    the child written here names exactly the one alpha this run was driven at,
    with ``searched: false``. The outer search is the run tier's
    (:mod:`certiqs_key.runs.alpha_search`): it runs this function once per
    candidate, and on the chosen run's outcome it fills this same child with
    ``searched: true``, the settings and every evaluation
    (:func:`~certiqs_key.runs.alpha_search.attach_alpha_search`). A grid over
    alpha is a grid of RUNS, and each of them carries its own child here --
    which is what makes "key length against alpha" plottable from the records
    alone.
    """
    certificate_record: dict[str, Any] = dict(key_rate.certificate)
    return (
        StageChild(
            name="bundle_validation",
            status="passed",
            detail={
                "report": dict(key_rate.map_validation_report),
                "note": (
                    "a bundle that does not validate produces no result at all "
                    "(spec/architecture.md 3.6), so a result implies this passed"
                ),
            },
        ),
        StageChild(
            name="map_generation_and_cross_validation",
            status="passed",
            detail={"report": dict(key_rate.map_validation_report)},
        ),
        StageChild(
            name="frank_wolfe",
            status=str(certificate_record["solver_status"]),
            detail={
                "iterations": certificate_record["iterations"],
                "final_gap": certificate_record["frank_wolfe_gap"],
                "accumulation_rule": certificate_record["accumulation_rule"],
            },
        ),
        StageChild(
            name="alpha",
            status="chosen",
            detail={
                "alpha": key_rate.alpha,
                "h_low": key_rate.h_low,
                "h_lb": key_rate.h_lb,
                "key_length": key_rate.key_length,
                "searched": False,
            },
        ),
        StageChild(
            name="key_length_assembly",
            status=(
                "emitted" if key_rate.key_length is not None else "no_key_length"
            ),
            detail={
                "deductions": dict(key_rate.deductions),
                "reason": key_rate.key_length_reason,
                "reported_tier": str(key_rate.reported_tier),
                "security_gates": dict(certificate_record["security_gates"]),
            },
        ),
    )



def _prepare(
    specification: ProtocolSpecification | None,
    *,
    device: DeviceRequests | MultiDeviceRequests | None,
    specification_provider: SpecificationProvider | None,
    raw_joint_provider: RawJointProvider | None,
    channel_interface_provider: ChannelInterfaceProvider | None,
    flow: FlowRecorder,
) -> Preparation | SliceRefusal:
    """Run the device prologue and the compilation, or refuse.

    THE SHARED HALF OF THE PATH, and the reason :func:`prepare` and
    :func:`run_slice` cannot disagree about a route: there is one of these and
    both call it. What is NOT here is everything that needs the honest model or
    the oracle -- the acceptance set, the docking, the bundle and the solve --
    which is the line between :func:`prepare` and :func:`run_slice`.
    """
    if (specification is None) == (device is None):
        raise SliceAssemblyError(
            "a run supplies EITHER a finished specification OR a device and a "
            "specification provider; this one supplied "
            f"{'both' if specification is not None else 'neither'}. Which was "
            "meant is not this tier's to decide"
        )

    receiver_artifact: ReceiverMeasurementArtifact | None = None
    reduction_artifact: ProofReductionArtifact | None = None
    rows_adaptation: Mapping[str, object] | None = None
    #: What the compilation consumed, on the route where a prologue ran: the
    #: receiver artefact and the reduction chain the specification was built
    #: from. Empty on the route that supplies a finished specification, where
    #: the compiler's input came from the caller and not from a stage.
    upstream: tuple[str, ...] = ()
    device_artifacts: tuple[DeviceEmission, ...] = ()

    if isinstance(device, MultiDeviceRequests):
        if specification_provider is not None:
            raise SliceAssemblyError("multi-device requests carry their own provider")
        emissions: list[DeviceEmission] = []
        for index, station in enumerate(device.devices):
            emission = _run_device_prologue(station, flow, index=index)
            if isinstance(emission, SliceRefusal):
                return replace(
                    emission, stages=flow.finish(), device_artifacts=tuple(emissions)
                )
            emissions.append(emission)
        device_artifacts = tuple(emissions)
        specification = device.specification_provider(device_artifacts)
        upstream = tuple(identifier for e in emissions for identifier in e.upstream)
        rows_adaptation = {"stations": [e.rows_adaptation for e in emissions]}
    elif device is not None:
        if specification_provider is None:
            raise SliceAssemblyError(
                "a device was supplied without a specification provider, so "
                "there is nothing to turn its artifacts into a specification. "
                "Assembling one needs the source part, the announcements and "
                "the sector structure, which are a protocol's identity and not "
                "this tier's (spec/architecture.md 3.3)"
            )
        if device.station is not None:
            raise SliceAssemblyError(
                f"the single-device route was given the station {device.station}; "
                "a station identity tells stations apart and is declared on a "
                "MultiDeviceRequests, where there is more than one"
            )
        prologue = _run_device_prologue(device, flow)
        if isinstance(prologue, SliceRefusal):
            return replace(prologue, stages=flow.finish())
        receiver_artifact, reduction_artifact = prologue.receiver, prologue.reduction
        rows_adaptation, upstream = prologue.rows_adaptation, prologue.upstream
        specification = specification_provider(receiver_artifact, reduction_artifact)

    assert specification is not None  # the exclusive or above
    stations_told = (
        device.devices if isinstance(device, MultiDeviceRequests)
        else () if device is None else (device,)
    )
    _check_public_choice_told(specification, stations_told)

    # THE RUN'S WORD ON THE CHAIN IT DOCKED (protocol-compiler/
    # req:link-row-provenance (ii)), per measured factor: on a prologue route, for
    # flat-instance artefacts whose one instance link and read-off family are what the
    # specification presents at every factor. A supplied specification passes none, and
    # the compiler then emits A-LINK.
    provenance = attest_chain_provenance(
        specification,
        _artifacts_by_factor(
            specification, device, device_artifacts, reduction_artifact
        ),
    )
    flow.start(SliceStage.COMPILATION, artefacts=list(upstream))
    compilation = compile_specification(specification, chain_provenance=provenance)
    if compilation.refusal is not None:
        refusal = compilation.refusal
        flow.refused(SliceStage.COMPILATION, str(refusal.reason), refusal.detail)
        return SliceRefusal(
            stage=SliceStage.COMPILATION,
            reason=str(refusal.reason),
            detail=refusal.detail,
            compilation=compilation,
            stages=flow.finish(),
            device_artifacts=device_artifacts,
        )
    declaration = compilation.declaration
    assert declaration is not None  # CompilationResult enforces the exclusive or
    _check_declared_stations(device_artifacts, declaration)
    declaration_artefact = Artefact(
        kind=ArtefactKind.DECLARATION,
        digest=artefact_digest(compilation.as_machine_record()),
        record_key="payload.stages.compilation",
    )
    transmitter_artefact = Artefact(
        kind=ArtefactKind.TRANSMITTER_ARTIFACT,
        digest=artefact_digest(specification.source.artifact.as_machine_record()),
        # THE TRANSMITTER'S ARTEFACT IS READ BY THE COMPILER AND REACHES THE
        # RECORD ONLY AS A CONSUMED VERSION. It is an artefact of this graph
        # all the same -- the compilation consumed it -- and naming it here is
        # what lets a reader see where Alice's declaration entered.
        record_key="payload.contracts.transmitter",
    )
    flow.executed(
        SliceStage.COMPILATION,
        emits=[transmitter_artefact, declaration_artefact],
        key_length_eligible=compilation.key_length_eligible,
        acceptance_alphabet=list(declaration.acceptance_alphabet),
    )

    interface = (
        None
        if channel_interface_provider is None
        else channel_interface_provider(receiver_artifact)
    )
    if isinstance(device, MultiDeviceRequests) and device.channel_interface_provider:
        if channel_interface_provider is not None:
            raise SliceAssemblyError("declare one channel-interface provider")
        interface = device.channel_interface_provider(device_artifacts)
    if isinstance(interface, BipartiteChannelInterface):
        if len(device_artifacts) != len(interface.arms):
            raise SliceAssemblyError("bipartite arms must match the device stations")
        for arm, emission in zip(interface.arms, device_artifacts, strict=True):
            _check_declared_modes(arm, emission.receiver)
    elif isinstance(interface, ModeIntensityChannelInterface):
        _check_declared_modes(interface.arm, receiver_artifact)
    else:
        _check_declared_modes(interface, receiver_artifact)

    # THE REFERENCE COMPANION, compiled beside the declaration by the same map
    # from the same specification (protocol-compiler/req:reference-companion-
    # compiled): the measured families of the factors whose reduction emitted
    # one, and their last links' entries, replaced; nothing decided on it.
    artifacts = (
        tuple(emission.reduction for emission in device_artifacts)
        if device_artifacts
        else (() if reduction_artifact is None else (reduction_artifact,))
    )
    companion = (
        compile_reference_companion(specification, compilation, artifacts)
        if artifacts
        else None
    )
    if isinstance(companion, CompiledReferenceCompanion):
        companion = replace(companion, companion_of=declaration_artefact.identifier)

    # receiver/detector-imperfections/req:loss-before-evaluation, for the RAW
    # law too: it is the honest model's law on X x V, and lambda_EC and the
    # record's raw table are formed from it. Decided before the provider is
    # called, at the stage whose law it is: see LossAppliedRawProvider.
    normalized = _normalized_stations(device_artifacts, receiver_artifact)
    if (
        normalized
        and raw_joint_provider is not None
        and not isinstance(raw_joint_provider, LossAppliedRawProvider)
    ):
        reason = str(RunRefusalReason.FACTORED_LOSS_NOT_APPLIED)
        detail = _loss_not_applied_detail(
            normalized, "raw joint provider", "raw_factored_loss_applied"
        )
        flow.start(
            SliceStage.HONEST_MODEL,
            artefacts=[declaration_artefact.identifier],
            config_keys=["model"],
        )
        flow.refused(SliceStage.HONEST_MODEL, reason, detail)
        return SliceRefusal(
            stage=SliceStage.HONEST_MODEL,
            reason=reason,
            detail=detail,
            compilation=compilation,
            receiver_artifact=receiver_artifact,
            stages=flow.finish(),
            device_artifacts=device_artifacts,
        )
    return Preparation(
        specification=specification,
        compilation=compilation,
        declaration=declaration,
        acceptance_alphabet=tuple(declaration.acceptance_alphabet),
        receiver_artifact=receiver_artifact,
        reduction_artifact=reduction_artifact,
        rows_adaptation=rows_adaptation,
        raw_joint_distribution=(
            None if raw_joint_provider is None else raw_joint_provider(declaration)
        ),
        channel_interface=interface,
        declaration_artefact=declaration_artefact,
        device_artifacts=device_artifacts,
        reference_companion=companion,
    )


def _normalized_stations(
    device_artifacts: tuple[DeviceEmission, ...],
    receiver_artifact: ReceiverMeasurementArtifact | None,
) -> tuple[tuple[str, Fraction], ...]:
    """Return every station whose receiver carries a factored loss ``t < 1``.

    Read off the receiver artefacts' ``efficiency_record``
    (``receiver/detector-imperfections/req:normalization-record``): each
    station of a multi-station run by its declared factor, or the one receiver
    of the single-device route as ``receiver``.
    """
    named: tuple[tuple[str, ReceiverMeasurementArtifact], ...]
    if device_artifacts:
        named = tuple(
            (
                "receiver" if emission.station is None else emission.station.factor,
                emission.receiver,
            )
            for emission in device_artifacts
        )
    elif receiver_artifact is not None:
        named = (("receiver", receiver_artifact),)
    else:
        named = ()
    return tuple(
        (name, artifact.efficiency_record.normalization.factored_loss)
        for name, artifact in named
        if artifact.efficiency_record.normalization.below_one
    )


def _loss_not_applied_detail(
    normalized: tuple[tuple[str, Fraction], ...], provider: str, marker: str
) -> str:
    """Return the detail of a ``factored_loss_not_applied`` refusal.

    ``provider`` names the provider refused (the honest or the raw one) and
    ``marker`` the function of this module that declares the loss applied.
    """
    spelled = ", ".join(f"{name}: t = {t}" for name, t in normalized)
    return (
        f"the receiver of {spelled} was compiled at its normalized station "
        "(receiver/detector-imperfections/req:efficiency-normalization), and "
        f"the {provider} does not declare that it applies the pure-loss "
        "channel of that factored loss before evaluating the emitted "
        "measurement (req:loss-before-evaluation; "
        f"certiqs_key.runs.pipeline.{marker}). Its law would be "
        "a more efficient receiver's. Apply the loss and declare it, or "
        "declare efficiency_normalization = 1 to the receiver"
    )


def _station_factors(
    device: DeviceRequests | MultiDeviceRequests | None,
) -> tuple[str, ...]:
    """Return the declared station factors in station order; ``()`` off that route."""
    if not isinstance(device, MultiDeviceRequests):
        return ()
    return tuple(
        station.station.factor
        for station in device.devices
        if station.station is not None  # MultiDeviceRequests requires one
    )


def certification_withheld(prepared: Preparation) -> tuple[str, ...]:
    """Return ``frank-wolfe/req:certified-evaluation`` (vii)'s reasons for a run.

    Read off the receiver artifacts the run's reductions consumed: (a)
    ``numerical_trust_premise`` where one records A-EIG invoked at some setting
    (``receiver/req:eig-ledger-row``), A-EIG being the one numerical-trust
    assumption a run's closure can hold; (b) ``receiver_weight_floating_point``
    where one whose slot carries a weight labels its evaluation
    ``floating_point`` (``receiver/req:evaluation-label``): its weights are
    routed into the declaration setting by setting, and a uniform weight
    counts every setting, so some floating-point setting weight enters.
    """
    receivers = [emission.receiver for emission in prepared.device_artifacts]
    if not receivers and prepared.receiver_artifact is not None:
        receivers = [prepared.receiver_artifact]
    reasons: list[str] = []
    if any(
        dict(row.constrains).get("invoked_at")
        for artifact in receivers
        for row in artifact.assumption_ledger
        if row.assumption_id is ReceiverAssumption.A_EIG
    ):
        reasons.append("numerical_trust_premise")
    if any(
        artifact.bound_evaluation != "rigorous" and artifact.high_photon_bounds.entries
        for artifact in receivers
    ):
        reasons.append("receiver_weight_floating_point")
    return tuple(reasons)


def _check_declared_stations(
    emissions: tuple[DeviceEmission, ...], declaration: CandidateDeclaration
) -> None:
    """Hold each station's declared identity against the compiled declaration.

    The instance declares which measured factor each
    station is (:class:`Station`), and the compiler emits the measured factors
    with their labels and parties. The two are declarations about the SAME
    factors by two parties -- the instance and ``protocol-compiler`` -- and the
    composition is this tier's (spec/architecture.md 3.3), so this is where
    they are held together, exactly as :func:`_check_declared_modes` holds the
    instance's mode space against the receiver artefact's.

    Each station must name a measured factor, with that factor's party, and
    every measured factor must be named by exactly one station. THE ORDER IS
    NOT CHECKED: the point of the declaration is that nobody has to pair by
    position. A disagreement is a :class:`SliceAssemblyError` and not a
    refusal: both sides are well formed, and it is their composition that is
    wrong. Nothing is checked on a route without stations.
    """
    stations = [emission.station for emission in emissions]
    if not stations or any(station is None for station in stations):
        return
    declared = {
        label: factor.party
        for label, factor in zip(
            declaration.measured_factor_labels,
            declaration.measured_factors,
            strict=True,
        )
    }
    named = sorted(station.factor for station in stations if station is not None)
    if named != sorted(declared):
        raise SliceAssemblyError(
            f"the stations name the measured factors {named} and the compiled "
            f"declaration has {sorted(declared)}. Each station is one measured "
            "factor of the declaration and each measured factor one station; "
            "a disagreement is a composition error rather than either side's "
            "refusal"
        )
    for station in stations:
        assert station is not None
        if declared[station.factor] != station.party:
            raise SliceAssemblyError(
                f"the station {station.factor!r} declares the party "
                f"{station.party!r} and the compiled declaration scopes that "
                f"factor to {declared[station.factor]!r}"
            )


def _check_declared_modes(
    interface: ChannelInterface | OpticalChannelArm | None,
    artifact: ReceiverMeasurementArtifact | None,
) -> None:
    """Hold an instance's declared mode space against the receiver artefact's.

    An INSTANCE may declare the structured mode space, because the
    receiver artefact carries only label strings and parsing one back into a
    path and a polarization is the guessing the structure exists to remove. The
    price of that is that the instance could declare a space the artefact does
    not have, and nothing would say so: an optics view would draw rails that
    are not the ones the POVM was built on, in the right shape and with the
    wrong content, which is the hardest kind of mistake to see.

    So this tier compares the two where it has both -- the labels IN ORDER, and
    each mode's role against what the artefact's own label lists make it -- and
    a disagreement is a HARD ERROR and not a refusal. It is not either module's
    to decline: the receiver emitted a well-formed artefact and the instance
    returned a well-formed interface, and the composition is this tier's
    (spec/architecture.md 3.3), which is where the two are held together.

    Nothing is checked on the route with no mode space, where both sides are
    ``None``, nor where no provider was supplied.
    """
    if interface is None or interface.modes is None or artifact is None:
        return
    space = artifact.input_mode_space
    declared = tuple(mode.label for mode in interface.modes)
    if declared != tuple(space.mode_labels):
        raise SliceAssemblyError(
            f"the instance declared the mode space {list(declared)} and the "
            f"receiver artefact emitted {list(space.mode_labels)}. The instance's "
            "structured modes are the instance's declaration ABOUT this "
            "artefact, in the artefact's own mode_labels order, and a "
            "disagreement is a composition error rather than either module's "
            "refusal"
        )
    for mode in interface.modes:
        expected = mode_role(mode.label, space)
        if mode.role is not expected:
            raise SliceAssemblyError(
                f"the instance declared mode {mode.label} with role "
                f"{mode.role}, and the receiver artefact's own label lists "
                f"make it {expected}. The role is READ OFF those lists and is "
                "never decided from a label's spelling"
            )
    # AND THE CHANNEL HALF IN THE ARTEFACT'S OWN CHANNEL ORDER, WHICH IS A
    # DIFFERENT ORDER FROM THE ONE ABOVE. ``mode_labels`` is Definition
    # def:modes' lexicographic order; ``channel_labels`` is the ``Inp_C`` block
    # of Section 2.5's ``subsystem_order``, which "takes precedence where the
    # two disagree" -- and ``check_input_modes`` decides range, disjointness
    # and non-emptiness and NOT that ``Inp_C`` ascends in ``M``, so a receiver
    # may emit them in different orders and is not refused for it.
    #
    # ``ChannelInterface.channel_modes`` is ``modes`` FILTERED, so it inherits
    # the ``mode_labels`` order, while ``transmitted_basis`` and the columns of
    # the isometry ``V`` are built in ``channel_labels`` order. On such a device
    # the two index different modes, and runs/channel.py's own "THE BASIS ORDER
    # IS THE TRAP" section says what that costs: a consumer reading ``V``
    # against ``channel_modes`` builds a state that is still a state, still has
    # the right marginal, and has the wrong error rate IN ONE BASIS ONLY.
    #
    # It is checked here and not in the receiver because the disagreement is
    # between two well-formed artefacts, which is this tier's business. AND IT
    # IS CHECKED AT ALL BECAUSE ``channel_modes`` IS A DERIVED VIEW: were it
    # built straight from ``channel_labels`` the agreement would hold by
    # construction and need no guard.
    channel = interface.channel_modes or ()
    if tuple(mode.label for mode in channel) != tuple(space.channel_labels):
        raise SliceAssemblyError(
            f"the instance's channel modes read "
            f"{[mode.label for mode in channel]} and the receiver artefact's "
            f"channel_labels are {list(space.channel_labels)}. The columns of "
            "V are indexed by the artefact's channel order and by no other, "
            "so a disagreement here mis-indexes the isometry against the "
            "modes a consumer reads it with"
        )


def prepare(
    config: RunConfig,
    *,
    device: DeviceRequests | MultiDeviceRequests | None = None,
    specification: ProtocolSpecification | None = None,
    specification_provider: SpecificationProvider | None = None,
    raw_joint_provider: RawJointProvider | None = None,
    channel_interface_provider: ChannelInterfaceProvider | None = None,
) -> PreparationOutcome:
    """Run everything that needs no oracle, and return it.

    ``config`` is present so that a caller prepares THE CONFIGURATION IT
    WILL RUN rather than a lookalike -- the declared tolerance the prologue
    spends is read off it, and the planned stage list it returns is that
    configuration's. Nothing else of the configuration is read here: the
    rounds, the budget and the parameters belong to the stages this function
    does not run.

    Args:
        config: the run configuration. Its ``declared_tolerance`` is what the
            instance's snap is permitted to spend, and is decided here on the
            same rule :func:`run_slice` decides it on.
        device: the physical receiver's declarations, or ``None`` on the route
            that supplies a finished specification.
        specification: the finished specification, on that route.
        specification_provider: builds the specification from the device
            prologue's two artefacts.
        raw_joint_provider: the instance's honest model over ``X x V``. See
            :data:`RawJointProvider`; ``None`` is an honest answer.

    Returns:
        A :class:`Preparation`, or a :class:`SliceRefusal` naming the stage
        that declined and that module's own reason.
    """
    _check_declared_tolerance(config.declared_tolerance)
    flow = FlowRecorder(
        device_prologue=device is not None, stations=_station_factors(device)
    )
    prepared = _prepare(
        specification,
        device=device,
        specification_provider=specification_provider,
        raw_joint_provider=raw_joint_provider,
        channel_interface_provider=channel_interface_provider,
        flow=flow,
    )
    if isinstance(prepared, SliceRefusal):
        return prepared
    return replace(prepared, stages=flow.planned())


def _require_matched_alphabet(
    outcomes: Sequence[str], alphabet: Sequence[str]
) -> None:
    """Refuse an acceptance set not indexed by the declaration's alphabet.

    Implements ``statistics/req:matched-alphabet``: the set is built on a
    matched alphabet and round count (``statistics/def:matched-alphabet``),
    and before it is docked its alphabet and enumeration are compared with
    the declaration the consumer solves. The round count needs no comparison
    here: :func:`run_slice` hands the one ``rounds`` argument to both. A
    disagreement is a hard error of the consumer's input validation, a refusal
    code of neither module; nothing is repaired.
    """
    if tuple(outcomes) != tuple(alphabet):
        raise SliceAssemblyError(
            f"the constructed acceptance set is indexed by {list(outcomes)} "
            f"and the emitted declaration by {list(alphabet)}. "
            "statistics/req:matched-alphabet builds the set only on a matched "
            "alphabet and round count (statistics/def:matched-alphabet): the "
            "alphabet and its enumeration are the consuming declaration's, and "
            "a disagreement is a hard error rather than either module's refusal"
        )


def _check_declared_tolerance(declared_tolerance: float) -> None:
    """Decide ``tau`` on the run, not only on one of its representations.

    A caller may reach the pipeline without ever building a
    :class:`~certiqs_key.runs.config.RunConfig` -- every instance's own
    ``run_slice`` does -- and spec/architecture.md 2.8 puts the rule on the RUN:
    "tau itself has no default and no fallback: a run whose configuration does
    not declare it is refused". The domain is the repo-wide ``[0, 1)`` of that
    section, whose upper limit is derived there; the type is binary64 because
    "a declared value IS its binary64 datum". Nothing is coerced and nothing
    substituted.
    """
    if type(declared_tolerance) is not float:
        raise SliceAssemblyError(
            f"declared_tolerance is {declared_tolerance!r}, a "
            f"{type(declared_tolerance).__name__}. The engine is binary64 end "
            "to end (spec/architecture.md 2.8): pass 0.0 rather than 0, "
            "and a float rather than a Fraction"
        )
    if not 0.0 <= declared_tolerance < 1.0:
        raise SliceAssemblyError(
            f"declared_tolerance is {declared_tolerance!r}, outside [0, 1). "
            "spec/architecture.md 2.8 fixes that interval repo-wide "
            "and derives its upper limit; nothing may widen it"
        )



def _run_device_prologue(
    device: DeviceRequests,
    flow: FlowRecorder,
    *,
    index: int | None = None,
) -> DeviceEmission | SliceRefusal:
    """Run spec/architecture.md 6's three stages, in that order, or refuse.

    Split out so that :func:`run_slice` reads as the one ordered path it is. The
    order is the whole content of this function: ``reductions`` Section 2.2
    says of its own three steps that "THE ORDER IS PART OF THE INTERFACE, NOT AN
    IMPLEMENTATION DETAIL", and the same holds one level up.

    ``index`` is this station's position in a multi-station request, ``None``
    on the single-device route. It decides WHERE THE RECORD HOLDS the two
    artefacts this prologue emits -- ``payload.stages.stations[<index>]``,
    whose ``receiver`` and ``reduction`` are this station's, or the
    single-device keys -- so that every ``record_key`` resolves to the artefact
    it names. Each stage it records names the
    station by its declared factor.
    """
    station = None if device.station is None else device.station.factor
    receiver_key, reduction_key = (
        ("payload.stages.receiver_construction", "payload.stages.reduction")
        if index is None
        else (
            f"payload.stages.stations[{index}].receiver",
            f"payload.stages.stations[{index}].reduction",
        )
    )
    # THE DEVICE SECTION IS NAMED PER SECTION AND NOT PER KEY, and that is
    # the uniformity rule rather than laziness: ``RunConfig.device`` is
    # OPAQUE to this tier by construction (an instance's provider reads it and
    # nothing else does), so naming individual keys here would be this tier
    # claiming to know a vocabulary it deliberately does not. The instance's
    # runner, which does know, names them per key where it hands them over.
    flow.start(
        SliceStage.RECEIVER_CONSTRUCTION, config_keys=["device"], station=station
    )
    emission = construct_receiver(
        device.receiver_request,
        exact_reference_only=not device.reference_enclosure,
    )
    if emission.refusal is not None:
        flow.refused(
            SliceStage.RECEIVER_CONSTRUCTION,
            str(emission.refusal.reason),
            emission.refusal.detail,
        )
        return SliceRefusal(
            stage=SliceStage.RECEIVER_CONSTRUCTION,
            reason=str(emission.refusal.reason),
            detail=emission.refusal.detail,
        )
    artifact = emission.artifact
    assert artifact is not None  # ReceiverEmission enforces the exclusive or
    receiver_artefact = Artefact(
        kind=ArtefactKind.RECEIVER_ARTIFACT,
        digest=artefact_digest(artifact.as_payload()),
        record_key=receiver_key,
    )
    flow.executed(
        SliceStage.RECEIVER_CONSTRUCTION,
        emits=[receiver_artefact],
        receiver_version=artifact.mathematical_spec_version,
        photon_cutoff=artifact.bound_quantifier_domain.photon_cutoff,
    )

    flow.start(
        SliceStage.RECEIVER_DOCKING,
        artefacts=[receiver_artefact.identifier],
        config_keys=["declared_tolerance"],
        station=station,
    )
    adaptation: Mapping[str, object] | None = None
    rows: ReceiverArtifactRows
    if device.rows_adapter is None:
        docked = receiver_artifact_rows(artifact)
        if isinstance(docked, DockingRefusal):
            flow.refused(
                SliceStage.RECEIVER_DOCKING, str(docked.reason), docked.detail
            )
            return SliceRefusal(
                stage=SliceStage.RECEIVER_DOCKING,
                reason=str(docked.reason),
                detail=docked.detail,
                receiver_artifact=artifact,
            )
        rows = docked
    else:
        # The instance's adapter docks the artefact itself, in the form it
        # declares, and snaps what it declares; a docking refusal comes back
        # as its refusal with the docking reason unchanged.
        adapted = device.rows_adapter(artifact)
        if isinstance(adapted, AdapterRefusal):
            flow.refused(
                SliceStage.RECEIVER_DOCKING, adapted.reason, adapted.detail
            )
            return SliceRefusal(
                stage=SliceStage.RECEIVER_DOCKING,
                reason=adapted.reason,
                detail=adapted.detail,
                receiver_artifact=artifact,
            )
        rows, adaptation = adapted.rows, adapted.report

    flow.executed(
        SliceStage.RECEIVER_DOCKING,
        emits=[receiver_artefact],
        instance_declared_the_family=device.rows_adapter is not None,
    )

    flow.start(
        SliceStage.REDUCTION,
        artefacts=[receiver_artefact.identifier],
        config_keys=["device"],
        station=station,
    )
    request = device.reduction_request
    # reductions/req:recv-row-provenance (i), (iii): this tier built the
    # receiver artefact one stage above and docks it here, so it is the part
    # of the engine that can say so; the reduction decides (ii) and (iv) on the
    # artefact and omits the A-RECV row only where all four hold.
    provenance = attest_receiver_provenance(artifact, rows)
    call = ReductionCall(
        rows,
        device.reduction_declaration,
        request,
        public_choice_applied=device.public_choice_at_station,
        receiver_provenance=provenance,
    )
    outcome = device.reduction_entry(call)
    if outcome.refusal is not None:
        flow.refused(
            SliceStage.REDUCTION,
            str(outcome.refusal.reason),
            outcome.refusal.detail,
            rule=outcome.refusal.rule,
        )
        return SliceRefusal(
            stage=SliceStage.REDUCTION,
            reason=str(outcome.refusal.reason),
            detail=outcome.refusal.detail,
            receiver_artifact=artifact,
            verification_report=outcome.verification_report,
            rule=outcome.refusal.rule,
        )
    reduction = outcome.artifact
    assert reduction is not None  # ReductionOutcome enforces the exclusive or

    if device.carried_operator_provider is not None:
        requested = device.carried_operator_provider(reduction)
        if requested:
            # The SECOND pass, on the SAME rows and the same declaration. Only
            # the requested operators differ, so a refusal here is a refusal of
            # those entries and of nothing the baseline already passed.
            call = ReductionCall(
                rows, device.reduction_declaration,
                replace(request, carried_operators=requested),
                public_choice_applied=device.public_choice_at_station,
                receiver_provenance=provenance,
            )
            outcome = device.reduction_entry(call)
            if outcome.refusal is not None:
                flow.refused(
                    SliceStage.REDUCTION,
                    str(outcome.refusal.reason),
                    outcome.refusal.detail,
                    rule=outcome.refusal.rule,
                    pass_="carried-operator",
                )
                return SliceRefusal(
                    stage=SliceStage.REDUCTION,
                    reason=str(outcome.refusal.reason),
                    detail=(
                        f"{outcome.refusal.detail} [on the carried-operator pass, "
                        f"asking for {len(requested)} entry/entries built from the "
                        "baseline emission; the baseline itself was emitted]"
                    ),
                    receiver_artifact=artifact,
                    verification_report=outcome.verification_report,
                    rule=outcome.refusal.rule,
                )
            reduction = outcome.artifact
            assert reduction is not None

    reduction_artefact = Artefact(
        kind=ArtefactKind.REDUCTION_CHAIN,
        digest=artefact_digest(reduction.as_machine_record()),
        record_key=reduction_key,
    )
    flow.executed(
        SliceStage.REDUCTION,
        emits=[reduction_artefact],
        route=str(reduction.route),
        status=str(reduction.status),
        constraint_entries=len(reduction.constraint_list),
        links=len(reduction.reduction_chain.links),
    )
    return DeviceEmission(
        receiver=artifact,
        reduction=reduction,
        call=call,
        rows_adaptation=adaptation,
        # THE TWO ARTEFACTS THE SPECIFICATION WAS BUILT FROM, by name, so that
        # the compilation can record the edge that carries them. This tier
        # handed both to the instance's specification provider one line above,
        # and the specification the compiler consumes is what came back: on the
        # device route the prologue's emissions would otherwise be dead ends in
        # the graph, with the compilation showing no input at all.
        upstream=(receiver_artefact.identifier, reduction_artefact.identifier),
        station=device.station,
    )


def _honest_payload(
    honest: Mapping[str, Fraction] | HonestEnvelope,
) -> dict[str, Any]:
    """Return the honest input as the record serialises it, for its digest.

    A distribution is its ``"p/q"`` table, as before; an envelope is the pair of
    tables under ``lower`` and ``upper``, which is how the record writes it.
    """
    if isinstance(honest, HonestEnvelope):
        return {
            "lower": {key: str(value) for key, value in honest.lower.items()},
            "upper": {key: str(value) for key, value in honest.upper.items()},
        }
    return {key: str(value) for key, value in honest.items()}
