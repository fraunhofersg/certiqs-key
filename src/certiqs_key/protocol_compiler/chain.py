"""PC7, PC8 -- the reduction chain: two typed segments and their conditions.

protocol-compiler 0.3.0 Definition ``def:chaincond`` ((C1)-(C5), (S1)-(S4), (X1)),
Theorem ``thm:chain-consumption``, Definition ``def:banda``, Theorem ``thm:band-a``,
Remark ``rem:coarse`` and Requirement ``req:chain-record-slots``.

THE COMPOSITION ORDER IS THE SHAPE OF THE RECORD, NOT A TAG
===========================================================
``def:spec`` (c) and design.md's decision 3: a source map replaces Alice's
signal ensemble on the TRANSMITTED system and a squashing map replaces Bob's
measurement on the RECEIVER system; "these are different types, and A SINGLE
LIST OF LINKS CANNOT CARRY BOTH". So :class:`ReductionChain` is an ordered PAIR
of ordered lists, composed source segment first, and the ordering rule is a
property of the pair. The ``chain_order`` convention: "a source-map link cannot
be placed after a squashing link BECAUSE THERE IS NO SLOT IN WHICH TO WRITE
IT".

(X1) IS THEREFORE NOT A RUNTIME CHECK, AND MUST NOT BE NAMED BY A REFUSAL.
Theorem ``thm:chain-consumption`` (i): "(X1) is NOT DECIDED, because it is not a
condition on data: it is the TYPE of the record", and its proof adds that (X1) "is a
statement about WHICH OF THE TWO LISTS a link was written into, which the
record answers by construction". A link written into the wrong segment fails
that segment's DESCRIPTOR rule -- (C1) for a source map, since ``A'`` is not
the physical receiver space, and (S1) for a squashing map, since ``Q`` is not
an Alice-side descriptor -- and an implementation that refused naming (X1)
would be naming a condition the contract says is not checked. The verdict for
(X1) in :class:`ChainReport` is accordingly always ``holds``, and
:data:`certiqs_key.protocol_compiler.reasons.CHAIN_REFUSAL_REASONS` carries no
entry for it.

(C4) AND (S3) ARE CONDITIONAL ON THE DATA, AND SILENCE IS NOT A PASS
====================================================================
Both are stated "where checkable": (C4) holds "IF EVERY LINK OF ``R_rec``
SUPPLIES ITS CHANNEL AS DATA", and "where some link supplies only A THEOREM
CONSTRUCTOR AND NO CHANNEL, the identity is NOT DECIDABLE FROM THE EMITTED DATA
and is carried instead as the supplier obligation Assumption ``ass:link``";
(S3) carries the same clause. Where the composite does not exist this module
records :attr:`~certiqs_key.protocol_compiler.reasons.ConditionOutcome.NOT_CHECKED` AND
NAMES A-LINK. It does not record ``holds``, and it does not refuse: the chain
is admissible and the obligation is TRANSFERRED, not discharged. Assumption
``ass:link``: the checks this contract performs "are NECESSARY CONDITIONS AND
NOT THE OBLIGATION".

The same applies when an earlier condition has already failed: with (C2) failed
there are no well-defined fibres ``gamma^{-1}(v)`` to sum over, so
Eq. ``eq:pullback`` has no right-hand side and (C4) is ``not checked`` --
"an implementation that evaluated (C4) first and reported it ``passed`` would
be reporting a computation on an ill-formed input".

THE DIRECTION OF (C2) IS FORCED AND IS NOT A CONVENTION
=======================================================
``gamma`` runs from the PHYSICAL alphabet ONTO the emitted one -- the
coarse-graining direction, of which a bijection is the special case. Theorem
``thm:chain-consumption`` (iii), Step 3 of its proof, shows that the reverse
admits no proper coarse-graining by an integer argument (Remark ``rem:coarse``
draws the direction of (C2) from it): summing
the reversed pullback over ``v`` and using unitality forces
``sum_w (|gamma'^{-1}(w)| - 1) F^ph_w = 0``, so every over-covered outcome is
null and "the only non-injective ``gamma'`` that survives is one whose extra
outcomes are null, i.e. NO COARSE-GRAINING AT ALL".

EVERY SLOT IS EMITTED, EMPTY OR NOT
===================================
Requirement ``req:chain-record-slots``: both segments, and on every link the
constraint slot and the licence slot, are emitted unconditionally -- including
in Band A, where the source segment is empty and the receiver segment is one
identity link with both slots empty. "This costs nothing now and is NOT
RETROFITTABLE: a record shape that omits an empty slot cannot later distinguish
'no entries' from 'entries not carried'." So :class:`ChainLink` carries the
slots as fields that are present and possibly empty, never as fields that are
absent.

A STATUS IS CARRIED AND NEVER READ
==================================
The three status tags of the inputs table -- ``exact``, ``certified_outer``,
``exploratory_numeric`` -- are the only three, and NO THEOREM, GATE OR OUTPUT
ROW OF THE CONTRACT READS A STATUS. Nothing in this module branches on one, and
an implementation that let a status decide a verdict would be inventing a rule.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import pairwise
from typing import TYPE_CHECKING, Final

from certiqs_key.domain.chain import (
    LINK_STATUS_VOCABULARY,
    ChainLink,
    LinkStage,
    LinkStatus,
    ReductionChain,
    Side,
    SystemDescriptor,
)
from certiqs_key.domain.constraints import ConstraintEntry, RhsTag
from certiqs_key.foundations.blocks import (
    BlockOperator,
    Label,
    block_sum_in_declared_order,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Matrix,
    add,
    conjugate_transpose,
    dimension,
    equal,
    identity,
    matmul,
    zeros,
)
from certiqs_key.protocol_compiler.reasons import (
    CHAIN_REFUSAL_REASONS,
    AssumptionId,
    ConditionOutcome,
    Refusal,
    RefusalReason,
)
from certiqs_key.protocol_compiler.transcript import (
    PredicateOutcome,
    PredicateSource,
    scoped_to_factor,
    sector_map_predicates,
)
from certiqs_key.transmitter.decoy.reasons import DECOY_ASSUMPTION_MACHINE_KEYS
from certiqs_key.transmitter.links import (
    SOUNDNESS_REGISTRY,
    SoundnessRegistryEntry,
    SourceLink,
    check_source_link,
)
from certiqs_key.transmitter.reasons import ASSUMPTION_MACHINE_KEYS

if TYPE_CHECKING:  # pragma: no cover - NumPy stays off this import path
    pass

__all__ = [
    "CHAIN_CONDITIONS",
    "LINK_STATUS_VOCABULARY",
    "ChainContext",
    "ChainLink",
    "ChainReport",
    "FactorChainReport",
    "LinkStage",
    "LinkStatus",
    "ReductionChain",
    "Side",
    "SystemDescriptor",
    "band_a_chain",
    "check_chain",
    "check_factor_chains",
    "check_licensed_only",
    "check_source_segment",
    "compose_channel",
    "identity_channel",
]


# ---------------------------------------------------------------------
#  THE SIX FROZEN CHAIN RECORDS ARE NOT DECLARED HERE.
#
#  LinkStatus, LinkStage, Side,
#  SystemDescriptor, ChainLink and ReductionChain live in
#  certiqs_key.domain.chain, so that the reductions module can
#  emit them without importing the compiler. They are
#  imported above and re-exported below: ONE WIRE RECORD, ONE
#  DECLARATION. What belongs to this module
#  is the CONSUMER'S EVALUATION of its own conditions -- ChainContext,
#  ChainReport, ConditionOutcome and check_chain.
# ---------------------------------------------------------------------


def identity_channel(dim: int) -> tuple[Matrix, ...]:
    """Return the identity channel as data: the single Kraus operator ``1``."""
    return (identity(dim),)


def compose_channel(
    links: Sequence[ChainLink],
) -> tuple[Matrix, ...] | None:
    """Return the Kraus set of the composite, or ``None`` if any link has none.

    The composite of ``Lambda_L o ... o Lambda_1`` has Kraus set the pairwise
    products, in that order. Returning ``None`` where a link supplies only a
    theorem constructor is what makes (C4) and (S3) ``not checked`` rather than
    false: THE IDENTITY HAS NO LEFT-HAND SIDE, so there is nothing to evaluate.
    """
    if any(link.channel is None for link in links):
        return None
    composite: tuple[Matrix, ...] | None = None
    for link in links:
        assert link.channel is not None
        if composite is None:
            composite = link.channel
            continue
        composite = tuple(
            matmul(later, earlier) for later in link.channel for earlier in composite
        )
    return composite


def _apply_channel(kraus: Sequence[Matrix], state: Matrix) -> Matrix:
    """Return ``Lambda(rho) = sum_i K_i rho K_i^dag``."""
    rows = dimension(kraus[0])
    result: Matrix = zeros(rows, rows)
    for operator in kraus:
        result = add(
            result,
            matmul(matmul(operator, state), conjugate_transpose(operator)),
        )
    return result


def _apply_adjoint(kraus: Sequence[Matrix], operator: Matrix) -> Matrix:
    """Return ``Lambda^dag(Y) = sum_i K_i^dag Y K_i``."""
    cols = len(kraus[0][0])
    result: Matrix = zeros(cols, cols)
    for element in kraus:
        result = add(
            result, matmul(matmul(conjugate_transpose(element), operator), element)
        )
    return result


@dataclass(frozen=True)
class ChainContext:
    """The data the interface conditions are read against.

    Everything (C1)-(C5) and (S1)-(S4) quantify over, and nothing else: the
    physical receiver descriptor and its POVM, the emitted target descriptor
    and its POVM, the declared outcome correspondence, the sector projectors,
    the signal index set with its weights on both sides of the source segment,
    and the two ensembles Eq. ``eq:srcmap`` relates. A pure predicate on data,
    with no compilation step in sight.
    """

    physical_descriptor: SystemDescriptor
    physical_alphabet: tuple[Label, ...]
    physical_povm: Mapping[Label, Matrix]
    target_descriptor: SystemDescriptor
    emitted_alphabet: tuple[Label, ...]
    emitted_povm: Mapping[Label, BlockOperator]
    #: ``gamma : V^ph -> V``, the coarse-graining direction of (C2).
    gamma: Mapping[Label, Label]
    #: (S1): the virtual transmitted system the source segment starts from.
    virtual_descriptor: SystemDescriptor | None = None
    #: (S1): the transmitted system the source segment terminates in.
    transmitted_descriptor: SystemDescriptor | None = None
    signal_alphabet: tuple[Label, ...] = ()
    virtual_weights: Mapping[Label, Fraction] = field(default_factory=dict)
    specified_weights: Mapping[Label, Fraction] = field(default_factory=dict)
    virtual_states: Mapping[Label, Matrix] = field(default_factory=dict)
    specified_states: Mapping[Label, Matrix] = field(default_factory=dict)
    #: (S2): the index set each source link maps onto, per link id.
    link_index_sets: Mapping[str, tuple[Label, ...]] = field(default_factory=dict)


#: The ten conditions of Definition ``def:chaincond``, in its order. (X1) is
#: last and is a TYPING property, not a check.
CHAIN_CONDITIONS: Final[tuple[str, ...]] = (
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "S1",
    "S2",
    "S3",
    "S4",
    "X1",
)


@dataclass(frozen=True)
class _ConditionDecision:
    """One condition's verdict TOGETHER WITH what deciding it recorded.

    A RECORD AND NOT A 2-TUPLE. The nine ``_check_*`` functions below return
    one of these, and a bare pair at nine call sites is exactly the positional
    misreading :class:`~certiqs_key.protocol_compiler.gates.GateEntry`'s
    docstring argues against -- the more so here, where both components are
    themselves collections and neither would fail to unpack the wrong way
    round.

    ``predicates`` IS EMPTY WHERE THE ROW KEYS NOTHING, not where nothing was
    decided: (C2)'s totality and surjectivity count and the slots of (C5) and
    (S4) are decided and are excluded by the ``recorded_predicates`` scope
    note, so their decisions carry the condition's verdict and no key. The
    uniform return type is what gives a later predicate a place to go without
    another signature change.
    """

    outcome: ConditionOutcome
    predicates: tuple[PredicateOutcome, ...] = ()

    @classmethod
    def of(cls, outcome: ConditionOutcome) -> _ConditionDecision:
        """Return a decision that recorded no keyed predicate."""
        return cls(outcome=outcome)


@dataclass(frozen=True)
class ChainReport:
    """The verdict of every interface condition, and the refusal if any.

    ``named_assumption`` is set exactly where a condition is ``not checked``
    because the data ran out; it is A-LINK, and it says the obligation was
    transferred rather than discharged.
    """

    verdicts: dict[str, ConditionOutcome]
    failing_condition: str | None
    named_assumption: AssumptionId | None
    refusal: Refusal | None
    #: THE PER-PREDICATE TRANSCRIPT of the conditions, in the order
    #: :func:`check_chain` decided them -- which is the conditions' own order
    #: with (C4) and (S3) last, because both read the verdicts of the
    #: conditions before them. A DEFAULTED FIELD, so that a report assembled by
    #: hand stays valid and an unfilled transcript is a visible ``()``.
    predicates: tuple[PredicateOutcome, ...] = ()

    @property
    def refuses(self) -> bool:
        """Whether the chain is refused."""
        return self.refusal is not None

    def verdict(self, condition: str) -> ConditionOutcome:
        """Return the verdict of one named condition."""
        return self.verdicts[condition]


def check_chain(chain: ReductionChain, context: ChainContext) -> ChainReport:
    """Decide (C1)-(C5) and (S1)-(S4) on the presented data; report (X1) as typing.

    Every condition is evaluated and recorded. A chain failing one is refused
    "with that condition named" (Theorem ``thm:chain-consumption`` (i)), and the FIRST
    failure in the conditions' own order is the one the refusal names, so that
    a refusal points where the contract says it points rather than at whichever
    condition an implementation happened to test last.

    THE TRANSCRIPT IS IN THE ORDER THE CONDITIONS WERE DECIDED, which is the
    order below and not ``CHAIN_CONDITIONS``: (C4) and (S3) are decided LAST
    because each reads the verdicts of the conditions before it, and a record
    that claimed the contract's order would misreport when each decision was
    taken. Which decisions are keyed is the ``gate_report`` row's
    ``recorded_predicates``: "the exact identities (C4) and the source
    identity (S3), together with the descriptor decisions of (C1) and (S1) ...
    and (S2)'s comparison of the two index sets each source link carries and of
    the |X| declared weights p_x it leaves untouched".
    """
    verdicts: dict[str, ConditionOutcome] = {}
    decided: list[PredicateOutcome] = []

    def take(condition: str, decision: _ConditionDecision) -> None:
        """Record one condition's verdict and what deciding it recorded."""
        verdicts[condition] = decision.outcome
        decided.extend(decision.predicates)

    take("C1", _check_c1(chain, context))
    take("C2", _check_c2(context))
    take("C3", _check_c3(context))
    take("C5", _ConditionDecision.of(ConditionOutcome.HOLDS))
    take("S1", _check_s1(chain, context))
    take("S2", _check_s2(chain, context))
    take(
        "S4",
        _ConditionDecision.of(
            ConditionOutcome.VACUOUS
            if not chain.source_segment
            else ConditionOutcome.HOLDS
        ),
    )
    take("C4", _check_c4(chain, context, verdicts))
    take("S3", _check_s3(chain, context, verdicts))
    # (X1) is the type of the record and is answered by construction; it is
    # never the failing condition and carries no refusal reason.
    take("X1", _ConditionDecision.of(ConditionOutcome.HOLDS))

    named_assumption = (
        AssumptionId.A_LINK
        if any(
            verdicts[condition] is ConditionOutcome.NOT_CHECKED
            and _is_supplier_gap(condition, chain)
            for condition in ("C4", "S3")
        )
        else None
    )

    failing = next(
        (
            condition
            for condition in CHAIN_CONDITIONS
            if verdicts[condition] is ConditionOutcome.FAILS
        ),
        None,
    )
    refusal = (
        None
        if failing is None
        else Refusal(
            # ONE REASON FOR ALL NINE CONDITIONS, AND THE CONDITION IN THE
            # DETAIL. interface.yaml fixes exactly one spelling of its own
            # for this row and its machine keys are binding; def:chaincond
            # and thm:chain-consumption (i) require the refusal to NAME the condition,
            # which this string plus `failing` -- carried as a datum on the
            # report beside the reason -- does.
            reason=CHAIN_REFUSAL_REASONS[failing],
            detail=(
                f"the presented reduction chain fails interface condition "
                f"({failing}) of Definition def:chaincond"
            ),
        )
    )
    return ChainReport(
        verdicts=verdicts,
        failing_condition=failing,
        named_assumption=named_assumption,
        refusal=refusal,
        predicates=tuple(decided),
    )


