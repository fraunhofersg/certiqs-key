"""The ``gate_report`` row's per-predicate transcript: keying, invariants, completeness.

WHAT THIS FILE HOLDS FIXED, AND WHY EACH PART IS HERE
=====================================================
``spec/modules/protocol-compiler/interface.yaml``'s ``outputs.gate_report``
asks for the outcome of every predicate the compiler decided, "KEYED BY
(source, element, block)", with the first-failure index of a failed one and,
for (S), the index of the first inexact addition. Four groups of test:

1. THE RECORD'S OWN INVARIANTS. An index belongs to a FAILURE, the index of a
   first inexact addition belongs to condition (S), and the machine record has
   the seven keys it has. These are the properties that make a reader able to
   trust what an entry means.
2. THE COMPLETENESS TEST, which is the one that matters. It reads the eight
   items of ``recorded_predicates.the_enumeration`` out of ``interface.yaml``
   and holds the transcript of a compiled BB84 declaration against a
   HAND-WRITTEN key set derived from the row and from the declaration --
   never from the transcript the code produced, which would assert nothing. It
   also asserts, per enumeration item, that the sources that item names are
   present where BB84 exercises them and ABSENT WITH A REASON where it does
   not: an item whose elements BB84 has none of (V6 at ``m = 0``), the
   transmitter-owned virtual-ensemble conditions excluded from this module's
   inventory, and (C3)'s unkeyed legs are each named at their assertion.
   THE CONDITIONAL FAMILIES'
   ADMISSIBILITY IS DECIDED AND KEYED, and is in the hand-written key set.
3. THE NEGATIVE CASES, one per decider: a failed predicate of validation, of
   the chain, of the certificate and of the compilation map, each asserting
   the index the row asks for. They are taken at the DECIDER and not through
   :func:`compile_specification` for two of the four, and the reason is the
   fail-closed shape rather than convenience: a chain refusal and an emission
   refusal are taken BEFORE the gates run, so no ``gate_report`` exists on
   those paths at all -- the record they would be recorded on is never built.
   What a consumer sees of a refusal is ``refusal``; what the transcript is
   for is the compilation that PASSED, which is the reason the transcript exists.
4. THE SHAPE OF AN ABSENT TRANSCRIPT. A report built without one says
   "nothing was recorded" out loud, which is the property a defaulted field has
   and a recorder threaded down does not.

NO REGISTRY IMPORT. These are properties of the record and of the mapping from
the row to the code; the frozen registries pin the four gate verdicts and the
numbers, and this file asserts nothing either owns.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path

import pytest
import yaml
from instances.bb84.specification import bb84_specification
from protocol_blocks import as_blocks

from certiqs_key.domain.chain import (
    ChainLink,
    LinkStage,
    LinkStatus,
    ReductionChain,
    Side,
    SystemDescriptor,
)
from certiqs_key.domain.constraints import ConstraintEntry, Relation, RhsTag
from certiqs_key.foundations.blocks import (
    BlockKind,
    BlockOperator,
    JointBlockOperator,
    SectorStructure,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import matrix
from certiqs_key.protocol_compiler import (
    DEFAULT_CANDIDATE,
    EMPTY_TRANSCRIPT,
    SUMMATION_PREDICATE,
    SUPPLIED_WITNESS,
    CertificateState,
    ChainContext,
    GateInputs,
    PredicateOutcome,
    PredicateSource,
    PredicateTranscript,
    Refusal,
    RefusalReason,
    SettingWeightedFamily,
    SourceMode,
    check_chain,
    check_v1,
    check_v3,
    check_v6,
    check_v7,
    compile_specification,
    decide_emission,
    default_witness,
    identity_channel,
    resolve_gates,
    sector_map_predicates,
    setting_weighted_family,
    weighted_family,
)
from certiqs_key.protocol_compiler.compile import _certificate_predicates
from certiqs_key.protocol_compiler.spec import (
    Party,
    PublicChoices,
    SpecConstraints,
)
from certiqs_key.protocol_compiler.weights import (
    ChoiceWeighting,
    _decide_stochastic,
)
from certiqs_key.transmitter.certificate import (
    SourceReplacementCertificate,
    verify_certificate,
)

pytestmark = pytest.mark.contract

ROOT = Path(__file__).resolve().parents[2]
INTERFACE = ROOT / "spec" / "modules" / "protocol-compiler" / "interface.yaml"

HALF = F(1, 2)
QUBIT = SectorStructure(labels=("s0",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR)
P_Z0 = matrix(((1, 0), (0, 0)))
P_Z1 = matrix(((0, 0), (0, 1)))

#: A four-element family on ``A`` that satisfies (H), (P) and (C) and FAILS
#: (S) at its second addition. ``1 - 2^-53`` and ``2^-54`` are both binary64
#: numbers, their exact total is one, and the intermediate
#: ``1 - 2^-53 + 2^-54 = 1 - 2^-54`` is not on the lattice -- which is
#: Definition ``def:exact``'s own point: "(S) is on the ADDITIONS, not on the
#: operands, so a family every one of whose entries is a binary64 number may
#: still be refused".
_BIG = F(1) - F(1, 2**53)
_SMALL = F(1, 2**54)
ROUNDING_FAMILY = (
    matrix(((_BIG, 0), (0, F(1, 4)))),
    matrix(((_SMALL, 0), (0, F(1, 4)))),
    matrix(((_SMALL, 0), (0, F(1, 4)))),
    matrix(((0, 0), (0, F(1, 4)))),
)


def _bb84_transcript() -> PredicateTranscript:
    """Return the transcript of the compiled BB84 declaration."""
    result = compile_specification(bb84_specification(HALF, HALF, HALF, HALF))
    assert result.gate_report is not None
    return result.gate_report.transcript


def _bb84_declaration():  # noqa: ANN202 - the module's own record type
    """Return the emitted BB84 declaration, for the per-check negative cases."""
    result = compile_specification(bb84_specification(HALF, HALF, HALF, HALF))
    assert result.declaration is not None
    return result.declaration


def _interface_row() -> dict[str, object]:
    """Return the ``outputs`` row named ``gate_report``, which is BINDING."""
    interface = yaml.safe_load(INTERFACE.read_text(encoding="utf-8"))
    return next(
        entry for entry in interface["outputs"] if entry["name"] == "gate_report"
    )


def _enumeration() -> list[str]:
    """Return ``outputs.gate_report.recorded_predicates.the_enumeration``."""
    row = _interface_row()
    recorded = row["recorded_predicates"]
    assert isinstance(recorded, dict)
    return list(recorded["the_enumeration"])


# ---------------------------------------------------------------------------
#  1. The record's own invariants
# ---------------------------------------------------------------------------


def test_an_outcome_is_keyed_by_source_element_and_block() -> None:
    """The key is the row's three components and nothing else."""
    outcome = PredicateOutcome(
        source=PredicateSource.V3,
        predicate="(H)",
        element="F_v0",
        block="s0",
        outcome=True,
    )
    assert outcome.key == (PredicateSource.V3, "F_v0", "s0")


