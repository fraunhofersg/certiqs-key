"""The target's sectors: data sectors, scalar sectors, and the family they build.

DEFINITION ``def:reduction-instance`` (I2), AS CODE. The target is
``SecSet = SecSet_dat u SecSet_sc`` with declared dimensions and order, and

    ``F_v = (+)_s F^(s)_v``,  ``F^(s)_v = A^(s)_v`` on a data sector and
                             ``phi_s(v) 1_{d_s}`` on a scalar one,

ONE SECTOR BLOCK AT A TIME, AND THE LIST IS WHAT IS CARRIED.
:func:`assemble_sector_blocks` returns ``(F^(s)_v)_s`` per outcome and nothing
else: it decides nothing, it reorders nothing, and it invents no block. The
direct sum is "what that list MEANS, not an object the artifact carries" (the
outputs table, `target_povm`; spec/architecture.md 2.8-2.9), so this module
assembles no ``dim H(Q) x dim H(Q)`` array and offers no function that does
(once a producer writes one sector block at a time there is no off-sector
entry to write and therefore none to verify, so there is no ``assemble_family``
and no off-block zero check; and a CONSTRAINT ENTRY's operator, an operator on
``Q``, is carried as its sector-block list like every other and built from
:meth:`SectorSet.block_projector`).

WHY THE DISTINCTION IS THE ONE THAT MATTERS. A DATA SECTOR carries, per
outcome, a matrix formed from the handed numbers by finitely many exact
operations -- it is what the emission normalizer of ``def:emitnorm`` acts on,
and the only thing it acts on. A SCALAR SECTOR carries one lattice value
``phi_s(v)`` per outcome with ``sum_v phi_s(v) = 1`` exactly, and the
normalizer never reads it: a flag sector's value is declared, not computed from
a receiver block. That is what makes ``def:emitnorm``'s stability clause
checkable -- "the normalizer reads data sectors only".

THIS TYPE IS MODE-FREE: a sector type built from one model's BRANCH MODES
would fix its sectors as that model orders them. A branching submodule builds
its sectors from this type, and so does the flat instance of ``wpfss``;
deleting the one leaves the other whole. ``labels`` and
``dimensions`` are an ordered list of ``(group, name)`` pairs and an ordered list of
dimensions -- because the emitted ``target_descriptor`` and the docking's joined
``"group:name"`` identifiers read them.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.exact import Cx, Matrix, direct_sum, identity, zeros
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import JointOutcome, Label

__all__ = [
    "DEFAULT_PARTY",
    "ScalarValues",
    "Sector",
    "SectorKind",
    "SectorSet",
    "assemble_sector_blocks",
    "declared_party",
    "flag_scalar_values",
    "joined_sector_label",
    "party_partition_statement",
    "scalar_sectors",
    "sector_projector_label",
    "sector_projectors",
]

#: The party of the DEFAULT party partition of ``def:reduction-instance`` (I2):
#: "The default stays the default, and it stays Bob's." Every instance of this
#: module and of its submodules declares no other label today.
DEFAULT_PARTY: Final[Label] = "Bob"

#: Per scalar sector label, the lattice value ``phi_s(v)`` at every outcome.
ScalarValues = Mapping[tuple[Label, str], Mapping[JointOutcome, Fraction]]


class SectorKind(StrEnum):
    """Which of ``def:reduction-instance`` (I2)'s two kinds a sector is."""

    #: Carries a matrix per outcome; the normalizer acts here and nowhere else.
    DATA = "data"
    #: Carries one declared lattice value per outcome; the normalizer never
    #: reads it.
    SCALAR = "scalar"


@dataclass(frozen=True)
class Sector:
    """One sector of the target: its label, its dimension, its kind, its support.

    ``label`` is the ``(group, name)`` pair the emitted ``target_descriptor``
    carries and the docking joins into one identifier. The group names the
    branch or the system the sector belongs to; the name is the photon number
    of a preserved block or the outcome of a flag basis vector.

    ``support`` is ``V^(s)`` of ``def:reduction-instance`` (I1): the declared
    subset of ``V`` a DATA sector's datum may be non-zero on, which must meet
    every class. ``None`` is the DEFAULT support ``V``, at which nothing
    changes. An element at an outcome outside it is OUTSIDE THE SECTOR
    SUPPORT -- "exactly zero, on the lattice, and touched by no step" of
    ``def:emitnorm``, which is why the normalizer takes the supports and why
    such an element is never designated (spec/architecture.md 2.9: "an outcome
    that cannot occur in a photon-number block must come back exactly
    zero").
    """

    label: tuple[Label, str]
    dimension: int
    kind: SectorKind
    support: frozenset[JointOutcome] | None = None


