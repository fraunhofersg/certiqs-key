"""The admission surface against the FROZEN Group 11 entries.

``SUMMATION_CASES``, ``ALICE_POVM_EXACT_CASES`` and the five Group 11 oracle
entries were authored by a different implementer instance, before the code that
decides them existed. The part of the admission rule that this file reads
against the implementation is the sector-map comparison, the declared-order
summation condition, the two round-nowhere clauses on Alice's data and the
licensed-class type check.

EVERY ROW IS DECIDED AT EXACTLY 0 AND AT NO WINDOW, and the strongest form of
that is structural: THERE IS NO TOLERANCE ARGUMENT FOR A WINDOW TO ENTER BY
(spec/architecture.md 2.8, "Modules receive no tolerance to reason with"). Each
case runs once, because there is no second tolerance value to run it at.

There is no tolerance datum, no domain for one and no refusal about one:
``declared_tolerance_absent`` and
``declared_tolerance_out_of_domain`` are in
:data:`certiqs_key.meat_core.reasons.RETIRED_REFUSAL_REASONS`, and
:func:`test_the_tolerance_vocabulary_is_absent_from_the_code` asserts
that. THE FROZEN ENTRIES THEMSELVES ARE UNTOUCHED: the registry
still carries ``O-DECLARED-TOLERANCE-REQUIRED`` and ``RENAMED_REASON_1_0_0``,
and an oracle is never edited to match the code it tests (PRINCIPLES.md
section 2.3).
"""

from __future__ import annotations

from fractions import Fraction
from inspect import signature

import numpy as np
import pytest
from dummy_bundles import build_bundle
from registry import (
    ALICE_ORDER_COUNT,
    ALICE_POVM_EXACT_CASES,
    OPTOL_FAMILIES,
    REASON_VOCABULARY_1_0_0,
    RENAMED_REASON_1_0_0,
    SUMMATION_CASES,
    AlicePovmExactCase,
    SummationCase,
    oracle,
)
from toy_declarations import toy

from certiqs_key.domain.bundle import OperatorBundle
from certiqs_key.foundations.exact_admission import sum_rounds_nowhere
from certiqs_key.meat_core.declaration import admission
from certiqs_key.meat_core.declaration.admission import (
    AdmissionError,
    AdmissionRefusal,
    check_sector_map,
)
from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.meat_core.declaration.declaration import RhsTag
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.finitekey.keylength import licensed_class_check
from certiqs_key.meat_core.reasons import RETIRED_REFUSAL_REASONS

pytestmark = [pytest.mark.contract, pytest.mark.oracle]

# ===========================================================================
#  The absent tolerance datum.
# ===========================================================================


def test_the_tolerance_vocabulary_is_absent_from_the_code() -> None:
    """The datum, its domain and its two refusal strings are all absent.

    The frozen registry records a ``tau_num`` datum that was REQUIRED with no
    default (``O-DECLARED-TOLERANCE-REQUIRED``), whose domain was the half-open
    ``[0, 1)``, and a refusal respelled ``declared_tolerance_out_of_domain``
    (``RENAMED_REASON_1_0_0``). This module has no such datum, so none of those
    can be asserted here; what CAN be asserted, and is, is that neither
    spelling is reachable and that no entry point takes the argument.

    THE FROZEN ENTRIES ARE READ AND NOT EDITED. ``REASON_VOCABULARY_1_0_0``
    still lists both strings, because an oracle is never regenerated from the
    code it tests; what this test asserts is that this implementation spells
    NEITHER.
    """
    assert oracle("O-DECLARED-TOLERANCE-REQUIRED").kind == "fail-closed"
    old, new = RENAMED_REASON_1_0_0
    # The registry knows both spellings; this module has neither.
    assert new in REASON_VOCABULARY_1_0_0
    assert old not in REASON_VOCABULARY_1_0_0
    live = {str(member) for member in AdmissionRefusal}
    assert old not in live
    assert new not in live
    assert "declared_tolerance_absent" not in live
    for retired in ("declared_tolerance_absent", "declared_tolerance_out_of_domain"):
        assert retired in RETIRED_REFUSAL_REASONS
    # AND NO ENTRY POINT TAKES THE ARGUMENT, which is the structural half:
    # a window cannot enter a signature that has no parameter for it.
    assert not hasattr(admission, "check_declared_tolerance")
    assert not hasattr(admission, "DECLARED_TOLERANCE_DOMAIN")
    assert len(signature(declaration_from_bundle).parameters) == 1
    assert list(signature(admission.admit_declaration).parameters) == ["declaration"]