def _is_supplier_gap(condition: str, chain: ReductionChain) -> bool:
    """Whether a ``not checked`` verdict is the A-LINK gap and not a cascade."""
    links = chain.receiver_segment if condition == "C4" else chain.source_segment
    if condition == "S3" and not links:
        return False
    return any(not link.channel_supplied for link in links)


def _check_c1(chain: ReductionChain, context: ChainContext) -> _ConditionDecision:
    """(C1): descriptor match across the receiver segment and at both ends.

    The last clause is the one 0.3.0 sharpened: "the target descriptor of
    ``Lambda_L`` is ``(Q, Smap)`` -- that is, THE LAST LINK'S TARGET DESCRIPTOR
    IS THE SECTOR MAP. THAT EQUALITY IS DECIDED HERE AND NOWHERE ELSE: it is a
    condition on the chain record and not on a slot of Eq. eq:declaration, so
    NO TARGET CONDITION QUANTIFIES OVER IT AND CHECK V1 DOES NOT READ IT. It is
    decided BY THE SAME FOUR-COMPONENT COMPARISON V1 MAKES on the map of a
    declared Q-operator family, and a chain failing it is refused NAMING (C1)."

    THE THREE CLAUSES ARE THE THREE THE ROW KEYS SEPARATELY: "(C1)'s inter-link
    matches, its match of ``Lambda_1``'s source descriptor against the physical
    receiver space, and its last clause, the four-component comparison of
    ``Lambda_L``'s target descriptor against ``(Q, Smap)``" -- the first per
    adjacent PAIR of links, the second and third on one link each, and the last
    in the same four components :func:`
    ~certiqs_key.protocol_compiler.validation._sector_map_predicates` records
    for V1.
    """
    links = chain.receiver_segment
    recorded: list[PredicateOutcome] = []

    def record(predicate: str, element: str, outcome: bool, index: int) -> None:
        """Record one of (C1)'s descriptor decisions, WITH ITS LINK INDEX.

        ``index`` is 1-based in the receiver segment's own order, which is the
        "link index" the row asks a failed predicate for; for a decision on an
        adjacent PAIR it is the index of the EARLIER link, the pair being the
        one that starts there.
        """
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.C1,
                predicate=predicate,
                element=element,
                block=None,
                outcome=outcome,
                first_failure_index=None if outcome else index,
            )
        )

    for position, (earlier, later) in enumerate(pairwise(links), start=1):
        adjacent = earlier.target_descriptor == later.source_descriptor
        record(
            "the target descriptor of the earlier link is the source "
            "descriptor of the later",
            f"{earlier.link_id} -> {later.link_id}",
            adjacent,
            position,
        )
        if not adjacent:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    first_matches = links[0].source_descriptor == context.physical_descriptor
    record(
        "the source descriptor of Lambda_1 is the physical receiver space",
        links[0].link_id,
        first_matches,
        1,
    )
    if not first_matches:
        return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    last = links[-1].target_descriptor
    target = context.target_descriptor
    last_id = links[-1].link_id
    named = (
        last.name == target.name
        and last.dim == target.dim
        and last.side == target.side
    )
    record(
        "the target descriptor of Lambda_L is (Q, Smap) in name, dimension "
        "and side",
        last_id,
        named,
        len(links),
    )
    if not named:
        return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    # THE FOUR-COMPONENT COMPARISON, on the map itself. A descriptor carrying
    # identifiers but no block kind has no map to compare and is REFUSED, never
    # completed with one of this module's choosing.
    both_carry_a_map = (last.sectors is None) == (target.sectors is None)
    record(
        "the target descriptor of Lambda_L carries a sector map exactly where "
        "(Q, Smap) does",
        last_id,
        both_carry_a_map,
        len(links),
    )
    if not both_carry_a_map:
        return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    if last.sectors is not None:
        declared = last.sector_map()
        emitted = target.sector_map()
        comparable = declared is not None and emitted is not None
        record(
            "both maps carry the block kind their comparison needs",
            last_id,
            comparable,
            len(links),
        )
        if declared is None or emitted is None:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
        disagreement = emitted.disagreement(declared)
        recorded.extend(
            sector_map_predicates(PredicateSource.C1, last_id, disagreement)
        )
        if disagreement is not None:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    return _ConditionDecision(ConditionOutcome.HOLDS, tuple(recorded))


