"""The protocol specification: this compiler's input object, typed.

protocol-compiler 0.3.0 Definition ``def:spec``: a specification is the tuple
``S = (S_src, S_rec, R, S_pub, S_con)`` in five parts, and the inputs table says how
those parts arrive, key by key, with the preamble "Machine keys are binding for
interface.yaml". :data:`INPUT_KEYS` is that table's twelve keys in its order,
and every record below carries one part of one of them.

WHAT IS DELIBERATELY ABSENT FROM THE TYPED INPUT
================================================
**A test-statistics-model selector.** :class:`PublicChoices` is typed exactly
as the the inputs table ``public_choices`` row types it -- ``(T_pub, q, {N_{u|t}})``
-- and carries no model field, because no input row of the contract carries
one. ``interface.yaml`` records the consequence as a thin spot with two
conforming readings and decides neither, and the frozen registry routes it as a
change-request candidate for a human. This module takes the reading the
contract's own text forces: within the typed input a ``fixed_fraction`` request
is INEXPRESSIBLE, so the obligation of Theorem ``thm:choice-encoding`` (iv) holds by
construction. AN IMPLEMENTATION MUST NOT INVENT AN INPUT MACHINE KEY FOR IT --
the inputs table's keys are binding, and adding one would be a SCOPE CHANGE
to this module rather than an implementation choice. The out-of-band
caller-level route is served by
:func:`certiqs_key.protocol_compiler.weights.refuse_fixed_fraction`, which emits the
verbatim reason without adding a key.

**A sifting-predicate slot in the emitted declaration.** ``varsigma`` is an
INPUT (:class:`PublicPart`) and Eq. ``eq:declaration``'s tuple does not carry
it. Keeping it
outside the declaration object is a scope decision -- "the
sifting predicate stays outside the declaration object ... any future pinning
is a scope change" -- so nothing here emits it and nothing downstream reads it
from a slot.

THE RAW-KEY MAP IS BUILT, NEVER ACCEPTED
========================================
Eq. ``eq:rdef`` and Eq. ``eq:rhold`` are functions of ``S_pub`` alone, and
:func:`raw_key_map` and :func:`derived_holder_key_rule` are those two
equations. Remark ``rem:rbuilt`` is why they are here rather than in the input:
"A specification that supplied ``r`` directly would have to be CHECKED for D(v)
and D(viii); built as Eq. eq:rdef, ``r`` satisfies both by construction, and
the only residual obligation is the side condition that ``r^0_h`` maps into
``Z``" -- which :func:`key_rule_side_condition` decides by inspecting one
function table, as Remark ``rem:sidecond`` says. The step that WRITES the built
map into an emitted declaration belongs to Definition ``def:compile`` and is
not in this pass; here the two equations are predicates on ``S_pub``, which is
what Theorems ``thm:sifting-and-key`` and ``thm:validator-soundness`` need to be stated
on candidates.

ONE MODELLING DECISION, RECORDED BECAUSE IT LOOKS LIKE A SIMPLIFICATION
======================================================================
D(vi) writes two relation sets, ``{preceq, =, succeq}`` in trusted-source mode
and ``{<=, =, >=}`` in untrusted-source mode. Those are the SAME THREE ORDERING
SYMBOLS read in two orders -- the Loewner order on Hermitian operators, and the
real order -- and which order they are read in is fixed by the source mode,
which the ``source_model`` convention derives from whether the marginal slot is
filled. :class:`Relation` therefore carries the three symbols once, and the
mode carries the reading; the typing half of D(vi) is then the type of the
right-hand side, which is exactly what check V6 tests. The equivalence
V6 <=> D(vi) that Theorem ``thm:validator-soundness`` (i)-(ii) needs is unaffected: a
declared entry satisfies D(vi) iff its right-hand side is a Hermitian operator on ``A``
with the slot filled, or a real scalar with the slot holding ``nomarg``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction
from typing import TYPE_CHECKING, Final, Literal

from certiqs_key.domain.announcements import AnnouncementTranscript
from certiqs_key.domain.constraints import AttackSetLicense, ConstraintEntry
from certiqs_key.domain.families import AliceForm, AliceSlot
from certiqs_key.foundations.blocks import (
    BlockOperator,
    JointBlockOperator,
    Label,
    SectorStructure,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Matrix, dimension, direct_sum
from certiqs_key.transmitter.artifact import TransmitterArtifact
from certiqs_key.transmitter.links import SourceLink
from certiqs_key.transmitter.presentation import (
    EnsemblePresentation,
    alice_marginal_blocks,
)
from certiqs_key.transmitter.reasons import CertificateForm, SourceMode

if TYPE_CHECKING:  # pragma: no cover - weights.py imports this module
    from certiqs_key.protocol_compiler.weights import ChoiceWeighting

__all__ = [
    "INPUT_KEYS",
    "PERP",
    "RETIRED_INPUT_KEYS",
    "AnnouncementClass",
    "DirectPovm",
    "KeyValue",
    "Party",
    "PartyPartition",
    "PovmPresentation",
    "ProtocolSpecification",
    "PublicChoices",
    "PublicPart",
    "ReceiverPart",
    "Sifting",
    "SourcePart",
    "SpecConstraints",
    "default_party_partition",
    "derived_holder_key_rule",
    "joint_announcement",
    "key_rule_side_condition",
    "raw_key_map",
]

#: THE ELEVEN INPUT MACHINE KEYS of spec/modules/protocol-compiler/
#: interface.yaml, in the table's order.
#:
#: ONE ROW, ``transmitter_artifact``, CARRIES ALICE'S SYSTEM, HER POVM SPEC AND
#: THE SOURCE-REPLACEMENT CERTIFICATE: those objects are the transmitter's and
#: ``def:spec`` (a) reads them off the artefact
#: (:class:`~certiqs_key.transmitter.artifact.TransmitterArtifact`). There is
#: no ``source_mode_request`` row: the mode is read off the artefact's
#: marginal slot and off nothing else, and the transmitter refuses a
#: trusted-mode request without a certificate before any artefact exists.
#: ``choice_weighting`` is route C's setting-dependent weighting.
#:
#: WHY ``target_povm`` NEEDED A KEY OF ITS OWN, in Definition ``def:compile``'s
#: words: "Where a supplied family arrives with a declared order on the
#: alphabet that indexes it -- AS THE TARGET POVM OF THE LAST LINK OF R_rec
#: DOES, ITS SUPPLIER HAVING ESTABLISHED ITS OWN COMPLETENESS SUM IN THAT ORDER
#: -- the compiler takes THAT ORDER as idx's component there ... ONE ORDER AT
#: ALL THREE PLACES, AND NO FAMILY IS REFUSED HERE FOR AN ORDERING ITS SUPPLIER
#: NEVER CHOSE." That is "the ONE accumulation order the consuming engine's
#: text also fixes (interface point (7)), WHICH IS WHY `target_povm` HAS A
#: MACHINE KEY OF ITS OWN: as an UNKEYED COMPONENT OF A CHAIN LINK THE ORDER
#: WOULD HAVE NO NAME ON THE WIRE."
#:
#: ITS SLOT IS THE LAST RECEIVER LINK'S ``target_povm`` AND ``target_alphabet``
#: (:class:`~certiqs_key.protocol_compiler.chain.ChainLink`), which is where
#: the supplier's declared order lives; the key NAMES that component rather
#: than duplicating it, because a second carrier of the same order would be a second
#: source of
#: truth. Definition ``def:compile`` fills ``V`` and ``bob_povm`` from it, so
#: condition (S) is decided in the supplier's order and ``label_index_map``
#: emits that same order.
INPUT_KEYS: Final[tuple[str, ...]] = (
    "transmitter_artifact",
    "receiver_povm",
    "public_choices",
    "choice_weighting",
    "reduction_chain",
    "target_sectors",
    "target_povm",
    "public_structure",
    "constraint_entries",
    "attack_set_license",
    "feasibility_witness",
)

#: The row ``source_mode_request`` is not an input, kept as a NAME so
#: that a reader can find out where it went.
RETIRED_INPUT_KEYS: Final[tuple[str, ...]] = ("source_mode_request",)

#: An announcement class ``kappa`` of ``K``: the pair ``(c_A, c_B)`` of
#: ``C_A x C_B`` (Eq. ``eq:jointann``), and in the general format the ``L``-tuple
#: ``(kappa_m)_m`` of ``prod_m C_m`` (``def:declaration`` (DX5),
#: ``eq:transcript``).
#:
#: ONE TYPE FOR BOTH, and the widening is the claim's own: (DX5) says the accepted
#: pair IS the transcript at ``L = 2``, so an announcement class is a tuple of
#: message values whose length is ``L``, and the pair is the case ``L = 2``. A
#: second type would make every map declared on ``K`` -- ``phi``, ``sigma``,
#: ``r^0_hold`` -- two maps.
type AnnouncementClass = tuple[Label, ...]

#: The sifting-failure key value ``perp``. The ``source_model`` convention
#: records the sentinel discipline: ``nomarg`` is "deliberately NOT perp,
#: which is the
#: sifting-failure key value, and not 0, which is inadmissible", so this value
#: is never used for an empty marginal slot -- that slot holds ``None``.
PERP: Final[Literal["perp"]] = "perp"

#: A value of the raw-key alphabet ``Z_perp = Z sqcup {perp}``.
type KeyValue = int | Literal["perp"]


class Party(StrEnum):
    """The two party labels. Sans-serif capitals in the contract; labels here."""

    ALICE = "A"
    BOB = "B"


class Sifting(StrEnum):
    """The two values of ``varsigma : K -> {pass, fail}`` (D(v))."""

    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True)
class DirectPovm:
    """A POVM presented directly, as a matrix list over an ordered alphabet."""

    alphabet: tuple[Label, ...]
    elements: Mapping[Label, Matrix]

    def __post_init__(self) -> None:
        """Refuse a presentation whose table does not cover its alphabet."""
        if len(set(self.alphabet)) != len(self.alphabet):
            raise MalformedInputError(
                "a POVM alphabet enumerates a set; one label repeats"
            )
        missing = [label for label in self.alphabet if label not in self.elements]
        if missing:
            raise MalformedInputError(f"no matrix for POVM outcome(s) {missing}")

    def ordered(self) -> tuple[Matrix, ...]:
        """Return the elements in the declared alphabet order."""
        return tuple(self.elements[label] for label in self.alphabet)


@dataclass(frozen=True)
class PublicChoices:
    """The ``public_choices`` record ``(T_pub, q, {N_{u|t}})`` of the inputs table.

    Definition ``def:weighted``: ``T_pub`` finite and non-empty with declared
    weights ``q_t > 0`` summing to one, and for each ``t`` a POVM
    ``{N_{u|t}}`` on the declaring party's system. ONE SUCH RECORD PER PARTY,
    either possibly absent.

    NO MODEL SELECTOR FIELD, AND NONE MAY BE ADDED -- see the module docstring.
    """

    party: Party
    choices: tuple[Label, ...]
    weights: Mapping[Label, Fraction]
    #: For each choice, the residual alphabet and the conditional POVM on it.
    conditional_alphabets: Mapping[Label, tuple[Label, ...]]
    conditional_elements: Mapping[Label, Mapping[Label, Matrix]]
    #: An optional spelling of the emitted joint labels, keyed by the pair
    #: ``(u, t)``. Definition ``def:weighted`` fixes the joint alphabet's
    #: STRUCTURE -- the disjoint union ``sqcup_t U_t x {t}`` -- and not the
    #: NAME of each member, and the outputs table says "semantic labels are
    #: metadata; indices are binding". The BB84 instance writes
    #: ``F_{(b', y)}`` with the CHOICE first where Definition ``def:weighted``
    #: writes ``N_{u,t}`` with the outcome first, so an instance may declare
    #: its own spelling. A relabelling is a BIJECTION and changes no matrix,
    #: no weight and no index order; where it is absent the default spelling
    #: ``(u,t)`` is used.
    joint_labels: Mapping[tuple[Label, Label], Label] | None = None

    def __post_init__(self) -> None:
        """Refuse a presentation that tabulates no choice-weighted family."""
        if not self.choices:
            raise MalformedInputError("T_pub is finite and NON-EMPTY (def:weighted)")
        if len(set(self.choices)) != len(self.choices):
            raise MalformedInputError("T_pub enumerates a set; one choice repeats")
        for choice in self.choices:
            if choice not in self.weights:
                raise MalformedInputError(
                    f"no declared weight q_t for choice {choice!r}"
                )
            if choice not in self.conditional_alphabets:
                raise MalformedInputError(f"no residual alphabet U_t for {choice!r}")
            if choice not in self.conditional_elements:
                raise MalformedInputError(f"no conditional POVM for {choice!r}")
            # U_t IS TYPED LIKE T_pub AND FOR THE SAME REASONS.
            # def:weighted declares "for each t in T_pub a POVM
            # {N_{u|t}}_{u in U_t}": an EMPTY U_t tabulates no family for
            # def:exact to be read against -- eq:declorder has no Sigma_{|J|}
            # over an empty alphabet and `sum_in_declared_order` raises rather
            # than answering -- and a REPEATED u is not an alphabet, would be
            # summed twice by (C) and (S) and would collide in the disjoint
            # union sqcup_t U_t x {t}. Both are MALFORMED and not refusals:
            # they are presentations of an input this module does not type, so
            # no clause of def:weighted can be read against them and refusing
            # them would have to invent a reason (the same rule T_pub's two
            # guards above follow, and `refusal` names no such string).
            outcomes = self.conditional_alphabets[choice]
            if not outcomes:
                raise MalformedInputError(
                    f"the residual alphabet U_t of choice {choice!r} is empty; "
                    "def:weighted declares a POVM {N_{u|t}}_{u in U_t} for "
                    "every t and a POVM has at least one element"
                )
            if len(set(outcomes)) != len(outcomes):
                raise MalformedInputError(
                    f"the residual alphabet U_t of choice {choice!r} enumerates "
                    "a set; one outcome repeats"
                )


#: How Alice's or Bob's family arrives: directly, or as a choice-weighted
#: family that Definition ``def:weighted`` turns into one.
type PovmPresentation = DirectPovm | PublicChoices


@dataclass(frozen=True)
class PartyPartition:
    """The declared party partition ``P`` of Definition ``def:declaration``.

    Two total readout maps on ``X x V`` onto declared finite alphabets, the
    party label of ``A``, and the declared tensor factorization of each
    ``H(Q_s)`` with a party label per factor. THE FACTORIZATION IS METADATA
    HERE: no derivation of this contract reads it, so it is carried through
    and never allowed to decide anything; the consuming engine's laboratory
    premise (``meat-core/ass:lab``) reads its labels as naming the parties'
    laboratories (``def:declaration``).
    """

    alice_readout: Mapping[tuple[Label, Label], Label]
    bob_readout: Mapping[tuple[Label, Label], Label]
    alice_readout_alphabet: tuple[Label, ...]
    bob_readout_alphabet: tuple[Label, ...]
    alice_system_party: Party = Party.ALICE
    sector_factor_parties: tuple[tuple[Party, ...], ...] = ()

    def readout(self, party: Party, x: Label, v: Label) -> Label:
        """Return ``pi_party(x, v)``."""
        table = self.alice_readout if party is Party.ALICE else self.bob_readout
        try:
            return table[(x, v)]
        except KeyError as exc:  # pragma: no cover - V1 reports the untabulated cell
            raise MalformedInputError(
                f"the readout of party {party} is not tabulated at ({x!r}, {v!r})"
            ) from exc

    def readout_alphabet(self, party: Party) -> tuple[Label, ...]:
        """Return ``O_party``."""
        return (
            self.alice_readout_alphabet
            if party is Party.ALICE
            else self.bob_readout_alphabet
        )


def default_party_partition(
    x_alphabet: Sequence[Label],
    v_alphabet: Sequence[Label],
    sector_factor_parties: tuple[tuple[Party, ...], ...] = (),
) -> PartyPartition:
    """Return THE DEFAULT PARTY PARTITION of Definition ``def:target``.

    ``pi_A(x, v) = x``, ``pi_B(x, v) = v``, with ``A`` labelled ``A`` and every
    ``Q_s`` labelled ``B``. The readout alphabets are then ``X`` and ``V``, and
    they are still SEPARATE ALPHABETS -- a declaration with a non-default
    partition has ``O_A`` different from ``X``, and an implementation that
    identified the two would be correct only by accident of the default.

    Whether an emitted declaration spells the default EXPLICITLY or BY ABSENCE
    is a serialization question ``interface.yaml`` records as open choice
    ``OC-party-partition`` and does not decide; it is not decided here either,
    because this function builds a partition and emits nothing.
    """
    return PartyPartition(
        alice_readout={(x, v): x for x in x_alphabet for v in v_alphabet},
        bob_readout={(x, v): v for x in x_alphabet for v in v_alphabet},
        alice_readout_alphabet=tuple(x_alphabet),
        bob_readout_alphabet=tuple(v_alphabet),
        sector_factor_parties=sector_factor_parties,
    )


@dataclass(frozen=True)
class PublicPart:
    """``S_pub`` of Definition ``def:spec`` (d): the public structure.

    ``(P, a_A, a_B, varsigma, r^0_h, h, phi, Chat)``. All maps are total; the
    key rule ``r^0_h`` is total on ``O_h x K`` and INTO ``Z`` -- the side
    condition of Remark ``rem:sidecond``, decided by
    :func:`key_rule_side_condition` and caught on the candidate by check V5.
    """

    partition: PartyPartition
    announce_alice: Mapping[Label, Label]
    announce_bob: Mapping[Label, Label]
    alice_announcement_alphabet: tuple[Label, ...]
    bob_announcement_alphabet: tuple[Label, ...]
    sifting: Mapping[AnnouncementClass, Sifting]
    key_rule: Mapping[tuple[Label, AnnouncementClass], KeyValue]
    holder: Party
    key_alphabet: tuple[int, ...]
    acceptance_alphabet: tuple[Label, ...]
    #: ``phi`` on the accepted format's ``K = C_A x C_B``, keyed by the pair.
    #: EMPTY exactly where :attr:`accept_statistic_general` carries it, which is
    #: where a transcript is declared (``def:spec`` (d')); the two are siblings and
    #: not one widened key, for the reason ``CandidateDeclaration``'s field of
    #: the same name gives.
    accept_statistic: Mapping[tuple[Label, Label], Label]
    #: THE TRANSCRIPT OF ``def:spec`` (d'), in place of ``announce_alice`` and
    #: ``announce_bob``: ``L`` messages, each with its sender, its alphabet and its
    #: total table over the sender's readout and the earlier messages.
    transcript: AnnouncementTranscript | None = None
    #: ``phi`` on the DERIVED ``K = prod_m C_m``, present exactly where
    #: :attr:`transcript` is. ``K`` "is a set determined by the tables and is
    #: declared by no one".
    accept_statistic_general: Mapping[AnnouncementClass, Label] | None = None

    @property
    def announcement_classes(self) -> tuple[AnnouncementClass, ...]:
        """Return ``K = C_A x C_B`` in the declared order."""
        return tuple(
            (c_a, c_b)
            for c_a in self.alice_announcement_alphabet
            for c_b in self.bob_announcement_alphabet
        )


def joint_announcement(public: PublicPart, x: Label, v: Label) -> AnnouncementClass:
    """Return ``a(x, v) = (a_A(pi_A(x, v)), a_B(pi_B(x, v)))`` (Eq. ``eq:jointann``).

    Theorem ``thm:sifting-and-key`` (i) is true BY TYPING and not by check: the
    announcement maps are declared on the READOUT alphabets, "so no other signature is
    expressible".
    """
    alice_readout = public.partition.readout(Party.ALICE, x, v)
    bob_readout = public.partition.readout(Party.BOB, x, v)
    try:
        return (public.announce_alice[alice_readout], public.announce_bob[bob_readout])
    except KeyError as exc:  # pragma: no cover - V1/V8 report the untabulated cell
        raise MalformedInputError(
            f"an announcement map is not tabulated at readout {exc.args[0]!r}"
        ) from exc


def raw_key_map(
    public: PublicPart,
    x_alphabet: Sequence[Label],
    v_alphabet: Sequence[Label],
) -> dict[tuple[Label, Label], KeyValue]:
    """Return ``r`` of Eq. ``eq:rdef``, built from ``S_pub`` and nothing else.

    ``r(x, v) = r^0_h(pi_h(x, v), a(x, v))`` where ``varsigma(a(x, v)) = pass``,
    and ``perp`` where it is ``fail``. TOTAL, because Eq. ``eq:rdef`` is a case
    distinction on the value of the total map ``varsigma o a``, both branches of
    which are defined on all of ``X x V``.
    """
    built: dict[tuple[Label, Label], KeyValue] = {}
    for x in x_alphabet:
        for v in v_alphabet:
            kappa = joint_announcement(public, x, v)
            if public.sifting[kappa] is Sifting.FAIL:
                built[(x, v)] = PERP
            else:
                readout = public.partition.readout(public.holder, x, v)
                built[(x, v)] = public.key_rule[(readout, kappa)]
    return built


def derived_holder_key_rule(
    public: PublicPart,
) -> dict[tuple[Label, AnnouncementClass], KeyValue]:
    """Return ``r_h`` of Eq. ``eq:rhold``, total on ``O_h x K``.

    ``r^0_h`` on the passing classes and ``perp`` on the failing ones, WITHOUT
    reference to realizability -- which is why it differs from the
    reconstruction inside the proof of Theorem ``thm:validator-soundness`` on unrealized
    pairs. Both are total and both satisfy Eq. ``eq:partycomp``, which quantifies over
    ``(x, v)`` only; the contract says the value on unrealized pairs "is
    immaterial", so neither table may be asserted of the other.
    """
    built: dict[tuple[Label, AnnouncementClass], KeyValue] = {}
    for readout in public.partition.readout_alphabet(public.holder):
        for kappa in public.announcement_classes:
            if public.sifting[kappa] is Sifting.FAIL:
                built[(readout, kappa)] = PERP
            else:
                built[(readout, kappa)] = public.key_rule[(readout, kappa)]
    return built


def key_rule_side_condition(public: PublicPart) -> bool:
    """Whether ``r^0_h`` maps into ``Z`` -- Remark ``rem:sidecond``'s condition.

    "A typing condition on the specification, decided by inspection of one
    function table" (Remark ``rem:rbuilt``). Its violation is what makes
    sifting stop being announcement-determined, and check V5 is what catches
    the consequence on the candidate declaration.
    """
    return all(value != PERP for value in public.key_rule.values())


@dataclass(frozen=True)
class SourcePart:
    """``S_src`` of ``def:spec`` (a): A THIN READER OF THE TRANSMITTER ARTEFACT.

    THIS TYPE READS THE SOURCE AND DOES NOT DECLARE IT.
    ``def:spec`` (a) is "a source specification in the sense of
    transmitter/def:source-spec, PRESENTED AS THE TRANSMITTER ARTEFACT in its
    declared mode, with the certificate of transmitter/def:srcert where that
    mode carries one", so every field below is a projection of
    :class:`~certiqs_key.transmitter.artifact.TransmitterArtifact` and none is
    a second declaration of the same datum.

    THE MODE IS READ OFF THE MARGINAL SLOT AND OFF NOTHING ELSE: filled is
    trusted, nomarg is untrusted, and this record carries no mode field for the
    two to disagree through. The compiler nevertheless RE-DECIDES the marginal
    at V2 and Alice's POVM at V3, on the emitted data, whether or not the
    transmitter decided them first -- which is the ``decide_never_infer``
    convention and not a duplication of ownership.
    """

    artifact: TransmitterArtifact
    #: The ``public_choices`` record declared ON ALICE'S SIDE, where the
    #: specification declares one. ITS PRESENCE IS THE ONE PLACE THIS RECORD
    #: IS NOT A PROJECTION OF THE ARTEFACT, and it is here because
    #: ``def:compile`` fills ``{M_x}`` "from ``S_src``, WEIGHTED by
    #: ``def:weighted`` where a choice family is presented" while ``def:spec``
    #: (a) reads ``alice_povm`` off the artefact. The two are reconciled the
    #: way the ``decide_never_infer`` convention reconciles every consumed
    #: datum: the transmitter emits the family it decided, and this module
    #: CONSTRUCTS THE SAME FAMILY AGAIN from the declared choice record and
    #: takes ``def:weighted``'s emission decision on its own products. That is
    #: what keeps ``emitted_value_not_representable`` reachable through
    #: :func:`~certiqs_key.protocol_compiler.compile.compile_specification`
    #: (thm:choice-encoding (viii); the fail-closed rows), which it would not be if this
    #: module only read a family somebody else had already constructed.
    #:
    #: THE CLAIMS PUT the weighting in two places and this field is where the code
    #: carries both.
    alice_choices: PublicChoices | None = None
    #: The TYPED source-segment links of ``Ch_src``, presented beside the
    #: artefact's own ``source_segment`` row -- which is a list of DESCRIPTIONS,
    #: "always emitted and always empty at version 1". ``def:chaincond``'s
    #: (A1)--(A3) are decided on the record a link's obligation carries, so the
    #: typed records travel here; at ``L_s = 0`` this is empty and those
    #: conditions are admitted vacuously.
    source_links: tuple[SourceLink, ...] = ()

    def __post_init__(self) -> None:
        """Require the typed segment to be the artefact's own segment.

        The typed links are carried separately only because (A1)--(A3) read
        fields the older thin chain record does not.  They are not a caller's
        second source declaration.  Accepting links beside an empty or
        different artefact segment would falsely make provenance (A3) true of
        an unrelated core artefact, so a twin-field disagreement is malformed
        input and never reaches the gate.
        """
        artifact_segment: tuple[object, ...] = tuple(self.artifact.source_segment)
        typed_segment: tuple[object, ...] = self.source_links
        if artifact_segment != typed_segment:
            raise MalformedInputError(
                "SourcePart.source_links must equal the transmitter artefact's "
                "own source_segment entry for entry; the typed copy exists for "
                "the compiler's (A1)--(A3) checks and is not a second segment. "
                f"The artefact carries {len(artifact_segment)} link(s) and the "
                f"SourcePart carries {len(self.source_links)}"
            )
        presentation = getattr(
            self.artifact.source_replacement_license, "presentation", None
        )
        if isinstance(presentation, EnsemblePresentation):
            blocks = alice_marginal_blocks(presentation, self.artifact.signal_alphabet)
            dense = direct_sum(list(blocks))
            if self.artifact.alice_marginal != dense:
                raise MalformedInputError(
                    "the transmitter artifact's dense alice_marginal must equal "
                    "the direct sum of its ensemble presentation's declared "
                    "marginal blocks exactly; the two supplier carriers disagree"
                )

    @property
    def alphabet(self) -> tuple[Label, ...]:
        """Return ``X`` with its declared order, from the artefact."""
        return self.artifact.signal_alphabet

    @property
    def alice_dim(self) -> int:
        """Return ``d_A``, from the artefact."""
        return self.artifact.alice_dim

    @property
    def alice_povm(self) -> PovmPresentation:
        """Return ``{M_x}`` AS PRESENTED: the choice record, or the artefact's.

        Where the specification declares a public choice on Alice's side the
        record itself is returned, and ``def:weighted`` is applied to it by
        :func:`~certiqs_key.protocol_compiler.weights.resolve_povm` -- the one
        path in this package from a choice record to emitted matrices, and the
        one that takes the emission decision. Where it does not, the artefact's
        decided family is returned as a direct presentation, which carries no
        emission obligation because this module did not construct it.
        """
        if self.alice_choices is not None:
            return self.alice_choices
        return DirectPovm(
            alphabet=self.artifact.signal_alphabet,
            elements=dict(self.artifact.alice_povm),
        )

    @property
    def transmitted_dim(self) -> int:
        """Return ``dim H(A^v)``, the virtual transmitted system's dimension."""
        return self.artifact.virtual_transmitted_system

    @property
    def signal_weights(self) -> Mapping[Label, Fraction]:
        """Return ``{p_x}`` of the VIRTUAL ensemble, which is what a consumer gets."""
        return self.artifact.virtual_ensemble_weights

    @property
    def signal_states(self) -> Mapping[Label, Matrix]:
        """Return ``{rho^v_x}`` of the virtual ensemble."""
        return self.artifact.virtual_ensemble_states

    @property
    def marginal(self) -> Matrix | None:
        """Return ``tau_A``, or ``None`` spelling nomarg. ITS PRESENCE IS THE MODE."""
        return self.artifact.alice_marginal

    @property
    def source_mode(self) -> SourceMode:
        """Return the EMITTED mode, derived from the marginal slot."""
        return self.artifact.source_mode

    @property
    def licence(self) -> object | None:
        """Return the transmitter's licence record, which gate (G2) consumes."""
        return self.artifact.source_replacement_license

    # --- def:spec (a'): THE SOURCE PART IN THE GENERAL FORMAT ---------------
    # Every reader below is a PROJECTION OF THE ARTEFACT and none is a second
    # declaration: "which form a certificate is in is read off the artefact and
    # is never a second datum, exactly as the mode is". This record fills no
    # slot and CONVERTS NO FORM -- it forms neither eq:ensemblepovm from an
    # ensemble slot nor an ensemble slot from a POVM slot.

    @property
    def declares_alice_sectors(self) -> bool:
        """Whether the artefact declares an Alice sector map of its own.

        (DX1): "where no factor is tagged ``A``, ``T = {t_0}`` and ``A_{t_0} =
        A``". An artefact that declares none is the degenerate case and the
        compilation map emits NO ``A`` factor for it, which is what keeps the
        emitted record of every shipped instance the record it was.
        """
        return self.artifact.alice_sector_map is not None

    @property
    def alice_sectors(self) -> SectorStructure:
        """Return ``T`` with its dimensions, from the artefact and from nothing else."""
        return self.artifact.alice_sectors

    @property
    def certificate_form(self) -> CertificateForm:
        """Return which of the three forms the certificate was declared in.

        Read off the artefact. Which forms gate (G2) ADMITS is
        ``def:eligible``'s and is decided there; what this reader does is carry
        the form to it.
        """
        return self.artifact.certificate_form

    @property
    def alice_form(self) -> AliceForm:
        """Return which of (DX4)'s two slots the artefact fills. POVM by default.

        An ensemble presentation is what fills the ensemble slot: the artefact's
        ``alice_ensemble_operators`` are ``N^{(t)}_x`` of
        ``transmitter/lem:ensemble-presentation`` (v), "what a consumer reads of
        Alice's side in an ensemble presentation, where ``{M_x}`` is not declared
        and is formed by nobody".
        """
        if self.artifact.alice_ensemble_operators is not None:
            return AliceForm.ENSEMBLE
        return AliceForm.POVM

    @property
    def alice_slot(self) -> AliceSlot | None:
        """Return Alice's measurement slot as block lists along ``T`` (DX2), (DX4).

        ``None`` is the degenerate case: the POVM slot the accepted format
        carries as one matrix per letter, which :attr:`alice_povm` reads. In
        ENSEMBLE form the slot holds the artefact's ``{N_x}`` block lists --
        ``N^{(t)}_x`` of ``transmitter/lem:ensemble-presentation`` (v), passed
        through and not converted.

        WHY POVM FORM AT SEVERAL ALICE SECTORS ANSWERS ``None`` AND IS REFUSED
        ELSEWHERE, which is the one place this reader takes a reading the accepted
        text does not state. ``def:spec`` (a') says Alice's measurement "arrives
        in one of the two forms of (DX4): the POVM slot, or ... the ensemble
        slot", and the transmitter's outputs table has a dense ``alice_povm`` row
        and NO ``alice_povm_blocks`` row: the artefact emits ``{M_x}`` as one
        matrix per letter, the direct sum over the sectors, whatever sector map it
        declares. So at several Alice sectors a POVM-form artefact carries no
        per-sector block list, and THIS MODULE DOES NOT SPLIT the dense matrix
        into blocks -- splitting would form a datum nobody declared, on a
        basis-order assumption the artefact's table does not state.
        :func:`~certiqs_key.protocol_compiler.compile.refuse_dense_alice_povm_at_several_sectors`
        is where the refusing reading is taken and named; an ensemble
        presentation, which is the form a source with several Alice sectors has
        today (``transmitter/decoy/cor:emitted-decoy``), is unaffected.
        """
        operators = self.artifact.alice_ensemble_operators
        if operators is None:
            return None
        sectors = self.alice_sectors
        return AliceSlot.of(
            AliceForm.ENSEMBLE,
            self.alphabet,
            tuple(
                BlockOperator.of(sectors, list(operators[label]))
                for label in self.alphabet
            ),
        )

    @property
    def marginal_blocks(self) -> BlockOperator | None:
        """Return ``tau_A`` as a block list along ``T``, or ``None``.

        ``None`` both for ``nomarg`` and for the degenerate case, where
        :attr:`marginal` carries the one matrix the accepted format declares --
        the slot is ONE slot with two spellings, and
        :attr:`~certiqs_key.protocol_compiler.declaration.CandidateDeclaration.marginal_blocks`
        reads the one-block list off the matrix where the general spelling is
        absent.

        WHERE THE GENERAL SPELLING COMES FROM, AND IT IS THE SUPPLIER'S OWN
        FUNCTION RATHER THAN A SPLIT OF THE DENSE MATRIX. The transmitter's
        accepted outputs table has ONE ``alice_marginal`` row and it is one
        matrix: the presentation path emits the DIRECT SUM of the per-sector
        blocks it computed. So ``def:compile``'s "passed through unchanged, THE
        BLOCK LIST ALONG ``T`` INCLUDED" names a per-sector row the supplier's
        interface does not carry, and the two ways out are to SPLIT the matrix
        here -- which forms a datum nobody declared, on a basis-order assumption
        the artefact does not state -- or to read the blocks where the supplier
        declared them. THE SECOND IS TAKEN: for an ensemble presentation the
        licence record carries the presentation itself, and
        :func:`certiqs_key.transmitter.presentation.alice_marginal_blocks` is the
        supplier's own spelling of (E3)'s sum -- the function that produced the
        matrix the artefact emits. Nothing is formed here that the supplier did
        not declare, and check V3 re-decides the identity on the declared numbers
        afterwards. Where no presentation is carried this answers ``None``, which
        is what makes a POVM-form artefact with several Alice sectors reach the
        refusal :attr:`alice_slot` names instead of a fabricated block list.
        """
        presentation = getattr(
            self.artifact.source_replacement_license, "presentation", None
        )
        if not isinstance(presentation, EnsemblePresentation):
            return None
        return BlockOperator.of(
            self.alice_sectors,
            list(alice_marginal_blocks(presentation, self.alphabet)),
        )