# ===========================================================================
#  O-BOB-POVM-SUMMATION-ROUNDS -- def:optol condition (S).
# ===========================================================================


@pytest.mark.parametrize("case", SUMMATION_CASES, ids=lambda c: c.case_id)
def test_o_bob_povm_summation_rounds_reproduces_each_frozen_verdict(
    case: SummationCase,
) -> None:
    """Condition (S) on each frozen family: the verdict AND the named index.

    "THE REFUSAL CARRIES THREE THINGS, and an implementation that emits the
    reason without them has not implemented the rule: the sector, THE OUTCOME
    INDEX AT WHICH THE FIRST INEXACT ADDITION OCCURRED, and the declared
    order." So the index is compared, not only the boolean.

    THE PAIR THAT MAKES THIS A DISCRIMINATOR is ``S-CONVERSE-2^-53`` beside
    ``S-EXACT-NEIGHBOUR``: "two families at operator-norm distance ``2^-53``,
    both with representable entries and ALL THREE DEFECTS READING 0, one
    admitted and one refused -- and the thing that separates them is not a
    defect at all but WHETHER AN ADDITION ROUNDED. An implementation that
    measures defects and does not verify the additions cannot tell them apart."
    """
    family = [np.array([[term]], dtype=np.float64) for term in case.terms]
    result = sum_rounds_nowhere(family)
    assert result.ok is (case.first_inexact_index is None)
    assert result.first_inexact_index == case.first_inexact_index
    # The frozen verdict and the frozen ADMISSION agree: (S) is what decides
    # these four, every one of their three defects being exactly zero.
    assert result.ok is case.admitted
    assert case.computed_completeness_defect == 0.0


@pytest.mark.parametrize("case", SUMMATION_CASES, ids=lambda c: c.case_id)
def test_condition_s_is_decided_at_exactly_zero_and_at_no_window(
    case: SummationCase,
) -> None:
    """The summation row is decided at exactly zero, and the check says so.

    THE CHECK TAKES NO TOLERANCE ARGUMENT AT ALL, which is the strongest form
    of "decided at no window": there is no parameter for one to enter by.
    """
    family = [np.array([[term]], dtype=np.float64) for term in case.terms]
    assert sum_rounds_nowhere(family).ok is case.admitted


def test_the_exact_totals_of_the_frozen_families_are_the_rationals_recorded() -> None:
    """The REAL sum, over the rationals, against the frozen numerator/denominator.

    This is the half ``Delta_cpl`` does not see. "``Delta_cpl = 0`` says the
    COMPUTED sum is the identity; it does NOT say that ``sum_v F_v = 1_Q``
    holds of the numbers, AND EVERY CONSUMER OF ``Delta_cpl`` IN THIS CONTRACT
    READS IT AS SAYING THE LATTER." The frozen exact totals are what the
    computed ones differ from, and re-deriving them over ``Fraction`` shares no
    step with the binary64 emulation the check performs.
    """
    for case in SUMMATION_CASES:
        exact = sum((Fraction(term) for term in case.terms), Fraction(0))
        numerator, denominator = case.exact_total
        assert exact == Fraction(numerator, denominator), case.case_id
        # And a family whose exact sum is NOT one is exactly the hazard: its
        # computed sum reads as the identity while the real one does not.
        if exact != 1:
            assert not case.admitted, case.case_id


# ===========================================================================
#  O-SECTOR-MAP-DISAGREEMENT -- def:optol condition (T).
# ===========================================================================