def _check_c2(context: ChainContext) -> _ConditionDecision:
    """(C2): ``gamma`` is a tabulated TOTAL SURJECTION ``V^ph -> V``.

    Totality and surjectivity "by counting preimages" (Theorem ``thm:chain-consumption``
    (i)). The direction is forced by Remark ``rem:coarse``: a correspondence
    tabulated the other way round -- emitted onto physical -- is not a
    coarse-graining and fails here.

    NOTHING IS KEYED HERE AND THAT IS THE ROW'S DECISION: the
    ``recorded_predicates`` scope note excludes "(C2)'s totality and
    surjectivity count" by name, with the rest of the combinatorial and
    presence tests, "recorded through the outcome of the gate that carries
    them ... and, where one fails, through ``refusal``".
    """
    for outcome in context.physical_alphabet:
        if outcome not in context.gamma:
            return _ConditionDecision.of(ConditionOutcome.FAILS)
    if any(key not in context.physical_alphabet for key in context.gamma):
        return _ConditionDecision.of(ConditionOutcome.FAILS)
    images = {context.gamma[outcome] for outcome in context.physical_alphabet}
    if any(image not in context.emitted_alphabet for image in images):
        return _ConditionDecision.of(ConditionOutcome.FAILS)
    if images != set(context.emitted_alphabet):
        return _ConditionDecision.of(ConditionOutcome.FAILS)
    return _ConditionDecision.of(ConditionOutcome.HOLDS)