def test_the_lookup_returns_every_predicate_decided_on_one_element() -> None:
    """THE KEY IS NOT UNIQUE, and the lookup must not choose between two decisions.

    (H) and (P) are decided on the same ``M_x`` and share a key; a lookup that
    returned one of them would drop a decision the compiler took.
    """
    transcript = _bb84_transcript()
    found = transcript.lookup(PredicateSource.V3, "M_(Z,0)")
    assert tuple(entry.predicate for entry in found) == ("(H)", "(P)")
    # ``None`` is a key VALUE and not a wildcard: the per-element decisions are
    # not returned by a lookup that asks for the family-level ones.
    assert transcript.lookup(PredicateSource.V3, "{M_x}") != found
    assert transcript.lookup(PredicateSource.V3, "nothing decided this") == ()


def test_a_passing_predicate_carries_neither_index() -> None:
    """An index means "this is where it FIRST FAILED", so a pass carries none."""
    with pytest.raises(MalformedInputError, match="PASSING predicate"):
        PredicateOutcome(
            source=PredicateSource.V3,
            predicate="(C)",
            element="{M_x}",
            block=None,
            outcome=True,
            first_failure_index=2,
        )
    with pytest.raises(MalformedInputError, match="rounds nowhere"):
        PredicateOutcome(
            source=PredicateSource.V3,
            predicate=SUMMATION_PREDICATE,
            element="{M_x}",
            block=None,
            outcome=True,
            first_inexact_index=2,
        )


def test_the_index_of_a_first_inexact_addition_belongs_to_condition_s() -> None:
    """And a failing (S) decision must carry it, every decider computing one."""
    with pytest.raises(MalformedInputError, match="condition"):
        PredicateOutcome(
            source=PredicateSource.V2,
            predicate="(C)",
            element="tau_A",
            block=None,
            outcome=False,
            first_failure_index=2,
            first_inexact_index=2,
        )
    with pytest.raises(MalformedInputError, match="one number"):
        PredicateOutcome(
            source=PredicateSource.V2,
            predicate=SUMMATION_PREDICATE,
            element="tau_A",
            block=None,
            outcome=False,
            first_failure_index=1,
            first_inexact_index=2,
        )
    with pytest.raises(MalformedInputError, match="first inexact addition"):
        PredicateOutcome(
            source=PredicateSource.V2,
            predicate=SUMMATION_PREDICATE,
            element="tau_A",
            block=None,
            outcome=False,
        )


def test_the_machine_record_of_an_outcome_has_the_seven_keys_it_has() -> None:
    """The wire form, spelled out rather than derived from the field list."""
    outcome = PredicateOutcome(
        source=PredicateSource.V2,
        predicate=SUMMATION_PREDICATE,
        element="tau_A",
        block=None,
        outcome=False,
        first_failure_index=2,
        first_inexact_index=2,
    )
    assert outcome.as_record() == {
        "source": "V2",
        "predicate": "(S)",
        "element": "tau_A",
        "block": None,
        "outcome": False,
        "first_failure_index": 2,
        "first_inexact_index": 2,
    }
    assert PredicateTranscript((outcome,)).as_record() == [outcome.as_record()]


def test_the_sector_map_comparison_records_one_outcome_per_component() -> None:
    """Four components, and the record stops where the comparison stopped."""
    emitted = SectorStructure(
        labels=("s0", "s1"), dims=(2, 3), block_kind=BlockKind.PROOF_SECTOR
    )
    agreeing = sector_map_predicates(PredicateSource.V1, "F_v0", None)
    assert tuple(entry.predicate for entry in agreeing) == (
        "block_kind",
        "identifier",
        "order",
        "dimension",
    )
    assert all(entry.outcome for entry in agreeing)

    permuted = SectorStructure(
        labels=("s1", "s0"), dims=(3, 2), block_kind=BlockKind.PROOF_SECTOR
    )
    order = sector_map_predicates(
        PredicateSource.V1, "F_v0", emitted.disagreement(permuted)
    )
    assert tuple((e.predicate, e.outcome) for e in order) == (
        ("block_kind", True),
        ("identifier", True),
        ("order", False),
    )
    # 0-BASED, because it is SectorMapDisagreement.position carried through:
    # the transcript and the refusal detail name the same number.
    assert order[-1].first_failure_index == 0

    renamed = SectorStructure(
        labels=("s0", "s2"), dims=(2, 3), block_kind=BlockKind.PROOF_SECTOR
    )
    identifiers = sector_map_predicates(
        PredicateSource.V1, "F_v0", emitted.disagreement(renamed)
    )
    # NO ORDER QUESTION WAS DECIDED: lists with different members have no
    # order to compare, so the record carries two components and not three.
    assert tuple((e.predicate, e.outcome) for e in identifiers) == (
        ("block_kind", True),
        ("identifier", False),
    )
    assert identifiers[-1].first_failure_index == 1

    kinds = sector_map_predicates(
        PredicateSource.V1,
        "F_v0",
        emitted.disagreement(
            SectorStructure(
                labels=("s0", "s1"), dims=(2, 3), block_kind=BlockKind.NUMERICAL_BLOCK
            )
        ),
    )
    assert tuple((e.predicate, e.outcome) for e in kinds) == (("block_kind", False),)
    # The block kind is not a position in a list, so no index is invented.
    assert kinds[-1].first_failure_index is None


# ---------------------------------------------------------------------------
#  2. THE COMPLETENESS TEST
# ---------------------------------------------------------------------------

#: THE KEY SET THE ROW AND THE BB84 DECLARATION TOGETHER FIX, hand-written.
#: The declaration is ``instances/bb84``'s: ``|X| = |V| = 4`` with the labels
#: below, ONE sector ``s0`` of dimension 2, ``d_A = 2``, trusted source mode
#: with a certificate, ``CList`` EMPTY, no supplied feasibility witness, no
#: ``choice_weighting``, and BOTH the Alice family and the receiver's
#: physical family presented as choice-weighted families over ``T_pub`` of
#: size two. Each group below is the row's enumeration item read against
#: those facts; the comment says which item and how the count follows.
_LABELS = ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")

