"""The declaration of the GENERAL FORMAT, ``def:declaration`` (DX1)-(DX6).

The accepted format is the case ``|T| = 1``, one measured factor, POVM form,
``L = 2`` and no ``party_local`` entry, **entry for entry**, and this module
keeps that reading literally: :meth:`GeneralDeclaration.is_degenerate` decides
it, :func:`general_from_accepted` embeds an accepted
:class:`~certiqs_key.meat_core.declaration.declaration.ProtocolDeclaration` as
the general declaration it is, and :meth:`GeneralDeclaration.as_accepted` is
the inverse on the degenerate case. ONE DRIVER RUNS BOTH: an accepted-format
declaration is solved as its embedding, by the same loop and into the same
record as every other one, so the degenerate-case identity is one code path and
not two that agree numerically.

WHAT IS DECLARED AND WHAT IS DERIVED
====================================
(DX1) the factor list is declared; the product sector map, the product outcome
alphabet and the joint sectors ``(t, s)`` are DERIVED here. (DX3) one family of
block lists per measured factor is declared and **no product datum is**: the
Kronecker block ``F_v^{(s)} = (x)_f F^{f,(s_f)}_{v_f}`` is formed in floating
point by :meth:`GeneralDeclaration.bob_block`, which the objective calls and no
predicate does -- the zero test of ``def:joint-sectors`` runs per factor
(:meth:`GeneralDeclaration.bob_block_is_zero`). (DX4) Alice's slot holds either
``{M_x}`` (POVM form) or ``{N_x}`` (ensemble form); in ensemble form neither
``{M_x}`` of ``eq:ensemblepovm`` nor an inverse square root of ``tau_A`` nor a
rank is ever formed, and what the objective reads is the declared ``N_x``
(``lem:choi-factor`` (iii), (iv)). (DX5) the transcript is declared and the
joint announcement function ``a`` is derived by composition (``eq:transcript``).
(DX6) an entry carries its scope and its tag, and the lifted operator
``1 (x) O_k (x) 1`` is never formed as a declared datum. Numerical row
assembly may materialize it in the optimization coordinates.

WHAT THIS MODULE DOES NOT DECIDE
================================
Nothing. It is data plus derivations of declared data;
:mod:`certiqs_key.meat_core.declaration.general_validation` decides
def:admissible-declaration in the general format and owns every refusal.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property
from itertools import product
from types import MappingProxyType

import numpy as np

from certiqs_key.domain.manifest import ConstraintRelation, KeyHolder, PartyLabel
from certiqs_key.foundations.blocks import PRODUCT_LABEL_SEPARATOR, SystemTag
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    ConstraintEntry,
    KeyLengthParameters,
    PartyPartition,
    ProtocolDeclaration,
    RhsTag,
    SourceMode,
)
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix

#: The separator a product identifier is joined by. ONE SPELLING, the shared
#: one (``spec/architecture.md`` 2.9), so that a product label this module
#: derives is the label ``domain/`` would flatten to.
SEPARATOR = PRODUCT_LABEL_SEPARATOR


class AliceForm(StrEnum):
    """Which of the two slots of ``def:declaration`` (DX4) is filled."""

    #: ``{M_x}``, a POVM on ``A`` -- the accepted format's slot.
    POVM = "povm"
    #: ``{N_x}`` with ``sum_x N_x^{(t)} = tau_A^{(t)}`` and ``tau_A^{(t)} != 0``
    #: (``eq:ensembleform``). TRUSTED-SOURCE MODE ONLY, and
    #: ``general_validation`` refuses it in the other mode.
    ENSEMBLE = "ensemble"


class GeneralRhsTag(StrEnum):
    """The DECLARED form of an entry's right-hand side, ``def:homog``.

    The two accepted tags plus the third licensed form of the general format.
    Licensing stays a TYPE check on the declared tag and compares no numbers.
    """

    HOMOGENEOUS = "homogeneous"
    GENERAL = "general"
    #: ``(O_k, bowtie_k, c_k; f)`` of ``eq:partylocal-entry``, licensed in
    #: EITHER source mode, carrying the OPERATOR relation symbols in either
    #: (``def:homog``, the relation-symbol clause).
    PARTY_LOCAL = "party_local"


def _product_parts(axes: tuple[tuple[str, ...], ...]) -> dict[str, tuple[str, ...]]:
    """Invert the declared Cartesian product, refusing colliding identifiers.

    Even a factor label without the full separator may end in its prefix;
    splitting joined strings then loses part of that opaque label. Enumeration
    preserves exactly the supplier's labels and declared product order.
    """
    result: dict[str, tuple[str, ...]] = {}
    for parts in product(*axes):
        label = SEPARATOR.join(parts)
        if label in result:
            raise DeclarationError(
                "declared factor products have colliding identifiers"
            )
        result[label] = parts
    return result


@dataclass(frozen=True)
class SectorAxis:
    """One factor's own sector map: ordered identifiers with their dimensions.

    ``def:declaration`` (DX1): a factor carries "a sector map of its own, an
    ordered list of block identifiers with their dimensions".
    """

    labels: tuple[str, ...]
    dims: Mapping[str, int]

    def __post_init__(self) -> None:
        """Freeze the axis: ``labels`` a tuple, ``dims`` a read-only copy.

        The declaration caches values derived from it (sector dimensions, the
        product sector tables), so an in-place write after first use would
        leave them stale. A copy is taken, so a caller's own dict stays theirs.
        """
        object.__setattr__(self, "labels", tuple(self.labels))
        object.__setattr__(self, "dims", MappingProxyType(dict(self.dims)))

    @property
    def count(self) -> int:
        """Return how many blocks this axis has."""
        return len(self.labels)

    @property
    def total_dim(self) -> int:
        """Return the sum of the block dimensions."""
        return sum(self.dims[label] for label in self.labels)


@dataclass(frozen=True)
class AliceFactor:
    """The factor tagged ``A`` of (DX1): the index set ``T`` and ``d_{A_t}``.

    Absent from a declaration, ``T = {t_0}`` and ``A_{t_0} = A``, which is what
    :func:`single_alice_factor` builds.
    """

    party: PartyLabel
    sectors: SectorAxis
    system: SystemTag = SystemTag.A


@dataclass(frozen=True)
class MeasuredFactor:
    """One factor tagged ``Q`` of (DX1), with its own family of (DX3).

    ``blocks[v_f][s_f]`` is ``F^{f,(s_f)}_{v_f}``, declared against THIS
    factor's sector map and over THIS factor's ordered alphabet. Nothing here
    is a product.
    """

    label: str
    party: PartyLabel
    sectors: SectorAxis
    alphabet: tuple[str, ...]
    blocks: Mapping[str, Mapping[str, Matrix]]
    system: SystemTag = SystemTag.Q


@dataclass(frozen=True)
class Message:
    """One message of the transcript protocol, ``def:declaration`` (DX5).

    ``table[(readout, earlier)]`` is
    ``a_m(pi_{pi_m}(x, v), kappa_1, ..., kappa_{m-1})``: a function of its
    SENDER'S readout and of the earlier messages of the same round, and of
    nothing else. The type is what enforces that -- a table keyed by the other
    party's readout cannot be written.
    """

    sender: KeyHolder
    alphabet: tuple[str, ...]
    table: Mapping[tuple[str, tuple[str, ...]], str]

    def letter(self, readout: str, earlier: tuple[str, ...]) -> str:
        """Return ``kappa_m``; raise ``KeyError`` for a table that is not total."""
        return self.table[(readout, earlier)]


@dataclass(frozen=True)
class Transcript:
    """The ordered message list of (DX5), with ``a`` DERIVED by composition.

    ``eq:transcript``. The two accepted announcement maps are the case
    ``L = 2``, ``pi = (A, B)``, ``a_1 = a_A`` and
    ``a_2(o, kappa_1) = a_B(o)``, which :func:`two_message_transcript` builds
    and :attr:`is_two_independent_messages` recognises.
    """

    messages: tuple[Message, ...]

    @property
    def length(self) -> int:
        """Return ``L``."""
        return len(self.messages)

    @property
    def is_two_independent_messages(self) -> bool:
        """Return whether this transcript IS the accepted format's pair.

        ``L = 2``, the first sender Alice, the second Bob, and the second
        table independent of the first message -- which is the degenerate case
        (DX5) names, and the condition under which the accepted format's
        ``announce_alice`` and ``announce_bob`` exist as maps.
        """
        if self.length != 2:
            return False
        first, second = self.messages
        if first.sender is not KeyHolder.ALICE or second.sender is not KeyHolder.BOB:
            return False
        by_readout: dict[str, set[str]] = {}
        for (readout, _earlier), letter in second.table.items():
            by_readout.setdefault(readout, set()).add(letter)
        return all(len(letters) == 1 for letters in by_readout.values())

    def announcement(self, readouts: Mapping[KeyHolder, str]) -> tuple[str, ...]:
        """Return ``a(x, v) = (kappa_m)_{m=1..L}`` of ``eq:transcript``."""
        letters: tuple[str, ...] = ()
        for message in self.messages:
            letters = (*letters, message.letter(readouts[message.sender], letters))
        return letters


@dataclass(frozen=True)
class GeneralConstraintEntry:
    """One entry of ``L`` in the general format, ``def:declaration`` (DX6).

    ``operator_blocks[s_f]`` is ``O_k`` against the sector map of its SCOPE,
    one measured factor; the lifted operator ``1 (x) O_k (x) 1`` is never
    formed. ``bound`` is the real ``c_k`` under ``homogeneous`` and
    ``party_local`` and the Hermitian block list ``Theta_k^{(t)}`` under
    ``general`` (DX2).
    """

    scope: str
    operator_blocks: Mapping[str, Matrix]
    relation: ConstraintRelation
    bound: float | Mapping[str, Matrix]
    rhs_tag: GeneralRhsTag

    @property
    def is_party_local(self) -> bool:
        """Return whether the entry carries the third licensed form."""
        return self.rhs_tag is GeneralRhsTag.PARTY_LOCAL

    @property
    def scalar_bound(self) -> float:
        """Return ``c_k``; raise for an entry that declares an operator."""
        if isinstance(self.bound, Mapping):
            raise TypeError(
                "this entry is tagged `general` and carries the block list "
                "Theta_k^(t); there is no scalar c_k to read"
            )
        return float(self.bound)

    def operator_bound(self, alice_sector: str) -> Matrix:
        """Return the DECLARED ``Theta_k^{(t)}``; raise for a scalar entry.

        THE DECLARED ONE, NOT A CONSTRUCTED ONE: a ``homogeneous`` entry's
        right-hand side is BUILT as ``c_k tau_A^{(t)}``
        (:meth:`GeneralDeclaration.right_hand_side`), and returning
        ``c_k 1_{A_t}`` here would be the unlicensed reading of
        ``rem:homog`` (a).
        """
        if not isinstance(self.bound, Mapping):
            raise TypeError(
                "this entry carries the scalar c_k; there is no declared "
                "Theta_k^(t) to read. Use right_hand_side, which CONSTRUCTS "
                "c_k tau_A^(t)"
            )
        return as_matrix(self.bound[alice_sector])


def single_alice_factor(alice_dim: int, *, label: str = "t0") -> AliceFactor:
    """Return the ``T = {t_0}`` of (DX1) for a declaration with no ``A`` factor."""
    return AliceFactor(
        party=PartyLabel.ALICE,
        sectors=SectorAxis(labels=(label,), dims={label: alice_dim}),
    )


def two_message_transcript(
    announce_alice: Mapping[str, str], announce_bob: Mapping[str, str]
) -> Transcript:
    """Return the ``L = 2`` transcript the two accepted announcement maps are.

    ``def:declaration`` (DX5): ``a_1 = a_A`` and
    ``a_2(o, kappa_1) = a_B(o)`` -- the second table reads its sender's
    readout and ignores the first message, which is what makes the two maps
    "neither of which reads the other".
    """
    first_letters = tuple(dict.fromkeys(announce_alice.values()))
    return Transcript(
        messages=(
            Message(
                sender=KeyHolder.ALICE,
                alphabet=first_letters,
                table={(x, ()): c for x, c in announce_alice.items()},
            ),
            Message(
                sender=KeyHolder.BOB,
                alphabet=tuple(dict.fromkeys(announce_bob.values())),
                table={
                    (v, (c,)): announce_bob[v]
                    for v in announce_bob
                    for c in first_letters
                },
            ),
        )
    )


@dataclass(frozen=True)
class GeneralDeclaration:
    """The declaration ``D`` in the general format of ``def:declaration``.

    Construction performs no validation, as on the accepted path:
    :func:`certiqs_key.meat_core.declaration.general_validation.validate_general_declaration`
    decides def:admissible-declaration in the general format and every refusal is its.

    THE SOURCE MODE IS DERIVED from the marginal slot and has no field, which
    is the accepted path's rule and the same one bit fourteen statements branch
    on.
    """

    alice: AliceFactor
    #: ``tau_A`` as the block list ``tau_A^{(t)}`` of (DX2), or ``None`` for
    #: untrusted-source mode.
    alice_marginal: Mapping[str, Matrix] | None
    alice_alphabet: tuple[str, ...]
    #: ``M_x^{(t)}`` in POVM form, ``N_x^{(t)}`` in ensemble form: the DECLARED
    #: operators of (DX4), keyed ``[x][t]``.
    alice_operators: Mapping[str, Mapping[str, Matrix]]
    alice_form: AliceForm
    factors: tuple[MeasuredFactor, ...]
    transcript: Transcript
    #: ``phi``, keyed by the DERIVED transcript tuple.
    accept_statistic: Mapping[tuple[str, ...], str]
    #: ``r``, keyed by ``(x, v)`` with ``v`` the PRODUCT letter.
    key_map: Mapping[tuple[str, str], int | None]
    key_holder: KeyHolder
    acceptance_values: tuple[str, ...]
    key_value_count: int
    acceptance_set: AcceptanceSet
    rounds: int
    parameters: KeyLengthParameters
    party_partition: PartyPartition | None = None
    sector_block_kind: str | None = None
    constraint_list: tuple[GeneralConstraintEntry, ...] = ()
    constraints_through_a_reductions_chain: int = 0
    attack_set_license: Mapping[str, object] | None = None
    source_replacement_license: Mapping[str, object] | None = None
    #: The Kronecker cache of (DX3). NOT DECLARED DATA: it holds what the
    #: objective asked for, in floating point, and is keyed by the pair of
    #: product labels it was asked at.
    _product_cache: dict[tuple[str, str], Matrix] = field(
        default_factory=dict, compare=False, repr=False
    )

    # -- the two source modes -------------------------------------------------

    @property
    def source_mode(self) -> SourceMode:
        """Return the DERIVED source mode (``rem:modes-da1``)."""
        if self.alice_marginal is None:
            return SourceMode.UNTRUSTED
        return SourceMode.TRUSTED

    @property
    def is_trusted_source(self) -> bool:
        """Return whether a trusted marginal is declared."""
        return self.source_mode is SourceMode.TRUSTED

    def marginal_block(self, alice_sector: str) -> Matrix:
        """Return ``tau_A^{(t)}``; raise in untrusted-source mode."""
        if self.alice_marginal is None:
            raise TypeError(
                "this declaration is in untrusted-source mode: the marginal "
                "slot holds `none` and there is no tau_A^(t). Nothing may "
                "stand in for it (def:untrusted-choi (b))"
            )
        return as_matrix(self.alice_marginal[alice_sector])

    # -- (DX1): the derived maps ---------------------------------------------

    @property
    def alice_sectors(self) -> tuple[str, ...]:
        """Return ``T`` in its declared order."""
        return self.alice.sectors.labels

    def alice_dim_of(self, alice_sector: str) -> int:
        """Return ``d_{A_t}``."""
        return self.alice.sectors.dims[alice_sector]

    @property
    def alice_dim(self) -> int:
        """Return ``d_A = sum_t d_{A_t}``."""
        return self.alice.sectors.total_dim

    # The derived tuples below are CACHED on first access. The declaration is
    # frozen and every input they read (the factor list, each factor's
    # labels, alphabet and dimensions, the Alice axis) is an immutable tuple
    # or a mapping nothing writes after construction, so a cached value
    # cannot go stale; ``dataclasses.replace`` builds a new declaration with
    # an empty cache. The joint-format objective reads them tens of
    # thousands of times per solve, and rebuilding them is measurable.

    @cached_property
    def sector_index_set(self) -> tuple[str, ...]:
        """Return ``S = prod_f S^f`` of ``eq:productmap``, last factor fastest.

        A product identifier is the factors' identifiers joined by the one
        declared separator, which is why a factor identifier may not contain
        it (``general_validation`` refuses one that does).
        """
        labels: tuple[tuple[str, ...], ...] = ((),)
        for factor in self.factors:
            labels = tuple(
                (*prefix, label) for prefix in labels for label in factor.sectors.labels
            )
        return tuple(SEPARATOR.join(parts) for parts in labels)

    @property
    def sector_dims(self) -> Mapping[str, int]:
        """Return ``d_s = prod_f d_{f,s_f}`` of ``eq:productmap``, a fresh dict."""
        return dict(self._sector_dim_table)

    @cached_property
    def _sector_dim_table(self) -> Mapping[str, int]:
        return MappingProxyType(
            {sector: self._product_dim(sector) for sector in self.sector_index_set}
        )

    def sector_dim(self, sector: str) -> int:
        """Return ``d_s`` of one product sector without building the full map."""
        return self._sector_dim_table[sector]

    def _product_dim(self, sector: str) -> int:
        product = 1
        for factor, part in zip(self.factors, self.split_sector(sector), strict=True):
            product *= factor.sectors.dims[part]
        return product

    @cached_property
    def _sector_parts(self) -> Mapping[str, tuple[str, ...]]:
        return _product_parts(tuple(f.sectors.labels for f in self.factors))

    @cached_property
    def _letter_parts(self) -> Mapping[str, tuple[str, ...]]:
        return _product_parts(tuple(f.alphabet for f in self.factors))

    def split_sector(self, sector: str) -> tuple[str, ...]:
        """Look up a product sector against the declared factor order."""
        return self._sector_parts[sector]

    def split_letter(self, letter: str) -> tuple[str, ...]:
        """Look up opaque factor letters; never parse separator substrings."""
        return self._letter_parts[letter]

    @cached_property
    def joint_sectors(self) -> tuple[tuple[str, str], ...]:
        """Return the joint sectors ``(t, s)`` of (DX1), ``t`` SLOWEST."""
        return tuple(
            (alice_sector, sector)
            for alice_sector in self.alice_sectors
            for sector in self.sector_index_set
        )

    def joint_block_dim(self, alice_sector: str, sector: str) -> int:
        """Return ``d_{A_t} d_s``, the size of the block of one joint sector."""
        return self.alice_dim_of(alice_sector) * self.sector_dim(sector)

    # -- (DX3): the factorised family ----------------------------------------

    @cached_property
    def bob_outcomes(self) -> tuple[str, ...]:
        """Return ``V = prod_f V^f`` in the product order, last factor fastest."""
        letters: tuple[tuple[str, ...], ...] = ((),)
        for factor in self.factors:
            letters = tuple(
                (*prefix, letter) for prefix in letters for letter in factor.alphabet
            )
        return tuple(SEPARATOR.join(parts) for parts in letters)

    def bob_block(self, letter: str, sector: str) -> Matrix:
        """Return ``F_v^{(s)}`` of ``eq:productfamily``, FORMED HERE.

        The one place a product of the declared per-factor blocks becomes an
        array. It is floating point, it is not declared data, no exact
        predicate reads it, and nothing snaps it (``def:declaration`` (DX3),
        and the ``bob_povm.per_factor`` input row). With one measured factor
        it IS the declared block, returned without a Kronecker product.
        """
        parts = self.split_letter(letter)
        sector_parts = self.split_sector(sector)
        if len(self.factors) == 1:
            return as_matrix(self.factors[0].blocks[parts[0]][sector_parts[0]])
        cached = self._product_cache.get((letter, sector))
        if cached is not None:
            return cached
        block = as_matrix(self.factors[0].blocks[parts[0]][sector_parts[0]])
        for factor, part, sector_part in zip(
            self.factors[1:], parts[1:], sector_parts[1:], strict=True
        ):
            block = np.asarray(
                np.kron(block, as_matrix(factor.blocks[part][sector_part])),
                dtype=np.complex128,
            )
        self._product_cache[(letter, sector)] = block
        return block

    def bob_block_is_zero(self, letter: str, sector: str) -> bool:
        """Return whether ``F_v^{(s)} = 0``, DECIDED PER FACTOR.

        ``def:joint-sectors``, "Decided on declared data": a tensor product of
        matrices vanishes exactly when one of them does, so the predicate is
        decided on the declared factor blocks and NO PRODUCT IS FORMED.
        """
        parts = self.split_letter(letter)
        sector_parts = self.split_sector(sector)
        for factor, part, sector_part in zip(
            self.factors, parts, sector_parts, strict=True
        ):
            if not np.any(as_matrix(factor.blocks[part][sector_part]) != 0.0):
                return True
        return False

    # -- (DX4): Alice's slot --------------------------------------------------

    @property
    def is_ensemble_form(self) -> bool:
        """Return whether Alice's slot holds ``{N_x}`` (``eq:ensembleform``)."""
        return self.alice_form is AliceForm.ENSEMBLE

    def alice_block(self, letter: str, alice_sector: str) -> Matrix:
        """Return the DECLARED block of Alice's slot: ``M_x^{(t)}`` or ``N_x^{(t)}``."""
        return as_matrix(self.alice_operators[letter][alice_sector])

    def alice_block_is_zero(self, letter: str, alice_sector: str) -> bool:
        """Return whether Alice's operator vanishes on ``A_t``.

        In POVM form this is ``M_x^{(t)} = 0`` and in ensemble form
        ``N_x^{(t)} = 0``, which decide the same thing by
        ``lem:ensemble-form`` (iii) -- the reason that lemma splits the
        completion in proportion to ``tr N_x`` at all. Either way it is a
        comparison of a DECLARED block with the zero block.
        """
        return not bool(np.any(self.alice_block(letter, alice_sector) != 0.0))

    # -- (DX5), (DX6) and the rest of the tuple ------------------------------

    def readouts(self, x: str, v: str) -> Mapping[KeyHolder, str]:
        """Return the declared readouts, defaulting to ``pi_A=x, pi_B=v``."""
        if self.party_partition is not None:
            return {
                KeyHolder.ALICE: self.party_partition.readout_alice[(x, v)],
                KeyHolder.BOB: self.party_partition.readout_bob[(x, v)],
            }
        return {KeyHolder.ALICE: x, KeyHolder.BOB: v}

    def announcement(self, x: str, v: str) -> tuple[str, ...]:
        """Return ``a(x, v)`` of ``eq:transcript``."""
        return self.transcript.announcement(self.readouts(x, v))

    def acceptance_value(self, x: str, v: str) -> str:
        """Return ``phi(a(x, v))``."""
        return self.accept_statistic[self.announcement(x, v)]

    def raw_key(self, x: str, v: str) -> int | None:
        """Return ``r(x, v)``, with ``None`` for sifting failure."""
        return self.key_map[(x, v)]

    def right_hand_side(self, index: int, alice_sector: str) -> Matrix:
        """Return ``Theta_k^{(t)}``, CONSTRUCTED for the licensed forms.

        ``def:homog`` (a) in the general format: a ``homogeneous`` entry
        declares ``c_k`` and its right-hand side is BUILT as
        ``c_k tau_A^{(t)}``, so ``eq:transport`` and ``eq:feas-general`` carry
        one expression in the same declared numbers. A ``general`` entry
        imposes the block it declares. A ``party_local`` entry has no
        right-hand side of this shape at all: ``eq:partylocal-entry`` compares
        against ``0``.
        """
        entry = self.constraint_list[index]
        if entry.rhs_tag is GeneralRhsTag.GENERAL:
            return entry.operator_bound(alice_sector)
        if entry.is_party_local:
            raise TypeError(
                "a party_local entry's reading is eq:partylocal-entry, an "
                "operator relation against 0 on the systems other than its "
                "scope; it has no Theta_k^(t)"
            )
        return entry.scalar_bound * self.marginal_block(alice_sector)

    @property
    def has_party_local_entry(self) -> bool:
        """Return whether ``L`` carries an entry declared ``party_local``."""
        return any(entry.is_party_local for entry in self.constraint_list)

    # -- the degenerate case, which is the accepted format -------------------

    @property
    def is_degenerate(self) -> bool:
        """Return whether this declaration IS one of the accepted format.

        ``|T| = 1``, one measured factor, POVM form, ``L = 2`` with two
        independent messages, and no ``party_local`` entry: the five
        conditions ``def:declaration``'s general-format paragraph names, at
        which "every object defined in (DX1)--(DX6) is the object of the same
        name above, and nothing else is declared".
        """
        return (
            len(self.alice_sectors) == 1
            and len(self.factors) == 1
            and self.alice_form is AliceForm.POVM
            and self.transcript.is_two_independent_messages
            and not self.has_party_local_entry
        )

    def as_accepted(self) -> ProtocolDeclaration:
        """Return the accepted-format declaration this one IS, or raise.

        The inverse of :func:`general_from_accepted` on the degenerate case:
        ``def:declaration``'s general-format paragraph says every object of
        (DX1)--(DX6) is then the accepted object of the same name, and this
        reading is what the embedding tests hold both directions against. No
        solve routes through it (one driver runs both formats). A declaration
        that is not degenerate has no accepted-format reading and raises
        rather than being approximated by one.
        """
        if not self.is_degenerate:
            raise TypeError(
                "this declaration is not of the accepted format: it has "
                f"{len(self.alice_sectors)} Alice sector(s), "
                f"{len(self.factors)} measured factor(s), Alice's slot in "
                f"{self.alice_form.value} form, a transcript of "
                f"{self.transcript.length} message(s) and "
                f"{'a' if self.has_party_local_entry else 'no'} party_local "
                "entry. Only |T| = 1, one factor, POVM form, two independent "
                "messages and no party_local entry is the accepted format"
            )
        (alice_sector,) = self.alice_sectors
        factor = self.factors[0]
        first, second = self.transcript.messages
        announce_alice = {
            readout: letter for (readout, _), letter in first.table.items()
        }
        announce_bob = {
            readout: letter for (readout, _), letter in second.table.items()
        }
        pairs = [(x, v) for x in self.alice_alphabet for v in factor.alphabet]
        return ProtocolDeclaration(
            alice_dim=self.alice_dim_of(alice_sector),
            alice_marginal=(
                None
                if self.alice_marginal is None
                else self.marginal_block(alice_sector)
            ),
            sector_index_set=factor.sectors.labels,
            sector_dims=dict(factor.sectors.dims),
            alice_povm={
                x: self.alice_block(x, alice_sector) for x in self.alice_alphabet
            },
            bob_povm={
                v: {s: as_matrix(factor.blocks[v][s]) for s in factor.sectors.labels}
                for v in factor.alphabet
            },
            announce_alice=announce_alice,
            announce_bob=announce_bob,
            accept_statistic={
                (announce_alice[x], announce_bob[v]): self.acceptance_value(x, v)
                for x, v in pairs
            },
            key_map={(x, v): self.raw_key(x, v) for x, v in pairs},
            key_holder=self.key_holder,
            acceptance_values=self.acceptance_values,
            key_value_count=self.key_value_count,
            acceptance_set=self.acceptance_set,
            rounds=self.rounds,
            parameters=self.parameters,
            sector_block_kind=self.sector_block_kind,
            constraint_list=tuple(
                ConstraintEntry(
                    operator_blocks={
                        s: as_matrix(entry.operator_blocks[s])
                        for s in factor.sectors.labels
                    },
                    relation=entry.relation,
                    bound=(
                        entry.operator_bound(alice_sector)
                        if entry.rhs_tag is GeneralRhsTag.GENERAL
                        else entry.scalar_bound
                    ),
                    rhs_tag={
                        GeneralRhsTag.GENERAL: RhsTag.GENERAL,
                        GeneralRhsTag.HOMOGENEOUS: RhsTag.HOMOGENEOUS,
                    }[entry.rhs_tag],
                )
                for entry in self.constraint_list
            ),
            constraints_through_a_reductions_chain=(
                self.constraints_through_a_reductions_chain
            ),
            attack_set_license=self.attack_set_license,
            source_replacement_license=self.source_replacement_license,
            party_partition=self.party_partition,
        )