def _check_c3(context: ChainContext) -> _ConditionDecision:
    """(C3): ``{F_v}`` is a family of block lists, and a POVM PER BLOCK.

    "``{F_v}`` is a family of block lists against ``Smap`` -- TYPING, HELD BY
    THE EMITTED FORM AND NOT CHECKED -- and FOR EACH ``s`` the block family
    ``{F_v^(s)}_v`` is a POVM on ``Q_s``, decided EXACTLY on the emitted blocks
    themselves: ``F_v^(s)`` Hermitian and positive semidefinite for each ``v``,
    ``sum_v F_v^(s) = 1_{Q_s}``, and THE DECLARED-ORDER SUM FORMING IT ROUNDING
    NOWHERE."

    THERE IS NO BLOCK-DIAGONALITY LOOP HERE.
    Block-diagonality is typing -- a ``BlockOperator`` cannot express an
    off-block entry -- so "a chain that merely CLAIMS a block structure cannot
    smuggle one past the check" holds by construction rather than by an
    evaluation. "This condition is CHECK V3 RESTRICTED TO ``{F_v}`` and states
    the same list of conjuncts ...; THE TWO CAN NEVER BE AMENDED APART."

    NOTHING IS KEYED HERE, AND UNLIKE (C2) THAT IS A RESIDUE AND NOT A
    DECISION OF THE ROW. The ``recorded_predicates`` enumeration does not name
    (C3) at all: its eight items key check V2's and V3's decisions on the
    EMITTED families, (C1), (C4), (S1), (S2), (S3), the certificate's
    conditions and the compilation map's. Its scope note names only "(C3)'s
    TYPING HALF" among the conditions decided nowhere -- and the conditions
    decided HERE are the other half, the four legs of Definition ``def:exact``
    on the family the last link delivered, which the row's own first clause
    ("per exact predicate of Definition ``def:exact`` that the compiler
    decided") does reach. The two halves of the row therefore disagree about
    (C3), and which one binds is an INTERFACE question and not an
    implementer's: the enumeration is keyed and (C3) is left unkeyed.
    Deciding it the other way would
    add keys the scope note says the record does not carry.
    """
    sector_map = context.target_descriptor.sector_map()
    if sector_map is None:
        return _ConditionDecision.of(ConditionOutcome.FAILS)
    elements = [context.emitted_povm[label] for label in context.emitted_alphabet]
    if not elements:
        return _ConditionDecision.of(ConditionOutcome.FAILS)
    for element in elements:
        if not sector_map.agrees_with(element.sector_map):
            return _ConditionDecision.of(ConditionOutcome.FAILS)
        if not element.is_hermitian() or not element.is_positive_semidefinite():
            return _ConditionDecision.of(ConditionOutcome.FAILS)
    for position, verdict in enumerate(block_sum_in_declared_order(elements)):
        if not verdict.computed_total_equals(identity(sector_map.dims[position])):
            return _ConditionDecision.of(ConditionOutcome.FAILS)
        if not verdict.rounds_nowhere:
            return _ConditionDecision.of(ConditionOutcome.FAILS)
    return _ConditionDecision.of(ConditionOutcome.HOLDS)