EXPECTED_KEYS: frozenset[tuple[PredicateSource, str | None, str | None]] = frozenset(
    [
        # Item 8, the compilation map, TWICE: one choice-weighted presentation
        # per party, and the party prefix is what keeps their identical joint
        # labels apart. Per presentation: the CONDITIONAL FAMILIES -- one (T)
        # decision for the presentation and (H), (P), (C), (S) per choice value
        # -- then the weight family (sum_t q_t = 1 and its (S) leg) and the
        # representability of each of the four emitted elements.
        #
        # THE CONDITIONAL-FAMILY KEYS: the row asks for them "KEYED PER (SOURCE, PARTY,
        # CHOICE VALUE t, BLOCK)", and BB84 declares T_pub = {Z, X} on both sides. The
        # BLOCK IS ``None`` because a `public_choices` record declares one undecomposed
        # array per outcome and no sector map, so there is no block identifier on the
        # wire to key by (def:weighted; decide_conditional_families).
        *(
            (PredicateSource.COMPILATION_MAP, f"{party}:{name}", None)
            for party in ("A", "B")
            for name in (
                "{N_(u|t)}",
                "{N_(u|Z)}",
                "{N_(u|X)}",
                "{q_t}",
                *_LABELS,
            )
        ),
        # Item 8 again: req:physical-family-decision on the receiver's
        # physical family as presented, keyed by its measured factor (``f0``,
        # the default label of the one factor). That family is a decided clause
        # of def:well-formed-spec (iv): BB84's receiver is
        # choice-weighted, so the one condition decided of the family itself
        # is (S) on its own declared-order sum.
        (PredicateSource.COMPILATION_MAP, "f0:{F^ph_w}", None),
        # Item 7, (C1) on the chain: Band A is ONE receiver link, so there is
        # no adjacent pair, and every clause is decided on that link.
        (PredicateSource.C1, "Lambda_1", None),
        # Item 7, (C4): the pullback identity per EMITTED OUTCOME.
        *((PredicateSource.C4, f"F_{label}", None) for label in _LABELS),
        # Item 6: the three conditions on Psi with the (S) leg of its trace,
        # under the gate that decides them; (SR1) on the marginal; (SR2) per
        # SIGNAL LABEL.
        (PredicateSource.G2, "Psi", None),
        (PredicateSource.SR1, "tau_A", None),
        *((PredicateSource.SR2, f"x = {label}", None) for label in _LABELS),
        # Item 4, V1: the sector-order clause of D(i), and the four-component
        # comparison per DECLARED Q-OPERATOR family -- the four emitted Bob
        # families, and no constraint operator, CList being empty.
        (PredicateSource.V1, "idxm|_S", None),
        *((PredicateSource.V1, f"F_{label}", None) for label in _LABELS),
        # Item 1, V2 on tau_A: (H), (P), (C) and (S), all four on one element.
        (PredicateSource.V2, "tau_A", None),
        # Item 1, V3: (H) and (P) per M_x on A, which carries no block; (H)
        # and (P) per Bob family member PER BLOCK; and (C) with (S) on each
        # family, keyed by the family and, for the Bob family, by the block.
        *((PredicateSource.V3, f"M_{label}", None) for label in _LABELS),
        *((PredicateSource.V3, f"F_{label}", "s0") for label in _LABELS),
        (PredicateSource.V3, "{M_x}", None),
        (PredicateSource.V3, "{F_v}", "s0"),
        # Item 2, V7, on the candidate it verified -- the default one, CList
        # being empty: (H) and (P) PER BLOCK on the one sector, the trace leg,
        # and, in trusted mode, the marginal. No per-entry leg: CList is empty.
        (PredicateSource.V7, "omega* (default candidate)", "s0"),
        (PredicateSource.V7, "omega* (default candidate)", None),
        (PredicateSource.V7, "tau_A", None),
    ]
)

#: How many OUTCOMES each source records on that declaration, which the key
#: set alone does not fix: V2 decides four predicates on one element, V1 four
#: components per family, (C1) eight clauses on one link.
EXPECTED_COUNTS: dict[PredicateSource, int] = {
    # Per party: 1 (T) + 4 legs on each of the two conditional families, then
    # 2 on {q_t} and 4 emitted elements, nine outcomes per party for the
    # conditional-family decision, plus one (S) on the receiver's
    # choice-weighted physical family (req:physical-family-decision).
    PredicateSource.COMPILATION_MAP: 31,
    PredicateSource.C1: 8,  # 4 descriptor clauses + 4 map components
    PredicateSource.C4: 4,  # one identity per emitted outcome
    PredicateSource.G2: 4,  # (H), idempotence, tr = 1, (S)
    PredicateSource.SR1: 1,
    PredicateSource.SR2: 4,  # one per signal
    PredicateSource.V1: 17,  # 1 order clause + 4 families x 4 components
    PredicateSource.V2: 4,  # (H), (P), (C), (S) on tau_A
    PredicateSource.V3: 20,  # 8 on {M_x}, 8 on {F_v} per block, 2 + 2 sums
    PredicateSource.V7: 4,  # (H) and (P) on s0, the trace leg, the marginal
}


