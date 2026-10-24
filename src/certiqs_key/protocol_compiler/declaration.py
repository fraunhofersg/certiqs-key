"""The module-owned declaration object, and the machine-key vocabulary.

THIS TYPE IS THIS MODULE'S OWN, BY DESIGN
=======================================================================
It is NOT the CONSUMING ENGINE's ``ProtocolDeclaration`` (meat-core) and NOT
the wire ``Declaration`` of the operator-bundle manifest. Three reasons, and
the first is the operative one:

1. **It must be constructible without an acceptance set and without a round
   count.** the outputs table's preamble names those two as inputs of the consuming
   engine that "are NOT outputs of this module": ``acceptance_set`` is owned by
   ``statistics-acceptance`` and ``rounds`` is a run parameter. A type that
   required them could not represent the object this contract emits, and a
   compiler that filled them would emit something it does not own.
2. **Every check of this module is stated on a CANDIDATE.** Definition
   ``def:validator`` reads "given a candidate declaration", and Theorem
   ``thm:validator-soundness`` (ii)-(iii) are unstatable otherwise -- the V5- and
   V8-discriminating cases are candidates Definition ``def:compile`` could not
   have emitted, and a type that could only hold a validated object could not
   carry them.
3. **The artifact is self-contained.** No bundle-schema extension is
   authorized in this band, so the six compiler-only keys of the outputs table have
   no home in the frozen wire format and this module keeps its own.

WHAT THE TWENTY-THREE KEYS ARE, AND WHICH OF THEM THIS PASS FILLS
=================================================================
:data:`OUTPUT_KEYS` is the outputs table's table in its order: SEVENTEEN declaration
slots then SIX compiler-only keys. Two rows of the first tabular carry two keys
each -- ``sector_index_set, sector_dims`` and ``announce_alice,
announce_bob`` -- so counting ROWS undercounts KEYS, which is the transcription
error :data:`DECLARATION_SLOT_KEYS` exists to prevent. ``sector_block_kind`` and
``constraint_rhs_tag`` are declaration slots.

:class:`CandidateDeclaration` carries the seventeen declaration slots together
with ``acceptance_alphabet`` and ``label_index_map``. The remaining four
compiler-only keys -- ``reduction_chain_record``, ``key_length_eligible``,
``gate_report`` and ``refusal`` -- are EMISSION results: the first is the
consumed chain carried through, the second and third are decided by the gates
of Definition ``def:eligible``, and the fourth is present exactly when nothing
is emitted at all. Their shapes are recorded in ``interface.yaml`` as open
implementation choices and are not decided here, because this pass writes no
emission path; assembling the full twenty-one-key artifact is the emission
pass's work. What IS fixed here is the vocabulary: the names, their split, and
the two keys that are not outputs of this module at all.

SERIALIZATION
=============
:meth:`CandidateDeclaration.as_machine_record` writes the declaration under
exactly the machine keys of the outputs table, with every matrix in the exact wire
form of :func:`certiqs_key.foundations.exact.serialize_matrix`, so that a key-rate
generation run can log the object that produced its input. The encoding is a
serialization decision with no proof-relevant content -- the contract fixes no
wire form for any emitted matrix or table -- and it is deliberately simple:
JSON-representable scalars, lists and mappings, no binary, no schema version of
its own, and every rational exact.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Final

from certiqs_key.domain.announcements import AnnouncementTranscript
from certiqs_key.domain.constraints import AttackSetLicense, ConstraintEntry
from certiqs_key.domain.families import AliceForm, AliceSlot, FactorisedFamily
from certiqs_key.foundations.blocks import (
    PRODUCT_LABEL_SEPARATOR,
    BlockOperator,
    FactorisedSectorMap,
    Label,
    SectorFactor,
    SectorStructure,
    SystemTag,
    default_factor_label,
    single_alice_sector,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Matrix, serialize_matrix
from certiqs_key.protocol_compiler.spec import (
    PERP,
    AnnouncementClass,
    KeyValue,
    Party,
    PartyPartition,
)

__all__ = [
    "COMPILER_ONLY_KEYS",
    "CONTRACT_VERSION",
    "DECLARATION_SLOT_KEYS",
    "INDEXED_ALPHABETS",
    "MATHEMATICAL_SPEC_VERSION",
    "NOT_OUTPUTS",
    "OUTPUT_KEYS",
    "CandidateDeclaration",
    "LabelIndexMap",
    "build_label_index_map",
    "realized_readout_classes",
]

#: THE CONTRACT VERSION THIS CODE IMPLEMENTS: an accepted ``version`` of
#: spec/modules/protocol-compiler/module.yaml, this repository's single source
#: of truth for a module's version. PRINCIPLES.md section 6 puts the module
#: version at the human-accepted batch, and an artefact may not claim a draft
#: version or one that does not exist. The expectations that spell the emitted
#: string are edited BY HAND when it moves, never regenerated from the code.
#:
#: IT LIVES HERE AND NOT ON THE PACKAGE SURFACE because
#: :meth:`~certiqs_key.protocol_compiler.compile.CompilationResult.as_machine_record`
#: emits it under ``mathematical_spec_version`` and ``__init__`` imports
#: ``compile``; a constant in ``__init__`` would be a cycle. This module owns
#: the emitted key list, which is the right place for the emitted version.
CONTRACT_VERSION: Final[str] = "0.23.0"

#: The string the emitted record carries under ``mathematical_spec_version``.
MATHEMATICAL_SPEC_VERSION: Final[str] = f"protocol-compiler@{CONTRACT_VERSION}"

#: The TWENTY-THREE output machine keys of the outputs table, in the table's order.
#: ``sector_block_kind`` and ``constraint_rhs_tag`` are among them. The first completes
#: the ONE sector map -- "ALL THREE of its components are machine keys of the
#: emitted artifact ... so that a consumer comparing sector maps can compare
#: all three and not two of them" -- and the second carries each entry's
#: declared form, "emitted with each entry so that the consuming engine's type
#: check has a datum" (Definition ``def:homog``).
OUTPUT_KEYS: Final[tuple[str, ...]] = (
    "alice_dim",
    "alice_marginal",
    "source_replacement_license",
    "party_partition",
    "sector_index_set",
    "sector_dims",
    "sector_block_kind",
    "alice_povm",
    "bob_povm",
    "announce_alice",
    "announce_bob",
    "accept_statistic",
    "key_map",
    "key_holder",
    "constraint_list",
    "constraint_rhs_tag",
    "attack_set_license",
    "acceptance_alphabet",
    "label_index_map",
    "reduction_chain_record",
    "key_length_eligible",
    "gate_report",
    "refusal",
)

#: The SIX compiler-only keys -- the second tabular of the outputs table
#: (sec:outputs). None is a slot of Eq. ``eq:declaration``.
COMPILER_ONLY_KEYS: Final[tuple[str, ...]] = (
    "acceptance_alphabet",
    "label_index_map",
    "reduction_chain_record",
    "key_length_eligible",
    "gate_report",
    "refusal",
)

#: The SEVENTEEN declaration slots: the keys the consuming engine reads.
#: Fifteen at 0.1.4, and the two 0.3.0 additions are both slots rather than
#: compiler-only keys -- each is a component of the emitted declaration and is
#: read by the consumer, not a record of how this module decided something.
DECLARATION_SLOT_KEYS: Final[tuple[str, ...]] = tuple(
    key for key in OUTPUT_KEYS if key not in COMPILER_ONLY_KEYS
)

#: The two inputs of the consuming engine that are NOT outputs of this module,
#: with their owners, as the outputs table's preamble names them. Recorded as data so
#: that no emission path can "complete" a declaration by filling them.
NOT_OUTPUTS: Final[tuple[tuple[str, str], ...]] = (
    ("acceptance_set", "statistics-acceptance"),
    ("rounds", "a run parameter; no module emits it"),
)

#: The NINE alphabets Definition ``def:compile`` indexes through ``idx``, in
#: its order.
INDEXED_ALPHABETS: Final[tuple[str, ...]] = (
    "X",
    "V",
    "S",
    "O_A",
    "O_B",
    "C_A",
    "C_B",
    "Chat",
    "Z_perp",
)


@dataclass(frozen=True)
class LabelIndexMap:
    """The emitted ``label_index_map``: nine bijections, each with its inverse.

    Definition ``def:compile`` asks for "a choice, for each of ``X``, ``V``,
    ``S``, ``O_A``, ``O_B``, ``C_A``, ``C_B``, ``Chat`` and ``Z_perp``, of a
    bijection onto an INITIAL SEGMENT of the non-negative integers", with the
    inverse table emitted alongside so that the semantic label of an index is
    recoverable (Theorem ``thm:typing``).

    WHICH BIJECTION IS OPEN AND IS DECIDED HERE. ``interface.yaml`` records it
    as open choice ``OC-label-index-map``: the contract fixes the requirement
    and no particular bijection, and any two choices differ by a permutation
    that every emitted list and table is indexed through consistently. THE
    CHOICE MADE IS THE DECLARED ORDER: label ``i`` of the declared enumeration
    gets index ``i``. It is the only choice that needs no further datum, it
    makes ``subsystem_order``'s "sector blocks in the declared total order of
    ``S``" literally true of the emitted index, and it is stable under
    re-emission of the same specification.
    """

    forward: Mapping[str, Mapping[Label, int]]
    inverse: Mapping[str, Mapping[int, Label]]

    def index_of(self, alphabet: str, label: Label) -> int:
        """Return the binding index of a semantic label."""
        return self.forward[alphabet][label]

    def label_of(self, alphabet: str, index: int) -> Label:
        """Return the semantic label an index carries."""
        return self.inverse[alphabet][index]

    def as_machine_record(self) -> dict[str, dict[str, list[list[object]]]]:
        """Return the map and its inverse as a machine record."""
        return {
            "forward": {
                name: [[label, index] for label, index in table.items()]
                for name, table in self.forward.items()
            },
            "inverse": {
                name: [[index, label] for index, label in table.items()]
                for name, table in self.inverse.items()
            },
        }


def build_label_index_map(
    alphabets: Mapping[str, Sequence[Label]],
    factor_components: Sequence[tuple[str, Sequence[Label]]] = (),
) -> LabelIndexMap:
    """Return the label-to-index map over the nine alphabets of ``def:compile``.

    Refuses any presentation that is not a bijection onto an initial segment:
    a repeated label makes the forward table non-injective, and a missing
    alphabet leaves an emitted list unindexed.

    ``factor_components`` IS THE GENERAL FORMAT'S DERIVED COMPONENTS and is
    EMPTY for the accepted format, so the nine stay the nine and a declaration
    that says what it said before is indexed exactly as it was. It is a separate
    argument rather than nine-plus-n entries of ``alphabets`` because the refusal
    above is what keeps a tenth alphabet out of the accepted map: a caller that
    put ``T`` in the mapping would be adding an alphabet ``def:compile``'s
    accepted clause does not index, and that refusal is worth keeping.
    ``def:compile``'s general clause names these components and says they "are
    not further choices"; the caller derives them and this function only enumerates.
    """
    missing = [name for name in INDEXED_ALPHABETS if name not in alphabets]
    if missing:
        raise MalformedInputError(f"no enumeration for indexed alphabet(s) {missing}")
    extra = [name for name in alphabets if name not in INDEXED_ALPHABETS]
    if extra:
        raise MalformedInputError(
            f"{extra} is not one of the nine alphabets Definition def:compile indexes"
        )
    declared = [name for name, _ in factor_components]
    if len(set(declared)) != len(declared):
        raise MalformedInputError(
            f"the per-factor index components {declared} name one twice; each "
            "names one factor's alphabet or one factor's sector set and a "
            "repeated name would leave a per-factor order ambiguous"
        )
    clash = [name for name in declared if name in INDEXED_ALPHABETS]
    if clash:
        raise MalformedInputError(
            f"the per-factor index component(s) {clash} would overwrite one of "
            "the nine alphabets Definition def:compile indexes"
        )
    forward: dict[str, Mapping[Label, int]] = {}
    inverse: dict[str, Mapping[int, Label]] = {}
    for name in (*INDEXED_ALPHABETS, *declared):
        labels = tuple(
            alphabets[name]
            if name in INDEXED_ALPHABETS
            else next(entry for key, entry in factor_components if key == name)
        )
        if not labels:
            raise MalformedInputError(f"alphabet {name} is finite and NON-EMPTY (D(i))")
        if len(set(labels)) != len(labels):
            raise MalformedInputError(
                f"alphabet {name} repeats a label, so no bijection onto an "
                "initial segment exists"
            )
        forward[name] = {label: index for index, label in enumerate(labels)}
        inverse[name] = dict(enumerate(labels))
    return LabelIndexMap(forward=forward, inverse=inverse)


@dataclass(frozen=True)
class CandidateDeclaration:
    """A candidate protocol declaration: the tuple of Eq. ``eq:declaration``.

    CANDIDATE, not emitted. Definition ``def:validator`` is stated on a
    candidate and Theorem ``thm:validator-soundness`` applies to candidates, so this
    type is what the checks of :mod:`certiqs_key.protocol_compiler.validation` are
    stated on and holds declarations Definition ``def:compile`` could not have produced
    -- which is exactly what makes V5 and V8 exhibitable at all.

    ``alice_marginal`` is ``None`` for the value ``nomarg`` of the marginal
    slot. The ``source_model`` convention: ``nomarg`` is "deliberately not
    ``perp`` ... and not ``0``, which is inadmissible", so the empty slot is ``None``
    and never a
    zero matrix -- check V2 refuses the zero matrix, and an implementation that
    spelled the empty slot that way would refuse every untrusted declaration.
    """

    alice_dim: int
    alice_marginal: Matrix | None
    sectors: SectorStructure
    alice_alphabet: tuple[Label, ...]
    alice_povm: Mapping[Label, Matrix]
    bob_alphabet: tuple[Label, ...]
    bob_povm: Mapping[Label, BlockOperator]
    partition: PartyPartition
    announce_alice: Mapping[Label, Label]
    announce_bob: Mapping[Label, Label]
    alice_announcement_alphabet: tuple[Label, ...]
    bob_announcement_alphabet: tuple[Label, ...]
    acceptance_alphabet: tuple[Label, ...]
    #: ``phi`` ON THE ACCEPTED FORMAT'S ``K = C_A x C_B``, keyed by the pair.
    #: EMPTY exactly where :attr:`accept_statistic_general` carries it instead,
    #: which is where a transcript is declared: a sibling key rather than a
    #: widened one, for the reason the shared format gives at
    #: ``Declaration.alice_marginal_blocks`` -- a consumer typed against the
    #: degenerate case reads the key it has always read or finds it empty, and
    #: never an ``L``-tuple under a name it knows as a pair.
    accept_statistic: Mapping[tuple[Label, Label], Label]
    key_map: Mapping[tuple[Label, Label], KeyValue]
    key_alphabet: tuple[int, ...]
    key_holder: Party
    constraint_list: tuple[ConstraintEntry, ...] = ()
    attack_set_license: AttackSetLicense | None = None
    source_replacement_license: object | None = None
    label_index_map: LabelIndexMap | None = None

    # --- THE GENERAL FORMAT OF def:declaration (DX1)-(DX6) -----------------
    # EVERY FIELD BELOW IS OPTIONAL AND ITS ABSENCE IS THE DEGENERATE VALUE, so
    # a candidate of the accepted format is the object it was, field for field,
    # and every check reads the accepted clause on it. THEY ARE FIELDS OF THIS
    # TYPE AND NOT OF A SECOND ONE: def:declaration's implements binding is this
    # class, the general format is the SAME definition's appended paragraph, and
    # a parallel candidate type would make Theorem thm:validator-soundness's "all four
    # parts hold for a candidate declaration in the general format" a statement about
    # another object.
    #: THE FACTOR LIST OF (DX1), or ``None`` for the single-factor default: one
    #: ``Q`` factor whose map is :attr:`sectors` and no ``A`` factor. THE PRODUCT
    #: MAP IS DERIVED FROM IT AND IS NOT A SECOND DATUM -- :attr:`sectors` is
    #: what the ``Q`` side flattens to, and V1 is where that is decided.
    sector_factorisation: FactorisedSectorMap | None = None
    #: ALICE'S MEASUREMENT SLOT OF (DX2), (DX4) as block lists along ``T``, or
    #: ``None`` where :attr:`alice_povm` carries it as one matrix per letter,
    #: which is the accepted format. IN ENSEMBLE FORM IT HOLDS ``{N_x}`` and
    #: :attr:`alice_povm` IS EMPTY: the two stand in place of one another
    #: (``eq:ensembleform``), and the POVM an ensemble form denotes
    #: (``eq:ensemblepovm``) is formed by no one.
    alice_slot: AliceSlot | None = None
    #: ``tau_A`` AS A BLOCK LIST ALONG ``T`` (DX2), or ``None`` where
    #: :attr:`alice_marginal` carries it as one matrix. THE SLOT IS ONE SLOT:
    #: both absent is ``nomarg`` and is the only thing that is, so
    #: :attr:`is_trusted_mode` reads the pair.
    alice_marginal_blocks: BlockOperator | None = None
    #: THE MEASURED FAMILY PER FACTOR (DX3) with the product rule, or ``None``
    #: where :attr:`bob_povm` carries the one family of the accepted format. NO
    #: PRODUCT BLOCK IS A DATUM and nothing here forms one.
    bob_factors: FactorisedFamily | None = None
    #: THE TRANSCRIPT PROTOCOL OF (DX5), or ``None`` for the two independent
    #: messages of the accepted format, which stay :attr:`announce_alice` and
    #: :attr:`announce_bob`. The joint announcement function is DERIVED from it
    #: by ``eq:transcript`` and is a slot of nothing.
    transcript: AnnouncementTranscript | None = None
    #: ``phi`` ON THE DERIVED ``K = prod_m C_m`` of ``eq:transcript``, keyed by the
    #: ``L``-tuple, present exactly where :attr:`transcript` is and IN PLACE OF
    #: :attr:`accept_statistic`. ``K`` is "a set determined by the tables and is
    #: declared by no one" (``def:spec`` (d')), so this table's DOMAIN is derived
    #: while the table itself is declared.
    accept_statistic_general: Mapping[AnnouncementClass, Label] | None = None

    @property
    def is_general_format(self) -> bool:
        """Whether any slot of (DX1)--(DX6) is filled in its general spelling.

        WHAT IT IS FOR: choosing which reading of a check to run, in the one
        place per check where the two readings differ. It is NOT a mode and not a
        declared datum -- "the accepted text is the case ... entry for entry", so
        a candidate for which this is ``False`` is read by the accepted clauses
        and one for which it is ``True`` by the general ones, and at the
        degenerate values the two agree conjunct for conjunct.
        """
        return any(
            slot is not None
            for slot in (
                self.sector_factorisation,
                self.alice_slot,
                self.alice_marginal_blocks,
                self.bob_factors,
                self.transcript,
            )
        ) or any(entry.scope is not None for entry in self.constraint_list)

    @property
    def alice_form(self) -> AliceForm:
        """Return which of (DX4)'s two slots is filled. POVM form by default."""
        return AliceForm.POVM if self.alice_slot is None else self.alice_slot.form

    @property
    def alice_factor(self) -> SectorFactor | None:
        """Return the factor tagged ``A``, or ``None`` where none is declared.

        (DX1): "at most one factor is tagged ``A``, and where there is one it is
        the first of the list", which
        :class:`~certiqs_key.foundations.blocks.FactorisedSectorMap` refuses otherwise,
        so this reads the first factor of that side and never searches.
        """
        if self.sector_factorisation is None:
            return None
        retained = self.sector_factorisation.factors_of(SystemTag.A)
        return retained[0] if retained else None

    @property
    def alice_sectors(self) -> SectorStructure:
        """Return ``T`` with its dimensions: the ``A`` factor's map, or one block.

        (DX1): "where no factor is tagged ``A``, ``T = {t_0}`` and ``A_{t_0} =
        A``", which is the accepted format's reading of Alice's side and is what
        :func:`~certiqs_key.foundations.blocks.single_alice_sector` spells. THE BLOCK
        KIND OF THE DEGENERATE MAP IS THE EMITTED ONE, so that a comparison
        against it compares three components and not two.
        """
        factor = self.alice_factor
        if factor is not None:
            return factor.sectors
        return single_alice_sector(self.alice_dim, self.sectors.block_kind)

    @property
    def joint_sectors(self) -> SectorStructure:
        """Return the JOINT map ``((t, s), d_{A_t} d_s)``, ``t`` slowest (DX1).

        The map ``omega`` is a block list against: "the joint sectors are the pairs
        ``(t, s)``, ORDERED WITH ``t`` SLOWEST", which is the ``A``-first product
        order the shared format flattens by
        (:meth:`~certiqs_key.foundations.blocks.JointBlockOperator.joint_sectors`).
        DERIVED AND NOT DECLARED, like every other product order of (DX1).

        AT ONE ALICE SECTOR IT IS THE ``Q`` MAP, identifier for identifier -- the
        join of a single identifier is that identifier -- so the accepted format's
        witness comparison is this one at the degenerate value.

        THE JOIN IS THE ONE
        :meth:`~certiqs_key.foundations.blocks.JointBlockOperator.joint_sectors`
        MAKES, AND IT IS SPELLED HERE RATHER THAN BUILT OUT OF
        :class:`~certiqs_key.foundations.blocks.SectorFactor`. With several measured
        factors the emitted ``Q`` identifiers are themselves products, so they carry the
        declared separator, and a ``SectorFactor`` may not: a factor of a product
        declares ONE system's own labels, and that refusal is right where it is.
        The joint map is not such a factor; it is the ``A``-first join of the two
        sides, the ``Q`` side running fastest, and a joint identifier stays
        unambiguous because there is at most one ``A`` factor, it comes first, and
        its labels carry no separator. This method and the joint operator's must
        agree identifier for identifier -- branch (c) of V7 compares a supplied
        witness's map against this one -- so both are that one join.
        """
        return SectorStructure(
            labels=tuple(
                PRODUCT_LABEL_SEPARATOR.join((alice_label, sector_label))
                for alice_label in self.alice_sectors.labels
                for sector_label in self.sectors.labels
            ),
            dims=tuple(
                alice_dim * sector_dim
                for alice_dim in self.alice_sectors.dims
                for sector_dim in self.sectors.dims
            ),
            block_kind=self.sectors.block_kind,
        )

    @property
    def measured_factors(self) -> tuple[SectorFactor, ...]:
        """Return the factors tagged ``Q``, in the product order.

        With no declared factor list this is the single-factor default of (DX1):
        one factor whose map IS :attr:`sectors`, scoped to the party the
        partition labels ``Q`` with. One factor and one entry, which is the
        accepted format.
        """
        if self.sector_factorisation is not None:
            return self.sector_factorisation.factors_of(SystemTag.Q)
        return (
            SectorFactor(
                party=str(Party.BOB),
                sectors=self.sectors,
                system=SystemTag.Q,
                label=default_factor_label(0),
            ),
        )

    @property
    def measured_factor_labels(self) -> tuple[Label, ...]:
        """Return the measured factors' LABELS, in the product order of ``F``.

        The list an entry's scope is compared against. A declared label where a
        factor carries one and
        :func:`~certiqs_key.foundations.blocks.default_factor_label` of its position
        among the MEASURED factors otherwise, which is ``reductions``' own default
        for an emitted factor.
        """
        if self.sector_factorisation is None:
            return (default_factor_label(0),)
        return self.sector_factorisation.labels_of(SystemTag.Q)

    def measured_factor(self, scope: Label) -> SectorFactor | None:
        """Return the measured factor a SCOPE names, or ``None`` if none does.

        The comparison behind ``constraint_scope_not_a_factor``: "every entry's
        scope names a measured factor of the emitted sector map, A COMPARISON OF A
        LABEL AGAINST THE FACTOR LIST" (V6 in the general format).

        THE LABEL COMPARED IS THE FACTOR'S OWN AND NEVER ITS PARTY, and the
        difference is not cosmetic: a party may hold TWO measured factors -- two
        stations of one party -- so a comparison against party labels would admit
        an entry scoped to either of them and refuse neither, which is the
        direction ``constraint_scope_not_a_factor`` exists to close.
        ``reductions``' factor emission declares a label per factor and carries the
        party beside it, and this module passes those labels through unchanged.

        A READING TAKEN WHERE THE ACCEPTED TEXT IS SILENT, and it is the refusing
        one. (DX1) types a factor as "a system tag, a party label, and a sector map
        of its own" and names no label slot, while (DX6) scopes an entry to "the
        label of one measured factor" and V6 compares the two; the only reading
        under which that comparison is decidable AND refuses at two factors of one
        party is a per-factor name. The interface row ``sector_factorisation`` owes
        one normative sentence for it.
        """
        for label, factor in zip(
            self.measured_factor_labels, self.measured_factors, strict=True
        ):
            if label == scope:
                return factor
        return None

    def measured_factor_position(self, scope: Label | None) -> int:
        """Return the product position of the factor a scope names.

        ``None`` is the accepted format's scope -- "with one measured factor the
        scope is that factor" -- and is position ``0``. A scope naming no factor
        raises: V6 refuses it with ``constraint_scope_not_a_factor`` before any
        value is computed, so reaching this with one is a hypothesis violation and
        not a case to be guessed at.
        """
        if scope is None:
            return 0
        labels = self.measured_factor_labels
        if scope not in labels:
            raise MalformedInputError(
                f"the scope {scope!r} names no measured factor of {list(labels)}; "
                "check V6 refuses such an entry with "
                "constraint_scope_not_a_factor before a value is computed"
            )
        return labels.index(scope)

    def alice_operator(self, x: Label) -> BlockOperator:
        """Return Alice's declared block list at one letter, IN EITHER SPELLING.

        ``M_x`` in POVM form and ``N_x`` in ensemble form, from
        :attr:`alice_slot` where one is declared and from :attr:`alice_povm` as a
        one-block list otherwise -- which is the accepted format's datum read in
        the general shape, ``A`` carrying one sector there. NOTHING IS CONVERTED:
        the one-block list is the declared matrix and no other array is formed.
        """
        if self.alice_slot is not None:
            return self.alice_slot.member(x)
        return BlockOperator.of(self.alice_sectors, [self.alice_povm[x]])

    @property
    def is_trusted_mode(self) -> bool:
        """Whether the EMITTED source mode is trusted.

        the ``source_model`` convention: the mode is DERIVED from whether the
        marginal slot is filled and is "never emitted as a second key. A second
        carrier of the mode would be a second source of truth."

        THE SLOT HAS TWO SPELLINGS (DX2) AND IS ONE SLOT: the matrix
        of the accepted format and the block list along ``T`` of the general one.
        Both absent is ``nomarg``, and that is what this reads.
        """
        return self.alice_marginal is not None or self.alice_marginal_blocks is not None

    @property
    def marginal_blocks(self) -> BlockOperator | None:
        """Return ``tau_A`` as a block list along ``T``, or ``None`` for nomarg.

        The one reading of the marginal slot every general-format check uses, so
        that neither spelling is read twice: the declared block list where the
        general spelling is filled, and the declared matrix as a ONE-BLOCK list
        otherwise, which is the accepted format's datum in the general shape.
        NOTHING IS FORMED: the one-block list holds the declared matrix.
        """
        if self.alice_marginal_blocks is not None:
            return self.alice_marginal_blocks
        if self.alice_marginal is None:
            return None
        return BlockOperator.of(self.alice_sectors, [self.alice_marginal])

    @property
    def q_dim(self) -> int:
        """Return ``d_Q``."""
        return self.sectors.total_dim

    @property
    def raw_key_alphabet(self) -> tuple[KeyValue, ...]:
        """Return ``Z_perp = Z sqcup {perp}`` in the emitted order."""
        return (*self.key_alphabet, PERP)

    def announcement(self, x: Label, v: Label) -> AnnouncementClass:
        """Return ``a(x, v)``: Eq. ``eq:jointann``, or ``eq:transcript`` in general.

        ONE FUNCTION FOR BOTH, because ``a`` is one object: (DX5) says "the two
        maps ``a_A``, ``a_B`` above are the transcript with ``L = 2``", so the
        accepted pair is the degenerate composition and every check that reads
        ``a`` -- V4, V5, V8, the key map -- reads it here and is unchanged.
        ``thm:sifting-and-key`` (iv) is what says the proofs of (ii) and (iii) "use of
        ``a`` only that it is a total map into ``K``", which is why they apply
        unchanged.

        THE RETURN IS AN ``L``-TUPLE and at ``L = 2`` it is the pair
        ``(c_A, c_B)`` the accepted format's class is, class for class.
        """
        if self.transcript is not None:
            return self.transcript.joint_announcement(
                lambda sender: self.partition.readout(Party(sender), x, v)
            )
        alice_readout = self.partition.readout(Party.ALICE, x, v)
        bob_readout = self.partition.readout(Party.BOB, x, v)
        try:
            return (self.announce_alice[alice_readout], self.announce_bob[bob_readout])
        except KeyError as exc:  # pragma: no cover - V1/V8 report the missing cell
            raise MalformedInputError(
                f"an announcement map is not tabulated at readout {exc.args[0]!r}"
            ) from exc

    def tabulated_classes(self) -> frozenset[AnnouncementClass]:
        """Return the classes ``phi`` is tabulated on, IN EITHER SPELLING.

        What V1's totality clause on ``phi`` is decided against: the keys of
        whichever of the two tables is filled. A SET AND NOT A LIST, because the
        clause asks membership and the declared ORDER of ``K`` is
        :meth:`announcement_classes`'s.
        """
        if self.accept_statistic_general is not None:
            return frozenset(self.accept_statistic_general)
        return frozenset(self.accept_statistic)

    def acceptance_value(self, kappa: AnnouncementClass) -> Label:
        """Return ``phi(kappa)`` from whichever spelling of the table is filled.

        ONE READING FOR BOTH, so that ``phi`` is one map: the derived-``K`` table
        where a transcript is declared and the accepted pair table otherwise. A
        missing cell RAISES rather than defaulting, because "a partial ``phi``
        loses probability mass (``rem:phitotal``) and is refused rather than
        completed with a default value" -- and the refusal is check V1's.
        """
        table = (
            self.accept_statistic
            if self.accept_statistic_general is None
            else self.accept_statistic_general
        )
        return _tabulated_at(table, kappa)

    def outcome_pairs(self) -> tuple[tuple[Label, Label], ...]:
        """Return ``X x V`` in the declared order."""
        return tuple((x, v) for x in self.alice_alphabet for v in self.bob_alphabet)

    def announcement_classes(self) -> tuple[AnnouncementClass, ...]:
        """Return ``K``: ``C_A x C_B``, or ``prod_m C_m`` under a transcript.

        Both in the product order, the last component fastest, which is the one
        convention (DX5) and ``eq:jointann`` share; at ``L = 2`` the two are the
        same list, class for class.
        """
        if self.transcript is not None:
            return self.transcript.joint_alphabet()
        return tuple(
            (c_a, c_b)
            for c_a in self.alice_announcement_alphabet
            for c_b in self.bob_announcement_alphabet
        )

    def as_machine_record(self) -> dict[str, object]:
        """Return the declaration under the machine keys of the outputs table.

        The fifteen declaration slots plus ``acceptance_alphabet`` and
        ``label_index_map``. The four remaining compiler-only keys are the
        emission pass's and are absent here rather than filled with a default:
        the ``fail_closed`` convention -- "no default value is ever substituted
        for a missing datum".
        """
        record: dict[str, object] = {
            "alice_dim": self.alice_dim,
            "alice_marginal": (
                None
                if self.alice_marginal is None
                else serialize_matrix(self.alice_marginal)
            ),
            "source_replacement_license": self.source_replacement_license,
            "party_partition": _serialize_partition(self.partition),
            "sector_index_set": list(self.sectors.labels),
            "sector_dims": list(self.sectors.dims),
            # THE THIRD COMPONENT OF THE ONE SECTOR MAP, a machine key of this
            # module "so that a consumer comparing sector maps can
            # compare ALL THREE AND NOT TWO of them".
            "sector_block_kind": self.sectors.block_kind.value,
            # THE TWO ACCEPTED FAMILY KEYS ARE EMPTY WHERE THE GENERAL FORMAT
            # CARRIES THE FAMILY ELSEWHERE, and empty rather than absent for the
            # reason `req:chain-record-slots` gives of every slot of the chain record: a
            # record that omits a slot cannot later distinguish "no elements"
            # from "elements not carried". In ensemble form "{M_x} is not
            # declared and is formed by nobody" and the blocks are under
            # `alice_ensemble`; with a declared factor list "no entry of a
            # product is declared, formed, rounded or decided on" (DX3) and the
            # factors are under `bob_povm_factors`. A declaration of the accepted
            # format fills both keys exactly as it always did.
            "alice_povm": (
                []
                if self.alice_slot is not None
                else [
                    serialize_matrix(self.alice_povm[label])
                    for label in self.alice_alphabet
                ]
            ),
            "bob_povm": (
                []
                if self.bob_factors is not None
                else [
                    [serialize_matrix(block) for block in self.bob_povm[label].blocks]
                    for label in self.bob_alphabet
                ]
            ),
            # THE TWO ANNOUNCEMENT KEYS ARE EMPTY UNDER A TRANSCRIPT, which is
            # (DX5)'s own reading: "the two maps a_A, a_B above are the transcript
            # with L = 2", so where one is declared the pair is no slot at all and
            # the tables are under `transcript`. Empty and not absent, for the
            # reason the two family keys above are.
            "announce_alice": (
                []
                if self.transcript is not None
                else [
                    [label, self.announce_alice[label]]
                    for label in self.partition.alice_readout_alphabet
                ]
            ),
            "announce_bob": (
                []
                if self.transcript is not None
                else [
                    [label, self.announce_bob[label]]
                    for label in self.partition.bob_readout_alphabet
                ]
            ),
            "accept_statistic": [
                [list(kappa), self.acceptance_value(kappa)]
                for kappa in self.announcement_classes()
            ],
            "key_map": [
                [list(pair), self.key_map[pair]] for pair in self.outcome_pairs()
            ],
            "key_holder": str(self.key_holder),
            "constraint_list": [
                _serialize_entry(entry) for entry in self.constraint_list
            ],
            # `constraint_rhs_tag`, one per entry in the emitted entry order,
            # READ OFF THE DATUM and never taken on a supplier's word. It is
            # carried inside each serialized entry as well; this key is the
            # the outputs table output row, which is the list.
            "constraint_rhs_tag": [
                None if entry.tag is None else str(entry.tag)
                for entry in self.constraint_list
            ],
            "attack_set_license": (
                None
                if self.attack_set_license is None
                else {
                    "supplier": self.attack_set_license.supplier,
                    "statement": self.attack_set_license.statement,
                }
            ),
            "acceptance_alphabet": list(self.acceptance_alphabet),
            "label_index_map": (
                None
                if self.label_index_map is None
                else self.label_index_map.as_machine_record()
            ),
        }
        record.update(self._general_format_record())
        return record

    def _general_format_record(self) -> dict[str, object]:
        """Return the general format's keys, EACH PRESENT ONLY WHERE IT IS USED.

        The general-format output rows of ``interface.yaml``: the factor list of
        (DX1), Alice's form and her blocks (DX2), (DX4), the per-factor family
        (DX3), the transcript (DX5) and each entry's scope (DX6). A DECLARATION
        OF THE ACCEPTED FORMAT ADDS NO KEY HERE -- the mapping is empty for it --
        which is what makes the emitted record of every shipped instance the
        record it was, key for key and byte for byte.

        THREE KEY NAMES ARE SIBLINGS OF AN EXISTING ROW RATHER THAN THE ROW'S OWN
        DOTTED NAME, and the reading is recorded here as it is in the shared
        format. ``alice_marginal.blocks`` and ``bob_povm.per_factor`` are rows
        that give an existing key a second SHAPE; this record emits them as
        ``alice_marginal_blocks``, ``alice_povm_blocks`` and ``bob_povm_factors``
        instead, so that a consumer reading ``alice_marginal`` or ``bob_povm``
        finds the type it has always found there or finds the key absent, and
        never a differently-shaped value under a name it already knows. The
        product map, the product alphabet, the joint sectors, the joint
        announcement function, a lifted constraint operator and the POVM an
        ensemble form denotes are NOT KEYS and are formed by no one.
        """
        record: dict[str, object] = {}
        if self.sector_factorisation is not None:
            # THE ENGINE CANNOT RECONSTRUCT THESE THREE ALPHABETS FROM THE
            # DEGENERATE EMBEDDING IN THE GENERAL FORMAT.  In particular, ``X``
            # need not be a party readout alphabet, ``Chat`` is the codomain of
            # the declared phi, and the key alphabet is a declared protocol
            # choice.  Carry their engine-facing spellings beside the general
            # factorisation; accepted-format records remain byte-for-byte
            # unchanged because this branch is absent there.
            record["alice_alphabet"] = list(self.alice_alphabet)
            record["acceptance_values"] = list(self.acceptance_alphabet)
            record["key_value_count"] = len(self.key_alphabet)
            record["sector_factorisation"] = [
                {
                    "system": factor.system.value,
                    "party": factor.party,
                    "label": label,
                    "sectors": [list(entry) for entry in factor.sectors.entries],
                }
                for factor, label in zip(
                    self.sector_factorisation.factors,
                    _emitted_factor_labels(self.sector_factorisation),
                    strict=True,
                )
            ]
        if self.alice_slot is not None:
            record["alice_form"] = str(self.alice_slot.form)
            key = (
                "alice_ensemble"
                if self.alice_slot.is_ensemble
                else "alice_povm_blocks"
            )
            record[key] = [
                [serialize_matrix(block) for block in self.alice_slot.member(x).blocks]
                for x in self.alice_slot.alphabet
            ]
        if self.alice_marginal_blocks is not None:
            record["alice_marginal_blocks"] = [
                serialize_matrix(block)
                for block in self.alice_marginal_blocks.blocks
            ]
        if self.bob_factors is not None:
            record["bob_povm_factors"] = [
                {
                    "party": family.party,
                    "alphabet": list(family.alphabet),
                    "members": [
                        [serialize_matrix(block) for block in member.blocks]
                        for member in family.members
                    ],
                }
                for family in self.bob_factors.factors
            ]
        if self.transcript is not None:
            record["transcript"] = [
                {
                    "sender": message.sender,
                    "alphabet": list(message.alphabet),
                    "table": [
                        [readout, list(prefix), value]
                        for (readout, prefix), value in message.table.items()
                    ],
                }
                for message in self.transcript.messages
            ]
        if any(entry.scope is not None for entry in self.constraint_list):
            record["constraint_scope"] = [
                entry.scope for entry in self.constraint_list
            ]
        return record