def _check_c4(
    chain: ReductionChain,
    context: ChainContext,
    verdicts: Mapping[str, ConditionOutcome],
) -> _ConditionDecision:
    """(C4): the pullback identity Eq. ``eq:pullback``, WHERE CHECKABLE.

    ``Lambda^dag(F_v) = sum_{w in gamma^{-1}(v)} F^ph_w`` for every ``v``, with
    the fibre SUMMED -- which is the whole difference from a bare index map.
    ``not checked`` where the composite does not exist (A-LINK) or where (C1)
    or (C2) has already failed, so that the identity is never evaluated on
    data whose descriptors do not compose or whose fibres are undefined.

    THIS FUNCTION FORMS THE WHOLE-SPACE ``F_v``, AND THAT DIVERGES FROM A
    BINDING CONVENTION. It calls ``BlockOperator.dense()`` on the emitted
    element in order to apply the composed adjoint, which builds a
    ``d_Q x d_Q`` array -- and the ``operator_form`` convention says "NO
    ``d_Q x d_Q`` OR ``d_A d_Q x d_A d_Q`` ARRAY IS FORMED ON ANY PATH THIS
    CONTRACT DESCRIBES".

    IT DOES SO BECAUSE THE CONTRACT LEAVES NO OTHER ROUTE, and that is the
    substance of the divergence rather than an excuse for it. Definition
    ``def:chaincond`` (C4) is stated on the WHOLE-SPACE ``F_v``, and the
    ``reduction_chain`` input row types a link's channel as UNDECOMPOSED
    DATA -- a Kraus set on ``Q``, carrying no sector structure of its own -- so
    there is no per-block adjoint to apply and no per-block form of the
    identity to decide. The convention and (C4) cannot both be honoured on the
    data the claims type.
    The sibling site :meth:`certiqs_key.foundations.blocks.JointBlockOperator.dense`
    carries the opposite note -- "FORMED BY NO PREDICATE OF THIS MODULE" -- and
    that note stays true; this is the one predicate that forms one.

    THE DIVERGENCE IS DISCLOSED, NOT RESOLVED. THE CONTRACT-SIDE RESOLUTION --
    scope the convention so that it does not reach (C4), or give (C4) a
    per-block form together with a per-block typing of the link channel -- IS
    A CONTRACT CHANGE and not an implementer's to take (the implementer role
    file).
    ``interface.yaml`` carries the same disclosure under
    ``conventions.operator_form_divergence_at_c4_note``.
    """
    if verdicts["C1"] is not ConditionOutcome.HOLDS:
        return _ConditionDecision.of(ConditionOutcome.NOT_CHECKED)
    if verdicts["C2"] is not ConditionOutcome.HOLDS:
        return _ConditionDecision.of(ConditionOutcome.NOT_CHECKED)
    composite = compose_channel(chain.receiver_segment)
    if composite is None:
        return _ConditionDecision.of(ConditionOutcome.NOT_CHECKED)
    # THE IDENTITY IS RECORDED PER EMITTED OUTCOME, which is what it is
    # quantified over ("for every ``v``"), and NOT AT ALL on the three branches
    # above: a ``not checked`` verdict means the identity was never evaluated,
    # and an entry claiming otherwise would report a computation nothing made.
    recorded: list[PredicateOutcome] = []
    for outcome_index, emitted in enumerate(context.emitted_alphabet, start=1):
        fibre = [
            outcome
            for outcome in context.physical_alphabet
            if context.gamma[outcome] == emitted
        ]
        dim = context.physical_descriptor.dim
        if dim is None:  # Receiver descriptors reject this at construction.
            raise MalformedInputError("(C4) requires a finite receiver dimension")
        total: Matrix = zeros(dim, dim)
        for outcome in fibre:
            total = add(total, context.physical_povm[outcome])
        pulled_back = _apply_adjoint(composite, context.emitted_povm[emitted].dense())
        holds = equal(pulled_back, total)
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.C4,
                predicate="Lambda^dag(F_v) = sum_{w in gamma^{-1}(v)} F^ph_w",
                element=f"F_{emitted}",
                block=None,
                outcome=holds,
                first_failure_index=None if holds else outcome_index,
            )
        )
        if not holds:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    return _ConditionDecision(ConditionOutcome.HOLDS, tuple(recorded))


def _check_s1(chain: ReductionChain, context: ChainContext) -> _ConditionDecision:
    """(S1): descriptor match across the source segment, and ALICE-SIDE throughout.

    The two end clauses -- the source descriptor of ``Xi_1`` is the virtual
    transmitted system ``A''`` and the target descriptor of ``Xi_{L_s}`` is the
    transmitted system ``A'`` -- and the adjacency clause between them; plus
    the clause that decides a misplaced squashing link, that EVERY descriptor
    of the segment is Alice-side.

    THE ROW KEYS "(S1)'s inter-link matches", per adjacent PAIR, and the three
    clauses beside them are recorded per LINK: the side clause on each link and
    the two end clauses on the first and the last. At ``L_s = 0`` the condition
    is VACUOUS and nothing is recorded -- there is no link to decide anything
    on, which Theorem ``thm:band-a`` (ii) is the statement of.
    """
    links = chain.source_segment
    if not links:
        return _ConditionDecision.of(ConditionOutcome.VACUOUS)
    recorded: list[PredicateOutcome] = []

    def record(predicate: str, element: str, outcome: bool, index: int) -> None:
        """Record one of (S1)'s descriptor decisions, WITH ITS LINK INDEX.

        1-based in the source segment's own order, and for a decision on an
        adjacent PAIR the index of the EARLIER link -- the same convention
        :func:`_check_c1` uses on the receiver segment.
        """
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.S1,
                predicate=predicate,
                element=element,
                block=None,
                outcome=outcome,
                first_failure_index=None if outcome else index,
            )
        )

    for position, link in enumerate(links, start=1):
        alice_side = (
            link.source_descriptor.side is Side.ALICE
            and link.target_descriptor.side is Side.ALICE
        )
        record(
            "both descriptors of the link are Alice-side",
            link.link_id,
            alice_side,
            position,
        )
        if not alice_side:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    for position, (earlier, later) in enumerate(pairwise(links), start=1):
        adjacent = earlier.target_descriptor == later.source_descriptor
        record(
            "the target descriptor of the earlier link is the source "
            "descriptor of the later",
            f"{earlier.link_id} -> {later.link_id}",
            adjacent,
            position,
        )
        if not adjacent:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    if context.virtual_descriptor is not None:
        starts = links[0].source_descriptor == context.virtual_descriptor
        record(
            "the source descriptor of Xi_1 is the virtual transmitted system",
            links[0].link_id,
            starts,
            1,
        )
        if not starts:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    if context.transmitted_descriptor is not None:
        ends = links[-1].target_descriptor == context.transmitted_descriptor
        record(
            "the target descriptor of Xi_{L_s} is the transmitted system",
            links[-1].link_id,
            ends,
            len(links),
        )
        if not ends:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    return _ConditionDecision(ConditionOutcome.HOLDS, tuple(recorded))