@dataclass(frozen=True)
class SectorSet:
    """``SecSet`` with its declared dimensions and its ORDER.

    The order IS the datum: "sector blocks in the declared total order of
    ``S``", so the projector of the ``i``-th sector is the diagonal 0/1
    operator on the ``i``-th consecutive block, and ``dim H(Q) = sum_s d_s``.
    """

    sectors: tuple[Sector, ...]

    def __post_init__(self) -> None:
        """Refuse an empty set or one whose labels do not enumerate a set."""
        if not self.sectors:
            raise MalformedInputError("a target has at least one sector")
        if len({sector.label for sector in self.sectors}) != len(self.sectors):
            raise MalformedInputError("two sectors carry the same (group, name)")

    @property
    def labels(self) -> tuple[tuple[Label, str], ...]:
        """Return the ``(group, name)`` pairs, in the declared order."""
        return tuple(sector.label for sector in self.sectors)

    @property
    def dimensions(self) -> tuple[int, ...]:
        """Return ``(d_s)_s``, in the declared order."""
        return tuple(sector.dimension for sector in self.sectors)

    @property
    def total_dimension(self) -> int:
        """Return ``dim H(Q)``, the sum of the sector dimensions."""
        return sum(self.dimensions)

    @property
    def data_sectors(self) -> tuple[Sector, ...]:
        """Return the data sectors, in the declared order."""
        return tuple(s for s in self.sectors if s.kind is SectorKind.DATA)

    @property
    def scalar_sectors(self) -> tuple[Sector, ...]:
        """Return the scalar sectors, in the declared order."""
        return tuple(s for s in self.sectors if s.kind is SectorKind.SCALAR)

    @property
    def data_dimensions(self) -> tuple[int, ...]:
        """Return the dimension of each data sector, in the declared order."""
        return tuple(s.dimension for s in self.data_sectors)

    @property
    def data_supports(self) -> tuple[frozenset[JointOutcome] | None, ...]:
        """Return ``V^(s)`` of each data sector, in the declared order.

        ``def:reduction-instance`` (I1). ``None`` is the default support ``V``.
        This is what a builder hands
        :func:`certiqs_key.reductions.normalizer.normalize`, so that the
        designation order and the round-down of ``def:emitnorm`` (2)-(3)
        range over ``V_t n V^(s)`` and never over an element outside the
        sector support.
        """
        return tuple(s.support for s in self.data_sectors)

    def offsets(self) -> tuple[tuple[int, int], ...]:
        """Return ``(start, stop)`` of every sector block, in the declared order."""
        out: list[tuple[int, int]] = []
        offset = 0
        for dim in self.dimensions:
            out.append((offset, offset + dim))
            offset += dim
        return tuple(out)

    def projectors(self) -> tuple[tuple[Matrix, ...], ...]:
        """Return the orthogonal ``{Pi_s}`` of Proposition ``prop:pinching``.

        EACH ONE AS ITS SECTOR-BLOCK LIST, which is the operator type of
        spec/architecture.md 2.9 -- ``1_{d_s}`` on its own block and the zero
        block on every other. A caller that needs the ``d_Q x d_Q`` rendering
        forms the direct sum itself; no emitted object carries one.
        """
        return tuple(
            self.block_projector(start, stop - start) for start, stop in self.offsets()
        )

    def dense_projectors(self) -> tuple[Matrix, ...]:
        """Return ``{Pi_s}`` as ``d_Q x d_Q`` arrays, FOR A WHOLE-SPACE COMPUTATION.

        NOT AN EMITTED FORM AND ON NO EMISSION PATH. Proposition
        ``prop:pinching``'s adjoint is stated on the whole space and a TOY
        instance evaluates it there (``sum_s Pi_s X Pi_s`` on a dense ``X``);
        this is the rendering such a computation reads, exactly as
        :meth:`certiqs_key.foundations.blocks.BlockOperator.dense` is. What an
        instance transports is :meth:`projectors`.
        """
        return tuple(direct_sum(list(blocks)) for blocks in self.projectors())

    def block_projector(self, start: int, length: int) -> tuple[Matrix, ...]:
        """Return the projector onto ``[start, start + length)`` AS A BLOCK LIST.

        The sum of the sector projectors the range covers, in the operator type
        of spec/architecture.md 2.9: ``1_{d_s}`` on every sector inside the
        range and the zero block on every sector outside it. THE RANGE IS A
        UNION OF SECTORS OR IT IS REFUSED -- a range cutting a sector in half
        is not a sum of sector projectors, so it names no operator of this type,
        and a producer asking for one would be constructing ambiently again
        (spec/architecture.md 2.9).
        """
        return tuple(
            identity(dim) if inside else zeros(dim, dim)
            for inside, dim in zip(
                self.sectors_inside(start, length), self.dimensions, strict=True
            )
        )

    def sectors_inside(self, start: int, length: int) -> tuple[bool, ...]:
        """Return, per sector, whether its block lies inside ``[start, start+length)``.

        THE RANGE IS A UNION OF SECTORS OR IT IS REFUSED: a range cutting a
        sector in half describes no sum of sector projectors and no restriction
        to a branch's sectors, and acting on one entrywise is the ambient
        construction spec/architecture.md 2.9 removed. Every range this module
        passes -- a branch, its data part, its scalar part -- is a run of whole
        sectors by construction, so the refusal is a structural check on a
        caller and not a decision on declared data.
        """
        stop = start + length
        out: list[bool] = []
        for block_start, block_stop in self.offsets():
            inside = start <= block_start and block_stop <= stop
            overlaps = block_start < stop and start < block_stop
            if overlaps and not inside:
                raise MalformedInputError(
                    f"the range [{start}, {stop}) cuts the sector block "
                    f"[{block_start}, {block_stop}) in half; a sector-block "
                    "list carries one square block per sector and a range over "
                    "it is a run of whole sectors (spec/architecture.md 2.9)"
                )
            out.append(inside)
        return tuple(out)


