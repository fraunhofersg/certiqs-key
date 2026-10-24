"""The registry is well-formed, admissible, and internally consistent.

Three things this pins.

1. **Traceability.** Every claim a registry entry names resolves to a claim of
   this repository. See EIGHTEEN TESTS REMOVED below: the traceability itself
   is re-established in ``test_meat_core_registry_interface.py``, against the
   claim files and the ``interface.yaml`` beside them.
2. **Admissibility.** No expected value here comes from MATLAB,
   OpenQKDSecurity, CVX, MOSEK or Julia: every oracle reproduces from a clean
   checkout without them.
3. **The freeze.** Every entry carries a derivation, and every alpha-dependent
   entry's frozen decimal table agrees with its closed form. The table guards a
   refactor or a typo; the DERIVATION, not the table, is authoritative.

And four more added as the contract grew.

4. **The declared operator tolerance.** Every frozen defect is non-negative and
   equal to the operator norm the case states; every family's
   ``exactly_admissible`` is true exactly when all three defects vanish; the
   boundary pairs differ in exactly one datum. THE APPARATUS THE CASES WERE
   AUTHORED AGAINST IS RETIRED and the
   cases are NOT edited: they still say what they said, and what changed is
   which of them this repository's code can be held to. The cross-check against
   ``reference.defects`` is a WITNESS to the
   hand derivations recorded with each family -- the derivation stays
   authoritative.
5. **The hand-off invariant.** Every object the amendment marks
   in ``SUPERSEDED_BY_0_5_0`` names a contract site, a reason and a replacement
   that resolves; and no file that has moved past the amendment asserts a
   marked object without naming the supersession list. The scan may only
   SHRINK, never grow, and a pair is discharged by a file's deletion or by the
   file being deliberately absent (:data:`DELIBERATELY_ABSENT_FILES`).
6. **The first-order rung.** The bracket's closed form reproduces its frozen
   tables exactly; it is strictly decreasing and strictly negative on TOY-1,
   and tight at the constrained optimum of TOY-5 and strictly below it
   elsewhere; the first-order key lengths are the key-length expression with
   ``max{0, h_lb}`` and nothing else.
7. **The admission surface.** Every frozen summation verdict is the binary64
   arithmetic it records, checked against ``Fraction``; the Alice cases
   separate a refused genuine POVM from a refused non-POVM.

EIGHTEEN TESTS WERE REMOVED AT THE MEAT-CORE MOVE, and one reason covers all
eighteen: THEY READ A SINGLE INTERFACE TRANSCRIPTION
AND A ``contract.tex`` PINNED BY CONTENT HASH. Neither document exists in this
repository and neither will -- the contract is one file per claim, assembled
for reading, and git plus human review is the ledger, with no second one
(PRINCIPLES.md sections 5 and 2.5). The removed tests, by what they asked:

* the document's own bookkeeping -- its ``contract_version``, its
  ``symbols_md_version``, its ``max_attainable_tier``, its content hash, its
  count of ``open`` claims, its list of settled change requests. NOT
  RE-ESTABLISHABLE AND NOT REPLACED: this repository has no such fields, and
  the facts they stood for are computed rather than transcribed
  (``python -m harness.check_claims --module meat-core --status``);
* the surfaces the retired apparatus occupied -- the tolerance rows, the
  certificate rows, the forced-downgrade reason. RE-ESTABLISHED AS THEIR
  RETIREMENT in ``test_meat_core_registry_interface.py``, which asserts that
  each is named as retired on both sides rather than merely absent;
* the traceability, the ledger, the reason vocabulary, the declared
  thresholds, the withdrawal vocabulary, the ladder and the recorded
  parameters. RE-ESTABLISHED, one test per group, in the same file.

THE FROZEN VALUES ARE UNTOUCHED. Not one byte of ``registry.py`` moved at the
meat-core move: an oracle is never regenerated from the code it tests
(PRINCIPLES.md section 2.3), and an expected value that looks wrong is a
finding rather than a correction.
"""

from __future__ import annotations

import math
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, TypedDict

import pytest
import reference
import yaml
from registry import (
    ALPHA_GRID,
    AMENDMENT_SPEC_VERSION_MARKER,
    CERTIFICATE_SUPERSESSION_LINE,
    FIRST_ORDER_KEY_LENGTH_CASES,
    FO_TOY1_TABLE,
    FO_TOY5_TABLE,
    INADMISSIBLE_SOURCES,
    KEY_LENGTH_CASES,
    KINDS,
    MATHEMATICAL_SPEC_VERSION_0_5_0,
    NOT_SUPERSEDED_BY_0_5_0,
    O_ALPHA_LIMIT_TABLE,
    OPTOL_ADMISSION_CASES,
    OPTOL_ASSURANCE_REASON,
    OPTOL_BRANCH_OUTPUTS,
    OPTOL_DOMAIN,
    OPTOL_DOMAIN_CASES,
    OPTOL_FAMILIES,
    OPTOL_NOBOUND_CASES,
    OPTOL_OUTPUT_KEYS,
    OPTOL_REACH_STATEMENTS,
    OPTOL_REFUSAL_REASONS,
    OPTOL_REPORT_CASES,
    OPTOL_SUBCONSTANT,
    OPTOL_SUBCONSTANT_TOLERANCE,
    OPTOL_WITNESS_CASES,
    OPTOL_WITNESS_GUARANTEE_THRESHOLD,
    ORACLES,
    PENDING_RETIREMENT_AT_RUN_B,
    RUN_B_SCANNED_FILES,
    SUMMATION_CASES,
    SUPERSEDED_BY_0_5_0,
    SUPERSEDED_BY_SCOPE_1_0_0,
    SUPERSEDED_SPEC_VERSION,
    _fo_bracket_one_sector,
    _freeze,
    _hlow_constrained,
    is_superseded,
    oracle,
    pending_row_superseded,
    supersession,
)
from toy_declarations import ALL_TOYS, ALL_TOYS_0_4_0, CERTIFICATE_TOYS

REPO_ROOT = Path(__file__).resolve().parents[2]
INTERFACE_PATH = (
    REPO_ROOT / "docs" / "mathematical-contracts" / "meat-core" / "interface.yaml"
)
CONTRACT_VERSION = "1.0.0"

#: THE MEAT-CORE FILE SET INSIDE ``tests/oracles/``, named rather than globbed.
#: This directory holds five modules' registries and their
#: interface tests, so the scans below do not glob it, and another module's
#: file is not this one's to hold to this module's rules.
MEAT_CORE_ORACLE_FILES: tuple[str, ...] = (
    "registry.py",
    "reference.py",
    "toy_declarations.py",
    "toy_evaluation.py",
    "dummy_bundles.py",
    "test_registry_integrity.py",
    "test_alpha_limit.py",
    "test_analytic_limits.py",
    "test_dummy_bundles.py",
    "test_fail_closed.py",
    "test_key_length.py",
    "test_sector_classification.py",
    "test_source_modes.py",
    "test_structural_identities.py",
    "test_meat_core_registry_interface.py",
)

#: TEST FILES THAT ARE DELIBERATELY ABSENT. Their subject is the
#: declared-tolerance apparatus, which is retired (the reason is kept), and
#: nothing is left for them to test. What survives of their subject is carried,
#: in four parts, by tests/golden/test_admission_surface_against_registry.py:
#: the sector-map comparison, the declared-order summation condition, the two
#: Alice rows, and the eleven frozen ``OPTOL_FAMILIES``, whose
#: ``exactly_admissible`` is the predicate the exact admission decides.
#:
#: A pair of the hand-off invariant naming either file is discharged by the
#: file's absence, the same way a deletion discharges one. The list may only
#: SHRINK: a file that returns leaves it, and its pairs are then discharged the
#: ordinary way, by the file existing and naming the supersession list.
DELIBERATELY_ABSENT_FILES: frozenset[str] = frozenset(
    {
        "tests/unit/test_meat_operator_tolerance.py",
        "tests/golden/test_operator_tolerance_against_registry.py",
    }
)

#: The four claims contract 1.0.0 REMOVES. They are not reused and they are not
#: retracted as mathematics -- contract Section 1.3 -- so every registry entry
#: naming one is MARKED rather than deleted.
CLAIMS_DELETED_AT_1_0_0: frozenset[str] = frozenset({"C13", "C18", "C19", "C20"})


#: The tolerance the Group 9 cross-checks use against ``reference``. The frozen
#: values are exact rationals and the reproduction path is an eigendecomposition,
#: so the residue is the numerical route's and not the derivation's. ``abs``
#: dominates for the sub-1e-10 discriminator values, where ``rel`` would be
#: meaninglessly tight.
class _ApproxTolerance(TypedDict):
    """The two keyword arguments the Group 9 cross-checks pass to `approx`."""

    rel: float
    abs: float