def _check_s2(chain: ReductionChain, context: ChainContext) -> _ConditionDecision:
    """(S2): index preservation, with THE WEIGHTS UNTOUCHED.

    "Each link carries the signal index ``x`` through unchanged: it maps a
    family indexed by ``X`` to a family indexed by ``X``, WITH THE WEIGHTS
    ``p_x`` UNTOUCHED." Two independent halves, and a link may preserve the
    index set and reweight -- which is why both are tested. Theorem
    ``thm:chain-consumption`` (iv) is where the second half does its work: a link that
    reweighted would carry the classical-quantum source state onto a different
    one, and (SR2) -- which reads weight and state TOGETHER -- would then be
    checked against the wrong ``p_x``.
    """
    links = chain.source_segment
    if not links:
        return _ConditionDecision.of(ConditionOutcome.VACUOUS)
    if any(
        link.source_descriptor.side is not Side.ALICE
        or link.target_descriptor.side is not Side.ALICE
        for link in links
    ):
        # A link whose descriptors are not Alice-side is not TYPED as a source
        # map at all, so "it maps a family indexed by X to a family indexed by
        # X" has nothing to be evaluated against. NOT CHECKED, not false --
        # which keeps the refusal pointing at the one condition that decided
        # it, (S1), as "refused WITH THAT CONDITION NAMED" requires.
        return _ConditionDecision.of(ConditionOutcome.NOT_CHECKED)
    # THE ROW KEYS BOTH HALVES SEPARATELY: "(S2)'s comparison of the two index
    # sets each source link carries and of the |X| declared weights p_x it
    # leaves untouched" -- the first per LINK, the second per SIGNAL LABEL.
    recorded: list[PredicateOutcome] = []

    def record(predicate: str, element: str, outcome: bool, index: int) -> None:
        """Record one of (S2)'s two kinds of decision, with its own index.

        The LINK INDEX for the index-set comparison and the SIGNAL INDEX for
        the weight comparison, both 1-based in their own declared order: the
        two halves range over different enumerations, which is why the row
        names four kinds of index and not one.
        """
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.S2,
                predicate=predicate,
                element=element,
                block=None,
                outcome=outcome,
                first_failure_index=None if outcome else index,
            )
        )

    for position, link in enumerate(links, start=1):
        declared = context.link_index_sets.get(link.link_id)
        if declared is None:
            # The link declares no index set, so the comparison has no second
            # side and is not made. Nothing is recorded for it.
            continue
        carries_x = set(declared) == set(context.signal_alphabet)
        record(
            "the link maps a family indexed by X to a family indexed by X",
            link.link_id,
            carries_x,
            position,
        )
        if not carries_x:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    for signal, label in enumerate(context.signal_alphabet, start=1):
        virtual = context.virtual_weights.get(label)
        specified = context.specified_weights.get(label)
        untouched = (
            virtual is not None and specified is not None and virtual == specified
        )
        # THE PREDICATE NAMES BOTH HALVES OF WHAT `untouched` DECIDES.
        # The conjunction is
        # false in two different ways -- the weight is tabulated on both sides
        # and differs, or it is absent from one side -- and a record saying
        # only "left untouched" would tell a consumer the segment reweighted a
        # weight that was never there to reweight. The (S2) VERDICT is `fails`
        # either way and does not move.
        record(
            "p_x is tabulated on both sides and equal",
            f"p_{label}",
            untouched,
            signal,
        )
        if not untouched:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    return _ConditionDecision(ConditionOutcome.HOLDS, tuple(recorded))


def _check_s3(
    chain: ReductionChain,
    context: ChainContext,
    verdicts: Mapping[str, ConditionOutcome],
) -> _ConditionDecision:
    """(S3): the source identity Eq. ``eq:srcmap``, WHERE CHECKABLE.

    ``Xi(rho^v_x) = rho_x`` for every ``x``. NOTE THE DIRECTION: the channel
    runs from the VIRTUAL states to the SPECIFIED ones, and the object the
    compiler emits is the virtual protocol. At ``L_s = 0`` the segment is
    empty, ``Xi`` is the identity, ``A'' = A'`` and ``rho^v_x = rho_x``, so the
    condition is vacuous.

    The compiler "checks this identity AND NOTHING BEYOND IT" (Theorem
    ``thm:chain-consumption`` (iv)); that security of the virtual protocol transfers to
    the real one is Assumption ``ass:link``, which this contract never verifies and
    never asserts.
    """
    links = chain.source_segment
    if not links:
        return _ConditionDecision.of(ConditionOutcome.VACUOUS)
    if verdicts["S1"] is not ConditionOutcome.HOLDS:
        return _ConditionDecision.of(ConditionOutcome.NOT_CHECKED)
    if verdicts["S2"] is not ConditionOutcome.HOLDS:
        # With (S2) failed the two families are not indexed compatibly and the
        # weights are not the ones the segment presents, so Eq. eq:srcmap would
        # be read against an ensemble the link does not carry. NOT CHECKED.
        return _ConditionDecision.of(ConditionOutcome.NOT_CHECKED)
    composite = compose_channel(links)
    if composite is None:
        return _ConditionDecision.of(ConditionOutcome.NOT_CHECKED)
    # THE IDENTITY IS RECORDED PER SIGNAL LABEL, which is what it is quantified
    # over ("for every ``x``"). A label whose state is missing on either side
    # makes the identity NOT CHECKED, and what was recorded for the labels
    # before it stands: those decisions were taken.
    recorded: list[PredicateOutcome] = []
    for signal, label in enumerate(context.signal_alphabet, start=1):
        virtual = context.virtual_states.get(label)
        specified = context.specified_states.get(label)
        if virtual is None or specified is None:
            return _ConditionDecision(
                ConditionOutcome.NOT_CHECKED, tuple(recorded)
            )
        holds = equal(_apply_channel(composite, virtual), specified)
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.S3,
                predicate="Xi(rho^v_x) = rho_x",
                element=f"rho^v_{label}",
                block=None,
                outcome=holds,
                first_failure_index=None if holds else signal,
            )
        )
        if not holds:
            return _ConditionDecision(ConditionOutcome.FAILS, tuple(recorded))
    return _ConditionDecision(ConditionOutcome.HOLDS, tuple(recorded))