def test_o_sector_map_disagreement_is_the_only_failure_the_form_admits() -> None:
    """(T) is a TYPE rule at 1.0.0, and its one failure has a spelled reason.

    "A declared operator arrives as A LIST OF SECTOR BLOCKS PLUS THE SECTOR
    MAP, so an off-block entry is ABSENT FROM THE DATUM rather than small in
    it: nothing can write one, NOTHING VERIFIES THAT NONE WAS WRITTEN, and no
    ``d_Q x d_Q`` matrix is assembled in order to be checked." What a consumer
    compares is the map -- block kind, identifiers, ordering -- "and a
    disagreement is a refusal with a machine-readable reason, WHICH IS THE ONLY
    FAILURE MODE THE REPRESENTATION ADMITS". The string is NEW at 1.0.0.
    """
    assert oracle("O-SECTOR-MAP-DISAGREEMENT").kind == "fail-closed"
    assert "sector_map_disagreement" in REASON_VOCABULARY_1_0_0

    # Agreement in all three components passes.
    check_sector_map(
        ["s0", "s1"],
        ["s0", "s1"],
        "test",
        declared_kind="proof_sector",
        consumer_kind="proof_sector",
    )
    # Each component alone is enough to refuse: identifiers, ORDERING, kind.
    for declared, consumer, kinds in (
        (["s0", "s2"], ["s0", "s1"], ("proof_sector", "proof_sector")),
        (["s1", "s0"], ["s0", "s1"], ("proof_sector", "proof_sector")),
        (["s0", "s1"], ["s0", "s1"], ("photon_number", "proof_sector")),
    ):
        with pytest.raises(AdmissionError) as refusal:
            check_sector_map(
                declared,
                consumer,
                "test",
                declared_kind=kinds[0],
                consumer_kind=kinds[1],
            )
        assert str(refusal.value.reason) == "sector_map_disagreement"


def test_condition_t_is_decided_before_the_other_four() -> None:
    """(T) FIRST, which is why ``exactly_admissible`` states only the other four.

    Section 2.2's ``tolerance_report`` row "says so and draws the consequence":
    (T) "is not among ``exactly_admissible``'s conjuncts BECAUSE IT IS DECIDED
    BEFORE ANY OF THEM and a disagreement refuses the run outright, so that
    boolean is emitted only on runs where (T) holds and states the remaining
    FOUR of the five conditions".

    A missing block kind is refused by the RULE that owns (T) and not by a
    ``TypeError``, which is what makes the refusal legible to a producer.
    """
    with pytest.raises(AdmissionError) as refusal:
        check_sector_map(
            ["s0"], ["s0"], "test", declared_kind=None, consumer_kind="proof_sector"
        )
    assert str(refusal.value.reason) == "sector_map_disagreement"
    # A AdmissionError IS a DeclarationError: the run is refused and no
    # result is produced, and what the subclass adds is the machine-readable
    # reason rather than a different outcome.
    assert isinstance(refusal.value, DeclarationError)


# ===========================================================================
#  O-GENERAL-TAG-NOT-LICENSED -- def:homog as amended, Section 2.1 part (i).
# ===========================================================================


def test_o_general_tag_not_licensed_reads_the_declared_tag() -> None:
    """TOY-7: ``general``-tagged, admitted as input, and NEVER LICENSED.

    "A ``general`` entry remains admissible input -- every structural and
    numerical claim below is proved for it -- but IT IS NEVER LICENSED, so a
    list containing one carries no key-length claim, WHICH IS THE FAIL-CLOSED
    DIRECTION."

    AT 1.0.0 THE MECHANISM IS A TYPE CHECK AND NOT A MEASUREMENT. At 0.5.0
    part (i) asked whether ``Theta_1 = c tau_A``, a numerical test TOY-7 fails
    because "``c = 2`` from the first diagonal entry and ``c = 1`` from the
    second". At 1.0.0 it "asks WHICH FORM THE ENTRY DECLARES AND COMPARES NO
    NUMBERS", so the verdict cannot move with the tolerance -- which is what
    running it at both ends asserts.
    """
    entry = oracle("O-GENERAL-TAG-NOT-LICENSED")
    assert entry.toy_id == "TOY-7"
    declaration = declaration_from_bundle(build_bundle(toy("TOY-7")))
    assert declaration.alice_dim == 2  # so part (i) is not vacuous (rem:cgate)
    assert declaration.is_trusted_source
    (constraint,) = declaration.constraint_list
    assert constraint.rhs_tag is RhsTag.GENERAL
    verdict = licensed_class_check(declaration)
    assert verdict.licensed is False
    assert verdict.vacuous is False