def test_the_enumeration_is_eight_items_and_the_transcript_covers_them() -> None:
    """THE COMPLETENESS TEST: every source the row enumerates, per element.

    ``recorded_predicates.scope_note``: "THE ENUMERATION LISTS EVERY DECISION
    THE RECORD KEYS PER ELEMENT AND IS COMPLETE FOR THOSE." So the eight items
    are read out of the row and each is held against the transcript, with the
    sources it names written out here from its own text.

    TWO OF THE EIGHT ARE NOT FULLY COVERED AND EACH SAYS SO AT ITS ASSERTION.
    They are findings, not silences: V6 has no element on this declaration
    (``CList`` is empty) and is covered by the second test below, and item 8's
    last clause -- the virtual ensemble's own conditions -- is decided by the
    transmitter before this module sees an artefact. The third, the conditional
    families' exact admissibility, is decided and keyed.
    """
    enumeration = _enumeration()
    assert len(enumeration) == 8, (
        "the row's enumeration has eight items; if it grew, the transcript and "
        "this test move with it"
    )
    transcript = _bb84_transcript()
    present = set(transcript.sources)

    # Item 1: V2 and V3 on tau_A, {M_x}, each Bob family and each hat O_k.
    assert "checks V2 and V3" in enumeration[0]
    assert {PredicateSource.V2, PredicateSource.V3} <= present
    # Item 2: check V7 on the candidate it verified.
    assert "check V7 takes on the candidate it verified" in enumeration[1]
    assert PredicateSource.V7 in present
    # Item 3: V6's type decisions -- NO ELEMENT HERE, CList being empty. The
    # decisions are per ENTRY and this declaration declares none, so the
    # honest record is empty and the coverage is asserted on a declaration
    # that HAS entries, below.
    assert "the type decisions of V6" in enumeration[2]
    assert PredicateSource.V6 not in present
    # Items 4 and 5: V1's comparison, and V7's on a supplied witness's map --
    # the second has no subject here either, no witness being supplied.
    assert "V1's sector-map comparison" in enumeration[3]
    assert "the sector-map comparison check V7 makes" in enumeration[4]
    assert PredicateSource.V1 in present
    assert transcript.lookup(PredicateSource.V7, "omega* (supplied witness)") == ()
    # Item 6: (SR1), (SR2) and the three conditions on Psi decided by (G2).
    assert "(SR1), (SR2)" in enumeration[5]
    assert {
        PredicateSource.SR1,
        PredicateSource.SR2,
        PredicateSource.G2,
    } <= present
    # Item 7: the chain. (C1) and (C4) are decided; (S1), (S2) and (S3) are
    # VACUOUS at L_s = 0 -- there is no source link to decide anything on, and
    # a record for one would be a decision nothing took.
    assert "the exact identities (C4) and the source identity (S3)" in enumeration[6]
    assert {PredicateSource.C1, PredicateSource.C4} <= present
    assert not {
        PredicateSource.S1,
        PredicateSource.S2,
        PredicateSource.S3,
    } & present
    # Item 8: the compilation map.
    assert "THE DECISIONS THE COMPILATION MAP TAKES" in enumeration[7]
    assert PredicateSource.COMPILATION_MAP in present

    # --- ITEM 2's PER-BLOCK LEGS ARE RECORDED -----------------------------
    # `feasibility.verify_witness` records them where it decides them, and not
    # AGGREGATED as one boolean over every block.
    # Definition def:exact's (H) and (P) are stated per block, so the key
    # carries the block and not just the candidate.
    per_block = transcript.lookup(
        PredicateSource.V7, "omega* (default candidate)", "s0"
    )
    assert tuple(entry.predicate for entry in per_block) == ("(H)", "(P)")
    assert all(entry.outcome for entry in per_block)

    # Conditional-family admission is the compiler's decision. The virtual
    # ensemble's own admission is transmitter-owned and is excluded from this
    # inventory; no compiler verdict is inferred from the supplier's success.
    assert "the exact admissibility of each conditional family" in enumeration[7]
    assert "the virtual ensemble's own conditions" not in enumeration[7]
    owned = _interface_row()["recorded_predicates"]["transmitter_owned_conditions"]
    assert "decided by the transmitter" in owned
    filling = transcript.for_source(PredicateSource.COMPILATION_MAP)
    assert {entry.predicate for entry in filling} == {
        "(T)",
        "(H)",
        "(P)",
        "(C)",
        "sum_t q_t = 1",
        SUMMATION_PREDICATE,
        "every entry of the emitted N_(u,t) is a binary64 number",
    }
    status = _interface_row()["implementation_status"]
    assert isinstance(status, str)
    # The two limits on the enumeration, stated in the row.
    assert "transmitter-owned ensemble conditions remain with the transmitter" in (
        status
    )
    assert "one exact equality decision" in status
    forms = _interface_row()["recorded_predicates"]["form_reporting"]
    assert "Alice measurement-slot operator" in forms["general_v1"]
    assert "aggregate keyed G2 predicate" in forms["presentation_g2"]
    assert "not declared or executed predicates" in forms["presentation_g2"]
    # And (C3)'s own per-block legs, which the enumeration does not name while
    # the row's first clause reaches them: the scope note binds, so the
    # enumeration is the list and (C3) keys nothing
    # -- still decided in chain.py, still reported through its gate's outcome.
    assert PredicateSource.C3 not in present

    # AND THE WHOLE KEY SET, hand-written above from the row and the
    # declaration. Equality and not containment: a key the row does not fix
    # would be a decision this record invented.
    assert {outcome.key for outcome in transcript.outcomes} == EXPECTED_KEYS
    counted = {
        source: len(transcript.for_source(source)) for source in transcript.sources
    }
    assert counted == EXPECTED_COUNTS
    assert len(transcript) == sum(EXPECTED_COUNTS.values())
    # EVERY OUTCOME HOLDS on the honest instance, and none carries an index:
    # the transcript of a compilation that PASSED is what a consumer could not
    # reconstruct from a refusal, which is why the row asks for it.
    assert all(outcome.outcome for outcome in transcript.outcomes)
    assert all(outcome.first_failure_index is None for outcome in transcript.outcomes)


def test_the_two_items_bb84_has_no_element_for_are_covered_where_it_does() -> None:
    """Item 3 (V6) and item 5 (V7 branch (c)) on a declaration that has both.

    THE DECLARATION IS BB84'S WITH TWO CONSTRAINT ENTRIES ADDED, one scalar
    and one matrix right-hand side, and the checks are called directly: what
    is asserted is the transcript of the CHECK, which is what
    :attr:`ValidationResult.predicates` concatenates.
    """
    declaration = _bb84_declaration()
    entries = (
        ConstraintEntry(
            operator=as_blocks(QUBIT, P_Z0), relation=Relation.GE, rhs=F(1, 4)
        ),
        ConstraintEntry(
            operator=as_blocks(QUBIT, P_Z1),
            relation=Relation.LE,
            rhs=matrix(((F(1, 2), 0), (0, F(1, 2)))),
            arriving_tag=RhsTag.GENERAL,
        ),
    )
    with_entries = replace(declaration, constraint_list=entries)

    v6 = check_v6(with_entries)
    assert v6.passed
    keys = [
        (outcome.element, outcome.predicate) for outcome in v6.predicates
    ]
    # Per ENTRY, and only the decisions that entry reached: the first is a
    # scalar, so the two ``general`` questions are not asked of it; the second
    # arrived carrying a tag, so the agreement question is.
    assert ("CList[1]", "(H)") not in keys
    assert ("CList[2]", "(H)") in keys
    assert ("CList[2]", "Theta_k is an operator on A") in keys
    assert (
        "CList[2]",
        "the arriving tag agrees with the type of the datum",
    ) in keys
    assert {element for element, _ in keys} == {"CList[1]", "CList[2]"}

    # And V3 decides Hermiticity of each hat O_k PER BLOCK, which is the tail
    # of item 1 that CList being empty leaves out.
    v3 = check_v3(with_entries)
    assert v3.passed
    assert (
        PredicateOutcome(
            source=PredicateSource.V3,
            predicate="(H)",
            element="O^_2",
            block="s0",
            outcome=True,
        )
        in v3.predicates
    )


# ---------------------------------------------------------------------------
#  3. The negative cases, one per decider
# ---------------------------------------------------------------------------