def band_a_chain(target: SystemDescriptor) -> ReductionChain:
    """Return the Band-A chain of Definition ``def:banda`` (b).

    ``L_s = 0`` and ``L = 1`` with ``Lambda_1 = id_Q``, status ``exact``, empty
    constraint slot and empty licence slot. A DATA CONSTRUCTOR and not an
    emission decision: the record is what Theorem ``thm:band-a`` (ii) evaluates
    the ten conditions on, and the empty source segment together with the two
    empty-but-present slots is exactly what Requirement
    ``req:chain-record-slots`` requires be representable.
    """
    if target.side is not Side.RECEIVER:
        raise MalformedInputError(
            "the Band-A target descriptor is the receiver system Q"
        )
    if target.dim is None:  # Receiver descriptors reject this at construction.
        raise MalformedInputError("the Band-A receiver target has a finite dimension")
    link = ChainLink(
        link_id="Lambda_1",
        segment=LinkStage.RECEIVER,
        link_type="squashing (identity)",
        source_descriptor=target,
        target_descriptor=target,
        status=LinkStatus.EXACT,
        channel=identity_channel(target.dim),
        transported_constraints=(),
        license_slot=None,
    )
    return ReductionChain(source_segment=(), receiver_segment=(link,))

# ---------------------------------------------------------------------------
#  THE GENERAL FORMAT: one receiver segment per measured factor, a non-empty
#  source segment, and the licensed-only rule (``def:chaincond``, the three
#  appended paragraphs).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FactorChainReport:
    """The per-factor verdicts of ``def:chaincond`` in its general-format reading.

    ``def:chaincond``, the general format: with
    ``Ch_rec = (Ch^f_rec)_{f in F}`` the conditions (C1)--(C5) "are decided OF EACH
    SEGMENT SEPARATELY, AND OF NOTHING ACROSS TWO SEGMENTS", and a failure is
    ``chain_interface_condition_failed`` "naming the condition AND THE FACTOR".

    THE PRODUCT COMPOSITE AND THE PRODUCT PULLBACK ARE FORMED BY NO ONE:
    ``eq:pullback-product`` "is a consequence of ``eq:pullback-factor`` and of the
    product rule ``eq:productfamily`` -- it is ``reductions/thm:emitted-product``
    (ii), named here and decided here by nothing -- and (C4) is the per-factor
    identity and nothing wider". So this record holds one ordinary
    :class:`ChainReport` per factor and composes no channel across two.

    WITH ONE FACTOR IT IS ONE REPORT and every field below is that report's, which
    is the accepted format.
    """

    #: One report per measured factor, IN THE ORDER OF ``F``, paired with the
    #: FACTOR'S OWN LABEL -- which is what the refusal names beside the condition.
    #: NOT the party label: a party may hold two measured factors, so a report
    #: keyed by party could not say which segment failed, which is the same
    #: distinction ``constraint_scope_not_a_factor`` rests on.
    per_factor: tuple[tuple[Label, ChainReport], ...]
    #: The first ``(factor, condition)`` that failed, in the order of ``F`` and
    #: then of the conditions, or ``None``.
    failing: tuple[Label, str] | None
    refusal: Refusal | None
    named_assumption: AssumptionId | None
    predicates: tuple[PredicateOutcome, ...] = ()

    @property
    def refuses(self) -> bool:
        """Whether some factor's segment is refused."""
        return self.refusal is not None

    def report_of(self, factor: Label) -> ChainReport:
        """Return one factor's report, BY THAT FACTOR'S OWN LABEL."""
        for label, report in self.per_factor:
            if label == factor:
                return report
        raise KeyError(f"no receiver segment for the measured factor {factor!r}")


def check_factor_chains(
    segments: Sequence[tuple[Label, ReductionChain, ChainContext]],
) -> FactorChainReport:
    """Decide (C1)--(C5) OF EACH FACTOR'S RECEIVER SEGMENT SEPARATELY.

    Each element is one factor's own LABEL -- not its party label, a party being
    able to hold two factors -- that factor's own chain record and
    the context its conditions are read against -- whose target descriptor is
    "(Q_f, S^f, (d_{f,s_f})) -- THAT FACTOR'S OWN SECTOR MAP, AND NOT THE PRODUCT
    MAP, which is derived by (DX1) and is the target descriptor of nothing".

    THE FIRST FAILURE IN THE ORDER OF ``F`` AND THEN OF THE CONDITIONS is the one
    the refusal names, for the reason :func:`check_chain` names the first in the
    conditions' own order: a refusal points where the contract says it points
    rather than at whichever segment an implementation happened to read last.

    THE SOURCE SEGMENT IS NOT DECIDED PER FACTOR. There is ONE source segment --
    its links act on the transmitted system and not on any receiver factor -- so
    it is decided once, by :func:`check_source_segment`, and the segments this
    function is given carry an EMPTY source list. A caller that passed the same
    source segment to every factor would decide (S1)--(S4) once per factor and
    report one defect ``|F|`` times.

    THE TRANSCRIPT NAMES THE FACTOR WHERE THERE ARE SEVERAL. ``predicates``
    keys each segment's decisions ``<factor>:<element>`` when more than one
    segment is given (the transcript module's factor rule): two factors of one
    party emit families over the same letters, so their (C4) decisions on
    ``F_<v>`` would otherwise share a key. Each factor's own
    :class:`ChainReport` in ``per_factor`` keeps its unprefixed record, being
    one segment's report read on its own.
    """
    if not segments:
        raise MalformedInputError(
            "a chain in the general format carries ONE receiver segment PER "
            "MEASURED FACTOR and (DX1) declares at least one measured factor; an "
            "empty list describes no declaration (def:spec (c'))"
        )
    reports: list[tuple[Label, ChainReport]] = []
    decided: list[PredicateOutcome] = []
    failing: tuple[Label, str] | None = None
    named: AssumptionId | None = None
    several_factors = len(segments) > 1
    for factor, chain, context in segments:
        if chain.source_segment:
            raise MalformedInputError(
                f"the receiver segment of the measured factor {factor!r} was "
                "given a non-empty SOURCE segment; there is one source segment "
                "per chain and it is decided once (def:chaincond, the general "
                "format), not once per factor"
            )
        report = check_chain(chain, context)
        reports.append((factor, report))
        decided.extend(
            scoped_to_factor(report.predicates, factor)
            if several_factors
            else report.predicates
        )
        if report.named_assumption is not None and named is None:
            named = report.named_assumption
        if failing is None and report.failing_condition is not None:
            failing = (factor, report.failing_condition)
    refusal = (
        None
        if failing is None
        else Refusal(
            reason=CHAIN_REFUSAL_REASONS[failing[1]],
            detail=(
                "the presented reduction chain fails interface condition "
                f"({failing[1]}) of Definition def:chaincond in the receiver "
                f"segment of the measured factor {failing[0]!r}"
            ),
        )
    )
    return FactorChainReport(
        per_factor=tuple(reports),
        failing=failing,
        refusal=refusal,
        named_assumption=named,
        predicates=tuple(decided),
    )