def test_the_licensed_class_reads_the_declared_tag_never_the_bound_type() -> None:
    """def:homog: "the form is part of the DATUM rather than a property measured".

    Section 2.1: part (i) "is a TYPE CHECK ON THE DECLARED TAG and compares no
    numbers". So the tag a consumer reads is the one the producer DECLARED, and
    ``domain/manifest.py`` says the same of the format: it "does not invent one,
    and IT DOES NOT READ ONE OFF ``bound``, because the tag is a DECLARED datum
    and a format-supplied one would be a code default deciding a
    security-relevant predicate ... on nobody's authority".

    THE UNSAFE DIRECTION IS A ``general``-DECLARED ENTRY CARRYING A SCALAR
    BOUND. Reading the tag off the bound's type calls it ``homogeneous`` and
    LICENSES a key length on an entry def:homog says "is NEVER licensed". Both
    mismatched pairs are refused here, at admission, as the malformed
    declarations they are -- which is the fail-closed answer and is stronger
    than reading the tag and declining the licence.
    """
    for declared_tag, bound, expected in (
        # general + scalar: the UNSAFE pair, read as `homogeneous` by a
        # type-inferring consumer and licensed.
        ("general", 0.5, "carries a scalar"),
        # homogeneous + operator: the converse, always refused.
        ("homogeneous", None, "carries an operator"),
    ):
        bundle = _edited_toy7(constraint_rhs_tag=declared_tag, bound=bound)
        with pytest.raises(DeclarationError) as refusal:
            declaration_from_bundle(bundle)
        assert "def:homog" in str(refusal.value)
        assert expected in str(refusal.value)


def test_a_tag_outside_the_two_declared_forms_is_refused_and_never_defaulted() -> None:
    """A third tag is refused, and NOT mapped onto the fail-closed one.

    def:homog fixes exactly two forms. A consumer that read an unknown tag as
    ``general`` -- on the grounds that ``general`` is the safe value -- would
    still be deciding which security-relevant class a producer meant, which
    Section 2.1 forbids in the same breath as it forbids reading the tag off
    ``bound``.
    """
    bundle = _edited_toy7(constraint_rhs_tag="homogeneous-ish", bound=None)
    with pytest.raises(DeclarationError) as refusal:
        declaration_from_bundle(bundle)
    assert "neither `homogeneous` nor `general`" in str(refusal.value)


# ===========================================================================
#  O-ALICE-EXACT-ORDER -- Section 2.6's alice_povm_exact row.
# ===========================================================================


@pytest.mark.parametrize("case", ALICE_POVM_EXACT_CASES, ids=lambda c: c.case_id)
def test_o_alice_exact_order_reproduces_each_frozen_verdict(
    case: AlicePovmExactCase,
) -> None:
    """The BB84 Alice POVM at three basis biases, in the declared order.

    The three cases separate the clause's two faces. ``p_Z = 1/2`` is admitted
    and dyadic; ``p_Z = 0.9`` is REFUSED and "the family IS A GENUINE POVM --
    its real sum is exactly the identity", the DISCLOSED COST; ``p_Z = 0.1`` is
    refused and "the family IS NOT A POVM -- its real sum is ``1 + 2^-55``
    while its computed sum is exactly the identity, SO ALL THREE DEFECTS READ
    ZERO", the hazard the clause exists for.

    The diagonal partial sums and the index of the first inexact addition are
    compared, not just the verdict, because "the refusal carries the outcome
    index at which the first inexact addition occurred".
    """
    family = [np.array([[value]], dtype=np.float64) for value in _diagonal(case)]
    result = sum_rounds_nowhere(family)
    assert result.ok is case.admitted
    assert result.first_inexact_index == case.first_inexact_index
    # THE COMPUTED SUM IS THE IDENTITY IN EVERY CASE, which is the point: the
    # three defects read zero on all three families and cannot separate them.
    # ``declared_order_sum`` IS the accumulation eq:declorder describes -- left
    # to right, entrywise, no re-ordering, no re-association -- so the frozen
    # boolean is asserted against the module's own sum rather than against a
    # sum this file forms (the round-nowhere row's own test is where this
    # function is exercised).
    total = admission.declared_order_sum(family)
    assert (float(np.real(total[0, 0])) == 1.0) is case.computed_sum_is_identity
    assert case.computed_sum_is_identity is True