def general_from_accepted(declaration: ProtocolDeclaration) -> GeneralDeclaration:
    """Return the degenerate general declaration an accepted one IS.

    The inverse of :meth:`GeneralDeclaration.as_accepted` on the degenerate
    case, and the embedding ``def:declaration``'s general-format paragraph
    states: one Alice sector, one measured factor, POVM form, the two
    announcement maps as the ``L = 2`` transcript, no ``party_local`` entry.
    Every derived object it carries is the object of the same name in the
    accepted declaration, which is what the degenerate-case tests check.
    """
    sectors = SectorAxis(
        labels=declaration.sector_index_set,
        dims={s: declaration.sector_dims[s] for s in declaration.sector_index_set},
    )
    partition = declaration.partition
    factor = MeasuredFactor(
        label="f0",
        party=next(
            iter(
                partition.party_of_sector_factors.get(
                    sectors.labels[0], (PartyLabel.BOB,)
                )
            ),
        ),
        sectors=sectors,
        alphabet=declaration.bob_outcomes,
        blocks={
            v: {s: as_matrix(declaration.bob_povm[v][s]) for s in sectors.labels}
            for v in declaration.bob_outcomes
        },
    )
    alice_label = "t0"
    return GeneralDeclaration(
        alice=AliceFactor(
            party=partition.party_of_alice_system,
            sectors=SectorAxis(
                labels=(alice_label,), dims={alice_label: declaration.alice_dim}
            ),
        ),
        alice_marginal=(
            None
            if declaration.alice_marginal is None
            else {alice_label: declaration.trusted_marginal}
        ),
        alice_alphabet=declaration.alice_outcomes,
        alice_operators={
            x: {alice_label: as_matrix(declaration.alice_povm[x])}
            for x in declaration.alice_outcomes
        },
        alice_form=AliceForm.POVM,
        factors=(factor,),
        transcript=two_message_transcript(
            declaration.announce_alice, declaration.announce_bob
        ),
        accept_statistic={
            (first, second): value
            for (first, second), value in declaration.accept_statistic.items()
        },
        key_map={
            (x, v): declaration.raw_key(x, v)
            for x in declaration.alice_outcomes
            for v in declaration.bob_outcomes
        },
        key_holder=declaration.key_holder,
        acceptance_values=declaration.acceptance_values,
        key_value_count=declaration.key_value_count,
        acceptance_set=declaration.acceptance_set,
        rounds=declaration.rounds,
        parameters=declaration.parameters,
        sector_block_kind=declaration.sector_block_kind,
        constraint_list=tuple(
            GeneralConstraintEntry(
                scope=factor.label,
                operator_blocks={
                    s: as_matrix(entry.operator_blocks[s]) for s in sectors.labels
                },
                relation=entry.relation,
                bound=(
                    {alice_label: entry.operator_bound}
                    if entry.rhs_tag is RhsTag.GENERAL
                    else entry.scalar_bound
                ),
                rhs_tag=(
                    GeneralRhsTag.GENERAL
                    if entry.rhs_tag is RhsTag.GENERAL
                    else GeneralRhsTag.HOMOGENEOUS
                ),
            )
            for entry in declaration.constraint_list
        ),
        constraints_through_a_reductions_chain=(
            declaration.constraints_through_a_reductions_chain
        ),
        attack_set_license=declaration.attack_set_license,
        source_replacement_license=declaration.source_replacement_license,
        party_partition=declaration.party_partition,
    )


def sector_axis(dims: Sequence[tuple[str, int]]) -> SectorAxis:
    """Return a :class:`SectorAxis` from ordered ``(label, dimension)`` pairs."""
    return SectorAxis(labels=tuple(label for label, _ in dims), dims=dict(dims))