def check_source_segment(
    links: Sequence[SourceLink],
    *,
    assumption_ledger: Sequence[str],
    from_admitting_module: bool,
    registry: Sequence[SoundnessRegistryEntry] = SOUNDNESS_REGISTRY,
) -> Refusal | None:
    """Decide (A1)--(A3) of a PRESENTED non-empty source segment, or return ``None``.

    ``def:chaincond``, the source-segment paragraph: beside (S1)--(S4)
    this module decides "(A1)--(A3) of that definition, WHICH ARE DECIDED ON DATA
    AND ARE NOT PART OF (S1)--(S4): that the triple a link's obligation record
    carries ... appears ENTRY BY ENTRY in the soundness registry the artefact
    carrying the segment emits, both components of that registry entry's
    assumption list compared ...; that every assumption of that entry is in the
    artefact's assumption ledger; and that the segment is presented inside an
    artefact of the module that admits its links."

    THE DECIDER IS THE TRANSMITTER'S AND IS CALLED, NOT RE-SPELLED.
    :func:`certiqs_key.transmitter.links.check_source_link` is where those
    conditions are written, on the record type that declares them; a second
    implementation here would be a second spelling of one rule, and the refusal
    strings it returns are that module's. THIS IS THE ONE DOCKING FUNCTION FOR THE
    SOURCE SIDE.

    WHAT IT DOES NOT DECIDE, and the absence is the claim's: "that the named
    claim's conclusion applies to these descriptors -- family membership is the
    emitting module's assertion and NO CONSUMER RE-PROVES A THEOREM". (S3)'s share
    for a data link is decided by :func:`check_chain` on the presented channel, and
    for a constructor link it is carried as Assumption ``ass:link``.

    An empty segment reaches this function as an empty list and is admitted
    vacuously.
    """
    short_ledger = set(assumption_ledger)
    short_ledger.update(
        str(identifier)
        for identifier, machine_key in (
            *ASSUMPTION_MACHINE_KEYS.items(),
            *DECOY_ASSUMPTION_MACHINE_KEYS.items(),
        )
        if machine_key in assumption_ledger
    )
    for link in links:
        refusal = check_source_link(
            link,
            assumption_ledger=tuple(short_ledger),
            from_admitting_module=from_admitting_module,
            registry=registry,
        )
        if refusal is not None:
            return Refusal(
                reason=RefusalReason(str(refusal.reason)),
                detail=refusal.detail,
            )
    return None


def check_licensed_only(
    entries: Sequence[ConstraintEntry], *, source_segment_is_non_empty: bool
) -> Refusal | None:
    """Decide THE LICENSED-ONLY RULE beside a non-empty source segment.

    ``def:chaincond``: "Beside a non-empty source segment EVERY entry of the
    emitted ``CList`` is required to carry A REAL SCALAR as its right-hand side --
    ``homogeneous``, ``party_local``, or an untrusted-mode scalar -- and an entry
    declared ``general`` is REFUSED, with reason
    ``general_entry_beside_source_segment`` naming the entry."

    IT IS A REFUSAL OF A CASE THE ACCEPTED FORMAT ADMITS, AND THAT IS STATED
    RATHER THAN GLOSSED. A non-empty source segment is declarable in the accepted
    format, and WERE THIS RULE ABSENT a ``general`` entry beside one would, where
    no other condition or gate refused it, reach the gates and be emitted with
    ``key_length_eligible`` false by row 5 of the gate outcome table. Under this
    rule the case is refused where the chain is consumed, before any
    declaration exists, so row 5 is never reached for it. "The two outcomes are
    not the same, and THE SECOND IS STRICTLY THE MORE CONSERVATIVE."

    THE CASE IS REACHABLE: a presented chain may carry a non-empty source segment,
    "and the rule is then simply a refusal, which is the direction a consumer may
    always take".

    THE REASON IS THIS MODULE'S SIDE OF ANOTHER MODULE'S RULE: "the consuming side
    of the admission rule of ``reductions/def:chain``, whose reason is that
    module's ``lem:precomposition`` and its counterexample"; this module states
    neither and decides THE TYPE OF THE ENTRY.
    """
    if not source_segment_is_non_empty:
        return None
    for index, entry in enumerate(entries, start=1):
        if entry.tag is RhsTag.GENERAL:
            return Refusal(
                reason=RefusalReason.GENERAL_ENTRY_BESIDE_SOURCE_SEGMENT,
                detail=(
                    f"entry {index} of the emitted constraint list is declared "
                    "`general` and stands beside a NON-EMPTY source segment, where "
                    "every entry must carry a real scalar -- `homogeneous`, "
                    "`party_local`, or an untrusted-mode scalar (def:chaincond, "
                    "the licensed-only rule; def:homog). The accepted format "
                    "admits this case, and without the rule it would, where no "
                    "other condition or gate refused it, reach the gates and be "
                    "emitted with key_length_eligible false by row 5 of the "
                    "gate outcome table; the rule REFUSES it here, "
                    "before any declaration exists, which is strictly the more "
                    "conservative outcome"
                ),
            )
    return None