def scalar_sectors(
    group: Label, names: Sequence[str], dimension: int = 1
) -> tuple[Sector, ...]:
    """Return one scalar sector per name, in the given order, under one group."""
    return tuple(
        Sector(label=(group, name), dimension=dimension, kind=SectorKind.SCALAR)
        for name in names
    )


def flag_scalar_values(
    group: Label,
    flag_names: Sequence[str],
    order: Sequence[JointOutcome],
) -> dict[tuple[Label, str], dict[JointOutcome, Fraction]]:
    """Return ``phi_f(v) = delta_{vf}``: the flag PVM of ``cor:flag-instance``.

    The instance an UNCHARACTERISED BRANCH gets. Lemma ``lem:top`` squashes any
    POVM to this target with no hypothesis at all, which is why an
    uncharacterised branch -- arbitrary, possibly unknown, possibly chosen by
    the adversary -- needs nothing declared about it before it can contribute
    a sector.

    Each value is ``0`` or ``1`` and ``sum_v phi_f(v) = 1`` exactly, so (I2)'s
    lattice condition holds at every declared ``kappa``.
    """
    if len(flag_names) != len(order):
        raise MalformedInputError(
            "a flag sector per joint outcome is required: the flag basis is in "
            "the declared order of V"
        )
    return {
        (group, name): {
            outcome: Fraction(1) if position == index else Fraction(0)
            for position, outcome in enumerate(order)
        }
        for index, name in enumerate(flag_names)
    }


def assemble_sector_blocks(
    sectors: SectorSet,
    data: Mapping[JointOutcome, tuple[Matrix, ...]],
    scalar_values: ScalarValues,
    order: Sequence[JointOutcome],
) -> dict[JointOutcome, tuple[Matrix, ...]]:
    """Return ``F_v`` as the SECTOR-BLOCK LIST of Eq. ``eq:instance-target``.

    The list before the direct sum, over EVERY sector -- data and scalar -- in
    the declared sector order. It is the presentation ``thm:emit`` (ii) states
    the six (D-EMIT) conditions of: "the family ``{F_v}``, PRESENTED AS THE
    SECTOR-BLOCK LIST eq:instance-target, satisfies the six conditions ... each
    of the six is decided ... PER SECTOR BLOCK". Passing only the data sectors
    would leave a scalar sector's declared values undecided on the numbers
    about to be emitted.
    """
    out: dict[JointOutcome, tuple[Matrix, ...]] = {}
    for outcome in order:
        blocks: list[Matrix] = []
        data_position = 0
        for sector in sectors.sectors:
            if sector.kind is SectorKind.DATA:
                blocks.append(data[outcome][data_position])
                data_position += 1
                continue
            value = scalar_values[sector.label][outcome]
            blocks.append(
                tuple(
                    tuple(
                        Cx(value, Fraction(0))
                        if i == j
                        else Cx(Fraction(0), Fraction(0))
                        for j in range(sector.dimension)
                    )
                    for i in range(sector.dimension)
                )
            )
        out[outcome] = tuple(blocks)
    return out