OPTOL_APPROX: _ApproxTolerance = {"rel": 1e-12, "abs": 1e-15}


def _interface() -> dict[str, Any]:
    with INTERFACE_PATH.open(encoding="utf-8") as handle:
        document: dict[str, Any] = yaml.safe_load(handle)
    return document


@pytest.mark.contract
def test_the_registry_covers_the_claims_this_run_is_scoped_to() -> None:
    """The coverage list of the oracle set, checked against what is pinned."""
    covered = {claim for entry in ORACLES for claim in entry.claims}
    assert {
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9a",
        "C9b",
        "C10",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        # New at 0.4.0: the certificate chain that closes C13.
        "C18",
        "C19",
        "C20",
        # New at 0.5.0: the declared operator tolerance.
        "C21",
    } <= covered


@pytest.mark.contract
def test_no_entry_is_a_choi_parametrization_or_a_gradient() -> None:
    """The C11/C12 exclusion, narrowed at 0.3.0 rather than dropped.

    The exclusion exists to forbid an oracle that *is* the implementation: a
    Choi parametrization routine or a gradient routine written in the test
    tree would be checking the solver against itself. It does not forbid a
    frozen scalar witness that discriminates the contract's rule from a wrong
    one -- which is the opposite, and is exactly what the Round-1
    implementation-verification findings F-01-01 and F-01-02 turned on. So the
    two entries that name C11 and C12 are enumerated by ID here, and any third
    one is a defect this test catches.
    """
    naming = {
        claim: {entry.oracle_id for entry in ORACLES if claim in entry.claims}
        for claim in ("C11", "C12")
    }
    assert naming["C11"] == {"O-CHOI-BASIS-INVARIANCE"}
    assert naming["C12"] == {"O-GRADIENT-FACE-SPLIT"}
    # Neither carries a callable that could stand in for the solver: their
    # closed forms are functions of alpha alone.
    for oracle_id in {"O-CHOI-BASIS-INVARIANCE", "O-GRADIENT-FACE-SPLIT"}:
        entry = next(e for e in ORACLES if e.oracle_id == oracle_id)
        assert entry.closed_form is not None
        assert entry.closed_form(1.5) == pytest.approx(
            dict(entry.frozen_values)[1.5], rel=1e-15
        )


@pytest.mark.contract
def test_every_oracle_entry_is_well_formed() -> None:
    """Each entry has a unique id, a known kind, and a derivation worth reading."""
    identifiers = [entry.oracle_id for entry in ORACLES]
    assert len(identifiers) == len(set(identifiers))
    known_toys = {toy.toy_id for toy in ALL_TOYS_0_4_0}
    for entry in ORACLES:
        assert entry.kind in KINDS, entry.oracle_id
        assert len(entry.derivation.strip()) > 200, entry.oracle_id
        assert entry.subject.strip(), entry.oracle_id
        if entry.toy_id is not None:
            assert entry.toy_id in known_toys, entry.oracle_id
        # 0.5.0 adds ONE optional field, and it takes exactly two values.
        assert entry.superseded_by in {None, "0.5.0"}, entry.oracle_id


@pytest.mark.contract
def test_no_entry_derives_from_an_inadmissible_source() -> None:
    """ADR-0003: no MATLAB, OpenQKD, CVX, MOSEK or Julia value is an oracle."""
    for entry in ORACLES:
        text = f"{entry.subject}\n{entry.derivation}"
        for source in INADMISSIBLE_SOURCES:
            assert source.lower() not in text.lower(), (entry.oracle_id, source)
    for toy in ALL_TOYS_0_4_0:
        text = f"{toy.summary}\n{toy.derivation}"
        for source in INADMISSIBLE_SOURCES:
            assert source.lower() not in text.lower(), (toy.toy_id, source)


@pytest.mark.contract
def test_frozen_tables_agree_with_their_closed_forms() -> None:
    """The decimal table is the closed form evaluated, to the last digit."""
    checked = 0
    for entry in ORACLES:
        if entry.closed_form is None:
            assert entry.frozen_values == (), entry.oracle_id
            continue
        assert entry.frozen_values, entry.oracle_id
        assert tuple(a for a, _ in entry.frozen_values) == ALPHA_GRID
        assert _freeze(entry.closed_form) == entry.frozen_values, entry.oracle_id
        for alpha, expected in entry.frozen_values:
            assert entry.closed_form(alpha) == pytest.approx(expected, rel=1e-15)
        checked += 1
    assert checked >= 3


@pytest.mark.contract
def test_every_alpha_in_the_registry_lies_in_the_declared_domain() -> None:
    """req:key-length-alpha-domain: (1, 2) for key length; (1, inf) for the rest."""
    for alpha in ALPHA_GRID:
        assert 1.0 < alpha < 2.0
    for case in KEY_LENGTH_CASES:
        assert 1.0 < case.alpha < 2.0, case.case_id


@pytest.mark.contract
def test_key_length_cases_are_well_formed() -> None:
    """Each frozen key-length case carries its arithmetic and a legal parameter set."""
    identifiers = [case.case_id for case in KEY_LENGTH_CASES]
    assert len(identifiers) == len(set(identifiers))
    for case in KEY_LENGTH_CASES:
        assert case.rounds >= 1
        assert case.lambda_ec >= 0
        assert 0.0 < case.eps_pa <= 1.0
        assert 0.0 < case.eps_ev <= 1.0
        assert case.expected >= 0
        assert len(case.arithmetic.strip()) > 80, case.case_id


@pytest.mark.contract
def test_c16_table_entries_resolve_to_real_toys() -> None:
    """Every alpha -> 1+ entry names a toy, a limit, a p_0 and a Feas_1 witness."""
    known = {toy.toy_id for toy in ALL_TOYS}
    for toy_id, h1, limit, p0, witness in O_ALPHA_LIMIT_TABLE:
        assert toy_id in known
        assert h1 == pytest.approx(limit)
        assert p0 > 0.0
        assert witness.strip()


@pytest.mark.contract
def test_registry_never_cites_the_corpus() -> None:
    """PRINCIPLES.md section 8: the corpus is evidence, never authority.

    The needle is assembled at run time so that this file is checked by the same
    rule as every other file it scans, rather than exempting itself.

    THE SCAN IS THE MEAT-CORE FILE SET AND NOT THE WHOLE DIRECTORY.
    ``tests/oracles/`` holds five modules' registries, and a sibling's interface
    test QUOTES PRINCIPLES.md section 8 in order to state the rule, which is not
    a citation of the corpus but a statement of the prohibition. Other modules'
    oracle files are their batches' and are deliberately outside this scan,
    exactly as they are outside the hand-off invariant below.
    """
    needles = ("".join(("cont", "ext", "/")), "".join(("cont", "ext", "\\")))
    directory = Path(__file__).parent
    for name in MEAT_CORE_ORACLE_FILES:
        text = (directory / name).read_text(encoding="utf-8")
        for needle in needles:
            assert needle not in text, (name, needle)


@pytest.mark.contract
def test_the_certificate_toys_are_registered_and_new() -> None:
    """The two 0.4.0 toys exist, are one per source mode, and are additions."""
    assert {t.toy_id for t in CERTIFICATE_TOYS} == {
        "CERT-TOY-3REL-T",
        "CERT-TOY-3REL-UN",
    }
    assert len(ALL_TOYS_0_4_0) == len(ALL_TOYS) + 7 + len(CERTIFICATE_TOYS)
    for declaration in CERTIFICATE_TOYS:
        relations = {entry.relation for entry in declaration.constraint_list}
        assert relations == {"succeq", "preceq", "eq"}, declaration.toy_id


# ===========================================================================
#  Group 9 -- the declared operator tolerance (C21), new at contract 0.5.0
# ===========================================================================


def _family(family_id: str) -> Any:
    """Return the frozen family with this id."""
    for item in OPTOL_FAMILIES:
        if item.family_id == family_id:
            return item
    raise KeyError(family_id)


def _elements(family: Any) -> list[list[list[complex]]]:
    """Return the family's literal operators as nested lists for NumPy."""
    return [[list(row) for row in element] for element in family.elements]


