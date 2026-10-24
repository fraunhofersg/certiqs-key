"""The sixteen declared inputs of the inputs table, as this module's own types.

THIS MODULE OWNS ITS INPUT SERIALIZATION (ADR-0007), and that is why the
receiver-artifact rows are typed HERE and not imported from anywhere. Section
2.1 groups the sixteen machine keys as ``7 + 5 + 4``: what the receiver artifact
supplies, what the protocol declaration supplies, and what the reduction request
declares. The three groups are three records below, key for key, in the
contract's own order.

WHAT IS NOT IMPORTED, AND WHY
=============================
No type of ``certiqs_key.receiver`` and none of the protocol compiler appears
here; what this file does import is :mod:`certiqs_key.foundations.exact`, the
substrate at the floor every module may reach. PRINCIPLES.md section 4 lets
imports point downward only, and a module's own package is the one place its
input serialization may live. :class:`ReceiverArtifactRows` is therefore this
module's reading of the
seven rows the inputs table quotes from a ``ReceiverMeasurementArtifact`` -- not the
supplier's type and not a copy of it. Its ``mathematical_spec_version`` is
checked against the accepted-version set the caller supplies, which is part of
the conforming behaviour for Assumption A-RECV: "test that the version
resolves to an accepted one, carry into the emitted ledger EVERY KEY OF THE
SUPPLIED LEDGER ... and NAME the artifact by version in the licence record"
(``interface.yaml``, the ``receiver_artifact`` input row,
``what_this_module_may_never_decide``). NOTHING HERE DECIDES A-RECV, whose
``verification`` field is ``never`` (spec/claim-format.md section 3.2).

WHAT A BRANCHING SUBMODULE HOLDS
================================
A branching model, its mode labels and the declaration field that carries it
are NOT here. They are that submodule's declaration and live in its package,
because deleting a removable submodule must leave this package importable and
every remaining test green. A branching request WRAPS a core one: the
submodule's entry takes the :class:`ReductionCall` below and the model beside
it.

THE ALPHABET COLLISION, RESOLVED BY THE CONTRACT AND NOT RE-RESOLVED HERE
=========================================================================
``receiver-povm`` 0.1.3 calls ITS emitted coarse alphabet ``V`` and writes ``F_v`` for
the coarse-grained PHYSICAL POVM indexed by it. Definition ``def:joint-family`` states
the identification: "This contract writes ``M_{y|t}`` FOR THAT SAME OBJECT ... and
RESERVES ``F_v`` FOR THE SQUASHED TARGET." So the supplier's emitted alphabet IS this
module's ``Y``, its per-setting families ARE this module's ``{M_{y|t}}``, and this
module's ``V`` is the JOINT alphabet ``Y x T``. The field on
:class:`ReceiverArtifactRows` is therefore named ``detection_alphabet`` and never ``V``,
and :data:`JointOutcome` is a pair.

OPEN IMPLEMENTATION CHOICE 3 OF 12 IS DECIDED HERE: THE SOURCE DESCRIPTOR
=========================================================================
The outputs table fixes the CONTENT of ``source_descriptor`` -- "the channel Fock
space WITH ITS DECLARED PHOTON-NUMBER GRADING", with a branching model's
register and its POVM ``{N_b}`` where there is one -- and no wire form.
``H(C) = (+)_{m>=0} H(C_m)`` is infinite-dimensional, which Definition
``def:system-setting`` permits exactly here and nowhere else, so a finite
dimension cannot carry it.

THE DECISION: :class:`ChannelGrading` carries the sequence of block dimensions
``dim H(C_m)`` for ``0 <= m <= N`` and the explicit flag ``above_cutoff_finite``,
which is ``False`` for a Fock space. NO SINGLE DIMENSION IS EMITTED for the
channel system, and no code path of this module computes one: the target
``H(Q)`` is finite and its dimension is the sum of the instance's declared
sector dimensions (``def:reduction-instance`` (I2)), while the source system is
described by its grading. A branch
register carries a finite dimension because ``{N_b}`` is a POVM on it and is
declared as matrices.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.exact import Matrix
from certiqs_key.foundations.recentring import EntrywiseEnclosure
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.provenance import ReceiverProvenance
from certiqs_key.reductions.reasons import (
    CertificateKind,
    LinkKind,
    LinkStage,
    Relation,
    SourceMode,
)

__all__ = [
    "OFF_SETTING",
    "PHOTON_BLOCK_FORMS",
    "BoundQuantifierDomain",
    "CarriedOperatorRequest",
    "ChannelGrading",
    "ClickPattern",
    "CoarseGraining",
    "ConstraintForm",
    "DarkCountChannel",
    "HandedReference",
    "HighPhotonBound",
    "InheritedAssumption",
    "InstanceSnapBlock",
    "InstanceSnapRecord",
    "JointOutcome",
    "Label",
    "LinkDeclaration",
    "ProbeDeclaration",
    "ProtocolDeclaration",
    "ReceiverArtifactRows",
    "ReductionCall",
    "ReductionRequest",
    "canonical_coarse_graining",
    "outcome_label",
    "patterns",
    "probe_settings_of",
    "product_form_dark_counts",
]

#: A letter of an alphabet -- of ``Y``, of ``T``, of ``Blmode``, of a sector.
Label = str

#: An element of ``V = Y x T``. A COMMA denotes a joint outcome (the conventions block,
#: ``povm_index_convention``), and the pair is written in that order.
JointOutcome = tuple[Label, Label]

#: The probe-off setting of Definition ``receiver/def:probe``, "whose state is
#: vacuum", which every probe declaration carries. The receiver's
#: ``certiqs_key.receiver.settings.OFF_SETTING`` is the same string; it is NOT
#: imported from there because this package imports no array library (the
#: receiver package loads NumPy), and a unit test keeps the two equal.
OFF_SETTING: Final[Label] = "off"


#: The two input forms of the supplied preserved blocks
#: (``wpfss/def:weight-route``, "the two input forms"; the ``wpfss`` input
#: ``photon_blocks_form``): ``bare``, before the dark-count channel, so that
#: step 1 acts on them, and ``dark_composed``, a declared complete family the
#: model takes below the cutoff after the dark counts, to which step 1 is not
#: applied (``wpfss/prop:precomposed-blocks``).
PHOTON_BLOCK_FORMS: Final[tuple[str, ...]] = ("bare", "dark_composed")


def probe_settings_of(alphabet: Iterable[JointOutcome]) -> tuple[Label, ...]:
    """Return ``T`` read off a declared ``V = Y x T``, in first-appearance order.

    The flag basis every artefact carries IS the declared ``V`` (the
    ``wpfss_data`` output row), validated as exactly the product set, so its
    second projection is exactly the declared ``T``. A reader holding an
    artefact but not its request reads the settings here rather than from a
    second carrier that could disagree.
    """
    return tuple(dict.fromkeys(setting for _, setting in alphabet))


def outcome_label(outcome: JointOutcome, settings: Sequence[Label]) -> str:
    """Return a joint outcome ``(y, t)`` as the ONE flat label every wire indexes by.

    THE ONLY JOIN OF A JOINT OUTCOME IN THE TREE. The docking, the emitted
    machine record, the flag sectors and the factor families all spell ``V``
    through this function, so a reader moving between them sees one spelling.

    ``y,t`` in general, and ``y`` alone when the declared settings are exactly
    ``{off}`` (:data:`OFF_SETTING`). The probe setting of Definition
    ``receiver/def:probe`` is an ADD-ON: a receiver
    without a probe declares ``T = {off}``, where ``V = Y x {off}`` is ``Y``
    relabelled and the component carries no information, so writing it into
    every label would make the countermeasure look present where it is not.
    The join stays injective: at ``T = {off}`` the ``y`` are the distinct
    letters of ``Y``. It is a SPELLING and not a structure -- ``V = Y x T`` and
    every number indexed by it are unchanged.

    Raises:
        MalformedInputError: if ``outcome``'s setting is not one of
            ``settings``, which would spell a label outside the declared ``V``.
    """
    detection, setting = outcome
    if setting not in settings:
        raise MalformedInputError(
            f"the joint outcome {outcome!r} carries the setting {setting!r}, "
            f"which is not one of the declared settings {list(settings)!r}"
        )
    if tuple(settings) == (OFF_SETTING,):
        return detection
    return f"{detection},{setting}"


#: A raw click pattern ``S`` in ``2^[K]``, as the set of ports that fired.
ClickPattern = frozenset[int]


def patterns(ports: int) -> tuple[ClickPattern, ...]:
    """Return ``2^[K]`` in a canonical order: by size, then lexicographically.

    The order is bookkeeping only. Nothing the contract states depends on the
    order in which raw patterns are enumerated -- ``cg`` is a total map on the
    set, the descent property of Lemma ``lem:descent`` quantifies over columns,
    and every emitted object is indexed by ``Y`` or by ``V``. A canonical order
    exists so that a refusal names the same pattern twice.
    """
    if ports < 0:
        raise MalformedInputError("the number of ports is non-negative")
    out: list[ClickPattern] = []
    for size in range(ports + 1):
        for mask in range(1 << ports):
            members = frozenset(k + 1 for k in range(ports) if mask & (1 << k))
            if len(members) == size:
                out.append(members)
    return tuple(out)


@dataclass(frozen=True)
class DarkCountChannel:
    """``R``, column-stochastic on ``2^[K]``, with the monotonicity it declares.

    Section ``sec:inputs``: "EXACTLY column-stochastic --- ``R_{S|S'} >= 0`` for
    every entry and ``sum_S R_{S|S'} = 1`` for every column --- and MONOTONE on
    ``2^[K]`` (``R_{S|S'} > 0 => S' subset S``)". Nothing is asserted here; this
    record is the declaration.

    EACH OF THE TWO TYPE CONDITIONS HAS ITS OWN ROW. The contract, verbatim:
    "EACH OF THE TWO IS DECIDED BY ITS OWN ROW OF [``sec:failclosed``], under
    ``dark_counts_not_column_stochastic`` and ``dark_counts_do_not_descend``
    RESPECTIVELY, and NEITHER IS DECIDED WITHIN ANYTHING (Remark
    ``rem:exactboundary``)." So
    :func:`~certiqs_key.reductions.validation.rule_column_stochastic` decides
    column-stochasticity on THIS matrix;
    :func:`~certiqs_key.reductions.validation.rule_descent` decides monotonicity and
    that ``R`` descends through ``cg``; and the absorbing condition
    Eq. ``eq:absorbing`` is decided by its own row on the DESCENDED matrix under
    ``bounded_letter_not_absorbing``.

    WHAT HAVING THE ROW MEANS. The boundary remark's statement that "a
    declaration whose scalar data is only approximately valid --- A DARK-COUNT
    MATRIX WHOSE COLUMNS SUM TO 1 ONLY TO WITHIN A ROUNDING ERROR, say --- IS
    STILL REFUSED" ends "NOW BY THE COLUMN-STOCHASTICITY ROW AND UNDER ITS OWN
    REASON STRING" (``rem:exactboundary``). Where a violation moves an emitted
    number the refusal can also arrive under another row --
    ``total_weight_not_below_one`` where some ``r_min,i`` reaches one -- and the
    residue outside it would "MEET NO ROW AT ALL" without this one. Remark
    ``rem:colstoch``'s own summary is that "what is closed here is COVERAGE AND
    ATTRIBUTION, NOT SOUNDNESS", every result of the contract having been proved
    for an exactly column-stochastic ``R`` and asserting nothing about a
    declaration that is not one.

    ``entries`` maps ``(S, S')`` to ``R_{S|S'}``; AN ABSENT PAIR IS ZERO, which
    is this record's declared convention and not a default substituted for a
    missing datum. Both halves of the row are therefore quantified over the
    whole index set ``2^[K]`` rather than over the keys present: a column that
    declares nothing sums to ``0``, not to ``1``, and is refused.
    """

    ports: int
    entries: Mapping[tuple[ClickPattern, ClickPattern], Fraction]

    def value(self, row: ClickPattern, column: ClickPattern) -> Fraction:
        """Return ``R_{row|column}``, zero where the declaration is silent."""
        return self.entries.get((row, column), Fraction(0))


def product_form_dark_counts(
    ports: int, probabilities: Mapping[int, Fraction]
) -> DarkCountChannel:
    r"""Return the independent per-port dark-count channel.

    ``R_{S|S'} = 0`` unless ``S' subset S``, and otherwise
    ``prod_{k in S \\ S'} p_k * prod_{k not in S} (1 - p_k)``: port ``k`` in
    ``S \\ S'`` fired spuriously, port ``k`` outside ``S`` stayed silent, and a
    port in ``S'`` fired for real. This is the "independent per-port product
    form" the receiver contract's ``dark_count_channel`` row admits and the one
    Remark ``rem:absorbneeded`` and Remark ``rem:descentneedsconstant`` are
    stated on. The general declared column-stochastic monotone matrix is the
    other admissible form and is built with :class:`DarkCountChannel` directly.
    """
    for port, probability in probabilities.items():
        if not 1 <= port <= ports:
            raise MalformedInputError(f"port {port} is outside 1..{ports}")
        if not 0 <= probability <= 1:
            raise MalformedInputError(
                f"a dark-count probability lies in [0, 1]; port {port} has "
                f"{probability}"
            )
    entries: dict[tuple[ClickPattern, ClickPattern], Fraction] = {}
    all_patterns = patterns(ports)
    for column in all_patterns:
        for row in all_patterns:
            if not column <= row:
                continue
            value = Fraction(1)
            for port in range(1, ports + 1):
                probability = probabilities.get(port, Fraction(0))
                if port in row and port not in column:
                    value *= probability
                elif port not in row:
                    value *= 1 - probability
            if value != 0:
                entries[(row, column)] = value
    return DarkCountChannel(ports=ports, entries=entries)


@dataclass(frozen=True)
class CoarseGraining:
    """``cg``, a TOTAL map ``2^[K] -> Y``, surjective onto the declared ``Y``.

    The inputs table types it exactly so and adds the fibre condition each bounded set
    must satisfy. ``letters`` is the DECLARED ORDER of ``Y``, which the conventions
    block ``subsystem_order`` says the flag basis inherits and which the fail-closed
    table's ``alphabet_or_order_mismatch`` row compares across artifacts.
    """

    ports: int
    letters: tuple[Label, ...]
    assignment: Mapping[ClickPattern, Label]

    def fibre(self, letter: Label) -> frozenset[ClickPattern]:
        """Return ``cg^{-1}(letter)``."""
        return frozenset(
            pattern for pattern, image in self.assignment.items() if image == letter
        )

    def image(self, pattern: ClickPattern) -> Label:
        """Return ``cg(pattern)``, refusing a pattern the map does not cover."""
        try:
            return self.assignment[pattern]
        except KeyError as exc:  # pragma: no cover - guarded by validation
            raise MalformedInputError(
                f"the coarse-graining is not total: {sorted(pattern)} is unmapped"
            ) from exc


def canonical_coarse_graining(
    ports: int,
    *,
    empty_letter: Label,
    single_letters: Mapping[int, Label],
    multiclick_letter: Label,
) -> CoarseGraining:
    r"""Return the canonical declaration of Eq. ``eq:canonicalcg``.

    ``cg`` injective on ``2^[K] \\ MC``, CONSTANT on ``MC = {S : |S| >= 2}``,
    and ``cg^{-1}(y_mc) = MC``. Lemma ``lem:descent`` proves that a monotone
    ``R`` descends through it; the fail-closed table nonetheless requires descent to be
    "TESTED DIRECTLY, NOT VIA THE SHORTCUT Eq. ``eq:canonicalcg``", and
    :mod:`certiqs_key.reductions.wpfss.weights` tests it directly whatever built the
    map. This constructor is a convenience for a caller declaring the canonical
    threshold-detector coarse-graining; it confers no exemption.
    """
    assignment: dict[ClickPattern, Label] = {}
    for pattern in patterns(ports):
        if len(pattern) == 0:
            assignment[pattern] = empty_letter
        elif len(pattern) == 1:
            port = next(iter(pattern))
            if port not in single_letters:
                raise MalformedInputError(f"no letter declared for port {port}")
            assignment[pattern] = single_letters[port]
        else:
            assignment[pattern] = multiclick_letter
    ordered: list[Label] = [empty_letter]
    ordered.extend(single_letters[port] for port in sorted(single_letters))
    if ports >= 2:
        ordered.append(multiclick_letter)
    return CoarseGraining(ports=ports, letters=tuple(ordered), assignment=assignment)


@dataclass(frozen=True)
class HighPhotonBound:
    """One entry ``(O_i, (p_i^(t))_{t in T})`` of the supplier's strengthening slot.

    THE PER-SETTING FORM THE SUPPLIER STATES: a raw outcome set ``O_i subset 2^[K]`` and
    ONE WEIGHT PER SETTING ``t`` in ``T`` -- the same ``T`` as the supplied
    ``photon_blocks`` and the class weights ``q_t`` -- with ``sum_{S in O_i} blk
    M^{>N}_{S|t} >= p_i^(t) 1`` at that setting (receiver ``thm:emitted-bound`` Eq.
    ``eq:pmcsetting``, ``def:slot``; ``wpfss/def:weight-route``). The weight
    route forms the weight of the joint outcome ``(y_i, t)`` from ``p_i^(t)``,
    the weight of ITS OWN SETTING (``wpfss/rem:minweight``), and this module
    takes no minimum of its own.

    ``per_setting`` is ``((t, p_i^(t)), ...)`` in the order the supplier gives
    it. THE RECORD DECIDES NOTHING about it: that the slot comes from a
    receiver version that states the per-setting weights (an artifact of an
    earlier version is refused whatever its weights, a probe-free and
    setting-uniform one included), that its settings are exactly ``T``, that
    every weight is non-negative, and that the weights sum to at most one at
    every setting, are the ``high_photon_slot`` row's (``wpfss`` interface;
    refusal ``high_photon_slot_ill_formed``), and a record that fails one of
    them is carried to that row rather than refused on construction.

    THE ``t``-UNIFORM FORM IS THE SPECIAL CASE, AND :meth:`uniform` SPELLS IT:
    one weight at every setting, which is the form every one-setting slot
    has -- and on it the
    per-setting route gives exactly the numbers the ``t``-uniform route gave
    (``wpfss/rem:minweight``, last paragraph).
    """

    outcome_set: frozenset[ClickPattern]
    per_setting: tuple[tuple[Label, Fraction], ...]

    @classmethod
    def uniform(
        cls,
        outcome_set: frozenset[ClickPattern],
        weight: Fraction,
        settings: Sequence[Label],
    ) -> HighPhotonBound:
        """Return the entry with the ONE weight ``p_i`` at every setting of ``T``.

        receiver ``def:slot``: "At a one-setting family ... an entry has the
        single weight ``p^(off)_i = p_i`` and is written ``(O_i, p_i)``"; and
        ``wpfss/prop:route``: a slot "whose weights do not depend on the
        setting ... the ``t``-uniform form, which every one-setting slot has".
        """
        return cls(
            outcome_set=outcome_set,
            per_setting=tuple((setting, weight) for setting in settings),
        )

    @property
    def settings(self) -> tuple[Label, ...]:
        """Return the settings the entry carries a weight at, in its own order."""
        return tuple(setting for setting, _ in self.per_setting)

    @property
    def weights(self) -> tuple[Fraction, ...]:
        """Return the per-setting weights, in the entry's own order."""
        return tuple(weight for _, weight in self.per_setting)

    def weight_at(self, setting: Label) -> Fraction:
        """Return ``p_i^(t)`` at ``setting``.

        Raises:
            MalformedInputError: if the entry carries no weight at ``setting``,
                which the slot row refuses before any weight is read.
        """
        for candidate, weight in self.per_setting:
            if candidate == setting:
                return weight
        raise MalformedInputError(
            f"the slot entry carries no weight at the setting {setting!r}; its "
            f"settings are {list(self.settings)!r} (the high_photon_slot row "
            "refuses a slot whose settings are not exactly T)"
        )

    @property
    def uniform_weight(self) -> Fraction:
        """Return the entry's UNIFORM WEIGHT ``p_i = min_t p_i^(t)`` (``def:slot``)."""
        if not self.per_setting:
            raise MalformedInputError("a slot entry carries at least one weight")
        return min(self.weights)

    @property
    def is_setting_uniform(self) -> bool:
        """Whether the entry carries one weight at every setting (``t``-uniform)."""
        return len(set(self.weights)) <= 1


@dataclass(frozen=True)
class BoundQuantifierDomain:
    """The literal statement "for all ``m > N`` and all ``t in T``".

    ``cutoff`` is the ``N`` the receiver artifact ECHOES. The inputs table: "The
    ``N`` echoed here must equal ``photon_cutoff``; A MISMATCH IS REFUSED."
    """

    cutoff: int
    settings: tuple[Label, ...]


@dataclass(frozen=True)
class ChannelGrading:
    """``H(C) = (+)_{m>=0} H(C_m)`` with its DECLARED photon-number grading.

    Open implementation choice 3 of 10 is decided here; see the module
    docstring. ``block_dimensions[m]`` is ``dim H(C_m)`` for ``0 <= m <= N``,
    in increasing ``m`` -- which is the order the conventions block ``subsystem_order``
    fixes for the preserved blocks. ``above_cutoff_finite`` records whether
    ``H(C_{>N})`` is finite-dimensional; a Fock space declares ``False``, and
    NO DIMENSION IS CARRIED FOR IT. Definition ``def:system-setting`` permits
    exactly that: only the target and the side registers are finite-dimensional.
    """

    block_dimensions: tuple[int, ...]
    above_cutoff_finite: bool = False

    @property
    def preserved_dimension(self) -> int:
        """Return ``sum_{m <= N} dim H(C_m)``, the preserved block's dimension."""
        return sum(self.block_dimensions)

    @property
    def cutoff(self) -> int:
        """Return ``N``, read off the number of declared blocks."""
        return len(self.block_dimensions) - 1


@dataclass(frozen=True)
class InheritedAssumption:
    """One row of the SUPPLIER's assumption ledger, transported as it stands.

    Assumption A-RECV at 1.0.0: "THE INHERITED ASSUMPTIONS ARE NAMED BY THE
    SUPPLIER'S OWN MACHINE KEYS ... and the emitted ``assumption_ledger``
    carries them AS KEYS RATHER THAN AS PROSE." Every row is carried onto the
    A-RECV entry as it stands and in the supplier's order; this module holds
    no list of the keys. Which of them an artifact must carry is the
    receiver's own presence rule, read by
    :func:`~certiqs_key.reductions.validation.required_receiver_keys`, under
    which every row is on every artifact.

    ``constrains`` is the supplier's own declared record for that key, carried
    unread. It exists because ONE of the inherited keys has content this contract
    names: A-RECV says of the supplier's ``exact_window_eigenvalue_slack`` that
    "its declared slack ``eps_eig`` is physics rather than arithmetic ... IT IS
    RECORDED IN THE EMITTED LEDGER BESIDE THE SETTINGS AT WHICH THE SUPPLIER
    SAYS IT WAS INVOKED". Nothing here reads, checks or re-derives any of it:
    "this module can NEITHER VERIFY NOR IMPROVE IT".
    """

    machine_key: str
    constrains: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class InstanceSnapBlock:
    """One block of the declaring party's snap of the receiver blocks.

    Read from the party's record of its snap (``foundations/req:who-snaps``)
    for one thing: naming its MOVED blocks in the A-SNAP row of the emitted
    ledger (``thm:emit`` (vi); ``foundations/req:snap-reference`` (iii)),
    with whether the reference is handed beside the snap on the block, the
    cause the party records where none is handed, and the flag
    ``support_not_preserved`` of a block snapped by the last resort. Which of
    them rest on the assumption is the run's decision after its search; this
    module names them provisionally and decides nothing about them.
    """

    #: The photon-number block ``m``, the index of the flat instance's data
    #: sector ``(m)``.
    block: int
    #: The probe setting ``t`` the snap was made at; ``None`` where the snap
    #: was not made per setting.
    setting: Label | None
    #: The party's per-block status: ``kept`` or ``moved``
    #: (``foundations/def:snap``).
    status: str
    #: Whether the party hands the reference beside its snap on the block
    #: (``foundations/def:evaluated-off-snap`` (i)).
    handed: bool = False
    #: The cause of ``foundations/req:snap-reference`` (iii)(a) the party
    #: records for a moved block on which it hands no reference.
    cause: str | None = None
    support_not_preserved: bool = False
    #: The kind of the reference the party's snap ran on (``exact`` or
    #: ``none``), where its record names it.
    reference_kind: str | None = None

    def __post_init__(self) -> None:
        """Refuse a record no rule can be read against (types, not values)."""
        if isinstance(self.block, bool) or not isinstance(self.block, int):
            raise MalformedInputError(
                f"instance-snap block {self.block!r} is not a photon number"
            )

    @property
    def moved(self) -> bool:
        """Whether the party's snap moved the block (``foundations/def:snap``)."""
        return self.status == "moved"

    @property
    def name(self) -> str:
        """``m=<m>, t=<setting>``, as the reference companion names a block."""
        return f"m={self.block}, t={self.setting}"

    def as_record(self) -> dict[str, object]:
        """JSON-ready."""
        return {
            "block": self.block,
            "setting": self.setting,
            "status": self.status,
            "handed": self.handed,
            "cause": self.cause,
            "support_not_preserved": self.support_not_preserved,
            "reference_kind": self.reference_kind,
        }


@dataclass(frozen=True)
class InstanceSnapRecord:
    """The declaring party's record of its snap of the receiver blocks.

    Its blocks (:class:`InstanceSnapBlock`), one per photon-number block and
    probe setting. PRESENT WITH EVERY ARTEFACT WHOSE HANDED DATUM IS FORMED
    FROM BLOCKS A DECLARING PARTY SNAPPED; absent
    (``ReceiverArtifactRows.instance_snap is None``) where none was supplied,
    and then no block of it is named.
    """

    blocks: tuple[InstanceSnapBlock, ...] = ()

    def __post_init__(self) -> None:
        """Refuse a record no rule can be read against (types, not values)."""
        if not all(isinstance(block, InstanceSnapBlock) for block in self.blocks):
            raise MalformedInputError(
                "an instance-snap record carries InstanceSnapBlock records"
            )

    @property
    def moved(self) -> tuple[InstanceSnapBlock, ...]:
        """The moved blocks, in the order the party snapped them."""
        return tuple(block for block in self.blocks if block.moved)

    @classmethod
    def from_snap_records(
        cls, records: Mapping[Label, Mapping[str, object]]
    ) -> InstanceSnapRecord:
        """Read the declaring party's per-setting snap records.

        ``records`` maps each probe setting to the JSON-ready record of one
        measurement-family snap (``foundations/req:who-snaps``; the
        ``as_record()`` of the foundations ``MeasurementSnapRecord``), one
        snap per setting, its blocks labelled ``m=<photon number>``. Nothing
        is decided here: the blocks are read as recorded.
        """
        blocks: list[InstanceSnapBlock] = []
        for setting, record in records.items():
            raw_blocks = record.get("blocks") or ()
            if not isinstance(raw_blocks, (list, tuple)):
                raise MalformedInputError("a snap record's blocks are a list")
            for position, raw in enumerate(raw_blocks):
                if not isinstance(raw, Mapping):
                    raise MalformedInputError("a snap block record is a mapping")
                blocks.append(
                    InstanceSnapBlock(
                        block=_photon_number(raw.get("block"), position),
                        setting=setting,
                        status=str(raw.get("status")),
                        handed=raw.get("handed_reference") is not None,
                        cause=(
                            None if raw.get("cause") is None else str(raw.get("cause"))
                        ),
                        support_not_preserved=bool(raw.get("support_not_preserved")),
                        reference_kind=(
                            None
                            if raw.get("reference_kind") is None
                            else str(raw.get("reference_kind"))
                        ),
                    )
                )
        return cls(blocks=tuple(blocks))

    def as_record(self) -> dict[str, object]:
        """JSON-ready, as the declaring party records it."""
        return {"blocks": [block.as_record() for block in self.blocks]}


def _photon_number(label: object, position: int) -> int:
    """Return ``m`` from a foundations block label ``m=<m>``, else the position."""
    if isinstance(label, int) and not isinstance(label, bool):
        return label
    if isinstance(label, str):
        tail = label.rsplit("=", 1)[-1].strip()
        if tail.isdigit():
            return int(tail)
    return position


@dataclass(frozen=True)
class HandedReference:
    """The reference a declaring instance hands beside its snap of the blocks.

    ``foundations/def:evaluated-off-snap`` (i): with the snapped family the
    declarer passes, altered by no step, the centre (entries of ``Q(i)``) and
    the radii (rationals) of an entrywise enclosure of every element of every
    HANDED block, with the identity of the reference and the claims that
    establish it. ``blocks`` is keyed as ``photon_blocks`` is, ``(y, t)`` to the
    tuple over ``m`` in increasing order, and holds ``None`` on a block that is
    not handed (the snapped block then stands there). ``identity`` is, per
    probe setting, the reference's identity record
    (``foundations/reference.ReferenceIdentity.as_record``). This module
    decides nothing of it beyond reading it
    (``reductions/interface.yaml``, ``handed_reference``).
    """

    blocks: Mapping[JointOutcome, tuple[EntrywiseEnclosure | None, ...]]
    identity: Mapping[Label, Mapping[str, object]] = field(default_factory=dict)

    @property
    def handed(self) -> bool:
        """Whether at least one block is handed."""
        return any(
            enclosure is not None
            for row in self.blocks.values()
            for enclosure in row
        )


@dataclass(frozen=True)
class ReceiverArtifactRows:
    """Group 1 of the inputs table: the SEVEN rows the receiver artifact supplies.

    Every field is REFERENCED, TRANSPORTED AND NEVER RE-DERIVED (the outputs table's
    closing paragraph). In particular ``high_photon_bounds`` carries the
    supplier's per-setting weights unchanged (one per entry and setting,
    :class:`HighPhotonBound`) and ``photon_blocks`` the bare pre-dark-count
    blocks; nothing here recomputes either.

    ``photon_blocks`` maps ``(y, t)`` to the tuple ``(blk M^{=0}_{y|t}, ...,
    blk M^{=N}_{y|t})`` in increasing ``m``. THE SUPPLIER EMITS NO ABOVE-CUTOFF
    BLOCK AT ALL, which the outputs table states twice and which is why the emitted
    ``squashing_channel`` is a symbolic constructor record: neither
    ``Lambda^WP`` nor ``Lambda^FSS`` can be materialised from an artifact.

    ``validation_results_present`` mirrors the supplier's own
    ``validation_results`` key, and the receiver-spec row is what reads it: two
    of spec/architecture.md 5.4's conditions -- a noncontractive receiver
    instrument and a doubly applied efficiency -- are discharged UPSTREAM and
    are re-checked here ONLY AS CONSISTENCY, and THIS MODULE REFUSES AN
    ARTIFACT THAT DOES NOT CARRY ITS SUPPLIER'S VALIDATION RESULTS. That
    refusal is stated WITHOUT a reason string of its own;
    :mod:`certiqs_key.reductions.validation` decides it inside the
    receiver-spec row rather than inventing a new string.

    ``declared_device_family`` mirrors the supplier's ``calibration_coverage``
    statement that "no characterization data, uncertainty set or device family
    is represented". A non-empty tuple is refused with
    ``device_family_unsupported``: this module reduces ONE declared device.

    NO DEFAULT IN THE ACCEPTING DIRECTION, ON ANY OF THE THREE. Section
    2.5's ``fail_closed`` convention reads "NO DEFAULT IS SUBSTITUTED FOR
    A MISSING DATUM", and a default is worst exactly where it makes a
    refusal unreachable. ``validation_results_present = True`` would have
    let the consistency refusal fire only when a caller volunteered
    the failure; ``declared_device_family = ()`` would have done the same
    to the fail-closed table's ``device_family_unsupported`` row;
    ``occupation_basis_order = ()`` would have silently satisfied the
    basis-order clause of the ``alphabet_or_order_mismatch`` row.

    THE CONTRACT FIXES NO EMPTY VALUE FOR ANY OF THEM. It fixes what a
    CONFORMING supplier emits -- ``receiver-povm`` 0.1.3's
    ``calibration_coverage`` row states that no device family is
    represented, and its ``validation_results`` row emits the four residual
    identities -- but that is the SUPPLIER'S CONFORMANCE, which Assumption
    A-RECV imports and this module never verifies (its ``verification`` field
    is ``never``; ``ass:recv``: "inherited here unverified"). A default here
    would be this module assuming that conformance rather than reading it,
    which is the one thing A-RECV forbids. So all three are stated by the
    caller and the fail-closed table decides them.
    """

    mathematical_spec_version: str
    detection_alphabet: tuple[Label, ...]
    photon_blocks: Mapping[JointOutcome, tuple[Matrix, ...]]
    high_photon_bounds: tuple[HighPhotonBound, ...]
    bound_quantifier_domain: BoundQuantifierDomain
    dark_count_channel: DarkCountChannel
    outcome_coarse_graining: CoarseGraining
    bound_evaluation: str
    channel_grading: ChannelGrading
    #: THESE FOUR CARRY NO DEFAULT, and the field order above is unchanged:
    #: they are declared keyword-only so that requiring them moves no positional
    #: argument. See the class docstring, "no default in the accepting
    #: direction".
    validation_results_present: bool = field(kw_only=True)
    declared_device_family: tuple[str, ...] = field(kw_only=True)
    occupation_basis_order: tuple[tuple[str, ...], ...] = field(kw_only=True)
    #: THE SUPPLIER'S OWN ASSUMPTION LEDGER, CARRYING NO
    #: DEFAULT FOR THE SAME REASON AS THE THREE ABOVE. sec:outputs,
    #: `assumption_ledger`: the emitted ledger carries "for the inherited
    #: receiver assumptions, THE SUPPLIER'S OWN MACHINE KEYS READ FROM THE
    #: RECEIVER ARTIFACT'S LEDGER", entire, every one the receiver's own
    #: presence rules require being present
    #: (:func:`~certiqs_key.reductions.validation.required_receiver_keys`), and
    #: "A KEY THE ARTIFACT DOES NOT CARRY IS A REFUSAL
    #: (`receiver_spec_not_accepted`) RATHER THAN A SILENTLY SHORTENED LIST". An
    #: empty default would make that refusal unreachable in exactly the
    #: accepting direction, and a hardcoded key list would be this module
    #: ASSERTING the supplier's ledger instead of READING it -- the one thing
    #: A-RECV forbids.
    inherited_assumption_ledger: tuple[InheritedAssumption, ...] = field(kw_only=True)
    #: ``wpfss``'s ``photon_blocks_form``: ``bare`` (step 1 of
    #: ``wpfss/def:weight-route`` acts on the blocks) or ``dark_composed``
    #: (the declaring party composed the dark counts before its snap; step 1
    #: is not applied again, ``wpfss/prop:precomposed-blocks``). A value
    #: outside :data:`PHOTON_BLOCK_FORMS` is refused by the block-structure
    #: row. THE DEFAULT ``bare`` IS NAMED: the interface gives the row no
    #: default. The receiver's docking states the form on every rows object
    #: it emits (``dark_composed`` where the instance snaps the dark-composed
    #: family, ``bare`` otherwise), so the default is read only by rows built
    #: by hand, which all supply bare blocks.
    photon_blocks_form: str = field(default="bare", kw_only=True)
    #: The declaring party's record of its snap of these blocks, read to name
    #: its moved blocks in the A-SNAP row (``thm:emit`` (vi)); ``None`` where
    #: none was supplied.
    instance_snap: InstanceSnapRecord | None = field(default=None, kw_only=True)
    #: The reference the declaring party hands beside its snap of these blocks
    #: (``foundations/def:evaluated-off-snap`` (i); the input row
    #: ``handed_reference``), from which the reference companion is formed
    #: (``req:reference-companion``); ``None`` where none is handed.
    handed_reference: HandedReference | None = field(default=None, kw_only=True)
    #: ``wpfss``'s ``factored_loss`` input row: the factored loss ``t`` the
    #: receiver artefact's ``efficiency_record`` carries
    #: (``receiver/detector-imperfections/req:normalization-record``). Where it
    #: is below one the blocks are the NORMALIZED STATION's, and the flat
    #: instance is emitted precomposed with the pure-loss channel of that
    #: transmittance (``wpfss/cor:normalized-flat``,
    #: ``wpfss/req:normalized-link-record``), while an artefact embedding the
    #: flat instance as a branch refuses it
    #: (``wpfss/req:normalized-branch-refusal``). THE DEFAULT ``1`` IS NAMED,
    #: as ``photon_blocks_form``'s is: the receiver's docking states the
    #: factor on every rows object it emits, so the default is read only by
    #: rows built by hand, which supply a receiver's own blocks.
    factored_loss: Fraction = field(default=Fraction(1), kw_only=True)
    #: WHETHER THE ARTIFACT RECORDS THAT ITS DECLARATION HAS A MODEL ADMISSIBLE
    #: EXACTLY: the ``has_exact_model`` of its exact-route record
    #: (``receiver/req:exact-route-decision`` (iv)), which a declaration
    #: admitted only within the receiver tolerances (the fallback
    #: ``port_grams_not_enclosed``) does not have. Read for one decision, the
    #: presence rule of A-RECV (``req:recv-row-provenance`` (iv),
    #: :func:`certiqs_key.reductions.emit.receiver_row_omitted_on_provenance`),
    #: and by nothing that forms a number. THE DEFAULT ``False`` IS THE SAFE
    #: DIRECTION: rows built by hand that do not say keep the row. The
    #: receiver's docking reads it off every artifact it docks.
    exact_model_admissible: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class ProbeDeclaration:
    """``T`` and ``{q_t}``: Bob's own declared randomness (Assumption A-PROBE).

    The inputs table: "finite non-empty, ``q_t > 0``, ``sum_t q_t = 1``". All three
    are validated, and a violation is ``probe_weights_ill_formed``.
    """

    settings: tuple[Label, ...]
    weights: Mapping[Label, Fraction]


@dataclass(frozen=True)
class ProtocolDeclaration:
    """Group 2 of the inputs table: the FIVE rows the protocol declaration supplies.

    ``joint_alphabet`` is the DECLARED ORDER of ``V = Y x T``. THE PHRASE "with ``Y``
    major" ADMITS TWO READINGS -- ``Y`` slowest, or ``y`` running fastest within each
    ``t`` -- and the frozen oracle evidence uses the second; the
    ``subsystem_order`` convention states the second in terms, y fastest and t
    slowest. The reading applied
    here is that THE ORDER IS DECLARED AND VALIDATED, NEVER CONSTRUCTED, so the
    module decides nothing either way. The convention
    (``subsystem_order``) says the flag basis is "in the DECLARED ORDER of
    ``V = Y x T`` with ``Y`` major", and the ``wpfss_data`` output row emits
    "the flag basis IN THE DECLARED ORDER OF ``V``"; the fail-closed rule is
    "alphabets, sector order and basis order AGREE ACROSS ARTIFACTS". SO THE
    ORDER IS A DECLARED DATUM AND IS VALIDATED, NEVER CONSTRUCTED: the module
    checks that ``joint_alphabet`` is exactly the product set ``Y x T``, with no
    letter missing and none repeated, and uses the declared sequence as the flag
    basis. Constructing one would substitute a default for a declared datum,
    which the conventions block's ``fail_closed`` convention forbids in as many words.

    ``source_mode`` carries the MODE and never a state. Definition
    ``def:licensed`` writes the emitted entries as ``(O^_k, bowtie_k, c_k)`` in
    both modes, and Remark ``rem:notlicensed`` (a) is blunt: "Nothing here
    licenses declaring ``tau_A``." Theorem ``thm:licence`` (iv) adds that the
    identification of the right-hand side "is THE DECLARATION'S AND NOT THIS
    CONTRACT'S", so no field of this record holds ``tau_A`` and no code path of
    this module produces one.

    ``party_label`` IS THE OPTIONAL DECLARED PARTY OF THE INSTANCE, one label
    for the whole instance, and ``None`` IS THE DEFAULT AND IS BOB'S. Definition
    ``def:reduction-instance`` (I2): "The default stays
    the default, and it stays Bob's; an instance may in addition be declared
    with ANOTHER PARTY'S LABEL ... every factor of every ``H(Q_s)`` is that
    party's, because the handed model lives on the system THAT party receives."
    It is A DECLARED IDENTIFIER, COMPARED AND NEVER COMPUTED: no rule of this
    module reads its value, no condition of (I1)-(I4) depends on it, and it is
    emitted with the sector map in ``target_descriptor.party_partition``
    (:func:`certiqs_key.reductions.sectors.party_partition_statement`). Where
    several parties measure there is one instance and one artefact PER FACTOR,
    each with its own label (``thm:emitted-product`` (i);
    :mod:`certiqs_key.reductions.factors`).
    """

    probe_declaration: ProbeDeclaration
    detection_alphabet: tuple[Label, ...]
    photon_cutoff: int
    source_mode: SourceMode
    joint_alphabet: tuple[JointOutcome, ...]
    #: The `sector_declaration` input row's ``party_label``: optional, ONE PER
    #: INSTANCE, and Bob's where it is absent -- which is every instance this
    #: repository declares today.
    party_label: Label | None = None


class ConstraintForm(StrEnum):
    """Which of Remark ``rem:unsound``'s two forms a caller is asking for.

    The remark names both and says what this module does with each: "The operator
    form is REFUSED (the fail-closed table), because it is unsound. The expectation form
    is sound but is NOT EMITTED BY DEFAULT either ... The expectation form
    remains AVAILABLE ON REQUEST." A request naming :attr:`OPERATOR` gets
    ``unsound_constraint_requested``; one naming :attr:`EXPECTATION` is
    evaluated against Eq. ``eq:certificate`` like any other entry.
    """

    EXPECTATION = "expectation"
    OPERATOR = "operator"


@dataclass(frozen=True)
class CarriedOperatorRequest:
    """One entry of ``carried_operators``: an operator the caller requests as an entry.

    The inputs table: a requested operator is admitted "ONLY WHERE its
    certificate Lambda^dagger(hat O) [relation] c 1_B is DECIDED FOR THE EMITTED
    NUMBERS" -- by ``cor:entries`` (i) for a default carried operator, (ii) for
    the class-marginal entry, and under (iii) by a DECIDED CERTIFICATE a claim
    stated for the instance gives -- and every other requested operator is
    refused (``req:uncertified-operator-refused``).

    ``operator`` is ``O^_k`` on ``Q``; ``relation`` and ``constant`` are the
    ``bowtie_k`` and ``c_k`` the caller asks for, and
    :func:`certiqs_key.reductions.constraints.certify_carried_operators` DECIDES
    the certificate on the emitted numbers rather than trusting it.
    ``certificate_kind`` records which case of Corollary ``cor:pullback`` the
    caller names; it is no certificate and nothing decides on it: the emitted
    entry carries the case of the decided certificate that admitted it.

    ``constant_is_declared`` is the A-CONST field: "every constant ``c_k`` in an
    emitted entry is FIXED BEFORE THE PROTOCOL RUN by the device fact that
    certifies it, and IS NOT A FUNCTION OF ANY STATISTIC OBSERVED DURING THE
    RUN". A caller that says ``False`` gets ``data_dependent_constant``. The
    field is a declaration and not an inference: no function of the emitted data
    can tell whether a number came from a run, which is exactly why A-CONST is
    an assumption and the refusal is on the declaration.

    ``certified_against`` names the channel witness the caller certified the entry
    against, and the fail-closed table refuses an entry certified against a channel that
    is not its own link's witness (``constraint_channel_mismatch``). Remark
    ``rem:tworoutes`` freezes what goes wrong: the same entry pulls back to ``0`` under
    ``Lambda^FSS`` and to a NEGATIVE operator under ``Lambda^WP``, excluding a state
    reachable under the latter.
    """

    label: str
    operator: Matrix
    relation: Relation
    constant: Fraction
    certificate_kind: CertificateKind
    certified_against: str
    constant_is_declared: bool = True
    form: ConstraintForm = ConstraintForm.EXPECTATION


@dataclass(frozen=True)
class LinkDeclaration:
    """One declared link of ``link_declarations``, before it is built.

    The inputs table types the row as an ordered list, "each with ``stage`` in
    {source, receiver} and ``kind`` in" the nine values. ``requested_status``
    exists so that a request for ``certified_outer`` or ``exploratory_numeric``
    is EXPRESSIBLE and therefore refusable with
    ``approximate_squashing_unsupported``; this module emits ``exact`` only.
    """

    stage: LinkStage
    kind: LinkKind
    requested_status: str = "exact"


@dataclass(frozen=True)
class ReductionRequest:
    """Group 3 of the inputs table: the FIVE rows the reduction request declares.

    1.0.0 **REPLACES** ``operator_tolerance`` by ``lattice_exponent``. That is
    not a rename and ``interface.yaml`` says so in terms: the old row was an
    OPTIONAL, DEFAULTABLE (absent = 0) non-negative scalar carrying the
    caller's assertion about a DISTANCE; the new one is a REQUIRED,
    NON-DEFAULTABLE INTEGER fixing a SET of representable values, and it is
    read by this module's own EMISSION as well as by its admission. The two
    share a group and a position and nothing else. The input key count stays
    at seventeen.

    ``route`` is typed as a plain string and not as
    :class:`~certiqs_key.reductions.reasons.Route` ON PURPOSE. The inputs table refuses
    the value ``both`` with ``route_not_single_valued``, and a value that cannot
    be presented cannot be refused: typing the field as the enum would turn a
    contract refusal into a type error and lose the machine-readable reason.
    The rule resolves the string into a :class:`~certiqs_key.reductions.reasons.Route`
    or into a refusal.

    ``carried_operators`` defaults to the empty tuple and NOT to the default
    set the ``carried_operators`` input row names, which is the INSTANCE'S
    sector projectors (``cor:entries`` (i)). The default set depends on the
    instance, so it is built where the instance is known rather than stored
    here.

    ``requested_assurance`` is REQUIRED and is validated against the two
    values the inputs table's row admits
    (:class:`certiqs_key.foundations.assurance.Assurance`, the platform's ONE tier
    vocabulary -- see
    :func:`certiqs_key.reductions.emit._requested_assurance`). It is READ
    and RECORDED and never becomes a label: design.md says such a request
    "INHERITS the upstream ``bound_evaluation`` and FALLS BACK
    FAIL-CLOSED", and since the upstream value is ``floating_point``
    (``receiver`` Definition ``def:evaluation-model``) the fall-back has already
    happened before this module is reached. What the module does with the
    request is therefore exactly one thing: record it beside the inherited
    ``bound_evaluation`` in the verification report, so that an artifact
    says what was asked for and what backed it. NOTHING IN THIS PACKAGE
    ASSIGNS AN ASSURANCE TIER TO ANYTHING.

    ``squash_before_post_processing`` exists for the same reason as
    ``requested_status``: the fail-closed table refuses "squash requested AFTER
    classical post-processing, NOT BEFORE" with ``post_processing_order_violated``, and
    the request must be able to state the thing that is refused. Remark
    ``rem:intertwining`` is why: a classical map applied before a FIXED squasher may not
    be moved across it, which "asks whether ``P' M = P M`` has a stochastic solution
    ``P'`` -- a linear feasibility problem that has NO SOLUTION IN GENERAL". This
    module never asks it.
    """

    link_declarations: tuple[LinkDeclaration, ...]
    route: str = "encoded"
    carried_operators: tuple[CarriedOperatorRequest, ...] = ()
    #: NO DEFAULT: the inputs table gives this row none and the conventions block's
    #: ``fail_closed`` convention forbids substituting one. Keyword-only, so
    #: that requiring it moves no positional argument. An out-of-enum value is
    #: MALFORMED INPUT and not a refusal -- the fail-closed table names no reason for
    #: one, and inventing a twenty-fifth string would decide in code what the
    #: contract leaves unstated.
    requested_assurance: str = field(kw_only=True)
    squash_before_post_processing: bool = False
    accepted_receiver_versions: tuple[str, ...] = ()
    declared_sector_order: tuple[str, ...] | None = None
    declared_occupation_basis_order: tuple[tuple[str, ...], ...] | None = None
    #: The relations the fail-closed table's obstruction row quantifies over: "EVERY
    #: DECLARED relation passes the necessary conditions of Lemma
    #: ``lem:obstructions``". A relation is declared as the pair of families
    #: ``({M_v}, {F_v})``; the relation this module CONSTRUCTS is a theorem
    #: (an instance's own existence theorem, ``def:reduction-instance`` (I3))
    #: and is not a declaration to refuse, so the row is vacuous when this is
    #: empty.
    declared_relations: tuple[tuple[tuple[Matrix, ...], tuple[Matrix, ...]], ...] = ()
    #: the inputs table's ``lattice_exponent`` row (``kappa``),
    #: **REQUIRED**: "THERE IS NO DEFAULT AND NO FALLBACK"
    #: (spec/architecture.md 2.9, condition (D-LAT)). The one declared exponent of the
    #: dyadic lattice Eq. eq:latinv that every declared AND every emitted
    #: operator entry lies on.
    #:
    #: KEYWORD-ONLY, so that requiring it moves no positional argument -- the
    #: same shape ``requested_assurance`` has for the same reason.
    #:
    #: WHAT IT IS NOT, and it is the sentence most likely to be misread:
    #: "It fixes a SET of representable numbers and DECIDES NO PREDICATE ABOUT
    #: HOW NEAR ONE NUMBER IS TO ANOTHER. IT IS NOT A TOLERANCE, NOTHING IS
    #: ADMITTED OR REFUSED 'WITHIN' kappa, and THIS CONTRACT CARRIES NO
    #: TOLERANCE ROW AT ALL."
    #:
    #: TYPED ``object`` FOR THE SAME REASON ``route`` IS TYPED ``str``: Section
    #: 4.14 refuses a value outside ``1 <= kappa <= 53``, or one that is not an
    #: integer at all, with ``lattice_exponent_not_declared``, and a value that
    #: cannot be PRESENTED cannot be REFUSED. Typing the field as ``int`` would
    #: turn a contract refusal into a type error and lose the machine-readable
    #: reason. The module NEITHER CHOOSES kappa NOR DERIVES IT FROM THE
    #: RECEIVER ARTIFACT: "it is the INSTANCE'S DECLARATION, read here and used
    #: unchanged".
    lattice_exponent: object = field(kw_only=True)
    #: THE STRICT OPTION (``foundations/req:snap-reference`` (iv); the core
    #: input ``strict_snaps``): off by default, and recorded either way. Off,
    #: a moved emission class is DISCLOSED; on, it is refused at emission
    #: where no reference companion is formed (``req:emission-refusal``).
    strict_snaps: bool = field(default=False, kw_only=True)
    #: The run's enclosure setting (``foundations/req:snap-reference`` (i),
    #: run parameter ``reference_enclosure``), default on: echoed in the
    #: emission record, as ``foundations/req:who-snaps`` asks of the record of
    #: every snap, though it does not bear on the normalizer's, whose
    #: reference is always exact (``req:emission-record``).
    reference_enclosure: bool = field(default=True, kw_only=True)


@dataclass(frozen=True)
class ReductionCall:
    """The three groups of declared inputs, as ONE argument.

    The interface groups the declared inputs as ``7 + 5 + 4``: what the receiver
    artifact supplies, what the protocol declaration supplies, and what the
    reduction request declares. The core entry point of this module takes an
    INSTANCE BUILDER beside them
    (:func:`certiqs_key.reductions.emit.reduce`), so the three travel as one
    record and the signature reads ``reduce(request, builder)``.

    This record holds the three objects, in the interface's own order.
    """

    artifact_rows: ReceiverArtifactRows
    declaration: ProtocolDeclaration
    request: ReductionRequest
    #: WHETHER THE CONSUMING SPECIFICATION APPLIES A PUBLIC CHOICE AT THIS
    #: INSTANCE'S MEASURED FACTOR (a choice-weighted physical family or a
    #: ``choice_weighting`` of that factor), which A-TSM's emission rule reads:
    #: "the emission is told whether such a choice is applied; where it is not
    #: told, the row is emitted" (``interface.yaml``). ``None`` is "not told".
    #: Its interface input row is ``public_choice_applied``; it is no member of the
    #: three groups below, and no number reads it.
    public_choice_applied: bool | None = None
    #: THE RUN'S WORD THAT THE RECEIVER ARTIFACT READ IS ONE IT BUILT
    #: (``req:recv-row-provenance`` (i), (iii); the interface's input row
    #: ``receiver_provenance``), passed beside the artifact rows and never
    #: read from them. ``None`` -- every route but the run tier's own
    #: (:func:`certiqs_key.runs.receiver_provenance.attest_receiver_provenance`)
    #: -- keeps the A-RECV row. It decides that row's presence and nothing
    #: else; no number reads it.
    receiver_provenance: ReceiverProvenance | None = None
