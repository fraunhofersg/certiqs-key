"""The sector-block operator form: the block kind, the sector map, the operator.

THREE FROZEN SHARED TYPES, so that no module imports the protocol compiler:

* :class:`BlockKind`;
* :class:`SectorStructure`;
* :class:`BlockOperator`.

They are the type the reductions module's docking file converts INTO: the
docking converts to a frozen shared type rather than to a sibling module's, and
the compiler imports them from this package. They live in
:mod:`certiqs_key.foundations`, beside ``foundations/def:sector-map``, which
:class:`SectorStructure` implements; every package imports them from one place.

WHAT THEY ARE, IN spec/architecture.md 2.9's WORDS
==================================================
"The operator type is a list of sector blocks. ``OperatorRef`` IS
``BlockDiagonalOperator``: one array per block plus the block kind and the
ordering that names them, with no full-space alternative inside it." And: "A
consumer's structural check is a SECTOR-MAP COMPARISON -- the producer's block
kind, block identifiers and ordering against its own -- and a disagreement is a
refusal with a machine-readable reason. That replaces every zero-verification
the removed full-space form made necessary: the case it protected against, an
off-sector part that must be visible in order to be rejected, cannot be
constructed once a producer emits per sector."

So :class:`BlockOperator` takes BLOCKS and never a dense array: there is no
route by which a caller hands over a ``d_Q x d_Q`` matrix with a non-zero
off-block entry and has it silently truncated. :meth:`BlockOperator.dense`
goes the other way and is a CONVENIENCE for the places the mathematics is
stated on the whole space; it builds the direct sum, which "is what the list
MEANS, not a condition on it", so nothing is decided there that was not already
decided per block.

THE COMPILER'S WORKING TYPES. :class:`JointBlockOperator` (a block
list on ``A Q``), :func:`identity_blocks` and
:func:`block_sum_in_declared_order` live here too, so that one package holds
the block form and the compiler declares none of it twice. ``SemanticRole`` and
the rest of the bundle format are not here.

THE FACTORISED MAP. :class:`SectorFactor` and :class:`FactorisedSectorMap` add
2.9's declared product of party-scoped factors with its fixed product order,
and :class:`FactorDisagreement` is the factor-by-factor comparison. They sit
BESIDE :class:`SectorStructure` and change nothing in it: the single-factor map
is the default, :meth:`FactorisedSectorMap.single_factor`, and one factor
flattens to exactly the :class:`SectorStructure` it was given, so every
consumer of a single-factor map sees the single-factor behaviour. The format
DECLARES STRUCTURE AND NEVER A LICENCE: a producer that declares ``tau_A`` or
``{M_x}`` block diagonal licenses no consumer to infer that ``omega`` is.

THE SYSTEM TAG, AND THE ``A`` SIDE OF THE PRODUCT. A factor is scoped by a
SYSTEM as well as by a party -- :class:`SystemTag`, the closed two-member
vocabulary ``A`` and ``Q`` -- so that the two shapes needed are one
format: decoy declares ``[(A, alice, Alice sectors), (Q, bob, receiver
sectors)]`` and BBM92 declares ``[(Q, alice, her receiver's sectors), (Q, bob,
his)]`` at ``d_A = 1``.

THE ONE-ALICE-SECTOR, ONE-``Q``-FACTOR FORMAT IS THE SPECIAL CASE OF THAT,
ENTRY FOR ENTRY, and every clause below is written so that this sentence is
true:

* :data:`DEFAULT_FACTOR_SYSTEM` is ``Q``, so :class:`SectorFactor` and
  :meth:`FactorisedSectorMap.single_factor` default to the ``Q`` system;
* at most ONE ``A`` factor, and where there is one it comes FIRST in the
  product order, because the joint block convention is ``A``-first (the
  ``subsystem_order`` convention). A second ``A`` factor and an ``A`` factor
  anywhere but first are REFUSED rather than merged or permuted: a silent
  permutation is exactly the drift the declared product order exists to stop;
* :class:`JointBlockOperator` carries an ``A``-side :class:`SectorStructure`
  instead of one ``d_A``, with block ``(t, s)`` of the flattened joint map of
  size ``d_{A_t} d_s`` and the ``A`` index first inside a block. An
  integer ``alice_dim`` still constructs one -- :func:`single_alice_sector`, the
  one implicit sector labelled :data:`IMPLICIT_ALICE_SECTOR_LABEL` -- and the
  block list of a one-Alice-sector operator is the plain block list.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import product
from typing import Final

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Matrix,
    SummationVerdict,
    dimension,
    identity,
    is_hermitian,
    is_positive_semidefinite,
    is_square,
    matrix_is_binary64,
    sum_in_declared_order,
    zeros,
)

__all__ = [
    "DEFAULT_FACTOR_SYSTEM",
    "FACTORISED_MAP_COMPONENTS",
    "IMPLICIT_ALICE_SECTOR_LABEL",
    "PRODUCT_LABEL_SEPARATOR",
    "SECTOR_MAP_COMPONENTS",
    "BlockKind",
    "BlockOperator",
    "FactorDisagreement",
    "FactorisedSectorMap",
    "JointBlockOperator",
    "Label",
    "SectorFactor",
    "SectorMapDisagreement",
    "SectorStructure",
    "SystemTag",
    "block_sum_in_declared_order",
    "check_product_join",
    "default_factor_label",
    "identity_blocks",
    "single_alice_sector",
]

#: A block identifier, an outcome letter, a sector name: the shared format's
#: label type, spelled once.
Label = str


class BlockKind(StrEnum):
    """The kind a block structure carries (spec/architecture.md 2.9).

    The word "block" never appears in this format without one of these three
    kinds attached, because a positional ``blockDims`` list is not a stable
    public contract.
    """

    PHYSICAL_SECTOR = "physical_sector"
    PROOF_SECTOR = "proof_sector"
    NUMERICAL_BLOCK = "numerical_block"


class SystemTag(StrEnum):
    """Which system of the round model one sector factor decomposes.

    A CLOSED TWO-MEMBER VOCABULARY, and it is small on purpose. ``A`` is the
    transmitter's retained system -- the one ``tau_A``, ``{M_x}`` and a
    ``general`` right-hand side live on -- and ``Q`` is a measured system, the
    one ``{F_v}`` and every ``O^_k`` live on. Those are the only two the round
    model has, so a third member would be a system nothing in the mathematics
    names.

    IT IS NOT THE PARTY, AND THE TWO ARE INDEPENDENT. BBM92 declares two ``Q``
    factors, one scoped to Alice and one to Bob (each party's own receiver),
    while decoy declares one ``A`` factor scoped to Alice and one ``Q`` factor
    scoped to Bob. A format that carried only the party could not tell those
    two apart, and they differ in exactly the way that decides whether the
    Alice-side restriction of ``omega`` is available.
    """

    A = "A"
    Q = "Q"


#: The system a factor carries when its declaration does not say. It is ``Q``,
#: which is what makes :meth:`FactorisedSectorMap.single_factor` and every
#: plain :class:`SectorFactor` construction mean the one factor of Bob's
#: ``Q``.
DEFAULT_FACTOR_SYSTEM: Final[SystemTag] = SystemTag.Q


@dataclass(frozen=True)
class SectorMapDisagreement:
    """The first position at which two sector maps differ, and on which ground.

    The sector map is "the ordered list ``((s, d_s))_s`` of block identifiers
    with their dimensions, together with the block kind that names what the
    identifiers mean; it is ONE OBJECT". A comparison may report exactly one of
    four grounds: "a disagreement in KIND, in an IDENTIFIER, in the ORDER or in
    a DIMENSION".
    """

    #: One of ``block_kind``, ``identifier``, ``order``, ``dimension``.
    component: str
    #: The first position at which the lists differ, 0-based, or ``None`` for
    #: the block kind, which is not a position in a list.
    position: int | None
    detail: str


#: The four grounds, in comparison order. A comparison reports
#: exactly one of them and never a fifth.
SECTOR_MAP_COMPONENTS: Final[tuple[str, ...]] = (
    "block_kind",
    "identifier",
    "order",
    "dimension",
)


@dataclass(frozen=True)
class SectorStructure:
    """The sector map ``Smap``: identifiers, dimensions AND THE BLOCK KIND.

    Implements ``foundations/def:sector-map``: a non-empty list of distinct
    identifiers, each with a dimension ``d_s >= 1``, and a block kind; two
    maps agree (:meth:`agrees_with`) when all of these are equal, in order.

    ALL THREE COMPONENTS ARE MACHINE KEYS -- ``sector_index_set``,
    ``sector_dims`` and ``sector_block_kind`` -- "so that a consumer comparing
    sector maps can compare all three and not two of them".

    ``block_kind`` IS REQUIRED AND HAS NO DEFAULT. spec/architecture.md 2.9
    fixes the alphabet the answer is drawn from; it does not decide WHICH kind
    a given map is, and neither does this type. A value outside the enum is a
    malformed declaration and is refused as one -- never mapped to a nearest
    member, never defaulted. Supplying a kind where a declaration carries none
    would be deciding what the identifiers of somebody else's map mean.
    """

    labels: tuple[Label, ...]
    dims: tuple[int, ...]
    block_kind: BlockKind

    def __post_init__(self) -> None:
        """Refuse a presentation no sector-map comparison can be read against."""
        if len(self.labels) != len(self.dims):
            raise MalformedInputError(
                "a sector label list and a dim list of equal length"
            )
        if len(set(self.labels)) != len(self.labels):
            raise MalformedInputError("sector labels enumerate a set; one repeats")
        # foundations/def:sector-map: "a finite NON-EMPTY set S of block
        # identifiers ..., each identifier s with a dimension d_s >= 1".
        if not self.labels:
            raise MalformedInputError(
                "a sector map lists a non-empty set of block identifiers "
                "(foundations/def:sector-map); this one lists none"
            )
        for label, dim in zip(self.labels, self.dims, strict=True):
            if dim < 1:
                raise MalformedInputError(
                    f"sector {label!r} has dimension {dim!r}; every block of a "
                    "sector map has a dimension d_s >= 1 "
                    "(foundations/def:sector-map)"
                )
        if not isinstance(self.block_kind, BlockKind):
            raise MalformedInputError(
                "a sector map carries a block kind from the shared format's "
                "BlockKind (spec/architecture.md 2.9); "
                f"{self.block_kind!r} is not one of "
                f"{[kind.value for kind in BlockKind]}, and this type maps no "
                "value onto a nearest member and supplies none of its own"
            )

    @property
    def total_dim(self) -> int:
        """Return ``d_Q = sum_s d_s``."""
        return sum(self.dims)

    @property
    def count(self) -> int:
        """Return ``|S|``."""
        return len(self.labels)

    @property
    def entries(self) -> tuple[tuple[Label, int], ...]:
        """Return the ordered list ``((s, d_s))_s`` the map IS."""
        return tuple(zip(self.labels, self.dims, strict=True))

    def disagreement(self, other: SectorStructure) -> SectorMapDisagreement | None:
        """Return the first way ``other`` differs from this map, or ``None``.

        The four-component comparison: "in BLOCK KIND, in the LIST of block
        identifiers, in their ORDER and in their DIMENSIONS", reporting "the
        first position at which the lists differ". It is COMBINATORIAL -- "it
        compares labels and integers, NEVER MATRIX ENTRIES".
        """
        if self.block_kind is not other.block_kind:
            return SectorMapDisagreement(
                component="block_kind",
                position=None,
                detail=(
                    f"block kind {other.block_kind.value!r} against the emitted "
                    f"map's {self.block_kind.value!r}"
                ),
            )
        for position in range(max(len(self.labels), len(other.labels))):
            mine = self.labels[position] if position < len(self.labels) else None
            theirs = other.labels[position] if position < len(other.labels) else None
            if mine != theirs:
                # An identifier list that is a PERMUTATION of the emitted one
                # disagrees in ORDER; anything else disagrees in an IDENTIFIER.
                permuted = sorted(self.labels) == sorted(other.labels)
                return SectorMapDisagreement(
                    component="order" if permuted else "identifier",
                    position=position,
                    detail=(
                        f"at position {position} the supplied map carries "
                        f"{theirs!r} where the emitted map carries {mine!r}"
                    ),
                )
        for position, (mine_dim, their_dim) in enumerate(
            zip(self.dims, other.dims, strict=True)
        ):
            if mine_dim != their_dim:
                return SectorMapDisagreement(
                    component="dimension",
                    position=position,
                    detail=(
                        f"at position {position} the block "
                        f"{self.labels[position]!r} carries dimension "
                        f"{their_dim} against the emitted {mine_dim}"
                    ),
                )
        return None

    def agrees_with(self, other: SectorStructure) -> bool:
        """Whether ``other`` is this map, on all four components."""
        return self.disagreement(other) is None

    def projector(self, index: int) -> BlockOperator:
        """Return ``Pi_s`` for the sector at position ``index``, AS A BLOCK LIST.

        "Sector blocks in the declared total order of ``S``", so the projector
        of the ``i``-th sector is ``1_{d_i}`` on the ``i``-th block and zero on
        every other -- which IS the list this returns. It is an operator, so it
        has the operator type of spec/architecture.md 2.9 and not a dense
        alternative: "``OperatorRef`` IS ``BlockDiagonalOperator`` ... with no
        full-space alternative inside it". A caller that wants the
        ``d_Q x d_Q`` rendering forms it with :meth:`BlockOperator.dense`.
        """
        return BlockOperator.of(
            self,
            [
                identity(dim) if position == index else zeros(dim, dim)
                for position, dim in enumerate(self.dims)
            ],
        )

    def projectors(self) -> tuple[BlockOperator, ...]:
        """Return ``(Pi_s)_s`` in the declared order, each as its block list."""
        return tuple(self.projector(i) for i in range(self.count))


@dataclass(frozen=True)
class BlockOperator:
    """One operator on the target space, as its list of sector blocks.

    ``blocks[i]`` is the array on the ``i``-th sector in the declared total
    order of the map it is given, which is the order ``Smap`` fixes and which
    is "NOT A SECOND CHOICE".

    THE TARGET SPACE IS WHATEVER ITS MAP NAMES, and that is not a widening:
    this type reads ``sector_map.dims`` and nothing else, so an ``A``-side
    family -- ``{M_x}``, ``tau_A``, a ``general`` right-hand side against the
    ``A`` factor of :class:`FactorisedSectorMap` -- is served by it unchanged,
    as is :func:`block_sum_in_declared_order` over such a family. At one
    ``A`` sector the single block IS the dense ``d_A x d_A`` operator and
    :meth:`dense` returns it entry for entry.
    """

    sector_map: SectorStructure
    blocks: tuple[Matrix, ...]

    def __post_init__(self) -> None:
        """Refuse a block list that is not a block list against its own map."""
        if len(self.blocks) != self.sector_map.count:
            raise MalformedInputError(
                f"a block list against a map with {self.sector_map.count} "
                f"sectors carries that many blocks, not {len(self.blocks)}"
            )
        for position, (block, dim) in enumerate(
            zip(self.blocks, self.sector_map.dims, strict=True)
        ):
            if not is_square(block):
                raise MalformedInputError(
                    f"the block at position {position} is not a square array"
                )
            if dimension(block) != dim:
                raise MalformedInputError(
                    f"the block at position {position} has dimension "
                    f"{dimension(block)} against the declared d_s = {dim}"
                )

    @classmethod
    def of(cls, sector_map: SectorStructure, blocks: Sequence[Matrix]) -> BlockOperator:
        """Return the operator whose blocks are ``blocks``, in ``Smap``'s order."""
        return cls(sector_map=sector_map, blocks=tuple(blocks))

    def dense(self) -> Matrix:
        """Return the direct sum ``bigoplus_s F^(s)``.

        "The identity ``F_v = bigoplus_s F_v^(s)`` is what the list MEANS, not
        a condition on it."
        """
        total = self.sector_map.total_dim
        rows = [list(row) for row in zeros(total, total)]
        offset = 0
        for block, dim in zip(self.blocks, self.sector_map.dims, strict=True):
            for i in range(dim):
                for j in range(dim):
                    rows[offset + i][offset + j] = block[i][j]
            offset += dim
        return tuple(tuple(row) for row in rows)

    def is_hermitian(self) -> bool:
        """Per block: ``F^(s) = F^(s)dag`` for every ``s``, decided exactly."""
        return all(is_hermitian(block) for block in self.blocks)

    def is_positive_semidefinite(self) -> bool:
        """Per block, decided at zero and at no window."""
        return all(is_positive_semidefinite(block) for block in self.blocks)

    def is_binary64(self) -> bool:
        """Whether every entry of every block is a binary64 number."""
        return all(matrix_is_binary64(block) for block in self.blocks)


#: The identifier of the ONE ``A`` sector of an operator constructed from an
#: integer ``d_A``. It is a DECLARED CONSTANT and not an ad hoc string at a call
#: site: the implicit sector is the same sector wherever it is built, and two
#: producers that spelled it differently would disagree in a sector-map
#: comparison about a sector neither of them declared.
IMPLICIT_ALICE_SECTOR_LABEL: Final[Label] = "A"


def single_alice_sector(alice_dim: int, block_kind: BlockKind) -> SectorStructure:
    """Return the one-sector ``A``-side map of an undecomposed ``A``.

    THE DEGENERATE CASE, SAID IN THE GENERAL SHAPE: one sector labelled
    :data:`IMPLICIT_ALICE_SECTOR_LABEL` of dimension ``d_A``. The kind is the
    one the joint map carries -- a product of factors carries ONE block kind
    (spec/architecture.md 2.9) -- so it is taken from the caller's own map and
    never supplied here, for the reason :class:`SectorStructure` defaults none.
    """
    if alice_dim < 1:
        raise MalformedInputError(
            f"d_A is a positive dimension; {alice_dim} is not one"
        )
    return SectorStructure(
        labels=(IMPLICIT_ALICE_SECTOR_LABEL,),
        dims=(alice_dim,),
        block_kind=block_kind,
    )


@dataclass(frozen=True)
class JointBlockOperator:
    """A block list on ``A Q``: one array on ``A_t Q_s`` per joint sector.

    The type of ``omega`` in the compiler's ``def:feasible`` and of its
    ``feasibility_witness`` input key. ``thm:feasibility`` (ii): "The verification of a
    candidate is finite AND PER BLOCK: NO ARRAY OF DIMENSION ``d_A d_Q`` IS
    FORMED AT ANY POINT", the ``(t, s)``-block having size ``d_{A_t} d_s``.

    Its sector structure "is NOT A CONDITION here: ``omega^*`` is presented as
    a list, one array on ``A Q_s`` per ``s``, so THE OFF-BLOCK CONJUNCT HOLDS
    BY THE PRESENTATION AND THERE IS NOTHING TO VERIFY". What is compared
    instead, for a SUPPLIED witness, is its sector map, at one place only.

    THE ``A`` SIDE IS A SECTOR STRUCTURE, NOT ONE ``d_A``.
    ``blocks`` runs over the JOINT sectors in the flattened product order --
    the ``A`` factor first and the ``Q`` map fastest, which is
    :meth:`FactorisedSectorMap.flattened`'s own order and the ``A``-first
    convention ``subsystem_order`` declares -- so at ONE ``A`` sector the list
    is the per-``Q``-sector list, entry for entry, and
    :attr:`alice_dim` is the integer. Construction from an
    integer is supported: :meth:`of` takes ``int`` or
    :class:`SectorStructure` in that position and builds
    :func:`single_alice_sector` from the integer.
    """

    sector_map: SectorStructure
    #: The ``A``-side map. One sector at ``d_A`` undecomposed.
    alice_sectors: SectorStructure
    blocks: tuple[Matrix, ...]

    def __post_init__(self) -> None:
        """Refuse a list whose blocks are not the blocks of its own maps."""
        if not isinstance(self.alice_sectors, SectorStructure):
            raise MalformedInputError(
                "the A side of a joint operator is a SectorStructure -- the map "
                "of the retained system -- and "
                f"{self.alice_sectors!r} is not one. An integer d_A is passed "
                "to JointBlockOperator.of, which builds the one-sector map "
                "from it (single_alice_sector); this constructor supplies no "
                "map of its own"
            )
        # The joint map is a product of the two sides, so its identifiers are
        # joined by the declared separator and the same two refusals apply
        # neither side's labels may contain it, and the A side's may not
        # end where it begins. `joint_sectors` is where the join happens; here
        # is where a list that could not be flattened is refused.
        check_product_join(
            [self.alice_sectors.labels, self.sector_map.labels],
            what="sector identifier",
        )
        # THE A SIDE'S IDENTIFIERS MAY NOT CONTAIN THE SEPARATOR, AND THE Q
        # SIDE'S MAY. The refusal's
        # reason is that the flattened joint identifier must say which side
        # supplied which part, and with the A side FIRST, AT MOST ONE A FACTOR
        # (FactorisedSectorMap refuses a second) and no separator inside an A
        # identifier, the split is the FIRST occurrence and is unambiguous
        # whatever the Q side carries. And the Q side must be allowed to carry
        # one: with several measured factors its identifiers ARE the factors'
        # identifiers joined by this separator (protocol-compiler
        # def:declaration (DX1)), so refusing them would refuse every joint
        # operator of a two-factor declaration -- including the feasible set's
        # own omega, whose blocks are per JOINT sector. The Q side's own
        # unambiguity is its factor list's, decided by `check_product_join` when
        # that list was flattened; what stays refused here is the leading
        # separator character on the Q side, which the call above covers.
        for label in self.alice_sectors.labels:
            if PRODUCT_LABEL_SEPARATOR in label:
                raise MalformedInputError(
                    f"the A-side sector identifier {label!r} contains the "
                    f"declared product separator {PRODUCT_LABEL_SEPARATOR!r}, "
                    "so the flattened joint identifier would not say where the "
                    "A part ends; the A side is the FIRST component of the join "
                    "and the split is its first occurrence"
                )
        if self.alice_sectors.block_kind is not self.sector_map.block_kind:
            raise MalformedInputError(
                "the two sides of one joint map carry ONE block kind, because "
                "the flattened joint map carries one (spec/architecture.md "
                f"2.9); the A side is {self.alice_sectors.block_kind.value!r} "
                f"and the Q side {self.sector_map.block_kind.value!r}, and this "
                "type assigns no kind of its own to a product"
            )
        expected = self.alice_sectors.count * self.sector_map.count
        if len(self.blocks) != expected:
            raise MalformedInputError(
                f"a block list on A Q against {self.alice_sectors.count} A "
                f"sectors and {self.sector_map.count} Q sectors carries "
                f"{expected} joint blocks, not {len(self.blocks)}"
            )
        for position, (block, dim) in enumerate(
            zip(self.blocks, self._joint_dims(), strict=True)
        ):
            if not is_square(block) or dimension(block) != dim:
                raise MalformedInputError(
                    f"the block at position {position} is not an "
                    f"n_j x n_j array with n_j = d_A_t d_s = {dim}"
                )

    def _joint_dims(self) -> tuple[int, ...]:
        """Return ``(d_{A_t} d_s)_{(t, s)}`` in the flattened product order."""
        return tuple(
            alice_dim * sector_dim
            for alice_dim in self.alice_sectors.dims
            for sector_dim in self.sector_map.dims
        )

    @classmethod
    def of(
        cls,
        sector_map: SectorStructure,
        alice_side: int | SectorStructure,
        blocks: Sequence[Matrix],
    ) -> JointBlockOperator:
        """Return the joint block list with these blocks, in the joint order.

        ``alice_side`` is the ``A``-side map, or the integer ``d_A`` of an
        undecomposed ``A`` -- which is the call every existing site makes and
        which means what it meant.
        """
        alice_sectors = (
            single_alice_sector(alice_side, sector_map.block_kind)
            if isinstance(alice_side, int)
            else alice_side
        )
        return cls(
            sector_map=sector_map,
            alice_sectors=alice_sectors,
            blocks=tuple(blocks),
        )

    @property
    def alice_dim(self) -> int:
        """Return ``d_A`` of an operator whose ``A`` carries ONE sector.

        THE COMPATIBILITY READING, AND IT RAISES RATHER THAN ANSWERING WRONGLY.
        Every site that reads ``.alice_dim`` is written for a
        joint operator on an undecomposed ``A``, where ``d_A`` is the size of
        the one sector and the answer is the number it always was. At two or
        more ``A`` sectors there is no single ``d_A`` those sites could mean:
        ``sum_t d_{A_t}`` would make ``kron(identity(d_A), .)`` the wrong
        operator and ``d_A d_s`` the wrong block size, silently. So the
        question is refused, naming the ``A`` map, and the caller reads
        :attr:`alice_sectors` instead.
        """
        if self.alice_sectors.count != 1:
            raise MalformedInputError(
                "d_A is the dimension of an undecomposed A; this joint operator "
                f"carries {self.alice_sectors.count} A sectors "
                f"{list(self.alice_sectors.labels)}, and no one integer stands "
                "for them. Read alice_sectors and work per A sector"
            )
        return self.alice_sectors.dims[0]

    def joint_sectors(self) -> SectorStructure:
        """Return the flattened joint map ``((t, s), d_{A_t} d_s)``, in order.

        The flattening :class:`FactorisedSectorMap` declares, applied to the
        ``A`` side and this operator's ``Q`` map: identifiers joined by
        :data:`PRODUCT_LABEL_SEPARATOR`, dimensions multiplied, the ``Q`` side
        running fastest. It names the positions of :attr:`blocks`; it is not a
        second place a sector map is declared, and it names NO PARTY -- a joint
        operator carries the two systems and not who holds them.
        """
        return SectorStructure(
            labels=tuple(
                PRODUCT_LABEL_SEPARATOR.join((alice_label, sector_label))
                for alice_label in self.alice_sectors.labels
                for sector_label in self.sector_map.labels
            ),
            dims=self._joint_dims(),
            block_kind=self.sector_map.block_kind,
        )

    def block(self, alice_index: int, sector_index: int) -> Matrix:
        """Return the block on ``A_t Q_s`` at the two declared positions."""
        return self.blocks[alice_index * self.sector_map.count + sector_index]

    def dense(self) -> Matrix:
        """Return the operator on ``A Q`` the list denotes.

        FORMED BY NO PREDICATE OF THE COMPILER -- ``thm:feasibility`` (ii) says no
        ``d_A d_Q`` array is formed at any point -- and provided only for a
        caller stating a proposition ABOUT the feasible set rather than
        deciding membership in it. The block at joint position ``(t, s)`` sits
        on the rows and columns ``A_t`` indexes within the ``s``-th sector,
        which is the ``A``-first factor order the ``subsystem_order``
        convention declares; at one ``A`` sector that is the placement this
        method has always made.
        """
        dims = self.sector_map.dims
        q_total = self.sector_map.total_dim
        total = self.alice_sectors.total_dim * q_total
        rows = [list(row) for row in zeros(total, total)]
        for alice_position, alice_dim in enumerate(self.alice_sectors.dims):
            alice_start = sum(self.alice_sectors.dims[:alice_position])
            for position, dim in enumerate(dims):
                start = sum(dims[:position])
                block = self.block(alice_position, position)
                for a1 in range(alice_dim):
                    for s1 in range(dim):
                        for a2 in range(alice_dim):
                            for s2 in range(dim):
                                rows[(alice_start + a1) * q_total + start + s1][
                                    (alice_start + a2) * q_total + start + s2
                                ] = block[a1 * dim + s1][a2 * dim + s2]
        return tuple(tuple(row) for row in rows)


def identity_blocks(sector_map: SectorStructure) -> BlockOperator:
    """Return ``1_Q`` as the block list ``(1_{Q_s})_s``."""
    return BlockOperator.of(sector_map, [identity(dim) for dim in sector_map.dims])


def block_sum_in_declared_order(
    family: Sequence[BlockOperator],
) -> tuple[SummationVerdict, ...]:
    """Accumulate ``sum_j a_j^(s)`` per sector, in the declared order.

    The compiler's ``def:exact`` (S) is stated per block -- "writing
    ``Sigma^(s)`` for the total ``Sigma`` that Eq. ``eq:declorder`` produces on
    the block family ``{a_j^(s)}_j``: FOR EACH ``s``, every one of the ``|J|``
    entrywise binary64 additions forming it is exact" -- so this returns one
    verdict per sector, in ``Smap``'s order, and the caller reads (C) and (S)
    off each.
    """
    if not family:
        raise MalformedInputError(
            "a completeness sum is over a NON-EMPTY declared alphabet"
        )
    sector_map = family[0].sector_map
    for member in family:
        if member.sector_map is not sector_map and not sector_map.agrees_with(
            member.sector_map
        ):
            raise MalformedInputError(
                "a family summed per block is a family against ONE map; the "
                "sector-map comparison is where a disagreement is refused, "
                "not here"
            )
    return tuple(
        sum_in_declared_order([member.blocks[index] for member in family])
        for index in range(sector_map.count)
    )


#: The separator that joins the factors' identifiers into one flattened
#: identifier -- of a sector, and of a product outcome letter
#: (:mod:`certiqs_key.domain.families`). It is part of the declared product
#: convention, so a factor identifier may not contain it: the flattening stays
#: readable backwards.
#:
#: IT IS ``"__"`` AND NOT ``"*"``, because a flattened
#: identifier is a WIRE identifier too. A sector identifier is an HDF5 link
#: name, so it is drawn from ``identifiers.IDENTIFIER_PATTERN``
#: (``[A-Za-z0-9_][A-Za-z0-9_.+-]*``), which does not contain ``*``: with
#: ``*`` the flattened identifier of a product of two measured factors
#: would be a string no ``sector_index_set`` could carry, and BBM92 declares two
#: measured factors. The pattern is not widened for it -- it is restricted for
#: a mechanical reason, not an aesthetic one -- so the separator is ``"__"``.
#:
#: WHY ``"__"`` OF THE LEGAL CANDIDATES. The separator must appear in NO label
#: that is declared, or this format's own "a label may not contain the
#: separator" refusal would refuse something already declared. Of the
#: identifier-legal candidates: ``+`` and ``-`` are already label characters
#: (the receiver's ``sc_+``, ``Lfss+``, ``Lwp+``, and every dashed assumption
#: id); ``_`` is in most labels (``Z_H``, ``Chan_0``, ``in_0``); ``.`` occurs
#: in identifier-shaped ids such as ``AE-PZ-0.1`` and is the character that
#: separates a basis path (``computational.Q.<label>``), so a dotted flattened
#: label would read as one. ``__`` occurs in no label: of the 24159
#: identifier-shaped string literals under ``src/``, ``instances/`` and
#: ``tests/``, exactly three contain it (``__future__``,
#: ``__dataclass_fields__``, ``__init__.py``) and none of the three is a label;
#: and of the 73 distinct labels the whole suite constructs at run time, none
#: contains it.
PRODUCT_LABEL_SEPARATOR: Final[str] = "__"


def check_product_join(
    groups: Sequence[Sequence[Label]], *, what: str = "identifier"
) -> None:
    """Refuse a product whose flattened identifier is ambiguous.

    THE SEPARATOR MUST OCCUR IN A FLATTENED IDENTIFIER EXACTLY ONCE PER JOIN,
    and containment alone does not give that once ``_`` is itself a label
    character: the factors ``("a", "a_")`` and ``("b", "_b")`` flatten
    ``a_``+``b`` and ``a``+``_b`` to the SAME string ``a___b``, so the
    flattening stops saying which factor supplied which part and two different
    product sectors collide under one identifier.

    THE RULE, over the label lists IN PRODUCT ORDER: a label may not END with a
    non-empty proper prefix of the separator unless its factor is the LAST, and
    may not BEGIN with a non-empty proper suffix of the separator unless its
    factor is the FIRST. For the declared ``"__"`` both sets are ``{"_"}``, so
    it reads: no trailing ``_`` except in the last factor, no leading ``_``
    except in the first.

    WHY THAT IS THE SAME AS "the join of each adjacent pair contains the
    separator exactly once". An extra occurrence either lies inside one label,
    which :class:`SectorFactor` and :class:`FactorFamily` already refuse, or
    overlaps the inserted separator. An occurrence overlapping it on the left
    ends inside the separator, so the left label ends with a non-empty proper
    prefix of it; one overlapping on the right begins inside it, so the right
    label begins with a non-empty proper suffix. Forbidding both leaves exactly
    one. Checking it this way is per label rather than per pair of labels, which
    matters for an outcome alphabet that is itself a product.

    A ONE-FACTOR PRODUCT IS UNCONSTRAINED, since its only factor is both first
    and last -- which is what makes this refusal refuse nothing that is declared.
    """
    separator = PRODUCT_LABEL_SEPARATOR
    prefixes = tuple(separator[:k] for k in range(1, len(separator)))
    suffixes = tuple(separator[k:] for k in range(1, len(separator)))
    last = len(groups) - 1
    for position, labels in enumerate(groups):
        for label in labels:
            if position != last and label.endswith(prefixes):
                raise MalformedInputError(
                    f"the {what} {label!r} of the factor at position "
                    f"{position} ends where the declared product separator "
                    f"{separator!r} begins, so the flattened {what} would "
                    "contain the separator twice and would not say which "
                    "factor supplied which part; only the LAST factor's labels "
                    "may end that way"
                )
            if position != 0 and label.startswith(suffixes):
                raise MalformedInputError(
                    f"the {what} {label!r} of the factor at position "
                    f"{position} begins where the declared product separator "
                    f"{separator!r} ends, so the flattened {what} would "
                    "contain the separator twice and would not say which "
                    "factor supplied which part; only the FIRST factor's "
                    "labels may begin that way"
                )


#: The grounds a FACTOR-BY-FACTOR comparison may report: the three that are
#: about the factorisation itself, then the four of a single map, reported
#: inside the first factor that disagrees.
FACTORISED_MAP_COMPONENTS: Final[tuple[str, ...]] = (
    "factor_count",
    "system",
    "party",
    *SECTOR_MAP_COMPONENTS,
)


def default_factor_label(position: int) -> Label:
    """Return the label a factor that declared none carries: ``f<position>``.

    0-BASED IN THE PRODUCT ORDER OF ITS OWN SIDE, which is ``reductions``' own
    default for an emitted factor, so a declaration built from that emission and
    one built by hand name the same factor the same way. It is a DEFAULT and not a
    rule: a declarer that names its factors keeps its names, and this is what a
    scope is compared against where nobody did.
    """
    return f"f{position}"


@dataclass(frozen=True)
class SectorFactor:
    """One factor of a sector map: a system, a party label and its map.

    spec/architecture.md 2.9: a sector map "is a product of party-scoped
    factors", each of them "a party label together with that party's own sector
    map". The party label is the declaration's own and not a member of a fixed
    alphabet -- 2.9 fixes the SHAPE, and naming the parties of a protocol is
    the declaration's business.

    THE SYSTEM IS SCOPE OF ANOTHER AXIS, and it IS a fixed alphabet
    (:class:`SystemTag`): a factor decomposes the retained ``A`` or a measured
    ``Q``, the round model has those two and no third, and which one it is
    decides what may be declared block diagonal against it. It defaults to
    :data:`DEFAULT_FACTOR_SYSTEM`, so a factor written without a tag
    is the ``Q`` factor.
    """

    party: Label
    sectors: SectorStructure
    system: SystemTag = DEFAULT_FACTOR_SYSTEM
    #: THE FACTOR'S OWN NAME, which is NOT its party. ``""`` means "the
    #: position default", :func:`default_factor_label`, so a factor
    #: written without a label is the position-default factor and nothing on
    #: the wire moves.
    #:
    #: WHY A FACTOR NEEDS A NAME OF ITS OWN. A party may hold TWO factors -- two
    #: stations of one party -- so a party label does not identify a factor, and a
    #: consumer that compared a scoped constraint entry's scope against party
    #: labels would admit an entry scoped to either of them and refuse neither.
    #: ``protocol-compiler`` ``def:declaration`` (DX6) scopes an entry to ONE
    #: measured factor and ``def:validator`` V6 refuses a scope that "names no
    #: measured factor" with ``constraint_scope_not_a_factor``; that comparison is
    #: decidable only against a per-factor name. ``reductions``' emission declares
    #: one per factor and carries the party label BESIDE it, and this slot is where
    #: it lands.
    label: Label = ""

    def __post_init__(self) -> None:
        """Refuse a factor that cannot be read back out of the product."""
        if not self.party:
            raise MalformedInputError(
                "a sector factor carries a non-empty party label; the party is "
                "what scopes the factor"
            )
        if not isinstance(self.system, SystemTag):
            raise MalformedInputError(
                "a sector factor carries a system from the shared format's "
                f"SystemTag; {self.system!r} is not one of "
                f"{[tag.value for tag in SystemTag]}, and this type maps no "
                "value onto a nearest member"
            )
        for label in self.sectors.labels:
            if PRODUCT_LABEL_SEPARATOR in label:
                raise MalformedInputError(
                    f"the sector identifier {label!r} contains the declared "
                    f"product separator {PRODUCT_LABEL_SEPARATOR!r}, so the "
                    "flattened identifier would not say which factor supplied "
                    "which part"
                )


@dataclass(frozen=True)
class FactorDisagreement:
    """The first factor at which two factorised sector maps differ.

    ``component`` is one of :data:`FACTORISED_MAP_COMPONENTS`: the number of
    factors, a system tag or a party label, which are about the factorisation,
    or one of the four components of a single map, which is then also carried
    whole in ``within`` together with its position INSIDE that factor.
    """

    #: The position of the first disagreeing factor in the product order, or
    #: ``None`` when the factor lists are not the same length.
    factor_position: int | None
    #: The party the disagreeing factor is scoped to, where there is one.
    party: Label | None
    #: The system the disagreeing factor decomposes, where there is one. It is
    #: the EMITTED map's, as ``party`` is, so a refusal says what was expected.
    system: SystemTag | None
    component: str
    #: The single-map disagreement inside that factor, where the ground is one
    #: of the four of :data:`SECTOR_MAP_COMPONENTS`.
    within: SectorMapDisagreement | None
    detail: str


@dataclass(frozen=True)
class FactorisedSectorMap:
    """A sector map as a product of party-scoped factors, in the product order.

    THE TUPLE ORDER IS THE PRODUCT ORDER (spec/architecture.md 2.9): the
    flattened map "runs the last factor fastest, its identifiers are the
    factors' identifiers joined in that order and its dimensions are the
    products", which is what keeps two producers from flattening the same pair
    differently.

    THE SINGLE-FACTOR MAP IS THE DEFAULT, :meth:`single_factor`, and
    :meth:`flattened` returns exactly the :class:`SectorStructure` it was given
    there.

    THE FACTORS CARRY ONE BLOCK KIND, because the flattened map carries one. A
    product of differently-licensed factors is REFUSED rather than assigned a
    kind here, for the reason :class:`SectorStructure` defaults none: deciding
    it would be deciding what somebody else's decomposition is licensed by
    (2.3: the kind records WHY the decomposition is licensed, not what its
    labels mean physically).

    IT DECLARES STRUCTURE AND NEVER A LICENCE. A producer that declares
    ``tau_A`` or ``{M_x}`` block diagonal licenses no consumer to infer that
    ``omega`` is; nothing here reads one factor's structure onto another's, and
    no method of this type says anything about a joint operator.

    AT MOST ONE ``A`` FACTOR, AND IT COMES FIRST. The retained
    system is one system: a product of two ``A`` factors would be a second
    decomposition of ``A`` beside the first, which no consumer here knows how
    to read, so it is refused
    rather than flattened into a shape whose meaning nobody declared. And where
    an ``A`` factor is present it is the FIRST of the product, because the
    joint block convention is ``A``-first (the ``subsystem_order`` convention,
    :meth:`JointBlockOperator.dense`); a product that puts it elsewhere is
    refused rather than permuted, for the reason the product order is declared
    at all.
    """

    factors: tuple[SectorFactor, ...]

    def __post_init__(self) -> None:
        """Refuse an empty product, or one whose factors are licensed apart."""
        if not self.factors:
            raise MalformedInputError(
                "a sector map is a product of AT LEAST ONE factor; the "
                "single-factor default is the map itself"
            )
        kinds = {factor.sectors.block_kind for factor in self.factors}
        if len(kinds) != 1:
            raise MalformedInputError(
                "the factors of one sector map carry ONE block kind, because "
                "the flattened map carries one; this product mixes "
                f"{sorted(kind.value for kind in kinds)} and this type assigns "
                "no kind of its own to a product"
            )
        alice = [
            position
            for position, factor in enumerate(self.factors)
            if factor.system is SystemTag.A
        ]
        if len(alice) > 1:
            raise MalformedInputError(
                f"a sector map carries AT MOST ONE {SystemTag.A.value!r} "
                f"factor; this product carries {len(alice)}, at positions "
                f"{alice}. The retained system is one system, and a second "
                "decomposition of it is a shape no consumer of this format "
                "reads -- nothing in the two-sided sweep declares one"
            )
        if alice and alice[0] != 0:
            raise MalformedInputError(
                f"an {SystemTag.A.value!r} factor is the FIRST factor of the "
                f"product; this one is at position {alice[0]}. The joint block "
                "convention is A-first (the subsystem_order convention), and "
                "this type refuses another order rather than permuting a "
                "declared product silently"
            )
        # THE FLATTENING IS INJECTIVE OR THE PRODUCT IS REFUSED. Containment of
        # the separator is refused per factor; this is the other half, which is
        # about a PAIR of factors and so can only be decided here.
        check_product_join(
            [factor.sectors.labels for factor in self.factors],
            what="sector identifier",
        )

    @classmethod
    def single_factor(
        cls, party: Label, sectors: SectorStructure
    ) -> FactorisedSectorMap:
        """Return the one-factor map.

        The factor takes :data:`DEFAULT_FACTOR_SYSTEM`, so this is the one
        ``Q`` factor.
        """
        return cls(factors=(SectorFactor(party=party, sectors=sectors),))

    @property
    def block_kind(self) -> BlockKind:
        """Return the one kind the factors agree on."""
        return self.factors[0].sectors.block_kind

    def labels_of(self, system: SystemTag) -> tuple[Label, ...]:
        """Return one side's FACTOR LABELS, in the product order.

        A declared label where a factor carries one and
        :func:`default_factor_label` of its position on that side otherwise, so
        that every factor has a name whether or not one was declared. THE POSITION
        IS THE ONE ON ITS OWN SIDE, which is the side a scope is compared against:
        ``def:declaration`` (DX6) scopes an entry to a MEASURED factor, and the
        measured factors are the ones ``F`` enumerates.

        THE LABELS ARE AN ALPHABET AND A REPEAT IS REFUSED, because a scope that
        named two factors would make ``constraint_scope_not_a_factor`` undecidable
        in the direction that matters -- it would not refuse.
        """
        side = self.factors_of(system)
        labels = tuple(
            factor.label or default_factor_label(position)
            for position, factor in enumerate(side)
        )
        if len(set(labels)) != len(labels):
            raise MalformedInputError(
                f"the factors of system {system.value!r} carry the repeated "
                f"label(s) in {list(labels)}; a factor label NAMES a factor, and "
                "a scope that named two of them could not be refused"
            )
        return labels

    @property
    def parties(self) -> tuple[Label, ...]:
        """Return the party labels in the product order."""
        return tuple(factor.party for factor in self.factors)

    @property
    def systems(self) -> tuple[SystemTag, ...]:
        """Return the system tags in the product order."""
        return tuple(factor.system for factor in self.factors)

    def factors_of(self, system: SystemTag) -> tuple[SectorFactor, ...]:
        """Return the factors scoped to one system, IN THE PRODUCT ORDER.

        What a consumer reads the product by: the ``A``-side factors (at most
        one) and the ``Q``-side factors. The order is the product's own, so a
        consumer that walks one side walks it in the order the flattening
        multiplies it in.
        """
        return tuple(factor for factor in self.factors if factor.system is system)

    def flattened_of(self, system: SystemTag) -> SectorStructure | None:
        """Return the flattening of one side of the product, or ``None``.

        The same declared convention as :meth:`flattened`, applied to that
        side's factors alone: it is the map of ``A`` or of the measured system
        that a block list on that side is declared against. ``None`` where no
        factor carries the system -- a map with no ``A`` factor has no ``A``
        side, and an empty product is not a sector map.
        """
        side = self.factors_of(system)
        if not side:
            return None
        return FactorisedSectorMap(factors=side).flattened()

    def flattened(self) -> SectorStructure:
        """Return the product map as one :class:`SectorStructure`, in order.

        The last factor runs fastest. With one factor this is the factor's own
        map, entry for entry: the join of a single identifier is that
        identifier and the product of a single dimension is that dimension.
        """
        labels: list[Label] = []
        dims: list[int] = []
        for combination in product(
            *(factor.sectors.entries for factor in self.factors)
        ):
            labels.append(
                PRODUCT_LABEL_SEPARATOR.join(label for label, _ in combination)
            )
            dim = 1
            for _, factor_dim in combination:
                dim *= factor_dim
            dims.append(dim)
        return SectorStructure(
            labels=tuple(labels), dims=tuple(dims), block_kind=self.block_kind
        )

    def disagreement(self, other: FactorisedSectorMap) -> FactorDisagreement | None:
        """Return the first factor at which ``other`` differs, or ``None``.

        FACTOR BY FACTOR IN THE PRODUCT ORDER, so that a consumer says WHICH
        party's factor it refused. The comparison inside a factor is
        :meth:`SectorStructure.disagreement`, unchanged, and it is
        combinatorial there as it is here: labels, integers and party names,
        never matrix entries.
        """
        if len(self.factors) != len(other.factors):
            return FactorDisagreement(
                factor_position=None,
                party=None,
                system=None,
                component="factor_count",
                within=None,
                detail=(
                    f"the supplied map is a product of {len(other.factors)} "
                    f"factors against the emitted map's {len(self.factors)}"
                ),
            )
        for position, (mine, theirs) in enumerate(
            zip(self.factors, other.factors, strict=True)
        ):
            # THE SYSTEM BEFORE THE PARTY. Which system a factor decomposes is
            # what fixes its place in the product (an A factor is first) and
            # what decides which operators may be declared against it; the
            # party says who holds it. A comparison that reported the party
            # first would name the finer disagreement of the two.
            if mine.system is not theirs.system:
                return FactorDisagreement(
                    factor_position=position,
                    party=mine.party,
                    system=mine.system,
                    component="system",
                    within=None,
                    detail=(
                        f"the factor at position {position} decomposes system "
                        f"{theirs.system.value!r} where the emitted map "
                        f"decomposes {mine.system.value!r}"
                    ),
                )
            if mine.party != theirs.party:
                return FactorDisagreement(
                    factor_position=position,
                    party=mine.party,
                    system=mine.system,
                    component="party",
                    within=None,
                    detail=(
                        f"the factor at position {position} is scoped to party "
                        f"{theirs.party!r} where the emitted map scopes it to "
                        f"{mine.party!r}"
                    ),
                )
            inside = mine.sectors.disagreement(theirs.sectors)
            if inside is not None:
                return FactorDisagreement(
                    factor_position=position,
                    party=mine.party,
                    system=mine.system,
                    component=inside.component,
                    within=inside,
                    detail=(
                        f"in the factor at position {position}, system "
                        f"{mine.system.value!r}, party "
                        f"{mine.party!r}: {inside.detail}"
                    ),
                )
        return None

    def agrees_with(self, other: FactorisedSectorMap) -> bool:
        """Whether ``other`` is this product, factor by factor and in order."""
        return self.disagreement(other) is None