@pytest.mark.contract
def test_every_frozen_defect_is_the_norm_the_case_states() -> None:
    """Eq. eq:defects, recomputed from the literal operators of each family.

    The hand derivation recorded with each family is AUTHORITATIVE; this is a
    witness to it, along the reproduction path of ``reference.py``. All three
    defects are non-negative by construction and the check asserts that too.
    """
    for family in OPTOL_FAMILIES:
        elements = _elements(family)
        herm, pos, cpl = reference.defects(elements)
        assert herm >= 0.0 and pos >= 0.0 and cpl >= 0.0, family.family_id
        assert herm == pytest.approx(family.delta_herm, **OPTOL_APPROX), (
            family.family_id
        )
        assert pos == pytest.approx(family.delta_pos, **OPTOL_APPROX), family.family_id
        assert cpl == pytest.approx(family.delta_cpl, **OPTOL_APPROX), family.family_id
        # And the same for the two PER-OUTCOME vectors the report carries.
        assert reference.hermiticity_defects(elements) == pytest.approx(
            family.per_outcome_hermiticity, **OPTOL_APPROX
        ), family.family_id
        assert reference.negative_parts(elements) == pytest.approx(
            family.per_outcome_negative, **OPTOL_APPROX
        ), family.family_id


@pytest.mark.contract
def test_the_per_outcome_vectors_attain_their_maxima() -> None:
    """Section 2.2: the per-outcome quantities "that ATTAIN the first two"."""
    for family in OPTOL_FAMILIES:
        assert len(family.per_outcome_hermiticity) == len(family.elements)
        assert len(family.per_outcome_negative) == len(family.elements)
        assert all(value >= 0.0 for value in family.per_outcome_hermiticity)
        assert all(value >= 0.0 for value in family.per_outcome_negative)
        assert max(family.per_outcome_hermiticity) == family.delta_herm, (
            family.family_id
        )
        assert max(family.per_outcome_negative) == family.delta_pos, family.family_id
    # Both SHAPES the vector can take are frozen, which is why it is a vector
    # and not an attaining index: OPTOL-HERM's maximum is attained by BOTH
    # outcomes and OPTOL-NEG's by ONE.
    assert _family("OPTOL-HERM").per_outcome_hermiticity == (0.25, 0.25)
    assert _family("OPTOL-NEG").per_outcome_negative == (0.125, 0.0)


@pytest.mark.contract
def test_exactly_admissible_is_block_diagonal_with_three_zero_defects() -> None:
    """Definition def:optol; Lemma lem:optol-zero.

    ``exactly_admissible`` is (T) together with all three defects zero, and
    OPTOL-BLOCK is the case that shows the two halves are independent: a
    genuine POVM with three zero defects that is still not exactly admissible,
    because its declared sector decomposition is not the one it is diagonal in.
    """
    for family in OPTOL_FAMILIES:
        zero = (
            family.delta_herm == 0.0
            and family.delta_pos == 0.0
            and family.delta_cpl == 0.0
        )
        assert family.exactly_admissible == (zero and family.block_diagonal), (
            family.family_id
        )
        # The declared sector dims sum to the operator dimension.
        assert sum(family.sector_dims) == len(family.elements[0]), family.family_id
    block = _family("OPTOL-BLOCK")
    assert (block.delta_herm, block.delta_pos, block.delta_cpl) == (0.0, 0.0, 0.0)
    assert block.block_diagonal is False
    assert block.exactly_admissible is False
    # Its off-block defect is real and is never compared against eps_dec.
    for element in _elements(block):
        assert reference.block_diagonality_defect(
            element, block.sector_dims
        ) == pytest.approx(0.25, **OPTOL_APPROX)
    # Exactly one family is exactly admissible, and it is the POVM of TOY-1.
    admissible = [f.family_id for f in OPTOL_FAMILIES if f.exactly_admissible]
    assert admissible == ["OPTOL-EXACT"]


@pytest.mark.contract
def test_the_admission_cases_agree_with_their_families() -> None:
    """Definition def:optol applied to each frozen (family, tolerance) pair."""
    identifiers = [case.case_id for case in OPTOL_ADMISSION_CASES]
    assert len(identifiers) == len(set(identifiers))
    known = {family.family_id for family in OPTOL_FAMILIES}
    for case in OPTOL_ADMISSION_CASES:
        assert case.family_id in known, case.case_id
        assert len(case.derivation.strip()) > 120, case.case_id
        family = _family(case.family_id)
        effective = 0.0 if case.declared is None else case.declared
        assert OPTOL_DOMAIN[0] <= effective < OPTOL_DOMAIN[1], case.case_id
        # THE RULE, recomputed: (T) exactly, then the three inequalities, which
        # are NOT strict.
        expected = family.block_diagonal and all(
            defect <= effective
            for defect in (family.delta_herm, family.delta_pos, family.delta_cpl)
        )
        assert case.admitted == expected, case.case_id
        # The branch is the theorem's, and only an ADMITTED pair has one.
        if not case.admitted:
            assert case.branch is None, case.case_id
            assert case.proceeds is False, case.case_id
        elif family.exactly_admissible:
            assert case.branch == "i", case.case_id
            assert case.proceeds is True, case.case_id
            assert case.reason is None, case.case_id
        elif family.delta_herm > 0.0 or family.delta_pos > 0.0:
            assert case.branch == "ii", case.case_id
            assert case.proceeds is False, case.case_id
            assert case.reason == "bob_povm_not_evaluable", case.case_id
        else:
            assert case.branch == "iii", case.case_id
            assert case.proceeds is True, case.case_id
            assert case.reason == OPTOL_ASSURANCE_REASON, case.case_id
        # A REFUSAL names the failed part, and it names the RIGHT one.
        if not case.admitted and family.block_diagonal:
            assert case.reason in OPTOL_REFUSAL_REASONS, case.case_id
            failed = {
                "bob_povm_hermiticity_defect": family.delta_herm,
                "bob_povm_negative_part": family.delta_pos,
                "bob_povm_completeness_defect": family.delta_cpl,
            }[case.reason]
            assert failed > effective, case.case_id
    # Every branch of the theorem is exercised, and so is every refusal reason
    # a (family, tolerance) pair can produce.
    assert {case.branch for case in OPTOL_ADMISSION_CASES} == {None, "i", "ii", "iii"}
    reasons = {case.reason for case in OPTOL_ADMISSION_CASES}
    assert {
        "bob_povm_hermiticity_defect",
        "bob_povm_negative_part",
        "bob_povm_completeness_defect",
        "bob_povm_not_evaluable",
        OPTOL_ASSURANCE_REASON,
    } <= reasons


@pytest.mark.contract
def test_condition_t_is_refused_at_every_tolerance_and_carries_no_new_reason() -> None:
    """Definition def:optol (T); Remark rem:optol-reach (a), rem:optol-interface (2).

    "Block-diagonality, decided EXACTLY and never within a tolerance", and its
    failure "refused as a malformed declaration, AT EVERY eps_dec". Section 1.1
    counts the amendment's additions as five refusal reasons, none of them
    naming block-diagonality, so a (T) refusal carries NONE of the six.
    """
    cases = [case for case in OPTOL_ADMISSION_CASES if case.family_id == "OPTOL-BLOCK"]
    assert len(cases) == 3
    tolerances = {case.declared for case in cases}
    # Absent, mid-domain and the largest value the domain admits.
    assert tolerances == {None, 0.5, 0.999}
    for case in cases:
        assert case.admitted is False, case.case_id
        assert case.proceeds is False, case.case_id
        assert case.branch is None, case.case_id
        assert case.reason is None, case.case_id
    # And no other case in the group refuses without a reason: a `None` reason
    # on a refusal means (T) and nothing else.
    for case in OPTOL_ADMISSION_CASES:
        if not case.admitted and case.reason is None:
            assert _family(case.family_id).block_diagonal is False, case.case_id


@pytest.mark.contract
def test_the_boundary_pairs_differ_in_exactly_one_datum() -> None:
    """Each of (H), (P), (C) admitted at Delta = eps_dec and refused above it.

    The inequality of Definition ``def:optol`` is NOT strict, so equality
    ADMITS. An implementation writing ``Delta < eps_dec`` passes every "below"
    case and fails every boundary case, which is what the pairing is for.
    """
    pairs = (
        ("AD-HERM-boundary", "AD-HERM-below", "bob_povm_hermiticity_defect"),
        ("AD-2DH-boundary", "AD-2DH-below", "bob_povm_hermiticity_defect"),
        ("AD-NEG-boundary", "AD-NEG-below", "bob_povm_negative_part"),
        ("AD-2DN-boundary", "AD-2DN-below", "bob_povm_negative_part"),
        ("AD-COMP-boundary", "AD-COMP-below", "bob_povm_completeness_defect"),
        ("AD-2DC-boundary", "AD-2DC-below", "bob_povm_completeness_defect"),
    )
    by_id = {case.case_id: case for case in OPTOL_ADMISSION_CASES}
    for admitted_id, refused_id, reason in pairs:
        admitted, refused = by_id[admitted_id], by_id[refused_id]
        # EXACTLY ONE DATUM DIFFERS: the declared tolerance.
        assert admitted.family_id == refused.family_id, admitted_id
        assert admitted.declared != refused.declared, admitted_id
        assert admitted.admitted is True and refused.admitted is False
        assert refused.reason == reason, refused_id
        family = _family(admitted.family_id)
        defect = {
            "bob_povm_hermiticity_defect": family.delta_herm,
            "bob_povm_negative_part": family.delta_pos,
            "bob_povm_completeness_defect": family.delta_cpl,
        }[reason]
        # The boundary case sits AT the defect; the refused one strictly below.
        assert admitted.declared == defect, admitted_id
        assert refused.declared is not None and refused.declared < defect, refused_id
    # All three conditions have a pair, on both family shapes.
    assert len(pairs) == 6