def declared_party(party_label: Label | None) -> Label:
    """Return the instance's party: the declared label, or Bob where none is.

    ``def:reduction-instance`` (I2): "Where no label is declared the label is
    Bob's." COMPARED AND NEVER COMPUTED -- this function substitutes the
    DEFAULT of a declaration that carries none, which the definition states, and
    decides nothing about a label that is there.
    """
    return DEFAULT_PARTY if party_label is None else party_label


#: The declaration's formal party labels, in words, for the bindings that name
#: the instance's party (:func:`party_name`).
_PARTY_NAMES: Final[dict[str, str]] = {"A": "Alice", "B": "Bob"}


def party_name(party_label: Label | None) -> str:
    """Return the instance's party in words, for a binding that names it.

    The declared label (``A`` reads Alice, ``B`` Bob, any other label as
    itself), or Bob where none is declared (:func:`declared_party`). The
    A-MEAS, A-ROUND-SQ and A-SEQ bindings name the station's party with it
    rather than a singular role noun such as "the measuring party's", because
    a run emits them once per station. Naming the party decides nothing: no rule reads
    it.
    """
    party = declared_party(party_label)
    return _PARTY_NAMES.get(party, party)


def party_partition_statement(party_label: Label | None) -> str:
    """Return the emitted ``target_descriptor.party_partition``, for one party.

    ``def:reduction-instance`` (I2): every
    factor of every ``H(Q_s)`` belongs to the instance's declared party, Bob's
    by default, "because the handed model lives on the system THAT party
    receives". It is what makes the emitted tuple ``(Q, S, {F_v})`` satisfy the
    well-formedness conditions the consuming declaration places ON THAT PARTY'S
    SIDE (``thm:emit`` (ii)).

    THE DEFAULT SENTENCE IS THE ACCEPTED ONE, WORD FOR WORD, and is what every
    instance of this repository emits: no declaration carries a label today, so
    this function returns exactly the string the artefacts carried before the
    label existed. A declared label produces a sentence that NAMES THAT PARTY;
    nothing else in the artefact moves with it, the label deciding no condition
    (``thm:emit`` (ii): "no step reads the label's value").
    """
    party = declared_party(party_label)
    if party == DEFAULT_PARTY:
        return "default: Bob holds every factor of every H(Q_s)"
    return (
        f"declared: {party} holds every factor of every H(Q_s) "
        "(def:reduction-instance (I2), the declared party label)"
    )


def joined_sector_label(label: tuple[Label, str]) -> str:
    """Return a sector's ``(group, name)`` pair as ONE identifier, ``group:name``.

    ONE SPELLING OF THE JOIN, because two would be two conventions waiting to
    disagree. The emitted ``target_descriptor`` carries the PAIR
    (``def:reduction-instance`` (I2)); a consumer whose sector map is a flat
    list of identifiers -- the shared format's
    :class:`~certiqs_key.foundations.blocks.SectorStructure`, and so the docking and
    the factor emission alike -- reads the pair joined this way. The join is
    refused where it would collide, by whoever does it: this function decides
    nothing.
    """
    group, name = label
    return f"{group}:{name}"


def sector_projector_label(label: tuple[Label, str]) -> str:
    """Return the emitted label of the sector projector ``Pi_s``.

    ONE SPELLING, SHARED BY EVERY BUILDER, because the transported set of every
    instance contains every sector projector (``def:reduction-instance`` (I3))
    and the emitted ``transported_operators`` row names each one. The label is
    the sector's own ``(group, name)`` pair, which is what the emitted
    ``target_descriptor`` carries, so a consumer reading the row against the
    sector map needs no dictionary: ``Pi_(C,0)``, ``Pi_(nb,y0,t0)``.

    A SUM OF SECTOR PROJECTORS THAT AN INSTANCE TRANSPORTS BESIDES KEEPS ITS
    OWN NAME -- ``Pi_leq``, ``Pi_flag``, ``Pi_bl1`` -- because it is not the
    projector of any one sector; ``cor:entries`` (i) names the two kinds side
    by side.
    """
    group, name = label
    return f"Pi_({group},{name})"


def sector_projectors(sectors: SectorSet) -> tuple[tuple[Matrix, ...], ...]:
    """Return the mutually orthogonal ``{Pi_s}`` of Proposition ``prop:pinching``.

    The free-function spelling of :meth:`SectorSet.projectors`, kept because it
    is how callers and the frozen tests name the operation.
    Each projector is its SECTOR-BLOCK LIST; :meth:`SectorSet.dense_projectors`
    is the whole-space rendering a toy computation reads.
    """
    return sectors.projectors()