def test_validation_records_the_element_index_at_which_s_first_failed() -> None:
    """Condition (S) on ``sum_x M_x``, with the index of the first inexact addition.

    The family is exactly admissible in (H), (P) and (C) and fails (S) at its
    SECOND addition, which is the 1-based index
    :class:`~certiqs_key.foundations.exact.SummationVerdict` computes and the
    refusal detail names.
    """
    declaration = _bb84_declaration()
    rounding = replace(
        declaration,
        alice_povm=dict(zip(_LABELS, ROUNDING_FAMILY, strict=True)),
    )
    outcome = check_v3(rounding)
    assert not outcome.passed
    summation = [
        entry for entry in outcome.predicates if entry.predicate == SUMMATION_PREDICATE
    ]
    assert len(summation) == 1
    assert summation[0].key == (PredicateSource.V3, "{M_x}", None)
    assert summation[0].outcome is False
    assert summation[0].first_failure_index == 2
    assert summation[0].first_inexact_index == 2
    # (C) was decided first and HELD -- the computed total IS the identity --
    # which is the pair Theorem thm:pc12 (ii) exhibits, and the transcript
    # keeps the two apart instead of reporting one verdict for both.
    completeness = [
        entry for entry in outcome.predicates if entry.predicate == "(C)"
    ]
    assert completeness[0].outcome is True
    # Nothing after the failure is recorded: the check returned there.
    assert outcome.predicates[-1] is summation[0]


def test_validation_records_the_component_at_which_a_map_comparison_failed() -> None:
    """V1, per component, with the 0-based position the domain record names."""
    declaration = _bb84_declaration()
    renamed = SectorStructure(
        labels=("s1",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
    )
    povm = dict(declaration.bob_povm)
    povm["(Z,1)"] = BlockOperator.of(renamed, povm["(Z,1)"].blocks)
    outcome = check_v1(replace(declaration, bob_povm=povm))
    assert not outcome.passed
    failing = [entry for entry in outcome.predicates if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].key == (PredicateSource.V1, "F_(Z,1)", None)
    assert failing[0].predicate == "identifier"
    assert failing[0].first_failure_index == 0
    # The family before it was compared on all four components and held; the
    # families after it were never compared.
    assert len(outcome.predicates) == 1 + 4 + 2


def test_v7_records_every_leg_of_thm_pc5_per_block_and_per_entry() -> None:
    """Item 2 in full, on a declaration with constraint entries.

    THE ENTRIES ARE CHOSEN SO THAT ONE HOLDS AND THE NEXT FAILS at the default
    candidate ``omega* = tau_A (x) 1_Q / d_Q``, which on this declaration is
    ``1_4 / 4``: the trusted left-hand side of Eq. ``eq:feas-modes`` is
    ``diag(1/4, 1/4)`` for the operator ``P_Z0``, the first entry compares it
    against ``(1/4) tau_A = diag(1/8, 1/8)`` and holds, and the second against
    ``1 . tau_A = diag(1/2, 1/2)`` and fails. So the per-entry legs are
    recorded with the second entry's index, which is what the row asks a
    failed predicate for.
    """
    declaration = replace(
        _bb84_declaration(),
        constraint_list=(
            ConstraintEntry(
                operator=as_blocks(QUBIT, P_Z0), relation=Relation.GE, rhs=F(1, 4)
            ),
            ConstraintEntry(
                operator=as_blocks(QUBIT, P_Z0), relation=Relation.GE, rhs=F(1)
            ),
        ),
    )
    outcome, feasibility = check_v7(declaration)
    assert not outcome.passed
    assert not feasibility.passes
    assert feasibility.default_verification is not None
    # THE AGGREGATE VERDICTS ARE UNCHANGED by the unrolling: one leg failed and
    # it is the constraints leg, which is what the refusal detail names.
    assert feasibility.default_verification.failing_legs() == ("constraints",)

    keyed = [
        (entry.predicate, entry.element, entry.block, entry.outcome)
        for entry in outcome.predicates
    ]
    assert keyed == [
        # (H) and (P) per block, on the candidate the verdict rests on.
        ("(H)", DEFAULT_CANDIDATE, "s0", True),
        ("(P)", DEFAULT_CANDIDATE, "s0", True),
        ("tr omega = 1", DEFAULT_CANDIDATE, None, True),
        # The marginal equality is keyed by tau_A, trusted mode deciding it.
        ("omega_A = tau_A", "tau_A", None, True),
        # ONE LEG PER ENTRY, in the list's order, and BOTH are decided: the
        # loop does not stop at the first failure, so the record says of each
        # entry what was decided of it.
        ("the Loewner leg of Eq. eq:feas-modes", "CList[1]", None, True),
        ("the Loewner leg of Eq. eq:feas-modes", "CList[2]", None, False),
    ]
    failing = [entry for entry in outcome.predicates if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].first_failure_index == 2

    # AND THE CANDIDATE IS PART OF THE KEY. Supply the same failing state as a
    # witness: both candidates are now verified, the verdict rests on the
    # SUPPLIED one -- whose failing legs the refusal detail names -- and that is
    # the one the transcript is about. Recording both would answer one question
    # twice.
    supplied, _ = check_v7(declaration, default_witness(declaration))
    assert {entry.element for entry in supplied.predicates} == {
        SUPPLIED_WITNESS,
        "tau_A",
        "CList[1]",
        "CList[2]",
    }
    assert DEFAULT_CANDIDATE not in {
        entry.element for entry in supplied.predicates
    }


def test_a_witness_rejected_on_its_map_records_the_component_and_the_legs() -> None:
    """Item 5, and what item 2 records beside it on that path.

    Condition (T) on a supplied witness is compared in
    :func:`check_v7` itself, BEFORE any verification, and a disagreement
    refuses with ``no_feasibility_witness`` -- V7's reason and not V1's. The
    default candidate is nonetheless verified on that path, so ITS legs were
    decided and are recorded beside the failing component; the supplied witness
    is never verified, so no leg of it appears.
    """
    declaration = replace(
        _bb84_declaration(),
        constraint_list=(
            ConstraintEntry(
                operator=as_blocks(QUBIT, P_Z0), relation=Relation.GE, rhs=F(1, 4)
            ),
        ),
    )
    witness = default_witness(declaration)
    renamed = SectorStructure(
        labels=("s1",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
    )
    outcome, _ = check_v7(
        declaration,
        JointBlockOperator.of(renamed, declaration.alice_dim, witness.blocks),
    )
    assert not outcome.passed
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.NO_FEASIBILITY_WITNESS
    assert [
        (entry.predicate, entry.element, entry.outcome)
        for entry in outcome.predicates[:2]
    ] == [
        ("block_kind", SUPPLIED_WITNESS, True),
        ("identifier", SUPPLIED_WITNESS, False),
    ]
    assert outcome.predicates[1].first_failure_index == 0
    decided = {entry.element for entry in outcome.predicates[2:]}
    assert decided == {DEFAULT_CANDIDATE, "tau_A", "CList[1]"}
    assert SUPPLIED_WITNESS not in decided


def test_an_untrusted_declaration_records_the_scalar_leg_and_no_marginal() -> None:
    """The two legs Eq. ``eq:feas-modes`` and ``def:feasible`` make conditional.

    WHICH LINE is read is decided by the EMITTED SOURCE MODE, so the leg's name
    is the scalar one here; and Definition ``def:feasible`` imposes NO marginal
    condition in untrusted mode, so no ``omega_A = tau_A`` outcome is recorded
    -- the aggregate verdict is ``True`` there "in the sense 'no condition to
    violate'", and recording that as a decided outcome would report a
    comparison nothing made.
    """
    declaration = replace(
        _bb84_declaration(),
        alice_marginal=None,
        constraint_list=(
            ConstraintEntry(
                operator=as_blocks(QUBIT, P_Z0), relation=Relation.EQ, rhs=F(1, 4)
            ),
        ),
    )
    outcome, _ = check_v7(declaration)
    keyed = [(entry.predicate, entry.element) for entry in outcome.predicates]
    assert ("omega_A = tau_A", "tau_A") not in keyed
    # Equality is one exact decision. PC5 proves its equivalence to the two
    # operator inequalities, and the interface records that one predicate;
    # scalar equality is the one-dimensional specialization.
    equality = [
        entry for entry in outcome.predicates if entry.element == "CList[1]"
    ]
    assert len(equality) == 1
    assert equality[0].predicate == "the scalar equality leg of Eq. eq:feas-modes"


def test_a_g1_refusal_emits_the_transcript_that_refused_it() -> None:
    """END TO END, on the one refusal path a ``gate_report`` exists on.

    Row 1 of the gate outcome table refuses "naming the check", and the
    resolution it produces CARRIES A REPORT -- ``(G1) failed`` with three
    unengaged gates -- so the transcript travels with it and a consumer of a
    (G1) refusal gets both the reason and the decisions behind it. The entry
    below declares a matrix right-hand side that is not Hermitian, which is
    "the one decision of that check that is on DATA rather than on a type",
    and V6 refuses it.
    """
    specification = bb84_specification(HALF, HALF, HALF, HALF)
    refused = compile_specification(
        replace(
            specification,
            constraints=SpecConstraints(
                entries=(
                    ConstraintEntry(
                        operator=as_blocks(QUBIT, P_Z0),
                        relation=Relation.LE,
                        rhs=matrix(((1, 1), (0, 1))),
                    ),
                )
            ),
        )
    )
    assert refused.refuses
    assert refused.refusal is not None
    assert refused.refusal.reason is RefusalReason.CHECK_V6_FAILED
    assert refused.gate_report is not None
    transcript = refused.gate_report.transcript
    failing = [entry for entry in transcript.outcomes if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].key == (PredicateSource.V6, "CList[1]", None)
    assert failing[0].predicate == "(H)"
    assert failing[0].first_failure_index == 1
    # AND THE DECISIONS TAKEN BEFORE IT ARE THERE TOO, which is the whole
    # point of a transcript over a refusal reason: V1 compared the entry's
    # operator against the emitted sector map (a family CList being empty does
    # not have) and V3 decided its Hermiticity per block.
    assert transcript.lookup(PredicateSource.V1, "O^_1") != ()
    assert transcript.lookup(PredicateSource.V3, "O^_1", "s0") != ()
    # V7 could not be READ against this candidate -- Eq. eq:feas-modes is not
    # well posed once V6 has failed -- so it decided nothing and records
    # nothing.
    assert PredicateSource.V7 not in transcript.sources


def test_the_chain_records_the_outcome_index_at_which_c4_first_failed() -> None:
    """(C4) is quantified over ``v``, and the record carries that index."""
    report = check_chain(*_swapped_pullback())
    assert report.failing_condition == "C4"
    failing = [entry for entry in report.predicates if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].key == (PredicateSource.C4, "F_v0", None)
    assert failing[0].first_failure_index == 1
    # (C1) was decided before it and holds, so its clauses are in the record
    # too: what the transcript carries is what was decided, in that order.
    assert report.predicates[0].source is PredicateSource.C1


def _swapped_pullback() -> tuple[ReductionChain, ChainContext]:
    """Return a Band-A chain whose physical family is the emitted one, swapped.

    Eq. ``eq:pullback`` then fails at the FIRST emitted outcome: the identity
    link pulls ``F_v0`` back to itself and the physical family declares
    ``F^ph_v0 = F_v1``.
    """
    descriptor = SystemDescriptor(
        name="Q",
        dim=2,
        side=Side.RECEIVER,
        sectors=(("s0", 2),),
        sector_block_kind=BlockKind.PROOF_SECTOR,
    )
    chain = ReductionChain(
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment=LinkStage.RECEIVER,
                link_type="squashing (identity)",
                source_descriptor=descriptor,
                target_descriptor=descriptor,
                status=LinkStatus.EXACT,
                channel=identity_channel(2),
                transported_constraints=(),
                license_slot=None,
                target_alphabet=("v0", "v1"),
                target_povm={
                    "v0": BlockOperator.of(QUBIT, (P_Z0,)),
                    "v1": BlockOperator.of(QUBIT, (P_Z1,)),
                },
            ),
        ),
        outcome_correspondence={"v0": "v0", "v1": "v1"},
    )
    context = ChainContext(
        physical_descriptor=descriptor,
        physical_alphabet=("v0", "v1"),
        physical_povm={"v0": P_Z1, "v1": P_Z0},
        target_descriptor=descriptor,
        emitted_alphabet=("v0", "v1"),
        emitted_povm={
            "v0": BlockOperator.of(QUBIT, (P_Z0,)),
            "v1": BlockOperator.of(QUBIT, (P_Z1,)),
        },
        gamma={"v0": "v0", "v1": "v1"},
    )
    return chain, context