@pytest.mark.contract
def test_admission_is_not_evaluation() -> None:
    """Theorem thm:optol (ii): admitted by the rule, and still refused.

    Of the three boundary cases only (C)'s run PROCEEDS. This is the fact the
    freeze exists to separate: ``admitted`` and ``proceeds`` are two different
    columns, and the contract says so -- "It is ADMISSION, NOT EVALUATION, that
    eps_dec governs here."
    """
    by_id = {case.case_id: case for case in OPTOL_ADMISSION_CASES}
    for case_id in (
        "AD-HERM-boundary",
        "AD-NEG-boundary",
        "AD-2DH-boundary",
        "AD-2DN-boundary",
        "AD-SUBP-above",
    ):
        case = by_id[case_id]
        assert case.admitted is True, case_id
        assert case.proceeds is False, case_id
        assert case.reason == "bob_povm_not_evaluable", case_id
        assert case.branch == "ii", case_id
    # And the completeness boundary is the one that proceeds.
    comp = by_id["AD-COMP-boundary"]
    assert comp.admitted is True and comp.proceeds is True
    assert comp.branch == "iii"


@pytest.mark.contract
def test_the_declared_domain_is_half_open_and_absent_means_zero() -> None:
    """Section 2.1 and Remark rem:optol-interface (1): eps_dec in [0, 1)."""
    assert OPTOL_DOMAIN == (0.0, 1.0)
    identifiers = [case.case_id for case in OPTOL_DOMAIN_CASES]
    assert len(identifiers) == len(set(identifiers))
    for case in OPTOL_DOMAIN_CASES:
        assert len(case.derivation.strip()) > 120, case.case_id
        if case.declared is None:
            # ABSENT MEANS eps_dec = 0, and it is in domain.
            assert case.in_domain is True and case.effective == 0.0, case.case_id
            assert case.reason is None, case.case_id
            continue
        expected = OPTOL_DOMAIN[0] <= case.declared < OPTOL_DOMAIN[1]
        assert case.in_domain == expected, case.case_id
        if expected:
            assert case.effective == case.declared, case.case_id
            assert case.reason is None, case.case_id
        else:
            assert case.effective is None, case.case_id
            assert case.reason == "operator_tolerance_out_of_domain", case.case_id
    values = {case.declared for case in OPTOL_DOMAIN_CASES}
    # Both endpoints are exercised, and the top one is EXCLUDED.
    assert 0.0 in values and 1.0 in values and None in values
    assert next(c for c in OPTOL_DOMAIN_CASES if c.declared == 0.0).in_domain is True
    assert next(c for c in OPTOL_DOMAIN_CASES if c.declared == 1.0).in_domain is False
    # ABSENT AND DECLARED-ZERO DECIDE IDENTICALLY, on every family that carries
    # both cases.
    by_family: dict[str, dict[object, Any]] = {}
    for admission in OPTOL_ADMISSION_CASES:
        by_family.setdefault(admission.family_id, {})[admission.declared] = admission
    checked = 0
    for cases in by_family.values():
        if None in cases and 0.0 in cases:
            absent, zero = cases[None], cases[0.0]
            assert absent.admitted == zero.admitted
            assert absent.reason == zero.reason
            assert absent.branch == zero.branch
            assert absent.proceeds == zero.proceeds
            checked += 1
    assert checked >= 2


@pytest.mark.contract
def test_the_branch_table_is_the_theorem() -> None:
    """Theorem thm:optol (i)-(iii) and Remark rem:optol-interface (3), (4)."""
    branches = {row.branch: row for row in OPTOL_BRANCH_OUTPUTS}
    assert set(branches) == {"i", "ii", "iii"}
    for row in OPTOL_BRANCH_OUTPUTS:
        assert len(row.derivation.strip()) > 200, row.branch
        # present and absent PARTITION the six output keys of Section 2.2.
        assert set(row.present) | set(row.absent) == set(OPTOL_OUTPUT_KEYS), row.branch
        assert not set(row.present) & set(row.absent), row.branch
        for key in row.present:
            assert key in OPTOL_OUTPUT_KEYS, (row.branch, key)

    # (i) the version-0.4.0 reading, verbatim: everything, both assurances,
    # both claims.
    first = branches["i"]
    assert first.absent == ()
    assert set(first.assurance) == {"estimate", "certified"}
    assert first.assurance_reason is None
    assert first.hcert_bounds_hlow is True
    assert first.hlow_bounds_hqkd is True
    assert first.key_length_claim is True

    # (ii) not evaluable: no result at all.
    second = branches["ii"]
    assert second.present == ()
    assert second.assurance == ()
    assert second.key_length_claim is False

    # (iii) exploration: everything but the key length, assurance FORCED.
    third = branches["iii"]
    assert third.absent == ("key_length",)
    assert third.assurance == ("estimate",)
    assert third.assurance_reason == OPTOL_ASSURANCE_REASON
    # AND NEITHER NUMBER BOUNDS ANYTHING THERE.
    assert third.hcert_bounds_hlow is False
    assert third.hlow_bounds_hqkd is False
    assert third.key_length_claim is False
    for key in (
        "h_low",
        "h_cert",
        "sector_report",
        "optimizer_certificate",
        "operator_tolerance_report",
    ):
        assert key in third.present

    # `certified` is reachable on branch (i) alone.
    assert [row.branch for row in OPTOL_BRANCH_OUTPUTS if "certified" in row.assurance]
    assert {
        row.branch for row in OPTOL_BRANCH_OUTPUTS if "certified" in row.assurance
    } == {"i"}


@pytest.mark.contract
def test_the_report_is_a_function_of_the_measured_defects() -> None:
    """Section 2.2 and Remark rem:optol-interface (5), field for field."""
    identifiers = [case.case_id for case in OPTOL_REPORT_CASES]
    assert len(identifiers) == len(set(identifiers))
    for case in OPTOL_REPORT_CASES:
        assert len(case.derivation.strip()) > 120, case.case_id
        family = _family(case.family_id)
        # The three defects and the two vectors are the FAMILY'S, not the
        # request's: the report measures, it does not echo the tolerance.
        assert case.delta_herm == family.delta_herm, case.case_id
        assert case.delta_pos == family.delta_pos, case.case_id
        assert case.delta_cpl == family.delta_cpl, case.case_id
        assert case.per_outcome_hermiticity == family.per_outcome_hermiticity
        assert case.per_outcome_negative == family.per_outcome_negative
        # exactly_admissible is "Delta_herm = Delta_pos = Delta_cpl = 0", and
        # key_length_claim EQUALS it.
        assert case.exactly_admissible == (
            case.delta_herm == 0.0 and case.delta_pos == 0.0 and case.delta_cpl == 0.0
        ), case.case_id
        assert case.key_length_claim == case.exactly_admissible, case.case_id
        # The declared tolerance is carried VERBATIM and is in domain when
        # present.
        if case.declared is not None:
            assert OPTOL_DOMAIN[0] <= case.declared < OPTOL_DOMAIN[1], case.case_id

    by_id = {case.case_id: case for case in OPTOL_REPORT_CASES}
    # "At eps_dec = 0 the report is (0, 0, 0, 0, true, true)".
    zero = by_id["REPORT-EXACT-absent"]
    assert (
        zero.declared,
        zero.delta_herm,
        zero.delta_pos,
        zero.delta_cpl,
        zero.exactly_admissible,
        zero.key_length_claim,
    ) == (None, 0.0, 0.0, 0.0, True, True)
    # THE CASE THAT CATCHES THE WRONG READING: a tolerance declared on data
    # that does not need it leaves BOTH booleans true.
    quarter = by_id["REPORT-EXACT-quarter"]
    assert quarter.declared == 0.25
    assert quarter.exactly_admissible is True and quarter.key_length_claim is True
    # AND THE CONVERSE: two small numbers that are not each other.
    small = by_id["REPORT-SUBC-above"]
    assert small.declared == OPTOL_SUBCONSTANT_TOLERANCE
    assert small.delta_cpl == OPTOL_SUBCONSTANT
    assert small.declared != small.delta_cpl
    assert small.exactly_admissible is False and small.key_length_claim is False


