"""Group PC-M -- the 0.3.0 exact number model, READ and not merely frozen.

WHY THIS FILE EXISTS. The registry has six frozen tuples for the exact
number model, with every value derived twice by independent routes. Without a
reader they would be frozen and unread: the four fail-closed rows
(``alice_povm_summation_rounds``, ``bob_povm_summation_rounds``,
``alice_marginal_trace_rounds``, ``emitted_value_not_representable``) would
occur only inside an enum-vocabulary assertion, which "pins the spelling
of an enum and would pass with every one of their refusal paths deleted".

This file is the reader. Each test drives a frozen tuple THROUGH THE CODE and
compares the code's verdict against the frozen one:

* ``SUMMATION_CASES``            -> ``compile_specification`` on the BB84
                                    instance's weight presentations;
* ``EMISSION_REPRESENTABILITY_CASES``
                                 -> ``resolve_povm`` / ``decide_emission``;
* ``CERTIFICATE_OPERATOR_CASES`` -> ``verify_certificate``, per predicate;
* ``RHS_TAG_CASES``             -> ``ConstraintEntry.tag``, check V6 and gate
                                    (G3)(a)'s licensing;
* ``SECTOR_MAP_COMPARISON_CASES`` -> check V1's four-component comparison;
* ``DECLARED_ORDER_CASES``      -> the two orders the compilation map is BOUND
                                    to, and the one alphabet ``idx`` does not
                                    index.

NOTHING HERE EDITS A FROZEN VALUE, and nothing here re-derives one. Every
assertion reads the registry and drives the code; where the two disagree the
CODE is wrong, which is the direction a golden test exists to enforce (the
two-instance freeze).
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import pytest
from instances.bb84.specification import band_a_block_kind, bb84_specification
from registry_protocol_compiler import (
    CERTIFICATE_OPERATOR_CASES,
    DECLARED_ORDER_CASES,
    EMISSION_REPRESENTABILITY_CASES,
    RHS_TAG_CASES,
    SECTOR_MAP_COMPARISON_CASES,
    SUMMATION_CASES,
    CertificateOperatorCase,
    DeclaredOrderCase,
    EmissionRepresentabilityCase,
    RhsTagCase,
    SectorMapComparisonCase,
    SummationCase,
)

from certiqs_key.domain.constraints import ConstraintEntry, Relation, RhsTag
from certiqs_key.foundations.blocks import (
    BlockOperator,
    JointBlockOperator,
    SectorStructure,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import identity, matrix, scale
from certiqs_key.protocol_compiler import (
    INDEXED_ALPHABETS,
    Party,
    PublicChoices,
    compile_specification,
    decide_conditional_families,
    decide_emission,
    resolve_povm,
    weighted_family,
)
from certiqs_key.protocol_compiler.validation import check_v1, check_v6, check_v7
from certiqs_key.transmitter import SourceReplacementCertificate, verify_certificate

pytestmark = [pytest.mark.contract, pytest.mark.oracle]


# ---------------------------------------------------------------------------
#  (a) SUMMATION_CASES -- condition (S), through the whole compilation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", SUMMATION_CASES, ids=lambda c: c.case_id)
def test_the_frozen_summation_verdicts_hold_against_the_compiler(
    case: SummationCase,
) -> None:
    """Group PC-M's frozen (S) verdicts, driven through ``compile_specification``.

    The families differ ONLY in whether the additions forming the completeness
    sum were exact: all are genuine POVMs, every entry is a binary64 number,
    and all compute to exactly ``1_A``. A test written on the computed total
    alone would pass them all, which is precisely what Rem.
    ``rem:bb84checks`` warns of. So this one is written on the verdict and on
    the index the refusal must carry.

    THE DECIMAL-LITERAL FAMILY IS FROZEN TWICE (O-PC-EXACT-SUMMATION's
    ``revalidation`` records it). Presented
    through Alice's public-choice record, ``req:weight-list`` refuses the
    weight list first, with ``choice_weights_not_normalized`` naming the first
    rounding addition of the list; presented directly, with no weight list,
    check V3 refuses the completeness sum with ``alice_povm_summation_rounds``
    naming its first inexact element.
    """
    weights = dict(case.weights)
    specification = bb84_specification(
        weights["p^A_Z"], weights["p^A_X"], F(1, 2), F(1, 2)
    )
    if case.presentation == "direct":
        # No public-choice record on Alice's side: the compiler reads the
        # transmitter artefact's own `alice_povm`, the same matrices.
        specification = replace(
            specification, source=replace(specification.source, alice_choices=None)
        )
    else:
        assert case.presentation == "public_choices", case.case_id
    result = compile_specification(specification)
    # (C) holds on BOTH cases, on the computed total. That is the premise the
    # whole entry rests on, so it is asserted rather than assumed.
    assert case.computed_sum_is_identity is True
    assert case.every_entry_is_binary64 is True

    if case.sum_rounds_nowhere:
        assert case.refusal_reason is None, case.case_id
        assert case.first_inexact_addition_index is None, case.case_id
        assert result.refusal is None, case.case_id
        assert result.declaration is not None, case.case_id
        # The exact total IS the identity here, which is what (S) buys.
        assert case.exact_total_multiple_of_identity == F(1), case.case_id
    else:
        assert result.refusal is not None, case.case_id
        assert str(result.refusal.reason) == case.refusal_reason, case.case_id
        # AND THE REFUSAL CARRIES WHERE, which Section 2.3 requires of an (S)
        # failure: "the index of the first inexact addition" -- of the weight
        # list where req:weight-list refused, of the completeness sum where V3
        # did.
        assert case.first_inexact_addition_index is not None
        if case.weight_list_first_inexact_addition is not None:
            assert case.refusal_reason == "choice_weights_not_normalized"
            assert (
                f"addition {case.weight_list_first_inexact_addition}"
                in result.refusal.detail
            ), case.case_id
            # The exact weight sum is named too: it is not 1.
            assert str(case.exact_total_multiple_of_identity) in result.refusal.detail
        else:
            assert (
                f"element {case.first_inexact_addition_index}"
                in result.refusal.detail
            ), case.case_id
        # The exact total is NOT the identity, and the gap is the 2**-55 the
        # contract writes out.
        assert case.exact_total_multiple_of_identity == 1 + F(1, 2**55)
        assert result.declaration is None, case.case_id


def test_both_summation_verdicts_are_exercised_so_neither_branch_is_vacuous() -> None:
    """A parametrized set proves nothing if every member falls on one side.

    The frozen reasons are three: none, the
    weight list's (req:weight-list) and V3's (S) leg on {M_x}, so both
    refusals on the public-choice presentation are exercised.
    """
    verdicts = {case.sum_rounds_nowhere for case in SUMMATION_CASES}
    assert verdicts == {True, False}
    reasons = {case.refusal_reason for case in SUMMATION_CASES}
    assert reasons == {
        None,
        "choice_weights_not_normalized",
        "alice_povm_summation_rounds",
    }


# ---------------------------------------------------------------------------
#  (e) EMISSION_REPRESENTABILITY_CASES -- def:weighted's one emission duty
# ---------------------------------------------------------------------------


def _emission_choices(case: EmissionRepresentabilityCase) -> PublicChoices:
    """Build the two-choice family the case describes, on a qubit.

    ``N_{0|t} = diag(e, 1 - e)`` and ``N_{1|t} = diag(1 - e, e)`` with ``e`` the
    frozen ``conditional_entry``: a genuine POVM whose completeness sum is
    exact, so that every decision upstream of the product passes and the case
    isolates the representability of ``q_t N_{u|t}``.
    """
    entry = case.conditional_entry
    other = 1 - entry
    conditional = {
        "u0": matrix(((entry, 0), (0, other))),
        "u1": matrix(((other, 0), (0, entry))),
    }
    return PublicChoices(
        party=Party.ALICE,
        choices=("t0", "t1"),
        weights={"t0": case.weights[0], "t1": case.weights[1]},
        conditional_alphabets={"t0": ("u0", "u1"), "t1": ("u0", "u1")},
        conditional_elements={"t0": conditional, "t1": conditional},
    )


@pytest.mark.parametrize(
    "case", EMISSION_REPRESENTABILITY_CASES, ids=lambda c: c.case_id
)
def test_the_frozen_emission_decisions_hold_against_resolve_povm(
    case: EmissionRepresentabilityCase,
) -> None:
    """Def. ``def:weighted``'s decision, on the path that takes it.

    ``resolve_povm`` is "the ONLY path in this package from a public-choice
    record to emitted matrices" (Thm. ``thm:choice-encoding`` (iii)'s exclusivity
    clause), so the frozen verdict is driven through IT and not only through
    ``decide_emission``: a refusal asserted only on ``decide_emission`` would
    be unreachable from any compilation if nothing called it.
    """
    choices = _emission_choices(case)

    # THE EXACT PRODUCT, re-formed here and compared with the frozen one. The
    # arithmetic is the registry's; this is the code agreeing with it.
    product = case.weights[0] * case.conditional_entry
    assert product == case.exact_product, case.case_id

    # THE FROZEN `conditional_family_exactly_admissible` FIELD. Each case's
    # ``arithmetic`` works the conditional family's (H), (P), (C) and (S) by
    # hand, so that the case isolates the representability of the product. It
    # is the oracle of the predicate it names.
    # The declared system is a qubit: the frozen conditional families are
    # 2x2 and (C) is compared with 1_2, which is the identity on the system
    # the presentation measures and not on the arrays' own dimension.
    admissibility = decide_conditional_families(choices, 2)
    assert (
        admissibility.admitted is case.conditional_family_exactly_admissible
    ), case.case_id

    family = weighted_family(choices)
    decision = decide_emission(family)
    assert decision.weights_sum_rounds_nowhere is case.weights_sum_rounds_nowhere
    assert decision.every_product_is_binary64 is case.product_is_binary64

    resolution = resolve_povm(choices)
    if case.emits:
        assert case.refusal_reason is None, case.case_id
        assert resolution.refusal is None, case.case_id
        assert resolution.povm is not None, case.case_id
        # The emitted element carries the weight ALREADY INSIDE (eq:weighted).
        assert resolution.require().elements["(u0,t0)"][0][0].re == case.exact_product
    else:
        assert resolution.povm is None, case.case_id
        assert resolution.refusal is not None, case.case_id
        assert str(resolution.refusal.reason) == case.refusal_reason, case.case_id
        # "It refuses, and it declares no k": no lattice exponent is emitted
        # anywhere on this path.
        assert "declares no k" in resolution.refusal.detail, case.case_id


def test_both_emission_verdicts_are_exercised() -> None:
    """One emitting case and one refusing case, or the pair proves nothing."""
    assert {case.emits for case in EMISSION_REPRESENTABILITY_CASES} == {True, False}


# ---------------------------------------------------------------------------
#  (c) CERTIFICATE_OPERATOR_CASES -- gate (G2)'s five conditions, per predicate
# ---------------------------------------------------------------------------


def _certificate(case: CertificateOperatorCase) -> SourceReplacementCertificate:
    """Build the certificate the case describes, with its own Psi.

    ``G2-PHI-PLUS`` is ``|Phi+><Phi+|`` -- ``1/2`` at (0,0), (0,3), (3,0), (3,3)
    -- and ``G2-MAXIMALLY-MIXED-NOT-IDEMPOTENT`` is ``1_4 / 4``. Both are read
    off the frozen ``psi_entries``, so the fixture cannot drift from the entry.
    """
    zero, half = case.psi_entries
    if case.case_id == "G2-PHI-PLUS":
        psi = matrix(
            (
                (half, zero, zero, half),
                (zero, zero, zero, zero),
                (zero, zero, zero, zero),
                (half, zero, zero, half),
            )
        )
    else:
        psi = scale(half, identity(4))
    signal_states = {
        "(Z,0)": matrix(((1, 0), (0, 0))),
        "(Z,1)": matrix(((0, 0), (0, 1))),
        "(X,0)": matrix(((F(1, 2), F(1, 2)), (F(1, 2), F(1, 2)))),
        "(X,1)": matrix(((F(1, 2), F(-1, 2)), (F(-1, 2), F(1, 2)))),
    }
    return SourceReplacementCertificate(
        alice_marginal=scale(F(1, 2), identity(2)),
        psi=psi,
        virtual_dim=case.virtual_dim,
        virtual_weights=dict.fromkeys(signal_states, F(1, 4)),
        virtual_states=signal_states,
    )


@pytest.mark.parametrize("case", CERTIFICATE_OPERATOR_CASES, ids=lambda c: c.case_id)
def test_the_frozen_certificate_predicates_hold_against_verify_certificate(
    case: CertificateOperatorCase,
) -> None:
    """The five conditions of Def. ``def:eligible`` (G2), each decided separately.

    "Gate (G2) is stated on all five and Section 2.3's ``gate_report`` keys them
    per predicate, SO A CASE FAILING TWO RECORDS TWO FAILURES." The mixed-state
    case is the sharp one: (SR1) PASSES on it -- "an implementation deciding
    (SR1) alone would admit it" -- and idempotence and (SR2) fail, so a test
    that read only the aggregate verdict could not tell which.
    """
    certificate = _certificate(case)
    alphabet = ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")
    povm = {
        label: scale(F(1, 2), state)
        for label, state in certificate.virtual_states.items()
    }
    verification = verify_certificate(certificate, alphabet, povm)

    # PER PREDICATE, and in the order Definition def:eligible (G2) states them.
    assert verification.purity.hermitian is case.psi_hermitian, case.case_id
    assert verification.purity.idempotent is case.psi_idempotent, case.case_id
    assert verification.purity.trace_is_one is case.psi_trace_is_one, case.case_id
    assert verification.purity.trace_rounds_nowhere is case.psi_trace_rounds_nowhere, (
        case.case_id
    )
    assert verification.sr1_holds is case.sr1_holds, case.case_id
    assert verification.sr2_holds is case.sr2_holds, case.case_id
    assert verification.passes is case.gate_g2_passes, case.case_id

    # THE TRACE PARTIAL SUMS, accumulated over the ROW INDEX in increasing
    # order -- the order Section 2.5 (`summation_order`) fixes for a trace and
    # which `idx` does not carry, that map indexing alphabets and not a basis.
    computed = tuple(partial.re for partial in verification.purity.trace_partial_sums)
    assert computed == case.trace_partial_sums, case.case_id


def test_the_certificate_pair_separates_the_predicates_it_claims_to() -> None:
    """The mixed case fails exactly (2) and (SR2) and passes the other three."""
    mixed = next(
        case
        for case in CERTIFICATE_OPERATOR_CASES
        if case.case_id == "G2-MAXIMALLY-MIXED-NOT-IDEMPOTENT"
    )
    assert mixed.psi_hermitian is True
    assert mixed.psi_trace_is_one is True
    # (SR1) PASSES, which is the sharp part: the failure is invisible to it.
    assert mixed.sr1_holds is True
    assert mixed.psi_idempotent is False
    assert mixed.sr2_holds is False
    assert mixed.gate_g2_passes is False


# ---------------------------------------------------------------------------
#  (b) RHS_TAG_CASES -- V6's tag typing, which compares no numbers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", RHS_TAG_CASES, ids=lambda c: c.case_id)
def test_the_frozen_tag_typing_holds_against_the_entry_and_the_gate(
    case: RhsTagCase,
) -> None:
    """Def. ``def:homog``: "the tag IS the type and is read off it".

    ``expected_tag`` is a function of ``rhs_type`` alone and never of a number,
    which is the content of 0.3.0's design decision 4: "LICENSING IS THEREFORE A
    TYPE CHECK ON THE TAG, AND IT COMPARES NO NUMBERS." So this test reads the
    tag off a datum of the frozen TYPE and never off a frozen value.
    """
    sector_map = SectorStructure(
        labels=("s0",), dims=(2,), block_kind=band_a_block_kind()
    )
    operator = BlockOperator.of(sector_map, [identity(2)])
    rhs: object
    if case.rhs_type == "real scalar":
        rhs = F(1, 4)
    elif case.rhs_type == "Hermitian matrix on A":
        rhs = scale(F(1, 4), identity(2))
    else:
        # "NEITHER ADMITTED OBJECT", which has no tag at all: Definition
        # def:homog admits a real scalar and a Hermitian matrix on A and
        # nothing else, and V6 "REFUSES IT BY TYPE AND NOT MEASURED".
        assert case.expected_tag is None, case.case_id
        rhs = "not an admitted object"

    arriving = (
        None if case.arriving_tag_field is None else RhsTag(case.arriving_tag_field)
    )
    entry = ConstraintEntry(
        operator=operator,
        relation=Relation.LE,
        rhs=rhs,  # type: ignore[arg-type]
        arriving_tag=arriving,
    )

    # THE TAG IS READ OFF THE DATUM AND NEVER OFF THE SUPPLIER'S FIELD, which is
    # why `ConstraintEntry.tag` does not consult `arriving_tag` at all. The
    # frozen `expected_tag` is "the tag V6 reads off the type, or None WHERE THE
    # ENTRY IS REFUSED", so it is None in TWO different situations and they are
    # separated here rather than conflated.
    if case.rhs_type.startswith("neither"):
        # No admitted type, so there is no tag to read: V6 "REFUSES IT BY TYPE
        # AND NOT MEASURED".
        assert entry.tag is None, case.case_id
        assert case.expected_tag is None, case.case_id
        assert case.v6_passes is False, case.case_id
    else:
        # An admitted type, so the tag IS read -- even where the supplier's own
        # field contradicts it. "The tag is NEVER TAKEN ON A SUPPLIER'S WORD
        # AGAINST THE OBJECT THE ENTRY HOLDS", and the contradiction is what V6
        # refuses, not what the tag becomes.
        assert entry.tag is not None, case.case_id
        expected_from_type = (
            RhsTag.HOMOGENEOUS if case.rhs_type == "real scalar" else RhsTag.GENERAL
        )
        assert entry.tag is expected_from_type, case.case_id
        if case.v6_passes:
            assert str(entry.tag) == case.expected_tag, case.case_id
        else:
            # The disagreeing case: the entry carries a readable tag and is
            # refused anyway, so the frozen `expected_tag` is None.
            assert case.expected_tag is None, case.case_id
            assert arriving is not None and arriving is not entry.tag, case.case_id

    # AND LICENSING IS THE TYPE CHECK, not a comparison against c_k tau_A: a
    # `general` entry is admissible input and is NEVER licensed, which is the
    # fail-closed direction (Thm. thm:gates). It is asked only of an entry V6
    # admits -- gate (G3)(a) is a condition on an EMITTED declaration, and a
    # refused entry never reaches one.
    licensed = case.v6_passes and entry.tag is RhsTag.HOMOGENEOUS
    assert licensed is case.licensed, case.case_id


def test_the_tag_cases_cover_both_types_and_both_licensing_verdicts() -> None:
    """Neither axis is degenerate, or the tuple would prove only one branch."""
    assert {case.expected_tag for case in RHS_TAG_CASES} >= {
        "homogeneous",
        "general",
        None,
    }
    assert {case.licensed for case in RHS_TAG_CASES} == {True, False}
    assert {case.v6_passes for case in RHS_TAG_CASES} == {True, False}
    # BOTH EMITTED SOURCE MODES, because the licensed class is stated per mode.
    assert {case.source_mode for case in RHS_TAG_CASES} == {"trusted", "untrusted"}
    # NOTHING IN THE TUPLE IS A NUMBER. That is the whole content of 0.3.0's
    # design decision 4 -- "LICENSING IS THEREFORE A TYPE CHECK ON THE TAG, AND
    # IT COMPARES NO NUMBERS" -- so it is asserted of the frozen data itself.
    for case in RHS_TAG_CASES:
        assert not isinstance(case.expected_tag, (int, float, F))
        assert case.expected_tag in {"homogeneous", "general", None}


def test_an_entry_whose_tag_field_disagrees_with_its_type_is_refused_by_v6() -> None:
    """The frozen ``TAG-trusted-tag-disagrees-with-type`` case, through V6.

    Def. ``def:validator`` V6: where an arriving entry carries an explicit tag
    field, "V6 compares that field with the type of the datum it names and A
    DISAGREEMENT IS A REFUSAL ... the tag is NEVER TAKEN ON A SUPPLIER'S WORD
    AGAINST THE OBJECT THE ENTRY HOLDS". The entry below declares ``general``
    and holds a real scalar. Its tag is still read off the DATUM -- so
    ``ConstraintEntry.tag`` is ``homogeneous``, not ``None`` and not
    ``general`` -- and V6 is what refuses it, which is the division of labour
    the frozen ``expected_tag = None`` records.
    """
    case = next(
        c for c in RHS_TAG_CASES if c.case_id == "TAG-trusted-tag-disagrees-with-type"
    )
    assert case.v6_passes is False
    assert case.expected_tag is None

    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert result.declaration is not None
    sector_map = result.declaration.sectors
    entry = ConstraintEntry(
        operator=BlockOperator.of(sector_map, [identity(2)]),
        relation=Relation.LE,
        rhs=F(1, 4),
        arriving_tag=RhsTag.GENERAL,
    )
    # THE TAG IS THE TYPE, so it is `homogeneous` here whatever the field says.
    assert entry.tag is RhsTag.HOMOGENEOUS
    assert entry.arriving_tag is RhsTag.GENERAL

    from dataclasses import replace

    mistagged = replace(result.declaration, constraint_list=(entry,))
    outcome = check_v6(mistagged)
    assert outcome.passed is False
    assert outcome.check == "V6"
    # AND THE AGREEING PRESENTATION OF THE SAME DATUM PASSES, so the refusal is
    # the disagreement and not the presence of a tag field.
    agreeing = replace(entry, arriving_tag=RhsTag.HOMOGENEOUS)
    assert check_v6(replace(result.declaration, constraint_list=(agreeing,))).passed


# ---------------------------------------------------------------------------
#  (d) SECTOR_MAP_COMPARISON_CASES -- V1's four-component comparison
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", SECTOR_MAP_COMPARISON_CASES, ids=lambda c: c.case_id)
def test_the_frozen_sector_map_comparisons_hold_against_check_v1(
    case: SectorMapComparisonCase,
) -> None:
    """Check V1, on the two declaration slots that carry a ``Q``-operator.

    Def. ``def:validator`` V1: "The families compared are EXACTLY THE
    Q-OPERATOR FAMILIES of Eq. eq:declaration ... the emitted Bob family
    ``bob_povm``, ``{F_v}`` ... AND EACH CONSTRAINT ENTRY of ``CList``. Those
    two slots are THE WHOLE of Eq. eq:declaration that carries a Q-operator, so
    THE LIST IS EXHAUSTIVE BY CONSTRUCTION RATHER THAN BY ENUMERATION." The
    comparison "is COMBINATORIAL -- it compares LABELS AND INTEGERS, NEVER
    MATRIX ENTRIES", which is why nothing below reads an entry.
    """
    from dataclasses import replace

    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert result.declaration is not None
    declaration = result.declaration

    if not case.refuses:
        # The two non-refusing cases: the declaration's own map, unmodified.
        # One of them (`MAP-physical-receiver-not-compared`) is a case about a
        # family V1 compares NOTHING of -- "the PHYSICAL receiver POVM is not a
        # slot of the declaration at all" -- so `compared_by` is None and there
        # is no comparison to drive; what it pins is the SCOPE, asserted below.
        assert case.refusal_reason is None, case.case_id
        assert case.disagreeing_component is None, case.case_id
        assert check_v1(declaration).passed is True, case.case_id
        return

    if case.compared_by == "V1":
        # A DISAGREEING CONSTRAINT ENTRY, built against a DIFFERENT map. Only
        # the combinatorial components differ -- the identifiers and their
        # order -- and the arrays are the same size, so nothing but the map can
        # be what V1 sees. "It compares LABELS AND INTEGERS, NEVER MATRIX
        # ENTRIES."
        assert case.refusal_reason == "sector_map_mismatch", case.case_id
        other_map = SectorStructure(
            labels=("s1",), dims=(2,), block_kind=band_a_block_kind()
        )
        entry = ConstraintEntry(
            operator=BlockOperator.of(other_map, [identity(2)]),
            relation=Relation.LE,
            rhs=F(1),
        )
        mismatched = replace(declaration, constraint_list=(entry,))
        outcome = check_v1(mismatched)
        assert outcome.passed is False, case.case_id
        assert outcome.refusal is not None, case.case_id
        assert str(outcome.refusal.reason) == case.refusal_reason, case.case_id
        return

    # THE WITNESS CASE, WHICH V1 DOES NOT SEE. A supplied omega^* is not a slot
    # of Eq. eq:declaration, so its map is compared at V7 BRANCH (c) instead --
    # "that being the one place a witness's map is compared" -- and the refusal
    # there is V7's own `no_feasibility_witness` and NOT `sector_map_mismatch`.
    # The two reasons staying distinct is the whole content of this case.
    assert case.compared_by == "V7 branch (c)", case.case_id
    assert case.refusal_reason == "no_feasibility_witness", case.case_id
    # Branch (c) is reached only where CList is non-empty AND the default
    # candidate of Eq. eq:witness-empty fails, so the fixture supplies an
    # unsatisfiable entry to get there: tr[(1 (x) 1_Q) omega] <= -1 holds of no
    # normalized state.
    unsatisfiable = ConstraintEntry(
        operator=BlockOperator.of(declaration.sectors, [identity(2)]),
        relation=Relation.LE,
        rhs=F(-1),
    )
    constrained = replace(declaration, constraint_list=(unsatisfiable,))
    permuted = SectorStructure(
        labels=("s1",), dims=(2,), block_kind=band_a_block_kind()
    )
    witness = JointBlockOperator.of(
        permuted, declaration.alice_dim, [scale(F(1, 4), identity(4))]
    )
    outcome, _ = check_v7(constrained, witness)
    assert outcome.passed is False, case.case_id
    assert outcome.refusal is not None, case.case_id
    assert str(outcome.refusal.reason) == case.refusal_reason, case.case_id
    # THE TWO REASONS STAY DISTINCT, which is what this case is for: a witness
    # whose map disagrees is `no_feasibility_witness` and never
    # `sector_map_mismatch`, that string belonging to V1's slots alone.
    assert str(outcome.refusal.reason) != "sector_map_mismatch", case.case_id
    # AND V1 IS UNTOUCHED BY IT: a witness is not a slot of Eq. eq:declaration,
    # so the declaration itself still passes V1.
    assert check_v1(declaration).passed is True, case.case_id


def test_v1_compares_exactly_the_two_q_operator_slots_and_no_wider_list() -> None:
    """The frozen scope, asserted of the tuple rather than trusted.

    Def. ``def:validator`` V1 names the compared families BY MACHINE KEY
    "because at a non-trivial chain TWO DIFFERENT FAMILIES COULD ANSWER TO 'THE
    RECEIVER POVM'", and the list is ``bob_povm`` and each constraint entry --
    "THE WHOLE of Eq. eq:declaration that carries a Q-operator, so THE LIST IS
    EXHAUSTIVE BY CONSTRUCTION RATHER THAN BY ENUMERATION". The other two frozen
    cases are about sites V1 does NOT reach.
    """
    by_site: dict[str | None, set[str]] = {}
    for case in SECTOR_MAP_COMPARISON_CASES:
        by_site.setdefault(case.compared_by, set()).add(case.compared_object)

    # V1's two slots, and no third.
    v1_slots = by_site["V1"]
    assert any("bob_povm" in name for name in v1_slots)
    assert any("CList" in name or "O^_k" in name for name in v1_slots)
    assert len(v1_slots) == 2

    # A SUPPLIED WITNESS IS COMPARED SOMEWHERE ELSE, and the physical receiver
    # POVM is compared NOWHERE -- it is not a slot of the declaration. If either
    # distinction ever collapses, this is where it shows.
    assert any("omega" in name for name in by_site["V7 branch (c)"])
    assert any("F^ph" in name for name in by_site[None])
    assert set(by_site) == {"V1", "V7 branch (c)", None}


# ---------------------------------------------------------------------------
#  (f) DECLARED_ORDER_CASES -- which order, and whether the choice is free
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", DECLARED_ORDER_CASES, ids=lambda c: c.case_id)
def test_the_frozen_declared_orders_hold_against_the_compilation_map(
    case: DeclaredOrderCase,
) -> None:
    """Def. ``def:compile``'s binding rules, and the one alphabet ``idx`` misses.

    Every case in this tuple is BINDING -- the compiler has no free bijection at
    any of these four sites -- so the assertion that matters is which of them
    ``idx`` indexes. ``T_pub`` and a matrix's row order are not among the nine.
    """
    assert case.binding is True, case.case_id
    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert result.declaration is not None
    index_map = result.declaration.label_index_map
    assert index_map is not None

    if case.case_id == "ORDER-V-from-supplier":
        # THE SUPPLIER'S ORDER, taken as idx's component on V. The Band-A chain
        # declares its target POVM in the order below, and the emitted alphabet
        # IS that order rather than a re-sorting of it.
        assert result.declaration.bob_alphabet == ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")
        assert case.indexed_by_idx is True
        assert "V" in index_map.forward
        for position, label in enumerate(result.declaration.bob_alphabet):
            assert index_map.index_of("V", label) == position
    elif case.case_id == "ORDER-S-is-the-sector-map":
        # ONE ORDER ON THE SECTORS, and not a second choice: idx's component on
        # S is the sector map's own order, which the last clause of D(i)
        # requires and check V1 decides.
        assert case.indexed_by_idx is True
        sectors = result.declaration.sectors
        for position, label in enumerate(sectors.labels):
            assert index_map.index_of("S", label) == position
    elif case.case_id == "ORDER-T-pub-not-indexed-by-idx":
        # THE ONE DECLARED ALPHABET idx DOES NOT INDEX. An implementation "must
        # therefore NOT ROUTE THIS SUM THROUGH `label_index_map`", and the way
        # to make that checkable is that the map has no component to route it
        # through.
        assert case.indexed_by_idx is False
        assert "T_pub" not in index_map.forward
        assert "T_pub" not in INDEXED_ALPHABETS
    else:
        # A TRACE IS NOT INDEXED BY idx: "that map indexing ALPHABETS and not
        # the basis of a matrix on A or on Q_s".
        assert case.case_id == "ORDER-trace-is-the-row-order"
        assert case.indexed_by_idx is False


def test_idx_indexes_nine_alphabets_and_t_pub_is_not_one_of_them() -> None:
    """Def. ``def:compile``'s nine, against the two frozen cases that name them."""
    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert result.declaration is not None
    index_map = result.declaration.label_index_map
    assert index_map is not None
    assert len(INDEXED_ALPHABETS) == 9
    assert set(index_map.forward) == set(INDEXED_ALPHABETS)
    assert "T_pub" not in index_map.forward
    not_indexed = {
        case.case_id for case in DECLARED_ORDER_CASES if not case.indexed_by_idx
    }
    assert not_indexed == {
        "ORDER-T-pub-not-indexed-by-idx",
        "ORDER-trace-is-the-row-order",
    }