def test_the_source_segment_half_of_item_7_is_keyed_per_link_and_per_signal() -> None:
    """(S1), (S2) and (S3) on a two-link source segment, which BB84 has none of.

    Item 7's SOURCE half is keyed by code that the completeness test above
    cannot read: it runs on BB84, where ``L_s = 0`` makes all three conditions
    vacuous, so it can only assert their ABSENCE. The frozen registry pins their
    VERDICTS; this test pins their key shapes, which would otherwise change in
    silence.

    THE EXPECTED LIST IS DERIVED FROM THE ROW AND FROM ``def:chaincond``, not
    read off the record. Item 7 asks for "(S1)'s inter-link matches" and for
    "(S2)'s comparison of the two index sets each source link carries and of
    the |X| declared weights p_x it leaves untouched"; ``def:chaincond`` gives
    (S1) its two end clauses and its Alice-side clause, and (S3) its identity
    per signal. So, in the order the decisions are taken: the side clause per
    LINK, the adjacency clause per adjacent PAIR keyed by the earlier link,
    the two end clauses on the first and the last link, (S2)'s index-set
    clause per LINK and its weight clause per SIGNAL, and (S3) per SIGNAL.
    """
    report = check_chain(*_two_link_source_chain())
    assert report.failing_condition is None
    source_side = [
        entry
        for entry in report.predicates
        if entry.source
        in {PredicateSource.S1, PredicateSource.S2, PredicateSource.S3}
    ]
    assert [(entry.source, entry.element) for entry in source_side] == [
        (PredicateSource.S1, "Xi_1"),
        (PredicateSource.S1, "Xi_2"),
        (PredicateSource.S1, "Xi_1 -> Xi_2"),
        (PredicateSource.S1, "Xi_1"),
        (PredicateSource.S1, "Xi_2"),
        (PredicateSource.S2, "Xi_1"),
        (PredicateSource.S2, "Xi_2"),
        (PredicateSource.S2, "p_x0"),
        (PredicateSource.S2, "p_x1"),
        (PredicateSource.S3, "rho^v_x0"),
        (PredicateSource.S3, "rho^v_x1"),
    ]
    # Every one of them HOLDS on this chain, and none carries an index: the
    # record's own invariant is that an index belongs to a failure.
    assert all(entry.outcome for entry in source_side)
    assert all(entry.first_failure_index is None for entry in source_side)
    # AND NONE IS PER BLOCK. (S1)-(S3) are decisions about descriptors, index
    # sets, weights and states, none of which has a sector decomposition to
    # key by; a block here would be a component the condition does not name.
    assert all(entry.block is None for entry in source_side)
    # (S2)'s WEIGHT CLAUSE NAMES BOTH HALVES OF WHAT IT DECIDES: the
    # weight is tabulated on both sides AND equal. The conjunction is false in
    # two ways, and a predicate reading "left untouched" would tell a consumer
    # the segment reweighted a weight that was never tabulated at all.
    weights = [entry for entry in source_side if entry.element.startswith("p_")]
    assert {entry.predicate for entry in weights} == {
        "p_x is tabulated on both sides and equal"
    }