@pytest.mark.contract
def test_the_witness_cases_are_exactly_admissible_and_within_the_bound() -> None:
    """Lemma lem:nearpovm, forward and converse, on four frozen families."""
    identifiers = [case.case_id for case in OPTOL_WITNESS_CASES]
    assert len(identifiers) == len(set(identifiers))
    for case in OPTOL_WITNESS_CASES:
        assert len(case.derivation.strip()) > 200, case.case_id
        family = _family(case.family_id)
        # theta = Delta_cpl + |V| Delta_pos, and the lemma needs theta < 1.
        expected_theta = family.delta_cpl + len(family.elements) * family.delta_pos
        assert case.theta == pytest.approx(expected_theta, **OPTOL_APPROX), case.case_id
        assert case.theta < 1.0, case.case_id
        # eps_dec_star = Delta_herm/2 + Delta_pos + theta(1+theta)/(1-theta).
        expected_star = (
            0.5 * family.delta_herm
            + family.delta_pos
            + case.theta * (1.0 + case.theta) / (1.0 - case.theta)
        )
        assert case.eps_dec_star == pytest.approx(expected_star, **OPTOL_APPROX), (
            case.case_id
        )
        # THE WITNESS IS EXACTLY ADMISSIBLE: all three defects vanish on it.
        star = [[list(row) for row in element] for element in case.star_elements]
        herm, pos, cpl = reference.defects(star)
        assert herm == pytest.approx(0.0, **OPTOL_APPROX), case.case_id
        assert pos == pytest.approx(0.0, **OPTOL_APPROX), case.case_id
        assert cpl == pytest.approx(0.0, **OPTOL_APPROX), case.case_id
        # AND IT IS WITHIN THE BOUND the lemma states.
        elements = _elements(family)
        distances = [
            reference.operator_norm(
                [
                    [a - b for a, b in zip(row_a, row_b, strict=True)]
                    for row_a, row_b in zip(element, witness, strict=True)
                ]
            )
            for element, witness in zip(elements, star, strict=True)
        ]
        assert distances == pytest.approx(case.distances, **OPTOL_APPROX), case.case_id
        assert case.eta == pytest.approx(max(case.distances), **OPTOL_APPROX)
        assert case.eta <= case.eps_dec_star + 1e-15, case.case_id
        # THE CONVERSE, Eq. eq:nearpovm-conv, on the same eta.
        assert family.delta_herm <= 2.0 * case.eta + 1e-15, case.case_id
        assert family.delta_pos <= case.eta + 1e-15, case.case_id
        assert family.delta_cpl <= len(family.elements) * case.eta + 1e-15
        assert case.sufficient_tolerance == pytest.approx(
            max(2, len(family.elements)) * case.eta, **OPTOL_APPROX
        ), case.case_id
        # And that tolerance does suffice for admission.
        for defect in (family.delta_herm, family.delta_pos, family.delta_cpl):
            assert defect <= case.sufficient_tolerance + 1e-15, case.case_id

    by_id = {case.case_id: case for case in OPTOL_WITNESS_CASES}
    # BOTH HALVES ATTAINED on WIT-HERM: a bound that is never tight is a bound
    # no test can distinguish from a looser one.
    herm_case = by_id["WIT-HERM"]
    assert herm_case.eta == herm_case.eps_dec_star == 0.125
    assert _family("OPTOL-HERM").delta_herm == 2.0 * herm_case.eta
    # Its witness IS the exactly admissible family the registry already froze.
    assert herm_case.star_elements == _family("OPTOL-EXACT").elements
    # And the second converse bound is attained on WIT-NEG.
    assert _family("OPTOL-NEG").delta_pos == by_id["WIT-NEG"].eta
    # The guarantee threshold is (|V| + 1)^-1 and is NOT the domain endpoint.
    assert pytest.approx(1.0 / 3.0) == OPTOL_WITNESS_GUARANTEE_THRESHOLD
    assert OPTOL_DOMAIN[1] > OPTOL_WITNESS_GUARANTEE_THRESHOLD


@pytest.mark.contract
def test_the_nobound_cases_exhibit_the_gap_the_proposition_states() -> None:
    """Proposition prop:optol-nobound (i) and (ii), in either direction."""
    identifiers = [case.case_id for case in OPTOL_NOBOUND_CASES]
    assert len(identifiers) == len(set(identifiers))
    assert {case.part for case in OPTOL_NOBOUND_CASES} == {"i", "ii"}

    def hlow(g0: float, alpha: float) -> float:
        """Eq. eq:optol-instance, on the shared instance."""
        return (alpha / (alpha - 1.0)) * math.log2(1.0 / g0)

    for case in OPTOL_NOBOUND_CASES:
        assert len(case.derivation.strip()) > 200, case.case_id
        g0, g1 = case.declared
        assert g0 > 0.0 and g1 >= 0.0, case.case_id
        # The declared family's defects, on the one-dimensional instance.
        assert case.declared_defects[0] == 0.0, case.case_id
        assert case.declared_defects[1] == pytest.approx(
            max(0.0, -min(g0, g1)), **OPTOL_APPROX
        ), case.case_id
        assert case.declared_defects[2] == pytest.approx(
            abs(g0 + g1 - 1.0), **OPTOL_APPROX
        ), case.case_id
        # BOTH exhibited families are exact POVMs: non-negative, summing to 1.
        for family in (case.family_one, case.family_two):
            assert all(value >= 0.0 for value in family), case.case_id
            assert sum(family) == pytest.approx(1.0, **OPTOL_APPROX), case.case_id
        # ... and lie within the distance the case must respect.
        for family, distance in (
            (case.family_one, case.distance_one),
            (case.family_two, case.distance_two),
        ):
            computed = max(
                abs(a - b) for a, b in zip(family, case.declared, strict=True)
            )
            assert computed == pytest.approx(distance, **OPTOL_APPROX), case.case_id
            assert distance <= case.distance_bound + 1e-15, case.case_id
        # THE GAP, between the two values the case names, and that it
        # exceeds the prescribed bound at every alpha. WHICH PAIR is data:
        # the direction is the proposition's content, not a convention.
        first, second = case.gap_between
        assert {first, second} <= {"declared", "family_one", "family_two"}
        assert first != second, case.case_id
        values = {
            "declared": case.declared,
            "family_one": case.family_one,
            "family_two": case.family_two,
        }
        for alpha in ALPHA_GRID:
            gap = hlow(values[first][0], alpha) - hlow(values[second][0], alpha)
            assert gap == pytest.approx(case.gap_form(alpha), rel=1e-9), case.case_id
            assert gap > case.bound_b, (case.case_id, alpha)
        assert case.frozen_gap == _freeze(case.gap_form), case.case_id

    by_id = {case.case_id: case for case in OPTOL_NOBOUND_CASES}
    # PART (i): both families are EXACT POVMs, so the phenomenon is not caused
    # by the defects (Remark rem:optol-direction).
    for case_id in ("NB-i-eps-half-B3", "NB-i-eps-quarter-B1"):
        assert by_id[case_id].declared_defects == (0.0, 0.0, 0.0), case_id
    # PART (ii): the declared family is DEFECTIVE, admitted, and on branch
    # (iii) -- Delta_herm = Delta_pos = 0 < Delta_cpl.
    for case_id in ("NB-ii-c-half-B2", "NB-ii-reversed"):
        case = by_id[case_id]
        assert case.declared_defects[0] == 0.0 and case.declared_defects[1] == 0.0
        assert case.declared_defects[2] > 0.0, case_id
    # THE SIGN REVERSES at the same tolerance with the same two neighbours.
    forward, reversed_case = by_id["NB-ii-c-half-B2"], by_id["NB-ii-reversed"]
    assert forward.declared_defects == reversed_case.declared_defects
    assert forward.family_one == reversed_case.family_one
    assert forward.family_two == reversed_case.family_two
    assert forward.distance_bound == reversed_case.distance_bound
    assert forward.declared != reversed_case.declared
    # The two cases measure OPPOSITE pairs, which is the reversal itself.
    assert forward.gap_between == ("declared", "family_one")
    assert reversed_case.gap_between == ("family_two", "declared")
    for alpha in ALPHA_GRID:
        # The forward case's h_low lies ABOVE family_one's; the reversed one's
        # lies BELOW family_two's, by the same amount -- so no function of the
        # declared metadata, which is identical for the two, can be both.
        assert hlow(forward.declared[0], alpha) > hlow(forward.family_one[0], alpha)
        assert hlow(reversed_case.declared[0], alpha) < hlow(
            reversed_case.family_two[0], alpha
        )
        above = hlow(forward.declared[0], alpha) - hlow(forward.family_one[0], alpha)
        below = hlow(reversed_case.family_two[0], alpha) - hlow(
            reversed_case.declared[0], alpha
        )
        assert above == pytest.approx(below, rel=1e-12)
    # The instance's dimensions do not move with B: the two part-(i) cases
    # share every alphabet and differ only in epsilon and B.
    assert len(by_id["NB-i-eps-half-B3"].declared) == 2
    assert len(by_id["NB-i-eps-quarter-B1"].declared) == 2