@dataclass(frozen=True)
class ReceiverPart:
    """``S_rec`` of ``def:spec`` (b): the physical receiver part.

    THE PART HAS A THIRD SLOT, ROUTE C, and it is the claim's own.
    ``def:spec`` (b) reads: the receiver part
    is the physical family "and, optionally, a public choice of Bob's
    whose weight depends on his private setting ... to be applied by
    this module AFTER the reduction chain". So the weighting is a PART
    OF THE SPECIFICATION and not a second argument beside it, and it
    belongs here rather than on :class:`ProtocolSpecification`.

    ``None`` IS THE ORDINARY CASE: with no such record the emitted
    family is the chain's ``{F_v}`` unchanged (``rem:relabel``, "what
    version 1 emits"), and the shipped instances declare none.

    THE TYPE IS IMPORTED UNDER ``TYPE_CHECKING`` because
    :mod:`certiqs_key.protocol_compiler.weights` imports THIS module
    for :class:`PublicChoices` and :class:`DirectPovm`; the annotation
    is a string at runtime (``from __future__ import annotations``) and
    the record is where ``def:weighted``'s second construction lives.
    """

    physical_dim: int
    physical_povm: PovmPresentation
    #: ``(F, t: V -> T, P(f | t))``, the ``choice_weighting``
    #: input row. Applied by
    #: :func:`~certiqs_key.protocol_compiler.compile.compile_specification`
    #: AFTER the chain and BEFORE the validator and the gates
    #: (``def:compile``; ``rem:relabel``). In the general format it is applied
    #: after THAT FACTOR'S OWN segment and to that factor's family alone.
    choice_weighting: ChoiceWeighting | None = None
    # --- def:spec (b'): ONE ENTRY OF THE ORDERED LIST, one measured factor ---
    #: THE PARTY LABEL of this factor. ``def:spec`` (b'): each entry of the
    #: ordered list carries one. The party set is unchanged, ``{A, B}``, and what
    #: is new is that several measured factors may carry a label -- so two entries
    #: may carry the SAME party and are still two factors.
    party: Party = Party.BOB
    #: THE FACTOR'S OWN NAME, which is what a scoped entry names and is NOT the
    #: party label. ``None`` takes ``reductions``' position default
    #: ``f<position>`` on the measured side
    #: (:func:`~certiqs_key.foundations.blocks.default_factor_label`), so a factor
    #: nobody named is named the same way here and there.
    factor_label: Label | None = None
    #: THIS FACTOR'S OWN RECEIVER SEGMENT ``Ch^f_rec`` (``def:spec`` (c')),
    #: presented with the factor whose system its links act on, because "the
    #: segments are separate lists because their links act on different systems,
    #: and no link of one is composable with a link of another". ``None`` is the
    #: degenerate case, where the one receiver segment is
    #: :attr:`ProtocolSpecification.chain`'s. Annotated loosely for the reason
    #: that field is.
    chain: object | None = None

    def __post_init__(self) -> None:
        """Require every presented physical effect to act on ``physical_dim``."""
        if self.physical_dim < 1:
            raise MalformedInputError("a physical receiver dimension is positive")
        if isinstance(self.physical_povm, DirectPovm):
            matrices = self.physical_povm.ordered()
        else:
            matrices = tuple(
                self.physical_povm.conditional_elements[choice][outcome]
                for choice in self.physical_povm.choices
                for outcome in self.physical_povm.conditional_alphabets[choice]
            )
        for position, element in enumerate(matrices, start=1):
            if dimension(element) != self.physical_dim:
                raise MalformedInputError(
                    "every physical POVM element acts on the ReceiverPart's "
                    f"declared physical_dim={self.physical_dim}; element "
                    f"{position} has dimension {dimension(element)}"
                )