def _two_link_source_chain() -> tuple[ReductionChain, ChainContext]:
    """Return a chain with a TWO-LINK source segment on which (S1)-(S3) hold.

    Two identity source maps, from the virtual transmitted system through an
    intermediate one to the transmitted system, beside the minimal receiver
    segment, with the virtual ensemble tabulated identically on both sides of
    the segment -- so every source-side condition holds and the record carries
    its full key shape rather than stopping at a first failure.
    """
    virtual = SystemDescriptor(
        name="A''",
        dim=2,
        side=Side.ALICE,
        sectors=(("s0", 2),),
        sector_block_kind=BlockKind.PROOF_SECTOR,
    )
    middle = replace(virtual, name="A_mid")
    transmitted = replace(virtual, name="A'")
    received = SystemDescriptor(
        name="Q",
        dim=2,
        side=Side.RECEIVER,
        sectors=(("s0", 2),),
        sector_block_kind=BlockKind.PROOF_SECTOR,
    )

    def source_link(
        link_id: str, before: SystemDescriptor, after: SystemDescriptor
    ) -> ChainLink:
        return ChainLink(
            link_id=link_id,
            segment=LinkStage.SOURCE,
            link_type="source map (identity)",
            source_descriptor=before,
            target_descriptor=after,
            status=LinkStatus.EXACT,
            channel=identity_channel(2),
            transported_constraints=(),
            license_slot=None,
            target_alphabet=("x0", "x1"),
            target_povm=None,
        )

    chain = ReductionChain(
        source_segment=(
            source_link("Xi_1", virtual, middle),
            source_link("Xi_2", middle, transmitted),
        ),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment=LinkStage.RECEIVER,
                link_type="squashing (identity)",
                source_descriptor=received,
                target_descriptor=received,
                status=LinkStatus.EXACT,
                channel=identity_channel(2),
                transported_constraints=(),
                license_slot=None,
                target_alphabet=("v0", "v1"),
                target_povm={
                    "v0": BlockOperator.of(QUBIT, (P_Z0,)),
                    "v1": BlockOperator.of(QUBIT, (P_Z1,)),
                },
            ),
        ),
        outcome_correspondence={"v0": "v0", "v1": "v1"},
    )
    context = ChainContext(
        physical_descriptor=received,
        physical_alphabet=("v0", "v1"),
        physical_povm={"v0": P_Z0, "v1": P_Z1},
        target_descriptor=received,
        emitted_alphabet=("v0", "v1"),
        emitted_povm={
            "v0": BlockOperator.of(QUBIT, (P_Z0,)),
            "v1": BlockOperator.of(QUBIT, (P_Z1,)),
        },
        gamma={"v0": "v0", "v1": "v1"},
        virtual_descriptor=virtual,
        transmitted_descriptor=transmitted,
        signal_alphabet=("x0", "x1"),
        virtual_weights={"x0": HALF, "x1": HALF},
        specified_weights={"x0": HALF, "x1": HALF},
        virtual_states={"x0": P_Z0, "x1": P_Z1},
        specified_states={"x0": P_Z0, "x1": P_Z1},
        link_index_sets={"Xi_1": ("x0", "x1"), "Xi_2": ("x0", "x1")},
    )
    return chain, context


def test_the_certificate_records_the_signal_index_at_which_sr2_failed() -> None:
    """(SR2) is quantified over ``x``; the failure carries the signal index."""
    psi = matrix(
        (
            (HALF, 0, 0, HALF),
            (0, 0, 0, 0),
            (0, 0, 0, 0),
            (HALF, 0, 0, HALF),
        )
    )
    certificate = SourceReplacementCertificate(
        alice_marginal=matrix(((HALF, 0), (0, HALF))),
        psi=psi,
        virtual_dim=2,
        virtual_weights={"x0": HALF, "x1": HALF},
        # rho^v_{x1} SHOULD be P_Z1; declaring P_Z0 twice is the mis-specified
        # source (SR2) exists to catch, and it fails at the SECOND label.
        virtual_states={"x0": P_Z0, "x1": P_Z0},
    )
    verification = verify_certificate(
        certificate, ("x0", "x1"), {"x0": P_Z0, "x1": P_Z1}
    )
    assert not verification.passes
    recorded = _certificate_predicates(verification)
    failing = [entry for entry in recorded if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].key == (PredicateSource.SR2, "x = x1", None)
    assert failing[0].first_failure_index == 2
    # The three conditions on Psi and (SR1) were decided and hold.
    assert len([entry for entry in recorded if entry.source is PredicateSource.G2]) == 4
    assert all(
        entry.outcome for entry in recorded if entry.source is not PredicateSource.SR2
    )