@pytest.mark.contract
def test_the_undeclared_constant_discriminator() -> None:
    """A defect of order 1e-11 with no tolerance declared is a REFUSAL.

    Section 2.5: "ABSENT MEANS eps_dec = 0, and eps_dec = 0 MEANS EXACT AT
    EVERY SITE OF THIS CONTRACT; no default is fixed here or in any artifact
    derived from here." A validation path that decides a declared identity
    inside a constant absolute window has fixed an UNDECLARED default, and
    these two families are the pair it cannot pass.
    """
    # The perturbation is an exact power of two, of order 1e-11, and BELOW the
    # 1e-10 an undeclared window would use; the tolerance beside it is above.
    assert OPTOL_SUBCONSTANT == 2.0**-37
    assert 1e-12 < OPTOL_SUBCONSTANT < 1e-10
    assert OPTOL_SUBCONSTANT_TOLERANCE == 2.0**-33
    assert OPTOL_SUBCONSTANT_TOLERANCE > 1e-10 > OPTOL_SUBCONSTANT
    completeness = _family("OPTOL-SUBCONST-C")
    positivity = _family("OPTOL-SUBCONST-P")
    assert completeness.delta_cpl == OPTOL_SUBCONSTANT
    assert (completeness.delta_herm, completeness.delta_pos) == (0.0, 0.0)
    assert positivity.delta_pos == OPTOL_SUBCONSTANT
    assert (positivity.delta_herm, positivity.delta_cpl) == (0.0, 0.0)
    assert completeness.exactly_admissible is False
    assert positivity.exactly_admissible is False

    by_id = {case.case_id: case for case in OPTOL_ADMISSION_CASES}
    # WITH NO TOLERANCE DECLARED, both are REFUSED -- naming the failed part.
    assert by_id["AD-SUBC-absent"].admitted is False
    assert by_id["AD-SUBC-absent"].reason == "bob_povm_completeness_defect"
    assert by_id["AD-SUBC-zero"].reason == "bob_povm_completeness_defect"
    assert by_id["AD-SUBP-absent"].admitted is False
    assert by_id["AD-SUBP-absent"].reason == "bob_povm_negative_part"
    # AT A DECLARED TOLERANCE ABOVE THE DEFECT, each reaches the branch the
    # CONTRACT assigns -- and neither ever produces a key length.
    above = by_id["AD-SUBC-above"]
    assert above.declared == OPTOL_SUBCONSTANT_TOLERANCE
    assert above.admitted is True and above.branch == "iii" and above.proceeds is True
    assert above.reason == OPTOL_ASSURANCE_REASON
    boundary = by_id["AD-SUBC-boundary"]
    assert boundary.declared == OPTOL_SUBCONSTANT and boundary.branch == "iii"
    subp = by_id["AD-SUBP-above"]
    assert subp.declared == OPTOL_SUBCONSTANT_TOLERANCE
    assert subp.admitted is True and subp.proceeds is False
    assert subp.reason == "bob_povm_not_evaluable" and subp.branch == "ii"
    # NO DECLARED TOLERANCE IN THE DOMAIN MAKES THE POSITIVITY FAMILY
    # COMPUTABLE: every admitted pair on it lands on branch (ii).
    for case in OPTOL_ADMISSION_CASES:
        if case.family_id == "OPTOL-SUBCONST-P" and case.admitted:
            assert case.proceeds is False, case.case_id


@pytest.mark.contract
def test_the_reach_table_governs_three_identities_and_no_more() -> None:
    """Remark rem:optol-reach: (H), (P), (C) on bob_povm, and nothing else."""
    governed = [row for row in OPTOL_REACH_STATEMENTS if "governed by" in row[1]]
    assert len(governed) == 3
    assert [row[0] for row in governed] == [
        "bob_povm Hermiticity defect Delta_herm",
        "bob_povm negative part Delta_pos",
        "bob_povm completeness defect Delta_cpl",
    ]
    # Every other row is decided EXACTLY, at every declared value.
    for what, verdict, site in OPTOL_REACH_STATEMENTS:
        assert what.strip() and verdict.strip() and site.strip()
        if "governed by" not in verdict:
            assert "EXACT at every eps_dec" in verdict or "EXACT machine" in verdict, (
                what
            )
    # The three identities a validation path most easily widens are named, and
    # named as EXACT: the marginal's normalization, Alice's POVM, and the
    # acceptance set.
    text = "\n".join(row[0] for row in OPTOL_REACH_STATEMENTS)
    assert "tr tau_A = 1" in text
    assert "sum_x M_x = 1_A" in text
    assert "acceptance_set" in text
    assert len(OPTOL_REACH_STATEMENTS) == 11


@pytest.mark.contract
def test_the_supersession_list_is_well_formed() -> None:
    """Every mark names a site, a reason and a replacement, and resolves."""
    module = sys.modules["registry"]
    seen = [(entry.module, entry.name) for entry in SUPERSEDED_BY_0_5_0]
    assert len(set(seen)) == len(seen)
    for entry in SUPERSEDED_BY_0_5_0:
        assert entry.superseded_by == "0.5.0", entry.name
        assert entry.kind in {"superseded", "incomplete", "reframed"}, entry.name
        assert entry.contract_site.strip(), entry.name
        assert len(entry.reason) > 120, entry.name
        assert entry.table.strip() and entry.module.strip(), entry.name
        assert entry.scan_pattern.strip(), entry.name
        # Every replacement resolves in the registry, and is not itself marked.
        assert entry.replacement, entry.name
        for replacement in entry.replacement:
            assert _resolves(module, replacement), (entry.name, replacement)
            assert not is_superseded(replacement), (entry.name, replacement)
        # Where the mark names a registry object, that object exists and, where
        # it is an oracle entry, carries the mark IN PLACE.
        if entry.module == "registry" and entry.table == "ORACLES":
            marked = next(e for e in ORACLES if e.oracle_id == entry.name)
            assert marked.superseded_by == "0.5.0", entry.name
    # The helpers agree with the table, and an unmarked object is unmarked.
    for entry in SUPERSEDED_BY_0_5_0:
        assert is_superseded(entry.name)
        assert supersession(entry.name) is entry
    assert not is_superseded("O-ASSURANCE-ESTIMATE")
    assert supersession("O-ASSURANCE-ESTIMATE") is None
    # THE ENTRIES CARRYING A `superseded_by` FIELD ARE EXACTLY THE MARKED ONES.
    marked_in_place = {
        entry.oracle_id for entry in ORACLES if entry.superseded_by is not None
    }
    listed = {
        entry.name
        for entry in SUPERSEDED_BY_0_5_0
        if entry.module == "registry" and entry.table == "ORACLES"
    }
    assert marked_in_place == listed, (marked_in_place, listed)
    # The list is complete in BOTH directions.
    assert len(NOT_SUPERSEDED_BY_0_5_0) >= 8
    for what, why in NOT_SUPERSEDED_BY_0_5_0:
        assert what.strip() and len(why) > 60, what
    # THE SPEC PIN IS MARKED AS A VALUE, NOT AS AN IDENTIFIER, because three
    # files pin it under two different names; marking the string catches all
    # three and the scan shrinks by itself as each is retyped.
    pin = supersession("SPEC_VERSION_0_4_0")
    assert pin is not None
    assert pin.scan_pattern == SUPERSEDED_SPEC_VERSION == "meat-core@0.4.0"
    assert "dummy_bundles" in pin.module and "mode_bundles" in pin.module
    assert AMENDMENT_SPEC_VERSION_MARKER == MATHEMATICAL_SPEC_VERSION_0_5_0
    assert AMENDMENT_SPEC_VERSION_MARKER != SUPERSEDED_SPEC_VERSION


def _resolves(module: Any, name: str) -> bool:
    """Whether ``name`` is a module attribute or a case id inside one."""
    if hasattr(module, name):
        return True
    for attribute in dir(module):
        value = getattr(module, attribute)
        if not isinstance(value, tuple):
            continue
        for row in value:
            for field_name in ("case_id", "oracle_id", "family_id"):
                if getattr(row, field_name, None) == name:
                    return True
    return False


