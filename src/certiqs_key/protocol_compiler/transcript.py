"""The per-predicate transcript: WHAT WAS DECIDED, KEYED BY (source, element, block).

WHAT THIS MODULE ANSWERS, AND IT IS THE SECOND HALF OF ONE OUTPUT ROW
====================================================================
``spec/modules/protocol-compiler/interface.yaml``'s ``outputs.gate_report``
asks for two things. The first is a verdict per gate with the degeneration
record of Remark ``rem:degenerate``, which :class:`
~certiqs_key.protocol_compiler.gates.GateReport` emits. The
second is this: "per exact predicate of Definition ``def:exact`` that the
compiler decided, and per further decision of the kind the enumeration beneath
this table delimits, THE OUTCOME, KEYED BY (source, element, block)", with "a
FAILED predicate ... recorded with the block, outcome, signal or entry index at
which it FIRST failed, and (S) additionally with the index of the first inexact
addition".

WHAT IT IS NOT, IN THE ROW'S OWN SENTENCE: "THERE ARE NO MEASURED DEFECTS TO
REPORT AND NONE IS REPORTED: every entry of this record is an OUTCOME, not a
number." Nothing here carries a residual, a norm, a distance or a window. A
:class:`PredicateOutcome` carries a BOOLEAN and, where the predicate was
decided over an enumeration, the INDEX at which it first failed -- an index
into a declared order, not a magnitude. This module computes no predicate of
its own: every outcome it carries was decided by the decider that returned it,
and the transcript is the record of that decision and never a second one.

WHY A FIELD ON THE RETURNED RECORD AND NOT A RECORDER PASSED DOWN
=================================================================
The choice is recorded where it takes effect
(``harness/README.md``'s rule, and PRINCIPLES.md section 3 on deviations):

1. A recorder threaded down is a MUTABLE ACCUMULATOR inside modules this
   repository has accepted as pure functions over serialisable artefacts
   (PRINCIPLES.md section 9). The run tier's own rule -- "no logging call
   enters an accepted module" (:mod:`certiqs_key.runs.flow`) -- is the same judgement
   one tier up, and a recorder is a logging channel under another name.
2. A recorder is OPTIONAL BY CONSTRUCTION, so a path that forgot to pass one
   would record nothing and say nothing about it. A field cannot be forgotten:
   an unfilled transcript is a visible empty tuple, and a test can demand
   otherwise.
3. The blast radius is the same either way -- both need a recording expression
   at every decision site -- but a defaulted field on a frozen record forces NO
   caller to change, while a new parameter changes every decider's signature.

THE RECURRING COST, stated plainly: a NEW predicate must be RECORDED as
well as decided, and every decider that returns early on a failure must
accumulate what it decided before it returns.
``tests/unit/test_protocol_compiler_transcript.py`` is what makes forgetting
that a red.

THE KEY IS (source, element, block) AND IT IS NOT UNIQUE
=======================================================
The row fixes the key and not a container. Several predicates are decided on
ONE element -- (H) and (P) on the same ``M_x``; the four components of one
sector-map comparison -- so :meth:`PredicateTranscript.lookup` returns a
TUPLE, and ``predicate`` is what tells the members apart. A lookup that
returned one outcome would have to choose between two decisions the compiler
took, which is the kind of collapse the ``gate_report`` row exists to prevent.

THE ELEMENT SPELLINGS ARE THIS BATCH'S; THE ROW FIXES NONE
==========================================================
The row says the element is "the label ``x``, the outcome ``v``, the entry id,
the link index, the family name, ``tau_A``" and fixes no spelling. One spelling
is used per OBJECT, so that a consumer joining two sources on one object finds
the same string:

* ``tau_A``, ``Psi`` -- the declared marginal and the certificate operator;
* ``M_<x>`` -- Alice's POVM element at the signal label ``x``;
* ``F_<v>`` -- the emitted receiver family member at the outcome label ``v``;
* ``O^_<k>`` -- the operator of the ``k``-th constraint entry, ``k`` 1-based as
  the claims number it;
* ``CList[<k>]`` -- the ``k``-th constraint ENTRY as a whole, which is the
  object V6's type decisions are about (its operator is ``O^_<k>``: two
  objects, two names);
* ``{M_x}``, ``{F_v}`` -- a WHOLE FAMILY, where the decision is about the
  family and not about one member: (C) and (S) of ``def:exact`` are the
  completeness sum, which no single element has;
* ``{q_t}`` -- the declared weights of a choice-weighted presentation as a
  whole, for the same reason, and ``P( . | <t>)`` -- one ROW of a declared
  ``choice_weighting``, the object whose sum is decided;
* ``p_<x>``, ``rho^v_<x>`` -- the virtual ensemble's weight and state at the
  signal label ``x``, the objects (S2) and (S3) compare across a source link;
* ``x = <label>`` -- a signal label as the object of a TYPE decision, where
  ``M_<x>`` would name a matrix the decision is not about;
* ``(<u>,<t>)``, ``<t>|<f>`` -- an emitted joint outcome of the first form and
  a setting-choice pair of the second, which is what the representability
  decision is taken on;
* ``idxm|_S`` -- the sector-order clause of D(i);
* ``omega* (default candidate)`` / ``omega* (supplied witness)`` -- WHICH
  candidate check V7 verified, the row's "the candidate it verified";
* a link's ``link_id``, or ``<earlier> -> <later>`` for a decision on an
  adjacent PAIR of links;
* for the compilation map, the declaring party's label and a colon before the
  rest -- ``A:(Z,0)``, ``B:T_pub`` -- because two presentations of one
  specification may carry THE SAME joint label and the two decisions are then
  distinct decisions on distinct data;
* in the general format, where the specification presents MORE THAN ONE
  measured factor, the factor's label and a colon before the rest of every
  element decided on that factor's own data -- ``b:B:{q_t}``, ``b:B:<letter>``,
  ``b:P( . | <t>)``, ``b:F_<v>``, ``b:F^B_<v>``, ``b:{F^B_v}``,
  ``b:B:{N_(u|t)}`` -- because a party may hold two factors (``def:spec``
  (b'), (c')), so two factors' decisions on the same letter would otherwise
  share a key. :func:`scoped_to_factor` writes the prefix for the deciders
  that do not take a factor argument. At one measured factor no prefix is
  written, so the accepted format's keys are unchanged. The one exception is
  the physical family's own decision, ``<factor>:{F^ph_w}``, which carries its
  factor at every factor count.

The ``block`` component is the sector label or the photon block, and is
``None`` for a decision that is not per block -- on ``A``, which carries no
sector decomposition, and for every combinatorial or type decision.

THE INDEX CONVENTIONS ARE TWO, AND THAT IS FORCED RATHER THAN CHOSEN
====================================================================
The row asks a failed predicate for "the block, outcome, signal or entry index
at which it FIRST failed". Two conventions meet in this record and neither is
this module's to change, both being a datum a domain record computed:

* 1-BASED in the declared order, for every summation index --
  :attr:`~certiqs_key.foundations.exact.SummationVerdict.first_inexact_index` and
  :attr:`~certiqs_key.foundations.exact.TraceVerdict.first_inexact_row` are
  documented so -- and for every index THIS package computes itself: the
  signal index of an ``x``, the outcome index of a ``v``, the entry index of a
  ``CList`` entry (which is the ``k`` of ``O^_k``, 1-based in the claims too)
  and the link index of a chain link;
* 0-BASED, for the position inside a sector-map comparison, which is
  :attr:`~certiqs_key.foundations.blocks.SectorMapDisagreement.position` carried
  through unchanged. Normalising it would put a DIFFERENT number in the
  transcript from the one the refusal detail names for the same disagreement,
  which is worse than carrying the decider's own. THE SAME 0-BASED POSITION IS
  CARRIED BY THE ORDER CLAUSE ``idxm|_S``, which this package does compute
  itself (:func:`~certiqs_key.protocol_compiler.validation.check_v1`'s
  comparison of ``idxm``'s sector order against ``Smap``'s) and which is
  therefore the one index of this record that the first bullet's rule would
  get wrong: it is 0-based BECAUSE the refusal detail beside it is, and the
  two must name the same sector. It is
  unreachable through :func:`compile_specification`, whose ``idx`` always
  agrees, and reachable through ``check_v1`` on a hand-built candidate --
  which is the object D(i) is stated on.

One further index is neither: the representability decision of
``def:weighted`` carries the FLAT ENTRY INDEX inside the emitted matrix, which
is the number its refusal reason names ("flat entry <n>") and the only index
that locates the entry at all.

Both choice-weighting forms require declared binary64 weights before their
summation predicates are evaluated. Hence the first addition from zero is
exact for those weight sums. The historical off-lattice first-form exception
was removed with the first-form weight-lattice amendment; ordinary numeric
input is prepared and recorded at the declaring boundary instead.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Final

from certiqs_key.foundations.blocks import (
    SECTOR_MAP_COMPONENTS,
    SectorMapDisagreement,
)
from certiqs_key.foundations.errors import MalformedInputError

__all__ = [
    "EMPTY_TRANSCRIPT",
    "SUMMATION_PREDICATE",
    "PredicateOutcome",
    "PredicateSource",
    "PredicateTranscript",
    "scoped_to_factor",
    "sector_map_predicates",
]


class PredicateSource(StrEnum):
    """WHAT DECIDED IT. A CLOSED SET, fixed by the ``gate_report`` row.

    The row: the source is "the check, the gate, the interface condition OR THE
    COMPILATION MAP that decided it, the last being where a decision taken in
    FILLING ``eq:declaration`` rather than in checking it is recorded". So:
    the eight checks of Definition ``def:validator``; the four gate entries of
    Definition ``def:eligible`` with (G3) split as :class:`
    ~certiqs_key.protocol_compiler.gates.GateId` splits it; the ten interface
    conditions of Definition ``def:chaincond`` and the two checkable conditions
    of the source-replacement certificate; and the compilation map itself.

    IT IS A CLOSED ENUM AND NOT A FREE STRING because the row fixes the
    vocabulary: a source outside this list would be a decision taken by
    something Definition ``def:compile`` does not name. Members that no
    decision keys today are still members -- (G1), whose content is V1-V8;
    (G3)(a) and (G3)(b), which the enumeration does not list; (C2), (C3), (C5)
    and (S4), whose decisions the ``recorded_predicates`` scope note excludes
    or does not name -- because the vocabulary is the row's and not an
    inventory of this module.
    """

    V1 = "V1"
    V2 = "V2"
    V3 = "V3"
    V4 = "V4"
    V5 = "V5"
    V6 = "V6"
    V7 = "V7"
    V8 = "V8"
    G1 = "G1"
    G2 = "G2"
    G3A = "G3a"
    G3B = "G3b"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    C4 = "C4"
    C5 = "C5"
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"
    SR1 = "SR1"
    SR2 = "SR2"
    COMPILATION_MAP = "compilation_map"


#: THE ONE SPELLING OF CONDITION (S), used wherever a declared-order sum or an
#: accumulated trace is decided to round nowhere -- Definition ``def:exact``
#: (S), the trace of ``tau_A``, the trace of ``Psi``, the weight sum
#: ``sum_t q_t`` and each row sum of ``P``. It is a constant rather than a
#: string repeated at each of those sites because
#: :meth:`PredicateOutcome.__post_init__` READS it: ``first_inexact_index``
#: belongs to (S) and to no other predicate, and a second spelling would make
#: that invariant silently unenforceable.
SUMMATION_PREDICATE: Final[str] = "(S)"


@dataclass(frozen=True)
class PredicateOutcome:
    """One decision the compiler took, and the outcome it reached.

    ``outcome`` IS A BOOLEAN AND NOT A VERDICT TOKEN. The three-valued gate
    vocabulary -- passed, failed, PASSED VACUOUSLY -- belongs to
    :attr:`~certiqs_key.protocol_compiler.gates.GateEntry.verdict` and must not
    leak here: Remark ``rem:degenerate`` forbids reporting a vacuous pass "as
    evidence of anything", and a transcript entry is a decision that WAS taken
    on data. Where a condition was NOT decided -- (C4) at a link that supplies
    no channel, check V7's branch (c) where no witness was supplied -- there is
    NO ENTRY, and the absence is the record: ``not checked`` is the verdict of
    the condition and lives on the chain report beside Assumption ``ass:link``,
    never as a third value of a per-predicate outcome.
    """

    source: PredicateSource
    #: WHICH predicate: ``(H)``, ``(P)``, ``(C)``, :data:`SUMMATION_PREDICATE`,
    #: ``(T)``, a type decision, one of the four sector-map components, or the
    #: identity a condition of Definition ``def:chaincond`` states.
    predicate: str
    #: The element it was decided on, in the spelling the module docstring
    #: lists. ``None`` only where the decision is not per element -- the
    #: completeness sum of a family, the weight sum of a presentation.
    element: str | None
    #: The sector block or photon block. ``None`` where the decision is not per
    #: block: on ``A``, which carries no sector decomposition, and for every
    #: combinatorial, presence or type decision.
    block: str | None
    outcome: bool
    #: The row: "A FAILED predicate is recorded with the block, outcome, signal
    #: or entry index at which it FIRST failed." Present exactly where the
    #: failing predicate was decided over an ENUMERATION the row names, and
    #: ``None`` on a pass.
    #:
    #: The row asks for an index "present exactly on a
    #: failure" (a deviation recorded under PRINCIPLES.md section 3). Some failures
    #: carry no index at all: ``tau_A`` is not Hermitian, a declared alphabet is empty,
    #: a descriptor does not match -- one element, one decision, nothing enumerated.
    #: Writing ``0`` there would put a false datum on the wire in a record whose own row
    #: says every entry is an outcome and not a number. So the enforced invariant is the
    #: direction that is always true: AN INDEX IMPLIES A FAILURE, and a pass
    #: carries none.
    first_failure_index: int | None = None
    #: The row: "and (S) additionally with the index of the first inexact
    #: addition". Present only on a FAILING (S) decision, where it is the
    #: index of that addition in the declared order. It coincides with
    #: :attr:`first_failure_index` by construction -- for (S) the addition at
    #: which the predicate first failed IS the first inexact addition -- and
    #: both are carried because the row names both and a consumer reading
    #: either key must find it.
    first_inexact_index: int | None = None

    def __post_init__(self) -> None:
        """Keep the two indices and the outcome in step.

        Written the way :meth:`
        ~certiqs_key.protocol_compiler.gates.GateEntry.__post_init__` keeps the
        degeneration record and the third token in step: a record that could
        carry an index beside a passing outcome would let a reader take the
        index for something other than a first failure.
        """
        if self.outcome and self.first_failure_index is not None:
            raise MalformedInputError(
                "a PASSING predicate carries no first-failure index: the index "
                "is the one at which the predicate FIRST FAILED (the "
                "``gate_report`` output row)"
            )
        if self.outcome and self.first_inexact_index is not None:
            raise MalformedInputError(
                "a sum that rounds nowhere has no first inexact addition; "
                "condition (S) holds of it (Definition def:exact)"
            )
        if self.first_inexact_index is not None:
            if self.predicate != SUMMATION_PREDICATE:
                raise MalformedInputError(
                    "the index of the first inexact addition belongs to "
                    f"condition {SUMMATION_PREDICATE} and to no other "
                    f"predicate; this one is {self.predicate!r}"
                )
            if self.first_failure_index != self.first_inexact_index:
                raise MalformedInputError(
                    "for condition (S) the addition at which the predicate "
                    "first failed IS the first inexact addition, so the two "
                    "indices are one number recorded under both names"
                )
        if (
            not self.outcome
            and self.predicate == SUMMATION_PREDICATE
            and self.first_inexact_index is None
        ):
            raise MalformedInputError(
                "a failing (S) decision names the index of the first inexact "
                "addition; every decider of this repository computes it "
                "(foundations.exact.SummationVerdict, TraceVerdict)"
            )

    @property
    def key(self) -> tuple[PredicateSource, str | None, str | None]:
        """Return ``(source, element, block)`` -- THE KEY THE ROW FIXES."""
        return (self.source, self.element, self.block)

    def as_record(self) -> dict[str, object]:
        """Return the outcome as a machine record."""
        return {
            "source": str(self.source),
            "predicate": self.predicate,
            "element": self.element,
            "block": self.block,
            "outcome": self.outcome,
            "first_failure_index": self.first_failure_index,
            "first_inexact_index": self.first_inexact_index,
        }


@dataclass(frozen=True)
class PredicateTranscript:
    """Every decision one compilation took, IN THE ORDER IT TOOK THEM.

    THE ORDER IS THE DECISION ORDER of
    :func:`~certiqs_key.protocol_compiler.compile.compile_specification` and is
    part of the record: the receiver's choice-weighted family is constructed
    before the chain is read, the chain before Alice's family, the certificate
    before route C, and the validator last -- so a reader can see not only what
    was decided but what had already been decided when it was.

    AN EMPTY TRANSCRIPT IS A TRANSCRIPT. :class:`
    ~certiqs_key.protocol_compiler.gates.GateReport` defaults to one, so a
    report assembled by hand -- in a test, or by
    :func:`~certiqs_key.protocol_compiler.gates.resolve_gates` called without
    one -- says "nothing was recorded" rather than carrying a field that might
    or might not be there.
    """

    outcomes: tuple[PredicateOutcome, ...] = ()

    def __len__(self) -> int:
        """Return how many decisions are recorded."""
        return len(self.outcomes)

    def lookup(
        self,
        source: PredicateSource,
        element: str | None = None,
        block: str | None = None,
    ) -> tuple[PredicateOutcome, ...]:
        """Return every outcome keyed by ``(source, element, block)``.

        A TUPLE BECAUSE THE KEY IS NOT UNIQUE -- see the module docstring. The
        default arguments are the keys of a decision that is not per element or
        not per block, which is what ``None`` means in both fields; they are not
        wildcards, and a lookup with ``element=None`` does not return the
        per-element decisions.
        """
        return tuple(
            outcome
            for outcome in self.outcomes
            if outcome.key == (source, element, block)
        )

    def keys(self) -> tuple[tuple[PredicateSource, str | None, str | None], ...]:
        """Return the distinct keys, in the order they were first decided."""
        seen: list[tuple[PredicateSource, str | None, str | None]] = []
        for outcome in self.outcomes:
            if outcome.key not in seen:
                seen.append(outcome.key)
        return tuple(seen)

    def for_source(self, source: PredicateSource) -> tuple[PredicateOutcome, ...]:
        """Return every outcome one source decided, in the decision order."""
        return tuple(
            outcome for outcome in self.outcomes if outcome.source is source
        )

    @property
    def sources(self) -> tuple[PredicateSource, ...]:
        """Return the sources that decided something, in the decision order."""
        seen: list[PredicateSource] = []
        for outcome in self.outcomes:
            if outcome.source not in seen:
                seen.append(outcome.source)
        return tuple(seen)

    @property
    def negative_outcomes(self) -> tuple[PredicateOutcome, ...]:
        """Return the outcomes that came out FALSE, in the decision order.

        NOT NAMED ``failures``, and the difference is the record's own: a
        negative outcome is a VIOLATION for a predicate stated as a
        requirement -- (H), (C), an identity -- and a CLASSIFICATION ANSWER for
        one stated as a membership: the support decision of Eq. ``eq:support``
        reads ``False`` for a pair off the support, which "is not an outcome,
        is not emitted and indexes nothing" and is no defect at all. The two
        are told apart by the predicate, and a violation additionally carries
        an index wherever the decision ranged over an enumeration.
        """
        return tuple(outcome for outcome in self.outcomes if not outcome.outcome)

    def as_record(self) -> list[dict[str, object]]:
        """Return the transcript as a machine record, in the decision order."""
        return [outcome.as_record() for outcome in self.outcomes]


#: THE ONE EMPTY TRANSCRIPT, shared. It is the default of
#: :attr:`~certiqs_key.protocol_compiler.gates.GateReport.transcript` and the
#: value :func:`~certiqs_key.protocol_compiler.gates.resolve_gates` uses when a
#: caller passes none; a frozen record with no mutable field can be shared, and
#: a constant is also what keeps the dataclass default a value rather than a
#: call (ruff RUF009).
EMPTY_TRANSCRIPT: Final[PredicateTranscript] = PredicateTranscript()


def scoped_to_factor(
    predicates: Iterable[PredicateOutcome], factor: str
) -> tuple[PredicateOutcome, ...]:
    """Return ``predicates`` with each element keyed to one measured factor.

    The module docstring's factor rule: in the general format with more than
    one measured factor, a decision on one factor's own data carries the
    factor's label and a colon before its element, because two factors may
    carry the same party label (``def:spec`` (b'), (c')) and their decisions
    would otherwise share a ``(source, element, block)`` key. A decision with
    no element is keyed by the factor label alone. The caller decides whether
    more than one factor is presented; this function records nothing new and
    changes no outcome or index.
    """
    return tuple(
        replace(
            outcome,
            element=(
                factor if outcome.element is None else f"{factor}:{outcome.element}"
            ),
        )
        for outcome in predicates
    )


def sector_map_predicates(
    source: PredicateSource,
    element: str,
    disagreement: SectorMapDisagreement | None,
) -> tuple[PredicateOutcome, ...]:
    """Return one outcome PER COMPONENT of a four-component map comparison.

    THREE SOURCES MAKE THE SAME COMPARISON and the row asks all three for the
    same four components, so the recording is written once here rather than
    three times: check V1 on "each DECLARED Q-OPERATOR family ... per component
    (block kind, identifiers, order, dimensions)"; check V7 on the map a
    supplied witness carries, "condition (T) of Definition ``def:exact``,
    decided in the same four components"; and (C1)'s last clause, "the
    four-component comparison of ``Lambda_L``'s target descriptor against
    ``(Q, Smap)``".
    :data:`~certiqs_key.foundations.blocks.SECTOR_MAP_COMPONENTS` is the vocabulary
    and :meth:`~certiqs_key.foundations.blocks.SectorStructure.disagreement` decides
    the components in that order, reporting the FIRST that disagrees.

    SO THE RECORD STOPS WHERE THE COMPARISON STOPPED, and the three shapes are
    exactly the three the comparison has:

    * it agrees: all four components were decided and hold;
    * the identifier lists differ IN MEMBERSHIP: the kind held, the identifiers
      did not, and NO ORDER QUESTION WAS DECIDED -- lists with different
      members have no order to compare;
    * the identifier lists are a PERMUTATION of one another: the kind and the
      identifiers held and the order did not.

    An implementation that filled the components it never reached would be
    reporting decisions the comparison did not take.
    """
    if disagreement is None:
        return tuple(
            PredicateOutcome(
                source=source,
                predicate=component,
                element=element,
                block=None,
                outcome=True,
            )
            for component in SECTOR_MAP_COMPONENTS
        )
    reached = SECTOR_MAP_COMPONENTS[
        : SECTOR_MAP_COMPONENTS.index(disagreement.component) + 1
    ]
    if disagreement.component == "identifier":
        # The lists differ in membership: "order" is not among the components
        # decided, although it precedes "dimension" in the vocabulary.
        reached = ("block_kind", "identifier")
    return tuple(
        PredicateOutcome(
            source=source,
            predicate=component,
            element=element,
            block=None,
            outcome=component != disagreement.component,
            first_failure_index=(
                disagreement.position
                if component == disagreement.component
                else None
            ),
        )
        for component in reached
    )
