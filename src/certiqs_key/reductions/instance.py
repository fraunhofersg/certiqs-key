"""Definition ``def:reduction-instance``: what a squasher hands the core.

WHY THIS TYPE EXISTS. An emission theorem stated over ONE construction -- a
branching flag-state target -- would hard-wire that construction into the entry
point: the normalizer, the entries, the chain, the descriptor and the ledger
would all name that model. The emission theorems (``thm:emit``,
``cor:entries``, ``def:emitnorm``, ``def:exactadm``, ``thm:chain``,
``ass:recv``) are therefore stated over an abstract instance, exactly as the
receiver module's own emission theorems are stated over
``def:setting-family``. This file is that abstraction in code.

WHAT AN INSTANCE IS, IN THE DEFINITION'S OWN FOUR PARTS
=======================================================
(I1) THE HANDED MODEL AND THE DATUM: a POVM presented as a finite list of DATA
SECTORS, each with a declared dimension and, per outcome, a matrix formed from
the handed numbers by finitely many exact operations, CLASS COMPLETE; together
with HYPOTHESES (H) on the rest of the model -- operators without a finite
presentation, above-cutoff facts, register POVMs -- each decided exactly on
declared data by an interface row or a ledger assumption, AND NONE OF WHICH
READS A DATA-SECTOR ENTRY. That last clause is the STABILITY CLAUSE, and it is
what lets ``thm:emit`` (iii) apply the instance's own existence theorem to the
NORMALISED datum without re-proving anything. :attr:`ReductionInstance.hypotheses`
is the record of (H); the normalizer reads data sectors only, which is
:mod:`certiqs_key.reductions.sectors`'s type distinction made structural.

(I2) THE TARGET: the sector set with its declared dimensions and order, the
scalar values, and ``F_v`` AS THE SECTOR-BLOCK LIST ``(F^(s)_v)_s`` -- assembled
by :func:`certiqs_key.reductions.sectors.assemble_sector_blocks`, the direct sum
``(+)_s`` being what the list means and not an object anything here carries.

(I3) THE EXISTENCE THEOREM: the channel with its constructor record and the
transported set, "stated for EVERY datum satisfying (H) and exactly admissible
per data sector". The record is the channel witness of
:mod:`certiqs_key.reductions.channels`; the theorem itself is a claim and is
not code.

(I4) THE CERTIFIED ENTRIES, each with its ``cor:pullback`` certificate
discharged AT THE NUMBERS ABOUT TO BE EMITTED.

THE BUILDER IS A PROTOCOL WITH ONE METHOD, AND THAT IS THE WHOLE COUPLING
=========================================================================
:class:`InstanceBuilder` has exactly one method. The core's
:func:`certiqs_key.reductions.emit.reduce` decides the rows that are decidable
before anything is constructed, hands the builder a :class:`BuildContext` --
the declared inputs, the validated lattice exponent, the resolved route, the
class decomposition, and THE CORE'S OWN NORMALIZER as one call -- and receives
a :class:`BuildOutcome`: the rows the builder owns, their outcomes, and the
instance or ``None``.

THE CORE NEVER IMPORTS A SUBMODULE. ``wpfss`` and the other submodules import
the core and supply builders; the core names none of them, which is what
makes deleting a removable submodule a deletion rather than an amendment.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Protocol

from certiqs_key.foundations.exact import Matrix
from certiqs_key.reductions.artifact import (
    ExactIdentity,
    SourceDescriptor,
    TargetDescriptor,
    WpfssData,
)
from certiqs_key.reductions.channels import ChannelWitness, TransportedOperator
from certiqs_key.reductions.constraints import ConstraintEntry, EntryWriting
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import (
    JointOutcome,
    Label,
    ReductionCall,
)
from certiqs_key.reductions.normalizer import JointClass, Normalization, normalize
from certiqs_key.reductions.reasons import (
    AssumptionRow,
    FailClosedRow,
    LinkKind,
    Refusal,
    Route,
)
from certiqs_key.reductions.sectors import (
    ScalarValues,
    Sector,
    SectorKind,
    SectorSet,
)
from certiqs_key.reductions.validation import RuleOutcome

__all__ = [
    "Branch",
    "BuildContext",
    "BuildOutcome",
    "CompanionMode",
    "InstanceBuilder",
    "Precomposition",
    "ReductionInstance",
    "combine_branches",
    "precompose",
]


@dataclass(frozen=True)
class ReductionInstance:
    """One reduction instance: everything the core needs and nothing device-free.

    Every field is the BUILDER'S. The core reads them, decides the emitted
    family on the normalised datum, binds the chain and assembles the artifact;
    it constructs none of them and it names no construction.
    """

    #: (I2): the sector set with its declared dimensions and order.
    sectors: SectorSet
    #: (I1) after ``def:emitnorm``: the DECLARED datum of the data sectors,
    #: with the per-sector record of what the normalizer did.
    normalized: Normalization
    #: (I2): ``phi_s(v)`` per scalar sector.
    scalar_values: ScalarValues
    #: (I2): ``{F_v}`` in the declared order of ``V``, assembled one sector
    #: block at a time AND CARRIED AS THAT LIST: ``target_povm[i]`` is
    #: ``(F^(s)_{v_i})_s``, one square block per sector in the declared sector
    #: order. ``F_v = (+)_s F^(s)_v`` "is what that list MEANS, not an object
    #: the artifact carries" (the outputs table, `target_povm`;
    #: spec/architecture.md 2.8-2.9).
    target_povm: tuple[tuple[Matrix, ...], ...]
    #: (I3): the constructor record the entries are certified against.
    witness: ChannelWitness
    #: (I3): the transported set, each entry with its pull-back certificate.
    transported: tuple[TransportedOperator, ...]
    #: (I4): the certified entries, module-built and caller-requested together.
    entries: tuple[ConstraintEntry, ...]
    #: The labels of the entries the INSTANCE built, as against those a caller
    #: requested. Only the first are discharged by theorem.
    module_built: tuple[str, ...]
    #: Label to THE INSTANCE'S OWN discharge locator, for every entry in
    #: :attr:`module_built`. THE BUILDER SUPPLIES IT AND THE CORE NAMES NO
    #: CONSTRUCTION: the certificate of a flat instance's entry is
    #: ``wpfss/cor:fssinstance``'s, of a branching instance's entry
    #: ``cor:register-instance`` (ii)'s, and a core that hard-coded either
    #: would attribute a certificate the entry did not earn.
    module_built_locators: Mapping[str, str]
    #: Label to the locator of what discharged it, for a caller-requested entry
    #: the builder decided on declared data before the certificate row ran.
    requested_locators: Mapping[str, str]
    #: Label to the direction a caller-declared constant was rounded in, for
    #: every requested entry whose constant was off the lattice
    #: (``cor:entries`` (iii)). ``thm:emit`` (iv): "the direction of each of
    #: these is recorded in ``emission_record``", which is where the core puts
    #: it.
    constant_rounding: Mapping[str, str]
    #: A caller-requested entry the builder refused. The core folds it into the
    #: constraint-certificate row rather than deciding it twice.
    carried_operator_refusal: Refusal | None
    #: (I1): the record of (H) -- what the instance assumes about the rest of
    #: the model, each item decided by a row or named by a ledger assumption.
    #: NONE OF THEM READS A DATA-SECTOR ENTRY; that is the stability clause.
    hypotheses: tuple[str, ...]
    #: The emitted ``source_descriptor``: the physical system as the instance
    #: describes it, with its branching register where it has one.
    source_descriptor: SourceDescriptor
    #: How the chain's first link names the physical family.
    physical_family_description: str
    #: The emitted ``target_descriptor``, with the instance's own formulas.
    target_descriptor: TargetDescriptor
    #: The emitted ``exact_identity``, including what the normalizer's action
    #: means for the DECLARED model (``rem:emitclaim``).
    exact_identity: ExactIdentity
    #: The emitted ``reachable_set_statement``.
    reachable_set_statement: str
    #: The emitted certified-weight record.
    weight_record: WpfssData
    #: The certified weights by outcome, as the entries were built at.
    weights: Mapping[JointOutcome, Fraction]
    #: The declared value of every parameter each ledger assumption constrains,
    #: by assumption id: a string, or structured data where the instance binds
    #: a declared record (a branching model).
    ledger_rows: Mapping[str, tuple[tuple[str, object], ...]]
    #: The ledger rows the instance ADDS to the core's, each with its place in
    #: the table. Empty for an instance that adds none.
    extra_assumptions: tuple[AssumptionRow, ...]
    #: The link kinds that may name this instance's squashing link.
    squashing_kinds: frozenset[LinkKind]
    #: Those of them whose choice is BOUND TO THE ROUTE, because "the two
    #: routes run on DIFFERENT CHANNELS" (``rem:tworoutes``). A kind in
    #: :attr:`squashing_kinds` and not here names the same composed channel
    #: from another side and is accepted on either route.
    route_bound_kinds: frozenset[LinkKind]
    #: The kind a route-bound squashing link must carry on the resolved route.
    expected_squashing_kind: LinkKind
    #: Label to the writing in the form ``eq:instance-entry`` by which a
    #: caller-requested entry was recognised, for every requested entry the
    #: builder certified: the reference companion forms the entry's companion
    #: form at that writing (``reductions/cor:reference-companion`` (vi);
    #: ``req:reference-companion`` (iii)).
    requested_writings: Mapping[str, EntryWriting] = field(default_factory=dict)
    #: The labels of the entries whose discharging claim reads NO supplier
    #: fact, so that the licence names no receiver artefact for them
    #: (``req:licence-record``): a requested default carried operator
    #: (``cor:entries`` (i)), and a branch-weight entry decided on a declared
    #: register POVM. Every other entry's discharge is read as reading the
    #: supplier's claims under A-RECV, which names a premise and never omits one.
    supplier_free_entries: frozenset[str] = frozenset()
    #: The channel ``Phi`` this instance is precomposed with, where it is one
    #: (``lem:precomposed-instance``); ``None`` otherwise. Set by
    #: :func:`precompose` and read by the chain, which records the pull-backs
    #: of the carried tuple through ``Phi^dagger``.
    precomposition: Precomposition | None = None

    def __post_init__(self) -> None:
        """Refuse an instance that under-declares what the definition requires.

        TWO STRUCTURAL CONDITIONS, both of them the DEFINITION'S and neither of
        them a rule a caller declares, so both are decided here rather than in
        a fail-closed row: a row decides a declaration, and these decide a
        BUILDER.

        (I4): a module-built entry carries the instance's own discharge
        locator. ``cor:entries`` (iii) emits an instance's own entry "at the
        constant its certificate is discharged at", and the certificate is the
        instance's -- so a module-built entry with no locator would reach the
        verification report attributed to nothing, or to another submodule's
        corollary.

        (I3): the transported set CONTAINS EVERY SECTOR PROJECTOR. The
        definition asks for "a finite transported set hat O[A'] of
        sector-block-diagonal Hermitian operators on Q CONTAINING EVERY SECTOR
        PROJECTOR Pi_s", and its third consequence puts the certificate
        ``(Pi_s, >=, 0)`` of every instance there -- "it travels with the
        transported set, ON EVERY ROUTE", which ``cor:entries`` (i) emits and
        the ``transported_operators`` output row records per entry. Since the
        constraint list is EMPTY on the ``encoded`` route, that row is the only
        place the certificate can be emitted, so a builder that declares fewer
        operators than (I3) requires emits an artifact that carries fewer
        certified operators than the instance earns. Linearity does not repair
        it: (I3)'s closing sentence transports every real combination of what
        is DECLARED, and ``Pi_(m)`` is not a combination of the two sums a
        cutoff split transports. The containment is decided on the operators
        themselves and not on labels, so a builder cannot satisfy it by naming
        one. The operators compared are
        SECTOR-BLOCK LISTS on both sides -- what the builder declared and
        :meth:`SectorSet.projectors` -- so the comparison is per block and no
        ``dim H(Q) x dim H(Q)`` array is formed to make it.
        """
        missing = tuple(
            label
            for label in self.module_built
            if label not in self.module_built_locators
        )
        if missing:
            raise MalformedInputError(
                "every module-built entry carries the instance's own discharge "
                f"locator (def:reduction-instance (I4)); {missing!r} carry none"
            )
        carried = {entry.target_operator for entry in self.transported}
        undeclared = tuple(
            sector.label
            for sector, projector in zip(
                self.sectors.sectors, self.sectors.projectors(), strict=True
            )
            if projector not in carried
        )
        if undeclared:
            raise MalformedInputError(
                "the transported set of an instance contains EVERY sector "
                "projector (def:reduction-instance (I3), third consequence; "
                "cor:entries (i)); the projectors of "
                f"{undeclared!r} are not in it"
            )

    @property
    def target_dimension(self) -> int:
        """Return ``dim H(Q) = sum_s d_s``."""
        return self.sectors.total_dimension

    def pullback_expression(self, expression: str) -> str:
        """Return a carried pull-back as THIS instance's: through ``Phi^dagger``.

        ``lem:precomposed-instance`` (ii): the pull-backs of ``J o Phi`` are
        ``Phi^dagger(O[A'])``. ``expression`` is the pull-back as the
        un-precomposed instance writes it; where nothing is precomposed it is
        returned unchanged.
        """
        if self.precomposition is None:
            return expression
        return f"{self.precomposition.adjoint}({expression})"


@dataclass(frozen=True)
class Precomposition:
    """A channel ``Phi`` in front of an instance -- ``lem:precomposed-instance``.

    The lemma's data as the record carries them: the channel's witness,
    which ACTS FIRST; how its adjoint is written in a pull-back
    (``Phi^dagger``); the source family of the precomposed instance, the
    declared model ``Phi^dagger(M')`` (item (iii)); and the reachable-set
    statement of the composite channel (``def:sound``). Nothing here is
    evaluable: like every witness, the record names the construction.
    """

    witness: ChannelWitness
    adjoint: str
    source_family_description: str
    reachable_set_statement: str


def precompose(
    instance: ReductionInstance, precomposition: Precomposition
) -> ReductionInstance:
    """Return the precomposed instance ``J o Phi`` -- ``lem:precomposed-instance``.

    Item (ii): ``J o Phi`` has the joint alphabet, data sectors, supports,
    handed datum, hypotheses, scalar values, sector set, target family,
    transported set, entry list and class-marginal flag of ``J``, so every
    one of those fields is kept; its channel is ``Lambda o Phi``, which the
    witness records as ``Phi`` precomposed (keeping the identity the entries
    are certified against, item (i): every certificate holds of the
    composite at the same constant); its pull-backs are
    ``Phi^dagger(O[A'])``, which the chain records
    (:meth:`ReductionInstance.pullback_expression`). Item (iii): the emission
    normalizer reads the same declared datum, so the emitted target, entries
    and constants are ``J``'s, and the declared model is ``Phi^dagger`` of
    ``J``'s, which is the source family recorded. A second precomposition
    is refused: the record carries one channel in front.
    """
    if instance.precomposition is not None:
        raise MalformedInputError(
            "an instance is precomposed with one channel at most here; "
            "compose the two channels into one witness first"
        )
    witness = instance.witness
    return replace(
        instance,
        witness=ChannelWitness(
            identity=witness.identity,
            equation=(
                f"{witness.equation}, precomposed with "
                f"{precomposition.witness.identity} (lem:precomposed-instance)"
            ),
            parameters=witness.parameters,
            composed_of=witness.composed_of,
            precomposed_with=precomposition.witness,
        ),
        physical_family_description=precomposition.source_family_description,
        reachable_set_statement=precomposition.reachable_set_statement,
        precomposition=precomposition,
    )


@dataclass(frozen=True)
class CompanionMode:
    """The context a builder is called in to form a reference companion.

    ``reductions/req:reference-companion`` (i): the companion is the SAME
    construction run on the handed reference, with no normalizer and no
    lattice condition. A builder called with a context that carries this mode
    builds its instance as it always does; the context's
    :meth:`BuildContext.normalize` then applies NO normalizer (the datum the
    builder formed is the datum, or :attr:`override` where the caller supplies
    the datum recentred by ``foundations/lem:recentred-enclosure``).

    :attr:`captured` receives every datum the builder formed, in call order:
    the companion's construction reads the datum the instance's own rule (I1)
    formed from the reference, which no other field of the instance carries
    before the normalizer. It is the one mutable member of a frozen record and
    is read by :mod:`certiqs_key.reductions.companion` only.
    """

    override: Mapping[JointOutcome, tuple[Matrix, ...]] | None = None
    captured: list[Mapping[JointOutcome, tuple[Matrix, ...]]] = field(
        default_factory=list, compare=False
    )


@dataclass(frozen=True)
class BuildContext:
    """What the core hands a builder: the declared inputs and its normalizer.

    ``core_ready`` is the core's verdict on the rows a construction depends on
    -- the block structure, the probe weights, the cutoff and the alphabet
    agreements. A builder that receives ``False`` reports its own rows as
    undecided and returns no instance: the core refuses on the row that
    actually failed, and a construction on disagreeing alphabets is never
    attempted.
    """

    request: ReductionCall
    lattice_exponent: int | None
    route: Route | None
    classes: tuple[JointClass, ...]
    core_ready: bool
    #: Set exactly where the builder is called to form the reference companion
    #: (:class:`CompanionMode`); ``None`` on every emission of an artefact.
    companion: CompanionMode | None = None

    def normalize(
        self,
        data: Mapping[JointOutcome, tuple[Matrix, ...]],
        sector_dimensions: Sequence[int],
        supports: Sequence[frozenset[JointOutcome] | None] | None = None,
    ) -> Normalization:
        """Run ``def:emitnorm`` on the instance's data sectors.

        THE NORMALIZER IS THE CORE'S AND IS REACHED ONLY THROUGH HERE, so that
        no submodule carries a second reading of ``def:emitnorm`` and the
        emission record of every instance is produced by one function.

        ``supports`` is ``V^(s)`` per data sector
        (``def:reduction-instance`` (I1)), which every builder passes from its
        own sector set (:attr:`SectorSet.data_supports`); ``None`` is the
        default support ``V``. The steps act on ``V_t n V^(s)``, so an element
        outside the sector support is never rounded or a host.

        IN COMPANION MODE NO NORMALIZER IS APPLIED (``reductions/
        req:reference-companion`` (i)): the datum is returned as the builder
        formed it, or as the mode's override, with no per-sector record, and
        is captured for the companion's construction.
        """
        if self.companion is not None:
            datum = dict(
                data if self.companion.override is None else self.companion.override
            )
            self.companion.captured.append(datum)
            return Normalization(family=datum, blocks=())
        if self.lattice_exponent is None:
            raise MalformedInputError(
                "the lattice row refused, so there is no declared kappa and "
                "def:emitnorm has no lattice to round onto; a builder decides "
                "its rows and returns no instance in that case"
            )
        return normalize(
            data,
            classes=self.classes,
            sector_dimensions=sector_dimensions,
            kappa=self.lattice_exponent,
            supports=supports,
        )


@dataclass(frozen=True)
class BuildOutcome:
    """What a builder returns: the rows it owns, their outcomes, the instance.

    ``rows`` is declared WHETHER OR NOT an instance was built, because the
    verification report carries every row of the reduction with its outcome and
    a row that could not be decided must say so rather than be absent.
    """

    rows: tuple[FailClosedRow, ...]
    outcomes: tuple[RuleOutcome, ...]
    instance: ReductionInstance | None


class InstanceBuilder(Protocol):
    """The one method the core calls. See the module docstring.

    A builder decides the rows it owns, constructs its datum, normalises it
    through :meth:`BuildContext.normalize`, assembles its target and returns
    the instance. It never decides a core row and never emits an artifact.
    """

    def build(self, context: BuildContext) -> BuildOutcome:
        """Return the rows this builder owns, their outcomes, and the instance."""
        ...


@dataclass(frozen=True)
class Branch:
    """One branch of a register-conditioned instance, before it is relabelled.

    ``cor:register-instance``: ``B = B_0 D``, ``{N_j}`` a POVM on ``D``,
    ``M_v = sum_j M_{v|j} (x) N_j``. Each branch contributes ITS OWN SECTORS to
    the combined target, relabelled under the branch's name, and the combined
    sector set is ``bigsqcup_j {j} x SecSet_j``.

    ``data`` is ``None`` for a branch with no data sector at all -- which is
    what an UNCHARACTERISED branch is: ``cor:flag-instance`` gives it scalar
    sectors only, because Lemma ``lem:top`` squashes any POVM to a flag PVM
    with no hypothesis, and nothing about that branch is presented as a matrix.

    A branch's sector keeps its declared SUPPORT through the relabelling: the
    support is a subset of ``V`` and the register conditioning renames sectors,
    not outcomes (``def:reduction-instance`` (I1)).
    """

    label: Label
    sectors: SectorSet
    data: Mapping[JointOutcome, tuple[Matrix, ...]] | None
    scalar_values: ScalarValues


def combine_branches(
    branches: Sequence[Branch],
) -> tuple[SectorSet, dict[tuple[Label, str], Mapping[JointOutcome, Fraction]]]:
    """Return the sector set and the scalar values of ``cor:register-instance``.

    ``bigsqcup_j {j} x SecSet_j``, in the declared order of the branches and,
    within a branch, in that branch's own declared order. A branch's sector
    keeps its NAME and takes the branch's label as its GROUP, so a relabelling
    is all that the register conditioning does to the sector set -- which is
    what "the register bookkeeping" means when the flat instance and its
    one-branch register lift are compared.

    Nothing is decided here. Whether the combined family is a POVM is
    ``def:reduction-instance``'s consequence, decided on the numbers about to
    be emitted by the emitted-family row.
    """
    if not branches:
        raise MalformedInputError("a register instance has at least one branch")
    sectors: list[Sector] = []
    scalars: dict[tuple[Label, str], Mapping[JointOutcome, Fraction]] = {}
    for branch in branches:
        for sector in branch.sectors.sectors:
            label = (branch.label, sector.label[1])
            sectors.append(
                Sector(
                    label=label,
                    dimension=sector.dimension,
                    kind=sector.kind,
                    support=sector.support,
                )
            )
            if sector.kind is SectorKind.SCALAR:
                scalars[label] = branch.scalar_values[sector.label]
    return SectorSet(tuple(sectors)), scalars
