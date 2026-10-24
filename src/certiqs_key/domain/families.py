"""The factorised operator family: several measuring parties, no product datum.

WHY A FAMILY PER FACTOR. Forming the product of two stations' targets and
passing it through the emission normaliser has three obstructions: a product
sector -- one station's data block times the other's flag -- is neither a class-complete
datum nor a scalar times the identity, the stability clause fails at the lattice scale
for weighted-flag values whose products leave the lattice, and a normalised product
would declare a NON-PRODUCT measurement for two separated stations.

WHAT IS DECLARED INSTEAD, and what this module carries: one exactly admissible
block-list family PER MEASURED FACTOR, over that factor's own alphabet, plus
the rule

    F_v = (x)_f F^f_{v_f},    v = (v_f)_f in prod_f V^f.

``reductions/thm:emitted-product`` (draft) proves the rest: the product is a
POVM, Hermitian, positive semidefinite and complete "as identities of the exact
rational numbers the factors emitted"; it is block diagonal for the product
sector map, its block at ``s = (s_f)_f`` being the Kronecker product of the
factors' blocks; and with one factor every statement is the one-factor
statement, which is today's format.

SO NO PRODUCT IS A DATUM AND NO PREDICATE FORMS ONE. Every exact predicate of
spec/architecture.md 2.9's admission -- the sector-map comparison, Hermiticity,
positive semidefiniteness, completeness in the declared order -- runs PER
FACTOR, with the functions :mod:`certiqs_key.foundations.blocks` already has, on
arrays of the factor's own size. :meth:`FactorisedFamily.product_block` exists
for a numerical consumer that has to multiply something by ``F_v``; it is
called by nothing that decides anything, and its docstring says so where a
reader meets it.

ONE FACTOR IS TODAY'S FAMILY, ENTRY FOR ENTRY: the product alphabet of one
factor is that factor's alphabet, the flattened map is that factor's map, and
the product block at one factor is that factor's block -- the join of a single
identifier is that identifier and the Kronecker product of one operand is that
operand.

ALICE'S SIDE ARRIVED WITH BATCH C3, AND IT IS NOT A FACTOR FAMILY
=================================================================
``{F_v}`` is a measurement on the MEASURED systems; Alice's own measurement slot
is a family of block lists over the factor tagged ``A``, in one of the two forms
``def:declaration`` (DX4) declares. :class:`AliceForm` is which slot is filled
and :class:`AliceSlot` is the slot, and they live beside the measured family
rather than inside it because no rule of the product reaches them: there is at
most one ``A`` factor, nothing is ever tensored along it, and the ensemble form's
condition is an identity with ``tau_A`` and not a completeness identity.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import product

from certiqs_key.foundations.blocks import (
    PRODUCT_LABEL_SEPARATOR,
    BlockOperator,
    FactorisedSectorMap,
    Label,
    SectorStructure,
    SystemTag,
    block_sum_in_declared_order,
    check_product_join,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Matrix, SummationVerdict, kron

__all__ = [
    "AliceForm",
    "AliceSlot",
    "FactorFamily",
    "FactorisedFamily",
]


class AliceForm(StrEnum):
    """WHICH OF THE TWO SLOTS of ``def:declaration`` (DX4) Alice's data fills.

    ``POVM`` is the accepted format's slot, ``{M_x}``, and is the degenerate
    value: a declaration that says what it said before says ``povm``. ``ENSEMBLE``
    is the other form, holding ``{N_x}`` with ``sum_x N_x^(t) =
    tau_A^(t)`` per Alice sector (``eq:ensembleform``), and it exists IN TRUSTED
    MODE ONLY -- an ensemble slot beside an empty marginal slot is refused, and
    the refusal is the consumer's (``ensemble_form_in_untrusted_mode``) rather
    than this type's, because which slot is filled is a declared fact and not a
    malformed argument.

    THE FORM IS READ AND NEVER CONVERTED. The POVM an ensemble form DENOTES,
    ``eq:ensemblepovm``, is "defined, in general irrational, and formed by no
    one"; nothing in ``domain/`` forms an inverse square root, a support
    projector or a rank, and no function here turns one form into the other.
    """

    POVM = "povm"
    ENSEMBLE = "ensemble"


@dataclass(frozen=True)
class AliceSlot:
    """Alice's measurement slot as BLOCK LISTS ALONG HER SECTORS (DX2), (DX4).

    ``members[i]`` is the block list of the ``i``-th letter of ``alphabet``, in
    the DECLARED ORDER -- the order ``def:exact`` (S) reads the per-sector sum in
    -- against the map of the factor tagged ``A``. With one Alice sector each
    member is the one matrix on ``A`` the accepted format declares, entry for
    entry, so ``AliceSlot`` at ``|T| = 1`` and ``form = povm`` IS today's
    ``alice_povm``.

    WHAT IS NOT A FIELD. The sector map is the members' own
    (:attr:`sectors`), as for :class:`FactorFamily`, so it is declared once; and
    ``tau_A`` is NOT here although the ensemble form's condition compares against
    it -- the marginal is a slot of the declaration in its own right, and a
    second copy beside the measurement would be a second source of truth for the
    object gate (G2) and check V2 both read.
    """

    form: AliceForm
    alphabet: tuple[Label, ...]
    members: tuple[BlockOperator, ...]

    def __post_init__(self) -> None:
        """Refuse a slot that is not a family over its own alphabet."""
        if not self.alphabet:
            raise MalformedInputError(
                "Alice's measurement slot is declared over a NON-EMPTY alphabet "
                "X; an empty one has no sum for def:exact (S) to decide"
            )
        if len(set(self.alphabet)) != len(self.alphabet):
            raise MalformedInputError(
                f"the signal alphabet {list(self.alphabet)} repeats a letter; an "
                "alphabet is a set listed in its declared order"
            )
        if len(self.members) != len(self.alphabet):
            raise MalformedInputError(
                f"a slot over an alphabet of {len(self.alphabet)} letters "
                f"carries that many block lists, not {len(self.members)}"
            )
        first = self.members[0].sector_map
        for index, member in enumerate(self.members):
            disagreement = first.disagreement(member.sector_map)
            if disagreement is not None:
                raise MalformedInputError(
                    f"the member {self.alphabet[index]!r} of Alice's slot is a "
                    f"block list against another map: {disagreement.detail}. "
                    "One slot is declared against ONE map, the factor tagged A's"
                )

    @classmethod
    def of(
        cls,
        form: AliceForm,
        alphabet: Sequence[Label],
        members: Sequence[BlockOperator],
    ) -> AliceSlot:
        """Return the slot whose members are ``members``, in declared order."""
        return cls(form=form, alphabet=tuple(alphabet), members=tuple(members))

    @property
    def sectors(self) -> SectorStructure:
        """Return the Alice sector map its members are block lists against."""
        return self.members[0].sector_map

    @property
    def is_ensemble(self) -> bool:
        """Whether the ensemble slot of (DX4) is the one that is filled."""
        return self.form is AliceForm.ENSEMBLE

    def member(self, letter: Label) -> BlockOperator:
        """Return the block list of one declared letter."""
        try:
            index = self.alphabet.index(letter)
        except ValueError as error:
            raise MalformedInputError(
                f"{letter!r} is not a letter of the declared alphabet "
                f"{list(self.alphabet)}"
            ) from error
        return self.members[index]

    def sums_per_sector(self) -> tuple[SummationVerdict, ...]:
        """Return the declared-order sum PER ALICE SECTOR, one verdict each.

        ``sum_x M_x^(t)`` in POVM form, which ``def:exact``'s general reading
        compares with ``1_{A_t}``, and ``sum_x N_x^(t)`` in ensemble form, which
        it compares with the declared ``tau_A^(t)`` (``eq:ensembleform``). ONE
        FUNCTION FOR BOTH, because the accumulation is the same accumulation and
        only the right-hand side differs: the comparison is the consumer's
        (check V3) and this returns the sum it decides (S) and (C) on.
        """
        return block_sum_in_declared_order(self.members)


@dataclass(frozen=True)
class FactorFamily:
    """One measured factor's declared family: its party, alphabet and blocks.

    ``members[i]`` is the block list of the ``i``-th letter of ``alphabet``, in
    the DECLARED ORDER -- the order the completeness sum is formed in
    (``def:exact`` (S)), which is not a set and must not be re-sorted.

    THE FACTOR'S SECTOR MAP IS NOT A FIELD HERE. It is the map's own: a
    :class:`FactorisedFamily` is built against a
    :class:`~certiqs_key.foundations.blocks.FactorisedSectorMap` and each family is
    matched to that map's measured factor at its position, so the map is
    declared once. What this type carries is what the map does not: the
    alphabet, and the operators.
    """

    party: Label
    alphabet: tuple[Label, ...]
    members: tuple[BlockOperator, ...]

    def __post_init__(self) -> None:
        """Refuse a family that is not a family over its own alphabet."""
        if not self.party:
            raise MalformedInputError(
                "a factor family carries a non-empty party label; the party is "
                "what scopes the factor it belongs to"
            )
        if not self.alphabet:
            raise MalformedInputError(
                "a declared family is over a NON-EMPTY alphabet; an empty one "
                "has no completeness sum to decide"
            )
        if len(set(self.alphabet)) != len(self.alphabet):
            raise MalformedInputError(
                f"the alphabet {list(self.alphabet)} of the factor scoped to "
                f"party {self.party!r} repeats a letter; an alphabet is a set "
                "listed in its declared order"
            )
        for letter in self.alphabet:
            if PRODUCT_LABEL_SEPARATOR in letter:
                raise MalformedInputError(
                    f"the outcome letter {letter!r} contains the declared "
                    f"product separator {PRODUCT_LABEL_SEPARATOR!r}, so the "
                    "product letter would not say which factor supplied which "
                    "part"
                )
        if len(self.members) != len(self.alphabet):
            raise MalformedInputError(
                f"a family over an alphabet of {len(self.alphabet)} letters "
                f"carries that many block lists, not {len(self.members)}"
            )

    @classmethod
    def of(
        cls,
        party: Label,
        alphabet: Sequence[Label],
        members: Sequence[BlockOperator],
    ) -> FactorFamily:
        """Return the family whose members are ``members``, in declared order."""
        return cls(party=party, alphabet=tuple(alphabet), members=tuple(members))

    @property
    def sectors(self) -> SectorStructure:
        """Return the map its members are block lists against."""
        return self.members[0].sector_map

    def member(self, letter: Label) -> BlockOperator:
        """Return the block list of one declared letter."""
        try:
            index = self.alphabet.index(letter)
        except ValueError as error:
            raise MalformedInputError(
                f"{letter!r} is not a letter of the declared alphabet "
                f"{list(self.alphabet)}"
            ) from error
        return self.members[index]


@dataclass(frozen=True)
class FactorisedFamily:
    """``{F_v}`` as one family per measured factor, plus the product rule.

    THE PRODUCT IS NEVER A DATUM. ``factors[i]`` is the declared family of the
    ``i``-th MEASURED factor of ``sector_map`` -- ``sector_map.factors_of(Q)``,
    in the product order -- and ``F_v`` is defined by the rule, not stored. The
    module docstring says whose decision that is and what it avoids.

    THE PRODUCT ORDER IS THE MAP'S, for the alphabet exactly as for the
    sectors: the last factor runs fastest and a product letter is the factors'
    letters joined by
    :data:`~certiqs_key.foundations.blocks.PRODUCT_LABEL_SEPARATOR`, which is the
    convention a product SECTOR identifier already uses. One convention and one
    separator for both, so that a reader of ``v0__d1`` reads it the way it
    reads ``s0__t1``, and a consumer can take a product identifier apart the
    same way in both cases.

    THE ``A`` FACTOR IS HANDED NO FAMILY. ``{F_v}`` is a measurement on the
    measured systems; the retained system carries ``{M_x}`` and ``tau_A``,
    which are block lists over the ``A`` factor and not members of this type
    (:class:`~certiqs_key.foundations.blocks.BlockOperator` serves them directly).
    A family list as long as the whole product is refused, naming that.
    """

    sector_map: FactorisedSectorMap
    factors: tuple[FactorFamily, ...]

    def __post_init__(self) -> None:
        """Refuse a factor list that is not the measured factors of its map."""
        measured = self.sector_map.factors_of(SystemTag.Q)
        if not measured:
            raise MalformedInputError(
                "a declared family is over AT LEAST ONE measured factor; this "
                f"sector map has only {[tag.value for tag in self.sector_map.systems]}"
            )
        if len(self.factors) != len(measured):
            retained = self.sector_map.factors_of(SystemTag.A)
            if retained and len(self.factors) == len(self.sector_map.factors):
                raise MalformedInputError(
                    f"the {SystemTag.A.value!r} factor is handed no family: "
                    "{F_v} is a measurement on the MEASURED systems, and the "
                    "retained system carries {M_x} and tau_A, which are block "
                    "lists over the A factor and not members of this family. "
                    f"This map has {len(measured)} measured factor(s) and was "
                    f"given {len(self.factors)} families"
                )
            raise MalformedInputError(
                f"a factorised family carries ONE family per measured factor: "
                f"{len(measured)} against the {len(self.factors)} supplied"
            )
        # The product LETTER is joined by the same separator as the product
        # sector identifier, so the same injectivity rule binds it: the
        # containment half is refused per factor by FactorFamily, and this is
        # the half about a pair of adjacent factors.
        check_product_join(
            [family.alphabet for family in self.factors], what="outcome letter"
        )
        for position, (factor, family) in enumerate(
            zip(measured, self.factors, strict=True)
        ):
            if factor.party != family.party:
                raise MalformedInputError(
                    f"the family at position {position} is scoped to party "
                    f"{family.party!r} where the map's measured factor at that "
                    f"position is scoped to {factor.party!r}; the families are "
                    "matched to the factors IN THE PRODUCT ORDER, and a list "
                    "in another order is refused rather than reordered"
                )
            for index, member in enumerate(family.members):
                disagreement = factor.sectors.disagreement(member.sector_map)
                if disagreement is not None:
                    raise MalformedInputError(
                        f"the member {family.alphabet[index]!r} of the family "
                        f"at position {position} is a block list against "
                        f"another map: {disagreement.detail}"
                    )

    @classmethod
    def of(
        cls, sector_map: FactorisedSectorMap, families: Sequence[FactorFamily]
    ) -> FactorisedFamily:
        """Return the family of ``families``, matched to the measured factors."""
        return cls(sector_map=sector_map, factors=tuple(families))

    @classmethod
    def single_factor(
        cls, party: Label, sectors: SectorStructure, family: FactorFamily
    ) -> FactorisedFamily:
        """Return the one-factor family: today's format, said in the new shape."""
        return cls(
            sector_map=FactorisedSectorMap.single_factor(party, sectors),
            factors=(family,),
        )

    @property
    def count(self) -> int:
        """Return the number of measured factors."""
        return len(self.factors)

    def factor(self, position: int) -> FactorFamily:
        """Return the family of one measured factor, by its product position."""
        return self.factors[position]

    def flattened(self) -> SectorStructure:
        """Return the product sector map, DELEGATING to the factorised map.

        It is ``sector_map.flattened_of(Q)`` and nothing of its own: the map is
        declared in one place, and a second flattening here would be a second
        convention waiting to disagree with the first. With one factor it is
        that factor's map, entry for entry.
        """
        measured = self.sector_map.flattened_of(SystemTag.Q)
        if measured is None:  # pragma: no cover - __post_init__ refuses it
            raise MalformedInputError("a declared family has a measured side")
        return measured

    def product_letters(self) -> tuple[tuple[Label, ...], ...]:
        """Return the factors' letters behind each product letter, in order.

        The same product order as :meth:`alphabet` and in the same positions,
        so a consumer that wants the factors of ``v`` reads them here rather
        than splitting a joined string back apart.
        """
        return tuple(product(*(family.alphabet for family in self.factors)))

    def alphabet(self) -> tuple[Label, ...]:
        """Return the product alphabet ``prod_f V^f``, the last factor fastest.

        A product letter is the factors' letters joined by
        :data:`~certiqs_key.foundations.blocks.PRODUCT_LABEL_SEPARATOR`, in the
        product order -- the convention the flattened SECTOR identifier already
        uses, and the reason a factor letter may not contain the separator.
        With one factor this is that factor's alphabet, letter for letter.
        """
        return tuple(
            PRODUCT_LABEL_SEPARATOR.join(letters)
            for letters in self.product_letters()
        )

    def completeness_per_factor(self) -> tuple[tuple[SummationVerdict, ...], ...]:
        """Return each factor's per-sector completeness sum, in declared order.

        PER FACTOR AND PER BLOCK, by the function
        :func:`~certiqs_key.foundations.blocks.block_sum_in_declared_order` that
        already decides it: the largest array touched is one block of one
        factor. That the PRODUCT is then complete is
        ``reductions/thm:emitted-product`` (i) -- ``sum_v (x)_f F^f_{v_f} =
        (x)_f sum_{v_f} F^f_{v_f}`` by multilinearity -- which is a theorem and
        not a computation this type performs.
        """
        return tuple(
            block_sum_in_declared_order(family.members) for family in self.factors
        )

    def is_hermitian(self) -> bool:
        """Whether every member of every factor is Hermitian, decided per block.

        Per factor, per member, per block, with
        :meth:`~certiqs_key.foundations.blocks.BlockOperator.is_hermitian`. The
        product's Hermiticity follows by ``thm:emitted-product`` (i); no
        product is formed to decide it.
        """
        return all(
            member.is_hermitian()
            for family in self.factors
            for member in family.members
        )

    def is_positive_semidefinite(self) -> bool:
        """Whether every member of every factor is PSD, decided per block.

        As :meth:`is_hermitian`: the product's positivity is
        ``thm:emitted-product`` (i), a theorem about the factors' exact
        numbers, and is never decided on an array of product size.
        """
        return all(
            member.is_positive_semidefinite()
            for family in self.factors
            for member in family.members
        )

    def product_block(self, outcome: int, sector: int) -> Matrix:
        """Return the block of ``F_v`` at one product sector, as the Kronecker product.

        FORMED BY NO PREDICATE OF THIS TIER, and that is the whole point of the
        type: every admission decision above runs per factor, on arrays of a
        factor's size. This is here for a NUMERICAL CONSUMER -- the engine that
        has to multiply a state by ``F_v`` -- and the arithmetic is the exact
        one the rest of ``domain/`` uses
        (:func:`~certiqs_key.foundations.exact.kron`), so nothing rounds here
        either.

        ``outcome`` and ``sector`` are positions in :meth:`alphabet` and in
        :meth:`flattened`, which are the same product order; the block is
        ``(x)_f F^{f,(s_f)}_{v_f}`` in the factors' order, which is
        ``thm:emitted-product`` (i)'s block at ``s = (s_f)_f``.
        """
        letters = self.product_letters()[outcome]
        sectors = tuple(
            product(*(family.sectors.labels for family in self.factors))
        )[sector]
        blocks = [
            family.member(letter).blocks[family.sectors.labels.index(sector_label)]
            for family, letter, sector_label in zip(
                self.factors, letters, sectors, strict=True
            )
        ]
        total = blocks[0]
        for block in blocks[1:]:
            total = kron(total, block)
        return total