def _emitted_factor_labels(
    factorisation: FactorisedSectorMap,
) -> tuple[Label, ...]:
    """Return every factor's label, in the product order of the whole list.

    The label a factor declared, or its position default ON ITS OWN SIDE -- which
    is the side a scope is compared against, so that what is emitted is what V6
    decides against and not a second numbering.
    """
    per_side = {
        system: iter(factorisation.labels_of(system))
        for system in (SystemTag.A, SystemTag.Q)
        if factorisation.factors_of(system)
    }
    return tuple(next(per_side[factor.system]) for factor in factorisation.factors)


def _tabulated_at(table: Mapping[Any, Label], kappa: AnnouncementClass) -> Label:
    """Return ``phi(kappa)`` from one of the two spellings of the table.

    THE ONE PLACE IN THIS PACKAGE WHERE A TABLE'S KEY TYPE IS ``Any``, and it is
    confined to this helper deliberately. ``phi``'s domain is ``K``, which is a
    PAIR in the accepted format and an ``L``-TUPLE in the general one; the two
    tables are separate fields so that a consumer typed against the degenerate
    case keeps its type (the sibling-key reading recorded at
    :attr:`CandidateDeclaration.accept_statistic`), and one lookup serves both
    because a pair IS a tuple of message values at ``L = 2``.

    A MISSING CELL RAISES AND IS NEVER DEFAULTED: "a partial ``phi`` loses
    probability mass (``rem:phitotal``) and is refused rather than completed with
    a default value". Check V1 is what refuses it with a named reason.
    """
    try:
        return table[kappa]
    except KeyError as exc:  # pragma: no cover - V1 reports the missing cell
        raise MalformedInputError(
            f"phi is not tabulated on the announcement class {kappa!r}"
        ) from exc