def test_a_supplier_declared_order_is_never_the_ground_of_a_refusal_here() -> None:
    """Def. ``def:compile``: no family is refused for an order it did not choose.

    In the contract's own words: "NO FAMILY IS REFUSED HERE FOR AN ORDERING ITS
    SUPPLIER NEVER CHOSE."

    The same four elements in a different declared order compile just as well:
    at the balanced weights every partial sum is a multiple of ``1/4`` in any
    order, so (S) holds either way and the reordering changes no verdict. What
    it DOES change is ``idx``, and the emitted alphabet follows the supplier.
    """
    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert result.refusal is None
    assert result.declaration is not None
    # The order the supplier declared is the order emitted, element for element.
    assert result.declaration.bob_alphabet == ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")


def test_a_malformed_weight_is_refused_before_any_order_question_arises() -> None:
    """The domain condition of Def. ``def:weighted``, decided BY SIGN.

    Recorded here because Section 2.3's enumeration lists it among the
    conditions the ``gate_report`` does NOT key per element -- "the domain
    condition ``q_t > 0`` on a declared weight, REFUSED BY ITS SIGN RATHER THAN
    MEASURED" -- so it must not become a summation question.
    """
    conditional = {
        "u0": matrix(((1, 0), (0, 0))),
        "u1": matrix(((0, 0), (0, 1))),
    }
    with pytest.raises(MalformedInputError, match="q_t > 0"):
        weighted_family(
            PublicChoices(
                party=Party.ALICE,
                choices=("t0", "t1"),
                weights={"t0": F(-1, 2), "t1": F(3, 2)},
                conditional_alphabets={"t0": ("u0", "u1"), "t1": ("u0", "u1")},
                conditional_elements={"t0": conditional, "t1": conditional},
            )
        )