@pytest.mark.contract
def test_no_superseded_object_is_asserted_unmarked_by_a_run_b_file() -> None:
    """The hand-off invariant.

    A file that has moved to the amendment -- which it declares
    by naming the amendment's spec version, which
    :data:`AMENDMENT_SPEC_VERSION_MARKER` spells so that this docstring does not
    have to -- may not assert a marked pre-amendment object unless it names
    ``SUPERSEDED_BY_0_5_0`` itself. A file still pinned to the earlier version
    is pre-amendment; its references are the pending work the marking run
    recorded, and the scan may only SHRINK from that list, never grow.

    The scanned set is the meat-core file list BY NAME. The tree also holds the
    receiver, reductions, protocol-compiler and statistics suites, which belong
    to other batches and are none of this invariant's business.
    """
    marked = list(SUPERSEDED_BY_0_5_0)
    files = [REPO_ROOT / relative for relative in RUN_B_SCANNED_FILES]
    existing = [path for path in files if path.exists()]
    assert existing, "no run-B meat-core files found"
    found: set[tuple[str, str]] = set()
    for path in existing:
        source = path.read_text(encoding="utf-8")
        relative = path.relative_to(REPO_ROOT).as_posix()
        on_amendment = AMENDMENT_SPEC_VERSION_MARKER in source
        acknowledges = "SUPERSEDED_BY_0_5_0" in source or "is_superseded" in source
        for entry in marked:
            pattern = (
                r"(?<![A-Za-z0-9_@.\-])" + re.escape(entry.scan_pattern)
                if entry.scan_pattern.isidentifier()
                else re.escape(entry.scan_pattern)
            )
            if not re.search(pattern, source):
                continue
            found.add((relative, entry.name))
            if acknowledges:
                continue
            assert not on_amendment, (
                f"{relative} has moved to {AMENDMENT_SPEC_VERSION_MARKER} and still "
                f"asserts the superseded {entry.name!r} without naming "
                "SUPERSEDED_BY_0_5_0; retire or rewrite it"
            )
    pending = set(PENDING_RETIREMENT_AT_RUN_B)
    assert found <= pending, sorted(found - pending)
    # EVERY PENDING PAIR NAMES A MARKED OBJECT, and either a file that still
    # exists or one this band DELETED.
    #
    # A DELETED FILE DISCHARGES ITS PAIR AND DOES NOT REMOVE IT. The row stays
    # in the frozen tuple -- the two-instance freeze forbids a deletion inside a
    # frozen file even of an inventory row, because a row that is gone cannot be
    # read as having been disposed of deliberately -- and the disposal is
    # recorded BESIDE it, in PENDING_ROWS_SUPERSEDED_BY_SCOPE_1_0_0, with its
    # dated ground. So the invariant still SHRINKS and never grows: what changed
    # is that a pair may be discharged by a deletion as well as by a rewrite.
    for relative, name in PENDING_RETIREMENT_AT_RUN_B:
        assert is_superseded(name), name
        if pending_row_superseded(relative, name):
            assert not (REPO_ROOT / relative).exists(), (
                f"{relative} is marked superseded-by-scope because band B1 "
                "deleted it, and it is still on disk; a mark and a file cannot "
                "both stand"
            )
            continue
        # A DELIBERATELY ABSENT FILE DISCHARGES ITS PAIR THE SAME WAY A
        # DELETION DOES. Its pairs stay in the frozen tuple, because a row that
        # is gone cannot be read as having been disposed of deliberately, and
        # what discharges them is that the file is not here.
        if relative in DELIBERATELY_ABSENT_FILES:
            assert not (REPO_ROOT / relative).exists(), relative
            continue
        assert (REPO_ROOT / relative).exists(), relative
    # The scan reads only the meat-core file set, by name: the sibling modules'
    # suites belong to other bands and are deliberately outside it.
    for relative in RUN_B_SCANNED_FILES:
        for foreign in (
            "receiver_povm",
            "proof_reductions",
            "protocol_compiler",
            "statistics_acceptance",
            "reductions_",
        ):
            assert foreign not in relative, relative


@pytest.mark.contract
def test_the_oracle_files_never_import_the_implementation() -> None:
    """The 0.4.0 freeze's rule, and it still stands at 0.5.0.

    ``registry.py`` and ``reference.py`` are the frozen evidence and the
    reproduction path; neither may import ``certiqs_key``, or the oracle would be
    the implementation checked against itself. ``dummy_bundles.py`` is the one
    oracle file that legitimately imports ``certiqs_key.domain`` -- it SERIALIZES
    a toy into the shared bundle format, which is a format concern and not a
    mathematical one -- and it imports nothing from ``certiqs_key.meat_core``.
    """
    for name in ("registry.py", "reference.py", "toy_declarations.py"):
        source = (Path(__file__).parent / name).read_text(encoding="utf-8")
        assert "import certiqs_key" not in source, name
        assert "from certiqs_key" not in source, name
    bundles = (Path(__file__).parent / "dummy_bundles.py").read_text(encoding="utf-8")
    assert "from certiqs_key.domain.bundle import" in bundles
    assert "certiqs_key.meat_core" not in bundles


# ===========================================================================
#  Group 10 -- the first-order rung (C22), new at contract 1.0.0
# ===========================================================================


@pytest.mark.contract
def test_the_bracket_tables_are_the_closed_form_evaluated() -> None:
    """FO_TOY1_TABLE and FO_TOY5_TABLE are ``_fo_bracket_one_sector``, exactly.

    Not ``approx``: the tables were generated from the function as written and
    a last-ulp difference here would mean the function had been edited without
    the tables being regenerated, which is the one failure a frozen table
    exists to catch.
    """
    for weight, table in FO_TOY1_TABLE:
        assert tuple(alpha for alpha, _ in table) == ALPHA_GRID
        for alpha, value in table:
            assert _fo_bracket_one_sector(alpha, weight, 0.0) == value, (weight, alpha)
    for weight, table in FO_TOY5_TABLE:
        assert tuple(alpha for alpha, _ in table) == ALPHA_GRID
        for alpha, value in table:
            assert _fo_bracket_one_sector(alpha, weight, 0.5) == value, (weight, alpha)


@pytest.mark.contract
def test_the_unconstrained_bracket_is_strictly_negative_and_decreasing() -> None:
    """TOY-1: h_lb < 0 = h_low at every admissible iterate, and the sup is not met.

    Theorem ``thm:firstorder`` (ii) gives ``h_lb <= h_low``; on TOY-1 the
    inequality is STRICT at every weight the theorem admits, and the value 0 it
    approaches is unreachable because the only iterate attaining it -- w0 = 0 --
    fails (H-SUPP), the key-active branch operator being 0 there while
    dim W_chat0,s0 = 1. So a correct implementation reports a NEGATIVE h_lb on
    this declaration and clamps it to 0 for the key length.
    """
    entry = oracle("O-FO-BRACKET-UNCONSTRAINED")
    assert entry.closed_form is not None
    closed_form = entry.closed_form
    # The closed form is the maximum over the tabulated iterate set, i.e. the
    # smallest tabulated weight, because the bracket decreases in the weight.
    smallest = min(weight for weight, _ in FO_TOY1_TABLE)
    assert smallest == 0.125
    assert entry.frozen_values == next(
        table for weight, table in FO_TOY1_TABLE if weight == smallest
    )
    for alpha in ALPHA_GRID:
        values = [
            _fo_bracket_one_sector(alpha, weight, 0.0) for weight, _ in FO_TOY1_TABLE
        ]
        assert all(value < 0.0 for value in values), alpha
        # FO_TOY1_TABLE runs from the largest weight to the smallest, and the
        # bracket increases along it.
        assert all(values[i] < values[i + 1] for i in range(len(values) - 1)), alpha
        assert max(values) == closed_form(alpha)
    # The clamp reaches the key length and h_lb keeps the unclamped value.
    assert "max{0, h_lb} = 0" in entry.derivation
    assert "first_order_clamped" in entry.derivation


@pytest.mark.contract
def test_the_constrained_bracket_is_tight_at_the_optimum() -> None:
    """TOY-5: h_lb = h_low at w0 = 1/2 and strictly below it elsewhere.

    This is the only frozen case in which the first-order bound is TIGHT at a
    non-zero value, so it is the one that discriminates the contract's bracket
    from a bracket with the vertex at the wrong end of the interval -- which
    would return a number ABOVE h_low, violating the theorem in the unsafe
    direction.
    """
    entry = oracle("O-FO-BRACKET-CONSTRAINED")
    assert entry.closed_form is _hlow_constrained
    assert entry.frozen_values == oracle("O-HLOW-CONSTRAINED").frozen_values
    for alpha in ALPHA_GRID:
        tight = _hlow_constrained(alpha)
        # Tight at the constraint boundary: the correction term carries the
        # factor (w* - w) = 0 there, exactly, in binary64 as in the reals.
        assert _fo_bracket_one_sector(alpha, 0.5, 0.5) == pytest.approx(
            tight, rel=1e-14
        )
        # Strictly below at every tabulated suboptimal weight.
        for weight, table in FO_TOY5_TABLE:
            assert weight > 0.5
            assert dict(table)[alpha] < tight, (weight, alpha)
        # AND THE WRONG VERTEX WOULD BREAK THE THEOREM. Taking w0* = 1, the
        # maximizer of the linear form rather than its minimizer, puts the
        # bracket ABOVE h_low at every suboptimal iterate -- which is what the
        # sign computation of the one-sector reduction rules out.
        for weight, _ in FO_TOY5_TABLE:
            assert _fo_bracket_one_sector(alpha, weight, 1.0) > tight, (weight, alpha)