@dataclass(frozen=True)
class SpecConstraints:
    """``S_con`` of Definition ``def:spec`` (e): entries, licence, witness."""

    entries: tuple[ConstraintEntry, ...] = ()
    attack_set_license: AttackSetLicense | None = None
    #: ``omega^*``, supplied AS A BLOCK LIST AGAINST ``Smap`` (check V7
    #: branch (c)), consumed and verified and NEVER EMITTED.
    feasibility_witness: JointBlockOperator | None = None


@dataclass(frozen=True)
class ProtocolSpecification:
    """The five parts of ``def:spec``. THERE IS NO SIXTH, AND NO MODE REQUEST.

    ``reduction_chain`` is typed in :mod:`certiqs_key.protocol_compiler.chain`
    and is carried here as the third input of the join; ``target_sectors`` is
    "supplied by the last link's target descriptor" and is carried alongside so
    that the sector structure is available to every predicate of this pass
    without composing the chain.

    There is no ``source_mode_request`` field: the mode is
    ``source.source_mode``, read off the artefact's marginal slot.
    """

    source: SourcePart
    receiver: ReceiverPart
    public: PublicPart
    sectors: SectorStructure
    #: ``R = (R_src, R_rec)`` of Definition ``def:spec`` (c). Typed in
    #: :mod:`certiqs_key.protocol_compiler.chain`; annotated loosely here so that the
    #: input record does not import the chain module, which imports this one.
    chain: object | None = None
    constraints: SpecConstraints = field(default_factory=SpecConstraints)
    #: THE MEASURED FACTORS BEYOND THE FIRST (``def:spec`` (b')): the ordered
    #: list of that clause is :attr:`receiver` followed by these, in this order,
    #: which :attr:`receiver_parts` assembles. ``()`` is the degenerate case, one
    #: measured factor, and every specification this repository ships.
    #:
    #: WHY THE FIRST FACTOR STAYS ON ITS OWN FIELD. ``receiver`` is the accepted
    #: input row and every existing caller fills it; a second field holding the
    #: whole list would carry the first factor twice and let the two disagree.
    #: With this shape the general format is ADDITIVE and the accepted format is
    #: the empty tuple, field for field.
    further_receiver_factors: tuple[ReceiverPart, ...] = ()

    @property
    def receiver_parts(self) -> tuple[ReceiverPart, ...]:
        """Return ``S_rec`` as the ORDERED LIST of ``def:spec`` (b').

        One entry per measured factor and in the order of ``F``, which is the
        order the factor list of (DX1) is assembled in and the order every product
        of this format is derived in. With no further factors it is
        ``(receiver,)`` -- one entry, which is the accepted format.
        """
        return (self.receiver, *self.further_receiver_factors)

    @property
    def is_general_format(self) -> bool:
        """Whether this specification presents ``def:spec``'s (a')--(e') at all.

        A DECISION ON WHICH READING TO TAKE, not a declared mode and not a
        datum: at one measured factor, POVM form, one Alice sector, two messages
        and no scoped entry "every object named below is the object of the same
        name there and nothing else is presented", so a specification for which
        this is ``False`` is compiled by the accepted clauses and emits what it
        emits today.
        """
        return (
            bool(self.further_receiver_factors)
            or self.source.declares_alice_sectors
            or self.source.alice_form is AliceForm.ENSEMBLE
            or self.public.transcript is not None
            or any(entry.scope is not None for entry in self.constraints.entries)
        )