def _serialize_partition(partition: PartyPartition) -> dict[str, object]:
    """Return the party partition as a machine record."""
    return {
        "alice_readout_alphabet": list(partition.alice_readout_alphabet),
        "bob_readout_alphabet": list(partition.bob_readout_alphabet),
        "alice_readout": [
            [list(pair), value] for pair, value in partition.alice_readout.items()
        ],
        "bob_readout": [
            [list(pair), value] for pair, value in partition.bob_readout.items()
        ],
        "alice_system_party": str(partition.alice_system_party),
        "sector_factor_parties": [
            [str(party) for party in factors]
            for factors in partition.sector_factor_parties
        ],
    }


def _serialize_entry(entry: ConstraintEntry) -> dict[str, object]:
    """Return one constraint entry as a machine record."""
    rhs = entry.rhs
    tag = entry.tag
    return {
        "operator": [serialize_matrix(block) for block in entry.operator.blocks],
        "relation": str(entry.relation),
        "rhs": (
            str(rhs)
            if isinstance(rhs, Fraction)
            else [serialize_matrix(block) for block in rhs.blocks]
            if isinstance(rhs, BlockOperator)
            else serialize_matrix(rhs)
        ),
        "rhs_kind": (
            "scalar"
            if isinstance(rhs, Fraction)
            else "block_operator"
            if isinstance(rhs, BlockOperator)
            else "operator"
        ),
        # `constraint_rhs_tag`, a machine key of this module,
        # "emitted with each entry so that the consuming engine's type check
        # has a datum" (Definition def:homog). READ OFF THE DATUM, never off a
        # field the supplier sent.
        "constraint_rhs_tag": None if tag is None else str(tag),
    }


def realized_readout_classes(
    declaration: CandidateDeclaration,
) -> tuple[tuple[Label, AnnouncementClass], ...]:
    """Return the ``(o, kappa)`` pairs realized by some ``(x, v)``.

    The proof of Theorem ``thm:validator-soundness``'s V8 => D(viii) direction defines
    ``r_h`` on realized pairs from ``r`` and puts ``perp`` elsewhere, and the contract
    says the value on the unrealized ones "is immaterial". This function is
    what makes that set explicit, so that no test asserts a value off it.
    """
    seen: list[tuple[Label, AnnouncementClass]] = []
    for x, v in declaration.outcome_pairs():
        pair = (
            declaration.partition.readout(declaration.key_holder, x, v),
            declaration.announcement(x, v),
        )
        if pair not in seen:
            seen.append(pair)
    return tuple(seen)