@pytest.mark.contract
def test_the_degenerate_brackets_equal_the_estimate() -> None:
    """A singleton feasible set and a constant gradient both give h_lb = h_low.

    TOY-3(m=2): the feasible set is one point, so both minimizations of
    Eq. ``eq:lmo`` are over one-point sets, both differences in Eq. ``eq:hlb``
    vanish, and the bracket IS the objective -- A-LMO is discharged on both
    sides rather than assumed on one.
    TOY-2: every pair is key-inert, so K = P and the objective is a function of
    the sector-weight SUM alone; its gradient has equal components, the linear
    form is constant on the simplex, and the bracket's linear term is zero at
    every vertex.
    """
    singleton = oracle("O-FO-BRACKET-SINGLETON")
    assert singleton.value == oracle("O-HLOW-FULLY-DEPHASED").value == 1.0
    assert singleton.toy_id == "TOY-3(m=2)"
    inert = oracle("O-FO-BRACKET-KEY-INERT")
    assert inert.value == oracle("O-HLOW-DETERMINISTIC").value == 0.0
    assert inert.toy_id == "TOY-2"
    # (H-SUPP) is VACUOUS on TOY-2 -- both sectors are constraint-active, so
    # the set of key-active sectors is empty -- and an implementation reading
    # it as a condition on ALL sectors withdraws h_lb here, which is a defect
    # this pairing catches.
    assert "VACUOUS" in inert.derivation
    assert "S_K(chat0) is EMPTY" in inert.derivation


@pytest.mark.contract
def test_the_first_order_key_lengths_are_the_formula_with_the_clamp() -> None:
    """Eq. ``eq:keylength`` with ``max{0, h_lb}`` and nothing else changed."""
    identifiers = [case.case_id for case in FIRST_ORDER_KEY_LENGTH_CASES]
    assert len(identifiers) == len(set(identifiers))
    for case in FIRST_ORDER_KEY_LENGTH_CASES:
        assert 1.0 < case.alpha < 2.0, case.case_id
        assert len(case.arithmetic.strip()) > 200, case.case_id
        bound = max(0.0, case.h_lb)
        raw = (
            case.rounds * bound
            - case.lambda_ec
            - math.ceil(math.log2(1.0 / case.eps_ev))
            - (case.alpha / (case.alpha - 1.0)) * math.log2(1.0 / case.eps_pa)
            + 1.0
        )
        assert max(0, math.floor(raw)) == case.expected, case.case_id
        assert (case.h_lb < 0.0) is case.clamped, case.case_id
    # THE INPUTS ARE CHAINED TO THE BRACKET ORACLES rather than invented.
    tight, clamped, anchor = FIRST_ORDER_KEY_LENGTH_CASES
    assert tight.h_lb == _hlow_constrained(1.5)
    assert (
        clamped.h_lb
        == dict(next(table for weight, table in FO_TOY1_TABLE if weight == 0.125))[1.5]
    )
    # MONOTONICITY IN THE LEAKAGE, which prop:monotone (i) gives verbatim for
    # the first-order length: doubling lambda_EC costs exactly its increase.
    assert anchor.h_lb == tight.h_lb
    assert anchor.lambda_ec - tight.lambda_ec == 1_000
    assert tight.expected - anchor.expected == 1_000
    # THE CLAMP IS APPLIED TO h_lb BEFORE THE FORMULA and not to its output.
    # Feeding the unclamped value in gives a different, wrong answer.
    wrong = (
        clamped.rounds * clamped.h_lb
        - clamped.lambda_ec
        - math.ceil(math.log2(1.0 / clamped.eps_ev))
        - (clamped.alpha / (clamped.alpha - 1.0)) * math.log2(1.0 / clamped.eps_pa)
        + 1.0
    )
    assert max(0, math.floor(wrong)) != clamped.expected


# ===========================================================================
#  Group 11 -- the 1.0.0 admission surface (C21 as amended)
# ===========================================================================


def _sequential(terms: tuple[float, ...]) -> tuple[tuple[float, ...], int | None]:
    """Return the binary64 partial sums and the first inexact addition's index.

    An addition is EXACT exactly when the binary64 result equals the exact
    rational sum of the same two operands, which is what ``Fraction`` decides.
    """
    accumulated = 0.0
    exact = Fraction(0)
    partials: list[float] = []
    first: int | None = None
    for index, term in enumerate(terms):
        accumulated = accumulated + term
        exact = exact + Fraction(term)
        partials.append(accumulated)
        if first is None and Fraction(accumulated) != exact:
            first = index
    return tuple(partials), first


@pytest.mark.contract
def test_the_summation_cases_are_the_arithmetic_they_record() -> None:
    """Condition (S) of ``def:optol``, recomputed from the literal families.

    The verdict is decided by comparing each binary64 addition against the same
    addition over ``Fraction``; the HAND DERIVATION recorded with each case --
    2^-60 is below half an ulp of 1, and 1 + 2^-53 is a tie that
    round-to-nearest-even resolves downward -- stays authoritative.
    """
    identifiers = [case.case_id for case in SUMMATION_CASES]
    assert len(identifiers) == len(set(identifiers))
    for case in SUMMATION_CASES:
        assert len(case.derivation.strip()) > 200, case.case_id
        partials, first = _sequential(case.terms)
        assert partials == case.partial_sums, case.case_id
        assert first == case.first_inexact_index, case.case_id
        exact = sum((Fraction(term) for term in case.terms), Fraction(0))
        assert (exact.numerator, exact.denominator) == case.exact_total, case.case_id
        # Delta_cpl is the defect of the COMPUTED sum, which is exactly what
        # makes (S) necessary: it reads 0 on every refused case here.
        assert abs(partials[-1] - 1.0) == case.computed_completeness_defect
        # ADMITTED EXACTLY WHEN NO ADDITION ROUNDS, and refused with the one
        # reason at every tau_num otherwise.
        assert case.admitted is (first is None), case.case_id
        assert (case.reason is None) is case.admitted, case.case_id
        if case.reason is not None:
            assert case.reason == "bob_povm_summation_rounds", case.case_id
    # THE PAIR IS THE POINT: two families at operator-norm distance 2^-53, both
    # with representable entries and all three defects reading 0, one admitted
    # and one refused -- separated by whether an addition rounded.
    refused = next(c for c in SUMMATION_CASES if c.case_id == "S-CONVERSE-2^-53")
    admitted = next(c for c in SUMMATION_CASES if c.case_id == "S-EXACT-NEIGHBOUR")
    assert refused.computed_completeness_defect == 0.0
    assert admitted.computed_completeness_defect == 0.0
    assert refused.admitted is False and admitted.admitted is True
    deltas = zip(refused.terms, admitted.terms, strict=True)
    assert max(abs(a - b) for a, b in deltas) == 2.0**-53
    # And at least one case is an ADMISSION, so the group is not all refusals.
    assert any(case.admitted for case in SUMMATION_CASES)


# ===========================================================================
#  The 1.0.0 marks -- superseded-by-scope, repoint, superseded
# ===========================================================================


@pytest.mark.contract
def test_the_scope_marks_share_a_derivation_line_naming_its_ground() -> None:
    """A superseded-by-scope group carries one derivation line."""
    # ONE line for the group, naming the decision and the shelving.
    assert "meat-core 1.0.0" in CERTIFICATE_SUPERSESSION_LINE
    assert "D3" in CERTIFICATE_SUPERSESSION_LINE or (
        "decision D3" in CERTIFICATE_SUPERSESSION_LINE
    )
    assert "FUTURE_SCOPE.md Section 3" in CERTIFICATE_SUPERSESSION_LINE
    assert "LICENSE:" in CERTIFICATE_SUPERSESSION_LINE
    assert "superseded-by-scope" in CERTIFICATE_SUPERSESSION_LINE.lower()
    # NOT RE-DERIVED AND NOT DELETED: every marked entry is still in ORACLES
    # with its derivation intact.
    for name, ground in SUPERSEDED_BY_SCOPE_1_0_0:
        entry = oracle(name)
        assert len(entry.derivation.strip()) > 200, name
        assert len(ground) > 80, name
        # Each ground names the deleted claim or claims it went with.
        assert any(claim in ground for claim in CLAIMS_DELETED_AT_1_0_0), name