def test_the_order_dependence_of_the_alice_clause_is_the_frozen_one() -> None:
    """The verdict at ``p_Z = 0.9`` DEPENDS ON THE ORDER; at ``0.1`` it does not.

    "Of the 24 orders of this four-element family, 20 round somewhere and 4
    round nowhere -- the four that add the two X elements FIRST, smallest terms
    first", while at ``p_Z = 0.1`` "all 24 orders round somewhere, so no choice
    of order admits this family". That is why Section 2.6 requires the order to
    be one "this module FIXES AND RECORDS" and why interface.yaml records it as
    OC-5: it is not a free choice, and "a run-B implementation must not decide
    it by the accident of a dict iteration order".

    The counts are re-derived here over all 24 permutations, by a route sharing
    no step with the frozen record.
    """
    from itertools import permutations

    assert ALICE_ORDER_COUNT == 24
    for case in ALICE_POVM_EXACT_CASES:
        elements = _alice_elements(case)
        clean = 0
        for order in permutations(range(4)):
            family = [elements[index] for index in order]
            clean += int(sum_rounds_nowhere(family).ok)
        assert clean == case.orders_that_round_nowhere, case.case_id
    # And the module's own order is FIXED AND RECORDED, which is the half the
    # counts make non-ceremonial.
    from certiqs_key.meat_core.declaration.admission import ALICE_SUMMATION_ORDER

    assert "no re-ordering and no re-association" in ALICE_SUMMATION_ORDER


def test_the_alice_cases_separate_the_cost_from_the_hazard() -> None:
    """The three cases the registry exists to separate, and the exact totals.

    THREE CASES AND THEY ARE THREE DIFFERENT THINGS: an ADMISSION on dyadic
    data; a REFUSAL of a genuine POVM, which is the round-nowhere clause's
    DISCLOSED COST and is ORDER-DEPENDENT; and a REFUSAL of a family whose
    computed sum is the identity while its real sum is not, which is the HAZARD
    the clause exists for and is order-INDEPENDENT. The three defects read zero
    on all three and cannot tell them apart.
    """
    identifiers = [case.case_id for case in ALICE_POVM_EXACT_CASES]
    assert len(identifiers) == len(set(identifiers))
    for case in ALICE_POVM_EXACT_CASES:
        assert len(case.derivation.strip()) > 200, case.case_id
        # THE REAL SUM, over the rationals, against the frozen pair. This is the
        # half no defect sees: the computed sum is the identity in every case.
        exact = sum((Fraction(value) for value in _diagonal(case)), Fraction(0))
        assert (exact.numerator, exact.denominator) == case.exact_diagonal_total, (
            case.case_id
        )

    by_id = {case.case_id: case for case in ALICE_POVM_EXACT_CASES}
    # THE COST: a genuine POVM -- its REAL sum is exactly the identity --
    # refused, and refused only under SOME orders.
    cost = by_id["AE-PZ-0.9"]
    assert cost.exact_diagonal_total == (1, 1)
    assert cost.admitted is False
    assert 0 < cost.orders_that_round_nowhere < ALICE_ORDER_COUNT
    # THE HAZARD: computed sum the identity, real sum 1 + 2^-55, every defect
    # reading zero -- and NO order admits it.
    hazard = by_id["AE-PZ-0.1"]
    assert hazard.computed_sum_is_identity is True
    assert Fraction(*hazard.exact_diagonal_total) - 1 == Fraction(1, 2**55)
    assert hazard.orders_that_round_nowhere == 0
    # THE CONTROL: dyadic data, admitted in every order.
    control = by_id["AE-PZ-HALF"]
    assert control.admitted is True
    assert control.orders_that_round_nowhere == ALICE_ORDER_COUNT


# ===========================================================================
#  Helpers.
# ===========================================================================


def _alice_elements(case: AlicePovmExactCase) -> tuple[np.ndarray, ...]:
    """Return the FOUR 2x2 declared elements, in the declared order.

    ``M_Z0 = p_Z |0><0|``, ``M_Z1 = p_Z |1><1|``, ``M_X0 = p_X |+><+|``,
    ``M_X1 = p_X |-><-|``. The whole element and not one entry: the
    round-nowhere clause is ENTRYWISE over the family, so an addition that is
    exact on the diagonal and rounds off it still fails, and the frozen
    order counts are over the elements.
    """
    p_z = case.p_z
    half = (1.0 - p_z) / 2.0
    return (
        np.array([[p_z, 0.0], [0.0, 0.0]], dtype=np.float64),
        np.array([[0.0, 0.0], [0.0, p_z]], dtype=np.float64),
        np.array([[half, half], [half, half]], dtype=np.float64),
        np.array([[half, -half], [-half, half]], dtype=np.float64),
    )