def test_the_compilation_map_records_the_flat_entry_index_of_an_unrepresentable() -> (
    None
):
    """``emitted_value_not_representable``, per emitted label and per entry."""
    third = F(1, 3)
    choices = PublicChoices(
        party=Party.ALICE,
        choices=("t0", "t1"),
        weights={"t0": HALF, "t1": HALF},
        conditional_alphabets={"t0": ("u0",), "t1": ("u0",)},
        # 1/3 is no binary64 number, so the product q_t N_{u|t} is not one
        # either -- and the entry is the SECOND of the first emitted matrix.
        conditional_elements={
            "t0": {"u0": matrix(((1, third), (third, 1)))},
            "t1": {"u0": matrix(((1, 0), (0, 1)))},
        },
    )
    decision = decide_emission(weighted_family(choices))
    assert decision.refusal is not None
    failing = [entry for entry in decision.predicates if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].key == (PredicateSource.COMPILATION_MAP, "A:(u0,t0)", None)
    assert failing[0].first_failure_index == 1
    # The weight sum was decided first, on both legs, and holds; the second
    # emitted label was never reached.
    assert [entry.predicate for entry in decision.predicates[:2]] == [
        "sum_t q_t = 1",
        SUMMATION_PREDICATE,
    ]
    assert len(decision.predicates) == 3


def test_the_compilation_map_records_the_row_of_p_at_which_s_failed() -> None:
    """Route C: a row sum of ``P`` that ROUNDS, with the index of the addition.

    ``fl(0.9) + fl(0.1)`` is the presentation Theorem ``thm:pc12`` (ii) writes
    out: the exact sum is not one and the addition is not exact, so (S) refuses
    at the SECOND entry of the row in the declared order of the choice
    alphabet.
    """
    weighting = ChoiceWeighting(
        choice_alphabet=("test", "gen"),
        setting_alphabet=("Z",),
        setting_of={"v0": "Z", "v1": "Z"},
        matrix={("Z", "test"): F(0.9), ("Z", "gen"): F(0.1)},
    )
    refusal = setting_weighted_family(
        ("v0", "v1"),
        {
            "v0": BlockOperator.of(QUBIT, (P_Z0,)),
            "v1": BlockOperator.of(QUBIT, (P_Z1,)),
        },
        weighting,
    )
    # THE REFUSAL IS WHAT REACHES A CALLER, and it carries no transcript: a
    # refused weighting emits no declaration and therefore no gate report, so
    # the decisions are read off the decider, which is where the row's index
    # lives. ``_decide_stochastic`` is private and is reached here for exactly
    # that reason: it is the only place the row-sum decisions survive a
    # refusal.
    assert isinstance(refusal, Refusal)
    assert refusal.reason is RefusalReason.CHOICE_WEIGHT_NOT_STOCHASTIC
    decision = _decide_stochastic(weighting)
    assert decision.refusal is not None
    failing = [entry for entry in decision.predicates if not entry.outcome]
    assert len(failing) == 1
    assert failing[0].key == (PredicateSource.COMPILATION_MAP, "P( . | Z)", None)
    assert failing[0].predicate == SUMMATION_PREDICATE
    assert failing[0].first_failure_index == 2
    assert failing[0].first_inexact_index == 2


def test_route_c_records_the_support_and_the_row_sums_where_it_passes() -> None:
    """The support is a DECISION and its outcome is MEMBERSHIP, not a violation."""
    weighting = ChoiceWeighting(
        choice_alphabet=("test", "gen"),
        setting_alphabet=("Z", "X"),
        setting_of={"v0": "Z", "v1": "X"},
        matrix={
            ("Z", "test"): F(1, 4),
            ("Z", "gen"): F(3, 4),
            ("X", "test"): F(1),
            ("X", "gen"): F(0),
        },
    )
    family = setting_weighted_family(
        ("v0", "v1"),
        {
            "v0": BlockOperator.of(QUBIT, (P_Z0,)),
            "v1": BlockOperator.of(QUBIT, (P_Z1,)),
        },
        weighting,
    )
    assert isinstance(family, SettingWeightedFamily)
    recorded = family.predicates
    support = [
        entry
        for entry in recorded
        if entry.predicate.startswith("(v, f) in V_P")
    ]
    assert [(entry.element, entry.outcome) for entry in support] == [
        ("B:(v0,test)", True),
        ("B:(v0,gen)", True),
        ("B:(v1,test)", True),
        ("B:(v1,gen)", False),
    ]
    # OFF THE SUPPORT IS NOT A FAILURE: "a pair (v, f) with P(f | t(v)) = 0 is
    # not an outcome, is not emitted and indexes nothing", so the outcome is
    # False and there is no index, there being no failure to index.
    assert support[-1].first_failure_index is None
    # Both rows of P were decided, on both legs, before any product was formed.
    assert [
        (entry.element, entry.predicate)
        for entry in recorded
        if entry.element in {"P( . | Z)", "P( . | X)"}
    ] == [
        ("P( . | Z)", SUMMATION_PREDICATE),
        ("P( . | Z)", "sum_f P(f | t) = 1"),
        ("P( . | X)", SUMMATION_PREDICATE),
        ("P( . | X)", "sum_f P(f | t) = 1"),
    ]


# ---------------------------------------------------------------------------
#  4. The shape of an absent transcript
# ---------------------------------------------------------------------------


def test_a_gate_report_built_without_a_transcript_says_so() -> None:
    """An unfilled transcript is a visible ``()`` and not a missing field.

    This is the property a defaulted field has over a recorder
    threaded down: a path that records nothing CANNOT be told apart from one
    whose decisions all held if the record is optional, and here it can.
    """
    resolution = resolve_gates(
        GateInputs(
            validator_passed=True,
            emitted_mode=SourceMode.UNTRUSTED,
            alice_dim=2,
            certificate=CertificateState.ABSENT,
            has_constraint_entries=False,
            list_licensed=True,
            license_present=False,
        )
    )
    assert resolution.report.transcript is EMPTY_TRANSCRIPT
    assert len(resolution.report.transcript) == 0
    assert resolution.report.as_machine_record()["predicates"] == []


def test_the_emitted_record_carries_the_transcript_beside_the_gates() -> None:
    """``predicates`` is a key of its own, not a field of a gate's entry."""
    result = compile_specification(bb84_specification(HALF, HALF, HALF, HALF))
    record = result.as_machine_record()["gate_report"]
    assert isinstance(record, dict)
    assert set(record) == {"gates", "predicates"}
    gates = record["gates"]
    assert isinstance(gates, list)
    assert all(
        set(entry) == {"gate", "engaged", "verdict", "degeneration"}
        for entry in gates
    )
    predicates = record["predicates"]
    assert isinstance(predicates, list)
    assert len(predicates) == sum(EXPECTED_COUNTS.values())
    # THE FIRST DECISION THE COMPILATION TAKES is (T) on the receiver's
    # conditional families, and not the receiver weight sum's equality, because that
    # decision is taken "BEFORE ANY PRODUCT IS FORMED and therefore before the chain's
    # conditions are decided" (fail-closed row 1). The transcript's order IS
    # the decision order, so this assertion is where that order is visible.
    assert predicates[0] == {
        "source": "compilation_map",
        "predicate": "(T)",
        "element": "B:{N_(u|t)}",
        "block": None,
        "outcome": True,
        "first_failure_index": None,
        "first_inexact_index": None,
    }