def _diagonal(case: AlicePovmExactCase) -> tuple[float, ...]:
    """Return the four ``(0, 0)`` entries whose partial sums the case freezes.

    ``M_Z0 = p_Z |0><0|``, ``M_Z1 = p_Z |1><1|``, ``M_X0 = p_X |+><+|``,
    ``M_X1 = p_X |-><-|``: on the ``(0, 0)`` entry those are ``p_Z``, ``0``,
    ``p_X/2``, ``p_X/2``. Derived from the declared elements rather than read
    off the frozen partial sums, so that the two agree by computation.
    """
    p_z = case.p_z
    p_x = 1.0 - p_z
    diagonal = (p_z, 0.0, p_x / 2.0, p_x / 2.0)
    # The frozen partial sums are what those four produce in the declared order.
    running = 0.0
    partials = []
    for value in diagonal:
        running = running + value
        partials.append(running)
    assert tuple(partials) == case.diagonal_partial_sums, case.case_id
    return diagonal


def _edited_toy7(*, constraint_rhs_tag: str, bound: float | None) -> OperatorBundle:
    """Return TOY-7's bundle with its one constraint entry re-declared.

    The frozen builder emits the manifest as plain data before parsing it, so
    the edit is made on the DECLARATION as a producer would write it and the
    result is then parsed and validated by the format exactly as any other
    bundle is. Nothing frozen is modified: ``bundle_documents`` is called
    afresh and the dictionary it returns is this test's.

    The format itself constrains ``constraint_rhs_tag`` to the two tags
    (``schemas/proof-instance/operator-bundle.schema.json``), so an unknown one
    is fed past ``parse_manifest``'s pydantic model, which types the field as a
    plain string -- which is precisely why the CONSUMER must refuse it rather
    than trust the wire.
    """
    from dummy_bundles import bundle_documents

    from certiqs_key.domain.bundle import parse_manifest

    manifest, arrays = bundle_documents(toy("TOY-7"))
    (entry,) = manifest["payload"]["declaration"]["constraint_list"]
    entry["constraint_rhs_tag"] = constraint_rhs_tag
    if bound is not None:
        entry["bound"] = bound
    return OperatorBundle(manifest=parse_manifest(manifest), arrays=arrays)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_frozen_zero_tolerance_verdicts_are_what_the_exact_admission_decides() -> (
    None
):
    """``OPTOL_FAMILIES.exactly_admissible``, against the code that decides it.

    A STATEMENT ABOUT THIS MODULE. The frozen field is "(T) AND all three
    defects zero", which is equivalent to the ``{F_v}`` clauses of
    ``def:admissible-declaration`` (iii) -- and that equivalence is exactly
    the predicate :func:`admit_bob_povm_exact` decides, so the eleven
    hand-derived families are its oracle, decided at exactly zero. Two of
    them carry a defect of ``7.28e-12``, far inside any window a tolerance
    datum would plausibly carry, and both are refused.

    ``OPTOL-BLOCK`` IS EXCLUDED AND THAT IS THE POINT OF THE SECTOR MAP: its
    off-block entries are absent from a declared datum
    (spec/architecture.md 2.9), so it cannot be presented to this rule at all,
    and its refusal belongs to :func:`check_sector_map`, which this file tests
    separately.
    """
    checked = 0
    for family in OPTOL_FAMILIES:
        if not family.block_diagonal:
            continue
        checked += 1
        sectors = tuple(f"s{index}" for index in range(len(family.sector_dims)))
        blocks: dict[str, dict[str, np.ndarray]] = {}
        for index, element in enumerate(family.elements):
            array = np.array(
                [[complex(entry) for entry in row] for row in element],
                dtype=np.complex128,
            )
            per_sector: dict[str, np.ndarray] = {}
            start = 0
            for sector, dim in zip(sectors, family.sector_dims, strict=True):
                per_sector[sector] = np.ascontiguousarray(
                    array[start : start + dim, start : start + dim]
                )
                start += dim
            blocks[f"v{index}"] = per_sector
        if family.exactly_admissible:
            record = admission.admit_bob_povm_exact(blocks, sectors)
            assert record.exactly_admissible is True, family.family_id
            continue
        with pytest.raises(AdmissionError) as refusal:
            admission.admit_bob_povm_exact(blocks, sectors)
        assert refusal.value.predicate is not None, family.family_id
    assert checked == len(OPTOL_FAMILIES) - 1
